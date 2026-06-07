#!/usr/bin/env python3
"""
Collect Expert Demonstration Data for World Model Training.

This script collects expert demonstrations from the phase-based cable-on-hook
manipulation workflow, saving observations and actions in HDF5 format.

Data collected per step:
- 4 camera images (256x256, JPEG compressed): front_left, front_right, back, overhead
- proprio (34D): joint positions, velocities, EE positions for both arms
- task_state (44D): cable segments, hook, EE positions, distances
- action (18D): 7 joint deltas + 2 gripper per arm

Usage:
    cd /home/rlrk/IsaacLab
    DISPLAY=:1 CUDA_VISIBLE_DEVICES=0 timeout 1800 env_isaaclab/bin/python \
        thread_isaac_lab/scripts/collect_demo_data.py \
        --num_cycles 5 --output_dir data/demo_data_v1

Output:
    data/demo_data_v1/demo_cycle_XXXX.h5
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

parser = argparse.ArgumentParser()
parser.add_argument("--num_cycles", type=int, default=5, help="Number of cycles to collect")
parser.add_argument("--output_dir", type=str, default="data/demo_data_v1", help="Output directory")
parser.add_argument("--image_size", type=int, default=256, help="Image size (square)")
parser.add_argument("--jpeg_quality", type=int, default=85, help="JPEG compression quality")
parser.add_argument("--save_video", action="store_true", help="Save 2x2 grid video")
parser.add_argument("--video_output", type=str, default="data/videos/demo_collection.mp4", help="Video output path")
parser.add_argument("--video_fps", type=int, default=30, help="Video frame rate")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import h5py
import torch
import numpy as np
import shutil
import subprocess
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS,
    PHASE45_LEFT_JOINTS, PHASE45_RIGHT_JOINTS,
    PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
    PHASE55_LEFT_JOINTS, PHASE55_RIGHT_JOINTS,
    PHASE7_LEFT_JOINTS, PHASE7_RIGHT_JOINTS,
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE45A_LEFT, WAYPOINT_PHASE45A_RIGHT,
    WAYPOINT_PHASE45B_LEFT, WAYPOINT_PHASE45B_RIGHT,
    WAYPOINT_PHASE45C_LEFT, WAYPOINT_PHASE45C_RIGHT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    WAYPOINT_PHASE7_LEFT, WAYPOINT_PHASE7_RIGHT,
    GRIPPER_CLOSE, GRIPPER_OPEN,
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS, PHASE55_TO_6_STEPS,
    CYCLE_RESET_STABILIZATION_STEPS,
    HOOK_X, HOOK_Y, HOOK_Z,
)

# Constants
HIGH_FRICTION = 5.0
Z_OFFSET = 0.1173  # Corrected: fingertip at cable Z=0.755, panda_hand = 0.755 + 0.1123 = 0.8673

# Phase step counts
PHASE1_STEPS = 100
PHASE12_STEPS = 300
GRASP_CLOSE_STEPS = 100  # Gradual gripper close (like opt_b)
GRASP_STABILIZE = 100
LIFT_STEPS = 1600  # Double slow lift for NaN prevention
PHASE34_STEPS = 400
PHASE445_STEPS = 300
PHASE455_STEPS = 300
PHASE55_STEPS = 200
POST_RETREAT_STEPS = 200
PHASE67_STEPS = 400
LIFT_CM = 10.0  # Target: 10cm lift with cable v5 + damping=80.0

# Frame collection interval
# シミュレーション240Hz、収集間隔4ステップ = 60Hz収集
# 動画長を維持しながらフレーム数を増やす
FRAME_COLLECT_INTERVAL = 4  # 20→4に変更で5倍のフレーム数

# Video frame skip (save every N data collection steps)
# データ収集ステップ数に対するスキップ数
# 1 = 全データステップでビデオフレーム保存（最大フレーム数）
# 2 = 2ステップに1回保存（フレーム数半分）
VIDEO_FRAME_SKIP = 1  # 全データステップでビデオフレーム保存

# Data dimensions
PROPRIO_DIM = 34
TASK_STATE_DIM = 44
ACTION_DIM = 18

os.makedirs(args.output_dir, exist_ok=True)

# Video recording setup
VIDEO_FRAME_DIR = "/tmp/demo_video_frames"
video_frame_count = 0
video_collect_counter = 0  # Track data collection steps for video frame skip

if args.save_video:
    os.makedirs(VIDEO_FRAME_DIR, exist_ok=True)
    # Clear old frames
    for f in os.listdir(VIDEO_FRAME_DIR):
        os.remove(os.path.join(VIDEO_FRAME_DIR, f))
    video_output_dir = os.path.dirname(args.video_output)
    if video_output_dir:
        os.makedirs(video_output_dir, exist_ok=True)

print("=" * 70)
print("EXPERT DEMONSTRATION DATA COLLECTION")
print(f"Cycles: {args.num_cycles}")
print(f"Output: {args.output_dir}")
if args.save_video:
    print(f"Video: {args.video_output} ({args.video_fps} fps)")
print("=" * 70)


def compress_image_jpeg(img_array: np.ndarray, quality: int = 85) -> bytes:
    """Compress numpy image array to JPEG bytes."""
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


def save_video_frame(images: dict, resolution: int = 512):
    """Save 3x2 grid frame for video (5 cameras + 1 empty slot).

    Args:
        images: Dictionary of camera name -> numpy array
        resolution: Output resolution per camera
    """
    global video_frame_count, video_collect_counter
    if not args.save_video:
        return

    # Skip frames based on VIDEO_FRAME_SKIP
    video_collect_counter += 1
    if video_collect_counter % VIDEO_FRAME_SKIP != 0:
        return

    # Resize images
    resized = {}
    for name, img_array in images.items():
        img = Image.fromarray(img_array)
        resized[name] = img.resize((resolution, resolution), Image.LANCZOS)

    # Create 3x2 grid (3 columns, 2 rows)
    # Layout:
    # front_left | front_center | front_right
    # back       | overhead     | (empty)
    grid = Image.new('RGB', (resolution * 3, resolution * 2))
    grid.paste(resized["front_left"], (0, 0))
    grid.paste(resized["front_center"], (resolution, 0))
    grid.paste(resized["front_right"], (resolution * 2, 0))
    grid.paste(resized["back"], (0, resolution))
    grid.paste(resized["overhead"], (resolution, resolution))
    # Bottom-right slot left empty (black)

    # Save frame
    grid.save(os.path.join(VIDEO_FRAME_DIR, f"frame_{video_frame_count:06d}.png"))
    video_frame_count += 1


class DemoDataCollector:
    """Collects expert demonstration data during phase-based manipulation."""

    def __init__(self, scene, sim, output_dir: str, image_size: int = 256, jpeg_quality: int = 85):
        self.scene = scene
        self.sim = sim
        self.output_dir = output_dir
        self.image_size = image_size
        self.jpeg_quality = jpeg_quality
        self.device = scene["robot_left"].device

        # Cameras
        self.cameras = {
            'front_left': scene["front_left_camera"],
            'front_right': scene["front_right_camera"],
            'back': scene["back_camera"],
            'overhead': scene["overhead_camera"],
            'front_center': scene["front_center_camera"],
        }
        print(f"[Cameras] Found {len(self.cameras)} cameras")

        # Store previous state for action calculation
        self.prev_joint_pos_left = None
        self.prev_joint_pos_right = None
        self.prev_gripper_left = None
        self.prev_gripper_right = None

        self.reset_buffers()

    def reset_buffers(self):
        """Reset data collection buffers."""
        self.front_left_imgs = []
        self.front_right_imgs = []
        self.back_imgs = []
        self.overhead_imgs = []
        self.proprios = []
        self.task_states = []
        self.actions = []
        self.phases = []
        self.step_count = 0

    def get_camera_images(self) -> dict:
        """Get current camera images from all 4 cameras."""
        # Update cameras
        for cam in self.cameras.values():
            cam.update(self.sim.get_physics_dt())

        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"][0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            images[name] = rgb.astype(np.uint8)
        return images

    def get_proprio(self) -> np.ndarray:
        """Get proprioceptive observation (34D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        left_joint_pos = robot_left.data.joint_pos[0, :7].cpu().numpy()
        right_joint_pos = robot_right.data.joint_pos[0, :7].cpu().numpy()
        left_joint_vel = robot_left.data.joint_vel[0, :7].cpu().numpy()
        right_joint_vel = robot_right.data.joint_vel[0, :7].cpu().numpy()
        left_ee_pos = robot_left.data.body_pos_w[0, 8, :].cpu().numpy()
        right_ee_pos = robot_right.data.body_pos_w[0, 8, :].cpu().numpy()

        proprio = np.concatenate([
            left_joint_pos, left_joint_vel, left_ee_pos,
            right_joint_pos, right_joint_vel, right_ee_pos,
        ])
        return proprio.astype(np.float32)

    def get_task_state(self) -> np.ndarray:
        """Get task-relevant state information (44D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]
        cable = self.scene["cable"]
        hook_stem = self.scene["hook_stem"]

        # Hook position
        hook_pos = hook_stem.data.root_pos_w[0].cpu().numpy()

        # Cable root position and orientation
        cable_pos = cable.data.root_pos_w[0].cpu().numpy()
        cable_quat = cable.data.root_quat_w[0].cpu().numpy()

        # Handle NaN values from unstable physics
        if np.any(np.isnan(cable_pos)) or np.any(np.isnan(cable_quat)):
            cable_pos = np.zeros(3, dtype=np.float32)
            cable_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

        # Compute virtual cable segment positions (10 segments x 3D = 30D)
        segment_positions = self._compute_cable_segments(cable_pos, cable_quat)

        # EE positions
        left_ee_pos = robot_left.data.body_pos_w[0, 8, :].cpu().numpy()
        right_ee_pos = robot_right.data.body_pos_w[0, 8, :].cpu().numpy()

        # Distances
        cable_center = cable_pos
        cable_hook_dist = np.linalg.norm(cable_center - hook_pos)
        left_ee_cable_dist = np.linalg.norm(left_ee_pos - cable_center)
        right_ee_cable_dist = np.linalg.norm(right_ee_pos - cable_center)
        left_ee_hook_dist = np.linalg.norm(left_ee_pos - hook_pos)
        right_ee_hook_dist = np.linalg.norm(right_ee_pos - hook_pos)

        task_state = np.concatenate([
            segment_positions.flatten(),  # 30D
            hook_pos,  # 3D
            left_ee_pos,  # 3D
            right_ee_pos,  # 3D
            [cable_hook_dist, left_ee_cable_dist, right_ee_cable_dist,
             left_ee_hook_dist, right_ee_hook_dist],  # 5D
        ])

        # Final NaN check
        task_state = np.nan_to_num(task_state, nan=0.0, posinf=10.0, neginf=-10.0)
        return task_state.astype(np.float32)

    def _compute_cable_segments(self, cable_pos: np.ndarray, cable_quat: np.ndarray) -> np.ndarray:
        """Compute virtual cable segment positions (10 segments)."""
        num_segments = 10
        cable_length = 0.5  # Approximate cable length

        # Convert quaternion to direction vector (local X axis)
        w, x, y, z = cable_quat
        R00 = 1 - 2 * (y * y + z * z)
        R10 = 2 * (x * y + z * w)
        R20 = 2 * (x * z - y * w)
        local_x = np.array([R00, R10, R20])

        # Compute segment positions along cable
        segment_offsets = np.linspace(-cable_length / 2, cable_length / 2, num_segments)
        segment_positions = cable_pos + segment_offsets[:, np.newaxis] * local_x
        return segment_positions

    def compute_action(self, gripper_left: float, gripper_right: float) -> np.ndarray:
        """Compute action from joint position changes."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        curr_joint_pos_left = robot_left.data.joint_pos[0, :7].cpu().numpy()
        curr_joint_pos_right = robot_right.data.joint_pos[0, :7].cpu().numpy()

        if self.prev_joint_pos_left is None:
            # First step: zero action
            action = np.zeros(ACTION_DIM, dtype=np.float32)
        else:
            # Compute delta
            delta_left = curr_joint_pos_left - self.prev_joint_pos_left
            delta_right = curr_joint_pos_right - self.prev_joint_pos_right
            gripper_delta_left = gripper_left - self.prev_gripper_left
            gripper_delta_right = gripper_right - self.prev_gripper_right

            action = np.concatenate([
                delta_left,  # 7D
                [gripper_delta_left, gripper_delta_left],  # 2D (both fingers)
                delta_right,  # 7D
                [gripper_delta_right, gripper_delta_right],  # 2D
            ]).astype(np.float32)

        # Update previous state
        self.prev_joint_pos_left = curr_joint_pos_left.copy()
        self.prev_joint_pos_right = curr_joint_pos_right.copy()
        self.prev_gripper_left = gripper_left
        self.prev_gripper_right = gripper_right

        return action

    def collect_step(self, phase: int, gripper_left: float, gripper_right: float):
        """Collect one step of demonstration data.

        Args:
            phase: Current phase number
            gripper_left: Left gripper position
            gripper_right: Right gripper position
        """
        # Get observations
        images = self.get_camera_images()
        proprio = self.get_proprio()
        task_state = self.get_task_state()
        action = self.compute_action(gripper_left, gripper_right)

        # Store data (compressed images)
        self.front_left_imgs.append(compress_image_jpeg(images['front_left'], self.jpeg_quality))
        self.front_right_imgs.append(compress_image_jpeg(images['front_right'], self.jpeg_quality))
        self.back_imgs.append(compress_image_jpeg(images['back'], self.jpeg_quality))
        self.overhead_imgs.append(compress_image_jpeg(images['overhead'], self.jpeg_quality))
        self.proprios.append(proprio)
        self.task_states.append(task_state)
        self.actions.append(action)
        self.phases.append(phase)
        self.step_count += 1

        # Save video frame (respects VIDEO_FRAME_SKIP)
        save_video_frame(images)

    def save_cycle(self, cycle_idx: int):
        """Save collected cycle data to HDF5 file."""
        filename = os.path.join(self.output_dir, f"demo_cycle_{cycle_idx:04d}.h5")
        print(f"[Save] Saving {len(self.proprios)} steps to {filename}")

        with h5py.File(filename, 'w') as f:
            # Images (variable length JPEG bytes)
            # Create vlen datasets and write one by one to avoid numpy object array issues
            dt = h5py.special_dtype(vlen=np.uint8)
            n_steps = len(self.front_left_imgs)

            # Create datasets
            ds_fl = f.create_dataset('front_left_img', shape=(n_steps,), dtype=dt)
            ds_fr = f.create_dataset('front_right_img', shape=(n_steps,), dtype=dt)
            ds_back = f.create_dataset('back_img', shape=(n_steps,), dtype=dt)
            ds_oh = f.create_dataset('overhead_img', shape=(n_steps,), dtype=dt)

            # Write data one by one
            for i in range(n_steps):
                ds_fl[i] = np.frombuffer(self.front_left_imgs[i], dtype=np.uint8)
                ds_fr[i] = np.frombuffer(self.front_right_imgs[i], dtype=np.uint8)
                ds_back[i] = np.frombuffer(self.back_imgs[i], dtype=np.uint8)
                ds_oh[i] = np.frombuffer(self.overhead_imgs[i], dtype=np.uint8)

            # State data
            f.create_dataset('proprio', data=np.array(self.proprios), dtype=np.float32)
            f.create_dataset('task_state', data=np.array(self.task_states), dtype=np.float32)
            f.create_dataset('action', data=np.array(self.actions), dtype=np.float32)
            f.create_dataset('phase', data=np.array(self.phases), dtype=np.int32)

            # Metadata
            f.attrs['num_steps'] = len(self.proprios)
            f.attrs['num_cameras'] = 4
            f.attrs['camera_names'] = ['front_left', 'front_right', 'back', 'overhead']
            f.attrs['proprio_dim'] = PROPRIO_DIM
            f.attrs['task_state_dim'] = TASK_STATE_DIM
            f.attrs['action_dim'] = ACTION_DIM
            f.attrs['cycle_idx'] = cycle_idx
            f.attrs['timestamp'] = datetime.now().isoformat()
            f.attrs['success'] = True

        print(f"[Save] Done: {len(self.proprios)} steps saved")
        self.reset_buffers()


# Setup simulation
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)


@configclass
class TestSceneCfg(DualArmSceneCfg):
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


scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)
sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
device = robot_left.device

# Store initial cable state for reset
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

# Setup Diff IK
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.2},  # Best performing value (90.3% at 2000 steps)
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

# Create data collector
collector = DemoDataCollector(scene, sim, args.output_dir, args.image_size, args.jpeg_quality)

# ============================================================
# INITIAL CABLE STABILIZATION (Critical for NaN prevention)
# ============================================================
print("\n[Init] Stabilizing cable physics...")
cable.write_root_state_to_sim(initial_cable_root_state)
for _ in range(CYCLE_RESET_STABILIZATION_STEPS * 2):  # Double stabilization on first init
    sim.step()
    scene.update(sim.get_physics_dt())

# Verify cable state is valid
cable_pos_init = cable.data.root_pos_w[0].cpu().numpy()
if np.any(np.isnan(cable_pos_init)):
    print(f"  [ERROR] Cable position is NaN after initialization!")
    print(f"  Cable pos: {cable_pos_init}")
else:
    print(f"  [OK] Cable position: {cable_pos_init}")
print("[Init] Cable stabilization complete")
# 2026-01-06: 全セグメントの状態を保存（root_state_wは1セグメントのみで不完全）
initial_cable_body_state = cable.data.body_state_w.clone()  # [1, 20, 13] 全セグメント
initial_cable_joint_pos = cable.data.joint_pos.clone()
initial_cable_joint_vel = cable.data.joint_vel.clone()
initial_robot_left_state = robot_left.data.root_state_w.clone()
initial_robot_right_state = robot_right.data.root_state_w.clone()
initial_joint_pos_left = robot_left.data.joint_pos.clone()
initial_joint_vel_left = robot_left.data.joint_vel.clone()
initial_joint_pos_right = robot_right.data.joint_pos.clone()
initial_joint_vel_right = robot_right.data.joint_vel.clone()

# 2026-01-07: Identify cable root body index by comparing root_pos_w with body_state_w positions
# This is critical for correct reset - write_root_state_to_sim expects root body state
cable_root_pos = cable.data.root_pos_w[0]  # [3]
cable_body_positions = initial_cable_body_state[0, :, :3]  # [20, 3]
distances = torch.norm(cable_body_positions - cable_root_pos.unsqueeze(0), dim=1)
cable_root_body_idx = distances.argmin().item()
print(f"  [OK] Cable root body identified: seg_{cable_root_body_idx}")
print(f"       Root position: {cable_root_pos.cpu().numpy()}")
print(f"       seg_0 position:  {cable_body_positions[0].cpu().numpy()}")
print(f"       seg_10 position: {cable_body_positions[10].cpu().numpy()}")
print(f"       seg_19 position: {cable_body_positions[19].cpu().numpy()}")

# 2026-01-07: Check body_names order for debugging
print(f"  [Debug] Cable body_names (first 5): {cable.body_names[:5]}")
print(f"  [Debug] Cable body_names (last 5): {cable.body_names[-5:]}")
# Find actual left end (most negative Y) and right end (most positive Y)
# 2026-01-07: body_names order is NOT numerical! e.g., ['seg_9', 'seg_8', ...]
# We need to find correct indices for actual endpoints
y_positions = cable_body_positions[:, 1]
left_end_idx = y_positions.argmin().item()  # Index of leftmost segment (most negative Y)
right_end_idx = y_positions.argmax().item()  # Index of rightmost segment (most positive Y)
print(f"  [Debug] Actual left end: idx={left_end_idx} ({cable.body_names[left_end_idx]}), Y={y_positions[left_end_idx].item():.4f}")
print(f"  [Debug] Actual right end: idx={right_end_idx} ({cable.body_names[right_end_idx]}), Y={y_positions[right_end_idx].item():.4f}")

print(f"  [OK] Initial states saved after stabilization")
print(f"  Cable body_state shape: {initial_cable_body_state.shape}")  # 期待: [1, 20, 13]
print(f"  Cable joint_pos shape: {initial_cable_joint_pos.shape}")


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


def check_cable_nan_detailed(cable_obj):
    """Check each segment for NaN and return first NaN segment info."""
    num_segs = cable_obj.data.body_pos_w.shape[1]
    pos = cable_obj.data.body_pos_w[0]  # (num_segments, 3)
    vel = cable_obj.data.body_lin_vel_w[0]  # (num_segments, 3)

    for i in range(num_segs):
        if torch.any(torch.isnan(pos[i])) or torch.any(torch.isnan(vel[i])):
            return i, pos.cpu().numpy(), vel.cpu().numpy()
    return -1, pos.cpu().numpy(), vel.cpu().numpy()


def run_arc_rotation_with_collection(
    start_pos_left, start_pos_right, start_quat_left, start_quat_right,
    target_pos_left, target_pos_right, num_steps, gripper_val, phase: int
):
    """
    Rotate both grippers along an arc to maintain constant gripper distance.

    The rotation is done around the midpoint of the cable (center between grippers),
    maintaining the initial gripper distance throughout the rotation.
    """
    diff_ik_left.reset()
    diff_ik_right.reset()

    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # Get initial positions
    start_l = start_pos_left[0].cpu().numpy()  # [x, y, z]
    start_r = start_pos_right[0].cpu().numpy()
    target_l = target_pos_left[0].cpu().numpy()
    target_r = target_pos_right[0].cpu().numpy()

    # Calculate center point (midpoint between left and right grippers)
    start_center = (start_l + start_r) / 2  # [x, y, z]
    target_center = (target_l + target_r) / 2

    # Calculate initial radius from center to each gripper
    start_radius_l = np.linalg.norm(start_l[:2] - start_center[:2])  # XY distance
    start_radius_r = np.linalg.norm(start_r[:2] - start_center[:2])
    target_radius_l = np.linalg.norm(target_l[:2] - target_center[:2])
    target_radius_r = np.linalg.norm(target_r[:2] - target_center[:2])

    # Calculate initial and target angles (in XY plane, relative to center)
    start_angle_l = np.arctan2(start_l[1] - start_center[1], start_l[0] - start_center[0])
    start_angle_r = np.arctan2(start_r[1] - start_center[1], start_r[0] - start_center[0])
    target_angle_l = np.arctan2(target_l[1] - target_center[1], target_l[0] - target_center[0])
    target_angle_r = np.arctan2(target_r[1] - target_center[1], target_r[0] - target_center[0])

    # Debug info
    gripper_dist = np.linalg.norm(start_l - start_r)
    print(f"  Arc rotation: gripper_dist={gripper_dist:.3f}m")
    print(f"  Start angles: L={np.degrees(start_angle_l):.1f}°, R={np.degrees(start_angle_r):.1f}°")
    print(f"  Target angles: L={np.degrees(target_angle_l):.1f}°, R={np.degrees(target_angle_r):.1f}°")

    # NaN detection state
    last_good_pos = None
    last_good_vel = None
    nan_detected_step = -1

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Interpolate center position
        center = start_center + alpha * (target_center - start_center)

        # Interpolate angles and radii
        angle_l = start_angle_l + alpha * (target_angle_l - start_angle_l)
        angle_r = start_angle_r + alpha * (target_angle_r - start_angle_r)
        radius_l = start_radius_l + alpha * (target_radius_l - start_radius_l)
        radius_r = start_radius_r + alpha * (target_radius_r - start_radius_r)

        # Calculate gripper positions on arc (XY plane) + interpolated Z
        z = start_l[2] + alpha * (target_l[2] - start_l[2])

        pos_l = np.array([
            center[0] + radius_l * np.cos(angle_l),
            center[1] + radius_l * np.sin(angle_l),
            z
        ])
        pos_r = np.array([
            center[0] + radius_r * np.cos(angle_r),
            center[1] + radius_r * np.sin(angle_r),
            z
        ])

        # Convert to torch tensors
        cmd_pos_l = torch.tensor([pos_l], device=device, dtype=torch.float32)
        cmd_pos_r = torch.tensor([pos_r], device=device, dtype=torch.float32)

        cmd_l = torch.cat([cmd_pos_l, start_quat_left], dim=1)
        cmd_r = torch.cat([cmd_pos_r, start_quat_right], dim=1)

        diff_ik_left.set_command(cmd_l)
        diff_ik_right.set_command(cmd_r)

        jac_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
        jac_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

        ee_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        ee_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left]
        ee_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right]
        ee_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right]

        joint_pos_l = robot_left.data.joint_pos[:, :7]
        joint_pos_r = robot_right.data.joint_pos[:, :7]

        joint_cmd_l = diff_ik_left.compute(ee_pos_l, ee_quat_l, jac_left, joint_pos_l)
        joint_cmd_r = diff_ik_right.compute(ee_pos_r, ee_quat_r, jac_right, joint_pos_r)

        # v51: Joint delta clamping for stability (Phase 1-3)
        JOINT_DELTA_MAX = 0.02  # v51b: 0.02rad (GPU1)
        delta_l = joint_cmd_l[0] - joint_pos_l[0]
        delta_r = joint_cmd_r[0] - joint_pos_r[0]
        delta_l_clamped = torch.clamp(delta_l, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        delta_r_clamped = torch.clamp(delta_r, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        joint_cmd_l_safe = joint_pos_l + delta_l_clamped.unsqueeze(0)
        joint_cmd_r_safe = joint_pos_r + delta_r_clamped.unsqueeze(0)

        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = joint_cmd_l_safe[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r_safe[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # NaN detection and progress logging
        nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
        if nan_seg >= 0 and nan_detected_step < 0:
            nan_detected_step = i
            print(f"\n{'!'*70}")
            print(f"[NaN DETECTED] Phase {phase} (arc), Step {i}/{num_steps} ({alpha*100:.1f}%)")
            print(f"First NaN segment: seg_{nan_seg}")
            print(f"{'!'*70}")
            sys.stdout.flush()
            if last_good_pos is not None:
                print(f"\nLast good state (step {i-1}):")
                speeds = np.linalg.norm(last_good_vel, axis=1)
                top_speed_idx = np.argsort(speeds)[-3:][::-1]
                print(f"Top 3 fastest segments:")
                for idx in top_speed_idx:
                    print(f"  seg_{idx}: speed={speeds[idx]:.4f} m/s")
                sys.stdout.flush()
        elif nan_detected_step < 0:
            last_good_pos = pos_arr.copy()
            last_good_vel = vel_arr.copy()
            # Progress logging: every 100 steps
            if i % 100 == 0 or i == num_steps - 1:
                speeds = np.linalg.norm(vel_arr, axis=1)
                z_vals = pos_arr[:, 2]
                ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
                ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
                actual_dist = torch.norm(ee_l - ee_r).item()
                print(f"  [P{phase} arc {i:4d}/{num_steps}] EE dist={actual_dist:.3f}m L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f})")
                sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def run_joint_space_motion_with_collection(target_joints_left: list, target_joints_right: list,
                                           num_steps: int, gripper_val, phase: int):
    """Run joint space interpolation motion while collecting demonstration data.

    2026-01-07: Phase 4.5用に追加。Diff IKでは右腕が追従できないため、
    事前計算されたPHASE45_*_JOINTSを使用した関節空間補間に変更。

    Args:
        target_joints_left: Target joint angles for left arm (7 values)
        target_joints_right: Target joint angles for right arm (7 values)
        num_steps: Number of interpolation steps
        gripper_val: Gripper position value
        phase: Current phase number for logging
    """
    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # Get current joint positions
    start_joints_l = robot_left.data.joint_pos[:, :7].clone()
    start_joints_r = robot_right.data.joint_pos[:, :7].clone()

    # Convert target to tensors
    target_l = torch.tensor([target_joints_left], device=device, dtype=torch.float32)
    target_r = torch.tensor([target_joints_right], device=device, dtype=torch.float32)

    print(f"  [Joint Space] Start joints L[0]={start_joints_l[0,0]:.3f}, R[0]={start_joints_r[0,0]:.3f}")
    print(f"  [Joint Space] Target joints L[0]={target_l[0,0]:.3f}, R[0]={target_r[0,0]:.3f}")

    # Track cable state for NaN diagnosis
    last_good_pos = None
    last_good_vel = None
    nan_detected_step = -1

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Linear interpolation in joint space
        interp_l = start_joints_l + alpha * (target_l - start_joints_l)
        interp_r = start_joints_r + alpha * (target_r - start_joints_r)

        # Apply joint positions
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = interp_l[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = interp_r[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # NaN detection and progress logging
        nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
        if nan_seg >= 0 and nan_detected_step < 0:
            nan_detected_step = i
            print(f"\n{'!'*70}")
            print(f"[NaN DETECTED] Phase {phase} (Joint Space), Step {i}/{num_steps} ({alpha*100:.1f}%)")
            print(f"First NaN segment: seg_{nan_seg}")
            print(f"{'!'*70}")
            sys.stdout.flush()
            if last_good_pos is not None:
                print(f"\nLast good state (step {i-1}):")
                print(f"{'Seg':>4} | {'X':>8} {'Y':>8} {'Z':>8} | {'Speed':>8}")
                print("-" * 50)
                for j in range(len(last_good_pos)):
                    speed = np.linalg.norm(last_good_vel[j])
                    print(f"{j:4d} | {last_good_pos[j,0]:8.4f} {last_good_pos[j,1]:8.4f} {last_good_pos[j,2]:8.4f} | {speed:8.4f}")
                sys.stdout.flush()
        else:
            last_good_pos = pos_arr.copy()
            last_good_vel = vel_arr.copy()
            # Progress logging: every 100 steps
            if i % 100 == 0 or i == num_steps - 1:
                ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
                ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
                z_vals = pos_arr[:, 2]
                print(f"  [P{phase} step {i:4d}/{num_steps}] EE: L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f}) cable_Z: {z_vals.min():.3f}-{z_vals.max():.3f}")
                sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def run_diff_ik_motion_with_collection(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                                       target_pos_left, target_pos_right, num_steps, gripper_val, phase: int):
    """Run Diff IK motion while collecting demonstration data."""
    diff_ik_left.reset()
    diff_ik_right.reset()

    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # For Phase 3 (lift), track cable state for NaN diagnosis
    last_good_pos = None
    last_good_vel = None
    nan_detected_step = -1

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        pos_left = start_pos_left + alpha * (target_pos_left - start_pos_left)
        pos_right = start_pos_right + alpha * (target_pos_right - start_pos_right)

        cmd_left = torch.cat([pos_left, start_quat_left], dim=1)
        cmd_right = torch.cat([pos_right, start_quat_right], dim=1)

        diff_ik_left.set_command(cmd_left)
        diff_ik_right.set_command(cmd_right)

        jac_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
        jac_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

        ee_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        ee_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left]
        ee_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right]
        ee_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right]

        joint_pos_l = robot_left.data.joint_pos[:, :7]
        joint_pos_r = robot_right.data.joint_pos[:, :7]

        joint_cmd_l = diff_ik_left.compute(ee_pos_l, ee_quat_l, jac_left, joint_pos_l)
        joint_cmd_r = diff_ik_right.compute(ee_pos_r, ee_quat_r, jac_right, joint_pos_r)

        # v51: Joint delta clamping for stability
        JOINT_DELTA_MAX = 0.02  # v51b: 0.02rad (GPU1)
        delta_l = joint_cmd_l[0] - joint_pos_l[0]
        delta_r = joint_cmd_r[0] - joint_pos_r[0]
        delta_l_clamped = torch.clamp(delta_l, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        delta_r_clamped = torch.clamp(delta_r, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        joint_cmd_l_safe = joint_pos_l + delta_l_clamped.unsqueeze(0)
        joint_cmd_r_safe = joint_pos_r + delta_r_clamped.unsqueeze(0)

        # Debug: Check joint command delta for Phase 4.5 (phase=4)
        if phase == 4 and i % 100 == 0:
            delta_l_max = delta_l.abs().max().item()
            delta_r_max = delta_r.abs().max().item()
            clamped_l = (delta_l.abs() > JOINT_DELTA_MAX).any().item()
            clamped_r = (delta_r.abs() > JOINT_DELTA_MAX).any().item()
            print(f"  [IK Debug step {i}] delta_max: L={delta_l_max:.4f}rad R={delta_r_max:.4f}rad, clamped: L={clamped_l} R={clamped_r}")
            print(f"    Target EE: L=({pos_left[0,0]:.3f},{pos_left[0,1]:.3f},{pos_left[0,2]:.3f}) "
                  f"R=({pos_right[0,0]:.3f},{pos_right[0,1]:.3f},{pos_right[0,2]:.3f})")
            print(f"    Actual EE: L=({ee_pos_l[0,0]:.3f},{ee_pos_l[0,1]:.3f},{ee_pos_l[0,2]:.3f}) "
                  f"R=({ee_pos_r[0,0]:.3f},{ee_pos_r[0,1]:.3f},{ee_pos_r[0,2]:.3f})")
            # EE position error
            err_l = ((pos_left - ee_pos_l).pow(2).sum(dim=1)).sqrt().item()
            err_r = ((pos_right - ee_pos_r).pow(2).sum(dim=1)).sqrt().item()
            print(f"    EE error: L={err_l*100:.1f}cm R={err_r*100:.1f}cm")
            sys.stdout.flush()

        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = joint_cmd_l_safe[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r_safe[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # NaN detection and progress logging for all phases
        nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
        if nan_seg >= 0 and nan_detected_step < 0:
            nan_detected_step = i
            print(f"\n{'!'*70}")
            print(f"[NaN DETECTED] Phase {phase}, Step {i}/{num_steps} ({alpha*100:.1f}%)")
            print(f"First NaN segment: seg_{nan_seg}")
            print(f"{'!'*70}")
            sys.stdout.flush()
            if last_good_pos is not None:
                print(f"\nLast good state (step {i-1}):")
                print(f"{'Seg':>4} | {'X':>8} {'Y':>8} {'Z':>8} | {'Vx':>8} {'Vy':>8} {'Vz':>8} | {'Speed':>8}")
                print("-" * 80)
                for j in range(len(last_good_pos)):
                    speed = np.linalg.norm(last_good_vel[j])
                    print(f"{j:4d} | {last_good_pos[j,0]:8.4f} {last_good_pos[j,1]:8.4f} {last_good_pos[j,2]:8.4f} | "
                          f"{last_good_vel[j,0]:+8.4f} {last_good_vel[j,1]:+8.4f} {last_good_vel[j,2]:+8.4f} | {speed:8.4f}")
                # Find segments with highest speed
                speeds = np.linalg.norm(last_good_vel, axis=1)
                top_speed_idx = np.argsort(speeds)[-3:][::-1]
                print(f"\nTop 3 fastest segments:")
                for idx in top_speed_idx:
                    print(f"  seg_{idx}: speed={speeds[idx]:.4f} m/s")
                sys.stdout.flush()
        elif nan_detected_step < 0:
            last_good_pos = pos_arr.copy()
            last_good_vel = vel_arr.copy()
            # Progress logging: every 100 steps (regardless of phase)
            if i % 100 == 0 or i == num_steps - 1:
                speeds = np.linalg.norm(vel_arr, axis=1)
                z_vals = pos_arr[:, 2]
                max_speed_idx = np.argmax(speeds)
                ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
                ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
                print(f"  [P{phase} step {i:4d}/{num_steps}] EE: L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f}) cable_Z: {z_vals.min():.3f}-{z_vals.max():.3f}")
                sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def check_cable_nan() -> bool:
    """Check if cable position/orientation contains NaN.

    Returns:
        True if cable state is valid (no NaN), False otherwise.
    """
    cable_pos = cable.data.root_pos_w[0]
    cable_quat = cable.data.root_quat_w[0]
    has_nan = torch.any(torch.isnan(cable_pos)) or torch.any(torch.isnan(cable_quat))
    return not has_nan.item()


def reset_cable_to_initial(max_retries: int = 5) -> bool:
    """Reset cable to initial position with comprehensive state restoration.

    2026-01-06修正: 全セグメントのbody_state_wを復元 + 位置検証追加

    Args:
        max_retries: Maximum number of retry attempts.

    Returns:
        True if reset successful (no NaN and position verified), False otherwise.
    """
    # 期待する初期Z位置（initial_cable_body_stateから取得）
    expected_min_z = initial_cable_body_state[:, :, 2].min().item()
    expected_max_z = initial_cable_body_state[:, :, 2].max().item()
    print(f"  [Reset] Expected Z range: {expected_min_z:.3f} - {expected_max_z:.3f}")

    for attempt in range(max_retries):
        # 2026-01-07: More aggressive reset to clear accumulated PhysX state
        # First reset the simulation context (soft=False for complete reset)
        sim.reset(soft=True)  # Use soft reset to avoid full reinit
        scene.reset()  # Reset all scene entities
        sim.step()

        # 2026-01-06: 全セグメントの状態を復元（速度はゼロ化）
        # initial_cable_body_state: [1, num_bodies, 13]
        # 13 = pos(3) + quat(4) + lin_vel(3) + ang_vel(3)
        reset_body_state = initial_cable_body_state.clone()
        reset_body_state[:, :, 7:13] = 0.0  # 線速度・角速度をゼロ化

        # RigidObjectの全ボディ状態を書き込み
        # Articulation/RigidObjectのAPIに応じて適切なメソッドを使用
        has_body_write = hasattr(cable, 'write_body_state_to_sim')
        if has_body_write:
            cable.write_body_state_to_sim(reset_body_state)
            print(f"  [Reset] Using write_body_state_to_sim (attempt {attempt+1})")
        else:
            # フォールバック: ルート状態のみ書き込み + 関節状態
            # 2026-01-07: Use correct root body index (not always seg_0!)
            root_state = reset_body_state[:, cable_root_body_idx, :]
            cable.write_root_state_to_sim(root_state)
            print(f"  [Reset] Using write_root_state_to_sim for seg_{cable_root_body_idx} (attempt {attempt+1})")

        # 関節状態も復元（速度ゼロ）
        zero_joint_vel = torch.zeros_like(initial_cable_joint_vel)
        cable.write_joint_state_to_sim(initial_cable_joint_pos, zero_joint_vel)

        # 2026-01-07: Code B recommendation - Clear articulation drive targets
        # This helps clear PhysX TGS solver warm-start state
        try:
            cable.set_joint_position_target(initial_cable_joint_pos)
            cable.set_joint_velocity_target(zero_joint_vel)
            print(f"  [Reset] Articulation drive targets cleared")
        except (AttributeError, TypeError) as e:
            print(f"  [Reset] Note: Drive target methods not available ({type(e).__name__})")

        cable.reset()
        cable.write_data_to_sim()

        # 最小限のステップで状態を適用（重力の影響を最小化）
        for _ in range(3):
            sim.step()
            scene.update(sim.get_physics_dt())

        # Restore robot states with more aggressive reset
        # 2026-01-07: Multiple write cycles to ensure precise joint positions
        for reset_iter in range(3):
            robot_left.write_root_state_to_sim(initial_robot_left_state)
            robot_right.write_root_state_to_sim(initial_robot_right_state)
            robot_left.write_joint_state_to_sim(initial_joint_pos_left, initial_joint_vel_left)
            robot_right.write_joint_state_to_sim(initial_joint_pos_right, initial_joint_vel_right)
            # Also set joint position targets to prevent drift
            robot_left.set_joint_position_target(initial_joint_pos_left)
            robot_right.set_joint_position_target(initial_joint_pos_right)
            robot_left.reset()
            robot_right.reset()
            robot_left.write_data_to_sim()
            robot_right.write_data_to_sim()
            sim.step()
            scene.update(sim.get_physics_dt())

        # 2026-01-07: Verify robot joint positions after reset
        actual_left_joints = robot_left.data.joint_pos[0, :7].cpu().numpy()
        actual_right_joints = robot_right.data.joint_pos[0, :7].cpu().numpy()
        expected_left_joints = initial_joint_pos_left[0, :7].cpu().numpy()
        expected_right_joints = initial_joint_pos_right[0, :7].cpu().numpy()
        left_diff = np.abs(actual_left_joints - expected_left_joints).max()
        right_diff = np.abs(actual_right_joints - expected_right_joints).max()
        print(f"  [Reset] Robot joint diff: L={left_diff:.4f}rad, R={right_diff:.4f}rad")

        # 最小限の安定化ステップ
        for _ in range(10):
            sim.step()
            scene.update(sim.get_physics_dt())

        # 位置検証: ケーブルZ位置とY位置（端点）が期待値に近いか確認
        current_z = cable.data.body_state_w[:, :, 2]
        current_min_z = current_z.min().item()
        current_max_z = current_z.max().item()
        z_tolerance = 0.05  # 5cm tolerance

        z_ok = (abs(current_min_z - expected_min_z) < z_tolerance and
                abs(current_max_z - expected_max_z) < z_tolerance)
        nan_ok = check_cable_nan()

        # 2026-01-07: Y位置検証追加（端点が正しい位置にあるか）
        # IMPORTANT: Use left_end_idx and right_end_idx, NOT hardcoded 0 and 19!
        # body_state_w indices don't match segment numbers (body_names order is NOT numerical)
        current_body_state = cable.data.body_state_w
        left_y = current_body_state[0, left_end_idx, 1].item()  # Actual left end
        right_y = current_body_state[0, right_end_idx, 1].item()  # Actual right end
        expected_left_y = initial_cable_body_state[0, left_end_idx, 1].item()
        expected_right_y = initial_cable_body_state[0, right_end_idx, 1].item()
        y_tolerance = 0.05  # 5cm tolerance
        y_ok = (abs(left_y - expected_left_y) < y_tolerance and
                abs(right_y - expected_right_y) < y_tolerance)

        print(f"  [Reset] Attempt {attempt+1}: Z={current_min_z:.3f}-{current_max_z:.3f} "
              f"(expected {expected_min_z:.3f}-{expected_max_z:.3f}), "
              f"Z_OK={z_ok}, NaN_OK={nan_ok}")
        print(f"  [Reset] Y endpoints: left={left_y:.3f} (exp {expected_left_y:.3f}), "
              f"right={right_y:.3f} (exp {expected_right_y:.3f}), Y_OK={y_ok}")

        if nan_ok and z_ok and y_ok:
            print(f"  [Reset] Success after {attempt+1} attempt(s)")
            # 2026-01-07: Extended post-reset stabilization to clear accumulated physics state
            # Increased from 50 to 200 steps per Code B recommendation (iteration v7)
            print(f"  [Reset] Post-reset stabilization (200 steps)...")
            for _ in range(200):
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())
            # Verify cable is still valid
            if not check_cable_nan():
                print(f"  [ERROR] Cable NaN after post-reset stabilization!")
                continue  # Try another reset attempt
            # Check velocity
            cable_vel = cable.data.body_state_w[:, :, 7:10]
            max_vel = cable_vel.abs().max().item()
            print(f"  [Reset] Post-stabilization velocity: {max_vel:.6f} m/s")
            return True
        elif not nan_ok:
            print(f"  [WARNING] Cable NaN detected after reset")
        elif not z_ok:
            print(f"  [WARNING] Cable Z position mismatch (Z diff: "
                  f"min={abs(current_min_z - expected_min_z):.3f}m, "
                  f"max={abs(current_max_z - expected_max_z):.3f}m)")
        elif not y_ok:
            print(f"  [WARNING] Cable Y position mismatch! "
                  f"left: {left_y:.3f} (exp {expected_left_y:.3f}, diff {abs(left_y - expected_left_y):.3f}m), "
                  f"right: {right_y:.3f} (exp {expected_right_y:.3f}, diff {abs(right_y - expected_right_y):.3f}m)")

    print(f"  [ERROR] Reset failed after {max_retries} attempts")
    return False


def get_contact_force() -> tuple:
    """Get contact force from both grippers.

    Returns:
        (left_force, right_force) in Newtons.
    """
    contact_left = scene["contact_left"]
    contact_right = scene["contact_right"]
    contact_left.update(sim.get_physics_dt())
    contact_right.update(sim.get_physics_dt())

    left_force = contact_left.data.net_forces_w[0].norm().item()
    right_force = contact_right.data.net_forces_w[0].norm().item()
    return left_force, right_force


def run_cycle(cycle_idx: int):
    """Run one complete cycle and collect demonstration data."""
    global cable  # Required because cable is reassigned inside this function

    print(f"\n{'='*70}")
    print(f"CYCLE {cycle_idx + 1}/{args.num_cycles}")
    print("=" * 70)

    # Reset collector state for new cycle
    collector.prev_joint_pos_left = None
    collector.prev_joint_pos_right = None

    # 2026-01-07: Reset Diff IK controllers at cycle start
    # This clears any accumulated state from previous cycles
    diff_ik_left.reset()
    diff_ik_right.reset()
    print("  [Cycle Reset] Diff IK controllers reset")

    # ============================================================
    # PRE-CYCLE: CABLE STATE VERIFICATION
    # ============================================================
    if not check_cable_nan():
        print("  [WARNING] Cable NaN detected at cycle start, attempting reset...")
        if not reset_cable_to_initial():
            print("  [ERROR] Failed to recover cable state, skipping cycle")
            return False

    # Record initial cable Z for lift measurement
    initial_cable_z = cable.data.root_pos_w[0, 2].item()
    print(f"  [OK] Cable Z at start: {initial_cable_z:.4f}m")

    # 2026-01-07: Detailed cable state logging for Cycle 2 NaN debugging
    cable_pos = cable.data.body_state_w[:, :, :3]
    cable_vel = cable.data.body_state_w[:, :, 7:10]
    max_vel = cable_vel.abs().max().item()
    print(f"  [Cycle {cycle_idx+1}] Cable state after reset:")
    print(f"    Position X: {cable_pos[:,:,0].min().item():.3f}~{cable_pos[:,:,0].max().item():.3f}")
    print(f"    Position Y: {cable_pos[:,:,1].min().item():.3f}~{cable_pos[:,:,1].max().item():.3f}")
    print(f"    Position Z: {cable_pos[:,:,2].min().item():.3f}~{cable_pos[:,:,2].max().item():.3f}")
    print(f"    Max velocity: {max_vel:.6f} m/s")
    if max_vel > 0.01:
        print(f"    [WARNING] Non-zero velocity after reset! (threshold: 0.01 m/s)")
        # Additional stabilization
        print(f"    [Stabilization] Running 100 extra steps...")
        for _ in range(100):
            scene.write_data_to_sim()
            sim.step()
            scene.update(sim.get_physics_dt())
        if not check_cable_nan():
            print(f"    [ERROR] Cable NaN after stabilization!")
            return False
        # Re-check velocity
        cable_vel = cable.data.body_state_w[:, :, 7:10]
        max_vel = cable_vel.abs().max().item()
        print(f"    Max velocity after stabilization: {max_vel:.6f} m/s")

    # ============================================================
    # PHASE 1: APPROACH
    # ============================================================
    # 2026-01-07: Cable endpoint logging per Code B (grasp failure diagnosis)
    # IMPORTANT: Use left_end_idx and right_end_idx, NOT hardcoded 0 and 19!
    cable_pos = cable.data.body_state_w[:, :, :3]
    left_end_pos = cable_pos[0, left_end_idx, :]   # Actual left end
    right_end_pos = cable_pos[0, right_end_idx, :]  # Actual right end
    print(f"[Cycle {cycle_idx+1}] Cable endpoints before Phase 1:")
    print(f"  {cable.body_names[left_end_idx]} (left):  X={left_end_pos[0].item():.4f}, Y={left_end_pos[1].item():.4f}, Z={left_end_pos[2].item():.4f}")
    print(f"  {cable.body_names[right_end_idx]} (right): X={right_end_pos[0].item():.4f}, Y={right_end_pos[1].item():.4f}, Z={right_end_pos[2].item():.4f}")
    print(f"  Expected Y: left={initial_cable_body_state[0, left_end_idx, 1].item():.3f}, right={initial_cable_body_state[0, right_end_idx, 1].item():.3f}")

    print("\n[Phase 1] Approach...")
    teleport_robot(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    teleport_robot(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)

    for i in range(PHASE1_STEPS):
        set_robot_joints(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(1, GRIPPER_OPEN, GRIPPER_OPEN)

    p1_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p1_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p1_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p1_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # 2026-01-07: Gripper-Cable distance check per Code B (grasp failure diagnosis)
    # Use dynamic indices: left arm grasps left end, right arm grasps right end
    cable_pos = cable.data.body_state_w[:, :, :3]
    left_cable_target = cable_pos[0, left_end_idx, :]   # Left arm grasps left end
    right_cable_target = cable_pos[0, right_end_idx, :]  # Right arm grasps right end
    left_dist = torch.norm(p1_pos_l[0] - left_cable_target).item()
    right_dist = torch.norm(p1_pos_r[0] - right_cable_target).item()
    print(f"[Phase 1] Gripper-Cable distance:")
    print(f"  Left:  {left_dist*100:.1f}cm (gripper->{cable.body_names[left_end_idx]})")
    print(f"  Right: {right_dist*100:.1f}cm (gripper->{cable.body_names[right_end_idx]})")
    if left_dist > 0.02 or right_dist > 0.02:
        print(f"  [WARNING] Large distance detected! May cause grasp failure")

    # ============================================================
    # PHASE 2: GRASP (Joint interpolation - same as test_multi_cycle.py)
    # ============================================================
    print("\n[Phase 2] Grasp...")

    # Phase 2 approach: Joint interpolation from INIT to PHASE2 joints
    # (This method works in test_multi_cycle.py with 27N contact force)
    for step in range(PHASE12_STEPS):
        alpha = (step + 1) / PHASE12_STEPS
        left_joints = [l + alpha * (p - l) for l, p in zip(LEFT_ARM_INIT_JOINTS, PHASE2_LEFT_JOINTS)]
        right_joints = [l + alpha * (p - l) for l, p in zip(RIGHT_ARM_INIT_JOINTS, PHASE2_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, GRIPPER_OPEN, GRIPPER_OPEN)

    # Grasp: Close grippers with contact force feedback control
    # 2026-01-07 v2: Lowered target force for more stable grasp
    # Previous: 25N target led to 30-37N after stabilization → NaN at 18.5%
    TARGET_CONTACT_FORCE = 20.0  # N - lower target for safety margin
    MAX_CONTACT_FORCE = 30.0     # N - relax grip if exceeded (lowered from 35)
    MAX_GRASP_STEPS = 200        # Double the steps for safer closing

    print(f"  [Grasp] Closing grippers: {GRIPPER_OPEN} -> {GRIPPER_CLOSE} over {MAX_GRASP_STEPS} steps (max)")
    print(f"  [Grasp] Target force: {TARGET_CONTACT_FORCE}N, Max: {MAX_CONTACT_FORCE}N")

    grip_val_left = GRIPPER_OPEN
    grip_val_right = GRIPPER_OPEN
    grip_step = (GRIPPER_OPEN - GRIPPER_CLOSE) / MAX_GRASP_STEPS  # Slower closing
    grasp_complete = False

    for i in range(MAX_GRASP_STEPS):
        # Get current contact forces
        left_force, right_force = get_contact_force()

        # Check if target force reached on both grippers
        if left_force >= TARGET_CONTACT_FORCE and right_force >= TARGET_CONTACT_FORCE:
            print(f"    [Step {i+1}] Target force reached: L={left_force:.1f}N, R={right_force:.1f}N")
            grasp_complete = True
            break

        # Handle excessive force - relax grip slightly
        if right_force > MAX_CONTACT_FORCE:
            grip_val_right = min(GRIPPER_OPEN, grip_val_right + 0.001)
            print(f"    [Step {i+1}] Relaxing RIGHT grip (force={right_force:.1f}N)")
        else:
            grip_val_right = max(GRIPPER_CLOSE, grip_val_right - grip_step)

        if left_force > MAX_CONTACT_FORCE:
            grip_val_left = min(GRIPPER_OPEN, grip_val_left + 0.001)
            print(f"    [Step {i+1}] Relaxing LEFT grip (force={left_force:.1f}N)")
        else:
            grip_val_left = max(GRIPPER_CLOSE, grip_val_left - grip_step)

        # Apply gripper positions
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, grip_val_left)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, grip_val_right)
        sim.step()
        scene.update(sim.get_physics_dt())

        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, grip_val_left, grip_val_right)
        if i % 50 == 0:
            print(f"    [Step {i+1}/{MAX_GRASP_STEPS}] grip_L={grip_val_left:.4f}, grip_R={grip_val_right:.4f}, force_L={left_force:.1f}N, force_R={right_force:.1f}N")

    if not grasp_complete:
        print(f"  [Grasp] Max steps reached without target force")

    # Stabilize: Hold position with CONTINUOUS force monitoring
    # 2026-01-07 v2: Force monitoring during stabilization to prevent force buildup
    final_grip_left = grip_val_left
    final_grip_right = grip_val_right
    RELAX_STEP = 0.0005  # How much to relax grip when force is too high
    MIN_GRIP = GRIPPER_CLOSE  # Don't relax beyond minimum grip
    force_warnings = 0

    for i in range(GRASP_STABILIZE):
        # Monitor contact force during stabilization
        if i % 10 == 0:  # Check every 10 steps
            left_force, right_force = get_contact_force()

            # Relax grip if force exceeds limit
            if right_force > MAX_CONTACT_FORCE:
                final_grip_right = min(GRIPPER_OPEN, final_grip_right + RELAX_STEP)
                if force_warnings < 5:  # Limit log spam
                    print(f"    [Stabilize {i}] Relaxing RIGHT: force={right_force:.1f}N, grip→{final_grip_right:.4f}")
                force_warnings += 1

            if left_force > MAX_CONTACT_FORCE:
                final_grip_left = min(GRIPPER_OPEN, final_grip_left + RELAX_STEP)
                if force_warnings < 5:
                    print(f"    [Stabilize {i}] Relaxing LEFT: force={left_force:.1f}N, grip→{final_grip_left:.4f}")
                force_warnings += 1

        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, final_grip_left)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, final_grip_right)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, final_grip_left, final_grip_right)

    if force_warnings > 0:
        print(f"    [Stabilize] Total force warnings: {force_warnings}")

    # ============================================================
    # PHASE 2 VERIFICATION: Contact Force
    # ============================================================
    left_force, right_force = get_contact_force()
    print(f"  [Verify] Contact force: L={left_force:.1f}N, R={right_force:.1f}N")
    # 2026-01-07: Critical grasp verification per Code B
    if left_force < 10 or right_force < 10:
        print(f"  [ERROR] Grasp failed! L={left_force:.1f}N, R={right_force:.1f}N")
        print(f"  [ERROR] Aborting cycle - contact force below 10N threshold")
        print(f"         Expected: 10-25N for stable grasp")
        return False  # Abort this cycle
    elif left_force > 25 or right_force > 25:
        print(f"  [WARNING] High contact force detected (recommended: 10-25N)")
        print(f"           High force may cause instability in later phases")

    # Check cable NaN after grasp
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after grasp phase!")

    p2_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p2_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p2_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p2_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # ============================================================
    # PHASE 2→3 TRANSITION DIAGNOSTICS
    # ============================================================
    print("\n" + "="*70)
    print("[Phase 2→3 Transition] Detailed cable state before lift:")
    cable_pos = cable.data.body_pos_w[0].cpu().numpy()  # [20, 3]
    cable_vel = cable.data.body_lin_vel_w[0].cpu().numpy()  # [20, 3]
    speeds = np.linalg.norm(cable_vel, axis=1)
    for seg_idx in [16, 17, 18, 19]:  # Grasp point segments
        print(f"  seg_{seg_idx}: pos=({cable_pos[seg_idx, 0]:.4f}, {cable_pos[seg_idx, 1]:.4f}, {cable_pos[seg_idx, 2]:.4f}), "
              f"vel=({cable_vel[seg_idx, 0]:.4f}, {cable_vel[seg_idx, 1]:.4f}, {cable_vel[seg_idx, 2]:.4f}), speed={speeds[seg_idx]:.4f} m/s")
    print(f"  Max segment speed: {speeds.max():.4f} m/s (seg_{np.argmax(speeds)})")
    print(f"  Contact force: L={left_force:.1f}N, R={right_force:.1f}N")
    print("="*70)

    # ============================================================
    # PHASE 3: LIFT
    # ============================================================
    print(f"\n[Phase 3] Lift ({LIFT_CM}cm)...")
    p3_target_l = p2_pos_l.clone()
    p3_target_l[0, 2] += LIFT_CM / 100.0
    p3_target_r = p2_pos_r.clone()
    p3_target_r[0, 2] += LIFT_CM / 100.0

    p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r = run_diff_ik_motion_with_collection(
        p2_pos_l, p2_pos_r, p2_quat_l, p2_quat_r,
        p3_target_l, p3_target_r, LIFT_STEPS, GRIPPER_CLOSE, phase=3
    )

    # ============================================================
    # PHASE 3 VERIFICATION: Lift Distance and Force
    # ============================================================
    left_force_lift, right_force_lift = get_contact_force()
    print(f"  [Force] After lift: L={left_force_lift:.1f}N, R={right_force_lift:.1f}N")

    # Measure cable lift using grasped segments (endpoints)
    # cable.data.body_pos_w shape: [num_envs, num_bodies, 3]
    # Use dynamic indices from initialization
    left_end_z = cable.data.body_pos_w[0, left_end_idx, 2].item()
    right_end_z = cable.data.body_pos_w[0, right_end_idx, 2].item()
    grasped_z = (left_end_z + right_end_z) / 2
    lift_distance = grasped_z - initial_cable_z
    print(f"  [Verify] Lift distance: {lift_distance*100:.1f}cm (target: {LIFT_CM}cm)")
    print(f"  [Debug] {cable.body_names[left_end_idx]} Z: {left_end_z:.4f}m, {cable.body_names[right_end_idx]} Z: {right_end_z:.4f}m")

    # Debug: EE position after lift
    ee_z_l = robot_left.data.body_pos_w[0, jacobian_body_left, 2].item()
    ee_z_r = robot_right.data.body_pos_w[0, jacobian_body_right, 2].item()
    print(f"  [Debug] EE Z: L={ee_z_l:.4f}m, R={ee_z_r:.4f}m")

    if lift_distance < 0.03:
        print(f"  [WARNING] Lift too low - possible grasp failure")

    # Check cable NaN after lift
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after lift phase!")

    # ============================================================
    # PHASE 4: 回転前に高くリフト
    # 2026-01-06: 回転中の中間距離縮小（51cm→39cm）でNaN発生
    # 解決策: より高くリフトしてケーブルに余裕を持たせる
    # ============================================================
    print("\n[Phase 4] Pre-rotation lift using Diff IK...")
    # 2026-01-07: PRE_ROTATION_Z=1.05m（オリジナル値）
    # ケーブルたるみ約10cm考慮: ケーブル最低点Z≈0.95 > フック上端Z=0.90
    # マージン: 約5cm（0.95-0.90）
    # Note: 1.10/1.15mは右アームのIK到達限界（Z≈1.035m）を超えて追従不能
    PRE_ROTATION_Z = 1.05

    # Get current EE positions after Phase 3 lift
    p3_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p3_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p3_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p3_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
    print(f"  Start EE: L=({p3_pos_l[0,0]:.3f}, {p3_pos_l[0,1]:.3f}, {p3_pos_l[0,2]:.3f})")
    print(f"           R=({p3_pos_r[0,0]:.3f}, {p3_pos_r[0,1]:.3f}, {p3_pos_r[0,2]:.3f})")

    # Lift target: same XY, higher Z
    p4_lift_l = torch.tensor([[p3_pos_l[0,0].item(), p3_pos_l[0,1].item(), PRE_ROTATION_Z]], device=device)
    p4_lift_r = torch.tensor([[p3_pos_r[0,0].item(), p3_pos_r[0,1].item(), PRE_ROTATION_Z]], device=device)
    print(f"  Lift target Z: {PRE_ROTATION_Z}m")

    # Lift higher (now to Z=1.25m, ~30cm from Z=0.96)
    PHASE4_LIFT_STEPS = 600  # More steps for larger lift distance
    p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r = run_diff_ik_motion_with_collection(
        p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r,
        p4_lift_l, p4_lift_r, PHASE4_LIFT_STEPS, GRIPPER_CLOSE, phase=4
    )

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after pre-rotation lift!")

    # Log Phase 4 end contact force
    p4_end_force_l, p4_end_force_r = get_contact_force()
    p4_end_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P4 End] Contact: L={p4_end_force_l:.1f}N, R={p4_end_force_r:.1f}N, cable_Z: {p4_end_cable_z.min():.3f}-{p4_end_cable_z.max():.3f}")

    # ============================================================
    # PHASE 4.5: 90度回転（3段階遷移）- X/Y移動分離でNaN回避
    # 2026-01-07 v19: X移動とY移動を分離して、IK解空間の連続性を維持
    # Stage 1b: X移動のみ（Y固定）
    # Stage 1c: Y移動のみ（X固定）
    # Stage 2: 最終位置へ
    # ============================================================
    print("\n[Phase 4.5] 90-degree rotation (3-stage X/Y split) using Diff IK...")
    print("  2026-01-07 v19: X移動とY移動を分離してNaN回避")

    # Get current EE positions after Phase 4 lift
    p4_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p4_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p4_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p4_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
    print(f"  Start EE: L=({p4_pos_l[0,0]:.3f}, {p4_pos_l[0,1]:.3f}, {p4_pos_l[0,2]:.3f})")
    print(f"           R=({p4_pos_r[0,0]:.3f}, {p4_pos_r[0,1]:.3f}, {p4_pos_r[0,2]:.3f})")

    # Stage 1b: X移動のみ（現在のY座標を維持）
    print("  --- Stage 1b: X movement only (Y fixed) ---")
    # Use current Y position, target X from WAYPOINT_PHASE45B
    p45b_target_l = torch.tensor([[WAYPOINT_PHASE45B_LEFT[0], p4_pos_l[0,1].item(), PRE_ROTATION_Z]], device=device)
    p45b_target_r = torch.tensor([[WAYPOINT_PHASE45B_RIGHT[0], p4_pos_r[0,1].item(), PRE_ROTATION_Z]], device=device)
    print(f"  Stage 1b Target: L=({p45b_target_l[0,0]:.3f}, {p45b_target_l[0,1]:.3f}, {p45b_target_l[0,2]:.3f})")
    print(f"                   R=({p45b_target_r[0,0]:.3f}, {p45b_target_r[0,1]:.3f}, {p45b_target_r[0,2]:.3f})")

    PHASE45B_X_STEPS = 500
    p45b_pos_l, p45b_pos_r, p45b_quat_l, p45b_quat_r = run_diff_ik_motion_with_collection(
        p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r,
        p45b_target_l, p45b_target_r, PHASE45B_X_STEPS, GRIPPER_CLOSE, phase=4
    )

    # Check cable NaN after Stage 1b
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 1b (X movement)!")

    # Log Stage 1b completion with contact force
    s1b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s1b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    s1b_force_l, s1b_force_r = get_contact_force()
    cable = scene["cable"]
    s1b_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  Stage 1b Complete: L=({s1b_ee_l[0,0]:.3f}, {s1b_ee_l[0,1]:.3f}, {s1b_ee_l[0,2]:.3f})")
    print(f"                     R=({s1b_ee_r[0,0]:.3f}, {s1b_ee_r[0,1]:.3f}, {s1b_ee_r[0,2]:.3f})")
    print(f"  [P4.5 Stage1b] Contact: L={s1b_force_l:.1f}N, R={s1b_force_r:.1f}N, cable_Z: {s1b_cable_z.min():.3f}-{s1b_cable_z.max():.3f}")

    # Stage 1c: Y移動のみ（X固定）
    print("  --- Stage 1c: Y movement only (X fixed) ---")
    p45c_target_l = torch.tensor([[WAYPOINT_PHASE45C_LEFT[0], WAYPOINT_PHASE45C_LEFT[1], PRE_ROTATION_Z]], device=device)
    p45c_target_r = torch.tensor([[WAYPOINT_PHASE45C_RIGHT[0], WAYPOINT_PHASE45C_RIGHT[1], PRE_ROTATION_Z]], device=device)
    print(f"  Stage 1c Target: L=({p45c_target_l[0,0]:.3f}, {p45c_target_l[0,1]:.3f}, {p45c_target_l[0,2]:.3f})")
    print(f"                   R=({p45c_target_r[0,0]:.3f}, {p45c_target_r[0,1]:.3f}, {p45c_target_r[0,2]:.3f})")

    PHASE45C_Y_STEPS = 500
    p45c_pos_l, p45c_pos_r, p45c_quat_l, p45c_quat_r = run_diff_ik_motion_with_collection(
        p45b_pos_l, p45b_pos_r, p45b_quat_l, p45b_quat_r,
        p45c_target_l, p45c_target_r, PHASE45C_Y_STEPS, GRIPPER_CLOSE, phase=4
    )

    # Check cable NaN after Stage 1c
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 1c (Y movement)!")

    # Log Stage 1c completion with contact force
    s1c_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s1c_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    s1c_force_l, s1c_force_r = get_contact_force()
    s1c_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  Stage 1c Complete: L=({s1c_ee_l[0,0]:.3f}, {s1c_ee_l[0,1]:.3f}, {s1c_ee_l[0,2]:.3f})")
    print(f"                     R=({s1c_ee_r[0,0]:.3f}, {s1c_ee_r[0,1]:.3f}, {s1c_ee_r[0,2]:.3f})")
    print(f"  [P4.5 Stage1c] Contact: L={s1c_force_l:.1f}N, R={s1c_force_r:.1f}N, cable_Z: {s1c_cable_z.min():.3f}-{s1c_cable_z.max():.3f}")

    # ================================================================
    # Stage 2: v32 - Z段階的下降アプローチ
    # Stage 2a: Z=1.05のままX移動（前半）
    # Stage 2b: Z下降（1.05→1.00）しながらX移動（後半）
    # ================================================================

    # ============================================
    # v49: Stage 2a - 4段階細分化（各50mm以下）
    # ============================================
    print("  --- Stage 2a: 4-step subdivision (v49) ---")
    STAGE2A_STEPS = 300  # 各ステージ300ステップ

    # Stage 2a-1: (0.40, -0.15) → (0.445, -0.17)
    print("  Stage 2a-1: Target (0.445, -0.17, 1.05)")
    p2a1_target_l = torch.tensor([[0.445, -0.17, PRE_ROTATION_Z]], device=device)
    p2a1_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p2a1_pos_l, p2a1_pos_r, p2a1_quat_l, p2a1_quat_r = run_diff_ik_motion_with_collection(
        p45c_pos_l, p45c_pos_r, p45c_quat_l, p45c_quat_r,
        p2a1_target_l, p2a1_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4
    )
    s2a1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a1_force_l, s2a1_force_r = get_contact_force()
    s2a1_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P4.5 Stage2a-1] L=({s2a1_ee_l[0,0]:.3f}, {s2a1_ee_l[0,1]:.3f}, {s2a1_ee_l[0,2]:.3f}), Force: L={s2a1_force_l:.1f}N R={s2a1_force_r:.1f}N, cable_Z: {s2a1_cable_z.min():.3f}-{s2a1_cable_z.max():.3f}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-1!")

    # Stage 2a-2: (0.445, -0.17) → (0.49, -0.19)
    print("  Stage 2a-2: Target (0.49, -0.19, 1.05)")
    p2a2_target_l = torch.tensor([[0.49, -0.19, PRE_ROTATION_Z]], device=device)
    p2a2_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p2a2_pos_l, p2a2_pos_r, p2a2_quat_l, p2a2_quat_r = run_diff_ik_motion_with_collection(
        p2a1_pos_l, p2a1_pos_r, p2a1_quat_l, p2a1_quat_r,
        p2a2_target_l, p2a2_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4
    )
    s2a2_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a2_force_l, s2a2_force_r = get_contact_force()
    s2a2_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P4.5 Stage2a-2] L=({s2a2_ee_l[0,0]:.3f}, {s2a2_ee_l[0,1]:.3f}, {s2a2_ee_l[0,2]:.3f}), Force: L={s2a2_force_l:.1f}N R={s2a2_force_r:.1f}N, cable_Z: {s2a2_cable_z.min():.3f}-{s2a2_cable_z.max():.3f}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-2!")

    # Stage 2a-3: (0.49, -0.19) → (0.535, -0.215)
    print("  Stage 2a-3: Target (0.535, -0.215, 1.05)")
    p2a3_target_l = torch.tensor([[0.535, -0.215, PRE_ROTATION_Z]], device=device)
    p2a3_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p2a3_pos_l, p2a3_pos_r, p2a3_quat_l, p2a3_quat_r = run_diff_ik_motion_with_collection(
        p2a2_pos_l, p2a2_pos_r, p2a2_quat_l, p2a2_quat_r,
        p2a3_target_l, p2a3_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4
    )
    s2a3_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a3_force_l, s2a3_force_r = get_contact_force()
    s2a3_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P4.5 Stage2a-3] L=({s2a3_ee_l[0,0]:.3f}, {s2a3_ee_l[0,1]:.3f}, {s2a3_ee_l[0,2]:.3f}), Force: L={s2a3_force_l:.1f}N R={s2a3_force_r:.1f}N, cable_Z: {s2a3_cable_z.min():.3f}-{s2a3_cable_z.max():.3f}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-3!")

    # Stage 2a-4: (0.535, -0.215) → (0.575, -0.24) [オリジナル中間点]
    print("  Stage 2a-4: Target (0.575, -0.24, 1.05)")
    MID_X_LEFT = 0.575
    p2a4_target_l = torch.tensor([[MID_X_LEFT, WAYPOINT_PHASE45_LEFT[1], PRE_ROTATION_Z]], device=device)
    p2a4_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p45_mid_pos_l, p45_mid_pos_r, p45_mid_quat_l, p45_mid_quat_r = run_diff_ik_motion_with_collection(
        p2a3_pos_l, p2a3_pos_r, p2a3_quat_l, p2a3_quat_r,
        p2a4_target_l, p2a4_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4
    )
    s2a4_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a4_force_l, s2a4_force_r = get_contact_force()
    s2a4_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    target_diff_x = MID_X_LEFT - s2a4_ee_l[0,0].item()
    target_diff_y = WAYPOINT_PHASE45_LEFT[1] - s2a4_ee_l[0,1].item()
    target_diff_z = PRE_ROTATION_Z - s2a4_ee_l[0,2].item()
    print(f"  [P4.5 Stage2a-4] L=({s2a4_ee_l[0,0]:.3f}, {s2a4_ee_l[0,1]:.3f}, {s2a4_ee_l[0,2]:.3f}), Force: L={s2a4_force_l:.1f}N R={s2a4_force_r:.1f}N, cable_Z: {s2a4_cable_z.min():.3f}-{s2a4_cable_z.max():.3f}")
    print(f"  Stage2a Final Diff: dX={target_diff_x*1000:.1f}mm, dY={target_diff_y*1000:.1f}mm, dZ={target_diff_z*1000:.1f}mm")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-4!")

    # ============================================
    # v49: Stage 2b - 2段階細分化
    # ============================================
    print("  --- Stage 2b: 2-step subdivision (v49) ---")
    STAGE2B_STEPS = 400
    FINAL_Z = PRE_ROTATION_Z  # v46: Z下降削除、1.05を維持

    # Stage 2b-1: (0.575, -0.24) → (0.64, -0.24)
    print("  Stage 2b-1: Target (0.64, -0.24, 1.05)")
    p2b1_target_l = torch.tensor([[0.64, WAYPOINT_PHASE45_LEFT[1], FINAL_Z]], device=device)
    p2b1_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1], FINAL_Z]], device=device)
    p2b1_pos_l, p2b1_pos_r, p2b1_quat_l, p2b1_quat_r = run_diff_ik_motion_with_collection(
        p45_mid_pos_l, p45_mid_pos_r, p45_mid_quat_l, p45_mid_quat_r,
        p2b1_target_l, p2b1_target_r, STAGE2B_STEPS, GRIPPER_CLOSE, phase=4
    )
    s2b1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2b1_force_l, s2b1_force_r = get_contact_force()
    s2b1_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P4.5 Stage2b-1] L=({s2b1_ee_l[0,0]:.3f}, {s2b1_ee_l[0,1]:.3f}, {s2b1_ee_l[0,2]:.3f}), Force: L={s2b1_force_l:.1f}N R={s2b1_force_r:.1f}N, cable_Z: {s2b1_cable_z.min():.3f}-{s2b1_cable_z.max():.3f}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2b-1!")

    # Stage 2b-2: (0.64, -0.24) → (0.70, -0.24) [最終位置]
    print("  Stage 2b-2: Target (0.70, -0.24, 1.05)")
    p45_target_l = torch.tensor([[WAYPOINT_PHASE45_LEFT[0], WAYPOINT_PHASE45_LEFT[1], FINAL_Z]], device=device)
    p45_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1], FINAL_Z]], device=device)
    p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r = run_diff_ik_motion_with_collection(
        p2b1_pos_l, p2b1_pos_r, p2b1_quat_l, p2b1_quat_r,
        p45_target_l, p45_target_r, STAGE2B_STEPS, GRIPPER_CLOSE, phase=4
    )

    # Log final EE positions with contact force
    final_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    final_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    s2b_force_l, s2b_force_r = get_contact_force()
    s2b_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P4.5 Stage2b-2] L=({final_ee_l[0,0]:.3f}, {final_ee_l[0,1]:.3f}, {final_ee_l[0,2]:.3f}), Force: L={s2b_force_l:.1f}N R={s2b_force_r:.1f}N, cable_Z: {s2b_cable_z.min():.3f}-{s2b_cable_z.max():.3f}")
    print(f"  Stage 2b Complete: L=({final_ee_l[0,0]:.3f}, {final_ee_l[0,1]:.3f}, {final_ee_l[0,2]:.3f})")
    print(f"                     R=({final_ee_r[0,0]:.3f}, {final_ee_r[0,1]:.3f}, {final_ee_r[0,2]:.3f})")

    # Check cable NaN
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2b!")

    # ============================================================
    # PHASE 5: v34 - 2段階Z上昇（張力分散）
    # ============================================================
    print("\n[Phase 5] Above hook using Diff IK (2-stage v34)...")
    print(f"  ケーブル最低点Z = 0.997 - 0.077(たるみ) = 0.92m > フック上端0.90m")

    # Get current EE positions after rotation
    p45_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p45_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p45_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p45_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Log Phase 5 start contact force
    p5_start_force_l, p5_start_force_r = get_contact_force()
    p5_start_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    print(f"  [P5 Start] Contact: L={p5_start_force_l:.1f}N, R={p5_start_force_r:.1f}N, cable_Z: {p5_start_cable_z.min():.3f}-{p5_start_cable_z.max():.3f}")

    # Phase 5a: First Z rise (current → 1.04)
    print("  --- Phase 5a: First Z rise (→ 1.04) ---")
    PHASE5A_Z = 1.04
    p5a_target_l = torch.tensor([[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], PHASE5A_Z]], device=device)
    p5a_target_r = torch.tensor([[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], PHASE5A_Z]], device=device)
    print(f"  Target: L=({p5a_target_l[0,0]:.3f}, {p5a_target_l[0,1]:.3f}, {p5a_target_l[0,2]:.3f})")
    print(f"          R=({p5a_target_r[0,0]:.3f}, {p5a_target_r[0,1]:.3f}, {p5a_target_r[0,2]:.3f})")

    PHASE5A_STEPS = 150
    p5a_pos_l, p5a_pos_r, p5a_quat_l, p5a_quat_r = run_diff_ik_motion_with_collection(
        p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r,
        p5a_target_l, p5a_target_r, PHASE5A_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5a completion
    s5a_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s5a_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5a Complete: L=({s5a_ee_l[0,0]:.3f}, {s5a_ee_l[0,1]:.3f}, {s5a_ee_l[0,2]:.3f})")
    print(f"                     R=({s5a_ee_r[0,0]:.3f}, {s5a_ee_r[0,1]:.3f}, {s5a_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5a
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5a!")

    # Stabilization (100 steps)
    print("  [Stabilization] 100 steps...")
    for _ in range(100):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 5b: Second Z rise (1.04 → 1.09)
    print("  --- Phase 5b: Second Z rise (1.04 → 1.09) ---")
    # Get current positions after stabilization
    p5a_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p5a_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p5a_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p5a_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    p5_target_l = torch.tensor([[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], WAYPOINT_PHASE5_LEFT[2]]], device=device)
    p5_target_r = torch.tensor([[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], WAYPOINT_PHASE5_RIGHT[2]]], device=device)
    print(f"  Target: L=({p5_target_l[0,0]:.3f}, {p5_target_l[0,1]:.3f}, {p5_target_l[0,2]:.3f})")
    print(f"          R=({p5_target_r[0,0]:.3f}, {p5_target_r[0,1]:.3f}, {p5_target_r[0,2]:.3f})")

    PHASE5B_STEPS = 150
    p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r = run_diff_ik_motion_with_collection(
        p5a_pos_l, p5a_pos_r, p5a_quat_l, p5a_quat_r,
        p5_target_l, p5_target_r, PHASE5B_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5b completion
    s5b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s5b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5b Complete: L=({s5b_ee_l[0,0]:.3f}, {s5b_ee_l[0,1]:.3f}, {s5b_ee_l[0,2]:.3f})")
    print(f"                     R=({s5b_ee_r[0,0]:.3f}, {s5b_ee_r[0,1]:.3f}, {s5b_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5b
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5b!")

    # ============================================================
    # PHASE 5.5: v35 - 2段階Z下降（張力分散）
    # ============================================================
    print("\n[Phase 5.5] Lower onto hook using Diff IK (2-stage v35)...")
    print(f"  目標: Z=1.09 → Z=1.02 (下降7cm)")

    # Get current EE positions
    p5_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p5_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p5_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p5_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Phase 5.5a: First Z descent (current → 1.05)
    print("  --- Phase 5.5a: First Z descent (→ 1.05) ---")
    PHASE55A_Z = 1.05
    p55a_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1], PHASE55A_Z]], device=device)
    p55a_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], WAYPOINT_PHASE55_RIGHT[1], PHASE55A_Z]], device=device)
    print(f"  Target: L=({p55a_target_l[0,0]:.3f}, {p55a_target_l[0,1]:.3f}, {p55a_target_l[0,2]:.3f})")
    print(f"          R=({p55a_target_r[0,0]:.3f}, {p55a_target_r[0,1]:.3f}, {p55a_target_r[0,2]:.3f})")

    PHASE55A_STEPS = 150
    p55a_pos_l, p55a_pos_r, p55a_quat_l, p55a_quat_r = run_diff_ik_motion_with_collection(
        p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r,
        p55a_target_l, p55a_target_r, PHASE55A_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5a completion
    s55a_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55a_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5a Complete: L=({s55a_ee_l[0,0]:.3f}, {s55a_ee_l[0,1]:.3f}, {s55a_ee_l[0,2]:.3f})")
    print(f"                       R=({s55a_ee_r[0,0]:.3f}, {s55a_ee_r[0,1]:.3f}, {s55a_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5a
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5a!")

    # Stabilization (100 steps)
    print("  [Stabilization] 100 steps...")
    for _ in range(100):
        sim.step()
        scene.update(sim.get_physics_dt())

    # ================================================================
    # Phase 5.5b: v37 - Z移動とY移動を分離してNaN回避
    # ================================================================

    # Phase 5.5b1a: Z movement only (Z 1.05→1.035, Y fixed)
    print("  --- Phase 5.5b1a: Z movement only (Z→1.035) ---")
    # Get current positions after stabilization
    p55a_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p55a_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p55a_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p55a_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Get current Y position for Right arm (keep Y fixed)
    current_right_y = p55a_pos_r[0, 1].item()

    # Phase 5.5b1a targets: Z movement only
    PHASE55B1A_Z = 1.035
    p55b1a_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1], PHASE55B1A_Z]], device=device)
    p55b1a_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], current_right_y, PHASE55B1A_Z]], device=device)  # Keep Y fixed
    print(f"  Target: L=({p55b1a_target_l[0,0]:.3f}, {p55b1a_target_l[0,1]:.3f}, {p55b1a_target_l[0,2]:.3f})")
    print(f"          R=({p55b1a_target_r[0,0]:.3f}, {p55b1a_target_r[0,1]:.3f}, {p55b1a_target_r[0,2]:.3f})")

    PHASE55B1A_STEPS = 50
    p55b1a_pos_l, p55b1a_pos_r, p55b1a_quat_l, p55b1a_quat_r = run_diff_ik_motion_with_collection(
        p55a_pos_l, p55a_pos_r, p55a_quat_l, p55a_quat_r,
        p55b1a_target_l, p55b1a_target_r, PHASE55B1A_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5b1a completion
    s55b1a_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55b1a_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5b1a Complete: L=({s55b1a_ee_l[0,0]:.3f}, {s55b1a_ee_l[0,1]:.3f}, {s55b1a_ee_l[0,2]:.3f})")
    print(f"                         R=({s55b1a_ee_r[0,0]:.3f}, {s55b1a_ee_r[0,1]:.3f}, {s55b1a_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5b1a
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5b1a!")

    # Stabilization (50 steps)
    print("  [Stabilization] 50 steps...")
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 5.5b1b: Y movement only (Right Y → 0.22, Z fixed)
    print("  --- Phase 5.5b1b: Y movement only (Right Y→0.22) ---")
    # Get current positions after stabilization
    p55b1a_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p55b1a_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p55b1a_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p55b1a_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Get current Z position (keep Z fixed)
    current_left_z = p55b1a_pos_l[0, 2].item()
    current_right_z = p55b1a_pos_r[0, 2].item()

    # Phase 5.5b1b targets: Y movement only
    PHASE55B1B_RIGHT_Y = 0.22  # Half way between current (~0.26) and target (0.15)
    p55b1b_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1], current_left_z]], device=device)
    p55b1b_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], PHASE55B1B_RIGHT_Y, current_right_z]], device=device)
    print(f"  Target: L=({p55b1b_target_l[0,0]:.3f}, {p55b1b_target_l[0,1]:.3f}, {p55b1b_target_l[0,2]:.3f})")
    print(f"          R=({p55b1b_target_r[0,0]:.3f}, {p55b1b_target_r[0,1]:.3f}, {p55b1b_target_r[0,2]:.3f})")

    PHASE55B1B_STEPS = 50
    p55b1b_pos_l, p55b1b_pos_r, p55b1b_quat_l, p55b1b_quat_r = run_diff_ik_motion_with_collection(
        p55b1a_pos_l, p55b1a_pos_r, p55b1a_quat_l, p55b1a_quat_r,
        p55b1b_target_l, p55b1b_target_r, PHASE55B1B_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5b1b completion
    s55b1b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55b1b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5b1b Complete: L=({s55b1b_ee_l[0,0]:.3f}, {s55b1b_ee_l[0,1]:.3f}, {s55b1b_ee_l[0,2]:.3f})")
    print(f"                         R=({s55b1b_ee_r[0,0]:.3f}, {s55b1b_ee_r[0,1]:.3f}, {s55b1b_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5b1b
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5b1b!")

    # Stabilization (20 steps) - v38: reduced from 100 to prevent tension accumulation
    print("  [Stabilization] 20 steps (v38: short stabilization)...")
    for _ in range(20):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 5.5b2: Final (Z 1.035→1.02, Right Y final)
    print("  --- Phase 5.5b2: Final (Z→1.02, Right Y final) ---")
    # Get current positions after stabilization
    p55b1_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p55b1_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p55b1_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p55b1_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    p55_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1], WAYPOINT_PHASE55_LEFT[2]]], device=device)
    p55_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], WAYPOINT_PHASE55_RIGHT[1], WAYPOINT_PHASE55_RIGHT[2]]], device=device)
    print(f"  Target: L=({p55_target_l[0,0]:.3f}, {p55_target_l[0,1]:.3f}, {p55_target_l[0,2]:.3f})")
    print(f"          R=({p55_target_r[0,0]:.3f}, {p55_target_r[0,1]:.3f}, {p55_target_r[0,2]:.3f})")

    PHASE55B2_STEPS = 100
    p55_pos_l, p55_pos_r, p55_quat_l, p55_quat_r = run_diff_ik_motion_with_collection(
        p55b1_pos_l, p55b1_pos_r, p55b1_quat_l, p55b1_quat_r,
        p55_target_l, p55_target_r, PHASE55B2_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5b2 completion
    s55b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5b2 Complete: L=({s55b_ee_l[0,0]:.3f}, {s55b_ee_l[0,1]:.3f}, {s55b_ee_l[0,2]:.3f})")
    print(f"                        R=({s55b_ee_r[0,0]:.3f}, {s55b_ee_r[0,1]:.3f}, {s55b_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5b2
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5b2!")

    # ================================================================
    # Phase 5.5c: Lower to hook level (Z 1.02 → 0.85) - v39
    # フックZ=0.905より下に下げてからリリース
    # ================================================================
    print("  --- Phase 5.5c: Lower to hook level (Z→0.85) ---")

    # Get current positions
    p55c_start_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p55c_start_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p55c_start_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p55c_start_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Target: Same X/Y, but Z=0.75 (well below hook Z=0.905)
    # v39: 0.85 → 実際0.918で停止（7cm不足）
    # v40: 0.80に下げてフックより確実に下にする
    # v42: 0.75に下げてフックに接触しやすくする
    PHASE55C_Z = 0.75
    p55c_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1], PHASE55C_Z]], device=device)
    p55c_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], WAYPOINT_PHASE55_RIGHT[1], PHASE55C_Z]], device=device)
    print(f"  Target: L=({p55c_target_l[0,0]:.3f}, {p55c_target_l[0,1]:.3f}, {p55c_target_l[0,2]:.3f})")
    print(f"          R=({p55c_target_r[0,0]:.3f}, {p55c_target_r[0,1]:.3f}, {p55c_target_r[0,2]:.3f})")

    PHASE55C_STEPS = 100
    p55c_pos_l, p55c_pos_r, p55c_quat_l, p55c_quat_r = run_diff_ik_motion_with_collection(
        p55c_start_pos_l, p55c_start_pos_r, p55c_start_quat_l, p55c_start_quat_r,
        p55c_target_l, p55c_target_r, PHASE55C_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5c completion
    s55c_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55c_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5c Complete: L=({s55c_ee_l[0,0]:.3f}, {s55c_ee_l[0,1]:.3f}, {s55c_ee_l[0,2]:.3f})")
    print(f"                       R=({s55c_ee_r[0,0]:.3f}, {s55c_ee_r[0,1]:.3f}, {s55c_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5c
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5c!")

    # Short stabilization before release
    print("  [Stabilization] 20 steps before release...")
    for _ in range(20):
        sim.step()
        scene.update(sim.get_physics_dt())

    # ============================================================
    # PHASE 6: RELEASE AND RETREAT (実際の現在位置から)
    # ============================================================
    print("\n[Phase 6] Release and retreat...")

    # Get actual joint positions after Phase 5.5 Diff IK motion
    p55_actual_left = robot_left.data.joint_pos[0, :7].cpu().numpy().tolist()
    p55_actual_right = robot_right.data.joint_pos[0, :7].cpu().numpy().tolist()
    print(f"  Actual joints after Phase 5.5: Left[0]={p55_actual_left[0]:.3f}, Right[0]={p55_actual_right[0]:.3f}")

    # Stabilize at current position
    for i in range(RELEASE_STABILIZE_STEPS):
        set_robot_joints(robot_left, p55_actual_left, GRIPPER_CLOSE)
        set_robot_joints(robot_right, p55_actual_right, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, GRIPPER_CLOSE, GRIPPER_CLOSE)

    # Release gripper gradually
    for i in range(RELEASE_GRIPPER_STEPS):
        alpha = (i + 1) / RELEASE_GRIPPER_STEPS
        gripper_val = GRIPPER_CLOSE + alpha * (GRIPPER_OPEN - GRIPPER_CLOSE)
        set_robot_joints(robot_left, p55_actual_left, gripper_val)
        set_robot_joints(robot_right, p55_actual_right, gripper_val)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, gripper_val, gripper_val)

    # Retreat: Current position -> Phase 7 (Home) via joint interpolation
    for step in range(PHASE55_TO_6_STEPS + POST_RETREAT_STEPS):
        alpha = (step + 1) / (PHASE55_TO_6_STEPS + POST_RETREAT_STEPS)
        left_joints = [p55 + alpha * (p7 - p55) for p55, p7 in zip(p55_actual_left, PHASE7_LEFT_JOINTS)]
        right_joints = [p55 + alpha * (p7 - p55) for p55, p7 in zip(p55_actual_right, PHASE7_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, GRIPPER_OPEN, GRIPPER_OPEN)

    # ============================================================
    # PHASE 7: HOME RETURN (Joint interpolation - already at home from Phase 6)
    # ============================================================
    print("\n[Phase 7] Home return...")

    # Stabilize at home
    for i in range(100):
        set_robot_joints(robot_left, PHASE7_LEFT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, PHASE7_RIGHT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(7, GRIPPER_OPEN, GRIPPER_OPEN)

    print("  Home position reached")

    # ============================================================
    # PHASE 8: CYCLE RESET
    # ============================================================
    print("\n[Phase 8] Cycle reset...")
    reset_success = reset_cable_to_initial()
    if reset_success:
        print("  [OK] Cable reset complete")
    else:
        print("  [WARNING] Cable reset had issues, but continuing")

    # Save cycle data
    collector.save_cycle(cycle_idx)

    return True


# ============================================================
# MAIN LOOP
# ============================================================
success_count = 0

for cycle_idx in range(args.num_cycles):
    success = run_cycle(cycle_idx)
    if success:
        success_count += 1

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("DATA COLLECTION SUMMARY")
print("=" * 70)
print(f"\nCycles completed: {success_count}/{args.num_cycles}")
print(f"Output directory: {args.output_dir}")

# List saved files
saved_files = [f for f in os.listdir(args.output_dir) if f.endswith('.h5')]
print(f"Saved files: {len(saved_files)}")
for f in sorted(saved_files):
    filepath = os.path.join(args.output_dir, f)
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  - {f} ({size_mb:.1f} MB)")

# Convert frames to video if requested
if args.save_video and video_frame_count > 0:
    print("\n" + "=" * 70)
    print("CONVERTING TO VIDEO")
    print("=" * 70)
    print(f"Total frames: {video_frame_count}")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(args.video_fps),
        "-i", os.path.join(VIDEO_FRAME_DIR, "frame_%06d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        args.video_output
    ]

    print(f"Running: {' '.join(ffmpeg_cmd)}")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Video saved: {args.video_output}")
        if os.path.exists(args.video_output):
            size_mb = os.path.getsize(args.video_output) / (1024 * 1024)
            print(f"File size: {size_mb:.1f} MB")
    else:
        print(f"FFmpeg error: {result.stderr}")

    # Cleanup frames
    print("Cleaning up temporary frames...")
    shutil.rmtree(VIDEO_FRAME_DIR)

print("\n" + "=" * 70)
print("DATA COLLECTION COMPLETE")
print("=" * 70)

simulation_app.close()
