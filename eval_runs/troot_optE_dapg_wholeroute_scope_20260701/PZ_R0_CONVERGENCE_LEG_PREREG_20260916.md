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

## Addendum 4 (2026-09-20 08:18:24 JST) — static read of p0's follow-up harness `ffa612ea33` before p11's §17 line: rows 1/1′/2b/2c/3 hold statically, and the row-4 re-pin is number-preserving (spec-nominal == addendum 2's values, difference 0)

**Order of existence at writing**: HEAD `2f7e9208fb`; harness commits after `ffa612ea33` = 0; p11 design-doc commits after `2743fc4549` = 0 (no §17 line on the R0 targets' source yet); the hub's ledger last banked @ `5adf8d6483 2026-09-16 18:44` (PZ-230 not yet banked). The **leg itself (execution, rows 2a-runtime, 3-AXFIX, 5-11) is not run here** — p4's order (kickoff item 16 @ `6592e12c49`, m-p4-276 via m-p18-377) puts it after p11's line. This addendum records what the object already shows statically so that p11's line can be written against measured facts, and so that a later leg does not re-derive them.

**Object**: `ffa612ea33` (author date 2026-09-20 08:10:06 JST, parent `b1f75124de`, +491/−196, one file), harness blob `0163e36e5187` (sha256 `53e5daa5f426e6b173e6931071e37189d9c8c900395c47c13de2e3d91e83112b`, 1,073 lines); its previous blob `1d6b53840028` @ `d038e2536f` (778 lines, sha256 `28115a3d523a1061…`). Driver blobs compared against: `84a372439c59` @ `96e9ece175` and `d2bc133e1320` @ `3370f7a872`.

| row | static result on `ffa612ea33` | measurement (appendix D/E instruments; python3 AST only, nothing imported or run) |
|---|---|---|
| 1 / 1′ copy fidelity | **holds statically** | 16 top-level defs of the harness have the same name in the driver and are **raw-`ast.dump`-equal** (no N1-N3) to **both** driver blobs: the 14-function closure of addendum 2 (`solve_ik :131-551`, `pose_menu`, `_wrap`, `_rdes`, `pinch`, `touching`, `sigma_min`, `wrist_jac`, `column_gap`, `path_mast_min`, `arm_pair_min`, `path_arm_min`, `furniture_gap`, `path_furniture_min`) + the driver's rules `_own_bodies` (:853) and `_measure_axfix` (:871). v1's three stubs and four raisers are gone. **Negative control fired**: the harness's `solve_ik` with `0.002 → 0.003` reads **unequal** to the blob (the comparison is alive) |
| 1′ the 30-global binding | **30/30 bound** | free names of the closure (v2 scan, store-context Names = locals) = the 30 of addendum 3; the harness's copied defs read exactly those 30; every one is bound at module level or in `_bind()` via `global`. By statement: **16 bound by a statement AST-equal to the driver's own** (`ARMG`, `AXFIX = _measure_axfix()`, `COLFREE`, `COLG`, `FURNG`, `GNAME`, `CLEARANCE_REPORT = {}`, `LAST_CLEAR = {}`, `LIM = np.array(LIMS)`, `_DEPTH_AUDIT` init, `Rotation`, `math`, `mujoco`, `np`, `os`, `re`); **4 with the composed prefixes** (`QADR`/`VADR` `a_{j}` for `{t}_{j}`, `PAD` `g_{s}_pad` for `{t}g_{s}_pad`, `TOOLB` `g_base` for `{t}g_base`) plus `ARMB = _own_bodies("a_") | _own_bodies("g_")` for the driver's `{t}_`/`{t}g_` (`:499`, = addendum 3 (b)); `SIDES` narrowed to `{t: _spec.SIDES[t]}`; `m`/`d` = the composed model; the 7 spec constants (`ARM_CLEARANCE`, `ARM_DECIDE_CUTOFF`, `ARM_PAIR_CUTOFF`, `COLUMN_R`, `SIGMA_FLOOR/GOOD/PENALTY`) imported from `ur15_cell_spec` by name, the driver's source. `mujoco.mj_step` is rebound to a counter (the row-2a witness) — the one rebinding outside the closure's globals |
| 2b static sweep | **0 hits** | `ur15_steps_wired`, `ur15_steps`, `kinonly_step_solve`, `subprocess`, `runpy`, `exec(`, `__import__`, `importlib` = 0 each; `py_compile` OK (env7 3.12) |
| 2c outputs | **untracked path only** | default `--out` = `p4_ur15_sim_20260727/_gen/r0_convergence/` (tracked files under `_gen` = 0); my execution will run from a `git archive` in the scratchpad with `--out` there |
| 3 composed models | **same builder** | `build_side` @ HEAD blob `ad1d80d49f24` == the `b7a5e39ecf` blob (same blob id; all 6 defs AST-equal). Measured today on both sides: `nbody` 22, `ngeom` 38, `nq` 14; bodies outside `a_`/`g_` = `world`, `column` with **0 geoms** ⇒ 0 collidable non-arm geoms; `ncon` = 0 at `qpos = 0` and at the AXFIX seed pose |
| 4 targets (re-pin, pending p11) | **numbers unchanged** | the harness binds rows 2-5 to **spec-nominal committed text**: `x = C1[0] ∓ GRIP_HALF_SPAN`, `y = REST_Y`, `z = REST_TOP + CABLE_R` (driver `:337-338` cable placement, `:1246` `GRASP_CENTRE_X` default) — evaluated from `ur15_cell_spec.py` blob `6bdf7ea4f9ca` (`C1 :537`, `GRIP_HALF_SPAN :65`, `REST_Y :433`, `REST_TOP :512`, `CABLE_R :57`) = **`GL = (0.106, 0.28, 0.954)`, `GR = (0.194, 0.28, 0.954)` — identical to addendum 2's dump-derived values, difference 0.0 in all six numbers** (the L1 dump holds the cable at exactly that placement pose). The U0 settled values `(0.0986, 0.28, 0.9488)` / `(0.1886, 0.28, 0.951)` (`_gen/dod_c2_20260810/run.log :93`, sha256 `04599b84e34be51e…`, present on disk, untracked) are **reported beside, not solved**. Rows 6-18: `Z_SEAT = seat_z(FLOAT_Z) = 0.809`, `Z_RISE_REST = 1.030`, `Z_RISE_ROUTE = 0.980`, `RX_MID = 0.095` = addendum 2. ⇒ addendum 3's expectation table applies unchanged to the harness's binding targets. The formal re-pin follows p11's line: if (b) spec-nominal, these numbers; if (a) the U0 values, rows 2-5 move ≤ 7.4 mm in x / ≤ 5.2 mm in z and are re-solved |
| 5 / 6 run form, converged | **matches the wired form** | `_solve_rows` (:969): `solve_ik(t, tgt, tries=None, iters=300, seed=seed, near=None, other=None, re_max=re_max, quiet=True)`, defaults seed 1 / re_max 0.05; converged := `solve_ik` returned; `RuntimeError("no IK solution …")` → tag `controller non-convergence`, `AssertionError` in the closure → `instrument calibration stop`, other `RuntimeError` → `other` (§17.4); `pe` re-checked on a throwaway `MjData` (kinematics only), `re` not re-checked — stated in the record, not hidden; start pose = the spec's `HOME_POSE` = my instrument's |
| 7 / 8 bar, negative control | **computed as pre-registered** | `main` (:1007): `L_converges_R_not` must be `[]`, `R_converged == 0` → STOP flag; negative control (R column on the L model) **recorded** (`negative_control_fired`) and no longer gates the exit — consistent with addendum 3 (row 8 measured as failed-to-fire); exit 0 iff bar ∧ ¬STOP |
| R0-ii | absent | `pose_only` does not occur in the harness — held for p11 (m-p4-276 ③) |

**A v1 concern, closed by measurement.** v1 (`1d6b53840028`) stubbed `touching → []`. The driver's `touching` (`:576-591`) reports contacts between this arm's geoms (`ARMG`) and geoms **outside** it; on the composed model there are 0 geoms outside the `a_`/`g_` bodies, so the real function returns ∅ there — v1's stub was equivalent by measurement, not only "by construction". Moot for v2 (the real function is copied), recorded so the reasoning is not lost.

**What remains for the leg (after p11's line)**: run `ffa612ea33` from a `git archive` under my `mj_step` counter (row 2a + positive control), `sys.modules` sweep, AXFIX vs my banked values ≤ 1e-9 (row 3), the 17 rows both sides (rows 5-7), negative control (row 8), row-for-row cross-check with `pz_r0.py` (row 9), report form with stop-cause tags (row 10), pins (row 11); plus R0-ii if p11 adopts it. Nothing executed by this desk for this addendum; route run (2) / #69 / D4′ / WIP untouched.

Supersedes sha `7746348239a179527ea0bdb1ebee60b3e622cd2f0d9fa0f0886490ea6bd92836` @ dd7cfd18b4 (rows 1-11, 1′, addenda 2-3 stand).

## Appendix D — `pz_r0_static.py` (verbatim; sha256 45e6b5f93d62157c3c9006de4bb779789781245d92faa98be091517d154f1419)
```python
"""pZ static read of the R0 harness: copy fidelity (raw ast.dump), closure coverage, free-name binding, negative control."""
import ast, sys, builtins
H, BLOB = sys.argv[1], sys.argv[2]
hs = open(H).read(); bs = open(BLOB).read()
ht, bt = ast.parse(hs), ast.parse(bs)
hf = {n.name: n for n in ht.body if isinstance(n, ast.FunctionDef)}
bf = {n.name: n for n in bt.body if isinstance(n, ast.FunctionDef)}
CLOSURE = ["solve_ik","pose_menu","_wrap","_rdes","pinch","touching","sigma_min","wrist_jac","column_gap","path_mast_min","arm_pair_min","path_arm_min","furniture_gap","path_furniture_min"]
print("== per-def raw ast.dump equality (harness vs blob) ==")
eq = {}
for n, f in hf.items():
    if n in bf:
        eq[n] = ast.dump(f) == ast.dump(bf[n])
        print(f"  {n:22} harness {f.lineno}-{f.end_lineno:<4} blob {bf[n].lineno}-{bf[n].end_lineno:<5} equal={eq[n]}")
print("== my 14-function closure: status in the harness ==")
hassign = {}
for s in ht.body:
    if isinstance(s, ast.Assign):
        for tg in s.targets: hassign[ast.unparse(tg)] = ast.unparse(s.value)[:60]
for n in CLOSURE:
    if n in hf: st = "COPY(AST-equal)" if eq.get(n) else "REDEFINED(stub, not equal)"
    elif n in hassign: st = f"ASSIGNED = {hassign[n]}"
    else: st = "ABSENT"
    print(f"  {n:22} {st}")
# free names (v2: store-context Names are locals; params too)
def free(fn):
    params = {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
    if fn.args.vararg: params.add(fn.args.vararg.arg)
    if fn.args.kwarg: params.add(fn.args.kwarg.arg)
    loc = set(params); glob_decl = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store): loc.add(n.id)
        if isinstance(n, ast.Global): glob_decl |= set(n.names)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not fn: loc.add(n.name)
        if isinstance(n, ast.arg): loc.add(n.arg)
        if isinstance(n, ast.ExceptHandler) and n.name: loc.add(n.name)
        if isinstance(n, ast.comprehension): pass
    loc -= glob_decl
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in loc and not hasattr(builtins, n.id): out.add(n.id)
    return out
closure_free = set()
for n in CLOSURE:
    if n in bf: closure_free |= free(bf[n])
closure_free -= set(CLOSURE)
print(f"== driver closure (14 fns) free names: {len(closure_free)} ==\n  {sorted(closure_free)}")
copied = [n for n in hf if n in bf and eq.get(n)]
cf = set()
for n in copied: cf |= free(hf[n])
cf -= set(hf)
print(f"== harness copied defs ({len(copied)}) free names: {len(cf)} ==\n  {sorted(cf)}")
# binding in the harness: module-level names
bound = set()
for s in ht.body:
    if isinstance(s, ast.Assign):
        for tg in s.targets:
            for n in ast.walk(tg):
                if isinstance(n, ast.Name): bound.add(n.id)
    if isinstance(s, (ast.Import, ast.ImportFrom)): bound |= {(a.asname or a.name).split(".")[0] for a in s.names}
    if isinstance(s, (ast.FunctionDef, ast.ClassDef)): bound.add(s.name)
# names set via `global` inside functions
gset = set()
for f in hf.values():
    for n in ast.walk(f):
        if isinstance(n, ast.Global): gset |= set(n.names)
print(f"== unbound free names of the copied defs at harness module level: {sorted(cf - bound)}  (global-decl in fns: {sorted(gset)})")
print(f"== closure names the harness does NOT bind or define: {sorted(closure_free - bound)}")
# negative control for row 1': one literal changed in the harness's solve_ik must read unequal
src2 = hs.replace("pe > 0.002", "pe > 0.003", 1)
assert src2 != hs, "literal not found"
f2 = {n.name: n for n in ast.parse(src2).body if isinstance(n, ast.FunctionDef)}["solve_ik"]
print("== row 1' negative control: solve_ik with 0.002->0.003 equal to blob? ", ast.dump(f2) == ast.dump(bf["solve_ik"]), "(must be False)")
```

## Appendix E — `pz_r0_bind.py` (verbatim; sha256 6957aa83feb98e780df14e87074d88f6a5562007c76108e56efbeb18b5f35bc7)
```python
"""pZ: for each of the 30 closure globals, compare the harness's binding statement with the driver's own Assign (raw ast.dump)."""
import ast, sys
H, BLOB = sys.argv[1], sys.argv[2]
ht, bt = ast.parse(open(H).read()), ast.parse(open(BLOB).read())
NAMES = ['ARMG','ARM_CLEARANCE','ARM_DECIDE_CUTOFF','ARM_PAIR_CUTOFF','AXFIX','CLEARANCE_REPORT','COLFREE','COLG','COLUMN_R','FURNG','GNAME','LAST_CLEAR','LIM','PAD','QADR','Rotation','SIDES','SIGMA_FLOOR','SIGMA_GOOD','SIGMA_PENALTY','TOOLB','VADR','_DEPTH_AUDIT','d','m','math','mujoco','np','os','re']
def binders(tree, into_fns=True):
    out = {}
    def add(name, node, where):
        out.setdefault(name, []).append((where, node))
    for s in tree.body:
        if isinstance(s, (ast.Import, ast.ImportFrom)):
            for a in s.names: add((a.asname or a.name).split(".")[0], s, "module import")
        if isinstance(s, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            for tg in (s.targets if isinstance(s, ast.Assign) else [s.target]):
                for n in ast.walk(tg):
                    if isinstance(n, ast.Name): add(n.id, s, "module assign")
        if isinstance(s, ast.For):
            for n in ast.walk(s):
                if isinstance(n, (ast.Assign, ast.AugAssign)):
                    for tg in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                        for nn in ast.walk(tg):
                            if isinstance(nn, ast.Name) and isinstance(nn.ctx, ast.Store): add(nn.id, s, "module for-loop")
        if into_fns and isinstance(s, ast.FunctionDef):
            g = set()
            for n in ast.walk(s):
                if isinstance(n, ast.Global): g |= set(n.names)
            for n in ast.walk(s):
                if isinstance(n, (ast.Assign, ast.AugAssign)):
                    for tg in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                        for nn in ast.walk(tg):
                            if isinstance(nn, ast.Name) and nn.id in g: add(nn.id, n, f"in {s.name}()")
    return out
hb, bb = binders(ht), binders(bt, into_fns=False)
for nm in NAMES:
    hs = hb.get(nm, []); bs = bb.get(nm, [])
    if not hs: print(f"  {nm:18} HARNESS: UNBOUND"); continue
    for where, node in hs:
        hsrc = ast.unparse(node).replace("\n", " ")[:110]
        same = any(ast.dump(node) == ast.dump(bn) for _, bn in bs)
        bsrc = (ast.unparse(bs[0][1]).replace("\n", " ")[:90] if bs else "<driver: not module-bound>")
        print(f"  {nm:18} {where:18} equal-to-driver={str(same):5} | H: {hsrc}\n  {'':18} {'':18} {'':17} | D: {bsrc}")
```

## Addendum 5 (2026-09-20 08:39:08 JST) — row 4 re-pinned in the `:2812` link-centre form per v3 §17.7 @ `7427c1764c`: `GL = (0.1125, 0.28, 0.954)` cab27 / `GR = (0.1875, 0.28, 0.954)` cab32, derived twice independently (agreement 1.7e-16); addendum 2's values were the `:1241` commanded-x form and are withdrawn as the bar; the follow-up harness `ffa612ea33` still binds the `:1241` form (catch for p0)

**Order of existence at writing**: p11 §17.7 landed at `7427c1764c` (2026-09-20 08:23:05 JST; design-doc commits after it = 0); harness commits after `ffa612ea33` = 1 (its rows 2-5 binding predates §17.7); HEAD `827766ffa2`. §17.7's order: this re-pin → p0's announce/follow-up → my execution. Nothing physical stepped; the driver never imported.

**§17.7's three readings of the driver, checked in blob `d2bc133e1320` (base of this prereg) by me**: ① `cable_at` `:1210-1217` returns the centre of the link nearest x (body origin + `CABLE_SEG/2` along the link's x axis) — confirmed. ② two module-level bindings of `GL`/`GR`: `:1241-1242` = **x commanded** (`GRASP_CENTRE_X ∓ GRIP_HALF_SPAN`), y/z from the link; `:2812-2813` = **x/y/z all from the link centre** — confirmed by AST (the only Store sites of `GL`/`GR` are `:1241`, `:1242`, `:2812`, `:2813`). ③ `STEPS` is bound at `:2890`, after `:2812-2813`; `:3161` only maps the `RELEASE` strings — confirmed ⇒ at run time rows 2-5 command the `:2812` form. Addendum 2's `(0.106, 0.28, 0.954)` / `(0.194, 0.28, 0.954)` are exactly what `:1241-1242` bind (my instrument reproduced that form: same y/z, commanded x) — **not what `STEPS` commands**; withdrawn as the bar, links unchanged.

**Row 4 (re-pinned)**: rows 2-5 targets = the emitted cell's rest state (the dump's initial state, `mj_forward`, settle 0) evaluated by the driver's own `cable_at` in the `:2812` form. Two independent derivations (appendix F, `pz_r0_targets.py`):
- **(b-1)** the driver's `cable_at` taken from the blob text by AST segment (`:1210-1217`, segment sha256 `da0881e7b1abf365…`) and `exec`'d with `CAB` = the 40 `cab{i}` bodies, on the dump `_gen/_steps_cell_full.xml` (sha256 `4158e4e638e9b0fc0eddad324f2a0fdd8b80a77d51b9526d63d1be3cf4e2204b`, 61,833 bytes, untracked; meshes loaded from their referenced paths with unique asset keys, none substituted): **L = cab27 `(0.1125, 0.28, 0.954)`, R = cab32 `(0.1875, 0.28, 0.954)`** (x to 1.7e-16 of these decimals).
- **(b-2)** closed form from committed constants (`ur15_cell_spec.py` blob `6bdf7ea4f9ca`, `task_config.py` blob `d86380dbe186`): `CABLE_SEG = 0.015`, `CABLE_N = 40` ⇒ `x0 = −0.300`; `c_i = (x0 + (i + ½)·CABLE_SEG, REST_Y = 0.28, REST_TOP + CABLE_R = 0.950 + 0.004)`; nearest link to `GRASP_CENTRE_X ∓ GRIP_HALF_SPAN = 0.150 ∓ 0.044` ⇒ **cab27 `(0.1125, 0.28, 0.954)`, cab32 `(0.1875, 0.28, 0.954)`**.
- **Agreement (b-1) vs (b-2)**: links 27 == 27, 32 == 32; max |Δ| = 1.665e-16 both sides (bar 1e-9). **Equal to §17.7's stated values** to ≤ 1.7e-16. Effective `GRASP_CENTRE_X = C1[0] = 0.150`, `WORK_ROW_DY = 0.0` (both env unset at derivation). The dump's `cab0` origin `(−0.300, 0.28, 0.954)`; link-centre x span `[−0.2925, +0.2925]`.
- **(a) U0** `(0.0986, 0.28, 0.9488)` / `(0.1886, 0.28, 0.951)` (`_gen/dod_c2_20260810/run.log :93`, sha256 `04599b84e34be51e…`) = report-only rows outside the denominator, settle offset (a) − (b) = **L `(−0.0139, 0, −0.0052)`, R `(+0.0011, 0, −0.0030)`** (computed from the two tuples; the harness must print its own).
- Rows 6-18 unchanged (addendum 2).

**Expectation table, rows 2-5 re-solved with the `:2812` targets** (my instrument `pz_r0.py` with a 2-line env override for `GL`/`GR` — `pz_r0_v2.py`, appendix G — on the closure of blob `84a372439c59` @ `96e9ece175` (closure sha256 `a87deb96fde026b3…`, identical to `d2bc133e1320`'s), composed models from `build_side` @ HEAD, `HOME_POSE` start, seed 1, `n_try` 22, `mj_step` calls 0, driver family in `sys.modules` = []):

| step | L target | L conv / solved / pe mm (was) | R target | R conv / solved / pe mm (was) |
|---|---|---|---|---|
| 2 | (0.1125, 0.28, 1.03) | ✓ / 10 / 0.0 (was 11 / 1.2652) | (0.1875, 0.28, 1.03) | ✓ / 13 / 0.0 (unchanged) |
| 3 | (0.1125, 0.28, 0.954) | ✓ / 13 / 0.0 (unchanged) | (0.1875, 0.28, 0.954) | ✓ / 13 / 0.0 (unchanged) |
| 4 | (0.1125, 0.28, 0.954) | ✓ / 13 / 0.0 (unchanged) | (0.1875, 0.28, 0.954) | ✓ / 13 / 0.0 (unchanged) |
| 5 | (0.1125, 0.28, 1.03) | ✓ / 10 / 0.0 (was 11 / 1.2652) | (0.1875, 0.28, 1.03) | ✓ / 13 / 0.0 (unchanged) |

Rows 6-18: conv/solved/pe identical to addendum 3's table on both sides. Totals **L 17/17, R 17/17**; stop-cause tag on every row: none. Still convergence only (Rs1 Q1); the non-discrimination finding of addendum 3 stands (not re-measured here).

**Catch for p0's follow-up (order per §17.7: after this re-pin)**: the follow-up harness `ffa612ea33` `_targets()` `:930-932` binds rows 2-5 to `x = C1[0] ∓ GRIP_HALF_SPAN, y = REST_Y, z = REST_TOP + CABLE_R` = `(0.106, 0.28, 0.954)` / `(0.194, 0.28, 0.954)` = the **`:1241` form** (x off by 6.5 mm per side from the `:2812` form; links unchanged). Under §17.7 the harness must: bind the `:2812` form; derive it by both routes (driver `cable_at` on the dump with its sha printed; closed form from the constants), print both values, the link numbers and the effective `GRASP_CENTRE_X`/`WORK_ROW_DY`, and **STOP with the instrument tag** if the routes disagree by > 1e-9; solve the (a) U0 targets as extra rows tagged 「settled example (U0)」 outside the denominator and print the settle offset (a) − (b) per side (3 components) with the log sha and the `:2814` print line. Rows 6-18 unchanged. My execution (rows 2a, 3, 5-11) waits for that follow-up per §17.7's order; when it lands, the table above is the expectation for rows 2-5.

Supersedes sha `9088954e1e8f70b55925373d953fba7e3492ee3ba94a1d73c72433d6dd4fde74` @ e8a2d6d02a (rows 1-11, 1′, addenda 2-4 stand, with row 4 in this form).

## Appendix F — `pz_r0_targets.py` (verbatim; sha256 caf8fd117fae7f2869f82936126f4b30bd99ba82bbfb919c3555b60ba223439a)
```python
"""pZ row-4 re-pin (v3 §17.7): rows 2-5 targets by two independent routes.
(b-1) the driver's own cable_at rule (blob text, :1210-1216) on the emitted cell dump's initial state (mj_forward, no settle);
(b-2) the closed form from the cell constants: c_i = (x0 + (i+1/2)*CABLE_SEG, REST_Y, REST_TOP + CABLE_R), x0 = -CABLE_SEG*CABLE_N/2.
Both in the :2812 form (x/y/z = link centre).  Nothing stepped; the driver is never imported."""
import sys, re, os, hashlib, ast, numpy as np, mujoco
DUMP, MESHDIR, BLOB, SPECDIR = sys.argv[1:5]
raw = open(DUMP, "rb").read(); print("dump sha256", hashlib.sha256(raw).hexdigest(), "bytes", len(raw))
xml = raw.decode()
# assets: resolve each mesh file to the mesh dir and give every <mesh> element a unique file key
assets = {}; n = [0]
def sub(mo):
    n[0] += 1; ref = mo.group(1); src = ref if os.path.isabs(ref) else os.path.join(MESHDIR, ref)
    assert os.path.exists(src), f"mesh missing on disk: {src}"      # no silent substitution of geometry
    key = f"{n[0]:02d}_{os.path.basename(ref)}"                        # MuJoCo keys assets by basename -> make each unique
    assets[key] = open(src, "rb").read(); return f'file="{key}"'
xml2 = re.sub(r'file="([^"]+)"', sub, xml)
m = mujoco.MjModel.from_xml_string(xml2, assets); d = mujoco.MjData(m)
mujoco.mj_forward(m, d)   # initial state = the emitter's rest placement, settle 0
# constants from the committed spec (imported from its dir; the spec is constants only)
sys.path.insert(0, SPECDIR); import ur15_cell_spec as sp
CABLE_SEG, CABLE_N, REST_Y, REST_TOP, CABLE_R = sp.CABLE_SEG, sp.CABLE_N, sp.REST_Y, sp.REST_TOP, sp.CABLE_R
GRASP_CENTRE_X = float(os.environ.get("GRASP_CENTRE_X", sp.C1[0])); GRIP_HALF_SPAN = sp.GRIP_HALF_SPAN
print("constants:", dict(CABLE_SEG=CABLE_SEG, CABLE_N=CABLE_N, REST_Y=REST_Y, REST_TOP=REST_TOP, CABLE_R=CABLE_R, GRASP_CENTRE_X=GRASP_CENTRE_X, GRIP_HALF_SPAN=GRIP_HALF_SPAN,
      env_GRASP_CENTRE_X=os.environ.get("GRASP_CENTRE_X"), env_WORK_ROW_DY=os.environ.get("WORK_ROW_DY")))
# (b-1): the driver's cable_at, taken from the blob text by AST segment and exec'd with CAB/d/np/CABLE_SEG bound
src = open(BLOB).read(); tree = ast.parse(src)
fn = [s for s in tree.body if isinstance(s, ast.FunctionDef) and s.name == "cable_at"][0]
seg = ast.get_source_segment(src, fn); print("cable_at from blob :%d-%d sha256 %s" % (fn.lineno, fn.end_lineno, hashlib.sha256(seg.encode()).hexdigest()[:16]))
CAB = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"cab{i}") for i in range(CABLE_N)]
assert min(CAB) >= 0, "cab bodies missing"
ns = {"np": np, "d": d, "CAB": CAB, "CABLE_SEG": CABLE_SEG}; exec(seg, ns); cable_at = ns["cable_at"]
gL, iL = cable_at(GRASP_CENTRE_X - GRIP_HALF_SPAN); gR, iR = cable_at(GRASP_CENTRE_X + GRIP_HALF_SPAN)
GL_2812 = (float(gL[0]), float(gL[1]), float(gL[2])); GR_2812 = (float(gR[0]), float(gR[1]), float(gR[2]))
GL_1241 = (float(GRASP_CENTRE_X - GRIP_HALF_SPAN), float(gL[1]), float(gL[2])); GR_1241 = (float(GRASP_CENTRE_X + GRIP_HALF_SPAN), float(gR[1]), float(gR[2]))
print(f"(b-1) driver cable_at on the dump: L=cab{iL} {GL_2812}  R=cab{iR} {GR_2812}   [:2812 form]")
print(f"      the :1241 form (commanded x, y/z from the link): L {GL_1241}  R {GR_1241}")
# (b-2): closed form
x0 = -CABLE_SEG * CABLE_N / 2.0
def closed(x):
    i = int(np.argmin([abs(x0 + (k + 0.5) * CABLE_SEG - x) for k in range(CABLE_N)]))
    return (x0 + (i + 0.5) * CABLE_SEG, REST_Y, REST_TOP + CABLE_R), i
cL, jL = closed(GRASP_CENTRE_X - GRIP_HALF_SPAN); cR, jR = closed(GRASP_CENTRE_X + GRIP_HALF_SPAN)
print(f"(b-2) closed form: x0={x0} L=cab{jL} {cL}  R=cab{jR} {cR}")
dL = max(abs(a - b) for a, b in zip(GL_2812, cL)); dR = max(abs(a - b) for a, b in zip(GR_2812, cR))
print(f"agreement (b-1) vs (b-2): links {iL}=={jL} {iR}=={jR}; max|diff| L={dL:.3e} R={dR:.3e}  (bar 1e-9: {'OK' if max(dL,dR)<=1e-9 and iL==jL and iR==jR else 'STOP'})")
print(f"p11 §17.7 values (0.1125, 0.28, 0.954)/(0.1875, 0.28, 0.954): max|diff| L={max(abs(a-b) for a,b in zip(GL_2812,(0.1125,0.28,0.954))):.3e} R={max(abs(a-b) for a,b in zip(GR_2812,(0.1875,0.28,0.954))):.3e}")
print(f"cab bodies {CABLE_N}; cab0 origin {np.round(d.xpos[CAB[0]],4)}; link-centre x span [{min(float(np.array(d.xpos[b])[0]+CABLE_SEG/2) for b in CAB):.4f}, {max(float(np.array(d.xpos[b])[0]+CABLE_SEG/2) for b in CAB):.4f}]; mj_step calls 0 (never called)")
```

## Appendix G — `pz_r0_v2.py` = appendix C's `pz_r0.py` with one line replaced (verbatim delta; v2 sha256 f22116e367e6ac40dbc9f49468fefb792fc18669b3578ef5dc64475862897096)
```text
- GL, GR = (0.106, 0.28, 0.954), (0.194, 0.28, 0.954); C1, C2 = spec.C1, spec.C2; H = spec.GRIP_HALF_SPAN
+ GL, GR = (0.106, 0.28, 0.954), (0.194, 0.28, 0.954)
+ if os.environ.get("PZ_R0_GLGR"): GL, GR = [tuple(float(v) for v in s.split(",")) for s in os.environ["PZ_R0_GLGR"].split(";")]   # v2: row-4 re-pin (v3 §17.7, :2812 link-centre form) via env; default = the addendum 2 (:1241-form) values
+ C1, C2 = spec.C1, spec.C2; H = spec.GRIP_HALF_SPAN
```
Run: `PZ_R0_GLGR="0.1125,0.28,0.954;0.1875,0.28,0.954" python pz_r0_v2.py <blob 84a372439c59 as text> <git archive of the sim dir> L|R <out.json> own`.
