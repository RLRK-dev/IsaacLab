"""fallback_guard.py — Safety guard for residual actions (SOMA Phase B4).

Combines obs anomaly detection with action conversion.
When anomaly detected: residual → zeros (heuristic-only mode).
"""

import torch
from thread_isaac_lab.configs.task_config import FALLBACK


class FallbackGuard:
    """Applies fallback conditions to residual actions.

    Usage:
        guard = FallbackGuard(obs_builder, action_converter)
        action = guard.apply(obs, action_normalized, phase_id, env_idx, step)
    """

    def __init__(self, obs_builder, action_converter):
        self.obs_builder = obs_builder
        self.action_converter = action_converter
        self.fallback_count = 0
        self._log = FALLBACK.get("log_fallback", True)

    def apply(self, obs: torch.Tensor, action_normalized: torch.Tensor,
              phase_id: float, env_idx: int = -1, step: int = -1) -> torch.Tensor:
        """Apply fallback guard to action.

        Args:
            obs: (N, 24) raw obs
            action_normalized: (N, 8) in [-1, 1]
            phase_id: Current phase
            env_idx: Current env index (for logging)
            step: Current step (for logging)

        Returns:
            (N, 8) physical action — zeros for anomalous envs
        """
        # Convert to physical
        action_physical = self.action_converter.to_physical(
            action_normalized, phase_id)

        # Check anomalies
        anomalous = self.obs_builder.is_anomalous(obs)

        if anomalous.any():
            n_anomalous = anomalous.sum().item()
            self.fallback_count += n_anomalous

            if self._log:
                anomalous_ids = anomalous.nonzero(as_tuple=True)[0].tolist()
                reasons = self._diagnose(obs, anomalous)
                print(f"[FALLBACK] env={env_idx} step={step} phase={phase_id} "
                      f"triggered for {n_anomalous} env(s): {anomalous_ids} "
                      f"reason={reasons} (total={self.fallback_count})")

            # Zero out actions for anomalous envs
            action_physical[anomalous] = 0.0

        return action_physical

    def _diagnose(self, obs: torch.Tensor, anomalous: torch.Tensor) -> list:
        """Identify which fallback condition triggered."""
        reasons = []
        if torch.isnan(obs[anomalous]).any() or torch.isinf(obs[anomalous]).any():
            reasons.append("nan_inf")
        if self.obs_builder._p99_upper is not None:
            if (obs[anomalous] > self.obs_builder._p99_upper).any():
                reasons.append("out_of_range_upper")
            if (obs[anomalous] < self.obs_builder._p99_lower).any():
                reasons.append("out_of_range_lower")
        if self.obs_builder._step_count > 0:
            grip_l = obs[anomalous, 22]
            delta_l = (grip_l - self.obs_builder._prev_grip_effort_left[anomalous]).abs()
            if (delta_l > 100.0).any():
                reasons.append("grip_spike")
        return reasons if reasons else ["unknown"]

    def reset_count(self):
        """Reset fallback counter."""
        self.fallback_count = 0
