#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RSL-RL PPO + DAPG training for AerialRegrasp -- Multi-world.

Uses NewtonAerialRegraspEnv with N parallel worlds via Newton replicate() + SolverVBD.
Precondition: left arm holds cable at LIFT_Z, right arm open.
Task: right arm approaches and grasps cable.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_aerial_regrasp.py \
        --world-count 256 --max-iterations 300 --device cuda:0 \
        --demos thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_v6_warmup.npz
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
    parser.add_argument("--reward-mode", type=str, default=None,
                        choices=["exp", "hybrid", "multiplicative"],
                        help="Override env REWARD_MODE")
    parser.add_argument("--range-ori", type=float, default=None,
                        help="Right arm ori reward scale [rad]")
    parser.add_argument("--w-hold", type=float, default=None,
                        help="Left arm action norm penalty weight")
    parser.add_argument("--w-drift", type=float, default=None,
                        help="Left arm EE drift penalty weight")
    parser.add_argument("--w-tail", type=float, default=None,
                        help="Ori tail penalty weight")
    parser.add_argument("--thresh-warn", type=float, default=None,
                        help="Ori tail warning threshold [rad]")
    parser.add_argument("--ori-tail-cap", type=float, default=None,
                        help="Ori tail excess cap [rad]")
    parser.add_argument("--drift-cap", type=float, default=None,
                        help="Left arm drift cap [m]")
    parser.add_argument("--r-step-bonus", type=float, default=None,
                        help="Override R_STEP_BONUS (step completion bonus)")
    parser.add_argument("--w-stab", type=float, default=None,
                        help="Cable jitter penalty weight (0=disabled)")
    parser.add_argument("--w-ease", type=float, default=None,
                        help="Cable ease reward weight (0=disabled)")
    parser.add_argument("--w-ori", type=float, default=None,
                        help="Orientation reward weight")
    parser.add_argument("--eps-ori", type=float, default=None,
                        help="Orientation reward decay length [rad]")
    parser.add_argument("--w-pos", type=float, default=None,
                        help="Position reward weight")
    parser.add_argument("--r-penalty", type=float, default=None,
                        help="Per-step penalty (negative)")
    parser.add_argument("--r-drop", type=float, default=None,
                        help="Cable drop terminal penalty (negative)")
    parser.add_argument("--r-task-bonus", type=float, default=None,
                        help="Task success bonus")
    parser.add_argument("--target-ema-alpha", type=float, default=None,
                        help="Target EMA smoothing (0.2=heavy, 1.0=disabled)")
    parser.add_argument("--k-sustain", type=int, default=None,
                        help="Override C5_SUSTAIN_STEPS (default=K_GRASP=5)")


def _create_env(args):
    from newton_aerial_regrasp_env import NewtonAerialRegraspEnv
    return NewtonAerialRegraspEnv(
        world_count=args.world_count, device=args.device)


def _apply_overrides(env, args):
    ov = {}

    def _set(attr, val):
        if val is not None:
            setattr(env, attr, val)
            ov[attr] = val

    _set("REWARD_MODE", args.reward_mode)
    _set("RANGE_ORI", args.range_ori)
    _set("W_HOLD", args.w_hold)
    _set("W_DRIFT", args.w_drift)
    _set("W_TAIL", args.w_tail)
    _set("THRESH_WARN", args.thresh_warn)
    _set("ORI_TAIL_CAP", args.ori_tail_cap)
    _set("DRIFT_CAP", args.drift_cap)
    _set("R_STEP_BONUS", args.r_step_bonus)
    _set("W_STAB", args.w_stab)
    _set("W_EASE", args.w_ease)
    _set("W_ORI", args.w_ori)
    _set("EPS_ORI", args.eps_ori)
    _set("W_POS", args.w_pos)
    _set("R_PENALTY", args.r_penalty)
    _set("R_DROP", args.r_drop)
    _set("R_TASK_BONUS", args.r_task_bonus)
    _set("TARGET_EMA_ALPHA", args.target_ema_alpha)
    _set("C5_SUSTAIN_STEPS", args.k_sustain)
    return ov


def _convert_demos(raw_obs, raw_act, env, device):
    """Pad 42D demos to 45D (append 3 zeros at [42:45]) and apply L1 quat fix."""
    T = raw_obs.shape[0]
    if raw_obs.shape[1] == 42 and env.num_obs == 45:
        # L1 fix: normalize quats to w >= 0
        for qs in [3, 11, 19, 26]:
            w = raw_obs[:, qs + 3]
            neg = w < 0
            if neg.any():
                raw_obs[neg, qs:qs+4] *= -1
        # Pad 42D → 45D
        padded = np.zeros((T, 45), dtype=np.float32)
        padded[:, :42] = raw_obs
        print(f"[AR-DEMO] Padded 42D→45D ({T} transitions)")
        return (
            torch.tensor(padded, dtype=torch.float32, device=device),
            torch.tensor(raw_act, dtype=torch.float32, device=device),
        )
    elif raw_obs.shape[1] == env.num_obs:
        # Already correct dim — just L1 fix
        for qs in [3, 11, 19, 26]:
            if qs + 4 <= raw_obs.shape[1]:
                w = raw_obs[:, qs + 3]
                neg = w < 0
                if neg.any():
                    raw_obs[neg, qs:qs+4] *= -1
        return (
            torch.tensor(raw_obs, dtype=torch.float32, device=device),
            torch.tensor(raw_act, dtype=torch.float32, device=device),
        )
    else:
        raise ValueError(
            f"AR demo obs dim {raw_obs.shape[1]} unexpected (env={env.num_obs})")


def _best_metric(env, it, args):
    """Track success rate for best-model save."""
    if it < 5:
        return None  # Skip early noisy iterations
    sr = float(env._last_success_rate) if hasattr(env, "_last_success_rate") else None
    if sr is not None:
        return ("success_rate", sr, "max")
    return None


# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    run_dapg_training(SkillTrainConfig(
        skill_name="AerialRegrasp",
        skill_tag="TRAIN-AR",
        log_dir_prefix="rl_aerial_regrasp",
        create_env=_create_env,
        add_skill_args=_add_args,
        apply_env_overrides=_apply_overrides,
        convert_demos=_convert_demos,
        compute_best_metric=_best_metric,
        skill_adapter_type="AERIAL_REGRASP",
    ))
