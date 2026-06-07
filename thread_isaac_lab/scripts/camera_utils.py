"""camera_utils.py

Camera-based 3D object detection utilities for Isaac Lab scenes.

Provides red-ball detection via RGB color segmentation, depth back-projection,
and multi-camera fusion.  Designed for use with Isaac Lab's CameraCfg sensors
(ROS coordinate convention).

No Isaac Sim / AppLauncher side-effects -- safe to import from any script.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# 2D red ball detection (RGB color segmentation)
# ---------------------------------------------------------------------------

def detect_red_ball_2d(
    rgb: np.ndarray, min_pixels: int = 10
) -> Optional[tuple[float, float, int]]:
    """Detect red ball centroid in an RGB image.

    Simple colour mask: R > 180  AND  R - G > 80  AND  R - B > 80.
    Returns (u, v, pixel_count) where u = column, v = row,
    or None if fewer than *min_pixels* red pixels are found.
    """
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    mask = (r > 180) & (r - g > 80) & (r - b > 80)
    count = int(mask.sum())
    if count < min_pixels:
        return None
    ys, xs = np.nonzero(mask)
    u = float(np.mean(xs))
    v = float(np.mean(ys))
    return (u, v, count)


# ---------------------------------------------------------------------------
# Quaternion / geometry helpers
# ---------------------------------------------------------------------------

def _quat_to_rotation_matrix(q_wxyz: np.ndarray) -> np.ndarray:
    """Convert quaternion (w, x, y, z) to 3x3 rotation matrix."""
    w, x, y, z = q_wxyz
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)


# ---------------------------------------------------------------------------
# Pixel -> world back-projection
# ---------------------------------------------------------------------------

def pixel_to_world(
    u: float,
    v: float,
    depth: float,
    intrinsic_matrix: np.ndarray,
    cam_pos_w: np.ndarray,
    cam_quat_w_ros: np.ndarray,
) -> np.ndarray:
    """Back-project a single pixel (u, v, depth) to world coordinates.

    Isaac Lab cameras use ROS convention for the local frame:
      X-right, Y-down, Z-forward (into the scene).
    The depth from ``distance_to_image_plane`` is orthogonal (plane-depth).

    Args:
        u, v: Pixel coordinates (u = column, v = row).
        depth: Depth in metres at that pixel (distance_to_image_plane).
        intrinsic_matrix: 3x3 camera K matrix (fx, fy, cx, cy).
        cam_pos_w: (3,) camera position in world frame.
        cam_quat_w_ros: (4,) quaternion (w,x,y,z) mapping ROS camera -> world.

    Returns:
        (3,) world-frame position of the 3-D point.
    """
    fx = intrinsic_matrix[0, 0]
    fy = intrinsic_matrix[1, 1]
    cx = intrinsic_matrix[0, 2]
    cy = intrinsic_matrix[1, 2]
    # Camera-frame 3-D point (ROS: X-right, Y-down, Z-forward)
    x_cam = (u - cx) * depth / fx
    y_cam = (v - cy) * depth / fy
    z_cam = depth
    p_cam = np.array([x_cam, y_cam, z_cam], dtype=np.float64)
    R = _quat_to_rotation_matrix(cam_quat_w_ros)
    p_world = R @ p_cam + cam_pos_w.astype(np.float64)
    return p_world.astype(np.float32)


# ---------------------------------------------------------------------------
# Multi-camera 3D estimation
# ---------------------------------------------------------------------------

_BALL_RADIUS = 0.03  # metres

# Camera scene keys used for 3D estimation
_ESTIMATION_CAMS = [
    ("overhead", "overhead_camera"),
    ("front_center", "front_center_camera"),
    ("front_left", "front_left_camera"),
    ("front_right", "front_right_camera"),
]


def estimate_target_from_cameras(
    scene,
    sim,
    ground_truth: Optional[np.ndarray] = None,
) -> Optional[np.ndarray]:
    """Estimate red ball 3-D position from overhead + front_center + front_left + front_right.

    For each camera:
      1. RGB -> red-ball 2-D centroid (u, v).
      2. Depth map -> median of 5x5 patch around (u, v).
      3. Intrinsics + extrinsics -> world-frame 3-D point.

    Returns the per-axis median of successful estimates (>= 2 cameras),
    or None if fewer than 2 cameras detect the ball.
    """
    estimates: list[np.ndarray] = []

    for short, cam_name in _ESTIMATION_CAMS:
        try:
            cam = scene[cam_name]
            cam.update(sim.get_physics_dt())

            # --- RGB: detect red ball ---
            rgb_t = cam.data.output["rgb"][0]
            rgb = rgb_t.cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            rgb = rgb.astype(np.uint8)
            det = detect_red_ball_2d(rgb)
            if det is None:
                print(f"[CAM3D] {short}: no red ball detected")
                continue
            u, v, px_count = det

            # --- Depth at (u, v): 5x5 median for noise robustness ---
            depth_t = cam.data.output.get("distance_to_image_plane", None)
            if depth_t is None:
                print(f"[CAM3D] {short}: no depth data")
                continue
            depth_arr = depth_t[0].cpu().numpy()
            if depth_arr.ndim == 3 and depth_arr.shape[-1] == 1:
                depth_arr = depth_arr[:, :, 0]
            h, w = depth_arr.shape
            iv, iu = int(round(v)), int(round(u))
            iv = max(2, min(iv, h - 3))
            iu = max(2, min(iu, w - 3))
            patch = depth_arr[iv - 2: iv + 3, iu - 2: iu + 3]
            valid = patch[np.isfinite(patch) & (patch > 0.0)]
            if valid.size == 0:
                print(f"[CAM3D] {short}: depth invalid at ({iu},{iv})")
                continue
            d = float(np.median(valid))

            # --- Intrinsics ---
            K = cam.data.intrinsic_matrices[0].cpu().numpy()

            # --- Extrinsics: ROS-convention quaternion ---
            cam_pos = cam.data.pos_w[0].cpu().numpy()
            cam_quat = cam.data.quat_w_ros[0].cpu().numpy()

            # --- Back-project ---
            p_world = pixel_to_world(u, v, d, K, cam_pos, cam_quat)
            # Correct for ball surface -> center: depth measures the surface,
            # not the sphere center.  Push the estimate away from camera
            # by the ball radius along the viewing ray.
            ray = p_world - cam_pos.astype(np.float32)
            ray_len = float(np.linalg.norm(ray))
            if ray_len > 1e-6:
                p_world = p_world + _BALL_RADIUS * (ray / ray_len)
            estimates.append(p_world)
            cam_err_str = ""
            if ground_truth is not None:
                cam_err = float(np.linalg.norm(p_world - ground_truth))
                cam_err_str = (
                    f" err_vs_gt={cam_err:.4f}m({cam_err * 100:.1f}cm)"
                )
            print(
                f"[CAM3D] {short}: uv=({u:.1f},{v:.1f}) depth={d:.3f}m "
                f"px={px_count} -> world=({p_world[0]:.4f}, {p_world[1]:.4f}, {p_world[2]:.4f})"
                f"{cam_err_str}"
            )
        except Exception as exc:
            print(f"[CAM3D] {short}: error: {exc}")
            continue

    n_total = len(_ESTIMATION_CAMS)
    if len(estimates) < 2:
        print(
            f"[CAM3D] FAIL: only {len(estimates)} camera(s) detected "
            f"the ball (need >=2)"
        )
        return None
    stacked = np.stack(estimates, axis=0)
    result = np.median(stacked, axis=0).astype(np.float32)
    spread = float(np.max(np.linalg.norm(stacked - result, axis=1)))
    gt_str = ""
    if ground_truth is not None:
        fuse_err = float(np.linalg.norm(result - ground_truth))
        gt_str = (
            f" gt=({ground_truth[0]:.4f},{ground_truth[1]:.4f},"
            f"{ground_truth[2]:.4f}) "
            f"fuse_err={fuse_err:.4f}m({fuse_err * 100:.1f}cm)"
        )
    print(
        f"[CAM3D] estimate=({result[0]:.4f}, {result[1]:.4f}, {result[2]:.4f}) "
        f"from {len(estimates)}/{n_total} cameras, max_spread={spread:.4f}m{gt_str}"
    )
    return result
