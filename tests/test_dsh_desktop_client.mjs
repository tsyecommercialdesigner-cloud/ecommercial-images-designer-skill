import {test} from 'node:test';
import assert from 'node:assert/strict';
import {connectDesktop} from '../scripts/dsh_desktop_client.mjs';

test('Host loss rejects pending Inspector work instead of hanging cleanup',async()=>{
  const previousFetch=globalThis.fetch,previousSocket=globalThis.WebSocket;
  let socket,requests=0;
  class Socket {
    static OPEN=1;
    readyState=1;
    constructor(){socket=this;queueMicrotask(()=>this.onopen());}
    send(raw){const message=JSON.parse(raw);if(++requests===1)queueMicrotask(()=>
      this.onmessage({data:JSON.stringify({id:message.id,result:{result:{value:'http://127.0.0.1:7413/?token=synthetic'}}})}));}
    close(){this.readyState=3;this.onclose?.();}
  }
  globalThis.WebSocket=Socket;
  globalThis.fetch=async url=>String(url).endsWith('/json/list')?
    {json:async()=>[{url:'dsh://host',webSocketDebuggerUrl:'ws://synthetic'}]}:
    {status:302,headers:{getSetCookie:()=>['session=synthetic; Path=/']}};
  try{
    const client=await connectDesktop();
    const pending=client.evaluate('return 1;');socket.close();
    await assert.rejects(pending,/disconnected/);
    await assert.rejects(client.evaluate('return 2;'),/closed/);
  }finally{globalThis.fetch=previousFetch;globalThis.WebSocket=previousSocket;}
});
