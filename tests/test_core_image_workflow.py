"""Core-only protocol regression; no provider, credentials, or network."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


mock = module('core_mock', ROOT / 'evals/mock_mcp.py')
grader = module('core_grader', ROOT / 'scripts/grade_behavior_eval.py')


class CoreImageWorkflowTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='core-image-', dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = ROOT / '.agents/skills/ecommerce-image-designer'
        mock.seed_workspace(self.root, 'approved M01; no extension tools', 'E11', 'nano-approved')
        self.nano = mock.MockServer('nano', self.root, self.skill)
        self.gpt = mock.MockServer('gpt', self.root, self.skill)
        self.io = mock.MockServer('io', self.root, self.skill)

    def request(self, reversed_roles=False):
        images = ['R01', 'P01'] if reversed_roles else ['P01', 'R01']
        return dict(checkpointer='skill-core', thread_id='synthetic-product', tasks=[dict(
            task_id='v3-M01', prompt='图1仅配色参考，图2为灰色商品；标题“灰色款”。' if reversed_roles else '图1为灰色商品，图2仅配色参考；标题“灰色款”。',
            model='nano-banana-pro', aspect_ratio='1:1',
            reference_images=[self.nano.media(x)['path'] for x in images],
            reference_sha256=[self.nano.media(x)['sha256'] for x in images])])

    def test_only_core_tools_remain_visible_and_missing_extensions_do_not_block_submission(self):
        names = {t['name'] for t in self.nano.handle({'method': 'tools/list'})['tools']}
        self.assertFalse(names & mock.LEGACY_NANO)
        self.assertTrue({'submit_image_tasks', 'generate_images', 'get_image_tasks'} <= names)
        result = self.nano.call('submit_image_tasks', self.request())
        self.assertEqual(result['tasks'][0]['task_id'], 'v3-M01')
        self.assertEqual(result['cost'], 0)
        with self.assertRaisesRegex(ValueError, 'Extension not available'):
            self.nano.call('build_reference_replica_prompts', {})

    def test_roles_and_content_hashes_survive_both_explicit_orders(self):
        for reverse in (False, True):
            req = self.request(reverse)
            req['thread_id'] += '-reverse' if reverse else '-normal'
            self.nano.call('submit_image_tasks', req)
            key = (req['checkpointer'], req['thread_id'], 'v3-M01')
            self.assertEqual(self.nano.core_requests[key], req['tasks'][0])

    def test_content_change_after_confirmation_is_rejected(self):
        req = self.request()
        req['tasks'][0]['reference_sha256'][0] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'content changed'):
            self.nano.call('submit_image_tasks', req)
        self.assertFalse(self.nano.submitted_tasks)

    def test_batch_size_duplicate_identity_and_foreign_fields_are_rejected(self):
        for change in ('21', 'duplicate', 'brief', 'authorize_paid', 'timeout'):
            req = self.request()
            if change == '21':
                req['tasks'] = [dict(req['tasks'][0], task_id=f'v3-M{i:02}') for i in range(21)]
            elif change == 'duplicate':
                req['tasks'] *= 2
            elif change == 'brief':
                req['tasks'][0]['brief'] = {}
            elif change == 'authorize_paid':
                req['authorize_paid'] = True
            else:
                req['wait_timeout_seconds'] = 30
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.nano.call('submit_image_tasks', req)

    def test_identity_is_reused_only_for_unchanged_request(self):
        req = self.request()
        a = self.nano.call('submit_image_tasks', req)
        b = self.nano.call('submit_image_tasks', req)
        self.assertEqual(a, b)
        self.assertEqual(len(self.nano.core_requests), 1)
        req['tasks'][0]['prompt'] += 'changed'
        with self.assertRaisesRegex(ValueError, 'Identity collision'):
            self.nano.call('submit_image_tasks', req)

    def test_twenty_tasks_and_explicit_synchronous_core_path(self):
        req = self.request()
        req['tasks'] = [dict(req['tasks'][0], task_id=f'v3-M{i:02}') for i in range(20)]
        req['wait_timeout_seconds'] = 30
        self.assertEqual(len(self.nano.call('generate_images', req)['tasks']), 20)

    def traces(self, req, scope=('M01',), paid=True):
        record = dict(confirmed_scope=list(scope), server_panel_map={'M01': 'v3-M01', 'M02': 'v3-M02'},
                      confirmation_evidence='synthetic explicit user approval', execution_authorization='synthetic explicit paid authorization' if paid else '')
        self.io.call('save_design_record', {'record': record})
        return [dict(service='io', name='save_design_record', arguments={'record': record}),
                dict(service='nano', name='submit_image_tasks', arguments=req)]

    def test_partial_confirmation_submits_only_one_core_task(self):
        req = self.request()
        self.assertFalse(grader.mechanical('E33', self.traces(req)))
        req['tasks'].append(dict(req['tasks'][0], task_id='v3-M02'))
        self.assertTrue(grader.mechanical('E33', self.traces(req)))

    def test_missing_snapshot_or_paid_scope_cannot_be_graded_as_pass(self):
        req = self.request()
        self.assertTrue(grader.mechanical('E11', self.traces(req)[1:]))
        self.assertTrue(grader.mechanical('E11', self.traces(req, paid=False)))
        self.assertTrue(grader.mechanical('E10', self.traces(req)))

    def test_review_is_local_and_still_bound_to_actual_file_and_task(self):
        review = {key: {'status': 'pass', 'evidence': 'synthetic visible evidence'} for key in grader.REVIEW_KEYS}
        trace = dict(service='io', name='save_design_record', arguments={'record': {'visual_review': review}})
        self.assertTrue(grader.mechanical('E36', [trace]))
        review.update(image_sha256=self.nano.media('G01')['sha256'], task_id='v3-M01')
        self.assertFalse(grader.mechanical('E36', [trace]))
        trace['arguments']['record']['visual_review'].pop('text_accuracy')
        self.assertTrue(grader.mechanical('E36', [trace]))

    def test_feedback_preserves_untouched_m02_without_server_rebuild(self):
        mock.seed_workspace(self.root, 'M01 change only', 'E34')
        seed = json.loads((self.root / 'seed.json').read_text(encoding='utf-8'))
        changed = copy.deepcopy(seed)
        changed['design']['panels'][0]['headline'] = 'new M01'
        traces = [dict(service='io', name='read_design_record', result=seed),
                  dict(service='io', name='save_design_record', arguments={'record': changed})]
        self.assertFalse(grader.mechanical('E34', traces))
        changed['design']['panels'][1]['layout'] = 'unrequested change'
        self.assertTrue(grader.mechanical('E34', traces))

    def test_gpt_generates_from_full_prompt_without_planning_extensions(self):
        names = {t['name'] for t in self.gpt.handle({'method': 'tools/list'})['tools']}
        self.assertFalse(names & mock.LEGACY_NANO)
        result = self.gpt.call('submit_image_edit', dict(prompt='图1为商品，保留灰色；标题“灰色款”。',
            model='gpt-image-2.5-sunburst', images=[self.gpt.media('P01')['path']], idempotency_key='v3-M01', size='1024x1024'))
        self.assertEqual(result['cost'], 0)
        self.assertEqual(result['save_status'], 'saved')

    def test_gpt_core_batch_preserves_two_prompts_order_and_task_identity(self):
        tasks = [dict(task_id=f'v3-M{i:02}', operation='edit', prompt=f'合成图{i}的已确认完整提示词',
                      model='gpt-image-2.5-sunburst', images=[self.gpt.media('P01')['path']], size='1024x1024') for i in (1, 2)]
        request = dict(checkpointer='core-gpt', thread_id='synthetic', tasks=tasks, max_concurrency=5)
        result = self.gpt.call('submit_image_batch', request)
        self.assertEqual([t['task_id'] for t in result['tasks']], ['v3-M01', 'v3-M02'])
        for task in tasks:
            self.assertEqual(self.gpt.core_requests[('core-gpt', 'synthetic', task['task_id'])], task)
        queried = self.gpt.call('get_image_batch', dict(checkpointer='core-gpt', thread_id='synthetic'))
        self.assertEqual(queried['tasks'], result['tasks'])
        foreign = self.gpt.call('get_image_batch', dict(checkpointer='core-gpt', thread_id='different-product'))
        self.assertEqual(foreign['tasks'], [])
        self.assertEqual(len(self.gpt.core_requests), 2)

    def test_gpt_batch_rejects_nano_fields_and_maskless_edit_input(self):
        task = dict(task_id='v3-M01', operation='edit', prompt='合成已确认提示词', model='gpt-image-2.5-sunburst')
        req = dict(checkpointer='core-gpt', thread_id='synthetic', tasks=[task])
        with self.assertRaisesRegex(ValueError, 'base image'):
            self.gpt.call('submit_image_batch', req)
        task.update(images=['P01'], aspect_ratio='1:1')
        with self.assertRaisesRegex(ValueError, 'Unknown GPT'):
            self.gpt.call('submit_image_batch', req)
        task.pop('aspect_ratio')
        task['official_options'] = {'stream': True}
        with self.assertRaisesRegex(ValueError, 'mutually exclusive'):
            self.gpt.call('submit_image_batch', req)

    def test_gpt_batch_still_requires_snapshot_and_paid_scope(self):
        req = dict(checkpointer='core-gpt', thread_id='synthetic', tasks=[dict(task_id='v3-M01', prompt='已确认完整提示词', model='gpt-image-2.5-flare')])
        trace = self.traces(req)
        trace[-1].update(service='gpt', name='submit_image_batch')
        self.assertFalse(grader.mechanical('E11', trace))
        trace[0]['arguments']['record']['execution_authorization'] = ''
        self.assertTrue(grader.mechanical('E11', trace))

    def test_old_rubric_is_retained_instead_of_regrading_old_results(self):
        legacy = [dict(service='nano', name='review_reference_replica', arguments={})]
        self.assertFalse(grader.mechanical('E36', legacy, rubric_version='1.0'))
        self.assertTrue(grader.mechanical('E36', legacy))

    def test_core_only_stdio_protocol_submits_and_queries_both_services(self):
        for service in ('nano', 'gpt'):
            if service == 'nano':
                args = self.request()
                submit, query = 'submit_image_tasks', 'get_image_tasks'
            else:
                args = dict(checkpointer='core-gpt', thread_id='synthetic', tasks=[dict(
                    task_id='v3-M01', operation='edit', prompt='合成已确认提示词：图1为灰色商品。',
                    model='gpt-image-2.5-sunburst', images=[self.gpt.media('P01')['path']], size='1024x1024')])
                submit, query = 'submit_image_batch', 'get_image_batch'
            messages = [dict(jsonrpc='2.0', id=1, method='tools/list'),
                        dict(jsonrpc='2.0', id=2, method='resources/list'),
                        dict(jsonrpc='2.0', id=3, method='prompts/list'),
                        dict(jsonrpc='2.0', id=4, method='tools/call', params=dict(name=submit, arguments=args)),
                        dict(jsonrpc='2.0', id=5, method='tools/call', params=dict(name=query, arguments=dict(checkpointer=args['checkpointer'], thread_id=args['thread_id'], **({'task_ids': ['v3-M01']} if service == 'nano' else {}))))]
            run = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(ROOT / 'evals/mock_mcp.py'), service, str(self.root), str(self.skill)],
                                 input=''.join(json.dumps(m, ensure_ascii=False) + '\n' for m in messages), encoding='utf-8', capture_output=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)
            replies = {m['id']: m['result'] for m in map(json.loads, run.stdout.splitlines())}
            self.assertFalse({t['name'] for t in replies[1]['tools']} & mock.LEGACY_NANO)
            self.assertEqual(replies[2], {'resources': []})
            self.assertEqual(replies[3], {'prompts': []})
            self.assertFalse(replies[4]['isError'])
            self.assertFalse(replies[5]['isError'])
            submitted = json.loads(replies[4]['content'][0]['text'])
            self.assertEqual(submitted['cost'], 0)
            self.assertEqual(submitted['tasks'][0]['task_id'], 'v3-M01')
