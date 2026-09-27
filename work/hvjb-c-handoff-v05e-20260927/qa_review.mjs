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
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const entry=process.argv[2] || path.join(root,'delivery/index.html');
const seeks=[];
try {
  await page.goto(pathToFileURL(entry).href);
  await page.waitForFunction(()=>document.querySelector('video').readyState>=1);
  await page.locator('video').evaluate(v=>{
    const observe=(_now,metadata)=>{window.lastDecodedFrame=metadata.mediaTime;v.requestVideoFrameCallback(observe)};
    v.requestVideoFrameCallback(observe);
  });
  const metadata=await page.locator('video').evaluate(v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,src:v.currentSrc}));
  assert(Math.abs(metadata.duration-209.2)<0.02);assert.equal(metadata.width,1920);assert.equal(metadata.height,1080);
  const buttons=page.locator('button[data-seek]');assert.equal(await buttons.count(),16);
  for(let i=0;i<16;i++) {
    const button=buttons.nth(i), expected=Number(await button.getAttribute('data-seek'));
    await button.click();
    await page.waitForFunction(t=>{const v=document.querySelector('video');return !v.seeking && v.readyState>=2
      && Math.abs(v.currentTime-t)<1 && Math.abs(window.lastDecodedFrame-t)<1},expected);
    await page.locator('video').evaluate(v=>v.pause());
    const state=await page.locator('video').evaluate(v=>({time:v.currentTime,decoded_frame_time:window.lastDecodedFrame,
      error:v.error?.message??null}));
    assert.equal(state.error,null);seeks.push({button:i,expected,...state});
  }
  await buttons.nth(0).click();
  await page.waitForFunction(()=>Math.abs(window.lastDecodedFrame-175.2)<0.3);
  await page.locator('video').evaluate(v=>v.pause());
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(output,'desktop_page.png'),fullPage:true});
  await buttons.nth(9).click();
  await page.waitForFunction(()=>Math.abs(window.lastDecodedFrame-181.2)<0.3);
  await page.locator('video').evaluate(v=>v.pause());
  await page.locator('video').screenshot({path:path.join(output,'c_regrip_player.png')});
  const images=await page.locator('img').evaluateAll(imgs=>imgs.map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})));
  assert(images.every(i=>i.loaded));
  const desktopOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert(!desktopOverflow);
  await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(output,'mobile_page.png'),fullPage:true});
  const mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert(!mobileOverflow);
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({observed_at:new Date().toISOString(),entry,metadata,seeks,images,desktopOverflow,mobileOverflow,errors},null,2)+'\n');
  process.stdout.write('C_REVIEW_BROWSER_COMPLETE buttons=16 images=2 desktop_and_mobile_no_horizontal_overflow=true\n');
} finally {await browser.close();}
