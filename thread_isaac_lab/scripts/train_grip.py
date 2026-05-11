#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Train Grip (unified Clamp/Unclamp) policy with DAPG (PPO + BC auxiliary loss).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_grip.py \
        --mode clamp --world-count 256 --device cuda:1 \
        --demos data/bc_demos/grip_clamp_demos_v1.npz \
        --alpha-init 0.3 --alpha-min 0.2 --max-iterations 200
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
    parser.add_argument("--mode", type=str, required=True, choices=["clamp", "unclamp"])
    parser.add_argument(
        "--expected-arm",
        type=str,
        default="both",
        choices=["right", "left", "both"],
        help="Clamp success predicate selector. Default 'both' preserves legacy strict dual-arm success.",
    )
    parser.add_argument(
        "--k-clamp", type=int, default=None, help="Override CLAMP_SUSTAIN (default: K_CLAMP from task_config)"
    )
    parser.add_argument("--dual-arm", action="store_true", help="Use dual-arm 42D/14D format instead of per-arm 28D/6D")
    parser.add_argument(
        "--hand",
        type=str,
        default=None,
        choices=["R", "L"],
        help="Hand for adapter type (R=CLAMP_R, L=CLAMP_L). Required with --dual-arm",
    )


def _create_env(args):
    from newton_grip_env import NewtonGripEnv

    return NewtonGripEnv(
        world_count=args.world_count,
        device=args.device,
        mode=args.mode,
        cfg={"expected_arm": args.expected_arm},
        dual_arm=args.dual_arm,
    )


def _apply_overrides(env, args):
    ov = {}
    if args.k_clamp is not None:
        env.CLAMP_SUSTAIN = args.k_clamp
        ov["K_CLAMP"] = args.k_clamp
    return ov


def _normalize_quat_w_positive(q):
    """Flip quaternion sign so w >= 0 (double-cover consistency)."""
    # q: [..., 4] with (x, y, z, w) convention, w at index 3
    mask = q[..., 3:4] < 0
    return np.where(mask, -q, q)


def _convert_demos(raw_obs, raw_act, env, device):
    """Convert demos to match env format.

    Per-arm (28D/6D): Convert 42D/12D dual-arm demos to per-arm format.
    Dual-arm (42D/14D): Use 42D obs directly, pad 12D actions to 14D with zero finger cmds.

    Fixes applied:
    - C2: Filter approach-phase transitions (keep only near-cable Z < threshold)
    - L1: Normalize quaternions to w >= 0 (left arm had 44% qw < 0)
    """
    T = raw_obs.shape[0]
    if raw_obs.shape[1] in (42, 45) and raw_act.shape[1] == 12 and getattr(env, "_dual_arm", False):
        # Dual-arm mode: keep 42D/45D obs, pad 12D actions → 14D (append 2D zero finger cmds)
        # C2 filter
        from configs.task_config import GROOVE_CENTER_Z

        FILTER_RADIUS = 0.030
        r_z = raw_obs[:, 2]
        l_z = raw_obs[:, 10]
        near_mask = (np.abs(r_z - GROOVE_CENTER_Z) < FILTER_RADIUS) & (np.abs(l_z - GROOVE_CENTER_Z) < FILTER_RADIUS)
        n_before = T
        raw_obs = raw_obs[near_mask]
        raw_act = raw_act[near_mask]
        T = raw_obs.shape[0]
        print(f"[GRIP-DEMO] Filtered approach-phase: {n_before} -> {T} transitions ({T / n_before * 100:.1f}% kept)")
        if T < 50:
            raise ValueError(f"Too few near-cable transitions ({T}).")
        # L1 fix
        for qstart in [3, 11, 19, 26]:
            raw_obs[:, qstart : qstart + 4] = _normalize_quat_w_positive(raw_obs[:, qstart : qstart + 4])
        # Pad actions: [N,12] → [N,14] with zero finger commands
        padded_act = np.zeros((T, 14), dtype=np.float32)
        padded_act[:, :12] = raw_act
        # finger cmds = 0 means "don't move" (no closing/opening delta)
        print(f"[GRIP-DEMO] Dual-arm: obs {raw_obs.shape[1]}D, act 12D→14D (zero finger cmds)")
        return (
            torch.tensor(raw_obs, dtype=torch.float32, device=device),
            torch.tensor(padded_act, dtype=torch.float32, device=device),
        )
    elif raw_obs.shape[1] in (42, 45) and raw_act.shape[1] == 12:
        # --- C2 fix: Filter to near-cable transitions only ---
        # obs[2] = right hand Z (clamp/fingertip frame)
        from configs.task_config import GROOVE_CENTER_Z

        FILTER_RADIUS = 0.030  # 30mm
        r_z = raw_obs[:, 2]
        l_z = raw_obs[:, 10]
        # Keep transitions where BOTH arms are near cable height
        near_mask = (np.abs(r_z - GROOVE_CENTER_Z) < FILTER_RADIUS) & (np.abs(l_z - GROOVE_CENTER_Z) < FILTER_RADIUS)
        n_before = T
        raw_obs = raw_obs[near_mask]
        raw_act = raw_act[near_mask]
        T = raw_obs.shape[0]
        print(
            f"[GRIP-DEMO] Filtered approach-phase: {n_before} -> {T} "
            f"transitions ({T / n_before * 100:.1f}% kept, Z within {FILTER_RADIUS * 1000:.0f}mm)"
        )

        if T < 50:
            raise ValueError(
                f"Too few near-cable transitions ({T}). Demos may be from wrong phase. Recollect from Grip P0."
            )

        # --- L1 fix: Normalize quaternions to w >= 0 ---
        # Right hand quat: obs[3:7], Left hand quat: obs[11:15]
        # Cable quat: obs[19:23], Clip quat: obs[26:30]
        for qstart in [3, 11, 19, 26]:
            raw_obs[:, qstart : qstart + 4] = _normalize_quat_w_positive(raw_obs[:, qstart : qstart + 4])

        per_obs = np.empty((T * 2, 28), dtype=np.float32)
        per_act = np.empty((T * 2, 6), dtype=np.float32)
        # Right arm (even slots)
        # Old obs: [0:8]=R_hand, [8:16]=L_hand, [16:23]=cable_seg,
        #          [23:30]=clip, [30:36]=R_error, [36:42]=L_error
        # Per-arm: [0:8]=own_hand, [8:15]=cable, [15:22]=clip, [22:28]=own_error
        per_obs[0::2, 0:8] = raw_obs[:, 0:8]
        per_obs[0::2, 8:15] = raw_obs[:, 16:23]
        per_obs[0::2, 15:22] = raw_obs[:, 23:30]
        per_obs[0::2, 22:28] = raw_obs[:, 30:36]
        per_act[0::2] = raw_act[:, 0:6]
        # Left arm (odd slots)
        per_obs[1::2, 0:8] = raw_obs[:, 8:16]
        per_obs[1::2, 8:15] = raw_obs[:, 16:23]
        per_obs[1::2, 15:22] = raw_obs[:, 23:30]
        per_obs[1::2, 22:28] = raw_obs[:, 36:42]
        per_act[1::2] = raw_act[:, 6:12]
        return (
            torch.tensor(per_obs, dtype=torch.float32, device=device),
            torch.tensor(per_act, dtype=torch.float32, device=device),
        )
    elif raw_obs.shape[1] == env.num_obs and raw_act.shape[1] == env.num_actions:
        # --- C2 fix: Filter to near-cable transitions only (42D dual-arm only) ---
        if raw_obs.shape[1] == 42:
            from configs.task_config import GROOVE_CENTER_Z

            FILTER_RADIUS = 0.030
            r_z = raw_obs[:, 2]
            l_z = raw_obs[:, 10]
            near_mask = (np.abs(r_z - GROOVE_CENTER_Z) < FILTER_RADIUS) & (
                np.abs(l_z - GROOVE_CENTER_Z) < FILTER_RADIUS
            )
            n_before = T
            raw_obs = raw_obs[near_mask]
            raw_act = raw_act[near_mask]
            T = raw_obs.shape[0]
            print(
                f"[GRIP-DEMO] Filtered approach-phase: {n_before} -> {T} transitions ({T / n_before * 100:.1f}% kept)"
            )
            if T < 50:
                raise ValueError(f"Too few near-cable transitions ({T}).")
            # L1 fix: 42D quat indices
            for qstart in [3, 11, 19, 26]:
                raw_obs[:, qstart : qstart + 4] = _normalize_quat_w_positive(raw_obs[:, qstart : qstart + 4])
        elif raw_obs.shape[1] == 45:
            # 45D dual-arm: same layout as 42D + 3 zero-pad at [42:45]
            from configs.task_config import GROOVE_CENTER_Z

            FILTER_RADIUS = 0.030
            r_z = raw_obs[:, 2]
            l_z = raw_obs[:, 10]
            near_mask = (np.abs(r_z - GROOVE_CENTER_Z) < FILTER_RADIUS) & (
                np.abs(l_z - GROOVE_CENTER_Z) < FILTER_RADIUS
            )
            n_before = T
            raw_obs = raw_obs[near_mask]
            raw_act = raw_act[near_mask]
            T = raw_obs.shape[0]
            print(
                f"[GRIP-DEMO] Filtered approach-phase (45D): {n_before} -> {T} "
                f"transitions ({T / n_before * 100:.1f}% kept)"
            )
            if T < 50:
                raise ValueError(f"Too few near-cable transitions ({T}).")
            # L1 fix: 45D uses AC/AR layout (quat@3, @11, @19, @26)
            for qstart in [3, 11, 19, 26]:
                raw_obs[:, qstart : qstart + 4] = _normalize_quat_w_positive(raw_obs[:, qstart : qstart + 4])
        elif raw_obs.shape[1] == 28:
            # Per-arm 28D: filter on own-hand Z only, quat indices differ
            from configs.task_config import GROOVE_CENTER_Z

            FILTER_RADIUS = 0.030
            own_z = raw_obs[:, 2]
            near_mask = np.abs(own_z - GROOVE_CENTER_Z) < FILTER_RADIUS
            n_before = T
            raw_obs = raw_obs[near_mask]
            raw_act = raw_act[near_mask]
            T = raw_obs.shape[0]
            print(f"[GRIP-DEMO] Filtered (per-arm): {n_before} -> {T} transitions ({T / n_before * 100:.1f}% kept)")
            if T < 50:
                raise ValueError(f"Too few near-cable transitions ({T}).")
            # L1 fix: 28D quat indices [own_quat=3, cable_quat=11, clip_quat=18]
            for qstart in [3, 11, 18]:
                raw_obs[:, qstart : qstart + 4] = _normalize_quat_w_positive(raw_obs[:, qstart : qstart + 4])
        else:
            raise ValueError(f"Unrecognized obs dim {raw_obs.shape[1]} in passthrough branch. Expected 42, 45, or 28.")
        print(f"[GRIP-DEMO] Passthrough: obs {raw_obs.shape[1]}D, act {raw_act.shape[1]}D")
        return (
            torch.tensor(raw_obs, dtype=torch.float32, device=device),
            torch.tensor(raw_act, dtype=torch.float32, device=device),
        )
    else:
        raise ValueError(f"Demo shape mismatch: obs={raw_obs.shape[1]}, act={raw_act.shape[1]}")


def _best_metric(env, it, args):
    """Track episode success rate for best-model save."""
    if it < 5:
        return None
    sr = float(env._last_success_rate) if hasattr(env, "_last_success_rate") else None
    if sr is not None:
        return ("success_rate", sr, "max")
    return None


def _extra_summary(env, args):
    return {
        "mode": args.mode,
        "expected_arm": getattr(env, "_expected_arm", args.expected_arm),
        "expected_arm_code": getattr(env, "_expected_arm_code", None),
        "selected_success_semantics_version": "b5_expected_arm_v1",
    }


# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    run_dapg_training(
        SkillTrainConfig(
            skill_name="Grip",
            skill_tag="TRAIN-GRIP",
            log_dir_prefix=lambda args: f"rl_grip_{args.mode}",
            create_env=_create_env,
            default_num_steps_per_env=100,
            add_skill_args=_add_args,
            apply_env_overrides=_apply_overrides,
            convert_demos=_convert_demos,
            compute_best_metric=_best_metric,
            extra_summary_fn=_extra_summary,
            skill_adapter_type=lambda args: (
                f"CLAMP_{args.hand}"
                if args.dual_arm and args.hand
                else ("CLAMP" if args.mode == "clamp" else "UNCLAMP")
            ),
            # Grip uses different PPO defaults (shorter episodes, tighter KL)
            ppo_overrides={
                "num_learning_epochs": 5,
                "value_loss_coef": 1.0,
                "desired_kl": 0.01,
            },
        )
    )
