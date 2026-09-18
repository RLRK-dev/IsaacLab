// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP workflow from check_hvjb_fastening_datum_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, recordPath, output] = process.argv.slice(2);
if (!preview || !recordPath || !output) throw new Error('Usage: checker preview.html record.json output_directory');
const record = JSON.parse(await readFile(recordPath, 'utf8'));
const profile = await mkdtemp(join(tmpdir(), 'hvjb-ses2001-comparison-browser-'));
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
  for (let i = 0; i < 80; i++) {
    try { port = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; }
    catch { await pause(100); }
  }
  if (!port) throw new Error('No isolated Chrome DevTools port');
  const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = pages.find(p => p.type === 'page' && p.url === 'about:blank');
  if (!page) throw new Error('Own blank page unavailable');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  const waiting = new Map(), contexts = new Map(), errors = [];
  let serial = 0;
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.executionContextCreated') {
      const context = message.params.context;
      if (context.auxData?.isDefault) contexts.set(context.auxData.frameId, {
        id: context.id, sessionId: message.sessionId
      });
    }
    if (message.method === 'Target.attachedToTarget') {
      call('Runtime.enable', {}, message.params.sessionId).catch(error => errors.push(error));
    }
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
    if (message.id) {
      const pair = waiting.get(message.id);
      waiting.delete(message.id);
      if (message.error) pair.reject(message.error); else pair.resolve(message.result);
    }
  };
  const call = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++serial;
    waiting.set(id, {resolve, reject});
    socket.send(JSON.stringify({id, method, params, sessionId}));
  });
  await call('Runtime.enable');
  await call('Page.enable');
  await call('Target.setAutoAttach', {autoAttach: true, waitForDebuggerOnStart: false, flatten: true});
  await call('Emulation.setDeviceMetricsOverride', {width: 768, height: 1190, deviceScaleFactor: 1, mobile: false});
  await call('Page.navigate', {url: pathToFileURL(preview).href});
  let context;
  for (let i = 0; i < 80; i++) {
    const tree = await call('Page.getFrameTree');
    context = contexts.get(tree.frameTree.childFrames?.[0]?.frame.id);
    const isolated = [...contexts.values()].filter(item => item.sessionId);
    if (!context && isolated.length === 1) context = isolated[0];
    if (context) break;
    await pause(100);
  }
  if (!context) throw new Error('Sandboxed preview frame not found');
  const evaluate = async expression => {
    const result = await call('Runtime.evaluate', {
      expression, contextId: context.id, returnByValue: true, awaitPromise: true
    }, context.sessionId);
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const root = "document.getElementById('hvjb-ses2001-comparison-v01')";
  for (let i = 0; i < 80; i++) {
    if (await evaluate(`${root}?.dataset.ready === 'true'`)) break;
    if (i === 79) throw new Error('Fragment did not initialize');
    await pause(100);
  }
  await evaluate('document.fonts.ready.then(() => true)');
  const results = [], screenshots = {};
  for (const width of [736, 320]) {
    await call('Emulation.setDeviceMetricsOverride', {width: width + 32, height: 1190, deviceScaleFactor: 1, mobile: false});
    for (const scheme of ['light', 'dark']) {
      await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: scheme}]});
      for (const view of ['front', 'whole']) {
        await evaluate(`(() => {
          const r = ${root}, select = r.querySelector('select');
          select.value='${view}'; select.dispatchEvent(new Event('change',{bubbles:true}));
          return Promise.all([...r.querySelectorAll('img')].map(img => img.decode())).then(() => true);
        })()`);
        await pause(120);
        const observed = await evaluate(`(() => {
          const r=${root}, box=r.getBoundingClientRect(), outside=[];
          for (const node of r.querySelectorAll('select,img,[data-layout],[data-detail],[data-caption]')) {
            const b=node.getBoundingClientRect();
            if (b.left<box.left-1 || b.right>box.right+1 || b.top<box.top-1 || b.bottom>box.bottom+1) outside.push(node.tagName);
          }
          const models={};
          for (const section of r.querySelectorAll('[data-tool]')) {
            const img=section.querySelector('img');
            models[section.dataset.tool]={...JSON.parse(r.dataset.observation)[section.dataset.tool],
              image_width:img.clientWidth,image_height:img.clientHeight,natural_pixels:[img.naturalWidth,img.naturalHeight],
              actual_image:img.src,detail:section.querySelector('[data-detail]').textContent,
              overlay_lines:[...section.querySelectorAll('[data-overlay] line')].map(node=>
                ['x1','y1','x2','y2'].map(key=>Number(node.getAttribute(key)))),
              scale_label:section.querySelector('svg text').textContent,
              scale_label_size:Number.parseFloat(getComputedStyle(section.querySelector('svg text')).fontSize)};
          }
          return {width:box.width,height:box.height,document_width:document.documentElement.scrollWidth,
            selected:r.querySelector('select').value,outside,models};
        })()`);
        if (observed.width !== width || observed.document_width > width || observed.outside.length || observed.selected !== view) {
          throw new Error(JSON.stringify(observed));
        }
        for (const model of ['SES2001','SEV2001']) {
          const got=observed.models[model], expected=record.models[model], frame=expected.render.frames[view];
          const hash=sha(Buffer.from(got.actual_image.split(',')[1],'base64'));
          delete got.actual_image;
          got.loaded_webp_sha256=hash;
          if (got.view !== view || hash !== frame.webp_sha256 || got.png_sha256 !== frame.png_sha256) throw new Error('Saved image identity mismatch');
          if (JSON.stringify(got.natural_pixels) !== JSON.stringify(frame.pixels)) throw new Error('Image dimensions mismatch');
          if (Math.abs(got.image_height/got.image_width-frame.pixels[1]/frame.pixels[0])>0.004) throw new Error('Image distorted');
          if (got.distance_mm !== expected.observation.axis_to_plane_distance_m*1000) throw new Error('Datum label mismatch');
          if (JSON.stringify(got.annotations) !== JSON.stringify(expected.render.annotations)) throw new Error('Datum annotation data mismatch');
          const keys=['axis_line_xz_m','plane_line_xz_m','dimension_line_xz_m'];
          for (let i=0;i<keys.length;i++) {
            const projected=expected.render.annotations[keys[i]].flatMap(([x,z])=>[
              (x-frame.x_m[0])/(frame.x_m[1]-frame.x_m[0])*got.image_width,
              (frame.z_m[1]-z)/(frame.z_m[1]-frame.z_m[0])*got.image_width*frame.pixels[1]/frame.pixels[0]
            ]);
            if (projected.some((value,j)=>Math.abs(value-got.overlay_lines[i][j])>1e-6)) throw new Error('Overlay projection mismatch');
          }
          const scale=got.overlay_lines[3], length=0.1/(frame.x_m[1]-frame.x_m[0])*got.image_width;
          if (Math.abs(scale[2]-scale[0]-length)>1e-6 || scale[1]!==scale[3] || got.scale_label!=='100 mm' || got.scale_label_size<11) throw new Error('Scale label mismatch');
        }
        const one=observed.models.SES2001, two=observed.models.SEV2001;
        if (one.image_width!==two.image_width || one.image_height!==two.image_height) throw new Error('Unequal display scales');
        const name=`${width}_${scheme}_${view}.png`;
        const shot=await call('Page.captureScreenshot',{format:'png'}), bytes=Buffer.from(shot.data,'base64');
        await writeFile(join(output,name),bytes,{flag:'wx'}); screenshots[name]=sha(bytes);
        results.push({requested_width:width,scheme,...observed});
      }
    }
  }
  if (errors.length) throw new Error(JSON.stringify(errors));
  const audit={observed_at:new Date().toISOString(),preview_sha256:sha(await readFile(preview)),
    record_sha256:sha(await readFile(recordPath)),results,screenshots,javascript_errors:errors,
    scope:'Both saved CAD images, common scale, source-coordinate overlays, selection, widths and themes; no physical verdict'};
  await writeFile(join(output,'browser_audit.json'),JSON.stringify(audit,null,2)+'\n',{flag:'wx'});
  console.log('SES2001_COMPARISON_BROWSER_OK',JSON.stringify({states:results.length,errors:errors.length}));
} finally {
  if (socket) socket.close();
  chrome.kill('SIGTERM');
}
