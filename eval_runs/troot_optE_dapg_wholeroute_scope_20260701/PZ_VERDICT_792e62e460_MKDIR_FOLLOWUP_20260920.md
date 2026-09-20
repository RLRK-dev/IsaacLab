# pZ — verdict on the instrument follow-up `792e62e460` (`ur15_gripper_mirror_acceptance.py`: create `_gen/` before the record write; p4 m-p4-293 via m-p18-439), judged against its own parent blob `ad1d80d49f24`

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 14:39:18 JST (p4 item 37: the `_gen/` stop found in the R1′ leg = 「別の小さな計器 follow-up・§7.2 宣言の前・R1′ の条件ではない」; chain state: 「mkdir follow-up（p0 → pZ rc 0 → 当卓）」). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted.**

**The object**: commit `792e62e460` (author date 14:27:48 JST, parent `dd05fd3051`, one file, +1/−0): blob `ad1d80d49f24` → `f1909891539c`; commits touching the file after it = **0**; HEAD at writing `6a73dc3aa4`. The added line, verbatim (landed `:186`, immediately before the record write):
```diff
+    (HERE / "_gen").mkdir(parents=True, exist_ok=True)   # p4 m-p4-293: the dir is untracked and absent in a clean checkout
```

## Rows (this desk's, fixed by the finding in `PZ_VERDICT_R1P_HAND_ON_ARM_LEG_20260920.md` row d and its stop-cause report)

| # | row | verdict | measured |
|---|---|---|---|
| 1 | change set = one inserted statement in `main()`, nothing else | **CONFIRMED** | `pz_r0iii_pred.py` (the additions-only predicate of addendum 9, generic; sha256 `0a8a4aa6eb75c050…`) on (parent, landed): `PASS main(): inserted=1 dict_extended=0; top-level new defs/constants=0`; parent/parent: `FAIL main(): nothing added (not a landing)`; diff = 1 added / 0 removed lines |
| 2 | the stop is gone in a clean checkout | **CONFIRMED** | `git archive 792e62e460` under the scratchpad, `_gen/` **absent** before the run (checked), no directory created by this desk: **rc 0**, record written, `VERDICT: PASS` |
| 3 | the legs' numbers unchanged | **CONFIRMED** |   TEST (mirrored asset on the right): 192/192 geom-instances hold (worst Hausdorff 0.000041 mm)|  NEGATIVE (LEFT asset on the right -- the rotated-copy defect; MUST fail): 0/192 geom-instances hold (worst Hausdorff 135.377130 mm)|  VERTEX SPOT CHECK (spring_link, file-level): baked == A x original, Hausdorff 0.000e+00 m over 5088 verts: True|VERDICT: PASS  (test holds: True; negative fails as it must: True; vertices: True; denominator 192 geom-instances)| — identical to the R1′ leg's second run; the regenerated record's sha256 `92fad9158f708a4d…` **equals** the one produced on `92059373a3` after this desk's manual `mkdir` (`92fad9158f708a4d…`): the line changes nothing but the directory's existence |
| 4 | control invariance / no run | **CONFIRMED** | the script is `mj_kinematics`-only by its own code (unchanged); `mj_step` tokens in the file = 0; run 0 |
| 5 | the tracked 07-29 record and window W untouched | **CONFIRMED** | one file in the commit; `ur15_mirror_acceptance.py` (window W) has no `_gen` reference (p4 item 37's check, re-read here: 0 occurrences) |

**Stop-cause tag: none** (the calibration stop reported in the R1′ leg is closed by this line; nothing else stopped).

## Provenance
Blobs by `git cat-file`; the run in the `git archive` of `792e62e460` only (`mkdir_fu_run.log`); zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-439 (p4 m-p4-293) as relayed in the hub's records.
