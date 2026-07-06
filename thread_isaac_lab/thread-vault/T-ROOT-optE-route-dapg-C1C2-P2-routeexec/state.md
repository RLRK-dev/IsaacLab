---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-routeexec
node_name: "P2 whole-route route-executor (実 route engine + state-bank)"
goal: "env-core が stub interface で受けている route を、locked `_run_mujoco_grasp_route` (test_newton_clip_routing.py:3692, 0.716 MOTION STANDARD, ANTI-REVERT Rs-LOCKED) を reference oracle とする実 route engine に置換する。D-1=C 採択 (Rs 2026-07-06 23:5x): locked file 不触・faithful 抽出 → 新 route_executor module + byte-repro guard。staged build chain 第 2 component (env-core [COMPLETE] → route-executor → oracle → OG → trainer)。"
goal_verification: |
  route-executor DoD (charter scoping §1、byte-repro が全項の前提 guard):
  ① byte-repro: 抽出 route で canonical 81-grid → strict_v2 58/81 EXACT (env-core ⑨a′ recorded-state 25/81 proxy を live 58/81 へ)
  ② ⑦ handover-fidelity: reset_to_phase(k) の qpos/qvel L∞ ≤ 提案 1mm / 1mm/s
  ③ ⑨b online-numerator: residual≡0 × 81 live → 58/81 (live earned-clock + contact + physics)
  ④ ⑥ 6-phase full-fire live (実 grip で cable carried)
  ⑤ 58/81 wall/spacer exact predicate (mjModel geom introspection、center-dist≤3.5mm proxy → wall-dist≤0.5mm spacer-excluded)
  ⑥ C2-seating 動画 gate (Rs 約束済、実 C2 groove scene)
  ⑦ CABLE_XY_OFFSET per-cell wiring
  ⑧ ⑬ enabler のみ (recorded-target-replay stub upgrade + C1-escape non-vacuous cell 供給; ⑬-VERDICT は D-2=trainer 段 defer)
  分子 conjoin = strict_v2 (C1-retention + C2-seat 両 leg)。trainer 段の policy 学習成果は本 node scope 外。
  現況 (2026-07-06 23:5x): [DEFINE]/[L-TRIAGE]=L3/scope DONE (charter scoping doc committed) + D-1=C / D-2=trainer Rs 決定済。次 = build plan 起草 (%11 再 bind) → design-gate → 5体 [VERIFY] → build。code 未着手。
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2
children_nodes: []
dependencies:
  precedent:
    - "env-core node T-ROOT-optE-route-dapg-C1C2-P2-envcore = COMPLETE (2026-07-06 23:11, Rs 動画 gate PASS; stub 契約 v1 + 8 blocking LOUD-CARRY を本 node へ hand-off)"
    - "P2 spec v1.5h + build plan (BUILD_PLAN_ENVCORE_COORD §6 stub 契約) + Rs W0-a′ v1.1 一括承認 (staged charter 授権, b7d7857dfc)"
    - "D-1=C (新 module 抽出+byte-repro) / D-2=trainer (⑬ VERDICT defer) = Rs 決定 2026-07-06 23:5x"
  blocker: []
created: 2026-07-06T23:58:00+09:00
last_updated: 2026-07-07T00:12:15+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-07 00:0x-00:12 %11 (COORD, w2:p3) 再 bind: /clear 後 role re-derive (peek: w2:p3=COORD) → charter 受領 → §運用4 anchor set grounding (LEDGER:47 / charter §1/§4/§5/§6 / spec v1.5h §2-F2/§5/§7:102 / env-core build plan §6/§12 / env-core state.md:62-71 8-carry / locked runner _run_mujoco_grasp_route:3692 [fn 3692-6167, 2476L, ANTI-REVERT :5128/:5148/:5290] 構造実読 / ik_move_both:1958 共有 helper / NominalRouteStub:178 integration point / SOMA:37/:717) → [TASK]/[L-TRIAGE]=L3 confirm (charter §3 と独立再導出 concur; FOUNDATIONAL INVARIANT 不変=byte-repro 保存=即STOP非該当だが high-care) → **build plan 起草 (BUILD_PLAN_ROUTEEXEC_COORD_20260707.md, PAPER-ONLY)**: 抽出アーキテクチャ (monolith→step_target/reset_to_phase 分離表, ik_move_both/geom=import 再利用, inline target[W0-e/seat k8/ANTI-REVERT]=抽出) + DoD ①-⑧ (byte-repro 58/81 EXACT=PRIMARY) + byte-repro regression harness §4 (locked oracle↔RouteExecutor 81-grid per-cell EXACT, cuda:0 canonical, namesake guard) + stub 契約 v1 実装方針 §5 (RouteExecutor(rc.RouteInterfaceV1) 差し替え) + LOC 見込 ~780-1190 (core ≤800 + byte-repro test 分離) + open items 5 + risks。task-start SHA f0bd54992c。次 = %12 checkpoint ping → [DESIGN-GATE] (/geometric-design C2 + /reward-design 軽 + /pre-check)。"
  - "2026-07-06 23:2x-23:5x lead %12 (RS-TECH-LEAD, w2:p4): env-core COMPLETE 後、route-executor charter 起票。§運用4 anchor set 接地 (LEDGER LADDER v2 / spec v1.5h §7:102+§2-F2+§5 / build plan §6+§12 CC5-2 / env-core node state.md:62-71 8-carry / locked runner test_newton_clip_routing.py:3692 [ANTI-REVERT Rs-LOCKED] / SOMA)。charter scoping doc = ROUTE_EXECUTOR_CHARTER_SCOPING_RSTECHLEAD_20260706.md (paper-only, committed): [DEFINE] goal/means/success + [TASK] node proposal + [L-TRIAGE]=L3 (FOUNDATIONAL INVARIANT は byte-repro で保存=即STOP非該当だが high-care) + scope partition (8 carry のうち 7+⑬enabler を owns / oracle・OG・trainer defer) + stub 契約 v1 + §6 D-1/D-2 fork。**Rs 決定 23:5x: D-1=C (locked file 不触・faithful 抽出→新 route_executor module + byte-repro regression [cuda:0 canonical 58/81 EXACT] = 先祖返り guard) / D-2=trainer 段実 policy (route-executor=⑬ enabler のみ)**。→ 本 node 作成 (§3.1、staged chain authorized + Rs charter engage)。次 = %11 再 bind → build plan 起草 → design-gate → 5体 [VERIFY] → build。"
---

## goal / means / status
- **goal (検証可能):** frontmatter goal_verification の DoD ①-⑧ で route-executor を verified とする。核心 = byte-repro (0.716 canonical を新 module で live 再現) + ⑦ handover-fidelity + ⑨b online-numerator。
- **means (leaf action):** D-1=C — locked `_run_mujoco_grasp_route` (reference oracle、不触) の route ロジックを新 `route_executor` module (production engine) へ faithful 抽出。2476L monolith を per-step target-computation (step_target) + phase-k state-bank driver (reset_to_phase) に分解。stub 契約 v1 (reset_to_phase / step_target→(target_6d,phase_id,grip_cmd) / per-arm grip 2-vec / is_dual_grip boolean / recorded-target-replay mode) + 実 C2 groove scene + 実 grip force。byte-repro regression (locked↔module, cuda:0 canonical 58/81 EXACT) が全 DoD 前提 + 先祖返り guard。
- **status:** IN_PROGRESS (charter [DEFINE]/[L-TRIAGE]/scope + D-1/D-2 Rs 決定 DONE、build plan 起草へ)。

## 決定済み前提 (charter scoping + Rs D-1/D-2, LOCKED)
- D-1=C: locked file 不触・新 route_executor module 抽出 + byte-repro guard。
- D-2=trainer: ⑬ VERDICT は trainer 段実 policy、route-executor は enabler のみ。
- stub 契約 v1 = build plan §6 (env-core が既に期待)。
- byte-repro 判定 = cuda:0 canonical のみ ([[project-canonical-route-device-fragile-cpu-vs-cuda]])。
- namesake hazard: production `_run_mujoco_grasp_route` を cite、legacy 同名関数と混同しない ([[reference-test-newton-legacy-vs-production-route-namesake-functions]])。
- 上位 goal に SR/学習成果 claim を出さない (trainer 段、over-claim 禁止)。

## route-executor が owns する 8 blocking carry (env-core hand-off)
env-core node state.md:64-71 の 8 項。1-7 = route-executor discharge、8 = enabler のみ (VERDICT trainer):
1. 58/81 wall/spacer exact-split (mjModel geom introspection)
2. ⑥ 6-phase full-fire live (実 grip)
3. CABLE_XY_OFFSET per-cell wiring
4. real grip force
5. ⑨b online-numerator (residual≡0×81 live→58/81)
6. ⑦ handover-fidelity (reset_to_phase state-bank)
7. C2 groove + C2-seating 動画
8. ⑬ enabler (recorded-target-replay + C1-escape cell; VERDICT=trainer D-2)
