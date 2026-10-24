"""Prepare fresh synthetic inputs for the installed DSH Desktop free suite."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[1]

_workspace_spec = importlib.util.spec_from_file_location('evaluation_workspace', Path(__file__).with_name('evaluation_workspace.py'))
_workspace = importlib.util.module_from_spec(_workspace_spec)
_workspace_spec.loader.exec_module(_workspace)
validate_root, claim_root, initialize_project = _workspace.validate_root, _workspace.claim_root, _workspace.initialize_project



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        root = validate_root(args.output)
    except ValueError as error:
        parser.error(str(error))
    if root.exists() or not root.name.startswith('dsh-skill-host-76d8-'):
        parser.error('Use a new directory below .eval-workspaces named dsh-skill-host-76d8-<unique-id>')
    spec = importlib.util.spec_from_file_location('image_fixture', REPO / 'evals/mock_mcp.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    claim_root(root)
    for model in ('sonnet', 'sol'):
        for case in ('explicit', 'implicit', 'negative', 'recovery'):
            work = root / f'{model}-{case}-r1'
            work.mkdir()
            initialize_project(work)  # Isolated project boundary; no commits or remotes.
            shutil.copytree(REPO / '.agents/skills/ecommerce-image-designer', work / '.agents/skills/ecommerce-image-designer')
            fixture.png_fixture(work / 'P01.png')
            fixture.png_fixture(work / 'R01.png', reference=True)
            record = dict(design_id='dsh-host-fixture', version=1, scope='synthetic test only',
                          facts=[dict(id='F01', value='灰色盒体、深灰盖沿', source='合成夹具')],
                          images=[dict(id='P01', role='product', source='P01.png'),
                                  dict(id='R01', role='reference', reference_use='style', source='R01.png')],
                          accepted_images=['M01'], changed_image='M02', previous_layout='M02上标题下商品', paid_authorization=False)
            (work / 'design-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (REPO / '.agents/skills/ecommerce-image-designer').rglob('*') if p.is_file()}
    home = Path(os.environ.get('DSH_HOME', Path.home() / '.dsh'))
    paths = [home / 'profiles/desktop' / name for name in ('cordis.patch.yml', 'cordis.yml', 'package.json', 'pnpm-lock.yaml')]
    paths.append(home / '.credentials.yaml')
    preserve = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    orchestrator = root / 'orchestrator-source'
    orchestrator.mkdir()
    source_names = ('dsh_postprocess_trial.py', 'dsh_state_audit.py', 'audit_dsh_desktop_smoke.py',
                    'run_dsh_desktop_smoke.mjs', 'dsh_postprocess_client.mjs', 'dsh_desktop_client.mjs',
                    'dsh_free_guard.mjs', 'dsh_trial_status.mjs', 'dsh_test_lifecycle.mjs')
    for name in source_names:
        shutil.copyfile(REPO / 'scripts' / name, orchestrator / name)
    orchestrator_manifest = {name: hashlib.sha256((orchestrator / name).read_bytes()).hexdigest() for name in source_names}
    contract_path = REPO / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py'
    output_contract = None
    if contract_path.exists():
        contract_spec = importlib.util.spec_from_file_location('prepared_design_contract', contract_path)
        contract_module = importlib.util.module_from_spec(contract_spec)
        contract_spec.loader.exec_module(contract_module)
        output_contract = contract_module.CONTRACT_ID
    # The request asks for one NEW main image. Allocate its stable identity in
    # trusted orchestration, independently of input P01/R01 and the model answer.
    design_targets = {f'{model}-implicit-r1': ['M01'] for model in ('sonnet', 'sol')}
    (root / 'before.json').write_text(json.dumps(dict(skill_manifest=manifest, configuration_sha256=preserve,
                                                  design_targets=design_targets,
                                                  orchestrator_manifest=orchestrator_manifest, output_contract=output_contract), indent=2), encoding='utf-8')
    print(root)


if __name__ == '__main__':
    main()
