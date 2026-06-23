#!/usr/bin/env python
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""R-S7.1 CLIP INSERT + KINEMATIC PIN v4 (human 2026-06-21). Fixes the v3 (_68) VISUAL artifacts the human caught:
(A) the cable appeared to MOVE / shift off-center / penetrate the clip base AT THE PIN — DIAGNOSED (clip_diag_69)
    as a RENDER artifact, NOT physics: the physics is clean (clip-region cable z=809.0-809.4, x centered 300.3, pin
    move=0.0mm). Root: EV.drive renders the cable from `solver.mj_data.qpos` (engagement_video:102), but the pin only
    froze the Newton `st.joint_q` -> the render showed solver.mj_data's un-frozen within-frame state. FIX: freeze
    solver.mj_data.qpos[cable]+qvel=0+mj_forward in the pin too (render source now matches the frozen physics).
(B) too few frames (9) — FIX: dense capture during every motion (~35 frames).
R-S7.1.1 B->A DROP-IN (derived from _70 by %4 2026-06-21): now with the REAL collidable clip (CLIP_COLLISION=1,
harness test:1006) the ko lower claw (18mm) is WIDER than the 15mm groove -> it CANNOT descend into the groove
(geometric: clip top=830 / seat=809) -> so we DROP-IN: grasp+lift -> descend ABOVE the clip (cable ~842, claws
clear 830) -> UNCLAMP (release) -> cable free-falls into the COLLIDABLE groove (real floor catches 809) -> PIN
(Y-fixation; the real floor holds vertical; authorized clip-only trick log.md:6534) -> ascend.
A/B by PIN flag (argv1 1=pin default / 0=no-pin): with REAL collision the floor holds vertical either way; the pin
adds Y-fix -> tests whether the real-collision floor ALONE retains, vs needs the pin.
⚠ CAVEATS: pin freezes the WHOLE cable (non-conservative pseudo-fix, GROVE §2.2); the DROP-IN dynamics (bounce/miss
the 15mm groove) are UNTESTED (feas_71 only proved settling from REST); CPU/scratch/ko un-banked; GPU UNVERIFIED.
Human visual = ground truth.

Run: MUJOCO_GL=osmesa CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python -u \
  ../../eval_runs/troot_optE_rs71_kinematic_retention_20260616/r_s71_clip_insert_pin_70.py [PIN=1|0]
"""
import os
import sys
import time

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("NEWTON_DEVICE", "cpu")
os.environ.setdefault("MUJOCO_GL", "osmesa")
os.environ.setdefault("CLIP_COLLISION", "1")             # R-S7.1.1 B->A: REAL collidable clip (harness test:1006)
os.environ.setdefault("CLIP_X", "0.40"); os.environ.setdefault("CLIP_Y", "0.075")  # FC-0: REAL clip C2 = CLIP_POSITIONS[1] (0.40,+0.075). X=0.40 OFF the void X[0.234,0.366] = solid table; grasp_y=0.075 (off-center, smoke-verified). Odd clips C1/C3/C5@X=0.35 are over-void = separate later sub-problem.

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
for p in (_HERE, "/home/rlrk/IsaacLab/thread_isaac_lab/scripts", "/home/rlrk/IsaacLab/thread_isaac_lab/configs"):
    if p not in sys.path:
        sys.path.insert(0, p)
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mujoco  # noqa: E402
import r_s71_engagement_video_full as EV  # noqa: E402
import r_s71_dualarm_slot_13 as D13  # noqa: E402
import r_s71_deepseat_verify_05 as V5  # noqa: E402

EP, T, C = EV.EP, EV.T, EV.C
GHS = float(C.GRIP_HALF_SPAN); GX = D13.GX; ZE = EP.Z_ENGAGE
CX = float(os.environ["CLIP_X"]); CY = float(os.environ["CLIP_Y"])  # clip XY — SEPARATED from grasp GX (over the void)
SEAT_Z = float(C.GROOVE_CENTER_Z); TABLE_H = float(C.TABLE_HEIGHT)
RAD_FULL = D13.RAD_FULL; RAD_OPEN = 0.0
BOX = int(mujoco.mjtGeom.mjGEOM_BOX); CAP = int(mujoco.mjtGeom.mjGEOM_CAPSULE)
ARM_Q = 2 * T.JOINTS_PER_ARM
PIN_ON = bool(int(sys.argv[1])) if len(sys.argv) > 1 else True
TAG = "pin" if PIN_ON else "nopin"
FRAMES = os.path.join(_HERE, f"_fc0_c2_smoke_{TAG}_frames")
MP4 = os.path.join(_HERE, f"r_fc0_c2_smoke_{TAG}.mp4")
T.ROBOTIQ_STRIPPED_XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml"  # FC-0: COMMITTED ko asset (swap 85315bbec6; CC3 verified geom+model identical to scratch)

CLIP_PARTS = [(0, 0, 0.0025, 0.020, 0.015, 0.0025), (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
              (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075), (-0.013, 0, 0.025, 0.002, 0.015, 0.005),
              (+0.013, 0, 0.025, 0.002, 0.015, 0.005)]

_PIN = {"active": False, "jq": None, "mjq": None}
_ops = T.physics_step


def _pp(model, state, solver, contacts, si):
    st = _ops(model, state, solver, contacts, si)
    if _PIN["active"]:
        jq = st.joint_q.numpy(); jq[ARM_Q:] = _PIN["jq"]; st.joint_q.assign(jq)
        qd = st.joint_qd.numpy(); qd[ARM_Q:] = 0.0; st.joint_qd.assign(qd)
        md = solver.mj_data                                   # RENDER source (EV.drive:102) — freeze it too
        md.qpos[ARM_Q:] = _PIN["mjq"]; md.qvel[ARM_Q:] = 0.0
        mujoco.mj_forward(solver.mj_model, md)
    return st


T.physics_step = _pp


def build_render_clip(solver, clip_xy):
    mph = solver.mj_model
    scene = mujoco.MjSpec(); wb = scene.worldbody
    wb.add_geom(type=int(mujoco.mjtGeom.mjGEOM_PLANE), size=[3.0, 3.0, 0.1], rgba=[0.26, 0.28, 0.32, 1.0])
    for gi in range(int(mph.ngeom)):
        nm = (mujoco.mj_id2name(mph, mujoco.mjtObj.mjOBJ_GEOM, gi) or "").lower()
        if int(mph.geom_type[gi]) == BOX and "pad" not in nm:
            wb.add_geom(type=BOX, pos=list(mph.geom_pos[gi]), quat=list(mph.geom_quat[gi]),
                        size=list(mph.geom_size[gi]), rgba=[0.80, 0.73, 0.60, 1.0])
    cx, cy = float(clip_xy[0]), float(clip_xy[1])
    # base OPAQUE (so the cable clearly rests ON it), walls/edges SEMI-TRANSPARENT (so the cable in the groove shows)
    clip_alpha = [1.0, 0.40, 0.40, 0.35, 0.35]
    for (dx, dy, dz, hx, hy, hz), a in zip(CLIP_PARTS, clip_alpha):
        wb.add_geom(type=BOX, pos=[cx + dx, cy + dy, TABLE_H + dz], size=[hx, hy, hz], rgba=[0.18, 0.62, 0.36, a])
    for pref, base in [("L_", C.ROBOT_LEFT_BASE), ("R_", C.ROBOT_RIGHT_BASE)]:
        s = wb.add_site(pos=[float(base[0]), float(base[1]), float(base[2])])
        scene.attach(EV.one_arm_spec(), prefix=pref, site=s)
    cgs = [gi for gi in range(int(mph.ngeom)) if int(mph.geom_type[gi]) == CAP]
    for i, gi in enumerate(cgs):
        b = wb.add_body(mocap=True, name=f"cab_{i}"); sz = mph.geom_size[gi]
        b.add_geom(type=CAP, size=[float(sz[0]), float(sz[1]), 0.0], rgba=[0.95, 0.55, 0.18, 1.0])
    pgs = [gi for gi in range(int(mph.ngeom)) if int(mph.geom_type[gi]) == BOX
           and "pad" in (mujoco.mj_id2name(mph, mujoco.mjtObj.mjOBJ_GEOM, gi) or "").lower()]
    for i, gi in enumerate(pgs):
        nm = (mujoco.mj_id2name(mph, mujoco.mjtObj.mjOBJ_GEOM, gi) or "").lower()
        col = [0.16, 0.40, 0.95, 1.0] if ("_f2" in nm or "lip2" in nm) else (
            [0.90, 0.22, 0.22, 1.0] if "_f1" in nm else [0.82, 0.82, 0.85, 0.45])
        b = wb.add_body(mocap=True, name=f"vgbox_{i}"); sz = mph.geom_size[gi]
        b.add_geom(type=BOX, size=[float(sz[0]), float(sz[1]), float(sz[2])], rgba=col)
    m = scene.compile()
    GRIP = ("follower", "spring_link", "_pad", "base_mount", "coupler", "driver", "knuckle", "2f85", "_rg")
    for gi in range(int(m.ngeom)):
        bn = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[gi])) or "").lower()
        if bn.startswith("vgbox") or "cab_" in bn:
            continue
        if any(k in bn for k in GRIP):
            rgba = list(m.geom_rgba[gi]); rgba[3] = 0.11; m.geom_rgba[gi] = rgba
    qmap = []
    for ai, pref in enumerate(["L_", "R_"]):
        for k, name in enumerate(EV.ARM14):
            jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, pref + name)
            qmap.append((int(m.jnt_qposadr[jid]), ai * 14 + k))
    cab_map = [(int(m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"cab_{i}")]), gi) for i, gi in enumerate(cgs)]
    pad_map = [(int(m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"vgbox_{i}")]), gi) for i, gi in enumerate(pgs)]
    m.vis.headlight.ambient[:] = [0.55, 0.55, 0.55]; m.vis.headlight.diffuse[:] = [0.6, 0.6, 0.6]
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), EV.HI); m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), EV.WI)
    return m, qmap, cab_map, pad_map


def cable_seat_z(st, cb):
    b, _ = EP.gripped_seg(st, cb, 0.0)
    return float(st.body_q.numpy()[b][2]) * 1e3, b


def main():
    t0 = time.time()
    model, solver, contacts, si, fks, fkm, drivers, seed, st = V5._seed_scene(grasp_y=0.075)  # FC-0: C2 grasp_y (off-center +0.075; void re-centers on grasp_y -> clip X=0.40 stays off void X-band)
    control = si["vbd_control"]; cb = si["cable_bodies"]
    for _ in range(150):
        st = T.physics_step(model, st, solver, contacts, si)
    c0, _ = cable_seat_z(st, cb)
    print(f"[CFG] PIN={PIN_ON} GX={GX:.3f} SEAT_Z={SEAT_Z:.3f} rest={c0:.1f} table={TABLE_H*1e3:.0f}", flush=True)
    z_grasp = ZE + 0.008; z_high = z_grasp + 0.10; z_lift = z_grasp + 0.05
    mr, qmap, cab_map, pad_map = build_render_clip(solver, (CX, CY))
    dr = mujoco.MjData(mr); dd2 = mujoco.MjData(solver.mj_model)
    renderer = mujoco.Renderer(mr, height=EV.HI, width=EV.WI)
    idx = [0]; traj = []
    mph, mphd = solver.mj_model, solver.mj_data
    st_box = [st]; ws = [seed]

    def cams():
        cS = mujoco.MjvCamera(); cS.type = mujoco.mjtCamera.mjCAMERA_FREE
        cS.lookat[:] = [CX, CY, 0.812]; cS.distance = 0.42; cS.azimuth = 92; cS.elevation = -7
        cC = mujoco.MjvCamera(); cC.type = mujoco.mjtCamera.mjCAMERA_FREE
        cC.lookat[:] = [CX, CY, 0.809]; cC.distance = 0.12; cC.azimuth = 145; cC.elevation = -3
        cD = mujoco.MjvCamera(); cD.type = mujoco.mjtCamera.mjCAMERA_FREE
        cD.lookat[:] = [CX, CY, 0.84]; cD.distance = 0.55; cD.azimuth = 220; cD.elevation = -24
        return [("SIDE (az92 low): cable z vs clip groove (green) + table", cS),
                ("CLIP CLOSE-UP: cable seated in groove (809) / fallen (804)?", cC),
                ("3/4 overview", cD)]

    def cap(phase, note=""):
        EV.drive(mr, dr, qmap, cab_map, st_box[0], solver, dd2)
        mujoco.mj_forward(mph, mphd)
        for mocap_id, gi in pad_map:
            dr.mocap_pos[mocap_id] = mphd.geom_xpos[gi]
            q = np.zeros(4); mujoco.mju_mat2Quat(q, np.asarray(mphd.geom_xmat[gi]).flatten()); dr.mocap_quat[mocap_id] = q
        mujoco.mj_forward(mr, dr)
        cz, _ = cable_seat_z(st_box[0], cb)
        traj.append((phase, cz))
        imgs = []; cs = cams()
        for _nm, cam in cs:
            renderer.update_scene(dr, camera=cam); imgs.append(renderer.render().copy())
        fig, axes = plt.subplots(1, 3, figsize=(17.4, 5.2))
        for ax, im, (nm, _c) in zip(axes, imgs, cs):
            ax.imshow(im); ax.axis("off"); ax.set_title(nm, fontsize=7.4, color="0.3")
        fig.suptitle(f"R-S7.1 CLIP INSERT + PIN [{TAG.upper()}] — {phase}\n"
                     f"cable z = {cz and round(cz)}mm (clip seat 809; table-rest {c0:.0f}) | "
                     f"PIN={'ON' if _PIN['active'] else 'OFF'} | {note}", fontsize=9.0)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.85, bottom=0.01, wspace=0.02)
        fig.savefig(os.path.join(FRAMES, f"f{idx[0]:05d}.png"), dpi=98); plt.close(fig)
        idx[0] += 1

    def move(tL, tR, label, conv=3.0, sf=0.3):
        s2, _ = T.ik_move_both(model, st_box[0], si, solver, contacts, tL, tR,
                               label=label, converge_mm=conv, speed_factor=sf, warmstart_jq=ws[0])
        st_box[0] = s2; ws[0] = fks.joint_q.numpy().copy()

    def settle_cap(nsteps, nchunks, phase, note=""):
        per = max(nsteps // nchunks, 1)
        for _c in range(nchunks):
            for _ in range(per):
                st_box[0] = T.physics_step(model, st_box[0], solver, contacts, si)
            cap(phase, note=note)

    os.makedirs(FRAMES, exist_ok=True)
    for old in os.listdir(FRAMES):
        if old.endswith(".png"):
            os.remove(os.path.join(FRAMES, old))

    # 1) PROVEN centered grasp + lift (dense)
    move((GX, CY - GHS, z_high), (GX, CY + GHS, z_high), "AP", 8.0, 0.2)
    cap("1) approach high")
    for k in range(1, 9):
        z = z_high + (z_grasp - z_high) * k / 8
        move((GX, CY - GHS, z), (GX, CY + GHS, z), f"DZ{k}", 2.5, 0.25)
        if k % 2 == 0:
            cap(f"1) descend {k}/8")
    T._set_gripper_target(control, drivers, RAD_FULL)
    settle_cap(130, 4, "1) closing")
    cz_g, _ = cable_seat_z(st_box[0], cb)
    posR = T.get_ee_positions(st_box[0], si)[1]
    ee_off = float(posR[2]) - (cz_g / 1e3)
    for k in range(1, 13):
        zl = z_grasp + 0.05 * k / 12
        move((GX, CY - GHS, zl), (GX, CY + GHS, zl), f"LIFT{k}", 3.0, 0.3)
        if k % 2 == 0:
            cap(f"1) lift {k}/12")

    # 1.5) ROUTE the grasped+lifted cable from the grasp X (over the void) to the CLIP X (on solid table, SEPARATE
    #      from the grasp slot — human 2026-06-21). Symmetric X move (both arms) -> the grasp stayed clean/vertical.
    for k in range(1, 7):
        xk = GX + (CX - GX) * k / 6
        move((xk, CY - GHS, z_lift), (xk, CY + GHS, z_lift), f"ROUTE{k}", 3.0, 0.3)
        if k % 2 == 0:
            cap(f"1.5) route GX->clipX {k}/6", note=f"X={xk:.3f}")

    # 2) LOWER the grasped cable INTO the clip mouth. v1 (cable~842, claws above clip top 830) FAILED — the cable
    #    rested ON the clip top (834), never threaded the 25mm down into the 809 groove. v2: the ko bottom claw (18mm)
    #    fits the 22mm edge-mouth but stops at the 15mm wall top (~820); lower the claw to the wall top so the cable
    #    (~claw+7 ~= 827) is INSIDE the mouth, then UNCLAMP -> the cable drops the last ~18mm into the 809 channel.
    release_ee_z = float(os.environ.get("REL_CABLE_Z", "0.820")) + ee_off
    for k in range(1, 9):
        zk = z_lift + (release_ee_z - z_lift) * k / 8
        move((CX, CY - GHS, zk), (CX, CY + GHS, zk), f"ABOVE{k}", 2.5, 0.25)
        if k % 2 == 0:
            cap(f"2) descend-above-clip {k}/8")
    settle_cap(40, 2, "2) above clip (pre-release)", note="cable above groove; ko claws clear clip top 830")

    # 2.5) DROP-IN: UNCLAMP above the clip -> cable free-falls into the COLLIDABLE groove (real floor catches 809)
    T._set_gripper_target(control, drivers, RAD_OPEN)
    settle_cap(150, 5, "2.5) DROP-IN (released above; cable falls into groove)",
               note="real-collision floor catches the cable")
    cz_seat, _ = cable_seat_z(st_box[0], cb)
    seated = abs(cz_seat - SEAT_Z * 1e3) < 4.0
    cap("2.5) DROPPED into clip groove", note=f"cable={cz_seat and round(cz_seat)} target=809 SEATED={seated}")

    # 3) FIRE PIN on the FLOOR-SEATED cable (Y-fixation; the real floor holds vertical). Authorized clip-only (log.md:6534).
    # CC5 fix (FC-0): gate the pin on `seated` so a missed/bounced drop-in is NOT frozen + falsely reported held=TRUE.
    if PIN_ON and seated:
        _PIN["jq"] = st_box[0].joint_q.numpy()[ARM_Q:].copy()
        _PIN["mjq"] = solver.mj_data.qpos[ARM_Q:].copy()
        _PIN["active"] = True
        settle_cap(30, 2, "3) PIN fired (Y-fix; floor holds vertical)", note="cable frozen at floor seat (render+physics)")
    else:
        cap("3) NO PIN (control) — real-collision floor only", note="floor holds vertical; Y/perturbation free")

    # 4) settle with the gripper OPEN (already unclamped in 2.5) — confirm the released cable stays seated
    settle_cap(60, 2, "4) released (gripper open)", note=("pin holds" if PIN_ON else "real floor holds vertical?"))
    cz_unc, _ = cable_seat_z(st_box[0], cb)

    # 5) ASCEND both (dense) — gripper retracts above the clip; the cable must STAY in the groove
    for k in range(1, 7):
        zk = release_ee_z + 0.02 * k
        move((CX, CY - GHS, zk), (CX, CY + GHS, zk), f"UP{k}", 4.0, 0.3)
        cz_up, _ = cable_seat_z(st_box[0], cb)
        cap(f"5) ascend {k}/6", note=f"cable={cz_up and round(cz_up)}")
    cz_final, _ = cable_seat_z(st_box[0], cb)

    print(f"\n=== CLIP INSERT + PIN [{TAG}] (cable z, mm) ===", flush=True)
    for ph, cz in traj:
        print(f"  {ph[:48]:48s} cable={cz and round(cz)}", flush=True)
    print(f"\n--- JUDGMENT [{TAG}] --- rest={c0:.0f} SEAT={cz_seat and round(cz_seat)}(t809,SEATED={seated}) "
          f"UNCLAMP={cz_unc and round(cz_unc)} ASCEND={cz_final and round(cz_final)}", flush=True)
    held = abs(cz_final - SEAT_Z * 1e3) < 8.0; fell = cz_final < (TABLE_H * 1e3 + 7.0)
    if PIN_ON:
        print(f"  >>> PIN: retained_at_seat={held} (expect TRUE)  [frames={idx[0]}]", flush=True)
    else:
        print(f"  >>> NO-PIN control: fell_to_table={fell} ({cz_final and round(cz_final)})  [frames={idx[0]}]", flush=True)

    import subprocess
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "6", "-i",
                    os.path.join(FRAMES, "f%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    "-pix_fmt", "yuv420p", MP4], check=True)
    subprocess.run(["cp", MP4, os.path.expanduser(f"~/Downloads/r_fc0_c2_smoke_{TAG}.mp4")], check=False)
    print(f"\n[CLIP DROP-IN {TAG}] frames={idx[0]} -> ~/Downloads/r_s71_clip_dropin72_{TAG}.mp4 ({time.time()-t0:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
