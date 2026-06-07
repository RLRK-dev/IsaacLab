#!/usr/bin/env python3
"""
Calculate intermediate waypoint between Phase 4 and Phase 5.
Analyze joint angle changes to determine if intermediate points are needed.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import solve_ik_best

# Robot base positions (from grid=6 optimization)
LEFT_BASE = np.array([0.3360, -0.4200, 1.2800])
RIGHT_BASE = np.array([0.3360, 0.2960, 1.2800])

# Wall mount quaternion (w, x, y, z)
WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

# Joint limits
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Phase 4 and 5 EE positions
PHASE4_LEFT = np.array([0.25, -0.15, 1.00])
PHASE4_RIGHT = np.array([0.25, +0.15, 1.00])
PHASE5_LEFT = np.array([0.20, -0.25, 0.80])
PHASE5_RIGHT = np.array([0.20, 0.00, 0.80])

# Threshold for needing intermediate waypoint
JOINT_CHANGE_THRESHOLD_DEG = 30.0

def compute_joint_margin(joints):
    """Compute minimum distance to joint limits in degrees."""
    margin_lower = joints - JOINT_LIMITS_LOWER
    margin_upper = JOINT_LIMITS_UPPER - joints
    margin_rad = np.minimum(margin_lower, margin_upper).min()
    return np.degrees(margin_rad)

def format_joints_for_config(joints, name):
    """Format joints for task_config.py"""
    lines = [f"{name} = ["]
    for i, j in enumerate(joints):
        deg = np.degrees(j)
        sign = "+" if j >= 0 else ""
        lines.append(f"    {sign}{j:.6f},  # panda_joint{i+1}: {sign}{deg:.1f} deg")
    lines.append("]")
    return "\n".join(lines)

def solve_and_print(name, ee_left, ee_right):
    """Solve IK for both arms and return joint angles."""
    print(f"\n{'=' * 60}")
    print(f"{name}")
    print(f"{'=' * 60}")
    print(f"  Left EE:  {ee_left}")
    print(f"  Right EE: {ee_right}")

    # Left arm
    left_success, left_joints, _ = solve_ik_best(
        ee_left, LEFT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=50
    )

    # Right arm
    right_success, right_joints, _ = solve_ik_best(
        ee_right, RIGHT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=50
    )

    if left_success and right_success:
        left_margin = compute_joint_margin(left_joints)
        right_margin = compute_joint_margin(right_joints)
        print(f"  Left margin:  {left_margin:.1f}°")
        print(f"  Right margin: {right_margin:.1f}°")
        return left_joints, right_joints
    else:
        print(f"  IK FAILED: left={left_success}, right={right_success}")
        return None, None

def analyze_joint_changes(joints1, joints2, name1, name2, arm_name):
    """Analyze joint angle changes between two configurations."""
    if joints1 is None or joints2 is None:
        return None

    delta = np.degrees(joints2 - joints1)
    max_change = np.max(np.abs(delta))
    max_joint = np.argmax(np.abs(delta)) + 1

    print(f"\n  {arm_name}: {name1} → {name2}")
    print(f"    Joint changes (deg): ", end="")
    for i, d in enumerate(delta):
        sign = "+" if d >= 0 else ""
        exceed = " ⚠️" if abs(d) > JOINT_CHANGE_THRESHOLD_DEG else ""
        print(f"J{i+1}:{sign}{d:.1f}{exceed}", end=" ")
    print()
    print(f"    Max change: Joint{max_joint} = {max_change:.1f}°", end="")
    if max_change > JOINT_CHANGE_THRESHOLD_DEG:
        print(f" ⚠️ EXCEEDS {JOINT_CHANGE_THRESHOLD_DEG}° THRESHOLD")
    else:
        print(" ✅ OK")

    return delta, max_change, max_joint

def main():
    print("=" * 60)
    print("Phase 4→5 Intermediate Waypoint Analysis")
    print("=" * 60)
    print(f"\nJoint change threshold: {JOINT_CHANGE_THRESHOLD_DEG}°")

    # Calculate waypoints
    mid_left = (PHASE4_LEFT + PHASE5_LEFT) / 2
    mid_right = (PHASE4_RIGHT + PHASE5_RIGHT) / 2

    # Solve IK for each phase
    p4_left, p4_right = solve_and_print("Phase 4 (Hook)", PHASE4_LEFT, PHASE4_RIGHT)
    p45_left, p45_right = solve_and_print("Phase 4.5 (Intermediate)", mid_left, mid_right)
    p5_left, p5_right = solve_and_print("Phase 5 (Place)", PHASE5_LEFT, PHASE5_RIGHT)

    # Analyze direct Phase 4 → 5 transition
    print("\n" + "=" * 60)
    print("Direct Transition Analysis: Phase 4 → Phase 5")
    print("=" * 60)

    analyze_joint_changes(p4_left, p5_left, "P4", "P5", "Left Arm")
    analyze_joint_changes(p4_right, p5_right, "P4", "P5", "Right Arm")

    # Analyze with intermediate waypoint
    print("\n" + "=" * 60)
    print("With Intermediate Waypoint: Phase 4 → 4.5 → 5")
    print("=" * 60)

    analyze_joint_changes(p4_left, p45_left, "P4", "P4.5", "Left Arm")
    analyze_joint_changes(p45_left, p5_left, "P4.5", "P5", "Left Arm")

    analyze_joint_changes(p4_right, p45_right, "P4", "P4.5", "Right Arm")
    analyze_joint_changes(p45_right, p5_right, "P4.5", "P5", "Right Arm")

    # Summary
    print("\n" + "=" * 60)
    print("Summary & Recommendation")
    print("=" * 60)

    # Check if intermediate point is needed
    direct_left_delta = np.degrees(p5_left - p4_left) if p4_left is not None and p5_left is not None else None
    direct_right_delta = np.degrees(p5_right - p4_right) if p4_right is not None and p5_right is not None else None

    if direct_left_delta is not None and direct_right_delta is not None:
        max_left = np.max(np.abs(direct_left_delta))
        max_right = np.max(np.abs(direct_right_delta))
        max_direct = max(max_left, max_right)

        if max_direct > JOINT_CHANGE_THRESHOLD_DEG:
            print(f"\n⚠️  Direct transition has {max_direct:.1f}° max joint change")
            print(f"   RECOMMENDATION: Add intermediate waypoint (Phase 4.5)")

            # Print config for intermediate waypoint
            if p45_left is not None and p45_right is not None:
                print("\n" + "=" * 60)
                print("Copy-paste for task_config.py:")
                print("=" * 60)
                print(f"\n# Phase 4.5: Intermediate (between Hook and Place)")
                print(f"WAYPOINT_PHASE45_LEFT = ({mid_left[0]:.4f}, {mid_left[1]:.4f}, {mid_left[2]:.4f})")
                print(f"WAYPOINT_PHASE45_RIGHT = ({mid_right[0]:.4f}, {mid_right[1]:.4f}, {mid_right[2]:.4f})")
                print()
                print(format_joints_for_config(p45_left, 'PHASE45_LEFT_JOINTS'))
                print()
                print(format_joints_for_config(p45_right, 'PHASE45_RIGHT_JOINTS'))
        else:
            print(f"\n✅ Direct transition is smooth (max {max_direct:.1f}° < {JOINT_CHANGE_THRESHOLD_DEG}°)")
            print("   No intermediate waypoint needed")

if __name__ == "__main__":
    main()
