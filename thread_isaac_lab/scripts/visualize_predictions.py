#!/usr/bin/env python3
"""Visualize World Model predictions vs ground truth."""

import argparse
import os
import sys
import glob
import torch
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thread_isaac_lab.scripts.train_4cam_wm import (
    FourCameraWorldModel,
    FourCameraWorldModelConfig,
    FourCameraHDF5Dataset,
)


def visualize_predictions(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Device] {device}")

    # Setup camera names
    camera_names = args.cameras
    print(f"[Cameras] {camera_names}")

    # Create config
    config = FourCameraWorldModelConfig()
    config.camera_names = camera_names
    config.num_cameras = len(camera_names)

    # Load dataset
    data_files = sorted(glob.glob(os.path.join(args.data_path, "*.h5")))
    if not data_files:
        print(f"[Error] No h5 files found in {args.data_path}")
        return

    print(f"[Data] Loading from {len(data_files)} files...")
    dataset = FourCameraHDF5Dataset(data_files, camera_names=camera_names)

    # Update config from dataset
    if hasattr(dataset, 'proprio_dim'):
        config.proprio_dim = dataset.proprio_dim
    if hasattr(dataset, 'task_state_dim'):
        config.task_state_dim = dataset.task_state_dim

    # Create model
    model = FourCameraWorldModel(config, encoder_type=args.encoder_type).to(device)

    # Load checkpoint
    print(f"[Load] {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)

    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint

    # Filter out missing keys
    model_dict = model.state_dict()
    filtered_dict = {k: v for k, v in state_dict.items() if k in model_dict and v.shape == model_dict[k].shape}
    model.load_state_dict(filtered_dict, strict=False)
    model.eval()

    print(f"[Model] Loaded {len(filtered_dict)}/{len(model_dict)} parameters")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample random indices
    np.random.seed(args.seed)
    indices = np.random.choice(len(dataset), size=args.num_samples, replace=False)

    print(f"[Visualize] Generating {args.num_samples} samples...")

    for i, idx in enumerate(indices):
        sample = dataset[idx]

        # Prepare inputs
        images = {cam: sample[f"{cam}_img"].unsqueeze(0).to(device) for cam in camera_names}
        proprio = sample["proprio"].unsqueeze(0).to(device)
        task_state = sample.get("task_state")
        if task_state is not None:
            task_state = task_state.unsqueeze(0).to(device)
        action = sample["action"].unsqueeze(0).to(device)

        # Ground truth next images
        gt_next_images = {cam: sample[f"next_{cam}_img"].numpy() for cam in camera_names}

        # Forward pass
        with torch.no_grad():
            outputs = model(images, proprio, task_state, action, decode_images=True)

        pred_images = outputs.get('pred_images', {})

        if not pred_images:
            print(f"  [Warning] No predicted images for sample {i}")
            continue

        # Create comparison figure
        num_cameras = len(camera_names)
        fig, axes = plt.subplots(2, num_cameras, figsize=(4 * num_cameras, 8))

        for j, cam in enumerate(camera_names):
            # Ground truth
            gt_img = gt_next_images[cam].transpose(1, 2, 0)  # CHW -> HWC
            gt_img = np.clip(gt_img, 0, 1)

            if num_cameras == 1:
                ax_gt = axes[0]
                ax_pred = axes[1]
            else:
                ax_gt = axes[0, j]
                ax_pred = axes[1, j]

            ax_gt.imshow(gt_img)
            ax_gt.set_title(f"{cam} (GT)")
            ax_gt.axis('off')

            # Prediction
            if cam in pred_images:
                pred_img = pred_images[cam][0].cpu().numpy().transpose(1, 2, 0)
                pred_img = np.clip(pred_img, 0, 1)

                # Compute PSNR
                mse = np.mean((gt_img - pred_img) ** 2)
                psnr = 10 * np.log10(1.0 / (mse + 1e-10))

                ax_pred.imshow(pred_img)
                ax_pred.set_title(f"{cam} (Pred) PSNR={psnr:.1f}dB")
            else:
                ax_pred.text(0.5, 0.5, "No prediction", ha='center', va='center')
                ax_pred.set_title(f"{cam} (Pred)")
            ax_pred.axis('off')

        plt.suptitle(f"Sample {idx} - Ground Truth (top) vs Prediction (bottom)")
        plt.tight_layout()

        save_path = output_dir / f"prediction_{i:03d}_idx{idx}.png"
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  [{i+1}/{args.num_samples}] Saved: {save_path}")

    # Compute overall metrics on more samples
    print(f"\n[Metrics] Computing on {args.metric_samples} samples...")

    metric_indices = np.random.choice(len(dataset), size=args.metric_samples, replace=False)
    all_psnr = {cam: [] for cam in camera_names}
    all_mse = {cam: [] for cam in camera_names}

    for idx in metric_indices:
        sample = dataset[idx]

        images = {cam: sample[f"{cam}_img"].unsqueeze(0).to(device) for cam in camera_names}
        proprio = sample["proprio"].unsqueeze(0).to(device)
        task_state = sample.get("task_state")
        if task_state is not None:
            task_state = task_state.unsqueeze(0).to(device)
        action = sample["action"].unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(images, proprio, task_state, action, decode_images=True)

        pred_images = outputs.get('pred_images', {})

        for cam in camera_names:
            if cam in pred_images:
                gt = sample[f"next_{cam}_img"].numpy()
                pred = pred_images[cam][0].cpu().numpy()

                mse = np.mean((gt - pred) ** 2)
                psnr = 10 * np.log10(1.0 / (mse + 1e-10))

                all_mse[cam].append(mse)
                all_psnr[cam].append(psnr)

    print("\n" + "=" * 60)
    print("Image Reconstruction Metrics")
    print("=" * 60)

    total_psnr = []
    for cam in camera_names:
        if all_psnr[cam]:
            avg_psnr = np.mean(all_psnr[cam])
            avg_mse = np.mean(all_mse[cam])
            total_psnr.extend(all_psnr[cam])
            print(f"  {cam}: PSNR={avg_psnr:.2f} dB, MSE={avg_mse:.6f}")

    if total_psnr:
        print(f"\n  Overall: PSNR={np.mean(total_psnr):.2f} dB")

    print("=" * 60)
    print(f"\n[Done] Images saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--cameras", type=str, nargs='+',
                        default=['front_left', 'front_right', 'back'])
    parser.add_argument("--encoder_type", type=str, default="hybrid")
    parser.add_argument("--output_dir", type=str, default="visualization_output")
    parser.add_argument("--num_samples", type=int, default=10)
    parser.add_argument("--metric_samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    visualize_predictions(args)
