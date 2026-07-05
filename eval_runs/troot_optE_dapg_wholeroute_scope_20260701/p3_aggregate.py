#!/usr/bin/env python3
"""P3-grid aggregator (W0-d) — per-cell parse -> summary CSV + P3_GRID_REPORT draft.

Encodes the PINNED counting (P3_GRID_PREREG §2-4 + AMENDMENT A1):
  - class (A1): strict = SUCCESS* AND c2_seated_honest=True / seat_miss = SUCCESS* AND not seated (delivery-ok, rider-1)
                / FAIL = non-SUCCESS (R_MISS etc.) / infra = no-json OR finite=False.
  - SR PRIMARY = strict, SECONDARY = any-seat (SUCCESS*). Wilson 95% CI. winnable denominator excludes draw cells
    (draw-class line-drawing = %9/%12 joint-read; this DRAFT reports counts + FAIL forensics + BOTH denominators
    [all-81 and winnable-candidate=81-minus-infra] and flags the draw exclusion as joint-read-pending).
  - derivations: per-offset SR, corner-miss magnitude, dual-grip span, episode length, draw-class candidates.
DRAFT only: %9 re-counts (unique-offset + counting compliance) -> %12+%9 joint read finalizes draw-class + SR.
0-commit (result dir). Run after the grid completes (cite the 2nd-invocation DONE line, NOT the wave-1-only artifact).
"""
import csv
import json
import math
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__)) + "/p3_grid"
MM = [-20, -15, -10, -5, 0, 5, 10, 15, 20]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def classify(verdict, seated_honest, finite, has_json):
    if not has_json:
        return "infra_nojson"
    if finite is False:
        return "infra_nonfinite"
    if verdict and str(verdict).startswith("SUCCESS"):
        return "strict" if seated_honest is True else "seat_miss"
    return "FAIL"


def miss_geom(r):
    """Provisional draw-class forensic label (PREREG §3 step1; thresholds fixed pre-data).

    corner-vs-draw LINE = %9/%12 joint-read step2 — this label is only an INPUT, not the decision.
    Only interpreted for non-strict cells; strict -> "" (blank).
    """
    if r.get("cls") == "strict":
        return ""
    rr = r.get("r_reach_resid_mm")
    excess = r.get("excess_span_mm")  # raw column (achieved - target); computed in load_cell before this call
    if rr is not None and rr > 20:
        return "reach-wall"
    if excess is not None and excess > 15:
        return "air/bow"
    return "seat/other"


def load_cell(tag):
    d = os.path.join(BASE, f"cell_{tag}")
    jp = os.path.join(d, "route_c2_pin.json")
    row = {"tag": tag, "has_json": os.path.isfile(jp)}
    if row["has_json"]:
        j = json.load(open(jp))
        m = j.get("route_c2_metrics", {})
        row.update(
            finite=j.get("finite"), qvel=j.get("qvel_ok"),
            verdict=m.get("c2_regrasp_verdict"), regrasp_ok=m.get("c2_regrasp_ok"),
            seated_honest=m.get("c2_seated_honest"), seated_naive=m.get("c2_seated_naive"),
            r_grip_N=m.get("c2_regrasp_r_grip_N"), l_grip_N=m.get("c2_regrasp_l_grip_N"),
            r_reach_resid_mm=m.get("c2_regrasp_r_reach_resid_mm"),
            target_span_mm=m.get("c2_regrasp_target_y_span_mm"),
            tilt_deg=m.get("c2_regrasp_tilt_theta_deg"),
            c1_seat_dist_mm=m.get("cable_c1_seat_dist_mm"), c2_seat_dist_mm=m.get("cable_c2_seat_dist_mm"),
            c2_wall_dist_mm=m.get("c2_wall_dist_spacer_excluded_mm"),  # producer :4756 seat metric (raw c2-miss magnitude)
            c2z_mm=m.get("cable_z_at_c2_mm"),  # cable Z at c2 [mm] — DOMINANT seat-miss separator (%9 joint-read 13:35)
            cable_c1_final_dist_mm=m.get("cable_c1_final_dist_mm"), min_rpad_c1_mm=m.get("min_rpad_c1_mm"),
            max_slip_xy=m.get("max_abs_slip_xy"), mean_slip_xy=m.get("mean_slip_xy"),
        )
    else:
        row.update(finite=None, verdict=None, seated_honest=None)
    # npz-derived: episode length (frames) + achieved dual-grip span (last-frame 3D ee_l<->ee_r)
    npz = os.path.join(d, "route_demo_raw.npz")
    row["ep_frames"] = None
    row["achieved_span_mm"] = None
    if os.path.isfile(npz):
        try:
            z = np.load(npz, allow_pickle=True)
            row["ep_frames"] = int(z["frame_idx"].shape[0])
            el, er = z["ee_pos_l"], z["ee_pos_r"]
            row["achieved_span_mm"] = round(float(np.linalg.norm(el[-1] - er[-1]) * 1e3), 2)
        except Exception as e:  # noqa: BLE001
            row["npz_err"] = str(e)[:60]
    # derived raw magnitude: dual-grip span excess (achieved - target); both already parsed above
    ach, tgt = row.get("achieved_span_mm"), row.get("target_span_mm")
    row["excess_span_mm"] = round(ach - tgt, 2) if (ach is not None and tgt is not None) else None
    _cz = row.get("c2z_mm")  # z-gap vs groove ref 829.0mm (%12 13:38) — DOMINANT seat-miss separator (%9 13:35)
    row["c2z_gap_mm"] = round(_cz - 829.0, 2) if _cz is not None else None
    row["cls"] = classify(row.get("verdict"), row.get("seated_honest"), row.get("finite"), row["has_json"])
    row["miss_geom"] = miss_geom(row)
    return row


def main():
    tags = [f"x{x}_y{y}" for x in MM for y in MM]
    rows = [load_cell(t) for t in tags]
    by = {c: [r for r in rows if r["cls"] == c] for c in ("strict", "seat_miss", "FAIL", "infra_nojson", "infra_nonfinite")}
    n = len(rows)
    n_infra = len(by["infra_nojson"]) + len(by["infra_nonfinite"])
    n_strict, n_seatmiss, n_fail = len(by["strict"]), len(by["seat_miss"]), len(by["FAIL"])
    n_anyseat = n_strict + n_seatmiss

    # --- CSV (per-cell, all fields + class) ---
    cols = ["tag", "cls", "miss_geom", "verdict", "regrasp_ok", "seated_honest", "seated_naive", "finite", "qvel",
            "r_grip_N", "l_grip_N", "r_reach_resid_mm", "min_rpad_c1_mm",
            "target_span_mm", "achieved_span_mm", "excess_span_mm",
            "c1_seat_dist_mm", "cable_c1_final_dist_mm", "c2_seat_dist_mm", "c2_wall_dist_mm",
            "c2z_mm", "c2z_gap_mm",
            "tilt_deg", "max_slip_xy", "mean_slip_xy", "ep_frames"]
    with open(os.path.join(BASE, "p3_grid_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (int(r["tag"].split("_")[0][1:]), int(r["tag"].split("_")[1][1:]))):
            w.writerow(r)

    # --- distributions (over valid = has_json & finite!=False) ---
    valid = [r for r in rows if r["has_json"] and r.get("finite") is not False]
    def dist(key, cells):
        vals = [r[key] for r in cells if r.get(key) is not None]
        if not vals:
            return "n/a"
        a = np.array(vals, float)
        return f"n={len(a)} p1={np.percentile(a,1):.2f} p50={np.percentile(a,50):.2f} p99={np.percentile(a,99):.2f} max={a.max():.2f}"

    # --- SR (both denominators; draw exclusion = joint-read-pending) ---
    def sr_line(k, label):
        p, lo, hi = wilson(k, n - n_infra)
        p2, lo2, hi2 = wilson(k, n)
        return (f"- {label}: {k}/{n - n_infra} winnable-candidate = {p:.3f} (Wilson95 [{lo:.3f},{hi:.3f}]) "
                f"| {k}/{n} all-cells = {p2:.3f} [{lo2:.3f},{hi2:.3f}] "
                f"(winnable EXCLUDES draw cells -> %9/%12 joint-read finalizes)")

    # --- draw-class candidates = FAIL + seat_miss with forensics ---
    def forensic(r):
        vd, rr = r.get("verdict"), r.get("r_reach_resid_mm")
        ach, excess = r.get("achieved_span_mm"), r.get("excess_span_mm")
        geom = r.get("miss_geom") or "seat/other"  # SSOT = miss_geom() (same label as CSV column)
        return (f"  {r['tag']:>10} cls={r['cls']:9} verdict={vd} r_grip={r.get('r_grip_N')} "
                f"reach_resid={rr}mm achieved_span={ach}mm (excess={excess}) "
                f"c2_wall={r.get('c2_wall_dist_mm')}mm ⭐c2z_gap={r.get('c2z_gap_mm')}mm rpad_c1={r.get('min_rpad_c1_mm')}mm -> {geom}")

    rep = []
    rep.append("# P3-GRID REPORT (DRAFT — %11 aggregate; %9 re-count + %12/%9 joint read finalizes)")
    rep.append("")
    rep.append(f"cells parsed = {n} (expect 81). infra = {n_infra} (no-json {len(by['infra_nojson'])} / non-finite {len(by['infra_nonfinite'])}).")
    rep.append(f"class counts: strict={n_strict}  seat_miss(any-seat∧¬strict, rider-1)={n_seatmiss}  FAIL={n_fail}  infra={n_infra}")
    rep.append("")
    rep.append("## SR (PREREG §2 + A1; PRIMARY=strict, SECONDARY=any-seat)")
    rep.append(sr_line(n_strict, "PRIMARY strict (SUCCESS*∧seated_honest)"))
    rep.append(sr_line(n_anyseat, "SECONDARY any-seat (SUCCESS*)"))
    rep.append(f"- evidence-gate (PREREG §2): strict SR ≥95% -> M-C bites (α-DR: perturb/obs-noise) / ≤80% -> position-DR+c2 / mid -> Rs")
    rep.append(f"- ≥95% certify needs n_winnable≥59 (rule-of-3). candidate winnable = {n - n_infra}.")
    rep.append("")
    rep.append("## Derivations (PREREG §4)")
    rep.append(f"- corner-miss: R reach residual [mm] (row2 p_hit input): {dist('r_reach_resid_mm', valid)}")
    rep.append(f"- corner-miss: c2 wall dist [mm] (pos=off-wall/miss, neg=seated; c1->c2 Δ bound input): {dist('c2_wall_dist_mm', valid)}")
    rep.append(f"- dual-grip achieved span [mm] (row3, target=88): {dist('achieved_span_mm', valid)}")
    rep.append(f"- episode length [RAW FRAMES] (row4): {dist('ep_frames', valid)}")
    _epf = [r["ep_frames"] for r in valid if r.get("ep_frames") is not None]
    if _epf:
        _cs99 = np.percentile(np.array(_epf, float), 99) / 10.0  # 10 phys-frames/ctrl-step (PREREG p50~771 <-> 7709/10)
        rep.append(f"  -> CONTROL-STEPS = frames/10: p99≈{_cs99:.0f} ctrl-steps (horizon unit). horizon 900 "
                   f"{'OK (<810 bump thresh)' if _cs99 < 810 else 'BUMP needed (>=810)'}. n<100 -> max-of-n conservative.")
    rep.append(f"- c2_seat_dist [mm] (neg=penetrated/seated): {dist('c2_seat_dist_mm', valid)}")
    rep.append(f"- ⭐ c2z_gap [mm] (DOMINANT seat separator, %9/%12 13:35-38; cable Z at c2 − groove ref 829.0): {dist('c2z_gap_mm', valid)}")
    rep.append(f"    strict-class: {dist('c2z_gap_mm', by['strict'])} | seat_miss+FAIL: {dist('c2z_gap_mm', by['seat_miss'] + by['FAIL'])}")
    rep.append(f"- c2 regrasp tilt [deg]: {dist('tilt_deg', valid)}")
    rep.append(f"- max_slip_xy [mm]: {dist('max_slip_xy', valid)}")
    rep.append("")
    # --- 2D offset-grid map (anisotropic seat-window + systematic-vs-stochastic direction, PREREG §3/§4) ---
    # The 81-cell offset grid IS the controlled 2D displacement sampling; cls + signed c2_wall_dist as f(dx,dy)
    # gives the DIRECTIONAL seat-window WITHOUT a per-cell landing vector. NOTE: c2x/c2y (JSON) = constant TARGET
    # (0.40/0.075), NOT cable landing; producer c2_wall_dist (:4743) = mujoco geom<->geom surface min-dist, whose
    # 2D witness points are not saved -> per-cell miss-vector RESERVED (c2_miss_dx/dy, c1_miss_dx/dy: joint-read re-deriv).
    rowmap = {r["tag"]: r for r in rows}
    GLY = {"strict": ".", "seat_miss": "s", "FAIL": "X", "infra_nojson": "?", "infra_nonfinite": "!"}
    rep.append("## 2D offset-grid map (rows dy=+20(top)..-20(bottom), cols dx=-20..+20 mm)")
    rep.append("(p_hit object, %12 2026-07-05: Delta_EE common-mode compensates cable offset ~1:1 (first order) -> P(correction")
    rep.append(" lands in success region) = success-region SHAPE in offset space = THIS map. Witness-vector only sets within-")
    rep.append(" cell curvature; 5mm pitch ~ sigma 2-7.5mm same scale -> grid resolution suffices. (a) is more direct, not a compromise.)")
    rep.append("class (. strict / s seat_miss / X FAIL / ? no-json / ! non-finite):")
    rep.append("         dx=" + "".join(f"{x:>5}" for x in MM))
    for y in reversed(MM):
        rep.append(f"  dy={y:>4}   " + "".join(f"{GLY.get(rowmap.get(f'x{x}_y{y}', {}).get('cls'), ' '):>5}" for x in MM))
    rep.append("signed c2_wall_dist [mm] (+off-wall/miss, -seated = wall-normal directed component):")
    rep.append("         dx=" + "".join(f"{x:>7}" for x in MM))
    for y in reversed(MM):
        cells = []
        for x in MM:
            v = rowmap.get(f"x{x}_y{y}", {}).get("c2_wall_dist_mm")
            cells.append(f"{v:>7.1f}" if isinstance(v, (int, float)) else "    n/a")
        rep.append(f"  dy={y:>4}   " + "".join(cells))
    rep.append("⭐ c2z_gap [mm] (DOMINANT separator, %9/%12 13:35-38: strict≈0, miss perches +Z above groove):")
    rep.append("         dx=" + "".join(f"{x:>7}" for x in MM))
    for y in reversed(MM):
        cells = []
        for x in MM:
            v = rowmap.get(f"x{x}_y{y}", {}).get("c2z_gap_mm")
            cells.append(f"{v:>7.1f}" if isinstance(v, (int, float)) else "    n/a")
        rep.append(f"  dy={y:>4}   " + "".join(cells))
    rep.append("NOTE (real separating axis = Z): seat-miss is separated by Z (cable perched above groove), NOT lateral wall")
    rep.append("  (wall within margin = NON-separating). z_gap = the p_hit-relevant miss magnitude; c2_wall identifies only the")
    rep.append("  3 XY-lateral-tail cells. in_groove(z) leg = the failing measure for all 22 non-strict (%9/%12 joint-read 13:35-40).")
    rep.append("RESERVED (per-cell XY-lateral miss vector): c2_miss_dx/dy_mm + c1_miss_dx/dy_mm — !! DO NOT re-invent from npz nodes.")
    rep.append("  WHY ABSENT (evidence, rider r-a2): producer c2_wall_dist (test_newton_clip_routing.py:4743) = mujoco geom<->")
    rep.append("  geom SURFACE min-dist (_min_dist_mm(cable_geoms, c2_wall_g)); its 2D witness points are NOT saved in JSON/npz.")
    rep.append("  c2x/c2y (JSON) = CONSTANT target (0.40/0.075) NOT landing. Naive nearest-cable-node-to-target proxy gives")
    rep.append("  |miss|=40.2mm vs producer scalar 12.655mm = 3x off = INVALID (would mislead p_hit sigma). Correct fill =")
    rep.append("  model reload + mj_geomDistance witness at joint-read, ONLY if within-cell curvature resolution is needed.")
    rep.append("")
    rep.append("## Draw-class CANDIDATES (PREREG §3 step1 forensics; corner-vs-draw line = joint-read step2)")
    rep.append(f"FAIL cells ({n_fail}) + seat_miss cells ({n_seatmiss}) — per-cell forensics (miss geom classified provisionally):")
    for r in by["FAIL"] + by["seat_miss"]:
        rep.append(forensic(r))
    if n_infra:
        rep.append(f"\n⚠ INFRA cells ({n_infra}) — excluded from SR, re-run candidates:")
        for r in by["infra_nojson"] + by["infra_nonfinite"]:
            rep.append(f"  {r['tag']} cls={r['cls']}")
    rep.append("")
    rep.append("## Conservatism (PREREG §5): script grid = α base behavior; for β = UPPER bound on 'script-solvable support' (NOT β from-P0 SR).")
    rep.append("## Verification scope (video-leg, §運用14): visual leg OMITTED-with-justification (loud, not silent) — this RESULT is")
    rep.append("  a NUMERIC verdict-aggregate over the PRODUCER's pinned honest metrics (c2_seated_honest geom-dist :4756 / c2_regrasp")
    rep.append("  :4805 = validated success criteria), over the banked Rs-confirmed WORKING square-on route (nominal x0_y0 byte-")
    rep.append("  identical to b2_cpC), varying only CABLE_XY_OFFSET (DR sweep, NOT a new motion-capability claim). Targeted video =")
    rep.append("  joint-read step2 ONLY for specific FAIL/seat_miss cells whose miss MECHANISM needs visual confirm before draw-class.")
    open(os.path.join(BASE, "P3_GRID_REPORT_draft.md"), "w").write("\n".join(rep))
    print("\n".join(rep))
    print(f"\n[written] {BASE}/p3_grid_summary.csv + P3_GRID_REPORT_draft.md")


if __name__ == "__main__":
    main()
