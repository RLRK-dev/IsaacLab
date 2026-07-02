# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""B1 trainer wrapper (B_BC_BUILD_SPEC.md §3): REUSE ``bc_pretrain.py`` on the converted route demo.

``build_actor_critic(25, 6, (128,128)) -> train_bc(MSE on the actor MEAN, bc_pretrain.py:103) ->
save_bc_checkpoint`` (RSL-RL format = PPO-fine-tune compatible). Emits ``policy.pt`` + ``loss_curve.json``
(the §9-B1 loss-curve artifact). Inference is deterministic actor-mean ONLY (see policy_route_runner
--policy). Run on GPU by the parent; this file is code-only (no auto-run here).
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
    ap.add_argument("--dataset", required=True, help="bc_dataset[_abs].npz (obs[770,25], actions[770,6], meta)")
    ap.add_argument("--out-dir", required=True, help="output dir for policy[_abs].pt + loss_curve.json + sidecar")
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

    # dataset action_repr (sidecar provenance; the runner asserts sidecar repr == its --policy-absolute mode)
    with np.load(args.dataset, allow_pickle=True) as z:
        action_repr = json.loads(str(z["meta"])).get("action_repr", "delta") if "meta" in z.files else "delta"

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    policy = build_actor_critic(25, 6, (128, 128), args.device)  # §3: obs 25D / act 6D / (128,128)
    t0 = time.time()
    # train_bc loads dataset["obs"]/["actions"] (bc_pretrain.py:66-68), MSE on policy.actor mean (:103),
    # and RETURNS history={"train_loss":[...],"val_loss":[...]} (:94/:135) -> the §9-B1 loss curve.
    history = train_bc(policy, args.dataset, epochs=args.epochs, batch_size=256, lr=1e-3, device=args.device)
    elapsed = time.time() - t0

    curve = [
        {"epoch": i + 1, "loss": float(tl), "val_loss": float(vl)}
        for i, (tl, vl) in enumerate(zip(history["train_loss"], history["val_loss"]))
    ]
    (out / "loss_curve.json").write_text(json.dumps(curve, indent=2))
    ckpt_name = f"policy_abs{args.tag}.pt" if action_repr == "abs" else f"policy{args.tag}.pt"
    ckpt_path = out / ckpt_name
    save_bc_checkpoint(policy, str(ckpt_path))  # {"model_state_dict",...} RSL-RL fmt (:143-149)

    sidecar = {
        "ckpt_sha256": _sha256_file(str(ckpt_path)),
        "dataset_sha256": _sha256_file(args.dataset),
        "action_repr": action_repr,  # E15: runner asserts sidecar repr == mode
        "seed": args.seed,
        "epochs": args.epochs,
        "batch_size": 256,
        "lr": 1e-3,
        "device": args.device,
        "elapsed_s": round(elapsed, 1),
        "final_train_loss": float(history["train_loss"][-1]),
        "final_val_loss": float(history["val_loss"][-1]),
    }
    (out / f"{ckpt_path.stem}_sidecar.json").write_text(json.dumps(sidecar, indent=2))

    print(
        f"[bc_train_route] repr={action_repr} seed={args.seed} epochs={args.epochs} "
        f"final train_loss={history['train_loss'][-1]:.6f} val_loss={history['val_loss'][-1]:.6f} "
        f"elapsed={elapsed:.0f}s -> {ckpt_path}"
    )


if __name__ == "__main__":
    main()
