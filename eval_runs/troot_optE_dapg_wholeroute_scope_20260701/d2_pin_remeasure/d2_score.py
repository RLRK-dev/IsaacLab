# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(d2) scorer -- runs the POSITIVE CONTROL in the same process as the scoring, and persists both.

WHY THIS FILE EXISTS. Until now the (d2) instrument was validated by ad-hoc scripts typed into a session: the
numbers were real, but they lived in chat messages, not on disk. That is not a control. It cannot be re-run, it
cannot be sha-pinned, and it asks the reader to take the instrument's liveness on trust -- which is exactly the
failure this whole arc has been about ("the evidence exists only in narrative"). I was policing that in other
people's work while doing it in my own.

So: every scored run re-proves its own instrument, in-process, and FAILS LOUD if the instrument is dead. The
positive control is the ungrasped cable at t=0, lying ~50mm off the groove. The env's shipped ``c1_retained``
calls that PASS (it reads only Z), which is precisely how a dead instrument looks.

Scoring (never uses c1_retained / _seat_metrics / c1_seat -- see d2_metrics for why):
  * did the pin FIRE            -> the witness from route_executor.activate_c1_pin (every failure raises)
  * did the WELD hold           -> weld_hold_mm (no groove convention, no quantization)
  * did the CABLE ESCAPE        -> centerline offset, BOTH axes (X across the walls, Z straight up and out),
                                   with the welded segment EXCLUDED (a welded body is held by definition).
                                   ⛔ THIS DOES NOT ESTABLISH GROOVE CAPTURE -- see below.
  * is the instrument ALIVE     -> the t=0 positive control, asserted here, recorded in the JSON

⛔⛔ NO NUMERIC METRIC CAN ESTABLISH GROOVE CAPTURE. This was PROVEN and banked on 2026-07-12, by the very
author of the design spec: "EVERY numeric metric ... reads pass/retained, yet Rs-GT = OFF C1. therefore no
current numeric metric covers lateral groove-CAPTURE; the honest-looking ones false-positive on wall/adjacent
contact" (harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:107-108). DoD6 cell 2037 is the standing
counterexample: |dx| = 0.99mm and dz = -0.21mm -- a textbook "seated" reading -- and Rs's eyes said OFF C1.
That is the same |dx|+dz instrument used here. So these fields are named for what they CAN support: the cable
did not ESCAPE (a far-field question: 50mm vs 0.5mm is not ambiguous). Whether it is CAPTURED in the groove is
a near-field question that this instrument provably cannot answer, and only Rs's video can.

⛔ NUMERIC NEVER YIELDS A PASS ON ITS OWN. A verdict that would falsify FORK-1 is not acted on until Rs's video
human-GT: a weld overrides physics, so it can turn bad physics into good numbers (it may have HIDDEN the failure
by rigidifying the chain rather than fixing it, which only video can tell).

Usage: d2_score.py <cable_xyz.npz|route_demo_raw.npz> --arm A|B|C [--onset N] --out result.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d2_metrics as m  # noqa: E402


def score(cable_xyz, onset, arm, artifact_sha, clip_y=0.150):
    """Score one arm. Raises if the instrument itself is dead -- a dead instrument passes everything."""
    alive = m.instrument_alive(cable_xyz, clip_y)
    if not alive["alive"]:
        raise RuntimeError(
            f"INSTRUMENT DEAD: the t=0 positive control reads |dx| = {alive['t0_dx_mm']}mm, outside "
            f"{alive['band_mm']}mm. At t=0 the cable lies ungrasped on the table ~50mm off the groove; an "
            "instrument that cannot see that cannot see anything, and would score this run as PASS regardless "
            "of what the pin did. Refusing to score. (This is how the env's own c1_retained fails: it reads "
            "only Z, so it calls the ungrasped cable RETAINED.)"
        )
    dx_all, zg_all = m.centerline_offset_mm(cable_xyz, clip_y)
    dx_ex, zg_ex = m.weld_excluded_offset_mm(cable_xyz, clip_y)
    return {
        "arm": arm,
        "artifact_sha256_12": artifact_sha,
        "onset_frame": int(onset),
        "instrument_positive_control": alive,  # persisted, per run, per %10/%12
        "weld_hold": m._axis_verdict(m.weld_hold_mm(cable_xyz, onset), onset, m.P1_BOUND_MM),
        "cable_NOT_ESCAPED_all": m.p1_verdict(dx_all, zg_all, onset),
        "cable_NOT_ESCAPED_weld_excluded": m.p1_verdict(dx_ex, zg_ex, onset),
        "articulation": m.articulation(cable_xyz),  # input to the VIDEO judgment, never a verdict
        "confounded_telemetry_node3d_mm": {
            "median": round(float(np.median(m.seat_distance_mm(cable_xyz)[onset:])), 3),
            "note": "the broken instrument, recorded beside the correct one so the divergence is evidence",
        },
        "verdict_note": (
            "NUMERIC ONLY. A verdict that falsifies FORK-1 is NOT acted on before Rs's video human-GT: a weld "
            "overrides physics and can hide a failure by rigidifying the chain rather than fixing it."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz")
    ap.add_argument("--arm", required=True, choices=["A", "Aprime", "B", "C"])
    ap.add_argument("--onset", type=int, default=None)
    ap.add_argument("--clip-y", type=float, default=0.150)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    p = Path(a.npz)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    z = np.load(p, allow_pickle=True)
    xyz = np.asarray(z["cable_xyz"])
    onset = a.onset
    if onset is None:
        pin = np.asarray(z["pin_active"]).ravel() if "pin_active" in z else None
        nz = np.nonzero(pin > 0)[0] if pin is not None else np.array([], dtype=int)
        if nz.size == 0:
            raise SystemExit("no --onset given and the artifact carries no pin_active to derive it from")
        onset = int(nz[0])

    res = score(xyz, onset, a.arm, sha, a.clip_y)
    out = Path(a.out) if a.out else p.parent / f"d2_score_{a.arm}.json"
    out.write_text(json.dumps(res, indent=1))
    pc = res["instrument_positive_control"]
    print(f"[d2] arm {a.arm}  artifact {sha}  onset {onset}")
    print(f"[d2] instrument positive control: t=0 |dx| = {pc['t0_dx_mm']}mm in {pc['band_mm']} -> ALIVE")
    print(f"[d2] weld held            : {res['weld_hold']['ok']}  (max {res['weld_hold']['max_mm']}mm)")
    for k in ("cable_NOT_ESCAPED_all", "cable_NOT_ESCAPED_weld_excluded"):
        v = res[k]
        print(
            f"[d2] {k:30s}: held={v['held']}  X(max {v['x']['max_mm']}mm, slope {v['x']['slope_mm_per_kframe']})"
            f"  Z(max {v['z']['max_mm']}mm, slope {v['z']['slope_mm_per_kframe']})"
        )
    print(f"[d2] -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
