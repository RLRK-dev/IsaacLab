# pZ — R1′ hand-on-arm leg, re-pinned on the current blobs in one artifact (v3 §10 R1′ @ `8d9fdf3bbb` `:139`; p4's adopted order `caa742b8d3` via m-p4-288): the 08-10 192/192, the AXFIX relation, and the stock-hand negative control fired and banked as this desk's measurement

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 11:50:46 JST on m-p18-426 (p4 m-p4-288 (2): 「R1′（08-10 の 192/192 ＋ AXFIX 関係 4.9e-15 を現 blob で 1 artifact に再 pin・負の対照 stock hand（98.6 mm = p11 の期待・pZ の測定として bank）を発火）」). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted** (Rs1 supplement b): acceptance is p4's word after this leg.

**Order of existence (commit dates; every one precedes today's measurement at 11:47 JST)**: the **bars** = v3 §10 R1′ (a)/(b) @ `8d9fdf3bbb` `:139` — (a) same-named pad/claw world correspondence `|Mx·p_L(name) − p_R(name)| ≤ 1e-9 m` at equal q, negative control = stock hand on UR15-B, expected 98.6 mm, bar ≥ 10 mm; (b) `AXFIX_R = diag(1,−1,1)·AXFIX_L·A`, residual ≤ 1e-12 — and this desk's 08-10 rows 3/4/6/7 (`PZ_MIRROR_LEG_PREREG_20260810.md` @ `9d118cbf93`, blob `2a1e025907d8`). The **objects** = the current blobs, unchanged since `b7a5e39ecf` (08-10): commits touching `ur15_gripper_mirror_acceptance.py` after `b7a5e39ecf` = **0**. No new bar is introduced here; this artifact is the leg against those two committed pre-registrations, plus controls that can fail.

**Objects (blob at HEAD `03b42afdb5` = blob at `92059373a3`, the archive the leg ran in; last commit; shared-tree state)**

| file | blob | last commit | worktree vs HEAD |
|---|---|---|---|
| `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` | `cdf284c42eb4` | `1a1efe0ac5` | `clean` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/_ur15_2f85_koshape_actuated_mirrored.xml` | `4a0ea5a827bd` | `b7a5e39ecf` | `clean` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_base.xml` | `7334710cc0d6` | `bf0235cfd8` | `clean` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_base_mirrored.xml` | `6751866fd3f4` | `6a542f45dd` | `1 file changed, 1 insertion(+), 1 deletion(-)` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_cell_spec.py` | `6bdf7ea4f9ca` | `0f6b4a733e` | `1 file changed, 391 insertions(+), 246 deletions(-)` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_gripper_mirror_acceptance.py` | `ad1d80d49f24` | `b7a5e39ecf` | `1 file changed, 29 insertions(+), 24 deletions(-)` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ko_mirror_meshes/` (8 baked STLs) | tree `d286ae12f5b9` | — | (tree object equal at HEAD and `92059373a3`) |
| stock ko meshes `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets/` (8 STLs the stock xml names) | tracked 8/8 | — | dirty 0/8 (the 6 dirty entries in that directory are untracked scratch xmls, not inputs) |

**Where the leg ran**: the `git archive` of `92059373a3` under this desk's scratchpad (`wt_92059373a3`, the same archive as window W's leg); the acceptance module imported from the archive (it is not the driver); the stock ko xml and its 8 meshes are read by the script's absolute path from the shared tree (tracked, clean, listed above). Three of the six input files carry the 09-07 WIP overlay in the shared tree, so nothing ran there. **`mj_step` = 0**, driver family in `sys.modules` = `[]`, `mj_kinematics` / `mj_forward` only; **run 0**. **Stop-cause tags**: on the legs **none**; on the acceptance script's own record write **one instrument calibration stop** (row d, reported separately below).

## Rows and verdicts

| # | row (bar as pre-registered) | verdict | measured by `pz_r1p.py` (appendix A) |
|---|---|---|---|
| a1 | body-level world correspondence on **B** (mirrored arm + mirrored ko): `|Mx·p_L(name) − p_R(name)| ≤ 1e-9 m` for every hand body × placement — 14 hand bodies (`g_*`) × 6 placements (HOME/open, HOME/half, HOME/close, alt/open, alt/half, alt/close) = 84 pairs | **CONFIRMED** | **84/84**; max **9.09e-13 mm** |
| a2 | the script's own geom-level form (`run_leg` `:109-141`: symmetric Hausdorff of world point sets of every `g_*` geom, 32 geoms × 6 placements = 192, tol 1e-3 mm) on B | **CONFIRMED** | **pZ B: 192/192 geom-instances hold (worst Hausdorff 0.000041 mm)** — the 08-10 numbers (192/192, worst 4.1e-5 mm) reproduced on the current blobs |
| a3 | **negative control = stock hand on UR15-B** (NH: `build_side("ur15_base_mirrored.xml", KO_LEFT, +1)`, the script's own NEGATIVE `:153`): must fail; bar ≥ 10 mm; p11's expectation 98.6 mm | **CONFIRMED (fires)** | body level **12/84** within 1e-9 m — the 12 are `g_base` and `g_base_mount` at all 6 placements (they sit on the wrist; chirality-blind), the **four pad bodies read exactly 98.600 mm at every placement (= p11's 98.6)**, worst body **136.400 mm** at `alt/open/g_left_follower`; geom level **pZ NH: 0/192 geom-instances hold (worst Hausdorff 135.377130 mm)** (= 08-10's 135.4). Banked as this desk's measurement |
| a4 | second control RC (stock arm + stock ko on the right mount, sign +1) | fires | body level 0/84 (max 1629.2 mm); geom level pZ RC: 0/192 geom-instances hold (worst Hausdorff 1686.312778 mm) |
| a5 | wrong-plane control on B: the predicate with `My = diag(1,−1,1)` in place of `Mx` | fires | 0/84 (max 1328.8 mm) — no other reflection satisfies row a1 |
| b1 | AXFIX relation `AXFIX_R = diag(1,−1,1)·AXFIX_L·A`, `A = diag(−1,1,1)`, residual ≤ 1e-12 (seed q `[0, −1.2, 1.0, −1.4, −1.57, 0]`, fingers 0, fresh MjData — the driver's rule as copied in the harness `:914-933`) | **CONFIRMED** | **4.94e-15** (= the 4.9e-15 pinned in `PZ_R3_TILT_CAP_LEG_PREREG_20260913.md` `:19` and `PZ_VERDICT_8e5905539c_R0_LEG_20260920.md` row 3); measured rows L c/s/a = [0 1 0] / [1 0 0] / [0 0 −1] = the banked expectation |
| b2 | wrong-form control: v2's `Mx·AXFIX_L·A` | fires | residual **2.00** (p11 `:80`: "c 行の符号が逆・残差 2.0") |
| b3 | AXFIX on NH and RC against B (not a bar; p11 `:80`: AXFIX does not discriminate the hand) | measured | NH vs B 3.07e-15, RC vs B 4.77e-15 — **identical**: the stock and the mirrored hand give the same AXFIX at the seed, so row b cannot tell the hands apart; rows a1-a3 do |
| c | control invariance / no run | **CONFIRMED** | `mj_step` calls 0; driver family in `sys.modules` `[]`; mount from `ur15_cell_spec` = {'YOKE_SPREAD': 0.28, 'TILT_rad': 1.2217304763960306, 'SHOULDER_HEIGHT': 1.5299999999999998, 'HOME_POSE': [-3.1521, -0.2867, 2.4674, -1.3953, 1.5634, -1.5782]} |
| d | the acceptance script itself, executed in the archive (rc, VERDICT, record) | **CONFIRMED after one instrument stop** | first run **rc 1**: `FileNotFoundError` at the record write (`:186`, `HERE/_gen/ko_mirror_acceptance.txt`) because `_gen/` is untracked and absent in a clean checkout — the legs had already computed; second run after `mkdir _gen` in the archive: **rc 0, `VERDICT: PASS`** (TEST 192/192 worst 4.1e-5 mm; NEGATIVE 0/192 worst 135.377 mm; vertex spot check 0.000e+00 m over 5088 verts); record sha256 `92fad9158f708a4d…`, 13 lines |

## Stop-cause report (Rs1 supplement a), separate from the legs
**instrument calibration stop** — the acceptance script writes its record into `_gen/` without creating it (`:186`); 08-10 ran in the shared tree where `_gen/` existed, so the stop is new to a clean checkout, not to the code. It is not a controller failure and it does not touch the legs' numbers (all computed before the write; identical in both runs). A one-line proposal for p4's disposition, not implemented by this desk: create the directory as the R0 harness does (`out_dir.mkdir(parents=True, exist_ok=True)`, harness `:1255`).

## The stock-hand negative control per body and placement (verbatim, mm)
```text
NH (stock hand on UR15-B) body-level |Mx.p_L - p_R| [mm] per placement (rows) x body (cols)
placement                base     base_mount   left_coupler    left_driver  left_follower       left_pad left_silicone_pad left_spring_link  right_coupler   right_driver right_follower      right_pad right_silicone_pad right_spring_link
HOME/open               0.000          0.000        124.202         61.202        136.400         98.600         98.600         26.400        124.202         61.202        136.400         98.600         98.600         26.400
HOME/half               0.000          0.000        122.422         61.202        136.400         98.600         98.600         26.400        122.422         61.202        136.400         98.600         98.600         26.400
HOME/close              0.000          0.000        113.229         61.202        136.400         98.600         98.600         26.400        113.229         61.202        136.400         98.600         98.600         26.400
alt/open                0.000          0.000        124.202         61.202        136.400         98.600         98.600         26.400        124.202         61.202        136.400         98.600         98.600         26.400
alt/half                0.000          0.000        122.422         61.202        136.400         98.600         98.600         26.400        122.422         61.202        136.400         98.600         98.600         26.400
alt/close               0.000          0.000        113.229         61.202        136.400         98.600         98.600         26.400        113.229         61.202        136.400         98.600         98.600         26.400
```
Reading: p11's 98.6 mm is the **pad** row (`left_pad`, `left_silicone_pad`, `right_pad`, `right_silicone_pad`), constant over placements because the pad offset from the wrist is rigid; the follower (136.400) and coupler (124.202) are larger; `base` / `base_mount` are 0 by construction. The bar (≥ 10 mm) is met by 12 of the 14 bodies; a negative control that looked only at the base bodies would **not** fire — the 14-body set (or the pads alone) is what discriminates.

## What this leg does not show (holes)
- The stand-in (column + one arm + one hand per side), not the driver's full cell — 08-10 §3's boundary is unchanged; the driver is not imported here.
- Body positions and geom point sets at 6 placements only; not mass / inertia / actuator / tendon fields (R2), not the arm's own self-mirror (R1), not motion or contact (run; #69).
- Row b measures a consistency relation that both hands satisfy (b3); it is not evidence about the hand asset.

## Appendix A — `pz_r1p.py` (verbatim; sha256 f182a44625d2a46d294ab5e5c8aa933faa8c4551a78b096b54aa5978fccc61d9)
```python
"""pZ R1' instrument (v3 section 10 R1'): (a) hand-on-arm world correspondence of same-named hand BODIES at equal q, |Mx.p_L(name) - p_R(name)|,
on B (mirrored arm + mirrored ko), NH (mirrored arm + stock ko = the stock-hand negative), RC (stock arm + stock ko on the right mount), plus the
script's own geom-level run_leg form; a wrong-plane control (My instead of Mx) on B; (b) the AXFIX relation AXFIX_R = diag(1,-1,1).AXFIX_L.A with the
v2 wrong form and the NH/RC AXFIX as controls.  argv: W(archive sim dir) OUT.json.  Static: mj_kinematics / mj_forward only."""
import sys, io, json, contextlib, numpy as np, mujoco
W, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, W)
with contextlib.redirect_stdout(io.StringIO()):
    import ur15_gripper_mirror_acceptance as g; import ur15_cell_spec as spec
Mx = np.diag([-1.0, 1.0, 1.0]); My = np.diag([1.0, -1.0, 1.0]); A = np.diag([-1.0, 1.0, 1.0])
steps = 0; _orig = mujoco.mj_step
def _counted(*a, **k):
    global steps; steps += 1; return _orig(*a, **k)
mujoco.mj_step = _counted
with contextlib.redirect_stderr(io.StringIO()):
    models = {"L": g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["L"]),
              "B": g.build_side("ur15_base_mirrored.xml", g.KO_MIRROR, g.acc.SIDE_SIGN["R"]),
              "NH": g.build_side("ur15_base_mirrored.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"]),
              "RC": g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"])}
B_ = lambda m, n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)
def hand_bodies(m): return sorted(n for n in (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) for b in range(m.nbody)) if n and n.startswith("g_"))
mL, dL = models["L"]; names = hand_bodies(mL)
res = {"n_hand_bodies": len(names), "hand_bodies": names, "placements": [f"{p}/{f}" for p in g.ARM_POSES for f in g.FINGERS], "a_body_level": {}, "a_geom_level_script_form": {}, "b_axfix": {}}
for mn in ("B", "NH", "RC"):
    mR, dR = models[mn]; assert hand_bodies(mR) == names, mn
    for label, MM in (("Mx", Mx), ("My_wrong_plane", My)):
        worst, worst_at, within, total = 0.0, None, 0, 0
        for pn, pose in g.ARM_POSES.items():
            for fn, fing in g.FINGERS.items():
                g.place(mL, dL, pose, fing); g.place(mR, dR, pose, fing)
                for n in names:
                    e = float(np.linalg.norm(MM @ np.array(dL.xpos[B_(mL, n)]) - np.array(dR.xpos[B_(mR, n)]))); total += 1; within += e <= 1e-9
                    if e > worst: worst, worst_at = e, f"{pn}/{fn}/{n}"
        res["a_body_level"][f"{mn}:{label}"] = {"pairs_within_1e-9_m": within, "pairs": total, "max_mm": worst * 1000.0, "worst_at": worst_at}
    out = []; ok, n = g.run_leg(mL, dL, mR, dR, f"pZ {mn}", out)
    res["a_geom_level_script_form"][mn] = {"holds": bool(ok), "n": n, "lines": out}
def axfix(m):
    d = mujoco.MjData(m)   # fresh data: fingers 0
    J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
    for k, j in enumerate(J6): d.qpos[m.joint(f"a_{j}").qposadr[0]] = [0.0, -1.2, 1.0, -1.4, -1.57, 0.0][k]   # the driver's seed q (:600)
    mujoco.mj_forward(m, d)
    pl, pr = np.array(d.xpos[B_(m, "g_left_pad")]), np.array(d.xpos[B_(m, "g_right_pad")]); c_w = (pr - pl) / max(np.linalg.norm(pr - pl), 1e-9); pinch = 0.5 * (pl + pr)
    a_w = np.array(d.xpos[B_(m, "g_base")]) - pinch; a_w = a_w / max(np.linalg.norm(a_w), 1e-9); Rt = np.array(d.xmat[B_(m, "g_base")]).reshape(3, 3)
    c_l, a_l = Rt.T @ c_w, Rt.T @ a_w
    return np.column_stack([c_l, np.cross(a_l, c_l), a_l]).T
AX = {mn: axfix(models[mn][0]) for mn in models}
res["b_axfix"] = {"AXFIX": {mn: np.round(AX[mn], 12).tolist() for mn in AX},
                  "relation_B_vs_diag(1,-1,1).AXFIX_L.A_max": float(np.abs(AX["B"] - np.diag([1, -1, 1]) @ AX["L"] @ A).max()),
                  "wrong_form_v2_B_vs_Mx.AXFIX_L.A_max": float(np.abs(AX["B"] - Mx @ AX["L"] @ A).max()),
                  "NH_vs_B_max": float(np.abs(AX["NH"] - AX["B"]).max()), "RC_vs_B_max": float(np.abs(AX["RC"] - AX["B"]).max()),
                  "L_c_dot_a": float(AX["L"][0] @ AX["L"][2]), "B_c_dot_a": float(AX["B"][0] @ AX["B"][2])}
res["mj_step_calls"] = steps; res["driver_family_in_sys_modules"] = [k for k in sys.modules if "ur15_steps" in k]
res["mount"] = {"YOKE_SPREAD": float(g.acc.YOKE_SPREAD), "TILT_rad": float(g.acc.TILT), "SHOULDER_HEIGHT": float(g.acc.SHOULDER_HEIGHT), "HOME_POSE": list(map(float, spec.HOME_POSE))}
open(OUT, "w").write(json.dumps(res, indent=1))
for k, v in res["a_body_level"].items(): print(f"[r1'] (a) body level {k:20s}: {v['pairs_within_1e-9_m']}/{v['pairs']} pairs within 1e-9 m; max {v['max_mm']:.6f} mm at {v['worst_at']}")
for k, v in res["a_geom_level_script_form"].items(): print(f"[r1'] (a) geom level (run_leg) {k}: holds={v['holds']} n={v['n']} | " + " | ".join(v["lines"][-1:]))
b = res["b_axfix"]; print(f"[r1'] (b) AXFIX_B vs diag(1,-1,1).AXFIX_L.A: {b['relation_B_vs_diag(1,-1,1).AXFIX_L.A_max']:.2e} | v2 wrong form Mx.AXFIX_L.A: {b['wrong_form_v2_B_vs_Mx.AXFIX_L.A_max']:.2e} | NH vs B: {b['NH_vs_B_max']:.2e} | RC vs B: {b['RC_vs_B_max']:.2e} | c.a L {b['L_c_dot_a']:.2e} B {b['B_c_dot_a']:.2e}")
for mn in ("L", "B", "NH", "RC"): print(f"[r1'] AXFIX[{mn}] rows c/s/a = " + "; ".join("[" + " ".join(f"{v:+.6f}" for v in row) + "]" for row in AX[mn]))
print(f"[r1'] hand bodies {len(names)}: {names}"); print(f"[r1'] mj_step calls: {steps}; driver family in sys.modules: {res['driver_family_in_sys_modules']}; mount {res['mount']}")
```

## Appendix B — outputs (verbatim)
```text
## pz_r1p.py on the archive (env7 python 3.12.3 / mujoco 3.11.0), 11:47:32-11:47:37 JST
[r1'] (a) body level B:Mx                : 84/84 pairs within 1e-9 m; max 0.000000 mm at HOME/open/g_right_pad
[r1'] (a) body level B:My_wrong_plane    : 0/84 pairs within 1e-9 m; max 1328.814009 mm at alt/open/g_right_pad
[r1'] (a) body level NH:Mx               : 12/84 pairs within 1e-9 m; max 136.400000 mm at alt/open/g_left_follower
[r1'] (a) body level NH:My_wrong_plane   : 0/84 pairs within 1e-9 m; max 1319.984722 mm at alt/open/g_left_pad
[r1'] (a) body level RC:Mx               : 0/84 pairs within 1e-9 m; max 1629.249613 mm at alt/open/g_left_pad
[r1'] (a) body level RC:My_wrong_plane   : 0/84 pairs within 1e-9 m; max 2303.282716 mm at alt/open/g_left_pad
[r1'] (a) geom level (run_leg) B: holds=True n=192 |   pZ B: 192/192 geom-instances hold (worst Hausdorff 0.000041 mm)
[r1'] (a) geom level (run_leg) NH: holds=False n=192 |   pZ NH: 0/192 geom-instances hold (worst Hausdorff 135.377130 mm)
[r1'] (a) geom level (run_leg) RC: holds=False n=192 |   pZ RC: 0/192 geom-instances hold (worst Hausdorff 1686.312778 mm)
[r1'] (b) AXFIX_B vs diag(1,-1,1).AXFIX_L.A: 4.94e-15 | v2 wrong form Mx.AXFIX_L.A: 2.00e+00 | NH vs B: 3.07e-15 | RC vs B: 4.77e-15 | c.a L 3.62e-16 B -1.30e-15
[r1'] AXFIX[L] rows c/s/a = [+0.000000 +1.000000 -0.000000]; [+1.000000 -0.000000 -0.000000]; [-0.000000 +0.000000 -1.000000]
[r1'] AXFIX[B] rows c/s/a = [+0.000000 +1.000000 +0.000000]; [+1.000000 -0.000000 +0.000000]; [+0.000000 +0.000000 -1.000000]
[r1'] AXFIX[NH] rows c/s/a = [+0.000000 +1.000000 -0.000000]; [+1.000000 -0.000000 -0.000000]; [-0.000000 -0.000000 -1.000000]
[r1'] AXFIX[RC] rows c/s/a = [+0.000000 +1.000000 -0.000000]; [+1.000000 -0.000000 +0.000000]; [+0.000000 +0.000000 -1.000000]
[r1'] hand bodies 14: ['g_base', 'g_base_mount', 'g_left_coupler', 'g_left_driver', 'g_left_follower', 'g_left_pad', 'g_left_silicone_pad', 'g_left_spring_link', 'g_right_coupler', 'g_right_driver', 'g_right_follower', 'g_right_pad', 'g_right_silicone_pad', 'g_right_spring_link']
[r1'] mj_step calls: 0; driver family in sys.modules: []; mount {'YOKE_SPREAD': 0.28, 'TILT_rad': 1.2217304763960306, 'SHOULDER_HEIGHT': 1.5299999999999998, 'HOME_POSE': [-3.1521, -0.2867, 2.4674, -1.3953, 1.5634, -1.5782]}

## the acceptance script itself, first run in the archive (rc 1; last lines)
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/claude-1000/-home-rlrk-IsaacLab/f0babc66-64fb-405d-bbd6-6f765758dd7b/scratchpad/wt_92059373a3/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/_gen/ko_mirror_acceptance.txt'

## second run after mkdir _gen (rc 0; key lines)
assets: L=_ur15_2f85_koshape_actuated.xml  R=_ur15_2f85_koshape_actuated_mirrored.xml  A=diag(-1,1,1)
tolerance: symmetric Hausdorff 0.001 mm; poses ['HOME', 'alt'] x fingers ['open', 'half', 'close']
  TEST (mirrored asset on the right): 192/192 geom-instances hold (worst Hausdorff 0.000041 mm)
  NEGATIVE (LEFT asset on the right -- the rotated-copy defect; MUST fail): 0/192 geom-instances hold (worst Hausdorff 135.377130 mm)
  VERTEX SPOT CHECK (spring_link, file-level): baked == A x original, Hausdorff 0.000e+00 m over 5088 verts: True
VERDICT: PASS  (test holds: True; negative fails as it must: True; vertices: True; denominator 192 geom-instances)
```

## Provenance
Blob ids by `git ls-tree` at HEAD and at `92059373a3`; the leg executed only in the `git archive` under the scratchpad (`_gen/` created there, never in the shared tree); zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-426.
