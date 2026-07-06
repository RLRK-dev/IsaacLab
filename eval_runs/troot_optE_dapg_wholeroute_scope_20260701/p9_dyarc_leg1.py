#!/usr/bin/env python3
"""%9 leg-1 (zero-GPU) — PREREG_DYARC_STAGEA.md O1/O2/O3 mechanical computation.

O1: slack budget at R-close on the 27 phi10-column cells of w0e_81rerun_snapdown_0537:
    arc_len(pin node -> lane-crossing point, path integral along cable) minus
    chord |xyz_pin - xyz_cross|. Validity leg: arc >= chord (negative slack =
    path-assumption breakdown -> H-capture elevation flag). Separation test:
    HIGH group (dx<=-15, 6 cells) vs LOW group (dx>=-10, 21 cells); s* = midpoint
    of the inter-group gap IF separated (procedure pre-fixed in PREREG).
O2: crossing Z at phase-11 entry frame (pre-grasp) per cell.
O3: as-executed extraction from band probes P-2'/P-3'/P-6' (0511_* dirs):
    [W0E-F1B] log line + settle prints + L-EE position at ph11-entry and R-close.

Lane/crossing/pin machinery is IDENTICAL to frozen parser v2.1 (sha 170de62e...)
so O1/O2 rows are comparable to banked diag columns. Script self-sha printed in
header per countersign pin-1.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701")
NEW = ROOT / "w0e_81rerun_snapdown_0537"
PROBES = [("P-2'", ROOT / "w0e_f1b_150mm_rederive/0511_P2_x0_ym5"),
          ("P-3'", ROOT / "w0e_f1b_150mm_rederive/0511_P3_x5_yp10"),
          ("P-6'", ROOT / "w0e_f1b_150mm_rederive/0511_P6_x20_ym20")]
GHS = 0.044
PIN_BODY_TO_NODE = 28
C2_REGRASP_PH = 11
PHI10_DY = {-20.0, -5.0, 10.0}
BAR = 840.0


def lane_of(cell_dir):
    try:
        meta = json.loads((cell_dir / "route_demo_raw_meta.json").read_text())
        c2y = float(meta.get("env_gates", {}).get("CLIP2_Y") or 0.075)
    except Exception:
        c2y = 0.075
    return c2y + GHS


def crossings(cab, lane):
    """All lane crossings: list of (seg_i, frac, point)."""
    out = []
    for i in range(len(cab) - 1):
        y0, y1 = cab[i, 1], cab[i + 1, 1]
        if (y0 - lane) * (y1 - lane) <= 0 and abs(y1 - y0) > 1e-9:
            f = (lane - y0) / (y1 - y0)
            out.append((i, float(f), cab[i] * (1 - f) + cab[i + 1] * f))
    return out


def pick(crs, eex):
    best = None
    for i, f, p in crs:
        if best is None or abs(p[0] - eex) < abs(best[2][0] - eex):
            best = (i, f, p)
    return best


def arc_chord(cab, pn, seg, f, p):
    """Path length along cable from node pn to crossing point p (between seg, seg+1)."""
    d = np.linalg.norm(np.diff(cab, axis=0), axis=1)  # d[k] = |node k+1 - node k|
    if pn >= seg + 1:
        arc = (1.0 - f) * d[seg] + d[seg + 1: pn].sum()
    else:
        arc = f * d[seg] + d[pn: seg].sum()
    chord = float(np.linalg.norm(cab[pn] - p))
    return float(arc), chord


def cell_row(cell_dir):
    pin_j = json.loads((cell_dir / "route_c2_pin.json").read_text())
    pb = pin_j.get("route_c2_freeze_scope", {}).get("pin_body")
    pn = int(pb) - PIN_BODY_TO_NODE if pb is not None else None
    v = str(pin_j.get("route_c2_regrasp", {}).get("regrasp_verdict", ""))
    lane = lane_of(cell_dir)
    with np.load(cell_dir / "route_demo_raw.npz", mmap_mode="r") as z:
        ph = np.array(z["phase_id"])
        w = np.where(ph == C2_REGRASP_PH)[0]
        g = np.array(z["grip_cmd"][w[0]: w[-1] + 1, 1])
        tr = np.where(g[1:] != g[:-1])[0]
        t_close = int(w[0] + tr[-1] + 1) if len(tr) else int(w[-1])
        t_entry = int(w[0])
        cab_c = np.array(z["cable_xyz"][t_close])
        cab_e = np.array(z["cable_xyz"][t_entry])
        eex_c = float(np.array(z["ee_pos_r"][t_close])[0])
        eex_e = float(np.array(z["ee_pos_r"][t_entry])[0])
    crs_c = crossings(cab_c, lane)
    crs_e = crossings(cab_e, lane)
    row = dict(cell=cell_dir.name, verdict=v, pin=pn, n_cross_close=len(crs_c),
               n_cross_entry=len(crs_e))
    b = pick(crs_c, eex_c)
    if b and pn is not None:
        seg, f, p = b
        arc, chord = arc_chord(cab_c, pn, seg, f, p)
        row.update(seg=seg, crossZ_close=round(float(p[2]) * 1e3, 1),
                   arc_mm=round(arc * 1e3, 1), chord_mm=round(chord * 1e3, 1),
                   slack_mm=round((arc - chord) * 1e3, 1), valid=arc >= chord)
    be = pick(crs_e, eex_e)
    if be:
        row["crossZ_entry"] = round(float(be[2][2]) * 1e3, 1)
    return row


def off_of(name):
    import re
    m = re.search(r"x(-?\d+(?:\.\d+)?)_y(p?-?\d+(?:\.\d+)?)", name)
    return (float(m.group(1)), float(m.group(2).replace("p", ""))) if m else None


def o3_probe(tag, pd):
    cells = list(pd.glob("cell_*")) or [pd]
    c = cells[0]
    lines = []
    for lg in list(pd.glob("*.log")) + list(c.glob("*.log")):
        for ln in lg.read_text(errors="replace").splitlines():
            if "[W0E-F1B]" in ln or "settle" in ln.lower() or "GRASP_YC" in ln:
                lines.append(ln.strip())
    npz = c / "route_demo_raw.npz"
    feed = {}
    if npz.exists():
        with np.load(npz, mmap_mode="r") as z:
            ph = np.array(z["phase_id"])
            w = np.where(ph == C2_REGRASP_PH)[0]
            g = np.array(z["grip_cmd"][w[0]: w[-1] + 1, 1])
            tr = np.where(g[1:] != g[:-1])[0]
            t_close = int(w[0] + tr[-1] + 1) if len(tr) else int(w[-1])
            for lbl, t in (("entry", int(w[0])), ("close", t_close)):
                L = np.array(z["ee_pos_l"][t])
                feed[lbl] = [round(float(x), 4) for x in L]
    return dict(tag=tag, dir=str(pd.name), log_lines=lines[:8], L_ee=feed)


def main():
    self_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(f"== %9 dy-arc leg-1 (zero-GPU) — script sha {self_sha} (pin-1) ==")
    rows = []
    for c in sorted(NEW.glob("cell_*")):
        off = off_of(c.name)
        if off is None or off[1] not in PHI10_DY:
            continue
        r = cell_row(c)
        r["off"] = off
        r["grp"] = "HIGH" if off[0] <= -15.0 else "LOW"
        rows.append(r)
    print(f"phi10-column cells = {len(rows)} (expect 27)")
    print("\n-- O1/O2 per cell (grp = expected class by dx boundary) --")
    print(f"{'off':>15s} {'grp':>4s} {'verdict':<26s} pin seg nX(c/e) "
          f"{'arc':>6s} {'chord':>6s} {'slack':>6s} vld {'czC':>6s} {'czE':>6s}")
    for r in sorted(rows, key=lambda r: (r['off'][1], r['off'][0])):
        print(f"{str(r['off']):>15s} {r['grp']:>4s} {r['verdict'][:26]:<26s} "
              f"{r.get('pin')!s:>3s} {r.get('seg')!s:>3s} "
              f"{r['n_cross_close']}/{r['n_cross_entry']}   "
              f"{r.get('arc_mm')!s:>6s} {r.get('chord_mm')!s:>6s} {r.get('slack_mm')!s:>6s} "
              f"{str(r.get('valid'))[:1]:>3s} {r.get('crossZ_close')!s:>6s} {r.get('crossZ_entry')!s:>6s}")
    # O1 separation
    inval = [r for r in rows if not r.get("valid", False)]
    hi = sorted(r["slack_mm"] for r in rows if r["grp"] == "HIGH" and r.get("valid"))
    lo = sorted(r["slack_mm"] for r in rows if r["grp"] == "LOW" and r.get("valid"))
    print("\n-- O1 separation (slack mm) --")
    print(f"HIGH (dx<=-15, n={len(hi)}): {hi}")
    print(f"LOW  (dx>=-10, n={len(lo)}): {lo}")
    if inval:
        print(f"!! O1 VALIDITY: arc<chord in {len(inval)} cells -> H-capture elevation flag:")
        for r in inval:
            print(f"   {r['off']} arc={r.get('arc_mm')} chord={r.get('chord_mm')}")
    if hi and lo:
        if max(hi) < min(lo):
            print(f"SEPARATED: HIGH max {max(hi)} < LOW min {min(lo)}; s* = {(max(hi)+min(lo))/2:.1f}mm")
        elif max(lo) < min(hi):
            print(f"SEPARATED (inverted): LOW max {max(lo)} < HIGH min {min(hi)}; s* = {(max(lo)+min(hi))/2:.1f}mm")
        else:
            print("NOT SEPARATED (overlap) — H-slack fit fails on O1")
    # O2 summary
    pre_low = sum(1 for r in rows if isinstance(r.get("crossZ_entry"), float) and r["crossZ_entry"] < BAR)
    n_e = sum(1 for r in rows if isinstance(r.get("crossZ_entry"), float))
    print(f"\n-- O2: crossZ at ph11-entry < {BAR} in {pre_low}/{n_e} cells with entry crossing --")
    print("\n== O3 as-executed (band probes) ==")
    for tag, pd in PROBES:
        d = o3_probe(tag, pd)
        print(f"{tag} ({d['dir']}): L_ee entry={d['L_ee'].get('entry')} close={d['L_ee'].get('close')}")
        for ln in d["log_lines"]:
            print(f"    {ln}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
