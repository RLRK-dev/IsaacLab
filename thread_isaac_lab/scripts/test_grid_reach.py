#!/usr/bin/env python3
"""
Grid-based Reachability Test Script

Measure reachable area for both robot arms on an XY grid.
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test Grid Reachability")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
from typing import Tuple, List
from scipy.spatial.transform import Rotation as R

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT


class GridReachabilityTester:
    """Test IK reachability on a grid for both arms."""

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

        for _ in range(30):
            robot.set_joint_position_target(ready_joint_pos)
            self.step_sim(4)

        ik_controller.reset()

    def test_single_position(self, robot, ik_controller, target_pos, max_steps=100):
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

    def test_grid(self, robot, ik_controller, x_range: List[float], y_range: List[float],
                  z_height: float, arm_name: str, joint0_angle: float) -> np.ndarray:
        """Test reachability on a grid."""
        print(f"\n{'='*60}")
        print(f"Testing {arm_name} arm reachability grid")
        print(f"{'='*60}")
        print(f"X range: {x_range}")
        print(f"Y range: {y_range}")
        print(f"Z (panda_hand): {z_height:.3f}")

        results = np.zeros((len(y_range), len(x_range)))

        for yi, y in enumerate(y_range):
            row_results = []
            for xi, x in enumerate(x_range):
                # Reset arm before each test
                self.reset_arm(robot, ik_controller, joint0_angle)

                target = torch.tensor([[x, y, z_height]], device=self.device)
                error = self.test_single_position(robot, ik_controller, target, max_steps=80)
                results[yi, xi] = error

                # Status indicator
                if error < 0.02:
                    status = "○"
                elif error < 0.05:
                    status = "△"
                else:
                    status = "×"
                row_results.append(f"{error*100:.1f}")
                print(f"  ({x:.2f}, {y:.2f}): {error*100:.1f}cm {status}")

        return results

    def print_map(self, results: np.ndarray, x_range: List[float], y_range: List[float], arm_name: str):
        """Print reachability map."""
        print(f"\n{arm_name} Arm Reachability Map:")
        print(f"(○=<2cm, △=2-5cm, ×=>5cm)")

        # Header
        header = "Y\\X   "
        for x in x_range:
            header += f" {x:.2f} "
        print(header)

        # Rows
        for yi, y in enumerate(y_range):
            row = f"{y:+.2f} "
            for xi in range(len(x_range)):
                err = results[yi, xi]
                if err < 0.02:
                    row += "  ○   "
                elif err < 0.05:
                    row += "  △   "
                else:
                    row += "  ×   "
            print(row)


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
    tester = GridReachabilityTester(scene, sim, device)

    # Z height: fingertip at 3cm above table -> panda_hand at 3cm + 10.7cm
    PANDA_HAND_Z = TABLE_HEIGHT + 0.03 + 0.1123

    # Grid ranges
    x_range = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]

    # Left arm Y range (negative Y side)
    left_y_range = [-0.20, -0.15, -0.10, -0.05, 0.00]

    # Right arm Y range (positive Y side)
    right_y_range = [0.00, 0.05, 0.10, 0.15, 0.20]

    # Test left arm
    left_results = tester.test_grid(
        tester.robot_left, tester.left_ik,
        x_range, left_y_range, PANDA_HAND_Z,
        "Left", joint0_angle=0.3
    )

    # Print left arm map
    tester.print_map(left_results, x_range, left_y_range, "Left")

    # Test right arm
    right_results = tester.test_grid(
        tester.robot_right, tester.right_ik,
        x_range, right_y_range, PANDA_HAND_Z,
        "Right", joint0_angle=-0.3
    )

    # Print right arm map
    tester.print_map(right_results, x_range, right_y_range, "Right")

    # Analysis
    print(f"\n{'='*60}")
    print("ANALYSIS")
    print(f"{'='*60}")

    THRESHOLD = 0.02  # 2cm

    # Find reachable regions for left arm
    print("\nLeft Arm Reachable Positions (<2cm error):")
    left_reachable = []
    for yi, y in enumerate(left_y_range):
        for xi, x in enumerate(x_range):
            if left_results[yi, xi] < THRESHOLD:
                left_reachable.append((x, y))
                print(f"  ({x:.2f}, {y:.2f}): {left_results[yi, xi]*100:.1f}cm")

    # Find reachable regions for right arm
    print("\nRight Arm Reachable Positions (<2cm error):")
    right_reachable = []
    for yi, y in enumerate(right_y_range):
        for xi, x in enumerate(x_range):
            if right_results[yi, xi] < THRESHOLD:
                right_reachable.append((x, y))
                print(f"  ({x:.2f}, {y:.2f}): {right_results[yi, xi]*100:.1f}cm")

    # Find valid diagonal combinations
    print("\n" + "="*60)
    print("VALID DIAGONAL CABLE PLACEMENTS")
    print("="*60)
    print("(Left end position, Right end position)")

    valid_combos = []
    for lx, ly in left_reachable:
        for rx, ry in right_reachable:
            # Check diagonal constraint: different X positions
            if abs(lx - rx) >= 0.05:  # At least 5cm X difference
                valid_combos.append(((lx, ly), (rx, ry)))
                print(f"  Left:({lx:.2f},{ly:.2f}) <-> Right:({rx:.2f},{ry:.2f})")

    if not valid_combos:
        print("  No valid diagonal combinations found!")
        # Show closest combinations
        print("\nClosest combinations (relaxed threshold):")
        RELAXED = 0.05
        for yi, y in enumerate(left_y_range):
            for xi, x in enumerate(x_range):
                if left_results[yi, xi] < RELAXED:
                    for yj, yr in enumerate(right_y_range):
                        for xj, xr in enumerate(x_range):
                            if right_results[yj, xj] < RELAXED and abs(x - xr) >= 0.05:
                                le = left_results[yi, xi] * 100
                                re = right_results[yj, xj] * 100
                                print(f"  L:({x:.2f},{y:.2f})={le:.1f}cm, R:({xr:.2f},{yr:.2f})={re:.1f}cm")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if left_reachable:
        lx_vals = [p[0] for p in left_reachable]
        ly_vals = [p[1] for p in left_reachable]
        print(f"Left arm reachable: X={min(lx_vals):.2f}-{max(lx_vals):.2f}, Y={min(ly_vals):.2f}-{max(ly_vals):.2f}")
    else:
        print("Left arm: No positions within 2cm threshold")

    if right_reachable:
        rx_vals = [p[0] for p in right_reachable]
        ry_vals = [p[1] for p in right_reachable]
        print(f"Right arm reachable: X={min(rx_vals):.2f}-{max(rx_vals):.2f}, Y={min(ry_vals):.2f}-{max(ry_vals):.2f}")
    else:
        print("Right arm: No positions within 2cm threshold")

    print(f"\nValid diagonal combinations: {len(valid_combos)}")

    simulation_app.close()


if __name__ == "__main__":
    main()
