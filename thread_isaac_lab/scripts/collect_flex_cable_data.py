#!/usr/bin/env python3
"""Collect training data from dual arm flexible cable environment for World Model.

This script collects (s, a, r, s') transitions with camera images from
the dual arm manipulation environment with a flexible multi-segment cable.

Task State (44D):
    - Cable segment positions: 10 segments * 3D = 30D
    - Hook position: 3D
    - Left EE position: 3D
    - Right EE position: 3D
    - Distances: 5D (cable_center_hook, left_ee_cable, right_ee_cable, left_ee_hook, right_ee_hook)

Usage:
    cd /home/rlrk/IsaacLab
    source env_isaaclab/bin/activate
    CUDA_VISIBLE_DEVICES=0 OMNI_KIT_ALLOW_ROOT=1 python \
        thread_isaac_lab/scripts/collect_flex_cable_data.py \
        --num_envs 64 --num_episodes 500 --headless --enable_cameras

Output:
    data/world_model_flex_cable/wm_flex_cable_batch{batch}.h5
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Collect flexible cable data for World Model")
parser.add_argument("--num_envs", type=int, default=64, help="Number of environments")
parser.add_argument("--num_episodes", type=int, default=500, help="Total episodes to collect")
parser.add_argument("--max_steps", type=int, default=200, help="Max steps per episode")
parser.add_argument("--output_dir", type=str, default="data/world_model_flex_cable", help="Output directory")
parser.add_argument("--save_frequency", type=int, default=100, help="Save every N episodes")
parser.add_argument("--seed", type=int, default=42, help="Random seed")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os
import io
import h5py
import torch
import numpy as np
from datetime import datetime
from PIL import Image
import omni.usd
from pxr import UsdGeom, Gf

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from envs.dual_arm_flex_env_cfg import (
    DualArmFlexCableSceneCfg,
    NUM_CABLE_SEGMENTS,
    CABLE_SEGMENT_LENGTH,
    TABLE_HEIGHT,
    TASK_STATE_DIM,
)
from envs.flexible_cable_utils import create_flexible_cable
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def compress_image_jpeg(img_array: np.ndarray, quality: int = 85) -> bytes:
    """Compress numpy image array to JPEG bytes."""
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


def decompress_jpeg_image(jpeg_bytes: bytes) -> np.ndarray:
    """Decompress JPEG bytes to numpy array."""
    buffer = io.BytesIO(jpeg_bytes)
    img = Image.open(buffer)
    return np.array(img)


class FlexCableDataCollector:
    """Collects (s, a, r, s') transitions with camera images for flexible cable."""

    def __init__(
        self,
        scene: InteractiveScene,
        cable_segment_paths: list,
        output_dir: str,
        num_envs: int,
        max_steps: int = 200,
    ):
        self.scene = scene
        self.cable_segment_paths = cable_segment_paths
        self.output_dir = output_dir
        self.num_envs = num_envs
        self.max_steps = max_steps
        self.device = scene["robot_left"].device
        self.stage = omni.usd.get_context().get_stage()

        os.makedirs(output_dir, exist_ok=True)

        # Action dimension: 7 joints + 2 gripper for each arm = 18
        self.action_dim = 18
        self.proprio_dim = 34  # (7 pos + 7 vel + 3 ee) × 2 arms = 34
        self.task_state_dim = TASK_STATE_DIM  # 44D

        # Camera specs
        self.left_cam = scene["left_hand_camera"]
        self.right_cam = scene["right_hand_camera"]
        self.overhead_cam = scene["overhead_camera"]

        print(f"[Collector] Using random actions")
        print(f"[Collector] Task state dim: {self.task_state_dim}D")
        print(f"[Collector] Cable segments: {len(cable_segment_paths)}")

        # Buffers for current batch
        self.reset_buffers()

    def reset_buffers(self):
        """Reset data collection buffers."""
        self.left_hand_imgs = []
        self.right_hand_imgs = []
        self.overhead_imgs = []
        self.proprios = []
        self.actions = []
        self.rewards = []
        self.next_left_hand_imgs = []
        self.next_right_hand_imgs = []
        self.next_overhead_imgs = []
        self.next_proprios = []
        self.dones = []
        self.episode_lengths = []
        self.episode_rewards = []
        # Task-relevant state information (44D)
        self.task_states = []
        self.next_task_states = []

    def get_camera_images(self):
        """Get current camera images."""
        left_rgb = self.left_cam.data.output["rgb"]  # (num_envs, H, W, 4)
        right_rgb = self.right_cam.data.output["rgb"]
        overhead_rgb = self.overhead_cam.data.output["rgb"]

        # Remove alpha channel and convert to numpy
        left_img = left_rgb[..., :3].cpu().numpy().astype(np.uint8)
        right_img = right_rgb[..., :3].cpu().numpy().astype(np.uint8)
        overhead_img = overhead_rgb[..., :3].cpu().numpy().astype(np.uint8)

        return left_img, right_img, overhead_img

    def get_proprio(self):
        """Get proprioceptive observation (42D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        # Left arm
        left_joint_pos = robot_left.data.joint_pos[:, :7]  # 7D
        left_joint_vel = robot_left.data.joint_vel[:, :7]  # 7D
        left_ee_idx = robot_left.find_bodies("panda_hand")[0][0]
        left_ee_pos = robot_left.data.body_pos_w[:, left_ee_idx]  # 3D

        # Right arm
        right_joint_pos = robot_right.data.joint_pos[:, :7]  # 7D
        right_joint_vel = robot_right.data.joint_vel[:, :7]  # 7D
        right_ee_idx = robot_right.find_bodies("panda_hand")[0][0]
        right_ee_pos = robot_right.data.body_pos_w[:, right_ee_idx]  # 3D

        # Concatenate: (7+7+3)*2 = 42D
        proprio = torch.cat([
            left_joint_pos, left_joint_vel, left_ee_pos,
            right_joint_pos, right_joint_vel, right_ee_pos,
        ], dim=-1)

        return proprio

    def get_cable_segment_positions_runtime(self):
        """Get cable segment positions during simulation.

        Returns:
            positions: Tensor [num_envs, num_segments, 3]
        """
        positions = []
        for path in self.cable_segment_paths:
            prim = self.stage.GetPrimAtPath(path)
            if prim.IsValid():
                xform = UsdGeom.Xformable(prim)
                world_mtx = xform.ComputeLocalToWorldTransform(0)
                pos = world_mtx.ExtractTranslation()
                positions.append([pos[0], pos[1], pos[2]])
            else:
                positions.append([0.0, 0.0, 0.0])

        # Convert to tensor [1, num_segments, 3] and repeat for num_envs
        pos_tensor = torch.tensor(positions, device=self.device, dtype=torch.float32)
        pos_tensor = pos_tensor.unsqueeze(0).expand(self.num_envs, -1, -1)

        return pos_tensor

    def get_task_state(self):
        """Get task-relevant state information (44D).

        Returns:
            task_state: Tensor [num_envs, 44] containing:
                - cable_segment_positions (30D): 10 segments * 3D
                - hook_pos (3D): Hook position
                - left_ee_pos (3D): Left end-effector position
                - right_ee_pos (3D): Right end-effector position
                - cable_center_hook_dist (1D): Distance from cable center to hook
                - left_ee_cable_dist (1D): Distance from left EE to cable center
                - right_ee_cable_dist (1D): Distance from right EE to cable center
                - left_ee_hook_dist (1D): Distance from left EE to hook
                - right_ee_hook_dist (1D): Distance from right EE to hook
        """
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]
        hook_vertical = self.scene["hook_vertical"]

        # Get EE positions
        left_ee_idx = robot_left.find_bodies("panda_hand")[0][0]
        right_ee_idx = robot_right.find_bodies("panda_hand")[0][0]
        left_ee_pos = robot_left.data.body_pos_w[:, left_ee_idx]  # [num_envs, 3]
        right_ee_pos = robot_right.data.body_pos_w[:, right_ee_idx]  # [num_envs, 3]

        # Get hook position
        hook_pos = hook_vertical.data.root_pos_w  # [num_envs, 3]

        # Get cable segment positions [num_envs, num_segments, 3]
        cable_positions = self.get_cable_segment_positions_runtime()

        # Flatten cable positions to [num_envs, 30]
        cable_pos_flat = cable_positions.reshape(self.num_envs, -1)

        # Compute cable center (average of all segments)
        cable_center = cable_positions.mean(dim=1)  # [num_envs, 3]

        # Compute distances
        cable_center_hook_dist = torch.norm(cable_center - hook_pos, dim=-1, keepdim=True)
        left_ee_cable_dist = torch.norm(left_ee_pos - cable_center, dim=-1, keepdim=True)
        right_ee_cable_dist = torch.norm(right_ee_pos - cable_center, dim=-1, keepdim=True)
        left_ee_hook_dist = torch.norm(left_ee_pos - hook_pos, dim=-1, keepdim=True)
        right_ee_hook_dist = torch.norm(right_ee_pos - hook_pos, dim=-1, keepdim=True)

        # Concatenate all task state information
        task_state = torch.cat([
            cable_pos_flat,           # 30D (10 segments * 3)
            hook_pos,                 # 3D
            left_ee_pos,              # 3D
            right_ee_pos,             # 3D
            cable_center_hook_dist,   # 1D
            left_ee_cable_dist,       # 1D
            right_ee_cable_dist,      # 1D
            left_ee_hook_dist,        # 1D
            right_ee_hook_dist,       # 1D
        ], dim=-1)  # Total: 44D

        return task_state

    def sample_action(self, proprio: torch.Tensor):
        """Sample random action."""
        # Random action in [-1, 1]
        action = torch.rand(self.num_envs, self.action_dim, device=self.device) * 2 - 1
        return action

    def compute_reward(self):
        """Compute reward based on task progress."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]
        hook_vertical = self.scene["hook_vertical"]

        # Get positions
        left_ee_idx = robot_left.find_bodies("panda_hand")[0][0]
        right_ee_idx = robot_right.find_bodies("panda_hand")[0][0]
        left_ee_pos = robot_left.data.body_pos_w[:, left_ee_idx]
        right_ee_pos = robot_right.data.body_pos_w[:, right_ee_idx]
        hook_pos = hook_vertical.data.root_pos_w

        # Get cable center
        cable_positions = self.get_cable_segment_positions_runtime()
        cable_center = cable_positions.mean(dim=1)

        # Distance rewards
        left_to_cable = torch.norm(left_ee_pos - cable_center, dim=-1)
        right_to_cable = torch.norm(right_ee_pos - cable_center, dim=-1)
        cable_to_hook = torch.norm(cable_center - hook_pos, dim=-1)

        # Approach reward
        approach_reward = -0.5 * (left_to_cable + right_to_cable)

        # Hook proximity reward
        hook_reward = -cable_to_hook

        # Combined reward
        reward = approach_reward + 0.5 * hook_reward

        return reward

    def collect_step(self, sim):
        """Collect single step of data."""
        # Get current state
        left_img, right_img, overhead_img = self.get_camera_images()
        proprio = self.get_proprio()
        task_state = self.get_task_state()

        # Sample action
        action = self.sample_action(proprio)

        # Apply action to robots
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        # Split action: left arm (0:9), right arm (9:18)
        left_action = action[:, :9]
        right_action = action[:, 9:]

        # Set joint targets (all 9 joints: 7 arm + 2 gripper)
        robot_left.set_joint_position_target(left_action)
        robot_right.set_joint_position_target(right_action)

        # Step simulation
        self.scene.write_data_to_sim()
        sim.step()
        self.scene.update(sim.get_physics_dt())

        # Get next state
        next_left_img, next_right_img, next_overhead_img = self.get_camera_images()
        next_proprio = self.get_proprio()
        next_task_state = self.get_task_state()

        # Compute reward
        reward = self.compute_reward()

        # Store compressed images
        for env_idx in range(self.num_envs):
            self.left_hand_imgs.append(compress_image_jpeg(left_img[env_idx]))
            self.right_hand_imgs.append(compress_image_jpeg(right_img[env_idx]))
            self.overhead_imgs.append(compress_image_jpeg(overhead_img[env_idx]))
            self.next_left_hand_imgs.append(compress_image_jpeg(next_left_img[env_idx]))
            self.next_right_hand_imgs.append(compress_image_jpeg(next_right_img[env_idx]))
            self.next_overhead_imgs.append(compress_image_jpeg(next_overhead_img[env_idx]))

        self.proprios.append(proprio.cpu().numpy())
        self.actions.append(action.cpu().numpy())
        self.rewards.append(reward.cpu().numpy())
        self.next_proprios.append(next_proprio.cpu().numpy())
        self.task_states.append(task_state.cpu().numpy())
        self.next_task_states.append(next_task_state.cpu().numpy())

    def save_batch(self, batch_idx: int, total_episodes: int):
        """Save collected data to HDF5 file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wm_flex_cable_batch{batch_idx:04d}_{timestamp}.h5"
        filepath = os.path.join(self.output_dir, filename)

        num_transitions = len(self.proprios) * self.num_envs

        with h5py.File(filepath, 'w') as f:
            # Metadata
            f.attrs['num_transitions'] = num_transitions
            f.attrs['num_envs'] = self.num_envs
            f.attrs['max_steps'] = self.max_steps
            f.attrs['total_episodes'] = total_episodes
            f.attrs['action_dim'] = self.action_dim
            f.attrs['proprio_dim'] = self.proprio_dim
            f.attrs['task_state_dim'] = self.task_state_dim
            f.attrs['num_cable_segments'] = NUM_CABLE_SEGMENTS
            f.attrs['cable_segment_length'] = CABLE_SEGMENT_LENGTH
            f.attrs['timestamp'] = timestamp

            # Create variable-length dtype for JPEG images
            dt = h5py.special_dtype(vlen=np.uint8)

            # Store JPEG compressed images
            f.create_dataset('left_hand_imgs', data=np.array(
                [np.frombuffer(img, dtype=np.uint8) for img in self.left_hand_imgs],
                dtype=object
            ), dtype=dt)
            f.create_dataset('right_hand_imgs', data=np.array(
                [np.frombuffer(img, dtype=np.uint8) for img in self.right_hand_imgs],
                dtype=object
            ), dtype=dt)
            f.create_dataset('overhead_imgs', data=np.array(
                [np.frombuffer(img, dtype=np.uint8) for img in self.overhead_imgs],
                dtype=object
            ), dtype=dt)
            f.create_dataset('next_left_hand_imgs', data=np.array(
                [np.frombuffer(img, dtype=np.uint8) for img in self.next_left_hand_imgs],
                dtype=object
            ), dtype=dt)
            f.create_dataset('next_right_hand_imgs', data=np.array(
                [np.frombuffer(img, dtype=np.uint8) for img in self.next_right_hand_imgs],
                dtype=object
            ), dtype=dt)
            f.create_dataset('next_overhead_imgs', data=np.array(
                [np.frombuffer(img, dtype=np.uint8) for img in self.next_overhead_imgs],
                dtype=object
            ), dtype=dt)

            # Store numeric data
            f.create_dataset('proprio', data=np.vstack(self.proprios))
            f.create_dataset('action', data=np.vstack(self.actions))
            f.create_dataset('reward', data=np.hstack(self.rewards))
            f.create_dataset('next_proprio', data=np.vstack(self.next_proprios))
            f.create_dataset('task_state', data=np.vstack(self.task_states))
            f.create_dataset('next_task_state', data=np.vstack(self.next_task_states))

        print(f"[Save] Saved {num_transitions} transitions to {filepath}")
        self.reset_buffers()


def main():
    print("\n" + "="*60, flush=True)
    print("FLEXIBLE CABLE DATA COLLECTION", flush=True)
    print("="*60, flush=True)

    print(f"\n[Config]", flush=True)
    print(f"  Num envs: {args_cli.num_envs}", flush=True)
    print(f"  Num episodes: {args_cli.num_episodes}", flush=True)
    print(f"  Max steps: {args_cli.max_steps}", flush=True)
    print(f"  Output dir: {args_cli.output_dir}", flush=True)
    print(f"  Cable segments: {NUM_CABLE_SEGMENTS}", flush=True)
    print(f"  Task state dim: {TASK_STATE_DIM}D", flush=True)

    # Setup simulation
    print("\n[Status] Setting up simulation...", flush=True)
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.5, -1.0, 1.5), target=(0.5, 0.0, 0.75))

    # Create scene
    print("[Status] Creating scene...", flush=True)
    cfg = DualArmFlexCableSceneCfg()
    cfg.num_envs = args_cli.num_envs
    scene = InteractiveScene(cfg)

    # Add flexible cable with joints
    print("[Status] Adding flexible cable...", flush=True)
    cable_segment_paths = create_flexible_cable(
        base_path="/World/envs/env_0",
        cable_name="flexible_cable",
        start_pos=(0.35, 0.0, TABLE_HEIGHT + 0.02),
        num_segments=NUM_CABLE_SEGMENTS,
        segment_length=CABLE_SEGMENT_LENGTH,
        segment_radius=0.006,
        color=(1.0, 0.4, 0.0),
    )
    print(f"[Status] Created {len(cable_segment_paths)} cable segments", flush=True)

    # Start simulation
    print("[Status] Starting simulation...", flush=True)
    sim.reset()
    print("[Status] Simulation started!", flush=True)

    # Create collector
    collector = FlexCableDataCollector(
        scene=scene,
        cable_segment_paths=cable_segment_paths,
        output_dir=args_cli.output_dir,
        num_envs=args_cli.num_envs,
        max_steps=args_cli.max_steps,
    )

    print("\n" + "="*60, flush=True)
    print("Starting data collection...", flush=True)
    print("="*60 + "\n", flush=True)

    batch_idx = 0
    total_episodes = 0
    episodes_since_save = 0

    while total_episodes < args_cli.num_episodes and simulation_app.is_running():
        # Collect one episode
        for step in range(args_cli.max_steps):
            collector.collect_step(sim)

        total_episodes += args_cli.num_envs
        episodes_since_save += args_cli.num_envs

        # Progress report
        if total_episodes % (args_cli.num_envs * 10) == 0:
            print(f"[Progress] Episodes: {total_episodes}/{args_cli.num_episodes}", flush=True)

        # Save batch
        if episodes_since_save >= args_cli.save_frequency:
            collector.save_batch(batch_idx, total_episodes)
            batch_idx += 1
            episodes_since_save = 0

    # Save remaining data
    if episodes_since_save > 0:
        collector.save_batch(batch_idx, total_episodes)

    print("\n" + "="*60, flush=True)
    print(f"Data collection complete! Total episodes: {total_episodes}", flush=True)
    print("="*60, flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
