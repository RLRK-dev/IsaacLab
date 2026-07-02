# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""B1 trainer wrapper (B_BC_BUILD_SPEC.md §3): REUSE ``bc_pretrain.py`` on the converted route demo.

``build_actor_critic(obs_dim, 6, (128,128)) -> train_bc(MSE on the actor MEAN, bc_pretrain.py:103) ->
save_bc_checkpoint`` (RSL-RL format = PPO-fine-tune compatible). Emits ``policy.pt`` + ``loss_curve.json``
(the §9-B1 loss-curve artifact). Inference is deterministic actor-mean ONLY (see policy_route_runner
--policy). Run on GPU by the parent; this file is code-only (no auto-run here).

``obs_dim`` is read from the dataset meta (25 for 13-phase v1, 27 for 15-phase v2; default 25 for
back-compat) so the trainer is schema-aware. ``bc_pretrain.train_bc`` does a RANDOM-ROW val split (an
internal training-progress PROXY); spec §3.1 requires a WHOLE-DEMO holdout, so an optional
``--val-dataset`` (the ``bc_dataset_abs_val.npz`` whole demos) is scored post-training as the
AUTHORITATIVE val loss WITHOUT touching the locked bc_pretrain.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def _sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="B1/B1' BC trainer wrapper (spec §3/E15) -> policy[_abs].pt + loss_curve")
    ap.add_argument("--dataset", required=True, help="bc_dataset[_abs].npz (obs[N,obs_dim], actions[N,6], meta)")
    ap.add_argument("--out-dir", required=True, help="output dir for policy[_abs].pt + loss_curve.json + sidecar")
    ap.add_argument(
        "--val-dataset",
        default=None,
        help="B2 (spec §3.1): whole-demo holdout npz (e.g. bc_dataset_abs_val.npz) scored post-training as the "
        "AUTHORITATIVE val; if absent, behaves as before (train_bc internal random-row proxy only)",
    )
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)  # E15 CP2: PIN the RNG (B1 was unseeded); recorded in sidecar
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--tag", default="", help="ckpt-name suffix, e.g. _e2000 for the E15 convergence-extension")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import random

    import numpy as np
    import torch
    from bc_pretrain import build_actor_critic, save_bc_checkpoint, train_bc  # REUSE (§3)

    # E15 CP2: PIN all RNG seeds BEFORE network init/training (B1 was unseeded -> non-reproducible init)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    # dataset action_repr + obs_dim (sidecar provenance; runner asserts sidecar repr == its --policy-absolute mode)
    with np.load(args.dataset, allow_pickle=True) as z:
        _meta = json.loads(str(z["meta"])) if "meta" in z.files else {}
    action_repr = _meta.get("action_repr", "delta")
    obs_dim = int(_meta.get("obs_dim", 25))  # schema-aware: 25 (13-phase v1) / 27 (15-phase v2); default 25

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    policy = build_actor_critic(obs_dim, 6, (128, 128), args.device)  # §3: obs {obs_dim}D / act 6D / (128,128)
    t0 = time.time()
    # train_bc loads dataset["obs"]/["actions"] (bc_pretrain.py:66-68), MSE on policy.actor mean (:103),
    # and RETURNS history={"train_loss":[...],"val_loss":[...]} (:94/:135) -> the §9-B1 loss curve.
    history = train_bc(policy, args.dataset, epochs=args.epochs, batch_size=256, lr=1e-3, device=args.device)
    elapsed = time.time() - t0

    # --- spec §3.1: WHOLE-DEMO holdout val (AUTHORITATIVE), scored post-training on --val-dataset ---
    # train_bc's per-epoch val_loss is an INTERNAL random-row PROXY on the training demos (bc_pretrain is
    # LOCKED); the whole-demo holdout is the real generalization signal. Same MSE-on-actor-mean metric as
    # train_bc (bc_pretrain.py:103), so the two numbers are directly comparable.
    proxy_final_val = float(history["val_loss"][-1])
    whole_demo_val_loss = None
    val_dataset_sha = None
    if args.val_dataset:
        with np.load(args.val_dataset, allow_pickle=True) as vz:
            v_obs = torch.tensor(vz["obs"], dtype=torch.float32, device=args.device)
            v_act = torch.tensor(vz["actions"], dtype=torch.float32, device=args.device)
        policy.eval()
        with torch.no_grad():
            whole_demo_val_loss = float(torch.nn.functional.mse_loss(policy.actor(v_obs), v_act).item())
        val_dataset_sha = _sha256_file(args.val_dataset)

    curve = [
        {"epoch": i + 1, "loss": float(tl), "val_loss": float(vl)}
        for i, (tl, vl) in enumerate(zip(history["train_loss"], history["val_loss"]))
    ]
    if whole_demo_val_loss is not None:  # append the AUTHORITATIVE whole-demo val as the final record
        curve.append(
            {
                "epoch": "whole_demo_val",
                "whole_demo_val_loss": whole_demo_val_loss,
                "note": (
                    "AUTHORITATIVE whole-demo holdout val (spec §3.1); the per-epoch val_loss above is the "
                    "train_bc internal random-row PROXY on the training demos, NOT a generalization signal"
                ),
            }
        )
    (out / "loss_curve.json").write_text(json.dumps(curve, indent=2))
    ckpt_name = f"policy_abs{args.tag}.pt" if action_repr == "abs" else f"policy{args.tag}.pt"
    ckpt_path = out / ckpt_name
    save_bc_checkpoint(policy, str(ckpt_path))  # {"model_state_dict",...} RSL-RL fmt (:143-149)

    sidecar = {
        "ckpt_sha256": _sha256_file(str(ckpt_path)),
        "dataset_sha256": _sha256_file(args.dataset),
        "action_repr": action_repr,  # E15: runner asserts sidecar repr == mode
        "obs_dim": obs_dim,  # schema-aware (25 v1 / 27 v2)
        "seed": args.seed,
        "epochs": args.epochs,
        "batch_size": 256,
        "lr": 1e-3,
        "device": args.device,
        "elapsed_s": round(elapsed, 1),
        "final_train_loss": float(history["train_loss"][-1]),
        "final_val_loss": proxy_final_val,  # PROXY: train_bc internal random-row split (kept for back-compat)
        "final_val_loss_note": "internal random-row PROXY (train_bc); see whole_demo_val_loss for spec §3.1 holdout",
        "whole_demo_val_loss": whole_demo_val_loss,  # AUTHORITATIVE spec §3.1 (None if no --val-dataset)
        "val_dataset": args.val_dataset,
        "val_dataset_sha256": val_dataset_sha,
    }
    (out / f"{ckpt_path.stem}_sidecar.json").write_text(json.dumps(sidecar, indent=2))

    _wd = f"{whole_demo_val_loss:.6f}" if whole_demo_val_loss is not None else "N/A(no --val-dataset)"
    print(
        f"[bc_train_route] repr={action_repr} obs_dim={obs_dim} seed={args.seed} epochs={args.epochs} "
        f"final train_loss={history['train_loss'][-1]:.6f} val_loss(proxy,random-row)={proxy_final_val:.6f} "
        f"whole_demo_val_loss(§3.1 authoritative)={_wd} elapsed={elapsed:.0f}s -> {ckpt_path}"
    )


if __name__ == "__main__":
    main()
