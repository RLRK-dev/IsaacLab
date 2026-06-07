# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0A Phase 0 main eval: pretrained MobileSAM zero-shot baseline.

Loads dataset from `data/mvp0a_phase0_dataset/` and runs MobileSAM with bbox
prompts derived from per-frame GT class masks. Computes per-class mIoU
on AC env wrist L+R RGB-D as cheap Go/No-Go signal vs MVP-0A gates
(cable mIoU > 0.8, clip > 0.75, ROI recall > 0.95).

Scope: PROPOSE v2 Phase 0 main per Rs Option A.

Usage::

    CUDA_VISIBLE_DEVICES=1 /home/rlrk/env_isaaclab6/bin/python \
        thread_isaac_lab/scripts/eval_pretrained_seg_mvp0a.py \
        --dataset-dir /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset \
        --mobile-sam-path /tmp/MobileSAM \
        --weights-path /tmp/mobile_sam.pt \
        --device cuda:0 \
        --output-report /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset/phase0_eval_report.json
"""

import argparse
import json
import os
import sys
import time
import urllib.request

import numpy as np
import torch


CLASS_LEGEND = {
    0: "background",
    1: "cable",
    2: "clip",
    3: "gripper_finger",
    4: "robot_arm",
    5: "other_static",
}
EVAL_CLASSES = [1, 2, 3]  # cable, clip, gripper — relevant to MVP-0A gate
MVP0A_GATES = {
    1: 0.80,  # cable mIoU > 0.8
    2: 0.75,  # clip > 0.75
    3: 0.65,  # gripper auxiliary heavy-occlusion stratum
}


def rgba_uint32_to_rgb_uint8(rgba_u32: np.ndarray) -> np.ndarray:
    """Decode (W,H) uint32 RGBA → (H,W,3) uint8 RGB."""
    raw_bytes = rgba_u32.view(np.uint8).reshape(*rgba_u32.shape, 4)
    rgb = raw_bytes[..., :3]
    return np.ascontiguousarray(rgb)


def derive_class_map(shape_idx: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """shape_idx (uint32) → class_id (uint8)."""
    NO_HIT = np.uint32(0xFFFFFFFF)
    bg_mask = shape_idx == NO_HIT
    safe_idx = np.where(bg_mask, np.uint32(0), shape_idx)
    safe_idx = np.minimum(safe_idx, np.uint32(lut.shape[0] - 1))
    cls = lut[safe_idx]
    cls[bg_mask] = 0
    return cls


def get_class_bboxes(class_map: np.ndarray, class_id: int):
    """Return list of (x0, y0, x1, y1) bboxes for connected components of class_id."""
    from scipy import ndimage
    mask = class_map == class_id
    if not mask.any():
        return []
    labeled, n = ndimage.label(mask)
    bboxes = []
    for k in range(1, n + 1):
        rs, cs = np.where(labeled == k)
        if len(rs) < 5:  # skip tiny components
            continue
        bboxes.append((int(cs.min()), int(rs.min()), int(cs.max()), int(rs.max())))
    return bboxes


def compute_iou(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    pred = pred_mask.astype(bool)
    gt = gt_mask.astype(bool)
    inter = (pred & gt).sum()
    union = (pred | gt).sum()
    return float(inter / union) if union > 0 else 0.0


def maybe_download_mobilesam_weights(weights_path: str):
    if os.path.exists(weights_path):
        return
    url = "https://github.com/ChaoningZhang/MobileSAM/raw/master/weights/mobile_sam.pt"
    print(f"[eval_pretrained] Downloading MobileSAM weights → {weights_path}")
    urllib.request.urlretrieve(url, weights_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    parser.add_argument("--mobile-sam-path", default="/tmp/MobileSAM",
                        help="Path to MobileSAM repo (git clone)")
    parser.add_argument("--weights-path", default="/tmp/mobile_sam.pt")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--output-report",
                        default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset/phase0_eval_report.json")
    parser.add_argument("--max-frames", type=int, default=200,
                        help="Max world-camera frames to evaluate")
    args = parser.parse_args()

    # Add MobileSAM to sys.path
    if not os.path.isdir(args.mobile_sam_path):
        raise SystemExit(f"MobileSAM repo not found: {args.mobile_sam_path}. "
                         "git clone https://github.com/ChaoningZhang/MobileSAM.git first.")
    sys.path.insert(0, args.mobile_sam_path)

    maybe_download_mobilesam_weights(args.weights_path)

    from mobile_sam import sam_model_registry, SamPredictor
    print(f"[eval_pretrained] Loading MobileSAM (device={args.device})")
    sam = sam_model_registry["vit_t"](checkpoint=args.weights_path)
    sam.to(args.device).eval()
    predictor = SamPredictor(sam)

    # Load dataset metadata
    metadata_path = os.path.join(args.dataset_dir, "metadata.json")
    with open(metadata_path) as f:
        meta = json.load(f)
    print(f"[eval_pretrained] Dataset: {meta['saved_frame_count']} frames "
          f"({len(meta['frames'])} npz triplets)")

    # Load LUT
    lut = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY", "shape_class_lut.npz"))["lut"]
    print(f"[eval_pretrained] LUT loaded: shape={lut.shape}")

    # Eval loop
    per_class_iou = {c: [] for c in EVAL_CLASSES}
    per_frame_log = []
    n_processed = 0

    t0 = time.perf_counter()
    for frame_meta in meta["frames"]:
        if n_processed >= args.max_frames:
            break
        fid = frame_meta["frame_id"]
        rgb = np.load(os.path.join(args.dataset_dir, "RGB", f"{fid}_rgb.npz"))["color"]
        shape_idx = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY",
                                         f"{fid}_label.npz"))["shape_idx"]

        W, C, H, Wp = rgb.shape
        for w in range(W):
            for c in range(C):
                if n_processed >= args.max_frames:
                    break
                rgb_uint8 = rgba_uint32_to_rgb_uint8(rgb[w, c])  # (H, W, 3) uint8
                cls_map = derive_class_map(shape_idx[w, c], lut)  # (H, W) uint8

                predictor.set_image(rgb_uint8)

                for class_id in EVAL_CLASSES:
                    bboxes = get_class_bboxes(cls_map, class_id)
                    if not bboxes:
                        continue  # class not in this frame

                    # Combine all bboxes of this class into single multi-bbox prompt
                    pred_mask_full = np.zeros((H, Wp), dtype=bool)
                    for bbox in bboxes:
                        # MobileSAM SamPredictor expects [x1, y1, x2, y2]
                        masks, scores, _ = predictor.predict(
                            box=np.array([bbox], dtype=np.float32),
                            multimask_output=False,
                        )
                        if masks.shape[0] > 0:
                            pred_mask_full |= masks[0].astype(bool)

                    gt_mask = (cls_map == class_id)
                    iou = compute_iou(pred_mask_full, gt_mask)
                    per_class_iou[class_id].append(iou)

                per_frame_log.append({
                    "frame_id": fid, "world": int(w), "camera": int(c),
                    "iou_per_class": {str(c): float(per_class_iou[c][-1])
                                       if per_class_iou[c] else None
                                       for c in EVAL_CLASSES},
                })
                n_processed += 1
                if n_processed % 50 == 0:
                    print(f"[eval_pretrained] processed {n_processed} frames "
                          f"(elapsed {time.perf_counter() - t0:.1f}s)")

    elapsed = time.perf_counter() - t0
    # Aggregate
    summary = {
        "n_frames_processed": int(n_processed),
        "elapsed_seconds": float(elapsed),
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

    print(f"\n[eval_pretrained] === Phase 0 main result ({elapsed:.1f}s, {n_processed} frames) ===")
    for c in EVAL_CLASSES:
        s = summary["per_class_mIoU"][str(c)]
        marker = "PASS" if s["PASSED"] else "FAIL"
        print(f"  {s['class_name']:>14} mIoU={s['mean_iou']:.4f} ± {s['std_iou']:.4f} "
              f"(n={s['n_samples']}, gate>{s['gate']:.2f}) [{marker}]")
    print(f"\n[eval_pretrained] Report: {args.output_report}")


if __name__ == "__main__":
    main()
