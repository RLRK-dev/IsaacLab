# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RSL-RL PPO training for ApproachCable -- Multi-world.

Uses NewtonApproachCableEnv with N parallel worlds via Newton replicate() + SolverVBD.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_approach_cable.py \
        --world-count 256 --max-iterations 300 --device cuda:0 \
        --demos thread_isaac_lab/data/bc_demos/grasp_cable_demos_v7.npz
"""

import os
import sys

import torch

_D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _D)
sys.path.insert(0, os.path.join(_D, "..", "envs"))
sys.path.insert(0, os.path.join(_D, ".."))

from train_common import SkillTrainConfig, run_dapg_training

# -- Skill-specific callbacks --------------------------------------------------

def _add_args(parser):
    # Reward magnitude overrides
    parser.add_argument("--grasp-bonus", type=float, default=None)
    parser.add_argument("--success-bonus", type=float, default=None)
    parser.add_argument("--step-penalty", type=float, default=None)
    parser.add_argument("--r-penalty", type=float, default=None,
                        help="R_PENALTY (per-step penalty, default=-1.33)")
    parser.add_argument("--align-reward-scale", type=float, default=None,
                        help="r_align scale (0=disabled, 0.05=default)")
    parser.add_argument("--align-gate-dist", type=float, default=None,
                        help="r_align only within this dist [m]")
    parser.add_argument("--eps-pos", type=float, default=None,
                        help="Position reward decay length [m]")
    parser.add_argument("--eps-pos-coarse", type=float, default=None,
                        help="Coarse position reward decay length [m] (default 1.0)")
    parser.add_argument("--eps-ori", type=float, default=None,
                        help="Orientation reward decay length [rad]")
    parser.add_argument("--reward-mode", type=str, default=None,
                        choices=["exp", "hybrid", "multiplicative"])
    parser.add_argument("--w-ori", type=float, default=None,
                        help="Orientation reward weight")
    parser.add_argument("--mult-w-pos", type=float, default=None,
                        help="Multiplicative: independent pos weight")
    parser.add_argument("--mult-w-ori", type=float, default=None,
                        help="Multiplicative: independent ori weight")
    parser.add_argument("--mult-w-coupled", type=float, default=None,
                        help="Multiplicative: coupled pos*ori weight")
    parser.add_argument("--range-pos", type=float, default=None,
                        help="Multiplicative: RANGE_POS [m]")
    parser.add_argument("--range-ori", type=float, default=None,
                        help="Multiplicative: RANGE_ORI [rad]")
    parser.add_argument("--pos-action-scale", type=float, default=None,
                        help="POS_ACTION_SCALE [m]")
    parser.add_argument("--rot-action-scale", type=float, default=None,
                        help="ROT_ACTION_SCALE [rad]")
    parser.add_argument("--adaptive-pos-scale", action="store_true",
                        help="Enable distance-adaptive pos action scaling")
    parser.add_argument("--fine-threshold", type=float, default=None,
                        help="FINE_THRESHOLD [m] for adaptive scaling")
    parser.add_argument("--min-pos-scale", type=float, default=None,
                        help="MIN_POS_SCALE [m] for adaptive floor")
    parser.add_argument("--precondition-cache", type=str, default=None,
                        help="Path to custom precondition cache .npz")
    parser.add_argument("--terminal-steps", type=int, default=None,
                        help="Override max episode length")
    parser.add_argument("--k-sustain", type=int, default=None,
                        help="Override C5_SUSTAIN_STEPS (default=K_GRASP=5)")
    parser.add_argument("--enable-camera", action="store_true",
                        help="Enable wrist camera rendering (Phase 2 visual obs)")
    # Option C' (2026-04-25): cable XY domain randomization during PPO training.
    # BC demos must also be regenerated with --randomize-cable-xy for distribution
    # match (otherwise BC→PPO mismatch reproduces the fixed-cable plateau).
    parser.add_argument("--randomize-cable-xy", action="store_true",
                        help="Enable cable XY ±CABLE_XY_DR_AMPLITUDE DR at each env reset. "
                             "Default False (backward-compat). Required for Option C' retrain.")


def _create_env(args):
    from newton_approach_cable_env import NewtonApproachCableEnv
    return NewtonApproachCableEnv(
        world_count=args.world_count, device=args.device,
        enable_camera=getattr(args, 'enable_camera', False))


def _apply_overrides(env, args):
    # Option C' (2026-04-25): fresh-init enforcement when cable-DR retrain is active.
    # Prohibits resume from collapsed AC checkpoints (iter 50 model_best.pt eval 0/5)
    # per prohibited.md "崩壊 checkpoint resume 禁止". Only enforced when the caller
    # opts into cable DR, so baseline/ablation resumes stay unaffected.
    if getattr(args, "randomize_cable_xy", False):
        if getattr(args, "resume", None):
            raise RuntimeError(
                f"Option C' cable-DR retrain requires fresh init. "
                f"--resume={args.resume!r} detected. Remove --resume and restart."
            )
        if getattr(args, "base_model", None):
            raise RuntimeError(
                f"Option C' cable-DR retrain requires fresh init. "
                f"--base-model={args.base_model!r} detected. Remove --base-model."
            )
        log_dir = getattr(args, "log_dir", None)
        if log_dir and os.path.isdir(log_dir):
            import glob
            existing_ckpts = sorted(glob.glob(os.path.join(log_dir, "model_*.pt")))
            if existing_ckpts:
                raise RuntimeError(
                    f"log_dir={log_dir} already contains {len(existing_ckpts)} checkpoint(s) "
                    f"(e.g. {os.path.basename(existing_ckpts[0])}). Option C' requires "
                    f"a fresh log_dir to avoid RSL-RL auto-pickup."
                )

    # Option C' (2026-04-25): enable cable XY DR on env before any reset.
    env.set_cable_xy_randomize(getattr(args, "randomize_cable_xy", False))

    ov = {}

    def _set(attr, val):
        if val is not None:
            setattr(env, attr, val)
            ov[attr] = val

    _set("GRASP_BONUS", args.grasp_bonus)
    _set("SUCCESS_BONUS", args.success_bonus)
    _set("STEP_PENALTY", args.step_penalty)
    _set("R_PENALTY", args.r_penalty)
    _set("ALIGN_REWARD_SCALE", args.align_reward_scale)
    _set("ALIGN_GATE_DIST", args.align_gate_dist)
    _set("EPS_POS", args.eps_pos)
    _set("EPS_POS_COARSE", args.eps_pos_coarse)
    _set("EPS_ORI", args.eps_ori)
    _set("REWARD_MODE", args.reward_mode)
    _set("W_ORI", args.w_ori)
    _set("PROGRESS_W_POS", args.mult_w_pos)
    _set("PROGRESS_W_ORI", args.mult_w_ori)
    _set("PROGRESS_W_COUPLED", args.mult_w_coupled)
    _set("RANGE_POS", args.range_pos)
    _set("RANGE_ORI", args.range_ori)
    _set("POS_ACTION_SCALE", args.pos_action_scale)
    _set("ROT_ACTION_SCALE", args.rot_action_scale)
    _set("TERMINAL_STEPS_OVERRIDE", args.terminal_steps)
    _set("C5_SUSTAIN_STEPS", args.k_sustain)
    if args.precondition_cache is not None:
        env.PRECONDITION_CACHE_OVERRIDE = os.path.abspath(args.precondition_cache)
        ov["PRECONDITION_CACHE"] = args.precondition_cache
    if args.adaptive_pos_scale:
        env.ADAPTIVE_POS_SCALE = True
        ov["ADAPTIVE_POS_SCALE"] = True
    _set("FINE_THRESHOLD", args.fine_threshold)
    _set("MIN_POS_SCALE", args.min_pos_scale)
    return ov


def _on_bc_step(pred, act_batch):
    """L/R split BC loss diagnostic (12D action = 6D right + 6D left)."""
    return {
        "DAPG/bc_loss_r": torch.nn.functional.mse_loss(
            pred[:, :6], act_batch[:, :6]).item(),
        "DAPG/bc_loss_l": torch.nn.functional.mse_loss(
            pred[:, 6:], act_batch[:, 6:]).item(),
    }


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
    run_dapg_training(SkillTrainConfig(
        skill_name="ApproachCable",
        skill_tag="TRAIN-A",
        log_dir_prefix="rl_approach_cable_A",
        create_env=_create_env,
        add_skill_args=_add_args,
        apply_env_overrides=_apply_overrides,
        on_bc_step_fn=_on_bc_step,
        compute_best_metric=_best_metric,
        skill_adapter_type="APPROACH_CABLE",
    ))
