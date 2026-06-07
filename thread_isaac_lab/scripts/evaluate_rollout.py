#!/usr/bin/env python3
"""Evaluate World Model multi-step rollout accuracy."""

import argparse
import os
import sys
import glob
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thread_isaac_lab.scripts.train_4cam_wm import (
    FourCameraWorldModel,
    FourCameraWorldModelConfig,
    FourCameraHDF5Dataset,
    TransformerDynamics,
)


def evaluate_rollout(args):
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

    # Add Transformer Dynamics if Stage 2
    if args.stage2:
        model.use_transformer_dynamics = True
        model.transformer_dynamics = TransformerDynamics(
            latent_dim=config.fusion_dim,
            action_dim=config.action_dim,
            num_layers=4,
            nhead=8,
        ).to(device)

    # Load checkpoint
    print(f"[Load] {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)

    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint

    model_dict = model.state_dict()
    filtered_dict = {k: v for k, v in state_dict.items() if k in model_dict and v.shape == model_dict[k].shape}
    model.load_state_dict(filtered_dict, strict=False)
    model.eval()

    print(f"[Model] Loaded {len(filtered_dict)}/{len(model_dict)} parameters")
    print(f"[Model] Transformer Dynamics: {'Yes' if args.stage2 else 'No'}")

    # Prepare evaluation
    horizon = args.horizon
    num_sequences = args.num_sequences
    sequence_length = horizon + 1  # Need horizon+1 consecutive frames

    print(f"\n[Eval] Horizon: {horizon} steps, Sequences: {num_sequences}")

    # Find valid sequence starts that don't cross episode boundaries
    np.random.seed(args.seed)

    # Get done flags to detect episode boundaries
    done_flags = dataset.done if hasattr(dataset, 'done') else None

    valid_starts = []
    if done_flags is not None:
        print("[Eval] Finding valid sequences (avoiding episode boundaries)...")
        for i in range(len(dataset) - sequence_length):
            # Check if any done flag is set within the sequence
            # done=1 means episode ended at that step
            if not np.any(done_flags[i:i + sequence_length - 1]):
                valid_starts.append(i)
        print(f"[Eval] Found {len(valid_starts)} valid sequence starts (no episode boundaries)")
    else:
        print("[Eval] No done flags found, using all indices")
        valid_starts = list(range(len(dataset) - sequence_length))

    if len(valid_starts) < num_sequences:
        print(f"[Warning] Only {len(valid_starts)} valid sequences, using all")
        num_sequences = len(valid_starts)

    start_indices = np.random.choice(valid_starts, size=num_sequences, replace=False)

    # Metrics storage
    proprio_mse_per_step = {step: [] for step in range(1, horizon + 1)}
    task_mse_per_step = {step: [] for step in range(1, horizon + 1)}
    reward_mse_per_step = {step: [] for step in range(1, horizon + 1)}
    image_psnr_per_step = {step: [] for step in range(1, horizon + 1)}

    print(f"[Eval] Running rollouts...")

    for seq_idx, start_idx in enumerate(start_indices):
        if seq_idx % 20 == 0:
            print(f"  Sequence {seq_idx + 1}/{num_sequences}")

        # Load initial state
        sample = dataset[start_idx]

        # Current state
        images = {cam: sample[f"{cam}_img"].unsqueeze(0).to(device) for cam in camera_names}
        proprio = sample["proprio"].unsqueeze(0).to(device)
        task_state = sample.get("task_state")
        if task_state is not None:
            task_state = task_state.unsqueeze(0).to(device)

        # Encode initial state
        with torch.no_grad():
            visual_features = model.visual_encoder(images)
            proprio_features = model.proprio_encoder(proprio)

            if task_state is not None and hasattr(model, 'task_encoder'):
                task_features = model.task_encoder(task_state)
                fused_state = torch.cat([visual_features, proprio_features, task_features], dim=-1)
            else:
                fused_state = torch.cat([visual_features, proprio_features], dim=-1)

        # Rollout
        current_fused = fused_state
        current_proprio = proprio
        current_task = task_state

        for step in range(1, horizon + 1):
            # Get action and ground truth from dataset
            step_sample = dataset[start_idx + step - 1]
            action = step_sample["action"].unsqueeze(0).to(device)

            gt_next_proprio = step_sample["next_proprio"].unsqueeze(0).to(device)
            gt_reward = step_sample["reward"].unsqueeze(0).to(device).squeeze(-1)
            gt_next_task = step_sample.get("next_task_state")
            if gt_next_task is not None:
                gt_next_task = gt_next_task.unsqueeze(0).to(device)

            # Predict next state
            with torch.no_grad():
                if args.stage2 and hasattr(model, 'transformer_dynamics'):
                    next_fused = model.transformer_dynamics(current_fused, action)
                else:
                    next_fused = model.predict_next(current_fused, action)

                pred_proprio = model.proprio_predictor(next_fused)
                pred_reward = model.reward_predictor(torch.cat([current_fused, next_fused], dim=-1))

                if hasattr(model, 'task_predictor'):
                    pred_task = model.task_predictor(next_fused)

            # Compute errors
            proprio_mse = F.mse_loss(pred_proprio, gt_next_proprio).item()
            reward_mse = F.mse_loss(pred_reward.squeeze(-1), gt_reward).item()

            proprio_mse_per_step[step].append(proprio_mse)
            reward_mse_per_step[step].append(reward_mse)

            if gt_next_task is not None and hasattr(model, 'task_predictor'):
                task_mse = F.mse_loss(pred_task, gt_next_task).item()
                task_mse_per_step[step].append(task_mse)

            # Image reconstruction (if decoder available)
            if hasattr(model, 'image_decoder') and model.use_image_decoder:
                with torch.no_grad():
                    pred_images = model.image_decoder(next_fused)

                # Get ground truth next images
                next_step_sample = dataset[start_idx + step]
                psnr_list = []
                for cam in camera_names:
                    gt_img = next_step_sample[f"{cam}_img"].unsqueeze(0).to(device)
                    pred_img = pred_images[cam]

                    mse = F.mse_loss(pred_img, gt_img).item()
                    psnr = 10 * np.log10(1.0 / (mse + 1e-10))
                    psnr_list.append(psnr)

                image_psnr_per_step[step].append(np.mean(psnr_list))

            # Update state for next step (autoregressive)
            current_fused = next_fused
            current_proprio = pred_proprio
            if hasattr(model, 'task_predictor'):
                current_task = pred_task

    # Compute statistics
    print("\n" + "=" * 70)
    print("Multi-Step Rollout Evaluation Results")
    print("=" * 70)

    print(f"\n{'Step':<6} {'Proprio MSE':<15} {'Task MSE':<15} {'Reward MSE':<15} {'Image PSNR':<15}")
    print("-" * 70)

    steps = list(range(1, horizon + 1))
    proprio_means = []
    task_means = []
    reward_means = []
    psnr_means = []

    for step in steps:
        proprio_mean = np.mean(proprio_mse_per_step[step]) if proprio_mse_per_step[step] else 0
        task_mean = np.mean(task_mse_per_step[step]) if task_mse_per_step[step] else 0
        reward_mean = np.mean(reward_mse_per_step[step]) if reward_mse_per_step[step] else 0
        psnr_mean = np.mean(image_psnr_per_step[step]) if image_psnr_per_step[step] else 0

        proprio_means.append(proprio_mean)
        task_means.append(task_mean)
        reward_means.append(reward_mean)
        psnr_means.append(psnr_mean)

        print(f"{step:<6} {proprio_mean:<15.6f} {task_mean:<15.6f} {reward_mean:<15.6f} {psnr_mean:<15.2f}")

    print("-" * 70)

    # Summary
    print(f"\n[Summary]")
    print(f"  Step 1 Proprio MSE:  {proprio_means[0]:.6f}")
    print(f"  Step {horizon} Proprio MSE: {proprio_means[-1]:.6f}")
    print(f"  Degradation ratio:   {proprio_means[-1] / (proprio_means[0] + 1e-10):.2f}x")

    if psnr_means[0] > 0:
        print(f"\n  Step 1 PSNR:  {psnr_means[0]:.2f} dB")
        print(f"  Step {horizon} PSNR: {psnr_means[-1]:.2f} dB")
        print(f"  PSNR drop:    {psnr_means[0] - psnr_means[-1]:.2f} dB")

    print("=" * 70)

    # Plot results
    if args.save_plot:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Proprio MSE
        axes[0, 0].plot(steps, proprio_means, 'b-o', linewidth=2, markersize=6)
        axes[0, 0].set_xlabel('Rollout Step')
        axes[0, 0].set_ylabel('MSE')
        axes[0, 0].set_title('Proprio Prediction Error')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_yscale('log')

        # Task MSE
        if any(task_means):
            axes[0, 1].plot(steps, task_means, 'g-o', linewidth=2, markersize=6)
            axes[0, 1].set_xlabel('Rollout Step')
            axes[0, 1].set_ylabel('MSE')
            axes[0, 1].set_title('Task State Prediction Error')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].set_yscale('log')

        # Reward MSE
        axes[1, 0].plot(steps, reward_means, 'r-o', linewidth=2, markersize=6)
        axes[1, 0].set_xlabel('Rollout Step')
        axes[1, 0].set_ylabel('MSE')
        axes[1, 0].set_title('Reward Prediction Error')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_yscale('log')

        # Image PSNR
        if any(psnr_means):
            axes[1, 1].plot(steps, psnr_means, 'm-o', linewidth=2, markersize=6)
            axes[1, 1].set_xlabel('Rollout Step')
            axes[1, 1].set_ylabel('PSNR (dB)')
            axes[1, 1].set_title('Image Reconstruction Quality')
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].axhline(y=30, color='r', linestyle='--', alpha=0.5, label='Good (30dB)')
            axes[1, 1].axhline(y=40, color='g', linestyle='--', alpha=0.5, label='Excellent (40dB)')
            axes[1, 1].legend()

        plt.suptitle(f'Multi-Step Rollout Evaluation (Horizon={horizon})', fontsize=14)
        plt.tight_layout()

        plot_path = output_dir / f"rollout_evaluation_h{horizon}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"\n[Plot] Saved to: {plot_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--cameras", type=str, nargs='+',
                        default=['front_left', 'front_right', 'back'])
    parser.add_argument("--encoder_type", type=str, default="hybrid")
    parser.add_argument("--stage2", action="store_true", help="Use Transformer Dynamics")
    parser.add_argument("--horizon", type=int, default=10, help="Rollout horizon")
    parser.add_argument("--num_sequences", type=int, default=100)
    parser.add_argument("--output_dir", type=str, default="rollout_evaluation")
    parser.add_argument("--save_plot", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    evaluate_rollout(args)
