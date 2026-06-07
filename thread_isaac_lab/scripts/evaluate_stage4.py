#!/usr/bin/env python3
"""
Evaluation script for Stage 4: Cross-Attention World Model

Tests:
1. Single-step prediction accuracy
2. Multi-step rollout
3. Image reconstruction quality (PSNR)
4. Counterfactual generation
5. Cross-attention visualization
"""

import torch
import numpy as np
import os
import sys
import h5py
import io
from PIL import Image
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.world_model_with_task import WorldModelWithTask, WorldModelWithTaskConfig


def decompress_jpeg(jpeg_bytes):
    """Decompress JPEG bytes to numpy array."""
    img = Image.open(io.BytesIO(bytes(jpeg_bytes)))
    return np.array(img)


def load_model(checkpoint_path, device='cuda'):
    """Load Stage 4 model with cross-attention."""
    config = WorldModelWithTaskConfig(
        use_cross_attention=True,
        cross_attention_heads=4,
        cross_attention_layers=2,
        use_transformer_dynamics=True,
        transformer_dynamics_layers=4,
    )
    model = WorldModelWithTask(config)

    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if 'model_state_dict' in ckpt:
        model.load_state_dict(ckpt['model_state_dict'])
    else:
        model.load_state_dict(ckpt)

    model.eval().to(device)
    return model


def load_sample(h5_file, idx, device='cuda'):
    """Load a single sample from HDF5 file."""
    with h5py.File(h5_file, 'r') as f:
        images = {}
        next_images = {}
        for cam in ['front', 'left', 'right', 'back', 'overhead']:
            img = decompress_jpeg(f[f'{cam}_img_jpeg'][idx])
            images[cam] = torch.tensor(img).permute(2, 0, 1).float() / 255.0
            images[cam] = images[cam].unsqueeze(0).to(device)

            next_img = decompress_jpeg(f[f'next_{cam}_img_jpeg'][idx])
            next_images[cam] = torch.tensor(next_img).permute(2, 0, 1).float() / 255.0
            next_images[cam] = next_images[cam].unsqueeze(0).to(device)

        proprio = torch.tensor(f['proprio'][idx]).float().unsqueeze(0).to(device)
        next_proprio = torch.tensor(f['next_proprio'][idx]).float().unsqueeze(0).to(device)
        task_state = torch.tensor(f['task_state'][idx]).float().unsqueeze(0).to(device)
        next_task_state = torch.tensor(f['next_task_state'][idx]).float().unsqueeze(0).to(device)
        action = torch.tensor(f['action'][idx]).float().unsqueeze(0).to(device)
        reward = torch.tensor(f['reward'][idx]).float().unsqueeze(0).to(device)

    return {
        'images': images,
        'next_images': next_images,
        'proprio': proprio,
        'next_proprio': next_proprio,
        'task_state': task_state,
        'next_task_state': next_task_state,
        'action': action,
        'reward': reward,
    }


def evaluate_single_step(model, data_file, num_samples=100, device='cuda'):
    """Evaluate single-step prediction accuracy."""
    print("\n" + "=" * 60)
    print("Single-Step Prediction Evaluation")
    print("=" * 60)

    proprio_errors = []
    task_errors = []
    reward_errors = []
    psnr_values = {cam: [] for cam in ['front', 'left', 'right', 'back', 'overhead']}

    with h5py.File(data_file, 'r') as f:
        total_samples = len(f['proprio'])
        indices = np.random.choice(total_samples, min(num_samples, total_samples), replace=False)

    for idx in indices:
        sample = load_sample(data_file, idx, device)

        with torch.no_grad():
            outputs = model(
                sample['images']['front'],
                sample['images']['left'],
                sample['images']['right'],
                sample['images']['back'],
                sample['images']['overhead'],
                sample['proprio'],
                sample['task_state'],
                sample['action'],
                decode_images=True
            )

        # Compute errors
        proprio_err = torch.mean((outputs['pred_proprio'] - sample['next_proprio']) ** 2).item()
        task_err = torch.mean((outputs['pred_task_state'] - sample['next_task_state']) ** 2).item()
        reward_err = torch.mean((outputs['pred_reward'] - sample['reward']) ** 2).item()

        proprio_errors.append(proprio_err)
        task_errors.append(task_err)
        reward_errors.append(reward_err)

        # Compute PSNR for each camera
        for cam in ['front', 'left', 'right', 'back', 'overhead']:
            pred = outputs['pred_images'][cam][0].cpu().numpy()
            true = sample['next_images'][cam][0].cpu().numpy()
            pred = np.clip(pred, 0, 1)
            mse = np.mean((pred - true) ** 2)
            psnr = 10 * np.log10(1.0 / mse) if mse > 0 else float('inf')
            psnr_values[cam].append(psnr)

    print(f"\nResults ({num_samples} samples):")
    print(f"  Proprio MSE:  {np.mean(proprio_errors):.6f} +/- {np.std(proprio_errors):.6f}")
    print(f"  Task MSE:     {np.mean(task_errors):.6f} +/- {np.std(task_errors):.6f}")
    print(f"  Reward MSE:   {np.mean(reward_errors):.6f} +/- {np.std(reward_errors):.6f}")
    print(f"\nImage Reconstruction PSNR:")
    for cam in ['front', 'left', 'right', 'back', 'overhead']:
        print(f"  {cam:10s}: {np.mean(psnr_values[cam]):.2f} +/- {np.std(psnr_values[cam]):.2f} dB")

    return {
        'proprio_mse': np.mean(proprio_errors),
        'task_mse': np.mean(task_errors),
        'reward_mse': np.mean(reward_errors),
        'psnr': {cam: np.mean(psnr_values[cam]) for cam in psnr_values},
    }


def evaluate_rollout(model, data_file, horizon=10, num_samples=20, device='cuda'):
    """Evaluate multi-step rollout accuracy."""
    print("\n" + "=" * 60)
    print(f"Multi-Step Rollout Evaluation (horizon={horizon})")
    print("=" * 60)

    rollout_errors = {step: [] for step in range(1, horizon + 1)}

    with h5py.File(data_file, 'r') as f:
        total_samples = len(f['proprio'])
        # Start indices that allow for full horizon
        valid_starts = total_samples - horizon
        if valid_starts <= 0:
            print(f"[WARN] Not enough samples for horizon {horizon}")
            return {}
        indices = np.random.choice(valid_starts, min(num_samples, valid_starts), replace=False)

    for start_idx in indices:
        # Load initial state
        sample = load_sample(data_file, start_idx, device)

        # Initialize predicted state
        pred_proprio = sample['proprio'].clone()
        pred_task = sample['task_state'].clone()
        current_images = {cam: sample['images'][cam].clone() for cam in sample['images']}

        for step in range(1, horizon + 1):
            # Load action and true next state for this step
            step_sample = load_sample(data_file, start_idx + step - 1, device)
            action = step_sample['action']

            with torch.no_grad():
                outputs = model(
                    current_images['front'],
                    current_images['left'],
                    current_images['right'],
                    current_images['back'],
                    current_images['overhead'],
                    pred_proprio,
                    pred_task,
                    action,
                    decode_images=True
                )

            # Update predicted state
            pred_proprio = outputs['pred_proprio']
            pred_task = outputs['pred_task_state']

            # Update images for next step (use predicted images)
            for cam in current_images:
                current_images[cam] = outputs['pred_images'][cam]

            # Load true state at this step
            true_sample = load_sample(data_file, start_idx + step, device)

            # Compute error
            proprio_err = torch.mean((pred_proprio - true_sample['proprio']) ** 2).item()
            rollout_errors[step].append(proprio_err)

    print(f"\nRollout Proprio MSE (accumulated error):")
    for step in range(1, horizon + 1):
        mean_err = np.mean(rollout_errors[step])
        std_err = np.std(rollout_errors[step])
        print(f"  Step {step:2d}: {mean_err:.6f} +/- {std_err:.6f}")

    return rollout_errors


def evaluate_counterfactual(model, data_file, device='cuda'):
    """Test counterfactual generation."""
    print("\n" + "=" * 60)
    print("Counterfactual Generation Test")
    print("=" * 60)

    sample = load_sample(data_file, 100, device)

    # Define action candidates
    real_action = sample['action']
    actions = [
        real_action,
        real_action * 0.5,
        real_action * 2.0,
        -real_action,
        torch.zeros_like(real_action),
    ]
    action_labels = ['original', 'half', 'double', 'opposite', 'idle']

    # Generate counterfactual predictions
    futures = model.counterfactual.predict_futures(
        sample['images']['front'],
        sample['images']['left'],
        sample['images']['right'],
        sample['images']['back'],
        sample['images']['overhead'],
        sample['proprio'],
        sample['task_state'],
        actions,
        horizon=1,
        decode_images=True
    )

    print(f"\nAction comparison:")
    for i, (label, future) in enumerate(zip(action_labels, futures)):
        reward = future['pred_reward'].item()
        proprio_change = torch.norm(future['pred_proprio'] - sample['proprio']).item()
        print(f"  {label:10s}: reward={reward:.4f}, proprio_delta={proprio_change:.4f}")

    # Best action selection
    best_idx, best_action, _ = model.counterfactual.select_best_action(
        sample['images']['front'],
        sample['images']['left'],
        sample['images']['right'],
        sample['images']['back'],
        sample['images']['overhead'],
        sample['proprio'],
        sample['task_state'],
        actions,
        criterion='reward'
    )
    print(f"\nBest action by reward: {action_labels[best_idx]}")

    # Save visualization
    save_dir = '/home/rlrk/IsaacLab/thread_isaac_lab/training_debug/stage4_counterfactual'
    os.makedirs(save_dir, exist_ok=True)
    model.counterfactual.visualize_futures(futures, save_dir, camera='front', action_labels=action_labels)
    print(f"\nVisualization saved to: {save_dir}")

    return futures


def main():
    print("=" * 60)
    print("Stage 4: Cross-Attention World Model Evaluation")
    print("=" * 60)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    checkpoint_path = '/home/rlrk/IsaacLab/checkpoints/world_model_v2_stage4/stage4_best.pt'
    data_path = '/home/rlrk/IsaacLab/data/world_model_dual_arm_v2'

    # Find data files
    import glob
    data_files = sorted(glob.glob(os.path.join(data_path, '*.h5')))
    if not data_files:
        print(f"[ERROR] No data files found in {data_path}")
        return

    data_file = data_files[0]
    print(f"\n[Config]")
    print(f"  Checkpoint: {checkpoint_path}")
    print(f"  Data file: {data_file}")
    print(f"  Device: {device}")

    # Load model
    print("\n[Loading model...]")
    model = load_model(checkpoint_path, device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"[OK] Model loaded: {total_params:,} parameters")
    print(f"     Cross-Attention: {model.use_cross_attention}")

    # Run evaluations
    single_step_results = evaluate_single_step(model, data_file, num_samples=100, device=device)
    rollout_results = evaluate_rollout(model, data_file, horizon=5, num_samples=20, device=device)
    counterfactual_results = evaluate_counterfactual(model, data_file, device=device)

    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"\nSingle-step Prediction:")
    print(f"  Proprio MSE: {single_step_results['proprio_mse']:.6f}")
    print(f"  Task MSE:    {single_step_results['task_mse']:.6f}")
    print(f"  Avg PSNR:    {np.mean(list(single_step_results['psnr'].values())):.2f} dB")

    if rollout_results:
        print(f"\nMulti-step Rollout:")
        print(f"  Step 1 MSE: {np.mean(rollout_results[1]):.6f}")
        print(f"  Step 5 MSE: {np.mean(rollout_results[5]):.6f}")

    print(f"\nCounterfactual Generation: [OK]")
    print("=" * 60)


if __name__ == '__main__':
    main()
