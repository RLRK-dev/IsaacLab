#!/usr/bin/env node
// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
/** Inspect a local review page using Node 22 and a new, isolated headless Chrome. */

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { access, mkdir, mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const pause = (milliseconds) => new Promise((done) => setTimeout(done, milliseconds));

function argumentsFrom(argv) {
  const options = {
    output_dir: join(projectRoot, "audit", "op030_split_page_browser_v03"),
    timeout_ms: 120000,
    label: "OP030_split_v03_delivery",
    plan_name: "data/op030_split_shots_v03.json",
    chapter_field: "phases",
  };
  const known = new Set(["stage_path", "page_path", "output_dir", "browser", "timeout_ms", "label", "plan_name", "chapter_field"]);
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index].replace(/^--/, "");
    if (argv[index] === "--help") {
      console.log("node analysis/verify_op030_split_page.mjs --stage_path /path/package " +
        "[--page_path /path/index.html] [--output_dir /path/audit] [--browser /path/chrome] " +
        "[--timeout_ms 120000] [--label probe] [--plan_name data/plan.json] [--chapter_field phases|milestones]");
      return null;
    }
    if (!argv[index].startsWith("--") || !known.has(key) || argv[index + 1] === undefined) {
      throw new Error(`Unknown option or missing value: ${argv[index]}`);
    }
    options[key] = argv[++index];
  }
  if (options.stage_path && !options.page_path) options.page_path = join(options.stage_path, "review_OP030_split_v03.html");
  if (!options.page_path) throw new Error("--stage_path or --page_path is required");
  options.page_path = resolve(options.page_path);
  options.stage_path = resolve(options.stage_path || dirname(options.page_path));
  options.output_dir = resolve(options.output_dir);
  options.timeout_ms = Number(options.timeout_ms);
  if (!Number.isInteger(options.timeout_ms) || options.timeout_ms < 1000 || options.timeout_ms > 180000) {
    throw new Error("--timeout_ms must be an integer between 1000 and 180000");
  }
  if (!["phases", "milestones"].includes(options.chapter_field)) throw new Error("Invalid chapter_field");
  return options;
}

async function browserPath(explicit) {
  const candidates = explicit ? [resolve(explicit)] : [
    "/opt/google/chrome/chrome", "/usr/bin/google-chrome", "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    ...(process.env.PATH || "").split(delimiter).flatMap((directory) =>
      ["google-chrome", "chromium", "chromium-browser"].map((name) => join(directory, name))),
  ];
  for (const candidate of candidates) {
    try {
      await access(candidate, constants.X_OK);
      if ((await stat(candidate)).isFile()) return candidate;
    } catch { /* Try the next executable, never an existing debugging connection. */ }
  }
  throw new Error("Chrome executable not found; supply --browser");
}

class DevTools {
  constructor(socket, deadline) {
    this.socket = socket;
    this.deadline = deadline;
    this.nextId = 0;
    this.pending = new Map();
    this.listeners = new Map();
    socket.addEventListener("message", ({ data }) => {
      const message = JSON.parse(data);
      if (message.id !== undefined) {
        const request = this.pending.get(message.id);
        if (!request) return;
        clearTimeout(request.timer);
        this.pending.delete(message.id);
        if (message.error) request.reject(new Error(JSON.stringify(message.error)));
        else request.resolve(message.result);
      } else {
        for (const listener of this.listeners.get(message.method) || []) listener(message.params);
      }
    });
    socket.addEventListener("close", () => this.rejectAll(new Error("Chrome debugging connection closed")));
    socket.addEventListener("error", () => this.rejectAll(new Error("Chrome debugging connection failed")));
  }

  static async connect(url, deadline) {
    const socket = new WebSocket(url);
    await new Promise((done, fail) => {
      const timer = setTimeout(() => { socket.close(); fail(new Error("Chrome connection timeout")); },
        Math.max(1, deadline - Date.now()));
      socket.addEventListener("open", () => { clearTimeout(timer); done(); }, { once: true });
      socket.addEventListener("error", () => { clearTimeout(timer); fail(new Error("Chrome WebSocket failed")); },
        { once: true });
    });
    return new DevTools(socket, deadline);
  }

  on(method, listener) {
    if (!this.listeners.has(method)) this.listeners.set(method, []);
    this.listeners.get(method).push(listener);
  }

  send(method, params = {}, sessionId, maximumMs = 10000) {
    if (this.socket.readyState !== WebSocket.OPEN) return Promise.reject(new Error("Chrome is disconnected"));
    if (Date.now() >= this.deadline) return Promise.reject(new Error("Overall browser inspection timeout"));
    const id = ++this.nextId;
    return new Promise((done, fail) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        fail(new Error(`CDP timeout: ${method}`));
      }, Math.min(maximumMs, this.deadline - Date.now()));
      this.pending.set(id, { resolve: done, reject: fail, timer });
      this.socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    });
  }

  rejectAll(error) {
    for (const request of this.pending.values()) { clearTimeout(request.timer); request.reject(error); }
    this.pending.clear();
  }

  close() {
    this.rejectAll(new Error("Inspection finished"));
    this.socket.close();
  }
}

async function inspect(options, context, report, deadline) {
  const pageBytes = await readFile(options.page_path);
  report.page = { path: options.page_path, url: pathToFileURL(options.page_path).href,
    sha256: createHash("sha256").update(pageBytes).digest("hex"), bytes: pageBytes.length };
  context.profile = await mkdtemp(join(tmpdir(), "op030-split-browser-"));
  const executable = await browserPath(options.browser);
  if (Date.now() >= deadline) throw new Error("Overall timeout before Chrome launch");
  const chrome = spawn(executable, [
    "--headless=new", `--user-data-dir=${context.profile}`, "--remote-debugging-port=0",
    "--remote-debugging-address=127.0.0.1", "--no-first-run", "--no-default-browser-check",
    "--disable-background-networking", "--disable-component-update", "--disable-sync",
    "--disable-default-apps", "--disable-extensions", "--disable-domain-reliability", "--disable-breakpad",
    "--disable-client-side-phishing-detection", "--safebrowsing-disable-auto-update", "--metrics-recording-only",
    "--disable-features=Translate,MediaRouter,OptimizationHints,CertificateTransparencyComponentUpdater",
    "--host-resolver-rules=MAP * ~NOTFOUND,EXCLUDE localhost", "--password-store=basic", "--use-mock-keychain",
    "--window-size=1200,900", "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"], detached: process.platform !== "win32" });
  context.chrome = chrome;
  context.stderr = "";
  chrome.stderr.on("data", (chunk) => { context.stderr = (context.stderr + chunk).slice(-6000); });
  chrome.on("error", (error) => { context.spawnError = error; });
  report.browser = { executable, pid: chrome.pid, temporary_profile: true, private_profile_accessed: false,
    debugging_bind_address: "127.0.0.1", externally_networked_page_requests_blocked: true };
  let port, socketPath;
  while (Date.now() < deadline) {
    if (context.spawnError) throw context.spawnError;
    if (chrome.exitCode !== null || chrome.signalCode !== null) throw new Error(`Chrome exited: ${context.stderr}`);
    try {
      [port, socketPath] = (await readFile(join(context.profile, "DevToolsActivePort"), "utf8")).trim().split("\n");
      if (/^\d+$/.test(port) && Number(port) <= 65535 && socketPath?.startsWith("/devtools/browser/")) break;
    } catch { /* This file belongs only to the freshly spawned Chrome. */ }
    await pause(60);
  }
  if (!port || !socketPath) throw new Error("Chrome did not publish its temporary debugging port");
  const response = await fetch(`http://127.0.0.1:${port}/json/version`, {
    signal: AbortSignal.timeout(Math.max(1, deadline - Date.now())), redirect: "error",
  });
  if (!response.ok) throw new Error(`Chrome discovery returned HTTP ${response.status}`);
  const version = await response.json();
  report.browser.version = version.Browser;
  const client = await DevTools.connect(`ws://127.0.0.1:${port}${socketPath}`, deadline);
  context.client = client;
  const { targetId } = await client.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await client.send("Target.attachToTarget", { targetId, flatten: true });
  const command = (method, params = {}) => client.send(method, params, sessionId);
  const evaluate = async (expression) => {
    const result = await command("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true,
      userGesture: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const poll = async (expression, limitMs = 4000) => {
    const end = Math.min(deadline, Date.now() + limitMs);
    while (Date.now() < end) {
      const result = await evaluate(expression);
      if (result) return result;
      await pause(80);
    }
    throw new Error(`Page condition timeout: ${expression.slice(0, 160)}`);
  };
  report.javascript_exceptions = [];
  report.failed_resource_requests = [];
  const requestUrls = new Map();
  client.on("Runtime.exceptionThrown", ({ exceptionDetails }) => report.javascript_exceptions.push(exceptionDetails));
  client.on("Network.requestWillBeSent", ({ requestId, request }) => requestUrls.set(requestId, request.url));
  client.on("Network.loadingFailed", (event) => report.failed_resource_requests.push({
    url: requestUrls.get(event.requestId), error: event.errorText, blocked_reason: event.blockedReason,
    cancelled: Boolean(event.canceled), resource_type: event.type,
  }));
  await command("Page.enable");
  await command("Runtime.enable");
  await command("Network.enable");
  await command("Network.setBlockedURLs", { urls: ["http://*", "https://*", "ws://*", "wss://*", "ftp://*"] });
  await command("Network.setCacheDisabled", { cacheDisabled: true });
  const navigation = await command("Page.navigate", { url: report.page.url });
  if (navigation.errorText) throw new Error(`Page navigation failed: ${navigation.errorText}`);
  await poll("document.readyState === 'complete'");
  const hasVideo = await evaluate("Boolean(document.querySelector('video'))");
  if (!hasVideo) throw new Error("The page contains no video element");
  await evaluate("(() => { const v = document.querySelector('video'); v.pause(); v.muted = true; " +
    "v.preload = 'metadata'; if (v.readyState < 1) v.load(); return true; })()");
  await poll("(() => { const v = document.querySelector('video'); if (v.error) throw new Error(v.error.message); " +
    "return v.readyState >= 1 && Number.isFinite(v.duration) && v.videoWidth > 0; })()", 6000);
  report.video = await evaluate("(() => { const v = document.querySelector('video'); return { duration_s: v.duration, " +
    "width_px: v.videoWidth, height_px: v.videoHeight, ready_state: v.readyState, " +
    "source: v.currentSrc, paused: v.paused, error: v.error?.message || null }; })()");
  report.video.source_is_local_file = report.video.source.startsWith("file:");
  if (report.video.source_is_local_file) {
    report.video.file_bytes = (await stat(fileURLToPath(report.video.source))).size;
  }
  const buttons = await evaluate("[...document.querySelectorAll('button[data-time]')].map((b, index) => " +
    "({index, label: b.textContent.trim(), requested_time_s: Number(b.dataset.time)}))");
  report.seek_button_count = buttons.length;
  const planPath = join(options.stage_path, options.plan_name);
  const planBytes = await readFile(planPath);
  const presentation = JSON.parse(planBytes);
  const chapters = presentation[options.chapter_field];
  const expectedButtonCount = chapters.length;
  report.presentation = { path: planPath, sha256: createHash("sha256").update(planBytes).digest("hex"), chapter_field: options.chapter_field };
  report.expected_seek_button_count = expectedButtonCount;
  report.chapter_definitions = buttons.map((button, index) => {
    const chapter = chapters[index];
    const expectedTime = chapter?.[options.chapter_field === "phases" ? "start_s" : "time_s"];
    const expectedLabel = chapter?.[options.chapter_field === "phases" ? "label" : "title"];
    return {index, expected_time_s: expectedTime, expected_label: expectedLabel,
      matches: Boolean(chapter) && Math.abs(button.requested_time_s - expectedTime) < 0.00051 &&
        button.label.replace(/^\d+\s*/, "") === expectedLabel};
  });
  report.seek_results = [];
  for (const button of buttons) {
    const result = { ...button, succeeded: false };
    try {
      if (!Number.isFinite(button.requested_time_s) || button.requested_time_s < 0 ||
          button.requested_time_s > report.video.duration_s) throw new Error("Button time is outside video duration");
      await evaluate(`document.querySelectorAll('button[data-time]')[${button.index}].click()`);
      await poll(`(() => { const v = document.querySelector('video'); return !v.seeking && ` +
        `Math.abs(v.currentTime - ${JSON.stringify(button.requested_time_s)}) <= 0.12; })()`, 2200);
      await evaluate("document.querySelector('video').pause()");
      Object.assign(result, await evaluate("(() => { const v = document.querySelector('video'); return {" +
        "actual_time_s: v.currentTime, seeking: v.seeking, ready_state: v.readyState, paused: v.paused}; })()"));
      result.succeeded = true;
    } catch (error) { result.error = error.message; }
    report.seek_results.push(result);
    if ((button.index + 1) % 25 === 0) console.log("CHAPTER_SEEKS", button.index + 1, expectedButtonCount);
  }
  await evaluate("document.querySelectorAll('video').forEach(v => { v.pause(); v.muted = true; v.preload = 'metadata'; if (v.readyState < 1) v.load(); })");
  await poll("[...document.querySelectorAll('video')].every(v => !v.error && v.readyState >= 1 && v.videoWidth > 0)", 6000);
  report.all_videos = await evaluate("[...document.querySelectorAll('video')].map(v => ({source:v.currentSrc, duration_s:v.duration, width_px:v.videoWidth, height_px:v.videoHeight, error:v.error?.message || null}))");
  report.playback_results = [];
  for (let index = 0; index < report.all_videos.length; index++) {
    const before = await evaluate(`(async () => { const v=document.querySelectorAll('video')[${index}];
      v.currentTime=Math.min(5,v.duration/4); await v.play(); return v.currentTime; })()`);
    await evaluate("new Promise(done => setTimeout(done, 600))");
    const result = await evaluate(`(() => { const v=document.querySelectorAll('video')[${index}];
      v.pause(); return {source:v.currentSrc, current_time_s:v.currentTime, ready_state:v.readyState,
      decoded_frames:v.getVideoPlaybackQuality().totalVideoFrames, error:v.error?.message || null}; })()`);
    result.advanced_s = result.current_time_s - before;
    result.succeeded = result.advanced_s > 0.2 && result.decoded_frames > 0 && result.ready_state >= 2 && !result.error;
    report.playback_results.push(result);
  }
  await evaluate("[...document.images].forEach(img => { img.loading = 'eager'; })");
  try { await poll("[...document.images].every(img => img.complete)", 3500); }
  catch (error) { report.image_load_wait_error = error.message; }
  report.images = await evaluate("[...document.images].map(img => ({src: img.currentSrc || img.src, " +
    "complete: img.complete, natural_width_px: img.naturalWidth, natural_height_px: img.naturalHeight}))");
  for (const image of report.images) {
    image.source_is_local_file = image.src.startsWith("file:");
    image.loaded = image.complete && image.natural_width_px > 0 && image.natural_height_px > 0;
  }
  report.image_loading_forced_eager = true;
  report.local_links = await evaluate("[...document.querySelectorAll('a[href]')].map(a=>({label:a.textContent.trim(),href:a.href,raw:a.getAttribute('href')}))");
  let inventory = null;
  try { inventory = JSON.parse(await readFile(join(options.stage_path, "DELIVERY_SHA256.json"), "utf8")); }
  catch (error) { if (error.code !== "ENOENT") throw error; }
  for (const link of report.local_links) {
    try {
      if (!link.href.startsWith("file:")) throw new Error("Non-local link in an offline page");
      const target = fileURLToPath(link.href);
      const path = relative(options.stage_path, target);
      if (path.startsWith(`..${sep}`) || path === "..") throw new Error("Link escapes the stage directory");
      const info = await stat(target);
      if (!info.isFile() || !info.size) throw new Error("Link is not a nonempty file");
      link.relative_path = path;
      link.bytes = info.size;
      link.sha256 = createHash("sha256").update(await readFile(target)).digest("hex");
      if (inventory && path !== "DELIVERY_SHA256.json") {
        const expectedSha = typeof inventory[path] === "string" ? inventory[path] : inventory[path]?.sha256;
        if (expectedSha !== link.sha256) throw new Error("Link target differs from delivery SHA inventory");
        link.delivery_hash_matches = true;
      }
      link.succeeded = true;
    } catch (error) { link.succeeded = false; link.error = error.message; }
  }
  report.local_link_scope = "Browser-resolved href URLs checked against existing local files and optional delivery SHA inventory; no external navigation or downloads";
  report.viewports = [];
  for (const [width, height] of [[1200, 900], [390, 844]]) {
    await command("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
    await evaluate("window.scrollTo(0, 0); new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))");
    const layout = await evaluate("(() => { const d = document.documentElement; const width = d.clientWidth; " +
      "const scrollWidth = Math.max(d.scrollWidth, document.body?.scrollWidth || 0); return {" +
      "viewport_width_px: width, inner_width_px: innerWidth, scroll_width_px: scrollWidth, " +
      "horizontal_overflow_px: Math.max(0, scrollWidth - width), " +
      "overflow_elements: [...document.querySelectorAll('body *')].map(el => ({el, r: el.getBoundingClientRect()}))" +
      ".filter(({r}) => r.width > 0 && (r.left < -1 || r.right > width + 1)).slice(0, 20)" +
      ".map(({el, r}) => ({tag: el.tagName, id: el.id, class_name: String(el.className), " +
      "left_px: r.left, right_px: r.right}))}; })()");
    const screenshot = join(options.output_dir, `page_top_${width}.png`);
    const capture = await command("Page.captureScreenshot", { format: "png", fromSurface: true,
      captureBeyondViewport: false });
    await writeFile(screenshot, Buffer.from(capture.data, "base64"));
    report.viewports.push({ requested_width_px: width, requested_height_px: height, ...layout, screenshot });
  }
  report.checks = {
    video_metadata_loaded: report.video.duration_s > 0 && report.video.width_px > 0 && report.video.height_px > 0,
    video_source_is_local_file: report.video.source_is_local_file,
    expected_seek_buttons_present: buttons.length === expectedButtonCount,
    chapter_labels_and_times_match_plan: report.chapter_definitions.length === expectedButtonCount && report.chapter_definitions.every(row => row.matches),
    all_seek_buttons_worked: buttons.length === expectedButtonCount && report.seek_results.every((result) => result.succeeded),
    process_video_loaded: report.all_videos.length === 1 && report.all_videos.every(v => v.source.startsWith('file:') && v.width_px > 0 && v.duration_s > 0 && !v.error),
    process_video_played: report.playback_results.length === 1 && report.playback_results.every(v => v.succeeded),
    all_images_loaded: report.images.every((image) => image.loaded),
    all_images_are_local_files: report.images.every((image) => image.source_is_local_file),
    all_local_links_resolve: report.local_links.length > 0 && report.local_links.every(link => link.succeeded),
    no_horizontal_overflow_at_both_widths: report.viewports.every((view) => view.horizontal_overflow_px <= 1),
    no_uncaught_page_exceptions: report.javascript_exceptions.length === 0,
    no_failed_resource_requests: report.failed_resource_requests.every((request) => {
      // Keep media cancellation notifications, and classify only sources whose
      // metadata and actual playback succeeded, after all chapter seeks worked.
      request.completed_video_seek_cancellation = request.cancelled && request.error === "net::ERR_ABORTED" &&
        request.resource_type === "Media" && report.playback_results.some(v => v.source === request.url && v.succeeded) &&
        buttons.length === expectedButtonCount &&
        report.seek_results.every((result) => result.succeeded);
      return request.completed_video_seek_cancellation;
    }),
  };
  report.browser_checks_succeeded = Object.values(report.checks).every(Boolean);
  report.status = report.browser_checks_succeeded ? "browser_checks_completed" : "browser_checks_found_issues";
}

async function cleanup(context) {
  const browser = context.chrome;
  const ended = () => !browser || browser.exitCode !== null || browser.signalCode !== null;
  try { await context.client?.send("Browser.close", {}, undefined, 500); } catch { /* Terminate our own process below. */ }
  context.client?.close();
  const waitUntilExit = async (milliseconds) => {
    const until = Date.now() + milliseconds;
    while (!ended() && Date.now() < until) await pause(40);
  };
  await waitUntilExit(500);
  for (const signal of ["SIGTERM", "SIGKILL"]) {
    if (ended()) break;
    try {
      if (process.platform !== "win32" && browser.pid) process.kill(-browser.pid, signal);
      else browser.kill(signal);
    } catch (error) { if (error.code !== "ESRCH") throw error; }
    await waitUntilExit(400);
  }
  if (context.profile) await rm(context.profile, { recursive: true, force: true, maxRetries: 2, retryDelay: 80 });
  return { owned_browser_exited: ended(), exit_code: browser?.exitCode, signal: browser?.signalCode,
    temporary_profile_removed: Boolean(context.profile), private_profile_accessed: false };
}

async function main() {
  const options = argumentsFrom(process.argv.slice(2));
  if (options === null) return;
  try { await access(options.output_dir); throw new Error("Keep the existing browser report directory unchanged"); }
  catch (error) { if (error.code !== "ENOENT") throw error; }
  await mkdir(options.output_dir, { recursive: true });
  const reportPath = join(options.output_dir, "page_browser_report.json");
  if ([reportPath, join(options.output_dir, "page_top_1200.png"), join(options.output_dir, "page_top_390.png")]
    .includes(options.page_path)) throw new Error("Output must not overwrite the input page");
  const started = Date.now();
  const context = {};
  const report = {
    schema_version: 1, observed_at: new Date().toISOString(), label: options.label,
    purpose: "Local OP030 split page playback, chapter, link and layout diagnostics; no physical-validity verdict",
    timeout_ms: options.timeout_ms, browser_checks_succeeded: false, status: "not_completed",
    limits: ["Browser functionality only; no physical-validity verdict or review of scene geometry.",
      "Page HTTP(S), WebSocket and FTP requests are blocked; debugging uses only loopback.",
      "Screenshots are viewport-top captures, not full-page visual judgments."],
  };
  let timer;
  try {
    await Promise.race([
      inspect(options, context, report, started + options.timeout_ms),
      new Promise((_, fail) => { timer = setTimeout(() => fail(new Error("Overall browser inspection timeout")),
        options.timeout_ms); }),
    ]);
  } catch (error) {
    report.status = "browser_checks_error";
    report.error = error.message;
    report.chrome_stderr_tail = context.stderr || "";
  } finally {
    clearTimeout(timer);
    try { report.cleanup = await cleanup(context); }
    catch (error) { report.cleanup = { error: error.message }; report.browser_checks_succeeded = false; }
    if (report.cleanup.owned_browser_exited !== true) report.browser_checks_succeeded = false;
    report.elapsed_ms = Date.now() - started;
    report.checker = { path: fileURLToPath(import.meta.url), sha256: createHash("sha256").update(await readFile(fileURLToPath(import.meta.url))).digest("hex"),
      reused_from: "scripts/verify_op030_page_v02.mjs", new_dependencies_added: false };
    await writeFile(reportPath, JSON.stringify(report, null, 2) + "\n");
  }
  console.log(JSON.stringify({ report: reportPath, status: report.status,
    browser_checks_succeeded: report.browser_checks_succeeded, elapsed_ms: report.elapsed_ms }));
  if (!report.browser_checks_succeeded) process.exitCode = 1;
}

main().catch((error) => { console.error(error.message); process.exitCode = 1; });
