# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0A Phase 0 main v2: histogram-fit recalibrated trivial CV baseline.

Improvement over v1 (eval_trivial_cv_baseline_mvp0a.py):
- Pass 1: compute per-class depth + HSV distribution histograms across N sample frames
- Pass 2: derive adaptive thresholds (10/90 percentile bounds per class)
- Pass 3: re-evaluate with adaptive thresholds + cable shape prior (narrow extent perpendicular to gradient)

Usage::

    /home/rlrk/env_isaaclab6/bin/python \
        thread_isaac_lab/scripts/eval_trivial_cv_v2_mvp0a.py \
        --dataset-dir /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset \
        --output-report /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset/phase0_trivial_cv_v2_report.json
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
EVAL_CLASSES = [1, 3, 5]  # cable, gripper, static
MVP0A_GATES = {1: 0.80, 3: 0.65, 5: 0.50}


def rgba_uint32_to_rgb_uint8(rgba_u32: np.ndarray) -> np.ndarray:
    raw_bytes = rgba_u32.view(np.uint8).reshape(*rgba_u32.shape, 4)
    return np.ascontiguousarray(raw_bytes[..., :3])


def derive_class_map(shape_idx: np.ndarray, lut: np.ndarray) -> np.ndarray:
    NO_HIT = np.uint32(0xFFFFFFFF)
    bg_mask = shape_idx == NO_HIT
    safe_idx = np.where(bg_mask, np.uint32(0), shape_idx)
    safe_idx = np.minimum(safe_idx, np.uint32(lut.shape[0] - 1))
    cls = lut[safe_idx]
    cls[bg_mask] = 0
    return cls


def compute_iou(pred_mask, gt_mask):
    pred = pred_mask.astype(bool)
    gt = gt_mask.astype(bool)
    inter = (pred & gt).sum()
    union = (pred | gt).sum()
    return float(inter / union) if union > 0 else 0.0


def fit_depth_histograms(meta, dataset_dir, lut, max_fit_frames=100):
    """Pass 1: collect per-class depth values across sample frames."""
    print(f"[v2 fit] collecting depth distribution from up to {max_fit_frames} frames...")
    per_class_depths = {c: [] for c in EVAL_CLASSES}
    n_collected = 0
    for frame_meta in meta["frames"]:
        if n_collected >= max_fit_frames:
            break
        fid = frame_meta["frame_id"]
        depth = np.load(os.path.join(dataset_dir, "DEPTH", f"{fid}_depth.npz"))["depth"]
        shape_idx = np.load(os.path.join(dataset_dir, "LABELS_ONLY",
                                         f"{fid}_label.npz"))["shape_idx"]
        for w in range(depth.shape[0]):
            for c in range(depth.shape[1]):
                cls_map = derive_class_map(shape_idx[w, c], lut)
                d = depth[w, c]
                for cid in EVAL_CLASSES:
                    mask = cls_map == cid
                    if mask.sum() > 5:
                        # subsample to avoid huge arrays
                        vals = d[mask]
                        if vals.size > 200:
                            vals = vals[np.random.choice(vals.size, 200, replace=False)]
                        per_class_depths[cid].append(vals)
                n_collected += 1
                if n_collected >= max_fit_frames:
                    break
            if n_collected >= max_fit_frames:
                break

    # Aggregate
    fit_summary = {}
    for cid, arrs in per_class_depths.items():
        if not arrs:
            fit_summary[cid] = None
            continue
        all_vals = np.concatenate(arrs)
        fit_summary[cid] = {
            "n_pixels": int(all_vals.size),
            "min": float(np.min(all_vals)),
            "p10": float(np.percentile(all_vals, 10)),
            "p25": float(np.percentile(all_vals, 25)),
            "p50": float(np.percentile(all_vals, 50)),
            "p75": float(np.percentile(all_vals, 75)),
            "p90": float(np.percentile(all_vals, 90)),
            "max": float(np.max(all_vals)),
            "mean": float(np.mean(all_vals)),
            "std": float(np.std(all_vals)),
        }
    return fit_summary


def derive_adaptive_thresholds(fit_summary):
    """Pass 2: derive class-specific depth bounds from histograms."""
    th = {}
    # Cable: use p5-p95 of cable depth (cable has narrow depth range in working area)
    cable = fit_summary.get(1)
    if cable:
        th["cable_depth_min"] = max(cable["p10"] - 0.005, 0.005)
        th["cable_depth_max"] = cable["p90"] + 0.005
    else:
        th["cable_depth_min"] = 0.10
        th["cable_depth_max"] = 0.40

    # Gripper: depth < gripper p90 (gripper is closest)
    grip = fit_summary.get(3)
    if grip:
        th["gripper_depth_max"] = grip["p90"] + 0.005
    else:
        th["gripper_depth_max"] = 0.08

    # Static: depth > static p10 (static is farthest)
    static = fit_summary.get(5)
    if static:
        th["static_depth_min"] = max(static["p10"], 0.10)
    else:
        th["static_depth_min"] = 0.30
    return th


def detect_gripper_v2(depth, th):
    return depth < th["gripper_depth_max"]


def detect_static_v2(depth, th):
    return depth > th["static_depth_min"]


def detect_cable_v2(rgb_uint8, depth, th):
    """Improved cable detector with shape prior.

    Cable shape prior: 9-px diameter (8mm @ 0.86 mm/px). Cable surface produces:
      - Depth in narrow range (cable_depth_min, cable_depth_max)
      - Width perpendicular to gradient ~9 px
      - Local depth gradient strong on edges
    """
    H, W = depth.shape

    # Step 1: depth-in-cable-range
    dr_mask = (depth > th["cable_depth_min"]) & (depth < th["cable_depth_max"])

    # Step 2: depth gradient magnitude
    dz_x = np.zeros_like(depth)
    dz_y = np.zeros_like(depth)
    dz_x[:, 1:-1] = depth[:, 2:] - depth[:, :-2]
    dz_y[1:-1, :] = depth[2:, :] - depth[:-2, :]
    grad_mag = np.sqrt(dz_x ** 2 + dz_y ** 2)
    edge_mask = grad_mag > 0.003  # 3mm gradient over 1 px = relaxed thin-object edge

    # Step 3: morphological close to fill cable interior between edges (~5 px width target)
    from scipy.ndimage import binary_closing, binary_dilation
    edge_dilated = binary_dilation(edge_mask, iterations=2)
    interior = binary_closing(edge_dilated, iterations=3)

    # Step 4: combine
    cable_mask = dr_mask & interior

    # Step 5: cable shape prior — keep only narrow-extent connected components
    from scipy import ndimage
    labeled, n_cc = ndimage.label(cable_mask)
    if n_cc == 0:
        return cable_mask
    keep_mask = np.zeros_like(cable_mask)
    for k in range(1, n_cc + 1):
        cc = labeled == k
        rs, cs = np.where(cc)
        if rs.size < 5:
            continue
        bbox_h = rs.max() - rs.min() + 1
        bbox_w = cs.max() - cs.min() + 1
        # Cable: at least one extent > 12 px (long enough to span camera) AND area density modest
        area = cc.sum()
        long_extent = max(bbox_h, bbox_w)
        narrow_extent = min(bbox_h, bbox_w)
        density = area / (bbox_h * bbox_w)
        if long_extent >= 10 and narrow_extent <= 30 and density >= 0.20:
            keep_mask |= cc
    return keep_mask


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    parser.add_argument("--output-report",
                        default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset/phase0_trivial_cv_v2_report.json")
    parser.add_argument("--max-fit-frames", type=int, default=80)
    parser.add_argument("--max-eval-frames", type=int, default=400)
    args = parser.parse_args()

    metadata_path = os.path.join(args.dataset_dir, "metadata.json")
    with open(metadata_path) as f:
        meta = json.load(f)
    print(f"[v2] Dataset: {meta['saved_frame_count']} frames")
    lut = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY", "shape_class_lut.npz"))["lut"]

    # Pass 1: histogram fit
    fit = fit_depth_histograms(meta, args.dataset_dir, lut, args.max_fit_frames)
    print(f"\n[v2] === Per-class depth histogram (Pass 1) ===")
    for cid in EVAL_CLASSES:
        s = fit[cid]
        if s is None:
            print(f"  {CLASS_LEGEND[cid]:>16}: no samples")
        else:
            print(f"  {CLASS_LEGEND[cid]:>16}: n={s['n_pixels']:>7}, "
                  f"p10={s['p10']:.3f} p50={s['p50']:.3f} p90={s['p90']:.3f} "
                  f"mean={s['mean']:.3f}±{s['std']:.3f}")

    # Pass 2: derive adaptive thresholds
    th = derive_adaptive_thresholds(fit)
    print(f"\n[v2] === Adaptive thresholds (Pass 2) ===")
    for k, v in th.items():
        print(f"  {k} = {v:.4f}")

    # Pass 3: eval
    per_class_iou = {c: [] for c in EVAL_CLASSES}
    n_processed = 0
    t0 = time.perf_counter()
    for frame_meta in meta["frames"]:
        if n_processed >= args.max_eval_frames:
            break
        fid = frame_meta["frame_id"]
        rgb = np.load(os.path.join(args.dataset_dir, "RGB", f"{fid}_rgb.npz"))["color"]
        depth = np.load(os.path.join(args.dataset_dir, "DEPTH", f"{fid}_depth.npz"))["depth"]
        shape_idx = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY",
                                         f"{fid}_label.npz"))["shape_idx"]
        for w in range(rgb.shape[0]):
            for c in range(rgb.shape[1]):
                if n_processed >= args.max_eval_frames:
                    break
                rgb_u8 = rgba_uint32_to_rgb_uint8(rgb[w, c])
                depth_f = depth[w, c]
                cls_map = derive_class_map(shape_idx[w, c], lut)
                cable_pred = detect_cable_v2(rgb_u8, depth_f, th)
                gripper_pred = detect_gripper_v2(depth_f, th)
                static_pred = detect_static_v2(depth_f, th)
                cable_gt = (cls_map == 1)
                gripper_gt = (cls_map == 3)
                static_gt = (cls_map == 5)
                if cable_gt.sum() > 10:
                    per_class_iou[1].append(compute_iou(cable_pred, cable_gt))
                if gripper_gt.sum() > 10:
                    per_class_iou[3].append(compute_iou(gripper_pred, gripper_gt))
                if static_gt.sum() > 10:
                    per_class_iou[5].append(compute_iou(static_pred, static_gt))
                n_processed += 1
    elapsed = time.perf_counter() - t0

    summary = {
        "n_frames_processed": int(n_processed),
        "elapsed_seconds": float(elapsed),
        "method": "trivial_cv_v2_histogram_fit",
        "fit_histogram": fit,
        "adaptive_thresholds": th,
        "per_class_mIoU": {},
        "gate_evaluation": {},
        "class_legend": CLASS_LEGEND,
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

    with open(args.output_report, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[v2] === Phase 0 trivial CV v2 (histogram-fit, {elapsed:.1f}s, {n_processed} frames) ===")
    for c in EVAL_CLASSES:
        s = summary["per_class_mIoU"][str(c)]
        marker = "PASS" if s["PASSED"] else "FAIL"
        print(f"  {s['class_name']:>16} mIoU={s['mean_iou']:.4f} ± {s['std_iou']:.4f} "
              f"(n={s['n_samples']}, gate>{s['gate']:.2f}) [{marker}]")
    print(f"\n[v2] Report: {args.output_report}")
    print(f"\n[v2] Interpretation:")
    print(f"  - V2 uses fitted-from-data depth thresholds + cable shape prior")
    print(f"  - If gripper or static now PASS while cable still <0.3 → cable thin/sparse, NN required")
    print(f"  - If cable >0.5 → SAM-class pretrained likely PASS gate (>0.8 reachable)")


if __name__ == "__main__":
    main()
