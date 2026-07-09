# comp3⊕comp4 5体 [VERIFY] VERDICT — RS-TECH-LEAD (%12, CC1) — 2026-07-10

**Object:** COMP3_PLAN_ROUTEEXEC_GRASPACT_COORD_20260708.md (`d718acc7f8`) + design-gate outputs (`4394525821`) + the PROPOSE diff-shape (pre-implementation).
**Structure:** CC1 (me) PROPOSE → CC2 (byte-preserve) / CC3 (servo physics) / CC4 (multi-world/reset) / CC5 (process/rules) Challengers + CC6 (NHA), parallel, independent contexts → REBUT_OR_ACCEPT → NO_ACTION_EVALUATION → DECIDE.
**Raw challenge outputs:** agent transcripts (session f533c023); inventory below is the complete list (no silent dismissal).

---

## DECIDE = **REVISE** (Layer-B precedent pattern: fold → CC1 focused re-gate → RULE-CHECK → build)

- NHA (CC6) = **CHANGE_JUSTIFIED** — No-Action rejected (see §NO_ACTION below). The change itself remains authorized in direction.
- But ACCEPTED CRITICAL×3 + HIGH×10 mean the plan AS WRITTEN cannot proceed to build. All accepted findings + CC1 rulings R1–R8 must be folded into plan v2, then CC1 focused re-gate, then RULE-CHECK (+ /pre-check + scoped /reward-design + prior-art script), then build (no-GPU legs only).
- ⛔ GPU G1 remains HELD behind /production-launch-gate + explicit Rs surface (unchanged).

## CC1 independent verification of the pivotal CRITICAL (§運用28)

CC3-CH1 (substrate) — **CONFIRMED by my own reads** (not taken on agent authority):
- `configs/task_config.py:116` `USE_MUJOCO_CPU = True`; `newton_route_env.py:94-101` patches ONLY `SOLVER_BACKEND` (grep: no use_mujoco_cpu override anywhere in the env).
- `newton_skill_env_base.py:1302` `make_solver(..., use_mujoco_cpu=USE_MUJOCO_CPU, ...)` and **`solver="newton"` hardwired in both branches** — no cg plumbing exists.
- `solver_mujoco.py` (env7, python3.12 site-packages) CPU path: single `mj_step(self.mj_model, self.mj_data)`; conversion sets `single_world_template = len(mj_data.qpos) < effective_coord_count` → `nworld = 1`.
- CC3's empirical probe (2-world CPU build via the env's call path): `mj_data.qpos len 74` vs `joint_coord_count 148`; world0 cable settles, world1 dz == 0.0 → **worlds≥1 not integrated (frozen)** on the as-coded substrate.
⇒ comp3 plan §2 delta-table row "solver | cuda:0-cg | cuda:0-cg | MATCHED" is **FALSE**; the env as-coded runs mujoco-CPU-newton (warp arrays on cuda:0), and live multi-world stepping is structurally absent on this path.

## Challenge inventory + REBUT_OR_ACCEPT (complete)

Convergent clusters first (3+ lenses → strongest):

**K1 — :670 reset defect (CC2-CH3 + CC3-CH2 + CC4-CH1 + CC5-CH4; 4 lenses) — ACCEPT, CRITICAL.**
PROPOSE items 2 and 4 were mutually contradictory at :670, and both wrong for the default k=0 reset: (a) bank intentionally omits k=0 (`build_state_bank_from_recording` phases=(1..5), route_executor.py:339; `reset_to_phase(0)`=no-op :3172-3174); (b) arm-only write at reset → gripper joint_q/qd + servo target stay episode-end-CLOSED ("grippers latched" :3191) → every episode ≥2 starts corrupted; (c) `_reset_worlds(env_ids)` is per-world-subset while `apply_banked_restore` writes ALL worlds → mid-episode worlds clobbered. → Ruling R1.

**K2 — grip radians data-path + schedule semantics (CC2-CH2 + CC3-CH3 + CC3-CH4 + CC4-CH2; 3 lenses) — ACCEPT, CRITICAL-adjacent.**
(a) No public radians channel exists: `step_target` returns thresholded grip_2 {0,1} (:3211-3213); raw per-frame radians are private `rex._recording["grip_cmd"]` [L,R] (footgun :3206-3208). (b) Binary→radian reconstruction destroys the proven schedule: L_HALF_UNCLAMP transit hold (L=0.69 while R re-grasps, run_route :2071/:2091/:2418), cage90 staircase (instant→0.667 then 12×12 to 0.7407, :1565-1577). (c) "proven ramp; no instant jump" (force-design constraint (a)) mischaracterizes the recording — the proven schedule IS engineered instant jumps + staircase; SRG itself closed with a single jump (srg_probe.py:307). (d) One `set_gripper_target` scalar call cannot express asymmetric L≠R windows. → Ruling R2.

**K3 — substrate/multi-world (CC3-CH1, CC1-confirmed above; + CC3-CH7 dependent) — ACCEPT, CRITICAL.** → Ruling R3 + Rs escalation.

**K4 — L1 evidence conflation / B⑨a′ is a GPU leg (CC2-CH1 + CC5-CH2; 2 lenses) — ACCEPT, CRITICAL (CC2 grading).**
"static diff + B⑨a′ full-arm_q sha + env-core 25/81 re-regression" conflates: dod9a_prime = predicate-only (loads recorded cable states; never exercises write-sites; a write-site bug passes it unchanged); the existing sha harness regresses the monolith-extraction path, not the env write-sites; the env-side flag-OFF golden was never built; any env rollout needs cuda:0 warp → not no-GPU. → Ruling R5.

**K5 — flag-matrix + build-order guards (CC2-CH4 + CC2-CH5 + CC3-CH8 + CC4-CH6; 3 lenses) — ACCEPT, MEDIUM.**
`grasp_actuation=True` + `route_executor_impl="stub"` = servo built with no grip writer (silent inert-grip revival); cfg.get truthiness hazard; `_broadcast_arm_jointq` runs before RouteExecutor exists → env must own its index maps. → Ruling R8.

**K6 — servo-seed assert vacuous (CC2-CH7 + CC4-CH4; 2 lenses) — ACCEPT, MEDIUM-HIGH.**
OPEN_RAD=0.0 == zero-init default → assert passes on unwired builds (empirically passes flag-OFF today). Replace with discriminating readback. → Ruling R8.

**K7 — obs[7]/[15] finger-dim desync + un-named servo call site (CC2-CH6 + CC5-CH7; 2 lenses) — ACCEPT, MEDIUM.**
:747/:777 are FK warm-start bookkeeping (fk_jq), NOT the servo surface — PROPOSE item 3's re-purposing of them was a category error; the actual per-frame `joint_target_pos` call site was never named; obs[7]/[15] read FK-side and would lie flag-ON. → Ruling R6.

Singles:
- **CC3-CH5 (HIGH) ACCEPT:** `set_gripper_target` on a `.numpy()` host copy of a CUDA warp array never reaches the solver; CPU-unit passes / GPU silently open. Mandate read→mutate→`.assign()` (the run_route `_set_gripper_target` :967-974 pattern) + device readback assert. (Note: less acute if G1 runs the CPU substrate per R3, but the assign-pattern is mandated regardless — the code must be device-robust.)
- **CC3-CH6 (MED) ACCEPT:** 4-bar eq stiffening is mj_model-template-only; mjw eq re-poke DEFERRED by design (base:1355-1358). Pin the documented state in plan §6 + L3; forbid mjw eq re-poke inside comp3.
- **CC3-CH7 (MED) ACCEPT:** "read mj+mjw solref" leg binds to the substrate decision (CPU G1 → mj_model authoritative, mjw recorded inert; GPU-if-ever → dual read as GPU preflight).
- **CC3-CH9 (LOW) ACCEPT:** pin "per-frame" = per-PHYSICS-frame lookup inside the drive loop (cf[t]+i), noting ≤9-frame quantization if per-RL-step were chosen (it is not).
- **CC4-CH3 (HIGH) ACCEPT:** env has NO cable-offset mechanism (`dr_xy=(0.0,0.0)` hardcoded :680; DoD⑦ open) → G1 "tail cells" impossible as scoped. → Ruling R4 (descope G1 to nominal; tail-cells + k≥1 behind DoD⑦/⑦(b) as a registered later row).
- **CC4-CH5 (MED) ACCEPT:** `_settled_fk_jq` gripper coords are FK constants (FINGER_OPEN_POS), not servo-settled; AR:868-872 patch (copy world-0 physics gripper coords post-settle) required flag-ON — 4-bar follower branch-flip risk otherwise.
- **CC5-CH1 (HIGH) ACCEPT — CC1's own dispatch gap:** [DESIGN-GATE] mandates /reward-design + /pre-check for env changes; I dispatched only /force-design + /geometric-design. Fold: run /pre-check on the bundle diff post-fold pre-RULE-CHECK (BLOCK → no build) + run /reward-design SCOPED to the flag-ON delta (predicate reachability under live grip + obs table) — obs semantics change under R6 makes a loud-skip inappropriate.
- **CC5-CH3 (HIGH) ACCEPT:** §運用15 L3 post-implementation layers (層3 mechanical -f/tests, 層2 post-debate on on-disk state, 層5 multi-view) were missing from the §11 chain — write them in (after build, before PLG/Rs surface).
- **CC5-CH5 (HIGH) ACCEPT:** ⑦(b) cable re-seed is CODE (route_executor.py + env), not a run; G2 as scoped promised what the declared diff cannot execute. → Ruling R4: G2 descoped from comp3; registered as its own follow-on row (comp3b) with the ⑦(b) MUST carried loud.
- **CC5-CH6 (MED) ACCEPT:** run `scripts/check_thread_vault_prior_art.sh --fail-on-blocker grasp_actuation gripper overwrite inert-grip write-site servo` before build; attach output; STOP on blocker without a recorded delta.
- **CC5-CH8 (MED) ACCEPT:** enumerate validation-artifact files in plan v2 (extend test_routeexec_state_bank.py for L4; new probe file for L2 named under eval_runs/...) — no un-named new files at build time.
- **CC5-CH9 (LOW) ACCEPT:** correct §1 size prong (bundle ~40-95→grows with R-fixes but 1-2 files); L3 stands via path/keyword regardless.
- **CC5-CH10 (LOW) ACCEPT:** bind the G1 video leg to the skill-path (/verify-run or /video-analyzer + video-analyst) + human-GT in the gate spec.
- **CC2-CH8 (LOW) ACCEPT:** restate single-writer invariant: set_gripper_target = sole PER-STEP writer; apply_banked_restore = sole RESET-time writer; unit-check both.

**REBUT: none.** Every challenge survived my check against disk; several were independently re-verified (CH1 substrate reads above; K1 bank phases + no-op read; K2 grip_2 threshold read during plan [VERIFY]).

## NO_ACTION_EVALUATION (with CC6 NHA)

- CC6 = **CHANGE_JUSTIFIED**. A0 No-Action fails: DoD legs ③⑨b live, ④⑥ live-grip, ②⑦(b) Stage-B, ⑥ video all structurally undischargeable with fingers pinned OPEN (write-sites verified); trainer reward vacuous without live grip → "defer for trainer evidence" is circular. A1 exhausted by SRG (FORK-1 is an env-wiring property). A2 = inert-grip (empirically banked defect). A3 prohibited. A4 duplicates BUILT machinery.
- CC6 conditions 1-7 ADOPTED, with condition-7 file-set amendment: `route_executor.py` additions (radians accessor/applier per R2) are IN scope; per condition 5, any route_executor.py edit → re-run the byte-repro ref-leg self-check before claiming the banked 81/81 stands. Zero drift into task_config.py / newton_skill_env_base.py / locked test file MAINTAINED (the substrate finding explicitly does NOT authorize touching make_solver — R3).

## CC1 rulings R1–R8 (fold targets for plan v2)

- **R1 (:670 reset semantics, K1):** flag-ON `_reset_worlds` keeps the **28-wide reset-init write incl gripper** (prohibited.md reset-init exception; AR:1084-1093 precedent) + per-world servo-target re-seed to route step-0 grip (OPEN) via `maps["l/r_driver_dofs"][w]` (AR:1095-1104 mirror) + gripper qd zeroed at reset. `reset_to_phase(k≥1)` stays OUT of `_reset_worlds` (full-reset channel only) and is hard-guarded (assert/NotImplemented) until ⑦(b). PROPOSE items 2/4 corrected: :670 is NOT an arm-only site; :440/:791 remain the arm-only flag-ON sites.
- **R2 (grip drive, K2):** replay the recorded `grip_cmd` **staircase EXACTLY** per physics frame — values incl 0.667 cage90 / 0.69 half-hold; [L,R] columns split to per-arm driver dofs; NO thresholding/smoothing/re-ramping. Mechanism = RouteExecutor-owned accessor/applier (it owns `_recording`/`_maps`/`_control`) called inside the env drive loop per physics frame (cf[t]+i); `route_executor.py` enters the declared file set. Force-design constraint (a) reworded accordingly. L4 unit pins a transit-window frame (L target==0.69 ∧ R target==0.0) + the [L,R]→per-arm mapping.
- **R3 (substrate, K3):** G1 runs on the env's **as-coded production substrate** (mujoco-CPU newton stepping, warp cuda:0), world scope = world-0/nominal. comp3 does NOT touch make_solver/base. Plan §2 "cuda:0-cg MATCHED" row corrected to "mujoco-CPU newton (env as-coded); GPU-cg leg NOT available without base plumbing". G1 verdict must carry loud caveats: multi-world leg NOT covered; GPU-cg leg NOT covered. **The worlds≥1-frozen finding is escalated to Rs as a SEPARATE campaign-level item** (affects any future multi-world RL training on this env; options = GPU-mjwarp+cg plumbing [base L3, r_s66 #1415 constraint] vs single-world training; decision Rs-level, NOT comp3 scope). Also fold CC3 FIX(d): reconcile with env-core node records how multi-world legs were exercised (likely predicate-only/offline → freeze never exercised — verify and record).
- **R4 (G1/G2 scope):** G1 = nominal-cell close+cage+hold on the substrate per R3. Tail-cells (needs DoD⑦ cable-offset wiring) + k≥1 fork divergence G2 (needs ⑦(b) cable re-seed CODE) = descoped to a registered follow-on row (comp3b), owners named, MUSTs carried loud. comp3's own G-scope = G1 only.
- **R5 (L1 honesty, K4):** pre-GPU flag-OFF evidence = static code-diff + a no-GPU CPU write-pattern unit (mocked/captured phys_jq/jqd over a step, flag-OFF vs current == byte-equal). The env-side runtime golden (B⑨a′-class full joint_q sha incl gripper, fixed seed, K steps + ≥1 done-reset) = declared as a **GPU-cost leg** bundled into the Rs G1 surface (route warp = cuda:0). STOP citing dod9a_prime 25/81 as write-site coverage (it is predicate-only).
- **R6 (obs + FK bookkeeping, K7):** :747-749/:777-780 FK warm-start pinning kept AS-IS on both flags (IK bookkeeping; not the servo surface). Flag-ON obs[7]/[15] = **physics joint_q readback** (per-world driver coords); flag-OFF unchanged. Document in plan v2 obs table; L4 asserts the flag-ON obs source.
- **R7 (process folds):** add to the chain: /pre-check (bundle diff, post-fold, pre-RULE-CHECK) + /reward-design scoped run (flag-ON delta) + prior-art script run (CC5-CH6 keywords) + §運用15 層3/層2(post)/層5 after build + video skill-path binding in G1 + validation-artifact file enumeration + §1 size correction.
- **R8 (guards):** cfg flag bool-type assert + `grasp_actuation ⇒ route_executor_impl=="route_executor"` fail-loud; env-owned index maps built at end of `_build_model` (post-:417, pre-settle) via `build_perworld_index_maps` (single-source with rex maps); L3 servo readback = `joint_target_mode[drivers]==POSITION` + ke==66.7/kd==2.0/effort==2.5 + negative control (non-driver dof carries no servo ke) on the authoritative model per R3 (replaces the vacuous seed-assert as the discriminating leg; seed-assert kept as a secondary); `.assign()` write pattern + device readback assert (CC3-CH5); mjw-eq-deferred caveat pinned (CC3-CH6); `_settled_fk_jq` gripper patch AR:868-872 mirror when flag-ON (CC4-CH5).

## Next chain (supersedes plan §11 first hops)

COORD folds → plan v2 (+ corrected PROPOSE file set {newton_route_env.py, route_executor.py} + validation-artifact files) → CC1 focused re-gate → /pre-check + scoped /reward-design + prior-art script → RULE-CHECK stage2 → build → no-GPU legs (L-set per R5/R8) → §運用15 層3/層2/層5 → /production-launch-gate + **Rs surface (G1 GPU + the worlds≥1-frozen escalation as a separate item)**.

---
*%12 RS-TECH-LEAD (w2:p4), 2026-07-10. 5体 = CC2/CC3/CC4/CC5 Challengers + CC6 NHA, independent parallel contexts. DECIDE=REVISE; no challenge rebutted; NHA CHANGE_JUSTIFIED with amended conditions. Pivotal substrate CRITICAL independently re-verified by CC1 before acceptance (§運用28).*
