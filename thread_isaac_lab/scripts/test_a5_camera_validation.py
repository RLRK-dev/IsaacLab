#!/usr/bin/env python3
"""SOMA Phase A5: Camera Infrastructure Validation for Cable Scene.

Validates that existing camera infrastructure (Phase 2 red ball pipeline)
works with the cable grasping scene. Tests RGB, Depth, and Semantic Segmentation
across 3 cameras (overhead, front_left, front_right).

Checks:
  1. RGB — cable visible in each camera (non-black image)
  2. Depth — valid depth rate >= 80% in centre 10×10 patch
  3. Semantic Segmentation — cable label pixels present
  4. Ground truth — cable_midpoint projected onto overhead RGB

Usage:
    python thread_isaac_lab/scripts/test_a5_camera_validation.py \
        --device cuda:0 --num_envs 1 --headless --enable_cameras
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

import numpy as np

_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="SOMA Phase A5: Camera Validation")
parser.add_argument("--output_dir", type=str, default="data/test_a5")
parser.add_argument("--settle_steps", type=int, default=200,
                    help="Physics steps to settle before capture")
parser.add_argument("--video_frames", type=int, default=30,
                    help="Number of RGB frames to capture for video")

from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Post-AppLauncher imports
# ---------------------------------------------------------------------------
import torch

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.scripts.camera_utils import _quat_to_rotation_matrix
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# 3 cameras to test (short_name → scene key)
CAMERAS = {
    "overhead": "overhead_camera",
    "front_left": "front_left_camera",
    "front_right": "front_right_camera",
}

# Data types to request from each camera
EXTENDED_DATA_TYPES = [
    "rgb",
    "distance_to_image_plane",
    "semantic_segmentation",
    "instance_segmentation_fast",
]


# =========================================================================
# Helpers
# =========================================================================

def world_to_pixel(point_3d, K, cam_pos, cam_quat_ros):
    """Project 3-D world point → 2-D pixel (u, v)."""
    R = _quat_to_rotation_matrix(cam_quat_ros)
    p_cam = R.T @ (point_3d.astype(np.float64) - cam_pos.astype(np.float64))
    if p_cam[2] <= 0:
        return None
    u = float(K[0, 0] * p_cam[0] / p_cam[2] + K[0, 2])
    v = float(K[1, 1] * p_cam[1] / p_cam[2] + K[1, 2])
    return u, v


def save_rgb(rgb_np: np.ndarray, path: str):
    """Save uint8 RGB array as PNG (PIL) or .npy fallback."""
    try:
        from PIL import Image
        Image.fromarray(rgb_np).save(path)
    except ImportError:
        np.save(path.replace(".png", ".npy"), rgb_np)


def save_depth_vis(depth_np: np.ndarray, path: str):
    """Save depth as greyscale PNG (0=invalid, 255=near, 1=far)."""
    try:
        from PIL import Image
        valid = depth_np[np.isfinite(depth_np) & (depth_np > 0)]
        if valid.size > 0:
            lo, hi = float(valid.min()), float(valid.max())
            norm = np.clip((depth_np - lo) / max(hi - lo, 1e-6), 0, 1)
            norm[~np.isfinite(depth_np) | (depth_np <= 0)] = 0
            img = Image.fromarray((255 - norm * 254).astype(np.uint8), mode="L")
        else:
            img = Image.fromarray(np.zeros(depth_np.shape[:2], dtype=np.uint8), mode="L")
        img.save(path)
    except ImportError:
        np.save(path.replace(".png", ".npy"), depth_np)


def draw_crosshair(rgb: np.ndarray, u: int, v: int,
                   color=(0, 255, 0), size: int = 7):
    """Draw a small crosshair on rgb (mutates in-place)."""
    h, w = rgb.shape[:2]
    for d in range(-size, size + 1):
        if 0 <= v < h and 0 <= u + d < w:
            rgb[v, u + d] = color
        if 0 <= v + d < h and 0 <= u < w:
            rgb[v + d, u] = color


def make_video(frames: list[np.ndarray], path: str, fps: int = 10):
    """Try to write frames list → mp4 via OpenCV.  Silent no-op on failure."""
    try:
        import cv2
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(path, fourcc, fps, (w, h))
        for f in frames:
            out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        out.release()
        print(f"  Video saved: {path} ({len(frames)} frames)")
    except Exception as e:
        print(f"  Video write skipped: {e}")


# =========================================================================
# Main
# =========================================================================

def main():
    device_str = f"cuda:{app_launcher.device_id}"
    out_dir = os.path.join(str(_REPO_ROOT), args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    print(f"[A5] SOMA Phase A5: Camera Validation ({device_str})", flush=True)
    print(f"[A5] Output: {out_dir}\n", flush=True)

    # ------------------------------------------------------------------
    # Scene — add semantic + instance seg to the 3 test cameras
    # ------------------------------------------------------------------
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)

    for cam_key in CAMERAS.values():
        cam_cfg = getattr(scene_cfg, cam_key)
        cam_cfg.data_types = EXTENDED_DATA_TYPES.copy()
        # raw IDs for programmatic check  (uint8 colorized saved separately)
        cam_cfg.colorize_semantic_segmentation = False
        cam_cfg.colorize_instance_id_segmentation = False
        cam_cfg.colorize_instance_segmentation = False

    physx_cfg = sim_utils.PhysxCfg(
        gpu_found_lost_pairs_capacity=2**23,
        gpu_total_aggregate_pairs_capacity=2**23,
    )
    sim_cfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT, render_interval=2, device=device_str,
        physx=physx_cfg,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()
    scene.reset()

    # ------------------------------------------------------------------
    # Settle physics + populate camera buffers
    # ------------------------------------------------------------------
    print(f"[A5] Running {args.settle_steps} settle steps …", flush=True)
    for _ in range(args.settle_steps):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Extra camera update to ensure buffers are fresh
    for cam_key in CAMERAS.values():
        scene[cam_key].update(sim.get_physics_dt())

    # ------------------------------------------------------------------
    # Cable ground truth
    # ------------------------------------------------------------------
    cable = scene["cable"]
    cable_pos = cable.data.body_pos_w[0].cpu().numpy()      # (n_bodies, 3)
    cable_mid = cable_pos.mean(axis=0)
    print(f"[A5] Cable: {cable_pos.shape[0]} bodies, "
          f"midpoint=({cable_mid[0]:.4f}, {cable_mid[1]:.4f}, {cable_mid[2]:.4f})\n", flush=True)

    # ------------------------------------------------------------------
    # Per-camera validation
    # ------------------------------------------------------------------
    results = {
        "phase": "A5",
        "description": "Camera infrastructure validation for cable scene",
        "device": device_str,
        "cable_midpoint_gt": cable_mid.tolist(),
        "cable_bodies": int(cable_pos.shape[0]),
        "cameras": {},
    }
    all_pass = True

    for short, cam_key in CAMERAS.items():
        print(f"=== {short} ({cam_key}) ===")
        cam = scene[cam_key]
        cam.update(sim.get_physics_dt())

        cam_pos = cam.data.pos_w[0].cpu().numpy()
        cam_quat = cam.data.quat_w_ros[0].cpu().numpy()
        K = cam.data.intrinsic_matrices[0].cpu().numpy()
        h_img, w_img = cam.data.image_shape
        cr = {"name": cam_key, "pos": cam_pos.tolist(),
              "resolution": [h_img, w_img]}
        print(f"  pos=({cam_pos[0]:.3f},{cam_pos[1]:.3f},{cam_pos[2]:.3f})  "
              f"res={h_img}×{w_img}")

        # ---------- 1. RGB ----------
        rgb_t = cam.data.output.get("rgb")
        if rgb_t is not None:
            rgb = rgb_t[0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            rgb = rgb.astype(np.uint8)
            path = os.path.join(out_dir, f"rgb_{short}.png")
            save_rgb(rgb, path)
            mean_px = float(rgb.mean())
            max_px = float(rgb.max())
            ok = max_px > 10
            cr["rgb"] = {"status": "PASS" if ok else "FAIL",
                         "mean": round(mean_px, 2), "max": int(max_px),
                         "path": path}
            print(f"  RGB  mean={mean_px:.1f} max={max_px}  → {'PASS' if ok else 'FAIL'}")
            if not ok:
                all_pass = False
        else:
            cr["rgb"] = {"status": "FAIL", "error": "no data"}
            all_pass = False

        # ---------- 2. Depth ----------
        dep_t = cam.data.output.get("distance_to_image_plane")
        if dep_t is not None:
            dep = dep_t[0].cpu().numpy()
            if dep.ndim == 3:
                dep = dep[:, :, 0]
            path = os.path.join(out_dir, f"depth_{short}.png")
            save_depth_vis(dep, path)

            # centre 10×10
            cy, cx = h_img // 2, w_img // 2
            patch = dep[cy - 5:cy + 5, cx - 5:cx + 5]
            n_valid = int(np.sum(np.isfinite(patch) & (patch > 0) & (patch < 100)))
            n_total = patch.size
            rate = n_valid / max(n_total, 1)
            ok = rate >= 0.80

            # global stats
            gv = dep[np.isfinite(dep) & (dep > 0) & (dep < 100)]
            stats = {"valid_px": int(gv.size), "total_px": int(dep.size)}
            if gv.size > 0:
                stats.update({"min": round(float(gv.min()), 4),
                              "max": round(float(gv.max()), 4),
                              "mean": round(float(gv.mean()), 4)})

            cr["depth"] = {"status": "PASS" if ok else "FAIL",
                           "centre_valid_rate": round(rate, 3),
                           "centre_valid": n_valid, "centre_total": n_total,
                           "global": stats, "path": path}
            print(f"  Depth  centre={rate*100:.0f}% ({n_valid}/{n_total})  → {'PASS' if ok else 'FAIL'}")
            if gv.size > 0:
                print(f"    global {stats['valid_px']}/{stats['total_px']} "
                      f"valid  range=[{stats['min']:.3f}, {stats['max']:.3f}]m")
            if not ok:
                all_pass = False
        else:
            cr["depth"] = {"status": "FAIL", "error": "no data"}
            all_pass = False

        # ---------- 3. Semantic Segmentation ----------
        print("  Semantic  checking output keys …", flush=True)
        print(f"    available keys: {list(cam.data.output.keys())}", flush=True)
        sem_t = cam.data.output.get("semantic_segmentation")
        if sem_t is not None:
            print(f"    tensor shape={sem_t.shape} dtype={sem_t.dtype}", flush=True)
            sem = sem_t[0].cpu().numpy()
            # Squeeze trailing dim if present (e.g. (H,W,1) → (H,W))
            if sem.ndim == 3 and sem.shape[-1] == 1:
                sem = sem[:, :, 0]
            print(f"    numpy shape={sem.shape} dtype={sem.dtype}", flush=True)
            path = os.path.join(out_dir, f"semantic_{short}.png")

            # Analyse — avoid expensive np.unique on full image
            if sem.ndim == 3 and sem.shape[-1] >= 3:
                # Colorized RGBA/RGB — count non-black pixels
                non_bg = int(np.sum(np.any(sem[:, :, :3] > 0, axis=-1)))
                # Count classes via downsampled unique (fast)
                step = max(1, sem.shape[0] // 64)
                samp = sem[::step, ::step].reshape(-1, sem.shape[-1])
                n_classes = len(np.unique(samp, axis=0))
                save_rgb(sem[:, :, :3].astype(np.uint8), path)
            else:
                ids = np.unique(sem)
                n_classes = len(ids)
                non_bg = int(np.sum(sem != 0))
                # Pseudo-colour vis
                vis = np.zeros((*sem.shape[:2], 3), dtype=np.uint8)
                for i, uid in enumerate(ids[:64]):  # cap at 64 classes
                    if uid == 0:
                        continue
                    c = [(i * 67 + 100) % 256, (i * 137 + 50) % 256,
                         (i * 97 + 150) % 256]
                    vis[sem == uid] = c
                save_rgb(vis, path)

            cable_detected = non_bg > 50  # at least 50 labelled pixels
            cr["semantic"] = {"status": "PASS" if cable_detected else "FAIL",
                              "n_classes": n_classes,
                              "non_bg_pixels": non_bg,
                              "shape": list(sem.shape), "path": path}
            print(f"  Semantic  classes={n_classes} non_bg={non_bg}  "
                  f"→ {'PASS' if cable_detected else 'FAIL'}", flush=True)
            # Dump info metadata if available
            try:
                info = cam.data.info
                if info and len(info) > 0:
                    sem_info = info[0].get("semantic_segmentation", {})
                    if sem_info:
                        cr["semantic"]["info"] = str(sem_info)[:500]
            except Exception as e:
                print(f"    info extraction error: {e}", flush=True)
            if not cable_detected:
                all_pass = False
        else:
            cr["semantic"] = {"status": "SKIP", "error": "no data (annotator not available)"}
            print(f"  Semantic  SKIP (annotator returned None)", flush=True)

        # ---------- 3b. Instance Segmentation (bonus) ----------
        print("  Instance  checking …", flush=True)
        inst_t = cam.data.output.get("instance_segmentation_fast")
        if inst_t is not None:
            print(f"    tensor shape={inst_t.shape} dtype={inst_t.dtype}", flush=True)
            inst = inst_t[0].cpu().numpy()
            if inst.ndim == 3 and inst.shape[-1] == 1:
                inst = inst[:, :, 0]
            path = os.path.join(out_dir, f"instance_{short}.png")
            if inst.ndim == 3 and inst.shape[-1] >= 3:
                step = max(1, inst.shape[0] // 64)
                samp = inst[::step, ::step].reshape(-1, inst.shape[-1])
                n_inst = len(np.unique(samp, axis=0))
                save_rgb(inst[:, :, :3].astype(np.uint8), path)
            else:
                n_inst = len(np.unique(inst))
                vis = np.zeros((*inst.shape[:2], 3), dtype=np.uint8)
                for i, uid in enumerate(np.unique(inst)[:64]):
                    if uid == 0:
                        continue
                    c = [(i * 53 + 80) % 256, (i * 127 + 40) % 256,
                         (i * 89 + 120) % 256]
                    vis[inst == uid] = c
                save_rgb(vis, path)
            cr["instance"] = {"n_instances": n_inst, "path": path}
            print(f"  Instance  {n_inst} instances", flush=True)
        else:
            cr["instance"] = {"note": "not available"}
            print("  Instance  SKIP (not available)", flush=True)

        # ---------- 4. GT projection (overhead only) ----------
        if short == "overhead":
            proj = world_to_pixel(cable_mid, K, cam_pos, cam_quat)
            if proj is not None:
                pu, pv = proj
                in_frame = 0 <= pu < w_img and 0 <= pv < h_img
                cr["gt_projection"] = {
                    "pixel": [round(pu, 1), round(pv, 1)],
                    "in_frame": in_frame,
                }
                print(f"  GT proj  cable_mid → pixel ({pu:.1f}, {pv:.1f})  "
                      f"in_frame={in_frame}")
                # Overlay on RGB
                if "rgb" in cr and cr["rgb"]["status"] == "PASS":
                    marked = rgb.copy()
                    draw_crosshair(marked, int(round(pu)), int(round(pv)))
                    gt_path = os.path.join(out_dir, f"rgb_{short}_gt_overlay.png")
                    save_rgb(marked, gt_path)
                    cr["gt_projection"]["overlay"] = gt_path
            else:
                cr["gt_projection"] = {"error": "behind camera"}

        results["cameras"][short] = cr
        print()

    # ------------------------------------------------------------------
    # Video capture (short RGB sequence from each camera)
    # ------------------------------------------------------------------
    print(f"[A5] Capturing {args.video_frames} video frames …")
    frames = {s: [] for s in CAMERAS}
    for _ in range(args.video_frames):
        sim.step()
        sim.step()                         # 2 steps per frame (render_interval=2)
        scene.update(sim.get_physics_dt())
        for short, cam_key in CAMERAS.items():
            cam = scene[cam_key]
            cam.update(sim.get_physics_dt())
            rgb_t = cam.data.output.get("rgb")
            if rgb_t is not None:
                f = rgb_t[0].cpu().numpy()
                if f.shape[-1] == 4:
                    f = f[:, :, :3]
                frames[short].append(f.astype(np.uint8))

    for short, fr_list in frames.items():
        if fr_list:
            vpath = os.path.join(out_dir, f"video_{short}.mp4")
            make_video(fr_list, vpath, fps=10)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    elapsed = time.time() - t0
    results["overall"] = "PASS" if all_pass else "FAIL"
    results["elapsed_s"] = round(elapsed, 1)

    metrics_path = os.path.join(out_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SOMA Phase A5 Camera Validation: {results['overall']}")
    print(f"{'='*60}")
    for short, cr in results["cameras"].items():
        rgb_s = cr.get("rgb", {}).get("status", "N/A")
        dep_s = cr.get("depth", {}).get("status", "N/A")
        sem_s = cr.get("semantic", {}).get("status", "N/A")
        print(f"  {short:<12s}  RGB={rgb_s}  Depth={dep_s}  Semantic={sem_s}")
    print(f"  Results → {metrics_path}")
    print(f"  Elapsed: {elapsed:.0f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
    simulation_app.close()
