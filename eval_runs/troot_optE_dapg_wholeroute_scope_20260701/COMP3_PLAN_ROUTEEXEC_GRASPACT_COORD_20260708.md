---
doc_class: design-surface
---

# COMP3 PLAN v2 — route-executor Stage-B grasp_actuation flag-flip + FORK-1 close-kinematics validation — %11 COORD (w2:p3)

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec (IN_PROGRESS) — charter %12, D-1=C.
**rev:** **v2** (2026-07-10 06:4x) — folds 5体 [VERIFY] DECIDE=REVISE (`c80a546f6c`, verdict COMP3_5TAI_VERIFY_VERDICT_RSTECHLEAD_20260710.md): CRITICAL×3 (K1/K3/K4) + CRIT-adjacent K2 + MED/HIGH + CC1 rulings R1-R8, all ACCEPTED (no REBUT). v1 = `d718acc7f8` (%12 [VERIFY] PASS on grounding/STAGED-GAP/CC4-C1, superseded on substrate/reset/grip/L1/scope).
**PLANNING only (no-GPU, structural). Build FORBIDDEN until: fold → CC1 focused re-gate → /pre-check + scoped /reward-design + prior-art → RULE-CHECK → build (no-GPU legs only). GPU G1 HELD behind /production-launch-gate + Rs surface.**

---

## §D. v2 DELTA (fold map — 5体 accepted findings + R1-R8)
| ruling | finding (lens) | fold |
|---|---|---|
| **R1** | K1 :670 reset defect (4 lenses CRIT) | :670 = **AR-precedent reset** (28-wide reset-init incl gripper + per-world servo re-seed to OPEN + gripper qd=0 + k≥1 hard-guard), NOT arm-only NOR banked-restore. :440/:791 = the arm-only flag-ON sites. §5. |
| **R2** | K2 grip radians data-path (3 lenses CRIT-adj) | replay recorded grip_cmd **staircase EXACT** per-physics-frame (incl 0.667 cage90 / 0.69 half-hold, [L,R]→per-arm, NO threshold/smooth/re-ramp) via a RouteExecutor-owned accessor. route_executor.py enters file set. force-design (a) reworded. §6. |
| **R3** | K3 substrate = mujoco-CPU newton single-world (CC1-confirmed §運用28) | §2 "cuda:0-cg MATCHED" = FALSE → **mujoco-CPU newton (env as-coded), world-0/nominal**; comp3 does NOT touch make_solver/base; worlds≥1-frozen → **Rs escalate (separate campaign item)**. §7. |
| **R4** | CC4-CH3 no cable-offset (HIGH) + CC5-CH5 ⑦(b)=code (HIGH) | G1 = **nominal-cell only**; tail-cells (needs DoD⑦ offset) + k≥1 G2 (needs ⑦(b) cable re-seed CODE) → **comp3b registered follow-on**. §13. |
| **R5** | K4 L1 conflation (2 lenses CRIT) | pre-GPU flag-OFF = static diff + **no-GPU CPU write-pattern unit** (mocked phys_jq/jqd, flag-OFF==current byte-equal). runtime golden (B⑨a′-class incl gripper) = **GPU-cost leg** into Rs G1. STOP citing dod9a_prime 25/81 as write-site coverage. §12. |
| **R6** | K7 obs/FK desync (2 lenses MED) | :747-749/:777-780 FK warm-start kept AS-IS both flags (NOT servo surface). flag-ON obs[7]/[15] = **physics joint_q readback**. obs table + L4 assert. §11. |
| **R7** | CC5-CH1/CH3/CH6/CH8/CH10 process (HIGH×2 + MED×2 + LOW) | chain: **/pre-check + scoped /reward-design** (my own dispatch gap, CC5-CH1) + prior-art script + §運用15 層3/層2(post)/層5 after build + video skill-path + validation-artifact file enumeration + §1 size. §14. |
| **R8** | K5 flag-matrix + K6 seed-assert + CC3-CH5/CH6 + CC4-CH5 (MED/HIGH) | cfg bool-assert + `grasp_actuation⇒route_executor_impl=="route_executor"` fail-loud; env-owned index maps; **discriminating servo readback** (POSITION+ke/kd/effort+negative-control) replaces vacuous seed-assert; `.assign()` write-pattern + device readback; mjw-eq-deferred pinned; `_settled_fk_jq` gripper patch AR:866-872. §10. |

**CC6 NHA = CHANGE_JUSTIFIED** (No-Action fails: DoD live legs undischargeable with fingers pinned OPEN). Conditions 1-7 ADOPTED; **route_executor.py edit ⇒ re-run byte-repro ref-leg self-check** before claiming banked 81/81 stands; ZERO drift into task_config.py / newton_skill_env_base.py / locked test file (substrate finding does NOT authorize touching make_solver — R3). §16.

> **2026-07-10 supersession (5tai verdict a35cb359a0 / fix 65b5b9dd21 + folds):** the flag-OFF byte-identity/byte-preserve claim is SUPERSEDED at the EE-Z floor clip site (newton_route_env.py, _apply_actions_batch target z clamp) — the lane-aware floor (Rs adjudication B) is an env-core latent-defect fix common to BOTH flags: flag-OFF close-window + descend targets change by <=3.12mm (achieved-col window start {896..900}, target-col from {859..863}). All other flag-OFF surfaces remain byte-preserved.

---

## §0. Grounding (anchor set, §運用4) — read + cited (v1 §0 + verdict)
v1 anchor set (LEDGER:47 / node / build plan v0.2.2 / verdict / live code base:1492/1537/1586/1738/1905 / route env:391/440/670/791 / route_executor:80/181/206/229) + **5体 verdict `c80a546f6c`** + **K3 §運用28 re-verify (my own reads): USE_MUJOCO_CPU=True task_config:116 / make_solver solver="newton" hardwired :1329/:1338 / route env patches SOLVER_BACKEND only :96/:101 / build plan §6 "81 sequential single-cell" = multi-world never live-exercised** + AR reset precedent (newton_aerial_regrasp_mujoco_env.py:1084-1104 verified) + AR gripper patch (:866-872 verified).

## §1. [TASK]/[L-TRIAGE] = L3 (size corrected, CC5-CH9)
path-match (newton_route_env.py) + diff-keyword (grasp_actuation/servo/physics/ik) → L3 high-care, invariant-PRESERVING (NOT immediate-STOP; Rs=A `bad0d25204`). **size: bundle ~40-95 LOC but grows with R-fixes; 1-2 files {newton_route_env.py, route_executor.py}. L3 stands via path/keyword regardless of size prong** (v1 ">200L/≥3 files" over-stated — corrected).

## §2. comp3 objective = FORK-1 close-kinematics on the env's AS-CODED substrate (R3-corrected)
FORK-1 = does the gripper CLOSE+CAGE+HOLD the cable in **the route env as-coded**? SRG proved grip ROBUST on build_scene (cuda:0-cg + cpu-newton de-confound); comp3 validates the env-drive path. **Substrate delta table (R3-CORRECTED):**
| axis | build_scene (SRG) | build_multiworld route env (AS-CODED) | conservatism |
|---|---|---|---|
| solver | cuda:0-cg (S1/S2) **AND cpu-newton (de-confound)** | **mujoco-CPU newton (USE_MUJOCO_CPU=True, solver="newton" hardwired)** | ⭐**route env = the cpu-newton SRG de-confound found FIRMER (holds TIGHTER) = conservative-FAVOURABLE prior** |
| worlds | 1 | **1 effective (single_world_template; worlds≥1 FROZEN as-coded)** | multi-world NOT covered (R3 Rs-escalate) |
| arm drive | scripted grasp_cable | `_apply_actions_batch` kinematic write (:791, arm-only flag-ON) | env-drive NEW |
| grip drive | single jump (srg_probe:307) | **recorded grip_cmd staircase EXACT replay** (R2) | schedule fidelity NEW |
| env-replay substep | 4 (SRG cage-escape ran 4) | RL_SIM_SUBSTEPS=4 | MATCHED (grip HOLD @4 = SRG-validated) |
| ⚠ recording-gen substep | — | run_route generated the ee_pos+grip staircase at **SIM_SUBSTEPS=10** (route_executor physics_step; task_config:101) | **NOT matched — /pre-check ISSUE 1**: a 10-substep-recorded schedule replayed at 4-substep contact solve; **direction UNKNOWN** (grip close is contact/force-limited) → G1 caveat, NOT folded into the favourable prior (aligns w/ known substep 4→N Rs-level carry, build plan §7) |
| void geom | [0.090,0.210] | [0.090,0.210] (base:1738) | PARITY (SRG void-gate) |
⇒ the genuinely-unproven delta = env-drive path + recorded-staircase grip (10→4 substep transfer) + reset semantics; the substrate SOLVER (cpu-newton) is the SRG-de-confound FIRMER one = favorable, **but the 10→4 recording-replay substep delta is a separate axis, direction unknown (ISSUE 1)**. **"cuda:0-cg MATCHED" (v1) was FALSE.**

## §3. %9 grasp_actuation gap = STAGED-GAP (UNCHANGED — %12 [VERIFY] PASS v1)
build_multiworld_scene signature accepts `grasp_actuation=False` (base:1492); :391 un-passed = intentional env-core byte-preserve default (CC4-SOUND byte-clean-by-construction). 5 evidences + test:3715 CONSISTENT (Stage-A recorded_replay=live-CUT ⇒ OFF legit / Stage-B comp3 ON ⇒ satisfies test:3715). comp3 ADDS the kwarg flag-gated. **NOT a wiring-omission.**

## §4. comp3 mechanism = grasp_actuation flag-flip (newton_route_env.py:391)
cfg flag `cfg["grasp_actuation"]` (bool, default False); pass to build_multiworld_scene :391. flag-OFF = env-core byte-identity; flag-ON = 4 base mutations (§8). **R8 guard: `grasp_actuation=True ⇒ route_executor_impl=="route_executor"` fail-loud (K5: True+stub = servo with no grip writer = silent inert-grip).**

> **2026-07-10 supersession (5tai verdict a35cb359a0 / fix 65b5b9dd21 + folds):** the flag-OFF byte-identity/byte-preserve claim is SUPERSEDED at the EE-Z floor clip site (newton_route_env.py, _apply_actions_batch target z clamp) — the lane-aware floor (Rs adjudication B) is an env-core latent-defect fix common to BOTH flags: flag-OFF close-window + descend targets change by <=3.12mm (achieved-col window start {896..900}, target-col from {859..863}). All other flag-OFF surfaces remain byte-preserved.

## §5. Write-site flag-gate — R1-CORRECTED (3 sites, DISTINCT semantics)
CC4-C1 invariant (flag-OFF = 28-wide gripper-pinned byte-exact) STANDS. But the 3 sites are NOT uniform (v1 error — R1):
| site | fn | flag-OFF | flag-ON (comp3) |
|---|---|---|---|
| :440 | `_broadcast_arm_jointq` | 28-wide `phys_jq[:28]` | **arm-only** `apply_arm_only_write_broadcast` (gripper {6-13,20-27} untouched → servo drives) |
| :791 | `_apply_actions_batch` drive | 28-wide `phys_jq[:28]`+`phys_jqd=0` | **arm-only** `apply_arm_only_write_perworld` (gripper coords servo-DYNAMIC) |
| **:670** | `_reset_worlds` | 28-wide reset-init `phys_jq[:28]`+`phys_jqd=0` | ⭐**AR-precedent reset (NOT arm-only, NOT banked-restore)**: keep 28-wide reset-init incl gripper (prohibited.md reset-init EXCEPTION; AR:1084-1093) + **per-world servo-target re-seed to route step-0 grip = OPEN both arms** — as-BUILT = `RouteExecutor.reseed_grip_open(env_ids)` (internally `maps["l/r_driver_dofs"][w]` → `set_gripper_target` → single `.assign()` + device readback; S-F4 fold 8b で本行を as-built に整合) (AR:1095-1104 mirror; ⚠ route step-0 = both-OPEN, NOT AR's L-close/R-open — dual-arm role ADAPT) + gripper qd zeroed. |
- **⚠ k≥1:** `reset_to_phase(k≥1)` stays OUT of `_reset_worlds` (full-reset channel only) + hard-guarded (assert/NotImplemented) until ⑦(b)/comp3b. bank omits k=0 (route_executor:339 phases=(1..5); reset_to_phase(0)=no-op :3172).
- **⚠ per-world-subset vs all-world (K1c):** `_reset_worlds(env_ids)` is a subset; the servo re-seed loops `for w in env_ids` (NOT all-world clobber). single-writer invariant (CC2-CH8): `apply_banked_restore`=sole RESET-time writer / `set_gripper_target`=sole PER-STEP writer.
- comp3⊕comp4 INSEPARABLE (bundle).

## §6. Grip drive — R2 (recorded staircase EXACT per-physics-frame)
- ⛔ **NO thresholding/smoothing/re-ramping.** The proven schedule = engineered jumps + staircase (NOT a smooth ramp — v1 force-design "proven ramp, no jump" was a MISCHARACTERIZATION, R2): L_HALF_UNCLAMP transit hold (L=0.69 while R re-grasps, run_route:2071/2091/2418), cage90 staircase (instant→0.667 then 12×12 to 0.7407, :1565-1577). SRG itself closed with a single jump (srg_probe:307).
- **mechanism = RouteExecutor-owned accessor/applier** (it owns `_recording`/`_maps`/`_control`): a new method that reads `_recording["grip_cmd"]` [L,R] at physics frame `cf[t]+i`, splits [L,R]→per-arm driver dofs (`_l_driver_dofs`/`_r_driver_dofs`), and applies via read→mutate→`.assign()` (§10 CC3-CH5). Called inside the env drive loop per physics frame. **route_executor.py enters the declared file set.**
- ⚠ **[L,R] footgun** (:3206-3208): recording cols are [L,R]; assert the per-arm mapping.
- **per-frame = per-PHYSICS-frame** lookup (cf[t]+i inside drive loop; CC3-CH9); NOT per-RL-step (would ≤9-frame-quantize the staircase).
- L4 unit: pin a transit-window frame (L target==0.69 ∧ R target==0.0) + the [L,R]→per-arm mapping.

## §7. Substrate — R3 (mujoco-CPU newton, world-0/nominal; worlds≥1 → Rs escalate)
- G1 runs on the env's **as-coded production substrate**: mujoco-CPU newton stepping (warp arrays on cuda:0), world scope = world-0/nominal. comp3 does NOT touch make_solver/base (zero drift, R3/CC6).
- ⭐**favorable:** this cpu-newton substrate is the one SRG's de-confound found holds TIGHTER (0.09/0.54mm vs cuda:0-cg 1.53/6.93mm) = conservative-FAVOURABLE prior for G1.
- **worlds≥1-FROZEN escalation (Rs, SEPARATE campaign item):** the as-coded env cannot live-step worlds≥1 (single_world_template → nworld=1; CC3 empirical world1 dz==0). Affects any FUTURE multi-world RL training. Options = GPU-mjwarp+cg plumbing (base L3, r_s66 #1415 constraint) vs single-world training. **Rs-level, NOT comp3 scope.**
- **reconcile (R3, verified §運用28):** env-core ⑨a′ ran **81 sequential single-cell** (build plan §6) → multi-world legs were predicate-only/offline → the freeze was NEVER exercised (consistent, recorded here).
- G1 verdict MUST carry loud: multi-world leg NOT covered / GPU-cg leg NOT covered.

## §8. 4 grasp_actuation mutations + geometry (UNCHANGED — /geometric-design PASS)
condim6 (:1537) / POSITION servo drivers [6,10,20,24] (:1586, ke=66.7/kd=2.0/eff=2.5N) / table VOID 4-box (:1738, solid→void) / `_wire_s6_grasp_solref` (:1905, PAD_SOLREF mj+mjw). Geometry PARITY SRG-validated (void [0.090,0.210]); H1-H4 satisfied (COMP3_GEOMETRIC_DESIGN_VOID). **CC3-CH6: 4-bar eq stiffening = mj_model-template-only; mjw eq re-poke DEFERRED by design (base:1355-1358) — comp3 FORBIDS mjw eq re-poke; pin the documented state.**

## §9. Design-gate (both run; force reworded per R2/R3)
- /force-design (COMP3_FORCE_DESIGN_SERVO, PASS-LIGHT) — **constraint (a) REWORDED (R2):** servo target = recorded grip_cmd staircase EXACT per-physics-frame (jumps+holds ARE the proven schedule; NO re-ramp). substrate note (R3): grip runs cpu-newton (SRG de-confound firmer). params inherited (KE66.7/KD2.0/EFF2.5, task_config:314-316).
- /geometric-design (COMP3_GEOMETRIC_DESIGN_VOID, PASS) — void re-confirm, UNAFFECTED by substrate.
- **R7 ADD: /reward-design SCOPED to flag-ON delta** (predicate reachability under live grip + obs table under R6) + **/pre-check on the bundle diff** (post-fold, pre-RULE-CHECK; BLOCK → no build). These were MY dispatch gap (CC5-CH1).

## §10. Guards — R8 + singles
- cfg flag **bool-type assert** + `grasp_actuation ⇒ route_executor_impl=="route_executor"` fail-loud (K5; cfg.get truthiness hazard).
- **env-owned per-world index maps** built at END of `_build_model` (post-:417, pre-settle) via `build_perworld_index_maps` (single-source with rex maps; K5: `_broadcast_arm_jointq` runs before RouteExecutor exists → env must own maps).
- **discriminating servo readback (replaces vacuous seed-assert, K6)** on the authoritative model per R3: `joint_target_mode[drivers]==POSITION` + ke==66.7/kd==2.0/effort==2.5 + **negative control** (a non-driver dof carries NO servo ke). seed-assert (OPEN_RAD) kept as SECONDARY only.
- **`.assign()` write pattern + device readback assert** (CC3-CH5): set_gripper_target on a `.numpy()` host copy never reaches the solver → mandate read→mutate→`.assign()`. ✅ **%12 citation CORRECT (my prior §運用28 counter-read was WRONG — I grepped the wrong file, test_newton, hitting cable_cfg): `route_executor.py:967-974` IS `def _set_gripper_target(control, driver_joints, target_rad)` = the exact read→mutate→`.assign()` (`tp=control.joint_target_pos.numpy()` → `tp[d]=target_rad` → `control.joint_target_pos.assign(tp)`).** ⇒ **the accessor EXISTS**: R2's per-frame applier REUSES `_set_gripper_target` (already the schedule writer for the recorded staircase — cage90 :1567/:1573, L_HALF_UNCLAMP :2071, R-OPEN :2091, L-CLOSE :2418) with the per-arm driver dofs + the recorded grip_cmd value at cf[t]+i. + device readback assert.
- **`_settled_fk_jq` gripper patch (CC4-CH5)** flag-ON: mirror AR:866-872 — after settle, overwrite gripper coords {6-13,20-27} in `_settled_fk_jq` with world-0 post-settle PHYSICS gripper config (else 4-bar follower branch-flip). ⚠ route step-0 = OPEN (not AR's L-close).
- **mjw-eq-deferred** caveat pinned (CC3-CH6); forbid mjw eq re-poke in comp3.

## §11. Obs — R6
:747-749/:777-780 FK warm-start pinning kept AS-IS BOTH flags (IK bookkeeping, fk_jq, NOT the servo surface — v1 item-3 re-purposing was a category error, K7). **flag-ON obs[7]/[15] = physics joint_q readback** (per-world driver coords), NOT FK-side (which would lie flag-ON). obs table in plan; L4 asserts the flag-ON obs source.

## §12. L1 honesty — R5 (K4)
- **pre-GPU flag-OFF evidence (no-GPU):** (a) static code-diff (flag-OFF branch == current) + (b) **no-GPU CPU write-pattern unit** — mock/capture phys_jq/jqd over a step, flag-OFF vs current == byte-equal (this ACTUALLY exercises the write-sites, unlike dod9a_prime).
- ⛔ **STOP citing dod9a_prime 25/81 as write-site coverage** — it is predicate-only (loads recorded cable states; never exercises write-sites; a write-site bug passes it unchanged). The monolith sha harness regresses the EXTRACTION path, not env write-sites.
- **env-side runtime golden (B⑨a′-class full joint_q sha incl gripper, fixed seed, K steps + ≥1 done-reset) = a GPU-cost leg** (route warp = cuda:0) bundled into the Rs G1 surface — NOT a no-GPU leg.

## §13. G-scope — R4 (+ /pre-check ISSUE 2/3 folds)
- **G1 (comp3) = nominal-cell GRASP/LIFT legs ONLY (層2/5 fold 9 再定義, G-F3)** on the R3 substrate (cpu-newton), world_count=1. creep-budgeted (SRG method). **C1-seat 以降 (seat/pin/transit/C2) は G1 から除外** — 録画 schedule の下流 leg は G-F1 (support-clip topology) 裁定後の別 row。video skill-path (/verify-run or /video-analyzer + video-analyst) + human-GT (CC5-CH10)。GPU-cost → /production-launch-gate + Rs surface。
- **G1 PRECONDITIONS (fold 9):** (a) **Rs support-clip 裁定 (G-F1b)** — A: `add_support_clips=False` で録画基盤に整合 (%12 推奨) / B: clips 維持 + 期待値再基準化。probe leg G の cable-parity 実測が判断材料。(b) **mjw-eq-deferred pin (P-F6)** — G1 は CPU substrate (mj_model authoritative) で走る前提; 将来 GPU-cg leg を張る場合は mjw eq re-poke が先行必須。(c) **nominal-provenance assert (G-F2)** — flag-ON env は録画 sha == RUN1_REFERENCE_V2 を build 時 assert (wired)。
- ⚠ **/pre-check ISSUE 2 — PIN `world_count=1`** (env default `__init__ world_count=4` :252; worlds≥1 FROZEN would contaminate any batch metric). "world-0/nominal" ≡ a SINGLE-world build, NOT world-index-0 of a 4-world batch. Apply to G1 run spec AND the L2 CPU probe.
- ⚠ **/pre-check ISSUE 3 — close-frame contact zoom** (§運用14): the env IK-interpolates arm joint_q LINEARLY over 10 frames (:786) while the grip staircase fires per-physics-frame → the close can act on a not-yet-arrived (joint-linear) arm pose ≠ the recorded nonlinear IK descent (close-on-transient risk). G1 video MUST zoom the pad↔cable contact AT the close frame, not only end-of-episode hold.
- ⚠ **/pre-check ISSUE 1 caveat carried:** G1 verdict states the 10→4 recording-replay substep delta (direction unknown) alongside the multi-world-NOT-covered / GPU-cg-NOT-covered caveats.
- **comp3b (registered follow-on, descoped):** tail-cells (needs DoD⑦ cable-offset wiring — env has `dr_xy=(0.0,0.0)` hardcoded :680, CC4-CH3) + k≥1 fork divergence G2 (needs ⑦(b) cable re-seed CODE — CC5-CH5). ⚠ **⑦(b) MUST carried loud** (build plan §8-B): build_state_bank cable_xyz capture + env-level seed_cable_joint_state offset-aware.

## §14. Process chain — R7 (supersedes v1 §11 first hops)
fold → **CC1 focused re-gate** → **/pre-check (bundle diff) + scoped /reward-design + prior-art script** (`check_thread_vault_prior_art.sh --fail-on-blocker grasp_actuation gripper overwrite inert-grip write-site servo`, attach output, STOP on blocker w/o recorded delta) → **RULE-CHECK stage2** → **build (no-GPU legs L-set)** → **§運用15 層3 (mechanical -f/tests) / 層2 (post-debate on-disk) / 層5 (multi-view)** → **/production-launch-gate + Rs surface (G1 GPU + worlds≥1-frozen escalation as separate item)**.

## §15. PROPOSE file set (CORRECTED) + validation-artifact files (CC5-CH8)
- **code file set = {newton_route_env.py, route_executor.py}** (v1 named only newton_route_env.py; R2 adds route_executor.py for the radians accessor). ZERO drift into task_config.py / newton_skill_env_base.py / locked test file.
- **validation-artifact files (named now, no un-named files at build):**
  - L1 static-diff: inline in re-gate (git diff flag-OFF branch).
  - L1 CPU write-pattern unit + L4 wiring/obs/grip-staircase unit: **extend `test_routeexec_state_bank.py`** (or sibling `test_routeexec_writesite.py`) — mock phys_jq/jqd, flag-OFF byte-equal + flag-ON gripper-excluded + transit-window grip (L=0.69∧R=0.0) + flag-ON obs source.
  - L2 void-parity readback (no-GPU): **new probe `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_void_readback.py`** (build_multiworld flag-ON CPU, void formula + no claw↔table artifact + mj/mjw solref per R3=mj authoritative).
  - L3 servo readback (discriminating): in the same probe or unit.

## §16. CC6 conditions (ADOPTED) + drift guard
- route_executor.py additions (radians accessor per R2) IN scope; **any route_executor.py edit ⇒ re-run the byte-repro ref-leg self-check** before claiming banked 81/81 stands.
- ZERO drift into task_config.py / newton_skill_env_base.py / locked test file MAINTAINED (substrate finding does NOT authorize touching make_solver — R3).

## §17. Risks
substrate-transfer (env-drive path; G1 measures; but cpu-newton = SRG-firmer favorable) / worlds≥1-frozen (Rs campaign item, NOT comp3) / grip-staircase fidelity (EXACT replay; L4 unit) / reset semantics (AR-precedent; L1/L4) / device-robust grip write (.assign() + readback) / obs flag-ON source (R6; L4).

## §18. Prior-art / no-repeat disposition (R7, VaultProtocol V10 — gate (1) run 2026-07-10)
`check_thread_vault_prior_art.sh --fail-on-blocker grasp_actuation gripper overwrite inert-grip write-site servo` = findings=30, blockers=30. **Classified — NO genuine do-not-repeat path violated; concrete delta recorded:**
- 18/30 = **this node's own earlier build plan** (BUILD_PLAN_ROUTEEXEC_COORD_20260707) — self-reference, not a foreign failed path.
- 7/30 = **AR grasp_actuation PROVEN precedent** (AR_BUILD_RESULT: `build_multiworld_scene(grasp_actuation=True)` wired + fail-loud assert + world-0 servo closes 0.0018→0.7424; VOID_CROSSPV 4/4 PASS) = the mechanism comp3 REUSES (supportive, not a repeat).
- B0_BUILD_REPORT: "servo on `vbd_control` — **never a fresh control**" = exactly the device-robust `.assign()` pattern R2/CC3-CH5 mandates (supportive).
- **S-2 (CRITICAL keystone):** friction-only grasp CANNOT hold the 45g cable in-sim (all-FAIL static hold) → drove the 爪/form-closure pivot. ⇒ **plan RESPECTS it** (koshape form-closure CAGE, SRG cage-hold confirmed — NOT friction-only).
- **D2 S-4 (MED, FLAGGED):** scripted-kinematic finger close (joint_q overwrite) brushes SOMA no-kinematic-trick. ⇒ ⭐**plan DIRECTLY GUARDS it** — comp3 uses the POSITION servo (grasp_actuation restores the actuated 4-bar); comp4 EXCLUDES the gripper from the 28-wide joint_q write so the finger closes by PHYSICAL PD, NOT kinematic overwrite.
- **CONCRETE DELTA (VaultProtocol V10):** plan v2 uses the proven AR actuated POSITION-servo form-closure (gripper excluded from the kinematic write), avoiding BOTH friction-only-hold (S-2 FAIL) and scripted-kinematic-close (S-4 SOMA-brush). ⇒ proceed authorized to gates (2)/(3); **BUILD itself remains %12's auth** (not taken here).

## §19. /pre-check disposition (gate (2), run 2026-07-10) = PASS
skeptical sub-agent (read code end-to-end, not plan-on-faith) = **VERDICT PASS** (0 critical / 0 high / 2 medium / 1 low). **All R1-R8 VERIFIED SOUND** (none insufficient). CONFIRMED (non-issues): write-site completeness = exactly 3 gripper joint_q sites (:440/:670/:791), NO missed 4th per-step site (`assign_world_states_to_sim` writes body only; `seed_cable_joint_state` cable only) → inert-grip defect CLOSED; grip writer genuinely new + `_set_gripper_target` device-robust + `_REC_CADENCE=10==PHYSICS_STEPS_PER_RL` cf[t]+i 1:1; reset re-seed→OPEN + `_settled_fk_jq` patch close the cross-episode leak; no-kinematic-trick RESPECTED; zero drift (grasp_actuation gates pre-exist in base; env only passes kwarg :391). **3 folds (pre-build, non-blocking):** ISSUE 1 (MED) 10→4 recording-replay substep delta = §2 caveat, direction unknown / ISSUE 2 (MED) pin world_count=1 = §13 / ISSUE 3 (LOW) close-frame contact zoom = §13. None block the no-GPU legs; G1 stays behind /production-launch-gate + Rs.

---
*%11 COORD (w2:p3) v2 2026-07-10. Folds 5体 DECIDE=REVISE (c80a546f6c), all R1-R8 + accepted findings, no REBUT. K3 substrate CC1-confirmed + §運用28 re-verified by me. PLANNING only. → %12 focused re-gate → /pre-check + scoped /reward-design + prior-art → RULE-CHECK → build no-GPU. GPU G1 + worlds≥1 escalation = Rs surface.*
