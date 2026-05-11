#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unified policy evaluation for all THREAD RL skills.

Loads a checkpoint, runs deterministic rollouts, reports per-world metrics,
and optionally records per-camera MP4 videos.

Usage:
    source ~/env_isaaclab6/bin/activate

    # Fast statistics (32 worlds, no video)
    python thread_isaac_lab/scripts/eval_skill.py \
        --skill ac --checkpoint <path/to/model_N.pt> \
        --world-count 32 --device cuda:0

    # Video recording (4 worlds, 5 episodes)
    python thread_isaac_lab/scripts/eval_skill.py \
        --skill ar --checkpoint <path/to/model_best.pt> \
        --base-model <path/to/base_model.pt> \
        --video --episodes 5 --device cuda:0

Supported skills:
    ac           ApproachCable
    ar           AerialRegrasp   (adapter: --base-model)
    ic_approach  InsertIntoClip (approach mode)
    ic_insert    InsertIntoClip (insert mode)
    grip_clamp   Grip clamp      (dual_arm)
    grip_unclamp Grip unclamp
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass

import numpy as np
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_pkg_dir = os.path.join(_script_dir, "..")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _pkg_dir)

from newton_skill_env_base import EE_BODY_OFFSET, FRANKA_NUM_JOINTS

# ---------------------------------------------------------------------------
# Skill Registry
# ---------------------------------------------------------------------------


@dataclass
class SkillEntry:
    env_module: str  # Module name to import from envs/
    env_class: str  # Class name within module
    env_kwargs: dict  # Extra kwargs for env constructor
    default_world_count: int
    uses_adapter: bool  # Whether this skill uses base_model + LoRA
    skill_type: str | None  # SkillType enum value (for adapter)


SKILL_REGISTRY = {
    "ac": SkillEntry(
        env_module="newton_approach_cable_env",
        env_class="NewtonApproachCableEnv",
        env_kwargs={},
        default_world_count=32,
        uses_adapter=True,
        skill_type="APPROACH_CABLE",
    ),
    "ar": SkillEntry(
        env_module="newton_aerial_regrasp_env",
        env_class="NewtonAerialRegraspEnv",
        env_kwargs={},
        default_world_count=4,
        uses_adapter=True,
        skill_type="AERIAL_REGRASP",
    ),
    "ic_approach": SkillEntry(
        env_module="newton_insert_clip_env",
        env_class="NewtonInsertClipEnv",
        env_kwargs={"mode": "approach"},
        default_world_count=32,
        uses_adapter=True,
        skill_type="INSERT_INTO_CLIP",
    ),
    "ic_insert": SkillEntry(
        env_module="newton_insert_clip_env",
        env_class="NewtonInsertClipEnv",
        env_kwargs={"mode": "insert"},
        default_world_count=32,
        uses_adapter=True,
        skill_type="INSERT_INTO_CLIP",
    ),
    "grip_clamp": SkillEntry(
        env_module="newton_grip_env",
        env_class="NewtonGripEnv",
        env_kwargs={"mode": "clamp", "dual_arm": True},
        default_world_count=32,
        uses_adapter=False,
        skill_type="CLAMP",
    ),
    "grip_unclamp": SkillEntry(
        env_module="newton_grip_env",
        env_class="NewtonGripEnv",
        env_kwargs={"mode": "unclamp"},
        default_world_count=32,
        uses_adapter=False,
        skill_type="UNCLAMP",
    ),
}


# ---------------------------------------------------------------------------
# EvalRecorder (unified, camera list parameterized)
# ---------------------------------------------------------------------------

EVAL_CAMERAS_5 = [
    ("overhead", (0.35, -0.05, 2.20), (0.35, -0.05, 0.82)),
    ("front", (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),
    ("right", (0.35, 0.55, 0.93), (0.35, -0.05, 0.82)),
    ("left", (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),
    ("back", (-0.30, -0.05, 1.05), (0.30, -0.05, 0.82)),
]

# On-hand camera: local offsets in hand body frame (body 6 = link7/panda_hand).
# ~45° diagonal view of finger clamp area (opening/closing visible).
# Hand frame: Z toward fingertips, Y = finger open/close axis.
# NOTE: Must match test_newton_clip_routing.py ONHAND_LOCAL_OFFSET/TARGET.
ONHAND_LOCAL_OFFSET = np.array([0.05, 0.05, 0.10])  # 5cm X, 5cm Y, 10cm along Z
ONHAND_LOCAL_TARGET = np.array([0.0, 0.0, 0.17])  # finger mid-area (EE_TO_FINGERTIP≈0.22)

CAM_W, CAM_H = 640, 480
FPS = 30


def _cam_angles(pos, tgt):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm < 1e-9 or math.isnan(norm):
        return 0.0, 0.0
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


def _quat_rotate_np(q_xyzw, v):
    """Rotate vector v by quaternion q (xyzw convention)."""
    qx, qy, qz, qw = q_xyzw[0], q_xyzw[1], q_xyzw[2], q_xyzw[3]
    u = np.array([qx, qy, qz])
    t = 2.0 * np.cross(u, v)
    return v + qw * t + np.cross(u, t)


class EvalRecorder:
    """Per-camera MP4 recorder using Newton ViewerGL (headless offscreen).

    Supports static (world-fixed) cameras and dynamic on-hand cameras that
    track the hand body pose each frame.
    """

    def __init__(self, model, output_dir, cameras=None, onhand_body_indices=None):
        """
        Args:
            model: Newton model for ViewerGL.
            output_dir: Directory for output MP4 files.
            cameras: List of (name, pos, tgt) for static cameras.
            onhand_body_indices: List of (name, body_index) for on-hand cameras.
                Each entry creates a camera that tracks the specified body at
                a 45° diagonal offset looking at the finger clamp area.
        """
        import warp as wp
        from newton.viewer import ViewerGL

        cameras = cameras or EVAL_CAMERAS_5
        self.viewer = ViewerGL(width=CAM_W, height=CAM_H, vsync=False, headless=True)
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        self._cams = []
        for name, pos, tgt in cameras:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cams.append((name, wp.vec3(*pos), pitch, yaw))
        self._cam_names = [c[0] for c in cameras]
        self._frames = {name: [] for name in self._cam_names}
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # On-hand dynamic cameras
        self._onhand_cams = onhand_body_indices or []
        for name, _ in self._onhand_cams:
            self._cam_names.append(name)
            self._frames[name] = []

    def capture(self, state, sim_time):
        import warp as wp

        # Static cameras
        for name, pos, pitch, yaw in self._cams:
            self.viewer.set_camera(pos, pitch, yaw)
            self.viewer.begin_frame(sim_time)
            self.viewer.log_state(state)
            self.viewer.end_frame()
            frame = self.viewer.get_frame().numpy().copy()
            self._frames[name].append(frame)
        # Dynamic on-hand cameras
        if self._onhand_cams:
            body_q = state.body_q.numpy()
            for name, body_idx in self._onhand_cams:
                bq = body_q[body_idx]
                hand_pos = bq[:3]
                hand_quat = bq[3:7]  # xyzw
                cam_pos = hand_pos + _quat_rotate_np(hand_quat, ONHAND_LOCAL_OFFSET)
                cam_tgt = hand_pos + _quat_rotate_np(hand_quat, ONHAND_LOCAL_TARGET)
                pitch, yaw = _cam_angles(cam_pos, cam_tgt)
                self.viewer.set_camera(wp.vec3(*cam_pos), pitch, yaw)
                self.viewer.begin_frame(sim_time)
                self.viewer.log_state(state)
                self.viewer.end_frame()
                frame = self.viewer.get_frame().numpy().copy()
                self._frames[name].append(frame)

    def save(self, episode_idx):
        paths = []
        for name in self._cam_names:
            frames = self._frames[name]
            if not frames:
                continue
            frames_dir = os.path.join(self._output_dir, f"_tmp_{name}_ep{episode_idx}")
            os.makedirs(frames_dir, exist_ok=True)
            for i, f in enumerate(frames):
                from PIL import Image

                img = Image.fromarray(f)
                img.save(os.path.join(frames_dir, f"frame_{i:05d}.png"))

            video_path = os.path.join(self._output_dir, f"ep{episode_idx}_{name}.mp4")
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                os.path.join(frames_dir, "frame_%05d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "23",
                video_path,
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True, timeout=60)
                paths.append(video_path)
                import shutil

                shutil.rmtree(frames_dir, ignore_errors=True)
            except Exception as e:
                print(f"  [EVAL] ffmpeg failed for {name}: {e}")
                paths.append(frames_dir)
        return paths

    def reset(self):
        for name in self._frames:
            self._frames[name] = []


# ---------------------------------------------------------------------------
# Policy loading (checkpoint + optional adapter)
# ---------------------------------------------------------------------------


def _build_train_cfg(env, world_count: int, device: str) -> dict:
    return {
        "seed": 42,
        "device": device,
        "num_steps_per_env": env.MAX_EPISODE_STEPS,
        "max_iterations": 1,
        "save_interval": 999,
        "empirical_normalization": False,
        "policy": {
            "class_name": "ActorCritic",
            "actor_hidden_dims": [128, 128],
            "critic_hidden_dims": [128, 128],
            "activation": "elu",
            "init_noise_std": 0.1,
        },
        "algorithm": {
            "class_name": "PPO",
            "learning_rate": 3e-4,
            "num_learning_epochs": 10,
            "num_mini_batches": min(world_count, 4),
            "gamma": 0.99,
            "lam": 0.95,
            "clip_param": 0.2,
            "entropy_coef": 0.01,
            "max_grad_norm": 1.0,
            "value_loss_coef": 0.5,
            "use_clipped_value_loss": True,
            "desired_kl": 0.01,
            "schedule": "adaptive",
        },
    }


def _load_policy(runner, args, entry: SkillEntry):
    """Load checkpoint into runner, with optional adapter remapping."""
    if args.base_model and entry.uses_adapter:
        from models.skill_adapter import (
            SkillAdapterConfig,
            SkillType,
            apply_skill_adapter,
        )

        skill_type = getattr(SkillType, entry.skill_type)
        print(f"[EVAL] Applying skill adapter from: {args.base_model}")
        cfg = SkillAdapterConfig(lora_rank=args.lora_rank)
        apply_skill_adapter(runner, args.base_model, skill_type, adapter_config=cfg)

    ckpt = torch.load(args.checkpoint, weights_only=False, map_location=args.device)
    sd = ckpt.get("model_state_dict", ckpt)

    # Handle skill_embedding size mismatch (old 5-skill -> new 7-skill)
    emb_key = "adapter.skill_embedding.weight"
    if emb_key in sd:
        model_emb = runner.alg.policy.state_dict().get(emb_key)
        if model_emb is not None and sd[emb_key].shape[0] < model_emb.shape[0]:
            old_skills = [
                "approach_cable",
                "clamp",
                "insert_into_clip",
                "unclamp",
                "aerial_regrasp",
            ]
            from models.skill_adapter import SkillType

            new_skills = [s.value for s in SkillType]
            remapped = torch.zeros_like(model_emb)
            for old_idx, skill_name in enumerate(old_skills):
                if skill_name in new_skills:
                    new_idx = new_skills.index(skill_name)
                    remapped[new_idx] = sd[emb_key][old_idx]
            sd[emb_key] = remapped
            print(f"[EVAL] Remapped skill embedding: {len(old_skills)} -> {model_emb.shape[0]}")

    runner.alg.policy.load_state_dict(sd)
    runner.alg.policy.eval()
    return runner.alg.policy


def _select_action(policy, obs, args) -> torch.Tensor:
    """Select deterministic or stochastic actions with optional eval-time std control."""
    if not args.stochastic:
        return policy.act_inference(obs)

    if args.noise_std_scale is None and args.noise_std_override is None:
        return policy.act(obs)

    if args.noise_std_scale is not None and math.isclose(args.noise_std_scale, 1.0):
        return policy.act(obs)

    if (args.noise_std_scale is not None and args.noise_std_scale <= 0.0) or (
        args.noise_std_override is not None and args.noise_std_override <= 0.0
    ):
        return policy.act_inference(obs)

    actor_obs = policy.get_actor_obs(obs) if hasattr(policy, "get_actor_obs") else obs
    if hasattr(policy, "actor_obs_normalizer"):
        actor_obs = policy.actor_obs_normalizer(actor_obs)
    update_distribution = getattr(policy, "update_distribution", None) or getattr(policy, "_update_distribution")
    update_distribution(actor_obs)
    mean = policy.distribution.mean
    if args.noise_std_override is not None:
        std = torch.full_like(mean, args.noise_std_override)
    else:
        std = policy.distribution.stddev * args.noise_std_scale
    return mean + torch.randn_like(mean) * std


# ---------------------------------------------------------------------------
# Metrics collection
# ---------------------------------------------------------------------------


def _collect_step_metrics(extras: dict, world_count: int, num_envs: int) -> dict:
    """Extract all available metrics from env step extras.

    Args:
        extras: env.step() extras dict with "log" and "log_per_world".
        world_count: Physical world count (N).
        num_envs: RSL-RL env count (N for dual-arm, 2N for per-arm).
    """
    metrics = {}
    log = extras.get("log", {})
    for k, v in log.items():
        metrics[k] = v
    lpw = extras.get("log_per_world", {})
    for k, v in lpw.items():
        arr = np.asarray(v)
        if arr.ndim == 1 and len(arr) in (world_count, num_envs):
            if arr.dtype.kind in {"O", "S", "U"}:
                values, counts = np.unique(arr[:world_count], return_counts=True)
                for value, count in zip(values, counts, strict=True):
                    metrics[f"per_world/{k}/count/{value}"] = int(count)
                continue
            metrics[f"per_world/{k}/median"] = float(np.nanmedian(arr))
            metrics[f"per_world/{k}/mean"] = float(np.nanmean(arr))
            metrics[f"per_world/{k}/min"] = float(np.nanmin(arr))
            metrics[f"per_world/{k}/max"] = float(np.nanmax(arr))
    return metrics


def _detect_termination(extras: dict, env, world_idx: int = 0) -> str:
    """Determine termination reason for a specific world."""
    lpw = extras.get("log_per_world", {})
    if lpw.get("success", np.zeros(1))[world_idx] > 0.5:
        return "success"
    if "explosion" in lpw and lpw["explosion"][world_idx]:
        return "explosion"
    if "cable_terminated" in lpw and lpw["cable_terminated"][world_idx]:
        return "cable_terminated"
    if env.episode_length_buf[world_idx].item() >= env.max_episode_length:
        return "timeout"
    return "unknown"


def _update_best_per_world(best_per_world: dict, lpw: dict, world_count: int) -> None:
    """Track per-world best clamp diagnostics over an episode."""
    min_keys = ("dist_pos_r", "dist_pos_l", "dist_ori_r", "dist_ori_l", "finger_r", "finger_l")
    max_keys = ("success", "explosion")
    for key in min_keys:
        if key not in lpw:
            continue
        arr = np.asarray(lpw[key])
        if arr.ndim == 1 and len(arr) >= world_count:
            vals = arr[:world_count].astype(np.float64, copy=False)
            if key not in best_per_world:
                best_per_world[key] = vals.copy()
            else:
                best_per_world[key] = np.minimum(best_per_world[key], vals)
    for key in max_keys:
        if key not in lpw:
            continue
        arr = np.asarray(lpw[key])
        if arr.ndim == 1 and len(arr) >= world_count:
            vals = arr[:world_count].astype(np.float64, copy=False)
            if key not in best_per_world:
                best_per_world[key] = vals.copy()
            else:
                best_per_world[key] = np.maximum(best_per_world[key], vals)


def _classify_failure_buckets(best_per_world: dict, env, args, world_count: int) -> tuple[dict, list[dict]]:
    """Classify per-world Grip-CLAMP outcomes from best observed diagnostics."""
    required = ("dist_pos_r", "dist_pos_l", "dist_ori_r", "dist_ori_l", "finger_r", "finger_l")
    if not all(k in best_per_world for k in required):
        return {"unavailable": world_count}, []

    pos_thresh = float(getattr(env, "CLAMP_DIST_THRESH", 0.002))
    relaxed_pos_thresh = float(args.failure_bucket_relaxed_pos_thresh)
    ori_thresh = float(getattr(env, "CLAMP_ORI_THRESH", 0.1745))
    finger_thresh = float(getattr(env, "CLAMP_FINGER_THRESH", 0.012))

    success = best_per_world.get("success", np.zeros(world_count)) > 0.5
    explosion = best_per_world.get("explosion", np.zeros(world_count)) > 0.5
    dist_pos_r = best_per_world["dist_pos_r"]
    dist_pos_l = best_per_world["dist_pos_l"]
    dist_ori_r = best_per_world["dist_ori_r"]
    dist_ori_l = best_per_world["dist_ori_l"]
    finger_r = best_per_world["finger_r"]
    finger_l = best_per_world["finger_l"]

    canonical_pos_ok = (dist_pos_r < pos_thresh) & (dist_pos_l < pos_thresh)
    relaxed_pos_ok = (dist_pos_r < relaxed_pos_thresh) & (dist_pos_l < relaxed_pos_thresh)
    ori_ok = (dist_ori_r < ori_thresh) & (dist_ori_l < ori_thresh)
    finger_ok = (finger_r < finger_thresh) & (finger_l < finger_thresh)

    buckets = {
        "success": 0,
        "explosion": 0,
        "near_pos_miss": 0,
        "finger_miss": 0,
        "orientation_miss": 0,
        "position_miss": 0,
        "timeout_or_other": 0,
    }
    per_world = []
    for wi in range(world_count):
        if success[wi]:
            bucket = "success"
        elif explosion[wi]:
            bucket = "explosion"
        elif relaxed_pos_ok[wi] and ori_ok[wi] and finger_ok[wi] and not canonical_pos_ok[wi]:
            bucket = "near_pos_miss"
        elif relaxed_pos_ok[wi] and ori_ok[wi] and not finger_ok[wi]:
            bucket = "finger_miss"
        elif relaxed_pos_ok[wi] and not ori_ok[wi]:
            bucket = "orientation_miss"
        elif not relaxed_pos_ok[wi]:
            bucket = "position_miss"
        else:
            bucket = "timeout_or_other"
        buckets[bucket] += 1
        per_world.append(
            {
                "world": wi,
                "bucket": bucket,
                "dist_pos_r": float(dist_pos_r[wi]),
                "dist_pos_l": float(dist_pos_l[wi]),
                "dist_ori_r": float(dist_ori_r[wi]),
                "dist_ori_l": float(dist_ori_l[wi]),
                "finger_r": float(finger_r[wi]),
                "finger_l": float(finger_l[wi]),
                "success": bool(success[wi]),
                "explosion": bool(explosion[wi]),
            }
        )
    return buckets, per_world


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():  # noqa: C901 -- pre-existing eval CLI complexity; refactor deferred outside B5
    parser = argparse.ArgumentParser(
        description="Unified THREAD RL skill evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Skills: " + ", ".join(SKILL_REGISTRY.keys()),
    )
    parser.add_argument("--skill", type=str, required=True, choices=list(SKILL_REGISTRY.keys()))
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--world-count", type=int, default=None, help="Override default world count for statistics")
    parser.add_argument("--episodes", type=int, default=1, help="Number of episodes (resets) to run")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--video", action="store_true", help="Record per-camera MP4 videos")
    parser.add_argument("--stochastic", action="store_true", help="Use stochastic policy (default: deterministic)")
    parser.add_argument(
        "--noise-std-scale",
        type=float,
        default=None,
        help="Scale stochastic policy std at eval time. 1.0 matches --stochastic; 0.0 is deterministic.",
    )
    parser.add_argument(
        "--noise-std-override",
        type=float,
        default=None,
        help="Override stochastic policy std at eval time. 0.0 is deterministic.",
    )
    parser.add_argument(
        "--failure-bucket-relaxed-pos-thresh",
        type=float,
        default=0.003,
        help="Reporting-only relaxed position threshold [m] for near-miss buckets.",
    )
    parser.add_argument(
        "--expected-arm",
        type=str,
        default="both",
        choices=["right", "left", "both"],
        help="Grip clamp success predicate selector for B5 diagnostics.",
    )
    # Adapter
    parser.add_argument(
        "--base-model", type=str, default=None, help="Base model for SkillAdapter (adapter skills only)"
    )
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument(
        "--onhand-camera",
        action="store_true",
        help="Add on-hand cameras tracking left/right hand bodies (45 deg diagonal)",
    )

    args = parser.parse_args()

    entry = SKILL_REGISTRY[args.skill]

    if args.noise_std_scale is not None and args.noise_std_override is not None:
        parser.error("--noise-std-scale and --noise-std-override are mutually exclusive")
    if args.noise_std_scale is not None and args.noise_std_scale < 0.0:
        parser.error("--noise-std-scale must be non-negative")
    if args.noise_std_override is not None and args.noise_std_override < 0.0:
        parser.error("--noise-std-override must be non-negative")
    if args.failure_bucket_relaxed_pos_thresh <= 0.0:
        parser.error("--failure-bucket-relaxed-pos-thresh must be positive")
    if (args.noise_std_scale is not None or args.noise_std_override is not None) and not args.stochastic:
        print("[EVAL] NOTE: noise std control implies --stochastic mode.")
        args.stochastic = True

    # Validation: on-hand camera requires video
    if args.onhand_camera and not args.video:
        print("[EVAL] WARNING: --onhand-camera requires --video, ignoring.")
        args.onhand_camera = False

    # Validation: adapter mismatch warning
    if args.base_model and not entry.uses_adapter:
        print(
            f"[EVAL] WARNING: --base-model provided but skill '{args.skill}' "
            f"does not use adapter (uses_adapter=False). Ignoring --base-model."
        )
        args.base_model = None
    if not args.base_model and entry.uses_adapter:
        print(
            f"[EVAL] NOTE: skill '{args.skill}' normally uses adapter but "
            f"--base-model not provided. Evaluating as plain MLP."
        )

    world_count = args.world_count or entry.default_world_count
    os.environ["NEWTON_DEVICE"] = args.device

    # Output directory
    if args.output_dir is None:
        ckpt_dir = os.path.dirname(args.checkpoint)
        ckpt_name = os.path.splitext(os.path.basename(args.checkpoint))[0]
        args.output_dir = os.path.join(ckpt_dir, f"eval_{args.skill}_{ckpt_name}")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[EVAL] Skill: {args.skill}")
    print(f"[EVAL] Checkpoint: {args.checkpoint}")
    print(f"[EVAL] Output: {args.output_dir}")
    print(f"[EVAL] Worlds: {world_count}, Episodes: {args.episodes}")
    print(f"[EVAL] Mode: {'stochastic' if args.stochastic else 'deterministic'}")
    if args.noise_std_scale is not None:
        print(f"[EVAL] Noise std scale: {args.noise_std_scale:g}")
    if args.noise_std_override is not None:
        print(f"[EVAL] Noise std override: {args.noise_std_override:g}")
    if args.base_model:
        print(f"[EVAL] Base model: {args.base_model} (LoRA rank={args.lora_rank})")

    # --- Import env ---
    import importlib

    env_mod = importlib.import_module(entry.env_module)
    EnvClass = getattr(env_mod, entry.env_class)

    # --- Create env ---
    print(f"[EVAL] Creating {entry.env_class} (worlds={world_count})...")
    env_kwargs = dict(entry.env_kwargs)
    if args.skill == "grip_clamp":
        env_kwargs["cfg"] = {"expected_arm": args.expected_arm}
    env = EnvClass(world_count=world_count, device=args.device, **env_kwargs)
    max_steps = env.MAX_EPISODE_STEPS

    # --- Load policy ---
    from rsl_rl.runners import OnPolicyRunner

    train_cfg = _build_train_cfg(env, world_count, args.device)
    runner = OnPolicyRunner(
        env=env,
        train_cfg=train_cfg,
        log_dir=args.output_dir,
        device=args.device,
    )
    policy = _load_policy(runner, args, entry)
    print(f"[EVAL] Policy loaded. obs={env.num_obs}D, act={env.num_actions}D")

    # --- Video recorder ---
    recorder = None
    if args.video:
        import warp as wp
        from newton_skill_env_base import RL_SIM_DT

        dt_per_step = RL_SIM_DT * env.PHYSICS_STEPS_PER_RL
        # On-hand cameras: track left/right hand body pose
        onhand = None
        if args.onhand_camera:
            bws0 = env._bws[0]  # body offset for world 0
            onhand = [
                ("hand_L", bws0 + EE_BODY_OFFSET),
                ("hand_R", bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET),
            ]
        recorder = EvalRecorder(
            model=env._model,
            output_dir=args.output_dir,
            onhand_body_indices=onhand,
        )
        n_cams = len(EVAL_CAMERAS_5) + (len(onhand) if onhand else 0)
        print(f"[EVAL] Video recording: {n_cams} cameras, {CAM_W}x{CAM_H}")

    # --- Rollout ---
    num_envs = env.num_envs
    all_results = []

    t0 = time.time()
    for ep in range(args.episodes):
        print(f"\n[EVAL] Episode {ep}/{args.episodes - 1}")
        obs, _ = env.reset()
        if recorder:
            recorder.reset()

        ep_rewards = np.zeros(num_envs)
        sim_time = 0.0
        best_metrics = {}
        best_per_world = {}
        ep_completions = 0
        ep_successes = 0

        for step in range(max_steps):
            with torch.no_grad():
                actions = _select_action(policy, obs, args)

            obs, rewards, dones, extras = env.step(actions)
            ep_rewards += rewards.cpu().numpy()

            if recorder:
                import warp as wp

                sim_time += dt_per_step
                wp.synchronize()
                recorder.capture(env._state_0, sim_time)

            # Collect metrics
            step_m = _collect_step_metrics(extras, world_count, num_envs)

            # Track per-episode success (completed episodes, not snapshots)
            dones_np = dones.cpu().numpy()
            lpw = extras.get("log_per_world", {})
            _update_best_per_world(best_per_world, lpw, world_count)
            success_arr = lpw.get("success", np.zeros(world_count))
            done_indices = np.where(dones_np[:world_count])[0]
            for wi in done_indices:
                ep_completions += 1
                if success_arr[wi] > 0.5:
                    ep_successes += 1

            # Track best values for key metrics
            for k, v in step_m.items():
                if "median" in k or "mean" in k:
                    if "dist" in k:
                        # Distance: track minimum
                        if k not in best_metrics or v < best_metrics[k]:
                            best_metrics[k] = v
                    elif "success" in k:
                        # Success rate: track maximum
                        if k not in best_metrics or v > best_metrics[k]:
                            best_metrics[k] = v

            # Log progress
            if step % 50 == 0 or step == max_steps - 1:
                ep_sr = ep_successes / max(ep_completions, 1)
                dist_keys = [k for k in step_m if "dist_pos" in k and "median" in k]
                dist_str = ""
                if dist_keys:
                    dk = dist_keys[0]
                    dist_str = f"  dist_median={step_m[dk] * 1000:.1f}mm"
                print(
                    f"  step {step:3d}: ep_success={ep_sr:.1%} "
                    f"({ep_successes}/{ep_completions}){dist_str}  "
                    f"reward={np.mean(ep_rewards):.3f}"
                )

            # Track per-world done status (for video episodes)
            if len(done_indices) > 0 and 0 in done_indices:
                term = _detect_termination(extras, env, 0)
                print(f"  ** World 0 DONE @ step {step}: {term}")

            # Check if all worlds done
            if dones.all():
                break

        per_episode_success_rate = ep_successes / max(ep_completions, 1)
        failure_buckets, per_world_buckets = _classify_failure_buckets(best_per_world, env, args, world_count)

        # Episode summary
        video_paths = []
        if recorder:
            video_paths = recorder.save(ep)

        all_results.append(
            {
                "episode": ep,
                "mean_reward": float(np.mean(ep_rewards)),
                "median_reward": float(np.median(ep_rewards)),
                "steps": step + 1,
                "best_metrics": best_metrics,
                "failure_buckets": failure_buckets,
                "per_world_failure_buckets": per_world_buckets,
                "per_episode_success_rate": float(per_episode_success_rate),
                "completions": ep_completions,
                "successes": ep_successes,
                "videos": [str(p) for p in video_paths],
            }
        )

        # Print episode summary
        print(f"  reward: mean={np.mean(ep_rewards):.3f} median={np.median(ep_rewards):.3f}")
        print(
            f"  per_episode_success_rate: {per_episode_success_rate:.1%} "
            f"({ep_successes}/{ep_completions} completed episodes)"
        )
        for k, v in sorted(best_metrics.items()):
            if "dist" in k and "per_world" in k:
                print(f"  best {k}: {v * 1000:.1f}mm")
            elif "success" in k:
                print(f"  best {k}: {v:.4f}")
        if failure_buckets:
            bucket_str = ", ".join(f"{k}={v}" for k, v in sorted(failure_buckets.items()) if v)
            print(f"  failure buckets: {bucket_str}")
        for vp in video_paths:
            print(f"  -> {vp}")

    elapsed = time.time() - t0

    # --- Final Report ---
    print(f"\n{'=' * 70}")
    print(f"  EVAL SUMMARY: {args.skill} ({args.episodes} episodes, {world_count} worlds, {elapsed:.1f}s)")
    print(f"{'=' * 70}")

    rewards_all = [r["mean_reward"] for r in all_results]
    print(f"  Mean reward: {np.mean(rewards_all):.3f} +/- {np.std(rewards_all):.3f}")

    # Per-episode success rate (aggregate)
    total_completions = sum(r["completions"] for r in all_results)
    total_successes = sum(r["successes"] for r in all_results)
    agg_ep_sr = total_successes / max(total_completions, 1)
    print(f"  Per-episode success rate: {agg_ep_sr:.1%} ({total_successes}/{total_completions} completed episodes)")

    # Aggregate best metrics across episodes
    agg_best = {}
    for r in all_results:
        for k, v in r["best_metrics"].items():
            if k not in agg_best:
                agg_best[k] = []
            agg_best[k].append(v)
    if agg_best:
        print("\n  Key Metrics (best per episode, then mean across episodes):")
        for k in sorted(agg_best.keys()):
            vals = agg_best[k]
            mean_v = np.mean(vals)
            if "dist" in k:
                print(f"    {k}: {mean_v * 1000:.1f}mm")
            else:
                print(f"    {k}: {mean_v:.4f}")

    agg_buckets = {}
    for r in all_results:
        for k, v in r.get("failure_buckets", {}).items():
            agg_buckets[k] = agg_buckets.get(k, 0) + v
    if agg_buckets:
        print("\n  Failure Buckets (sum across episodes):")
        for k, v in sorted(agg_buckets.items()):
            if v:
                print(f"    {k}: {v}")

    if args.video:
        print(f"\n  Videos in: {args.output_dir}")

    # --- Save summary JSON ---
    summary = {
        "skill": args.skill,
        "checkpoint": args.checkpoint,
        "base_model": args.base_model,
        "world_count": world_count,
        "mode": "stochastic" if args.stochastic else "deterministic",
        "device": args.device,
        "noise_std_scale": args.noise_std_scale,
        "noise_std_override": args.noise_std_override,
        "failure_bucket_thresholds": {
            "canonical_pos_thresh": float(getattr(env, "CLAMP_DIST_THRESH", 0.002)),
            "relaxed_pos_thresh": float(args.failure_bucket_relaxed_pos_thresh),
            "canonical_ori_thresh": float(getattr(env, "CLAMP_ORI_THRESH", 0.1745)),
            "canonical_finger_thresh": float(getattr(env, "CLAMP_FINGER_THRESH", 0.012)),
        },
        "expected_arm": getattr(env, "_expected_arm", None),
        "expected_arm_code": getattr(env, "_expected_arm_code", None),
        "selected_success_semantics_version": "b5_expected_arm_v1" if args.skill == "grip_clamp" else None,
        "elapsed_s": elapsed,
        "episodes": all_results,
        "aggregate": {
            "mean_reward": float(np.mean(rewards_all)),
            "std_reward": float(np.std(rewards_all)),
            "per_episode_success_rate": float(agg_ep_sr),
            "total_completions": total_completions,
            "total_successes": total_successes,
            "failure_buckets": agg_buckets,
            "best_metrics_mean": {k: float(np.mean(v)) for k, v in agg_best.items()},
        },
    }
    summary_path = os.path.join(args.output_dir, "eval_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary: {summary_path}")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
