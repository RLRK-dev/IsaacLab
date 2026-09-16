// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP procedure in check_hvjb_receiving_support_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory=process.argv[2]||'/home/rlrk/Downloads/THREAD_HVJB_受渡し対象と手先_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-interface-browser-'));
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
let socket;
try{
  let port;
  for(let i=0;i<50;i++){
    try{port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break;}
    catch{await pause(100);}
  }
  if(!port)throw new Error('No own DevTools port');
  const pages=await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page=pages.find(p=>p.type==='page'&&p.url==='about:blank');
  if(!page)throw new Error('Own blank target not found');
  socket=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  let serial=0;
  const waiting=new Map(),errors=[];
  socket.onmessage=event=>{
    const message=JSON.parse(event.data);
    if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails);
    if(message.id){const pair=waiting.get(message.id);waiting.delete(message.id);if(message.error)pair.reject(message.error);else pair.resolve(message.result);}
  };
  const call=(method,params={})=>new Promise((resolve,reject)=>{
    const id=++serial;waiting.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));
  });
  const evaluate=async expression=>{
    const result=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if(result.exceptionDetails)throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const decodeImage=()=>evaluate(`document.getElementById('source-image').decode().then(()=>true)`);
  const screenshot=async name=>{
    const shot=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(join(directory,name),Buffer.from(shot.data,'base64'),{flag:'wx'});
  };
  await call('Runtime.enable');await call('Page.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1300,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.interfacesReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  await evaluate('document.fonts.ready.then(()=>true)');
  const cases=[];
  for(const target of expected.targets){
    await evaluate(`document.querySelector('[data-target="${target.id}"]').click()`);
    for(const view of target.view_data){
      await evaluate(`document.querySelector('[data-second="${view.second}"]').click()`);
      await decodeImage();
      const actual=await evaluate(`({state:window.interfaceState,markers:[...document.querySelectorAll('#markers g')].map(n=>({entity:n.dataset.entity,xy:n.dataset.xy})),candidates:[...document.querySelectorAll('[data-candidate]')].map(n=>n.dataset.candidate),source:document.getElementById('source-image').getAttribute('src'),size:[document.getElementById('source-image').naturalWidth,document.getElementById('source-image').naturalHeight],intent:document.getElementById('contact-intent').textContent,clear:document.getElementById('keep-clear').textContent,next:document.getElementById('next').textContent,profile:document.getElementById('hand-title').textContent})`);
      if(!equal(actual.state,{target:target.id,second:view.second,entity:target.entity,profile:target.profile,markers:view.markers,candidates:target.model_candidates.map(c=>c.id)}))throw new Error(JSON.stringify(actual));
      if(!equal(actual.markers,view.markers.map(m=>({entity:m.entity,xy:m.xy_px.join(',')})))||!equal(actual.candidates,target.model_candidates.map(c=>c.id)))throw new Error('Rendered correspondence mismatch');
      const frame=expected.frames[view.second];
      if(actual.source!==frame.local_image||!equal(actual.size,frame.size_px)||actual.intent!==target.contact_intent_ja||actual.clear!==target.clear_ja||actual.next!==target.next_ja||!actual.profile.startsWith(target.profile+'系'))throw new Error(JSON.stringify(actual));
      cases.push(actual);
    }
    await evaluate(`document.querySelector('[data-second="${target.default_view}"]').click();window.scrollTo(0,0)`);
    await decodeImage();await screenshot(`browser_${target.id.toLowerCase()}.png`);
  }
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')).filter(h=>!/^https?:/.test(h))`);
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:1150,deviceScaleFactor:1,mobile:false});
  await pause(100);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,targets:document.querySelectorAll('[data-target]').length})`);
  if(mobile.documentWidth>mobile.width||mobile.targets!==4)throw new Error(JSON.stringify(mobile));
  await screenshot('browser_mobile.png');
  const images={};
  for(const second of [24,154])images[second]='data:image/png;base64,'+(await readFile(join(directory,expected.frames[second].local_image))).toString('base64');
  const overview=await evaluate(`window.exportInterfaceOverview(${JSON.stringify(images)})`);
  await writeFile(join(directory,'overview.svg'),overview,{flag:'wx'});
  await call('Page.navigate',{url:pathToFileURL(join(directory,'overview.svg')).href});
  for(let i=0;i<100;i++){if(await evaluate(`document.documentElement.tagName==='svg'`))break;await pause(100);}
  if(!await evaluate(`document.documentElement.tagName==='svg'`))throw new Error('Standalone SVG did not load');
  await evaluate('document.fonts.ready.then(()=>true)');
  await evaluate(`Promise.all([...document.querySelectorAll('image')].map(e=>new Promise((resolve,reject)=>{const im=new Image();im.onload=resolve;im.onerror=reject;im.src=e.getAttribute('href');}))).then(()=>true)`);
  await call('Emulation.setDeviceMetricsOverride',{width:1380,height:1030,deviceScaleFactor:1,mobile:false});
  await pause(100);await screenshot('overview.png');
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  if(errors.length)throw new Error(JSON.stringify(errors));
  const sha=name=>readFile(join(directory,name)).then(bytes=>createHash('sha256').update(bytes).digest('hex'));
  const audit=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(await sha('review.html')!==audit.page_sha256)throw new Error('Packaged page changed');
  const exports={};
  for(const name of ['overview.svg','overview.png','browser_base.png','browser_panel.png','browser_inner.png','browser_ring.png','browser_mobile.png'])exports[name]=await sha(name);
  const report={observed_at:new Date().toISOString(),directory,cases,mobile,local_links:links,exports_sha256:exports,javascript_errors:errors,scope:'UI, saved-source correspondence and display-mesh metadata only; no physical judgment'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_receiving_interfaces_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('RECEIVING_INTERFACES_BROWSER_OK',JSON.stringify({target_views:cases.length,links:links.length,mobile,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
