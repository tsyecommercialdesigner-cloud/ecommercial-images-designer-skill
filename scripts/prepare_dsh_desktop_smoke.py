"""Prepare fresh synthetic inputs for the installed DSH Desktop free suite."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists() or root.is_relative_to(REPO) or not root.name.startswith('dsh-skill-host-76d8-'):
        parser.error('Use a new external directory named dsh-skill-host-76d8-<unique-id>')
    spec = importlib.util.spec_from_file_location('image_fixture', REPO / 'evals/mock_mcp.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    root.mkdir(parents=True)
    for model in ('sonnet', 'sol'):
        for case in ('explicit', 'implicit', 'negative', 'recovery'):
            work = root / f'{model}-{case}-r1'
            work.mkdir()
            (work / '.git').mkdir()  # A project-boundary marker, no Git operations.
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
    (root / 'before.json').write_text(json.dumps(dict(skill_manifest=manifest, configuration_sha256=preserve,
                                                  orchestrator_manifest=orchestrator_manifest, output_contract=output_contract), indent=2), encoding='utf-8')
    print(root)


if __name__ == '__main__':
    main()
