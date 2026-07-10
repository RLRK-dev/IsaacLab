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


def test_broadcast():
    """apply_arm_only_write_broadcast (setup/hold path :460) vs the 28-wide reference."""
    # 2-world layout with a cable FREE-root gap between worlds (world1 arm start is NOT 28 -- sec 23).
    arm_q_start = [0, 100]
    arm_qd_start = [0, 96]
    n_world = 2
    total_q, total_qd = 200, 200
    maps = rex.build_perworld_index_maps(arm_q_start, arm_qd_start)

    fk_1world = np.arange(1.0, 1.0 + _N_ARM)  # one world's 28-wide arm pose (arm+gripper)
    src_per_world = [fk_1world.copy(), fk_1world.copy()]  # broadcast = same pose to every world

    # flag-OFF reference (28-wide), starting from a distinct sentinel so "untouched" is detectable.
    SENT = -777.0
    jq_off = np.full(total_q, SENT)
    jqd_off = np.full(total_qd, SENT)
    _ref_28wide(jq_off, jqd_off, src_per_world, arm_q_start, arm_qd_start, n_world)

    # flag-ON (arm-only), same sentinel start.
    jq_on = np.full(total_q, SENT)
    jqd_on = np.full(total_qd, SENT)
    rex.apply_arm_only_write_broadcast(
        jq_on, jqd_on, fk_1world, maps["arm_ow_q_idx"], maps["arm_ow_qd_idx"], maps["arm_ow_src"]
    )

    for w in range(n_world):
        b = arm_q_start[w]
        bd = arm_qd_start[w]
        for li in _ARM_LOCAL:  # arm coords: flag-ON must equal flag-OFF (byte-identical arm write)
            assert jq_on[b + li] == jq_off[b + li], f"arm q mismatch w{w} li{li}: {jq_on[b + li]} vs {jq_off[b + li]}"
            assert jqd_on[bd + li] == jqd_off[bd + li] == 0.0, f"arm qd mismatch w{w} local{li}"
        for li in _GRIPPER_LOCAL:  # gripper coords: flag-ON UNTOUCHED (sentinel), flag-OFF WRITTEN
            assert jq_on[b + li] == SENT, f"flag-ON gripper q was written w{w} local{li} (should be servo-held)"
            assert jqd_on[bd + li] == SENT, f"flag-ON gripper qd was written w{w} local{li}"
            assert jq_off[b + li] != SENT, f"flag-OFF ref should have written gripper q w{w} local{li}"
    # the ONLY q/qd diff between flag-OFF and flag-ON is exactly the gripper-coord set
    diff_q = [i for i in range(total_q) if jq_on[i] != jq_off[i]]
    expected_q = sorted(arm_q_start[w] + li for w in range(n_world) for li in _GRIPPER_LOCAL)
    assert diff_q == expected_q, f"broadcast q diff set != gripper set: {diff_q} vs {expected_q}"
    print(f"  [broadcast] PASS: arm byte-id; gripper untouched flag-ON; diff==gripper set ({len(diff_q)})")


def test_perworld():
    """apply_arm_only_write_perworld (RL drive path :823) vs the 28-wide reference."""
    arm_q_start = [0, 100]
    arm_qd_start = [0, 96]
    n_world = 2
    total_q, total_qd = 200, 200
    maps = rex.build_perworld_index_maps(arm_q_start, arm_qd_start)

    # distinct per-world 28-wide arm pose (drive = different target per world)
    jq_interp = np.stack([np.arange(1.0, 1.0 + _N_ARM), np.arange(50.0, 50.0 + _N_ARM)])  # [2, 28]

    SENT = -777.0
    jq_off = np.full(total_q, SENT)
    jqd_off = np.full(total_qd, SENT)
    _ref_28wide(jq_off, jqd_off, [jq_interp[0], jq_interp[1]], arm_q_start, arm_qd_start, n_world)

    jq_on = np.full(total_q, SENT)
    jqd_on = np.full(total_qd, SENT)
    rex.apply_arm_only_write_perworld(jq_on, jqd_on, jq_interp, maps["arm_ow_q_idx"], maps["arm_ow_qd_idx"])

    for w in range(n_world):
        b = arm_q_start[w]
        bd = arm_qd_start[w]
        for li in _ARM_LOCAL:
            assert jq_on[b + li] == jq_off[b + li], f"arm q mismatch w{w} local{li}"
            assert jqd_on[bd + li] == 0.0, f"arm qd not zeroed w{w} local{li}"
        for li in _GRIPPER_LOCAL:
            assert jq_on[b + li] == SENT, f"flag-ON gripper q written w{w} local{li}"
            assert jqd_on[bd + li] == SENT, f"flag-ON gripper qd written w{w} local{li}"
    diff_q = [i for i in range(total_q) if jq_on[i] != jq_off[i]]
    expected_q = sorted(arm_q_start[w] + li for w in range(n_world) for li in _GRIPPER_LOCAL)
    assert diff_q == expected_q, f"perworld q diff set != gripper set: {diff_q} vs {expected_q}"
    print(f"  [perworld] PASS: per-world arm byte-id; gripper untouched; diff==gripper set ({len(diff_q)})")


def test_guard():
    """The __init__ flag-matrix guard (K5/R8) fires BEFORE any scene build."""
    import newton_route_env as nre

    # grasp_actuation=True + stub route -> ValueError (servo would be built with no grip writer = inert).
    try:
        nre.NewtonRouteEnv(world_count=1, cfg={"grasp_actuation": True, "route_executor_impl": "stub"})
        raise AssertionError("guard did NOT raise for grasp_actuation=True + stub route")
    except ValueError as e:
        assert "route_executor" in str(e), f"unexpected ValueError text: {e}"
    # non-bool grasp_actuation -> AssertionError (cfg.get truthiness hazard).
    try:
        nre.NewtonRouteEnv(world_count=1, cfg={"grasp_actuation": "yes", "route_executor_impl": "route_executor"})
        raise AssertionError("guard did NOT raise for non-bool grasp_actuation")
    except AssertionError as e:
        if "did NOT raise" in str(e):
            raise
        assert "bool" in str(e), f"unexpected AssertionError text: {e}"
    print("  [guard] PASS: grasp_actuation=True+stub -> ValueError; non-bool -> AssertionError (pre-build)")


# =====================================================================================================
# L4 grip-drive / reset-reseed wiring unit (chunk 2: R1 reset + R2 grip staircase). Pure CPU/no-GPU: a
# warp array is mocked (``.numpy()`` returns a HOST COPY, ``.assign()`` writes back -- so a forgotten
# assign is caught, per CC3-CH5), and the RouteExecutor grip methods are exercised against a synthetic
# recording. Layout matches the L1 tests (2 worlds, cable FREE-root q/qd gap).
# =====================================================================================================

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


def _build_executor(grip_frames=None, forbid_banked_fork=False):
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
    }
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
    rec = {k: z[k] for k in ("ee_pos_r", "ee_pos_l", "grip_cmd", "phase_id")}
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


if __name__ == "__main__":
    print("[L1 write-pattern unit] comp3 write-site flag-gate (no-GPU, CPU)")
    test_broadcast()
    test_perworld()
    test_guard()
    print("[L4 grip-drive / reset-reseed unit] comp3 chunk 2 (R1 reset + R2 grip staircase)")
    test_grip_transit_window()
    test_reset_reseed_open()
    test_settled_fk_gripper_patch()
    test_forbid_banked_fork()
    print("[L4 chunk-3 unit] comp3 chunk 3 (R6 obs source + R8 discriminating servo readback)")
    test_physics_finger_obs()
    test_servo_readback_discriminating()
    print("[L4 fold unit] comp3 layer-2/5 folds (golden columns G-F6 + readback arming P-F2/P-F3)")
    test_golden_transit_columns()
    test_readback_arming()
    print(
        "ALL PASS (L1 broadcast+perworld+guard; L4 grip-transit+reset-reseed+settled-patch+forbid-fork"
        "+finger-obs+servo-readback+golden-transit+readback-arming)"
    )
