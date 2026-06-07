#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared DAPG (PPO + BC auxiliary loss) training infrastructure for THREAD RL skills.

Each skill-specific train_*.py defines a SkillTrainConfig and calls run_dapg_training().
This eliminates code duplication and ensures consistent behavior across all skills.

Usage (from a skill wrapper):
    from train_common import SkillTrainConfig, run_dapg_training
    cfg = SkillTrainConfig(skill_name="ApproachCable", ...)
    run_dapg_training(cfg)
"""

import argparse
import copy
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import torch

# Line buffering for nohup compatibility (all skills)
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


@dataclass
class SkillTrainConfig:
    """Per-skill training configuration passed to run_dapg_training()."""

    # Identity
    skill_name: str        # e.g. "ApproachCable"
    skill_tag: str         # e.g. "TRAIN-A" (log prefix)
    log_dir_prefix: str | Callable  # e.g. "rl_approach_cable_A" or (args) -> str

    # Env creation: (args) -> env
    create_env: Callable

    # Per-skill defaults (overridable via CLI)
    default_world_count: int = 256
    default_alpha_init: float = 0.7
    default_num_steps_per_env: int = 200

    # PPO overrides applied on top of unified defaults
    ppo_overrides: dict = field(default_factory=dict)

    # Optional callbacks
    add_skill_args: Callable | None = None          # (parser) -> None
    apply_env_overrides: Callable | None = None     # (env, args) -> dict
    convert_demos: Callable | None = None           # (obs_np, act_np, env, device) -> (obs_t, act_t)
    custom_get_alpha: Callable | None = None        # (it, args, env) -> float
    compute_best_metric: Callable | None = None     # (env, it, args) -> (name, value, "max"|"min") | None
    on_bc_step_fn: Callable | None = None           # (pred, act_batch) -> dict (extra log)
    per_iter_log_fn: Callable | None = None         # (it, env) -> dict (extra log, called every iter)
    extra_summary_fn: Callable | None = None        # (env, args) -> dict

    # LoRA skill adapter: SkillType attr name, str or (args) -> str
    skill_adapter_type: str | Callable | None = None


def add_common_args(parser: argparse.ArgumentParser, cfg: SkillTrainConfig):
    """Register all common DAPG training CLI arguments."""
    parser.add_argument("--world-count", type=int, default=cfg.default_world_count)
    parser.add_argument("--max-iterations", type=int, default=300)
    parser.add_argument("--num-steps-per-env", type=int,
                        default=cfg.default_num_steps_per_env)
    parser.add_argument("--device", type=str,
                        default=os.environ.get("NEWTON_DEVICE", "auto"))
    parser.add_argument("--log-dir", type=str, default=None)
    parser.add_argument("--save-interval", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed (PPO + torch + np). Default 42 (backward compat).")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume from")
    # DAPG BC auxiliary loss
    parser.add_argument("--demos", type=str, default=None,
                        help="Path to demo .npz (obs, actions) for DAPG BC loss")
    parser.add_argument("--alpha-init", type=float, default=cfg.default_alpha_init,
                        help="Initial BC loss weight")
    parser.add_argument("--alpha-anneal-iters", type=int, default=200,
                        help="Iterations to anneal alpha to alpha_min (linear)")
    parser.add_argument("--alpha-min", type=float, default=0.5,
                        help="Minimum alpha floor (BC maintenance: alpha_min=0.5)")
    parser.add_argument("--surr-loss-max", type=float, default=0.2,
                        help="Surrogate loss spike guard (0=disabled)")
    parser.add_argument("--warmup-critic-iters", type=int, default=0,
                        help="Critic-only warm-up iters on resume (0=disabled)")
    parser.add_argument("--bc-warmup-steps", type=int, default=0,
                        help="BC-only warmup steps before RL (adapter pre-training)")
    parser.add_argument("--bc-batch-size", type=int, default=256)
    parser.add_argument("--bc-updates-per-iter", type=int, default=1)
    parser.add_argument("--bc-grad-clip", type=float, default=1.0,
                        help="BC gradient norm clipping (0=disabled)")
    parser.add_argument("--entropy-coef", type=float, default=0.01,
                        help="PPO entropy coefficient")
    parser.add_argument("--noise-std", type=float, default=None,
                        help="Init noise std (default: 0.1 if --resume, 0.5 otherwise)")
    parser.add_argument("--override-noise-std", type=float, default=None,
                        help="Force noise_std after loading checkpoint")
    parser.add_argument("--noise-std-max", type=float, default=0.3,
                        help="Upper bound for noise_std (0=disabled)")
    parser.add_argument("--load-optimizer", action="store_true",
                        help="Restore optimizer state from checkpoint")
    parser.add_argument("--base-model", type=str, default=None,
                        help="Path to base model for LoRA skill adapter")
    parser.add_argument("--lora-rank", type=int, default=8,
                        help="LoRA rank for skill adapter")
    parser.add_argument("--wandb", action="store_true",
                        help="Enable wandb logging (offline)")
    parser.add_argument("--wandb-project", type=str, default="thread-rl")
    # Convergence auto-stop
    from convergence_monitor import ConvergenceMonitor
    ConvergenceMonitor.add_argparse_args(parser)


def _build_ppo_config(args, cfg: SkillTrainConfig) -> dict:
    """Build unified PPO config with per-skill overrides."""
    cfg_max_iter = max(args.max_iterations, 10000)
    noise_std = (args.noise_std if args.noise_std is not None
                 else (0.1 if args.resume else 0.5))

    algo = {
        "class_name": "PPO",
        "learning_rate": 3e-4,
        "num_learning_epochs": 10,
        "num_mini_batches": min(args.world_count, 4),
        "gamma": 0.99,
        "lam": 0.95,
        "clip_param": 0.2,
        "entropy_coef": args.entropy_coef,
        "max_grad_norm": 1.0,
        "value_loss_coef": 0.5,
        "use_clipped_value_loss": True,
        "desired_kl": 0.05,
        "schedule": "adaptive",
    }
    algo.update(cfg.ppo_overrides)

    return {
        "seed": args.seed,
        "device": args.device,
        "num_steps_per_env": args.num_steps_per_env,
        "max_iterations": cfg_max_iter,
        "save_interval": args.save_interval,
        "empirical_normalization": False,
        "policy": {
            "class_name": "ActorCritic",
            "actor_hidden_dims": [128, 128],
            "critic_hidden_dims": [128, 128],
            "activation": "elu",
            "init_noise_std": noise_std,
        },
        "algorithm": algo,
    }


def _default_get_alpha(it, args, _env):
    """Linear annealing: alpha_init -> alpha_min over anneal_iters."""
    if it >= args.alpha_anneal_iters:
        return args.alpha_min
    t = it / args.alpha_anneal_iters
    return args.alpha_init + t * (args.alpha_min - args.alpha_init)


def run_dapg_training(cfg: SkillTrainConfig):
    """Run DAPG (PPO + BC auxiliary) training for any THREAD RL skill.

    Handles the complete lifecycle: arg parsing, env creation, PPO setup,
    demo loading, DAPG training loop, convergence monitoring, and summary.
    """
    tag = cfg.skill_tag

    # --- Argument parsing ---
    parser = argparse.ArgumentParser(
        description=f"RSL-RL PPO+DAPG {cfg.skill_name}")
    add_common_args(parser, cfg)
    if cfg.add_skill_args:
        cfg.add_skill_args(parser)
    args = parser.parse_args()

    # Consistent validation across all skills
    if args.alpha_min < 0:
        parser.error("--alpha-min must be >= 0")
    if args.alpha_min >= args.alpha_init:
        parser.error(
            f"--alpha-min ({args.alpha_min}) must be < --alpha-init ({args.alpha_init})")

    from gpu_utils import resolve_device, snapshot_env_config
    args.device = resolve_device(args.device)
    os.environ["NEWTON_DEVICE"] = args.device

    try:
        from rsl_rl.runners import OnPolicyRunner
    except ImportError:
        print(f"[{tag}] ERROR: rsl_rl not installed. pip install rsl-rl-lib")
        sys.exit(1)

    # --- Output directory ---
    if args.log_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        prefix = cfg.log_dir_prefix
        if callable(prefix):
            prefix = prefix(args)
        args.log_dir = os.path.join(
            script_dir, "..", "data",
            f"{prefix}_w{args.world_count}_{ts}",
        )
    os.makedirs(args.log_dir, exist_ok=True)

    print(f"[{tag}] Log dir: {args.log_dir}")
    print(f"[{tag}] Device: {args.device}")
    print(f"[{tag}] World count: {args.world_count}")
    print(f"[{tag}] Max iterations: {args.max_iterations}")
    print(f"[{tag}] Steps/env: {args.num_steps_per_env}")
    total_steps = args.max_iterations * args.num_steps_per_env * args.world_count
    print(f"[{tag}] Total env steps: {total_steps:,}")

    # --- Env ---
    print(f"[{tag}] Creating {cfg.skill_name} environment...")
    env = cfg.create_env(args)

    overrides = {}
    if cfg.apply_env_overrides:
        overrides = cfg.apply_env_overrides(env, args) or {}
        if overrides:
            print(f"[{tag}] Env overrides: {overrides}")

    # --- PPO Runner ---
    train_cfg = _build_ppo_config(args, cfg)

    print(f"[{tag}] Creating OnPolicyRunner...")
    runner = OnPolicyRunner(
        env=env, train_cfg=train_cfg,
        log_dir=args.log_dir, device=args.device,
    )

    # --- Checkpoint / LoRA adapter ---
    adapter_type = cfg.skill_adapter_type
    if callable(adapter_type):
        adapter_type = adapter_type(args)

    if args.base_model and adapter_type:
        from models.skill_adapter import (
            apply_skill_adapter, SkillType, SkillAdapterConfig)
        skill_type = getattr(SkillType, adapter_type)
        print(f"[{tag}] Skill adapter from: {args.base_model}")
        adapter_cfg = SkillAdapterConfig(lora_rank=args.lora_rank)
        apply_skill_adapter(runner, args.base_model, skill_type,
                            adapter_config=adapter_cfg)
        if args.resume:
            print(f"[{tag}] Resuming adapter from: {args.resume}")
            ckpt = torch.load(
                args.resume, map_location=args.device, weights_only=False)
            runner.alg.policy.load_state_dict(ckpt["model_state_dict"])
            if args.load_optimizer and "optimizer_state_dict" in ckpt:
                runner.alg.optimizer.load_state_dict(
                    ckpt["optimizer_state_dict"])
                print(f"[{tag}] Adapter weights + optimizer restored")
            else:
                print(f"[{tag}] Adapter weights restored (optimizer reset)")
            if args.override_noise_std is not None:
                old = runner.alg.policy.std.data.clone()
                runner.alg.policy.std.data.fill_(args.override_noise_std)
                print(f"[{tag}] sigma override: "
                      f"{old.mean().item():.4f} -> {args.override_noise_std}")
        # Clamp noise_std immediately after adapter creation/loading
        # to prevent first-iteration rollout with hardcoded std=0.5
        if args.noise_std_max and args.noise_std_max > 0:
            cur = runner.alg.policy.std.data.mean().item()
            if cur > args.noise_std_max:
                runner.alg.policy.std.data.clamp_(max=args.noise_std_max)
                print(f"[{tag}] post-adapter sigma clamp: "
                      f"{cur:.4f} -> {args.noise_std_max}")
    elif args.resume:
        print(f"[{tag}] Loading checkpoint: {args.resume}")
        runner.load(args.resume, load_optimizer=args.load_optimizer)
        opt_msg = "restored" if args.load_optimizer else "reset"
        print(f"[{tag}] Weights loaded (optimizer {opt_msg})")
        if args.override_noise_std is not None:
            old = runner.alg.policy.std.data.clone()
            runner.alg.policy.std.data.fill_(args.override_noise_std)
            print(f"[{tag}] sigma override: "
                  f"{old.mean().item():.4f} -> {args.override_noise_std}")

    # Phase 3: add visual encoder trainable params to PPO optimizer
    if hasattr(env, 'visual_encoder_params'):
        enc_params = env.visual_encoder_params()
        if enc_params:
            runner.alg.optimizer.add_param_group({
                'params': enc_params,
                'lr': 3e-4,
            })
            n_enc = sum(p.numel() for p in enc_params)
            print(f"[{tag}] Visual encoder projection added to optimizer: {n_enc} params")

    # --- Demos ---
    if not args.demos:
        print(f"[{tag}] ERROR: --demos is required.")
        sys.exit(1)

    print(f"[{tag}] Loading demos: {args.demos}")
    dd = np.load(args.demos)
    raw_obs, raw_act = dd["obs"], dd["actions"]
    print(f"[{tag}] Raw demos: {raw_obs.shape[0]} transitions, "
          f"obs={raw_obs.shape[1]}D, act={raw_act.shape[1]}D")
    if cfg.convert_demos:
        demo_obs, demo_act = cfg.convert_demos(
            raw_obs, raw_act, env, args.device)
        print(f"[{tag}] Converted: {demo_obs.shape[0]} transitions, "
              f"obs={demo_obs.shape[1]}D, act={demo_act.shape[1]}D")
    else:
        # L1 fix: Normalize quaternions to w >= 0 (double-cover consistency)
        # 42D/45D layout: R_quat@3, L_quat@11, cable_quat@19, clip_quat@26
        obs_dim = raw_obs.shape[1]
        quat_starts = [qs for qs in [3, 11, 19, 26] if qs + 4 <= obs_dim]
        n_flipped = 0
        for qs in quat_starts:
            w = raw_obs[:, qs + 3]
            neg_mask = w < 0
            n_neg = neg_mask.sum()
            if n_neg > 0:
                raw_obs[neg_mask, qs:qs+4] *= -1
                n_flipped += n_neg
        if n_flipped > 0:
            print(f"[{tag}] L1 quat fix: flipped {n_flipped} negative-w quaternions "
                  f"across {len(quat_starts)} quat fields")
        demo_obs = torch.tensor(
            raw_obs, dtype=torch.float32, device=args.device)
        demo_act = torch.tensor(
            raw_act, dtype=torch.float32, device=args.device)
    # Phase 3: pad demos if env has visual obs (extra dims beyond base state obs)
    if demo_obs.shape[1] < env.num_obs:
        n_pad = env.num_obs - demo_obs.shape[1]
        pad = torch.zeros(demo_obs.shape[0], n_pad,
                          dtype=demo_obs.dtype, device=demo_obs.device)
        demo_obs = torch.cat([demo_obs, pad], dim=1)
        print(f"[{tag}] Demo obs padded: {demo_obs.shape[1] - n_pad}D → {demo_obs.shape[1]}D "
              f"(visual dims zero-filled, BC loss via SkillAdapter base_obs only)")
    assert demo_obs.shape[1] == env.num_obs, (
        f"Demo obs dim {demo_obs.shape[1]} != env obs dim {env.num_obs}")
    assert demo_act.shape[1] == env.num_actions, (
        f"Demo act dim {demo_act.shape[1]} != env action dim {env.num_actions}")
    demo_n = demo_obs.shape[0]

    bc_loss_fn = torch.nn.MSELoss()
    bc_params = list(runner.alg.policy.actor.parameters())
    bc_optimizer = torch.optim.Adam(bc_params, lr=3e-4)
    print(f"[{tag}] DAPG: alpha_init={args.alpha_init}, alpha_min={args.alpha_min}, "
          f"anneal={args.alpha_anneal_iters}, bc_batch={args.bc_batch_size}, "
          f"bc_updates={args.bc_updates_per_iter}, bc_clip={args.bc_grad_clip}")
    print(f"[{tag}] BC uses separate optimizer (L4 fix: no critic momentum corruption)")

    # --- BC warmup (adapter pre-training on demos before RL) ---
    if args.bc_warmup_steps > 0 and demo_n > 0:
        print(f"[{tag}] BC warmup: {args.bc_warmup_steps} steps")
        for wi in range(args.bc_warmup_steps):
            idx = torch.randint(
                0, demo_n, (args.bc_batch_size,), device=args.device)
            obs_b = demo_obs[idx]
            act_b = demo_act[idx]
            pred = runner.alg.policy.actor(obs_b)
            loss_bc = bc_loss_fn(pred, act_b)
            bc_optimizer.zero_grad()
            loss_bc.backward()
            if args.bc_grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(bc_params, args.bc_grad_clip)
            bc_optimizer.step()
            if wi % 100 == 0 or wi == args.bc_warmup_steps - 1:
                print(f"[{tag}] BC warmup step={wi} bc_loss={loss_bc.item():.6f}")
        print(f"[{tag}] BC warmup complete. Final bc_loss={loss_bc.item():.6f}")

    # --- MLflow ---
    from mlflow_utils import setup_mlflow_tracking, log_bc_metrics, finish_mlflow
    mlflow_params = {
        "skill": cfg.skill_name,
        "world_count": args.world_count,
        "max_iterations": args.max_iterations,
        "num_steps_per_env": args.num_steps_per_env,
        "device": args.device,
        "alpha_init": args.alpha_init,
        "alpha_min": args.alpha_min,
        "alpha_anneal_iters": args.alpha_anneal_iters,
        "bc_batch_size": args.bc_batch_size,
        "bc_grad_clip": args.bc_grad_clip,
        "entropy_coef": args.entropy_coef,
        "noise_std_max": args.noise_std_max,
        "base_model": args.base_model or "",
        "lora_rank": args.lora_rank if args.base_model else 0,
        "demos": args.demos or "",
        "resume": args.resume or "",
    }
    mlflow_params.update(overrides)
    writer = setup_mlflow_tracking(
        experiment="THREAD-RL",
        run_name=f"{cfg.skill_name}_{os.path.basename(args.log_dir)}",
        params=mlflow_params, log_dir=args.log_dir,
        tags={"skill": cfg.skill_name},
    )
    runner.writer = writer
    runner.logger_type = "tensorboard"
    print(f"[{tag}] MLflow tracking enabled: experiment=THREAD-RL")

    # --- Surr loss spike guard ---
    _last_loss_dict = {}
    _orig_update = runner.alg.update

    def _patched_update():
        ld = _orig_update()
        _last_loss_dict.update(ld)
        return ld

    runner.alg.update = _patched_update

    # --- Critic warm-up on resume ---
    if args.warmup_critic_iters > 0 and args.resume:
        print(f"[{tag}] Critic warm-up: {args.warmup_critic_iters} iters (actor frozen)")
        for p in runner.alg.policy.actor.parameters():
            p.requires_grad_(False)
        runner.alg.policy.std.requires_grad_(False)
        for wi in range(args.warmup_critic_iters):
            runner.learn(num_learning_iterations=1, init_at_random_ep_len=False)
            vl = _last_loss_dict.get("value_function", float("nan"))
            if wi % 5 == 0 or wi == args.warmup_critic_iters - 1:
                print(f"[{tag}] warmup iter={wi} value_loss={vl:.4f}")
        for p in runner.alg.policy.actor.parameters():
            p.requires_grad_(True)
        runner.alg.policy.std.requires_grad_(True)
        print(f"[{tag}] Critic warm-up complete. value_loss={vl:.4f}")
        # Reset runner counter so main loop checkpoints start at 0
        runner.current_learning_iteration = 0

    # --- Convergence monitor ---
    from convergence_monitor import ConvergenceMonitor
    monitor = ConvergenceMonitor.from_args(args)
    monitor.log_dir = args.log_dir
    monitor.skill_tag = tag
    monitor.patch_runner(runner)
    if args.patience > 0:
        print(f"[{tag}] Auto-stop: metric={monitor.metric}, "
              f"patience={monitor.patience}, min_iter={monitor.min_iterations}, "
              f"delta={monitor.delta}")
    else:
        print(f"[{tag}] Auto-stop: disabled (patience=0)")

    # --- Training loop ---
    print(f"[{tag}] Starting training: {args.max_iterations} iterations")
    t0 = time.time()
    get_alpha = cfg.custom_get_alpha or _default_get_alpha

    bc_losses = []
    best_val = None
    best_name = None
    best_iter = -1
    surr_rollback_count = 0

    for it in range(args.max_iterations):
        # Snapshot for surr_loss rollback
        if args.surr_loss_max > 0:
            _snap = {k: v.clone()
                     for k, v in runner.alg.policy.state_dict().items()}
            _opt_snap = copy.deepcopy(runner.alg.optimizer.state_dict())

        # 1. PPO step
        runner.learn(num_learning_iterations=1, init_at_random_ep_len=False)

        # 1a. Surr spike guard
        surr = _last_loss_dict.get("surrogate", 0.0)
        if args.surr_loss_max > 0 and surr > args.surr_loss_max:
            surr_rollback_count += 1
            print(f"[{tag}] SURR SPIKE iter={it}: {surr:.4f} > "
                  f"{args.surr_loss_max} -> ROLLBACK #{surr_rollback_count}")
            runner.alg.policy.load_state_dict(_snap)
            runner.alg.optimizer.load_state_dict(_opt_snap)
            monitor.step(it)  # track iteration even on rollback
            continue

        # 1b. Noise clamp
        if args.noise_std_max and args.noise_std_max > 0:
            with torch.no_grad():
                cur = runner.alg.policy.std.data.mean().item()
                runner.alg.policy.std.data.clamp_(max=args.noise_std_max)
                if cur > args.noise_std_max and (it % 50 == 0 or args.verbose):
                    print(f"[{tag}] iter={it} noise_std clamped: "
                          f"{cur:.4f} -> {args.noise_std_max}")

        # 2. BC auxiliary
        alpha = get_alpha(it, args, env)
        bc_loss_val = 0.0
        bc_extra = {}
        if alpha > 0 and demo_n > 0:
            for _ in range(args.bc_updates_per_iter):
                idx = torch.randint(
                    0, demo_n, (args.bc_batch_size,), device=args.device)
                obs_b = demo_obs[idx]
                act_b = demo_act[idx]
                pred = runner.alg.policy.actor(obs_b)
                loss_bc = bc_loss_fn(pred, act_b)
                bc_optimizer.zero_grad()
                (alpha * loss_bc).backward()
                if args.bc_grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(
                        bc_params, args.bc_grad_clip)
                bc_optimizer.step()
            bc_loss_val = float(loss_bc.item())
            bc_losses.append(bc_loss_val)
            if cfg.on_bc_step_fn:
                with torch.no_grad():
                    bc_extra = cfg.on_bc_step_fn(pred, act_b)

        # Per-iteration extras (always, even when alpha=0)
        iter_extra = {}
        if cfg.per_iter_log_fn:
            iter_extra = cfg.per_iter_log_fn(it, env)
        log_bc_metrics(it, bc_loss_val, alpha, **bc_extra, **iter_extra)
        if args.verbose or it % 10 == 0:
            bc_extra_str = ""
            if bc_extra:
                bc_extra_str = " " + " ".join(
                    f"{k.split('/')[-1]}={v:.4f}" for k, v in bc_extra.items())
            print(f"[{tag}] iter={it} alpha={alpha:.4f} "
                  f"bc_loss={bc_loss_val:.6f}{bc_extra_str}")

        # 3. Best-model save (skill-specific metric)
        if cfg.compute_best_metric:
            result = cfg.compute_best_metric(env, it, args)
            if result is not None:
                name, val, mode = result
                improved = (best_val is None
                            or (mode == "max" and val > best_val)
                            or (mode == "min" and val < best_val))
                if improved:
                    best_val = val
                    best_name = name
                    best_iter = it
                    bp = os.path.join(args.log_dir, "model_best.pt")
                    runner.save(bp)
                    print(f"[{tag}] Best model: iter={it} {name}={val:.4f}")

        # 4. Convergence check
        should_stop, reason = monitor.step(it)
        if should_stop:
            print(f"[{tag}] AUTO-STOP iter={it}: {reason}")
            break

    # --- Summary ---
    elapsed = time.time() - t0
    # Actual iterations completed (including rollbacks which consume env steps)
    actual_iters = it + 1 if args.max_iterations > 0 else 0
    actual_total_steps = actual_iters * args.num_steps_per_env * args.world_count
    print(f"\n[{tag}] Training complete in {elapsed:.0f}s")
    print(f"[{tag}] Actual iterations: {actual_iters}/{args.max_iterations} "
          f"(rollbacks: {surr_rollback_count})")
    print(f"[{tag}] Total env steps: {actual_total_steps:,}")
    if elapsed > 0:
        print(f"[{tag}] Throughput: {actual_total_steps / elapsed:.0f} steps/s")

    summary = {
        "experiment": cfg.skill_name,
        "framework": "RSL-RL",
        "base_model": args.base_model,
        "lora_rank": args.lora_rank if args.base_model else None,
        "world_count": args.world_count,
        "max_iterations": args.max_iterations,
        "actual_iterations": actual_iters,
        "num_steps_per_env": args.num_steps_per_env,
        "total_env_steps": actual_total_steps,
        "elapsed_s": elapsed,
        "throughput_steps_per_s": actual_total_steps / elapsed if elapsed > 0 else 0,
        "device": args.device,
        "surr_rollback_count": surr_rollback_count,
        "ppo": {
            "entropy_coef": args.entropy_coef,
            "init_noise_std": train_cfg["policy"]["init_noise_std"],
            "noise_std_max": args.noise_std_max,
            "override_noise_std": args.override_noise_std,
        },
        "dapg": {
            "demos": args.demos,
            "alpha_init": args.alpha_init,
            "alpha_min": args.alpha_min,
            "alpha_anneal_iters": args.alpha_anneal_iters,
            "bc_updates_per_iter": args.bc_updates_per_iter,
            "bc_grad_clip": args.bc_grad_clip,
            "bc_losses": bc_losses,
        },
        "env_config": snapshot_env_config(env),
        "convergence": monitor.summary(),
    }
    if best_name is not None:
        summary["best_model"] = {
            "metric": best_name,
            "value": best_val,
            "iter": best_iter,
        }
    if cfg.extra_summary_fn:
        summary.update(cfg.extra_summary_fn(env, args))

    with open(os.path.join(args.log_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[{tag}] Summary saved to {args.log_dir}/summary.json")

    finish_mlflow()

    if hasattr(env, "close"):
        env.close()
