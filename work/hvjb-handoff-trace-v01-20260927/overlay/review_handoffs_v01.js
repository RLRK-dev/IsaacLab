"use strict";
(() => {
  const data = JSON.parse(document.getElementById("review-data").textContent);
  const byId = (id) => document.getElementById(id);
  const jobs = new Map(data.jobs.map((row) => [row.id, row]));
  const features = new Map(data.features.map((row) => [row.id, row]));
  const scenes = new Map(data.scenes.map((row) => [row.id, row]));
  const tabs = ["video", "holds", "jobs", "features", "diagrams"];
  const video = byId("video");
  let currentScene = null;
  let currentFeature = null;
  let wantedSeek = null;

  const timeLabel = (seconds) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
  function button(text, action, label) {
    const node = document.createElement("button");
    node.type = "button";
    node.textContent = text;
    if (label) node.setAttribute("aria-label", label);
    node.addEventListener("click", action);
    return node;
  }
  function fieldList(node, entries) {
    node.replaceChildren();
    entries.forEach(([key, value]) => {
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = key;
      detail.textContent = value || "未確定";
      node.append(term, detail);
    });
  }
  function showTab(name) {
    tabs.forEach((tab) => {
      byId(`tab-${tab}`).setAttribute("aria-selected", String(tab === name));
      byId(`tab-${tab}`).tabIndex = tab === name ? 0 : -1;
      byId(`panel-${tab}`).hidden = tab !== name;
    });
    if (name !== "video") video.pause();
  }
  tabs.forEach((tab, index) => {
    byId(`tab-${tab}`).addEventListener("click", () => showTab(tab));
    byId(`tab-${tab}`).addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      showTab(tabs[next]);
      byId(`tab-${tabs[next]}`).focus();
    });
  });
  function setScene(id) {
    if (id === currentScene) return;
    currentScene = id;
    const row = scenes.get(id);
    byId("scene-current").textContent = `${id} · ${row.title_ja}`;
    byId("scene-hold").textContent = row.hold_or_limit_ja;
    byId("scene-buttons").querySelectorAll("button").forEach((node) => node.setAttribute("aria-pressed", String(node.dataset.scene === id)));
  }
  function seekScene(id) {
    const row = scenes.get(id);
    showTab("video");
    video.pause();
    wantedSeek = row.start_s;
    if (video.readyState >= 1) {
      video.currentTime = wantedSeek;
      wantedSeek = null;
    }
    setScene(id);
    byId("panel-video").scrollIntoView({block:"start"});
  }
  video.addEventListener("loadedmetadata", () => {
    if (wantedSeek !== null) { video.currentTime = wantedSeek; wantedSeek = null; }
  });
  video.addEventListener("timeupdate", () => {
    const t = Math.min(video.currentTime, data.duration_s - 0.001);
    const row = data.scenes.find((scene) => scene.start_s <= t && t < scene.stop_s);
    if (row) setScene(row.id);
  });
  data.scenes.forEach((row) => {
    const node = button("", () => seekScene(row.id), `${timeLabel(row.start_s)} ${row.title_ja}の場面へ移動`);
    node.className = "scene-button";
    node.dataset.scene = row.id;
    node.setAttribute("aria-pressed", "false");
    const time = document.createElement("time");
    const label = document.createElement("span");
    time.textContent = timeLabel(row.start_s);
    label.textContent = row.title_ja;
    node.append(time, label);
    byId("scene-buttons").append(node);
  });
  const handUsage = JSON.parse(byId("hand-usage-data").textContent);
  function renderHandLinks(jobId) {
    const row = handUsage.jobs.find((item) => item.id === jobId);
    const nodes = row.variant_ids.map((id) => {
      const variant = handUsage.variants.find((item) => item.id === id);
      const link = document.createElement("a");
      link.className = "job-hand-link";
      link.href = `hand_review/index_v03.html#${id}`;
      link.dataset.hand = id;
      const figure = document.createElement("img");
      figure.src = `hand_review/figures/${variant.image}`;
      figure.alt = `${variant.title}の既存比較図`;
      const text = document.createElement("span");
      const title = document.createElement("strong");
      title.textContent = `${id} · ${variant.title}`;
      const status = document.createElement("span");
      status.className = "hand-link-status";
      status.textContent = variant.status;
      const action = document.createElement("span");
      action.className = "hand-link-action";
      action.textContent = "図・保持面・退避の説明へ →";
      text.append(title, status, action);
      link.append(figure, text);
      return link;
    });
    byId("job-hand-links").replaceChildren(...nodes);
    byId("job-hand-note").textContent = row.note_ja;
  }
  function chooseJob(id, navigate = true) {
    const row = jobs.get(id);
    if (navigate) showTab("jobs");
    byId("job-buttons").querySelectorAll("button").forEach((node) => node.setAttribute("aria-pressed", String(node.dataset.job === id)));
    byId("job-kicker").textContent = `${row.id} / 元工程 ${row.operation} / ${row.location_ja}`;
    byId("job-title").textContent = row.title_ja;
    fieldList(byId("job-fields"), [["主担当",row.primary_ja],["手先の用途",row.hands_ja],["補助の役割",row.assistance_ja],["支持の引継ぎ",row.transfer_ja],["残っている確認",row.unresolved_ja]]);
    renderHandLinks(id);
    byId("job-scenes").replaceChildren(...row.scene_ids.map((id) => button(`${id} · ${timeLabel(scenes.get(id).start_s)}`, () => seekScene(id))));
    byId("job-features").replaceChildren(...row.review_feature_ids.map((id) => button(id, () => chooseFeature(id), `${id} ${features.get(id).name_ja}を確認`)));
    if (!row.review_feature_ids.length) {
      const note = document.createElement("p");
      note.className = "secondary";
      note.textContent = "この仕事に直接対応づけた写真特徴はありません。";
      byId("job-features").append(note);
    }
    if (navigate && location.hash !== `#job=${id}`) history.pushState(null, "", `#job=${id}`);
    if (navigate) byId("panel-jobs").scrollIntoView({block:"start"});
  }
  data.jobs.forEach((row) => {
    const node = button("", () => {
      chooseJob(row.id, false);
      if (location.hash !== `#job=${row.id}`) history.pushState(null, "", `#job=${row.id}`);
    });
    const id = document.createElement("span");
    const name = document.createElement("span");
    id.className = "job-id"; id.textContent = row.id; name.textContent = row.title_ja;
    node.append(id, name); node.className = "job-button"; node.dataset.job = row.id;
    node.setAttribute("aria-pressed", "false");
    byId("job-buttons").append(node);
  });
  function updateFeatureButtons() {
    const query = byId("feature-search").value.trim().toLocaleLowerCase();
    const group = byId("feature-group").value;
    const filtered = data.features.filter((row) => (!group || row.group === group) && `${row.id} ${row.name_ja} ${row.group_name_ja}`.toLocaleLowerCase().includes(query));
    byId("feature-count").textContent = `${filtered.length} / ${data.features.length} 項目`;
    const nodes = filtered.map((row) => {
      const node = button(row.id, () => chooseFeature(row.id, false), `${row.id} ${row.name_ja}`);
      node.dataset.feature = row.id;
      node.setAttribute("aria-pressed", String(row.id === currentFeature));
      return node;
    });
    byId("feature-buttons").replaceChildren(...nodes);
    if (!filtered.length) {
      const note = document.createElement("p"); note.textContent = "一致する項目はありません。";
      byId("feature-buttons").append(note);
    }
  }
  function chooseFeature(id, navigate = true) {
    const row = features.get(id);
    currentFeature = id;
    if (navigate) { showTab("features"); byId("feature-search").value = ""; byId("feature-group").value = ""; }
    updateFeatureButtons();
    byId("feature-kicker").textContent = `${row.id} / ${row.group_name_ja}`;
    byId("feature-title").textContent = row.name_ja;
    byId("feature-context").src = row.context_image;
    byId("feature-context").alt = `${row.id} ${row.name_ja}の完成状態内の位置。青が選択対象。`;
    byId("feature-isolated").src = row.isolated_image;
    byId("feature-isolated").alt = `${row.id} ${row.name_ja}に属する保存メッシュの単体表示。`;
    byId("feature-visibility").textContent = row.context_selected_visible_pixels === 0 ? "この視点では対象が他の形状に隠れています。単体図で参照してください。" : "選択対象以外もすべて含む完成状態の保存モデルです。";
    fieldList(byId("feature-fields"), [["対応の根拠",row.basis_ja],["残っている確認",row.unresolved_ja],["施工の採用",row.physical_operation_selected || "この工程対応だけでは物理施工を確定していません。"]]);
    byId("feature-jobs").replaceChildren(...row.review_task_ids.map((id) => button(`${id} ${jobs.get(id).title_ja}`, () => chooseJob(id))));
    if (navigate) byId("panel-features").scrollIntoView({block:"start"});
  }
  new Map(data.features.map((row) => [row.group,row.group_name_ja])).forEach((name,id) => {
    const option = document.createElement("option"); option.value = id; option.textContent = name;
    byId("feature-group").append(option);
  });
  byId("feature-search").addEventListener("input", updateFeatureButtons);
  byId("feature-group").addEventListener("change", updateFeatureButtons);
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

  const diagramNames = ["全体の流れ", "部品群との対応", "支持の引継ぎ", "20仕事の一覧", "3STと補助の占有", "後工程"];
  function chooseDiagram(index) {
    const path = `output/pages/page-${index + 1}.png`;
    byId("diagram-image").src = path;
    byId("diagram-image").alt = diagramNames[index];
    byId("diagram-link").href = path;
    byId("diagram-caption").textContent = `${index + 1} / 6 · ${diagramNames[index]}。画像を選ぶと原寸で開きます。`;
    byId("diagram-buttons").querySelectorAll("button").forEach((node,i) => node.setAttribute("aria-pressed", String(i === index)));
  }
  diagramNames.forEach((name,index) => byId("diagram-buttons").append(button(`${index + 1} ${name}`, () => chooseDiagram(index))));
  chooseJob("D00", false);
  chooseFeature("P01", false);
  chooseDiagram(0);
  setScene("INTRO");
  showTab("video");
  function followReviewLink() {
    const params = new URLSearchParams(location.hash.slice(1));
    const holdId = params.get("hold");
    if (holdId && holds.has(holdId)) { chooseHold(holdId); return; }
    const jobId = params.get("job");
    if (jobId && jobs.has(jobId)) { chooseJob(jobId); return; }
    const value = params.get("scene");
    if (value && scenes.has(value)) seekScene(value);
  }
  window.addEventListener("hashchange", followReviewLink);
  document.querySelectorAll('a[href^="#scene="]').forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const value = new URLSearchParams(link.hash.slice(1)).get("scene");
      if (scenes.has(value)) {
        if (location.hash !== link.hash) history.pushState(null, "", link.hash);
        seekScene(value);
      }
    });
  });
  followReviewLink();
})();
