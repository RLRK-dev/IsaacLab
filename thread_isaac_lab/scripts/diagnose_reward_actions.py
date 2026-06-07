# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Diagnose reward components and action distributions for ApproachCable policy.

Uses the v8 env's native per-component reward logging (no monkey-patching).
Reports per-phase breakdown of reward components and action distributions.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/diagnose_reward_actions.py \
        --checkpoint thread_isaac_lab/data/rl_grasp_cable_A_w256_20260328_233910/model_0.pt \
        --world-count 64 --device cuda:1
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)


def main():
    parser = argparse.ArgumentParser(description="Diagnose reward + action distributions")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--world-count", type=int, default=64)
    parser.add_argument("--device", type=str, default="cuda:1")
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    from rsl_rl.runners import OnPolicyRunner
    from newton_approach_cable_env import NewtonApproachCableEnv

    N = args.world_count
    T = args.max_steps

    print(f"[DIAG] Checkpoint: {args.checkpoint}")
    print(f"[DIAG] Worlds: {N}, Steps: {T}, Device: {args.device}")

    env = NewtonApproachCableEnv(world_count=N, device=args.device)

    train_cfg = {
        "seed": 42, "device": args.device,
        "num_steps_per_env": T, "max_iterations": 1, "save_interval": 999,
        "empirical_normalization": False,
        "policy": {
            "class_name": "ActorCritic",
            "actor_hidden_dims": [128, 128],
            "critic_hidden_dims": [128, 128],
            "activation": "elu",
            "init_noise_std": 0.1,
        },
        "algorithm": {
            "class_name": "PPO", "learning_rate": 3e-4,
            "num_learning_epochs": 10, "num_mini_batches": min(N, 4),
            "gamma": 0.99, "lam": 0.95, "clip_param": 0.2,
            "entropy_coef": 0.01, "max_grad_norm": 1.0,
            "value_loss_coef": 0.5, "use_clipped_value_loss": True,
            "desired_kl": 0.01, "schedule": "adaptive",
        },
    }

    log_dir = os.path.join(os.path.dirname(args.checkpoint), "diag_reward_actions")
    os.makedirs(log_dir, exist_ok=True)
    runner = OnPolicyRunner(env=env, train_cfg=train_cfg, log_dir=log_dir, device=args.device)
    print(f"[DIAG] Loading checkpoint...")
    runner.load(args.checkpoint, load_optimizer=False)
    policy_fn = runner.get_inference_policy(device=args.device)

    # Collect per-step data
    all_actions = []
    all_rewards = []
    all_log_data = []
    all_per_world = []  # per-world arrays [T, N]

    obs, _ = env.get_observations()
    print(f"[DIAG] Running {T} steps x {N} worlds (deterministic)...")
    t0 = time.time()

    for step in range(T):
        with torch.no_grad():
            actions = policy_fn(obs)
        obs, rewards, dones, extras = env.step(actions)
        all_actions.append(actions.cpu().numpy())
        all_rewards.append(rewards.cpu().numpy())
        if "log" in extras:
            all_log_data.append({k: v for k, v in extras["log"].items()})
        if "log_per_world" in extras:
            all_per_world.append({k: v.copy() for k, v in extras["log_per_world"].items()})

    elapsed = time.time() - t0
    print(f"[DIAG] Done in {elapsed:.1f}s")

    actions_arr = np.stack(all_actions)   # [T, N, 6]
    rewards_arr = np.stack(all_rewards)   # [T, N]

    # Per-world trajectory arrays
    has_pw = len(all_per_world) == T
    if has_pw:
        pw_dist = np.stack([d["dist"] for d in all_per_world])             # [T, N]
        pw_finger = np.stack([d["finger_opening"] for d in all_per_world]) # [T, N]

    # ================================================================
    # REWARD COMPONENT ANALYSIS
    # ================================================================
    print("\n" + "=" * 70)
    print(f"REWARD COMPONENT ANALYSIS ({N} worlds, {T} steps)")
    print("=" * 70)

    if all_log_data:
        keys = sorted(all_log_data[0].keys())
        for key in keys:
            vals = [d[key] for d in all_log_data if key in d]
            print(f"  {key:40s}  mean={np.mean(vals):10.6f}  std={np.std(vals):10.6f}")

    # Per-phase breakdown
    third = T // 3
    phases = [
        ("early  (steps 0-66)", 0, third),
        ("mid    (steps 67-133)", third, 2 * third),
        ("late   (steps 134-200)", 2 * third, T),
    ]
    reward_keys = [k for k in (all_log_data[0].keys() if all_log_data else []) if k.startswith("/reward/")]
    metric_keys = [k for k in (all_log_data[0].keys() if all_log_data else []) if k.startswith("/metrics/")]

    print(f"\n--- Per-Phase Reward Components ---")
    for phase_name, s, e in phases:
        print(f"  {phase_name}:")
        for key in sorted(reward_keys):
            vals = [d[key] for d in all_log_data[s:e] if key in d]
            if vals:
                print(f"    {key:38s}  mean={np.mean(vals):10.6f}")

    print(f"\n--- Per-Phase Metrics ---")
    for phase_name, s, e in phases:
        print(f"  {phase_name}:")
        for key in sorted(metric_keys):
            vals = [d[key] for d in all_log_data[s:e] if key in d]
            if vals:
                print(f"    {key:38s}  mean={np.mean(vals):10.6f}")

    # ================================================================
    # ACTION DISTRIBUTION ANALYSIS
    # ================================================================
    print("\n" + "=" * 70)
    print("ACTION DISTRIBUTION ANALYSIS")
    print("=" * 70)

    act_names = ["right_dx", "right_dy", "right_dz", "finger_cmd", "left_dx", "left_dy"]
    for i, name in enumerate(act_names):
        a = actions_arr[:, :, i].flatten()
        pcts = np.percentile(a, [5, 25, 50, 75, 95])
        print(f"  {name:12s}  mean={np.mean(a):7.4f}  std={np.std(a):7.4f}  "
              f"[p5={pcts[0]:7.4f}  p50={pcts[2]:7.4f}  p95={pcts[4]:7.4f}]")

    # Finger command analysis
    finger = actions_arr[:, :, 3].flatten()
    close_pct = float(np.mean(finger > 0)) * 100
    open_pct = float(np.mean(finger < 0)) * 100
    print(f"\n  Finger command overall:  close(>0)={close_pct:.1f}%  open(<0)={open_pct:.1f}%")

    print(f"\n  Per-phase finger command:")
    for phase_name, s, e in phases:
        fc = actions_arr[s:e, :, 3].flatten()
        print(f"    {phase_name}:  mean={np.mean(fc):7.4f}  close%={float(np.mean(fc > 0)) * 100:5.1f}%  "
              f"open%={float(np.mean(fc < 0)) * 100:5.1f}%  std={np.std(fc):.4f}")

    # Per-phase action magnitudes (EE movement)
    print(f"\n  Per-phase EE action magnitude:")
    for phase_name, s, e in phases:
        ee = actions_arr[s:e, :, :3]  # [steps, N, 3]
        mag = np.linalg.norm(ee, axis=2).flatten()
        print(f"    {phase_name}:  mean={np.mean(mag):.4f}  std={np.std(mag):.4f}  "
              f"max={np.max(mag):.4f}")

    # ================================================================
    # CUMULATIVE REWARD
    # ================================================================
    cumrew = rewards_arr.sum(axis=0)  # [N]
    print(f"\n" + "=" * 70)
    print(f"CUMULATIVE REWARD ({N} worlds)")
    print(f"=" * 70)
    pcts = np.percentile(cumrew, [0, 10, 25, 50, 75, 90, 100])
    print(f"  mean={np.mean(cumrew):.2f}  std={np.std(cumrew):.2f}")
    print(f"  p0={pcts[0]:.2f}  p10={pcts[1]:.2f}  p25={pcts[2]:.2f}  "
          f"p50={pcts[3]:.2f}  p75={pcts[4]:.2f}  p90={pcts[5]:.2f}  p100={pcts[6]:.2f}")

    # Step reward trend
    step_means = rewards_arr.mean(axis=1)
    print(f"\n  Per-step reward trend (20-step bins):")
    for i in range(0, T, 20):
        end = min(i + 20, T)
        print(f"    steps {i:3d}-{end:3d}: {np.mean(step_means[i:end]):.4f}")

    # ================================================================
    # PER-WORLD TRAJECTORY ANALYSIS (hypothesis verification)
    # ================================================================
    if has_pw:
        APPROACH_MAX_DIST = 0.03  # 30mm — must match env
        print(f"\n" + "=" * 70)
        print(f"PER-WORLD TRAJECTORY ANALYSIS ({N} worlds)")
        print("=" * 70)

        # Per-world: min dist achieved and step at which it was achieved
        min_dist_per_world = pw_dist.min(axis=0)       # [N]
        min_dist_step = pw_dist.argmin(axis=0)          # [N]

        # Per-world: step at which finger fully closed (< 5mm)
        finger_closed_step = np.full(N, T, dtype=int)
        for w in range(N):
            closed_mask = pw_finger[:, w] < 0.005
            if closed_mask.any():
                finger_closed_step[w] = int(np.argmax(closed_mask))

        print(f"\n  --- Finger close vs approach timing ---")
        print(f"  Finger closed step:  median={np.median(finger_closed_step):.0f}  "
              f"mean={np.mean(finger_closed_step):.1f}  "
              f"p10={np.percentile(finger_closed_step, 10):.0f}  "
              f"p90={np.percentile(finger_closed_step, 90):.0f}")
        print(f"  Min dist step:       median={np.median(min_dist_step):.0f}  "
              f"mean={np.mean(min_dist_step):.1f}  "
              f"p10={np.percentile(min_dist_step, 10):.0f}  "
              f"p90={np.percentile(min_dist_step, 90):.0f}")
        close_before_approach = np.sum(finger_closed_step < min_dist_step)
        print(f"  Close BEFORE min-dist: {close_before_approach}/{N} ({100*close_before_approach/N:.1f}%)")

        # Death zone analysis: worlds where a=0 for most of episode
        a_values = np.clip(1.0 - pw_dist / APPROACH_MAX_DIST, 0, 1)  # [T, N]
        death_zone_frac = np.mean(a_values == 0, axis=0)  # [N] fraction of steps in death zone
        print(f"\n  --- Death zone (dist > {APPROACH_MAX_DIST*1000:.0f}mm → a=0, no reward) ---")
        print(f"  Frac of episode in death zone per world:")
        print(f"    mean={np.mean(death_zone_frac):.2f}  "
              f"median={np.median(death_zone_frac):.2f}  "
              f"p10={np.percentile(death_zone_frac, 10):.2f}  "
              f"p90={np.percentile(death_zone_frac, 90):.2f}")
        chronic_death = np.sum(death_zone_frac > 0.5)
        print(f"  Worlds >50% in death zone: {chronic_death}/{N} ({100*chronic_death/N:.1f}%)")

        # Hypothesis 1 check: dist plateau after close
        # For each world, after finger close, does dist stabilize or diverge?
        print(f"\n  --- Hypothesis 1: geometric blockage (dist after close) ---")
        dist_after_close = []
        for w in range(N):
            cs = finger_closed_step[w]
            if cs < T - 10:  # at least 10 steps after close
                dist_post = pw_dist[cs:, w]
                dist_after_close.append(dist_post)
        if dist_after_close:
            # Check if dist stabilizes (std < mean * 0.3) or diverges (trend > 0)
            stabilize_count = 0
            diverge_count = 0
            for traj in dist_after_close:
                mean_d = np.mean(traj)
                # Linear trend: positive = diverging
                if len(traj) > 1:
                    trend = (traj[-1] - traj[0]) / len(traj)
                    if trend > 0.0001:  # > 0.1mm/step divergence
                        diverge_count += 1
                    elif np.std(traj) < mean_d * 0.3:
                        stabilize_count += 1
            print(f"  Worlds with dist data after close: {len(dist_after_close)}/{N}")
            print(f"    Diverging (trend > 0.1mm/step):  {diverge_count} ({100*diverge_count/len(dist_after_close):.1f}%)")
            print(f"    Stabilizing (low std):           {stabilize_count} ({100*stabilize_count/len(dist_after_close):.1f}%)")
            # Distribution of dist at close-step vs end-of-episode
            dist_at_close = np.array([pw_dist[finger_closed_step[w], w] for w in range(N) if finger_closed_step[w] < T])
            dist_at_end = np.array([pw_dist[-1, w] for w in range(N) if finger_closed_step[w] < T])
            if len(dist_at_close) > 0:
                print(f"    Dist at close step:  mean={np.mean(dist_at_close)*1000:.1f}mm  "
                      f"median={np.median(dist_at_close)*1000:.1f}mm")
                print(f"    Dist at episode end: mean={np.mean(dist_at_end)*1000:.1f}mm  "
                      f"median={np.median(dist_at_end)*1000:.1f}mm")
        else:
            print(f"  No worlds with sufficient post-close data")

    # ================================================================
    # SAVE RESULTS
    # ================================================================
    if args.output is None:
        args.output = os.path.join(os.path.dirname(args.checkpoint), "diag_reward_actions.json")

    result = {
        "checkpoint": args.checkpoint,
        "world_count": N,
        "max_steps": T,
        "elapsed_s": elapsed,
        "reward_components": {},
        "reward_by_phase": {},
        "action_stats": {},
        "finger_distribution": {"close_pct": close_pct, "open_pct": open_pct},
        "cumulative_reward": {
            "mean": float(np.mean(cumrew)), "std": float(np.std(cumrew)),
            "min": float(np.min(cumrew)), "max": float(np.max(cumrew)),
        },
    }
    if all_log_data:
        for key in sorted(all_log_data[0].keys()):
            vals = [d[key] for d in all_log_data if key in d]
            result["reward_components"][key] = {"mean": float(np.mean(vals)), "std": float(np.std(vals))}
        for phase_name, s, e in phases:
            pd = {}
            for key in sorted(all_log_data[0].keys()):
                vals = [d[key] for d in all_log_data[s:e] if key in d]
                if vals:
                    pd[key] = float(np.mean(vals))
            result["reward_by_phase"][phase_name] = pd
    for i, name in enumerate(act_names):
        a = actions_arr[:, :, i].flatten()
        result["action_stats"][name] = {
            "mean": float(np.mean(a)), "std": float(np.std(a)),
            "min": float(np.min(a)), "max": float(np.max(a)),
        }
    if has_pw:
        result["per_world"] = {
            "finger_closed_step": {
                "median": float(np.median(finger_closed_step)),
                "mean": float(np.mean(finger_closed_step)),
            },
            "min_dist_step": {
                "median": float(np.median(min_dist_step)),
                "mean": float(np.mean(min_dist_step)),
            },
            "close_before_approach_pct": float(100 * close_before_approach / N),
            "death_zone_frac_mean": float(np.mean(death_zone_frac)),
            "chronic_death_zone_pct": float(100 * chronic_death / N),
        }
        if dist_after_close:
            result["per_world"]["diverge_pct"] = float(100 * diverge_count / len(dist_after_close))
            result["per_world"]["stabilize_pct"] = float(100 * stabilize_count / len(dist_after_close))

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[DIAG] Results saved to {args.output}")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
