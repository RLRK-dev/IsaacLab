#!/usr/bin/env python3
"""THREAD: Hook-Hanging Training with Isaac Lab 2.3.0 + RSL-RL 3.x"""

from __future__ import annotations
import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="THREAD Hook-Hanging Training")
parser.add_argument("--num_envs", type=int, default=256)
parser.add_argument("--max_iterations", type=int, default=50000)
parser.add_argument("--learning_rate", type=float, default=3e-4)
parser.add_argument("--experiment_name", type=str, default="THREAD_HookHanging")
parser.add_argument("--seed", type=int, default=42)

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

print("=" * 60)
print("THREAD: Hook-Hanging Training with Isaac Lab 2.3.0")
print("=" * 60)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

print("Isaac Sim initialized!")

import torch
import gymnasium as gym
from pathlib import Path
from datetime import datetime

# Add thread_isaac_lab to path
sys.path.insert(0, str(Path(__file__).parent))

from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from rsl_rl.runners import OnPolicyRunner

# Import THREAD environment
from envs.hook_hanging_env import HookHangingEnv, HookHangingEnvCfg

print(f"\nConfig: num_envs={args.num_envs}, lr={args.learning_rate}")
print("=" * 60)

# Enable TF32 for faster training
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


def main():
    device = args.device if args.device else "cuda:0"

    print("\n[1/3] Creating Hook-Hanging environment...")

    # Create environment config
    env_cfg = HookHangingEnvCfg()
    env_cfg.scene.num_envs = args.num_envs
    env_cfg.seed = args.seed

    # Create environment
    env = HookHangingEnv(cfg=env_cfg)

    # Get observation and action dimensions
    obs = env.observation_manager.compute()
    num_obs = obs["policy"].shape[-1]
    num_actions = env.action_manager.total_action_dim

    print(f"  Task: THREAD Hook-Hanging")
    print(f"  num_envs: {args.num_envs}, obs_dim: {num_obs}, action_dim: {num_actions}")

    # Wrap for RSL-RL
    env = RslRlVecEnvWrapper(env)

    # Setup log directory
    log_root = Path(f"logs/rsl_rl/{args.experiment_name}")
    log_dir = log_root / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir.mkdir(parents=True, exist_ok=True)

    print("\n[2/3] Creating OnPolicyRunner...")

    # RSL-RL 3.x train_cfg format (A6000 48GB最適化)
    train_cfg = {
        "seed": args.seed,
        "device": device,
        "num_steps_per_env": 48,  # 増加: 24 → 48 (GPU使用率向上)
        "max_iterations": args.max_iterations,
        "save_interval": 100,
        "empirical_normalization": False,
        "obs_groups": {},  # Will be resolved by runner
        "policy": {
            "class_name": "ActorCritic",
            "actor_hidden_dims": [512, 256, 128],  # 増加: より大きなネットワーク
            "critic_hidden_dims": [512, 256, 128],
            "activation": "elu",
            "init_noise_std": 1.0,
        },
        "algorithm": {
            "class_name": "PPO",
            "value_loss_coef": 1.0,
            "use_clipped_value_loss": True,
            "clip_param": 0.2,
            "entropy_coef": 0.01,
            "num_learning_epochs": 5,
            "num_mini_batches": 8,  # 増加: 4 → 8 (バッチサイズ最適化)
            "learning_rate": args.learning_rate,
            "schedule": "adaptive",
            "gamma": 0.99,
            "lam": 0.95,
            "desired_kl": 0.01,
            "max_grad_norm": 1.0,
        },
    }

    runner = OnPolicyRunner(
        env=env,
        train_cfg=train_cfg,
        log_dir=str(log_dir),
        device=device
    )

    print(f"  Log dir: {log_dir}")
    print(f"  Iterations: {args.max_iterations}")

    print("\n[3/3] Starting training...")
    print("=" * 60)

    runner.learn(num_learning_iterations=args.max_iterations, init_at_random_ep_len=True)

    # Save final model
    final_path = log_dir / "policy_final.pt"
    runner.save(str(final_path))
    print(f"\nSaved: {final_path}")

    env.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulation_app.close()
