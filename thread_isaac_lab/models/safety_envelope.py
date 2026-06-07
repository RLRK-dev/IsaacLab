"""safety_envelope.py — SOMA Safety Envelope 4-layer structure.

Phase 1: Measurement infrastructure only. Layers 1-3 are pass-through
(measure and log, but do NOT enforce). Layer 4 (Adaptive Retreat) is
the existing FallbackGuard, the only layer that enforces in Phase 1.

SOMA Safety Envelope layers:
  1. Energy Tank — cumulative energy budget counter
  2. Passivity Filter — output power <= dissipated power
  3. CBF — joint limits / contact force barrier functions
  4. Adaptive Retreat — obs anomaly → residual=0 (FallbackGuard)
"""

import torch
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SafetyMetrics:
    """Accumulated safety metrics for RUN_METRICS output."""
    # Layer 1: Energy Tank
    energy_injected: float = 0.0
    energy_dissipated: float = 0.0
    energy_balance: float = 0.0
    tank_would_deplete: bool = False

    # Layer 2: Passivity Filter
    passivity_violations: int = 0
    max_power_inject: float = 0.0

    # Layer 3: CBF (placeholder)
    joint_limit_proximity_min: float = float("inf")
    max_contact_force: float = 0.0

    # Layer 4: Adaptive Retreat (FallbackGuard)
    fallback_count: int = 0
    fallback_reasons: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Export for RUN_METRICS.json."""
        return {
            "safety_envelope": {
                "layer1_energy_balance": round(self.energy_balance, 6),
                "layer1_tank_would_deplete": self.tank_would_deplete,
                "layer2_passivity_violations": self.passivity_violations,
                "layer2_max_power_inject": round(self.max_power_inject, 6),
                "layer3_joint_limit_proximity_min": round(
                    self.joint_limit_proximity_min, 6)
                if self.joint_limit_proximity_min != float("inf") else None,
                "layer3_max_contact_force": round(self.max_contact_force, 6),
                "layer4_fallback_count": self.fallback_count,
                "layer4_fallback_reasons": list(set(self.fallback_reasons)),
            }
        }


class SafetyEnvelope:
    """SOMA Safety Envelope — 4-layer structure.

    Phase 1 (current): Layers 1-3 measure only, Layer 4 enforces.
    Phase B (future): All layers enforce.

    Usage:
        envelope = SafetyEnvelope(fallback_guard, joint_limits)
        action = envelope.apply(obs, action_normalized, phase_id,
                                joint_pos, joint_vel, ee_force)
        metrics = envelope.get_metrics()
    """

    def __init__(self, fallback_guard, joint_limits: Optional[torch.Tensor] = None,
                 energy_tank_capacity: float = 100.0):
        """
        Args:
            fallback_guard: Existing FallbackGuard instance (Layer 4).
            joint_limits: (num_joints, 2) tensor of [lower, upper] limits.
            energy_tank_capacity: Max energy budget (Layer 1, measurement only).
        """
        self.fallback_guard = fallback_guard
        self.joint_limits = joint_limits
        self.energy_tank_capacity = energy_tank_capacity
        self.metrics = SafetyMetrics()
        self._prev_action = None

    def apply(self, obs: torch.Tensor, action_normalized: torch.Tensor,
              phase_id: float, env_idx: int = -1, step: int = -1,
              joint_pos: Optional[torch.Tensor] = None,
              joint_vel: Optional[torch.Tensor] = None,
              ee_force: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Apply all 4 safety layers (1-3 measure-only, 4 enforces).

        Args:
            obs: (N, obs_dim) observation tensor.
            action_normalized: (N, action_dim) in [-1, 1].
            phase_id: Current task phase.
            env_idx: Environment index for logging.
            step: Current step for logging.
            joint_pos: (N, num_joints) joint positions (optional, for L3).
            joint_vel: (N, num_joints) joint velocities (optional, for L1/L2).
            ee_force: (N, 3) or (N, 6) end-effector force (optional, for L2/L3).

        Returns:
            (N, action_dim) physical action after Layer 4 enforcement.
        """
        # --- Layer 1: Energy Tank (MEASUREMENT ONLY) ---
        self._measure_energy(action_normalized, joint_vel)

        # --- Layer 2: Passivity Filter (MEASUREMENT ONLY) ---
        self._measure_passivity(action_normalized, joint_vel, ee_force)

        # --- Layer 3: CBF (MEASUREMENT ONLY) ---
        self._measure_cbf(joint_pos, ee_force)

        # --- Layer 4: Adaptive Retreat (ENFORCES) ---
        action_physical = self.fallback_guard.apply(
            obs, action_normalized, phase_id, env_idx, step)

        # Sync Layer 4 metrics
        self.metrics.fallback_count = self.fallback_guard.fallback_count

        self._prev_action = action_normalized.detach().clone()
        return action_physical

    def _measure_energy(self, action: torch.Tensor,
                        joint_vel: Optional[torch.Tensor]):
        """Layer 1: Compute energy injection/dissipation (pass-through)."""
        if joint_vel is None:
            return

        # Approximate: P_inject = |action · vel| (power = torque * velocity)
        # Use first 2 dims (grip) as torque proxy, rest as position commands
        grip_action = action[:, :2]
        grip_vel = joint_vel[:, :2] if joint_vel.shape[1] >= 2 else joint_vel

        power = (grip_action * grip_vel).abs().sum().item()
        dt = 1.0 / 120.0  # Assume 120Hz control loop

        self.metrics.energy_injected += power * dt
        # Dissipation approximation: friction ~ vel^2
        dissipation = (joint_vel ** 2).sum().item() * 0.01 * dt
        self.metrics.energy_dissipated += dissipation
        self.metrics.energy_balance = (
            self.metrics.energy_injected - self.metrics.energy_dissipated)

        if self.metrics.energy_balance > self.energy_tank_capacity:
            self.metrics.tank_would_deplete = True

    def _measure_passivity(self, action: torch.Tensor,
                           joint_vel: Optional[torch.Tensor],
                           ee_force: Optional[torch.Tensor]):
        """Layer 2: Check passivity constraint (pass-through)."""
        if joint_vel is None:
            return

        # Instantaneous power: P = action · vel
        power_inject = (action * joint_vel[:, :action.shape[1]]).sum(dim=1)
        max_power = power_inject.max().item()

        if max_power > self.metrics.max_power_inject:
            self.metrics.max_power_inject = max_power

        # Count violations (P_inject > 0 without sufficient dissipation)
        violations = (power_inject > 0.1).sum().item()
        self.metrics.passivity_violations += int(violations)

    def _measure_cbf(self, joint_pos: Optional[torch.Tensor],
                     ee_force: Optional[torch.Tensor]):
        """Layer 3: Measure joint limit proximity and contact force (pass-through)."""
        if joint_pos is not None and self.joint_limits is not None:
            limits = self.joint_limits
            # Distance to nearest joint limit
            dist_lower = (joint_pos - limits[:, 0]).min().item()
            dist_upper = (limits[:, 1] - joint_pos).min().item()
            proximity = min(dist_lower, dist_upper)
            if proximity < self.metrics.joint_limit_proximity_min:
                self.metrics.joint_limit_proximity_min = proximity

        if ee_force is not None:
            force_mag = ee_force.norm(dim=-1).max().item()
            if force_mag > self.metrics.max_contact_force:
                self.metrics.max_contact_force = force_mag

    def get_metrics(self) -> dict:
        """Return metrics dict for RUN_METRICS.json."""
        return self.metrics.to_dict()

    def reset(self):
        """Reset all metrics for new episode."""
        self.metrics = SafetyMetrics()
        self.fallback_guard.reset_count()
        self._prev_action = None
