# P2 whole-route RL reward design — INDEPENDENT GT cross-PV of the /pre-check BLOCK

**Verifier:** OPS-SUPERVISOR (%9, independent PV). **Requested by:** RS-TECH-LEAD (%12), Rs directive 2026-07-02「連携して進めて」.
**Decider≠verifier:** %12 ran /pre-check → BLOCK; I independently re-adjudicate against the ACTUAL code (file:line). NOT a rubber-stamp.
**Subject:** `P2_REWARD_DESIGN.md` (Architecture A = 12D dual-arm EE-delta RESIDUAL PPO/DAPG on the committed square-on route; obs 49D).
**HEAD** `bcb7393ec8` (verified `git rev-parse`). **Constraints honored:** 0-commit, 0-build, INVARIANTS #1-5 untouched, read-only + this one MD.

## §0. Grounding (anchor-set, §運用4 — read + cited myself, not from handoff/memory)
| Anchor | Cite | Fact used |
|---|---|---|
| LEDGER row43 | `00-DESIGN-STATUS-LEDGER.md:43` | committed square-on route = 🟢 WORKING Rs-confirmed, `bcb7393ec8` = the DAPG demo SEED |
| LEDGER row54 | `:54` | AR single-L コ-cage NOT load-bearing (force-falsified); retain-vs-load FUNDAMENTAL for rigid mujoco-コ cable; clip-retention sub-thread IN-PROGRESS |
| RS71 §0 INV | `RS71-System-Spec-SSOT.md:23-27` | #1 DUAL-ARM / #2 88mm span (bases Y=∓0.35) / #3 DiffIK-only / #4 コ-shape LOCKED / #5 no kinematic trick (only clip-pin) |
| RS71 §4 | `:53-54` | cable = 1-DOF VERTICAL bender → horizontal routing curvature is KINEMATIC (banked sim2real limitation) |
| Scoping | `DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md:35` | whole-route RL **env = ABSENT** (AC/AR/Grip are single-skill); demo-set + train-entry = real gaps |

## §1. Per-issue adjudication (CONCUR / DISSENT / PARTIAL + evidence + severity)

| # | Pre-check | My verdict | Evidence (independently read) | Severity |
|---|---|---|---|---|
| **CRIT1** | r_phase base-scheduled → ~0 gradient → doesn't bridge gates → §3/§4/§6 PASS invalid | **CONCUR** (mechanism refined) | `test_newton_clip_routing.py:2702` `run_episode(...)` is an IMPERATIVE validation fn (not `VecEnv.step()`); phases advance on the SCRIPT (2-phase servo `:3358-3369`, argmin re-target `:4338`, settle loops `for _ in range(30/40): physics_step`). **Refine:** r_phase is not literally zero-grad — it is a **one-sided "preserve" signal** (agent only LOSES +5 by breaking the base's progress); it never PULLS the agent through an agent-earnable gate. So the design's "r_phase bridges the gates → no dead zone" reasoning is **INVALID as written** (the base earns the gates, not the residual). | **CRITICAL — upstream** |
| **CRIT2** | no demos → DAPG degenerates to from-scratch PPO | **CONCUR** | route emits **0** demos (`grep -cE "savez|\.npz"` = 0); no `*dapg*` script; `train_common.py:349-352` HARD-asserts `demo_obs.shape[1]==num_obs` & `demo_act==num_actions`; `:342-348` zero-pad only fills the extra dims with zeros → a 42D grasp-only demo would pad `[42:49]`=0 (garbage phase/held) and cover only 2 of 6 phases. No 49D/12D whole-route generator exists. §8 risk table OMITS the demo gap. | **CRITICAL — upstream** |
| **HIGH3** | anti-hover holds ONLY @P0; mid-episode positive basin missed | **CONCUR (strengthened)** | `AR:293/1380-1429` `_measure_p0_and_calibrate` sets ONE constant so `Net@P0 = TARGET_NET_P0(-0.07)`; it includes only P0-active terms (r_pos/r_ori/r_oritail/r_height). The design ADDS **phase-gated** r_retention(+0.30, GRASP→SEAT) & r_seat(+0.5, SEAT) that are 0 at P0 → NOT in the calib → design's OWN §5 shows per-step Net +0.68 (GRASP)..+0.90 (SEAT). AR's pattern does NOT port: AR's positive dense term (r_height) is live-from-P0 (calibrated-in via frozen-L); the design's are gated-ON later. Hover@GRASP is a real competitive basin (γ=0.99: 0.68/0.01≈+68 vs delayed +200 under drop-risk). | **HIGH** (fixable-in-design, env-dependent) |
| **HIGH4** | seat-ori cos>0.85 undischarged + residual-unfixable | **CONCUR** | route has **NO** seat-ori cosine gate (`grep cos/dot/T_SEAT/0.85` → only `:965` geom-angle, `:6287` drift_rot, `:4357/5340` quat-construct — all unrelated); the re-grasp verdict `:4437-4468` gates on NORMAL FORCE + reach, never ori. `AC:58-65`: active ori-IK UNDER-APPLIES ~100× (14°→0.11°), "HARD PREREQUISITE … UNRESOLVED". So success's `cos>0.85` is base-UNVERIFIED **and** residual-INERT → possibly UNREACHABLE, no computed value proves the base reaches ≥0.85. | **HIGH** (partly Rs-reserved: G7) |
| **HIGH5** | 6/12 action dims (rot) dead under G7 | **CONCUR (wording: near-inert)** | actions `[3:6]/[9:12]` = R/L rot deltas (`AC:40-42`); under G7 (`AC:58-65`) ∂(actual-EE-ori)/∂(rot-action)≈1/100 → ~inert, and BC (the only other constraint) is absent (CRIT2). Not literally "dead" (0.11°/step) but optimization-inert for practical purposes. **Downstream of the G7 root**, and it compounds HIGH4 (can't fix seat-ori). | **HIGH (downstream of G7)** |
| **HIGH6** | base imperative, not per-RL-step; re-expressing at RL cadence is a LARGE ABSENT build; retention mechs not residual-controllable | **CONCUR — SEVERITY-UP → CRITICAL** | `ik_move_both(..., converge_mm, speed_factor)` = variable-convergence loops; monkeypatched `solve_ik_dual` `:4400`→restore `:4479`; mid-episode eq-pin `:4063-4071`; 2-phase servos `:3358-3369`/`:4430-4436`; settle `for _ in range(30/40)`. RL drives a fixed 12D-EE-delta at `PHYSICS_STEPS_PER_RL=10` (`AC:238`). The whole-route MDP env **does not exist** (`SCOPING:35`) → this is the co-equal ROOT blocker, not a HIGH detail. Retention (pin+cage) is base-scheduled → residual has ~0 authority over it. | **CRITICAL — upstream (co-root)** |
| **MED7** | ROUTE_TERMINAL_STEPS=400 underived | **CONCUR** | `grep -rn ROUTE_TERMINAL_STEPS thread_isaac_lab/` = empty (new param). 1 RL step = 10×(1/480)=1/48s → 400=8.33s, NOT derived from the route's actual physics-frame count (which is only knowable once the env re-expresses the imperative route). May under-run SEAT → r_seat/r_task never sampled. | **MED** (fixable once env frame-count known) |
| **MED8** | r_seat obs[16:19] = R-clamp nearest seg, ~44mm off the seated seg | **CONCUR (→ HIGH-adjacent if unfixed)** | obs[16:19] = seg nearest R-clamp (`AR:988/997-1002` argmin-to-clamp). Route `:4480-4482`: TRANSPORT carries the cable so the **centre** (between L&R) seats at the C2 groove, while R holds +Y = `c2y+GHS`, `GRIP_HALF_SPAN=0.044` (`TC:235`) → obs[16:19] is ~44mm off the seated seg → `e^(−0.044/0.003)=e^(−14.7)≈0` → r_seat is a DEAD success term. Fixable-in-design (add a dedicated seated-seg obs index). | **MED→HIGH** (fixable) |
| **MED9** | retention obs-fix CORRECT (Rule21); residual authority overstated; caveat not blocker | **CONCUR — and credit the design** | `AR:48-52` explicitly: cz_l_excl NOT in obs is sound ONLY under frozen-L (cz≈LIFT_Z invariant); the whole route MOVES L → held_cable_z MUST be in obs → the design's `[48]` is a **genuinely correct §運用21 fix** (own-errors-both-ways: this is a design POSITIVE). BUT retention is base-scheduled (pin `:4063`, cage `:3358/:4430`) → "r_retention keeps cable held through drag" overstates residual authority. Caveat, NOT a blocker; NOT SRG_PROBE_ONLY. | **CAVEAT (not a blocker)** |
| **MED10** | "auto-close (pos<thresh)" mischaracterization; AC has no gripper channel; anchor:3952-3960 = CLIP_FLOAT_Z readback | **CONCUR** | real close = scheduled 2-phase servo (`:3358-3369` C1 CAGE_FRAC=0.9; `:4430-4436` C2 cage 0.9); `AC:224` fingers always OPEN + 12D action has NO gripper dim (`AC:38-42`); AR's close is a scripted "auto-close at pose-match" (`AR:1432`), NOT an RL channel. `:3953` IS a `CLIP_FLOAT_Z` consistency READBACK (not a close). Design conflates AR's scripted servo with an RL "auto-close channel". | **MED** (records-vs-code; fixable) |

**Adjudication summary: CONCUR on all 10** (no DISSENT survived independent code-reading). Refinements: CRIT1 = one-sided-preserve not zero-grad; HIGH5 = near-inert not dead; HIGH6 = severity-UP to CRITICAL; MED8 = →HIGH if unfixed; MED9 = the obs-fix is a design POSITIVE. I looked for over-statements to reverse; found only wording nuances, none that flip a verdict.

## §2. MISSED issues (pre-check did NOT catch)
- **M-A (the real #1 blocker): the whole-route ENV is ABSENT, not merely the demos.** The design's 49D obs + 6-phase reward presuppose a `NewtonWholeRouteMujocoEnv` that must be BUILT from scratch, re-expressing the entire imperative choreography (monkeypatched tilt-IK `:4356-4401`, eq-pin `:4063-4071`, 2-phase servos, argmin re-target) as an MDP — with the phase-advance rule (CRIT1's fork) unresolved. The four /reward-design artifacts (§3-§6) are all computed against an **assumed** env behavior → per **§運用18** they cannot be validly discharged (no env exists to MEASURE the ground-truth P0; the `R_PENALTY=−1.51` is a placeholder, not "measured-in-build" as §5 claims — AR measures in-build only because AR's env exists).
- **M-B (ori-weight regression vs AR):** the design uses `W_ORI=0.5` (AC value) for a route whose terminal success is ori-critical (seat cos>0.85), but AR — after hitting the ori bottleneck — raised `W_ORI 0.5→0.75` + added `W_TAIL=4.0` ori-tail (`AR:285-288`). The design DOWNGRADES ori weighting exactly where ori matters most, compounding HIGH4/HIGH5. Not caught by pre-check.
- **M-C (the "robustness" the design trains is largely illusory — bears on the strategic):** the base argmin-follows the ACTUAL cable using SIM PERFECT STATE (`:4335-4340`, reads `state.body_q`). So it already defeats the ±20mm position-DR (`CABLE_XY_DR_AMPLITUDE=(0.02,0.02)`, `TC:264`) the reward worries about — the residual's DR-absorption is redundant *for sim perfect-state*. The robustness that WOULD matter (noisy/estimated cable pose for sim2real, curved-cable) is NOT trained here (perfect-state obs, DR OFF-by-default `TC:257-261`). So Architecture-A-as-specified trains against a disturbance the base already defeats and does NOT train the pose-uncertainty a real deployment needs.
- **M-D (INVARIANT#2 at SEAT — watch, not a defect):** the committed base holds 88mm at re-grasp (`:4341`, `AR:306` REGRASP_SPAN_MAX=0.088), so the SEED is INVARIANT#2-clean; but the design's success clause "both arms reached seat pose" must be verified to preserve the 88mm span through SEAT in the env (the earlier B1' step-13 flagged a 120mm>88mm regime, LEDGER `:54`). Carry as a build-time gate.
- **M-E (Grip-VBD substrate residue — minor):** any reuse of Grip-derived close logic must force the mujoco backend (`newton_grip_env.py:366` defaults to VBD springs, `SCOPING:39`); the design reuses AC/AR (mujoco-forced) so this is low-risk but worth a build-time assert (先祖返り guard).

## §3. STRATEGIC verdict (the #1 item — UPSTREAM of the 10 reward issues)
**Evidence-based finding: Architecture A, as specified, does not clearly buy the robustness Rs wants, and ~7 of the 10 reward issues are DOWNSTREAM symptoms of two upstream facts.**

1. **The base already does the DR job (sim).** `:4335-4340` argmin-re-targets to the actual cable bow each grasp/re-grasp (Rs-LOCKED anti-revert `:4335/:4350`). The ±20mm "air-grip" DR (`TC:264`) is removed by the base itself → the residual's stated DR-absorption value (design §0 line 14) is largely REDUNDANT for sim perfect-state.
2. **The one unsolved risk is unreachable by the residual.** Retention-under-load (row54 sliding-cradle, `LEDGER:54`) is the real open gap — but retention is a base-scheduled mechanism (clip-pin `:4063`, gripper cage servo `:3358/:4430`), NOT residual-controllable (MED9). So the residual cannot LEARN the very robustness that matters.
3. **No demos → "DAPG" is from-scratch PPO** (CRIT2) on a 6-phase long-horizon task, where the base does the actual work and the residual can mostly only MATCH (≈0) or WORSEN (penalty) it → the RL optimum is residual≈0 = the deterministic base = a BC-like regularization, but WITHOUT the demos that would make it tractable.
4. **Half the action authority is inert** (HIGH5/G7), so the residual is position-only.

**Verdict:** the reward-design GATE is correctly BLOCK, but the decisive question is UPSTREAM — the **unit of learning**, which is Rs's call:
- **(i) Residual-PPO on the committed route (Architecture A):** legitimate technique, but here it (a) needs a large ABSENT env build (M-A/HIGH6), (b) can't reach the retention gap (row54/MED9), (c) has no demos (CRIT2) → high cost, unclear payoff **in this configuration**.
- **(ii) BC / imitation of the already-DR-robust deterministic route:** the base is already targeting-robust; distilling it into a policy (then adding noisy-pose/vision DR later) may be a cleaner, lower-risk unit than residual-PPO-with-absent-demos.
- **(iii) Narrow-scope RL on the real gap:** put RL only where there is an actual unsolved, agent-earnable problem (retention/seat under perturbation), scripted-guide-data for the rest — matches Rs's "collect DAPG guide-data" goal and avoids the imperative→whole-route-MDP rebuild.

Fixing the reward (the 10 issues) is premature until Rs picks the unit and authorizes (or defers) the whole-route env build.

## §4. OVERALL: **CONCUR-BLOCK** (reward-design gate), reframed as UPSTREAM
The design's self-GATE=PASS is not valid: §3-§6 artifacts rest on a non-existent env + a false "agent-earnable phase" model (CRIT1), and "DAPG" has no demos (CRIT2). But the BLOCK is best actioned as an architecture/scope decision, not a 10-bug reward patch.

### WHAT MUST Rs DECIDE (each mapped to a concrete question)
**Rs-reserved (upstream — decide BEFORE any reward finalization):**
- **Q1 UNIT:** residual-PPO (A) vs BC-imitation of the deterministic route vs narrow-scope RL on the retention/seat gap? *(§3; drives everything below.)*
- **Q2 BUILD the whole-route MDP env?** re-expressing the imperative route (servos, monkeypatch IK, eq-pin, variable-convergence moves) as a per-RL-step VecEnv, incl. the phase-advance rule (script-schedule vs agent-condition, CRIT1 fork). env/reset/DR = Rs design-gate. *(M-A/HIGH6/CRIT1.)*
- **Q3 DEMOS:** authorize a whole-route 49D/12D demo recorder off the committed route (else no real DAPG)? *(CRIT2.)*
- **Q4 RETENTION:** keep base-scheduled (residual can't learn it — accept as P4 GPU/real gate), OR add a physical retainer (deferred C2-pin/latch/finger, design §8 Q1), OR expose retention to the policy (INVARIANT#4-touching → premise change)? *(row54/MED9.)*
- **Q5 G7 ori-control:** resolve active ori (HARD PREREQUISITE, `AC:58-65`) before gating success on seat cos>0.85, or drop the ori success clause for now? *(HIGH4/HIGH5.)*
- **Q6 HORIZON / time_outs purity:** `ROUTE_TERMINAL_STEPS` (proposed 400) is time_outs-sensitive (prohibited.md value_loss-105× guard) → Rs design-gate. *(MED7.)*
- **Q7 inter-arm collision:** re-enable the arm-arm collision spheres AC drops (`AC:47-52`) for the both-arms-moving route? *(design §8 Q3.)*

**Fixable-in-design (once the env + unit are settled — do NOT need Rs, but are moot until Q1-Q3):**
- HIGH3: recalibrate/anti-hover for the mid-episode positive basin (phase-gate the dense positives, or make R_PENALTY phase-aware so Net stays ≤0 pre-success).
- MED8: dedicated **seated-seg** obs index for r_seat (not the R-clamp-nearest seg).
- MED10: correct the "auto-close (pos<thresh)" wording → the scripted 2-phase servo; decide the gripper action representation.
- M-B: restore AR's `W_ORI=0.75`/`W_TAIL` (or better) for the ori-critical seat.
- M-D/M-E: build-time asserts (88mm SEAT span; mujoco-backend guard).

## §5. Conservatism direction on every fidelity-bound claim
| Claim | Direction | Note |
|---|---|---|
| Base "air-grip removed" by argmin-follow | **NON-CONSERVATIVE for real** | uses SIM PERFECT cable state (`:4335`); real pose is estimated/noisy → base targeting won't be perfect → the residual's DR value only appears under noisy-pose training (not this design) |
| Retention (row54 sliding-cradle) | **NON-CONSERVATIVE** | non-load-bearing on soft/real; sim CPU-newton is the current bar, GPU-cg + real = harder → carry as P4 gate (design §8 does this = correct) |
| r_seat 3mm groove reachable | **NON-CONSERVATIVE** | rigid sim clip = EASIER than a compliant real clip |
| seat-ori cos>0.85 (G7) | **NON-CONSERVATIVE** | straight-cable ori-PASS is non-conservative (`AC:62-64`); curved/deploy needs real ori validation FIRST |
| whole-route GPU validity | **UNKNOWN → must screen** | AC/AR are CPU-smoke only; cg-GPU whole-route NOT screened (my P1 GT-PV NEW axis) — verify before P4 |
| §4 horizontal routing curvature | **fidelity boundary (banked)** | KINEMATIC in the env7 cable (`RS71:53-54`) either arch → real-cable gate |

---
**BOTTOM LINE:** CONCUR-BLOCK on the reward-design gate. The 10 issues are well-founded (independently code-verified); the pre-check is not over-stated. But the block is UPSTREAM: resolve the UNIT (Q1) + whole-route-env build (Q2) + demos (Q3) + retention/ori premises (Q4/Q5) BEFORE finalizing the reward. Own-errors-both-ways credit: the design's §運用21 held_cable_z obs-fix (MED9) is genuinely correct. 0-commit/0-build; HEAD `bcb7393ec8`; INVARIANTS #1-5 untouched.
