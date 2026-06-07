#!/usr/bin/env python3
"""
Analytical FK Verification Script

Verify all Phase joint angles using pure Python FK calculation.
No Isaac Sim dependency - validates IK solutions analytically.

T1タスク: 2026-01-02
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
sys.path.insert(0, "/home/rlrk/IsaacLab")

import numpy as np
from scipy.spatial.transform import Rotation

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


# Panda DH parameters (modified DH convention)
# d: link offset along z
# a: link length along x
# alpha: twist angle around x
DH_PARAMS = [
    # (d, a, alpha)
    (0.333, 0.0, 0.0),        # Joint 1
    (0.0, 0.0, -np.pi/2),     # Joint 2
    (0.316, 0.0, np.pi/2),    # Joint 3
    (0.0, 0.0825, np.pi/2),   # Joint 4
    (0.384, -0.0825, -np.pi/2), # Joint 5
    (0.0, 0.0, np.pi/2),      # Joint 6
    (0.107, 0.088, np.pi/2),  # Joint 7
]

# Flange to EE (panda_hand) offset
FLANGE_TO_EE = 0.1034  # meters (from panda URDF)


def dh_transform(theta, d, a, alpha):
    """Compute DH transformation matrix."""
    ct = np.cos(theta)
    st = np.sin(theta)
    ca = np.cos(alpha)
    sa = np.sin(alpha)

    return np.array([
        [ct, -st*ca, st*sa, a*ct],
        [st, ct*ca, -ct*sa, a*st],
        [0.0, sa, ca, d],
        [0.0, 0.0, 0.0, 1.0]
    ])


def forward_kinematics(joint_angles, base_pos, base_quat_wxyz):
    """
    Compute FK for Franka Panda.

    Args:
        joint_angles: 7-element list of joint angles in radians
        base_pos: (x, y, z) base position in world frame
        base_quat_wxyz: (w, x, y, z) quaternion for base orientation

    Returns:
        ee_pos: (x, y, z) end-effector position in world frame
    """
    # Start with identity
    T = np.eye(4)

    # Apply DH transformations for each joint
    for i, (d, a, alpha) in enumerate(DH_PARAMS):
        T = T @ dh_transform(joint_angles[i], d, a, alpha)

    # Add flange to EE offset (along z-axis of the flange)
    T_ee = np.eye(4)
    T_ee[2, 3] = FLANGE_TO_EE
    T = T @ T_ee

    # Get EE position in base frame
    ee_in_base = T[:3, 3]

    # Transform to world frame
    # Convert quaternion wxyz to scipy format xyzw
    quat_xyzw = [base_quat_wxyz[1], base_quat_wxyz[2], base_quat_wxyz[3], base_quat_wxyz[0]]
    rot = Rotation.from_quat(quat_xyzw)

    # Rotate EE position and add base offset
    ee_world = rot.apply(ee_in_base) + np.array(base_pos)

    return ee_world


def verify_phase(phase_name, left_joints, right_joints,
                 left_waypoint, right_waypoint):
    """Verify a single phase using analytical FK."""
    print(f"\n{'=' * 60}")
    print(f"{phase_name}")
    print(f"{'=' * 60}")

    # Expected EE positions
    expected_left = np.array(left_waypoint)
    expected_right = np.array(right_waypoint)

    print(f"Expected Left EE:  ({expected_left[0]:.4f}, {expected_left[1]:.4f}, {expected_left[2]:.4f})")
    print(f"Expected Right EE: ({expected_right[0]:.4f}, {expected_right[1]:.4f}, {expected_right[2]:.4f})")

    # Compute FK
    actual_left = forward_kinematics(list(left_joints), ROBOT_LEFT_BASE, ROBOT_BASE_QUAT_WXYZ)
    actual_right = forward_kinematics(list(right_joints), ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ)

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
    """Main function for analytical FK verification."""
    print("=" * 70)
    print("Analytical FK Verification - All Phases")
    print("=" * 70)
    print(f"\nROBOT_LEFT_BASE:  {ROBOT_LEFT_BASE}")
    print(f"ROBOT_RIGHT_BASE: {ROBOT_RIGHT_BASE}")
    print(f"ROBOT_BASE_QUAT_WXYZ: {ROBOT_BASE_QUAT_WXYZ}")
    print(f"Flange-to-EE offset: {FLANGE_TO_EE:.4f} m")

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
