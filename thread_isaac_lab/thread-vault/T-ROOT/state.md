---
node_id: T-ROOT
node_name: "5-clip cable routing (vision-based) — 現行の中間目標"
goal: "Isaac Lab / SIM で 5-clip cable routing を vision-based で動作させ、最終/ultimate target として 95% 成功率へ改善する。現在の bar は rough/imperfect でも SIM で基本動作させること。real-world / physical UR15 × 2 deploy は current project scope ではない。REAL2SIM / sim-to-real は future consideration のみ。Foundation (robot mechanism / environment / cable) は厳密に構成する。"
means: "知覚 (T-Vision) + 制御 (T-Skill) + 統合 (T-L1-B) + 経験基盤 (T-Empirical) + 失敗回復 (T-WM) の 5 capability axis"
goal_verification: |
  95% 成功率（ultimate target）。現在の bar = SIM で基本動作。
  ⚠ 本 node の goal 文字列は、これまで `scripts/build_nest_snapshot.py` が stub として供給していた文言をそのまま採録した（p6 が state.md 化に際して文言を変更していない）。
status: IN_PROGRESS
parent_node: T-PRODUCTION-LINE
children_nodes:
  - T-Empirical
  - T-Forward-Capability
  - T-L1-B
  - T-L1-F
  - T-L1-G
  - T-L1-H
  - T-L1C-PerSkill-RL
  - T-L1X-Substrate-Realism
  - T-Meta
  - T-Predicate-Redefinition
  - T-ROOT-COORD
  - T-ROOT-DesignDoc-Renewal-20260711
  - T-ROOT-Kinematic-Pin-Complete-Removal-20260719
  - T-ROOT-Legacy-Architecture
  - T-ROOT-Paper-BCRL-JA-20260710
  - T-ROOT-Pivot-Chain-Architecture-Review
  - T-ROOT-Planning-Surfaces-Consolidation-20260702
  - T-ROOT-R0-Measurement-Foundation
  - T-ROOT-R1-Product-Predicate-Decision
  - T-ROOT-R2-Architecture-Redesign
  - T-ROOT-RS-TECH-LEAD2
  - T-ROOT-StepTable-Verbal-Teaching-20260703
  - T-ROOT-Vault-DesignContent-Audit-20260711
  - T-ROOT-VaultRefCopy-SpotAudit-20260711
  - T-ROOT-Verbal-Teaching-20260705
  - T-Skill
  - T-Vision
  - T-WM
dependencies:
  precedent: []
  blocker: []
session_history: []
created: 2026-07-27T12:26:40+09:00
last_updated: 2026-07-27T12:26:40+09:00
spec_version: LTM-1 v1.2
---

# T-ROOT — 5-clip cable routing（中間目標）

## 0. 本 file 化の経緯

`T-ROOT` はこれまで **state.md を持たず**、`scripts/build_nest_snapshot.py` が
stub として goal / means を供給していた（`T_ROOT_GOAL` / `T_ROOT_MEANS`）。
2026-07-27 の Rs 指示「最上位に（生産ライン）、その次に現在の目標（中間目標）」により
**親を持つ必要が生じた**ため、data として state.md を作成した。
⭐ **script は変更していない**（logic 変更を避け、data で解決）。

## 1. 文言の非改変

goal / means は stub が供給していた文字列を **そのまま**採録している。⇒ 本 file 化によって
tree 上の T-ROOT の意味は変わらない。**変わったのは `parent_node` が null → `T-PRODUCTION-LINE` になった点のみ。**

## 2. ⚠ goal 文字列に含まれる古い記述（p6 は書き換えない）

- ✅**「physical Franka × 2」= 訂正済 → 「UR15 × 2」**（Rs 直接指示 2026-07-27「UR15だぞ」）。⚠p6 は当初これを「goal 変更 = Rs 専権」として flag に留めたが、**誤った事実の削除は goal の変更ではない**（Rs 指摘「これは完全に誤りだ。なぜ削除しない」）。同種の訂正は今後 flag で止めず直す。⛔ただし **2026-06-05 当時の記録**（各 node の session_history・log.md・eval_runs・S1B doc の「current frame (2026-06-05)」）は、当時 robot が Franka だった事実の記録ゆえ **書き換えない**。
- **「real-world deploy は current project scope ではない」** — 上位に `T-PRODUCTION-LINE`（実ラインの実現）が置かれた現在、
  この一文の射程は Rs の再確認を要する。
⇒ いずれも **goal の変更 = Rs 専権**ゆえ p6 は書き換えず、ここに flag のみ置く。接地 = LEDGER 統治ブロック。
