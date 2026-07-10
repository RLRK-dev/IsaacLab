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
  - "2026-07-11 04:25 p6 (PLAN-KEEPER、%12 dispatch 04:24 反映): node 登録 (%12 登録案、verbatim 照合の上で)。起動承認 = Rs 直接指示 (NEST §3.1、一次記録 = %12 session)。assignee = %10 (COORD2、監査 charter 受領・[DEFINE] 着手予定)。⚠除外境界 = 07-Design 内部 (renewal node owns、二重 scope 禁止) を goal_verification に明記。次 = %10 [DEFINE] ping。provenance 正直記載: Rs verbatim は %12 relay 経由、p6 は Rs→%12 raw を未直接観測 (paper node と同型の honesty)。node IN_PROGRESS 維持。"
---

## goal / means / status
- **goal:** frontmatter verbatim (via %12 relay) + inference 解釈参照。監査 → disposition map → per-item Rs 承認最適化。
- **means:** %10 (COORD2) が監査実施。%12 charter に基づき survey → disposition map → 最適化提案 (per-item Rs 承認 gate)。設計内容改変は Rs 専権。
- **status:** IN_PROGRESS — node 登録済 (監査 charter 発行・%10 [DEFINE] ping 待ち)。除外 = 07-Design 内部 (renewal 二重 scope 禁止)。
