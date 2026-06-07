#!/usr/bin/env python3
"""Evaluate trained World Model prediction accuracy.

Evaluation metrics:
1. Autoencoder reconstruction quality (MSE, SSIM)
2. Dynamics prediction accuracy (MAE, RMSE for proprio and task_state)
3. Multi-step prediction (1, 5, 10 steps ahead)

Usage:
    cd /home/rlrk/IsaacLab
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/evaluate_world_model.py \
        --model_path checkpoints/world_model_4cam/phase2_best.pt \
        --data_path data/demo_data_v1 \
        --eval_cycles 8,9
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import h5py
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.world_model_4cam import (
    WorldModel4CamConfig,
    WorldModel4Cam,
    FourCameraAutoencoder,
)


def decompress_jpeg_image(jpeg_bytes) -> np.ndarray:
    """Decompress JPEG bytes to numpy array."""
    if isinstance(jpeg_bytes, np.ndarray):
        jpeg_bytes = jpeg_bytes.tobytes()
    buffer = io.BytesIO(jpeg_bytes)
    img = Image.open(buffer)
    return np.array(img)


def compute_ssim(img1: torch.Tensor, img2: torch.Tensor, window_size: int = 11) -> float:
    """Compute Structural Similarity Index (SSIM) between two images.

    Args:
        img1, img2: Images of shape [B, C, H, W] in range [0, 1]
    """
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2

    # Create Gaussian window
    def gaussian_window(size, sigma=1.5):
        coords = torch.arange(size, dtype=torch.float32) - size // 2
        g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
        g = g / g.sum()
        return g.view(1, 1, -1, 1) * g.view(1, 1, 1, -1)

    window = gaussian_window(window_size).to(img1.device)
    window = window.expand(img1.shape[1], 1, window_size, window_size)

    mu1 = F.conv2d(img1, window, padding=window_size//2, groups=img1.shape[1])
    mu2 = F.conv2d(img2, window, padding=window_size//2, groups=img2.shape[1])

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size//2, groups=img1.shape[1]) - mu1_sq
    sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size//2, groups=img2.shape[1]) - mu2_sq
    sigma12 = F.conv2d(img1 * img2, window, padding=window_size//2, groups=img1.shape[1]) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))

    return ssim_map.mean().item()


class EvalDataset(torch.utils.data.Dataset):
    """Dataset for evaluation with specific cycle selection."""

    def __init__(self, data_dir: str, eval_cycles: List[int], img_size: int = 256):
        self.img_size = img_size
        self.data_paths = []

        # Find files for specified cycles
        for cycle_idx in eval_cycles:
            path = os.path.join(data_dir, f"demo_cycle_{cycle_idx:04d}.h5")
            if os.path.exists(path):
                self.data_paths.append(path)
            else:
                print(f"[WARNING] Cycle {cycle_idx} not found: {path}")

        if not self.data_paths:
            raise ValueError(f"No valid data files found for cycles {eval_cycles}")

        print(f"[EvalDataset] Loading {len(self.data_paths)} files for evaluation")

        # Build index and load small data
        self.index_map = []
        self.proprio_per_file = []
        self.task_state_per_file = []
        self.action_per_file = []

        for file_idx, path in enumerate(self.data_paths):
            print(f"  Loading {path}...")
            with h5py.File(path, "r") as f:
                num_samples = len(f["proprio"])

                # Use consecutive pairs (exclude last sample)
                for local_idx in range(num_samples - 1):
                    self.index_map.append((file_idx, local_idx))

                proprio = f["proprio"][:]
                task_state = f["task_state"][:]
                action = f["action"][:]

                # Handle NaN
                proprio = np.nan_to_num(proprio, nan=0.0)
                task_state = np.nan_to_num(task_state, nan=0.0)
                action = np.nan_to_num(action, nan=0.0)

                self.proprio_per_file.append(proprio)
                self.task_state_per_file.append(task_state)
                self.action_per_file.append(action)

        self._file_handles = {}
        print(f"[EvalDataset] Total samples: {len(self.index_map)}")

    def _get_file_handle(self, file_idx: int):
        if file_idx not in self._file_handles:
            self._file_handles[file_idx] = h5py.File(self.data_paths[file_idx], "r")
        return self._file_handles[file_idx]

    def __len__(self):
        return len(self.index_map)

    def _process_img(self, img):
        h, w = img.shape[:2]
        if h != self.img_size or w != self.img_size:
            pil_img = Image.fromarray(img)
            pil_img = pil_img.resize((self.img_size, self.img_size), Image.BILINEAR)
            img = np.array(pil_img)
        return torch.from_numpy(img.copy()).permute(2, 0, 1).float() / 255.0

    def __getitem__(self, idx):
        file_idx, local_idx = self.index_map[idx]
        f = self._get_file_handle(file_idx)

        # Current frame
        front_left = decompress_jpeg_image(f["front_left_img"][local_idx])
        front_right = decompress_jpeg_image(f["front_right_img"][local_idx])
        back = decompress_jpeg_image(f["back_img"][local_idx])
        overhead = decompress_jpeg_image(f["overhead_img"][local_idx])

        proprio = self.proprio_per_file[file_idx][local_idx]
        task_state = self.task_state_per_file[file_idx][local_idx]
        action = self.action_per_file[file_idx][local_idx]

        # Next frame
        next_idx = local_idx + 1
        next_front_left = decompress_jpeg_image(f["front_left_img"][next_idx])
        next_front_right = decompress_jpeg_image(f["front_right_img"][next_idx])
        next_back = decompress_jpeg_image(f["back_img"][next_idx])
        next_overhead = decompress_jpeg_image(f["overhead_img"][next_idx])

        next_proprio = self.proprio_per_file[file_idx][next_idx]
        next_task_state = self.task_state_per_file[file_idx][next_idx]

        return {
            "front_left_img": self._process_img(front_left),
            "front_right_img": self._process_img(front_right),
            "back_img": self._process_img(back),
            "overhead_img": self._process_img(overhead),
            "proprio": torch.from_numpy(proprio.copy()).float(),
            "task_state": torch.from_numpy(task_state.copy()).float(),
            "action": torch.from_numpy(action.copy()).float(),
            "next_front_left_img": self._process_img(next_front_left),
            "next_front_right_img": self._process_img(next_front_right),
            "next_back_img": self._process_img(next_back),
            "next_overhead_img": self._process_img(next_overhead),
            "next_proprio": torch.from_numpy(next_proprio.copy()).float(),
            "next_task_state": torch.from_numpy(next_task_state.copy()).float(),
        }

    def __del__(self):
        for f in self._file_handles.values():
            try:
                f.close()
            except:
                pass


def evaluate_autoencoder(model: FourCameraAutoencoder, dataloader: DataLoader, device: torch.device) -> Dict:
    """Evaluate autoencoder reconstruction quality."""
    print("\n" + "=" * 60)
    print("AUTOENCODER RECONSTRUCTION EVALUATION")
    print("=" * 60)

    model.eval()

    mse_per_camera = {"front_left": [], "front_right": [], "back": [], "overhead": []}
    ssim_per_camera = {"front_left": [], "front_right": [], "back": [], "overhead": []}

    with torch.no_grad():
        for batch in dataloader:
            front_left = batch["front_left_img"].to(device)
            front_right = batch["front_right_img"].to(device)
            back = batch["back_img"].to(device)
            overhead = batch["overhead_img"].to(device)

            output = model(front_left, front_right, back, overhead)

            # MSE per camera
            mse_per_camera["front_left"].append(F.mse_loss(output["front_left_recon"], front_left).item())
            mse_per_camera["front_right"].append(F.mse_loss(output["front_right_recon"], front_right).item())
            mse_per_camera["back"].append(F.mse_loss(output["back_recon"], back).item())
            mse_per_camera["overhead"].append(F.mse_loss(output["overhead_recon"], overhead).item())

            # SSIM per camera
            ssim_per_camera["front_left"].append(compute_ssim(output["front_left_recon"], front_left))
            ssim_per_camera["front_right"].append(compute_ssim(output["front_right_recon"], front_right))
            ssim_per_camera["back"].append(compute_ssim(output["back_recon"], back))
            ssim_per_camera["overhead"].append(compute_ssim(output["overhead_recon"], overhead))

    results = {}
    print("\nReconstruction Quality:")
    print("-" * 50)
    print(f"{'Camera':<15} {'MSE':<12} {'SSIM':<12}")
    print("-" * 50)

    for cam in ["front_left", "front_right", "back", "overhead"]:
        mse = np.mean(mse_per_camera[cam])
        ssim = np.mean(ssim_per_camera[cam])
        results[f"{cam}_mse"] = float(mse)
        results[f"{cam}_ssim"] = float(ssim)
        print(f"{cam:<15} {mse:<12.6f} {ssim:<12.4f}")

    avg_mse = np.mean([results[f"{cam}_mse"] for cam in ["front_left", "front_right", "back", "overhead"]])
    avg_ssim = np.mean([results[f"{cam}_ssim"] for cam in ["front_left", "front_right", "back", "overhead"]])
    results["avg_mse"] = float(avg_mse)
    results["avg_ssim"] = float(avg_ssim)

    print("-" * 50)
    print(f"{'Average':<15} {avg_mse:<12.6f} {avg_ssim:<12.4f}")

    return results


def evaluate_dynamics(model: WorldModel4Cam, dataloader: DataLoader, device: torch.device) -> Dict:
    """Evaluate dynamics prediction accuracy."""
    print("\n" + "=" * 60)
    print("DYNAMICS PREDICTION EVALUATION")
    print("=" * 60)

    model.eval()

    proprio_errors = []
    task_state_errors = []

    proprio_per_dim = []
    task_per_dim = []

    with torch.no_grad():
        for batch in dataloader:
            front_left = batch["front_left_img"].to(device)
            front_right = batch["front_right_img"].to(device)
            back = batch["back_img"].to(device)
            overhead = batch["overhead_img"].to(device)
            proprio = batch["proprio"].to(device)
            task_state = batch["task_state"].to(device)
            action = batch["action"].to(device)

            next_proprio = batch["next_proprio"].to(device)
            next_task_state = batch["next_task_state"].to(device)

            output = model(front_left, front_right, back, overhead, proprio, task_state, action)

            # Per-sample errors
            proprio_err = (output["pred_proprio"] - next_proprio).abs()
            task_err = (output["pred_task_state"] - next_task_state).abs()

            proprio_errors.append(proprio_err.cpu().numpy())
            task_state_errors.append(task_err.cpu().numpy())

            # Per-dimension tracking
            proprio_per_dim.append(proprio_err.mean(dim=0).cpu().numpy())
            task_per_dim.append(task_err.mean(dim=0).cpu().numpy())

    proprio_errors = np.concatenate(proprio_errors, axis=0)
    task_state_errors = np.concatenate(task_state_errors, axis=0)

    # Compute statistics
    proprio_mae = proprio_errors.mean()
    proprio_rmse = np.sqrt((proprio_errors ** 2).mean())
    task_mae = task_state_errors.mean()
    task_rmse = np.sqrt((task_state_errors ** 2).mean())

    # Per-dimension analysis
    proprio_per_dim = np.stack(proprio_per_dim).mean(axis=0)
    task_per_dim = np.stack(task_per_dim).mean(axis=0)

    results = {
        "proprio_mae": float(proprio_mae),
        "proprio_rmse": float(proprio_rmse),
        "task_state_mae": float(task_mae),
        "task_state_rmse": float(task_rmse),
    }

    print("\nPrediction Accuracy:")
    print("-" * 50)
    print(f"{'Metric':<20} {'MAE':<12} {'RMSE':<12}")
    print("-" * 50)
    print(f"{'Proprio (34D)':<20} {proprio_mae:<12.6f} {proprio_rmse:<12.6f}")
    print(f"{'Task State (44D)':<20} {task_mae:<12.6f} {task_rmse:<12.6f}")

    # Proprio breakdown (joint pos 0-6, joint vel 7-13, EE pos 14-16 for each arm)
    print("\nProprio Breakdown (per arm):")
    print("-" * 50)

    # Left arm
    left_joint_pos = proprio_per_dim[0:7].mean()
    left_joint_vel = proprio_per_dim[7:14].mean()
    left_ee_pos = proprio_per_dim[14:17].mean()

    # Right arm
    right_joint_pos = proprio_per_dim[17:24].mean()
    right_joint_vel = proprio_per_dim[24:31].mean()
    right_ee_pos = proprio_per_dim[31:34].mean()

    print(f"  Left Joint Pos (7D):  {left_joint_pos:.6f}")
    print(f"  Left Joint Vel (7D):  {left_joint_vel:.6f}")
    print(f"  Left EE Pos (3D):     {left_ee_pos:.6f}")
    print(f"  Right Joint Pos (7D): {right_joint_pos:.6f}")
    print(f"  Right Joint Vel (7D): {right_joint_vel:.6f}")
    print(f"  Right EE Pos (3D):    {right_ee_pos:.6f}")

    results["left_joint_pos_mae"] = float(left_joint_pos)
    results["left_joint_vel_mae"] = float(left_joint_vel)
    results["left_ee_pos_mae"] = float(left_ee_pos)
    results["right_joint_pos_mae"] = float(right_joint_pos)
    results["right_joint_vel_mae"] = float(right_joint_vel)
    results["right_ee_pos_mae"] = float(right_ee_pos)

    # Task state breakdown (cable segments 0-29, hook 30-32, left EE 33-35, right EE 36-38, distances 39-43)
    print("\nTask State Breakdown:")
    print("-" * 50)

    cable_segments = task_per_dim[0:30].mean()
    hook_pos = task_per_dim[30:33].mean()
    left_ee = task_per_dim[33:36].mean()
    right_ee = task_per_dim[36:39].mean()
    distances = task_per_dim[39:44].mean()

    print(f"  Cable Segments (30D): {cable_segments:.6f}")
    print(f"  Hook Position (3D):   {hook_pos:.6f}")
    print(f"  Left EE (3D):         {left_ee:.6f}")
    print(f"  Right EE (3D):        {right_ee:.6f}")
    print(f"  Distances (5D):       {distances:.6f}")

    results["cable_segments_mae"] = float(cable_segments)
    results["hook_pos_mae"] = float(hook_pos)
    results["task_left_ee_mae"] = float(left_ee)
    results["task_right_ee_mae"] = float(right_ee)
    results["distances_mae"] = float(distances)

    return results


def evaluate_multistep(model: WorldModel4Cam, dataloader: DataLoader, device: torch.device,
                       steps: List[int] = [1, 5, 10]) -> Dict:
    """Evaluate multi-step prediction accuracy."""
    print("\n" + "=" * 60)
    print("MULTI-STEP PREDICTION EVALUATION")
    print("=" * 60)

    model.eval()

    # Collect all data for multi-step evaluation
    all_data = []
    for batch in dataloader:
        batch_size = batch["proprio"].shape[0]
        for i in range(batch_size):
            all_data.append({
                "front_left_img": batch["front_left_img"][i:i+1],
                "front_right_img": batch["front_right_img"][i:i+1],
                "back_img": batch["back_img"][i:i+1],
                "overhead_img": batch["overhead_img"][i:i+1],
                "proprio": batch["proprio"][i:i+1],
                "task_state": batch["task_state"][i:i+1],
                "action": batch["action"][i:i+1],
                "next_proprio": batch["next_proprio"][i:i+1],
                "next_task_state": batch["next_task_state"][i:i+1],
            })

    results = {}
    print(f"\nEvaluating {len(all_data)} samples for multi-step prediction")
    print("-" * 50)
    print(f"{'Steps':<10} {'Proprio MAE':<15} {'Task MAE':<15}")
    print("-" * 50)

    for n_steps in steps:
        proprio_errors = []
        task_errors = []

        # We need sequences of at least n_steps
        max_start = len(all_data) - n_steps
        if max_start <= 0:
            print(f"  {n_steps:<10} Not enough data")
            continue

        with torch.no_grad():
            for start_idx in range(0, max_start, n_steps):  # Non-overlapping sequences
                # Get initial state
                data = all_data[start_idx]

                front_left = data["front_left_img"].to(device)
                front_right = data["front_right_img"].to(device)
                back = data["back_img"].to(device)
                overhead = data["overhead_img"].to(device)
                proprio = data["proprio"].to(device)
                task_state = data["task_state"].to(device)

                # Roll out predictions
                for step in range(n_steps):
                    if start_idx + step >= len(all_data):
                        break

                    action = all_data[start_idx + step]["action"].to(device)

                    output = model(front_left, front_right, back, overhead, proprio, task_state, action)

                    # Update state for next step (use predicted values)
                    proprio = output["pred_proprio"]
                    task_state = output["pred_task_state"]

                # Compare final prediction with ground truth
                if start_idx + n_steps < len(all_data):
                    gt_proprio = all_data[start_idx + n_steps]["proprio"].to(device)
                    gt_task = all_data[start_idx + n_steps]["task_state"].to(device)

                    proprio_err = (proprio - gt_proprio).abs().mean().item()
                    task_err = (task_state - gt_task).abs().mean().item()

                    proprio_errors.append(proprio_err)
                    task_errors.append(task_err)

        if proprio_errors:
            avg_proprio = np.mean(proprio_errors)
            avg_task = np.mean(task_errors)
            results[f"{n_steps}step_proprio_mae"] = float(avg_proprio)
            results[f"{n_steps}step_task_mae"] = float(avg_task)
            print(f"  {n_steps:<10} {avg_proprio:<15.6f} {avg_task:<15.6f}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate World Model")
    parser.add_argument("--model_path", type=str, required=True,
                       help="Path to trained World Model checkpoint")
    parser.add_argument("--ae_path", type=str, default=None,
                       help="Path to autoencoder checkpoint (optional)")
    parser.add_argument("--data_path", type=str, default="data/demo_data_v1",
                       help="Path to data directory")
    parser.add_argument("--eval_cycles", type=str, default="8,9",
                       help="Comma-separated list of cycle indices for evaluation")
    parser.add_argument("--output_dir", type=str, default="data/eval_results",
                       help="Output directory for results")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--multistep", action="store_true",
                       help="Enable multi-step prediction evaluation")
    args = parser.parse_args()

    # Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Device] {device}")

    os.makedirs(args.output_dir, exist_ok=True)

    # Parse eval cycles
    eval_cycles = [int(x.strip()) for x in args.eval_cycles.split(",")]
    print(f"[Eval Cycles] {eval_cycles}")

    # Load dataset
    dataset = EvalDataset(args.data_path, eval_cycles)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=2)

    # Load World Model
    print(f"\n[Model] Loading {args.model_path}")
    checkpoint = torch.load(args.model_path, map_location=device, weights_only=False)

    config = checkpoint.get("config", WorldModel4CamConfig())
    model = WorldModel4Cam(config).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    print(f"[Model] Loaded from epoch {checkpoint.get('epoch', 'unknown')}")
    print(f"[Model] Training loss: {checkpoint.get('loss', 'unknown')}")

    all_results = {
        "model_path": args.model_path,
        "eval_cycles": eval_cycles,
        "num_samples": len(dataset),
    }

    # Evaluate dynamics
    dynamics_results = evaluate_dynamics(model, dataloader, device)
    all_results["dynamics"] = dynamics_results

    # Evaluate autoencoder if path provided
    if args.ae_path and os.path.exists(args.ae_path):
        print(f"\n[Autoencoder] Loading {args.ae_path}")
        ae_checkpoint = torch.load(args.ae_path, map_location=device, weights_only=False)
        ae_model = FourCameraAutoencoder(config).to(device)
        ae_model.load_state_dict(ae_checkpoint["model_state_dict"])
        ae_model.eval()

        ae_results = evaluate_autoencoder(ae_model, dataloader, device)
        all_results["autoencoder"] = ae_results

    # Multi-step evaluation
    if args.multistep:
        multistep_results = evaluate_multistep(model, dataloader, device)
        all_results["multistep"] = multistep_results

    # Save results
    output_path = os.path.join(args.output_dir, "wm_evaluation.json")
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[Results] Saved to {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Eval Samples: {len(dataset)}")
    print(f"  Proprio MAE:  {dynamics_results['proprio_mae']:.6f}")
    print(f"  Proprio RMSE: {dynamics_results['proprio_rmse']:.6f}")
    print(f"  Task MAE:     {dynamics_results['task_state_mae']:.6f}")
    print(f"  Task RMSE:    {dynamics_results['task_state_rmse']:.6f}")

    if "autoencoder" in all_results:
        print(f"  AE Avg MSE:   {all_results['autoencoder']['avg_mse']:.6f}")
        print(f"  AE Avg SSIM:  {all_results['autoencoder']['avg_ssim']:.4f}")


if __name__ == "__main__":
    main()
