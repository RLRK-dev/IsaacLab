# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Gate-2 rerun probe v2: PER-FRAME extrema (leg-3 Issue 5 correction of the cadence-10 v1 evidence).

v1 (gate2_rerun_fm34_probe.py, preserved) sampled at stride 10 from pin onset, which (a) conflated
"first seated" with "first seated post-onset" -- the seat is already true BEFORE the pin fires -- and
(b) understated the C2 lateral extremum ~1.6x. This v2 scans every frame from 0.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TIL = _HERE.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL / "envs"), str(_TIL)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import newton_route_env as nre  # noqa: E402

GOLDEN = _HERE / "w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz"


def main():
    d = np.load(GOLDEN)
    cable = d["cable_xyz"].astype(np.float64)
    pin_active = d["pin_active"].astype(int)
    n = cable.shape[0]
    onset = int(np.argmax(pin_active == 1))

    env = object.__new__(nre.NewtonRouteEnv)
    env._pin_seat_seg = 27  # v1 derivation (physics-derived, stable) = recording pin identity

    c1_seated = np.zeros(n, dtype=bool)
    c2_seated = np.zeros(n, dtype=bool)
    c2_dx = np.full(n, np.nan)
    esc = np.zeros(n, dtype=bool)
    xdev = np.full(n, np.nan)
    for f in range(n):
        cp = cable[f]
        dx1, z1 = env._seat_metrics(cp, nre._C1_XY)
        c1_seated[f] = env._seated_in_groove(dx1, z1)
        dx2, z2 = env._seat_metrics(cp, nre._C2_XY)
        c2_seated[f] = env._seated_in_groove(dx2, z2)
        c2_dx[f] = dx2
        esc[f] = env._c1_escape_after_seat(cp, True)
        dev = env._crossing_x_dev(cp)
        xdev[f] = np.nan if dev is None else dev

    first_c1 = int(np.argmax(c1_seated)) if c1_seated.any() else None
    first_c2 = int(np.argmax(c2_seated)) if c2_seated.any() else None
    c2_dx_seated = c2_dx[c2_seated]
    out = {
        "ts": time.time(),
        "supersedes": "gate2_rerun_fm34_probe_result.json (v1, cadence-10 from onset; kept as lineage)",
        "n_frames": int(n),
        "pin_onset_frame": onset,
        "c1_first_seated_frame_ANY": first_c1,
        "c1_pre_onset_seated_frames": int(c1_seated[:onset].sum()),
        "c1_seated_post_onset": f"{int(c1_seated[onset:].sum())}/{n - onset}",
        "c2_first_seated_frame": first_c2,
        "c2_seated_after_first": (
            f"{int(c2_seated[first_c2:].sum())}/{n - first_c2}" if first_c2 is not None else None
        ),
        "c2_max_dx_mm_while_seated_PER_FRAME": (
            round(float(np.nanmax(c2_dx_seated)) * 1000, 3) if c2_dx_seated.size else None
        ),
        "fm3_false_escape_frames_post_onset_PER_FRAME": int(esc[onset:].sum()),
        "fm3_max_abs_xdev_mm_post_onset_PER_FRAME": round(float(np.nanmax(np.abs(xdev[onset:]))) * 1000, 3),
        "global_xdev_max_mm_ALL_frames_incl_pre_onset": round(float(np.nanmax(np.abs(xdev))) * 1000, 3),
        "global_xdev_note": "pre-onset the GLOBAL crossing wanders to ~50mm dev (FM3 inert pre-G3, no "
        "exposure on canonical) -- but it illustrates leg-3 Issue 3: the escape guard consumes the "
        "identity-UNRESTRICTED crossing, so near-bar global states + a mid-latch could interact; see verdict.",
        "note": "seat precedes the pin by the pre-onset window; the pin RETAINS an already-made seat "
        "(matters for the pin-lifecycle blocker, pre-check leg-3 Issue 1).",
    }
    (_HERE / "gate2_rerun_fm34_probe_v2_result.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
