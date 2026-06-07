#!/usr/bin/env python3
"""
Comprehensive Robot Base Position Optimization with Joint Angle Output

This script performs grid search optimization and then outputs all joint angles
for all phases in a format ready to copy-paste into task_config.py.

Usage:
    python comprehensive_optimization.py [OPTIONS]

Options:
    --sequential        Run without parallelization
    --workers N         Number of parallel workers
    --output DIR        Output directory (default: data/comprehensive_optimization)
    --quick             Use 10x10 grid for quick test
    --verbose           Show detailed progress

Output:
    After optimization, prints task_config.py compatible values:
    - ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE
    - LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS (Phase 1)
    - PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS
    - PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS
    - PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS
    - PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS
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
import argparse

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
# Search Parameters (configurable)
# ============================================================

# Default: 20 points each
DEFAULT_GRID_SIZE = 20
QUICK_GRID_SIZE = 10

# Base X: [0.30, 0.50]
BASE_X_MIN, BASE_X_MAX = 0.30, 0.50

# Base Y left: [-0.45, -0.25]
BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX = -0.45, -0.25

# Base Y right: [+0.15, +0.35]
BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX = 0.15, 0.35

# Base Z: [1.05, 1.25]
BASE_Z_MIN, BASE_Z_MAX = 1.05, 1.25

# ============================================================
# Waypoints (Phase 1-5) from task_config.py
# ============================================================

WAYPOINTS = {
    'Phase1': {
        'left': (0.30, -0.285, 0.905),   # Initial hover (15cm above cable)
        'right': (0.30, +0.285, 0.905),
    },
    'Phase2': {
        'left': (0.30, -0.285, 0.755),   # Grasp position (cable surface)
        'right': (0.30, +0.285, 0.755),
    },
    'Phase3': {
        'left': (0.30, -0.285, 0.90),    # Lift position
        'right': (0.30, +0.285, 0.90),
    },
    'Phase4': {
        'left': (0.25, -0.15, 1.00),     # Hook approach
        'right': (0.25, +0.15, 1.00),
    },
    'Phase5': {
        'left': (0.10, -0.20, 0.90),     # Cable placement
        'right': (0.10, +0.05, 0.90),
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
    margin_details = {}
    for i, name in enumerate(['joint1', 'joint2', 'joint3', 'joint4',
                              'joint5', 'joint6', 'joint7']):
        angle = joint_angles[i]
        limit_min, limit_max = JOINT_LIMITS[name]
        margin_to_min = abs(angle - limit_min)
        margin_to_max = abs(limit_max - angle)
        margin = min(margin_to_min, margin_to_max)
        margin_deg = np.degrees(margin)
        margins.append(margin_deg)
        margin_details[name] = margin_deg
    return min(margins), margins, margin_details


def solve_ik_numerical(target_pos, base_pos, base_quat,
                       initial_joints=None, max_iter=200, tol=0.003):
    """
    Numerical IK solver using gradient descent with damped least squares

    Returns:
        success: bool
        joint_angles: np.ndarray (7,) or None
        min_margin_deg: float (minimum joint margin in degrees)
        margin_details: dict with per-joint margins
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
        min_margin, margins, margin_details = compute_joint_margins(best_joints)
        return True, best_joints, min_margin, margin_details
    else:
        return False, None, 0.0, {}


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
    phase_joints: Dict[str, Dict[str, np.ndarray]]  # phase -> {'left': joints, 'right': joints}


def evaluate_configuration(base_x: float, base_y_left: float,
                          base_y_right: float, base_z: float) -> ConfigResult:
    """
    Evaluate a single robot base configuration across all waypoints.
    """
    left_base = (base_x, base_y_left, base_z)
    right_base = (base_x, base_y_right, base_z)

    all_success = True
    min_margin = float('inf')
    phase_margins = {}
    phase_joints = {}

    for phase_name, targets in WAYPOINTS.items():
        # Left arm
        left_target = np.array(targets['left'])
        left_success, left_joints, left_margin, _ = solve_ik_numerical(
            left_target, left_base, WALL_MOUNT_QUAT
        )

        # Right arm
        right_target = np.array(targets['right'])
        right_success, right_joints, right_margin, _ = solve_ik_numerical(
            right_target, right_base, WALL_MOUNT_QUAT
        )

        if not left_success or not right_success:
            all_success = False
            phase_margins[phase_name] = (left_margin if left_success else 0.0,
                                         right_margin if right_success else 0.0)
            phase_joints[phase_name] = {
                'left': left_joints,
                'right': right_joints
            }
            min_margin = 0.0
        else:
            phase_margins[phase_name] = (left_margin, right_margin)
            phase_joints[phase_name] = {
                'left': left_joints,
                'right': right_joints
            }
            min_margin = min(min_margin, left_margin, right_margin)

    return ConfigResult(
        base_x=base_x,
        base_y_left=base_y_left,
        base_y_right=base_y_right,
        base_z=base_z,
        all_success=all_success,
        min_margin_deg=min_margin if all_success else 0.0,
        phase_margins=phase_margins,
        phase_joints=phase_joints,
    )


def evaluate_batch(args):
    """Evaluate a batch of configurations (for parallel processing)"""
    configs = args
    results = []
    for base_x, base_y_left, base_y_right, base_z in configs:
        result = evaluate_configuration(base_x, base_y_left, base_y_right, base_z)
        results.append(result)
    return results


def run_optimization(grid_size=DEFAULT_GRID_SIZE, parallel=True, num_workers=None, verbose=False):
    """
    Run the full grid search optimization.
    """
    print("=" * 70)
    print("Comprehensive Robot Base Position Optimization")
    print("=" * 70)

    # Generate grids
    base_x_values = np.linspace(BASE_X_MIN, BASE_X_MAX, grid_size)
    base_y_left_values = np.linspace(BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX, grid_size)
    base_y_right_values = np.linspace(BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX, grid_size)
    base_z_values = np.linspace(BASE_Z_MIN, BASE_Z_MAX, grid_size)

    total_configs = grid_size ** 4

    print(f"\n[CHECK] Search space:")
    print(f"  Base X: [{BASE_X_MIN:.2f}, {BASE_X_MAX:.2f}] ({grid_size} points)")
    print(f"  Base Y_left: [{BASE_Y_LEFT_MIN:.2f}, {BASE_Y_LEFT_MAX:.2f}] ({grid_size} points)")
    print(f"  Base Y_right: [{BASE_Y_RIGHT_MIN:.2f}, {BASE_Y_RIGHT_MAX:.2f}] ({grid_size} points)")
    print(f"  Base Z: [{BASE_Z_MIN:.2f}, {BASE_Z_MAX:.2f}] ({grid_size} points)")
    print(f"  Total configurations: {total_configs:,}")
    print(f"  IK evaluations: {total_configs * 5 * 2:,} (5 phases x 2 arms)")

    print(f"\n[CHECK] Waypoints to evaluate:")
    for phase, targets in WAYPOINTS.items():
        print(f"  {phase}: Left={targets['left']}, Right={targets['right']}")

    # Generate configuration list
    configs = []
    for base_x in base_x_values:
        for base_y_left in base_y_left_values:
            for base_y_right in base_y_right_values:
                for base_z in base_z_values:
                    configs.append((base_x, base_y_left, base_y_right, base_z))

    print(f"\n[RUN] Starting optimization...")
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

            if verbose and (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (len(configs) - i - 1) / rate
                print(f"  Progress: {i+1:,}/{len(configs):,} "
                      f"({100*(i+1)/len(configs):.1f}%) "
                      f"ETA: {remaining:.0f}s")

    elapsed = time.time() - start_time
    print(f"\n[RESULT] Completed in {elapsed:.1f}s ({len(configs)/elapsed:.0f} configs/s)")

    return results


def format_joints_for_config(joints: np.ndarray, name: str) -> str:
    """Format joint angles for task_config.py"""
    lines = [f"{name} = ["]
    joint_names = [
        "panda_joint1", "panda_joint2", "panda_joint3", "panda_joint4",
        "panda_joint5", "panda_joint6", "panda_joint7"
    ]
    for i, (joint_name, angle) in enumerate(zip(joint_names, joints)):
        comma = "," if i < 6 else ""
        lines.append(f"    {angle:+.6f}{comma}  # {joint_name}: {np.degrees(angle):+.1f} deg")
    lines.append("]")
    return "\n".join(lines)


def output_task_config_values(best: ConfigResult):
    """
    Output all values in task_config.py compatible format
    """
    print("\n" + "=" * 70)
    print("VALUES FOR task_config.py")
    print("=" * 70)

    # Robot Base Positions
    print(f"""
# =============================================================================
# Robot Base Positions (Comprehensive optimization result)
# =============================================================================
# Optimization date: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Grid search: explored {DEFAULT_GRID_SIZE}^4 configurations
# Worst-case joint margin: {best.min_margin_deg:.1f} deg

ROBOT_LEFT_BASE = ({best.base_x:.4f}, {best.base_y_left:.4f}, {best.base_z:.4f})
ROBOT_RIGHT_BASE = ({best.base_x:.4f}, {best.base_y_right:.4f}, {best.base_z:.4f})

# Base rotation: Y+90 deg for wall-mount
ROBOT_BASE_QUAT_WXYZ = (0.7071, 0.0, 0.7071, 0.0)  # (w, x, y, z) for Isaac Sim
ROBOT_BASE_QUAT_XYZW = (0.0, 0.7071, 0.0, 0.7071)  # (x, y, z, w) for scipy
""")

    # Phase 1: Initial position (LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS)
    print("""
# =============================================================================
# Phase 1: Initial Joint Angles (hover position, 15cm above cable)
# =============================================================================
# EE Left:  (0.30, -0.285, 0.905)
# EE Right: (0.30, +0.285, 0.905)
""")
    phase1_left = best.phase_joints['Phase1']['left']
    phase1_right = best.phase_joints['Phase1']['right']
    print(format_joints_for_config(phase1_left, "LEFT_ARM_INIT_JOINTS"))
    print()
    print(format_joints_for_config(phase1_right, "RIGHT_ARM_INIT_JOINTS"))

    # Phase 2: Grasp position
    print("""

# =============================================================================
# Phase 2: Grasp Joint Angles (cable surface)
# =============================================================================
# EE Left:  (0.30, -0.285, 0.755)
# EE Right: (0.30, +0.285, 0.755)
""")
    phase2_left = best.phase_joints['Phase2']['left']
    phase2_right = best.phase_joints['Phase2']['right']
    print(format_joints_for_config(phase2_left, "PHASE2_LEFT_JOINTS"))
    print()
    print(format_joints_for_config(phase2_right, "PHASE2_RIGHT_JOINTS"))

    # Phase 3: Lift position
    print("""

# =============================================================================
# Phase 3: Lift Joint Angles (after grasp)
# =============================================================================
# EE Left:  (0.30, -0.285, 0.90)
# EE Right: (0.30, +0.285, 0.90)
""")
    phase3_left = best.phase_joints['Phase3']['left']
    phase3_right = best.phase_joints['Phase3']['right']
    print(format_joints_for_config(phase3_left, "PHASE3_LEFT_JOINTS"))
    print()
    print(format_joints_for_config(phase3_right, "PHASE3_RIGHT_JOINTS"))

    # Phase 4: Hook approach
    print("""

# =============================================================================
# Phase 4: Hook Approach Joint Angles
# =============================================================================
# EE Left:  (0.25, -0.15, 1.00)
# EE Right: (0.25, +0.15, 1.00)
""")
    phase4_left = best.phase_joints['Phase4']['left']
    phase4_right = best.phase_joints['Phase4']['right']
    print(format_joints_for_config(phase4_left, "PHASE4_LEFT_JOINTS"))
    print()
    print(format_joints_for_config(phase4_right, "PHASE4_RIGHT_JOINTS"))

    # Phase 5: Cable placement
    print("""

# =============================================================================
# Phase 5: Cable Placement Joint Angles
# =============================================================================
# EE Left:  (0.10, -0.20, 0.90)
# EE Right: (0.10, +0.05, 0.90)
""")
    phase5_left = best.phase_joints['Phase5']['left']
    phase5_right = best.phase_joints['Phase5']['right']
    print(format_joints_for_config(phase5_left, "PHASE5_LEFT_JOINTS"))
    print()
    print(format_joints_for_config(phase5_right, "PHASE5_RIGHT_JOINTS"))

    print("\n" + "=" * 70)
    print("END OF VALUES FOR task_config.py")
    print("=" * 70)


def analyze_and_report(results: List[ConfigResult], output_dir: Path = None):
    """
    Analyze results, generate report, and output task_config.py values.
    """
    print("\n" + "=" * 70)
    print("[RESULT] ANALYSIS RESULTS")
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
            print(f"\n  #{i+1}: X={r.base_x:.4f}, Y_L={r.base_y_left:.4f}, "
                  f"Y_R={r.base_y_right:.4f}, Z={r.base_z:.4f}")
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
            "optimization_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "search_parameters": {
                "base_x_range": [float(BASE_X_MIN), float(BASE_X_MAX)],
                "base_y_left_range": [float(BASE_Y_LEFT_MIN), float(BASE_Y_LEFT_MAX)],
                "base_y_right_range": [float(BASE_Y_RIGHT_MIN), float(BASE_Y_RIGHT_MAX)],
                "base_z_range": [float(BASE_Z_MIN), float(BASE_Z_MAX)],
                "total_configs": len(results),
            },
            "waypoints": {k: {"left": list(v["left"]), "right": list(v["right"])}
                         for k, v in WAYPOINTS.items()},
            "results_summary": {
                "total_tested": len(results),
                "successful": len(successful),
                "success_rate": f"{100*len(successful)/len(results):.1f}%",
            },
            "best_configuration": {
                "base_x": float(ranked[0].base_x),
                "base_y_left": float(ranked[0].base_y_left),
                "base_y_right": float(ranked[0].base_y_right),
                "base_z": float(ranked[0].base_z),
                "min_margin_deg": float(ranked[0].min_margin_deg),
                "phase_margins": {k: {"left": float(v[0]), "right": float(v[1])}
                                 for k, v in ranked[0].phase_margins.items()},
                "phase_joints": {
                    phase: {
                        "left": joints['left'].tolist() if joints['left'] is not None else None,
                        "right": joints['right'].tolist() if joints['right'] is not None else None,
                    }
                    for phase, joints in ranked[0].phase_joints.items()
                },
            } if ranked else None,
            "top_10_configurations": [
                {
                    "rank": i+1,
                    "base_x": float(r.base_x),
                    "base_y_left": float(r.base_y_left),
                    "base_y_right": float(r.base_y_right),
                    "base_z": float(r.base_z),
                    "min_margin_deg": float(r.min_margin_deg),
                }
                for i, r in enumerate(ranked[:10])
            ],
        }

        json_path = output_dir / "comprehensive_optimization_results.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n[RESULT] Saved JSON: {json_path}")

    # Final recommendation and task_config.py output
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

        # Output task_config.py compatible values
        output_task_config_values(best)

    return results, ranked


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive robot base position optimization with joint angle output"
    )
    parser.add_argument("--sequential", action="store_true",
                        help="Run sequentially (no parallelization)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers")
    parser.add_argument("--output", type=str, default="data/comprehensive_optimization",
                        help="Output directory")
    parser.add_argument("--quick", action="store_true",
                        help="Use 10x10 grid for quick test")
    parser.add_argument("--verbose", action="store_true",
                        help="Show detailed progress")
    args = parser.parse_args()

    grid_size = QUICK_GRID_SIZE if args.quick else DEFAULT_GRID_SIZE

    print(f"\n[TASK] Comprehensive Robot Base Position Optimization")
    print(f"  目的: 最適なロボット配置と全Phase関節角度を計算")
    print(f"  Grid size: {grid_size}^4 = {grid_size**4:,} configurations")

    # Run optimization
    results = run_optimization(
        grid_size=grid_size,
        parallel=not args.sequential,
        num_workers=args.workers,
        verbose=args.verbose
    )

    # Analyze, report, and output task_config.py values
    output_dir = Path(args.output)
    analyze_and_report(results, output_dir)

    print("\n[RESULT] Optimization complete!")
    print("  次: task_config.py に上記の値をコピペしてください")


if __name__ == "__main__":
    main()
