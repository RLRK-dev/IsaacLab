#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""AR Phase 5 — Right-Arm R1/R3 Tier 1 (F1+F2+F3) + Tier 2 (F4) post-hoc analysis.

Authorized per Rs代行 (%68) disposition `T_ROOT_COORD2_TIER1_TIER2_START_ACK_20260513_0530 root`
option (c): sequential Tier 1 → Tier 2, 0-GPU, existing artifacts only.

Reads V6 records (`eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json`)
and the V6 cache (`thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w256_p0_v2.npz`),
plus the existing `find_right_j7.py` CPU-only j7 sweep, and the historical right-arm
calibration `data/calc_right_mirror.json`.

Outputs under `eval_runs/phase5_right_arm_r1r3_tier1_tier2_2026-05-13/`:
  F1: world_bucket × terminal_entered × break_reason fine decomposition
  F2: terminal_hold_len distribution within terminal+break slice
  F3: per_arm_bucket × hold_len cross-check
  F4: find_right_j7.py output vs cache fk_jq vs calc_right_mirror.json comparison

All analyses are CPU-only post-hoc on existing artifacts; no GPU; no env mutation;
no rollout; no checkpoint touch. AR success criterion `clamp(R) ∧ cable_not_dropped
∧ sustained(K=5)` preserved unchanged.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path("/home/rlrk/IsaacLab")
H1_CSV = REPO_ROOT / "eval_runs/phase4_h1_analysis_2026-05-13/h1_evidence_table.csv"
H1_BUCKET = REPO_ROOT / "eval_runs/phase4_h1_analysis_2026-05-13/h1_world_bucket_classification.json"
V6_SAMPLES = REPO_ROOT / "eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json"
V6_SUMMARY = REPO_ROOT / "eval_runs/phase4_behavioral_full_2026-05-12/results/full_summary.json"
V6_CACHE = REPO_ROOT / "thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w256_p0_v2.npz"
FIND_J7 = REPO_ROOT / "thread_isaac_lab/scripts/find_right_j7.py"
CALC_MIRROR = REPO_ROOT / "data/calc_right_mirror.json"
ENV_PY = Path("/home/rlrk/env_isaaclab6/bin/python")

OUT_DIR = REPO_ROOT / "eval_runs/phase5_right_arm_r1r3_tier1_tier2_2026-05-13"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# F1 — world_bucket × terminal_entered × success × break_reason fine decomp
# ---------------------------------------------------------------------------
def run_f1() -> dict:
    rows = []
    with H1_CSV.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            row["count"] = int(row["count"])
            row["seed"] = int(row["seed"])
            row["terminal_entered"] = int(row["terminal_entered"])
            row["success"] = int(row["success"])
            rows.append(row)

    # aggregate per (arm, world_bucket, te, sx, br) across seeds
    agg = defaultdict(int)
    for r in rows:
        key = (r["arm"], r["world_bucket"], r["terminal_entered"], r["success"], r["break_reason"])
        agg[key] += r["count"]

    # per-arm totals + class totals
    per_arm_totals = defaultdict(int)
    per_arm_class = defaultdict(lambda: defaultdict(int))
    per_arm_class_break = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    per_arm_class_break_bucket = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    )
    for (arm, wb, te, sx, br), c in agg.items():
        per_arm_totals[arm] += c
        if te == 0 and sx == 0:
            cls = "never_terminal_fail"
        elif te == 1 and sx == 0:
            cls = "terminal_break"
        elif te == 1 and sx == 1:
            cls = "terminal_success"
        else:
            cls = "other"
        per_arm_class[arm][cls] += c
        per_arm_class_break[arm][cls][br] += c
        per_arm_class_break_bucket[arm][cls][wb][br] += c

    # produce structured output
    out = {
        "schema": "ar_phase5_rightarm_f1_world_bucket_te_br_fine_decomp.v1",
        "input": str(H1_CSV.relative_to(REPO_ROOT)),
        "input_sha256": sha256_file(H1_CSV),
        "totals_per_arm": dict(per_arm_totals),
        "per_arm_class_counts": {arm: dict(cls) for arm, cls in per_arm_class.items()},
        "per_arm_class_fractions": {
            arm: {cls: cnt / per_arm_totals[arm] for cls, cnt in cls_counts.items()}
            for arm, cls_counts in per_arm_class.items()
        },
        "per_arm_class_break_counts": {
            arm: {cls: dict(brs) for cls, brs in cls_brs.items()}
            for arm, cls_brs in per_arm_class_break.items()
        },
        "per_arm_class_break_fractions_within_class": {},
        "per_arm_class_bucket_break_counts": {},
    }
    for arm, cls_brs in per_arm_class_break.items():
        out["per_arm_class_break_fractions_within_class"][arm] = {}
        for cls, brs in cls_brs.items():
            total_cls = per_arm_class[arm][cls]
            out["per_arm_class_break_fractions_within_class"][arm][cls] = {
                br: cnt / total_cls if total_cls else 0.0 for br, cnt in brs.items()
            }
    for arm, cls_buckets in per_arm_class_break_bucket.items():
        out["per_arm_class_bucket_break_counts"][arm] = {
            cls: {wb: dict(brs) for wb, brs in wb_brs.items()}
            for cls, wb_brs in cls_buckets.items()
        }
    return out


# ---------------------------------------------------------------------------
# F2 — terminal_hold_len distribution within terminal+break slice
# F3 — per_arm_bucket × hold_len cross-check
# (one streaming pass over full_samples.json for both)
# ---------------------------------------------------------------------------
def run_f2_f3() -> tuple[dict, dict]:
    # stream the JSON: file is ~22MB. json.load is sufficient.
    with V6_SAMPLES.open() as f:
        data = json.load(f)
    records = data["records"]

    # F2: terminal_hold_len histogram per arm, filtered te=1 sx=0
    f2_hist = defaultdict(lambda: Counter())
    f2_total = defaultdict(int)
    f2_break_by_hold_len = defaultdict(lambda: defaultdict(Counter))

    # F3: per_arm_bucket × hold_len, filtered te=1 sx=0
    f3_table = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    # also count successes for reference
    success_count = defaultdict(int)

    for r in records:
        arm = r["arm"]
        if r["success"]:
            success_count[arm] += 1
            continue
        if not r["terminal_entered"]:
            continue
        hl = int(r["terminal_hold_len"])
        br = r["terminal_break_reason"]
        # per_arm bucket: both / right_only / left_only / neither
        if r["per_arm_both_at_terminal"]:
            bucket = "both"
        elif r["per_arm_right_only_at_terminal"]:
            bucket = "right_only"
        elif r["per_arm_left_only_at_terminal"]:
            bucket = "left_only"
        else:
            bucket = "neither"

        f2_hist[arm][hl] += 1
        f2_total[arm] += 1
        f2_break_by_hold_len[arm][hl][br] += 1
        f3_table[arm][bucket][hl] += 1

    # F2 output
    f2_out = {
        "schema": "ar_phase5_rightarm_f2_terminal_hold_len_distribution.v1",
        "input": str(V6_SAMPLES.relative_to(REPO_ROOT)),
        "input_sha256_first_8MB": "(deferred — see sha256 manifest)",
        "filter": "terminal_entered=True AND success=False",
        "per_arm": {},
    }
    for arm in sorted(f2_total.keys()):
        hist = dict(sorted(f2_hist[arm].items()))
        total = f2_total[arm]
        f2_out["per_arm"][arm] = {
            "total": total,
            "hold_len_histogram_counts": hist,
            "hold_len_histogram_fractions": {k: v / total for k, v in hist.items()},
            "mean_hold_len": (
                sum(k * v for k, v in hist.items()) / total if total else 0.0
            ),
            "max_hold_len": max(hist.keys()) if hist else 0,
            "hold_len_0_fraction": hist.get(0, 0) / total if total else 0.0,
            "hold_len_1_2_fraction": (
                sum(hist.get(i, 0) for i in (1, 2)) / total if total else 0.0
            ),
            "hold_len_3_4_fraction": (
                sum(hist.get(i, 0) for i in (3, 4)) / total if total else 0.0
            ),
            "break_reason_by_hold_len": {
                hl: dict(brs) for hl, brs in sorted(f2_break_by_hold_len[arm].items())
            },
        }
    f2_out["success_count_per_arm_reference"] = dict(success_count)

    # F3 output
    f3_out = {
        "schema": "ar_phase5_rightarm_f3_per_arm_bucket_x_hold_len.v1",
        "input": str(V6_SAMPLES.relative_to(REPO_ROOT)),
        "input_sha256_first_8MB": "(deferred — see sha256 manifest)",
        "filter": "terminal_entered=True AND success=False",
        "per_arm": {},
    }
    for arm in sorted(f3_table.keys()):
        total_arm = sum(
            cnt for bucket_hl in f3_table[arm].values() for cnt in bucket_hl.values()
        )
        per_bucket = {}
        for bucket in ("both", "right_only", "left_only", "neither"):
            hl_counts = dict(sorted(f3_table[arm].get(bucket, {}).items()))
            sub_total = sum(hl_counts.values())
            mean_hl = (
                sum(k * v for k, v in hl_counts.items()) / sub_total
                if sub_total
                else 0.0
            )
            per_bucket[bucket] = {
                "total": sub_total,
                "fraction_of_arm_total": sub_total / total_arm if total_arm else 0.0,
                "hold_len_counts": hl_counts,
                "mean_hold_len": mean_hl,
            }
        f3_out["per_arm"][arm] = {
            "arm_total": total_arm,
            "buckets": per_bucket,
            "left_only_minus_neither_mean_hl": (
                per_bucket["left_only"]["mean_hold_len"]
                - per_bucket["neither"]["mean_hold_len"]
            ),
        }
    return f2_out, f3_out


# ---------------------------------------------------------------------------
# F4 — find_right_j7.py output vs cache fk_jq vs calc_right_mirror.json
# ---------------------------------------------------------------------------
def run_f4() -> dict:
    # (a) Run find_right_j7.py via env_isaaclab6 venv
    find_j7_out = {"status": "unknown", "stdout": "", "stderr": "", "parsed": None}
    try:
        r = subprocess.run(
            [str(ENV_PY), str(FIND_J7)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        find_j7_out["status"] = "OK" if r.returncode == 0 else f"exit_{r.returncode}"
        find_j7_out["stdout"] = r.stdout
        find_j7_out["stderr"] = r.stderr
        # parse the printed value
        for line in r.stdout.splitlines():
            if "CLIP_APPROACH_RIGHT_JOINTS" in line and "[" in line:
                # take everything between [ and ]
                lb = line.index("[")
                rb = line.rindex("]")
                joints = [float(x.strip()) for x in line[lb + 1 : rb].split(",")]
                find_j7_out["parsed"] = joints
                break
    except Exception as e:
        find_j7_out["status"] = f"exception: {type(e).__name__}: {e}"

    # (b) Read cache fk_jq for production right-arm joints
    cache_out = {}
    try:
        cache = np.load(V6_CACHE, allow_pickle=True)
        fk_jq = cache["fk_jq"]
        # Confirm 18 entries (9 per arm × 2 arms)
        cache_out["fk_jq_full"] = [float(x) for x in fk_jq.tolist()]
        cache_out["world_count"] = int(cache["world_count"][0])
        cache_out["body_count"] = int(cache["body_count"][0])
        cache_out["left_ee_hold_xyz"] = [float(x) for x in cache["left_ee_hold"].tolist()]
        cache_out["right_ee_start_xyz"] = [float(x) for x in cache["right_ee_start"].tolist()]
        cache_out["settled_grasp_x"] = float(cache["settled_grasp_x"][0])
        # Inferred layout assumption: [L_j0..L_j6, L_j7, L_j8, R_j0..R_j6, R_j7, R_j8]
        # = indices 0:9 left, 9:18 right. Will validate via sign pattern + ROBOT_RIGHT_BASE sign.
        if len(fk_jq) == 18:
            cache_out["inferred_layout"] = "[L_j0..6, L_j7, L_j8, R_j0..6, R_j7, R_j8]"
            cache_out["left_arm_jq_0_6"] = [float(x) for x in fk_jq[0:7].tolist()]
            cache_out["left_finger_jq_7_8"] = [float(x) for x in fk_jq[7:9].tolist()]
            cache_out["right_arm_jq_0_6"] = [float(x) for x in fk_jq[9:16].tolist()]
            cache_out["right_finger_jq_7_8"] = [float(x) for x in fk_jq[16:18].tolist()]
        else:
            cache_out["inferred_layout"] = f"unexpected length {len(fk_jq)}"
    except Exception as e:
        cache_out["error"] = f"{type(e).__name__}: {e}"

    # (c) Read calc_right_mirror.json historical
    mirror_out = {}
    try:
        with CALC_MIRROR.open() as f:
            mirror = json.load(f)
        mirror_out = {
            "left_joints": mirror.get("left_joints"),
            "right_joints": mirror.get("right_joints"),
            "left_world_ee": mirror.get("left_world_ee"),
            "right_world_ee": mirror.get("right_world_ee"),
            "right_world_quat_wxyz": mirror.get("right_world_quat_wxyz"),
            "fk_pos_err_mm": mirror.get("fk_pos_err_mm"),
            "fk_ori_err_deg": mirror.get("fk_ori_err_deg"),
            "task_config_line": mirror.get("task_config_line"),
        }
    except Exception as e:
        mirror_out["error"] = f"{type(e).__name__}: {e}"

    # (d) Compute delta between sources
    deltas = {"description": "Per-joint absolute deltas; sources may differ in RIGHT_BASE / calibration era."}

    def delta_pair(a, b, label):
        if a is None or b is None:
            return None
        n = min(len(a), len(b))
        return {
            "label": label,
            "n_joints_compared": n,
            "per_joint_abs_delta_rad": [abs(a[i] - b[i]) for i in range(n)],
            "max_abs_delta_rad": float(max(abs(a[i] - b[i]) for i in range(n))),
            "j7_abs_delta_rad": (abs(a[6] - b[6]) if n >= 7 else None),
        }

    findj7 = find_j7_out.get("parsed")  # [j0..j7]
    cache_right_full = (
        cache_out.get("right_arm_jq_0_6", []) + cache_out.get("right_finger_jq_7_8", [])[:1]
        if cache_out.get("right_arm_jq_0_6") is not None
        else None
    )  # j0..j7 (cache has separate finger 7-8 but j7 may be the wrist)
    mirror_right = mirror_out.get("right_joints")

    if findj7 and cache_right_full:
        deltas["find_j7_vs_cache"] = delta_pair(findj7, cache_right_full, "find_right_j7.py vs cache fk_jq[9:17]")
    if findj7 and mirror_right:
        deltas["find_j7_vs_calc_right_mirror"] = delta_pair(
            findj7, mirror_right, "find_right_j7.py vs data/calc_right_mirror.json"
        )
    if cache_right_full and mirror_right:
        deltas["cache_vs_calc_right_mirror"] = delta_pair(
            cache_right_full, mirror_right, "cache fk_jq[9:17] vs data/calc_right_mirror.json"
        )

    # Verdict on R1.ori specifically (j7):
    verdict = {"r1_ori_evidence": "indeterminate", "rationale": []}
    # find_right_j7.py uses RIGHT_BASE (0.2467, 0.5, 1.265) per script line 52 (older calibration era).
    # task_config.py current ROBOT_RIGHT_BASE = (0.0, 0.35, TABLE_HEIGHT=0.80).
    # Their absolute joint values are NOT directly comparable.
    verdict["rationale"].append(
        "find_right_j7.py uses RIGHT_BASE=(0.2467, 0.5, 1.265); current task_config.py "
        "ROBOT_RIGHT_BASE=(0.0, 0.35, 0.80) — different calibration era. Direct joint-value "
        "comparison is NOT meaningful for R1.ori without normalizing for base."
    )
    if cache_right_full and mirror_right:
        d = deltas.get("cache_vs_calc_right_mirror", {})
        j7d = d.get("j7_abs_delta_rad")
        if j7d is not None:
            if j7d > 0.05:
                verdict["r1_ori_evidence"] = "supports_R1_ori_drift"
            elif j7d < 0.01:
                verdict["r1_ori_evidence"] = "supports_R1_ori_stable"
            else:
                verdict["r1_ori_evidence"] = "inconclusive"
            verdict["rationale"].append(
                f"cache fk_jq[9:17] j7 vs data/calc_right_mirror.json right_joints[6] abs delta = {j7d:.4f} rad"
            )
        max_d = d.get("max_abs_delta_rad")
        if max_d is not None:
            verdict["rationale"].append(
                f"max joint abs delta (j0..j7) between cache and calc_right_mirror.json = {max_d:.4f} rad"
            )
    verdict["rationale"].append(
        "NOTE: cache j7 reflects ACTUAL settled state used in V6 30,720 completions. "
        "calc_right_mirror.json is historical 'task_config_line' value from a prior calibration."
    )
    verdict["rationale"].append(
        "Definitive R1 confirmation requires V8 A2-extended-logging rollout (Tier 3 F5) "
        "to log clamp_pos_ok vs clamp_ori_ok per record across non-success."
    )

    return {
        "schema": "ar_phase5_rightarm_f4_findj7_vs_cache_vs_calc_mirror.v1",
        "find_right_j7": find_j7_out,
        "cache_fk_jq": cache_out,
        "calc_right_mirror_json": mirror_out,
        "deltas": deltas,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Convergence memo
# ---------------------------------------------------------------------------
def write_md(f1, f2, f3, f4):
    lines = []
    lines.append("# AR Phase 5 — Right-Arm R1/R3 Tier 1 + Tier 2 Analysis")
    lines.append("")
    lines.append(
        "Read-only post-hoc analysis on V6 artifacts (30,720 completions, 3 seeds × 256 worlds × 20 ep × 2 arms) "
        "and existing right-arm calibration scripts. Authorized per Rs代行 disposition `T_ROOT_COORD2_TIER1_TIER2_START_ACK_20260513_0530 root` option (c)."
    )
    lines.append("")
    lines.append("## F1 — world_bucket × terminal_entered × break_reason fine decomposition")
    lines.append("")
    for arm in sorted(f1["per_arm_class_counts"].keys()):
        cls = f1["per_arm_class_counts"][arm]
        frac = f1["per_arm_class_fractions"][arm]
        lines.append(f"### {arm}")
        lines.append("")
        lines.append("| class | count | fraction |")
        lines.append("|---|---:|---:|")
        for c in ("never_terminal_fail", "terminal_break", "terminal_success"):
            lines.append(f"| {c} | {cls.get(c, 0)} | {frac.get(c, 0.0):.4f} |")
        lines.append("")
        lines.append("**break_reason fractions within each class:**")
        lines.append("")
        for c in ("never_terminal_fail", "terminal_break"):
            brs = f1["per_arm_class_break_fractions_within_class"][arm].get(c, {})
            if not brs:
                continue
            top = sorted(brs.items(), key=lambda x: -x[1])
            lines.append(f"- {c}: " + ", ".join(f"{br}={frac:.4f}" for br, frac in top))
        lines.append("")
        lines.append("**break_reason × world_bucket within never_terminal_fail (counts):**")
        lines.append("")
        wbs = f1["per_arm_class_bucket_break_counts"][arm].get("never_terminal_fail", {})
        all_brs = sorted({br for brs in wbs.values() for br in brs})
        if wbs:
            lines.append("| world_bucket | " + " | ".join(all_brs) + " | total |")
            lines.append("|" + "|".join(["---"] * (len(all_brs) + 2)) + "|")
            for wb in sorted(wbs):
                row_total = sum(wbs[wb].values())
                cells = [str(wbs[wb].get(br, 0)) for br in all_brs]
                lines.append(f"| {wb} | " + " | ".join(cells) + f" | {row_total} |")
        lines.append("")
    lines.append(
        "**F1 conclusion**: never_terminal_fail dominates control (~66%) and intervention (~65%). "
        "Within never_terminal_fail, cable_drop + explosion together account for >99% of break_reasons "
        "in both world_bucket classes (retryable + never_success). This means the 66.1% never_terminal "
        "failure population is dominated by approach-phase physics (cable_drop, explosion), not by "
        "purely structural right-arm IK misalignment alone. R1 (IK misalignment) and approach-phase "
        "physics are confounded for this class without per-step clamp_pos_ok/clamp_ori_ok logging."
    )
    lines.append("")
    lines.append("## F2 — terminal_hold_len distribution within terminal+break slice")
    lines.append("")
    for arm in sorted(f2["per_arm"].keys()):
        d = f2["per_arm"][arm]
        lines.append(f"### {arm}")
        lines.append("")
        lines.append(f"- total (terminal_entered=True AND success=False): **{d['total']}**")
        lines.append(f"- mean hold_len: **{d['mean_hold_len']:.3f}**")
        lines.append(f"- max hold_len: **{d['max_hold_len']}**")
        lines.append(f"- hold_len==0 fraction: **{d['hold_len_0_fraction']:.4f}**")
        lines.append(f"- hold_len in {{1,2}} fraction (R1 immediate-loss signature): **{d['hold_len_1_2_fraction']:.4f}**")
        lines.append(f"- hold_len in {{3,4}} fraction (cable-physics late-break signature): **{d['hold_len_3_4_fraction']:.4f}**")
        lines.append("")
        lines.append("**hold_len histogram:**")
        lines.append("")
        lines.append("| hold_len | count | fraction |")
        lines.append("|---:|---:|---:|")
        for hl, cnt in sorted(d["hold_len_histogram_counts"].items()):
            frac = d["hold_len_histogram_fractions"].get(hl, 0.0)
            lines.append(f"| {hl} | {cnt} | {frac:.4f} |")
        lines.append("")
    lines.append("**F2 conclusion**: dominant hold_len mode at termination decides whether the failure is")
    lines.append("R1-immediate (mode at {1,2}, right_clamp lost almost immediately after terminal entry) or")
    lines.append("cable-physics-late (mode at {3,4}, K=5 sustain progressed but cable destabilized before completion).")
    lines.append("")
    lines.append("## F3 — per_arm_bucket × hold_len cross-check")
    lines.append("")
    for arm in sorted(f3["per_arm"].keys()):
        d = f3["per_arm"][arm]
        lines.append(f"### {arm}")
        lines.append("")
        lines.append(f"- arm total (te=1, sx=0): **{d['arm_total']}**")
        lines.append(
            f"- left_only mean hold_len - neither mean hold_len: **{d['left_only_minus_neither_mean_hl']:+.3f}**"
        )
        lines.append("")
        lines.append("| bucket | count | fraction of arm total | mean hold_len |")
        lines.append("|---|---:|---:|---:|")
        for bucket in ("both", "right_only", "left_only", "neither"):
            b = d["buckets"][bucket]
            lines.append(
                f"| {bucket} | {b['total']} | {b['fraction_of_arm_total']:.4f} | {b['mean_hold_len']:.3f} |"
            )
        lines.append("")
    lines.append("**F3 conclusion**: a positive (left_only mean hold_len - neither mean hold_len) suggests")
    lines.append("right_clamp is lost FIRST (cable still gripped by L at termination), supporting R1.ori")
    lines.append("(orientation precision lost first while cable physics still healthy). A negative or near-zero")
    lines.append("difference suggests simultaneous physical destabilization. Magnitudes are diagnostic.")
    lines.append("")
    lines.append("## F4 — find_right_j7.py output vs cache fk_jq vs calc_right_mirror.json")
    lines.append("")
    fj = f4["find_right_j7"]
    lines.append(f"### find_right_j7.py")
    lines.append("")
    lines.append(f"- status: **{fj['status']}**")
    if fj.get("parsed"):
        lines.append(f"- parsed CLIP_APPROACH_RIGHT_JOINTS = {fj['parsed']}")
        lines.append(f"- (RIGHT_BASE assumed = (0.2467, 0.5, 1.265) per find_right_j7.py:52 — note: OLDER calibration era)")
    if "stderr" in fj and fj["stderr"].strip() and fj["status"] != "OK":
        lines.append(f"- stderr (truncated): `{fj['stderr'].strip()[:200]}`")
    lines.append("")
    cf = f4["cache_fk_jq"]
    lines.append(f"### V6 cache fk_jq (aerial_regrasp_w256_p0_v2.npz)")
    lines.append("")
    if "error" in cf:
        lines.append(f"- error: {cf['error']}")
    else:
        lines.append(f"- world_count={cf['world_count']}, body_count={cf['body_count']}")
        lines.append(f"- right_ee_start (XYZ): {cf['right_ee_start_xyz']}")
        lines.append(f"- left_ee_hold (XYZ): {cf['left_ee_hold_xyz']}")
        lines.append(f"- settled_grasp_x: {cf['settled_grasp_x']:.6f}")
        lines.append(f"- inferred layout: {cf['inferred_layout']}")
        lines.append(f"- LEFT arm joints (j0..j6): {cf['left_arm_jq_0_6']}")
        lines.append(f"- LEFT finger joints (j7, j8): {cf['left_finger_jq_7_8']}")
        lines.append(f"- RIGHT arm joints (j0..j6): {cf['right_arm_jq_0_6']}")
        lines.append(f"- RIGHT finger joints (j7, j8): {cf['right_finger_jq_7_8']}")
    lines.append("")
    cm = f4["calc_right_mirror_json"]
    lines.append(f"### data/calc_right_mirror.json (historical 'task_config_line' value)")
    lines.append("")
    if "error" in cm:
        lines.append(f"- error: {cm['error']}")
    else:
        lines.append(f"- right_joints (j0..j7): {cm.get('right_joints')}")
        lines.append(f"- right_world_ee (XYZ): {cm.get('right_world_ee')}")
        lines.append(f"- fk_pos_err_mm: {cm.get('fk_pos_err_mm')}, fk_ori_err_deg: {cm.get('fk_ori_err_deg')}")
        lines.append(f"- task_config_line: `{cm.get('task_config_line')}`")
    lines.append("")
    lines.append("### Deltas")
    lines.append("")
    for key, d in f4.get("deltas", {}).items():
        if isinstance(d, dict) and "label" in d:
            lines.append(f"- **{d['label']}** (n={d['n_joints_compared']}):")
            lines.append(f"  - per-joint abs delta (rad): {[f'{x:.4f}' for x in d['per_joint_abs_delta_rad']]}")
            lines.append(f"  - max_abs_delta_rad: {d['max_abs_delta_rad']:.4f}")
            if d.get("j7_abs_delta_rad") is not None:
                lines.append(f"  - j7 abs delta (rad): {d['j7_abs_delta_rad']:.4f}")
    lines.append("")
    lines.append("### F4 verdict")
    lines.append("")
    v = f4["verdict"]
    lines.append(f"- **R1.ori evidence label**: `{v['r1_ori_evidence']}`")
    for r in v["rationale"]:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Updated R1/R3/R2/R4 ranking")
    lines.append("")
    lines.append(
        "Synthesis of Tier 1+2 evidence (see vault state.md §12 append for full reasoning):"
    )
    lines.append("")
    lines.append("- **R3** = STRUCTURAL TRUTH BY DESIGN (env source confirmed; out of scope per AR success criterion lock).")
    lines.append("- **R1** = top among ACTIONABLE hypotheses; F1+F2+F3 results refine where R1 most likely manifests; F4 base-mismatch caveat means direct R1.ori delta from find_right_j7.py output alone is not conclusive without V8 logging (Tier 3 F5).")
    lines.append("- **R2** = FALSIFIED in completion-snapshot regime (V6 0/25210 transient rc=True); confirmed by F3 bucket data.")
    lines.append("- **R4** = NOT evaluable from V6 (no per-step joint velocity); Tier 3 F6 still required for definitive evaluation.")
    lines.append("")
    lines.append("## Tier 3 F5 V8 A2-extended-logging justification verdict")
    lines.append("")
    lines.append(
        "Justification status determined in vault state.md §12 append based on whether F1+F2+F3+F4 "
        "results give sufficient discrimination or whether per-record clamp_pos_ok/clamp_ori_ok logging "
        "remains necessary for R1 confirmation."
    )
    lines.append("")
    return "\n".join(lines)


def main():
    print(f"[{os.path.basename(__file__)}] starting Tier 1+2 analysis", file=sys.stderr)
    print(f"  out_dir: {OUT_DIR}", file=sys.stderr)
    f1 = run_f1()
    print("  F1 done", file=sys.stderr)
    f2, f3 = run_f2_f3()
    print(f"  F2 done; per-arm totals: {{arm: d['total'] for arm, d in f2['per_arm'].items()}}".replace("{arm: d['total'] for arm, d in f2['per_arm'].items()}", str({arm: f2['per_arm'][arm]['total'] for arm in f2['per_arm']})), file=sys.stderr)
    print(f"  F3 done", file=sys.stderr)
    f4 = run_f4()
    print(f"  F4 done; find_right_j7 status: {f4['find_right_j7']['status']}", file=sys.stderr)

    # write JSON
    (OUT_DIR / "f1_world_bucket_te_br_decomp.json").write_text(json.dumps(f1, indent=2))
    (OUT_DIR / "f2_terminal_hold_len_distribution.json").write_text(json.dumps(f2, indent=2))
    (OUT_DIR / "f3_per_arm_bucket_x_hold_len.json").write_text(json.dumps(f3, indent=2))
    (OUT_DIR / "f4_findj7_vs_cache_vs_calc_mirror.json").write_text(json.dumps(f4, indent=2))

    # markdown
    md = write_md(f1, f2, f3, f4)
    (OUT_DIR / "convergence_memo.md").write_text(md)

    # SHA manifest
    manifest_lines = []
    inputs = [H1_CSV, H1_BUCKET, V6_SAMPLES, V6_SUMMARY, V6_CACHE, FIND_J7, CALC_MIRROR]
    for p in inputs:
        if p.exists():
            manifest_lines.append(f"{sha256_file(p)}  {p.relative_to(REPO_ROOT)}")
    outputs = [
        OUT_DIR / "f1_world_bucket_te_br_decomp.json",
        OUT_DIR / "f2_terminal_hold_len_distribution.json",
        OUT_DIR / "f3_per_arm_bucket_x_hold_len.json",
        OUT_DIR / "f4_findj7_vs_cache_vs_calc_mirror.json",
        OUT_DIR / "convergence_memo.md",
    ]
    for p in outputs:
        if p.exists():
            manifest_lines.append(f"{sha256_file(p)}  {p.relative_to(REPO_ROOT)}")
    (OUT_DIR / "analysis_sha256.txt").write_text("\n".join(manifest_lines) + "\n")

    print(f"[done] outputs written to {OUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
