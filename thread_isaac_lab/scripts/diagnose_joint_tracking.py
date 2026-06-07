#!/usr/bin/env python3
"""
H149 Diagnostic Script: Joint Position Tracking Analysis

Compares:
1. Target joint angles (from IK)
2. Actual joint angles (from simulation)
3. FK(Target joints) - expected EE position
4. FK(Actual joints) - computed EE from actual joints
5. Simulated EE position (from Isaac Sim)

This helps identify whether tracking errors come from:
- IK computation (FK(Target) != expected EE)
- Joint tracking (Actual joints != Target joints)
- Simulation discrepancy (Sim EE != FK(Actual))
"""

import numpy as np
import torch
import sys
import os

# Add path for imports
sys.path.insert(0, "/home/rlrk/IsaacLab")

from thread_isaac_lab.configs.task_config import (
    LEFT_ARM_INIT_JOINTS,
    RIGHT_ARM_INIT_JOINTS,
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
)
from thread_isaac_lab.scripts.franka_analytical_ik import forward_kinematics


def analyze_tracking():
    """Analyze joint tracking without Isaac Sim (pure math check)."""
    print("=" * 70)
    print("H149 Diagnostic: Joint Tracking Analysis (Pure Math)")
    print("=" * 70)

    # Target joints
    target_left = np.array(LEFT_ARM_INIT_JOINTS)
    target_right = np.array(RIGHT_ARM_INIT_JOINTS)

    print("\n[1] Target Joint Angles (from task_config.py):")
    print(f"  Left:  {np.degrees(target_left).round(1)} deg")
    print(f"  Right: {np.degrees(target_right).round(1)} deg")

    # Compute FK for target joints (in robot base frame)
    T_left = forward_kinematics(target_left)
    T_right = forward_kinematics(target_right)

    ee_local_left = T_left[:3, 3]
    ee_local_right = T_right[:3, 3]

    print("\n[2] FK(Target) - EE Position in Robot Base Frame:")
    print(f"  Left:  ({ee_local_left[0]:.4f}, {ee_local_left[1]:.4f}, {ee_local_left[2]:.4f})")
    print(f"  Right: ({ee_local_right[0]:.4f}, {ee_local_right[1]:.4f}, {ee_local_right[2]:.4f})")

    # Transform to world frame
    robot_left_base = np.array(ROBOT_LEFT_BASE[:3])
    robot_right_base = np.array(ROBOT_RIGHT_BASE[:3])

    # Robot bases are rotated 90° around Y axis (ROBOT_BASE_QUAT_WXYZ = 0.7071, 0, 0.7071, 0)
    # Rotation matrix for 90° Y rotation: [cos90, 0, sin90; 0, 1, 0; -sin90, 0, cos90]
    # = [0, 0, 1; 0, 1, 0; -1, 0, 0]
    # So: X_world = Z_local, Y_world = Y_local, Z_world = -X_local
    # Wait, this is for the standard convention. Let's just apply the rotation properly.
    # 90° rotation around Y: (x,y,z) -> (z, y, -x)
    # But we need to consider the robot is looking in -X direction after rotation.
    # FK gives position in robot base frame. After 90° Y rotation:
    # new_x = old_z, new_y = old_y, new_z = -old_x
    ee_world_left = robot_left_base + np.array([ee_local_left[2], ee_local_left[1], -ee_local_left[0]])
    ee_world_right = robot_right_base + np.array([ee_local_right[2], ee_local_right[1], -ee_local_right[0]])

    print("\n[3] FK(Target) - EE Position in World Frame:")
    print(f"  Robot Left Base:  ({robot_left_base[0]:.4f}, {robot_left_base[1]:.4f}, {robot_left_base[2]:.4f})")
    print(f"  Robot Right Base: ({robot_right_base[0]:.4f}, {robot_right_base[1]:.4f}, {robot_right_base[2]:.4f})")
    print(f"  Left EE (world):  ({ee_world_left[0]:.4f}, {ee_world_left[1]:.4f}, {ee_world_left[2]:.4f})")
    print(f"  Right EE (world): ({ee_world_right[0]:.4f}, {ee_world_right[1]:.4f}, {ee_world_right[2]:.4f})")

    # Expected target EE (from task_config.py comments)
    expected_left = np.array([0.29, -0.285, 0.895])
    expected_right = np.array([0.29, +0.285, 0.895])

    print("\n[4] Expected EE Position (from IK target):")
    print(f"  Left:  ({expected_left[0]:.4f}, {expected_left[1]:.4f}, {expected_left[2]:.4f})")
    print(f"  Right: ({expected_right[0]:.4f}, {expected_right[1]:.4f}, {expected_right[2]:.4f})")

    # Compute error
    error_left = ee_world_left - expected_left
    error_right = ee_world_right - expected_right

    print("\n[5] FK vs Expected Error (Target joints → FK → compare to expected):")
    print(f"  Left error:  ({error_left[0]*100:.1f}, {error_left[1]*100:.1f}, {error_left[2]*100:.1f}) cm")
    print(f"  Right error: ({error_right[0]*100:.1f}, {error_right[1]*100:.1f}, {error_right[2]*100:.1f}) cm")
    print(f"  Left distance: {np.linalg.norm(error_left)*100:.1f} cm")
    print(f"  Right distance: {np.linalg.norm(error_right)*100:.1f} cm")

    # Cable position
    cable_z = 0.755  # From CABLE_Z in task_config.py
    fingertip_offset = 0.1123  # From FINGERTIP_OFFSET

    print("\n[6] Distance Analysis:")
    print(f"  Cable Z: {cable_z:.4f} m")
    print(f"  Fingertip offset (below panda_hand): {fingertip_offset:.4f} m")
    expected_panda_hand_z = cable_z + fingertip_offset
    print(f"  Expected panda_hand Z for grasp: {expected_panda_hand_z:.4f} m")
    print(f"  FK panda_hand Z (left):  {ee_world_left[2]:.4f} m")
    print(f"  FK panda_hand Z (right): {ee_world_right[2]:.4f} m")
    print(f"  Z error left:  {(ee_world_left[2] - expected_panda_hand_z)*100:.1f} cm")
    print(f"  Z error right: {(ee_world_right[2] - expected_panda_hand_z)*100:.1f} cm")

    # Fingertip position
    fingertip_z_left = ee_world_left[2] - fingertip_offset
    fingertip_z_right = ee_world_right[2] - fingertip_offset

    print("\n[7] Fingertip Position (panda_hand Z - offset):")
    print(f"  Left fingertip Z:  {fingertip_z_left:.4f} m (target cable: {cable_z:.4f})")
    print(f"  Right fingertip Z: {fingertip_z_right:.4f} m (target cable: {cable_z:.4f})")
    print(f"  Left fingertip-cable Z delta:  {(fingertip_z_left - cable_z)*100:.1f} cm")
    print(f"  Right fingertip-cable Z delta: {(fingertip_z_right - cable_z)*100:.1f} cm")

    print("\n" + "=" * 70)
    print("DIAGNOSIS SUMMARY:")
    print("=" * 70)

    if np.linalg.norm(error_left) > 0.05 or np.linalg.norm(error_right) > 0.05:
        print("⚠️ ISSUE DETECTED: FK(Target joints) does not match expected EE position")
        print("   This indicates IK solution or world frame transform error")
    else:
        print("✓ FK(Target joints) matches expected EE position")
        print("   Issue may be in simulation joint tracking")


if __name__ == "__main__":
    analyze_tracking()
