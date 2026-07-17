# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(d) materials: offline capture-window analysis over the 81-cell grid (charter Q1/Q2/Q5/Q6 inputs).

Computes, per cell, from the RECORDING alone (no env build -- cable_xyz is the physics ground truth
the reward instruments read):
  fork (B) recording-derived identity: the recorded pin seat's capture-predicate truth timeline vs C1
    -> first-True frame ("geometric fire, B") vs the recorded onset -> how much EARLIER a live
    geometric trigger would fire (charter sec 3 predicted ~11 RL steps on canonical).
  fork (A) fired-body identity: the predicate over ALL 40 bodies -> which body captures FIRST, and
    whether it equals the recorded seat (a mismatch means fork A binds identity to a DIFFERENT
    segment than fork B -- the decisive Q2 discriminator).
  pin-before-release: geometric fire vs the grip-release frame (D-6: the producer opens at
    onset+54); the (d) trigger must fire while the gripper still holds (charter sec 2-2).
  margins at fire (artifact (i) seed): |dx| lateral / |dy| domain / z distance to the volume bars.

The predicate is re-expressed vectorized (two <= legs + one strict < leg, route_executor.py:903-911);
a positive control asserts scalar/vector agreement against route_executor.clip_capture_predicate on
sampled frames. y_win = 0.015 (the model-derived, N1-N7-validated C1 bar recorded in
authorize_clip_pin_controls_result.json; the live path derives it from geom_size each call).

Run:
    /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_d_capture_window_analysis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import route_env_config as rc  # noqa: E402
import route_executor as rex  # noqa: E402

GRID = _EVAL / "w0e_81rerun_snapdown_0537"
OUT = _EVAL / "pin_d_capture_window_analysis_result.json"
C1X, C1Y = rc.ROUTE_CLIP_CENTERS[0]
LAT, YWIN, ZLO, ZHI = rc.SEAT_LAT_BAR_M, 0.015, rc.SEAT_Z_LO_M, rc.SEAT_Z_HI_M
GRIP_OPEN_BAR = 0.5  # closed = 0.7407 both (D-6, 81/81); open commands are 0.040/0.006


def captured_mask(xyz: np.ndarray) -> np.ndarray:
    """Vectorized clip_capture_predicate vs C1 over [..., 3] points (semantics of :903-911)."""
    dx = np.abs(xyz[..., 0] - C1X)
    dy = np.abs(xyz[..., 1] - C1Y)
    z = xyz[..., 2]
    return (dx <= LAT) & (dy <= YWIN) & (z > ZLO) & (z < ZHI)


def main() -> int:
    # positive control: vectorized == scalar on a probe set spanning all four outcomes.
    probes = [
        (C1X, C1Y, 0.829),  # captured
        (C1X + 0.0036, C1Y, 0.829),  # lateral reject (just over 3.5mm)
        (C1X, C1Y + 0.016, 0.829),  # domain reject
        (C1X, C1Y, 0.8809),  # height reject (aerial, controls leg B)
        (C1X + 0.0035, C1Y + 0.015, 0.8215),  # boundary: on <= legs, inside strict z
        (C1X, C1Y, 0.821),  # boundary: z == z_lo -> reject (strict)
    ]
    for p in probes:
        want, _ = rex.clip_capture_predicate(p, C1X, C1Y, LAT, YWIN, ZLO, ZHI)
        got = bool(captured_mask(np.asarray(p, dtype=np.float64)))
        assert got == want, f"vectorized predicate diverges from route_executor at {p}: {got} != {want}"

    cells = sorted(GRID.glob("cell_*"))
    per_cell, agg = {}, {
        "onset_minus_geoB_frames": [],
        "A_first_seg_equals_B_seat": 0,
        "A_first_seg_mismatch": [],
        "fire_before_release_B": 0,
        "cells": 0,
    }
    for cell in cells:
        z = np.load(str(cell / "route_demo_raw.npz"), allow_pickle=True)
        cable = np.asarray(z["cable_xyz"], dtype=np.float64)  # [F, 40, 3]
        pin = np.asarray(z["pin_active"]).ravel()
        grip = np.asarray(z["grip_cmd"], dtype=np.float64)  # [F, 2] cols [L, R]
        on = np.nonzero(pin > 0)[0]
        onset = int(on[0])
        seat_b = int(np.unique(np.asarray(z["pin_eqid"]).ravel()[pin > 0])[0])  # fork B identity

        cap_all = captured_mask(cable)  # [F, 40]
        # fork B: recorded seat's own timeline
        b_true = np.nonzero(cap_all[:, seat_b])[0]
        geo_b = int(b_true[0]) if b_true.size else None
        # fork A: first (frame, body) capture
        any_true = np.nonzero(cap_all.any(axis=1))[0]
        geo_a = int(any_true[0]) if any_true.size else None
        a_first_segs = np.nonzero(cap_all[geo_a])[0].tolist() if geo_a is not None else []
        # release: first frame at/after onset where either channel leaves the closed band
        rel = np.nonzero(grip[onset:].min(axis=1) < GRIP_OPEN_BAR)[0]
        release = int(onset + rel[0]) if rel.size else None
        # margins at the B geometric fire
        m = cable[geo_b, seat_b] if geo_b is not None else None
        margins = (
            {
                "dx_mm": round(abs(float(m[0]) - C1X) * 1e3, 3),
                "dy_mm": round(abs(float(m[1]) - C1Y) * 1e3, 3),
                "z_mm": round(float(m[2]) * 1e3, 2),
            }
            if m is not None
            else None
        )
        row = {
            "onset": onset,
            "seat_seg_B": seat_b,
            "geo_fire_B": geo_b,
            "onset_minus_geoB": (onset - geo_b) if geo_b is not None else None,
            "geo_fire_A": geo_a,
            "A_first_segs": a_first_segs,
            "A_matches_B": bool(geo_a is not None and a_first_segs == [seat_b]),
            "release_frame": release,
            "fire_before_release_B": bool(geo_b is not None and release is not None and geo_b < release),
            "margins_at_geoB": margins,
        }
        per_cell[cell.name] = row
        agg["cells"] += 1
        if row["onset_minus_geoB"] is not None:
            agg["onset_minus_geoB_frames"].append(row["onset_minus_geoB"])
        if row["A_matches_B"]:
            agg["A_first_seg_equals_B_seat"] += 1
        else:
            agg["A_first_seg_mismatch"].append({cell.name: {"A": a_first_segs, "B": seat_b}})
        agg["fire_before_release_B"] += int(row["fire_before_release_B"])

    d = np.asarray(agg["onset_minus_geoB_frames"], dtype=np.int64)
    summary = {
        "bars": {"C1": [C1X, C1Y], "lat_m": LAT, "y_win_m": YWIN, "z_lo_m": ZLO, "z_hi_m": ZHI,
                 "y_win_source": "model-derived C1 bar, N1-N7 validated (controls result json)"},
        "cells": agg["cells"],
        "onset_minus_geoB_frames": {
            "min": int(d.min()), "p50": float(np.percentile(d, 50)),
            "p90": float(np.percentile(d, 90)), "max": int(d.max()),
            "rl_steps_at_10phys": {"min": round(int(d.min()) / 10, 1), "max": round(int(d.max()) / 10, 1)},
        },
        "fork_A_first_capture_equals_B_seat": f"{agg['A_first_seg_equals_B_seat']}/{agg['cells']}",
        "fork_A_mismatches": agg["A_first_seg_mismatch"],
        "fire_before_release_B": f"{agg['fire_before_release_B']}/{agg['cells']}",
    }
    OUT.write_text(json.dumps({"summary": summary, "per_cell": per_cell}, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
