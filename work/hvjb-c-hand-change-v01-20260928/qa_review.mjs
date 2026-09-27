// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved. SPDX-License-Identifier: BSD-3-Clause
import { chromium } from '/home/rlrk/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root=path.dirname(fileURLToPath(import.meta.url));
const output=path.join(root,'browser_qa');
assert(!fs.existsSync(output));fs.mkdirSync(output);
const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
const errors=[];page.on('pageerror',error=>errors.push(String(error)));
const results=[];
try {
  await page.goto(pathToFileURL(path.join(root,'delivery/index.html')).href);
  await page.waitForFunction(()=>document.querySelectorAll('.method-svg').length===3);
  await page.evaluate(()=>document.fonts.ready);
  for(const width of [1440,736,390,320]){
    await page.setViewportSize({width,height:1000});
    for(const method of ['common','jaws','whole']){
      await page.locator(`button[data-method="${method}"]`).click();
      for(let stage=0;stage<6;stage++){
        await page.locator(`button[data-stage="${stage}"]`).click();
        const result=await page.evaluate(()=>{
          const root=document.getElementById('review');
          const labels=[...root.querySelectorAll('svg text')].map(text=>{
            const box=text.getBoundingClientRect(),svg=text.ownerSVGElement.getBoundingClientRect();
            const transform=text.getScreenCTM();
            const fontSize=parseFloat(getComputedStyle(text).fontSize)*Math.hypot(transform.a,transform.b);
            return {text:text.textContent,font_size_px:fontSize,
              clipped:box.left<svg.left-.5||box.top<svg.top-.5||box.right>svg.right+.5||box.bottom>svg.bottom+.5};
          });
          return {width:innerWidth,method:root.dataset.method,stage:Number(root.dataset.stage),
            pressed:root.querySelectorAll('[aria-pressed=true]').length,
            overflow:document.documentElement.scrollWidth>innerWidth,
            support:document.getElementById('support-text').textContent,labels};
        });
        results.push(result);
        assert.equal(result.method,method);assert.equal(result.stage,stage);assert.equal(result.pressed,2);
        assert(!result.overflow);assert(!result.labels.some(row=>row.clipped),JSON.stringify(result));
        assert(result.labels.every(row=>row.font_size_px>=11),JSON.stringify(result));
      }
    }
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#config-capture').screenshot({path:path.join(root,'delivery/01_C工程_手先切替3案.png')});
  await page.locator('button[data-method="whole"]').click();
  await page.locator('button[data-stage="2"]').click();
  await page.locator('#sequence-capture').screenshot({path:path.join(root,'delivery/02_C工程_交換中の支持.png')});
  await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
  const links=await page.locator('a[data-local-link]').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('href')));
  assert.equal(links.length,2);
  const finalRoot='/home/rlrk/Downloads/HVJB_C工程_手先切替の比較_v01_20260928';
  links.forEach(link=>assert(fs.existsSync(path.resolve(finalRoot,link)),link));
  assert.deepEqual(errors,[]);
  const report={observed_at:new Date().toISOString(),states:results,links,errors,physical_verdict:null};
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(report,null,2)+'\n');
  process.stdout.write('C_HAND_CHANGE_BROWSER_COMPLETE states=72 links=2 text_clipping=0 horizontal_overflow=0 new_mp4=0\n');
}catch(error){
  fs.writeFileSync(path.join(output,'failure.json'),JSON.stringify({error:String(error),states:results,errors},null,2)+'\n');
  await page.screenshot({path:path.join(output,'failure.png'),fullPage:true});
  throw error;
}finally{await browser.close();}
