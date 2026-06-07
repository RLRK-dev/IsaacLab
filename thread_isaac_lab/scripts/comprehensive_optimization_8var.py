#!/usr/bin/env python3
"""
Comprehensive 8-Variable Optimization with Analytical IK

Optimizes both robot base positions AND Phase 5 EE positions:
- Base: X, Y_left, Y_right, Z (4 variables)
- Phase 5 EE: X, Y_left, Y_right, Z (4 variables)

Constraints:
- |ee5_yl - ee5_yr| > 0.15m (arm separation for collision avoidance)
- ee5_x < HOOK_X (EE must be in front of hook)

Usage:
    python comprehensive_optimization_8var.py [OPTIONS]

Options:
    --workers N     Number of parallel workers (default: 64)
    --grid N        Grid size per dimension (default: 8)
    --quick         Use 5x5 grid for quick test
    --output DIR    Output directory
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

# Hook position
HOOK_X = 0.25

# ============================================================
# Search Parameters - Base Position (4 variables)
# ============================================================

BASE_X_MIN, BASE_X_MAX = 0.28, 0.42
BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX = -0.42, -0.30
BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX = 0.20, 0.32
BASE_Z_MIN, BASE_Z_MAX = 1.12, 1.28

# ============================================================
# Search Parameters - Phase 5 EE Position (4 variables)
# ============================================================

EE5_X_MIN, EE5_X_MAX = 0.05, 0.20
EE5_YL_MIN, EE5_YL_MAX = -0.25, -0.05
EE5_YR_MIN, EE5_YR_MAX = 0.00, 0.20
EE5_Z_MIN, EE5_Z_MAX = 0.80, 0.95

# Constraints
MIN_ARM_SEPARATION = 0.15  # Minimum distance between left and right EE

# ============================================================
# Fixed Waypoints (Phase 1-4)
# ============================================================

FIXED_WAYPOINTS = {
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
}


@dataclass
class Config8Var:
    """8-variable configuration"""
    # Base position
    base_x: float
    base_y_left: float
    base_y_right: float
    base_z: float
    # Phase 5 EE position
    ee5_x: float
    ee5_y_left: float
    ee5_y_right: float
    ee5_z: float


@dataclass
class ConfigResult:
    """Result for a single configuration"""
    config: Config8Var
    all_success: bool
    min_margin_deg: float
    phase_margins: Dict[str, Tuple[float, float]]
    phase_joints: Dict[str, Dict[str, np.ndarray]]
    constraint_violated: bool = False


def check_constraints(config: Config8Var) -> bool:
    """
    Check if configuration satisfies constraints.

    Returns:
        True if constraints are satisfied, False otherwise
    """
    # Arm separation constraint
    arm_separation = abs(config.ee5_y_left - config.ee5_y_right)
    if arm_separation < MIN_ARM_SEPARATION:
        return False

    # Hook constraint: EE must be in front of hook
    if config.ee5_x >= HOOK_X:
        return False

    return True


def evaluate_configuration(config_tuple: Tuple) -> ConfigResult:
    """
    Evaluate a single 8-variable configuration using analytical IK.
    """
    (base_x, base_y_left, base_y_right, base_z,
     ee5_x, ee5_y_left, ee5_y_right, ee5_z) = config_tuple

    config = Config8Var(
        base_x=base_x, base_y_left=base_y_left,
        base_y_right=base_y_right, base_z=base_z,
        ee5_x=ee5_x, ee5_y_left=ee5_y_left,
        ee5_y_right=ee5_y_right, ee5_z=ee5_z
    )

    # Check constraints first
    if not check_constraints(config):
        return ConfigResult(
            config=config,
            all_success=False,
            min_margin_deg=0.0,
            phase_margins={},
            phase_joints={},
            constraint_violated=True
        )

    left_base = np.array([base_x, base_y_left, base_z])
    right_base = np.array([base_x, base_y_right, base_z])

    # Build waypoints including dynamic Phase 5
    waypoints = dict(FIXED_WAYPOINTS)
    waypoints['Phase5'] = {
        'left': np.array([ee5_x, ee5_y_left, ee5_z]),
        'right': np.array([ee5_x, ee5_y_right, ee5_z]),
    }

    all_success = True
    min_margin = float('inf')
    phase_margins = {}
    phase_joints = {}

    for phase_name, targets in waypoints.items():
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
        config=config,
        all_success=all_success,
        min_margin_deg=min_margin if all_success else 0.0,
        phase_margins=phase_margins,
        phase_joints=phase_joints,
        constraint_violated=False
    )


def evaluate_batch(configs: List[Tuple]) -> List[ConfigResult]:
    """Evaluate a batch of configurations."""
    return [evaluate_configuration(cfg) for cfg in configs]


def generate_configurations(grid_size: int) -> List[Tuple]:
    """
    Generate all 8-variable configurations.
    """
    base_x_values = np.linspace(BASE_X_MIN, BASE_X_MAX, grid_size)
    base_y_left_values = np.linspace(BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX, grid_size)
    base_y_right_values = np.linspace(BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX, grid_size)
    base_z_values = np.linspace(BASE_Z_MIN, BASE_Z_MAX, grid_size)

    ee5_x_values = np.linspace(EE5_X_MIN, EE5_X_MAX, grid_size)
    ee5_yl_values = np.linspace(EE5_YL_MIN, EE5_YL_MAX, grid_size)
    ee5_yr_values = np.linspace(EE5_YR_MIN, EE5_YR_MAX, grid_size)
    ee5_z_values = np.linspace(EE5_Z_MIN, EE5_Z_MAX, grid_size)

    configs = []
    for base_x in base_x_values:
        for base_y_left in base_y_left_values:
            for base_y_right in base_y_right_values:
                for base_z in base_z_values:
                    for ee5_x in ee5_x_values:
                        for ee5_yl in ee5_yl_values:
                            for ee5_yr in ee5_yr_values:
                                for ee5_z in ee5_z_values:
                                    configs.append((
                                        base_x, base_y_left, base_y_right, base_z,
                                        ee5_x, ee5_yl, ee5_yr, ee5_z
                                    ))
    return configs


def run_optimization(grid_size: int = 8, num_workers: int = 64, verbose: bool = True):
    """
    Run the full 8-variable grid search optimization.
    """
    print("=" * 70)
    print("8-Variable Comprehensive Optimization with Analytical IK")
    print("=" * 70)

    total_configs = grid_size ** 8

    print(f"\n[CHECK] Search space (8 variables):")
    print(f"  Base X:     [{BASE_X_MIN:.2f}, {BASE_X_MAX:.2f}] ({grid_size} points)")
    print(f"  Base Y_L:   [{BASE_Y_LEFT_MIN:.2f}, {BASE_Y_LEFT_MAX:.2f}] ({grid_size} points)")
    print(f"  Base Y_R:   [{BASE_Y_RIGHT_MIN:.2f}, {BASE_Y_RIGHT_MAX:.2f}] ({grid_size} points)")
    print(f"  Base Z:     [{BASE_Z_MIN:.2f}, {BASE_Z_MAX:.2f}] ({grid_size} points)")
    print(f"  EE5 X:      [{EE5_X_MIN:.2f}, {EE5_X_MAX:.2f}] ({grid_size} points)")
    print(f"  EE5 Y_L:    [{EE5_YL_MIN:.2f}, {EE5_YL_MAX:.2f}] ({grid_size} points)")
    print(f"  EE5 Y_R:    [{EE5_YR_MIN:.2f}, {EE5_YR_MAX:.2f}] ({grid_size} points)")
    print(f"  EE5 Z:      [{EE5_Z_MIN:.2f}, {EE5_Z_MAX:.2f}] ({grid_size} points)")
    print(f"\n  Total configurations: {total_configs:,}")
    print(f"  Parallel workers: {num_workers}")

    print(f"\n[CHECK] Constraints:")
    print(f"  Arm separation: |EE5_Y_L - EE5_Y_R| > {MIN_ARM_SEPARATION}m")
    print(f"  Hook constraint: EE5_X < {HOOK_X}m")

    # Generate configurations
    print(f"\n[RUN] Generating configurations...")
    configs = generate_configurations(grid_size)
    print(f"  Generated {len(configs):,} configurations")

    print(f"\n[RUN] Starting optimization with {num_workers} workers...")
    start_time = time.time()

    results = []

    # Split into batches
    batch_size = max(50, len(configs) // (num_workers * 4))
    batches = [configs[i:i+batch_size] for i in range(0, len(configs), batch_size)]

    print(f"  {len(batches)} batches of ~{batch_size} configurations")

    if num_workers > 1:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            completed = 0
            for batch_results in executor.map(evaluate_batch, batches):
                results.extend(batch_results)
                completed += len(batch_results)
                if verbose and completed % 10000 < batch_size:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (len(configs) - completed) / rate if rate > 0 else 0
                    print(f"  Progress: {completed:,}/{len(configs):,} "
                          f"({100*completed/len(configs):.1f}%) "
                          f"Rate: {rate:.0f}/s, ETA: {remaining:.0f}s")
    else:
        for i, cfg in enumerate(configs):
            results.append(evaluate_configuration(cfg))
            if verbose and (i + 1) % 1000 == 0:
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
    cfg = best.config

    print("\n" + "=" * 70)
    print("VALUES FOR task_config.py")
    print("=" * 70)

    print(f"""
# =============================================================================
# Robot Base Positions (8-Variable Analytical IK Optimization)
# =============================================================================
# Optimization date: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Method: He & Liu Analytical IK (8-variable optimization)
# Worst-case joint margin: {best.min_margin_deg:.1f} deg

ROBOT_LEFT_BASE = ({cfg.base_x:.4f}, {cfg.base_y_left:.4f}, {cfg.base_z:.4f})
ROBOT_RIGHT_BASE = ({cfg.base_x:.4f}, {cfg.base_y_right:.4f}, {cfg.base_z:.4f})

# Base rotation: Y+90 deg for wall-mount
ROBOT_BASE_QUAT_WXYZ = (0.7071, 0.0, 0.7071, 0.0)
ROBOT_BASE_QUAT_XYZW = (0.0, 0.7071, 0.0, 0.7071)

# =============================================================================
# Phase 5 Optimal EE Positions (Optimized)
# =============================================================================
# Arm separation: {abs(cfg.ee5_y_left - cfg.ee5_y_right):.3f}m (> {MIN_ARM_SEPARATION}m required)

WAYPOINT_PHASE5_LEFT = ({cfg.ee5_x:.4f}, {cfg.ee5_y_left:.4f}, {cfg.ee5_z:.4f})
WAYPOINT_PHASE5_RIGHT = ({cfg.ee5_x:.4f}, {cfg.ee5_y_right:.4f}, {cfg.ee5_z:.4f})
""")

    # Output joint angles for each phase
    phase_configs = [
        ('Phase1', 'LEFT_ARM_INIT_JOINTS', 'RIGHT_ARM_INIT_JOINTS',
         'Initial (hover 15cm above cable)'),
        ('Phase2', 'PHASE2_LEFT_JOINTS', 'PHASE2_RIGHT_JOINTS',
         'Grasp (cable surface)'),
        ('Phase3', 'PHASE3_LEFT_JOINTS', 'PHASE3_RIGHT_JOINTS',
         'Lift'),
        ('Phase4', 'PHASE4_LEFT_JOINTS', 'PHASE4_RIGHT_JOINTS',
         'Hook approach'),
        ('Phase5', 'PHASE5_LEFT_JOINTS', 'PHASE5_RIGHT_JOINTS',
         'Cable placement (OPTIMIZED)'),
    ]

    for phase_key, left_name, right_name, desc in phase_configs:
        left_joints = best.phase_joints[phase_key]['left']
        right_joints = best.phase_joints[phase_key]['right']
        left_margin, right_margin = best.phase_margins[phase_key]

        # Get EE positions
        if phase_key == 'Phase5':
            left_ee = f"({cfg.ee5_x:.2f}, {cfg.ee5_y_left:.2f}, {cfg.ee5_z:.2f})"
            right_ee = f"({cfg.ee5_x:.2f}, {cfg.ee5_y_right:.2f}, {cfg.ee5_z:.2f})"
        else:
            left_ee = str(tuple(FIXED_WAYPOINTS[phase_key]['left']))
            right_ee = str(tuple(FIXED_WAYPOINTS[phase_key]['right']))

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

    # Count constraint violations
    constraint_violated = sum(1 for r in results if r.constraint_violated)
    evaluated = len(results) - constraint_violated

    print(f"\nTotal configurations: {len(results):,}")
    print(f"  Constraint violated: {constraint_violated:,} ({100*constraint_violated/len(results):.1f}%)")
    print(f"  Actually evaluated: {evaluated:,}")

    # Filter successful configurations
    successful = [r for r in results if r.all_success and not r.constraint_violated]
    print(f"\nSuccessful configurations: {len(successful):,} / {evaluated:,} "
          f"({100*len(successful)/evaluated:.1f}% of evaluated)")

    if not successful:
        print("\n[ERROR] No successful configuration found!")
        # Show partial results
        partial = [r for r in results if not r.constraint_violated]
        if partial:
            partial = sorted(partial, key=lambda x: x.min_margin_deg, reverse=True)[:5]
            print("\nBest partial results:")
            for i, r in enumerate(partial):
                cfg = r.config
                print(f"\n  #{i+1}: Base=({cfg.base_x:.2f}, {cfg.base_y_left:.2f}, "
                      f"{cfg.base_y_right:.2f}, {cfg.base_z:.2f})")
                print(f"       EE5=({cfg.ee5_x:.2f}, {cfg.ee5_y_left:.2f}, "
                      f"{cfg.ee5_y_right:.2f}, {cfg.ee5_z:.2f})")
                print(f"       Margin: {r.min_margin_deg:.1f} deg")
        return results, None

    # Sort by minimum margin
    ranked = sorted(successful, key=lambda x: x.min_margin_deg, reverse=True)

    # Top 10
    print("\n" + "-" * 50)
    print("TOP 10 BY MINIMUM JOINT MARGIN")
    print("-" * 50)

    for i, r in enumerate(ranked[:10]):
        cfg = r.config
        arm_sep = abs(cfg.ee5_y_left - cfg.ee5_y_right)
        print(f"\n#{i+1}: Margin={r.min_margin_deg:.1f} deg, ArmSep={arm_sep:.2f}m")
        print(f"    Base: X={cfg.base_x:.3f}, Y_L={cfg.base_y_left:.3f}, "
              f"Y_R={cfg.base_y_right:.3f}, Z={cfg.base_z:.3f}")
        print(f"    EE5:  X={cfg.ee5_x:.3f}, Y_L={cfg.ee5_y_left:.3f}, "
              f"Y_R={cfg.ee5_y_right:.3f}, Z={cfg.ee5_z:.3f}")
        for phase, (lm, rm) in r.phase_margins.items():
            print(f"    {phase}: L={lm:.1f} deg, R={rm:.1f} deg")

    # Save results
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        best = ranked[0]
        cfg = best.config

        summary = {
            "optimization_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "method": "Analytical IK (8-variable)",
            "search_parameters": {
                "base_x_range": [float(BASE_X_MIN), float(BASE_X_MAX)],
                "base_y_left_range": [float(BASE_Y_LEFT_MIN), float(BASE_Y_LEFT_MAX)],
                "base_y_right_range": [float(BASE_Y_RIGHT_MIN), float(BASE_Y_RIGHT_MAX)],
                "base_z_range": [float(BASE_Z_MIN), float(BASE_Z_MAX)],
                "ee5_x_range": [float(EE5_X_MIN), float(EE5_X_MAX)],
                "ee5_yl_range": [float(EE5_YL_MIN), float(EE5_YL_MAX)],
                "ee5_yr_range": [float(EE5_YR_MIN), float(EE5_YR_MAX)],
                "ee5_z_range": [float(EE5_Z_MIN), float(EE5_Z_MAX)],
                "total_configs": len(results),
            },
            "constraints": {
                "min_arm_separation": float(MIN_ARM_SEPARATION),
                "max_ee5_x": float(HOOK_X),
            },
            "results_summary": {
                "total_tested": len(results),
                "constraint_violated": constraint_violated,
                "evaluated": evaluated,
                "successful": len(successful),
                "success_rate": f"{100*len(successful)/evaluated:.1f}%",
            },
            "best_configuration": {
                "base_x": float(cfg.base_x),
                "base_y_left": float(cfg.base_y_left),
                "base_y_right": float(cfg.base_y_right),
                "base_z": float(cfg.base_z),
                "ee5_x": float(cfg.ee5_x),
                "ee5_y_left": float(cfg.ee5_y_left),
                "ee5_y_right": float(cfg.ee5_y_right),
                "ee5_z": float(cfg.ee5_z),
                "min_margin_deg": float(best.min_margin_deg),
                "arm_separation": float(abs(cfg.ee5_y_left - cfg.ee5_y_right)),
            },
        }

        json_path = output_dir / "8var_optimization_results.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n[RESULT] Saved JSON: {json_path}")

    # Output task_config.py values
    if ranked:
        output_task_config_values(ranked[0])

    return results, ranked


def main():
    parser = argparse.ArgumentParser(
        description="8-variable optimization with analytical IK"
    )
    parser.add_argument("--workers", type=int, default=64,
                        help="Number of parallel workers (default: 64)")
    parser.add_argument("--grid", type=int, default=8,
                        help="Grid size per dimension (default: 8)")
    parser.add_argument("--quick", action="store_true",
                        help="Use 5x5 grid for quick test")
    parser.add_argument("--output", type=str,
                        default="data/8var_optimization",
                        help="Output directory")
    args = parser.parse_args()

    grid_size = 5 if args.quick else args.grid

    print(f"\n[TASK] 8-Variable Comprehensive Optimization")
    print(f"  Grid: {grid_size}^8 = {grid_size**8:,} configurations")
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
