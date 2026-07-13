# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""F-9 leg 3: a POSITIVE CONTROL on the seat instrument, and the |dx| bar DERIVED instead of calibrated.

F-9 (spec sec 20) reached the defect from the mechanism (the free axis dy is charged as seating error, and
its quantization floor of 7.32mm is wider than the 3mm bar) and from a 24/81 recount. This leg supplies the
two things F-9 argued without:

LEG 3a -- POSITIVE CONTROL.
    Take the cells the PRODUCER says are PHYSICALLY seated -- it measures mj_geomDistance, a continuous
    surface distance with no node quantization, weld excluded (cable_c1_nonpin_final_mm < 0, and
    c2_seated_honest). On that known-seated set, run the ENV's predicate formula verbatim. A working
    instrument fires n/n. F-9 predicts it will not, and says why.

    This tests the FORMULA, not the build: _seat_metrics is a pure function of cable node positions, so it
    can be evaluated on the recording. A different build moves the nodes but keeps the same 40-node/15mm
    discretization, so the quantization floor -- and therefore the defect -- is build-independent.

LEG 3b -- DERIVE THE BAR.
    F-9.5(1) proposed keeping |dx| <= 3.0mm and justified it as "measured max is 1.94mm, so 3mm is
    reasonable". That is calibration against the data, not derivation from the constraint -- the same move
    F-9 itself indicts. The groove geometry fixes the bound with no data at all:

        groove inner radius   6mm   (create_clip.py:48 GROOVE_INNER_D = 0.012 -> :72 groove_r = D/2)
        cable radius          4mm   (task_config.py:137 CABLE_RADIUS = 0.004)
        --------------------------
        lateral clearance   2.0mm   = the largest |dx| a seated cable can have (rigid-body bound)

    The measured max then becomes an independent CHECK on the derivation rather than its source. The CAD
    cross-section and 58 measured trajectories landing 0.06mm apart is the positive control for the fix.

    ON THE VALUE. 2.0mm is the RIGID bound; MuJoCo's soft contacts let a loaded cable press into the wall
    (the producer records wall distances down to -1.12mm), so a bar set AT 2.0mm can false-FAIL a genuinely
    seated cable. Recommendation: KEEP 3.0mm, REPLACE its justification --
        3.0mm = 2.0mm geometric clearance + 1.0mm solver-penetration allowance,
    not "T_GROOVE reuse". Same number; derived rather than borrowed; no bar is loosened.

Run:
    /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/f9_positive_control_seat_predicate.py
"""

from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

# The 81-cell golden recording is UNTRACKED (~1GB of .npz), so it lives only in the working checkout that
# produced it. Resolve it explicitly and PRINT what was resolved -- a measurement that will not say which
# artifact it read is not a measurement.
REL = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537"
FALLBACK_CHECKOUT = "/home/rlrk/IsaacLab"

# Every constant below is read from the built model / SSOT, not from this arc's narrative.
ROUTE_GROOVE_Z = 0.829  # route_env_config.py:144 -- 0.809 base + 20mm clip float
T_GROOVE = 0.003  # task_config.py:368 -- the p3/p5 bar (newton_route_env.py:1549, :1551)
C2_SETTLE_Z_TOL_MM = 3.0  # route_env_config.py:123
C2_WALL_SEAT_TOL_MM = 0.5  # route_env_config.py:124
C2_XY = np.array([0.40, 0.00])  # route_env_config.py:140 ROUTE_C2_XY
GROOVE_R_M = 0.006  # create_clip.py:48, :72 -- 12mm inner diameter -> 6mm inner radius
CABLE_R_M = 0.004  # task_config.py:137
CLEARANCE_MM = (GROOVE_R_M - CABLE_R_M) * 1e3  # 2.0mm -- derived lateral bound for a seated cable


def seat_metrics(cable_pos: np.ndarray, clip_xy: np.ndarray) -> tuple[float, float, int]:
    """VERBATIM ``newton_route_env.py:1299-1310`` -- the instrument under test.

    Args:
        cable_pos: cable node world positions [m], shape [n_node, 3], float.
        clip_xy: clip centre [m], shape [2], float.

    Returns:
        ``(seat_dist [m], z_gap [m], nearest_node_index)``.
    """
    near = int(np.argmin(np.abs(cable_pos[:, 1] - clip_xy[1])))
    p = cable_pos[near]
    z_gap = float(p[2] - ROUTE_GROOVE_Z)
    lateral = float(np.linalg.norm(p[:2] - clip_xy))  # the XY norm that mixes the fatal dx with the free dy
    seat_dist = float(np.sqrt(lateral * lateral + z_gap * z_gap))
    return seat_dist, z_gap, near


def centerline_dx_zgap(cable_pos: np.ndarray, clip_xy: np.ndarray) -> tuple[float, float]:
    """The fixed instrument: interpolate the cable polyline at ``y = clip_y``, score the CONSTRAINED axes.

    Quantization-free by construction -- it never asks which node happened to land nearest.

    Args:
        cable_pos: cable node world positions [m], shape [n_node, 3], float.
        clip_xy: clip centre [m], shape [2], float.

    Returns:
        ``(|dx| [mm], z_gap [mm])`` at the groove's own Y.
    """
    y = cable_pos[:, 1]
    i = int(np.argmin(np.abs(y - clip_xy[1])))
    j = int(np.clip(i + (1 if y[i] < clip_xy[1] else -1), 0, len(y) - 1))
    dy = y[j] - y[i]
    w = 0.0 if abs(dy) < 1e-12 else (clip_xy[1] - y[i]) / dy
    x = cable_pos[i, 0] + w * (cable_pos[j, 0] - cable_pos[i, 0])
    z = cable_pos[i, 2] + w * (cable_pos[j, 2] - cable_pos[i, 2])
    return abs(x - clip_xy[0]) * 1e3, (z - ROUTE_GROOVE_Z) * 1e3


def resolve_root(explicit: str | None = None) -> str:
    """Locate the golden recording, preferring this checkout and falling back to the one that produced it."""
    for cand in (explicit, REL, os.path.join(FALLBACK_CHECKOUT, REL)):
        if cand and glob.glob(os.path.join(cand, "cell_*", "route_demo_raw.npz")):
            return cand
    raise SystemExit(f"golden recording not found (looked for {REL}); pass --root explicitly")


def collect(root: str) -> list[dict]:
    """Evaluate both instruments on every cell's final frame, tagged by the producer's ground truth."""
    rows = []
    for cell in sorted(glob.glob(os.path.join(root, "cell_*"))):
        pin_p = os.path.join(cell, "route_c2_pin.json")
        npz_p = os.path.join(cell, "route_demo_raw.npz")
        if not (os.path.exists(pin_p) and os.path.exists(npz_p)):
            continue
        with open(pin_p) as fh:
            meta = json.load(fh)
        prod = meta.get("route_c2_metrics", {})
        # Producer ground truth: mj_geomDistance, continuous surface, weld EXCLUDED.
        gt_c1 = prod.get("cable_c1_nonpin_final_mm")
        gt_c2 = prod.get("c2_seated_honest")
        if gt_c1 is None or gt_c2 is None:
            continue
        c1_xy = np.array([meta["x_clip"], meta["y_clip"]])
        fin = np.load(npz_p)["cable_xyz"][-1].astype(np.float64)

        c1_seat, _, c1_near = seat_metrics(fin, c1_xy)
        c2_seat, c2_zgap, _ = seat_metrics(fin, C2_XY)
        c1_dx, _ = centerline_dx_zgap(fin, c1_xy)
        c2_dx, _ = centerline_dx_zgap(fin, C2_XY)

        rows.append(
            {
                "cell": os.path.basename(cell),
                "seated": bool(gt_c1 < 0 and gt_c2),
                "p3": c1_seat < T_GROOVE,  # :1549 G3 latch
                "p5": c2_seat < T_GROOVE,  # :1551 G5 latch; G6 requires G5 latched (:1569)
                "c2_honest": bool(
                    (c2_seat * 1e3) <= (C2_WALL_SEAT_TOL_MM + T_GROOVE * 1e3)  # :1318 -> a 3.5mm bar
                    and abs(c2_zgap * 1e3) <= C2_SETTLE_Z_TOL_MM
                ),
                "c1_dy": abs(fin[c1_near, 1] - c1_xy[1]) * 1e3,
                "c1_dx": c1_dx,
                "c2_dx": c2_dx,
                "c2_zgap": abs(c2_zgap * 1e3),
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None, help="path to the 81-cell golden recording")
    root = resolve_root(ap.parse_args().root)

    rows = collect(root)
    seated = [r for r in rows if r["seated"]]
    n = len(seated)
    if not n:
        raise SystemExit("no positive-control cells found -- refusing to report (the instrument would be untested)")

    print(f"golden recording: {os.path.abspath(root)}")
    print(f"cells: {len(rows)}    PRODUCER says physically seated: {n}\n")
    print(f"LEG 3a -- the ENV formula on a KNOWN-SEATED set (a working instrument fires {n}/{n}):")
    for key, label in (("p3", "p3  G3 latch  (C1)"), ("p5", "p5  G5 latch  (C2)"), ("c2_honest", "_c2_seated_honest")):
        fired = sum(r[key] for r in seated)
        print(f"    {label:22s}{fired:3d}/{n}   ({100 * fired / n:3.0f}%)")

    def stat(key: str) -> str:
        v = np.array([r[key] for r in seated], dtype=float)
        return f"med {np.median(v):5.2f}   max {v.max():5.2f}"

    print("\n  why -- decompose the distance the env charges as 'seating error':")
    print(f"    |dy|  the FREE axis, no measurand : {stat('c1_dy')}   <- dominates. floor is +-7.32mm")
    print(f"    |dx|  C1, the FATAL axis          : {stat('c1_dx')}")
    print(f"    |dx|  C2, the FATAL axis          : {stat('c2_dx')}")

    c1dx = np.array([r["c1_dx"] for r in seated], dtype=float)
    c2dx = np.array([r["c2_dx"] for r in seated], dtype=float)
    print(
        f"\nLEG 3b -- the bar, DERIVED (no data): groove_r {GROOVE_R_M * 1e3:.0f}mm"
        f" - cable_r {CABLE_R_M * 1e3:.0f}mm = {CLEARANCE_MM:.1f}mm"
    )
    print(f"    measured |dx| max            : C1 {c1dx.max():.2f}mm    C2 {c2dx.max():.2f}mm")
    print(
        f"    exceeding the derived {CLEARANCE_MM:.1f}mm  : C1 {int((c1dx > CLEARANCE_MM).sum())}/{n}"
        f"    C2 {int((c2dx > CLEARANCE_MM).sum())}/{n}"
    )
    print(f"    -> the CAD cross-section and {n} measured trajectories agree to {CLEARANCE_MM - c1dx.max():.2f}mm.")

    z = np.array([r["c2_zgap"] for r in seated], dtype=float)
    print(
        f"\n  WARN -- the SHIPPED C2 z-band (|z_gap| <= {C2_SETTLE_Z_TOL_MM}mm) has thin headroom:"
        f" golden max = {z.max():.2f}mm"
        f" = {100 * z.max() / C2_SETTLE_Z_TOL_MM:.0f}% of budget ({C2_SETTLE_Z_TOL_MM - z.max():.2f}mm spare)."
    )
    print("         The ENV is a different build and must clear the same bar. Worth a margin review.")


if __name__ == "__main__":
    main()
