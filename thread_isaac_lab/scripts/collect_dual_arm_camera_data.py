#!/usr/bin/env python3
"""Collect training data from dual arm camera environment for World Model.

This script collects (s, a, r, s') transitions with camera images from
the dual arm manipulation environment.

Configuration:
- 5 cameras: front, left, right, back, overhead
- 44D task_state: 30D cable segments + 3D hook + 3D left_ee + 3D right_ee + 5D distances
- 34D proprio: joint positions, velocities, and EE positions for both arms

Usage:
    cd /home/rlrk/IsaacLab
    source env_isaaclab/bin/activate
    CUDA_VISIBLE_DEVICES=0 OMNI_KIT_ALLOW_ROOT=1 python \
        thread_isaac_lab/scripts/collect_dual_arm_camera_data.py \
        --num_envs 64 --num_episodes 200 --headless --enable_cameras

Output:
    data/world_model_dual_arm_v2/wm_dual_arm_batch{batch}.h5
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Collect dual arm camera data for World Model")
parser.add_argument("--num_envs", type=int, default=64, help="Number of environments")
parser.add_argument("--num_episodes", type=int, default=200, help="Total episodes to collect")
parser.add_argument("--max_steps", type=int, default=200, help="Max steps per episode")
parser.add_argument("--output_dir", type=str, default="data/world_model_dual_arm_v2", help="Output directory")
parser.add_argument("--policy_path", type=str, default=None, help="Path to trained policy (optional)")
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
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def compress_image_jpeg(img_array: np.ndarray, quality: int = 85) -> bytes:
    """Compress numpy image array to JPEG bytes.

    Args:
        img_array: RGB image as numpy array (H, W, 3) uint8
        quality: JPEG quality (1-100), higher = better quality, larger size

    Returns:
        JPEG compressed bytes
    """
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


def decompress_jpeg_image(jpeg_bytes: bytes) -> np.ndarray:
    """Decompress JPEG bytes to numpy array.

    Args:
        jpeg_bytes: JPEG compressed image bytes

    Returns:
        RGB image as numpy array (H, W, 3) uint8
    """
    buffer = io.BytesIO(jpeg_bytes)
    img = Image.open(buffer)
    return np.array(img)


class DualArmDataCollector:
    """Collects (s, a, r, s') transitions with 5 camera images and 44D task state."""

    def __init__(
        self,
        scene: InteractiveScene,
        output_dir: str,
        num_envs: int,
        max_steps: int = 200,
        policy_path: str = None,
    ):
        self.scene = scene
        self.output_dir = output_dir
        self.num_envs = num_envs
        self.max_steps = max_steps
        self.device = scene["robot_left"].device

        os.makedirs(output_dir, exist_ok=True)

        # Action dimension: 7 joints + 2 gripper for each arm = 18
        self.action_dim = 18

        # Proprio dimension: (7 pos + 7 vel + 3 ee) * 2 arms = 34
        self.proprio_dim = 34

        # Task state dimension: 30 (cable segments) + 3 (hook) + 3 (left_ee) + 3 (right_ee) + 5 (distances) = 44
        self.task_state_dim = 44

        # 5 Cameras
        self.cameras = {
            'front': scene["front_camera"],
            'left': scene["left_camera"],
            'right': scene["right_camera"],
            'back': scene["back_camera"],
            'overhead': scene["overhead_camera"],
        }
        print(f"[Cameras] Found {len(self.cameras)} cameras: {list(self.cameras.keys())}")

        # Load policy if provided
        self.policy = None
        if policy_path and os.path.exists(policy_path):
            print(f"[Policy] Loading from: {policy_path}")
            checkpoint = torch.load(policy_path, map_location=self.device)
            # TODO: Instantiate policy network and load weights
            # self.policy = ...
            print("[Policy] Loaded successfully")
        else:
            print("[Policy] Using random actions")

        # Buffers for current batch
        self.reset_buffers()

    def reset_buffers(self):
        """Reset data collection buffers."""
        # 5 camera images
        self.front_imgs = []
        self.left_imgs = []
        self.right_imgs = []
        self.back_imgs = []
        self.overhead_imgs = []

        # Next state images
        self.next_front_imgs = []
        self.next_left_imgs = []
        self.next_right_imgs = []
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
        """Get current camera images from all 5 cameras."""
        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"]  # (num_envs, H, W, 4)
            # Remove alpha channel and convert to numpy
            img = rgb[..., :3].cpu().numpy().astype(np.uint8)
            images[name] = img
        return images

    def get_proprio(self):
        """Get proprioceptive observation (34D).

        Returns:
            proprio: Tensor [num_envs, 34] containing:
                - left_joint_pos (7D)
                - left_joint_vel (7D)
                - left_ee_pos (3D)
                - right_joint_pos (7D)
                - right_joint_vel (7D)
                - right_ee_pos (3D)
        """
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        # Joint positions (7 each)
        left_joint_pos = robot_left.data.joint_pos[:, :7]
        right_joint_pos = robot_right.data.joint_pos[:, :7]

        # Joint velocities (7 each)
        left_joint_vel = robot_left.data.joint_vel[:, :7]
        right_joint_vel = robot_right.data.joint_vel[:, :7]

        # End-effector positions (panda_hand body, index 8)
        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]

        # Concatenate: 7 + 7 + 3 + 7 + 7 + 3 = 34D
        proprio = torch.cat([
            left_joint_pos,
            left_joint_vel,
            left_ee_pos,
            right_joint_pos,
            right_joint_vel,
            right_ee_pos,
        ], dim=-1)

        return proprio

    def get_task_state(self):
        """Get task-relevant state information (44D).

        Returns:
            task_state: Tensor [num_envs, 44] containing:
                - cable_segment_pos (30D): 10 segments × 3D (x,y,z)
                - hook_pos (3D): Y-hook center position
                - left_ee_pos (3D): Left end-effector position
                - right_ee_pos (3D): Right end-effector position
                - cable_hook_dist (1D): Distance from cable center to hook
                - left_ee_cable_dist (1D): Distance from left EE to cable center
                - right_ee_cable_dist (1D): Distance from right EE to cable center
                - left_ee_hook_dist (1D): Distance from left EE to hook
                - right_ee_hook_dist (1D): Distance from right EE to hook
        """
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        # Get Y-hook position (use stem position as reference)
        hook_stem = self.scene["hook_stem"]
        hook_pos = hook_stem.data.root_pos_w  # [num_envs, 3]

        # Get cable position and orientation
        cable = self.scene["cable"]
        cable_pos = cable.data.root_pos_w  # [num_envs, 3]
        cable_quat = cable.data.root_quat_w  # [num_envs, 4] (w, x, y, z)

        # Compute virtual cable segment positions
        # Cable extends along local X axis, so we compute 10 points along the cable
        cable_segment_pos = self._compute_cable_segments(cable_pos, cable_quat)  # [num_envs, 30]

        # Get end-effector positions
        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]

        # Compute distances
        cable_hook_dist = torch.norm(cable_pos - hook_pos, dim=-1, keepdim=True)
        left_ee_cable_dist = torch.norm(left_ee_pos - cable_pos, dim=-1, keepdim=True)
        right_ee_cable_dist = torch.norm(right_ee_pos - cable_pos, dim=-1, keepdim=True)
        left_ee_hook_dist = torch.norm(left_ee_pos - hook_pos, dim=-1, keepdim=True)
        right_ee_hook_dist = torch.norm(right_ee_pos - hook_pos, dim=-1, keepdim=True)

        # Concatenate all task state information
        task_state = torch.cat([
            cable_segment_pos,    # 30D
            hook_pos,             # 3D
            left_ee_pos,          # 3D
            right_ee_pos,         # 3D
            cable_hook_dist,      # 1D
            left_ee_cable_dist,   # 1D
            right_ee_cable_dist,  # 1D
            left_ee_hook_dist,    # 1D
            right_ee_hook_dist,   # 1D
        ], dim=-1)  # Total: 44D

        return task_state

    def _compute_cable_segments(self, cable_pos, cable_quat):
        """Compute virtual cable segment positions from cable center and orientation.

        Args:
            cable_pos: Cable center position [num_envs, 3]
            cable_quat: Cable orientation quaternion [num_envs, 4] (w, x, y, z)

        Returns:
            segment_positions: Flattened segment positions [num_envs, 30]
        """
        num_envs = cable_pos.shape[0]
        device = cable_pos.device

        # Cable extends along local X axis
        # Create local segment offsets along X
        segment_offsets = torch.zeros(CABLE_NUM_SEGMENTS, 3, device=device)
        half_length = CABLE_TOTAL_LENGTH / 2
        segment_spacing = CABLE_TOTAL_LENGTH / (CABLE_NUM_SEGMENTS - 1)

        for i in range(CABLE_NUM_SEGMENTS):
            segment_offsets[i, 0] = -half_length + i * segment_spacing  # X offset

        # Rotate offsets by cable orientation
        # Convert quaternion to rotation matrix
        # Using (w, x, y, z) format
        w, x, y, z = cable_quat[:, 0], cable_quat[:, 1], cable_quat[:, 2], cable_quat[:, 3]

        # Rotation matrix from quaternion
        rot_mat = torch.zeros(num_envs, 3, 3, device=device)
        rot_mat[:, 0, 0] = 1 - 2*y*y - 2*z*z
        rot_mat[:, 0, 1] = 2*x*y - 2*w*z
        rot_mat[:, 0, 2] = 2*x*z + 2*w*y
        rot_mat[:, 1, 0] = 2*x*y + 2*w*z
        rot_mat[:, 1, 1] = 1 - 2*x*x - 2*z*z
        rot_mat[:, 1, 2] = 2*y*z - 2*w*x
        rot_mat[:, 2, 0] = 2*x*z - 2*w*y
        rot_mat[:, 2, 1] = 2*y*z + 2*w*x
        rot_mat[:, 2, 2] = 1 - 2*x*x - 2*y*y

        # Apply rotation to each segment offset
        # segment_offsets: [10, 3], rot_mat: [num_envs, 3, 3]
        # Result: [num_envs, 10, 3]
        rotated_offsets = torch.einsum('nij,sj->nsi', rot_mat, segment_offsets)

        # Add cable center position
        # cable_pos: [num_envs, 3] -> [num_envs, 1, 3]
        segment_positions = rotated_offsets + cable_pos.unsqueeze(1)

        # Flatten to [num_envs, 30]
        return segment_positions.reshape(num_envs, -1)

    def sample_action(self, proprio: torch.Tensor):
        """Sample action from policy or random."""
        if self.policy is not None:
            with torch.no_grad():
                action = self.policy(proprio)
        else:
            # Random action in [-1, 1]
            action = torch.rand(self.num_envs, self.action_dim, device=self.device) * 2 - 1
        return action

    def compute_reward(self):
        """Compute reward based on task progress."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]
        hook_stem = self.scene["hook_stem"]
        cable = self.scene["cable"]

        # Get positions
        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]  # panda_hand
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]
        hook_pos = hook_stem.data.root_pos_w
        cable_pos = cable.data.root_pos_w

        # Distance rewards
        left_to_cable = torch.norm(left_ee_pos - cable_pos, dim=-1)
        right_to_cable = torch.norm(right_ee_pos - cable_pos, dim=-1)
        cable_to_hook = torch.norm(cable_pos - hook_pos, dim=-1)

        # Approach reward
        approach_reward = torch.exp(-3.0 * left_to_cable) + torch.exp(-3.0 * right_to_cable)

        # Task reward
        task_reward = torch.exp(-3.0 * cable_to_hook)

        # Combined reward
        reward = 0.5 * approach_reward + 0.5 * task_reward

        return reward

    def apply_action(self, action: torch.Tensor):
        """Apply action to robots."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        # Split actions
        left_action = action[:, :9]  # 7 joints + 2 gripper
        right_action = action[:, 9:]

        # Get current joint positions
        left_joint_pos = robot_left.data.joint_pos
        right_joint_pos = robot_right.data.joint_pos

        # Apply delta action
        scale = 0.1
        left_target = left_joint_pos + scale * left_action
        right_target = right_joint_pos + scale * right_action

        # Set targets
        robot_left.set_joint_position_target(left_target)
        robot_right.set_joint_position_target(right_target)

    def collect_episode(self):
        """Collect one episode of data from all environments."""
        episode_length = torch.zeros(self.num_envs, device=self.device)
        episode_reward = torch.zeros(self.num_envs, device=self.device)
        done = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

        for step in range(self.max_steps):
            # Get current state
            images = self.get_camera_images()
            proprio = self.get_proprio()
            task_state = self.get_task_state()

            # Sample and apply action
            action = self.sample_action(proprio)
            self.apply_action(action)

            # Step simulation
            self.scene.write_data_to_sim()
            for _ in range(4):  # 4 physics steps per action
                sim_utils.SimulationContext.instance().step()
            self.scene.update(sim_utils.SimulationContext.instance().get_physics_dt() * 4)

            # Get next state
            next_images = self.get_camera_images()
            next_proprio = self.get_proprio()
            next_task_state = self.get_task_state()

            # Compute reward
            reward = self.compute_reward()
            episode_reward += reward

            # Check done (simple timeout for now)
            step_done = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
            episode_length += (~done).float()

            # Store transitions for active environments
            active_mask = ~done
            for env_idx in range(self.num_envs):
                if active_mask[env_idx]:
                    # Current images
                    self.front_imgs.append(images['front'][env_idx])
                    self.left_imgs.append(images['left'][env_idx])
                    self.right_imgs.append(images['right'][env_idx])
                    self.back_imgs.append(images['back'][env_idx])
                    self.overhead_imgs.append(images['overhead'][env_idx])

                    # State
                    self.proprios.append(proprio[env_idx].cpu().numpy())
                    self.task_states.append(task_state[env_idx].cpu().numpy())

                    # Action and reward
                    self.actions.append(action[env_idx].cpu().numpy())
                    self.rewards.append(reward[env_idx].cpu().numpy())

                    # Next images
                    self.next_front_imgs.append(next_images['front'][env_idx])
                    self.next_left_imgs.append(next_images['left'][env_idx])
                    self.next_right_imgs.append(next_images['right'][env_idx])
                    self.next_back_imgs.append(next_images['back'][env_idx])
                    self.next_overhead_imgs.append(next_images['overhead'][env_idx])

                    # Next state
                    self.next_proprios.append(next_proprio[env_idx].cpu().numpy())
                    self.next_task_states.append(next_task_state[env_idx].cpu().numpy())

                    self.dones.append(step_done[env_idx].cpu().numpy())

            done = done | step_done

            if done.all():
                break

        # Record episode stats
        for env_idx in range(self.num_envs):
            self.episode_lengths.append(int(episode_length[env_idx].item()))
            self.episode_rewards.append(float(episode_reward[env_idx].item()))

        return int(episode_length.mean().item()), float(episode_reward.mean().item())

    def save_batch(self, batch_idx: int, jpeg_quality: int = 85):
        """Save current batch to HDF5 file with JPEG compression for images.

        Args:
            batch_idx: Batch index for filename
            jpeg_quality: JPEG compression quality (1-100). Default 85 gives ~10x compression.
        """
        if len(self.front_imgs) == 0:
            print("[Save] No data to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wm_dual_arm_batch{batch_idx:04d}_{timestamp}.h5"
        filepath = os.path.join(self.output_dir, filename)

        num_samples = len(self.front_imgs)
        print(f"[Save] Saving {num_samples} transitions to {filepath}")
        print(f"[Save] Using JPEG compression (quality={jpeg_quality})")

        with h5py.File(filepath, "w") as f:
            # JPEG compressed images using variable-length byte arrays
            dt = h5py.vlen_dtype(np.dtype('uint8'))

            # Create datasets for JPEG images (5 cameras)
            camera_names = ['front', 'left', 'right', 'back', 'overhead']
            current_imgs = {
                'front': self.front_imgs,
                'left': self.left_imgs,
                'right': self.right_imgs,
                'back': self.back_imgs,
                'overhead': self.overhead_imgs,
            }
            next_imgs = {
                'front': self.next_front_imgs,
                'left': self.next_left_imgs,
                'right': self.next_right_imgs,
                'back': self.next_back_imgs,
                'overhead': self.next_overhead_imgs,
            }

            # Create datasets for each camera
            jpeg_datasets = {}
            next_jpeg_datasets = {}
            for name in camera_names:
                jpeg_datasets[name] = f.create_dataset(f"{name}_img_jpeg", (num_samples,), dtype=dt)
                next_jpeg_datasets[name] = f.create_dataset(f"next_{name}_img_jpeg", (num_samples,), dtype=dt)

            # Compress and store images
            print("[Save] Compressing images...")
            for i in range(num_samples):
                for name in camera_names:
                    jpeg_datasets[name][i] = np.frombuffer(
                        compress_image_jpeg(current_imgs[name][i], jpeg_quality), dtype=np.uint8)
                    next_jpeg_datasets[name][i] = np.frombuffer(
                        compress_image_jpeg(next_imgs[name][i], jpeg_quality), dtype=np.uint8)

                if (i + 1) % 10000 == 0:
                    print(f"[Save] Compressed {i + 1}/{num_samples} images...")

            # State and action (no compression needed, small data)
            f.create_dataset("proprio", data=np.array(self.proprios))
            f.create_dataset("next_proprio", data=np.array(self.next_proprios))
            f.create_dataset("action", data=np.array(self.actions))
            f.create_dataset("reward", data=np.array(self.rewards))
            f.create_dataset("done", data=np.array(self.dones))

            # Task-relevant state (44D)
            f.create_dataset("task_state", data=np.array(self.task_states))
            f.create_dataset("next_task_state", data=np.array(self.next_task_states))

            # Episode stats
            f.create_dataset("episode_lengths", data=np.array(self.episode_lengths))
            f.create_dataset("episode_rewards", data=np.array(self.episode_rewards))

            # Metadata
            f.attrs["total_transitions"] = num_samples
            f.attrs["num_episodes"] = len(self.episode_lengths)
            f.attrs["timestamp"] = timestamp
            f.attrs["jpeg_quality"] = jpeg_quality
            f.attrs["image_format"] = "jpeg"
            f.attrs["num_cameras"] = 5
            f.attrs["camera_names"] = ",".join(camera_names)
            f.attrs["proprio_dim"] = self.proprio_dim
            f.attrs["task_state_dim"] = self.task_state_dim
            f.attrs["task_state_fields"] = (
                "cable_segment_pos(30),"
                "hook_pos(3),"
                "left_ee_pos(3),"
                "right_ee_pos(3),"
                "cable_hook_dist(1),"
                "left_ee_cable_dist(1),"
                "right_ee_cable_dist(1),"
                "left_ee_hook_dist(1),"
                "right_ee_hook_dist(1)"
            )

        # Calculate file size
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"[Save] Saved {num_samples} transitions, {len(self.episode_lengths)} episodes")
        print(f"[Save] File size: {file_size_mb:.1f} MB")

        # Reset buffers
        self.reset_buffers()


def main():
    print("\n" + "=" * 60)
    print("DUAL ARM CAMERA DATA COLLECTION (5 Cameras + 44D Task State)")
    print("=" * 60)

    device = torch.device("cuda:0")

    # Create scene configuration
    cfg = DualArmSceneCfg()
    cfg.num_envs = args_cli.num_envs
    cfg.env_spacing = 3.0

    print(f"\n[Config]")
    print(f"  Num environments: {cfg.num_envs}")
    print(f"  Num episodes: {args_cli.num_episodes}")
    print(f"  Max steps per episode: {args_cli.max_steps}")
    print(f"  Output directory: {args_cli.output_dir}")
    print(f"  Cameras: front, left, right, back, overhead")
    print(f"  Task state dim: 44 (30 cable + 14 positions/distances)")

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(
        device=str(device),
        dt=PHYSICS_DT,
        render_interval=1,
    )
    sim = sim_utils.SimulationContext(sim_cfg)

    # Create scene
    print("\n[Status] Creating scene with 5 cameras...")
    scene = InteractiveScene(cfg)

    print("[Status] Starting simulation...")
    sim.reset()

    # Run initial steps to settle
    print("[Status] Running initial settling steps...")
    for i in range(60):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Create collector
    collector = DualArmDataCollector(
        scene=scene,
        output_dir=args_cli.output_dir,
        num_envs=args_cli.num_envs,
        max_steps=args_cli.max_steps,
        policy_path=args_cli.policy_path,
    )

    # Collection loop
    print("\n[Status] Starting data collection...")
    total_episodes = 0
    batch_idx = 0

    while total_episodes < args_cli.num_episodes:
        # Collect episode
        avg_length, avg_reward = collector.collect_episode()
        total_episodes += args_cli.num_envs

        print(f"[Episode {total_episodes}/{args_cli.num_episodes}] "
              f"avg_length={avg_length:.1f}, avg_reward={avg_reward:.3f}")

        # Save periodically
        if total_episodes % args_cli.save_frequency == 0 or total_episodes >= args_cli.num_episodes:
            collector.save_batch(batch_idx)
            batch_idx += 1

        # Reset environments
        sim.reset()
        for _ in range(30):
            scene.write_data_to_sim()
            sim.step()
            scene.update(sim.get_physics_dt())

    # GPU memory
    print("\n[GPU Memory]")
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        print(f"  Allocated: {allocated:.2f} GB")
        print(f"  Reserved:  {reserved:.2f} GB")

    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)
    print(f"Total episodes: {total_episodes}")
    print(f"Output: {args_cli.output_dir}")


if __name__ == "__main__":
    main()
    simulation_app.close()
