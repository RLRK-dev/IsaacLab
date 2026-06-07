# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate a trained AerialRegrasp policy and render video.

Loads a checkpoint, runs deterministic rollouts in a 1-world env,
and renders per-camera MP4s via Newton ViewerGL (headless offscreen).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/eval_aerial_regrasp.py \
        --checkpoint <path/to/model_N.pt> \
        --episodes 3 --device cuda:0
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_models_dir = os.path.join(_script_dir, "..")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _models_dir)


EVAL_CAMERAS = [
    ("overhead", (0.35, -0.05, 1.50), (0.35, -0.05, 0.80)),
    ("front",    (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),
    ("right",    (0.35,  0.55, 0.93), (0.35, -0.05, 0.82)),
    ("left",     (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),
    ("back",     (-0.30, -0.05, 1.05), (0.30, -0.05, 0.82)),
]

CAM_W, CAM_H = 640, 480
FPS = 30


def _cam_angles(pos, tgt):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


class EvalRecorder:
    def __init__(self, model, output_dir):
        from newton.viewer import ViewerGL
        self.viewer = ViewerGL(width=CAM_W, height=CAM_H, vsync=False, headless=True)
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        self._cams = []
        for name, pos, tgt in EVAL_CAMERAS:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cams.append((name, wp.vec3(*pos), pitch, yaw))
        self._frames = {name: [] for name, _, _ in EVAL_CAMERAS}
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def capture(self, state, sim_time):
        for name, pos, pitch, yaw in self._cams:
            self.viewer.set_camera(pos, pitch, yaw)
            self.viewer.begin_frame(sim_time)
            self.viewer.log_state(state)
            self.viewer.end_frame()
            frame = self.viewer.get_frame().numpy().copy()
            self._frames[name].append(frame)

    def save(self, episode_idx):
        paths = []
        for name, _, _, _ in self._cams:
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
                "ffmpeg", "-y", "-framerate", str(FPS),
                "-i", os.path.join(frames_dir, "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "23", video_path,
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


def main():
    parser = argparse.ArgumentParser(description="Evaluate AerialRegrasp policy with video")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--deterministic", action="store_true", default=True)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--base-model", type=str, default=None,
                        help="Base model for SkillAdapter (required if trained with --base-model)")
    parser.add_argument("--lora-rank", type=int, default=8)
    args = parser.parse_args()

    if args.stochastic:
        args.deterministic = False

    os.environ["NEWTON_DEVICE"] = args.device

    from rsl_rl.runners import OnPolicyRunner
    from newton_aerial_regrasp_env import NewtonAerialRegraspEnv

    if args.output_dir is None:
        ckpt_dir = os.path.dirname(args.checkpoint)
        ckpt_name = os.path.splitext(os.path.basename(args.checkpoint))[0]
        args.output_dir = os.path.join(ckpt_dir, f"eval_{ckpt_name}")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[EVAL-AR] Checkpoint: {args.checkpoint}")
    print(f"[EVAL-AR] Output: {args.output_dir}")
    print(f"[EVAL-AR] Episodes: {args.episodes}")
    print(f"[EVAL-AR] Mode: {'deterministic' if args.deterministic else 'stochastic'}")

    # Use world_count=4 (smallest cached precondition)
    print("[EVAL-AR] Creating 4-world environment...")
    env = NewtonAerialRegraspEnv(world_count=4, device=args.device)

    train_cfg = {
        "seed": 42,
        "device": args.device,
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
            "num_mini_batches": 1,
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
    runner = OnPolicyRunner(
        env=env, train_cfg=train_cfg,
        log_dir=args.output_dir, device=args.device,
    )

    if args.base_model:
        from models.skill_adapter import apply_skill_adapter, SkillType, SkillAdapterConfig
        print(f"[EVAL-AR] Applying skill adapter from: {args.base_model}")
        cfg = SkillAdapterConfig(lora_rank=args.lora_rank)
        apply_skill_adapter(runner, args.base_model, SkillType.AERIAL_REGRASP, adapter_config=cfg)

    print(f"[EVAL-AR] Loading checkpoint...")
    # Handle skill_embedding size mismatch (v30 has 5 skills, current code has 7)
    # Old 5-skill enum order: AC, CLAMP, IC, UNCLAMP, AR
    # New 7-skill enum order: AC, CLAMP, CLAMP_R, CLAMP_L, IC, UNCLAMP, AR
    ckpt = torch.load(args.checkpoint, weights_only=False, map_location=args.device)
    sd = ckpt["model_state_dict"]
    emb_key = "adapter.skill_embedding.weight"
    if emb_key in sd:
        ckpt_emb = sd[emb_key]
        model_emb = runner.alg.policy.state_dict()[emb_key]
        if ckpt_emb.shape[0] < model_emb.shape[0]:
            # Remap old indices to new positions by skill name
            old_skills = ["approach_cable", "clamp", "insert_into_clip", "unclamp", "aerial_regrasp"]
            from models.skill_adapter import SkillType
            new_skills = [s.value for s in SkillType]
            remapped = torch.zeros_like(model_emb)
            for old_idx, skill_name in enumerate(old_skills):
                if skill_name in new_skills:
                    new_idx = new_skills.index(skill_name)
                    remapped[new_idx] = ckpt_emb[old_idx]
                    print(f"[EVAL-AR] Remap embedding: {skill_name} old[{old_idx}] → new[{new_idx}]")
            sd[emb_key] = remapped
    runner.alg.policy.load_state_dict(sd)
    policy = runner.alg.policy
    policy.eval()

    recorder = EvalRecorder(model=env._model, output_dir=args.output_dir)

    from newton_skill_env_base import RL_SIM_DT
    dt_per_step = RL_SIM_DT * env.PHYSICS_STEPS_PER_RL

    results = []
    for ep in range(args.episodes):
        print(f"\n[EVAL-AR] Episode {ep}/{args.episodes-1}")
        obs, _ = env.reset()
        recorder.reset()

        ep_reward = 0.0
        success = False
        term_reason = "timeout"
        sim_time = 0.0

        for step in range(env.MAX_EPISODE_STEPS):
            with torch.no_grad():
                if args.deterministic:
                    actions = policy.act_inference(obs)
                else:
                    actions = policy.act(obs)

            # Log action stats for world 0 (first 3 steps + every 50)
            if step < 3 or step % 50 == 0:
                a0 = actions[0].cpu().numpy()
                print(f"  step {step}: action[0] norm={np.linalg.norm(a0):.3f} "
                      f"R_pos=[{a0[0]:.3f},{a0[1]:.3f},{a0[2]:.3f}] "
                      f"L_pos=[{a0[6]:.3f},{a0[7]:.3f},{a0[8]:.3f}]")

            obs, rewards, dones, extras = env.step(actions)
            # Use world 0 metrics only (multi-world env, recording world 0)
            ep_reward += rewards[0].item()
            sim_time += dt_per_step

            wp.synchronize()
            recorder.capture(env._state_0, sim_time)

            # Per-step diagnostics for world 0
            lpw = extras.get("log_per_world", {})
            log_agg = extras.get("log", {})
            if step < 3 or step % 50 == 0:
                d0 = lpw.get("dist_pos", [0])[0] if "dist_pos" in lpw else 0
                cz0 = lpw.get("cable_z_min", [0])[0] if "cable_z_min" in lpw else 0
                print(f"         dist_pos={d0:.4f} cable_z_min={cz0:.4f} "
                      f"drop_grace={log_agg.get('/metrics/drop_grace_mean', 0):.1f}")

            # Check only world 0 done status
            if dones[0].item():
                # Extract per-world termination reason
                if lpw.get("success", np.zeros(1))[0] > 0.5:
                    success = True
                    term_reason = "success"
                elif lpw.get("explosion", np.zeros(1))[0]:
                    term_reason = "explosion"
                elif lpw.get("cable_terminated", np.zeros(1))[0]:
                    term_reason = "cable_terminated"
                elif env.episode_length_buf[0].item() >= env.max_episode_length:
                    term_reason = "timeout"
                else:
                    term_reason = "unknown"
                print(f"  ** DONE @ step {step}: reason={term_reason}")
                break

        video_paths = recorder.save(ep)
        results.append({
            "episode": ep,
            "reward": ep_reward,
            "steps": step + 1,
            "success": success,
            "term_reason": term_reason,
            "videos": video_paths,
        })
        print(f"  reward={ep_reward:.3f}  steps={step+1}  success={success}  term={term_reason}")
        for vp in video_paths:
            print(f"  -> {vp}")

    print(f"\n[EVAL-AR] === Summary ===")
    rewards_list = [r["reward"] for r in results]
    successes = [r["success"] for r in results]
    term_reasons = [r["term_reason"] for r in results]
    print(f"  Mean reward: {np.mean(rewards_list):.3f} +/- {np.std(rewards_list):.3f}")
    print(f"  Success rate: {sum(successes)}/{len(successes)}")
    from collections import Counter
    reason_counts = Counter(term_reasons)
    print(f"  Termination reasons: {dict(reason_counts)}")
    print(f"  Mean steps: {np.mean([r['steps'] for r in results]):.1f}")
    print(f"  Videos in: {args.output_dir}")

    summary = {
        "checkpoint": args.checkpoint,
        "episodes": results,
        "mean_reward": float(np.mean(rewards_list)),
        "success_rate": sum(successes) / len(successes) if successes else 0.0,
        "termination_reasons": dict(reason_counts),
    }
    summary_path = os.path.join(args.output_dir, "eval_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary: {summary_path}")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
