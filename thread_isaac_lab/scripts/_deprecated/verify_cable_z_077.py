#!/usr/bin/env python3
"""
Verify IK feasibility with CABLE_Z = 0.77 using current optimal robot configuration.
"""

import numpy as np
import sys
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab/scripts')

from franka_analytical_ik import solve_ik_best, forward_kinematics

# Current optimal robot configuration (from grid=6 optimization)
ROBOT_LEFT_BASE = np.array([0.3360, -0.4200, 1.2800])
ROBOT_RIGHT_BASE = np.array([0.3360, 0.2960, 1.2800])
WALL_MOUNT_QUAT = np.array([0.7071068, 0.0, 0.7071068, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # fingers open in X

# Franka joint limits
JOINT_LIMITS_LOWER = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Link radius for collision check
LINK_RADIUS = 0.08
MIN_LINK_CLEARANCE = 2 * LINK_RADIUS + 0.04  # 0.20m

# Flange to EE offset
FLANGE_TO_EE = 0.1123

def compute_joint_margin(joints):
    """Compute minimum distance to joint limits in degrees."""
    margin_lower = joints - JOINT_LIMITS_LOWER
    margin_upper = JOINT_LIMITS_UPPER - joints
    margin_rad = np.minimum(margin_lower, margin_upper).min()
    return np.degrees(margin_rad)

def compute_all_joint_positions(joints, base_pos, base_quat):
    """Compute positions of all joints using FK."""
    positions = [base_pos.copy()]

    # Get EE transformation in robot frame
    T_ee = forward_kinematics(joints)
    ee_local = T_ee[:3, 3]

    # Base rotation (wall mount)
    w, x, y, z = base_quat
    R_base = np.array([
        [1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
        [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
        [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]
    ])

    # Transform EE to world frame
    ee_pos = base_pos + R_base @ ee_local

    # Interpolate intermediate joint positions (simplified)
    for i in range(1, 8):
        t = i / 8.0
        p = base_pos + t * (ee_pos - base_pos)
        positions.append(p)

    positions.append(ee_pos)
    return positions

def check_arm_collision(left_positions, right_positions, min_clearance=MIN_LINK_CLEARANCE):
    """Check collision between arm links."""
    min_dist = float('inf')
    for lp in left_positions[1:]:  # Skip base
        for rp in right_positions[1:]:
            dist = np.linalg.norm(lp - rp)
            min_dist = min(min_dist, dist)
    return min_dist >= min_clearance, min_dist

def verify_phase(phase_name, left_target, right_target):
    """Verify IK for a single phase."""
    # Solve IK for left arm
    left_success, left_joints, left_margin = solve_ik_best(
        left_target, ROBOT_LEFT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=30
    )

    # Solve IK for right arm
    right_success, right_joints, right_margin = solve_ik_best(
        right_target, ROBOT_RIGHT_BASE, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
        q7_range=(-2.8, 2.8), q7_steps=30
    )

    if not left_success or not right_success:
        return {
            'phase': phase_name,
            'success': False,
            'left_success': left_success,
            'right_success': right_success,
            'margin': 0.0,
            'clearance': 0.0,
            'collision_free': False
        }

    # Compute margins
    left_margin_deg = compute_joint_margin(left_joints)
    right_margin_deg = compute_joint_margin(right_joints)
    min_margin = min(left_margin_deg, right_margin_deg)

    # Compute collision
    left_positions = compute_all_joint_positions(left_joints, ROBOT_LEFT_BASE, WALL_MOUNT_QUAT)
    right_positions = compute_all_joint_positions(right_joints, ROBOT_RIGHT_BASE, WALL_MOUNT_QUAT)
    collision_free, clearance = check_arm_collision(left_positions, right_positions)

    return {
        'phase': phase_name,
        'success': True,
        'left_success': True,
        'right_success': True,
        'left_margin': left_margin_deg,
        'right_margin': right_margin_deg,
        'margin': min_margin,
        'clearance': clearance,
        'collision_free': collision_free,
        'left_joints': left_joints,
        'right_joints': right_joints
    }

def main():
    print("=" * 60)
    print("CABLE_Z = 0.77 IK Verification")
    print("=" * 60)
    print(f"\nRobot Configuration:")
    print(f"  Left Base:  {ROBOT_LEFT_BASE}")
    print(f"  Right Base: {ROBOT_RIGHT_BASE}")
    print()

    # Original waypoints (CABLE_Z = 0.755)
    original_waypoints = {
        'Phase1': {'left': np.array([0.30, -0.285, 0.905]), 'right': np.array([0.30, +0.285, 0.905])},
        'Phase2': {'left': np.array([0.30, -0.285, 0.755]), 'right': np.array([0.30, +0.285, 0.755])},
        'Phase3': {'left': np.array([0.30, -0.285, 0.90]), 'right': np.array([0.30, +0.285, 0.90])},
        'Phase4': {'left': np.array([0.25, -0.15, 1.00]), 'right': np.array([0.25, +0.15, 1.00])},
        'Phase5': {'left': np.array([0.20, -0.25, 0.80]), 'right': np.array([0.20, 0.00, 0.80])},
    }

    # New waypoints (CABLE_Z = 0.77, +1.5cm for Phase 1-2)
    new_waypoints = {
        'Phase1': {'left': np.array([0.30, -0.285, 0.920]), 'right': np.array([0.30, +0.285, 0.920])},
        'Phase2': {'left': np.array([0.30, -0.285, 0.770]), 'right': np.array([0.30, +0.285, 0.770])},
        'Phase3': {'left': np.array([0.30, -0.285, 0.90]), 'right': np.array([0.30, +0.285, 0.90])},
        'Phase4': {'left': np.array([0.25, -0.15, 1.00]), 'right': np.array([0.25, +0.15, 1.00])},
        'Phase5': {'left': np.array([0.20, -0.25, 0.80]), 'right': np.array([0.20, 0.00, 0.80])},
    }

    # Test original configuration
    print("=" * 60)
    print("Original Configuration (CABLE_Z = 0.755)")
    print("=" * 60)

    original_results = []
    for phase_name, targets in original_waypoints.items():
        result = verify_phase(phase_name, targets['left'], targets['right'])
        original_results.append(result)

        status = "✓" if result['success'] and result['collision_free'] else "✗"
        print(f"{status} {phase_name}: margin={result['margin']:.1f}°, clearance={result['clearance']*100:.1f}cm")

    original_min_margin = min(r['margin'] for r in original_results if r['success'])
    original_min_clearance = min(r['clearance'] for r in original_results if r['success'])

    print(f"\n  Worst-case margin: {original_min_margin:.1f}°")
    print(f"  Min clearance: {original_min_clearance*100:.1f}cm")

    # Test new configuration
    print()
    print("=" * 60)
    print("New Configuration (CABLE_Z = 0.77)")
    print("=" * 60)

    new_results = []
    for phase_name, targets in new_waypoints.items():
        result = verify_phase(phase_name, targets['left'], targets['right'])
        new_results.append(result)

        status = "✓" if result['success'] and result['collision_free'] else "✗"
        print(f"{status} {phase_name}: margin={result['margin']:.1f}°, clearance={result['clearance']*100:.1f}cm")

    new_min_margin = min(r['margin'] for r in new_results if r['success'])
    new_min_clearance = min(r['clearance'] for r in new_results if r['success'])

    print(f"\n  Worst-case margin: {new_min_margin:.1f}°")
    print(f"  Min clearance: {new_min_clearance*100:.1f}cm")

    # Comparison
    print()
    print("=" * 60)
    print("Comparison")
    print("=" * 60)
    print(f"{'Phase':<10} {'Original':<12} {'New (Z+1.5cm)':<12} {'Delta':<10}")
    print("-" * 44)

    for orig, new in zip(original_results, new_results):
        if orig['success'] and new['success']:
            delta = new['margin'] - orig['margin']
            sign = "+" if delta >= 0 else ""
            print(f"{orig['phase']:<10} {orig['margin']:>8.1f}°    {new['margin']:>8.1f}°    {sign}{delta:.1f}°")

    print("-" * 44)
    delta_margin = new_min_margin - original_min_margin
    sign = "+" if delta_margin >= 0 else ""
    print(f"{'Worst':<10} {original_min_margin:>8.1f}°    {new_min_margin:>8.1f}°    {sign}{delta_margin:.1f}°")

    # Conclusion
    print()
    print("=" * 60)
    print("Conclusion")
    print("=" * 60)

    all_success = all(r['success'] and r['collision_free'] for r in new_results)
    margin_ok = new_min_margin >= 20.0

    if all_success and margin_ok:
        print("✅ CABLE_Z = 0.77 is FEASIBLE")
        print(f"   - All phases have valid IK solutions")
        print(f"   - Worst-case margin: {new_min_margin:.1f}° (>= 20°)")
        print(f"   - All phases are collision-free")
    else:
        print("❌ CABLE_Z = 0.77 has issues:")
        if not all_success:
            for r in new_results:
                if not r['success']:
                    print(f"   - {r['phase']}: IK failed")
                elif not r['collision_free']:
                    print(f"   - {r['phase']}: Collision detected")
        if not margin_ok:
            print(f"   - Margin too low: {new_min_margin:.1f}° (< 20°)")

if __name__ == "__main__":
    main()
