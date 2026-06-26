# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

# thread_isaac_lab/configs/task_config.py
"""
Newton VBD task configuration — Single Source of Truth.

Code A (harness) modifies this file to tune parameters autonomously.
test_newton_clip_routing.py imports from here.

IMPORTANT: Values here are the authoritative source. Do NOT hardcode
overrides in the test script.
"""

# =============================================================================
# Scene Geometry (structural — normally not tuned by Code A)
# =============================================================================
TABLE_HEIGHT = 0.80
ROBOT_LEFT_BASE = (0.0, -0.35, TABLE_HEIGHT)
ROBOT_RIGHT_BASE = (0.0, 0.35, TABLE_HEIGHT)

# === Robot DOF SSOT (S2 substrate swap: Franka 9DOF VBD -> UR5e+Robotiq 14DOF, 2026-06-08) ===
# DERIVED on disk (eval_runs/troot_optE_s2_index_space_derivation_*, collapse=True). Newton-DOF SSOT ONLY
# (the PhysX dual_arm_cfg_*/legacy scripts keep their own Franka constants -- see S2 design C8).
ARM_DOF = 6  # UR5e arm joints (revolute)
GRIPPER_DOF = 8  # Robotiq 2f85 kinematic joints (4-bar x2)
ROBOT_NUM_JOINTS = ARM_DOF + GRIPPER_DOF  # 14
EE_BODY_IDX = 5  # wrist_3_link body local index
ROBOT_BODIES_PER_ARM = ROBOT_NUM_JOINTS  # 14 (bodies==joints, collapse=True; probe-confirmed)

# --- index-SPACE split (carry-forward #1: three joint roles diverge for UR5e+Robotiq) ---
GRIPPER_DRIVER_JOINT_IDX = [6, 10]  # JOINT space: ACTUATED driver joints (control / open-set)
GRIPPER_JOINT_RANGE = list(range(ARM_DOF, ROBOT_NUM_JOINTS))  # JOINT space: ALL 8 gripper joints [6..13]
#                                                   (exclude-gripper-from-arm-IK / finger_mask / pin sets)
GRIPPER_PAD_BODY_IDX = [9, 13]  # BODY space: pad-carrying followers (contact-filter LOGIC;
#                                                   pad GEOMETRY itself deferred to S5)
N_ARM_BODIES = ARM_DOF  # 6 (contact-filter: arm bodies 0..5)

# --- stride split (joint-stride vs body-stride; both =14 today, behavior-preserving) ---
JOINTS_PER_ARM = ROBOT_NUM_JOINTS  # 14: per-arm stride for joint_q arrays
BODIES_PER_ARM = ROBOT_BODIES_PER_ARM  # 14: per-arm stride for body_q arrays

# Backward-compat aliases (re-pointed to the CORRECT space):
FRANKA_NUM_JOINTS = ROBOT_NUM_JOINTS  # 14 (legacy stride; migrate sites to JOINTS_PER_ARM/BODIES_PER_ARM)
EE_BODY_OFFSET = EE_BODY_IDX  # 5
FINGER_LOCAL = GRIPPER_PAD_BODY_IDX  # [9,13]  (BODY-space finger-pos reads)

# =============================================================================
# Initial Joint Angles (Phase 1 hover)
# =============================================================================
# Reused from task_config_optionB/C/D.py. These are the existing analytical IK
# Phase-1 hover values required by the Isaac Lab dual-arm scene config.
LEFT_ARM_INIT_JOINTS = [
    +2.187389,
    +1.298854,
    -0.835999,
    -2.612635,
    -1.796263,
    +2.393499,
    -0.176715,
]

RIGHT_ARM_INIT_JOINTS = [
    +2.050813,
    +1.417245,
    -0.685936,
    -2.728376,
    -1.937756,
    +2.243239,
    +0.176715,
]

# =============================================================================
# End-Effector Geometry
# =============================================================================
EE_TO_FINGERTIP = 0.220  # FRANKA panda_hand->fingertip [m]; UR5e measured pins =
# EE_TO_PINCH_CLOSED / EE_TO_PINCH_TIP_CLOSED (Robotiq Grasp SSOT section below; S5 P1)

# =============================================================================
# Height Parameters (Code A: tune these to fix table penetration)
#
# IK target = wrist_3 (EE body 5). Finger tips are EE_TO_FINGERTIP (220mm, Franka value; re-derive S6) below.
# Finger tip Z ≈ param_value - 0.220.
# Table surface at TABLE_HEIGHT (0.80m).
# Cable rests on clip base plate: center at TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS.
# Design constraint: finger_tip_z ≥ clip base top (no clip/table penetration).
# GRASP_Z: fingertip at cable center → policy Z-clip auto-aligns to optimal height.
# =============================================================================
CLIP_BASE_HEIGHT = 0.005  # 5mm clip base plate above table (clip_parts dz=2.5mm, hz=2.5mm)
APPROACH_Z = TABLE_HEIGHT + 0.320  # 1.120: body6 height (fingertip=0.900, 100mm above table)
GRASP_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP  # 1.025: fingertip at clip base top (= cable bottom)
LIFT_Z = TABLE_HEIGHT + 0.320  # 1.120: body6 height (fingertip=0.900, 100mm above table)
PUSH_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP  # 1.025: same as GRASP_Z
EE_Z_SAFETY_UPPER = TABLE_HEIGHT + 0.5  # 1.300: wide safety bound for BC-guided envs (no waypoint semantics)

# =============================================================================
# Solver Parameters (Code A: tune these for contact stability)
# =============================================================================
SIM_SUBSTEPS = 10  # Featherstone substeps per physics frame (cloth_franka/panda_hydro: 10)
DISABLE_CONTACTS = False  # Must be False for rod cable: capsule-table + capsule-finger contact (selective filtering keeps arm bodies 0-6 filtered)
NJMAX = 64000  # Max constraint rows (w=512: ~63 contacts/world × 512 = 32256, headroom to 64k)

# Option-E solver backend SSOT (D-Opt1-3). Default "vbd" through Opt-1 for VBD A/B control;
# "mujoco" is the Option-E target (hosts the Robotiq 4-bar that VBD drops); flip deferred post-S7.
SOLVER_BACKEND = "vbd"  # "vbd" | "mujoco"
# FLIP-BLOCK (SC3): changing this default to "mujoco" is BLOCKED until (1) the SC3 standalone body_q_prev
# guards land, (2) the S4 mujoco reset-path (the 17 .numpy read-modify-write sites + joint_q seeding)
# lands, AND (3) the section-5.6 body_q_prev audit passes. The --solver-backend CLI smoke overrides
# locally (script-only, --solver-backend mujoco) without flipping this SSOT default.
# FLIP-CHECKLIST addition (S4b): the 3 own-solver envs (approach/insert/unclamp) build their OWN
# solver via make_solver() WITHOUT enable_cable_contacts — on a future flip their cable would
# silently build with contacts DISABLED. They are mujoco-DE-SCOPED (cycle-3 §9.1, no mujoco arm
# branch); wire enable_cable_contacts when (and only when) their mujoco port lands.
USE_MUJOCO_CPU = True  # Opt-1/S4-S7 = CPU smoke; GPU (use_mujoco_cpu=False) = S8

# Legacy MuJoCo parameters (kept for backward compatibility, not used by Featherstone)
MUJOCO_ITERATIONS = 8
MUJOCO_LS_ITERATIONS = 4

# =============================================================================
# PD Gains
# =============================================================================
ARM_KE = 8000.0
ARM_KD = 400.0
FINGER_KE = 2000.0  # Higher than panda_hydro(650) due to substeps=1 vs 10. < contact_ke(2500)
FINGER_KD = 100.0
FINGER_EFFORT_LIMIT = 60.0  # Higher than panda_hydro(20N): substeps=1 needs more force to overcome contact
FINGER_ARMATURE = 0.5  # panda_hydro reference: 0.5 (stabilizes finger dynamics)

# =============================================================================
# Cable Physical Properties
# =============================================================================
CABLE_SEGMENTS = 40  # 40 segments × 15mm = 600mm (5-clip span 300mm + 150mm margin each end)
CABLE_SEG_LEN = 0.015
CABLE_RADIUS = 0.004
# Cable mass MODEL-TRUTH = 44.97 g (~45.0 g): capsule volume × ρ=1100 → 1.1243 g/seg × 40
# [measured: s5_p1_probe_rev7_result.json gates.cable_mass.measured_kg = 0.04497085511684418].
# The earlier "0.8 g/seg → 32 g" figure was a cylinder-only print formula (end caps ignored,
# −36%) — RETIRED. Service load = m·g = 0.44 N (axial bars of the G3 class derive from THIS mass).

# add_rod cable — rigid-capsule chain with CABLE joints (rigid-link REVOLUTE on SolverMuJoCo; NOT Cosserat — see log.md:6042)
CABLE_BEND_STIFFNESS = 0.005  # EI [N·m²] — power-cable-floppy (human VISUAL pick 2026-06-19, %3 AUDIT-PASS
# R_S71_CABLE_DRAPE_AUDIT_03.md). Was 1.0 (EI 1.0 → joint K 66.67 = rigid rod = the "rod-like" complaint) / orig 0.1.
# CABLE_BEND_STIFFNESS = EI here (build:809 add_rod, :827 CABLE_MUJOCO_BEND_K = EI/CABLE_SEG_LEN), NOT a joint
# stiffness; active mujoco add_revolute_cable joint K = 0.005/0.015 = 0.333 N·m/rad. Inside the realistic Ø8 EI
# window 1e-3..5e-2 (Cable-Bending-Stiffness-EI-8mm.md); 45mm drape / 200mm overhang. Picked VISUALLY from the
# drape render (the sim drape IS the acceptance criterion; the "sim under-droops" rationale was retracted — audit
# F-B). The estimators/cable_state_cosserat.py:47 _NOMINAL_BEND_EI mirror is a SEPARATE env6/RL Cosserat-estimator
# weight, intentionally NOT synced here (pre-existing 0.1 drift; that track's own decision — audit F-A).
CABLE_BEND_DAMPING = 0.01  # Bend damping [N·m·s]
CABLE_STRETCH_STIFFNESS = 1.0e6  # EA [N] axial stiffness (high enough to prevent stretching)
CABLE_STRETCH_DAMPING = 0.0  # Stretch damping [N·s]

# Cable contact parameters (MuJoCo rigid body penalty contact for capsules)
CABLE_CONTACT_KE = 2500.0  # Contact stiffness (ShapeConfig default=2500; was 100 — 25x too low)
CABLE_CONTACT_KD = 100.0  # Contact damping (ShapeConfig default=100; was 10)
CABLE_CONTACT_MU = 1.0  # Friction coefficient (high for grip traction)

# SolverMuJoCo-path contact stiffness (S4a, empirically decided 2026-06-10; %3-PV-PASS_SCOPED).
# Newton maps ShapeConfig ke/kd -> MuJoCo solref via convert_solref (kernels.py:185):
# solref = (2/kd, (kd/2)*sqrt(1/ke)). The VBD-era CABLE_CONTACT_KE/KD above map to EXACTLY the
# MuJoCo default (0.02, 1.0) = mass-scaled soft contact (~3.1 mm rest compression on the r=4 mm
# cable); these values invert to solref=(0.005, 1.0) (tau = 24x SIM_DT >= the 2*dt stability
# floor, zeta=1) -> 0.1 mm rest compression (S4a smoke-verified). Used by the mujoco branch ONLY
# (cable capsules + table); the VBD path keeps CABLE_CONTACT_* (A/B byte-identity).
MUJOCO_CONTACT_KE = 40000.0
MUJOCO_CONTACT_KD = 400.0

# --- S5 P1 contact families (mujoco branch ONLY; VBD path byte-unchanged) ---------------------
# Runtime-poke-validated through the P1.3 rev7/rev8 full-chain runs + the B-2/calib benches.
# Readbacks: s5_p1_probe_rev8_result.json phases."P1.3-rev8".gates.payload_readback (poke source
# s5_p1_probe_rev7.py:98-107). Consumers wire on the mujoco-branch port (S5b); the SOLVER_BACKEND
# default stays "vbd" (FLIP-BLOCK above unchanged).
MUJOCO_CONTACT_CONDIM = 6  # cable + table(static) + pads (readback condim_readback all [6]).
# condim=3 has NO rolling rows -> the capsule cable escapes by log-rolling (-80.6 mm class,
# s5_b2_raw_discriminator G2); friction-adjacent knobs (impratio/solref/noslip) are INERT until
# rolling rows exist (G3 grid). LL: thread-vault/06-Knowledge/LL-Condim-Rolling-Mechanism.md
MUJOCO_CABLE_TABLE_FRICTION = (1.0, 0.005, 0.005)  # (slide, torsion[m], roll[m]) — applied to
# BOTH cable capsules and table/static geoms (rev7.py:98-100; readback cable_friction_after).
# roll/torsion 0.005 = SIMPLICITY+MARGIN choice (RULE-A): lowest-passing was 0.002 (s5_b2_sweep2
# W2 family); 0.005 adds margin at no measured cost.
MUJOCO_PAD_ROLL_FRICTION = 0.005  # pads keep shipped slide/torsion (0.7|0.6, 0.005 — 2f85.xml);
# roll set EXPLICITLY (readback pad_friction.after = [0.7, 0.005, 0.005]). NEVER rely on
# default/inherited mu_roll: inherited-roll + condim 6 reproduced a NaN (pinch bench P2).
MUJOCO_PAD_SOLREF = (-65789.0, -2105.3)  # ACTIVE pad<->cable solref: R6-bx4 TRUE-overdamp
# NEGATIVE form (-k, -b) = the (0.004, 1)-equivalent stiffness with damping x4 [ADOPTED
# human-Rs 2026-06-10 23:33 (A)+R6; bench: s5_calib_bench3r_result.json cells.R6_F00.solref_form;
# creep 134.9->60.4 um/f, collapse 0 at 0-2.2 N, clearance p-p 15x down]. CHAIN validation =
# the S5b first run (bench-validated only; the rev8 chain ran R4).
# FALLBACK (rev8-chain-validated): R4 positive form (0.002, 1.0) [readback pad_solref.after].
# DO-NOT-USE: positive solref with dampratio>1 (k ~ 1/zeta^2 softening -> ghost-contact regime;
# thread-vault/06-Knowledge/LL-GhostContact-DoNotUse.md).
MUJOCO_OPT_CONE = 1  # mjCONE_ELLIPTIC (readback opt.cone=1) — production DECIDE (P1.1).
MUJOCO_OPT_IMPRATIO = 10.0  # readback opt.impratio=10.0. The stripped 2f85 xml ships
# <option cone="elliptic" impratio="10"/>; these two constants pin that decision as SSOT.

# =============================================================================
# Clip Layout (5-clip, Y equal spacing + X staggered 千鳥)
# =============================================================================
CLIP_Y_SPACING = 0.075  # 75mm between adjacent clips
CLIP_X_ODD = 0.35  # X for C1, C3, C5
CLIP_X_EVEN = 0.40  # X for C2, C4 (千鳥 +50mm)
CLIP_X_DR_RANGE = (0.35, 0.40)  # X-stagger DR range for RL training [m]
CLIP_Y_CENTER = 0.0  # Center Y of clip array (midpoint of robot bases)

# Derived 5-clip positions (X, Y) — Z = TABLE_HEIGHT for all
# Routing direction: C1(+Y, right robot side) → C5(-Y, left robot side)
# Matches full_43step.json SSOT waypoints
CLIP_POSITIONS = [
    (CLIP_X_ODD, CLIP_Y_CENTER + 2 * CLIP_Y_SPACING),  # C1: (0.35, +0.150)
    (CLIP_X_EVEN, CLIP_Y_CENTER + 1 * CLIP_Y_SPACING),  # C2: (0.40, +0.075)
    (CLIP_X_ODD, CLIP_Y_CENTER),  # C3: (0.35,  0.000)
    (CLIP_X_EVEN, CLIP_Y_CENTER - 1 * CLIP_Y_SPACING),  # C4: (0.40, -0.075)
    (CLIP_X_ODD, CLIP_Y_CENTER - 2 * CLIP_Y_SPACING),  # C5: (0.35, -0.150)
]

# REST clips (S1, S2, S3 — cable initial support, Phase A grasp)
REST_CLIP_X = 0.15  # REST clip X position (§2 RL-Routing-Design.md)

# Single-clip convenience constants (C1, for test scripts and envs)
CLIP1_X = CLIP_POSITIONS[0][0]  # 0.35
CLIP1_Y = CLIP_POSITIONS[0][1]  # +0.150
CLIP1_Z = TABLE_HEIGHT  # 0.80: clip base on table (placement)
GROOVE_CENTER_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS  # 0.809: cable seated Z (insertion target)

# =============================================================================
# Grasp Coordinates
# =============================================================================
GRASP_X = 0.30  # Cable initial X position
CLIP_X = CLIP_X_ODD  # Clip1 X position (backward compat)
CLIP_GROOVE_INNER_RADIUS = 0.006  # 6mm — groove inner radius (from create_clip.py GROOVE_INNER_D/2)
P3_X_OFFSET = 0.012  # Small +X overshoot past clip for groove alignment
GRIP_HALF_SPAN = 0.044  # Each arm's EE offset from clip center in Y [m] (commanded arm-to-arm span = 88mm).
# History: 0.060 -> 0.028 (human source-GO 2026-06-19, max clip-insertion pressure) -> RELAXED to 0.044
# (reach-flag resolution, r_s71_reach_resolve_04 + r_s71_reach_minconv_04). The dual-arm collision-avoidance
# IK objective (newton_routing_utils: EE-EE safety spheres 0.035+0.035=70mm, +10mm margin, COLLISION_WEIGHT=5.0)
# FLOORS the achieved arm separation at ~80.5mm, so 0.028 (56mm) was UNREACHABLE in production: ik_move_both
# left 12.3mm error at every phase -> converged=False -> moves_ok FAILS. Cause = the collision objective BY
# DESIGN, NOT under-convergence (ik_move_both = ONE solve_ik_dual @ IK_ITERATIONS=100) and NOT kinematic reach
# (collision-OFF hits 0.028 exactly, cost 0). 0.044 = min-converging span with a 3mm margin under the 5mm
# moves_ok gate (shortfall 2.2mm; achieved sep 92.4mm); 0.040 is the gate-edge floor (4.2mm, fragile C2-C5/DR).
# ⚠ ROOT-CAUSE lever to reach the full 0.028 (max pressure): reduce the conservative COLLISION_SPHERE_RADII
# (real collidable pads clear at 34mm @28mm, r_s71_gripspan_verify_04) — an IK change in newton_routing_utils.py,
# NOT this file (separate GO). COUPLING: cable hold-span = the achieved sep (~92mm), not the commanded 88mm.

# =============================================================================
# Cable XY Domain Randomization (2026-04-25 Option C' ALT-MIN)
# =============================================================================
# Amplitude half-range (m) for cable XY uniform noise at env _reset_worlds.
# Applied per-world per-episode when env attribute `_randomize_cable_xy=True`
# (opt-in via `env.set_cable_xy_randomize(True)` or generator --randomize-cable-xy).
# Disabled by default (backward-compat with existing eval/train scripts).
# Scope: AC skill BC demo-collection variance augmentation (Phase 1 工程内 fix),
#   NOT sim-to-real DR per SOMA L38 distinction (deployment 時は cable fixed 動作).
#   ⚠ SUPERSEDED 2026-06-24 (Rs directive「位置姿勢はランダムに対応する必要あり」): deployment MUST handle
#   RANDOM cable position/pose → the "deploy = cable fixed (position/pose)" premise above no longer holds. This
#   DR is now ALSO a deployment-robustness requirement, not demo-only. ⚠ records-ahead-of-code: decision MADE,
#   impl PENDING (DR still opt-in/OFF by default below; the deploy range + policy-retrain wiring = Rs to spec,
#   NOT auto-set here — value unchanged). (Cable SHAPE-from-bending = a SEPARATE axis → Stage B/C.)
#   ref: log.md 2026-06-24; SOMA "L38" line-ref now stale/unlocatable (flagged to Rs).
# Reference: vault log.md 2026-04-25 01:25 rs Option B explicit approval entry.
CABLE_XY_DR_AMPLITUDE = (0.020, 0.020)  # (|dx_max|, |dy_max|) m — ±20mm X × ±20mm Y

# Derived: grip Y centered on C1 (for single-clip scripts).
# Multi-clip routing should use clip_y ± GRIP_HALF_SPAN directly.
WIDE_LEFT_Y = CLIP_POSITIONS[0][1] - GRIP_HALF_SPAN  # C1: +0.150 - 0.044 = +0.106
WIDE_RIGHT_Y = CLIP_POSITIONS[0][1] + GRIP_HALF_SPAN  # C1: +0.150 + 0.044 = +0.194

# =============================================================================
# Finger Control
# =============================================================================
FINGER_OPEN_POS = 0.04  # 40mm open
GRIPPER_INIT = FINGER_OPEN_POS  # Backward-compatible open gripper alias for scene configs.
FINGER_HALF_OPEN_POS = 0.006  # 6mm — guide hand しごき position (cable slides through claw)
FINGER_CLOSE_POS = 0.002  # 2mm gripping (gap=4mm < cable 8mm → 2mm/side compression)
FINGER_CLOSE_STEPS = 500  # One-shot target + effort_limit=20N cap. PD converges within 500 steps
FINGER_STEP_SIZE = 0.001  # 1mm per RL step — §12.4 finger action granularity

# =============================================================================
# Robotiq 2f85 Grasp SSOT (S5 P1 close, D-S5-2 — mujoco branch ONLY)
# =============================================================================
# Measured/validated on the P1.3 rev7/rev8 full-chain runs (UR5e+Robotiq, neq=8 equality build,
# grasp DOWN-pose). POSE-DEPENDENT CALIBRATION: the gap(driver-angle) curve settles gravity-
# dependently (same q -> gap differs by ~8 mm class between home/air and down-pose, rev3);
# the anchors below are DOWN-pose/neq8 values — ANY re-orientation (S6+ routing) RE-OPENS this
# calibration. The Franka FINGER_* block above stays for the VBD/legacy path.
GRIPPER_DRIVER_OPEN_RAD = 0.0  # driver open target [rad]; measured open gap 85.394 mm
# [s5_p1_probe_rev7_result.json phases."P1.2".gates.open_gap_mm = 85.39388778394712]
GRIPPER_DRIVER_CLOSE_RAD = 0.7407  # = q(free-air 4.0 mm) on the in-pose (e)-curve
# [rev8 close_target_pinned: "measured(rev7 e-curve)+derived(interp @4.0mm)"; in-run NAMED-1
# gate verified the fresh-curve q(4.0mm) vs 0.7407 within 1%]. The close is CONTACT/FORCE-
# limited (official 2f85 semantics): pads stop on the cable surface and squeeze under the
# effort cap — NOT a position-reached target.
# (e)-curve anchors (DOWN-pose, neq8; gate-verified rev7/rev8 within 1%):
GRIPPER_ECURVE_Q6MM_RAD = 0.7239  # q(6.0 mm) [rev7 "(e) q(6.0mm) verification" PASS]
GRIPPER_ECURVE_Q5MM_RAD = 0.7323  # q(5.0 mm) [rev7 pinned target, gate-verified]
GRIPPER_ECURVE_Q4MM_RAD = 0.7407  # q(4.0 mm) [rev8 NAMED-1, gate-verified]
# (The AIR-pose 8 mm anchor 0.7071682989734179 [rev8 phases."P1.2".close_target_rad] is a
# DIFFERENT calibration family — do not mix with the down-pose anchors.)
# --- HALF clamp (grasp/lift/route GUIDANCE) for the コ finger (step-table HALF: SOMA.md:80
# full=clip-insertion / half=guidance; Gripper-VGroove-Design.md:106). Human-CONFIRMED 0.69
# (2026-06-21 「0.69で確定」), supersedes the earlier PROPOSED 0.667. %2 cross-PV
# (eval_runs/troot_optE_rs71_kinematic_retention_20260616/R_S71_KO_GRIP_DOWN_{SWEEP_75,RETENTION_CROSSPV_76}):
# CPU 66.6N CLOSED/arm (vs 153N CLOSED at full CLOSE_RAD), penetration 0.898mm CLOSED, retention HOLDS
# (slip 0.7mm, firmer than the step-table-exact 0.667). 0.69 = human grip-MARGIN pick (0.667 has lower
# force 9.9N / pen 0.392mm but margin-light/intermittent) — a robustness trade, NOT a physics optimum.
# ⚠ CPU-only, NON-conservative x3 for GPU; GPU R-S6.6 + full-131mm-route/snag-retention PENDING before
# production (route verified 80 of 131mm only). ⚠ SSOT-ONLY: no committed consumer yet — the committed S6
# grasp (_run_mujoco_grasp_episode) is FREE-AIR (keeps CLOSE_RAD); the cable grasp lives in eval_runs
# probes that import this. FULL=insertion (CLOSE_RAD 0.7407) / HALF=guidance (this).
GRIPPER_DRIVER_HALF_OPEN_RAD = 0.69
GRIPPER_SERVO_TARGET_KE = 66.7  # driver position-servo stiffness, as run
GRIPPER_SERVO_TARGET_KD = 2.0  # [rev7+rev8 phases."P1.2".servo = {66.7, 2.0, 2.5}]
GRIPPER_DRIVER_EFFORT_LIMIT_NM = 2.5  # ~= official 5 N tendon force x coef 0.5 — restores the
# force cap the tendon strip removed (D-S5-2); the one-frame post-clamp |qfrc_actuator| <= 2.5
# gate held on rev7/rev8.
# EE->pinch geometry (CLOSED pose, measured; the re-pinned neq8 A1 reference, rev8 a1_measured):
EE_TO_PINCH_CLOSED = 0.2548428289592266  # wrist_3 -> pinch_mid drop [m] (drop_closed_m)
EE_TO_PINCH_TIP_CLOSED = 0.27574726696  # wrist_3 -> pad TIP drop [m] (tip_drop_m; コ f1ext claw tip,
# re-derived 2026-06-22 = +0.58mm vs the prior ◇ value 0.27516789724506097; pads extend ~20.90 mm distal
# of pinch_mid; keeps the designed 20mm closed-tip table clearance). Artifact:
# eval_runs/troot_optE_rs71_koshape_ee_tip_rederive_20260622/. EE_TO_FINGERTIP above (0.220) is the Franka/legacy
# value — UR5e+Robotiq consumers use THESE.
EE_TO_PINCH_OPEN = 0.26092  # wrist_3 -> pinch_mid drop [m], OPEN gripper. koshape f1ext bottom-claw
# cradle re-derive 2026-06-26 (Rs DC2); supersedes the ◇/S6-era 0.2092 body-origin value (probe_wrist3_frame
# wrist3_to_pinch_open_m, measured on the UN-CLAWED 2f85 FK model -> undershot the koshape f1ext claw by
# 51.7mm -> P0 claw penetration); refs gate_a_koshape_REDERIVE.py + %2 cross-confirm log:6684. SSOT for
# DOWNSTREAM consumers (S2-impl/S3, which have a cable); NOT consumed by the S6 infra smoke (no cable,
# descends by closed-tip table-clearance) -- defined-for-downstream, not dead (post-debate CC4/CC5/NHA).
# S6 scripted-close 8-vector (gripper-local JOINT order [6..13] == [right_driver, right_coupler,
# right_spring_link, right_follower, left_driver, left_coupler, left_spring_link, left_follower];
# probe_hover_seed VERIFIED this order on disk). LOOP-CONSISTENT, driver PINNED at
# GRIPPER_DRIVER_CLOSE_RAD=0.7407 in the standalone full-2f85 (equality 4-bar), probe_closed_config_v2.
# Used by the S6 mujoco IK-motion smoke's scripted-kinematic close (NO grip-force claim; the faithful
# actuated close is deferred — production stripped build has no actuator/equality, R-S6.6).
GRIPPER_CLOSE_QPOS = [0.7407, 7.2e-05, 0.728815, -0.699558, 0.7407, 7.2e-05, 0.728815, -0.699558]
# Grip-force datum (CONFIG-LABELED, %3 delta; in-grip sampling rule: N_total averaged over the
# both-pad-contact window ONLY, onset -> last-contact — e.g. the rev7 window [248,538], n=255):
GRIP_FORCE_DATUM_R4_BENCH_N = 47.3  # R4 (0.002,1) @ q=0.7407, PINCH-harness hold, F=0
# [s5_calib_bench3r_result.json cells.R4_F00.n_mean; the leg-ii II0 rev8-replica concurs]
GRIP_FORCE_DATUM_R6_BENCH_N = 37.1  # R6-bx4 @ q=0.7407, same harness [cells.R6_F00.n_mean].
# FULL-CHAIN datum so far: 37.485 N at q=0.7323/R4 [rev7 b_i_grip_force_in_grip.N_total_mean]
# — RE-MEASURE at the S5b first-run chain validation before gating on either bench number.

# =============================================================================
# Motion Control
# =============================================================================
STEPS_PER_CM = 50  # Physics steps per cm of EE motion
CONVERGE_MM = 2.0  # Convergence threshold in mm
MAX_MOVE_STEPS = 3000  # Safety limit per phase move
SETTLE_STEPS = 200  # Steps to hold position after motion

# =============================================================================
# Success Criteria (07-Design RL-Routing-Design.md Section 4 成功条件定義 v3)
# Source: thread-vault/07-Design/RL-Routing-Design.md L462-581
# Harness and RL env MUST import from here. Hardcoded overrides prohibited.
# =============================================================================

# clamp(hand, n) primitives
T_DIST = 0.002  # clamp.pos: 2mm (Grip/Clamp用)
T_DIST_APPROACH = 0.012  # approach.pos: 12mm (ApproachCable用。Grip INIT_POS_NOISE=12mmと整合)
T_ALIGN = 0.1745  # clamp.ori: 10° (0.1745 rad)
T_FINGER = 0.012  # clamp.grip: 12mm (2×CABLE_RADIUS + 4mm margin)

# seated(groove_n, clip) primitives
T_GROOVE = 0.003  # seated.pos: 3mm (CLIP_GROOVE_INNER_RADIUS / 2)
T_SEAT = 0.85  # seated.ori: cos > 0.85 (≈32°). 段階的引き締め: 0.85→0.9→0.95

# sustained (RL-Routing-Design.md §4 成功条件定義 v3 準拠)
K_GRASP = 5  # ApproachCable / AerialRegrasp: 5 RL steps (0.4s)
K_INSERT = 10  # InsertIntoClip: 10 RL steps (0.8s)
K_CLAMP = 5  # Clamp: 5 RL steps (0.4s). EXP-094推奨K=3, design doc K=5で確定
K_UNCLAMP = 5  # Unclamp: 5 RL steps (0.4s)

# terminal conditions
GRASP_TERMINAL_STEPS = 200  # ApproachCable: max episode length
INSERT_TERMINAL_STEPS = 200  # InsertIntoClip approach mode: max episode length
INSERT_TERMINAL_STEPS_INSERT = 300  # InsertIntoClip insert mode: longer for precision (3mm target)
CLAMP_TERMINAL_STEPS = 100  # Clamp: max episode length (shorter — only finger close + EE compensation)
UNCLAMP_TERMINAL_STEPS = 100  # Unclamp: max episode length (finger open + EE tracking/retreat)
GRIP_TERMINAL_STEPS = 100  # Unified Grip (Clamp+Unclamp): max episode length
GROOVE_BODIES_MIN = 2  # InsertIntoClip: bodies in groove >= 2

# ApproachCable terminal: cable lifted to LIFT_Z (defined in Height Parameters)
# InsertIntoClip terminal: bodies in groove >= GROOVE_BODIES_MIN
