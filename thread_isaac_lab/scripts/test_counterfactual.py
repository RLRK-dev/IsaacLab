#!/usr/bin/env python3
"""
Test script for Stage 3: Counterfactual Generation

Tests the CounterfactualPredictor to predict multiple futures from the same state
with different actions, enabling "what if" reasoning.
"""

import torch
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.world_model_with_task import WorldModelWithTask, WorldModelWithTaskConfig


def test_with_dummy_data():
    """Test counterfactual generation with dummy data."""
    print("=" * 60)
    print("Stage 3: Counterfactual Generation Test (Dummy Data)")
    print("=" * 60)

    # Load model
    print("\n[1] Loading model...")
    config = WorldModelWithTaskConfig(
        use_transformer_dynamics=True,
        transformer_dynamics_layers=4,
    )
    model = WorldModelWithTask(config)

    checkpoint_path = '/home/rlrk/IsaacLab/checkpoints/world_model_v2_stage2/stage2_best.pt'
    if os.path.exists(checkpoint_path):
        ckpt = torch.load(checkpoint_path, map_location='cuda', weights_only=False)
        if 'model_state_dict' in ckpt:
            model.load_state_dict(ckpt['model_state_dict'])
        else:
            model.load_state_dict(ckpt)
        print(f"[OK] Loaded checkpoint from {checkpoint_path}")
    else:
        print(f"[WARN] Checkpoint not found, using random weights")

    model = model.cuda()
    model.eval()

    print(f"[OK] Model loaded: {sum(p.numel() for p in model.parameters()):,} parameters")

    # Create dummy inputs
    print("\n[2] Creating dummy inputs...")
    batch_size = 1
    device = 'cuda'

    front_img = torch.randn(batch_size, 3, 256, 256, device=device)
    left_img = torch.randn(batch_size, 3, 256, 256, device=device)
    right_img = torch.randn(batch_size, 3, 256, 256, device=device)
    back_img = torch.randn(batch_size, 3, 256, 256, device=device)
    overhead_img = torch.randn(batch_size, 3, 256, 256, device=device)
    proprio = torch.randn(batch_size, 34, device=device)
    task_state = torch.randn(batch_size, 44, device=device)

    # Define multiple action candidates
    print("\n[3] Defining action candidates...")
    actions = [
        torch.randn(batch_size, 18, device=device) * 0.1,  # Small random action
        torch.randn(batch_size, 18, device=device) * 0.5,  # Medium random action
        torch.randn(batch_size, 18, device=device) * 1.0,  # Large random action
        torch.zeros(batch_size, 18, device=device),         # No action (idle)
    ]
    action_labels = ['small_random', 'medium_random', 'large_random', 'idle']

    print(f"[OK] Created {len(actions)} action candidates")

    # Test single-step counterfactual
    print("\n[4] Testing single-step counterfactual prediction...")
    futures = model.counterfactual.predict_futures(
        front_img, left_img, right_img, back_img, overhead_img,
        proprio, task_state, actions, horizon=1, decode_images=True
    )

    print(f"[OK] Generated {len(futures)} futures")
    for i, future in enumerate(futures):
        reward = future['pred_reward'].item()
        print(f"  {action_labels[i]}: reward={reward:.4f}")

    # Test best action selection
    print("\n[5] Testing best action selection...")
    best_idx, best_action, _ = model.counterfactual.select_best_action(
        front_img, left_img, right_img, back_img, overhead_img,
        proprio, task_state, actions, criterion='reward'
    )
    print(f"[OK] Best action by reward: {action_labels[best_idx]} "
          f"(reward: {futures[best_idx]['pred_reward'].item():.4f})")

    # Test multi-step horizon
    print("\n[6] Testing multi-step counterfactual (horizon=5)...")
    futures_h5 = model.counterfactual.predict_futures(
        front_img, left_img, right_img, back_img, overhead_img,
        proprio, task_state, actions, horizon=5, decode_images=False
    )

    print(f"[OK] Generated {len(futures_h5)} futures with 5-step horizon")
    for i, future in enumerate(futures_h5):
        cumulative = future.get('cumulative_reward', 0)
        print(f"  {action_labels[i]}: cumulative_reward={cumulative:.4f}")

    # Test comparison summary
    print("\n[7] Generating action comparison summary...")
    summary = model.counterfactual.compare_actions_summary(futures, action_labels)
    print(summary)

    # Test visualization
    print("\n[8] Testing visualization...")
    save_dir = '/home/rlrk/IsaacLab/thread_isaac_lab/training_debug/counterfactual'
    model.counterfactual.visualize_futures(futures, save_dir, camera='front', action_labels=action_labels)

    print("\n" + "=" * 60)
    print("COUNTERFACTUAL GENERATION TEST COMPLETE")
    print("=" * 60)
    print(f"\nResults saved to: {save_dir}")


def test_with_real_data():
    """Test counterfactual generation with real dataset sample."""
    print("\n" + "=" * 60)
    print("Stage 3: Counterfactual Generation Test (Real Data)")
    print("=" * 60)

    # Check if data exists
    data_path = '/home/rlrk/IsaacLab/data/world_model_dual_arm_v2'
    if not os.path.exists(data_path):
        print(f"[SKIP] Data not found at {data_path}")
        return

    import h5py
    import io
    from PIL import Image
    import numpy as np

    def decompress_jpeg(jpeg_bytes):
        img = Image.open(io.BytesIO(bytes(jpeg_bytes)))
        return np.array(img)

    # Load model
    print("\n[1] Loading model...")
    config = WorldModelWithTaskConfig(
        use_transformer_dynamics=True,
        transformer_dynamics_layers=4,
    )
    model = WorldModelWithTask(config)

    checkpoint_path = '/home/rlrk/IsaacLab/checkpoints/world_model_v2_stage2/stage2_best.pt'
    ckpt = torch.load(checkpoint_path, map_location='cuda', weights_only=False)
    if 'model_state_dict' in ckpt:
        model.load_state_dict(ckpt['model_state_dict'])
    else:
        model.load_state_dict(ckpt)
    model = model.cuda()
    model.eval()
    print("[OK] Model loaded")

    # Load real sample
    print("\n[2] Loading real data sample...")
    import glob
    h5_files = sorted(glob.glob(os.path.join(data_path, '*.h5')))

    with h5py.File(h5_files[0], 'r') as f:
        idx = 100  # Sample index

        def load_img(key):
            img = decompress_jpeg(f[key][idx])
            img = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
            return img.unsqueeze(0).cuda()

        front_img = load_img('front_img_jpeg')
        left_img = load_img('left_img_jpeg')
        right_img = load_img('right_img_jpeg')
        back_img = load_img('back_img_jpeg')
        overhead_img = load_img('overhead_img_jpeg')

        proprio = torch.from_numpy(f['proprio'][idx]).float().unsqueeze(0).cuda()
        task_state = torch.from_numpy(f['task_state'][idx]).float().unsqueeze(0).cuda()
        real_action = torch.from_numpy(f['action'][idx]).float().unsqueeze(0).cuda()

    print("[OK] Loaded real sample")

    # Create action variations
    print("\n[3] Creating action variations...")
    actions = [
        real_action,                                # Original action
        real_action * 0.5,                          # Half intensity
        real_action * 2.0,                          # Double intensity
        -real_action,                               # Opposite direction
        torch.zeros_like(real_action),              # No action
    ]
    action_labels = ['original', 'half', 'double', 'opposite', 'idle']

    # Generate counterfactual predictions
    print("\n[4] Generating counterfactual predictions...")
    futures = model.counterfactual.predict_futures(
        front_img, left_img, right_img, back_img, overhead_img,
        proprio, task_state, actions, horizon=1, decode_images=True
    )

    # Display comparison
    print("\n[5] Action comparison:")
    summary = model.counterfactual.compare_actions_summary(futures, action_labels)
    print(summary)

    # Save visualization
    print("\n[6] Saving visualization...")
    save_dir = '/home/rlrk/IsaacLab/thread_isaac_lab/training_debug/counterfactual_real'
    model.counterfactual.visualize_futures(futures, save_dir, camera='front', action_labels=action_labels)
    model.counterfactual.visualize_futures(futures, save_dir, camera='overhead', action_labels=action_labels)

    print(f"\n[OK] Results saved to: {save_dir}")


if __name__ == '__main__':
    test_with_dummy_data()
    test_with_real_data()
