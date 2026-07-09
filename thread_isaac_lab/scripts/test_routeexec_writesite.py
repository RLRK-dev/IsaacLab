# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""No-GPU CPU WRITE-PATTERN unit for the comp3 write-site flag-gate (L1, plan v2 §12/R5).

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
from configs.task_config import JOINTS_PER_ARM  # noqa: E402

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
            assert jq_on[b + li] == jq_off[b + li], f"arm q mismatch w{w} li{li}: {jq_on[b+li]} vs {jq_off[b+li]}"
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


if __name__ == "__main__":
    print("[L1 write-pattern unit] comp3 write-site flag-gate (no-GPU, CPU)")
    test_broadcast()
    test_perworld()
    test_guard()
    print("ALL PASS (broadcast + perworld + guard) -- flag-ON diff == gripper-coord set exactly; guard fires loud")
