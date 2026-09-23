// Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
// All rights reserved.
//
// SPDX-License-Identifier: BSD-3-Clause
(() => {
  "use strict";
  let groupId = "FG_FUSE";
  let angle = "oblique";
  const sections = Array.from(document.querySelectorAll("[data-group-panel]"));
  const groupButtons = Array.from(document.querySelectorAll("[data-select-group]"));
  const angleButtons = Array.from(document.querySelectorAll("[data-select-angle]"));
  function update() {
    sections.forEach(section => { section.hidden = section.dataset.groupPanel !== groupId; });
    groupButtons.forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.selectGroup === groupId));
    });
    angleButtons.forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.selectAngle === angle));
    });
    document.querySelectorAll("[data-view-angle]").forEach(figure => {
      figure.hidden = figure.dataset.viewAngle !== angle;
    });
    const chosen = sections.find(section => section.dataset.groupPanel === groupId);
    document.getElementById("selection-status").textContent = chosen.dataset.label + "を表示中";
  }
  groupButtons.forEach(button => button.addEventListener("click", () => {
    groupId = button.dataset.selectGroup;
    update();
  }));
  angleButtons.forEach(button => button.addEventListener("click", () => {
    angle = button.dataset.selectAngle;
    update();
  }));
  update();
})();
