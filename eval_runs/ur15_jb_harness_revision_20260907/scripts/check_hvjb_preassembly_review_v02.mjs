// Copyright (c) 2022-2026, The Isaac Lab Project Developers.
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
// Reuse the local Chrome/CDP check pattern; this checks UI, not assembly validity.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory='/home/rlrk/Downloads/THREAD_HVJB_外組み工程_v02_20260916';
const expected=JSON.parse(await readFile(join(directory,'process_correspondence.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-process-browser-'));
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
  for(let i=0;i<100;i++){ready=await evaluate('window.processReviewReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  const initial=await evaluate(`({features:document.querySelectorAll('#features tr').length,operations:document.querySelectorAll('#operations tr').length,requirements:document.querySelectorAll('#requirements tr').length,groups:document.querySelectorAll('#connections tr').length,cells:document.querySelectorAll('#cells .card').length,entities:document.querySelectorAll('#entities tr').length,handoffs:document.querySelectorAll('#handoffs tr').length,archiveFrames:document.querySelectorAll('#all-frames a').length})`);
  if(initial.features!==expected.feature_correspondence.length||initial.operations!==expected.operations.length||initial.requirements!==17||initial.groups!==13||initial.cells!==3||initial.entities!==expected.observed_entities.length||initial.handoffs!==expected.handoff_roles.length||initial.archiveFrames!==18)throw new Error(JSON.stringify(initial));
  const evidence=[];
  for(let i=0;i<expected.observations.length;i++){
    const state=await evaluate(`new Promise((resolve,reject)=>{document.querySelector('[data-evidence="${i}"]').click();const img=document.getElementById('evidence-image');img.decode().then(()=>resolve({index:window.processEvidenceIndex,width:img.naturalWidth,height:img.naturalHeight,url:document.getElementById('source-link').href,markers:document.querySelectorAll('#markers circle').length,legend:document.querySelectorAll('#marker-legend li').length,rawImage:document.getElementById('full-image').getAttribute('href')})).catch(reject);})`);
    const entry=expected.observations[i],frame=expected.source_video_evidence.frames[entry.frame];
    if(state.index!==i||state.width!==frame.size_px[0]||state.height!==frame.size_px[1]||state.url!==entry.source_url||state.markers!==entry.markers.length||state.legend!==entry.markers.length||state.rawImage!==entry.local_image)throw new Error(JSON.stringify(state));
    evidence.push(state);
  }
  const toggle=await evaluate(`document.getElementById('toggle-annotations').click();const hidden=getComputedStyle(document.getElementById('markers')).display==='none';document.getElementById('toggle-annotations').click();({hidden,visible:getComputedStyle(document.getElementById('markers')).display!=='none'})`);
  if(!toggle.hidden||!toggle.visible)throw new Error('Annotation toggle failed');
  const filters=[];
  for(const cell of ['A','B','C','PREP','SUPPLY']){
    const ids=await evaluate(`document.getElementById('cell-filter').value='${cell}';document.getElementById('cell-filter').dispatchEvent(new Event('change'));window.processVisibleIds`);
    const wanted=expected.feature_correspondence.filter(r=>r.candidate_cells.includes(cell)).map(r=>r.id);
    if(JSON.stringify(ids)!==JSON.stringify(wanted))throw new Error('Cell filter '+cell);
    filters.push({cell,count:ids.length});
  }
  const searched=await evaluate(`document.getElementById('cell-filter').value='';document.getElementById('search').value='P02';document.getElementById('search').dispatchEvent(new Event('input'));window.processVisibleIds`);
  if(JSON.stringify(searched)!==JSON.stringify(['P02']))throw new Error('ID search failed');
  await evaluate(`document.getElementById('search').value='';document.getElementById('search').dispatchEvent(new Event('input'));document.querySelector('[data-evidence="4"]').click();window.scrollTo(0,0);`);
  await pause(200);
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_review.png'),Buffer.from(shot.data,'base64'));
  for(const [index,seconds] of [[4,146],[8,170]]){
    await evaluate(`document.querySelector('[data-evidence="${index}"]').click();document.getElementById('evidence-buttons').closest('section').scrollIntoView();document.getElementById('evidence-image').decode()`);
    const evidenceShot=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(join(directory,`browser_evidence_${seconds}s.png`),Buffer.from(evidenceShot.data,'base64'));
  }
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  const missing=[];
  for(const link of links){if(link.startsWith('http')||link.startsWith('#'))continue;try{await readFile(join(directory,decodeURIComponent(link)));}catch{missing.push(link);}}
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:920,deviceScaleFactor:1,mobile:false});
  await evaluate('window.scrollTo(0,0)');
  await pause(200);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,brokenImages:Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).length})`);
  const mobileShot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(mobileShot.data,'base64'));
  if(mobile.documentWidth>mobile.width||mobile.brokenImages||missing.length||errors.length)throw new Error(JSON.stringify({mobile,missing,errors}));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const deliveryAudit=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==deliveryAudit.generated_page_sha256)throw new Error('Page changed after packaging');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,initial,evidence,toggle,filters,search:searched,mobile,missing_links:missing,javascript_errors:errors,scope:'Offline UI and source-link checks only; no physical acceptance'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_preassembly_browser_v02.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('PREASSEMBLY_V02_BROWSER_OK',JSON.stringify({initial,evidence:evidence.length,toggle,filters,missing:missing.length,errors:errors.length,mobile}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
