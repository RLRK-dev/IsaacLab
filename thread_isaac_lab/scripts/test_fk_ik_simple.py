#!/usr/bin/env python3
"""
Simple FK-IK consistency test with base at origin.

Tests:
1. Known joint angles -> FK -> position
2. Position -> IK -> joints -> FK -> verify position matches

T1タスク: 2026-01-02
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
sys.path.insert(0, "/home/rlrk/IsaacLab")

import numpy as np
from scipy.spatial.transform import Rotation as R

from thread_isaac_lab.scripts.franka_analytical_ik import (
    forward_kinematics,
    franka_IK_EE,
    GRIPPER_DOWN_QUAT_WXYZ,
)


def test_fk_simple():
    """Test FK with a simple joint configuration."""
    print("=" * 60)
    print("Test 1: Simple FK test (base at origin)")
    print("=" * 60)

    # Home position joints
    joints_home = np.array([0, 0, 0, -np.pi/2, 0, np.pi/2, 0])
    print(f"Input joints (rad): {joints_home}")
    print(f"Input joints (deg): {np.degrees(joints_home)}")

    T = forward_kinematics(joints_home)
    pos = T[:3, 3]
    print(f"FK result (base frame): {pos}")

    # According to Franka specs, the home position should be approximately:
    # x ≈ 0.088 (A7), y ≈ 0, z ≈ D1 + D3 + D5 + D7E = 0.333 + 0.316 + 0.384 + 0.2104 = 1.2434
    print(f"\nExpected approximate (from DH): x≈0.088, y≈0, z≈1.24")
    print(f"Actual: x={pos[0]:.4f}, y={pos[1]:.4f}, z={pos[2]:.4f}")


def test_ik_fk_roundtrip_no_base():
    """Test IK -> FK roundtrip without base transformation."""
    print("\n" + "=" * 60)
    print("Test 2: IK -> FK roundtrip (no base transformation)")
    print("=" * 60)

    # Create target transformation matrix
    # Position: some reachable point
    target_pos = np.array([0.4, 0.0, 0.5])

    # Orientation: gripper pointing down
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)  # (w, x, y, z)
    quat_xyzw = [target_quat[1], target_quat[2], target_quat[3], target_quat[0]]
    R_target = R.from_quat(quat_xyzw).as_matrix()

    O_T_EE = np.eye(4)
    O_T_EE[:3, :3] = R_target
    O_T_EE[:3, 3] = target_pos

    print(f"Target position (base frame): {target_pos}")
    print(f"Target quaternion (wxyz): {target_quat}")

    # Solve IK
    q7 = 0.0
    solutions = franka_IK_EE(O_T_EE, q7)

    print(f"\nIK solutions found: {len(solutions)}")

    if len(solutions) == 0:
        print("[FAILED] No IK solution found")
        return

    # Take best solution (highest margin)
    best = max(solutions, key=lambda s: s.margin_deg)
    joints = best.joints
    print(f"Best solution: {np.degrees(joints).round(1)} deg")
    print(f"Margin: {best.margin_deg:.1f} deg")

    # Verify with FK
    T_fk = forward_kinematics(joints)
    fk_pos = T_fk[:3, 3]

    print(f"\nFK verification (base frame): {fk_pos}")
    error = np.linalg.norm(fk_pos - target_pos)
    print(f"Error: {error * 100:.2f} cm")

    if error < 0.01:
        print("[OK] FK matches target within 1cm")
    else:
        print(f"[FAILED] FK error = {error*100:.2f} cm")


def test_ik_fk_with_base():
    """Test IK -> FK with base transformation."""
    print("\n" + "=" * 60)
    print("Test 3: IK -> FK with base transformation")
    print("=" * 60)

    from thread_isaac_lab.scripts.franka_analytical_ik import franka_IK_EE_with_base
    from thread_isaac_lab.configs.task_config import (
        ROBOT_LEFT_BASE,
        ROBOT_BASE_QUAT_WXYZ,
    )

    base_pos = np.array(ROBOT_LEFT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)

    # Target position in world frame
    target_world = np.array([0.29, -0.285, 0.895])
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    print(f"Base position: {base_pos}")
    print(f"Base quaternion (wxyz): {base_quat}")
    print(f"Target position (world): {target_world}")

    # Solve IK
    q7 = 0.0
    solutions = franka_IK_EE_with_base(target_world, target_quat, base_pos, base_quat, q7)

    print(f"\nIK solutions found: {len(solutions)}")

    if len(solutions) == 0:
        print("[FAILED] No IK solution found")
        return

    # Take best solution
    best = max(solutions, key=lambda s: s.margin_deg)
    joints = best.joints
    print(f"Best solution: {np.degrees(joints).round(1)} deg")
    print(f"Margin: {best.margin_deg:.1f} deg")

    # Verify with FK (in base frame)
    T_fk = forward_kinematics(joints)
    fk_pos_base = T_fk[:3, 3]
    print(f"\nFK result (base frame): {fk_pos_base}")

    # Transform to world frame
    quat_xyzw = [base_quat[1], base_quat[2], base_quat[3], base_quat[0]]
    R_base = R.from_quat(quat_xyzw).as_matrix()

    T_base = np.eye(4)
    T_base[:3, :3] = R_base
    T_base[:3, 3] = base_pos

    T_world_ee = T_base @ T_fk
    fk_pos_world = T_world_ee[:3, 3]

    print(f"FK result (world frame): {fk_pos_world}")
    print(f"Target (world frame):    {target_world}")

    error = np.linalg.norm(fk_pos_world - target_world)
    print(f"\nError: {error * 100:.2f} cm")

    if error < 0.02:
        print("[OK] FK matches target within 2cm")
    else:
        print(f"[FAILED] FK error = {error*100:.2f} cm")

    # Also show the transformation detail
    print("\n--- Transformation detail ---")
    print(f"T_base:\n{T_base}")
    print(f"T_fk (base to EE):\n{T_fk}")
    print(f"T_world_ee:\n{T_world_ee}")


def main():
    test_fk_simple()
    test_ik_fk_roundtrip_no_base()
    test_ik_fk_with_base()


if __name__ == "__main__":
    main()
