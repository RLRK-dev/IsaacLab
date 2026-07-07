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
    rec = {k: z[k] for k in ("ee_pos_r", "ee_pos_l", "grip_cmd", "phase_id")}
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


def main():
    print("=" * 78)
    print("route-executor recorded_replay step_target gate-ii byte-consistency (comp2 Stage-A gate-ii)")
    print("=" * 78)
    r = test_step_target_byte_consistent()
    print("-" * 78)
    if r is None:
        print("gate-ii: SKIP (reference recording absent)")
        return 0
    print(f"gate-ii step_target == run_route recording (== BC/trainer base): {'PASS' if r else 'FAIL'}")
    return 0 if r else 1


if __name__ == "__main__":
    sys.exit(main())
