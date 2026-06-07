#!/usr/bin/env python3
"""
Robot Base Position Optimization - Refinement around optimal region

Based on coarse search result:
  Best: X=0.35, Y_L=-0.30, Y_R=0.10, Z=1.11

Refined search with 20 points in narrower range.

Parallelized with multiprocessing for 30x speedup.
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
import time
import json
from pathlib import Path
import sys
from multiprocessing import Pool, cpu_count
from functools import partial

# ============================================================
# Constants
# ============================================================

JOINT_LIMITS = np.array([
    [-2.8973, 2.8973],
    [-1.7628, 1.7628],
    [-2.8973, 2.8973],
    [-3.0718, -0.0698],
    [-2.8973, 2.8973],
    [-0.0175, 3.7525],
    [-2.8973, 2.8973],
])

_quat = (0.7071, 0.0, 0.7071, 0.0)
_rot = R.from_quat([_quat[1], _quat[2], _quat[3], _quat[0]])
BASE_ROT_MATRIX = _rot.as_matrix()

DH_A = np.array([0, 0, 0, 0.0825, -0.0825, 0, 0.088])
DH_D = np.array([0.333, 0, 0.316, 0, 0.384, 0, 0])
DH_ALPHA = np.array([0, -np.pi/2, np.pi/2, np.pi/2, -np.pi/2, np.pi/2, np.pi/2])
FLANGE_TO_EE = 0.1123

# Refined search grid (20 points in narrow range around optimal)
# Based on coarse result: X=0.35, Y_L=-0.30, Y_R=0.10, Z=1.11
N_POINTS = 20

# Narrow ranges around optimal
BASE_X = np.linspace(0.30, 0.40, N_POINTS)        # +/- 0.05 from 0.35
BASE_Y_LEFT = np.linspace(-0.35, -0.25, N_POINTS)  # +/- 0.05 from -0.30
BASE_Y_RIGHT = np.linspace(0.05, 0.15, N_POINTS)   # +/- 0.05 from 0.10
BASE_Z = np.linspace(1.0, 1.2, N_POINTS)           # +/- 0.1 from 1.11

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


def solve_ik(target, base_pos, max_iter=80, tol=0.003):
    joints = np.array([0, -0.5, 0, -1.5, 0, 1.5, 0.785])
    target = np.array(target)
    base_pos = np.array(base_pos)

    lr = 0.2
    for _ in range(max_iter):
        ee = forward_kinematics(joints, base_pos)
        error = target - ee
        if np.linalg.norm(error) < tol:
            return True, compute_margins(joints)

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
    """Evaluate a single configuration"""
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


def evaluate_config_tuple(params):
    """Wrapper for parallel execution - accepts (x, yl, yr, z) tuple"""
    x, yl, yr, z = params
    success, margin, phases = evaluate_config(x, yl, yr, z)
    return (x, yl, yr, z, success, margin, phases)


def main():
    print("=" * 70)
    print("Robot Base Position Optimization - Refined Search (20^4)")
    print("=" * 70)

    print(f"\nRefined search ranges:")
    print(f"  X:     [{BASE_X[0]:.2f}, {BASE_X[-1]:.2f}]")
    print(f"  Y_L:   [{BASE_Y_LEFT[0]:.2f}, {BASE_Y_LEFT[-1]:.2f}]")
    print(f"  Y_R:   [{BASE_Y_RIGHT[0]:.2f}, {BASE_Y_RIGHT[-1]:.2f}]")
    print(f"  Z:     [{BASE_Z[0]:.2f}, {BASE_Z[-1]:.2f}]")

    total = N_POINTS ** 4
    n_workers = cpu_count()
    print(f"\nTotal configurations: {total:,}")
    print(f"CPU cores available: {n_workers}")
    print(f"Using multiprocessing with {n_workers} workers")
    sys.stdout.flush()

    # Generate all configurations
    all_configs = []
    for x in BASE_X:
        for yl in BASE_Y_LEFT:
            for yr in BASE_Y_RIGHT:
                for z in BASE_Z:
                    all_configs.append((x, yl, yr, z))

    start_time = time.time()
    best_margin = 0
    best_config = None
    best_phases = None
    successful_count = 0

    # Store top 10
    top_results = []

    # Parallel execution with multiprocessing
    print(f"\nStarting parallel evaluation...")
    sys.stdout.flush()

    with Pool(processes=n_workers) as pool:
        # Use imap for progress tracking
        chunk_size = max(1, total // (n_workers * 10))
        results_iter = pool.imap(evaluate_config_tuple, all_configs, chunksize=chunk_size)

        for count, result in enumerate(results_iter, 1):
            x, yl, yr, z, success, margin, phases = result

            if success:
                successful_count += 1
                # Keep top 10
                top_results.append((margin, x, yl, yr, z, phases))
                top_results.sort(key=lambda r: -r[0])
                top_results = top_results[:10]

                if margin > best_margin:
                    best_margin = margin
                    best_config = (x, yl, yr, z)
                    best_phases = phases

            if count % 5000 == 0 or count == total:
                elapsed = time.time() - start_time
                rate = count / elapsed
                remaining = (total - count) / rate if count < total else 0
                print(f"Progress: {count:,}/{total:,} ({100*count/total:.1f}%) "
                      f"| Best: {best_margin:.1f} deg | Success: {successful_count} "
                      f"| Rate: {rate:.0f}/s | ETA: {remaining/60:.1f} min")
                sys.stdout.flush()

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Completed in {elapsed/60:.1f} min ({count/elapsed:.0f} configs/s)")
    print(f"Successful: {successful_count:,} / {total:,} ({100*successful_count/total:.1f}%)")

    if best_config:
        x, yl, yr, z = best_config
        print(f"\n{'='*70}")
        print("TOP 5 CONFIGURATIONS")
        print(f"{'='*70}")
        for i, (margin, rx, ryl, ryr, rz, rphases) in enumerate(top_results[:5]):
            print(f"\n#{i+1}: X={rx:.4f}, Y_L={ryl:.4f}, Y_R={ryr:.4f}, Z={rz:.4f}")
            print(f"     Min margin: {margin:.2f} deg")
            for name, (lm, rm) in rphases.items():
                print(f"     {name}: {lm:.1f} / {rm:.1f}")

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
        output_dir = Path("data/base_optimization_refined")
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {
            "grid_size": N_POINTS,
            "search_ranges": {
                "base_x": [float(BASE_X[0]), float(BASE_X[-1])],
                "base_y_left": [float(BASE_Y_LEFT[0]), float(BASE_Y_LEFT[-1])],
                "base_y_right": [float(BASE_Y_RIGHT[0]), float(BASE_Y_RIGHT[-1])],
                "base_z": [float(BASE_Z[0]), float(BASE_Z[-1])],
            },
            "total_tested": total,
            "successful": successful_count,
            "best_margin_deg": float(best_margin),
            "best_config": {
                "base_x": float(x), "base_y_left": float(yl),
                "base_y_right": float(yr), "base_z": float(z)
            },
            "phase_margins": {k: {"left": float(v[0]), "right": float(v[1])}
                             for k, v in best_phases.items()},
            "top_5": [
                {
                    "rank": i+1,
                    "margin_deg": float(m),
                    "config": {"x": float(rx), "y_l": float(ryl), "y_r": float(ryr), "z": float(rz)},
                }
                for i, (m, rx, ryl, ryr, rz, _) in enumerate(top_results[:5])
            ],
            "elapsed_minutes": elapsed / 60,
        }
        with open(output_dir / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_dir}/results.json")
    else:
        print("\n[ERROR] No successful configuration found!")


if __name__ == "__main__":
    main()
