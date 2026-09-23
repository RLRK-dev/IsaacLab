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
const folder = path.join(root, "output");
const output = path.join(root, "browser_qa02");
await mkdir(output);
const digest = async (name) => createHash("sha256").update(await readFile(name)).digest("hex");
const errors = [];
const failures = [];
const observations = [];
const screenshots = [];
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1680, height: 1050 }, deviceScaleFactor: 1 });
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("requestfailed", (request) => failures.push({
    url: request.url(), type: request.resourceType(), reason: request.failure(),
  }));
  const entry = pathToFileURL(path.join(folder, "index.html")).href;
  await page.goto(entry);
  await page.waitForFunction(() => document.querySelector("video").readyState === 4);
  const metadata = await page.locator("video").evaluate((video) => ({
    duration: video.duration, width: video.videoWidth, height: video.videoHeight,
    currentSrc: video.currentSrc, paused: video.paused,
  }));
  assert.equal(metadata.duration, 155.2);
  assert.equal(metadata.width, 1920);
  assert.equal(metadata.height, 1080);
  assert.equal(await page.locator("#scene-buttons button").count(), 22);
  assert.equal(await page.locator("#job-buttons button").count(), 20);
  assert.equal(await page.locator("#feature-buttons button").count(), 92);
  assert.equal(await page.locator("#diagram-buttons button").count(), 6);
  observations.push({ initialVideoMetadata: metadata, scenes: 22, jobs: 20, features: 92, diagrams: 6 });

  async function capture(name) {
    const file = path.join(output, name + ".png");
    await page.screenshot({ path: file });
    screenshots.push({ file: path.relative(root, file), sha256: await digest(file), viewport: page.viewportSize() });
  }

  async function checkSeek(scene, time) {
    await page.waitForFunction((wanted) => {
      const video = document.querySelector("video");
      return !video.seeking && video.readyState === 4 && Math.abs(video.currentTime - wanted) < 0.001;
    }, time);
    const label = await page.locator("#scene-current").textContent();
    assert(label.includes(scene));
    assert.equal(await page.locator("video").evaluate((video) => video.paused), true);
    const mediaError = await page.locator("video").evaluate((video) => video.error?.code ?? null);
    assert.equal(mediaError, null);
    observations.push({ scene, requestedTime: time, visibleLabel: label, readyState: 4, mediaError });
  }

  for (const [scene, time] of [["H06_loading", 119], ["H06_pickup", 129], ["H05_P16", 139], ["H05_P17", 147]]) {
    await page.locator(`a[href="#scene=${scene}"]`).click();
    await checkSeek(scene, time);
    await capture(scene);
  }
  await page.locator("#tab-jobs").click();
  await page.locator('#job-buttons [data-job="D50"]').click();
  assert.equal(await page.locator("#job-scenes button").count(), 3);
  await capture("job_D50");
  await page.locator("#job-scenes button").filter({ hasText: "H05_P17" }).click();
  await checkSeek("H05_P17", 147);

  await page.locator("#tab-features").click();
  await page.locator("#feature-search").fill("P16");
  assert.equal(await page.locator("#feature-buttons button").count(), 1);
  await page.locator('#feature-buttons [data-feature="P16"]').click();
  await page.waitForFunction(() => ["feature-context", "feature-isolated"].every((id) => {
    const image = document.getElementById(id);
    return image.complete && image.naturalWidth > 0;
  }));
  await capture("feature_P16");

  await page.goto(pathToFileURL(path.join(folder, "hand_review/index.html")).href);
  await page.locator('a[href="../index.html#scene=H05_P16"]').click();
  await checkSeek("H05_P16", 139);
  observations.push({ handReviewDeepLink: "H05_P16", source: "hand_review/index.html" });

  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto(entry + "#scene=H06_loading");
  await checkSeek("H06_loading", 119);
  const widths = await page.evaluate(() => ({ viewport: innerWidth, body: document.body.scrollWidth, page: document.documentElement.scrollWidth }));
  assert(widths.body <= widths.viewport && widths.page <= widths.viewport);
  observations.push({ mobileWidth: widths });
  await capture("mobile_H06");
  assert.deepEqual(errors, []);
  const cancellations = failures.filter((row) => row.type === "media" &&
    row.reason?.errorText === "net::ERR_ABORTED" && row.url === metadata.currentSrc);
  const unexpectedFailures = failures.filter((row) => !cancellations.includes(row));
  assert.deepEqual(unexpectedFailures, []);
  const report = {
    observed_at: new Date().toISOString(), method: "Isolated headless Chrome; local file package; no user browser profile",
    browser_version: browser.version(), entry_sha256: await digest(path.join(folder, "index.html")),
    script_sha256: await digest(fileURLToPath(import.meta.url)), observations, screenshots,
    page_errors: errors, all_requestfailed_events: failures, media_cancellations_during_seek_or_navigation: cancellations,
    unexpected_failed_requests: unexpectedFailures, physical_acceptance_verdict: null,
    visual_inspection_recorded_separately: true,
  };
  await writeFile(path.join(output, "browser_receipt.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
  process.stdout.write("V05C_BROWSER_QA metadata=155.2s scenes=22 jobs=20 features=92 seek_links=4 mobile_overflow=false\n");
} catch (error) {
  await writeFile(path.join(output, "failure_receipt.json"), JSON.stringify({
    observed_at: new Date().toISOString(), error: String(error), observations, screenshots, errors, failures,
  }, null, 2) + "\n", { flag: "wx" });
  throw error;
} finally {
  await browser.close();
}
