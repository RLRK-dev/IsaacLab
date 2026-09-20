# pZ — pre-registered leg R2 (asset-grade dynamics fields; v3 §10 R2 @ `8d9fdf3bbb` `:140`; p4's adopted order `caa742b8d3` via m-p4-288, R2 in parallel with W/R1), written before the instrument has been run

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 14:42:51 JST on m-p18-426 (p4 m-p4-288 (2): 「R2（新計器: mjModel の field 走査と field ごとの Mx 写像を、負の対照（RC/NH は hand 列で FAIL・意図的に摂動した 1 field で FAIL）つきで事前登録してから測る）」; condition ②: the negative controls must be shown to be able to give a different result). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted**.

**Order of existence (measured in the writing command)**: the instrument's outputs `r2.json` / `r2.log` and its perturbed-asset file do **not** exist (asserted); HEAD `d948b10298`. Every field, map and bar below is fixed here before the first run.

**Objects (blobs at HEAD, each equal to its blob at `792e62e460` — the archive the leg runs in (the gripper acceptance blob is `f1909891539c` = `ad1d80d49f24` + the one `mkdir` line of the accepted follow-up; `build_side` untouched); the stock ko xml and its 8 meshes are read by absolute path from the shared tree, tracked and clean per `PZ_VERDICT_R1P_HAND_ON_ARM_LEG_20260920.md`)**

| file | blob |
|---|---|
| `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` | `cdf284c42eb4` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/_ur15_2f85_koshape_actuated_mirrored.xml` | `4a0ea5a827bd` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_base.xml` | `7334710cc0d6` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_base_mirrored.xml` | `6751866fd3f4` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_gripper_mirror_acceptance.py` | `f1909891539c` |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_cell_spec.py` | `6bdf7ea4f9ca` |

**Models compared** (all built by `ur15_gripper_mirror_acceptance.build_side` from the archive, or compiled alone by `MjModel.from_xml_path`; elements matched **by name** — bodies/joints/actuators/tendons by name, geoms by (body name, ordinal in body), equalities by (type, object-1 name, object-2 name); the `world`/`column` bodies excluded):
- **L** = stock arm + stock ko on the left mount (sign −1) vs **B** = mirrored arm + mirrored ko on the right mount (+1) — the leg;
- negative controls: **NH** = mirrored arm + stock ko (+1); **RC** = stock arm + stock ko (+1); **B′** = B with one hand mass perturbed in a scratch copy of the mirrored ko xml (`mass="0.0125222"` → `"0.0125223"`, first of its two occurrences; the copy is written beside the original so `meshdir` resolves, never into the tracked file);
- single-asset compiles: arm stock vs arm mirrored; hand stock vs hand mirrored.

## Rows (maps and bars from v3 §10 R2 `:140`: 「int/range/exact 列 = 厳密／body_quat ≤ 1e-12／body_iquat ≤ 1e-8（hand）・≤ 1e-10（arm）」; `Mx = diag(−1,1,1)`, `A = diag(−1,1,1)`)

| # | row | field → map → bar (fixed now) |
|---|---|---|
| R2-1 | bodies (L vs B, composed) | `body_mass`, `body_inertia` → equal → **exact**; `body_pos`, `body_ipos` → `Mx·v_L = v_R` → **exact**; `body_quat` → `R_R = Mx·R_L·Mx` (rotation matrices from the quaternions, so `q` and `−q` are the same frame) → **≤ 1e-12**; `body_iquat` → same map → **≤ 1e-8** on the composed model (the hand bound; the arm's own bound 1e-10 is tested in R2-7) |
| R2-2 | joints (by name) | `jnt_type`, `jnt_range`, `jnt_stiffness`, `qpos_spring`, `dof_armature`/`dof_damping` → equal → **exact**; `jnt_axis` → `a_R = −A·a_L` (08-10 B3's measured loader-level map) → **exact**; `jnt_pos` → `Mx` → **exact**. Reported alongside, not a bar: whether `a_R = −a_L` also holds (it coincides with `−A·a` exactly when `a_x = 0`, which is the case for every axis in both assets — expected to hold) |
| R2-3 | geoms (by body + ordinal) | `geom_type`, `geom_size`, `geom_solref`/`geom_solimp` (the pads included), `geom_friction`/`condim`/`contype`/`conaffinity` → **exact**; `geom_pos` → `Mx` → **exact**; `geom_quat` of **non-mesh** geoms → `Mx·R·Mx` → **≤ 1e-12**. **Mesh geom quats are excluded by design**: MuJoCo re-frames each mesh by its principal axes at load and a reflected vertex set earns a different convention (08-10 §3 / the script's `:93-97`); the mesh shapes themselves are R1′'s 192/192 |
| R2-4 | hand actuator (by name: `fingers_actuator`) | `actuator_gainprm`/`biasprm`, `ctrlrange`/`forcerange`/`gear`, `trntype`/`dyntype`/`gaintype`/`biastype` → **exact** |
| R2-5 | tendon (by name: `split`) | `tendon_stiffness`/`damping`/`range` → **exact**; the wrap list (joint names + `wrap_prm` coefficients, in order) → **exact** |
| R2-6 | equalities (by type + object names) | `eq_type`/`eq_active0`, `eq_data`, `eq_solref`/`eq_solimp` → **exact** (p11's column says exact; if `eq_data` fails exactly while an `Mx`-mapped anchor would hold, that is reported as such, not re-graded) |
| R2-7 | single-asset compiles | arm stock vs mirrored: the R2-1..3 fields with `body_iquat ≤ 1e-10`; hand stock vs mirrored: the R2-1..6 fields with `body_iquat ≤ 1e-8`. Expected fine structure: the stock hand xml carries un-normalised inertial quaternions (e.g. `quat="1 0.1664 0 0"`) while the mirrored one carries 8-digit normalised ones — a text-rounding difference at the 1e-9 level is expected inside the 1e-8 bar, and its size is reported |
| R2-8 | **negative controls (p4 condition ②)** | **NH**: hand-body rows (`body_pos`/`body_ipos`/`body_quat` of `g_*` bodies with a non-zero x-component, and the hand `jnt_axis`) must **FAIL**, arm rows must PASS — the stock hand is not the mirror; **RC**: arm rows (`body_pos`/`quat`/`jnt_axis` of `a_*`) must **FAIL**; **B′**: exactly **one** field, `body_mass`, must FAIL on exactly **one** body pair (the perturbed one), every other field unchanged from B's result |
| R2-9 | not measurable here (named, not inherited) | driver-injected parameters — the arm actuators' kp/kv/`forcerange`/`ctrlrange` (driver `:426-433`) and `arm_spec`'s armature/damping (`:238-244`) — are not in these models; they are text-cited equalities by loop construction and are measured only in the #69 run (R4). The `dof_armature`/`damping` compared in R2-2 are the assets' own values |
| R2-10 | control invariance / no run | `mj_step` = 0 (counted); driver family in `sys.modules` = []; model fields only, no `mj_forward` needed; run 0 |

**Expectation (pre-registered)**: on B every bar holds (the mirrored assets were generated by exact arithmetic — 08-10 B3 loader level `pos → A p` exact, `quat → A R A` 6.7e-16; hand mirror `make_ko_mirror.py`); the controls fail where stated. Any B row failing ⇒ asset-level finding ⇒ the asset court (p11 `:149`'s form). A control not failing where stated ⇒ that row cannot discriminate and is downgraded to "measured, not evidence" in the verdict, not silently kept.

## Leg procedure
`3.12.3 3.11.0` on the archive: `python pz_r2.py <archive sim dir> r2.json` once; the verdict embeds the log verbatim and judges each row against the bars above.

## Appendix A — `pz_r2.py` (verbatim; sha256 3f6dab44b655d64bd38d23696fe5aeadaddffa6aa3a92b31cb3e6b1d71ace5f0)
```python
"""pZ R2 instrument (v3 section 10 R2, asset-grade dynamics fields): walk mjModel fields of name-matched elements on the composed models
(build_side of ur15_gripper_mirror_acceptance) L vs {B, NH, RC, B' (one perturbed mass)} and on the single-asset compiles (arm stock vs mirrored,
hand stock vs mirrored).  Maps: exact for scalars/ranges/int fields; Mx = diag(-1,1,1) for positions (exact); Mx.R.Mx for frames (tolerance);
joint axis -> -A.a with A = diag(-1,1,1) (exact; -a also reported).  argv: W(archive sim dir) OUT.json.  No physics: model fields only."""
import sys, io, json, contextlib, numpy as np, mujoco
W, OUT = sys.argv[1], sys.argv[2]; sys.path.insert(0, W)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import ur15_gripper_mirror_acceptance as g
Mx = np.diag([-1.0, 1.0, 1.0]); A = np.diag([-1.0, 1.0, 1.0])
steps = 0; _orig = mujoco.mj_step
def _counted(*a, **k):
    global steps; steps += 1; return _orig(*a, **k)
mujoco.mj_step = _counted
def q2R(q): m = np.zeros(9); mujoco.mju_quat2Mat(m, np.asarray(q, float)); return m.reshape(3, 3)
def name(m, typ, i): return mujoco.mj_id2name(m, typ, int(i))
BODY, JNT, GEOM, ACT, TEN, EQ = (mujoco.mjtObj.mjOBJ_BODY, mujoco.mjtObj.mjOBJ_JOINT, mujoco.mjtObj.mjOBJ_GEOM, mujoco.mjtObj.mjOBJ_ACTUATOR, mujoco.mjtObj.mjOBJ_TENDON, mujoco.mjtObj.mjOBJ_EQUALITY)
def geom_key(m, gi): b = name(m, BODY, m.geom_bodyid[gi]); k = sum(1 for j in range(gi) if m.geom_bodyid[j] == m.geom_bodyid[gi]); return f"{b}#{k}"
def eq_key(m, ei):
    t = int(m.eq_type[ei]); typ = BODY if t in (int(mujoco.mjtEq.mjEQ_CONNECT), int(mujoco.mjtEq.mjEQ_WELD)) else JNT
    return f"{t}:{name(m, typ, m.eq_obj1id[ei])}:{name(m, typ, m.eq_obj2id[ei])}"
def compare(mL, mR, tag, tol_quat=1e-12, tol_iquat=1e-8):
    """returns {field: {n, fail, max, fails[:6]}}; a field FAILs if any pair violates its bar."""
    out = {}
    def rec(field, key, diff, bar, extra=""):
        f = out.setdefault(field, {"n": 0, "fail": 0, "max": 0.0, "bar": bar, "fails": []}); f["n"] += 1; f["max"] = max(f["max"], float(diff))
        if (diff > bar) if bar > 0 else (diff != 0): f["fail"] += 1; f["fails"].append(f"{key}: {diff:.3e}{extra}") if len(f["fails"]) < 6 else None
    def exact(a, b): return float(np.abs(np.asarray(a, float) - np.asarray(b, float)).max()) if np.asarray(a).size else 0.0
    bL = {name(mL, BODY, i): i for i in range(mL.nbody)}; bR = {name(mR, BODY, i): i for i in range(mR.nbody)}
    keys = sorted(set(bL) & set(bR)); out["_bodies"] = {"L": mL.nbody, "R": mR.nbody, "matched": len(keys), "unmatched": sorted((set(bL) ^ set(bR)) - {None})}
    for k in keys:
        i, j = bL[k], bR[k]
        if k in ("world", "column"): continue
        rec("body_mass (exact)", k, exact(mL.body_mass[i], mR.body_mass[j]), 0)
        rec("body_inertia (exact)", k, exact(mL.body_inertia[i], mR.body_inertia[j]), 0)
        rec("body_pos (Mx, exact)", k, exact(Mx @ mL.body_pos[i], mR.body_pos[j]), 0)
        rec("body_ipos (Mx, exact)", k, exact(Mx @ mL.body_ipos[i], mR.body_ipos[j]), 0)
        rec("body_quat (Mx.R.Mx)", k, exact(Mx @ q2R(mL.body_quat[i]) @ Mx, q2R(mR.body_quat[j])), tol_quat)
        rec("body_iquat (Mx.R.Mx)", k, exact(Mx @ q2R(mL.body_iquat[i]) @ Mx, q2R(mR.body_iquat[j])), tol_iquat)
    jL = {name(mL, JNT, i): i for i in range(mL.njnt)}; jR = {name(mR, JNT, i): i for i in range(mR.njnt)}
    jk = sorted(set(jL) & set(jR)); out["_joints"] = {"L": mL.njnt, "R": mR.njnt, "matched": len(jk)}
    for k in jk:
        i, j = jL[k], jR[k]
        rec("jnt_type (exact)", k, exact(mL.jnt_type[i], mR.jnt_type[j]), 0)
        rec("jnt_range (exact)", k, exact(mL.jnt_range[i], mR.jnt_range[j]), 0)
        rec("jnt_axis (-A.a, exact)", k, exact(-A @ mL.jnt_axis[i], mR.jnt_axis[j]), 0)
        rec("jnt_axis (-a, reported)", k, exact(-mL.jnt_axis[i], mR.jnt_axis[j]), 0)
        rec("jnt_pos (Mx, exact)", k, exact(Mx @ mL.jnt_pos[i], mR.jnt_pos[j]), 0)
        rec("jnt_stiffness (exact)", k, exact(mL.jnt_stiffness[i], mR.jnt_stiffness[j]), 0)
        rec("qpos_spring (exact)", k, exact(mL.qpos_spring[mL.jnt_qposadr[i]], mR.qpos_spring[mR.jnt_qposadr[j]]), 0)
        rec("dof_armature/damping (exact)", k, exact([mL.dof_armature[mL.jnt_dofadr[i]], mL.dof_damping[mL.jnt_dofadr[i]]], [mR.dof_armature[mR.jnt_dofadr[j]], mR.dof_damping[mR.jnt_dofadr[j]]]), 0)
    gL = {geom_key(mL, i): i for i in range(mL.ngeom)}; gR = {geom_key(mR, i): i for i in range(mR.ngeom)}
    gk = sorted(set(gL) & set(gR)); out["_geoms"] = {"L": mL.ngeom, "R": mR.ngeom, "matched": len(gk)}
    for k in gk:
        i, j = gL[k], gR[k]
        rec("geom_type (exact)", k, exact(mL.geom_type[i], mR.geom_type[j]), 0)
        rec("geom_size (exact)", k, exact(mL.geom_size[i], mR.geom_size[j]), 0)
        rec("geom_pos (Mx, exact)", k, exact(Mx @ mL.geom_pos[i], mR.geom_pos[j]), 0)
        if mL.geom_type[i] != mujoco.mjtGeom.mjGEOM_MESH: rec("geom_quat non-mesh (Mx.R.Mx)", k, exact(Mx @ q2R(mL.geom_quat[i]) @ Mx, q2R(mR.geom_quat[j])), tol_quat)
        rec("geom_solref/solimp (exact)", k, exact(np.r_[mL.geom_solref[i], mL.geom_solimp[i]], np.r_[mR.geom_solref[j], mR.geom_solimp[j]]), 0)
        rec("geom_friction/condim/contype/conaffinity (exact)", k, exact(np.r_[mL.geom_friction[i], mL.geom_condim[i], mL.geom_contype[i], mL.geom_conaffinity[i]], np.r_[mR.geom_friction[j], mR.geom_condim[j], mR.geom_contype[j], mR.geom_conaffinity[j]]), 0)
    aL = {name(mL, ACT, i): i for i in range(mL.nu)}; aR = {name(mR, ACT, i): i for i in range(mR.nu)}
    ak = sorted(set(aL) & set(aR)); out["_actuators"] = {"L": mL.nu, "R": mR.nu, "matched": len(ak)}
    for k in ak:
        i, j = aL[k], aR[k]
        rec("actuator_gainprm/biasprm (exact)", k, exact(np.r_[mL.actuator_gainprm[i], mL.actuator_biasprm[i]], np.r_[mR.actuator_gainprm[j], mR.actuator_biasprm[j]]), 0)
        rec("actuator_ctrlrange/forcerange/gear (exact)", k, exact(np.r_[mL.actuator_ctrlrange[i], mL.actuator_forcerange[i], mL.actuator_gear[i]], np.r_[mR.actuator_ctrlrange[j], mR.actuator_forcerange[j], mR.actuator_gear[j]]), 0)
        rec("actuator_trntype/dyntype/gaintype/biastype (exact)", k, exact([mL.actuator_trntype[i], mL.actuator_dyntype[i], mL.actuator_gaintype[i], mL.actuator_biastype[i]], [mR.actuator_trntype[j], mR.actuator_dyntype[j], mR.actuator_gaintype[j], mR.actuator_biastype[j]]), 0)
    tL = {name(mL, TEN, i): i for i in range(mL.ntendon)}; tR = {name(mR, TEN, i): i for i in range(mR.ntendon)}
    tk = sorted(set(tL) & set(tR)); out["_tendons"] = {"L": mL.ntendon, "R": mR.ntendon, "matched": len(tk)}
    for k in tk:
        i, j = tL[k], tR[k]
        rec("tendon_stiffness/damping/range (exact)", k, exact(np.r_[mL.tendon_stiffness[i], mL.tendon_damping[i], mL.tendon_range[i]], np.r_[mR.tendon_stiffness[j], mR.tendon_damping[j], mR.tendon_range[j]]), 0)
        wl = [(name(mL, JNT, mL.wrap_objid[w]) if mL.wrap_type[w] == mujoco.mjtWrap.mjWRAP_JOINT else int(mL.wrap_objid[w]), float(mL.wrap_prm[w])) for w in range(mL.tendon_adr[i], mL.tendon_adr[i] + mL.tendon_num[i])]
        wr = [(name(mR, JNT, mR.wrap_objid[w]) if mR.wrap_type[w] == mujoco.mjtWrap.mjWRAP_JOINT else int(mR.wrap_objid[w]), float(mR.wrap_prm[w])) for w in range(mR.tendon_adr[j], mR.tendon_adr[j] + mR.tendon_num[j])]
        rec("tendon wraps (obj names + coef, exact)", k, 0.0 if wl == wr else 1.0, 0, f" L={wl} R={wr}")
    eL = {eq_key(mL, i): i for i in range(mL.neq)}; eR = {eq_key(mR, i): i for i in range(mR.neq)}
    ek = sorted(set(eL) & set(eR)); out["_equalities"] = {"L": mL.neq, "R": mR.neq, "matched": len(ek), "unmatched": sorted(set(eL) ^ set(eR))}
    for k in ek:
        i, j = eL[k], eR[k]
        rec("eq_type/active (exact)", k, exact([mL.eq_type[i], mL.eq_active0[i]], [mR.eq_type[j], mR.eq_active0[j]]), 0)
        rec("eq_data (exact)", k, exact(mL.eq_data[i], mR.eq_data[j]), 0)
        rec("eq_solref/solimp (exact)", k, exact(np.r_[mL.eq_solref[i], mL.eq_solimp[i]], np.r_[mR.eq_solref[j], mR.eq_solimp[j]]), 0)
    out["_summary"] = {"fields": sum(1 for k in out if not k.startswith("_")), "fields_failed": sorted(k for k, v in out.items() if not k.startswith("_") and v["fail"] > 0)}
    return out
with contextlib.redirect_stderr(io.StringIO()):
    L = g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["L"])[0]; B = g.build_side("ur15_base_mirrored.xml", g.KO_MIRROR, g.acc.SIDE_SIGN["R"])[0]
    NH = g.build_side("ur15_base_mirrored.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"])[0]; RC = g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"])[0]
    src = open(g.KO_MIRROR).read(); assert src.count('mass="0.0125222"') == 2
    pert = f"{W}/_pz_r2_perturbed_hand.xml"; open(pert, "w").write(src.replace('mass="0.0125222"', 'mass="0.0125223"', 1))
    BP = g.build_side("ur15_base_mirrored.xml", pert, g.acc.SIDE_SIGN["R"])[0]
    armL, armR = mujoco.MjModel.from_xml_path(f"{W}/ur15_base.xml"), mujoco.MjModel.from_xml_path(f"{W}/ur15_base_mirrored.xml")
    handL, handR = mujoco.MjModel.from_xml_path(g.KO_LEFT), mujoco.MjModel.from_xml_path(g.KO_MIRROR)
res = {"composed_L_vs_B": compare(L, B, "B"), "composed_L_vs_NH (negative: stock hand)": compare(L, NH, "NH"), "composed_L_vs_RC (negative: stock arm on the right mount)": compare(L, RC, "RC"),
       "composed_L_vs_Bperturbed (negative: one hand mass +1e-7)": compare(L, BP, "BP"), "arm_stock_vs_mirrored (single asset)": compare(armL, armR, "arm", tol_iquat=1e-10), "hand_stock_vs_mirrored (single asset)": compare(handL, handR, "hand")}
res["mj_step_calls"] = steps; res["driver_family_in_sys_modules"] = [k for k in sys.modules if "ur15_steps" in k]; res["perturbed_xml"] = pert
open(OUT, "w").write(json.dumps(res, indent=1, default=str))
for cmp_, tab in res.items():
    if not isinstance(tab, dict): continue
    s = tab["_summary"]; print(f"[r2] {cmp_}: bodies matched {tab['_bodies']['matched']} (L {tab['_bodies']['L']} / R {tab['_bodies']['R']}; unmatched {tab['_bodies']['unmatched']}), joints {tab['_joints']['matched']}, geoms {tab['_geoms']['matched']}, actuators {tab['_actuators']['matched']}, tendons {tab['_tendons']['matched']}, eqs {tab['_equalities']['matched']} | fields {s['fields']}, FAILED {len(s['fields_failed'])}: {s['fields_failed']}")
    for k, v in tab.items():
        if k.startswith("_"): continue
        print(f"[r2]    {k:52s} n={v['n']:3d} fail={v['fail']:3d} max={v['max']:.3e} bar={'exact' if v['bar'] == 0 else v['bar']}" + (f"  e.g. {v['fails'][:3]}" if v['fail'] else ""))
print(f"[r2] mj_step calls: {steps}; driver family in sys.modules: {res['driver_family_in_sys_modules']}")
```

## Provenance
Blob ids by `git ls-tree` at HEAD and at `92059373a3`; no instrument output exists at writing (asserted). Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-426.

## Addendum (corrected pre-registration, 2026-09-20 14:59:34 JST) — the bars of rows R2-1b/R2-1d/R2-3/R2-6/R2-7 replaced per p4's disposition (m-p4-300 via m-p18-454) and p11's append-only correction §17.20 @ `7b61c9ae2f`; the same instrument re-run once under this addendum

**This is a bar change made after the object was measured**, and it is written as such: the first run (14:42:53 JST, verdict `PZ_VERDICT_R2_DYNAMICS_FIELDS_LEG_20260920.md` @ `381713ca34`) reported 6 field comparisons as FAIL under the bars above and did not re-grade them; p4 ruled both to be bar defects and adopted this desk's proposal; p11 corrected the source of the bars (§10 R2 `:140`) in §17.20 with the reasons and the discrimination margins. **Order of existence (measured in the writing command)**: §17.20 = `7b61c9ae2f` (14:57:18 JST; blob `b5726481b7c8`, sha256 `7affe9b0cb29d2d2…`, 370 lines, `:357-370`; design commits after it = 0); the re-run's outputs (`r2_rerun.json`/`.log`, `r2_inertia_v2.json`, `r2_judge.txt`) do **not** exist (asserted); HEAD `927c45f9d3`; objects unchanged (the six input blobs equal their blobs at `792e62e460`, re-asserted). The instrument **`pz_r2.py` is byte-identical** (sha256 `3f6dab44b655d64bd38d23696fe5aeadaddffa6aa3a92b31cb3e6b1d71ace5f0` = appendix A) — p4's condition 「計器 sha 不変」; the tensor row and the judgment under the corrected bars are two small additional instruments registered here by sha before the run (p11 §17.20 left their form to this desk).

### Corrected rows (replace the bar column of the rows named; everything else in the table above stands)

| # | row | corrected bar (§17.20) | judged from |
|---|---|---|---|
| R2-1b | `body_pos`, `body_ipos` (Mx) | **≤ 1e-12 m** (was exact) | `pz_r2.py`'s per-field `max` |
| R2-1d | `body_iquat` → **the frame-independent inertia tensor** `Mx·(R_L·diag(I_L)·R_Lᵀ)·Mx = R_R·diag(I_R)·R_Rᵀ` per name-matched body | **≤ 1e-9 kg·m²** (composed and single-asset alike); `body_iquat`'s `Mx·R·Mx` residual **reported only** | `pz_r2_inertia_v2.py` (appendix B below; sha256 `6609eacef7fa3f1a5280326f4bf83860fb836c972c6edf04c5001c96d77aa363`; = the verdict's appendix-C instrument `pz_r2_inertia.py` sha256 `b96f2bc967325e6801b38e73174767261fef6b707595194a80ff83fca8c8e166` extended from L-vs-B to all six comparisons; same formula) |
| R2-3 | `geom_size`, `geom_pos` (Mx) | **≤ 1e-12 m** (was exact); non-mesh `geom_quat` ≤ 1e-12 unchanged; the other geom fields exact unchanged | `pz_r2.py` `max` |
| R2-6 | `eq_data` | **≤ 1e-12** (was exact); `eq_type`/`active`, `eq_solref`/`solimp` exact unchanged | `pz_r2.py` `max` |
| R2-7 | single-asset compiles | the same corrected bars; the arm's `body_iquat ≤ 1e-10` and the hand's `≤ 1e-8` are replaced by the tensor row | as above |
| R2-2 | `jnt_axis` | map made explicit by §17.20: `a_R = −A·a_L`, exact (unchanged); `−a` reported only (unchanged) | `pz_r2.py` |
| R2-8 | controls | unchanged except the withdrawn expectation below; the tensor row carries **no** control requirement (§17.20: hand chirality is carried by `body_ipos`/`body_quat`/`geom_pos` and R1′); NH/RC/B′ tensor values are reported | `pz_r2_judge.py` lists, per comparison, the fields that fail the corrected bars |

**Withdrawn** (recorded in §17.20 too): the R2-8 expectation that the hand `jnt_axis` (−A·a) row fails on NH — every hand axis is `(1, 0, 0)`, for which `−A·a = a`; `body_pos` likewise cannot see the hand (local offsets have `x = 0`).

**Unchanged bars**: `body_mass`, `body_inertia`, `jnt_type`/`range`/`stiffness`/`qpos_spring`/`dof_armature`/`damping`, `jnt_pos`, `geom_type`, `geom_solref`/`solimp`, friction/condim/contype/conaffinity, actuator, tendon, `eq_type`/`active`, `eq_solref`/`solimp` — exact (text constants, no arithmetic; measured 0.0 on the first run).

### Expectation under the corrected bars (fixed before the re-run; the first run's numbers are known and the instrument is deterministic, so this is a prediction only in the formal sense)
- L vs B: **all 28 barred comparisons pass** (27 `pz_r2.py` fields + the tensor row); reported-only: `body_iquat` residual 2.0 on the three sign-flipped bodies, `−a` failing on the 8 hand joints.
- NH: fails `body_ipos` (max ~7.2e-4 m), `body_quat` (`g_base`), `geom_pos` (~7.2e-4 m); tensor row reported (expected to fail on hand bodies — reported, not required); arm rows pass. RC: fails `body_pos` (~1.3 m), `body_ipos`, `jnt_axis (−A·a)` on the 6 arm joints, `geom_pos`, tensor on arm bodies (reported). B′: exactly `body_mass` (1 pair, 1e-7 kg) beyond B's result; tensor unchanged (inertia explicit).
- Single assets: arm and hand pass all corrected bars.

### Leg procedure (re-run)
In the `git archive` of `792e62e460`: `python pz_r2.py <archive> r2_rerun.json` (unchanged instrument), then `python pz_r2_inertia_v2.py <archive> r2_inertia_v2.json`, then `python pz_r2_judge.py r2_rerun.json r2_inertia_v2.json > r2_judge.txt`; each once; the verdict embeds all three outputs verbatim and judges by the judge's lists. Run 0; `mj_step` counted by `pz_r2.py` (must stay 0).

## Appendix B — `pz_r2_inertia_v2.py` (verbatim; sha256 6609eacef7fa3f1a5280326f4bf83860fb836c972c6edf04c5001c96d77aa363)
```python
"""pZ R2 inertia-tensor row (v2 of the supplementary instrument; now on all six comparisons of pz_r2.py): per name-matched body,
I_body = R(iquat) diag(inertia) R(iquat)^T, compared as Mx.I_L.Mx vs I_R (frame-independent); body_iquat residual reported alongside.
Comparisons: composed L vs {B, NH, RC, B'(perturbed hand xml already written by pz_r2.py)}; single assets arm L/R, hand L/R.  argv: W OUT"""
import sys, io, json, contextlib, numpy as np, mujoco
W, OUT = sys.argv[1], sys.argv[2]; sys.path.insert(0, W)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import ur15_gripper_mirror_acceptance as g
    L = g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["L"])[0]; B = g.build_side("ur15_base_mirrored.xml", g.KO_MIRROR, g.acc.SIDE_SIGN["R"])[0]
    NH = g.build_side("ur15_base_mirrored.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"])[0]; RC = g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["R"])[0]
    BP = g.build_side("ur15_base_mirrored.xml", f"{W}/_pz_r2_perturbed_hand.xml", g.acc.SIDE_SIGN["R"])[0]
    armL, armR = mujoco.MjModel.from_xml_path(f"{W}/ur15_base.xml"), mujoco.MjModel.from_xml_path(f"{W}/ur15_base_mirrored.xml")
    handL, handR = mujoco.MjModel.from_xml_path(g.KO_LEFT), mujoco.MjModel.from_xml_path(g.KO_MIRROR)
Mx = np.diag([-1.0, 1.0, 1.0])
def q2R(q): m = np.zeros(9); mujoco.mju_quat2Mat(m, np.asarray(q, float)); return m.reshape(3, 3)
def name(m, i): return mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(i))
def cmp(mL, mR):
    bL = {name(mL, i): i for i in range(mL.nbody)}; bR = {name(mR, i): i for i in range(mR.nbody)}
    out = {"per_body": {}, "iquat_residual": {}, "n": 0, "worst": 0.0, "worst_at": None}
    for k in sorted(set(bL) & set(bR)):
        if k in ("world", "column"): continue
        i, j = bL[k], bR[k]
        IL = q2R(mL.body_iquat[i]) @ np.diag(mL.body_inertia[i]) @ q2R(mL.body_iquat[i]).T; IR = q2R(mR.body_iquat[j]) @ np.diag(mR.body_inertia[j]) @ q2R(mR.body_iquat[j]).T
        d = float(np.abs(Mx @ IL @ Mx - IR).max()); out["per_body"][k] = d; out["n"] += 1
        out["iquat_residual"][k] = float(np.abs(Mx @ q2R(mL.body_iquat[i]) @ Mx - q2R(mR.body_iquat[j])).max())
        if d > out["worst"]: out["worst"], out["worst_at"] = d, k
    return out
res = {"composed_L_vs_B": cmp(L, B), "composed_L_vs_NH": cmp(L, NH), "composed_L_vs_RC": cmp(L, RC), "composed_L_vs_Bperturbed": cmp(L, BP), "arm_stock_vs_mirrored": cmp(armL, armR), "hand_stock_vs_mirrored": cmp(handL, handR)}
open(OUT, "w").write(json.dumps(res, indent=1))
for k, v in res.items():
    nfl = sum(1 for d in v["per_body"].values() if d > 1e-9)
    print(f"[r2-I] {k:26s}: bodies {v['n']:2d}, inertia tensor under Mx worst {v['worst']:.3e} kg m^2 at {v['worst_at']}; bodies > 1e-9: {nfl}; iquat residuals > 1e-8: {sum(1 for r in v['iquat_residual'].values() if r > 1e-8)}")
```

## Appendix C — `pz_r2_judge.py` (verbatim; sha256 20d823d0a4866a993733fd1c4301618ab52e76a12ebc9b7cb4c223fcc470dc2d)
```python
"""pZ R2 judgment layer under the CORRECTED bars (p4 m-p4-300): applies field bars to pz_r2.py's per-field max (r2.json) and to
pz_r2_inertia_v2.py's per-body tensor differences (r2_inertia_v2.json).  Bars: exact (max == 0) for the integer/range/parameter fields;
<= 1e-12 for body_pos, body_ipos, geom_size, geom_pos, eq_data, body_quat, non-mesh geom_quat; jnt_axis (-A.a) exact; inertia tensor <= 1e-9 kg m^2.
Reported only (no bar): body_iquat, jnt_axis (-a).  argv: r2.json r2_inertia_v2.json"""
import json, sys
r = json.load(open(sys.argv[1])); I = json.load(open(sys.argv[2]))
TOL = {"body_pos (Mx, exact)": 1e-12, "body_ipos (Mx, exact)": 1e-12, "geom_size (exact)": 1e-12, "geom_pos (Mx, exact)": 1e-12, "eq_data (exact)": 1e-12, "body_quat (Mx.R.Mx)": 1e-12, "geom_quat non-mesh (Mx.R.Mx)": 1e-12}
REPORT_ONLY = {"body_iquat (Mx.R.Mx)", "jnt_axis (-a, reported)"}
KEYMAP = {"composed_L_vs_B": "composed_L_vs_B", "composed_L_vs_NH (negative: stock hand)": "composed_L_vs_NH", "composed_L_vs_RC (negative: stock arm on the right mount)": "composed_L_vs_RC",
          "composed_L_vs_Bperturbed (negative: one hand mass +1e-7)": "composed_L_vs_Bperturbed", "arm_stock_vs_mirrored (single asset)": "arm_stock_vs_mirrored", "hand_stock_vs_mirrored (single asset)": "hand_stock_vs_mirrored"}
summary = {}
for cmp_, tab in r.items():
    if not isinstance(tab, dict) or cmp_ not in KEYMAP: continue
    barred, passed, failed, reported = 0, 0, [], {}
    for field, v in tab.items():
        if field.startswith("_"): continue
        if field in REPORT_ONLY: reported[field] = (v["fail"], v["max"]); continue
        bar = TOL.get(field, 0.0); ok = (v["max"] <= bar) if bar > 0 else (v["max"] == 0.0); barred += 1; passed += ok
        if not ok: failed.append((field, v["max"], v["fail"], v["n"]))
    it = I[KEYMAP[cmp_]]; ok_I = it["worst"] <= 1e-9; barred += 1; passed += ok_I
    if not ok_I: failed.append(("inertia tensor (Mx, <= 1e-9)", it["worst"], sum(1 for d in it["per_body"].values() if d > 1e-9), it["n"]))
    summary[cmp_] = {"barred": barred, "passed": passed, "failed": failed, "reported": reported, "inertia_worst": it["worst"]}
    print(f"[r2-judge] {cmp_}: {passed}/{barred} barred comparisons pass; failed = {[(f, f'{m:.2e}', nf, n) for f, m, nf, n in failed]}; reported-only = {{k: (nf, f'{mx:.2e}') for k, (nf, mx) in reported.items()}}; inertia tensor worst {it['worst']:.2e}")
print(json.dumps({k: {"passed": v["passed"], "barred": v["barred"], "failed_fields": [f for f, *_ in v["failed"]]} for k, v in summary.items()}))
```

## Appendix D — p11 §17.20 @ `7b61c9ae2f` `:357-370` (verbatim, the source of the corrected bars)
```text
### 17.20 §10 R2（`:140`）の bar 訂正 = append-only（§10 本文は不触）— p4 m-p4-300 → m-p18-454 受領 2026-09-20 14:57:18 JST・kickoff 09-20 08:23 節 item 56 @ `5f3e407487`（当卓が blob で直読）・pZ verdict `PZ_VERDICT_R2_DYNAMICS_FIELDS_LEG_20260920.md` @ `381713ca34`（rows 表 R2-8 = `:24`・処分案 `:29`-`:31`・appendix C `:211`・当卓が blob で実読）・pZ 事前登録 `PZ_R2_DYNAMICS_FIELDS_LEG_PREREG_20260920.md` @ `ad06cff8eb`（写像 `:23`/`:53`・exact の実装 `:70`・`jnt_axis` `:89`・NH 期待 `:34`）
- **何が起きたか**: R2 leg（1 回の run・計器 `pz_r2.py` sha256 `3f6dab44b655d64b…`）は 28 比較中 21 が bar 通過、7 が FAIL のうち 1 は報告行（`−a`）、残る **6 は bar の欠陥**（pZ が再採点せず FAIL のまま報告・p4 同意・当卓同意）。bar の出所は当卓の §10 R2 `:140`（@ `8d9fdf3bbb`・on-disk `:140` と byte 同一を当卓が確認）ゆえ訂正は当卓が理由つきで書く。**object を見た後の bar 変更**である — 以下に理由と判別の余裕を書き、pZ が訂正事前登録の下で同一計器を再走行し、p4 が受け入れる（順序 = p4 の word・item 56）。
- **訂正 1 — 「exact」5 field → `≤ 1e-12 m`**: `body_pos`・`body_ipos`（Mx 写像後）・`geom_size`・`geom_pos`（Mx 写像後）・`eq_data`。composed model と単体 compile（R2-7）の両方に適用。
  - 理由（当卓の読み・帰結は p4 と同じ）: IEEE 754 の符号反転そのものは exact だが、これら 5 field は **compile 時の算術の出力**（mount 姿勢との frame 合成・`fromto`/frame 変換からの size・pos・connect の第 2 anchor の算出）であり、両側で被演算数の順序と符号が異なるため double の最下位桁（1 ulp 級）の残差が原理的に残る。差 0 を要求する bar（事前登録 `:70` = `diff != 0` で FAIL）は物理量を測っていない。実測 = max 2.8e-17 m（`geom_pos` `a_wrist_1_link#0` 2.776e-17／`eq_data` 2.082e-16 は無次元 anchor 成分の 1 ulp／`body_pos` `g_base_mount` 3.109e-18、verdict log）。
  - 判別の余裕: 対照 NH の最小の落ち = **1.7e-8 m**（verdict `:29`）。bar 1e-12 は雑音 2.8e-17 の約 3.6e4 倍上・対照 1.7e-8 の約 1.7e4 倍下 — **判別不変**（同じ bar を `body_quat` が既に持つ）。RC は `body_pos` 最大 1.295 m・B′ は `body_mass` 1 field のみ（1.0e-7 kg）で、いずれも訂正の影響外（verdict `:24`）。
  - 変えないもの: int/range/`body_mass`/`body_inertia`/`jnt_*`/actuator/tendon/`eq_type`/`eq_solref`/`eq_solimp`/`geom_solref`/`geom_solimp`/friction 列は **exact のまま**（text 定数の copy で算術を経ない・実測差 0.0）。
- **訂正 2 — `body_iquat` 行 → frame 非依存の慣性テンソル行**: 各対応 body で `Mx·(R_L·diag(I_L)·R_Lᵀ)·Mx = R_R·diag(I_R)·R_Rᵀ`（`R` = `body_iquat` の回転行列・`diag(I)` = `body_inertia`・`Mx = diag(−1,1,1)` = 事前登録 `:23`）、bar **`≤ 1e-9 kg·m²`**（hand・arm 共通、composed と単体 compile とも）。`body_iquat` の `Mx·R·Mx` 残差は **報告のみ（bar なし）**。旧 bar「`body_iquat` ≤ 1e-8（hand）・≤ 1e-10（arm）」は本行で置換。
  - 理由: MuJoCo は `body_iquat` を慣性テンソルの固有分解で定め、**主軸の符号（= 主軸まわり 180° 回転）は一意でない**（縮退主モーメントでは軸自体も）。よって `Mx·R·Mx` 比較は同一の慣性に対し残差 2.0 を返し得る — 実測 `g_base_mount`・`g_left/right_silicone_pad` の 3 body（verdict R2-1d）。物理量 = テンソル `R·diag(I)·Rᵀ`（body frame）で、その Mx 共役差は同 3 body で **0.0**・全 body max **1.0e-10 kg·m²**（verdict appendix C `:211`、事前登録外の補助測定 `pz_r2_inertia.py` sha256 `b96f2bc967325e68…`）。bar 1e-9 = 実測 max の 10 倍・pZ 処分案 `:30` の値・p4 の word。
  - 対照: 本行に「NH で落ちる」を要求しない — hand の chirality は `body_ipos`（NH 最大 7.21e-4 m）・`body_quat`・`geom_pos` 行と R1′ が担う（verdict `:24`）。本行の NH/RC/B′ 値は報告。
  - pZ への注記（質問であって finding でない）: 本行の計器は appendix C の補助測定に相当し、`pz_r2.py`（sha 不変）の外にある。p4 の条件「計器 sha 不変」の下で本行をどう事前登録するか（appendix C 計器を sha で登録・`pz_r2.py` の log から `max` を新 bar で判定）は pZ の裁量。当卓は要件（上式・max・bar）のみ書く。
- **`jnt_axis` の写像を明記**（§10 は map を書いていなかった）: `a_R = −A·a_L`、`A = diag(−1,1,1)`（事前登録 `:23`/`:89`・08-10 B3 の loader-level 写像）、exact のまま（実測 14/14 差 0.0）。`−a` は報告行（arm 6 で成立・hand 8 で不成立 = hand の axis が全て (1,0,0)）。
- **撤回の記録**: pZ 事前登録 R2-8（`:34`）の期待「NH で hand `jnt_axis`（−A·a）行が落ちる」は verdict R2-8（`:24`）で反証 — hand の全 axis = (1,0,0) ゆえ `−A·a = a` で行は chirality を見ない（`body_pos` も hand の local offset x = 0 で同様）。撤回 = pZ（verdict `:31`）、当卓も同じ読み。§10 R2 の bar は本件で変わらない。
- **R2-9（driver 注入 parameter）**: p4 が driver blob `:238-244`（armature/damping）・`:426-433`（kp/kv/`forcerange`/`ctrlrange`）を読み text 上の両側同一を確認、静的 leg 不要・実効値は R4（p4 の word・item 56）。§10 R2 の記載「計器の model に無い・実測は #69 run のみ」と整合、訂正なし。
- **鎖の状態**: R2 = 本訂正 → pZ 訂正事前登録 → 同一計器の再走行 → verdict → p4 受入（28/28 ＋ 対照 3 種が落ちる所で落ちる）。§7.2 前提の残り = R2・p6 の state.md 反映。⛔ 解錠なし（route run (2)・#69・D4′・WIP）・run 0・当卓は run しない。
```

## Addendum 2 (2026-09-20 15:05:51 JST) — the judgment layer registered at its corrected sha (p4 m-p4-302 via m-p18-460: 「v2 sha を事前登録に追記 → 判定層のみ再走行 → verdict に追記」; the form p0's v8→v9 took)

**What changed and why**: the addendum above registered `pz_r2_judge.py` at sha256 `20d823d0a4866a993733fd1c4301618ab52e76a12ebc9b7cb4c223fcc470dc2d` (v1). On the re-run v1 stopped at its print line — `NameError: name 'mx' is not defined. Did you mean: 'm'?` — before printing any judgment (the crash is in the formatting of the output; the bars, the field list and the counting were not reached). It was corrected in place to sha256 **`2b8b78e43752fc620aa7251348741f87ca9337db1c7beb4012a6ed8782cdc6dc`** (v2) by rewriting that one print statement; the `diff` is appendix C of `PZ_VERDICT_R2_DYNAMICS_FIELDS_LEG_CORRECTED_BARS_20260920.md` @ `735934bef8` (two lines; no bar, field, tolerance or count touched), which p4 read and confirmed (item 63). **This addendum registers v2 by sha before the judgment layer is run again.** `pz_r2.py` (sha256 `3f6dab44b655d64b…`) and `pz_r2_inertia_v2.py` (sha256 `6609eacef7fa3f1a…`) are not re-run: their outputs (`r2_rerun.json`, `r2_inertia_v2.json`) are the inputs and are unchanged.

**Order of existence (measured in the writing command)**: `r2_judge_rerun.txt` does not exist (asserted); the pre-registration and the verdict are clean in the shared tree; HEAD `4df3610121`.

**Expectation (fixed now)**: the re-run's output is **byte-identical** to the verdict's appendix A (`r2_judge.txt`, sha256 `54ef029392451c037019e424a973ce85e3f8cba249b18243cb50b2492f2ff777`): L vs B 27/27; NH 23/27 failing `body_ipos`/`body_quat`/`geom_pos`/tensor; RC 21/27 failing `body_pos`/`body_ipos`/`body_quat`/`jnt_axis (−A·a)`/`geom_pos`/tensor; B′ 26/27 failing `body_mass` only; arm 18/18; hand 27/27. Any differing line ⇒ return (p4's word).

**Leg procedure**: `python pz_r2_judge.py r2_rerun.json r2_inertia_v2.json > r2_judge_rerun.txt` once; `cmp` against `r2_judge.txt`; the result appended to the verdict.
