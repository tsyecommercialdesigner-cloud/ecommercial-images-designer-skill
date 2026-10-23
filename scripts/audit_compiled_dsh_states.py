"""Offline replay: retain raw scores, compile separate candidates without new inference."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from audit_dsh_desktop_smoke import check_trace
from dsh_state_audit import evidence_for

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / '.agents/skills/ecommerce-image-designer'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay(source, output):
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents or output in source.parents or output.exists():
        raise ValueError('Use a new, separate output directory; preserve original evidence')
    run = json.loads((source / 'run.json').read_text(encoding='utf-8'))
    expected = {(model, case) for model in ('sonnet', 'sol') for case in ('explicit', 'implicit', 'negative', 'recovery')}
    actual = [(row['modelKey'], row['case']) for row in run['results']]
    if len(actual) != 8 or set(actual) != expected or not run.get('defaultUnchanged') or run['runtimeAgentsBefore'] != run['runtimeAgentsAfter']:
        raise ValueError('Incomplete suite or changed original runtime/default')
    compiler_path = SKILL / 'scripts/compile_design_state.py'
    compiler = load(compiler_path, 'replay_compiler')
    original_audit = digest(source / 'full-audit.json')
    output.mkdir(parents=True)
    rows = []
    for model, case in sorted(expected):
        work = source / f'{model}-{case}-r1'
        answer = work / 'answer.txt'
        original = digest(answer)
        trial = json.loads((work / 'trial.json').read_text(encoding='utf-8'))
        snapshot = json.loads((work / 'events.json').read_text(encoding='utf-8'))
        if trial['status'] != 'completed' or not all(trial['lifecycle'].get(key) is True for key in ('released', 'persisted', 'runtimeAgentAbsent', 'runtimeSessionAbsent')):
            raise ValueError('Incomplete or unreleased original trial')
        stored = json.loads((work / 'persisted-events.json').read_text(encoding='utf-8'))
        if stored[:len(snapshot['events'])] != snapshot['events']:
            raise ValueError('Persisted history differs from observed events')
        if not all(digest(work / path) == sha for path, sha in run['skillManifest'].items()):
            raise ValueError('Original frozen package changed')
        check_trace(snapshot, case, run['routes'][model], work, contract=True)
        row = dict(model=model, case=case, trace_passed=True, raw_answer_sha256=original)
        if case == 'negative':
            row.update(raw_passed=True, compiled=False)
        else:
            checker_path = work / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py'
            if digest(checker_path) != digest(SKILL / 'scripts/validate_design_state.py'):
                raise ValueError('Do not loosen the frozen validator for compilation')
            checker = compiler.load_checker(checker_path)
            evidence = evidence_for(case, snapshot, work)
            raw = checker.parse_answer(answer.read_text(encoding='utf-8'))
            try:
                checker.validate(raw, evidence)
                row['raw_passed'] = True
            except (ValueError, KeyError, TypeError) as error:
                row.update(raw_passed=False, raw_error=str(error))
            candidate, changes = compiler.compile_candidate(raw, evidence, checker)
            target = output / work.name
            target.mkdir()
            for name, value in [('evidence.json', evidence), ('state.json', candidate), ('changes.json', changes)]:
                (target / name).write_text(compiler.serialized(value), encoding='utf-8')
            (target / 'view.md').write_text(checker.render(candidate), encoding='utf-8')
            row.update(compiled=True, candidate_valid=True, requires_user_review=True,
                       changed_paths=changes['changed_paths'], validator_sha256=digest(checker_path))
        if digest(answer) != original:
            raise ValueError('Original answer changed')
        row['raw_unchanged'] = True
        rows.append(row)
    if digest(source / 'full-audit.json') != original_audit:
        raise ValueError('Original audit changed')
    report = dict(source=str(source), new_model_calls=0, new_mcp_calls=0, raw_passed=sum(row['raw_passed'] for row in rows),
                  trials=8, compiled_candidates=sum(row['compiled'] for row in rows),
                  compiled_valid=sum(row.get('candidate_valid', False) for row in rows),
                  negative_passed=sum(row['case'] == 'negative' and row['raw_passed'] for row in rows),
                  raw_audit_unchanged=True, compiler_sha256=digest(compiler_path), rows=rows)
    (output / 'report.json').write_text(compiler.serialized(report), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = replay(args.source, args.output)
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}))


if __name__ == '__main__':
    main()
