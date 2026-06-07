#!/usr/bin/env python3
"""
全Phase (1-5) IK統一計算スクリプト

task_config.pyからベース位置をインポートし、
全Phaseの関節角度を一括計算する。

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
    print("All Phases (1-5) IK Calculation with Correct Base Positions")
    print("=" * 70)

    left_base = np.array(ROBOT_LEFT_BASE)
    right_base = np.array(ROBOT_RIGHT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    print(f"\nBase Positions (from task_config.py):")
    print(f"  LEFT_BASE:  {ROBOT_LEFT_BASE}")
    print(f"  RIGHT_BASE: {ROBOT_RIGHT_BASE}")
    print(f"  BASE_QUAT:  {ROBOT_BASE_QUAT_WXYZ}")
    print(f"  GRIPPER_DOWN_QUAT: {GRIPPER_DOWN_QUAT_WXYZ}")

    # Waypoints from TASKS_T1.md
    # Phase 4 optimized for margin >= 20°
    phases = [
        ("Phase 1", "Initial hover (15cm above cable)",
         (0.30, -0.285, 0.905), (0.30, +0.285, 0.905)),
        ("Phase 2", "Grasp position (fingertip at cable center)",
         (0.30, -0.285, 0.75), (0.30, +0.285, 0.75)),
        ("Phase 3", "Lift position (after grasp)",
         (0.30, -0.285, 0.90), (0.30, +0.285, 0.90)),
        ("Phase 4", "Hook approach (optimized for margin >= 20°)",
         (0.35, -0.17, 0.82), (0.35, 0.17, 0.82)),
        ("Phase 4.5", "Intermediate (between Phase 4 and 5)",
         (0.33, -0.215, 0.85), (0.33, 0.1235, 0.85)),
        ("Phase 5", "Cable placement",
         (0.30, -0.25, 0.85), (0.30, 0.067, 0.85)),
    ]

    print(f"\nWaypoints:")
    for name, desc, left, right in phases:
        print(f"  {name}: Left={left}, Right={right}")

    results = {}
    all_success = True
    all_margin_ok = True

    for phase_name, description, left_wp, right_wp in phases:
        print(f"\n{'=' * 60}")
        print(f"{phase_name}: {description}")
        print(f"{'=' * 60}")

        # Left arm
        left_target = np.array(left_wp)
        success_left, joints_left, margin_left = solve_ik_best(
            left_target, left_base, base_quat, target_quat,
            q7_range=(-2.5, 2.5), q7_steps=100
        )

        # Right arm
        right_target = np.array(right_wp)
        success_right, joints_right, margin_right = solve_ik_best(
            right_target, right_base, base_quat, target_quat,
            q7_range=(-2.5, 2.5), q7_steps=100
        )

        print(f"  Left:  Target={left_wp}")
        if success_left:
            print(f"         Margin: {margin_left:.1f}°")
            if margin_left < 20:
                all_margin_ok = False
                print(f"         [WARNING] Margin < 20°")
        else:
            print(f"         FAILED - No valid IK solution")
            all_success = False

        print(f"  Right: Target={right_wp}")
        if success_right:
            print(f"         Margin: {margin_right:.1f}°")
            if margin_right < 20:
                all_margin_ok = False
                print(f"         [WARNING] Margin < 20°")
        else:
            print(f"         FAILED - No valid IK solution")
            all_success = False

        results[phase_name] = {
            "description": description,
            "left": {"success": success_left, "joints": joints_left, "margin": margin_left, "waypoint": left_wp},
            "right": {"success": success_right, "joints": joints_right, "margin": margin_right, "waypoint": right_wp},
        }

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    min_margin = float('inf')
    for phase_name, data in results.items():
        if data["left"]["success"] and data["right"]["success"]:
            min_margin = min(min_margin, data["left"]["margin"], data["right"]["margin"])

    print(f"\nMinimum margin: {min_margin:.1f}°")
    if min_margin >= 20:
        print("[OK] All margins >= 20°")
    else:
        print(f"[WARNING] Some margins < 20°")

    if all_success:
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
            desc = data["description"]

            print(f"\n# {phase_name}: {desc}")
            print(f"# EE Left:  {left_wp}  Margin: {left_margin:.1f}°")
            print(f"# EE Right: {right_wp}  Margin: {right_margin:.1f}°")
            print(f"# Gripper orientation: GRIPPER_DOWN_QUAT = (0, 0.7071, -0.7071, 0)")

            # Variable names based on phase
            if phase_name == "Phase 1":
                left_var = "LEFT_ARM_INIT_JOINTS"
                right_var = "RIGHT_ARM_INIT_JOINTS"
            elif phase_name == "Phase 4.5":
                left_var = "PHASE45_LEFT_JOINTS"
                right_var = "PHASE45_RIGHT_JOINTS"
            else:
                left_var = f"{phase_key}_LEFT_JOINTS"
                right_var = f"{phase_key}_RIGHT_JOINTS"

            print(f"{left_var} = [")
            for i, j in enumerate(left_joints):
                deg = np.degrees(j)
                print(f"    {j:+.6f},  # panda_joint{i+1}: {deg:+.1f} deg")
            print("]")

            print(f"\n{right_var} = [")
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
                    status = "[OK]" if max_diff_deg < 15 else "[WARN]"
                    print(f"  {status} {from_phase} -> {to_phase} ({arm}): max Δ = {max_diff_deg:.1f}° (joint{max_diff_idx + 1})")

        # Margins table
        print("\n" + "-" * 60)
        print("Margins Summary:")
        print("-" * 60)
        print(f"{'Phase':<12} {'Left':>10} {'Right':>10}")
        print("-" * 32)
        for phase_name, data in results.items():
            l_margin = data["left"]["margin"]
            r_margin = data["right"]["margin"]
            l_status = "✓" if l_margin >= 20 else "!"
            r_status = "✓" if r_margin >= 20 else "!"
            print(f"{phase_name:<12} {l_margin:>8.1f}° {l_status} {r_margin:>8.1f}° {r_status}")

    else:
        print("\n[FAILED] Some IK solutions failed!")
        for phase_name, data in results.items():
            l_ok = "OK" if data["left"]["success"] else "FAILED"
            r_ok = "OK" if data["right"]["success"] else "FAILED"
            print(f"  {phase_name}: Left={l_ok}, Right={r_ok}")

    return all_success and all_margin_ok, results


if __name__ == "__main__":
    success, results = main()
    sys.exit(0 if success else 1)
