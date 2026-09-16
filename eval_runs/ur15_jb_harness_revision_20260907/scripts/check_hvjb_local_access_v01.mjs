// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Own-profile Chrome/CDP workflow reused from check_hvjb_final_connection_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory=process.argv[2]||'/home/rlrk/Downloads/THREAD_HVJB_Cセル手先比較_v01_20260917';
const data=JSON.parse(await readFile(join(directory,'measurements.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-local-access-browser-'));
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const mm=value=>(value*1000).toFixed(2);
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
  const waiting=new Map(),errors=[];
  let serial=0;
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
    await writeFile(join(directory,name),bytes,{flag:'wx'});exports[name]=sha(bytes);
  };
  await call('Runtime.enable');await call('Page.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  let ready=false;
  for(let i=0;i<100;i++){ready=await evaluate('window.localAccessReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  await evaluate('document.fonts.ready.then(()=>true)');
  const cases=[];
  for(const [id,state] of Object.entries(data.hand)){
    await evaluate(`document.querySelector('[data-state="${id}"]').click()`);
    const shown=await evaluate(`({state:window.localAccessState.hand,title:document.getElementById('state-title').textContent,width:document.getElementById('hand-width').textContent,distances:[...document.querySelectorAll('#radial tr')].map(r=>r.cells[1].textContent),polygons:document.querySelectorAll('#hand-side polygon').length})`);
    if(shown.state!==id||shown.title!==state.label_ja||shown.width!==`幅 ${mm(state.bounds.size_m[0])} mm`||shown.polygons!==state.surfaces.length)throw new Error(JSON.stringify(shown));
    if(JSON.stringify(shown.distances)!==JSON.stringify(state.tool_axis_to_hand.map(r=>mm(r.radius_to_surface_m)+' mm')))throw new Error('Hand measurements differ from source JSON');
    const bounds=await evaluate(`Array.from(document.querySelectorAll('#hand-side polygon')).map(p=>{const b=p.getBBox();return [b.x,b.y,b.x+b.width,b.y+b.height]})`);
    if(bounds.some(b=>b[0]<0||b[1]<0||b[2]>620||b[3]>465))throw new Error('Hand drawing clipped: '+id+' '+JSON.stringify(bounds));
    shown.projected_polygon_bounds=bounds;
    cases.push(shown);
    await evaluate(`document.getElementById('state-buttons').scrollIntoView({block:'start'})`);
    await screenshot(`hand_${id}.png`);
  }
  const joints=[];
  for(const row of data.product_row){
    await evaluate(`document.querySelector('[data-joint="${row.id}"]').click()`);
    const shown=await evaluate(`({id:window.localAccessState.joint,distances:[...document.querySelectorAll('#product-radial tr')].map(r=>r.cells[1].textContent),markers:[...document.querySelectorAll('#markers circle')].map(c=>[Number(c.getAttribute('cx')),Number(c.getAttribute('cy'))])})`);
    if(shown.id!==row.id||JSON.stringify(shown.distances)!==JSON.stringify(row.bands.map(r=>mm(r.radius_to_surface_m)+' mm'))||JSON.stringify(shown.markers)!==JSON.stringify(data.product_row.map(r=>r.center_px)))throw new Error(JSON.stringify(shown));
    joints.push(shown);
  }
  const imageSizes=await evaluate(`Promise.all(['product.jpg','assembly_242s.png'].map(src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve([src,im.naturalWidth,im.naturalHeight]);im.onerror=reject;im.src=src;})))`);
  if(JSON.stringify(imageSizes)!==JSON.stringify([['product.jpg',1620,1080],['assembly_242s.png',1920,1080]]))throw new Error('Source images did not load');
  await evaluate(`document.querySelector('[data-state="near"]').click();document.querySelector('[data-joint="J09"]').click();window.scrollTo(0,0)`);
  await screenshot('browser_desktop.png');
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:1100,deviceScaleFactor:1,mobile:false});
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,states:document.querySelectorAll('[data-state]').length})`);
  if(mobile.documentWidth>mobile.width||mobile.states!==4)throw new Error(JSON.stringify(mobile));
  await screenshot('browser_mobile.png');
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')).filter(h=>!/^https?:/.test(h))`);
  const svg=await evaluate('window.exportOverview()');
  await writeFile(join(directory,'overview.svg'),svg,{flag:'wx'});exports['overview.svg']=sha(svg);
  await call('Emulation.setDeviceMetricsOverride',{width:1320,height:470,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:pathToFileURL(join(directory,'overview.svg')).href});
  let svgReady=false;
  for(let i=0;i<100;i++){svgReady=await evaluate(`document.documentElement.tagName==='svg'`);if(svgReady)break;await pause(100);}
  if(!svgReady)throw new Error('Standalone SVG did not load');
  await evaluate('document.fonts.ready.then(()=>true)');
  await screenshot('overview.png');
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  const audit=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(sha(await readFile(join(directory,'review.html')))!==audit.page_sha256)throw new Error('Packaged page changed');
  if(errors.length)throw new Error(JSON.stringify(errors));
  const report={observed_at:new Date().toISOString(),directory,cases,joints,imageSizes,mobile,links,exports_sha256:exports,javascript_errors:errors,scope:'UI/source correspondence only; no physical verdict'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_local_access_browser_v01.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('LOCAL_ACCESS_BROWSER_OK',JSON.stringify({states:cases.length,joints:joints.length,errors:errors.length,mobile}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
