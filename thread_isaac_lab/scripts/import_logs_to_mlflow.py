#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Import existing training log files into MLflow.

Parses RSL-RL stdout logs and extracts per-iteration metrics.
Use this to backfill MLflow for training runs that started without MLflow.

Usage:
    python import_logs_to_mlflow.py \
        --log /tmp/train_grip_v19_cuda0.log \
        --experiment THREAD-RL \
        --run-name "Grip_v19"

    # Import all 4 current runs:
    python import_logs_to_mlflow.py --all-current
"""

import argparse
import re
import sys

import mlflow

TRACKING_URI = "sqlite:///home/rlrk/mlflow_data/mlflow.db"

# Current running logs
CURRENT_RUNS = [
    {"log": "/tmp/train_ac_v21_cuda2.log", "run_name": "AC_v21", "skill": "ApproachCable"},
    {"log": "/tmp/train_ar_v32_cuda2.log", "run_name": "AR_v32", "skill": "AerialRegrasp"},
    {"log": "/tmp/train_ic_v29_cuda0.log", "run_name": "IC_v29", "skill": "InsertIntoClip"},
    {"log": "/tmp/train_grip_v19_cuda0.log", "run_name": "Grip_v19", "skill": "Grip_clamp"},
]


def parse_log(path: str) -> list[dict]:
    """Parse RSL-RL training log into per-iteration metric dicts."""
    with open(path) as f:
        text = f.read()

    iterations = []
    # Split by iteration headers
    blocks = re.split(r"#{60,}", text)

    for block in blocks:
        metrics = {}

        # Extract iteration number
        m = re.search(r"Learning iteration\s+(\d+)/(\d+)", block)
        if not m:
            continue
        it = int(m.group(1))
        metrics["_iter"] = it

        # RSL-RL standard metrics
        for pattern, key in [
            (r"Mean value_function loss:\s+([\d.e+-]+)", "Loss/value_function"),
            (r"Mean surrogate loss:\s+([\d.e+-]+)", "Loss/surrogate"),
            (r"Mean entropy loss:\s+([\d.e+-]+)", "Loss/entropy"),
            (r"Mean action noise std:\s+([\d.e+-]+)", "Policy/mean_noise_std"),
            (r"Mean reward:\s+([\d.e+-]+)", "Train/mean_reward"),
            (r"Mean episode length:\s+([\d.e+-]+)", "Train/mean_episode_length"),
            (r"Total timesteps:\s+(\d+)", "Perf/total_timesteps"),
        ]:
            m2 = re.search(pattern, block)
            if m2:
                metrics[key] = float(m2.group(1))

        # Episode/env metrics: /metrics/*, /reward/*, /episode/*
        for m3 in re.finditer(r"((?:/\w+)+):\s+([\d.e+-]+)", block):
            tag = m3.group(1).strip()
            val = float(m3.group(2))
            metrics[tag] = val

        # DAPG BC lines: [TRAIN-*] iter=N alpha=... bc_loss=...
        for m4 in re.finditer(
            r"\[TRAIN-\w+\]\s+iter=(\d+)\s+alpha=([\d.]+)\s+bc_loss=([\d.e+-]+)",
            block,
        ):
            dapg_iter = int(m4.group(1))
            if dapg_iter == it:
                metrics["DAPG/alpha"] = float(m4.group(2))
                metrics["DAPG/bc_loss"] = float(m4.group(3))
                # Optional R/L split
                rest = block[m4.end():]
                mr = re.match(r"\s+R=([\d.e+-]+)", rest)
                if mr:
                    metrics["DAPG/bc_loss_r"] = float(mr.group(1))
                ml = re.search(r"L=([\d.e+-]+)", rest[:60] if rest else "")
                if ml:
                    metrics["DAPG/bc_loss_l"] = float(ml.group(1))

        # Best model save
        for m5 in re.finditer(
            r"Best model saved: iter=(\d+) auto_close=([\d.]+)", block
        ):
            if int(m5.group(1)) == it:
                metrics["best/auto_close"] = float(m5.group(2))

        # Noise std clamp
        for m6 in re.finditer(
            r"noise_std clamped: ([\d.]+) -> ([\d.]+)", block
        ):
            metrics["Policy/noise_std_pre_clamp"] = float(m6.group(1))

        if len(metrics) > 1:  # more than just _iter
            iterations.append(metrics)

    return iterations


def extract_params(path: str) -> dict:
    """Extract hyperparameters from log header lines."""
    params = {}
    with open(path) as f:
        for line in f:
            if line.startswith("#" * 10):
                break  # hit first iteration block
            # [TRAIN-*] key: value patterns
            m = re.match(r"\[TRAIN-\w+\]\s+(.+)", line.strip())
            if m:
                content = m.group(1)
                if ":" in content:
                    k, v = content.split(":", 1)
                    params[k.strip()] = v.strip()
                elif "=" in content and "iter=" not in content:
                    # DAPG: alpha_init=0.7, alpha_min=0.1, ...
                    for pair in content.replace("DAPG: ", "").split(","):
                        pair = pair.strip()
                        if "=" in pair:
                            k2, v2 = pair.split("=", 1)
                            params[k2.strip()] = v2.strip()
            if len(params) > 20:
                break
    return params


def import_log(log_path: str, experiment: str, run_name: str, skill: str = ""):
    """Import a single log file into MLflow."""
    print(f"Parsing: {log_path}")
    iterations = parse_log(log_path)
    if not iterations:
        print(f"  No iterations found in {log_path}")
        return

    params = extract_params(log_path)
    params["skill"] = skill
    params["source_log"] = log_path
    params["import_mode"] = "backfill"

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(experiment)

    with mlflow.start_run(run_name=run_name, tags={"skill": skill, "backfill": "true"}):
        # Log params (truncate long values)
        for k, v in params.items():
            sv = str(v)[:500]
            try:
                mlflow.log_param(k, sv)
            except Exception:
                pass

        # Log metrics per iteration
        for metrics in iterations:
            it = int(metrics.pop("_iter"))
            for key, val in metrics.items():
                # MLflow disallows leading '/' in metric names
                safe_key = key.lstrip("/")
                try:
                    mlflow.log_metric(safe_key, val, step=it)
                except Exception as e:
                    print(f"  Warning: failed to log {safe_key}={val} at step {it}: {e}")

    print(f"  Imported {len(iterations)} iterations as '{run_name}'")


def main():
    parser = argparse.ArgumentParser(description="Import training logs into MLflow")
    parser.add_argument("--log", type=str, help="Path to log file")
    parser.add_argument("--experiment", type=str, default="THREAD-RL")
    parser.add_argument("--run-name", type=str, help="MLflow run name")
    parser.add_argument("--skill", type=str, default="")
    parser.add_argument("--all-current", action="store_true",
                        help="Import all 4 current training logs")
    args = parser.parse_args()

    if args.all_current:
        for run in CURRENT_RUNS:
            try:
                import_log(run["log"], args.experiment, run["run_name"], run["skill"])
            except FileNotFoundError:
                print(f"  Skipped (not found): {run['log']}")
    elif args.log:
        import_log(args.log, args.experiment, args.run_name or "imported_run", args.skill)
    else:
        parser.error("Specify --log or --all-current")


if __name__ == "__main__":
    main()
