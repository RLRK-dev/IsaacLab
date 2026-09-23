// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "/home/rlrk/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const root = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(root, "playback_qa");
await mkdir(output);
const digest = async (name) => createHash("sha256").update(await readFile(name)).digest("hex");
const entry = path.join(root, "output/index.html");
const observations = [];
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1680, height: 1050 }, deviceScaleFactor: 1 });
  for (const [scene, time] of [["H06_loading", 119], ["H05_P16", 139]]) {
    await page.goto(pathToFileURL(entry).href + "#scene=" + scene);
    await page.waitForFunction((wanted) => {
      const video = document.querySelector("video");
      return !video.seeking && video.readyState === 4 && Math.abs(video.currentTime - wanted) < 0.001;
    }, time);
    await page.locator("video").evaluate((video) => video.play());
    await page.waitForFunction((start) => document.querySelector("video").currentTime >= start + 1.1, time);
    await page.locator("video").evaluate((video) => video.pause());
    await page.mouse.move(1600, 10);
    await page.waitForTimeout(1000);
    const state = await page.locator("video").evaluate((video) => ({
      currentTime: video.currentTime, readyState: video.readyState, paused: video.paused,
      mediaError: video.error?.code ?? null, frames: video.getVideoPlaybackQuality().totalVideoFrames,
    }));
    assert(state.currentTime > time + 1 && state.currentTime < time + 3);
    assert.equal(state.mediaError, null);
    assert(state.frames > 1);
    const screenshot = path.join(output, scene + ".png");
    await page.screenshot({ path: screenshot });
    observations.push({ scene, start: time, ...state, screenshot: path.basename(screenshot), sha256: await digest(screenshot) });
  }
  const report = {
    observed_at: new Date().toISOString(), entry_sha256: await digest(entry), script_sha256: await digest(fileURLToPath(import.meta.url)),
    method: "Headless Chrome: start and pause playback after successful scene seek; investigate transient native spinner",
    observations, physical_acceptance_verdict: null,
  };
  await writeFile(path.join(output, "playback_receipt.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
  process.stdout.write("V05C_PLAYBACK_QA two_chapters_advance_and_pause=true\n");
} finally {
  await browser.close();
}
