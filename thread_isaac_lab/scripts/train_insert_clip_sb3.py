# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""SB3 PPO training for InsertIntoClip on Newton VBD.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_insert_clip_sb3.py [--total-steps 100000] [--device cuda:0]
"""

import argparse
import json
import os
import sys
import time

import numpy as np

# Add scripts dir to path for env import
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)


def main():
    parser = argparse.ArgumentParser(description="SB3 PPO InsertIntoClip")
    parser.add_argument("--total-steps", type=int, default=100_000)
    parser.add_argument("--device", type=str, default=os.environ.get("NEWTON_DEVICE", "cuda:0"))
    parser.add_argument("--log-dir", type=str, default=None)
    parser.add_argument("--eval-freq", type=int, default=5000)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Set device before importing Newton
    os.environ["NEWTON_DEVICE"] = args.device

    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from newton_insert_clip_env import NewtonInsertClipEnv

    # Output directory
    if args.log_dir is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        args.log_dir = os.path.join(
            _script_dir, "..", "data", f"rl_insert_clip_sb3_{timestamp}"
        )
    os.makedirs(args.log_dir, exist_ok=True)
    print(f"[SB3] Log dir: {args.log_dir}")
    print(f"[SB3] Device: {args.device}")
    print(f"[SB3] Total steps: {args.total_steps}")

    # Create env
    print("[SB3] Creating environment...")
    env = NewtonInsertClipEnv(device=args.device, verbose=args.verbose)
    print(f"[SB3] Obs space: {env.observation_space}")
    print(f"[SB3] Act space: {env.action_space}")

    # Custom callback for logging
    class InsertClipCallback(BaseCallback):
        def __init__(self, log_dir, eval_freq=5000):
            super().__init__()
            self.log_dir = log_dir
            self.eval_freq = eval_freq
            self.episode_rewards = []
            self.episode_lengths = []
            self.current_reward = 0
            self.current_length = 0
            self.successes = 0
            self.total_episodes = 0
            self.metrics = []
            self.step_times = []
            self._last_time = time.time()

        def _on_step(self):
            now = time.time()
            self.step_times.append(now - self._last_time)
            self._last_time = now

            info = self.locals.get("infos", [{}])[0] if self.locals.get("infos") else {}
            reward = self.locals.get("rewards", [0])[0] if self.locals.get("rewards") is not None else 0
            done = self.locals.get("dones", [False])[0] if self.locals.get("dones") is not None else False

            self.current_reward += float(reward)
            self.current_length += 1

            if done:
                self.episode_rewards.append(self.current_reward)
                self.episode_lengths.append(self.current_length)
                self.total_episodes += 1
                if info.get("groove_insertion", False):
                    self.successes += 1
                self.current_reward = 0
                self.current_length = 0

            if self.num_timesteps % self.eval_freq == 0 and self.total_episodes > 0:
                recent = min(20, len(self.episode_rewards))
                avg_reward = np.mean(self.episode_rewards[-recent:])
                avg_length = np.mean(self.episode_lengths[-recent:])
                success_rate = self.successes / max(self.total_episodes, 1)
                avg_step_ms = np.mean(self.step_times[-1000:]) * 1000

                metric = {
                    "step": self.num_timesteps,
                    "episodes": self.total_episodes,
                    "avg_reward_20": float(avg_reward),
                    "avg_length_20": float(avg_length),
                    "success_rate": float(success_rate),
                    "successes": self.successes,
                    "step_ms": float(avg_step_ms),
                }
                self.metrics.append(metric)

                print(f"[SB3] Step {self.num_timesteps}: "
                      f"ep={self.total_episodes}, "
                      f"reward={avg_reward:.2f}, "
                      f"len={avg_length:.0f}, "
                      f"success={success_rate:.1%}, "
                      f"step={avg_step_ms:.0f}ms")

                # Save metrics
                with open(os.path.join(self.log_dir, "metrics.json"), "w") as f:
                    json.dump(self.metrics, f, indent=2)

            return True

    callback = InsertClipCallback(args.log_dir, eval_freq=args.eval_freq)

    # PPO config
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=200,           # = max_episode_steps (collect full episodes)
        batch_size=200,        # Must divide n_steps * n_envs evenly
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        max_grad_norm=1.0,
        verbose=1,
        device="cpu",          # PPO on CPU (Newton on GPU)
        policy_kwargs={
            "net_arch": [128, 128],
            "activation_fn": __import__("torch").nn.ELU,
        },
    )

    print(f"[SB3] Starting training: {args.total_steps} steps")
    t0 = time.time()

    model.learn(
        total_timesteps=args.total_steps,
        callback=callback,
        progress_bar=False,
    )

    elapsed = time.time() - t0
    print(f"\n[SB3] Training complete in {elapsed:.0f}s")
    print(f"[SB3] Episodes: {callback.total_episodes}")
    print(f"[SB3] Successes: {callback.successes}")
    if callback.total_episodes > 0:
        print(f"[SB3] Success rate: {callback.successes/callback.total_episodes:.1%}")
        print(f"[SB3] Final avg reward (20ep): {np.mean(callback.episode_rewards[-20:]):.2f}")

    # Save model
    model_path = os.path.join(args.log_dir, "ppo_insert_clip")
    model.save(model_path)
    print(f"[SB3] Model saved to {model_path}")

    # Save final summary
    summary = {
        "framework": "SB3",
        "total_steps": args.total_steps,
        "elapsed_s": elapsed,
        "episodes": callback.total_episodes,
        "successes": callback.successes,
        "success_rate": callback.successes / max(callback.total_episodes, 1),
        "avg_step_ms": np.mean(callback.step_times) * 1000 if callback.step_times else 0,
        "final_avg_reward": float(np.mean(callback.episode_rewards[-20:])) if callback.episode_rewards else 0,
        "device": args.device,
    }
    with open(os.path.join(args.log_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[SB3] Summary: {json.dumps(summary, indent=2)}")

    env.close()


if __name__ == "__main__":
    main()
