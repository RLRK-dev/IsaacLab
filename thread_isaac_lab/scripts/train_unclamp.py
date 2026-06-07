# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RSL-RL PPO training for Unclamp skill — Multi-world.

Uses NewtonUnclampEnv with N parallel worlds via Newton replicate() + SolverVBD.
Supports pure RL and DAPG (BC auxiliary loss).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_unclamp.py \
        --world-count 256 --max-iterations 200 --device cuda:0 --demos PATH
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_pkg_dir = os.path.join(_script_dir, "..")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _pkg_dir)


def main():
    parser = argparse.ArgumentParser(description="RSL-RL PPO Unclamp")
    parser.add_argument("--world-count", type=int, default=256)
    parser.add_argument("--max-iterations", type=int, default=200)
    parser.add_argument("--num-steps-per-env", type=int, default=100)
    parser.add_argument("--device", type=str,
                        default=os.environ.get("NEWTON_DEVICE", "auto"))
    parser.add_argument("--log-dir", type=str, default=None)
    parser.add_argument("--save-interval", type=int, default=50)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--resume", type=str, default=None)
    # DAPG
    parser.add_argument("--demos", type=str, default=None)
    parser.add_argument("--alpha-init", type=float, default=0.3)
    parser.add_argument("--alpha-anneal-iters", type=int, default=100)
    parser.add_argument("--alpha-min", type=float, default=0.0)
    parser.add_argument("--bc-batch-size", type=int, default=256)
    parser.add_argument("--bc-grad-clip", type=float, default=1.0)
    parser.add_argument("--bc-updates-per-iter", type=int, default=1)
    # Reward overrides
    parser.add_argument("--range-seated", type=float, default=None)
    parser.add_argument("--range-ori", type=float, default=None)
    parser.add_argument("--pos-action-scale", type=float, default=None)
    parser.add_argument("--finger-action-scale", type=float, default=None)
    parser.add_argument("--precondition-cache", type=str, default=None)
    parser.add_argument("--terminal-steps", type=int, default=None)
    # PPO tuning
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--noise-std", type=float, default=None)
    parser.add_argument("--override-noise-std", type=float, default=None)
    # Skill adapter
    parser.add_argument("--base-model", type=str, default=None)
    parser.add_argument("--lora-rank", type=int, default=8)
    # Logging
    parser.add_argument("--wandb", action="store_true")
    parser.add_argument("--wandb-project", type=str, default="thread-rl")
    args = parser.parse_args()

    from gpu_utils import resolve_device, snapshot_env_config
    args.device = resolve_device(args.device)
    os.environ["NEWTON_DEVICE"] = args.device

    try:
        from rsl_rl.runners import OnPolicyRunner
    except ImportError:
        print("[TRAIN] ERROR: rsl_rl not installed. pip install rsl-rl-lib")
        sys.exit(1)

    from newton_unclamp_env import NewtonUnclampEnv

    if args.log_dir is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        args.log_dir = os.path.join(
            _script_dir, "..", "data",
            f"rl_unclamp_w{args.world_count}_{timestamp}",
        )
    os.makedirs(args.log_dir, exist_ok=True)

    print(f"[TRAIN-UC] Log dir: {args.log_dir}")
    print(f"[TRAIN-UC] Device: {args.device}")
    print(f"[TRAIN-UC] World count: {args.world_count}")
    print(f"[TRAIN-UC] Max iterations: {args.max_iterations}")
    total_steps = args.max_iterations * args.num_steps_per_env * args.world_count
    print(f"[TRAIN-UC] Total env steps: {total_steps:,}")

    env = NewtonUnclampEnv(world_count=args.world_count, device=args.device)

    # Apply overrides
    overrides = {}
    if args.range_seated is not None:
        env.RANGE_SEATED = args.range_seated
        overrides["RANGE_SEATED"] = args.range_seated
    if args.range_ori is not None:
        env.RANGE_ORI = args.range_ori
        overrides["RANGE_ORI"] = args.range_ori
    if args.pos_action_scale is not None:
        env.POS_ACTION_SCALE = args.pos_action_scale
        overrides["POS_ACTION_SCALE"] = args.pos_action_scale
    if args.finger_action_scale is not None:
        env.FINGER_ACTION_SCALE = args.finger_action_scale
        overrides["FINGER_ACTION_SCALE"] = args.finger_action_scale
    if args.precondition_cache is not None:
        env.PRECONDITION_CACHE_OVERRIDE = os.path.abspath(args.precondition_cache)
        overrides["PRECONDITION_CACHE"] = args.precondition_cache
    if args.terminal_steps is not None:
        env.TERMINAL_STEPS_OVERRIDE = args.terminal_steps
        env.max_episode_length = args.terminal_steps
        overrides["TERMINAL_STEPS"] = args.terminal_steps
    if overrides:
        print(f"[TRAIN-UC] Overrides: {overrides}")

    train_cfg = {
        "seed": 42,
        "device": args.device,
        "num_steps_per_env": args.num_steps_per_env,
        "max_iterations": args.max_iterations,
        "save_interval": args.save_interval,
        "empirical_normalization": False,
        "policy": {
            "class_name": "ActorCritic",
            "actor_hidden_dims": [128, 128],
            "critic_hidden_dims": [128, 128],
            "activation": "elu",
            "init_noise_std": args.noise_std if args.noise_std is not None else (
                0.1 if args.resume else 0.5),
        },
        "algorithm": {
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
        },
    }

    runner = OnPolicyRunner(env=env, train_cfg=train_cfg,
                            log_dir=args.log_dir, device=args.device)

    if args.base_model:
        try:
            from models.skill_adapter import apply_skill_adapter, SkillType, SkillAdapterConfig
        except ImportError:
            print("[TRAIN-UC] ERROR: models.skill_adapter not found. "
                  "--base-model requires the skill_adapter module.")
            sys.exit(1)
        print(f"[TRAIN-UC] Skill adapter from: {args.base_model}")
        cfg = SkillAdapterConfig(lora_rank=args.lora_rank)
        apply_skill_adapter(runner, args.base_model, SkillType.UNCLAMP,
                            adapter_config=cfg)
    if args.resume:
        print(f"[TRAIN-UC] Loading checkpoint: {args.resume}")
        runner.load(args.resume, load_optimizer=False)
        if args.override_noise_std is not None:
            runner.alg.policy.std.data.fill_(args.override_noise_std)

    # DAPG or pure RL
    use_dapg = args.demos is not None
    bc_losses = []

    if use_dapg:
        print(f"[TRAIN-UC] DAPG mode: demos={args.demos}")
        demo_data = np.load(args.demos)
        demo_obs = torch.tensor(demo_data["obs"], dtype=torch.float32,
                                device=args.device)
        demo_act = torch.tensor(demo_data["actions"], dtype=torch.float32,
                                device=args.device)
        assert demo_obs.shape[1] == env.num_obs
        assert demo_act.shape[1] == env.num_actions
        bc_loss_fn = torch.nn.MSELoss()
        demo_n = demo_obs.shape[0]

        def get_alpha(iteration):
            if iteration >= args.alpha_anneal_iters:
                return args.alpha_min
            t = iteration / args.alpha_anneal_iters
            return args.alpha_init + t * (args.alpha_min - args.alpha_init)

    # wandb
    _wandb_enabled = False
    if args.wandb:
        os.environ["WANDB_MODE"] = "offline"
        import wandb
        run_name = os.path.basename(args.log_dir)
        wandb.init(project=args.wandb_project, name=run_name,
                   config={"skill": "Unclamp", **overrides})
        from torch.utils.tensorboard import SummaryWriter
        _tb_writer = SummaryWriter(log_dir=args.log_dir, flush_secs=10)
        _orig = _tb_writer.add_scalar

        def _dual(tag, val, step=None, **kw):
            _orig(tag, val, step, **kw)
            wandb.log({tag: val}, step=step)

        _tb_writer.add_scalar = _dual
        runner.writer = _tb_writer
        runner.logger_type = "tensorboard"
        _wandb_enabled = True

    print(f"[TRAIN-UC] Starting training: {args.max_iterations} iterations")
    t0 = time.time()

    for it in range(args.max_iterations):
        runner.learn(num_learning_iterations=1, init_at_random_ep_len=False)

        if use_dapg:
            alpha = get_alpha(it)
            if alpha > 0:
                for _ in range(args.bc_updates_per_iter):
                    idx = torch.randint(0, demo_n, (args.bc_batch_size,),
                                        device=args.device)
                    pred = runner.alg.policy.actor(demo_obs[idx])
                    loss_bc = bc_loss_fn(pred, demo_act[idx])
                    runner.alg.optimizer.zero_grad()
                    (alpha * loss_bc).backward()
                    if args.bc_grad_clip > 0:
                        torch.nn.utils.clip_grad_norm_(
                            runner.alg.policy.actor.parameters(),
                            args.bc_grad_clip)
                    runner.alg.optimizer.step()
                bc_losses.append(float(loss_bc.item()))
                if _wandb_enabled:
                    wandb.log({"DAPG/bc_loss": loss_bc.item(),
                               "DAPG/alpha": alpha}, step=it)
                if args.verbose or it % 50 == 0:
                    print(f"[TRAIN-UC] iter={it} alpha={alpha:.4f} "
                          f"bc_loss={loss_bc.item():.6f}")

    if _wandb_enabled:
        wandb.finish()

    elapsed = time.time() - t0
    print(f"\n[TRAIN-UC] Training complete in {elapsed:.0f}s")
    print(f"[TRAIN-UC] Throughput: {total_steps / elapsed:.0f} env steps/s")

    summary = {
        "experiment": "Unclamp",
        "world_count": args.world_count,
        "max_iterations": args.max_iterations,
        "total_env_steps": total_steps,
        "elapsed_s": elapsed,
        "device": args.device,
        "dapg": {
            "demos": args.demos,
            "alpha_init": args.alpha_init,
            "alpha_min": args.alpha_min,
            "bc_losses": bc_losses,
        } if use_dapg else None,
        "env_config": snapshot_env_config(env),
    }
    with open(os.path.join(args.log_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
