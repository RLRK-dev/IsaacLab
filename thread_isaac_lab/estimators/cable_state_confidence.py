# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage E: per-segment confidence calibration (T-Vision-CableState L1.A.2, Phase 2 design).

Per ``thread-vault/06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md`` §4:

- :class:`ConfidenceSignals` — 5-signal dataclass (visibility / density /
  residual / curvature / temporal)
- :class:`ConfidenceCalibratorConfig` — sigmoid scales + ECE target
- :class:`ConfidenceCalibrator` — signal computation + sigmoid aggregation
- :class:`LogisticCalibrator` — post-train logistic regression for ``α, β``
- :func:`compute_ece` — Expected Calibration Error helper

Phase: SKELETON (T-Vision-CableState-Impl-Phase-2-Design-CC, 2026-05-04). Every
compute method raises :class:`NotImplementedError`; this module exists to lock
the public surface (R6) and the Phase 4 integration contract.

Calibration target: ``ECE < 5 %`` per parent memo §2.6.2 + §5.3. Coefficients
``(α [5], β scalar)`` fit via 1 k held-out val sample with 5-fold CV
(design memo §4.4).

R6 module boundary: imports restricted to :mod:`thread_isaac_lab.estimators.*`
+ :mod:`torch`. NO ``newton``, NO :mod:`thread_isaac_lab.envs`.
"""

from dataclasses import dataclass

import torch

from thread_isaac_lab.estimators.types import CableState40

# ---------------------------------------------------------------------------
# Constants mirrored from task_config.py + design memo §4 defaults.
# ---------------------------------------------------------------------------
_NUM_CABLE_SEGMENTS = 40  # mirrors CABLE_SEGMENTS

_DEFAULT_RESIDUAL_SCALE_M = 0.005  # s_residual sigmoid scale (5 mm)
_DEFAULT_TEMPORAL_SCALE_M = 0.005  # s_temporal sigmoid scale (5 mm)
_DEFAULT_NN_RADIUS_M = 0.010  # s_density radius (10 mm)
_DEFAULT_N_CAMERAS = 3  # 3-cam config (parent memo §2.2.1)
_DEFAULT_TARGET_ECE = 0.05  # parent memo §5.3 PASS gate
_DEFAULT_TARGET_ERROR_THRESHOLD_M = 0.005  # logistic regression label cutoff


@dataclass
class ConfidenceSignals:
    """Per-segment 5-signal raw outputs (parent memo §2.6.1).

    All tensors share the leading shape ``[40]`` (one value per cable
    segment). Ranges:

    - ``s_visibility``: ``{0, 1, 2, 3}`` count of cameras that see segment
    - ``s_density``: ``[0, ~50]`` cloud point count within
      ``nn_radius_m`` of the segment
    - ``s_residual``: ``(0, 1)`` ``sigmoid(-residual / scale)``
    - ``s_curvature``: ``(0, 1)`` ``sigmoid(-|κ_i - μ_κ| / σ_κ)``
    - ``s_temporal``: ``(0, 1)`` ``sigmoid(-temporal_diff / scale)``;
      identically ``0.5`` (neutral) at episode start when ``prev=None``.

    ``NaN`` segments (Phase 1 empty-bin output) yield zero on every signal
    (design memo §5.2 confidence row).
    """

    s_visibility: torch.Tensor  # [40] in {0, 1, 2, 3}
    s_density: torch.Tensor  # [40] in [0, 50]
    s_residual: torch.Tensor  # [40] in (0, 1)
    s_curvature: torch.Tensor  # [40] in (0, 1)
    s_temporal: torch.Tensor  # [40] in (0, 1)


@dataclass
class ConfidenceCalibratorConfig:
    """Stage E calibrator configuration (design memo §4.5.1).

    Attributes:
        residual_scale_m: ``s_residual`` sigmoid scale.
        temporal_scale_m: ``s_temporal`` sigmoid scale.
        nn_radius_m: ``s_density`` cloud-point radius.
        n_cameras: max value for ``s_visibility`` (3-cam = ``{0, 1, 2, 3}``).
        target_ece: PASS threshold for ECE; ``< 5 %`` per parent memo §5.3.
        target_error_threshold_m: logistic-regression label cutoff
            (segment "correct" iff ``error < threshold``).
    """

    residual_scale_m: float = _DEFAULT_RESIDUAL_SCALE_M
    temporal_scale_m: float = _DEFAULT_TEMPORAL_SCALE_M
    nn_radius_m: float = _DEFAULT_NN_RADIUS_M
    n_cameras: int = _DEFAULT_N_CAMERAS
    target_ece: float = _DEFAULT_TARGET_ECE
    target_error_threshold_m: float = _DEFAULT_TARGET_ERROR_THRESHOLD_M


class ConfidenceCalibrator:
    """Stage E per-segment confidence calibration.

    Public surface (design memo §4.5.1):

    - :meth:`compute_signals` extracts 5 raw signals from
      ``(seg, cloud, prev, cameras)`` inputs.
    - :meth:`aggregate` combines signals via
      ``sigmoid(α · signals + β)`` with coefficients fit by
      :class:`LogisticCalibrator`.

    Coefficients are loaded from a ``state_dict``-style artifact produced by
    :meth:`LogisticCalibrator.fit` during the Phase 4 calibration pass.

    R6: imports limited to :mod:`torch` + :mod:`thread_isaac_lab.estimators`.
    """

    def __init__(self, config: ConfidenceCalibratorConfig | None = None) -> None:
        self._config = config or ConfidenceCalibratorConfig()

    @property
    def config(self) -> ConfidenceCalibratorConfig:
        return self._config

    def compute_signals(
        self,
        seg: torch.Tensor,
        cloud: torch.Tensor,
        prev: CableState40 | None = None,
        camera_poses: list[torch.Tensor] | None = None,
        camera_intrinsics: list[torch.Tensor] | None = None,
    ) -> ConfidenceSignals:
        """Extract 5 raw signals per segment (parent memo §2.6.1).

        Args:
            seg: ``[40, 3]`` final per-segment positions (Stage D output,
                possibly with ``NaN`` segments — handled per design memo §5.2).
            cloud: ``[N_pts, 3]`` voxel-fused cloud.
            prev: Optional previous-frame ``CableState40``; powers
                ``s_temporal``. ``None`` at episode start collapses
                ``s_temporal`` to ``0.5`` (neutral).
            camera_poses: Optional list of per-camera ``[7]`` (px py pz qx qy
                qz qw) world poses for ``s_visibility`` projection check.
                Length must equal :attr:`ConfidenceCalibratorConfig.n_cameras`
                when provided.
            camera_intrinsics: Optional list of per-camera ``[3, 3]`` pinhole
                matrices, paired with ``camera_poses``. When ``None``, the
                ``s_visibility`` signal is set to ``0``.

        Returns:
            :class:`ConfidenceSignals` with all five fields shape ``[40]``.

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "ConfidenceCalibrator.compute_signals: design memo §4.1 — impl pending "
            "(T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )

    def aggregate(
        self,
        signals: ConfidenceSignals,
        coefficients: torch.Tensor,
        intercept: float,
    ) -> torch.Tensor:
        """Combine 5 signals with ``sigmoid(α · signals + β)`` (parent memo §2.6.2).

        Args:
            signals: 5-signal dataclass from :meth:`compute_signals`.
            coefficients: ``[5]`` weight vector ``α`` ordered
                ``(s_visibility, s_density, s_residual, s_curvature,
                s_temporal)``.
            intercept: scalar bias ``β``.

        Returns:
            ``[40]`` per-segment confidence ``c_i`` in ``[0, 1]``.

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "ConfidenceCalibrator.aggregate: design memo §4.2 — impl pending "
            "(T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )


class LogisticCalibrator:
    """Post-train logistic regression for ``(α [5], β scalar)`` (design memo §4.4).

    Phase 4 calibration loop:

        1. Run Phase-trained Stage A → D pipeline on 1 k held-out val scenes
        2. Collect ``(signals, per_seg_error)`` pairs (40 k pairs total)
        3. Label each segment ``correct = error < target_error_threshold_m``
        4. Fit logistic regression on
           ``(features, label) = (signals, correct)``
        5. 5-fold CV; report mean + std ECE on the held-out fold

    Returns ``(α, β)`` artifact saved alongside the DD-PINN checkpoint.

    R6: imports limited to :mod:`torch` + :mod:`thread_isaac_lab.estimators`.
    Logistic regression itself uses pure-tensor gradient descent (or
    :func:`torch.linalg.lstsq` warm start) — NOT scikit-learn — to keep the
    boundary tight at this layer.
    """

    def __init__(self, lr: float = 1e-2, max_iter: int = 1000) -> None:
        self._lr = lr
        self._max_iter = max_iter

    def fit(
        self,
        signals_list: list[ConfidenceSignals],
        per_seg_errors: list[torch.Tensor],
        target_error_threshold_m: float = _DEFAULT_TARGET_ERROR_THRESHOLD_M,
    ) -> tuple[torch.Tensor, float]:
        """Fit logistic regression coefficients.

        Args:
            signals_list: list of length ``N_val`` with per-scene
                :class:`ConfidenceSignals`.
            per_seg_errors: list of length ``N_val`` with per-scene ``[40]``
                error tensors.
            target_error_threshold_m: cutoff for the binary label.

        Returns:
            ``(coefficients [5], intercept scalar)`` ready for
            :meth:`ConfidenceCalibrator.aggregate`.

        Raises:
            NotImplementedError: SKELETON — Phase 4 impl pending.
        """
        raise NotImplementedError(
            "LogisticCalibrator.fit: design memo §4.4 — impl pending (T-Vision-CableState-Impl-Phase-4-Stage-DE)"
        )


def compute_ece(
    confidences: torch.Tensor,
    errors: torch.Tensor,
    threshold_m: float = _DEFAULT_TARGET_ERROR_THRESHOLD_M,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error (parent memo §5.3 PASS gate).

    ::

        ECE = Σ_b (|B_b| / N) · |acc(B_b) - conf(B_b)|

    where ``B_b`` is bin ``b`` of confidence range, ``acc`` is the empirical
    correct rate, and ``conf`` is the bin-mean confidence.

    Args:
        confidences: ``[N]`` predicted per-segment confidence in ``[0, 1]``.
        errors: ``[N]`` per-segment error in meters; ``correct = errors <
            threshold_m``.
        threshold_m: Cutoff for the "correct" label. Default 5 mm.
        n_bins: Number of equal-width confidence bins. Default 10.

    Returns:
        ECE as a Python ``float`` in ``[0, 1]``.

    Raises:
        NotImplementedError: SKELETON — Phase 4 impl pending.
    """
    raise NotImplementedError(
        "compute_ece: design memo §4.3 — impl pending (T-Vision-CableState-Impl-Phase-4-Stage-DE)"
    )
