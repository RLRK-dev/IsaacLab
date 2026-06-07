#!/usr/bin/env python3
"""
IK-FK Round-trip Verification

Test that IK solutions can be verified by FK:
1. Given target position T, compute IK -> joints J
2. Compute FK(J) -> actual position A
3. Verify that A ≈ T

This confirms that IK and FK implementations are consistent.

T1タスク: 2026-01-02
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
sys.path.insert(0, "/home/rlrk/IsaacLab")

import numpy as np
from scipy.spatial.transform import Rotation as R

# Import from IK module
from thread_isaac_lab.scripts.franka_analytical_ik import (
    forward_kinematics,
    franka_IK_EE_with_base,
    solve_ik_best,
)

# Project imports
from thread_isaac_lab.configs.task_config import (
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    ROBOT_BASE_QUAT_WXYZ,
    GRIPPER_DOWN_QUAT_WXYZ,
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


def fk_to_world(joints, base_pos, base_quat_wxyz):
    """Compute EE position in world frame from joints."""
    # Get FK in base frame
    T_base_ee = forward_kinematics(np.array(joints))

    # Build base transformation
    quat_xyzw = [base_quat_wxyz[1], base_quat_wxyz[2], base_quat_wxyz[3], base_quat_wxyz[0]]
    R_base = R.from_quat(quat_xyzw).as_matrix()

    T_base = np.eye(4)
    T_base[:3, :3] = R_base
    T_base[:3, 3] = base_pos

    # Transform to world
    T_world_ee = T_base @ T_base_ee

    return T_world_ee[:3, 3]


def roundtrip_test(target_pos, base_pos, base_quat_wxyz, target_quat_wxyz, name):
    """Perform IK -> FK round-trip test."""
    print(f"\n{'=' * 50}")
    print(f"{name}")
    print(f"{'=' * 50}")
    print(f"Target position: {target_pos}")

    # Step 1: Compute IK
    success, joints, margin = solve_ik_best(
        np.array(target_pos),
        np.array(base_pos),
        np.array(base_quat_wxyz),
        np.array(target_quat_wxyz),
        q7_range=(-2.5, 2.5),
        q7_steps=100
    )

    if not success:
        print(f"[FAILED] IK failed to find solution")
        return None, None, "IK_FAILED"

    print(f"IK solution: {np.degrees(joints).round(1)} deg")
    print(f"IK margin: {margin:.1f} deg")

    # Step 2: Compute FK from joints
    fk_pos = fk_to_world(joints, base_pos, base_quat_wxyz)
    print(f"FK result:  {fk_pos.round(4)}")

    # Step 3: Compare
    error = np.linalg.norm(fk_pos - np.array(target_pos))
    print(f"Round-trip error: {error*100:.2f} cm")

    diff = fk_pos - np.array(target_pos)
    print(f"  dX={diff[0]*100:.2f}cm, dY={diff[1]*100:.2f}cm, dZ={diff[2]*100:.2f}cm")

    status = "OK" if error < 0.02 else "FAILED"
    print(f"Status: {status}")

    return joints, error * 100, status


def verify_stored_joints(phase_name, stored_joints, target_pos, base_pos, base_quat_wxyz):
    """Verify that stored joints produce the expected position."""
    print(f"\n--- Stored Joints Verification for {phase_name} ---")
    print(f"Stored joints: {np.degrees(stored_joints).round(1)} deg")

    fk_pos = fk_to_world(stored_joints, base_pos, base_quat_wxyz)
    print(f"FK result:     {fk_pos.round(4)}")
    print(f"Expected:      {np.array(target_pos).round(4)}")

    error = np.linalg.norm(fk_pos - np.array(target_pos))
    print(f"Error: {error*100:.2f} cm")

    diff = fk_pos - np.array(target_pos)
    print(f"  dX={diff[0]*100:.2f}cm, dY={diff[1]*100:.2f}cm, dZ={diff[2]*100:.2f}cm")

    return error * 100


def main():
    """Main function."""
    print("=" * 70)
    print("IK-FK Round-trip Verification")
    print("=" * 70)
    print(f"\nROBOT_LEFT_BASE:  {ROBOT_LEFT_BASE}")
    print(f"ROBOT_RIGHT_BASE: {ROBOT_RIGHT_BASE}")
    print(f"GRIPPER_DOWN_QUAT: {GRIPPER_DOWN_QUAT_WXYZ}")

    # First, test IK -> FK round-trip for each waypoint
    print("\n" + "=" * 70)
    print("PART 1: IK -> FK Round-trip Tests")
    print("=" * 70)

    tests = [
        ("Phase 1 Left", WAYPOINT_PHASE1_LEFT, ROBOT_LEFT_BASE),
        ("Phase 1 Right", WAYPOINT_PHASE1_RIGHT, ROBOT_RIGHT_BASE),
        ("Phase 2 Left", WAYPOINT_PHASE2_LEFT, ROBOT_LEFT_BASE),
        ("Phase 2 Right", WAYPOINT_PHASE2_RIGHT, ROBOT_RIGHT_BASE),
        ("Phase 3 Left", WAYPOINT_PHASE3_LEFT, ROBOT_LEFT_BASE),
        ("Phase 3 Right", WAYPOINT_PHASE3_RIGHT, ROBOT_RIGHT_BASE),
    ]

    results = []
    for name, target, base in tests:
        joints, error, status = roundtrip_test(
            target, base, ROBOT_BASE_QUAT_WXYZ, GRIPPER_DOWN_QUAT_WXYZ, name
        )
        results.append((name, error, status))

    # Second, verify stored joints
    print("\n" + "=" * 70)
    print("PART 2: Stored Joints -> FK Verification")
    print("=" * 70)

    stored_tests = [
        ("Phase 1 Left", LEFT_ARM_INIT_JOINTS, WAYPOINT_PHASE1_LEFT, ROBOT_LEFT_BASE),
        ("Phase 1 Right", RIGHT_ARM_INIT_JOINTS, WAYPOINT_PHASE1_RIGHT, ROBOT_RIGHT_BASE),
        ("Phase 2 Left", PHASE2_LEFT_JOINTS, WAYPOINT_PHASE2_LEFT, ROBOT_LEFT_BASE),
        ("Phase 2 Right", PHASE2_RIGHT_JOINTS, WAYPOINT_PHASE2_RIGHT, ROBOT_RIGHT_BASE),
        ("Phase 3 Left", PHASE3_LEFT_JOINTS, WAYPOINT_PHASE3_LEFT, ROBOT_LEFT_BASE),
        ("Phase 3 Right", PHASE3_RIGHT_JOINTS, WAYPOINT_PHASE3_RIGHT, ROBOT_RIGHT_BASE),
    ]

    stored_results = []
    for name, joints, target, base in stored_tests:
        error = verify_stored_joints(name, joints, target, base, ROBOT_BASE_QUAT_WXYZ)
        stored_results.append((name, error))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Round-trip Tests")
    print("=" * 70)
    print(f"\n{'Test':<20} {'Error (cm)':>12} {'Status':>10}")
    print("-" * 45)
    for name, error, status in results:
        print(f"{name:<20} {error:>10.2f} cm {status:>10}")

    print("\n" + "=" * 70)
    print("SUMMARY: Stored Joints Verification")
    print("=" * 70)
    print(f"\n{'Test':<20} {'Error (cm)':>12}")
    print("-" * 35)
    for name, error in stored_results:
        status = "OK" if error < 2.0 else "NG"
        print(f"{name:<20} {error:>10.2f} cm {status:>5}")


if __name__ == "__main__":
    main()
