"""Free test Host postprocessing: score raw answer, then compile a separate draft."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from audit_dsh_desktop_smoke import check_trace
from dsh_state_audit import evidence_for

ROUTES = {'sonnet': dict(provider='codeproxy-anthropic', model='claude-sonnet-5-5'),
          'sol': dict(provider='codeproxy-openai', model='gpt-6.1-sol')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process_trial(root, name):
    root = root.resolve()
    if not re.fullmatch(r'(sonnet|sol)-(explicit|implicit|negative|recovery)-r1', name):
        raise ValueError('Unknown fixed trial identity')
    work = root / name
    output = root / 'postprocessing' / name
    # Refuse second processing, including a previous failed attempt.
    output.mkdir(parents=True, exist_ok=False)
    report = dict(version=1, trial=name, trace_passed=False, raw_passed=False, raw_evaluated=False,
                  compiled=False, candidate_valid=False, ready_for_user_review=False,
                  new_model_calls=0, new_mcp_calls=0)
    try:
        run, trial = read(root / 'run.json'), read(work / 'trial.json')
        model, case = name.split('-')[:2]
        if run['routes'] != ROUTES or (trial['modelKey'], trial['case']) != (model, case):
            raise ValueError('Actual trial route or identity differs from frozen suite')
        if trial['status'] != 'completed' or not all(trial.get('lifecycle', {}).get(key) is True for key in
                                                   ('released', 'persisted', 'runtimeAgentAbsent', 'runtimeSessionAbsent')):
            raise ValueError('Do not compile incomplete or unreleased runtime output')
        for path, digest in run['skillManifest'].items():
            candidate_path = (work / path).resolve()
            if not candidate_path.is_relative_to(work.resolve()) or sha(candidate_path) != digest:
                raise ValueError('Frozen Skill package mismatch')
        snapshot = read(work / 'events.json')
        stored = read(work / 'persisted-events.json')
        if stored[:len(snapshot['events'])] != snapshot['events']:
            raise ValueError('Cold history does not preserve observed events')
        check_trace(snapshot, case, ROUTES[model], work, contract=True)
        report['trace_passed'] = True
        answer_path = work / 'answer.txt'
        answer = answer_path.read_text(encoding='utf-8')
        report['raw_answer_sha256'] = sha(answer_path)
        if not answer.strip():
            raise ValueError('Empty raw answer')
        if case == 'negative':
            report.update(raw_evaluated=True, raw_passed=True, compilation='not_applicable', pipeline_passed=True)
        else:
            checker_path = work / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py'
            compiler_path = checker_path.with_name('compile_design_state.py')
            checker = load(checker_path, 'frozen_trial_checker')
            compiler = load(compiler_path, 'frozen_trial_compiler')
            report.update(validator_sha256=sha(checker_path), compiler_sha256=sha(compiler_path))
            evidence = evidence_for(case, snapshot, work)
            (output / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
            # A parse failure cannot be repaired by compilation. A validation
            # failure stays a raw failure even if a new candidate is valid.
            report['raw_evaluated'] = True
            raw = checker.parse_answer(answer)
            try:
                checker.validate(raw, evidence)
                report['raw_passed'] = True
            except (ValueError, TypeError, KeyError) as error:
                report['raw_error'] = str(error)
            candidate, changes = compiler.compile_candidate(raw, evidence, checker)
            # Only a new candidate is written. No session/prompt, permission,
            # approval, generation or model request exists in this process.
            for filename, value in [('state.json', candidate), ('changes.json', changes)]:
                (output / filename).write_text(compiler.serialized(value), encoding='utf-8')
            (output / 'view.md').write_text(checker.render(candidate), encoding='utf-8')
            report.update(compiled=True, candidate_valid=True, pipeline_passed=True,
                          ready_for_user_review=True, execution='not_authorized',
                          candidate_sha256=sha(output / 'state.json'))
        if sha(answer_path) != report['raw_answer_sha256']:
            raise ValueError('Original answer changed during postprocessing')
        report['raw_unchanged'] = True
    except (ValueError, TypeError, KeyError, OSError, StopIteration) as error:
        report.update(pipeline_passed=False, ready_for_user_review=False, error=str(error))
    (output / 'raw-score.json').write_text(json.dumps({key: value for key, value in report.items()
                                                      if key.startswith('raw_') or key == 'error'}, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('trial')
    args = parser.parse_args()
    try:
        report = process_trial(args.root, args.trial)
        print(json.dumps(report, ensure_ascii=False))
        return int(not report['pipeline_passed'])
    except (ValueError, OSError) as error:
        print(json.dumps(dict(pipeline_passed=False, error=str(error)), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
