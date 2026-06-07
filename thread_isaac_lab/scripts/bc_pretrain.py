# Copyright (c) 2024, THREAD Project
# SPDX-License-Identifier: BSD-3-Clause

"""Behavioral Cloning (BC) pretraining for RL policies.

Trains an ActorCritic MLP on expert demonstrations, then saves weights
in RSL-RL checkpoint format for fine-tuning with PPO.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/bc_pretrain.py \
        --demos data/bc_demos/insert_clip_demos.npz \
        --output data/bc_checkpoints/insert_clip_bc.pt \
        --epochs 100 --device cuda:0
"""

import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def build_actor_critic(obs_dim, act_dim, hidden_dims=(128, 128), device="cuda:0"):
    """Build RSL-RL ActorCritic model for BC pretraining."""
    try:
        from rsl_rl.modules import ActorCritic
    except ImportError:
        print("[BC] ERROR: rsl_rl not installed")
        sys.exit(1)

    policy = ActorCritic(
        num_actor_obs=obs_dim,
        num_critic_obs=obs_dim,
        num_actions=act_dim,
        actor_hidden_dims=list(hidden_dims),
        critic_hidden_dims=list(hidden_dims),
        activation="elu",
        init_noise_std=0.1,  # low noise for BC-pretrained policy
    ).to(device)

    return policy


def train_bc(policy, demos_path, epochs=100, batch_size=256, lr=1e-3,
             val_split=0.1, device="cuda:0"):
    """Train policy with behavioral cloning (MSE on actor mean).

    Args:
        policy: ActorCritic model.
        demos_path: path to .npz with 'obs' and 'actions'.
        epochs: training epochs.
        batch_size: mini-batch size.
        lr: learning rate.
        val_split: fraction for validation.
        device: torch device.

    Returns:
        dict with training history.
    """
    # Load demos
    data = np.load(demos_path)
    obs_all = torch.tensor(data["obs"], dtype=torch.float32, device=device)
    act_all = torch.tensor(data["actions"], dtype=torch.float32, device=device)

    print(f"[BC] Loaded {obs_all.shape[0]} transitions from {demos_path}")
    print(f"[BC] obs: {obs_all.shape}, actions: {act_all.shape}")

    # Train/val split
    n = obs_all.shape[0]
    n_val = max(int(n * val_split), 1)
    n_train = n - n_val

    perm = torch.randperm(n, device=device)
    train_idx, val_idx = perm[:n_train], perm[n_train:]

    train_ds = TensorDataset(obs_all[train_idx], act_all[train_idx])
    val_ds = TensorDataset(obs_all[val_idx], act_all[val_idx])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    print(f"[BC] Train: {n_train}, Val: {n_val}, Batch: {batch_size}")

    # Optimizer — only actor parameters (critic will be trained by PPO)
    actor_params = list(policy.actor.parameters())
    optimizer = torch.optim.Adam(actor_params, lr=lr)
    loss_fn = nn.MSELoss()

    history = {"train_loss": [], "val_loss": []}

    for epoch in range(epochs):
        # Train
        policy.train()
        train_loss_sum = 0.0
        train_count = 0
        for obs_batch, act_batch in train_loader:
            # Forward through actor only (get mean action)
            action_mean = policy.actor(obs_batch)
            loss = loss_fn(action_mean, act_batch)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss_sum += loss.item() * obs_batch.shape[0]
            train_count += obs_batch.shape[0]

        train_loss = train_loss_sum / train_count

        # Validation
        policy.eval()
        val_loss_sum = 0.0
        val_count = 0
        with torch.no_grad():
            for obs_batch, act_batch in val_loader:
                action_mean = policy.actor(obs_batch)
                loss = loss_fn(action_mean, act_batch)
                val_loss_sum += loss.item() * obs_batch.shape[0]
                val_count += obs_batch.shape[0]

        val_loss = val_loss_sum / val_count

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"[BC] Epoch {epoch+1}/{epochs}: "
                  f"train_loss={train_loss:.6f}, val_loss={val_loss:.6f}")

    return history


def save_bc_checkpoint(policy, path):
    """Save BC-pretrained weights in RSL-RL checkpoint format.

    Only saves model_state_dict (no optimizer — PPO will create its own).
    """
    saved_dict = {
        "model_state_dict": policy.state_dict(),
        "iter": 0,
        "infos": {"bc_pretrained": True},
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(saved_dict, path)
    print(f"[BC] Checkpoint saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="BC pretrain for RL")
    parser.add_argument("--demos", type=str, required=True,
                        help="Path to expert demos .npz")
    parser.add_argument("--output", type=str, default=None,
                        help="Output checkpoint path")
    parser.add_argument("--obs-dim", type=int, default=12)
    parser.add_argument("--act-dim", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", type=str, default="cuda:0")
    args = parser.parse_args()

    if args.output is None:
        base = os.path.splitext(os.path.basename(args.demos))[0]
        args.output = os.path.join(
            os.path.dirname(args.demos), "..", "bc_checkpoints",
            f"{base}_bc.pt")

    print(f"[BC] Demos: {args.demos}")
    print(f"[BC] Output: {args.output}")
    print(f"[BC] obs_dim={args.obs_dim}, act_dim={args.act_dim}")
    print(f"[BC] epochs={args.epochs}, batch_size={args.batch_size}, lr={args.lr}")

    # Build model
    policy = build_actor_critic(
        args.obs_dim, args.act_dim, device=args.device)
    print(f"[BC] Actor: {policy.actor}")

    # Train
    t0 = time.time()
    history = train_bc(
        policy, args.demos,
        epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
        device=args.device,
    )
    elapsed = time.time() - t0

    print(f"\n[BC] Training complete in {elapsed:.0f}s")
    print(f"[BC] Final train_loss={history['train_loss'][-1]:.6f}, "
          f"val_loss={history['val_loss'][-1]:.6f}")

    # Save
    save_bc_checkpoint(policy, args.output)


if __name__ == "__main__":
    main()
