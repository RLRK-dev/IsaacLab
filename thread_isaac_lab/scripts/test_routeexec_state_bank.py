# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""No-GPU STATIC unit test for the route-executor state-bank (comp2 Stage-A gate-i = DoD ⑦(a)).

Verifies the reset-side of the whole-route env-integration WITHOUT any physics rollout:

    recording  --build_state_bank_from_recording-->  {k: banked}
    banked     --RouteExecutor.reset_to_phase(k) / apply_banked_restore-->  physics joint_q/joint_qd/target
    readback   ==  the recorded phase-k boundary snapshot   (L-inf <= 1mm / 1mm/s, DoD ⑦(a))

This is the roundtrip + index-alignment guard for the F1/G7-recurring gripper-coordinate class: it
catches a wrong per-world offset, a wrong ``_ARM_OVERWRITE_LOCAL`` / ``_GRIPPER_COORDS_LOCAL`` split, a
wrong world-major tiling, or a wrong driver-DOF ``grip_target`` order -- none of which a GPU run is needed
to expose. A mujoco-style warp array is mocked (``.numpy()`` -> host copy, ``.assign()`` -> store), so the
whole test runs on CPU in ``env_isaaclab7`` in ~seconds and never builds a scene.

qvel note (comp2 design, mirrors :func:`build_state_bank_from_recording`): the recording carries NO
``joint_qd`` -- banked velocities are 0 (EXACT for the arm: the kinematic re-pose zeroes arm ``joint_qd``
every step; the servo re-accelerates the gripper live at Stage-B ⑦(b)). So the qvel leg asserts the
restored velocities are 0 (a corruption/index check), while the qpos leg is a real fidelity check vs the
recorded ``arm_q``.

Run: ``/home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/test_routeexec_state_bank.py``
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

# --- sys.path (mirror test_routeexec_byte_repro.py): envs (route_executor/route_env_config) + configs ---
_SCRIPTS_DIR = Path(__file__).resolve().parent
_TIL_DIR = _SCRIPTS_DIR.parent  # thread_isaac_lab/
_ENVS_DIR = _TIL_DIR / "envs"
_CONFIGS_DIR = _TIL_DIR / "configs"
_REPO = _TIL_DIR.parent  # IsaacLab/
for _d in (str(_ENVS_DIR), str(_TIL_DIR), str(_CONFIGS_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import route_executor as rex  # noqa: E402  (path set above)

_EVAL = _REPO / "eval_runs" / "troot_optE_dapg_wholeroute_scope_20260701"
NOMINAL_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"

_N_ARM = rex._N_ARM_JOINTS  # 28
_ARM_LOCAL = list(rex._ARM_OVERWRITE_LOCAL)  # {0-5,14-19}
_GRIP_LOCAL = sorted(rex._GRIPPER_COORDS_LOCAL)  # {6-13,20-27}
_DRIVERS_LOCAL = [6, 10, 20, 24]  # L,L,R,R driver DOFs (order matches maps["all_driver_dofs"])

_TOL_Q = 1e-6  # far tighter than the DoD 1mm bound: a float32 copy roundtrip is bit-exact (~0)
_TOL_QD = 1e-6


class _MockArr:
    """Minimal stand-in for a warp array: ``.numpy()`` returns a host copy, ``.assign()`` stores one."""

    def __init__(self, a):
        self._a = np.asarray(a).copy()

    def numpy(self):
        return self._a.copy()

    def assign(self, x):
        self._a = np.asarray(x).copy()


class _MockState:
    def __init__(self, total_q, total_qd):
        self.joint_q = _MockArr(np.zeros(total_q, dtype=np.float32))
        self.joint_qd = _MockArr(np.zeros(total_qd, dtype=np.float32))


class _MockControl:
    def __init__(self, total_qd):
        # seeded all-OPEN (0.0) so RouteExecutor.__init__ servo_seed_assert passes.
        self.joint_target_pos = _MockArr(np.zeros(total_qd, dtype=np.float32))


def _boundary_frame(phase_id, k):
    """First frame whose recorded phase_id maps to G-phase k (mirror of the builder's boundary rule)."""
    g = np.array([rex._RECORDED_PHASE_TO_G[int(p)] for p in phase_id], dtype=np.int64)
    hits = np.nonzero(g == int(k))[0]
    return int(hits[0]) if hits.size else None


def _roundtrip_check(recording, n_world, arm_q_start, arm_qd_start, label):
    """Build the bank, fork each phase-k, assert the restored physics == the recorded phase-k snapshot."""
    horizon = 900
    total_q = max(arm_q_start) + _N_ARM + 2
    total_qd = max(arm_qd_start) + _N_ARM + 2
    state = _MockState(total_q, total_qd)
    control = _MockControl(total_qd)
    bank = rex.build_state_bank_from_recording(recording, n_world, arm_off=0)
    ex = rex.RouteExecutor(arm_q_start, arm_qd_start, horizon, state_0=state, control=control, state_bank=bank)

    arm_q = np.asarray(recording["arm_q"], dtype=np.float32)
    grip = np.asarray(recording["grip_cmd"], dtype=np.float32)
    phase_id = np.asarray(recording["phase_id"])

    ok = True
    print(f"  [{label}] n_world={n_world} banked phases={sorted(bank)}")
    if sorted(bank) != [1, 2, 3, 4, 5]:
        print(f"  [{label}] FAIL: expected banks {{1,2,3,4,5}}, got {sorted(bank)}")
        return False
    for k in sorted(bank):
        bf = _boundary_frame(phase_id, k)
        exp_span = arm_q[bf, 0:_N_ARM]  # expected two-arm 28-wide snapshot at the boundary
        exp_gl, exp_gr = float(grip[bf, 0]), float(grip[bf, 1])

        # pre-fill with a sentinel so the assertion proves the restore actually WROTE (not leftover).
        state.joint_q.assign(np.full(total_q, -99.0, dtype=np.float32))
        state.joint_qd.assign(np.full(total_qd, -99.0, dtype=np.float32))
        control.joint_target_pos.assign(np.full(total_qd, -99.0, dtype=np.float32))
        ex.reset_to_phase(k)
        jq = state.joint_q.numpy()
        jqd = state.joint_qd.numpy()
        jtp = control.joint_target_pos.numpy()

        linf_q = linf_qd = 0.0
        grip_ok = True
        for w in range(n_world):
            got_q = jq[arm_q_start[w] : arm_q_start[w] + _N_ARM]  # all 28 arm+gripper coords restored
            got_qd = jqd[arm_qd_start[w] : arm_qd_start[w] + _N_ARM]  # all 28 -> banked 0
            linf_q = max(linf_q, float(np.abs(got_q - exp_span).max()))
            linf_qd = max(linf_qd, float(np.abs(got_qd - 0.0).max()))
            # grip_target: L drivers (6,10) -> grip_L; R drivers (20,24) -> grip_R.
            for d, exp in ((6, exp_gl), (10, exp_gl), (20, exp_gr), (24, exp_gr)):
                grip_ok = grip_ok and abs(float(jtp[arm_qd_start[w] + d]) - exp) < _TOL_Q
        leg = (linf_q <= _TOL_Q) and (linf_qd <= _TOL_QD) and grip_ok
        ok = ok and leg
        gstat = "OK" if grip_ok else "MISMATCH"
        vstat = "PASS" if leg else "FAIL"
        print(
            f"  [{label}] k={k} bf={bf} qpos_Linf={linf_q:.3e} qvel_Linf={linf_qd:.3e} "
            f"grip_target={gstat} (gL={exp_gl:.4f} gR={exp_gr:.4f}) -> {vstat}"
        )
    return ok


def _synthetic_recording():
    """Deterministic tiny recording (CI-safe, no npz dependency); each coord is uniquely identifiable."""
    seg = [(-1, 10), (3, 10), (4, 10), (7, 10), (12, 10), (13, 10)]  # hits G0..G5
    phase = np.concatenate([np.full(n, p, dtype=np.int16) for p, n in seg])
    nfr = phase.shape[0]
    # arm_q[f, j] = f*100 + j  -> every (frame, coord) pair is unique (any index bug shows up as a mismatch).
    arm_q = (np.arange(nfr)[:, None] * 100.0 + np.arange(30)[None, :]).astype(np.float32)  # width 30 (> 28)
    grip = np.stack([np.arange(nfr) * 0.001, np.arange(nfr) * 0.002], axis=1).astype(np.float32)  # [L, R]
    return {"arm_q": arm_q, "grip_cmd": grip, "phase_id": phase}


def test_synthetic():
    print("[SYNTHETIC] deterministic recording, 2-world cable-offset (q35/qd34) ...")
    rec = _synthetic_recording()
    return _roundtrip_check(rec, n_world=2, arm_q_start=[0, 35], arm_qd_start=[0, 34], label="SYNTH")


def test_nominal():
    if not NOMINAL_NPZ.is_file():
        print(f"[NOMINAL] SKIP (npz absent: {NOMINAL_NPZ})")
        return None
    print(f"[NOMINAL] real cell_x0_y0 recording ({NOMINAL_NPZ}) ...")
    z = np.load(NOMINAL_NPZ, allow_pickle=True)
    rec = {"arm_q": z["arm_q"], "grip_cmd": z["grip_cmd"], "phase_id": z["phase_id"]}
    # 4-world default env layout mock (contiguous, cable-offset q!=qd), arm_off=0 (verified: arm at joint_q[0:28]).
    aqs = [0, 40, 80, 120]
    aqds = [0, 38, 76, 114]  # qd start != q start per world (cable FREE root => 2-extra/world), mock offsets
    return _roundtrip_check(rec, n_world=4, arm_q_start=aqs, arm_qd_start=aqds, label="NOMINAL")


def test_world_slice():
    """W1-B1 interface v2: reset_to_phase(k, world_ids) restores ONLY those worlds (conformance v2.1 R12).

    Discriminating construction (CC3-CH2 + %9 F-1): the bank is per-world-DISTINCT (hand-built, NOT the
    tiled build_state_bank output) and W = {1, 3} is a non-prefix, world-0-excluding subset -- a buggy
    slice that reads the FIRST |W| banked blocks (or world-0's block via an un-re-based enumerate) writes
    values that DIFFER from the expected per-world blocks, so the asserts below can see it. Also pins the
    k=0-never-banked invariant and the world_ids=None (v1-compatible all-worlds) path.
    """
    print("[WORLD-SLICE] per-world-distinct bank, W={1,3} (non-prefix, world-0 excluded) ...")
    n_world = 4
    aqs = [0, 35, 70, 105]
    aqds = [0, 34, 68, 102]
    total_q = aqs[-1] + _N_ARM + 2
    total_qd = aqds[-1] + _N_ARM + 2
    state = _MockState(total_q, total_qd)
    control = _MockControl(total_qd)

    # hand-built per-world-DISTINCT bank for k=3: world w's block = 1000*w + slot (unique everywhere).
    n_arm_blk, n_grip_blk, n_drv_blk = len(_ARM_LOCAL), len(_GRIP_LOCAL), 4

    def _dis(nblk):
        return np.concatenate([1000.0 * w + np.arange(nblk, dtype=np.float32) for w in range(n_world)])

    banked = {
        "arm_q": _dis(n_arm_blk),
        "arm_qd": _dis(n_arm_blk),
        "gripper_q": _dis(n_grip_blk),
        "gripper_qd": _dis(n_grip_blk),
        "grip_target": _dis(n_drv_blk),
    }
    bank = {3: banked}
    assert 0 not in bank, "k=0 must NEVER be banked (env-authoritative reset; v2.1 R12/R13 invariant)"
    ex = rex.RouteExecutor(aqs, aqds, 900, state_0=state, control=control, state_bank=bank)

    state.joint_q.assign(np.full(total_q, -99.0, dtype=np.float32))
    state.joint_qd.assign(np.full(total_qd, -99.0, dtype=np.float32))
    control.joint_target_pos.assign(np.full(total_qd, -99.0, dtype=np.float32))
    ex.reset_to_phase(3, world_ids=[3, 1])  # unsorted on purpose: the impl must sort ascending
    jq = state.joint_q.numpy()
    jqd = state.joint_qd.numpy()
    jtp = control.joint_target_pos.numpy()

    maps = rex.build_perworld_index_maps(aqs, aqds)

    def _mblk(key, w, n):
        return np.asarray(maps[key])[w * n : (w + 1) * n]

    ok = True
    for w in range(n_world):
        arm_q_i = _mblk("arm_ow_q_idx", w, n_arm_blk)
        arm_qd_i = _mblk("arm_ow_qd_idx", w, n_arm_blk)
        grip_q_i = _mblk("gripper_restore_q_idx", w, n_grip_blk)
        grip_qd_i = _mblk("gripper_restore_qd_idx", w, n_grip_blk)
        drv = _mblk("all_driver_dofs", w, n_drv_blk)
        if w in (1, 3):
            leg = (
                np.array_equal(jq[arm_q_i], banked["arm_q"][w * n_arm_blk : (w + 1) * n_arm_blk])
                and np.array_equal(jqd[arm_qd_i], banked["arm_qd"][w * n_arm_blk : (w + 1) * n_arm_blk])
                and np.array_equal(jq[grip_q_i], banked["gripper_q"][w * n_grip_blk : (w + 1) * n_grip_blk])
                and np.array_equal(jqd[grip_qd_i], banked["gripper_qd"][w * n_grip_blk : (w + 1) * n_grip_blk])
                and np.array_equal(jtp[drv], banked["grip_target"][w * n_drv_blk : (w + 1) * n_drv_blk])
            )
            print(f"  [WORLD-SLICE] w={w} restored == OWN block (distinct values) -> {'PASS' if leg else 'FAIL'}")
        else:
            leg = (
                np.all(jq[arm_q_i] == -99.0)
                and np.all(jq[grip_q_i] == -99.0)
                and np.all(jqd[arm_qd_i] == -99.0)
                and np.all(jqd[grip_qd_i] == -99.0)  # %9 R-2: gripper_qd untouched too
                and np.all(jtp[drv] == -99.0)
            )
            print(f"  [WORLD-SLICE] w={w} sentinel untouched -> {'PASS' if leg else 'FAIL'}")
        ok = ok and leg

    # v1-compat: world_ids=None restores ALL worlds (the v1-identical path).
    ex.reset_to_phase(3)
    jq = state.joint_q.numpy()
    v1_ok = all(
        np.array_equal(jq[_mblk("arm_ow_q_idx", w, n_arm_blk)], banked["arm_q"][w * n_arm_blk : (w + 1) * n_arm_blk])
        for w in range(n_world)
    )
    print(f"  [WORLD-SLICE] world_ids=None -> ALL worlds restored -> {'PASS' if v1_ok else 'FAIL'}")
    return ok and v1_ok


# =========================================================================================================
# W1-B3a units: chunk-aligned boundaries + the cable-carrying bank v2 builder + its fail-loud guards
# (conformance W1_B3_CONFORMANCE_COORD_20260713.md R2). CPU-only: a SYNTHETIC capture is derived from the
# canonical recording itself (joint_q := the recording's own 74-wide physics joint_q; joint_qd := a central
# finite difference of it), so the builder's whole guard surface is exercised with zero GPU.
# =========================================================================================================
def _synthetic_capture(rec, live_eq=True):
    """A capture npz-shaped dict derived from the recording (see module note): frame-aligned BY CONSTRUCTION.

    ``eq_active`` mirrors the producer's real layout -- pre-allocated, initially-DISABLED per-body clip-pin
    CONNECT eqs plus the 6 always-on structural eqs -- and, when ``live_eq``, carries the clip pin exactly as
    the recording's own ``pin_active``/``pin_eqid`` witness reports it. ``live_eq=False`` reproduces the
    never-stepped mjw_data MIRROR (pin column frozen at 0), which the builder must REJECT: banking the mirror
    restores "pin OFF" at every k past the pin onset. That is the defect this fixture pair exists to catch.
    """
    q = np.asarray(rec["arm_q"], dtype=np.float32)
    f, nq = q.shape
    nv = nq - 1  # the cable free root is 7 coords / 6 dofs
    qd = np.zeros((f, nv), dtype=np.float32)
    dq = np.gradient(q.astype(np.float64), rex.DT, axis=0)
    qd[:, : rex._N_ARM_JOINTS] = dq[:, : rex._N_ARM_JOINTS]
    qd[:, rex._N_ARM_JOINTS + 6 :] = dq[:, rex._N_ARM_JOINTS + 7 :]  # hinge rates (skip the free-root quat)
    pin = np.asarray(rec["pin_active"]).astype(int).ravel()
    eqid_col = np.asarray(rec["pin_eqid"]).astype(int).ravel()
    active = eqid_col[pin > 0]
    eqid = int(np.unique(active)[0]) if active.size else 27
    eq = np.zeros((f, eqid + 7), dtype=np.int32)
    eq[:, -6:] = 1  # structural eqs (4 CONNECT + 2 follower-mirror), always on
    if live_eq:
        eq[pin > 0, eqid] = 1
    return {
        "joint_q": q,
        "joint_qd": qd,
        "qacc_warmstart": np.zeros((f, nv), dtype=np.float32),
        "eq_active": eq,
    }


def test_bank_v2_builder():
    """R2a-k: chunk-aligned boundaries, cable q/qd, arm_qd EXACT-zero, provenance + fail-loud guards."""
    if not NOMINAL_NPZ.is_file():
        print("  [B3a bank-v2] SKIP (canonical recording absent)")
        return None
    z = np.load(NOMINAL_NPZ, allow_pickle=True)
    rec = {k: z[k] for k in ("arm_q", "grip_cmd", "phase_id", "pin_active", "pin_eqid")}
    sha = hashlib.sha256(NOMINAL_NPZ.read_bytes()).hexdigest()
    assert sha == rex.RUN1_REFERENCE_V2_SHA256, "fixture is not the canonical golden"

    # (R2c) boundaries: ceil-aligned chunk starts; capture_frame = cadence*t_k - 1 (the state at chunk start)
    bounds = rex.bank_boundaries_from_recording(rec)
    exp = {1: (1124, 113, 1129), 2: (1724, 173, 1729), 3: (2584, 259, 2589), 4: (6181, 619, 6189), 5: (6801, 681, 6809)}
    got = {k: (v["f_k"], v["t_k"], v["capture_frame"]) for k, v in bounds.items()}
    assert got == exp, f"boundary derivation drift: {got} != {exp}"

    cap = _synthetic_capture(rec)
    n_world = 2
    bank = rex.build_state_bank_v2_from_capture(cap, rec, n_world, recording_sha256=sha)
    assert sorted(bank) == [1, 2, 3, 4, 5], f"banked phases {sorted(bank)}"
    n_arm_blk = len(rex._ARM_OVERWRITE_LOCAL)
    for k, b in bank.items():
        f = b["capture_frame"]
        assert b["bank_boundary_step"] == exp[k][1]
        # (R2b) arm_qd is EXACT-as-zero (the substrate zeroes it every frame) -- NOT a compromise
        assert np.count_nonzero(b["arm_qd"]) == 0, f"k={k}: arm_qd must be banked zero (substrate zeroes it)"
        # cable q/qd carried, world-invariant single-world blocks
        assert b["cable_q"].shape == (cap["joint_q"].shape[1] - rex._N_ARM_JOINTS,)
        assert b["cable_qd"].shape == (cap["joint_qd"].shape[1] - rex._N_ARM_JOINTS,)
        assert np.count_nonzero(b["cable_qd"]) > 0, f"k={k}: cable_qd must be non-zero (mid-route cable moves)"
        # (R2f) the banked arm block IS the recording's row at the capture frame (frame-alignment proof)
        arm_span = np.asarray(rec["arm_q"])[f, : rex._N_ARM_JOINTS]
        assert np.array_equal(b["arm_q"][:n_arm_blk], arm_span[list(rex._ARM_OVERWRITE_LOCAL)].astype(np.float32))
        # (R2k) the clip-pin equality state at the fork is banked (measured: OFF for k<=2, ON for k>=3)
        assert b["pin_active"] == (0 if k <= 2 else 1), f"k={k}: pin_active={b['pin_active']}"
    print(f"  [B3a bank-v2] PASS: boundaries {got} / cable q+qd carried / arm_qd exact-zero / pin banked")

    # --- fail-loud guards (each MUST raise) ---
    def _raises(fn, why):
        try:
            fn()
        except (ValueError, AssertionError):
            return True
        raise AssertionError(f"guard did NOT raise: {why}")

    _raises(
        lambda: rex.build_state_bank_v2_from_capture(cap, rec, n_world, recording_sha256="deadbeef"),
        "non-canonical recording sha (a degenerate bank would be built silently)",
    )
    _raises(
        lambda: rex.build_state_bank_v2_from_capture(cap, rec, n_world, recording_sha256=None),
        "missing provenance sha",
    )
    # missing phase: strip every G6 frame -> the builder must raise, not skip silently (v1 `continue`)
    ph = np.asarray(rec["phase_id"]).copy()
    ph[np.isin(ph, [13, 14])] = 12
    _raises(
        lambda: rex.bank_boundaries_from_recording({"phase_id": ph}),
        "G-phase with ZERO frames (non-canonical recording -> degenerate bank)",
    )
    # capture/recording frame skew: roll the capture by one frame -> the q-EXACT check must catch it
    skewed = dict(cap, joint_q=np.roll(cap["joint_q"], 1, axis=0))
    _raises(
        lambda: rex.build_state_bank_v2_from_capture(skewed, rec, n_world, recording_sha256=sha),
        "capture NOT frame-aligned with the recording (1-frame skew)",
    )
    # (R2k) DEAD-MIRROR eq_active: SolverMuJoCo builds a mjw_data mirror even on the CPU backend
    # (solver_mujoco.py:5791) and never steps it, so its pin column stays 0 for the whole run. A bank built
    # from it restores "pin OFF" at every k past the pin onset (k=3,4,5) -- a FORK-1-class silent mismatch.
    # The recording's own pin_active/pin_eqid witness is what rejects it. This guard is the negative control
    # for the hidden-state channel; without it the channel is merely PRESENT, not LIVE.
    dead = _synthetic_capture(rec, live_eq=False)
    _raises(
        lambda: rex.build_state_bank_v2_from_capture(dead, rec, n_world, recording_sha256=sha),
        "eq_active captured from the never-stepped mjw_data mirror (clip pin frozen OFF)",
    )
    print(
        "  [B3a bank-v2 guards] PASS: non-canonical sha / missing sha / zero-frame phase / frame skew / "
        "dead-mirror eq_active all raise"
    )
    return True


def test_bank_v2_null_control():
    """ERRATUM-C: the qd channel must have DISCRIMINATING power -- a null bank (cable_qd=0) must be rejected.

    The B3 v1 plan's bars passed a fully qd-zeroed bank (measured 3.4-44x margin), i.e. they could not tell
    bank v2 from bank v1. This unit encodes the discrimination requirement itself: build a null bank and show
    the FD consistency check (the only leg with an independent qd ground truth) rejects it.
    """
    if not NOMINAL_NPZ.is_file():
        print("  [B3a null-control] SKIP")
        return None
    z = np.load(NOMINAL_NPZ, allow_pickle=True)
    rec = {k: z[k] for k in ("arm_q", "grip_cmd", "phase_id", "pin_active", "pin_eqid")}
    sha = hashlib.sha256(NOMINAL_NPZ.read_bytes()).hexdigest()
    cap = _synthetic_capture(rec)
    good = rex.build_state_bank_v2_from_capture(cap, rec, 1, recording_sha256=sha)
    null_cap = dict(cap, joint_qd=np.zeros_like(cap["joint_qd"]))
    null = rex.build_state_bank_v2_from_capture(null_cap, rec, 1, recording_sha256=sha)
    n_arm = rex._N_ARM_JOINTS
    q = np.asarray(rec["arm_q"], dtype=np.float64)
    detected = []
    for k in sorted(good):
        f = good[k]["capture_frame"]
        fd = (q[f + 1] - q[f - 1]) / (2.0 * rex.DT)
        hinge_fd = fd[n_arm + 7 :]
        good_err = np.linalg.norm(good[k]["cable_qd"][6:] - hinge_fd) / max(np.linalg.norm(hinge_fd), 1e-12)
        null_err = np.linalg.norm(null[k]["cable_qd"][6:] - hinge_fd) / max(np.linalg.norm(hinge_fd), 1e-12)
        detected.append(good_err <= 0.20 < null_err)
        assert good_err <= 0.20, f"k={k}: real bank failed its own FD check ({good_err:.3f})"
        assert null_err > 0.20, f"k={k}: NULL bank passed the FD check ({null_err:.3f}) -> bar has no power"
    print(f"  [B3a null-control] PASS: real bank accepted AND null (cable_qd=0) bank rejected at all k={sorted(good)}")
    return all(detected)


def main():
    print("=" * 78)
    print("route-executor state-bank: ⑦(a) restore-fidelity (comp2) + W1-B3a bank v2 builder")
    print("=" * 78)
    r_syn = test_synthetic()
    r_nom = test_nominal()
    r_ws = test_world_slice()
    r_v2 = test_bank_v2_builder()
    r_nc = test_bank_v2_null_control()
    print("-" * 78)
    results = {"synthetic": r_syn, "nominal": r_nom, "world_slice": r_ws, "bank_v2": r_v2, "null_control": r_nc}
    hard = [v for v in results.values() if v is not None]
    verdict = all(hard)
    print(f"RESULTS: {results}")
    print(f"⑦(a) restore-fidelity + B3a bank v2: {'PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
