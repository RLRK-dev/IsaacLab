# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Convert MPPI HDF5 AC demos to npz for DAPG BC (Option B: α-2 replay).

Strategy
--------
1. Load PASS episodes from one or more M3-AC HDF5 files (R-first action layout).
2. Instantiate NewtonApproachCableEnv(world_count=1) and override POS/ROT action
   scales to match MPPI (pos=0.03, rot=0.15) so the env-side scaling matches the
   MPPI training-time scaling.
3. For each episode:
   a. Reset env (restores P0 precondition cache).
   b. Per step t:
      - Record env obs BEFORE applying action (pre-action state).
      - Apply HDF5 action_delta[t] (already R-first, raw [-0.3, 0.3] range).
      - If env reports done, break (env may terminate early due to success or
        collision, in which case we stop recording this episode).
4. Aggregate all (obs, action) pairs, save npz with schema matching existing
   `aerial_regrasp_demos_v14_45d.npz`: {obs, actions, episode_lengths,
   episode_success, source}.

Why replay (α-2) over direct compute (α-4)
------------------------------------------
- Direct compute uses HDF5 body[6] + quat_rotate([0,0,+EE_TO_FINGERTIP]) to fake
  env's clamp pose. However MPPI's cost minimizes body[6]↔cable-endpoint, so
  body[6] reaches cable level at "success" → reconstructed clamp is ~22cm below
  cable (geometrically invalid).
- Replay captures env-side obs that is physically consistent with env's actual
  state, even if trajectory diverges from MPPI's. BC + PPO can still extract
  useful action signal.

Usage
-----
    CUDA_VISIBLE_DEVICES=0 \
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/convert_mppi_demos_to_npz.py \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s342_n15_p3/demos_default.hdf5 \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s42_p3/demos_default.hdf5 \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s142_p3/demos_default.hdf5 \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s242_p3/demos_default.hdf5 \
        --output thread_isaac_lab/data/bc_demos/approach_cable_demos_mppi_v1.npz \
        --skill ac --device cuda:0
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_D, "..", "envs"))
sys.path.insert(0, os.path.join(_D, "..", "configs"))
sys.path.insert(0, _D)


@dataclass
class EpisodeData:
    key: str  # "{basename}/episode_N"
    actions: np.ndarray  # (T, 12) R-first float32
    hdf5_ee_pos_r: np.ndarray  # (T, 3) — MPPI reference trajectory
    hdf5_ee_pos_l: np.ndarray
    success_mppi: bool
    steps: int


def load_pass_episodes(hdf5_paths: list[str]) -> list[EpisodeData]:
    """Load SUCCESS episodes from HDF5 file(s). Verify R-first layout."""
    out = []
    for p in hdf5_paths:
        with h5py.File(p, "r") as f:
            layout = f["metadata"].attrs["action_layout"]
            if layout != "R-first":
                raise ValueError(f"{p}: action_layout={layout} (expected R-first)")
            ep_keys = sorted(
                [k for k in f.keys() if k.startswith("episode_")],
                key=lambda s: int(s.split("_")[1]),
            )
            base = os.path.basename(os.path.dirname(p))
            for k in ep_keys:
                g = f[k]
                if not bool(g.attrs.get("success", False)):
                    continue
                out.append(
                    EpisodeData(
                        key=f"{base}/{k}",
                        actions=g["action_delta"][()].astype(np.float32),
                        hdf5_ee_pos_r=g["right_ee_pos"][()].astype(np.float32),
                        hdf5_ee_pos_l=g["left_ee_pos"][()].astype(np.float32),
                        success_mppi=True,
                        steps=int(g.attrs.get("steps", g["action_delta"].shape[0])),
                    )
                )
    return out


def replay_one_episode(env, torch_mod, actions: np.ndarray, max_steps: int) -> tuple[np.ndarray, np.ndarray, dict]:
    """Reset env, replay actions, return (obs_arr, act_arr, diagnostics).

    - Records env obs BEFORE each env.step (pre-action state).
    - Stops if env returns done=True or at max_steps.
    - Pairs: (obs[t], action[t]) for t in [0, T_recorded-1].

    Returns:
        obs_arr: (T_recorded, 45) float32 — env obs
        act_arr: (T_recorded, 12) float32 — actions consumed
        diagnostics: dict with trajectory statistics
    """
    # Reset env (single world)
    env._reset_worlds([0])
    env.episode_length_buf[0] = 0
    # Clear last actions to avoid stale r_hold term
    env._last_actions = None
    # Reset per-world tracking to fresh state
    env._step_completed_right[0] = False
    env._success_sustain_count[0] = 0

    T = min(len(actions), max_steps)
    obs_list = np.zeros((T, 45), dtype=np.float32)
    act_list = np.zeros((T, 12), dtype=np.float32)
    clamp_r_trace = np.zeros((T, 3), dtype=np.float32)
    pos_err_r_mag = np.zeros(T, dtype=np.float32)
    done_step = T  # if never done, we record all steps
    for t in range(T):
        obs = env._compute_obs_batch()  # (1, 45)
        obs_np = obs[0].detach().cpu().numpy().astype(np.float32).copy()
        obs_list[t] = obs_np
        clamp_r_trace[t] = obs_np[0:3]
        pos_err_r_mag[t] = float(np.linalg.norm(obs_np[33:36]))
        act_np = actions[t].astype(np.float32).copy()
        act_list[t] = act_np
        act_t = torch_mod.tensor(act_np, dtype=torch_mod.float32, device=env.device).unsqueeze(0)
        _, _, dones, _ = env.step(act_t)
        if bool(dones[0].item()):
            done_step = t + 1  # recorded through step t (inclusive)
            break
    obs_arr = obs_list[:done_step]
    act_arr = act_list[:done_step]
    diag = {
        "T_recorded": done_step,
        "T_hdf5": len(actions),
        "clamp_r_z_start": float(clamp_r_trace[0, 2]) if done_step > 0 else None,
        "clamp_r_z_end": float(clamp_r_trace[done_step - 1, 2]) if done_step > 0 else None,
        "pos_err_r_start_mm": float(pos_err_r_mag[0] * 1000) if done_step > 0 else None,
        "pos_err_r_end_mm": float(pos_err_r_mag[done_step - 1] * 1000) if done_step > 0 else None,
        "early_done": done_step < T,
    }
    return obs_arr, act_arr, diag


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=str, action="append", required=True, help="HDF5 path; repeat for multiple files")
    ap.add_argument("--output", type=str, required=True, help="Output npz path")
    ap.add_argument("--skill", type=str, choices=["ac"], default="ac")
    ap.add_argument("--device", type=str, default="cuda:0")
    ap.add_argument(
        "--max-steps-per-ep", type=int, default=300, help="Upper bound per episode (should exceed MPPI max_steps=160)"
    )
    ap.add_argument(
        "--pos-action-scale", type=float, default=0.03, help="Override env POS_ACTION_SCALE (match MPPI metadata)"
    )
    ap.add_argument(
        "--rot-action-scale", type=float, default=0.15, help="Override env ROT_ACTION_SCALE (match MPPI metadata)"
    )
    ap.add_argument("--dry-run", action="store_true", help="Load episodes + instantiate env, but don't replay/save")
    ap.add_argument("--first-n", type=int, default=None, help="Debug: only replay first N episodes")
    args = ap.parse_args()

    # Load episodes first (fast, no env dep)
    print("[REPLAY] Loading HDF5 input(s)...")
    episodes = load_pass_episodes(args.input)
    if args.first_n is not None:
        episodes = episodes[: args.first_n]
    print(f"[REPLAY] {len(episodes)} PASS episodes loaded from {len(args.input)} HDF5")
    for ep in episodes:
        print(f"  - {ep.key}: T={len(ep.actions)}")

    if args.dry_run:
        print("[REPLAY] --dry-run: skipping env instantiation and replay")
        return

    # Instantiate env
    import torch
    import warp as wp

    wp.init()
    print(f"[REPLAY] Instantiating NewtonApproachCableEnv(world_count=1, device={args.device})...")
    t0 = time.time()
    from newton_approach_cable_env import NewtonApproachCableEnv

    env = NewtonApproachCableEnv(world_count=1, device=args.device)
    print(f"[REPLAY] Env instantiated in {time.time() - t0:.1f}s")

    # Override action scales to match MPPI
    env.POS_ACTION_SCALE = args.pos_action_scale
    env.ROT_ACTION_SCALE = args.rot_action_scale
    # Disable adaptive pos scale (keep MPPI's fixed scale)
    if hasattr(env, "ADAPTIVE_POS_SCALE"):
        env.ADAPTIVE_POS_SCALE = False
    # Set high terminal step limit (avoid env timeout during replay)
    env.TERMINAL_STEPS_OVERRIDE = args.max_steps_per_ep + 50
    print(
        f"[REPLAY] scales: pos={env.POS_ACTION_SCALE}, rot={env.ROT_ACTION_SCALE}, "
        f"max_steps={env.TERMINAL_STEPS_OVERRIDE}"
    )

    # Replay loop
    all_obs, all_acts, ep_lens, ep_success_mppi, diags = [], [], [], [], []
    t0 = time.time()
    for ep_idx, ep in enumerate(episodes):
        t_ep = time.time()
        obs_ep, act_ep, diag = replay_one_episode(env, torch, ep.actions, args.max_steps_per_ep)
        ep_time = time.time() - t_ep
        print(
            f"[REPLAY] {ep_idx + 1}/{len(episodes)} {ep.key}: "
            f"T_rec={diag['T_recorded']}/{diag['T_hdf5']} "
            f"early_done={diag['early_done']} "
            f"clamp_z {diag['clamp_r_z_start']:.3f}→{diag['clamp_r_z_end']:.3f} "
            f"pos_err_r {diag['pos_err_r_start_mm']:.1f}→{diag['pos_err_r_end_mm']:.1f} mm "
            f"({ep_time:.1f}s)"
        )
        if len(obs_ep) > 0:
            all_obs.append(obs_ep)
            all_acts.append(act_ep)
            ep_lens.append(diag["T_recorded"])
            ep_success_mppi.append(ep.success_mppi)
            diags.append(diag)
    total_time = time.time() - t0
    print(
        f"[REPLAY] All {len(episodes)} episodes replayed in {total_time:.1f}s "
        f"(avg {total_time / max(1, len(episodes)):.2f}s/episode)"
    )

    if not all_obs:
        print("[REPLAY] ERROR: no episodes recorded (all zero-length)", file=sys.stderr)
        sys.exit(1)

    obs_all = np.concatenate(all_obs, axis=0)
    act_all = np.concatenate(all_acts, axis=0)
    ep_lens_arr = np.array(ep_lens, dtype=np.int64)

    # Validation diagnostics
    total = obs_all.shape[0]
    act_sat = float(np.mean(np.abs(act_all) > 0.99))
    r_rms = float(np.sqrt(np.mean(act_all[:, 0:6] ** 2)))
    l_rms = float(np.sqrt(np.mean(act_all[:, 6:12] ** 2)))
    obs_mean = obs_all.mean(axis=0)
    obs_std = obs_all.std(axis=0)
    print("\n=== VALIDATION ===")
    print(f"  total transitions: {total}")
    print(f"  episodes kept: {len(ep_lens)}")
    print(f"  obs shape: {obs_all.shape}  act shape: {act_all.shape}")
    print(f"  action saturation (|a|>0.99): {act_sat:.3%}")
    print(f"  R-arm action RMS: {r_rms:.3f}  L-arm action RMS: {l_rms:.3f}")
    print(f"  obs[0] (clamp_r_x) mean/std: {obs_mean[0]:.3f} / {obs_std[0]:.3f}")
    print(f"  obs[2] (clamp_r_z) mean/std: {obs_mean[2]:.3f} / {obs_std[2]:.3f}")
    print(f"  obs[23] (clip_x) mean/std: {obs_mean[23]:.3f} / {obs_std[23]:.3f}")
    print(
        f"  obs[33:36] pos_err_r mean magnitude: "
        f"{np.linalg.norm(obs_mean[33:36]):.4f} m  "
        f"(std {np.linalg.norm(obs_std[33:36]):.4f} m)"
    )

    # Save npz
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        str(out_path),
        obs=obs_all.astype(np.float32),
        actions=act_all.astype(np.float32),
        episode_lengths=ep_lens_arr,
        episode_success_mppi=np.array(ep_success_mppi, dtype=bool),
        source=f"m3_ac_replay_v1 (strategy=α-2 replay, pos_scale={args.pos_action_scale}, "
        f"rot_scale={args.rot_action_scale})",
    )
    print(f"\n[REPLAY] Saved → {out_path}")


if __name__ == "__main__":
    main()
