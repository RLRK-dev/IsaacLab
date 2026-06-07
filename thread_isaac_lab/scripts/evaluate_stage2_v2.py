#!/usr/bin/env python3
"""
Stage 2 v2 Model Evaluation Script
Evaluates prediction quality, multi-step rollout, and state prediction accuracy
"""

import torch
import numpy as np
import os
import sys
import io
import h5py
import glob
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.world_model_with_task import WorldModelWithTask, WorldModelWithTaskConfig


def decompress_jpeg_image(jpeg_bytes) -> np.ndarray:
    """Decompress JPEG bytes to numpy array."""
    img = Image.open(io.BytesIO(bytes(jpeg_bytes)))
    return np.array(img)


class FiveCameraHDF5Dataset(torch.utils.data.Dataset):
    """Dataset for 5-camera HDF5 data with 44D task_state."""

    def __init__(self, data_path: str):
        # Get all HDF5 files
        if os.path.isdir(data_path):
            self.data_paths = sorted(glob.glob(os.path.join(data_path, "*.h5")))
        else:
            self.data_paths = [data_path]

        print(f"[Dataset] Found {len(self.data_paths)} files")

        # Build index mapping
        self.index_map = []
        all_proprio = []
        all_task_state = []
        all_action = []
        all_reward = []
        all_next_proprio = []
        all_next_task_state = []

        for file_idx, path in enumerate(self.data_paths):
            print(f"  Loading {os.path.basename(path)}...")
            with h5py.File(path, "r") as f:
                num_samples = len(f["front_img_jpeg"])

                for local_idx in range(num_samples):
                    self.index_map.append((file_idx, local_idx))

                all_proprio.append(f["proprio"][:])
                all_action.append(f["action"][:])
                all_reward.append(f["reward"][:])
                all_next_proprio.append(f["next_proprio"][:])

                if "task_state" in f:
                    all_task_state.append(f["task_state"][:])
                    all_next_task_state.append(f["next_task_state"][:])
                else:
                    all_task_state.append(np.zeros((num_samples, 44), dtype=np.float32))
                    all_next_task_state.append(np.zeros((num_samples, 44), dtype=np.float32))

        self.proprio = np.concatenate(all_proprio, axis=0)
        self.task_state = np.concatenate(all_task_state, axis=0)
        self.action = np.concatenate(all_action, axis=0)
        self.reward = np.concatenate(all_reward, axis=0)
        self.next_proprio = np.concatenate(all_next_proprio, axis=0)
        self.next_task_state = np.concatenate(all_next_task_state, axis=0)

        self._file_handles = {}

        print(f"[Dataset] Total samples: {len(self.index_map)}")

    def _get_file(self, file_idx):
        if file_idx not in self._file_handles:
            self._file_handles[file_idx] = h5py.File(self.data_paths[file_idx], "r")
        return self._file_handles[file_idx]

    def __len__(self):
        return len(self.index_map)

    def __getitem__(self, idx):
        file_idx, local_idx = self.index_map[idx]
        f = self._get_file(file_idx)

        def process_img(jpeg_data, size=256):
            img = decompress_jpeg_image(jpeg_data)
            if img.shape[0] != size or img.shape[1] != size:
                img = np.array(Image.fromarray(img).resize((size, size), Image.BILINEAR))
            return torch.from_numpy(img.copy()).permute(2, 0, 1).float() / 255.0

        return {
            "front_img": process_img(f["front_img_jpeg"][local_idx]),
            "left_img": process_img(f["left_img_jpeg"][local_idx]),
            "right_img": process_img(f["right_img_jpeg"][local_idx]),
            "back_img": process_img(f["back_img_jpeg"][local_idx]),
            "overhead_img": process_img(f["overhead_img_jpeg"][local_idx]),
            "next_front_img": process_img(f["next_front_img_jpeg"][local_idx]),
            "next_left_img": process_img(f["next_left_img_jpeg"][local_idx]),
            "next_right_img": process_img(f["next_right_img_jpeg"][local_idx]),
            "next_back_img": process_img(f["next_back_img_jpeg"][local_idx]),
            "next_overhead_img": process_img(f["next_overhead_img_jpeg"][local_idx]),
            "proprio": torch.from_numpy(self.proprio[idx].copy()).float(),
            "task_state": torch.from_numpy(self.task_state[idx].copy()).float(),
            "action": torch.from_numpy(self.action[idx].copy()).float(),
            "reward": torch.tensor([self.reward[idx]]).float(),
            "next_proprio": torch.from_numpy(self.next_proprio[idx].copy()).float(),
            "next_task_state": torch.from_numpy(self.next_task_state[idx].copy()).float(),
        }


def load_model(checkpoint_path: str, device: str = 'cuda'):
    """Load Stage 2 model with Transformer Dynamics"""
    config = WorldModelWithTaskConfig(
        use_transformer_dynamics=True,
        transformer_dynamics_layers=4,
    )
    model = WorldModelWithTask(config)

    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if 'model_state_dict' in ckpt:
        model.load_state_dict(ckpt['model_state_dict'])
    else:
        model.load_state_dict(ckpt)

    model = model.to(device)
    model.eval()

    print(f"\n[Model] Loaded from {checkpoint_path}")
    print(f"[Model] Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"[Model] Transformer Dynamics: {model.use_transformer_dynamics}")

    return model


def evaluate_single_step(model, dataset, device, num_samples=5, save_dir=None):
    """Evaluate single-step prediction accuracy"""
    print("\n" + "="*60)
    print("1. Single-Step Prediction Evaluation")
    print("="*60)

    model.eval()
    proprio_errors = []
    task_errors = []
    reward_errors = []
    psnr_values = []

    indices = np.random.choice(len(dataset), min(num_samples, len(dataset)), replace=False)

    with torch.no_grad():
        for i, idx in enumerate(indices):
            batch = dataset[idx]

            # Prepare inputs
            front_img = batch['front_img'].unsqueeze(0).to(device)
            left_img = batch['left_img'].unsqueeze(0).to(device)
            right_img = batch['right_img'].unsqueeze(0).to(device)
            back_img = batch['back_img'].unsqueeze(0).to(device)
            overhead_img = batch['overhead_img'].unsqueeze(0).to(device)
            proprio = batch['proprio'].unsqueeze(0).to(device)
            task_state = batch['task_state'].unsqueeze(0).to(device)
            action = batch['action'].unsqueeze(0).to(device)

            # Ground truth
            next_proprio_gt = batch['next_proprio'].unsqueeze(0).to(device)
            next_task_gt = batch['next_task_state'].unsqueeze(0).to(device)
            reward_gt = batch['reward'].unsqueeze(0).to(device)

            # Prediction
            outputs = model(front_img, left_img, right_img, back_img, overhead_img,
                          proprio, task_state, action, decode_images=True)

            # Calculate errors
            proprio_err = torch.mean((outputs['pred_proprio'] - next_proprio_gt) ** 2).item()
            task_err = torch.mean((outputs['pred_task_state'] - next_task_gt) ** 2).item()
            reward_err = torch.mean((outputs['pred_reward'] - reward_gt) ** 2).item()

            proprio_errors.append(proprio_err)
            task_errors.append(task_err)
            reward_errors.append(reward_err)

            # Calculate PSNR if images available
            psnr = None
            if 'pred_images' in outputs and outputs['pred_images'] is not None:
                true_next = {
                    'front': batch['next_front_img'].unsqueeze(0),
                    'overhead': batch['next_overhead_img'].unsqueeze(0),
                }
                mse_front = torch.mean((outputs['pred_images']['front'].cpu() - true_next['front']) ** 2).item()
                mse_overhead = torch.mean((outputs['pred_images']['overhead'].cpu() - true_next['overhead']) ** 2).item()
                avg_mse = (mse_front + mse_overhead) / 2
                if avg_mse > 0:
                    psnr = 10 * np.log10(1.0 / avg_mse)
                    psnr_values.append(psnr)

            print(f"\n[Sample {i+1}] idx={idx}")
            print(f"  Proprio MSE: {proprio_err:.6f}")
            print(f"  Task MSE:    {task_err:.6f}")
            print(f"  Reward MSE:  {reward_err:.6f}")
            if psnr:
                print(f"  Image PSNR:  {psnr:.2f} dB")

            # Save comparison images
            if save_dir and 'pred_images' in outputs and outputs['pred_images'] is not None:
                os.makedirs(save_dir, exist_ok=True)

                for cam_name in ['front', 'overhead']:
                    true_img = batch[f'next_{cam_name}_img'].numpy().transpose(1, 2, 0)
                    pred_img = outputs['pred_images'][cam_name][0].cpu().numpy().transpose(1, 2, 0)

                    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
                    axes[0].imshow(np.clip(true_img, 0, 1))
                    axes[0].set_title(f'Ground Truth [{cam_name}]')
                    axes[0].axis('off')
                    axes[1].imshow(np.clip(pred_img, 0, 1))
                    axes[1].set_title(f'Predicted [{cam_name}]')
                    axes[1].axis('off')

                    plt.tight_layout()
                    plt.savefig(f'{save_dir}/sample{i+1}_{cam_name}.png', dpi=150)
                    plt.close()

    print("\n" + "-"*40)
    print("Single-Step Summary:")
    print(f"  Avg Proprio MSE: {np.mean(proprio_errors):.6f} ± {np.std(proprio_errors):.6f}")
    print(f"  Avg Task MSE:    {np.mean(task_errors):.6f} ± {np.std(task_errors):.6f}")
    print(f"  Avg Reward MSE:  {np.mean(reward_errors):.6f} ± {np.std(reward_errors):.6f}")
    if psnr_values:
        print(f"  Avg PSNR:        {np.mean(psnr_values):.2f} ± {np.std(psnr_values):.2f} dB")

    return np.mean(proprio_errors), np.mean(task_errors)


def evaluate_rollout(model, dataset, device, num_steps=10, num_samples=3, save_dir=None):
    """Evaluate multi-step rollout prediction"""
    print("\n" + "="*60)
    print(f"2. Multi-Step Rollout Evaluation ({num_steps} steps)")
    print("="*60)

    model.eval()
    all_rollout_errors = []

    with torch.no_grad():
        for sample_idx in range(num_samples):
            start_idx = np.random.randint(0, max(1, len(dataset) - num_steps - 1))

            print(f"\n[Rollout {sample_idx+1}] Starting from idx={start_idx}")

            batch = dataset[start_idx]

            # Get initial latent state
            front_img = batch['front_img'].unsqueeze(0).to(device)
            left_img = batch['left_img'].unsqueeze(0).to(device)
            right_img = batch['right_img'].unsqueeze(0).to(device)
            back_img = batch['back_img'].unsqueeze(0).to(device)
            overhead_img = batch['overhead_img'].unsqueeze(0).to(device)
            proprio = batch['proprio'].unsqueeze(0).to(device)
            task_state = batch['task_state'].unsqueeze(0).to(device)

            latent = model.encode_state(front_img, left_img, right_img, back_img, overhead_img,
                                       proprio, task_state)

            step_errors = []

            for step in range(num_steps):
                step_batch = dataset[start_idx + step]
                action = step_batch['action'].unsqueeze(0).to(device)

                # Predict next state (autoregressive)
                next_latent = model.predict_next(latent, action)

                # Decode predictions
                pred_proprio = model.proprio_predictor(next_latent)
                pred_task = model.task_predictor(next_latent)

                # Ground truth
                gt_proprio = step_batch['next_proprio'].unsqueeze(0).to(device)
                gt_task = step_batch['next_task_state'].unsqueeze(0).to(device)

                # Errors
                proprio_err = torch.mean((pred_proprio - gt_proprio) ** 2).item()
                task_err = torch.mean((pred_task - gt_task) ** 2).item()

                step_errors.append({'proprio': proprio_err, 'task': task_err})

                # Use predicted latent for next step
                latent = next_latent

                if step < 3 or step == num_steps - 1:
                    print(f"  Step {step+1}: Proprio={proprio_err:.6f}, Task={task_err:.6f}")

            all_rollout_errors.append(step_errors)

    # Aggregate by step
    step_proprio = [np.mean([r[s]['proprio'] for r in all_rollout_errors]) for s in range(num_steps)]
    step_task = [np.mean([r[s]['task'] for r in all_rollout_errors]) for s in range(num_steps)]

    print("\n" + "-"*40)
    print("Rollout Summary:")
    print(f"  Step 1:  Proprio={step_proprio[0]:.6f}, Task={step_task[0]:.6f}")
    print(f"  Step 5:  Proprio={step_proprio[4]:.6f}, Task={step_task[4]:.6f}")
    print(f"  Step 10: Proprio={step_proprio[-1]:.6f}, Task={step_task[-1]:.6f}")

    # Calculate error growth ratio
    proprio_growth = step_proprio[-1] / step_proprio[0] if step_proprio[0] > 0 else float('inf')
    task_growth = step_task[-1] / step_task[0] if step_task[0] > 0 else float('inf')
    print(f"  Error growth (step 10 / step 1): Proprio={proprio_growth:.2f}x, Task={task_growth:.2f}x")

    # Plot
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        steps = list(range(1, num_steps + 1))

        axes[0].plot(steps, step_proprio, 'b-o', linewidth=2, markersize=6)
        axes[0].set_xlabel('Rollout Step')
        axes[0].set_ylabel('Proprio MSE')
        axes[0].set_title('Proprio Error vs Rollout Step')
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(steps, step_task, 'r-o', linewidth=2, markersize=6)
        axes[1].set_xlabel('Rollout Step')
        axes[1].set_ylabel('Task MSE')
        axes[1].set_title('Task Error vs Rollout Step')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{save_dir}/rollout_error_growth.png', dpi=150)
        plt.close()
        print(f"\n[Saved] {save_dir}/rollout_error_growth.png")

    return step_proprio, step_task


def evaluate_state_components(model, dataset, device, num_samples=100):
    """Evaluate per-dimension prediction accuracy"""
    print("\n" + "="*60)
    print("3. State Component Analysis")
    print("="*60)

    model.eval()
    proprio_errors = []
    task_errors = []

    indices = np.random.choice(len(dataset), min(num_samples, len(dataset)), replace=False)

    with torch.no_grad():
        for idx in indices:
            batch = dataset[idx]

            front_img = batch['front_img'].unsqueeze(0).to(device)
            left_img = batch['left_img'].unsqueeze(0).to(device)
            right_img = batch['right_img'].unsqueeze(0).to(device)
            back_img = batch['back_img'].unsqueeze(0).to(device)
            overhead_img = batch['overhead_img'].unsqueeze(0).to(device)
            proprio = batch['proprio'].unsqueeze(0).to(device)
            task_state = batch['task_state'].unsqueeze(0).to(device)
            action = batch['action'].unsqueeze(0).to(device)

            next_proprio_gt = batch['next_proprio'].unsqueeze(0).to(device)
            next_task_gt = batch['next_task_state'].unsqueeze(0).to(device)

            outputs = model(front_img, left_img, right_img, back_img, overhead_img,
                          proprio, task_state, action)

            proprio_err = ((outputs['pred_proprio'] - next_proprio_gt) ** 2).squeeze().cpu().numpy()
            task_err = ((outputs['pred_task_state'] - next_task_gt) ** 2).squeeze().cpu().numpy()

            proprio_errors.append(proprio_err)
            task_errors.append(task_err)

    proprio_mean = np.mean(proprio_errors, axis=0)
    task_mean = np.mean(task_errors, axis=0)

    print(f"\nProprio (34D) Analysis:")
    print(f"  Joint positions (0-13):   {np.mean(proprio_mean[:14]):.6f}")
    print(f"  Joint velocities (14-27): {np.mean(proprio_mean[14:28]):.6f}")
    print(f"  Gripper states (28-33):   {np.mean(proprio_mean[28:]):.6f}")
    print(f"  Max error: dim {np.argmax(proprio_mean)} ({np.max(proprio_mean):.6f})")
    print(f"  Min error: dim {np.argmin(proprio_mean)} ({np.min(proprio_mean):.6f})")

    print(f"\nTask State (44D) Analysis:")
    print(f"  Cable segments (0-29):    {np.mean(task_mean[:30]):.6f}")
    print(f"  Hook position (30-32):    {np.mean(task_mean[30:33]):.6f}")
    print(f"  EE positions (33-38):     {np.mean(task_mean[33:39]):.6f}")
    print(f"  Distances (39-43):        {np.mean(task_mean[39:]):.6f}")
    print(f"  Max error: dim {np.argmax(task_mean)} ({np.max(task_mean):.6f})")
    print(f"  Min error: dim {np.argmin(task_mean)} ({np.min(task_mean):.6f})")

    return proprio_mean, task_mean


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', default='/home/rlrk/IsaacLab/checkpoints/world_model_v2_stage2/stage2_best.pt')
    parser.add_argument('--data_path', default='/home/rlrk/IsaacLab/data/world_model_dual_arm_v2')
    parser.add_argument('--save_dir', default='/home/rlrk/IsaacLab/checkpoints/world_model_v2_stage2/eval_results')
    parser.add_argument('--num_samples', type=int, default=5)
    parser.add_argument('--rollout_steps', type=int, default=10)
    parser.add_argument('--device', default='cuda')
    args = parser.parse_args()

    print("="*60)
    print("Stage 2 v2 Model Evaluation")
    print("="*60)

    # Load model
    model = load_model(args.checkpoint, args.device)

    # Load data
    print(f"\n[Data] Loading from {args.data_path}")
    dataset = FiveCameraHDF5Dataset(args.data_path)

    os.makedirs(args.save_dir, exist_ok=True)

    # Evaluations
    single_proprio, single_task = evaluate_single_step(
        model, dataset, args.device, args.num_samples, args.save_dir)

    rollout_proprio, rollout_task = evaluate_rollout(
        model, dataset, args.device, args.rollout_steps, 3, args.save_dir)

    proprio_per_dim, task_per_dim = evaluate_state_components(
        model, dataset, args.device, 100)

    # Final summary
    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60)
    print(f"\nSingle-Step Avg MSE: Proprio={single_proprio:.6f}, Task={single_task:.6f}")
    print(f"10-Step Rollout Final MSE: Proprio={rollout_proprio[-1]:.6f}, Task={rollout_task[-1]:.6f}")
    print(f"\nResults saved to: {args.save_dir}")


if __name__ == '__main__':
    main()
