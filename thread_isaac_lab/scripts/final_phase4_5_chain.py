#!/usr/bin/env python3
"""
Final calculation of Phase 4 → 4.5 → 5 chain with improved margins.

IMPORTANT: Robot base positions are now read from task_config.py
to ensure consistency with the actual simulation.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab')

from franka_analytical_ik import franka_IK_EE_with_base
from configs.task_config import ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE

# Robot base positions FROM task_config.py (single source of truth)
LEFT_BASE = np.array(ROBOT_LEFT_BASE)
RIGHT_BASE = np.array(ROBOT_RIGHT_BASE)
print(f"Using base positions from task_config.py:")
print(f"  LEFT_BASE  = {LEFT_BASE}")
print(f"  RIGHT_BASE = {RIGHT_BASE}")

WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Phase 4 (elbow-down, X > 0.336)
# From search_phase4_elbow_down.py (2025-12-29)
PHASE4_LEFT = np.array([0.36, -0.18, 0.85])
PHASE4_RIGHT = np.array([0.36, 0.18, 0.85])

# Phase 5 (elbow-down, X > 0.336)
# From search_phase5_better_margin.py (2025-12-29)
PHASE5_LEFT = np.array([0.36, -0.27, 0.87])   # Symmetric offset for left arm
PHASE5_RIGHT = np.array([0.36, 0.18, 0.87])

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
            if joints[4] >= 0:
                continue
            if not check_joint_limits(joints):
                continue
            margin = compute_joint_margin(joints)
            if margin > best_margin:
                best_margin = margin
                best_joints = joints.copy()

    return best_joints, best_margin

def format_joints(joints, name):
    lines = [f"{name} = ["]
    for i, j in enumerate(joints):
        deg = np.degrees(j)
        sign = "+" if j >= 0 else ""
        lines.append(f"    {sign}{j:.6f},  # panda_joint{i+1}: {sign}{deg:.1f} deg")
    lines.append("]")
    return "\n".join(lines)

def analyze_transition(joints1, joints2, name):
    delta = np.degrees(joints2 - joints1)
    max_change = np.max(np.abs(delta))
    print(f"  {name}: max={max_change:.1f}°", end="")
    if max_change <= 30:
        print(" ✅")
    else:
        print(" ⚠️")
    return max_change

def main():
    print("=" * 70)
    print("Final Phase 4 → 4.5 → 5 Chain Calculation")
    print("=" * 70)
    print()

    # Calculate Phase 4.5 (midpoint between new Phase 4 and Phase 5)
    phase45_left = (PHASE4_LEFT + PHASE5_LEFT) / 2
    phase45_right = (PHASE4_RIGHT + PHASE5_RIGHT) / 2

    print("EE Positions:")
    print(f"  Phase 4:   Left={PHASE4_LEFT}, Right={PHASE4_RIGHT}")
    print(f"  Phase 4.5: Left={phase45_left}, Right={phase45_right}")
    print(f"  Phase 5:   Left={PHASE5_LEFT}, Right={PHASE5_RIGHT}")
    print()

    # Solve all IK
    results = {}

    for phase, left_ee, right_ee in [
        ("Phase4", PHASE4_LEFT, PHASE4_RIGHT),
        ("Phase45", phase45_left, phase45_right),
        ("Phase5", PHASE5_LEFT, PHASE5_RIGHT),
    ]:
        left_joints, left_margin = solve_ik_elbow_down(left_ee, LEFT_BASE)
        right_joints, right_margin = solve_ik_elbow_down(right_ee, RIGHT_BASE)

        results[phase] = {
            'left_ee': left_ee,
            'right_ee': right_ee,
            'left_joints': left_joints,
            'right_joints': right_joints,
            'left_margin': left_margin,
            'right_margin': right_margin,
        }

        print(f"{phase}:")
        if left_joints is not None:
            print(f"  Left:  margin={left_margin:.1f}°, J5={np.degrees(left_joints[4]):.1f}°")
        else:
            print(f"  Left:  FAILED")
        if right_joints is not None:
            print(f"  Right: margin={right_margin:.1f}°, J5={np.degrees(right_joints[4]):.1f}°")
        else:
            print(f"  Right: FAILED")
        print()

    # Transition analysis
    print("=" * 70)
    print("Transition Analysis")
    print("=" * 70)
    print()

    all_ok = True
    transitions = [("Phase4", "Phase45"), ("Phase45", "Phase5")]

    for p1, p2 in transitions:
        print(f"{p1} → {p2}:")
        if results[p1]['left_joints'] is not None and results[p2]['left_joints'] is not None:
            max_left = analyze_transition(results[p1]['left_joints'], results[p2]['left_joints'], "Left")
            if max_left > 30:
                all_ok = False
        if results[p1]['right_joints'] is not None and results[p2]['right_joints'] is not None:
            max_right = analyze_transition(results[p1]['right_joints'], results[p2]['right_joints'], "Right")
            if max_right > 30:
                all_ok = False
        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    margins = []
    for phase in results.values():
        if phase['left_margin']:
            margins.append(phase['left_margin'])
        if phase['right_margin']:
            margins.append(phase['right_margin'])

    min_margin = min(margins) if margins else 0
    print(f"Worst-case margin: {min_margin:.1f}°")

    if all_ok and min_margin > 10:
        print("✅ All transitions smooth and margins adequate")
    else:
        print("⚠️ Issues detected")

    # Output
    print()
    print("=" * 70)
    print("Copy-paste for task_config.py:")
    print("=" * 70)
    print()

    # Phase 4
    r = results["Phase4"]
    print("# Phase 4: Hook approach (elbow-down)")
    print(f"WAYPOINT_PHASE4_LEFT = ({r['left_ee'][0]:.2f}, {r['left_ee'][1]:.2f}, {r['left_ee'][2]:.2f})")
    print(f"WAYPOINT_PHASE4_RIGHT = ({r['right_ee'][0]:.2f}, {r['right_ee'][1]:.2f}, {r['right_ee'][2]:.2f})")
    print()
    print(format_joints(r['left_joints'], 'PHASE4_LEFT_JOINTS'))
    print()
    print(format_joints(r['right_joints'], 'PHASE4_RIGHT_JOINTS'))
    print()

    # Phase 4.5
    r = results["Phase45"]
    print("# Phase 4.5: Intermediate")
    print(f"WAYPOINT_PHASE45_LEFT = ({r['left_ee'][0]:.3f}, {r['left_ee'][1]:.3f}, {r['left_ee'][2]:.3f})")
    print(f"WAYPOINT_PHASE45_RIGHT = ({r['right_ee'][0]:.3f}, {r['right_ee'][1]:.3f}, {r['right_ee'][2]:.3f})")
    print()
    print(format_joints(r['left_joints'], 'PHASE45_LEFT_JOINTS'))
    print()
    print(format_joints(r['right_joints'], 'PHASE45_RIGHT_JOINTS'))
    print()

    # Phase 5
    r = results["Phase5"]
    print("# Phase 5: Place (improved margin)")
    print(f"WAYPOINT_PHASE5_LEFT = ({r['left_ee'][0]:.2f}, {r['left_ee'][1]:.2f}, {r['left_ee'][2]:.2f})")
    print(f"WAYPOINT_PHASE5_RIGHT = ({r['right_ee'][0]:.2f}, {r['right_ee'][1]:.2f}, {r['right_ee'][2]:.2f})")
    print()
    print(format_joints(r['left_joints'], 'PHASE5_LEFT_JOINTS'))
    print()
    print(format_joints(r['right_joints'], 'PHASE5_RIGHT_JOINTS'))

if __name__ == "__main__":
    main()
