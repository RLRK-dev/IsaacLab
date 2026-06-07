#!/usr/bin/env python3
"""Optuna Bayesian hyperparameter sweep for THREAD RL training.

Local-only. No cloud auth required.

Usage:
    source ~/env_isaaclab6/bin/activate

    # Single GPU, 10 trials:
    python thread_isaac_lab/scripts/sweep_optuna.py \
        --skill ApproachCable --device cuda:2 --n-trials 10

    # 3 GPUs parallel (run in separate terminals):
    python thread_isaac_lab/scripts/sweep_optuna.py \
        --skill ApproachCable --device cuda:0 --n-trials 4 --study-name ac-sweep &
    python thread_isaac_lab/scripts/sweep_optuna.py \
        --skill ApproachCable --device cuda:1 --n-trials 3 --study-name ac-sweep &
    python thread_isaac_lab/scripts/sweep_optuna.py \
        --skill ApproachCable --device cuda:2 --n-trials 3 --study-name ac-sweep &

    # View dashboard (use absolute path, not ~):
    optuna-dashboard sqlite:////home/$USER/optuna_sweeps/ac-sweep.db --port 8080
"""

import argparse
import json
import os
import subprocess
import sys
import time

import optuna
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR, "..", "data")
_DEMO_DIR = os.path.join(_SCRIPT_DIR, "..", "data", "bc_demos")

# =========================================================================
# Skill definitions: script, demos, metric, search space
# =========================================================================

SKILLS = {
    "ApproachCable": {
        "script": os.path.join(_SCRIPT_DIR, "train_approach_cable.py"),
        "demos": os.path.join(_DEMO_DIR, "grasp_cable_demos_v24_warmup.npz"),
        "metric_tag": "Episode//metrics/dist_pos_median",
        "ori_metric_tag": "Episode//metrics/dist_ori_median",
        "search_space": {
            "range_ori": {"type": "float", "low": 0.3, "high": 1.0},
            "reward_mode": {"type": "categorical", "choices": ["multiplicative", "hybrid"]},
            "alpha_min": {"type": "float", "low": 0.05, "high": 0.3},
            "range_pos": {"type": "float", "low": 0.010, "high": 0.050},
        },
        "fixed_args": ["--alpha-init", "0.3", "--alpha-anneal-iters", "200",
                        "--entropy-coef", "0.01"],
    },
    "InsertIntoClip": {
        "script": os.path.join(_SCRIPT_DIR, "train_insert_clip.py"),
        "demos": os.path.join(_DEMO_DIR, "insert_clip_demos_v3_orifix.npz"),
        "metric_tag": "Episode//metrics/cable_clip_dist_median",
        "ori_metric_tag": "Episode//metrics/cable_clip_ori_mean",
        "search_space": {
            "range_ori": {"type": "float", "low": 0.3, "high": 1.0},
            "reward_mode": {"type": "categorical", "choices": ["multiplicative", "hybrid"]},
            "alpha_min": {"type": "float", "low": 0.05, "high": 0.3},
        },
        "fixed_args": ["--alpha-init", "0.3", "--alpha-anneal-iters", "100",
                        "--alpha-dist-thresh", "0.030", "--entropy-coef", "0.01"],
    },
    "AerialRegrasp": {
        "script": os.path.join(_SCRIPT_DIR, "train_aerial_regrasp.py"),
        "demos": os.path.join(_DEMO_DIR, "aerial_regrasp_demos_v6_warmup.npz"),
        "metric_tag": "Episode//metrics/dist_pos_median",
        "ori_metric_tag": "Episode//metrics/dist_ori_median",
        "search_space": {
            "range_ori": {"type": "float", "low": 0.3, "high": 1.0},
            "reward_mode": {"type": "categorical", "choices": ["multiplicative", "hybrid"]},
            "alpha_init": {"type": "float", "low": 0.3, "high": 0.7},
            "alpha_min": {"type": "float", "low": 0.05, "high": 0.3},
        },
        "fixed_args": ["--alpha-anneal-iters", "200", "--entropy-coef", "0.01"],
    },
}


def read_tb_metric(log_dir: str, tag: str, last_n: int = 10) -> float | None:
    """Read the average of the last N values of a TensorBoard scalar tag."""
    try:
        ea = EventAccumulator(log_dir)
        ea.Reload()
        scalars = ea.Tags().get("scalars", [])
        if tag not in scalars:
            # Try without Episode/ prefix
            alt_tag = tag.replace("Episode/", "")
            if alt_tag in scalars:
                tag = alt_tag
            else:
                return None
        events = ea.Scalars(tag)
        if not events:
            return None
        values = [e.value for e in events[-last_n:]]
        return sum(values) / len(values)
    except Exception:
        return None


def read_tb_metric_at_step(log_dir: str, tag: str, step: int) -> float | None:
    """Read the TensorBoard scalar value closest to the given step."""
    try:
        ea = EventAccumulator(log_dir)
        ea.Reload()
        scalars = ea.Tags().get("scalars", [])
        if tag not in scalars:
            alt_tag = tag.replace("Episode/", "")
            if alt_tag in scalars:
                tag = alt_tag
            else:
                return None
        events = ea.Scalars(tag)
        if not events:
            return None
        # Find closest step
        closest = min(events, key=lambda e: abs(e.step - step))
        return closest.value
    except Exception:
        return None


def build_command(skill_cfg: dict, trial_params: dict, device: str,
                  max_iters: int, world_count: int, log_dir: str) -> list[str]:
    """Build the training command from trial parameters."""
    cmd = [
        sys.executable, "-u", skill_cfg["script"],
        "--world-count", str(world_count),
        "--max-iterations", str(max_iters),
        "--device", device,
        "--demos", skill_cfg["demos"],
        "--log-dir", log_dir,
        "--verbose",
    ]

    # Fixed args
    cmd.extend(skill_cfg["fixed_args"])

    # Trial-suggested args
    for param, value in trial_params.items():
        cli_name = f"--{param.replace('_', '-')}"
        # Skip if already in fixed_args
        if cli_name in skill_cfg["fixed_args"]:
            continue
        cmd.extend([cli_name, str(value)])

    return cmd


def create_objective(skill_name: str, device: str, max_iters: int,
                     world_count: int, prune_at: int | None):
    """Create an Optuna objective function for the given skill."""
    skill_cfg = SKILLS[skill_name]
    search_space = skill_cfg["search_space"]
    metric_tag = skill_cfg["metric_tag"]

    def objective(trial: optuna.Trial) -> float:
        # Suggest parameters
        params = {}
        for name, spec in search_space.items():
            if spec["type"] == "float":
                params[name] = trial.suggest_float(name, spec["low"], spec["high"])
            elif spec["type"] == "categorical":
                params[name] = trial.suggest_categorical(name, spec["choices"])
            elif spec["type"] == "int":
                params[name] = trial.suggest_int(name, spec["low"], spec["high"])

        # Create unique log directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join(
            _DATA_DIR,
            f"sweep_{skill_name.lower()}_t{trial.number}_{timestamp}",
        )
        os.makedirs(log_dir, exist_ok=True)

        # Build and run command
        cmd = build_command(skill_cfg, params, device, max_iters, world_count, log_dir)
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        print(f"\n[SWEEP] Trial {trial.number}: {param_str}")
        print(f"[SWEEP] Log: {log_dir}")
        print(f"[SWEEP] CMD: {' '.join(cmd[-10:])}")  # last 10 args

        t0 = time.time()

        if prune_at is not None:
            # Run with periodic pruning check
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            # Poll for intermediate results
            while proc.poll() is None:
                time.sleep(60)  # check every 60s
                val = read_tb_metric(log_dir, metric_tag, last_n=3)
                if val is not None:
                    # Find which iteration we're at
                    ea = EventAccumulator(log_dir)
                    ea.Reload()
                    tags = ea.Tags().get("scalars", [])
                    tag = metric_tag if metric_tag in tags else metric_tag.replace("Episode/", "")
                    if tag in tags:
                        events = ea.Scalars(tag)
                        if events:
                            current_step = events[-1].step
                            trial.report(val, current_step)
                            if trial.should_prune():
                                print(f"[SWEEP] Trial {trial.number} PRUNED at step {current_step} (val={val*1000:.1f}mm)")
                                proc.terminate()
                                proc.wait(timeout=30)
                                raise optuna.TrialPruned()
            proc.wait()
        else:
            # Simple: run to completion
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[SWEEP] Trial {trial.number} FAILED (exit {result.returncode})")
                print(result.stderr[-500:] if result.stderr else "no stderr")
                return float("inf")

        elapsed = time.time() - t0
        print(f"[SWEEP] Trial {trial.number} finished in {elapsed/60:.0f}min")

        # Read final metric (average of last 10 iterations)
        dist_median = read_tb_metric(log_dir, metric_tag, last_n=10)
        if dist_median is None:
            print(f"[SWEEP] Trial {trial.number}: could not read metric {metric_tag}")
            return float("inf")

        # Also read ori metric for logging
        ori_metric = read_tb_metric(log_dir, skill_cfg["ori_metric_tag"], last_n=10)

        print(f"[SWEEP] Trial {trial.number} result: dist={dist_median*1000:.1f}mm"
              + (f", ori={ori_metric:.4f}rad" if ori_metric else ""))

        # Store extra info
        trial.set_user_attr("dist_mm", dist_median * 1000)
        trial.set_user_attr("elapsed_min", elapsed / 60)
        trial.set_user_attr("log_dir", log_dir)
        if ori_metric is not None:
            trial.set_user_attr("ori_rad", ori_metric)

        return dist_median  # minimize

    return objective


def main():
    parser = argparse.ArgumentParser(
        description="Optuna Bayesian sweep for THREAD RL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick sweep (50 iter, 10 trials):
  python sweep_optuna.py --skill ApproachCable --device cuda:2 --n-trials 10

  # 3-GPU parallel (same study name):
  python sweep_optuna.py --skill InsertIntoClip --device cuda:0 --n-trials 4 --study-name ic-sweep &
  python sweep_optuna.py --skill InsertIntoClip --device cuda:1 --n-trials 3 --study-name ic-sweep &

  # View dashboard:
  optuna-dashboard sqlite:////home/$USER/optuna_sweeps/ic-sweep.db --port 8080
        """,
    )
    parser.add_argument("--skill", type=str, required=True,
                        choices=list(SKILLS.keys()),
                        help="Skill to sweep")
    parser.add_argument("--device", type=str, default="cuda:0",
                        help="GPU device")
    parser.add_argument("--n-trials", type=int, default=10,
                        help="Number of trials")
    parser.add_argument("--max-iters", type=int, default=50,
                        help="Max iterations per trial (50=fast eval, 200=full)")
    parser.add_argument("--world-count", type=int, default=256,
                        help="Parallel worlds")
    parser.add_argument("--study-name", type=str, default=None,
                        help="Study name (default: sweep-{skill})")
    parser.add_argument("--db-dir", type=str,
                        default=os.path.expanduser("~/optuna_sweeps"),
                        help="Directory for Optuna SQLite databases")
    parser.add_argument("--prune", action="store_true",
                        help="Enable MedianPruner (kill bad trials early)")
    parser.add_argument("--prune-after", type=int, default=20,
                        help="Start pruning after this many iterations")
    args = parser.parse_args()

    os.makedirs(args.db_dir, exist_ok=True)

    study_name = args.study_name or f"sweep-{args.skill.lower()}"
    db_path = os.path.join(args.db_dir, f"{study_name}.db")
    storage = f"sqlite:///{db_path}"

    # Create or load study
    pruner = (
        optuna.pruners.MedianPruner(n_startup_trials=3, n_warmup_steps=args.prune_after)
        if args.prune else optuna.pruners.NopPruner()
    )
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        direction="minimize",
        load_if_exists=True,
        pruner=pruner,
        sampler=optuna.samplers.TPESampler(seed=42),
    )

    print(f"[SWEEP] Skill: {args.skill}")
    print(f"[SWEEP] Device: {args.device}")
    print(f"[SWEEP] Trials: {args.n_trials} (max_iters={args.max_iters})")
    print(f"[SWEEP] Study: {study_name}")
    print(f"[SWEEP] DB: {db_path}")
    print(f"[SWEEP] Prune: {'MedianPruner(after={})'.format(args.prune_after) if args.prune else 'disabled'}")
    print(f"[SWEEP] Search space: {list(SKILLS[args.skill]['search_space'].keys())}")
    print(f"[SWEEP] Dashboard: optuna-dashboard sqlite:///{db_path} --port 8080")
    print()

    objective = create_objective(
        args.skill, args.device, args.max_iters, args.world_count,
        prune_at=args.prune_after if args.prune else None,
    )

    study.optimize(objective, n_trials=args.n_trials)

    # Report results
    print("\n" + "=" * 60)
    print(f"[SWEEP] Study complete: {study_name}")
    print(f"[SWEEP] Best trial: #{study.best_trial.number}")
    print(f"[SWEEP] Best value: {study.best_value * 1000:.1f}mm")
    print(f"[SWEEP] Best params:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")
    if "ori_rad" in study.best_trial.user_attrs:
        print(f"  (ori: {study.best_trial.user_attrs['ori_rad']:.4f} rad)")
    if "log_dir" in study.best_trial.user_attrs:
        print(f"  (log_dir: {study.best_trial.user_attrs['log_dir']})")

    # Summary table
    print(f"\n[SWEEP] All trials:")
    print(f"{'#':>3} {'dist_mm':>8} {'ori_rad':>8} {'time':>6} | params")
    print("-" * 60)
    for t in sorted(study.trials, key=lambda x: x.value if x.value is not None else float("inf")):
        dist = t.user_attrs.get("dist_mm", float("inf"))
        ori = t.user_attrs.get("ori_rad", float("nan"))
        mins = t.user_attrs.get("elapsed_min", 0)
        params = ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
                           for k, v in t.params.items())
        state = "P" if t.state == optuna.trial.TrialState.PRUNED else " "
        print(f"{t.number:>3} {dist:>7.1f}mm {ori:>7.4f}r {mins:>5.0f}m {state}| {params}")


if __name__ == "__main__":
    main()
