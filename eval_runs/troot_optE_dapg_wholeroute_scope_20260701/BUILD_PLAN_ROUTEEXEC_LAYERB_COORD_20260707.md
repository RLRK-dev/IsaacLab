# BUILD PLAN — route-executor Layer B (env-integration) — %11 COORD (w2:p3)

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec (IN_PROGRESS) — charter %12, D-1=C.
**rev:** **v0.2.1** (2026-07-07 15:4x — %12 focused re-gate PASS + ee_pos ESCALATION RESOLVED = (b) ee_pos fork-(iv)-CONSISTENT [%12 grounding route_demo_to_bc.py:287; §運用28 CONCUR]). v0.2 = 39176db220 / v0.1 = a51825bd28. ⚠ **minimal Stage-A {comp1,comp2} BUILD-AUTHORIZED (no-GPU, structural); comp3-8 Stage-B HOLD.** DESIGN-GATE skip-recorded (Stage-A structural: reward/env/success/physics/geometry 不変, flag-gated default-off). → [RULE-CHECK] Tier0 → BUILD (chunk+ast-verify+commit+ping) → §5 STATIC gate → %12 verify.
**precedent:** Layer-A byte-repro COMPLETE (81/81 byte-id, 50f877c7f5) — run_route faithful extraction PROVEN.

---

## §D. v0.2 DELTA summary (for focused re-gate — 7 accepted revision items)
All 5体 = NEEDS-REVISION unanimous, no REBUT (code-verified). Architecture SOUND (D-1=C preserved / grasp_actuation gating byte-clean / strict_v2 no-J-9 / C2 geom X=0.40-solid / cadence-10 sim-time-consistent). Deltas:
1. **[§2/§5] Re-scope Stage-A → MINIMAL {comp1,comp2}** (CC6): comp1 step_target recorded_replay-ONLY (**live CUT/deferred-trainer**, Q1) + comp2 env-wiring + state_bank. Discharges ⑦(a) restore-fidelity (no-GPU) + ⑬-precursor. **comp3-8 DEFER → Stage-B, behind a MINIMAL SRG probe FIRST.** No 4-substep premise bet in Stage-A.
2. **[§6] BAKE step_target packet spec** (CC2, load-bearing): phase_id/grip_2/is_dual from **RECORDED arrays** (verified: phase_id 15 vals [-1,0..8,10..14]→[0,6) map; grip_cmd radians 0-0.7407→{0,1}); **81 single-cell** + `__init__` recording-carry + INIT_XY_NOISE=0; **R-first [R,L] assembly + unit assert** (recorder _STACK_KEYS is [L,R], consumer R-first). ✅ **ee_pos-vs-ee_tgt = RESOLVED = (b) ee_pos fork-(iv)-CONSISTENT** (%12 15:44, §6).
3. **[§3] RESTORE DoD⑤ / carry#1** (wall/spacer EXACT seat-predicate, CC5-CH1, silently dropped in v0.1) + discharge §運用29 leg table. ⑨b strict_v2 uses **EXACT predicate** (wall-dist≤0.5mm spacer-excluded, NOT 3.5mm center proxy → else Layer-A offline 58/81 divergence misread as substrate divergence).
4. **[§7] REVISE SRG** (CC3-CH1 CRITICAL, before Stage-B): **creep-BUDGETED** criterion (no-slip is banked-UNREACHABLE, intrinsic creep 60.4µm/f, 2× false-PASS) + **4-substep creep re-measure FIRST** + tail-cell screening + levers {noslip_iterations 110×/impratio/solver-iters/friction} (substep 4→N LAST, Rs-level) + per-axis conservatism + observable-bound no-silent-cap.
5. **[§5/§10] comp4 write-site FLAG-GATE required** (CC4-C1, else twice-recurring gripper-overwrite defect) + **§9 tripwire 2-leg semantic fix** (CC4-C2, current reverse-F11-on-monolith = tautology) + **B⑨a′ = full-arm_q sha incl gripper** + ⑩ geom assert (CC4-C4).
6. **[§3/§8] Split ⑦** → ⑦(a) restore-L∞ no-GPU **Stage-A** / ⑦(b) 1-step-after-reset grasp_actuation=ON **Stage-B** (CC6; v0.1 "⑦ Stage-A verifiable" was half-true). Stage-A gate-i = STATIC diff not GPU (CC5-CH4).
7. **[§12] Open-Q RESOLVED**: Q1=recorded_replay-only / Q2=C2 pre-resolved (over-solid additive flag-gated) / Q3=state_bank phase-k from recording phase_id per-frame / Q4=creep-budgeted / Q5=reuse+pin 81 recordings now.

---

## §0. Grounding (anchor set, §運用4) — LEDGER route-executor row (Layer-A PASS 2b7c4d6b23) / node state.md 14:20 / charter §4+§5 / Layer-A plan §5+§10.1+§13.1 / env-core 8-carry / fresh-cat newton_route_env.py + route_env_config.py + route_executor.py(:2972) + route_demo_recorder.py + 5体 verdict.

## §1. [TASK]/[L-TRIAGE] = L3 (%12 §運用28 verified) — newton_route_env.py core + {env/newton/ik/reset} keywords + >200L/≥3 files; grasp_actuation invariant-PRESERVING (proven model-servo, NOT kinematic-pin) → high-care L3, NOT immediate-STOP.

## §2. Scope — RE-SCOPED to staged minimal (CC6)
**BUILT (do NOT rebuild):** run_route (byte-repro 81/81) / AR-reuse write-site machinery unit-PASS / G4/G5 asserts / physics+IK substrate / _GRIPPER_COORDS_LOCAL SSOT / RouteExecutor.__init__(:2987) + reset_to_phase(:3007) / route_env_config RouteInterfaceV1 + C2 constants + recorded_replay mode / env-core COMPLETE (consumes interface: _apply_actions_batch:676 base+residual NON-accumulating).

| # | component | stage | file | new LOC | notes |
|---|---|---|---|---|---|
| **1** | **step_target facade (recorded_replay-ONLY)** | **A** | route_executor.py :3026 | ~50-110 | THE crux gap; packet spec §6; live CUT |
| **2** | **env-wiring (RouteExecutor replace stub:309 flag-gated) + state_bank build** | **A** | newton_route_env.py | ~50-110 | ⑦(a) + ⑬-precursor; flag `route_executor_impl` default stub |
| 3 | grasp_actuation flag-flip (:338 default False→flag) | B | newton_route_env.py | ~10-25 | §10.1; grip activation, bundle w/ SRG |
| 4 | 3-pattern write-site **FLAG-GATED** (:387/:738/:617) | B | newton_route_env.py | ~30-70 | CC4-C1: flag-OFF = byte-exact 28-wide write; flag-ON = gripper-excluded + banked-restore |
| 5 | real C2 groove scene (additive flag-gated, over-solid) | B | newton_route_env.py | ~20-60 | Q2 pre-resolved; /geometric-design |
| 6 | §9 static drift tripwire unstub (2-leg) | B | test_routeexec_byte_repro.py:265 | ~50-90 | §10; keep stub non-blocking until leg-(b) specified |
| 7 | **SRG minimal probe FIRST → creep-budgeted measure** | B | scripts/ | ~90-170 | §7; HARD decision-gate BEFORE comp3/4/5 |
| 8 | DoD Layer-B validation (⑨b/⑥/⑦(b)/C2-seating video) | B | env run + video | — | after SRG PASS |

**Stage-A LOC (comp1+2, no-GPU):** ~100-220 touched. Stage-B = SRG-gated.

## §3. DoD (Layer-B; §運用29 leg table RESTORED — CC5-CH2)
**§運用29 leg table (分子 conjoin vs diagnostic):**
| leg | in strict_v2 分子? | source |
|---|---|---|
| 把持 (grasp) | transitive (via C1-retention + C2-seat require held cable) | Stage-B live |
| C1-retention | ✅ conjoined (z_c1<840 ∧ flank<840) | ⑨b predicate |
| C2-seat | ✅ conjoined (**EXACT wall-dist≤0.5mm spacer-excluded** ∧ groove-z≤3mm) | ⑤ predicate |
| crossing/lane | diagnostic only (not conjoined) | lane-cross diag |
trainer policy 学習成果 = out of node scope (over-claim 禁止).

- **⑦(a) restore-fidelity** (Stage-A, no-GPU): reset_to_phase(k) restored qpos/qvel L∞ ≤ 1mm/1mm/s vs recorded phase-k + static (no rollout). **⑦(b)** (Stage-B): 1-step-after-reset divergence (grasp_actuation=ON).
- **⑤ wall/spacer EXACT seat-predicate** (RESTORED, CC5-CH1): mjModel geom introspection, wall-dist≤0.5mm spacer-excluded. ⑨b uses THIS (not 3.5mm center proxy).
- **⑨b online-numerator** (Stage-B): residual≡0 × 81 live (4-substep + servo) → strict_v2 実測 w/ EXACT predicate (58/81 仮定禁止; divergence = finding).
- **⑥ full-fire live** / **実grip** (SRG-gated) / **C2-seating 動画** (§運用14 video) / **⑬ enabler** (recorded_replay; VERDICT trainer-defer). All Stage-B.
⚠ conservatism: Layer-B = substrate-transfer, non-conservative, bar=measured.

## §4. Design constraints (%12 mandatory + verdict) — plan-binding
1. step_target SINGLE-SOURCE with run_route (recorded_replay = run_route's recorded output, byte-consistent; **live CUT** so no 2nd computation, Q1). 2. flag-OFF = env-core byte-identity (comp2/3/4/5 all flag-gated; B⑨a′ full-arm_q sha guards). 3. SRG measure-first HARD gate (§7). 4. stage separation (§5). 5. design-gate skills by content (§11). 6. PLANNING only.

## §5. Stage-separated gate chain (re-scoped)
### Stage A — minimal no-GPU {comp1,comp2}
gate: **focused re-gate (delta-only)** → %12 授権 → BUILD {1,2} → **STATIC verify (gate-i, NOT GPU, CC5-CH4)**: (i) ⑦(a) restore-L∞ ≤1mm/1mm/s (unit, no rollout) (ii) recorded_replay step_target == run_route recording byte-consistent (unit) (iii) **flag-OFF byte-identity**: legacy-config == env-core 25/81 EXACT re-regression + **B⑨a′ = full-arm_q sha incl gripper** (CC4-C4). Stage-A env-core NON-perturbing (all flag-gated default-off) → no GPU training, full PLG 不要.
### Stage B — SRG-gated (comp3-8)
gate: Stage-A GREEN → **MINIMAL SRG probe FIRST** (cheapest C1-grasp+hold go/no-go, single nominal) → creep-budgeted SRG measure (§7) → if PASS: comp3/4/5 build (grasp_actuation ON + flag-gated write-site + C2 scene) + live DoD (⑨b 81-single-cell / ⑥ / ⑦(b) / C2-seating video) → HIGH-COST → **/production-launch-gate**. SRG FAIL → STOP + surface decision point (NO threshold-relax).

## §6. step_target packet spec (BAKED — CC2 component-1 build spec)
- **recorded_replay-ONLY** (live CUT, Q1): replay run_route recording per RL step. **81 single-cell** (interface carries no world-index → 81 sequential single-cell replays for ⑨b; `__init__` extended to carry per-cell recorded_targets; INIT_XY_NOISE=0 for pure replay — CC2-CH3).
- **target_6d = ee_pos (DECIDED (b), %12 15:44; fork-(iv)-CONSISTENT — my v0.2 framing was INVERTED, §運用28 CONCUR)**: replay recorded `ee_pos` at the next-waypoint frame, R-then-L, EXACTLY matching the banked BC/trainer base `route_demo_to_bc.py:255-287`: `cf = arange(0, LAST_CTRL_FRAME(7700)+1, PHYSICS_STEPS_PER_RL(10))` [771 frames] → `next_f = cf[1:]` [770 steps] → `wp = concat([ee_pos_r[next_f], ee_pos_l[next_f]])` [R-then-L]. ⇒ ⑨b base == fork-(iv) trainer base == BC pipeline == run_route recording = **single-source** (resolves CC2-CH1: `ee_pos` IS the achieved smooth path, NO snap-vs-ramp). `ee_tgt_pos` = macro-leg segmentation ONLY (`route_demo_to_bc.py:854`, NOT the base). step_target MUST reuse/cite this exact indexing (NOT reimpl). ⚠ frame `next_f[t]=cf[t+1]` for RL step t∈[0,769]; phase/grip sampled at `step_f[t]=cf[t]`.
- **phase_id** (CC2-CH2, verified 15 vals): map recorded phase_id [-1,0..8,10..14] → [0,6) N_ROUTE_PHASES (spec the 15→6 map from the monolith route sub-phase semantics; NOT the stub equal-split clock — that desyncs 100s-steps → cable drop).
- **grip_2** (verified radians 0-0.7407): threshold recorded grip_cmd radians → {0,1} (open/closed; e.g. ≥ GRIPPER_DRIVER_HALF_OPEN_RAD). **is_dual** from grip_2/phase (single-source, not re-derived).
- **R-first [R,L] assembly + unit assert** (CC2-CH5, verified _STACK_KEYS [L,R]): explicit [R,L] concat, assert vs a known cell (arms-not-swapped).
- **n_frames** per-cell 7706-7710 not const (CC4/CC2-CH4): read per-cell, no hardcode; pad-to-horizon holds grippers → assert G6-latch BEFORE pad.

## §7. SRG (revised, Stage-B, CC3) — creep-budgeted HARD decision-gate
- **MINIMAL probe FIRST**: cheapest C1-grasp+hold go/no-go (single nominal, grasp_actuation=ON 4-substep) before comp3/4/5.
- **creep-BUDGETED criterion** (CC3-CH1, no-slip UNREACHABLE): grip = form-closure CAGE (cage≠hold); intrinsic creep 60.4µm/f @F=0 (10-substep). **re-measure creep floor at 4-substep as FIRST substep** (10-substep bank doesn't transfer). criterion = rate-under-load ≤~1.2 OR service-exposure window (not absolute no-slip).
- **tail screening** (CC3-CH2): nominal + DR-corner (±16mm table-void edge) + known-hard; gate = worst-screened.
- **levers** (CC3-CH3, ranked cheap→campaign): {noslip_iterations (110× banked-BEST), impratio (∝1/impratio), solver iters, pad friction/solref} → substep 4→N LAST (Rs-level, campaign-affecting).
- **per-axis conservatism** (CC3-CH5): substep=conservative-w-caveat / offset=non-conservative / creep-floor=unknown-until-measured.
- **observable-bound no-silent-cap** (CC3-CH4): bind to creep metric + tail cells + quantified slip-time-series (single nominal video+human-GT insufficient). human-GT verdict.

## §8. state_bank + ⑦ (CC6 split)
- comp2 builds `_state_bank[k]` = phase-k banked {arm+all-16-gripper qpos/qvel, grip_target} from the recording (Q3: recording carries phase_id per-frame → phase-k boundary = first frame at mapped phase k). RouteExecutor.reset_to_phase(:3007) restores via apply_banked_restore (BUILT).
- **⑦(a)** (Stage-A no-GPU): restored qpos/qvel L∞ ≤ 1mm/1mm/s (static unit). **⑦(b)** (Stage-B): 1-step-after-reset divergence (grasp_actuation=ON, live). SCALAR k (per-world curriculum → trainer, §13.2).

## §9. C2 groove scene (comp5, Stage-B) — Q2 pre-resolved (CC5-SOUND): C2=even clip X=0.40 on SOLID floor (NO void), additive flag-gated build → env-core byte-preserve when off. /geometric-design at Stage-B design-gate.

## §10. §9 static drift tripwire (comp6, Stage-B, 2-leg — CC4-C2)
current test_routeexec_byte_repro.py:265 = stub (non-blocking, KEEP until leg-(b) specified). 2 legs: **(a)** raw sha256(test:3692-5765)==_ROUTE_MONOLITH_GOLDEN_SHA256 = monolith-EDIT tripwire (catches locked-file drift, NOT run_route). **(b)** run_route-DRIFT = ast-semantic-equiv reversing ONLY the F11 delta (mirror §12.4) = the actual先祖返り guard. leg-(a) alone (v0.1) = tautology.

## §11. design-gate skills (by content)
- Stage-A {1,2}: no reward/geom/force change (facade + wiring + state_bank; predicate 不変) → design-gate LIGHT; **/reward-design for the RESTORED ⑤ EXACT predicate + §運用29 leg table** (success-condition surface). confirm at re-gate.
- Stage-B: /force-design (grip servo 4-substep + SRG) + /geometric-design (C2 scene) at Stage-B design-gate.

## §12. Open-Q RESOLVED (item 7) + 1 ESCALATED
Q1=recorded_replay-only (live deferred-trainer) / Q2=C2 pre-resolved / Q3=state_bank phase-k from recording phase_id per-frame / Q4=creep-budgeted / Q5=reuse+pin 81 Layer-A recordings now. **✅ RESOLVED (%12 15:44): ee_pos-vs-ee_tgt = (b) ee_pos, fork-(iv)-CONSISTENT (route_demo_to_bc.py:287 base = ee_pos[next_f]; §運用28 CONCUR). single-source ⑨b==trainer==BC==run_route; resolves CC2-CH1 snap-vs-ramp. NO Rs escalation needed.**

## §13. Risks — substrate-transfer material (SRG §7 gate, substep→Rs post-data) / grip 4-substep premise (SRG probe first) / step_target divergence (recorded_replay single-source + ee_pos/ee_tgt escalated) / flag-OFF byte-preserve (B⑨a′ full-arm_q sha incl gripper, CC4-C4) / ramp-vs-snap trajectory divergence (⑨b, tied to §6 escalation).

---
*%11 COORD (w2:p3) v0.2 2026-07-07 15:3x (folds 5体 DECIDE=REVISE, all 7 items). PLANNING only. → %12 focused re-gate (delta-only) → PASS → minimal Stage-A {1,2} build 授権. ee_pos/ee_tgt fork ESCALATED.*
