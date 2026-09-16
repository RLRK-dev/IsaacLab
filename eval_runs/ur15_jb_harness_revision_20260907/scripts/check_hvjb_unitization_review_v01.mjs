// Copyright (c) 2022-2026, The Isaac Lab Project Developers.
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP review checks; no physics or contact verdict.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory='/home/rlrk/Downloads/THREAD_HVJB_支持と受渡し_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-unitization-browser-'));
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
  for(let i=0;i<100;i++){ready=await evaluate('window.unitizationReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  const stateResults=[];
  for(let i=0;i<expected.states.length;i++){
    const actual=await evaluate(`document.querySelector('[data-state="${i}"]').click();({index:window.unitizationIndex,title:document.getElementById('step-title').textContent,detail:document.getElementById('step-detail').textContent,release:document.getElementById('release').textContent,active:Array.from(document.querySelectorAll('.node.active')).map(n=>n.id.slice(5)),joined:document.getElementById('join-line').classList.contains('active'),selectedRows:document.querySelectorAll('#matrix tr.selected').length,second:window.unitizationSecond})`);
    const row=expected.states[i];
    if(actual.index!==i||actual.title!==row.title_ja||actual.detail!==row.detail_ja||actual.release!==row.before_release_ja||actual.joined!==row.joined_assumption||actual.selectedRows!==1||actual.second!==row.image_second||JSON.stringify([...actual.active].sort())!==JSON.stringify([...row.active].sort()))throw new Error(JSON.stringify(actual));
    stateResults.push(actual);
  }
  const sources=[];
  for(const row of expected.evidence_views){
    const actual=await evaluate(`document.querySelector('[data-second="${row.second}"]').click();document.getElementById('evidence-image').decode().then(()=>({second:window.unitizationSecond,width:document.getElementById('evidence-image').naturalWidth,height:document.getElementById('evidence-image').naturalHeight,url:document.getElementById('source-link').href,raw:document.getElementById('full-image').getAttribute('href'),markers:document.querySelectorAll('#markers circle').length,viewBox:document.getElementById('markers').getAttribute('viewBox')}))`);
    if(actual.second!==row.second||actual.width!==row.frame.size_px[0]||actual.height!==row.frame.size_px[1]||actual.url!==row.frame.url||actual.raw!==row.local_image||actual.markers!==row.markers.length||actual.viewBox!==`0 0 ${row.frame.size_px.join(' ')}`)throw new Error(JSON.stringify(actual));
    sources.push(actual);
  }
  const toggle=await evaluate(`document.getElementById('toggle-markers').click();const hidden=getComputedStyle(document.getElementById('markers')).display==='none';document.getElementById('toggle-markers').click();({hidden,visible:getComputedStyle(document.getElementById('markers')).display!=='none'})`);
  if(!toggle.hidden||!toggle.visible)throw new Error('Marker toggle failed');
  const initial=await evaluate(`({stateButtons:document.querySelectorAll('[data-state]').length,rows:document.querySelectorAll('#matrix tr').length,interfaces:document.querySelectorAll('#interface-cards article').length})`);
  if(initial.stateButtons!==9||initial.rows!==9||initial.interfaces!==6)throw new Error(JSON.stringify(initial));
  for(const index of [2,5,7]){
    await evaluate(`document.querySelector('[data-state="${index}"]').click();window.scrollTo(0,0)`);
    await pause(100);
    const shot=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(join(directory,`browser_state_${index+1}.png`),Buffer.from(shot.data,'base64'));
  }
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  const missing=[];
  for(const link of links){if(link.startsWith('http')||link.startsWith('#'))continue;try{await readFile(join(directory,decodeURIComponent(link)));}catch{missing.push(link);}}
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:920,deviceScaleFactor:1,mobile:false});
  await evaluate('window.scrollTo(0,0)');await pause(100);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,brokenImages:Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).length})`);
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(shot.data,'base64'));
  if(mobile.documentWidth>mobile.width||mobile.brokenImages||missing.length||errors.length)throw new Error(JSON.stringify({mobile,missing,errors}));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==delivery.generated_page_sha256)throw new Error('Page changed after packaging');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,initial,stateResults,sources,toggle,mobile,missing_links:missing,javascript_errors:errors,scope:'UI and artifact checks only; no contact or physical acceptance'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_unitization_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('UNITIZATION_BROWSER_OK',JSON.stringify({initial,states:stateResults.length,sources:sources.length,toggle,mobile,missing:missing.length,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
