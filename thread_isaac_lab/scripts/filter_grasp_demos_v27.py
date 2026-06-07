# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Filter ApproachCable BC demos — quality gate + sustained-hover cut.

Accepts variable-length episodes via episode_lengths array in npz.

Filter logic:
  1. Quality gate: d_min = min(max(d_r, d_l)) <= QUALITY_THRESH (5mm).
  2. Approach completion gate: first near-min frame within INCOMPLETE_GAP
     frames of first zero-action frame.
  3. Sustained near-min run: contiguous frames where d_max <= d_min + TOL,
     keep only runs >= K_GRASP frames. Cut at longest run end + 1.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "configs"))

from task_config import K_GRASP  # SSOT: task_config.py:162

QUALITY_THRESH = 0.005  # 5mm: d_min must be <= this (grasp success proxy)
TOL = 0.005  # 5mm: near-min tolerance window
INCOMPLETE_GAP = 5  # Max allowed frames between first_near_min and first_zero_action
ZERO_ACTION_THRESH = 0.01  # ||action|| below this is treated as zero


def filter_episode(ep_obs: np.ndarray, ep_acts: np.ndarray) -> tuple[int | None, str]:
    """Compute cut index for an episode, or return None with exclusion reason.

    Args:
        ep_obs: Episode observations, shape (T, 42).
        ep_acts: Episode actions, shape (T, 12).

    Returns:
        (cut_index, 'ok') if episode is kept (keep frames [0..cut_index)).
        (None, reason_str) if episode is excluded.
    """
    d_r = np.linalg.norm(ep_obs[:, 33:36], axis=1)
    d_l = np.linalg.norm(ep_obs[:, 39:42], axis=1)
    d_max = np.maximum(d_r, d_l)
    d_min = float(d_max.min())

    if d_min > QUALITY_THRESH:
        return None, f"quality_fail(d_min={d_min * 1000:.2f}mm)"

    act_norms = np.linalg.norm(ep_acts, axis=1)
    zero_action = act_norms < ZERO_ACTION_THRESH
    near_min = d_max <= (d_min + TOL)

    if not near_min.any():
        return None, "never_near_min"

    first_near = int(np.argmax(near_min))
    first_zero = int(np.argmax(zero_action)) if zero_action.any() else len(d_max)

    if first_near - first_zero > INCOMPLETE_GAP:
        return None, (
            f"approach_incomplete(first_near={first_near},first_zero={first_zero})"
        )

    runs: list[tuple[int, int]] = []
    in_run = False
    run_start = 0
    for t in range(len(near_min)):
        if near_min[t] and not in_run:
            run_start = t
            in_run = True
        elif not near_min[t] and in_run:
            runs.append((run_start, t - 1))
            in_run = False
    if in_run:
        runs.append((run_start, len(near_min) - 1))

    sustained = [(s, e) for s, e in runs if (e - s + 1) >= K_GRASP]
    if not sustained:
        return None, f"no_sustained_hover(runs={runs})"

    best_start, best_end = max(sustained, key=lambda r: r[1] - r[0])
    return best_end + 1, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="thread_isaac_lab/data/bc_demos/approach_cable_demos_v6.npz",
        help="Input demo npz path (must contain episode_lengths)",
    )
    parser.add_argument(
        "--output",
        default="thread_isaac_lab/data/bc_demos/approach_cable_demos_v6_filtered.npz",
        help="Output filtered demo npz path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print filter summary without writing output",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] Input not found: {args.input}")
        return 1

    data = np.load(args.input, allow_pickle=False)
    obs = data["obs"]
    acts = data["actions"]
    total_tr = obs.shape[0]

    if "episode_lengths" not in data:
        print("[ERROR] Input npz missing 'episode_lengths' array")
        return 1
    ep_lengths = data["episode_lengths"].astype(int)
    n_eps = len(ep_lengths)
    if n_eps == 0:
        print("[ERROR] No episodes in input")
        return 1
    if ep_lengths.sum() != total_tr:
        print(f"[ERROR] episode_lengths sum {ep_lengths.sum()} != total transitions {total_tr}")
        return 1

    print(f"[INFO] Input: {args.input}")
    print(f"[INFO] obs shape: {obs.shape}, actions shape: {acts.shape}")
    print(f"[INFO] Episodes: {n_eps} (variable length, range {ep_lengths.min()}-{ep_lengths.max()})")
    print()

    kept_obs_list: list[np.ndarray] = []
    kept_act_list: list[np.ndarray] = []
    kept_ep_ids: list[int] = []
    excluded: dict[int, str] = {}
    per_ep_kept_tr: list[int] = []

    print("ep | len | cut | kept | reason")
    print("-" * 70)
    offset = 0
    for ep in range(n_eps):
        ep_len = int(ep_lengths[ep])
        ep_obs = obs[offset : offset + ep_len]
        ep_acts = acts[offset : offset + ep_len]
        offset += ep_len
        cut, reason = filter_episode(ep_obs, ep_acts)
        if cut is None:
            excluded[ep] = reason
            print(f"{ep:2d} | {ep_len:3d} |  -- | --   | EXCLUDE: {reason}")
        else:
            kept_obs_list.append(ep_obs[:cut])
            kept_act_list.append(ep_acts[:cut])
            kept_ep_ids.append(ep)
            per_ep_kept_tr.append(cut)
            print(f"{ep:2d} | {ep_len:3d} | {cut:3d} | {cut:3d}  | ok")

    print()
    total_kept_tr = sum(per_ep_kept_tr)
    print(f"[SUMMARY] Kept: {len(kept_ep_ids)} / {n_eps} eps")
    print(f"[SUMMARY] Kept: {total_kept_tr} / {total_tr} tr ({total_kept_tr / total_tr * 100:.1f}%)")
    print(f"[SUMMARY] Excluded: {sorted(excluded.keys())}")
    for ep, reason in sorted(excluded.items()):
        print(f"           ep{ep}: {reason}")

    if args.dry_run:
        print("\n[DRY-RUN] No output written.")
        return 0

    filtered_obs = np.concatenate(kept_obs_list, axis=0).astype(np.float32)
    filtered_acts = np.concatenate(kept_act_list, axis=0).astype(np.float32)

    metadata = {
        "source": os.path.basename(args.input),
        "kept_ep_ids": np.array(kept_ep_ids, dtype=np.int32),
        "excluded_ep_ids": np.array(sorted(excluded.keys()), dtype=np.int32),
        "excluded_reasons": np.array([excluded[e] for e in sorted(excluded.keys())], dtype="U1024"),
        "per_ep_kept_tr": np.array(per_ep_kept_tr, dtype=np.int32),
        "cut_method": "longest_sustained_near_min_run",
        "quality_thresh_m": QUALITY_THRESH,
        "tol_m": TOL,
        "k_grasp": K_GRASP,
        "incomplete_gap": INCOMPLETE_GAP,
        "original_tr": total_tr,
        "kept_tr": total_kept_tr,
        "original_eps": n_eps,
        "kept_eps": len(kept_ep_ids),
    }

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    np.savez(
        args.output,
        obs=filtered_obs,
        actions=filtered_acts,
        episode_lengths=np.array(per_ep_kept_tr, dtype=np.int32),
        **metadata,
    )
    print(f"\n[OK] Wrote: {args.output}")
    print(f"     obs: {filtered_obs.shape}, actions: {filtered_acts.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
