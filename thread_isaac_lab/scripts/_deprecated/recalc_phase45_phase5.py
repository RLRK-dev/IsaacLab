#!/usr/bin/env python3
"""
Recalculate Phase 4.5 and Phase 5 based on new Phase 4 position.
Ensure elbow continuity (J5 < 0) throughout.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import solve_ik_best, franka_IK_EE_with_base

# Robot base positions
LEFT_BASE = np.array([0.3360, -0.4200, 1.2800])
RIGHT_BASE = np.array([0.3360, 0.2960, 1.2800])

# Quaternions
WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

# Joint limits
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# NEW Phase 4 positions (elbow-down constrained)
NEW_PHASE4_LEFT = np.array([0.30, -0.16, 0.84])
NEW_PHASE4_RIGHT = np.array([0.30, +0.16, 0.84])

# NEW Phase 4 joints
NEW_PHASE4_LEFT_JOINTS = np.array([
    +1.017691, +0.985742, -0.121765, -2.253345, -2.198015, +1.598196, -2.220690
])
NEW_PHASE4_RIGHT_JOINTS = np.array([
    +0.844297, +1.469719, -0.588336, -2.457930, -2.499795, +1.354008, -1.448276
])

# Current Phase 5 positions (from optimization)
CURRENT_PHASE5_LEFT = np.array([0.20, -0.25, 0.80])
CURRENT_PHASE5_RIGHT = np.array([0.20, 0.00, 0.80])

def compute_joint_margin(joints):
    """Compute minimum distance to joint limits in degrees."""
    margin_lower = joints - JOINT_LIMITS_LOWER
    margin_upper = JOINT_LIMITS_UPPER - joints
    margin_rad = np.minimum(margin_lower, margin_upper).min()
    return np.degrees(margin_rad)

def check_joint_limits(joints):
    """Check if joints are within limits."""
    return np.all(joints >= JOINT_LIMITS_LOWER) and np.all(joints <= JOINT_LIMITS_UPPER)

def solve_ik_elbow_down(target_ee, base_pos):
    """Solve IK with elbow-down constraint (J5 < 0)."""
    best_joints = None
    best_margin = -float('inf')

    q7_values = np.linspace(-2.8, 2.8, 80)

    for q7 in q7_values:
        solutions = franka_IK_EE_with_base(
            target_ee, GRIPPER_DOWN_QUAT, base_pos, WALL_MOUNT_QUAT, q7
        )

        if solutions is None:
            continue

        for sol in solutions:
            if sol is None or sol.joints is None:
                continue

            joints = sol.joints

            # Elbow down constraint
            if joints[4] >= 0:
                continue

            if not check_joint_limits(joints):
                continue

            margin = compute_joint_margin(joints)
            if margin > best_margin:
                best_margin = margin
                best_joints = joints.copy()

    return best_joints, best_margin

def analyze_transition(joints1, joints2, name):
    """Analyze joint changes between two configurations."""
    delta = np.degrees(joints2 - joints1)
    max_change = np.max(np.abs(delta))

    print(f"  {name}:")
    print(f"    Changes: ", end="")
    for i, d in enumerate(delta):
        flag = "⚠" if abs(d) > 30 else ""
        print(f"J{i+1}:{d:+.0f}{flag} ", end="")
    print()
    print(f"    Max: {max_change:.1f}°", end="")
    if max_change <= 30:
        print(" ✅")
    else:
        print(" ⚠️ >30°")

    return max_change

def format_joints_for_config(joints, name):
    """Format joints for task_config.py"""
    lines = [f"{name} = ["]
    for i, j in enumerate(joints):
        deg = np.degrees(j)
        sign = "+" if j >= 0 else ""
        lines.append(f"    {sign}{j:.6f},  # panda_joint{i+1}: {sign}{deg:.1f} deg")
    lines.append("]")
    return "\n".join(lines)

def main():
    print("=" * 70)
    print("Phase 4.5 & Phase 5 Recalculation")
    print("=" * 70)
    print()
    print("New Phase 4 EE positions:")
    print(f"  Left:  {NEW_PHASE4_LEFT}")
    print(f"  Right: {NEW_PHASE4_RIGHT}")
    print()

    # Calculate Phase 4.5 (midpoint)
    phase45_left = (NEW_PHASE4_LEFT + CURRENT_PHASE5_LEFT) / 2
    phase45_right = (NEW_PHASE4_RIGHT + CURRENT_PHASE5_RIGHT) / 2

    print("=" * 70)
    print("Phase 4.5 (Intermediate)")
    print("=" * 70)
    print(f"  Left EE:  ({phase45_left[0]:.3f}, {phase45_left[1]:.3f}, {phase45_left[2]:.3f})")
    print(f"  Right EE: ({phase45_right[0]:.3f}, {phase45_right[1]:.3f}, {phase45_right[2]:.3f})")
    print()

    # Solve Phase 4.5 IK
    p45_left_joints, p45_left_margin = solve_ik_elbow_down(phase45_left, LEFT_BASE)
    p45_right_joints, p45_right_margin = solve_ik_elbow_down(phase45_right, RIGHT_BASE)

    if p45_left_joints is not None:
        print(f"  Left:  margin={p45_left_margin:.1f}°, J5={np.degrees(p45_left_joints[4]):.1f}° ✓")
    else:
        print(f"  Left:  FAILED")

    if p45_right_joints is not None:
        print(f"  Right: margin={p45_right_margin:.1f}°, J5={np.degrees(p45_right_joints[4]):.1f}° ✓")
    else:
        print(f"  Right: FAILED")

    # Phase 5
    print()
    print("=" * 70)
    print("Phase 5 (Place)")
    print("=" * 70)
    print(f"  Left EE:  {CURRENT_PHASE5_LEFT}")
    print(f"  Right EE: {CURRENT_PHASE5_RIGHT}")
    print()

    # Solve Phase 5 IK with elbow-down
    p5_left_joints, p5_left_margin = solve_ik_elbow_down(CURRENT_PHASE5_LEFT, LEFT_BASE)
    p5_right_joints, p5_right_margin = solve_ik_elbow_down(CURRENT_PHASE5_RIGHT, RIGHT_BASE)

    if p5_left_joints is not None:
        print(f"  Left:  margin={p5_left_margin:.1f}°, J5={np.degrees(p5_left_joints[4]):.1f}° ✓")
    else:
        print(f"  Left:  FAILED")

    if p5_right_joints is not None:
        print(f"  Right: margin={p5_right_margin:.1f}°, J5={np.degrees(p5_right_joints[4]):.1f}° ✓")
    else:
        print(f"  Right: FAILED")

    # Verify all transitions
    print()
    print("=" * 70)
    print("Transition Analysis")
    print("=" * 70)
    print()

    all_ok = True

    if p45_left_joints is not None and p45_right_joints is not None:
        print("Phase 4 → Phase 4.5:")
        max_left = analyze_transition(NEW_PHASE4_LEFT_JOINTS, p45_left_joints, "Left Arm")
        max_right = analyze_transition(NEW_PHASE4_RIGHT_JOINTS, p45_right_joints, "Right Arm")
        if max(max_left, max_right) > 30:
            all_ok = False
        print()

    if p45_left_joints is not None and p5_left_joints is not None:
        print("Phase 4.5 → Phase 5:")
        max_left = analyze_transition(p45_left_joints, p5_left_joints, "Left Arm")
        max_right = analyze_transition(p45_right_joints, p5_right_joints, "Right Arm")
        if max(max_left, max_right) > 30:
            all_ok = False
        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    if all_ok and p45_left_joints is not None and p5_left_joints is not None:
        print("✅ All transitions are smooth (<30° max change)")
        print()

        min_margin = min(p45_left_margin, p45_right_margin, p5_left_margin, p5_right_margin)
        print(f"Worst-case margin: {min_margin:.1f}°")
        print()

        # Output config
        print("=" * 70)
        print("Copy-paste for task_config.py:")
        print("=" * 70)
        print()

        # Phase 4 (confirmed)
        print("# Phase 4: Hook approach (elbow-down)")
        print(f"WAYPOINT_PHASE4_LEFT = ({NEW_PHASE4_LEFT[0]:.2f}, {NEW_PHASE4_LEFT[1]:.2f}, {NEW_PHASE4_LEFT[2]:.2f})")
        print(f"WAYPOINT_PHASE4_RIGHT = ({NEW_PHASE4_RIGHT[0]:.2f}, {NEW_PHASE4_RIGHT[1]:.2f}, {NEW_PHASE4_RIGHT[2]:.2f})")
        print()
        print(format_joints_for_config(NEW_PHASE4_LEFT_JOINTS, 'PHASE4_LEFT_JOINTS'))
        print()
        print(format_joints_for_config(NEW_PHASE4_RIGHT_JOINTS, 'PHASE4_RIGHT_JOINTS'))
        print()

        # Phase 4.5
        print("# Phase 4.5: Intermediate")
        print(f"WAYPOINT_PHASE45_LEFT = ({phase45_left[0]:.3f}, {phase45_left[1]:.3f}, {phase45_left[2]:.3f})")
        print(f"WAYPOINT_PHASE45_RIGHT = ({phase45_right[0]:.3f}, {phase45_right[1]:.3f}, {phase45_right[2]:.3f})")
        print()
        print(format_joints_for_config(p45_left_joints, 'PHASE45_LEFT_JOINTS'))
        print()
        print(format_joints_for_config(p45_right_joints, 'PHASE45_RIGHT_JOINTS'))
        print()

        # Phase 5
        print("# Phase 5: Place")
        print(f"WAYPOINT_PHASE5_LEFT = ({CURRENT_PHASE5_LEFT[0]:.2f}, {CURRENT_PHASE5_LEFT[1]:.2f}, {CURRENT_PHASE5_LEFT[2]:.2f})")
        print(f"WAYPOINT_PHASE5_RIGHT = ({CURRENT_PHASE5_RIGHT[0]:.2f}, {CURRENT_PHASE5_RIGHT[1]:.2f}, {CURRENT_PHASE5_RIGHT[2]:.2f})")
        print()
        print(format_joints_for_config(p5_left_joints, 'PHASE5_LEFT_JOINTS'))
        print()
        print(format_joints_for_config(p5_right_joints, 'PHASE5_RIGHT_JOINTS'))

    else:
        print("❌ Some transitions exceed 30° or IK failed")
        print("   Manual adjustment may be needed")

if __name__ == "__main__":
    main()
