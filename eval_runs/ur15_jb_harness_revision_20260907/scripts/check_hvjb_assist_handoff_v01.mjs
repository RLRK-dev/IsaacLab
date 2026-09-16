// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// The own-profile Chrome path is reused from check_hvjb_robot_diagram_v02.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory=process.argv[2]||'/home/rlrk/Downloads/THREAD_HVJB_補助腕の保持と受渡し_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-handoff-browser-'));
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
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1250,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.handoffReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  await evaluate('document.fonts.ready.then(()=>true)');
  const cases=[];
  for(const order of ['AB','BA']){
    await evaluate(`document.getElementById('order').value='${order}';document.getElementById('order').dispatchEvent(new Event('change'))`);
    for(const phase of expected.phases){
      await evaluate(`document.querySelector('[data-phase="${phase.id}"]').click()`);
      const actual=await evaluate(`({state:window.handoffState,units:[...document.querySelectorAll('#role-diagram .arm-icon')].map(n=>n.dataset.unit),owners:[...document.querySelectorAll('.ab-link')].map(n=>n.dataset.owner),description:document.getElementById('phase-description').textContent})`);
      const owner=phase.owner==='first'?order[0]:phase.owner==='second'?order[1]:null;
      if(actual.state.owner!==owner||actual.state.order!==order||actual.state.phase!==phase.id||actual.state.busy!==phase.busy||actual.state.cTask!=='D40'||actual.description!==phase.explanation_ja)throw new Error(JSON.stringify(actual));
      if(actual.units.join(',')!=='ARM_A,ARM_B,ARM_C,ASSIST_1,ASSIST_2'||actual.owners.length!==(owner?1:0)||owner&&actual.owners[0]!==owner)throw new Error(JSON.stringify(actual));
      cases.push(actual);
    }
  }
  const cCases=[];
  for(const card of expected.assist_groups[1].cards){
    await evaluate(`document.querySelector('[data-c-task="${card.id}"]').click()`);
    const actual=await evaluate(`({state:window.handoffState,start:document.getElementById('c-start').textContent,keep:document.getElementById('c-keep').textContent,end:document.getElementById('c-end').textContent,reuse:document.getElementById('c-reuse').textContent,missing:document.getElementById('c-missing').textContent})`);
    if(actual.state.cTask!==card.id||actual.state.order!=='BA'||actual.state.phase!=='next_grasp'||actual.start!=='開始：'+card.start_ja||actual.keep!=='継続：'+card.keep_ja||actual.end!=='区切り：'+card.end_ja||actual.reuse!==card.reuse_ja||actual.missing!=='具体化が必要：'+card.missing_ja)throw new Error(JSON.stringify(actual));
    cCases.push(actual);
  }
  const taskIds=await evaluate(`Array.from(document.querySelectorAll('[data-task]')).map(n=>n.dataset.task)`);
  if(JSON.stringify(taskIds)!==JSON.stringify(expected.assist_groups.flatMap(g=>g.cards.map(c=>c.id))))throw new Error('Incomplete auxiliary work table');
  await evaluate(`document.getElementById('order').value='AB';document.getElementById('order').dispatchEvent(new Event('change'));document.querySelector('[data-phase="handoff_wait"]').click();document.querySelector('[data-c-task="D40"]').click();window.scrollTo(0,0)`);
  let shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_desktop.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  const overview=await evaluate('window.exportHandoffOverview()');
  await writeFile(join(directory,'overview.svg'),overview,{flag:'wx'});
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:1150,deviceScaleFactor:1,mobile:false});
  await pause(100);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,units:document.querySelectorAll('.arm-icon').length})`);
  if(mobile.width<mobile.documentWidth||mobile.units!==5)throw new Error(JSON.stringify(mobile));
  shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  await call('Page.navigate',{url:pathToFileURL(join(directory,'overview.svg')).href});
  for(let i=0;i<100;i++){if(await evaluate(`document.documentElement.tagName==='svg'`))break;await pause(100);}
  if(!await evaluate(`document.documentElement.tagName==='svg'`))throw new Error('Standalone SVG did not load');
  await evaluate('document.fonts.ready.then(()=>true)');
  await call('Emulation.setDeviceMetricsOverride',{width:1320,height:810,deviceScaleFactor:1,mobile:false});
  await pause(100);
  shot=await call('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:1320,height:810,scale:1}});
  await writeFile(join(directory,'overview.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  if(errors.length)throw new Error(JSON.stringify(errors));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==delivery.page_sha256)throw new Error('Page changed after packaging');
  const exports={};
  for(const name of ['overview.svg','overview.png','browser_desktop.png','browser_mobile.png'])exports[name]=createHash('sha256').update(await readFile(join(directory,name))).digest('hex');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,cases,c_cases:cCases,assist_task_ids:taskIds,mobile,local_links:links,exports_sha256:exports,javascript_errors:errors,scope:'UI and source-text correspondence only; not a physical or cycle-time verdict'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_assist_handoff_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('ASSIST_HANDOFF_BROWSER_OK',JSON.stringify({ab_cases:cases.length,c_cases:cCases.length,tasks:taskIds.length,links:links.length,mobile,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
