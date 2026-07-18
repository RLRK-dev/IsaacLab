# (d) ARM-CONTROL REMEDIATION — ENGINEERING BRIEF (RS-TECH-LEAD → VT-DESIGN)

- **Date:** 2026-07-19 (JST)
- **Author:** RS-TECH-LEAD (w2:p4) — records/framing only
- **For:** VT-DESIGN (w2:p5) — control design owner
- **Node context:** §0 control-method remediation (task (d), the substrate-compliance body of work)
- **Rs status:** "実施" approved (L3 GO). This brief is the DESIGN entry, not an implementation.

## 0. Role boundary (read first)

This is an **engineering framing** by RS-TECH-LEAD: the problem, the target mechanism (which
already exists), the scope, the pivotal unknown, and the open design questions. **The control
design itself — how the target is set each step, gains/force limits, tolerance bars, which sites
are reset-init vs control-loop, the de-risk probe spec, and the staged rollout — is VT-DESIGN's
call.** This brief poses those questions; it deliberately does not answer them (never self-derive
control design; `feedback-design-ask-vt-design-never-self-derive`).

## 1. The violation (grounded)

- RS71 §0#3 (**DiffIK / IK-based control only**) and §0#5 (**no kinematic trick / forced
  placement**) are **substrate-agnostic** invariants — clarified this session in CLAUDE.md
  (commit `a97c3fe43d`) and machine-checked by `validate.sh` **Layer 8** (commit `0936ba13ac`).
- **Current arm drive = a kinematic trick.** The arm pose is set by writing the physics
  joint-position array directly and zeroing velocity, then stepping the solver:
  - `route_executor.py:1817-1824` — `phys_jq[_ARM_OVERWRITE_LOCAL] = fk_state...` ; `phys_jqd = 0.0` ;
    `state_0.joint_q.assign(phys_jq)` ; `solver.step(...)`. = **infinite-stiffness forced placement**,
    no physics torque path.
- **Footprint = 16 direct joint-position writes across 5 env files** (the Layer 8 baseline; 15 arm + 1 gripper-restore):
  - `route_executor.py` (6): `:213 :236 :342 :344(gripper) :1817 :1820`
  - `newton_aerial_regrasp_mujoco_env.py` (3): `:475 :1090 :1575`
  - `newton_approach_cable_mujoco_env.py` (3): `:419 :746 :1203`
  - `newton_route_env.py` (3): `:827 :1094 :1270`
  - `newton_skill_env_base.py` (1): `:2080`
- **Why it exists (root):** a **VBD-era workaround** — the VBD solver could not simulate
  REVOLUTE/PRISMATIC joints, so the arm was FK-driven (`LL-Newton.md:666, :670`). The substrate is
  now **MuJoCo** (`RS71-System-Spec-SSOT.md:15`, SolverMuJoCo), which supports PD actuators, but the
  kinematic drive was carried over unchanged.

## 2. The target mechanism — it ALREADY EXISTS (grounded)

- **Arm PD actuators are in the model:** `ur5e.xml:124-131` — 6 `<general>` position actuators
  (shoulder_pan/lift, elbow, wrist_1/2/3). Gains/limits: size3 = `gainprm 2000 / biasprm 0 -2000 -400 /
  forcerange ±150 N·m`; size1 = `gainprm 500 / biasprm 0 -500 -100 / forcerange ±28 N·m`
  (`ur5e.xml:10-11, :19`). biastype affine ⇒ position servo (force = kp·(ctrl−q) − kd·q̇).
- **Arm PD is confirmed working on the MuJoCo solver:** `LL-Newton.md:98` ("Arm PD control (MuJoCo
  solver, max_err 0.002 rad)"), `:189` ("MuJoCo solver: PD control 安定動作, j0 → 0.5000 exact").
- **The gripper is already actuator-driven** — the working model to mirror: `newton_route_env.py:309-321`
  wires 4 MuJoCo **position servo actuators** (`GRIPPER_SERVO_TARGET_KE/KD`, effort caps at the joint
  level `jnt_actfrcrange`), driven by `control.joint_target_pos`.
- ⇒ **The migration is a rewire, in principle:** replace each `phys_jq[arm…] = target` write with
  **setting the MuJoCo `ctrl` (arm position target)** and letting the PD actuators drive the arm
  through physics — exactly as the gripper already works.

## 3. Why this is NOT a trivial rewire — the pivotal unknown

- kinematic = the arm pose is **realized EXACTLY every step** (qd forced to 0). PD = the arm
  **tracks** the target with **finite force** (±150 / ±28 N·m) ⇒ tracking error, dynamics, settling lag.
- **The entire downstream pipeline was built and validated on kinematic exactness:** recorded-route
  playback, the DAPG demos, the trainer's residual-on-script action model, the clip-pin **seat gates**
  (contact / groove-height / lateral bars read at exact poses), and the #18 grip-slip work. PD tracking
  error perturbs all of these.
- **THE gating empirical question:** *does the MuJoCo arm PD track the recorded/commanded arm
  trajectory within an acceptable tolerance under the ±150/±28 N·m force limits (with the cable +
  gripper load)?* — If YES, (d) is largely a rewire (set `ctrl` = the existing target each step).
  If NO, (d) is a re-tuning / re-trajectory effort. **This one fact gates the whole design.**

## 4. Open design questions FOR VT-DESIGN (p5)

- **Q1 — target-setting scheme:** per control step, set `ctrl` = the current recorded/IK arm target
  (mirror the gripper's `joint_target_pos`)? Or interpolate a feasible trajectory? Does the IK layer
  (`solve_ik_dual`) feed the actuator target, or the recorded `arm_q`?
- **Q2 — gains / limits / tolerance:** are the `ur5e.xml` defaults (size3 2000 / size1 500; ±150/±28)
  adequate, or re-tune? What is the **tolerance bar** for "tracks acceptably" (per-joint rad? EE mm?),
  and against which reference (recorded trajectory / IK target)?
- **Q3 — reset-init vs control-loop:** which of the 16 sites are **one-time reset/init** pose-seeds
  (a permitted exception — cf. `prohibited.md` reset-init note) vs **per-step control-loop** writes
  (the actual violation to migrate)? (e.g. `:1817/:1820` sit in a STEP-1 probe/init block; `:342` is a
  phase-k restore; `:213/:236` are the per-step drive.) This classification sets what must change.
- **Q4 — de-risk probe spec:** what is the cheapest measurement that answers §3's gating question —
  trajectory, tolerance metric, baseline (kinematic), env, N? RS-TECH-LEAD will run it.
- **Q5 — staged rollout + re-validation:** which env first (a single skill env, or `route_executor`)?
  What re-validation gate at each stage (route reproduction vs the Rs motion standard `p2r_c11_route.mp4`;
  grasp; seat; re-grasp; #18)?
- **Q6 — interaction with the trainer + pin:** does PD tracking error break the **residual-on-script**
  assumption (script = exact recorded arm) or the **clip-pin seat gates** (bars read at exact poses)?
  Does the pin exception (`§0#5`, the only kinematic exception) stay untouched? (It writes body_q/eq,
  not joint_q, so Layer 8 does not flag it — confirm the design keeps it that way.)

## 5. Proposed staged approach (RS-TECH-LEAD recommendation — for p5 to shape/replace)

1. **De-risk probe (measurement, RS-TECH-LEAD runs):** drive the arm to the recorded trajectory via
   PD `ctrl` in ONE isolated env; measure tracking error vs the kinematic baseline (§3's gating fact).
2. **Control design (VT-DESIGN):** target scheme + gains + tolerance + site classification, informed
   by the probe.
3. **Staged rollout:** one env → re-validate → next; pipeline re-validation at each stage.
4. **Rs sign-off** before landing; §運用2 [VERIFY] / [DESIGN-GATE] as applicable (control change = L3).

## 6. Invariants preserved (this migration MAKES the arm compliant; it changes no premise)

- §0#1 DUAL-ARM, §0#2 88 mm span / fixed bases, §0#3 IK-based control, §0#4 コ-gripper geometry,
  §0#5 no-kinematic-trick (clip-pin exception only). The migration removes the arm's kinematic drive
  to satisfy §0#3/#5; it must not alter any invariant. If any design option would touch one → STOP +
  Rs (FOUNDATIONAL gate).

## Appendix — evidence index (file:line)

- Violation sites: Layer 8 baseline in `scripts/validations/check_control_method.sh` (commit `0936ba13ac`).
- Current drive: `route_executor.py:213 :236 :342 :1817 :1820 :1822-1824`.
- VBD root: `LL-Newton.md:666 :670`. Substrate now MuJoCo: `RS71-System-Spec-SSOT.md:15`.
- Arm PD target: `ur5e.xml:10-11 :19 :124-131`; confirmed `LL-Newton.md:98 :189`.
- Gripper mirror: `newton_route_env.py:309-321`.
- Invariants: `RS71-System-Spec-SSOT.md:23-32` (§0#1-#5).
