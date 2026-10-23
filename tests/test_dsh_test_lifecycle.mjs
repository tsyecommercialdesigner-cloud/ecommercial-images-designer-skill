import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createOwnedTestAgent,releaseOwnedTestAgent} from '../scripts/dsh_test_lifecycle.mjs';
const id='session-76d8-12345678-1234-1234-1234-123456789abc';
function fixture({corrupt=false,disposeFails=false}={}){
  const agents=new Map(),sessions=new Map(),disk=new Map();let disposed=0;
  const ctx={agents:{get:k=>agents.get(k),create:async options=>{
    await options.setup();const events=[{type:'turn/end',data:{reason:{kind:'completed'}}}];
    const agent={session:{header:{id:options.sessionId,...options.meta},snapshotEvents:()=>structuredClone(events)}};
    agents.set(options.sessionId,agent);sessions.set(options.sessionId,agent.session);
    return {agent,dispose:async()=>{disposed++;if(disposeFails)throw Error('flush failed');
      disk.set(options.sessionId,{session:agent.session.header,events:corrupt?[]:events});
      agents.delete(options.sessionId);sessions.delete(options.sessionId);}};
  }},sessions:{get:k=>sessions.get(k)},sessionController:{commands:{agents:{
    composeAgent:async()=>({agentPreset:'standard',setup:async()=>{}}),agentOptions:()=>({provider:'existing'})}}},
    sessionQuery:{readSession:async k=>structuredClone(disk.get(k))}};
  return {ctx,agents,disk,get disposed(){return disposed;}};
}
test('release unregisters runtime while cold history remains readable',async()=>{
  const f=fixture();await createOwnedTestAgent(f.ctx,id,'E:/fixture','run-a');
  const result=await releaseOwnedTestAgent(f.ctx,id,'E:/fixture','run-a');
  assert.equal(result.persisted,true);assert.equal(result.persistedEvents,1);
  assert.equal(f.agents.size,0);assert.equal(f.disk.size,1);assert.equal(f.disposed,1);
});
test('foreign owner or cwd cannot release an agent',async()=>{
  const f=fixture();await createOwnedTestAgent(f.ctx,id,'E:/fixture','run-a');
  await assert.rejects(releaseOwnedTestAgent(f.ctx,id,'E:/fixture','run-b'),/matching/);
  await assert.rejects(releaseOwnedTestAgent(f.ctx,id,'E:/other','run-a'),/matching/);
  assert.equal(f.disposed,0);assert.equal(f.agents.size,1);
  await assert.rejects(createOwnedTestAgent(f.ctx,id,'E:/fixture','run-a'),/existing/);
});
test('lost persistent events and failed flush cannot be reported as release success',async()=>{
  for(const options of [{corrupt:true},{disposeFails:true}]){
    const f=fixture(options);await createOwnedTestAgent(f.ctx,id,'E:/fixture','run-a');
    await assert.rejects(releaseOwnedTestAgent(f.ctx,id,'E:/fixture','run-a'),/history|flush/);
  }
});
