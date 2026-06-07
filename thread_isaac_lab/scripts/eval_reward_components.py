# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate trained ApproachCable policy with per-component reward breakdown.

Runs deterministic rollout across N worlds and reports:
- Per-world C1∧C2 (grasp) achievement rate
- r_lift distribution (actual lift after gate)
- Per-component reward breakdown

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/eval_reward_components.py \
        --checkpoint thread_isaac_lab/data/rl_grasp_cable_A_w1024_20260327_135449/model_29.pt \
        --world-count 256 --device cuda:0
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--world-count", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda:0")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    from rsl_rl.runners import OnPolicyRunner
    from newton_approach_cable_env import NewtonApproachCableEnv, FINGER_OPEN_POS, \
        LIFT_Z, TABLE_HEIGHT, EE_TO_FINGERTIP, FRANKA_NUM_JOINTS, EE_BODY_OFFSET
    import warp as wp

    N = args.world_count
    T = 200  # MAX_EPISODE_STEPS

    print(f"[EVAL-COMP] Checkpoint: {args.checkpoint}")
    print(f"[EVAL-COMP] Worlds: {N}, Device: {args.device}")

    # Create env
    print("[EVAL-COMP] Creating environment...")
    env = NewtonApproachCableEnv(world_count=N, device=args.device)

    # Load policy
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
    log_dir = os.path.join(os.path.dirname(args.checkpoint), "eval_components")
    os.makedirs(log_dir, exist_ok=True)
    runner = OnPolicyRunner(env=env, train_cfg=train_cfg, log_dir=log_dir, device=args.device)
    runner.load(args.checkpoint, load_optimizer=False)
    policy = runner.alg.policy
    policy.eval()

    # Per-world component tracking
    comp_proximity = np.zeros((N, T))
    comp_finger_close = np.zeros((N, T))
    comp_grasp = np.zeros((N, T))
    comp_lift = np.zeros((N, T))
    comp_success = np.zeros((N, T))
    comp_step = np.zeros((N, T))
    per_world_c1c2_ever = np.zeros(N, dtype=bool)
    per_world_max_z_gain = np.zeros(N)
    per_world_min_dist = np.full(N, 999.0)
    per_world_min_finger = np.full(N, 999.0)

    # Monkey-patch reward function to capture components
    _orig_compute = env._compute_rewards_dones_batch
    _step_idx = [0]

    def _instrumented_compute():
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        rewards_np = np.zeros(N, dtype=np.float32)
        dones_np = np.zeros(N, dtype=np.int64)
        timeouts_np = np.zeros(N, dtype=np.int64)
        successes_np = np.zeros(N, dtype=np.float32)
        t = _step_idx[0]

        for w in range(N):
            ws = env._bws[w]
            ee_pos = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            cable_pos = bq[env._cable_bodies[w], :3]
            fingertip_pos = ee_pos.copy()
            fingertip_pos[2] -= EE_TO_FINGERTIP

            dists_to_ee = np.linalg.norm(cable_pos - fingertip_pos, axis=1)
            nearest_idx = np.argmin(dists_to_ee)
            nearest_pos = cable_pos[nearest_idx]

            fk_jq = env._per_world_fk_jq[w]
            finger_opening = fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8]

            dist_tip_cable = float(np.min(dists_to_ee))

            # R_prox (delta-based, must compute before updating prev)
            r_proximity = 0.0
            if dist_tip_cable < env.APPROACH_MAX_DIST:
                delta_prox = env._prev_tip_cable_dist[w] - dist_tip_cable
                r_proximity = env.PROXIMITY_SCALE * max(0.0, delta_prox) / env.APPROACH_MAX_DIST
            env._prev_tip_cable_dist[w] = dist_tip_cable

            # Track min values
            per_world_min_dist[w] = min(per_world_min_dist[w], dist_tip_cable)
            per_world_min_finger[w] = min(per_world_min_finger[w], finger_opening)

            # R1
            r_finger_close = 0.0
            if dist_tip_cable < env.CLOSE_PROXIMITY:
                prev_opening = env._prev_finger_opening[w]
                delta_close = (prev_opening - finger_opening) / (2.0 * FINGER_OPEN_POS)
                r_finger_close = 2.0 * max(0.0, delta_close)
            env._prev_finger_opening[w] = finger_opening

            # R2
            r_grasp = 0.0
            if dist_tip_cable < env.GRASP_DIST_THRESH and finger_opening < env.C1_FINGER_THRESH and not env._grasp_achieved[w]:
                r_grasp = env.GRASP_BONUS
                env._grasp_achieved[w] = True

            # C1, C2
            c1 = finger_opening < env.C1_FINGER_THRESH
            c2 = dist_tip_cable < env.GRASP_DIST_THRESH
            if c1 and c2:
                per_world_c1c2_ever[w] = True

            # R3
            z_nearest = float(nearest_pos[2])
            cable_z_gain = max(0.0, z_nearest - env._cable_z_init[w])
            per_world_max_z_gain[w] = max(per_world_max_z_gain[w], cable_z_gain)
            lift_range = LIFT_Z - TABLE_HEIGHT
            if c1 and c2 and lift_range > 0:
                r_lift = env.LIFT_BONUS_SCALE * cable_z_gain / lift_range
            else:
                r_lift = 0.0

            # Success
            c3 = cable_z_gain > env.C3_LIFT_THRESH
            c4 = abs(z_nearest - fingertip_pos[2]) < env.C4_COMOVEMENT_THRESH
            if c1 and c2 and c3 and c4:
                env._success_sustain_count[w] += 1
            else:
                env._success_sustain_count[w] = 0
            success = env._success_sustain_count[w] >= env.C5_SUSTAIN_STEPS
            r_success = env.SUCCESS_BONUS if success else 0.0

            r_step = env.STEP_PENALTY
            r = r_proximity + r_finger_close + r_grasp + r_lift + r_success + r_step

            timeout = env.episode_length_buf[w].item() >= env.max_episode_length
            done = success or timeout

            rewards_np[w] = r
            dones_np[w] = int(done)
            timeouts_np[w] = int(timeout)
            successes_np[w] = float(success)

            # Store components
            if t < T:
                comp_proximity[w, t] = r_proximity
                comp_finger_close[w, t] = r_finger_close
                comp_grasp[w, t] = r_grasp
                comp_lift[w, t] = r_lift
                comp_success[w, t] = r_success
                comp_step[w, t] = r_step

        _step_idx[0] += 1
        return (
            torch.tensor(rewards_np, dtype=torch.float32, device=env.device),
            torch.tensor(dones_np, dtype=torch.long, device=env.device),
            {
                "observations": {},
                "time_outs": torch.tensor(timeouts_np, dtype=torch.long, device=env.device),
                "log": {"/episode/success": float(np.mean(successes_np))},
            },
        )

    env._compute_rewards_dones_batch = _instrumented_compute

    # Run deterministic rollout
    print("[EVAL-COMP] Running deterministic rollout (200 steps)...")
    obs, _ = env.reset()
    _step_idx[0] = 0

    for step in range(T):
        with torch.no_grad():
            actions = policy.act_inference(obs)
        obs, rewards, dones, extras = env.step(actions)

    # ---- Report ----
    print("\n" + "=" * 70)
    print(f"  PER-COMPONENT REWARD ANALYSIS ({N} worlds, {T} steps)")
    print("=" * 70)

    # Per-episode totals
    ep_proximity = comp_proximity.sum(axis=1)
    ep_finger_close = comp_finger_close.sum(axis=1)
    ep_grasp = comp_grasp.sum(axis=1)
    ep_lift = comp_lift.sum(axis=1)
    ep_success = comp_success.sum(axis=1)
    ep_step = comp_step.sum(axis=1)
    ep_total = ep_proximity + ep_finger_close + ep_grasp + ep_lift + ep_success + ep_step

    print(f"\n--- Episode Return Breakdown (mean ± std across {N} worlds) ---")
    print(f"  r_proximity    : {ep_proximity.mean():+7.3f} ± {ep_proximity.std():.3f}")
    print(f"  r_finger_close : {ep_finger_close.mean():+7.3f} ± {ep_finger_close.std():.3f}")
    print(f"  r_grasp        : {ep_grasp.mean():+7.3f} ± {ep_grasp.std():.3f}")
    print(f"  r_lift         : {ep_lift.mean():+7.3f} ± {ep_lift.std():.3f}")
    print(f"  r_success      : {ep_success.mean():+7.3f} ± {ep_success.std():.3f}")
    print(f"  r_step         : {ep_step.mean():+7.3f} ± {ep_step.std():.3f}")
    print(f"  ─────────────────────────────────────")
    print(f"  TOTAL          : {ep_total.mean():+7.3f} ± {ep_total.std():.3f}")

    # C1∧C2 (grasp) achievement
    n_c1c2 = per_world_c1c2_ever.sum()
    print(f"\n--- C1∧C2 (Grasp) Achievement ---")
    print(f"  Worlds with C1∧C2 ever: {n_c1c2}/{N} ({100*n_c1c2/N:.1f}%)")
    print(f"  Worlds with r_grasp>0 : {(ep_grasp > 0).sum()}/{N} ({100*(ep_grasp > 0).sum()/N:.1f}%)")

    # Proximity stats
    print(f"\n--- Proximity Stats ---")
    print(f"  Min fingertip-cable dist per world:")
    print(f"    mean={per_world_min_dist.mean()*1000:.2f}mm  median={np.median(per_world_min_dist)*1000:.2f}mm")
    print(f"    <30mm (CLOSE_PROX): {(per_world_min_dist < 0.03).sum()}/{N}")
    print(f"    <5mm  (GRASP_DIST): {(per_world_min_dist < 0.005).sum()}/{N}")
    print(f"  Min finger opening per world:")
    print(f"    mean={per_world_min_finger.mean()*1000:.2f}mm  median={np.median(per_world_min_finger)*1000:.2f}mm")
    print(f"    <12mm (C1_THRESH) : {(per_world_min_finger < 0.012).sum()}/{N}")

    # Lift stats (only for C1∧C2 worlds)
    print(f"\n--- Lift Stats (gated by C1∧C2) ---")
    c1c2_mask = per_world_c1c2_ever
    if c1c2_mask.sum() > 0:
        z_gains = per_world_max_z_gain[c1c2_mask]
        print(f"  Max cable z_gain (C1∧C2 worlds only, n={c1c2_mask.sum()}):")
        print(f"    mean={z_gains.mean()*1000:.2f}mm  max={z_gains.max()*1000:.2f}mm")
        print(f"    >10mm (C3 thresh): {(z_gains > 0.010).sum()}/{c1c2_mask.sum()}")
        print(f"    >5mm            : {(z_gains > 0.005).sum()}/{c1c2_mask.sum()}")
        print(f"    >1mm            : {(z_gains > 0.001).sum()}/{c1c2_mask.sum()}")
        # Lift reward distribution
        lifts_c1c2 = ep_lift[c1c2_mask]
        print(f"  Episode r_lift (C1∧C2 worlds):")
        print(f"    mean={lifts_c1c2.mean():.3f}  max={lifts_c1c2.max():.3f}")
    else:
        print(f"  No worlds achieved C1∧C2 — no gated lift data")
        # Still show overall z_gain
        print(f"  Max cable z_gain (all worlds):")
        print(f"    mean={per_world_max_z_gain.mean()*1000:.2f}mm  max={per_world_max_z_gain.max()*1000:.2f}mm")

    # Percentile distribution of total return
    print(f"\n--- Episode Return Distribution ---")
    pcts = [0, 10, 25, 50, 75, 90, 100]
    vals = np.percentile(ep_total, pcts)
    for p, v in zip(pcts, vals):
        print(f"  p{p:3d}: {v:+7.3f}")

    if hasattr(env, "close"):
        env.close()

    print("\n[EVAL-COMP] Done.")


if __name__ == "__main__":
    main()
