"""Offline stdio MCP double. No HTTP client, provider SDK, credentials, or subprocesses."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import zlib


def png_fixture(path: Path, reference: bool = False, mask: bool = False, label: str = '') -> None:
    """Render deterministic geometric test data, not an AI-generated merchant image."""
    w = h = 256
    glyphs={'G':['01110','10000','10000','10111','10001','10001','01110'],'R':['11110','10001','10001','11110','10100','10010','10001'],'E':['11111','10000','10000','11110','10000','10000','11111'],'Y':['10001','10001','01010','00100','00100','00100','00100']}
    ink=set()
    for index,letter in enumerate(label):
        for gy,line in enumerate(glyphs[letter]):
            for gx,pixel in enumerate(line):
                if pixel=='1':
                    ink.update((70+index*24+gx*4+dx,12+gy*4+dy) for dx in range(4) for dy in range(4))
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            color = (247, 240, 226) if reference else (245, 245, 245)
            if 45 < x < 212 and 64 < y < 217:
                color = (185, 110, 52) if reference else (145, 151, 157)
            if 32 < x < 224 and 51 < y < 76:
                color = (97, 58, 37) if reference else (93, 101, 109)
            if reference and 25 < x < 231 and 15 < y < 35:
                color = (90, 54, 32)
            if (x,y) in ink:color=(25,25,25)
            row.extend((*color,0 if y<50 else 255) if mask else color)
        rows.append(b'\0' + bytes(row))
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w,h,8,6 if mask else 2,0,0,0)) + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))


def schema(properties, required=()):
    return dict(type='object', properties=properties, required=list(required), additionalProperties=False)


S = {'type': 'string'}
I = {'type': 'integer'}
B = {'type': 'boolean'}
O = {'type': 'object', 'additionalProperties': True}
A = {'type': 'array', 'items': S}
REVIEW_KEYS=('product_fidelity','style_fidelity','category_fit','layout_and_lighting','text_accuracy','factual_accuracy')
CRITERION=schema({'status':{'type':'string','enum':['pass','revise','uncertain']},'evidence':S,'correction':S},['status','evidence'])
ASSESSMENT=schema({key:CRITERION for key in REVIEW_KEYS},REVIEW_KEYS)
TOOLS = {
    'io': {
        'read_skill_resource': ('Read one file from the available skill package. path=SKILL.md or references/....', schema({'path': S}, ['path'])),
        'read_design_record': ('Read the synthetic prior conversation/design record and available attachments.', schema({})),
        'save_design_record': ('Save a design/confirmation/submission/revision record in this isolated workspace.', schema({'record': O}, ['record'])),
    },
    'gpt': {
        'get_model_guide': ('Read available GPT Image 2.5 models; no generation.', schema({})),
        'submit_image_generation': ('Submit a simulated generation; stable idempotency_key. No real provider.', schema({'prompt':S,'model':S,'images':A,'size':S,'quality':S,'group':S,'official_options':O,'idempotency_key':S,'output_dir':S}, ['prompt','model'])),
        'submit_image_edit': ('Submit a simulated image edit with images in their actual order. No real provider.', schema({'prompt':S,'model':S,'images':A,'size':S,'quality':S,'group':S,'official_options':O,'idempotency_key':S,'output_dir':S}, ['prompt','model','images'])),
        'generate_image': ('Synchronous simulated generation; supports official stream configuration.', schema({'prompt':S,'model':S,'images':A,'size':S,'quality':S,'group':S,'official_options':O,'idempotency_key':S,'output_dir':S}, ['prompt','model'])),
        'edit_image': ('Synchronous simulated edit; mask corresponds to first image.', schema({'prompt':S,'model':S,'images':A,'size':S,'quality':S,'group':S,'official_options':O,'idempotency_key':S,'output_dir':S}, ['prompt','model','images'])),
        'get_image_task': ('Query an existing simulated task; save=true retrieves its existing result.', schema({'task_id':S,'save':B,'output_dir':S}, ['task_id'])),
        'wait_image_task': ('Wait for an existing simulated task; not a new submission.', schema({'task_id':S,'timeout_seconds':I,'poll_interval':I,'output_dir':S}, ['task_id'])),
        'download_image': ('Restore an existing synthetic image from fixture.invalid; no HTTP is performed.', schema({'url':S,'output_dir':S}, ['url'])),
    },
    'nano': {
        'list_models': ('Read Nano Banana capabilities; no generation.', schema({})),
        'inspect_design_images': ('Read 1-4 accessible synthetic product/reference/result images for Host observation; free.', schema({'images':A}, ['images'])),
        'plan_ecommerce_design': ('Save a draft with complete brief and PanelCopy edits; rebuilds default panels then applies edits. No generation.', schema({'design_id':S,'brief':O,'expected_revision':I,'edits':{'type':'array','items':O}}, ['design_id','brief'])),
        'build_product_suite_prompts': ('Build and export a full main+detail+SKU suite; shared suite.style and frames. No generation.', schema({'design_id':S,'brief':O,'expected_revision':I}, ['design_id','brief'])),
        'build_reference_replica_prompts': ('Build and export reference_replica. Input1 style_only; input2+ product_identity. No generation.', schema({'design_id':S,'brief':O,'expected_revision':I}, ['design_id','brief'])),
        'export_product_suite_prompts': ('Export existing suite task.prompt, style digest, actual parameters.', schema({'design_id':S,'revision':I}, ['design_id'])),
        'export_validated_reference_replica': ('Export existing reference_replica task.prompt and ordered input_images.', schema({'design_id':S,'revision':I}, ['design_id'])),
        'get_ecommerce_design': ('Read current/specified design version, questions, tasks, paths; not ordinary prompt export.', schema({'design_id':S,'revision':I}, ['design_id'])),
        'confirm_ecommerce_design': ('Record approval of the WHOLE current version; does not submit or charge.', schema({'design_id':S,'revision':I,'digest':S,'confirmation_note':S,'user_confirmed':B}, ['design_id','revision','digest','confirmation_note'])),
        'submit_ecommerce_design': ('Submit 1-20 panel_ids from approved current version with authorize_paid=true; simulated only.', schema({'design_id':S,'revision':I,'digest':S,'panel_ids':A,'authorize_paid':B}, ['design_id','revision','digest','panel_ids'])),
        'get_image_tasks': ('Query existing tasks by original namespace.', schema({'checkpointer':S,'thread_id':S,'task_ids':A}, ['checkpointer','thread_id'])),
        'wait_image_tasks': ('Wait for existing tasks by original namespace; no new submission.', schema({'checkpointer':S,'thread_id':S,'task_ids':A,'wait_timeout_seconds':I}, ['checkpointer','thread_id','task_ids'])),
        'review_reference_replica': ('Save Host six-dimension evidence bound to actual design/task/image SHA. No image recognition or redraw.', schema({'design_id':S,'revision':I,'task_id':S,'image_sha256':S,'assessment':ASSESSMENT}, ['design_id','revision','task_id','image_sha256','assessment'])),
        'retry_image_tasks': ('Retry only original safe recovery stages; never resend unknown requests.', schema({'checkpointer':S,'thread_id':S,'task_ids':A,'repair_files':B}, ['checkpointer','thread_id','task_ids'])),
        'submit_image_tasks': ('Generic simulated task submission; no design-plan gate. No real provider.', schema({'tasks':{'type':'array','items':O},'authorize_paid':B}, ['tasks'])),
        'generate_images': ('Generic simulated generation entry, outside design-plan workflow. No real provider.', schema({'prompt':S,'images':A}, ['prompt'])),
    },
    'foreign': {'generate_image': ('Another image service, simulated only.', schema({'prompt':S}, ['prompt']))},
}


def seed_workspace(root: Path, context: str, case_id: str, variant: str = ''):
    root.mkdir(parents=True, exist_ok=True)
    for name, ref in [('P01',False),('R01',True),('R02',True),('G01',False),('G02',False)]:
        png_fixture(root/f'{name}.png', ref)
    attachments = {} if case_id in {'E01','E02','E21','E22','E26'} else {k:str(root/f'{k}.png') for k in ('P01','R01')}
    if case_id=='E03': attachments['R02']=str(root/'R02.png')
    if case_id == 'E07':
        attachments = {'R01':str(root/'R01.png')}
    panels=[dict(panel_id=f'p{i:02}',headline='灰色款',body='仅展示已确认的灰色款外观',visual='灰色盒状测试商品，背景干净',layout='上标题下商品',fact_ids=['F01']) for i in range(1, (5 if case_id in {'E13','E33'} else 3 if case_id=='E17' else 2 if case_id in {'E18','E34'} else 1)+1)]
    brief=dict(kind='main',product_name='合成测试商品',platform='测试页面',audience='已在上下文确认的目标用户',objective='展示已确认外观',product_images=[str(root/'P01.png')] if 'P01' in attachments else [],visual_observations='合成灰色盒状物体，有深灰色盖沿；无性能依据',facts=[dict(fact_id='F01',label='灰色款',value='仅灰色外观',source='合成测试资料与图片观察',category='usage')],main_count=len(panels),aspect_ratio='1:1',resolution={'width':1024,'height':1024},model='nano-banana-pro',api_format='dalle',endpoint='edits',reference_choice='provided',benchmarks=[dict(source=str(root/'R01.png'),visual_focus='居中',hierarchy='上标题下商品',copy_approach='简短',strengths='清晰',weaknesses='信息有限',adaptation='仅按用户批准用途借鉴')],style=dict(palette='中性色',typography='无衬线',layout='上标题下商品',tone='简洁真实'))
    if case_id=='E34': panels[1]['headline']='用户已定稿的M02标题'; panels[1]['layout']='用户已定稿的左图右文布局'
    if case_id in {'E30','E36'}: brief['reference_replica']={'scope':'series','reference_image':str(root/'R01.png'),'source_category':'合成盒','target_category':'合成盒','style':{},'analysis':{},'adaptations':{},'frames':[]}
    if case_id=='E35':
        frames=[dict(panel_id='p01',kind='main',template_id='main.hero',purpose='主图',title='灰色款',visual='完整商品',fact_ids=['F01'])]
        for i,template in enumerate(['opening','solution','feature','material','size','usage','proof','closing'],1):
            frames.append(dict(panel_id=f'd{i:02}',kind='detail',template_id='detail.'+template,purpose='详情',title='可见外观',visual='仅展示可见外观',fact_ids=['F01']))
        frames.append(dict(panel_id='k01',kind='sku',template_id='sku.variant',purpose='规格',title='灰色款',visual='灰色款',fact_ids=['F01'],sku_id='gray'))
        brief['suite']={'style':{'palette':{'primary':'#245A50'}},'frames':frames}
        brief['variants']=[dict(sku_id='gray',label='灰色款',attributes={'颜色':'灰色'},product_images=[str(root/'P01.png')],fact_ids=['F01'])]
    if case_id=='E13': panels[0]['body']+='；未经确认的1年质保'
    design=dict(design_id='fixture-design',revision=3,digest='a'*64,status='draft',brief=brief,panels=panels,assets=[],questions=[])
    approval=['M01'] if case_id in {'E11','E13','E33','E41'} else []
    record=dict(simulated=True,context=context,attachments=attachments,design_id='fixture-design',revision=3,phase='restored',facts=brief['facts'],images=[dict(image_id=k,source=v,identity='reference' if k.startswith('R') else 'generated' if k.startswith('G') else 'product',reference_use='unknown' if case_id=='E03' else 'style' if k.startswith('R') else 'none') for k,v in attachments.items()],server_panel_map={f'M{i:02}':p['panel_id'] for i,p in enumerate(panels,1)},confirmed_scope=approval,confirmation_evidence='合成上下文中的用户已确认r3/M01，原批准完整文案、排版、提示词及图片映射均未改变' if case_id=='E11' else '按当前场景上下文判断，不推定未批准范围',execution_authorization='E11模拟用户明确授权按展示范围收费，服务本身不收费' if case_id=='E11' else '以场景上下文为准',selected_service='zhenzhen-gptimagegen2.5-mcp',model='gpt-image-2.5-sunburst',size='1024x1024',prompt='为合成灰色盒状商品制作M01主图。图1是本商品外观依据，保持盖沿和灰色，干净背景，标题“灰色款”，只展示外观，不添加参数和承诺。',pending_task={'task_id':'T1','idempotency_key':'K1','checkpointer':'ecommerce-design','thread_id':'fixture-design'},design=design)
    if case_id=='E03':
        for item in record['images']: item['identity']='unknown';item['reference_use']='unknown'
    if case_id not in {'E14','E15','E16','E17','E28','E36','E40','E42'}:
        record.pop('pending_task',None)
    if case_id in {'E13','E17','E28','E29','E30','E31','E32','E33','E34','E35','E36'}:
        record['selected_service']='zhenzhen-nanobanana-mcp';record['model']='nano-banana-pro'
    if case_id=='E17':
        record['pending_task'].pop('task_id',None)
        record['pending_task']['task_ids']=['r3-p01','r3-p02','r3-p03']
    if case_id=='E15':
        record['pending_task'].pop('task_id',None)
        record['pending_task']['submitted_at']='2026-10-22T08:00:00Z'
        record['pending_task']['status']='unknown'
    if case_id=='E39':
        png_fixture(root/'mask.png',mask=True)
        record['edit_inputs']=[dict(index=1,image_id='R01',role='style_reference',path=str(root/'R01.png')),dict(index=2,image_id='G01',role='edit_base',path=str(root/'G01.png'))]
        record['mask']=dict(path=str(root/'mask.png'),width=256,height=256,format='PNG',has_alpha=True,bytes=(root/'mask.png').stat().st_size,base_image_id='G01')
    if case_id in {'E01','E02','E07'}:
        record['facts']=[];record['design']['brief']['facts']=[]
    if case_id in {'E16','E17','E18','E19','E35','E36'}:
        record['outputs']=[dict(image_id='G01',panel_id='M01',path=str(root/'G01.png'),sha256=hashlib.sha256((root/'G01.png').read_bytes()).hexdigest(),user_acceptance='accepted' if case_id in {'E18','E35'} else 'pending')]
    if case_id=='E16':record['result_url']='https://fixture.invalid/existing-G01.png'
    if case_id=='E17':record['outputs'].append(dict(image_id='G02',panel_id='M02',path=str(root/'G02.png'),sha256=hashlib.sha256((root/'G02.png').read_bytes()).hexdigest(),user_acceptance='pending'))
    if case_id=='E19':
        png_fixture(root/'G01.png',label='GREY')
        record['outputs'][0]['sha256']=hashlib.sha256((root/'G01.png').read_bytes()).hexdigest()
        record['prompt']='编辑G01，保持产品、布局和背景不变，仅将原已批准标题GRAY准确写回。'
        record['design']['panels'][0]['headline']='GRAY'
        record['confirmed_copy']='GRAY'
        record['reported_typo']='GREY，应按原批准文案改为GRAY'
    if case_id=='E12':
        record['previous_snapshot']=dict(revision=2,headline='灰色款',reference_use='style',model='gpt-image-2.5-flare',approved=True)
        record['design']['panels'][0]['headline']='整洁，有自己的位置'
        record['images'][1]['reference_use']='both'
        record['prompt']='P01保持灰色盒状商品外观；R01参考风格和画面结构，标题“整洁，有自己的位置”。'
    if case_id=='E34':
        record['requested_change']=dict(panel_id='M01',headline='简洁收纳',user_evidence='模拟历史中的用户补充：M01新标题用“简洁收纳”，其余定稿保持。')
    if case_id=='E18':
        record['outputs'].append(dict(image_id='G02',panel_id='M02',path=str(root/'G02.png'),sha256=hashlib.sha256((root/'G02.png').read_bytes()).hexdigest(),user_acceptance='changes_requested'))
    if case_id=='E41': record['input_changed']=True;record['previous_image_sha256']='0'*64
    if variant=='nano-approved':
        record['selected_service']='zhenzhen-nanobanana-mcp';record['model']='nano-banana-pro'
        record['design']['brief']['reference_replica']={'scope':'series','reference_image':str(root/'R01.png'),'source_category':'合成盒','target_category':'合成盒','style':{},'analysis':{},'adaptations':{},'frames':[]}
        record['prompt']=json.dumps(record['design']['panels'][0],ensure_ascii=False)
        record['approved_input_order']=[dict(image_id='R01',role='style_only'),dict(image_id='P01',role='product_identity')]
    (root/'seed.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')


class MockServer:
    def __init__(self, service: str, root: Path, skill: Path):
        self.service,self.root,self.skill=service,root.resolve(),skill.resolve()
        self.seed=json.loads((self.root/'seed.json').read_text(encoding='utf-8'))
        self.design=self.seed['design']
        self.submitted_tasks=[]

    def media(self, source):
        known={str(p.resolve()):p for p in self.root.glob('*.png')}
        aliases={p.stem:str(p.resolve()) for p in known.values()}
        key=aliases.get(source,source)
        if key not in known: raise ValueError('Unknown/inaccessible fixture image; no external file/network access')
        p=known[key];b=p.read_bytes()
        return dict(path=str(p),source=source,sha256=hashlib.sha256(b).hexdigest(),width=256,height=256,bytes=len(b),mime_type='image/png')

    def export(self, reference=False):
        key='reference_replica' if reference else 'suite'
        if not self.design['brief'].get(key): raise ValueError('This design is not the requested export type')
        sources=([str(self.root/'R01.png')] if reference else [])+self.design['brief']['product_images']
        return dict(design=self.design,style_digest='b'*64,prompts=[dict(panel_id=p['panel_id'],task=dict(task_id=f'r{self.design["revision"]}-{p["panel_id"]}',prompt=json.dumps(p,ensure_ascii=False),reference_images=sources,reference_sha256=[self.media(s)['sha256'] for s in sources],model='nano-banana-pro',aspect_ratio='1:1',resolution={'width':1024,'height':1024}),input_images=[dict(index=i+1,role='style_only' if reference and i==0 else 'product_identity',**self.media(s)) for i,s in enumerate(sources)]) for p in self.design['panels']])

    def call(self, name, a):
        if self.service=='io':
            if name=='read_skill_resource':
                p=(self.skill/a['path']).resolve()
                if not p.is_relative_to(self.skill) or not p.is_file(): raise ValueError('Only packaged skill resources are readable')
                return {'text':p.read_text(encoding='utf-8')}
            if name=='read_design_record': return self.seed
            if name=='save_design_record':
                (self.root/'saved_record.json').write_text(json.dumps(a['record'],ensure_ascii=False),encoding='utf-8');return {'saved':True,'path':str(self.root/'saved_record.json')}
        if name in {'get_model_guide','list_models'}:
            return dict(simulated=True,models=['gpt-image-2.5-sunburst','gpt-image-2.5-flare'] if self.service=='gpt' else ['nano-banana-pro'],key_present=True,api_key_configured=True,upstream_verified=False,max_reference_images=4,async_tasks=True)
        if name=='inspect_design_images': return {'images':[self.media(s) for s in a['images']]}
        if name=='get_ecommerce_design':
            tasks=list(self.submitted_tasks)
            if self.root.name.startswith('E17'):
                tasks=[dict(task_id=f'r3-p{i:02}',status='succeeded' if i<3 else 'failed',images=[self.media('G01' if i==1 else 'G02')] if i<3 else []) for i in range(1,4)]
            elif self.seed.get('pending_task',{}).get('task_id') or self.root.name.startswith('E36'):
                tasks=[dict(task_id='T1',status='running' if self.root.name.startswith(('E14','E28','E40')) else 'succeeded',images=[self.media('G01')])]
            return dict(design=self.design,tasks=tasks,checkpointer='ecommerce-design',thread_id='fixture-design',unsubmitted_panel_ids=[p['panel_id'] for p in self.design['panels']])
        if name.startswith(('plan_','build_')):
            brief=a['brief'];suite=brief.get('suite');ref=brief.get('reference_replica')
            if suite:
                counts={k:sum(f.get('kind')==k for f in suite.get('frames',[])) for k in ('main','detail','sku')}
                if not(1<=counts['main']<=8 and 8<=counts['detail']<=15 and counts['sku']>=1): raise ValueError('suite requires main+8..15 detail+real SKU')
            if brief.get('kind')=='detail' and not ref and not 8<=brief.get('detail_count',10)<=15: raise ValueError('ordinary detail_count must be 8..15')
            if name=='plan_ecommerce_design' and a.get('edits') and (suite or ref): raise ValueError('Do not use ordinary edits for suite/reference_replica')
            self.design=dict(self.design,design_id=a['design_id'],revision=a.get('expected_revision',0)+1,digest='c'*64,brief=brief,status='draft')
            frames=(suite or ref or {}).get('frames')
            if frames: self.design['panels']=frames
            else:
                self.design['panels']=[dict(panel_id=f'p{i:02}',headline='默认标题',body='',visual='默认构图',layout='默认排版',fact_ids=[]) for i in range(1,brief.get('main_count',1)+1)]
                for e in a.get('edits',[]):
                    for p in self.design['panels']:
                        if p['panel_id']==e['panel_id']:p.update(e)
            if name.startswith('build_'): return self.export(bool(ref))
            return self.design
        if name.startswith('export_'): return self.export(name=='export_validated_reference_replica')
        if name=='confirm_ecommerce_design':
            if not a.get('user_confirmed'): raise ValueError('user_confirmed required')
            if a['revision']!=self.design['revision'] or a['digest']!=self.design['digest']: raise ValueError('stale revision/digest')
            self.design['status']='approved';return self.design
        if name=='review_reference_replica':
            assessment=a['assessment']
            if set(assessment)!=set(REVIEW_KEYS):raise ValueError('Exactly six named review dimensions required')
            for criterion in assessment.values():
                if criterion.get('status') not in {'pass','revise','uncertain'} or not criterion.get('evidence'):raise ValueError('Review status and concrete evidence required')
                if criterion['status']!='pass' and not criterion.get('correction'):raise ValueError('revise/uncertain require correction')
            task_ids={t['task_id'] for t in self.submitted_tasks}
            if self.seed.get('pending_task',{}).get('task_id'):task_ids.add(self.seed['pending_task']['task_id'])
            if a['revision']!=self.design['revision'] or a['task_id'] not in task_ids or a['image_sha256']!=self.media('G01')['sha256']:raise ValueError('Review does not match actual task/version/image SHA')
            outcome='revise' if any(c['status']=='revise' for c in assessment.values()) else 'needs_user_review' if any(c['status']=='uncertain' for c in assessment.values()) else 'agent_passed'
            return dict(simulated=True,outcome=outcome,review_id=1,**a)
        if name in {'get_image_task','wait_image_task','get_image_tasks','wait_image_tasks','retry_image_tasks'}:
            if self.service=='nano' and self.root.name.startswith('E17'):
                return dict(checkpointer=a.get('checkpointer'),thread_id=a.get('thread_id'),tasks=[dict(task_id=f'r3-p{i:02}',status='succeeded' if i<3 else 'failed',images=[self.media('G01' if i==1 else 'G02')] if i<3 else []) for i in range(1,4)])
            active=self.root.name.startswith(('E14','E28','E40'))
            data=dict(simulated=True,task_id=a.get('task_id','T1'),status='IN_PROGRESS' if active else 'SUCCESS',files=[] if active else [dict(index=0,**self.media('G01'))],save_status='no_images' if active else 'saved')
            if self.service=='nano': return dict(checkpointer=a.get('checkpointer'),thread_id=a.get('thread_id'),tasks=[dict(task_id=t,status='running' if active else 'succeeded',images=[] if active else [self.media('G01')]) for t in a.get('task_ids',['T1'])])
            return data
        if name=='download_image':
            if not a['url'].startswith('https://fixture.invalid/'): raise ValueError('Only fixture URL can be restored')
            return self.media('G01')
        if name in {'submit_image_generation','submit_image_edit','generate_image','edit_image','submit_ecommerce_design','submit_image_tasks','generate_images'}:
            if name=='submit_ecommerce_design' and (not a.get('authorize_paid') or self.design['status']!='approved'): raise ValueError('approved version and explicit authorization required')
            if name.startswith('submit_image') and a.get('official_options',{}).get('stream'): raise ValueError('stream and async are mutually exclusive')
            for image in a.get('images',[]): self.media(image)
            if name=='submit_ecommerce_design':
                self.submitted_tasks=[dict(task_id=f'r{self.design["revision"]}-{panel}',status='succeeded',images=[self.media('G01')]) for panel in a['panel_ids']]
                return dict(simulated=True,cost=0,checkpointer='ecommerce-design',thread_id=self.design['design_id'],tasks=self.submitted_tasks)
            return dict(simulated=True,task_id='SIM-'+str(a.get('idempotency_key','TNEW')),status='COMPLETED',files=[dict(index=0,**self.media('G01'))],save_status='saved',cost=0)
        raise ValueError('Unknown simulated tool')

    def handle(self, message):
        method=message['method'];p=message.get('params',{})
        if method=='initialize': return dict(protocolVersion=p.get('protocolVersion','2024-11-05'),capabilities={'tools':{},'resources':{}},serverInfo={'name':self.service+'-SIMULATED','version':'1.0'})
        if method=='tools/list': return {'tools':[dict(name=n,description=d,inputSchema=s) for n,(d,s) in TOOLS[self.service].items()]}
        if method=='resources/list': return {'resources':[]}
        if method=='prompts/list': return {'prompts':[]}
        if method=='tools/call':
            name=p['name'];args=p.get('arguments',{})
            entry=dict(service=self.service,name=name,arguments=args)
            try:
                result=self.call(name,args);entry['result']=result
                content=[{'type':'text','text':json.dumps(result,ensure_ascii=False)}]
                if name=='inspect_design_images':
                    content.extend(dict(type='image',mimeType='image/png',data=base64.b64encode(Path(m['path']).read_bytes()).decode()) for m in result['images'])
                response={'content':content,'isError':False}
            except (ValueError,KeyError,TypeError) as e:
                entry['error']=str(e);response={'content':[{'type':'text','text':str(e)}],'isError':True}
            with (self.root/'calls.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
            return response
        if method=='ping':return {}
        raise ValueError('Unsupported MCP method')


if __name__=='__main__':
    # Hosts may filter PYTHONUTF8 from child environments on Windows.
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8',newline='\n')
    server=MockServer(sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3]))
    for line in sys.stdin:
        try:
            request=json.loads(line)
            if 'id' not in request:continue
            try:reply={'jsonrpc':'2.0','id':request['id'],'result':server.handle(request)}
            except Exception as e:reply={'jsonrpc':'2.0','id':request['id'],'error':{'code':-32603,'message':type(e).__name__+': '+str(e)}}
            print(json.dumps(reply,ensure_ascii=False),flush=True)
        except (ValueError,KeyError):continue
