# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0A Phase 0 main (trivial CV baseline, network-blocker fallback per Rs Option B).

Computes per-class mIoU on dataset/mvp0a_phase0_dataset using purely classical
detectors (depth gradient for cable, depth threshold for gripper, depth far for
static/table). No NN, no pretrained model, no network dependency.

Purpose: Phase 0 lower-bound Go/No-Go signal. If trivial baseline already gets
cable mIoU > 0.5, NN pretrained should easily exceed gate; if not, full training
clearly required.

Usage::

    /home/rlrk/env_isaaclab6/bin/python \
        thread_isaac_lab/scripts/eval_trivial_cv_baseline_mvp0a.py \
        --dataset-dir /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset \
        --output-report /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset/phase0_trivial_cv_report.json
"""

import argparse
import json
import os
import time

import numpy as np


CLASS_LEGEND = {
    0: "background_no_hit",
    1: "cable",
    2: "clip",
    3: "gripper_finger",
    4: "robot_arm",
    5: "other_static",
}
EVAL_CLASSES = [1, 3, 5]  # cable, gripper, static (skip 2 clip — not in wrist view per LUT verify)
MVP0A_GATES = {
    1: 0.80,  # cable mIoU > 0.8 (per v3 §7.1)
    3: 0.65,  # gripper auxiliary (heavy occlusion stratum target per v3.1 §F.6)
    5: 0.50,  # static/table — sanity reference
}


def rgba_uint32_to_rgb_uint8(rgba_u32: np.ndarray) -> np.ndarray:
    raw_bytes = rgba_u32.view(np.uint8).reshape(*rgba_u32.shape, 4)
    return np.ascontiguousarray(raw_bytes[..., :3])


def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """RGB uint8 → HSV float32 [0,1]^3。 Vectorized."""
    r = rgb[..., 0].astype(np.float32) / 255.0
    g = rgb[..., 1].astype(np.float32) / 255.0
    b = rgb[..., 2].astype(np.float32) / 255.0
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    diff = cmax - cmin
    h = np.zeros_like(cmax)
    mask = diff > 1e-6
    rmax = (cmax == r) & mask
    gmax = (cmax == g) & mask
    bmax = (cmax == b) & mask
    h[rmax] = (60 * ((g[rmax] - b[rmax]) / diff[rmax]) + 360) % 360
    h[gmax] = 60 * ((b[gmax] - r[gmax]) / diff[gmax]) + 120
    h[bmax] = 60 * ((r[bmax] - g[bmax]) / diff[bmax]) + 240
    h /= 360
    s = np.where(cmax > 0, diff / cmax, 0)
    v = cmax
    return np.stack([h, s, v], axis=-1)


def derive_class_map(shape_idx: np.ndarray, lut: np.ndarray) -> np.ndarray:
    NO_HIT = np.uint32(0xFFFFFFFF)
    bg_mask = shape_idx == NO_HIT
    safe_idx = np.where(bg_mask, np.uint32(0), shape_idx)
    safe_idx = np.minimum(safe_idx, np.uint32(lut.shape[0] - 1))
    cls = lut[safe_idx]
    cls[bg_mask] = 0
    return cls


def detect_gripper(depth: np.ndarray) -> np.ndarray:
    """Gripper = near-camera pixels (depth < 0.08 m from wrist).

    Wrist camera is at link7 + 5cm-10cm offset; finger TIP is at 17cm in target frame.
    Anything within 8cm of camera is finger/gripper material.
    """
    return depth < 0.08


def detect_static(depth: np.ndarray) -> np.ndarray:
    """Table/static = far pixels (depth > 0.5 m or so)."""
    return depth > 0.5


def detect_cable(rgb_uint8: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """Cable = thin object with depth gradient + low-saturation color in mid-depth range.

    Heuristic:
      - depth in [0.1, 0.4] m (cable in wrist view typical depth)
      - high local depth gradient (cable edges)
      - low saturation (cable is grayish, not vivid color)
    """
    H, W = depth.shape
    depth_in_range = (depth > 0.10) & (depth < 0.40)

    # depth gradient via Sobel-like approximation
    dz_x = np.zeros_like(depth)
    dz_y = np.zeros_like(depth)
    dz_x[:, 1:-1] = depth[:, 2:] - depth[:, :-2]
    dz_y[1:-1, :] = depth[2:, :] - depth[:-2, :]
    grad_mag = np.sqrt(dz_x ** 2 + dz_y ** 2)
    high_grad = grad_mag > 0.005  # 5mm gradient over 1px = thin object edge

    # HSV
    hsv = rgb_to_hsv(rgb_uint8)
    low_sat = hsv[..., 1] < 0.30  # cable is gray-ish

    # combine with morphological dilation: cable surface = high-grad neighborhood
    from scipy.ndimage import binary_dilation
    edge_dilated = binary_dilation(high_grad, iterations=2)
    cable_mask = depth_in_range & edge_dilated & low_sat
    return cable_mask


def compute_iou(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    pred = pred_mask.astype(bool)
    gt = gt_mask.astype(bool)
    inter = (pred & gt).sum()
    union = (pred | gt).sum()
    return float(inter / union) if union > 0 else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    parser.add_argument("--output-report",
                        default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset/phase0_trivial_cv_report.json")
    parser.add_argument("--max-frames", type=int, default=400,
                        help="Max world-camera frames to evaluate")
    args = parser.parse_args()

    metadata_path = os.path.join(args.dataset_dir, "metadata.json")
    with open(metadata_path) as f:
        meta = json.load(f)
    print(f"[trivial_cv] Dataset: {meta['saved_frame_count']} frames "
          f"({len(meta['frames'])} npz triplets)")
    lut = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY", "shape_class_lut.npz"))["lut"]

    per_class_iou = {c: [] for c in EVAL_CLASSES}
    n_processed = 0
    t0 = time.perf_counter()

    for frame_meta in meta["frames"]:
        if n_processed >= args.max_frames:
            break
        fid = frame_meta["frame_id"]
        rgb = np.load(os.path.join(args.dataset_dir, "RGB", f"{fid}_rgb.npz"))["color"]
        depth = np.load(os.path.join(args.dataset_dir, "DEPTH", f"{fid}_depth.npz"))["depth"]
        shape_idx = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY",
                                         f"{fid}_label.npz"))["shape_idx"]
        W, C, H, Wp = rgb.shape
        for w in range(W):
            for c in range(C):
                if n_processed >= args.max_frames:
                    break
                rgb_u8 = rgba_uint32_to_rgb_uint8(rgb[w, c])
                depth_f = depth[w, c]
                cls_map = derive_class_map(shape_idx[w, c], lut)

                # Detectors
                cable_pred = detect_cable(rgb_u8, depth_f)
                gripper_pred = detect_gripper(depth_f)
                static_pred = detect_static(depth_f)

                # GT masks
                cable_gt = (cls_map == 1)
                gripper_gt = (cls_map == 3)
                static_gt = (cls_map == 5)

                # IoU per class — only count if GT class exists in this frame
                if cable_gt.sum() > 10:
                    per_class_iou[1].append(compute_iou(cable_pred, cable_gt))
                if gripper_gt.sum() > 10:
                    per_class_iou[3].append(compute_iou(gripper_pred, gripper_gt))
                if static_gt.sum() > 10:
                    per_class_iou[5].append(compute_iou(static_pred, static_gt))
                n_processed += 1
                if n_processed % 100 == 0:
                    print(f"[trivial_cv] processed {n_processed} frames "
                          f"(elapsed {time.perf_counter() - t0:.1f}s)")

    elapsed = time.perf_counter() - t0
    summary = {
        "n_frames_processed": int(n_processed),
        "elapsed_seconds": float(elapsed),
        "per_class_mIoU": {},
        "gate_evaluation": {},
        "class_legend": CLASS_LEGEND,
        "method": "trivial_cv_lower_bound",
        "detectors": {
            "cable": "depth in [0.10, 0.40] m AND high-depth-gradient (>5mm/px, dilated) AND HSV-saturation < 0.30",
            "gripper": "depth < 0.08 m (near-camera proximal)",
            "static_table": "depth > 0.50 m",
        },
    }
    for c in EVAL_CLASSES:
        ious = per_class_iou[c]
        if ious:
            mean_iou = float(np.mean(ious))
            std_iou = float(np.std(ious))
            n = len(ious)
        else:
            mean_iou, std_iou, n = 0.0, 0.0, 0
        gate = MVP0A_GATES[c]
        passed = mean_iou > gate
        summary["per_class_mIoU"][str(c)] = {
            "class_name": CLASS_LEGEND[c],
            "mean_iou": mean_iou,
            "std_iou": std_iou,
            "n_samples": n,
            "gate": gate,
            "PASSED": passed,
        }
        summary["gate_evaluation"][CLASS_LEGEND[c]] = "PASS" if passed else "FAIL"

    os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
    with open(args.output_report, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[trivial_cv] === Phase 0 trivial CV baseline ({elapsed:.1f}s, {n_processed} frames) ===")
    for c in EVAL_CLASSES:
        s = summary["per_class_mIoU"][str(c)]
        marker = "PASS" if s["PASSED"] else "FAIL"
        print(f"  {s['class_name']:>16} mIoU={s['mean_iou']:.4f} ± {s['std_iou']:.4f} "
              f"(n={s['n_samples']}, gate>{s['gate']:.2f}) [{marker}]")
    print(f"\n[trivial_cv] Report: {args.output_report}")
    print(f"\n[trivial_cv] Interpretation:")
    print(f"  - Trivial CV is LOWER BOUND. Pretrained NN should exceed by 10-30 pp.")
    print(f"  - If cable trivial > 0.5 → pretrained likely PASS (gate 0.8 reachable)")
    print(f"  - If cable trivial < 0.3 → from-scratch NN training required for MVP-0A")


if __name__ == "__main__":
    main()
