#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect precision AerialRegrasp demonstrations for DAPG (1mm action scale).

Uses the standard AerialRegrasp env with POS_ACTION_SCALE=0.001 (1mm).
Scripted proportional controller: action = clip(-error / scale, -1, 1).
Starts from default P0 cache (cable held in air) or custom precondition.

Obs layout is identical to ApproachCable (42D), so the same proportional
controller logic applies:
  obs[30:33] = ori_error_aa_r (axis-angle)
  obs[33:36] = pos_error_r (clamp_r - seg_pos)
  obs[36:39] = ori_error_aa_l
  obs[39:42] = pos_error_l

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    python thread_isaac_lab/scripts/collect_precision_regrasp_demos.py \\
        --num-episodes 80 --world-count 4 \\
        --output thread_isaac_lab/data/bc_demos/precision_regrasp_demos_v1.npz \\
        --device cuda:2
"""

import argparse
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import torch

# Ensure envs/ is importable
_envs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "envs")
if _envs_dir not in sys.path:
    sys.path.insert(0, _envs_dir)


def main():
    parser = argparse.ArgumentParser(description="Collect precision AerialRegrasp demos (1mm action scale)")
    parser.add_argument("--num-episodes", type=int, default=80)
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default="cuda:2")
    parser.add_argument("--output", type=str,
                        default="thread_isaac_lab/data/bc_demos/precision_regrasp_demos_v1.npz")
    parser.add_argument("--pos-action-scale", type=float, default=0.001,
                        help="POS_ACTION_SCALE [m] (default: 0.001 = 1mm)")
    parser.add_argument("--rot-action-scale", type=float, default=0.003,
                        help="ROT_ACTION_SCALE [rad] (default: 0.003 = 0.17deg)")
    parser.add_argument("--terminal-steps", type=int, default=50,
                        help="Max episode length (default: 50)")
    parser.add_argument("--pos-gain", type=float, default=0.6,
                        help="Proportional gain for position (scales error before clipping)")
    parser.add_argument("--ori-gain", type=float, default=0.4,
                        help="Proportional gain for orientation")
    parser.add_argument("--precondition-cache", type=str, default=None,
                        help="Path to custom precondition cache (default: standard P0)")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    from newton_aerial_regrasp_env import NewtonAerialRegraspEnv

    # Configure env for precision descent
    NewtonAerialRegraspEnv.POS_ACTION_SCALE = args.pos_action_scale
    NewtonAerialRegraspEnv.ROT_ACTION_SCALE = args.rot_action_scale
    NewtonAerialRegraspEnv.MAX_EPISODE_STEPS = args.terminal_steps
    if args.precondition_cache:
        NewtonAerialRegraspEnv.PRECONDITION_CACHE_OVERRIDE = os.path.abspath(args.precondition_cache)

    print(f"[PrecisionRegrasp] Config: POS_SCALE={args.pos_action_scale*1000:.1f}mm, "
          f"ROT_SCALE={args.rot_action_scale:.3f}rad, "
          f"episodes={args.num_episodes}, worlds={args.world_count}, "
          f"terminal={args.terminal_steps}")

    env = NewtonAerialRegraspEnv(world_count=args.world_count, device=args.device, freeze_left_anchor=False)

    all_obs = []
    all_actions = []
    success_count = 0
    total_episodes = 0
    batches = (args.num_episodes + args.world_count - 1) // args.world_count

    t0 = time.perf_counter()

    for batch_idx in range(batches):
        obs, _ = env.reset()  # obs: [N, 42] tensor

        for step in range(args.terminal_steps):
            obs_np = obs.cpu().numpy()  # [N, 42]

            # Proportional controller: action = gain * (-error / action_scale)
            # obs[30:33] = ori_error_aa_r (axis-angle from hand to grasp target)
            # obs[33:36] = pos_error_r = clamp_r_pos - seg_pos
            # obs[36:39] = ori_error_aa_l
            # obs[39:42] = pos_error_l

            actions = np.zeros((args.world_count, 12), dtype=np.float32)

            for w in range(args.world_count):
                # Right arm: position
                pos_err_r = obs_np[w, 33:36]
                pos_act_r = -args.pos_gain * pos_err_r / args.pos_action_scale
                actions[w, 0:3] = np.clip(pos_act_r, -1.0, 1.0)

                # Right arm: rotation
                ori_err_r = obs_np[w, 30:33]
                ori_act_r = -args.ori_gain * ori_err_r / args.rot_action_scale
                actions[w, 3:6] = np.clip(ori_act_r, -1.0, 1.0)

                # Left arm: position
                pos_err_l = obs_np[w, 39:42]
                pos_act_l = -args.pos_gain * pos_err_l / args.pos_action_scale
                actions[w, 6:9] = np.clip(pos_act_l, -1.0, 1.0)

                # Left arm: rotation
                ori_err_l = obs_np[w, 36:39]
                ori_act_l = -args.ori_gain * ori_err_l / args.rot_action_scale
                actions[w, 9:12] = np.clip(ori_act_l, -1.0, 1.0)

            # Record transitions
            all_obs.append(obs_np.copy())
            all_actions.append(actions.copy())

            # Step env
            actions_tensor = torch.tensor(actions, dtype=torch.float32, device=args.device)
            obs, rewards, dones, extras = env.step(actions_tensor)

            # Diagnostic: step-level progress (first batch, world 0)
            if batch_idx == 0 and step < 20 or (step + 1) % 25 == 0:
                obs_diag = obs.cpu().numpy()
                pe = np.linalg.norm(obs_diag[0, 33:36]) * 1000
                oe = np.linalg.norm(obs_diag[0, 30:33])
                act_mag = np.linalg.norm(actions[0, 0:3])
                d = int(dones[0].item()) if hasattr(dones[0], 'item') else int(dones[0])
                print(f"    step {step:3d}: pos_err={pe:6.1f}mm ori_err={oe:.3f}rad "
                      f"|act_pos|={act_mag:.2f} done={d}")

        total_episodes += args.world_count

        # Progress
        ep_done = min((batch_idx + 1) * args.world_count, args.num_episodes)
        elapsed = time.perf_counter() - t0

        # Check final distances for this batch
        final_obs = obs.cpu().numpy()
        pos_errs = [np.linalg.norm(final_obs[w, 33:36]) * 1000 for w in range(args.world_count)]
        ori_errs = [np.linalg.norm(final_obs[w, 30:33]) for w in range(args.world_count)]
        print(f"  Batch {batch_idx+1}/{batches}: "
              f"pos_err=[{min(pos_errs):.1f}, {max(pos_errs):.1f}]mm, "
              f"ori_err=[{min(ori_errs):.3f}, {max(ori_errs):.3f}]rad, "
              f"ep={ep_done}/{args.num_episodes}, {elapsed:.0f}s")

    # Stack and save
    obs_all = np.concatenate(all_obs, axis=0)      # [total_steps * N, 42]
    act_all = np.concatenate(all_actions, axis=0)   # [total_steps * N, 12]

    total_transitions = obs_all.shape[0]

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    np.savez_compressed(
        args.output,
        obs=obs_all.astype(np.float32),
        actions=act_all.astype(np.float32),
    )

    elapsed = time.perf_counter() - t0
    print(f"\n[PrecisionRegrasp] Done in {elapsed:.1f}s")
    print(f"  Episodes: {total_episodes}, Transitions: {total_transitions}")
    print(f"  obs shape: {obs_all.shape}, actions shape: {act_all.shape}")
    print(f"  Saved to: {args.output}")


if __name__ == "__main__":
    main()
