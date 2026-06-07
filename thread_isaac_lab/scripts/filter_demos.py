#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Best-of-N demo filter for DAPG training.

Reads a raw demo npz produced by collect_{grip,approach_cable,insert_clip}_demos.py,
scores each episode by a per-channel weighted L1 over the entire commanded action
trajectory plus an optional step-count penalty, then writes a filtered npz
containing only the best-k episodes.

Score (lower = better):
    motion = W_POS * Σ|dpos_R| + W_POS * Σ|dpos_L|
           + W_ROT * Σ|drot_R| + W_ROT * Σ|drot_L|
           + W_GRIP * Σ|dgrip|   (only for act_dim == 14)
    score  = motion + lambda_steps * T
    W_POS = 1.0, W_ROT = 1.0, W_GRIP = 0.5.

Episodes with ANY non-finite value in the action tensor are DROPPED before
scoring (not ranked to infinity), since an Inf-ranked episode would still be
saved when keep-top-k exceeds scorable count.

Input npz requirements:
    obs:              (N, obs_dim) float32
    actions:          (N, act_dim) float32, act_dim in {12, 14}
    episode_lengths:  (E,) int32 or int64, sum == N
    episode_success:  (E,) bool, optional. When present, failure episodes
                      are dropped before scoring.

Output npz fields (same layout, filtered to best-k episodes):
    obs, actions, episode_lengths

Per-skill ground-truth motion ladder (run filter with --report-only once to
populate; these are expected ranges, not thresholds):
    IC approach (act_dim=12, λ=0):  motion ≈ 20.0   (scripted descent)
    AC grasp   (act_dim=12, λ=0):  motion ≈ 6–15
    Grip clamp (act_dim=14, λ≥0):  motion ≈ 30–60  (includes grip dim)

Scope: supports Grip (14D), ApproachCable (12D), InsertIntoClip (12D).
AerialRegrasp (AR) is NOT supported — its collector does not yet save
episode_lengths because step×world are interleaved in a flat list.

Usage:
    python thread_isaac_lab/scripts/filter_demos.py \\
        --input thread_isaac_lab/data/bc_demos/grasp_cable_demos_raw.npz \\
        --output thread_isaac_lab/data/bc_demos/grasp_cable_demos_filtered.npz \\
        --keep-top-k 10 --lambda-steps 0.0
"""

import argparse
import os
import sys

import numpy as np


_W_POS = 1.0
_W_ROT = 1.0
_W_GRIP = 0.5


def score_episode(ep_actions: np.ndarray, lambda_steps: float) -> tuple[float, float, int]:
    """Return ``(score, motion, steps)`` for one episode.

    Args:
        ep_actions: shape (T, act_dim) with act_dim in {12, 14}.
        lambda_steps: weight on step count (>= 0).

    Returns:
        score:  ``motion + lambda_steps * T``. ``nan`` if any non-finite is
                present in ep_actions — caller MUST drop the episode, NOT
                rank-by-inf, because otherwise an Inf-scored episode would be
                saved when keep-top-k > scorable count.
        motion: per-channel weighted L1 (W_POS for dpos, W_ROT for drot,
                W_GRIP for dgrip). ``nan`` when any non-finite is present.
        steps:  T.

    F-4 (v3): previously scored only [0:3]/[6:9] (position), silently dropped
    rotation and gripper columns. Grip demos ranked by position alone were
    degenerate (all ≈ 0 motion). Non-finite was demoted to inf — but with
    keep_top_k > scorable this still saved them.
    """
    if ep_actions.ndim != 2:
        raise ValueError(f"ep_actions must be 2-D, got shape {ep_actions.shape}")
    act_dim = ep_actions.shape[1]
    if act_dim not in (12, 14):
        raise ValueError(f"action dim {act_dim} not in {{12, 14}}")
    steps = int(ep_actions.shape[0])
    # F-4 pt.1: ANY non-finite in ANY column → drop the episode. Return nan
    # as a sentinel so the caller can distinguish from a legitimate high score.
    if not np.isfinite(ep_actions).all():
        nan = float("nan")
        return nan, nan, steps

    # F-4 pt.2: per-channel weighted L1 over ALL columns.
    # Layout (action v5): [r_dpos(3), r_drot(3), l_dpos(3), l_drot(3), (r_grip, l_grip)]
    r_dpos = ep_actions[:, 0:3]
    r_drot = ep_actions[:, 3:6]
    l_dpos = ep_actions[:, 6:9]
    l_drot = ep_actions[:, 9:12]
    motion = (
        _W_POS * float(np.sum(np.abs(r_dpos)))
        + _W_POS * float(np.sum(np.abs(l_dpos)))
        + _W_ROT * float(np.sum(np.abs(r_drot)))
        + _W_ROT * float(np.sum(np.abs(l_drot)))
    )
    if act_dim == 14:
        grip = ep_actions[:, 12:14]
        motion += _W_GRIP * float(np.sum(np.abs(grip)))

    score = motion + lambda_steps * steps
    return score, motion, steps


def split_episodes(
    obs: np.ndarray,
    actions: np.ndarray,
    episode_lengths: np.ndarray,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split flat (obs, actions) into per-episode slices using episode_lengths."""
    if int(episode_lengths.sum()) != obs.shape[0]:
        raise ValueError(
            f"episode_lengths.sum()={int(episode_lengths.sum())} != obs.shape[0]={obs.shape[0]}"
        )
    if obs.shape[0] != actions.shape[0]:
        raise ValueError(f"obs/actions length mismatch: {obs.shape[0]} vs {actions.shape[0]}")

    episodes = []
    cursor = 0
    for ep_len in episode_lengths:
        ep_len_i = int(ep_len)
        episodes.append((obs[cursor : cursor + ep_len_i], actions[cursor : cursor + ep_len_i]))
        cursor += ep_len_i
    return episodes


def filter_demos(
    input_path: str,
    output_path: str,
    keep_top_k: int,
    lambda_steps: float = 0.0,
    report_only: bool = False,
    min_steps: int | None = None,
) -> None:
    # F3: reject non-positive keep_top_k instead of silently producing empty npz.
    if keep_top_k <= 0:
        raise ValueError(f"keep_top_k must be > 0, got {keep_top_k}")
    # W4: reject negative lambda_steps (inverts score direction silently).
    if lambda_steps < 0:
        raise ValueError(f"lambda_steps must be >= 0, got {lambda_steps}")
    if min_steps is not None and min_steps < 0:
        raise ValueError(f"min_steps must be >= 0, got {min_steps}")

    # F7: allow_pickle=False closes the object-array RCE surface. Grip now
    # writes episode_stats to a JSON sidecar instead of pickling into npz.
    with np.load(input_path, allow_pickle=False) as data:
        files = list(data.files)
        # F-5: hard reject legacy Grip npz (pre-F7). Pickled `episode_stats`
        # field would only raise on materialization, and the filter never
        # reads it, so legacy files silently passed allow_pickle=False.
        # MUST come before the episode_lengths KeyError — legacy files may
        # lack the field too, and the generic error hides the real cause.
        if "episode_stats" in files:
            raise ValueError(
                f"{input_path} contains legacy 'episode_stats' field "
                "(pickled under allow_pickle=True). Re-run collect_grip_demos.py "
                "— post-F7 writes episode_lengths in the npz and episode_stats "
                "in a JSON sidecar."
            )
        if "episode_lengths" not in files:
            # W3: AR-specific guidance — AR collector is knowingly excluded.
            raise KeyError(
                f"{input_path} has no 'episode_lengths' field.\n"
                "  Grip/ApproachCable/InsertIntoClip collectors were updated to save\n"
                "  it. AerialRegrasp (collect_aerial_regrasp_demos.py) is NOT supported\n"
                "  because step×world are interleaved in a flat list — re-collecting\n"
                "  with the current collector will not produce the field. To filter AR\n"
                "  demos you must pre-compute episode boundaries externally."
            )

        obs = np.asarray(data["obs"])
        actions = np.asarray(data["actions"])
        ep_lens_raw = np.asarray(data["episode_lengths"])
        ep_success = np.asarray(data["episode_success"]).astype(bool) \
            if "episode_success" in files else None

    # min_steps auto (v3.1 W2 + v3.2 C2): the floor=5 is a DEFENSIVE FLOOR
    # against step-0 explosions / immediate early-termination, NOT a calibration
    # of sustain latency. SSOT for the value 5 is `task_config.py:164-165`
    # (`K_CLAMP = K_UNCLAMP = 5`), pass-through at newton_grip_env.py:225,230.
    # Legitimate Grip clamp actually takes ~48 steps to reach sustain-satisfied
    # (38mm finger travel at 0.8mm/step), so 5 is permissive — intended to drop
    # degenerate episodes only. IC/AC (12D) use 0 since their env success
    # criteria are not sustain-based and any non-empty demo is valid.
    #
    # Known limitation: `train_grip.py --k-clamp N` overrides env.CLAMP_SUSTAIN
    # at runtime; if using a non-default sustain value, pass `--min-steps`
    # explicitly. (v3.1 P4 deferred — tracked in post_v3_1_consolidated_verdict.md)
    if min_steps is None:
        min_steps = 5 if actions.shape[1] == 14 else 0

    # W6: validate episode_lengths before int32 cast (silent truncation guard).
    if ep_lens_raw.ndim != 1:
        raise ValueError(f"episode_lengths must be 1-D, got shape {ep_lens_raw.shape}")
    if np.any(ep_lens_raw < 0):
        raise ValueError(
            f"episode_lengths contains negative values: min={int(ep_lens_raw.min())}"
        )
    if np.any(ep_lens_raw > np.iinfo(np.int32).max):
        raise ValueError(
            f"episode_lengths exceeds int32 max: max={int(ep_lens_raw.max())}"
        )
    episode_lengths = ep_lens_raw.astype(np.int32)

    episodes = split_episodes(obs, actions, episode_lengths)
    n_available = len(episodes)
    if n_available == 0:
        raise RuntimeError(f"{input_path} contains 0 episodes")

    # F4 (filter side): if episode_success is present, drop failure episodes
    # before scoring. Failures are typically short (early termination) and
    # would otherwise rank as "best" under motion-minimizing score.
    if ep_success is not None:
        if ep_success.shape[0] != n_available:
            raise ValueError(
                f"episode_success length {ep_success.shape[0]} "
                f"!= episode count {n_available}"
            )
        n_fail = int((~ep_success).sum())
        if n_fail > 0:
            print(f"[FILTER] Dropping {n_fail} failure episodes before scoring")

    scored = []
    n_dropped_nan = 0
    n_dropped_short = 0
    n_dropped_failure = 0
    n_dropped_empty = 0
    for idx, (ep_obs, ep_act) in enumerate(episodes):
        if ep_success is not None and not bool(ep_success[idx]):
            n_dropped_failure += 1
            continue
        if ep_act.shape[0] == 0:
            n_dropped_empty += 1
            continue
        if ep_act.shape[0] < min_steps:
            n_dropped_short += 1
            continue
        score, motion, steps = score_episode(ep_act, lambda_steps)
        # F-4: DROP non-finite (not rank-to-inf). If keep_top_k > scorable,
        # an inf-ranked episode would still be saved.
        if not np.isfinite(score):
            n_dropped_nan += 1
            continue
        scored.append({"idx": idx, "score": score, "motion": motion, "steps": steps})

    if not scored:
        raise RuntimeError(
            f"{input_path}: 0 scorable episodes "
            f"(failure={n_dropped_failure}, empty={n_dropped_empty}, "
            f"short={n_dropped_short}, nan={n_dropped_nan})"
        )

    scored.sort(key=lambda e: (e["score"], e["steps"], e["idx"]))

    n_scorable = len(scored)
    k = min(keep_top_k, n_scorable)
    if k < keep_top_k:
        print(
            f"[FILTER] WARN: requested keep_top_k={keep_top_k} > scorable={n_scorable}; "
            f"clamping to {k}"
        )

    kept = scored[:k]
    dropped = scored[k:]

    print(f"[FILTER] Input:  {input_path}")
    print(f"[FILTER]   episodes={n_available} (scorable={n_scorable}), "
          f"transitions={obs.shape[0]}, obs_dim={obs.shape[1]}, "
          f"act_dim={actions.shape[1]}")
    print(f"[FILTER]   pre-filter drops: failure={n_dropped_failure}, "
          f"empty={n_dropped_empty}, short(<{min_steps})={n_dropped_short}, "
          f"non-finite={n_dropped_nan}")
    print(f"[FILTER] Scoring: weighted-L1 motion + {lambda_steps} * steps "
          f"(W_POS={_W_POS}, W_ROT={_W_ROT}, W_GRIP={_W_GRIP}; lower = better)")
    print(f"[FILTER] Kept top-{k}:")
    for e in kept:
        print(f"[FILTER]   ep{e['idx']:3d}: score={e['score']:.4f}, "
              f"motion={e['motion']:.4f}, steps={e['steps']}")
    if dropped:
        worst = dropped[-1]
        print(f"[FILTER] Dropped {len(dropped)} episodes "
              f"(worst score={worst['score']:.4f}, motion={worst['motion']:.4f}, "
              f"steps={worst['steps']})")

    if report_only:
        print("[FILTER] --report-only; skipping save.")
        return

    kept_episodes = [episodes[e["idx"]] for e in kept]
    out_obs = np.concatenate([ep_obs for ep_obs, _ in kept_episodes], axis=0)
    out_act = np.concatenate([ep_act for _, ep_act in kept_episodes], axis=0)
    out_lengths = np.array([ep_obs.shape[0] for ep_obs, _ in kept_episodes], dtype=np.int32)

    # F-3: raise, not assert. `python -O` strips asserts.
    if int(out_lengths.sum()) != out_obs.shape[0]:
        raise RuntimeError(
            f"post-filter length mismatch: sum={int(out_lengths.sum())} "
            f"vs obs.shape[0]={out_obs.shape[0]}"
        )

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    # W2: use savez_compressed for consistency with collect_grip_demos (~3-5x smaller).
    np.savez_compressed(
        output_path, obs=out_obs, actions=out_act, episode_lengths=out_lengths
    )
    print(f"[FILTER] Output: {output_path}")
    print(f"[FILTER]   episodes={k}, transitions={out_obs.shape[0]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="Raw demo npz path")
    parser.add_argument("--output", required=True, help="Filtered demo npz path")
    parser.add_argument(
        "--keep-top-k",
        type=int,
        required=True,
        help="Number of best episodes to keep (clamped to available)",
    )
    parser.add_argument(
        "--lambda-steps",
        type=float,
        default=0.0,
        help="Weight on step count in the score (default: 0.0 = trajectory length only)",
    )
    parser.add_argument(
        "--min-steps",
        type=int,
        default=None,
        help="Drop episodes shorter than this before scoring. "
        "Default (v3.1): 5 for act_dim=14 (Grip CLAMP_SUSTAIN=5), 0 otherwise.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print the score ranking but do not write an output file",
    )
    args = parser.parse_args()

    filter_demos(
        input_path=args.input,
        output_path=args.output,
        keep_top_k=args.keep_top_k,
        lambda_steps=args.lambda_steps,
        report_only=args.report_only,
        min_steps=args.min_steps,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
