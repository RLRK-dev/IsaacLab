// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP workflow from check_hvjb_local_access_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, specPath, output] = process.argv.slice(2);
if (!preview || !specPath || !output) throw new Error('Usage: checker preview.html spec.json output_directory');
const spec = JSON.parse(await readFile(specPath, 'utf8'));
const profile = await mkdtemp(join(tmpdir(), 'hvjb-compact-hand-browser-'));
await mkdir(output, {recursive: true});
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
  const root = "document.getElementById('hvjb-compact-hand-20260917')";
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
      for (const state of ['hold', 'open']) {
        await evaluate(`${root}.querySelector('[data-hand-state="${state}"]').click()`);
        await pause(80);
        const observed = await evaluate(`(() => {
          const r = ${root};
          const outside = [], overlap = [];
          for (const svg of r.querySelectorAll('svg')) {
            const frame = svg.getBoundingClientRect();
            const labels = [...svg.querySelectorAll('[data-label]')].map(n => ({text: n.textContent, box: n.getBoundingClientRect()}));
            labels.forEach(({text, box}) => { if (box.left < frame.left - 1 || box.right > frame.right + 1 || box.top < frame.top - 1 || box.bottom > frame.bottom + 1) outside.push(text); });
            labels.forEach((a, i) => labels.slice(i + 1).forEach(b => { if (a.box.left < b.box.right && a.box.right > b.box.left && a.box.top < b.box.bottom && a.box.bottom > b.box.top) overlap.push([a.text, b.text]); }));
          }
          return {state: r.dataset.state, width: r.clientWidth, documentWidth: document.documentElement.scrollWidth,
            fingers: r.querySelectorAll('[data-finger]').length, pads: r.querySelectorAll('[data-contact]').length,
            opening: [...r.querySelectorAll('[data-finger]')].map(n => +n.dataset.opening),
            pressed: [...r.querySelectorAll('button[aria-pressed="true"]')].map(n => n.dataset.handState),
            bodies: [...r.querySelectorAll('[data-candidate]')].map(n => { const rect = n.querySelector('rect'); return {id: n.dataset.candidate, width: +rect.dataset.bodyWidthMm, depth: +rect.dataset.bodyDepthMm, text: n.textContent}; }),
            outside, overlap};
        })()`);
        if (observed.state !== state || observed.fingers !== 2 || observed.pads !== 4 || observed.pressed.join() !== state) throw new Error(JSON.stringify(observed));
        if (observed.documentWidth > width || observed.outside.length || observed.overlap.length) throw new Error(JSON.stringify(observed));
        for (const item of observed.bodies) {
          const source = spec.candidates.find(c => c.id === item.id);
          if (!source || source.body_width_mm !== item.width || source.body_depth_mm !== item.depth) throw new Error('Body dimensions differ from source record');
        }
        if (state === 'hold' && observed.opening.some(value => value !== 0)) throw new Error('Nominal hold drawing differs');
        if (state === 'open' && observed.opening.some(value => value <= 0)) throw new Error('Open interaction did not move fingers');
        results.push({requested_width: width, scheme, ...observed});
        const name = `${width}_${scheme}_${state}.png`;
        const screenshot = await call('Page.captureScreenshot', {format: 'png'});
        const bytes = Buffer.from(screenshot.data, 'base64');
        await writeFile(join(output, name), bytes, {flag: 'wx'});
        images[name] = sha(bytes);
      }
    }
  }
  if (errors.length) throw new Error(JSON.stringify(errors));
  const audit = {observed_at: new Date().toISOString(), preview_sha256: sha(await readFile(preview)),
    spec_sha256: sha(await readFile(specPath)), results, images, javascript_errors: errors,
    scope: 'UI, source correspondence and label bounds only; no physical verdict'};
  await writeFile(join(output, 'browser_audit.json'), JSON.stringify(audit, null, 2) + '\n', {flag: 'wx'});
  console.log('COMPACT_HAND_BROWSER_OK', JSON.stringify({states: results.length, errors: errors.length}));
} finally {
  if (socket) socket.close();
  chrome.kill('SIGTERM');
}
