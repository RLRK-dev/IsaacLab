#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect Grip (Clamp/Unclamp) demonstrations -- scripted policy.

Clamp mode:  finger close + EE tracking (same as collect_clamp_demos.py)
Unclamp mode: finger open + EE tracking (proportional toward groove center)

Records (obs, action) pairs matching NewtonGripEnv format (42D obs, 14D action).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/collect_grip_demos.py \
        --mode clamp --num-episodes 20 --world-count 4 --device cuda:0
    python thread_isaac_lab/scripts/collect_grip_demos.py \
        --mode unclamp --num-episodes 20 --world-count 4 --device cuda:0
"""

import argparse
import json
import os
import sys

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np
import torch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "configs"))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "envs"))

from newton_grip_env import NewtonGripEnv
from task_config import (
    FINGER_CLOSE_POS,
    FINGER_OPEN_POS,
    T_FINGER,
)

# Scripted policy parameters
# Clamp: near-cable P0 (dist≈5mm) → gentle tracking to avoid IK orientation flip.
# Ori tracking disabled: cable tangent changes during finger close cause IK instability.
KP_POS = 0.1
KP_ORI = 0.0
FINGER_CLOSE_SPEED = 0.8
FINGER_OPEN_SPEED = 0.8


def scripted_clamp_action(obs, env):
    """14D scripted action for clamp: close fingers + track cable."""
    action = np.zeros(14, dtype=np.float32)

    pos_error_r = obs[33:36]
    pos_error_l = obs[39:42]
    action[0:3] = np.clip(-KP_POS * pos_error_r / env.POS_ACTION_SCALE, -1.0, 1.0)
    action[6:9] = np.clip(-KP_POS * pos_error_l / env.POS_ACTION_SCALE, -1.0, 1.0)

    ori_error_r = obs[30:33]
    ori_error_l = obs[36:39]
    action[3:6] = np.clip(-KP_ORI * ori_error_r / env.ROT_ACTION_SCALE, -1.0, 1.0)
    action[9:12] = np.clip(-KP_ORI * ori_error_l / env.ROT_ACTION_SCALE, -1.0, 1.0)

    r_finger = obs[7]
    l_finger = obs[15]
    r_close_target = FINGER_CLOSE_POS * 2
    l_close_target = FINGER_CLOSE_POS * 2

    action[12] = FINGER_CLOSE_SPEED if r_finger > r_close_target + 0.001 else 0.0
    action[13] = FINGER_CLOSE_SPEED if l_finger > l_close_target + 0.001 else 0.0

    return action


def scripted_unclamp_action(obs, env):
    """14D scripted action for unclamp: open left finger + track groove."""
    action = np.zeros(14, dtype=np.float32)

    # Left arm: track groove center
    pos_error_l = obs[39:42]
    action[6:9] = np.clip(-KP_POS * pos_error_l / env.POS_ACTION_SCALE, -1.0, 1.0)

    ori_error_l = obs[36:39]
    action[9:12] = np.clip(-KP_ORI * ori_error_l / env.ROT_ACTION_SCALE, -1.0, 1.0)

    # Right arm: small tracking corrections only
    pos_error_r = obs[33:36]
    action[0:3] = np.clip(-0.3 * pos_error_r / env.POS_ACTION_SCALE, -0.5, 0.5)

    # Left finger: open (-1 = open)
    l_finger = obs[15]
    full_open_sum = 2 * FINGER_OPEN_POS
    action[13] = -FINGER_OPEN_SPEED if l_finger < full_open_sum - 0.002 else 0.0

    # Right finger: hold open
    action[12] = 0.0

    return action


def main():
    parser = argparse.ArgumentParser(description="Collect Grip demos")
    parser.add_argument("--mode", type=str, required=True, choices=["clamp", "unclamp"])
    parser.add_argument("--num-episodes", type=int, default=20)
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default=os.environ.get("NEWTON_DEVICE", "auto"))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.join(_SCRIPT_DIR, "..", "data", "bc_demos", f"grip_{args.mode}_demos_v1.npz")

    # F-6 (v3.1 + v3.2 C3): validate output path BEFORE env build / collection
    # run AND before `resolve_device` (which probes GPUs). Ordered FIRST after
    # parse_args so `--output foo.txt` fails in <1 ms, not after seconds of
    # device probing.
    if not args.output.endswith(".npz"):
        parser.error(f"--output must end in .npz, got {args.output!r}")
    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    from gpu_utils import resolve_device

    args.device = resolve_device(args.device)
    os.environ["NEWTON_DEVICE"] = args.device

    print(f"[COLLECT-GRIP] Mode: {args.mode}, device: {args.device}, worlds: {args.world_count}")
    print(f"[COLLECT-GRIP] Episodes: {args.num_episodes}, output: {args.output}")

    env = NewtonGripEnv(world_count=args.world_count, device=args.device, mode=args.mode, dual_arm=True)

    scripted_fn = scripted_clamp_action if args.mode == "clamp" else scripted_unclamp_action

    all_obs = []
    all_actions = []
    all_rewards = []
    episode_stats = []

    episodes_collected = 0
    filtered_count = 0
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

        for step in range(env.max_episode_length):
            actions = np.zeros((args.world_count, 14), dtype=np.float32)
            for w in range(args.world_count):
                if not batch_done[w]:
                    actions[w] = scripted_fn(obs_np[w], env)
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

        # Quality filter
        for w in range(args.world_count):
            if episodes_collected >= args.num_episodes:
                break
            if len(batch_obs[w]) > 0:
                ep_obs = np.array(batch_obs[w])
                ep_act = np.array(batch_act[w])
                ep_rew = np.array(batch_rew[w])

                if args.mode == "clamp":
                    final_finger_r = float(ep_obs[-1][7])
                    final_finger_l = float(ep_obs[-1][15])
                    if final_finger_r > T_FINGER or final_finger_l > T_FINGER:
                        filtered_count += 1
                        continue
                else:
                    final_finger_l = float(ep_obs[-1][15])
                    if final_finger_l < 2 * (FINGER_OPEN_POS - 0.005):
                        filtered_count += 1
                        continue

                all_obs.append(ep_obs)
                all_actions.append(ep_act)
                all_rewards.append(ep_rew)
                episode_stats.append(
                    {
                        "steps": len(batch_obs[w]),
                        "total_reward": float(ep_rew.sum()),
                    }
                )
                episodes_collected += 1

        print(
            f"[COLLECT-GRIP] Batch {batch + 1}/{max_batches}: "
            f"{episodes_collected}/{args.num_episodes} episodes "
            f"(filtered {filtered_count})"
        )

    if len(all_obs) == 0:
        print(f"[COLLECT-GRIP] ERROR: No episodes passed quality filter (filtered {filtered_count})")
        sys.exit(1)

    all_obs = np.concatenate(all_obs, axis=0)
    all_actions = np.concatenate(all_actions, axis=0)
    print(
        f"[COLLECT-GRIP] Total: {all_obs.shape[0]} transitions, "
        f"obs={all_obs.shape[1]}D, act={all_actions.shape[1]}D "
        f"(filtered {filtered_count} failed episodes)"
    )

    avg_steps = np.mean([s["steps"] for s in episode_stats])
    avg_reward = np.mean([s["total_reward"] for s in episode_stats])
    print(f"[COLLECT-GRIP] Avg steps: {avg_steps:.0f}, avg reward: {avg_reward:.1f}")

    # F-6 validation moved to post-parse_args (v3.1). Output dir exists by now.
    episode_lengths = np.array([s["steps"] for s in episode_stats], dtype=np.int32)
    # F7: drop episode_stats from npz (was a pickled list-of-dict that forced
    # allow_pickle=True on every reader — an RCE surface). Write to a JSON
    # sidecar next to the npz so downstream readers can still use it.
    np.savez_compressed(
        args.output,
        obs=all_obs,
        actions=all_actions,
        episode_lengths=episode_lengths,
    )
    stats_path = os.path.splitext(args.output)[0] + "_stats.json"

    def _jsonable(v):
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, np.ndarray):
            return v.tolist()
        return v

    stats_jsonable = [
        {k: _jsonable(v) for k, v in s.items()} for s in episode_stats
    ]
    with open(stats_path, "w") as f:
        json.dump(stats_jsonable, f, indent=2)
    print(f"[COLLECT-GRIP] Saved to {args.output}")
    print(f"[COLLECT-GRIP] Stats sidecar: {stats_path}")


if __name__ == "__main__":
    main()
