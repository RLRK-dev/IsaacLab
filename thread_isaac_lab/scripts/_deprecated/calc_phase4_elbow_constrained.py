#!/usr/bin/env python3
"""
Calculate Phase 4 joint angles with elbow continuity constraint.
Specifically, Right arm J5 must be < 0 to match Phase 3 elbow configuration.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import franka_IK_EE_with_base, forward_kinematics

# Robot base positions
LEFT_BASE = np.array([0.3360, -0.4200, 1.2800])
RIGHT_BASE = np.array([0.3360, 0.2960, 1.2800])

# Wall mount quaternion (w, x, y, z)
WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

# Joint limits
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Phase 3 joints (reference for continuity)
PHASE3_LEFT_J5 = -2.096
PHASE3_RIGHT_J5 = -2.334

# Phase 4 EE targets
PHASE4_LEFT = np.array([0.25, -0.15, 1.00])
PHASE4_RIGHT = np.array([0.25, +0.15, 1.00])

def compute_joint_margin(joints):
    """Compute minimum distance to joint limits in degrees."""
    margin_lower = joints - JOINT_LIMITS_LOWER
    margin_upper = JOINT_LIMITS_UPPER - joints
    margin_rad = np.minimum(margin_lower, margin_upper).min()
    return np.degrees(margin_rad)

def check_joint_limits(joints):
    """Check if joints are within limits."""
    return np.all(joints >= JOINT_LIMITS_LOWER) and np.all(joints <= JOINT_LIMITS_UPPER)

def solve_ik_with_elbow_constraint(target_ee, base_pos, base_quat, target_quat, j5_sign=-1):
    """
    Solve IK with elbow constraint (J5 sign).
    j5_sign: -1 for elbow down (J5 < 0), +1 for elbow up (J5 > 0)
    """
    best_joints = None
    best_margin = -float('inf')

    # Search over q7 range
    q7_values = np.linspace(-2.8, 2.8, 100)

    for q7 in q7_values:
        solutions = franka_IK_EE_with_base(target_ee, target_quat, base_pos, base_quat, q7)

        if solutions is None:
            continue

        for sol in solutions:
            if sol is None or sol.joints is None:
                continue

            joints = sol.joints

            # Check elbow constraint (J5 sign)
            if j5_sign < 0 and joints[4] >= 0:
                continue
            if j5_sign > 0 and joints[4] <= 0:
                continue

            # Check joint limits
            if not check_joint_limits(joints):
                continue

            # Compute margin
            margin = compute_joint_margin(joints)
            if margin > best_margin:
                best_margin = margin
                best_joints = joints.copy()

    return best_joints, best_margin

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
    print("Phase 4 IK with Elbow Continuity Constraint")
    print("=" * 60)
    print(f"\nConstraint: Right arm J5 < 0 (match Phase 3 elbow)")
    print(f"Phase 3 Right J5: {np.degrees(PHASE3_RIGHT_J5):.1f}°")

    # Phase 4 Left arm (normal solve, J5 < 0 already)
    print("\n" + "=" * 60)
    print("Left Arm (standard solve)")
    print("=" * 60)
    print(f"  Target EE: {PHASE4_LEFT}")

    left_joints, left_margin = solve_ik_with_elbow_constraint(
        PHASE4_LEFT, LEFT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT, j5_sign=-1
    )

    if left_joints is not None:
        print(f"  Status: SUCCESS")
        print(f"  Margin: {left_margin:.1f}°")
        print(f"  J5: {np.degrees(left_joints[4]):.1f}° (elbow down ✓)")
    else:
        print(f"  Status: FAILED")

    # Phase 4 Right arm (constrained solve, J5 < 0)
    print("\n" + "=" * 60)
    print("Right Arm (elbow-constrained solve)")
    print("=" * 60)
    print(f"  Target EE: {PHASE4_RIGHT}")
    print(f"  Constraint: J5 < 0")

    right_joints, right_margin = solve_ik_with_elbow_constraint(
        PHASE4_RIGHT, RIGHT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT, j5_sign=-1
    )

    if right_joints is not None:
        print(f"  Status: SUCCESS")
        print(f"  Margin: {right_margin:.1f}°")
        print(f"  J5: {np.degrees(right_joints[4]):.1f}° (elbow down ✓)")

        # Verify FK
        T = forward_kinematics(right_joints)
        # Transform to world frame
        w, x, y, z = WALL_MOUNT_QUAT
        R_base = np.array([
            [1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
            [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
            [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]
        ])
        ee_world = RIGHT_BASE + R_base @ T[:3, 3]
        ee_error = np.linalg.norm(ee_world - PHASE4_RIGHT)
        print(f"  FK EE: {ee_world}")
        print(f"  EE error: {ee_error*1000:.2f}mm")
    else:
        print(f"  Status: FAILED - no solution with J5 < 0")
        print(f"  Trying alternative EE positions...")

        # Try nearby positions
        for dz in [-0.05, -0.10, -0.15, -0.20]:
            alt_target = PHASE4_RIGHT.copy()
            alt_target[2] += dz
            alt_joints, alt_margin = solve_ik_with_elbow_constraint(
                alt_target, RIGHT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT, j5_sign=-1
            )
            if alt_joints is not None:
                print(f"\n  Found solution at Z={alt_target[2]:.2f}:")
                print(f"    Margin: {alt_margin:.1f}°")
                print(f"    J5: {np.degrees(alt_joints[4]):.1f}°")
                right_joints = alt_joints
                right_margin = alt_margin
                PHASE4_RIGHT[2] = alt_target[2]
                break

    # Comparison with Phase 3
    if right_joints is not None:
        print("\n" + "=" * 60)
        print("Phase 3 → Phase 4 Transition (Right Arm)")
        print("=" * 60)

        # Load Phase 3 joints
        sys.path.insert(0, '/home/rlrk/IsaacLab')
        from thread_isaac_lab.configs.task_config import PHASE3_RIGHT_JOINTS

        phase3 = np.array(PHASE3_RIGHT_JOINTS)
        delta = np.degrees(right_joints - phase3)

        print("  Joint changes:")
        for i, d in enumerate(delta):
            sign = "+" if d >= 0 else ""
            flag = " ⚠️" if abs(d) > 30 else " ✓"
            print(f"    J{i+1}: {sign}{d:.1f}°{flag}")

        max_change = np.max(np.abs(delta))
        print(f"\n  Max change: {max_change:.1f}°", end="")
        if max_change <= 30:
            print(" ✅ OK")
        else:
            print(" ⚠️ EXCEEDS 30°")

    # Output config
    if left_joints is not None and right_joints is not None:
        print("\n" + "=" * 60)
        print("Copy-paste for task_config.py:")
        print("=" * 60)
        print()
        print("# Phase 4: Hook approach (elbow-constrained)")
        print(f"WAYPOINT_PHASE4_LEFT = ({PHASE4_LEFT[0]:.2f}, {PHASE4_LEFT[1]:.2f}, {PHASE4_LEFT[2]:.2f})")
        print(f"WAYPOINT_PHASE4_RIGHT = ({PHASE4_RIGHT[0]:.2f}, {PHASE4_RIGHT[1]:.2f}, {PHASE4_RIGHT[2]:.2f})")
        print()
        print(format_joints_for_config(left_joints, 'PHASE4_LEFT_JOINTS'))
        print()
        print(format_joints_for_config(right_joints, 'PHASE4_RIGHT_JOINTS'))

if __name__ == "__main__":
    main()
