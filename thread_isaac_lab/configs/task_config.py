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
ARM_DOF = 6                          # UR5e arm joints (revolute)
GRIPPER_DOF = 8                      # Robotiq 2f85 kinematic joints (4-bar x2)
ROBOT_NUM_JOINTS = ARM_DOF + GRIPPER_DOF          # 14
EE_BODY_IDX = 5                      # wrist_3_link body local index
ROBOT_BODIES_PER_ARM = ROBOT_NUM_JOINTS           # 14 (bodies==joints, collapse=True; probe-confirmed)

# --- index-SPACE split (carry-forward #1: three joint roles diverge for UR5e+Robotiq) ---
GRIPPER_DRIVER_JOINT_IDX = [6, 10]                # JOINT space: ACTUATED driver joints (control / open-set)
GRIPPER_JOINT_RANGE = list(range(ARM_DOF, ROBOT_NUM_JOINTS))   # JOINT space: ALL 8 gripper joints [6..13]
#                                                   (exclude-gripper-from-arm-IK / finger_mask / pin sets)
GRIPPER_PAD_BODY_IDX = [9, 13]                    # BODY space: pad-carrying followers (contact-filter LOGIC;
#                                                   pad GEOMETRY itself deferred to S5)
N_ARM_BODIES = ARM_DOF                            # 6 (contact-filter: arm bodies 0..5)

# --- stride split (joint-stride vs body-stride; both =14 today, behavior-preserving) ---
JOINTS_PER_ARM = ROBOT_NUM_JOINTS                 # 14: per-arm stride for joint_q arrays
BODIES_PER_ARM = ROBOT_BODIES_PER_ARM             # 14: per-arm stride for body_q arrays

# Backward-compat aliases (re-pointed to the CORRECT space):
FRANKA_NUM_JOINTS = ROBOT_NUM_JOINTS              # 14 (legacy stride; migrate sites to JOINTS_PER_ARM/BODIES_PER_ARM)
EE_BODY_OFFSET = EE_BODY_IDX                       # 5
FINGER_LOCAL = GRIPPER_PAD_BODY_IDX               # [9,13]  (BODY-space finger-pos reads)

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
EE_TO_FINGERTIP = 0.220  # panda_hand (body 6) to finger mesh TIP [m] (URDF: 0.107+0.0584+0.0545=0.2199)

# =============================================================================
# Height Parameters (Code A: tune these to fix table penetration)
#
# IK target = panda_hand (body 6). Finger tips are EE_TO_FINGERTIP (220mm) below.
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

# Cosserat Rod (add_rod) — capsule chain with cable joints
CABLE_BEND_STIFFNESS = 1.0# EI [N·m²] L3 stiffness calibration variant 1.0 (was 0.1)
CABLE_BEND_DAMPING = 0.01# Bend damping [N·m·s]
CABLE_STRETCH_STIFFNESS = 1.0e6  # EA [N] axial stiffness (high enough to prevent stretching)
CABLE_STRETCH_DAMPING = 0.0# Stretch damping [N·s]

# Cable contact parameters (MuJoCo rigid body penalty contact for capsules)
CABLE_CONTACT_KE = 2500.0# Contact stiffness (ShapeConfig default=2500; was 100 — 25x too low)
CABLE_CONTACT_KD = 100.0# Contact damping (ShapeConfig default=100; was 10)
CABLE_CONTACT_MU = 1.0# Friction coefficient (high for grip traction)

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
GRIP_HALF_SPAN = 0.060  # Each arm's EE offset from clip center in Y [m] (arm-to-arm span = 120mm)

# =============================================================================
# Cable XY Domain Randomization (2026-04-25 Option C' ALT-MIN)
# =============================================================================
# Amplitude half-range (m) for cable XY uniform noise at env _reset_worlds.
# Applied per-world per-episode when env attribute `_randomize_cable_xy=True`
# (opt-in via `env.set_cable_xy_randomize(True)` or generator --randomize-cable-xy).
# Disabled by default (backward-compat with existing eval/train scripts).
# Scope: AC skill BC demo-collection variance augmentation (Phase 1 工程内 fix),
#   NOT sim-to-real DR per SOMA L38 distinction (deployment 時は cable fixed 動作).
# Reference: vault log.md 2026-04-25 01:25 rs Option B explicit approval entry.
CABLE_XY_DR_AMPLITUDE = (0.020, 0.020)  # (|dx_max|, |dy_max|) m — ±20mm X × ±20mm Y

# Derived: grip Y centered on C1 (for single-clip scripts).
# Multi-clip routing should use clip_y ± GRIP_HALF_SPAN directly.
WIDE_LEFT_Y = CLIP_POSITIONS[0][1] - GRIP_HALF_SPAN  # C1: +0.150 - 0.060 = +0.090
WIDE_RIGHT_Y = CLIP_POSITIONS[0][1] + GRIP_HALF_SPAN  # C1: +0.150 + 0.060 = +0.210

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
