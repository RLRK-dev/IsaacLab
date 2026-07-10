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
- **status:** IN_PROGRESS (packet v0.1 起草済、5体 debate 前)。

## log
- 2026-07-11 00:4x (p5 VT-DESIGN): **RENEWAL_PLAN packet v0.1-DRAFT 起草完了** → `eval_runs/troot_verbal_teaching_20260705/RENEWAL_PLAN_07DESIGN.md`。内容: §1 inventory 11 doc/16.7k 行 (LEDGER status 照合列込) / §2 step-0 提案 (tracked 化 6 file 前 sha 固定 + VGroove ' M' = 内容検証済 currentization commit 案、origin 不明は %12 とも一致) / §3 disposition (RENEW 2 / CONSOLIDATE = PoseEst 系譜 [LEDGER 照合: v3.2 PARKED head + 4 SUPERSEDED、FAILED 混在なし] Option P-light 推奨 vs P-full = Rs decision / ARCHIVE-LABEL 3 [Progress verbatim 保存 guardrail 明記 / S1B 復活禁止 / VGroove] / EXCLUDE = LEDGER) / §4 新構造 skeleton (STATUS banner = LEDGER mirror + reference-over-copy + HISTORICAL 区画 + §5 版管理準拠) / §5 canonical-invariance 機械検査案 (数値 token 多重集合 diff==∅ + 43-step row-wise EXACT + 除外 regex pre-registered、script 設計のみ) / **§6 cite-breakage 実数 (行 cite 69/21 + § cite 56/28 + 名前系; policy = rename ゼロ + §番号後方互換 + migration map 必須 + banked evidence retro-edit 禁止)** / §7 batch 0/A/B/C + gate / §8 louds (除外 regex = 5体攻撃対象指定 / cite 再 grep / Fable5 期限注記) / §9 Rs decision 4 項。**次 = 5体 debate (L3 pre、CC1 = p5)。**
