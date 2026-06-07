#!/usr/bin/env python3
"""
Search for better Phase 5 Right position with improved margin.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import franka_IK_EE_with_base

# Robot base positions
LEFT_BASE = np.array([0.3360, -0.4200, 1.2800])
RIGHT_BASE = np.array([0.3360, 0.2960, 1.2800])

# Robot base X position - EE must be forward of this
BASE_X = 0.336

# Quaternions
WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

# Joint limits
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Note: Phase 4.5 joints will be calculated after Phase 4 and 5 are determined
# Transition check will be done in final_phase4_5_chain.py

def compute_joint_margin(joints):
    margin_lower = joints - JOINT_LIMITS_LOWER
    margin_upper = JOINT_LIMITS_UPPER - joints
    margin_rad = np.minimum(margin_lower, margin_upper).min()
    return np.degrees(margin_rad)

def check_joint_limits(joints):
    return np.all(joints >= JOINT_LIMITS_LOWER) and np.all(joints <= JOINT_LIMITS_UPPER)

def solve_ik_elbow_down(target_ee, base_pos):
    best_joints = None
    best_margin = -float('inf')

    for q7 in np.linspace(-2.8, 2.8, 80):
        solutions = franka_IK_EE_with_base(
            target_ee, GRIPPER_DOWN_QUAT, base_pos, WALL_MOUNT_QUAT, q7
        )
        if solutions is None:
            continue
        for sol in solutions:
            if sol is None or sol.joints is None:
                continue
            joints = sol.joints
            if joints[4] >= 0:  # Elbow down only
                continue
            if not check_joint_limits(joints):
                continue
            margin = compute_joint_margin(joints)
            if margin > best_margin:
                best_margin = margin
                best_joints = joints.copy()

    return best_joints, best_margin

def main():
    print("=" * 70)
    print("Search Better Phase 5 Right Position")
    print("=" * 70)
    print(f"Robot base X: {BASE_X}")
    print(f"Constraint: EE X > {BASE_X} (forward of base)")
    print()

    # Search grid - EE must be forward of robot base
    results = []

    # EE must be forward of robot base (X > 0.336)
    # For RIGHT arm: Y should be >= 0 (right side for cable placement)
    x_range = np.arange(BASE_X + 0.02, 0.50, 0.02)  # 0.356 ~ 0.48
    y_range = np.arange(0.00, 0.20, 0.02)  # Right side only (Y >= 0)
    z_range = np.arange(0.75, 0.95, 0.02)  # Near hook height

    print(f"X range: {x_range[0]:.3f} ~ {x_range[-1]:.3f}")
    print(f"Y range: {y_range[0]:.3f} ~ {y_range[-1]:.3f}")
    print(f"Z range: {z_range[0]:.3f} ~ {z_range[-1]:.3f}")
    print("Searching...")

    for x in x_range:
        for y in y_range:
            for z in z_range:
                target = np.array([x, y, z])
                joints, margin = solve_ik_elbow_down(target, RIGHT_BASE)

                if joints is not None and margin > 10.0:  # Minimum 10° margin
                    results.append({
                        'target': target,
                        'joints': joints,
                        'margin': margin,
                        'j5': np.degrees(joints[4])
                    })

    print(f"Found {len(results)} valid configurations")
    print()

    if not results:
        print("❌ No valid configuration found with margin > 10° and J5 < 0")
        return

    # Sort by margin (prefer higher margin)
    results.sort(key=lambda r: r['margin'], reverse=True)

    print("=" * 70)
    print("Top 5 configurations (sorted by margin):")
    print("=" * 70)
    print()

    for i, r in enumerate(results[:5]):
        print(f"Option {i+1}:")
        print(f"  EE: ({r['target'][0]:.2f}, {r['target'][1]:.2f}, {r['target'][2]:.2f})")
        print(f"  Margin: {r['margin']:.1f}°")
        print(f"  J5: {r['j5']:.1f}° (elbow down ✓)")
        print()

    # Best result
    best = results[0]
    print("=" * 70)
    print("Best Configuration:")
    print("=" * 70)
    print(f"  EE: ({best['target'][0]:.2f}, {best['target'][1]:.2f}, {best['target'][2]:.2f})")
    print(f"  Margin: {best['margin']:.1f}°")
    print()

    # Also find matching Left position
    left_target = np.array([best['target'][0], -best['target'][1] - 0.09, best['target'][2]])
    # Adjust Y for symmetric but reasonable position
    left_joints, left_margin = solve_ik_elbow_down(left_target, LEFT_BASE)

    if left_joints is not None:
        print(f"Left arm at ({left_target[0]:.2f}, {left_target[1]:.2f}, {left_target[2]:.2f}):")
        print(f"  Margin: {left_margin:.1f}°")
    else:
        # Try original left position
        left_target = CURRENT_PHASE5_RIGHT.copy()
        left_target[1] = -0.25  # Keep original Y
        left_joints, left_margin = solve_ik_elbow_down(left_target, LEFT_BASE)
        print(f"Left arm (original Y): margin={left_margin:.1f}°")

    # Output
    print()
    print("=" * 70)
    print("Copy-paste for task_config.py:")
    print("=" * 70)
    print()
    print("# Phase 5: Place (improved margin)")
    print(f"WAYPOINT_PHASE5_RIGHT = ({best['target'][0]:.2f}, {best['target'][1]:.2f}, {best['target'][2]:.2f})")
    print()
    print("PHASE5_RIGHT_JOINTS = [")
    for i, j in enumerate(best['joints']):
        deg = np.degrees(j)
        sign = "+" if j >= 0 else ""
        print(f"    {sign}{j:.6f},  # panda_joint{i+1}: {sign}{deg:.1f} deg")
    print("]")

if __name__ == "__main__":
    main()
