---
node_id: T-ROOT-Vault-DesignContent-Audit-20260711
node_name: "Vault 設計内容 scatter/重複 監査 + 最適化"
goal: "Rs 直接指示 verbatim (via %12 relay 2026-07-11 04:24、p6 未直接観測 [Rs→%12 channel 範囲外、正直記載]):「設計内容がvaultで散在、重複などないか？あれば最適化して」。解釈 (inference、%12 charter 起案・Rs verbatim ではない): 監査 (設計内容の scatter/重複 特定) → disposition map 作成 → 最適化は per-item Rs 承認 (一括改変せず item ごとに承認 gate)。"
goal_verification: |
  DoD (charter レベル、%10 [DEFINE] で精緻化):
  ① scatter/重複 survey: 設計内容の所在を列挙 (%12 即時 survey = 04-Specs 10+ / 06-Knowledge 設計 15+ / eval_runs live 設計 doc 32 本)
  ② disposition map: 各 scatter/重複 item に keep / merge / reference-over-copy / archive の disposition を付与 (memory feedback-vault-consistency-reference-over-copy 準拠)
  ③ 最適化 = per-item Rs 承認 gate (設計内容改変は Rs 専権、一括改変禁止)
  ⚠除外 = **07-Design 内部 doc 群 (renewal node T-ROOT-DesignDoc-Renewal-20260711 が owns、二重 scope 禁止)**
  最終 gate = per-item Rs 承認。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "Rs 直接指示 (Rs→%12; via %12 relay 2026-07-11 04:24; Rs 側送信時刻・raw wording = p6 未直接観測 [正直記載])"
    - "%12 監査 charter → %10 (COORD2) 発行済 (2026-07-11 04:2x)"
  blocker: []
created: 2026-07-11T04:24:00+09:00
last_updated: 2026-07-11T04:25:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-11 04:55 Rs ⭐**batch V1 build 授権 (verbatim「承認」— 文脈 = 唯一 pending の V1 授権 [inference]、%12 bank)** — 2 段の第 2 段 (V1 = PR-1): LEDGER +12 lineage 行 (status = Rs-confirmable 明記、member-file 列挙列) + 50 file doc_class tag (tag-only-diff gate: 1add/0del/0body-mod)。執行 plan = EXEC_PLAN v1.1 (content sha 567439b7、①' pin 精確化済 = 執行同ターン sha 測定 = provenance 生成 + 存在照合のみ STOP)。executor = %10、sequence = 事前宣言 ①'②③④⑤ → %12 verify。V2 (banner 22) = V1 PASS 後に別途 1 行授権。"
  - "2026-07-11 04:38 Rs ⭐⭐**最適化 package = 承認 (AskUserQuestion「package 承認 (推奨)」採択、%12 bank) = policy/design 承認 (2 段の第 1 段)** — 承認内容: **PR-1** (untracked 51 本に LEDGER 追跡 + doc_class frontmatter tag、ファイル移動なし = cite 破壊ゼロ) / **PR-4** (superseded lineage ~23 本 [DQ7/B-BC/W0-e packet 系] に banner + SUPERSEDED 行) / **PR-3** (reference-over-copy spot-audit = follow-on task 化) / **PR-2** (工程表の 07-Design 昇格 = 後日個別提案) / **⛔mass file-move = 非採用確定**。監査 verify = %12 PASS (sha fe9bb92b、spot-check 3/3、repo-wide 値散在は in-scope 値より大の verify 注記付き)。執行 = renewal 同型 2 段: 本承認 = policy、**各執行 batch (V1=PR-1 / V2=PR-4) は執行計画起草 → %12 verify → Rs 1 行授権 → 執行**。執行設計上の注意 (%12): LEDGER 行は per-file 51 行でなく **lineage 粒度 (~10-13 行 + member file 列挙)** を推奨 — 生きた SSOT の肥大防止。executor = %10。"
  - "2026-07-11 04:25 p6 (PLAN-KEEPER、%12 dispatch 04:24 反映): node 登録 (%12 登録案、verbatim 照合の上で)。起動承認 = Rs 直接指示 (NEST §3.1、一次記録 = %12 session)。assignee = %10 (COORD2、監査 charter 受領・[DEFINE] 着手予定)。⚠除外境界 = 07-Design 内部 (renewal node owns、二重 scope 禁止) を goal_verification に明記。次 = %10 [DEFINE] ping。provenance 正直記載: Rs verbatim は %12 relay 経由、p6 は Rs→%12 raw を未直接観測 (paper node と同型の honesty)。node IN_PROGRESS 維持。"
---

## goal / means / status
- **goal:** frontmatter verbatim (via %12 relay) + inference 解釈参照。監査 → disposition map → per-item Rs 承認最適化。
- **means:** %10 (COORD2) が監査実施。%12 charter に基づき survey → disposition map → 最適化提案 (per-item Rs 承認 gate)。設計内容改変は Rs 専権。
- **status:** IN_PROGRESS — node 登録済 (監査 charter 発行・%10 [DEFINE] ping 待ち)。除外 = 07-Design 内部 (renewal 二重 scope 禁止)。
