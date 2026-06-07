"""action_converter.py — Converts normalized [-1,1] actions to physical units.

SOMA Phase B3: Action space conversion for Residual PPO.
8D action: delta_grip(2) + delta_ee_pos(6)
Active only in phases defined by ACTION_SPACE["active_phases"].
"""

import torch
from thread_isaac_lab.configs.task_config import ACTION_SPACE, ACTION_DIM


class ActionConverter:
    """Converts between normalized [-1,1] and physical action spaces.

    Usage:
        converter = ActionConverter(num_envs, device)
        physical = converter.to_physical(normalized, phase_id)
        normalized = converter.to_normalized(physical)
    """

    def __init__(self, num_envs: int, device: str):
        self.num_envs = num_envs
        self.device = device
        self.action_dim = ACTION_DIM
        self._clip = torch.tensor(
            ACTION_SPACE["clip_physical"], dtype=torch.float32, device=device)
        self._active_phases = set(ACTION_SPACE["active_phases"])

    def to_physical(self, action_normalized: torch.Tensor,
                    phase_id: float) -> torch.Tensor:
        """Convert normalized [-1,1] action to physical units.

        Args:
            action_normalized: (N, 8) tensor in [-1, 1]
            phase_id: Current phase (3.0, 4.0, 5.0 etc.)

        Returns:
            (N, 8) tensor in physical units (N for grip, m for position)
            Returns zeros if phase is not in active_phases.
        """
        # Phase gate: only apply residual in active phases
        phase_int = int(phase_id)
        if phase_int not in self._active_phases:
            return torch.zeros_like(action_normalized)

        # Scale and clamp
        physical = action_normalized * self._clip
        physical = physical.clamp(-self._clip, self._clip)
        return physical

    def to_normalized(self, action_physical: torch.Tensor) -> torch.Tensor:
        """Convert physical action to normalized [-1,1] (inverse, for debug).

        Args:
            action_physical: (N, 8) tensor in physical units

        Returns:
            (N, 8) tensor in [-1, 1]
        """
        return (action_physical / self._clip).clamp(-1.0, 1.0)

    def zeros(self) -> torch.Tensor:
        """Return zero action tensor (no residual)."""
        return torch.zeros(self.num_envs, self.action_dim, device=self.device)
