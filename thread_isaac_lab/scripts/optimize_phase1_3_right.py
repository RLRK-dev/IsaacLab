#!/usr/bin/env python3
"""
Phase 1 & 3 Right Arm Optimization Script

Search for waypoint adjustments to improve joint margins.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab')

from thread_isaac_lab.configs.task_config import (
    ROBOT_RIGHT_BASE,
    ROBOT_BASE_QUAT_WXYZ,
    GRIPPER_DOWN_QUAT_WXYZ,
)

from thread_isaac_lab.scripts.franka_analytical_ik import solve_ik_best

def optimize_waypoint(name, original_target, right_base, base_quat, target_quat, min_margin=20.0):
    print(f"\n{'=' * 60}")
    print(f"Optimizing {name}")
    print(f"{'=' * 60}")
    print(f"Original target: {original_target}")

    results = []
    best_margin = 0
    best_target = None
    best_joints = None

    # Search space around original target - small adjustments
    for dx in np.arange(-0.03, 0.04, 0.01):
        for dy in np.arange(-0.03, 0.04, 0.01):
            for dz in np.arange(-0.03, 0.04, 0.01):
                target = original_target + np.array([dx, dy, dz])

                success, joints, margin = solve_ik_best(
                    target, right_base, base_quat, target_quat,
                    q7_range=(-2.5, 2.5), q7_steps=50
                )

                if success:
                    dist = np.linalg.norm(target - original_target)
                    if margin >= min_margin:
                        results.append({
                            'target': target.copy(),
                            'margin': margin,
                            'distance': dist,
                            'joints': joints.copy()
                        })

                    if margin > best_margin:
                        best_margin = margin
                        best_target = target.copy()
                        best_joints = joints.copy()

    if results:
        results.sort(key=lambda x: x['distance'])
        print(f"\nFound {len(results)} configurations with margin >= {min_margin}°")
        print("\nTop 5 closest to original:")
        for i, r in enumerate(results[:5]):
            dx = r['target'][0] - original_target[0]
            dy = r['target'][1] - original_target[1]
            dz = r['target'][2] - original_target[2]
            print(f"  {i+1}. Target: ({r['target'][0]:.3f}, {r['target'][1]:.3f}, {r['target'][2]:.3f})")
            print(f"     Delta: (dx={dx:+.3f}, dy={dy:+.3f}, dz={dz:+.3f})")
            print(f"     Margin: {r['margin']:.1f}°, Distance: {r['distance']*100:.1f}cm")
        return results[0]  # Return closest that meets margin
    else:
        print(f"\nNo configurations found with margin >= {min_margin}°")
        print(f"Best found: margin = {best_margin:.1f}°")
        if best_target is not None:
            print(f"  Target: ({best_target[0]:.3f}, {best_target[1]:.3f}, {best_target[2]:.3f})")
        return None

def main():
    print("=" * 70)
    print("Phase 1 & 3 Right Arm Optimization")
    print("=" * 70)

    right_base = np.array(ROBOT_RIGHT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    print(f"\nRight base: {ROBOT_RIGHT_BASE}")

    # Phase 1: Right arm at (0.30, +0.285, 0.905)
    phase1_original = np.array([0.30, 0.285, 0.905])
    result1 = optimize_waypoint("Phase 1 Right", phase1_original, right_base, base_quat, target_quat)

    # Phase 3: Right arm at (0.30, +0.285, 0.90)
    phase3_original = np.array([0.30, 0.285, 0.90])
    result3 = optimize_waypoint("Phase 3 Right", phase3_original, right_base, base_quat, target_quat)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if result1:
        print(f"\nPhase 1 Right: Use ({result1['target'][0]:.3f}, {result1['target'][1]:.3f}, {result1['target'][2]:.3f})")
        print(f"  Margin: {result1['margin']:.1f}°")
    else:
        print("\nPhase 1 Right: No configuration found with margin >= 20°")

    if result3:
        print(f"\nPhase 3 Right: Use ({result3['target'][0]:.3f}, {result3['target'][1]:.3f}, {result3['target'][2]:.3f})")
        print(f"  Margin: {result3['margin']:.1f}°")
    else:
        print("\nPhase 3 Right: No configuration found with margin >= 20°")

    return result1, result3


if __name__ == "__main__":
    result1, result3 = main()
