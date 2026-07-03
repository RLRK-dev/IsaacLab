# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Offline converter: ``route_demo_raw.npz`` -> ``bc_dataset.npz`` + ``schedule.json`` (B_BC_BUILD_SPEC.md v2.2 §2).

Pure offline transform -- numpy + json + hashlib + a pure-CONSTANT SSOT read of
``task_config.GROOVE_CENTER_Z`` (no solver / mujoco / newton / env-runtime import; task_config is a
leaf config module, verified to pull no sim runtime). §10 ERRATA E1-E11 (+ E4'/E10/E11) binding.

DQ1=B pipeline, phase B0/B1. Consumes the 13-phase canonical npz (E3, schema v1) OR the 15-phase
CP-C npz (schema v2, B2 §1.3/§1.4). Produces the ``bc_pretrain.py`` (obs, actions) contract + an
evaluator replay ``schedule.json``. Actions are the ACHIEVED ee_pos deltas the route produced (R-then-L,
/POS_ACTION_SCALE); grip_cmd columns are [L, R] (E6, OPPOSITE of the action layout).

Schema-aware (B2): 13-phase (obs 25D) and 15-phase (obs 27D) share ``_seg_rule`` / obs / affine logic;
the 13-phase path is preserved BYTE-IDENTICAL (schema is parametrized with 13-phase defaults). The
15-schema = the 13-schema with 2 inserts: GUIDE_PRELIFT(idx10) after GUIDE_C2(9) and C2_TRANSPORT(idx12)
after C2_REGRASP(11). ``convert_b2`` builds a multi-demo UNION affine + whole-demo val split (§1.3/§1.4).
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
# E3: the FROZEN 13-phase canonical schema (v1). A DIFFERENT length that is NOT 15 => STOP.
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
# B2 (§1.4): the 15-phase CP-C schema (v2) = PHASES13 with 2 inserts:
#   GUIDE_PRELIFT at idx10 (after GUIDE_C2), C2_TRANSPORT at idx12 (after C2_REGRASP).
# Phases 0-8 are IDENTICAL to v1; both new phases (idx10, idx12) are >=9 -> argmin-to-C2 (see _seg_rule).
PHASES15 = (
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
    "GUIDE_PRELIFT",
    "C2_REGRASP",
    "C2_TRANSPORT",
    "C2_DUAL_SEAT",
    "C2_SETTLE",
)
_SCHEMAS = {13: PHASES13, 15: PHASES15}
OBS_DIM, ACT_DIM = 25, 6  # OBS_DIM = the v1 default (13-phase); obs_dim per-dataset = 12 + n_phases


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


def _detect_schema(meta):
    """Detect the phase schema (13 v1 / 15 v2) from ``meta['phase_names']``. Returns (n_phases, PHASES).

    A length that is NOT in {13, 15} => STOP (schema-version mismatch, keeps the E3 tag). The phase-name
    tuple must match the canonical schema exactly. Prints a loud echo (pin c) of the detected schema.
    """
    n = len(meta["phase_names"])
    if n not in _SCHEMAS:  # E3: only the frozen 13-phase (v1) / 15-phase (v2) schemas are supported
        raise SystemExit(f"E3 STOP: expected 13- or 15-phase canonical npz, got {n} -> unsupported schema")
    assert tuple(meta["phase_names"]) == _SCHEMAS[n], f"phase-name mismatch (schema {n}): {meta['phase_names']}"
    print(f"[route_demo_to_bc] SCHEMA={n}-phase (obs {12 + n}D)")
    return n, _SCHEMAS[n]


def _seg_rule(phase, frame, d, seated_seg, c2xy):
    """seg(t) rule per spec §2.3 / %9 §2.3a (per-phase, echoed into meta). Returns (seg_index, source_tag).

    Schema-correct for BOTH 13 and 15 with NO change (spec §1.4): phases 0-8 are identical in both
    schemas; ALL phases >=9 -- including the two 15-schema inserts GUIDE_PRELIFT/C2_TRANSPORT, which are
    argmin-to-C2 per spec §1.4 -- fall into the ``else`` argmin_to_c2 branch.
    """
    p = 0 if phase < 0 else int(phase)
    if p <= 4:  # GRASP_HOVER..ROUTE_C1 -> nearest_seg_r
        return int(d["nearest_seg_r"][frame]), "nearest_seg_r"
    if p <= 6:  # C1_SEAT, C1_PIN -> seated seg (pinned_body-28 = 27; NOT phase-entry argmin 28)
        return int(seated_seg), "seated_seg(pinned-28)"
    if p <= 8:  # L_HALF_UNCLAMP, R_UNCLAMP_RISE -> grip-predicated held seg
        if float(d["grip_cmd"][frame, 0]) >= GRIP_CLOSED_RAD:  # col0 = L (E6)
            return int(d["held_seg_l"][frame]), "held_seg_l(grip>=0.6)"
        return int(d["nearest_seg_r"][frame]), "nearest_seg_r(grip<0.6)"
    # GUIDE_C2..C2_SETTLE (incl. 15-schema GUIDE_PRELIFT/C2_TRANSPORT, spec §1.4) -> nearest-to-C2,
    # recomputed from cable_xyz (NOT recorder convenience indices)
    return int(np.argmin(np.linalg.norm(d["cable_xyz"][frame][:, :2] - c2xy, axis=1))), "argmin_to_c2"


# --- E15 fork-(iv): ABSOLUTE-TARGET action representation (per-phase x per-axis affine) ---
ABS_MARGIN = 0.10  # +-10% of the in-phase target range
ABS_FLOOR_M = 0.030  # guard-1 v2: minimum affine box span (30mm), centered on the midpoint
ABS_AXIS_NAMES = ("Rx", "Ry", "Rz", "Lx", "Ly", "Lz")  # R-then-L, matches the action layout


def _build_abs_affine(wp, ph, n_phases=13, phases=PHASES13):
    """Per-phase(n) x per-axis(6) affine box [lo,hi] [m] (E15 §10, v2 CRIT fix). Schema-parametric.

    lo/hi = in-phase target min/max +- ABS_MARGIN*range. guard-1 v2: any box span < ABS_FLOOR_M is
    widened to ABS_FLOOR_M centered on the midpoint (min+max)/2 (NOT median). Returns
    (affine[n_phases,6,2] float64, guard1_record list). Asserts every phase owns >=1 control step.
    Default args (13, PHASES13) keep 13-phase callers byte-identical.
    """
    affine = np.zeros((n_phases, 6, 2), np.float64)
    guard1 = []
    for p in range(n_phases):
        rows = np.where(ph == p)[0]
        if rows.size == 0:
            # Phase defined in the schema but ABSENT in the data (e.g. the 15-schema GUIDE_C2 idx9 is skipped
            # by the CP-C route -> never at a control step). No row carries this phase, so _abs_encode/_abs_decode
            # never index affine[p]; assign an INERT valid placeholder box (floor-wide, centred on 0) and move on.
            # (13-phase v1 never has an empty phase -> this branch never fires there -> byte-identity preserved.)
            affine[p] = np.array([[-0.5 * ABS_FLOOR_M, 0.5 * ABS_FLOOR_M]] * 6, np.float64)
            continue
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
                        "phase_name": phases[p],
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


def _assert_e4prime(d, meta, strict=True):
    """E4' cable_body_start validation. Shared by convert() and _compute_demo (do NOT duplicate).

    ``seated_seg = pinned_body - CABLE_BODY_START`` is the STRUCTURAL body->segment offset (verified
    constant = 28 across all survivors, nseg=40, on every well-seated demo). The argmin-to-C1 cross-check
    is a SEATING-QUALITY gate: when the cable is well-seated at the pin frame the pinned segment IS the
    segment physically nearest to C1 (argmin == seated_seg). ``strict=True`` (single-demo path, incl. the
    frozen 13-phase canonical) RAISES on a mismatch; ``strict=False`` (B2 multi-demo) records it as a
    quality flag so poorly-seated but CURATED survivors proceed with the structural (pinned) seg -- which
    also matches the runner's ``_live_seg_pos`` obs (policy_route_runner.py:117-118, seated_body_row).
    Returns (pin_frame, pinned_body, pin_eqid, c1xy, c2xy, seated_seg, seat_quality).
    """
    pin_frame = int(np.argmax(d["pin_active"] > 0))
    pinned_body, pin_eqid = int(d["pinned_body"][pin_frame]), int(d["pin_eqid"][pin_frame])
    c1xy, c2xy = np.array(meta["resolved_clip_c1_xy"]), np.array(meta["resolved_clip_c2_xy"])
    seated_seg = pinned_body - CABLE_BODY_START  # structural body->segment offset (= 27 for the canonical demo)
    argmin_c1 = int(np.argmin(np.linalg.norm(d["cable_xyz"][pin_frame][:, :2] - c1xy, axis=1)))
    seat_dist_mm = float(np.linalg.norm(d["cable_xyz"][pin_frame][argmin_c1][:2] - c1xy)) * 1000.0
    matches = argmin_c1 == seated_seg
    if strict and not matches:
        raise SystemExit(f"E4' STOP: argmin {argmin_c1} != {pinned_body}-{CABLE_BODY_START}")
    seat_quality = {
        "argmin_c1": argmin_c1,
        "seated_seg": int(seated_seg),
        "argmin_matches_pinned": bool(matches),
        "seat_dist_mm": round(seat_dist_mm, 2),
    }
    return pin_frame, pinned_body, pin_eqid, c1xy, c2xy, seated_seg, seat_quality


def _assert_quat_default(d):
    """quat-default assert (§2.4): effective quat == Rx(-90) ALL frames AND exactly ONE override window.
    Shared by convert() and _compute_demo (do NOT duplicate). Returns ov_window [start,end] (or [])."""
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
    return ov_window


def _compute_demo(npz_path, meta_path, strict_e4=True):
    """Shared obs/wp/ph computation (§2.1-2.3, schema-aware) reused by convert() and convert_b2().

    Loads the raw npz+meta, detects the schema, runs the E4'/quat asserts (via the shared helpers -- NOT
    duplicated), and computes the cadence, obs[770, 12+n], per-step next-waypoint EE target wp[770,6],
    and the per-phase seg rule. ``strict_e4`` (default True) hard-fails on an E4' seating-quality mismatch
    (single-demo path); convert_b2 passes strict_e4=False (records the mismatch, proceeds). Returns a dict;
    ``obs``/``wp``/``ph``/``n_phases``/``PHASES``/``seg_rule_by_phase``/``d``/``cf`` are the brief-required
    keys, plus the fields convert() / convert_b2 need (incl. ``seat_quality``).
    """
    d = np.load(npz_path)
    with open(meta_path) as fh:
        meta = json.load(fh)
    T = int(d["arm_q"].shape[0])
    n_phases, PHASES = _detect_schema(meta)

    # --- cadence (§2.1): control frames 0,10,..,7700 (771) -> 770 actions ---
    cf = np.arange(0, LAST_CTRL_FRAME + 1, PHYSICS_STEPS_PER_RL)
    assert cf[-1] == LAST_CTRL_FRAME and len(cf) == 771, (cf[-1], len(cf))
    tc = len(cf) - 1  # 770
    step_f, next_f = cf[:-1], cf[1:]  # obs at step_f; action = delta step_f -> next_f

    er, el = d["ee_pos_r"].astype(np.float64), d["ee_pos_l"].astype(np.float64)

    # --- E4' + quat-default asserts (shared helpers; no output side effect) ---
    pin_frame, pinned_body, pin_eqid, c1xy, c2xy, seated_seg, seat_quality = _assert_e4prime(d, meta, strict=strict_e4)
    ov_window = _assert_quat_default(d)

    # --- obs [770, 12+n_phases] (§2.3) ---
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
        seg_rule_by_phase.setdefault(PHASES[0 if p < 0 else p], tag)
    onehot = np.zeros((tc, n_phases), np.float64)
    onehot[np.arange(tc), ph] = 1.0
    obs = np.concatenate([er[step_f], el[step_f], seg_pos, next_clip, onehot], axis=1).astype(np.float32)
    wp = np.concatenate([er[next_f], el[next_f]], axis=1)  # [770,6] absolute EE targets (R-then-L, = next waypoint)

    return {
        "d": d,
        "meta": meta,
        "T": T,
        "n_phases": n_phases,
        "PHASES": PHASES,
        "cf": cf,
        "step_f": step_f,
        "next_f": next_f,
        "tc": tc,
        "er": er,
        "el": el,
        "ph": ph,
        "obs": obs,
        "wp": wp,
        "seg_idx": seg_idx,
        "seg_pos": seg_pos,
        "next_clip": next_clip,
        "seg_rule_by_phase": seg_rule_by_phase,
        "z_top": z_top,
        "pin_frame": pin_frame,
        "pinned_body": pinned_body,
        "pin_eqid": pin_eqid,
        "seated_seg": seated_seg,
        "seat_quality": seat_quality,
        "c1xy": c1xy,
        "c2xy": c2xy,
        "ov_window": ov_window,
    }


def _mask_injection(dm):
    """DQ7 stage-(ii) kick-and-recover mask (mini-spec v2 §F; %9 C1 command-keyed).

    DROP the control-frames whose obs frame (``step_f``) OR action-target frame (``next_f``) lies in an injection KICK
    window (``meta['injection_windows']`` ``[start_frame, end_frame)`` = the frames whose COMMANDED target carried the
    offset = the anti-restoring outbound); KEEP the rest (post-release recovery = the restoring teacher). KEEP/DROP is
    keyed on window MEMBERSHIP (== commanded-offset==0), NOT the achieved ee_pos -- a recovery frame's achieved is
    legitimately off-path (script+offset -> script transit); an achieved-keyed drop would delete the restoring teacher
    = a FALSE Outcome-B (%9 C1). No-op when ``injection_windows`` is empty (clean demos -> the SAME dict is returned ->
    byte-identity). The union affine is later built over the masked ``wp`` so the {1}/{11} per-phase box EXPANDS to fit
    the kept recovery excursions with ``amax<=0.95`` by margin (%9 C2, expand-not-clip, automatic in _build_abs_affine).
    """
    wins = dm["meta"].get("injection_windows") or []
    if not wins:
        return dm  # clean demo: untouched -> byte-identity of the normal b2 build
    step_f, next_f, tc0 = dm["step_f"], dm["next_f"], dm["tc"]
    kick = np.zeros(int(dm["T"]), dtype=bool)  # per-physics-frame kick flag
    for w in wins:
        kick[int(w["start_frame"]):int(w["end_frame"])] = True
    keep = ~(kick[step_f] | kick[next_f])  # drop a control-frame if its obs OR its action-target frame is a kick frame
    # %9 C1 command-key self-consistency: no KEPT control-frame touches a kick window (offset==0 by construction)
    assert not (kick[step_f[keep]].any() or kick[next_f[keep]].any()), "p2r mask STOP: a kept row still touches a kick window"
    for k in ("obs", "wp", "ph", "step_f", "next_f", "seg_idx", "seg_pos", "next_clip"):
        dm[k] = dm[k][keep]
    dm["tc"] = int(keep.sum())
    dm["n_p2r_dropped"], dm["n_injection_windows"] = int((~keep).sum()), len(wins)
    print(
        f"[route_demo_to_bc] p2r mask: {len(wins)} kick window(s) -> dropped {dm['n_p2r_dropped']}/{tc0} outbound/kick "
        f"control-frames, kept {dm['tc']} (recovery+normal; command-keyed on injection_windows, %9 C1)"
    )
    return dm


def convert(npz_path, meta_path, out_dir, action_repr="delta"):
    dm = _compute_demo(npz_path, meta_path)  # E3 schema gate + shared obs/wp/ph (13 v1 / 15 v2)
    d, meta = dm["d"], dm["meta"]
    n_phases, PHASES = dm["n_phases"], dm["PHASES"]
    cf, step_f, next_f, tc = dm["cf"], dm["step_f"], dm["next_f"], dm["tc"]
    er, el, T = dm["er"], dm["el"], dm["T"]
    obs, ph, wp = dm["obs"], dm["ph"], dm["wp"]
    seg_idx, z_top = dm["seg_idx"], dm["z_top"]
    seg_rule_by_phase = dm["seg_rule_by_phase"]
    pin_frame, pinned_body, pin_eqid = dm["pin_frame"], dm["pinned_body"], dm["pin_eqid"]
    seated_seg = dm["seated_seg"]
    ov_window = dm["ov_window"]

    # --- actions [770,6] (§2.2, E6): R-then-L achieved ee_pos delta / scale ---
    d_r = (er[next_f] - er[step_f]) / POS_ACTION_SCALE
    d_l = (el[next_f] - el[step_f]) / POS_ACTION_SCALE
    actions = np.concatenate([d_r, d_l], axis=1).astype(np.float32)  # [770,6] = R(0:3)+L(3:6)

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
            "name": (PHASES[d["phase_id"][f + 1]] if d["phase_id"][f + 1] >= 0 else "PRE_SETTLE"),
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

    # NAME-based landmark indices (schema-robust; identical to the 13-phase literals 5/10/11/12 because
    # PHASES13.index(...) == 5/10/11/12, byte-identical for v1; correct under 15-phase where C2_REGRASP/
    # C2_DUAL_SEAT/C2_SETTLE shift to 11/13/14).
    landmarks = {
        "c1_seat_landmark_frame": _phase_first(PHASES.index("C1_SEAT")),  # claw-partition freeze (C1_SEAT entry)
        "c2_hover_end_frame": _phase_last(PHASES.index("C2_REGRASP")),  # reach target = recorded ee_tgt_pos_r there
        "post_close_settle_end_frame": _phase_last(PHASES.index("C2_DUAL_SEAT")),  # grip-force read
        "c2_settle_end_frame": _phase_last(PHASES.index("C2_SETTLE")),  # C2 seat check
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
    schema_base = f"BC_ROUTE_v{'1' if n_phases == 13 else '2'}_{n_phases}phase"
    ds_meta = {
        "schema": schema_base,
        "action_repr": "delta",  # E15: delta-side tag (abs branch overrides); phase_schema x action_repr orthogonal
        "source_npz": os.path.basename(npz_path),
        "source_npz_sha256": _sha256_file(npz_path),
        "source_meta_sha256": _sha256_file(meta_path),
        "source_as_run_sha256": meta.get("as_run_sha256"),
        "T_raw": T,
        "T_ctrl": tc,
        "obs_dim": 12 + n_phases,
        "act_dim": ACT_DIM,
        "cadence_physics_steps_per_rl": PHYSICS_STEPS_PER_RL,
        "last_ctrl_frame": LAST_CTRL_FRAME,
        "pos_action_scale": POS_ACTION_SCALE,
        "action_layout": "[0:3]=Δee_pos_r/scale, [3:6]=Δee_pos_l/scale (R-then-L; achieved ee_pos delta)",
        "obs_layout": (
            f"[0:3]=ee_pos_r, [3:6]=ee_pos_l, [6:9]=seg_pos, [9:12]=next_clip_xyz, "
            f"[12:{12 + n_phases}]=phase_onehot{n_phases}"
        ),
        "grip_cmd_columns": "[0]=L, [1]=R (E6, OPPOSITE of action R-then-L)",
        "phase_names": list(PHASES),
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
    affine, guard1 = _build_abs_affine(wp, ph, n_phases, PHASES)
    labels = _abs_encode(wp, ph, affine)
    amax = float(np.abs(labels).max())
    assert amax <= 0.95, f"E15 abs STOP: max|a| {amax:.4f} > 0.95 (affine box too tight)"
    ds_meta_abs = dict(ds_meta)
    ds_meta_abs.update(
        {
            "schema": schema_base + "_abs",
            "action_repr": "abs",
            "phase_schema": n_phases,
            "action_layout": "[0:3]=abs ee_pos_r target, [3:6]=abs ee_pos_l target; "
            f"a=2(wp-lo_p)/(hi_p-lo_p)-1 per-phase({n_phases}) per-axis(6)",
            "abs_affine": affine.tolist(),  # [n_phases][6][2] = [lo,hi] per axis per phase [m]
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


# --- B2 (§1.3/§1.4): multi-demo UNION-affine schema-v2 build ---
# CP-C XY start-offset resolution is META-AUTHORITATIVE (W0, Option B, ``_offset_from_meta``): the recorder
# writes ``env_gates.CABLE_XY_OFFSET`` (a ``"dx,dy"`` METERS string) -> (x, y) mm for any recording,
# independent of the dir name. When that key is absent/empty the legacy dir-basename ``rec_<x>_<y>`` encoding
# is used (preserves the exact offsets -- hence byte-identity -- of the pre-existing rec_<x>_<y> demos); an
# arbitrarily-named legacy recording with no meta offset (e.g. ``rec_d1a`` at IC(0,0)) resolves to (0, 0).
# The dir basename (NOT the offset) is the unique per-recording identity, so two same-IC recordings never
# collide on a forced ``rec_0_0`` name. Hull-vertex vs interior sets are the brief §Survivor-set constants
# (used to pick the whole-demo val split from the interior).
B2_HULL_VERTEX_OFFSETS = frozenset({(20, 0), (-20, 0), (0, 20), (20, -20), (-20, 20), (-20, -20)})
B2_INTERIOR_OFFSETS = frozenset({(0, 0), (10, 0), (-10, 0), (0, 10), (0, -10)})
B2_VERDICT_CRITICAL_PHASES = ("C1_SEAT", "C1_PIN", "C2_REGRASP", "C2_DUAL_SEAT", "C2_SETTLE")


def _offset_from_npz_path(npz_path):
    """Legacy dir-name parser: CP-C XY offset (x, y) mm from basename ``rec_<x>_<y>``; ``None`` if non-conforming.

    Token rule: ``z0``/``0``/``z`` -> 0, ``p<N>`` -> +N, ``m<N>`` -> -N. Returns ``None`` (non-fatal, W0) when
    the basename is not ``rec_<x>_<y>`` so an arbitrarily-named recording (e.g. ``rec_d1a``) no longer STOPs the
    build; :func:`_offset_from_meta` is the authoritative resolver that falls back through this to (0, 0).
    """
    base = os.path.basename(os.path.dirname(os.path.abspath(npz_path)))
    parts = base.split("_")
    if len(parts) != 3 or parts[0] != "rec":
        return None

    def _tok(t):
        if t in ("z0", "0", "z"):
            return 0
        if t and t[0] == "p" and t[1:].isdigit():
            return int(t[1:])
        if t and t[0] == "m" and t[1:].isdigit():
            return -int(t[1:])
        return None

    x, y = _tok(parts[1]), _tok(parts[2])
    return None if (x is None or y is None) else (x, y)


def _offset_from_meta(npz_path, meta):
    """Resolve the CP-C XY start-offset (x, y) mm, META-authoritative (W0, Option B; dir-name-independent).

    Priority: (1) ``meta['env_gates']['CABLE_XY_OFFSET']`` -- a ``"dx,dy"`` METERS string -> (x, y) mm, the
    authoritative source the recorder writes for any recording regardless of dir name; (2) the legacy dir
    basename ``rec_<x>_<y>`` (:func:`_offset_from_npz_path`) when that key is absent/empty, preserving the exact
    offsets (hence byte-identity) of the pre-existing rec_<x>_<y> demos; (3) (0, 0) for an arbitrarily-named
    legacy recording with no meta offset (e.g. ``rec_d1a`` / ``rec_c11`` at IC(0,0)). The per-recording IDENTITY
    used for audit ``dir`` / dict keys is the dir basename, never this offset -- so two same-IC recordings (both
    (0, 0)) stay distinct instead of colliding on a single forced ``rec_0_0`` name.

    Args:
        npz_path: path to the demo ``route_demo_raw.npz`` (its dir basename is the legacy-offset / identity source).
        meta: the already-parsed ``route_demo_raw_meta.json`` dict (holds ``env_gates.CABLE_XY_OFFSET`` if present).
    """
    raw = (meta.get("env_gates") or {}).get("CABLE_XY_OFFSET")
    if raw is not None and str(raw).strip():
        dx, dy = (float(v) for v in str(raw).split(","))
        return (int(round(dx * 1000.0)), int(round(dy * 1000.0)))
    dirn = _offset_from_npz_path(npz_path)
    return dirn if dirn is not None else (0, 0)


def convert_b2(train_specs, heldout_specs, out_dir, seed=0):
    """Multi-demo UNION-affine schema-v2 BC dataset (B2, spec §1.3/§1.4).

    Args:
        train_specs: list of (npz_path, meta_path) for the train demos (offsets from the dir name).
        heldout_specs: list of (npz_path, meta_path) for the held-out (generalization) demos.
        out_dir: output dir for bc_dataset_abs.npz + bc_dataset_abs_val.npz + bc_dataset_abs_meta.json.
        seed: RNG seed for the deterministic whole-demo val split (default 0).

    Builds ONE union affine over ALL train demos (pin a), encodes every train demo with it, deterministically
    holds out 2 whole demos for val from the NON-hull-vertex interior set (pin b), asserts the 3 held-out
    demos are interior to the union hull (pin d), and reports round-trip mm + a per-phase box-span audit.
    Returns a dict of the built arrays / meta / dispositions for reporting. No solver/sim import.
    """
    # strict_e4=False: the E4' argmin cross-check is a SEATING-QUALITY gate, not the structural offset (=28,
    # constant). A few CURATED survivors are poorly seated at the pin frame (argmin != pinned-28); they proceed
    # with the structural pinned seg (recorded loudly in seat_quality_audit) rather than crashing the union build.
    # DQ7 (ii): _mask_injection is a no-op for clean demos (injection_windows=[]) -> byte-identity of the normal b2
    # build; for injected recordings it DROPs the kick frames (command-keyed, %9 C1) BEFORE the union affine (%9 C2).
    train = [_mask_injection(_compute_demo(npz, meta, strict_e4=False)) for (npz, meta) in train_specs]
    held = [_mask_injection(_compute_demo(npz, meta, strict_e4=False)) for (npz, meta) in heldout_specs]
    assert train, "B2 STOP: empty train_specs"
    n_phases, PHASES = train[0]["n_phases"], train[0]["PHASES"]
    for demo in train + held:
        assert demo["n_phases"] == n_phases, f"B2 STOP: mixed schema {demo['n_phases']} != {n_phases}"
    print(
        f"[route_demo_to_bc] B2 UNION build: SCHEMA={n_phases}-phase (obs {12 + n_phases}D), "
        f"{len(train)} train + {len(held)} held-out demos, seed={seed}"
    )

    # W0: offset is META-authoritative (env_gates.CABLE_XY_OFFSET), reusing the meta already loaded into each
    # demo dict; dir-basename rec_<x>_<y> is the legacy fallback (byte-identical for the pre-existing demos).
    train_off = [_offset_from_meta(train_specs[i][0], train[i]["meta"]) for i in range(len(train))]
    held_off = [_offset_from_meta(heldout_specs[i][0], held[i]["meta"]) for i in range(len(held))]

    # --- E4' seating-quality audit (structural offset is 28; argmin mismatch => poorly-seated demo) ---
    seat_quality_audit = []
    _rows = [(train_specs[i][0], train[i], train_off[i], "train") for i in range(len(train))]
    _rows += [(heldout_specs[i][0], held[i], held_off[i], "heldout") for i in range(len(held))]
    for npz, demo, off, role in _rows:
        sq = demo["seat_quality"]
        entry = {"offset": list(off), "dir": os.path.basename(os.path.dirname(os.path.abspath(npz))), "role": role, **sq}
        seat_quality_audit.append(entry)
        if not sq["argmin_matches_pinned"]:
            print(
                f"[route_demo_to_bc] B2 SEAT-QUALITY WARN: {role} {off} pinned_seg={sq['seated_seg']} "
                f"!= argmin_to_C1={sq['argmin_c1']} (seat_dist={sq['seat_dist_mm']}mm at pin); using structural "
                f"pinned seg for obs seg_pos (matches runner _live_seg_pos; affine/labels unaffected)"
            )
    _n_seat_mismatch = sum(1 for e in seat_quality_audit if not e["argmin_matches_pinned"])

    # --- pin a: UNION affine over ALL train demos ---
    wp_all = np.concatenate([demo["wp"] for demo in train], axis=0)
    ph_all = np.concatenate([demo["ph"] for demo in train], axis=0)
    affine, guard1 = _build_abs_affine(wp_all, ph_all, n_phases, PHASES)
    empty_phases = [p for p in range(n_phases) if not np.any(ph_all == p)]
    if empty_phases:  # e.g. 15-schema GUIDE_C2 (idx9) is skipped by the route -> defined slot, no data
        print(
            f"[route_demo_to_bc] B2 EMPTY-PHASE: {[(p, PHASES[p]) for p in empty_phases]} absent at all control "
            f"steps across the {len(train)} train demos -> inert placeholder affine box (never decoded; slot kept "
            f"for onehot/phase_id index alignment)"
        )

    # encode each train demo with the union affine; assert |labels|<=0.95 across ALL train demos
    union_max_abs_a = 0.0
    for demo in train:
        demo["labels"] = _abs_encode(demo["wp"], demo["ph"], affine)
        union_max_abs_a = max(union_max_abs_a, float(np.abs(demo["labels"]).max()))
    assert union_max_abs_a <= 0.95, f"B2 STOP: union max|a| {union_max_abs_a:.4f} > 0.95 over {len(train)} train demos"

    # --- round-trip DoD: decode(encode(wp)) == wp for every train demo (<= 1e-3mm hard bound) ---
    roundtrip_max_mm = 0.0
    for demo in train:
        rec = _abs_decode(demo["labels"], demo["ph"], affine)
        roundtrip_max_mm = max(roundtrip_max_mm, float(np.abs(rec - demo["wp"]).max()) * 1000.0)
    assert roundtrip_max_mm <= 1e-3, f"B2 STOP: round-trip max {roundtrip_max_mm:.3e}mm > 1e-3mm"

    # --- pin b: deterministic WHOLE-DEMO val split from the NON-hull-vertex interior set ---
    for off in train_off:
        if off not in B2_HULL_VERTEX_OFFSETS and off not in B2_INTERIOR_OFFSETS:
            raise SystemExit(f"B2 STOP: train offset {off} in neither hull-vertex nor interior set")
    interior_idx = sorted(
        (i for i, off in enumerate(train_off) if off in B2_INTERIOR_OFFSETS),
        key=lambda i: train_off[i],
    )
    assert len(interior_idx) >= 2, f"B2 STOP: need >=2 interior (non-hull-vertex) demos for val, got {len(interior_idx)}"
    rs = np.random.RandomState(seed)
    pick = rs.choice(len(interior_idx), size=2, replace=False)
    val_idx = sorted(interior_idx[int(p)] for p in pick)
    val_set = set(val_idx)
    val_off = [train_off[i] for i in val_idx]
    train_keep_idx = [i for i in range(len(train)) if i not in val_set]
    train_keep_off = [train_off[i] for i in train_keep_idx]
    print(
        f"[route_demo_to_bc] B2 val split (seed={seed}): FROZEN val demos = {val_off} "
        f"(picked from interior {sorted(B2_INTERIOR_OFFSETS)}); {len(train_keep_idx)} train demos remain"
    )

    # --- concat train (keep) / val, both encoded with the SAME union affine ---
    obs_train = np.concatenate([train[i]["obs"] for i in train_keep_idx], axis=0)
    labels_train = np.concatenate([train[i]["labels"] for i in train_keep_idx], axis=0)
    obs_val = np.concatenate([train[i]["obs"] for i in val_idx], axis=0)
    labels_val = np.concatenate([train[i]["labels"] for i in val_idx], axis=0)

    # --- pin d (§1.3-ii): hull assert on the held-out demos (interior vs EXTRAPOLATION, loud reclassify) ---
    held_disp = []
    survivors = 0
    for demo, off in zip(held, held_off):
        a_h = _abs_encode(demo["wp"], demo["ph"], affine)
        mx = float(np.abs(a_h).max())
        interior = mx <= 1.0
        held_disp.append(
            {"offset": list(off), "max_abs_a": round(mx, 6), "disposition": "interior" if interior else "EXTRAPOLATION"}
        )
        if interior:
            survivors += 1
        else:
            print(f"[route_demo_to_bc] B2 HULL RECLASSIFY: held-out {off} max|a|={mx:.4f} > 1.0 -> EXTRAPOLATION")
    if survivors < 3:
        raise SystemExit(f"B2 STOP: only {survivors} held-out survive as interior (<3); union hull under-covers")

    # --- box-span audit: per-phase per-axis span (hi-lo) [m]; flag any below the guard-1 floor ---
    # (empty/placeholder phases are excluded from the min/max + degenerate scan and listed separately)
    span = affine[:, :, 1] - affine[:, :, 0]  # [n_phases, 6]
    empty_set = set(empty_phases)
    real_p = [p for p in range(n_phases) if p not in empty_set]
    degenerate = [
        {
            "phase": p,
            "phase_name": PHASES[p],
            "axis": ax,
            "axis_name": ABS_AXIS_NAMES[ax],
            "span_mm": round(float(span[p, ax]) * 1000.0, 4),
        }
        for p in real_p
        for ax in range(6)
        if span[p, ax] < ABS_FLOOR_M - 1e-9
    ]
    real_span = span[real_p] if real_p else span
    box_span_audit = {
        "min_span_mm": round(float(real_span.min()) * 1000.0, 4),
        "max_span_mm": round(float(real_span.max()) * 1000.0, 4),
        "floor_mm": round(ABS_FLOOR_M * 1000.0, 4),
        "empty_phases": [{"phase": p, "phase_name": PHASES[p]} for p in empty_phases],
        "degenerate_below_floor": degenerate,
        "verdict_critical_phases": list(B2_VERDICT_CRITICAL_PHASES),
        "verdict_critical_span_mm": {
            PHASES[p]: [round(float(span[p, ax]) * 1000.0, 4) for ax in range(6)]
            for p in range(n_phases)
            if PHASES[p] in B2_VERDICT_CRITICAL_PHASES
        },
    }

    # --- provenance: per-demo sha + hull/split disposition ---
    per_demo = []
    for i, (npz, meta) in enumerate(train_specs):
        off = train_off[i]
        per_demo.append(
            {
                "offset": list(off),
                "dir": os.path.basename(os.path.dirname(os.path.abspath(npz))),
                "source_npz_sha256": _sha256_file(npz),
                "source_meta_sha256": _sha256_file(meta),
                "hull_class": "hull_vertex" if off in B2_HULL_VERTEX_OFFSETS else "interior",
                "split": "val" if i in val_set else "train",
            }
        )
    per_heldout = []
    for i, (npz, meta) in enumerate(heldout_specs):
        per_heldout.append(
            {
                "offset": list(held_off[i]),
                "dir": os.path.basename(os.path.dirname(os.path.abspath(npz))),
                "source_npz_sha256": _sha256_file(npz),
                "source_meta_sha256": _sha256_file(meta),
                "max_abs_a": held_disp[i]["max_abs_a"],
                "disposition": held_disp[i]["disposition"],
            }
        )

    schema_base = f"BC_ROUTE_v{'1' if n_phases == 13 else '2'}_{n_phases}phase"
    ds_meta = {
        "schema": schema_base + "_abs",
        "dataset_kind": "b2_multi_union",
        "action_repr": "abs",
        "phase_schema": n_phases,
        "phase_names": list(PHASES),
        "phase_idx_table": {str(i): PHASES[i] for i in range(n_phases)},
        "obs_dim": 12 + n_phases,
        "act_dim": ACT_DIM,
        "cadence_physics_steps_per_rl": PHYSICS_STEPS_PER_RL,
        "last_ctrl_frame": LAST_CTRL_FRAME,
        "pos_action_scale": POS_ACTION_SCALE,
        "action_layout": (
            "[0:3]=abs ee_pos_r target, [3:6]=abs ee_pos_l target; "
            f"a=2(wp-lo_p)/(hi_p-lo_p)-1 per-phase({n_phases}) per-axis(6) (UNION affine over all train demos)"
        ),
        "obs_layout": (
            f"[0:3]=ee_pos_r, [3:6]=ee_pos_l, [6:9]=seg_pos, [9:12]=next_clip_xyz, "
            f"[12:{12 + n_phases}]=phase_onehot{n_phases}"
        ),
        "abs_affine": affine.tolist(),  # union [n_phases][6][2] = [lo,hi] per axis per phase [m]
        "abs_affine_axis_order": list(ABS_AXIS_NAMES),
        "abs_affine_margin": ABS_MARGIN,
        "guard1_floor_mm": round(ABS_FLOOR_M * 1000.0, 4),
        "guard1_widened": guard1,
        "box_span_audit": box_span_audit,
        "empty_phases": [{"phase": p, "phase_name": PHASES[p]} for p in empty_phases],
        "next_clip_z_top": train[0]["z_top"],
        "cable_body_start": CABLE_BODY_START,
        "seated_seg": int(train[0]["seated_seg"]),
        "resolved_clip_c1_xy": train[0]["meta"]["resolved_clip_c1_xy"],
        "resolved_clip_c2_xy": train[0]["meta"]["resolved_clip_c2_xy"],
        "seed": seed,
        "val_demo_offsets": [list(o) for o in val_off],
        "train_demo_offsets": [list(o) for o in train_keep_off],
        "all_train_offsets": [list(o) for o in train_off],
        "heldout_offsets": [list(o) for o in held_off],
        "heldout_disposition": per_heldout,
        "per_demo": per_demo,
        "seat_quality_audit": seat_quality_audit,
        "seat_quality_note": (
            f"{_n_seat_mismatch} demo(s) poorly seated at pin (argmin_to_C1 != pinned_seg=pinned_body-{CABLE_BODY_START}); "
            "obs seg_pos for C1_SEAT/C1_PIN uses the structural pinned seg (matches runner _live_seg_pos); "
            "affine/labels/hull are EE-based and unaffected"
        ),
        "survivor_filter_note": (
            f"{len(train)} train + {len(held)} held-out survivors (brief §Survivor set); "
            "excluded (-8,+8) R_MISS + seat-filtered (0,-20),(+20,+20)"
        ),
        "n_train_demos": len(train_keep_idx),
        "n_val_demos": len(val_idx),
        "obs_train_shape": list(obs_train.shape),
        "obs_val_shape": list(obs_val.shape),
        "roundtrip_max_mm": round(roundtrip_max_mm, 9),
        "union_max_abs_a": round(union_max_abs_a, 6),
        "env_gates": train[0]["meta"].get("env_gates"),
    }

    os.makedirs(out_dir, exist_ok=True)
    npz_train = os.path.join(out_dir, "bc_dataset_abs.npz")
    tmp = npz_train + ".tmp.npz"
    np.savez(tmp, obs=obs_train.astype(np.float32), actions=labels_train.astype(np.float32), meta=json.dumps(ds_meta))
    os.replace(tmp, npz_train)
    npz_val = os.path.join(out_dir, "bc_dataset_abs_val.npz")
    tmp = npz_val + ".tmp.npz"
    np.savez(tmp, obs=obs_val.astype(np.float32), actions=labels_val.astype(np.float32), meta=json.dumps(ds_meta))
    os.replace(tmp, npz_val)
    with open(os.path.join(out_dir, "bc_dataset_abs_meta.json"), "w") as fh:
        json.dump(ds_meta, fh, indent=2)

    return {
        "affine": affine,
        "guard1": guard1,
        "obs_train": obs_train,
        "labels_train": labels_train,
        "obs_val": obs_val,
        "labels_val": labels_val,
        "ds_meta": ds_meta,
        "val_off": val_off,
        "train_keep_off": train_keep_off,
        "held_disp": held_disp,
        "roundtrip_max_mm": roundtrip_max_mm,
        "union_max_abs_a": union_max_abs_a,
        "box_span_audit": box_span_audit,
        "n_phases": n_phases,
    }


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


def self_check(obs, actions, ds_meta, schedule, d, cf, n_phases=13, PHASES=PHASES13):
    """§2.6 self-checks on the REAL npz + a 5-row human dump. Raises on any failure. Schema-parametric
    (n_phases/PHASES default to 13-phase v1); the demo-specific asserts (pin 2544, 37 grips) target the
    canonical demo."""
    fails = []

    def ck(cond, msg):
        print(("  OK  " if cond else "  FAIL") + " " + msg)
        if not cond:
            fails.append(msg)

    ck(obs.shape == (770, 12 + n_phases), f"obs shape {obs.shape} == (770,{12 + n_phases})")
    ck(actions.shape == (770, 6), f"actions shape {actions.shape} == (770,6)")
    repr_ = ds_meta.get("action_repr", "delta")
    a_bound = 0.95 if repr_ == "abs" else 1.0
    amx = float(np.abs(actions).max())
    ck(amx <= a_bound, f"|a|<={a_bound} (max {amx:.4f}, repr={repr_})")
    ck(bool(np.isfinite(obs).all() and np.isfinite(actions).all()), "obs+actions all finite")
    ck(np.allclose(obs[:, 12 : 12 + n_phases].sum(1), 1.0), "phase one-hot sums to 1 every row")
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
    ck(
        len(ds_meta["seg_rule_by_phase"]) == n_phases,
        f"seg table covers {n_phases} phases ({len(ds_meta['seg_rule_by_phase'])})",
    )
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
        p = int(np.argmax(obs[t, 12 : 12 + n_phases]))
        er3, ar3, sp, nc = obs[t, 0:3], actions[t, 0:3], obs[t, 6:9], obs[t, 9:12]
        print(
            f"  {t:3d} {PHASES[p]:15s} [{er3[0]:.3f},{er3[1]:.3f},{er3[2]:.3f}]"
            f"  [{ar3[0]:+.3f},{ar3[1]:+.3f},{ar3[2]:+.3f}]  [{sp[0]:.3f},{sp[1]:.3f},{sp[2]:.3f}]"
            f"  [{nc[0]:.3f},{nc[1]:.3f},{nc[2]:.3f}]"
        )
    if fails:
        raise SystemExit(f"\n§2.6 SELF-CHECK: {len(fails)} FAIL -> {fails}")
    print("\n§2.6 SELF-CHECK: ALL PASS")


def _read_spec_list(path):
    """Read a B2 list file: lines of ``npz_path,meta_path`` (blank / #-comment lines skipped)."""
    specs = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cols = [c.strip() for c in line.split(",")]
            if len(cols) != 2:
                raise SystemExit(f"B2 STOP: bad list line {line!r} in {path} (expected npz_path,meta_path)")
            specs.append((cols[0], cols[1]))
    return specs


# ============================================================================
# DQ7 stage (iv) restoring-augmented BC (denoising) sampler — ADDITIVE, default-off.
# Reads a committed B2 abs dataset and emits synthetic off-manifold (obs', a') rows
# per dq7_iv_mini_spec.md v1.1 (%12-approved 2026-07-03, DQ7_IV_MINISPEC_DEBATE_DECIDE.md
# U1-U11). NO edit to convert()/convert_b2() -> the committed B2 path is byte-untouched
# (regression = re-run normal convert, sha match). Gated on --b2-augment only.
# ============================================================================
AUG_GATED_PHASES = (0, 1, 2, 3, 11)  # DR-movable {0-3} + cable-anchored C2_REGRASP {11} (og:33-34)
AUG_AXIS_COS = 0.906  # 25deg: reject a D_train direction within 25deg of any probe axis (anti-teach-to-the-test)
AUG_BOX_MAX = 0.95  # union-box guard: reject a re-encoded label with any |a'| > this (frozen-hull, no re-fit)
AUG_MAG_BINS_MM = (2.0, 5.0, 8.0, 12.0, 21.0)  # accept/reject reporting bins (U3/U7)
# per-leg definition: perturb obs dims, optional co-move dims (seg-leg), label rule, tangent-proj (preserved legs).
AUG_LEGS = (
    # name, phases, perturb_dims, comove_dims, label, tangent_proj, mag_key
    ("ee_hover_descend", (0, 1), (0, 1, 2, 3, 4, 5), (), "preserve", True, "ee_wide"),
    ("ee_close_lift", (2, 3), (3, 4, 5), (), "preserve", True, "ee_narrow"),  # non-holder L dims
    ("ee_regrasp_R", (11,), (0, 1, 2), (), "preserve", True, "ee_wide"),  # acting-R dims, pre-contact
    ("seg_regrasp", (11,), (6, 7, 8), (3, 4, 5), "faithful_c2", False, "seg"),  # seg + holder-L co-move (og:252)
)
# retry ladder (dq7_iv_mini_spec.md v1.1 §2): step -> (K, {mag_key: (lo_mm, hi_mm)})
AUG_LADDER = {
    1: (2, {"ee_wide": (2.0, 20.0), "ee_narrow": (2.0, 8.0), "seg": (2.0, 10.0)}),
    2: (1, {"ee_wide": (2.0, 10.0), "ee_narrow": (2.0, 6.0), "seg": (2.0, 6.0)}),
    3: (1, {"ee_wide": (2.0, 5.0), "ee_narrow": (2.0, 5.0), "seg": (2.0, 5.0)}),
}


def _aug_sample_dir(rng, n_dims, tangent, tangent_proj):
    """Sample a unit D_train direction in an n_dims subspace with tangent-orthogonal projection (preserved legs)
    and 25deg-axis rejection (all legs). Returns the unit vector, or None if rejected after the try budget.

    tangent = the local path tangent restricted to the leg dims (og_b dwp construction), or None. When
    tangent_proj is True and |tangent|>0 the sampled direction is projected orthogonal to it (a tangent-aligned
    perturbation moves ALONG the demo path, where the label-preserved assumption is false) then renormalized.
    The 25deg guard (max_k |d.e_k| <= AUG_AXIS_COS) keeps training OFF the axis-aligned probe family the OG gate
    measures on (anti-teach-to-the-test); D_heldout = {+-e_k} is never trained.
    """
    tan_hat = None
    if tangent_proj and tangent is not None:
        tn = float(np.linalg.norm(tangent))
        if tn > 1e-9:
            tan_hat = np.asarray(tangent, np.float64) / tn
    for _ in range(64):  # try budget; exhaustion -> None (counted as axis_reject by the caller)
        d = rng.standard_normal(n_dims)
        nd = float(np.linalg.norm(d))
        if nd < 1e-12:
            continue
        d /= nd
        if tan_hat is not None:
            d = d - float(d @ tan_hat) * tan_hat
            nd = float(np.linalg.norm(d))
            if nd < 1e-6:  # sampled ~parallel to the tangent -> resample
                continue
            d /= nd
        if float(np.max(np.abs(d))) <= AUG_AXIS_COS:  # off every probe axis by >=25deg
            return d
    return None


def augment_b2(in_npz, out_dir, ladder_step=1, seed=0):
    """Emit the restoring-augmented dataset (dq7_iv_mini_spec.md v1.1). ADDITIVE; convert_b2 untouched.

    Reads ``in_npz`` (a committed abs dataset with obs/actions/meta.abs_affine -- the BC train set OR the
    replicate-null set for the augmented-null, both sharing the union affine), generates per-leg synthetic
    off-manifold rows (ee-legs = obs perturbed + label PRESERVED; seg-leg = seg+holder-L obs co-moved + faithful
    per-axis label: R_x,R_z co-move / R_y,L preserved -- U4, test:4404/:4405/:4377), applies the 25deg-axis +
    union-box guards, and writes ``{out_dir}/bc_dataset_abs_aug.npz`` (+ ``_aug_meta.json``) = clean rows ++
    accepted aug rows. Returns a dict with per-(leg x magnitude-bin) accept/reject counts for the report (U3/U5/U7).
    """
    step_K, mag_tab = AUG_LADDER[int(ladder_step)]
    src_npz = in_npz
    z = np.load(src_npz, allow_pickle=True)
    obs_clean = z["obs"].astype(np.float32)
    a_clean = z["actions"].astype(np.float32)
    base_meta = json.loads(str(z["meta"]))
    affine = np.asarray(base_meta["abs_affine"], np.float64)
    n_phases = affine.shape[0]
    PHASES = tuple(base_meta["phase_names"])
    ph = np.argmax(obs_clean[:, 12 : 12 + n_phases], axis=1).astype(int)
    wp = _abs_decode(a_clean.astype(np.float64), ph, affine)  # [T,6] true next-waypoint targets (round-trip exact)
    dwp = np.zeros_like(wp)  # local path tangent (og_b construction): wp[t+1]-wp[t]
    dwp[:-1] = wp[1:] - wp[:-1]
    dwp[-1] = dwp[-2]
    rng = np.random.RandomState(int(seed))

    def _bin(m_mm):
        return int(np.clip(np.searchsorted(AUG_MAG_BINS_MM, m_mm, side="right") - 1, 0, len(AUG_MAG_BINS_MM) - 2))

    aug_obs, aug_a = [], []
    counts = {}  # leg -> {"accept":[per-bin], "axis_reject":n, "box_reject":n, "n_src_rows":n, "K":step_K}
    for name, phases, pdims, cdims, label, tproj, mag_key in AUG_LEGS:
        lo_mm, hi_mm = mag_tab[mag_key]
        rows = np.where(np.isin(ph, phases))[0]
        c = counts[name] = {
            "accept_per_bin": [0] * (len(AUG_MAG_BINS_MM) - 1),
            "axis_reject": 0,
            "box_reject": 0,
            "n_src_rows": int(rows.size),
            "K": step_K,
            "mag_mm": [lo_mm, hi_mm],
            "bins_mm": list(AUG_MAG_BINS_MM),
        }
        for t in rows:
            for _ in range(step_K):
                m_m = float(np.exp(rng.uniform(np.log(lo_mm), np.log(hi_mm)))) / 1000.0  # log-U magnitude [m]
                tangent = dwp[t, list(pdims)] if tproj else None
                d = _aug_sample_dir(rng, len(pdims), tangent, tproj)
                if d is None:
                    c["axis_reject"] += 1
                    continue
                o2 = obs_clean[t].copy()
                o2[list(pdims)] += (d * m_m).astype(np.float32)  # perturb the leg's obs dims
                if cdims:  # seg-leg: holder-L co-moves with the seg (og pair-probe obs pattern :252)
                    o2[list(cdims)] += (d * m_m).astype(np.float32)
                if label == "preserve":
                    a2 = a_clean[t].copy()  # label unchanged -> |a2|<=|a_clean|<0.95, never box-rejected
                else:  # faithful_c2 (U4): R_x,R_z co-move with the seg d_x,d_z; R_y and L[3:6] PRESERVED
                    wp2 = wp[t].copy()
                    wp2[0] += d[0] * m_m  # R_x follows cable X (test:4404 _cRx)
                    wp2[2] += d[2] * m_m  # R_z follows cable Z (test:4404 _cRz); R_y(1)+L(3:6) held (:4405/:4377)
                    a2 = _abs_encode(wp2[None, :], ph[t : t + 1], affine)[0]
                    if float(np.max(np.abs(a2))) > AUG_BOX_MAX:  # union-box guard (frozen hull)
                        c["box_reject"] += 1
                        continue
                aug_obs.append(o2)
                aug_a.append(a2.astype(np.float32))
                c["accept_per_bin"][_bin(m_m * 1000.0)] += 1

    aug_obs = np.asarray(aug_obs, np.float32) if aug_obs else np.zeros((0, obs_clean.shape[1]), np.float32)
    aug_a = np.asarray(aug_a, np.float32) if aug_a else np.zeros((0, a_clean.shape[1]), np.float32)
    obs_out = np.concatenate([obs_clean, aug_obs], axis=0)
    a_out = np.concatenate([a_clean, aug_a], axis=0)
    n_accept = int(aug_obs.shape[0])

    aug_meta = dict(base_meta)  # copy base (schema, affine, phase_names, clip xy, seated_seg, ...) + truthful overrides
    aug_meta.update(
        {
            "schema": base_meta.get("schema", "") + "_aug",
            "dataset_kind": "dq7_iv_restoring_augmented",
            "n_rows_clean": int(obs_clean.shape[0]),
            "n_rows_aug": n_accept,
            "obs_aug_shape": list(obs_out.shape),
            "aug_cfg": {
                "V1": False,
                "ladder_step": int(ladder_step),
                "K": step_K,
                "per_leg_magnitude_ranges_mm": {name: list(mag_tab[mk]) for (name, _, _, _, _, _, mk) in AUG_LEGS},
                "rejection": {"axis_cos": AUG_AXIS_COS, "deg": 25, "tangent_projection": True, "box_max_abs_a": AUG_BOX_MAX},
                "sampler_seed": int(seed),
                "source_npz_sha256": _sha256_file(src_npz),
                "converter_git_note": "route_demo_to_bc.py augment_b2 (dq7_iv_mini_spec v1.1)",
                "per_leg_bin_counts": counts,
            },
        }
    )
    os.makedirs(out_dir, exist_ok=True)
    npz_out = os.path.join(out_dir, "bc_dataset_abs_aug.npz")
    tmp = npz_out + ".tmp.npz"
    np.savez(tmp, obs=obs_out, actions=a_out, meta=json.dumps(aug_meta))
    os.replace(tmp, npz_out)
    with open(os.path.join(out_dir, "bc_dataset_abs_aug_meta.json"), "w") as fh:
        json.dump(aug_meta, fh, indent=2)
    return {"n_clean": int(obs_clean.shape[0]), "n_aug": n_accept, "counts": counts, "out": npz_out, "meta": aug_meta}


def main():
    ap = argparse.ArgumentParser(description="route_demo_raw.npz -> bc_dataset.npz + schedule.json (B spec §2)")
    ap.add_argument("--npz", help="single-demo mode: route_demo_raw.npz")
    ap.add_argument("--meta", help="single-demo mode: route_demo_raw_meta.json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--action-repr", choices=["delta", "abs"], default="delta")  # E15 fork-(iv)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--b2-multi", action="store_true", help="B2 (§1.3/§1.4): multi-demo UNION-affine schema-v2 build")
    ap.add_argument("--train-list", help="B2: file of lines npz_path,meta_path (train demos)")
    ap.add_argument("--heldout-list", help="B2: file of lines npz_path,meta_path (held-out demos)")
    ap.add_argument("--seed", type=int, default=0, help="B2 val-split / augment sampler RNG seed (default 0)")
    ap.add_argument(
        "--b2-augment",
        action="store_true",
        help="DQ7 (iv): emit restoring-augmented dataset from --aug-in-dir (default-off; convert path untouched)",
    )
    ap.add_argument("--aug-in-dir", help="DQ7 (iv): dir holding bc_dataset_abs.npz to augment (BC train set)")
    ap.add_argument("--aug-in-npz", help="DQ7 (iv): explicit npz path to augment (e.g. the replicate-null set)")
    ap.add_argument("--aug-ladder-step", type=int, default=1, choices=[1, 2, 3], help="DQ7 (iv) retry ladder step")
    a = ap.parse_args()

    if a.b2_augment:  # DQ7 stage (iv) restoring-augmented dataset (additive; convert_b2 untouched)
        assert a.aug_in_dir or a.aug_in_npz, "--b2-augment requires --aug-in-dir or --aug-in-npz"
        in_npz = a.aug_in_npz or os.path.join(a.aug_in_dir, "bc_dataset_abs.npz")
        r = augment_b2(in_npz, a.out_dir, a.aug_ladder_step, a.seed)
        print(
            f"[route_demo_to_bc] DQ7-(iv) wrote {r['out']} = {r['n_clean']} clean + {r['n_aug']} aug rows "
            f"(ladder step {a.aug_ladder_step}, seed {a.seed}) -> {a.out_dir}"
        )
        for name, c in r["counts"].items():
            print(
                f"  leg {name:16s} src_rows={c['n_src_rows']:4d} K={c['K']} accept/bin={c['accept_per_bin']} "
                f"axis_reject={c['axis_reject']} box_reject={c['box_reject']}"
            )
        return

    if a.b2_multi:  # B2 multi-demo UNION-affine mode
        assert a.train_list and a.heldout_list, "--b2-multi requires --train-list and --heldout-list"
        train_specs = _read_spec_list(a.train_list)
        heldout_specs = _read_spec_list(a.heldout_list)
        res = convert_b2(train_specs, heldout_specs, a.out_dir, a.seed)
        print(
            f"[route_demo_to_bc] B2 wrote bc_dataset_abs.npz (obs {res['obs_train'].shape}) + "
            f"bc_dataset_abs_val.npz (obs {res['obs_val'].shape}) + bc_dataset_abs_meta.json -> {a.out_dir}\n"
            f"[route_demo_to_bc] B2 val_offsets={res['val_off']} roundtrip_max_mm={res['roundtrip_max_mm']:.3e} "
            f"union_max|a|={res['union_max_abs_a']:.4f} guard1={len(res['guard1'])}"
        )
        return

    assert a.npz and a.meta, "single-demo mode requires --npz and --meta (or use --b2-multi)"
    obs, actions, ds_meta, schedule, d, cf = convert(a.npz, a.meta, a.out_dir, a.action_repr)
    out_name = "bc_dataset_abs.npz" if a.action_repr == "abs" else "bc_dataset.npz"
    print(
        f"[route_demo_to_bc] wrote {out_name} (obs {obs.shape}, actions {actions.shape}, "
        f"repr={a.action_repr}) -> {a.out_dir}"
    )
    if a.action_repr == "delta":
        emit_macro_schedule(d, schedule, a.out_dir)  # B0b (E14): delta-side macro; NOT re-emitted in abs mode
    if a.self_check:
        n_phases = len(ds_meta["phase_names"])
        PHASES = tuple(ds_meta["phase_names"])
        self_check(obs, actions, ds_meta, schedule, d, cf, n_phases, PHASES)


if __name__ == "__main__":
    main()
