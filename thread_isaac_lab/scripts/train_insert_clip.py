#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RSL-RL PPO + DAPG training for InsertIntoClip -- Multi-world.

Uses NewtonInsertClipEnv with N parallel worlds via Newton replicate() + SolverVBD.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_insert_clip.py \
        --world-count 512 --max-iterations 300 --device cuda:0 \
        --demos thread_isaac_lab/data/bc_demos/insert_clip_demos.npz
"""

import os
import sys

import numpy as np
import torch

_D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _D)
sys.path.insert(0, os.path.join(_D, "..", "envs"))
sys.path.insert(0, os.path.join(_D, ".."))

from train_common import SkillTrainConfig, run_dapg_training


# -- Skill-specific callbacks --------------------------------------------------

def _add_args(parser):
    parser.add_argument("--mode", type=str, default="approach",
                        choices=["approach", "insert"],
                        help="IC mode: approach (coarse, LIFT_Z→groove+12mm) "
                             "or insert (precision, groove+12mm→groove 3mm)")
    parser.add_argument("--alpha-dist-thresh", type=float, default=0.030,
                        help="Distance threshold [m]: latch alpha at alpha_min "
                             "when median dist < this (default 30mm)")
    parser.add_argument("--reward-mode", type=str, default=None,
                        choices=["exp", "hybrid", "multiplicative"],
                        help="Override env REWARD_MODE")
    parser.add_argument("--range-ori", type=float, default=None,
                        help="Override env RANGE_ORI [rad]")
    parser.add_argument("--w-hold", type=float, default=None,
                        help="Left arm action norm penalty weight")
    parser.add_argument("--left-damping", type=float, default=None,
                        help="Left arm action damping factor")


def _create_env(args):
    from newton_insert_clip_env import NewtonInsertClipEnv
    return NewtonInsertClipEnv(
        world_count=args.world_count, device=args.device, mode=args.mode)


def _apply_overrides(env, args):
    ov = {}

    def _set(attr, val):
        if val is not None:
            setattr(env, attr, val)
            ov[attr] = val

    _set("REWARD_MODE", args.reward_mode)
    _set("RANGE_ORI", args.range_ori)
    _set("W_HOLD", args.w_hold)
    _set("LEFT_ACTION_DAMPING", args.left_damping)
    return ov


def _make_ic_alpha_and_log():
    """Distance-conditioned alpha with latch + per-iter logging.

    get_alpha consumes the rollout accumulator (reset on read).
    per_iter_log reuses the cached value to avoid double-reset (P1 fix).
    """
    latched_off = False
    cached_dist = 1.0  # fallback: far

    def get_alpha(it, args, env):
        nonlocal latched_off, cached_dist
        cached_dist = env.get_rollout_dist_median()
        if latched_off:
            return args.alpha_min
        if it >= args.alpha_anneal_iters:
            alpha = args.alpha_min
        else:
            t = it / args.alpha_anneal_iters
            alpha = args.alpha_init + t * (args.alpha_min - args.alpha_init)
        if cached_dist < args.alpha_dist_thresh:
            latched_off = True
            alpha = args.alpha_min
        return alpha

    def per_iter_log(it, env):
        return {"DAPG/dist_median_mm": cached_dist * 1000}

    return get_alpha, per_iter_log


def _convert_demos(raw_obs, raw_act, env, device):
    """IC-specific demo conversion: skip L1 quat fix.

    IC obs layout differs from AC/AR/Grip:
      [3:7]=R_quat, [10:14]=L_quat (no finger_width gap at [7]).
    The default train_common L1 fix uses indices [3, 11, 19, 26] which are
    correct for AC/AR/Grip but WRONG for IC (indices 11, 19, 26 point to
    non-quaternion data: L_quat partial, cable shape, distance).

    IC env already normalizes quats via _normalize_quat_w_positive() during
    data collection, so no L1 fix is needed here.
    """
    assert raw_obs.shape[1] == env.num_obs, (
        f"IC demo obs dim {raw_obs.shape[1]} != env {env.num_obs}")
    assert raw_act.shape[1] == env.num_actions, (
        f"IC demo act dim {raw_act.shape[1]} != env {env.num_actions}")
    return (
        torch.tensor(raw_obs, dtype=torch.float32, device=device),
        torch.tensor(raw_act, dtype=torch.float32, device=device),
    )


def _best_metric(env, it, args):
    """Track episode success rate for best-model save."""
    if it < 5:
        return None
    sr = float(env._last_success_rate) if hasattr(env, "_last_success_rate") else None
    if sr is not None:
        return ("success_rate", sr, "max")
    return None


# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    # Pre-parse --mode for config naming (before run_dapg_training parses all args)
    import argparse as _ap
    _pre = _ap.ArgumentParser(add_help=False)
    _pre.add_argument("--mode", type=str, default="approach", choices=["approach", "insert"])
    _pre_args, _ = _pre.parse_known_args()
    _mode_suffix = _pre_args.mode  # "approach" or "insert"

    _ic_get_alpha, _ic_per_iter_log = _make_ic_alpha_and_log()
    run_dapg_training(SkillTrainConfig(
        skill_name=f"InsertIntoClip-{_mode_suffix}",
        skill_tag=f"TRAIN-IC-{_mode_suffix.upper()}",
        log_dir_prefix=f"rl_insert_clip_{_mode_suffix}",
        create_env=_create_env,
        default_world_count=512,
        default_alpha_init=0.9,
        add_skill_args=_add_args,
        apply_env_overrides=_apply_overrides,
        convert_demos=_convert_demos,
        custom_get_alpha=_ic_get_alpha,
        per_iter_log_fn=_ic_per_iter_log,
        compute_best_metric=_best_metric,
        skill_adapter_type="INSERT_INTO_CLIP",
    ))
