# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Estimator input / label boundary types (PROPOSE v2 narrowed for MVP-0A).

Per v3.1 Appendix D §D.4 + v3.2 Appendix H §H.4. Narrowed scope:
- Single-camera (wrist_L) per v3 §7.1 literal (CC6 MISSED-4)
- No ``PoseEstimate14D`` placeholder (Stage 2-4 deferred per CC6 NHA-7)
- Decorator name-based check + grep test (CC4-6 acknowledges name-based limit)

Phase 2 (T-Vision-CableState L1.A.2) cable-state extension SKELETON:
- :class:`CableState40` — 40-segment per-segment 3D position + confidence
- :class:`EstimatorInputs` Optional fields for multi-cam (wrist_R + overhead),
  per ``thread-vault/06-Knowledge/LL-Vision-CableState-Design.md`` §4.4 + §6.1.
  All Phase 2 fields default to ``None`` for backward compat with Phase 1
  callers (e.g., :class:`thread_isaac_lab.estimators.core.pose_estimator_core.PoseEstimatorCorePhase1`).
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field

import torch


@dataclass
class CableState40:
    """Per-segment 3D position + confidence (T-Vision-CableState L1.A.2 output).

    40 segments × 3 (xyz) world-frame, mirrors
    ``thread_isaac_lab.configs.task_config.CABLE_SEGMENTS=40``
    (``CABLE_SEG_LEN=0.015`` m, total cable length ~0.6 m). Per
    ``thread-vault/06-Knowledge/LL-Vision-CableState-Design.md`` §6.1.

    Defined BEFORE :class:`EstimatorInputs` so that the
    ``previous_cable_estimate`` Optional field can reference it without a
    string forward declaration.
    """

    positions: torch.Tensor  # [B, 40, 3] world-frame xyz [m]
    confidences: torch.Tensor  # [B, 40] in [0, 1]
    stage_diagnostics: dict = field(default_factory=dict)
    # ↑ per-stage debug metrics (var_ratio, n_pts, iter_count, ...). See
    # design memo §5.4 (per-stage diagnostics for failure attribution).


@dataclass
class EstimatorInputs:
    """ONLY allowed inputs to estimator forward (v3.1 Appendix D §D.2 whitelist).

    Phase 1 (MVP-0A) narrowed: single camera (wrist_L), no previous estimate
    yet (Stage 4 temporal filter is MVP-2C). Robot kinematics fields permitted
    per v3.1 D.2 (joint state + wrist body pose are robot-measurable).

    Phase 2 (T-Vision-CableState L1.A.2) cable-state extension fields are
    Optional[None] for backward compat — Phase 1 callers (e.g.,
    :class:`thread_isaac_lab.estimators.core.pose_estimator_core.PoseEstimatorCorePhase1`)
    can omit them. Per
    ``thread-vault/06-Knowledge/LL-Vision-CableState-Design.md`` §4.4:
      - rgb_r / depth_r / wrist_camera_pose_r / wrist_intrinsics_l/r:
        right-wrist + per-cam intrinsics (robot-measurable)
      - rgb_oh / depth_oh / overhead_camera_pose / overhead_intrinsics:
        world-fixed overhead cam (robot-known constant calibration)
      - previous_cable_estimate: temporal smoothness anchor (Stage D L_temp)

    R6 boundary: all new field names avoid forbidden substrings
    (``body_q`` / ``gt_`` / ``ground_truth`` / ``state_0``); decorator
    :func:`enforce_input_boundary` and grep test
    ``tests/test_estimator_input_boundary.py`` remain effective.
    """

    # Phase 1 (MVP-0A wrist_L, mandatory).
    rgb_l: torch.Tensor  # [B, 3, H, W] float32 in [0, 1]
    depth_l: torch.Tensor  # [B, 1, H, W] float32 [m]
    joint_state: torch.Tensor  # [B, J] arm joint pos + vel (robot-measurable)
    wrist_camera_pose_l: torch.Tensor  # [B, 7] (px py pz qx qy qz qw) — derived from body_q[wrist_L] env-side
    finger_positions: torch.Tensor  # [B, 2, 3] world xyz for (left, right) fingers — pre-sliced env-side; v2.1 P3
    routing_target_seg_idx: torch.Tensor  # [B] int (orchestrator-provided integer)
    routing_target_clip_idx: torch.Tensor  # [B] int

    # Phase 2 (T-Vision-CableState L1.A.2 SKELETON, impl pending).
    # All Optional[None] — Phase 1 callers leave these None.
    rgb_r: torch.Tensor | None = None  # [B, 3, H, W] right-wrist RGB in [0, 1]
    depth_r: torch.Tensor | None = None  # [B, 1, H, W] right-wrist depth [m]
    wrist_camera_pose_r: torch.Tensor | None = None  # [B, 7] env-side derived (right wrist body pose)
    wrist_intrinsics_l: torch.Tensor | None = None  # [B, 3, 3] left-wrist pinhole K
    wrist_intrinsics_r: torch.Tensor | None = None  # [B, 3, 3] right-wrist pinhole K
    rgb_oh: torch.Tensor | None = None  # [B, 3, H_oh, W_oh] overhead RGB in [0, 1]
    depth_oh: torch.Tensor | None = None  # [B, 1, H_oh, W_oh] overhead depth [m]
    overhead_camera_pose: torch.Tensor | None = None  # [B, 7] world-fixed (calibrated)
    overhead_intrinsics: torch.Tensor | None = None  # [B, 3, 3] overhead pinhole K
    previous_cable_estimate: CableState40 | None = None  # Stage D temporal anchor


@dataclass
class EstimatorLabelsForEvalOnly:
    """GT labels for OFFLINE EVALUATION ONLY (v3.1 Appendix D §D.4).

    Must NOT be passed to estimator forward. Only ``EvalPoseEstimator.compare``
    may access both ``EstimatorInputs`` and these labels at the same call site.
    """

    gt_class_map: torch.Tensor  # [B, H, W] uint8 (class id per pixel from shape_index LUT)
    gt_cable_body_q: torch.Tensor | None = None  # [B, 40, 7] (Phase 1: optional)
    gt_clip_pose: torch.Tensor | None = None  # [B, 5, 7] (Phase 1: optional)
    gt_target_seg_idx: torch.Tensor | None = None  # [B] (Phase 1: optional)


# Forbidden parameter-name substrings for runtime decorator (CC4-6: name-based,
# bypassable via aliasing — grep test in tests/ is the real R6 enforcement).
_FORBIDDEN_PARAM_SUBSTRINGS = (
    "body_q",
    "gt_",
    "ground_truth",
    "state_0",
)


def enforce_input_boundary(fn: Callable) -> Callable:
    """Decorator: reject estimator forward signatures that smuggle GT-like params.

    Limitations (CC4-6 ACCEPT):
      - Name-based only; does NOT inspect tensor content or dataclass fields.
      - Aliased imports (e.g., ``from newton import state as s_; s_.body_q``)
        bypass this decorator. The accompanying grep test
        ``tests/test_estimator_input_boundary.py`` is the real R6 enforcement.
    """
    sig = inspect.signature(fn)
    for pname in sig.parameters:
        if any(sub in pname.lower() for sub in _FORBIDDEN_PARAM_SUBSTRINGS):
            raise TypeError(
                f"{fn.__qualname__}: forbidden GT-like parameter '{pname}'. See v3.1 Appendix D.2 for allowed inputs."
            )
    return fn


# Class IDs aligned with Phase 0 dataset LUT (data/mvp0a_phase0_dataset/LABELS_ONLY/).
class_legend = {
    0: "background_no_hit",
    1: "cable",
    2: "clip",
    3: "gripper_finger",
    4: "robot_arm",
    5: "other_static",
}

# MVP-0A Phase 1 narrowed: 3 active output channels matching Phase 0 GT availability.
# (clip class 2 has 0 pixels in current AC env wrist views per Phase 0 verification;
# arm and static are auxiliary; cable + gripper are MVP-0A primary metrics.)
PHASE1_OUTPUT_CLASSES = [1, 3, 5]  # cable, gripper, static
PHASE1_NUM_CLASSES = len(PHASE1_OUTPUT_CLASSES)
