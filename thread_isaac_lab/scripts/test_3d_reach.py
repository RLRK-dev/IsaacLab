#!/usr/bin/env python3
"""
3D Grid-based Reachability Test Script

Measure reachable volume for both robot arms on an XYZ grid.
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test 3D Grid Reachability")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
import sys
from typing import Tuple, List, Dict
from scipy.spatial.transform import Rotation as R

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT


class GridReachabilityTester3D:
    """Test IK reachability on a 3D grid for both arms."""

    def __init__(self, scene: InteractiveScene, sim, device: str):
        self.scene = scene
        self.sim = sim
        self.device = device

        # IK configuration
        ik_cfg = DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="dls",
            ik_params={"lambda_val": 0.02},
        )

        self.left_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)
        self.right_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)

        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        # Resolve body and joint indices
        body_ids, _ = self.robot_left.find_bodies("panda_hand")
        self.ee_body_idx = body_ids[0]
        self.jacobi_body_idx = self.ee_body_idx - 1

        joint_ids, _ = self.robot_left.find_joints("panda_joint.*")
        self.arm_joint_ids = list(joint_ids)

        # Default orientation (gripper pointing down with -90 Z rotation)
        base_rot = R.from_euler('x', 180, degrees=True)
        z_rot = R.from_euler('z', -90, degrees=True)
        final_rot = base_rot * z_rot
        quat_xyzw = final_rot.as_quat()
        quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
        self.default_quat = torch.tensor([quat_wxyz], device=device)

        # EE offset (fingertip is 10.7cm below panda_hand when pointing down)
        self.ee_offset = 0.1123

    def step_sim(self, steps: int = 1):
        for _ in range(steps):
            self.scene.write_data_to_sim()
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

    def get_ee_pose(self, robot) -> Tuple[torch.Tensor, torch.Tensor]:
        ee_pos_w = robot.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat_w = robot.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos_w, ee_quat_w

    def reset_arm(self, robot, ik_controller, joint0_angle: float):
        """Reset single arm to ready position."""
        ready_joint_pos = torch.tensor([
            [joint0_angle, -0.4, 0.0, -2.0, 0.0, 1.6, 0.785, 0.04, 0.04]
        ], device=self.device)

        for _ in range(20):
            robot.set_joint_position_target(ready_joint_pos)
            self.step_sim(4)

        ik_controller.reset()

    def test_single_position(self, robot, ik_controller, target_pos, max_steps=60):
        """Move arm to target and return final position error."""
        target_quat = self.default_quat

        for step in range(max_steps):
            joint_pos = robot.data.joint_pos[:, self.arm_joint_ids]
            jacobian = robot.root_physx_view.get_jacobians()[:, self.jacobi_body_idx, :, self.arm_joint_ids]
            ee_pos_w, ee_quat_w = self.get_ee_pose(robot)

            root_pos_w = robot.data.root_pos_w
            root_quat_w = robot.data.root_quat_w

            ee_pos_b, ee_quat_b = subtract_frame_transforms(
                root_pos_w, root_quat_w, ee_pos_w, ee_quat_w
            )
            target_pos_b, target_quat_b = subtract_frame_transforms(
                root_pos_w, root_quat_w, target_pos, target_quat
            )

            command = torch.cat([target_pos_b, target_quat_b], dim=-1)
            ik_controller.reset()
            ik_controller.set_command(command)

            try:
                result = ik_controller.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)
            except Exception:
                result = joint_pos

            # Apply joint positions
            gripper_pos = torch.full((1, 2), 0.04, device=self.device)
            robot.set_joint_position_target(torch.cat([result, gripper_pos], dim=-1))

            self.step_sim(2)

        # Get final position error
        ee_pos_w, _ = self.get_ee_pose(robot)
        pos_error = torch.norm(ee_pos_w - target_pos).item()
        return pos_error

    def test_3d_grid(self, robot, ik_controller, x_range: List[float], y_range: List[float],
                     z_range: List[float], arm_name: str, joint0_angle: float) -> Dict:
        """Test reachability on a 3D grid."""
        print(f"\n{'='*70}")
        print(f"Testing {arm_name} arm 3D reachability grid")
        print(f"{'='*70}")
        print(f"X range: {x_range}")
        print(f"Y range: {y_range}")
        print(f"Z range: {z_range}")
        print(f"Total positions: {len(x_range) * len(y_range) * len(z_range)}")

        results = {}

        for z in z_range:
            print(f"\n--- Z = {z:.2f} ---")
            results[z] = np.zeros((len(y_range), len(x_range)))

            for yi, y in enumerate(y_range):
                row_status = []
                for xi, x in enumerate(x_range):
                    # Reset arm before each test
                    self.reset_arm(robot, ik_controller, joint0_angle)

                    target = torch.tensor([[x, y, z]], device=self.device)
                    error = self.test_single_position(robot, ik_controller, target, max_steps=60)
                    results[z][yi, xi] = error

                    # Status indicator
                    if error < 0.02:
                        status = "○"
                    elif error < 0.05:
                        status = "△"
                    else:
                        status = "×"
                    row_status.append(status)

                # Print row summary
                y_str = f"{y:+.2f}" if y >= 0 else f"{y:.2f}"
                print(f"  Y={y_str}: {' '.join(row_status)}")

        return results

    def print_3d_map(self, results: Dict, x_range: List[float], y_range: List[float],
                     z_range: List[float], arm_name: str):
        """Print 3D reachability maps by Z slice."""
        print(f"\n{'='*70}")
        print(f"{arm_name} Arm 3D Reachability Maps")
        print(f"{'='*70}")
        print(f"(○=<2cm, △=2-5cm, ×=>5cm)")

        for z in z_range:
            print(f"\nZ = {z:.2f}:")

            # Header
            header = "Y\\X    "
            for x in x_range:
                header += f" {x:.2f} "
            print(header)

            # Rows
            for yi, y in enumerate(y_range):
                y_str = f"{y:+.2f}" if y >= 0 else f"{y:.2f}"
                row = f"{y_str} "
                for xi in range(len(x_range)):
                    err = results[z][yi, xi]
                    if err < 0.02:
                        row += "  ○   "
                    elif err < 0.05:
                        row += "  △   "
                    else:
                        row += "  ×   "
                print(row)

    def analyze_results(self, left_results: Dict, right_results: Dict,
                       x_range: List[float], left_y_range: List[float],
                       right_y_range: List[float], z_range: List[float]):
        """Analyze and summarize results."""
        print(f"\n{'='*70}")
        print("ANALYSIS")
        print(f"{'='*70}")

        THRESHOLD = 0.02  # 2cm

        # Left arm reachable region
        print("\n## 左アーム到達可能領域 (<2cm誤差)")
        left_reachable = []
        for z in z_range:
            for yi, y in enumerate(left_y_range):
                for xi, x in enumerate(x_range):
                    if left_results[z][yi, xi] < THRESHOLD:
                        left_reachable.append((x, y, z, left_results[z][yi, xi]))

        if left_reachable:
            lx_vals = [p[0] for p in left_reachable]
            ly_vals = [p[1] for p in left_reachable]
            lz_vals = [p[2] for p in left_reachable]
            print(f"  X範囲: {min(lx_vals):.2f} - {max(lx_vals):.2f}")
            print(f"  Y範囲: {min(ly_vals):.2f} - {max(ly_vals):.2f}")
            print(f"  Z範囲: {min(lz_vals):.2f} - {max(lz_vals):.2f}")
            print(f"  到達可能点数: {len(left_reachable)}")

            # Best positions by Z
            print("\n  Z別最良位置:")
            for z in z_range:
                z_positions = [(x, y, e) for x, y, zv, e in left_reachable if zv == z]
                if z_positions:
                    best = min(z_positions, key=lambda p: p[2])
                    print(f"    Z={z:.2f}: ({best[0]:.2f}, {best[1]:.2f}) = {best[2]*100:.1f}cm")
                else:
                    print(f"    Z={z:.2f}: 到達不可")
        else:
            print("  2cm以内に到達できる位置なし")

        # Right arm reachable region
        print("\n## 右アーム到達可能領域 (<2cm誤差)")
        right_reachable = []
        for z in z_range:
            for yi, y in enumerate(right_y_range):
                for xi, x in enumerate(x_range):
                    if right_results[z][yi, xi] < THRESHOLD:
                        right_reachable.append((x, y, z, right_results[z][yi, xi]))

        if right_reachable:
            rx_vals = [p[0] for p in right_reachable]
            ry_vals = [p[1] for p in right_reachable]
            rz_vals = [p[2] for p in right_reachable]
            print(f"  X範囲: {min(rx_vals):.2f} - {max(rx_vals):.2f}")
            print(f"  Y範囲: {min(ry_vals):.2f} - {max(ry_vals):.2f}")
            print(f"  Z範囲: {min(rz_vals):.2f} - {max(rz_vals):.2f}")
            print(f"  到達可能点数: {len(right_reachable)}")

            # Best positions by Z
            print("\n  Z別最良位置:")
            for z in z_range:
                z_positions = [(x, y, e) for x, y, zv, e in right_reachable if zv == z]
                if z_positions:
                    best = min(z_positions, key=lambda p: p[2])
                    print(f"    Z={z:.2f}: ({best[0]:.2f}, {best[1]:.2f}) = {best[2]*100:.1f}cm")
                else:
                    print(f"    Z={z:.2f}: 到達不可")
        else:
            print("  2cm以内に到達できる位置なし")

        # Z-axis lift capability
        print("\n## Z軸方向の到達可能性（リフト能力）")

        # For each XY position, find achievable Z range
        print("\n左アーム - 各XY位置でのZ到達範囲:")
        for yi, y in enumerate(left_y_range):
            for xi, x in enumerate(x_range):
                z_reachable = []
                for z in z_range:
                    if left_results[z][yi, xi] < 0.05:  # 5cm threshold for lift
                        z_reachable.append(z)
                if z_reachable:
                    y_str = f"{y:+.2f}" if y >= 0 else f"{y:.2f}"
                    print(f"  ({x:.2f}, {y_str}): Z = {min(z_reachable):.2f} - {max(z_reachable):.2f}")

        print("\n右アーム - 各XY位置でのZ到達範囲:")
        for yi, y in enumerate(right_y_range):
            for xi, x in enumerate(x_range):
                z_reachable = []
                for z in z_range:
                    if right_results[z][yi, xi] < 0.05:  # 5cm threshold for lift
                        z_reachable.append(z)
                if z_reachable:
                    y_str = f"{y:+.2f}" if y >= 0 else f"{y:.2f}"
                    print(f"  ({x:.2f}, {y_str}): Z = {min(z_reachable):.2f} - {max(z_reachable):.2f}")

        # Cable task feasibility
        print(f"\n{'='*70}")
        print("ケーブル操作タスクの実現可能性分析")
        print(f"{'='*70}")

        # Find positions where both arms can work
        print("\n## 対角線配置での有効な組み合わせ")

        RELAXED = 0.05  # 5cm threshold
        valid_combos = []

        for z in z_range:
            for lyi, ly in enumerate(left_y_range):
                for lxi, lx in enumerate(x_range):
                    left_err = left_results[z][lyi, lxi]
                    if left_err >= RELAXED:
                        continue

                    for ryi, ry in enumerate(right_y_range):
                        for rxi, rx in enumerate(x_range):
                            right_err = right_results[z][ryi, rxi]
                            if right_err >= RELAXED:
                                continue

                            # Check diagonal constraint
                            if abs(lx - rx) >= 0.05:  # At least 5cm X difference
                                total_err = left_err + right_err
                                valid_combos.append({
                                    'left': (lx, ly, z),
                                    'right': (rx, ry, z),
                                    'left_err': left_err,
                                    'right_err': right_err,
                                    'total_err': total_err,
                                    'z': z
                                })

        if valid_combos:
            # Sort by total error
            valid_combos.sort(key=lambda c: c['total_err'])

            print(f"\n有効な組み合わせ数: {len(valid_combos)}")
            print("\nTop 10 最良組み合わせ:")
            for i, combo in enumerate(valid_combos[:10]):
                lx, ly, lz = combo['left']
                rx, ry, rz = combo['right']
                le = combo['left_err'] * 100
                re = combo['right_err'] * 100
                te = combo['total_err'] * 100
                print(f"  {i+1}. Z={lz:.2f}: L({lx:.2f},{ly:.2f})={le:.1f}cm, R({rx:.2f},{ry:.2f})={re:.1f}cm, 合計={te:.1f}cm")

            # Analyze by Z level
            print("\n各Z高さでの最良組み合わせ:")
            for z in z_range:
                z_combos = [c for c in valid_combos if c['z'] == z]
                if z_combos:
                    best = min(z_combos, key=lambda c: c['total_err'])
                    lx, ly, _ = best['left']
                    rx, ry, _ = best['right']
                    le = best['left_err'] * 100
                    re = best['right_err'] * 100
                    print(f"  Z={z:.2f}: L({lx:.2f},{ly:.2f})={le:.1f}cm <-> R({rx:.2f},{ry:.2f})={re:.1f}cm")
                else:
                    print(f"  Z={z:.2f}: 有効な組み合わせなし")
        else:
            print("\n有効な対角線配置なし（5cm閾値内）")

        # Task feasibility summary
        print(f"\n{'='*70}")
        print("タスク実現可能性サマリー")
        print(f"{'='*70}")

        # Check grasp height (Z ~ 0.80-0.85)
        grasp_z = [z for z in z_range if 0.78 <= z <= 0.87]
        lift_z = [z for z in z_range if z >= 0.90]

        print(f"\n1. 把持高さ (Z≈{TABLE_HEIGHT:.2f}+α):")
        if grasp_z:
            grasp_combos = [c for c in valid_combos if c['z'] in grasp_z]
            if grasp_combos:
                best = min(grasp_combos, key=lambda c: c['total_err'])
                print(f"   可能 - 最良: Z={best['z']:.2f}, 合計誤差={best['total_err']*100:.1f}cm")
            else:
                print("   困難 - 5cm以内の組み合わせなし")
        else:
            print("   テスト範囲外")

        print(f"\n2. リフト高さ (Z≥0.90):")
        if lift_z:
            lift_combos = [c for c in valid_combos if c['z'] in lift_z]
            if lift_combos:
                best = min(lift_combos, key=lambda c: c['total_err'])
                print(f"   可能 - 最良: Z={best['z']:.2f}, 合計誤差={best['total_err']*100:.1f}cm")
            else:
                print("   困難 - 5cm以内の組み合わせなし")
        else:
            print("   テスト範囲外")

        print(f"\n3. 推奨ケーブル配置:")
        if valid_combos:
            # Find best overall
            best = valid_combos[0]
            lx, ly, lz = best['left']
            rx, ry, rz = best['right']

            # Center position for cable/hook
            cx = (lx + rx) / 2
            cy = (ly + ry) / 2

            print(f"   ケーブル左端: ({lx:.2f}, {ly:.2f})")
            print(f"   ケーブル右端: ({rx:.2f}, {ry:.2f})")
            print(f"   ケーブル/フック中心: ({cx:.2f}, {cy:.2f})")
            print(f"   推奨作業高さ: Z={lz:.2f}")
        else:
            print("   現在のロボット配置では対角線配置困難")
            print("   ロボット位置の再検討が必要")


def main():
    # Setup scene
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = 1

    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Initialize
    for _ in range(30):
        sim.step()
    scene.update(sim.get_physics_dt())

    device = scene["robot_left"].device
    tester = GridReachabilityTester3D(scene, sim, device)

    # Grid ranges
    x_range = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    z_range = [0.80, 0.85, 0.90, 0.95, 1.00]

    # Left arm Y range (negative Y side)
    left_y_range = [-0.25, -0.20, -0.15, -0.10, -0.05, 0.00]

    # Right arm Y range (positive Y side)
    right_y_range = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]

    # Test left arm
    left_results = tester.test_3d_grid(
        tester.robot_left, tester.left_ik,
        x_range, left_y_range, z_range,
        "Left", joint0_angle=0.3
    )

    # Print left arm maps
    tester.print_3d_map(left_results, x_range, left_y_range, z_range, "Left")

    # Test right arm
    right_results = tester.test_3d_grid(
        tester.robot_right, tester.right_ik,
        x_range, right_y_range, z_range,
        "Right", joint0_angle=-0.3
    )

    # Print right arm maps
    tester.print_3d_map(right_results, x_range, right_y_range, z_range, "Right")

    # Analyze results
    tester.analyze_results(
        left_results, right_results,
        x_range, left_y_range, right_y_range, z_range
    )

    simulation_app.close()


if __name__ == "__main__":
    main()
