"""Mechanical checks for real Desktop trials; human semantic review remains required."""
import argparse
from collections import Counter
import hashlib
import json
import ntpath
from pathlib import Path

FREE = {
    'mcp__zhenzhen-gptimagegen2-5-mcp__get_model_guide',
    'mcp__zhenzhen-nanobanana-mcp__list_models',
    'mcp__zhenzhen-nanobanana-mcp__inspect_design_images',
}


def trace_metrics(snapshot):
    """Count raw observations even when another step makes the trial fail."""
    calls = [e['data'] for e in snapshot['events'] if e['type'] == 'tool/call']
    mcp = [c for c in calls if c['name'].startswith('mcp__')]
    mcp_ids = {c['callId'] for c in mcp}
    image_blocks = sum(block['type'] == 'image'
                       for e in snapshot['events'] if e['type'] == 'tool/result'
                       and e['data']['message']['toolCallId'] in mcp_ids
                       for block in e['data']['message']['content'])
    host_calls = sum(c['name'] == 'list_agents' for c in calls)
    return dict(tool_calls=len(calls), host_discovery_calls=host_calls,
                business_tool_calls=len(calls)-host_calls, mcp_calls=len(mcp), image_blocks=image_blocks,
                tools=Counter(c['name'] for c in calls))


def check_trace(snapshot, case, route, work=None, *, contract=False):
    events = snapshot['events']
    headers = [e['data']['header']['config'] for e in events if e['type'] == 'request/header']
    if not headers or any(any(h.get(k) != route[k] for k in ('provider', 'model')) for h in headers):
        raise ValueError('Missing or wrong actual model request header')
    end = [e['data'] for e in events if e['type'] == 'turn/end']
    if len(end) != 1 or end[0]['reason']['kind'] != 'completed':
        raise ValueError('Turn did not complete normally')
    calls = [e['data'] for e in events if e['type'] == 'tool/call']
    results = {e['data']['message']['toolCallId']: e['data']['message']
               for e in events if e['type'] == 'tool/result'}
    for call in calls:
        if call['callId'] not in results or results[call['callId']].get('isError'):
            raise ValueError('Missing or unsuccessful tool result')
    if any(not row['allowed'] for row in snapshot['audit'] if row['phase'] == 'model'):
        raise ValueError('A model attempted a capability rejected by the free guard')
    for call in calls:
        if call['name'] == 'list_agents':
            if json.loads(call['arguments']) != {}:
                raise ValueError('Host discovery requires empty arguments')
        elif call['name'] not in FREE | {'skill', 'read', 'working_directory', 'run_code'}:
            raise ValueError('Unauthorized non-business capability')
    mcp = [c for c in calls if c['name'].startswith('mcp__')]
    if any(c['name'] not in FREE for c in mcp):
        raise ValueError('Forbidden MCP attempt, including attempts rejected elsewhere')
    image_blocks = sum(block['type'] == 'image' for call in mcp
                       for block in results[call['callId']]['content'])
    reads = [json.loads(c['arguments'])['file_path'] for c in calls if c['name'] == 'read']
    skills = [json.loads(c['arguments']).get('name') for c in calls if c['name'] == 'skill']
    if case == 'negative':
        if any(c['name'] != 'list_agents' for c in calls):
            raise ValueError('Negative case invoked tools')
    elif 'ecommerce-image-designer' not in skills:
        raise ValueError('Positive case did not actually load the Skill')
    if case == 'explicit' and {c['name'] for c in mcp} != FREE - {'mcp__zhenzhen-nanobanana-mcp__inspect_design_images'}:
        raise ValueError('Explicit case did not query both actual MCP services')
    if case == 'implicit' and (image_blocks != 2 or not any(c['name'].endswith('__inspect_design_images') for c in mcp)):
        raise ValueError('Implicit case lacks the two actual MCP image blocks')
    if case == 'recovery' and (mcp or not any(p.replace('\\', '/').endswith('/design-record.json') or p == 'design-record.json' for p in reads)):
        raise ValueError('Recovery did not read its actual record, or used an MCP')
    if case == 'recovery':
        # This fixed fixture asks only for a text revision; unrelated successful
        # reads are also failures, not merely filesystem errors or guard denials.
        resource_dir = 'reference'
        if work:
            package = Path(work) / '.agents/skills/ecommerce-image-designer'
            if (package / 'references').is_dir():
                if (package / 'reference').exists():
                    raise ValueError('Ambiguous frozen resource layout')
                resource_dir = 'references'  # Read-only auditing of old snapshots.
        prefix = '.agents/skills/ecommerce-image-designer/' + resource_dir + '/'
        recovery_resources = ('design-record.md',) if contract and resource_dir == 'reference' else (
            'design-record.md', 'planning-and-prompts.md', 'review-and-revision.md')
        allowed = {'design-record.json'} | {
            prefix + name
            for name in recovery_resources}
        if contract:
            allowed.add(prefix + 'state-contract.md')
        for path in reads:
            relative = ntpath.relpath(path, str(work)) if work and ntpath.isabs(path) else path
            if ntpath.normpath(relative).replace('\\', '/') not in allowed:
                raise ValueError('Recovery read outside its record and stage resources')
    host_calls = sum(c['name'] == 'list_agents' for c in calls)
    return dict(tool_calls=len(calls), host_discovery_calls=host_calls,
                business_tool_calls=len(calls)-host_calls, mcp_calls=len(mcp), image_blocks=image_blocks,
                tools=Counter(c['name'] for c in calls), read_paths=reads,
                skill_loaded=bool(skills), actual_request_headers=headers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    run = json.loads((root / 'run.json').read_text(encoding='utf-8'))
    expected = {(model, case) for model in ('sonnet', 'sol')
                for case in ('explicit', 'implicit', 'negative', 'recovery')}
    found = [(row['modelKey'], row['case']) for row in run['results']]
    if len(found) != 8 or set(found) != expected or not run.get('defaultUnchanged'):
        raise ValueError('Incomplete suite or changed default selection')
    rows = []
    for model, case in sorted(expected):
        work = root / f'{model}-{case}-r1'
        trial = json.loads((work / 'trial.json').read_text(encoding='utf-8'))
        if trial['status'] != 'completed' or not (work / 'answer.txt').read_text(encoding='utf-8').strip():
            raise ValueError('Trial or answer incomplete')
        if run.get('lifecycleVersion') == 1:
            lifecycle = trial.get('lifecycle', {})
            if not all(lifecycle.get(k) is True for k in
                       ('released', 'persisted', 'runtimeAgentAbsent', 'runtimeSessionAbsent')):
                raise ValueError('Missing verified runtime release and persistent history')
            stored = json.loads((work / 'persisted-events.json').read_text(encoding='utf-8'))
            live = json.loads((work / 'events.json').read_text(encoding='utf-8'))['events']
            if stored[:len(live)] != live:
                raise ValueError('Cold history lost observed events')
        for path, digest in run['skillManifest'].items():
            if hashlib.sha256((work / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Frozen Skill package mismatch')
        snapshot = json.loads((work / 'events.json').read_text(encoding='utf-8'))
        try:
            use_contract = run.get('outputContract') in ('ecommerce-design-state/v1', 'ecommerce-design-state/v2')
            row = check_trace(snapshot, case, run['routes'][model], work, contract=use_contract)
            if use_contract and case != 'negative':
                from dsh_state_audit import verify
                row['state_contract'] = verify((work / 'answer.txt').read_text(encoding='utf-8'), case, snapshot, work)
            row['status'] = 'passed'
        except (ValueError, TypeError, KeyError, StopIteration) as exc:
            row = dict(status='failed', error=str(exc), **trace_metrics(snapshot))
        row.update(trial=work.name, seconds=trial['seconds'])
        rows.append(row)
    failed = sum(row['status'] == 'failed' for row in rows)
    report = dict(status='mechanical_failed' if failed else 'mechanical_pass_pending_semantic_review', trials=8, failed=failed,
                  tool_calls=sum(row['tool_calls'] for row in rows),
                  host_discovery_calls=sum(row['host_discovery_calls'] for row in rows),
                  business_tool_calls=sum(row['business_tool_calls'] for row in rows),
                  mcp_calls=sum(row['mcp_calls'] for row in rows),
                  image_blocks=sum(row['image_blocks'] for row in rows), rows=rows)
    (root / 'mechanical-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, ensure_ascii=False))
    return int(failed > 0)


if __name__ == '__main__':
    raise SystemExit(main())
