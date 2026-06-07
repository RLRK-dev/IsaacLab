#!/usr/bin/env python3
"""
3D Workspace Mapping Script

Maps the reachable workspace of both Franka Panda arms in XYZ space.

Usage:
    PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/test_workspace_3d.py \
        --headless --enable_cameras
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test 3D Workspace")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
from scipy.spatial.transform import Rotation as R

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import quat_apply

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT
from thread_isaac_lab.configs.task_config import PHYSICS_DT


class WorkspaceMapper:
    """Map the 3D reachable workspace of both robot arms."""

    def __init__(self, scene: InteractiveScene, device: str = "cuda:0"):
        self.scene = scene
        self.device = device

        # Get robot references
        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        # EE frame offset (from panda_hand to fingertip)
        self.ee_offset = torch.tensor([[0.0, 0.0, 0.1123]], device=device)

        # IK controllers
        ik_cfg = DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="dls",
            ik_params={"lambda_val": 0.02},
        )
        self.ik_left = DifferentialIKController(ik_cfg, num_envs=1, device=device)
        self.ik_right = DifferentialIKController(ik_cfg, num_envs=1, device=device)

        # Gripper orientation (pointing down)
        euler = R.from_euler('xyz', [180, 0, 0], degrees=True)
        quat_xyzw = euler.as_quat()
        self.gripper_quat = torch.tensor([[quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]],
                                         device=device, dtype=torch.float32)

        # Joint indices
        self.arm_joint_ids_left = self.robot_left.find_joints("panda_joint.*")[0][:7]
        self.arm_joint_ids_right = self.robot_right.find_joints("panda_joint.*")[0][:7]

        # Jacobian body indices
        self.jacobian_body_idx_left = self.robot_left.find_bodies("panda_hand")[0][0]
        self.jacobian_body_idx_right = self.robot_right.find_bodies("panda_hand")[0][0]

        # Results storage
        self.left_results = {}  # (x, y, z) -> error
        self.right_results = {}

    def get_ee_pose(self, robot, jacobian_body_idx):
        """Get current end-effector pose."""
        ee_pos_w = robot.data.body_pos_w[:, jacobian_body_idx]
        ee_quat_w = robot.data.body_quat_w[:, jacobian_body_idx]

        # Apply fingertip offset
        offset_world = quat_apply(ee_quat_w, self.ee_offset)
        ee_pos_w = ee_pos_w + offset_world

        return ee_pos_w, ee_quat_w

    def reset_arm(self, robot, is_left: bool):
        """Reset single arm to home position."""
        if is_left:
            home = torch.tensor([[0.3, -0.8, 0.0, -2.2, 0.0, 2.0, 0.785, 0.04, 0.04]], device=self.device)
        else:
            home = torch.tensor([[-0.3, -0.8, 0.0, -2.2, 0.0, 2.0, -0.785, 0.04, 0.04]], device=self.device)

        robot.set_joint_position_target(home)
        robot.write_data_to_sim()

        for _ in range(15):
            sim_utils.SimulationContext.instance().step(render=False)
            self.scene.update(sim_utils.SimulationContext.instance().get_physics_dt())

    def move_arm_to_target(self, robot, ik_controller, arm_joint_ids, jacobian_body_idx,
                           target_pos: torch.Tensor, max_steps: int = 80) -> float:
        """Move single arm to target position and return final position error."""

        target_pose = torch.cat([target_pos, self.gripper_quat], dim=-1)
        ik_controller.set_command(target_pose)

        for step in range(max_steps):
            ee_pos, ee_quat = self.get_ee_pose(robot, jacobian_body_idx)
            jacobian = robot.root_physx_view.get_jacobians()[:, jacobian_body_idx, :, :7]
            joint_pos = robot.data.joint_pos[:, arm_joint_ids]

            joint_pos_des = ik_controller.compute(ee_pos, ee_quat, jacobian, joint_pos)

            targets = robot.data.joint_pos_target.clone()
            targets[:, arm_joint_ids] = joint_pos_des
            robot.set_joint_position_target(targets)
            robot.write_data_to_sim()

            sim_utils.SimulationContext.instance().step(render=False)
            self.scene.update(sim_utils.SimulationContext.instance().get_physics_dt())

        # Return final error
        ee_pos, _ = self.get_ee_pose(robot, jacobian_body_idx)
        return torch.norm(ee_pos - target_pos).item()

    def test_point(self, x: float, y: float, z: float, is_left: bool) -> float:
        """Test a single point and return position error."""
        if is_left:
            self.reset_arm(self.robot_left, True)
            target = torch.tensor([[x, y, z]], device=self.device)
            err = self.move_arm_to_target(
                self.robot_left, self.ik_left, self.arm_joint_ids_left,
                self.jacobian_body_idx_left, target
            )
            self.left_results[(x, y, z)] = err
        else:
            self.reset_arm(self.robot_right, False)
            target = torch.tensor([[x, y, z]], device=self.device)
            err = self.move_arm_to_target(
                self.robot_right, self.ik_right, self.arm_joint_ids_right,
                self.jacobian_body_idx_right, target
            )
            self.right_results[(x, y, z)] = err
        return err

    def error_to_symbol(self, err: float) -> str:
        """Convert error to symbol."""
        if err < 0.02:
            return "○"
        elif err < 0.05:
            return "△"
        else:
            return "×"

    def run_mapping(self):
        """Run the full 3D workspace mapping."""

        # Grid definition
        X_vals = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
        Y_left = [-0.30, -0.20, -0.10, 0.00]  # Left arm tests Y <= 0
        Y_right = [0.00, 0.10, 0.20, 0.30]     # Right arm tests Y >= 0
        Z_vals = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05]

        print("=" * 80, flush=True)
        print("3D WORKSPACE MAPPING", flush=True)
        print(f"TABLE_HEIGHT = {TABLE_HEIGHT}", flush=True)
        print("=" * 80, flush=True)

        # Test left arm
        print("\n### 左アーム到達可能マップ", flush=True)
        total_left = len(X_vals) * len(Y_left) * len(Z_vals)
        count = 0

        for z in Z_vals:
            print(f"\nZ={z:.2f}:", flush=True)
            print("Y\\X   " + "  ".join(f"{x:.2f}" for x in X_vals), flush=True)
            print("-" * (6 + len(X_vals) * 6), flush=True)

            for y in Y_left:
                row = f"{y:+.2f} "
                for x in X_vals:
                    count += 1
                    print(f"  [Left {count}/{total_left}] Testing ({x:.2f}, {y:.2f}, {z:.2f})...", end="\r", flush=True)
                    err = self.test_point(x, y, z, is_left=True)
                    row += f"  {self.error_to_symbol(err)}  "
                print(row, flush=True)

        # Test right arm
        print("\n### 右アーム到達可能マップ", flush=True)
        total_right = len(X_vals) * len(Y_right) * len(Z_vals)
        count = 0

        for z in Z_vals:
            print(f"\nZ={z:.2f}:", flush=True)
            print("Y\\X   " + "  ".join(f"{x:.2f}" for x in X_vals), flush=True)
            print("-" * (6 + len(X_vals) * 6), flush=True)

            for y in Y_right:
                row = f"{y:+.2f} "
                for x in X_vals:
                    count += 1
                    print(f"  [Right {count}/{total_right}] Testing ({x:.2f}, {y:.2f}, {z:.2f})...", end="\r", flush=True)
                    err = self.test_point(x, y, z, is_left=False)
                    row += f"  {self.error_to_symbol(err)}  "
                print(row, flush=True)

        # Summary
        self.print_summary(X_vals, Y_left, Y_right, Z_vals)

    def print_summary(self, X_vals, Y_left, Y_right, Z_vals):
        """Print summary of reachable regions."""

        print("\n" + "=" * 80, flush=True)
        print("SUMMARY - 結果サマリー", flush=True)
        print("=" * 80, flush=True)

        # Find reachable regions (error < 2cm)
        left_reachable = [(k, v) for k, v in self.left_results.items() if v < 0.02]
        right_reachable = [(k, v) for k, v in self.right_results.items() if v < 0.02]

        # Left arm analysis
        print("\n### 1. 左アーム到達可能領域", flush=True)
        if left_reachable:
            x_min = min(p[0] for p, _ in left_reachable)
            x_max = max(p[0] for p, _ in left_reachable)
            y_min = min(p[1] for p, _ in left_reachable)
            y_max = max(p[1] for p, _ in left_reachable)
            z_min = min(p[2] for p, _ in left_reachable)
            z_max = max(p[2] for p, _ in left_reachable)
            print(f"   X: {x_min:.2f} ~ {x_max:.2f}", flush=True)
            print(f"   Y: {y_min:.2f} ~ {y_max:.2f}", flush=True)
            print(f"   Z: {z_min:.2f} ~ {z_max:.2f}", flush=True)
            print(f"   到達可能点数: {len(left_reachable)}/{len(self.left_results)}", flush=True)
        else:
            print("   到達可能領域なし (2cm閾値)", flush=True)
            # Show best results
            if self.left_results:
                best = min(self.left_results.items(), key=lambda x: x[1])
                print(f"   最小誤差: {best[1]*100:.1f}cm at {best[0]}", flush=True)

        # Right arm analysis
        print("\n### 2. 右アーム到達可能領域", flush=True)
        if right_reachable:
            x_min = min(p[0] for p, _ in right_reachable)
            x_max = max(p[0] for p, _ in right_reachable)
            y_min = min(p[1] for p, _ in right_reachable)
            y_max = max(p[1] for p, _ in right_reachable)
            z_min = min(p[2] for p, _ in right_reachable)
            z_max = max(p[2] for p, _ in right_reachable)
            print(f"   X: {x_min:.2f} ~ {x_max:.2f}", flush=True)
            print(f"   Y: {y_min:.2f} ~ {y_max:.2f}", flush=True)
            print(f"   Z: {z_min:.2f} ~ {z_max:.2f}", flush=True)
            print(f"   到達可能点数: {len(right_reachable)}/{len(self.right_results)}", flush=True)
        else:
            print("   到達可能領域なし (2cm閾値)", flush=True)
            if self.right_results:
                best = min(self.right_results.items(), key=lambda x: x[1])
                print(f"   最小誤差: {best[1]*100:.1f}cm at {best[0]}", flush=True)

        # Common reachable region
        print("\n### 3. 両アーム共通到達可能領域", flush=True)
        # Find X, Z where both can reach at their respective Y positions
        left_xz = {(p[0], p[2]) for p, _ in left_reachable}
        right_xz = {(p[0], p[2]) for p, _ in right_reachable}
        common_xz = left_xz & right_xz

        if common_xz:
            x_common = sorted(set(p[0] for p in common_xz))
            z_common = sorted(set(p[1] for p in common_xz))
            print(f"   共通X範囲: {min(x_common):.2f} ~ {max(x_common):.2f}", flush=True)
            print(f"   共通Z範囲: {min(z_common):.2f} ~ {max(z_common):.2f}", flush=True)
        else:
            print("   共通領域なし", flush=True)

        # Task feasibility
        print("\n### 4. タスク実行可能位置", flush=True)

        # For cable grasping: need to reach cable ends at Y=±0.15 (or adjusted)
        # For lifting: need to reach Z ~ 0.90-1.00
        # For hook: need to reach center at Y~0

        # Find points suitable for each phase
        left_grasp = [(p, e) for p, e in self.left_results.items()
                      if p[1] <= -0.10 and p[2] < 0.85 and e < 0.05]
        right_grasp = [(p, e) for p, e in self.right_results.items()
                       if p[1] >= 0.10 and p[2] < 0.85 and e < 0.05]

        left_lift = [(p, e) for p, e in self.left_results.items()
                     if p[2] >= 0.90 and e < 0.05]
        right_lift = [(p, e) for p, e in self.right_results.items()
                      if p[2] >= 0.90 and e < 0.05]

        left_hook = [(p, e) for p, e in self.left_results.items()
                     if -0.05 <= p[1] <= 0.05 and e < 0.05]
        right_hook = [(p, e) for p, e in self.right_results.items()
                      if -0.05 <= p[1] <= 0.05 and e < 0.05]

        print(f"\n   掴み位置 (5cm閾値):", flush=True)
        if left_grasp:
            best_l = min(left_grasp, key=lambda x: x[1])
            print(f"     左: {best_l[0]} (誤差 {best_l[1]*100:.1f}cm)", flush=True)
        else:
            print(f"     左: 到達不可", flush=True)
        if right_grasp:
            best_r = min(right_grasp, key=lambda x: x[1])
            print(f"     右: {best_r[0]} (誤差 {best_r[1]*100:.1f}cm)", flush=True)
        else:
            print(f"     右: 到達不可", flush=True)

        print(f"\n   リフト位置 (Z>=0.90, 5cm閾値):", flush=True)
        if left_lift:
            best_l = min(left_lift, key=lambda x: x[1])
            print(f"     左: {best_l[0]} (誤差 {best_l[1]*100:.1f}cm)", flush=True)
        else:
            print(f"     左: 到達不可", flush=True)
        if right_lift:
            best_r = min(right_lift, key=lambda x: x[1])
            print(f"     右: {best_r[0]} (誤差 {best_r[1]*100:.1f}cm)", flush=True)
        else:
            print(f"     右: 到達不可", flush=True)

        print(f"\n   フック位置 (Y~0, 5cm閾値):", flush=True)
        if left_hook:
            best_l = min(left_hook, key=lambda x: x[1])
            print(f"     左: {best_l[0]} (誤差 {best_l[1]*100:.1f}cm)", flush=True)
        else:
            print(f"     左: 到達不可", flush=True)
        if right_hook:
            best_r = min(right_hook, key=lambda x: x[1])
            print(f"     右: {best_r[0]} (誤差 {best_r[1]*100:.1f}cm)", flush=True)
        else:
            print(f"     右: 到達不可", flush=True)

        # Final recommendation
        print("\n### 5. 推奨構成", flush=True)
        can_grasp = len(left_grasp) > 0 and len(right_grasp) > 0
        can_lift = len(left_lift) > 0 and len(right_lift) > 0
        can_hook = len(left_hook) > 0 and len(right_hook) > 0

        if can_grasp and can_lift and can_hook:
            print("   タスク実行可能", flush=True)

            # Recommend cable position
            if left_grasp and right_grasp:
                best_l_grasp = min(left_grasp, key=lambda x: x[1])
                best_r_grasp = min(right_grasp, key=lambda x: x[1])
                avg_x = (best_l_grasp[0][0] + best_r_grasp[0][0]) / 2
                print(f"   推奨ケーブル位置: X={avg_x:.2f}, Y=0 (中心)", flush=True)
                print(f"     左端: Y={best_l_grasp[0][1]:.2f}", flush=True)
                print(f"     右端: Y={best_r_grasp[0][1]:.2f}", flush=True)
        else:
            print("   タスク実行不可能（5cm閾値）", flush=True)
            issues = []
            if not can_grasp:
                issues.append("掴み位置に到達不可")
            if not can_lift:
                issues.append("リフト位置に到達不可")
            if not can_hook:
                issues.append("フック位置に到達不可")
            print(f"   理由: {', '.join(issues)}", flush=True)

        print("\n" + "=" * 80, flush=True)
        print("凡例: ○ = <2cm, △ = 2-5cm, × = >5cm", flush=True)
        print("=" * 80, flush=True)


def main():
    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(
        device="cuda:0",
        dt=PHYSICS_DT,
        render_interval=1,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([2.0, 0.0, 2.0], [0.4, 0.0, 0.75])

    # Create scene
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)
    scene = InteractiveScene(scene_cfg)

    # Initialize
    sim.reset()
    scene.reset()

    # Warm up
    print("Warming up simulation...", flush=True)
    for _ in range(50):
        sim.step(render=False)
        scene.update(sim.get_physics_dt())

    # Run mapping
    mapper = WorkspaceMapper(scene, device="cuda:0")
    mapper.run_mapping()

    # Cleanup
    simulation_app.close()


if __name__ == "__main__":
    main()
