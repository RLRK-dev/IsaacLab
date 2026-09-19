// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP workflow; checks presentation and saved values only.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, recordPath, displayPath, output] = process.argv.slice(2);
if (!preview || !recordPath || !displayPath || !output) throw new Error('Usage: checker preview record display output');
const record = JSON.parse(await readFile(recordPath, 'utf8'));
const display = JSON.parse(await readFile(displayPath, 'utf8')).display;
const axes = display.headers.flatMap(h => h.axes.map(axis => ({...axis, feature_id: h.feature_id})));
const profile = await mkdtemp(join(tmpdir(), 'hvjb-header-tool-envelope-browser-'));
await mkdir(output, {recursive: false});
const chrome = spawn('/usr/bin/google-chrome', [
  '--headless=new', '--no-sandbox', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-dev-shm-usage', 'about:blank'
], {stdio: ['ignore', 'ignore', 'ignore']});
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const near = (a, b) => a === null || b === null ? a === b : Math.abs(a-b) < 1e-9;
let socket;
try {
  let port;
  for (let i = 0; i < 80; i++) {
    try {port = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0];break;}
    catch {await pause(100);}
  }
  if (!port) throw new Error('No isolated Chrome port');
  const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = pages.find(p => p.type === 'page' && p.url === 'about:blank');
  if (!page) throw new Error('Own blank page unavailable');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {socket.onopen = resolve;socket.onerror = reject;});
  const waiting = new Map(), contexts = new Map(), errors = [];
  let serial = 0;
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.executionContextCreated') {
      const context = message.params.context;
      if (context.auxData?.isDefault) contexts.set(context.auxData.frameId, {id: context.id, sessionId: message.sessionId});
    }
    if (message.method === 'Target.attachedToTarget') call('Runtime.enable', {}, message.params.sessionId).catch(error => errors.push(error));
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
    if (message.id) {
      const pair = waiting.get(message.id);waiting.delete(message.id);
      if (message.error) pair.reject(message.error);else pair.resolve(message.result);
    }
  };
  const call = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++serial;waiting.set(id, {resolve, reject});socket.send(JSON.stringify({id, method, params, sessionId}));
  });
  await call('Runtime.enable');await call('Page.enable');
  await call('Target.setAutoAttach', {autoAttach: true, waitForDebuggerOnStart: false, flatten: true});
  await call('Emulation.setDeviceMetricsOverride', {width: 768, height: 1320, deviceScaleFactor: 1, mobile: false});
  await call('Page.navigate', {url: pathToFileURL(preview).href});
  let context;
  for (let i = 0; i < 80; i++) {
    const tree = await call('Page.getFrameTree');context = contexts.get(tree.frameTree.childFrames?.[0]?.frame.id);
    const isolated = [...contexts.values()].filter(item => item.sessionId);
    if (!context && isolated.length === 1) context = isolated[0];
    if (context) break;
    await pause(100);
  }
  if (!context) throw new Error('Sandboxed preview frame unavailable');
  const evaluate = async expression => {
    const result = await call('Runtime.evaluate', {expression, contextId: context.id, returnByValue: true, awaitPromise: true}, context.sessionId);
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const root = "document.getElementById('hvjb-header-tool-envelope-v01')";
  for (let i = 0; i < 80; i++) {
    if (await evaluate(`${root}?.dataset.ready === 'true'`)) break;
    if (i === 79) throw new Error('Figure failed to initialize');
    await pause(100);
  }
  await evaluate('document.fonts.ready.then(()=>true)');
  const numeric = await evaluate(`(() => {
    const r=${root},select=r.querySelector('select'),slider=r.querySelector('[data-offset]'),rows=[];
    for(const option of select.options) {
      select.value=option.value;select.dispatchEvent(new Event('change'));
      for(let offset=0;offset<=100;offset+=2) {
        slider.value=offset;slider.dispatchEvent(new Event('input'));
        rows.push(JSON.parse(r.dataset.observation));
      }
    }
    return rows;
  })()`);
  if (numeric.length !== 714) throw new Error('Missing axis/offset combinations');
  for (const got of numeric) {
    const axis = axes.find(a => a.id === got.id);
    if (got.adopted_offset_mm !== null || got.frame !== axis.frame || got.axes_total !== 14) throw new Error('Pose/selection changed');
    for (const name of ['SES2001', 'SEV2001']) {
      const expected = record.registration_comparisons.find(row => row.feature_id === axis.feature_id && row.nominal_index === axis.nominal_index && row.tool === name && Math.abs(row.hypothetical_cad_leading_position_m*1000-got.offset_mm)<1e-9);
      const actual = got.minimum_differences[name];
      if (!expected || actual.compared_bins !== expected.compared_bins || !near(actual.minimum?.difference_mm??null, expected.minimum_radial_bound_difference_m===null?null:expected.minimum_radial_bound_difference_m*1000)) throw new Error(JSON.stringify({got, expected}));
      if (got.tool_triangles[name] !== record.tools[name].source_triangles) throw new Error('Full source count mismatch');
    }
  }
  const layout = [], screenshots = {};
  for (const width of [736, 320]) {
    await call('Emulation.setDeviceMetricsOverride', {width: width+32, height: 1320, deviceScaleFactor: 1, mobile: false});
    for (const scheme of ['light', 'dark']) {
      await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: scheme}]});
      for (const axis of axes) for (const offset of [0, 20, 40, 60, 80, 100]) {
        await evaluate(`(() => {
          const r=${root},s=r.querySelector('select'),input=r.querySelector('[data-offset]');
          s.value=${JSON.stringify(axis.id)};s.dispatchEvent(new Event('change'));
          input.value=${offset};input.dispatchEvent(new Event('input'));
          return new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))));
        })()`);
        const got = await evaluate(`(() => {
          const r=${root},box=r.getBoundingClientRect(),outside=[];
          for(const node of r.querySelectorAll('select,input,[data-label],[data-detail],[data-offset-label],.series-legend button')) {
            const b=node.getBoundingClientRect();
            if(b.left<box.left-1||b.right>box.right+1||b.top<box.top-1||b.bottom>box.bottom+1)outside.push(node.textContent||node.tagName);
          }
          return {width:box.width,height:box.height,document_width:document.documentElement.scrollWidth,outside,
            label_overlaps:JSON.parse(r.dataset.labelOverlaps),labels_min_px:Math.min(...[...r.querySelectorAll('[data-label]')].map(n=>Number.parseFloat(getComputedStyle(n).fontSize))),
            observation:JSON.parse(r.dataset.observation),profile:JSON.parse(r.querySelector('[data-profile]').dataset.profile),
            select_options:r.querySelector('select').options.length,slider:[r.querySelector('input').min,r.querySelector('input').max,r.querySelector('input').step],
            offset_label:r.querySelector('[data-offset-label]').textContent,detail:r.querySelector('[data-detail]').textContent};
        })()`);
        if (got.width!==width||got.document_width>width||got.outside.length||got.label_overlaps.length||got.labels_min_px<11) throw new Error(JSON.stringify(got));
        if (got.observation.id!==axis.id||got.observation.offset_mm!==offset||got.select_options!==14||!equal(got.slider,['0','100','2'])||got.offset_label!==`${offset} mm`) throw new Error('Control mismatch');
        if (got.profile.bins!==axis.profile.length) throw new Error('Profile bins lost');
        for (let i=0;i<axis.profile.length;i++) {
          const b=got.profile.data[i], hand=axis.profile[i];
          if (!equal(b.depth_mm,hand.depth_mm)||b.radius_mm.H05!==hand.radius_mm) throw new Error('Hand values changed');
          for(const name of ['SES2001','SEV2001']) {
            const source=record.tools[name].profile.find(p=>Math.abs(p.depth_range_m[0]*1000-(hand.depth_mm[0]-offset))<1e-9);
            if (!near(b.radius_mm[name],source?.radius_m===undefined||source.radius_m===null?null:source.radius_m*1000)) throw new Error('Tool band mismatch');
          }
        }
        const {data, ...plotSummary} = got.profile;
        got.profile = plotSummary;
        layout.push({requested_width:width,scheme,...got,all_profile_values_match:true});
        if ((axis.id==='P16_2'&&[0,40].includes(offset)&&((width===736&&scheme==='light')||(width===320&&scheme==='dark')))||
            (axis.id==='P17_14'&&offset===100&&width===320&&scheme==='dark')) {
          const name=`${width}_${scheme}_${axis.id}_${offset}.png`;
          const shot=await call('Page.captureScreenshot',{format:'png'}),bytes=Buffer.from(shot.data,'base64');
          await writeFile(join(output,name),bytes,{flag:'wx'});screenshots[name]=sha(bytes);
        }
      }
    }
  }
  const interaction = await evaluate(`(() => {
    const r=${root},select=r.querySelector('select'),slider=r.querySelector('input');
    select.value='P16_2';select.dispatchEvent(new Event('change'));slider.value=20;slider.dispatchEvent(new Event('input'));
    const svg=r.querySelector('[data-profile]'),overlay=svg.querySelector('[data-chart-hover-overlay]');
    const box=svg.getBoundingClientRect(),p=JSON.parse(svg.dataset.profile),depth=53.37;
    const x=p.x_range[0]+(depth-p.x_domain[0])/(p.x_domain[1]-p.x_domain[0])*(p.x_range[1]-p.x_range[0]);
    overlay.dispatchEvent(new PointerEvent('pointermove',{clientX:box.left+x,clientY:box.top+100,bubbles:true}));
    const hover=JSON.parse(svg.dataset.hover),guideX=Number(svg.querySelector('[data-chart-hover-guide]').getAttribute('x1'));
    overlay.dispatchEvent(new MouseEvent('click',{clientX:box.left+x,clientY:box.top+100,bubbles:true}));
    overlay.dispatchEvent(new PointerEvent('pointerleave',{bubbles:true}));
    const pinned=!r.querySelector('[role="tooltip"]').hidden;
    r.querySelector('[data-series="SES2001"]').click();
    const next=r.querySelector('[data-profile]'),nextBox=next.getBoundingClientRect();
    next.querySelector('[data-chart-hover-overlay]').dispatchEvent(new PointerEvent('pointermove',{clientX:nextBox.left+x,clientY:nextBox.top+100,bubbles:true}));
    const hidden={series_paths:[...next.querySelectorAll('[data-series-path]')].map(n=>n.dataset.seriesPath),
      hover:JSON.parse(next.dataset.hover),tooltip:r.querySelector('[role="tooltip"]').textContent,detail:r.querySelector('[data-detail]').textContent};
    r.querySelector('[data-series="SES2001"]').click();
    return {requested_depth_mm:depth,requested_x:x,hover,guide_x:guideX,pinned,hidden};
  })()`);
  if (Math.abs(interaction.hover.depth_mm-interaction.requested_depth_mm)>1e-9||Math.abs(interaction.guide_x-interaction.requested_x)>1e-9||!interaction.pinned) throw new Error('Hover/pin mismatch');
  if (interaction.hidden.series_paths.includes('SES2001')||interaction.hidden.hover.series.some(s=>s.key==='SES2001')||interaction.hidden.tooltip.includes('SES2001')||interaction.hidden.detail.includes('SES2001')) throw new Error('Legend visibility mismatch');
  if (errors.length) throw new Error(JSON.stringify(errors));
  const audit={observed_at:new Date().toISOString(),preview_sha256:sha(await readFile(preview)),
    record_sha256:sha(await readFile(recordPath)),display_sha256:sha(await readFile(displayPath)),
    numeric_states:numeric,numeric_tool_comparisons:numeric.length*2,layout_states:layout,
    interaction,screenshots,javascript_errors:errors,
    scope:'All saved radial bound values, hypothetical offsets, source identities and UI; no chosen TCP or physical verdict'};
  await writeFile(join(output,'browser_audit.json'),JSON.stringify(audit,null,2)+'\n',{flag:'wx'});
  console.log('HEADER_TOOL_ENVELOPE_BROWSER_OK',JSON.stringify({numeric_states:numeric.length,layout_states:layout.length,errors:errors.length}));
} finally {
  if (socket) socket.close();
  chrome.kill('SIGTERM');
}
