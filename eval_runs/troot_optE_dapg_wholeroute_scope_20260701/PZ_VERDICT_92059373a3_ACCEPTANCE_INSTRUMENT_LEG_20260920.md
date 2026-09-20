# pZ — verdict on the acceptance-instrument landing `92059373a3` (window W, p4's FULL form): rows 1-7 of the pre-registration @ `c401aa330a`, each judged against the object's own parent blob `0803ea391298`

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 11:28:46 JST on m-p18-426 (relay of p4 m-p4-288: predicate v2 = p4's FULL form; the order `caa742b8d3` adopted; p0 may land FULL from a clean worktree; pZ = W leg, run 0). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted** (Rs1 supplement b): this file is the leg; acceptance of the window is p4's word after it.

**The object** (all values below are command outputs, none typed): commit `92059373a3` — parent `aabae73074`, author date 2026-09-20 11:21:41 JST, `1 file changed, 15 insertions(+), 9 deletions(-)`, files touched = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_mirror_acceptance.py` only. `ur15_mirror_acceptance.py` blob `11ea985d8b19` (sha256 `4a2e3396059214409cd4e1746972a06a6cf8d501d21df754c1e1db31c5a7667b`, 248 lines). **Parent blob** `0803ea391298` (sha256 `dc473752a36fdf0074de895b75d037b0ed31cd51bf9ea107e80af5255e762b93`, 242 lines; last commit `38678f5946`). Commits touching the file after `38678f5946` = **1** (= the object): `92059373a3 2026-09-20 11:21:41 Point the mirror acceptance at the repo reference bundle and correct the limit rule`. HEAD at writing `bbd86d8449` (shared branch; other desks commit continuously).

**Where the leg ran**: a `git archive 92059373a3 -- p4_ur15_sim_20260727` extracted under this desk's scratchpad (`wt_92059373a3`; the script there has sha256 `4a2e3396059214409cd4e1746972a06a6cf8d501d21df754c1e1db31c5a7667b` = the landed blob). The shared tree was **not executed and not modified** by this desk. ⚠ The shared tree's copy of the file is **not the landed instrument**: `git diff 11ea985d8b19 -- <file>` = `1 file changed, 105 insertions(+), 77 deletions(-)` (worktree blob `1bb1e54463`: an SPDX header, a formatter reflow, and `REF_DIR` back at the `~/Downloads` path — the 09-07 tree-wide WIP overlay; p0 §8.61 @ `bbc26fbc1b` reports the same overlay and did not merge it). Anyone running `:236` in the shared tree runs that overlay, not `92059373a3`. **Run: 0** (no route run; the instrument is FK-only, `mj_step` = 0 by row 6). **Stop-cause tag: none** (the only stop in this leg is row 2's deliberate positive control).

## Verdict per row (rows as pre-registered @ `cd0d68bf8c`, row 1 re-pinned FULL @ `c401aa330a`)

| # | row | verdict | measured (instrument · output · where) |
|---|---|---|---|
| 1 | change set = p4's FULL form | **CONFIRMED** | `pz_acc_pred_v2.py` (sha256 `106b124b8be96dfc…`, appendix C of the prereg; `pz_d4_pred.py` v3 sha256 `0ba3c59b583b39d1…`) on (parent blob, landed blob): `PASS changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=ok`. Controls fired now on the same blobs: parent/parent `FAIL`, landed/landed `FAIL`. The landed blob is **byte-identical** to the FULL mock the nine pre-registered controls were fired on (`cmp` → identical; mock sha256 `4a2e339605921440…` = landed sha256), so appendix D of `c401aa330a` (FULL mock PASS; MIN, literal flip, stray statement, heading altered, absolute REF_DIR, comment outside the block → FAIL) applies to this exact content. Change sites in the landed blob: `:49` REF_DIR, `:220` `want = (lo_a, hi_a)`, `:207-208` heading, `:236-239` HONEST SCOPE (sites measured with grep -n on the landed blob; the diff parent→landed is appendix A) |
| 2 | REF_DIR opens the reference JSON | **CONFIRMED** | In the archive the record's line 2 resolves to `…/wt_92059373a3/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json`, whose sha256 = `20ac0935c707757c35a974f4c7adc9b9412ed18a04905f06b34dc76affa3990d` (= the 08-10 pin `20ac0935c707757c…`; tracked blob `6db65e349131` at `92059373a3`). **Positive control**: with that JSON renamed away the script stops with `FileNotFoundError`, rc 1 (appendix B run C) — the row can fail |
| 3 | the new rule discriminates (mock asymmetric ranges) | **CONFIRMED** | Appendix B of the prereg re-fired now under env7 mujoco: `old(a,good)=False new(a,good)=True | old(a,bad)=True new(a,bad)=False` → the old rule accepts the negated range (the defect) and rejects the same range; the new rule does the opposite. The landed code applies the new rule: `220:            want = (lo_a, hi_a)` / `221:            ok = abs(lo_b - want[0]) < 1e-9 and abs(hi_b - want[1]) < 1e-9` (parent had `214:            want = (-hi_a, -lo_a)`). On the real assets every range is symmetric, so this mock is the only place the row can fail — it did fail for the old rule |
| 4 | the 07-29 legs reproduce in a clean worktree | **CONFIRMED** | Run A (`YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45`, env7): control **48/48** (worst 0.0076 mm at main_route_high), test **48/48**, formula **48/48**, negative **0/48** (worst 1357.5480 mm at connector_insert), limit **all 6 joints consistent**, rc 0. Regenerated record = 147 lines vs the 07-29 blob's 147; `diff` line numbers = `2c2 136c136 147c147` — **exactly the set written down before the run** (disclosure below): line 2 = the resolved reference path, 136 = the LEG-limit heading, 147 = the HONEST-SCOPE sentence; every other line byte-identical. Run B (overrides unset = the C-2 defaults 0.28/70): control **0/48** (worst 241.0804 mm at connector_insert), test 0/48, formula 0/48, negative 0/48, limit 6/6, rc 1 — the 08-10 finding, expected, not a defect of this landing |
| 5 | the record file | **CONFIRMED** | `92059373a3` touches one file (the script); the tracked `UR15_MIRROR_ACCEPTANCE_20260729.txt` at `92059373a3` is blob `3c9640b805a6`, sha256 `c5229911315f57b59566bf3cf6b66a86895b73a5e617ce04e243c00205722b61` (last commit `38678f5946 2026-07-29 00:56`); the shared-tree copy has the same sha256 (`c5229911315f57b5…`, `git status` → `(clean)`) after this leg — the regeneration lived in the archive only (p4: 「再生成は archive 内の比較のみ」) |
| 6 | control invariance (`mj_step` = 0 before and after) | **CONFIRMED** | grep: `acc_parent_0803.py:0 acc_landed_11ea.py:0`; AST: `AST mj_step calls in acc_parent_0803.py: 0` / `AST mj_step calls in acc_landed_11ea.py: 0` |
| 7 | pins / no run | **CONFIRMED** | landed `92059373a3` blob `11ea985d8b19` sha256 `4a2e339605921440…`; parent blob `0803ea391298` sha256 `dc473752a36fdf00…`; predicate `106b124b8be96dfc…`; env7 `3.12.3 mujoco 3.11.0 numpy 2.3.1 scipy 1.17.0`; run 0; shared tree untouched by this desk |

**The observation of `cd0d68bf8c` (not a row)** — answered by FULL as the addendum predicted: the regenerated record now describes the rule the code applies (lines 136 and 147 of run A's record, appendix B).

## Collation of p0's §8.61 (`bbc26fbc1b`) against this desk's own measurements

| p0's claim | this desk |
|---|---|
| predicate v2 on (base blob, landed file) → PASS | CONFIRMED independently on the blobs pulled from git (row 1) |
| base/base FAIL; literal flip FAIL | CONFIRMED (parent/parent now; the literal-flip control on byte-identical content in `c401aa330a` appendix D) |
| `mj_step` occurrences 0 | CONFIRMED (row 6, grep + AST) |
| py_compile OK | CONFIRMED by execution (runs A/B completed) |
| landed blob == the §8.52 candidate (sha256 `4a2e3396…`) | CONFIRMED (`cmp` identical to this desk's mock built from the committed `acc_full.diff`) |
| the 48/48 · 48/48 · 48/48 · 0/48 · 6/6 numbers are the candidate's, the leg's numbers are pZ's | CONFIRMED and now measured on the landed commit (row 4, run A) |
| landing from a clean worktree, pathspec-limited, the shared-tree overlay not merged | consistent with what git shows (one file in the commit; the overlay still `M` in the tree); the worktree mechanics themselves are p0's record, not re-run here |

## Disclosure — row 4's expectation re-written for FULL before the run
The addendum @ `c401aa330a` said "rows 2-7 unchanged", but row 4's byte-identity clause ("identical except line 2") was the MIN-form wording: under FULL the two rewritten record lines differ by construction. The expectation was corrected and written to a file **before** the landed script was run (file timestamp precedes run A's start 11:26:16 JST):
```text
written 2026-09-20 11:25:53 JST before any run of the landed script
expected regenerated record at YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45 vs 07-29 blob c5229911315f57b5: differing lines = exactly {2 (reference path), 136 (LEG limit heading), 147 (HONEST SCOPE)}; same line count 147; control 48/48, test 48/48, formula 48/48, negative 0/48 worst 1357.5 mm, limit 6/6 consistent, rc 0.
expected at defaults (overrides unset): all four position legs 0/48 (control worst 241.1 mm), rc 1 (08-10 finding).
note: prereg addendum said rows 2-7 unchanged; row 4's 'except line 2' was the MIN-form wording — under FULL the two rewritten record lines differ by construction. This expectation replaces it and is written before measuring.
```
Measured: `2c2 136c136 147c147`, 147 lines — equal to the written set.

## What this leg does not show (holes)
- The limit leg on the **real** assets cannot tell the old rule from the new one (every stock range is symmetric; the record's own HONEST-SCOPE line says so). The discrimination lives only in row 3's mock; DDR 73's `:214` finding is closed by row 3, and the closure is p6's entry after p4's acceptance.
- Rows 2-4 measure what the 07-29 instrument measures: FK positions of the stock and mirrored arms against the reference's published positions at the record's mounting (0.22/45), plus the limit/axis pairs. They do not judge the mirrored asset beyond that (R1/R1′/R2 are the next legs in p4's adopted order), and nothing here is a run or a physical-validity judgment (Rs1's court).
- The C-2 defaults (0.28/70) still give 0/48 on every position leg (run B): the 08-10 finding that the C-2 mounting is not the reference's, unchanged by this landing and not a defect of it.
- The shared-tree overlay of this file (`1 file changed, 105 insertions(+), 77 deletions(-)` vs the landed blob) is reported, not judged: it is the 09-07 WIP, not p0's landing, and not this desk's to touch.

## Appendix A — the landing diff, parent blob → landed blob (`git diff 0803ea391298 11ea985d8b19`, verbatim)
```diff
diff --git a/0803ea391298eb7f2c0e833c7df62cf9c468fb6b b/11ea985d8b19920ea7e9eade679132b3b55c1601
index 0803ea3912..11ea985d8b 100644
--- a/0803ea391298eb7f2c0e833c7df62cf9c468fb6b
+++ b/11ea985d8b19920ea7e9eade679132b3b55c1601
@@ -46,7 +46,7 @@ sys.path.insert(0, str(HERE))
 
 from ur15_cell_spec import SHOULDER_HEIGHT, TILT, YOKE_SPREAD  # noqa: E402
 
-REF_DIR = Path("/home/rlrk/Downloads/ur15-dual-arm-cell")
+REF_DIR = HERE / "reference" / "ur15-dual-arm-cell"   # the repo copy (was ~/Downloads, absent since); Rs1 Q3/Q9
 REF_JSON = REF_DIR / "ur15-dual-arm-cell.json"
 J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
       "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
@@ -196,10 +196,16 @@ def main() -> int:
     # --- the limit leg, which the position legs cannot see -----------------------------------
     # p5 -163, unconditional: joint LIMITS do not enter FK, so no amount of tool-landing evidence
     # touches them, and the reference's poses reach |q| = 5.63 rad against a 6.283 rad limit --
-    # they never come near it, so a wrong limit passes in silence.  Convention #2 says the axis
-    # and the limit inverted together, atomically; that is exactly [lo, hi] -> [-hi, -lo].
+    # they never come near it, so a wrong limit passes in silence.  ⛔ The rule this leg tested
+    # from 07-29 to 09-16 was [lo, hi] -> [-hi, -lo] -- the SIGN-FLIP convention (q_R = -q_L).  The
+    # mirror build does not use it: it flips the joint AXIS and keeps q (make_ko_mirror.py:16-19;
+    # PZ-216 measured q_R = q_L to 2.2e-15), and under M R(n,q) M = R(-Mn, q) the range that goes
+    # with a flipped axis and the same q is the SAME [lo, hi].  Byte-identical ranges are the
+    # requirement (DDR 73; three desks read it: p11 v3 sec 5 D6, pZ PZ-216, p0 sec 8.50).  The old
+    # rule could not fail on these assets because every stock range is symmetric.
     out.append("")
-    out.append("=== LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [-hi,-lo] ===")
+    out.append("=== LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [lo,hi] "
+               "(axis flipped, q kept; the 07-29 rule [-hi,-lo] was the sign-flip convention) ===")
     out.append("    ⛔ Position legs are blind here: limits are not in the kinematics, and the")
     out.append("    reference's largest |joint| is far inside the range, so a wrong limit is silent.")
     lim_ok, lim_n = True, 0
@@ -211,7 +217,7 @@ def main() -> int:
             ja, jb = a.joint(name), b.joint(name)
             lo_a, hi_a = float(ja.range[0]), float(ja.range[1])
             lo_b, hi_b = float(jb.range[0]), float(jb.range[1])
-            want = (-hi_a, -lo_a)
+            want = (lo_a, hi_a)
             ok = abs(lo_b - want[0]) < 1e-9 and abs(hi_b - want[1]) < 1e-9
             ax_a, ax_b = a.jnt_axis[ja.id], b.jnt_axis[jb.id]
             ax_ok = bool(np.allclose(ax_b, -ax_a))
@@ -227,10 +233,10 @@ def main() -> int:
     out.append(f"  -- limit: {'all ' + str(lim_n) + ' joints consistent' if lim_ok else 'MISMATCH'}"
                f" (axis inversion checked alongside, which is the other half of the atomic pair)")
     if sym_all:
-        out.append("  ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [-hi,-lo] "
-                   "equals [lo,hi] and this leg CANNOT fail on these assets.  It is a standing "
-                   "check for the day a range is not symmetric -- today it confirms the axes are "
-                   "inverted and records that the limits had nothing asymmetric to preserve.")
+        out.append("  ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [lo,hi] and the "
+                   "sign-flip rule's [-hi,-lo] coincide and this leg CANNOT tell the two rules apart "
+                   "on these assets.  It is a standing check for the day a range is not symmetric -- "
+                   "today it confirms the axes are inverted and the ranges are byte-identical.")
 
     text = "\n".join(out) + "\n"
     (HERE / "UR15_MIRROR_ACCEPTANCE_20260729.txt").write_text(text)
```

## Appendix B — instrument outputs (verbatim, this session)
```text
## row 1 — pz_acc_pred_v2.py (sha256 106b124b8be96dfc365e062e469fa0174722de1ffe4b856ee6d97c441a7e4977)
parent/landed  PASS changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=ok
parent/parent  FAIL changed=[] fine=["REF_DIR not HERE-relative reference/ur15-dual-arm-cell: names={'Path'} consts=['/home/rlrk/Downloads/ur15-dual-arm-cell']", 'main() differing statements != the FULL three: []']
landed/landed  FAIL changed=[] fine=['main() differing statements != the FULL three: []']
cmp acc_landed_11ea.py acc_full_mock.py -> identical

## row 3 — mock-asset control (prereg appendix B verbatim, /home/rlrk/env_isaaclab7/bin/python)
old(a,good)=False new(a,good)=True | old(a,bad)=True new(a,bad)=False
landed rule lines:
220:            want = (lo_a, hi_a)
221:            ok = abs(lo_b - want[0]) < 1e-9 and abs(hi_b - want[1]) < 1e-9
parent rule line:
214:            want = (-hi_a, -lo_a)

## row 6
acc_parent_0803.py:0
acc_landed_11ea.py:0
AST mj_step calls in acc_parent_0803.py: 0
AST mj_step calls in acc_landed_11ea.py: 0

## run A — archive wt_92059373a3, YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45, rc 0 (key lines, line-numbered in the log)
2: reference : /tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/wt_92059373a3/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json
4: mounting  : YOKE_SPREAD=0.22  TILT=45.0000 deg  SHOULDER_HEIGHT=1.5299999999999998  (imported from ur15_cell_spec, not retyped)
37: -- control: 48/48 position pairs land within 1.0 mm (worst 0.0076 mm at main_route_high)
65: -- test: 48/48 position pairs land within 1.0 mm (worst 0.0076 mm at main_route_high)
93: -- formula: 48/48 position pairs land within 1.0 mm (worst 0.0076 mm at main_route_high)
121: -- negative: 0/48 position pairs land within 1.0 mm (worst 1357.5480 mm at connector_insert)
131:   The test leg IS the acceptance test.  Control says whether my mounting and FK reproduce the reference at all -- without it, a passing test leg could be two errors cancelling.  Formula is the reference's own non-mirrored route, and its size is the difference the mirrored asset removes.
136: === LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [lo,hi] (axis flipped, q kept; the 07-29 rule [-hi,-lo] was the sign-flip convention) ===
146:   -- limit: all 6 joints consistent (axis inversion checked alongside, which is the other half of the atomic pair)
147:   ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [lo,hi] and the sign-flip rule's [-hi,-lo] coincide and this leg CANNOT tell the two rules apart on these assets.  It is a standing check for the day a range is not symmetric -- today it confirms the axes are inverted and the ranges are byte-identical.
-- limit block of the regenerated record (lines 136-147):
=== LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [lo,hi] (axis flipped, q kept; the 07-29 rule [-hi,-lo] was the sign-flip convention) ===
    ⛔ Position legs are blind here: limits are not in the kinematics, and the
    reference's largest |joint| is far inside the range, so a wrong limit is silent.
  ur15_base.xml  vs  ur15_base_mirrored.xml
    shoulder_pan_joint     stock[-6.283190 +6.283190] -> want[-6.283190 +6.283190]  got[-6.283190 +6.283190]  ok; axis inverted   ⚠ range is symmetric, so this row would also pass unchanged
    shoulder_lift_joint    stock[-6.283190 +6.283190] -> want[-6.283190 +6.283190]  got[-6.283190 +6.283190]  ok; axis inverted   ⚠ range is symmetric, so this row would also pass unchanged
    elbow_joint            stock[-3.141590 +3.141590] -> want[-3.141590 +3.141590]  got[-3.141590 +3.141590]  ok; axis inverted   ⚠ range is symmetric, so this row would also pass unchanged
    wrist_1_joint          stock[-6.283190 +6.283190] -> want[-6.283190 +6.283190]  got[-6.283190 +6.283190]  ok; axis inverted   ⚠ range is symmetric, so this row would also pass unchanged
    wrist_2_joint          stock[-6.283190 +6.283190] -> want[-6.283190 +6.283190]  got[-6.283190 +6.283190]  ok; axis inverted   ⚠ range is symmetric, so this row would also pass unchanged
    wrist_3_joint          stock[-6.283190 +6.283190] -> want[-6.283190 +6.283190]  got[-6.283190 +6.283190]  ok; axis inverted   ⚠ range is symmetric, so this row would also pass unchanged
  -- limit: all 6 joints consistent (axis inversion checked alongside, which is the other half of the atomic pair)
  ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [lo,hi] and the sign-flip rule's [-hi,-lo] coincide and this leg CANNOT tell the two rules apart on these assets.  It is a standing check for the day a range is not symmetric -- today it confirms the axes are inverted and the ranges are byte-identical.

## run A record vs the 07-29 blob (sha256 c5229911315f57b59566bf3cf6b66a86895b73a5e617ce04e243c00205722b61)
wc -l: 07-29 blob 147 / regenerated 147
2c2
< reference : /home/rlrk/Downloads/ur15-dual-arm-cell/ur15-dual-arm-cell.json
---
> reference : /tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/wt_92059373a3/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json
136c136
< === LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [-hi,-lo] ===
---
> === LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [lo,hi] (axis flipped, q kept; the 07-29 rule [-hi,-lo] was the sign-flip convention) ===
147c147
<   ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [-hi,-lo] equals [lo,hi] and this leg CANNOT fail on these assets.  It is a standing check for the day a range is not symmetric -- today it confirms the axes are inverted and records that the limits had nothing asymmetric to preserve.
---
>   ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [lo,hi] and the sign-flip rule's [-hi,-lo] coincide and this leg CANNOT tell the two rules apart on these assets.  It is a standing check for the day a range is not symmetric -- today it confirms the axes are inverted and the ranges are byte-identical.

## run B — overrides unset (C-2 defaults), rc 1 (key lines)
4: mounting  : YOKE_SPREAD=0.28  TILT=70.0000 deg  SHOULDER_HEIGHT=1.5299999999999998  (imported from ur15_cell_spec, not retyped)
37: -- control: 0/48 position pairs land within 1.0 mm (worst 241.0804 mm at connector_insert)
65: -- test: 0/48 position pairs land within 1.0 mm (worst 534.8151 mm at clip_seat)
93: -- formula: 0/48 position pairs land within 1.0 mm (worst 534.8157 mm at clip_seat)
121: -- negative: 0/48 position pairs land within 1.0 mm (worst 1637.8629 mm at connector_insert)
131:   The test leg IS the acceptance test.  Control says whether my mounting and FK reproduce the reference at all -- without it, a passing test leg could be two errors cancelling.  Formula is the reference's own non-mirrored route, and its size is the difference the mirrored asset removes.
146:   -- limit: all 6 joints consistent (axis inversion checked alongside, which is the other half of the atomic pair)

## run C — row-2 positive control: reference JSON renamed away, rc 1 (last lines)
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/wt_92059373a3/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json'

(JSON restored; sha256 20ac0935c707757c35a974f4c7adc9b9412ed18a04905f06b34dc76affa3990d)

## environment
3.12.3 mujoco 3.11.0 numpy 2.3.1 scipy 1.17.0
```

## Provenance
Blobs read with `git cat-file` / `git show`; the leg executed only inside the `git archive` of `92059373a3` under the scratchpad; the shared tree's tracked record and script were not written by this desk (`git status` on the record = `(clean)`; the script's `M` is the pre-existing overlay). Zero tracked-content modifications by pZ other than this file. Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; the hub instruction is m-p18-426.
