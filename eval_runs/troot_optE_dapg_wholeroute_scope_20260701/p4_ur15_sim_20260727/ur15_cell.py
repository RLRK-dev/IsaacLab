#!/usr/bin/env python3
"""Build the UR15 Y-yoke cell with a table, two clips and a cable, and let it settle.

Cable: a chain of capsule links joined by two hinges each (bend in both directions, no twist).
Clips: a groove made of two walls and a floor, open at the top, so a cable can be pressed in.
Rs allowed the clip layout and the clip/cable structure to change, so both are built to suit the
new arm geometry rather than copied from the old cell. Nothing here is kinematic: the cable is
free, and the arms are driven by their position servos.
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
GRIP_XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"

SHOULDER_HEIGHT = 0.37 + 0.58 * 2.0
YOKE_SPREAD = 0.22
TILT = math.pi / 2.0 - math.radians(45.0)
ARMATURE, DAMP = 0.1, 1.0
KP_ARM, KP_WRI, KVR = 10000.0, 1200.0, 0.06
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
EFFORT = np.array([433.0, 433.0, 204.0, 70.0, 70.0, 70.0])
SIDES = {"L": -1.0, "R": +1.0}

# --- cell layout (chosen for the UR15 reach measured earlier: x in +/-[0.3, 1.4] at z 0.7-1.1) ---
TABLE_TOP = 0.80
TABLE_HX, TABLE_HY = 0.95, 0.30
CABLE_N = 40
CABLE_SEG = 0.030
CABLE_R = 0.005
CABLE_Y = 0.45
CABLE_Z0 = TABLE_TOP + 0.05
CLIP_C1 = (-0.55, CABLE_Y)  # seat first
CLIP_C2 = (+0.55, CABLE_Y)  # guide toward second
GROOVE_W = 0.016
GROOVE_D = 0.030
CLIP_H = 0.070


def arm_spec():
    x = (S / "ur15_base.xml").read_text()
    for j in J6:
        x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)
    p = S / "_arm_only.xml"
    p.write_text(x)
    return mujoco.MjSpec.from_file(str(p))


def clip_xml(name, cx, cy):
    """A groove: two walls and a floor, open at the top."""
    zc = TABLE_TOP
    half = GROOVE_W / 2.0
    return f"""
    <body name="{name}" pos="{cx} {cy} {zc}">
      <geom name="{name}_base" type="box" size="0.030 0.022 0.006" pos="0 0 0.006" material="clip"/>
      <geom name="{name}_wl" type="box" size="0.006 0.022 {CLIP_H/2:.4f}" pos="{-(half+0.006):.4f} 0 {0.012+CLIP_H/2:.4f}" material="clip"/>
      <geom name="{name}_wr" type="box" size="0.006 0.022 {CLIP_H/2:.4f}" pos="{ (half+0.006):.4f} 0 {0.012+CLIP_H/2:.4f}" material="clip"/>
      <geom name="{name}_floor" type="box" size="{half:.4f} 0.022 0.006" pos="0 0 0.018" material="clipf"/>
    </body>"""


def cable_xml():
    """Chain of capsules; two hinges per link so it bends in both directions but does not twist."""
    x0 = -CABLE_SEG * CABLE_N / 2.0
    s = f'\n    <body name="cab0" pos="{x0:.4f} {CABLE_Y} {CABLE_Z0:.4f}">\n'
    s += '      <freejoint name="cable_free"/>\n'
    s += f'      <geom name="cab0_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="0.004" material="cable" friction="0.9 0.02 0.002"/>\n'
    depth = 1
    for i in range(1, CABLE_N):
        s += "  " * depth + f'      <body name="cab{i}" pos="{CABLE_SEG:.4f} 0 0">\n'
        s += "  " * depth + f'        <joint name="cab{i}_y" type="hinge" axis="0 1 0" range="-1.2 1.2" damping="0.004" stiffness="0.02"/>\n'
        s += "  " * depth + f'        <joint name="cab{i}_z" type="hinge" axis="0 0 1" range="-1.2 1.2" damping="0.004" stiffness="0.02"/>\n'
        s += "  " * depth + f'        <geom name="cab{i}_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="0.004" material="cable" friction="0.9 0.02 0.002"/>\n'
        depth += 1
    for i in range(CABLE_N - 1, 0, -1):
        depth -= 1
        s += "  " * depth + "      </body>\n"
    s += "    </body>\n"
    return s


world = f"""<mujoco model="ur15_cell">
  <compiler angle="radian"/>
  <option timestep="0.002" integrator="implicitfast" cone="elliptic"/>
  <visual>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.75 0.75 0.75" specular="0.2 0.2 0.2"/>
    <global offwidth="1600" offheight="900"/>
    <map znear="0.02"/>
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
    {clip_xml("C1", *CLIP_C1)}
    {clip_xml("C2", *CLIP_C2)}
    {cable_xml()}
  </worldbody>
</mujoco>
"""
(S / "_cell_world.xml").write_text(world)
cell = mujoco.MjSpec.from_file(str(S / "_cell_world.xml"))
column = cell.body("column")

for tag, sign in SIDES.items():
    q = Rotation.from_euler("xyz", [0.0, sign * TILT, 0.0]).as_quat()
    f = column.add_frame(pos=[sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT], quat=[float(q[3]), float(q[0]), float(q[1]), float(q[2])])
    _aspec = arm_spec()
    f.attach_body(_aspec.bodies[1], f"{tag}_", "")
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
print(f"[cell] nq={m.nq} nu={m.nu} nbody={m.nbody} ngeom={m.ngeom}")
print(f"[cell] cable links={CABLE_N} length={CABLE_N*CABLE_SEG:.3f} m  clips C1={CLIP_C1} C2={CLIP_C2} table_top={TABLE_TOP}")

# park the arms clear of the table, then let the cable settle
HOME = np.array([0.0, -1.9, 1.6, -1.3, -1.57, 0.0])
AN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
for t in SIDES:
    for k, j in enumerate(J6):
        d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")]] = HOME[k]
        d.ctrl[AN.index(f"{t}_{j}_act")] = HOME[k]
mujoco.mj_forward(m, d)
for _ in range(3000):
    mujoco.mj_step(m, d)

cb = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"cab{i}") for i in range(CABLE_N)]
P = np.array([d.xpos[b] for b in cb])
print(f"[cell] settled cable: x[{P[:,0].min():.3f},{P[:,0].max():.3f}] y[{P[:,1].min():.3f},{P[:,1].max():.3f}] z[{P[:,2].min():.3f},{P[:,2].max():.3f}]")
print(f"[cell] cable rests {P[:,2].mean()-TABLE_TOP:+.4f} m relative to the table top; contacts={d.ncon}")

renderer = mujoco.Renderer(m, height=900, width=1600)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.0, CABLE_Y, TABLE_TOP + 0.05]
cam.distance = 1.9
cam.elevation = -22
cam.azimuth = 108
renderer.update_scene(d, camera=cam)
import imageio.v2 as imageio  # noqa: E402

imageio.imwrite(str(S / "cell_settled.png"), renderer.render())
print("[cell] wrote cell_settled.png")
