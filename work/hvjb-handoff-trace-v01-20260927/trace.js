  // Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
  // All rights reserved.
  // SPDX-License-Identifier: BSD-3-Clause
  const holdData = JSON.parse(byId("handoff-trace-data").textContent);
  const holds = new Map(holdData.jobs.map((row) => [row.id, row]));
  function chooseHold(id, navigate = true) {
    const row = holds.get(id);
    const job = jobs.get(id);
    if (navigate) showTab("holds");
    byId("hold-map").querySelectorAll("button").forEach((node) => node.setAttribute("aria-pressed", String(node.dataset.hold === id)));
    byId("hold-kicker").textContent = `${id} / ${job.location_ja}`;
    byId("hold-title").textContent = job.title_ja;
    byId("hold-status").textContent = row.status_ja;
    byId("hold-primary").textContent = job.primary_ja;
    byId("hold-hands").textContent = job.hands_ja;
    byId("hold-assist").textContent = job.assistance_ja;
    for (const key of ["start", "keep", "end", "reuse"]) byId(`hold-${key}`).textContent = row[`${key}_ja`];
    byId("hold-unresolved").textContent = job.unresolved_ja;
    byId("hold-basis").textContent = row.basis_ja;
    const reserved = holdData.reservations.filter((item) => item.tasks.includes(id));
    byId("hold-reservations").replaceChildren(...reserved.map((item) => {
      const node = document.createElement("div");
      node.className = "hold-reservation";
      const title = document.createElement("strong");
      title.textContent = `${item.resource === "X-C" ? "C専用補助" : "C主腕"}の担当を残す：${item.tasks.join(" → ")}`;
      const note = document.createElement("p"); note.textContent = item.note_ja;
      const condition = document.createElement("small"); condition.textContent = item.condition_ja;
      node.append(title, note, condition);
      return node;
    }));
    byId("hold-job-links").replaceChildren(button(`${id} の手先図と対象部品へ →`, () => chooseJob(id)));
    byId("hold-scene-links").replaceChildren(...job.scene_ids.map((sceneId) => {
      const scene = scenes.get(sceneId);
      const node = button(`${timeLabel(scene.start_s)} · ${scene.title_ja}`, () => {
        if (location.hash !== `#scene=${sceneId}`) history.pushState(null, "", `#scene=${sceneId}`);
        seekScene(sceneId);
      });
      node.dataset.holdScene = sceneId;
      return node;
    }));
    if (navigate && location.hash !== `#hold=${id}`) history.pushState(null, "", `#hold=${id}`);
    if (navigate) byId(innerWidth <= 900 ? "hold-detail" : "panel-holds").scrollIntoView({block:"start"});
  }
  for (const group of holdData.groups) {
    const target = document.querySelector(`[data-hold-group="${group.id}"] .hold-choices`);
    for (const id of group.jobs) {
      const row = jobs.get(id);
      const node = button("", () => chooseHold(id), `${id} ${row.title_ja}の保持と引継ぎを表示`);
      const code = document.createElement("span"); code.textContent = id;
      node.append(code, document.createTextNode(row.title_ja));
      node.dataset.hold = id;
      node.setAttribute("aria-pressed", "false");
      target.append(node);
    }
  }
  chooseHold("D12", false);
  byId("job-hold-link").addEventListener("click", () => {
    const selected = byId("job-buttons").querySelector('[aria-pressed="true"]');
    if (selected) chooseHold(selected.dataset.job);
  });
