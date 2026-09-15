// Copyright (c) 2022-2026, The Isaac Lab Project Developers.
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
// Reuse the existing isolated Chrome/CDP checks for the new offline interface page.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory='/home/rlrk/Downloads/THREAD_HVJB_開口ヘッダー照合_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'interface_review.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-header-browser-'));
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
  if(!page)throw new Error('Own blank page not found');
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
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.headerReviewReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  const counts=await evaluate(`({apertures:document.querySelectorAll('#apertures tr').length,steps:document.querySelectorAll('#steps tr').length,archive:document.querySelectorAll('#archive a').length,documents:document.querySelectorAll('#documents li').length,changed:document.querySelectorAll('.changed').length,featureIds:data.feature_ids.length})`);
  if(counts.apertures!==5||counts.steps!==6||counts.archive!==19||counts.documents!==4||counts.changed!==3||counts.featureIds!==92)throw new Error(JSON.stringify(counts));
  const apertures=[];
  for(let i=0;i<5;i++){
    const state=await evaluate(`document.getElementById('bay').value='${i}';document.getElementById('bay').dispatchEvent(new Event('change'));({id:window.headerProjectionId,width:Number(document.getElementById('opening').getAttribute('width')),height:Number(document.getElementById('opening').getAttribute('height')),radius:Number(document.getElementById('opening').getAttribute('rx')),outline:document.getElementById('housing').getAttribute('d'),text:document.getElementById('projection-result').textContent})`);
    const row=expected.apertures[i];
    if(state.id!==row.id||state.width!==row.width_m*1000||state.height!==13.5||state.radius!==4.4||!state.outline.endsWith('Z')||!state.text.includes((row.projection.minimum_nominal_projected_inward_distance_m*1000).toFixed(3)))throw new Error(JSON.stringify(state));
    apertures.push(state);
  }
  const toggle=await evaluate(`document.getElementById('old-outline').click();const hidden=getComputedStyle(document.getElementById('old-opening')).display==='none';document.getElementById('old-outline').click();({hidden,shown:getComputedStyle(document.getElementById('old-opening')).display!=='none'})`);
  if(!toggle.hidden||!toggle.shown)throw new Error('Outline toggle failed');
  const frames=[];
  for(let i=0;i<expected.observations.length;i++){
    const state=await evaluate(`new Promise((resolve,reject)=>{document.querySelector('[data-frame="${i}"]').click();const img=document.getElementById('evidence-image');img.decode().then(()=>resolve({index:window.headerEvidenceIndex,width:img.naturalWidth,height:img.naturalHeight,url:document.getElementById('source-link').href,image:document.getElementById('raw-image').getAttribute('href'),pressed:document.querySelectorAll('[data-frame][aria-pressed="true"]').length})).catch(reject);})`);
    const row=expected.observations[i];
    if(state.index!==i||state.width!==1920||state.height!==1080||state.url!==row.source_url||state.image!==row.image||state.pressed!==1)throw new Error(JSON.stringify(state));
    frames.push(state);
  }
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  const missing=[];
  for(const link of links){if(link.startsWith('http')||link.startsWith('#'))continue;try{await readFile(join(directory,decodeURIComponent(link.split('#')[0])));}catch{missing.push(link);}}
  await evaluate(`document.getElementById('bay').value='0';document.getElementById('bay').dispatchEvent(new Event('change'));window.scrollTo(0,0);`);
  await pause(200);
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_review.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  await evaluate(`document.querySelector('[data-frame="3"]').click();document.getElementById('frames').closest('section').scrollIntoView();document.getElementById('evidence-image').decode()`);
  const evidenceShot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_evidence.png'),Buffer.from(evidenceShot.data,'base64'),{flag:'wx'});
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:920,deviceScaleFactor:1,mobile:false});
  await evaluate('window.scrollTo(0,0)');await pause(200);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,brokenImages:Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).length})`);
  const mobileShot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(mobileShot.data,'base64'),{flag:'wx'});
  if(mobile.documentWidth>mobile.width||mobile.brokenImages||missing.length||errors.length)throw new Error(JSON.stringify({mobile,missing,errors}));
  const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  const pageSha=digest(await readFile(join(directory,'review.html')));
  if(pageSha!==delivery.page_sha256)throw new Error('Packaged page changed');
  const copied=await Promise.all(delivery.copied_files.map(async row=>({file:row.file,equal:digest(await readFile(join(directory,row.file)))===row.sha256})));
  if(copied.some(row=>!row.equal))throw new Error('Packaged source changed');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,counts,apertures,toggle,frames,mobile,missing_links:missing,javascript_errors:errors,copy_hashes_equal:copied,scope:'Offline UI, dimension labels and file identity only; no physical acceptance'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_header_interface_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('HEADER_INTERFACE_BROWSER_OK',JSON.stringify({counts,toggle,frames:frames.length,missing:missing.length,errors:errors.length,mobile}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
