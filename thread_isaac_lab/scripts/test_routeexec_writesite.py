# c6 (2026-07-19, Rs kinematic complete-removal): the 5 WRITER tests (test_broadcast /
# test_perworld / test_guard / test_recorded_arm_ff / test_recorded_arm_ff_golden) are RETIRED --
# they assert kinematic joint-state mutation, which is removed by design (helpers raise).
# The 11 remaining tests are non-writer regression surfaces (pN per-test disposition,
# 17:16 JST). Historical full file: git 349d13551c.
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""No-GPU CPU WRITE-PATTERN unit for the comp3 write-site flag-gate (L1) + grip-drive/reset-reseed wiring (L4).

L1 (chunk 1, plan v2 §12/R5): the arm-only write-site flag-gate. L4 (chunk 2, plan v2 §6/§10, R1/R2): the
recorded grip_cmd staircase per-arm mapping + the reset servo re-seed to OPEN + the settled-fk gripper patch
+ the forbid-banked-fork guard. All CPU/no-GPU (a warp array is mocked).

Unlike the predicate-only dod9a_prime check, this test ACTUALLY EXERCISES the write-site: it runs the
arm-only write functions the flag-ON branch calls (``apply_arm_only_write_broadcast`` /
``apply_arm_only_write_perworld``) against a synthetic multi-world ``phys_jq``/``phys_jqd`` and compares
them, coord-by-coord, to a 28-wide reference (the flag-OFF branch behaviour). It proves:

  (a) flag-OFF path == the current 28-wide write (byte-equal on ALL 28 arm+gripper coords per world);
  (b) flag-ON path writes the arm coords byte-identically to flag-OFF, but leaves the gripper coords
      {6-13, 20-27} per world UNTOUCHED (so the POSITION servo drives them) -- i.e. the ONLY difference
      between flag-OFF and flag-ON is exactly the gripper-coord set;
  (c) the __init__ flag-matrix guard fires loud (grasp_actuation=True + stub route -> ValueError; a
      non-bool grasp_actuation -> AssertionError), BEFORE any scene build.

A mujoco-style warp array is mocked; the whole test runs on CPU in seconds and never builds a scene.

Run (CPU/no-GPU; the write-pattern tests are pure numpy, the guard test imports the env but raises before
any scene build). Device pinning, if desired, stays in the shell per the THREAD convention (no py literal):
    /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/test_routeexec_writesite.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SCRIPTS_DIR = Path(__file__).resolve().parent
_TIL_DIR = _SCRIPTS_DIR.parent  # thread_isaac_lab/
_ENVS_DIR = _TIL_DIR / "envs"
for _p in (str(_TIL_DIR), str(_ENVS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import route_executor as rex  # noqa: E402
from configs.task_config import (  # noqa: E402
    GRIPPER_DRIVER_CLOSE_RAD,
    GRIPPER_DRIVER_EFFORT_LIMIT_NM,
    GRIPPER_DRIVER_HALF_OPEN_RAD,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_SERVO_TARGET_KD,
    GRIPPER_SERVO_TARGET_KE,
    JOINTS_PER_ARM,
)

_N_ARM = 2 * JOINTS_PER_ARM  # 28
_GRIPPER_LOCAL = sorted(rex._GRIPPER_COORDS_LOCAL)  # {6-13, 20-27}
_ARM_LOCAL = rex._ARM_OVERWRITE_LOCAL  # {0-5, 14-19}


def _ref_28wide(phys_jq, phys_jqd, src_per_world, arm_q_start, arm_qd_start, n_world):
    """The flag-OFF reference: write ALL 28 coords (arm + gripper) per world (the current env behaviour)."""
    for w in range(n_world):
        phys_jq[arm_q_start[w] : arm_q_start[w] + _N_ARM] = src_per_world[w]
        phys_jqd[arm_qd_start[w] : arm_qd_start[w] + _N_ARM] = 0.0
    return phys_jq, phys_jqd


_ARM_Q_START = [0, 100]
_ARM_QD_START = [0, 96]
_TOTAL = 200


class _MockWarpArray:
    """A warp-array stand-in: ``.numpy()`` returns a HOST COPY (CC3-CH5), ``.assign()`` stores a copy."""

    def __init__(self, arr):
        self._arr = np.asarray(arr, dtype=np.float32).copy()

    def numpy(self):
        return self._arr.copy()

    def assign(self, arr):
        self._arr = np.asarray(arr, dtype=np.float32).copy()


class _MockControl:
    def __init__(self, n, fill):
        self.joint_target_pos = _MockWarpArray(np.full(n, fill, dtype=np.float32))


def _build_executor(grip_frames=None, forbid_banked_fork=False, arm_q=None):
    """Build a RouteExecutor over a synthetic 7701-frame recording + a mock control seeded OPEN."""
    n_frames = rex._REC_LAST_CTRL_FRAME + 1
    grip = np.zeros((n_frames, 2), dtype=np.float32)  # cols [L, R]
    for f, (gl, gr) in (grip_frames or {}).items():
        grip[f] = (gl, gr)
    recording = {
        "ee_pos_r": np.zeros((n_frames, 3), dtype=np.float32),
        "ee_pos_l": np.zeros((n_frames, 3), dtype=np.float32),
        "grip_cmd": grip,
        "phase_id": np.zeros(n_frames, dtype=np.int64),  # 0 is a valid _RECORDED_PHASE_TO_G key
        # W1-B2 contract v2: cable_xyz + held_seg_l are REQUIRED keys now (spec sec 4.2 N9).
        "cable_xyz": np.zeros((n_frames, 40, 3), dtype=np.float32),
        "held_seg_l": np.zeros(n_frames, dtype=np.int64),
    }
    if arm_q is not None:
        recording["arm_q"] = arm_q  # OPTIONAL key (D rho=0 feedforward source)
    control = _MockControl(_TOTAL, GRIPPER_DRIVER_OPEN_RAD)  # build-seeded OPEN (servo_seed_assert passes)
    ex = rex.RouteExecutor(
        _ARM_Q_START,
        _ARM_QD_START,
        900,
        state_0=None,
        control=control,
        state_bank=None,
        recording=recording,
        forbid_banked_fork=forbid_banked_fork,
    )
    return ex, control


def test_grip_transit_window():
    """R2: the recorded grip_cmd [L,R] staircase maps to per-arm drivers EXACTLY, per physics sub-frame."""
    # cf = arange(0, 7701, 10); step_f[t] = cf[t]. Frame for RL step t, sub-frame i = cf[t] + i.
    # transit window (L_HALF_UNCLAMP): L target == 0.69 (HALF_OPEN hold) while R == 0.0 (OPEN, re-grasps).
    f_transit = 5 * rex._REC_CADENCE + 3  # cf[5]=50, sub_i=3 -> 53
    f_distinct = 6 * rex._REC_CADENCE + 0  # cf[6]=60, sub_i=0 -> 60
    ex, control = _build_executor(
        grip_frames={
            f_transit: (GRIPPER_DRIVER_HALF_OPEN_RAD, GRIPPER_DRIVER_OPEN_RAD),  # [L=0.69, R=0.0]
            f_distinct: (0.31, 0.62),  # distinct L!=R to prove the [L,R]->per-arm mapping is not swapped
        }
    )
    maps = ex._maps

    # (a) transit window: L drivers -> 0.69, R drivers -> 0.0 (both worlds).
    ex.apply_recorded_grip([5, 5], 3)
    jtp = control.joint_target_pos.numpy()
    for w in range(2):
        for d in maps["l_driver_dofs"][w]:
            assert abs(jtp[d] - GRIPPER_DRIVER_HALF_OPEN_RAD) < 1e-6, f"L driver {d} != 0.69 (transit hold)"
        for d in maps["r_driver_dofs"][w]:
            assert abs(jtp[d] - GRIPPER_DRIVER_OPEN_RAD) < 1e-6, f"R driver {d} != 0.0 (re-grasp OPEN)"

    # (b) [L,R] mapping (not swapped): L col -> l_driver_dofs (0.31), R col -> r_driver_dofs (0.62).
    ex.apply_recorded_grip([6, 6], 0)
    jtp = control.joint_target_pos.numpy()
    for w in range(2):
        for d in maps["l_driver_dofs"][w]:
            assert abs(jtp[d] - 0.31) < 1e-6, f"L driver {d} got R value -> [L,R] mapping SWAPPED"
        for d in maps["r_driver_dofs"][w]:
            assert abs(jtp[d] - 0.62) < 1e-6, f"R driver {d} got L value -> [L,R] mapping SWAPPED"
    print("  [grip-transit] PASS: [L=0.69, R=0.0] transit window + non-swapped [L,R]->per-arm mapping")


def test_grip_hold_clamp():
    """W1-B2 R4c (spec sec 4.2 N3 + CC3-4 dual-site): a HELD world's staircase frame clamps to the chunk
    END (cf[t]+cadence-1) at BOTH the write site AND the readback-assert site; None = v1-identical."""
    cad = rex._REC_CADENCE
    # chunk 5: distinct values at sub-frame 3 (53) vs chunk end (59). Chunk-end values are NON-OPEN so the
    # one-time readback assert ARMS on this very call -- if the readback recomputed the frame WITHOUT the
    # clamp (the CC3-4 crack), it would compare the chunk-end write against frame 53's values and throw.
    ex, control = _build_executor(
        grip_frames={
            5 * cad + 3: (0.11, 0.22),  # cf[5]+3 = 53 (what an UN-held world reads at sub_i=3)
            5 * cad + (cad - 1): (GRIPPER_DRIVER_HALF_OPEN_RAD, 0.667),  # cf[5]+9 = 59 (chunk end)
        }
    )
    maps = ex._maps
    ex.apply_recorded_grip([5, 5], 3, hold_mask=[True, False])  # w0 HELD, w1 marching
    jtp = control.joint_target_pos.numpy()
    for d in maps["l_driver_dofs"][0]:
        assert abs(jtp[d] - GRIPPER_DRIVER_HALF_OPEN_RAD) < 1e-6, f"held w0 L driver {d} != chunk-end value"
    for d in maps["r_driver_dofs"][0]:
        assert abs(jtp[d] - 0.667) < 1e-6, f"held w0 R driver {d} != chunk-end value"
    for d in maps["l_driver_dofs"][1]:
        assert abs(jtp[d] - 0.11) < 1e-6, f"marching w1 L driver {d} != sub_i frame value"
    for d in maps["r_driver_dofs"][1]:
        assert abs(jtp[d] - 0.22) < 1e-6, f"marching w1 R driver {d} != sub_i frame value"
    assert ex._grip_rb_checked, "readback assert did not arm (non-open chunk-end write should arm it)"
    # ff twin (R4d): the recorded arm_q feedforward clamps with the SAME convention.
    n_frames = rex._REC_LAST_CTRL_FRAME + 1
    arm_q = np.zeros((n_frames, rex._N_ARM_JOINTS), dtype=np.float32)
    arm_q[5 * cad + 3, 0] = 1.0
    arm_q[5 * cad + (cad - 1), 0] = 2.0
    ex2, _ = _build_executor(arm_q=arm_q)

    class _S:
        joint_q = _MockWarpArray(np.zeros(_TOTAL, dtype=np.float64))
        joint_qd = _MockWarpArray(np.zeros(_TOTAL, dtype=np.float64))

    maps2 = ex2._maps
    jq_ff = ex2.apply_recorded_arm_ff(
        [5, 5], 3, _S(), maps2["arm_ow_q_idx"], maps2["arm_ow_qd_idx"], hold_mask=[True, False]
    )
    assert jq_ff[0][0] == 2.0, f"held w0 ff row != chunk-end arm_q: {jq_ff[0][0]}"
    assert jq_ff[1][0] == 1.0, f"marching w1 ff row != sub_i arm_q: {jq_ff[1][0]}"
    print("  [B2 hold-clamp] PASS: held world -> chunk-end frame at write+readback sites; ff twin; v1 None-path")


def test_hold_resume_semantics():
    """W1-B2 R3m resume half (%10 audit F-1a): after a resume the NEXT chunk (t+1) is driven from its own
    start -- the frozen chunk's staircase is never re-walked (N3). Composes update_sync's mask with the
    env increment miniature route_t += ~mask and the hold-clamped staircase."""
    cad = rex._REC_CADENCE
    ex, control = _build_executor(
        grip_frames={
            10 * cad: (0.11, 0.0),  # chunk 10 START
            10 * cad + cad - 1: (0.22, 0.0),  # chunk 10 END (held worlds pin here)
            11 * cad: (0.33, 0.0),  # chunk 11 START (what a resumed world must drive next)
        }
    )
    maps = ex._maps
    v_hi = np.zeros((40, 3))
    v_hi[0, 0] = 0.020  # 20mm on seg 0 (synthetic rec cable is zeros) -> fire
    v_lo = np.zeros((40, 3))
    v_lo[0, 0] = 0.011  # 11mm -> <=12 resume
    v_0 = np.zeros((40, 3))
    t = np.array([10, 10])
    m1 = ex.update_sync(list(t), [v_hi, v_0], [True, True])
    assert m1.tolist() == [True, False], f"fire setup: {m1.tolist()}"
    t = t + (~m1).astype(int)  # env increment miniature (R4a): held w0 stays 10, w1 -> 11
    assert t.tolist() == [10, 11]
    ex.apply_recorded_grip(list(t), 0, hold_mask=m1)  # held step: w0 pins chunk-10 END, w1 chunk-11 START
    jtp = control.joint_target_pos.numpy()
    assert all(abs(jtp[d] - 0.22) < 1e-6 for d in maps["l_driver_dofs"][0]), "held w0 must pin chunk-10 END"
    assert all(abs(jtp[d] - 0.33) < 1e-6 for d in maps["l_driver_dofs"][1]), "marching w1 must drive chunk 11"
    m2 = ex.update_sync(list(t), [v_lo, v_0], [True, True])
    assert m2.tolist() == [False, False] and ex._resume_count[0] == 1, "11mm must resume w0"
    t = t + (~m2).astype(int)  # resumed w0 -> 11
    assert t.tolist() == [11, 12]
    ex.apply_recorded_grip(list(t), 0, hold_mask=m2)
    jtp = control.joint_target_pos.numpy()
    assert all(abs(jtp[d] - 0.33) < 1e-6 for d in maps["l_driver_dofs"][0]), (
        "resumed w0 must drive chunk 11 from its START (0.33) -- re-walking chunk 10 (0.11) = the N3 sawtooth"
    )
    print("  [B2 resume-semantics] PASS: fire->freeze (chunk-end pin) -> resume -> next chunk from start")


def test_reset_reseed_open():
    """R1a: reset re-seeds every driver's servo target to OPEN (episode >= 2 starts OPEN, not CLOSED)."""
    ex, control = _build_executor()
    # simulate an episode ending with the grippers CLOSED (servo target latched at CLOSE).
    control.joint_target_pos.assign(np.full(_TOTAL, GRIPPER_DRIVER_CLOSE_RAD, dtype=np.float32))
    ex.reseed_grip_open([0, 1])
    jtp = control.joint_target_pos.numpy()
    driver = set(rex.build_perworld_index_maps(_ARM_Q_START, _ARM_QD_START)["all_driver_dofs"])
    for d in driver:  # every driver dof re-seeded OPEN
        assert abs(jtp[d] - GRIPPER_DRIVER_OPEN_RAD) < 1e-6, f"driver {d} not re-seeded OPEN (still {jtp[d]})"
    # a NON-driver gripper qd (follower, e.g. 8/108) + an arm dof (0) stay at the pre-reset CLOSE value.
    for d in (0, 8, 108):
        assert d not in driver
        assert abs(jtp[d] - GRIPPER_DRIVER_CLOSE_RAD) < 1e-6, f"non-driver {d} was clobbered by reseed"
    print("  [reset-reseed] PASS: after CLOSE-latch, reset re-seeds all drivers OPEN; non-drivers untouched")


def test_settled_fk_gripper_patch():
    """R1d/CC4-CH5: the reset-init source's gripper coords are overwritten from world-0 physics; arm intact."""
    settled = np.arange(1000.0, 1000.0 + _N_ARM, dtype=np.float64)  # 28-wide FK arm row (distinct values)
    orig = settled.copy()
    phys_jq = np.full(_TOTAL, -1.0, dtype=np.float64)
    aq0 = _ARM_Q_START[0]
    for gc in _GRIPPER_LOCAL:
        phys_jq[aq0 + gc] = 500.0 + gc  # world-0 post-settle gripper config (distinct)
    rex.patch_settled_fk_gripper(settled, phys_jq, aq0)
    for gc in _GRIPPER_LOCAL:  # gripper coords now = world-0 physics
        assert settled[gc] == 500.0 + gc, f"gripper coord {gc} not patched from physics"
    for al in _ARM_LOCAL:  # arm coords untouched
        assert settled[al] == orig[al], f"arm coord {al} was modified by the gripper patch"
    print("  [settled-patch] PASS: gripper coords <- world-0 physics; arm coords untouched")


def test_forbid_banked_fork():
    """R1: forbid_banked_fork=True -> reset_to_phase(k>=1) raises; k=0 no-op; default False keeps capability."""
    ex_f, _ = _build_executor(forbid_banked_fork=True)
    ex_f.reset_to_phase(0)  # k=0 -> no-op (env-core reset authoritative), must NOT raise
    try:
        ex_f.reset_to_phase(1)
        raise AssertionError("reset_to_phase(1) did NOT raise under forbid_banked_fork=True")
    except NotImplementedError as e:
        assert "comp3b" in str(e), f"unexpected NotImplementedError text: {e}"
    # default (False): k>=1 is allowed to proceed (no bank -> no-op), NOT guarded (state-bank unit path).
    ex_ok, _ = _build_executor(forbid_banked_fork=False)
    ex_ok.reset_to_phase(1)  # no bank + state_0 None -> no-op; must NOT raise
    print("  [forbid-fork] PASS: forbid=True raises for k>=1 (comp3b); k=0 ok; default keeps k>=1 capability")


# =====================================================================================================
# L4 chunk-3 unit (R6 obs source + R8 discriminating servo readback). Pure CPU/no-GPU: the Newton model
# and the mj_model are mocked; the REAL-build positive/negative demonstration is the L2 probe
# (eval_runs/.../comp3_void_readback.py, flag-OFF build must FAIL the readback / flag-ON must PASS).
# =====================================================================================================


def test_physics_finger_obs():
    """R6: flag-ON obs[7]/[15] source = PHYSICS joint_q (NOT the FK-side OPEN-pinned sum)."""
    import newton_route_env as nre

    aq0 = _ARM_Q_START[1]  # world-1 (offset base; catches a hardcoded world-0 read)
    phys_jq = np.zeros(_TOTAL, dtype=np.float64)
    l0, l1 = GRIPPER_DRIVER_JOINT_IDX[0], GRIPPER_DRIVER_JOINT_IDX[1]
    r0, r1 = JOINTS_PER_ARM + l0, JOINTS_PER_ARM + l1
    phys_jq[aq0 + l0], phys_jq[aq0 + l1] = 0.31, 0.02  # L drivers (physics, mid-close)
    phys_jq[aq0 + r0], phys_jq[aq0 + r1] = 0.62, 0.04  # R drivers (physics, distinct)
    r_f, l_f = nre.physics_finger_obs(phys_jq, aq0)
    assert abs(r_f - 0.66) < 1e-9, f"r_finger {r_f} != physics driver sum 0.66"
    assert abs(l_f - 0.33) < 1e-9, f"l_finger {l_f} != physics driver sum 0.33"
    # source discrimination: the FK-side sum (OPEN-pinned = 0.0) differs -> a FK-sourced obs would be 0.
    assert r_f != 0.0 and l_f != 0.0, "physics source indistinguishable from the FK OPEN pin"
    print("  [finger-obs] PASS: obs[7]/[15] flag-ON source = physics joint_q per-world driver sum")


def _mock_models(wired, blanket=False):
    """Build (newton-model, mj_model) mocks: wired=True mirrors the base servo mutation; False = flag-OFF."""
    import newton_route_env as nre

    pos_mode = int(nre.newton.JointTargetMode.POSITION)
    maps = rex.build_perworld_index_maps(_ARM_Q_START, _ARM_QD_START)
    jtm = np.zeros(_TOTAL, dtype=np.int32)
    ke = np.zeros(_TOTAL, dtype=np.float32)
    kd = np.zeros(_TOTAL, dtype=np.float32)
    eff = np.full(_TOTAL, 1e6, dtype=np.float32)
    if wired:
        for d in maps["all_driver_dofs"]:
            jtm[d] = pos_mode
            ke[d] = GRIPPER_SERVO_TARGET_KE
            kd[d] = GRIPPER_SERVO_TARGET_KD
            eff[d] = GRIPPER_DRIVER_EFFORT_LIMIT_NM
    if blanket:  # blanket-wired defect: a 4-bar FOLLOWER also carries the servo
        f = _ARM_QD_START[0] + GRIPPER_DRIVER_JOINT_IDX[0] + 1
        jtm[f] = pos_mode
        ke[f] = GRIPPER_SERVO_TARGET_KE

    class _M:
        joint_target_mode = _MockWarpArray(jtm)
        joint_target_ke = _MockWarpArray(ke)
        joint_target_kd = _MockWarpArray(kd)
        joint_effort_limit = _MockWarpArray(eff)

    n_act = 4 if wired else 0

    class _MJ:
        nu = n_act
        actuator_gainprm = np.zeros((n_act, 10))
        actuator_biasprm = np.zeros((n_act, 10))
        actuator_trnid = np.zeros((n_act, 2), dtype=np.int32)
        jnt_actfrcrange = np.zeros((8, 2))

    for a in range(n_act):  # solver_mujoco POSITION-mode convention (hinge: effort cap = JOINT actfrcrange)
        _MJ.actuator_gainprm[a, 0] = GRIPPER_SERVO_TARGET_KE
        _MJ.actuator_biasprm[a, 1] = -GRIPPER_SERVO_TARGET_KE
        _MJ.actuator_biasprm[a, 2] = -GRIPPER_SERVO_TARGET_KD
        _MJ.actuator_trnid[a, 0] = a  # target joint id
        _MJ.jnt_actfrcrange[a] = (-GRIPPER_DRIVER_EFFORT_LIMIT_NM, GRIPPER_DRIVER_EFFORT_LIMIT_NM)
    return _M, _MJ, maps


def test_servo_readback_discriminating():
    """R8/K6: the readback PASSES a wired build, RAISES on unwired (flag-OFF) + on a blanket-wired defect."""
    import newton_route_env as nre

    negative = [
        _ARM_QD_START[w] + off
        for w in range(2)
        for off in (0, GRIPPER_DRIVER_JOINT_IDX[0] + 1, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0] + 1)
    ]
    # (a) wired build -> PASS.
    m, mj, maps = _mock_models(wired=True)
    nre.servo_readback_assert(m, mj, maps["all_driver_dofs"], negative)
    # (b) UNWIRED (flag-OFF-like) build -> must RAISE (this is the discriminating property K6 demanded).
    m0, mj0, _ = _mock_models(wired=False)
    try:
        nre.servo_readback_assert(m0, mj0, maps["all_driver_dofs"], negative)
        raise AssertionError("servo_readback_assert PASSED an unwired build (vacuous, K6 regression)")
    except AssertionError as e:
        if "vacuous" in str(e):
            raise
    # (c) blanket-wired defect (a follower carries the servo) -> negative control must RAISE.
    mb, mjb, _ = _mock_models(wired=True, blanket=True)
    try:
        nre.servo_readback_assert(mb, mjb, maps["all_driver_dofs"], negative)
        raise AssertionError("negative control MISSED a blanket-wired follower")
    except AssertionError as e:
        if "MISSED" in str(e):
            raise
        assert "NEGATIVE CONTROL" in str(e), f"unexpected failure leg: {e}"
    print("  [servo-readback] PASS: wired ok; unwired RAISES (discriminating); blanket-wired RAISES (neg ctrl)")


_GOLDEN_NPZ = (
    _TIL_DIR.parent
    / "eval_runs"
    / "troot_optE_dapg_wholeroute_scope_20260701"
    / "w0e_81rerun_snapdown_0537"
    / "cell_x0_y0"
    / "route_demo_raw.npz"
)


def test_golden_transit_columns():
    """G-F6 (fold 8d): the transit-window mapping asserted against the REAL golden npz columns (not only
    the synthetic recording -- closes the self-referentiality of the L4 transit test)."""
    if not _GOLDEN_NPZ.exists():
        raise AssertionError(f"golden npz missing: {_GOLDEN_NPZ}")
    z = np.load(_GOLDEN_NPZ)
    rec = {k: z[k] for k in ("ee_pos_r", "ee_pos_l", "grip_cmd", "phase_id", "cable_xyz", "held_seg_l")}
    control = _MockControl(_TOTAL, GRIPPER_DRIVER_OPEN_RAD)
    ex = rex.RouteExecutor(_ARM_Q_START, _ARM_QD_START, 900, state_0=None, control=control, recording=rec)
    g = z["grip_cmd"]
    # first REAL transit frame: L == float32(0.69) hold while R == 0.0 (L_HALF_UNCLAMP window).
    m = (g[:, 0] == np.float32(GRIPPER_DRIVER_HALF_OPEN_RAD)) & (g[:, 1] == 0.0)
    idx = np.argwhere(m).ravel()
    assert len(idx) > 0, "golden recording has no [L=0.69, R=0.0] transit frame -- premise broken"
    f = int(idx[0])
    t, sub_i = f // rex._REC_CADENCE, f % rex._REC_CADENCE
    ex.apply_recorded_grip([t, t], sub_i)
    jtp = control.joint_target_pos.numpy()
    maps = ex._maps
    for w in range(2):
        for d in maps["l_driver_dofs"][w]:
            assert abs(jtp[d] - GRIPPER_DRIVER_HALF_OPEN_RAD) < 1e-6, f"golden transit: L driver {d} != 0.69"
        for d in maps["r_driver_dofs"][w]:
            assert abs(jtp[d] - GRIPPER_DRIVER_OPEN_RAD) < 1e-6, f"golden transit: R driver {d} != 0.0"
    print(f"  [golden-transit] PASS: REAL golden frame {f} (t={t},sub={sub_i}) maps [L=0.69, R=0.0] per-arm")


def test_readback_arming():
    """P-F2 (fold 4): the one-time grip readback arms at the first CLOSE onset, NOT at an all-OPEN call
    (all-OPEN == warp zero-init default -> a vacuous arm would never discriminate, K6)."""
    f_close = 7 * rex._REC_CADENCE  # frame 70: CLOSE both
    ex, _ = _build_executor(grip_frames={f_close: (GRIPPER_DRIVER_CLOSE_RAD, GRIPPER_DRIVER_CLOSE_RAD)})
    ex.apply_recorded_grip([0, 0], 0)  # frame 0 = all-OPEN -> must NOT arm
    assert not ex._grip_rb_checked, "readback armed on an all-OPEN call (vacuous, K6/P-F2 regression)"
    ex.apply_recorded_grip([7, 7], 0)  # frame 70 = CLOSE -> arms + verifies
    assert ex._grip_rb_checked, "readback did not arm at the first CLOSE onset"
    # P-F3: sub_i bounds fail loud.
    try:
        ex.apply_recorded_grip([0, 0], rex._REC_CADENCE)
        raise AssertionError("sub_i == _REC_CADENCE did NOT raise (P-F3 bounds)")
    except AssertionError as e:
        if "did NOT raise" in str(e):
            raise
        assert "sub_i" in str(e)
    print("  [readback-arming] PASS: no arm at all-OPEN; arms at first CLOSE; sub_i bounds fail loud")


def test_lane_floor():
    """Lane-aware EE-Z floor (G1 root-cause fix, Rs adjudication B + 5tai folds R-A/R-B): in/out-lane +
    edge values + C1-island carve-out + shared-floor pair semantics + the recorded grasp-park target must
    NOT bind the lane floor (and DID bind the old clip-base floor)."""
    import newton_route_env as nre
    import route_env_config as rc_mod

    f_lane, f_old = float(nre.EE_Z_FLOOR_KO_LANE), float(nre.EE_Z_FLOOR_KO)
    f_island = float(nre.EE_Z_FLOOR_KO_C1_ISLAND)
    assert abs(f_lane - 1.06492) < 1e-5, f_lane
    assert abs(f_old - 1.06992) < 1e-5, f_old
    assert abs((f_old - f_lane) - 0.005) < 1e-9, "step must equal CLIP_BASE_HEIGHT"
    # R-B: island floor is FLOAT-AWARE (formula, not a pinned literal): degenerates to f_old at float 0.
    assert abs(f_island - (f_old + rc_mod.ROUTE_CLIP_FLOAT_Z)) < 1e-9, "island floor must track the float"
    assert abs(f_island - 1.08992) < 1e-5, f_island  # current float 0.020
    # lane bounds pinned to the banked void footprint (probe leg C + build-time lane_void_parity_assert
    # pin the REAL built model to the same).
    assert abs(nre._LANE_Y_LO - 0.090) < 1e-9 and abs(nre._LANE_Y_HI - 0.210) < 1e-9
    assert abs(nre._LANE_X_LO - 0.234) < 1e-9 and abs(nre._LANE_X_HI - 0.366) < 1e-9
    # in-lane (park XY), out-lane, and inclusive edges.
    assert nre.ee_z_floor_ko(0.300, 0.106) == f_lane and nre.ee_z_floor_ko(0.300, 0.194) == f_lane
    assert nre.ee_z_floor_ko(0.300, 0.250) == f_old and nre.ee_z_floor_ko(0.100, 0.106) == f_old
    assert nre.ee_z_floor_ko(0.234, 0.090) == f_lane and nre.ee_z_floor_ko(0.366, 0.210) == f_lane
    assert nre.ee_z_floor_ko(0.2339, 0.106) == f_old and nre.ee_z_floor_ko(0.300, 0.2101) == f_old
    # R-B: C1 island (inside the lane box) takes PRECEDENCE over the lane floor; inclusive edges.
    assert nre.ee_z_floor_ko(0.350, 0.150) == f_island, "C1 center must get the island floor"
    assert nre.ee_z_floor_ko(0.330, 0.135) == f_island and nre.ee_z_floor_ko(0.370, 0.165) == f_island
    assert nre.ee_z_floor_ko(0.3299, 0.150) == f_lane and nre.ee_z_floor_ko(0.350, 0.1651) == f_lane
    # R-A: pair semantics -- common-mode shares the MAX floor (z-span preserved: floor_r == floor_l
    # always); transit stays per-arm.
    assert nre.ee_z_floor_ko_pair(0.300, 0.194, 0.300, 0.106, True) == (f_lane, f_lane)
    assert nre.ee_z_floor_ko_pair(0.300, 0.250, 0.300, 0.106, True) == (f_old, f_old)  # one out -> both up
    assert nre.ee_z_floor_ko_pair(0.350, 0.150, 0.300, 0.106, True) == (f_island, f_island)
    assert nre.ee_z_floor_ko_pair(0.300, 0.250, 0.300, 0.106, False) == (f_old, f_lane)  # transit per-arm
    for rxy, lxy in (((0.300, 0.194), (0.300, 0.106)), ((0.366, 0.210), (0.234, 0.090))):
        fr, fl = nre.ee_z_floor_ko_pair(rxy[0], rxy[1], lxy[0], lxy[1], True)
        assert fr == fl, "common-mode must return z-equal floors (span invariant)"
    # recorded low-z frames (REAL golden npz): every below-old-floor frame must be in-lane on BOTH arms
    # and OUTSIDE the island -> shared max floor == lane floor == replay-neutral (R-A/R-B data assert;
    # the 81-cell version lives in comp3_lane_floor_sweep). Park frame also documents the old bind.
    if not _GOLDEN_NPZ.exists():
        raise AssertionError(f"golden npz missing: {_GOLDEN_NPZ}")
    z = np.load(_GOLDEN_NPZ)
    pl = np.asarray(z["ee_pos_l"], dtype=np.float64)
    pr = np.asarray(z["ee_pos_r"], dtype=np.float64)
    below = (pl[:, 2] < f_old) | (pr[:, 2] < f_old)
    assert below.sum() > 0, "golden must document the old-floor bind window"
    for f in np.nonzero(below)[0]:
        frf, flf = nre.ee_z_floor_ko_pair(pr[f, 0], pr[f, 1], pl[f, 0], pl[f, 1], True)
        assert frf == f_lane and flf == f_lane, f"replay-neutrality broken at frame {f}: shared floor != lane"
    for key in ("ee_pos_l", "ee_pos_r"):
        park = np.asarray(z[key], dtype=np.float64)[1000]  # mid close-window park frame
        assert park[2] > f_lane + 1e-4, f"{key} park z {park[2]:.5f} binds the LANE floor"
        assert park[2] < f_old, f"{key} park z {park[2]:.5f} no longer documents the old-floor bind"
    print(
        "  [lane-floor] PASS: values+edges+island(float-aware)+pair(shared-max/z-equal) pinned; "
        "replay low-z frames all lane-floored (neutral); park documents old bind"
    )


class _MockState:
    """A physics-state stand-in for the feedforward writer (joint_q/joint_qd, host-copy semantics)."""

    def __init__(self, n, fill):
        self.joint_q = _MockWarpArray(np.full(n, fill, dtype=np.float32))
        self.joint_qd = _MockWarpArray(np.full(n, fill, dtype=np.float32))


