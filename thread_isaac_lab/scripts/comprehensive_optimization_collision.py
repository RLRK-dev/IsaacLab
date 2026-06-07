#!/usr/bin/env python3
"""
Comprehensive 8-Variable Optimization with Collision Avoidance

Adds robot geometry-based collision checking:
- Computes all joint positions via FK
- Checks minimum distance between arm links
- Uses conservative link radius for safety margin

Usage:
    python comprehensive_optimization_collision.py [OPTIONS]
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
    solve_ik_best, compute_joint_margin, Q_MIN, Q_MAX,
    D1, D3, D5, A4, A7, franka_IK_EE_with_base
)


def solve_ik_elbow_down(target_pos: np.ndarray, base_pos: np.ndarray,
                        base_quat: np.ndarray,
                        target_quat: np.ndarray = None,
                        q7_range: tuple = (-2.8, 2.8),
                        q7_steps: int = 25):
    """
    Find best IK solution with elbow-down constraint (J5 < 0).
    """
    if target_quat is None:
        # Wall mount: Y-axis +90° rotation for gripper pointing down in world frame
        target_quat = np.array([0.7071, 0.0, 0.7071, 0.0])  # (w,x,y,z)

    best_solution = None
    best_margin = -1.0

    for q7 in np.linspace(q7_range[0], q7_range[1], q7_steps):
        solutions = franka_IK_EE_with_base(
            target_pos, target_quat, base_pos, base_quat, q7
        )

        for sol in solutions:
            if sol.valid and sol.joints[4] < 0:  # Elbow-down constraint
                if sol.margin_deg > best_margin:
                    best_margin = sol.margin_deg
                    best_solution = sol.joints.copy()

    if best_solution is not None:
        return True, best_solution, best_margin
    else:
        return False, None, 0.0

# Flange to EE offset (not exported from franka_analytical_ik)
FLANGE_TO_EE = 0.1123  # URDF実測値: panda_hand → fingertip (2025-12-30確認)

# ============================================================
# Constants
# ============================================================

WALL_MOUNT_QUAT = np.array([0.7071, 0.0, 0.7071, 0.0])
GRIPPER_DOWN_QUAT = np.array([0.0, 0.7071, -0.7071, 0.0])
HOOK_X = 0.25

# ============================================================
# Robot Geometry for Collision Checking
# ============================================================

# Franka Panda approximate link radii (conservative)
LINK_RADIUS = 0.08  # 8cm radius for arm links
GRIPPER_RADIUS = 0.05  # 5cm for gripper

# Minimum clearance between arm link centers
# = 2 * LINK_RADIUS + safety_margin
MIN_LINK_CLEARANCE = 2 * LINK_RADIUS + 0.04  # 0.20m total

# ============================================================
# Search Parameters
# ============================================================

BASE_X_MIN, BASE_X_MAX = 0.20, 0.27
BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX = -0.42, -0.30
BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX = 0.20, 0.32
BASE_Z_MIN, BASE_Z_MAX = 1.12, 1.28

EE5_X_MIN, EE5_X_MAX = 0.30, 0.40
EE5_YL_MIN, EE5_YL_MAX = -0.25, -0.05
EE5_YR_MIN, EE5_YR_MAX = 0.00, 0.20
EE5_Z_MIN, EE5_Z_MAX = 0.80, 0.95

MIN_ARM_SEPARATION = 0.15

# ============================================================
# Fixed Waypoints (Phase 1-4)
# ============================================================

FIXED_WAYPOINTS = {
    'Phase1': {
        'left': np.array([0.30, -0.285, 0.905]),
        'right': np.array([0.30, +0.285, 0.905]),
    },
    'Phase2': {
        'left': np.array([0.30, -0.285, 0.75]),
        'right': np.array([0.30, +0.285, 0.75]),
    },
    'Phase3': {
        'left': np.array([0.30, -0.285, 0.90]),
        'right': np.array([0.30, +0.285, 0.90]),
    },
    'Phase4': {
        'left': np.array([0.36, -0.18, 0.85]),
        'right': np.array([0.36, +0.18, 0.85]),
    },
}


# ============================================================
# Forward Kinematics for All Joint Positions
# ============================================================

def compute_all_joint_positions(joints: np.ndarray, base_pos: np.ndarray,
                                 base_quat: np.ndarray) -> List[np.ndarray]:
    """
    Compute positions of all joints (0-7) and EE in world frame.

    Returns:
        List of 9 positions: [base, j1, j2, j3, j4, j5, j6, j7, EE]
    """
    from scipy.spatial.transform import Rotation as R

    # Base transformation
    r_base = R.from_quat([base_quat[1], base_quat[2], base_quat[3], base_quat[0]])
    R_base = r_base.as_matrix()

    # DH parameters: (a, d, alpha)
    dh_params = [
        (0, D1, 0),           # Joint 1
        (0, 0, -np.pi/2),     # Joint 2
        (0, D3, np.pi/2),     # Joint 3
        (A4, 0, np.pi/2),     # Joint 4
        (-A4, D5, -np.pi/2),  # Joint 5
        (0, 0, np.pi/2),      # Joint 6
        (A7, 0, np.pi/2),     # Joint 7
    ]

    positions = [base_pos.copy()]  # Base position

    T = np.eye(4)
    T[:3, :3] = R_base
    T[:3, 3] = base_pos

    for i, (a, d, alpha) in enumerate(dh_params):
        theta = joints[i]
        ct, st = np.cos(theta), np.sin(theta)
        ca, sa = np.cos(alpha), np.sin(alpha)

        dh_matrix = np.array([
            [ct, -st*ca, st*sa, a*ct],
            [st, ct*ca, -ct*sa, a*st],
            [0, sa, ca, d],
            [0, 0, 0, 1]
        ])

        T = T @ dh_matrix
        positions.append(T[:3, 3].copy())

    # Add EE position (offset from joint 7)
    T_ee = np.eye(4)
    T_ee[2, 3] = 0.1123  # Flange to fingertip
    T_final = T @ T_ee
    positions.append(T_final[:3, 3].copy())

    return positions


def check_arm_collision(left_positions: List[np.ndarray],
                        right_positions: List[np.ndarray],
                        min_clearance: float = MIN_LINK_CLEARANCE) -> Tuple[bool, float]:
    """
    Check if two arms are in collision based on joint positions.

    Args:
        left_positions: List of 9 positions for left arm
        right_positions: List of 9 positions for right arm
        min_clearance: Minimum required distance between link centers

    Returns:
        collision_free: True if no collision
        min_distance: Minimum distance found between any two links
    """
    min_dist = float('inf')

    # Check distances between corresponding and adjacent joints
    # Skip base (index 0) as it's fixed
    for i in range(1, len(left_positions)):
        for j in range(1, len(right_positions)):
            dist = np.linalg.norm(left_positions[i] - right_positions[j])
            min_dist = min(min_dist, dist)

    collision_free = min_dist >= min_clearance
    return collision_free, min_dist


# ============================================================
# Configuration and Result Classes
# ============================================================

@dataclass
class Config8Var:
    base_x: float
    base_y_left: float
    base_y_right: float
    base_z: float
    ee5_x: float
    ee5_y_left: float
    ee5_y_right: float
    ee5_z: float


@dataclass
class ConfigResult:
    config: Config8Var
    all_success: bool
    min_margin_deg: float
    min_arm_distance: float  # NEW: minimum distance between arms
    phase_margins: Dict[str, Tuple[float, float]]
    phase_joints: Dict[str, Dict[str, np.ndarray]]
    phase_min_distances: Dict[str, float]  # NEW: per-phase minimum distances
    constraint_violated: bool = False
    collision_detected: bool = False  # NEW


def check_constraints(config: Config8Var) -> bool:
    """Check basic geometric constraints."""
    arm_separation = abs(config.ee5_y_left - config.ee5_y_right)
    if arm_separation < MIN_ARM_SEPARATION:
        return False
    # ベースはウェイポイントより後方（必須）
    min_waypoint_x = min(wp['left'][0] for wp in FIXED_WAYPOINTS.values())
    if config.base_x >= min_waypoint_x - 0.02:
        return False
    return True


def evaluate_configuration(config_tuple: Tuple) -> ConfigResult:
    """
    Evaluate configuration with collision checking.
    """
    (base_x, base_y_left, base_y_right, base_z,
     ee5_x, ee5_y_left, ee5_y_right, ee5_z) = config_tuple

    config = Config8Var(
        base_x=base_x, base_y_left=base_y_left,
        base_y_right=base_y_right, base_z=base_z,
        ee5_x=ee5_x, ee5_y_left=ee5_y_left,
        ee5_y_right=ee5_y_right, ee5_z=ee5_z
    )

    # Check basic constraints
    if not check_constraints(config):
        return ConfigResult(
            config=config,
            all_success=False,
            min_margin_deg=0.0,
            min_arm_distance=0.0,
            phase_margins={},
            phase_joints={},
            phase_min_distances={},
            constraint_violated=True
        )

    left_base = np.array([base_x, base_y_left, base_z])
    right_base = np.array([base_x, base_y_right, base_z])

    # Build waypoints including Phase 5
    waypoints = dict(FIXED_WAYPOINTS)
    waypoints['Phase5'] = {
        'left': np.array([ee5_x, ee5_y_left, ee5_z]),
        'right': np.array([ee5_x, ee5_y_right, ee5_z]),
    }

    all_success = True
    min_margin = float('inf')
    min_arm_distance = float('inf')
    phase_margins = {}
    phase_joints = {}
    phase_min_distances = {}
    collision_detected = False

    for phase_name, targets in waypoints.items():
        # Solve IK for both arms (elbow-down constrained)
        left_success, left_joints, left_margin = solve_ik_elbow_down(
            targets['left'], left_base, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
            q7_range=(-2.5, 2.5), q7_steps=25
        )

        right_success, right_joints, right_margin = solve_ik_elbow_down(
            targets['right'], right_base, WALL_MOUNT_QUAT, GRIPPER_DOWN_QUAT,
            q7_range=(-2.5, 2.5), q7_steps=25
        )

        if not left_success or not right_success:
            all_success = False
            phase_margins[phase_name] = (
                left_margin if left_success else 0.0,
                right_margin if right_success else 0.0
            )
            phase_joints[phase_name] = {'left': left_joints, 'right': right_joints}
            phase_min_distances[phase_name] = 0.0
            min_margin = 0.0
            continue

        # Compute all joint positions for collision check
        left_positions = compute_all_joint_positions(left_joints, left_base, WALL_MOUNT_QUAT)
        right_positions = compute_all_joint_positions(right_joints, right_base, WALL_MOUNT_QUAT)

        # Check collision
        collision_free, phase_min_dist = check_arm_collision(left_positions, right_positions)

        if not collision_free:
            collision_detected = True
            all_success = False

        phase_margins[phase_name] = (left_margin, right_margin)
        phase_joints[phase_name] = {'left': left_joints, 'right': right_joints}
        phase_min_distances[phase_name] = phase_min_dist

        min_margin = min(min_margin, left_margin, right_margin)
        min_arm_distance = min(min_arm_distance, phase_min_dist)

    return ConfigResult(
        config=config,
        all_success=all_success and not collision_detected,
        min_margin_deg=min_margin if (all_success and not collision_detected) else 0.0,
        min_arm_distance=min_arm_distance,
        phase_margins=phase_margins,
        phase_joints=phase_joints,
        phase_min_distances=phase_min_distances,
        constraint_violated=False,
        collision_detected=collision_detected
    )


def evaluate_batch(configs: List[Tuple]) -> List[ConfigResult]:
    return [evaluate_configuration(cfg) for cfg in configs]


def generate_configurations(grid_size: int) -> List[Tuple]:
    base_x_values = np.linspace(BASE_X_MIN, BASE_X_MAX, grid_size)
    base_y_left_values = np.linspace(BASE_Y_LEFT_MIN, BASE_Y_LEFT_MAX, grid_size)
    base_y_right_values = np.linspace(BASE_Y_RIGHT_MIN, BASE_Y_RIGHT_MAX, grid_size)
    base_z_values = np.linspace(BASE_Z_MIN, BASE_Z_MAX, grid_size)
    ee5_x_values = np.linspace(EE5_X_MIN, EE5_X_MAX, grid_size)
    ee5_yl_values = np.linspace(EE5_YL_MIN, EE5_YL_MAX, grid_size)
    ee5_yr_values = np.linspace(EE5_YR_MIN, EE5_YR_MAX, grid_size)
    ee5_z_values = np.linspace(EE5_Z_MIN, EE5_Z_MAX, grid_size)

    configs = []
    for bx in base_x_values:
        for byl in base_y_left_values:
            for byr in base_y_right_values:
                for bz in base_z_values:
                    for e5x in ee5_x_values:
                        for e5yl in ee5_yl_values:
                            for e5yr in ee5_yr_values:
                                for e5z in ee5_z_values:
                                    configs.append((bx, byl, byr, bz, e5x, e5yl, e5yr, e5z))
    return configs


def run_optimization(grid_size: int = 6, num_workers: int = 64, verbose: bool = True):
    print("=" * 70)
    print("8-Variable Optimization with COLLISION CHECKING")
    print("=" * 70)

    total_configs = grid_size ** 8

    print(f"\n[CHECK] Robot geometry:")
    print(f"  Link radius: {LINK_RADIUS*100:.0f} cm")
    print(f"  Min link clearance: {MIN_LINK_CLEARANCE*100:.0f} cm")

    print(f"\n[CHECK] Search space: {grid_size}^8 = {total_configs:,} configurations")
    print(f"  Workers: {num_workers}")

    configs = generate_configurations(grid_size)
    print(f"\n[RUN] Starting optimization...")
    start_time = time.time()

    results = []
    batch_size = max(50, len(configs) // (num_workers * 4))
    batches = [configs[i:i+batch_size] for i in range(0, len(configs), batch_size)]

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
                          f"ETA: {remaining:.0f}s")
    else:
        for cfg in configs:
            results.append(evaluate_configuration(cfg))

    elapsed = time.time() - start_time
    print(f"\n[RESULT] Completed in {elapsed:.1f}s ({len(configs)/elapsed:.0f} configs/s)")

    return results


def format_joints_for_config(joints: np.ndarray, name: str) -> str:
    lines = [f"{name} = ["]
    joint_names = ["panda_joint1", "panda_joint2", "panda_joint3", "panda_joint4",
                   "panda_joint5", "panda_joint6", "panda_joint7"]
    for i, (jn, angle) in enumerate(zip(joint_names, joints)):
        comma = "," if i < 6 else ""
        lines.append(f"    {angle:+.6f}{comma}  # {jn}: {np.degrees(angle):+.1f} deg")
    lines.append("]")
    return "\n".join(lines)


def output_task_config_values(best: ConfigResult):
    cfg = best.config
    print("\n" + "=" * 70)
    print("VALUES FOR task_config.py")
    print("=" * 70)

    print(f"""
# =============================================================================
# Robot Base Positions (8-Var Optimization with Collision Check)
# =============================================================================
# Optimization date: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Method: He & Liu Analytical IK + Geometry-based Collision Check
# Worst-case joint margin: {best.min_margin_deg:.1f} deg
# Minimum arm clearance: {best.min_arm_distance*100:.1f} cm (required: {MIN_LINK_CLEARANCE*100:.0f} cm)

ROBOT_LEFT_BASE = ({cfg.base_x:.4f}, {cfg.base_y_left:.4f}, {cfg.base_z:.4f})
ROBOT_RIGHT_BASE = ({cfg.base_x:.4f}, {cfg.base_y_right:.4f}, {cfg.base_z:.4f})

ROBOT_BASE_QUAT_WXYZ = (0.7071, 0.0, 0.7071, 0.0)
ROBOT_BASE_QUAT_XYZW = (0.0, 0.7071, 0.0, 0.7071)

# =============================================================================
# Phase 5 Optimal EE Positions
# =============================================================================
WAYPOINT_PHASE5_LEFT = ({cfg.ee5_x:.4f}, {cfg.ee5_y_left:.4f}, {cfg.ee5_z:.4f})
WAYPOINT_PHASE5_RIGHT = ({cfg.ee5_x:.4f}, {cfg.ee5_y_right:.4f}, {cfg.ee5_z:.4f})
""")

    phase_configs = [
        ('Phase1', 'LEFT_ARM_INIT_JOINTS', 'RIGHT_ARM_INIT_JOINTS', 'Initial'),
        ('Phase2', 'PHASE2_LEFT_JOINTS', 'PHASE2_RIGHT_JOINTS', 'Grasp'),
        ('Phase3', 'PHASE3_LEFT_JOINTS', 'PHASE3_RIGHT_JOINTS', 'Lift'),
        ('Phase4', 'PHASE4_LEFT_JOINTS', 'PHASE4_RIGHT_JOINTS', 'Hook'),
        ('Phase5', 'PHASE5_LEFT_JOINTS', 'PHASE5_RIGHT_JOINTS', 'Place'),
    ]

    for phase_key, left_name, right_name, desc in phase_configs:
        left_joints = best.phase_joints[phase_key]['left']
        right_joints = best.phase_joints[phase_key]['right']
        left_margin, right_margin = best.phase_margins[phase_key]
        phase_dist = best.phase_min_distances.get(phase_key, 0)

        print(f"""
# {phase_key}: {desc} | Margin: L={left_margin:.1f}°, R={right_margin:.1f}° | Clearance: {phase_dist*100:.1f}cm
""")
        if left_joints is not None:
            print(format_joints_for_config(left_joints, left_name))
            print()
        if right_joints is not None:
            print(format_joints_for_config(right_joints, right_name))

    print("\n" + "=" * 70)


def analyze_and_report(results: List[ConfigResult], output_dir: Path = None):
    print("\n" + "=" * 70)
    print("[RESULT] ANALYSIS")
    print("=" * 70)

    constraint_violated = sum(1 for r in results if r.constraint_violated)
    collision_detected = sum(1 for r in results if r.collision_detected)
    evaluated = len(results) - constraint_violated

    print(f"\nTotal: {len(results):,}")
    print(f"  Constraint violated: {constraint_violated:,}")
    print(f"  Collision detected: {collision_detected:,}")
    print(f"  Evaluated: {evaluated:,}")

    successful = [r for r in results if r.all_success and not r.collision_detected]
    print(f"\nCollision-free success: {len(successful):,} / {evaluated:,} "
          f"({100*len(successful)/max(1,evaluated):.1f}%)")

    if not successful:
        print("\n[ERROR] No collision-free configuration found!")
        return results, None

    # Sort by margin, then by arm distance
    ranked = sorted(successful, key=lambda x: (x.min_margin_deg, x.min_arm_distance), reverse=True)

    print("\n" + "-" * 50)
    print("TOP 10 (Collision-Free)")
    print("-" * 50)

    for i, r in enumerate(ranked[:10]):
        cfg = r.config
        print(f"\n#{i+1}: Margin={r.min_margin_deg:.1f}°, Clearance={r.min_arm_distance*100:.1f}cm")
        print(f"    Base: X={cfg.base_x:.3f}, Y_L={cfg.base_y_left:.3f}, Y_R={cfg.base_y_right:.3f}, Z={cfg.base_z:.3f}")
        print(f"    EE5:  X={cfg.ee5_x:.3f}, Y_L={cfg.ee5_y_left:.3f}, Y_R={cfg.ee5_y_right:.3f}, Z={cfg.ee5_z:.3f}")
        for phase, (lm, rm) in r.phase_margins.items():
            pd = r.phase_min_distances.get(phase, 0)
            print(f"    {phase}: L={lm:.1f}°, R={rm:.1f}°, dist={pd*100:.1f}cm")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "collision_optimization_results.json"
        with open(json_path, 'w') as f:
            json.dump({
                "date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total": len(results),
                "successful": len(successful),
                "best_margin_deg": ranked[0].min_margin_deg,
                "best_clearance_m": ranked[0].min_arm_distance,
            }, f, indent=2)
        print(f"\n[RESULT] Saved: {json_path}")

    if ranked:
        output_task_config_values(ranked[0])

    return results, ranked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=64)
    parser.add_argument("--grid", type=int, default=5)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--output", type=str, default="data/collision_optimization")
    args = parser.parse_args()

    grid_size = 4 if args.quick else args.grid

    print(f"\n[TASK] 8-Variable Optimization with Collision Checking")
    print(f"  Grid: {grid_size}^8 = {grid_size**8:,} configurations")

    results = run_optimization(grid_size=grid_size, num_workers=args.workers)
    analyze_and_report(results, Path(args.output))


if __name__ == "__main__":
    main()
