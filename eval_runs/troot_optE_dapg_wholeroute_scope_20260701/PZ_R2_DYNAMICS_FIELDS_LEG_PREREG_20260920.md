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
