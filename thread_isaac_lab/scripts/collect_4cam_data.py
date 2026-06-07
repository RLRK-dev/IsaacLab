#!/usr/bin/env python3
"""Collect training data from dual arm 4-camera environment for World Model.

This script collects (s, a, r, s') transitions with 4 camera images from
the dual arm manipulation environment.

Configuration:
- 4 cameras: front_left, front_right, back, overhead
- 44D task_state: 30D cable segments + 3D hook + 3D left_ee + 3D right_ee + 5D distances
- 34D proprio: joint positions, velocities, and EE positions for both arms

Usage:
    python thread_isaac_lab/scripts/collect_4cam_data.py \
        --device cuda:1 --num_envs 1024 --num_episodes 500 --headless --enable_cameras

Output:
    data/world_model_4cam_v1/wm_4cam_batch{batch}.h5
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Collect 4-camera dual arm data for World Model")
parser.add_argument("--num_envs", type=int, default=256, help="Number of environments")
parser.add_argument("--num_episodes", type=int, default=500, help="Total episodes to collect")
parser.add_argument("--max_steps", type=int, default=200, help="Max steps per episode")
parser.add_argument("--output_dir", type=str, default="data/world_model_4cam_v1", help="Output directory")
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

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from envs.dual_arm_cfg import DualArmSceneCfg
from envs.flexible_cable_cfg import CABLE_TOTAL_LENGTH, CABLE_NUM_SEGMENTS


def compress_image_jpeg(img_array: np.ndarray, quality: int = 85) -> bytes:
    """Compress numpy image array to JPEG bytes."""
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


class FourCamDataCollector:
    """Collects (s, a, r, s') transitions with 4 camera images and 44D task state."""

    def __init__(
        self,
        scene: InteractiveScene,
        sim,
        output_dir: str,
        num_envs: int,
        max_steps: int = 200,
    ):
        self.scene = scene
        self.sim = sim
        self.output_dir = output_dir
        self.num_envs = num_envs
        self.max_steps = max_steps
        self.device = scene["robot_left"].device

        os.makedirs(output_dir, exist_ok=True)

        self.action_dim = 18
        self.proprio_dim = 34
        self.task_state_dim = 44

        # 4 Cameras (new naming convention)
        self.cameras = {
            'front_left': scene["front_left_camera"],
            'front_right': scene["front_right_camera"],
            'back': scene["back_camera"],
            'overhead': scene["overhead_camera"],
        }
        print(f"[Cameras] Found {len(self.cameras)} cameras: {list(self.cameras.keys())}")

        self.reset_buffers()

    def reset_buffers(self):
        """Reset data collection buffers."""
        # 4 camera images
        self.front_left_imgs = []
        self.front_right_imgs = []
        self.back_imgs = []
        self.overhead_imgs = []

        # Next state images
        self.next_front_left_imgs = []
        self.next_front_right_imgs = []
        self.next_back_imgs = []
        self.next_overhead_imgs = []

        # State
        self.proprios = []
        self.next_proprios = []

        # Task state (44D)
        self.task_states = []
        self.next_task_states = []

        # Actions and rewards
        self.actions = []
        self.rewards = []
        self.dones = []

        # Episode stats
        self.episode_lengths = []
        self.episode_rewards = []

    def get_camera_images(self):
        """Get current camera images from all 4 cameras."""
        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"]  # (num_envs, H, W, 4)
            img = rgb[..., :3].cpu().numpy().astype(np.uint8)
            images[name] = img
        return images

    def get_proprio(self):
        """Get proprioceptive observation (34D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        left_joint_pos = robot_left.data.joint_pos[:, :7]
        right_joint_pos = robot_right.data.joint_pos[:, :7]
        left_joint_vel = robot_left.data.joint_vel[:, :7]
        right_joint_vel = robot_right.data.joint_vel[:, :7]
        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]

        proprio = torch.cat([
            left_joint_pos, left_joint_vel, left_ee_pos,
            right_joint_pos, right_joint_vel, right_ee_pos,
        ], dim=-1)

        return proprio

    def get_task_state(self):
        """Get task-relevant state information (44D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        hook_stem = self.scene["hook_stem"]
        hook_pos = hook_stem.data.root_pos_w

        cable = self.scene["cable"]
        cable_pos = cable.data.root_pos_w
        cable_quat = cable.data.root_quat_w

        # Virtual cable segment positions
        segment_positions = self._compute_cable_segments(cable_pos, cable_quat)

        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]

        cable_center = cable_pos
        cable_hook_dist = torch.norm(cable_center - hook_pos, dim=-1, keepdim=True)
        left_ee_cable_dist = torch.norm(left_ee_pos - cable_center, dim=-1, keepdim=True)
        right_ee_cable_dist = torch.norm(right_ee_pos - cable_center, dim=-1, keepdim=True)
        left_ee_hook_dist = torch.norm(left_ee_pos - hook_pos, dim=-1, keepdim=True)
        right_ee_hook_dist = torch.norm(right_ee_pos - hook_pos, dim=-1, keepdim=True)

        task_state = torch.cat([
            segment_positions.view(self.num_envs, -1),
            hook_pos, left_ee_pos, right_ee_pos,
            cable_hook_dist, left_ee_cable_dist, right_ee_cable_dist,
            left_ee_hook_dist, right_ee_hook_dist,
        ], dim=-1)

        return task_state

    def _compute_cable_segments(self, cable_pos, cable_quat):
        """Compute virtual cable segment positions."""
        batch_size = cable_pos.shape[0]
        device = cable_pos.device

        segment_offsets = torch.linspace(
            -CABLE_TOTAL_LENGTH / 2,
            CABLE_TOTAL_LENGTH / 2,
            CABLE_NUM_SEGMENTS,
            device=device
        )

        w, x, y, z = cable_quat[:, 0], cable_quat[:, 1], cable_quat[:, 2], cable_quat[:, 3]
        R00 = 1 - 2 * (y * y + z * z)
        R10 = 2 * (x * y + z * w)
        R20 = 2 * (x * z - y * w)

        local_x = torch.stack([R00, R10, R20], dim=-1)
        segment_positions = cable_pos.unsqueeze(1) + segment_offsets.unsqueeze(0).unsqueeze(-1) * local_x.unsqueeze(1)

        return segment_positions

    def compute_reward(self, task_state):
        """Compute simple reward based on cable-hook distance."""
        cable_hook_dist = task_state[:, 39:40]
        reward = -cable_hook_dist.squeeze(-1)
        return reward

    def sample_action(self):
        """Sample random action."""
        action = torch.randn(self.num_envs, self.action_dim, device=self.device) * 0.1
        action = torch.clamp(action, -1.0, 1.0)
        return action

    def apply_action(self, action):
        """Apply action to robots."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        left_action = action[:, :9]
        right_action = action[:, 9:]

        left_joint_targets = robot_left.data.joint_pos[:, :7] + left_action[:, :7] * 0.05
        right_joint_targets = robot_right.data.joint_pos[:, :7] + right_action[:, :7] * 0.05

        left_gripper = left_action[:, 7:9] * 0.04 + 0.04
        right_gripper = right_action[:, 7:9] * 0.04 + 0.04

        robot_left.set_joint_position_target(
            torch.cat([left_joint_targets, left_gripper], dim=-1)
        )
        robot_right.set_joint_position_target(
            torch.cat([right_joint_targets, right_gripper], dim=-1)
        )

    def collect_episode(self, episode_id: int):
        """Collect one episode of data."""
        print(f"[Episode {episode_id}] Starting...", flush=True)
        episode_reward = 0.0
        step = 0

        print(f"[Episode {episode_id}] Getting camera images...", flush=True)
        images = self.get_camera_images()
        print(f"[Episode {episode_id}] Getting proprio...", flush=True)
        proprio = self.get_proprio()
        print(f"[Episode {episode_id}] Getting task state...", flush=True)
        task_state = self.get_task_state()
        print(f"[Episode {episode_id}] Initial state collected", flush=True)

        for step in range(self.max_steps):
            action = self.sample_action()
            self.apply_action(action)

            # Store current state
            for env_idx in range(self.num_envs):
                self.front_left_imgs.append(compress_image_jpeg(images['front_left'][env_idx]))
                self.front_right_imgs.append(compress_image_jpeg(images['front_right'][env_idx]))
                self.back_imgs.append(compress_image_jpeg(images['back'][env_idx]))
                self.overhead_imgs.append(compress_image_jpeg(images['overhead'][env_idx]))
                self.proprios.append(proprio[env_idx].cpu().numpy())
                self.task_states.append(task_state[env_idx].cpu().numpy())
                self.actions.append(action[env_idx].cpu().numpy())

            # Step simulation
            for _ in range(4):
                self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

            # Get next state
            next_images = self.get_camera_images()
            next_proprio = self.get_proprio()
            next_task_state = self.get_task_state()

            reward = self.compute_reward(next_task_state)
            episode_reward += reward.mean().item()

            for env_idx in range(self.num_envs):
                self.next_front_left_imgs.append(compress_image_jpeg(next_images['front_left'][env_idx]))
                self.next_front_right_imgs.append(compress_image_jpeg(next_images['front_right'][env_idx]))
                self.next_back_imgs.append(compress_image_jpeg(next_images['back'][env_idx]))
                self.next_overhead_imgs.append(compress_image_jpeg(next_images['overhead'][env_idx]))
                self.next_proprios.append(next_proprio[env_idx].cpu().numpy())
                self.next_task_states.append(next_task_state[env_idx].cpu().numpy())
                self.rewards.append(reward[env_idx].item())
                self.dones.append(False)

            images = next_images
            proprio = next_proprio
            task_state = next_task_state

        # Mark last step of episode as done=True
        for env_idx in range(self.num_envs):
            self.dones[-self.num_envs + env_idx] = True

        self.episode_lengths.append(step + 1)
        self.episode_rewards.append(episode_reward / (step + 1))

    def save_batch(self, batch_id: int):
        """Save collected data to HDF5 file."""
        filename = os.path.join(self.output_dir, f"wm_4cam_batch{batch_id:04d}.h5")
        print(f"[Save] Saving {len(self.proprios)} samples to {filename}")

        with h5py.File(filename, 'w') as f:
            # Images (variable length)
            dt = h5py.special_dtype(vlen=np.uint8)
            f.create_dataset('front_left_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.front_left_imgs], dtype=object), dtype=dt)
            f.create_dataset('front_right_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.front_right_imgs], dtype=object), dtype=dt)
            f.create_dataset('back_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.back_imgs], dtype=object), dtype=dt)
            f.create_dataset('overhead_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.overhead_imgs], dtype=object), dtype=dt)

            f.create_dataset('next_front_left_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_front_left_imgs], dtype=object), dtype=dt)
            f.create_dataset('next_front_right_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_front_right_imgs], dtype=object), dtype=dt)
            f.create_dataset('next_back_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_back_imgs], dtype=object), dtype=dt)
            f.create_dataset('next_overhead_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_overhead_imgs], dtype=object), dtype=dt)

            # State data
            f.create_dataset('proprio', data=np.array(self.proprios), dtype=np.float32)
            f.create_dataset('next_proprio', data=np.array(self.next_proprios), dtype=np.float32)
            f.create_dataset('task_state', data=np.array(self.task_states), dtype=np.float32)
            f.create_dataset('next_task_state', data=np.array(self.next_task_states), dtype=np.float32)
            f.create_dataset('action', data=np.array(self.actions), dtype=np.float32)
            f.create_dataset('reward', data=np.array(self.rewards), dtype=np.float32)
            f.create_dataset('done', data=np.array(self.dones), dtype=bool)

            # Metadata
            f.attrs['num_cameras'] = 4
            f.attrs['camera_names'] = ['front_left', 'front_right', 'back', 'overhead']
            f.attrs['proprio_dim'] = self.proprio_dim
            f.attrs['task_state_dim'] = self.task_state_dim
            f.attrs['action_dim'] = self.action_dim
            f.attrs['timestamp'] = datetime.now().isoformat()

        self.reset_buffers()
        print(f"[Save] Done: {filename}")


def main():
    print(f"\n{'='*60}")
    print(f"4-Camera Data Collection for World Model")
    print(f"{'='*60}")
    print(f"num_envs: {args_cli.num_envs}")
    print(f"num_episodes: {args_cli.num_episodes}")
    print(f"max_steps: {args_cli.max_steps}")
    print(f"output_dir: {args_cli.output_dir}")
    print(f"{'='*60}\n")

    # Setup scene
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = args_cli.num_envs

    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Create collector
    collector = FourCamDataCollector(
        scene=scene,
        sim=sim,
        output_dir=args_cli.output_dir,
        num_envs=args_cli.num_envs,
        max_steps=args_cli.max_steps,
    )

    # Run simulation for a few steps to settle
    print("[Setup] Running initial simulation steps...", flush=True)
    for i in range(30):
        if i % 10 == 0:
            print(f"  Step {i}/30...", flush=True)
        sim.step()
    print("[Setup] Updating scene...", flush=True)
    scene.update(sim.get_physics_dt())
    print("[Setup] Initial setup complete!", flush=True)

    # Collect episodes
    batch_id = 0
    for episode in range(args_cli.num_episodes):
        collector.collect_episode(episode)

        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(collector.episode_rewards[-10:])
            print(f"[Episode {episode + 1}/{args_cli.num_episodes}] Avg reward: {avg_reward:.4f}, Samples: {len(collector.proprios)}")

        if (episode + 1) % args_cli.save_frequency == 0:
            collector.save_batch(batch_id)
            batch_id += 1

    # Save remaining data
    if len(collector.proprios) > 0:
        collector.save_batch(batch_id)

    print(f"\n[Done] Data collection complete!")
    print(f"Total episodes: {args_cli.num_episodes}")
    print(f"Output directory: {args_cli.output_dir}")

    simulation_app.close()


if __name__ == "__main__":
    main()
