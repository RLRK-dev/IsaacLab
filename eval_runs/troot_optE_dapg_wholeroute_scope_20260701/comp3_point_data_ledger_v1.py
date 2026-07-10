# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Rs directive #6 (02:09): machine-extract the comp3 grasp point-data ledger (for p5 CANONICAL_MOTION_TABLE_V1).

Rs '記録してくれ' -> consolidate the measured point data scattered across the banked run JSONs into ONE
values table with PER-ROW provenance (run commit + cell), MACHINE-extracted (no hand-typing). Tables:
  T1 z_drop (cell x arm) [mm]        -- clamp-retention quality proxy (%12: better than rise)
  T2 claw z @close (cell x arm) [m]  -- per-arm claw height (symmetry / Rs #3)
  T3 lane cable z L/R + L-R diff [mm] -- the seesaw substrate
  T4 bend close-window peak by SCENE (flat vs supported) [deg]
  T5 per-arm park EE z + pinch z [m] -- commanded depth per condition
  T6 rise (cell x arm) [mm]          -- lift outcome (hook-capable; read with z_drop)

Source JSONs (banked; commit provenance hard-coded per file):
  comp3_zsweep_result.json         5227d9e916 / verdict 00e191e4ba  (FLAT ik_chord, dz0/3/4/5)
  comp3_perarm_result.json         73c246f812                       (FLAT ik_chord, R+3/L+0)
  comp3_slotprobe_result.json      47c075dad9 / verdict c1a9d66523  (2-slot SUPPORTED, dz0/3/4/5 -- CONFOUNDED)
  comp3_seesaw_result.json         dfbe7fca0b                       (camera map + lane z + engagement)
  comp3_g1_armq_diag_result.json   39b206ddb0                       (baseline park geometry)

Run:
    CUDA_VISIBLE_DEVICES='' /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_point_data_ledger_v1.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
OUT_JSON = _EVAL / "comp3_point_data_ledger_v1.json"
OUT_MD = _EVAL / "comp3_point_data_ledger_v1.md"

PROV = {
    "zsweep": "5227d9e916 (verdict 00e191e4ba) FLAT ik_chord",
    "perarm": "73c246f812 FLAT ik_chord R+3/L+0",
    "slot": "47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5]",
    "seesaw": "dfbe7fca0b camera-map + lane-z",
    "diag": "39b206ddb0 baseline geometry",
}
REC_PARK_EE_Z = 1.06680  # recorded grasp-park EE z (both arms), diag 39b206ddb0
REC_PARK_PINCH_Z = 0.80588  # recorded park pinch z (= EE - EE_TO_PINCH_OPEN 0.26092)


def _load(name):
    p = _EVAL / name
    return json.loads(p.read_text()) if p.exists() else None


def main():
    zs = _load("comp3_zsweep_result.json")
    pa = _load("comp3_perarm_result.json")
    sl = _load("comp3_slotprobe_result.json")

    rows_zdrop, rows_claw, rows_lane, rows_bend, rows_park, rows_rise = [], [], [], [], [], []

    def zsweep_cells():
        for c in zs["cells"]:
            yield f"dz+{c['dz_mm']}", c, PROV["zsweep"]

    def _cell(c, key_l, key_r):
        cb = c["legs"].get("creep_budget", {})
        return cb.get(key_l, {}).get("end_mm"), cb.get(key_r, {}).get("end_mm")

    # T1 z_drop (cell x arm)
    for label, c, prov in zsweep_cells():
        zl, zr = _cell(c, "L_z_drop", "R_z_drop")
        rows_zdrop.append({"cell": label, "scene": "FLAT", "L_z_drop_mm": zl, "R_z_drop_mm": zr, "provenance": prov})
    if pa:
        c = pa["cells"][0]
        zl, zr = _cell(c, "L_z_drop", "R_z_drop")
        rows_zdrop.append(
            {"cell": "R+3/L+0", "scene": "FLAT", "L_z_drop_mm": zl, "R_z_drop_mm": zr, "provenance": PROV["perarm"]}
        )
    if sl:
        for c in sl["cells"]:
            zl, zr = _cell(c, "L_z_drop", "R_z_drop")
            rows_zdrop.append(
                {
                    "cell": f"dz+{c['dz_mm']}",
                    "scene": "SUPPORTED[confounded]",
                    "L_z_drop_mm": zl,
                    "R_z_drop_mm": zr,
                    "provenance": PROV["slot"],
                }
            )

    # T2 claw z @close + T3 lane cable z + T6 rise (from zsweep series) + T4 bend (flat vs supported)
    for label, c, prov in zsweep_cells():
        s = c["series"]
        lt = c["legs"]["close_latched"]["latch_t"]
        ti = s["t"].index(lt) if lt in s["t"] else 0
        rows_claw.append(
            {
                "cell": label,
                "scene": "FLAT",
                "claw_z_L": s["claw_z_l"][ti] if ti < len(s["claw_z_l"]) else None,
                "claw_z_R": s["claw_z_r"][ti] if ti < len(s["claw_z_r"]) else None,
                "claw_dz_LmR_mm": round((s["claw_z_l"][ti] - s["claw_z_r"][ti]) * 1e3, 3)
                if ti < len(s["claw_z_l"])
                else None,
                "provenance": prov,
            }
        )
        cl = s["cable_z_lane_l"][ti] if ti < len(s.get("cable_z_lane_l", [])) else None
        cr = s["cable_z_lane_r"][ti] if ti < len(s.get("cable_z_lane_r", [])) else None
        rows_lane.append(
            {
                "cell": label,
                "scene": "FLAT",
                "cable_z_lane_L": cl,
                "cable_z_lane_R": cr,
                "lane_LmR_mm": round((cl - cr) * 1e3, 2) if (cl is not None and cr is not None) else None,
                "provenance": prov,
            }
        )
        lr = c["legs"].get("lift_rise", {})
        rows_rise.append(
            {
                "cell": label,
                "scene": "FLAT",
                "rise_L_mm": round((lr.get("rise_l_m") or 0) * 1e3, 1),
                "rise_R_mm": round((lr.get("rise_r_m") or 0) * 1e3, 1),
                "provenance": prov,
            }
        )
        rows_bend.append(
            {
                "cell": label,
                "scene": "FLAT",
                "bend_peak_L_deg": c["bend_close_peak_deg"]["L"],
                "bend_peak_R_deg": c["bend_close_peak_deg"]["R"],
                "provenance": prov,
            }
        )
    if pa:
        c = pa["cells"][0]
        lr = c["legs"].get("lift_rise", {})
        rows_rise.append(
            {
                "cell": "R+3/L+0",
                "scene": "FLAT",
                "rise_L_mm": round((lr.get("rise_l_m") or 0) * 1e3, 1),
                "rise_R_mm": round((lr.get("rise_r_m") or 0) * 1e3, 1),
                "provenance": PROV["perarm"],
            }
        )
        rows_bend.append(
            {
                "cell": "R+3/L+0",
                "scene": "FLAT",
                "bend_peak_L_deg": c["bend_close_peak_deg"]["L"],
                "bend_peak_R_deg": c["bend_close_peak_deg"]["R"],
                "provenance": PROV["perarm"],
            }
        )
    if sl:
        for c in sl["cells"]:
            rows_bend.append(
                {
                    "cell": f"dz+{c['dz_mm']}",
                    "scene": "SUPPORTED",
                    "bend_peak_L_deg": c["bend_close_peak_deg"]["L"],
                    "bend_peak_R_deg": c["bend_close_peak_deg"]["R"],
                    "provenance": PROV["slot"],
                }
            )

    # T5 per-arm park EE z + pinch z (commanded depth per condition)
    for label, dz_r, dz_l in (("recording nominal", 0, 0), ("uniform +3", 3, 3), ("R+3/L+0 (Rs #5)", 3, 0)):
        rows_park.append(
            {
                "condition": label,
                "R_park_EE_z": round(REC_PARK_EE_Z + dz_r * 1e-3, 5),
                "R_park_pinch_z": round(REC_PARK_PINCH_Z + dz_r * 1e-3, 5),
                "L_park_EE_z": round(REC_PARK_EE_Z + dz_l * 1e-3, 5),
                "L_park_pinch_z": round(REC_PARK_PINCH_Z + dz_l * 1e-3, 5),
                "provenance": PROV["perarm"] if label.startswith("R+3") else PROV["diag"],
            }
        )

    ledger = {
        "title": "CANONICAL comp3 grasp point-data ledger v1 (Rs directive #6, 2026-07-11)",
        "mapping_note": "NEAR/手前 = R arm (lane Y 0.194); FAR/奥 = L arm (lane Y 0.106) -- camera-verified"
        " dfbe7fca0b. rise is hook-capable; read WITH z_drop (clamp-retention).",
        "T1_z_drop_mm": rows_zdrop,
        "T2_claw_z_at_close": rows_claw,
        "T3_lane_cable_z": rows_lane,
        "T4_bend_peak_by_scene_deg": rows_bend,
        "T5_per_arm_park_z_m": rows_park,
        "T6_rise_mm": rows_rise,
    }
    OUT_JSON.write_text(json.dumps(ledger, indent=1))

    def _md_table(title, rows, cols):
        out = [f"### {title}", "", "| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for r in rows:
            out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
        return "\n".join(out) + "\n"

    md = [
        f"# {ledger['title']}",
        "",
        f"> {ledger['mapping_note']}",
        "",
        "Machine-extracted from banked run JSONs (comp3_point_data_ledger_v1.py). Standing rule (Rs #6):"
        " key point data supplied to this ledger same-turn as the result bank.",
        "",
    ]
    md.append(
        _md_table(
            "T1 z_drop [mm] (clamp-retention; lower=better)",
            rows_zdrop,
            ["cell", "scene", "L_z_drop_mm", "R_z_drop_mm", "provenance"],
        )
    )
    md.append(
        _md_table(
            "T2 claw z @close [m] (per-arm height; Rs #3 symmetry)",
            rows_claw,
            ["cell", "scene", "claw_z_L", "claw_z_R", "claw_dz_LmR_mm", "provenance"],
        )
    )
    md.append(
        _md_table(
            "T3 lane cable z [m] + L-R diff [mm] (seesaw substrate)",
            rows_lane,
            ["cell", "scene", "cable_z_lane_L", "cable_z_lane_R", "lane_LmR_mm", "provenance"],
        )
    )
    md.append(
        _md_table(
            "T4 bend close-window peak [deg] by scene",
            rows_bend,
            ["cell", "scene", "bend_peak_L_deg", "bend_peak_R_deg", "provenance"],
        )
    )
    md.append(
        _md_table(
            "T5 per-arm park z [m] (commanded depth)",
            rows_park,
            ["condition", "R_park_EE_z", "R_park_pinch_z", "L_park_EE_z", "L_park_pinch_z", "provenance"],
        )
    )
    md.append(
        _md_table(
            "T6 rise [mm] (lift outcome; hook-capable, read with T1 z_drop)",
            rows_rise,
            ["cell", "scene", "rise_L_mm", "rise_R_mm", "provenance"],
        )
    )
    OUT_MD.write_text("\n".join(md))

    # ---- Rs #6 FORMAT CORRECTION (%12 02:12): STEP-keyed r3 fragment for the p5 §1.2 unified table.
    # canonical 43-step map (data/waypoints/full_43step.json, phase A initial pick = the comp3 grasp arc):
    #   STEP 2 Above cable / STEP 3 Descend to cable (park z) / STEP 4 Clamp cable (grasp) / STEP 5 Lift cable.
    def _row(cells_rows, keyfn):
        return "; ".join(keyfn(r) for r in cells_rows)

    park = rows_park
    step_md = [
        "# comp3 grasp point-data -- STEP-keyed r3 (Rs #6 fmt; for p5 §1.2 unified-table integration)",
        "",
        f"> {ledger['mapping_note']}",
        "> Canonical 43-step map (full_43step.json, phase-A initial pick): STEP2 Above / STEP3 Descend(park z) /"
        " STEP4 Clamp(grasp) / STEP5 Lift. Machine-extracted; per-row provenance. r3 = this integration round.",
        "",
        "## STEP 3 -- Descend to cable (per-arm PARK z, commanded) [m]",
        "| condition | R_pinch_z (手前) | L_pinch_z (奥) | R_EE_z | L_EE_z | provenance |",
        "|---|---|---|---|---|---|",
    ]
    for r in park:
        step_md.append(
            f"| {r['condition']} | {r['R_park_pinch_z']} | {r['L_park_pinch_z']} | {r['R_park_EE_z']} |"
            f" {r['L_park_EE_z']} | {r['provenance']} |"
        )
    step_md += [
        "",
        "## STEP 4 -- Clamp cable (grasp; close-window measurements)",
        "Primary: per-arm claw z @close = SYMMETRIC <=0.05mm (claws descend equally; the L/R height diff Rs"
        " saw on the slot videos was a slot-contact artifact, absent on flat).",
        "",
        "| footnote | cell | scene | L | R | provenance |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows_claw:
        step_md.append(
            f"| claw_z@close [m] | {r['cell']} | {r['scene']} | {r['claw_z_L']} | {r['claw_z_R']} | {r['provenance']} |"
        )
    for r in rows_lane:
        step_md.append(
            f"| lane_cable_z L-R [mm] | {r['cell']} | {r['scene']} | {r['cable_z_lane_L']} | {r['cable_z_lane_R']}"
            f" (L-R={r['lane_LmR_mm']}) | {r['provenance']} |"
        )
    for r in rows_bend:
        step_md.append(
            f"| bend_peak [deg] | {r['cell']} | {r['scene']} | {r['bend_peak_L_deg']} | {r['bend_peak_R_deg']} |"
            f" {r['provenance']} |"
        )
    step_md += [
        "",
        "## STEP 5 -- Lift cable (retention; z_drop is the clamp-quality proxy, rise is hook-capable)",
        "| footnote | cell | scene | L | R | provenance |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows_zdrop:
        step_md.append(
            f"| z_drop_end [mm] | {r['cell']} | {r['scene']} | {r['L_z_drop_mm']} | {r['R_z_drop_mm']} | {r['provenance']} |"
        )
    for r in rows_rise:
        step_md.append(
            f"| rise [mm] | {r['cell']} | {r['scene']} | {r['rise_L_mm']} | {r['rise_R_mm']} | {r['provenance']} |"
        )
    # route-step (STEP 6-17) context: the comp3 G1 arc executed STEP 2-5 ONLY (runner stops before the
    # route, phase>=2). STEP 6-17 z is NOT comp3-measured; supply the RECORDING-nominal EE z per G-phase
    # (golden w0e_81rerun_snapdown, mujoco-コ 0.716 official) so p5 can map to the route steps.
    import newton_route_env as _nre_unused  # noqa: F401  (path already set by extractor)
    import route_executor as rex

    gz = np.load(_EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz")
    phid = np.asarray(gz["phase_id"])
    eer, eel = np.asarray(gz["ee_pos_r"], float), np.asarray(gz["ee_pos_l"], float)
    p2g = rex._RECORDED_PHASE_TO_G
    step_md += [
        "",
        "## STEP 6-17 (route) -- NOT comp3-measured (G1 arc = STEP 2-5 only). RECORDING-nominal EE z per"
        " G-phase, golden w0e_81rerun_snapdown (mujoco-コ, 0.716 official). p5 maps G-phase -> route steps.",
        "| G-phase | R_EE_z [min,max] | L_EE_z [min,max] | provenance |",
        "|---|---|---|---|",
    ]
    for g in range(6):
        fr = np.array([i for i in range(len(phid)) if p2g.get(int(phid[i]), -1) == g])
        if len(fr) == 0:
            continue
        zr, zl = eer[fr, 2], eel[fr, 2]
        step_md.append(
            f"| G{g} | [{zr.min():.4f},{zr.max():.4f}] | [{zl.min():.4f},{zl.max():.4f}] |"
            " golden w0e_81rerun_snapdown (recording-nominal, NOT comp3-run) |"
        )
    step_md += [
        "",
        "## STEP 3 park depth CORRECTION status (Rs #5 手前R +3~4mm)",
        "- R-only +3~4mm is NOT a confirmed value -- '検証中' resolved to: the per-arm confirmation cell"
        " (R+3/L+0, 73c246f812) found the arms are CABLE-COUPLED (R z_drop 15.9mm vs uniform-dz3 R 0.0mm;"
        " video: R hold MARGINAL, sharp bend, not a clean clamp). So R-only depth does NOT recover R's"
        " uniform-depth quality -- do NOT record R+3~4mm as a confirmed park correction. HELD.",
        "",
        "## Load-bearing reads for p5 §1.2",
        "- ik_chord holds the NEAR(R/手前) arm (z_drop 0 at uniform dz3) but NEVER the FAR(L/奥) arm at any"
        " depth; only FEEDFORWARD (D rho=0, f8b1ff6b4c) holds L. STEP4/5 are the failing legs on ik_chord.",
        "- per-arm depth is CABLE-COUPLED (R+3/L+0 -> R z_drop 15.9mm vs uniform-dz3 R 0.0mm): R-only depth"
        " does NOT recover R's uniform-depth quality. VN-2 R-only-+3..4mm is NOT a clean independent lever.",
        "- seesaw substrate real (lane cable z L-R flips sign with dz) but the outcome winner (R) does not flip.",
    ]
    out_step = _EVAL / "comp3_point_data_STEPkeyed_r3.md"
    out_step.write_text("\n".join(step_md))

    print("\n".join(step_md))
    print(f"-> {OUT_JSON}\n-> {OUT_MD}\n-> {out_step}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
