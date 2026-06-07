#!/usr/bin/env python3
"""
MPC Control for Dual Arm Cable Manipulation.

This script runs Model Predictive Control using the trained World Model
for the cable-on-hook manipulation task.

Usage:
    cd /home/rlrk/IsaacLab
    DISPLAY=:1 CUDA_VISIBLE_DEVICES=0 env_isaaclab/bin/python \
        thread_isaac_lab/scripts/run_mpc_control.py \
        --phase 3 --max_steps 500
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
import io
import argparse
from datetime import datetime
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="MPC Control for Cable Manipulation")
parser.add_argument("--phase", type=int, default=3, help="Phase to test (3=Lift, 4=Hook, 5=Place)")
parser.add_argument("--max_steps", type=int, default=500, help="Maximum control steps")
parser.add_argument("--model_path", type=str, default="checkpoints/world_model_4cam/phase2_best.pt",
                    help="Path to World Model checkpoint")
parser.add_argument("--horizon", type=int, default=10, help="MPC planning horizon")
parser.add_argument("--candidates", type=int, default=500, help="Number of CEM candidates")
parser.add_argument("--cem_iters", type=int, default=3, help="CEM iterations")
parser.add_argument("--log_interval", type=int, default=10, help="Logging interval")
parser.add_argument("--save_video", action="store_true", help="Save video of execution")
parser.add_argument("--video_output", type=str, default="data/videos/mpc_control.mp4")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    GRIPPER_CLOSE, GRIPPER_OPEN,
)
from thread_isaac_lab.configs.mpc_config import MPCConfig
from thread_isaac_lab.models.mpc_controller import MPCController, Observation

# Constants
HIGH_FRICTION = 5.0
SETUP_STEPS = 100
GRASP_STEPS = 200

print("=" * 70)
print("MPC CONTROL TEST")
print(f"Phase: {args.phase}")
print(f"Model: {args.model_path}")
print(f"Horizon: {args.horizon}, Candidates: {args.candidates}")
print("=" * 70)


class MPCRunner:
    """Runs MPC control in Isaac Lab simulation."""

    def __init__(self, scene, sim, mpc_controller: MPCController, device: torch.device):
        self.scene = scene
        self.sim = sim
        self.mpc = mpc_controller
        self.device = device

        # Cameras
        self.cameras = {
            'front_left': scene["front_left_camera"],
            'front_right': scene["front_right_camera"],
            'back': scene["back_camera"],
            'overhead': scene["overhead_camera"],
        }

        # Robots
        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]
        self.cable = scene["cable"]

        # Metrics
        self.initial_cable_z = None
        self.max_lift = 0.0
        self.step_count = 0

        # Video frames
        self.video_frames = []

    def get_observation(self) -> Observation:
        """Get current observation for MPC planning."""
        # Update cameras
        for cam in self.cameras.values():
            cam.update(self.sim.get_physics_dt())

        # Get camera images
        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"][0]  # [H, W, 4]
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            # Convert to [C, H, W] and normalize to [0, 1]
            rgb = rgb.permute(2, 0, 1).float() / 255.0
            images[name] = rgb.unsqueeze(0)  # [1, C, H, W]

        # Get proprio
        proprio = self._get_proprio()

        # Get task state
        task_state = self._get_task_state()

        return Observation(
            front_left_img=images['front_left'].to(self.device),
            front_right_img=images['front_right'].to(self.device),
            back_img=images['back'].to(self.device),
            overhead_img=images['overhead'].to(self.device),
            proprio=proprio.to(self.device),
            task_state=task_state.to(self.device),
        )

    def _get_proprio(self) -> torch.Tensor:
        """Get proprioceptive observation (34D)."""
        left_joint_pos = self.robot_left.data.joint_pos[0, :7]
        right_joint_pos = self.robot_right.data.joint_pos[0, :7]
        left_joint_vel = self.robot_left.data.joint_vel[0, :7]
        right_joint_vel = self.robot_right.data.joint_vel[0, :7]
        left_ee_pos = self.robot_left.data.body_pos_w[0, 8, :]
        right_ee_pos = self.robot_right.data.body_pos_w[0, 8, :]

        proprio = torch.cat([
            left_joint_pos, left_joint_vel, left_ee_pos,
            right_joint_pos, right_joint_vel, right_ee_pos,
        ]).unsqueeze(0)
        return proprio

    def _get_task_state(self) -> torch.Tensor:
        """Get task state (44D)."""
        hook_stem = self.scene["hook_stem"]
        hook_pos = hook_stem.data.root_pos_w[0]
        cable_pos = self.cable.data.root_pos_w[0]
        cable_quat = self.cable.data.root_quat_w[0]

        # Handle NaN values
        if torch.any(torch.isnan(cable_pos)) or torch.any(torch.isnan(cable_quat)):
            cable_pos = torch.zeros(3, device=self.device)
            cable_quat = torch.tensor([1.0, 0.0, 0.0, 0.0], device=self.device)

        # Compute virtual cable segment positions (10 segments x 3D = 30D)
        segment_positions = self._compute_cable_segments(cable_pos, cable_quat)

        # EE positions
        left_ee_pos = self.robot_left.data.body_pos_w[0, 8, :]
        right_ee_pos = self.robot_right.data.body_pos_w[0, 8, :]

        # Distances
        cable_center = cable_pos
        cable_hook_dist = torch.norm(cable_center - hook_pos)
        left_ee_cable_dist = torch.norm(left_ee_pos - cable_center)
        right_ee_cable_dist = torch.norm(right_ee_pos - cable_center)
        left_ee_hook_dist = torch.norm(left_ee_pos - hook_pos)
        right_ee_hook_dist = torch.norm(right_ee_pos - hook_pos)

        task_state = torch.cat([
            segment_positions.flatten(),  # 30D
            hook_pos,  # 3D
            left_ee_pos,  # 3D
            right_ee_pos,  # 3D
            torch.stack([cable_hook_dist, left_ee_cable_dist, right_ee_cable_dist,
                        left_ee_hook_dist, right_ee_hook_dist]),  # 5D
        ]).unsqueeze(0)

        # Handle NaN
        task_state = torch.nan_to_num(task_state, nan=0.0)
        return task_state

    def _compute_cable_segments(self, cable_pos: torch.Tensor, cable_quat: torch.Tensor) -> torch.Tensor:
        """Compute virtual cable segment positions."""
        num_segments = 10
        cable_length = 0.5

        # Extract quaternion components
        w, x, y, z = cable_quat[0], cable_quat[1], cable_quat[2], cable_quat[3]

        # Rotation matrix first column (local X axis)
        R00 = 1 - 2 * (y * y + z * z)
        R10 = 2 * (x * y + z * w)
        R20 = 2 * (x * z - y * w)
        local_x = torch.stack([R00, R10, R20])

        # Compute segment positions
        offsets = torch.linspace(-cable_length / 2, cable_length / 2, num_segments, device=self.device)
        segment_positions = cable_pos.unsqueeze(0) + offsets.unsqueeze(1) * local_x.unsqueeze(0)
        return segment_positions

    def apply_action(self, action: torch.Tensor):
        """Apply MPC action to robots."""
        # Split action: [left_joints(7), left_gripper(2), right_joints(7), right_gripper(2)]
        left_joint_delta = action[:7]
        left_gripper_delta = action[7:9]
        right_joint_delta = action[9:16]
        right_gripper_delta = action[16:18]

        # Get current joint positions
        curr_left_joints = self.robot_left.data.joint_pos[0, :7]
        curr_right_joints = self.robot_right.data.joint_pos[0, :7]
        curr_left_gripper = self.robot_left.data.joint_pos[0, -2:]
        curr_right_gripper = self.robot_right.data.joint_pos[0, -2:]

        # Apply delta
        new_left_joints = curr_left_joints + left_joint_delta.to(self.device)
        new_right_joints = curr_right_joints + right_joint_delta.to(self.device)
        new_left_gripper = curr_left_gripper + left_gripper_delta.mean().to(self.device)
        new_right_gripper = curr_right_gripper + right_gripper_delta.mean().to(self.device)

        # Clamp gripper values
        new_left_gripper = torch.clamp(new_left_gripper, 0.0, GRIPPER_OPEN)
        new_right_gripper = torch.clamp(new_right_gripper, 0.0, GRIPPER_OPEN)

        # Set targets
        target_left = self.robot_left.data.joint_pos[0].unsqueeze(0).clone()
        target_left[0, :7] = new_left_joints
        target_left[0, -2:] = new_left_gripper[0]
        self.robot_left.set_joint_position_target(target_left)
        self.robot_left.write_data_to_sim()

        target_right = self.robot_right.data.joint_pos[0].unsqueeze(0).clone()
        target_right[0, :7] = new_right_joints
        target_right[0, -2:] = new_right_gripper[0]
        self.robot_right.set_joint_position_target(target_right)
        self.robot_right.write_data_to_sim()

    def get_cable_z(self) -> float:
        """Get current cable center Z position."""
        cable_z = self.cable.data.root_pos_w[0, 2].item()
        return cable_z if not np.isnan(cable_z) else 0.0

    def save_frame(self):
        """Save current frame for video."""
        if not args.save_video:
            return

        # Get front_left camera image
        self.cameras['front_left'].update(self.sim.get_physics_dt())
        rgb = self.cameras['front_left'].data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        self.video_frames.append(rgb.astype(np.uint8))

    def run_phase3_lift(self, max_steps: int) -> dict:
        """Run Phase 3 Lift with MPC control."""
        print("\n[Phase 3] MPC Lift Control")
        print("-" * 40)

        # Record initial cable Z
        self.initial_cable_z = self.get_cable_z()
        print(f"Initial cable Z: {self.initial_cable_z:.4f} m")

        # Reset MPC state
        self.mpc.reset()

        results = {
            "lift_distances": [],
            "actions": [],
            "cable_positions": [],
        }

        for step in range(max_steps):
            # Get observation
            obs = self.get_observation()

            # Plan action
            action = self.mpc.plan(obs, phase=3)

            # Apply action
            self.apply_action(action)

            # Step simulation
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

            # Track metrics
            current_z = self.get_cable_z()
            lift = current_z - self.initial_cable_z
            self.max_lift = max(self.max_lift, lift)

            results["lift_distances"].append(lift)
            results["actions"].append(action.cpu().numpy())
            results["cable_positions"].append(current_z)

            # Save video frame
            if step % 5 == 0:
                self.save_frame()

            # Log progress
            if step % args.log_interval == 0:
                stats = self.mpc.get_action_statistics()
                print(f"  Step {step:4d}: lift={lift*100:.2f}cm, "
                      f"max={self.max_lift*100:.2f}cm, "
                      f"action_norm={stats.get('mean_action_norm', 0):.4f}")

            # Success check
            if self.max_lift >= 0.10:  # 10cm target
                print(f"\n  SUCCESS! Achieved {self.max_lift*100:.2f}cm lift at step {step}")
                break

        # Final report
        print("\n" + "=" * 40)
        print("PHASE 3 LIFT RESULTS")
        print("=" * 40)
        print(f"  Initial Z:    {self.initial_cable_z:.4f} m")
        print(f"  Final Z:      {self.get_cable_z():.4f} m")
        print(f"  Max Lift:     {self.max_lift*100:.2f} cm")
        print(f"  Steps:        {step + 1}")
        print(f"  Success:      {'YES' if self.max_lift >= 0.10 else 'NO'}")

        results["max_lift"] = self.max_lift
        results["success"] = self.max_lift >= 0.10
        results["total_steps"] = step + 1

        return results


# Setup simulation
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)


@configclass
class MPCSceneCfg(DualArmSceneCfg):
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )


scene_cfg = MPCSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)
sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
device = robot_left.device

# Store initial cable state
initial_cable_root_state = cable.data.root_state_w.clone()


# Apply high friction
def set_friction(asset, sf, df):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = sf
    materials[..., 1] = df
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))


set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)


def set_robot_joints(robot, arm_joints, gripper_val):
    target = robot.data.joint_pos[0].unsqueeze(0).clone()
    target[0, :7] = torch.tensor(arm_joints, device=device)
    target[0, -2:] = gripper_val
    robot.set_joint_position_target(target)
    robot.write_data_to_sim()


def teleport_robot(robot, arm_joints, gripper_val):
    state = robot.data.joint_pos[0].unsqueeze(0).clone()
    state[0, :7] = torch.tensor(arm_joints, device=device)
    state[0, -2:] = gripper_val
    robot.write_joint_state_to_sim(state, robot.data.joint_vel[0].unsqueeze(0))


# Initialize MPC controller
print("\nInitializing MPC Controller...")
mpc_config = MPCConfig(
    horizon=args.horizon,
    num_candidates=args.candidates,
    cem_iterations=args.cem_iters,
    world_model_path=args.model_path,
)
mpc_controller = MPCController(mpc_config)

# Create MPC runner
mpc_runner = MPCRunner(scene, sim, mpc_controller, device)


def setup_for_phase3():
    """Setup scene for Phase 3 (Lift) testing - grasp the cable first."""
    print("\n[Setup] Preparing for Phase 3...")

    # Reset cable
    cable.write_root_state_to_sim(initial_cable_root_state)

    # Phase 1: Move to initial position
    print("  [Phase 1] Initial position...")
    teleport_robot(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    teleport_robot(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    for _ in range(SETUP_STEPS):
        set_robot_joints(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 2: Move to grasp position
    print("  [Phase 2] Moving to grasp position...")
    for step in range(300):
        alpha = (step + 1) / 300
        left_joints = [l + alpha * (p - l) for l, p in zip(LEFT_ARM_INIT_JOINTS, PHASE2_LEFT_JOINTS)]
        right_joints = [l + alpha * (p - l) for l, p in zip(RIGHT_ARM_INIT_JOINTS, PHASE2_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    # Close grippers
    print("  [Phase 2] Closing grippers...")
    for _ in range(GRASP_STEPS):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    # Stabilize
    print("  [Phase 2] Stabilizing grasp...")
    for _ in range(100):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    print("  [Setup] Ready for Phase 3 MPC control")


def save_video():
    """Save video from collected frames."""
    if not args.save_video or len(mpc_runner.video_frames) == 0:
        return

    import subprocess

    # Save frames
    frame_dir = "/tmp/mpc_frames"
    os.makedirs(frame_dir, exist_ok=True)

    for i, frame in enumerate(mpc_runner.video_frames):
        img = Image.fromarray(frame)
        img.save(os.path.join(frame_dir, f"frame_{i:06d}.png"))

    # Create video with ffmpeg
    video_dir = os.path.dirname(args.video_output)
    if video_dir:
        os.makedirs(video_dir, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", os.path.join(frame_dir, "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        args.video_output
    ]
    subprocess.run(cmd, capture_output=True)
    print(f"[Video] Saved to {args.video_output}")


# Main execution
if args.phase == 3:
    setup_for_phase3()
    results = mpc_runner.run_phase3_lift(args.max_steps)

    # Save video
    save_video()

    # Summary
    print("\n" + "=" * 70)
    print("MPC CONTROL TEST COMPLETE")
    print("=" * 70)
    if results["success"]:
        print("  STATUS: SUCCESS")
    else:
        print("  STATUS: FAILED (did not reach 10cm lift)")
    print(f"  Max Lift: {results['max_lift']*100:.2f} cm")
    print(f"  Steps: {results['total_steps']}")

else:
    print(f"Phase {args.phase} not yet implemented")

# Cleanup
simulation_app.close()
