# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate a trained ApproachCable policy and render video.

Loads a checkpoint, runs deterministic rollouts in a 1-world env,
and renders per-camera MP4s via Newton ViewerGL (headless offscreen).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/eval_approach_cable.py \
        --checkpoint <path/to/model_N.pt> \
        --episodes 5 --device cuda:0
"""

import argparse
import math
import os
import subprocess
import sys

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)


# Camera definitions (subset: overhead + front + right for eval)
EVAL_CAMERAS = [
    ("overhead", (0.35, -0.05, 1.50), (0.35, -0.05, 0.80)),
    ("front",    (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),
    ("right",    (0.35,  0.55, 0.93), (0.35, -0.05, 0.82)),
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
    """Lightweight per-camera MP4 recorder for eval rollouts."""

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
        self._step = 0
        # Capture every N physics sub-steps to get ~30fps
        # RL env: PHYSICS_STEPS_PER_RL=10, each at RL_SIM_DT
        # We capture once per RL step (called after each env.step)
        os.makedirs(output_dir, exist_ok=True)

    def capture(self, state, sim_time):
        self._step += 1
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
        self._step = 0


def main():
    parser = argparse.ArgumentParser(description="Evaluate ApproachCable policy with video")
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model_N.pt checkpoint")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--deterministic", action="store_true", default=True,
                        help="Use deterministic (mean) actions (default: True)")
    parser.add_argument("--stochastic", action="store_true",
                        help="Use stochastic actions instead of deterministic")
    # Option C' (2026-04-25): dual-eval protocol — fixed cable (sanity) vs
    # randomized cable (deployment-distribution primary eval criterion).
    parser.add_argument("--randomize-cable-xy", action="store_true",
                        help="Enable cable XY ±CABLE_XY_DR_AMPLITUDE DR at each reset. "
                             "Omit for sanity eval (fixed cable baseline). "
                             "Include for deployment-distribution eval (primary success criterion).")
    parser.add_argument("--eval-seed", type=int, default=None,
                        help="Per-episode numpy seed base (seed = eval_seed + ep_idx). "
                             "Default None = OS entropy (true distribution test). "
                             "Set to integer for reproducible cable XY sequence.")
    args = parser.parse_args()

    if args.stochastic:
        args.deterministic = False

    os.environ["NEWTON_DEVICE"] = args.device

    from newton_approach_cable_env import NewtonApproachCableEnv
    from rsl_rl.runners import OnPolicyRunner

    # Output directory
    if args.output_dir is None:
        ckpt_dir = os.path.dirname(args.checkpoint)
        ckpt_name = os.path.splitext(os.path.basename(args.checkpoint))[0]
        args.output_dir = os.path.join(ckpt_dir, f"eval_{ckpt_name}")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[EVAL] Checkpoint: {args.checkpoint}")
    print(f"[EVAL] Output: {args.output_dir}")
    print(f"[EVAL] Episodes: {args.episodes}")
    print(f"[EVAL] Mode: {'deterministic' if args.deterministic else 'stochastic'}")

    # Create 1-world env for rendering
    print("[EVAL] Creating 1-world environment...")
    env = NewtonApproachCableEnv(world_count=1, device=args.device)
    # Option C' (2026-04-25): apply cable XY DR mode to match training distribution.
    env.set_cable_xy_randomize(args.randomize_cable_xy)
    if args.randomize_cable_xy:
        print(f"[EVAL] Cable XY DR: ENABLED (±CABLE_XY_DR_AMPLITUDE per reset, "
              f"eval_seed={args.eval_seed})")
    else:
        print("[EVAL] Cable XY DR: disabled (sanity eval mode, fixed cable)")

    # Build runner + load checkpoint
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
    print("[EVAL] Loading checkpoint...")
    runner.load(args.checkpoint, load_optimizer=False)
    policy = runner.alg.policy
    policy.eval()

    # Video recorder
    recorder = EvalRecorder(model=env._model, output_dir=args.output_dir)

    # Rollout episodes
    results = []
    for ep in range(args.episodes):
        print(f"\n[EVAL] Episode {ep}/{args.episodes-1}")
        # Option C' (2026-04-25): per-episode seed for reproducible cable XY
        # sequence when --eval-seed is set. None = OS entropy (true distribution).
        if args.eval_seed is not None:
            np.random.seed(args.eval_seed + ep)
        obs, _ = env.reset()
        recorder.reset()

        ep_reward = 0.0
        success = False
        sim_time = 0.0
        dt_per_step = (1.0 / 480.0) * env.PHYSICS_STEPS_PER_RL

        for step in range(env.MAX_EPISODE_STEPS):
            with torch.no_grad():
                if args.deterministic:
                    actions = policy.act_inference(obs)
                else:
                    actions = policy.act(obs)

            # Normalize action shape to [N, A] (env expects batched)
            if actions.dim() == 1:
                actions = actions.unsqueeze(0)

            obs, rewards, dones, extras = env.step(actions)
            ep_reward += rewards.sum().item()
            sim_time += dt_per_step

            # Capture frame after physics step
            wp.synchronize()
            recorder.capture(env._state_0, sim_time)

            if dones.any():
                # Env returns success under extras["log_per_world"]["success"] (np.float32 array)
                lpw = extras.get("log_per_world", {})
                if isinstance(lpw, dict) and "success" in lpw:
                    success = bool(np.asarray(lpw["success"]).any())
                elif "success" in extras:  # legacy fallback
                    success = bool(extras["success"].any().item())
                break

        video_paths = recorder.save(ep)
        results.append({
            "episode": ep,
            "reward": ep_reward,
            "steps": step + 1,
            "success": success,
            "videos": video_paths,
        })
        print(f"  reward={ep_reward:.3f}  steps={step+1}  success={success}")
        for vp in video_paths:
            print(f"  -> {vp}")

    # Summary
    print("\n[EVAL] === Summary ===")
    rewards = [r["reward"] for r in results]
    successes = [r["success"] for r in results]
    print(f"  Mean reward: {np.mean(rewards):.3f} +/- {np.std(rewards):.3f}")
    print(f"  Success rate: {sum(successes)}/{len(successes)}")
    print(f"  Videos in: {args.output_dir}")

    # Save summary JSON
    import json
    summary = {
        "checkpoint": args.checkpoint,
        "episodes": results,
        "mean_reward": float(np.mean(rewards)),
        "success_rate": sum(successes) / len(successes) if successes else 0.0,
    }
    summary_path = os.path.join(args.output_dir, "eval_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary: {summary_path}")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
