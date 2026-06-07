#!/usr/bin/env python3
"""
Replay H5 demo data and generate post-hoc video with 4-camera 2x2 grid.

Purpose: Decouple rendering from live simulation to avoid C++ crash
(LL-20260320-DIAG-001). Loads joint states from H5 file recorded during
headless 0-camera run, replays them in a separate Isaac Sim session with
cameras enabled, and captures frames for ffmpeg video assembly.

Usage:
    cd /home/rlrk/IsaacLab
    DISPLAY=:1 OMNI_KIT_DEFAULT_GPU_INDEX=0 PYTHONPATH=/home/rlrk/IsaacLab \
    ./env_isaaclab/bin/python thread_isaac_lab/scripts/replay_for_video.py \
        --h5_path data/test_v279_H270_nocam_gpu0/demo_cycle_0000.h5 \
        --output data/test_v279_H270_nocam_gpu0/video.mp4 \
        --device cuda:0

State Application Method:
    PENDING rs confirmation — write_joint_state_to_sim usage in replay
    context is ambiguous under CLAUDE.md. Skeleton loads H5 and sets up
    scene/cameras but does NOT apply states until rs confirms.

H5 proprio layout (34D):
    [0:7]   left_joint_pos
    [7:14]  left_joint_vel
    [14:17] left_ee_pos
    [17:24] right_joint_pos
    [24:31] right_joint_vel
    [31:34] right_ee_pos
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
import argparse
import subprocess

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Replay H5 demo and generate post-hoc video")
parser.add_argument("--h5_path", type=str, required=True, help="Path to H5 demo file")
parser.add_argument("--output", type=str, default="data/videos/replay.mp4", help="Output video path")
parser.add_argument("--fps", type=int, default=30, help="Video frame rate")
parser.add_argument("--resolution", type=int, default=512, help="Per-camera resolution")
parser.add_argument("--frame_skip", type=int, default=4,
                    help="Render every N-th step (reduces frame count for long episodes)")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import h5py
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.utils import configclass

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAME_DIR = "/tmp/replay_video_frames"

# ---------------------------------------------------------------------------
# H5 Loading
# ---------------------------------------------------------------------------
def load_h5_data(h5_path: str) -> dict:
    """Load demonstration data from H5 file."""
    print(f"[Replay] Loading H5: {h5_path}")
    if not os.path.exists(h5_path):
        raise FileNotFoundError(f"H5 file not found: {h5_path}")

    with h5py.File(h5_path, "r") as f:
        data = {
            "proprio": np.array(f["proprio"]),   # (T, 34)
            "phase": np.array(f["phase"]),        # (T,)
            "action": np.array(f["action"]),      # (T, 18)
            "task_state": np.array(f["task_state"]),  # (T, 44)
        }
        num_steps = f.attrs.get("num_steps", len(data["proprio"]))
        print(f"[Replay] Loaded {num_steps} steps, proprio shape={data['proprio'].shape}")
    return data


def extract_joint_states(proprio: np.ndarray) -> tuple:
    """Extract left/right joint positions and velocities from proprio.

    Returns:
        left_joint_pos:  (T, 7)
        left_joint_vel:  (T, 7)
        right_joint_pos: (T, 7)
        right_joint_vel: (T, 7)
    """
    left_joint_pos = proprio[:, 0:7]
    left_joint_vel = proprio[:, 7:14]
    right_joint_pos = proprio[:, 17:24]
    right_joint_vel = proprio[:, 24:31]
    return left_joint_pos, left_joint_vel, right_joint_pos, right_joint_vel


# ---------------------------------------------------------------------------
# Scene Setup
# ---------------------------------------------------------------------------
@configclass
class ReplaySceneCfg(DualArmSceneCfg):
    """Scene config for replay — cameras enabled, no contact sensors needed."""
    pass


def setup_scene():
    """Initialize simulation and scene with cameras."""
    sim_cfg = sim_utils.SimulationCfg(dt=1 / 120, render_interval=1)
    sim = sim_utils.SimulationContext(sim_cfg)

    scene_cfg = ReplaySceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    sim.reset()
    scene.reset()

    return sim, scene


def get_cameras(scene):
    """Get camera handles from scene."""
    camera_names = ["front_left_camera", "front_right_camera", "back_camera", "overhead_camera"]
    cameras = {}
    for name in camera_names:
        try:
            cameras[name] = scene[name]
        except KeyError:
            print(f"[Replay] WARNING: Camera '{name}' not found in scene")
    print(f"[Replay] Found {len(cameras)} cameras")
    return cameras


# ---------------------------------------------------------------------------
# Frame Capture
# ---------------------------------------------------------------------------
def capture_grid_frame(cameras: dict, sim, frame_idx: int, resolution: int):
    """Capture 4 cameras and save 2x2 grid frame."""
    dt = sim.get_physics_dt()
    for cam in cameras.values():
        cam.update(dt)

    imgs = {}
    layout_names = ["front_left_camera", "front_right_camera", "back_camera", "overhead_camera"]
    for name in layout_names:
        if name not in cameras:
            imgs[name] = Image.new("RGB", (resolution, resolution), (128, 128, 128))
            continue
        rgb = cameras[name].data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        img = Image.fromarray(rgb.astype(np.uint8))
        imgs[name] = img.resize((resolution, resolution), Image.LANCZOS)

    # 2x2 grid: front_left | front_right / back | overhead
    grid = Image.new("RGB", (resolution * 2, resolution * 2))
    grid.paste(imgs["front_left_camera"], (0, 0))
    grid.paste(imgs["front_right_camera"], (resolution, 0))
    grid.paste(imgs["back_camera"], (0, resolution))
    grid.paste(imgs["overhead_camera"], (resolution, resolution))

    grid.save(os.path.join(FRAME_DIR, f"frame_{frame_idx:06d}.png"))


# ---------------------------------------------------------------------------
# Video Assembly
# ---------------------------------------------------------------------------
def assemble_video(output_path: str, fps: int):
    """Assemble frames into MP4 using ffmpeg."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(FRAME_DIR, "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        output_path,
    ]
    print(f"[Replay] Assembling video: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[Replay] ffmpeg FAILED: {result.stderr[:500]}")
        return False

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[Replay] Video saved: {output_path} ({size_mb:.1f} MB)")
        return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # 1. Load H5 data
    h5_data = load_h5_data(args.h5_path)
    left_jp, left_jv, right_jp, right_jv = extract_joint_states(h5_data["proprio"])
    phases = h5_data["phase"]
    num_steps = len(phases)
    print(f"[Replay] Total steps: {num_steps}, frame_skip: {args.frame_skip}")

    # 2. Setup scene with cameras
    sim, scene = setup_scene()
    cameras = get_cameras(scene)
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    device = robot_left.device

    # 3. Prepare frame directory
    os.makedirs(FRAME_DIR, exist_ok=True)
    for f in os.listdir(FRAME_DIR):
        os.remove(os.path.join(FRAME_DIR, f))

    # 4. Replay loop
    frame_count = 0
    print(f"[Replay] Starting replay of {num_steps} steps...")

    for step_idx in range(num_steps):
        # ------------------------------------------------------------------
        # STATE APPLICATION — PENDING rs confirmation
        # ------------------------------------------------------------------
        # TODO: Apply joint states from H5 to robots.
        #
        # Option B (State Replay) requires write_joint_state_to_sim to
        # teleport robots to recorded positions each step. CLAUDE.md says
        # this is prohibited during "runtime control" but allowed at
        # "reset initialization". Replay is neither — it's offline
        # visualization. rs confirmation needed before uncommenting:
        #
        # left_pos = torch.tensor(left_jp[step_idx], device=device).unsqueeze(0)
        # left_vel = torch.tensor(left_jv[step_idx], device=device).unsqueeze(0)
        # # Append finger joints (default open)
        # left_full_pos = torch.cat([left_pos, torch.zeros(1, 2, device=device)], dim=1)
        # left_full_vel = torch.cat([left_vel, torch.zeros(1, 2, device=device)], dim=1)
        # robot_left.write_joint_state_to_sim(left_full_pos, left_full_vel)
        #
        # right_pos = torch.tensor(right_jp[step_idx], device=device).unsqueeze(0)
        # right_vel = torch.tensor(right_jv[step_idx], device=device).unsqueeze(0)
        # right_full_pos = torch.cat([right_pos, torch.zeros(1, 2, device=device)], dim=1)
        # right_full_vel = torch.cat([right_vel, torch.zeros(1, 2, device=device)], dim=1)
        # robot_right.write_joint_state_to_sim(right_full_pos, right_full_vel)
        #
        # sim.step()
        # scene.update(sim.get_physics_dt())
        # ------------------------------------------------------------------

        # Capture frame at skip interval
        if step_idx % args.frame_skip == 0:
            capture_grid_frame(cameras, sim, frame_count, args.resolution)
            frame_count += 1

            if frame_count % 50 == 0:
                phase = phases[step_idx]
                print(f"[Replay] Step {step_idx}/{num_steps}, Phase {phase}, Frame {frame_count}")

    print(f"[Replay] Captured {frame_count} frames")

    # 5. Assemble video
    if frame_count > 0:
        success = assemble_video(args.output, args.fps)
        if success:
            print(f"[Replay] DONE — video at {args.output}")
        else:
            print("[Replay] FAIL — video assembly failed")
    else:
        print("[Replay] No frames captured — skipping video assembly")

    simulation_app.close()


if __name__ == "__main__":
    main()
