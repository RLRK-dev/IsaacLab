// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuse the isolated Chrome/CDP setup of check_hvjb_fastening_mount_faces_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, recordPath, output] = process.argv.slice(2);
if (!preview || !recordPath || !output) throw new Error('Usage: checker preview.html display.json output_directory');
const record = JSON.parse(await readFile(recordPath, 'utf8'));
const screws = record.display.headers.flatMap(header => header.screws);
const profile = await mkdtemp(join(tmpdir(), 'hvjb-header-fastening-browser-'));
await mkdir(output, {recursive: false});
const chrome = spawn('/usr/bin/google-chrome', [
  '--headless=new', '--no-sandbox', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-dev-shm-usage', 'about:blank'
], {stdio: ['ignore', 'ignore', 'ignore']});
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
let socket;
try {
  let port;
  for (let i=0; i<80; i++) {
    try { port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]; break; }
    catch { await pause(100); }
  }
  if (!port) throw new Error('No isolated browser port');
  const pages=await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page=pages.find(p=>p.type==='page' && p.url==='about:blank');
  if (!page) throw new Error('Own browser page unavailable');
  socket=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  const waiting=new Map(),contexts=new Map(),errors=[];
  let serial=0;
  const call=(method,params={},sessionId)=>new Promise((resolve,reject)=>{
    const id=++serial;waiting.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params,sessionId}));
  });
  socket.onmessage=event=>{
    const message=JSON.parse(event.data);
    if(message.method==='Runtime.executionContextCreated') {
      const c=message.params.context;
      if(c.auxData?.isDefault) contexts.set(c.auxData.frameId,{id:c.id,sessionId:message.sessionId});
    }
    if(message.method==='Target.attachedToTarget') call('Runtime.enable',{},message.params.sessionId).catch(e=>errors.push(e));
    if(message.method==='Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
    if(message.id) {
      const pair=waiting.get(message.id);waiting.delete(message.id);
      if(message.error) pair.reject(message.error);else pair.resolve(message.result);
    }
  };
  await call('Runtime.enable');await call('Page.enable');
  await call('Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:false,flatten:true});
  await call('Emulation.setDeviceMetricsOverride',{width:768,height:1190,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:pathToFileURL(preview).href});
  let context;
  for(let i=0;i<80;i++) {
    const tree=await call('Page.getFrameTree');
    context=contexts.get(tree.frameTree.childFrames?.[0]?.frame.id);
    const isolated=[...contexts.values()].filter(c=>c.sessionId);
    if(!context && isolated.length===1) context=isolated[0];
    if(context) break;
    await pause(100);
  }
  if(!context) throw new Error('Sandboxed preview frame unavailable');
  const evaluate=async expression=>{
    const result=await call('Runtime.evaluate',{
      expression,contextId:context.id,returnByValue:true,awaitPromise:true
    },context.sessionId);
    if(result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const root="document.getElementById('hvjb-header-fastening-v01')";
  for(let i=0;i<80;i++) {
    if(await evaluate(`${root}?.dataset.ready==='true'`)) break;
    if(i===79) throw new Error('Fragment not initialized');
    await pause(100);
  }
  await evaluate('document.fonts.ready.then(()=>true)');
  const results=[],screenshots={};
  for(const width of [736,320]) {
    await call('Emulation.setDeviceMetricsOverride',{width:width+32,height:1190,deviceScaleFactor:1,mobile:false});
    for(const scheme of ['light','dark']) {
      await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:scheme}]});
      for(const screw of screws) {
        await evaluate(`(()=>{const s=${root}.querySelector('select');s.value=${JSON.stringify(screw.id)};s.dispatchEvent(new Event('change'));})()`);
        await pause(80);
        const observed=await evaluate(`(()=>{
          const r=${root},box=r.getBoundingClientRect(),outside=[],overlaps=[];
          const labels=[...r.querySelectorAll('[data-label]')];
          for(const n of r.querySelectorAll('svg, select, [data-selected], [data-label]')) {
            const b=n.getBoundingClientRect();
            if(b.left<box.left-1 || b.right>box.right+1 || b.top<box.top-1 || b.bottom>box.bottom+1) outside.push(n.textContent);
          }
          for(let i=0;i<labels.length;i++) {
            const a=labels[i].getBoundingClientRect();
            for(let j=i+1;j<labels.length;j++) {
              const b=labels[j].getBoundingClientRect();
              if(a.left<b.right && a.right>b.left && a.top<b.bottom && a.bottom>b.top) overlaps.push([labels[i].textContent,labels[j].textContent]);
            }
          }
          return {...JSON.parse(r.dataset.observation),width:box.width,outside,overlaps,
            document_width:document.documentElement.scrollWidth,labels_min_px:Math.min(...labels.map(n=>parseFloat(getComputedStyle(n).fontSize))),
            selected:r.querySelector('select').value,marker_ids:[...r.querySelectorAll('.axis-mark')].map(n=>n.dataset.id),
            active_rings:r.querySelectorAll('.active-ring').length,
            projections:[...r.querySelectorAll('[data-map]')].map(svg=>({feature_id:svg.dataset.map,
              ...JSON.parse(svg.dataset.projection),viewBox:svg.getAttribute('viewBox'),
              points:[...svg.querySelectorAll('.axis-mark')].map(n=>({id:n.dataset.id,d:n.getAttribute('d')}))})),
            section:JSON.parse(r.querySelector('[data-section]').dataset.section)};
        })()`);
        if(observed.id!==screw.id || observed.selected!==screw.id || observed.axis_count!==14 || observed.active_rings!==1) throw new Error('Selection differs');
        if(observed.width!==width || observed.document_width>width || observed.outside.length || observed.overlaps.length || observed.labels_min_px<11) throw new Error(JSON.stringify(observed));
        if(JSON.stringify(observed.marker_ids)!==JSON.stringify(screws.map(s=>s.id))) throw new Error('Missing axes');
        if(observed.protrusion_mm!==screw.protrusion_mm || JSON.stringify(observed.section.axial_mm)!==JSON.stringify(screw.axial_mm)) throw new Error('Axial data differs');
        for(const figure of observed.projections) {
          if(figure.viewBox!==`0 0 ${width} ${figure.height}`) throw new Error('Rescaled viewBox');
          for(const point of figure.points) {
            const source=screws.find(s=>s.id===point.id),[x,z]=source.local_xz_mm;
            const px=figure.left+(x-figure.xBounds[0])*figure.scale;
            const py=figure.top+(figure.zBounds[1]-z)*figure.scale;
            if(point.d!==`M${px-4} ${py}H${px+4}M${px} ${py-4}V${py+4}`) throw new Error('Position differs from saved data');
          }
        }
        results.push({requested_width:width,scheme,...observed});
        if(screw===screws[0] || screw===screws.at(-1)) {
          const name=`${width}_${scheme}_${screw.id}.png`;
          const capture=await call('Page.captureScreenshot',{format:'png'}),bytes=Buffer.from(capture.data,'base64');
          await writeFile(join(output,name),bytes,{flag:'wx'});screenshots[name]=sha(bytes);
        }
      }
    }
  }
  if(errors.length) throw new Error(JSON.stringify(errors));
  const audit={observed_at:new Date().toISOString(),preview_sha256:sha(await readFile(preview)),
    record_sha256:sha(await readFile(recordPath)),results,screenshots,javascript_errors:errors,
    scope:'Selection, complete axis display, saved numeric correspondence, label bounds and themes; no physical verdict'};
  await writeFile(join(output,'browser_audit.json'),JSON.stringify(audit,null,2)+'\n',{flag:'wx'});
  console.log('HEADER_FASTENING_BROWSER_OK',JSON.stringify({states:results.length,errors:errors.length}));
} finally {
  if(socket) socket.close();
  chrome.kill('SIGTERM');
}
