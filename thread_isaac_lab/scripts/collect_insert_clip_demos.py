#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect InsertIntoClip demonstrations for DAPG — multi-episode wet-run.

Replays the scripted descent (LIFT_Z → PUSH_Z) through NewtonInsertClipEnv,
recording (obs, action) pairs in env-matching format (45D obs, 12D act).

Each episode:
  1. env.reset() (restores precondition: cable clamped at LIFT_Z)
  2. Scripted descent: both arms descend in -Z (action_z = -0.1 per step)
  3. Hold at PUSH_Z for settle
  4. Record (obs, action) per step

Noise injection:
  - Action noise: Gaussian σ on XY (Z descent is clean)
  - Cable init noise: via env DR (future)

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    python thread_isaac_lab/scripts/collect_insert_clip_demos.py \
        --num-episodes 20 --device cuda:0 \
        --output thread_isaac_lab/data/bc_demos/insert_clip_demos.npz
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "envs"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"))

from newton_insert_clip_env import NewtonInsertClipEnv
from task_config import LIFT_Z, PUSH_Z, CABLE_SEG_LEN, CABLE_RADIUS, GROOVE_BODIES_MIN, GRIP_HALF_SPAN, GROOVE_CENTER_Z, EE_TO_FINGERTIP, T_DIST_APPROACH

# Action / obs scaling (must match env)
ROT_ACTION_SCALE = 0.05    # ~2.9 deg per action unit
KP_ORI = 0.4               # proportional gain for orientation correction
KP_XY = 0.3                # proportional gain for per-arm XY correction toward clip
ACTION_CLIP = 1.0


def _quat_multiply_xyzw(q1, q2):
    """Batch-safe quaternion multiply (xyzw convention)."""
    x1, y1, z1, w1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
    x2, y2, z2, w2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    return np.stack([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    ], axis=-1)


def _quat_to_axis_angle_batch(q_xyzw):
    """Batch quaternion to axis-angle. q: [..., 4] → aa: [..., 3]."""
    xyz = q_xyzw[..., :3]
    w = q_xyzw[..., 3:4]
    # Ensure w >= 0 (shortest path)
    sign = np.sign(np.where(w == 0, 1.0, w))
    xyz = xyz * sign
    w = w * sign
    sin_half = np.linalg.norm(xyz, axis=-1, keepdims=True).clip(1e-8, None)
    angle = 2.0 * np.arctan2(sin_half, w)
    axis = xyz / sin_half
    return axis * angle


def _compute_per_arm_ori_error(arm_quat_xyzw, target_quat_xyzw):
    """Per-arm orientation error: axis-angle from arm_quat to target_quat.
    arm_quat: [W, 4], target_quat: [4] → [W, 3]."""
    arm_inv = arm_quat_xyzw.copy()
    arm_inv[..., :3] = -arm_inv[..., :3]  # conjugate
    q_error = _quat_multiply_xyzw(
        np.broadcast_to(target_quat_xyzw, arm_quat_xyzw.shape), arm_inv)
    return _quat_to_axis_angle_batch(q_error)


def _update_success_flag(extras_i, flag, ep_done_prev, world_count):
    # B-1: only write into worlds not yet done BEFORE this step, to block
    # auto-reset cross-episode contamination.
    # B-3: no fallback — env contract is log_per_world["success"] (float32[W]).
    log_pw = extras_i.get("log_per_world")
    if log_pw is None or "success" not in log_pw:
        raise RuntimeError(
            "env did not expose log_per_world['success']; required by IC demo "
            "collector. Check NewtonInsertClipEnv contract at "
            "newton_insert_clip_env.py:1489."
        )
    sv = log_pw["success"]
    if not isinstance(sv, np.ndarray) or sv.shape != (world_count,):
        raise RuntimeError(
            f"log_per_world['success'] must be np.ndarray[{world_count}], "
            f"got {type(sv).__name__}/{getattr(sv, 'shape', None)}"
        )
    if not np.isfinite(sv).all():
        raise RuntimeError("log_per_world['success'] contains NaN/Inf")
    sv_bool = (sv > 0.5)
    active = ~ep_done_prev
    flag[active] |= sv_bool[active]


def main():
    parser = argparse.ArgumentParser(description="InsertIntoClip demo collection (wet-run)")
    parser.add_argument("--num-episodes", type=int, default=20,
                        help="Number of episodes to collect")
    parser.add_argument("--world-count", type=int, default=4,
                        help="Parallel worlds (episodes collected = num-episodes * world-count)")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output", type=str,
                        default="thread_isaac_lab/data/bc_demos/insert_clip_demos.npz")
    parser.add_argument("--mode", type=str, default="approach", choices=["approach", "insert"],
                        help="approach: LIFT_Z→groove+12mm, insert: groove+12mm→groove")
    parser.add_argument("--action-noise-xy", type=float, default=0.02,
                        help="Gaussian σ for XY action noise (units, not meters)")
    parser.add_argument("--overshoot-mm", type=float, default=10.0,
                        help="Overshoot past target in mm")
    parser.add_argument("--hold-steps", type=int, default=50,
                        help="Hold steps at target after descent")
    args = parser.parse_args()

    # F-6 (v3.1 W3 + v3.2 C4): fail-fast parity with Grip/AC — validate
    # output path BEFORE env build / collection run. Variable name `out_dir`
    # matches Grip:126 and AC (grep idiom parity).
    if not args.output.endswith(".npz"):
        parser.error(f"--output must end in .npz, got {args.output!r}")
    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    device = args.device
    world_count = args.world_count
    action_noise_sigma = args.action_noise_xy
    mode = args.mode

    print(f"=== InsertIntoClip Demo Collection (wet-run, mode={mode}) ===")
    print(f"  Episodes: {args.num_episodes} batches × {world_count} worlds "
          f"= {args.num_episodes * world_count} total")
    print(f"  Action noise σ(XY): {action_noise_sigma}")

    # Descent parameters — mode-dependent
    if mode == "approach":
        # LIFT_Z(1.120) → PUSH_Z(1.025) with overshoot
        descent_target_z = PUSH_Z - args.overshoot_mm / 1000.0
        descent_total = LIFT_Z - descent_target_z
        action_z_unit = -0.1  # 1.5mm per step (coarse)
    else:
        # groove+12mm(1.041) → GROOVE_CENTER_Z+EE_TO_FINGERTIP(1.029) with overshoot
        insert_start_z = GROOVE_CENTER_Z + T_DIST_APPROACH + EE_TO_FINGERTIP  # 1.041m
        insert_target_z = GROOVE_CENTER_Z + EE_TO_FINGERTIP - args.overshoot_mm / 1000.0  # ~1.019m
        descent_total = insert_start_z - insert_target_z  # ~22mm
        action_z_unit = -0.05  # 0.75mm per step (precise for 12mm descent)

    # Build env
    print(f"\n[BUILD] Constructing env (world_count={world_count}, mode={mode})...")
    env = NewtonInsertClipEnv(world_count=world_count, device=device, mode=mode)

    groove_target_quat = env.GROOVE_TARGET_QUAT  # target arm orientation for groove alignment

    step_descent = abs(action_z_unit) * env.POS_ACTION_SCALE
    n_descent_steps = int(math.ceil(descent_total / step_descent))
    hold_steps = args.hold_steps
    total_steps_per_ep = n_descent_steps + hold_steps

    print(f"  Descent: {n_descent_steps} steps × {step_descent*1000:.1f}mm "
          f"(total {descent_total*1000:.1f}mm)")
    print(f"  Hold: {hold_steps} steps")
    print(f"  Total steps/ep: {total_steps_per_ep}")

    # Collect
    all_obs = []
    all_act = []
    episode_success_list = []
    success_count = 0
    total_episodes = 0

    for batch_i in range(args.num_episodes):
        t0 = time.time()
        obs, info = env.reset()

        ep_obs = [obs.cpu().numpy()]
        ep_act = []
        ep_done = np.zeros(world_count, dtype=bool)
        # B-1: true success flag, sourced from env log_per_world["success"]
        # before auto-reset. Reset each batch.
        ep_success_flag = np.zeros(world_count, dtype=bool)
        t_done = np.full(world_count, total_steps_per_ep, dtype=np.int32)
        global_t = 0

        # Phase 1: Descent with per-arm independent corrections
        for step_i in range(n_descent_steps):
            current_obs_np = ep_obs[-1]  # [W, 45] obs at step start
            action = torch.zeros(world_count, 12, device=device)
            action[:, 2] = action_z_unit   # r_dz (descent)
            action[:, 8] = action_z_unit   # l_dz (descent)

            # Per-arm orientation P-control
            clamp_r_quat = current_obs_np[:, 3:7]    # [W, 4]
            clamp_l_quat = current_obs_np[:, 10:14]   # [W, 4]
            r_ori_err = _compute_per_arm_ori_error(clamp_r_quat, groove_target_quat)
            l_ori_err = _compute_per_arm_ori_error(clamp_l_quat, groove_target_quat)
            r_rot_action = np.clip(r_ori_err / ROT_ACTION_SCALE * KP_ORI,
                                   -ACTION_CLIP, ACTION_CLIP)
            l_rot_action = np.clip(l_ori_err / ROT_ACTION_SCALE * KP_ORI,
                                   -ACTION_CLIP, ACTION_CLIP)
            action[:, 3:6] = torch.from_numpy(r_rot_action).float().to(device)
            action[:, 9:12] = torch.from_numpy(l_rot_action).float().to(device)

            # Per-arm XY P-control toward clip (D1: compute from raw positions)
            clip_pos_xy = current_obs_np[:, 14:16]  # [W, 2] clip XY
            r_arm_xy = current_obs_np[:, 0:2]       # [W, 2] R clamp XY
            l_arm_xy = current_obs_np[:, 7:9]        # [W, 2] L clamp XY
            r_target_xy = clip_pos_xy.copy()
            r_target_xy[:, 1] += GRIP_HALF_SPAN      # R at +Y side
            l_target_xy = clip_pos_xy.copy()
            l_target_xy[:, 1] -= GRIP_HALF_SPAN      # L at -Y side
            r_clip_err_xy = r_arm_xy - r_target_xy    # [W, 2]
            l_clip_err_xy = l_arm_xy - l_target_xy    # [W, 2]
            action[:, 0] -= torch.from_numpy(
                r_clip_err_xy[:, 0] * KP_XY / env.POS_ACTION_SCALE).float().to(device)
            action[:, 1] -= torch.from_numpy(
                r_clip_err_xy[:, 1] * KP_XY / env.POS_ACTION_SCALE).float().to(device)
            action[:, 6] -= torch.from_numpy(
                l_clip_err_xy[:, 0] * KP_XY / env.POS_ACTION_SCALE).float().to(device)
            action[:, 7] -= torch.from_numpy(
                l_clip_err_xy[:, 1] * KP_XY / env.POS_ACTION_SCALE).float().to(device)

            # Independent XY noise per arm
            if action_noise_sigma > 0:
                noise_r = torch.randn(world_count, 2, device=device) * action_noise_sigma
                noise_l = torch.randn(world_count, 2, device=device) * action_noise_sigma
                action[:, 0] += noise_r[:, 0]
                action[:, 1] += noise_r[:, 1]
                action[:, 6] += noise_l[:, 0]
                action[:, 7] += noise_l[:, 1]

            obs_i, rew_i, done_i, extras_i = env.step(action)

            # Record for non-done worlds
            ep_act.append(action.cpu().numpy())
            ep_obs.append(obs_i.cpu().numpy())
            done_np = done_i.cpu().numpy().astype(bool)
            # W-6: exact ordering. success flag uses PRE-update ep_done as mask,
            # so step-of-done still captures the success signal.
            _update_success_flag(extras_i, ep_success_flag, ep_done, world_count)
            new_done = done_np & ~ep_done
            t_done[new_done] = global_t + 1
            ep_done |= done_np
            global_t += 1

            if ep_done.all():
                break

        # Phase 2: Hold with gentle per-arm orientation correction
        for step_i in range(hold_steps):
            current_obs_np = ep_obs[-1]  # [W, 45]
            action = torch.zeros(world_count, 12, device=device)

            # Per-arm gentle orientation correction
            clamp_r_quat = current_obs_np[:, 3:7]
            clamp_l_quat = current_obs_np[:, 10:14]
            r_ori_err = _compute_per_arm_ori_error(clamp_r_quat, groove_target_quat)
            l_ori_err = _compute_per_arm_ori_error(clamp_l_quat, groove_target_quat)
            r_rot_action = np.clip(r_ori_err / ROT_ACTION_SCALE * KP_ORI * 0.3,
                                   -ACTION_CLIP, ACTION_CLIP)
            l_rot_action = np.clip(l_ori_err / ROT_ACTION_SCALE * KP_ORI * 0.3,
                                   -ACTION_CLIP, ACTION_CLIP)
            action[:, 3:6] = torch.from_numpy(r_rot_action).float().to(device)
            action[:, 9:12] = torch.from_numpy(l_rot_action).float().to(device)

            # Per-arm XY P-control (gentle, D1: compute from raw positions)
            clip_pos_xy = current_obs_np[:, 14:16]
            r_arm_xy = current_obs_np[:, 0:2]
            l_arm_xy = current_obs_np[:, 7:9]
            r_target_xy = clip_pos_xy.copy()
            r_target_xy[:, 1] += GRIP_HALF_SPAN
            l_target_xy = clip_pos_xy.copy()
            l_target_xy[:, 1] -= GRIP_HALF_SPAN
            r_clip_err_xy = r_arm_xy - r_target_xy
            l_clip_err_xy = l_arm_xy - l_target_xy
            action[:, 0] -= torch.from_numpy(
                r_clip_err_xy[:, 0] * KP_XY * 0.5 / env.POS_ACTION_SCALE).float().to(device)
            action[:, 1] -= torch.from_numpy(
                r_clip_err_xy[:, 1] * KP_XY * 0.5 / env.POS_ACTION_SCALE).float().to(device)
            action[:, 6] -= torch.from_numpy(
                l_clip_err_xy[:, 0] * KP_XY * 0.5 / env.POS_ACTION_SCALE).float().to(device)
            action[:, 7] -= torch.from_numpy(
                l_clip_err_xy[:, 1] * KP_XY * 0.5 / env.POS_ACTION_SCALE).float().to(device)

            if action_noise_sigma > 0:
                noise_r = torch.randn(world_count, 2, device=device) * action_noise_sigma * 0.5
                noise_l = torch.randn(world_count, 2, device=device) * action_noise_sigma * 0.5
                action[:, 0] += noise_r[:, 0]
                action[:, 1] += noise_r[:, 1]
                action[:, 6] += noise_l[:, 0]
                action[:, 7] += noise_l[:, 1]

            obs_i, rew_i, done_i, extras_i = env.step(action)
            ep_act.append(action.cpu().numpy())
            ep_obs.append(obs_i.cpu().numpy())
            done_np = done_i.cpu().numpy().astype(bool)
            # W-6: exact ordering. success flag uses PRE-update ep_done.
            _update_success_flag(extras_i, ep_success_flag, ep_done, world_count)
            new_done = done_np & ~ep_done
            t_done[new_done] = global_t + 1
            ep_done |= done_np
            global_t += 1

            if ep_done.all():
                break

        # Per-world: collect transitions up to first-done step (F1 fix)
        # Without per-world t_done, auto-reset data post-termination would be
        # silently concatenated into the same "episode" (CRITICAL bug).
        ep_obs_arr = np.array(ep_obs)   # [T+1, W, obs_dim]
        ep_act_arr = np.array(ep_act)   # [T, W, act_dim]
        T = ep_act_arr.shape[0]
        t_done_clamped = np.minimum(t_done, T)

        batch_success = 0
        batch_kept = 0
        batch_skipped = 0
        for w in range(world_count):
            n_w = int(t_done_clamped[w])
            if n_w <= 0:
                # W-10: step-0 termination — skip and warn. Either reset-broken
                # precondition or env bug; propagating zero-length would break
                # downstream filter shape invariants.
                print(f"  [WARN] batch {batch_i} world {w}: n_w=0, skipped")
                batch_skipped += 1
                continue
            all_obs.append(ep_obs_arr[:n_w, w, :])
            all_act.append(ep_act_arr[:n_w, w, :])
            # B-1/v3: true success = env log_per_world["success"] raised at ANY
            # point before auto-reset. NOT `not ep_done` (that was F-1 inversion:
            # env `done = success ∨ timeout ∨ explosion ∨ cable_dropped`, so
            # `not ep_done` was keeping only worlds that never terminated —
            # i.e. the worst demos).
            success_w = bool(ep_success_flag[w])
            episode_success_list.append(success_w)
            batch_kept += 1
            if success_w:
                batch_success += 1

        success_count += batch_success
        # W1 (v3.1): count kept worlds in denominator, not world_count. Skipped
        # (n_w==0) worlds must NOT dilute the printed success rate since they
        # also don't contribute to episode_success_list.
        total_episodes += batch_kept

        elapsed = time.time() - t0
        print(f"  Batch {batch_i+1}/{args.num_episodes}: {T} steps, "
              f"success={batch_success}/{batch_kept} (skipped {batch_skipped}), "
              f"{elapsed:.1f}s")

    # W1 (v3.1): fail loudly on empty collection rather than hitting cryptic
    # ValueError at np.concatenate([], axis=0).
    if len(all_obs) == 0:
        raise RuntimeError(
            "[IC] 0 episodes collected — every world skipped (n_w=0). "
            "Check [WARN] lines above for reset/env precondition issues."
        )

    # Aggregate
    episode_lengths = np.array([ep.shape[0] for ep in all_obs], dtype=np.int32)
    episode_success = np.array(episode_success_list, dtype=bool)
    # F-3: raise, not assert. `python -O` strips asserts.
    if episode_success.shape[0] != len(all_obs):
        raise RuntimeError(
            f"episode_success {episode_success.shape[0]} != kept {len(all_obs)}"
        )
    all_obs_flat = np.concatenate(all_obs, axis=0)  # [N, obs_dim]
    all_act_flat = np.concatenate(all_act, axis=0)  # [N, act_dim]

    print(f"\n=== COLLECTION SUMMARY ===")
    print(f"  Total kept episodes: {total_episodes}")
    print(f"  Success rate: {success_count}/{total_episodes} "
          f"({100*success_count/total_episodes:.0f}%)")
    print(f"  Transitions: {all_obs_flat.shape[0]}")
    print(f"  obs: {all_obs_flat.shape}, act: {all_act_flat.shape}")
    print(f"  episodes: {episode_lengths.shape[0]}, "
          f"mean length={episode_lengths.mean():.1f}")

    # Save (C1 v3.2: out_dir already created in W3 pre-flight at main() top)
    np.savez(args.output, obs=all_obs_flat, actions=all_act_flat,
             episode_lengths=episode_lengths,
             episode_success=episode_success)
    print(f"  Saved: {args.output}")


if __name__ == "__main__":
    main()
