#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect ApproachCable expert demo via Newton VBD wet-run.

Reads verified waypoints from dry-run JSON, executes trajectory in Newton VBD
physics, and records (obs, action) pairs matching NewtonApproachCableEnv format.

Design doc: RL-Routing-Design.md §6 (Demo Collection Pipeline)
Principle: wet-run follows dry-run waypoints exactly. No independent position computation.

Output format:
    obs:     [N, 11] float32 — matches NewtonApproachCableEnv observation space
    actions: [N, 6]  float32 — matches NewtonApproachCableEnv action space

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/collect_approach_cable_demo.py \
        --waypoints thread_isaac_lab/data/waypoints/grasp_cable_c1.json \
        --output thread_isaac_lab/data/bc_demos/grasp_cable_demos.npz \
        --device cuda:0 --episodes 50 --save-video
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_script_dir, "..", "envs"))
sys.path.insert(0, os.path.join(_script_dir, "..", "configs"))

from newton_approach_cable_env import NewtonApproachCableEnv

# ── Video constants (shared with test_newton_clip_routing.py) ──
VIDEO_FPS = 30
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960
CAMERAS = [
    ("overhead",   (0.35, -0.05, 1.50), (0.35, -0.05, 0.80)),
    ("front",      (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),
    ("diag_upper", (0.65, -0.40, 1.00), (0.35, -0.05, 0.82)),
    ("left",       (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),
    ("right",      (0.35,  0.55, 0.93), (0.35, -0.05, 0.82)),
]


def _cam_angles(pos, tgt):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


class DemoVideoRecorder:
    """Lightweight video recorder for demo trajectory visualization.

    Captures one frame per RL step (not per physics substep) from the env's
    physics state via Newton ViewerGL headless rendering.
    """

    def __init__(self, output_dir, model, device):
        from newton.viewer import ViewerGL
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.viewer = ViewerGL(
            width=VIDEO_CAM_W, height=VIDEO_CAM_H,
            vsync=False, headless=True,
        )
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        self.device = device
        self._cam_params = []
        self._cam_frames = {}
        for name, pos, tgt in CAMERAS:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cam_params.append((name, wp.vec3(*pos), pitch, yaw))
            self._cam_frames[name] = []
        self._step = 0
        print(f"  [VIDEO] DemoVideoRecorder initialized "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {len(CAMERAS)} cameras)")

    def capture(self, state, sim_time=0.0):
        """Capture one frame from each camera."""
        self._step += 1
        for name, pos, pitch, yaw in self._cam_params:
            self.viewer.set_camera(pos, pitch, yaw)
            self.viewer.begin_frame(sim_time)
            self.viewer.log_state(state)
            self.viewer.end_frame()
            frame = self.viewer.get_frame().numpy().copy()
            self._cam_frames[name].append(frame)

    def save(self, label="demo"):
        """Encode per-camera MP4 videos. Returns list of paths."""
        try:
            from PIL import Image
        except ImportError:
            print("  [VIDEO] PIL not available")
            return []

        n_frames = len(next(iter(self._cam_frames.values()), []))
        if n_frames == 0:
            print("  [VIDEO] No frames to save")
            return []

        video_paths = []
        for name, _, _, _ in self._cam_params:
            frames = self._cam_frames[name]
            if not frames:
                continue
            frames_dir = os.path.join(self.output_dir, f"frames_{label}_{name}")
            os.makedirs(frames_dir, exist_ok=True)
            for i, f in enumerate(frames):
                Image.fromarray(f).save(
                    os.path.join(frames_dir, f"frame_{i:05d}.png"))

            video_path = os.path.join(self.output_dir, f"{label}_{name}.mp4")
            cmd = [
                "ffmpeg", "-y", "-framerate", str(VIDEO_FPS),
                "-i", os.path.join(frames_dir, "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "23", video_path,
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True, timeout=60)
                video_paths.append(video_path)
                import shutil
                shutil.rmtree(frames_dir, ignore_errors=True)
            except Exception as e:
                print(f"  [VIDEO] ffmpeg failed for {name}: {e}")
                video_paths.append(frames_dir)

        print(f"  [VIDEO] Saved {len(video_paths)} videos ({n_frames} frames each)")
        for p in video_paths:
            print(f"    {p}")
        return video_paths

    def reset(self):
        for name in self._cam_frames:
            self._cam_frames[name] = []
        self._step = 0


def compute_action(obs_np, target_r, finger_cmd, action_scale):
    """Compute RL action from current obs toward target EE position.

    Args:
        obs_np: [11] numpy — current observation (env format, unscaled EE at [0:3]).
        target_r: [3] right EE target position [m].
        finger_cmd: float in [-1, 1] — +1=close, -1=open, 0=hold.
        action_scale: float — env's ACTION_SCALE [m/step].

    Returns:
        [6] numpy action — [R_EE_dx, R_EE_dy, R_EE_dz, R_finger, L_EE_dx, L_EE_dy].
    """
    current_ee_r = obs_np[0:3]
    delta = np.array(target_r, dtype=np.float32) - current_ee_r
    action = np.zeros(6, dtype=np.float32)
    action[0:3] = np.clip(delta / action_scale, -1.0, 1.0)
    action[3] = float(finger_cmd)
    # action[4:6] = 0 — left arm holds position
    return action


def run_episode(env, wp_steps, device, recorder=None):
    """Run one demo episode. Returns (obs_list, action_list, success)."""
    action_scale = env.ACTION_SCALE
    obs_finger_scale = env.OBS_FINGER_SCALE
    sim_time = 0.0
    dt_per_step = env.PHYSICS_STEPS_PER_RL * (1.0 / 480.0)

    obs_tensor, _ = env.reset()
    obs = obs_tensor[0].cpu().numpy()

    if recorder is not None:
        recorder.capture(env._state_0, sim_time)

    ep_obs = []
    ep_actions = []
    episode_done = False
    success = False

    for i in range(len(wp_steps) - 1):
        if episode_done:
            break

        wp_from = wp_steps[i]
        wp_to = wp_steps[i + 1]
        target_r = wp_to["target_r"]

        if wp_to["finger_pos"] < wp_from["finger_pos"] - 0.001:
            finger_cmd = 1.0
        elif wp_to["finger_pos"] > wp_from["finger_pos"] + 0.001:
            finger_cmd = -1.0
        else:
            finger_cmd = 0.0

        for s in range(100):
            action = compute_action(obs, target_r, finger_cmd, action_scale)

            ep_obs.append(obs.copy())
            ep_actions.append(action.copy())

            action_tensor = torch.tensor(
                action, dtype=torch.float32, device=device,
            ).unsqueeze(0)
            obs_tensor, reward, done, extras = env.step(action_tensor)
            obs = obs_tensor[0].cpu().numpy()
            sim_time += dt_per_step

            if recorder is not None:
                recorder.capture(env._state_0, sim_time)

            if done.any():
                succ_tensor = extras.get("successes", torch.zeros(1))
                if succ_tensor.any():
                    success = True
                episode_done = True
                break

            ee_dist_mm = np.linalg.norm(
                obs[0:3] - np.array(target_r, dtype=np.float32)) * 1000
            finger_opening = obs[6] / obs_finger_scale
            finger_target_opening = 2 * wp_to["finger_pos"]
            finger_err = abs(finger_opening - finger_target_opening)

            if ee_dist_mm < 2.0 and finger_err < 0.003:
                break

    return ep_obs, ep_actions, success


def main():
    parser = argparse.ArgumentParser(description="ApproachCable wet-run demo collector")
    parser.add_argument("--waypoints", required=True, help="dry-run JSON path")
    parser.add_argument("--output", required=True, help="output .npz path")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--episodes", type=int, default=50,
                        help="Number of demo episodes to collect")
    parser.add_argument("--save-video", action="store_true",
                        help="Record video for first episode (ViewerGL headless)")
    args = parser.parse_args()

    # ── Load verified waypoints (dry-run output) ──
    with open(args.waypoints) as f:
        wp_data = json.load(f)
    wp_steps = wp_data["steps"]
    print(f"[WetRun] Loaded {len(wp_steps)} waypoints from {args.waypoints}")
    for ws in wp_steps:
        print(f"  Step {ws['step']}: {ws['phase']} — "
              f"R={ws['target_r']}, finger_pos={ws['finger_pos']:.3f}, "
              f"status={ws['status']}")

    for ws in wp_steps:
        if ws["status"] != "PASS":
            print(f"[WetRun] ABORT: Step {ws['step']} status={ws['status']}")
            sys.exit(1)

    # ── Create env (single world for demo collection) ──
    env = NewtonApproachCableEnv(world_count=1, device=args.device)

    # ── Video recorder (first episode only) ──
    recorder = None
    if args.save_video:
        video_dir = os.path.join(
            os.path.dirname(os.path.abspath(args.output)), "demo_video")
        recorder = DemoVideoRecorder(video_dir, env._model, args.device)

    all_obs = []
    all_actions = []
    success_count = 0
    t0 = time.perf_counter()

    for ep in range(args.episodes):
        # Record video for first episode only
        ep_recorder = recorder if ep == 0 else None

        ep_obs, ep_actions, success = run_episode(
            env, wp_steps, args.device, recorder=ep_recorder)

        if success:
            success_count += 1

        all_obs.extend(ep_obs)
        all_actions.extend(ep_actions)

        # Save video after first episode
        if ep == 0 and recorder is not None:
            recorder.save(label="demo_ep0")
            recorder.reset()

        if (ep + 1) % 10 == 0 or ep == 0:
            elapsed = time.perf_counter() - t0
            print(f"  ep {ep+1}/{args.episodes}: "
                  f"{len(ep_obs)} steps, "
                  f"success={success_count}/{ep+1}, "
                  f"total={len(all_obs)} transitions, "
                  f"{elapsed:.1f}s")

    # ── Save ──
    obs_array = np.array(all_obs, dtype=np.float32)
    act_array = np.array(all_actions, dtype=np.float32)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    np.savez_compressed(args.output, obs=obs_array, actions=act_array)

    elapsed = time.perf_counter() - t0
    print(f"\n[WetRun] Complete:")
    print(f"  Episodes:     {args.episodes}")
    print(f"  Successes:    {success_count}/{args.episodes}")
    print(f"  Transitions:  {len(all_obs)}")
    print(f"  Obs shape:    {obs_array.shape}")
    print(f"  Action shape: {act_array.shape}")
    print(f"  Elapsed:      {elapsed:.1f}s")
    print(f"  Saved to:     {args.output}")

    # ── Validation ──
    has_nan = False
    if np.any(np.isnan(obs_array)):
        print("[WetRun] WARNING: NaN in observations!")
        has_nan = True
    if np.any(np.isnan(act_array)):
        print("[WetRun] WARNING: NaN in actions!")
        has_nan = True
    if not has_nan:
        print("  NaN check:    PASS")
    print(f"  Obs range:    [{obs_array.min():.4f}, {obs_array.max():.4f}]")
    print(f"  Act range:    [{act_array.min():.4f}, {act_array.max():.4f}]")

    act_labels = ["R_dx", "R_dy", "R_dz", "R_fing", "L_dx", "L_dy"]
    print("  Action stats (mean ± std):")
    for d, label in enumerate(act_labels):
        col = act_array[:, d]
        print(f"    [{d}] {label:8s}: {col.mean():+.3f} ± {col.std():.3f}  "
              f"[{col.min():+.3f}, {col.max():+.3f}]")


if __name__ == "__main__":
    main()
