# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""No-GPU STATIC unit test for the route-executor recorded_replay step_target (comp2 Stage-A gate-ii).

Verifies that ``RouteExecutor.step_target`` (recorded_replay) reproduces the canonical fork-(iv) BC/trainer
base target BYTE-CONSISTENTLY -- the leg-ii the comp1 verify checked in scratchpad and %12 asked to commit.

The reference is NOT re-implemented: it is the ACTUAL ``route_demo_to_bc._compute_demo`` pipeline output
``wp = concat([ee_pos_r[next_f], ee_pos_l[next_f]])`` (route_demo_to_bc.py:255-287, the banked
BC/trainer absolute-target base, fork-(iv) LEDGER ADOPTED). So a pass proves:
``step_target(t).target_6d  ==  run_route recording  ==  BC/trainer base`` = SINGLE-SOURCE (build plan sec 6).

Any cadence / off-by-one (next_f = cf[1:]) / R-vs-L stacking regression in step_target shows up as a
non-zero L-inf. dtype note: the recorded ee_pos is float32; ``wp`` casts it to float64 (lossless) while
step_target stays float32, so the byte-exact compare upcasts step_target to float64 (L-inf == 0 exactly).

Run: ``/home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/test_routeexec_step_target.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# --- sys.path: envs (route_executor) + scripts (route_demo_to_bc) + configs -----------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
_TIL_DIR = _SCRIPTS_DIR.parent  # thread_isaac_lab/
_ENVS_DIR = _TIL_DIR / "envs"
_CONFIGS_DIR = _TIL_DIR / "configs"
_REPO = _TIL_DIR.parent
for _d in (str(_ENVS_DIR), str(_SCRIPTS_DIR), str(_TIL_DIR), str(_CONFIGS_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import route_demo_to_bc as rdbc  # noqa: E402  (the canonical BC/trainer converter; reference, not reimpl)
import route_executor as rex  # noqa: E402

_EVAL = _REPO / "eval_runs" / "troot_optE_dapg_wholeroute_scope_20260701"
_CELL = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0"
NOMINAL_NPZ = _CELL / "route_demo_raw.npz"
NOMINAL_META = _CELL / "route_demo_raw_meta.json"


def test_step_target_byte_consistent():
    if not (NOMINAL_NPZ.is_file() and NOMINAL_META.is_file()):
        print(f"[GATE-II] SKIP (npz/meta absent: {NOMINAL_NPZ})")
        return None
    # canonical fork-(iv) BC/trainer base via the ACTUAL route_demo_to_bc pipeline (REUSE, not reimpl).
    dm = rdbc._compute_demo(str(NOMINAL_NPZ), str(NOMINAL_META), strict_e4=True)
    wp = dm["wp"]  # [770, 6] float64, R-then-L = ee_pos_r[next_f] | ee_pos_l[next_f]
    n_steps = wp.shape[0]

    z = np.load(NOMINAL_NPZ, allow_pickle=True)
    rec = {k: z[k] for k in ("ee_pos_r", "ee_pos_l", "grip_cmd", "phase_id", "cable_xyz", "held_seg_l")}
    ex = rex.RouteExecutor([0], [0], 900, recording=rec)  # step_target only (control=None => no servo assert)

    linf = 0.0
    for t in range(n_steps):
        tgt = ex.step_target(t)[0]  # float32 [6]
        linf = max(linf, float(np.abs(tgt.astype(np.float64) - wp[t]).max()))
    target_ok = linf == 0.0  # byte-exact single-source with route_demo_to_bc.wp

    # pad-to-horizon: stepping past the recording holds the last waypoint (grippers latched).
    pad_ok = bool(np.array_equal(ex.step_target(n_steps)[0], ex.step_target(n_steps - 1)[0]))
    # phase-clock sanity: G0 (grasp) at t=0 -> G5 (C2 seat/settle) at the last step (not the stub equal-split).
    p0 = ex.step_target(0)[1]
    plast = ex.step_target(n_steps - 1)[1]
    phase_ok = (p0 == 0) and (plast == rex.rc.N_ROUTE_PHASES - 1)

    print(
        f"[GATE-II] step_target vs canonical wp (route_demo_to_bc._compute_demo REUSE): "
        f"n_steps={n_steps} target_Linf={linf:.3e} -> {'BYTE-EXACT' if target_ok else 'MISMATCH'}"
    )
    print(
        f"[GATE-II] pad-to-horizon (t>={n_steps} holds last wp): {'OK' if pad_ok else 'FAIL'}; "
        f"phase-clock span p0={p0}->plast={plast}: {'OK' if phase_ok else 'FAIL'}"
    )
    return target_ok and pad_ok and phase_ok


# =========================================================================================================
# W1-B2 units (HOLD + oracle API; conformance W1_B2_CONFORMANCE_COORD_20260712.md R1/R2/R3/R5)
# =========================================================================================================
_N_SEG = 8


def _mk_recording(grip_frames=None, phase=None, held=None):
    """Synthetic contract-v2 recording (mirror of the writesite fixture, cable keys included)."""
    n_frames = rex._REC_LAST_CTRL_FRAME + 1
    grip = np.zeros((n_frames, 2), dtype=np.float32)
    for f, (gl, gr) in (grip_frames or {}).items():
        grip[f] = (gl, gr)
    return {
        "ee_pos_r": np.zeros((n_frames, 3), dtype=np.float32),
        "ee_pos_l": np.zeros((n_frames, 3), dtype=np.float32),
        "grip_cmd": grip,
        "phase_id": phase if phase is not None else np.zeros(n_frames, dtype=np.int64),
        "cable_xyz": np.zeros((n_frames, _N_SEG, 3), dtype=np.float32),
        "held_seg_l": held if held is not None else np.zeros(n_frames, dtype=np.int64),
    }


def _mk_executor(rec, n_world=1):
    starts = [w * 100 for w in range(n_world)]
    return rex.RouteExecutor(starts, starts, 900, recording=rec)


def _view(d_mm, seg=0, axis=0):
    """One world's live cable view [segs, 3] with a d_mm displacement on `seg` (rec cable is zeros)."""
    v = np.zeros((_N_SEG, 3), dtype=np.float64)
    v[seg, axis] = d_mm / 1000.0
    return v


def test_contract_v2_validation():
    """R1a/b: required-key promotion + shape/range validation + dtype normalization."""
    base = _mk_recording()
    for k in ("cable_xyz", "held_seg_l"):
        bad = {kk: v for kk, v in base.items() if kk != k}
        try:
            rex._prepare_recording(bad)
            raise AssertionError(f"missing {k} did not raise")
        except ValueError as e:
            assert k in str(e)
    bad = dict(base)
    bad["cable_xyz"] = np.zeros((rex._REC_LAST_CTRL_FRAME + 1, 3), dtype=np.float32)  # 2D
    try:
        rex._prepare_recording(bad)
        raise AssertionError("2D cable_xyz did not raise")
    except ValueError:
        pass
    bad = dict(base)
    h = np.zeros(rex._REC_LAST_CTRL_FRAME + 1, dtype=np.int64)
    h[5] = _N_SEG  # out of [0, n_seg)
    bad["held_seg_l"] = h
    try:
        rex._prepare_recording(bad)
        raise AssertionError("out-of-range held_seg_l did not raise")
    except ValueError:
        pass
    bad = dict(base)
    bad["cable_xyz"] = base["cable_xyz"][:-1]  # frame-count mismatch
    try:
        rex._prepare_recording(bad)
        raise AssertionError("frame-count mismatch did not raise")
    except ValueError:
        pass
    ok = dict(base)
    ok["held_seg_l"] = base["held_seg_l"].astype(np.int16)  # golden dtype -> normalized
    prepared = rex._prepare_recording(ok)
    assert prepared["held_seg_l"].dtype == np.int64
    print("  [B2 contract-v2] PASS: required keys + shape/range/dtype validation")
    return True


def test_div_grip_pure():
    """R2a-d/h + R3h boundary pair (B2-F1: n runtime-derived, no hardcoded fencepost)."""
    held = np.zeros(rex._REC_LAST_CTRL_FRAME + 1, dtype=np.int64)
    # seg-follow: t=5's comparison frame is step_f[5]+9 = 59; t=7's is 79 (cadence 10).
    held[59] = 3
    held[79] = 6
    ex = _mk_executor(_mk_recording(held=held))
    d = ex.div_grip_mm(5, _view(4.0, seg=3), 0)
    assert abs(d - 4.0) < 1e-9, f"hand-computed div mismatch: {d} != 4.0"
    d = ex.div_grip_mm(7, _view(3.0, seg=6, axis=1), 0)
    assert abs(d - 3.0) < 1e-9, f"seg-follow div mismatch: {d} != 3.0"
    # purity: repeated calls mutate no sync state (R2h -- B3 restore check calls this outside the loop).
    before = ex._hold_count.copy()
    for _ in range(3):
        ex.div_grip_mm(5, _view(40.0, seg=3), 0)
    assert not ex._sync_hold.any() and (ex._hold_count == before).all() and (ex._hold_fire_count == 0).all()
    # recenter hook (B2 zeros; B4 wires): a matching recenter zeroes the div (R2d forward-compat).
    ex._recenter[0] = np.array([0.004, 0.0, 0.0])
    d = ex.div_grip_mm(5, _view(4.0, seg=3), 0)
    assert abs(d) < 1e-9, f"recenter subtraction failed: {d}"
    ex._recenter[0] = 0.0
    # boundary pair (%9 B2-F1): n = len(step_f) RUNTIME-derived; t=n-1 computes (with frame clamp), t=n skips.
    n = len(ex._recording["step_f"])
    assert isinstance(ex.div_grip_mm(n - 1, _view(1.0), 0), float), "t=n-1 must compute (clamped frame)"
    assert ex.div_grip_mm(n, _view(1.0), 0) is None, "t=n must skip (tail)"
    assert ex.div_grip_mm(899, _view(1.0), 0) is None, "deep tail must skip"
    print(f"  [B2 div_grip] PASS: formula/seg-follow/purity/recenter/boundary pair (n={n})")
    return True


def test_hold_state_machine():
    """R3b/c/e/f/g/h: fire/resume/hysteresis/equality/non-finite/MAX_HOLD/arming/tail (synthetic series)."""
    ex = _mk_executor(_mk_recording())
    armed = [True]

    def push(d_mm):
        if d_mm != d_mm:  # NaN request: poison the view
            v = _view(0.0)
            v[0, 0] = np.nan
        else:
            v = _view(d_mm)
        return bool(ex.update_sync([10], [v], armed)[0])

    assert push(10.0) is False, "10mm must MARCH"
    assert push(15.0) is False, "div=15.0 equality must NOT fire (strict >, %9 LOW)"
    assert push(15.1) is True and ex._hold_fire_count[0] == 1, "15.1mm must fire"
    assert push(12.0) is False and ex._resume_count[0] == 1, "<=12mm must resume immediately"
    assert push(16.0) is True and ex._chatter_count[0] == 1, "re-fire on resume's heels must count chatter"
    assert push(13.0) is True and push(13.0) is True, "in-band K<3 must stay held"
    assert push(13.0) is False and ex._resume_count[0] == 2, "K=3 consecutive in-band must resume"
    assert push(16.0) is True, "re-fire"
    assert push(13.0) is True and push(16.0) is True and push(13.0) is True, "13,16,13 must NOT resume (K reset)"
    hc0 = int(ex._hold_count[0])
    for _ in range(int(rex.rc.MAX_HOLD_STEPS) + 2 - hc0):
        push(16.0)
    assert ex._max_hold_event_count[0] == 1, "MAX_HOLD crossing must emit exactly one informative event"
    assert push(12.0) is False, "resume after MAX_HOLD event (no terminate)"
    assert push(float("nan")) is True and ex._nonfinite_div_count[0] == 1, "non-finite must fail-HOLD (loud)"
    # arming gate (R3g): unarmed world never fires, telemetry still lands.
    ex2 = _mk_executor(_mk_recording())
    assert bool(ex2.update_sync([10], [_view(40.0)], [False])[0]) is False and ex2._hold_fire_count[0] == 0
    assert np.isfinite(ex2._div_last[0]), "pre-grasp div must still be telemetered"
    # tail (R3h): past the recording end HOLD is disabled even when armed.
    n = len(ex2._recording["step_f"])
    assert bool(ex2.update_sync([n], [_view(40.0)], [True])[0]) is False, "tail must never hold"
    print("  [B2 hold-machine] PASS: fire/resume/K/equality/chatter/MAX_HOLD/non-finite/arming/tail")
    return True


def test_clear_neighbor_isolation():
    """R3k: clear_sync_state(world_ids) is world-sliced -- a neighbor's clear leaves held worlds intact."""
    ex = _mk_executor(_mk_recording(), n_world=2)
    mask = ex.update_sync([10, 10], [_view(20.0), _view(0.0)], [True, True])
    assert mask.tolist() == [True, False], f"setup: expected [True, False], got {mask.tolist()}"
    snap = (bool(ex._sync_hold[0]), int(ex._hold_count[0]), int(ex._hold_fire_count[0]))
    ex.clear_sync_state([1])
    after = (bool(ex._sync_hold[0]), int(ex._hold_count[0]), int(ex._hold_fire_count[0]))
    assert snap == after, f"neighbor clear mutated world 0: {snap} -> {after}"
    assert not ex._sync_hold[1] and ex._hold_count[1] == 0
    ex.clear_sync_state([0])
    assert not ex._sync_hold[0] and ex._hold_count[0] == 0 and ex._hold_fire_count[0] == 0
    print("  [B2 clear-isolation] PASS: world-sliced clear; neighbor state byte-intact")
    return True


def test_query_api():
    """R5a/b/c/e + R13c: 6-tuple shape, MARCH==step_target, HOLD chunk-end fields, mask derivation pin,
    release boundary pin (golden-based; SKIP if the reference npz is absent)."""
    if not NOMINAL_NPZ.is_file():
        print("  [B2 query] SKIP (reference npz absent)")
        return None
    z = np.load(NOMINAL_NPZ, allow_pickle=True)
    rec = {k: z[k] for k in ("ee_pos_r", "ee_pos_l", "grip_cmd", "phase_id", "cable_xyz", "held_seg_l")}
    ex = rex.RouteExecutor([0], [0], 900, recording=rec)
    prepared = ex._recording
    # MARCH equivalence (CC2-4): query packet fields == step_target on a spread of steps.
    for t in (0, 100, 343, 500, 769):
        st = ex.step_target(t)
        q = ex.query(t, 0, {"route_t": t})
        assert np.array_equal(q[0], st[0]) and q[1] == st[1], f"MARCH target/phase diverged at t={t}"
        assert np.array_equal(q[2], st[2]) and q[3] == st[3], f"MARCH grip/dual diverged at t={t}"
        assert isinstance(q[4], np.float32) and set(q[5]) == {"mode", "hold_count", "div_grip", "route_t"}
        assert q[5]["mode"] == "MARCH" and q[5]["route_t"] == t
    # HOLD variant (R4e, %12 A2): grip-derived fields evaluate at the chunk END. Find a chunk whose start
    # vs end grip classification differs (a staircase transition chunk) and assert the flip.
    thr = rex._GRIP_CLOSE_THR
    g = prepared["grip_cmd"]
    step_f = prepared["step_f"]
    t_flip = None
    for t in range(len(step_f)):
        f0, f9 = int(step_f[t]), min(int(step_f[t]) + rex._REC_CADENCE - 1, g.shape[0] - 1)
        if bool(((g[f0] >= thr) != (g[f9] >= thr)).any()):
            t_flip = t
            break
    assert t_flip is not None, "golden has no staircase-transition chunk -- premise broken"
    ex._sync_hold[0] = True
    qh = ex.query(t_flip, 0, {"route_t": t_flip})
    f9 = min(int(step_f[t_flip]) + rex._REC_CADENCE - 1, g.shape[0] - 1)
    exp = np.array([1.0 if g[f9, 1] >= thr else 0.0, 1.0 if g[f9, 0] >= thr else 0.0], dtype=np.float32)
    assert np.array_equal(qh[2], exp), f"HOLD grip_2 not chunk-end at t={t_flip}: {qh[2]} vs {exp}"
    assert qh[5]["mode"] == "HOLD"
    ex._sync_hold[0] = False
    # validity mask derivation pin (R5c, %12 23:29 ruling): events = recorded phases {0, 11}; detection
    # source = FIRST frame of each phase; G attribution via _RECORDED_PHASE_TO_G -> {G1(idx0), G4(idx3)}.
    mef = prepared["mask_event_frames"]
    assert set(mef) == {0, 11}, f"mask events {set(mef)} != {{0, 11}}"
    ph = prepared["phase_id"]
    for p in (0, 11):
        assert mef[p] == int(np.nonzero(ph == p)[0][0]), f"event frame for phase {p} not first-occurrence"
    mask = prepared["validity_mask_g"]
    assert mask.tolist() == [True, False, False, True, False, False], f"mask G attribution: {mask.tolist()}"
    # release boundary pin (R13c): both-release at ~frame 7617 -> first chunk starting at/after it = t 762.
    assert prepared["release_step"] == 762, f"release_step {prepared['release_step']} != 762 (canonical)"
    print(
        f"  [B2 query] PASS: MARCH==step_target / HOLD chunk-end @t{t_flip} / mask {{0:G1, 11:G4}} "
        f"(frames {mef}) / release_step=762"
    )
    return True


def main():
    print("=" * 78)
    print("route-executor units: gate-ii byte-consistency + W1-B2 HOLD/oracle (contract v2)")
    print("=" * 78)
    r = test_step_target_byte_consistent()
    results = [
        test_contract_v2_validation(),
        test_div_grip_pure(),
        test_hold_state_machine(),
        test_clear_neighbor_isolation(),
        test_query_api(),
    ]
    print("-" * 78)
    if r is None:
        print("gate-ii: SKIP (reference recording absent)")
    else:
        print(f"gate-ii step_target == run_route recording (== BC/trainer base): {'PASS' if r else 'FAIL'}")
    b2_ok = all(x is not False for x in results)
    print(f"W1-B2 units: {'PASS' if b2_ok else 'FAIL'}")
    if r is None:
        return 0 if b2_ok else 1
    return 0 if (r and b2_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
