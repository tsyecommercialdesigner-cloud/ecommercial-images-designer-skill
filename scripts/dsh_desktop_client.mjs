export async function connectDesktop() {
  const tabs=await (await fetch('http://127.0.0.1:9230/json/list')).json();
  const target=tabs.find(x=>x.url==='dsh://host');
  if(!target) throw Error('Desktop Host Inspector unavailable');
  const socket=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  const pending=new Map();let seq=0;
  socket.onmessage=e=>{const row=JSON.parse(e.data);const p=pending.get(row.id);if(p){pending.delete(row.id);clearTimeout(p.timer);p.resolve(row);}};
  socket.onclose=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('Desktop Host Inspector disconnected'));}pending.clear();};
  async function evaluate(body){
    const expression=`(async()=>{const ctx=[...globalThis[Symbol.for('dsh.inspector.realm-object-registries')].values()][0].resolve('object-1');${body}})()`;
    if(socket.readyState!==WebSocket.OPEN)throw Error('Desktop Host Inspector is closed');
    const id=++seq;const promise=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{pending.delete(id);reject(Error('Desktop Host Inspector evaluation timeout'));},45000);
      pending.set(id,{resolve,reject,timer});
      try{socket.send(JSON.stringify({id,method:'Runtime.evaluate',params:{expression,returnByValue:true,awaitPromise:true}}));}
      catch(error){clearTimeout(timer);pending.delete(id);reject(error);}
    });
    const response=await promise;
    if(response.error || response.result?.exceptionDetails) throw Error(JSON.stringify(response.error??response.result.exceptionDetails));
    return response.result.result.value;
  }
  // Obtain the existing Host's launch URL through its own connection API.
  // Exchange it normally; never forge cookies or expose authentication in logs.
  const launch=await evaluate('return ctx.connection.authenticatedUrl(`${ctx.webServer.protocol}//127.0.0.1:${ctx.webServer.port}`);');
  const url=new URL(launch);url.pathname='/connect';url.searchParams.set('interactions','none');
  const exchange=await fetch(url,{redirect:'manual'});
  if(exchange.status!==302) throw Error(`Desktop connection exchange failed: ${exchange.status}`);
  const cookie=exchange.headers.getSetCookie().map(x=>x.split(';')[0]).join('; ');
  if(!cookie) throw Error('Desktop connection returned no credential');
  const origin=url.origin;
  async function call(method,args={}){
    const response=await fetch(origin+'/api/'+method,{method:'POST',headers:{'Content-Type':'application/json',Cookie:cookie},
      body:JSON.stringify({type:'client-request',rpcId:'eval-'+(++seq),method,payload:{args}}),signal:AbortSignal.timeout(45000)});
    if(!response.ok) throw Error(`${method}: HTTP ${response.status}`);
    const message=await response.json();
    if(!message.result?.ok) throw Error(`${method}: ${JSON.stringify(message.result?.error)}`);
    return message.result.value;
  }
  return {call,evaluate,origin,close:()=>socket.close()};
}
