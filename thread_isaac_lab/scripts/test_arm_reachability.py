#!/usr/bin/env python3
"""
Arm Reachability Test Script

NOTE: Run with PYTHONUNBUFFERED=1 to see output in real-time

Tests the reachable workspace for both Franka Panda arms to determine
optimal cable and hook placement for the draping task.

Usage:
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/test_arm_reachability.py \
        --headless --enable_cameras
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test Arm Reachability")
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

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT
from thread_isaac_lab.configs.task_config import PHYSICS_DT


class ReachabilityTester:
    """Test reachability of both robot arms."""

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

        # Gripper orientation (fingers perpendicular to cable, pointing down)
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
        self.results = []

    def get_ee_pose(self, robot, jacobian_body_idx):
        """Get current end-effector pose."""
        ee_pos_w = robot.data.body_pos_w[:, jacobian_body_idx]
        ee_quat_w = robot.data.body_quat_w[:, jacobian_body_idx]

        # Apply fingertip offset
        from isaaclab.utils.math import quat_rotate
        offset_world = quat_rotate(ee_quat_w, self.ee_offset)
        ee_pos_w = ee_pos_w + offset_world

        return ee_pos_w, ee_quat_w

    def move_to_target(self, robot, ik_controller, arm_joint_ids, jacobian_body_idx,
                       target_pos: torch.Tensor, max_steps: int = 100,
                       threshold: float = 0.005) -> float:
        """Move arm to target position and return final position error."""

        target_pose = torch.cat([target_pos, self.gripper_quat], dim=-1)
        ik_controller.set_command(target_pose)

        for step in range(max_steps):
            # Get current state
            ee_pos, ee_quat = self.get_ee_pose(robot, jacobian_body_idx)
            jacobian = robot.root_physx_view.get_jacobians()[:, jacobian_body_idx, :, :7]
            joint_pos = robot.data.joint_pos[:, arm_joint_ids]

            # Compute IK
            joint_pos_des = ik_controller.compute(ee_pos, ee_quat, jacobian, joint_pos)

            # Apply
            current_targets = robot.data.joint_pos_target.clone()
            current_targets[:, arm_joint_ids] = joint_pos_des
            robot.set_joint_position_target(current_targets)
            robot.write_data_to_sim()

            # Step simulation
            sim_utils.SimulationContext.instance().step(render=False)
            self.scene.update(sim_utils.SimulationContext.instance().get_physics_dt())

            # Check convergence
            pos_error = torch.norm(ee_pos - target_pos).item()
            if pos_error < threshold:
                break

        # Return final error
        ee_pos, _ = self.get_ee_pose(robot, jacobian_body_idx)
        return torch.norm(ee_pos - target_pos).item()

    def reset_arms(self):
        """Reset arms to home position."""
        # Home joint positions
        home_left = torch.tensor([[0.3, -0.8, 0.0, -2.2, 0.0, 2.0, 0.785, 0.04, 0.04]], device=self.device)
        home_right = torch.tensor([[-0.3, -0.8, 0.0, -2.2, 0.0, 2.0, -0.785, 0.04, 0.04]], device=self.device)

        self.robot_left.set_joint_position_target(home_left)
        self.robot_right.set_joint_position_target(home_right)
        self.robot_left.write_data_to_sim()
        self.robot_right.write_data_to_sim()

        # Settle
        for _ in range(20):
            sim_utils.SimulationContext.instance().step(render=False)
            self.scene.update(sim_utils.SimulationContext.instance().get_physics_dt())

    def move_both_arms(self, left_target: torch.Tensor, right_target: torch.Tensor,
                       max_steps: int = 50) -> tuple:
        """Move both arms simultaneously and return final position errors."""

        left_pose = torch.cat([left_target, self.gripper_quat], dim=-1)
        right_pose = torch.cat([right_target, self.gripper_quat], dim=-1)
        self.ik_left.set_command(left_pose)
        self.ik_right.set_command(right_pose)

        for step in range(max_steps):
            # Left arm
            ee_pos_l, ee_quat_l = self.get_ee_pose(self.robot_left, self.jacobian_body_idx_left)
            jacobian_l = self.robot_left.root_physx_view.get_jacobians()[:, self.jacobian_body_idx_left, :, :7]
            joint_pos_l = self.robot_left.data.joint_pos[:, self.arm_joint_ids_left]
            joint_pos_des_l = self.ik_left.compute(ee_pos_l, ee_quat_l, jacobian_l, joint_pos_l)

            # Right arm
            ee_pos_r, ee_quat_r = self.get_ee_pose(self.robot_right, self.jacobian_body_idx_right)
            jacobian_r = self.robot_right.root_physx_view.get_jacobians()[:, self.jacobian_body_idx_right, :, :7]
            joint_pos_r = self.robot_right.data.joint_pos[:, self.arm_joint_ids_right]
            joint_pos_des_r = self.ik_right.compute(ee_pos_r, ee_quat_r, jacobian_r, joint_pos_r)

            # Apply both
            targets_l = self.robot_left.data.joint_pos_target.clone()
            targets_l[:, self.arm_joint_ids_left] = joint_pos_des_l
            self.robot_left.set_joint_position_target(targets_l)
            self.robot_left.write_data_to_sim()

            targets_r = self.robot_right.data.joint_pos_target.clone()
            targets_r[:, self.arm_joint_ids_right] = joint_pos_des_r
            self.robot_right.set_joint_position_target(targets_r)
            self.robot_right.write_data_to_sim()

            # Step simulation
            sim_utils.SimulationContext.instance().step(render=False)
            self.scene.update(sim_utils.SimulationContext.instance().get_physics_dt())

        # Return final errors
        ee_pos_l, _ = self.get_ee_pose(self.robot_left, self.jacobian_body_idx_left)
        ee_pos_r, _ = self.get_ee_pose(self.robot_right, self.jacobian_body_idx_right)
        left_err = torch.norm(ee_pos_l - left_target).item()
        right_err = torch.norm(ee_pos_r - right_target).item()

        return left_err, right_err

    def test_position(self, test_name: str, left_pos: tuple, right_pos: tuple) -> dict:
        """Test a single position for both arms."""
        self.reset_arms()

        # Convert to tensors
        left_target = torch.tensor([[left_pos[0], left_pos[1], left_pos[2]]], device=self.device)
        right_target = torch.tensor([[right_pos[0], right_pos[1], right_pos[2]]], device=self.device)

        # Test both arms simultaneously
        left_err, right_err = self.move_both_arms(left_target, right_target)

        # Determine if OK (< 1cm error)
        left_ok = left_err < 0.01
        right_ok = right_err < 0.01
        both_ok = left_ok and right_ok

        result = {
            "test": test_name,
            "left_pos": left_pos,
            "right_pos": right_pos,
            "left_err": left_err,
            "right_err": right_err,
            "left_ok": left_ok,
            "right_ok": right_ok,
            "both_ok": both_ok,
        }
        self.results.append(result)

        return result

    def print_result(self, r: dict):
        """Print a single result."""
        left_status = "OK" if r["left_ok"] else "NG"
        right_status = "OK" if r["right_ok"] else "NG"
        both_status = "OK" if r["both_ok"] else "NG"

        print(f"| {r['test']:<20} | ({r['left_pos'][0]:.2f}, {r['left_pos'][1]:.2f}, {r['left_pos'][2]:.2f}) | "
              f"{r['left_err']*100:.1f}cm {left_status} | {r['right_err']*100:.1f}cm {right_status} | {both_status} |", flush=True)

    def run_all_tests(self):
        """Run all reachability tests."""
        import sys

        print("\n" + "="*80, flush=True)
        print("ARM REACHABILITY TEST", flush=True)
        print("="*80, flush=True)

        GRASP_Z = TABLE_HEIGHT + 0.03  # 3cm above table

        # =========================================
        # 1. XY Plane Tests at Grasp Height
        # =========================================
        print("\n### 1. XY平面到達テスト (Z = TABLE_HEIGHT + 0.03)", flush=True)
        print("-" * 80, flush=True)
        print(f"| {'Test':<20} | {'Position (X,Y,Z)':<22} | {'Left Err':<10} | {'Right Err':<10} | {'Both':<5} |", flush=True)
        print("-" * 80, flush=True)

        xy_tests = [
            ("X=0.30,Y=0.15", (0.30, -0.15, GRASP_Z), (0.30, 0.15, GRASP_Z)),
            ("X=0.35,Y=0.15", (0.35, -0.15, GRASP_Z), (0.35, 0.15, GRASP_Z)),
            ("X=0.40,Y=0.15", (0.40, -0.15, GRASP_Z), (0.40, 0.15, GRASP_Z)),
        ]

        for name, left, right in xy_tests:
            r = self.test_position(name, left, right)
            self.print_result(r)

        # =========================================
        # 2. Z Height Tests (Lift)
        # =========================================
        print("\n### 2. リフト高さテスト (X=0.35, Y=±0.10)")
        print("-" * 80)
        print(f"| {'Test':<20} | {'Position (X,Y,Z)':<22} | {'Left Err':<10} | {'Right Err':<10} | {'Both':<5} |")
        print("-" * 80)

        z_tests = [
            ("Z+0.15 (15cm)", (0.35, -0.10, TABLE_HEIGHT + 0.15), (0.35, 0.10, TABLE_HEIGHT + 0.15)),
            ("Z+0.20 (20cm)", (0.35, -0.10, TABLE_HEIGHT + 0.20), (0.35, 0.10, TABLE_HEIGHT + 0.20)),
        ]

        for name, left, right in z_tests:
            r = self.test_position(name, left, right)
            self.print_result(r)

        # =========================================
        # 3. Hook Approach Tests
        # =========================================
        print("\n### 3. フック掛け位置テスト (フック X=0.40, Y=0.0)")
        print("-" * 80)
        print(f"| {'Test':<20} | {'Position (X,Y,Z)':<22} | {'Left Err':<10} | {'Right Err':<10} | {'Both':<5} |")
        print("-" * 80)

        # Hook is at X=0.40, Y=0.0
        HOOK_X = 0.40
        HOOK_Z = TABLE_HEIGHT + 0.12  # Above hook arms

        hook_tests = [
            ("Hook X=0.40", (HOOK_X, -0.03, HOOK_Z), (HOOK_X, 0.03, HOOK_Z)),
            ("Hook X=0.35", (0.35, -0.03, HOOK_Z), (0.35, 0.03, HOOK_Z)),
        ]

        for name, left, right in hook_tests:
            r = self.test_position(name, left, right)
            self.print_result(r)

        # =========================================
        # 4. Find Maximum X Range (reduced)
        # =========================================
        print("\n### 4. X方向最大到達範囲探索", flush=True)
        print("-" * 80, flush=True)

        max_x_both_ok = None
        for x in [0.30, 0.35, 0.40]:
            r = self.test_position(f"X={x:.2f}", (x, -0.10, GRASP_Z), (x, 0.10, GRASP_Z))
            self.print_result(r)
            if r["both_ok"]:
                max_x_both_ok = x

        # =========================================
        # Summary
        # =========================================
        print("\n" + "="*80)
        print("SUMMARY - 結果サマリー")
        print("="*80)

        # Count successes
        grasp_ok = sum(1 for r in self.results if "X=0." in r["test"] and r["both_ok"])
        lift_ok = sum(1 for r in self.results if "Z+" in r["test"] and r["both_ok"])
        hook_ok = sum(1 for r in self.results if "Hook" in r["test"] and r["both_ok"])

        print(f"\n1. 両アームが同時に到達可能なX範囲:")
        if max_x_both_ok:
            print(f"   → X ≤ {max_x_both_ok:.2f}m")
        else:
            print(f"   → 到達可能なX範囲なし")

        # Find best grasp position
        grasp_results = [r for r in self.results if r["test"].startswith("X=0.") and "Hook" not in r["test"]]
        best_grasp = min(grasp_results, key=lambda r: r["left_err"] + r["right_err"]) if grasp_results else None

        print(f"\n2. 推奨ケーブル初期位置:")
        if best_grasp and best_grasp["both_ok"]:
            print(f"   → X={best_grasp['left_pos'][0]:.2f}, Y=0.0 (ケーブル中心)")
            print(f"   → 左端 Y=-0.15, 右端 Y=+0.15")
        else:
            print(f"   → 要調整（到達可能範囲外）")

        print(f"\n3. 推奨フック位置:")
        hook_results = [r for r in self.results if "Hook" in r["test"]]
        best_hook = min(hook_results, key=lambda r: r["left_err"] + r["right_err"]) if hook_results else None
        if best_hook and best_hook["both_ok"]:
            print(f"   → X={best_hook['left_pos'][0]:.2f}, Y=0.0")
        else:
            print(f"   → 要調整（到達可能範囲外）")

        print(f"\n4. タスク実現可能性:")
        # Check all phases
        can_grasp = any(r["both_ok"] for r in self.results if "X=0." in r["test"] and "Hook" not in r["test"])
        can_lift = any(r["both_ok"] for r in self.results if "Z+" in r["test"])
        can_hook = any(r["both_ok"] for r in self.results if "Hook" in r["test"])

        if can_grasp and can_lift and can_hook:
            print("   → YES - タスク実現可能")
            print(f"     - 掴み: ✓")
            print(f"     - 持上げ: ✓")
            print(f"     - フック掛け: ✓")
        else:
            print("   → NO - タスク実現不可能")
            print(f"     - 掴み: {'✓' if can_grasp else '✗'}")
            print(f"     - 持上げ: {'✓' if can_lift else '✗'}")
            print(f"     - フック掛け: {'✗' if not can_hook else '✓'}")
            print(f"     理由: ", end="")
            issues = []
            if not can_grasp:
                issues.append("ケーブル端に到達不可")
            if not can_lift:
                issues.append("リフト高さに到達不可")
            if not can_hook:
                issues.append("フック位置に到達不可")
            print(", ".join(issues))

        print("\n" + "="*80)


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
    for _ in range(50):
        sim.step(render=False)
        scene.update(sim.get_physics_dt())

    # Run tests
    tester = ReachabilityTester(scene, device="cuda:0")
    tester.run_all_tests()

    # Cleanup
    simulation_app.close()


if __name__ == "__main__":
    main()
