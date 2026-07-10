---
node_id: T-ROOT-DesignDoc-Renewal-20260711
node_name: "設計文書 Fable5 刷新 (07-Design 主要 doc 群、構造から・canonical 値不変)"
goal: "Rs 裁定 (2026-07-11 00:30、%12 AskUserQuestion 3 点、選択肢 label = verbatim、bank = routeexec node `1fb2ce4aae`): 対象 =「07-Design 主要 doc 群」/ 深さ =「構造から刷新」(canonical 値不変保証付き) / tracked 化 =「承認」。07-Design 主要設計文書を Fable5 で構造から刷新する。canonical 値 (数値・決定・sha anchor) の不変を保証しつつ、構造・可読性を刷新。"
goal_verification: |
  DoD (charter = %12 00:35 dispatch、L3):
  step 0: 残 6 file の tracked 化提案 (一括)
  → RENEWAL_PLAN packet → 5体 [VERIFY] → %12 verify → Rs 承認 → per-doc 執行。
  不変保証 = canonical 値 (数値 / 決定記録 / sha anchor) の before/after 照合を per-doc で証跡化。
  除外推奨 = 00-DESIGN-STATUS-LEDGER.md (生きた SSOT、刷新対象外)。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "Rs 裁定 3 点 2026-07-11 00:30 (bank = routeexec node `1fb2ce4aae`; 一次 = %12 session AskUserQuestion 回答、選択肢 label verbatim)"
    - "先行執行 2 件: RL-Routing-Design.md tracked 化 (commit `59badc4b7a`、3760 行、内容 sha256 = eaf05513 [%12 明確化 00:39: file 内容 hash であり commit hash でない]、p6 独立確認 = git ls-files 1) / D-1 訂正注記 :2710 (p5 `fa8166cfcd`、表 v1.0a-r1、表 sha 26934095 = p6 独立照合 EXACT)"
    - "VT 工程表 v1.0a Rs-APPROVED 発効 (設計基盤 surface、p5) — 刷新は同 surface 運用の延長"
  blocker: []
created: 2026-07-11T00:37:00+09:00
last_updated: 2026-07-11T00:37:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-11 00:37 p6 (PLAN-KEEPER, w2:p6): node 登録 (%12 NEST 案 00:36、bank 1fb2ce4aae の裁定 verbatim と照合済 = 一致)。assignee = p5 (VT-DESIGN、設計基盤 surface)。charter = %12 00:35 dispatch 済 (step 0 = 残 6 file tracked 化提案 → RENEWAL_PLAN packet → 5体 → %12 verify → Rs 承認 → per-doc 執行)。現況 = p5 見積り中。L3 (07-Design path match)。除外推奨 = LEDGER (生きた SSOT)。"
---

## goal / means / status
- **goal:** 07-Design 主要 doc 群の構造刷新 (canonical 値不変保証)。verbatim = frontmatter 参照。
- **means:** p5 (設計基盤 surface) 実行、charter chain = step 0 tracked 化提案 → RENEWAL_PLAN → 5体 → %12 → Rs → per-doc。L3。
- **status:** IN_PROGRESS (charter 発行済、p5 見積り中)。
