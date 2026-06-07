#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect Clamp demonstrations for DAPG — scripted finger close + EE tracking.

Scripted policy:
  - finger_cmd: proportional close toward FINGER_CLOSE_POS
  - EE delta: proportional tracking toward cable segment (compensate displacement)

Records (obs, action) pairs matching NewtonClampEnv format (42D obs, 14D action).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/collect_clamp_demos.py \
        --num-episodes 20 --world-count 4 \
        --output thread_isaac_lab/data/bc_demos/clamp_demos_v1.npz \
        --device cuda:0
"""

import argparse
import math
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np
import torch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "configs"))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "envs"))

from task_config import (
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_STEP_SIZE, T_FINGER,
)
from newton_clamp_env import NewtonClampEnv


# Scripted policy parameters
KP_POS = 0.6       # Proportional gain for EE position tracking
KP_ORI = 0.4       # Proportional gain for EE orientation tracking
FINGER_CLOSE_SPEED = 0.8  # finger_cmd magnitude for closing (in [-1, 1])


def scripted_clamp_action(obs, env):
    """Compute scripted 14D action for one world from 42D obs.

    Strategy:
      - finger_cmd: constant close (capped proportional)
      - EE delta: proportional correction toward cable target (from obs error signals)

    Args:
        obs: [42] observation array.
        env: NewtonClampEnv instance (for action scales).

    Returns:
        [14] action array (normalized to [-1, 1] per dim).
    """
    action = np.zeros(14, dtype=np.float32)

    # obs layout:
    #   [30:33] right ori error axis-angle
    #   [33:36] right pos error (hand - cable)
    #   [36:39] left ori error axis-angle
    #   [39:42] left pos error (hand - cable)
    #   [7]     right finger opening
    #   [15]    left finger opening

    # EE position delta: move toward cable (negate pos error)
    pos_error_r = obs[33:36]  # hand - cable → negative = toward cable
    pos_error_l = obs[39:42]

    # Normalize by POS_ACTION_SCALE to get action in [-1, 1]
    action[0:3] = np.clip(-KP_POS * pos_error_r / env.POS_ACTION_SCALE, -1.0, 1.0)
    action[6:9] = np.clip(-KP_POS * pos_error_l / env.POS_ACTION_SCALE, -1.0, 1.0)

    # EE rotation delta: correct orientation error
    ori_error_r = obs[30:33]
    ori_error_l = obs[36:39]
    action[3:6] = np.clip(-KP_ORI * ori_error_r / env.ROT_ACTION_SCALE, -1.0, 1.0)
    action[9:12] = np.clip(-KP_ORI * ori_error_l / env.ROT_ACTION_SCALE, -1.0, 1.0)

    # Finger commands: close proportionally
    r_finger = obs[7]   # right finger opening (sum of j7+j8)
    l_finger = obs[15]  # left finger opening

    # Close if fingers are still open (above close threshold)
    r_close_target = FINGER_CLOSE_POS * 2  # sum of j7+j8 at close
    l_close_target = FINGER_CLOSE_POS * 2

    if r_finger > r_close_target + 0.001:
        action[12] = FINGER_CLOSE_SPEED  # +1 = close
    else:
        action[12] = 0.0  # hold

    if l_finger > l_close_target + 0.001:
        action[13] = FINGER_CLOSE_SPEED
    else:
        action[13] = 0.0

    return action


def main():
    parser = argparse.ArgumentParser(description="Collect Clamp demos for DAPG")
    parser.add_argument("--num-episodes", type=int, default=20)
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default=os.environ.get("NEWTON_DEVICE", "auto"))
    parser.add_argument("--output", type=str,
                        default=os.path.join(_SCRIPT_DIR, "..", "data", "bc_demos",
                                             "clamp_demos_v1.npz"))
    args = parser.parse_args()

    from gpu_utils import resolve_device
    args.device = resolve_device(args.device)
    os.environ["NEWTON_DEVICE"] = args.device

    print(f"[COLLECT-CLAMP] Device: {args.device}, worlds: {args.world_count}")
    print(f"[COLLECT-CLAMP] Episodes: {args.num_episodes}, output: {args.output}")

    env = NewtonClampEnv(world_count=args.world_count, device=args.device)

    all_obs = []
    all_actions = []
    all_rewards = []
    episode_stats = []

    episodes_collected = 0
    filtered_count = 0
    # Over-collect by 2x to account for filtered failures
    max_batches = 2 * (args.num_episodes + args.world_count - 1) // args.world_count

    for batch in range(max_batches):
        if episodes_collected >= args.num_episodes:
            break
        obs_tensor, _ = env.reset()
        obs_np = obs_tensor.cpu().numpy()

        batch_obs = [[] for _ in range(args.world_count)]
        batch_act = [[] for _ in range(args.world_count)]
        batch_rew = [[] for _ in range(args.world_count)]
        batch_done = [False] * args.world_count

        for step in range(env.MAX_EPISODE_STEPS):
            # Compute scripted actions per world
            actions = np.zeros((args.world_count, 14), dtype=np.float32)
            for w in range(args.world_count):
                if not batch_done[w]:
                    actions[w] = scripted_clamp_action(obs_np[w], env)
                    batch_obs[w].append(obs_np[w].copy())
                    batch_act[w].append(actions[w].copy())

            actions_tensor = torch.tensor(actions, dtype=torch.float32, device=args.device)
            obs_tensor, rewards, dones, infos = env.step(actions_tensor)
            obs_np = obs_tensor.cpu().numpy()
            rewards_np = rewards.cpu().numpy()
            dones_np = dones.cpu().numpy()

            for w in range(args.world_count):
                if not batch_done[w]:
                    batch_rew[w].append(rewards_np[w])
                    if dones_np[w]:
                        batch_done[w] = True

            if all(batch_done):
                break

        # Collect batch results (filter: keep only episodes where fingers closed)
        for w in range(args.world_count):
            if episodes_collected >= args.num_episodes:
                break
            if len(batch_obs[w]) > 0:
                ep_obs = np.array(batch_obs[w])
                ep_act = np.array(batch_act[w])
                ep_rew = np.array(batch_rew[w])
                final_finger_r = float(ep_obs[-1][7])
                final_finger_l = float(ep_obs[-1][15])

                # Quality filter: both fingers must be below T_FINGER threshold
                if final_finger_r > T_FINGER or final_finger_l > T_FINGER:
                    filtered_count += 1
                    continue

                all_obs.append(ep_obs)
                all_actions.append(ep_act)
                all_rewards.append(ep_rew)
                episode_stats.append({
                    "steps": len(batch_obs[w]),
                    "total_reward": float(ep_rew.sum()),
                    "final_finger_r": final_finger_r,
                    "final_finger_l": final_finger_l,
                })
                episodes_collected += 1

        print(f"[COLLECT-CLAMP] Batch {batch+1}/{max_batches}: "
              f"{episodes_collected}/{args.num_episodes} episodes "
              f"(filtered {filtered_count})")

    # Aggregate
    if len(all_obs) == 0:
        print(f"[COLLECT-CLAMP] ERROR: No episodes passed quality filter "
              f"(filtered {filtered_count}). T_FINGER={T_FINGER*1000:.0f}mm")
        sys.exit(1)
    all_obs = np.concatenate(all_obs, axis=0)
    all_actions = np.concatenate(all_actions, axis=0)
    print(f"[COLLECT-CLAMP] Total: {all_obs.shape[0]} transitions, "
          f"obs={all_obs.shape[1]}D, act={all_actions.shape[1]}D "
          f"(filtered {filtered_count} failed episodes)")

    # Summary
    avg_steps = np.mean([s["steps"] for s in episode_stats])
    avg_reward = np.mean([s["total_reward"] for s in episode_stats])
    avg_finger_r = np.mean([s["final_finger_r"] for s in episode_stats])
    avg_finger_l = np.mean([s["final_finger_l"] for s in episode_stats])
    print(f"[COLLECT-CLAMP] Avg steps: {avg_steps:.0f}, avg reward: {avg_reward:.1f}")
    print(f"[COLLECT-CLAMP] Final finger (avg): R={avg_finger_r*1000:.1f}mm, L={avg_finger_l*1000:.1f}mm")

    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    np.savez_compressed(
        args.output,
        obs=all_obs,
        actions=all_actions,
        episode_stats=episode_stats,
    )
    print(f"[COLLECT-CLAMP] Saved to {args.output}")


if __name__ == "__main__":
    main()
