#!/usr/bin/env python3
"""
Phase 4/4.5/5 IK再計算スクリプト（正しいベース位置使用）

task_config.pyからベース位置をインポートして、
正しいIK計算を行う。

T1タスク: 2026-01-02
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab')

from thread_isaac_lab.configs.task_config import (
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    ROBOT_BASE_QUAT_WXYZ,
    GRIPPER_DOWN_QUAT_WXYZ,
)

from thread_isaac_lab.scripts.franka_analytical_ik import solve_ik_best

def main():
    print("=" * 70)
    print("Phase 4/4.5/5 IK Recalculation with Correct Base Positions")
    print("=" * 70)

    # Base positions from task_config.py
    left_base = np.array(ROBOT_LEFT_BASE)
    right_base = np.array(ROBOT_RIGHT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    print(f"\nBase Positions (from task_config.py):")
    print(f"  LEFT_BASE:  {ROBOT_LEFT_BASE}")
    print(f"  RIGHT_BASE: {ROBOT_RIGHT_BASE}")
    print(f"  BASE_QUAT:  {ROBOT_BASE_QUAT_WXYZ}")

    # Waypoints from TASKS_T1.md (as specified in the task instructions)
    WAYPOINT_PHASE4_LEFT = (0.36, -0.18, 0.85)
    WAYPOINT_PHASE4_RIGHT = (0.36, 0.18, 0.85)
    WAYPOINT_PHASE45_LEFT = (0.33, -0.215, 0.85)
    WAYPOINT_PHASE45_RIGHT = (0.33, 0.1235, 0.85)
    WAYPOINT_PHASE5_LEFT = (0.30, -0.25, 0.85)
    WAYPOINT_PHASE5_RIGHT = (0.30, 0.067, 0.85)

    phases = [
        ("Phase 4", WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT),
        ("Phase 4.5", WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT),
        ("Phase 5", WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT),
    ]

    print(f"\nWaypoints (from TASKS_T1.md):")
    for name, left, right in phases:
        print(f"  {name}: Left={left}, Right={right}")

    results = {}
    all_success = True

    for phase_name, left_wp, right_wp in phases:
        print(f"\n{'=' * 60}")
        print(f"{phase_name}")
        print(f"{'=' * 60}")
        print(f"  Left target:  {left_wp}")
        print(f"  Right target: {right_wp}")

        # Solve IK for left arm
        left_target = np.array(left_wp)
        success_left, joints_left, margin_left = solve_ik_best(
            left_target, left_base, base_quat, target_quat,
            q7_range=(-2.5, 2.5), q7_steps=100
        )

        # Solve IK for right arm
        right_target = np.array(right_wp)
        success_right, joints_right, margin_right = solve_ik_best(
            right_target, right_base, base_quat, target_quat,
            q7_range=(-2.5, 2.5), q7_steps=100
        )

        print(f"\n  Left arm:")
        if success_left:
            print(f"    SUCCESS - Margin: {margin_left:.1f} deg")
            print(f"    Joints (rad): [{', '.join([f'{j:+.6f}' for j in joints_left])}]")
            print(f"    Joints (deg): [{', '.join([f'{np.degrees(j):+.1f}' for j in joints_left])}]")
        else:
            print(f"    FAILED - No valid IK solution")
            all_success = False

        print(f"\n  Right arm:")
        if success_right:
            print(f"    SUCCESS - Margin: {margin_right:.1f} deg")
            print(f"    Joints (rad): [{', '.join([f'{j:+.6f}' for j in joints_right])}]")
            print(f"    Joints (deg): [{', '.join([f'{np.degrees(j):+.1f}' for j in joints_right])}]")
        else:
            print(f"    FAILED - No valid IK solution")
            all_success = False

        results[phase_name] = {
            "left": {"success": success_left, "joints": joints_left, "margin": margin_left, "waypoint": left_wp},
            "right": {"success": success_right, "joints": joints_right, "margin": margin_right, "waypoint": right_wp},
        }

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if all_success:
        print("\n[SUCCESS] All IK solutions found!")

        # Print in task_config.py format
        print("\n" + "-" * 60)
        print("task_config.py format (copy-paste ready):")
        print("-" * 60)

        for phase_name, data in results.items():
            phase_key = phase_name.replace(" ", "").replace(".", "").upper()
            left_joints = data["left"]["joints"]
            right_joints = data["right"]["joints"]
            left_margin = data["left"]["margin"]
            right_margin = data["right"]["margin"]
            left_wp = data["left"]["waypoint"]
            right_wp = data["right"]["waypoint"]

            print(f"\n# {phase_name}")
            print(f"# EE Left:  {left_wp}  Margin: {left_margin:.1f}°")
            print(f"# EE Right: {right_wp}  Margin: {right_margin:.1f}°")
            print(f"# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)")

            if phase_key == "PHASE45":
                print(f"WAYPOINT_PHASE45_LEFT = {left_wp}")
                print(f"WAYPOINT_PHASE45_RIGHT = {right_wp}")
                print()
            elif phase_key == "PHASE5":
                print(f"WAYPOINT_PHASE5_LEFT = {left_wp}")
                print(f"WAYPOINT_PHASE5_RIGHT = {right_wp}")
                print()

            print(f"{phase_key}_LEFT_JOINTS = [")
            for i, j in enumerate(left_joints):
                deg = np.degrees(j)
                print(f"    {j:+.6f},  # panda_joint{i+1}: {deg:+.1f} deg")
            print("]")

            print(f"\n{phase_key}_RIGHT_JOINTS = [")
            for i, j in enumerate(right_joints):
                deg = np.degrees(j)
                print(f"    {j:+.6f},  # panda_joint{i+1}: {deg:+.1f} deg")
            print("]")

        # Transition analysis
        print("\n" + "-" * 60)
        print("Transition Analysis (max angle change):")
        print("-" * 60)

        phase_keys = list(results.keys())
        for i in range(len(phase_keys) - 1):
            from_phase = phase_keys[i]
            to_phase = phase_keys[i + 1]

            for arm in ["left", "right"]:
                from_joints = results[from_phase][arm]["joints"]
                to_joints = results[to_phase][arm]["joints"]

                if from_joints is not None and to_joints is not None:
                    diff = np.abs(to_joints - from_joints)
                    max_diff_idx = np.argmax(diff)
                    max_diff_deg = np.degrees(diff[max_diff_idx])

                    print(f"  {from_phase} -> {to_phase} ({arm}): max Δ = {max_diff_deg:.1f}° (joint{max_diff_idx + 1})")

        # Min margins
        print("\n" + "-" * 60)
        print("Minimum Margins:")
        print("-" * 60)

        min_margin = float('inf')
        for phase_name, data in results.items():
            l_margin = data["left"]["margin"]
            r_margin = data["right"]["margin"]
            print(f"  {phase_name}: Left={l_margin:.1f}°, Right={r_margin:.1f}°")
            min_margin = min(min_margin, l_margin, r_margin)

        print(f"\n  Overall minimum margin: {min_margin:.1f}°")

        if min_margin >= 20.0:
            print("  [OK] All margins >= 20°")
        else:
            print(f"  [WARNING] Some margins < 20°")

    else:
        print("\n[FAILED] Some IK solutions failed!")
        for phase_name, data in results.items():
            l_ok = "OK" if data["left"]["success"] else "FAILED"
            r_ok = "OK" if data["right"]["success"] else "FAILED"
            print(f"  {phase_name}: Left={l_ok}, Right={r_ok}")

    return all_success, results


if __name__ == "__main__":
    success, results = main()
    sys.exit(0 if success else 1)
