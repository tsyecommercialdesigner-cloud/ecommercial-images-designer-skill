import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('mock_mcp',Path(__file__).resolve().parents[1]/'evals/mock_mcp.py')
mock=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)


class MockProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='mock-only-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'E33-r1'
        mock.seed_workspace(self.root,'只有 M01 获准，其余待定','E33')
        self.skill=Path(__file__).resolve().parents[1]/'.agents/skills/ecommerce-image-designer'
        self.nano=mock.MockServer('nano',self.root,self.skill)

    def test_protocol_discovery(self):
        self.assertEqual(self.nano.handle({'method':'initialize','params':{'protocolVersion':'2024-11-05'}})['protocolVersion'],'2024-11-05')
        tools=self.nano.handle({'method':'tools/list'})['tools']
        self.assertIn('confirm_ecommerce_design',{t['name'] for t in tools})

    def test_unapproved_submit_is_logged_and_denied(self):
        r=self.nano.handle({'method':'tools/call','params':{'name':'submit_ecommerce_design','arguments':{'design_id':'fixture-design','revision':3,'digest':'a'*64,'panel_ids':['p01'],'authorize_paid':True}}})
        self.assertTrue(r['isError'])
        self.assertIn('approved',json.loads((self.root/'calls.jsonl').read_text())['error'])

    def test_confirmation_approves_whole_mock_record(self):
        self.nano.call('confirm_ecommerce_design',dict(design_id='fixture-design',revision=3,digest='a'*64,confirmation_note='synthetic confirmation',user_confirmed=True))
        self.assertEqual(self.nano.design['status'],'approved')
        self.assertEqual(len(self.nano.design['panels']),5)

    def test_ordinary_get_is_not_prompt_export(self):
        with self.assertRaises(ValueError):self.nano.call('export_product_suite_prompts',{'design_id':'fixture-design'})

    def test_no_arbitrary_file_or_url_access(self):
        for source in ['C:/private/key.png','https://example.com/image.png']:
            with self.assertRaises(ValueError):self.nano.media(source)

    def test_equivalent_fixture_paths_preserve_whitelist(self):
        canonical=self.nano.media('P01')
        equivalent=str(self.root/'..'/self.root.name/'P01.png')
        self.assertEqual(self.nano.media(equivalent)['sha256'],canonical['sha256'])
        self.assertEqual(self.nano.media(str((self.root/'P01.png').resolve()))['path'],canonical['path'])
        with self.assertRaises(ValueError):self.nano.media(str(self.root/'..'/'private.png'))

    def test_plain_plan_rebuilds_panels(self):
        brief=self.nano.design['brief']
        new=self.nano.call('plan_ecommerce_design',{'design_id':'fixture-design','brief':brief,'expected_revision':3,'edits':[dict(panel_id='p01',headline='changed')]})
        self.assertEqual(new['panels'][1]['headline'],'默认标题')

    def test_mock_edit_produces_existing_fixture_only(self):
        gpt=mock.MockServer('gpt',self.root,self.skill)
        result=gpt.call('submit_image_edit',{'prompt':'fixture edit','model':'gpt-image-2.5-sunburst','images':[str(self.root/'P01.png')],'idempotency_key':'only-mock'})
        self.assertTrue(result['simulated'])
        self.assertEqual(result['cost'],0)
        self.assertTrue(Path(result['files'][0]['path']).is_relative_to(self.root.resolve()))

    def test_async_stream_is_rejected(self):
        gpt=mock.MockServer('gpt',self.root,self.skill)
        with self.assertRaises(ValueError):gpt.call('submit_image_edit',{'official_options':{'stream':True}})

    def test_review_requires_real_six_dimensions_and_current_file(self):
        self.root=Path(self.temp.name)/'E36-r1'
        mock.seed_workspace(self.root,'复刻结果待验收','E36')
        nano=mock.MockServer('nano',self.root,self.skill)
        args=dict(design_id='fixture-design',revision=3,task_id='T1',image_sha256=nano.media('G01')['sha256'],assessment={key:dict(status='pass',evidence='fixture observation') for key in mock.REVIEW_KEYS})
        self.assertEqual(nano.call('review_reference_replica',args)['outcome'],'agent_passed')
        args['assessment']['text_accuracy']=dict(status='uncertain',evidence='no visible glyphs',correction='check approved copy')
        self.assertEqual(nano.call('review_reference_replica',args)['outcome'],'needs_user_review')
        args['image_sha256']='0'*64
        with self.assertRaises(ValueError):nano.call('review_reference_replica',args)

    def test_unknown_submission_has_no_invented_task_id(self):
        root=Path(self.temp.name)/'E15-r1'
        mock.seed_workspace(root,'无task_id','E15')
        self.assertNotIn('task_id',json.loads((root/'seed.json').read_text(encoding='utf-8'))['pending_task'])

    def test_edit_mask_is_alpha_png_and_matches_base(self):
        root=Path(self.temp.name)/'E39-r1'
        mock.seed_workspace(root,'mask匹配底图','E39')
        data=(root/'mask.png').read_bytes()
        self.assertEqual(data[25],6)  # PNG color type RGBA
        self.assertEqual(data[16:24],(root/'G01.png').read_bytes()[16:24])

    def test_nano_approved_variant_keeps_plan_gate_and_task_namespace(self):
        root=Path(self.temp.name)/'E11-r1'
        mock.seed_workspace(root,'完整单图版已确认，尚未提交','E11',variant='nano-approved')
        nano=mock.MockServer('nano',root,self.skill)
        self.assertEqual(nano.call('get_ecommerce_design',{'design_id':'fixture-design'})['tasks'],[])
        export=nano.call('export_validated_reference_replica',{'design_id':'fixture-design'})
        self.assertEqual([i['role'] for i in export['prompts'][0]['input_images']],['style_only','product_identity'])
        args=dict(design_id='fixture-design',revision=3,digest='a'*64,panel_ids=['p01'],authorize_paid=True)
        with self.assertRaises(ValueError):nano.call('submit_ecommerce_design',args)
        nano.call('confirm_ecommerce_design',dict(design_id='fixture-design',revision=3,digest='a'*64,user_confirmed=True,confirmation_note='simulated r3/M01 approval'))
        result=nano.call('submit_ecommerce_design',args)
        self.assertEqual(result['checkpointer'],'ecommerce-design')
        self.assertEqual(result['thread_id'],'fixture-design')
        self.assertEqual(result['tasks'][0]['task_id'],'r3-p01')
        self.assertEqual(nano.call('get_ecommerce_design',{'design_id':'fixture-design'})['tasks'],result['tasks'])
        review=nano.call('review_reference_replica',dict(design_id='fixture-design',revision=3,task_id='r3-p01',image_sha256=nano.media('G01')['sha256'],assessment={key:dict(status='pass',evidence='synthetic observation') for key in mock.REVIEW_KEYS}))
        self.assertEqual(review['task_id'],'r3-p01')


if __name__=='__main__':unittest.main()
