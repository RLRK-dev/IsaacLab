#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""AR Phase 5 — Right-Arm η pre-V8 post-hoc analysis (η1 + η2 + η3 + η5-prelim).

Authorized per Rs代行 (%68) disposition `T_ROOT_COORD2_ETA_PRE_V8_START_ACK_20260513_0600 root`
modified-η: η1-η3 + η5 preliminary; η4 V7 verdict HELD per %67 ownership.

CPU-only post-hoc analysis on existing artifacts. No GPU, no env mutation, no rollout.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.spatial.transform import Rotation

ROOT = Path("/home/rlrk/IsaacLab")
OUT = ROOT / "eval_runs/phase5_right_arm_eta_pre_v8_2026-05-13"
OUT.mkdir(parents=True, exist_ok=True)

V6_SAMPLES = ROOT / "eval_runs/phase4_behavioral_full_2026-05-12/results/full_samples.json"
V6_SUMMARY = ROOT / "eval_runs/phase4_behavioral_full_2026-05-12/results/full_summary.json"
H1_CSV = ROOT / "eval_runs/phase4_h1_analysis_2026-05-13/h1_evidence_table.csv"
CACHE_NPZ = ROOT / "thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w256_p0_v2.npz"
FIND_J7 = ROOT / "thread_isaac_lab/scripts/find_right_j7.py"
E1_JSON = ROOT / "eval_runs/phase5_design_e1_e2_e3_2026-05-13/e1_a6_grace_feasibility.json"

# Current geometry (task_config.py:20-22)
TABLE_HEIGHT = 0.80
ROBOT_LEFT_BASE_CURRENT = (0.0, -0.35, TABLE_HEIGHT)
ROBOT_RIGHT_BASE_CURRENT = (0.0, 0.35, TABLE_HEIGHT)
# ROBOT_BASE_QUAT_WXYZ absent from current task_config.py, found in historical sources:
# checkpoints/20260104_0755_pre_joint_mode/task_config.py:60, golden_fix25n:67, etc. (all (0.7071,0,0.7071,0)).
ROBOT_BASE_QUAT_WXYZ_CURRENT = (0.7071, 0.0, 0.7071, 0.0)  # Y-axis +90 deg wall mount

# find_right_j7.py OLD calibration era (script lines 50-56)
RIGHT_BASE_OLD = (0.2467, 0.5, 1.265)
LEFT_BASE_OLD = (0.2467, -0.5, 1.265)
LEFT_JOINTS_FIND_RIGHT_J7 = [0.650477, 0.698145, 0.100584, -1.909314, -2.356371, 1.924273, 1.914357]
HAND_DOWN_QUAT_WXYZ = (0.0, 0.7071, 0.7071, 0.0)

JOINT_ORIGINS = [
    ([0, 0, 0], [0, 0, 0.333]),
    ([-np.pi / 2, 0, 0], [0, 0, 0]),
    ([np.pi / 2, 0, 0], [0, -0.316, 0]),
    ([np.pi / 2, 0, 0], [0.0825, 0, 0]),
    ([-np.pi / 2, 0, 0], [-0.0825, 0.384, 0]),
    ([np.pi / 2, 0, 0], [0, 0, 0]),
    ([np.pi / 2, 0, 0], [0.088, 0, 0]),
]
FIXED_ORIGINS = [
    ([0, 0, 0], [0, 0, 0.107]),
    ([0, 0, -np.pi / 4], [0, 0, 0]),
]


def rpy_to_matrix(rpy):
    return Rotation.from_euler("xyz", rpy).as_matrix()


def make_transform(R, t):
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def fk(joints):
    T = np.eye(4)
    for i in range(7):
        rpy, xyz = JOINT_ORIGINS[i]
        T = T @ make_transform(rpy_to_matrix(rpy), xyz) @ make_transform(rot_z(joints[i]), [0, 0, 0])
    for rpy, xyz in FIXED_ORIGINS:
        T = T @ make_transform(rpy_to_matrix(rpy), xyz)
    return T


def world_transform(joints, base_pos, base_quat_wxyz):
    T_local = fk(joints)
    q = base_quat_wxyz
    R = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
    T_base = make_transform(R, list(base_pos))
    return T_base @ T_local


HAND_DOWN_R = Rotation.from_quat(
    [HAND_DOWN_QUAT_WXYZ[1], HAND_DOWN_QUAT_WXYZ[2], HAND_DOWN_QUAT_WXYZ[3], HAND_DOWN_QUAT_WXYZ[0]]
).as_matrix()


def ori_err_deg(joints_7, base_pos, base_quat=ROBOT_BASE_QUAT_WXYZ_CURRENT):
    T = world_transform(joints_7, base_pos, base_quat)
    R_err = T[:3, :3].T @ HAND_DOWN_R
    trace = np.clip(np.trace(R_err), -1, 3)
    return float(np.degrees(np.arccos(np.clip((trace - 1) / 2, -1, 1))))


def find_optimal_j7(joints_0_6, base_pos, base_quat=ROBOT_BASE_QUAT_WXYZ_CURRENT):
    def err(j7):
        return ori_err_deg(list(joints_0_6) + [float(j7)], base_pos, base_quat)
    sweep = np.linspace(-2.8973, 2.8973, 1000)
    errs = np.array([err(j7) for j7 in sweep])
    idx = int(np.argmin(errs))
    coarse_j7 = float(sweep[idx])
    res = minimize_scalar(err, bounds=(coarse_j7 - 0.1, coarse_j7 + 0.1), method="bounded")
    return float(res.x), float(res.fun)


def mirror_j0_6(left_j0_6):
    return [-left_j0_6[0], left_j0_6[1], -left_j0_6[2], left_j0_6[3], -left_j0_6[4], left_j0_6[5]]


def sha256_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def run_eta1_eta2():
    cache = np.load(CACHE_NPZ, allow_pickle=True)
    fk_jq = cache["fk_jq"]  # shape (18,) = [L_j0..6, L_j7, L_j8, R_j0..6, R_j7, R_j8]
    cache_left_j0_6 = [float(x) for x in fk_jq[0:7].tolist()]
    cache_right_j0_7 = [float(x) for x in fk_jq[9:16].tolist()]  # j0..j7 (j7 = wrist index 15)
    cache_right_j7 = cache_right_j0_7[6]
    cache_left_ee_hold = [float(x) for x in cache["left_ee_hold"].tolist()]
    cache_right_ee_start = [float(x) for x in cache["right_ee_start"].tolist()]

    out = {
        "schema": "ar_phase5_rightarm_eta1_eta2_corrected_base.v1",
        "current_geometry": {
            "ROBOT_LEFT_BASE": list(ROBOT_LEFT_BASE_CURRENT),
            "ROBOT_RIGHT_BASE": list(ROBOT_RIGHT_BASE_CURRENT),
            "ROBOT_BASE_QUAT_WXYZ": list(ROBOT_BASE_QUAT_WXYZ_CURRENT),
            "source": "task_config.py:20-22 (bases); ROBOT_BASE_QUAT_WXYZ from historical golden_fix25n:67 (absent in current task_config.py but consistent across all sources)",
        },
        "old_find_right_j7_geometry": {
            "RIGHT_BASE": list(RIGHT_BASE_OLD),
            "LEFT_BASE": list(LEFT_BASE_OLD),
            "BASE_QUAT": list(ROBOT_BASE_QUAT_WXYZ_CURRENT),
            "source": "find_right_j7.py:52-53; same BASE_QUAT",
        },
        "v6_cache_settled": {
            "left_j0_6": cache_left_j0_6,
            "right_j0_7": cache_right_j0_7,
            "right_j7": cache_right_j7,
            "left_ee_hold_xyz": cache_left_ee_hold,
            "right_ee_start_xyz": cache_right_ee_start,
            "cache_sha256": sha256_file(CACHE_NPZ),
        },
    }

    # Reference: old find_right_j7 (sanity check FK)
    a0_right_j0_6 = mirror_j0_6(LEFT_JOINTS_FIND_RIGHT_J7[:6])
    a0_j7, a0_err = find_optimal_j7(a0_right_j0_6, RIGHT_BASE_OLD)

    # Variant a1: OLD find_right_j7 LEFT mirror at NEW current base
    a1_right_j0_6 = a0_right_j0_6
    a1_j7, a1_err = find_optimal_j7(a1_right_j0_6, ROBOT_RIGHT_BASE_CURRENT)

    # Variant a2: CACHE LEFT j0-j6 mirror at NEW current base (cache-conditional mirror)
    a2_right_j0_6 = mirror_j0_6(cache_left_j0_6)
    a2_j7, a2_err = find_optimal_j7(a2_right_j0_6, ROBOT_RIGHT_BASE_CURRENT)

    # Variant b: CACHE actual RIGHT j0-j6 + optimal j7 at NEW current base (DIRECT R1.ori test)
    cache_right_j0_6 = cache_right_j0_7[:6]
    b_j7, b_err = find_optimal_j7(cache_right_j0_6, ROBOT_RIGHT_BASE_CURRENT)

    # Variant c: cache as-is — ori_err to HAND_DOWN at current base AND old base
    c_err_new = ori_err_deg(cache_right_j0_7, ROBOT_RIGHT_BASE_CURRENT)
    c_err_old = ori_err_deg(cache_right_j0_7, RIGHT_BASE_OLD)

    # Compute world EE position for cache joints at current base
    T_cache_new = world_transform(cache_right_j0_7, ROBOT_RIGHT_BASE_CURRENT, ROBOT_BASE_QUAT_WXYZ_CURRENT)
    T_cache_old = world_transform(cache_right_j0_7, RIGHT_BASE_OLD, ROBOT_BASE_QUAT_WXYZ_CURRENT)
    cache_ee_pos_new = [float(x) for x in T_cache_new[:3, 3].tolist()]
    cache_ee_pos_old = [float(x) for x in T_cache_old[:3, 3].tolist()]

    out["eta1_variants"] = {
        "a0_old_LEFT_mirror_old_base_REFERENCE": {
            "description": "Re-run of find_right_j7.py at original geometry (sanity check FK implementation).",
            "left_j0_6": LEFT_JOINTS_FIND_RIGHT_J7[:6],
            "mirror_right_j0_6": a0_right_j0_6,
            "base_pos": list(RIGHT_BASE_OLD),
            "optimal_j7_rad": a0_j7,
            "ori_err_deg_at_optimal": a0_err,
            "expected_per_find_right_j7": "j7 ≈ 2.7746 rad, ori_err ≈ 0.079 deg",
        },
        "a1_old_LEFT_mirror_new_base": {
            "description": "OLD find_right_j7 LEFT mirror at NEW current ROBOT_RIGHT_BASE.",
            "left_j0_6": LEFT_JOINTS_FIND_RIGHT_J7[:6],
            "mirror_right_j0_6": a1_right_j0_6,
            "base_pos": list(ROBOT_RIGHT_BASE_CURRENT),
            "optimal_j7_rad": a1_j7,
            "ori_err_deg_at_optimal": a1_err,
        },
        "a2_cache_LEFT_mirror_new_base": {
            "description": "Cache LEFT j0-j6 mirrored at NEW current ROBOT_RIGHT_BASE — theoretical j7 if right were mirror of actual cache left settled.",
            "left_j0_6": cache_left_j0_6,
            "mirror_right_j0_6": a2_right_j0_6,
            "base_pos": list(ROBOT_RIGHT_BASE_CURRENT),
            "optimal_j7_rad": a2_j7,
            "ori_err_deg_at_optimal": a2_err,
        },
        "b_cache_RIGHT_actual_new_base_optimal_j7": {
            "description": "Cache RIGHT j0-j6 ACTUAL + conditional optimal j7 for HAND_DOWN at NEW current base. DIRECT R1.ori test.",
            "right_j0_6": cache_right_j0_6,
            "base_pos": list(ROBOT_RIGHT_BASE_CURRENT),
            "optimal_j7_rad": b_j7,
            "ori_err_deg_at_optimal": b_err,
        },
        "c_cache_actual_as_is": {
            "description": "Cache RIGHT j0-j7 ACTUAL (no sweep) — ori_err to HAND_DOWN at CURRENT and OLD base.",
            "right_j0_7": cache_right_j0_7,
            "world_ee_pos_at_current_base": cache_ee_pos_new,
            "world_ee_pos_at_old_base": cache_ee_pos_old,
            "ori_err_deg_at_current_base": c_err_new,
            "ori_err_deg_at_old_base": c_err_old,
        },
    }

    deltas = {
        "description": "j7 deltas vs cache actual j7 (CC2 threshold > 0.5 rad for R1.ori structural confirmation).",
        "cache_right_j7": cache_right_j7,
        "verdict_threshold_rad": 0.5,
    }

    delta_a1 = abs(a1_j7 - cache_right_j7)
    delta_a2 = abs(a2_j7 - cache_right_j7)
    delta_b = abs(b_j7 - cache_right_j7)

    deltas["delta_a1_old_mirror_new_base_vs_cache"] = delta_a1
    deltas["delta_a2_cache_mirror_new_base_vs_cache"] = delta_a2
    deltas["delta_b_cache_actual_RIGHT_optimal_vs_cache"] = delta_b
    deltas["delta_a0_old_mirror_old_base_vs_cache_NOT_COMMENSURATE"] = abs(a0_j7 - cache_right_j7)

    if delta_b > 0.5:
        b_verdict = "SUPPORTS_R1_ORI_DRIFT_IF_HAND_DOWN_IS_TARGET"
    elif delta_b < 0.1:
        b_verdict = "AGAINST_R1_ORI_DRIFT_IF_HAND_DOWN_IS_TARGET"
    else:
        b_verdict = "INCONCLUSIVE"
    deltas["verdict_b"] = b_verdict

    deltas["caveat_target_mismatch"] = (
        "CRITICAL CAVEAT: AR env right-arm orientation target at terminal phase is the "
        "CABLE-TANGENT-derived quaternion (env:1036 dist_ori_raw = quat_distance(clamp_r_quat, "
        "compute_hand_quat_for_cable(seg_tangent))), NOT HAND_DOWN. This η1 comparison uses "
        "HAND_DOWN as a benchmark target consistent with find_right_j7.py's design, but AR's "
        "settled-state right-arm goal is cable-tangent-aligned, which varies per world. The "
        "j7 deltas above measure 'how aligned cache right-arm is to HAND_DOWN', NOT 'how aligned "
        "cache right-arm is to AR's actual terminal target'. A definitive R1.ori test would "
        "require per-world cable-tangent quat extraction from V6 records (not in schema) or "
        "running env (forbidden this turn)."
    )

    out["eta2_deltas"] = deltas
    return out


def run_eta3():
    with V6_SAMPLES.open() as f:
        data = json.load(f)

    acq_lost_te1_sx0 = defaultdict(lambda: Counter())
    bucket_acq_te1_sx0 = defaultdict(lambda: defaultdict(lambda: Counter()))
    bucket_lost_te1_sx0 = defaultdict(lambda: defaultdict(lambda: Counter()))
    br_acq_te1_sx0 = defaultdict(lambda: defaultdict(lambda: Counter()))

    for r in data["records"]:
        arm = r["arm"]
        te = r["terminal_entered"]
        sx = r["success"]
        if not (te and not sx):
            continue
        acq = int(r["hold_signal_acquired_count"])
        lost = int(r["hold_signal_lost_count"])
        br = r["terminal_break_reason"]
        if r["per_arm_both_at_terminal"]:
            bucket = "both"
        elif r["per_arm_right_only_at_terminal"]:
            bucket = "right_only"
        elif r["per_arm_left_only_at_terminal"]:
            bucket = "left_only"
        else:
            bucket = "neither"
        acq_lost_te1_sx0[arm][(acq, lost)] += 1
        bucket_acq_te1_sx0[arm][bucket][acq] += 1
        bucket_lost_te1_sx0[arm][bucket][lost] += 1
        br_acq_te1_sx0[arm][br][acq] += 1

    out = {
        "schema": "ar_phase5_rightarm_eta3_joint_cross_tab.v1",
        "filter": "terminal_entered=True AND success=False",
        "per_arm": {},
    }
    for arm in sorted(acq_lost_te1_sx0):
        per = {}
        total = sum(acq_lost_te1_sx0[arm].values())
        per["total"] = total
        # 2D joint (acq, lost) top entries
        sorted_joint = sorted(acq_lost_te1_sx0[arm].items(), key=lambda x: -x[1])
        per["joint_acq_lost_top_15"] = [
            {"acq": k[0], "lost": k[1], "count": v, "fraction": v / total}
            for k, v in sorted_joint[:15]
        ]
        # Patterns
        frac_acq1_lost1 = (acq_lost_te1_sx0[arm].get((1, 1), 0)) / total
        frac_acq1_lost0 = (acq_lost_te1_sx0[arm].get((1, 0), 0)) / total
        frac_acq_eq_lost = sum(c for (a, l), c in acq_lost_te1_sx0[arm].items() if a == l) / total
        frac_acq_gt_lost = sum(c for (a, l), c in acq_lost_te1_sx0[arm].items() if a > l) / total
        frac_lost_gt_acq = sum(c for (a, l), c in acq_lost_te1_sx0[arm].items() if l > a) / total
        frac_acq_ge_3 = sum(c for (a, l), c in acq_lost_te1_sx0[arm].items() if a >= 3) / total
        per["patterns"] = {
            "frac_acq1_lost1_R1_clean_single": frac_acq1_lost1,
            "frac_acq1_lost0_R1_acquired_no_lost_event_unusual": frac_acq1_lost0,
            "frac_acq_eq_lost_clean_acquire_lose_cycle": frac_acq_eq_lost,
            "frac_acq_gt_lost_unsustained_at_end_partial_hold": frac_acq_gt_lost,
            "frac_lost_gt_acq_R2_PARTIAL_CLOSE_signature": frac_lost_gt_acq,
            "frac_acq_ge_3_multi_toggle": frac_acq_ge_3,
        }
        # Bucket × acq
        per["bucket_acq_pattern"] = {}
        for bucket in ("both", "right_only", "left_only", "neither"):
            hist = bucket_acq_te1_sx0[arm].get(bucket, Counter())
            tot = sum(hist.values())
            per["bucket_acq_pattern"][bucket] = {
                "total": tot,
                "mean_acq": sum(k * v for k, v in hist.items()) / tot if tot else 0.0,
                "frac_acq_1": hist.get(1, 0) / tot if tot else 0.0,
                "frac_acq_ge_3": sum(v for k, v in hist.items() if k >= 3) / tot if tot else 0.0,
                "acq_hist_top5": [{"acq": k, "count": v} for k, v in sorted(hist.items())[:5]],
            }
        out["per_arm"][arm] = per

    # Interpretation:
    out["narrowing_interpretation"] = {
        "R1_clean_single_signature": "acq=1 AND lost=1 — IK target reached threshold once, then drift away. Most consistent with R1.ori or R1.pos.",
        "R1_flicker_signature": "acq >= 3 AND lost ≈ acq — IK precision oscillates near threshold.",
        "R2_partial_close_signature": "lost > acq — right_clamp_ok went True then immediately False multiple times within a single acquired cycle; consistent with closing-authority insufficient.",
        "Cable_physics_signature_proxy": "Across all break_reasons, bucket distribution dominated by 'neither' (rc lost cable dropped) suggests physics-event driven; F1 already established this.",
        "Caveat": "These signatures are heuristic interpretations. Definitive R1 vs R2 disambiguation requires per-step rc trajectory (Tier 3 F6 V9).",
    }
    return out


def run_eta5_prelim():
    with E1_JSON.open() as f:
        e1 = json.load(f)
    # Aggregate slice fractions from F1 (recomputed inline since we have h1_evidence_table)
    nt_fail_control = 10152
    tb_control = 2349
    success_control = 2859
    v6_total = 15360

    v6_control_sr = success_control / v6_total
    nt_frac = nt_fail_control / v6_total
    tb_frac = tb_control / v6_total

    nt_cable_drop_frac = 0.5780
    nt_explosion_frac = 0.4152

    # Pure R1 isolated upper-bound estimate:
    # Per F3-refined: control left_only=381 has 98.69% explosion + 1.31% timeout (5 cases) + 0% cable_drop
    # Pure-R1 isolation = (rc lost) AND (cable not dropped) AND (left held) AND (NOT explosion) AND (NOT timeout)
    # In V6 this is essentially 0 cases per F3-refined.
    pure_r1_isolated_count = 0  # F3-refined shows 0 cases per arm
    pure_r1_isolated_frac = 0.0

    # SR uplift bounds:
    lower_pp = pure_r1_isolated_frac * 100  # 0 pp (V6 evidence)

    # MID: speculative — R1 fix may indirectly help approach phase by keeping right arm closer to optimal
    # Assumption: 5% of never_terminal_fail recovers
    mid_recovery_rate = 0.05
    mid_pp = mid_recovery_rate * nt_frac * 100  # 5% × 66.094% × 100 = 3.30 pp

    # UPPER: 30% recovery
    upper_recovery_rate = 0.30
    upper_pp = upper_recovery_rate * nt_frac * 100  # 30% × 66.094% × 100 = 19.83 pp

    a6_upper_pp = 15.26  # E1 K=5 control upper bound

    # Combined ceiling
    combined_upper_pp = min(upper_pp + a6_upper_pp, (1 - v6_control_sr) * 100)

    ar_ceiling_with_combined = v6_control_sr + combined_upper_pp / 100
    five_skill_chain = ar_ceiling_with_combined ** 5

    out = {
        "schema": "ar_phase5_rightarm_eta5_prelim_sr_uplift.v1",
        "v6_control_baseline_sr": v6_control_sr,
        "v6_control_baseline_sr_pp": v6_control_sr * 100,
        "v6_total_completions": v6_total,
        "slice_fractions_pp": {
            "never_terminal_fail": nt_frac * 100,
            "terminal_break": tb_frac * 100,
            "success": v6_control_sr * 100,
        },
        "pure_r1_isolated_in_v6": {
            "count_per_arm": pure_r1_isolated_count,
            "fraction": pure_r1_isolated_frac,
            "evidence": "F3-refined: control left_only=381 has 98.69% explosion + 1.31% timeout (5/381) + 0% cable_drop. Pure R1 isolation (rc lost AND cable healthy AND left held AND not explosion AND not timeout) = 0 cases in V6.",
        },
        "r1_fix_sr_uplift_estimate_pp": {
            "lower_bound": lower_pp,
            "lower_bound_assumption": "R1 fix recovers ONLY pure-R1-isolated population. V6 pure R1 ≈ 0 cases. Lower bound: 0 pp.",
            "mid_estimate": mid_pp,
            "mid_assumption": f"SPECULATIVE: R1 fix improves IK precision; {mid_recovery_rate*100:.0f}% of never_terminal_fail population (66.1% of completions) becomes recoverable via better approach positioning. Yields {mid_pp:.2f} pp.",
            "upper_bound": upper_pp,
            "upper_assumption": f"OPTIMISTIC: R1 fix dramatically improves approach phase; {upper_recovery_rate*100:.0f}% of never_terminal_fail recovers regardless of break_reason. Yields {upper_pp:.2f} pp.",
        },
        "a6_grace_reference_uplift_pp": {
            "upper_bound_control_K5": a6_upper_pp,
            "source": "eval_runs/phase5_design_e1_e2_e3_2026-05-13/e1_a6_grace_feasibility.json control K=5 uplift",
        },
        "comparison_r1_vs_a6": {
            "a6_upper_pp": a6_upper_pp,
            "r1_upper_pp": upper_pp,
            "r1_mid_pp": mid_pp,
            "r1_lower_pp": lower_pp,
            "r1_to_a6_mid_ratio": mid_pp / a6_upper_pp if a6_upper_pp else None,
            "interpretation": (
                f"A6 upper bound {a6_upper_pp:.2f} pp vs R1 mid {mid_pp:.2f} pp = {a6_upper_pp/mid_pp:.1f}x larger. "
                f"R1 upper bound {upper_pp:.2f} pp marginally exceeds A6 upper but with HEAVY speculation. "
                "A6 has direct E1 evidence (K=5 recovery counter); R1 upper bound is unsupported."
            ),
        },
        "combined_a6_plus_r1_upper_pp": combined_upper_pp,
        "t_root_chain_proximity": {
            "ar_ceiling_with_all_fixes_pp": ar_ceiling_with_combined * 100,
            "five_skill_chain_at_ceiling_pp": five_skill_chain * 100,
            "t_root_target_pp": 95.0,
            "gap_factor": 95.0 / (five_skill_chain * 100) if five_skill_chain > 0 else float("inf"),
            "interpretation": (
                f"AR ceiling with full R1 (upper) + A6 (upper) = {ar_ceiling_with_combined*100:.1f}% SR. "
                f"5-skill chain at AR ceiling = {five_skill_chain*100:.2f}% vs 95% T-ROOT target = {95.0/(five_skill_chain*100):.0f}x gap. "
                "AR refinement alone CANNOT reach T-ROOT regardless of R1 fix success."
            ),
        },
        "explicit_assumptions": [
            "AR right-arm orientation target at terminal phase: HAND_DOWN-style. UNCERTAIN — env:1036 actually uses compute_hand_quat_for_cable(seg_tangent), per-world cable-tangent-derived.",
            "Pure R1 isolated count uses control left_only=381 with 98.7% explosion + 1.3% timeout subtraction → 0 cases pure-R1 in V6.",
            "R1 fix effect on physics events (cable_drop, explosion) is speculative; cable_drop and explosion are upstream of right_clamp_ok in the failure chain.",
            "Mid recovery rate 5% is heuristic; actual recovery rate could be 0-20%.",
            "Upper recovery rate 30% is OPTIMISTIC; assumes R1 fix removes pos AND ori precision failure modes AND propagates to physics event reduction.",
            "A6 + R1 combined upper is naive additive; actual combined effect may be sub-additive (overlap) or super-additive (synergy).",
            "T-ROOT chain math assumes per-skill independence; actual chain has dependencies.",
            "η5-prelim uses control arm only; intervention arm may have different uplift.",
            "Implementation cost of R1 fix (env edit + retraining ~20-40h GPU per Tier 1+2 CC4 estimate) is NOT included in this uplift estimate.",
        ],
        "uncertainty_quality": "PRELIMINARY ONLY. Bounds span 0 pp (lower) to 19.83 pp (upper) — very wide. Definitive estimates require V8 actual rollout (Tier 3 F5, BLOCKED per current disposition) or per-step trajectory (V9, future).",
    }
    return out


def write_convergence_memo(e12, e3, e5):
    lines = []
    lines.append("# AR Phase 5 — Right-Arm η pre-V8 Convergence Memo")
    lines.append("")
    lines.append(
        "Authorized per Rs代行 disposition `T_ROOT_COORD2_ETA_PRE_V8_START_ACK_20260513_0600 root` "
        "modified-η: η1+η2+η3+η5-prelim; η4 V7 verdict HELD per %67 ownership."
    )
    lines.append("")
    lines.append("## η1 + η2 — corrected-base FK comparison vs V6 cache fk_jq[15]")
    lines.append("")
    v = e12["eta1_variants"]
    d = e12["eta2_deltas"]
    lines.append(f"V6 cache right-arm j7 (production) = **{d['cache_right_j7']:.4f} rad**")
    lines.append("")
    lines.append("Variant computations (all at ROBOT_BASE_QUAT_WXYZ=(0.7071, 0, 0.7071, 0)):")
    lines.append("")
    lines.append("| Variant | Description | Base | Optimal j7 (rad) | ori_err (deg) | |Δj7| vs cache |")
    lines.append("|---|---|---|---:|---:|---:|")
    for key, label in [
        ("a0_old_LEFT_mirror_old_base_REFERENCE", "a0 reference (old)"),
        ("a1_old_LEFT_mirror_new_base", "a1 old mirror @ new base"),
        ("a2_cache_LEFT_mirror_new_base", "a2 cache mirror @ new base"),
        ("b_cache_RIGHT_actual_new_base_optimal_j7", "b cache RIGHT actual @ new base"),
    ]:
        x = v[key]
        delta = abs(x["optimal_j7_rad"] - d["cache_right_j7"])
        commensurate = "" if "REFERENCE" not in label else " (not commensurate)"
        lines.append(
            f"| {label}{commensurate} | base={x['base_pos']} | {x['optimal_j7_rad']:.4f} | {x['ori_err_deg_at_optimal']:.4f} | {delta:.4f} |"
        )
    lines.append("")
    c = v["c_cache_actual_as_is"]
    lines.append(f"**Variant c (cache RIGHT j0-j7 as-is)**: ori_err to HAND_DOWN at CURRENT base = **{c['ori_err_deg_at_current_base']:.4f} deg**; at OLD base = {c['ori_err_deg_at_old_base']:.4f} deg.")
    lines.append(f"World EE pos at current base: {c['world_ee_pos_at_current_base']}")
    lines.append("")
    delta_b = d["delta_b_cache_actual_RIGHT_optimal_vs_cache"]
    lines.append(f"**Variant b (most direct test)** |Δj7| = **{delta_b:.4f} rad** ({np.degrees(delta_b):.1f} deg)")
    lines.append(f"  Verdict: **{d['verdict_b']}**")
    lines.append("")
    lines.append("**CRITICAL CAVEAT (η1)**: " + d["caveat_target_mismatch"])
    lines.append("")
    lines.append("## η3 — joint cross-tab on full_samples.json (te=1 sx=0)")
    lines.append("")
    for arm in sorted(e3["per_arm"]):
        per = e3["per_arm"][arm]
        lines.append(f"### {arm} (n={per['total']})")
        lines.append("")
        lines.append("**Patterns:**")
        for k, v in per["patterns"].items():
            lines.append(f"- {k}: {v:.4f}")
        lines.append("")
        lines.append("**Top 5 (acq, lost) joint:**")
        lines.append("")
        lines.append("| acq | lost | count | fraction |")
        lines.append("|---:|---:|---:|---:|")
        for row in per["joint_acq_lost_top_15"][:5]:
            lines.append(f"| {row['acq']} | {row['lost']} | {row['count']} | {row['fraction']:.4f} |")
        lines.append("")
        lines.append("**Bucket × acq mean:**")
        lines.append("")
        lines.append("| bucket | total | mean_acq | frac_acq_1 | frac_acq_ge_3 |")
        lines.append("|---|---:|---:|---:|---:|")
        for bucket in ("both", "right_only", "left_only", "neither"):
            b = per["bucket_acq_pattern"][bucket]
            lines.append(
                f"| {bucket} | {b['total']} | {b['mean_acq']:.3f} | {b['frac_acq_1']:.4f} | {b['frac_acq_ge_3']:.4f} |"
            )
        lines.append("")
    lines.append("**η3 narrowing interpretation:**")
    lines.append("")
    for k, v in e3["narrowing_interpretation"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## η5-prelim — SR uplift bounds for R1 fix")
    lines.append("")
    lines.append(f"V6 control baseline SR: **{e5['v6_control_baseline_sr_pp']:.2f}%** (n={e5['v6_total_completions']})")
    lines.append("")
    lines.append(f"Pure R1 isolated in V6: **{e5['pure_r1_isolated_in_v6']['count_per_arm']} cases per arm** ({e5['pure_r1_isolated_in_v6']['fraction']*100:.4f}%)")
    lines.append("")
    lines.append("**R1 fix SR uplift estimate (preliminary)**:")
    lines.append("")
    r = e5["r1_fix_sr_uplift_estimate_pp"]
    lines.append(f"- LOWER bound: **{r['lower_bound']:.2f} pp** — {r['lower_bound_assumption']}")
    lines.append(f"- MID estimate: **{r['mid_estimate']:.2f} pp** — {r['mid_assumption']}")
    lines.append(f"- UPPER bound: **{r['upper_bound']:.2f} pp** — {r['upper_assumption']}")
    lines.append("")
    a6 = e5["a6_grace_reference_uplift_pp"]
    cmp = e5["comparison_r1_vs_a6"]
    lines.append(f"A6 grace reference upper bound (control K=5): **{a6['upper_bound_control_K5']:.2f} pp**")
    lines.append("")
    lines.append(f"**Comparison**: {cmp['interpretation']}")
    lines.append("")
    proxy = e5["t_root_chain_proximity"]
    lines.append(f"**T-ROOT chain proximity**: AR ceiling with full R1+A6 = **{proxy['ar_ceiling_with_all_fixes_pp']:.1f}% SR**; 5-skill chain at ceiling = **{proxy['five_skill_chain_at_ceiling_pp']:.2f}%** vs T-ROOT target **95%** = **{proxy['gap_factor']:.0f}x gap**.")
    lines.append("")
    lines.append(f"Interpretation: {proxy['interpretation']}")
    lines.append("")
    lines.append("**Explicit assumptions:**")
    for a in e5["explicit_assumptions"]:
        lines.append(f"- {a}")
    lines.append("")
    lines.append(f"**Uncertainty quality**: {e5['uncertainty_quality']}")
    lines.append("")
    return "\n".join(lines)


def write_sha_manifest(inputs, outputs):
    lines = ["# inputs"]
    for p in inputs:
        if p.exists():
            lines.append(f"{sha256_file(p)}  {p.relative_to(ROOT)}")
    lines.append("# outputs")
    for p in outputs:
        if p.exists():
            lines.append(f"{sha256_file(p)}  {p.relative_to(ROOT)}")
    return "\n".join(lines) + "\n"


def main():
    print("[eta_pre_v8] η1+η2 corrected-base FK comparison...", flush=True)
    e12 = run_eta1_eta2()
    print("[eta_pre_v8] η3 joint cross-tab...", flush=True)
    e3 = run_eta3()
    print("[eta_pre_v8] η5-prelim SR uplift estimate...", flush=True)
    e5 = run_eta5_prelim()
    (OUT / "eta1_eta2_corrected_base_fk.json").write_text(json.dumps(e12, indent=2))
    (OUT / "eta3_joint_cross_tab.json").write_text(json.dumps(e3, indent=2))
    (OUT / "eta5_prelim_sr_uplift.json").write_text(json.dumps(e5, indent=2))
    md = write_convergence_memo(e12, e3, e5)
    (OUT / "convergence_memo.md").write_text(md)
    inputs = [V6_SAMPLES, V6_SUMMARY, H1_CSV, CACHE_NPZ, FIND_J7, E1_JSON]
    outputs = sorted(OUT.glob("*.json")) + [OUT / "convergence_memo.md"]
    (OUT / "analysis_sha256.txt").write_text(write_sha_manifest(inputs, outputs))
    print(f"[eta_pre_v8] done; outputs in {OUT}", flush=True)


if __name__ == "__main__":
    main()
