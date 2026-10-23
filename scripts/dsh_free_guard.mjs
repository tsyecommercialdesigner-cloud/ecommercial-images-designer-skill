/** Pure, import-free policy: serializable into the installed Inspector realm. */
export function createFreeGuardPolicy(cwd, imageAliases={}) {
 const free=new Set(['mcp__zhenzhen-gptimagegen2-5-mcp__get_model_guide',
  'mcp__zhenzhen-nanobanana-mcp__list_models','mcp__zhenzhen-nanobanana-mcp__inspect_design_images']);
 const base=new URL('file:///'+cwd.replaceAll('\\','/')+'/');
 const canonical=p=>{
  if(typeof p!=='string'||p.startsWith('\\\\')||p.startsWith('//'))return undefined;
  const input=p.replaceAll('\\','/').replace(/\/{2,}/g,'/');
  try{const url=new URL(/^[a-z]:\//i.test(input)?'file:///'+input:input,base);return url.protocol==='file:'?url.href.toLowerCase():undefined;}catch{return undefined;}
 };
 const prefix=base.href.toLowerCase();
 const images=new Map();
 for(const name of ['P01.png','R01.png'])for(const p of [name,...imageAliases[name]??[]])images.set(canonical(p),name);
 return exec=>{
  const args=exec.arguments??{};
  // Authorized host housekeeping only. The guard is installed on agent.ctx;
  // the native tool resolves membership from that exact calling Agent.
  if(exec.name==='list_agents')return exec.arguments!==null&&typeof args==='object'&&!Array.isArray(args)&&Object.keys(args).length===0;
  if(exec.name==='skill')return args.name==='ecommerce-image-designer';
  if(exec.name==='read'){const path=canonical(args.file_path);return !!path&&(path===prefix.slice(0,-1)||path.startsWith(prefix));}
  if(exec.name==='working_directory')return Object.keys(args).length===0;
  if(exec.name==='run_code')return true; // End-capability dispatches remain guarded independently.
  if(exec.name==='mcp__zhenzhen-nanobanana-mcp__inspect_design_images')return Array.isArray(args.images)&&args.images.length===2&&args.images.every(p=>images.has(canonical(p)))&&new Set(args.images.map(p=>images.get(canonical(p)))).size===2;
  return free.has(exec.name);
 };
}
