// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP workflow to inspect diagram/UI correspondence.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

const root=dirname(dirname(fileURLToPath(import.meta.url)));
const directory=process.argv[2]||'/home/rlrk/Downloads/THREAD_HVJB_ロボット分担図_v02_20260916';
const expected=JSON.parse(await readFile(join(directory,'review_data.json'),'utf8'));
const profile=await mkdtemp(join(tmpdir(),'hvjb-diagram-browser-'));
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const focus=['S4','S5_AB'];
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
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1320,deviceScaleFactor:1,mobile:false});
  const navigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});
  if(navigation.errorText)throw new Error(JSON.stringify(navigation));
  let ready;
  for(let i=0;i<100;i++){ready=await evaluate('window.diagramReady||false');if(ready)break;await pause(100);}
  if(!ready)throw new Error('Page did not initialize');
  await evaluate('document.fonts.ready.then(()=>true)');
  const cases=[];
  for(const scene of expected.plans[0].scenarios){
    await evaluate(`for(const c of ['A','B','C']){const box=document.getElementById('assist-'+c);box.checked=${JSON.stringify(scene.active_assists)}.includes('X-'+c);box.dispatchEvent(new Event('change'));}`);
    for(const id of focus){
      const plan=expected.plans.find(p=>p.id===id),s=plan.scenarios.find(s=>s.id===scene.id);
      const actual=await evaluate(`(()=>{const svg=document.getElementById('svg-${id}');return {scene:window.diagramScene,units:[...svg.querySelectorAll('.arm-icon')].map(n=>n.dataset.unit),cells:[...svg.querySelectorAll('.station')].map(n=>n.dataset.cell),routes:[...svg.querySelectorAll('.assist-route')].map(n=>({role:n.dataset.role,unit:n.dataset.unit,active:n.dataset.active==='true'})),conflicts:[...svg.querySelectorAll('.helper.conflict')].map(n=>n.dataset.unit),result:document.getElementById('result-${id}').textContent};})()`);
      const units=[...new Set(Object.values(plan.role_to_unit))].sort();
      if(actual.scene!==scene.id||JSON.stringify(actual.units.sort())!==JSON.stringify(units)||actual.cells.join('')!=='ABC'||actual.routes.length!==3)throw new Error(JSON.stringify(actual));
      if(actual.units.length!==plan.arm_slots||JSON.stringify(actual.conflicts.sort())!==JSON.stringify(Object.keys(s.duplicate_assignments).sort()))throw new Error(JSON.stringify(actual));
      for(const route of actual.routes){if(route.unit!==plan.role_to_unit[route.role]||route.active!==s.active_assists.includes(route.role))throw new Error(JSON.stringify(route));}
      cases.push({plan:id,...actual});
    }
  }
  await evaluate(`document.getElementById('example-ab').click()`);
  if(await evaluate('window.diagramScene')!=='AB')throw new Error('AB preset failed');
  await evaluate(`document.getElementById('example-ac').click();window.scrollTo(0,0)`);
  if(await evaluate('window.diagramScene')!=='AC')throw new Error('AC preset failed');
  let shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_desktop.png'),Buffer.from(shot.data,'base64'));
  const standalone=await evaluate(`(()=>{
    const clone=(node,x,y,w,h)=>{const n=node.cloneNode(true);n.setAttribute('x',x);n.setAttribute('y',y);n.setAttribute('width',w);n.setAttribute('height',h);return new XMLSerializer().serializeToString(n);};
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1380" height="900" viewBox="0 0 1380 900" style="font-family:Noto Sans CJK JP,Yu Gothic,sans-serif">'+
    '<rect width="1380" height="900" fill="#edf2f5"/>'+text(690,42,'主担当3腕 ＋ 共用する補助腕',29,COLORS.ink,700)+
    clone(document.querySelector('.process svg'),25,60,1330,162)+
    text(690,252,'例：AとCが同時に補助を必要とする場面',20,COLORS.ink,700)+
    '<rect x="18" y="275" width="661" height="544" rx="12" fill="white"/><rect x="701" y="275" width="661" height="544" rx="12" fill="white"/>'+
    text(348,305,'4腕案：補助1腕をA・B・Cで共用',23,COLORS.assist,700)+text(1031,305,'5腕案：A・Bの共用補助 ＋ C専用補助',23,COLORS.dedicated,700)+
    clone(document.getElementById('svg-S4'),25,314,646,494)+clone(document.getElementById('svg-S5_AB'),708,314,646,494)+
    text(348,850,'AとCで同じ補助を取り合う → 順番を調整',20,COLORS.red,700)+text(1031,850,'AとCの補助を別々の腕に割り当てる',20,COLORS.dedicated,700)+
    text(690,883,'担当関係の概念図。配置・到達・動作は未確定。腕数はこの比較範囲のみ。',15,COLORS.muted)+ '</svg>';
  })()`);
  await writeFile(join(directory,'overview.svg'),standalone,{flag:'wx'});
  await call('Emulation.setDeviceMetricsOverride',{width:480,height:1100,deviceScaleFactor:1,mobile:false});
  await evaluate('window.scrollTo(0,0)');await pause(100);
  const mobile=await evaluate(`({width:innerWidth,documentWidth:document.documentElement.scrollWidth,scene:window.diagramScene,arms:document.querySelectorAll('.arm-icon').length})`);
  if(mobile.documentWidth>mobile.width||mobile.arms!==9||errors.length)throw new Error(JSON.stringify({mobile,errors}));
  shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(join(directory,'browser_mobile.png'),Buffer.from(shot.data,'base64'));
  const links=await evaluate(`Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))`);
  const svgNavigation=await call('Page.navigate',{url:pathToFileURL(join(directory,'overview.svg')).href});
  if(svgNavigation.errorText)throw new Error(JSON.stringify(svgNavigation));
  for(let i=0;i<100;i++){if(await evaluate(`document.documentElement.tagName==='svg'&&document.querySelectorAll('.arm-icon').length===9`))break;await pause(100);}
  if(!await evaluate(`document.documentElement.tagName==='svg'&&document.querySelectorAll('.arm-icon').length===9`))throw new Error('Standalone SVG did not load');
  await evaluate('document.fonts.ready.then(()=>true)');
  await call('Emulation.setDeviceMetricsOverride',{width:1380,height:900,deviceScaleFactor:1,mobile:false});
  await pause(100);
  shot=await call('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:1380,height:900,scale:1}});
  await writeFile(join(directory,'overview.png'),Buffer.from(shot.data,'base64'),{flag:'wx'});
  for(const link of links)await readFile(join(directory,decodeURIComponent(link)));
  const pageSha=createHash('sha256').update(await readFile(join(directory,'review.html'))).digest('hex');
  const delivery=JSON.parse(await readFile(join(directory,'audit.json'),'utf8'));
  if(pageSha!==delivery.page_sha256)throw new Error('Page changed after packaging');
  const exports={};
  for(const name of ['overview.svg','overview.png','browser_desktop.png','browser_mobile.png'])exports[name]=createHash('sha256').update(await readFile(join(directory,name))).digest('hex');
  const report={observed_at:new Date().toISOString(),directory,page_sha256:pageSha,cases,mobile,local_links:links,exports_sha256:exports,javascript_errors:errors,scope:'Diagram-to-source role correspondence only; no physical/scheduling verdict'};
  const body=JSON.stringify(report,null,2)+'\n';
  await writeFile(join(root,'audit/hvjb_robot_diagram_browser_v02.json'),body,{flag:'wx'});
  await writeFile(join(directory,'browser_audit.json'),body,{flag:'wx'});
  console.log('ROBOT_DIAGRAM_BROWSER_OK',JSON.stringify({cases:cases.length,links:links.length,mobile,errors:errors.length,exports:Object.keys(exports)}));
}finally{if(socket)socket.close();chrome.kill('SIGTERM');}
