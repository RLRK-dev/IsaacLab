// Copyright (c) 2022-2026, The Isaac Lab Project Developers.
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
// Browser interactions are auxiliary UI checks, not product/physical acceptance.
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const directory='/home/rlrk/Downloads/THREAD_HVJB_写真部品照合_v02_20260915';
const reviewUrl=pathToFileURL(join(directory,'review.html')).href;
const profile=await mkdtemp(join(tmpdir(),'hvjb-photo-browser-'));
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage',
  '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let socket;
try{
  let port;
  for(let i=0;i<50;i++){
    try{port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break;}
    catch{await pause(100);}
  }
  if(!port)throw new Error('Browser did not create DevToolsActivePort');
  const pages=await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  console.log('BROWSER_TARGETS',JSON.stringify(pages.map(p=>({type:p.type,url:p.url}))));
  const page=pages.find(p=>p.type==='page'&&p.url==='about:blank');
  if(!page)throw new Error('Own blank page target not found');
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
  await call('Emulation.setDeviceMetricsOverride',{width:1600,height:1100,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:reviewUrl});
  if(navigation.errorText){
    await pause(500);
    const current=await evaluate('({url:location.href,title:document.title,body:document.body?.innerText.slice(0,1500)})');
    const screenshot=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(join(directory,'audit/browser_navigation_failure.png'),Buffer.from(screenshot.data,'base64'));
    throw new Error(JSON.stringify({navigation,current}));
  }
  let initial;
  for(let i=0;i<200;i++){
    initial=await evaluate('window.photoReviewRendered||null');
    if(initial)break;
    if(errors.length)throw new Error(JSON.stringify(errors));
    await pause(100);
  }
  if(!initial){
    const diagnostic=await evaluate('({url:location.href,title:document.title,ready:document.readyState,body:document.body?.innerText.slice(0,1200),scripts:document.scripts.length,glError:document.getElementById("gl-error")?.hidden})');
    const shot=await call('Page.captureScreenshot',{format:'png'});
    await writeFile(join(directory,'audit/browser_failure.png'),Buffer.from(shot.data,'base64'));
    throw new Error('Timed out before first WebGL draw: '+JSON.stringify({diagnostic,errors}));
  }
  const ids=await evaluate('Array.from(document.querySelectorAll("#feature option")).map(o=>o.value).filter(Boolean)');
  const selected=[];
  for(const id of ids){
    const state=await evaluate(`new Promise(resolve=>{document.getElementById('isolate').checked=true;document.getElementById('feature').value=${JSON.stringify(id)};document.getElementById('feature').dispatchEvent(new Event('change'));requestAnimationFrame(()=>requestAnimationFrame(()=>resolve({render:window.photoReviewRendered,marked:document.querySelectorAll('#marks .selected').length,title:document.getElementById('selected-title').textContent})));})`);
    if(state.render.selected!==id||state.render.shown_features!==1||state.marked!==1||state.render.gl_error!==0)throw new Error(JSON.stringify(state));
    selected.push({id,shown_features:state.render.shown_features,photo_mark_count:state.marked});
  }
  await evaluate("document.getElementById('all').click()");await pause(100);
  const screenshot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  await writeFile(join(directory,'audit/browser_review.png'),Buffer.from(screenshot.data,'base64'));
  const content=await evaluate(`({requirements:document.querySelectorAll('#requirements tr').length,connection_groups:document.querySelectorAll('#connections tr').length,lv_pins:document.querySelectorAll('#pins tr').length,broken_images:Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).length,links:Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')),gl:window.photoReviewRendered})`);
  if(content.connection_groups!==13||content.lv_pins!==12||content.gl.gl_error!==0||!content.gl.finite)throw new Error(JSON.stringify(content));
  const sourceImages=await evaluate(`Promise.all(Object.entries(catalog.photos).map(([id,source])=>new Promise(resolve=>{const image=new Image();image.onload=()=>resolve({id,size:[image.naturalWidth,image.naturalHeight],expected:source.size_px});image.onerror=()=>resolve({id,error:true});image.src=source.file;})))`);
  if(sourceImages.some(r=>r.error||JSON.stringify(r.size)!==JSON.stringify(r.expected)))throw new Error('Source image failed '+JSON.stringify(sourceImages));
  const uncovered=await evaluate(`new Promise(resolve=>{document.getElementById('uncover').checked=true;document.getElementById('uncover').dispatchEvent(new Event('change'));requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.photoReviewRendered)));})`);
  if(uncovered.shown_features!==ids.length-2||uncovered.gl_error!==0)throw new Error(JSON.stringify(uncovered));
  await evaluate("document.getElementById('uncover').checked=false;document.getElementById('uncover').dispatchEvent(new Event('change'))");
  const sourceSelection=await evaluate(`new Promise(resolve=>{document.getElementById('feature').value='P19';document.getElementById('feature').dispatchEvent(new Event('change'));requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.photoReviewRendered)));})`);
  if(sourceSelection.source_view!=='fuse_detail')throw new Error(JSON.stringify(sourceSelection));
  await pause(250);
  const fuseScreenshot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  await writeFile(join(directory,'audit/browser_fuse_evidence.png'),Buffer.from(fuseScreenshot.data,'base64'));
  await evaluate("document.getElementById('all').click()");
  const missing=[];
  for(const link of content.links){
    if(link.startsWith('http')||link.startsWith('#'))continue;
    try{await readFile(join(directory,decodeURIComponent(link)));}catch{missing.push(link);}
  }
  if(missing.length)throw new Error('Missing links: '+JSON.stringify(missing));
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:920,deviceScaleFactor:1,mobile:false});
  await pause(100);
  const mobile=await evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,gl:window.photoReviewRendered})');
  if(mobile.scroll>mobile.client+1)throw new Error('Mobile overflow: '+JSON.stringify(mobile));
  const report={checked_at:new Date().toISOString(),initial,selected,content,mobile,sourceImages,uncovered,sourceSelection,missing_links:missing,
    javascript_errors:errors,scope:'UI display and interaction only; no physical acceptance'};
  const text=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(directory,'audit/browser_review.json'),text);
  await writeFile(fileURLToPath(new URL('../audit/hvjb_photo_browser_v02.json',import.meta.url)),text);
  console.log('PHOTO_BROWSER_CHECKED',JSON.stringify({ids:ids.length,connection_groups:content.connection_groups,lv_pins:content.lv_pins,errors:errors.length}));
}finally{
  if(socket)socket.close();
  chrome.kill('SIGTERM');
}
