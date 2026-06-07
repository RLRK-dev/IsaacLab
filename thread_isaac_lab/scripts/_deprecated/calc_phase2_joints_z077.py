#!/usr/bin/env python3
"""
Calculate Phase 2 joint angles for CABLE_Z = 0.77
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

# Gripper down quaternion, fingers open in X
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])

# Joint limits for margin calculation
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

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

def main():
    print("=" * 60)
    print("Phase 2 Joint Calculation for CABLE_Z = 0.77")
    print("=" * 60)

    # Phase 2 EE positions (updated for Z=0.77)
    EE_LEFT = np.array([0.30, -0.285, 0.77])
    EE_RIGHT = np.array([0.30, +0.285, 0.77])

    print(f"\nTarget EE Positions:")
    print(f"  Left:  {EE_LEFT}")
    print(f"  Right: {EE_RIGHT}")

    print(f"\nRobot Base Positions:")
    print(f"  Left:  {LEFT_BASE}")
    print(f"  Right: {RIGHT_BASE}")

    # Solve IK for left arm
    print("\n" + "=" * 60)
    print("Left Arm IK")
    print("=" * 60)

    left_success, left_joints, left_margin = solve_ik_best(
        EE_LEFT, LEFT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=50
    )

    if left_success:
        actual_margin = compute_joint_margin(left_joints)
        print(f"  Status: SUCCESS")
        print(f"  Joint margin: {actual_margin:.1f}°")
        print(f"\n{format_joints_for_config(left_joints, 'PHASE2_LEFT_JOINTS')}")
    else:
        print(f"  Status: FAILED")

    # Solve IK for right arm
    print("\n" + "=" * 60)
    print("Right Arm IK")
    print("=" * 60)

    right_success, right_joints, right_margin = solve_ik_best(
        EE_RIGHT, RIGHT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=50
    )

    if right_success:
        actual_margin = compute_joint_margin(right_joints)
        print(f"  Status: SUCCESS")
        print(f"  Joint margin: {actual_margin:.1f}°")
        print(f"\n{format_joints_for_config(right_joints, 'PHASE2_RIGHT_JOINTS')}")
    else:
        print(f"  Status: FAILED")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if left_success and right_success:
        left_margin_deg = compute_joint_margin(left_joints)
        right_margin_deg = compute_joint_margin(right_joints)
        min_margin = min(left_margin_deg, right_margin_deg)

        print(f"  Left margin:  {left_margin_deg:.1f}°")
        print(f"  Right margin: {right_margin_deg:.1f}°")
        print(f"  Worst-case:   {min_margin:.1f}°")
        print(f"\n  Status: ✅ Both arms have valid IK solutions")

        # Print copy-paste ready code
        print("\n" + "=" * 60)
        print("Copy-paste for task_config.py:")
        print("=" * 60)
        print()
        print("# Phase 2: Grasp (Z=0.77)")
        print(format_joints_for_config(left_joints, 'PHASE2_LEFT_JOINTS'))
        print()
        print(format_joints_for_config(right_joints, 'PHASE2_RIGHT_JOINTS'))
    else:
        print(f"  Status: ❌ IK failed for one or both arms")

if __name__ == "__main__":
    main()
