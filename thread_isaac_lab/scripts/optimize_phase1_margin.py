#!/usr/bin/env python3
"""
Phase 1 IK Re-optimization Script

Goal: Achieve joint margin >= 22.8° for Phase 1 (hover position)

Strategy:
1. Search over q7 more finely for better margins
2. Try small variations in Phase 1 EE position
3. Keep base positions fixed (from current config)
"""

import numpy as np
from typing import Tuple, List, Dict
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import (
    solve_ik_best, compute_joint_margin, Q_MIN, Q_MAX,
    franka_IK_EE_with_base
)

# Current configuration from task_config.py
CURRENT_BASE_X = 0.2467
CURRENT_BASE_Y_LEFT = -0.4200
CURRENT_BASE_Y_RIGHT = 0.2000
CURRENT_BASE_Z = 1.265

WALL_MOUNT_QUAT = np.array([0.7071, 0.0, 0.7071, 0.0])  # (w,x,y,z)
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # (w,x,y,z)

# Phase 1 target positions
PHASE1_LEFT = np.array([0.30, -0.285, 0.905])
PHASE1_RIGHT = np.array([0.30, +0.285, 0.905])

# Target margin
TARGET_MARGIN = 22.8


def solve_ik_fine(target_pos: np.ndarray, base_pos: np.ndarray,
                  q7_range: tuple = (-2.8, 2.8), q7_steps: int = 100) -> Tuple[bool, np.ndarray, float]:
    """
    Fine-grained IK search over q7 to maximize margin.
    """
    best_solution = None
    best_margin = -1.0

    for q7 in np.linspace(q7_range[0], q7_range[1], q7_steps):
        solutions = franka_IK_EE_with_base(
            target_pos, GRIPPER_DOWN_QUAT,
            base_pos, WALL_MOUNT_QUAT, q7
        )

        for sol in solutions:
            if sol.valid and sol.margin_deg > best_margin:
                best_margin = sol.margin_deg
                best_solution = sol.joints.copy()

    if best_solution is not None:
        return True, best_solution, best_margin
    return False, None, 0.0


def search_phase1_positions(base_left: np.ndarray, base_right: np.ndarray,
                            target_margin: float = TARGET_MARGIN,
                            verbose: bool = True) -> Dict:
    """
    Search for Phase 1 EE positions that achieve target margin.

    Try variations in X, Y, Z around current Phase 1 positions.
    """
    results = []

    # Search ranges (small variations around current position)
    x_range = np.linspace(0.28, 0.32, 5)
    z_range = np.linspace(0.88, 0.93, 6)

    # Y positions stay symmetric around cable endpoints
    y_left_range = np.linspace(-0.30, -0.27, 4)
    y_right_range = np.linspace(0.27, 0.30, 4)

    total = len(x_range) * len(z_range) * len(y_left_range) * len(y_right_range)
    count = 0

    print(f"\n[SEARCH] Phase 1 Position Search")
    print(f"  Total configurations: {total}")
    print(f"  Target margin: {target_margin}°")

    for x in x_range:
        for z in z_range:
            for yl in y_left_range:
                for yr in y_right_range:
                    count += 1

                    left_target = np.array([x, yl, z])
                    right_target = np.array([x, yr, z])

                    # Solve IK with fine q7 search
                    left_ok, left_joints, left_margin = solve_ik_fine(
                        left_target, base_left, q7_steps=100
                    )
                    right_ok, right_joints, right_margin = solve_ik_fine(
                        right_target, base_right, q7_steps=100
                    )

                    if left_ok and right_ok:
                        min_margin = min(left_margin, right_margin)
                        results.append({
                            'left_target': left_target.copy(),
                            'right_target': right_target.copy(),
                            'left_joints': left_joints,
                            'right_joints': right_joints,
                            'left_margin': left_margin,
                            'right_margin': right_margin,
                            'min_margin': min_margin
                        })

                        if min_margin >= target_margin and verbose:
                            print(f"\n  [FOUND] Config #{count}: min_margin={min_margin:.1f}°")
                            print(f"    Left:  {left_target} -> {left_margin:.1f}°")
                            print(f"    Right: {right_target} -> {right_margin:.1f}°")

    # Sort by minimum margin
    results.sort(key=lambda r: r['min_margin'], reverse=True)

    return results


def search_base_variations(target_margin: float = TARGET_MARGIN) -> List[Dict]:
    """
    Search for base position variations that improve Phase 1 margin.

    Only vary base Z slightly, keep X and Y separation.
    """
    results = []

    # Base Z variations
    z_range = np.linspace(1.24, 1.29, 6)

    # Base X variations (small)
    x_range = np.linspace(0.23, 0.27, 5)

    # Y separation variations
    y_left_range = np.linspace(-0.44, -0.40, 3)
    y_right_range = np.linspace(0.18, 0.22, 3)

    total = len(z_range) * len(x_range) * len(y_left_range) * len(y_right_range)
    count = 0

    print(f"\n[SEARCH] Base Position Search")
    print(f"  Total configurations: {total}")
    print(f"  Target margin: {target_margin}°")

    for bz in z_range:
        for bx in x_range:
            for byl in y_left_range:
                for byr in y_right_range:
                    count += 1

                    base_left = np.array([bx, byl, bz])
                    base_right = np.array([bx, byr, bz])

                    # Use original Phase 1 targets
                    left_ok, left_joints, left_margin = solve_ik_fine(
                        PHASE1_LEFT, base_left, q7_steps=80
                    )
                    right_ok, right_joints, right_margin = solve_ik_fine(
                        PHASE1_RIGHT, base_right, q7_steps=80
                    )

                    if left_ok and right_ok:
                        min_margin = min(left_margin, right_margin)
                        results.append({
                            'base_left': base_left.copy(),
                            'base_right': base_right.copy(),
                            'left_joints': left_joints,
                            'right_joints': right_joints,
                            'left_margin': left_margin,
                            'right_margin': right_margin,
                            'min_margin': min_margin
                        })

                        if min_margin >= target_margin:
                            print(f"\n  [FOUND] Config #{count}: min_margin={min_margin:.1f}°")
                            print(f"    Base L: {base_left}")
                            print(f"    Base R: {base_right}")

    results.sort(key=lambda r: r['min_margin'], reverse=True)
    return results


def format_joints_for_config(joints: np.ndarray, name: str) -> str:
    """Format joint angles for task_config.py"""
    lines = [f"{name} = ["]
    joint_names = ["panda_joint1", "panda_joint2", "panda_joint3", "panda_joint4",
                   "panda_joint5", "panda_joint6", "panda_joint7"]
    for i, (jn, angle) in enumerate(zip(joint_names, joints)):
        comma = "," if i < 6 else ","
        lines.append(f"    {angle:+.6f}{comma}  # {jn}: {np.degrees(angle):+.1f} deg")
    lines.append("]")
    return "\n".join(lines)


def verify_all_phases(base_left: np.ndarray, base_right: np.ndarray,
                      phase1_left: np.ndarray = None, phase1_right: np.ndarray = None) -> Dict:
    """
    Verify all phases work with given base positions.
    """
    if phase1_left is None:
        phase1_left = PHASE1_LEFT
    if phase1_right is None:
        phase1_right = PHASE1_RIGHT

    waypoints = {
        'Phase1': {'left': phase1_left, 'right': phase1_right},
        'Phase2': {'left': np.array([0.30, -0.285, 0.7639]), 'right': np.array([0.30, +0.285, 0.7639])},
        'Phase3': {'left': np.array([0.30, -0.285, 0.90]), 'right': np.array([0.30, +0.285, 0.90])},
        'Phase4': {'left': np.array([0.36, -0.18, 0.85]), 'right': np.array([0.36, +0.18, 0.85])},
        'Phase5': {'left': np.array([0.30, -0.25, 0.85]), 'right': np.array([0.30, 0.067, 0.85])},
    }

    results = {}
    all_ok = True

    for phase, targets in waypoints.items():
        left_ok, left_joints, left_margin = solve_ik_fine(
            targets['left'], base_left, q7_steps=50
        )
        right_ok, right_joints, right_margin = solve_ik_fine(
            targets['right'], base_right, q7_steps=50
        )

        results[phase] = {
            'left_ok': left_ok,
            'right_ok': right_ok,
            'left_margin': left_margin,
            'right_margin': right_margin,
            'min_margin': min(left_margin, right_margin) if left_ok and right_ok else 0,
            'left_joints': left_joints,
            'right_joints': right_joints,
        }

        if not (left_ok and right_ok):
            all_ok = False

    results['all_ok'] = all_ok
    return results


def main():
    print("=" * 70)
    print("Phase 1 IK Re-optimization")
    print("=" * 70)
    print(f"\nTarget: Joint margin >= {TARGET_MARGIN}°")

    # Current base positions
    base_left = np.array([CURRENT_BASE_X, CURRENT_BASE_Y_LEFT, CURRENT_BASE_Z])
    base_right = np.array([CURRENT_BASE_X, CURRENT_BASE_Y_RIGHT, CURRENT_BASE_Z])

    print(f"\nCurrent Base Left:  {base_left}")
    print(f"Current Base Right: {base_right}")

    # Step 1: Check current configuration with finer q7 search
    print("\n" + "=" * 50)
    print("[STEP 1] Fine-grained q7 search for current config")
    print("=" * 50)

    left_ok, left_joints, left_margin = solve_ik_fine(
        PHASE1_LEFT, base_left, q7_steps=200
    )
    right_ok, right_joints, right_margin = solve_ik_fine(
        PHASE1_RIGHT, base_right, q7_steps=200
    )

    print(f"\nCurrent Phase 1 (with fine q7):")
    print(f"  Left:  target={PHASE1_LEFT} -> margin={left_margin:.1f}°")
    print(f"  Right: target={PHASE1_RIGHT} -> margin={right_margin:.1f}°")
    print(f"  Min margin: {min(left_margin, right_margin):.1f}°")

    if min(left_margin, right_margin) >= TARGET_MARGIN:
        print(f"\n[SUCCESS] Target margin achieved with finer q7 search!")
        print("\nUpdated joint angles:")
        print(format_joints_for_config(left_joints, "LEFT_ARM_INIT_JOINTS"))
        print()
        print(format_joints_for_config(right_joints, "RIGHT_ARM_INIT_JOINTS"))
    else:
        # Step 2: Search for better Phase 1 positions
        print("\n" + "=" * 50)
        print("[STEP 2] Searching for better Phase 1 EE positions")
        print("=" * 50)

        pos_results = search_phase1_positions(base_left, base_right, TARGET_MARGIN)

        if pos_results and pos_results[0]['min_margin'] >= TARGET_MARGIN:
            best = pos_results[0]
            print(f"\n[SUCCESS] Found Phase 1 positions with {best['min_margin']:.1f}° margin!")
            print(f"  Left EE:  {best['left_target']}")
            print(f"  Right EE: {best['right_target']}")

            # Verify all phases
            print("\n[VERIFY] Checking all phases...")
            verify = verify_all_phases(base_left, base_right,
                                       best['left_target'], best['right_target'])

            print("\nPhase verification results:")
            for phase, data in verify.items():
                if phase == 'all_ok':
                    continue
                print(f"  {phase}: L={data['left_margin']:.1f}° R={data['right_margin']:.1f}° "
                      f"-> {'OK' if data['left_ok'] and data['right_ok'] else 'FAIL'}")

            if verify['all_ok']:
                print("\n[OUTPUT] Updated values for task_config.py:")
                print("\n# Phase 1 EE positions (re-optimized)")
                print(f"WAYPOINT_PHASE1_LEFT = ({best['left_target'][0]:.3f}, {best['left_target'][1]:.3f}, {best['left_target'][2]:.3f})")
                print(f"WAYPOINT_PHASE1_RIGHT = ({best['right_target'][0]:.3f}, {best['right_target'][1]:.3f}, {best['right_target'][2]:.3f})")
                print()
                print(format_joints_for_config(best['left_joints'], "LEFT_ARM_INIT_JOINTS"))
                print()
                print(format_joints_for_config(best['right_joints'], "RIGHT_ARM_INIT_JOINTS"))
        else:
            # Step 3: Search for better base positions
            print("\n" + "=" * 50)
            print("[STEP 3] Searching for better base positions")
            print("=" * 50)

            base_results = search_base_variations(TARGET_MARGIN)

            if base_results and base_results[0]['min_margin'] >= TARGET_MARGIN:
                best = base_results[0]
                print(f"\n[SUCCESS] Found base positions with {best['min_margin']:.1f}° margin!")
                print(f"  Base Left:  {best['base_left']}")
                print(f"  Base Right: {best['base_right']}")

                # Verify all phases
                print("\n[VERIFY] Checking all phases with new base positions...")
                verify = verify_all_phases(best['base_left'], best['base_right'])

                for phase, data in verify.items():
                    if phase == 'all_ok':
                        continue
                    print(f"  {phase}: L={data['left_margin']:.1f}° R={data['right_margin']:.1f}°")
            else:
                print("\n[INFO] No configuration found meeting target. Best results:")

                # Show best from position search
                if pos_results:
                    print(f"\n  Best from position search: {pos_results[0]['min_margin']:.1f}°")

                # Show best from base search
                if base_results:
                    print(f"  Best from base search: {base_results[0]['min_margin']:.1f}°")

                # Show top 5 from each
                print("\n  Top 5 Phase 1 positions:")
                for i, r in enumerate(pos_results[:5]):
                    print(f"    #{i+1}: L={r['left_margin']:.1f}° R={r['right_margin']:.1f}° "
                          f"at L={r['left_target']} R={r['right_target']}")


if __name__ == "__main__":
    main()
