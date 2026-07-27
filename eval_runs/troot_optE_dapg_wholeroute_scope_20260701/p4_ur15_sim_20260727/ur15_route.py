"""⚠ RETIRED RECORD -- this file is what ran on 2026-07-27, not what runs now.

Its cell constants are the ones that were in force when it ran, and several are known wrong:
the cable is 32 links of 30 mm at mass="0.004" and stiffness="0.12" (3.56x too heavy and 64%
too soft once the link is the SSOT's 15 mm), and the clip is a 78 mm block with 64 mm of solid
under a notch instead of the env's 30 mm V-groove.

⛔ Do not read constants out of this file.  The live driver is `ur15_steps_wired.py`, and every
cell constant it uses comes from `ur15_cell_spec.py`, which imports the repo SSOT.

Kept because it is the record of a run Rs judged; annotated because a copy left next to a fix
gets opened later (p5 ruling, 2026-07-27).  Nothing below is edited.
"""

#!/usr/bin/env python3
"""Reproduce the reference basic motion on the UR15 Y-yoke cell:

    seat C1 (full clamp) -> L half-unclamp -> guide toward C2

Everything is physics: the arms are position servos fed by per-arm IK, the fingers are the
gripper's own actuator, and the cable is a free chain. The ONLY kinematic element is the clip
retention (Rs: "kinematic はクリップのケーブル固定のみ") -- a connect equality between the clip and
the single cable link that is seated, pre-declared inactive and switched on only after the seat is
verified geometrically. Physical-validity judgment = Rs.
"""

from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402

S = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/scratchpad")
sys.path.insert(0, str(S))
GRIP_XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/rlrk/Downloads/ur15_route.mp4")

SHOULDER_HEIGHT = 0.37 + 0.58 * 2.0
YOKE_SPREAD = 0.22
TILT = math.pi / 2.0 - math.radians(45.0)
ARMATURE, DAMP = 0.1, 1.0
KP_ARM, KP_WRI, KVR = 10000.0, 1200.0, 0.06
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
EFFORT = np.array([433.0, 433.0, 204.0, 70.0, 70.0, 70.0])
SIDES = {"L": -1.0, "R": +1.0}

TABLE_TOP = 0.80
TABLE_HX, TABLE_HY = 0.95, 0.30
CABLE_N, CABLE_SEG, CABLE_R = 40, 0.030, 0.005
CABLE_Y = 0.45
CABLE_Z0 = TABLE_TOP + 0.05
C1X, C2X = -0.55, +0.55
GROOVE_W, CLIP_H = 0.016, 0.070


def arm_spec():
    x = (S / "ur15_base.xml").read_text()
    for j in J6:
        x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)
    p = S / "_arm_only.xml"
    p.write_text(x)
    return mujoco.MjSpec.from_file(str(p))


def clip_xml(name, cx):
    half = GROOVE_W / 2.0
    return f"""
    <body name="{name}" pos="{cx} {CABLE_Y} {TABLE_TOP}">
      <geom name="{name}_base" type="box" size="0.030 0.022 0.006" pos="0 0 0.006" material="clip"/>
      <geom name="{name}_wl" type="box" size="0.006 0.022 {CLIP_H/2:.4f}" pos="{-(half+0.006):.4f} 0 {0.012+CLIP_H/2:.4f}" material="clip"/>
      <geom name="{name}_wr" type="box" size="0.006 0.022 {CLIP_H/2:.4f}" pos="{ (half+0.006):.4f} 0 {0.012+CLIP_H/2:.4f}" material="clip"/>
      <geom name="{name}_floor" type="box" size="{half:.4f} 0.022 0.006" pos="0 0 0.018" material="clipf"/>
      <site name="{name}_seat" pos="0 0 0.030" size="0.004" rgba="1 0.6 0 0.35"/>
    </body>"""


def cable_xml():
    x0 = -CABLE_SEG * CABLE_N / 2.0
    s = f'\n    <body name="cab0" pos="{x0:.4f} {CABLE_Y} {CABLE_Z0:.4f}">\n      <freejoint name="cable_free"/>\n'
    s += f'      <geom name="cab0_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="0.004" material="cable" friction="1.1 0.03 0.002" condim="6"/>\n'
    dep = 1
    for i in range(1, CABLE_N):
        pad = "  " * dep
        s += pad + f'      <body name="cab{i}" pos="{CABLE_SEG:.4f} 0 0">\n'
        s += pad + f'        <joint name="cab{i}_y" type="hinge" axis="0 1 0" range="-1.2 1.2" damping="0.004" stiffness="0.02"/>\n'
        s += pad + f'        <joint name="cab{i}_z" type="hinge" axis="0 0 1" range="-1.2 1.2" damping="0.004" stiffness="0.02"/>\n'
        s += pad + f'        <geom name="cab{i}_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="0.004" material="cable" friction="1.1 0.03 0.002" condim="6"/>\n'
        dep += 1
    for i in range(CABLE_N - 1, 0, -1):
        dep -= 1
        s += "  " * dep + "      </body>\n"
    return s + "    </body>\n"


SEAT_LINK = int(round((C1X - (-CABLE_SEG * CABLE_N / 2.0)) / CABLE_SEG))  # link whose origin sits at C1
world = f"""<mujoco model="ur15_route">
  <compiler angle="radian"/>
  <option timestep="0.002" integrator="implicitfast" cone="elliptic"/>
  <visual>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.75 0.75 0.75" specular="0.2 0.2 0.2"/>
    <global offwidth="1600" offheight="900"/><map znear="0.02"/>
  </visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.19 0.21 0.25" rgb2="0.25 0.27 0.32" width="512" height="512"/>
    <material name="gridmat" texture="grid" texrepeat="12 12" reflectance="0.05"/>
    <material name="col" rgba="0.86 0.86 0.87 1"/>
    <material name="table" rgba="0.55 0.57 0.62 1"/>
    <material name="clip" rgba="0.30 0.78 0.42 1"/>
    <material name="clipf" rgba="0.20 0.62 0.32 1"/>
    <material name="cable" rgba="0.93 0.93 0.95 1"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="6 6 0.1" material="gridmat" pos="0 0 0" contype="0" conaffinity="0"/>
    <body name="column" pos="0 0 0">
      <geom name="stem" type="cylinder" size="0.102 {SHOULDER_HEIGHT/2:.4f}" pos="0 0 {SHOULDER_HEIGHT/2:.4f}" material="col" contype="0" conaffinity="0"/>
      <geom name="foot" type="cylinder" size="0.215 0.03" pos="0 0 0.03" material="col" contype="0" conaffinity="0"/>
    </body>
    <body name="table" pos="0 {CABLE_Y} 0">
      <geom name="table_top" type="box" size="{TABLE_HX} {TABLE_HY} 0.02" pos="0 0 {TABLE_TOP-0.02:.4f}" material="table"/>
    </body>
    {clip_xml("C1", C1X)}
    {clip_xml("C2", C2X)}
    {cable_xml()}
  </worldbody>
  <equality>
    <!-- clip retention: the ONE authorised kinematic element. Inactive until the seat is verified. -->
    <connect name="C1_pin" body1="C1" body2="cab{SEAT_LINK}" anchor="0 0 0.030" active="false"/>
  </equality>
</mujoco>
"""
(S / "_route_world.xml").write_text(world)
cell = mujoco.MjSpec.from_file(str(S / "_route_world.xml"))
column = cell.body("column")
for tag, sign in SIDES.items():
    q = Rotation.from_euler("xyz", [0.0, sign * TILT, 0.0]).as_quat()
    f = column.add_frame(pos=[sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT], quat=[float(q[3]), float(q[0]), float(q[1]), float(q[2])])
    _a = arm_spec()
    f.attach_body(_a.bodies[1], f"{tag}_", "")
    g = mujoco.MjSpec.from_file(GRIP_XML)
    Rt = Rotation.from_euler("xyz", [0, -np.pi / 2, -np.pi / 2]) * Rotation.from_euler("xyz", [np.pi / 2, 0, np.pi / 2])
    qt_ = Rt.as_quat()
    wf = cell.body(f"{tag}_wrist_3_link").add_frame(pos=[0, 0, 0], quat=[float(qt_[3]), float(qt_[0]), float(qt_[1]), float(qt_[2])])
    wf.attach_body(g.body("base_mount"), f"{tag}g_", "")

kps = np.array([KP_ARM] * 3 + [KP_WRI] * 3)
kvs = kps * KVR
for tag in SIDES:
    for i, j in enumerate(J6):
        a = cell.add_actuator()
        a.name, a.trntype, a.target = f"{tag}_{j}_act", mujoco.mjtTrn.mjTRN_JOINT, f"{tag}_{j}"
        a.gaintype, a.biastype = mujoco.mjtGain.mjGAIN_FIXED, mujoco.mjtBias.mjBIAS_AFFINE
        a.gainprm[0], a.biasprm[1], a.biasprm[2] = kps[i], -kps[i], -kvs[i]
        a.forcerange, a.ctrlrange, a.ctrllimited = [-EFFORT[i], EFFORT[i]], [-6.3, 6.3], 1

m = cell.compile()
d = mujoco.MjData(m)
AN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
AIDX = {t: [AN.index(f"{t}_{j}_act") for j in J6] for t in SIDES}
GIDX = {t: AN.index(f"{t}g_fingers_actuator") for t in SIDES}
QADR = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6] for t in SIDES}
VADR = {t: [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6] for t in SIDES}
PAD = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_{s}_pad") for s in ("left", "right")] for t in SIDES}
CAB = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"cab{i}") for i in range(CABLE_N)]
EQ_C1 = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, "C1_pin")
print(f"[route] nq={m.nq} nu={m.nu} nbody={m.nbody} ngeom={m.ngeom} eq={m.neq} seat_link=cab{SEAT_LINK}")


def pinch(t):
    return 0.5 * (np.array(d.xpos[PAD[t][0]]) + np.array(d.xpos[PAD[t][1]]))


def pinch_jac(t):
    Js = []
    for b in PAD[t]:
        jp = np.zeros((3, m.nv))
        mujoco.mj_jacBody(m, d, jp, None, b)
        Js.append(jp[:, VADR[t]])
    return 0.5 * (Js[0] + Js[1])


qt = {}


def ik(t, target, gain=0.35, lam=0.08, dq_max=0.012, lag=0.20):
    Jm = pinch_jac(t)
    e = target - pinch(t)
    dq = gain * (Jm.T @ np.linalg.solve(Jm @ Jm.T + lam**2 * np.eye(3), e))
    n = float(np.linalg.norm(dq))
    if n > dq_max:
        dq *= dq_max / n
    qn = np.array([d.qpos[a] for a in QADR[t]])
    qt[t] = np.clip(qt[t] + dq, qn - lag, qn + lag)
    return float(np.linalg.norm(e))


# seed both arms above their first grasp points
GRASP_L_X, GRASP_R_X = C1X - 0.16, C1X + 0.16
APPROACH_Z = TABLE_TOP + 0.22
seedwant = {"L": np.array([GRASP_L_X, CABLE_Y, APPROACH_Z]), "R": np.array([GRASP_R_X, CABLE_Y, APPROACH_Z])}
rng = np.random.default_rng(0)
lim = np.array([[-3.14, 3.14], [-3.05, -0.05], [-2.60, 2.60], [-3.14, 3.14], [-3.14, 3.14], [-3.14, 3.14]])
best = {t: (1e9, None) for t in SIDES}
for _ in range(40000):
    qq = rng.uniform(lim[:, 0], lim[:, 1])
    for t in SIDES:
        for k, a in enumerate(QADR[t]):
            d.qpos[a] = qq[k]
    mujoco.mj_forward(m, d)
    for t in SIDES:
        e = float(np.linalg.norm(pinch(t) - seedwant[t]))
        if e < best[t][0]:
            best[t] = (e, qq.copy())
for t in SIDES:
    print(f"[route] seed {t}: {best[t][0]*1000:.0f} mm")
    for k, a in enumerate(QADR[t]):
        d.qpos[a] = best[t][1][k]
    for k, i in enumerate(AIDX[t]):
        d.ctrl[i] = best[t][1][k]
    d.ctrl[GIDX[t]] = 0.0
d.qvel[:] = 0
mujoco.mj_forward(m, d)
qt = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}

CABLE_GRASP_Z = TABLE_TOP + 0.019
SEAT_Z = TABLE_TOP + 0.030
PHASES = [
    ("approach", 2.0, {"L": (GRASP_L_X, CABLE_Y, APPROACH_Z), "R": (GRASP_R_X, CABLE_Y, APPROACH_Z)}, (0, 0), False),
    ("descend", 2.2, {"L": (GRASP_L_X, CABLE_Y, CABLE_GRASP_Z), "R": (GRASP_R_X, CABLE_Y, CABLE_GRASP_Z)}, (0, 0), False),
    ("close", 1.4, {"L": (GRASP_L_X, CABLE_Y, CABLE_GRASP_Z), "R": (GRASP_R_X, CABLE_Y, CABLE_GRASP_Z)}, (255, 255), False),
    ("lift", 1.6, {"L": (GRASP_L_X, CABLE_Y, TABLE_TOP + 0.12), "R": (GRASP_R_X, CABLE_Y, TABLE_TOP + 0.12)}, (255, 255), False),
    ("over_C1", 2.0, {"L": (C1X - 0.12, CABLE_Y, TABLE_TOP + 0.12), "R": (C1X + 0.12, CABLE_Y, TABLE_TOP + 0.12)}, (255, 255), False),
    ("seat_C1", 2.4, {"L": (C1X - 0.12, CABLE_Y, SEAT_Z + 0.004), "R": (C1X + 0.12, CABLE_Y, SEAT_Z + 0.004)}, (255, 255), True),
    ("half_open_L", 1.6, {"L": (C1X - 0.12, CABLE_Y, SEAT_Z + 0.004), "R": (C1X + 0.12, CABLE_Y, SEAT_Z + 0.004)}, (110, 255), True),
    ("guide_C2a", 2.6, {"L": (C1X - 0.12, CABLE_Y, TABLE_TOP + 0.10), "R": (0.0, CABLE_Y, TABLE_TOP + 0.10)}, (110, 255), True),
    ("guide_C2b", 2.6, {"L": (C1X - 0.12, CABLE_Y, TABLE_TOP + 0.10), "R": (C2X, CABLE_Y, TABLE_TOP + 0.10)}, (110, 255), True),
    ("seat_C2", 2.2, {"L": (C1X - 0.12, CABLE_Y, TABLE_TOP + 0.10), "R": (C2X, CABLE_Y, SEAT_Z + 0.004)}, (110, 255), True),
]
FPS, W, H = 30, 1600, 900
renderer = mujoco.Renderer(m, height=H, width=W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.0, CABLE_Y, TABLE_TOP + 0.06]
cam.distance = 1.75
cam.elevation = -20
cam2 = mujoco.MjvCamera()
cam2.type = mujoco.mjtCamera.mjCAMERA_FREE
cam2.distance = 0.45
cam2.elevation = -14
cam2.azimuth = 95

frames = []
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
n = 0
pin_on_at = None
for name, secs, tgt, grip, want_pin in PHASES:
    steps = int(secs / m.opt.timestep)
    for t in SIDES:
        d.ctrl[GIDX[t]] = grip[0] if t == "L" else grip[1]
    for s in range(steps):
        if s % 5 == 0:
            for t in SIDES:
                ik(t, np.array(tgt[t]))
        for t in SIDES:
            for k, i in enumerate(AIDX[t]):
                d.ctrl[i] = qt[t][k]
        # clip retention: switch on only once the seated link is actually in the groove
        if want_pin and not d.eq_active[EQ_C1]:
            p = np.array(d.xpos[CAB[SEAT_LINK]])
            if abs(p[0] - C1X) < 0.020 and abs(p[2] - (TABLE_TOP + 0.030)) < 0.012:
                d.eq_active[EQ_C1] = 1
                pin_on_at = (name, float(n * m.opt.timestep))
                print(f"[route] clip retention ON at {name} t={n*m.opt.timestep:.2f}s  seat={np.round(p,4)}")
        mujoco.mj_step(m, d)
        n += 1
        if n % render_every == 0:
            cam.azimuth = 100 + 18.0 * np.sin(n * 0.0008)
            renderer.update_scene(d, camera=cam)
            a_img = renderer.render()
            cam2.lookat[:] = 0.5 * (pinch("L") + pinch("R"))
            renderer.update_scene(d, camera=cam2)
            frames.append(np.hstack([a_img, renderer.render()]))
    ps = np.array(d.xpos[CAB[SEAT_LINK]])
    print(f"[route] {name:12s} t={n*m.opt.timestep:5.1f}s  L_err={np.linalg.norm(pinch('L')-np.array(tgt['L']))*1000:6.1f}mm"
          f"  R_err={np.linalg.norm(pinch('R')-np.array(tgt['R']))*1000:6.1f}mm  seat_link_z={ps[2]-TABLE_TOP:+.4f}  pin={'ON' if d.eq_active[EQ_C1] else 'off'}")

print(f"[route] pin engaged: {pin_on_at}")
tip = np.array(d.xpos[CAB[-1]])
print(f"[route] cable end x={tip[0]:.3f}  seat link x={d.xpos[CAB[SEAT_LINK]][0]:.3f}")

import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=8, macro_block_size=None)
print(f"[route] wrote {OUT} frames={len(frames)} {OUT.stat().st_size} bytes")
