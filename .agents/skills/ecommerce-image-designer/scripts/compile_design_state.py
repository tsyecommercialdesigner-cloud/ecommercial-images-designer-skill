"""Compile a new unapproved candidate; trusted context owns state, not the LLM."""
import argparse
import copy
import hashlib
import importlib.util
import json
import ntpath
from pathlib import Path


def load_checker(path=None):
    path = path or Path(__file__).with_name('validate_design_state.py')
    spec = importlib.util.spec_from_file_location('candidate_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def serialized(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def changed_paths(before, after, path=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            child = path + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in before or key not in after:
                result.append(child)
            else:
                result.extend(changed_paths(before[key], after[key], child))
        return result
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [item for i, (old, new) in enumerate(zip(before, after))
                for item in changed_paths(old, new, path + '/' + str(i))]
    return [] if before == after else [path or '/']


def compile_candidate(raw, evidence, checker=None):
    checker = checker or load_checker()
    checker.shape(raw, ('contract', 'mode', 'validation', 'state', 'proposal', 'next'), 'raw record')
    checker.require(raw['contract'] == checker.CONTRACT_ID == 'ecommerce-design-state/v2', 'Compiler requires v2; no implicit v1 migration')
    checker.require(raw['mode'] == evidence['mode'], 'Proposal mode differs from requested task')
    checker.require(not evidence.get('generation_entry') and evidence.get('execution', 'not_authorized') == 'not_authorized', 'Only unapproved drafts without execution mapping may compile')
    mode = evidence['mode']
    images = []
    for row in evidence['images']:
        checker.require(not row.get('must_upload') and row.get('drawing_use') != 'upload', 'Do not discard a user-required upload; compile that mapping separately')
        source = row.get('source')
        # Select only a caller-verified absolute alias, never parse a model's
        # decorated source string or infer provenance from pixels/file names.
        for candidate in [source, *row.get('allowed_sources', [])]:
            if isinstance(candidate, str) and (ntpath.isabs(candidate) or '://' in candidate):
                source = candidate
                break
        images.append(dict(id=row['id'], source=source, role=row['role'], provenance=row['provenance'],
                           reference_use=row['reference_use'], input_index=None,
                           drawing_use=row.get('drawing_use', 'analysis_only' if row['role'] == 'reference' else 'undecided')))
    capabilities = []
    for row in evidence['capabilities']:
        checker.require(row.get('query_succeeded', True) is True, 'A failed query cannot become a successful capability record')
        capabilities.append(dict(server=checker.SERVER_ALIASES.get(row['server']), query_tool=row['query_tool'],
                                 models=copy.deepcopy(row['models']), query_succeeded=True, configured=row['configured'],
                                 upstream='not_tested', performance='not_tested'))
    state = dict(images=images, facts=copy.deepcopy(evidence['facts']), capabilities=capabilities,
                 locked_images=copy.deepcopy(evidence['locked_images']), edit_images=copy.deepcopy(evidence['edit_images']),
                 baseline=copy.deepcopy(evidence['baseline']))
    if mode == 'status':
        proposal = None
        confirm = []
        missing = ['product_image', 'product_details', 'canvas', 'brand']
    else:
        checker.shape(raw['proposal'], ('canvas', 'copy', 'layout', 'appearance', 'reference_style'), 'raw proposal')
        proposal = copy.deepcopy(raw['proposal'])
        if mode == 'revision':
            # The caller authorized layout edits only. Copy/style are restored
            # from the original ledger, not "corrected" by asking the model to
            # invent missing values. Every discarded field appears in the diff.
            proposal.update(canvas=copy.deepcopy(state['baseline']['canvas']),
                            copy={key: copy.deepcopy(state['baseline'][key]) for key in ('title', 'subtitle', 'labels', 'footnote')},
                            appearance=dict.fromkeys(('background', 'typography', 'lighting')), reference_style=[])
            for row in proposal['layout']:
                row['overflow'] = 'reflow_preserve_all_copy'
                if row['element'] in ('subtitle', 'labels', 'footnote'):
                    row['if_present'] = state['baseline'][row['element']] is None
            confirm = state['edit_images'][:]
        else:
            confirm = copy.deepcopy(evidence.get('target_images', raw['next']['confirm_images']))
            checker.unique(confirm, 'new draft identities')
            checker.require(len(confirm) == 1 and not set(confirm) & {image['id'] for image in images}, 'New draft identity must differ from input image identities')
        missing = [key for key, value in state['baseline'].items() if value is None]
    candidate = dict(contract=checker.CONTRACT_ID, mode=mode, validation='pending', state=state, proposal=proposal,
                     next=dict(rollback_stage='S2' if mode == 'revision' else None,
                               stage='S0' if mode == 'status' else 'S3', confirm_images=confirm,
                               missing_fields=missing, execution='not_authorized'))
    checker.validate(candidate, evidence)
    report = dict(valid=True, new_candidate=True, original_model_pass_claim=False, requires_user_review=True,
                  input_object_sha256=hashlib.sha256(serialized(raw).encode('utf-8')).hexdigest(),
                  compiled_state_sha256=hashlib.sha256(serialized(candidate).encode('utf-8')).hexdigest(),
                  changed_paths=changed_paths(raw, candidate),
                  ownership=dict(state='independent evidence', plan='model proposal', revision='model layout only'))
    return candidate, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwrite original or earlier candidate')
    args = parser.parse_args()
    try:
        checker = load_checker()
        raw = checker.parse_answer(args.record.read_text(encoding='utf-8'))
        candidate, report = compile_candidate(raw, json.loads(args.evidence.read_text(encoding='utf-8')), checker)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'state.json').write_text(serialized(candidate), encoding='utf-8')
        (args.output / 'changes.json').write_text(serialized(report), encoding='utf-8')
        (args.output / 'view.md').write_text(checker.render(candidate), encoding='utf-8')
        print(json.dumps(dict(valid=True, new_candidate=True, requires_user_review=True)))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps(dict(valid=False, error=str(error)), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
