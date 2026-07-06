---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-envcore
node_name: "P2 whole-route env-core (RL env class 骨格)"
goal: "spec v1.5 §4 に基づく whole-route C1→C2 RL env-core を build する — obs 60D (v1.5a) / action α-6D residual (非累積 Δ, DOF = (b′) phase-conditional structural projection v1.5b) / reward sparse-primary predicate (G1-G6 latched-monotonic) / termination (horizon 900 + terminates) / guards ((b′) span projection: dual-grip hard-project + 再把持窓 per-arm)。staged build chain の第 1 component (env-core → route-executor → oracle → OG → trainer)。"
goal_verification: |
  env-core smoke DoD 8 項 PASS (spec v1.5 §4): ①throughput ≥9.7 実効 fps ②device parity (per-phase predicate-fire + 終端 verdict 一致, cuda:0-only pin は FAIL 分岐) ③cg-GPU whole-route screen (全 phase finite + nacon engage + no nefc overflow) ④horizon 実測 max-of-81 (P3 piggyback) ⑤Δ=const drift-zero (=0.0 EXACT) ⑥predicate unit-test @cuda:0 (6 phase 全 fire + no-re-fire + guards-quiet) ⑦handover-fidelity (route-executor 接続後、qpos/qvel L∞) ⑧corner-miss 分布 (P3 grid 供給済)。
  現況 (2026-07-06 14:56): 5体 [VERIFY] 全完了 → CC1 **DECIDE = FAIL/BLOCK** (1 CRIT + 9 HIGH ACCEPTed; NHA=CHANGE_JUSTIFIED=方向妥当 fix-not-reject, core (b′) algebra 全 agent CLEAN)。⭐**CRITICAL (CC2-CH1, §運用28 confirmed strict_v2:108) = G6 が c1_retained_final 欠 = §運用29 C1-retention 分子 hole 再現** (DoD⑨ は residual≡0 base C1=81/81 で盲 → GPU 後顕在)。**Rs-owned escalate (%12/Rs)**: CC2-CH1 CRIT (G6+=c1_retained_final + C1-retention obs dim [Rs 60D→62D] + adversarial-rollout DoD) / CC2-CH2 (C2 leg=c2_seated_honest) / CC2-CH3 (ordered phase pointer) / CC4-CH1 (phase-conditioned σ — NEW-B fold algebra-REFUTED) / CC4-CH2 (corner p_hit core-viability)。**impl fold**: CC3-CH1/CH2 (achieved-span 言辞/G4 boundary symmetric) / CC5-1/CH2 (92.4mm home/stub single-source) / CC4-CH3 + 12 MED/LOW。**当方 error own**: build plan line17 reach-fail staleness + 「clean」over-claim + NEW-B insufficient。次 = %12 verify DECIDE → Rs-owned 5 disposition → 全 fold → build plan revise → 5体 round-2/targeted re-verify → build。code 未着手 (0-commit, locked runner 不触)。tally=scratchpad/verify_5tai_tally.md。
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2
children_nodes: []
dependencies:
  precedent:
    - "W0-e F-1b snap-down COMMITTED 6808964dc3 (official SR 0.716=58/81; env pin W0E_F1B_SNAPDOWN=1 = env-core 0.716 再現条件 / cuda:0 canonical 承継)"
    - "P2 spec v1.5 + artifacts v1.3 + packet v1.1 = Rs W0-a′ 一括承認 (state.md b7d7857dfc, 2026-07-06 10:1x)"
  blocker: []
created: 2026-07-06T10:35:32+09:00
last_updated: 2026-07-06T14:56:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-06 10:27 lead %12 (RS-TECH-LEAD, w2:p4): P2 env-core build charter (Rs W0-a′ packet v1.1 一括承認 b7d7857dfc, staged charter 授権) → %11 (COORD, w2:p3) §運用4 grounding (spec v1.5 118L + packet v1.1 98L) + [TASK]/[L-TRIAGE]=L3 HIGH → %12 APPROVE (10:33, 子 node 作成承認 = Rs packet §8-3 + [DEFINE]) → %11 本 state.md 作成 (1:1 binding = %11 session) → build 計画 起草へ。p6 に direct ping (parent children_nodes + manifest 反映)。"
  - "2026-07-06 10:5x-13:06 [DESIGN-GATE] iterate: /reward-design PASS + /pre-check 1走目 BLOCK (10-issue) → C1 fact-find (crossing-x ABSENT 決定的) → Rs obs 60D (v1.5a, 11:20 bb9e3666be) → 2走目 RE-RUN (9/10 CLOSED) → N1 CRITICAL (FOUNDATIONAL span #2, common-mode-preserves-span 論理無効) → BLOCKED_FOR_USER → %12 推奨 (b′) → **Rs「推奨で」= (b′) 確定 (spec v1.5b, 13:01 189c7c5bf9)**。BLOCKED 解除。N2-N6 %12 fold 承認。次 = (b′)+N2-N6 fold → /pre-check 3走目 → checkpoint。"
  - "2026-07-06 13:06-13:33 (b′)+N2-N6 fold + /reward-design PASS ((b′) delta = 全 G reachable, projection algebra sound) → /pre-check 3走目 = **BLOCK** (1 CRIT ISSUE-1 window-gaps-G3-C1-seat + 4 HIGH [ISSUE-2 PPO会計 / 3 DoD⑩ achieved-span / 4 DoD⑨ port-vs-online / 5 transit-reach obs] + 3 MED; ⭐core (b′) algebra CONFIRMED sound by verifier)。impl fold (ISSUE-1/3/4/6/7/8a) DONE (build plan §9)。design-level ISSUE-2/5/8b = %12+Rs escalate。%12 報告 → disposition → 4走目 待ち。"
  - "2026-07-06 13:42-13:43 %12 design-level disposition (spec v1.5c da9d94b849, Rs ask 不要): ISSUE-2 pushforward-log-prob (当方推奨採用) / ISSUE-5 [16:19] semantics pin = 新 obs なし + conditioning DoD⑪ (evidence-gated +3D fallback) / ISSUE-8b asymmetric transit 採用 / ISSUE-1 spec:75 grip-schedule 窓訂正。全 fold DONE (§9)。GO → /pre-check 4走目 (全込) 実行。"
  - "2026-07-06 13:43-13:58 /pre-check 4走目 (fix 検証) = **WARN** (7 disposition RESOLVED, design-CRIT 残無; 2 HIGH: NEW-A ISSUE-1 gate ∧both-contact fail-OPEN → gate=grip-schedule ALONE fold + spec amendment① 訂正要 / NEW-E spec §4 body stale [line 75 window/69 termination/74 DoD] = %12 reconcile 要; 3 MED NEW-B entropy / NEW-C flag=operator / NEW-D arm-role + ISSUE-5 FP32→normalization reframe)。当方 fold DONE (§10)。%12 に spec 2 点要請 → 5走目 → checkpoint。"
  - "2026-07-06 14:05-14:16 %12 spec v1.5d (bfeedea7d8, gate schedule-ALONE + §4 line 69/74/75 reconcile) → /pre-check 5走目 = **WARN (near-PASS)**: NEW-A/B/C/D/ISSUE-5 全 CLOSED, design-CRIT・HIGH 残無。WARN driver = NEW-E 残 2 spec line (67 reward terminate 括弧 / 68 success 全-phase deadlock-echo, §運用28 確認 spec 側のみ) + NEW-G(window=release-COMPLETE fold)/NEW-H(evidence-gated carry)。verifier: line 67/68 close + NEW-G/H carry → PASS build-ready。%12 に 67/68 要請 → on-disk 照合 → checkpoint。"
  - "2026-07-06 14:20-14:21 %12 spec v1.5e (5a01164793) line 67/68 correct reconcile (§運用28 on-disk clean 照合) → verifier conditional-PASS 3 条件 全充足 → ✅ **[DESIGN-GATE] = PASS** (/reward-design + /pre-check, 5走目収束, 全 disposition CLOSED, design-CRIT・HIGH 残無)。正式 %12 checkpoint 提出 (code-前, design summary + grounding v1.5e + 5体精査点)。次 = %12 承認 → 5体 [VERIFY]。"
  - "2026-07-06 14:24 %12 checkpoint = **APPROVE** (修正1 [58:60] slice 表記 → build plan obs 契約 反映)。**5体 [VERIFY] spawn (当方 CC1)**: CC2 correctness / CC3 physics / CC4 RL / CC5 SSOT / CC6 NHA 並列独立。PROPOSE = build plan §1-11 + spec v1.5e + KNOWN_ALTERNATIVES + §6 focus。→ CHALLENGE/NHA → CC1 REBUT_OR_ACCEPT + DECIDE → %12 verify → build。"
  - "2026-07-06 14:24-14:56 5体 [VERIFY] 全完了 → CC1 **DECIDE = FAIL/BLOCK** (1 CRIT CC2-CH1 §運用29 C1-retention hole [§運用28 confirm strict_v2:108] + 9 HIGH; NHA=CHANGE_JUSTIFIED 方向妥当)。5走 /pre-check 見逃し CRITICAL 捕捉 = 5体 value 実証 + NEW-B fold refuted (CC4-CH1 algebra: Var(common)=Var(diff))。Rs-owned 5 (CC2-CH1 obs+success / CC2-CH2/CH3 / CC4-CH1 σ / CC4-CH2 viability) escalate %12/Rs; impl fold 5 HIGH (CC3-CH1/CH2, CC5-1/CH2, CC4-CH3) + 12 MED/LOW。当方 error own (line17 reach-fail staleness + NEW-B insufficient)。DECIDE report → %12 verify。次 = Rs disposition → fold → re-verify → build。tally=scratchpad。"
---

# P2 whole-route env-core (T-ROOT-optE-route-dapg-C1C2-P2-envcore) — IN_PROGRESS

**Rs 承認履歴:** 2026-07-06 10:1x「W0-a′ packet v1.1 一括承認」(spec v1.5 + artifacts v1.3 を P2 設計基底採択 + §8 staged build charter 発行授権、state.md b7d7857dfc)。本 node = staged charter 第 1 component (env-core)。

RESOLVED (2026-07-06 13:01 Rs「推奨で」= (b′) 確定, spec v1.5b amendment commit 189c7c5bf9; BLOCKED_FOR_USER 解除 = Rs GO 済): env-core action DOF = **(b′) phase-conditional structural projection**。INVARIANT#2 (88mm span) は「適用場所で構造 enforce」。α-6D residual 契約維持。
**Rs 決定 (b′) 詳細 (spec v1.5b:123 忠実):**
  - dual-grip phase (span-guard 窓 {G1-G2}∪{G4-G6}): Δ を common-mode 部分空間へ **hard-project** (INV#2 span = 構造 enforcement, 検知でなく)。
  - 非 dual-grip 再把持窓 (phase 10-11): per-arm 許容 (span task 非 invariant ~160mm + N6 0.9mm reach fragility の補正が要る場所)。
  - differential-drift regression = DoD 追加 (N1↔N6 同 window 整合)。
[build 進行可 (Rs GO)。次 = (b′) fold + N2-N6 fold → /reward-design + /pre-check 3走目 → PASS → 正式 %12 checkpoint → 5体 [VERIFY] → build。action-path 実装は checkpoint+5体 PASS 後。]

## goal / means / status
- **goal (検証可能):** 上 frontmatter goal_verification の smoke DoD 8 項 PASS で env-core を verified とする。
- **means (leaf action):** 新規 env class ファイル群 (≤800 行 diff, 個別 L3 chain) を build。obs 57D / α-6D residual 非累積 (`Δ=const→drift=0` regression) / reward sparse-primary G1-G6 predicate (latched-monotonic, fire-once, never-revoked; phase one-hot=argmax(earned)) / termination (horizon 900, terminates=explosion/drop/span逸脱/reach-fail, time_outs=timeout純度のみ) / guards (action-path per-arm clamp 禁止=common-mode only [INV#2 as-executed 保護] / span 監視 dual-grip phase のみ {G1-G2窓}∪{G4-G6窓} informative-tier / mujoco-assert)。phase-clock の state-bank 機構は route-executor component (次段) と接続 — env-core は interface/stub。
- **status:** IN_PROGRESS (build 計画 起草段, code 未着手)。

## 決定済み前提 (packet v1.1 / charter, LOCKED)
α-6D residual (position-only, HIGH5 moot; action DOF = (b′) phase-conditional structural projection, spec v1.5b) / obs 60D (v1.5a; 57D + [57]crossing-x dev + [58:60]axis-resolved seat) / horizon 900 / Q7 draw = DR-support 除外 (EMPTY provisional) / Q3 = reach-terminate + wrist-proxy / T3 bar = ≥70% ∧ baseline 0.716 band 超え / cuda:0 canonical / FON_V1 (W0E_F1B_SNAPDOWN=1) env pin 承継 / 分子 = strict_v2 predicate-complete 承継。

## gates (L3, §運用2)
[DESIGN-GATE 直交] /reward-design 4 成果物 (artifacts v1.3 を具体 plan に再 discharge, M-A lesson) + /pre-check → [VERIFY] 5体 CC Debate (code 前, %12 checkpoint 後) → [RULE-CHECK] → [CHANGE] build → [層3 機械] → [層5 多視点 幾何/物理/SSOT] → [層2 事後 debate]。

## session_history (詳細は frontmatter)
本 node は %11 (w2:p3 COORD) session に 1:1 binding。build 計画 → %12 checkpoint → 5体 [VERIFY] → build の順で進行。
