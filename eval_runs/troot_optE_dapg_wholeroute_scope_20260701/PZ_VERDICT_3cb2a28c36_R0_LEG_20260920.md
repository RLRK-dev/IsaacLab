# pZ — verdict on the R0 harness `3cb2a28c36` (window R0, follow-up 2): convergence only, executed by this desk from a clean archive

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 08:54:50 JST on m-p18-393 (p4 m-p4-281: "pZ = row 4 再 pin → leg on 3cb2a28c36"). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. Authorization for execution = Rs1 Q1 verbatim 「認可する。p0が作り、pZが独立に検証・実行する。」 (scope: no physics step, no driver import, convergence only).
**Pre-registration** = `PZ_R0_CONVERGENCE_LEG_PREREG_20260916.md` rows 1-11, 1′, addenda 2-7 (latest `3ea663a5b4`; row 4 in the `:2812` form per v3 §17.7 @ `7427c1764c`; p4's condition and the disclosure line in addendum 7). **Object** = commit `3cb2a28c36` (author 2026-09-20 08:34:14 JST, parent `332df052d7`), file `p4_ur15_sim_20260727/r0_convergence_harness.py`, +154/−53, blob `77f952ab31ce` (sha256 `c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998`, 1,174 lines); its previous blob `0163e36e5187` @ `ffa612ea33`. Driver blobs the copies are judged against: `84a372439c59` @ `96e9ece175` and `d2bc133e1320` @ `3370f7a872`. At writing: HEAD `b7e58dc0e7`, harness commits after `3cb2a28c36` = 0, driver commits after `96e9ece175` = 0.

## Verdict in one paragraph

**The harness as landed stops at its own instrument on the pre-registered dump path** (exit 2, tag 「instrument calibration stop」) before solving anything: it loads the cell dump with `mujoco.MjModel.from_xml_path`, and the dump names the eight ko-hand meshes by bare basename (`follower.stl` …), which MuJoCo resolves relative to the dump's directory `_gen/`, where no STL exists. That is a loader limitation, not a controller failure (Rs1 supplement a). **With the same dump bytes (sha256 identical) placed beside its eight meshes and passed by `--dump`, the unchanged harness runs to exit 0**: no physics step (my counter 0 = its counter 0; the injected-step control reads 1 = 1), no driver module imported, AXFIX per side within 3.8e-15 of the banked expectation, §17.7's two target paths agree to 1.7e-16 with the links and the literal, **L 17/17, R 17/17 converged, "L converges and R does not" = 0 rows, §11 STOP not fired**, and every row equals my independent instrument row for row (flags, candidate counts, `pe` ≤ 7.6e-13 mm, `q` ≤ 5.0e-10 rad). Claim carried: **収束のみ／衝突・把持・動的追従は未証明**. "B is right" is not decided by this leg (addendum 3's finding stands, not re-measured). Acceptance is p4's word after this leg; p4 also requires p11's §10 and §17.7-citation corrections first.

## Rows (pre-registered) against `3cb2a28c36`

| # | row | result | measurement |
|---|---|---|---|
| 1 / 1′ | copy fidelity + negative control | **CONFIRMED** | 17 defs raw-`ast.dump`-equal to **both** driver blobs: the 14-function closure + `_own_bodies` + `_measure_axfix` + **`cable_at`** (`:912-919` ↔ `:1221-1228`). Negative control: the harness's `solve_ik` with `0.002 → 0.003` reads **unequal** (alive) |
| 1′ | the 30-global binding | **CONFIRMED (32/32)** | free names of the copied defs = the 30 of addendum 3 + `CAB`, `CABLE_SEG` (read by `cable_at`); all bound; bindings equal to the driver's own statements except the documented composed prefixes (`QADR`/`VADR` `a_{j}`, `PAD` `g_{s}_pad`, `TOOLB` `g_base`), `SIDES` narrowed, `m`/`d` = composed model or the dump model inside `_grasp_targets`; `GRASP_CENTRE_X` and `CAB` = the driver's own assignments |
| 2a | `mj_step = 0` + positive control | **CONFIRMED on the relocated-dump path** | my counter (installed before the harness wraps `mujoco.mj_step`) **0** = harness JSON **0** = module counter **0**; the copy with one injected `mujoco.mj_step` after the targets: **1 = 1 = 1**. On the as-landed dump path both runs stop before the injected step (0 = 0; the control cannot fire there — stated, not hidden) |
| 2b | driver-family import = 0 | **CONFIRMED** | static sweep of 8 tokens = 0 each; after execution `sys.modules` holds no `ur15_steps*`/`kinonly_step_solve`; modules loaded from the archive = `ur15_cell_spec`, `ur15_gripper_mirror_acceptance`, `ur15_mirror_acceptance` (the acceptance modules, not the driver) |
| 2c | no tracked write | **CONFIRMED** | run from `git archive 3cb2a28c36` in the scratchpad; `--out` in the scratchpad; the shared tree untouched (`git status` clean for the harness) |
| 3 | composed models, AXFIX ≤ 1e-9 | **CONFIRMED** | `build_side` @ HEAD blob `ad1d80d49f24` == `b7a5e39ecf`; both sides `nq` 14 / `nbody` 22 / `ngeom` 38; `AXFIX` via the harness's own `_bind`: max |Δ| vs banked **L 3.8e-15, R 3.3e-15**; `AXFIX_R = diag(1,−1,1)·AXFIX_L·A` to **4.9e-15** |
| 4 | targets (§17.7 form) | **CONFIRMED** | harness paths (b-1)/(b-2) agree to **1.665e-16**, links **cab27/cab32** on both paths = my derivation (addendum 5); `GL`/`GR` == §17.7 literal to ≤ 1.7e-16; dump sha256 printed == **my self-measured** `4158e4e638e9b0fc…`; `GRASP_CENTRE_X` 0.15 / `WORK_ROW_DY` 0.0 with env **unset**; settle offsets (a) − (b) L `(−0.0139, 0, −0.0052)`, R `(+0.0011, 0, −0.0030)` == mine to ≤ 1.7e-16; the (a) U0 rows: 4 per side, `in_denominator = False`, tag 「settled example (U0)」, all converged (report only) |
| 5 / 6 | run form, converged | **CONFIRMED** | `solve_ik(t, tgt, tries=None, iters=300, seed=1, near=None, other=None, re_max=0.05, quiet=True)`; converged := returned; per-row tag none on all 34 denominator rows; `pe` re-checked (max over rows: L 1.27e-16… see appendix B: L ≤ 4.5e-13 mm vs mine), `re` not re-checked (stated) |
| 7 | bar (§10 R0 / §11) | **PASS (convergence only)** | **L 17/17, R 17/17**; `L_converges_R_not = []`, `R_converges_L_not = []`; `section_11_STOP = False`; exit 0 |
| 8 | negative control (R targets on the L model) | **failed to fire** (as addendum 3 predicted) | 17/17 converge on the L model; differs on **0** rows; recorded (`negative_control_fired = False`), not gating — the convergence predicate cannot tell B from the L model; this is why "B is right" stays with the static legs |
| 9 | independent execution + row-for-row | **CONFIRMED** | vs my `pz_r0_v2.py` runs (`r0_L_2812.json` / `r0_R_2812.json`, same start `HOME_POSE`, seed 1, `n_try` 22): targets equal (1e-12), converged flags equal 17/17 both sides, candidate counts equal on **every** row (L `[10,13,13,10,12,12,12,12,12,12,12,12,12,10,10,10,12]`, R `[13,13,13,13,15,10,10,10,15,12,12,12,12,13,13,13,12]`), `pe` max |Δ| L 4.5e-13 mm / R 7.6e-13 mm, `q` max |Δ| L 5.0e-10 / R 4.9e-10 rad (my saved precision 1e-9) |
| 10 | report form | **CONFIRMED** | claim line 「収束のみ／衝突・把持・動的追従は未証明」 printed; tags ∈ {none} for solved rows; the composed model has `COLG = 0`, `FURNG = 0`, `other = None`, `near = None` — clearance/path branches vacuous by construction, said in the report |
| 11 | pins / no physics | **CONFIRMED** | harness commit + sha above; archive sha == blob; my instruments' shas in the appendices; `mj_forward`/`mj_kinematics` only |
| R0-ii | — | absent | `pose_only` occurs only inside the copied `solve_ik` signature; no R0-ii rows (p11's decision pending) |

**Stop-cause tags (Rs1 supplement a)**: as-landed dump path = **instrument calibration stop** (loader; reproduced standalone, appendix B); relocated-dump path = **none** on all rows. **Rs1 supplement b**: landed and verified on the rows above; the as-landed procedure does not run through — acceptance is p4's word, and needs either (i) a p0 fix so the harness resolves the dump's mesh files (an asset dict with unique keys or a mesh directory, as my loader in addendum 5 appendix F does), or (ii) p4 accepting "`--dump` = a copy of the dump beside its meshes" as the documented run form. The numbers in this verdict come from the unchanged harness code under (ii).

## What this leg does not show (named)
- Collision (mast/table/other arm), grasp, dynamic tracking, the servo — outside the composed model (Rs1 Q1 scope; #69 only).
- That UR15-B is *right*: convergence passes the rotated-copy defect too (addendum 3, measured 09-16 on the same class; not repeated here).
- Row 7 of the B line (runtime AXFIX print) — #69 only.
- The negative control of row 8 cannot fail on this class; the leg's discriminating power for "B vs L model" is nil by measurement.

## Corrections carried (dated, from addendum 7)
Addenda 5/6 said the §17.7-compliant follow-up did not exist while their own measured count said 1; `3cb2a28c36` (08:34:14) predates both (`b829c3f066` 08:39:08, `3ad4ac4399` 08:46:14). The addendum-5 catch on `ffa612ea33`'s `:1241` binding was already resolved when sent (PZ-232) — withdrawn on the current object. Disclosure per p4's condition: **harness `3cb2a28c36` landed before the row-4 re-pin (as-read order)**; the re-pin's literal, closed form and dump sha are my own (addendum 5, appendix F).

## Provenance
Instruments: `pz_r0_static.py` (addendum 4 appendix D), `pz_r0_bind.py` (appendix E), `pz_r0_targets.py` (addendum 5 appendix F), `pz_r0_v2.py` (appendix G), `pz_r0_exec.py` (addendum 6 appendix H; two lines adapted for the v3 CLI = `EXTRA` args and the second injection anchor — the adapted file is appendix C here), `pz_r0_compare.py` (appendix A). Runs: `git archive 3cb2a28c36` of the sim dir into the scratchpad; env `/home/rlrk/env_isaaclab7` (MuJoCo 3.11.0). Zero tracked-content modifications by pZ. Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction id m-p18-393.

## Appendix A — `pz_r0_compare.py` (verbatim; sha256 1123dea6734c5a91a06ac44a5b9f7279257ecc61d84df2007caab2db3ac0bb57)
```python
"""pZ row-9 and section-17.7 comparison of p0's harness report against my instrument's results and my own derivations."""
import json, sys, pathlib, hashlib
S = pathlib.Path(sys.argv[1]); REP = pathlib.Path(sys.argv[2]); DUMP = sys.argv[3]
rep = json.load(open(REP)); sm = rep["summary"]; src = sm["targets_source"]
mine = {t: json.load(open(S / f"r0_{t}_2812.json")) for t in "LR"}
LIT = {"L": (0.1125, 0.28, 0.954), "R": (0.1875, 0.28, 0.954)}; LINK = {"L": "cab27", "R": "cab32"}
my_dump_sha = hashlib.sha256(open(DUMP, "rb").read()).hexdigest()
my_offsets = {"L": (0.0986 - 0.1125, 0.28 - 0.28, 0.9488 - 0.954), "R": (0.1886 - 0.1875, 0.28 - 0.28, 0.951 - 0.954)}
out = {}
out["17.7 paths agree (harness)"] = (src["paths_max_abs_diff_m"], src["paths_links_equal"])
out["17.7 links"] = {t: (src["path_b1_driver_cable_at_on_dump"][t]["link"], src["path_b2_closed_form"][t]["link"], LINK[t]) for t in "LR"}
out["17.7 GL/GR vs literal max|diff|"] = {t: max(abs(a - b) for a, b in zip(src["G" + t], LIT[t])) for t in "LR"}
out["17.7 dump sha == mine (self-measured)"] = (src["dump_sha256"] == my_dump_sha, my_dump_sha[:16])
out["17.7 env unset"] = (not src["GRASP_CENTRE_X_env_set"], not src["WORK_ROW_DY_env_set"], src["GRASP_CENTRE_X"], src["WORK_ROW_DY"])
out["17.7 settle offsets vs mine max|diff|"] = {t: max(abs(a - b) for a, b in zip(src["settle_offset_a_minus_b"][t], my_offsets[t])) for t in "LR"}
u0 = {t: rep[f"U0_settled_{t}"] for t in "LR"}
out["U0 rows: n, in_denominator flags, tags, converged"] = {t: (len(u0[t]), sorted({r["in_denominator"] for r in u0[t]}), sorted({r["row_tag"] for r in u0[t]}), [r["converged"] for r in u0[t]]) for t in "LR"}
neg = rep["negative_control_R_on_L"]
out["neg control: n, in_denominator, converged count"] = (len(neg), sorted({r["in_denominator"] for r in neg}), sum(r["converged"] for r in neg))
for t in "LR":
    hr = {r["step"]: r for r in rep[t]}; mr = {r["step"]: r for r in mine[t]["rows"]}
    out[f"row9 {t}: rows"] = len(hr)
    out[f"row9 {t}: targets equal (1e-12)"] = all(max(abs(a - b) for a, b in zip(hr[s]["target"], mr[s]["tgt"])) < 1e-12 for s in hr)
    out[f"row9 {t}: converged flags equal"] = all(hr[s]["converged"] == mr[s]["converged"] for s in hr)
    out[f"row9 {t}: candidate counts equal"] = [s for s in hr if hr[s]["n_converged_candidates"] != mr[s]["solved"]] == []
    out[f"row9 {t}: pe max|diff| mm"] = max(abs(hr[s]["pe_recheck_m"] * 1000 - mr[s]["pe_mm"]) for s in hr)
    out[f"row9 {t}: q max|diff| rad"] = max(max(abs(a - b) for a, b in zip(hr[s]["q"], mr[s]["q"])) for s in hr)
    out[f"row9 {t}: in_denominator all True, tags"] = (all(r["in_denominator"] for r in rep[t]), sorted({r["stop_cause_tag"] for r in rep[t]}))
    out[f"row9 {t}: harness candidates"] = [hr[s]["n_converged_candidates"] for s in sorted(hr)]
    out[f"row9 {t}: my solved       "] = [mr[s]["solved"] for s in sorted(hr)]
out["summary"] = {k: sm[k] for k in ("stop_cause_tags_seen", "section_11_STOP_R_converged_0", "rows", "L_converged", "R_converged", "L_converges_R_not", "R_converges_L_not", "negative_control_R_rows_on_L_model_differ_on_steps", "negative_control_fired", "U0_settled_rows_reported", "seed", "re_max", "tries", "iters", "quiet", "start_pose", "mj_step_calls", "env_overrides_set", "harness_sha256", "elapsed_s")}
out["branches"] = sm["branches_on_composed_model"]
for k, v in out.items(): print(f"{k}: {v}")
```

## Appendix B — execution outputs (verbatim)
```text
## as-landed dump path (real _gen/): run / control
{"mode": "run", "harness_sha256": "c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998", "harness_reported_sha256": null, "exit_code": 2, "my_mj_step_count": 0, "harness_mj_step_count": 0, "driver_family_in_sys_modules": [], "modules_loaded_from_archive": ["ur15_cell_spec", "ur15_gripper_mirror_acceptance", "ur15_mirror_acceptance"], "L_converged": null, "R_converged": null, "L_not_R": null, "neg_diff": null, "stop_tags": ["instrument calibration stop"], "row3_axfix_maxabs_vs_banked": {"L": 3.83026943495679e-15, "R": 3.3306690738754696e-15, "mirror_relation": 4.935423814425584e-15}, "harness_module_counter": 0, "elapsed_s": null, "stdout_log": "/tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/r0exec_v3_run/harness_stdout_run.log"}
{"mode": "control", "harness_sha256": "c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998", "harness_reported_sha256": null, "exit_code": 2, "my_mj_step_count": 0, "harness_mj_step_count": 0, "driver_family_in_sys_modules": [], "modules_loaded_from_archive": ["ur15_cell_spec", "ur15_gripper_mirror_acceptance", "ur15_mirror_acceptance"], "L_converged": null, "R_converged": null, "L_not_R": null, "neg_diff": null, "stop_tags": ["instrument calibration stop"], "row3_axfix_maxabs_vs_banked": {"L": 3.83026943495679e-15, "R": 3.3306690738754696e-15, "mirror_relation": 4.935423814425584e-15}, "harness_module_counter": 0, "elapsed_s": null, "stdout_log": "/tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/r0exec_v3_ctrl/harness_stdout_control.log"}
## harness stop line
[r0] ⛔ instrument calibration stop (section 17.7 targets): cell dump unloadable: /home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/_gen/_steps_cell_full.xml: Error: Error opening file 'follower.stl'
## standalone reproduction (env7 python): mujoco.MjModel.from_xml_path(<real dump path>) -> Error: Error opening file 'follower.stl'; STL files beside the dump: []
## dump relocated beside its 8 ko meshes (same bytes, sha 4158e4e6...): run / control
{"mode": "run", "harness_sha256": "c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998", "harness_reported_sha256": "c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998", "exit_code": 0, "my_mj_step_count": 0, "harness_mj_step_count": 0, "driver_family_in_sys_modules": [], "modules_loaded_from_archive": ["ur15_cell_spec", "ur15_gripper_mirror_acceptance", "ur15_mirror_acceptance"], "L_converged": 17, "R_converged": 17, "L_not_R": [], "neg_diff": [], "stop_tags": [], "row3_axfix_maxabs_vs_banked": {"L": 3.83026943495679e-15, "R": 3.3306690738754696e-15, "mirror_relation": 4.935423814425584e-15}, "harness_module_counter": 0, "elapsed_s": 58.075, "stdout_log": "/tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/r0exec_v3w_run/harness_stdout_run.log"}
{"mode": "control", "harness_sha256": "c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998", "harness_reported_sha256": "ce1e343c0330622c511ce8e43f4b1e475b7bad21d19739d0d4b6e56a0a95ec97", "exit_code": 0, "my_mj_step_count": 1, "harness_mj_step_count": 1, "driver_family_in_sys_modules": [], "modules_loaded_from_archive": ["ur15_cell_spec", "ur15_gripper_mirror_acceptance", "ur15_mirror_acceptance"], "L_converged": 17, "R_converged": 17, "L_not_R": [], "neg_diff": [], "stop_tags": [], "row3_axfix_maxabs_vs_banked": {"L": 3.83026943495679e-15, "R": 3.3306690738754696e-15, "mirror_relation": 4.935423814425584e-15}, "harness_module_counter": 1, "elapsed_s": 59.103, "stdout_log": "/tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/r0exec_v3w_ctrl/harness_stdout_control.log"}
## pz_r0_compare.py on the relocated-dump run
17.7 paths agree (harness): (1.6653345369377348e-16, True)
17.7 links: {'L': ('cab27', 'cab27', 'cab27'), 'R': ('cab32', 'cab32', 'cab32')}
17.7 GL/GR vs literal max|diff|: {'L': 1.5265566588595902e-16, 'R': 1.6653345369377348e-16}
17.7 dump sha == mine (self-measured): (True, '4158e4e638e9b0fc')
17.7 env unset: (True, True, 0.15, 0.0)
17.7 settle offsets vs mine max|diff|: {'L': 1.5265566588595902e-16, 'R': 1.6653345369377348e-16}
U0 rows: n, in_denominator flags, tags, converged: {'L': (4, [False], ['settled example (U0)'], [True, True, True, True]), 'R': (4, [False], ['settled example (U0)'], [True, True, True, True])}
neg control: n, in_denominator, converged count: (17, [False], 17)
row9 L: rows: 17
row9 L: targets equal (1e-12): True
row9 L: converged flags equal: True
row9 L: candidate counts equal: True
row9 L: pe max|diff| mm: 4.528924144620228e-13
row9 L: q max|diff| rad: 4.995645563887763e-10
row9 L: in_denominator all True, tags: (True, ['none'])
row9 L: harness candidates: [10, 13, 13, 10, 12, 12, 12, 12, 12, 12, 12, 12, 12, 10, 10, 10, 12]
row9 L: my solved       : [10, 13, 13, 10, 12, 12, 12, 12, 12, 12, 12, 12, 12, 10, 10, 10, 12]
row9 R: rows: 17
row9 R: targets equal (1e-12): True
row9 R: converged flags equal: True
row9 R: candidate counts equal: True
row9 R: pe max|diff| mm: 7.550332863779065e-13
row9 R: q max|diff| rad: 4.891976823628852e-10
row9 R: in_denominator all True, tags: (True, ['none'])
row9 R: harness candidates: [13, 13, 13, 13, 15, 10, 10, 10, 15, 12, 12, 12, 12, 13, 13, 13, 12]
row9 R: my solved       : [13, 13, 13, 13, 15, 10, 10, 10, 15, 12, 12, 12, 12, 13, 13, 13, 12]
summary: {'stop_cause_tags_seen': [], 'section_11_STOP_R_converged_0': False, 'rows': 17, 'L_converged': 17, 'R_converged': 17, 'L_converges_R_not': [], 'R_converges_L_not': [], 'negative_control_R_rows_on_L_model_differ_on_steps': [], 'negative_control_fired': False, 'U0_settled_rows_reported': {'L': {'2': True, '3': True, '4': True, '5': True}, 'R': {'2': True, '3': True, '4': True, '5': True}}, 'seed': 1, 're_max': 0.05, 'tries': None, 'iters': 300, 'quiet': True, 'start_pose': [-3.1521, -0.2867, 2.4674, -1.3953, 1.5634, -1.5782], 'mj_step_calls': 0, 'env_overrides_set': {}, 'harness_sha256': 'c63539622cb8184f2088a91d094d6c109eb03117fe3e1c8625c153c97ad37998', 'elapsed_s': 58.075}
branches: {'L': {'COLG': 0, 'FURNG': 0, 'ARMG': 38, 'COLFREE': 38, 'FURNITURE_env': False, 'ARM_PATH_env': False, 'other': None, 'near': None}, 'R': {'COLG': 0, 'FURNG': 0, 'ARMG': 38, 'COLFREE': 38, 'FURNITURE_env': False, 'ARM_PATH_env': False, 'other': None, 'near': None}}
## harness stdout (relocated-dump run), section 17.7 lines and per-side AXFIX
[r0] effective GRASP_CENTRE_X=0.15 (env set: False), WORK_ROW_DY=0.0 (env set: False)
[r0] settle offset (a) - (b) [m]: L=[-0.013900000000000162, 0.0, -0.005199999999999982] R=[0.0010999999999998233, 0.0, -0.0030000000000000027]  (a = _gen/dod_c2_20260810/run.log :93 (sha256 04599b84e34be51ec906662f0d92aa8349eae833034c3a7e8d070d6c808b8868), the driver's 're-measured after the approach' print (:2825 @ 84a372439c59; driver c737f6974e at the run), rounded to 1e-4 by that print; reported, outside the deno
[r0] targets: 17 rows (2-18) in the denominator; 4 extra U0 rows reported
[r0] side L: composed model nq=14 nbody=22 ngeom=38; {'COLG': 0, 'FURNG': 0, 'ARMG': 38, 'COLFREE': 38, 'FURNITURE_env': False, 'ARM_PATH_env': False, 'other': None, 'near': None}; AXFIX rows c/s/a =
[r0]   c = [+0.000000 +1.000000 -0.000000]
[r0]   s = [+1.000000 -0.000000 -0.000000]
[r0]   a = [-0.000000 +0.000000 -1.000000]
[r0] side R: composed model nq=14 nbody=22 ngeom=38; {'COLG': 0, 'FURNG': 0, 'ARMG': 38, 'COLFREE': 38, 'FURNITURE_env': False, 'ARM_PATH_env': False, 'other': None, 'near': None}; AXFIX rows c/s/a =
[r0]   c = [+0.000000 +1.000000 +0.000000]
[r0]   s = [+1.000000 -0.000000 +0.000000]
[r0]   a = [+0.000000 +0.000000 -1.000000]
[r0] stop_cause_tags_seen=[] | section_11_STOP_R_converged_0=False | rows=17 | L_converged=17 | R_converged=17 | L_converges_R_not=[] | R_converges_L_not=[] | bar_L_not_R_must_be_0=True | negative_control_R_rows_on_L_model_differ_on_steps=[] | negative_control_fired=False | U0_settled_rows_reported={'L': {2: True, 3: True, 4: True, 5: True}, 'R': {2: True, 3: True, 4: True, 5: True}} | seed=1 | re_max=0.05 | tries=No
[r0] 収束のみ／衝突・把持・動的追従は未証明 (convergence only; collision, grasp and dynamic tracking are not shown)
```

## Appendix C — `pz_r0_exec.py` as run for this leg (verbatim; sha256 b70fdd7374aab11c85df13172bd0500738ec984b68312c8e3a4b733c3af81672)
```python
"""pZ R0 execution instrument: run p0's harness (from a git archive of its commit) IN-PROCESS under my own mj_step counter,
installed before the harness wraps mujoco.mj_step, so any physics step is counted by both.  MODE=run executes the harness
as landed; MODE=control executes a copy with ONE injected mujoco.mj_step call (positive control: both counters must read 1).
After the run: my counter, the harness's counter (from its JSON), the sys.modules sweep for the driver family, exit code."""
import sys, os, io, runpy, hashlib, json, contextlib, pathlib, re
W, HARNESS_REL, OUT, MODE = sys.argv[1:5]; EXTRA = sys.argv[5:]          # EXTRA = extra CLI args for the harness (e.g. --dump <path>)
import mujoco
_my = {"n": 0}; _orig = mujoco.mj_step
def _counted(*a, **k):
    _my["n"] += 1; return _orig(*a, **k)
mujoco.mj_step = _counted                          # installed FIRST
hpath = pathlib.Path(W) / HARNESS_REL
src = hpath.read_text(); sha = hashlib.sha256(src.encode()).hexdigest()
if MODE == "control":
    anchors = ["    rows, source = _targets()\n", "    rows, u0 = _targets(GL, GR), _u0_rows()\n"]     # v2 / v3 (3cb2a28c36) forms
    hits = [a for a in anchors if src.count(a) == 1]
    assert len(hits) == 1, f"anchor for the injected step not found exactly once: {[src.count(a) for a in anchors]}"
    src = src.replace(hits[0], hits[0] + "    mujoco.mj_step(models['L'][0], models['L'][1])   # pZ positive control: ONE injected physics step\n")
    hpath = hpath.with_name("_pz_control_copy.py"); hpath.write_text(src)
os.chdir(hpath.parent); sys.path.insert(0, str(hpath.parent))
sys.argv = [str(hpath), "--out", OUT] + EXTRA
buf = io.StringIO(); code = None
with contextlib.redirect_stdout(buf):
    g = runpy.run_path(str(hpath), run_name="pz_r0_harness")     # module executed, its __main__ guard skipped -> globals kept
    try:
        code = g["main"]()                                        # the harness's own main, same argv
    except SystemExit as e:
        code = e.code
# row 3: AXFIX per side, measured by the harness's own _bind on models built exactly as its main builds them, vs my banked expectation
import numpy as np
EXP = {"L": np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float), "R": np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float)}
axfix = {}
with contextlib.redirect_stdout(io.StringIO()):
    models = {"L": g["_acc"].build_side("ur15_base.xml", g["_acc"].KO_LEFT, g["_spec"].SIDES["L"]),
              "R": g["_acc"].build_side("ur15_base_mirrored.xml", g["_acc"].KO_MIRROR, g["_spec"].SIDES["R"])}
    ns = g["_bind"].__globals__                                   # the LIVE module namespace (run_path's dict is a snapshot)
    for t in ("L", "R"):
        g["_bind"](t, *models[t]); axfix[t] = np.array(ns["AXFIX"][t], float)
A = np.diag([-1, 1, 1]); rel = float(np.abs(axfix["R"] - np.diag([1, -1, 1]) @ axfix["L"] @ A).max())
row3 = {t: float(np.abs(axfix[t] - EXP[t]).max()) for t in axfix}; row3["mirror_relation"] = rel
log = pathlib.Path(OUT) / f"harness_stdout_{MODE}.log"; log.parent.mkdir(parents=True, exist_ok=True); log.write_text(buf.getvalue())
rep = json.load(open(pathlib.Path(OUT) / "R0_CONVERGENCE_REPORT.json"))
fam = sorted(k for k in sys.modules if any(w in k for w in ("ur15_steps", "kinonly_step_solve")))
print(json.dumps({"mode": MODE, "harness_sha256": sha, "harness_reported_sha256": rep["summary"].get("harness_sha256"),
                  "exit_code": code, "my_mj_step_count": _my["n"], "harness_mj_step_count": rep["summary"].get("mj_step_calls"),
                  "driver_family_in_sys_modules": fam, "modules_loaded_from_archive": sorted({k for k, v in sys.modules.items() if getattr(v, "__file__", None) and str(v.__file__).startswith(str(hpath.parent))}),
                  "L_converged": rep["summary"].get("L_converged"), "R_converged": rep["summary"].get("R_converged"),
                  "L_not_R": rep["summary"].get("L_converges_R_not"), "neg_diff": rep["summary"].get("negative_control_R_rows_on_L_model_differ_on_steps"),
                  "stop_tags": rep["summary"].get("stop_cause_tags_seen"), "row3_axfix_maxabs_vs_banked": row3, "harness_module_counter": g["_bind"].__globals__.get("_MJ_STEP_CALLS"), "elapsed_s": rep["summary"].get("elapsed_s"), "stdout_log": str(log)}, ensure_ascii=False))
```
