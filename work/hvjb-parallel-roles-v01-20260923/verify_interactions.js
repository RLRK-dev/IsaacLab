/* Copyright (c) 2022-2026, The Isaac Lab Project Developers. All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 */
"use strict";

// Plain Node callback checks. This does not launch a browser or assess its layout.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const base = __dirname;
const html = fs.readFileSync(path.join(base, "output/index.html"), "utf8");
const content = html.match(/<script type="application\/json" id="parallel-data">([\s\S]*?)<\/script>/)[1];
const data = JSON.parse(content);
const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
const elements = new Map();
function element(id) {
  assert(ids.has(id), `Missing actual HTML id: ${id}`);
  if (!elements.has(id)) {
    elements.set(id, {
      textContent: id === "parallel-data" ? content : "",
      attributes: {},
      classes: new Set(),
      setAttribute(name, value) { this.attributes[name] = value; },
      classList: { toggle(name, enabled) { this[name] = enabled; } }
    });
  }
  return elements.get(id);
}
const buttons = [...html.matchAll(/<button[^>]*data-scenario="([^"]+)"[^>]*>/g)].map(match => ({
  dataset: { scenario: match[1] },
  attributes: {},
  handlers: {},
  setAttribute(name, value) { this.attributes[name] = value; },
  addEventListener(name, handler) { this.handlers[name] = handler; }
}));
const document = {
  getElementById: element,
  querySelectorAll(selector) { assert.equal(selector, "button[data-scenario]"); return buttons; }
};
vm.runInNewContext(fs.readFileSync(path.join(base, "output/parallel.js"), "utf8"), { document });
assert.equal(element("scenario-image").src, "figures/AC.png");
assert.equal(buttons.length, 8);
for (const button of buttons) {
  button.handlers.click();
  const row = data.scenarios.find(item => item.id === button.dataset.scenario);
  assert.equal(button.attributes["aria-pressed"], "true");
  assert.equal(buttons.filter(item => item.attributes["aria-pressed"] === "true").length, 1);
  assert.equal(element("scenario-image").src, row.png);
  assert.equal(element("scenario-png").href, row.png);
  assert.equal(element("scenario-svg").href, row.diagram);
  assert.equal(element("scenario-message").textContent, row.note_ja);
  assert.equal(element("scenario-message").classList.overlap, ["AB", "ABC"].includes(row.id));
}
process.stdout.write("PLAIN_NODE_CALLBACK_CHECK_COMPLETE cases=8 initial=AC browser=false\n");
