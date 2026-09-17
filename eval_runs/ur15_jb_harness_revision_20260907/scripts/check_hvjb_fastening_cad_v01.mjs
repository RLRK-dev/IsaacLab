// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP workflow from check_hvjb_pge_tool_axis_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, recordPath, output] = process.argv.slice(2);
if (!preview || !recordPath || !output) throw new Error('Usage: checker preview.html record.json output_directory');
const record = JSON.parse(await readFile(recordPath, 'utf8'));
const profile = await mkdtemp(join(tmpdir(), 'hvjb-fastening-cad-browser-'));
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
  const root = "document.getElementById('hvjb-fastening-cad-v01')";
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
      for (const model of ['SES1601', 'SEM2001', 'SEV2001']) for (const view of ['whole', 'front']) {
        await evaluate(`(() => {
          const r = ${root};
          for (const [field, value] of [['model', '${model}'], ['view', '${view}']]) {
            const select = r.querySelector('[data-field="'+field+'"]');
            select.value = value; select.dispatchEvent(new Event('change', {bubbles:true}));
          }
          return r.querySelector('img').decode().then(() => true);
        })()`);
        await pause(120);
        const observed = await evaluate(`(() => {
          const r = ${root}, img = r.querySelector('img'), box = r.getBoundingClientRect();
          const outside = [];
          for (const node of r.querySelectorAll('select, img, [data-layout], [data-detail]')) {
            const b = node.getBoundingClientRect();
            if (b.left < box.left-1 || b.right > box.right+1 || b.top < box.top-1 || b.bottom > box.bottom+1) outside.push(node.tagName);
          }
          const c = [...r.querySelectorAll('select')].map(n => n.getBoundingClientRect());
          const overlap = c[0].left < c[1].right && c[0].right > c[1].left && c[0].top < c[1].bottom && c[0].bottom > c[1].top;
          return {...JSON.parse(r.dataset.observation), width: box.width,
            document_width: document.documentElement.scrollWidth, image_width: img.clientWidth,
            image_height: img.clientHeight, natural_pixels: [img.naturalWidth,img.naturalHeight],
            actual_image: img.src, outside, overlap, detail: r.querySelector('[data-detail]').textContent,
            selected: [...r.querySelectorAll('select')].map(n => n.value)};
        })()`);
        const expected = record.images[model], frame = expected.frames[view];
        const imageHash = sha(Buffer.from(observed.actual_image.split(',')[1], 'base64'));
        delete observed.actual_image;
        if (observed.model !== model || observed.view !== view || observed.selected.join() !== [model,view].join()) throw new Error('Selection mismatch');
        if (observed.width !== width || observed.document_width > width || observed.outside.length || observed.overlap) throw new Error(JSON.stringify(observed));
        if (JSON.stringify(observed.natural_pixels) !== JSON.stringify(frame.pixels)) throw new Error('Image size mismatch');
        if (Math.abs(observed.image_height / observed.image_width - frame.pixels[1] / frame.pixels[0]) > 0.004) throw new Error('Image distorted');
        if (observed.png_sha256 !== frame.png_sha256 || imageHash !== frame.webp_sha256 || observed.longitudinal_span_mm !== expected.longitudinal_span_mm) throw new Error('Display differs from saved render');
        results.push({requested_width: width, scheme, ...observed, loaded_webp_sha256: imageHash});
        const name = `${width}_${scheme}_${model}_${view}.png`;
        const screenshot = await call('Page.captureScreenshot', {format: 'png'});
        const bytes = Buffer.from(screenshot.data, 'base64');
        await writeFile(join(output, name), bytes, {flag: 'wx'});
        screenshots[name] = sha(bytes);
      }
    }
  }
  if (errors.length) throw new Error(JSON.stringify(errors));
  const audit = {observed_at: new Date().toISOString(), preview_sha256: sha(await readFile(preview)),
    record_sha256: sha(await readFile(recordPath)), results, screenshots, javascript_errors: errors,
    scope: 'Saved reference image identity, selection, aspect ratio, layout and themes; no fit or physical verdict'};
  await writeFile(join(output, 'browser_audit.json'), JSON.stringify(audit, null, 2) + '\n', {flag: 'wx'});
  console.log('FASTENING_CAD_BROWSER_OK', JSON.stringify({states: results.length, errors: errors.length}));
} finally {
  if (socket) socket.close();
  chrome.kill('SIGTERM');
}
