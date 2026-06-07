#!/usr/bin/env python3
"""
Robot Base Position Optimization (20^4 patterns) - Fast Version

Optimized for speed using vectorized operations and reduced iterations.
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
    [-1.7628, 1.7628],   # joint2 - most constrained
    [-2.8973, 2.8973],   # joint3
    [-3.0718, -0.0698],  # joint4
    [-2.8973, 2.8973],   # joint5
    [-0.0175, 3.7525],   # joint6
    [-2.8973, 2.8973],   # joint7
])

WALL_MOUNT_QUAT = (0.7071, 0.0, 0.7071, 0.0)

# Precompute base rotation matrix
_quat = WALL_MOUNT_QUAT
_rot = R.from_quat([_quat[1], _quat[2], _quat[3], _quat[0]])
BASE_ROT_MATRIX = _rot.as_matrix()

# DH parameters as arrays for faster access
DH_A = np.array([0, 0, 0, 0.0825, -0.0825, 0, 0.088])
DH_D = np.array([0.333, 0, 0.316, 0, 0.384, 0, 0])
DH_ALPHA = np.array([0, -np.pi/2, np.pi/2, np.pi/2, -np.pi/2, np.pi/2, np.pi/2])
FLANGE_TO_EE = 0.1123

# Search grids
BASE_X = np.linspace(0.35, 0.55, 20)
BASE_Y_LEFT = np.linspace(-0.50, -0.30, 20)
BASE_Y_RIGHT = np.linspace(0.10, 0.30, 20)
BASE_Z = np.linspace(1.0, 2.0, 20)

# Waypoints
WAYPOINTS = [
    # (name, left_target, right_target)
    ('Phase1', (0.30, -0.285, 0.905), (0.30, 0.285, 0.905)),
    ('Phase2', (0.30, -0.285, 0.755), (0.30, 0.285, 0.755)),
    ('Phase3', (0.30, -0.285, 0.90), (0.30, 0.285, 0.90)),
    ('Phase4', (0.25, -0.15, 1.00), (0.25, 0.15, 1.00)),
    ('Phase5', (0.20, -0.10, 0.85), (0.20, 0.10, 0.85)),
]


def dh_transform(a, d, alpha, theta):
    """Single DH transformation"""
    ct, st = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st, 0, a],
        [st*ca, ct*ca, -sa, -d*sa],
        [st*sa, ct*sa, ca, d*ca],
        [0, 0, 0, 1]
    ])


def forward_kinematics(joints, base_pos):
    """Compute EE position (using precomputed base rotation)"""
    T = np.eye(4)
    T[:3, :3] = BASE_ROT_MATRIX
    T[:3, 3] = base_pos

    for i in range(7):
        theta = joints[i]
        T = T @ dh_transform(DH_A[i], DH_D[i], DH_ALPHA[i], theta)

    # Add flange-to-EE offset
    ee_pos = T[:3, 3] + T[:3, 2] * FLANGE_TO_EE
    return ee_pos


def compute_margins(joints):
    """Compute minimum margin from all joint limits (degrees)"""
    margins = np.minimum(
        joints - JOINT_LIMITS[:, 0],
        JOINT_LIMITS[:, 1] - joints
    )
    return np.min(np.degrees(margins))


def solve_ik_fast(target, base_pos, max_iter=80, tol=0.005):
    """
    Fast numerical IK solver
    Returns: (success, min_margin_deg)
    """
    joints = np.array([0, -0.5, 0, -1.5, 0, 1.5, 0.785])
    target = np.array(target)
    base_pos = np.array(base_pos)

    lr = 0.2
    for _ in range(max_iter):
        ee = forward_kinematics(joints, base_pos)
        error = target - ee
        error_norm = np.linalg.norm(error)

        if error_norm < tol:
            margin = compute_margins(joints)
            return True, margin

        # Numerical Jacobian
        J = np.zeros((3, 7))
        delta = 0.001
        for i in range(7):
            joints_plus = joints.copy()
            joints_plus[i] += delta
            ee_plus = forward_kinematics(joints_plus, base_pos)
            J[:, i] = (ee_plus - ee) / delta

        # Damped least squares
        JJT = J @ J.T + 0.1 * np.eye(3)
        delta_q = J.T @ np.linalg.solve(JJT, error)
        joints = joints + lr * delta_q

        # Clip to limits
        joints = np.clip(joints, JOINT_LIMITS[:, 0], JOINT_LIMITS[:, 1])

    # Check final state
    ee = forward_kinematics(joints, base_pos)
    if np.linalg.norm(target - ee) < tol:
        return True, compute_margins(joints)
    return False, 0.0


def evaluate_config(base_x, base_y_left, base_y_right, base_z):
    """Evaluate a single configuration across all waypoints"""
    left_base = (base_x, base_y_left, base_z)
    right_base = (base_x, base_y_right, base_z)

    min_margin = float('inf')
    all_success = True
    phase_results = {}

    for name, left_target, right_target in WAYPOINTS:
        # Left arm
        left_ok, left_margin = solve_ik_fast(left_target, left_base)
        # Right arm
        right_ok, right_margin = solve_ik_fast(right_target, right_base)

        phase_results[name] = (left_margin, right_margin)

        if not left_ok or not right_ok:
            all_success = False
            min_margin = 0
        else:
            min_margin = min(min_margin, left_margin, right_margin)

    return all_success, min_margin, phase_results


def main():
    print("=" * 70)
    print("Robot Base Position Optimization (20^4 Grid Search)")
    print("=" * 70)

    total = 20 ** 4
    print(f"\nSearch space: {total:,} configurations")
    print(f"Waypoints: {len(WAYPOINTS)} phases x 2 arms = {len(WAYPOINTS)*2} IK per config")
    print(f"Total IK evaluations: {total * len(WAYPOINTS) * 2:,}")

    start_time = time.time()

    # Results storage
    best_margin = 0
    best_config = None
    best_phases = None
    successful_count = 0

    count = 0
    report_interval = 5000

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

                    if count % report_interval == 0:
                        elapsed = time.time() - start_time
                        rate = count / elapsed
                        remaining = (total - count) / rate
                        print(f"Progress: {count:,}/{total:,} ({100*count/total:.1f}%) "
                              f"| Best margin: {best_margin:.1f} deg "
                              f"| Success: {successful_count:,} "
                              f"| ETA: {remaining/60:.1f} min")
                        sys.stdout.flush()

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Completed in {elapsed:.1f}s ({count/elapsed:.0f} configs/s)")
    print(f"Successful configurations: {successful_count:,} / {total:,} ({100*successful_count/total:.1f}%)")

    if best_config:
        x, yl, yr, z = best_config
        print(f"\n{'='*70}")
        print("BEST CONFIGURATION")
        print(f"{'='*70}")
        print(f"Base X:      {x:.4f}")
        print(f"Base Y_left: {yl:.4f}")
        print(f"Base Y_right:{yr:.4f}")
        print(f"Base Z:      {z:.4f}")
        print(f"\nMinimum joint margin: {best_margin:.2f} deg")
        print(f"\nPhase margins (L/R):")
        for name, (lm, rm) in best_phases.items():
            print(f"  {name}: {lm:.1f} / {rm:.1f} deg")

        print(f"\n{'='*70}")
        print("UPDATE task_config.py:")
        print(f"{'='*70}")
        print(f"ROBOT_LEFT_BASE = ({x:.4f}, {yl:.4f}, {z:.4f})")
        print(f"ROBOT_RIGHT_BASE = ({x:.4f}, {yr:.4f}, {z:.4f})")

        # Save results
        output_dir = Path("data/base_optimization_20x20")
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "search_space": {
                "base_x": [float(BASE_X[0]), float(BASE_X[-1])],
                "base_y_left": [float(BASE_Y_LEFT[0]), float(BASE_Y_LEFT[-1])],
                "base_y_right": [float(BASE_Y_RIGHT[0]), float(BASE_Y_RIGHT[-1])],
                "base_z": [float(BASE_Z[0]), float(BASE_Z[-1])],
                "points_per_dim": 20,
            },
            "results": {
                "total_tested": total,
                "successful": successful_count,
                "best_margin_deg": float(best_margin),
                "best_config": {
                    "base_x": float(x),
                    "base_y_left": float(yl),
                    "base_y_right": float(yr),
                    "base_z": float(z),
                },
                "phase_margins": {k: {"left": float(v[0]), "right": float(v[1])}
                                  for k, v in best_phases.items()},
            },
            "elapsed_seconds": elapsed,
        }

        json_path = output_dir / "optimization_results.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {json_path}")
    else:
        print("\n[ERROR] No successful configuration found!")


if __name__ == "__main__":
    main()
