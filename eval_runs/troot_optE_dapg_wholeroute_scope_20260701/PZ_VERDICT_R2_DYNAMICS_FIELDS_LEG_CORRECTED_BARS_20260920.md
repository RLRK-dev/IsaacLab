# pZ — verdict on leg R2 under the corrected bars (pre-registration addendum @ `027174f94d`; p4 m-p4-300; p11 §17.20 @ `7b61c9ae2f`): the same instrument re-run once, 27 of 27 barred comparisons pass on B, the three controls fail where they must

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 15:01:42 JST on m-p18-454 (p4: 「pZ = 訂正事前登録 → 同一計器の再走行 → verdict」; acceptance on 「28/28 ＋ 対照 3 種が落ちる所で落ちる」). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted**: acceptance is p4's word. This verdict supersedes the row verdicts of `PZ_VERDICT_R2_DYNAMICS_FIELDS_LEG_20260920.md` @ `381713ca34` for the six re-barred comparisons and leaves its measurements, disclosures and holes standing.

**Order of existence**: p11 §17.20 `7b61c9ae2f` (14:57:18) ≺ corrected pre-registration `027174f94d` (14:59:34 JST; sha256 `97dd1621300e5fd1…`; bars, expectation and the three instrument shas fixed; re-run outputs asserted absent) ≺ re-run `pz_r2.py` (14:59:35) ≺ `pz_r2_inertia_v2.py` (14:59:36) ≺ `pz_r2_judge.py` (15:00:06) ≺ this verdict. HEAD at writing `91cdc8d897`; objects = the six blobs pinned in the pre-registration (re-asserted in the addendum); archive of `792e62e460`. **Run 0**; `mj_step` = 0; driver not imported. **Stop-cause tag: none.**

**The instrument is the same**: `pz_r2.py` sha256 `3f6dab44b655d64bd38d23696fe5aeadaddffa6aa3a92b31cb3e6b1d71ace5f0` (= appendix A of the pre-registration; p4's 「計器 sha 不変」), and its re-run reproduces the first run **exactly**: per-field `max` and `fail` counts identical on all 6 comparisons × fields (differing pairs = 0). The two registered additions: `pz_r2_inertia_v2.py` sha256 `6609eacef7fa3f1a5280326f4bf83860fb836c972c6edf04c5001c96d77aa363` (appendix B of the addendum) and `pz_r2_judge.py` — **registered as sha256 `20d823d0a4866a993733fd1c4301618ab52e76a12ebc9b7cb4c223fcc470dc2d` (v1), which stopped at its print line with `'m'?` before printing anything; the judgment logic (bars, fields, counts) was not reached. Corrected in place to sha256 `2b8b78e43752fc620aa7251348741f87ca9337db1c7beb4012a6ed8782cdc6dc` (v2) by rewriting that one print line — the diff is appendix C, two lines, no bar or field touched — and run once.** Disclosed here rather than re-registered: the change is in the formatting of the output, not in what is judged; if p4 wants the v2 sha under a pre-registration first, this desk re-registers and re-runs (deterministic).

## Verdict (judge output, appendix A; counts = 26 barred `pz_r2.py` fields + the tensor row = 27 barred comparisons per composed comparison; `body_iquat` and `−a` are the two reported-only rows; the arm single asset has no actuator/tendon/equality rows, hence 18)

| comparison | barred comparisons passing | failing fields (corrected bars) | reported-only |
|---|---|---|---|
| **L vs B (the leg)** | **27/27** | none | `body_iquat` residual 2.0 on 3 bodies (`g_base_mount`, `g_left/right_silicone_pad`; their tensor differences 0.0e+00, 0.0e+00, 0.0e+00); `−a` fails on the 8 hand joints (axes `(1,0,0)`) |
| NH (stock hand) — must fail on hand chirality | 23/27 | `body_ipos (Mx, exact)`, `body_quat (Mx.R.Mx)`, `geom_pos (Mx, exact)`, `inertia tensor (Mx, <= 1e-9)` | tensor row: 2.86e-07 kg·m² at `g_base_mount` (1 body; reported per §17.20, listed by the judge as failing the bar) |
| RC (stock arm on the right mount) — must fail on arm chirality | 21/27 | `body_pos (Mx, exact)`, `body_ipos (Mx, exact)`, `body_quat (Mx.R.Mx)`, `jnt_axis (-A.a, exact)`, `geom_pos (Mx, exact)`, `inertia tensor (Mx, <= 1e-9)` | tensor row: 6.43e-02 kg·m² at `a_upper_arm_link` (7 bodies) |
| B′ (one hand mass +1e-7) — must fail on exactly `body_mass` | 26/27 | `body_mass (exact)` (1 pair, `g_right_follower`) | tensor unchanged from B (1.04e-10; the inertia is explicit, so a mass edit does not move it) |
| arm stock vs mirrored (single asset) | 18/18 | none | `body_iquat` max 9.3e-11 (no sign flip on the arm); tensor 1.04e-10 |
| hand stock vs mirrored (single asset) | 27/27 | none | `body_iquat` 2.0 on the same 3 bodies; tensor 4.50e-14 |

**Reading (fact, not design)**: under the bars p11 corrected in §17.20 — 1e-12 m on the five compile-time fields, the frame-independent inertia tensor at 1e-9 kg·m² in place of `body_iquat` — every field of §10 R2 on the composed models and on the single assets passes, and the assets are the mirror of each other at the asset level (masses, inertias, positions, frames, joint ranges/axes/stiffness/springs, geom sizes/positions/contact parameters, the hand actuator, tendon and equalities). The controls keep their discriminating fields: NH on `body_ipos`/`body_quat`/`geom_pos` (7.2e-4 m, 2.0), RC on `body_pos`/`body_ipos`/`body_quat`/`jnt_axis`/`geom_pos` (1.3 m), B′ on `body_mass` alone. The margin between the noise (≤ 2.8e-17 m) and the smallest control failure (1.7e-8 m) is the one §17.20 states.

## What this leg does not show (holes) — unchanged from `381713ca34`
- Fields only; nothing dynamic is exercised; mesh geom quaternions excluded by design; driver-injected actuator/armature/damping values are p4's text reading (R2-9), effective values are #69's R4.

## Appendix A — `pz_r2_judge.py` output (verbatim; v2 sha256 2b8b78e43752fc620aa7251348741f87ca9337db1c7beb4012a6ed8782cdc6dc)
```text
[r2-judge] composed_L_vs_B: 27/27 barred comparisons pass; failed = []; reported-only = {body_iquat (Mx.R.Mx): (3, 2.00e+00), jnt_axis (-a, reported): (8, 2.00e+00)}; inertia tensor worst 1.04e-10
[r2-judge] composed_L_vs_NH (negative: stock hand): 23/27 barred comparisons pass; failed = [('body_ipos (Mx, exact)', '7.21e-04', 6, 20), ('body_quat (Mx.R.Mx)', '2.00e+00', 1, 20), ('geom_pos (Mx, exact)', '7.21e-04', 26, 38), ('inertia tensor (Mx, <= 1e-9)', '2.86e-07', 1, 20)]; reported-only = {body_iquat (Mx.R.Mx): (9, 2.00e+00), jnt_axis (-a, reported): (8, 2.00e+00)}; inertia tensor worst 2.86e-07
[r2-judge] composed_L_vs_RC (negative: stock arm on the right mount): 21/27 barred comparisons pass; failed = [('body_pos (Mx, exact)', '1.29e+00', 3, 20), ('body_ipos (Mx, exact)', '4.57e-01', 12, 20), ('body_quat (Mx.R.Mx)', '2.00e+00', 1, 20), ('jnt_axis (-A.a, exact)', '2.00e+00', 6, 14), ('geom_pos (Mx, exact)', '5.73e-01', 30, 38), ('inertia tensor (Mx, <= 1e-9)', '6.43e-02', 7, 20)]; reported-only = {body_iquat (Mx.R.Mx): (15, 2.00e+00), jnt_axis (-a, reported): (14, 2.00e+00)}; inertia tensor worst 6.43e-02
[r2-judge] composed_L_vs_Bperturbed (negative: one hand mass +1e-7): 26/27 barred comparisons pass; failed = [('body_mass (exact)', '1.00e-07', 1, 20)]; reported-only = {body_iquat (Mx.R.Mx): (3, 2.00e+00), jnt_axis (-a, reported): (8, 2.00e+00)}; inertia tensor worst 1.04e-10
[r2-judge] arm_stock_vs_mirrored (single asset): 18/18 barred comparisons pass; failed = []; reported-only = {body_iquat (Mx.R.Mx): (0, 9.26e-11), jnt_axis (-a, reported): (0, 0.00e+00)}; inertia tensor worst 1.04e-10
[r2-judge] hand_stock_vs_mirrored (single asset): 27/27 barred comparisons pass; failed = []; reported-only = {body_iquat (Mx.R.Mx): (3, 2.00e+00), jnt_axis (-a, reported): (8, 2.00e+00)}; inertia tensor worst 4.50e-14
{"composed_L_vs_B": {"passed": 27, "barred": 27, "failed_fields": []}, "composed_L_vs_NH (negative: stock hand)": {"passed": 23, "barred": 27, "failed_fields": ["body_ipos (Mx, exact)", "body_quat (Mx.R.Mx)", "geom_pos (Mx, exact)", "inertia tensor (Mx, <= 1e-9)"]}, "composed_L_vs_RC (negative: stock arm on the right mount)": {"passed": 21, "barred": 27, "failed_fields": ["body_pos (Mx, exact)", "body_ipos (Mx, exact)", "body_quat (Mx.R.Mx)", "jnt_axis (-A.a, exact)", "geom_pos (Mx, exact)", "inertia tensor (Mx, <= 1e-9)"]}, "composed_L_vs_Bperturbed (negative: one hand mass +1e-7)": {"passed": 26, "barred": 27, "failed_fields": ["body_mass (exact)"]}, "arm_stock_vs_mirrored (single asset)": {"passed": 18, "barred": 18, "failed_fields": []}, "hand_stock_vs_mirrored (single asset)": {"passed": 27, "barred": 27, "failed_fields": []}}
```

## Appendix B — `pz_r2_inertia_v2.py` output (verbatim; sha256 6609eacef7fa3f1a5280326f4bf83860fb836c972c6edf04c5001c96d77aa363)
```text
[r2-I] composed_L_vs_B           : bodies 20, inertia tensor under Mx worst 1.042e-10 kg m^2 at a_upper_arm_link; bodies > 1e-9: 0; iquat residuals > 1e-8: 3
[r2-I] composed_L_vs_NH          : bodies 20, inertia tensor under Mx worst 2.856e-07 kg m^2 at g_base_mount; bodies > 1e-9: 1; iquat residuals > 1e-8: 9
[r2-I] composed_L_vs_RC          : bodies 20, inertia tensor under Mx worst 6.427e-02 kg m^2 at a_upper_arm_link; bodies > 1e-9: 7; iquat residuals > 1e-8: 15
[r2-I] composed_L_vs_Bperturbed  : bodies 20, inertia tensor under Mx worst 1.042e-10 kg m^2 at a_upper_arm_link; bodies > 1e-9: 0; iquat residuals > 1e-8: 3
[r2-I] arm_stock_vs_mirrored     : bodies  6, inertia tensor under Mx worst 1.042e-10 kg m^2 at upper_arm_link; bodies > 1e-9: 0; iquat residuals > 1e-8: 0
[r2-I] hand_stock_vs_mirrored    : bodies 14, inertia tensor under Mx worst 4.504e-14 kg m^2 at left_spring_link; bodies > 1e-9: 0; iquat residuals > 1e-8: 3
```

## Appendix C — the judgment layer's one-line correction (v1 sha256 20d823d0a4866a993733fd1c4301618ab52e76a12ebc9b7cb4c223fcc470dc2d → v2 sha256 2b8b78e43752fc620aa7251348741f87ca9337db1c7beb4012a6ed8782cdc6dc; `diff` verbatim); v1's stop: `NameError: name 'mx' is not defined. Did you mean: 'm'?`
```diff
23c23,24
<     print(f"[r2-judge] {cmp_}: {passed}/{barred} barred comparisons pass; failed = {[(f, f'{m:.2e}', nf, n) for f, m, nf, n in failed]}; reported-only = {{k: (nf, f'{mx:.2e}') for k, (nf, mx) in reported.items()}}; inertia tensor worst {it['worst']:.2e}")
---
>     rep_s = ", ".join(f"{k}: ({nf}, {mx:.2e})" for k, (nf, mx) in reported.items()); fail_s = [(f_, f"{m:.2e}", nf, n) for f_, m, nf, n in failed]
>     print(f"[r2-judge] {cmp_}: {passed}/{barred} barred comparisons pass; failed = {fail_s}; reported-only = {{{rep_s}}}; inertia tensor worst {it['worst']:.2e}")
```

## Provenance
The re-run's JSON/logs under the scratchpad (`r2_rerun.*`, `r2_inertia_v2.*`, `r2_judge.txt`, `r2_judge_v1_crash.txt`); the first run's `r2.json` kept for the identity check. Zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-454.

## Addendum (2026-09-20 15:05:51 JST) — the judgment layer re-run under its registered v2 sha (pre-registration addendum 2 @ `13707643a0`; p4 m-p4-302)

`pz_r2_judge.py` sha256 `2b8b78e43752fc620aa7251348741f87ca9337db1c7beb4012a6ed8782cdc6dc` (= the sha registered in addendum 2, committed 13707643a0 before this run) was run once more on the unchanged `r2_rerun.json` / `r2_inertia_v2.json`: the output `r2_judge_rerun.txt` is **byte-identical** to appendix A (`cmp` silent; sha256 of both = `54ef029392451c037019e424a973ce85e3f8cba249b18243cb50b2492f2ff777`). Every number of the table above therefore stands as the expectation p4 named; nothing differs. `pz_r2.py` and `pz_r2_inertia_v2.py` were not re-run (their outputs are the inputs; shas unchanged). Run 0; stop-cause tag: none.
