  const handUsage = JSON.parse(byId("hand-usage-data").textContent);
  function renderHandLinks(jobId) {
    const row = handUsage.jobs.find((item) => item.id === jobId);
    const nodes = row.variant_ids.map((id) => {
      const variant = handUsage.variants.find((item) => item.id === id);
      const link = document.createElement("a");
      link.className = "job-hand-link";
      link.href = `hand_review/index_v02.html#${id}`;
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
