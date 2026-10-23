import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createFreeGuardPolicy} from '../scripts/dsh_free_guard.mjs';
const policy=createFreeGuardPolicy('E:\\owned\\trial');
test('both paid MCP families and unapproved capabilities denied',()=>{
 for(const name of ['mcp__zhenzhen-gptimagegen2-5-mcp__generate_image','mcp__zhenzhen-nanobanana-mcp__submit_ecommerce_design','subagent','powershell','write','terminal_open'])assert.equal(policy({name}),false,name);
});
test('only current Skill may load',()=>{
 assert.equal(policy({name:'skill',arguments:{name:'ecommerce-image-designer'}}),true);
 assert.equal(policy({name:'skill',arguments:{name:'other'}}),false);
});
test('host discovery allows only empty native list_agents; team mutations stay denied',()=>{
 assert.equal(policy({name:'list_agents',arguments:{}}),true);
 for(const args of [null,[],{sessionId:'foreign'},{target:'other'}])assert.equal(policy({name:'list_agents',arguments:args}),false);
 for(const name of ['spawn_teammate','subagent','send_message','interrupt_agent','wait_agent','list_tasks','mcp__other__list_agents'])assert.equal(policy({name,arguments:{}}),false,name);
 const remote=vm.runInNewContext(`(${createFreeGuardPolicy.toString()})('E:/owned/trial')`,{URL});
 assert.equal(remote({name:'list_agents',arguments:{}}),true);
});
test('workspace reads accept Windows equivalents and reject escape',()=>{
 for(const p of ['design-record.json','E:/owned/trial/.agents/skills/a.md','e:\\OWNED\\trial\\file.md'])assert.equal(policy({name:'read',arguments:{file_path:p}}),true,p);
 for(const p of ['../outside','E:/owned/trial-other/a','C:/Users/secret','\\\\server\\secret','https://example.com/','file:///E:/owned/trial/../secret'])assert.equal(policy({name:'read',arguments:{file_path:p}}),false,p);
});
test('image inspection accepts exactly the two local fixture identities',()=>{
 const name='mcp__zhenzhen-nanobanana-mcp__inspect_design_images';
 assert.equal(policy({name,arguments:{images:['P01.png','E:/owned/trial/R01.png']}}),true);
 for(const images of [['P01.png','P01.png'],['P01.png','../R01.png'],['https://example.com/a','R01.png']])assert.equal(policy({name,arguments:{images}}),false);
});
test('serialized guard works without dynamic imports in Inspector-like VM',()=>{
 const remote=vm.runInNewContext(`(${createFreeGuardPolicy.toString()})('E:/owned/trial')`,{URL});
 assert.equal(remote({name:'read',arguments:{file_path:'design-record.json'}}),true);
 assert.equal(remote({name:'mcp__zhenzhen-nanobanana-mcp__generate_images'}),false);
});
test('byte-verified attachment aliases preserve two distinct image roles',()=>{
 const guarded=createFreeGuardPolicy('E:/owned/trial',{'P01.png':['C:/store/product'],'R01.png':['C:/store/style']});
 const name='mcp__zhenzhen-nanobanana-mcp__inspect_design_images';
 assert.equal(guarded({name,arguments:{images:['C:\\\\store\\\\product','C:/store/style']}}),true);
 assert.equal(guarded({name,arguments:{images:['P01.png','C:/store/product']}}),false);
 assert.equal(guarded({name,arguments:{images:['C:/store/unverified','R01.png']}}),false);
});
