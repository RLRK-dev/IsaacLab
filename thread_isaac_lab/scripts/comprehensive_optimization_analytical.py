#!/usr/bin/env python3
"""
Comprehensive Robot Base Position Optimization with Analytical IK

Uses He & Liu's analytical IK for accurate joint margin calculation.
Supports parallel processing with 64 cores.

Usage:
    python comprehensive_optimization_analytical.py [OPTIONS]

Options:
    --workers N     Number of parallel workers (default: 64)
    --grid N        Grid size per dimension (default: 15)
    --quick         Use 10x10 grid for quick test
    --output DIR    Output directory

Output:
    Optimized robot base positions and joint angles for all phases.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import argparse

# Import analytical IK
from franka_analytical_ik import (
    solve_ik_best, compute_joint_margin, Q_MIN, Q_MAX
)

# ============================================================
# Constants
# ============================================================

# Wall mount quaternion (Y+90 deg)
WALL_MOUNT_QUAT = np.array([0.7071, 0.0, 0.7071, 0.0])  # wxyz

# Gripper pointing down (-Z direction), fingers open in X
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])  # wxyz

# ============================================================
# Search Parameters
# ============================================================

# Base X: [0.30, 0.45]
BASE_X_MIN, BASE_X_MAX = 0.30, 0.45

# Base Y left: [-0.40, -0.28]
BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX = -0.40, -0.28

# Base Y right: [+0.18, +0.30]
BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX = 0.18, 0.30

# Base Z: [1.10, 1.25]
BASE_Z_MIN, BASE_Z_MAX = 1.10, 1.25

# ============================================================
# Waypoints (Phase 1-5) from task_config.py
# ============================================================

WAYPOINTS = {
    'Phase1': {
        'left': np.array([0.30, -0.285, 0.905]),   # Initial hover
        'right': np.array([0.30, +0.285, 0.905]),
    },
    'Phase2': {
        'left': np.array([0.30, -0.285, 0.755]),   # Grasp
        'right': np.array([0.30, +0.285, 0.755]),
    },
    'Phase3': {
        'left': np.array([0.30, -0.285, 0.90]),    # Lift
        'right': np.array([0.30, +0.285, 0.90]),
    },
    'Phase4': {
        'left': np.array([0.25, -0.15, 1.00]),     # Hook approach
        'right': np.array([0.25, +0.15, 1.00]),
    },
    'Phase5': {
        'left': np.array([0.10, -0.20, 0.90]),     # Cable placement
        'right': np.array([0.10, +0.05, 0.90]),
    },
}


@dataclass
class ConfigResult:
    """Result for a single configuration"""
    base_x: float
    base_y_left: float
    base_y_right: float
    base_z: float
    all_success: bool
    min_margin_deg: float
    phase_margins: Dict[str, Tuple[float, float]]
    phase_joints: Dict[str, Dict[str, np.ndarray]]


def evaluate_configuration(config: Tuple[float, float, float, float]) -> ConfigResult:
    """
    Evaluate a single robot base configuration using analytical IK.
    """
    base_x, base_y_left, base_y_right, base_z = config

    left_base = np.array([base_x, base_y_left, base_z])
    right_base = np.array([base_x, base_y_right, base_z])

    all_success = True
    min_margin = float('inf')
    phase_margins = {}
    phase_joints = {}

    for phase_name, targets in WAYPOINTS.items():
        # Left arm
        left_success, left_joints, left_margin = solve_ik_best(
            targets['left'], left_base, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
            q7_range=(-2.5, 2.5), q7_steps=25
        )

        # Right arm
        right_success, right_joints, right_margin = solve_ik_best(
            targets['right'], right_base, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
            q7_range=(-2.5, 2.5), q7_steps=25
        )

        if not left_success or not right_success:
            all_success = False
            phase_margins[phase_name] = (
                left_margin if left_success else 0.0,
                right_margin if right_success else 0.0
            )
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


def evaluate_batch(configs: List[Tuple[float, float, float, float]]) -> List[ConfigResult]:
    """Evaluate a batch of configurations."""
    return [evaluate_configuration(cfg) for cfg in configs]


def run_optimization(grid_size: int = 15, num_workers: int = 64, verbose: bool = True):
    """
    Run the full grid search optimization with analytical IK.
    """
    print("=" * 70)
    print("Comprehensive Optimization with Analytical IK")
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
    print(f"  Parallel workers: {num_workers}")

    # Generate configuration list
    configs = []
    for base_x in base_x_values:
        for base_y_left in base_y_left_values:
            for base_y_right in base_y_right_values:
                for base_z in base_z_values:
                    configs.append((base_x, base_y_left, base_y_right, base_z))

    print(f"\n[RUN] Starting optimization with {num_workers} workers...")
    start_time = time.time()

    results = []

    # Split into batches
    batch_size = max(10, len(configs) // (num_workers * 4))
    batches = [configs[i:i+batch_size] for i in range(0, len(configs), batch_size)]

    print(f"  {len(batches)} batches of ~{batch_size} configurations")

    if num_workers > 1:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            completed = 0
            for batch_results in executor.map(evaluate_batch, batches):
                results.extend(batch_results)
                completed += len(batch_results)
                if verbose and completed % 1000 < batch_size:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    remaining = (len(configs) - completed) / rate if rate > 0 else 0
                    print(f"  Progress: {completed:,}/{len(configs):,} "
                          f"({100*completed/len(configs):.1f}%) "
                          f"ETA: {remaining:.0f}s")
    else:
        for i, cfg in enumerate(configs):
            results.append(evaluate_configuration(cfg))
            if verbose and (i + 1) % 100 == 0:
                print(f"  Progress: {i+1:,}/{len(configs):,}")

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
    """Output all values in task_config.py compatible format."""
    print("\n" + "=" * 70)
    print("VALUES FOR task_config.py")
    print("=" * 70)

    print(f"""
# =============================================================================
# Robot Base Positions (Analytical IK Optimization)
# =============================================================================
# Optimization date: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Method: He & Liu Analytical IK
# Worst-case joint margin: {best.min_margin_deg:.1f} deg

ROBOT_LEFT_BASE = ({best.base_x:.4f}, {best.base_y_left:.4f}, {best.base_z:.4f})
ROBOT_RIGHT_BASE = ({best.base_x:.4f}, {best.base_y_right:.4f}, {best.base_z:.4f})

# Base rotation: Y+90 deg for wall-mount
ROBOT_BASE_QUAT_WXYZ = (0.7071, 0.0, 0.7071, 0.0)
ROBOT_BASE_QUAT_XYZW = (0.0, 0.7071, 0.0, 0.7071)
""")

    # Output joint angles for each phase
    phase_configs = [
        ('Phase1', 'LEFT_ARM_INIT_JOINTS', 'RIGHT_ARM_INIT_JOINTS',
         'Initial (hover 15cm above cable)', '(0.30, -0.285, 0.905)', '(0.30, +0.285, 0.905)'),
        ('Phase2', 'PHASE2_LEFT_JOINTS', 'PHASE2_RIGHT_JOINTS',
         'Grasp (cable surface)', '(0.30, -0.285, 0.755)', '(0.30, +0.285, 0.755)'),
        ('Phase3', 'PHASE3_LEFT_JOINTS', 'PHASE3_RIGHT_JOINTS',
         'Lift', '(0.30, -0.285, 0.90)', '(0.30, +0.285, 0.90)'),
        ('Phase4', 'PHASE4_LEFT_JOINTS', 'PHASE4_RIGHT_JOINTS',
         'Hook approach', '(0.25, -0.15, 1.00)', '(0.25, +0.15, 1.00)'),
        ('Phase5', 'PHASE5_LEFT_JOINTS', 'PHASE5_RIGHT_JOINTS',
         'Cable placement', '(0.10, -0.20, 0.90)', '(0.10, +0.05, 0.90)'),
    ]

    for phase_key, left_name, right_name, desc, left_ee, right_ee in phase_configs:
        left_joints = best.phase_joints[phase_key]['left']
        right_joints = best.phase_joints[phase_key]['right']
        left_margin, right_margin = best.phase_margins[phase_key]

        print(f"""
# =============================================================================
# {phase_key}: {desc}
# =============================================================================
# EE Left:  {left_ee}  Margin: {left_margin:.1f} deg
# EE Right: {right_ee}  Margin: {right_margin:.1f} deg
""")
        if left_joints is not None:
            print(format_joints_for_config(left_joints, left_name))
            print()
        if right_joints is not None:
            print(format_joints_for_config(right_joints, right_name))

    print("\n" + "=" * 70)
    print("END OF VALUES FOR task_config.py")
    print("=" * 70)


def analyze_and_report(results: List[ConfigResult], output_dir: Path = None):
    """Analyze results and generate report."""
    print("\n" + "=" * 70)
    print("[RESULT] ANALYSIS RESULTS")
    print("=" * 70)

    # Filter successful configurations
    successful = [r for r in results if r.all_success]
    print(f"\nSuccessful configurations: {len(successful):,} / {len(results):,} "
          f"({100*len(successful)/len(results):.1f}%)")

    if not successful:
        print("\n[ERROR] No successful configuration found!")
        return results, None

    # Sort by minimum margin
    ranked = sorted(successful, key=lambda x: x.min_margin_deg, reverse=True)

    # Top 10
    print("\n" + "-" * 50)
    print("TOP 10 BY MINIMUM JOINT MARGIN")
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

        summary = {
            "optimization_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "method": "Analytical IK (He & Liu)",
            "search_parameters": {
                "base_x_range": [float(BASE_X_MIN), float(BASE_X_MAX)],
                "base_y_left_range": [float(BASE_Y_LEFT_MIN), float(BASE_Y_LEFT_MAX)],
                "base_y_right_range": [float(BASE_Y_RIGHT_MIN), float(BASE_Y_RIGHT_MAX)],
                "base_z_range": [float(BASE_Z_MIN), float(BASE_Z_MAX)],
                "total_configs": len(results),
            },
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
            } if ranked else None,
        }

        json_path = output_dir / "analytical_optimization_results.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n[RESULT] Saved JSON: {json_path}")

    # Output task_config.py values
    if ranked:
        output_task_config_values(ranked[0])

    return results, ranked


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive optimization with analytical IK"
    )
    parser.add_argument("--workers", type=int, default=64,
                        help="Number of parallel workers (default: 64)")
    parser.add_argument("--grid", type=int, default=15,
                        help="Grid size per dimension (default: 15)")
    parser.add_argument("--quick", action="store_true",
                        help="Use 10x10 grid for quick test")
    parser.add_argument("--output", type=str,
                        default="data/analytical_optimization",
                        help="Output directory")
    args = parser.parse_args()

    grid_size = 10 if args.quick else args.grid

    print(f"\n[TASK] Comprehensive Optimization with Analytical IK")
    print(f"  Grid: {grid_size}^4 = {grid_size**4:,} configurations")
    print(f"  Workers: {args.workers}")

    # Run optimization
    results = run_optimization(
        grid_size=grid_size,
        num_workers=args.workers,
        verbose=True
    )

    # Analyze and report
    output_dir = Path(args.output)
    analyze_and_report(results, output_dir)

    print("\n[RESULT] Optimization complete!")


if __name__ == "__main__":
    main()
