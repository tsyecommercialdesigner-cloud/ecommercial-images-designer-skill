/** Installed DSH Desktop 0.2.1-rc.2 integration; no image-generation capability. */
import {readFile,writeFile,stat} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {randomUUID,createHash} from 'node:crypto';
import {homedir} from 'node:os';
import {connectDesktop} from './dsh_desktop_client.mjs';
import {createFreeGuardPolicy} from './dsh_free_guard.mjs';
import {classifyTrial} from './dsh_trial_status.mjs';
import {createOwnedTestAgent,releaseOwnedTestAgent} from './dsh_test_lifecycle.mjs';
import {postprocessTrial} from './dsh_postprocess_client.mjs';

const root=resolve(process.argv[2]??'');
if(!process.argv[2] || !root.includes('dsh-skill-host-76d8-'))throw Error('Explicit prepared external evidence root required');
const before=JSON.parse(await readFile(join(root,'before.json'),'utf8'));
const python=resolve(process.argv[3]??'');
if(!process.argv[3]||!(await stat(python)).isFile())throw Error('Pass the existing Python executable explicitly; no runtime installation');
if(!before.orchestrator_manifest)throw Error('Prepare a new root with frozen postprocessing sources');
for(const [name,digest] of Object.entries(before.orchestrator_manifest)){
 if(createHash('sha256').update(await readFile(join(root,'orchestrator-source',name))).digest('hex')!==digest)throw Error('Frozen orchestrator source mismatch');
}
const routes={sonnet:{provider:'codeproxy-anthropic',model:'claude-sonnet-5-5'},sol:{provider:'codeproxy-openai',model:'gpt-6.1-sol'}};
const cases={
 explicit:'使用 ecommerce-image-designer 技能。首次为收纳盒做电商主图，目前没有图片。只先讨论，不出图。请实际免费查询两个指定 MCP 的模型/配置状态，给出下一步。',
 implicit:'为附件所示盒子策划一张电商主图，先给文案排版和完整提示词草案，不出图。这里是集成测试：第一张是合成商品外观夹具 P01，第二张 R01 只作风格参考，禁止借用其商品颜色和布局。事实仅限灰色盒体和深灰盖沿，不要推断材质、容量或性能。请通过免费 MCP 实际查看两张图片。',
 negative:'只帮我拟一份学习 Python 的三天计划，每天半小时。没有电商或图片需求。',
 recovery:'读取 design-record.json 恢复这份合成测试设计。用户已接受 M01，M02 反馈是标题区太挤，请给具体调整布局及相应完整提示词草案，商品、事实和 M01 不变。只改方案，不出图；说明回退到哪一步以及还须确认什么。',
};
const client=await connectDesktop();
const lifecycleOwner=randomUUID();
let lifecycleFailed=false;
const runtime=await client.evaluate('return {execPath:process.execPath,node:process.versions.node,electron:process.versions.electron};');
const runtimeAgentsBefore=await client.evaluate('return ctx.agents.list().map(a=>a.id);');
if(!runtime.execPath.endsWith('DeepSeek Harness.exe'))throw Error('Target is not the installed Desktop Host');
const catalog=await client.call('session/modelCatalog');
for(const route of Object.values(routes))if(!catalog.groups.some(g=>g.id===route.provider && g.models.some(m=>m.id===route.model)))throw Error('Requested model unavailable');
const manifest={runtime,routes,cases:Object.keys(cases),repeats:1,workers:2,origin:client.origin,
  desktopProfile:true,mockMcp:false,syntheticInputs:true,paidImageToolsAllowed:false,
  gatePolicy:{version:2,hostDiscovery:['list_agents'],teamMutationAllowed:false},
  previousDefault:catalog.default,skillManifest:before.skill_manifest,
  outputContract:before.output_contract??(before.skill_manifest['.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py']?'ecommerce-design-state/v1':null),
  lifecycleVersion:1,postprocessingVersion:1,orchestratorManifest:before.orchestrator_manifest,
  python,runtimeAgentsBefore,results:[]};
await writeFile(join(root,'run.json'),JSON.stringify(manifest,null,2),{flag:'wx'});

async function trial(modelKey,caseKey){
 const work=join(root,`${modelKey}-${caseKey}-r1`);
 const sessionId='session-76d8-'+randomUUID();
 const started=Date.now();let accepted=false;let owned=false;
 const record={modelKey,case:caseKey,sessionId,route:routes[modelKey]};
 try{
  await stat(join(work,'.agents/skills/ecommerce-image-designer/SKILL.md'));
  record.created=await client.evaluate(`return await (${createOwnedTestAgent.toString()})(ctx,${JSON.stringify(sessionId)},${JSON.stringify(work)},${JSON.stringify(lifecycleOwner)});`);
  owned=true;
  await writeFile(join(work,'identity.json'),JSON.stringify(record,null,2),{flag:'wx'});
  if(caseKey==='implicit'){
   // Use the same attachment admission as session/prompt before installing the
   // byte-verified alias guard; do not rely on an earlier test's cache.
   const images=[];
   for(const name of ['P01.png','R01.png'])images.push({type:'image',mediaType:'image/png',data:(await readFile(join(work,name))).toString('base64'),name});
   await client.evaluate(`await ctx.get('attachments').admitPromptContent(${JSON.stringify(images)});return {preparedImages:2};`);
  }
  const aliases={};const imageMap=[];
  for(const name of ['P01.png','R01.png']){
   const bytes=await readFile(join(work,name));const sha=createHash('sha256').update(bytes).digest('hex');
   const object=join(process.env.DSH_HOME??join(homedir(),'.dsh'),'attachments/v1/objects',sha.slice(0,2),sha);
   aliases[name]=[];
   try{const stored=await readFile(object);if(!stored.equals(bytes))throw Error('Attachment alias byte mismatch');aliases[name].push(object);}catch(error){if(error.code!=='ENOENT')throw error;}
   imageMap.push({name,sha256:sha,source:join(work,name),verifiedAliases:aliases[name]});
  }
  await writeFile(join(work,'image-map.json'),JSON.stringify(imageMap,null,2));
  const setup=await client.evaluate(`
    const agent=ctx.agents.get(${JSON.stringify(sessionId)});
    const resolved=await ctx.llm.resolveCallConfig(${JSON.stringify(routes[modelKey])});
    const selected={provider:resolved.provider,model:resolved.model,...resolved.reasoningEffort===undefined?{}:{reasoningEffort:resolved.reasoningEffort}};
    // Same validated Session selection as the UI, without its default-saving side effect.
    ctx.sessionController.commands.agents.selectForNextRequest(agent,selected);
    agent.ctx.get('permissionPresets').set(agent.session,'read-only');
    agent.ctx.get('approval').setPolicy(agent,'never');
    const free=['mcp__zhenzhen-gptimagegen2-5-mcp__get_model_guide','mcp__zhenzhen-nanobanana-mcp__list_models','mcp__zhenzhen-nanobanana-mcp__inspect_design_images'];
    // The fixtures and Skill base are already absolute in runtime/tool context.
    // Do not expose a directory-changing capability for these fixed read-only tasks.
    const safe=new Set([...free,'skill','read','run_code']);
    const tools=agent.ctx.get('tools');
    const visible=tools.schemas(agent).map(x=>x.name);
    tools.restrict({allow:visible.filter(n=>safe.has(n)&&n!=='run_code')});
    const cwd=${JSON.stringify(work)};const audit=[];let phase='preflight';
    agent.ctx[Symbol.for('dsh76d8.audit')]=audit;
    const policy=(${createFreeGuardPolicy.toString()})(cwd,${JSON.stringify(aliases)});
    tools.guard(exec=>{
      const allowed=policy(exec);
      audit.push({phase,name:exec.name,allowed});return allowed?undefined:'76d.8 free verification: capability or input denied';
    });
    const denied=tools.guardReason({name:'mcp__zhenzhen-gptimagegen2-5-mcp__generate_image',agent,arguments:{}});
    const deniedOther=tools.guardReason({name:'mcp__zhenzhen-nanobanana-mcp__submit_ecommerce_design',agent,arguments:{}});
    if(!denied||!deniedOther)throw Error('Paid-call guard self-test failed');
    const hostDiscoveryVisible=tools.schemas(agent).some(x=>x.name==='list_agents');
    if(hostDiscoveryVisible&&tools.guardReason({name:'list_agents',agent,arguments:{}}))throw Error('Authorized host discovery still rejected');
    phase='model';
    return {selected,paidGuardSelfTest:true,hostDiscovery:{visible:hostDiscoveryVisible,allowed:hostDiscoveryVisible},tools:tools.schemas(agent).map(x=>x.name),permissions:ctx.sessionProjections.snapshot(agent.session).values.permissions};
  `);
  await writeFile(join(work,'setup.json'),JSON.stringify(setup,null,2));
  const skills=await client.call('skills/list',{request:{sessionId}});
  await writeFile(join(work,'skills.json'),JSON.stringify(skills,null,2));
  const skill=skills.skills.find(x=>x.name==='ecommerce-image-designer');
  if(!skill || resolve(skill.path)!==resolve(work,'.agents/skills/ecommerce-image-designer/SKILL.md'))throw Error('Wrong Skill source');
  const text=cases[caseKey]+'\n本次仅验证，不生成、编辑、确认、提交或重试图片，不调用其他服务，不读取凭据或用户配置、不安装依赖、不创建子代理。';
  await writeFile(join(work,'input.txt'),text);
  const content=[{type:'text',text}];
  if(caseKey==='implicit')for(const name of ['P01.png','R01.png'])content.push({type:'image',mediaType:'image/png',data:(await readFile(join(work,name))).toString('base64'),name});
  record.admission=await client.call('session/prompt',{request:{requestId:randomUUID(),sessionId,mode:'queue',content,clientTimeZone:'Asia/Shanghai'}});
  accepted=record.admission.accepted===true;
  if(!accepted)throw Error('Prompt not admitted');
  console.log(JSON.stringify({trial:`${modelKey}-${caseKey}`,status:'started',sessionId}));
  while(Date.now()-started<600000){
   await new Promise(r=>setTimeout(r,3000));
   const snapshot=await client.evaluate(`const agent=ctx.agents.get(${JSON.stringify(sessionId)});return {events:agent.session.snapshotEvents(),audit:agent.ctx[Symbol.for('dsh76d8.audit')]};`);
   await writeFile(join(work,'events.json'),JSON.stringify(snapshot,null,2));
   if(snapshot.events.some(e=>e.type==='turn/end')){
    const last=snapshot.events.filter(e=>e.type==='assistant/message').at(-1);
    const answer=(last?.data?.message?.content??[]).filter(x=>x.type==='text').map(x=>x.text).join('\n');
    await writeFile(join(work,'answer.txt'),answer);
    record.turnEnd=snapshot.events.findLast(e=>e.type==='turn/end').data;
    Object.assign(record,classifyTrial(record.turnEnd,answer));
    break;
   }
  }
  if(!record.status)throw Error('Host trial timeout; no image request will be retried');
 }catch(error){
  record.status='failed';record.error=String(error);
  if(accepted)try{record.cancel=await client.call('session/cancel',{request:{sessionId}});}catch(cancel){record.cancelError=String(cancel);}
 }finally{
  if(owned)try{
   const released=await client.evaluate(`return await (${releaseOwnedTestAgent.toString()})(ctx,${JSON.stringify(sessionId)},${JSON.stringify(work)},${JSON.stringify(lifecycleOwner)});`);
   await writeFile(join(work,'persisted-events.json'),JSON.stringify(released.events,null,2));
   const {events,...summary}=released;record.lifecycle=summary;
  }catch(error){record.lifecycle={released:false,error:String(error)};record.status='failed';record.error??=String(error);lifecycleFailed=true;}
  record.seconds=Math.round((Date.now()-started)/10)/100;
  await writeFile(join(work,'trial.json'),JSON.stringify(record,null,2));
  record.postprocess=await postprocessTrial(python,root,`${modelKey}-${caseKey}-r1`);
  await writeFile(join(work,'trial.json'),JSON.stringify(record,null,2));
  manifest.results.push(record);await writeFile(join(root,'run.json'),JSON.stringify(manifest,null,2));
  console.log(JSON.stringify({trial:`${modelKey}-${caseKey}`,status:record.status,seconds:record.seconds,error:record.error,
    raw_passed:record.postprocess.raw_passed,candidate_valid:record.postprocess.candidate_valid,pipeline_passed:record.postprocess.pipeline_passed}));
 }
 return record;
}

try{
 // Independent scenes are not retries. A provider error does not suppress the
 // remaining fixed scenes after verified teardown; lifecycle/Host loss does.
 await Promise.all(Object.keys(routes).map(async key=>{for(const caseKey of Object.keys(cases)){if(lifecycleFailed)break;const result=await trial(key,caseKey);if(!result.lifecycle?.released)break;}}));
 try{
  const after=await client.call('session/modelCatalog');
  manifest.defaultUnchanged=JSON.stringify(catalog.default)===JSON.stringify(after.default);
  manifest.runtimeAgentsAfter=await client.evaluate('return ctx.agents.list().map(a=>a.id);');
 }catch(error){manifest.finalInspectionError=String(error);manifest.defaultUnchanged=false;}
 await writeFile(join(root,'run.json'),JSON.stringify(manifest,null,2));
 manifest.postprocessingSummary={rawPassed:manifest.results.filter(r=>r.postprocess?.raw_passed).length,
  compiledValid:manifest.results.filter(r=>r.postprocess?.candidate_valid).length,
  pipelinePassed:manifest.results.filter(r=>r.postprocess?.pipeline_passed).length};
 await writeFile(join(root,'run.json'),JSON.stringify(manifest,null,2));
 process.exitCode=manifest.results.length!==8||manifest.results.some(r=>r.status!=='completed'||!r.postprocess?.pipeline_passed)||!manifest.defaultUnchanged?1:0;
}finally{client.close();}
