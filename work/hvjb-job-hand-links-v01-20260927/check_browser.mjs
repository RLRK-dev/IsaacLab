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
const folder = path.join(root, "preview");
const output = path.join(root, "browser_qa");
const entryPath = path.join(folder, "index_v05d_1.html");
const entry = pathToFileURL(entryPath).href;
const usage = JSON.parse(await readFile(path.join(folder, "data/job_hand_links_v01.json"), "utf8"));
const digest = async (name) => createHash("sha256").update(await readFile(name)).digest("hex");
await mkdir(output);
const errors = [], failures = [], observations = [], screenshots = [];
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("requestfailed", (request) => failures.push({ url: request.url(), type: request.resourceType(), reason: request.failure() }));
  async function capture(name) {
    const file = path.join(output, `${name}.png`);
    await page.screenshot({ path: file });
    screenshots.push({ file: path.relative(root, file), sha256: await digest(file), viewport: page.viewportSize() });
  }
  async function checkJob(row) {
    assert.equal(await page.locator("#tab-jobs").getAttribute("aria-selected"), "true");
    assert((await page.locator("#job-kicker").textContent()).startsWith(row.id + " /"));
    const ids = await page.locator("#job-hand-links a").evaluateAll((nodes) => nodes.map((node) => node.dataset.hand));
    assert.deepEqual(ids, row.variant_ids);
    assert.equal(await page.locator("#job-hand-note").textContent(), row.note_ja);
    await page.waitForFunction(() => Array.from(document.querySelectorAll("#job-hand-links img")).every((img) => img.complete && img.naturalWidth > 0));
    assert.equal(await page.locator("video").evaluate((video) => video.paused), true);
    observations.push({ job: row.id, shown_hand_uses: ids, note_visible: true, images_loaded: true });
  }
  await page.goto(entry + "#job=D00");
  assert.equal(await page.locator("#job-buttons button").count(), 20);
  assert.equal(await page.locator("#feature-buttons button").count(), 92);
  assert.equal(await page.locator("#scene-buttons button").count(), 22);
  for (const row of usage.jobs) {
    await page.locator(`#job-buttons [data-job="${row.id}"]`).click();
    await checkJob(row);
    assert.equal(new URL(page.url()).hash, `#job=${row.id}`);
    if (["D00", "D31", "D50", "D60", "D61"].includes(row.id)) {
      await page.locator("#job-detail").scrollIntoViewIfNeeded();
      await capture(`desktop_${row.id}`);
    }
  }
  for (const variant of usage.variants) {
    const jobId = variant.jobs[0];
    await page.goto(entry + `#job=${jobId}`);
    await page.locator(`#job-hand-links [data-hand="${variant.id}"]`).click();
    assert.equal(new URL(page.url()).hash, `#${variant.id}`);
    const card = page.locator(`article#${variant.id}`);
    assert.equal(await card.locator("h2").textContent(), variant.title);
    await card.locator(`.job-links a[href="../index_v05d_1.html#job=${jobId}"]`).click();
    await checkJob(usage.jobs.find((row) => row.id === jobId));
    observations.push({ round_trip: variant.id, job: jobId, matching_card_and_return: true });
  }
  await page.goto(entry + "#job=D50");
  await page.locator("#job-scenes button").filter({ hasText: "H05_P16" }).click();
  await page.waitForFunction(() => { const v = document.querySelector("video"); return v.readyState === 4 && !v.seeking && Math.abs(v.currentTime - 139) < 0.001; });
  assert.equal(await page.locator("video").evaluate((v) => v.error?.code ?? null), null);
  observations.push({ scene_from_job: "H05_P16", time: 139, media_error: null });
  await page.goto(entry + "#job=D11");
  await page.locator('#job-buttons [data-job="D31"]').click();
  await page.goBack();
  await checkJob(usage.jobs.find((row) => row.id === "D11"));
  observations.push({ browser_back_restores_job: "D11" });
  await page.setViewportSize({ width: 430, height: 932 });
  for (const id of ["D31", "D50", "D61"]) {
    await page.goto(entry + `#job=${id}`);
    await checkJob(usage.jobs.find((row) => row.id === id));
    await page.locator("#job-detail").scrollIntoViewIfNeeded();
    const widths = await page.evaluate(() => ({ viewport: innerWidth, body: document.body.scrollWidth, root: document.documentElement.scrollWidth }));
    assert(widths.body <= widths.viewport && widths.root <= widths.viewport);
    observations.push({ mobile_job: id, widths });
    await capture(`mobile_${id}`);
  }
  assert.deepEqual(errors, []);
  const cancellations = failures.filter((row) => row.type === "media" && row.reason?.errorText === "net::ERR_ABORTED" && row.url.endsWith("HVJB_line_split_process_concept_v05d_review.mp4"));
  const unexpected = failures.filter((row) => !cancellations.includes(row));
  assert.deepEqual(unexpected, []);
  await writeFile(path.join(output, "browser_receipt.json"), JSON.stringify({
    observed_at: new Date().toISOString(), browser: browser.version(), entry_sha256: await digest(entryPath),
    script_sha256: await digest(fileURLToPath(import.meta.url)), observations, screenshots,
    page_errors: errors, all_requestfailures: failures, media_cancellations: cancellations,
    unexpected_failed_requests: unexpected, formal_physical_verdict: null,
  }, null, 2) + "\n", { flag: "wx" });
  process.stdout.write("JOB_HAND_BROWSER_QA jobs=20 round_trips=12 mobile_overflow=false\n");
} catch (error) {
  await writeFile(path.join(output, "failure_receipt.json"), JSON.stringify({
    observed_at: new Date().toISOString(), error: String(error), observations, screenshots, errors, failures,
  }, null, 2) + "\n", { flag: "wx" });
  throw error;
} finally {
  await browser.close();
}
