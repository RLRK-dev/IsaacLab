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
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',error=>errors.push(String(error)));
const results=[];
try {
  await page.goto(pathToFileURL(path.join(root,'delivery/index.html')).href);
  await page.waitForFunction(()=>document.querySelectorAll('.contact-svg').length===3);
  await page.evaluate(()=>document.fonts.ready);
  for(const width of [1440,736,390,320]) {
    await page.setViewportSize({width,height:1000});
    for(let stage=0;stage<5;stage++) {
      await page.locator(`[data-stage="${stage}"]`).click();
      const result=await page.evaluate(()=>{
        const root=document.getElementById('hvjb-c-contact-layout');
        const labels=[...root.querySelectorAll('svg text')].map(text=>{
          const box=text.getBBox(),view=text.ownerSVGElement.viewBox.baseVal;
          return {text:text.textContent,x:box.x,y:box.y,width:box.width,height:box.height,
            clipped:box.x<-.5 || box.y<-.5 || box.x+box.width>view.width+.5 || box.y+box.height>view.height+.5};
        });
        return {width:innerWidth,stage:Number(root.dataset.stage),
          pressed:root.querySelectorAll('[aria-pressed=true]').length,
          overflow:document.documentElement.scrollWidth>innerWidth,
          detail:root.querySelector('[data-detail]').textContent,labels};
      });
      results.push(result);
      assert.equal(result.stage,stage);assert.equal(result.pressed,1);
      assert(!result.overflow);assert(!result.labels.some(row=>row.clipped),JSON.stringify(result));
    }
  }
  const images=await page.locator('img').evaluateAll(images=>images.map(img=>({src:img.getAttribute('src'),loaded:img.complete&&img.naturalWidth>0})));
  assert.equal(images.length,2);assert(images.every(img=>img.loaded));
  await page.setViewportSize({width:1440,height:1000});
  for(const [stage,name] of [[1,'01_C工程_接触域の比較.png'],[4,'02_C工程_開放空間の比較.png']]){
    await page.locator(`[data-stage="${stage}"]`).click();
    await page.locator('#figure-pack').screenshot({path:path.join(root,'delivery',name)});
  }
  await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  const report={observed_at:new Date().toISOString(),states:results,images,errors,physical_verdict:null};
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(report,null,2)+'\n');
  process.stdout.write('C_CONTACT_BROWSER_COMPLETE states=20 images=2 text_clipping=0 horizontal_overflow=0\n');
} catch(error) {
  fs.writeFileSync(path.join(output,'failure.json'),JSON.stringify({error:String(error),states:results,errors},null,2)+'\n');
  await page.screenshot({path:path.join(output,'failure.png'),fullPage:true});
  throw error;
} finally {await browser.close();}
