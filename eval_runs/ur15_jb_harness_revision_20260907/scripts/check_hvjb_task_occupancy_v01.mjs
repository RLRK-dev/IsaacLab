// Copyright (c) 2022-2026, The Isaac Lab Project Developers.
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP artifact checks; this does not test physics.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory='/home/rlrk/Downloads/THREAD_HVJB_仕事と保持区間_v01_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-occupancy-browser-'));
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
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1120,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.occupancyReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  const initial=await evaluate(`({jobs:document.querySelectorAll('#job option').length,headers:document.querySelectorAll('#headers article').length,functions:document.querySelectorAll('#functions tr').length,electrical:document.querySelectorAll('#electrical tr').length,selected:window.occupancySelected})`);
  if(initial.jobs!==20||initial.headers!==2||initial.functions!==17||initial.electrical!==13||initial.selected!=='D50')throw new Error(JSON.stringify(initial));
  const cards=[];
  for(const row of expected.cards){
    const actual=await evaluate(`document.getElementById('job').value=${JSON.stringify(row.id)};document.getElementById('job').dispatchEvent(new Event('change'));({id:window.occupancySelected,title:document.getElementById('task-name').textContent,keep:document.querySelector('[data-field="keep_ja"]').textContent,end:document.querySelector('[data-field="end_ja"]').textContent,phases:document.querySelectorAll('.phase').length})`);
    if(actual.id!==row.id||actual.title!==row.task.work_ja||actual.keep!==row.keep_ja||actual.end!==row.end_ja||actual.phases!==4)throw new Error(JSON.stringify(actual));
    cards.push(actual.id);
  }
  const cells=[];
  for(const cell of [...new Set(expected.cards.map(r=>r.task.cell))]){
    const actual=await evaluate(`document.getElementById('cell').value=${JSON.stringify(cell)};document.getElementById('cell').dispatchEvent(new Event('change'));Array.from(document.querySelectorAll('#job option')).map(o=>o.value)`);
    const ids=expected.cards.filter(r=>r.task.cell===cell).map(r=>r.id);
    if(JSON.stringify(actual)!==JSON.stringify(ids))throw new Error(JSON.stringify({cell,actual,ids}));
    cells.push({cell,count:actual.length});
  }
  const search=await evaluate(`document.getElementById('only-task').click();document.getElementById('search').value='J01';document.getElementById('search').dispatchEvent(new Event('input'));({ids:Array.from(document.querySelectorAll('[data-target]')).map(r=>r.dataset.target),text:document.getElementById('target-body').textContent})`);
  if(search.ids.length!==1||search.ids[0]!=='J01'||!search.text.includes('P02'))throw new Error(JSON.stringify(search));
  const coverage=await evaluate(`document.getElementById('search').value='';document.getElementById('search').dispatchEvent(new Event('input'));Array.from(document.querySelectorAll('[data-target]')).map(r=>r.dataset.target)`);
  if(coverage.length!==92||new Set(coverage).size!==92)throw new Error('Feature coverage differs');
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  await evaluate(`document.querySelector('[data-job="D50"]').click();window.scrollTo(0,0)`);
  await pause(500);
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_header.png'),Buffer.from(shot.data,'base64'));
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:980,deviceScaleFactor:1,mobile:false});
  await evaluate(`document.querySelector('[data-job="D45"]').click();window.scrollTo(0,0)`);
  await pause(500);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,selected:window.occupancySelected})`);
  if(mobile.documentWidth>mobile.width||mobile.selected!=='D45'||errors.length)throw new Error(JSON.stringify({mobile,errors}));
  const mobileShot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(mobileShot.data,'base64'));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==delivery.page_sha256)throw new Error('Page changed after packaging');
  const result={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,initial,cards,cells,search,feature_ids:coverage,local_links:links,mobile,javascript_errors:errors,scope:'UI and saved-artifact checks; no physical acceptance or cycle measurement'};
  const body=JSON.stringify(result,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_task_occupancy_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('TASK_OCCUPANCY_BROWSER_OK',JSON.stringify({cards:cards.length,cells,features:coverage.length,links:links.length,mobile,errors:errors.length}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
