"""
IK到達可能性解析スクリプト

Isaac LabのDifferentialIKを使用して、実際のIKソルバーの挙動を解析し、
両アームがケーブル両端に到達できる最適な配置を探索する。

解析項目:
1. 各ロボットY位置でのケーブル端への到達可能性
2. joint2/joint4のマージン（限界からの余裕）
3. 最適配置のスコアリングとランキング
"""

import numpy as np
import torch
import csv
import json
from pathlib import Path
from scipy.spatial.transform import Rotation as R
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============================================================
# Constants
# ============================================================

# Joint limits (radians)
JOINT_LIMITS = {
    'joint1': (-2.8973, 2.8973),
    'joint2': (-1.7628, 1.7628),  # Most constrained: ±101°
    'joint3': (-2.8973, 2.8973),
    'joint4': (-3.0718, -0.0698),  # -176° to -4°
    'joint5': (-2.8973, 2.8973),
    'joint6': (-0.0175, 3.7525),
    'joint7': (-2.8973, 2.8973),
}

# Robot configuration
ROBOT_BASE_X = 0.0     # 壁位置
ROBOT_BASE_Z = 1.10    # 壁設置高さ
WALL_MOUNT_QUAT = (0.7071, 0.0, 0.7071, 0.0)  # Y+90° (wxyz)

# Cable configuration
TABLE_HEIGHT = 0.755
CABLE_LEFT_Y = -0.285   # seg_17
CABLE_RIGHT_Y = 0.285   # seg_19
CABLE_X = 0.30          # ケーブルX位置
GRASP_OFFSET = 0.03     # 3cm inward from cable ends

# Target positions (grasp positions)
GRASP_LEFT_Y = CABLE_LEFT_Y + GRASP_OFFSET   # -0.255
GRASP_RIGHT_Y = CABLE_RIGHT_Y - GRASP_OFFSET  # +0.255

# Search parameters
ROBOT_Y_SEARCH_LEFT = np.arange(-0.35, -0.05, 0.025)   # Left robot Y search range
ROBOT_Y_SEARCH_RIGHT = np.arange(0.05, 0.375, 0.025)   # Right robot Y search range (includes 0.35)


# ============================================================
# Panda DH Parameters (for analytical FK)
# ============================================================
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
    """
    Compute EE position from joint angles with base transformation

    Args:
        joint_angles: 7 joint angles in radians
        base_pos: (x, y, z) robot base position
        base_quat: (w, x, y, z) robot base orientation

    Returns:
        ee_pos: (x, y, z) end effector position
        ee_quat: (w, x, y, z) end effector orientation
    """
    # Base transformation
    T = np.eye(4)
    r = R.from_quat([base_quat[1], base_quat[2], base_quat[3], base_quat[0]])
    T[:3, :3] = r.as_matrix()
    T[:3, 3] = base_pos

    # Apply DH transformations
    for i in range(1, 8):
        a, d, alpha, theta_offset = PANDA_DH[i]
        theta = joint_angles[i-1] + theta_offset
        T = T @ dh_transform(a, d, alpha, theta)

    # Flange to EE
    T_ee = np.eye(4)
    T_ee[2, 3] = FLANGE_TO_EE
    T = T @ T_ee

    ee_pos = T[:3, 3]
    ee_rot = R.from_matrix(T[:3, :3])
    ee_quat_xyzw = ee_rot.as_quat()
    ee_quat = (ee_quat_xyzw[3], ee_quat_xyzw[0], ee_quat_xyzw[1], ee_quat_xyzw[2])

    return ee_pos, ee_quat


def compute_joint_margins(joint_angles):
    """
    Compute margin from joint limits for each joint

    Returns:
        margins: dict with margin for each joint (in degrees)
        min_margin: minimum margin across all joints
        critical_joints: list of joints with margin < 15°
    """
    margins = {}
    critical_joints = []

    for i, name in enumerate(['joint1', 'joint2', 'joint3', 'joint4',
                              'joint5', 'joint6', 'joint7']):
        angle = joint_angles[i]
        limit_min, limit_max = JOINT_LIMITS[name]

        margin_to_min = abs(angle - limit_min)
        margin_to_max = abs(limit_max - angle)
        margin = min(margin_to_min, margin_to_max)
        margin_deg = np.degrees(margin)

        margins[name] = {
            'angle_deg': np.degrees(angle),
            'margin_deg': margin_deg,
            'at_limit': margin_deg < 1.0,
        }

        if margin_deg < 15:
            critical_joints.append((name, margin_deg))

    min_margin = min(m['margin_deg'] for m in margins.values())

    return margins, min_margin, critical_joints


@dataclass
class IKResult:
    """Result of IK computation for a single target"""
    robot_y: float
    target_y: float
    success: bool
    joint_angles: Optional[np.ndarray]
    ee_pos: Optional[np.ndarray]
    position_error: float
    joint2_margin: float
    joint4_margin: float
    min_margin: float
    critical_joints: List[Tuple[str, float]]


@dataclass
class ConfigurationResult:
    """Result of a dual-arm configuration test"""
    left_robot_y: float
    right_robot_y: float
    left_result: IKResult
    right_result: IKResult
    both_success: bool
    total_score: float
    min_joint2_margin: float
    min_joint4_margin: float
    min_overall_margin: float


def solve_ik_numerical(target_pos, base_pos, base_quat,
                       initial_joints=None, max_iter=100, tol=0.005):
    """
    Numerical IK solver using gradient descent

    Args:
        target_pos: (x, y, z) target EE position
        base_pos: robot base position
        base_quat: robot base orientation (wxyz)
        initial_joints: starting joint configuration
        max_iter: maximum iterations
        tol: position tolerance (meters)

    Returns:
        IKResult with solution details
    """
    if initial_joints is None:
        # Default configuration for wall-mounted robot
        initial_joints = np.array([0, -0.5, 0, -1.5, 0, 1.5, 0.785])

    joints = initial_joints.copy()

    # Gradient descent with momentum
    learning_rate = 0.1
    momentum = 0.8
    velocity = np.zeros(7)

    best_joints = joints.copy()
    best_error = float('inf')

    for iteration in range(max_iter):
        # Forward kinematics
        ee_pos, _ = forward_kinematics(joints, base_pos, base_quat)

        # Position error
        error = target_pos - ee_pos
        error_norm = np.linalg.norm(error)

        if error_norm < best_error:
            best_error = error_norm
            best_joints = joints.copy()

        if error_norm < tol:
            break

        # Numerical Jacobian (simplified - only position, 3x7)
        J = np.zeros((3, 7))
        delta = 0.001
        for i in range(7):
            joints_plus = joints.copy()
            joints_plus[i] += delta
            ee_plus, _ = forward_kinematics(joints_plus, base_pos, base_quat)
            J[:, i] = (ee_plus - ee_pos) / delta

        # Damped least squares
        lambda_dls = 0.1
        JJT = J @ J.T + lambda_dls * np.eye(3)
        delta_q = J.T @ np.linalg.solve(JJT, error)

        # Update with momentum
        velocity = momentum * velocity + learning_rate * delta_q
        joints = joints + velocity

        # Apply joint limits
        for i, name in enumerate(['joint1', 'joint2', 'joint3', 'joint4',
                                  'joint5', 'joint6', 'joint7']):
            limit_min, limit_max = JOINT_LIMITS[name]
            joints[i] = np.clip(joints[i], limit_min, limit_max)

    # Final evaluation
    ee_pos, _ = forward_kinematics(best_joints, base_pos, base_quat)
    final_error = np.linalg.norm(target_pos - ee_pos)

    success = final_error < tol

    margins, min_margin, critical = compute_joint_margins(best_joints)

    return IKResult(
        robot_y=base_pos[1],
        target_y=target_pos[1],
        success=success,
        joint_angles=best_joints if success else None,
        ee_pos=ee_pos,
        position_error=final_error,
        joint2_margin=margins['joint2']['margin_deg'],
        joint4_margin=margins['joint4']['margin_deg'],
        min_margin=min_margin,
        critical_joints=critical,
    )


def test_configuration(left_robot_y: float, right_robot_y: float) -> ConfigurationResult:
    """
    Test a dual-arm configuration

    Args:
        left_robot_y: Y position of left robot base
        right_robot_y: Y position of right robot base

    Returns:
        ConfigurationResult with detailed analysis
    """
    # Left arm reaching left cable end
    left_base_pos = (ROBOT_BASE_X, left_robot_y, ROBOT_BASE_Z)
    left_target = np.array([CABLE_X, GRASP_LEFT_Y, TABLE_HEIGHT])

    # Right arm reaching right cable end
    right_base_pos = (ROBOT_BASE_X, right_robot_y, ROBOT_BASE_Z)
    right_target = np.array([CABLE_X, GRASP_RIGHT_Y, TABLE_HEIGHT])

    # Solve IK for both arms
    left_result = solve_ik_numerical(left_target, left_base_pos, WALL_MOUNT_QUAT)
    right_result = solve_ik_numerical(right_target, right_base_pos, WALL_MOUNT_QUAT)

    # Overall evaluation
    both_success = left_result.success and right_result.success

    # Score calculation (higher is better)
    # Components:
    # - Success bonus: 100 points each
    # - Joint2 margin: up to 50 points (scaled by margin/20°)
    # - Joint4 margin: up to 30 points
    # - Overall min margin: up to 20 points

    score = 0
    if left_result.success:
        score += 100
        score += min(50, left_result.joint2_margin * 2.5)
        score += min(30, left_result.joint4_margin * 1.0)
    if right_result.success:
        score += 100
        score += min(50, right_result.joint2_margin * 2.5)
        score += min(30, right_result.joint4_margin * 1.0)

    min_joint2 = min(left_result.joint2_margin, right_result.joint2_margin)
    min_joint4 = min(left_result.joint4_margin, right_result.joint4_margin)
    min_overall = min(left_result.min_margin, right_result.min_margin)

    score += min(20, min_overall)

    return ConfigurationResult(
        left_robot_y=left_robot_y,
        right_robot_y=right_robot_y,
        left_result=left_result,
        right_result=right_result,
        both_success=both_success,
        total_score=score,
        min_joint2_margin=min_joint2,
        min_joint4_margin=min_joint4,
        min_overall_margin=min_overall,
    )


def run_full_search():
    """
    Run comprehensive search over all robot Y position combinations
    """
    print("=" * 70)
    print("IK Reachability Analysis - Full Search")
    print("=" * 70)
    print(f"\nTarget positions:")
    print(f"  Left grasp:  X={CABLE_X}, Y={GRASP_LEFT_Y}, Z={TABLE_HEIGHT}")
    print(f"  Right grasp: X={CABLE_X}, Y={GRASP_RIGHT_Y}, Z={TABLE_HEIGHT}")
    print(f"\nSearch space:")
    print(f"  Left robot Y:  {ROBOT_Y_SEARCH_LEFT[0]:.3f} to {ROBOT_Y_SEARCH_LEFT[-1]:.3f}")
    print(f"  Right robot Y: {ROBOT_Y_SEARCH_RIGHT[0]:.3f} to {ROBOT_Y_SEARCH_RIGHT[-1]:.3f}")
    print(f"  Total combinations: {len(ROBOT_Y_SEARCH_LEFT) * len(ROBOT_Y_SEARCH_RIGHT)}")

    results = []

    total = len(ROBOT_Y_SEARCH_LEFT) * len(ROBOT_Y_SEARCH_RIGHT)
    count = 0

    for left_y in ROBOT_Y_SEARCH_LEFT:
        for right_y in ROBOT_Y_SEARCH_RIGHT:
            count += 1
            if count % 20 == 0:
                print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")

            result = test_configuration(left_y, right_y)
            results.append(result)

    print(f"\n  Completed: {count} configurations tested")

    return results


def analyze_results(results: List[ConfigurationResult]):
    """
    Analyze and rank all configuration results
    """
    print("\n" + "=" * 70)
    print("Analysis Results")
    print("=" * 70)

    # Filter successful configurations
    successful = [r for r in results if r.both_success]
    print(f"\nSuccessful configurations: {len(successful)} / {len(results)}")

    if not successful:
        print("\n[WARNING] No fully successful configuration found!")
        # Show best partial results
        partial = sorted(results, key=lambda x: x.total_score, reverse=True)[:10]
        print("\nBest partial results (by score):")
        for i, r in enumerate(partial):
            print(f"\n  #{i+1}: Left Y={r.left_robot_y:.3f}, Right Y={r.right_robot_y:.3f}")
            print(f"      Score: {r.total_score:.1f}")
            print(f"      Left:  success={r.left_result.success}, j2_margin={r.left_result.joint2_margin:.1f}°")
            print(f"      Right: success={r.right_result.success}, j2_margin={r.right_result.joint2_margin:.1f}°")
        return results, partial

    # Sort by score
    ranked = sorted(successful, key=lambda x: x.total_score, reverse=True)

    # Top 5 by score
    print("\n" + "-" * 50)
    print("TOP 5 BY TOTAL SCORE")
    print("-" * 50)
    for i, r in enumerate(ranked[:5]):
        print(f"\n#{i+1}: Left Y={r.left_robot_y:.3f}, Right Y={r.right_robot_y:.3f}")
        print(f"    Score: {r.total_score:.1f}")
        print(f"    Joint2 margins: Left={r.left_result.joint2_margin:.1f}°, Right={r.right_result.joint2_margin:.1f}°")
        print(f"    Joint4 margins: Left={r.left_result.joint4_margin:.1f}°, Right={r.right_result.joint4_margin:.1f}°")
        print(f"    Min overall margin: {r.min_overall_margin:.1f}°")
        if r.left_result.critical_joints or r.right_result.critical_joints:
            print(f"    Critical joints: L={r.left_result.critical_joints}, R={r.right_result.critical_joints}")

    # Sort by joint2 margin
    by_joint2 = sorted(successful, key=lambda x: x.min_joint2_margin, reverse=True)

    print("\n" + "-" * 50)
    print("TOP 5 BY JOINT2 MARGIN")
    print("-" * 50)
    for i, r in enumerate(by_joint2[:5]):
        print(f"\n#{i+1}: Left Y={r.left_robot_y:.3f}, Right Y={r.right_robot_y:.3f}")
        print(f"    Min Joint2 margin: {r.min_joint2_margin:.1f}°")
        print(f"    Left j2={r.left_result.joint2_margin:.1f}°, Right j2={r.right_result.joint2_margin:.1f}°")

    # Sort by joint4 margin
    by_joint4 = sorted(successful, key=lambda x: x.min_joint4_margin, reverse=True)

    print("\n" + "-" * 50)
    print("TOP 5 BY JOINT4 MARGIN")
    print("-" * 50)
    for i, r in enumerate(by_joint4[:5]):
        print(f"\n#{i+1}: Left Y={r.left_robot_y:.3f}, Right Y={r.right_robot_y:.3f}")
        print(f"    Min Joint4 margin: {r.min_joint4_margin:.1f}°")
        print(f"    Left j4={r.left_result.joint4_margin:.1f}°, Right j4={r.right_result.joint4_margin:.1f}°")

    return results, ranked


def save_results(results: List[ConfigurationResult], output_dir: Path):
    """
    Save all results to CSV and JSON
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_path = output_dir / "ik_reachability_results.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'left_robot_y', 'right_robot_y',
            'both_success', 'total_score',
            'left_success', 'left_pos_error', 'left_j2_margin', 'left_j4_margin', 'left_min_margin',
            'right_success', 'right_pos_error', 'right_j2_margin', 'right_j4_margin', 'right_min_margin',
            'min_joint2_margin', 'min_joint4_margin', 'min_overall_margin'
        ])

        for r in results:
            writer.writerow([
                f"{r.left_robot_y:.4f}", f"{r.right_robot_y:.4f}",
                r.both_success, f"{r.total_score:.2f}",
                r.left_result.success, f"{r.left_result.position_error:.4f}",
                f"{r.left_result.joint2_margin:.2f}", f"{r.left_result.joint4_margin:.2f}",
                f"{r.left_result.min_margin:.2f}",
                r.right_result.success, f"{r.right_result.position_error:.4f}",
                f"{r.right_result.joint2_margin:.2f}", f"{r.right_result.joint4_margin:.2f}",
                f"{r.right_result.min_margin:.2f}",
                f"{r.min_joint2_margin:.2f}", f"{r.min_joint4_margin:.2f}",
                f"{r.min_overall_margin:.2f}"
            ])

    print(f"\nSaved CSV: {csv_path}")

    # Save JSON summary
    successful = [r for r in results if r.both_success]
    ranked = sorted(successful, key=lambda x: x.total_score, reverse=True) if successful else []

    summary = {
        "search_parameters": {
            "cable_x": CABLE_X,
            "grasp_left_y": GRASP_LEFT_Y,
            "grasp_right_y": GRASP_RIGHT_Y,
            "table_height": TABLE_HEIGHT,
            "robot_base_x": ROBOT_BASE_X,
            "robot_base_z": ROBOT_BASE_Z,
        },
        "results_summary": {
            "total_tested": len(results),
            "successful": len(successful),
            "success_rate": f"{100*len(successful)/len(results):.1f}%",
        },
        "top_configurations": [
            {
                "rank": i+1,
                "left_robot_y": r.left_robot_y,
                "right_robot_y": r.right_robot_y,
                "score": r.total_score,
                "min_joint2_margin_deg": r.min_joint2_margin,
                "min_joint4_margin_deg": r.min_joint4_margin,
                "min_overall_margin_deg": r.min_overall_margin,
            }
            for i, r in enumerate(ranked[:10])
        ],
        "recommendation": ranked[0].left_robot_y if ranked else None,
    }

    json_path = output_dir / "ik_reachability_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Saved JSON: {json_path}")

    return csv_path, json_path


def main():
    print("\n" + "=" * 70)
    print("IK REACHABILITY ANALYSIS")
    print("Finding optimal robot placement for cable manipulation")
    print("=" * 70)

    # Run full search
    results = run_full_search()

    # Analyze results
    all_results, ranked = analyze_results(results)

    # Save results
    output_dir = Path("data/ik_analysis")
    csv_path, json_path = save_results(all_results, output_dir)

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL RECOMMENDATION")
    print("=" * 70)

    successful = [r for r in results if r.both_success]
    if successful:
        best = sorted(successful, key=lambda x: x.total_score, reverse=True)[0]
        print(f"\nBest configuration:")
        print(f"  Left robot Y:  {best.left_robot_y:.3f}")
        print(f"  Right robot Y: {best.right_robot_y:.3f}")
        print(f"  Total score:   {best.total_score:.1f}")
        print(f"  Joint2 margins: Left={best.left_result.joint2_margin:.1f}°, Right={best.right_result.joint2_margin:.1f}°")
        print(f"  Joint4 margins: Left={best.left_result.joint4_margin:.1f}°, Right={best.right_result.joint4_margin:.1f}°")

        if best.left_result.joint_angles is not None:
            print(f"\nLeft arm joint angles (deg):")
            for i, angle in enumerate(best.left_result.joint_angles):
                print(f"  joint{i+1}: {np.degrees(angle):.1f}°")

        if best.right_result.joint_angles is not None:
            print(f"\nRight arm joint angles (deg):")
            for i, angle in enumerate(best.right_result.joint_angles):
                print(f"  joint{i+1}: {np.degrees(angle):.1f}°")
    else:
        print("\n[WARNING] No successful configuration found!")
        print("Consider:")
        print("  1. Relaxing position tolerance")
        print("  2. Adjusting cable position")
        print("  3. Changing robot base height")

    print(f"\nOutput files:")
    print(f"  {csv_path}")
    print(f"  {json_path}")


if __name__ == "__main__":
    main()
