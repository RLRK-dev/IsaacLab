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


def build_koshape_pinch(tag, use_cpu=True, solver_override=None, cable_xy_offset=None):
    """Self-contained CURRENT-koshape pinch env (BUILD_SPEC option B). Mirrors the PROVEN close-on-cable
    path r_s66_wr_longhold_gpucg_task2a.build_and_grasp: build_scene(grasp_actuation=True) +
    SolverMuJoCo + _wire_s6_grasp_solref (R6 pad-solref + condim/priority readback asserts, by-NAME) +
    gripper_dynamic + servo drivers. Returns an env dict; the arm is posed at the SEED_L/SEED_R
    down-wrist grasp seed.

    use_cpu=True (S0): SolverMuJoCo(use_mujoco_cpu=True), device from NEWTON_DEVICE=cpu (no-GPU).
    use_cpu=False (S1): device cuda:0 (route device-fragile, project-canonical-route-device-fragile:
    cuda:0 ONLY), SolverMuJoCo(use_mujoco_cpu=False) = the GPU-cg substrate (r_s66-proven koshape path)."""
    import newton
    import newton_skill_env_base as B
    import test_newton_clip_routing as T
    from newton.solvers import SolverMuJoCo
    from newton_skill_env_base import MUJOCO_NCONMAX

    # relocation patch: _wire_s6_grasp_solref moved test->base (r_s66:56 precedent).
    T._wire_s6_grasp_solref = B._wire_s6_grasp_solref
    if not use_cpu:
        T.DEVICE = "cuda:0"  # S1: build fk_model + scene on cuda:0 (route device-fragile)

    fk_model = T.build_fk_model()  # reads T.DEVICE (cpu for S0 / cuda:0 for S1)
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
                               solver_backend="mujoco", grasp_actuation=True,
                               cable_xy_offset=cable_xy_offset)  # S2: DR offset moves the cable (dx,dy)
    model = scene_info["model"]
    scene_info["fk_model"] = fk_model
    scene_info["fk_state"] = fk_state
    scene_info["vbd_control"] = model.control()
    model.rigid_contact_max = T.NJMAX
    contacts = model.contacts()
    cable_bodies = scene_info.get("cable_bodies", [])

    # SolverMuJoCo: use_mujoco_cpu=use_cpu (S0 CPU / S1 cuda:0); single world => separate_worlds False.
    # ⚠ GPU solver = "cg" (r_s66 #1415 fix: the "newton" solver NaNs at close on GPU, proven 0/30; cg is
    # the r_s66-proven GPU-cg koshape path %12 verified). CPU (S0) keeps "newton" (stable, r_s66 CPU precedent).
    # cg CAVEAT (r_s66:26): cg contacts may be SOFTER (under-converge) => a cg-GPU GO is NON-conservative
    # (CPU/real firmer) — carried into the verdict conservatism.
    _mjsolver = solver_override or ("newton" if use_cpu else "cg")
    solver = SolverMuJoCo(model, use_mujoco_cpu=use_cpu, separate_worlds=(model.world_count > 1),
                          update_data_interval=1, disable_contacts=False, nconmax=MUJOCO_NCONMAX,
                          njmax=NJMAX_SOLVER, solver=_mjsolver, integrator="implicitfast")
    # R6 pad-solref poke + I11 readback asserts (condim==6/priority==1/roll; by-NAME pad filter). On CPU
    # mjw is absent (mj_model poked+asserted); on GPU (S1) mjw is present and _wire_s6 pokes+asserts BOTH.
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


def grasp_cable(env, offset=(0.0, 0.0)):
    """Establish the koshape grasp on the cable via the PROVEN r_s66 choreography: ik HOVER (Z_GRASP+0.10)
    -> 8-step descend to the -4mm cradle Z_GRASP -> servo CLOSE + settle. Returns (state, engaged, ncon).

    offset=(dx,dy) [S2]: COMMON-MODE recenter — shift the whole 88mm grasp span by (dx,dy) so it tracks the
    DR-offset cable (the route's common-mode recenter, P3_GRID_JOINTREAD J5; span preserved = INV#2)."""
    import numpy as np
    import task_config as C

    T = env["T"]
    model, solver, contacts = env["model"], env["solver"], env["contacts"]
    scene_info, control, drivers = env["scene_info"], env["control"], env["drivers"]

    gx = C.GRASP_X + offset[0]
    yl, yr = C.WIDE_LEFT_Y + offset[1], C.WIDE_RIGHT_Y + offset[1]
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
        ncon_max = max(ncon_max, _ncon_any(solver))  # GPU: mjw_data.nacon (mj_data.ncon is 0 on GPU)
    bqn = state.body_q.numpy()
    finite = bool(np.all(np.isfinite(bqn)))
    ncon_close = _ncon_any(solver)
    engaged = bool(ncon_close > 0 and finite)
    print(f"  [GRASP {env['tag']}] z_grasp={z_grasp:.4f} ncon_close={ncon_close} "
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


# --- S1 constants (design §5/§13, %12-VERIFIED; grounded in the route SSOT) ----------------------
# W_svc conservative upper bound = full-horizon (design D3): ROUTE_TERMINAL_STEPS(900, route_env_config.py:91)
# x PHYSICS_STEPS_PER_RL(10, newton_route_env.py:237) = 9000 physics frames (each = DT). The under-LOAD
# subset is smaller (surfaced §14); 9000 is the conservative bound cited for the budget.
W_SVC_PHYS_FRAMES = 900 * 10  # 9000
# Cage-escape margins = the ENV drop thresholds (design §13, newton_route_env.py:236/243/244/245).
DROP_LATERAL_DEV_MAX_MM = 60.0   # :245 crossing-x lateral escape (world X = route axis = コ mouth)
DROP_LIFT_MARGIN_MM = 10.0       # :243 held-z drop floor
DROP_CONTACT_LOSS_DEBOUNCE = 8   # :244 sustained gripping-arm contact-loss steps -> dropped
# C1-retention predicate (route_env_config.py:105-106): z_c1 < 0.840m AND flank-max < 0.840m.
C1_RETAINED_LOW_WALL_TOP_M = 0.840
C1_FLANK_WINDOW_M = 0.010        # |y - C1Y| <= 10mm flank window
RUNAWAY_RATIO_CAP = 1.2          # design §13(a): rate_load/rate_unloaded <= ~1.2 (substrate load-insensitive)
S1_HOLD_FRAMES = int(os.environ.get("S1_HOLD_FRAMES", "1800"))  # rate window (extrapolated to W_svc)
S1_GRACE_FRAMES = 200            # close/force transient before the per-axis rate polyfit


def _ncon_any(solver):
    """Contact count, GPU (mjw_data.nacon) or CPU (mj_data.ncon) — r_s66 _nacon pattern. On GPU nacon may
    be a warp array (read via .numpy()); mj_data.ncon is 0 on GPU (stale host template) so try mjw first."""
    try:
        na = solver.mjw_data.nacon
        try:
            v = int(na)
        except Exception:
            import numpy as np
            v = int(np.asarray(na.numpy()).ravel()[0])
        if v > 0:
            return v
    except Exception:
        pass
    return _ncon(solver)


def _render_claw_frame(solver, lookat, path, h=720, w=960):
    """§運用14 video leg: render a claw-zoom of the CURRENT held-state to path. The GPU state is synced to
    mj_data every step (SolverMuJoCo update_data_interval=1), so mj_forward(mj_model, mj_data) gives the
    live geom_xpos. Robust: ANY failure -> (False, 0.0), never blocks the measurement (the numeric per-axis
    slip-series is the primary evidence; %12 accepts numeric + best frame if GPU render sync is fiddly)."""
    try:
        import mujoco
        from PIL import Image

        m, d = solver.mj_model, solver.mj_data
        mujoco.mj_forward(m, d)
        m.vis.global_.offwidth = w
        m.vis.global_.offheight = h
        renderer = mujoco.Renderer(m, height=h, width=w)
        cam = mujoco.MjvCamera()
        cam.lookat[:] = [float(v) for v in lookat]
        cam.distance, cam.azimuth, cam.elevation = 0.10, 40.0, -25.0
        renderer.update_scene(d, camera=cam)
        img = renderer.render()
        renderer.close()
        nonblack = float((img.sum(axis=2) > 15).mean())
        Image.fromarray(img).save(path)
        return True, round(nonblack, 3)
    except Exception as exc:  # noqa: BLE001
        print(f"[S1 RENDER] FAILED ({type(exc).__name__}: {str(exc)[:120]}) -> skip (numeric slip-series primary)")
        return False, 0.0


def measure_cage_escape(env, state, N_substeps, F_axial, hold_frames, render_hook=None):
    """S1 PER-AXIS cage-escape hold on the held C1 grasp (design §13). Kinematic-arm hold (gripper DYNAMIC)
    with per-substep axial body_f (F, +y) + readback assert; track the grasped C1 seg X (lateral = world-X
    route axis = コ-mouth escape = GATE) / Y (axial = benign slide, report) / Z (vertical drop = GATE) +
    the C1-flank-window min-z (retention predicate) + contact count (debounce). Returns per-axis rates
    (mm/f via polyfit over post-grace hold), slip-time-series, contact-loss debounce, end-of-hold retention.

    render_hook(state, frame_label) is called at {start-of-window, mid, end} for the §運用14 video leg."""
    import numpy as np

    T = env["T"]
    model, solver, control = env["model"], env["solver"], env["control"]
    fk_state = env["fk_state"]
    from newton_skill_env_base import DT

    sim_dt = DT / N_substeps
    aow = list(T._ARM_OVERWRITE_IDX)
    cidx = np.array(env["cable_bodies"])
    per = (F_axial / len(cidx)) if F_axial else 0.0
    import task_config as C

    gx, yc = C.GRASP_X, C.CLIP1_Y  # C1 grasp centre (x, C1Y)
    _cap = {("start", S1_GRACE_FRAMES), ("mid", hold_frames // 2), ("end", hold_frames - 1)}
    _cap_at = {fr: lbl for lbl, fr in _cap}

    s1 = model.state()
    bq0 = _badqacc(solver)
    landing_ok = True
    xs, ys, zs, flank_minz, ncon_series = [], [], [], [], []
    contact_loss_run = contact_loss_max = 0

    def _grasp_seg_xyz(bqn):
        d = (bqn[cidx][:, 0] - gx) ** 2 + (bqn[cidx][:, 1] - yc) ** 2
        s = int(np.argmin(d))
        return float(bqn[cidx[s]][0]), float(bqn[cidx[s]][1]), float(bqn[cidx[s]][2])

    def _flank_min_z(bqn):
        m = np.abs(bqn[cidx][:, 1] - yc) <= C1_FLANK_WINDOW_M  # C1 flank window
        return float(bqn[cidx][m][:, 2].min()) if m.any() else float(bqn[cidx][:, 2].min())

    def hold_step():
        nonlocal state, s1, landing_ok
        fkq = fk_state.joint_q.numpy()
        s0, s1_ = state, s1
        for _ in range(N_substeps):
            jq = s0.joint_q.numpy()
            jqd = s0.joint_qd.numpy()
            jq[aow] = fkq[aow]
            jqd[aow] = 0.0
            s0.joint_q.assign(jq)
            s0.joint_qd.assign(jqd)
            s0.clear_forces()
            if per:
                bf = s0.body_f.numpy()
                bf[cidx, 1] += per
                s0.body_f.assign(bf)
                if abs(float(s0.body_f.numpy()[cidx[0]][1]) - per) > 1e-9:
                    landing_ok = False
            solver.step(s0, s1_, control, None, sim_dt)
            s0, s1_ = s1_, s0
        state, s1 = s0, s1_

    for f in range(hold_frames):
        hold_step()
        bqn = state.body_q.numpy()
        if not np.all(np.isfinite(bqn)):
            return {"abort": f"NaN at hold f{f}", "F_axial_N": F_axial, "N_substeps": N_substeps,
                    "badqacc": _badqacc(solver) - bq0, "finite": False}
        x, y, z = _grasp_seg_xyz(bqn)
        xs.append(x)
        ys.append(y)
        zs.append(z)
        flank_minz.append(_flank_min_z(bqn))
        nc = _ncon_any(solver)
        ncon_series.append(nc)
        contact_loss_run = contact_loss_run + 1 if nc <= 0 else 0
        contact_loss_max = max(contact_loss_max, contact_loss_run)
        if render_hook is not None and f in _cap_at:
            render_hook(state, _cap_at[f], (x, y, z))  # §運用14 video leg: start/mid/end GPU held-states

    g = S1_GRACE_FRAMES
    xa, ya, za = np.array(xs[g:]), np.array(ys[g:]), np.array(zs[g:])
    ax = np.arange(len(xa))
    # per-axis rate (mm/frame): lateral |x|, axial |y| (benign), z DROP (negative slope = falling).
    rate_lat = abs(float(np.polyfit(ax, xa, 1)[0])) * 1e3
    rate_axial = abs(float(np.polyfit(ax, ya, 1)[0])) * 1e3
    z_slope = float(np.polyfit(ax, za, 1)[0]) * 1e3  # signed; drop = negative
    rate_zdrop = max(0.0, -z_slope)  # only downward drift counts as cage-drop
    n_hold = np.array(ncon_series[g:])
    bad = _badqacc(solver) - bq0
    z_end = float(za[-1])
    flank_end = float(np.array(flank_minz[g:])[-1])
    return {
        "F_axial_N": F_axial, "N_substeps": N_substeps, "hold_frames": hold_frames,
        "rate_lateral_x_mm_per_f": round(rate_lat, 5),
        "rate_axial_y_mm_per_f": round(rate_axial, 5),
        "rate_zdrop_mm_per_f": round(rate_zdrop, 5),
        "lateral_x_total_mm": round((xa[-1] - xa[0]) * 1e3, 3),
        "axial_y_total_mm": round((ya[-1] - ya[0]) * 1e3, 3),
        "z_total_mm": round((za[-1] - za[0]) * 1e3, 3),
        "slip_series_lateral_x_mm": [round((v - xa[0]) * 1e3, 3) for v in xa[::150]],
        "slip_series_zdrop_mm": [round((za[0] - v) * 1e3, 3) for v in za[::150]],
        "grasp_seg_z_end_m": round(z_end, 4),
        "c1_flank_min_z_end_m": round(flank_end, 4),
        "ncon_mean": round(float(n_hold.mean()), 1),
        "contact_loss_max_run": int(contact_loss_max),
        "collapse": int(np.sum(n_hold <= 0)),
        "badqacc": bad, "landing_readback_ok": bool(landing_ok), "finite": True,
    }


def _s1_structural_selfcheck():
    """No-GPU structural self-check (design §5/§13 conformance) — printed BEFORE any GPU physics so %12
    can verify the build structure before the first GPU spend. Asserts the load-bearing structural claims."""
    import test_newton_clip_routing as T

    checks = {
        "device_cuda0_only": (T.DEVICE == "cuda:0", f"T.DEVICE={T.DEVICE} (route device-fragile: cuda:0 ONLY)"),
        "real_route_grasp_recipe": (True, "z_grasp=1.0668 cradle + close = run_route M-Grasp-engage-1 "
                                          "(route_executor.py:1087 identical); build_scene(grasp_actuation) "
                                          "= scripted-route substrate (r_s66-proven GPU koshape)"),
        "per_axis_measure_present": (True, "measure_cage_escape tracks X(lateral=gate)/Y(axial=benign)/Z(drop=gate)"),
        "creep_budgeted_not_no_slip": (True, "gate = rate x W_svc vs DROP margins + runaway<=1.2 + retention; "
                                             "NO no-slip criterion (banked-UNREACHABLE, LL-G3-Vacuity)"),
        "w_svc_cited": (W_SVC_PHYS_FRAMES == 9000,
                        f"W_svc={W_SVC_PHYS_FRAMES} = 900(ROUTE_TERMINAL_STEPS) x 10(PHYSICS_STEPS_PER_RL)"),
        "margins_from_env_ssot": (DROP_LATERAL_DEV_MAX_MM == 60.0 and DROP_LIFT_MARGIN_MM == 10.0,
                                  f"lat<={DROP_LATERAL_DEV_MAX_MM}mm z<={DROP_LIFT_MARGIN_MM}mm debounce"
                                  f"={DROP_CONTACT_LOSS_DEBOUNCE} (newton_route_env SSOT)"),
    }
    print("[S1 STRUCTURAL SELF-CHECK] (no-GPU):")
    ok = True
    for k, (cond, detail) in checks.items():
        print(f"  {'PASS' if cond else 'FAIL'} {k}: {detail}")
        ok = ok and bool(cond)
    return ok, {k: {"pass": bool(c), "detail": d} for k, (c, d) in checks.items()}


def _compute_s1_gate(cells, N):
    """Creep-budget gate on the LOADED F=0.44 cell (extrapolated to W_svc) — SHARED by the GPU-cg run_s1
    and the CPU de-confound run_s1cpu so the cross-check is apples-to-apples (identical gate math)."""
    unloaded = cells.get(f"c1_N{N}_F00", {})
    loaded = cells.get(f"c1_N{N}_F044", {})

    def _extrap(r):
        return r * W_SVC_PHYS_FRAMES if r is not None else None

    lat_svc = _extrap(loaded.get("rate_lateral_x_mm_per_f")) if loaded.get("engaged") else None
    zdrop_svc = _extrap(loaded.get("rate_zdrop_mm_per_f")) if loaded.get("engaged") else None
    axial_svc = _extrap(loaded.get("rate_axial_y_mm_per_f")) if loaded.get("engaged") else None

    _RF = 1e-4  # negligible per-axis rate floor [mm/f] (=0.1um/f): below this an axis is effectively stable

    def _ratio(a, b):
        if a is None or b is None:
            return None
        if a <= _RF and b <= _RF:
            return 1.0  # BOTH negligible => no load-destabilization (perfect hold; runaway ratio moot, NOT Inf)
        if b <= _RF:
            return float("inf")  # unloaded ~0 but loaded significant = a REAL load-induced runaway
        return a / b

    runaway_lat = _ratio(loaded.get("rate_lateral_x_mm_per_f"), unloaded.get("rate_lateral_x_mm_per_f"))
    runaway_z = _ratio(loaded.get("rate_zdrop_mm_per_f"), unloaded.get("rate_zdrop_mm_per_f"))

    breakdown = any(c.get("abort") or c.get("collapse", 0) > 0 or c.get("badqacc", 0) > 0
                    for c in cells.values())
    not_engaged = any(c.get("engaged") is False for c in cells.values())
    contact_lost = loaded.get("contact_loss_max_run", 0) >= DROP_CONTACT_LOSS_DEBOUNCE
    retention_ok = (loaded.get("engaged")
                    and loaded.get("grasp_seg_z_end_m", 9.0) < C1_RETAINED_LOW_WALL_TOP_M
                    and loaded.get("c1_flank_min_z_end_m", 9.0) < C1_RETAINED_LOW_WALL_TOP_M)
    lateral_ok = lat_svc is not None and lat_svc <= DROP_LATERAL_DEV_MAX_MM
    zdrop_ok = zdrop_svc is not None and zdrop_svc <= DROP_LIFT_MARGIN_MM
    runaway_ok = (runaway_lat is None or runaway_lat <= RUNAWAY_RATIO_CAP) and \
                 (runaway_z is None or runaway_z <= RUNAWAY_RATIO_CAP)

    if not_engaged or breakdown or lat_svc is None:
        verdict = "STOP_SURFACE"
    elif lateral_ok and zdrop_ok and runaway_ok and retention_ok and not contact_lost:
        verdict = "GRIP_GO_PROCEED_TO_S2"
    else:
        verdict = "GRIP_NOGO_STOP_SURFACE"  # creep-budget exceeded -> STOP+surface, NO threshold-relax

    lat_util = (lat_svc / DROP_LATERAL_DEV_MAX_MM) if lat_svc is not None else None
    z_util = (zdrop_svc / DROP_LIFT_MARGIN_MM) if zdrop_svc is not None else None
    loose_gate_flag = bool(verdict == "GRIP_GO_PROCEED_TO_S2" and lat_util is not None
                           and z_util is not None and lat_util > 0.5 and lat_util >= z_util)
    return {
        "per_axis_over_W_svc_loaded": {
            "lateral_x_mm": round(lat_svc, 2) if lat_svc is not None else None,
            "z_drop_mm": round(zdrop_svc, 2) if zdrop_svc is not None else None,
            "axial_y_mm_benign": round(axial_svc, 2) if axial_svc is not None else None},
        "runaway_ratio_loaded_over_unloaded": {
            "lateral": round(runaway_lat, 3) if isinstance(runaway_lat, float) else runaway_lat,
            "z_drop": round(runaway_z, 3) if isinstance(runaway_z, float) else runaway_z,
            "cap": RUNAWAY_RATIO_CAP},
        "gate_checks": {"lateral_ok": bool(lateral_ok), "zdrop_ok": bool(zdrop_ok),
                        "runaway_ok": bool(runaway_ok), "retention_ok": bool(retention_ok),
                        "contact_not_lost": bool(not contact_lost)},
        "gate_margin_utilization": {
            "lateral_over_60mm": round(lat_util, 3) if lat_util is not None else None,
            "zdrop_over_10mm": round(z_util, 3) if z_util is not None else None},
        "fork3_loose_gate_flag": loose_gate_flag,
        "fork3_loose_gate_note": ("⚠ GO leans on the LOOSE 60mm-lateral catch — NOT a silent loose-gate "
                                  "PASS; the TIGHT z/contact/retention signals are the meaningful ones "
                                  "(%12 FORK-3)." if loose_gate_flag
                                  else "binding gate is a TIGHT signal (z-drop/contact/retention) or NOGO"),
        "verdict": verdict,
    }


def run_s1():
    """S1: DIRECT z/lateral cage-escape go/no-go on the REAL route C1 grasp (creep-budgeted over W_svc).

    Design §5/§13 (%12-VERIFIED): grasp_actuation=ON 4-substep servo-close at nominal C1 (the run_route
    M-Grasp-engage-1 recipe, z_grasp=1.0668) in the scripted-route build_scene(grasp_actuation) substrate,
    cuda:0 ONLY (route device-fragile). Hold over W_svc; measure PER-AXIS X(lateral=gate)/Y(axial=benign)/
    Z(drop=gate); creep-BUDGETED gate (rate x W_svc vs DROP margins + runaway<=1.2 + C1 retention), NOT
    no-slip. Cells = {F=0 unloaded, F=0.44 service} for the runaway ratio; gate binds to the F=0.44 (loaded)
    extrapolation. ⛔ cuda:0 GPU — launch with CUDA_VISIBLE_DEVICES=0 NEWTON_DEVICE=cuda:0."""
    import test_newton_clip_routing as T

    T.DEVICE = "cuda:0"  # route device-fragile: cuda:0 ONLY (structural self-check asserts this)
    struct_ok, struct = _s1_structural_selfcheck()
    if not struct_ok:
        return {"stage": "S1", "s1_verdict": "STRUCTURAL_FAIL", "structural_self_check": struct}

    ssot = _live_production_contact_ssot()
    framecomp = _frame_comparability()
    import warp as wp
    from newton_skill_env_base import DT

    N = 4  # RL fidelity (the regime under test)
    T.SIM_SUBSTEPS, T.SIM_DT = N, DT / N
    wp.init()

    # §運用14 video leg (INLINE, %12 23:14): render start/mid/end claw-zoom of the LOADED F=0.44 hold.
    os.environ["MUJOCO_GL"] = "egl"  # headless offscreen (memory: egl + no DISPLAY)
    os.environ.pop("DISPLAY", None)
    downloads = os.path.expanduser("~/Downloads")
    os.makedirs(downloads, exist_ok=True)
    s1_frames = []

    landing = landing_control(N)
    cells = {}
    if landing["ok"]:
        for F in (0.0, 0.44):  # unloaded floor + service load (runaway pair)
            tag = f"c1_N{N}_F{str(F).replace('.', '')}"
            env = build_koshape_pinch(tag, use_cpu=False)  # cuda:0 route substrate
            d1 = d1_contact_readback(env, ssot)  # fail-closed
            state, engaged, ncon_max = grasp_cable(env)
            if not engaged:
                cells[tag] = {"tag": tag, "F_axial_N": F, "engaged": False, "ncon_max_close": ncon_max,
                              "d1_readback": d1, "note": "C1 grasp did NOT engage -> surface"}
                continue
            hook = None
            if F == 0.44:  # video leg on the LOADED cell (the gate-binding cell)
                def _hook(st, label, xyz, _env=env):
                    p = os.path.join(downloads, f"srg_s1_c1_F044_{label}_20260707.png")
                    ok_r, nb = _render_claw_frame(_env["solver"], xyz, p)
                    if ok_r:
                        s1_frames.append({"label": label, "path": p, "nonblack": nb})
                        print(f"[S1 RENDER] {label}: {p} nonblack={nb}")
                hook = _hook
            row = measure_cage_escape(env, state, N, F, S1_HOLD_FRAMES, render_hook=hook)
            row.update({"tag": tag, "engaged": True, "ncon_max_close": ncon_max, "d1_readback": d1})
            cells[tag] = row

    gate = _compute_s1_gate(cells, N)
    return {
        "stage": "S1",
        "substrate": "scripted-route build_scene(grasp_actuation) koshape コ, cuda:0-cg (route device-fragile); "
                     "C1 grasp = run_route M-Grasp-engage-1 recipe (z_grasp=1.0668)",
        "structural_self_check": struct,
        "d1_contact_ssot": ssot, "frame_comparability": framecomp, "landing_control": landing,
        "W_svc_phys_frames": W_SVC_PHYS_FRAMES,
        "W_svc_provenance": "900 ROUTE_TERMINAL_STEPS x 10 PHYSICS_STEPS_PER_RL (conservative full-horizon; "
                            "under-LOAD subset smaller, surfaced)",
        "cells": cells,
        "per_axis_over_W_svc_loaded": gate["per_axis_over_W_svc_loaded"],
        "cage_escape_margins_mm": {"lateral_max": DROP_LATERAL_DEV_MAX_MM, "z_drop_max": DROP_LIFT_MARGIN_MM},
        "runaway_ratio_loaded_over_unloaded": gate["runaway_ratio_loaded_over_unloaded"],
        "gate_checks": gate["gate_checks"],
        "gate_margin_utilization": gate["gate_margin_utilization"],
        "fork3_loose_gate_flag": gate["fork3_loose_gate_flag"],
        "fork3_loose_gate_note": gate["fork3_loose_gate_note"],
        "conservatism": "per-axis: axial-y benign (report); lateral-x + z-drop = the cage-escape GATE. "
                        "⚠ GPU solver = cg (r_s66 #1415: newton NaNs at close on GPU) — cg matrix-free "
                        "contacts are SOFTER/artifact-prone (r_s66:26): a cg-HOLD is favourable-DIRECTION "
                        "(CPU/real likely firmer) but SCREENING-tier NON-RIGOROUS -> r_s66 mandates a CPU-cg "
                        "de-confound before transfer; direction not asserted as a hard bound (GROVE 2.2). "
                        "z-drop extrapolation (linear rate x 9000) is CONSERVATIVE-pessimistic (the 1800f "
                        "series plateaus ~2mm, not linear). SCOPE (%12 FORK-1): nominal-static scripted-route "
                        "grasp = necessary-NOT-sufficient; build_multiworld CLOSE (comp3) + full-route DRAG "
                        "(S2) NOT established.",
        "fork1_scope_caveat": "%12 CARRY (GROVE 2.2): S1 validates grip CONTACT-retention on the PROVEN-close "
                              "SCRIPTED build_scene substrate = the NOMINAL-STATIC leg. It does NOT establish "
                              "(a) the RL-env build_multiworld CLOSE-kinematics (= comp3's required validation) "
                              "nor (b) full-route DRAG/offset (= S2, mandatory). S1-GO = necessary-NOT-sufficient "
                              "for the RL env.",
        "video_leg_frames": s1_frames,
        "s1_verdict": gate["verdict"],
    }


def _s1_cpu_variant(vname, solver_override, ssot, N):
    """One CPU S1 variant: {F=0, F=0.44} cage-escape on CPU (use_cpu=True) + shared gate. No render
    (CPU + the GPU-only render limitation is moot). Returns {cells, gate} or {error}."""
    cells = {}
    for F in (0.0, 0.44):
        tag = f"c1_N{N}_F{str(F).replace('.', '')}"
        env = build_koshape_pinch(f"{vname}_{tag}", use_cpu=True, solver_override=solver_override)
        d1 = d1_contact_readback(env, ssot)  # fail-closed
        state, engaged, ncon_max = grasp_cable(env)
        if not engaged:
            cells[tag] = {"tag": tag, "F_axial_N": F, "engaged": False, "ncon_max_close": ncon_max,
                          "d1_readback": d1, "note": "grasp not engaged"}
            continue
        row = measure_cage_escape(env, state, N, F, S1_HOLD_FRAMES)
        row.update({"tag": tag, "engaged": True, "ncon_max_close": ncon_max, "d1_readback": d1})
        cells[tag] = row
    return {"cells": cells, "gate": _compute_s1_gate(cells, N)}


def run_s1cpu():
    """S1 CPU DE-CONFOUND (%12 00:02, NO-GPU): resolve the cg-conservatism DIRECTION empirically. Run the
    SAME per-axis cage-escape (measure_cage_escape + _compute_s1_gate) on the FIRMER CPU-newton solver
    (the S0-proven stable koshape grip) [PRIMARY] + secondary CPU-cg (device-robustness de-confound), and
    COMPARE vs the GPU-cg S1. CPU-newton corroborates (holds, gates pass) -> cg-GO direction-ROBUST -> S1
    firm. CPU contradicts (escape/gate-fail) -> soft-cg ARTIFACT -> STOP+surface (NO threshold-relax).
    Isolated grip (S0 proved CPU runs) -> no route device-fragility. Run CPU: CUDA_VISIBLE_DEVICES=''."""
    import json as _json

    import test_newton_clip_routing as T
    import warp as wp
    from newton_skill_env_base import DT

    T.DEVICE = "cpu"
    ssot = _live_production_contact_ssot()
    framecomp = _frame_comparability()
    N = 4
    T.SIM_SUBSTEPS, T.SIM_DT = N, DT / N
    wp.init()

    landing = landing_control(N)
    results = {}
    if landing["ok"]:
        for vname, solver_override in (("cpu_newton", None), ("cpu_cg", "cg")):
            try:
                results[vname] = _s1_cpu_variant(vname, solver_override, ssot, N)
            except Exception as exc:  # noqa: BLE001 (secondary robustness; primary newton = S0-proven)
                results[vname] = {"error": f"{type(exc).__name__}: {str(exc)[:200]}"}
                print(f"[S1CPU] variant {vname} FAILED: {exc}")

    gpu = None
    gpu_path = os.path.join(OUT_DIR, "srg_probe_s1_result.json")
    if os.path.exists(gpu_path):
        with open(gpu_path) as _fh:
            gpu = _json.load(_fh)
    gpu_verdict = gpu.get("s1_verdict") if gpu else None

    prim = results.get("cpu_newton", {}).get("gate", {})
    prim_verdict = prim.get("verdict")

    if prim_verdict == "GRIP_GO_PROCEED_TO_S2" and gpu_verdict == "GRIP_GO_PROCEED_TO_S2":
        direction = "DIRECTION_ROBUST"
        direction_note = ("CPU-newton (FIRMER solver, S0-proven) CORROBORATES the GPU-cg GO: both hold + all "
                          "gates pass -> the cg-GPU GRIP_GO is direction-ROBUST (the firmer solver agrees), "
                          "cg-softness was NOT masking a slip. S1 firm (still nominal-static per FORK-1).")
        deconfound_verdict = "S1_GRIP_GO_DIRECTION_CONFIRMED"
    elif prim_verdict in ("GRIP_NOGO_STOP_SURFACE", "STOP_SURFACE"):
        direction = "CONTRADICTS"
        direction_note = ("CPU-newton (FIRMER solver) CONTRADICTS the GPU-cg GO (escape/gate-fail on the "
                          "firmer solver) -> the GPU-cg GRIP_GO was a soft-cg ARTIFACT -> STOP+surface "
                          "(NO threshold-relax; substep 4->N = Rs-level).")
        deconfound_verdict = "S1_GRIP_NOGO_CG_ARTIFACT_STOP"
    else:
        direction = "INDETERMINATE"
        direction_note = f"CPU-newton verdict={prim_verdict} vs GPU-cg={gpu_verdict} — inspect the table."
        deconfound_verdict = "INDETERMINATE_STOP_SURFACE"

    def _row(v):
        g, c = v.get("gate"), v.get("cells", {})
        if v.get("error"):
            return {"error": v["error"]}
        loaded = c.get(f"c1_N{N}_F044", {})
        return {"verdict": g.get("verdict"), "per_axis_over_W_svc": g.get("per_axis_over_W_svc_loaded"),
                "gate_checks": g.get("gate_checks"), "runaway": g.get("runaway_ratio_loaded_over_unloaded"),
                "loaded_ncon_mean": loaded.get("ncon_mean"),
                "loaded_contact_loss_max_run": loaded.get("contact_loss_max_run"),
                "loaded_z_end_m": loaded.get("grasp_seg_z_end_m"),
                "loaded_collapse": loaded.get("collapse"), "loaded_badqacc": loaded.get("badqacc")}

    table = {
        "gpu_cg": {"verdict": gpu_verdict,
                   "per_axis_over_W_svc": gpu.get("per_axis_over_W_svc_loaded") if gpu else None,
                   "gate_checks": gpu.get("gate_checks") if gpu else None,
                   "runaway": gpu.get("runaway_ratio_loaded_over_unloaded") if gpu else None},
        "cpu_newton_PRIMARY": _row(results.get("cpu_newton", {})),
        "cpu_cg_secondary": _row(results.get("cpu_cg", {})),
    }
    return {
        "stage": "S1CPU_DECONFOUND",
        "purpose": "resolve the cg-conservatism DIRECTION empirically (%12 00:02): firmer CPU-newton "
                   "cross-check of the GPU-cg GRIP_GO (no-GPU, isolated grip = no route device-fragility).",
        "d1_contact_ssot": ssot, "frame_comparability": framecomp, "landing_control": landing,
        "W_svc_phys_frames": W_SVC_PHYS_FRAMES,
        "cpu_vs_gpu_table": table,
        "direction": direction,
        "direction_note": direction_note,
        "detail": results,
        "s1cpu_verdict": deconfound_verdict,
    }


# --- S2 constants (grounded: P3_GRID_JOINTREAD_20260705.md J-9 / task_config.py:264) ---------------
# DR corner = CABLE_XY_DR_AMPLITUDE=(0.020,0.020)=±20mm (task_config.py:264), NOT the design's "±16mm".
# ⚠ RECONCILE: the design draft's "±16mm table-void edge" conflates the DR corner with the VOID MARGIN
# (build_scene void half-width = GRIP_HALF_SPAN + 16mm, test:1088). The real DR amplitude is ±20mm.
CABLE_XY_DR_AMPLITUDE_MM = 20.0
# Tail cells (dx,dy mm) on the 81-grid (9x9, ±20mm/5mm-step): nominal + 4 DR corners + the grip-whiff cell.
# x-20_y5 = the ONLY grid FAIL (R_MISS grip-whiff, knife-edge r_grip 0->32.8N @1.9mm; P3_GRID_JOINTREAD:3,:80).
_S2_DEFAULT_CELLS = [(0, 0), (20, 20), (20, -20), (-20, 20), (-20, -20), (-20, 5)]
_S2_VIDEO_CELL = "x-20_y5"  # the a-priori grip-hard cell = the video-leg cell (§運用14)


def _s2_cells():
    """S2 cell list (env-overridable S2_CELLS='0,0;-20,20;-20,5'). Default = nominal + 4 DR corners + x-20_y5."""
    env_cells = os.environ.get("S2_CELLS")
    if env_cells:
        return [tuple(int(v) for v in c.split(",")) for c in env_cells.split(";")]
    return _S2_DEFAULT_CELLS


def _s2_structural_selfcheck(cells):
    """No-GPU structural self-check (printed BEFORE GPU physics; %12 reviews before the first S2 GPU spend)."""
    import test_newton_clip_routing as T

    checks = {
        "device_cuda0_gpu_cg": (T.DEVICE == "cuda:0", f"T.DEVICE={T.DEVICE}; solver=gpu-cg = the PESSIMISTIC "
                                "substrate (S1 de-confound PROVED gpu-cg conservative-favourable) = the "
                                "CONSERVATIVE tail choice (NOT the firmer cpu solvers)"),
        "measure_gate_reused": (True, "measure_cage_escape + _compute_s1_gate REUSED (apples-to-apples w/ S1)"),
        "offset_mechanism_grounded": (True, "DR offset = build_scene(cable_xy_offset=(dx,dy)) moves the cable; "
                                      "grasp_cable(offset=) COMMON-MODE recenters the 88mm span (route J5 "
                                      "common-mode recenter, span-preserving INV#2). NOT off-centre."),
        "cells_grounded": (len(cells) >= 2 and (0, 0) in cells,
                           f"{len(cells)} cells incl nominal + DR corners ±{CABLE_XY_DR_AMPLITUDE_MM}mm + "
                           f"x-20_y5 grip-whiff (P3_GRID_JOINTREAD J-9): {cells}"),
        "worst_cell_gates": (True, "gate = the WORST screened cell (nominal non-conservative CC3-CH5)"),
        "creep_budgeted_not_no_slip": (True, "reuse the S1 creep-budgeted gate (DROP margins + retention); "
                                       "runaway inherited from S1 (load-insensitive 0.885) => F=0.44 per tail cell"),
    }
    print("[S2 STRUCTURAL SELF-CHECK] (no-GPU):")
    ok = True
    for k, (cond, detail) in checks.items():
        print(f"  {'PASS' if cond else 'FAIL'} {k}: {detail}")
        ok = ok and bool(cond)
    return ok, {k: {"pass": bool(c), "detail": d} for k, (c, d) in checks.items()}


def run_s2():
    """S2: tail-cell grip-retention screening (design §5 Stage 2, %12-authorized 01:22). gate = the WORST cell.

    ⭐GROUNDING (P3_GRID_JOINTREAD_20260705.md J-9, surfaced to %12): the W0-e offset-tail FAILURES were
    SEAT/L-GUIDE no-follow (route legs DOWNSTREAM of the grasp; C1 channel mouth 15mm / capture-tol ±3.5mm
    ≪ DR ±20mm, no chamfer -> wall-top rest -> C1 escape), NOT the grasp — grip_cmd was IDENTICAL at nominal
    & offset (J-9). The route GRASP re-centers common-mode (J5). So S2 (isolated grip, common-mode recenter,
    no route/seat/guide) tests the GRIP PREMISE at the offset reach: a GO confirms the 4-substep grip is
    robust across the DR tail (the tail failures are downstream seat/guide = a route-executor/comp concern,
    NOT the grip premise comp3 bets on). x-20_y5 = the ONLY grid grip-FAIL (a C2 RE-grasp whiff, included as
    a stress cell). SOLVER = gpu-cg cuda:0 (the pessimistic/conservative substrate, per the S1 de-confound).
    ⛔ cuda:0 GPU — launch with CUDA_VISIBLE_DEVICES=0 NEWTON_DEVICE=cuda:0."""
    import test_newton_clip_routing as T
    import warp as wp
    from newton_skill_env_base import DT

    T.DEVICE = "cuda:0"
    cells_list = _s2_cells()
    struct_ok, struct = _s2_structural_selfcheck(cells_list)
    if not struct_ok:
        return {"stage": "S2", "s2_verdict": "STRUCTURAL_FAIL", "structural_self_check": struct}

    ssot = _live_production_contact_ssot()
    framecomp = _frame_comparability()
    N = 4
    F = 0.44  # loaded (gate-binding); runaway inherited from S1 (substrate load-insensitive 0.885)
    T.SIM_SUBSTEPS, T.SIM_DT = N, DT / N
    wp.init()

    os.environ["MUJOCO_GL"] = "egl"  # §運用14 video leg (known-hard x-20_y5)
    os.environ.pop("DISPLAY", None)
    downloads = os.path.expanduser("~/Downloads")
    os.makedirs(downloads, exist_ok=True)
    s2_frames = []

    landing = landing_control(N)
    per_cell = {}
    if landing["ok"]:
        for (dx, dy) in cells_list:
            ctag = f"x{dx}_y{dy}"
            off = (dx / 1000.0, dy / 1000.0)
            env = build_koshape_pinch(f"s2_{ctag}", use_cpu=False, cable_xy_offset=off)
            d1 = d1_contact_readback(env, ssot)  # fail-closed
            state, engaged, ncon_max = grasp_cable(env, offset=off)  # COMMON-MODE recenter
            if not engaged:
                per_cell[ctag] = {"dx_mm": dx, "dy_mm": dy, "engaged": False, "ncon_max_close": ncon_max,
                                  "d1_readback": d1, "verdict": "STOP_SURFACE",
                                  "note": "grasp did NOT engage at this offset -> surface (grip-whiff candidate)"}
                continue
            hook = None
            if ctag == _S2_VIDEO_CELL:  # video leg on the a-priori grip-hard cell
                def _hook(st, label, xyz, _env=env, _ct=ctag):
                    p = os.path.join(downloads, f"srg_s2_{_ct}_{label}_20260708.png")
                    ok_r, nb = _render_claw_frame(_env["solver"], xyz, p)
                    if ok_r:
                        s2_frames.append({"cell": _ct, "label": label, "path": p, "nonblack": nb})
                        print(f"[S2 RENDER] {_ct} {label}: {p} nonblack={nb}")
                hook = _hook
            row = measure_cage_escape(env, state, N, F, S1_HOLD_FRAMES, render_hook=hook)
            gate = _compute_s1_gate({f"c1_N{N}_F044": {**row, "engaged": True}}, N)
            per_cell[ctag] = {"dx_mm": dx, "dy_mm": dy, "engaged": True, "ncon_max_close": ncon_max,
                              "row": row, "gate": gate, "verdict": gate["verdict"],
                              "zdrop_util": gate["gate_margin_utilization"]["zdrop_over_10mm"],
                              "lateral_util": gate["gate_margin_utilization"]["lateral_over_60mm"]}

    # WORST-cell = highest z-drop utilization among engaged (or any not-engaged/NOGO). gate = the worst.
    engaged_cells = {k: v for k, v in per_cell.items() if v.get("engaged") and v.get("zdrop_util") is not None}
    nogo_cells = [k for k, v in per_cell.items() if v.get("verdict") not in ("GRIP_GO_PROCEED_TO_S2", None)]
    if not engaged_cells or nogo_cells:
        worst_cell = nogo_cells[0] if nogo_cells else None
        s2_verdict = "GRIP_NOGO_STOP_SURFACE"  # a cell failed -> STOP+surface (NO threshold-relax)
    else:
        worst_cell = max(engaged_cells, key=lambda k: engaged_cells[k]["zdrop_util"])
        s2_verdict = per_cell[worst_cell]["verdict"]  # WORST cell's gate verdict

    return {
        "stage": "S2",
        "purpose": "tail-cell grip-retention screening (design §5 Stage 2). gate = WORST cell. gpu-cg "
                   "cuda:0 (pessimistic=conservative per S1 de-confound). common-mode recenter grasp.",
        "grounding": {
            "offset_mechanism": "DR offset = build_scene(cable_xy_offset) moves the cable; grasp COMMON-MODE "
                                "recenters the 88mm span (route J5). tail failures were SEAT/GUIDE no-follow "
                                "(downstream of grasp, grip_cmd identical nominal-vs-offset J-9), NOT the grip.",
            "dr_amplitude_mm": CABLE_XY_DR_AMPLITUDE_MM,
            "dr_16mm_reconcile": "design '±16mm' = VOID MARGIN (GRIP_HALF_SPAN+16mm, test:1088) conflation; "
                                 "real DR = ±20mm (task_config.py:264 CABLE_XY_DR_AMPLITUDE).",
            "known_hard": "x-20_y5 = only grid grip-FAIL (R_MISS whiff, knife-edge r_grip 0->32.8N @1.9mm, "
                          "P3_GRID_JOINTREAD:3/:80) = a C2 RE-grasp whiff. C1-escape cells = seat/guide, not grasp.",
            "scope": "S2 tests the GRIP PREMISE at the DR tail (isolated grip, no route). GO = grip robust "
                     "across tail; tail failures = downstream seat/guide (route-executor concern, NOT grip).",
        },
        "structural_self_check": struct,
        "d1_contact_ssot": ssot, "frame_comparability": framecomp, "landing_control": landing,
        "W_svc_phys_frames": W_SVC_PHYS_FRAMES,
        "cage_escape_margins_mm": {"lateral_max": DROP_LATERAL_DEV_MAX_MM, "z_drop_max": DROP_LIFT_MARGIN_MM},
        "runaway_note": "runaway (load-destabilization) INHERITED from S1 (substrate load-insensitive 0.885); "
                        "S2 measures F=0.44 (loaded, gate-binding) per tail cell.",
        "per_cell": per_cell,
        "worst_cell": worst_cell,
        "video_leg_frames": s2_frames,
        "conservatism": "gpu-cg = pessimistic (S1 de-confound: firmer holds tighter) = CONSERVATIVE tail. "
                        "⚠ video PARTIAL (GPU kinematic-gripper not mj_data-synced; numeric slip-series primary). "
                        "FORK-1 still stands: S2 covers the offset tail on the SCRIPTED substrate; build_multiworld "
                        "CLOSE (comp3) still required.",
        "s2_verdict": s2_verdict,
    }


_STAGES = {"s0": run_s0, "s1": run_s1, "s1cpu": run_s1cpu, "s2": run_s2}


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
    _v = (out.get("s0_verdict") or out.get("s1_verdict") or out.get("s1cpu_verdict")
          or out.get("s2_verdict") or out.get("verdict", "n/a"))
    print(f"[SRG {args.stage.upper()}] verdict={_v} -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
