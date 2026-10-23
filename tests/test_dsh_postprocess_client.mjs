import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,mkdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {postprocessTrial} from '../scripts/dsh_postprocess_client.mjs';

test('coordinator uses child output and retains raw failures separately',async()=>{
 const root=await mkdtemp(join(tmpdir(),'dsh-postprocessing-'));
 try{
  await mkdir(join(root,'orchestrator-source'));
  const script=join(root,'orchestrator-source','dsh_postprocess_trial.py');
  await writeFile(script,'import json, sys\nprint(json.dumps(dict(version=1, trial=sys.argv[-1], raw_passed=False, candidate_valid=True, pipeline_passed=True)))\n');
  const result=await postprocessTrial(process.env.DSH_TEST_PYTHON??resolve('.venv/Scripts/python.exe'),root,'sol-explicit-r1');
  assert.equal(result.pipeline_passed,true);
  assert.equal(result.raw_passed,false);
  assert.equal(result.candidate_valid,true);
  await writeFile(script,'print("not a protocol result")\n');
  const malformed=await postprocessTrial(process.env.DSH_TEST_PYTHON??resolve('.venv/Scripts/python.exe'),root,'sol-explicit-r1');
  assert.equal(malformed.pipeline_passed,false);
 }finally{await rm(root,{recursive:true,force:true});}
});

test('missing interpreter is a pipeline failure without a fallback',async()=>{
 const root=await mkdtemp(join(tmpdir(),'dsh-postprocessing-'));
 try{
  const result=await postprocessTrial(join(root,'missing-python.exe'),root,'sol-explicit-r1');
  assert.equal(result.pipeline_passed,false);
  assert.match(result.error,/process failed/);
 }finally{await rm(root,{recursive:true,force:true});}
});
