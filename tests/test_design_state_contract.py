"""Independent evidence and mutation cases for provenance/status/frozen scope."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py'
spec = importlib.util.spec_from_file_location('design_contract', SCRIPT)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def fixture(mode='revision'):
    baseline = dict.fromkeys(contract.BASE)
    images = [{'id': 'asset-27', 'source': 'asset.png', 'role': 'product', 'provenance': 'unknown', 'reference_use': 'none'},
              {'id': 'look-93', 'source': 'look.png', 'role': 'reference', 'provenance': 'unknown', 'reference_use': 'style'}]
    facts = [{'id': 'evidence-4', 'text': '蓝色外壳', 'source': 'record'}]
    evidence = dict(mode=mode, baseline=baseline, images=images, facts=facts,
                    locked_images=['accepted-5'], edit_images=['revise-2'], capabilities=[])
    state = copy.deepcopy(evidence)
    del state['mode']
    for row in state['images']:
        row.update(drawing_use='undecided', input_index=None)
    record = dict(contract=contract.CONTRACT_ID, mode=mode, validation='pending', state=state,
                  proposal=dict(canvas=None, copy=dict.fromkeys(('title', 'subtitle', 'labels', 'footnote')),
                                layout=[dict(element='title', region=dict(x=8, y=6, width=84, height=16), align='left',
                                             max_lines=2, if_present=False, overflow='reflow_preserve_all_copy')],
                                appearance=dict.fromkeys(('background', 'typography', 'lighting')), reference_style=[]),
                  next=dict(rollback_stage='S2' if mode == 'revision' else None, stage='S3', confirm_images=['revise-2'], missing_fields=['title'], execution='not_authorized'))
    return record, evidence


class DesignStateTests(unittest.TestCase):
    def test_valid_revision_is_generic_and_render_keeps_exact_state(self):
        record, evidence = fixture()
        contract.validate(record, evidence)
        rendered = contract.render(record).split('```json\n', 1)[1].rsplit('\n```', 1)[0]
        self.assertEqual(json.loads(rendered), record)

    def test_known_source_may_be_recorded_only_with_independent_evidence(self):
        record, evidence = fixture()
        record['state']['images'][1]['provenance'] = 'photo'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            contract.validate(record, evidence)
        evidence['images'][1]['provenance'] = 'photo'
        contract.validate(record, evidence)

    def test_role_is_not_image_provenance(self):
        record, evidence = fixture()
        record['state']['images'][0]['provenance'] = 'synthetic'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            contract.validate(record, evidence)

    def test_swapping_source_files_does_not_swap_roles(self):
        record, evidence = fixture()
        record['state']['images'][0]['source'] = 'look.png'
        with self.assertRaisesRegex(ValueError, 'source reference'):
            contract.validate(record, evidence)

    def test_free_queries_do_not_prove_readiness_history_or_model_association(self):
        record, evidence = fixture('status')
        for state in (record['state'], evidence):
            state.update(images=[], facts=[], locked_images=[], edit_images=[])
        cap = dict(server='zhenzhen-nanobanana-mcp', query_tool='actual-local-query', models=['native-model'],
                   query_succeeded=True, configured=True, upstream='not_tested', performance='not_tested')
        record['state']['capabilities'] = [cap]
        evidence['capabilities'] = [copy.deepcopy(cap)]
        record['proposal'] = None
        record['next'].update(stage='S0', confirm_images=[], missing_fields=['product_image'])
        contract.validate(record, evidence)
        for field, bad in [('upstream', 'never_verified'), ('upstream', 'ready'),
                           ('performance', 'fastest'), ('models', ['foreign-model']), ('configured', False)]:
            changed = copy.deepcopy(record)
            changed['state']['capabilities'][0][field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                contract.validate(changed, evidence)

    def test_confirmation_cannot_expand_into_frozen_scope(self):
        record, evidence = fixture()
        record['next']['confirm_images'].append('accepted-5')
        with self.assertRaisesRegex(ValueError, 'Frozen'):
            contract.validate(record, evidence)

    def test_cannot_drop_lock_or_reclassify_it_as_missing_field(self):
        for mutate in (lambda r: r['state'].update(locked_images=[]),
                       lambda r: r['next']['missing_fields'].append('locked_images')):
            record, evidence = fixture()
            mutate(record)
            with self.assertRaises(ValueError):
                contract.validate(record, evidence)

    def test_no_free_summary_or_questions_can_bypass_single_state(self):
        for field in ('summary', 'questions', 'prompt'):
            record, evidence = fixture()
            record[field] = 'Is accepted-5 still frozen?'
            with self.assertRaisesRegex(ValueError, 'closed fields'):
                contract.validate(record, evidence)

    def test_unknown_baseline_and_copy_cannot_be_filled_with_defaults(self):
        for field in ('kind', 'product_count', 'view', 'title'):
            record, evidence = fixture()
            record['state']['baseline'][field] = 'invented'
            with self.assertRaisesRegex(ValueError, 'Baseline'):
                contract.validate(record, evidence)
        record, evidence = fixture()
        record['proposal']['copy']['subtitle'] = 'new phrase'
        with self.assertRaisesRegex(ValueError, 'Original copy'):
            contract.validate(record, evidence)

    def test_local_revision_retains_actual_copy_and_overflow_cannot_delete(self):
        record, evidence = fixture()
        evidence['baseline']['subtitle'] = record['state']['baseline']['subtitle'] = '已有辅助原文'
        record['proposal']['copy']['subtitle'] = '已有辅助原文'
        contract.validate(record, evidence)
        record['proposal']['layout'][0]['overflow'] = 'drop_auxiliary_when_full'
        with self.assertRaisesRegex(ValueError, 'preserve'):
            contract.validate(record, evidence)

    def test_no_selected_entry_means_no_upload_or_index(self):
        for change in ({'input_index': 1}, {'drawing_use': 'upload'}):
            record, evidence = fixture()
            record['state']['images'][0].update(change)
            with self.assertRaises(ValueError):
                contract.validate(record, evidence)

    def test_style_only_reference_cannot_add_composition_field(self):
        record, evidence = fixture('plan')
        for state in (record['state'], evidence):
            state.update(locked_images=[], edit_images=[])
        record['next']['confirm_images'] = ['new-7']
        record['proposal']['reference_style'] = [dict(image_id='look-93', attribute='composition', value='center')]
        with self.assertRaisesRegex(ValueError, 'permission dimension'):
            contract.validate(record, evidence)

    def test_parser_rejects_extra_prose_duplicate_keys_and_nonfinite_values(self):
        for text in ('{}\nAll ready.', '{"mode":"status","mode":"plan"}', '{"value":NaN}'):
            with self.assertRaises(ValueError):
                contract.parse_answer(text)

    def test_cli_returns_nonzero_without_modifying_inputs(self):
        record, evidence = fixture()
        record['next']['confirm_images'] = ['accepted-5']
        with tempfile.TemporaryDirectory() as temp:
            path, source = Path(temp) / 'record.json', Path(temp) / 'source.json'
            path.write_text(json.dumps(record), encoding='utf-8')
            source.write_text(json.dumps(evidence), encoding='utf-8')
            before = (path.read_bytes(), source.read_bytes())
            result = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(SCRIPT), str(path), '--evidence', str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)['valid'])
            self.assertEqual(before, (path.read_bytes(), source.read_bytes()))

    def test_independently_grounded_fact_grouping_is_not_a_new_fact_license(self):
        record, evidence = fixture()
        # Revisions preserve exact record IDs; grouping alternatives are only
        # meaningful for a fresh plan whose source statement can be segmented.
        record['mode'] = evidence['mode'] = 'plan'
        record['next']['rollback_stage'] = None
        for state in (record['state'], evidence):
            state.update(locked_images=[], edit_images=[])
        record['next']['confirm_images'] = ['new-draft']
        evidence['fact_alternatives'] = [[dict(text='蓝色外壳和白色底座', source='user')]]
        record['state']['facts'] = [dict(id='new-fact', text='蓝色外壳和白色底座', source='user')]
        contract.validate(record, evidence)
        record['state']['facts'][0]['text'] = '防水外壳'
        with self.assertRaisesRegex(ValueError, 'Facts'):
            contract.validate(record, evidence)

    def test_single_prompt_cannot_confirm_multiple_images(self):
        record, evidence = fixture()
        record['state']['edit_images'].append('revise-3')
        evidence['edit_images'].append('revise-3')
        record['next']['confirm_images'].append('revise-3')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            contract.validate(record, evidence)

    def test_named_rectangles_reject_ambiguous_arrays_and_out_of_canvas(self):
        for region in ([8, 6, 92, 22], dict(x=95, y=5, width=10, height=20),
                       dict(x=8, y=6, width=84, height=0), dict(x=True, y=6, width=84, height=16)):
            record, evidence = fixture()
            record['proposal']['layout'][0]['region'] = region
            with self.subTest(region=region), self.assertRaises(ValueError):
                contract.validate(record, evidence)

    def test_new_planned_copy_is_not_unknown_original_auxiliary(self):
        record, evidence = fixture('plan')
        for state in (record['state'], evidence):
            state.update(locked_images=[], edit_images=[])
        record['next'].update(confirm_images=['new-one'], rollback_stage=None)
        record['proposal']['copy']['subtitle'] = '本轮新拟文案'
        row = copy.deepcopy(record['proposal']['layout'][0])
        row.update(element='subtitle', if_present=False)
        record['proposal']['layout'].append(row)
        contract.validate(record, evidence)

    def test_host_service_alias_and_short_method_still_bind_to_actual_query(self):
        record, evidence = fixture('status')
        for state in (record['state'], evidence):
            state.update(images=[], facts=[], locked_images=[], edit_images=[])
        cap = dict(server='zhenzhen-gptimagegen2.5-mcp', query_tool='mcp__zhenzhen-gptimagegen2-5-mcp__get_model_guide', models=['actual-id'],
                   query_succeeded=True, configured=True, upstream='not_tested', performance='not_tested')
        record['state']['capabilities'] = [copy.deepcopy(cap)]
        evidence['capabilities'] = [copy.deepcopy(cap)]
        record['proposal'] = None
        record['next'].update(stage='S0', confirm_images=[], missing_fields=['product_image'])
        record['state']['capabilities'][0].update(server='zhenzhen-gptimagegen2-5-mcp', query_tool='get_model_guide')
        contract.validate(record, evidence)
        for change in (dict(server='zhenzhen-nanobanana-mcp'), dict(query_tool='list_models'), dict(models=['foreign-id'])):
            bad = copy.deepcopy(record)
            bad['state']['capabilities'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                contract.validate(bad, evidence)

    def test_duplicate_service_alias_cannot_replace_a_second_service(self):
        record, evidence = fixture('status')
        for state in (record['state'], evidence):
            state.update(images=[], facts=[], locked_images=[], edit_images=[])
        caps = [dict(server='zhenzhen-gptimagegen2.5-mcp', query_tool='get_model_guide', models=['actual-id'], query_succeeded=True,
                     configured=True, upstream='not_tested', performance='not_tested'),
                dict(server='zhenzhen-nanobanana-mcp', query_tool='list_models', models=['other-id'], query_succeeded=True,
                     configured=True, upstream='not_tested', performance='not_tested')]
        evidence['capabilities'] = copy.deepcopy(caps)
        record['state']['capabilities'] = [copy.deepcopy(caps[0]), copy.deepcopy(caps[0])]
        record['state']['capabilities'][1]['server'] = 'zhenzhen-gptimagegen2-5-mcp'
        record['proposal'] = None
        record['next'].update(stage='S0', confirm_images=[], missing_fields=['product_image'])
        with self.assertRaisesRegex(ValueError, 'canonical'):
            contract.validate(record, evidence)

    def test_explicit_rollback_cannot_reopen_unrelated_stages(self):
        record, evidence = fixture()
        record['next']['rollback_stage'] = 'S0'
        with self.assertRaisesRegex(ValueError, 'Rollback'):
            contract.validate(record, evidence)


if __name__ == '__main__':
    unittest.main()
