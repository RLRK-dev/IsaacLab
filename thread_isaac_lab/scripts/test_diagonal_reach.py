#!/usr/bin/env python3
"""
Diagonal Reachability Test Script

Test if both robot arms can reach diagonal cable placement positions.
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test Diagonal Reachability")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
from typing import Dict, Tuple, List
from scipy.spatial.transform import Rotation as R

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT


class ReachabilityTester:
    """Test IK reachability for both arms."""

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

    def fingertip_to_panda_hand(self, fingertip_z: float) -> float:
        """Convert fingertip Z to panda_hand Z."""
        return fingertip_z + self.ee_offset

    def compute_ik_and_move(self, robot, ik_controller, target_pos, max_steps=200):
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
        return pos_error, ee_pos_w[0].cpu().tolist()

    def test_position(self, left_fingertip: Tuple[float, float, float],
                      right_fingertip: Tuple[float, float, float],
                      pattern_name: str) -> Dict:
        """Test if both arms can reach specified positions.

        Args:
            left_fingertip: (X, Y, Z) fingertip target for left arm
            right_fingertip: (X, Y, Z) fingertip target for right arm
            pattern_name: Name for logging

        Returns:
            Dict with test results
        """
        print(f"\n{'='*60}")
        print(f"Testing: {pattern_name}")
        print(f"{'='*60}")

        # Convert fingertip to panda_hand targets
        left_target = torch.tensor([[
            left_fingertip[0],
            left_fingertip[1],
            self.fingertip_to_panda_hand(left_fingertip[2])
        ]], device=self.device)

        right_target = torch.tensor([[
            right_fingertip[0],
            right_fingertip[1],
            self.fingertip_to_panda_hand(right_fingertip[2])
        ]], device=self.device)

        print(f"  Left fingertip target:  ({left_fingertip[0]:.2f}, {left_fingertip[1]:.2f}, {left_fingertip[2]:.2f})")
        print(f"  Right fingertip target: ({right_fingertip[0]:.2f}, {right_fingertip[1]:.2f}, {right_fingertip[2]:.2f})")
        print(f"  Left panda_hand target:  {left_target[0].cpu().tolist()}")
        print(f"  Right panda_hand target: {right_target[0].cpu().tolist()}")

        # Test left arm
        print(f"  Testing left arm...")
        left_error, left_final = self.compute_ik_and_move(
            self.robot_left, self.left_ik, left_target, max_steps=150
        )

        # Test right arm
        print(f"  Testing right arm...")
        right_error, right_final = self.compute_ik_and_move(
            self.robot_right, self.right_ik, right_target, max_steps=150
        )

        # Check success (threshold: 3cm)
        THRESHOLD = 0.03
        left_ok = left_error < THRESHOLD
        right_ok = right_error < THRESHOLD
        both_ok = left_ok and right_ok

        print(f"\n  Results:")
        print(f"    Left:  error={left_error*100:.1f}cm {'OK' if left_ok else 'NG'}")
        print(f"    Right: error={right_error*100:.1f}cm {'OK' if right_ok else 'NG'}")
        print(f"    Both OK: {'YES' if both_ok else 'NO'}")

        return {
            'pattern': pattern_name,
            'left_target': left_fingertip,
            'right_target': right_fingertip,
            'left_error': left_error,
            'right_error': right_error,
            'left_ok': left_ok,
            'right_ok': right_ok,
            'both_ok': both_ok,
        }

    def reset_arms(self):
        """Reset arms to ready position."""
        ready_joint_pos = torch.tensor([
            [0.0, -0.4, 0.0, -2.0, 0.0, 1.6, 0.785, 0.04, 0.04]
        ], device=self.device)

        left_joint = ready_joint_pos.clone()
        left_joint[0, 0] = 0.3

        right_joint = ready_joint_pos.clone()
        right_joint[0, 0] = -0.3

        for _ in range(50):
            self.robot_left.set_joint_position_target(left_joint)
            self.robot_right.set_joint_position_target(right_joint)
            self.step_sim(4)


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
    tester = ReachabilityTester(scene, sim, device)

    # Define test patterns
    # Z = TABLE_HEIGHT + 0.03 for grasp position (fingertip 3cm above table)
    GRASP_Z = TABLE_HEIGHT + 0.03
    LIFT_Z = TABLE_HEIGHT + 0.15

    test_patterns = [
        # Diagonal pattern 1: Left back -> Right front
        ("Diagonal 1 (L:back, R:front)",
         (0.30, -0.10, GRASP_Z),
         (0.40, +0.10, GRASP_Z)),

        # Diagonal pattern 2: Left front -> Right back
        ("Diagonal 2 (L:front, R:back)",
         (0.40, -0.10, GRASP_Z),
         (0.30, +0.10, GRASP_Z)),

        # Diagonal pattern 3: More outside
        ("Diagonal 3 (wider)",
         (0.30, -0.15, GRASP_Z),
         (0.40, +0.15, GRASP_Z)),

        # Diagonal pattern 4: More centered
        ("Diagonal 4 (centered)",
         (0.35, -0.05, GRASP_Z),
         (0.35, +0.05, GRASP_Z)),

        # Diagonal pattern 1 + Lift
        ("Diagonal 1 + Lift",
         (0.30, -0.10, LIFT_Z),
         (0.40, +0.10, LIFT_Z)),

        # Y-axis reference (current approach)
        ("Y-axis (X=0.40)",
         (0.40, -0.12, GRASP_Z),
         (0.40, +0.12, GRASP_Z)),

        # Y-axis with X=0.35
        ("Y-axis (X=0.35)",
         (0.35, -0.12, GRASP_Z),
         (0.35, +0.12, GRASP_Z)),
    ]

    results = []

    for pattern_name, left_pos, right_pos in test_patterns:
        # Reset arms before each test
        tester.reset_arms()
        result = tester.test_position(left_pos, right_pos, pattern_name)
        results.append(result)

    # Print summary table
    print(f"\n{'='*80}")
    print("SUMMARY TABLE")
    print(f"{'='*80}")
    print(f"| {'Pattern':<30} | {'Left Pos':<18} | {'Right Pos':<18} | {'L Err':>6} | {'R Err':>6} | {'OK?':>5} |")
    print(f"|{'-'*32}|{'-'*20}|{'-'*20}|{'-'*8}|{'-'*8}|{'-'*7}|")

    for r in results:
        left_str = f"({r['left_target'][0]:.2f},{r['left_target'][1]:.2f})"
        right_str = f"({r['right_target'][0]:.2f},{r['right_target'][1]:.2f})"
        ok_str = "YES" if r['both_ok'] else "NO"
        print(f"| {r['pattern']:<30} | {left_str:<18} | {right_str:<18} | {r['left_error']*100:>5.1f}cm | {r['right_error']*100:>5.1f}cm | {ok_str:>5} |")

    print(f"{'='*80}")

    # Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    successful = [r for r in results if r['both_ok']]
    if successful:
        print(f"\nSuccessful patterns ({len(successful)}):")
        for r in successful:
            print(f"  - {r['pattern']}")

        # Find best pattern (lowest combined error)
        best = min(successful, key=lambda x: x['left_error'] + x['right_error'])
        print(f"\nBest pattern: {best['pattern']}")
        print(f"  Combined error: {(best['left_error'] + best['right_error'])*100:.1f}cm")
    else:
        print("\nNo patterns achieved both arms within threshold!")
        # Find closest
        best = min(results, key=lambda x: x['left_error'] + x['right_error'])
        print(f"Closest pattern: {best['pattern']}")
        print(f"  Left error: {best['left_error']*100:.1f}cm")
        print(f"  Right error: {best['right_error']*100:.1f}cm")

    # Diagonal vs Y-axis comparison
    diagonal_results = [r for r in results if 'Diagonal' in r['pattern'] and 'Lift' not in r['pattern']]
    yaxis_results = [r for r in results if 'Y-axis' in r['pattern']]

    if diagonal_results and yaxis_results:
        diag_avg = sum(r['left_error'] + r['right_error'] for r in diagonal_results) / len(diagonal_results)
        yaxis_avg = sum(r['left_error'] + r['right_error'] for r in yaxis_results) / len(yaxis_results)

        print(f"\nDiagonal avg combined error: {diag_avg*100:.1f}cm")
        print(f"Y-axis avg combined error: {yaxis_avg*100:.1f}cm")

        if diag_avg < yaxis_avg:
            print("-> Diagonal placement is easier to reach")
        else:
            print("-> Y-axis placement is easier to reach")

    simulation_app.close()


if __name__ == "__main__":
    main()
