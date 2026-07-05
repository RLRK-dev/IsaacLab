#!/usr/bin/env python3
"""W0-e offline measurand validation (zero GPU) — 5体 [VERIFY] DECIDE evidence.

Validates, on the EXISTING 81 p3_grid npz recordings (cable_xyz per control step):
  A) F-1a measurand: guarded crossing dx at ROUTE_C1 end (|y-y_clip|<=7.5mm AND |x-x_clip|<=30mm)
     vs naive +-100mm-window mean (caveat-a style) vs bare Y-argmin — contamination + separation.
     [CC2-CH1/CH7, CC3-CH1]
  B) flank-z retention discriminator: max cable z within |y-y_clip|<=W at final frame, W in {7.5,10,15}mm
     — specificity on 45 retained cells (want 0 false fires) + sensitivity on 36 escapes.
     [CC3-CH2, CC5-CH1 amended strict_v2 C1 leg]
  C) F-3 measurand: guarded crossing dx at C2 entry (last C2_TRANSPORT frame) vs bare argmin (J-8c
     hijack check) + correlation with c2z_gap — adjudicates RC-3 mechanism. [CC3-CH1, CC4-CH2]
  D) C2-entry node phase (nearest-node (y-c2y) mod 15) — independent recompute of CC4-CH3 scrambling.
Output: per-cell CSV + aggregate report to stdout.
"""
import csv
import json
import os

import numpy as np

BASE = "/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p3_grid"
PH_ROUTE, PH_TRANSPORT = 4, 12  # meta phase_names order (verified cell_x-20_y-15)

rows = {}
with open(f"{BASE}/p3_grid_summary.csv") as f:
    for r in csv.DictReader(f):
        rows[r["tag"]] = r

res = []
for tag in sorted(rows):
    d = f"{BASE}/cell_{tag}"
    if not os.path.exists(f"{d}/route_demo_raw.npz"):
        print(f"MISSING npz: {tag}")
        continue
    z = np.load(f"{d}/route_demo_raw.npz")
    meta = json.load(open(f"{d}/route_demo_raw_meta.json"))
    pin = json.load(open(f"{d}/route_c2_pin.json"))["route_c2_freeze_scope"]
    assert meta["phase_names"][PH_ROUTE] == "ROUTE_C1" and meta["phase_names"][PH_TRANSPORT] == "C2_TRANSPORT"
    c1 = np.asarray(meta["resolved_clip_c1_xy"], float)
    c2 = np.asarray(meta["resolved_clip_c2_xy"], float)
    ph, cab = z["phase_id"], z["cable_xyz"]
    dx = int(tag.split("_")[0][1:])
    dy = int(tag.split("_")[1][1:])
    o = {"tag": tag, "dx": dx, "dy": dy, "cls": rows[tag]["cls"],
         "c2z_gap": float(rows[tag]["c2z_gap_mm"]), "honest": rows[tag]["seated_honest"] == "True",
         "z_c1_final": pin["z_c1_final_mm"], "c1_ret": bool(pin["c1_retained_lowwall"])}

    # A: ROUTE_C1 end (post-settle, pre-C1_SEAT)
    ir = np.where(ph == PH_ROUTE)[0]
    if len(ir):
        i = ir[-1]
        P = cab[i]
        mg = (np.abs(P[:, 1] - c1[1]) <= 0.0075) & (np.abs(P[:, 0] - c1[0]) <= 0.030)
        mn = np.abs(P[:, 1] - c1[1]) < 0.10
        k = int(np.argmin(np.abs(P[:, 1] - c1[1])))
        o["dxa_guard"] = float(P[mg, 0].mean() - c1[0]) * 1e3 if mg.any() else float("nan")
        o["n_guard"] = int(mg.sum())
        o["dxa_naive100"] = float(P[mn, 0].mean() - c1[0]) * 1e3
        o["dxa_argmin"] = float(P[k, 0] - c1[0]) * 1e3
        hl, nr = int(z["held_seg_l"][i]), int(z["nearest_seg_r"][i])
        lo, hi = sorted((hl, nr))
        mw = np.abs(P[:, 1] - c1[1]) <= 0.0075
        idx = np.arange(cab.shape[1])
        o["tail_in_win"] = int((mw & ((idx < lo) | (idx > hi))).sum())

    # B: final-frame flank z within clip Y-window
    P = cab[-1]
    for W in (7.5, 10.0, 15.0):
        m = np.abs(P[:, 1] - c1[1]) <= W * 1e-3
        o[f"flank{W:g}"] = float(P[m, 2].max()) * 1e3 if m.any() else float("nan")

    # C+D: C2 entry (last TRANSPORT frame)
    it = np.where(ph == PH_TRANSPORT)[0]
    if len(it):
        i = it[-1]
        P = cab[i]
        mg = (np.abs(P[:, 1] - c2[1]) <= 0.0075) & (np.abs(P[:, 0] - c2[0]) <= 0.030)
        k = int(np.argmin(np.abs(P[:, 1] - c2[1])))
        o["dxc_guard"] = float(P[mg, 0].mean() - c2[0]) * 1e3 if mg.any() else float("nan")
        o["nc_guard"] = int(mg.sum())
        o["dxc_argmin_all"] = float(P[k, 0] - c2[0]) * 1e3
        o["ph_c2_entry"] = float(((P[k, 1] - c2[1]) * 1e3) % 15.0)
    res.append(o)

out = f"{os.path.dirname(BASE)}/w0e_offline_validation/percell.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0].keys()))
    w.writeheader()
    w.writerows(res)
print(f"wrote {out} ({len(res)} cells)\n")

R = res
esc = [o for o in R if not o["c1_ret"]]
ret = [o for o in R if o["c1_ret"]]
print(f"== classes: escapes={len(esc)} retained={len(ret)} (expect 36/45)")

print("\n== A) F-1a measurand @ROUTE_C1 end ==")
ng = [o["n_guard"] for o in R if "n_guard" in o]
print(f"guarded-set size: min={min(ng)} max={max(ng)} (0-count cells={sum(1 for n in ng if n == 0)})")
print(f"tail-in-window(7.5mm) total across 81: {sum(o.get('tail_in_win', 0) for o in R)}")
print("per-dx guarded dx_a (mean/sd/min/max over dy rows):")
for dxv in (-20, -15, -10, -5, 0, 5, 10, 15, 20):
    v = [o["dxa_guard"] for o in R if o["dx"] == dxv and np.isfinite(o.get("dxa_guard", np.nan))]
    print(f"  dx={dxv:+3d}: mean={np.mean(v):+6.2f} sd={np.std(v):5.2f} min={np.min(v):+6.2f} max={np.max(v):+6.2f} (n={len(v)})")
dev_n = [abs(o["dxa_naive100"] - o["dxa_guard"]) for o in R if np.isfinite(o.get("dxa_guard", np.nan))]
dev_a = [abs(o["dxa_argmin"] - o["dxa_guard"]) for o in R if np.isfinite(o.get("dxa_guard", np.nan))]
print(f"contamination |naive100-guard|: median={np.median(dev_n):.2f}mm p95={np.percentile(dev_n, 95):.2f}mm max={np.max(dev_n):.2f}mm")
print(f"selector delta |argmin-guard|:  median={np.median(dev_a):.2f}mm p95={np.percentile(dev_a, 95):.2f}mm max={np.max(dev_a):.2f}mm")
# separation: ph0 stripe (dy%15==0, dx<=-10) vs good cells — |dxa_guard| magnitude
stripe = [o["dxa_guard"] for o in R if o["dy"] % 15 == 0 and o["dx"] <= -10]
good0 = [o["dxa_guard"] for o in R if o["dy"] % 15 == 0 and o["dx"] > -10]
print(f"ph0 stripe (dx<=-10) dxa_guard: {sorted(round(v, 1) for v in stripe)}")
print(f"ph0 others (dx>-10) dxa_guard:  {sorted(round(v, 1) for v in good0)}")

print("\n== B) flank-z discriminator @final ==")
for W in ("flank7.5", "flank10", "flank15"):
    fp = [o["tag"] for o in ret if o[W] >= 840.0]
    fn = [o["tag"] for o in esc if o[W] < 840.0]
    print(f"{W}: retained>=840 (false fires): {len(fp)}/{len(ret)} {fp[:6]} | escapes<840 (misses): {len(fn)}/{len(esc)} {fn[:6]}")
rmax = max(o["flank10"] for o in ret)
print(f"retained flank10 max = {rmax:.1f}mm (headroom to 840 = {840 - rmax:.1f}mm)")

print("\n== C) F-3 measurand @C2 entry ==")
hij = [o["tag"] for o in R if abs(o.get("dxc_argmin_all", 0)) > 30]
print(f"bare-argmin hijack (|dx|>30mm): {len(hij)}/81 {hij[:8]}")
ngc = [o["nc_guard"] for o in R if "nc_guard" in o]
print(f"guarded-set size @C2: min={min(ngc)} max={max(ngc)} (0-count={sum(1 for n in ngc if n == 0)})")
h_t = [o for o in R if o["honest"] and np.isfinite(o.get("dxc_guard", np.nan))]
h_f = [o for o in R if not o["honest"] and np.isfinite(o.get("dxc_guard", np.nan))]
print(f"|dxc_guard| honest=True : median={np.median([abs(o['dxc_guard']) for o in h_t]):.2f} p90={np.percentile([abs(o['dxc_guard']) for o in h_t], 90):.2f} (n={len(h_t)})")
print(f"|dxc_guard| honest=False: median={np.median([abs(o['dxc_guard']) for o in h_f]):.2f} p90={np.percentile([abs(o['dxc_guard']) for o in h_f], 90):.2f} (n={len(h_f)})")
fin = [o for o in R if np.isfinite(o.get("dxc_guard", np.nan))]
cc = np.corrcoef([abs(o["dxc_guard"]) for o in fin], [o["c2z_gap"] for o in fin])[0, 1]
print(f"corr(|dxc_guard|, c2z_gap) over {len(fin)} cells: r={cc:+.3f}")
mis = sorted((o for o in fin if not o["honest"]), key=lambda o: -abs(o["dxc_guard"]))
print("top-8 C2-miss cells by |dxc_guard|: " + ", ".join(f"{o['tag']}({o['dxc_guard']:+.1f}mm,gap{o['c2z_gap']:+.1f})" for o in mis[:8]))
low = [o for o in fin if not o["honest"] and abs(o["dxc_guard"]) <= 3.5]
print(f"C2-miss cells with |dxc_guard|<=3.5mm (laterally-captured misses, F-3 won't fix): {len(low)}/{len(h_f)}")

print("\n== D) C2-entry phase vs static (CC4-CH3 recompute) ==")
for o in R:
    if o["tag"] in ("x0_y0", "x0_y5", "x0_y10", "x0_y-10", "x0_y-5"):
        print(f"  {o['tag']}: static_phase={o['dy'] % 15:.1f} entry_phase={o.get('ph_c2_entry', float('nan')):.2f}")

# Wilson for 40/45 (CC4 minor)
n, k = 45, 40
p = k / n
zv = 1.959963984540054
den = 1 + zv**2 / n
ctr = (p + zv**2 / (2 * n)) / den
hw = zv * np.sqrt(p * (1 - p) / n + zv**2 / (4 * n**2)) / den
print(f"\nWilson 40/45: [{ctr - hw:.3f}, {ctr + hw:.3f}]")
