# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Offline converter: ``route_demo_raw.npz`` -> ``bc_dataset.npz`` + ``schedule.json`` (B_BC_BUILD_SPEC.md v2.2 §2).

Pure offline transform -- numpy + json + hashlib + a pure-CONSTANT SSOT read of
``task_config.GROOVE_CENTER_Z`` (no solver / mujoco / newton / env-runtime import; task_config is a
leaf config module, verified to pull no sim runtime). §10 ERRATA E1-E11 (+ E4'/E10/E11) binding.

DQ1=B pipeline, phase B0/B1. Consumes the FROZEN 13-phase canonical npz (E3): a 15-phase npz => STOP
(schema v2 is a separate B2 concern). Produces the ``bc_pretrain.py`` (obs, actions) contract + an
evaluator replay ``schedule.json``. Actions are the ACHIEVED ee_pos deltas the route produced (R-then-L,
/POS_ACTION_SCALE); grip_cmd columns are [L, R] (E6, OPPOSITE of the action layout).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

# --- constants (spec §2; AC env + task_config SSOT anchors) ---
POS_ACTION_SCALE = 0.015  # newton_approach_cable_mujoco_env.py:230
PHYSICS_STEPS_PER_RL = 10  # AC env :238 == task_config SIM_SUBSTEPS :101
LAST_CTRL_FRAME = 7700  # frame 7700 = last control frame (6-frame zero-motion tail 7701..7706 dropped)
CABLE_BODY_START = 28  # E4: pinned_body 55 - seated seg 27 (validated exactly by the E4' argmin assert)
GRIP_CLOSED_RAD = 0.6  # grip-predicate: OPEN 0.0 / HALF 0.69 / CLOSE 0.7407 (task_config:289/:291/:313)
_DEFAULT_QUAT = np.array([-0.7071067811865476, 0.0, 0.0, 0.7071067811865476], dtype=np.float32)  # Rx(-90) xyzw
# E3: the FROZEN 13-phase canonical schema. A different length => STOP (schema-version mismatch).
PHASES13 = (
    "GRASP_HOVER",
    "GRASP_DESCEND",
    "GRASP_CLOSE",
    "LIFT",
    "ROUTE_C1",
    "C1_SEAT",
    "C1_PIN",
    "L_HALF_UNCLAMP",
    "R_UNCLAMP_RISE",
    "GUIDE_C2",
    "C2_REGRASP",
    "C2_DUAL_SEAT",
    "C2_SETTLE",
)
OBS_DIM, ACT_DIM = 25, 6


def _sha256_file(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _groove_center_z():
    """Pure-CONSTANT SSOT read of task_config.GROOVE_CENTER_Z (no sim runtime pulled)."""
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, ".."))
    from configs.task_config import GROOVE_CENTER_Z  # noqa: PLC0415 - deliberate leaf-config read

    return float(GROOVE_CENTER_Z)


def _seg_rule(phase, frame, d, seated_seg, c2xy):
    """seg(t) rule per spec §2.3 / %9 §2.3a (per-phase, echoed into meta). Returns (seg_index, source_tag)."""
    p = 0 if phase < 0 else int(phase)
    if p <= 4:  # GRASP_HOVER..ROUTE_C1 -> nearest_seg_r
        return int(d["nearest_seg_r"][frame]), "nearest_seg_r"
    if p <= 6:  # C1_SEAT, C1_PIN -> seated seg (pinned_body-28 = 27; NOT phase-entry argmin 28)
        return int(seated_seg), "seated_seg(pinned-28)"
    if p <= 8:  # L_HALF_UNCLAMP, R_UNCLAMP_RISE -> grip-predicated held seg
        if float(d["grip_cmd"][frame, 0]) >= GRIP_CLOSED_RAD:  # col0 = L (E6)
            return int(d["held_seg_l"][frame]), "held_seg_l(grip>=0.6)"
        return int(d["nearest_seg_r"][frame]), "nearest_seg_r(grip<0.6)"
    # GUIDE_C2..C2_SETTLE -> nearest-to-C2, recomputed from cable_xyz (NOT recorder convenience indices)
    return int(np.argmin(np.linalg.norm(d["cable_xyz"][frame][:, :2] - c2xy, axis=1))), "argmin_to_c2"


# --- E15 fork-(iv): ABSOLUTE-TARGET action representation (per-phase x per-axis affine) ---
ABS_MARGIN = 0.10  # +-10% of the in-phase target range
ABS_FLOOR_M = 0.030  # guard-1 v2: minimum affine box span (30mm), centered on the midpoint
ABS_AXIS_NAMES = ("Rx", "Ry", "Rz", "Lx", "Ly", "Lz")  # R-then-L, matches the action layout


def _build_abs_affine(wp, ph):
    """Per-phase(13) x per-axis(6) affine box [lo,hi] [m] (E15 §10, v2 CRIT fix).

    lo/hi = in-phase target min/max +- ABS_MARGIN*range. guard-1 v2: any box span < ABS_FLOOR_M is
    widened to ABS_FLOOR_M centered on the midpoint (min+max)/2 (NOT median). Returns
    (affine[13,6,2] float64, guard1_record list). Asserts every phase owns >=1 control step.
    """
    affine = np.zeros((13, 6, 2), np.float64)
    guard1 = []
    for p in range(13):
        rows = np.where(ph == p)[0]
        assert rows.size > 0, f"E15 STOP: phase {p} ({PHASES13[p]}) has no control step -> affine undefined"
        wp_p = wp[rows]
        mn6, mx6 = wp_p.min(axis=0), wp_p.max(axis=0)
        for ax in range(6):
            mn, mx = float(mn6[ax]), float(mx6[ax])
            rng = mx - mn
            lo, hi = mn - ABS_MARGIN * rng, mx + ABS_MARGIN * rng
            if (hi - lo) < ABS_FLOOR_M:  # guard-1 v2: widen to 30mm centered on the midpoint
                mid = 0.5 * (mn + mx)
                lo, hi = mid - 0.5 * ABS_FLOOR_M, mid + 0.5 * ABS_FLOOR_M
                guard1.append(
                    {
                        "phase": p,
                        "phase_name": PHASES13[p],
                        "axis": ax,
                        "axis_name": ABS_AXIS_NAMES[ax],
                        "raw_range_mm": round(rng * 1000.0, 4),
                        "margined_span_mm": round(rng * 1.2 * 1000.0, 4),
                        "widened_to_mm": round(ABS_FLOOR_M * 1000.0, 4),
                    }
                )
            affine[p, ax] = (lo, hi)
    return affine, guard1


def _abs_encode(wp, ph, affine):
    """a = 2(wp - lo_p)/(hi_p - lo_p) - 1, per-phase p=ph[t] per-axis. Returns [T,6] float32."""
    lo, hi = affine[ph, :, 0], affine[ph, :, 1]  # [T,6] each (fancy-index by per-step phase)
    return (2.0 * (wp - lo) / (hi - lo) - 1.0).astype(np.float32)


def _abs_decode(a, ph, affine):
    """wp = lo_p + (a+1)/2 * (hi_p - lo_p). Exact inverse of :func:`_abs_encode`. Returns [T,6] float64."""
    lo, hi = affine[ph, :, 0], affine[ph, :, 1]
    return lo + 0.5 * (a.astype(np.float64) + 1.0) * (hi - lo)


def convert(npz_path, meta_path, out_dir, action_repr="delta"):
    d = np.load(npz_path)
    with open(meta_path) as fh:
        meta = json.load(fh)
    T = int(d["arm_q"].shape[0])

    # --- E3 schema gate: FROZEN 13-phase only ---
    if len(meta["phase_names"]) != 13:
        raise SystemExit(f"E3 STOP: expected 13-phase canonical npz, got {len(meta['phase_names'])} -> schema v2 (B2)")
    assert tuple(meta["phase_names"]) == PHASES13, f"phase-name mismatch: {meta['phase_names']}"

    # --- cadence (§2.1): control frames 0,10,..,7700 (771) -> 770 actions ---
    cf = np.arange(0, LAST_CTRL_FRAME + 1, PHYSICS_STEPS_PER_RL)
    assert cf[-1] == LAST_CTRL_FRAME and len(cf) == 771, (cf[-1], len(cf))
    tc = len(cf) - 1  # 770
    step_f, next_f = cf[:-1], cf[1:]  # obs at step_f; action = delta step_f -> next_f

    # --- actions [770,6] (§2.2, E6): R-then-L achieved ee_pos delta / scale ---
    er, el = d["ee_pos_r"].astype(np.float64), d["ee_pos_l"].astype(np.float64)
    d_r = (er[next_f] - er[step_f]) / POS_ACTION_SCALE
    d_l = (el[next_f] - el[step_f]) / POS_ACTION_SCALE
    actions = np.concatenate([d_r, d_l], axis=1).astype(np.float32)  # [770,6] = R(0:3)+L(3:6)

    # --- E4' cable_body_start validation (integer-exact argmin at the pin-fire frame) ---
    pin_frame = int(np.argmax(d["pin_active"] > 0))
    pinned_body, pin_eqid = int(d["pinned_body"][pin_frame]), int(d["pin_eqid"][pin_frame])
    c1xy, c2xy = np.array(meta["resolved_clip_c1_xy"]), np.array(meta["resolved_clip_c2_xy"])
    argmin_c1 = int(np.argmin(np.linalg.norm(d["cable_xyz"][pin_frame][:, :2] - c1xy, axis=1)))
    assert argmin_c1 == pinned_body - CABLE_BODY_START, (
        f"E4' STOP: argmin {argmin_c1} != {pinned_body}-{CABLE_BODY_START}"
    )
    seated_seg = pinned_body - CABLE_BODY_START  # = 27

    # --- quat-default assert (§2.4): effective quat == Rx(-90) ALL frames AND exactly ONE override window ---
    for arm in ("l", "r"):
        dev = float(np.abs(d[f"ee_tgt_quat_effective_{arm}"] - _DEFAULT_QUAT).max())
        if dev > 1e-6:
            raise SystemExit(f"§2.4 STOP: ee_tgt_quat_effective_{arm} deviates from Rx(-90) by {dev} (unsupported)")
    ov = d["ik_rot_override_active"].astype(int)
    edges = np.where(np.diff(ov) != 0)[0]
    on = np.where(ov == 1)[0]
    ov_window = [int(on[0]), int(on[-1])] if on.size else []
    if not (len(edges) == 2 and on.size):  # exactly one contiguous ON window
        raise SystemExit(f"§2.4 STOP: expected exactly ONE override window, edges={edges.tolist()}")

    # --- obs [770,25] (§2.3) ---
    ph_raw = d["phase_id"][step_f].astype(int)
    ph = np.where(ph_raw < 0, 0, ph_raw)  # -1 (pre-route settle) -> GRASP_HOVER (index 0)
    seg_pos = np.zeros((tc, 3), np.float64)
    seg_idx = np.zeros(tc, int)
    next_clip = np.zeros((tc, 3), np.float64)
    z_top = round(_groove_center_z() + float(meta["env_gates"].get("CLIP_FLOAT_Z") or 0.0), 6)  # 0.809+0.020=0.829
    seg_rule_by_phase = {}
    for t in range(tc):
        f = int(step_f[t])
        p = int(d["phase_id"][f])
        s, tag = _seg_rule(p, f, d, seated_seg, c2xy)
        seg_idx[t], seg_pos[t] = s, d["cable_xyz"][f, s]
        next_clip[t] = [
            *(c1xy if (0 if p < 0 else p) <= 6 else c2xy),
            z_top,
        ]  # C1 through C1_PIN; C2 from L_HALF_UNCLAMP
        seg_rule_by_phase.setdefault(PHASES13[0 if p < 0 else p], tag)
    onehot = np.zeros((tc, 13), np.float64)
    onehot[np.arange(tc), ph] = 1.0
    obs = np.concatenate([er[step_f], el[step_f], seg_pos, next_clip, onehot], axis=1).astype(np.float32)  # [770,25]

    # --- schedule.json (§2.4) ---
    grip_events = []
    for col, arm in ((0, "L"), (1, "R")):  # E6: col0=L, col1=R
        g = d["grip_cmd"][:, col]
        for f in np.where(np.diff(g) != 0)[0] + 1:
            grip_events.append({"frame": int(f), "arm": arm, "target_rad": round(float(g[f]), 6)})
    grip_events.sort(key=lambda e: e["frame"])
    assert d["grip_cmd"][0].tolist() == [0.0, 0.0], f"grip init != [0,0]: {d['grip_cmd'][0].tolist()}"
    assert len(grip_events) == 37, f"expected 37 per-arm grip transitions, got {len(grip_events)}"
    phase_transitions = [
        {
            "frame": int(f + 1),
            "to_phase": int(d["phase_id"][f + 1]),
            "name": (PHASES13[d["phase_id"][f + 1]] if d["phase_id"][f + 1] >= 0 else "PRE_SETTLE"),
        }
        for f in np.where(np.diff(d["phase_id"]) != 0)[0]
    ]
    # verdict landmark frames (CC3-6): recomputed by the evaluator §4.4 (frames + recorded references)

    def _phase_first(idx):
        w = np.where(d["phase_id"] == idx)[0]
        return int(w[0]) if w.size else None

    def _phase_last(idx):
        w = np.where(d["phase_id"] == idx)[0]
        return int(w[-1]) if w.size else None

    landmarks = {
        "c1_seat_landmark_frame": _phase_first(5),  # claw-partition freeze (C1_SEAT entry)
        "c2_hover_end_frame": _phase_last(10),  # reach target = recorded ee_tgt_pos_r there (C2_REGRASP end)
        "post_close_settle_end_frame": _phase_last(11),  # grip-force read (C2_DUAL_SEAT end)
        "c2_settle_end_frame": _phase_last(12),  # C2 seat check
    }
    schedule = {
        "grip_events": grip_events,
        "pin_event": {
            "frame": pin_frame,
            "pinned_body": pinned_body,
            "pin_eqid": pin_eqid,
            "anchor": "LIVE at fire (§4.5): seat-verify -> eq_data[3:6]=live seat-body pos; npz has NO anchor",
            "seated_seg": int(seated_seg),
            "cable_body_start": CABLE_BODY_START,
        },
        "phase_transitions": phase_transitions,
        "ik_rot_override": {
            "window": ov_window,
            "note": "effective quat==Rx(-90) all frames -> replay = plain solve_ik_dual (§4.3)",
        },
        "verdict_landmarks": landmarks,
        "ee_tgt_pos_r_at_c2_hover_end": d["ee_tgt_pos_r"][landmarks["c2_hover_end_frame"]].round(6).tolist()
        if landmarks["c2_hover_end_frame"] is not None
        else None,
        "cadence": {"physics_steps_per_rl": PHYSICS_STEPS_PER_RL, "t_ctrl": tc, "last_ctrl_frame": LAST_CTRL_FRAME},
    }

    # --- dataset meta (§2.5) ---
    ds_meta = {
        "schema": "BC_ROUTE_v1_13phase",
        "action_repr": "delta",  # E15: delta-side tag (abs branch overrides); phase_schema x action_repr orthogonal
        "source_npz": os.path.basename(npz_path),
        "source_npz_sha256": _sha256_file(npz_path),
        "source_meta_sha256": _sha256_file(meta_path),
        "source_as_run_sha256": meta.get("as_run_sha256"),
        "T_raw": T,
        "T_ctrl": tc,
        "obs_dim": OBS_DIM,
        "act_dim": ACT_DIM,
        "cadence_physics_steps_per_rl": PHYSICS_STEPS_PER_RL,
        "last_ctrl_frame": LAST_CTRL_FRAME,
        "pos_action_scale": POS_ACTION_SCALE,
        "action_layout": "[0:3]=Δee_pos_r/scale, [3:6]=Δee_pos_l/scale (R-then-L; achieved ee_pos delta)",
        "obs_layout": "[0:3]=ee_pos_r, [3:6]=ee_pos_l, [6:9]=seg_pos, [9:12]=next_clip_xyz, [12:25]=phase_onehot13",
        "grip_cmd_columns": "[0]=L, [1]=R (E6, OPPOSITE of action R-then-L)",
        "phase_names": list(PHASES13),
        "seg_rule_by_phase": seg_rule_by_phase,
        "seg_idx_min_max": [int(seg_idx.min()), int(seg_idx.max())],
        "cable_body_start": CABLE_BODY_START,
        "seated_seg": int(seated_seg),
        "next_clip_z_top": z_top,
        "z_top_formula": "task_config.GROOVE_CENTER_Z(0.809) + CLIP_FLOAT_Z(env_gate)",
        "resolved_clip_c1_xy": meta["resolved_clip_c1_xy"],
        "resolved_clip_c2_xy": meta["resolved_clip_c2_xy"],
        "override_window": ov_window,
        "env_gates": meta.get("env_gates"),  # SF-4 (%12-APPROVED): echo raw env_gates so the runner is self-contained
    }

    os.makedirs(out_dir, exist_ok=True)
    if action_repr == "delta":
        npz_out = os.path.join(out_dir, "bc_dataset.npz")
        tmp = npz_out + ".tmp.npz"
        np.savez(tmp, obs=obs, actions=actions, meta=json.dumps(ds_meta))
        os.replace(tmp, npz_out)
        with open(os.path.join(out_dir, "schedule.json"), "w") as fh:
            json.dump(schedule, fh, indent=2)
        with open(os.path.join(out_dir, "bc_dataset_meta.json"), "w") as fh:
            json.dump(ds_meta, fh, indent=2)
        return obs, actions, ds_meta, schedule, d, cf

    # --- E15 abs branch: absolute-target labels; the delta trio is NOT overwritten (assert-exists only) ---
    assert action_repr == "abs", f"unknown action_repr {action_repr!r}"
    delta_trio = ("bc_dataset.npz", "bc_dataset_meta.json", "schedule.json", "macro_schedule.json")
    missing = [f for f in delta_trio if not os.path.exists(os.path.join(out_dir, f))]
    if missing:
        raise SystemExit(f"E15 abs STOP: delta trio missing in {out_dir}: {missing} -> run --action-repr delta first")
    wp = np.concatenate([er[next_f], el[next_f]], axis=1)  # [770,6] absolute EE targets (R-then-L, = next waypoint)
    affine, guard1 = _build_abs_affine(wp, ph)
    labels = _abs_encode(wp, ph, affine)
    amax = float(np.abs(labels).max())
    assert amax <= 0.95, f"E15 abs STOP: max|a| {amax:.4f} > 0.95 (affine box too tight)"
    ds_meta_abs = dict(ds_meta)
    ds_meta_abs.update(
        {
            "schema": "BC_ROUTE_v1_13phase_abs",
            "action_repr": "abs",
            "phase_schema": 13,
            "action_layout": "[0:3]=abs ee_pos_r target, [3:6]=abs ee_pos_l target; "
            "a=2(wp-lo_p)/(hi_p-lo_p)-1 per-phase(13) per-axis(6)",
            "abs_affine": affine.tolist(),  # [13][6][2] = [lo,hi] per axis per phase [m]
            "abs_affine_axis_order": list(ABS_AXIS_NAMES),
            "abs_affine_margin": ABS_MARGIN,
            "guard1_floor_mm": round(ABS_FLOOR_M * 1000.0, 4),
            "guard1_widened": guard1,
            "source_delta_dataset_sha256": _sha256_file(os.path.join(out_dir, "bc_dataset.npz")),
        }
    )
    npz_abs = os.path.join(out_dir, "bc_dataset_abs.npz")
    tmp = npz_abs + ".tmp.npz"
    np.savez(tmp, obs=obs, actions=labels, meta=json.dumps(ds_meta_abs))
    os.replace(tmp, npz_abs)
    with open(os.path.join(out_dir, "bc_dataset_abs_meta.json"), "w") as fh:
        json.dump(ds_meta_abs, fh, indent=2)
    return obs, labels, ds_meta_abs, schedule, d, cf


def emit_macro_schedule(d, schedule, out_dir):
    """B0b (spec E14): extract macro-legs + map events/landmarks to legs -> macro_schedule.json.

    A macro-leg = a maximal run of consecutive frames with the SAME (ee_tgt_pos_l, ee_tgt_pos_r) tuple
    (= the ``ik_move_both`` entry targets = ``note_targets`` route :1950). Additive-only: the existing
    bc_dataset/schedule/meta outputs are unchanged.
    """
    tl, tr = d["ee_tgt_pos_l"].astype(np.float64), d["ee_tgt_pos_r"].astype(np.float64)
    key = np.concatenate([tl, tr], axis=1)  # [T,6]
    starts = [0, *(np.where(np.any(np.diff(key, axis=0) != 0.0, axis=1))[0] + 1).tolist()]
    ends = [s - 1 for s in starts[1:]] + [len(key) - 1]
    legs = [
        {
            "leg_idx": i,
            "target_l": tl[s].round(6).tolist(),
            "target_r": tr[s].round(6).tolist(),
            "frame_start": int(s),
            "frame_end": int(e),
        }
        for i, (s, e) in enumerate(zip(starts, ends))
    ]

    def _leg_of(frame):
        return next((lg["leg_idx"] for lg in legs if lg["frame_start"] <= frame <= lg["frame_end"]), None)

    grip_map = [{**ev, "leg_idx": _leg_of(int(ev["frame"]))} for ev in schedule["grip_events"]]
    pin_map = {"frame": schedule["pin_event"]["frame"], "leg_idx": _leg_of(int(schedule["pin_event"]["frame"]))}
    lm_map = {
        k: {"frame": int(v), "leg_idx": _leg_of(int(v))}
        for k, v in schedule["verdict_landmarks"].items()
        if v is not None
    }
    # self-check (E14): legs exist + cover the route contiguously + pin maps + leg0 target == demo ee frame0
    assert legs and legs[0]["frame_start"] == 0 and legs[-1]["frame_end"] == len(key) - 1, "E14: legs don't cover route"
    assert all(legs[i]["frame_end"] + 1 == legs[i + 1]["frame_start"] for i in range(len(legs) - 1)), "E14: leg gap"
    assert pin_map["leg_idx"] is not None, "E14: pin_event maps to no leg"
    assert np.allclose(tl[0], d["ee_pos_l"][0], atol=1e-3) and np.allclose(tr[0], d["ee_pos_r"][0], atol=1e-3), (
        "E14: leg0 target != demo ee frame0"
    )
    macro = {
        "n_legs": len(legs),
        "legs": legs,
        "event_leg_map": {"grip_events": grip_map, "pin_event": pin_map},
        "landmark_leg_map": lm_map,
        "note": "macro-leg = maximal run of const (ee_tgt_pos_l,ee_tgt_pos_r) = ik_move_both targets (route :1950)",
    }
    with open(os.path.join(out_dir, "macro_schedule.json"), "w") as fh:
        json.dump(macro, fh, indent=2)
    print(
        f"[route_demo_to_bc] wrote macro_schedule.json (n_legs={len(legs)}, pin@leg{pin_map['leg_idx']}) -> {out_dir}"
    )
    return macro


def self_check(obs, actions, ds_meta, schedule, d, cf):
    """§2.6 self-checks on the REAL npz + a 5-row human dump. Raises on any failure."""
    fails = []

    def ck(cond, msg):
        print(("  OK  " if cond else "  FAIL") + " " + msg)
        if not cond:
            fails.append(msg)

    ck(obs.shape == (770, 25), f"obs shape {obs.shape} == (770,25)")
    ck(actions.shape == (770, 6), f"actions shape {actions.shape} == (770,6)")
    repr_ = ds_meta.get("action_repr", "delta")
    a_bound = 0.95 if repr_ == "abs" else 1.0
    amx = float(np.abs(actions).max())
    ck(amx <= a_bound, f"|a|<={a_bound} (max {amx:.4f}, repr={repr_})")
    ck(bool(np.isfinite(obs).all() and np.isfinite(actions).all()), "obs+actions all finite")
    ck(np.allclose(obs[:, 12:25].sum(1), 1.0), "phase one-hot sums to 1 every row")
    if repr_ == "abs":
        # E15 abs round-trip: decode(labels) reconstructs the next-waypoint targets to <=0.01mm
        er = d["ee_pos_r"].astype(np.float64)
        el = d["ee_pos_l"].astype(np.float64)
        ph = np.where(d["phase_id"][cf[:-1]].astype(int) < 0, 0, d["phase_id"][cf[:-1]].astype(int))
        wp = np.concatenate([er[cf[1:]], el[cf[1:]]], axis=1)
        affine = np.asarray(ds_meta["abs_affine"], np.float64)
        rerr_mm = float(np.abs(_abs_decode(actions, ph, affine) - wp).max()) * 1000.0
        ck(rerr_mm <= 0.01, f"abs decode(labels)==wp round-trip {rerr_mm:.2e}mm <= 0.01mm")
        g = ds_meta.get("guard1_widened", [])
        echo = ", ".join(f"{x['phase_name']}/{x['axis_name']}" for x in g)
        print(f"  ECHO guard-1 fired on {len(g)} (phase,axis): {echo}")
    else:
        # delta cumulative reconstruction (achieved ee_pos): ee[cf[t+1]] = ee[0] + cumsum(a_R*scale)
        er = d["ee_pos_r"].astype(np.float64)
        recon = er[cf[0]] + np.cumsum(actions[:, 0:3].astype(np.float64) * 0.015, axis=0)
        rerr = float(np.abs(recon - er[cf[1:]]).max())
        ck(rerr < 1e-5, f"cumulative reconstruction err {rerr:.2e} < 1e-5")
    ck(len(ds_meta["seg_rule_by_phase"]) == 13, f"seg table covers 13 phases ({len(ds_meta['seg_rule_by_phase'])})")
    ck(d["grip_cmd"][0].tolist() == [0.0, 0.0], "grip init [0,0]")
    ck(len(schedule["grip_events"]) == 37, f"37 grip transitions ({len(schedule['grip_events'])})")
    ck(ds_meta["cable_body_start"] == 28 and ds_meta["seated_seg"] == 27, "cable_body_start=28 / seated_seg=27")
    ck(
        abs(ds_meta["next_clip_z_top"] - 0.829) < 1e-6,
        f"z_top {ds_meta['next_clip_z_top']} == 0.829 (canonical groove 829mm)",
    )
    ck(schedule["pin_event"]["frame"] == 2544, f"pin frame {schedule['pin_event']['frame']} == 2544")

    print("\n=== 5-row human dump (control steps 0, 254, 428, 550, 769) ===")
    print("  t  phase           ee_r(xyz)          a_r(xyz)           seg_pos(xyz)       next_clip(xyz)")
    for t in (0, 254, 428, 550, 769):
        p = int(np.argmax(obs[t, 12:25]))
        er3, ar3, sp, nc = obs[t, 0:3], actions[t, 0:3], obs[t, 6:9], obs[t, 9:12]
        print(
            f"  {t:3d} {PHASES13[p]:15s} [{er3[0]:.3f},{er3[1]:.3f},{er3[2]:.3f}]"
            f"  [{ar3[0]:+.3f},{ar3[1]:+.3f},{ar3[2]:+.3f}]  [{sp[0]:.3f},{sp[1]:.3f},{sp[2]:.3f}]"
            f"  [{nc[0]:.3f},{nc[1]:.3f},{nc[2]:.3f}]"
        )
    if fails:
        raise SystemExit(f"\n§2.6 SELF-CHECK: {len(fails)} FAIL -> {fails}")
    print("\n§2.6 SELF-CHECK: ALL PASS")


def main():
    ap = argparse.ArgumentParser(description="route_demo_raw.npz -> bc_dataset.npz + schedule.json (B spec §2)")
    ap.add_argument("--npz", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--action-repr", choices=["delta", "abs"], default="delta")  # E15 fork-(iv)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    obs, actions, ds_meta, schedule, d, cf = convert(a.npz, a.meta, a.out_dir, a.action_repr)
    out_name = "bc_dataset_abs.npz" if a.action_repr == "abs" else "bc_dataset.npz"
    print(
        f"[route_demo_to_bc] wrote {out_name} (obs {obs.shape}, actions {actions.shape}, "
        f"repr={a.action_repr}) -> {a.out_dir}"
    )
    if a.action_repr == "delta":
        emit_macro_schedule(d, schedule, a.out_dir)  # B0b (E14): delta-side macro; NOT re-emitted in abs mode
    if a.self_check:
        self_check(obs, actions, ds_meta, schedule, d, cf)


if __name__ == "__main__":
    main()
