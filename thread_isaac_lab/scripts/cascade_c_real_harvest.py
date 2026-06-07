#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C real failure log harvester — Track 2 skeleton (manual annotation).

Scans ``data/<run_dir>/RUN_METRICS.json`` files for failure events (overall
!= "PASS"), extracts per-episode failure metadata, and emits an annotation
template JSONL. Each emitted entry has the verdict / failure_mode / reasoning
fields left as ``null`` so that CC + Rs combined verify can fill them in
(per design memo §3 + Qwen §4.2 Track 2).

This is a *skeleton* — the real Track 2 dataset relies on G5 wet-run logs
which are still pending (per ``T-WM-G2/state.md`` external_dependencies). The
harvester is meant to be re-run when fresh logs land; the format is stable.

Output:
    data/cascade_c_dataset_v0/real_failures_template.jsonl
    data/cascade_c_dataset_v0/real_harvest_summary.json

Usage:
    python thread_isaac_lab/scripts/cascade_c_real_harvest.py \\
        --data-root data \\
        --output data/cascade_c_dataset_v0 \\
        --max-runs 50
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Modes recognized in RUN_METRICS — matches derive_skill_result + design memo F1-F7
KEYWORDS_F1 = ("nan", "explosion", "explod", "infinity", "inf ")  # NaN cascade
KEYWORDS_F2 = ("cable_drop", "drop", "p1_grasp_fail")
KEYWORDS_F3 = ("timeout", "max_steps", "time_out")
KEYWORDS_F4 = ("partial", "bilateral", "clamp_l_fail", "clamp_r_fail", "p2_lift_fail")
KEYWORDS_F5 = ("ood", "p3_move_fail", "p4_push_fail")  # spatial drift / OOD policy


def _classify_failure_mode_hint(fail_reason: str | None, error: str | None) -> str | None:
    """Return a best-effort F1-F7 hint based on keywords, or None for manual review."""
    blob = f"{fail_reason or ''} {error or ''}".lower()
    if not blob.strip():
        return None
    if any(k in blob for k in KEYWORDS_F1):
        return "F1"
    if any(k in blob for k in KEYWORDS_F2):
        return "F2"
    if any(k in blob for k in KEYWORDS_F3):
        return "F3"
    if any(k in blob for k in KEYWORDS_F4):
        return "F4"
    if any(k in blob for k in KEYWORDS_F5):
        return "F5"
    return None  # → reviewer assigns


def harvest_run_metrics(run_metrics_path: Path) -> list[dict]:
    """Extract one annotation-pending sample per FAIL/CRASH episode."""
    try:
        data = json.loads(run_metrics_path.read_text())
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"[harvest] skip {run_metrics_path}: {exc}", file=sys.stderr, flush=True)
        return []

    out: list[dict] = []
    episodes = data.get("episodes", [])
    if not isinstance(episodes, list):
        return out

    run_id = run_metrics_path.parent.name
    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        overall = ep.get("overall")
        if overall is None or str(overall).upper() == "PASS":
            continue
        fail_reason = ep.get("fail_reason")
        error = ep.get("error")
        # NaN sanitize for JSONL compatibility
        episode_blob = json.dumps(ep, default=str)
        if "NaN" in episode_blob or "Infinity" in episode_blob:
            episode_blob = episode_blob.replace("NaN", "null").replace("Infinity", "null")
            try:
                ep_clean = json.loads(episode_blob)
            except json.JSONDecodeError:
                ep_clean = {"raw": episode_blob[:500]}
        else:
            ep_clean = ep

        hint = _classify_failure_mode_hint(fail_reason, error)
        out.append(
            {
                "sample_id": f"REAL_{run_id}_ep{ep.get('episode', 'X')}",
                "track": "real",
                "source_run_id": run_id,
                "source_path": str(run_metrics_path),
                "episode_idx": ep.get("episode"),
                "skill": None,  # ← reviewer fills (AC/IC/AR/Grip)
                "failure_mode_gt": None,  # ← reviewer fills (F1-F7 ground truth)
                "failure_mode_hint": hint,  # heuristic (may be wrong)
                "input": {
                    "raw_episode": ep_clean,
                    "fail_reason": fail_reason,
                    "error": error,
                    "overall": overall,
                },
                "expected_output": {
                    "verdict": None,  # ← reviewer fills
                    "confidence": None,
                    "failure_mode": None,
                    "recommended_action": {
                        "skill_override": None,
                        "retry_seed_override": None,
                        "scripted_fallback": None,
                        "rollback_depth_hint": None,
                    },
                    "reasoning": None,  # ← reviewer fills with episode-specific cause
                },
                "annotation_status": "PENDING",
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Cascade C Track-2 real failure harvester")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("data/cascade_c_dataset_v0"))
    parser.add_argument(
        "--max-runs",
        type=int,
        default=200,
        help="Cap number of run dirs to scan (avoid scanning thousands).",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    candidates = sorted(args.data_root.glob("*/RUN_METRICS.json"))[: args.max_runs]
    if not candidates:
        print(f"[harvest] no RUN_METRICS.json under {args.data_root}", flush=True)
        return 1

    samples: list[dict] = []
    scanned = 0
    failed_runs = 0
    t0 = time.time()
    for path in candidates:
        scanned += 1
        run_samples = harvest_run_metrics(path)
        if run_samples:
            failed_runs += 1
            samples.extend(run_samples)

    template_path = args.output / "real_failures_template.jsonl"
    with template_path.open("w") as f:
        for s in samples:
            f.write(json.dumps(s, separators=(",", ":")) + "\n")

    summary = {
        "scanned_runs": scanned,
        "runs_with_failures": failed_runs,
        "total_pending_samples": len(samples),
        "elapsed_s": round(time.time() - t0, 3),
        "data_root": str(args.data_root),
        "max_runs_cap": args.max_runs,
        "annotation_status": "ALL_PENDING",
        "next_action": (
            "Manual review: assign skill (AC/IC/AR/Grip), failure_mode_gt (F1-F7), "
            "and verdict per design memo §3.1 (b). G5 wet-run logs (post Phase 5-2) "
            "expected to be the primary input source."
        ),
        "hint_distribution": _hint_distribution(samples),
    }
    (args.output / "real_harvest_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(
        f"[harvest] scanned={scanned} runs_with_failures={failed_runs} "
        f"pending_samples={len(samples)} → {template_path}",
        flush=True,
    )
    return 0


def _hint_distribution(samples: list[dict]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for s in samples:
        h = s.get("failure_mode_hint") or "UNCLASSIFIED"
        dist[h] = dist.get(h, 0) + 1
    return dist


if __name__ == "__main__":
    sys.exit(main())
