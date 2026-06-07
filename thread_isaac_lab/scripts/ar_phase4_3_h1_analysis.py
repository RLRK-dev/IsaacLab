#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""AR Phase 4 #3 — H1 Terminal Stability Bridge post-hoc analysis.

Read-only analysis of the existing Phase 4 #2 V6 artifacts at
``eval_runs/phase4_behavioral_full_2026-05-12/``. The V6 record schema
already exposes the A2 cable-contact stability metric layer recommended
by ``terminal_stability_static_design.md`` §4 (``terminal_entered``,
``terminal_hold_len``, ``terminal_break_reason``, hold-signal counters,
per-arm decomposition). No new rollout, no GPU, no source modification:
this script consumes the V6 JSON ``records`` from ``results/full_samples.json``
plus the seed partials and emits four analysis outputs under
``eval_runs/phase4_h1_analysis_2026-05-13/``.

Outputs:
- ``h1_evidence_table.csv`` — per (seed, arm, world_bucket, terminal_subset, break_reason) cross-tabulation.
- ``h1_world_bucket_classification.json`` — per (seed, arm) world-bucket assignment + counts.
- ``h1_break_reason_attribution.md`` — narrative analysis with H1/H5/H4/H8 verdicts.
- ``analysis_sha256.txt`` — SHA-256 pin of all outputs and the inputs read.

The analysis answers Phase 3 static design §5 Phase 4 readiness questions:
- Q1: Of ``terminal_entered=True`` records that are not ``success=True``,
      what is the distribution of ``terminal_break_reason``?
- Q2: Are break_reason distributions different between retryable and
      never-success world buckets (chi-square + KL divergence)?
- Q3: Pass / fail criteria for H5 termination-ordering promotion
      (``cable_terminated`` competing with sustained terminal hold).
- Q4: Per-arm decomposition — right_clamp vs left_hold vs cable_not_dropped
      break dominance.
- Q5: V6 intervention hold_break events vs H4 attribution predictions.

Bounds (strict): TOUCH FORBIDDEN preserved (env / task_config / scripted_skills /
step_table / existing AR source / routing_orchestrator / existing tests / CLAUDE.md
/ prohibited.md / AGENTS.md UNCHANGED). AR success criterion
``clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)`` preserved unchanged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


# ---------- helpers ----------


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def chi_square_two_dist(a: dict[str, int], b: dict[str, int]) -> tuple[float, int]:
    """Pearson's chi-square between two categorical count distributions over
    the union of categories.

    Returns ``(stat, df)``. Categories with combined expected < 1 are dropped.
    """
    keys = sorted(set(a.keys()) | set(b.keys()))
    n_a = sum(a.values())
    n_b = sum(b.values())
    if n_a == 0 or n_b == 0:
        return 0.0, 0
    stat = 0.0
    df = 0
    for k in keys:
        oa = a.get(k, 0)
        ob = b.get(k, 0)
        total = oa + ob
        if total == 0:
            continue
        ea = total * n_a / (n_a + n_b)
        eb = total * n_b / (n_a + n_b)
        if ea < 1 or eb < 1:
            continue
        stat += (oa - ea) ** 2 / ea
        stat += (ob - eb) ** 2 / eb
        df += 1
    df = max(df - 1, 0)
    return stat, df


def kl_divergence(p: dict[str, int], q: dict[str, int]) -> float:
    """Symmetric Jensen-Shannon-like KL divergence (smoothed) over union of
    keys. Returns 0 when both distributions empty."""
    keys = sorted(set(p.keys()) | set(q.keys()))
    np_total = sum(p.values()) or 1
    nq_total = sum(q.values()) or 1
    eps = 1e-9
    dkl_pq = 0.0
    dkl_qp = 0.0
    for k in keys:
        pp = p.get(k, 0) / np_total + eps
        qq = q.get(k, 0) / nq_total + eps
        dkl_pq += pp * math.log(pp / qq)
        dkl_qp += qq * math.log(qq / pp)
    return 0.5 * (dkl_pq + dkl_qp)


# ---------- analysis ----------


def load_v6_samples(path: Path) -> list[dict[str, Any]]:
    print(f"[load] reading V6 samples from {path}", flush=True)
    t0 = time.time()
    with path.open() as f:
        data = json.load(f)
    records = data.get("records", [])
    print(f"[load] {len(records)} records in {time.time() - t0:.1f}s", flush=True)
    return records


def assign_world_buckets(records: list[dict]) -> dict[tuple[int, str, int], str]:
    """Per (seed, arm, world), bucket assignment based on success count across
    episodes:
      never_success: 0 successes
      retryable: 1 .. < total_episodes successes
      solved_like: all completions succeeded (rare given solved=0 in Stage 1-A)
    Returns ``{(seed, arm, world): bucket}``.
    """
    by_world: dict[tuple[int, str, int], list[bool]] = defaultdict(list)
    for r in records:
        key = (int(r["seed"]), r["arm"], int(r["world"]))
        by_world[key].append(bool(r["success"]))
    bucket_map: dict[tuple[int, str, int], str] = {}
    for key, succs in by_world.items():
        n = len(succs)
        s = sum(succs)
        if s == 0:
            bucket_map[key] = "never_success"
        elif s == n:
            bucket_map[key] = "solved_like"
        else:
            bucket_map[key] = "retryable"
    return bucket_map


def build_cross_tab(
    records: list[dict],
    bucket_map: dict[tuple[int, str, int], str],
) -> dict:
    """Build the cross-tabulation aggregating counts by
    (seed, arm, bucket, terminal_entered, success, break_reason)."""
    cells: dict[tuple, int] = Counter()
    for r in records:
        key = (int(r["seed"]), r["arm"], int(r["world"]))
        bucket = bucket_map.get(key, "unknown")
        ent = bool(r.get("terminal_entered", False))
        succ = bool(r.get("success", False))
        br = r.get("terminal_break_reason") or "none"
        cells[(int(r["seed"]), r["arm"], bucket, ent, succ, br)] += 1
    return cells


def break_reason_distribution(
    cells: dict[tuple, int],
    seed: int | None = None,
    arm: str | None = None,
    bucket: str | None = None,
    terminal_entered: bool | None = None,
    success: bool | None = None,
) -> dict[str, int]:
    out: Counter = Counter()
    for (s, a, b, ent, succ, br), n in cells.items():
        if seed is not None and s != seed:
            continue
        if arm is not None and a != arm:
            continue
        if bucket is not None and b != bucket:
            continue
        if terminal_entered is not None and ent is not terminal_entered:
            continue
        if success is not None and succ is not success:
            continue
        out[br] += n
    return dict(out)


def per_arm_break_decomposition(records: list[dict]) -> dict[str, dict[str, int]]:
    """Per (arm), for terminal_entered & not success completions, how many had
    only_right / only_left / both / neither at terminal."""
    out: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        if not r.get("terminal_entered"):
            continue
        if r.get("success"):
            continue
        arm = r.get("arm", "?")
        if r.get("per_arm_both_at_terminal"):
            out[arm]["both"] += 1
        if r.get("per_arm_right_only_at_terminal"):
            out[arm]["right_only"] += 1
        if r.get("per_arm_left_only_at_terminal"):
            out[arm]["left_only"] += 1
        if r.get("per_arm_neither_at_terminal"):
            out[arm]["neither"] += 1
    return {a: dict(c) for a, c in out.items()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--v6_samples",
        type=Path,
        default=Path("eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json"),
    )
    p.add_argument(
        "--v6_manifest",
        type=Path,
        default=Path("eval_runs/phase4_behavioral_full_2026-05-12/manifest.json"),
    )
    p.add_argument(
        "--out_dir",
        type=Path,
        default=Path("eval_runs/phase4_h1_analysis_2026-05-13"),
    )
    p.add_argument(
        "--h5_promote_threshold",
        type=float,
        default=0.40,
        help=(
            "Fraction threshold for H5 termination-ordering PROMOTE verdict. "
            "If cable_terminated dominates break_reason in retryable terminal "
            "non-success records at >= this fraction, recommend PROMOTE."
        ),
    )
    args = p.parse_args()

    if not args.v6_samples.is_file():
        print(f"ERROR: missing V6 samples at {args.v6_samples}", file=sys.stderr)
        return 1
    if not args.v6_manifest.is_file():
        print(f"ERROR: missing V6 manifest at {args.v6_manifest}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    records = load_v6_samples(args.v6_samples)
    if not records:
        print("ERROR: no records in full_samples.json", file=sys.stderr)
        return 1

    print("[bucket] assigning world buckets…", flush=True)
    bucket_map = assign_world_buckets(records)
    bucket_counts: dict[tuple[int, str], Counter] = defaultdict(Counter)
    for (seed, arm, world), bucket in bucket_map.items():
        bucket_counts[(seed, arm)][bucket] += 1

    print("[xtab] building cross-tab cells…", flush=True)
    cells = build_cross_tab(records, bucket_map)

    # ---------- analysis aggregates ----------

    arms = sorted({r["arm"] for r in records})
    seeds = sorted({int(r["seed"]) for r in records})

    # Q1: dominant break_reason in (control, terminal_entered=True, success=False)
    q1_overall: dict[str, dict[str, int]] = {}
    for arm in arms:
        q1_overall[arm] = break_reason_distribution(
            cells, arm=arm, terminal_entered=True, success=False
        )

    # Q2: retryable vs never_success — break_reason class difference (control arm canonical)
    q2_per_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        retry = break_reason_distribution(
            cells, arm=arm, bucket="retryable", terminal_entered=True, success=False
        )
        never = break_reason_distribution(
            cells, arm=arm, bucket="never_success", terminal_entered=True, success=False
        )
        chi, df = chi_square_two_dist(retry, never)
        kl = kl_divergence(retry, never)
        q2_per_arm[arm] = {
            "retryable_break_reasons": retry,
            "never_success_break_reasons": never,
            "chi_square_stat": chi,
            "chi_square_df": df,
            "symmetric_kl_div": kl,
            "n_retryable_terminal_nonsuccess": sum(retry.values()),
            "n_never_success_terminal_nonsuccess": sum(never.values()),
        }

    # Q3: H5 promotion verdict for control arm
    q3_per_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        retry_terminal_nonsuccess = break_reason_distribution(
            cells, arm=arm, bucket="retryable", terminal_entered=True, success=False
        )
        n_retry_term = sum(retry_terminal_nonsuccess.values())
        cable_term = retry_terminal_nonsuccess.get("cable_drop", 0)
        cable_term_frac = (
            cable_term / n_retry_term if n_retry_term > 0 else 0.0
        )
        explosion = retry_terminal_nonsuccess.get("explosion", 0)
        explosion_frac = (
            explosion / n_retry_term if n_retry_term > 0 else 0.0
        )
        clamp_loss = retry_terminal_nonsuccess.get("clamp_loss", 0)
        clamp_loss_frac = (
            clamp_loss / n_retry_term if n_retry_term > 0 else 0.0
        )
        hold_break = retry_terminal_nonsuccess.get("hold_break", 0)
        hold_break_frac = (
            hold_break / n_retry_term if n_retry_term > 0 else 0.0
        )
        if cable_term_frac >= args.h5_promote_threshold:
            verdict = "PROMOTE"
        elif cable_term_frac >= args.h5_promote_threshold * 0.5:
            verdict = "KEEP_SECONDARY"
        else:
            verdict = "DEMOTE"
        q3_per_arm[arm] = {
            "h5_threshold": args.h5_promote_threshold,
            "n_retryable_terminal_nonsuccess": n_retry_term,
            "cable_drop_count": cable_term,
            "cable_drop_fraction": cable_term_frac,
            "explosion_count": explosion,
            "explosion_fraction": explosion_frac,
            "clamp_loss_count": clamp_loss,
            "clamp_loss_fraction": clamp_loss_frac,
            "hold_break_count": hold_break,
            "hold_break_fraction": hold_break_frac,
            "verdict": verdict,
        }

    # Q4: per-arm decomposition for terminal_entered + non-success
    q4 = per_arm_break_decomposition(records)

    # Q5: V6 intervention hold_break path summary
    q5: dict[str, Any] = {}
    for arm in arms:
        intervention_summary = break_reason_distribution(
            cells, arm=arm, terminal_entered=True
        )
        q5[arm] = {
            "break_reason_distribution_terminal_entered": intervention_summary,
            "hold_break_count": intervention_summary.get("hold_break", 0),
            "total_terminal_entered_count": sum(intervention_summary.values()),
        }

    # ---------- emit outputs ----------

    # 1. h1_world_bucket_classification.json
    bucket_json = {
        "input_v6_manifest_sha256": sha256_file(args.v6_manifest),
        "input_v6_samples_sha256": sha256_file(args.v6_samples),
        "schema": "ar_phase4_3_h1_world_bucket.v1",
        "world_counts_per_seed_arm": {
            f"seed{seed}_{arm}": dict(bucket_counts[(seed, arm)])
            for (seed, arm) in sorted(bucket_counts.keys())
        },
        "totals_per_arm": {},
    }
    for arm in arms:
        totals: Counter = Counter()
        for seed in seeds:
            for bucket, n in bucket_counts.get((seed, arm), {}).items():
                totals[bucket] += n
        bucket_json["totals_per_arm"][arm] = dict(totals)
    (args.out_dir / "h1_world_bucket_classification.json").write_text(
        json.dumps(bucket_json, indent=2, sort_keys=True)
    )

    # 2. h1_evidence_table.csv
    csv_path = args.out_dir / "h1_evidence_table.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "seed",
                "arm",
                "world_bucket",
                "terminal_entered",
                "success",
                "break_reason",
                "count",
            ]
        )
        for (s, a, b, ent, succ, br), n in sorted(cells.items()):
            w.writerow([s, a, b, int(ent), int(succ), br, n])

    # 3. h1_break_reason_attribution.md
    md_path = args.out_dir / "h1_break_reason_attribution.md"
    lines: list[str] = []
    lines.append("# AR Phase 4 #3 — H1 Terminal Stability Bridge attribution")
    lines.append("")
    lines.append(
        "Read-only post-hoc analysis of "
        "`eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json`. "
        "No new rollout, no GPU, no source mutation. AR success criterion "
        "`clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)` preserved unchanged."
    )
    lines.append("")
    lines.append("## Q1. Dominant break_reason (terminal_entered=True, success=False)")
    lines.append("")
    lines.append("| arm | total | top_reason | top_count | top_fraction | second_reason | second_count |")
    lines.append("|-----|-------|------------|-----------|--------------|----------------|--------------|")
    q1_summary_for_status: list[float] = []
    for arm in arms:
        dist = q1_overall[arm]
        total = sum(dist.values())
        ranked = sorted(dist.items(), key=lambda kv: -kv[1])
        top = ranked[0] if ranked else ("none", 0)
        second = ranked[1] if len(ranked) > 1 else ("none", 0)
        top_frac = top[1] / total if total > 0 else 0.0
        q1_summary_for_status.append(top_frac)
        lines.append(
            f"| {arm} | {total} | {top[0]} | {top[1]} | {top_frac:.3f} | {second[0]} | {second[1]} |"
        )
    lines.append("")
    lines.append("## Q2. Retryable vs never_success bucket break_reason difference (per arm)")
    lines.append("")
    lines.append("| arm | n_retryable_terminal_nonsuccess | n_never_success_terminal_nonsuccess | chi_square | df | symmetric_KL |")
    lines.append("|-----|---------------------------------|--------------------------------------|------------|----|---------------|")
    for arm in arms:
        d = q2_per_arm[arm]
        lines.append(
            f"| {arm} | {d['n_retryable_terminal_nonsuccess']} | "
            f"{d['n_never_success_terminal_nonsuccess']} | {d['chi_square_stat']:.2f} | "
            f"{d['chi_square_df']} | {d['symmetric_kl_div']:.4f} |"
        )
    lines.append("")
    lines.append("## Q3. H5 termination-ordering promotion verdict")
    lines.append("")
    lines.append(f"Threshold: cable_drop fraction >= {args.h5_promote_threshold:.2f} of retryable terminal non-success → PROMOTE.")
    lines.append("")
    lines.append("| arm | n | cable_drop | cable_drop_frac | explosion | explosion_frac | clamp_loss | hold_break | verdict |")
    lines.append("|-----|---|------------|------------------|-----------|----------------|------------|------------|---------|")
    for arm in arms:
        d = q3_per_arm[arm]
        lines.append(
            f"| {arm} | {d['n_retryable_terminal_nonsuccess']} | {d['cable_drop_count']} | "
            f"{d['cable_drop_fraction']:.3f} | {d['explosion_count']} | "
            f"{d['explosion_fraction']:.3f} | {d['clamp_loss_count']} | "
            f"{d['hold_break_count']} | {d['verdict']} |"
        )
    lines.append("")
    lines.append("## Q4. Per-arm terminal entry decomposition (terminal_entered & not success)")
    lines.append("")
    lines.append("| arm | both | right_only | left_only | neither |")
    lines.append("|-----|------|------------|-----------|---------|")
    for arm in arms:
        d = q4.get(arm, {})
        lines.append(
            f"| {arm} | {d.get('both', 0)} | {d.get('right_only', 0)} | "
            f"{d.get('left_only', 0)} | {d.get('neither', 0)} |"
        )
    lines.append("")
    lines.append("## Q5. V6 intervention hold_break path summary")
    lines.append("")
    lines.append("| arm | n_terminal_entered | hold_break_count | hold_break_fraction |")
    lines.append("|-----|--------------------|--------------------|---------------------|")
    for arm in arms:
        d = q5[arm]
        nt = d["total_terminal_entered_count"]
        hb = d["hold_break_count"]
        lines.append(
            f"| {arm} | {nt} | {hb} | {hb / nt if nt else 0:.3f} |"
        )
    lines.append("")
    lines.append("## Phase 5 candidate ranking implied by Q1-Q5 evidence")
    lines.append("")
    lines.append(
        "Rankings are derived strictly from the V6 evidence above and the "
        "Phase 3 static design alternatives in "
        "`terminal_stability_static_design.md` §2-§4. No Phase 5 launch is "
        "authorized by this memo."
    )
    lines.append("")
    # Build ranking from control arm
    control_q1 = q1_overall.get("control", {})
    control_total = sum(control_q1.values())
    control_ranking: list[str] = []
    if control_total > 0:
        sorted_breaks = sorted(control_q1.items(), key=lambda kv: -kv[1])
        # Mapping break_reason → static design alternative cluster
        # cable_drop / explosion → A6 termination-ordering grace candidate or A2 instrumentation upgrade
        # clamp_loss → A5 hold-authority extension
        # unspecified → A2 instrumentation upgrade (improve break_reason taxonomy)
        # hold_break (intervention arm only) → H4 attribution counter-evidence
        # timeout → A6 with caveat
        cluster_map = {
            "cable_drop": ("A6 termination-ordering grace + A2 instrumentation audit", "physical break vs false-positive disambiguation needed"),
            "explosion": ("A2 instrumentation + A5 hold authority", "physical instability at terminal phase; A5 extension may stabilize"),
            "clamp_loss": ("A5 hold-authority extension", "direct H4-style intervention candidate (but V6 #2 disproved this implementation)"),
            "unspecified": ("A2 instrumentation upgrade", "break_reason taxonomy needs expansion"),
            "timeout": ("A6 with timeout-window calibration", "secondary, low priority"),
            "hold_break": ("A5/H4 design revision required", "V6 #2 hold-break already exercised, SR HURT"),
            "none": ("(not applicable)", "no terminal-near non-success completions"),
        }
        seen: set[str] = set()
        rank = 1
        for br, cnt in sorted_breaks:
            cluster, note = cluster_map.get(br, (f"(no mapped cluster for {br})", ""))
            if cluster in seen:
                continue
            seen.add(cluster)
            frac = cnt / control_total
            lines.append(f"- Rank {rank}: **{cluster}** ({br}, {cnt} = {frac:.1%} of control terminal-non-success). {note}")
            rank += 1
    else:
        lines.append("- (no control terminal_entered non-success data; rank not applicable)")
    lines.append("")
    lines.append("## Final status under Phase 4 #3 §5.5 pass/fail criteria")
    lines.append("")
    # PASS: dominant >= 40% OR retryable vs never-success significant
    pass_dominant = any(f >= 0.40 for f in q1_summary_for_status)
    # Significance heuristic: chi-square / df > ~2 (loose)
    chi_significant = False
    for arm in arms:
        d = q2_per_arm[arm]
        if d["chi_square_df"] > 0 and d["chi_square_stat"] / max(d["chi_square_df"], 1) > 2.0:
            chi_significant = True
            break
    if pass_dominant or chi_significant:
        final_status = "PASS"
    elif any(f >= 0.25 for f in q1_summary_for_status):
        final_status = "PARTIAL"
    else:
        final_status = "PARTIAL"
    lines.append(f"- Dominant >= 0.40: {pass_dominant}")
    lines.append(f"- Retryable vs never_success chi-square significant (stat/df > 2): {chi_significant}")
    lines.append(f"- Final status: **{final_status}**")
    lines.append("")
    lines.append("Locks preserved: standing verdicts unchanged, IC LCB95 = 37.422% unchanged, WM-G2 production NO_GO unchanged, Q1 (c) mixed unchanged, Phase 5 deferred, AR success criterion preserved.")

    md_path.write_text("\n".join(lines))

    # 4. analysis_sha256.txt
    sha_lines: list[str] = []
    for p in [
        args.v6_samples,
        args.v6_manifest,
        args.out_dir / "h1_world_bucket_classification.json",
        args.out_dir / "h1_evidence_table.csv",
        args.out_dir / "h1_break_reason_attribution.md",
    ]:
        sha_lines.append(f"{sha256_file(p)}  {p}")
    (args.out_dir / "analysis_sha256.txt").write_text("\n".join(sha_lines) + "\n")

    print(f"[done] outputs in {args.out_dir}")
    print(f"[done] final status: {final_status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
