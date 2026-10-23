/** Coordinator-only child process; never exposed as a model tool. */
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {join} from 'node:path';
const execute=promisify(execFile);

export async function postprocessTrial(python,root,name){
 let stdout;
 try{
  ({stdout}=await execute(python,['-X','utf8','-B',join(root,'orchestrator-source','dsh_postprocess_trial.py'),root,name],
    {encoding:'utf8',timeout:15000,maxBuffer:1024*1024,windowsHide:true}));
 }catch(error){
  if(error.stdout)try{return {...JSON.parse(error.stdout),process_exit_failed:true,pipeline_passed:false};}catch{}
  return {pipeline_passed:false,error:`Postprocessing process failed: ${error.code??error.message}`};
 }
 try{
  const result=JSON.parse(stdout);
  if(result.version!==1||result.trial!==name||typeof result.pipeline_passed!=='boolean')throw Error('Invalid result identity or shape');
  return result;
 }catch(error){return {pipeline_passed:false,error:`Invalid postprocessing output: ${error.message}`};}
}
