#!/usr/bin/env python3
"""
Phase 4 Right Arm Optimization Script

Search for waypoint adjustments to improve the joint margin while
keeping the waypoint close to the original target.
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

def main():
    print("=" * 70)
    print("Phase 4 Right Arm Optimization")
    print("=" * 70)

    right_base = np.array(ROBOT_RIGHT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    # Original target
    original_target = np.array([0.36, 0.18, 0.85])

    print(f"\nOriginal target: {original_target}")
    print(f"Right base: {ROBOT_RIGHT_BASE}")

    # Search space around original target
    best_margin = 0
    best_target = None
    best_joints = None

    results = []

    # Scan X, Y, Z variations
    for dx in np.arange(-0.05, 0.06, 0.01):
        for dy in np.arange(-0.05, 0.06, 0.01):
            for dz in np.arange(-0.05, 0.06, 0.02):
                target = original_target + np.array([dx, dy, dz])

                success, joints, margin = solve_ik_best(
                    target, right_base, base_quat, target_quat,
                    q7_range=(-2.5, 2.5), q7_steps=50
                )

                if success and margin >= 20.0:
                    dist = np.linalg.norm(target - original_target)
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

    print(f"\n{'=' * 60}")
    print("Results with margin >= 20°:")
    print("=" * 60)

    if results:
        # Sort by margin
        results.sort(key=lambda x: x['margin'], reverse=True)

        print(f"\nFound {len(results)} valid configurations")
        print("\nTop 10 by margin:")
        for i, r in enumerate(results[:10]):
            print(f"  {i+1}. Target: ({r['target'][0]:.3f}, {r['target'][1]:.3f}, {r['target'][2]:.3f})")
            print(f"     Margin: {r['margin']:.1f}°, Distance from original: {r['distance']*100:.1f}cm")

        # Sort by closeness to original
        results.sort(key=lambda x: x['distance'])

        print("\nTop 5 closest to original target:")
        for i, r in enumerate(results[:5]):
            print(f"  {i+1}. Target: ({r['target'][0]:.3f}, {r['target'][1]:.3f}, {r['target'][2]:.3f})")
            print(f"     Margin: {r['margin']:.1f}°, Distance from original: {r['distance']*100:.1f}cm")
            print(f"     Joints (rad): [{', '.join([f'{j:+.6f}' for j in r['joints']])}]")
    else:
        print("\nNo configurations found with margin >= 20°")
        print("Showing best found:")

        # Find overall best
        for dx in np.arange(-0.05, 0.06, 0.02):
            for dy in np.arange(-0.05, 0.06, 0.02):
                for dz in np.arange(-0.05, 0.06, 0.02):
                    target = original_target + np.array([dx, dy, dz])

                    success, joints, margin = solve_ik_best(
                        target, right_base, base_quat, target_quat,
                        q7_range=(-2.5, 2.5), q7_steps=50
                    )

                    if success and margin > best_margin:
                        best_margin = margin
                        best_target = target.copy()
                        best_joints = joints.copy()

        if best_target is not None:
            print(f"\nBest target: ({best_target[0]:.3f}, {best_target[1]:.3f}, {best_target[2]:.3f})")
            print(f"Margin: {best_margin:.1f}°")
            print(f"Distance from original: {np.linalg.norm(best_target - original_target)*100:.1f}cm")

    return results


if __name__ == "__main__":
    results = main()
