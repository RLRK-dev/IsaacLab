# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Path A MVP-0 Phase A2 actual-impl skeleton (interface contract only).

Wires the existing R6-clean Phase A1 deliverables
(:class:`thread_isaac_lab.estimators.core.pose_estimator_core_v2.PoseEstimatorCoreV2`,
:class:`thread_isaac_lab.estimators.core.sam2_segmenter.Sam2Segmenter`,
:class:`thread_isaac_lab.estimators.core.pnp_pose_solver.PnpClipPoseSolver`)
into a single-image driver script for the upcoming Phase A2 actual install
execute child node (`T-Vision-Pose-MVP0-Impl-PhaseA2-SAM2-Install`).

This is a **skeleton + TODO + interface contract**. Production training,
eval-det benchmarks (N=10 / N=100), checkpoint management, and the §4 4-test
smoke acceptance gate (T1-T4) are deferred to the subsequent install-execute
CC session. Every TODO is annotated with the §-pointer back to the
PhaseA2-Design memo (`thread-vault/T-Vision-Pose-MVP0-Impl-PhaseA2-Design/a2_design.md`).

What this script DOES at skeleton stage:

- Defines the CLI contract for the single-image driver
  (``--input-image`` / ``--cad-cache`` / ``--camera-intrinsic`` / ``--device``).
- Provides factory wiring for ``PoseEstimatorCoreV2`` from disk artifacts
  (CAD ``.npz`` cache + camera intrinsic ``.json``) so the install-execute
  session only has to fill the ``forward`` body of ``Sam2Segmenter`` and
  ``establish_correspondence`` of ``PnpClipPoseSolver`` (a2_design §5).
- Marks each install-gated section with ``# TODO[A2-INSTALL]`` /
  ``# TODO[A2.5-CORRESPONDENCE]`` / ``# TODO[A3-E2E]`` so the impl task can
  grep its scope without re-reading the design memo.
- Emits a ``CoreOutputV2 → 14D pose tensor`` pack via
  :meth:`PoseEstimatorCoreV2.to_pose14d` for downstream env-side wiring.

What this script DOES NOT do (out-of-scope per task spec):

- Run actual SAM2 inference (gated on Phase A2 install + ``Sam2Segmenter.forward``
  body fill, a2_design §3 + §5.1).
- Run actual PnP convergence (gated on Phase A2.5 correspondence wire,
  a2_design §5.2).
- Run the 4-test smoke acceptance gate (T1-T4 in a2_design §4) — the gate
  driver is a separate child task ``T-Vision-Pose-MVP0-Impl-PhaseA2-Smoke``
  candidate per OQ-A2D-2.
- Modify any existing PhaseA1 deliverable (TOUCH FORBIDDEN: env files,
  ``task_config.py``, ``estimators/core/sam2_segmenter.py``,
  ``estimators/core/pnp_pose_solver.py``,
  ``estimators/core/pose_estimator_core_v2.py``, ``estimators/types.py``,
  ``estimators/input_adapter.py``).

Usage (post-install)::

    CUDA_VISIBLE_DEVICES=2 /home/rlrk/env_isaaclab6/bin/python \\
        thread_isaac_lab/scripts/vision/pose_mvp0_phase_a2.py \\
        --input-image /tmp/wrist_l_sample.png \\
        --cad-cache /home/rlrk/IsaacLab/data/clip/routing_clip_v1_vertices.npz \\
        --camera-intrinsic /home/rlrk/IsaacLab/data/camera_calibration/sim_default.json \\
        --target-clip-idx 0 \\
        --device cuda:2 \\
        --output-pose7 /tmp/clip_pose7_out.npy

Cross-references:

- a2_design.md §0-§10 (immediate input)
- LL-Vision-Pose-Design.md §3 (SAM2) / §4 (PnP+RANSAC) / §5 (MVP roadmap)
- LL-Vision-Pose-PhaseA1-Restart-InstallPathSummary.md §1 (install path
  candidates) / §3 (skeleton inventory)
- pose_estimator_core_v2.py (Stage 0-3 orchestrator, R6 lint 12/12 PASS)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

# Allow running ``python thread_isaac_lab/scripts/vision/pose_mvp0_phase_a2.py``
# from the repo root without prior ``pip install -e .``.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# R6-clean imports — all from ``thread_isaac_lab.estimators.*``. No newton,
# no env, no WristCameraManager. Verified by tests/test_estimator_module_boundary.py
# (12/12 PASS as of PhaseA1-Restart §3).
from thread_isaac_lab.estimators.core.pnp_pose_solver import (  # noqa: E402
    CameraCalibration,
    ClipPoseEstimate,
    PnpClipPoseSolver,
    PoseRegime,
    load_clip_cad,
)
from thread_isaac_lab.estimators.core.pose_estimator_core_v2 import (  # noqa: E402
    CoreOutputV2,
    PoseEstimatorCoreV2,
)
from thread_isaac_lab.estimators.core.roi_prior import CameraIntrinsics  # noqa: E402
from thread_isaac_lab.estimators.core.sam2_segmenter import (  # noqa: E402
    Sam2Backend,
    Sam2Config,
    Sam2Segmenter,
)
from thread_isaac_lab.estimators.types import EstimatorInputs  # noqa: E402

# ----------------------------------------------------------------------------
# Constants — sourced from a2_design.md / PhaseA1-Restart vault memo.
# These are CLI defaults; override at the command line.
# ----------------------------------------------------------------------------

# a2_design §3.1 — Candidate A primary HF repo.
DEFAULT_HF_REPO = "facebook/sam2.1-hiera-base-plus"

# a2_design §7.1 — cuda:2 PRO 4000 priority for offline replay.
DEFAULT_DEVICE = "cuda:2"

# a2_design §3.1 — confidence_threshold defaults mirror sam2_segmenter.py:99-100.
DEFAULT_CONF_HIGH = 0.85
DEFAULT_CONF_PREDICT = 0.5

# Sim default wrist-camera intrinsic resolution (from
# WristTiledCameraCfg analytical pinhole, parent OQ-4 placeholder).
DEFAULT_INTRINSIC_RES_HW = (480, 640)

# a2_design §4.1 / T4 — peak VRAM budget for smoke test.
SMOKE_VRAM_BUDGET_GIB = 4.0

# Routing target clip index default — first clip in the 5-clip layout.
DEFAULT_TARGET_CLIP_IDX = 0


# ----------------------------------------------------------------------------
# Run config dataclass — single source for CLI args + defaults.
# ----------------------------------------------------------------------------


@dataclass
class PhaseA2RunConfig:
    """Configuration bundle for one single-image Phase A2 driver run.

    Attributes:
        input_image: path to the wrist_L RGB image (PNG/JPG, HxWx3 uint8).
            Mock images are generated in-memory when ``None``.
        cad_cache: path to the cached CAD vertex ``.npz`` (see
            :func:`thread_isaac_lab.estimators.core.pnp_pose_solver.load_clip_cad`).
            ``None`` triggers a placeholder ``ClipCadModel`` for skeleton-only
            wiring smoke (no PnP convergence will succeed).
        camera_intrinsic: path to the JSON dump of camera K + dist coeffs
            (Charuco-calibrated for real cam, analytical for sim default).
            ``None`` triggers an analytical placeholder via :class:`CameraIntrinsics`.
        target_clip_idx: integer in [0, 5) selecting the routing target clip.
        device: torch device for SAM2 + tensor staging.
        sam2_backend: chosen install backend per a2_design §3 (Candidate A/B/C).
        sam2_hf_repo: HuggingFace repo id when ``sam2_backend == HUGGINGFACE``.
        output_pose7: optional path to dump the resulting ``[7]`` pose
            ``(t_xyz, q_xyzw)`` as numpy ``.npy`` for downstream consumption.
        output_diagnostics: optional path to dump the per-stage diagnostics
            JSON (regime, inlier count, reproj error).
    """

    input_image: str | None = None
    cad_cache: str | None = None
    camera_intrinsic: str | None = None
    target_clip_idx: int = DEFAULT_TARGET_CLIP_IDX
    device: str = DEFAULT_DEVICE
    sam2_backend: str = "huggingface"
    sam2_hf_repo: str = DEFAULT_HF_REPO
    output_pose7: str | None = None
    output_diagnostics: str | None = None


# ----------------------------------------------------------------------------
# CLI parsing.
# ----------------------------------------------------------------------------


def parse_cli(argv: list[str] | None = None) -> PhaseA2RunConfig:
    """Parse CLI args into a :class:`PhaseA2RunConfig`.

    Args:
        argv: optional argument vector for testability. Defaults to ``sys.argv[1:]``.

    Returns:
        a populated :class:`PhaseA2RunConfig`.
    """
    ap = argparse.ArgumentParser(
        description="Path A MVP-0 Phase A2 actual-impl skeleton (single-image driver)."
    )
    ap.add_argument("--input-image", default=None, help="Path to wrist_L RGB image (HxWx3 uint8).")
    ap.add_argument("--cad-cache", default=None, help="Path to clip CAD .npz (see load_clip_cad).")
    ap.add_argument("--camera-intrinsic", default=None, help="Path to camera intrinsic JSON.")
    ap.add_argument("--target-clip-idx", type=int, default=DEFAULT_TARGET_CLIP_IDX)
    ap.add_argument("--device", default=DEFAULT_DEVICE, help="torch device id (e.g. cuda:2 / cpu).")
    ap.add_argument(
        "--sam2-backend",
        choices=["huggingface", "facebookresearch"],
        default="huggingface",
        help="a2_design §3 install path selector (Candidate A/B).",
    )
    ap.add_argument("--sam2-hf-repo", default=DEFAULT_HF_REPO)
    ap.add_argument("--output-pose7", default=None, help="Optional .npy dump of [7] pose.")
    ap.add_argument("--output-diagnostics", default=None, help="Optional .json diagnostics dump.")
    args = ap.parse_args(argv)

    return PhaseA2RunConfig(
        input_image=args.input_image,
        cad_cache=args.cad_cache,
        camera_intrinsic=args.camera_intrinsic,
        target_clip_idx=args.target_clip_idx,
        device=args.device,
        sam2_backend=args.sam2_backend,
        sam2_hf_repo=args.sam2_hf_repo,
        output_pose7=args.output_pose7,
        output_diagnostics=args.output_diagnostics,
    )


# ----------------------------------------------------------------------------
# Input loaders — file path or mock fallback.
# ----------------------------------------------------------------------------


def load_input_image(path: str | None, device: str) -> torch.Tensor:
    """Load the input wrist_L RGB image as a ``[1, 3, H, W]`` float tensor in [0, 1].

    Args:
        path: filesystem path to a PNG/JPG. ``None`` returns a deterministic
            mock image so the wiring can be exercised without an asset.
        device: target torch device.

    Returns:
        ``[1, 3, H, W]`` float32 tensor on ``device``.

    Raises:
        FileNotFoundError: if ``path`` is provided but does not exist.
    """
    if path is None:
        # TODO[A2-INSTALL]: replace mock with sim Newton SensorTiledCamera
        # static frame once the install-execute session has SAM2 ready.
        # See a2_design §4.1 T2 for the smoke-test mock signature.
        h, w = DEFAULT_INTRINSIC_RES_HW
        rng = np.random.default_rng(seed=42)
        mock_uint8 = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        rgb = torch.from_numpy(mock_uint8).permute(2, 0, 1).float() / 255.0
        return rgb.unsqueeze(0).to(device)

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input image not found: {p}")
    # TODO[A2-INSTALL]: use cv2.imread or PIL.Image.open here. Deferred so
    # the skeleton stays import-light (no cv2 import needed for skeleton path).
    raise NotImplementedError(
        "load_input_image: real image read deferred to install-execute child"
        " (a2_design §4.1 T2). Pass --input-image=None for mock at skeleton stage."
    )


def load_camera_intrinsic(path: str | None, device: str) -> tuple[CameraIntrinsics, CameraCalibration]:
    """Load (or synthesize) camera intrinsic + calibration bundles.

    Two structures are returned because Stage 0 ROI uses
    :class:`CameraIntrinsics` (Warp kernel, fx/fy/cx/cy/H/W) while Stage 3 PnP
    uses :class:`CameraCalibration` (3x3 K + 5-vector dist coeffs).

    Args:
        path: optional JSON path. Schema (Charuco-calibrated):
            ``{"K": [[...], [...], [...]], "dist_coeffs": [...], "resolution": [W, H]}``.
            ``None`` synthesizes an analytical pinhole at
            :data:`DEFAULT_INTRINSIC_RES_HW` (placeholder; rejects the legacy
            (100, 100, 64, 64) sentinel per ``roi_prior.py`` __post_init__).
        device: target device hint (currently only used for symmetry with
            :func:`load_input_image` callers).

    Returns:
        a ``(CameraIntrinsics, CameraCalibration)`` pair.
    """
    if path is None:
        # TODO[A3-E2E]: swap analytical placeholder for the actual sim default
        # JSON dump (parent OQ-4, a2_design §1.4). Skeleton uses sentinel-safe
        # values that pass roi_prior.py:43-45 placeholder rejection.
        h, w = DEFAULT_INTRINSIC_RES_HW
        fx = fy = float(max(h, w))  # 1-pixel-per-radian-ish, not (100, 100)
        cx, cy = float(w) / 2.0, float(h) / 2.0
        intrinsics = CameraIntrinsics(fx=fx, fy=fy, cx=cx, cy=cy, H=h, W_img=w)
        K = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64)
        dist = np.zeros(5, dtype=np.float64)
        calib = CameraCalibration(K=K, dist_coeffs=dist, resolution=(w, h), source="analytical_skeleton")
        return intrinsics, calib

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Camera intrinsic not found: {p}")
    with open(p) as f:
        data = json.load(f)
    K = np.asarray(data["K"], dtype=np.float64)
    dist = np.asarray(data["dist_coeffs"], dtype=np.float64)
    w, h = int(data["resolution"][0]), int(data["resolution"][1])
    intrinsics = CameraIntrinsics(
        fx=float(K[0, 0]), fy=float(K[1, 1]), cx=float(K[0, 2]), cy=float(K[1, 2]), H=h, W_img=w
    )
    calib = CameraCalibration(
        K=K,
        dist_coeffs=dist,
        resolution=(w, h),
        source=str(data.get("source", str(p))),
    )
    return intrinsics, calib


def build_estimator_inputs(
    rgb: torch.Tensor,
    target_clip_idx: int,
    device: str,
) -> tuple[EstimatorInputs, torch.Tensor]:
    """Synthesize a minimal :class:`EstimatorInputs` + kinematic prior for skeleton runs.

    For a real run the env-side adapter
    (:class:`thread_isaac_lab.estimators.input_adapter.PoseEstimatorInputAdapter`)
    populates these from Newton ``body_q``. At skeleton stage we set
    placeholder zeros so the wiring is exercised without env import.

    Args:
        rgb: ``[1, 3, H, W]`` float tensor from :func:`load_input_image`.
        target_clip_idx: integer routing target clip index.
        device: target torch device.

    Returns:
        ``(EstimatorInputs, kinematic_prior_pose7)`` where
        ``kinematic_prior_pose7`` is ``[1, 7]`` ``(t_xyz, q_xyzw)`` in the
        camera frame.
    """
    b = rgb.shape[0]
    h, w = rgb.shape[-2:]
    depth = torch.zeros(b, 1, h, w, device=device)
    # 9 arm joints (7 arm + 2 gripper) is the env-side default; pad if needed.
    joint_state = torch.zeros(b, 9, device=device)
    # Wrist-L body pose [1, 7] — placeholder (origin, identity quat).
    wrist_pose = torch.tensor([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]], device=device).expand(b, 7).clone()
    # Finger positions [1, 2, 3] — placeholder zeros.
    finger_positions = torch.zeros(b, 2, 3, device=device)
    # Routing target indices — int64 broadcast.
    target_seg_idx = torch.zeros(b, dtype=torch.int64, device=device)
    target_clip_idx_t = torch.full((b,), target_clip_idx, dtype=torch.int64, device=device)

    inputs = EstimatorInputs(
        rgb_l=rgb,
        depth_l=depth,
        joint_state=joint_state,
        wrist_camera_pose_l=wrist_pose,
        finger_positions=finger_positions,
        routing_target_seg_idx=target_seg_idx,
        routing_target_clip_idx=target_clip_idx_t,
    )
    # TODO[A3-E2E]: kinematic prior should come from env-side `routing_target`
    # body pose (Newton body_q[clip_idx]). Skeleton uses identity at z=0.5 so
    # the PnP correspondence projection has a non-degenerate seed.
    prior_pose7 = torch.tensor(
        [[0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 1.0]], device=device, dtype=torch.float32
    ).expand(b, 7).clone()
    return inputs, prior_pose7


# ----------------------------------------------------------------------------
# Estimator factory.
# ----------------------------------------------------------------------------


def build_estimator_v2(cfg: PhaseA2RunConfig) -> PoseEstimatorCoreV2:
    """Wire the V2 Stage 0-3 orchestrator from disk artifacts + CLI choices.

    Args:
        cfg: parsed :class:`PhaseA2RunConfig`.

    Returns:
        a :class:`PoseEstimatorCoreV2` ready for ``forward``. The forward
        call will still raise :class:`NotImplementedError` until the install
        execute child fills ``Sam2Segmenter.forward`` and
        ``PnpClipPoseSolver.establish_correspondence`` (a2_design §5).
    """
    backend = (
        Sam2Backend.HUGGINGFACE if cfg.sam2_backend == "huggingface" else Sam2Backend.FACEBOOKRESEARCH
    )
    sam2_cfg = Sam2Config(
        backend=backend,
        hf_repo=cfg.sam2_hf_repo,
        device=cfg.device,
        confidence_threshold_high=DEFAULT_CONF_HIGH,
        confidence_threshold_predict=DEFAULT_CONF_PREDICT,
    )
    sam2 = Sam2Segmenter(sam2_cfg)

    intrinsics, calib = load_camera_intrinsic(cfg.camera_intrinsic, cfg.device)

    if cfg.cad_cache is None:
        # TODO[A3-E2E]: CAD cache .npz is built by a separate
        # `extract_clip_cad_cache.py` (a2_design §10.3 future artifact).
        # Skeleton path raises so the impl task hits a clear deferred-marker
        # rather than a silent passthrough.
        raise NotImplementedError(
            "build_estimator_v2: --cad-cache required (a2_design §1.4 + §10.3)."
            " Phase A3 e2e child will produce routing_clip_v1_vertices.npz."
        )
    cad = load_clip_cad(cfg.cad_cache)
    pnp_solver = PnpClipPoseSolver(camera=calib, cad=cad)

    return PoseEstimatorCoreV2(sam2=sam2, pnp_solver=pnp_solver, intrinsics=intrinsics)


# ----------------------------------------------------------------------------
# Driver — single-image forward + diagnostics emit.
# ----------------------------------------------------------------------------


def run_single_image(cfg: PhaseA2RunConfig) -> CoreOutputV2:
    """Run one Stage 0 + 1 + 2 + 3 forward over a single image.

    This is the minimal driver; the 4-test smoke acceptance gate
    (a2_design §4.1 T1-T4) is a separate orchestrator (deferred).

    Args:
        cfg: parsed :class:`PhaseA2RunConfig`.

    Returns:
        the :class:`CoreOutputV2` emitted by :meth:`PoseEstimatorCoreV2.forward`.

    Raises:
        NotImplementedError: until ``Sam2Segmenter.forward`` and
            ``PnpClipPoseSolver.establish_correspondence`` are filled in.
    """
    estimator = build_estimator_v2(cfg)
    rgb = load_input_image(cfg.input_image, cfg.device)
    inputs, prior_pose7 = build_estimator_inputs(rgb, cfg.target_clip_idx, cfg.device)

    # TODO[A2-INSTALL]: wrap with torch.cuda.synchronize + perf_counter once
    # SAM2 is wired so the latency budget (a2_design §7.3, ~30-50ms target)
    # can be measured against the smoke gate (T1-T4 §4.1).
    return estimator.forward(inputs, prior_pose7)


def emit_pose7(output: CoreOutputV2, batch_idx: int = 0) -> torch.Tensor:
    """Pack the per-batch :class:`ClipPoseEstimate` into a ``[7]`` tensor.

    Convention: ``(t_x, t_y, t_z, q_x, q_y, q_z, q_w)`` matching Newton
    ``body_q`` order. Mirrors :meth:`PnpClipPoseSolver.to_pose7_torch` but
    operates on the orchestrator output without a separate device move.

    Args:
        output: :class:`CoreOutputV2` from :func:`run_single_image`.
        batch_idx: which batch element to extract (default 0 for B=1 driver).

    Returns:
        ``[7]`` float32 CPU tensor.
    """
    estimate: ClipPoseEstimate = output.pose_per_batch[batch_idx]
    pose7_np = np.concatenate([estimate.translation, estimate.quat_xyzw], axis=0).astype(np.float32)
    return torch.from_numpy(pose7_np)


def collect_diagnostics(output: CoreOutputV2, batch_idx: int = 0) -> dict:
    """Gather a JSON-friendly diagnostic dict for one batch element.

    Args:
        output: :class:`CoreOutputV2` from :func:`run_single_image`.
        batch_idx: which batch element to summarise.

    Returns:
        a dict with regime / inlier_count / reproj_error_px / mask shape
        and seg_regime, suitable for ``json.dump``.
    """
    pose: ClipPoseEstimate = output.pose_per_batch[batch_idx]
    seg_regime = output.seg_regime_per_batch[batch_idx]
    masks_shape = tuple(int(s) for s in output.sam2_output.masks.shape)
    return {
        "pose_regime": pose.regime.value if isinstance(pose.regime, PoseRegime) else str(pose.regime),
        "inlier_count": int(pose.inlier_count),
        "reproj_error_px": float(pose.reproj_error_px),
        "translation": [float(x) for x in pose.translation.tolist()],
        "quat_xyzw": [float(x) for x in pose.quat_xyzw.tolist()],
        "sam2_masks_shape": list(masks_shape),
        "seg_regime": seg_regime.value if hasattr(seg_regime, "value") else str(seg_regime),
        "keypoint_method": output.diagnostics.get("keypoint_method", "unknown"),
        "keypoint_count": int(output.keypoints_per_batch[batch_idx].points.shape[0]),
    }


# ----------------------------------------------------------------------------
# Smoke acceptance gate stubs (a2_design §4.1) — deferred to subsequent task.
# ----------------------------------------------------------------------------


def smoke_t1_imports() -> bool:
    """T1: Import smoke (a2_design §4.1 row 1).

    Returns ``True`` iff every install-gated module import succeeds. Skeleton
    semantics: the imports at the top of this file already exercise the same
    set, so this stub returns the truthiness of the module-level binding
    presence.
    """
    # TODO[A2-INSTALL]: run actual ``from transformers import Sam2Model,
    # Sam2Processor`` here once the install lands (a2_design §3.1 step 5).
    return all(
        symbol is not None
        for symbol in (Sam2Segmenter, PnpClipPoseSolver, PoseEstimatorCoreV2, EstimatorInputs)
    )


def smoke_t2_mock_inference(_cfg: PhaseA2RunConfig) -> bool:
    """T2: Mock RGB inference (a2_design §4.1 row 2).

    Skeleton stub. The install-execute session must replace the body with
    an actual ``Sam2Segmenter.forward`` call against a 1024×1024 mock and
    assert ``masks.shape == (1, K, 1024, 1024)`` + non-NaN.
    """
    raise NotImplementedError(
        "smoke_t2_mock_inference: Phase A2 install-execute child responsibility."
        " See a2_design §4.1 T2 + §5.1.1 for body-fill skeleton."
    )


def smoke_t3_iou_range(_cfg: PhaseA2RunConfig) -> bool:
    """T3: iou_score sanity range (a2_design §4.1 row 3)."""
    raise NotImplementedError(
        "smoke_t3_iou_range: deferred to install-execute child (a2_design §4.1 T3)."
    )


def smoke_t4_vram_budget(_cfg: PhaseA2RunConfig) -> bool:
    """T4: VRAM budget verify (a2_design §4.1 row 4, ≤ 4 GiB peak).

    Skeleton stub: the install-execute session should call
    ``torch.cuda.max_memory_allocated`` after T2 and gate against
    :data:`SMOKE_VRAM_BUDGET_GIB`.
    """
    raise NotImplementedError(
        "smoke_t4_vram_budget: deferred to install-execute child (a2_design §4.1 T4)."
    )


# ----------------------------------------------------------------------------
# Entry point.
# ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        process exit code: 0 on graceful skeleton-mode exit, 2 on the expected
        ``NotImplementedError`` from the install-gated forward call (so the
        smoke gate driver can distinguish "skeleton OK" from "broken wiring").
    """
    cfg = parse_cli(argv)
    if not smoke_t1_imports():
        print("FAIL: import smoke (T1) — module wiring broken before install.", file=sys.stderr)
        return 1

    print(f"[skeleton] device={cfg.device} backend={cfg.sam2_backend} repo={cfg.sam2_hf_repo}")
    print(f"[skeleton] target_clip_idx={cfg.target_clip_idx}")
    print(f"[skeleton] cad_cache={cfg.cad_cache} intrinsic={cfg.camera_intrinsic}")

    t0 = time.perf_counter()
    try:
        output = run_single_image(cfg)
    except NotImplementedError as exc:
        # Expected at skeleton stage — print pointer and exit 2 so the smoke
        # gate driver can treat it as "skeleton OK, install pending".
        print(f"[skeleton] NotImplementedError (expected pre-install): {exc}", file=sys.stderr)
        return 2

    dt_ms = (time.perf_counter() - t0) * 1000.0
    pose7 = emit_pose7(output)
    diag = collect_diagnostics(output)
    diag["wall_ms"] = round(dt_ms, 3)

    print(f"[skeleton] pose7 = {pose7.tolist()}")
    print(f"[skeleton] diagnostics = {json.dumps(diag, indent=2)}")

    if cfg.output_pose7:
        np.save(cfg.output_pose7, pose7.numpy())
        print(f"[skeleton] pose7 saved to {cfg.output_pose7}")
    if cfg.output_diagnostics:
        os.makedirs(os.path.dirname(cfg.output_diagnostics) or ".", exist_ok=True)
        with open(cfg.output_diagnostics, "w") as f:
            json.dump(diag, f, indent=2)
        print(f"[skeleton] diagnostics saved to {cfg.output_diagnostics}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
