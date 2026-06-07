# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""AC explosion mechanism diagnostic — per-step trajectory capture.

Investigation tool for CC-AC-VBD-Physics-Investigation (2026-04-27).
Disambiguates init shock (CC1 PROPOSE) vs contact spike (CC6 NHA) by
capturing per-step cable body_q/body_qd, finger position, dist_pos for
failure trajectory analysis.

Outputs NPZ trajectory + console summary classifying NaN onset, cable
axial velocity magnitude at step 0, finger-cable contact onset step.

Usage:
    source ~/env_isaaclab6/bin/activate
    PYTHONPATH=/home/rlrk/IsaacLab CUDA_VISIBLE_DEVICES=0 \
        python thread_isaac_lab/scripts/diagnose_ac_explosion_trajectory.py \
            --checkpoint logs/rl_approach_cable_A_v30_sweep_p025_a07/model_best.pt \
            --pos-action-scale 0.025 --episodes 10 --seeds 5
"""

import argparse
import json
import os
import sys

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_cfg_dir = os.path.join(_script_dir, "..", "configs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _cfg_dir)
sys.path.insert(0, _script_dir)


def main():
    parser = argparse.ArgumentParser(description="AC explosion trajectory diagnostic")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--pos-action-scale", type=float, default=0.025,
                        help="Override env POS_ACTION_SCALE to match training (default: 0.025 = p025 winner)")
    parser.add_argument("--episodes", type=int, default=10,
                        help="Episodes per seed")
    parser.add_argument("--seeds", type=int, default=5,
                        help="Number of distinct seeds")
    parser.add_argument("--randomize-cable-xy", action="store_true", default=True,
                        help="Match deploy distribution (default: True)")
    parser.add_argument("--no-randomize-cable-xy", dest="randomize_cable_xy",
                        action="store_false")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output", type=str, default="/tmp/ac_explosion_trajectory.npz")
    parser.add_argument("--max-steps", type=int, default=15,
                        help="Stop ep at this many RL steps (failure typically <10)")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    from newton_approach_cable_env import NewtonApproachCableEnv
    from rsl_rl.runners import OnPolicyRunner

    # Override class-level POS_ACTION_SCALE to match p025 training
    NewtonApproachCableEnv.POS_ACTION_SCALE = args.pos_action_scale
    print(f"[DIAG] POS_ACTION_SCALE overridden to {args.pos_action_scale} (p025 training match)")

    # Create 1-world env
    print(f"[DIAG] Creating 1-world env on {args.device}...")
    env = NewtonApproachCableEnv(world_count=1, device=args.device)
    env.set_cable_xy_randomize(args.randomize_cable_xy)
    print(f"[DIAG] Cable XY DR: {'ENABLED' if args.randomize_cable_xy else 'disabled (sanity)'}")

    # Build runner + load checkpoint (config matches eval_approach_cable.py)
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
    log_dir = os.path.dirname(args.output) or "/tmp"
    runner = OnPolicyRunner(env=env, train_cfg=train_cfg, log_dir=log_dir, device=args.device)
    print(f"[DIAG] Loading checkpoint: {args.checkpoint}")
    runner.load(args.checkpoint, load_optimizer=False)
    policy = runner.alg.policy
    policy.eval()

    # Cable + finger body indices for world 0 (only 1 world)
    cable_indices = list(env._cable_bodies[0])  # 40 global indices
    bws_0 = env._bws[0]
    # Finger bodies: left arm body 7,8 (start=bws_0+0+7,8); right arm body 7,8 (bws_0+9+7,8)
    finger_l_indices = [bws_0 + 7, bws_0 + 8]
    finger_r_indices = [bws_0 + 9 + 7, bws_0 + 9 + 8]
    print(f"[DIAG] Cable bodies: {len(cable_indices)} segments, indices {cable_indices[0]}-{cable_indices[-1]}")
    print(f"[DIAG] Finger L: {finger_l_indices}, Finger R: {finger_r_indices}")

    # Per-trial trajectory data
    trials = []

    total_trials = args.seeds * args.episodes
    trial_idx = 0
    for seed in range(args.seeds):
        np.random.seed(seed + 42)
        torch.manual_seed(seed + 42)

        for ep in range(args.episodes):
            trial_idx += 1
            obs, _ = env.reset()
            T = args.max_steps  # max steps to capture

            # Pre-allocate arrays
            cable_pos = np.full((T, 40, 3), np.nan, dtype=np.float32)
            cable_vel = np.full((T, 40, 3), np.nan, dtype=np.float32)
            finger_l_pos = np.full((T, 2, 3), np.nan, dtype=np.float32)
            finger_r_pos = np.full((T, 2, 3), np.nan, dtype=np.float32)
            dist_pos_r = np.full(T, np.nan, dtype=np.float32)
            dist_pos_l_arr = np.full(T, np.nan, dtype=np.float32)
            actions_arr = np.full((T, 12), np.nan, dtype=np.float32)
            explosion_flag = np.zeros(T, dtype=bool)
            step_done = -1
            step_reason = "max_steps"

            for step in range(T):
                # Capture state BEFORE applying action (post-reset for step 0,
                # post-previous-step for step > 0)
                wp.synchronize()
                bq = env._state_0.body_q.numpy()
                bqd = env._state_0.body_qd.numpy()

                cable_pos[step] = bq[cable_indices, :3]
                cable_vel[step] = bqd[cable_indices, 3:6]  # linear velocity (6dof: ang3+lin3)
                finger_l_pos[step, 0] = bq[finger_l_indices[0], :3]
                finger_l_pos[step, 1] = bq[finger_l_indices[1], :3]
                finger_r_pos[step, 0] = bq[finger_r_indices[0], :3]
                finger_r_pos[step, 1] = bq[finger_r_indices[1], :3]

                # Action via deterministic policy
                with torch.no_grad():
                    actions = policy.act_inference(obs)
                if actions.dim() == 1:
                    actions = actions.unsqueeze(0)
                actions_arr[step] = actions[0].cpu().numpy()

                obs, rewards, dones, extras = env.step(actions)

                # Per-world dist (right arm via log_per_world)
                lpw = extras.get("log_per_world", {})
                if "dist_pos" in lpw:
                    dp = np.asarray(lpw["dist_pos"])
                    dist_pos_r[step] = float(dp[0]) if dp.size > 0 else np.nan
                if "explosion" in lpw:
                    exp_arr = np.asarray(lpw["explosion"])
                    explosion_flag[step] = bool(exp_arr[0]) if exp_arr.size > 0 else False

                # Compute left dist manually: nearest cable seg to left clamp
                # Left clamp = compute from finger L positions (avg) - 35mm above (clamp pos)
                # Simplification: use min dist from finger_l avg pos to any cable segment
                fl_avg = finger_l_pos[step].mean(axis=0)
                cable_seg_pos = cable_pos[step]
                if not np.any(np.isnan(cable_seg_pos)):
                    diffs = cable_seg_pos - fl_avg[None, :]
                    dists = np.linalg.norm(diffs, axis=1)
                    dist_pos_l_arr[step] = float(np.min(dists))

                if dones.any():
                    step_done = step
                    if explosion_flag[step]:
                        step_reason = "explosion"
                    else:
                        # Check success in extras
                        success_arr = lpw.get("success", np.zeros(1))
                        if np.asarray(success_arr).any():
                            step_reason = "success"
                        else:
                            step_reason = "timeout_or_other"
                    break

            # Trial summary
            # First non-NaN cable axial vel magnitude (step 0 = init shock indicator)
            init_cable_vel_mag = np.linalg.norm(cable_vel[0], axis=1).mean() if not np.isnan(cable_vel[0]).all() else np.nan
            # Cable vel at step before explosion
            if step_done >= 0 and step_reason == "explosion":
                pre_exp_cable_vel_mag = np.linalg.norm(cable_vel[step_done], axis=1).mean() if not np.isnan(cable_vel[step_done]).all() else np.nan
            else:
                pre_exp_cable_vel_mag = np.nan

            # Cable centroid Z displacement step 0 → step 1 (init relaxation indicator)
            if T >= 2:
                cable_z_step0 = cable_pos[0, :, 2].mean() if not np.isnan(cable_pos[0]).all() else np.nan
                cable_z_step1 = cable_pos[1, :, 2].mean() if not np.isnan(cable_pos[1]).all() else np.nan
                cable_z_drop_01 = cable_z_step0 - cable_z_step1
            else:
                cable_z_drop_01 = np.nan

            # First step where finger_l Z below cable centroid Z (contact onset proxy)
            finger_contact_step = -1
            for s in range(min(step_done + 1 if step_done >= 0 else T, T)):
                fl_z = finger_l_pos[s].mean(axis=0)[2]
                cable_z = cable_pos[s, :, 2].mean() if not np.isnan(cable_pos[s]).all() else np.nan
                if not np.isnan(fl_z) and not np.isnan(cable_z):
                    if fl_z < cable_z + 0.020:  # within 20mm above cable
                        finger_contact_step = s
                        break

            # NaN onset detection
            nan_step = -1
            nan_source = "none"
            for s in range(min(step_done + 2 if step_done >= 0 else T, T)):
                if np.any(np.isnan(cable_pos[s])):
                    nan_step = s
                    nan_source = "cable"
                    break
                if np.any(np.isnan(finger_l_pos[s])) or np.any(np.isnan(finger_r_pos[s])):
                    nan_step = s
                    nan_source = "finger"
                    break

            trial_data = {
                "seed": seed,
                "episode": ep,
                "step_done": step_done,
                "step_reason": step_reason,
                "init_cable_vel_mag_mean": float(init_cable_vel_mag),
                "pre_explosion_cable_vel_mag_mean": float(pre_exp_cable_vel_mag),
                "cable_z_drop_step0_to_step1": float(cable_z_drop_01),
                "finger_contact_onset_step": int(finger_contact_step),
                "nan_step": int(nan_step),
                "nan_source": nan_source,
            }
            trials.append(trial_data)

            print(f"[DIAG {trial_idx}/{total_trials}] seed={seed} ep={ep} done@step{step_done} ({step_reason}) "
                  f"init_v={init_cable_vel_mag:.4f} pre_exp_v={pre_exp_cable_vel_mag:.4f} "
                  f"contact_step={finger_contact_step} nan_step={nan_step}({nan_source})")

            # Save trajectory NPZ for this trial only if explosion (capture full traj)
            if step_reason == "explosion":
                traj_path = args.output.replace(".npz", f"_seed{seed}_ep{ep}.npz")
                np.savez_compressed(
                    traj_path,
                    cable_pos=cable_pos,
                    cable_vel=cable_vel,
                    finger_l_pos=finger_l_pos,
                    finger_r_pos=finger_r_pos,
                    dist_pos_r=dist_pos_r,
                    dist_pos_l=dist_pos_l_arr,
                    actions=actions_arr,
                    explosion_flag=explosion_flag,
                    step_done=step_done,
                )

    # Summary
    print("\n[DIAG] === Summary ===")
    n_total = len(trials)
    n_explosion = sum(1 for t in trials if t["step_reason"] == "explosion")
    n_success = sum(1 for t in trials if t["step_reason"] == "success")
    n_timeout = sum(1 for t in trials if t["step_reason"] not in ("explosion", "success"))
    print(f"  Total trials: {n_total}")
    print(f"  Explosion: {n_explosion} ({100*n_explosion/n_total:.1f}%)")
    print(f"  Success: {n_success} ({100*n_success/n_total:.1f}%)")
    print(f"  Other (timeout/maxsteps): {n_timeout}")

    if n_explosion > 0:
        exp_trials = [t for t in trials if t["step_reason"] == "explosion"]
        succ_trials = [t for t in trials if t["step_reason"] == "success"]

        # Average init cable vel magnitude (init shock signal)
        exp_init_v = np.array([t["init_cable_vel_mag_mean"] for t in exp_trials])
        succ_init_v = np.array([t["init_cable_vel_mag_mean"] for t in succ_trials]) if succ_trials else np.array([])
        print(f"\n  Init cable vel magnitude (m/s, mean over 40 segs):")
        print(f"    Explosion eps: mean={np.nanmean(exp_init_v):.4f} ± {np.nanstd(exp_init_v):.4f}")
        if len(succ_init_v) > 0:
            print(f"    Success eps:   mean={np.nanmean(succ_init_v):.4f} ± {np.nanstd(succ_init_v):.4f}")

        # Step at which explosion happened
        exp_steps = np.array([t["step_done"] for t in exp_trials])
        print(f"\n  Explosion step distribution:")
        for s in range(0, 11):
            cnt = np.sum(exp_steps == s)
            if cnt > 0:
                print(f"    step {s}: {cnt} eps")

        # Finger contact onset step
        fc_steps = np.array([t["finger_contact_onset_step"] for t in exp_trials])
        fc_valid = fc_steps[fc_steps >= 0]
        if len(fc_valid) > 0:
            print(f"\n  Finger contact onset step (explosion eps):")
            print(f"    mean={np.mean(fc_valid):.2f}, min={np.min(fc_valid)}, max={np.max(fc_valid)}")

        # NaN source distribution
        nan_sources = [t["nan_source"] for t in exp_trials]
        unique_sources = set(nan_sources)
        print(f"\n  NaN source distribution:")
        for src in unique_sources:
            cnt = nan_sources.count(src)
            print(f"    {src}: {cnt} eps ({100*cnt/len(exp_trials):.1f}%)")

        # Pre-explosion vs init cable vel comparison
        pre_exp_v = np.array([t["pre_explosion_cable_vel_mag_mean"] for t in exp_trials])
        print(f"\n  Pre-explosion cable vel magnitude (m/s):")
        print(f"    mean={np.nanmean(pre_exp_v):.4f} ± {np.nanstd(pre_exp_v):.4f}")

    # Save summary JSON
    summary_path = args.output.replace(".npz", "_summary.json")
    with open(summary_path, "w") as f:
        json.dump({"trials": trials, "n_total": n_total, "n_explosion": n_explosion,
                   "n_success": n_success, "n_timeout": n_timeout},
                  f, indent=2, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x))
    print(f"\n[DIAG] Summary saved: {summary_path}")
    print(f"[DIAG] Per-explosion-trial NPZ: {args.output.replace('.npz', '_seedX_epY.npz')}")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
