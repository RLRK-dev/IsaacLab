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
"""Drive the UR15 Y-yoke cell through STEP 1-18 of the canonical 43-step table.

Table = thread_isaac_lab/thread-vault/07-Design/RL-Routing-Design.md sec 2 at commit
59badc4b7a4dd7c6706c9a880d82a557fbb82c2b: Phase A initial grasp (STEP 1-5), Phase B C1 routing
(STEP 6-10), Phase C+D C2 routing (STEP 11-18).  The STEP sequence, the finger states per step and
the clip states per step are read off that table; the numeric layout is provisional for UR15 (Rs
allowed the clip layout to change) and p5 governs the final geometry.

Control: the arms are position servos only.  Nothing writes joint or body state into the live
MjData -- the IK seed search runs on a throwaway MjData, and the start pose is reached by the
servos physically moving there.  The fingers are the gripper's own tendon actuator.  The ONE
kinematic element is the clip retention, a connect equality that stays inactive until the seat is
verified geometrically.  Physical-validity judgment = Rs.
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
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/rlrk/Downloads/ur15_steps.mp4")

# --- yoke + servo constants (provisional; p11 court) ---
SHOULDER_HEIGHT = 0.37 + 0.58 * 2.0
YOKE_SPREAD, TILT = 0.40, math.pi / 2.0 - math.radians(20.0)  # measured: 0.22/45deg made the two arms interleave at an 88 mm span; 0.40/20deg clears the rest row and both clips
ARMATURE, DAMP = 0.1, 1.0
KP_ARM, KP_WRI, KVR = 10000.0, 1200.0, 0.06
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
EFFORT = np.array([433.0, 433.0, 204.0, 70.0, 70.0, 70.0])
SIDES = {"L": -1.0, "R": +1.0}

# --- cell layout: the table's clip row runs along X here, the rest row sits nearer the column ---
TABLE_TOP = 0.80
TABLE_HX, TABLE_HY = 0.70, 0.20
CABLE_N, CABLE_SEG, CABLE_R = 32, 0.030, 0.004  # task_config.py:137 CABLE_RADIUS = 0.004
                                                # (2f85_koshape.xml:9: the claws wrap the O8 cable)
REST_Y = 0.28  # S1-S3 equivalent: where the cable starts, OUTSIDE every clip
CLIP_Y_ODD, CLIP_Y_EVEN = 0.35, 0.40  # staggered, as C1/C3/C5 vs C2/C4 in the table
C1 = (0.150, CLIP_Y_ODD)   # table :1253 C1 = 0.35 / +0.150
C2 = (0.040, CLIP_Y_EVEN)  # table :1254 C2 = 0.40 / +0.075, widened for the 22 mm hand
REST_X = (-0.34, -0.14, 0.24)  # saddles kept clear of both 88 mm grasp spans
REST_TOP = TABLE_TOP + 0.150  # measured: at +0.060 the open fingers press into the table
GROOVE_W, CLIP_H = 0.016, 0.026
GRIP_HALF_SPAN = 0.044  # task_config.py:235 @ 843084ae5e47ddc9f17bfe33c2dbc3f46ea53562

# pinch-frame Z tiers.  The table's 1.12/1.07/1.05/1.02 are WRIST-FLANGE heights; pinch() below is
# the fingertip pinch point, so the tiers are re-expressed in the pinch frame (stated, not silent).
# task_config.py:320 EE_TO_PINCH_CLOSED = 0.2548428289592266 (wrist_3 -> pinch mid)
# task_config.py:321 EE_TO_PINCH_TIP_CLOSED = 0.27574726696    (wrist_3 -> ko f1ext claw TIP)
CLAW_OFFSET = 0.27574726696 - 0.2548428289592266  # 20.9 mm from the pinch to the claw tip

Z_HOME = TABLE_TOP + 0.20
Z_RISE_ROUTE = TABLE_TOP + 0.180
Z_RISE_REST = TABLE_TOP + 0.230
# Z_GRASP_REST / Y_GRASP_REST are MEASURED after the settle below, not assumed here.
CLIP_RISER = 0.040
Z_SEAT = TABLE_TOP + CLIP_RISER + 0.030 - CLAW_OFFSET  # groove seat, expressed at the pinch
                                                 # (the claw carrying the cable is 25.8 mm above it)

# finger commands (2F-85 tendon actuator, 0 open .. 255 closed) for the table's three states
CLAMP, HALF, OPEN = 255, 170, 0
# What actually holds the cable is the ko-shape claw pair, not the pads: at full clamp the pads
# stop 24.2 mm apart (cable is 10 mm) while the facing f2 claws sit 25.8 mm above the pinch with an
# 18.0 mm gap.  So the pinch must be driven BELOW the cable by that much, or the claws close on air.


def arm_spec():
    x = (S / "ur15_base.xml").read_text()
    for j in J6:
        x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)
    p = S / "_arm_only.xml"
    p.write_text(x)
    return mujoco.MjSpec.from_file(str(p))


def clip_xml(name, cx, cy):
    """Slot running along X so a cable lying along X can be pressed down into it."""
    h = GROOVE_W / 2.0
    return f"""
    <body name="{name}" pos="{cx} {cy} {TABLE_TOP + CLIP_RISER}">
      <geom name="{name}_riser" type="box" size="0.016 0.024 {CLIP_RISER/2:.4f}" pos="0 0 {-CLIP_RISER/2:.4f}" material="clipf"/>
      <geom name="{name}_base" type="box" size="0.016 0.024 0.006" pos="0 0 0.006" material="clip"/>
      <geom name="{name}_wa" type="box" size="0.016 0.006 {CLIP_H/2:.4f}" pos="0 {-(h+0.006):.4f} {0.012+CLIP_H/2:.4f}" material="clip"/>
      <geom name="{name}_wb" type="box" size="0.016 0.006 {CLIP_H/2:.4f}" pos="0 { (h+0.006):.4f} {0.012+CLIP_H/2:.4f}" material="clip"/>
      <geom name="{name}_floor" type="box" size="0.016 {h:.4f} 0.006" pos="0 0 0.018" material="clipf"/>
    </body>"""


def rest_xml(i, cx):
    """Saddle: a post with two lips so the cable is captured instead of rolling off."""
    h = REST_TOP - TABLE_TOP
    return f"""
    <body name="S{i}" pos="{cx} {REST_Y} {TABLE_TOP}">
      <geom name="S{i}_post" type="box" size="0.014 0.014 {h/2:.4f}" pos="0 0 {h/2:.4f}" material="rest"/>
      <geom name="S{i}_la" type="box" size="0.014 0.004 0.006" pos="0 -0.012 {h+0.006:.4f}" material="rest"/>
      <geom name="S{i}_lb" type="box" size="0.014 0.004 0.006" pos="0  0.012 {h+0.006:.4f}" material="rest"/>
    </body>"""


def cable_xml():
    x0 = -CABLE_SEG * CABLE_N / 2.0
    z0 = REST_TOP + CABLE_R
    s = f'\n    <body name="cab0" pos="{x0:.4f} {REST_Y} {z0:.4f}">\n      <freejoint name="cable_free"/>\n'
    s += f'      <geom name="cab0_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="0.004" material="cable" friction="1.1 0.03 0.002" condim="6"/>\n'
    dep = 1
    for i in range(1, CABLE_N):
        pad = "  " * dep
        s += pad + f'      <body name="cab{i}" pos="{CABLE_SEG:.4f} 0 0">\n'
        s += pad + f'        <joint name="cab{i}_y" type="hinge" axis="0 1 0" range="-1.2 1.2" damping="0.010" stiffness="0.12"/>\n'
        s += pad + f'        <joint name="cab{i}_z" type="hinge" axis="0 0 1" range="-1.2 1.2" damping="0.010" stiffness="0.12"/>\n'
        s += pad + f'        <geom name="cab{i}_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="0.004" material="cable" friction="1.1 0.03 0.002" condim="6"/>\n'
        dep += 1
    for i in range(CABLE_N - 1, 0, -1):
        dep -= 1
        s += "  " * dep + "      </body>\n"
    return s + "    </body>\n"


def link_at(x):
    return int(np.clip(round((x - (-CABLE_SEG * CABLE_N / 2.0)) / CABLE_SEG), 0, CABLE_N - 1))


SEAT1, SEAT2 = link_at(C1[0]), link_at(C2[0])
world = f"""<mujoco model="ur15_steps">
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
    <material name="rest" rgba="0.72 0.60 0.35 1"/>
    <material name="cable" rgba="0.95 0.95 0.97 1"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="6 6 0.1" material="gridmat" pos="0 0 0" contype="0" conaffinity="0"/>
    <body name="column" pos="0 0 0">
      <geom name="stem" type="cylinder" size="0.102 {SHOULDER_HEIGHT/2:.4f}" pos="0 0 {SHOULDER_HEIGHT/2:.4f}" material="col" contype="0" conaffinity="0"/>
      <geom name="foot" type="cylinder" size="0.215 0.03" pos="0 0 0.03" material="col" contype="0" conaffinity="0"/>
    </body>
    <body name="table" pos="0 {(REST_Y+CLIP_Y_EVEN)/2:.3f} 0">
      <geom name="table_top" type="box" size="{TABLE_HX} {TABLE_HY} 0.02" pos="0 0 {TABLE_TOP-0.02:.4f}" material="table"/>
    </body>
    {clip_xml("C1", *C1)}
    {clip_xml("C2", *C2)}
    {"".join(rest_xml(i + 1, x) for i, x in enumerate(REST_X))}
    {cable_xml()}
  </worldbody>
  <equality>
    <!-- clip retention: the ONE authorised kinematic element.  Both start inactive. -->
    <connect name="C1_pin" body1="C1" body2="cab{SEAT1}" anchor="0 0 0.030" active="false"/>
    <connect name="C2_pin" body1="C2" body2="cab{SEAT2}" anchor="0 0 0.030" active="false"/>
  </equality>
</mujoco>
"""
(S / "_steps_world.xml").write_text(world)
cell = mujoco.MjSpec.from_file(str(S / "_steps_world.xml"))
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
for tag in SIDES:
    for i, j in enumerate(J6):
        a = cell.add_actuator()
        a.name, a.trntype, a.target = f"{tag}_{j}_act", mujoco.mjtTrn.mjTRN_JOINT, f"{tag}_{j}"
        a.gaintype, a.biastype = mujoco.mjtGain.mjGAIN_FIXED, mujoco.mjtBias.mjBIAS_AFFINE
        a.gainprm[0], a.biasprm[1], a.biasprm[2] = kps[i], -kps[i], -(kps[i] * KVR)
        a.forcerange, a.ctrlrange, a.ctrllimited = [-EFFORT[i], EFFORT[i]], [-6.3, 6.3], 1

# Gravity compensation on the arm links, as the official UR MJCF does and as this project's
# PhysX config does (disable_gravity=True on the robot).  Without it the servos sit ~17 mm short
# of their commanded pose and the grippers close beside the cable instead of on it.
for _b in cell.bodies:
    if _b.name.startswith(("L_", "R_", "Lg_", "Rg_")):
        _b.gravcomp = 1.0

m = cell.compile()
d = mujoco.MjData(m)
AN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
AIDX = {t: [AN.index(f"{t}_{j}_act") for j in J6] for t in SIDES}
GIDX = {t: AN.index(f"{t}g_fingers_actuator") for t in SIDES}
QADR = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6] for t in SIDES}
VADR = {t: [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6] for t in SIDES}
PAD = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_{s}_pad") for s in ("left", "right")] for t in SIDES}
CAB = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"cab{i}") for i in range(CABLE_N)]
CABG = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"cab{i}_g") for i in range(CABLE_N)}
PADG = {t: {g for g in range(m.ngeom)
            if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").startswith(f"{t}g_")} for t in SIDES}
EQ = {"C1": mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, "C1_pin"),
      "C2": mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, "C2_pin")}
CLIPG = {c: {g for g in range(m.ngeom)
             if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").startswith(f"{c}_")} for c in ("C1", "C2")}
print(f"[steps] nq={m.nq} nu={m.nu} nbody={m.nbody} ngeom={m.ngeom} eq={m.neq}  seat links C1=cab{SEAT1} C2=cab{SEAT2}")

TOOLB = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_base") for t in SIDES}
GNAME = {g: (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f"g{g}") for g in range(m.ngeom)}


def _own_bodies(prefix):
    """Bodies belonging to one arm, by ancestry -- the URDF geoms are UNNAMED, so a name-prefix
    test silently matches nothing.  Walk the body tree instead."""
    out = set()
    for b in range(m.nbody):
        nb = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or ""
        if nb.startswith(prefix):
            out.add(b)
    changed = True
    while changed:
        changed = False
        for b in range(m.nbody):
            if b not in out and m.body_parentid[b] in out:
                out.add(b)
                changed = True
    return out


ARMB = {t: _own_bodies(f"{t}_") | _own_bodies(f"{t}g_") for t in SIDES}
ARMG = {t: {g for g in range(m.ngeom) if m.geom_bodyid[g] in ARMB[t]} for t in SIDES}
_unnamed = sum(1 for g in range(m.ngeom) if not mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g))
print(f"[steps] geoms: {m.ngeom} total, {_unnamed} unnamed; arm geom sets L={len(ARMG['L'])} R={len(ARMG['R'])}")


def touching(t, dd):
    """What this arm is in contact with, other than itself."""
    out = set()
    for i in range(dd.ncon):
        g1, g2 = dd.contact[i].geom1, dd.contact[i].geom2
        a1, a2 = g1 in ARMG[t], g2 in ARMG[t]
        if a1 != a2:
            other = g2 if a1 else g1
            ob = m.geom_bodyid[other]
            out.add(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, ob) or GNAME[other])
    return out


def _measure_axfix():
    """Measure, per arm, where the closing axis and the approach axis sit in the tool's own frame.
    Measured on a throwaway MjData; the live state is never touched."""
    sc = mujoco.MjData(m)
    for t in SIDES:
        for k, a in enumerate(QADR[t]):
            sc.qpos[a] = [0.0, -1.2, 1.0, -1.4, -1.57, 0.0][k]
    mujoco.mj_forward(m, sc)
    out = {}
    for t in SIDES:
        pl, pr = np.array(sc.xpos[PAD[t][0]]), np.array(sc.xpos[PAD[t][1]])
        c_w = (pr - pl) / max(np.linalg.norm(pr - pl), 1e-9)
        pinch_w = 0.5 * (pl + pr)
        a_w = np.array(sc.xpos[TOOLB[t]]) - pinch_w
        a_w = a_w / max(np.linalg.norm(a_w), 1e-9)
        Rt = np.array(sc.xmat[TOOLB[t]]).reshape(3, 3)
        c_l, a_l = Rt.T @ c_w, Rt.T @ a_w
        s_l = np.cross(a_l, c_l)
        out[t] = np.column_stack([c_l, s_l, a_l]).T  # B_local^T
    return out


AXFIX = _measure_axfix()


def pinch(t, dd=None):
    dd = dd if dd is not None else d
    return 0.5 * (np.array(dd.xpos[PAD[t][0]]) + np.array(dd.xpos[PAD[t][1]]))


def pinch_jac(t):
    """Translational Jacobian of the pinch point, plus the rotational Jacobian of the tool."""
    Js = []
    for b in PAD[t]:
        jp = np.zeros((3, m.nv))
        mujoco.mj_jacBody(m, d, jp, None, b)
        Js.append(jp[:, VADR[t]])
    jr = np.zeros((3, m.nv))
    mujoco.mj_jacBody(m, d, None, jr, TOOLB[t])
    return 0.5 * (Js[0] + Js[1]), jr[:, VADR[t]]


# Desired tool orientation: closing axis along world Y (across the cable), approach along world Z
# (the gripper hangs down, pinch at the bottom).  Measured once, in the tool's own frame.
R_DES = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])


def tool_R(t):
    return np.array(d.xmat[TOOLB[t]]).reshape(3, 3)


def ik(t, target, gain=0.45, lam=0.06, dq_max=0.030, lag=0.35, wrot=0.6):
    Jp, Jr = pinch_jac(t)
    ep = target - pinch(t)
    Rerr = (R_DES @ AXFIX[t]) @ tool_R(t).T
    er = Rotation.from_matrix(Rerr).as_rotvec()
    J = np.vstack([Jp, wrot * Jr])
    e = np.concatenate([ep, wrot * er])
    dq = gain * (J.T @ np.linalg.solve(J @ J.T + lam**2 * np.eye(6), e))
    n = float(np.linalg.norm(dq))
    if n > dq_max:
        dq *= dq_max / n
    qn = np.array([d.qpos[a] for a in QADR[t]])
    qt[t] = np.clip(qt[t] + dq, qn - lag, qn + lag)
    return float(np.linalg.norm(ep))


def grasped(t):
    """True only when the cable is inside the ko bracket: it must touch a CLAW geom (f1ext/f2ext)
    on BOTH pads.  Contact with any pad face is not a clamp -- that predicate could not tell the
    two apart, and reported a grip that Rs could see was not there."""
    hit = set()
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        for a, b in ((g1, g2), (g2, g1)):
            if a in PADG[t] and b in CABG:
                nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, a) or ""
                if "ext" in nm:
                    hit.add("L" if "left" in nm else ("R" if "right" in nm else "?"))
    return {"L", "R"} <= hit


def seated(clip, cx, cy, link):
    """Groove interior in all three axes AND the seated link touching the groove floor."""
    p = np.array(d.xpos[CAB[link]])
    inside = (abs(p[0] - cx) < 0.022 and abs(p[1] - cy) < GROOVE_W / 2.0
              and abs(p[2] - (TABLE_TOP + CLIP_RISER + 0.030)) < 0.006)
    if not inside:
        return False, p
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        if (g1 in CLIPG[clip] and g2 in CABG) or (g2 in CLIPG[clip] and g1 in CABG):
            return True, p
    return False, p


# ---- settle the cable on its saddles, then MEASURE where it actually is ----
for t in SIDES:
    d.ctrl[GIDX[t]] = OPEN
mujoco.mj_forward(m, d)
for _ in range(2000):
    mujoco.mj_step(m, d)
P = np.array([d.xpos[b] for b in CAB])
print(f"[steps] cable settled: x[{P[:,0].min():+.3f},{P[:,0].max():+.3f}] y[{P[:,1].min():+.3f},{P[:,1].max():+.3f}] "
      f"z-table[{(P[:,2]-TABLE_TOP).min():+.4f},{(P[:,2]-TABLE_TOP).max():+.4f}] ncon={d.ncon}")


def cable_at(x):
    """Centre of the cable link nearest this x.  A link's body origin is the START of its capsule,
    so the material sits half a segment further along the link's own x axis -- targeting the origin
    misses by ~15 mm."""
    C = np.array([np.array(d.xpos[b]) + np.array(d.xmat[b]).reshape(3, 3) @ np.array([CABLE_SEG / 2, 0, 0])
                  for b in CAB])
    i = int(np.argmin(np.abs(C[:, 0] - x)))
    return C[i], i


gL, iL = cable_at(C1[0] - GRIP_HALF_SPAN)
gR, iR = cable_at(C1[0] + GRIP_HALF_SPAN)
GL = (float(C1[0] - GRIP_HALF_SPAN), float(gL[1]), float(gL[2]))
GR = (float(C1[0] + GRIP_HALF_SPAN), float(gR[1]), float(gR[2]))
Z_GRASP_REST = float(0.5 * (gL[2] + gR[2]))
Y_GRASP_REST = float(0.5 * (gL[1] + gR[1]))
print(f"[steps] measured grasp: L=cab{iL} {np.round(gL,4)}  R=cab{iR} {np.round(gR,4)}  "
      f"drop across the span = {abs(gL[2]-gR[2])*1000:.1f} mm")

# ---- start pose: solve full 6-DOF IK on a THROWAWAY MjData; the live d is never written ----
GRASP1 = {"L": np.array([GL[0], GL[1], Z_RISE_REST]), "R": np.array([GR[0], GR[1], Z_RISE_REST])}
LIMS = np.array([[-6.283, 6.283], [-6.283, 6.283], [-3.1416, 3.1416],
                 [-6.283, 6.283], [-6.283, 6.283], [-6.283, 6.283]])  # ur15_mj.urdf <limit>


def _wrap(q):
    q = q.copy()
    for k in range(6):
        while q[k] > math.pi and q[k] - 2 * math.pi >= LIMS[k, 0]:
            q[k] -= 2 * math.pi
        while q[k] < -math.pi and q[k] + 2 * math.pi <= LIMS[k, 1]:
            q[k] += 2 * math.pi
    return q


def _rdes(yaw, roll=0.0):
    """Closing axis across the cable, approach down; `yaw` spins the tool about the vertical and
    `roll` tips it about the closing axis, which walks the WRIST outboard while the pinch stays
    put.  Rolling is what lets two arms share an 88 mm span without their wrists meeting."""
    base = Rotation.from_euler("z", yaw) * Rotation.from_euler("z", math.pi / 2.0)
    return (base * Rotation.from_euler("y", roll)).as_matrix()


def solve_ik(t, tgt, tries=26, iters=300, seed=1, near=None, quiet=False, warm=None, other=None, re_max=0.05, wide=False):
    """Damped least-squares IK for position AND tool orientation on scratch MjData.  Keeps every
    solution that converges, wraps it to the nearest branch, drops the ones that would sit in
    collision, and returns the one closest to `near` (so the servo move stays short)."""
    sc = mujoco.MjData(m)
    if other is not None:
        for t2 in SIDES:
            if t2 != t:
                for k, a in enumerate(QADR[t2]):
                    sc.qpos[a] = other[k]
    rg = np.random.default_rng(seed)
    cands = []
    sgn = -1.0 if t == "L" else 1.0   # each arm tips AWAY from the other
    POSES = [(0.0, sgn * r) for r in (0.0, 0.35, 0.6, 0.85, 1.1)] + \
            [(y, sgn * r) for r in (0.35, 0.6, 0.85) for y in (0.3, -0.3)]
    if wide:  # per-STEP waypoints get a bigger pose menu so a CONTINUOUS branch survives
        POSES = POSES + [(y, sgn * r) for r in (0.2, 0.5, 0.75, 1.0) for y in (0.15, -0.15, 0.5, -0.5)]
    for _try in range(tries):
        RD = _rdes(*POSES[_try % len(POSES)])
        # warm-start EVERY tool pose from the previous waypoint before trying random
        # restarts, else the solver keeps handing back a different branch each STEP
        q = np.asarray(warm) if (warm is not None and _try < len(POSES)) else rg.uniform(LIMS[:, 0], LIMS[:, 1])
        for k, a in enumerate(QADR[t]):
            sc.qpos[a] = q[k]
        for _ in range(iters):
            mujoco.mj_forward(m, sc)
            Js = []
            for b in PAD[t]:
                jp = np.zeros((3, m.nv))
                mujoco.mj_jacBody(m, sc, jp, None, b)
                Js.append(jp[:, VADR[t]])
            jr = np.zeros((3, m.nv))
            mujoco.mj_jacBody(m, sc, None, jr, TOOLB[t])
            Rt = np.array(sc.xmat[TOOLB[t]]).reshape(3, 3)
            ep = tgt - pinch(t, sc)
            er = Rotation.from_matrix((RD @ AXFIX[t]) @ Rt.T).as_rotvec()
            J = np.vstack([0.5 * (Js[0] + Js[1]), 0.6 * jr[:, VADR[t]]])
            e = np.concatenate([ep, 0.6 * er])
            dq = 0.5 * (J.T @ np.linalg.solve(J @ J.T + 0.05**2 * np.eye(6), e))
            n = float(np.linalg.norm(dq))
            if n > 0.15:
                dq *= 0.15 / n
            qc = np.clip(np.array([sc.qpos[a] for a in QADR[t]]) + dq, LIMS[:, 0], LIMS[:, 1])
            for k, a in enumerate(QADR[t]):
                sc.qpos[a] = qc[k]
        mujoco.mj_forward(m, sc)
        pe = float(np.linalg.norm(tgt - pinch(t, sc)))
        Rt = np.array(sc.xmat[TOOLB[t]]).reshape(3, 3)
        re_ = float(np.linalg.norm(Rotation.from_matrix((RD @ AXFIX[t]) @ Rt.T).as_rotvec()))
        if pe > 0.002 or re_ > re_max:
            continue
        qw = _wrap(np.array([sc.qpos[a] for a in QADR[t]]))
        for k, a in enumerate(QADR[t]):
            sc.qpos[a] = qw[k]
        mujoco.mj_forward(m, sc)
        if float(np.linalg.norm(tgt - pinch(t, sc))) > 0.002:
            continue
        hit = bool(touching(t, sc))
        cands.append((qw, pe, re_, hit, abs(POSES[_try % len(POSES)][1])))
    free = [c for c in cands if not c[3]] or cands
    if not free:
        raise RuntimeError(f"no IK solution for {t} at {tgt}")
    ref = np.zeros(6) if near is None else np.asarray(near)
    near_only = [c for c in free if np.abs(c[0] - ref).max() <= 1.2] or \
                [c for c in free if np.abs(c[0] - ref).max() <= 2.2]
    pool = near_only or free
    q, pe, re_, hit, roll = min(pool, key=lambda c: 2.0 * c[4] + float(np.linalg.norm(c[0] - ref)))
    if not quiet:
        print(f"[steps] start-pose IK {t}: {len(cands)} solved / {len(free)} collision-free, "
              f"chosen pos {pe*1000:5.2f} mm roll {math.degrees(roll):4.1f} deg |q|max={np.abs(q).max():.2f} rad")
    return q


START = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}
for _round in range(3):
    for t in SIDES:
        START[t] = solve_ik(t, GRASP1[t], tries=24, near=START[t],
                            other=START["R" if t == "L" else "L"], quiet=(_round < 2))

# ---- STEP 1: the arms REACH the start pose by servo motion; no state is written ----
q0 = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}
for t in SIDES:
    d.ctrl[GIDX[t]] = OPEN
RAMP = 4000
for s_ in range(RAMP + 3000):
    f = min(1.0, s_ / RAMP)
    for t in SIDES:
        qc = (1.0 - f) * q0[t] + f * START[t]
        for k, i in enumerate(AIDX[t]):
            d.ctrl[i] = qc[k]
    mujoco.mj_step(m, d)
for t in SIDES:
    print(f"[steps] STEP1 {t} arm touching: {sorted(touching(t, d)) or 'clear'}")
qt = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}
gL, iL = cable_at(C1[0] - GRIP_HALF_SPAN)
gR, iR = cable_at(C1[0] + GRIP_HALF_SPAN)
GL = (float(gL[0]), float(gL[1]), float(gL[2]))
GR = (float(gR[0]), float(gR[1]), float(gR[2]))
print(f"[steps] re-measured after the approach: L=cab{iL} {np.round(gL,4)}  R=cab{iR} {np.round(gR,4)}")
for t in SIDES:
    qa = np.array([d.qpos[a] for a in QADR[t]])
    af = np.array([d.actuator_force[i] for i in AIDX[t]])
    bias = np.array([d.qfrc_bias[v] for v in VADR[t]])
    print(f"[steps] STEP1 {t}: tool err={np.linalg.norm(pinch(t)-GRASP1[t])*1000:6.1f}mm")
    print(f"          joint err   = {np.round((qa-START[t])*1000,1)} mrad")
    print(f"          act force   = {np.round(af,1)} N.m   (limits {EFFORT})")
    print(f"          gravity load= {np.round(bias,1)} N.m")
    print(f"          saturated   = {list(np.abs(af) >= EFFORT*0.999)}")

# ---- STEP table 2-18.  (step, name, L target, R target, Lfinger, Rfinger, seconds, gate) ----
LX1, RX1 = C1[0] - GRIP_HALF_SPAN, C1[0] + GRIP_HALF_SPAN
LX2, RX2 = C2[0] - GRIP_HALF_SPAN, C2[0] + GRIP_HALF_SPAN
RX_MID = 0.5 * (C1[0] + C2[0])  # table :1283 "R-hand Y はクリップ間中点"
STEPS = [
    (2, "cable上空へ", (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST), OPEN, OPEN, 2.2, None),
    (3, "cableへ下降", GL, GR, OPEN, OPEN, 2.6, None),
    (4, "cable把持", GL, GR, CLAMP, CLAMP, 2.0, "grasp"),
    (5, "持ち上げ", (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST), CLAMP, CLAMP, 2.0, None),
    (6, "C1上空へ搬送", (LX1, C1[1], Z_RISE_ROUTE), (RX1, C1[1], Z_RISE_ROUTE), CLAMP, CLAMP, 2.8, None),
    (7, "C1へ押し込み", (LX1, C1[1], Z_SEAT), (RX1, C1[1], Z_SEAT), CLAMP, CLAMP, 2.8, None),
    (8, "誘導ハンド半保持", (LX1, C1[1], Z_SEAT), (RX1, C1[1], Z_SEAT), HALF, OPEN, 1.6, None),
    (9, "C1がcable固定", (LX1, C1[1], Z_SEAT), (RX1, C1[1], Z_SEAT), HALF, OPEN, 1.6, "pinC1"),
    (10, "C1から上昇", (LX1, C1[1], Z_RISE_ROUTE), (RX1, C1[1], Z_RISE_ROUTE), HALF, OPEN, 2.0, None),
    (11, "C2上空へ", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE), HALF, OPEN, 2.6, None),
    (12, "左クランプ", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE), CLAMP, OPEN, 1.4, None),
    (13, "右がcable再把持へ", (LX2, C2[1], Z_RISE_ROUTE), (RX_MID, C2[1], Z_RISE_ROUTE), CLAMP, OPEN, 2.2, None),
    (14, "両手クランプ", (LX2, C2[1], Z_RISE_ROUTE), (RX_MID, C2[1], Z_RISE_ROUTE), CLAMP, CLAMP, 1.6, None),
    (15, "C2へ押し込み", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), CLAMP, CLAMP, 2.6, None),
    (16, "C2固定", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), CLAMP, CLAMP, 1.6, "pinC2"),
    (17, "解放", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), HALF, OPEN, 1.4, None),
    (18, "上昇", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE), HALF, OPEN, 2.0, None),
]

FPS, W, H = 30, 1600, 900
renderer = mujoco.Renderer(m, height=H, width=W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.15, 0.30, TABLE_TOP + 0.06]
cam.distance, cam.elevation = 1.35, -22
cam2 = mujoco.MjvCamera()
cam2.type = mujoco.mjtCamera.mjCAMERA_FREE
cam2.distance, cam2.elevation, cam2.azimuth = 0.40, -16, 250

frames, log, n = [], [], 0
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
gates = {}

# Pre-solve one joint waypoint per STEP per arm.  The IK runs offline on scratch data; the live
# arms are moved ONLY by their position servos interpolating between these waypoints.
qcmd = {t: START[t].copy() for t in SIDES}
prev = {t: START[t].copy() for t in SIDES}
for num, name, lt, rt, lf, rf, secs, gate in STEPS:
    tgt = {"L": np.array(lt), "R": np.array(rt)}
    # The pinch point is the midpoint of the two pad bodies, and the pads swing as they close, so
    # the pinch rises by CLOSE_RISE between OPEN and CLAMP.  Approach that much lower or the grip
    # closes just above the cable.
    if num in (3, 4, 5):   # grasp steps: aim at where the cable IS, right now
        cl, _ = cable_at(GL[0])
        cr, _ = cable_at(GR[0])
        for t, c in (("L", cl), ("R", cr)):
            z = (c[2] - CLAW_OFFSET) if num in (3, 4) else float(tgt[t][2])
            tgt[t] = np.array([c[0], c[1], z])
    w = dict(prev)
    for _round in range(3):
        for t in SIDES:
            w[t] = solve_ik(t, tgt[t], tries=44, iters=260, seed=num * 10 + (t == "R"),
                            near=prev[t], warm=prev[t], other=w["R" if t == "L" else "L"],
                            quiet=True, re_max=0.30, wide=True)
    prev = w
    q_from = {t: qcmd[t].copy() for t in SIDES}
    d.ctrl[GIDX["L"]], d.ctrl[GIDX["R"]] = lf, rf
    steps = int(secs / m.opt.timestep)
    ramp = int(0.72 * steps)
    for s_ in range(steps):
        f = 0.5 - 0.5 * math.cos(math.pi * min(1.0, s_ / ramp))  # smooth start and stop
        for t in SIDES:
            qcmd[t] = (1.0 - f) * q_from[t] + f * w[t]
            for k, i in enumerate(AIDX[t]):
                d.ctrl[i] = qcmd[t][k]
        if gate == "pinC1" and not d.eq_active[EQ["C1"]]:
            ok, pp = seated("C1", *C1, SEAT1)
            if ok:
                d.eq_active[EQ["C1"]] = 1
                gates["pinC1"] = f"t={n*m.opt.timestep:.2f}s seat={np.round(pp,4)}"
        if gate == "pinC2" and not d.eq_active[EQ["C2"]]:
            ok, pp = seated("C2", *C2, SEAT2)
            if ok:
                d.eq_active[EQ["C2"]] = 1
                gates["pinC2"] = f"t={n*m.opt.timestep:.2f}s seat={np.round(pp,4)}"
        mujoco.mj_step(m, d)
        n += 1
        if n % render_every == 0:
            cam.azimuth = 108 + 14.0 * np.sin(n * 0.0007)
            renderer.update_scene(d, camera=cam)
            a_img = renderer.render()
            cam2.lookat[:] = 0.5 * (pinch("L") + pinch("R"))
            renderer.update_scene(d, camera=cam2)
            frames.append(np.hstack([a_img, renderer.render()]))
    if gate == "grasp":
        gates["grasp"] = grasped("L") and grasped("R")
        for t in SIDES:
            pw = pinch(t)
            dists = [float(np.linalg.norm(np.array(d.xpos[b]) - pw)) for b in CAB]
            j = int(np.argmin(dists))
            sep = float(np.linalg.norm(np.array(d.xpos[PAD[t][0]]) - np.array(d.xpos[PAD[t][1]])))
            names = set()
            for i in range(d.ncon):
                g1, g2 = d.contact[i].geom1, d.contact[i].geom2
                for a, b in ((g1, g2), (g2, g1)):
                    if a in PADG[t] and b in CABG:
                        names.add(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, a))
            blk = set()
            for i in range(d.ncon):
                g1, g2 = d.contact[i].geom1, d.contact[i].geom2
                for a, b in ((g1, g2), (g2, g1)):
                    if a in PADG[t] and b not in PADG[t]:
                        bb = m.geom_bodyid[b]
                        blk.add(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, bb) or f"g{b}")
            print(f"[steps] GRASP {t}: fingers blocked by {sorted(blk) if blk else 'nothing'}")
            print(f"[steps] GRASP {t}: nearest cable link cab{j} at {dists[j]*1000:5.1f} mm from the "
                  f"pinch, pad separation {sep*1000:5.1f} mm, ctrl={d.ctrl[GIDX[t]]:.0f}, "
                  f"pad geoms touching cable = {sorted(names) if names else 'none'}")
    le = np.linalg.norm(pinch("L") - tgt["L"]) * 1000
    re_ = np.linalg.norm(pinch("R") - tgt["R"]) * 1000
    p1, p2 = np.array(d.xpos[CAB[SEAT1]]), np.array(d.xpos[CAB[SEAT2]])
    row = (f"STEP{num:2d} {name:12s} t={n*m.opt.timestep:5.1f}s L={le:6.1f}mm R={re_:6.1f}mm "
           f"c1[y{p1[1]:+.3f} z{p1[2]-TABLE_TOP:+.3f}] c2[y{p2[1]:+.3f} z{p2[2]-TABLE_TOP:+.3f}] "
           f"pin={'C1' if d.eq_active[EQ['C1']] else '--'}/{'C2' if d.eq_active[EQ['C2']] else '--'} "
           f"grip={'L' if grasped('L') else '-'}{'R' if grasped('R') else '-'}")
    print("[steps] " + row)
    log.append(row)

print(f"[steps] gates: {gates}")
import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=8, macro_block_size=None)
print(f"[steps] wrote {OUT} frames={len(frames)} {OUT.stat().st_size} bytes")
