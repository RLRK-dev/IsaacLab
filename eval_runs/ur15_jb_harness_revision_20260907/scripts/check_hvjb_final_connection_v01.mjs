// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP checks from check_hvjb_wire_origin_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory=process.argv[2]||'/home/rlrk/Downloads/THREAD_HVJB_最終接続と保持_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-final-connection-browser-'));
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
  const exports={};
  const screenshot=async name=>{
    const shot=await call('Page.captureScreenshot',{format:'png'});
    const bytes=Buffer.from(shot.data,'base64');
    await writeFile(join(directory,name),bytes,{flag:'wx'});
    exports[name]=createHash('sha256').update(bytes).digest('hex');
  };
  await call('Runtime.enable');await call('Page.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1320,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.connectionReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  await evaluate('document.fonts.ready.then(()=>true)');
  const images={};
  for(const id of ['row242','main248'])images[id]='data:image/png;base64,'+(await readFile(join(directory,expected.views.find(v=>v.id===id).frame.local_image))).toString('base64');
  const overview=await evaluate(`window.exportConnectionOverview(${JSON.stringify(images)})`);
  await writeFile(join(directory,'overview.svg'),overview,{flag:'wx'});
  exports['overview.svg']=createHash('sha256').update(overview).digest('hex');
  await evaluate(`document.getElementById('overview').src='overview.svg?ready=1';document.getElementById('overview').decode().then(()=>true)`);
  const cases=[],links=new Set();
  for(const view of expected.views){
    await evaluate(`document.querySelector('[data-view="${view.id}"]').click()`);
    const size=await evaluate('window.frameLoaded');
    if(!equal(size,view.frame.size_px))throw new Error('Source image size mismatch');
    const actual=await evaluate(`({image:document.getElementById('source-image').getAttribute('href'),markers:[...document.querySelectorAll('[data-marker]')].map(m=>({id:m.dataset.marker,xy:m.dataset.xy})),observation:document.getElementById('observation').textContent,limit:document.getElementById('limit').textContent})`);
    if(actual.image!==view.frame.local_image||!equal(actual.markers,view.markers.map(m=>({id:m.id,xy:m.xy_px.join(',')})))||actual.observation!==view.observation_ja||actual.limit!==view.limit_ja)throw new Error(JSON.stringify(actual));
    for(const mode of ['full','focus']){
      await evaluate(`document.getElementById('${mode}').click()`);
      for(const annotations of [false,true]){
        await evaluate(`document.getElementById('annotations').click()`);
        const state=await evaluate('window.connectionState');
        const expectedState={view:view.id,zoom:mode==='focus',annotated:annotations,viewBox:mode==='focus'?view.focus_px:[0,0,1920,1080]};
        if(!equal(state,expectedState))throw new Error(JSON.stringify(state));
        const rendered=await evaluate(`({box:document.getElementById('frame').getAttribute('viewBox'),visible:document.getElementById('overlay').style.display!=='none'})`);
        if(rendered.visible!==annotations||rendered.box!==state.viewBox.join(' '))throw new Error('Viewport mismatch');
        cases.push(state);
      }
    }
    for(const link of await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')).filter(h=>!/^https?:/.test(h))`))links.add(link);
    if(['row242','main248','tool256'].includes(view.id))await screenshot(`browser_${view.id}.png`);
  }
  const roles=await evaluate(`Array.from(document.querySelectorAll('[data-role]')).map(e=>({id:e.dataset.role,text:e.innerText}))`);
  for(const role of expected.holding_comparison.roles){
    const actual=roles.find(r=>r.id===role.id);
    if(!actual||![role.name_ja,role.target_ja,role.action_ja,role.caution_ja].every(s=>actual.text.includes(s)))throw new Error('Role text mismatch');
  }
  const stages=await evaluate(`Array.from(document.querySelectorAll('[data-stage]')).map(e=>e.dataset.stage)`);
  if(!equal(stages,expected.holding_comparison.stages.map(s=>s.id)))throw new Error('Stage order mismatch');
  await evaluate(`document.querySelector('[data-view="row242"]').click();window.scrollTo(0,0)`);
  await evaluate('window.frameLoaded');
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:1150,deviceScaleFactor:1,mobile:false});
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,views:document.querySelectorAll('[data-view]').length})`);
  if(mobile.documentWidth>mobile.width||mobile.views!==7)throw new Error(JSON.stringify(mobile));
  await screenshot('browser_mobile.png');
  await call('Page.navigate',{url:pathToFileURL(join(directory,'overview.svg')).href});
  let svgReady=false;
  for(let i=0;i<100;i++){svgReady=await evaluate(`document.documentElement.tagName==='svg'`);if(svgReady)break;await pause(100);}
  if(!svgReady)throw new Error('Standalone SVG did not load');
  await evaluate('document.fonts.ready.then(()=>true)');
  await evaluate(`Promise.all([...document.querySelectorAll('image')].map(e=>new Promise((resolve,reject)=>{const im=new Image();im.onload=resolve;im.onerror=reject;im.src=e.getAttribute('href');}))).then(()=>true)`);
  await call('Emulation.setDeviceMetricsOverride',{width:1380,height:1060,deviceScaleFactor:1,mobile:false});
  await screenshot('overview.png');
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  if(errors.length)throw new Error(JSON.stringify(errors));
  const audit=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex')!==audit.page_sha256)throw new Error('Packaged page changed');
  const report={observed_at:new Date().toISOString(),directory,cases,roles,stages,mobile,local_links:[...links],exports_sha256:exports,javascript_errors:errors,scope:'UI, image and text correspondence only; no wire-completeness, release or physical acceptance verdict'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_final_connection_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('FINAL_CONNECTION_BROWSER_OK',JSON.stringify({cases:cases.length,links:links.size,mobile,roles:roles.length,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
