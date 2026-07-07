# BUILD PLAN — route-executor Layer B (env-integration) — %11 COORD (w2:p3)

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec (IN_PROGRESS) — charter %12, D-1=C.
**rev:** v0.1 DRAFT (P2, 2026-07-07 15:0x). ⚠ **PLANNING artifact only — NO build/GPU (Rs/%12 HOLD).** draft → %12 design-gate + 5体 [VERIFY] (L3) → PASS で %12 が build 授権.
**precedent:** Layer-A byte-repro COMPLETE (81/81 byte-id, commit 50f877c7f5) — run_route faithful extraction PROVEN. This plan wires the extracted engine into the env substrate (Layer B = substrate-transfer, non-conservative, bar = measured).

---

## §0. Grounding (anchor set, §運用4 hard gate — read + cite)
| source | ref | use |
|---|---|---|
| LEDGER | 00-DESIGN-STATUS-LEDGER.md route-executor row (Layer-A PASS marker 2b7c4d6b23) | 成否 SSOT |
| node state.md | 14:20 NEXT + goal_verification DoD | Layer-B scope + DoD |
| charter | ROUTE_EXECUTOR_CHARTER_SCOPING_RSTECHLEAD_20260706.md §4 (8-carry) + §5 (stub 契約 v1) | owns/defer + contract |
| Layer-A build plan | BUILD_PLAN_ROUTEEXEC_COORD_20260707.md §5 (execution model) + §10.1 (grasp_actuation) + §13.1 (3-pattern write-site) | Layer-B design basis |
| env-core 8-carry | env-core node state.md:64-71 | hand-off carry |
| fresh-cat (§運用16) | newton_route_env.py / route_env_config.py / route_executor.py (RouteExecutor:2972) | integration target |

---

## §1. [TASK] / [L-TRIAGE] = L3 (%12 verified §運用28)
- newton_route_env.py CORE edit + keywords {env/newton/ik/solver/phase/reset/grasp_actuation} + >200L / ≥3 files → L3.
- **invariant-PRESERVING** (§0 不変前提 DUAL-ARM / 88mm / DiffIK / コ gripper / no-kinematic-trick 不変更): grasp_actuation=True activates the PROVEN model-level POSITION servo (§10.1, %12-verified) — NOT a kinematic pin, NOT a control-method change. → high-care L3, NOT immediate-STOP.

---

## §2. Scope — components 1-8 (built vs new)
**BUILT (Layer-A + foundation, do NOT rebuild):** run_route (byte-repro 81/81 PASS) / AR-reuse write-site machinery (apply_arm_only_write_broadcast/perworld, set_gripper_target, build_perworld_index_maps, servo_seed_assert, apply_banked_restore) unit-PASS / G4/G5 asserts / physics+IK substrate / _GRIPPER_COORDS_LOCAL SSOT / RouteExecutor.__init__(:2987) + reset_to_phase(:3007 banked-restore) / route_env_config RouteInterfaceV1 + C2 constants + recorded_replay mode / env-core COMPLETE (env consumes the interface: _pull_route:1091 → _apply_actions_batch:676 NON-accumulating base+residual + _route_grip/_route_is_dual).

| # | component | file | new LOC (est) | notes |
|---|---|---|---|---|
| 1 | **step_target facade** (SINGLE-SOURCE, §6) | route_executor.py (:3026 impl) | ~60-140 | THE crux gap (NotImplementedError). recorded_replay primary + live design-question |
| 2 | **RouteExecutor env-wiring** (replace NominalRouteStub:309, flag-gated) + state_bank build | newton_route_env.py | ~40-90 | flag = `route_executor_impl` default stub (byte-preserve) |
| 3 | **grasp_actuation flag-flip** (:338 default False → flag) | newton_route_env.py | ~10-25 | §10.1; OFF = env-core byte-identity (constraint 2) |
| 4 | **3-pattern write-site** (:387 broadcast / :738 per-world / :617 banked-restore) use AR machinery | newton_route_env.py | ~30-70 | §13.1; gripper coords excluded per-step, banked-restore at reset |
| 5 | **real C2 groove scene** (physical C2 clip build; constants exist) | newton_route_env.py / route_env_config.py | ~20-60 | §9; env-core built C2 = geometric-proxy → route needs physical (design-question) |
| 6 | **§9 static drift tripwire unstub** (no-GPU) | test_routeexec_byte_repro.py:265 | ~40-80 | golden-hash vs monolith slice test:3692-5765 F11-reverse; layer-3 mechanical |
| 7 | **SRG measure-first leg** (4-substep grip efficacy, GPU-gated HARD decision-gate) | scripts/ (measure harness) | ~80-150 | §7; Stage-B gate BEFORE grip commit |
| 8 | **DoD Layer-B validation** (⑨b/⑥/実grip/C2-seating video) | env run + video | — | Stage-B, GPU |

**LOC est (core, Stage-A no-GPU):** ~150-450 touched. **Stage-B = validation runs (no new engine LOC beyond measure harness).**

---

## §3. DoD (Layer-B, charter §1 mapping; §運用29 predicate-completeness)
分子 conjoin = **strict_v2 (C1-retention leg ∧ C2-seat leg)**. trainer policy 学習成果 = out of node scope.
- **⑦ handover-fidelity** (reset_to_phase state-bank): qpos/qvel L∞ ≤ 1mm / 1mm/s (mechanism BUILT :3007; needs state_bank + 1-step-after-reset divergence test). **Stage-A verifiable (no live rollout).**
- **⑨b online-numerator**: residual≡0 × 81 live (env 4-substep + servo grip) → strict_v2 実測 (58/81 と**仮定禁止**, %12 Q3; substrate-transfer divergence = finding). **Stage-B GPU.**
- **⑥ 6-phase full-fire live** (実 grip で cable carried): all 6 phases fire, cable retained whole-route. **Stage-B GPU + video.**
- **実 grip** (real grip force at 4-substep servo): SRG measure-first (§7) is the gate. **Stage-B GPU.**
- **C2-seating 動画 gate** (Rs 約束, 実 C2 groove scene): §運用14 video leg. **Stage-B GPU + video.**
- **⑬ enabler** (recorded-target-replay + C1-escape non-vacuous cell): recorded_replay path (§6). VERDICT = trainer defer.

⚠ **conservatism (GROVE v1.1):** Layer-B = substrate-transfer, **non-conservative, bar = measured** (58/81 is the Layer-A byte-golden, NOT a Layer-B target). divergence itself is the finding.

---

## §4. ⭐ Design constraints (%12 mandatory, 2026-07-07 15:03 — plan-binding)
1. **step_target SINGLE-SOURCE with run_route** (divergent reimpl 禁止). recorded_replay + live BOTH byte-consistent with the proven route = crux 設計不変式 (a 2nd drifting route computation = 先祖返り risk). See §6.
2. **grasp_actuation flag-flip OFF = env-core byte-identity 完全保存** (flag-gated, default path 不触). Verified by B⑨a′ re-regression (legacy-config == env-core 25/81 EXACT).
3. **SRG measure-first = HARD decision-gate** (§7): 4-substep grip 効力 PASS してから grip approach commit. 不足 → **surface as decision point, silent 進行禁止, 閾値緩和で誤魔化さない** (§運用 gate-FAIL fix-first).
4. **stage separation** (§5): no-GPU build (byte/static-verifiable) vs GPU-gated validation. separate gate chains.
5. **design-gate skills by content** (§11): /force-design (servo/grip) + /geometric-design (C2 groove scene) + /reward-design (if ⑨b/success-def touched). compound → all.
6. **PLANNING artifact only** — no build until gate PASS + %12 授権.

---

## §5. ⭐ Stage-separated gate chain
### Stage A — no-GPU build (byte/static-verifiable, env-core non-perturbing)
components 1-6 (step_target facade + env-wiring flag-gated + grasp_actuation flag-flip default-off + 3-pattern write-site + C2 scene flag-gated + §9 tripwire unstub).
- gate: [DEFINE done] → **design-gate** (§11 skills) → **5体 [VERIFY] (L3)** → %12 授権 → **BUILD** → **static/byte verify**: (i) flag-OFF byte-identity (env-core 25/81 EXACT re-regression, B⑨a′) (ii) §9 static tripwire PASS (golden-hash == slice) (iii) recorded_replay step_target == run_route recording byte-consistent (unit).
- ⚠ Stage-A is env-core NON-perturbing (all flag-gated default-off) → low-risk, no GPU training. full production-launch-gate 不要 (Layer-A precedent).

### Stage B — GPU-gated validation (substrate-transfer, non-conservative)
components 7-8 (SRG measure-first + live DoD ⑥/実grip/⑨b/C2-seating video).
- gate: Stage-A GREEN → **SRG measure-first sub-gate (§7, HARD decision-gate)** → if PASS: live DoD runs (⑨b 81-live / ⑥ full-fire / C2-seating video) → if any run is HIGH-COST (GPU ≥10h or production-scale) → **/production-launch-gate** (§運用2 HIGH-COST-GATE).
- ⚠ SRG measure-first FAIL → STOP, surface decision point (grip approach re-design, NOT threshold-relax). Rs-level if grip infeasible at 4-substep.

---

## §6. step_target facade design (SINGLE-SOURCE, constraint 1)
- **PRIMARY = recorded_replay**: replay run_route's recorded per-step ee_tgt (route_demo_raw.npz `ee_tgt_pos_l/r`, frame→RL-step via cadence 10; 7707 frames → 771 steps, pad to horizon 900). **Single-source by construction** (targets ARE run_route's output; byte-consistent). Powers ⑨b (residual≡0 = pure replay) + ⑬ enabler.
- **per-cell offset**: each of 81 DR offsets has its own run_route recording (Layer-A grid already produced them). recorded_replay indexes the per-cell recording.
- **live (design-question, surface to 5体)**: on-the-fly re-derivation (no pre-recording) risks divergent reimpl (constraint 1 violation). **PROPOSAL: defer live to a shared target-computation extracted from run_route (NOT reimpl), OR keep recorded_replay-only for this node** (⑨b needs only replay). 5体 to rule on whether live is in-scope or deferred.
- packet: (target_6d [R_xyz,L_xyz abs, fork-(iv) non-累積], phase_id [base G1-G6 clock], grip_2 [per-arm], is_dual). env consumes at _apply_actions_batch:676 (already wired).

---

## §7. SRG measure-first (HARD decision-gate, constraint 3)
- **premise risk**: grasp_actuation=True servo is proven at SIM_SUBSTEPS=10 (monolith); env = RL_SIM_SUBSTEPS=4 (2.5× coarser). 10-substep grip efficacy ≠ 4-substep guaranteed (stiff cable contact + PD close dynamics).
- **measure**: run the env grip-close (grasp_actuation=True, 4-substep) on a nominal cell, measure grip efficacy (cable retained through the route? grip force? throat closure? slip-onset over time). video leg (§運用14, claw-zoom + throat_frac time-series, [[feedback-video-detect-intra-finger-cable-slip]]).
- **decision-gate (HARD)**: grip efficacy PASS (cable carried whole-route, no slip) → commit the grip approach → proceed to live DoD. **FAIL → STOP, surface as decision point** (candidate fixes: substep 4→N [Rs-level, campaign-affecting], PD gain re-design [/force-design], contact stiffness). NO threshold-relaxation, NO silent progress.
- conservatism direction: measure on the env substrate = the REAL bar (non-conservative measurement). grip verdict = human-GT ([[feedback-grasp-verdict-numeric-and-video-analyst-both-unreliable-human-ground-truth]]).

---

## §8. state_bank + reset_to_phase (⑦, mechanism BUILT)
- RouteExecutor.reset_to_phase(:3007) restores banked arm + all-16 gripper joint_q/qd + banked grip target (apply_banked_restore) from `_state_bank[k]`. **NEW = build the state_bank** = phase-k banked states (qpos/qvel + grip target) extracted from a run_route recording at phase boundaries.
- ⑦ DoD: reset_to_phase(k) qpos/qvel L∞ ≤ 1mm/1mm/s vs the recorded phase-k state + 1-step-after-reset divergence test (5体 CRIT4 precedent). **Stage-A verifiable (no live rollout).**
- SCALAR k (per-world curriculum start-mix deferred to trainer, §13.2 F14/F15).

---

## §9. real C2 groove scene (component 5)
- constants exist (route_env_config: ROUTE_C2_XY=(0.40,0.000) / ROUTE_GROOVE_Z=0.829 / C2 tolerances). env-core built C2 as geometric-proxy (docstring :50 "route is STUB").
- NEW = physical C2 clip build (byte-repro grid used S13_ROUTE_C2=1 + CLIP2=1 in build_scene → real C2). **design-question (5体)**: does build_multiworld_scene need C2-clip flags, and is env-core byte-preserved when off? /geometric-design (C2 groove scene, table-void×clip parity).

---

## §10. §9 static drift tripwire unstub (component 6, no-GPU)
- current: test_routeexec_byte_repro.py:265 static_drift_tripwire() = stub (TODO :277).
- unstub: compute sha256 of the monolith slice test_newton_clip_routing.py:3692-5765, reverse the C2-F11 delta (monkeypatch install/ik_solve_fn), compare to run_route's `_ROUTE_MONOLITH_GOLDEN_SHA256` (5a47dacf..). layer-3 mechanical (no-GPU, deterministic, test_route_geometry_sync.py pattern). Catches route_executor drift from the locked monolith cheaply (before the GPU grid).

---

## §11. design-gate skills (constraint 5, by content)
- **/force-design**: grip servo (grasp_actuation PD close) + 4-substep contact dynamics (SRG). REQUIRED.
- **/geometric-design**: real C2 groove scene (C2 clip build, table-void×clip parity). REQUIRED.
- **/reward-design**: ONLY if ⑨b success-def / predicate touched (route/predicate 不変 expected → likely skip; confirm at design-gate). 
- compound → load all applicable.

---

## §12. Open design questions (5体 / design-gate 対象)
1. step_target live mode: in-scope (shared target-computation extraction) or recorded_replay-only for this node? (§6)
2. C2 groove scene: build_multiworld_scene C2-clip flag + env-core byte-preserve? (§9)
3. state_bank source: run_route recording phase-boundary extraction — which frames = phase-k boundaries? (§8)
4. SRG threshold: what grip-efficacy criterion = PASS (cable-carried whole-route + no slip; human-GT)? (§7)
5. recorded_replay per-cell: 81 recordings (955MB) reuse vs on-demand re-record? (§6)

---

## §13. Risks / conservatism carries
- **substrate-transfer risk (material, %12→Rs surfaced)**: env 4-substep + servo ≠ monolith 10-substep. Layer-B = measured, non-conservative. SRG measure-first (§7) is the gate; substep decision = Rs-level post-data.
- **grip at 4-substep = premise risk** (§7 SRG). silent-cap 禁止.
- **step_target divergence = 先祖返り risk** (constraint 1); recorded_replay single-source mitigates.
- **flag-off byte-preserve** (constraint 2): B⑨a′ re-regression guards.

---
*%11 COORD (w2:p3) draft v0.1 2026-07-07 15:0x. PLANNING only. → %12 design-gate + 5体 [VERIFY] (L3) → build 授権.*
