# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Analyze per-world correlation between L-arm drift and ori tail in AR env.

Loads a trained AR model, runs 1 episode across N worlds, records per-world
per-step L_drift and dist_ori, then computes correlation.

Usage:
    source ~/env_isaaclab6/bin/activate
    CUDA_VISIBLE_DEVICES=1 python thread_isaac_lab/scripts/analyze_ar_drift_ori_corr.py \
        --checkpoint thread_isaac_lab/data/rl_aerial_regrasp_w256_20260406_162535/model_200.pt \
        --base-model thread_isaac_lab/data/base_model_mixed_20260404_190016.pt \
        --world-count 256 --device cuda:0
"""

import argparse
import math
import os
import sys

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_models_dir = os.path.join(_script_dir, "..")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _models_dir)

from newton_aerial_regrasp_env import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    NewtonAerialRegraspEnv,
    compute_clamp_pos,
    compute_hand_quat_for_cable,
    find_nearest_cable_point,
    normalize_quat_w_positive,
    quat_distance,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--base-model", type=str, required=True)
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument("--world-count", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda:0")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device
    wp.init()
    wp.config.quiet = True

    N = args.world_count
    env = NewtonAerialRegraspEnv(world_count=N, device=args.device)

    # Build runner + load model (same as eval_aerial_regrasp.py)
    from rsl_rl.runners import OnPolicyRunner
    train_cfg = {
        "seed": 42, "device": args.device,
        "num_steps_per_env": env.MAX_EPISODE_STEPS, "max_iterations": 1,
        "save_interval": 999, "empirical_normalization": False,
        "policy": {
            "class_name": "ActorCritic",
            "actor_hidden_dims": [128, 128], "critic_hidden_dims": [128, 128],
            "activation": "elu", "init_noise_std": 0.1,
        },
        "algorithm": {
            "class_name": "PPO", "learning_rate": 3e-4,
            "num_learning_epochs": 10, "num_mini_batches": 1,
            "gamma": 0.99, "lam": 0.95, "clip_param": 0.2,
            "entropy_coef": 0.01, "max_grad_norm": 1.0,
            "value_loss_coef": 0.5, "use_clipped_value_loss": True,
            "desired_kl": 0.01, "schedule": "adaptive",
        },
    }
    runner = OnPolicyRunner(env=env, train_cfg=train_cfg, log_dir="/tmp/corr_dummy", device=args.device)

    from models.skill_adapter import apply_skill_adapter, SkillType, SkillAdapterConfig
    cfg = SkillAdapterConfig(lora_rank=args.lora_rank)
    apply_skill_adapter(runner, args.base_model, SkillType.AERIAL_REGRASP, adapter_config=cfg)
    runner.load(args.checkpoint, load_optimizer=False)
    policy = runner.alg.policy
    policy.eval()

    obs, _ = env.reset()
    max_steps = env.max_episode_length

    drift_history = np.zeros((N, max_steps), dtype=np.float32)
    ori_history = np.zeros((N, max_steps), dtype=np.float32)

    print(f"[CORR] Running {max_steps} steps across {N} worlds...")
    for step in range(max_steps):
        with torch.no_grad():
            actions = policy.act_inference(obs)
        obs, _, _, info = env.step(actions)

        bq = env._state_0.body_q.numpy()
        for w in range(N):
            ws = env._bws[w]

            # L arm EE drift from settled position
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            drift_history[w, step] = float(np.linalg.norm(ee_l_pos - env._settled_ee_l_pos))

            # R arm dist_ori from cable
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]

            cable_bq = bq[env._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            _, seg_tangent, _ = find_nearest_cable_point(
                cable_pos, clamp_r_pos, env._target_seg_indices_r[w]
            )
            clamp_quat = normalize_quat_w_positive(ee_r_quat)
            target_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            ori_history[w, step] = quat_distance(clamp_quat, target_quat)

        if (step + 1) % 50 == 0:
            d_med = np.median(drift_history[:, step]) * 1000
            o_med = np.median(ori_history[:, step]) * 57.3
            print(f"  step {step+1}/{max_steps}  drift_med={d_med:.1f}mm  ori_med={o_med:.1f}deg")

    # === Analysis ===
    print("\n" + "=" * 60)
    print("Per-world correlation: L_drift vs ori")
    print("=" * 60)

    drift_mean = drift_history.mean(axis=1)
    ori_mean = ori_history.mean(axis=1)
    ori_max = ori_history.max(axis=1)
    ori_p95 = np.percentile(ori_history, 95, axis=1)

    def pearson(x, y):
        mx, my = x.mean(), y.mean()
        num = np.sum((x - mx) * (y - my))
        den = np.sqrt(np.sum((x - mx)**2) * np.sum((y - my)**2))
        return num / den if den > 1e-12 else 0.0

    r_mean = pearson(drift_mean, ori_mean)
    r_max = pearson(drift_mean, ori_max)
    r_p95 = pearson(drift_mean, ori_p95)

    print(f"  corr(L_drift_mean, ori_mean):  {r_mean:.4f}")
    print(f"  corr(L_drift_mean, ori_max):   {r_max:.4f}")
    print(f"  corr(L_drift_mean, ori_p95):   {r_p95:.4f}")

    # Burst analysis
    threshold = 0.1745  # 10 degrees
    burst_count = 0
    for w in range(N):
        consec = 0
        for s in range(max_steps):
            if ori_history[w, s] > threshold:
                consec += 1
                if consec >= 2:
                    burst_count += 1
                    break
            else:
                consec = 0

    print(f"\n=== Burst analysis (ori > 10deg for >= 2 consecutive steps) ===")
    print(f"  worlds with burst: {burst_count}/{N} ({100*burst_count/N:.1f}%)")

    # Single-step violation rate
    violations = (ori_history > threshold).sum()
    total = N * max_steps
    print(f"  single-step violation rate: {violations}/{total} ({100*violations/total:.2f}%)")

    # Quartile analysis
    drift_sorted = np.argsort(drift_mean)
    q_size = N // 4
    print(f"\n=== Quartile analysis (worlds by L_drift_mean) ===")
    print(f"{'Quartile':>10} {'drift_mm':>10} {'ori_med_d':>10} {'ori_p95_d':>10} {'ori_max_d':>10} {'burst%':>8}")
    for qi, label in enumerate(["Q1(low)", "Q2", "Q3", "Q4(high)"]):
        idx = drift_sorted[qi * q_size:(qi + 1) * q_size]
        d = np.median(drift_mean[idx]) * 1000
        o_med = np.median(ori_mean[idx]) * 57.3
        o_p95 = np.median(ori_p95[idx]) * 57.3
        o_max = np.median(ori_max[idx]) * 57.3
        bursts = sum(1 for w in idx
                     if any(ori_history[w, s] > threshold and ori_history[w, s+1] > threshold
                            for s in range(max_steps - 1)))
        print(f"{label:>10} {d:>9.1f}mm {o_med:>9.1f}deg {o_p95:>9.1f}deg {o_max:>9.1f}deg {100*bursts/len(idx):>7.1f}%")

    # Autocorrelation of ori (burst measure)
    lags = [1, 2, 5]
    print(f"\n=== Ori autocorrelation (temporal burst indicator) ===")
    for lag in lags:
        x = ori_history[:, :-lag].flatten()
        y = ori_history[:, lag:].flatten()
        ac = pearson(x, y)
        print(f"  lag={lag}: {ac:.4f}")

    out_path = os.path.join(_script_dir, "..", "data", "ar_drift_ori_corr.npz")
    np.savez(out_path, drift=drift_history, ori=ori_history)
    print(f"\nRaw data saved: {out_path}")


if __name__ == "__main__":
    main()
