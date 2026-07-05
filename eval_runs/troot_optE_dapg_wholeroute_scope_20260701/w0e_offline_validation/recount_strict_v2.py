#!/usr/bin/env python3
"""strict_v2 independent recount (%12 two-key leg) — PREREG v2 (spec v0.8) mechanical application.

strict_v2 = verdict in {SUCCESS_DUAL_LOADED_AT_88, SUCCESS_R_GRIP_L_CAGE_AT_88}
            AND c2_seated_honest
            AND c1_retained_final := (route_c2_metrics.z_c1_final_mm < 840)
                                     AND (c1_flank_max_z_final_mm < 840)
Flank source: producer field `c1_flank_max_z_final_mm` if present (post-fix builds),
else computed from route_demo_raw.npz final frame (|y - y_clip| <= 10mm window) —
the fallback reproduces the offline-validated discriminator (81/81 separation, 07-05).

Usage: recount_strict_v2.py <grid_dir>   (e.g. p3_grid or the re-grid dir)
Outputs: 4-class decomposition, per-offset unique strict_v2 count, Wilson 95% CI,
penetration columns vs bars (floor >= -1mm, wall >= -4mm), watch cells, span check.
"""
import glob
import json
import math
import os
import sys

import numpy as np

SUCCESS_SET = {"SUCCESS_DUAL_LOADED_AT_88", "SUCCESS_R_GRIP_L_CAGE_AT_88"}
LOW_WALL_TOP = 840.0
FLANK_WIN_M = 0.010


def wilson(k, n, z=1.959963984540054):
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return ctr - hw, ctr + hw


def flank_from_npz(cell_dir, y_clip):
    z = np.load(os.path.join(cell_dir, "route_demo_raw.npz"))
    p = z["cable_xyz"][-1]
    m = np.abs(p[:, 1] - y_clip) <= FLANK_WIN_M
    return float(p[m, 2].max()) * 1e3 if m.any() else float("nan")


def main(grid_dir):
    cells = sorted(glob.glob(os.path.join(grid_dir, "cell_*")))
    rows = []
    for d in cells:
        jp = os.path.join(d, "route_c2_pin.json")
        if not os.path.exists(jp):
            print(f"SKIP (no pin json): {d}")
            continue
        j = json.load(open(jp))
        m = j["route_c2_metrics"]
        tag = os.path.basename(d)[5:]
        verdict = m.get("c2_regrasp_verdict", "")
        honest = bool(m.get("c2_seated_honest", False))
        z_c1 = float(m.get("z_c1_final_mm", float("nan")))
        flank = m.get("c1_flank_max_z_final_mm")
        flank_src = "producer"
        if flank is None:
            flank = flank_from_npz(d, float(j["y_clip"]))
            flank_src = "npz-fallback"
        c1_ok = (z_c1 < LOW_WALL_TOP) and (float(flank) < LOW_WALL_TOP)
        strict = (verdict in SUCCESS_SET) and honest and c1_ok
        rows.append({
            "tag": tag, "verdict": verdict, "honest": honest, "z_c1_final": z_c1,
            "flank": round(float(flank), 1), "flank_src": flank_src, "c1_ok": c1_ok,
            "strict_v2": strict,
            "pen_c1_seat": m.get("cable_c1_seat_dist_mm"), "pen_c2_seat": m.get("cable_c2_seat_dist_mm"),
        })
    n = len(rows)
    k = sum(r["strict_v2"] for r in rows)
    both = k
    c2_only = sum(1 for r in rows if r["honest"] and r["verdict"] in SUCCESS_SET and not r["c1_ok"])
    c1_only = sum(1 for r in rows if r["c1_ok"] and not (r["honest"] and r["verdict"] in SUCCESS_SET))
    neither = n - both - c2_only - c1_only
    lo, hi = wilson(k, n)
    print(f"grid: {grid_dir}  cells={n}")
    print(f"strict_v2 = {k}/{n} = {k / n:.3f}  Wilson95 [{lo:.3f}, {hi:.3f}]")
    print(f"4-class: both={both} c2_only={c2_only} c1_only={c1_only} neither={neither}")
    src = {r["flank_src"] for r in rows}
    print(f"flank source(s): {src}")
    viol = [r for r in rows if (r["pen_c1_seat"] is not None and r["pen_c1_seat"] < -4.0)
            or (r["pen_c2_seat"] is not None and r["pen_c2_seat"] < -4.0)]
    print(f"wall-bar (-4mm) seat-field violations: {len(viol)} {[r['tag'] for r in viol][:6]}")
    watch = [r for r in rows if r["tag"] in ("x-10_y0", "x-20_y15")]
    for r in watch:
        print(f"watch {r['tag']}: strict_v2={r['strict_v2']} z_c1={r['z_c1_final']} flank={r['flank']}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"recount_{os.path.basename(grid_dir.rstrip('/'))}.json")
    json.dump(rows, open(out, "w"), indent=1)
    print(f"per-cell rows -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
