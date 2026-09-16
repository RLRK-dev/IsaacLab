# pZ — pre-registered R0 leg (the only leg that decides "the existing control class is right on UR15-B"): convergence only, static class

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-16 18:04 JST on m-p18-356 (p11 §17.1 @ `dc090f7753`, Rs1 Q1 verbatim via m-p4-265). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Authorization (Rs1 Q1, verbatim)**: 「認可する。p0が作り、pZが独立に検証・実行する。」 scope 「物理ステップを進めず、実行副作用のあるdriverをimportしない静的検査に限定します。収束確認と、衝突・把持・動的追従の成立は区別します。」 **Order**: this prereg → p0 builds the harness (a new file, name = p0's) → pZ verifies it, executes it independently, reports **convergence only**.
**Object (when it exists)**: p0's harness at a commit (content-pinned) and its output record. **Written before it exists**: at 18:04:59 JST no harness file is named yet and driver commits after `3370f7a872` = 0. Base driver blob for the copied functions = `d2bc133e1320` @ `3370f7a872` (re-pinned if the driver moves first).

## Rows (bars from v3 §10 R0 / §11 / §17.1; grade is this court's)

| # | row | requirement |
|---|---|---|
| 1 | copy fidelity | the harness's `solve_ik`, `pose_menu`, `_wrap`, `_rdes`, `pinch` (and `pinch_jac` if used) are **AST-equal** to the same-named statements in the base driver blob after the one permitted rebinding (module globals `m`/`d`/`AXFIX`/`QADR`/`VADR`/`PAD`/`TOOLB`/`CLAWG`/`SIDES`/`_spec` → the composed model's), enumerated in the harness; any other edit to the copied bodies = FAIL |
| 2 | static class — with positive controls | (a) **`mj_step` = 0**: measured by a counter I install on `mujoco.mj_step` when I execute the harness; positive control = the counter reads 1 on a copy with one injected step. (b) **driver-family import = 0**: static sweep of the harness source for `ur15_steps_wired`, `ur15_steps`, `kinonly_step_solve`, `subprocess`, `runpy`, `exec(`, `__import__`, `importlib` → 0 hits; runtime: `sys.modules` after execution holds none of the driver family; positive control = the sweep flags a copy with one added import line. (c) no write to any tracked file; outputs only under a named scratch/`_gen` directory, sha-pinned at read |
| 3 | composed models | `build_side()` @ `b7a5e39ecf` (== HEAD blob `17c79f596c…`), L = stock arm + ko (sign −1), R = mirrored arm + mirrored ko (sign +1), C-2 constants, env overrides unset; identity check against my R3 build: same `nq`/`nbody`/`ngeom` and body names; `AXFIX` re-measured on each composed model (seed `:600`, finger 0) == my banked values (`98d8e63173` instrument) to **1e-9** |
| 4 | targets | the L column (tuple element 2) and the R column (element 3) of `STEPS` (landed blob from `:2889`), constants resolved from the spec and the driver's own literal definitions read as text; the harness prints the resolved rows and I recompute them; count reported as the denominator |
| 5 | run form | per side, per target row: `solve_ik(t, tgt, tries=None, iters=300, seed=<one fixed int>, near=None, other=None, re_max=0.05)` (wired defaults `:2054`); `tries=None` ⇒ `n_try = 2·len(POSES)` and `pose_menu(t)` has the same length on both sides (its body depends on `t` only through the sign) ⇒ **the same seed gives the same draw at the same candidate index on both sides** |
| 6 | converged := the wired definition | `pe = |tgt − pinch(t, sc)| ≤ 0.002 m` and `re_ ≤ re_max` as `solve_ik` itself tests at landed `:2144/:2147` (quoted in the verdict); per row: pe, re, converged flag, chosen candidate index |
| 7 | bar (§10 R0) | **rows where L converges and R does not = 0**; R-converged rows / denominator reported; **R converged = 0 → §11 STOP-and-report** (the class cannot express B; no method swap, no fix by this desk); the symmetric count (R converges, L not) reported too |
| 8 | negative control — the leg must be able to fail | the R target rows solved on the **L** composed model (the wrong side of the yoke): convergence must differ from the R run on ≥ 1 row; if no row differs, the predicate cannot tell B from L and the leg is dead |
| 9 | independent execution | I run p0's harness from a `git archive` of its commit (never the dirty shared tree), pin its output; **and** my own instrument loads the same functions **from the driver blob's text** (not from p0's file) onto my composed models and re-solves every row with the same seed: converged flags equal row-for-row and pe/re equal to ≤ 1e-9 |
| 10 | report form (Rs1 Q1, §17.1, §17.4) | every line carries 「収束のみ／衝突・把持・動的追従は未証明」; stop-cause tag ∈ {instrument calibration stop, controller non-convergence, other}; the composed model has no column, cable or other arm, so `other=`/clearance/path are **vacuous by construction** — said, not implied |
| 11 | pins / no physics | harness commit + content sha; base blob; my instrument's sha; `mj_forward`/`mj_kinematics` only; route run (2) / #69 untouched |

## Provenance
v3 §10 R0 row, §11, §17.1 read at `dc090f7753`; the landed driver blob `d2bc133e1320` read as text; Rs1's words via m-p4-265/m-p18-353/356. Zero tracked-content modifications by pZ. Committed by pZ under the standing custody form (m-p18-344), pathspec-limited, --no-verify, no push.

## Addendum (2026-09-16 18:08 JST) — p4's condition (i) made an explicit row with its negative control (m-p4-268 via m-p18-360; kickoff 09-16 §3 @ HEAD)

- **Row 1′ (identity of the solver under test)**: the harness's `solve_ik` + dependencies (`pose_menu`, `_wrap`, `_rdes`, `pinch`, `pinch_jac` if used) are **AST-equal** to the same-named statements of the landed driver blob (`d2bc133e1320` @ `3370f7a872`, re-pinned if the driver moves) after the one enumerated rebinding of module globals. **Negative control, fired at leg time**: a copy of the harness's solver with **one literal changed** (e.g. `0.002 → 0.003` in the acceptance test) must read **unequal** under the same comparison; if it reads equal, the comparison is dead and row 1′ is not counted. Without this row R0 would measure the convergence of "a similar solver", not of the controller under test — p4's wording, adopted. Rows 1-11 unchanged; supersedes sha `ba24c5a529865dbf…` @ bf4433bfe6. Objects at writing: none (driver commits after `3370f7a872` = 0).

## Addendum 2 (2026-09-16 18:26 JST) — what the landed solver actually needs, measured before the harness exists (driver commits after `3370f7a872` = 1; harness files under `p4_ur15_sim_20260727/` matching r0/harness = 0)

1. **The copied closure is 14 functions, not 5.** Reachability from `solve_ik` (`:2054-2474`, 421 lines) in the landed blob `d2bc133e1320`: `solve_ik → pose_menu, _wrap, _rdes, pinch, touching, sigma_min → wrist_jac, column_gap, path_mast_min, arm_pair_min, path_arm_min, furniture_gap, path_furniture_min`. Module globals read by that closure (**29**): `ARMG, ARM_CLEARANCE, ARM_DECIDE_CUTOFF, ARM_PAIR_CUTOFF, AXFIX, COLFREE, COLG, COLUMN_R, FURNG, GNAME, LIM, PAD, QADR, Rotation, SIDES, SIGMA_FLOOR, SIGMA_GOOD, SIGMA_PENALTY, TOOLB, VADR, d, m, math, mujoco, np, os, re` (+ `_cost`, `_cost_terms`, which are nested inside `solve_ik`, not globals). Row 1/1′ binds to **this** closure: every reachable function AST-equal to the blob; the rebinding list = exactly these globals, each set by the driver's own rule on the composed model (`ARMG[t]` from `ARMB[t]`; `COLFREE[t] = sorted(ARMG[t])`; `COLG = []` and `FURNG = []` because the composed model has no mast and no furniture — the driver's own `COLG` comprehension filters `g >= 0`; `LIM = np.array(LIMS)` from the spec; `AXFIX` re-measured).
2. **Which clearance branches run on a one-arm model** (read from the guards): with `other=None`, `near=None`, and the env switches `FURNITURE`/`ARM_PATH` **unset** — `touching` (arm self-collision, active), `column_gap` and `path_mast_min` (active but **vacuous** with `COLG = []`: best stays 1e9), `sigma_min` (active). `arm_pair_min`/`path_arm_min` are skipped by `other is None`; the furniture tests by the env switch. The leg records which branches ran; the harness must not set those env switches.
3. **Targets: rows 2-5 are cable-dependent.** `GL`/`GR` (`:1241-1242`, re-measured at `:2812-2813`) come from `cable_at(x)` on the live cable, not from constants. **Pre-registered static values**, computed by the driver's own `cable_at` rule on the L1 cell dump `_gen/_steps_cell_full.xml` (sha256 `4158e4e638e9b0fc…`, mesh assets resolved, `mj_forward` at the dump's initial state; `GRASP_CENTRE_X = C1[0]`, `GRIP_HALF_SPAN = 0.044`): **`GL = (0.106, 0.28, 0.954)`, `GR = (0.194, 0.28, 0.954)`** (links cab27 / cab32). Rows 6-18 are constants: `C1 = (0.15, 0.35)`, `C2 = (0.04, 0.40)`, `LX1/RX1 = 0.106/0.194`, `LX2/RX2 = −0.004/0.084`, `RX_MID = 0.095`, `Z_RISE_REST = 1.030`, `Z_RISE_ROUTE = 0.980`, `Z_SEAT = seat_z(FLOAT_Z) = 0.809`. **17 rows** (steps 2-18), R column = tuple element 3. The harness must name the source of its rows 2-5 numbers; my re-solve uses the values above and accepts the harness's if equal to ≤ 1e-9. ⚠ The R targets are **not** mirror images of the L targets (same cable line `y = 0.28`, x offset by the 88 mm span): R0 compares each side to its own wired target, as `STEPS` does.
4. **Non-convergence is a raise.** `solve_ik` raises `RuntimeError("no IK solution for {t} at {tgt}")` at `:2339` when no candidate passes; the leg catches it per row and tags the row **controller non-convergence** (§17.4); it prints per candidate unless `quiet=True` — the harness passes `quiet=True` or captures stdout.
5. Rows 1-11 and 1′ otherwise unchanged; supersedes sha `bf6362e3ae008c94…` @ 642a9162f0.

## Addendum 3 (2026-09-16 18:35 JST) — the instrument exists and ran before the harness; the global set is 30 (my scan had a bug); and convergence alone does **not** discriminate UR15-B from the rotated-copy defect (measured)

**Corrections to addendum 2.** (a) The closure reads **30** module globals, not 29: my first scan treated the base name of a subscript store (`_DEPTH_AUDIT["cand_evals"] += 1`) as a local, so it missed the three mutable module-state dicts `_DEPTH_AUDIT` (init `:1564`), `CLEARANCE_REPORT` (`:1387`, `{}`), `LAST_CLEAR` (`:2027`, `{}`); the instrument found them by `NameError` and the v2 scan (store-context Names only are locals) confirms the set of 30. They are bound by `exec` of the driver's **own** `Assign` (AST unparse), never retyped. (b) `ARMB[t]` on the composed model = bodies prefixed `a_` ∪ `g_` (the driver's `:499` rule with the composed prefixes).

**The instrument** `pz_r0.py` (appendix C; sha256 `8dbad9840ab4102f4ff7403bd4cd1b38b7027119bc272626570942a52ab4b34e`): the 14-function closure extracted from the landed blob **as text by AST segments** (closure sha256 `a87deb96fde026b3…`, blob `a6a42f06…`), `exec`'d into a namespace bound to a composed model from `build_side()` @ `b7a5e39ecf`; `mj_step` counted by wrapping `mujoco.mj_step` (**0** calls in every run); `sys.modules` after each run holds **no** driver-family module; start pose `HOME_POSE`; `solve_ik(t, tgt, tries=None, iters=300, seed=1, near=None, other=None, quiet=False)` with stdout captured; `n_try = 22` (menu of 11 on both sides). Rows 2-5 targets = the dump-derived values of addendum 2. Driver commits after `3370f7a872` at run time: 1.

**Pre-computed expectations (the harness must reproduce the flags; the q's if it uses the same start and rebinding):**

| step | L target (x,y,z) | L conv / solved / pe mm | R target | R conv / solved / pe mm | L-model on R tgt: solved | rotated copy: solved | stock hand: solved |
|---|---|---|---|---|---|---|---|
| 2 | (0.106, 0.28, 1.03) | ✓ / 11 / 1.2652 | (0.194, 0.28, 1.03) | ✓ / 13 / 0.0 | 10 | 15 | 15 |
| 3 | (0.106, 0.28, 0.954) | ✓ / 13 / 0.0 | (0.194, 0.28, 0.954) | ✓ / 13 / 0.0 | 13 | 14 | 16 |
| 4 | (0.106, 0.28, 0.954) | ✓ / 13 / 0.0 | (0.194, 0.28, 0.954) | ✓ / 13 / 0.0 | 13 | 14 | 16 |
| 5 | (0.106, 0.28, 1.03) | ✓ / 11 / 1.2652 | (0.194, 0.28, 1.03) | ✓ / 13 / 0.0 | 10 | 15 | 15 |
| 6 | (0.106, 0.35, 0.98) | ✓ / 12 / 0.0 | (0.194, 0.35, 0.98) | ✓ / 15 / 0.0 | 12 | 14 | 16 |
| 7 | (0.106, 0.35, 0.809) | ✓ / 12 / 0.0 | (0.194, 0.35, 0.809) | ✓ / 10 / 0.0 | 13 | 12 | 13 |
| 8 | (0.106, 0.35, 0.809) | ✓ / 12 / 0.0 | (0.194, 0.35, 0.809) | ✓ / 10 / 0.0 | 13 | 12 | 13 |
| 9 | (0.106, 0.35, 0.809) | ✓ / 12 / 0.0 | (0.194, 0.35, 0.809) | ✓ / 10 / 0.0 | 13 | 12 | 13 |
| 10 | (0.106, 0.35, 0.98) | ✓ / 12 / 0.0 | (0.194, 0.35, 0.98) | ✓ / 15 / 0.0 | 12 | 14 | 16 |
| 11 | (-0.004, 0.4, 0.98) | ✓ / 12 / 0.0 | (0.084, 0.4, 0.98) | ✓ / 12 / 0.0 | 14 | 13 | 15 |
| 12 | (-0.004, 0.4, 0.98) | ✓ / 12 / 0.0 | (0.084, 0.4, 0.98) | ✓ / 12 / 0.0 | 14 | 13 | 15 |
| 13 | (-0.004, 0.4, 0.98) | ✓ / 12 / 0.0 | (0.095, 0.4, 0.98) | ✓ / 12 / 0.0 | 14 | 13 | 15 |
| 14 | (-0.004, 0.4, 0.98) | ✓ / 12 / 0.0 | (0.095, 0.4, 0.98) | ✓ / 12 / 0.0 | 14 | 13 | 15 |
| 15 | (-0.004, 0.4, 0.809) | ✓ / 10 / 0.0 | (0.084, 0.4, 0.809) | ✓ / 13 / 0.0 | 10 | 13 | 14 |
| 16 | (-0.004, 0.4, 0.809) | ✓ / 10 / 0.0 | (0.084, 0.4, 0.809) | ✓ / 13 / 0.0 | 10 | 13 | 14 |
| 17 | (-0.004, 0.4, 0.809) | ✓ / 10 / 0.0 | (0.084, 0.4, 0.809) | ✓ / 13 / 0.0 | 10 | 13 | 14 |
| 18 | (-0.004, 0.4, 0.98) | ✓ / 12 / 0.0 | (0.084, 0.4, 0.98) | ✓ / 12 / 0.0 | 14 | 13 | 15 |

- Own targets: **L 17/17, R 17/17** converged (R exact; L rows 2/5 within 1.27 mm of the 2 mm bar). "L converges and R does not" = **0 rows**; **no §11 STOP** on B. Stop-cause tag for every row: none.
- ⚠ **Row 8's negative control did not fire, and neither do the two that matter**: the **L model on the R targets** converges 17/17; the **rotated-copy defect** (stock arm + stock hand on the right mount, sign +1 — the defect Rs1's video caught) converges **17/17**; the acceptance's own negative (**mirrored arm + stock hand**) converges **17/17**. Only the per-row candidate counts differ (15 / 14 / 17 of 17 rows) — a fingerprint, not a correctness bar. ⇒ **As written (convergence only, own targets), R0 cannot tell a correct UR15-B from the rotated copy: a wrong right arm passes its bar.** What R0 still answers, and Rs1 Q1 limits it to: *does the existing class converge on B* (the §11 STOP question) — yes, on all 17 wired targets. v3 §10's sentence "R0 = the only leg that decides B is right" is contradicted by this measurement; the "B is right" evidence stays with the static legs (R1/R1′/R2: asset and composition mirror), not with R0.
- **A measured candidate for a discriminator — a question for p11 (design court), not a row**: solving the **mirror images of the L targets** on the right side, the identity joint map predicts `q_R == q_L` row for row on a correct B. Measured: correct B **5/17** rows equal (< 1e-6 rad; the other rows differ because `solve_ik` chooses among several converged candidates and that choice is not mirror-deterministic), rotated copy **0/17**, stock hand **0/17**. A per-menu-index form (`pose_only=k`, two tries per index) may sharpen it; whether R0 should carry such a row is p11's, then p4's. Limits: measured on `HOME_POSE` start, seed 1, the 17 wired targets, one mounting.

**Rows**: 1-11, 1′ and addendum 2 stand, with row 7 read as the §11 STOP test only and row 8 recorded as failed-to-fire. Supersedes sha `e8b74bc73a646d62…` @ 511a178176.

## Appendix C — `pz_r0.py` (verbatim, sha256 8dbad9840ab4102f4ff7403bd4cd1b38b7027119bc272626570942a52ab4b34e)
```python
"""pZ R0 instrument: the wired solver closure, loaded from the driver BLOB TEXT (never imported), rebound onto a composed one-arm model."""
import sys, os, io, re, ast, math, json, hashlib, contextlib, numpy as np, mujoco
from scipy.spatial.transform import Rotation
BLOB, W, SIDE, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, W)
with contextlib.redirect_stdout(io.StringIO()):
    import ur15_gripper_mirror_acceptance as g; import ur15_cell_spec as spec
src = open(BLOB).read(); tree = ast.parse(src)
CLOSURE = ["solve_ik","pose_menu","_wrap","_rdes","pinch","touching","sigma_min","wrist_jac","column_gap","path_mast_min","arm_pair_min","path_arm_min","furniture_gap","path_furniture_min"]
fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
code = "\n".join(ast.get_source_segment(src, fns[f]) for f in CLOSURE)
closure_sha = hashlib.sha256(code.encode()).hexdigest()
# composed model
MODEL = os.environ.get("PZ_R0_MODEL", SIDE)   # L | R | RC (rotated copy: stock arm + stock hand on the RIGHT mount) | NH (mirrored arm + stock hand, the acceptance's negative)
m, d = {"L": lambda: g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["L"]), "R": lambda: g.build_side("ur15_base_mirrored.xml", g.KO_MIRROR, g.acc.SIDE_SIGN["R"]),
        "RC": lambda: g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"]), "NH": lambda: g.build_side("ur15_base_mirrored.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"])}[MODEL]()
B = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n); G = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n); J = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)
t = SIDE
QADR = {t: [m.jnt_qposadr[J(f"a_{j}")] for j in g.acc.J6]}; VADR = {t: [m.jnt_dofadr[J(f"a_{j}")] for j in g.acc.J6]}
PAD = {t: [B("g_left_pad"), B("g_right_pad")]}; TOOLB = {t: B("g_base")}
assert min(QADR[t]) >= 0 and min(PAD[t]) >= 0 and TOOLB[t] >= 0
def _own(prefix): return {b for b in range(m.nbody) if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or "").startswith(prefix)}
ARMB = {t: _own("a_") | _own("g_")}                       # the driver's rule (:499) with the composed prefixes
ARMG = {t: {gg for gg in range(m.ngeom) if m.geom_bodyid[gg] in ARMB[t]}}
GNAME = {gg: (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, gg) or f"g{gg} on {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.geom_bodyid[gg]) or 'an unnamed body'}") for gg in range(m.ngeom)}
COLG = []; COLFREE = {t: sorted(ARMG[t])}; FURNG = []      # no mast, no furniture on the composed model
LIM = np.array(spec.LIMS); SIDES = spec.SIDES
# AXFIX by the driver's rule (:594-616): seed q, fingers 0, throwaway data
sc0 = mujoco.MjData(m)
for k, a in enumerate(QADR[t]): sc0.qpos[a] = [0.0, -1.2, 1.0, -1.4, -1.57, 0.0][k]
mujoco.mj_forward(m, sc0)
pl, pr = np.array(sc0.xpos[PAD[t][0]]), np.array(sc0.xpos[PAD[t][1]]); c_w = (pr-pl)/max(np.linalg.norm(pr-pl),1e-9); pinch_w = 0.5*(pl+pr)
a_w = np.array(sc0.xpos[TOOLB[t]]) - pinch_w; a_w = a_w/max(np.linalg.norm(a_w),1e-9); Rt = np.array(sc0.xmat[TOOLB[t]]).reshape(3,3)
c_l, a_l = Rt.T @ c_w, Rt.T @ a_w; AXFIX = {t: np.column_stack([c_l, np.cross(a_l, c_l), a_l]).T}
# start state = HOME_POSE (documented choice)
for k, a in enumerate(QADR[t]): d.qpos[a] = spec.HOME_POSE[k]
mujoco.mj_forward(m, d)
ns = dict(m=m, d=d, QADR=QADR, VADR=VADR, PAD=PAD, TOOLB=TOOLB, AXFIX=AXFIX, ARMG=ARMG, GNAME=GNAME, COLG=COLG, COLFREE=COLFREE, FURNG=FURNG, LIM=LIM, SIDES=SIDES,
          ARM_CLEARANCE=spec.ARM_CLEARANCE, ARM_DECIDE_CUTOFF=spec.ARM_DECIDE_CUTOFF, ARM_PAIR_CUTOFF=spec.ARM_PAIR_CUTOFF, COLUMN_R=spec.COLUMN_R,
          SIGMA_FLOOR=spec.SIGMA_FLOOR, SIGMA_GOOD=spec.SIGMA_GOOD, SIGMA_PENALTY=spec.SIGMA_PENALTY, Rotation=Rotation, math=math, mujoco=mujoco, np=np, os=os, re=re)
# module state the closure mutates (found by the v2 scan: store-only locals): initialised exactly as the driver does, by AST unparse of its own Assign
_mod = {n.targets[0].id: n for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
for _name in ("_DEPTH_AUDIT", "CLEARANCE_REPORT", "LAST_CLEAR"):
    exec(ast.unparse(_mod[_name]), ns)
steps = 0
_orig = mujoco.mj_step
def _counted(*a, **k):
    global steps; steps += 1; return _orig(*a, **k)
mujoco.mj_step = _counted
exec(compile(code, "<wired closure>", "exec"), ns)
# targets (pre-registered static values; rows 6-18 from spec constants; rows 2-5 from the L1 dump by cable_at)
GL, GR = (0.106, 0.28, 0.954), (0.194, 0.28, 0.954); C1, C2 = spec.C1, spec.C2; H = spec.GRIP_HALF_SPAN
LX1, RX1 = C1[0]-H, C1[0]+H; LX2, RX2 = C2[0]-H, C2[0]+H; RX_MID = float(np.mean([C1[0], C2[0]])); ZR, ZQ, ZS = spec.Z_RISE_REST, spec.Z_RISE_ROUTE, spec.seat_z(spec.FLOAT_Z)
L_COL = [(GL[0],GL[1],ZR), GL, GL, (GL[0],GL[1],ZR), (LX1,C1[1],ZQ), (LX1,C1[1],ZS), (LX1,C1[1],ZS), (LX1,C1[1],ZS), (LX1,C1[1],ZQ), (LX2,C2[1],ZQ), (LX2,C2[1],ZQ), (LX2,C2[1],ZQ), (LX2,C2[1],ZQ), (LX2,C2[1],ZS), (LX2,C2[1],ZS), (LX2,C2[1],ZS), (LX2,C2[1],ZQ)]
R_COL = [(GR[0],GR[1],ZR), GR, GR, (GR[0],GR[1],ZR), (RX1,C1[1],ZQ), (RX1,C1[1],ZS), (RX1,C1[1],ZS), (RX1,C1[1],ZS), (RX1,C1[1],ZQ), (RX2,C2[1],ZQ), (RX2,C2[1],ZQ), (RX_MID,C2[1],ZQ), (RX_MID,C2[1],ZQ), (RX2,C2[1],ZS), (RX2,C2[1],ZS), (RX2,C2[1],ZS), (RX2,C2[1],ZQ)]
TSEL = sys.argv[5] if len(sys.argv) > 5 else "own"
TGT = {"own": (L_COL if SIDE == "L" else R_COL), "Rtargets": R_COL, "MxL": [(-x, y, z) for (x, y, z) in L_COL]}[TSEL]   # MxL = the mirror images of the L targets (identity-map prediction: q_R == q_L on a correct B)
rows = []
for i, tgt in enumerate(TGT):
    step = i + 2; buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): q = ns["solve_ik"](t, np.array(tgt, float), tries=None, iters=300, seed=1, near=None, other=None, quiet=False, label=f"R0 step{step}")
        sc = mujoco.MjData(m); sc.qpos[:] = d.qpos
        for k, a in enumerate(QADR[t]): sc.qpos[a] = q[k]
        mujoco.mj_forward(m, sc); pe = float(np.linalg.norm(np.array(tgt) - ns["pinch"](t, sc)))
        line = [l for l in buf.getvalue().split("\n") if "solved /" in l]; mm = re.search(r"(\d+) solved / (\d+) collision-free", line[0]) if line else None
        rows.append(dict(step=step, tgt=[round(x,4) for x in tgt], q=[round(float(v),9) for v in q], converged=True, pe_mm=round(pe*1000,4), solved=int(mm.group(1)) if mm else None, clear=int(mm.group(2)) if mm else None, tag="none"))
    except RuntimeError as e:
        rows.append(dict(step=step, tgt=[round(x,4) for x in tgt], converged=False, err=str(e)[:80], tag="controller non-convergence"))
rec = dict(side=SIDE, model=MODEL, module_state_init={k: ast.unparse(_mod[k])[:90] for k in ("_DEPTH_AUDIT","CLEARANCE_REPORT","LAST_CLEAR")}, targets=TSEL, blob_sha256=hashlib.sha256(src.encode()).hexdigest(), closure_sha256=closure_sha, mj_step_calls=steps, driver_family_in_sys_modules=[k for k in sys.modules if k.startswith(("ur15_steps","kinonly"))], start="HOME_POSE", n_try=2*len(ns["pose_menu"](t)), rows=rows)
open(OUT, "w").write(json.dumps(rec, indent=1)); print(json.dumps({k: v for k, v in rec.items() if k != "rows"})); print("converged rows:", sum(r["converged"] for r in rows), "/", len(rows), "| pe_mm max:", max([r.get("pe_mm", 0) for r in rows] or [0]))
for r in rows: print(" ", r)
```
