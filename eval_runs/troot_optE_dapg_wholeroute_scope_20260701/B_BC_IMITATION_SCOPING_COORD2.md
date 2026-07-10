---
doc_class: reference
---

# B (BC-imitation) pipeline — SCOPING for the committed C1→C2 route

**Author:** COORD2 (%10, scoping/audit). **Date:** 2026-07-02. **HEAD** `bcb7393ec8`, env7 mujoco-コ (`env_isaaclab7`).
**Charter:** RS-TECH-LEAD (%12) → COORD2 (%10). **Rs DECISION 2026-07-02 ~07:37: DQ1 = B (BC-imitation)** (node `state.md:36`, verbatim「B」). PROPOSE-ONLY: scoping doc, **0-commit, no build**. Read-only + this one MD.
**Scope of B (node `state.md:37`):** DQ2 whole-route RL env = **moot under B** → replaced by **converter (raw npz → BC dataset) + pure-BC trainer + policy-rollout evaluator**. A/C (residual-PPO / narrow-RL) kept as future options, NOT killed (`state.md:36`).
**Constraints:** INVARIANTS #1-5 untouched. Do NOT touch %11's WT recorder files. Where `route_demo_raw.npz` is not yet on disk (VERIFIED absent 2026-07-02, `find` = 0 hits; recorder BUILT but DoD not run, `P3_RECORDER_BUILD_REPORT.md:4`), schema claims = **"per spec v2.4, pending artifact."**

---

## §0. GROUNDING (anchor-set, §運用4 — read + cited myself, not from handoff/memory)

| Anchor | Cite | Fact used |
|---|---|---|
| LEDGER row43 | `00-DESIGN-STATUS-LEDGER.md:43` | committed square-on C1→C2 route = 🟢 WORKING Rs-confirmed 2026-07-01, `bcb7393ec8` = **the demo SEED B imitates**; C2 positive-retention DEFERRED. |
| LEDGER row54 | `:54` | AR single-L コ-cage NOT load-bearing (force-falsified 06-29; hold = dual-clamp+tension); **retain-vs-load FUNDAMENTAL** for rigid mujoco-コ; clip-retention sub-thread IN-PROGRESS. |
| RS71 §0 INV | `RS71-System-Spec-SSOT.md:23-27` | #1 DUAL-ARM / #2 88mm span (bases Y=∓0.35) / #3 **DiffIK-only** / #4 コ-shape LOCKED / #5 no kinematic trick (only the authorized clip-pin `log.md:6534`). |
| RS71 §4 | `:53-54` | cable = 1-DOF vertical bender → horizontal routing curvature is KINEMATIC = banked fidelity boundary. |
| P1 verdict | `log.md:6851` + `canonical_run_records/p1_probe/P1_VERDICT.md` | whole C1→C2 route+retain window EXISTS on env7 mujoco-コ **CPU** — **PASS non-conservative** (%0 GT-PV CONCUR-W-CORR). 4 carried risks: row54 sliding-cradle / §4 curvature / **cg-GPU whole-route screen UNVERIFIED** / reach-fragility. |
| P2 pre-check | `P2_PRECHECK_CROSSPV_OPSSUP.md` §3-§4 | Architecture-A (residual-PPO) reward-design = CONCUR-BLOCK; the **UNIT** choice is Rs's; the pre-check RECOMMENDED **(ii) "BC / imitation of the already-DR-robust deterministic route"** (`:51`) = what Rs picked as B. |
| Device caveat | `P3_DEMO_RECORDER_SPEC.md:145-149` §4.2 | ⚠ **canonical route is cuda:0-SPECIFIC** — on cpu the R re-grasp reach knife-edge flips to BLOCKED (R 0N / reach 83.2mm vs 104.51N / 0.9mm). |
| ⚠ carried spec-drift (all panes) | `RS71-System-Spec-SSOT.md:26` / `GD-KoShape-Finger.md:95-96` | "f1ext form-closure retention" mechanism story is force-falsified (06-29, held via dual-clamp; LEDGER `:54` carries the BLOCKED_FOR_USER correction) but the 2 specs are still un-caveated (Rs専権, 04-Specs). Not B-blocking; flagged for anyone citing コ retention. |

**先祖返り guard (CONFIRMED clean):** B imitates the committed physics-faithful route (`bcb7393ec8`) with `bc_pretrain.py` (surviving env7 infra). It restores/imports **none** of the 5 deleted env6-VBD skill envs (LEDGER §FAILED 2-3, `:69-87`); `collect_expert_demos.py` is **NOT** reused (prior-art disposition `P3_DEMO_RECORDER_SPEC.md:40`: imports deleted env6-VBD envs at `:186,191` = banned; a sub-agent that read only its top import `:28`=task_config mis-scored it "safe" — reconciled to BANNED, moot since unused). Base = the committed route, NOT the BANNED Fix1 Kinematic Transport.

---

## §1. CONVERTER — `route_demo_raw.npz` → BC dataset (charter item 1)

### 1a. Design matrix — ACTION semantics (the core decision)

The recorder emits BOTH the actual EE pose and the commanded target per frame, so all three action sources are **derivable** from one npz (recorder `_STACK_KEYS`, `route_demo_recorder.py:29-42`; P3 spec `:110-123`). Requirement (charter): the rollout must reproduce the route when actions are re-applied through the SAME DiffIK apply path.

| # | Action source | Derivable from | BC-executability | Verdict |
|---|---|---|---|---|
| (i) | **actual-pose deltas** (Δee_pos over the cadence) | `ee_pos_l/r` (`recorder:125-128`) | **smooth ~2mm/RL-step** (`P3 spec:121`), dense, closed-loop; = the AC-env action semantics (`newton_approach_cable_mujoco_env.py:39-42`) applied through `solve_ik_dual` (`:1820`) → **preserves INVARIANT#3 DiffIK**. Caveat: "encodes the interp schedule" (`P3 spec:121`) — smoothness comes from the scripted FK-interp (`test:1990-2004`), so BC learns to reproduce that motion profile. | ✅ **RECOMMENDED** |
| (ii) | commanded-target deltas | `ee_tgt_pos_l/r` (`recorder:129-130`) | **zero/spike train** — `ik_move_both` solves once + FK-interps (`test:1962-1996`); the 100mm transport = one ~6.7× POS_ACTION_SCALE spike at a boundary (`P3 spec:119-120`) → needs boundary re-chunking; a BC policy must learn discrete jumps at boundaries it cannot observe. Also collapses the "policy" to ~16 macro-decisions (one per `ik_move_both` call), not a reactive controller. | ✗ dispreferred |
| (iii) | joint-space targets | `arm_q` (`recorder:133`, = `state.joint_q` PHYSICS vector) | **bypasses DiffIK** (a policy emitting joint targets directly is not DifferentialIK control = INVARIANT#3 tension) + `arm_q` carries frozen-finger dims (`P3 spec:96`) + higher-dim + non-transferable to the AC/AR obs/action layout. | ✗ dispreferred |

**Recommendation = (i) actual-pose deltas, POSITION-ONLY (6D: R xyz + L xyz), fixed cadence = every-10th-physics-frame ≈ 48 Hz** (matches `PHYSICS_STEPS_PER_RL=10`, `newton_approach_cable_mujoco_env.py:238`; DT=1/480 `test:124`). Rationale grounded above; the position-only choice is justified in 1c.

### 1b. OBS schema — recommend a LEAN B-specific vector, NOT the 42D/49D env obs

⚠ **§運用28 reconcile (42 vs 49):** the AC single-skill env obs = **definitively 42D** (`newton_approach_cable_mujoco_env.py:788` `np.zeros((world_count,42))`, `:1214` `return 42`; verified myself). The P3 spec's "49D" (`P3 spec:110-117`) = the **proposed whole-route obs** = 42D base + phase-one-hot + clip-idx/C2 + `held_cable_z` (the whole-route additions my prior scoping proposed, `DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md:66`). Not a contradiction — different objects. **Neither is required for B.**

For B the policy only needs what the **evaluator can feed at inference from the live scene** (charter item 1). Recommend a lean vector:

| B obs dim | Source at inference | Why |
|---|---|---|
| R EE pos (3) + L EE pos (3) | `state.body_q[ee,:3]` (`recorder:120`, `test:1905` accessor) | position control needs current EE |
| target cable seg pos (3) | `cable_xyz[nearest_seg]` (`recorder:123,143`) | where the cable is (base argmin-follows the actual cable, `test:4335-4340`) |
| phase scalar / one-hot (1–14) | the evaluator's scripted phase clock (`phase_id`, `recorder:138`; 14 native phases `P3_RECORDER_BUILD_REPORT.md:49-50`) | multi-phase route; the policy must know the phase |
| next-clip target pos (3) | sidecar RESOLVED C1/C2 (`recorder:216-217`) | where to route to |

**DROP** all quaternion dims (avoids the STATEFUL `temporal_quat_consistency` replay, `newton_skill_env_base.py:823-845` — a static w≥0 flip is NOT equivalent at sign boundaries, `P3 spec:114`), finger openings (gripper scripted, 1c), and ori-error dims (position-only). This is the "the BC policy only needs what the ROLLOUT can feed" principle — and it removes the single most fragile derivation (stateful quat replay). ⚠ **seated-seg re-index (ISSUE8):** at the SEAT phase the target seg must switch from R-clamp-nearest to the **seated** seg (`P2_PRECHECK_CROSSPV_OPSSUP.md:28` MED8: obs[16:19]=R-clamp-nearest is ~44mm off the seated seg → dead) — a convert-time re-index the lean obs must apply (`P3 spec:112`).

### 1c. gripper, rot-dims, quat conventions (charter item 1 sub-questions)

- **Gripper (grip_cmd = base-scheduled):** **keep SCRIPTED in the evaluator, NOT an action dim** (for B0/B1). The close is a scheduled 2-phase servo (`_set_gripper_target` `test:2992` chokepoint; C1 `test:3850-3865`, C2 `test:4430`-region), and the AC/AR 12D action has **no** gripper dim (`P2_PRECHECK_CROSSPV_OPSSUP.md:30` MED10; `newton_approach_cable_mujoco_env.py:1117-1120` fingers scripted OPEN). B imitates the **arm motion**; the gripper/pin/phase transitions replay from the recorded schedule (`grip_cmd`/`pin_active`/`phase_id`). Imitating the gripper as an action dim adds a discrete-event learning problem with no shakedown benefit → defer (Rs Q, §7).
- **Rot dims → DROP (position-only):** the recorded effective rotation is a **constant** Rx(−90°) (`recorder:28`, `test:1864`; `C2_TILT_SIGN=0` square-on `test:4347`) → the rot channel carries **no commanded signal** (`P3 spec:121-122`), and active ori-IK **under-applies ~100×** (14°→0.11°, G7 KNOWN-GAP `newton_approach_cable_mujoco_env.py:58-62`). Keeping rot as an action dim = 6 inert dims. The evaluator holds ori at the constant Rx(−90°) inside `solve_ik_dual` (`:1864`) → INVARIANT#3 preserved, the policy simply does not command ori-deltas.
- **Quat conventions:** all recorder quats are **xyzw (warp)** (`recorder:203`, `P3 spec:107`); the lean obs drops quats entirely (1b), so the xyzw/wxyz seam (`test:2350-2352`) and the stateful-replay requirement do not enter the B converter. (If a later variant re-adds quats, apply `temporal_quat_consistency` `newton_skill_env_base.py:823-845`, NOT the static `train_common.py:322-336` w-flip.)

### 1d. Converter output

A plain npz keyed **`obs` [T_ctrl, obs_dim]** + **`actions` [T_ctrl, 6]** (+ sidecar of the scripted gripper/pin/phase schedule for the evaluator to replay) — exactly the format `bc_pretrain.py:67-68` consumes (`data["obs"]`, `data["actions"]`). T_ctrl = T_physics / 10 (per-control-step). ~100–200 LOC, pure offline data transform (no solver call).

---

## §2. TRAINER (charter item 2) — inventory FIRST (§運用4), then recommend

**Inventory (grep-verified, file:line):**

| Asset | Env-coupled? | Verdict for pure BC |
|---|---|---|
| **`bc_pretrain.py`** (`scripts/bc_pretrain.py`, exists 2026-06-15) | **NO** | ✅ **REUSE.** `train_bc(policy, demos_path, …)` `:49`; loads `data["obs"]`/`data["actions"]` `:67-68`; `nn.MSELoss()` `:92`; Adam on actor params; builds `ActorCritic` WITHOUT an env (`build_actor_critic(obs_dim, act_dim)` `:28-46`); saves RSL-RL-compatible `model_state_dict` `:138-150`. **No `create_env`** (verified). |
| `train_base_model.py` (204 LOC) | NO | multi-task offline BC precedent (45D/12D, MSE); useful pattern, not needed for single-route B. |
| `train_common.py` "Shared DAPG (PPO+BC)" | **YES** | ✗ do NOT use for pure BC — `:349-352` HARD-asserts `demo.shape==env.num_obs/actions`; `:230` requires `create_env`. Its `--bc-warmup-steps` `:97` / w-flip `:322-336` = reference only. |
| `train_grip.py` "Train Grip … with DAPG" | YES (NewtonGripEnv) | ✗ inherits env coupling. |
| `SkillAdapter` (`models/skill_adapter.py:107-189`) | wrapper | optional post-BC LoRA fine-tune; not needed for B1. |
| rsl_rl `ActorCritic` | — | the policy net `bc_pretrain.py` already uses. |

**Recommendation: REUSE `bc_pretrain.py` as-is** + a thin CLI wrapper (`--demos bc_dataset.npz --obs-dim D --act-dim 6 --device cuda:0`), ~0–60 LOC. Loss = MSE on actor mean; obs/action normalization = optional (lean obs is already metric-scaled; NO quat dims → the `train_common` w-flip is N/A).

⭐ **STRATEGIC CONSEQUENCE — B avoids the P4 GPU-10h HIGH-COST-GATE.** BC is **supervised** (single forward/backward on a demo tensor, minutes on 1 demo; a DR set is still modest), with **no PPO rollouts**. So unlike Architecture-A (which needed `/production-launch-gate` for a GPU 10h+ residual-PPO run, `DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md:86`), **B's training has no 10h production-launch gate.** The only GPU use is the **evaluator** (route rollout on cuda:0 = inference scale, seconds-minutes/rollout), not training.

---

## §3. EVALUATOR (policy rollout) — the key NEW piece (charter item 3)

**Feasibility = CONFIRMED clean** (sub-agent apply-path map, all file:line verified myself):

- **Scene reuse, no RL env:** `build_scene(...)` `test:1031` returns `scene_info` (model/cable_bodies/…, callable standalone); solver via `make_solver()` `test:~6601`. The route runner `_run_mujoco_grasp_route(model, solver, contacts, scene_info, fk_state, …)` `test:3496` is a plain function, **no VecEnv class**.
- **CLEAN policy seam:** in the route, EE targets are computed ONCE before each `ik_move_both(model, state, scene_info, solver, contacts, target_left, target_right, …)` `test:1924` (via `tgt()`/`tgt2()` helpers, e.g. `test:3865`). A policy replaces the scripted target: **`new_target = current_ee + policy_Δ` → same `ik_move_both` / `solve_ik_dual` `test:1820`** — sub-agent found **no** inline-target entanglement (seam = clean).
- **Apply granularity (design nuance, honest):** for a reactive per-control-step BC policy, the runner re-solves IK each control step (`solve_ik_dual` + `physics_step(SIM_SUBSTEPS=10)` `test:1756/1781`) rather than calling `ik_move_both`'s once-per-macro-move FK-interp (`test:1990-2004`). This REUSES the DiffIK+physics core but is a **faithful-not-byte-identical** apply path vs the scripted macro-interp → **B0 (open-loop replay, §4) quantifies the reproduction gap** before any training.
- ⭐ **Substep FIDELITY ADVANTAGE (charter item 5):** the evaluator reuses the route's `physics_step` at **SIM_SUBSTEPS=10** (`task_config.py:101`, loop `test:1781`) = the EXACT integration the demo was recorded at → **no substep mismatch**. The RL-env path would consume at `RL_SIM_SUBSTEPS=4` (`newton_skill_env_base.py:95`, `newton_approach_cable_mujoco_env.py:1201`) = a 2.5× coarser, NON-CONSERVATIVE mismatch (`P3 spec:128`). **B eliminates that gap.**
- **Device = cuda:0 (MANDATORY):** `DEVICE=os.environ.get("NEWTON_DEVICE","cuda:0")` `test:123`; the canonical invocation pins `CUDA_VISIBLE_DEVICES=0` (`canonical_run_records/integrated_route/run_canonical.sh`). cpu flips the reach knife-edge to BLOCKED (`P3 spec:145-149`) → the evaluator MUST match the demo's device or it cannot reproduce the route.

**Success criteria = the canonical fingerprint** (`test:4486-4518`, JSON `route_c2_pin.json` `test:4744`): `regrasp_ok = (_at_88 and _R_grips)` `test:4502`; `SUCCESS_R_GRIP_L_CAGE_AT_88` `test:4501`; `r_grip_N` (canonical 104.51N), `r_reach_resid_mm` (0.9), `achieved_3d_span_mm` (100.3), `target_y_span_mm` (88), `tilt_sign` (0); seat `c2_seated_HONEST` / `SETTLED_IN_NOTCH` (z830.6, walls −0.392mm); C1 `C1_held_without_R` (z_c1 829→829) — all per `P1_VERDICT.md §1-3`. **+ §運用14 video leg** on the rollout (`--record-video` `test:6453` gate; skill-path `/video-analyzer` or `video-analyst`).

⚠ **Evaluator verdict-extraction fork (Rs/lead L question, §7):** the fingerprint is computed **INLINE** inside the Rs-LOCKED `_run_mujoco_grasp_route` (`test:4486-4518`, anti-revert markers `test:4372/4388/4487`), not a callable. The evaluator either (a) **re-implements** the verdict from raw state in a SEPARATE `policy_route_runner.py` (duplication, but keeps the locked route file UNTOUCHED = L2, 先祖返り/anti-revert safe) — **recommended**; or (b) **refactors** the verdict into a shared callable (edits the locked file = **L3** + anti-revert risk).

**Failure taxonomy (where BC silently diverges):**
1. **Drift accumulation** — open-loop over ~T_ctrl ≈ 2000 control steps (T≈20k physics frames, `P3 spec:181`) → small per-step errors compound. **Top B risk.**
2. **Phase timing** — the scripted phase clock (gripper/pin fire at recorded frames) can desync if the policy's motion is slower/faster than the demo → gripper closes on air. Mitigate: phase-advance on a geometric condition, not a fixed frame count.
3. **Gripper/pin events** — replayed on schedule; if the arm hasn't reached the pose, the close/pin mis-fires (couples to #2).
4. **Device non-determinism** — cuda:0 (GPU #562 non-det, `RS71 §0#4`) → run-to-run variance → the pass bar must be a **category-match RATE over N rollouts**, not one deterministic reproduction.

---

## §4. MILESTONES (charter item 4)

| B-phase | Definition | Pass bar (HONEST) | Cost / gate |
|---|---|---|---|
| **B0** (recommended, cheap) | open-loop replay: re-apply the recorded pose-Δ actions through the evaluator with **NO policy** | reproduces the fingerprint categories (`regrasp_ok=True`, `SUCCESS_R_GRIP_L_CAGE_AT_88`, seated) → validates converter+evaluator BEFORE any training | cuda:0 rollout; CC-domain; `/pre-check` |
| **B1** | single-demo BC (`bc_pretrain.py`) → policy rollout | fingerprint **category match** over **N** cuda:0 rollouts (NOT bitwise; N sized for GPU non-det) — a **PIPELINE SHAKEDOWN**, not a robust policy (1 demo = overfit replay of a deterministic + perfect-state route) | BC train (minutes) + N rollouts; `/pre-check`; **no HIGH-COST-GATE** |
| **B2** | DR demo-SET BC | generalizes to novel cable pos/pose/shape → the **real** policy | ⛔ **BLOCKED on the Rs DR-range decision** (§7 Q1); recorder re-run under DR to collect the set, then `bc_pretrain` on it |

B1's honest framing (charter "define the pass bar honestly"): the base route is **deterministic** and uses **perfect cable state** (argmin-follow reads `state.body_q`, `test:4335-4340`; `P2_PRECHECK_CROSSPV_OPSSUP.md:37,79`). A single-demo BC has nothing to generalize → it is a **replay-equivalent** whose value is proving the pipeline end-to-end. The **useful, robustness-bearing** policy is **B2** (a DR set teaches invariance to init-distribution variation) — which is exactly the "distill the already-DR-robust deterministic route, then add DR" unit the P2 pre-check recommended (`P2_PRECHECK_CROSSPV_OPSSUP.md:51`).

---

## §5. RISKS + conservatism directions (charter item 5, mandatory)

| Risk / claim | Direction | Note |
|---|---|---|
| Single-demo overfit | — | B1 = shakedown only (§4); do NOT read B1 success as "policy works." |
| **Reach-knife-edge inheritance** | **NON-CONSERVATIVE** | the demo sits on the cuda:0-specific R-reach wall (`P3 spec:131,145-149`); BC inherits a trajectory with ~0 reach margin → sharpens P1 risk④ reach-fragility; a small pose shift (B2 DR) may fall off the edge → reach-margin is a first-class robustness gap. |
| Device-fragility | **NON-CONSERVATIVE** | cuda:0-only reproduction + GPU non-det → eval on cuda:0, pass over N rollouts; cpu cannot even evaluate (BLOCKED). |
| **Perfect-state obs dependence** | **NON-CONSERVATIVE for real** | the base targets the actual cable with SIM PERFECT state (`test:4335`); a BC policy conditioned on perfect cable-seg pos inherits it → no sim2real gain over the base UNLESS B2 trains on **noisy/estimated** pose (the real payoff, Rs-range-gated). |
| Substep fidelity (SIM_SUBSTEPS=10) | **NEUTRALIZED (advantage)** | the evaluator MATCHES the demo's substeps exactly (§3) — the one place B is strictly better than the RL-env path. |
| Long-horizon drift (~2000 steps) | **NON-CONSERVATIVE** | open-loop compounding; B0 measures it; closed-loop obs (EE pos) helps but the horizon is long. |
| §4 kinematic route + retain-vs-load (row54) | **fidelity boundary (banked)** | BC imitates the physics — it **cannot** make the kinematic route segment physical, and it imitates a **sliding cradle** (`P1_VERDICT.md §2`, row54), not a load-bearing grip. Carried, not B-fixable. |
| pin-ON embedded in the demo | **NON-CONSERVATIVE vs pinless** | the demo learns C1-stays-seated dynamics whose cause (the eq-pin) is absent from obs (`P3 spec:135-138` §運用21 class) → Rs Q (§7). |
| cg-GPU whole-route validity | **UNKNOWN → must screen** | CPU-finite ≠ GPU-safe (`P1_VERDICT.md §2` check1); the evaluator runs cuda:0 = the screen itself, but bank nothing until it passes N. |

---

## §6. L-TRIAGE + phased plan (charter item 6)

**Per-piece L (Stage-1 estimate; final = Rs/§運用2 [L-TRIAGE]):**

| Piece | New file(s) / LOC | L | Gates |
|---|---|---|---|
| Converter `route_demo_to_bc.py` | ~100–200 LOC, pure data transform, no solver/reward/phase LOGIC | **L2** (new file) | rule-check stage2; 層3 mechanical |
| Trainer wrapper (reuse `bc_pretrain.py`) | ~0–60 LOC CLI wrapper | **L1–L2** | reuse-with-flags; no env |
| Evaluator `policy_route_runner.py` (SEPARATE runner, imports route building-blocks, verdict re-implemented) | ~200–400 LOC | **L2** if no edit to the locked `test_newton_clip_routing.py`; **L3** if verdict-refactor path (b) chosen (§3 fork) | **`/pre-check`** (has SUCCESS CONDITIONS — charter); 層5 if ≥3 code files touched |

- **`/reward-design` = N/A** (B has NO reward — pure supervised imitation). **`/pre-check` = required** on the evaluator (success conditions).
- **No GPU-10h HIGH-COST-GATE** for B (§2). Evaluator cuda:0 rollouts = inference scale.
- **Phased build order:** P-B0 (converter + open-loop replay evaluator → validate reproduction) → P-B1 (reuse `bc_pretrain.py` + policy rollout) → P-B2 (DR set, Rs-gated). Each phase small; B0 de-risks before any training. **The actual build = Rs design-gate + %12 [VERIFY]; this doc is PROPOSE-ONLY.**

---

## §7. Rs DESIGN QUESTIONS (charter item 7 — crisp)

1. ⛔ **DR range (B2 blocker, the one that gates a USEFUL policy):** what cable **pos/pose/shape** range must the BC demo-SET span for deployment? Knob exists (`CABLE_XY_DR_AMPLITUDE=±20mm`, `task_config.py:264`) but is a within-工程 demo-aug, **SUPERSEDED 2026-06-24** to a deploy requirement with the **range + retrain wiring unspecified = Rs to spec** (`task_config.py:257-262`); SHAPE/bending = a separate Stage-B/C axis.
2. **B1 pass-bar ratification:** accept "fingerprint **category** match over N cuda:0 rollouts" (NOT bitwise) + ratify **N** (given GPU non-det)?
3. **Gripper representation:** accept **scripted-in-evaluator** for B0/B1 (imitate arm motion only), deferring gripper-as-action to a later variant?
4. **pin-ON in training data** (INVARIANT#5-adjacent, `P3 spec:135`): may the BC demo embed the authorized C1 eq-pin (whose cause is unobserved), or must it be flagged/excluded?
5. **Device-fragility acceptance:** accept **cuda:0-only** evaluation + the reach-knife-edge as a known robustness gap, or require a reach-margin fix first? (A re-grasp-geometry change would touch the Rs-LOCKED square-on route → STOP-and-flag.)
6. **Evaluator verdict extraction (L fork):** re-implement the fingerprint in the separate runner (recommended, keeps the locked route file clean, L2) vs refactor it into a shared callable (edits Rs-LOCKED `test_newton_clip_routing.py`, L3 + anti-revert)?
7. ⛔ **INVARIANT STOP-check:** position-only actions keep `solve_ik_dual` (DiffIK, constant Rx(−90°) ori) → **INVARIANT#3 preserved** (the policy just omits inert ori-deltas); span/dual-arm/コ/kinematic all untouched. **No INVARIANT change proposed** — flagged per charter for confirmation.

---

## §8. Summary + the single biggest design fork

**B is a clean, low-risk pipeline:** REUSE `bc_pretrain.py` (pure offline BC, no env, **no GPU-10h gate**) + a NEW converter (pose-Δ, position-only, lean obs) + a NEW policy-rollout evaluator (imports the route building-blocks, seam CLEAN, substeps MATCH the demo, cuda:0). No INVARIANT change. 先祖返り clean.

**The single biggest design fork = the CONVERTER action semantics + evaluator granularity:** **(i) per-control-step position-Δ** (recommended — a reactive, deployable BC policy through `solve_ik_dual`; apply-path faithful-not-identical → B0 de-risks) **vs (ii) per-macro-move commanded-target** (byte-identical apply path but a ~16-decision waypoint scheduler, not a reactive controller). Choosing (i) commits B to a genuine per-step policy validated by B0 open-loop replay; choosing (ii) makes B closer to scripted replay. **The strategic corollary Rs must weigh:** B1-on-a-single-demo is a **pipeline shakedown** (deterministic + perfect-state + cuda:0-knife-edge route → overfit replay); the **robustness-bearing** policy is **B2**, gated on the **DR-range decision (Q1)**. Recommend building **B0 → B1** now (cheap, no HIGH-COST-GATE) to stand the pipeline up, and resolving Q1 in parallel to unblock B2.

**0-commit, HEAD `bcb7393ec8`, INVARIANTS #1-5 untouched. READ-ONLY scoping — no source/spec/07-Design edits. %11's WT recorder files untouched.**
