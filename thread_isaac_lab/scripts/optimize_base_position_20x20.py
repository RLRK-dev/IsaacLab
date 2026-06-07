#!/usr/bin/env python3
"""
Robot Base Position Optimization (20^4 patterns)

Grid search for optimal robot base positions that maximize joint margins
across all waypoints (Phase 1-5).

Search space:
  Base X: [0.35, 0.55] step=0.0105 (20 points)
  Base Y_left: [-0.50, -0.30] step=0.0105 (20 points)
  Base Y_right: [+0.10, +0.30] step=0.0105 (20 points)
  Base Z: [1.0, 2.0] step=0.0526 (20 points)

Total: 20^4 = 160,000 configurations x 5 waypoints x 2 arms
     = 1,600,000 IK evaluations

Evaluation metric: Maximize the minimum joint margin across all waypoints
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

# ============================================================
# Constants
# ============================================================

# Joint limits (radians)
JOINT_LIMITS = {
    'joint1': (-2.8973, 2.8973),
    'joint2': (-1.7628, 1.7628),  # Most constrained: +/-101 deg
    'joint3': (-2.8973, 2.8973),
    'joint4': (-3.0718, -0.0698),  # -176 to -4 deg
    'joint5': (-2.8973, 2.8973),
    'joint6': (-0.0175, 3.7525),   # -1 to 215 deg
    'joint7': (-2.8973, 2.8973),
}

# Wall mount quaternion (Y+90 deg)
WALL_MOUNT_QUAT = (0.7071, 0.0, 0.7071, 0.0)  # wxyz

# Panda DH Parameters
PANDA_DH = {
    1: (0,      0.333,  0,        0),
    2: (0,      0,     -np.pi/2,  0),
    3: (0,      0.316,  np.pi/2,  0),
    4: (0.0825, 0,      np.pi/2,  0),
    5: (-0.0825, 0.384, -np.pi/2, 0),
    6: (0,      0,      np.pi/2,  0),
    7: (0.088,  0,      np.pi/2,  0),
}
FLANGE_TO_EE = 0.1123

# ============================================================
# Search Parameters (20 points each)
# ============================================================

# Base X: [0.35, 0.55] with 20 points
BASE_X_MIN, BASE_X_MAX = 0.35, 0.55
BASE_X_POINTS = 20

# Base Y left: [-0.50, -0.30] with 20 points
BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX = -0.50, -0.30
BASE_Y_LEFT_POINTS = 20

# Base Y right: [+0.10, +0.30] with 20 points
BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX = 0.10, 0.30
BASE_Y_RIGHT_POINTS = 20

# Base Z: [1.0, 2.0] with 20 points
BASE_Z_MIN, BASE_Z_MAX = 1.0, 2.0
BASE_Z_POINTS = 20

# Generate grids
BASE_X_VALUES = np.linspace(BASE_X_MIN, BASE_X_MAX, BASE_X_POINTS)
BASE_Y_LEFT_VALUES = np.linspace(BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX, BASE_Y_LEFT_POINTS)
BASE_Y_RIGHT_VALUES = np.linspace(BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX, BASE_Y_RIGHT_POINTS)
BASE_Z_VALUES = np.linspace(BASE_Z_MIN, BASE_Z_MAX, BASE_Z_POINTS)

# ============================================================
# Waypoints (Phase 1-5)
# ============================================================

# EE target positions for each phase
# Left arm targets (Y < 0), Right arm targets (Y > 0)
WAYPOINTS = {
    'Phase1': {
        'left': (0.30, -0.285, 0.905),   # Cable hover
        'right': (0.30, +0.285, 0.905),
    },
    'Phase2': {
        'left': (0.30, -0.285, 0.755),   # Cable grasp
        'right': (0.30, +0.285, 0.755),
    },
    'Phase3': {
        'left': (0.30, -0.285, 0.90),    # Lift
        'right': (0.30, +0.285, 0.90),
    },
    'Phase4': {
        'left': (0.25, -0.15, 1.00),     # Transport to hook
        'right': (0.25, +0.15, 1.00),
    },
    'Phase5': {
        'left': (0.20, -0.10, 0.85),     # Initial/Ready
        'right': (0.20, +0.10, 0.85),
    },
}


# ============================================================
# Helper Functions
# ============================================================

def dh_transform(a, d, alpha, theta):
    """Modified DH transformation matrix"""
    ct, st = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st, 0, a],
        [st*ca, ct*ca, -sa, -d*sa],
        [st*sa, ct*sa, ca, d*ca],
        [0, 0, 0, 1]
    ])


def forward_kinematics(joint_angles, base_pos, base_quat):
    """Compute EE position from joint angles with base transformation"""
    T = np.eye(4)
    r = R.from_quat([base_quat[1], base_quat[2], base_quat[3], base_quat[0]])
    T[:3, :3] = r.as_matrix()
    T[:3, 3] = base_pos

    for i in range(1, 8):
        a, d, alpha, theta_offset = PANDA_DH[i]
        theta = joint_angles[i-1] + theta_offset
        T = T @ dh_transform(a, d, alpha, theta)

    T_ee = np.eye(4)
    T_ee[2, 3] = FLANGE_TO_EE
    T = T @ T_ee

    return T[:3, 3]


def compute_joint_margins(joint_angles):
    """Compute minimum margin from joint limits (in degrees)"""
    margins = []
    for i, name in enumerate(['joint1', 'joint2', 'joint3', 'joint4',
                              'joint5', 'joint6', 'joint7']):
        angle = joint_angles[i]
        limit_min, limit_max = JOINT_LIMITS[name]
        margin_to_min = abs(angle - limit_min)
        margin_to_max = abs(limit_max - angle)
        margin = min(margin_to_min, margin_to_max)
        margins.append(np.degrees(margin))
    return min(margins), margins


def solve_ik_numerical(target_pos, base_pos, base_quat,
                       initial_joints=None, max_iter=150, tol=0.003):
    """
    Numerical IK solver using gradient descent with damped least squares

    Returns:
        success: bool
        joint_angles: np.ndarray (7,) or None
        min_margin_deg: float (minimum joint margin in degrees)
    """
    if initial_joints is None:
        initial_joints = np.array([0, -0.5, 0, -1.5, 0, 1.5, 0.785])

    joints = initial_joints.copy()
    learning_rate = 0.15
    momentum = 0.7
    velocity = np.zeros(7)

    best_joints = joints.copy()
    best_error = float('inf')

    for _ in range(max_iter):
        ee_pos = forward_kinematics(joints, base_pos, base_quat)
        error = target_pos - ee_pos
        error_norm = np.linalg.norm(error)

        if error_norm < best_error:
            best_error = error_norm
            best_joints = joints.copy()

        if error_norm < tol:
            break

        # Numerical Jacobian
        J = np.zeros((3, 7))
        delta = 0.001
        for i in range(7):
            joints_plus = joints.copy()
            joints_plus[i] += delta
            ee_plus = forward_kinematics(joints_plus, base_pos, base_quat)
            J[:, i] = (ee_plus - ee_pos) / delta

        # Damped least squares
        lambda_dls = 0.1
        JJT = J @ J.T + lambda_dls * np.eye(3)
        delta_q = J.T @ np.linalg.solve(JJT, error)

        velocity = momentum * velocity + learning_rate * delta_q
        joints = joints + velocity

        # Apply joint limits
        for i, name in enumerate(['joint1', 'joint2', 'joint3', 'joint4',
                                  'joint5', 'joint6', 'joint7']):
            limit_min, limit_max = JOINT_LIMITS[name]
            joints[i] = np.clip(joints[i], limit_min, limit_max)

    # Final evaluation
    ee_pos = forward_kinematics(best_joints, base_pos, base_quat)
    final_error = np.linalg.norm(target_pos - ee_pos)
    success = final_error < tol

    if success:
        min_margin, _ = compute_joint_margins(best_joints)
        return True, best_joints, min_margin
    else:
        return False, None, 0.0


@dataclass
class ConfigResult:
    """Result for a single configuration"""
    base_x: float
    base_y_left: float
    base_y_right: float
    base_z: float
    all_success: bool
    min_margin_deg: float
    phase_margins: Dict[str, Tuple[float, float]]  # phase -> (left_margin, right_margin)


def evaluate_configuration(base_x: float, base_y_left: float,
                          base_y_right: float, base_z: float) -> ConfigResult:
    """
    Evaluate a single robot base configuration across all waypoints.

    Returns ConfigResult with worst-case margin.
    """
    left_base = (base_x, base_y_left, base_z)
    right_base = (base_x, base_y_right, base_z)

    all_success = True
    min_margin = float('inf')
    phase_margins = {}

    for phase_name, targets in WAYPOINTS.items():
        # Left arm
        left_target = np.array(targets['left'])
        left_success, _, left_margin = solve_ik_numerical(
            left_target, left_base, WALL_MOUNT_QUAT
        )

        # Right arm
        right_target = np.array(targets['right'])
        right_success, _, right_margin = solve_ik_numerical(
            right_target, right_base, WALL_MOUNT_QUAT
        )

        if not left_success or not right_success:
            all_success = False
            phase_margins[phase_name] = (left_margin if left_success else 0.0,
                                         right_margin if right_success else 0.0)
            min_margin = 0.0
        else:
            phase_margins[phase_name] = (left_margin, right_margin)
            min_margin = min(min_margin, left_margin, right_margin)

    return ConfigResult(
        base_x=base_x,
        base_y_left=base_y_left,
        base_y_right=base_y_right,
        base_z=base_z,
        all_success=all_success,
        min_margin_deg=min_margin if all_success else 0.0,
        phase_margins=phase_margins,
    )


def evaluate_batch(args):
    """Evaluate a batch of configurations (for parallel processing)"""
    configs = args
    results = []
    for base_x, base_y_left, base_y_right, base_z in configs:
        result = evaluate_configuration(base_x, base_y_left, base_y_right, base_z)
        results.append(result)
    return results


def run_optimization(parallel=True, num_workers=None):
    """
    Run the full grid search optimization.
    """
    print("=" * 70)
    print("Robot Base Position Optimization (20^4 Grid Search)")
    print("=" * 70)

    # Generate all configurations
    total_configs = BASE_X_POINTS * BASE_Y_LEFT_POINTS * BASE_Y_RIGHT_POINTS * BASE_Z_POINTS
    print(f"\nSearch space:")
    print(f"  Base X: [{BASE_X_MIN:.2f}, {BASE_X_MAX:.2f}] ({BASE_X_POINTS} points)")
    print(f"  Base Y_left: [{BASE_Y_LEFT_MIN:.2f}, {BASE_Y_LEFT_MAX:.2f}] ({BASE_Y_LEFT_POINTS} points)")
    print(f"  Base Y_right: [{BASE_Y_RIGHT_MIN:.2f}, {BASE_Y_RIGHT_MAX:.2f}] ({BASE_Y_RIGHT_POINTS} points)")
    print(f"  Base Z: [{BASE_Z_MIN:.2f}, {BASE_Z_MAX:.2f}] ({BASE_Z_POINTS} points)")
    print(f"  Total configurations: {total_configs:,}")
    print(f"  IK evaluations: {total_configs * 5 * 2:,} (5 phases x 2 arms)")

    print(f"\nWaypoints to evaluate:")
    for phase, targets in WAYPOINTS.items():
        print(f"  {phase}: Left={targets['left']}, Right={targets['right']}")

    # Generate configuration list
    configs = []
    for base_x in BASE_X_VALUES:
        for base_y_left in BASE_Y_LEFT_VALUES:
            for base_y_right in BASE_Y_RIGHT_VALUES:
                for base_z in BASE_Z_VALUES:
                    configs.append((base_x, base_y_left, base_y_right, base_z))

    print(f"\nStarting optimization...")
    start_time = time.time()

    results = []

    if parallel and num_workers != 1:
        # Parallel execution
        if num_workers is None:
            num_workers = max(1, mp.cpu_count() - 2)

        batch_size = max(100, len(configs) // (num_workers * 10))
        batches = [configs[i:i+batch_size] for i in range(0, len(configs), batch_size)]

        print(f"  Using {num_workers} workers, {len(batches)} batches of ~{batch_size}")

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            batch_results = list(executor.map(evaluate_batch, batches))
            for batch in batch_results:
                results.extend(batch)

    else:
        # Sequential execution with progress
        for i, config in enumerate(configs):
            result = evaluate_configuration(*config)
            results.append(result)

            if (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (len(configs) - i - 1) / rate
                print(f"  Progress: {i+1:,}/{len(configs):,} "
                      f"({100*(i+1)/len(configs):.1f}%) "
                      f"ETA: {remaining:.0f}s")

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f}s ({len(configs)/elapsed:.0f} configs/s)")

    return results


def analyze_and_report(results: List[ConfigResult], output_dir: Path = None):
    """
    Analyze results and generate report.
    """
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    # Filter successful configurations
    successful = [r for r in results if r.all_success]
    print(f"\nSuccessful configurations: {len(successful):,} / {len(results):,} "
          f"({100*len(successful)/len(results):.1f}%)")

    if not successful:
        print("\n[ERROR] No successful configuration found!")
        # Show best partial results
        partial = sorted(results, key=lambda x: sum(
            m[0] + m[1] for m in x.phase_margins.values()
        ), reverse=True)[:10]

        print("\nBest partial results:")
        for i, r in enumerate(partial):
            print(f"\n  #{i+1}: X={r.base_x:.3f}, Y_L={r.base_y_left:.3f}, "
                  f"Y_R={r.base_y_right:.3f}, Z={r.base_z:.3f}")
            for phase, (lm, rm) in r.phase_margins.items():
                status = "OK" if lm > 0 and rm > 0 else "FAIL"
                print(f"      {phase}: L={lm:.1f}, R={rm:.1f} [{status}]")
        return results, None

    # Sort by minimum margin
    ranked = sorted(successful, key=lambda x: x.min_margin_deg, reverse=True)

    # Top 10 by worst-case margin
    print("\n" + "-" * 50)
    print("TOP 10 BY MINIMUM JOINT MARGIN (worst-case optimal)")
    print("-" * 50)

    for i, r in enumerate(ranked[:10]):
        print(f"\n#{i+1}: X={r.base_x:.4f}, Y_L={r.base_y_left:.4f}, "
              f"Y_R={r.base_y_right:.4f}, Z={r.base_z:.4f}")
        print(f"    Min margin: {r.min_margin_deg:.2f} deg")
        for phase, (lm, rm) in r.phase_margins.items():
            print(f"    {phase}: L={lm:.1f} deg, R={rm:.1f} deg")

    # Save results
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON summary
        summary = {
            "search_parameters": {
                "base_x_range": [BASE_X_MIN, BASE_X_MAX],
                "base_y_left_range": [BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX],
                "base_y_right_range": [BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX],
                "base_z_range": [BASE_Z_MIN, BASE_Z_MAX],
                "points_per_dim": 20,
                "total_configs": len(results),
            },
            "waypoints": {k: {"left": v["left"], "right": v["right"]}
                         for k, v in WAYPOINTS.items()},
            "results_summary": {
                "total_tested": len(results),
                "successful": len(successful),
                "success_rate": f"{100*len(successful)/len(results):.1f}%",
            },
            "top_configurations": [
                {
                    "rank": i+1,
                    "base_x": r.base_x,
                    "base_y_left": r.base_y_left,
                    "base_y_right": r.base_y_right,
                    "base_z": r.base_z,
                    "min_margin_deg": r.min_margin_deg,
                    "phase_margins": {k: {"left": v[0], "right": v[1]}
                                     for k, v in r.phase_margins.items()},
                }
                for i, r in enumerate(ranked[:20])
            ],
            "best_configuration": {
                "base_x": ranked[0].base_x,
                "base_y_left": ranked[0].base_y_left,
                "base_y_right": ranked[0].base_y_right,
                "base_z": ranked[0].base_z,
                "min_margin_deg": ranked[0].min_margin_deg,
            } if ranked else None,
        }

        json_path = output_dir / "optimization_results.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nSaved results to: {json_path}")

    # Final recommendation
    print("\n" + "=" * 70)
    print("FINAL RECOMMENDATION")
    print("=" * 70)

    if ranked:
        best = ranked[0]
        print(f"\nOptimal Robot Base Positions:")
        print(f"  Left arm:  X={best.base_x:.4f}, Y={best.base_y_left:.4f}, Z={best.base_z:.4f}")
        print(f"  Right arm: X={best.base_x:.4f}, Y={best.base_y_right:.4f}, Z={best.base_z:.4f}")
        print(f"\nMinimum joint margin: {best.min_margin_deg:.2f} deg")
        print(f"\nMargins per phase:")
        for phase, (lm, rm) in best.phase_margins.items():
            print(f"  {phase}: Left={lm:.1f} deg, Right={rm:.1f} deg")

        print(f"\nUpdate task_config.py:")
        print(f"  ROBOT_LEFT_BASE = ({best.base_x:.4f}, {best.base_y_left:.4f}, {best.base_z:.4f})")
        print(f"  ROBOT_RIGHT_BASE = ({best.base_x:.4f}, {best.base_y_right:.4f}, {best.base_z:.4f})")

    return results, ranked


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Robot base position optimization")
    parser.add_argument("--sequential", action="store_true",
                        help="Run sequentially (no parallelization)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers")
    parser.add_argument("--output", type=str, default="data/base_optimization",
                        help="Output directory")
    args = parser.parse_args()

    # Run optimization
    results = run_optimization(
        parallel=not args.sequential,
        num_workers=args.workers
    )

    # Analyze and report
    output_dir = Path(args.output)
    analyze_and_report(results, output_dir)


if __name__ == "__main__":
    main()
