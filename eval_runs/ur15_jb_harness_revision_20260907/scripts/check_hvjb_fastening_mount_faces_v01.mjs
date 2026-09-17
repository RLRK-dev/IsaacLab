// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
// Reuses the isolated Chrome/CDP workflow from check_hvjb_fastening_cad_v01.mjs.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [preview, recordPath, output] = process.argv.slice(2);
if (!preview || !recordPath || !output) throw new Error('Usage: checker preview.html record.json output_directory');
const record = JSON.parse(await readFile(recordPath, 'utf8'));
const profile = await mkdtemp(join(tmpdir(), 'hvjb-fastening-mount-browser-'));
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
  const root = "document.getElementById('hvjb-fastening-mount-faces-v01')";
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
      for (const model of ['SES1601', 'SEM2001', 'SEV2001']) {
        await evaluate(`(() => {
          const r = ${root};
          const select = r.querySelector('[data-model]');
          select.value = '${model}'; select.dispatchEvent(new Event('change', {bubbles:true}));
        })()`);
        await pause(120);
        const observed = await evaluate(`(() => {
          const r = ${root}, box = r.getBoundingClientRect();
          const outside = [], labelOverlaps = [], labelSizes = [];
          for (const node of r.querySelectorAll('select, svg, [data-detail], [data-label]')) {
            const b = node.getBoundingClientRect();
            if (b.left < box.left-1 || b.right > box.right+1 || b.top < box.top-1 || b.bottom > box.bottom+1) outside.push(node.tagName);
          }
          const labels = [...r.querySelectorAll('[data-label]')];
          for (let i=0; i<labels.length; i++) {
            labelSizes.push(parseFloat(getComputedStyle(labels[i]).fontSize));
            const a = labels[i].getBoundingClientRect();
            for (let j=i+1; j<labels.length; j++) {
              const b = labels[j].getBoundingClientRect();
              if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top) labelOverlaps.push([i,j]);
            }
          }
          return {...JSON.parse(r.dataset.observation), width: box.width,
            document_width: document.documentElement.scrollWidth, outside, labelOverlaps, labelSizes,
            selected: r.querySelector('select').value,
            figures: [...r.querySelectorAll('svg')].map(svg => ({
              ...JSON.parse(svg.dataset.projection), viewBox: svg.getAttribute('viewBox'),
              paths: ['surface','boundary'].map(kind => svg.querySelector('.'+kind).getAttribute('d'))
            }))};
        })()`);
        const expected = record.models[model], display = record.display[model];
        if (observed.model !== model || observed.selected !== model) throw new Error('Selection mismatch');
        if (observed.width !== width || observed.document_width > width || observed.outside.length || observed.labelOverlaps.length) throw new Error(JSON.stringify(observed));
        if (observed.labelSizes.some(size => size < 11)) throw new Error('Unreadable labels');
        if (observed.gap_mm !== display.gap_mm || observed.triangles !== expected.selected_triangles || observed.boundaries !== expected.boundary_paths) throw new Error('Display differs from saved observation');
        for (const figure of observed.figures) {
          const expectedBounds = figure.view === 'detail' ? display.detail_bounds_mm : display.bounds_mm.map(p => p[0]);
          if (JSON.stringify(figure.xbounds) !== JSON.stringify(expectedBounds)) throw new Error('Unexpected crop');
          if (figure.width !== width || figure.viewBox !== `0 0 ${width} ${figure.height}`) throw new Error('ViewBox rescales labels');
          const coordinates = [display.triangles_mm, display.boundaries_mm];
          for (let i=0; i<2; i++) {
            const wanted = coordinates[i].flat().flatMap(([x,y]) => [
              44 + (x-figure.xbounds[0])*figure.scale,
              figure.top + (figure.transverse_max-y)*figure.scale
            ]);
            const got = [...figure.paths[i].matchAll(/[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?/g)].map(m => Number(m[0]));
            if (got.length !== wanted.length || wanted.some((v,j) => Math.abs(v-got[j]) > 1e-7)) throw new Error('Plane geometry differs from saved projection');
          }
          figure.path_sha256 = figure.paths.map(p => sha(Buffer.from(p)));
          delete figure.paths;
        }
        results.push({requested_width: width, scheme, ...observed});
        const name = `${width}_${scheme}_${model}.png`;
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
    scope: 'Saved plane vertices, equal-axis projection, selection, label bounds and themes; no physical verdict'};
  await writeFile(join(output, 'browser_audit.json'), JSON.stringify(audit, null, 2) + '\n', {flag: 'wx'});
  console.log('FASTENING_MOUNT_BROWSER_OK', JSON.stringify({states: results.length, errors: errors.length}));
} finally {
  if (socket) socket.close();
  chrome.kill('SIGTERM');
}
