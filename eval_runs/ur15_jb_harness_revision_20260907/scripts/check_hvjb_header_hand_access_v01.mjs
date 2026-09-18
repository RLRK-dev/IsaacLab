// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP setup of check_hvjb_header_fastening_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, recordPath, output] = process.argv.slice(2);
if (!preview || !recordPath || !output) throw new Error('Usage: checker preview.html display.json output_directory');
const record=JSON.parse(await readFile(recordPath,'utf8'));
const axes=record.display.headers.flatMap(header=>header.axes);
const profile=await mkdtemp(join(tmpdir(),'hvjb-header-hand-browser-'));
await mkdir(output,{recursive:false});
const chrome=spawn('/usr/bin/google-chrome',[
  '--headless=new','--no-sandbox','--remote-debugging-port=0',`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--disable-dev-shm-usage','about:blank'
],{stdio:['ignore','ignore','ignore']});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
let socket;
try {
  let port;
  for(let i=0;i<80;i++) {
    try { port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break; }
    catch { await pause(100); }
  }
  if(!port) throw new Error('No isolated browser port');
  const pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page=pages.find(p=>p.type==='page'&&p.url==='about:blank');
  if(!page) throw new Error('Own browser page unavailable');
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
      if(c.auxData?.isDefault)contexts.set(c.auxData.frameId,{id:c.id,sessionId:message.sessionId});
    }
    if(message.method==='Target.attachedToTarget')call('Runtime.enable',{},message.params.sessionId).catch(e=>errors.push(e));
    if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails);
    if(message.id) {
      const pair=waiting.get(message.id);waiting.delete(message.id);
      if(message.error)pair.reject(message.error);else pair.resolve(message.result);
    }
  };
  await call('Runtime.enable');await call('Page.enable');
  await call('Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:false,flatten:true});
  await call('Emulation.setDeviceMetricsOverride',{width:768,height:1190,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:pathToFileURL(preview).href});
  let context;
  for(let i=0;i<80;i++) {
    const tree=await call('Page.getFrameTree');context=contexts.get(tree.frameTree.childFrames?.[0]?.frame.id);
    const isolated=[...contexts.values()].filter(c=>c.sessionId);
    if(!context&&isolated.length===1)context=isolated[0];
    if(context)break;await pause(100);
  }
  if(!context)throw new Error('Sandboxed preview frame unavailable');
  const evaluate=async expression=>{
    const result=await call('Runtime.evaluate',{expression,contextId:context.id,returnByValue:true,awaitPromise:true},context.sessionId);
    if(result.exceptionDetails)throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const root="document.getElementById('hvjb-header-hand-access-v01')";
  for(let i=0;i<100;i++) {
    if(await evaluate(`${root}?.dataset.ready==='true'`))break;
    if(i===99)throw new Error('Fragment not initialized: '+JSON.stringify(errors));
    await pause(100);
  }
  await evaluate('document.fonts.ready.then(()=>true)');
  const results=[],screenshots={};
  for(const width of [736,320]) {
    await call('Emulation.setDeviceMetricsOverride',{width:width+32,height:1190,deviceScaleFactor:1,mobile:false});
    for(const scheme of ['light','dark']) {
      await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:scheme}]});
      for(const axis of axes) {
        await evaluate(`(()=>{const s=${root}.querySelector('select');s.value=${JSON.stringify(axis.id)};s.dispatchEvent(new Event('change'));})()`);
        await pause(80);
        const observed=await evaluate(`(()=>{
          const r=${root},box=r.getBoundingClientRect(),outside=[];
          for(const n of r.querySelectorAll('svg,select,[data-selected],[data-label],.series-legend button')) {
            const b=n.getBoundingClientRect();
            if(b.left<box.left-1||b.right>box.right+1||b.top<box.top-1||b.bottom>box.bottom+1)outside.push(n.textContent);
          }
          const plot=r.querySelector('[data-profile]');
          return {...JSON.parse(r.dataset.observation),width:box.width,outside,
            label_overlaps:JSON.parse(r.dataset.labelOverlaps),document_width:document.documentElement.scrollWidth,
            labels_min_px:Math.min(...[...r.querySelectorAll('[data-label]')].map(n=>parseFloat(getComputedStyle(n).fontSize))),
            selected:r.querySelector('select').value,option_count:r.querySelector('select').options.length,
            marker_ids:[...r.querySelectorAll('.axis-mark')].map(n=>n.dataset.id),rings:r.querySelectorAll('.active-ring').length,
            projection:JSON.parse(r.querySelector('[data-map]').dataset.projection),
            profile:JSON.parse(plot.dataset.profile),series:[...plot.querySelectorAll('[data-series-path]')].map(n=>n.dataset.seriesPath),
            plot_viewBox:plot.getAttribute('viewBox'),x_ticks:[...plot.querySelectorAll('text[data-label]')].filter(n=>n.getAttribute('y')==='276').length};
        })()`);
        const header=record.display.headers.find(h=>h.axes.some(a=>a.id===axis.id));
        if(observed.id!==axis.id||observed.selected!==axis.id||observed.axes_total!==14||observed.option_count!==14||observed.rings!==1)throw new Error('Axis selection mismatch');
        if(observed.width!==width||observed.document_width>width||observed.outside.length||observed.label_overlaps.length||observed.labels_min_px<11)throw new Error(JSON.stringify(observed));
        if(JSON.stringify(observed.marker_ids)!==JSON.stringify(header.axes.map(a=>a.id)))throw new Error('Header axes missing');
        if(JSON.stringify(observed.nearest)!==JSON.stringify(axis.nearest)||JSON.stringify(observed.profile.data)!==JSON.stringify(axis.profile)||observed.frame!==axis.frame)throw new Error('Display differs from saved observation');
        if(observed.plot_viewBox!==`0 0 ${width} 310`||observed.series.length!==3)throw new Error('Plot size or series mismatch');
        if(width===320&&observed.x_ticks>4)throw new Error('Too many narrow-screen ticks');
        const hover=await evaluate(`(()=>{
          const r=${root},s=r.querySelector('[data-profile]'),hit=s.querySelector('[data-chart-hover-overlay]'),b=hit.getBoundingClientRect();
          const px=b.left+b.width*.413;
          hit.dispatchEvent(new PointerEvent('pointermove',{clientX:px,clientY:b.top+b.height*.5,bubbles:true,pointerType:'mouse'}));
          return {...JSON.parse(s.dataset.hover),expected_x:px-s.getBoundingClientRect().left,
            markers:[...s.querySelectorAll('[data-chart-hover-marker]')].map(n=>({key:n.dataset.chartHoverMarker,cx:Number(n.getAttribute('cx'))})),
            tooltip_hidden:r.querySelector('[role="tooltip"]').hidden};
        })()`);
        const band=axis.profile.find(b=>hover.depth_mm>=b.depth_mm[0]&&hover.depth_mm<b.depth_mm[1]);
        if(!band||hover.tooltip_hidden||Math.abs(hover.guide_x-hover.expected_x)>1e-6)throw new Error('Hover guide displaced: '+JSON.stringify({axis:axis.id,width,scheme,hover}));
        for(const row of hover.series)if(row.radius_mm!==band.radius_mm[row.key])throw new Error('Hover interval value mismatch');
        for(const mark of hover.markers)if(Math.abs(mark.cx-hover.guide_x)>1e-6)throw new Error('Hover marker snapped away');
        await evaluate(`${root}.querySelector('[data-chart-hover-overlay]').dispatchEvent(new PointerEvent('pointerleave'))`);
        delete observed.profile.data;results.push({requested_width:width,scheme,...observed,hover});
        if(axis===axes[1]||axis===axes.at(-1)) {
          const name=`${width}_${scheme}_${axis.id}.png`,capture=await call('Page.captureScreenshot',{format:'png'});
          const bytes=Buffer.from(capture.data,'base64');await writeFile(join(output,name),bytes,{flag:'wx'});screenshots[name]=sha(bytes);
        }
      }
    }
  }
  const legend=await evaluate(`(()=>{
    const r=${root},b=r.querySelector('[data-series="hardware"]');b.click();
    const hidden=[...r.querySelectorAll('[data-series-path]')].map(n=>n.dataset.seriesPath),pressed=b.getAttribute('aria-pressed');
    b.click();return {hidden,pressed,restored:r.querySelectorAll('[data-series-path]').length};
  })()`);
  if(legend.pressed!=='false'||legend.hidden.includes('hardware')||legend.restored!==3)throw new Error('Legend toggle failed');
  if(errors.length)throw new Error(JSON.stringify(errors));
  const audit={observed_at:new Date().toISOString(),preview_sha256:sha(await readFile(preview)),record_sha256:sha(await readFile(recordPath)),
    results,screenshots,legend,javascript_errors:errors,scope:'Axis selection, complete saved interval data, hover, labels and themes; no physical verdict'};
  await writeFile(join(output,'browser_audit.json'),JSON.stringify(audit,null,2)+'\n',{flag:'wx'});
  console.log('HEADER_HAND_BROWSER_OK',JSON.stringify({states:results.length,errors:errors.length,legend}));
} finally {
  if(socket)socket.close();chrome.kill('SIGTERM');
}
