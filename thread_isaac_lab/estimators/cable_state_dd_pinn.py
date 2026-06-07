# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage C: DD-PINN warm start (T-Vision-CableState L1.A.2, Phase 2 design).

Per ``thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md`` §2:

- :class:`DDPINNConfig` — architecture + train config dataclass
- :class:`DDPINNModel` — ~52k-param MLP (input embed → global pool → backbone → 40×3 output)
- :func:`farthest_point_sampling` — anchor-point selection helper

Phase: SKELETON (T-Vision-CableState-Impl-Phase-2-Design-CC, 2026-05-04). Every
compute method raises :class:`NotImplementedError`; this module exists to lock
the public surface (R6) and the Phase 4 integration contract. Implementation +
training (~20 h GPU + 5 k labeled scenes) is deferred to
``T-Vision-CableState-Impl-Phase-3-Stage-C-Train``.

R6 module boundary (peer to ``estimators/cable_state.py`` discipline): imports
restricted to :mod:`thread_isaac_lab.estimators.*` + :mod:`torch`. NO ``newton``,
NO :mod:`thread_isaac_lab.envs`, NO ``cable_body_q`` access.

Cable physical params mirrored from ``thread_isaac_lab/configs/task_config.py``
(``CABLE_SEGMENTS=40``); SSOT remains task_config.py (TOUCH FORBIDDEN at this
phase).
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import torch

from thread_isaac_lab.estimators.types import CableState40

# ---------------------------------------------------------------------------
# Constants mirrored from task_config.py (TOUCH FORBIDDEN; SSOT remains there).
# ---------------------------------------------------------------------------
_NUM_CABLE_SEGMENTS = 40  # mirrors CABLE_SEGMENTS

# DD-PINN architecture defaults (design memo §2.1, "Option B" 3 hidden × 96).
_DEFAULT_N_ANCHOR = 256
_DEFAULT_EMBED_DIM = 64
_DEFAULT_HIDDEN_DIM = 96
_DEFAULT_N_HIDDEN_LAYERS = 3

# Param-count target window for the smoke test assertion (design memo §2.1.4).
# 3 hidden × 96 GELU + I/O ≈ 54_k; allow ±10 % for impl variation.
_PARAM_COUNT_LOWER = 50_000
_PARAM_COUNT_UPPER = 60_000


@dataclass
class DDPINNConfig:
    """Stage C DD-PINN architecture + train hyperparameters.

    Defaults reflect design memo §2.1.4 "Option B" choice
    (3 hidden × 96 GELU ≈ 54 k params, parent memo "~50 k" abstract).
    Train fields are reference-only at this phase (Phase 3 impl trigger).

    Attributes:
        n_anchor: Farthest-point-sampled anchor count fed to the encoder.
        embed_dim: Per-point xyz embed dimension (Linear(3, embed_dim) + GELU).
        hidden_dim: Backbone hidden width.
        n_hidden_layers: Number of hidden layers in the backbone MLP.
        n_segments: Output segment count; mirrors ``CABLE_SEGMENTS=40``.
        use_prev_estimate: When True the previous frame estimate is fused in
            (40 × 3 → flat 120). When False or ``prev=None`` the input is
            zero-filled (design memo §2.1.1 Step 4).
        activation: Activation name. Spec'd as "gelu" (design memo §2.1.2).
        train_lr: AdamW learning rate (Phase 3 impl trigger).
        train_weight_decay: AdamW weight decay.
        train_epochs: Cosine schedule ``T_max``.
        train_batch_size: Scene batch size.
        train_amp: Whether to use ``torch.cuda.amp`` mixed precision.
    """

    n_anchor: int = _DEFAULT_N_ANCHOR
    embed_dim: int = _DEFAULT_EMBED_DIM
    hidden_dim: int = _DEFAULT_HIDDEN_DIM
    n_hidden_layers: int = _DEFAULT_N_HIDDEN_LAYERS
    n_segments: int = _NUM_CABLE_SEGMENTS
    use_prev_estimate: bool = True
    activation: str = "gelu"
    # Phase 3 train-time fields (reference; not consumed by skeleton).
    train_lr: float = 1e-3
    train_weight_decay: float = 1e-4
    train_epochs: int = 100
    train_batch_size: int = 32
    train_amp: bool = True


def farthest_point_sampling(points: torch.Tensor, n_samples: int) -> torch.Tensor:
    """Greedy farthest-point sampling for anchor selection (design memo §2.1.1 Step 1).

    Selects ``n_samples`` indices from ``points`` greedily maximizing the
    minimum distance to already-selected points. ``O(n_samples × N)``.

    Args:
        points: ``[N, 3]`` candidate cloud (Stage A.3 voxel-fused output).
        n_samples: Number of anchors to return. Must satisfy
            ``0 < n_samples ≤ N``.

    Returns:
        ``[n_samples, 3]`` anchor positions.

    Raises:
        NotImplementedError: SKELETON — Phase 4 impl pending.
    """
    raise NotImplementedError(
        "farthest_point_sampling: design memo §2.1.1 — impl pending (T-Vision-CableState-Impl-Phase-4-Stage-DE)"
    )


class DDPINNModel(torch.nn.Module):
    """Stage C DD-PINN warm-start MLP (design memo §2.1, ~54 k params).

    Architecture (design memo §2.1.1 + §2.1.2):

        cloud [N, 3]
            └─ FPS → anchor [n_anchor, 3]
            └─ Linear(3, embed_dim) + GELU → [n_anchor, embed_dim]
            └─ max-pool + mean-pool → [2 * embed_dim]
            └─ concat with prev_flat [120] (or zeros) → [2 * embed_dim + 120]
            └─ MLP (n_hidden_layers × hidden_dim) GELU
            └─ Linear(hidden_dim, n_segments * 3) → [40, 3]

    Training is deferred to Phase 3 (5 k labeled scenes, ~20 h GPU @ cuda:2);
    inference latency target ``< 2 ms`` (design memo §2.2.5).

    R6: imports limited to :mod:`torch` + :mod:`thread_isaac_lab.estimators`.
    No newton / env imports.
    """

    def __init__(self, config: DDPINNConfig | None = None) -> None:
        super().__init__()
        self._config = config or DDPINNConfig()
        # Sub-module construction is impl-pending; declared via this attribute
        # so static analysis still sees the contract.
        self._encoder: torch.nn.Module | None = None
        self._backbone: torch.nn.Module | None = None
        self._head: torch.nn.Module | None = None

    @property
    def config(self) -> DDPINNConfig:
        return self._config

    @property
    def param_count(self) -> int:
        """Total trainable parameters; ``0`` while sub-modules are unbuilt.

        Phase 3 impl: must satisfy
        ``_PARAM_COUNT_LOWER ≤ param_count ≤ _PARAM_COUNT_UPPER`` per the
        smoke-test gate (design memo §6.1).
        """
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(
        self,
        cloud: torch.Tensor,
        prev: CableState40 | None = None,
    ) -> torch.Tensor:
        """Compute warm-start segment positions.

        Args:
            cloud: ``[N_pts, 3]`` voxel-fused cloud (Stage A.3 output).
                ``N_pts`` is expected ~1500-3000 per design memo §2.2.4.
            prev: Optional previous-frame estimate. When ``None`` (or when
                :attr:`DDPINNConfig.use_prev_estimate` is False) the prev-flat
                slot is zero-filled (design memo §2.1.1 Step 4).

        Returns:
            ``[40, 3]`` warm-start positions ``P̂_seg^(C)``, fed into Stage D
            as the initial seed (design memo §2.1.3).

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "DDPINNModel.forward: design memo §2.1 — impl pending "
            "(T-Vision-CableState-Impl-Phase-4-Stage-DE; checkpoint from Phase 3 train)"
        )

    @torch.no_grad()
    def load_checkpoint(self, ckpt_path: str | Path) -> None:
        """Load Phase 3 train checkpoint (state_dict).

        Args:
            ckpt_path: Path to a ``torch.save`` ``state_dict`` artifact
                produced by Phase 3 (design memo §2.2.4).

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "DDPINNModel.load_checkpoint: design memo §2.2.4 — impl pending (T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )


def build_train_loss(
    weights: dict[str, float] | None = None,
) -> Callable[[torch.Tensor, torch.Tensor], torch.Tensor]:
    """Construct the Phase 3 training loss closure (design memo §2.2.2).

    The loss combines per-segment position MSE, tangent-direction cosine, and
    arc-length monotonicity penalty with weights ``{w_pos, w_tan, w_arc}``.
    Defaults match design memo §2.2.2: ``w_pos = 1.0``, ``w_tan = 0.3``,
    ``w_arc = 0.5``.

    Args:
        weights: Override dict with keys ``w_pos`` / ``w_tan`` / ``w_arc``.

    Returns:
        Callable ``(pred [B, 40, 3], gt [B, 40, 3]) -> loss scalar``.

    Raises:
        NotImplementedError: SKELETON — Phase 3 impl pending.
    """
    raise NotImplementedError(
        "build_train_loss: design memo §2.2.2 — impl pending (T-Vision-CableState-Impl-Phase-3-Stage-C-Train)"
    )
