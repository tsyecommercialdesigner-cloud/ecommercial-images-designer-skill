"""Independently verify automatic Host postprocessing; never rescore raw as compiled."""
import argparse
import json
from pathlib import Path
from dsh_postprocess_trial import load, read, sha, ROUTES
from dsh_state_audit import evidence_for
from audit_dsh_desktop_smoke import check_trace, trace_metrics


def audit(root):
    root = root.resolve()
    run = read(root / 'run.json')
    expected = {(model, case) for model in ROUTES for case in ('explicit', 'implicit', 'negative', 'recovery')}
    actual = [(row['modelKey'], row['case']) for row in run['results']]
    if len(actual) != 8 or set(actual) != expected or run['routes'] != ROUTES or run.get('postprocessingVersion') != 1:
        raise ValueError('Incomplete or unexpected integrated suite')
    if not run.get('defaultUnchanged') or run['runtimeAgentsBefore'] != run['runtimeAgentsAfter']:
        raise ValueError('Original runtime/default state changed')
    if not all(sha(root / 'orchestrator-source' / name) == digest for name, digest in run['orchestratorManifest'].items()):
        raise ValueError('Frozen orchestrator source changed')
    rows = []
    for model, case in sorted(expected):
        work = root / f'{model}-{case}-r1'
        saved = read(root / 'postprocessing' / work.name / 'result.json')
        row = dict(model=model, case=case, original_postprocess=saved)
        if (work / 'events.json').exists():
            observed = trace_metrics(read(work / 'events.json'))
            row.update({key: observed[key] for key in ('tool_calls', 'mcp_calls', 'image_blocks')})
        try:
            trial = read(work / 'trial.json')
            row.update(runtime_status=trial['status'], runtime_error=trial.get('error'))
            recorded = {key: value for key, value in trial['postprocess'].items() if key != 'process_exit_failed'}
            if recorded != saved or not all(trial['lifecycle'].get(key) is True for key in
                     ('released', 'persisted', 'runtimeAgentAbsent', 'runtimeSessionAbsent')):
                raise ValueError('Missing automatic postprocessing or verified lifecycle')
            if trial['status'] != 'completed':
                raise ValueError('Runtime failed before compilation: ' + str(trial.get('error')))
            if not all(sha(work / path) == digest for path, digest in run['skillManifest'].items()):
                raise ValueError('Frozen Skill changed')
            snapshot = read(work / 'events.json')
            if read(work / 'persisted-events.json')[:len(snapshot['events'])] != snapshot['events']:
                raise ValueError('Cold history differs')
            metrics = check_trace(snapshot, case, ROUTES[model], work, contract=True)
            row.update({key: metrics[key] for key in ('tool_calls', 'mcp_calls', 'image_blocks')})
            if saved['raw_answer_sha256'] != sha(work / 'answer.txt') or not saved.get('raw_unchanged'):
                raise ValueError('Raw answer hash changed')
            if case == 'negative':
                row.update(raw_passed=True, compiled=False, candidate_valid=False)
                if saved['compiled'] or saved['raw_passed'] is not True:
                    raise ValueError('Negative case was compiled or raw score differs')
            else:
                skill = work / '.agents/skills/ecommerce-image-designer/scripts'
                checker = load(skill / 'validate_design_state.py', 'audit_frozen_checker')
                compiler = load(skill / 'compile_design_state.py', 'audit_frozen_compiler')
                evidence = evidence_for(case, snapshot, work)
                target = root / 'postprocessing' / work.name
                if read(target / 'evidence.json') != evidence:
                    raise ValueError('Stored evidence differs from original inputs/tools')
                raw = checker.parse_answer((work / 'answer.txt').read_text(encoding='utf-8'))
                raw_passed = True
                try:
                    checker.validate(raw, evidence)
                except (ValueError, TypeError, KeyError) as error:
                    raw_passed = False
                    row['raw_error'] = str(error)
                if saved['raw_passed'] != raw_passed or read(target / 'raw-score.json')['raw_passed'] != raw_passed:
                    raise ValueError('Raw score rewritten')
                candidate, changes = compiler.compile_candidate(raw, evidence, checker)
                if read(target / 'state.json') != candidate or read(target / 'changes.json') != changes:
                    raise ValueError('Candidate/diff differs from deterministic replay')
                if (target / 'view.md').read_text(encoding='utf-8') != checker.render(candidate):
                    raise ValueError('Human view differs from validated state')
                if saved['candidate_sha256'] != sha(target / 'state.json') or saved['validator_sha256'] != sha(skill / 'validate_design_state.py') or saved['compiler_sha256'] != sha(skill / 'compile_design_state.py'):
                    raise ValueError('Frozen program/candidate digest differs')
                row.update(raw_passed=raw_passed, compiled=True, candidate_valid=True,
                           confirm_images=candidate['next']['confirm_images'], execution=candidate['next']['execution'])
            if not saved.get('pipeline_passed'):
                raise ValueError('Automatic pipeline failed')
            row['pipeline_verified'] = True
        except (ValueError, KeyError, TypeError, OSError) as error:
            row.update(pipeline_verified=False, audit_error=str(error))
        rows.append(row)
    return dict(trials=8, runtime_completed=sum(item['status'] == 'completed' for item in run['results']),
                raw_evaluated=sum(row['original_postprocess']['raw_evaluated'] for row in rows),
                raw_passed=sum(row.get('raw_passed', False) for row in rows),
                compiled_valid=sum(row.get('candidate_valid', False) for row in rows),
                negative_passed=sum(row['case'] == 'negative' and row.get('raw_passed', False) for row in rows),
                pipeline_verified=sum(row['pipeline_verified'] for row in rows),
                tool_calls=sum(row.get('tool_calls', 0) for row in rows), mcp_calls=sum(row.get('mcp_calls', 0) for row in rows),
                image_blocks=sum(row.get('image_blocks', 0) for row in rows), rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    report = audit(args.root)
    output = args.root / 'postprocessing-audit.json'
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}))
    return int(report['pipeline_verified'] != 8)


if __name__ == '__main__':
    raise SystemExit(main())
