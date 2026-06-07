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
    ik_params={"lambda_val": 0.1},
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
initial_cable_root_state = cable.data.root_state_w.clone()
initial_robot_left_state = robot_left.data.root_state_w.clone()
initial_robot_right_state = robot_right.data.root_state_w.clone()
initial_joint_pos_left = robot_left.data.joint_pos.clone()
initial_joint_vel_left = robot_left.data.joint_vel.clone()
initial_joint_pos_right = robot_right.data.joint_pos.clone()
initial_joint_vel_right = robot_right.data.joint_vel.clone()
print(f"  [OK] Initial states saved after stabilization")


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

        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = joint_cmd_l[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # Phase 3 (lift) detailed NaN detection
        if phase == 3 and nan_detected_step < 0:
            nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
            if nan_seg >= 0:
                nan_detected_step = i
                print(f"\n{'!'*70}")
                print(f"[NaN DETECTED] Step {i}/{num_steps} ({alpha*100:.1f}% lift)")
                print(f"First NaN segment: seg_{nan_seg}")
                print(f"{'!'*70}")
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
            else:
                last_good_pos = pos_arr.copy()
                last_good_vel = vel_arr.copy()
                # Log every step for first 50, every 100 up to 1000, every 10 after 1000
                if i < 50:
                    log_interval = 1  # Every step for early phase
                elif i >= 1000:
                    log_interval = 10
                else:
                    log_interval = 100
                if i % log_interval == 0:
                    speeds = np.linalg.norm(vel_arr, axis=1)
                    z_vals = pos_arr[:, 2]
                    max_speed_idx = np.argmax(speeds)
                    # Get contact force
                    contact_left = scene["contact_left"]
                    contact_right = scene["contact_right"]
                    contact_left.update(sim.get_physics_dt())
                    contact_right.update(sim.get_physics_dt())
                    left_force = contact_left.data.net_forces_w[0].norm().item()
                    right_force = contact_right.data.net_forces_w[0].norm().item()
                    print(f"  [Lift step {i:4d}] Z: {z_vals.min():.4f}-{z_vals.max():.4f}m, max_speed: {speeds.max():.4f} m/s (seg_{max_speed_idx}), contact: L={left_force:.1f}N R={right_force:.1f}N")

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


def reset_cable_to_initial(max_retries: int = 3) -> bool:
    """Reset cable to initial position with comprehensive state restoration.

    Args:
        max_retries: Maximum number of retry attempts.

    Returns:
        True if reset successful (no NaN), False otherwise.
    """
    for attempt in range(max_retries):
        # Full scene reset to clear PhysX solver state
        scene.reset()
        sim.step()  # Apply reset

        # Restore cable state with explicit velocity zeroing
        cable.write_root_state_to_sim(initial_cable_root_state)
        zero_velocity = torch.zeros_like(cable.data.root_vel_w)
        cable.write_root_velocity_to_sim(zero_velocity)
        cable.reset()
        cable.write_data_to_sim()

        # Restore robot states
        robot_left.write_root_state_to_sim(initial_robot_left_state)
        robot_right.write_root_state_to_sim(initial_robot_right_state)
        robot_left.write_joint_state_to_sim(initial_joint_pos_left, initial_joint_vel_left)
        robot_right.write_joint_state_to_sim(initial_joint_pos_right, initial_joint_vel_right)
        robot_left.reset()
        robot_right.reset()

        # Extra stabilization before physics check
        for _ in range(20):
            sim.step()
            scene.update(sim.get_physics_dt())

        # Regular stabilization steps
        for _ in range(CYCLE_RESET_STABILIZATION_STEPS):
            sim.step()
            scene.update(sim.get_physics_dt())

        if check_cable_nan():
            return True
        else:
            print(f"  [WARNING] Cable NaN detected after reset (attempt {attempt + 1}/{max_retries})")
            # Extra stabilization
            for _ in range(CYCLE_RESET_STABILIZATION_STEPS):
                sim.step()
                scene.update(sim.get_physics_dt())

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
    print(f"\n{'='*70}")
    print(f"CYCLE {cycle_idx + 1}/{args.num_cycles}")
    print("=" * 70)

    # Reset collector state for new cycle
    collector.prev_joint_pos_left = None
    collector.prev_joint_pos_right = None

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

    # ============================================================
    # PHASE 1: APPROACH
    # ============================================================
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

    # Grasp: Close grippers while maintaining position (like test_multi_cycle.py)
    print(f"  [Grasp] Closing grippers: {GRIPPER_OPEN} -> {GRIPPER_CLOSE} over {GRASP_CLOSE_STEPS} steps")
    for i in range(GRASP_CLOSE_STEPS):
        # Interpolate gripper position gradually
        t = (i + 1) / GRASP_CLOSE_STEPS
        current_grip = GRIPPER_OPEN + t * (GRIPPER_CLOSE - GRIPPER_OPEN)

        # Hold joint position while closing grippers
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, current_grip)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, current_grip)
        sim.step()
        scene.update(sim.get_physics_dt())

        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, current_grip, current_grip)
        if i % 50 == 0:
            print(f"    [Step {i+1}/{GRASP_CLOSE_STEPS}] grip={current_grip:.4f}")

    # Stabilize: Hold position with grippers closed (like test_multi_cycle.py)
    for i in range(GRASP_STABILIZE):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, GRIPPER_CLOSE, GRIPPER_CLOSE)

    # ============================================================
    # PHASE 2 VERIFICATION: Contact Force
    # ============================================================
    left_force, right_force = get_contact_force()
    print(f"  [Verify] Contact force: L={left_force:.1f}N, R={right_force:.1f}N")
    if left_force < 5 or right_force < 5:
        print(f"  [WARNING] Low contact force detected (expected 10-16N)")
    elif left_force > 30 or right_force > 30:
        print(f"  [WARNING] Excessive contact force detected (expected 10-16N)")

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

    # Measure cable lift using seg_17 (grasped segment) instead of root (seg_0)
    # cable.data.body_pos_w shape: [num_envs, num_bodies, 3]
    # seg_17 is at index 17, seg_19 at index 19
    seg17_z = cable.data.body_pos_w[0, 17, 2].item()
    seg19_z = cable.data.body_pos_w[0, 19, 2].item()
    grasped_z = (seg17_z + seg19_z) / 2
    lift_distance = grasped_z - initial_cable_z
    print(f"  [Verify] Lift distance: {lift_distance*100:.1f}cm (target: {LIFT_CM}cm)")
    print(f"  [Debug] Seg17 Z: {seg17_z:.4f}m, Seg19 Z: {seg19_z:.4f}m")

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
    # PHASE 4-5.5: DIRECT MOVE TO HOOK (Skip Phase 4, 4.5, 5)
    # Phase 4-5 caused gripper orientation issues (gripper pointing up)
    # 2026-01-04: Direct Phase 2 -> Phase 5.5 to maintain gripper down
    # ============================================================
    print("\n[Phase 4-5.5] Direct move to hook position...")

    # FIX: Use actual current joints as start (not PHASE2 which differs after lift)
    # Move directly to Phase 5.5 position with many steps for smooth motion
    DIRECT_HOOK_STEPS = 600  # Slow movement to avoid jerky motion

    # Get actual joint positions after Phase 3 lift
    start_left_joints = robot_left.data.joint_pos[0, :7].cpu().numpy().tolist()
    start_right_joints = robot_right.data.joint_pos[0, :7].cpu().numpy().tolist()
    print(f"  [Interp Fix] Starting from actual joints after lift")

    for step in range(DIRECT_HOOK_STEPS):
        alpha = (step + 1) / DIRECT_HOOK_STEPS
        # Interpolate from actual current joints to Phase 5.5 joints
        left_joints = [s + alpha * (p55 - s) for s, p55 in zip(start_left_joints, PHASE55_LEFT_JOINTS)]
        right_joints = [s + alpha * (p55 - s) for s, p55 in zip(start_right_joints, PHASE55_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_CLOSE)
        set_robot_joints(robot_right, right_joints, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(5, GRIPPER_CLOSE, GRIPPER_CLOSE)

    # ============================================================
    # PHASE 6: RELEASE AND RETREAT (Joint interpolation)
    # ============================================================
    print("\n[Phase 6] Release and retreat...")

    # Stabilize at Phase 5.5 position
    for i in range(RELEASE_STABILIZE_STEPS):
        set_robot_joints(robot_left, PHASE55_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE55_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, GRIPPER_CLOSE, GRIPPER_CLOSE)

    # Release gripper gradually
    for i in range(RELEASE_GRIPPER_STEPS):
        alpha = (i + 1) / RELEASE_GRIPPER_STEPS
        gripper_val = GRIPPER_CLOSE + alpha * (GRIPPER_OPEN - GRIPPER_CLOSE)
        set_robot_joints(robot_left, PHASE55_LEFT_JOINTS, gripper_val)
        set_robot_joints(robot_right, PHASE55_RIGHT_JOINTS, gripper_val)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, gripper_val, gripper_val)

    # Retreat: Phase 5.5 -> Phase 7 (Home) directly via joint interpolation
    for step in range(PHASE55_TO_6_STEPS + POST_RETREAT_STEPS):
        alpha = (step + 1) / (PHASE55_TO_6_STEPS + POST_RETREAT_STEPS)
        left_joints = [p55 + alpha * (p7 - p55) for p55, p7 in zip(PHASE55_LEFT_JOINTS, PHASE7_LEFT_JOINTS)]
        right_joints = [p55 + alpha * (p7 - p55) for p55, p7 in zip(PHASE55_RIGHT_JOINTS, PHASE7_RIGHT_JOINTS)]
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
