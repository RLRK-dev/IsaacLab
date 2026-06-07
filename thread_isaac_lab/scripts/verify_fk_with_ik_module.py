#!/usr/bin/env python3
"""
FK Verification using IK module's FK function

Uses the same FK implementation as the IK solver to verify consistency.

T1タスク: 2026-01-02
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
sys.path.insert(0, "/home/rlrk/IsaacLab")

import numpy as np
from scipy.spatial.transform import Rotation

# Import FK from IK module (same implementation used for IK)
from thread_isaac_lab.scripts.franka_analytical_ik import forward_kinematics

# Project imports
from thread_isaac_lab.configs.task_config import (
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    ROBOT_BASE_QUAT_WXYZ,
    # Phase 1
    WAYPOINT_PHASE1_LEFT,
    WAYPOINT_PHASE1_RIGHT,
    LEFT_ARM_INIT_JOINTS,
    RIGHT_ARM_INIT_JOINTS,
    # Phase 2
    WAYPOINT_PHASE2_LEFT,
    WAYPOINT_PHASE2_RIGHT,
    PHASE2_LEFT_JOINTS,
    PHASE2_RIGHT_JOINTS,
    # Phase 3
    WAYPOINT_PHASE3_LEFT,
    WAYPOINT_PHASE3_RIGHT,
    PHASE3_LEFT_JOINTS,
    PHASE3_RIGHT_JOINTS,
    # Phase 4
    WAYPOINT_PHASE4_LEFT,
    WAYPOINT_PHASE4_RIGHT,
    PHASE4_LEFT_JOINTS,
    PHASE4_RIGHT_JOINTS,
    # Phase 4.5
    WAYPOINT_PHASE45_LEFT,
    WAYPOINT_PHASE45_RIGHT,
    PHASE45_LEFT_JOINTS,
    PHASE45_RIGHT_JOINTS,
    # Phase 5
    WAYPOINT_PHASE5_LEFT,
    WAYPOINT_PHASE5_RIGHT,
    PHASE5_LEFT_JOINTS,
    PHASE5_RIGHT_JOINTS,
)


def compute_world_ee_position(joint_angles, base_pos, base_quat_wxyz):
    """
    Compute EE position in world frame.

    Args:
        joint_angles: 7 joint angles in radians
        base_pos: (x, y, z) base position
        base_quat_wxyz: (w, x, y, z) base orientation quaternion

    Returns:
        World frame EE position
    """
    # Get EE transformation in base frame
    T_base_ee = forward_kinematics(np.array(joint_angles))
    ee_in_base = T_base_ee[:3, 3]

    # Transform to world frame
    # Quaternion wxyz -> xyzw for scipy
    quat_xyzw = [base_quat_wxyz[1], base_quat_wxyz[2], base_quat_wxyz[3], base_quat_wxyz[0]]
    rot = Rotation.from_quat(quat_xyzw)

    # Rotate and translate
    ee_world = rot.apply(ee_in_base) + np.array(base_pos)

    return ee_world


def verify_phase(phase_name, left_joints, right_joints,
                 left_waypoint, right_waypoint):
    """Verify a single phase using IK module's FK."""
    print(f"\n{'=' * 60}")
    print(f"{phase_name}")
    print(f"{'=' * 60}")

    # Expected EE positions
    expected_left = np.array(left_waypoint)
    expected_right = np.array(right_waypoint)

    print(f"Expected Left EE:  ({expected_left[0]:.4f}, {expected_left[1]:.4f}, {expected_left[2]:.4f})")
    print(f"Expected Right EE: ({expected_right[0]:.4f}, {expected_right[1]:.4f}, {expected_right[2]:.4f})")

    # Compute FK using IK module
    actual_left = compute_world_ee_position(list(left_joints), ROBOT_LEFT_BASE, ROBOT_BASE_QUAT_WXYZ)
    actual_right = compute_world_ee_position(list(right_joints), ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ)

    print(f"Actual Left EE:    ({actual_left[0]:.4f}, {actual_left[1]:.4f}, {actual_left[2]:.4f})")
    print(f"Actual Right EE:   ({actual_right[0]:.4f}, {actual_right[1]:.4f}, {actual_right[2]:.4f})")

    # Calculate errors
    error_left = np.linalg.norm(actual_left - expected_left)
    error_right = np.linalg.norm(actual_right - expected_right)

    print(f"\nError: Left = {error_left * 100:.2f} cm, Right = {error_right * 100:.2f} cm")

    # Component-wise errors
    diff_left = actual_left - expected_left
    diff_right = actual_right - expected_right
    print(f"Left diff:  dX={diff_left[0]*100:.2f}cm, dY={diff_left[1]*100:.2f}cm, dZ={diff_left[2]*100:.2f}cm")
    print(f"Right diff: dX={diff_right[0]*100:.2f}cm, dY={diff_right[1]*100:.2f}cm, dZ={diff_right[2]*100:.2f}cm")

    status = "OK" if error_left < 0.02 and error_right < 0.02 else "FAILED"
    print(f"Status: {status}")

    return {
        "phase": phase_name,
        "expected_left": expected_left,
        "expected_right": expected_right,
        "actual_left": actual_left,
        "actual_right": actual_right,
        "error_left_cm": error_left * 100,
        "error_right_cm": error_right * 100,
        "status": status,
    }


def main():
    """Main function for FK verification."""
    print("=" * 70)
    print("FK Verification using IK Module - All Phases")
    print("=" * 70)
    print(f"\nROBOT_LEFT_BASE:  {ROBOT_LEFT_BASE}")
    print(f"ROBOT_RIGHT_BASE: {ROBOT_RIGHT_BASE}")
    print(f"ROBOT_BASE_QUAT_WXYZ: {ROBOT_BASE_QUAT_WXYZ}")

    # Define phases to verify
    phases = [
        ("Phase 1", LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
         WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT),
        ("Phase 2", PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
         WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT),
        ("Phase 3", PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
         WAYPOINT_PHASE3_LEFT, WAYPOINT_PHASE3_RIGHT),
        ("Phase 4", PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS,
         WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT),
        ("Phase 4.5", PHASE45_LEFT_JOINTS, PHASE45_RIGHT_JOINTS,
         WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT),
        ("Phase 5", PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
         WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT),
    ]

    results = []

    for phase_name, left_joints, right_joints, left_wp, right_wp in phases:
        result = verify_phase(phase_name, left_joints, right_joints, left_wp, right_wp)
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_ok = True
    print(f"\n{'Phase':<12} {'Left Error':>12} {'Right Error':>12} {'Status':>10}")
    print("-" * 50)

    for r in results:
        status_icon = "OK" if r["status"] == "OK" else "NG"
        print(f"{r['phase']:<12} {r['error_left_cm']:>10.2f} cm {r['error_right_cm']:>10.2f} cm {status_icon:>10}")
        if r["status"] != "OK":
            all_ok = False

    print("-" * 50)
    if all_ok:
        print("\n[SUCCESS] All phases verified - EE errors < 2cm")
    else:
        print("\n[FAILED] Some phases have EE errors >= 2cm")

    return all_ok, results


if __name__ == "__main__":
    success, results = main()
    sys.exit(0 if success else 1)
