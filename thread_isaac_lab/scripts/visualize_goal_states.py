#!/usr/bin/env python3
"""
7フェーズゴール状態可視化スクリプト

各フェーズのゴール状態をIsaac Simで手動作成し、
3カメラ画像をキャプチャして確認する。

Usage:
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/visualize_goal_states.py \
        --headless --enable_cameras

    # GUIモードで確認
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/visualize_goal_states.py \
        --enable_cameras
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Visualize 7-Phase Goal States")
parser.add_argument("--output_dir", type=str, default="data/goal_states", help="Output directory")
parser.add_argument("--settle_steps", type=int, default=60, help="Steps to settle physics")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os
import torch
import numpy as np
from PIL import Image
from datetime import datetime
from typing import Dict, Tuple
from enum import Enum

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT


# =============================================================================
# Task Phases
# =============================================================================

class TaskPhase(Enum):
    """7-phase task state machine for cable draping."""
    REACH_CABLE = 1      # EE reaches cable ends
    GRASP_CABLE = 2      # Gripper grasps cable
    LIFT_CABLE = 3       # Cable lifted above table
    APPROACH_HOOK = 4    # EE reaches hook position
    DRAPE_ON_HOOK = 5    # Cable draped on hook
    RELEASE = 6          # Gripper released
    DONE = 7             # Task complete


PHASE_DESCRIPTIONS = {
    TaskPhase.REACH_CABLE: "両手がケーブル端に接近",
    TaskPhase.GRASP_CABLE: "グリッパーがケーブルを把持",
    TaskPhase.LIFT_CABLE: "ケーブルをテーブルから持ち上げ",
    TaskPhase.APPROACH_HOOK: "フックに接近",
    TaskPhase.DRAPE_ON_HOOK: "ケーブルをフックに掛ける",
    TaskPhase.RELEASE: "グリッパーを解放",
    TaskPhase.DONE: "タスク完了",
}


# =============================================================================
# IK Controller Helper
# =============================================================================

class DualArmIKHelper:
    """IK helper for positioning robots."""

    def __init__(self, scene: InteractiveScene, device: str):
        self.scene = scene
        self.device = device

        # IK configuration
        ik_cfg = DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="dls",
            ik_params={"lambda_val": 0.05},
        )

        self.left_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)
        self.right_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)

        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        self.ee_body_idx = 8
        self.jacobi_body_idx = self.ee_body_idx - 1
        self.arm_joint_ids = list(range(7))
        self.gripper_joint_ids = [7, 8]

        self.default_quat = torch.tensor([[0.0, 0.7071, -0.7071, 0.0]], device=device)  # fingers open in X

    def get_ee_pose(self, robot) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get current EE position and quaternion in world frame."""
        ee_pos_w = robot.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat_w = robot.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos_w, ee_quat_w

    def compute_ik(self, robot, ik_controller, target_pos, target_quat=None):
        """Compute joint positions for target EE pose."""
        if target_quat is None:
            target_quat = self.default_quat

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

        return ik_controller.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

    def set_robot_targets(
        self,
        left_pos: torch.Tensor,
        right_pos: torch.Tensor,
        left_gripper: float,
        right_gripper: float,
    ):
        """Set both robot arm targets with gripper positions."""
        left_joint = self.compute_ik(self.robot_left, self.left_ik, left_pos)
        right_joint = self.compute_ik(self.robot_right, self.right_ik, right_pos)

        left_grip = torch.full((1, 2), left_gripper, device=self.device)
        right_grip = torch.full((1, 2), right_gripper, device=self.device)

        self.robot_left.set_joint_position_target(torch.cat([left_joint, left_grip], dim=-1))
        self.robot_right.set_joint_position_target(torch.cat([right_joint, right_grip], dim=-1))

    def move_to_targets(
        self,
        scene,
        sim,
        left_pos: torch.Tensor,
        right_pos: torch.Tensor,
        left_gripper: float,
        right_gripper: float,
        max_iterations: int = 100,
        position_threshold: float = 0.02,
        steps_per_iter: int = 4,
    ) -> bool:
        """Iteratively move robots to target positions using IK.

        Returns True if targets reached within threshold.
        """
        for iteration in range(max_iterations):
            # Compute IK for current state
            left_joint = self.compute_ik(self.robot_left, self.left_ik, left_pos)
            right_joint = self.compute_ik(self.robot_right, self.right_ik, right_pos)

            # Set gripper positions
            left_grip = torch.full((1, 2), left_gripper, device=self.device)
            right_grip = torch.full((1, 2), right_gripper, device=self.device)

            # Apply targets
            self.robot_left.set_joint_position_target(torch.cat([left_joint, left_grip], dim=-1))
            self.robot_right.set_joint_position_target(torch.cat([right_joint, right_grip], dim=-1))

            # Step simulation
            for _ in range(steps_per_iter):
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())

            # Check if reached target
            left_ee_pos, _ = self.get_ee_pose(self.robot_left)
            right_ee_pos, _ = self.get_ee_pose(self.robot_right)

            left_dist = torch.norm(left_ee_pos - left_pos).item()
            right_dist = torch.norm(right_ee_pos - right_pos).item()

            if left_dist < position_threshold and right_dist < position_threshold:
                return True

        return False


# =============================================================================
# Goal State Visualizer
# =============================================================================

class GoalStateVisualizer:
    """Visualizes goal states for each phase."""

    GRIPPER_OPEN = 0.04
    GRIPPER_CLOSED = 0.005

    def __init__(self, scene: InteractiveScene, sim, output_dir: str):
        self.scene = scene
        self.sim = sim
        self.output_dir = output_dir
        self.device = scene["robot_left"].device

        os.makedirs(output_dir, exist_ok=True)

        self.ik_helper = DualArmIKHelper(scene, self.device)

        self.cameras = {
            'front_left': scene["front_left_camera"],
            'front_right': scene["front_right_camera"],
            'back': scene["back_camera"],
        }
        self.overhead = scene["overhead_camera"]

        # Get hook and cable references
        self.hook = scene["hook_stem"]
        self.cable = scene["cable"]

        # Get initial positions
        self.hook_pos = self.hook.data.root_pos_w[0].clone()
        self.cable_pos = self.cable.data.root_pos_w[0].clone()

        # V-hook position (top of hook)
        self.hook_v_pos = self.hook_pos.clone()
        self.hook_v_pos[2] += 0.07

        print(f"[Visualizer] Hook position: {self.hook_pos.cpu().tolist()}")
        print(f"[Visualizer] Cable position: {self.cable_pos.cpu().tolist()}")
        print(f"[Visualizer] Hook V position: {self.hook_v_pos.cpu().tolist()}")

    def get_camera_images(self) -> Dict[str, np.ndarray]:
        """Get current camera images."""
        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"]
            img = rgb[0, ..., :3].cpu().numpy().astype(np.uint8)
            images[name] = img

        # Also get overhead
        rgb = self.overhead.data.output["rgb"]
        images['overhead'] = rgb[0, ..., :3].cpu().numpy().astype(np.uint8)

        return images

    def save_phase_images(self, phase: TaskPhase, images: Dict[str, np.ndarray]):
        """Save images for a phase."""
        phase_dir = os.path.join(self.output_dir, f"phase_{phase.value}_{phase.name.lower()}")
        os.makedirs(phase_dir, exist_ok=True)

        for cam_name, img in images.items():
            filename = os.path.join(phase_dir, f"{cam_name}.png")
            Image.fromarray(img).save(filename)
            print(f"    Saved: {filename}")

        # Create composite image (2x2 grid)
        composite = self._create_composite(images)
        composite_file = os.path.join(phase_dir, "composite.png")
        Image.fromarray(composite).save(composite_file)
        print(f"    Composite: {composite_file}")

    def _create_composite(self, images: Dict[str, np.ndarray]) -> np.ndarray:
        """Create 2x2 composite image."""
        h, w = 256, 256
        composite = np.zeros((h * 2, w * 2, 3), dtype=np.uint8)

        # Resize and place images
        positions = {
            'front_left': (0, 0),
            'front_right': (0, w),
            'back': (h, 0),
            'overhead': (h, w),
        }

        for name, (y, x) in positions.items():
            if name in images:
                img = images[name]
                if img.shape[:2] != (h, w):
                    img = np.array(Image.fromarray(img).resize((w, h)))
                composite[y:y+h, x:x+w] = img

        return composite

    def settle_physics(self, steps: int):
        """Run physics simulation to settle."""
        for _ in range(steps):
            self.scene.write_data_to_sim()
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

    def get_cable_ends(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get cable end positions (estimated from cable center and orientation)."""
        cable_pos = self.cable.data.root_pos_w[0]
        cable_quat = self.cable.data.root_quat_w[0]

        # Cable length ~0.3m, so ends are ~0.15m from center
        cable_half_length = 0.15

        # Extract local X axis from quaternion
        w, x, y, z = cable_quat[0], cable_quat[1], cable_quat[2], cable_quat[3]
        local_x = torch.tensor([
            1 - 2 * (y*y + z*z),
            2 * (x*y + z*w),
            2 * (x*z - y*w)
        ], device=self.device)

        left_end = cable_pos - cable_half_length * local_x
        right_end = cable_pos + cable_half_length * local_x

        return left_end, right_end

    def create_goal_state(self, phase: TaskPhase, max_iterations: int = 150):
        """Create goal state for a specific phase using iterative IK.

        Args:
            phase: Target phase
            max_iterations: Maximum IK iterations for movement

        Returns:
            Tuple of (left_target, right_target, left_gripper, right_gripper)
        """
        print(f"\n[Phase {phase.value}] {phase.name}: {PHASE_DESCRIPTIONS[phase]}")

        cable_left, cable_right = self.get_cable_ends()

        if phase == TaskPhase.REACH_CABLE:
            # EEs positioned above cable ends
            left_target = cable_left.clone().unsqueeze(0)
            left_target[0, 2] += 0.03  # 3cm above
            right_target = cable_right.clone().unsqueeze(0)
            right_target[0, 2] += 0.03
            left_gripper = self.GRIPPER_OPEN
            right_gripper = self.GRIPPER_OPEN

        elif phase == TaskPhase.GRASP_CABLE:
            # EEs at cable ends, grippers closed
            left_target = cable_left.clone().unsqueeze(0)
            right_target = cable_right.clone().unsqueeze(0)
            left_gripper = self.GRIPPER_CLOSED
            right_gripper = self.GRIPPER_CLOSED

        elif phase == TaskPhase.LIFT_CABLE:
            # Cable lifted up - use current EE X,Y but lift Z
            left_ee_pos, _ = self.ik_helper.get_ee_pose(self.ik_helper.robot_left)
            right_ee_pos, _ = self.ik_helper.get_ee_pose(self.ik_helper.robot_right)
            lift_height = TABLE_HEIGHT + 0.15

            left_target = left_ee_pos.clone()
            left_target[0, 2] = lift_height
            right_target = right_ee_pos.clone()
            right_target[0, 2] = lift_height
            left_gripper = self.GRIPPER_CLOSED
            right_gripper = self.GRIPPER_CLOSED

        elif phase == TaskPhase.APPROACH_HOOK:
            # EEs approaching hook - maintain current height, move towards hook
            hook_v = self.hook_v_pos.clone()
            left_target = hook_v.clone().unsqueeze(0)
            left_target[0, 1] -= 0.08  # Left offset (wider for approach)
            left_target[0, 2] += 0.08  # Above hook
            right_target = hook_v.clone().unsqueeze(0)
            right_target[0, 1] += 0.08  # Right offset
            right_target[0, 2] += 0.08
            left_gripper = self.GRIPPER_CLOSED
            right_gripper = self.GRIPPER_CLOSED

        elif phase == TaskPhase.DRAPE_ON_HOOK:
            # Cable on hook V - lower onto the hook
            hook_v = self.hook_v_pos.clone()
            left_target = hook_v.clone().unsqueeze(0)
            left_target[0, 1] -= 0.05
            left_target[0, 2] += 0.02  # Just above hook V
            right_target = hook_v.clone().unsqueeze(0)
            right_target[0, 1] += 0.05
            right_target[0, 2] += 0.02
            left_gripper = self.GRIPPER_CLOSED
            right_gripper = self.GRIPPER_CLOSED

        elif phase == TaskPhase.RELEASE:
            # Grippers open, stay at current position briefly then retreat
            hook_v = self.hook_v_pos.clone()
            left_target = hook_v.clone().unsqueeze(0)
            left_target[0, 1] -= 0.10
            left_target[0, 2] += 0.08
            right_target = hook_v.clone().unsqueeze(0)
            right_target[0, 1] += 0.10
            right_target[0, 2] += 0.08
            left_gripper = self.GRIPPER_OPEN
            right_gripper = self.GRIPPER_OPEN

        elif phase == TaskPhase.DONE:
            # Arms retreated to home position
            left_target = torch.tensor([[0.3, -0.3, 1.1]], device=self.device)
            right_target = torch.tensor([[0.3, 0.3, 1.1]], device=self.device)
            left_gripper = self.GRIPPER_OPEN
            right_gripper = self.GRIPPER_OPEN

        else:
            raise ValueError(f"Unknown phase: {phase}")

        # Move to target using iterative IK
        print(f"  Moving to target positions...")
        print(f"  Left target: {left_target[0].cpu().tolist()}")
        print(f"  Right target: {right_target[0].cpu().tolist()}")

        reached = self.ik_helper.move_to_targets(
            self.scene, self.sim,
            left_target, right_target,
            left_gripper, right_gripper,
            max_iterations=max_iterations,
            position_threshold=0.03,  # 3cm threshold
            steps_per_iter=4,
        )

        if reached:
            print(f"  ✓ Targets reached")
        else:
            print(f"  △ Max iterations reached (may be close enough)")

        return left_target, right_target, left_gripper, right_gripper

    def visualize_all_phases(self, settle_steps: int = 30):
        """Visualize all 7 phases with iterative IK movement."""
        print(f"\n{'='*60}")
        print("7-Phase Goal State Visualization")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"Final settle steps: {settle_steps}")

        for phase in TaskPhase:
            # Create goal state with iterative IK movement
            left_target, right_target, _, _ = self.create_goal_state(phase)

            # Final settling for physics stability
            print(f"  Final settling ({settle_steps} steps)...")
            self.settle_physics(settle_steps)

            # Capture images
            images = self.get_camera_images()

            # Save images
            self.save_phase_images(phase, images)

            # Print EE positions for verification
            left_ee_pos, _ = self.ik_helper.get_ee_pose(self.ik_helper.robot_left)
            right_ee_pos, _ = self.ik_helper.get_ee_pose(self.ik_helper.robot_right)
            print(f"  Final Left EE: {left_ee_pos[0].cpu().tolist()}")
            print(f"  Final Right EE: {right_ee_pos[0].cpu().tolist()}")
            print(f"  Target Left: {left_target[0].cpu().tolist()}")
            print(f"  Target Right: {right_target[0].cpu().tolist()}")

        print(f"\n{'='*60}")
        print("Visualization Complete!")
        print(f"{'='*60}")
        print(f"Output: {self.output_dir}")

        # Create summary
        self._create_summary()

    def _create_summary(self):
        """Create summary HTML file."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>7-Phase Goal States</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        h1 { color: #333; }
        .phase { background: white; margin: 20px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .phase h2 { color: #0066cc; margin-top: 0; }
        .images { display: flex; gap: 10px; flex-wrap: wrap; }
        .images img { width: 200px; height: 200px; object-fit: cover; border: 1px solid #ddd; }
        .composite { width: 400px; height: 400px; }
        .description { color: #666; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>7-Phase Goal States - Cable Draping Task</h1>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
"""
        for phase in TaskPhase:
            phase_dir = f"phase_{phase.value}_{phase.name.lower()}"
            html_content += f"""
    <div class="phase">
        <h2>Phase {phase.value}: {phase.name}</h2>
        <p class="description">{PHASE_DESCRIPTIONS[phase]}</p>
        <div class="images">
            <div>
                <h4>Front Left</h4>
                <img src="{phase_dir}/front_left.png" alt="Front Left">
            </div>
            <div>
                <h4>Front Right</h4>
                <img src="{phase_dir}/front_right.png" alt="Front Right">
            </div>
            <div>
                <h4>Back</h4>
                <img src="{phase_dir}/back.png" alt="Back">
            </div>
            <div>
                <h4>Overhead</h4>
                <img src="{phase_dir}/overhead.png" alt="Overhead">
            </div>
            <div>
                <h4>Composite (2x2)</h4>
                <img src="{phase_dir}/composite.png" alt="Composite" class="composite">
            </div>
        </div>
    </div>
"""

        html_content += """
</body>
</html>
"""
        html_file = os.path.join(self.output_dir, "index.html")
        with open(html_file, 'w') as f:
            f.write(html_content)
        print(f"Summary HTML: {html_file}")


# =============================================================================
# Main
# =============================================================================

def main():
    # Setup scene
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = 1

    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Initial warm-up
    print("[Setup] Running initial simulation steps...")
    for _ in range(30):
        sim.step()
    scene.update(sim.get_physics_dt())
    print("[Setup] Initial setup complete!")

    # Create visualizer
    visualizer = GoalStateVisualizer(
        scene=scene,
        sim=sim,
        output_dir=args_cli.output_dir,
    )

    # Visualize all phases
    visualizer.visualize_all_phases(settle_steps=args_cli.settle_steps)

    simulation_app.close()


if __name__ == "__main__":
    main()
