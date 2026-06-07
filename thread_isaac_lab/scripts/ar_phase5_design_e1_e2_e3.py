#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""AR Phase 5 design-only E1 + E2 + E3 split-track analyses.

Read-only post-hoc analyses on existing V6 artifacts at
``eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json``.
No new rollout, no GPU, no source mutation.

Authorized by Rs代行 disposition 2026-05-13 05:50 JST ACK
``T_ROOT_COORD_P5_DESIGN_READINESS_ACK_20260513_0540 root`` option (α) under
split-track design-only scope:

- E1 (Track 1 primary): A6 grace feasibility — for each cable_drop and
  near-miss completion, estimate the SR uplift from a grace window
  K_GRACE in {3, 5, 10} given the existing ``terminal_hold_len`` distribution.
- E2 (Track 1 adjunct): cable_drop false-positive audit — flag cable_drop
  records where ``right_clamp ∧ left_hold`` remained True at termination
  (a structural signature of false-positive cable_drop per the AR bug
  history reference).
- E3 (Track 2 parallel): right-arm asymmetry hypothesis-class ranking.
  Per-bucket and per-break-reason decomposition of who reaches terminal,
  who never does. Ranks R1-R4 candidates by V6 evidence weight.

Outputs all under ``eval_runs/phase5_design_e1_e2_e3_2026-05-13/``:
- ``e1_a6_grace_feasibility.json`` / ``e1_a6_grace_feasibility.md``
- ``e2_cable_drop_false_positive_audit.json`` / ``e2_cable_drop_false_positive_audit.md``
- ``e3_right_arm_asymmetry_ranking.json`` / ``e3_right_arm_asymmetry_ranking.md``
- ``convergence_memo.md`` (cross-cutting recommendation + GO/NO_GO)
- ``analysis_sha256.txt``

Bounds: TOUCH FORBIDDEN preserved. AR success criterion
``clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)`` unchanged. No production
claim. No standing-verdict change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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


# ---------- E1 A6 grace feasibility ----------


def e1_a6_grace_feasibility(records: list[dict]) -> dict[str, Any]:
    """Estimate A6 grace feasibility SR uplift upper bound.

    Methodology:
      - For each completion classified as ``terminal_entered`` but
        ``success=False``, look at ``terminal_hold_len`` reached before break.
      - For K_GRACE ∈ {3, 5, 10}, count completions where:
          terminal_hold_len + K_GRACE ≥ 5 (K=5 sustain target)
          AND the break reason is mechanistically recoverable
          (cable_drop, explosion, clamp_loss treated as recoverable under
           A6 grace + A2 disambiguation; unspecified / timeout treated as not
           recoverable).
      - Compute SR uplift upper bound = (recoverable_almost_success / total_completions).
    """
    arms = sorted({r["arm"] for r in records})
    seeds = sorted({int(r["seed"]) for r in records})
    recoverable_reasons = {"cable_drop", "explosion", "clamp_loss"}
    out: dict[str, Any] = {
        "methodology": (
            "For each (seed, arm) completion with terminal_entered=True and "
            "success=False, count near-miss recoveries where "
            "terminal_hold_len + K_GRACE >= 5 AND break_reason in "
            "{cable_drop, explosion, clamp_loss}. SR uplift upper bound = "
            "near_miss_count / total_completions."
        ),
        "k_grace_values": [3, 5, 10],
        "results_per_seed_arm": {},
        "results_per_arm": {},
        "caveats": [
            "Upper bound: assumes EVERY near-miss recoverable break is fully recovered by A6 grace.",
            "Lower bound (no recovery): 0pp SR uplift.",
            "True benefit depends on per-step recovery probability (requires per-step data not in V6).",
            "Does not account for A6 grace masking real cable drops as false positives.",
        ],
    }

    per_arm_aggregate: dict[str, Counter] = defaultdict(Counter)
    per_arm_total: Counter = Counter()
    per_arm_success: Counter = Counter()

    for seed in seeds:
        for arm in arms:
            recs = [
                r
                for r in records
                if int(r["seed"]) == seed and r["arm"] == arm
            ]
            total = len(recs)
            successes = sum(1 for r in recs if r["success"])
            terminal_entered = [r for r in recs if r.get("terminal_entered")]
            non_success_terminal = [r for r in terminal_entered if not r["success"]]

            k_grace_counts: dict[int, int] = {}
            for k_grace in [3, 5, 10]:
                cnt = 0
                for r in non_success_terminal:
                    hold = int(r.get("terminal_hold_len", 0))
                    br = r.get("terminal_break_reason", "")
                    if hold + k_grace >= 5 and br in recoverable_reasons:
                        cnt += 1
                k_grace_counts[k_grace] = cnt

            per_arm_total[arm] += total
            per_arm_success[arm] += successes
            for k_grace, cnt in k_grace_counts.items():
                per_arm_aggregate[arm][k_grace] += cnt

            out["results_per_seed_arm"][f"seed{seed}_{arm}"] = {
                "total_completions": total,
                "successes": successes,
                "baseline_sr": successes / total if total else 0.0,
                "terminal_entered_count": len(terminal_entered),
                "non_success_terminal_count": len(non_success_terminal),
                "a6_recoverable_count_by_k_grace": k_grace_counts,
                "a6_upper_bound_sr_uplift_pp_by_k_grace": {
                    k: 100.0 * c / total if total else 0.0
                    for k, c in k_grace_counts.items()
                },
            }

    for arm in arms:
        total = per_arm_total[arm]
        success = per_arm_success[arm]
        out["results_per_arm"][arm] = {
            "total_completions": total,
            "successes": success,
            "baseline_sr": success / total if total else 0.0,
            "a6_recoverable_count_by_k_grace": dict(per_arm_aggregate[arm]),
            "a6_upper_bound_sr_uplift_pp_by_k_grace": {
                k: 100.0 * c / total if total else 0.0
                for k, c in per_arm_aggregate[arm].items()
            },
        }
    return out


# ---------- E2 cable_drop false-positive audit ----------


def e2_cable_drop_false_positive_audit(records: list[dict]) -> dict[str, Any]:
    """Audit cable_drop break_reason for false-positive structural signature.

    False-positive signature (per AR bug history reference):
      - ``terminal_break_reason == "cable_drop"`` AND
      - ``right_clamp == True`` AND ``left_hold == True`` at termination
      → both arms still indicate hold, but cable "dropped" → highly unusual,
        consistent with false-positive cable_drop signal.

    True-positive signature:
      - cable_drop AND ``cable_not_dropped == False`` AND
      - ``right_clamp == False`` AND ``left_hold == False``
      → both arms lost contact, consistent with physical drop.

    Mixed (single-arm holding) is reported separately as "partial-grip drop"
    — ambiguous, requires per-step data to disambiguate.
    """
    arms = sorted({r["arm"] for r in records})
    out: dict[str, Any] = {
        "methodology": (
            "For cable_drop records: classify by (right_clamp, left_hold) "
            "state at termination. Both-True = likely false-positive. "
            "Both-False = likely physical drop. Single-True = ambiguous "
            "(partial-grip drop). Reports rates per arm."
        ),
        "results_per_arm": {},
        "caveats": [
            "Without per-step cable_pos_z trajectory, classification is structural-only.",
            "AR bug history references prior cable_drop false-positive incidents (see LL-AerialRegrasp-BugHistory.md).",
            "Estimate is a STRUCTURAL false-positive rate; true rate may differ.",
        ],
    }

    for arm in arms:
        cable_drop_recs = [
            r
            for r in records
            if r.get("terminal_break_reason") == "cable_drop"
            and r["arm"] == arm
        ]
        likely_fp = 0
        likely_tp = 0
        partial_grip = 0
        for r in cable_drop_recs:
            rc = bool(r.get("right_clamp", False))
            lh = bool(r.get("left_hold", False))
            if rc and lh:
                likely_fp += 1
            elif not rc and not lh:
                likely_tp += 1
            else:
                partial_grip += 1
        total = len(cable_drop_recs)
        out["results_per_arm"][arm] = {
            "total_cable_drop_events": total,
            "likely_false_positive_count": likely_fp,
            "likely_false_positive_rate": likely_fp / total if total else 0.0,
            "likely_true_positive_count": likely_tp,
            "likely_true_positive_rate": likely_tp / total if total else 0.0,
            "partial_grip_ambiguous_count": partial_grip,
            "partial_grip_ambiguous_rate": partial_grip / total if total else 0.0,
        }
    return out


# ---------- E3 right-arm asymmetry hypothesis-class ranking ----------


def e3_right_arm_asymmetry_ranking(records: list[dict]) -> dict[str, Any]:
    """Rank right-arm asymmetry hypothesis classes R1-R4 by V6 evidence.

    Hypothesis classes:
      R1 (IK target misalignment): right_clamp consistently False at termination
        regardless of episode progress (would manifest as right_clamp=False
        even in terminal_hold_len>0 records).
      R2 (closing logic authority): right_clamp transient — sometimes True
        sometimes False within episodes (V6 has only termination snapshot,
        so cannot evaluate transient).
      R3 (topology asymmetry): control vs intervention symmetric in
        right_clamp-non-terminal pattern → topology-level issue, not
        intervention-specific.
      R4 (control timing): right_clamp success rate correlates with episode
        duration / step count — slow control update affects right more.

    With only completion-level summary in V6, ranking is based on:
      - Distribution of (right_clamp, left_hold) state in non-success
      - Comparison between control and intervention arms
      - Step-count distribution for right_clamp=True vs False completions
    """
    arms = sorted({r["arm"] for r in records})
    out: dict[str, Any] = {
        "methodology": (
            "Per-arm classification of non-success completions by "
            "(right_clamp, left_hold) state and step number. Ranks R1-R4 "
            "hypothesis classes by evidence strength from V6 summary data."
        ),
        "hypothesis_classes": {
            "R1": "Right-arm IK target persistently misaligned at terminal phase",
            "R2": "Right-arm closing logic has authority issue (transient or insufficient)",
            "R3": "Topology asymmetry (fixed-left/right-auto-close design)",
            "R4": "Right-arm control update timing different from left",
        },
        "results_per_arm": {},
        "evidence_summary": {},
        "ranking": [],
        "caveats": [
            "V6 records are completion snapshots, not per-step trajectories.",
            "R2 (transient closing) requires per-step right_clamp signal to evaluate fully.",
            "R4 (control timing) requires per-step joint velocity to evaluate fully.",
            "R1 (IK target) can be partially inferred from termination state distribution.",
            "R3 (topology) can be inferred from control vs intervention symmetry.",
        ],
    }

    # Per-arm decomposition (this also done in Phase 4 #3 H1, replicated here for E3 self-contained)
    for arm in arms:
        recs = [r for r in records if r["arm"] == arm]
        non_success = [r for r in recs if not r["success"]]
        total = len(recs)
        n_non_success = len(non_success)

        # state distribution in non_success
        rc_true_lh_true = sum(1 for r in non_success if r.get("right_clamp") and r.get("left_hold"))
        rc_true_lh_false = sum(1 for r in non_success if r.get("right_clamp") and not r.get("left_hold"))
        rc_false_lh_true = sum(1 for r in non_success if not r.get("right_clamp") and r.get("left_hold"))
        rc_false_lh_false = sum(1 for r in non_success if not r.get("right_clamp") and not r.get("left_hold"))

        # step distribution: right_clamp=True vs False at termination
        rc_true_steps = [r.get("step", 0) for r in non_success if r.get("right_clamp")]
        rc_false_steps = [r.get("step", 0) for r in non_success if not r.get("right_clamp")]
        rc_true_mean_step = sum(rc_true_steps) / len(rc_true_steps) if rc_true_steps else 0
        rc_false_mean_step = sum(rc_false_steps) / len(rc_false_steps) if rc_false_steps else 0

        # right_clamp success rate (in success cases right_clamp must be True per success criterion)
        success_recs = [r for r in recs if r["success"]]
        success_rc_rate = (
            sum(1 for r in success_recs if r.get("right_clamp")) / len(success_recs)
            if success_recs
            else 0.0
        )
        non_success_rc_rate = (
            sum(1 for r in non_success if r.get("right_clamp")) / n_non_success
            if n_non_success
            else 0.0
        )

        out["results_per_arm"][arm] = {
            "total_completions": total,
            "non_success_count": n_non_success,
            "state_distribution_non_success": {
                "rc_T_lh_T": rc_true_lh_true,
                "rc_T_lh_F": rc_true_lh_false,
                "rc_F_lh_T": rc_false_lh_true,
                "rc_F_lh_F": rc_false_lh_false,
            },
            "rc_True_rate_non_success": non_success_rc_rate,
            "rc_True_rate_success": success_rc_rate,
            "right_clamp_asymmetry_pp": (success_rc_rate - non_success_rc_rate) * 100,
            "step_distribution_at_termination": {
                "rc_True_mean_step": rc_true_mean_step,
                "rc_False_mean_step": rc_false_mean_step,
                "rc_True_count": len(rc_true_steps),
                "rc_False_count": len(rc_false_steps),
            },
        }

    # Evidence summary cross-arm
    control = out["results_per_arm"].get("control", {})
    intervention_keys = [k for k in out["results_per_arm"] if k != "control"]
    intervention_arm_name = intervention_keys[0] if intervention_keys else None
    intervention = out["results_per_arm"].get(intervention_arm_name, {}) if intervention_arm_name else {}

    if control and intervention:
        control_rc_rate = control.get("rc_True_rate_non_success", 0)
        intervention_rc_rate = intervention.get("rc_True_rate_non_success", 0)
        rc_rate_ratio = (
            intervention_rc_rate / control_rc_rate if control_rc_rate > 0 else float("inf")
        )

        out["evidence_summary"] = {
            "control_rc_rate_non_success": control_rc_rate,
            "intervention_rc_rate_non_success": intervention_rc_rate,
            "rc_rate_ratio_intervention_over_control": rc_rate_ratio,
            "interpretation": (
                "Intervention arm changes hold-break logic (B-A5.2); right_clamp "
                "behavior similar between arms = consistent with R3 topology (not "
                "intervention-specific). If control_rc_rate ≈ intervention_rc_rate "
                "≈ 0, R1/R3 likely dominant over R2/R4."
            ),
        }

    # Ranking heuristic based on V6 evidence
    if control:
        rc_T_lh_T = control["state_distribution_non_success"]["rc_T_lh_T"]
        rc_T_lh_F = control["state_distribution_non_success"]["rc_T_lh_F"]
        rc_F_lh_T = control["state_distribution_non_success"]["rc_F_lh_T"]
        rc_F_lh_F = control["state_distribution_non_success"]["rc_F_lh_F"]
        total_ns = control["non_success_count"]
        # rc_F means right_clamp never reached terminal in non_success
        rc_never_terminal_frac = (
            (rc_F_lh_T + rc_F_lh_F) / total_ns if total_ns > 0 else 0.0
        )
        # Strong evidence: rc_never_terminal_frac ≈ 1 (0.999+) suggests R1 dominant
        rank_score: dict[str, float] = {
            "R1": 0.0,
            "R2": 0.0,
            "R3": 0.0,
            "R4": 0.0,
        }
        if rc_never_terminal_frac > 0.99:
            rank_score["R1"] += 1.0  # strong R1 signal
            rank_score["R3"] += 0.8  # consistent with topology
        if intervention and rc_rate_ratio > 0.5 and rc_rate_ratio < 2.0:
            rank_score["R3"] += 0.5  # cross-arm consistency
        # R2 / R4 can't be evaluated with completion-only data
        rank_score["R2"] += 0.1  # uncertain
        rank_score["R4"] += 0.1  # uncertain
        ranked = sorted(rank_score.items(), key=lambda kv: -kv[1])
        out["ranking"] = [
            {"rank": i + 1, "class": k, "score": v} for i, (k, v) in enumerate(ranked)
        ]
        out["rc_never_terminal_frac_control"] = rc_never_terminal_frac
    return out


def convergence_recommendation(e1: dict, e2: dict, e3: dict) -> dict[str, Any]:
    """Cross-cutting convergence recommendation + GO/NO_GO."""
    out: dict[str, Any] = {}
    control_e1 = e1["results_per_arm"].get("control", {})
    a6_upper_pp = control_e1.get("a6_upper_bound_sr_uplift_pp_by_k_grace", {})
    control_e2 = e2["results_per_arm"].get("control", {})
    fp_rate = control_e2.get("likely_false_positive_rate", 0.0)
    e3_top = e3.get("ranking", [{}])[0].get("class", "?")

    # Recommendation logic
    a6_meaningful = any(pp >= 3.0 for pp in a6_upper_pp.values())
    fp_significant = fp_rate >= 0.05
    r1_or_r3_dominant = e3_top in ("R1", "R3")

    if a6_meaningful and r1_or_r3_dominant:
        recommendation = "split-implementation-gate"
        rationale = (
            "A6 grace shows meaningful SR uplift upper bound. Right-arm "
            "asymmetry hypothesis R1/R3 dominant (structural). Both surfaces "
            "warrant Phase 5 implementation but should be gated separately."
        )
    elif a6_meaningful and not r1_or_r3_dominant:
        recommendation = "A6-first-implementation"
        rationale = (
            "A6 grace shows meaningful SR uplift. Right-arm asymmetry not "
            "clearly structural (R2/R4 uncertain). A6-first design phase has "
            "stronger evidence."
        )
    elif not a6_meaningful and r1_or_r3_dominant:
        recommendation = "right-arm-first-implementation"
        rationale = (
            "A6 grace SR uplift below 3pp threshold. Right-arm asymmetry "
            "R1/R3 structural. Address right-arm first."
        )
    else:
        recommendation = "neither-strong-enough"
        rationale = (
            "Neither A6 nor right-arm hypothesis shows strong evidence. "
            "Additional design phase or different mechanism investigation "
            "needed."
        )

    # GO/NO_GO for asking Phase 5 implementation disposition
    if recommendation == "neither-strong-enough":
        go_no_go = "NO_GO_request_implementation_disposition"
        go_no_go_rationale = (
            "Evidence too weak to support Phase 5 implementation request. "
            "Recommend additional design phase or hypothesis reformulation."
        )
    else:
        go_no_go = "GO_request_implementation_disposition"
        go_no_go_rationale = (
            f"Recommendation '{recommendation}' supported by E1/E2/E3 evidence. "
            "Phase 5 implementation disposition request is justified, scoped per "
            "the recommendation above."
        )

    out["recommendation"] = recommendation
    out["rationale"] = rationale
    out["go_no_go"] = go_no_go
    out["go_no_go_rationale"] = go_no_go_rationale
    out["evidence_summary"] = {
        "a6_grace_max_pp_uplift_control": max(a6_upper_pp.values()) if a6_upper_pp else 0,
        "cable_drop_structural_fp_rate_control": fp_rate,
        "right_arm_top_hypothesis": e3_top,
    }
    out["bounds_preserved"] = [
        "no Phase 5 implementation this design phase",
        "no GPU compute",
        "no rollout / training / checkpoint mutation",
        "no combined H1+H4+H8 launch",
        "no production claim",
        "no standing-verdict change",
        "AR success criterion clamp(R) ∧ cable_not_dropped ∧ sustained(K=5) unchanged",
        "8 standing verdicts LOCKED unchanged",
        "IC LCB95 canonical 37.422% unchanged",
        "WM-G2 production NO_GO preserved",
        "Q1 (c) mixed unchanged",
    ]
    return out


# ---------- main ----------


def write_e1_md(out_dir: Path, e1: dict) -> Path:
    md = ["# AR Phase 5 E1 — A6 Grace Feasibility Post-Hoc Analysis", ""]
    md.append(
        "Read-only analysis on V6 artifacts. Computes upper-bound SR uplift "
        "from A6 termination-ordering grace assuming every near-miss "
        "recoverable break (cable_drop / explosion / clamp_loss) is fully "
        "recovered within the grace window K_GRACE ∈ {3, 5, 10}."
    )
    md.append("")
    md.append("## Methodology")
    md.append("")
    md.append(e1["methodology"])
    md.append("")
    md.append("## Per-arm aggregate results")
    md.append("")
    md.append("| arm | total | success | baseline SR | A6 K=3 uplift (pp) | K=5 uplift (pp) | K=10 uplift (pp) |")
    md.append("|-----|-------|---------|-------------|---------------------|-----------------|------------------|")
    for arm, d in sorted(e1["results_per_arm"].items()):
        upl = d["a6_upper_bound_sr_uplift_pp_by_k_grace"]
        md.append(
            f"| {arm} | {d['total_completions']} | {d['successes']} | "
            f"{d['baseline_sr']:.4f} | {upl.get(3, 0):.3f} | {upl.get(5, 0):.3f} | {upl.get(10, 0):.3f} |"
        )
    md.append("")
    md.append("## Per-seed-arm detail")
    md.append("")
    md.append("| key | total | success | baseline SR | K=3 (pp) | K=5 (pp) | K=10 (pp) |")
    md.append("|-----|-------|---------|-------------|----------|----------|-----------|")
    for key, d in sorted(e1["results_per_seed_arm"].items()):
        upl = d["a6_upper_bound_sr_uplift_pp_by_k_grace"]
        md.append(
            f"| {key} | {d['total_completions']} | {d['successes']} | "
            f"{d['baseline_sr']:.4f} | {upl.get(3, 0):.3f} | {upl.get(5, 0):.3f} | {upl.get(10, 0):.3f} |"
        )
    md.append("")
    md.append("## Caveats")
    for c in e1["caveats"]:
        md.append(f"- {c}")
    md.append("")
    path = out_dir / "e1_a6_grace_feasibility.md"
    path.write_text("\n".join(md))
    return path


def write_e2_md(out_dir: Path, e2: dict) -> Path:
    md = ["# AR Phase 5 E2 — cable_drop False-Positive Audit", ""]
    md.append(
        "Read-only structural classification of cable_drop events in V6 "
        "artifacts. Identifies cable_drop records that have (right_clamp ∧ "
        "left_hold) True at termination — a structural false-positive "
        "signature consistent with prior AR bug history."
    )
    md.append("")
    md.append("## Methodology")
    md.append("")
    md.append(e2["methodology"])
    md.append("")
    md.append("## Per-arm results")
    md.append("")
    md.append("| arm | total cable_drop | likely false-positive | FP rate | likely true-positive | TP rate | partial-grip ambig | ambig rate |")
    md.append("|-----|-------------------|------------------------|---------|------------------------|---------|---------------------|------------|")
    for arm, d in sorted(e2["results_per_arm"].items()):
        md.append(
            f"| {arm} | {d['total_cable_drop_events']} | {d['likely_false_positive_count']} | "
            f"{d['likely_false_positive_rate']:.4f} | {d['likely_true_positive_count']} | "
            f"{d['likely_true_positive_rate']:.4f} | {d['partial_grip_ambiguous_count']} | "
            f"{d['partial_grip_ambiguous_rate']:.4f} |"
        )
    md.append("")
    md.append("## Caveats")
    for c in e2["caveats"]:
        md.append(f"- {c}")
    md.append("")
    path = out_dir / "e2_cable_drop_false_positive_audit.md"
    path.write_text("\n".join(md))
    return path


def write_e3_md(out_dir: Path, e3: dict) -> Path:
    md = ["# AR Phase 5 E3 — Right-Arm Asymmetry Hypothesis-Class Ranking", ""]
    md.append(
        "Read-only analysis of right-arm asymmetric failure in V6 artifacts. "
        "Right_clamp NEVER reaches terminal in non-success cases (per Phase 4 #3 H1 Q4). "
        "Ranks NEW hypothesis classes R1-R4 by V6 evidence."
    )
    md.append("")
    md.append("## Hypothesis classes")
    md.append("")
    for k, v in e3["hypothesis_classes"].items():
        md.append(f"- **{k}**: {v}")
    md.append("")
    md.append("## Per-arm decomposition")
    md.append("")
    md.append("| arm | total | non_success | rc_T_lh_T | rc_T_lh_F | rc_F_lh_T | rc_F_lh_F | rc_True_non_success_rate | success_rc_rate | rc_asym_pp |")
    md.append("|-----|-------|-------------|------------|------------|-----------|-----------|--------------------------|-----------------|------------|")
    for arm, d in sorted(e3["results_per_arm"].items()):
        sd = d["state_distribution_non_success"]
        md.append(
            f"| {arm} | {d['total_completions']} | {d['non_success_count']} | "
            f"{sd['rc_T_lh_T']} | {sd['rc_T_lh_F']} | {sd['rc_F_lh_T']} | {sd['rc_F_lh_F']} | "
            f"{d['rc_True_rate_non_success']:.4f} | {d['rc_True_rate_success']:.4f} | "
            f"{d['right_clamp_asymmetry_pp']:.2f} |"
        )
    md.append("")
    md.append("## Evidence summary")
    md.append("")
    if e3.get("evidence_summary"):
        es = e3["evidence_summary"]
        md.append(f"- Control right_clamp rate in non_success: **{es['control_rc_rate_non_success']:.4f}**")
        md.append(f"- Intervention right_clamp rate in non_success: **{es['intervention_rc_rate_non_success']:.4f}**")
        md.append(f"- Ratio intervention/control: {es['rc_rate_ratio_intervention_over_control']:.4f}")
        md.append(f"- Interpretation: {es['interpretation']}")
    md.append("")
    md.append(f"- rc_never_terminal_frac (control non_success): **{e3.get('rc_never_terminal_frac_control', 0):.4f}**")
    md.append("")
    md.append("## Ranking")
    md.append("")
    md.append("| rank | class | score |")
    md.append("|------|-------|-------|")
    for r in e3.get("ranking", []):
        md.append(f"| {r['rank']} | {r['class']} | {r['score']:.2f} |")
    md.append("")
    md.append("## Caveats")
    for c in e3["caveats"]:
        md.append(f"- {c}")
    md.append("")
    path = out_dir / "e3_right_arm_asymmetry_ranking.md"
    path.write_text("\n".join(md))
    return path


def write_convergence_md(out_dir: Path, conv: dict, e1: dict, e2: dict, e3: dict) -> Path:
    md = ["# AR Phase 5 Convergence Memo — E1+E2+E3 cross-cutting analysis", ""]
    md.append(
        "Per Rs代行 disposition 2026-05-13 05:50 ACK "
        "`T_ROOT_COORD_P5_DESIGN_READINESS_ACK_20260513_0540 root` option (α) "
        "split-track design-only authorization. This memo synthesizes E1 + "
        "E2 + E3 evidence and provides convergence recommendation + GO/NO_GO "
        "for next Phase 5 implementation disposition request."
    )
    md.append("")
    md.append("## Required return items")
    md.append("")
    md.append("### 1. E1 result")
    md.append("")
    md.append(
        f"A6 grace maximum SR uplift (control, upper bound): **{conv['evidence_summary']['a6_grace_max_pp_uplift_control']:.3f}pp**"
    )
    md.append("")
    for arm, d in sorted(e1["results_per_arm"].items()):
        upl = d["a6_upper_bound_sr_uplift_pp_by_k_grace"]
        md.append(
            f"- {arm}: baseline SR {d['baseline_sr']:.4f}, A6 K=5 upper-bound uplift {upl.get(5, 0):.3f}pp, K=10 {upl.get(10, 0):.3f}pp"
        )
    md.append("")
    md.append("### 2. E2 false-positive estimate")
    md.append("")
    md.append(
        f"Cable_drop structural false-positive rate (control): **{conv['evidence_summary']['cable_drop_structural_fp_rate_control']:.4f}**"
    )
    md.append("")
    for arm, d in sorted(e2["results_per_arm"].items()):
        md.append(
            f"- {arm}: total cable_drop {d['total_cable_drop_events']}, "
            f"likely FP {d['likely_false_positive_count']} ({d['likely_false_positive_rate']:.4f}), "
            f"likely TP {d['likely_true_positive_count']} ({d['likely_true_positive_rate']:.4f}), "
            f"partial-grip ambig {d['partial_grip_ambiguous_count']} ({d['partial_grip_ambiguous_rate']:.4f})"
        )
    md.append("")
    md.append("### 3. E3 hypothesis-class ranking")
    md.append("")
    md.append("| rank | class | score |")
    md.append("|------|-------|-------|")
    for r in e3.get("ranking", []):
        md.append(f"| {r['rank']} | {r['class']} | {r['score']:.2f} |")
    md.append("")
    md.append(
        f"Top hypothesis: **{conv['evidence_summary']['right_arm_top_hypothesis']}**"
    )
    md.append("")
    md.append("### 4. Convergence recommendation")
    md.append("")
    md.append(f"**Recommendation**: `{conv['recommendation']}`")
    md.append("")
    md.append(f"Rationale: {conv['rationale']}")
    md.append("")
    md.append("### 5. GO/NO_GO for asking next Phase 5 implementation disposition")
    md.append("")
    md.append(f"**Verdict**: `{conv['go_no_go']}`")
    md.append("")
    md.append(f"Rationale: {conv['go_no_go_rationale']}")
    md.append("")
    md.append("## Bounds preserved")
    for b in conv["bounds_preserved"]:
        md.append(f"- {b}")
    md.append("")
    path = out_dir / "convergence_memo.md"
    path.write_text("\n".join(md))
    return path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--v6_samples",
        type=Path,
        default=Path("eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json"),
    )
    p.add_argument(
        "--out_dir",
        type=Path,
        default=Path("eval_runs/phase5_design_e1_e2_e3_2026-05-13"),
    )
    args = p.parse_args()

    if not args.v6_samples.is_file():
        print(f"ERROR: missing V6 samples at {args.v6_samples}", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[load] V6 samples from {args.v6_samples}")
    t0 = time.time()
    with args.v6_samples.open() as f:
        data = json.load(f)
    records = data.get("records", [])
    print(f"[load] {len(records)} records in {time.time() - t0:.1f}s")

    print("[E1] A6 grace feasibility…")
    e1 = e1_a6_grace_feasibility(records)
    (args.out_dir / "e1_a6_grace_feasibility.json").write_text(
        json.dumps(e1, indent=2, sort_keys=True, default=str)
    )
    write_e1_md(args.out_dir, e1)

    print("[E2] cable_drop false-positive audit…")
    e2 = e2_cable_drop_false_positive_audit(records)
    (args.out_dir / "e2_cable_drop_false_positive_audit.json").write_text(
        json.dumps(e2, indent=2, sort_keys=True)
    )
    write_e2_md(args.out_dir, e2)

    print("[E3] right-arm asymmetry hypothesis-class ranking…")
    e3 = e3_right_arm_asymmetry_ranking(records)
    (args.out_dir / "e3_right_arm_asymmetry_ranking.json").write_text(
        json.dumps(e3, indent=2, sort_keys=True, default=str)
    )
    write_e3_md(args.out_dir, e3)

    print("[converge] convergence memo + GO/NO_GO…")
    conv = convergence_recommendation(e1, e2, e3)
    (args.out_dir / "convergence_recommendation.json").write_text(
        json.dumps(conv, indent=2, sort_keys=True)
    )
    write_convergence_md(args.out_dir, conv, e1, e2, e3)

    print("[sha] hashing outputs…")
    sha_lines = []
    for p in [
        args.v6_samples,
        args.out_dir / "e1_a6_grace_feasibility.json",
        args.out_dir / "e1_a6_grace_feasibility.md",
        args.out_dir / "e2_cable_drop_false_positive_audit.json",
        args.out_dir / "e2_cable_drop_false_positive_audit.md",
        args.out_dir / "e3_right_arm_asymmetry_ranking.json",
        args.out_dir / "e3_right_arm_asymmetry_ranking.md",
        args.out_dir / "convergence_recommendation.json",
        args.out_dir / "convergence_memo.md",
    ]:
        sha_lines.append(f"{sha256_file(p)}  {p}")
    (args.out_dir / "analysis_sha256.txt").write_text("\n".join(sha_lines) + "\n")

    print(f"[done] outputs in {args.out_dir}")
    print(f"[done] recommendation: {conv['recommendation']}")
    print(f"[done] GO/NO_GO: {conv['go_no_go']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
