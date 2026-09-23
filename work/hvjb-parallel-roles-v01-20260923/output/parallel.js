/* Copyright (c) 2022-2026, The Isaac Lab Project Developers. All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 */
"use strict";

(() => {
  const data = JSON.parse(document.getElementById("parallel-data").textContent);
  const buttons = [...document.querySelectorAll("button[data-scenario]")];
  const image = document.getElementById("scenario-image");
  const message = document.getElementById("scenario-message");
  const caption = document.getElementById("scenario-caption");
  const png = document.getElementById("scenario-png");
  const svg = document.getElementById("scenario-svg");
  function select(id) {
    const scenario = data.scenarios.find(row => row.id === id);
    if (!scenario) return;
    buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.scenario === id)));
    image.src = scenario.png;
    image.alt = scenario.title_ja + "の担当図";
    message.textContent = scenario.note_ja;
    message.classList.toggle("overlap", Object.keys(scenario.duplicate_assignments).length > 0);
    caption.textContent = scenario.title_ja + "。独立した条件例で、時系列の移動を再生していません。";
    png.href = scenario.png;
    svg.href = scenario.diagram;
  }
  buttons.forEach(button => button.addEventListener("click", () => select(button.dataset.scenario)));
  select(data.default_scenario);
})();
