# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1 B0-4: derive the gate-iii 25-cell membership (offline mirror of dod9a_prime.py).

Recomputes, per canonical recording cell, the env strict predicate (c2_seated_honest AND c1_retained)
on the recorded FINAL cable state, using the offline mirror logic proven per-cell EXACT 81/81 against
the env's ACTUAL predicate methods (p2_envcore_smoke_20260706_211613/dod9a_prime.{py,json}: env==offline==25).
Pure numpy + route_env_config constants -- no env build, no GPU.

The emitted membership is PINNED as the B7 gate-iii flag-OFF byte-identity cell set (W1 charter B0-4,
%12 conditions 2026-07-12 14:26). B7 DoD (condition b): re-derive the set from the THEN-current predicate
and assert SET-EQUALITY (not count) vs the pinned membership; mismatch = loud STOP (predicate drifted).

Run (CPU):
    /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b04_derive_gateiii_25set.py
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import numpy as np

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _d in ("envs", "scripts", "configs"):
    _p = str(_TIL / _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import route_env_config as rc  # noqa: E402

GOLDEN_DIR = _EVAL / "w0e_81rerun_snapdown_0537"
OUT = _EVAL / "w1_b04_gateiii_25set.json"
C1Y = 0.150  # mirror of dod9a_prime.py


def off_seat(cable, clip_xy, groove_z):
    cy = cable[:, 1]
    near = int(np.argmin(np.abs(cy - clip_xy[1])))
    p = cable[near]
    z_gap = p[2] - groove_z
    lateral = float(np.linalg.norm(p[:2] - np.array(clip_xy)))
    return float(np.sqrt(lateral**2 + z_gap**2)), z_gap


def off_c2(cable):
    seat, z_gap = off_seat(cable, rc.ROUTE_C2_XY, rc.ROUTE_GROOVE_Z)
    return bool((abs(z_gap * 1e3) <= rc.C2_SETTLE_Z_TOL_MM) and ((seat * 1e3) <= (rc.C2_WALL_SEAT_TOL_MM + 0.003 * 1e3)))


def off_c1(cable):
    cy = cable[:, 1]
    nc = int(np.argmin(np.abs(cy - C1Y)))
    zc1 = cable[nc, 2]
    m = np.abs(cy - C1Y) <= rc.C1_FLANK_WINDOW_M
    flank = float(cable[m, 2].max()) if m.any() else float("nan")
    return bool(zc1 < rc.C1_RETAINED_LOW_WALL_TOP_M and flank == flank and flank < rc.C1_RETAINED_LOW_WALL_TOP_M)


def derive():
    both = []
    for c in sorted(glob.glob(str(GOLDEN_DIR / "cell_*"))):
        npz = os.path.join(c, "route_demo_raw.npz")
        if not os.path.exists(npz):
            continue
        cable = np.load(npz, allow_pickle=True)["cable_xyz"][-1]
        if off_c2(cable) and off_c1(cable):
            both.append(os.path.basename(c).replace("cell_", ""))
    return sorted(both)


def main():
    members = derive()
    result = {
        "gateiii_25set": members,
        "count": len(members),
        "derivation": "offline mirror of dod9a_prime.py (per-cell EXACT 81/81 proven; env==offline==25)",
        "predicate_constants": {
            "ROUTE_C2_XY": list(rc.ROUTE_C2_XY),
            "ROUTE_GROOVE_Z": rc.ROUTE_GROOVE_Z,
            "C2_SETTLE_Z_TOL_MM": rc.C2_SETTLE_Z_TOL_MM,
            "C2_WALL_SEAT_TOL_MM": rc.C2_WALL_SEAT_TOL_MM,
            "C1_FLANK_WINDOW_M": rc.C1_FLANK_WINDOW_M,
            "C1_RETAINED_LOW_WALL_TOP_M": rc.C1_RETAINED_LOW_WALL_TOP_M,
            "C1Y": C1Y,
        },
        "b7_dod_condition": (
            "B7 gate-iii leg: re-derive from the then-current predicate and assert SET-EQUALITY "
            "(not count) vs this pinned membership; mismatch = loud STOP (%12 condition b, 14:26)"
        ),
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps({"count": result["count"], "x0_y0_in_set": "x0_y0" in members}, indent=1))
    print(",".join(members))
    print(f"-> {OUT}")
    assert len(members) == 25, f"expected 25 members (dod9a_prime EXACT), got {len(members)}"
    return 0


if __name__ == "__main__":
    sys.exit(main())
