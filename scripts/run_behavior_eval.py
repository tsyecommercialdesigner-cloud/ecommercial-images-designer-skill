"""Run fresh Codex processes against offline MCP doubles; raw evidence stays in an ignored repository-local workspace."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

REPO=Path(__file__).resolve().parents[1]

_workspace_spec = importlib.util.spec_from_file_location('evaluation_workspace', Path(__file__).with_name('evaluation_workspace.py'))
_workspace = importlib.util.module_from_spec(_workspace_spec)
_workspace_spec.loader.exec_module(_workspace)
validate_root, claim_root, initialize_project = _workspace.validate_root, _workspace.claim_root, _workspace.initialize_project

MOCK=REPO/'evals/mock_mcp.py'
spec=importlib.util.spec_from_file_location('mock_mcp',MOCK)
mock=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)

DISABLED=['apps','plugins','hooks','image_generation','browser_use','browser_use_external','computer_use','shell_tool','unified_exec','multi_agent','memories','code_mode','workspace_dependencies','in_app_browser','skill_mcp_dependency_install']
OUTPUT_SCHEMA={'type':'object','properties':{'selected':{'type':'boolean'},'stage':{'type':'string','enum':['S0','S1','S2','S3','S4','S5','outside']},'reply':{'type':'string'},'record':{'type':'string'}},'required':['selected','stage','reply','record'],'additionalProperties':False}


def command(cwd: Path, schema: Path, last: Path):
    cmd=[shutil.which('codex') or 'codex','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--sandbox','read-only','-C',str(cwd),'--color','never','--output-schema',str(schema),'-o',str(last)]
    for name in DISABLED:cmd+=['-c',f'features.{name}=false']
    cmd+=['-c','features.skip_host_skill_discovery=true','-c','web_search="disabled"','-']
    return cmd


def services(case_id):
    if case_id in {'E21','E22'}:return ['io']
    if case_id=='E26':return ['io','foreign']
    if case_id=='E27':return ['io','gpt']
    if case_id=='E29':return ['io','nano']
    return ['io','gpt','nano']


def snapshot_skill(root):
    target=root/'skill'
    if not target.exists():shutil.copytree(REPO/'.agents/skills/ecommerce-image-designer',target)
    manifest={str(p.relative_to(target)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
    (root/'skill-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return target


def frozen_catalog(root):
    """Resumed runs use their own scenarios and rubric, never today's source."""
    return json.loads((root / 'harness/scenarios.json').read_text(encoding='utf-8'))


def run_trial(root,skill,case,repeat,timeout):
    tid=f'{case["id"]}-r{repeat}'
    work=root/tid
    if work.exists():raise RuntimeError('Refusing to overwrite trial '+tid)
    work.mkdir()
    initialize_project(work)
    frozen_mock=root/'harness/mock_mcp.py'
    fixture_module=mock
    if frozen_mock.exists():
        frozen_spec=importlib.util.spec_from_file_location('frozen_fixture',frozen_mock)
        fixture_module=importlib.util.module_from_spec(frozen_spec)
        frozen_spec.loader.exec_module(fixture_module)
    if case.get('_variant'):fixture_module.seed_workspace(work,case['context'],case['id'],variant=case['_variant'])
    else:fixture_module.seed_workspace(work,case['context'],case['id'])
    (work/'output-schema.json').write_text(json.dumps(OUTPUT_SCHEMA),encoding='utf-8')
    (work/'.codex').mkdir()
    labels={'io':'eval_io','gpt':'zhenzhen_gptimagegen2_5_mcp','nano':'zhenzhen_nanobanana_mcp','foreign':'other_image_mcp'}
    config=[]
    overrides=[]
    for service in services(case['id']):
        label=labels[service]
        # JSON string quoting is also valid TOML basic-string quoting for these paths.
        frozen_mock=root/'harness/mock_mcp.py'
        args=[str(frozen_mock if frozen_mock.exists() else MOCK),service,str(work),str(skill)]
        config.extend([f'[mcp_servers.{label}]',f'command = {json.dumps(sys.executable)}','args = '+json.dumps(args),'startup_timeout_sec = 20','tool_timeout_sec = 30','default_tools_approval_mode = "approve"',''])
        for key,value in [('command',sys.executable),('args',args),('startup_timeout_sec',20),('tool_timeout_sec',30),('default_tools_approval_mode','approve')]:
            overrides+=['-c',f'mcp_servers.{label}.{key}='+json.dumps(value)]
    (work/'.codex/config.toml').write_text('\n'.join(config),encoding='utf-8')
    body=(skill/'SKILL.md').read_text(encoding='utf-8')
    description=re.search(r'^description: (.*)$',body,re.M)[1]
    prompt=f'''这是隔离的模拟宿主任务。所有MCP都是本地无网络替身，返回值明确标记simulated；模拟用户历史确认仅限本任务夹具。只通过已暴露的工具推进任务，不调用任何真实服务。不要把模拟产物描述为真实供应商生成。
可用技能目录：ecommerce-image-designer，描述：{description}
判断技能是否适用。适用时先用 eval_io.read_skill_resource 读取 SKILL.md，按条件读取相关 reference 资料；不适用时不加载该技能，按用户原任务转向当前可用的适用能力，不强加电商流程。
历史上下文与附件台账可用 eval_io.read_design_record 读取，包含可访问的合成图片和原方案；它们是输入，不是评分答案。需要持久记录可用 save_design_record。已明确给出的资料可复用，不要无故重复访谈。若需要用户补充或确认，结束本轮并提出具体问题。若已有足够确认则执行可执行的模拟工具，不能仅说会执行。
最后以指定JSON输出：selected为是否使用该技能；stage为本轮实际定位的起点/阻塞阶段，而非你设想已完成的最终阶段；reply为给用户的实际答复；record为本轮保留的事实/映射/确认/修订摘要。
上下文（来自模拟历史）：
{case['context']}
用户当前请求：
{case['prompt']}
'''
    # The prompt contains only raw context/request and catalog; not the oracle assertions.
    (work/'input.txt').write_text(prompt,encoding='utf-8')
    started=time.time()
    cmd=command(work,work/'output-schema.json',work/'answer.json')
    cmd[-1:-1]=overrides
    (work/'command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2),encoding='utf-8')
    with (work/'stdout.txt').open('w',encoding='utf-8') as out,(work/'stderr.txt').open('w',encoding='utf-8') as err:
        try:
            p=subprocess.run(cmd,input=prompt,text=True,encoding='utf-8',stdout=out,stderr=err,timeout=timeout,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'})
            status='completed' if p.returncode==0 and (work/'answer.json').is_file() else 'infrastructure_error'
            exit_code=p.returncode
        except subprocess.TimeoutExpired:
            status='timeout';exit_code=None
    header=(work/'stderr.txt').read_text(encoding='utf-8',errors='replace')
    if any(marker in header for marker in ('code-mode host is disabled','MCP tool call requires approval','timed out awaiting tools/call')):
        status='infrastructure_error'
    model=re.search(r'^model:\s*(.+)$',header,re.M)
    result=dict(trial_id=tid,case_id=case['id'],repeat=repeat,status=status,exit_code=exit_code,seconds=round(time.time()-started,2),model=model[1].strip() if model else 'unavailable',mock_services=services(case['id']),networked_image_provider=False)
    if status=='completed':
        try:result['answer']=json.loads((work/'answer.json').read_text(encoding='utf-8'))
        except ValueError:result['status']='invalid_answer'
    (work/'trial.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--cases',default='all',help='all or comma-separated IDs')
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--workers',type=int,default=3)
    p.add_argument('--timeout',type=int,default=180)
    p.add_argument('--start-repeat',type=int,default=1)
    p.add_argument('--variant',choices=['nano-approved'],help='Additional E11 positive Nano workflow; report separately from the fixed suite')
    a=p.parse_args()
    try:
        root=validate_root(a.output)
    except ValueError as error:
        p.error(str(error))
    if a.repeats<1 or not 1<=a.workers<=6:raise SystemExit('Invalid repetition/worker bound')
    claim_root(root)
    skill=snapshot_skill(root)
    harness=root/'harness';harness.mkdir(exist_ok=True)
    for source in (MOCK,Path(__file__).resolve(),Path(__file__).with_name('evaluation_workspace.py'),REPO/'evals/scenarios.json'):
        dest=harness/source.name
        if not dest.exists():shutil.copyfile(source,dest)
    catalog=frozen_catalog(root)
    cases=catalog['cases']
    if a.cases!='all':
        wanted=set(a.cases.split(','));cases=[c for c in cases if c['id'] in wanted]
        if len(cases)!=len(wanted):raise SystemExit('Unknown case selection')
    if a.variant:
        if [c['id'] for c in cases]!=['E11']:raise SystemExit('nano-approved variant requires --cases E11')
        cases[0]=dict(cases[0],_variant=a.variant,context=cases[0]['context']+' 所选服务为Nano Banana核心任务接口；M01完整提示词、R01仅风格在前/P01商品身份在后的顺序及参数均已展示确认且费用明确授权，尚未提交。没有策划/确认/导出/评审扩展工具。')
    info=dict(rubric_version=catalog['rubric_version'],case_ids=[c['id'] for c in cases],repeats=a.repeats,workers=a.workers,timeout_seconds=a.timeout,model_selection='CLI supported default; no model override',cli_version=subprocess.check_output([shutil.which('codex'),'--version'],text=True).strip(),harness_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in harness.iterdir() if p.is_file()},isolation=dict(ignore_user_config=True,disabled=DISABLED,real_image_servers_loaded=False,stdin_mock_implementation=str(harness/'mock_mcp.py')))
    (root/'run.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    results=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        pending={pool.submit(run_trial,root,skill,c,r,a.timeout):(c['id'],r) for r in range(a.start_repeat,a.start_repeat+a.repeats) for c in cases}
        for f in as_completed(pending):
            result=f.result();results.append(result)
            with (root/'trials.jsonl').open('a',encoding='utf-8') as file:file.write(json.dumps(result,ensure_ascii=False)+'\n')
            print(json.dumps({k:result[k] for k in ('trial_id','status','seconds','model')},ensure_ascii=False),flush=True)
    return int(any(r['status']!='completed' for r in results))


if __name__=='__main__':raise SystemExit(main())
