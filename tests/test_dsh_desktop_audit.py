import copy
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile

spec = importlib.util.spec_from_file_location('dsh_audit', Path(__file__).resolve().parents[1] / 'scripts/audit_dsh_desktop_smoke.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class DesktopAuditTests(unittest.TestCase):
    def setUp(self):
        self.route = {'provider': 'codeproxy-openai', 'model': 'gpt-6.1-sol'}
        self.trace = {'events': [
            {'type': 'request/header', 'data': {'header': {'config': self.route}}},
            {'type': 'turn/end', 'data': {'reason': {'kind': 'completed'}}}], 'audit': []}

    def test_negative_case_passes_but_wrong_route_fails(self):
        self.assertEqual(audit.check_trace(self.trace, 'negative', self.route)['tool_calls'], 0)
        with self.assertRaisesRegex(ValueError, 'actual model'):
            audit.check_trace(self.trace, 'negative', self.route | {'model': 'other'})

    def test_host_discovery_is_counted_separately_from_negative_business_work(self):
        trace = copy.deepcopy(self.trace)
        trace['events'].extend([
            {'type': 'tool/call', 'data': {'name': 'list_agents', 'callId': 'host', 'arguments': '{}'}},
            {'type': 'tool/result', 'data': {'message': {'toolCallId': 'host', 'content': []}}}])
        row = audit.check_trace(trace, 'negative', self.route)
        self.assertEqual(row['host_discovery_calls'], 1)
        self.assertEqual(row['business_tool_calls'], 0)
        for args in ('[]', 'null', '{"sessionId":"foreign"}'):
            bad = copy.deepcopy(trace)
            bad['events'][-2]['data']['arguments'] = args
            with self.assertRaisesRegex(ValueError, 'empty arguments'):
                audit.check_trace(bad, 'negative', self.route)

    def test_other_team_tools_do_not_become_host_discovery(self):
        for name in ('spawn_teammate', 'send_message', 'interrupt_agent', 'wait_agent'):
            trace = self.recovery_trace(['design-record.json'])
            trace['events'].extend([
                {'type': 'tool/call', 'data': {'name': name, 'callId': 'team', 'arguments': '{}'}},
                {'type': 'tool/result', 'data': {'message': {'toolCallId': 'team', 'content': []}}}])
            with self.assertRaisesRegex(ValueError, 'Unauthorized'):
                audit.check_trace(trace, 'recovery', self.route)

    def test_guarded_attempt_is_failure_even_with_successful_turn(self):
        self.trace['audit'].append({'phase': 'model', 'name': 'generate', 'allowed': False})
        with self.assertRaisesRegex(ValueError, 'rejected'):
            audit.check_trace(self.trace, 'negative', self.route)

    def test_guard_preflight_is_not_counted_as_model_attempt(self):
        self.trace['audit'].append({'phase': 'preflight', 'name': 'generate', 'allowed': False})
        self.assertEqual(audit.check_trace(self.trace, 'negative', self.route)['mcp_calls'], 0)

    def test_cancelled_turn_or_missing_tool_result_is_failure(self):
        cancelled = copy.deepcopy(self.trace)
        cancelled['events'][-1]['data']['reason']['kind'] = 'cancelled'
        with self.assertRaisesRegex(ValueError, 'normally'):
            audit.check_trace(cancelled, 'negative', self.route)
        self.trace['events'].insert(1, {'type': 'tool/call', 'data': {'name': 'skill', 'callId': 'missing'}})
        with self.assertRaisesRegex(ValueError, 'tool result'):
            audit.check_trace(self.trace, 'negative', self.route)

    def recovery_trace(self, paths):
        trace = copy.deepcopy(self.trace)
        for i, (name, args) in enumerate([('skill', {'name': 'ecommerce-image-designer'})] +
                                         [('read', {'file_path': p}) for p in paths]):
            trace['events'].extend([
                {'type': 'tool/call', 'data': {'name': name, 'callId': str(i), 'arguments': json.dumps(args)}},
                {'type': 'tool/result', 'data': {'message': {'toolCallId': str(i), 'content': []}}}])
        return trace

    def test_recovery_rejects_unrelated_successful_reads(self):
        for unrelated in ('README.md', 'P01.png', 'other/design-record.json',
                          '.agents/skills/ecommerce-image-designer/reference/mcp-adapters.md'):
            with self.subTest(unrelated=unrelated), self.assertRaisesRegex(ValueError, 'outside'):
                audit.check_trace(self.recovery_trace(['design-record.json', unrelated]), 'recovery', self.route)

    def test_recovery_accepts_windows_paths_and_stage_resources(self):
        root = r'E:\fixture\recovery'
        paths = [root + r'\\design-record.json',
                 root + r'\.agents\skills\ecommerce-image-designer\reference\design-record.md']
        self.assertEqual(audit.check_trace(self.recovery_trace(paths), 'recovery', self.route, root)['tool_calls'], 3)

    def test_old_snapshot_layout_is_audited_without_allowing_mixed_paths(self):
        parent = Path(__file__).resolve().parents[1] / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            root = Path(temp)
            package = root / '.agents/skills/ecommerce-image-designer'
            (package / 'references').mkdir(parents=True)
            old = '.agents/skills/ecommerce-image-designer/references/design-record.md'
            new = old.replace('/references/', '/reference/')
            self.assertEqual(audit.check_trace(self.recovery_trace(['design-record.json', old]),
                                              'recovery', self.route, root)['tool_calls'], 3)
            with self.assertRaisesRegex(ValueError, 'outside'):
                audit.check_trace(self.recovery_trace(['design-record.json', new]), 'recovery', self.route, root)
            (package / 'reference').mkdir()
            with self.assertRaisesRegex(ValueError, 'Ambiguous'):
                audit.check_trace(self.recovery_trace(['design-record.json', old]), 'recovery', self.route, root)

    def test_contract_resource_is_relevant_only_for_new_contract_and_does_not_allow_other_reads(self):
        resource = '.agents/skills/ecommerce-image-designer/reference/state-contract.md'
        trace = self.recovery_trace(['design-record.json', resource])
        with self.assertRaisesRegex(ValueError, 'outside'):
            audit.check_trace(trace, 'recovery', self.route)
        self.assertEqual(audit.check_trace(trace, 'recovery', self.route, contract=True)['tool_calls'], 3)
        for path in ('README.md', '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py',
                     '.agents/skills/ecommerce-image-designer/reference/review-and-revision.md',
                     '.agents/skills/ecommerce-image-designer/reference/planning-and-prompts.md'):
            with self.assertRaisesRegex(ValueError, 'outside'):
                audit.check_trace(self.recovery_trace(['design-record.json', resource, path]), 'recovery', self.route, contract=True)

    def test_failure_metrics_keep_images_returned_before_later_error(self):
        trace = copy.deepcopy(self.trace)
        trace['events'].extend([
            {'type': 'tool/call', 'data': {'name': 'mcp__fixture', 'callId': 'images'}},
            {'type': 'tool/result', 'data': {'message': {'toolCallId': 'images', 'content': [{'type': 'image'}] * 2}}},
            {'type': 'tool/call', 'data': {'name': 'read', 'callId': 'error'}},
            {'type': 'tool/result', 'data': {'message': {'toolCallId': 'error', 'content': [], 'isError': True}}}])
        self.assertEqual(audit.trace_metrics(trace)['image_blocks'], 2)
        with self.assertRaisesRegex(ValueError, 'tool result'):
            audit.check_trace(trace, 'implicit', self.route)
