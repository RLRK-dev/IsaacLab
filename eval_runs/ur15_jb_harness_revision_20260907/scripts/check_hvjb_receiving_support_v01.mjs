// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP path from check_hvjb_assist_handoff_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory=process.argv[2]||'/home/rlrk/Downloads/THREAD_HVJB_C側の受渡し_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-receiving-browser-'));
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const equal=(actual,wanted)=>JSON.stringify(actual)===JSON.stringify(wanted);
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
  for(let i=0;i<100;i++){ready=await evaluate('window.receivingReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  await evaluate('document.fonts.ready.then(()=>true)');
  const cases=[];
  for(const state of expected.states){
    await evaluate(`document.querySelector('[data-state="${state.id}"]').click()`);
    const actual=await evaluate(`({state:window.receivingState,units:[...document.querySelectorAll('#support-diagram .arm-icon')].map(n=>n.dataset.unit),links:[...document.querySelectorAll('.ownership-link')].map(n=>[n.dataset.target,n.dataset.actor]),rows:[...document.querySelectorAll('[data-target-row]')].map(n=>n.dataset.targetRow),description:document.getElementById('state-description').textContent,selected:[...document.querySelectorAll('button[aria-pressed=true]')].map(n=>n.dataset.state),result:document.getElementById('state-result').textContent})`);
    const wantedLinks=Object.entries(state.owners).flatMap(([target,owners])=>owners.map(owner=>[target,owner]));
    if(actual.state.id!==state.id||!equal(actual.state.owners,state.owners)||!equal(actual.state.observations,state.observations)||!equal(actual.state.busy,state.busy_nonholding)||actual.description!==state.detail_ja)throw new Error(JSON.stringify(actual));
    if(!equal(actual.links,wantedLinks)||!equal(actual.rows,Object.keys(state.owners))||!equal(actual.selected,[state.id])||actual.units.join(',')!=='ARM_A,ARM_B,ARM_C,ASSIST_1,ASSIST_2')throw new Error(JSON.stringify(actual));
    cases.push(actual);
  }
  const sourceCards=await evaluate(`Array.from(document.querySelectorAll('#source-cards h3')).map(n=>n.textContent.split('｜')[0])`);
  if(!equal(sourceCards,['D12','D22','D30'])||expected.all_source_task_ids.length!==20||new Set(expected.all_source_task_ids).size!==20)throw new Error('Source task references incomplete');
  const retained=cases.find(c=>c.state.id==='B_KEEP').state.observations;
  if(!equal(retained.holding_arms,['ARM_C','ASSIST_1','ASSIST_2'])||!retained.shared_assistant_reserved)throw new Error('B retention assignment changed');
  const overlapping=cases.find(c=>c.state.id==='B_DOUBLE').state.observations;
  const unassigned=cases.find(c=>c.state.id==='B_DROP').state.observations;
  if(!equal(overlapping.duplicate_independent_arm_roles,{ASSIST_2:['A_END','B_END']})||!equal(unassigned.unassigned_targets,['B_END']))throw new Error('Missing diagnostic assignment');
  if(!cases.find(c=>c.state.id==='A_RETREAT').state.observations.shared_assistant_reserved)throw new Error('Retreat counted as free');
  await evaluate(`document.querySelector('[data-state="B_KEEP"]').click();window.scrollTo(0,0)`);
  let shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_desktop.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  const overview=await evaluate('window.exportReceivingOverview()');
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
  await call('Emulation.setDeviceMetricsOverride',{width:1380,height:830,deviceScaleFactor:1,mobile:false});
  await pause(100);
  shot=await call('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:1380,height:830,scale:1}});
  await writeFile(join(directory,'overview.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  if(errors.length)throw new Error(JSON.stringify(errors));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==delivery.page_sha256)throw new Error('Page changed after packaging');
  const exports={};
  for(const name of ['overview.svg','overview.png','browser_desktop.png','browser_mobile.png'])exports[name]=createHash('sha256').update(await readFile(join(directory,name))).digest('hex');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,cases,source_cards:sourceCards,source_task_count:expected.all_source_task_ids.length,mobile,local_links:links,exports_sha256:exports,javascript_errors:errors,scope:'UI and assignment bookkeeping only; not grasp, load, reach or cycle-time validation'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_receiving_support_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('RECEIVING_SUPPORT_BROWSER_OK',JSON.stringify({states:cases.length,source_tasks:expected.all_source_task_ids.length,links:links.length,mobile,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
