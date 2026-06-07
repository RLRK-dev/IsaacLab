# thread_isaac_lab/configs/task_config.py
"""
Task configuration parameters - Single Source of Truth

All scripts should import from here instead of hardcoding values.
This is the authoritative source for all numerical settings.

IMPORTANT: When changing robot positions, you MUST also update
the initial joint angles (LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS)
using IK calculation results.
"""

# =============================================================================
# Cable Physical Properties
# =============================================================================
CABLE_SEGMENT_COUNT = 20
CABLE_SEGMENT_LENGTH = 0.03  # 3cm per segment
CABLE_TOTAL_LENGTH = CABLE_SEGMENT_COUNT * CABLE_SEGMENT_LENGTH  # 60cm
CABLE_RADIUS = 0.005  # 5mm

# =============================================================================
# Table Properties
# =============================================================================
TABLE_HEIGHT = 0.75

# =============================================================================
# Cable Position (Y-axis layout)
# =============================================================================
CABLE_X = 0.30
CABLE_Z = TABLE_HEIGHT + 0.02  # 0.77 - 物理安定性のためのオフセット

# Cable endpoint Y positions
# H153: Rollback to H151 values (Y=±0.285)
# Reason: LL-2026-01-14-ROOT-004 - Cable USD length is fixed, Y change caused asymmetric displacement
CABLE_SEG17_Y = -0.285  # Left end (seg_17) - H153 rollback to H151
CABLE_SEG19_Y = +0.285  # Right end (seg_19) - H153 rollback to H151

# Grasp inward offset - grip at cable ends directly
# H148: Set to 0 to eliminate Y-axis gap between fingertip and cable
# Previous: 0.03 (3cm inward) caused 30mm Y-gap leading to poor grasp
GRASP_INWARD_OFFSET = 0.0  # H148: 0.03 -> 0.0

# =============================================================================
# Grasp Target Positions
# =============================================================================
# H153: Grip at cable endpoints (Y=±0.285, rolled back from H152)
GRASP_LEFT = (CABLE_X, CABLE_SEG17_Y + GRASP_INWARD_OFFSET, CABLE_Z)   # Y = -0.285 (H153)
GRASP_RIGHT = (CABLE_X, CABLE_SEG19_Y - GRASP_INWARD_OFFSET, CABLE_Z)  # Y = +0.285 (H153)

# =============================================================================
# Robot Base Positions (8-Variable Optimization with Collision Check)
# =============================================================================
# Optimization date: 2025-12-29 21:18:11
# Method: He & Liu Analytical IK + Geometry-based Collision Check
# Configurations explored: 65,536 (grid=4)
# Worst-case joint margin: 16.5°
# Minimum arm clearance: 20.5cm (required: 20cm)
# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)
ROBOT_LEFT_BASE = (0.2467, -0.4200, 1.265)
ROBOT_RIGHT_BASE = (0.2467, 0.2000, 1.265)

# Base rotation: Y+90° for wall-mount
ROBOT_BASE_QUAT_WXYZ = (0.7071, 0.0, 0.7071, 0.0)  # (w, x, y, z) for Isaac Sim
ROBOT_BASE_QUAT_XYZW = (0.0, 0.7071, 0.0, 0.7071)  # (x, y, z, w) for scipy

# Gripper orientation: pointing down (-Z) with fingers open in X direction
# This is X180° + Z90° rotation
GRIPPER_DOWN_QUAT_WXYZ = (0.0, 0.7071, -0.7071, 0.0)  # (w, x, y, z)

# =============================================================================
# Initial EE Positions (above grasp targets)
# =============================================================================
EE_HOVER_HEIGHT = 0.15  # 15cm above cable
# H153: Above cable endpoints (Y=±0.285, rolled back from H152)
EE_LEFT_INIT = (CABLE_X, CABLE_SEG17_Y + GRASP_INWARD_OFFSET, CABLE_Z + EE_HOVER_HEIGHT)   # (0.30, -0.285, 0.92) H153
EE_RIGHT_INIT = (CABLE_X, CABLE_SEG19_Y - GRASP_INWARD_OFFSET, CABLE_Z + EE_HOVER_HEIGHT)  # (0.30, +0.285, 0.92) H153

# =============================================================================
# Initial Joint Angles (Phase 1: Hover - Analytical IK result)
# =============================================================================
# H152: EE positions with Y = ±0.25 (3.5cm inward for improved manipulability)
# EE Left:  (0.29, -0.25, 0.895)  Margin: 26.3°
# EE Right: (0.29, +0.25, 0.895)  Margin: 19.7°
# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)
# Updated: 2026-01-14 H152 IK recalculation for Y=±0.25 targets

# Left arm (IK-optimized for Phase 1 hover)
# Target EE: (0.29, -0.25, 0.895), Margin: 26.3°
# H152: Y position optimized from -0.285 to -0.25
LEFT_ARM_INIT_JOINTS = [
    +2.187389,  # panda_joint1: +125.3 deg
    +1.298854,  # panda_joint2: +74.4 deg
    -0.835999,  # panda_joint3: -47.9 deg
    -2.612635,  # panda_joint4: -149.7 deg
    -1.796263,  # panda_joint5: -102.9 deg
    +2.393499,  # panda_joint6: +137.1 deg
    -0.176715,  # panda_joint7: -10.1 deg
]

# Right arm (IK-optimized for Phase 1 hover)
# Target EE: (0.29, +0.25, 0.895), Margin: 19.7°
# H152: Y position optimized from +0.285 to +0.25
RIGHT_ARM_INIT_JOINTS = [
    +2.050813,  # panda_joint1: +117.5 deg
    +1.417245,  # panda_joint2: +81.2 deg
    -0.685936,  # panda_joint3: -39.3 deg
    -2.728376,  # panda_joint4: -156.3 deg
    -1.937756,  # panda_joint5: -111.0 deg
    +2.243239,  # panda_joint6: +128.5 deg
    +0.176715,  # panda_joint7: +10.1 deg
]

# Gripper initial position (open)
GRIPPER_INIT = 0.04

# =============================================================================
# Grasp Parameters
# =============================================================================
GRASP_DISTANCE_THRESHOLD = 0.03  # 3cm
GRIPPER_CLOSED = 0.0
GRIPPER_OPEN = 0.04
GRIPPER_TOLERANCE = 0.025

# =============================================================================
# Safety Heights
# =============================================================================
SAFE_HEIGHT = TABLE_HEIGHT + 0.20  # 20cm above table for waypoint navigation

# =============================================================================
# Lift Parameters
# =============================================================================
LIFT_HEIGHT = 0.10  # 10cm lift for grasp verification
LIFT_VERIFY_THRESHOLD = 0.005  # Cable must rise at least 0.5cm (H157: relaxed threshold)

# =============================================================================
# Hook Position
# =============================================================================
# 2026-01-06: フック掛け改善 - 実際のケーブル中央位置に合わせる
# 実測: L=(0.74,0,z) R=(0.28,0,z) → center=(0.51,0,z)
# フックをX=0.50に配置（ケーブル中央とほぼ一致）
HOOK_X = 0.50
HOOK_Y = 0.00
HOOK_Z = TABLE_HEIGHT + 0.15  # 15cm above table = 0.90m

# =============================================================================
# Task Waypoints (All Phases)
# =============================================================================
# Optimized using analytical IK (2025-12-28)
# All positions verified for reachability and joint margin

# Phase 1: Initial hover position (optimized for margin >= 18°)
# H153: Y=±0.285 (rolled back from H152 due to cable asymmetric displacement)
# Directly above cable endpoints for accurate grasp
WAYPOINT_PHASE1_LEFT = (0.29, -0.285, 0.895)   # Y = SEG17 = -0.285 (H153)
WAYPOINT_PHASE1_RIGHT = (0.29, 0.285, 0.895)   # Y = SEG19 = +0.285 (H153)

# Phase 2: Grasp position (fingertip at cable center - radius for contact)
# Z = CABLE_Z - CABLE_RADIUS = 0.755 - 0.005 = 0.75
# H153: Grip at cable endpoints (Y=±0.285 via CABLE_SEG17_Y/SEG19_Y, rolled back)
WAYPOINT_PHASE2_LEFT = (CABLE_X, CABLE_SEG17_Y + GRASP_INWARD_OFFSET, 0.75)   # Y = -0.285 (H153)
WAYPOINT_PHASE2_RIGHT = (CABLE_X, CABLE_SEG19_Y - GRASP_INWARD_OFFSET, 0.75)  # Y = +0.285 (H153)

# Phase 3: Lift position (optimized for margin >= 17°)
# H153: Y=±0.285 (rolled back from H152 due to cable asymmetric displacement)
# Maintain same Y as grasp position (at cable endpoints)
WAYPOINT_PHASE3_LEFT = (0.29, -0.285, 0.90)   # Y = SEG17 = -0.285 (H153)
WAYPOINT_PHASE3_RIGHT = (0.29, 0.285, 0.90)   # Y = SEG19 = +0.285 (H153)

# Phase 4: Hook approach (optimized for margin >= 20°)
WAYPOINT_PHASE4_LEFT = (0.35, -0.17, 0.82)
WAYPOINT_PHASE4_RIGHT = (0.35, 0.17, 0.82)

# Phase 5: Cable placement (waypoints defined below with joint angles)

# =============================================================================
# Phase 2-5 Joint Angles (Analytical IK result)
# =============================================================================

# Phase 2: Grasp position (fingertip at cable endpoints)
# H152: Y = ±0.25 (3.5cm inward for improved manipulability)
# EE Left:  (0.30, -0.25, 0.75)  Margin: 37.6°
# EE Right: (0.30, +0.25, 0.75)  Margin: 28.9°
# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)
# Updated: 2026-01-14 H152 IK recalculation for Y=±0.25 targets
PHASE2_LEFT_JOINTS = [
    +1.549235,  # panda_joint1: +88.8 deg
    +1.090808,  # panda_joint2: +62.5 deg
    -0.817736,  # panda_joint3: -46.9 deg
    -2.362082,  # panda_joint4: -135.3 deg
    -2.241863,  # panda_joint5: -128.4 deg
    +2.098932,  # panda_joint6: +120.3 deg
    -0.277778,  # panda_joint7: -15.9 deg
]

PHASE2_RIGHT_JOINTS = [
    +1.478520,  # panda_joint1: +84.7 deg
    +1.257858,  # panda_joint2: +72.1 deg
    -0.860291,  # panda_joint3: -49.3 deg
    -2.468922,  # panda_joint4: -141.5 deg
    -2.380687,  # panda_joint5: -136.4 deg
    +1.996826,  # panda_joint6: +114.4 deg
    +0.025253,  # panda_joint7: +1.4 deg
]

# Phase 3: Lift position (after grasp)
# H152: Y = ±0.25 (3.5cm inward for improved manipulability)
# EE Left:  (0.29, -0.25, 0.90)  Margin: 25.5°
# EE Right: (0.29, +0.25, 0.90)  Margin: 19.3°
# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)
# Updated: 2026-01-14 H152 IK recalculation for Y=±0.25 targets
PHASE3_LEFT_JOINTS = [
    +2.223937,  # panda_joint1: +127.4 deg
    +1.317933,  # panda_joint2: +75.5 deg
    -0.838283,  # panda_joint3: -48.0 deg
    -2.620527,  # panda_joint4: -150.1 deg
    -1.771499,  # panda_joint5: -101.5 deg
    +2.424326,  # panda_joint6: +138.9 deg
    -0.176768,  # panda_joint7: -10.1 deg
]

PHASE3_RIGHT_JOINTS = [
    +2.075828,  # panda_joint1: +118.9 deg
    +1.420186,  # panda_joint2: +81.4 deg
    -0.677824,  # panda_joint3: -38.8 deg
    -2.735323,  # panda_joint4: -156.7 deg
    -1.918000,  # panda_joint5: -109.9 deg
    +2.257455,  # panda_joint6: +129.3 deg
    +0.176768,  # panda_joint7: +10.1 deg
]

# Phase 4: Hook approach (elbow-down)
# EE Left:  (0.35, -0.17, 0.82)  Margin: 35.0°
# EE Right: (0.35, 0.17, 0.82)  Margin: 20.7°
# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)
# Updated: 2026-01-02 T1 IK recalculation with correct base positions
PHASE4_LEFT_JOINTS = [
    +1.979009,  # panda_joint1: +113.4 deg
    +1.049738,  # panda_joint2: +60.1 deg
    -1.000510,  # panda_joint3: -57.3 deg
    -2.461316,  # panda_joint4: -141.0 deg
    -1.997756,  # panda_joint5: -114.5 deg
    +2.327467,  # panda_joint6: +133.4 deg
    -0.429293,  # panda_joint7: -24.6 deg
]

PHASE4_RIGHT_JOINTS = [
    -1.861715,  # panda_joint1: -106.7 deg
    +1.395119,  # panda_joint2: +79.9 deg
    +0.931691,  # panda_joint3: +53.4 deg
    -2.709798,  # panda_joint4: -155.3 deg
    +2.305861,  # panda_joint5: +132.1 deg
    +2.172162,  # panda_joint6: +124.5 deg
    -1.843434,  # panda_joint7: -105.6 deg
]

# Phase 4.5: 90度回転（ケーブルをY軸からX軸方向へ回転）
# 2026-01-06: フック掛け改善 - 実測値に合わせた調整
# グリッパー間距離: 45cm（実測L=0.74, R=0.28より）
# ケーブル中央X=0.51 ≈ フックX=0.50
# EE Left:  (0.75, 0.0, 0.95) - 前方（実測に近い値）
# EE Right: (0.30, 0.0, 0.95) - 後方（到達可能）

# 案1: 軌道の2段階分割（2026-01-06 test_rotation27で案2失敗後）
# Phase 4.5a: 両アーム→中間点（ケーブル中央を動かさない対称移動）
# Phase 4.5b: 左右に分離（ケーブル中央を固定したまま左右対称に展開）
# test_rotation28: X=0.525は右アームのワークスペース外、43.9%でNaN
# test_rotation29: X=0.40に縮小（右アーム到達可能範囲内）
# 2026-01-07 v19: 旧WAYPOINT_PHASE45Aは使用しない（X/Y同時移動でNaN発生）

# 2026-01-07 v19: X/Y移動分離の3段階アプローチ
# Stage 1b: X移動のみ（Y固定）- 開始位置のY座標を維持
# ベースライン: v66 (H090) X=0.31 - 61%進行（最良結果）
# テスト結果: X=0.305でもジョイント差分93°は変わらず（X位置は原因ではない）
WAYPOINT_PHASE45B_LEFT = (0.31, -0.232, 1.05)   # v66ベースライン
WAYPOINT_PHASE45B_RIGHT = (0.31, 0.237, 1.05)   # v66ベースライン

# H097/v71: Stage 1b中間ウェイポイント（エルボー遷移分割）
# 88°エルボーフリップを2段階に分割（各44°）
# Z=0.95は最終目標Z=1.05の約半分の上昇
WAYPOINT_STAGE1B_MID_LEFT = (0.31, -0.232, 0.95)   # 中間点（Z半分）
WAYPOINT_STAGE1B_MID_RIGHT = (0.31, 0.237, 0.95)   # 中間点（Z半分）
STAGE1B_MID_STABILIZE_STEPS = 20  # 中間点で安定化待機

# Stage 1c: Y移動のみ（X固定）- X=0.31を維持してY座標のみ移動
# H126: Y移動距離さらに短縮 - 1.5cm→1.0cmに縮小
# 左腕: -0.232→-0.222 (delta=+0.010), 右腕: +0.237→+0.227 (delta=-0.010)
# ケーブル物理の安定性を優先、移動距離を最小化（H125の60-80%成功→90%目標）
WAYPOINT_PHASE45C_LEFT = (0.31, -0.222, 1.05)    # Y: -0.232→-0.222 (delta=+0.010, 中心方向)
WAYPOINT_PHASE45C_RIGHT = (0.31, 0.227, 1.05)    # Y: 0.237→0.227 (delta=-0.010, 中心方向)

# 旧定義（互換性のため残す）
WAYPOINT_PHASE45A_LEFT = (0.40, -0.15, 0.95)    # 使用しない
WAYPOINT_PHASE45A_RIGHT = (0.40, 0.29, 0.95)    # 使用しない

# 2026-01-07: 右腕は-Y方向に移動できない（ワークスペース制限またはIK解空間問題）
# Y=0.24ではStage 1完了、Stage 2で63.1%でNaN
# Stage 1終了時の右腕Y位置（≈0.286）に近い値を設定し、Y移動を最小化

WAYPOINT_PHASE45_LEFT = (0.70, -0.222, 0.95)   # H126: Y=-0.222（Stage 1c短縮移動後、delta=0.010）
WAYPOINT_PHASE45_RIGHT = (0.30, 0.227, 0.95)   # H126: Y=0.227（Stage 1c短縮移動後、delta=0.010）

# H109: Right arm follow during Stage 2a to maintain cable tension balance
# When left arm moves +X, right arm moves -X to compensate
# Follow factor: right moves -28% of left's X movement
STAGE_2A_RIGHT_FOLLOW_FACTOR = 0.32  # H115: 0.34→0.32（最適点に戻す）

# H115: J3 constraint for Stage 2a (elbow boundary prevention)
# J3 range of -45° to -30° ensures 10-20° margin from boundary (-25.1°)
STAGE2A_J3_MIN_DEG = -45.0  # J3 minimum (elbow-down)
STAGE2A_J3_MAX_DEG = -30.0  # J3 maximum (margin from -25.1° boundary)

# H115: Max joint change per step (IK flip prevention)
MAX_JOINT_CHANGE_DEG = 45.0  # H129: 30→45° to allow larger elbow transitions in Stage 2a

# H115: Stage 2a step count (increased for smoother motion)
# H133: 450→600（33%増加）- 関節変化速度を0.054°/step→0.040°/stepに低下
# H135: STAGE2A_STEPS=750 (+25% from H133's 600)
# H133: 99.4%到達、あと4ステップで成功。+25%マージンで100%見込み
# J3速度: 0.040°/step → 0.032°/step (-20%)
# H134: Stage 2a-1.75 subdivision は逆効果（12.5%完了率）のためREVERT
STAGE2A_STEPS = 1500  # H138: 750 → 1500 (Option B2 per TIM-002 analysis)

# H136: Stage 2a-2 target X削減 (0.45 → 0.42)
# H144: さらにX削減 (0.42 → 0.38) - J3_L=-67.8deg長時間飽和がNaN原因
# Root cause: J3_L (LEFT arm) が-60°~-73°の特異点近傍に到達
# Solution: target X削減でJ3_L excursionを-55°以下に抑制
STAGE2A_POSITIONS = {
    "2a-2": {"L": (0.38, -0.19, 1.05), "R": (0.38, 0.19, 1.05)},
}

# H137: Maximum joint velocity for velocity clamping (rad/s)
# H136 (1.0 rad/s) was too restrictive - caused trajectory tracking failure
# Required velocity at Stage 2a-1.25 step 550: 5.18 rad/s
# 3.0 rad/s allows 58% trajectory tracking which prevents grip loss
MAX_JOINT_VELOCITY = 3.0  # rad/s (H137: relaxed from 1.0 for trajectory tracking)

# H145: Maximum end-effector velocity for position-based interpolation (m/s)
# Calculation: MAX_JOINT_VELOCITY(3.0) × average_link_length(0.4m) × safety_factor(0.5) = 0.6 m/s
MAX_EE_VELOCITY = 0.6  # m/s (H145: EE velocity limit for Diff IK position-based interpolation)

# =============================================================================
# H164: Force R Threshold-based Dynamic Velocity Control
# =============================================================================
# Root cause: LL-2026-01-15-NAN-001 - Stage B Force R spikes (24.7N) at step 50
#             leading to Force L explosion (1148N) and NaN at step 310
# Solution: Monitor Force R during Stage B, reduce velocity when high
# Hysteresis: 20N/15N threshold prevents velocity oscillation
FORCE_R_HIGH = 25.0      # N - Reduce velocity when Force R exceeds this (H168: 20→25)
FORCE_R_LOW = 10.0       # N - Restore velocity when Force R drops below this (H168: 15→10)
VEL_REDUCED = 0.50       # rad/s - Reduced velocity when Force R is high (H184: 0.25→0.50 restore)
FORCE_L_ABORT = 170.0    # N - Safety abort threshold for Force L collapse prevention (H173: 100→170)

# H165: Force L direct monitoring for Stage B stabilization
# Root cause: LL-2026-01-15-NAN-002 - Force R and Force L have weak correlation
# Force R spikes resolve in 1-2 steps, but Force L accumulates independently
# Solution: Monitor Force L directly, reduce velocity when > 50N
FORCE_L_HIGH_THRESHOLD = 30.0    # N - Reduce velocity when Force L exceeds this (H195: 50.0→30.0)
FORCE_L_LOW_THRESHOLD = 30.0     # N - Restore velocity when Force L drops below this
FORCE_L_REDUCED_VELOCITY = 0.15  # rad/s - Reduced velocity (H195: 0.30→0.15, more conservative)

PHASE45_LEFT_JOINTS = [
    +1.074466,  # panda_joint1
    -0.234999,  # panda_joint2
    +0.191661,  # panda_joint3
    -2.437814,  # panda_joint4
    -1.724246,  # panda_joint5
    +1.844539,  # panda_joint6
    -1.691919,  # panda_joint7
]

PHASE45_RIGHT_JOINTS = [
    -1.095666,  # panda_joint1
    +1.319994,  # panda_joint2
    -0.028137,  # panda_joint3
    -2.222626,  # panda_joint4
    +1.997859,  # panda_joint5
    +1.370971,  # panda_joint6
    -1.136364,  # panda_joint7
]

# Phase 5: ケーブルをフック上方に配置（90度回転後）
# 2026-01-06: フック掛け改善 - グリッパー間距離46cmでの高さ計算
# ケーブル60cm、グリッパー間46cm → スラック14cm
# ケーブル中央Z=0.92（フック上端0.90より上）に必要なグリッパーZ≈1.09m
# EE Left:  (0.75, 0.0, 1.09) - 前方（実測に近い値）
# EE Right: (0.30, 0.0, 1.09) - 後方
WAYPOINT_PHASE5_LEFT = (0.70, -0.222, 1.09)    # H126: Y=-0.222（短縮Y位置維持、delta=0.010）
WAYPOINT_PHASE5_RIGHT = (0.30, 0.227, 1.09)    # H126: Y=0.227（短縮Y位置維持、delta=0.010）

PHASE5_LEFT_JOINTS = [
    +2.232521,  # panda_joint1
    -0.373101,  # panda_joint2
    -0.744538,  # panda_joint3
    -2.483282,  # panda_joint4
    -1.801206,  # panda_joint5
    +1.463039,  # panda_joint6
    -1.742424,  # panda_joint7
]

PHASE5_RIGHT_JOINTS = [
    -1.244636,  # panda_joint1
    +1.333559,  # panda_joint2
    -0.047248,  # panda_joint3
    -2.240248,  # panda_joint4
    +1.841059,  # panda_joint5
    +1.400613,  # panda_joint6
    -1.186869,  # panda_joint7
]

# =============================================================================
# Friction Parameters (V-groove Finger)
# =============================================================================
# V-groove finger friction for cable gripping
# Higher friction improves vertical lift stability
FINGER_STATIC_FRICTION = 1.2   # static_friction >= 1.0
FINGER_DYNAMIC_FRICTION = 1.0  # H186: 2.0→1.0 rollback (H185 caused Phase 2 grip loss)
FINGER_RESTITUTION = 0.0       # No bounce for stable grasp

# Cable friction (moderate for realistic behavior)
CABLE_STATIC_FRICTION = 0.8
CABLE_DYNAMIC_FRICTION = 0.6
CABLE_RESTITUTION = 0.1

# Gripper close position for V-groove finger
# Tighter close for V-groove to ensure cable seats in groove
# 2026-01-07: 0.002に戻す（0.001は強すぎてケーブル不安定化）
# v66ベースライン: 0.002維持（0.001は強すぎてケーブル不安定化 - H096/v70で確認）
GRIPPER_CLOSE = 0.002  # 2mm gap (4mm total opening)

# =============================================================================
# Phase 5.5: ケーブルをフックV谷に下降
# =============================================================================
# 2026-01-06: フック掛け改善 - グリッパー間距離46cmでの高さ計算
# フック位置: (0.50, 0.0, 0.90)、V谷: Z≈0.83
# ケーブル中央Z=0.85（V谷）に必要なグリッパーZ≈1.02m
# EE Left:  (0.75, 0.0, 1.02) - 前方
# EE Right: (0.30, 0.0, 1.02) - 後方
WAYPOINT_PHASE55_LEFT = (0.70, -0.222, 1.02)   # H126: Y=-0.222（短縮Y位置維持、delta=0.010）
WAYPOINT_PHASE55_RIGHT = (0.30, 0.227, 1.02)   # H126: Y=0.227（短縮Y位置維持、delta=0.010）

# Phase 5.5 joint angles (IK計算済み 2026-01-06)
PHASE55_LEFT_JOINTS = [
    -0.298644,  # panda_joint1
    -0.369053,  # panda_joint2
    +1.220886,  # panda_joint3
    -2.284359,  # panda_joint4
    -1.732661,  # panda_joint5
    +2.299165,  # panda_joint6
    -1.590909,  # panda_joint7
]
PHASE55_RIGHT_JOINTS = [
    -0.800047,  # panda_joint1
    +1.290010,  # panda_joint2
    -0.010425,  # panda_joint3
    -2.134444,  # panda_joint4
    +2.316935,  # panda_joint5
    +1.368647,  # panda_joint6
    -0.984848,  # panda_joint7
]

# =============================================================================
# Phase 6: Release and Retreat
# =============================================================================
# After lowering cable onto hook, release grippers and retreat
# 案D リリースシーケンス (2026-01-03 テスト成功):
#   Step 1: Phase 5.5位置で静止（振動安定化）
#   Step 2: グリッパー徐々にオープン
#   Step 3: Phase 6退避位置へ移動

# Release sequence parameters
RELEASE_STABILIZE_STEPS = 150  # 静止ステップ（振動安定化）- 2026-01-04: 100→150に増加
RELEASE_GRIPPER_STEPS = 150    # グリッパー開放ステップ（徐々に開く）
PHASE55_TO_6_STEPS = 200       # Phase 5.5→6 移動ステップ

# 2026-01-06: 90度回転後の退避位置（X軸方向配置）
# Left: X=0.69→0.55（-14cm）、Z=0.85→0.95（+10cm）
# Right: X=0.11→0.25（+14cm）、Z=0.85→0.95（+10cm）
WAYPOINT_PHASE6_LEFT = (0.55, 0.0, 0.95)    # Retreat: X-14cm, Z+10cm
WAYPOINT_PHASE6_RIGHT = (0.25, 0.0, 0.95)   # Retreat: X+14cm, Z+10cm

# Phase 5.5 and 6 use cumulative Diff IK from Phase 5 position (no IK joint angles needed)

# =============================================================================
# Phase 7: Home Position (Return to Phase 1)
# =============================================================================
# After release and retreat, return to initial hover position for next cycle
# Reuses Phase 1 position and joint angles (no additional IK needed)
#
# Transition: Phase 6 → Phase 7
#   Left:  11.1cm (X:-11cm, Y:+1.5cm, Z:-0.5cm)
#   Right: 19.8cm (X:-11cm, Y:+16.5cm, Z:-0.5cm)
#
# Safety: Gripper open, no cable - clear air path

WAYPOINT_PHASE7_LEFT = WAYPOINT_PHASE1_LEFT    # (0.29, -0.25, 0.895) H152
WAYPOINT_PHASE7_RIGHT = WAYPOINT_PHASE1_RIGHT  # (0.29, +0.25, 0.895) H152

# Reuse Phase 1 joint angles
PHASE7_LEFT_JOINTS = LEFT_ARM_INIT_JOINTS
PHASE7_RIGHT_JOINTS = RIGHT_ARM_INIT_JOINTS

# =============================================================================
# Phase 8: Cycle Reset (Loop Control)
# =============================================================================
# After returning to home position, prepare for next cycle or terminate
#
# Purpose: Manage continuous episodes for RL training
#   - Reset cable to initial position
#   - Update cycle counter
#   - Transition to Phase 2 (Grasp) or terminate
#
# Flow:
#   Phase 7 (Home) → Phase 8 (Cycle Reset) → Phase 2 (Grasp) or End
#
# Note: Phase 8 is a control phase, not a motion phase
#   - No new waypoint needed (stays at Phase 7 position)
#   - Cable reset is handled by simulation API

# Cycle control parameters
ENABLE_CONTINUOUS_CYCLE = True   # Enable multi-cycle operation
MAX_CYCLES = 5                   # Maximum number of cycles (0 = unlimited)
CYCLE_RESET_STABILIZATION_STEPS = 500  # Steps to wait after cable reset (200→500 for NaN prevention)

# Phase 8 does not have waypoints - it's a control/reset phase
# Robot stays at Phase 7 (Home) position during Phase 8

# Phase 8 actions (for state machine implementation)
PHASE8_ACTION = "cycle_reset"    # Action type
PHASE8_NEXT_PHASE = 2            # Next phase after reset (Phase 2: Grasp)
PHASE8_END_CONDITION = "max_cycles"  # Termination condition

# =============================================================================
# 成功構成（13.6cmリフト達成時 - 2026-01-02）
# =============================================================================
# これらの値は dual_arm_cfg.py から参照される
# 変更時は必ずテストで動作確認すること

# アクチュエータdamping値
# 2026-01-02: 13.6cmリフト達成時の値
# 2026-01-04: 40.0に誤変更されたためリフト距離が5.1cmに低下
# バックアップ参照: dual_arm_cfg.py.bak (Dec 29 00:53)
# H115: 40→80に増加（under-damping解消、振動抑制）
PANDA_SHOULDER_DAMPING = 80.0  # panda_joint[1-4] damping (H115: 40→80)
PANDA_FOREARM_DAMPING = 80.0   # panda_joint[5-7] damping (H115: 40→80)
PANDA_HAND_DAMPING = 100.0     # panda_finger_joint damping

# アクチュエータstiffness値 (H111: 400→600で追従性向上)
PANDA_SHOULDER_STIFFNESS = 600.0  # panda_joint[1-4] stiffness (H111: 50%増)
PANDA_FOREARM_STIFFNESS = 600.0   # panda_joint[5-7] stiffness (H111: 50%増)
PANDA_HAND_STIFFNESS = 4000.0     # panda_finger_joint stiffness (H175: 6000→4000 restore, Phase 3 NaN fix)

# グリッパークランプ設定
CLAMP_STEPS = 300  # グリッパーを徐々に閉じるステップ数（100→300: 接触力スパイク抑制）

# H174: Force ABORT閾値（Stage B.5 grip loss防止）
FORCE_R_ABORT = 5.0  # 右グリッパーForce閾値 [N] - H181: 200→5N (grip loss検出閾値修正)

# 物理設定
FRICTION = 5.0  # ケーブル・フィンガー摩擦係数

# キネマティクス補正
Z_OFFSET_COMPENSATION = 0.1034  # IKターゲット計算時のZ補正（Isaac Lab URDFとの差分）
FINGERTIP_OFFSET = 0.1123      # panda_hand → fingertip距離（96.1mm接触面中心）

# リリースシーケンス Phase 5.5
PHASE_5_5_Z = 0.75  # v43: V谷下降目標Z（0.80→0.75でフック掛け改善テスト）

# H102: Part 2 3段階分割（エルボー境界対応）
# 境界: Z=0.99-1.00でJ3が-31度→+37度にジャンプ（68度のエルボーフリップ）
# Part 2を3段階に分割し、境界（Z=0.99-1.01）を低速で通過
PART2A_TARGET_Z = 0.99   # 境界前（J3 < 0維持）
PART2B_TARGET_Z = 1.01   # 境界通過後（J3 > 0へ遷移）
PART2C_TARGET_Z = 1.05   # 最終目標

PART2A_STEPS = 50        # 境界前（通常速度）
PART2B_STEPS = 100       # 境界通過（超低速 - 0.02m/100step）
PART2C_STEPS = 50        # 境界後（通常速度）

# =============================================================================
# H191: B.5c Mid-Stabilization (Force spike suppression)
# =============================================================================
# Purpose: Insert stabilization point before B.5c step 36 to prevent Force spike (L=13305.8N)
# Reference: LL-2026-01-23-FORCE-001, H190 PARTIAL_SUCCESS result
# Pattern: Same as H190 stabilization (hold_position + settle)
H191_B5C_MID_STABILIZE_STEPS = 30  # Stabilization steps before B.5c step 36
H191_B5C_PART1_STEPS = 36          # Steps before stabilization point (step 36)
H191_B5C_PART2_STEPS = 98          # Remaining steps after stabilization (134-36=98)

# =============================================================================
# H192: B.5c Part 2 Split (Force spike suppression at Part 2 step 26)
# =============================================================================
# Purpose: Split Part 2 (98 steps) into Part 2A + mid-stabilization + Part 2B
# Reference: LL-2026-01-23-FORCE-001/002, H191 result (spike at Part 2 step 26)
# Pattern: Same as H191 mid-stabilization (hold_position + settle)
# Calculation: Part 2 step 26 < Part 2A (49 steps) → step 26 is within Part 2A
# After Part 2A, stabilization allows physics to settle before Part 2B
H192_B5C_PART2A_STEPS = 49                # First half of Part 2 (49 steps)
H192_B5C_PART2_MID_STABILIZE_STEPS = 30   # Stabilization after Part 2A
H192_B5C_PART2B_STEPS = 49                # Second half of Part 2 (49 steps)

# =============================================================================
# H193: Proportional Follow (Subagent Recommendation)
# =============================================================================
# Purpose: Maintain left grip during Part 2B by proportionally following right arm movement
# Reference: franka-advisor subagent recommendation (confidence: medium)
# Rationale: 60% follow ratio distributes cable tension, prevents left grip loss
# Pattern: Left arm X-axis follows Right arm X-axis by LEFT_FOLLOW_RATIO
H193_LEFT_FOLLOW_RATIO = 0.6           # Left arm follows 40% of right arm X movement (H195: 0.6→0.4)
H193_FOLLOW_AXIS = ["X"]               # Follow only X-axis (cable tension direction)
H193_MIN_THRESHOLD_CM = 0.5            # Minimum movement threshold (0.5cm)
