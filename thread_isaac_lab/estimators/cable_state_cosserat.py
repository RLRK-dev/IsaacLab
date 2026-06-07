# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage D: Cosserat rod 7-term loss fitting (T-Vision-CableState L1.A.2, Phase 2 design).

Per ``thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md`` §3:

- :class:`CosseratLossWeights` — 7-term weights (parent memo §2.5.1)
- :class:`CosseratSolverConfig` — convergence + multi-restart + thresholds
- :class:`CosseratSolver` — PyTorch L-BFGS multi-restart fitter (Warp kernel
  optimization deferred to Phase 6 latency-profile decision)

Phase: SKELETON (T-Vision-CableState-Impl-Phase-2-Design-CC, 2026-05-04). Every
compute method raises :class:`NotImplementedError`; this module exists to lock
the public surface (R6) and the Phase 4 integration contract.

7-term energy ::

    L = w_pos L_pos + w_tan L_tan + w_bend L_bend + w_arc L_arc
      + w_id_grasp L_id + w_temp L_temp + w_proj L_proj

Term semantics per parent design memo §2.5.1; weights tuned empirically
against the Q5 worst-case benchmark (parent memo §5).

R6 module boundary: imports restricted to :mod:`thread_isaac_lab.estimators.*`
+ :mod:`torch`. NO ``newton``, NO :mod:`thread_isaac_lab.envs`,
NO ``cable_body_q``.

Cable physical params mirrored from ``thread_isaac_lab/configs/task_config.py``
(``CABLE_SEGMENTS=40``, ``CABLE_SEG_LEN=0.015``, ``CABLE_BEND_STIFFNESS=0.1``);
SSOT remains task_config.py.
"""

from dataclasses import dataclass, field

import torch

from thread_isaac_lab.estimators.types import CableState40

# ---------------------------------------------------------------------------
# Constants mirrored from task_config.py (TOUCH FORBIDDEN; SSOT remains there).
# ---------------------------------------------------------------------------
_NUM_CABLE_SEGMENTS = 40  # mirrors CABLE_SEGMENTS
_NOMINAL_SEG_LEN_M = 0.015  # mirrors CABLE_SEG_LEN
_NOMINAL_BEND_EI = 0.1  # mirrors CABLE_BEND_STIFFNESS

# Stage D defaults (parent memo §2.5.1 + §2.5.2 + design memo §3.4-§3.7).
_DEFAULT_MAX_ITER = 200
_DEFAULT_RESTART_COUNT = 5
_DEFAULT_RESTART_SIGMA_M = 0.002  # σ = 2 mm gaussian perturbation
_DEFAULT_NN_K = 5  # L_pos NN search top-k
_DEFAULT_NN_RADIUS_M = 0.010  # L_pos NN search radius
_DEFAULT_PROJ_TOLERANCE_M = 0.005  # L_proj 5 mm hinge
_DEFAULT_GRASP_FINGER_DISTANCE_M = 0.020  # L_id active when |finger - cable| < 20 mm
_DEFAULT_IDENTITY_INVERSION_DELTA_M = 0.050  # § 3.5 50 mm threshold
_DEFAULT_TOLERANCE_GRAD = 1e-6
_DEFAULT_TOLERANCE_CHANGE = 1e-9


@dataclass
class CosseratLossWeights:
    """7-term Cosserat loss weights (parent memo §2.5.1 initial values).

    Final tuning happens in the Q5 worst-case benchmark (parent memo §5);
    these defaults are the starting point for Phase 4 impl.

    Attributes:
        w_pos: per-segment fit to nearest cloud points (k = 5 NN).
        w_tan: tangent continuity (1st-derivative smoothness).
        w_bend: bend energy ``(EI / 2) Σ ||κ_i||²``; ``EI`` mirrors task_config.
        w_arc: arc-length monotonicity around ``CABLE_SEG_LEN = 0.015 m``.
        w_id_grasp: segment-identity anchor; active only when finger contact
            (``|finger - cable| < 20 mm``).
        w_temp: temporal smoothness vs ``prev``; disabled at episode start.
        w_proj: depth-consistency hinge; ``5 mm`` tolerance.
    """

    w_pos: float = 1.0
    w_tan: float = 0.3
    w_bend: float = 0.5
    w_arc: float = 1.0
    w_id_grasp: float = 0.5
    w_temp: float = 0.2
    w_proj: float = 0.3


@dataclass
class CosseratSolverConfig:
    """Stage D solver configuration (design memo §3.7.1).

    Attributes:
        weights: 7-term loss weights (see :class:`CosseratLossWeights`).
        max_iter: Hard cap on inner LBFGS iterations across all outer steps
            (parent memo §2.5.2 ``max iterations: 200``).
        restart_count: Number of multi-restart trials with σ-gaussian
            perturbation (parent memo §2.5.2 ``5 init perturbations``).
        restart_sigma_m: Gaussian perturbation σ in meters
            (parent memo §2.5.2 ``σ = 2 mm``).
        tolerance_grad: LBFGS gradient tolerance.
        tolerance_change: LBFGS function-change tolerance.
        nn_k: ``L_pos`` NN top-k count.
        nn_radius_m: ``L_pos`` NN search radius (excludes points farther than
            this from the segment).
        bend_ei: ``L_bend`` ``EI`` mirror of ``CABLE_BEND_STIFFNESS``.
        seg_len_m: ``L_arc`` target seg length, mirror of ``CABLE_SEG_LEN``.
        proj_tolerance_m: ``L_proj`` hinge tolerance.
        grasp_finger_distance_m: ``L_id`` activation threshold.
        identity_inversion_delta_m: post-fit inversion check threshold
            (design memo §3.5).
    """

    weights: CosseratLossWeights = field(default_factory=CosseratLossWeights)
    max_iter: int = _DEFAULT_MAX_ITER
    restart_count: int = _DEFAULT_RESTART_COUNT
    restart_sigma_m: float = _DEFAULT_RESTART_SIGMA_M
    tolerance_grad: float = _DEFAULT_TOLERANCE_GRAD
    tolerance_change: float = _DEFAULT_TOLERANCE_CHANGE
    nn_k: int = _DEFAULT_NN_K
    nn_radius_m: float = _DEFAULT_NN_RADIUS_M
    bend_ei: float = _NOMINAL_BEND_EI
    seg_len_m: float = _NOMINAL_SEG_LEN_M
    proj_tolerance_m: float = _DEFAULT_PROJ_TOLERANCE_M
    grasp_finger_distance_m: float = _DEFAULT_GRASP_FINGER_DISTANCE_M
    identity_inversion_delta_m: float = _DEFAULT_IDENTITY_INVERSION_DELTA_M


class CosseratSolver:
    """Stage D Cosserat 7-term loss + multi-restart L-BFGS fitter.

    Public entry: :meth:`fit`. Multi-restart strategy (design memo §3.4.2):
    ``restart_count`` trials, each starting from ``seg_init`` plus
    ``N(0, σ² I)`` Gaussian perturbation; keep the best final loss.

    Optimizer (design memo §3.4.1): PyTorch L-BFGS first (Strong-Wolfe line
    search), Warp kernel optimization deferred to Phase 6 once the Q5
    benchmark exposes a latency budget overrun.

    Identity inversion check (design memo §3.5): post-fit ``d_grasp`` /
    ``d_far`` test, reverse-and-refit one pass when triggered.

    R6: imports limited to :mod:`torch` + :mod:`thread_isaac_lab.estimators`.
    """

    def __init__(self, config: CosseratSolverConfig | None = None) -> None:
        self._config = config or CosseratSolverConfig()

    @property
    def config(self) -> CosseratSolverConfig:
        return self._config

    def fit(
        self,
        seg_init: torch.Tensor,
        cloud: torch.Tensor,
        prev: CableState40 | None = None,
        finger_positions: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Run multi-restart L-BFGS fit on the 7-term Cosserat loss.

        Args:
            seg_init: ``[40, 3]`` warm-start positions from Stage B (PCA
                40-bin) or Stage C (DD-PINN). May contain ``NaN`` for empty
                bins; ``L_pos`` masks these out (design memo §5.2).
            cloud: ``[N_pts, 3]`` voxel-fused cloud (Stage A.3 output).
            prev: Optional previous-frame estimate for ``L_temp``. ``None`` at
                episode start disables ``L_temp`` (weight effectively 0).
            finger_positions: ``[2, 3]`` left/right fingertip world xyz. When
                ``None`` or beyond ``grasp_finger_distance_m`` of the cable,
                ``L_id`` is disabled (design memo §3.1 ``w_id_grasp = 0``
                row).

        Returns:
            ``[40, 3]`` refined per-segment positions.

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "CosseratSolver.fit: design memo §3.4 — impl pending (T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )

    def _compute_loss(
        self,
        seg: torch.Tensor,
        cloud: torch.Tensor,
        prev: CableState40 | None,
        finger_positions: torch.Tensor | None,
        weights: CosseratLossWeights,
    ) -> torch.Tensor:
        """Sum the 7-term Cosserat energy at the current ``seg`` estimate.

        Term implementations (design memo §3.1-§3.3 + §5.2 NaN handling):

        - L_pos: ``cdist(seg, cloud)`` → top-k NN within ``nn_radius_m``;
          mask NaN segments out of the contribution.
        - L_tan: 2nd-order finite difference of ``seg`` along arc index.
        - L_bend: discrete curvature κ_i = ``||seg[i+1] - 2 seg[i] + seg[i-1]||``
          normalized by ``seg_len_m²``; sum ``(EI / 2) ||κ_i||²``.
        - L_arc: ``Σ (||seg[i+1] - seg[i]|| - seg_len_m)²``.
        - L_id: ``||seg[0] - p_grasp_end||² + ||seg[-1] - p_far_end||²``,
          gated by ``grasp_finger_distance_m``.
        - L_temp: ``||seg - prev.positions||²`` summed across segments.
        - L_proj: ``Σ max(0, |z_seg - z_depth_proj| - proj_tolerance_m)²``.

        Args:
            seg: current ``[40, 3]`` candidate.
            cloud: ``[N_pts, 3]`` voxel-fused cloud.
            prev: previous-frame estimate (or ``None`` at episode start).
            finger_positions: ``[2, 3]`` fingertip xyz (or ``None``).
            weights: 7-term weights.

        Returns:
            scalar tensor ``L``.

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "CosseratSolver._compute_loss: design memo §3.1-§3.3 — impl pending "
            "(T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )

    def _run_lbfgs(
        self,
        seg_init: torch.Tensor,
        cloud: torch.Tensor,
        prev: CableState40 | None,
        finger_positions: torch.Tensor | None,
        weights: CosseratLossWeights,
    ) -> tuple[torch.Tensor, float]:
        """Single L-BFGS run from ``seg_init``; returns (seg_fitted, final_loss).

        Implementation pattern (design memo §3.4.1)::

            optimizer = torch.optim.LBFGS(
                [seg],
                lr=1.0,
                max_iter=20,
                tolerance_grad=tolerance_grad,
                tolerance_change=tolerance_change,
                history_size=20,
                line_search_fn="strong_wolfe",
            )
            for outer in range(max_outer_steps):
                loss = optimizer.step(closure)
                if loss < 1e-6 or outer >= max_outer_steps - 1:
                    break

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "CosseratSolver._run_lbfgs: design memo §3.4.1 — impl pending (T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )

    def _verify_identity(
        self,
        seg: torch.Tensor,
        cloud: torch.Tensor,
        prev: CableState40 | None,
        finger_positions: torch.Tensor | None,
    ) -> torch.Tensor:
        """Identity inversion check + at most one reverse-then-refit pass.

        Algorithm (design memo §3.5):

            d_grasp = ||seg[0]  - finger_avg||
            d_far   = ||seg[-1] - finger_avg||
            if d_grasp > d_far + identity_inversion_delta_m:
                seg = flip(seg, dim=0)
                seg = self._run_lbfgs(seg, ...)  # one re-fit pass
            return seg

        Anchor source priority (parent memo §3.5):
        Tier 1 ``finger_positions`` → Tier 2 ``prev`` → Tier 3 ``t_min``
        default (handled by caller of :meth:`fit`).

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "CosseratSolver._verify_identity: design memo §3.5 — impl pending "
            "(T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )
