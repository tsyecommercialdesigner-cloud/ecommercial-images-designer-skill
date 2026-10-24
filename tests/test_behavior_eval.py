"""Test the evaluation machinery, not textual compliance of the skill."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('grader',REPO/'scripts/grade_behavior_eval.py')
grader=importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
summary_spec=importlib.util.spec_from_file_location('summary',REPO/'scripts/summarize_behavior_eval.py')
summary=importlib.util.module_from_spec(summary_spec)
summary_spec.loader.exec_module(summary)


class BehaviorHarnessTests(unittest.TestCase):
    def test_protocol_utf8_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'E01-r1'
            grader.runner.mock.seed_workspace(root,'无图片','E01')
            request={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'read_skill_resource','arguments':{'path':'SKILL.md'}}}
            result=subprocess.run([sys.executable,str(grader.runner.MOCK),'io',str(root),str(REPO/'.agents/skills/ecommerce-image-designer')],input=json.dumps(request)+'\n',encoding='utf-8',capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            response=json.loads(result.stdout)
            self.assertEqual(response['id'],1)
            self.assertIn('电商',response['result']['content'][0]['text'])

    def test_new_generation_does_not_inherit_pending_task(self):
        with tempfile.TemporaryDirectory() as temp:
            grader.runner.mock.seed_workspace(Path(temp),'新生成','E11')
            self.assertNotIn('pending_task',json.loads((Path(temp)/'seed.json').read_text(encoding='utf-8')))

    def test_blocked_attempt_is_still_a_failure(self):
        calls=[{'service':'nano','name':'submit_ecommerce_design','arguments':{},'error':'blocked'}]
        self.assertTrue(grader.mechanical('E33',calls))

    def test_e11_requires_one_submission(self):
        self.assertTrue(grader.mechanical('E11',[]))
        call={'service':'gpt','name':'submit_image_edit','arguments':{}}
        snapshot={'service':'io','name':'save_design_record','arguments':{}}
        self.assertTrue(grader.mechanical('E11',[call]))
        self.assertFalse(grader.mechanical('E11',[snapshot,call]))
        self.assertTrue(grader.mechanical('E11',[snapshot,call,call]))

    def test_partial_approval_cannot_become_whole_version(self):
        self.assertTrue(grader.mechanical('E33',[{'service':'nano','name':'confirm_ecommerce_design','arguments':{'user_confirmed':True}}]))

    def test_preserved_second_panel_survives_guard(self):
        call={'service':'nano','name':'plan_ecommerce_design','arguments':{'edits':[{'panel_id':'p01','headline':'new'},{'panel_id':'p02','headline':'用户已定稿的M02标题','layout':'用户已定稿的左图右文布局'}]}}
        self.assertFalse(grader.mechanical('E34',[call],rubric_version='1.0'))
        call['arguments']['edits'].pop()
        self.assertTrue(grader.mechanical('E34',[call],rubric_version='1.0'))

    def test_unrun_cases_cannot_pass(self):
        result=summary.summarize([], [{'id':'E01'}])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['scored_trials'],0)

    def test_incomplete_regression_cannot_cherry_pick_old_success(self):
        with tempfile.TemporaryDirectory() as temp:
            old,new=Path(temp)/'old',Path(temp)/'new'
            for root,count in ((old,3),(new,1)):
                root.mkdir()
                rows=[]
                for repeat in range(1,count+1):
                    tid=f'E01-r{repeat}';work=root/tid;work.mkdir()
                    (work/'trial.json').write_text(json.dumps(dict(trial_id=tid,repeat=repeat,status='completed')))
                    rows.append(dict(trial_id=tid,routing=2,evidence=2,boundaries=2,critical_failure=False))
                (root/'grades.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
            self.assertTrue(summary.summarize([old],[{'id':'E01'}])['accepted'])
            result=summary.summarize([old,new],[{'id':'E01'}])
            self.assertFalse(result['accepted'])
            self.assertEqual(result['cases'][0]['run'],str(new))


if __name__=='__main__':unittest.main()
