#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Baseline accumulation for Newton Aerial Regrasp terminal metrics.

This runner collects terminal metric observations only. It does not apply an
H4 intervention, compare treatment arms, or make a causal claim.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from types import SimpleNamespace

import numpy as np
import torch

REPO = "/home/rlrk/IsaacLab"
sys.path.insert(0, f"{REPO}/thread_isaac_lab/envs")
sys.path.insert(0, f"{REPO}/thread_isaac_lab/scripts")
sys.path.insert(0, f"{REPO}/thread_isaac_lab")


def _bool_array(log_per_world: dict, key: str, world_count: int) -> np.ndarray:
    return np.asarray(log_per_world[key])[:world_count].astype(bool, copy=False)


def _jsonable_counts(values: np.ndarray) -> dict[str, int]:
    labels, counts = np.unique(values.astype(str), return_counts=True)
    return {str(label): int(count) for label, count in zip(labels, counts, strict=True)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=f"{REPO}/logs/rl_ar_alpha4b_grid1v3_seed0/model_best.pt")
    parser.add_argument("--world-count", type=int, default=256)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--output-dir",
        default=f"{REPO}/eval_runs/phase4_terminal_metric_layer_baseline_2026-05-11/results",
    )
    parser.add_argument("--sample-limit", type=int, default=128)
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device
    os.makedirs(args.output_dir, exist_ok=True)

    from eval_skill import SKILL_REGISTRY, _build_train_cfg, _load_policy
    from newton_aerial_regrasp_env import NewtonAerialRegraspEnv
    from rsl_rl.runners import OnPolicyRunner

    started_at = time.time()
    env = NewtonAerialRegraspEnv(world_count=args.world_count, device=args.device)
    train_cfg = _build_train_cfg(env, args.world_count, args.device)
    runner = OnPolicyRunner(env=env, train_cfg=train_cfg, log_dir=args.output_dir, device=args.device)
    loader_args = SimpleNamespace(
        checkpoint=args.checkpoint,
        base_model=None,
        lora_rank=8,
        device=args.device,
    )
    policy = _load_policy(runner, loader_args, SKILL_REGISTRY["ar"])

    required_keys = {
        "success",
        "terminal_entered",
        "terminal_hold_len",
        "terminal_break_reason",
        "terminal_status_right_clamp",
        "terminal_status_left_hold",
        "terminal_status_cable_not_dropped",
    }
    break_reason_counts: dict[str, int] = {}
    terminal_entered_count = 0
    terminal_hold_lengths: list[int] = []
    success_count = 0
    completion_count = 0
    parity_mismatch_count = 0
    parity_checked_samples = 0
    component_counts = {
        "right_clamp": 0,
        "left_hold": 0,
        "cable_not_dropped": 0,
    }
    episode_summaries = []
    sample_records = []
    missing_keys: list[str] = []

    for episode in range(args.episodes):
        obs, _ = env.reset()
        completed_once = np.zeros(args.world_count, dtype=bool)
        episode_successes = 0
        episode_completions = 0
        episode_break_reasons: dict[str, int] = {}
        episode_max_hold = 0

        for step in range(args.max_steps):
            with torch.no_grad():
                actions = policy.act_inference(obs)

            obs, _, dones, extras = env.step(actions)
            log_per_world = extras.get("log_per_world", {})
            missing_keys = sorted(required_keys - set(log_per_world))
            if missing_keys:
                break

            success_arr = _bool_array(log_per_world, "success", args.world_count)
            terminal_entered = _bool_array(log_per_world, "terminal_entered", args.world_count)
            terminal_hold_len = np.asarray(log_per_world["terminal_hold_len"])[: args.world_count].astype(np.int32)
            terminal_break_reason = np.asarray(log_per_world["terminal_break_reason"])[: args.world_count].astype(str)
            right_clamp = _bool_array(log_per_world, "terminal_status_right_clamp", args.world_count)
            left_hold = _bool_array(log_per_world, "terminal_status_left_hold", args.world_count)
            cable_not_dropped = _bool_array(
                log_per_world,
                "terminal_status_cable_not_dropped",
                args.world_count,
            )

            success_from_hold = terminal_hold_len >= env.C5_SUSTAIN_STEPS
            parity_mismatch_count += int(np.sum(success_arr != success_from_hold))
            parity_checked_samples += int(args.world_count)

            done_idx = np.where(dones.cpu().numpy()[: args.world_count])[0]
            for world_idx in done_idx:
                if completed_once[world_idx]:
                    continue
                completed_once[world_idx] = True
                reason = str(terminal_break_reason[world_idx])
                success = bool(success_arr[world_idx])
                hold_len = int(terminal_hold_len[world_idx])
                entered = bool(terminal_entered[world_idx])

                completion_count += 1
                episode_completions += 1
                success_count += int(success)
                episode_successes += int(success)
                terminal_entered_count += int(entered)
                terminal_hold_lengths.append(hold_len)
                episode_max_hold = max(episode_max_hold, hold_len)
                break_reason_counts[reason] = break_reason_counts.get(reason, 0) + 1
                episode_break_reasons[reason] = episode_break_reasons.get(reason, 0) + 1
                component_counts["right_clamp"] += int(right_clamp[world_idx])
                component_counts["left_hold"] += int(left_hold[world_idx])
                component_counts["cable_not_dropped"] += int(cable_not_dropped[world_idx])

                if len(sample_records) < args.sample_limit:
                    sample_records.append(
                        {
                            "episode": int(episode),
                            "world": int(world_idx),
                            "step": int(step + 1),
                            "success": success,
                            "terminal_entered": entered,
                            "terminal_hold_len": hold_len,
                            "terminal_break_reason": reason,
                            "right_clamp": bool(right_clamp[world_idx]),
                            "left_hold": bool(left_hold[world_idx]),
                            "cable_not_dropped": bool(cable_not_dropped[world_idx]),
                        }
                    )

            if completed_once.all():
                break

        episode_summaries.append(
            {
                "episode": int(episode),
                "completions": int(episode_completions),
                "successes": int(episode_successes),
                "success_rate": float(episode_successes / max(episode_completions, 1)),
                "break_reason_counts": episode_break_reasons,
                "max_terminal_hold_len": int(episode_max_hold),
                "step_count": int(step + 1),
                "completed_all_worlds": bool(completed_once.all()),
            }
        )
        print(
            f"[BASELINE] episode={episode} completions={episode_completions}/{args.world_count} "
            f"successes={episode_successes} max_hold={episode_max_hold} "
            f"reasons={json.dumps(episode_break_reasons, sort_keys=True)}",
            flush=True,
        )
        if missing_keys:
            break

    elapsed_s = time.time() - started_at
    hold_array = np.asarray(terminal_hold_lengths, dtype=np.int32)
    summary = {
        "scope": "Phase 4 #1 AR terminal metric baseline accumulation",
        "causal_claim": "none",
        "checkpoint": args.checkpoint,
        "device": args.device,
        "world_count": args.world_count,
        "episodes_requested": args.episodes,
        "episodes_completed": len(episode_summaries),
        "max_steps": args.max_steps,
        "elapsed_s": elapsed_s,
        "required_metric_keys_present": not missing_keys,
        "missing_metric_keys": missing_keys,
        "canonical_k": int(env.C5_SUSTAIN_STEPS),
        "canonical_k_parity_pass": parity_mismatch_count == 0,
        "canonical_k_parity_mismatch_count": parity_mismatch_count,
        "canonical_k_parity_checked_samples": parity_checked_samples,
        "first_completion_count": int(completion_count),
        "first_completion_successes": int(success_count),
        "first_completion_success_rate": float(success_count / max(completion_count, 1)),
        "terminal_entered_count": int(terminal_entered_count),
        "terminal_entered_rate": float(terminal_entered_count / max(completion_count, 1)),
        "terminal_hold_len_max": int(hold_array.max()) if hold_array.size else 0,
        "terminal_hold_len_mean": float(hold_array.mean()) if hold_array.size else 0.0,
        "terminal_hold_len_median": float(np.median(hold_array)) if hold_array.size else 0.0,
        "first_completion_break_reason_counts": break_reason_counts,
        "component_true_counts": component_counts,
        "component_true_rates": {
            key: float(value / max(completion_count, 1)) for key, value in component_counts.items()
        },
        "episode_summaries": episode_summaries,
    }

    summary_path = os.path.join(args.output_dir, "baseline_terminal_metric_summary.json")
    samples_path = os.path.join(args.output_dir, "baseline_terminal_metric_samples.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    with open(samples_path, "w") as f:
        json.dump({"sample_first_done_records": sample_records}, f, indent=2)

    if hasattr(env, "close"):
        env.close()

    print(json.dumps(summary, indent=2))
    return 0 if summary["required_metric_keys_present"] and summary["canonical_k_parity_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
