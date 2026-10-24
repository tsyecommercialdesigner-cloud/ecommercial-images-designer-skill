import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from test_design_state_contract import fixture

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import dsh_postprocess_trial as pipeline


class PostprocessTests(unittest.TestCase):
    def test_trusted_new_target_replaces_model_input_identity_without_regrading_raw(self):
        parent = REPO / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            root = Path(temp)
            name, work, raw = self.prepare(root, 'implicit')
            raw['next']['confirm_images'] = ['P01']
            answer = work / 'answer.txt'
            answer.write_text(json.dumps(raw), encoding='utf-8')
            original = answer.read_bytes()
            manifest = json.loads((root / 'run.json').read_text())
            manifest['designTargets'] = {name: ['M01']}
            (root / 'run.json').write_text(json.dumps(manifest))
            report = pipeline.process_trial(root, name)
            self.assertTrue(report['pipeline_passed'], report)
            self.assertFalse(report['raw_passed'])
            self.assertEqual(answer.read_bytes(), original)
            candidate = json.loads((root / 'postprocessing' / name / 'state.json').read_text())
            self.assertEqual(candidate['next']['confirm_images'], ['M01'])
            self.assertEqual(candidate['next']['execution'], 'not_authorized')

    def test_trusted_target_still_rejects_input_identity_collision(self):
        parent = REPO / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            root = Path(temp)
            name, work, raw = self.prepare(root, 'implicit')
            manifest = json.loads((root / 'run.json').read_text())
            manifest['designTargets'] = {name: ['P01']}
            (root / 'run.json').write_text(json.dumps(manifest))
            report = pipeline.process_trial(root, name)
            self.assertFalse(report['pipeline_passed'])
            self.assertIn('independently allocated', report['error'])
            self.assertFalse((root / 'postprocessing' / name / 'state.json').exists())

    def test_replay_writes_new_candidate_without_overwriting_original_failure(self):
        parent = REPO / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            source = Path(temp) / 'source'
            name, work, raw = self.prepare(source, 'implicit')
            raw['next']['confirm_images'] = ['P01']
            (work / 'answer.txt').write_text(json.dumps(raw), encoding='utf-8')
            failed = pipeline.process_trial(source, name)
            self.assertFalse(failed['pipeline_passed'])
            original = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
            output = Path(temp) / 'new-replay'
            corrected = pipeline.process_trial(source, name, output_root=output, target_images=['M01'])
            self.assertTrue(corrected['pipeline_passed'], corrected)
            self.assertFalse(corrected['raw_passed'])
            self.assertEqual(original, {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()})
            with self.assertRaisesRegex(ValueError, 'separate'):
                pipeline.process_trial(source, name, output_root=source / 'overwrite')

    def prepare(self, root, case='recovery'):
        name = 'sol-' + case + '-r1'
        work = root / name
        skill = work / '.agents/skills/ecommerce-image-designer'
        shutil.copytree(REPO / '.agents/skills/ecommerce-image-designer', skill)
        raw, evidence = fixture('status' if case == 'explicit' else 'plan' if case == 'implicit' else 'revision')
        if case == 'explicit':
            raw['proposal'] = None
            raw['state'].update(images=[], facts=[], capabilities=[], locked_images=[], edit_images=[], baseline=dict.fromkeys(evidence['baseline']))
            raw['next'].update(rollback_stage=None, stage='S0', confirm_images=[], missing_fields=['product_image'])
            raw['state']['facts'] = [dict(id='bad', text='only discuss; not a product fact', source='user')]
        elif case == 'implicit':
            raw['state'].update(images=[dict(id='P01', source='附件路径：P01.png；SHA：not-a-source', role='product', provenance='synthetic', reference_use='none', drawing_use='undecided', input_index=None),
                                        dict(id='R01', source='R01.png', role='reference', provenance='unknown', reference_use='style', drawing_use='analysis_only', input_index=None)],
                                facts=[dict(id='V01', text='extra observation', source='observation')],
                                baseline=dict.fromkeys(evidence['baseline']), locked_images=[], edit_images=[])
            raw['next'].update(rollback_stage=None, stage='S3', confirm_images=['new-draft'], missing_fields=[])
        else:
            record = dict(images=[{key: image[key] for key in ('id', 'source', 'role', 'provenance', 'reference_use')}
                                  for image in evidence['images']],
                          facts=[dict(id=row['id'], value=row['text']) for row in evidence['facts']],
                          accepted_images=evidence['locked_images'], changed_image=evidence['edit_images'][0],
                          baseline=evidence['baseline'])
            (work / 'design-record.json').write_text(json.dumps(record), encoding='utf-8')
        events = [dict(type='request/header', data=dict(header=dict(config=pipeline.ROUTES['sol'])))]
        def call(name, args, content):
            identity = str(len(events))
            events.extend([dict(type='tool/call', data=dict(name=name, callId=identity, arguments=json.dumps(args))),
                           dict(type='tool/result', data=dict(message=dict(toolCallId=identity, content=content)))])
        call('skill', dict(name='ecommerce-image-designer'), [])
        if case == 'explicit':
            for tool in ('mcp__zhenzhen-gptimagegen2-5-mcp__get_model_guide', 'mcp__zhenzhen-nanobanana-mcp__list_models'):
                call(tool, {}, [dict(type='text', text=json.dumps(dict(models=['actual-model'], key_present=True, api_key_configured=True)))])
        elif case == 'implicit':
            call('mcp__zhenzhen-nanobanana-mcp__inspect_design_images', {}, [dict(type='image'), dict(type='image')])
        else:
            call('read', dict(file_path='design-record.json'), [])
        events.append(dict(type='turn/end', data=dict(reason=dict(kind='completed'))))
        (work / 'events.json').write_text(json.dumps(dict(events=events, audit=[])), encoding='utf-8')
        (work / 'persisted-events.json').write_text(json.dumps(events), encoding='utf-8')
        (work / 'trial.json').write_text(json.dumps(dict(modelKey='sol', case=case, status='completed',
              lifecycle=dict(released=True, persisted=True, runtimeAgentAbsent=True, runtimeSessionAbsent=True))), encoding='utf-8')
        manifest = {p.relative_to(work).as_posix(): pipeline.sha(p) for p in skill.rglob('*') if p.is_file()}
        (root / 'run.json').write_text(json.dumps(dict(routes=pipeline.ROUTES, skillManifest=manifest)), encoding='utf-8')
        answer = work / 'answer.txt'
        answer.write_text(json.dumps(raw), encoding='utf-8')
        return name, work, raw

    def test_state_query_instructions_are_not_compiled_as_product_facts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name, work, raw = self.prepare(root, 'explicit')
            original = (work / 'answer.txt').read_bytes()
            result = pipeline.process_trial(root, name)
            self.assertFalse(result['raw_passed'])
            self.assertTrue(result['candidate_valid'], result)
            candidate = pipeline.read(root / 'postprocessing' / name / 'state.json')
            self.assertEqual(candidate['state']['facts'], [])
            self.assertEqual(candidate['state']['capabilities'][0]['upstream'], 'not_tested')
            self.assertEqual(original, (work / 'answer.txt').read_bytes())

    def test_recovery_reference_placeholder_removed_in_new_candidate_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name, work, raw = self.prepare(root)
            raw['proposal']['reference_style'] = [dict(image_id=raw['state']['images'][1]['id'], attribute='background_tone', value='unknown tone')]
            (work / 'answer.txt').write_text(json.dumps(raw), encoding='utf-8')
            result = pipeline.process_trial(root, name)
            self.assertFalse(result['raw_passed'])
            self.assertTrue(result['candidate_valid'], result)
            candidate = pipeline.read(root / 'postprocessing' / name / 'state.json')
            self.assertEqual(candidate['proposal']['reference_style'], [])
            self.assertEqual(candidate['next']['confirm_images'], raw['state']['edit_images'])
            self.assertEqual(candidate['state']['locked_images'], raw['state']['locked_images'])
            self.assertEqual(pipeline.read(work / 'answer.txt'), raw)
            with self.assertRaises(FileExistsError):
                pipeline.process_trial(root, name)

    def test_plan_kind_source_and_facts_are_grounded_without_rewriting_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name, work, raw = self.prepare(root, 'implicit')
            result = pipeline.process_trial(root, name)
            self.assertFalse(result['raw_passed'])
            self.assertTrue(result['candidate_valid'], result)
            candidate = pipeline.read(root / 'postprocessing' / name / 'state.json')
            self.assertEqual(candidate['state']['baseline']['kind'], 'main')
            self.assertEqual(candidate['state']['images'][0]['source'], 'P01.png')
            self.assertEqual([row['text'] for row in candidate['state']['facts']], ['灰色盒体', '深灰盖沿'])
            self.assertEqual(candidate['proposal'], raw['proposal'])
            self.assertEqual(pipeline.read(work / 'answer.txt'), raw)

    def test_blocked_tool_attempt_stops_before_compilation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name, work, _ = self.prepare(root)
            trace = pipeline.read(work / 'events.json')
            trace['audit'] = [dict(phase='model', name='generate_image', allowed=False)]
            (work / 'events.json').write_text(json.dumps(trace))
            result = pipeline.process_trial(root, name)
            self.assertFalse(result['pipeline_passed'])
            self.assertFalse(result['raw_evaluated'])
            self.assertFalse((root / 'postprocessing' / name / 'state.json').exists())

    def test_release_failure_frozen_drift_and_bad_json_fail_closed(self):
        for failure in ('release', 'drift', 'json'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                name, work, _ = self.prepare(root)
                if failure == 'release':
                    trial = pipeline.read(work / 'trial.json')
                    trial['lifecycle']['released'] = False
                    (work / 'trial.json').write_text(json.dumps(trial))
                elif failure == 'drift':
                    (work / '.agents/skills/ecommerce-image-designer/SKILL.md').write_text('changed')
                else:
                    (work / 'answer.txt').write_text('invented state outside JSON')
                result = pipeline.process_trial(root, name)
                self.assertFalse(result['pipeline_passed'], result)
                self.assertTrue((root / 'postprocessing' / name / 'raw-score.json').exists())
                self.assertFalse((root / 'postprocessing' / name / 'state.json').exists())

    def test_work_identity_cannot_escape_to_other_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                pipeline.process_trial(Path(temp), '../other')


if __name__ == '__main__':
    unittest.main()
