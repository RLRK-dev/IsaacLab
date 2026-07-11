# CLAUDE.md pruned-content archive (2026-07-12)

Rs directive 2026-07-12: replace individual case-specific countermeasures with the general **⚓ アンカー式検証** methodology; delete redundant/historical/tip clutter from the always-loaded CLAUDE.md. This file preserves the pruned content (also recoverable via `git show <prune-commit>^:CLAUDE.md`).

## Deleted individual verification/design patches (subsumed by ⚓ アンカー式検証)
Rules §運用14/17/18/28/29/30 (verification) + §19/21/22/23 (RL/env design) + §12 (cable-free test tip). Their specific incidents live in vault `06-Knowledge/LL-{ApproachCable-BugHistory,RewardHacking-Analysis,RewardDeadlock}.md` + memory `feedback-*` + design skills `/reward-design` `/geometric-design` `/pre-check`.
- §18 ground-truth 検証 (実績 ORI-FRAME 1.45rad vs 0.5rad 閾値到達不可)
- §21 obs-reward 整合 (実績 IC obs[17:21] 静的値 → r_ori ノイズ化)
- §22 penalty/reward 比率 >5:1 RED FLAG (実績 AR 18.6:1 hover deadlock)
- §23 multi-world 状態分離 (実績 共有 FK state → 初期 dist 0.5-1.8m)
- §14 動画自己チェック + interpenetration zoom (実績 R-S7.1 D3e)
- §28 agent 出力数値照合 (実績 M2 12D/6D)
- §29 predicate-completeness (実績 P3-grid C1-escape SR 72.8→49.4)
- §30 単点実証 scope 限定 (実績 fix-⑤ +20,0 過大読み)

## Deleted historical/bootstrap notes
- **L判定 運用履歴 Day 1-5 (2026-04-24)**: framework 導入ログ (Day1 §0 導入 / Day2 rule-check Stage1 / Day3-4 統合計画 / Day5 §§本体統合)。Day5 計画書 = `thread-vault/02-Workflow/Day5-L-Integration-Plan.md`。
- **NEST Bootstrap 注記**: NEST section 追加自体は本ルール適用外 (循環回避)、commit 後発動。
- **§25 構造的デッドロック解消記録 (2026-04-16→04-21)**: PreCompact hook exit2 unconditional → auto-compact 全ブロック → SOFT=80/HARD=92 二段階 + SSOT ctx_thresholds.sh + stale flag cleanup + symlink guard で根本対処。詳細 `project_ctx_threshold_design.md`。§25 改訂経緯 (2026-05-10): 旧「debate 前 /handoff 必須」撤回 → 「原則必須ではない」。
- **Newton VBD DISCARDED status narrative**: env6-VBD track (AC/AR/IC/Clamp/Unclamp) 全 DISCARDED → mujoco-コ (Rs 2026-06-26)。SSOT = LEDGER §FAILED item 2-3。Grip = env7-mujoco ACTIVE。

## Deleted redundant sections
- **Session hierarchy 節 (parent/child sessions)**: NEST に superseded (NEST §173-175「NEST subset、仕様書 §3.2/3.3/4/5.1 で代替」)。
- **テスト検証プロトコル詳細**: 動画→ログ→照合 の 3 段は `/verify-run` skill + ⚓ methodology rule 3 に集約。Code C 独立動画判定 = INIT_CODE_C.md。Fingertip Z-Check Gate = test_newton_clip_routing.py 内。ハーネス cycle artifacts (RESULTS_B/STATE.json/EVENT_LOG/VERDICT_C + 5-cam mp4) = harness doc。

## Deleted operational tips (→ skill)
- §6 RUN_METRICS.json 一次 locator → `/experiment-run`
- §9 headless 動画記録 (offscreen 事後生成) → `/verify-run` `/experiment-run`
- §27 Verification Queue (pending-verification.jsonl) → tooling/skill
