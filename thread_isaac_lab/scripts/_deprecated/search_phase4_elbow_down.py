#!/usr/bin/env python3
"""
Search for valid Phase 4 EE position that allows elbow-down configuration (J5 < 0).
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import solve_ik_best

# Robot base positions
LEFT_BASE = np.array([0.3360, -0.4200, 1.2800])
RIGHT_BASE = np.array([0.3360, 0.2960, 1.2800])

# Quaternions
WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

# Joint limits
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Phase 3 Right joints for continuity comparison
PHASE3_RIGHT_JOINTS = np.array([
    +0.865437,  # panda_joint1
    +1.387131,  # panda_joint2
    -0.483665,  # panda_joint3
    -2.463108,  # panda_joint4
    -2.333584,  # panda_joint5
    +1.527820,  # panda_joint6
    -1.666667,  # panda_joint7
])

# Robot base X position - EE must be forward of this
BASE_X = 0.336

# Hook position (target area for Phase 4)
HOOK_POS = np.array([0.25, 0.0, 0.90])  # Reference hook position

def compute_joint_margin(joints):
    """Compute minimum distance to joint limits in degrees."""
    margin_lower = joints - JOINT_LIMITS_LOWER
    margin_upper = JOINT_LIMITS_UPPER - joints
    margin_rad = np.minimum(margin_lower, margin_upper).min()
    return np.degrees(margin_rad)

def format_joints(joints):
    """Format joints as compact string."""
    return "[" + ", ".join(f"{j:+.3f}" for j in joints) + "]"

def main():
    print("=" * 70)
    print("Search Phase 4 Position with Elbow-Down Constraint")
    print("=" * 70)
    print(f"\nPhase 3 Right J5: {np.degrees(PHASE3_RIGHT_JOINTS[4]):.1f}° (elbow down)")
    print(f"Constraint: Phase 4 Right J5 < 0")
    print()

    # Search grid for Phase 4 Right EE position
    # Keep Y near hook (0.0 to 0.15), Z around hook height (0.85-0.95)
    results = []

    print(f"Robot base X: {BASE_X}")
    print(f"Searching for EE positions with X > {BASE_X} (forward of base)...")
    print()

    # EE must be forward of robot base (X > 0.336)
    x_range = np.arange(BASE_X + 0.02, 0.55, 0.02)  # 0.356 ~ 0.54
    y_range = np.arange(-0.10, 0.25, 0.02)  # Wider Y range
    z_range = np.arange(0.75, 1.00, 0.02)   # Lower Z included

    total = len(x_range) * len(y_range) * len(z_range)
    count = 0

    for x in x_range:
        for y in y_range:
            for z in z_range:
                count += 1
                target = np.array([x, y, z])

                success, joints, margin = solve_ik_best(
                    target, RIGHT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
                    q7_range=(-2.8, 2.8), q7_steps=30
                )

                if success and joints[4] < 0:  # Elbow down
                    actual_margin = compute_joint_margin(joints)

                    # Compute transition from Phase 3
                    delta = np.degrees(joints - PHASE3_RIGHT_JOINTS)
                    max_change = np.max(np.abs(delta))

                    results.append({
                        'target': target,
                        'joints': joints,
                        'margin': actual_margin,
                        'j5': np.degrees(joints[4]),
                        'max_change': max_change,
                        'delta': delta
                    })

    print(f"Found {len(results)} valid configurations with J5 < 0")
    print()

    if not results:
        print("❌ No valid configuration found with J5 < 0")
        return

    # Sort by max_change (prefer smooth transition)
    results.sort(key=lambda r: r['max_change'])

    print("=" * 70)
    print("Top 5 configurations (sorted by transition smoothness):")
    print("=" * 70)
    print()

    for i, r in enumerate(results[:5]):
        print(f"Option {i+1}:")
        print(f"  EE Target: ({r['target'][0]:.2f}, {r['target'][1]:.2f}, {r['target'][2]:.2f})")
        print(f"  J5: {r['j5']:.1f}° (elbow down ✓)")
        print(f"  Margin: {r['margin']:.1f}°")
        print(f"  Max change from P3: {r['max_change']:.1f}°", end="")
        if r['max_change'] <= 30:
            print(" ✅ OK")
        else:
            print(" ⚠️ >30°")

        # Show per-joint changes
        print("  Joint changes: ", end="")
        for j, d in enumerate(r['delta']):
            flag = "⚠" if abs(d) > 30 else ""
            print(f"J{j+1}:{d:+.0f}{flag} ", end="")
        print()
        print()

    # Best option
    best = results[0]
    print("=" * 70)
    print("Best Configuration (smoothest transition):")
    print("=" * 70)
    print(f"  EE: ({best['target'][0]:.2f}, {best['target'][1]:.2f}, {best['target'][2]:.2f})")
    print(f"  Margin: {best['margin']:.1f}°")
    print(f"  Max change: {best['max_change']:.1f}°")
    print()

    # Also check Left arm
    print("=" * 70)
    print("Left Arm IK for symmetric position")
    print("=" * 70)

    left_target = np.array([best['target'][0], -best['target'][1], best['target'][2]])
    print(f"  Target: ({left_target[0]:.2f}, {left_target[1]:.2f}, {left_target[2]:.2f})")

    left_success, left_joints, _ = solve_ik_best(
        left_target, LEFT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=30
    )

    if left_success:
        left_margin = compute_joint_margin(left_joints)
        print(f"  Status: SUCCESS")
        print(f"  Margin: {left_margin:.1f}°")
        print(f"  J5: {np.degrees(left_joints[4]):.1f}°")
    else:
        print(f"  Status: FAILED")
        left_joints = None

    # Output config
    if left_joints is not None:
        print("\n" + "=" * 70)
        print("Copy-paste for task_config.py:")
        print("=" * 70)
        print()
        print(f"# Phase 4: Hook approach (elbow-down constrained)")
        print(f"WAYPOINT_PHASE4_LEFT = ({left_target[0]:.2f}, {left_target[1]:.2f}, {left_target[2]:.2f})")
        print(f"WAYPOINT_PHASE4_RIGHT = ({best['target'][0]:.2f}, {best['target'][1]:.2f}, {best['target'][2]:.2f})")
        print()
        print("PHASE4_LEFT_JOINTS = [")
        for i, j in enumerate(left_joints):
            deg = np.degrees(j)
            sign = "+" if j >= 0 else ""
            print(f"    {sign}{j:.6f},  # panda_joint{i+1}: {sign}{deg:.1f} deg")
        print("]")
        print()
        print("PHASE4_RIGHT_JOINTS = [")
        for i, j in enumerate(best['joints']):
            deg = np.degrees(j)
            sign = "+" if j >= 0 else ""
            print(f"    {sign}{j:.6f},  # panda_joint{i+1}: {sign}{deg:.1f} deg")
        print("]")

if __name__ == "__main__":
    main()
