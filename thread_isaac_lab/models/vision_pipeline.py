# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""vision_pipeline.py — Camera-based cable midpoint estimation (SOMA Stage 1-3).

Stage 1 (WHAT):  HSV color filter → cable binary mask (A6b)
Stage 2 (WHERE): Depth back-projection → 3D point cloud (A7)
Stage 3 (HOW):   PCA-center estimation → cable_midpoint (A7)

Usage:
    pipeline = VisionPipelineStage1to3(scene, camera_keys)
    midpoint, meta = pipeline.estimate_cable_midpoint()

Phase 2 extension (T-Vision-CableState L1.A.2):
    pipeline = MultiCamCableStatePipeline(scene, camera_keys)
    result = pipeline.estimate(finger_positions=...)  # CableStatePhase1Result
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from thread_isaac_lab.scripts.camera_utils import _quat_to_rotation_matrix

# HSV parameters for cable detection (confirmed in A6b: IoU=0.93)
_HSV_PARAMS = {
    "h_min": 20,
    "h_max": 40,
    "s_min": 25,
    "v_min": 150,
}

# Minimum valid points for estimation
_MIN_POINTS = 50

# Minimum PCA variance ratio for 1st component
_MIN_PCA_VARIANCE_RATIO = 0.5


class VisionPipelineStage1to3:
    """Camera-based cable midpoint estimation pipeline.

    Combines HSV color segmentation (Stage 1), depth back-projection (Stage 2),
    and PCA-center estimation (Stage 3) for cable_midpoint_pos.

    Args:
        scene: InteractiveScene with cameras.
        camera_keys: List of (short_name, scene_key) tuples.
        hsv_params: Optional HSV override dict (h_min, h_max, s_min, v_min).
    """

    def __init__(
        self,
        scene,
        camera_keys: list[tuple[str, str]],
        hsv_params: dict | None = None,
    ):
        self._scene = scene
        self._camera_keys = camera_keys
        self._hsv = hsv_params or _HSV_PARAMS
        self._prev_midpoint: np.ndarray | None = None
        self._fallback_count = 0
        self._call_count = 0

    def reset(self):
        """Reset state (call at episode start)."""
        self._prev_midpoint = None
        self._fallback_count = 0
        self._call_count = 0

    # ------------------------------------------------------------------
    # Stage 1: HSV color segmentation (WHAT)
    # ------------------------------------------------------------------

    def _detect_cable_mask(self, rgb: np.ndarray) -> np.ndarray:
        """HSV color filter for cable. Closing only (no opening — 1px cable)."""
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([self._hsv["h_min"], self._hsv["s_min"], self._hsv["v_min"]])
        upper = np.array([self._hsv["h_max"], 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    # ------------------------------------------------------------------
    # Stage 2: Depth back-projection (WHERE)
    # ------------------------------------------------------------------

    @staticmethod
    def _backproject_mask(
        mask: np.ndarray,
        depth: np.ndarray,
        K: np.ndarray,
        cam_pos: np.ndarray,
        cam_quat_ros: np.ndarray,
    ) -> np.ndarray:
        """Back-project masked pixels to 3D world coordinates.

        Returns (N, 3) float32 array of world-frame points.
        """
        ys, xs = np.nonzero(mask > 127)
        if len(ys) == 0:
            return np.empty((0, 3), dtype=np.float32)

        depths = depth[ys, xs]
        valid = np.isfinite(depths) & (depths > 0) & (depths < 100)
        ys, xs, depths = ys[valid], xs[valid], depths[valid]

        if len(ys) == 0:
            return np.empty((0, 3), dtype=np.float32)

        fx, fy = K[0, 0], K[1, 1]
        cx, cy = K[0, 2], K[1, 2]

        x_cam = (xs.astype(np.float64) - cx) * depths / fx
        y_cam = (ys.astype(np.float64) - cy) * depths / fy
        z_cam = depths.astype(np.float64)

        p_cam = np.stack([x_cam, y_cam, z_cam], axis=-1)
        R = _quat_to_rotation_matrix(cam_quat_ros)
        p_world = (R @ p_cam.T).T + cam_pos.astype(np.float64)
        return p_world.astype(np.float32)

    # ------------------------------------------------------------------
    # Stage 3: PCA-center estimation (HOW)
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_pca_center(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        """PCA: project onto 1st component, find midpoint of extremes.

        Returns (midpoint, direction, variance_ratio).
        """
        centroid = points.mean(axis=0)
        centered = points - centroid
        _, s, Vt = np.linalg.svd(centered, full_matrices=False)
        direction = Vt[0]
        projections = centered @ direction
        t_min, t_max = projections.min(), projections.max()
        t_mid = (t_min + t_max) / 2.0
        midpoint = centroid + t_mid * direction
        # Variance ratio: how much of total variance is in 1st component
        total_var = (s**2).sum()
        var_ratio = float((s[0] ** 2) / max(total_var, 1e-12))
        return midpoint.astype(np.float32), direction.astype(np.float32), var_ratio

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def estimate_cable_midpoint(self, dt: float = 0.0) -> tuple[np.ndarray, dict]:
        """Run full pipeline: mask → 3D → PCA-center.

        Args:
            dt: Physics dt for camera update.

        Returns:
            (midpoint_xyz, metadata) where midpoint is (3,) np.float32.
            If estimation fails, returns fallback (previous value).
        """
        self._call_count += 1
        all_points = []
        per_camera = {}

        for short, cam_key in self._camera_keys:
            try:
                cam = self._scene[cam_key]
                if dt > 0:
                    cam.update(dt)

                # RGB
                rgb_t = cam.data.output.get("rgb")
                if rgb_t is None:
                    per_camera[short] = {"status": "no_rgb", "points": 0}
                    continue
                rgb = rgb_t[0].cpu().numpy()
                if rgb.shape[-1] == 4:
                    rgb = rgb[:, :, :3]
                rgb = rgb.astype(np.uint8)

                # Depth
                dep_t = cam.data.output.get("distance_to_image_plane")
                if dep_t is None:
                    per_camera[short] = {"status": "no_depth", "points": 0}
                    continue
                dep = dep_t[0].cpu().numpy()
                if dep.ndim == 3:
                    dep = dep[:, :, 0]

                # Stage 1: Cable mask
                mask = self._detect_cable_mask(rgb)
                mask_px = int(np.sum(mask > 127))

                # Stage 2: Back-project
                cam_pos = cam.data.pos_w[0].cpu().numpy()
                cam_quat = cam.data.quat_w_ros[0].cpu().numpy()
                K = cam.data.intrinsic_matrices[0].cpu().numpy()
                points = self._backproject_mask(mask, dep, K, cam_pos, cam_quat)

                per_camera[short] = {
                    "status": "ok",
                    "mask_px": mask_px,
                    "points": points.shape[0],
                }
                if points.shape[0] > 0:
                    all_points.append(points)

            except Exception as e:
                per_camera[short] = {"status": f"error: {e}", "points": 0}

        meta = {
            "per_camera": per_camera,
            "total_points": 0,
            "method": "fallback",
            "fallback": True,
            "pca_variance_ratio": 0.0,
        }

        # Merge all points
        if all_points:
            merged = np.concatenate(all_points, axis=0)
            meta["total_points"] = merged.shape[0]
        else:
            merged = np.empty((0, 3), dtype=np.float32)

        # Fallback check 1: too few points
        if merged.shape[0] < _MIN_POINTS:
            return self._fallback(meta, reason=f"too_few_points({merged.shape[0]})")

        # Stage 3: PCA-center
        midpoint, direction, var_ratio = self._estimate_pca_center(merged)
        meta["pca_variance_ratio"] = round(var_ratio, 4)
        meta["pca_direction"] = direction.tolist()

        # Fallback check 2: scattered point cloud (PCA not useful)
        if var_ratio < _MIN_PCA_VARIANCE_RATIO:
            return self._fallback(meta, reason=f"low_pca_variance({var_ratio:.3f})")

        # Success
        meta["method"] = "pca_center"
        meta["fallback"] = False
        self._prev_midpoint = midpoint.copy()
        return midpoint, meta

    def _fallback(self, meta: dict, reason: str) -> tuple[np.ndarray, dict]:
        """Return previous estimate or zero."""
        self._fallback_count += 1
        meta["fallback_reason"] = reason
        if self._prev_midpoint is not None:
            return self._prev_midpoint.copy(), meta
        # No previous — return cable center estimate (world-frame default)
        return np.array([0.3, 0.0, 0.755], dtype=np.float32), meta

    def get_fallback(self) -> np.ndarray:
        """Get fallback value (previous estimate or default)."""
        if self._prev_midpoint is not None:
            return self._prev_midpoint.copy()
        return np.array([0.3, 0.0, 0.755], dtype=np.float32)

    @property
    def fallback_rate(self) -> float:
        """Fraction of calls that used fallback."""
        if self._call_count == 0:
            return 0.0
        return self._fallback_count / self._call_count


# ===========================================================================
# Stage A.3 / Stage B extension prep (T-Vision-CableState L1.A.2 SKELETON)
#
# Per ``thread-vault/06-Knowledge/LL-Vision-CableState-Design.md`` §2.2.4
# (Stage A.3: multi-cam fusion + voxel downsample) and §2.3.2 (Stage B.2:
# 40-bin arc-length discretization).
#
# These module-level helpers extend the existing single-midpoint pipeline
# (:class:`VisionPipelineStage1to3` above, unchanged) toward 40-segment cable
# state estimation. Impl pending in ``CC-L1A-Cable-State-Impl``
# (state.md §4 trigger). The class-based pipeline signature is preserved so
# Phase 1 callers (SOMA Stage 1-3 single-midpoint) keep working unchanged.
# ===========================================================================


def voxel_downsample_points(
    points: np.ndarray,
    voxel_size_m: float = 0.002,
) -> np.ndarray:
    """Voxel-downsample a 3D point cloud (Stage A.3, design memo §2.2.4).

    Hashes each point to its voxel center and keeps a single representative per
    voxel. Avoids stacking-density bias when merging clouds from overlapping
    cameras (3-cam configuration, design memo §2.2.1). Voxel size is chosen
    relative to cable geometry: cable radius = 4 mm, segment length = 15 mm,
    so a 2 mm voxel preserves shape information while bounding ``M``.

    Implementation: floor each coordinate to its voxel index, dedupe with
    :func:`numpy.unique` (O(N log N)), and return the centroid of points sharing
    the same voxel (mean within voxel for sub-voxel precision).

    Args:
        points: [N, 3] world-frame point cloud (float32). May be empty.
        voxel_size_m: voxel edge length in meters. Default 0.002 (design memo
            §2.2.4 default; ε=2 mm). Must be positive.

    Returns:
        [M, 3] deduplicated cloud, ``M <= N``. Expected ``M ~= 1500-3000`` for
        a 3-cam merged cloud per design memo §2.2.4. Output dtype matches input
        (float32 expected).
    """
    if points.size == 0:
        return np.empty((0, 3), dtype=points.dtype if points.dtype != object else np.float32)
    if voxel_size_m <= 0:
        raise ValueError(f"voxel_size_m must be positive, got {voxel_size_m}")

    pts64 = points.astype(np.float64, copy=False)
    voxel_idx = np.floor(pts64 / voxel_size_m).astype(np.int64)
    # Pack 3 int64 voxel coords into a single key for unique-grouping.
    # np.unique on a structured row view is more memory-efficient than hashing.
    keys = np.ascontiguousarray(voxel_idx).view(np.dtype((np.void, voxel_idx.dtype.itemsize * 3)))
    _, inverse = np.unique(keys, return_inverse=True)
    inverse = np.asarray(inverse, dtype=np.int64).reshape(-1)
    n_groups = int(inverse.max()) + 1 if inverse.size else 0

    sums = np.zeros((n_groups, 3), dtype=np.float64)
    counts = np.zeros(n_groups, dtype=np.int64)
    np.add.at(sums, inverse, pts64)
    np.add.at(counts, inverse, 1)
    centroids = sums / counts[:, None]
    return centroids.astype(points.dtype if np.issubdtype(points.dtype, np.floating) else np.float32)


def discretize_arc_length_40bins(
    points: np.ndarray,
    direction: np.ndarray,
    centroid: np.ndarray,
    num_bins: int = 40,
) -> tuple[np.ndarray, np.ndarray]:
    """40-bin arc-length discretization along a PCA principal direction.

    Extends the single-midpoint :meth:`VisionPipelineStage1to3._estimate_pca_center`
    above to per-bin centroids (Stage B.2 of the cable-state pipeline). Algorithm
    per design memo §2.3.2:

        1. Project each point onto ``direction``: ``t_i = (P_i - centroid) · d``
        2. Bin width: ``w = (t_max - t_min) / num_bins``
        3. For each bin ``k ∈ {0..num_bins-1}``::

               mask_k = (t_min + k*w <= t_i < t_min + (k+1)*w)
               P̂_seg(k) = mean(P_i where mask_k)

        4. Empty bin → NaN-fill (downstream Stage D temporal interp infills).
        5. Per design memo §2.3.3 ``bin_counts`` < 5 → warn, < 1 → mark for infill.

    Args:
        points: [N, 3] world-frame point cloud (float32).
        direction: [3] PCA 1st principal direction (unit vector).
        centroid: [3] cloud centroid (matches the centroid used to compute
            ``direction``).
        num_bins: number of arc-length bins. Default 40, mirrors
            ``thread_isaac_lab.configs.task_config.CABLE_SEGMENTS=40``.

    Returns:
        ``(seg_positions, bin_counts)`` where ``seg_positions`` is
        ``[num_bins, 3]`` per-bin centroid (NaN-filled for empty bins) and
        ``bin_counts`` is ``[num_bins]`` integer count per bin.
    """
    if num_bins <= 0:
        raise ValueError(f"num_bins must be positive, got {num_bins}")
    seg = np.full((num_bins, 3), np.nan, dtype=np.float32)
    counts = np.zeros(num_bins, dtype=np.int64)
    if points.size == 0:
        return seg, counts

    pts = points.astype(np.float64, copy=False)
    d = np.asarray(direction, dtype=np.float64).reshape(3)
    c = np.asarray(centroid, dtype=np.float64).reshape(3)
    t = (pts - c) @ d
    t_min = float(t.min())
    t_max = float(t.max())
    span = t_max - t_min
    if not np.isfinite(span) or span <= 0:
        # Degenerate: all points project to the same scalar — single bin holds all.
        seg[0] = pts.mean(axis=0).astype(np.float32)
        counts[0] = pts.shape[0]
        return seg, counts

    # Bin assignment using indices in [0, num_bins-1] via floor ratio.
    ratio = (t - t_min) / span
    bin_idx = np.floor(ratio * num_bins).astype(np.int64)
    bin_idx = np.clip(bin_idx, 0, num_bins - 1)  # right edge inclusive

    sums = np.zeros((num_bins, 3), dtype=np.float64)
    np.add.at(sums, bin_idx, pts)
    np.add.at(counts, bin_idx, 1)
    nonempty = counts > 0
    seg[nonempty] = (sums[nonempty] / counts[nonempty, None]).astype(np.float32)
    return seg, counts


# ===========================================================================
# Stage A→B end-to-end pipeline class (T-Vision-CableState-Impl-Phase-1)
#
# Per ``thread-vault/06-Knowledge/LL-Vision-CableState-Design.md``:
#   §2.2 (Stage A.1 mask + A.2 backproject + A.3 fusion)
#   §2.3 (Stage B PCA + 40-bin)
#   §2.3.2 anchoring orientation (handedness)
#   §3.5 anchor source priority (Tier 1 grasp finger / Tier 3 t_min default)
#   §4.3 3-cam recommendation (wrist L/R + overhead)
#
# Phase 1 scope: Stage A→B only (CPU-runnable). Stage C/D/E impl pending in
# subsequent phases (T-Vision-CableState-Impl-Phase-2/3/4 future tasks).
# ===========================================================================


# Phase 1 default thresholds, derived from design memo §2.2.4 + §2.3.3.
_DEFAULT_VOXEL_SIZE_M = 0.002
_DEFAULT_NUM_BINS = 40  # mirrors task_config.CABLE_SEGMENTS
_DEFAULT_VAR_RATIO_MIN = 0.6  # design memo §2.3.3 Stage B fail threshold
_DEFAULT_MIN_MERGED_PTS = 800  # design memo §2.2.4 Stage A failure gate
_DEFAULT_BIN_COUNT_WARN = 5  # design memo §2.3.3


@dataclass
class CableStatePhase1Result:
    """Stage A→B output (Phase 1, design memo §6.1 ``CableState40`` precursor).

    Phase 1 returns 40-bin centroid positions only (no confidence yet — Stage E
    is Phase 2+). Empty bins are ``NaN``-filled; ``bin_counts`` lets the caller
    distinguish "estimated" vs "infill needed".
    """

    seg_positions: np.ndarray  # [num_bins, 3] float32, NaN for empty bins
    bin_counts: np.ndarray  # [num_bins] int64
    var_ratio: float  # PCA 1st-component variance ratio
    n_pts_merged: int  # voxel-downsampled cloud size
    fallback_reason: str | None = None  # None on success, else reason
    per_camera: dict = field(default_factory=dict)  # {cam_short: {mask_px, points, status}}
    pca_direction: np.ndarray | None = None  # [3] float32 (post sign-anchor)
    pca_centroid: np.ndarray | None = None  # [3] float32

    @property
    def succeeded(self) -> bool:
        """True iff Stage A→B produced a usable estimate (no fallback)."""
        return self.fallback_reason is None

    @property
    def empty_bin_count(self) -> int:
        return int((self.bin_counts == 0).sum())


class MultiCamCableStatePipeline:
    """3-cam Stage A→B pipeline for T-Vision-CableState L1.A.2 (Phase 1 narrowed).

    Combines per-camera HSV mask + depth back-projection (existing Stage A.1
    + A.2) with multi-cam voxel fusion (new Stage A.3) and PCA-anchored 40-bin
    arc-length discretization (new Stage B). Stage C (DD-PINN warm start),
    Stage D (Cosserat 7-term loss), and Stage E (confidence) are out of scope
    for Phase 1 — see ``T-Vision-CableState/Impl-Phase-1/state.md`` §7.

    Camera coverage: design memo §4.3 recommends 3-cam (wrist L/R + world-fixed
    overhead). The class accepts any number of cameras via ``camera_keys`` and
    is camera-agnostic — multi-cam is handled by Stage A.3 voxel fusion.

    Backward compatibility: this class does not modify the existing
    :class:`VisionPipelineStage1to3` (single-midpoint) class; both can coexist.

    Args:
        scene: InteractiveScene-like with cameras keyed by ``camera_keys``.
        camera_keys: list of ``(short_name, scene_key)`` tuples. Phase 1 expects
            3 entries (wrist_L, wrist_R, overhead) but accepts any positive
            count for testing / 2-cam fallback (design memo §4.5).
        hsv_params: optional HSV override. Defaults to ``_HSV_PARAMS``.
        voxel_size_m: Stage A.3 voxel edge length. Default 2 mm (design memo
            §2.2.4).
        num_bins: Stage B bin count. Default 40 (mirrors
            ``task_config.CABLE_SEGMENTS=40``).
        var_ratio_min: Stage B PASS threshold on 1st-PCA variance ratio.
            Default 0.6 (design memo §2.3.3); below this triggers fallback in
            Phase 1 (Stage C DD-PINN trigger in Phase 2+).
        min_merged_pts: Stage A.3 minimum merged cloud size. Default 800
            (design memo §2.2.4 fail gate).
    """

    def __init__(
        self,
        scene,
        camera_keys: list[tuple[str, str]],
        hsv_params: dict | None = None,
        voxel_size_m: float = _DEFAULT_VOXEL_SIZE_M,
        num_bins: int = _DEFAULT_NUM_BINS,
        var_ratio_min: float = _DEFAULT_VAR_RATIO_MIN,
        min_merged_pts: int = _DEFAULT_MIN_MERGED_PTS,
    ):
        if not camera_keys:
            raise ValueError("camera_keys must be non-empty")
        self._scene = scene
        self._camera_keys = camera_keys
        self._hsv = hsv_params or _HSV_PARAMS
        self._voxel_size_m = voxel_size_m
        self._num_bins = num_bins
        self._var_ratio_min = var_ratio_min
        self._min_merged_pts = min_merged_pts
        # Phase 1: prev_estimate is reserved for Phase 2 Tier 2 anchor (design
        # memo §3.5). Kept as instance state for future fold-in.
        self._prev_estimate: np.ndarray | None = None
        self._fallback_count = 0
        self._call_count = 0

    def reset(self) -> None:
        """Reset state at episode start."""
        self._prev_estimate = None
        self._fallback_count = 0
        self._call_count = 0

    # ------------------------------------------------------------------
    # Stage A.1+A.2 per-camera (mask + back-project) — reuses existing helpers.
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_mask(rgb: np.ndarray, hsv_params: dict) -> tuple[np.ndarray, int]:
        """HSV cable mask. Returns (mask uint8, mask_pixel_count)."""
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([hsv_params["h_min"], hsv_params["s_min"], hsv_params["v_min"]])
        upper = np.array([hsv_params["h_max"], 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask, int(np.sum(mask > 127))

    # Stage A.2 backprojection delegates to ``VisionPipelineStage1to3._backproject_mask``
    # — called directly from ``estimate()`` to avoid duplicate static helper.

    # ------------------------------------------------------------------
    # Stage B sign-anchor (handedness) — design memo §2.3.2 + §3.5.
    # ------------------------------------------------------------------

    @staticmethod
    def _anchor_sign(
        direction: np.ndarray,
        centroid: np.ndarray,
        finger_positions: np.ndarray | None,
    ) -> np.ndarray:
        """Phase 1 anchor (Tier 1 + Tier 3). Returns the (possibly flipped) direction.

        Tier 1 (grasp finger): if ``finger_positions`` provided, flip ``direction``
        so the projected finger anchor lies at the LOW end (small ``t``) — i.e.,
        bin 0 is at the grasp end. Tier 3 (default): no flip; bin 0 = ``t_min``.
        Tier 2 (prev_estimate) is Phase 2 scope (design memo §3.5).

        Args:
            direction: [3] PCA 1st principal direction (unit).
            centroid: [3] cloud centroid (anchor for projection).
            finger_positions: [n_fingers, 3] world-frame xyz of grasp fingers
                (e.g., 2 for left+right, or n>2 for both arms). May be ``None``.

        Returns:
            [3] direction (sign-flipped if needed).
        """
        d = np.asarray(direction, dtype=np.float64).reshape(3)
        if finger_positions is None or finger_positions.size == 0:
            return d.astype(np.float32)
        fingers = np.asarray(finger_positions, dtype=np.float64).reshape(-1, 3)
        finger_anchor = fingers.mean(axis=0)
        c = np.asarray(centroid, dtype=np.float64).reshape(3)
        # Project finger anchor onto direction relative to centroid; want this
        # to land at the LOW end (so bin 0 = grasp end).
        t_finger = float((finger_anchor - c) @ d)
        if t_finger > 0:
            d = -d
        return d.astype(np.float32)

    # ------------------------------------------------------------------
    # Public estimate API.
    # ------------------------------------------------------------------

    def estimate(
        self,
        dt: float = 0.0,
        finger_positions: np.ndarray | None = None,
    ) -> CableStatePhase1Result:
        """Run Stage A→B end-to-end across all configured cameras.

        Args:
            dt: physics dt for camera update; ``0`` skips the update call.
            finger_positions: optional [n_fingers, 3] world-frame xyz for
                handedness anchor (Tier 1, design memo §3.5). ``None`` falls
                back to Tier 3 (``t_min`` = bin 0).

        Returns:
            :class:`CableStatePhase1Result`. ``succeeded == False`` indicates a
            Stage A or B fallback (see ``fallback_reason``); the caller may
            use prior estimates / Stage C+ in Phase 2+.
        """
        self._call_count += 1
        per_camera: dict = {}
        all_points: list[np.ndarray] = []

        # --- Stage A.1 + A.2 per-camera ---
        for short, cam_key in self._camera_keys:
            try:
                cam = self._scene[cam_key]
                if dt > 0:
                    cam.update(dt)

                rgb_t = cam.data.output.get("rgb")
                if rgb_t is None:
                    per_camera[short] = {"status": "no_rgb", "mask_px": 0, "points": 0}
                    continue
                rgb = rgb_t[0].cpu().numpy()
                if rgb.shape[-1] == 4:
                    rgb = rgb[:, :, :3]
                rgb = rgb.astype(np.uint8)

                dep_t = cam.data.output.get("distance_to_image_plane")
                if dep_t is None:
                    per_camera[short] = {"status": "no_depth", "mask_px": 0, "points": 0}
                    continue
                dep = dep_t[0].cpu().numpy()
                if dep.ndim == 3:
                    dep = dep[:, :, 0]

                mask, mask_px = self._detect_mask(rgb, self._hsv)
                cam_pos = cam.data.pos_w[0].cpu().numpy()
                cam_quat = cam.data.quat_w_ros[0].cpu().numpy()
                K = cam.data.intrinsic_matrices[0].cpu().numpy()
                pts = VisionPipelineStage1to3._backproject_mask(mask, dep, K, cam_pos, cam_quat)

                per_camera[short] = {
                    "status": "ok",
                    "mask_px": mask_px,
                    "points": int(pts.shape[0]),
                }
                if pts.shape[0] > 0:
                    all_points.append(pts)
            except Exception as e:  # noqa: BLE001 — per-camera failures must not halt other cams
                per_camera[short] = {
                    "status": f"error: {e}",
                    "mask_px": 0,
                    "points": 0,
                }

        # --- Stage A.3: voxel fusion ---
        if all_points:
            merged = np.concatenate(all_points, axis=0)
        else:
            merged = np.empty((0, 3), dtype=np.float32)
        merged = voxel_downsample_points(merged, voxel_size_m=self._voxel_size_m)

        if merged.shape[0] < self._min_merged_pts:
            return self._fallback(
                per_camera=per_camera,
                merged=merged,
                reason=f"too_few_merged_points({merged.shape[0]}<{self._min_merged_pts})",
            )

        # --- Stage B.1: PCA principal axis ---
        centroid = merged.mean(axis=0)
        centered = merged - centroid
        _, s, Vt = np.linalg.svd(centered, full_matrices=False)
        direction = Vt[0]
        total_var = float((s**2).sum())
        var_ratio = float((s[0] ** 2) / max(total_var, 1e-12))

        if var_ratio < self._var_ratio_min:
            return self._fallback(
                per_camera=per_camera,
                merged=merged,
                reason=f"low_pca_variance({var_ratio:.3f}<{self._var_ratio_min})",
                var_ratio=var_ratio,
                pca_direction=direction.astype(np.float32),
                pca_centroid=centroid.astype(np.float32),
            )

        # --- Sign anchor (Tier 1 finger / Tier 3 default) ---
        direction = self._anchor_sign(direction, centroid, finger_positions)

        # --- Stage B.2: 40-bin discretize ---
        seg_positions, bin_counts = discretize_arc_length_40bins(merged, direction, centroid, num_bins=self._num_bins)

        return CableStatePhase1Result(
            seg_positions=seg_positions,
            bin_counts=bin_counts,
            var_ratio=var_ratio,
            n_pts_merged=int(merged.shape[0]),
            fallback_reason=None,
            per_camera=per_camera,
            pca_direction=direction.astype(np.float32),
            pca_centroid=centroid.astype(np.float32),
        )

    def _fallback(
        self,
        per_camera: dict,
        merged: np.ndarray,
        reason: str,
        var_ratio: float = 0.0,
        pca_direction: np.ndarray | None = None,
        pca_centroid: np.ndarray | None = None,
    ) -> CableStatePhase1Result:
        """Build a fallback result. Phase 1 returns NaN-filled bins; Phase 2+
        will substitute Stage C DD-PINN warm start on the same trigger.
        """
        self._fallback_count += 1
        seg = np.full((self._num_bins, 3), np.nan, dtype=np.float32)
        counts = np.zeros(self._num_bins, dtype=np.int64)
        return CableStatePhase1Result(
            seg_positions=seg,
            bin_counts=counts,
            var_ratio=var_ratio,
            n_pts_merged=int(merged.shape[0]),
            fallback_reason=reason,
            per_camera=per_camera,
            pca_direction=pca_direction,
            pca_centroid=pca_centroid,
        )

    @property
    def fallback_rate(self) -> float:
        if self._call_count == 0:
            return 0.0
        return self._fallback_count / self._call_count
