# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""P-D1 offline analysis, prereg v1.2 (freeze pending; design v1.5).

Scores the six frozen runs against the FROZEN bars (prereg sec 2/3). Pure offline; bar arithmetic
only -- the probe verdict is p5's court; physical validity is Rs's (video leg).

Legs: L-P1 (|q-ctrl| per phase window, P-2 N/A rule), L-P3 effort/saturation (affine formula),
L-P4 no-haul, R4 sec12.1 calibration vs the precomputed |rec[0]-rec[t]| curve (scored vs the
INTENDED stream -- never vs the frozen ctrl), L-P2' predicate parity vs the clean reference R0b
(+ P-1 continuous divergence REPORTED), L-P0 impact assessment (R0 vs R0b), M-6 divergence dwell
counts (N_DIV=48, bar candidate 15 mrad), A-4 first-frame checks, R2-vs-R1 no-regression, and the
L-P1 stream cross-check max|ctrl-intended| <= 1e-9 on normal PD runs.

Usage: python3 armpd_analysis.py <probe_dir> [<ur5e_xml_path>]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BARS = {
    "qs_joint_rad": 0.002,
    "tr_joint_rad": 0.005,
    "qs_ee_m": 0.0015,
    "tr_ee_m": 0.003,
    "sat_warn": 0.01,
    "sat_fail": 0.05,
    "mdiv_bar_rad": 0.015,  # M-6 bar candidate (report only)
    "mdiv_dwell": 48,
    "calib_abs_rad": 0.06,  # sec12.1 band = abs + rel*predicted
    "calib_rel": 0.05,
    "a4_eps_pen_m": 0.003,
    "a4_dv_mult": 2.0,
    "a4_dv_floor": 0.01,
}
RUNS = ["r0v12_kin", "r1v12_lp0", "r2v12_pd", "r3v12_ramp", "r4v12_stale", "r5v12_gains01"]
PD_RUNS = ("r2v12_pd", "r3v12_ramp", "r4v12_stale", "r5v12_gains01")

_BODY_ID = None


def load_run(p: Path, tag: str):
    d = p / tag
    return {
        "tag": tag,
        "summary": json.loads((d / f"summary_{tag}.json").read_text()),
        "per_step": json.loads((d / f"per_step_{tag}.json").read_text()),
        "frames": np.load(d / f"armpd_frames_{tag}.npz"),
        "complete": (d / "COMPLETE.ok").exists(),
    }


def m_body_id(m, mujoco):
    global _BODY_ID
    if _BODY_ID is None:
        for name in ("wrist_3_link", "ee_link"):
            i = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
            if i >= 0:
                _BODY_ID = i
                break
        else:
            _BODY_ID = m.nbody - 1
    return _BODY_ID


def fk_flange(m, d, q6, mujoco):
    d.qpos[:6] = q6
    mujoco.mj_kinematics(m, d)
    return d.xpos[m_body_id(m, mujoco)].copy()


def phase_masks(run):
    fr = run["frames"]
    rl = np.asarray(fr["rl_step"])
    g3 = run["summary"].get("g3_step")
    done = run["summary"].get("done_step")
    end = int(rl.max()) if len(rl) else -1
    lo = g3 if g3 is not None else end + 1
    hi = done if done is not None else end
    qs = (rl >= lo) & (rl <= hi)
    return qs, ~qs


def dwell_counts(err, bar, n_dwell):
    """M-6: per-joint count of maximal runs of >=n_dwell consecutive frames above bar."""
    out = []
    for j in range(err.shape[1]):
        above = err[:, j] > bar
        run_len = 0
        events = 0
        for a in above:
            run_len = run_len + 1 if a else 0
            if run_len == n_dwell:
                events += 1  # count each dwell event once, at the frame it completes
        out.append(int(events))
    return out


def tracking_legs(run, mj_pack, stale: bool):
    fr = run["frames"]
    q, qd = np.asarray(fr["q"]), np.asarray(fr["qd"])
    ctrl = np.asarray(fr["ctrl"])
    intended = np.asarray(fr["intended"]) if "intended" in fr else None
    ref = intended if stale else ctrl  # sec12.1: R3 scored vs the INTENDED stream
    err = np.abs(q - ref)
    qs, tr = phase_masks(run)
    out = {
        "scored_vs": "intended" if stale else "ctrl",
        "frames": int(q.shape[0]),
        "qs_frames": int(qs.sum()),
        "tr_frames": int(tr.sum()),
        "qs_joint_max": (float(np.nanmax(err[qs])) if qs.any() else None),
        "tr_joint_max": (float(np.nanmax(err[tr])) if tr.any() else None),
        "per_joint_max": [float(x) for x in np.nanmax(err, axis=0)],
        "lp4_err_frame0_max": float(np.nanmax(err[0])) if len(err) else None,
        "mdiv_dwell_events_per_joint": dwell_counts(np.nan_to_num(err, nan=0.0), BARS["mdiv_bar_rad"], BARS["mdiv_dwell"]),
    }
    if intended is not None and not stale:
        # L-P1 stream cross-check (prereg sec3): on normal PD runs ctrl must equal intended.
        valid = ~np.isnan(intended).any(axis=1)
        out["ctrl_vs_intended_max"] = float(np.max(np.abs(ctrl[valid] - intended[valid]))) if valid.any() else None
    if mj_pack is not None:
        mujoco, m, d = mj_pack
        ee = np.zeros((q.shape[0], 2))
        for i in range(q.shape[0]):
            for a, sl in enumerate((slice(0, 6), slice(6, 12))):
                if np.isnan(ref[i, sl]).any():
                    ee[i, a] = np.nan
                    continue
                ee[i, a] = float(np.linalg.norm(fk_flange(m, d, q[i, sl], mujoco) - fk_flange(m, d, ref[i, sl], mujoco)))
        out["qs_ee_max"] = float(np.nanmax(ee[qs])) if qs.any() else None
        out["tr_ee_max"] = float(np.nanmax(ee[tr])) if tr.any() else None
    ke, kd, cap = (np.asarray(fr[k]) for k in ("ke", "kd", "effort_cap"))
    if ke.size == 12:
        f_raw = ke[None, :] * (np.nan_to_num(ref, nan=0.0) - q) - kd[None, :] * qd
        sat = np.abs(f_raw) >= (cap[None, :] - 1e-9)
        out["sat_share_max"] = float(sat.mean(axis=0).max())
        out["sat_share_per_joint"] = [float(x) for x in sat.mean(axis=0)]
    # bar verdicts (P-2: empty quasi-static window -> N/A, never PASS)
    v = {}
    v["L-P1 qs joint"] = "N/A (empty window)" if not qs.any() else bool(out["qs_joint_max"] <= BARS["qs_joint_rad"])
    v["L-P1 tr joint"] = bool(out["tr_joint_max"] <= BARS["tr_joint_rad"]) if tr.any() else "N/A"
    if "qs_ee_max" in out:
        v["L-P1 qs EE"] = "N/A (empty window)" if not qs.any() else bool(out["qs_ee_max"] <= BARS["qs_ee_m"])
        v["L-P1 tr EE"] = bool(out["tr_ee_max"] <= BARS["tr_ee_m"]) if tr.any() else "N/A"
    if "sat_share_max" in out:
        s = out["sat_share_max"]
        v["L-P3 saturation"] = "FAIL" if s > BARS["sat_fail"] else ("WARN" if s > BARS["sat_warn"] else "PASS")
    v["L-P4 no-haul"] = bool((out["lp4_err_frame0_max"] or 1e9) <= BARS["tr_joint_rad"])
    out["bar_verdicts"] = v
    return out


def r3_calibration(run):
    """sec12.1: measured |q - intended| must match the precomputed |rec[0] - rec[t]| within the band."""
    fr = run["frames"]
    q = np.asarray(fr["q"])
    intended = np.asarray(fr["intended"])
    ctrl = np.asarray(fr["ctrl"])
    valid = ~np.isnan(intended).any(axis=1)
    measured = np.abs(q - intended)[valid]
    predicted = np.abs(ctrl[0][None, :] - intended[valid])  # ctrl frozen at rec[0]
    dev = np.abs(measured - predicted)
    band = BARS["calib_abs_rad"] + BARS["calib_rel"] * predicted
    ok = bool(np.all(dev <= band))
    exceeds_lp1 = bool(np.nanmax(measured) > BARS["tr_joint_rad"])
    return {
        "frames_scored": int(valid.sum()),
        "max_dev_rad": float(np.max(dev)) if dev.size else None,
        "max_band_rad": float(np.max(band)) if band.size else None,
        "calibration_ok": ok,
        "failability_ok (exceeds an L-P1 bar)": exceeds_lp1,
        "instrument_verdict": ("VALID" if (ok and exceeds_lp1) else "INVALID"),
    }


def parity_row(run):
    s = run["summary"]
    return {
        "mode": (s.get("effective_config") or {}).get("mode"),
        "g3_reached": s.get("g3_reached"),
        "g3_step": s.get("g3_step"),
        "pin_fired": s.get("pin_fire_step") is not None,
        "pin_fire_step": s.get("pin_fire_step"),
        "first_cause": {k: v for k, v in (s.get("first_cause_step") or {}).items() if v is not None},
        "done_step": s.get("done_step"),
        "repose_count": s.get("route_start_repose_count"),
        "status": s.get("status"),
    }


def a4_checks(run, r0b):
    fr = run["frames"]
    pen = np.asarray(fr["pen_min"]) if "pen_min" in fr else np.array([])
    dv = np.asarray(fr["cable_vmax"]) if "cable_vmax" in fr else np.array([])
    r0b_dv = np.asarray(r0b["frames"]["cable_vmax"]) if (r0b and "cable_vmax" in r0b["frames"]) else np.array([])
    out = {}
    if pen.size:
        out["first_frame_pen_min_m"] = float(pen[0])
        out["A-4 penetration"] = bool(pen[0] >= -BARS["a4_eps_pen_m"])
    if dv.size:
        band = max(BARS["a4_dv_mult"] * (float(r0b_dv[0]) if r0b_dv.size else 0.0), BARS["a4_dv_floor"])
        out["first_frame_cable_vmax"] = float(dv[0])
        out["A-4 cable dv (band)"] = band
        out["A-4 cable dv"] = bool(dv[0] <= band)
    return out


def cont_divergence(a, b, mj_pack):
    """P-1 REPORTED leg: continuous R1-vs-R0b divergence (arm q + EE + cable proxy), no bar."""
    qa, qb = np.asarray(a["frames"]["q"]), np.asarray(b["frames"]["q"])
    n = min(len(qa), len(qb))
    out = {"frames_compared": int(n)}
    if n:
        dq = np.abs(qa[:n] - qb[:n])
        out["arm_dq_max"] = float(dq.max())
        out["arm_dq_p99"] = float(np.percentile(dq, 99))
        if mj_pack is not None:
            mujoco, m, d = mj_pack
            idx = np.unique(np.linspace(0, n - 1, min(n, 500)).astype(int))  # subsample EE FK
            ee = [
                max(
                    float(np.linalg.norm(fk_flange(m, d, qa[i, s], mujoco) - fk_flange(m, d, qb[i, s], mujoco)))
                    for s in (slice(0, 6), slice(6, 12))
                )
                for i in idx
            ]
            out["ee_div_max_m (subsampled)"] = float(max(ee)) if ee else None
        ca = np.asarray(a["frames"].get("cable_vmax", []))
        cb = np.asarray(b["frames"].get("cable_vmax", []))
        m2 = min(len(ca), len(cb))
        if m2:
            out["cable_vmax_div_max"] = float(np.max(np.abs(ca[:m2] - cb[:m2])))
    return out


def main():
    p = Path(sys.argv[1])
    mj_pack = None
    if len(sys.argv) > 2:
        import mujoco

        m = mujoco.MjModel.from_xml_path(sys.argv[2])
        mj_pack = (mujoco, m, mujoco.MjData(m))

    runs = {}
    for tag in RUNS:
        try:
            runs[tag] = load_run(p, tag)
        except FileNotFoundError as e:
            runs[tag] = None
            print(f"[analysis] MISSING run {tag}: {e}")

    res = {"prereg": "v1.2 (fill at freeze)", "bars": BARS, "runs": {}}
    r0b = runs.get("r1v12_lp0")
    for tag, run in runs.items():
        if run is None:
            res["runs"][tag] = {"missing": True}
            continue
        row = {"complete": run["complete"], "parity": parity_row(run)}
        if tag in PD_RUNS:
            row["tracking"] = tracking_legs(run, mj_pack, stale=(tag == "r4v12_stale"))
            row["a4"] = a4_checks(run, r0b)
        res["runs"][tag] = row

    if runs.get("r4v12_stale"):
        res["r3_sec12_1"] = r3_calibration(runs["r4v12_stale"])
    if runs.get("r0v12_kin") and r0b:
        qa = np.asarray(runs["r0v12_kin"]["frames"]["q"])
        qb = np.asarray(r0b["frames"]["q"])
        n = min(len(qa), len(qb))
        res["lp0_impact"] = {
            "frames_compared": int(n),
            "arm_dq_max": float(np.abs(qa[:n] - qb[:n]).max()) if n else None,
            "parity_r0": parity_row(runs["r0v12_kin"]),
            "parity_r0b": parity_row(r0b),
        }
    if runs.get("r2v12_pd") and r0b:
        res["lp2p_parity_vs_clean"] = {
            "r2": parity_row(runs["r2v12_pd"]),
            "r0b_ref": parity_row(r0b),
            "p1_continuous_divergence_REPORTED": cont_divergence(runs["r2v12_pd"], r0b, mj_pack),
        }
    if runs.get("r2v12_pd") and runs.get("r3v12_ramp"):
        q1 = np.asarray(runs["r2v12_pd"]["frames"]["q"])
        q2 = np.asarray(runs["r3v12_ramp"]["frames"]["q"])
        n = min(len(q1), len(q2))
        res["ramp_effect_r3_vs_r2_q_max_delta"] = float(np.abs(q1[:n] - q2[:n]).max()) if n else None

    (p / "analysis_result_v12.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print(f"\n[analysis] wrote {p}/analysis_result_v12.json")


if __name__ == "__main__":
    main()
