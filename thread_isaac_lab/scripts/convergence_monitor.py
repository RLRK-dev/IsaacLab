# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Convergence monitor for RL training auto-stop.

Hooks into RSL-RL's OnPolicyRunner.log() to capture per-iteration
episode metrics, then detects plateau (no improvement) to trigger
early stopping.

Usage in training scripts:

    from convergence_monitor import ConvergenceMonitor

    ConvergenceMonitor.add_argparse_args(parser)
    args = parser.parse_args()

    monitor = ConvergenceMonitor.from_args(args)
    monitor.patch_runner(runner)

    for it in range(args.max_iterations):
        runner.learn(num_learning_iterations=1, ...)
        # ... surr guard, BC update, etc.

        should_stop, reason = monitor.step(it)
        if should_stop:
            print(f"Auto-stop: {reason}")
            break
"""

import os


class ConvergenceMonitor:
    """Tracks a training metric and detects convergence plateau.

    Monitors a metric from env extras (e.g. dist_pos_median) captured
    via monkey-patched runner.log(). Signals auto-stop when the metric
    hasn't improved by more than `delta` in `patience` iterations.
    """

    def __init__(self, metric="/metrics/dist_pos_median", patience=30,
                 min_iterations=50, delta=0.001, mode="min",
                 log_dir=None, save_best=True):
        """
        Args:
            metric: Key in env extras to monitor.
            patience: Iterations without improvement before stopping. 0=disabled.
            min_iterations: Don't stop before this iteration.
            delta: Minimum improvement to reset patience counter.
                For dist metrics, this is in meters (0.001 = 1mm).
            mode: "min" (lower is better) or "max" (higher is better).
            log_dir: Directory for saving best model checkpoint.
            save_best: Whether to save best model when metric improves.
        """
        self.metric = metric
        self.patience = patience
        self.min_iterations = min_iterations
        self.delta = delta
        self.mode = mode
        self.log_dir = log_dir
        self.save_best = save_best

        self.history = []
        self.best_value = float("inf") if mode == "min" else float("-inf")
        self.best_iter = -1
        self._last_ep_metrics = {}
        self._runner = None

    @staticmethod
    def add_argparse_args(parser):
        """Add convergence-related CLI arguments to an argparse parser."""
        group = parser.add_argument_group("Convergence (auto-stop)")
        group.add_argument("--patience", type=int, default=30,
                           help="Stop after N iters with no improvement (0=disabled, default: 30)")
        group.add_argument("--min-iterations", type=int, default=50,
                           help="Don't auto-stop before this iteration (default: 50)")
        group.add_argument("--convergence-delta", type=float, default=0.001,
                           help="Minimum metric improvement to count as progress (default: 0.001 = 1mm)")
        group.add_argument("--convergence-metric", type=str,
                           default="/metrics/dist_pos_median",
                           help="Metric key to monitor (default: /metrics/dist_pos_median)")
        return group

    @classmethod
    def from_args(cls, args):
        """Create ConvergenceMonitor from parsed CLI args."""
        metric = getattr(args, "convergence_metric", "/metrics/dist_pos_median")
        mode = "max" if "success" in metric else "min"
        return cls(
            metric=metric,
            patience=getattr(args, "patience", 30),
            min_iterations=getattr(args, "min_iterations", 50),
            delta=getattr(args, "convergence_delta", 0.001),
            mode=mode,
            log_dir=getattr(args, "log_dir", None),
        )

    def patch_runner(self, runner):
        """Monkey-patch runner.log() to capture episode metrics each iteration."""
        self._runner = runner
        original_log = runner.log
        monitor = self

        def patched_log(locs, width=80, pad=35):
            ep_infos = locs.get("ep_infos")
            if ep_infos:
                for key in ep_infos[0]:
                    values = []
                    for ep_info in ep_infos:
                        if key not in ep_info:
                            continue
                        v = ep_info[key]
                        if hasattr(v, "item"):
                            values.append(v.item())
                        elif isinstance(v, (int, float)):
                            values.append(float(v))
                    if values:
                        monitor._last_ep_metrics[key] = sum(values) / len(values)
            return original_log(locs, width, pad)

        runner.log = patched_log

    def step(self, iteration):
        """Record metrics and check convergence.

        Returns:
            (should_stop, reason): should_stop is True if training should end.
                reason is a human-readable string (empty if not stopping).
        """
        value = self._last_ep_metrics.get(self.metric)
        self._last_ep_metrics = {}

        if value is None:
            return False, ""

        self.history.append((iteration, value))

        improved = False
        if self.mode == "min":
            if value < self.best_value - self.delta:
                improved = True
        else:
            if value > self.best_value + self.delta:
                improved = True

        if improved:
            self.best_value = value
            self.best_iter = iteration
            if self.save_best and self._runner and self.log_dir:
                best_path = os.path.join(self.log_dir, "model_best_converge.pt")
                self._runner.save(best_path)
                tag = getattr(self, "skill_tag", "CONVERGE")
                print(f"[{tag}] Converge-best saved: iter={iteration} "
                      f"{self.metric}={value:.6f}")

        if iteration < self.min_iterations:
            return False, ""

        if self.patience <= 0:
            return False, ""

        iters_since_best = iteration - self.best_iter
        if iters_since_best >= self.patience:
            reason = (
                f"plateau detected — no improvement in {self.metric} "
                f"for {iters_since_best} iters "
                f"(best={self.best_value:.4f} at iter={self.best_iter}, "
                f"current={value:.4f}, delta={self.delta})"
            )
            return True, reason

        return False, ""

    def get_metric(self, key=None):
        """Get the latest value of a captured metric."""
        if key is None:
            key = self.metric
        return self._last_ep_metrics.get(key)

    def summary(self):
        """Return a dict summarizing convergence state for summary.json."""
        last_value = self.history[-1][1] if self.history else None
        return {
            "metric": self.metric,
            "mode": self.mode,
            "best_value": self.best_value if self.best_iter >= 0 else None,
            "best_iter": self.best_iter,
            "final_value": last_value,
            "total_measured_iters": len(self.history),
            "patience": self.patience,
            "min_iterations": self.min_iterations,
            "delta": self.delta,
            "stopped_early": (
                len(self.history) > 0
                and self.best_iter >= 0
                and (self.history[-1][0] - self.best_iter >= self.patience)
            ),
        }
