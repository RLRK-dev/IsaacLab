# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""SRG probe (Stage-B, node T-ROOT-optE-route-dapg-C1C2-P2-routeexec) — the grip-efficacy
go/no-go that resolves the 4-substep grip UNKNOWN BEFORE committing comp3/4/5 (CC6 "build on sand").

DESIGN = SRG_PROBE_DESIGN_DRAFT_COORD_20260707.md (%12 [VERIFY] PASS 19:06) + BUILD_SPEC
option B (%12 RULED B, self-contained current-koshape CPU pinch; SRG_S0_BUILD_SPEC_B_COORD_20260707.md).
Staged, early-exit, cheapest-first; NOT "no-slip" (banked-UNREACHABLE, LL-G3-Vacuity) — creep-BUDGETED,
PER-AXIS.

  S0  4-substep AXIAL creep-floor re-measure on the CURRENT koshape (コ) gripper (isolated pinch, R6
      production solref) + CLEAN same-gripper K regime-screen.
      Build = the PROVEN current-koshape close-on-cable path (r_s66_wr_longhold: build_scene(
      grasp_actuation=True) + SolverMuJoCo + _wire_s6_grasp_solref + gripper_dynamic + SEED arms +
      ik HOVER/descend cradle + servo close), swapped to CPU (use_mujoco_cpu=True, NEWTON_DEVICE=cpu,
      single world). Measure = the s5 corrected instrument (com_y axial-creep polyfit + per-substep
      body_f readback assert + rule-2 free-body landing true-positive), ported asset-agnostic onto the
      koshape env.
      ⭐ %12 REFINEMENT (20:16): measure BOTH koshape 4-substep AND koshape 10-substep (both CPU, same
      gripper) → the K-screen = koshape4/koshape10 (CLEAN substep-transfer, same gripper). The V-groove
      60.4µm/f 10-substep bank is a CROSS-REFERENCE only (differs by GRIPPER too), NOT the K reference.
  S1  DIRECT z/lateral cage-escape go/no-go on the REAL route grasp (creep-budgeted over W_svc).  [HELD]
  S2  tail-cell screening (nominal + DR-corner +-16mm + known-hard; gate = worst-screened).         [HELD]

⛔ S0 is CPU-only (no GPU). S1/S2 are cuda:0 (route device-fragile) and HELD for Rs GPU auth.
grasp_actuation=ON is exercised in a STANDALONE probe (build_scene, temporary); the locked file
(_run_mujoco_grasp_route) and production config are NOT edited (D2).

Ground: SRG design draft §5/§12-14 (%12 [VERIFY] PASS) / BUILD_SPEC option B / LAYERB verdict CC3
(creep-budgeted) / LL-Creep-Characterization / LL-G3-Vacuity / task_config.py (contact SSOT).
Run (0-GPU CPU env_isaaclab7):
  CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python -u srg_probe.py --stage s0
"""

import argparse
import json
import os
import sys
import time

# CPU pin BEFORE any newton import (S0 = no-GPU; FK model + solver read NEWTON_DEVICE at build).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("NEWTON_DEVICE", "cpu")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = "/home/rlrk/IsaacLab/thread_isaac_lab"
for _p in (OUT_DIR, os.path.join(_ROOT, "envs"), os.path.join(_ROOT, "scripts"),
           os.path.join(_ROOT, "configs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# --- Cross-reference bank (V-groove 10-substep, R6, F=0) ------------------------------------------
# ⚠ CROSS-REFERENCE ONLY — this bank is the OLD V-groove gripper (s5_calib_bench3r, 2026-06-10, PRE the
# koshape swap 85315bbec6 2026-06-23). The koshape floors below differ by GRIPPER too, so the transfer
# factor vs this bank mixes substep AND gripper. The CLEAN substep screen is koshape4/koshape10 (%12).
BANK_VGROOVE_10SUB_R6_UM_PER_F = 60.4  # LL-Creep-Characterization.md:11 (R6 60.4 um/f @F=0, 10-substep)

# K regime-change screen (design §13 D4): granularity-coarsening ALONE scales creep by <= the substep
# ratio SIM_SUBSTEPS/RL_SIM_SUBSTEPS = 10/4 = 2.5x; K = 2.5x + margin => 3.5x. koshape4/koshape10 > K =>
# a NEW mechanism appeared at 4-substep (not mere coarsening) => STOP+surface (NOT a task budget).
SUBSTEP_RATIO = 10.0 / 4.0  # 2.5
K_REGIME_SCREEN = 3.5

# Landing-control band (rule-2 free-body true-positive; s5_calib_bench3r.py:50, authored around 24.6mm@1N/30f).
LANDING_BAND_MM = (10.0, 60.0)

# Grasp choreography (the PROVEN 6/21 WORKING koshape recipe; r_s66_wr_longhold_gpucg_task2a.py:62-77).
SEED_L = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]
SEED_R = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]
CLOSE_STEPS = 130     # servo-close settle frames (r_s66:62)
HOLD_FRAMES = 360     # post-close hold for the creep measure
GRACE_FRAMES = 60     # skip the close/force transient before the com_y polyfit (post-grace hold)
NJMAX_SOLVER = 8192   # r_s66:61 (contact-rich grasp headroom; > MUJOCO_NCONMAX)


def _live_production_contact_ssot():
    """Live task_config production contact SSOT (the values S0's env MUST share — D1 caveat a)."""
    import task_config as C

    return {
        "pad_solref": tuple(float(v) for v in C.MUJOCO_PAD_SOLREF),  # :187 R6-bx4
        "condim": int(C.MUJOCO_CONTACT_CONDIM),                      # :176 = 6
        "impratio": float(C.MUJOCO_OPT_IMPRATIO),                    # :196 = 10.0
    }


def _frame_comparability():
    """(b) frame-comparability HARD gate: N*substep_dt == DT in BOTH regimes (else um/f is not
    comparable 4-vs-10). Pure-constant check (design §3 / §12 Step 3); fail-closed."""
    from newton_skill_env_base import DT, RL_SIM_DT, RL_SIM_SUBSTEPS, SIM_DT, SIM_SUBSTEPS

    frame_10 = SIM_SUBSTEPS * SIM_DT
    frame_4 = RL_SIM_SUBSTEPS * RL_SIM_DT
    assert abs(frame_10 - DT) < 1e-12, f"10-substep frame {frame_10} != DT {DT}"
    assert abs(frame_4 - DT) < 1e-12, f"4-substep frame {frame_4} != DT {DT} (frame-comparability BROKEN)"
    return {"DT": float(DT), "frame_dt_10sub": float(frame_10), "frame_dt_4sub": float(frame_4),
            "SIM_SUBSTEPS": int(SIM_SUBSTEPS), "RL_SIM_SUBSTEPS": int(RL_SIM_SUBSTEPS)}


def _pad_box_geoms(m):
    """Pad COLLISION box geoms on the mj_model, located BY NAME (design §6; _wire_s6_grasp_solref:1379-83
    same filter). koshape names every pad geom '*_pad1/2/_f1ext/_f2ext' => 'pad' substring (2f85_koshape.xml
    comment :112). Narrow to BOX to drop the visual pad meshes."""
    import mujoco

    box = int(mujoco.mjtGeom.mjGEOM_BOX)
    out = []
    for g in range(int(m.ngeom)):
        gname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bid = int(m.geom_bodyid[g])
        bname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, bid) or "").lower()
        if "pad" in (gname + bname) and int(m.geom_type[g]) == box:
            out.append(g)
    return out


def _badqacc(solver):
    import mujoco

    try:
        return int(solver.mj_data.warning[mujoco.mjtWarning.mjWARN_BADQACC].number)
    except Exception:
        return -1


def _ncon(solver):
    try:
        return int(solver.mj_data.ncon)
    except Exception:
        return -1


def build_koshape_pinch(tag):
    """Self-contained CURRENT-koshape CPU pinch env (BUILD_SPEC option B). Mirrors the PROVEN
    close-on-cable path r_s66_wr_longhold_gpucg_task2a.build_and_grasp, swapped to CPU:
    build_scene(grasp_actuation=True) + SolverMuJoCo(use_mujoco_cpu=True) + _wire_s6_grasp_solref
    (R6 pad-solref + condim/priority readback asserts, by-NAME) + gripper_dynamic + servo drivers.
    Returns an env dict; the arm is posed at the SEED_L/SEED_R down-wrist grasp seed."""
    import newton
    import newton_skill_env_base as B
    import test_newton_clip_routing as T
    from newton.solvers import SolverMuJoCo
    from newton_skill_env_base import MUJOCO_NCONMAX

    # relocation patch: _wire_s6_grasp_solref moved test->base (r_s66:56 precedent).
    T._wire_s6_grasp_solref = B._wire_s6_grasp_solref

    fk_model = T.build_fk_model()  # reads NEWTON_DEVICE=cpu
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:T.ARM_DOF] = SEED_L
    fk_jq[T.JOINTS_PER_ARM:T.JOINTS_PER_ARM + T.ARM_DOF] = SEED_R
    for j in T.GRIPPER_JOINT_RANGE:  # both grippers start neutral/open
        fk_jq[j] = 0.0
        fk_jq[T.JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    scene_info = T.build_scene(use_cable=True, fk_model=fk_model, fk_state=fk_state,
                               solver_backend="mujoco", grasp_actuation=True)
    model = scene_info["model"]
    scene_info["fk_model"] = fk_model
    scene_info["fk_state"] = fk_state
    scene_info["vbd_control"] = model.control()
    model.rigid_contact_max = T.NJMAX
    contacts = model.contacts()
    cable_bodies = scene_info.get("cable_bodies", [])

    # CPU SolverMuJoCo (use_mujoco_cpu=True; single world => separate_worlds False).
    solver = SolverMuJoCo(model, use_mujoco_cpu=True, separate_worlds=(model.world_count > 1),
                          update_data_interval=1, disable_contacts=False, nconmax=MUJOCO_NCONMAX,
                          njmax=NJMAX_SOLVER, solver="newton", integrator="implicitfast")
    # R6 pad-solref poke + I11 readback asserts (condim==6/priority==1/roll; by-NAME pad filter). On CPU
    # mjw is absent -> the mjw asserts are skipped, mj_model (the CPU step-read array) is poked+asserted.
    wire_rb = T._wire_s6_grasp_solref(solver, scene_info)

    control = scene_info["vbd_control"]
    drivers = scene_info["driver_joints"]
    scene_info["gripper_dynamic"] = True  # CRITICAL: leave gripper coords DYNAMIC (servo-driven close)
    T._set_gripper_target(control, drivers, T.GRIPPER_DRIVER_OPEN_RAD)

    return {"model": model, "solver": solver, "control": control, "contacts": contacts,
            "scene_info": scene_info, "fk_state": fk_state, "cable_bodies": cable_bodies,
            "drivers": drivers, "wire_rb": wire_rb, "tag": tag, "T": T}


def d1_contact_readback(env, ssot):
    """D1 SSOT fail-closed gate (design §12): the built koshape env's ACTUAL mj_model contact params
    (pad solref/condim + opt impratio) EXACTLY share the live production SSOT. Raises (fail-closed) on
    any divergence -> the S0 floor would not be representative. Returns the readback dict."""
    m = env["solver"].mj_model
    pad_box = _pad_box_geoms(m)
    assert pad_box, "D1: no pad BOX geoms located on the koshape mj_model"
    g = pad_box[0]
    pad_solref = tuple(float(v) for v in m.geom_solref[g][:2])
    pad_condim = int(m.geom_condim[g])
    impratio = float(m.opt.impratio)
    readback = {"n_pad_box_geoms": len(pad_box), "pad_solref": pad_solref,
                "pad_condim": pad_condim, "impratio": impratio}
    assert pad_solref == ssot["pad_solref"], f"D1: pad_solref {pad_solref} != live {ssot['pad_solref']}"
    assert pad_condim == ssot["condim"], f"D1: pad condim {pad_condim} != live {ssot['condim']}"
    assert impratio == ssot["impratio"], f"D1: impratio {impratio} != live {ssot['impratio']}"
    return readback


def landing_control(N_substeps):
    """Rule-2 free-body landing true-positive (fail-closed): scratch cable + table, 1N/30f axial push,
    dy must land in LANDING_BAND_MM. Reimplemented asset-agnostic from s5_calib_bench3r.landing_control
    (no gripper -> gripper-swap invariant), run at N substeps (frame=DT)."""
    import mujoco
    import newton
    import newton_skill_env_base as B
    import numpy as np
    import task_config as C
    import test_newton_clip_routing as T
    import warp as wp
    from newton_skill_env_base import DT

    sim_dt = DT / N_substeps
    builder = newton.ModelBuilder(gravity=T.GRAVITY)
    tc = newton.ModelBuilder.ShapeConfig()
    tc.ke, tc.kd, tc.mu, tc.gap = C.MUJOCO_CONTACT_KE, C.MUJOCO_CONTACT_KD, 1.0, 0.002
    builder.add_shape_box(body=-1, hx=0.35, hy=0.35, hz=0.005,
                          xform=wp.transform((0.3, -0.05, C.TABLE_HEIGHT - 0.005), wp.quat_identity()),
                          cfg=tc)
    cb, _cj, _sr = T.add_revolute_cable(
        builder, start_pos=(0.3, -0.15, C.TABLE_HEIGHT + C.CABLE_RADIUS), direction=(0, 1, 0))
    builder.color()
    model = builder.finalize(device="cpu", requires_grad=False)
    solver = B.make_solver(model, backend="mujoco", use_mujoco_cpu=True, enable_cable_contacts=True)
    solver.mj_model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_AUTORESET)
    s0, s1 = model.state(), model.state()
    newton.eval_fk(model, s0.joint_q, s0.joint_qd, s0)
    ctrl = model.control()
    for _ in range(100):  # settle
        for _ in range(N_substeps):
            s0.clear_forces()
            solver.step(s0, s1, ctrl, None, sim_dt)
            s0, s1 = s1, s0
    per = 1.0 / len(cb)
    cbi = np.array(cb)
    y0 = float(s0.body_q.numpy()[cbi, 1].mean())
    for _f in range(30):  # 1N total axial push over 30 frames
        for _ in range(N_substeps):
            s0.clear_forces()
            bf = s0.body_f.numpy()
            bf[cbi, 1] += per
            s0.body_f.assign(bf)
            solver.step(s0, s1, ctrl, None, sim_dt)
            s0, s1 = s1, s0
    dy = (float(s0.body_q.numpy()[cbi, 1].mean()) - y0) * 1000
    ok = LANDING_BAND_MM[0] <= abs(dy) <= LANDING_BAND_MM[1]
    print(f"  [LANDING N={N_substeps}] free-body 1N/30f: dy={dy:+.2f}mm band={LANDING_BAND_MM} -> "
          f"{'PASS' if ok else 'FAIL (fail-closed: cell will NOT run)'}")
    return {"ok": bool(ok), "dy_mm": round(float(dy), 2), "N_substeps": N_substeps}


def grasp_cable(env):
    """Establish the koshape grasp on the cable via the PROVEN r_s66 choreography: ik HOVER (Z_GRASP+0.10)
    -> 8-step descend to the -4mm cradle Z_GRASP -> servo CLOSE + settle. Returns (state, engaged, ncon)."""
    import numpy as np
    import task_config as C

    T = env["T"]
    model, solver, contacts = env["model"], env["solver"], env["contacts"]
    scene_info, control, drivers = env["scene_info"], env["control"], env["drivers"]

    gx = C.GRASP_X
    yl, yr = C.WIDE_LEFT_Y, C.WIDE_RIGHT_Y
    z_engage = C.TABLE_HEIGHT + C.CABLE_RADIUS + C.EE_TO_PINCH_CLOSED  # ZE (the -4mm cradle sweet spot)
    z_grasp = z_engage + 0.008                                        # r_s66:74 z_grasp
    z_high = z_grasp + 0.10

    def tgt(z):
        return (gx, yl, z), (gx, yr, z)

    state = model.state()
    for _ in range(10):  # brief settle at the seed pose (kinematic arm from FK)
        state = T.physics_step(model, state, solver, contacts, scene_info)

    state, _ = T.ik_move_both(model, state, scene_info, solver, contacts, *tgt(z_high),
                              label="HOVER", converge_mm=8.0, speed_factor=0.2)
    ws = env["fk_state"].joint_q.numpy().copy()
    for k in range(1, 9):  # 8-step straight descend to the cradle depth
        z = z_high + (z_grasp - z_high) * k / 8
        state, _ = T.ik_move_both(model, state, scene_info, solver, contacts, *tgt(z),
                                  label=f"DZ{k}", converge_mm=2.5, speed_factor=0.25, warmstart_jq=ws)
        ws = env["fk_state"].joint_q.numpy().copy()

    T._set_gripper_target(control, drivers, T.GRIPPER_DRIVER_CLOSE_RAD)  # full clamp
    ncon_max = 0
    for _ in range(CLOSE_STEPS):
        state = T.physics_step(model, state, solver, contacts, scene_info)
        ncon_max = max(ncon_max, _ncon(solver))
    bqn = state.body_q.numpy()
    finite = bool(np.all(np.isfinite(bqn)))
    engaged = bool(_ncon(solver) > 0 and finite)
    print(f"  [GRASP {env['tag']}] z_grasp={z_grasp:.4f} ncon_close={_ncon(solver)} "
          f"ncon_max={ncon_max} finite={finite} engaged={engaged}")
    return state, engaged, ncon_max


def measure_axial_creep(env, state, N_substeps, F_axial):
    """s5-method AXIAL creep on the held koshape grasp: kinematic-arm hold (T._ARM_OVERWRITE_IDX,
    gripper DYNAMIC) with per-substep axial body_f (F on the cable, +y) injected AFTER clear_forces +
    a readback assert (rule-2 (b)); track com_y; creep = |polyfit slope| over the post-grace hold * 1e6.
    Mirrors s5_calib_bench3r.pinch_axial_cell:158-248 (asset-agnostic), grafted onto the koshape env."""
    import numpy as np

    T = env["T"]
    model, solver, control = env["model"], env["solver"], env["control"]
    fk_state = env["fk_state"]
    from newton_skill_env_base import DT

    sim_dt = DT / N_substeps
    aow = list(T._ARM_OVERWRITE_IDX)  # {0-5,14-19}: overwrite arm coords, leave gripper {6-13,20-27} dynamic
    cidx = np.array(env["cable_bodies"])
    per = (F_axial / len(cidx)) if F_axial else 0.0

    s1 = model.state()
    bq0 = _badqacc(solver)
    landing_ok = True
    com_y, N_series = [], []

    def hold_step(apply):
        nonlocal state, s1, landing_ok
        fkq = fk_state.joint_q.numpy()
        s0 = state
        s1_ = s1
        for _ in range(N_substeps):
            jq = s0.joint_q.numpy()
            jqd = s0.joint_qd.numpy()
            jq[aow] = fkq[aow]  # kinematic arm hold (gripper coords untouched = servo-dynamic)
            jqd[aow] = 0.0
            s0.joint_q.assign(jq)
            s0.joint_qd.assign(jqd)
            s0.clear_forces()
            if apply and per:
                bf = s0.body_f.numpy()
                bf[cidx, 1] += per
                s0.body_f.assign(bf)
                if abs(float(s0.body_f.numpy()[cidx[0]][1]) - per) > 1e-9:
                    landing_ok = False  # rule-2 (b): per-substep body_f readback assert
            solver.step(s0, s1_, control, None, sim_dt)
            s0, s1_ = s1_, s0
        state, s1 = s0, s1_

    for f in range(HOLD_FRAMES):
        hold_step(apply=True)  # force applied throughout the hold (F=0 => intrinsic floor)
        bqn = state.body_q.numpy()
        if not np.all(np.isfinite(bqn)):
            return {"abort": f"NaN at hold f{f}", "F_axial_N": F_axial, "N_substeps": N_substeps,
                    "badqacc": _badqacc(solver) - bq0, "finite": False}
        com_y.append(float(bqn[cidx][:, 1].mean()))
        N_series.append(_ncon(solver))

    comy = np.array(com_y[GRACE_FRAMES:])
    creep = abs(float(np.polyfit(np.arange(len(comy)), comy, 1)[0])) * 1e6  # um/f
    n_hold = np.array(N_series[GRACE_FRAMES:])
    bad = _badqacc(solver) - bq0
    row = {"F_axial_N": F_axial, "N_substeps": N_substeps,
           "creep_um_per_f": round(creep, 2),
           "com_y_total_mm": round((comy[-1] - comy[0]) * 1000, 3),
           "ncon_mean": round(float(n_hold.mean()), 1),
           "collapse": int(np.sum(n_hold < 1)),  # frames with no pad-cable contact
           "badqacc": bad, "landing_readback_ok": bool(landing_ok), "finite": True}
    print(f"  [CREEP {env['tag']}] creep={row['creep_um_per_f']}um/f com_dy={row['com_y_total_mm']}mm "
          f"ncon={row['ncon_mean']} collapse={row['collapse']} badqacc={bad} land_rb={landing_ok}")
    return row


def _run_cell(tag, N_substeps, F_axial, ssot):
    """One measurement cell: build fresh koshape env -> D1 gate -> grasp -> axial-creep hold."""
    import test_newton_clip_routing as T
    import warp as wp

    # Set the substep regime FIRST (physics_step + ik_move_both + hold read T.SIM_SUBSTEPS/SIM_DT).
    from newton_skill_env_base import DT

    orig = (T.SIM_SUBSTEPS, T.SIM_DT)
    T.SIM_SUBSTEPS, T.SIM_DT = N_substeps, DT / N_substeps
    try:
        wp.init()
        env = build_koshape_pinch(tag)
        d1 = d1_contact_readback(env, ssot)  # fail-closed
        state, engaged, ncon_max = grasp_cable(env)
        if not engaged:
            return {"tag": tag, "F_axial_N": F_axial, "N_substeps": N_substeps, "engaged": False,
                    "ncon_max": ncon_max, "d1_readback": d1,
                    "note": "grasp did NOT engage the cable (ncon==0 or NaN) -> floor unmeasurable, surface"}
        row = measure_axial_creep(env, state, N_substeps, F_axial)
        row.update({"tag": tag, "engaged": True, "ncon_max_close": ncon_max, "d1_readback": d1})
        return row
    finally:
        T.SIM_SUBSTEPS, T.SIM_DT = orig


def run_s0():
    """S0: CURRENT-koshape 4-substep AXIAL creep-floor re-measure + CLEAN same-gripper K regime-screen.

    Cells: koshape x {N in (4,10)} x {F in (0.0, 0.44N)}. K-screen = koshape4_F0 / koshape10_F0 (CLEAN,
    same gripper — %12 refinement). The V-groove 60.4 bank is a CROSS-REF only. Landing rule-2 fail-closed
    per N. STOP+surface on K>K_REGIME_SCREEN / qualitative breakdown / not-engaged / creep None."""
    ssot = _live_production_contact_ssot()
    framecomp = _frame_comparability()  # (b) HARD gate

    landing = {}
    cells = {}
    for N in (4, 10):
        landing[f"N{N}"] = landing_control(N)
        if not landing[f"N{N}"]["ok"]:
            continue  # fail-closed: cells at this N not run
        for F in (0.0, 0.44):  # floor + service-load pair (design §5 R6 x {F=0, F=0.44})
            key = f"koshape_N{N}_F{str(F).replace('.', '')}"
            cells[key] = _run_cell(key, N, F, ssot)

    floor4 = cells.get("koshape_N4_F00", {})
    floor10 = cells.get("koshape_N10_F00", {})
    creep4 = floor4.get("creep_um_per_f") if floor4.get("engaged") else None
    creep10 = floor10.get("creep_um_per_f") if floor10.get("engaged") else None

    k_clean = (creep4 / creep10) if (creep4 and creep10) else None
    vgroove_xref = (creep4 / BANK_VGROOVE_10SUB_R6_UM_PER_F) if creep4 else None

    # breakdown = any engaged cell with a qualitative failure (abort/collapse/badqacc/NaN).
    breakdown = False
    for c in cells.values():
        if c.get("abort") or c.get("collapse", 0) > 0 or c.get("badqacc", 0) > 0:
            breakdown = True
    not_engaged = any(c.get("engaged") is False for c in cells.values())
    regime_change = (k_clean is not None and k_clean > K_REGIME_SCREEN)

    if creep4 is None or creep10 is None or not_engaged or breakdown or regime_change:
        verdict = "STOP_SURFACE"
    else:
        verdict = "PROCEED_TO_S1"

    return {
        "stage": "S0",
        "substrate": "current koshape (コ) single-claw 2f85_koshape.xml (16-pad, by-NAME); CPU, isolated pinch",
        "d1_contact_ssot": ssot,
        "frame_comparability": framecomp,
        "landing_control": landing,
        "cells": cells,
        "koshape_4sub_floor_um_per_f": creep4,
        "koshape_10sub_floor_um_per_f": creep10,
        "k_screen_clean_koshape4_over_koshape10": round(k_clean, 3) if k_clean else None,
        "k_regime_screen": K_REGIME_SCREEN,
        "substep_ratio": SUBSTEP_RATIO,
        "vgroove_10sub_bank_um_per_f": BANK_VGROOVE_10SUB_R6_UM_PER_F,
        "vgroove_xref_factor_koshape4_over_vgroove10": round(vgroove_xref, 3) if vgroove_xref else None,
        "vgroove_xref_caveat": "CROSS-REF ONLY: differs by GRIPPER (V-groove vs koshape) AND substep; "
                               "the CLEAN substep screen is koshape4/koshape10",
        "qualitative_breakdown": breakdown,
        "not_engaged": not_engaged,
        "regime_change_vs_K": regime_change,
        "s0_verdict": verdict,
    }


def run_s1():
    """S1: DIRECT z/lateral cage-escape go/no-go on the REAL route grasp (creep-budgeted over W_svc).

    [BUILD PENDING — HELD]. Spec (design §5/§13, %12-VERIFIED): grasp_actuation=ON 4-substep servo-close at
    nominal C1 in the REAL route geometry (cuda:0-only, route device-fragile); hold over W_svc; measure
    PER-AXIS axial com-along-cable (benign) + LATERAL/z cage-escape (the gate). NOT no-slip. GPU HELD for
    Rs auth (first-GPU-spend of Layer-B)."""
    raise NotImplementedError("S1 HELD (cuda:0; spec in docstring) — RUN gated on %12/Rs GPU auth.")


def run_s2():
    """S2: tail-cell screening — nominal + DR-corner (+-16mm table-void edge) + known-hard; gate = worst.

    [BUILD PENDING — HELD]. nominal is easiest (non-conservative, CC3-CH5) so nominal-only cannot gate the
    81-offset tail; verdict = the WORST screened cell. GPU HELD for Rs auth."""
    raise NotImplementedError("S2 HELD (cuda:0; spec in docstring) — RUN gated on %12/Rs GPU auth.")


_STAGES = {"s0": run_s0, "s1": run_s1, "s2": run_s2}


def main() -> int:
    ap = argparse.ArgumentParser(description="SRG probe (staged grip-efficacy go/no-go)")
    ap.add_argument("--stage", choices=sorted(_STAGES), required=True)
    args = ap.parse_args()
    t0 = time.time()
    out = _STAGES[args.stage]()
    out["elapsed_s"] = round(time.time() - t0, 1)
    out["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    out["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    out["newton_device"] = os.environ.get("NEWTON_DEVICE", "<unset>")
    path = os.path.join(OUT_DIR, f"srg_probe_{args.stage}_result.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    print(f"[SRG {args.stage.upper()}] verdict={out.get('s0_verdict', out.get('verdict', 'n/a'))} -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
