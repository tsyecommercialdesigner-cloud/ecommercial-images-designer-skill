import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_design_state_contract import fixture, contract

SCRIPT = Path(__file__).resolve().parents[1] / '.agents/skills/ecommerce-image-designer/scripts/compile_design_state.py'
spec = importlib.util.spec_from_file_location('state_compiler', SCRIPT)
compiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compiler)


class CompilationTests(unittest.TestCase):
    def test_context_not_model_owns_provenance_facts_and_frozen_scope(self):
        raw, evidence = fixture()
        raw['state']['images'][1].update(provenance='photo', source='another-product.png')
        raw['state']['facts'][0]['text'] = 'invented performance'
        raw['state']['locked_images'] = []
        raw['next'].update(confirm_images=['accepted-5'], execution='authorized')
        raw['proposal']['copy']['title'] = 'unauthorized copy'
        raw['proposal']['appearance']['background'] = 'unauthorized global style'
        raw['proposal']['reference_style'] = [dict(image_id='look-93', attribute='background_tone', value='unknown')]
        before = copy.deepcopy(raw)
        candidate, report = compiler.compile_candidate(raw, evidence, contract)
        self.assertEqual(raw, before)
        self.assertEqual(candidate['state']['images'][1]['provenance'], 'unknown')
        self.assertEqual(candidate['state']['facts'], evidence['facts'])
        self.assertEqual(candidate['state']['locked_images'], ['accepted-5'])
        self.assertEqual(candidate['next']['confirm_images'], ['revise-2'])
        self.assertEqual(candidate['next']['execution'], 'not_authorized')
        self.assertIsNone(candidate['proposal']['copy']['title'])
        self.assertTrue(report['new_candidate'])
        self.assertFalse(report['original_model_pass_claim'])
        self.assertTrue(report['changed_paths'])

    def test_plan_creative_values_are_preserved_but_metadata_is_not_echoed(self):
        raw, evidence = fixture('plan')
        for state in (raw['state'], evidence):
            state.update(locked_images=[], edit_images=[])
        raw['next']['confirm_images'] = ['draft-x']
        raw['proposal']['copy']['title'] = '蓝色外壳'
        before_proposal = copy.deepcopy(raw['proposal'])
        raw['state']['images'][0]['source'] = '附件路径：asset.png；附带说明'
        evidence['images'][0]['allowed_sources'] = ['E:/original/asset.png']
        candidate, report = compiler.compile_candidate(raw, evidence, contract)
        self.assertEqual(candidate['proposal'], before_proposal)
        self.assertEqual(candidate['state']['images'][0]['source'], 'E:/original/asset.png')
        self.assertTrue(report['requires_user_review'])

    def test_compiler_cannot_turn_free_status_query_into_ready(self):
        raw, evidence = fixture('status')
        for state in (raw['state'], evidence):
            state.update(images=[], facts=[], locked_images=[], edit_images=[])
        cap = dict(server='zhenzhen-nanobanana-mcp', query_tool='list_models', models=['verified-local-id'], configured=True)
        evidence['capabilities'] = [cap]
        raw['state']['capabilities'] = [dict(cap, upstream='ready', performance='fastest')]
        raw['state']['facts'] = [dict(id='wrong', text='task instructions are not product facts', source='user')]
        candidate, _ = compiler.compile_candidate(raw, evidence, contract)
        self.assertEqual(candidate['state']['facts'], [])
        self.assertEqual(candidate['state']['capabilities'][0]['upstream'], 'not_tested')
        self.assertEqual(candidate['state']['capabilities'][0]['performance'], 'not_tested')

    def test_bad_geometry_is_rejected_not_guessed_or_reflowed(self):
        raw, evidence = fixture()
        for region in ([8, 6, 92, 22], dict(x=95, y=6, width=10, height=16)):
            raw['proposal']['layout'][0]['region'] = region
            with self.assertRaises(ValueError):
                compiler.compile_candidate(raw, evidence, contract)

    def test_no_implicit_upload_or_authorized_execution_compilation(self):
        for change in ('upload', 'execution'):
            raw, evidence = fixture()
            if change == 'upload':
                evidence['images'][1]['must_upload'] = True
            else:
                evidence['execution'] = 'authorized'
            with self.assertRaises(ValueError):
                compiler.compile_candidate(raw, evidence, contract)

    def test_extra_questions_and_v1_records_are_not_silently_migrated(self):
        raw, evidence = fixture()
        raw['questions'] = ['Is accepted-5 still frozen?']
        with self.assertRaises(ValueError):
            compiler.compile_candidate(raw, evidence, contract)
        del raw['questions']
        raw['contract'] = 'ecommerce-design-state/v1'
        with self.assertRaises(ValueError):
            compiler.compile_candidate(raw, evidence, contract)

    def test_cli_retains_original_and_refuses_overwriting_a_candidate(self):
        raw, evidence = fixture()
        with tempfile.TemporaryDirectory() as temp:
            record, source, output = Path(temp) / 'raw.json', Path(temp) / 'evidence.json', Path(temp) / 'candidate'
            record.write_text(json.dumps(raw), encoding='utf-8')
            source.write_text(json.dumps(evidence), encoding='utf-8')
            original = record.read_bytes()
            cmd = [sys.executable, '-X', 'utf8', '-B', str(SCRIPT), str(record), '--evidence', str(source), '--output', str(output)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            saved = (output / 'state.json').read_bytes()
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(second.returncode, 1)
            self.assertEqual(saved, (output / 'state.json').read_bytes())
            self.assertEqual(original, record.read_bytes())


if __name__ == '__main__':
    unittest.main()
