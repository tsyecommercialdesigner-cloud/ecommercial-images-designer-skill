import {test} from 'node:test';
import assert from 'node:assert/strict';
import {classifyTrial} from '../scripts/dsh_trial_status.mjs';

test('only a completed turn with a nonempty answer succeeds',()=>{
  assert.equal(classifyTrial({reason:{kind:'completed'}},'answer').status,'completed');
  assert.equal(classifyTrial({reason:{kind:'completed'}},' \n').status,'failed');
});
test('error, cancellation and absent terminal reason remain failures',()=>{
  for(const kind of ['error','cancelled']){
    const result=classifyTrial({reason:{kind,error:{message:'upstream overload'}}},'partial text');
    assert.equal(result.status,'failed');assert.match(result.error,new RegExp(kind));
  }
  assert.equal(classifyTrial(undefined,'partial text').status,'failed');
});
