---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-envcore
node_name: "P2 whole-route env-core (RL env class 骨格)"
goal: "spec v1.5 §4 に基づく whole-route C1→C2 RL env-core を build する — obs 57D / action α-6D residual (非累積 Δ) / reward sparse-primary predicate (G1-G6 latched-monotonic) / termination (horizon 900 + terminates) / common-mode guards。staged build chain の第 1 component (env-core → route-executor → oracle → OG → trainer)。"
goal_verification: |
  env-core smoke DoD 8 項 PASS (spec v1.5 §4): ①throughput ≥9.7 実効 fps ②device parity (per-phase predicate-fire + 終端 verdict 一致, cuda:0-only pin は FAIL 分岐) ③cg-GPU whole-route screen (全 phase finite + nacon engage + no nefc overflow) ④horizon 実測 max-of-81 (P3 piggyback) ⑤Δ=const drift-zero (=0.0 EXACT) ⑥predicate unit-test @cuda:0 (6 phase 全 fire + no-re-fire + guards-quiet) ⑦handover-fidelity (route-executor 接続後、qpos/qvel L∞) ⑧corner-miss 分布 (P3 grid 供給済)。
  現況 (2026-07-06 10:35): [DEFINE] = Rs packet §8-3 staged charter 授権 + %12 charter (10:27)。§運用4 grounding DONE (spec v1.5 + packet v1.1)。[L-TRIAGE] = L3 HIGH (%12 APPROVE 10:33)。build 計画 起草中 → %12 checkpoint (code 前) → 5体 [VERIFY] → build。code 未着手 (0-commit, locked runner 不触)。
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2
children_nodes: []
dependencies:
  precedent:
    - "W0-e F-1b snap-down COMMITTED 6808964dc3 (official SR 0.716=58/81; env pin W0E_F1B_SNAPDOWN=1 = env-core 0.716 再現条件 / cuda:0 canonical 承継)"
    - "P2 spec v1.5 + artifacts v1.3 + packet v1.1 = Rs W0-a′ 一括承認 (state.md b7d7857dfc, 2026-07-06 10:1x)"
  blocker: []
created: 2026-07-06T10:35:32+09:00
last_updated: 2026-07-06T10:35:32+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-06 10:27 lead %12 (RS-TECH-LEAD, w2:p4): P2 env-core build charter (Rs W0-a′ packet v1.1 一括承認 b7d7857dfc, staged charter 授権) → %11 (COORD, w2:p3) §運用4 grounding (spec v1.5 118L + packet v1.1 98L) + [TASK]/[L-TRIAGE]=L3 HIGH → %12 APPROVE (10:33, 子 node 作成承認 = Rs packet §8-3 + [DEFINE]) → %11 本 state.md 作成 (1:1 binding = %11 session) → build 計画 起草へ。p6 に direct ping (parent children_nodes + manifest 反映)。"
---

# P2 whole-route env-core (T-ROOT-optE-route-dapg-C1C2-P2-envcore) — IN_PROGRESS

**Rs 承認履歴:** 2026-07-06 10:1x「W0-a′ packet v1.1 一括承認」(spec v1.5 + artifacts v1.3 を P2 設計基底採択 + §8 staged build charter 発行授権、state.md b7d7857dfc)。本 node = staged charter 第 1 component (env-core)。

## goal / means / status
- **goal (検証可能):** 上 frontmatter goal_verification の smoke DoD 8 項 PASS で env-core を verified とする。
- **means (leaf action):** 新規 env class ファイル群 (≤800 行 diff, 個別 L3 chain) を build。obs 57D / α-6D residual 非累積 (`Δ=const→drift=0` regression) / reward sparse-primary G1-G6 predicate (latched-monotonic, fire-once, never-revoked; phase one-hot=argmax(earned)) / termination (horizon 900, terminates=explosion/drop/span逸脱/reach-fail, time_outs=timeout純度のみ) / guards (action-path per-arm clamp 禁止=common-mode only [INV#2 as-executed 保護] / span 監視 dual-grip phase のみ {G1-G2窓}∪{G4-G6窓} informative-tier / mujoco-assert)。phase-clock の state-bank 機構は route-executor component (次段) と接続 — env-core は interface/stub。
- **status:** IN_PROGRESS (build 計画 起草段, code 未着手)。

## 決定済み前提 (packet v1.1 / charter, LOCKED)
α-6D residual (position-only, HIGH5 moot) / obs 57D (v2.1) / horizon 900 / Q7 draw = DR-support 除外 (EMPTY provisional) / Q3 = reach-terminate + wrist-proxy / T3 bar = ≥70% ∧ baseline 0.716 band 超え / cuda:0 canonical / FON_V1 (W0E_F1B_SNAPDOWN=1) env pin 承継 / 分子 = strict_v2 predicate-complete 承継。

## gates (L3, §運用2)
[DESIGN-GATE 直交] /reward-design 4 成果物 (artifacts v1.3 を具体 plan に再 discharge, M-A lesson) + /pre-check → [VERIFY] 5体 CC Debate (code 前, %12 checkpoint 後) → [RULE-CHECK] → [CHANGE] build → [層3 機械] → [層5 多視点 幾何/物理/SSOT] → [層2 事後 debate]。

## session_history (詳細は frontmatter)
本 node は %11 (w2:p3 COORD) session に 1:1 binding。build 計画 → %12 checkpoint → 5体 [VERIFY] → build の順で進行。
