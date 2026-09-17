// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP workflow from check_hvjb_pge_finger_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, reportPath, output] = process.argv.slice(2);
if (!preview || !reportPath || !output) throw new Error('Usage: checker preview.html observations.json output_directory');
const report = JSON.parse(await readFile(reportPath, 'utf8'));
const profile = await mkdtemp(join(tmpdir(), 'hvjb-pge-axis-browser-'));
await mkdir(output, {recursive: true});
const chrome = spawn('/usr/bin/google-chrome', [
  '--headless=new', '--no-sandbox', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-dev-shm-usage',
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader', 'about:blank'
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
  await call('Emulation.setDeviceMetricsOverride', {width: 768, height: 1020, deviceScaleFactor: 1, mobile: false});
  await call('Page.navigate', {url: pathToFileURL(preview).href});
  let context;
  for (let i = 0; i < 80; i++) {
    const tree = await call('Page.getFrameTree');
    const frame = tree.frameTree.childFrames?.[0]?.frame.id;
    context = contexts.get(frame);
    const isolatedFrames = [...contexts.values()].filter(item => item.sessionId);
    if (!context && isolatedFrames.length === 1) context = isolatedFrames[0];
    if (context) break;
    await pause(100);
  }
  if (!context) throw new Error('Sandboxed preview frame not found: ' + JSON.stringify({
    tree: await call('Page.getFrameTree'), contexts: [...contexts]
  }));
  const evaluate = async expression => {
    const result = await call('Runtime.evaluate', {
      expression, contextId: context.id, returnByValue: true, awaitPromise: true
    }, context.sessionId);
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const root = "document.getElementById('hvjb-pge-tool-axis-v01')";
  for (let i = 0; i < 80; i++) {
    if (await evaluate(`${root}?.dataset.ready === 'true'`)) break;
    if (i === 79) throw new Error('Fragment did not initialize');
    await pause(100);
  }
  await evaluate('document.fonts.ready.then(() => true)');
  const results = [], images = {};
  for (const width of [736, 320]) {
    await call('Emulation.setDeviceMetricsOverride', {width: width + 32, height: 1190, deviceScaleFactor: 1, mobile: false});
    for (const scheme of ['light', 'dark']) {
      await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: scheme}]});
      for (const state of ['contour', 'open']) for (const band of ['tip', 'upper']) {
        await evaluate(`(() => {
          const r = ${root};
          for (const [field, value] of [['state', '${state}'], ['band', '${band}']]) {
            const s = r.querySelector('[data-field="'+field+'"]');
            s.value = value; s.dispatchEvent(new Event('change', {bubbles:true}));
          }
        })()`);
        await pause(150);
        const observed = await evaluate(`(() => {
          const r = ${root};
          const outside = [], overlappingLabels = [];
          for (const svg of r.querySelectorAll('svg')) {
            const frame = svg.getBoundingClientRect();
            const labels = [...svg.querySelectorAll('text')].map(n => ({text: n.textContent, box: n.getBoundingClientRect()}));
            labels.forEach(({text, box}) => { if (box.left < frame.left - 1 || box.right > frame.right + 1 || box.top < frame.top - 1 || box.bottom > frame.bottom + 1) outside.push(text); });
            for (let i=0;i<labels.length;i++) for (let j=i+1;j<labels.length;j++) {
              const a=labels[i].box,b=labels[j].box;
              if (a.left < b.right+4 && a.right+4 > b.left && a.top < b.bottom+4 && a.bottom+4 > b.top) overlappingLabels.push([labels[i].text,labels[j].text]);
            }
          }
          const controls = [...r.querySelectorAll('select')].map(n=>n.getBoundingClientRect());
          const controlsOverlap = controls[0].left < controls[1].right && controls[0].right > controls[1].left && controls[0].top < controls[1].bottom && controls[0].bottom > controls[1].top;
          return {...JSON.parse(r.dataset.observation), documentWidth: document.documentElement.scrollWidth,
            outside, overlappingLabels, controlsOverlap, selected: [...r.querySelectorAll('select')].map(n=>n.value)};
        })()`);
        if (observed.state !== state || observed.band !== band || observed.selected.join() !== [state,band].join()) throw new Error(JSON.stringify(observed));
        if (observed.documentWidth > width || observed.width !== width || observed.outside.length || observed.overlappingLabels.length || observed.controlsOverlap) throw new Error(JSON.stringify(observed));
        const expected = report.measurements.states[state].bands[band];
        if (JSON.stringify(observed.measurement) !== JSON.stringify(expected)) throw new Error('Displayed witness differs from the measurement report');
        const travel = state === 'open' ? 0.007 : 0;
        if (observed.opening_per_jaw_m !== travel || observed.pads !== 4 || observed.objects !== 21 || observed.measured_objects !== 17) throw new Error('Displayed saved layout differs from the sample');
        if (!observed.finite_vertices || observed.maximum_normalized_xy > 1 || observed.gl_error) throw new Error('Clipped or invalid geometry: ' + JSON.stringify(observed));
        results.push({requested_width: width, scheme, ...observed});
        const name = `${width}_${scheme}_${state}_${band}.png`;
        const screenshot = await call('Page.captureScreenshot', {format: 'png'});
        const bytes = Buffer.from(screenshot.data, 'base64');
        await writeFile(join(output, name), bytes, {flag: 'wx'});
        images[name] = sha(bytes);
      }
    }
  }
  if (errors.length) throw new Error(JSON.stringify(errors));
  const audit = {observed_at: new Date().toISOString(), preview_sha256: sha(await readFile(preview)),
    observations_sha256: sha(await readFile(reportPath)), results, images, javascript_errors: errors,
    scope: 'Saved-state display, numerical projection and UI only; no contact, force or physical verdict'};
  await writeFile(join(output, 'browser_audit.json'), JSON.stringify(audit, null, 2) + '\n', {flag: 'wx'});
  console.log('PGE_AXIS_BROWSER_OK', JSON.stringify({states: results.length, errors: errors.length}));
} finally {
  if (socket) socket.close();
  chrome.kill('SIGTERM');
}
