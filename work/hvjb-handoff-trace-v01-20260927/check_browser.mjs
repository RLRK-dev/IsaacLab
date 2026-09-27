// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
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
const entryPath = path.join(folder, "index_v05d_2.html");
const entry = pathToFileURL(entryPath).href;
const trace = JSON.parse(await readFile(path.join(folder, "data/handoff_trace_v01.json"), "utf8"));
const usage = JSON.parse(await readFile(path.join(folder, "data/job_hand_links_v01.json"), "utf8"));
const payload = JSON.parse(await readFile(path.join(folder, "data/line_review_data_v05d.json"), "utf8"));
const digest = async (name) => createHash("sha256").update(await readFile(name)).digest("hex");
await mkdir(output);
const observations = [], errors = [], failures = [], screenshots = [];
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1540, height: 1100 }, deviceScaleFactor: 1 });
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("requestfailed", (request) => failures.push({ url: request.url(), type: request.resourceType(), reason: request.failure() }));
  async function capture(name, locator) {
    const file = path.join(output, `${name}.png`);
    await locator.screenshot({ path: file });
    screenshots.push({ file: path.relative(root, file), sha256: await digest(file), viewport: page.viewportSize() });
  }
  async function checkHold(row) {
    const job = payload.jobs.find((item) => item.id === row.id);
    assert.equal(await page.locator("#tab-holds").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator("#hold-title").textContent(), job.title_ja);
    assert.equal(await page.locator("#hold-primary").textContent(), job.primary_ja);
    assert.equal(await page.locator("#hold-assist").textContent(), job.assistance_ja);
    for (const key of ["start", "keep", "end", "reuse"]) assert.equal(await page.locator(`#hold-${key}`).textContent(), row[`${key}_ja`]);
    assert.equal(await page.locator("#hold-unresolved").textContent(), job.unresolved_ja);
    assert.equal(await page.locator("#hold-status").textContent(), row.status_ja);
    const reserved = trace.reservations.filter((item) => item.tasks.includes(row.id));
    assert.equal(await page.locator(".hold-reservation").count(), reserved.length);
    assert.equal(await page.locator("video").evaluate((video) => video.paused), true);
    observations.push({ job: row.id, phases_and_roles_match: true, reservations: reserved.map((item) => item.id) });
  }
  await page.goto(entry + "#hold=D12");
  assert.equal(await page.locator("#hold-map button").count(), 20);
  assert.equal(await page.locator("#feature-buttons button").count(), 92);
  assert.equal(await page.locator("#scene-buttons button").count(), 22);
  await capture("desktop_overview", page.locator("#hold-map"));
  for (const row of trace.jobs) {
    await page.locator(`[data-hold="${row.id}"]`).click();
    await checkHold(row);
    assert.equal(new URL(page.url()).hash, `#hold=${row.id}`);
    await page.locator("#hold-job-links button").click();
    assert.equal(await page.locator("#tab-jobs").getAttribute("aria-selected"), "true");
    assert((await page.locator("#job-kicker").textContent()).startsWith(row.id + " /"));
    await page.locator("#job-hold-link").click();
    await checkHold(row);
    observations.push({ hold_job_round_trip: row.id });
    if (["D31", "D45", "D50", "D81"].includes(row.id)) await capture(`desktop_${row.id}`, page.locator("#hold-detail"));
  }
  for (const variant of usage.variants) {
    const jobId = variant.jobs[0];
    await page.goto(entry + `#job=${jobId}`);
    await page.locator(`[data-hand="${variant.id}"]`).click();
    assert.equal(new URL(page.url()).pathname.split("/").pop(), "index_v03.html");
    await page.locator(`article#${variant.id} .job-links a[href="../index_v05d_2.html#job=${jobId}"]`).click();
    await page.locator("#job-hold-link").click();
    await checkHold(trace.jobs.find((row) => row.id === jobId));
    observations.push({ hand_round_trip: variant.id, returns_to_updated_entry: true });
  }
  for (const [id, sceneId] of [["D12", "S05"], ["D31", "S07"], ["D40", "S08"], ["D42", "S09"], ["D45", "S10"], ["D50", "H05_P16"], ["D81", "S15"], ["D80", "S16"]]) {
    await page.goto(entry + `#hold=${id}`);
    await page.locator(`[data-hold-scene="${sceneId}"]`).click();
    const t = payload.scenes.find((row) => row.id === sceneId).start_s;
    await page.waitForFunction((time) => { const v = document.querySelector("video"); return v.readyState === 4 && !v.seeking && Math.abs(v.currentTime - time) < 0.001; }, t);
    assert.equal(await page.locator("video").evaluate((v) => v.error?.code ?? null), null);
    await page.goBack();
    await checkHold(trace.jobs.find((row) => row.id === id));
    observations.push({ scene_from_hold: sceneId, time: t, back_restores_hold: id });
  }
  await page.goto(entry + "#hold=D31");
  await page.locator("#tab-holds").focus();
  await page.keyboard.press("ArrowRight");
  assert.equal(await page.locator("#tab-jobs").getAttribute("aria-selected"), "true");
  await page.keyboard.press("ArrowLeft");
  assert.equal(await page.locator("#tab-holds").getAttribute("aria-selected"), "true");
  observations.push({ keyboard_tabs_checked: true });
  await page.setViewportSize({ width: 430, height: 932 });
  for (const id of ["D31", "D50", "D81"]) {
    await page.goto(entry + `#hold=${id}`);
    await checkHold(trace.jobs.find((row) => row.id === id));
    const widths = await page.evaluate(() => ({ viewport: innerWidth, body: document.body.scrollWidth, root: document.documentElement.scrollWidth }));
    assert(widths.body <= widths.viewport && widths.root <= widths.viewport);
    observations.push({ mobile_hold: id, widths });
    if (id === "D50") await capture(`mobile_${id}`, page.locator("#hold-detail"));
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
  process.stdout.write("HANDOFF_BROWSER_QA jobs=20 hand_round_trips=12 scene_round_trips=8 mobile_overflow=false\n");
} catch (error) {
  await writeFile(path.join(output, "failure_receipt.json"), JSON.stringify({
    observed_at: new Date().toISOString(), error: String(error), observations, screenshots, errors, failures,
  }, null, 2) + "\n", { flag: "wx" });
  throw error;
} finally { await browser.close(); }
