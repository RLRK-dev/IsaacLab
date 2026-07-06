# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sync-guard DoD: assert the whole-route env-core ``route_env_config.ROUTE_*`` geometry block equals the
canonical route provenance (``route_demo_raw_meta.json`` env_gates + ``route_c2_pin.json``).

This is a STATIC drift tripwire (reads a canonical meta ONCE at test time; the runtime env-core uses the
hardcoded ``ROUTE_*`` values -- no runtime ``eval_runs`` dependency). If ``task_config`` or a future edit
desyncs the ``ROUTE_*`` block from the recorded route's env-gate overrides (``CLIP2_Y``, ``CLIP_FLOAT_Z``,
...), this fails. Rationale: the env-core inherited ``task_config`` 5-clip-array defaults, but the C1->C2
whole-route work uses the route env-gate overrides; the two drifted (C2 y 0.075 vs 0.000; groove z 809 vs
829) and were reconciled into the ``ROUTE_*`` block (%12 systematic pin, 2026-07-06).
"""

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _sub in ("thread_isaac_lab/envs", "thread_isaac_lab/configs"):
    _p = os.path.join(_REPO_ROOT, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

# The canonical route provenance (nominal cell) -- the FON_V1 / 0.716-baseline recorded route.
_CANONICAL_CELL = os.path.join(
    _REPO_ROOT,
    "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0",
)


def test_route_geometry_sync():
    """route_env_config ROUTE_* == canonical meta env_gates (drift tripwire)."""
    import route_env_config as rc

    with open(os.path.join(_CANONICAL_CELL, "route_demo_raw_meta.json")) as _f:
        meta = json.load(_f)
    with open(os.path.join(_CANONICAL_CELL, "route_c2_pin.json")) as _f:
        pin = json.load(_f)
    gates = meta["env_gates"]

    assert rc.ROUTE_C1_XY[0] == float(gates["CLIP_X"]), "ROUTE_C1_XY.x != meta CLIP_X"
    assert rc.ROUTE_C1_XY[1] == float(gates["CLIP_Y"]), "ROUTE_C1_XY.y != meta CLIP_Y"
    assert rc.ROUTE_C2_XY[0] == float(gates["CLIP2_X"]), "ROUTE_C2_XY.x != meta CLIP2_X"
    assert rc.ROUTE_C2_XY[1] == float(gates["CLIP2_Y"]), "ROUTE_C2_XY.y != meta CLIP2_Y"
    assert rc.ROUTE_C2_XY[1] == meta["resolved_clip_c2_xy"][1], "ROUTE_C2_XY.y != resolved_clip_c2_xy"
    assert float(gates["CLIP_FLOAT_Z"]) == rc.ROUTE_CLIP_FLOAT_Z, "ROUTE_CLIP_FLOAT_Z != meta CLIP_FLOAT_Z"
    # ROUTE_GROOVE_Z == the recorded route groove z (base 809 + float 20mm == route_c2_pin groove_z_mm).
    assert abs(rc.ROUTE_GROOVE_Z - pin["route_c2_settle"]["groove_z_mm"] / 1000.0) < 1e-9, (
        "ROUTE_GROOVE_Z != route_c2_pin groove_z_mm/1000"
    )


if __name__ == "__main__":
    test_route_geometry_sync()
    print("SYNC_GUARD: PASS (route_env_config ROUTE_* == canonical meta env_gates)")
