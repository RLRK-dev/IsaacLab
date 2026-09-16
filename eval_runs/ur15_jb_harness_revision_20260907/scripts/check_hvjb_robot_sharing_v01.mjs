// Copyright (c) 2022-2026, The Isaac Lab Project Developers.
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP path for UI verification, not physical judgment.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory='/home/rlrk/Downloads/THREAD_HVJB_ロボット共用比較_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-sharing-browser-'));
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
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
  await call('Runtime.enable');await call('Page.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1150,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.sharingReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  const initial=await evaluate(`({plans:document.querySelectorAll('[data-plan]').length,rows:document.querySelectorAll('#matrix tr').length,equipment:document.querySelectorAll('#equipment tr').length,selected:window.sharingSelected,scene:window.sharingScene})`);
  if(initial.plans!==5||initial.rows!==8||initial.equipment!==11||initial.selected!=='S4'||initial.scene!=='AC')throw new Error(JSON.stringify(initial));
  const cases=[];
  for(const plan of expected.plans){
    await evaluate(`document.querySelector('[data-plan="${plan.id}"]').click()`);
    for(const scene of plan.scenarios){
      const actual=await evaluate(`for(const c of ['A','B','C']){const box=document.getElementById('assist-'+c);box.checked=${JSON.stringify(scene.active_assists)}.includes('X-'+c);box.dispatchEvent(new Event('change'));}({plan:window.sharingSelected,scene:window.sharingScene,units:document.querySelectorAll('[data-unit]').length,overlap:Array.from(document.querySelectorAll('.unit.overlap')).map(n=>n.dataset.unit),tasks:document.querySelectorAll('[data-task]').length,result:document.getElementById('scene-result').textContent})`);
      if(actual.plan!==plan.id||actual.scene!==scene.id||actual.units!==plan.arm_slots||actual.tasks!==20||JSON.stringify(actual.overlap.sort())!==JSON.stringify(Object.keys(scene.duplicate_assignments).sort()))throw new Error(JSON.stringify(actual));
      cases.push(actual);
    }
  }
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  const oldPage=await readFile(join(directory,'workcards/review.html'),'utf8');
  const oldLinks=[...oldPage.matchAll(/href="([^"]+)"/g)].map(m=>m[1]).filter(link=>!link.startsWith('http')&&!link.startsWith('#'));
  for(const link of oldLinks)await readFile(join(directory,'workcards',decodeURIComponent(link)));
  for(const plan of ['S4','S5_AB']){
    await evaluate(`document.querySelector('[data-plan="${plan}"]').click();for(const c of ['A','B','C']){const box=document.getElementById('assist-'+c);box.checked=c!=='B';box.dispatchEvent(new Event('change'));}window.scrollTo(0,0)`);
    await pause(100);
    const shot=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(join(directory,`browser_${plan}.png`),Buffer.from(shot.data,'base64'));
  }
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:1050,deviceScaleFactor:1,mobile:false});
  await evaluate('window.scrollTo(0,0)');await pause(100);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,plan:window.sharingSelected,scene:window.sharingScene})`);
  if(mobile.documentWidth>mobile.width||errors.length)throw new Error(JSON.stringify({mobile,errors}));
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(shot.data,'base64'));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==delivery.page_sha256)throw new Error('Page changed after packaging');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,initial,cases,local_links:links,workcard_links:oldLinks,mobile,javascript_errors:errors,scope:'Conditional role-ID display and local artifacts only; no physical or scheduling verdict'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_robot_sharing_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('ROBOT_SHARING_BROWSER_OK',JSON.stringify({cases:cases.length,links:links.length,workcardLinks:oldLinks.length,mobile,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
