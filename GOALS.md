# GOALS.md — pointer (superseded dashboard)

> ⚠ この file は 2026-03-20 凍結の dashboard だった (Track A/B 二本立て・旧 robot-platform・Newton Phase 7/8 等の framing はすべて **superseded**)。
> 現行の目標・Phase・進捗・制約の SSOT は下記へ。GOALS.md は tracked pointer + goal_evidence 契約 stub のみを保持する
> (planning-surface consolidation 2026-07-02, node `T-ROOT-Planning-Surfaces-Consolidation-20260702`, M4)。

## SSOT Pointers (現行)

| 何を | どこ |
|------|------|
| 目標定義・Phase・pipeline | `thread_isaac_lab/thread-vault/04-Specs/SOMA.md` |
| FOUNDATIONAL INVARIANTS | `thread_isaac_lab/thread-vault/04-Specs/RS71-System-Spec-SSOT.md` |
| 設計成否 (成否 SSOT) | `thread_isaac_lab/thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` |
| 読む入口 (地図) | `docs/logical_decomposition.html` |
| 全数値パラメータ | `thread_isaac_lab/configs/task_config.py` |
| 禁止事項・制約・運用ルール | `CLAUDE.md` (+ `.claude/rules/prohibited.md`) |

## Current Sprint

現行 sprint / 現在地 → 読む入口の地図 `docs/logical_decomposition.html` + 成否 SSOT `00-DESIGN-STATUS-LEDGER.md`。
（旧 Current Sprint 表 [2026-03-20 Newton Phase 7/8] は superseded。）

## Goal Evidence Contract (trajectory_contract_v1)

goal_evidence 4点（grasp_frame, pre_rotation_frame, post_rotation_frame, hook_sequence）が全て揃って初めてGoal PASSとする。
goal_evidence不足の場合、Goal PASS不可（FAIL_PROTOCOL扱い）。

動的最適化の証跡:
- plan_revision_count: 計画修正回数を記録し、収束を確認
- progress_metric.samples >= 2: 最低2サンプル以上のPhase進捗計測
