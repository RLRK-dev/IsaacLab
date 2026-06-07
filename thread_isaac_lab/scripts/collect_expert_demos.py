# Copyright (c) 2024, THREAD Project
# SPDX-License-Identifier: BSD-3-Clause

"""Collect expert demonstrations for BC pretraining.

Runs the scripted expert policy in the multi-world RL environment and records
(obs, action) pairs. The expert action is a geometric controller that moves
the right arm EE toward the clip groove center.

Usage:
    source ~/env_isaaclab6/bin/activate
    NEWTON_DEVICE=cuda:0 python thread_isaac_lab/scripts/collect_expert_demos.py \
        --world-count 32 --num-episodes 50 --device cuda:0
"""

import argparse
import os
import sys
import time

import numpy as np
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_script_dir, "..", "envs"))
sys.path.insert(0, os.path.join(_script_dir, "..", "configs"))

from task_config import PUSH_Z, LIFT_Z, GRASP_Z


def expert_action_aerial_regrasp(obs, action_scale=0.005):
    """Compute expert action for AerialRegrasp.

    Strategy: move right EE toward the nearest free cable body position.
    AerialRegrasp obs layout:
        [0:3] right EE, [3:6] nearest cable body, [6:9] left EE,
        [9:11] ideal grasp XY, [11] ideal grasp Z (GRASP_Z).

    Args:
        obs: [N, 12] observation tensor.
        action_scale: env ACTION_SCALE (meters per unit action).

    Returns:
        [N, 3] action tensor.
    """
    obs_np = obs.cpu().numpy()
    N = obs_np.shape[0]
    actions = np.zeros((N, 3), dtype=np.float32)

    for i in range(N):
        ee_xyz = obs_np[i, 0:3]           # right EE position
        nearest_cable = obs_np[i, 3:6]     # nearest free cable body
        grasp_z = obs_np[i, 11]            # target Z (GRASP_Z)

        # Target: nearest cable body position, at grasp Z height
        target = np.array([nearest_cable[0], nearest_cable[1], grasp_z])

        delta = target - ee_xyz
        dist = np.linalg.norm(delta)
        if dist > action_scale:
            delta = delta / dist * action_scale

        actions[i] = delta / action_scale

    return torch.tensor(actions, dtype=torch.float32)


def expert_action_insert_clip(obs, action_scale=0.005):
    """Compute expert action for InsertIntoClip.

    Strategy: move right EE toward the nearest cable body's XY, then push
    down to clip Z. This mimics the scripted P4 push.

    Args:
        obs: [N, 12] observation tensor.
        action_scale: env ACTION_SCALE (meters per unit action).

    Returns:
        [N, 3] action tensor (in action space, i.e., divided by action_scale).
    """
    obs_np = obs.cpu().numpy()
    N = obs_np.shape[0]
    actions = np.zeros((N, 3), dtype=np.float32)

    for i in range(N):
        ee_xyz = obs_np[i, 0:3]        # right EE position
        clip_xy = obs_np[i, 6:8]        # clip groove center XY
        clip_z = obs_np[i, 10]           # clip Z

        # Target: clip groove center at clip Z height
        target = np.array([clip_xy[0], clip_xy[1], clip_z])

        # Delta from current EE to target
        delta = target - ee_xyz

        # Clamp magnitude to action_scale (one step at a time)
        dist = np.linalg.norm(delta)
        if dist > action_scale:
            delta = delta / dist * action_scale

        # Convert to action space (divide by action_scale)
        actions[i] = delta / action_scale

    return torch.tensor(actions, dtype=torch.float32)


def collect_demos(env, expert_fn, num_episodes, max_steps=200, device="cuda:0"):
    """Collect expert demonstrations.

    Args:
        env: VecEnv instance.
        expert_fn: function(obs) -> actions.
        num_episodes: total episodes to collect (across all worlds).
        max_steps: max steps per episode.
        device: torch device.

    Returns:
        dict with 'obs' [T, obs_dim] and 'actions' [T, act_dim] numpy arrays.
    """
    all_obs = []
    all_actions = []
    episodes_collected = 0
    world_count = env.num_envs

    obs, _ = env.reset()

    print(f"[COLLECT] Starting: {num_episodes} episodes, {world_count} worlds")

    while episodes_collected < num_episodes:
        obs_before_ep = obs[0, :3].cpu().numpy().copy()
        for step in range(max_steps):
            # Expert computes action from observation
            actions = expert_fn(obs)

            # Record (obs, action) pair
            all_obs.append(obs.cpu().numpy().copy())
            all_actions.append(actions.cpu().numpy().copy())

            # Step environment
            obs, rewards, dones, extras = env.step(actions.to(device))

            # Sanity: check obs actually changes
            if step == 4:
                obs_at_5 = obs[0, :3].cpu().numpy()
                delta = np.linalg.norm(obs_at_5 - obs_before_ep)
                print(f"[COLLECT] Sanity: EE delta after 5 steps = {delta:.6f}m")
                if delta < 1e-4:
                    raise RuntimeError(
                        f"obs not updating! delta={delta:.8f}. "
                        f"obs_before={obs_before_ep}, obs_now={obs_at_5}")

        # Each world completed one episode
        episodes_collected += world_count
        # Reset all worlds for next batch
        obs, _ = env.reset()

        done_pct = min(episodes_collected / num_episodes * 100, 100)
        print(f"[COLLECT] Episodes: {episodes_collected}/{num_episodes} "
              f"({done_pct:.0f}%)")

    # Concatenate all transitions
    obs_arr = np.concatenate(all_obs, axis=0)       # [T*N, obs_dim]
    act_arr = np.concatenate(all_actions, axis=0)    # [T*N, act_dim]

    print(f"[COLLECT] Total transitions: {obs_arr.shape[0]}")
    return {"obs": obs_arr, "actions": act_arr}


def main():
    parser = argparse.ArgumentParser(description="Collect expert demos for BC")
    parser.add_argument("--task", type=str, default="insert_clip",
                        choices=["insert_clip", "aerial_regrasp"],
                        help="Task to collect demos for")
    parser.add_argument("--world-count", type=int, default=32)
    parser.add_argument("--num-episodes", type=int, default=64,
                        help="Total episodes (rounded up to world_count multiple)")
    parser.add_argument("--device", type=str,
                        default=os.environ.get("NEWTON_DEVICE", "cuda:0"))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    os.makedirs(os.path.join(_script_dir, "..", "data", "bc_demos"), exist_ok=True)

    if args.task == "insert_clip":
        from newton_insert_clip_multiworld_env import NewtonInsertClipMultiWorldEnv
        EnvClass = NewtonInsertClipMultiWorldEnv
        expert_fn = expert_action_insert_clip
        default_output = "insert_clip_demos.npz"
    else:
        from newton_aerial_regrasp_multiworld_env import NewtonAerialRegraspMultiWorldEnv
        EnvClass = NewtonAerialRegraspMultiWorldEnv
        expert_fn = expert_action_aerial_regrasp
        default_output = "aerial_regrasp_demos.npz"

    if args.output is None:
        args.output = os.path.join(
            _script_dir, "..", "data", "bc_demos", default_output)

    print(f"[COLLECT] Task: {args.task}")
    print(f"[COLLECT] Device: {args.device}")
    print(f"[COLLECT] World count: {args.world_count}")
    print(f"[COLLECT] Target episodes: {args.num_episodes}")
    print(f"[COLLECT] Output: {args.output}")

    env = EnvClass(
        world_count=args.world_count,
        device=args.device,
    )

    t0 = time.time()
    demos = collect_demos(
        env,
        expert_fn=expert_fn,
        num_episodes=args.num_episodes,
        device=args.device,
    )
    elapsed = time.time() - t0

    # Quality check — data is step-major: [step0_all_worlds, step1_all_worlds, ...]
    obs_arr = demos["obs"]
    act_arr = demos["actions"]
    N = env.num_envs
    T = obs_arr.shape[0] // N
    obs_std = obs_arr[:, :3].std(axis=0)
    act_norms = np.linalg.norm(act_arr, axis=1)
    print(f"\n[QUALITY] Total: {obs_arr.shape[0]} samples = {T} steps × {N} worlds")
    print(f"[QUALITY] obs[:3] std across all samples: {obs_std}")
    print(f"[QUALITY] action norm: mean={act_norms.mean():.4f}, std={act_norms.std():.4f}")
    # Correct reshape: step-major → [T, N, dim]
    if T > 1:
        obs_sw = obs_arr[:T * N].reshape(T, N, -1)  # [steps, worlds, obs_dim]
        # Per-world EE std over time (should be > 0 if robot is moving)
        ee_std_per_world = obs_sw[:, :, :3].std(axis=0)  # [N, 3]
        ee_std_mean = ee_std_per_world.mean(axis=0)
        print(f"[QUALITY] per-world EE std over time (mean): {ee_std_mean}")
        # World 0 trajectory
        w0_ee = obs_sw[:, 0, :3]
        print(f"[QUALITY] world0: t=0 EE={w0_ee[0]}, t={T-1} EE={w0_ee[-1]}")
        print(f"[QUALITY] world0: EE delta = {w0_ee[-1] - w0_ee[0]}")
        if ee_std_mean.max() < 1e-4:
            raise RuntimeError("[QUALITY] FAIL: EE position static within episodes!")

    # Save
    np.savez_compressed(args.output, **demos)
    print(f"\n[COLLECT] Saved {demos['obs'].shape[0]} transitions to {args.output}")
    print(f"[COLLECT] Time: {elapsed:.0f}s")
    print(f"[COLLECT] obs shape: {demos['obs'].shape}")
    print(f"[COLLECT] actions shape: {demos['actions'].shape}")

    env.close() if hasattr(env, "close") else None


if __name__ == "__main__":
    main()
