import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('state_audit', REPO / 'scripts/dsh_state_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class StateEvidenceTests(unittest.TestCase):
    def test_fact_source_and_scope_label_do_not_supply_image_provenance(self):
        actual = dict(scope='synthetic test only', images=[dict(id='image-x', role='product')],
                      facts=[dict(id='fact-x', value='白色壳体', source='合成夹具')],
                      accepted_images=['keep-x'], changed_image='change-y')
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            (work / 'design-record.json').write_text(json.dumps(actual), encoding='utf-8')
            evidence = audit.evidence_for('recovery', {'events': []}, work)
            self.assertEqual(evidence['images'][0]['provenance'], 'unknown')
            self.assertEqual(evidence['locked_images'], ['keep-x'])
            self.assertEqual(evidence['edit_images'], ['change-y'])
            self.assertEqual(evidence['facts'][0]['source'], 'record')

    def test_capability_source_is_actual_tool_and_no_secret_is_copied(self):
        tool = next(iter(audit.QUERIES))
        payload = dict(models=['provider-native-id'], key_present=True, private_key='never-retain-this')
        snapshot = {'events': [dict(type='tool/call', data=dict(callId='call-x', name=tool)),
                              dict(type='tool/result', data=dict(message=dict(toolCallId='call-x', content=[dict(type='text', text=json.dumps(payload))])))]}
        evidence = audit.evidence_for('explicit', snapshot, Path('.'))
        self.assertEqual(evidence['capabilities'][0]['models'], ['provider-native-id'])
        self.assertEqual(evidence['capabilities'][0]['query_tool'], tool)
        self.assertNotIn('never-retain-this', json.dumps(evidence))
        self.assertNotIn('ready', json.dumps(evidence))

    def test_failed_answer_is_not_rewritten_and_evidence_remains(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp) / 'case'
            script = work / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py'
            script.parent.mkdir(parents=True)
            shutil.copyfile(REPO / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py', script)
            answer = 'Everything is ready. Generate now.'
            path = work / 'answer.txt'
            path.write_text(answer, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'State contract'):
                audit.verify(answer, 'explicit', {'events': []}, work)
            self.assertEqual(path.read_text(encoding='utf-8'), answer)
            result = json.loads((Path(temp) / 'verification/case/result.json').read_text())
            self.assertFalse(result['valid'])
            self.assertTrue((Path(temp) / 'verification/case/evidence.json').exists())


if __name__ == '__main__':
    unittest.main()
