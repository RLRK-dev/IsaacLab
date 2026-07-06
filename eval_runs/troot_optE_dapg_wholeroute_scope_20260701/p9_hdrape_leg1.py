#!/usr/bin/env python3
"""%9 H-drape round leg-1 (zero-GPU) — PREREG_HDRAPE_ROUND.md O-A..O-E.

Observables (all 81 cells of w0e_81rerun_snapdown_0537, incl PASS controls):
  O-A  crossing_x + crossZ at phase-11 ENTRY (R-lane y=CLIP2_Y+GHS, R-EE-nearest).
  O-B  drape-over-clip contact: near-C2 cable node (min |y|) x/z + footprint membership
       (|x-cx2|<=hw_x AND |y-cy2|<=hw_y) at clip-top z.  Tests whether HIGH height is
       literally the cable resting ON the C2 clip (R3 refutation if HIGH cells have no
       footprint/clip-top node).
  O-C  rest-surface: HIGH cluster (crossZ>=840) vs wall-top rest, LOW (<840) vs floor 829.
  O-D  producer [C2-DUAL-SETTLE] near-C2 z + SETTLED_IN_NOTCH from run.log (best-effort).
  O-E  fix-class: e1 crossing_x vs dx continuity/column; e2 consistency (crossZ HIGH/LOW
       == crossing_x vs x*, x*=midpoint(HIGH-min, LOW-max) pre-fixed procedure); e3 margin
       Delta=x*-crossing_x vs F-1a-class authority |comp|<=22mm (clip(-(1-lam)dx0,+-0.022)).

Footprint/geometry params mechanically read (pin-2): clip_parts runner :1164-1170,
CLIP1_Z task_config :225, CLIP_FLOAT_Z per-cell meta, CABLE_RADIUS :137. Echoed in header.
Lane/crossing/pin machinery == frozen parser v2.1 / dy-arc leg-1. Self-sha in header (pin-1).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701")
NEW = ROOT / "w0e_81rerun_snapdown_0537"
TASK_CFG = Path("/home/rlrk/IsaacLab/thread_isaac_lab/configs/task_config.py")
GHS = 0.044
PIN_BODY_TO_NODE = 28
C2_REGRASP_PH = 11
BAR = 840.0  # HIGH/LOW split = low-wall-top physical boundary (PREREG, banked)
VERDICTS_OK = {"SUCCESS_DUAL_LOADED_AT_88", "SUCCESS_R_GRIP_L_CAGE_AT_88"}
AUTH_MM = 22.0  # F-1a-class coord authority clip |comp|<=0.022 (runner :4262), class-scale (pin-3)

# clip_parts (runner test_newton_clip_routing.py :1164-1170), (dx,dy,dz,hx,hy,hz):
CLIP_PARTS = [(0, 0, 0.0025, 0.020, 0.015, 0.0025), (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
              (0.009, 0, 0.0125, 0.0015, 0.015, 0.0075), (-0.013, 0, 0.025, 0.002, 0.015, 0.005),
              (0.013, 0, 0.025, 0.002, 0.015, 0.005)]
HW_X = max(p[3] for p in CLIP_PARTS)  # 0.020 base-plate half-x
HW_Y = max(p[4] for p in CLIP_PARTS)  # 0.015 half-y
WALL_TOP_LOW = CLIP_PARTS[1][2] + CLIP_PARTS[1][5]   # 0.020 above cz
WALL_TOP_HIGH = CLIP_PARTS[3][2] + CLIP_PARTS[3][5]  # 0.030 above cz
FLOOR_TOP = CLIP_PARTS[0][2] + CLIP_PARTS[0][5]       # 0.005 above cz


def cfg_val(name):
    m = re.search(rf"^{name}\s*=\s*([A-Za-z0-9_.]+)", TASK_CFG.read_text(), re.M)
    return m.group(1) if m else None


def off_of(name):
    m = re.search(r"x(-?\d+(?:\.\d+)?)_y(p?-?\d+(?:\.\d+)?)", name)
    return (float(m.group(1)), float(m.group(2).replace("p", ""))) if m else None


def meta_gates(cell):
    try:
        return json.loads((cell / "route_demo_raw_meta.json").read_text()).get("env_gates", {})
    except Exception:
        return {}


def crossing_at(cab, lane, eex):
    """R-lane crossing nearest R-EE-x -> (x, z_mm) or None. == v2.1 definition."""
    best = None
    for i in range(len(cab) - 1):
        y0, y1 = cab[i, 1], cab[i + 1, 1]
        if (y0 - lane) * (y1 - lane) <= 0 and abs(y1 - y0) > 1e-9:
            f = (lane - y0) / (y1 - y0)
            p = cab[i] * (1 - f) + cab[i + 1] * f
            if best is None or abs(p[0] - eex) < abs(best[0] - eex):
                best = (float(p[0]), float(p[2]) * 1e3)
    return best


def parse_cell(cell, cz):
    pin_j = json.loads((cell / "route_c2_pin.json").read_text())
    mt = pin_j.get("route_c2_metrics", {})
    v = str(pin_j.get("route_c2_regrasp", {}).get("regrasp_verdict", ""))
    zc1 = mt.get("z_c1_final_mm")
    eg = meta_gates(cell)
    c2y = float(eg.get("CLIP2_Y") or 0.0)
    cx2 = float(eg.get("CLIP2_X") or 0.40)
    lane = c2y + GHS
    with np.load(cell / "route_demo_raw.npz", mmap_mode="r") as z:
        ph = np.array(z["phase_id"])
        w = np.where(ph == C2_REGRASP_PH)[0]
        t_entry = int(w[0])
        cab_e = np.array(z["cable_xyz"][t_entry])
        eex_e = float(np.array(z["ee_pos_r"][t_entry])[0])
    cr = crossing_at(cab_e, lane, eex_e)
    # O-B: near-C2 cable node (min |y - c2y|) + footprint membership at clip-top z
    dy_arr = np.abs(cab_e[:, 1] - c2y)
    jn = int(np.argmin(dy_arr))
    nc = cab_e[jn]
    in_fp = (abs(nc[0] - cx2) <= HW_X) and (abs(nc[1] - c2y) <= HW_Y)
    # any node inside footprint (x,y), report its max z (highest draped point over clip)
    fp_mask = (np.abs(cab_e[:, 0] - cx2) <= HW_X) & (np.abs(cab_e[:, 1] - c2y) <= HW_Y)
    fp_zmax = float(cab_e[fp_mask, 2].max()) * 1e3 if fp_mask.any() else None
    s2 = (v in VERDICTS_OK) and (mt.get("c2_seated_honest") is True) and \
         (zc1 is not None and zc1 < 840.0)
    return dict(off=off_of(cell.name), verdict=v, s2=s2, cz=cz,
                crossX=round(cr[0], 4) if cr else None,
                crossZ=round(cr[1], 1) if cr else None,
                nearC2_x=round(float(nc[0]), 4), nearC2_y=round(float(nc[1]), 4),
                nearC2_z=round(float(nc[2]) * 1e3, 1), nc_in_fp=in_fp,
                fp_nodes=int(fp_mask.sum()), fp_zmax=round(fp_zmax, 1) if fp_zmax else None)


def o_d(cell):
    for lg in list(cell.glob("*.log")) + list(cell.parent.glob("*.log")):
        for ln in lg.read_text(errors="replace").splitlines():
            if "[C2-DUAL-SETTLE]" in ln:
                zm = re.search(r"near-C2 cable z=([\d.]+)", ln)
                sm = re.search(r"SETTLED_IN_NOTCH=(\w+)", ln)
                return (float(zm.group(1)) if zm else None, sm.group(1) if sm else None)
    return (None, None)


def main():
    self_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    clip1z = cfg_val("CLIP1_Z"); tableh = cfg_val("TABLE_HEIGHT")
    clip1z_v = 0.80  # CLIP1_Z = TABLE_HEIGHT = 0.80 (task_config :225 / :grep)
    # CLIP_FLOAT_Z per-cell from meta (constant expected); read from x0_y0
    cfz = float(meta_gates(NEW / "cell_x0_y0").get("CLIP_FLOAT_Z") or 0.0)
    cz = clip1z_v + cfz
    print(f"== %9 H-drape leg-1 (zero-GPU) — script sha {self_sha} (pin-1) ==")
    print(f"[GEOM pin-2] CLIP1_Z={clip1z}({clip1z_v}) TABLE_HEIGHT={tableh} CLIP_FLOAT_Z(meta)={cfz} "
          f"-> cz={cz:.3f}")
    print(f"[GEOM pin-2] footprint hw_x={HW_X} hw_y={HW_Y} (clip_parts :1164-1170) | "
          f"tops: floor={cz+FLOOR_TOP:.3f} lowW={cz+WALL_TOP_LOW:.3f} highW={cz+WALL_TOP_HIGH:.3f} "
          f"| rest(+r0.004): floor={1e3*(cz+FLOOR_TOP+0.004):.1f} lowW={1e3*(cz+WALL_TOP_LOW+0.004):.1f} "
          f"highW={1e3*(cz+WALL_TOP_HIGH+0.004):.1f}mm")
    print(f"[AUTH pin-3] F-1a-class scale = |comp|<={AUTH_MM}mm (runner :4262, class-borrow only; "
          f"C2-drape Stage-B needs NEW site authority)")
    recs = []
    for c in sorted(NEW.glob("cell_*")):
        if off_of(c.name) is None:
            continue
        r = parse_cell(c, cz)
        r["dz"], r["settled"] = o_d(c)
        recs.append(r)
    print(f"\ncells={len(recs)} (expect 81)")
    # classify
    for r in recs:
        r["hi"] = (r["crossZ"] is not None and r["crossZ"] >= BAR)
        r["phi10"] = r["off"][1] in (-20.0, -5.0, 10.0)
    hi = [r for r in recs if r["hi"]]
    lo = [r for r in recs if not r["hi"] and r["crossZ"] is not None]
    # O-E e2: x* = midpoint(HIGH-min crossX, LOW-max crossX)
    hx = [r["crossX"] for r in hi if r["crossX"] is not None]
    lx = [r["crossX"] for r in lo if r["crossX"] is not None]
    xstar = (min(hx) + max(lx)) / 2 if hx and lx else None
    print("\n-- O-A/O-B/O-C per cell (phi10 marked *) --")
    print(f"{'off':>14s} {'φ':>3s} {'verdict':<24s} s2 {'crX':>6s} {'crZ':>6s} HI "
          f"{'nearC2(x,y,z)':>22s} fp {'fpZmax':>7s} {'settleZ':>7s}")
    for r in sorted(recs, key=lambda r: (r['off'][1], r['off'][0])):
        star = "*" if r["phi10"] else " "
        nc = f"({r['nearC2_x']},{r['nearC2_y']},{r['nearC2_z']})"
        print(f"{str(r['off']):>14s} {star:>3s} {r['verdict'][:24]:<24s} {'T' if r['s2'] else '.'} "
              f"{r['crossX']!s:>6s} {r['crossZ']!s:>6s} {'H' if r['hi'] else 'L'} {nc:>22s} "
              f"{'Y' if r['nc_in_fp'] else '.'}{r['fp_nodes']:>1d} {r['fp_zmax']!s:>7s} {r['dz']!s:>7s}")
    # O-C
    print("\n-- O-C rest-surface --")
    hz = [r["crossZ"] for r in hi if r["crossZ"] is not None]
    loz = [r["crossZ"] for r in lo if r["crossZ"] is not None]
    if hz:
        print(f"HIGH n={len(hz)} crossZ [{min(hz)},{max(hz)}] mean {sum(hz)/len(hz):.1f} "
              f"| lowW-rest {1e3*(cz+WALL_TOP_LOW+0.004):.1f} highW-rest {1e3*(cz+WALL_TOP_HIGH+0.004):.1f}")
    if loz:
        print(f"LOW  n={len(loz)} crossZ [{min(loz)},{max(loz)}] mean {sum(loz)/len(loz):.1f} "
              f"| floor-rest {1e3*(cz+FLOOR_TOP+0.004):.1f}")
    # O-B / R3 summary
    hi_fp = sum(1 for r in hi if r["nc_in_fp"] or (r["fp_zmax"] and r["fp_zmax"] >= 1e3*(cz+WALL_TOP_LOW)))
    print(f"\n-- O-B/R3: HIGH cells with a footprint node at/above low-wall-top: {hi_fp}/{len(hi)} "
          f"(R3 refute if ~0 = height NOT from resting ON clip) --")
    # O-E e1 continuity: crossX vs dx per dy column
    print("\n-- O-E e1 continuity (crossX vs dx, per dy column; monotone? jump?) --")
    cols = {}
    for r in recs:
        cols.setdefault(r["off"][1], []).append((r["off"][0], r["crossX"]))
    for dy in sorted(cols):
        seq = [x for _, x in sorted(cols[dy]) if x is not None]
        dfs = [round(seq[i+1]-seq[i], 4) for i in range(len(seq)-1)]
        mono = all(d >= -1e-4 for d in dfs) or all(d <= 1e-4 for d in dfs)
        jump = max((abs(d) for d in dfs), default=0)
        print(f"  dy={dy:+5.0f}: crossX {[round(s,3) for s in seq]}  mono={mono} maxjump={jump:.3f}")
    # O-E e2 consistency
    print(f"\n-- O-E e2 consistency (x*={xstar}) --")
    if xstar is not None:
        viol = [r for r in recs if r["crossX"] is not None
                and ((r["crossX"] >= xstar) != r["hi"])]
        print(f"  x* = midpoint(HIGH-min {min(hx):.4f}, LOW-max {max(lx):.4f}) = {xstar:.4f}")
        print(f"  consistency violations (crossX>=x* XOR HIGH): {len(viol)}/{len(recs)}"
              + (" -> R1 REFUTE" if viol else " -> consistency HOLDS"))
        for r in viol:
            print(f"    {r['off']} crossX={r['crossX']} crossZ={r['crossZ']} HI={r['hi']}")
    # O-E e3 margin (LOW-fail cells)
    print("\n-- O-E e3 reachability (LOW-fail cells: Delta=x*-crossX vs authority) --")
    if xstar is not None:
        lf = [r for r in recs if not r["hi"] and not r["s2"] and r["crossX"] is not None]
        within = [r for r in lf if (xstar - r["crossX"]) * 1e3 <= AUTH_MM]
        over = [r for r in lf if (xstar - r["crossX"]) * 1e3 > AUTH_MM]
        print(f"  LOW-fail n={len(lf)} | within {AUTH_MM}mm: {len(within)} | over: {len(over)}")
        for tag, s in (("WITHIN", within), ("OVER", over)):
            for r in sorted(s, key=lambda r: r["off"]):
                print(f"    {tag:>6s} {str(r['off']):>14s} crossX={r['crossX']} "
                      f"Delta={(xstar-r['crossX'])*1e3:+.1f}mm verdict={r['verdict'][:20]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
