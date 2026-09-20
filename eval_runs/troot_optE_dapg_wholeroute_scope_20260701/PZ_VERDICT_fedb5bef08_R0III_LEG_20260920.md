# pZ — verdict on the R0 harness follow-up 6 `fedb5bef08` (R0-iii wrist-direction report row, v3 §17.12): addendum 9's predicate and leg, judged against the harness's own parent blob `89e7a0e52b4d` (= the accepted window-R0 harness `8e5905539c`)

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 14:42:27 JST on m-p18-438 (relay of p0 m-p0-385R; p4 kickoff item 24 = m-p4-287: the report row is 「可・置き場 = R0 harness の report 行・条件 5 点」; window R0's acceptance untouched). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted**: acceptance of the report row is p4's word.

**The object**: commit `fedb5bef08` (author date 14:23:35 JST, parent `09e47cb743`, `1 file changed, 78 insertions(+), 1 deletion(-)`): `r0_convergence_harness.py` blob `89e7a0e52b4d` → `f5dc14a8d1b3` (sha256 `3ff26da6a378afb28fe342ffc8e81a06c14f02c50cdeaa41e6ffdd219f1f289e`, 1422 lines); commits touching the file after it = **0**; driver commits after `96e9ece175` = 0; HEAD at writing `557e80f8ad`. **Order of existence**: addendum 9 (`03b42afdb5`, 11:43) ≺ the object (14:23:35) ≺ this leg (as-landed runs 14:33-14:36). **Pre-registration** = `PZ_R0_CONVERGENCE_LEG_PREREG_20260916.md` addendum 9 @ `03b42afdb5` (rows, predicate `pz_r0iii_pred.py`, expectation `r0iii_{L,B,RC,NH}.json`, leg procedure) — plus rows 1-11, 1′ and addenda 2-8 for the existing lines. **Run 0** (the harness is `mj_step` 0 by count, both by its own counter and by mine); **stop-cause tags**: on the report row **controller non-convergence** on the control model RC at k = 1 (expected in addendum 9, a control's tag, not an instrument stop); on the existing rows **none**; no instrument calibration stop.

## Verdict per row

| # | row (addendum 9 leg procedure) | verdict | measured |
|---|---|---|---|
| 1 | static: additions-only predicate on (parent blob, landed blob) | **CONFIRMED** | `PASS main(): inserted=1 dict_extended=1; top-level new defs/constants=4`; parent/parent `FAIL` (the eleven pre-registered controls stand, appendix of `03b42afdb5`). Hunks `@@ -1244,6 +1244,81 @@ def _r0ii(models_R, model_L, rows, seed, re_max, qL_unsharpened): @@ -1302,6 +1377,8 @@ def main() -> int: @@ -1333,7 +1410,7 @@ def main() -> int:`; the single removed line is the `rec` dict's closing line, re-emitted with the `"R0iii"` key (`dict_extended=1`); 70 lines added; new names: `1247:_E2 = np.array([0.0, 1.0, 0.0])            # section 17.12: the roll axis of the tool frame, RD @ e2; 1248:_E3 = np.array([0.0, 0.0, 1.0])            # section 17.12: the approach axis, RD @ e3; 1251:def _wrist_one(t, tgt, k, seed, re_max):; 1284:def _r0iii(models_R, model_L, GL, GR, seed, re_max):; 1381:    r0iii = _r0iii(models_r0ii, models["L"], GL, GR, args.seed, args.re_max); 1413:           "negative_control_R_on_L": neg, "R0ii": r0ii, "R0iii": r0iii}`; `mj_step` calls in the file = 0 (predicate rule 7) |
| 2 | execution from a `git archive` of the landed commit, the as-landed procedure (`pz_r0_exec.py`, `--dump` = the real dump copy sha `4158e4e638e9b0fc…`): exit 0; positive control counted | **CONFIRMED** | `start 14:33:02 · run rc=0 14:36:04 · ctrl rc=0 14:36:05`; run: my `mj_step` counter **0**, harness self-sha == file sha (`3ff26da6a378afb2…`); control (one injected `mj_step`): my counter **1**, the copy's self-sha differs (`69eb6eac2b328ad3…`) — the counter sees the harness's calls |
| 3 | every existing summary number and row equal to the `8e5905539c` verdict (`2bd3be01c2`) to 1e-12 | **CONFIRMED** | `pz_r0_compare_v4.py` run on both reports (v5 = `8e5905539c`, v6 = this commit): the two outputs differ in **2 lines = the same summary line**, and only in `harness_sha256: f630c9715832f40de7961a2cf9d912692d95259bb8f9fecf610780356acf5724, elapsed_s: 176.961` vs `harness_sha256: 3ff26da6a378afb28fe342ffc8e81a06c14f02c50cdeaa41e6ffdd219f1f289e, elapsed_s: 181.848` (the harness sha and the wall time); rows 1-18 both sides, U0, the negative control, R0-ii per (row, k) and its bar are identical; summary: L 18/18, R 18/18, `L_converges_R_not` [], R0-ii bar valid True, `mj_step_calls` 0 |
| 4 | the `R0iii` block vs `r0iii_{L,B,RC,NH}.json` per (model, k): converged flags and tags equal; Δ, d, wrist_3 − p, RD·e2/e3 ≤ 1e-6 mm / 1e-9; Δ_pair ≤ 1e-6 mm; k = 1 signs (L −1, R +1); `|Δx| ≤ 2 mm + 0.05·d` | **CONFIRMED** | `pz_r0iii_compare.py` (appendix B): worst diffs `{'delta_mm': 2.1316282072803006e-13, 'd_mm': 2.2737367544323206e-13, 'wrist3_mm': 3.268496584496461e-13, 'RD': 0.0, 'pair_mm': 3.410605131648481e-13}` (mm; RD exact); every converged/tag pair equal, including **RC k = 1 = controller non-convergence on both instruments**; signs at k = 1: L −1, B/R +1, NH/R +1; `|Δx|` within tolerance on every converged cell; Δ_pair(0) → Δ_pair(1) = 75.000 → 107.314 mm on B, 75.000 → 107.314 mm on NH, RC k = 1 none |
| 5 | falsification forms (§17.12) on the harness's own printed values | **none holds** | same-side signs at k = 1: no (L −1 / R +1 on B and NH); `Δ_pair(1) ≤ Δ_pair(0)`: no (grows on B and NH); `|Δx| > 2 mm + 0.05·d`: no. Reported quantity for p11's court: the wrists tip to opposite sides of the cable (L −y, R +y) by 0.343·d = 38.377 mm at roll 0.35, d = 111.920 mm |
| 6 | stop-cause tags (Rs1 supplement a) | **as expected** | `stop_cause_tags_seen` on the existing rows = []; the report row's RC k = 1 tag = controller non-convergence (control model, pre-registered); no `AssertionError` / instrument stop |
| 7 | bar / STOP / exit unchanged; window R0's acceptance untouched | **CONFIRMED** | predicate rule 6 (final `return` dump-identical) + measured exit 0 on the run; the existing rows' numbers unchanged (row 3); the report row prints and judges nothing (`claim` = 「report（手首方向）・bar なし」) |

## Collation of p0's §8.63 (`eca124a730`) against this desk's measurements
| p0's claim | this desk |
|---|---|
| predicate PASS on the landed blob (`inserted=1 dict_extended=1 new defs/constants=4`); base/base FAIL | CONFIRMED (row 1, same strings) |
| the §8.62 candidate v8 would have FAILED (module docstring edited) and was corrected to v9 before landing | not re-run here (v8 is p0's scratch, not an object); the landed object is what the predicate judged |
| copy check PASS (17 defs + 12 assignments AST-equal to both driver blobs), py_compile OK, run 0 | the copy fidelity was this desk's row 1/1′ on `8e5905539c` and the parent blob is that harness (`89e7a0e52b4d`); the new statements touch none of the copied defs (row 1); execution here = run 0 by count |

## What this leg does not show (holes)
- The report row is what it says: the wrist geometry of the row-4 solutions at k ∈ {0, 1} on the composed one-arm models, static; no contact, no motion, no route (#69). The two wrists' actual clearance during a route is not measured by Δ_pair.
- RC's k = 1 non-convergence is a control-model tag; it says nothing about B.
- p11's §17.12 predictions are reproduced; whether the "outside" convention is the right design reading is p11's court (p4 condition ④), not this leg's.

## Appendix A — the harness's printed report lines (run, verbatim)
```text
[r0-iii] model B k=0 (roll L -0.00 / R +0.00): L Δ=(-0.0 +0.0 +111.9) d=111.9 | R Δ=(+0.0 -0.0 +111.9) d=111.9 | sign(Δy) L=0 R=-1 | Δ_pair=75.00000000000061 mm  [mm; report only]
[r0-iii] model B k=1 (roll L -0.35 / R +0.35): L Δ=(-0.0 -38.4 +105.1) d=111.9 | R Δ=(+0.0 +38.4 +105.1) d=111.9 | sign(Δy) L=-1 R=1 | Δ_pair=107.31362522727086 mm  [mm; report only]
[r0-iii] model B: Δ_pair k0 -> k1 = 75.00000000000061 -> 107.31362522727086 mm; grows = True; roll axis RD·e2 (L k=1) = [-1.0, 0.0, 0.0], a = RD·e3 = [-0.0, -0.343, 0.939]
[r0-iii] model RC k=0 (roll L -0.00 / R +0.00): L Δ=(-0.0 +0.0 +111.9) d=111.9 | R Δ=(-0.0 +0.0 +111.9) d=111.9 | sign(Δy) L=0 R=1 | Δ_pair=75.00000000000075 mm  [mm; report only]
[r0-iii] model RC k=1 (roll L -0.35 / R +0.35): L Δ=(-0.0 -38.4 +105.1) d=111.9 | R NOT CONVERGED (controller non-convergence) | sign(Δy) L=-1 R=None | Δ_pair=None mm  [mm; report only]
[r0-iii] model RC: Δ_pair k0 -> k1 = 75.00000000000075 -> None mm; grows = None; roll axis RD·e2 (L k=1) = [-1.0, 0.0, 0.0], a = RD·e3 = [-0.0, -0.343, 0.939]
[r0-iii] model NH k=0 (roll L -0.00 / R +0.00): L Δ=(-0.0 +0.0 +111.9) d=111.9 | R Δ=(-0.0 +0.0 +111.9) d=111.9 | sign(Δy) L=0 R=1 | Δ_pair=75.00000000000038 mm  [mm; report only]
[r0-iii] model NH k=1 (roll L -0.35 / R +0.35): L Δ=(-0.0 -38.4 +105.1) d=111.9 | R Δ=(-0.0 +38.4 +105.1) d=111.9 | sign(Δy) L=-1 R=1 | Δ_pair=107.31362522727069 mm  [mm; report only]
[r0-iii] model NH: Δ_pair k0 -> k1 = 75.00000000000038 -> 107.31362522727069 mm; grows = True; roll axis RD·e2 (L k=1) = [-1.0, 0.0, 0.0], a = RD·e3 = [-0.0, -0.343, 0.939]
```

## Appendix B — `pz_r0iii_compare.py` output (verbatim; instrument sha256 a3b72c80486433580337bdc7f3072e587346c3a4db86f36479a8356bc3998f4a)
```text
L k=0 converged (harness | mine): (True, True, True)
L k=0 tag (harness | mine): ('none', 'none', True)
L k=0 (yaw, roll) (harness | mine): ((0.0, -0.0), (0.0, -0.0))
L k=0 max|RD.e2/e3 diff|: 0.0
L k=0 Delta harness | mine [mm]: ([-0.0, 0.0, 111.92], [-0.0, 0.0, 111.92], 'max|diff| 1.25e-13')
L k=0 d / wrist3 max|diff| [mm]: ('0.00e+00', '1.25e-13')
L k=0 |dx| <= 2 mm + 0.05 d (harness values): True
L k=1 converged (harness | mine): (True, True, True)
L k=1 tag (harness | mine): ('none', 'none', True)
L k=1 (yaw, roll) (harness | mine): ((0.0, -0.35), (0.0, -0.35))
L k=1 max|RD.e2/e3 diff|: 0.0
L k=1 Delta harness | mine [mm]: ([-0.0, -38.3771, 105.1346], [-0.0, -38.3771, 105.1346], 'max|diff| 4.97e-14')
L k=1 d / wrist3 max|diff| [mm]: ('1.42e-14', '5.68e-14')
L k=1 |dx| <= 2 mm + 0.05 d (harness values): True
L k=1 sign(dy) (harness | mine | expected): (-1, -1, -1)
B/R k=0 converged (harness | mine): (True, True, True)
B/R k=0 tag (harness | mine): ('none', 'none', True)
B/R k=0 (yaw, roll) (harness | mine): ((0.0, 0.0), (0.0, 0.0))
B/R k=0 max|RD.e2/e3 diff|: 0.0
B/R k=0 Delta harness | mine [mm]: ([0.0, -0.0, 111.92], [0.0, -0.0, 111.92], 'max|diff| 2.78e-14')
B/R k=0 d / wrist3 max|diff| [mm]: ('0.00e+00', '2.78e-14')
B/R k=0 |dx| <= 2 mm + 0.05 d (harness values): True
B/R k=1 converged (harness | mine): (True, True, True)
B/R k=1 tag (harness | mine): ('none', 'none', True)
B/R k=1 (yaw, roll) (harness | mine): ((0.0, 0.35), (0.0, 0.35))
B/R k=1 max|RD.e2/e3 diff|: 0.0
B/R k=1 Delta harness | mine [mm]: ([0.0, 38.3771, 105.1346], [0.0, 38.3771, 105.1346], 'max|diff| 2.13e-13')
B/R k=1 d / wrist3 max|diff| [mm]: ('2.27e-13', '2.13e-13')
B/R k=1 |dx| <= 2 mm + 0.05 d (harness values): True
B/R k=1 sign(dy) (harness | mine | expected): (1, 1, 1)
B pair block (harness): {"pair_mm": {"0": 75.00000000000061, "1": 107.31362522727086}, "pair_grows_k0_to_k1": true}
B Delta_pair(k=0) mine [mm]: 75.0
B Delta_pair(k=0) harness | mine: (75.00000000000061, 75.0, '2.84e-14')
B Delta_pair(k=1) mine [mm]: 107.313625
B Delta_pair(k=1) harness | mine: (107.31362522727086, 107.313625, '1.85e-13')
RC/R k=0 converged (harness | mine): (True, True, True)
RC/R k=0 tag (harness | mine): ('none', 'none', True)
RC/R k=0 (yaw, roll) (harness | mine): ((0.0, 0.0), (0.0, 0.0))
RC/R k=0 max|RD.e2/e3 diff|: 0.0
RC/R k=0 Delta harness | mine [mm]: ([-0.0, 0.0, 111.92], [-0.0, 0.0, 111.92], 'max|diff| 5.55e-14')
RC/R k=0 d / wrist3 max|diff| [mm]: ('0.00e+00', '5.55e-14')
RC/R k=0 |dx| <= 2 mm + 0.05 d (harness values): True
RC/R k=1 converged (harness | mine): (False, False, True)
RC/R k=1 tag (harness | mine): ('controller non-convergence', 'controller non-convergence', True)
RC/R k=1 (yaw, roll) (harness | mine): ((0.0, 0.35), (0.0, 0.35))
RC/R k=1 max|RD.e2/e3 diff|: 0.0
RC pair block (harness): {"pair_mm": {"0": 75.00000000000075, "1": null}, "pair_grows_k0_to_k1": null}
RC Delta_pair(k=0) mine [mm]: 75.0
RC Delta_pair(k=0) harness | mine: (75.00000000000075, 75.0, '3.41e-13')
NH/R k=0 converged (harness | mine): (True, True, True)
NH/R k=0 tag (harness | mine): ('none', 'none', True)
NH/R k=0 (yaw, roll) (harness | mine): ((0.0, 0.0), (0.0, 0.0))
NH/R k=0 max|RD.e2/e3 diff|: 0.0
NH/R k=0 Delta harness | mine [mm]: ([-0.0, 0.0, 111.92], [-0.0, 0.0, 111.92], 'max|diff| 1.14e-13')
NH/R k=0 d / wrist3 max|diff| [mm]: ('1.14e-13', '3.27e-13')
NH/R k=0 |dx| <= 2 mm + 0.05 d (harness values): True
NH/R k=1 converged (harness | mine): (True, True, True)
NH/R k=1 tag (harness | mine): ('none', 'none', True)
NH/R k=1 (yaw, roll) (harness | mine): ((0.0, 0.35), (0.0, 0.35))
NH/R k=1 max|RD.e2/e3 diff|: 0.0
NH/R k=1 Delta harness | mine [mm]: ([-0.0, 38.3771, 105.1346], [-0.0, 38.3771, 105.1346], 'max|diff| 0.00e+00')
NH/R k=1 d / wrist3 max|diff| [mm]: ('0.00e+00', '0.00e+00')
NH/R k=1 |dx| <= 2 mm + 0.05 d (harness values): True
NH/R k=1 sign(dy) (harness | mine | expected): (1, 1, 1)
NH pair block (harness): {"pair_mm": {"0": 75.00000000000038, "1": 107.31362522727069}, "pair_grows_k0_to_k1": true}
NH Delta_pair(k=0) mine [mm]: 75.0
NH Delta_pair(k=0) harness | mine: (75.00000000000038, 75.0, '1.42e-13')
NH Delta_pair(k=1) mine [mm]: 107.313625
NH Delta_pair(k=1) harness | mine: (107.31362522727069, 107.313625, '1.99e-13')
worst diffs: {'delta_mm': 2.1316282072803006e-13, 'd_mm': 2.2737367544323206e-13, 'wrist3_mm': 3.268496584496461e-13, 'RD': 0.0, 'pair_mm': 3.410605131648481e-13}
```

## Appendix C — `pz_r0iii_compare.py` (verbatim)
```python
"""pZ R0-iii comparison: the landed harness's R0iii block (report JSON) vs this desk's r0iii_{L,B,RC,NH}.json (addendum 9 expectation). argv: S REPORT"""
import json, sys, math, numpy as np
S, REP = sys.argv[1], sys.argv[2]
rep = json.load(open(REP)); blk = rep["R0iii"]; mine = {x: json.load(open(f"{S}/r0iii_{x}.json")) for x in ("L", "B", "RC", "NH")}
def ent(j, k): return next(e for e in j["entries"] if e["k"] == k)
out = {}; worst = {"delta_mm": 0.0, "d_mm": 0.0, "wrist3_mm": 0.0, "RD": 0.0, "pair_mm": 0.0}
def cmp_side(h, m, label):
    for k in (0, 1):
        hk, mk = h[str(k)], ent(m, k)
        out[f"{label} k={k} converged (harness | mine)"] = (hk["converged"], mk["converged"], hk["converged"] == mk["converged"])
        out[f"{label} k={k} tag (harness | mine)"] = (hk["stop_cause_tag"], mk["tag"], hk["stop_cause_tag"] == mk["tag"])
        out[f"{label} k={k} (yaw, roll) (harness | mine)"] = ((hk["yaw"], hk["roll"]), (mk["yaw"], mk["roll"]))
        dRD = max(float(np.abs(np.array(hk["roll_axis_RD_e2"]) - np.array(mk["RD_e2"])).max()), float(np.abs(np.array(hk["approach_RD_e3"]) - np.array(mk["RD_e3"])).max())); worst["RD"] = max(worst["RD"], dRD)
        out[f"{label} k={k} max|RD.e2/e3 diff|"] = dRD
        if hk["converged"] and mk["converged"]:
            dd = float(np.abs(np.array(hk["delta_mm"]) - np.array(mk["Delta_mm"])).max()); worst["delta_mm"] = max(worst["delta_mm"], dd)
            d3 = float(np.abs(np.array(hk["wrist3_delta_mm"]) - np.array(mk["Delta_wrist3_mm"])).max()); worst["wrist3_mm"] = max(worst["wrist3_mm"], d3)
            dn = abs(hk["d_mm"] - mk["d_mm"]); worst["d_mm"] = max(worst["d_mm"], dn)
            out[f"{label} k={k} Delta harness | mine [mm]"] = ([round(v, 4) for v in hk["delta_mm"]], [round(v, 4) for v in mk["Delta_mm"]], f"max|diff| {dd:.2e}")
            out[f"{label} k={k} d / wrist3 max|diff| [mm]"] = (f"{dn:.2e}", f"{d3:.2e}")
            out[f"{label} k={k} |dx| <= 2 mm + 0.05 d (harness values)"] = abs(hk["delta_mm"][0]) <= 2.0 + 0.05 * hk["d_mm"]
            if k == 1: out[f"{label} k=1 sign(dy) (harness | mine | expected)"] = (hk["sign_delta_y"], mk["sign_Delta_y"], -1 if label.startswith("L") else 1)
cmp_side(blk["L"], mine["L"], "L")
for mn in ("B", "RC", "NH"):
    cmp_side(blk["models"][mn]["R"], mine[mn], f"{mn}/R")
    hp = blk["models"][mn].get("pair", {}) if isinstance(blk["models"][mn].get("pair"), dict) else {k: v for k, v in blk["models"][mn].items() if k != "R"}
    out[f"{mn} pair block (harness)"] = json.dumps(hp)[:300]
    # my pair values from my JSONs: |w_R - w_L| per k
    for k in (0, 1):
        eL, eR = ent(mine["L"], k), ent(mine[mn], k)
        if eL["converged"] and eR["converged"]:
            mp = float(np.linalg.norm(np.array(eR["w_mm"]) - np.array(eL["w_mm"])))
            hv = None
            for key in ("Delta_pair_mm", "delta_pair_mm", "pair_mm"):
                if isinstance(hp, dict) and key in hp and isinstance(hp[key], dict): hv = hp[key].get(str(k)); break
            out[f"{mn} Delta_pair(k={k}) mine [mm]"] = round(mp, 6)
            if hv is not None: worst["pair_mm"] = max(worst["pair_mm"], abs(hv - mp)); out[f"{mn} Delta_pair(k={k}) harness | mine"] = (hv, round(mp, 6), f"{abs(hv-mp):.2e}")
out["worst diffs"] = worst
for k, v in out.items(): print(f"{k}: {v}")
```

## Provenance
Blobs by `git cat-file`; archive of `fedb5bef08` under the scratchpad; the as-landed procedure = `pz_r0_exec.py` (appendix H of the R0 pre-registration, sha `0916601f5c4cd73d…`) with the dump copy (bytes = the untracked `_gen/_steps_cell_full.xml`, sha `4158e4e638e9b0fc…`); the compare tools = appendix J of addendum 8 (`pz_r0_compare_v4.py`) and appendix C here. Zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-438.
