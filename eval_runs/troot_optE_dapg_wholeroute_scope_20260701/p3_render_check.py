#!/usr/bin/env python3
"""P3 render r-v1 determinism guard (W0-d J6, %12 rider 13:48).

For each rendered cell, compare the --record-video RE-RUN's route_c2_pin.json against the
ORIGINAL grid run's, on the 3 guard values (verdict / c2_seated_honest / cable_z_at_c2_mm).
A match => the re-run reproduces the grid trajectory (render is drawing the verified evidence).
A MISMATCH => deterministic-premise falsification => EXCLUDE that cell from render judgment +
report immediately (itself an important finding). Render != verdict (seat call = %12+%9).
0-commit (result dir).
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__)) + "/p3_grid"
CELLS = ["x0_y10", "x5_y20", "x15_y5", "x0_y-20", "x-15_y15", "x-20_y-15", "x-20_y5"]


def _read(p):
    if not os.path.isfile(p):
        return None
    j = json.load(open(p))
    m = j.get("route_c2_metrics", {})
    return {
        "verdict": m.get("c2_regrasp_verdict"),
        "seated_honest": m.get("c2_seated_honest"),
        "z_at_c2": m.get("cable_z_at_c2_mm"),
        "finite": j.get("finite"),
    }


def main():
    cells = sys.argv[1:] or CELLS
    print(f"{'cell':>10}  {'guard(verdict/seated/z_at_c2)':^46}  match?")
    print("-" * 74)
    allok = True
    for tag in cells:
        g = _read(os.path.join(BASE, f"cell_{tag}", "route_c2_pin.json"))          # grid original
        r = _read(os.path.join(BASE, f"render_{tag}", "route_c2_pin.json"))         # render re-run
        if g is None or r is None:
            print(f"{tag:>10}  grid={'MISSING' if g is None else 'ok'} render={'MISSING' if r is None else 'ok'}  -> PENDING")
            allok = False
            continue
        # z compared at 0.1mm; verdict + seated_honest exact
        zmatch = (g["z_at_c2"] is not None and r["z_at_c2"] is not None
                  and abs(float(g["z_at_c2"]) - float(r["z_at_c2"])) <= 0.1)
        ok = (g["verdict"] == r["verdict"]) and (g["seated_honest"] == r["seated_honest"]) and zmatch
        allok = allok and ok
        tag_v = "MATCH" if ok else "!! MISMATCH -> EXCLUDE + report"
        print(f"{tag:>10}  grid: {g['verdict']}/{g['seated_honest']}/{g['z_at_c2']}")
        print(f"{'':>10}  rerun:{r['verdict']}/{r['seated_honest']}/{r['z_at_c2']}  -> {tag_v}")
    print("-" * 74)
    print(f"r-v1 guard: {'ALL MATCH (re-run reproduces grid evidence)' if allok else 'MISMATCH/PENDING present -> see above'}")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
