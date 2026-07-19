# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""P-D1 offline analysis (prereg ARM_CONTROL_PD1_PROBE_PREREG_RSTECHLEAD_20260719.md sec 2/4).

Scores the five frozen runs against the FROZEN bars. Pure offline (npz/json + mujoco FK on the
ur5e.xml kinematics); no sim stepping, no GPU. Emits `analysis_result.json` + a printed table.
Bar arithmetic only -- the probe verdict is p5's court; physical validity is Rs's (video leg).

EE error = wrist-flange FK (wrist_3_link) |FK(q) - FK(ctrl)| per arm; rigid-base invariance makes
the arm-local frame exact for the error magnitude. Effort = clip-aware affine servo formula
f_raw = ke*(ctrl - q) - kd*qd; saturation = |f_raw| >= cap (exact for gaintype=fixed/biastype=affine).

Usage:
    python3 armpd_analysis.py <probe_dir> <ur5e_xml_path>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BARS = {
    "qs_joint_rad": 0.002,  # quasi-static per-joint
    "tr_joint_rad": 0.005,  # transient per-joint
    "qs_ee_m": 0.0015,
    "tr_ee_m": 0.003,
    "sat_warn": 0.01,
    "sat_fail": 0.05,
    "trip_rad": 0.015,  # informational
}
RUNS = ["r0_kin", "r0b_lp0", "r1_pd", "r2_pd_ramp", "r3_pd_neg"]


def load_run(p: Path, tag: str):
    d = p / tag
    summary = json.loads((d / f"summary_{tag}.json").read_text())
    per_step = json.loads((d / f"per_step_{tag}.json").read_text())
    frames = np.load(d / f"armpd_frames_{tag}.npz")
    complete = (d / "COMPLETE.ok").exists()
    return {"tag": tag, "summary": summary, "per_step": per_step, "frames": frames, "complete": complete}


def fk_flange(m, d, q6, mujoco):
    d.qpos[:6] = q6
    mujoco.mj_kinematics(m, d)
    return d.xpos[m_body_id(m, mujoco)].copy()


_BODY_ID = None


def m_body_id(m, mujoco):
    global _BODY_ID
    if _BODY_ID is None:
        for name in ("wrist_3_link", "wrist_3link", "ee_link"):
            i = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
            if i >= 0:
                _BODY_ID = i
                break
        else:
            _BODY_ID = m.nbody - 1  # fallback: last body
    return _BODY_ID


def phase_masks(run):
    """Quasi-static = RL steps in [g3_step, done/end] (prereg sec 2 operationalization); else transient."""
    fr = run["frames"]
    rl = np.asarray(fr["rl_step"])
    g3 = run["summary"].get("g3_step")
    done = run["summary"].get("done_step")
    end = int(rl.max()) if len(rl) else -1
    lo = g3 if g3 is not None else end + 1  # no g3 -> empty quasi-static window
    hi = done if done is not None else end
    qs = (rl >= lo) & (rl <= hi)
    return qs, ~qs


def tracking_legs(run, mj_pack):
    fr = run["frames"]
    q, ctrl, qd = np.asarray(fr["q"]), np.asarray(fr["ctrl"]), np.asarray(fr["qd"])
    err = np.abs(q - ctrl)
    qs, tr = phase_masks(run)
    out = {
        "frames": int(q.shape[0]),
        "qs_frames": int(qs.sum()),
        "tr_frames": int(tr.sum()),
        "qs_joint_max": (float(err[qs].max()) if qs.any() else None),
        "qs_joint_p99": (float(np.percentile(err[qs], 99)) if qs.any() else None),
        "tr_joint_max": (float(err[tr].max()) if tr.any() else None),
        "tr_joint_p99": (float(np.percentile(err[tr], 99)) if tr.any() else None),
        "per_joint_max": [float(x) for x in err.max(axis=0)],
        "lp4_err_frame0_max": float(err[0].max()) if len(err) else None,
        "trip_frames": int((err.max(axis=1) > BARS["trip_rad"]).sum()),
    }
    # EE (wrist flange) error, both arms, per frame
    if mj_pack is not None:
        mujoco, m, d = mj_pack
        ee = np.zeros((q.shape[0], 2))
        for i in range(q.shape[0]):
            for a, sl in enumerate((slice(0, 6), slice(6, 12))):
                p1 = fk_flange(m, d, q[i, sl], mujoco)
                p2 = fk_flange(m, d, ctrl[i, sl], mujoco)
                ee[i, a] = float(np.linalg.norm(p1 - p2))
        out["qs_ee_max"] = float(ee[qs].max()) if qs.any() else None
        out["tr_ee_max"] = float(ee[tr].max()) if tr.any() else None
    # L-P3 effort / saturation from the affine servo formula
    ke, kd, cap = (np.asarray(fr[k]) for k in ("ke", "kd", "effort_cap"))
    if ke.size == 12:
        f_raw = ke[None, :] * (ctrl - q) - kd[None, :] * qd
        sat = np.abs(f_raw) >= (cap[None, :] - 1e-9)
        out["sat_share_per_joint"] = [float(x) for x in sat.mean(axis=0)]
        out["sat_share_max"] = float(sat.mean(axis=0).max())
    # bar verdicts (arithmetic only)
    v = {}
    if out.get("qs_joint_max") is not None:
        v["L-P1 qs joint"] = out["qs_joint_max"] <= BARS["qs_joint_rad"]
    if out.get("tr_joint_max") is not None:
        v["L-P1 tr joint"] = out["tr_joint_max"] <= BARS["tr_joint_rad"]
    if out.get("qs_ee_max") is not None:
        v["L-P1 qs EE"] = out["qs_ee_max"] <= BARS["qs_ee_m"]
    if out.get("tr_ee_max") is not None:
        v["L-P1 tr EE"] = out["tr_ee_max"] <= BARS["tr_ee_m"]
    if out.get("sat_share_max") is not None:
        v["L-P3 saturation"] = (
            "FAIL" if out["sat_share_max"] > BARS["sat_fail"] else ("WARN" if out["sat_share_max"] > BARS["sat_warn"] else "PASS")
        )
    v["L-P4 no-haul (frame0 <= tr bar)"] = (out["lp4_err_frame0_max"] or 1e9) <= BARS["tr_joint_rad"]
    out["bar_verdicts"] = v
    return out


def parity_row(run):
    s = run["summary"]
    return {
        "g3_reached": s.get("g3_reached"),
        "g3_step": s.get("g3_step"),
        "pin_fired": s.get("pin_fire_step") is not None,
        "pin_fire_step": s.get("pin_fire_step"),
        "first_cause": {k: v for k, v in (s.get("first_cause_step") or {}).items() if v is not None},
        "done_step": s.get("done_step"),
        "repose_count": s.get("route_start_repose_count"),
        "status": s.get("status"),
    }


def main():
    p = Path(sys.argv[1])
    mj_pack = None
    if len(sys.argv) > 2:
        import mujoco

        m = mujoco.MjModel.from_xml_path(sys.argv[2])
        d = mujoco.MjData(m)
        mj_pack = (mujoco, m, d)

    runs = {}
    for tag in RUNS:
        try:
            runs[tag] = load_run(p, tag)
        except FileNotFoundError as e:
            runs[tag] = None
            print(f"[analysis] MISSING run {tag}: {e}")

    res = {"bars": BARS, "runs": {}}
    for tag, run in runs.items():
        if run is None:
            res["runs"][tag] = {"missing": True}
            continue
        row = {"complete": run["complete"], "parity": parity_row(run)}
        if tag in ("r1_pd", "r2_pd_ramp", "r3_pd_neg"):
            row["tracking"] = tracking_legs(run, mj_pack)
        res["runs"][tag] = row

    # L-P0: R0 vs R0b same-seed divergence (tug-of-war component alone)
    if runs.get("r0_kin") and runs.get("r0b_lp0"):
        qa = np.asarray(runs["r0_kin"]["frames"]["q"])
        qb = np.asarray(runs["r0b_lp0"]["frames"]["q"])
        n = min(len(qa), len(qb))
        dq = np.abs(qa[:n] - qb[:n])
        res["lp0"] = {
            "frames_compared": int(n),
            "arm_dq_max": float(dq.max()) if n else None,
            "arm_dq_p99": float(np.percentile(dq, 99)) if n else None,
            "parity_r0": parity_row(runs["r0_kin"]),
            "parity_r0b": parity_row(runs["r0b_lp0"]),
        }
    # L-P5: the negative control must FAIL at least one L-P1 bar
    neg = res["runs"].get("r3_pd_neg", {}).get("tracking", {}).get("bar_verdicts", {})
    lp1_flags = [v for k, v in neg.items() if k.startswith("L-P1") and isinstance(v, bool)]
    res["lp5_negative_control_failed_a_bar"] = (not all(lp1_flags)) if lp1_flags else None
    # R2 vs R1 mechanism no-regression
    if runs.get("r1_pd") and runs.get("r2_pd_ramp"):
        q1 = np.asarray(runs["r1_pd"]["frames"]["q"])
        q2 = np.asarray(runs["r2_pd_ramp"]["frames"]["q"])
        n = min(len(q1), len(q2))
        res["r2_vs_r1_q_max_delta"] = float(np.abs(q1[:n] - q2[:n]).max()) if n else None

    (p / "analysis_result.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print(f"\n[analysis] wrote {p}/analysis_result.json")


if __name__ == "__main__":
    main()
