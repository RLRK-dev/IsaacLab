#!/usr/bin/env python3
"""Import TensorBoard event files into MLflow for local visualization.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/import_tb_to_mlflow.py [--data-dir DIR] [--experiment NAME]

Then view at: mlflow ui --port 5000
"""

import argparse
import os
import glob

import mlflow
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def import_run(tb_dir: str, experiment_name: str):
    """Import a single TensorBoard run directory into MLflow."""
    run_name = os.path.basename(tb_dir)

    # Find event files
    event_files = glob.glob(os.path.join(tb_dir, "events.out.tfevents.*"))
    if not event_files:
        return

    # Determine skill from directory name
    if "grasp_cable" in run_name or "approach_cable" in run_name:
        skill = "ApproachCable"
    elif "insert_clip" in run_name:
        skill = "InsertIntoClip"
    elif "aerial_regrasp" in run_name:
        skill = "AerialRegrasp"
    else:
        skill = "unknown"

    # Load TensorBoard events
    ea = EventAccumulator(tb_dir)
    ea.Reload()
    tags = ea.Tags().get("scalars", [])
    if not tags:
        return

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name):
        mlflow.set_tag("skill", skill)
        mlflow.set_tag("tb_dir", tb_dir)

        # Log summary.json params if available
        summary_path = os.path.join(tb_dir, "summary.json")
        if os.path.exists(summary_path):
            import json
            with open(summary_path) as f:
                summary = json.load(f)
            # Log key params
            params_to_log = {}
            for key in ["world_count", "max_iterations", "num_steps_per_env", "device"]:
                if key in summary:
                    params_to_log[key] = summary[key]
            if "dapg" in summary:
                for key in ["alpha_init", "alpha_min", "alpha_anneal_iters"]:
                    if key in summary["dapg"]:
                        params_to_log[f"dapg.{key}"] = summary["dapg"][key]
            if "env_config" in summary:
                for key in ["REWARD_MODE", "RANGE_POS", "RANGE_ORI", "POS_ACTION_SCALE"]:
                    if key in summary["env_config"]:
                        params_to_log[key] = summary["env_config"][key]
            if params_to_log:
                mlflow.log_params(params_to_log)

        # Log all scalar metrics
        for tag in tags:
            events = ea.Scalars(tag)
            for event in events:
                # Sanitize tag name for MLflow (replace / with .)
                metric_name = tag.replace("/", ".")
                mlflow.log_metric(metric_name, event.value, step=event.step)

    print(f"  [{skill}] {run_name}: {len(tags)} metrics, {sum(len(ea.Scalars(t)) for t in tags)} datapoints")


def main():
    parser = argparse.ArgumentParser(description="Import TensorBoard runs to MLflow")
    parser.add_argument("--data-dir", type=str,
                        default=os.path.expanduser("~/IsaacLab/thread_isaac_lab/data"),
                        help="Directory containing rl_* run directories")
    parser.add_argument("--experiment", type=str, default="THREAD-RL",
                        help="MLflow experiment name")
    parser.add_argument("--recent", type=int, default=None,
                        help="Only import N most recent runs")
    args = parser.parse_args()

    # Find all run directories
    run_dirs = sorted(glob.glob(os.path.join(args.data_dir, "rl_*")),
                      key=os.path.getmtime, reverse=True)

    if args.recent:
        run_dirs = run_dirs[:args.recent]

    print(f"Importing {len(run_dirs)} runs to MLflow experiment '{args.experiment}'...")

    mlflow.set_tracking_uri(f"file://{os.path.expanduser('~/mlflow_data')}")

    for tb_dir in run_dirs:
        try:
            import_run(tb_dir, args.experiment)
        except Exception as e:
            print(f"  SKIP {os.path.basename(tb_dir)}: {e}")

    print(f"\nDone. View at: mlflow ui --backend-store-uri file://$HOME/mlflow_data --port 5000")


if __name__ == "__main__":
    main()
