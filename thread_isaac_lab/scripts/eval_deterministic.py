# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Fast deterministic eval — no video, multi-world.

Loads a checkpoint, runs deterministic (act_inference) rollouts,
reports per-step dist_pos/dist_ori metrics.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/eval_deterministic.py \
        --checkpoint <path/to/model_N.pt> \
        --world-count 32 --device cuda:0
"""

import argparse
import os
import sys

import numpy as np
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)


def main():
    parser = argparse.ArgumentParser(description="Fast deterministic eval")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--world-count", type=int, default=32)
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--num-obs", type=int, default=36,
                        help="Obs dimension (33 or 36)")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    from rsl_rl.runners import OnPolicyRunner
    from newton_approach_cable_env import NewtonApproachCableEnv

    print(f"[EVAL] Checkpoint: {args.checkpoint}")
    print(f"[EVAL] Worlds: {args.world_count}, Device: {args.device}")

    env = NewtonApproachCableEnv(world_count=args.world_count, device=args.device)

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
            "num_mini_batches": min(args.world_count, 4),
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
        log_dir="/tmp/eval_det", device=args.device,
    )
    runner.load(args.checkpoint, load_optimizer=False)
    policy = runner.alg.policy
    policy.eval()

    obs, _ = env.reset()

    step_metrics = []
    best_pos_median = 999.0
    best_ori_median = 999.0

    for step in range(env.MAX_EPISODE_STEPS):
        with torch.no_grad():
            actions = policy.act_inference(obs)

        obs, rewards, dones, extras = env.step(actions)

        log = extras.get("log", {})
        pw = extras.get("log_per_world", {})

        dist_pos = pw.get("dist_pos", np.array([]))
        dist_ori = pw.get("dist_ori", np.array([]))

        pos_median = float(np.median(dist_pos)) if len(dist_pos) > 0 else -1
        ori_median = float(np.median(dist_ori)) if len(dist_ori) > 0 else -1
        pos_min = float(np.min(dist_pos)) if len(dist_pos) > 0 else -1
        success = log.get("/episode/success", 0.0)

        best_pos_median = min(best_pos_median, pos_median)
        best_ori_median = min(best_ori_median, ori_median)

        step_metrics.append({
            "step": step,
            "pos_median": pos_median,
            "ori_median": ori_median,
            "pos_min": pos_min,
            "success": success,
        })

        if step % 20 == 0 or step == env.MAX_EPISODE_STEPS - 1:
            n_under_8mm = int(np.sum(dist_pos < 0.008)) if len(dist_pos) > 0 else 0
            print(f"  step {step:3d}: pos_median={pos_median*1000:.1f}mm  "
                  f"ori_median={ori_median:.3f}rad  "
                  f"pos_min={pos_min*1000:.1f}mm  "
                  f"<8mm={n_under_8mm}/{len(dist_pos)}  "
                  f"success={success:.4f}")

        if dones.all():
            break

    print(f"\n[EVAL] === Summary (deterministic, σ=0) ===")
    print(f"  Best dist_pos_median: {best_pos_median*1000:.1f}mm")
    print(f"  Best dist_ori_median: {best_ori_median:.3f}rad")
    print(f"  Final dist_pos_median: {step_metrics[-1]['pos_median']*1000:.1f}mm")
    print(f"  Final dist_ori_median: {step_metrics[-1]['ori_median']:.3f}rad")

    if best_pos_median < 0.008:
        print(f"  >>> POLICY REACHES 8mm. Problem is training noise only.")
    elif best_pos_median < 0.016:
        print(f"  >>> POLICY approaches but doesn't reach 8mm. Noise + policy gap.")
    else:
        print(f"  >>> POLICY stuck at {best_pos_median*1000:.1f}mm. Policy capacity insufficient.")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
