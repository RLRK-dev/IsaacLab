#!/usr/bin/env python3
"""
Robot Base Position Optimization (10^4 patterns) - Quick Search

Coarse grid search to find promising regions quickly.
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
import time
import json
from pathlib import Path
import sys

# ============================================================
# Constants
# ============================================================

JOINT_LIMITS = np.array([
    [-2.8973, 2.8973],   # joint1
    [-1.7628, 1.7628],   # joint2
    [-2.8973, 2.8973],   # joint3
    [-3.0718, -0.0698],  # joint4
    [-2.8973, 2.8973],   # joint5
    [-0.0175, 3.7525],   # joint6
    [-2.8973, 2.8973],   # joint7
])

# Precompute base rotation
_quat = (0.7071, 0.0, 0.7071, 0.0)
_rot = R.from_quat([_quat[1], _quat[2], _quat[3], _quat[0]])
BASE_ROT_MATRIX = _rot.as_matrix()

# DH parameters
DH_A = np.array([0, 0, 0, 0.0825, -0.0825, 0, 0.088])
DH_D = np.array([0.333, 0, 0.316, 0, 0.384, 0, 0])
DH_ALPHA = np.array([0, -np.pi/2, np.pi/2, np.pi/2, -np.pi/2, np.pi/2, np.pi/2])
FLANGE_TO_EE = 0.1123

# Coarse search grid (10 points each)
N_POINTS = 10
BASE_X = np.linspace(0.35, 0.55, N_POINTS)
BASE_Y_LEFT = np.linspace(-0.50, -0.30, N_POINTS)
BASE_Y_RIGHT = np.linspace(0.10, 0.30, N_POINTS)
BASE_Z = np.linspace(1.0, 2.0, N_POINTS)

# Waypoints
WAYPOINTS = [
    ('Phase1', (0.30, -0.285, 0.905), (0.30, 0.285, 0.905)),
    ('Phase2', (0.30, -0.285, 0.755), (0.30, 0.285, 0.755)),
    ('Phase3', (0.30, -0.285, 0.90), (0.30, 0.285, 0.90)),
    ('Phase4', (0.25, -0.15, 1.00), (0.25, 0.15, 1.00)),
    ('Phase5', (0.20, -0.10, 0.85), (0.20, 0.10, 0.85)),
]


def dh_transform(a, d, alpha, theta):
    ct, st = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st, 0, a],
        [st*ca, ct*ca, -sa, -d*sa],
        [st*sa, ct*sa, ca, d*ca],
        [0, 0, 0, 1]
    ])


def forward_kinematics(joints, base_pos):
    T = np.eye(4)
    T[:3, :3] = BASE_ROT_MATRIX
    T[:3, 3] = base_pos
    for i in range(7):
        T = T @ dh_transform(DH_A[i], DH_D[i], DH_ALPHA[i], joints[i])
    ee_pos = T[:3, 3] + T[:3, 2] * FLANGE_TO_EE
    return ee_pos


def compute_margins(joints):
    margins = np.minimum(
        joints - JOINT_LIMITS[:, 0],
        JOINT_LIMITS[:, 1] - joints
    )
    return np.min(np.degrees(margins))


def solve_ik(target, base_pos, max_iter=60, tol=0.005):
    joints = np.array([0, -0.5, 0, -1.5, 0, 1.5, 0.785])
    target = np.array(target)
    base_pos = np.array(base_pos)

    lr = 0.25
    for _ in range(max_iter):
        ee = forward_kinematics(joints, base_pos)
        error = target - ee
        if np.linalg.norm(error) < tol:
            return True, compute_margins(joints)

        # Numerical Jacobian
        J = np.zeros((3, 7))
        delta = 0.001
        for i in range(7):
            joints_p = joints.copy()
            joints_p[i] += delta
            J[:, i] = (forward_kinematics(joints_p, base_pos) - ee) / delta

        JJT = J @ J.T + 0.1 * np.eye(3)
        delta_q = J.T @ np.linalg.solve(JJT, error)
        joints = np.clip(joints + lr * delta_q, JOINT_LIMITS[:, 0], JOINT_LIMITS[:, 1])

    ee = forward_kinematics(joints, base_pos)
    if np.linalg.norm(target - ee) < tol:
        return True, compute_margins(joints)
    return False, 0.0


def evaluate_config(x, yl, yr, z):
    left_base = (x, yl, z)
    right_base = (x, yr, z)

    min_margin = float('inf')
    all_success = True
    phase_results = {}

    for name, left_target, right_target in WAYPOINTS:
        left_ok, left_margin = solve_ik(left_target, left_base)
        right_ok, right_margin = solve_ik(right_target, right_base)
        phase_results[name] = (left_margin, right_margin)

        if not left_ok or not right_ok:
            all_success = False
            min_margin = 0
        else:
            min_margin = min(min_margin, left_margin, right_margin)

    return all_success, min_margin, phase_results


def main():
    print("=" * 70)
    print("Robot Base Position Optimization (10^4 Coarse Grid)")
    print("=" * 70)

    total = N_POINTS ** 4
    print(f"\nSearch space: {total:,} configurations")
    print(f"Phases: {len(WAYPOINTS)} x 2 arms = {len(WAYPOINTS)*2} IK per config")
    sys.stdout.flush()

    start_time = time.time()
    best_margin = 0
    best_config = None
    best_phases = None
    successful_count = 0
    count = 0

    for x in BASE_X:
        for yl in BASE_Y_LEFT:
            for yr in BASE_Y_RIGHT:
                for z in BASE_Z:
                    count += 1
                    success, margin, phases = evaluate_config(x, yl, yr, z)

                    if success:
                        successful_count += 1
                        if margin > best_margin:
                            best_margin = margin
                            best_config = (x, yl, yr, z)
                            best_phases = phases

                    if count % 500 == 0:
                        elapsed = time.time() - start_time
                        rate = count / elapsed
                        remaining = (total - count) / rate
                        print(f"Progress: {count:,}/{total:,} ({100*count/total:.1f}%) "
                              f"| Best: {best_margin:.1f} deg | Success: {successful_count} "
                              f"| ETA: {remaining:.0f}s")
                        sys.stdout.flush()

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Completed in {elapsed:.1f}s ({count/elapsed:.0f} configs/s)")
    print(f"Successful: {successful_count:,} / {total:,} ({100*successful_count/total:.1f}%)")

    if best_config:
        x, yl, yr, z = best_config
        print(f"\n{'='*70}")
        print("BEST CONFIGURATION")
        print(f"{'='*70}")
        print(f"Base X:       {x:.4f}")
        print(f"Base Y_left:  {yl:.4f}")
        print(f"Base Y_right: {yr:.4f}")
        print(f"Base Z:       {z:.4f}")
        print(f"\nMin margin: {best_margin:.2f} deg")
        print(f"\nPhase margins (L/R deg):")
        for name, (lm, rm) in best_phases.items():
            print(f"  {name}: {lm:.1f} / {rm:.1f}")

        print(f"\n{'='*70}")
        print("UPDATE task_config.py:")
        print(f"{'='*70}")
        print(f"ROBOT_LEFT_BASE = ({x:.4f}, {yl:.4f}, {z:.4f})")
        print(f"ROBOT_RIGHT_BASE = ({x:.4f}, {yr:.4f}, {z:.4f})")

        # Save results
        output_dir = Path("data/base_optimization_10x10")
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {
            "grid_size": N_POINTS,
            "total_tested": total,
            "successful": successful_count,
            "best_margin_deg": float(best_margin),
            "best_config": {
                "base_x": float(x), "base_y_left": float(yl),
                "base_y_right": float(yr), "base_z": float(z)
            },
            "phase_margins": {k: {"left": float(v[0]), "right": float(v[1])}
                             for k, v in best_phases.items()},
            "elapsed_seconds": elapsed,
        }
        with open(output_dir / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_dir}/results.json")
    else:
        print("\n[ERROR] No successful configuration found!")


if __name__ == "__main__":
    main()
