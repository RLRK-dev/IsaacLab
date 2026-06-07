# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MLflow integration for THREAD RL training scripts.

Hooks into RSL-RL's TensorBoard writer to forward all metrics to MLflow.
All env metrics (/metrics/*, /reward/*, /episode/*) and PPO losses
(Loss/*, Train/*, Policy/*) are automatically captured.

Usage:
    from mlflow_utils import setup_mlflow_tracking

    writer = setup_mlflow_tracking(
        experiment="THREAD-RL",
        run_name="AC_v21",
        params={"skill": "ApproachCable", "world_count": 256, ...},
        log_dir=args.log_dir,
    )
    runner.writer = writer
    runner.logger_type = "tensorboard"
    # ... training loop ...
    # BC-specific metrics:
    log_bc_metrics(it, bc_loss, alpha)
    # At end:
    finish_mlflow()
"""

from __future__ import annotations

import mlflow
from torch.utils.tensorboard import SummaryWriter

_TRACKING_URI = "sqlite:///home/rlrk/mlflow_data/mlflow.db"


def setup_mlflow_tracking(
    experiment: str,
    run_name: str,
    params: dict,
    log_dir: str,
    tags: dict | None = None,
) -> SummaryWriter:
    """Create a TensorBoard writer that also logs to MLflow.

    Args:
        experiment: MLflow experiment name (e.g. "THREAD-RL").
        run_name: MLflow run name (e.g. "AC_v21").
        params: Hyperparameters to log.
        log_dir: Directory for TensorBoard events.
        tags: Optional MLflow tags.

    Returns:
        SummaryWriter with add_scalar hooked to MLflow.
    """
    mlflow.set_tracking_uri(_TRACKING_URI)
    mlflow.set_experiment(experiment)
    mlflow.start_run(run_name=run_name, tags=tags)

    # MLflow truncates param values > 500 chars; stringify dicts
    flat = {}
    for k, v in params.items():
        sv = str(v)
        if len(sv) > 500:
            sv = sv[:497] + "..."
        flat[k] = sv
    mlflow.log_params(flat)

    writer = SummaryWriter(log_dir=log_dir, flush_secs=10)
    _orig_add_scalar = writer.add_scalar

    def _mlflow_add_scalar(tag, scalar_value, global_step=None, **kwargs):
        _orig_add_scalar(tag, scalar_value, global_step, **kwargs)
        step = global_step if global_step is not None else 0
        # MLflow disallows leading '/' in metric names
        mlflow_tag = tag.lstrip("/")
        try:
            mlflow.log_metric(mlflow_tag, float(scalar_value), step=step)
        except Exception:
            pass  # don't crash training on MLflow errors

    writer.add_scalar = _mlflow_add_scalar
    return writer


def log_bc_metrics(step: int, bc_loss: float, alpha: float, **extra):
    """Log DAPG BC auxiliary metrics to MLflow."""
    metrics = {"DAPG/bc_loss": bc_loss, "DAPG/alpha": alpha}
    metrics.update(extra)
    try:
        mlflow.log_metrics(metrics, step=step)
    except Exception:
        pass


def finish_mlflow():
    """End the active MLflow run."""
    try:
        mlflow.end_run()
    except Exception:
        pass
