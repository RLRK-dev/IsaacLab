#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""BC-only pre-training for multi-task base model (45D unified).

Trains a standard ActorCritic actor (45->128->128->12) on mixed demos.
No skill labels -- backbone learns general features from obs alone.
Output: RSL-RL compatible checkpoint for use with --base-model in skill adapter pipeline.

All skills use 45D obs: AC/AR/Grip pad 42D→45D with zeros, IC natively 45D.
This enables unified frozen-base + LoRA adapter architecture across all skills.

Data balancing: each epoch samples min(N_per_skill) from each skill,
then shuffles the combined batch. This prevents larger datasets from dominating.

Supports 2-skill (AC+AR), 3-skill (AC+AR+IC), or 4-skill (AC+AR+IC+Grip) mode.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_base_model.py \
        --ac-demos thread_isaac_lab/data/bc_demos/grasp_cable_demos_v25_45d.npz \
        --ar-demos thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_v11_45d.npz \
        --ic-demos thread_isaac_lab/data/bc_demos/insert_clip_demos_v10_45d_approach.npz \
        --epochs 500 --device cuda:1
"""

import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from torch import optim


def main():
    parser = argparse.ArgumentParser(description="BC pre-training for multi-task base model")
    parser.add_argument("--ac-demos", type=str, required=True,
                        help="ApproachCable demo .npz (obs, actions)")
    parser.add_argument("--ar-demos", type=str, required=True,
                        help="AerialRegrasp demo .npz (obs, actions)")
    parser.add_argument("--ic-demos", type=str, default=None,
                        help="InsertIntoClip demo .npz (optional, 45D)")
    parser.add_argument("--grip-demos", type=str, default=None,
                        help="Grip clamp demo .npz (optional, 45D)")
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--device", type=str, default="cuda:1")
    parser.add_argument("--output", type=str, default=None,
                        help="Output checkpoint path (default: auto-generated)")
    parser.add_argument("--save-interval", type=int, default=100,
                        help="Save checkpoint every N epochs")
    args = parser.parse_args()

    device = args.device

    # Load demos (all must be 45D obs, 12D action)
    skill_data = {}
    demo_sources = [("AC", args.ac_demos), ("AR", args.ar_demos)]
    if args.ic_demos is not None:
        demo_sources.append(("IC", args.ic_demos))
    if args.grip_demos is not None:
        demo_sources.append(("Grip", args.grip_demos))
    for name, path in demo_sources:
        data = np.load(path)
        obs = torch.tensor(data["obs"], dtype=torch.float32, device=device)
        act = torch.tensor(data["actions"], dtype=torch.float32, device=device)
        # Action: allow 12D or 14D (Grip legacy); truncate to 12D
        if act.shape[1] == 14:
            act = act[:, :12]
            print(f"[BASE] {name}: truncated action 14D→12D (finger dims dropped)")
        assert obs.shape[1] == 45, f"{name} obs dim {obs.shape[1]} != 45 (use padded demos)"
        assert act.shape[1] == 12, f"{name} act dim {act.shape[1]} != 12"
        skill_data[name] = {"obs": obs, "act": act}
        print(f"[BASE] {name}: {obs.shape[0]} samples from {os.path.basename(path)}")

    # Balanced sampling count
    n_skills = len(skill_data)
    min_n = min(s["obs"].shape[0] for s in skill_data.values())
    total_per_epoch = min_n * n_skills
    print(f"[BASE] {n_skills} skills, balanced: {min_n}/skill/epoch = {total_per_epoch} total")

    # Build actor (same architecture as RSL-RL ActorCritic 128-128, now 45D input)
    actor = nn.Sequential(
        nn.Linear(45, 128), nn.ELU(),
        nn.Linear(128, 128), nn.ELU(),
        nn.Linear(128, 12),
    ).to(device)

    total_params = sum(p.numel() for p in actor.parameters())
    print(f"[BASE] Actor params: {total_params}")

    optimizer = optim.Adam(actor.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()

    # Output path
    if args.output is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.output = os.path.join(
            script_dir, "..", "data", f"base_model_mixed_{timestamp}.pt",
        )
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    print(f"[BASE] Training: {args.epochs} epochs, batch={args.batch_size}, lr={args.lr}")
    print(f"[BASE] Output: {args.output}")

    t0 = time.time()
    best_loss = float("inf")
    best_epoch = -1

    for epoch in range(args.epochs):
        # Balanced sampling: min_n from each skill, then shuffle
        all_obs = []
        all_act = []
        for s in skill_data.values():
            n = s["obs"].shape[0]
            idx = torch.randperm(n, device=device)[:min_n]
            all_obs.append(s["obs"][idx])
            all_act.append(s["act"][idx])

        obs = torch.cat(all_obs, dim=0)
        act = torch.cat(all_act, dim=0)
        perm = torch.randperm(obs.shape[0], device=device)
        obs = obs[perm]
        act = act[perm]

        # Mini-batch SGD
        epoch_loss = 0.0
        n_batches = 0
        for i in range(0, obs.shape[0], args.batch_size):
            batch_obs = obs[i:i + args.batch_size]
            batch_act = act[i:i + args.batch_size]

            pred = actor(batch_obs)
            loss = loss_fn(pred, batch_act)

            optimizer.zero_grad()
            loss.backward()
            if args.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(actor.parameters(), args.grad_clip)
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / n_batches

        # Save best
        if avg_loss < best_loss:
            best_loss = avg_loss
            best_epoch = epoch
            _save_checkpoint(actor, args.output)

        # Save interval
        if args.save_interval > 0 and (epoch + 1) % args.save_interval == 0:
            interval_path = args.output.replace(".pt", f"_ep{epoch + 1}.pt")
            _save_checkpoint(actor, interval_path)

        # Log
        if epoch % 50 == 0 or epoch == args.epochs - 1:
            skill_losses = _eval_per_skill(actor, skill_data, loss_fn)
            elapsed = time.time() - t0
            loss_str = " ".join(f"{k}={v:.4f}" for k, v in skill_losses.items())
            print(f"[BASE] ep={epoch:4d}/{args.epochs} loss={avg_loss:.6f} best={best_loss:.6f}@{best_epoch} "
                  f"{loss_str} [{elapsed:.0f}s]")

    elapsed = time.time() - t0

    # Final report
    skill_losses = _eval_per_skill(actor, skill_data, loss_fn)
    print(f"\n[BASE] Done in {elapsed:.1f}s. Best loss: {best_loss:.6f} @ epoch {best_epoch}")
    loss_str = " ".join(f"{k}={v:.6f}" for k, v in skill_losses.items())
    print(f"[BASE] Final per-skill: {loss_str}")
    print(f"[BASE] Saved: {args.output}")


def _save_checkpoint(actor: nn.Module, path: str):
    """Save in RSL-RL ActorCritic checkpoint format."""
    state_dict = {f"actor.{k}": v for k, v in actor.state_dict().items()}
    torch.save({"model_state_dict": state_dict}, path)


@torch.no_grad()
def _eval_per_skill(actor, skill_data, loss_fn):
    """Evaluate loss per skill on full dataset."""
    actor.eval()
    result = {}
    for name, s in skill_data.items():
        pred = actor(s["obs"])
        result[name] = loss_fn(pred, s["act"]).item()
    actor.train()
    return result


if __name__ == "__main__":
    main()
