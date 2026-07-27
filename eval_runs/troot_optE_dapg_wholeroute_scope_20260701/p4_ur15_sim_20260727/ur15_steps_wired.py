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

# --- every cell constant comes from one module (p5 spec §0 / §6) ---
# SOURCED: importing these from ur15_cell_spec is the one form the contract allows.  They used to
# be defined here, and in eleven sibling files, with twenty-one of them disagreeing.
from ur15_cell_spec import (  # noqa: E402
    ARMATURE, CABLE_N, CABLE_R, CABLE_SEG, CLAMP, CLAW_OFFSET, CLIP_BASE_HEIGHT, CLIP_COLLIDE,
    CLIP_FRICTION, CLIP_PARTS, CLIP_SOLREF, DAMP, EFFORT, GRIP_HALF_SPAN, GROOVE_CENTER_Z, HALF,
    C1, C2, CABLE_JOINT_RANGE, CELL_TIMESTEP, CLIP_Y_EVEN, CLIP_Y_ODD, COLUMN_R,
    COLUMN_HZ, FINGER_RAMP, FLOAT_Z, FLOOR_HALF, FLOOR_SPACING, GRASP_ATTITUDES,
    KP_ARM, KP_WRI, KVR, LIMS, OPEN, PEDESTAL_HZ, PEDESTAL_R, REST_LIP_DY,
    REST_LIP_HY, REST_LIP_HZ, REST_POST_HALF, REST_TOP, REST_X, REST_Y, R_DES,
    SETTLE_S, SETTLE_TOL, SIGMA_FLOOR, START_HOLD_S, START_RAMP_S, TABLE_HZ, TABLE_Y,
    Z_HOME, Z_RISE_REST, Z_RISE_ROUTE,
    SHOULDER_HEIGHT, SIDES, TABLE_HX, TABLE_HY, TABLE_TOP, TILT, YOKE_SPREAD, guard,
    seat_z,
)
import ur15_cell_spec as _spec  # noqa: E402

_spec.announce()
_unclassified = guard(__file__, strict=False)
if _unclassified:
    print(f"[steps] ⚠ the cell-constant contract is not satisfied yet: {len(_unclassified)} names")
    print("[steps] ⚠ each needs a home in the p5 spec; running non-strict while that is decided")
    for _n, _l, _w in _unclassified:
        print(f"[steps]     {_n:20s} line {_l:5d}  {_w[:60]}")

J6 = list(_spec.ARM_JOINTS)      # the URDF names, in kinematic order

# ⚠ STILL DEFINED HERE, and each one is a cell constant the spec does not yet carry.  The contract
# says a driver that needs a new one adds it to the spec rather than defining it, so these are
# reported to p5 rather than kept: CLIP_Y_ODD, CLIP_Y_EVEN, C1, C2, Z_HOME, Z_RISE_ROUTE,
# Z_RISE_REST, FLOAT_Z.
#
# EFFORT, LIMS and CLAW_OFFSET have LEFT this list: each had an authoritative source all along and
# was copied rather than read.  The joint limits had been rounded on the way across -- ±6.283 for
# ±6.283185307179586 -- so the driver was sampling and unwrapping inside a range very slightly
# narrower than the robot's own.

import os as _os  # noqa: E402
OLD_SEAT_AIM = _os.environ.get('P4_OLD_SEAT_AIM') == '1'

# FLOAT_Z is imported now.  It was declared here because the spec module refused to supply it;
# p5 withdrew the refusal on the grounds that a withheld value is an invented one.
GROOVE_Z = seat_z(FLOAT_Z)                 # where the cable centre must end up, world z
Z_SEAT = GROOVE_Z - CLAW_OFFSET            # the same height expressed at the pinch

# Finger commands for the table's three states.  The table and task_config speak in an opening per
# side [m] with the face gap stated as twice that (task_config.py:274/276/277: OPEN 0.04, HALF
# 0.006 "cable slides through claw", CLOSE 0.002 "gap=4mm < cable 8mm -> 2mm/side compression").
# The tendon actuator takes a dimensionless 0..255 instead, so these are the commands MEASURED to
# produce those face gaps (probe_ctrl_map.py, this model, static settle):
#     80.0 mm -> ctrl  17.7      12.0 mm -> ctrl 214.1      4.0 mm -> ctrl 235.5
# CLAMP commands the design gap, not the maximum.  I had gone to 255 because it clamped once and
# 236 did not, but p5 and p11 took that apart: the drive is a position target under an effort cap
# (task_config.py:129 FINGER_EFFORT_LIMIT = 60.0), so 255 does not "grip harder" -- it abandons the
# position reference and runs to a 1.3 mm overlap, which EXPELS a correctly seated O8 cable.  The
# run it clamped was one where the cable was not seated, so it is no evidence for the method.  With
# the cable seated the jaw stops on the cable anyway: the hand that held stopped at 6.81 mm while
# commanding 255.  So command 4.0 mm and let the cable and the effort cap decide where it stops.
# CLAMP / HALF / OPEN come from the spec module (imported above).  They were rebound here
# as well, which made the import dead -- the same second copy this contract exists to stop.
# Rs: the clamp is too fast, halve it.  Stepping the command shut the jaw in 0.544 s (149.2 mm/s
# of face travel, measured with probe_close_time.py on this model).  Ramping the command over
# 0.75 s gives 1.084 s (74.9 mm/s) -- half the speed, measured, not estimated.
# The measured worst was 0.0381 on the hand Rs watched swing around; the other arm never went
# below 0.1884 on the same trajectory, so 0.12 keeps what that arm already does and refuses what
# the other one did.  Candidates below it are dropped unless nothing else reaches.
# What holds the cable, per the banked ko design (GD-KoShape-Finger.md:95): the grip is COMPOSITE,
# "lateral flat-pad (pad1) pinch [dominant] + vertical claw (f1ext/f2ext) straddle".  The claws do
# NOT pinch -- they pass above and below the cable (f1ext BELOW, f2ext ABOVE, cable between them,
# :58-59) and catch it under lift load.  The pinch face is pad1.  So the cable must arrive in the
# slot BETWEEN the claws (pad-local z ~ 32.0 mm, the midpoint of f1ext 38.2 and f2ext 25.8), and
# the jaw then closes until the two pad1 faces compress it.  slot_centre() below measures that
# point live, because the four-bar tilts the pads as they close.


def arm_spec():
    x = (S / "ur15_base.xml").read_text()
    for j in J6:
        x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)
    p = S / "_arm_only.xml"
    p.write_text(x)
    return mujoco.MjSpec.from_file(str(p))


def clip_xml(name, cx, cy):
    """The env's own V-groove clip, turned a quarter turn and stood at `FLOAT_Z`.

    Five boxes: a base plate, two walls making the groove, and two lips above them making the
    mouth that funnels the cable in.  Read from `newton_skill_env_base._v_groove_clip_parts` by
    the spec module, so this cell cannot drift away from the env's.

    What this replaces was mine: a 40 mm pillar under a 12 mm plinth under a 12 mm floor, with a
    16 mm slot on top and no lip at all -- 78 mm tall against this one's 30, and 64 mm of it
    solid.  The cable was being driven straight through that solid part.
    """
    # The spacer stands the clip off the table, so it is the clip's own footprint --
    # not a shape of its own.  It used to be 40x48 mm against the real clip's 30x40.
    _bx, _by = CLIP_PARTS[0][3], CLIP_PARTS[0][4]
    spacer = (f'      <geom name="{name}_spacer" type="box" size="{_bx:.4f} {_by:.4f} '
              f'{max(FLOAT_Z / 2, 1e-4):.4f}" pos="0 0 {max(FLOAT_Z / 2, 1e-4):.4f}" '
              f'material="clipf"/>\n' if FLOAT_Z > 0 else "")
    parts = "".join(
        f'      <geom name="{name}_{i}" type="box" size="{hx:.4f} {hy:.4f} {hz:.4f}" '
        f'pos="{dx:.4f} {dy:.4f} {dz + FLOAT_Z:.4f}" material="clip" '
        f'solref="{CLIP_SOLREF[0]:.1f} {CLIP_SOLREF[1]:.1f}" '
        f'friction="{CLIP_FRICTION[0]} {CLIP_FRICTION[1]} {CLIP_FRICTION[2]}"'
        f'{"" if CLIP_COLLIDE else " contype=\"0\" conaffinity=\"0\""}/>\n'
        for i, (dx, dy, dz, hx, hy, hz) in enumerate(CLIP_PARTS))
    return f"""
    <body name="{name}" pos="{cx} {cy} {TABLE_TOP}">
{spacer}{parts}    </body>"""


def rest_xml(i, cx):
    """Saddle: a post with two lips so the cable is captured instead of rolling off."""
    h = REST_TOP - TABLE_TOP
    return f"""
    <body name="S{i}" pos="{cx} {REST_Y} {TABLE_TOP}">
      <geom name="S{i}_post" type="box" size="{REST_POST_HALF} {REST_POST_HALF} {h/2:.4f}" pos="0 0 {h/2:.4f}" material="rest"/>
      <geom name="S{i}_la" type="box" size="{REST_POST_HALF} {REST_LIP_HY} {REST_LIP_HZ}" pos="0 {-REST_LIP_DY} {h+REST_LIP_HZ:.4f}" material="rest"/>
      <geom name="S{i}_lb" type="box" size="{REST_POST_HALF} {REST_LIP_HY} {REST_LIP_HZ}" pos="0 {REST_LIP_DY} {h+REST_LIP_HZ:.4f}" material="rest"/>
    </body>"""


def cable_xml():
    # CABLE_JOINT_RANGE is None when the spec says "as the producer has it", which is
    # unlimited -- so the attribute is absent rather than set wide.
    _RANGE = "" if CABLE_JOINT_RANGE is None else \
        f' range="{CABLE_JOINT_RANGE[0]} {CABLE_JOINT_RANGE[1]}"'
    x0 = -CABLE_SEG * CABLE_N / 2.0
    z0 = REST_TOP + CABLE_R
    s = f'\n    <body name="cab0" pos="{x0:.4f} {REST_Y} {z0:.4f}">\n      <freejoint name="cable_free"/>\n'
    s += f'      <geom name="cab0_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="{_spec.cable_seg_mass():.6f}" material="cable" friction="{_spec.CABLE_FRICTION[0]} {_spec.CABLE_FRICTION[1]} {_spec.CABLE_FRICTION[2]}" condim="{_spec.CABLE_CONDIM}"/>\n'
    dep = 1
    for i in range(1, CABLE_N):
        pad = "  " * dep
        s += pad + f'      <body name="cab{i}" pos="{CABLE_SEG:.4f} 0 0">\n'
        s += pad + f'        <joint name="cab{i}_y" type="hinge" axis="0 1 0"{_RANGE} damping="{_spec.CABLE_BEND_DAMPING:.5f}" stiffness="{_spec.cable_joint_k():.5f}"/>\n'
        s += pad + f'        <joint name="cab{i}_z" type="hinge" axis="0 0 1"{_RANGE} damping="{_spec.CABLE_BEND_DAMPING:.5f}" stiffness="{_spec.cable_joint_k():.5f}"/>\n'
        s += pad + f'        <geom name="cab{i}_g" type="capsule" fromto="0 0 0 {CABLE_SEG:.4f} 0 0" size="{CABLE_R}" mass="{_spec.cable_seg_mass():.6f}" material="cable" friction="{_spec.CABLE_FRICTION[0]} {_spec.CABLE_FRICTION[1]} {_spec.CABLE_FRICTION[2]}" condim="{_spec.CABLE_CONDIM}"/>\n'
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
  <option timestep="{CELL_TIMESTEP:.6g}" integrator="implicitfast" cone="elliptic"/>
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
    <geom name="floor" type="plane" size="{FLOOR_HALF} {FLOOR_HALF} {FLOOR_SPACING}" material="gridmat" pos="0 0 0" contype="0" conaffinity="0"/>
    <body name="column" pos="0 0 0">
      <geom name="stem" type="cylinder" size="{COLUMN_R} {COLUMN_HZ:.4f}" pos="0 0 {COLUMN_HZ:.4f}" material="col"/>
      <geom name="foot" type="cylinder" size="{PEDESTAL_R} {PEDESTAL_HZ}" pos="0 0 {PEDESTAL_HZ}" material="col"/>
    </body>
    <body name="table" pos="0 {TABLE_Y:.3f} 0">
      <geom name="table_top" type="box" size="{TABLE_HX} {TABLE_HY} {TABLE_HZ}" pos="0 0 {TABLE_TOP-TABLE_HZ:.4f}" material="table"/>
    </body>
    {clip_xml("C1", *C1)}
    {clip_xml("C2", *C2)}
    {"".join(rest_xml(i + 1, x) for i, x in enumerate(REST_X))}
    {cable_xml()}
  </worldbody>
  <equality>
    <!-- clip retention: the ONE authorised kinematic element.  Both start inactive. -->
    <connect name="C1_pin" body1="C1" body2="cab{SEAT1}" anchor="0 0 {GROOVE_Z - TABLE_TOP:.4f}" active="false"/>
    <connect name="C2_pin" body1="C2" body2="cab{SEAT2}" anchor="0 0 {GROOVE_Z - TABLE_TOP:.4f}" active="false"/>
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

# by joint name rather than by a count of three: the gain follows which joint it is
kps = np.array([KP_WRI if "wrist" in j else KP_ARM for j in J6])
for tag in SIDES:
    for i, j in enumerate(J6):
        a = cell.add_actuator()
        a.name, a.trntype, a.target = f"{tag}_{j}_act", mujoco.mjtTrn.mjTRN_JOINT, f"{tag}_{j}"
        a.gaintype, a.biastype = mujoco.mjtGain.mjGAIN_FIXED, mujoco.mjtBias.mjBIAS_AFFINE
        a.gainprm[0], a.biasprm[1], a.biasprm[2] = kps[i], -kps[i], -(kps[i] * KVR)
        a.forcerange, a.ctrlrange, a.ctrllimited = [-EFFORT[i], EFFORT[i]], list(LIMS[i]), 1

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
# The four ko claws of each arm, by explicit name -- the slot the cable must land in is the space
# between them.  Named, not substring-matched, so the set cannot silently pick up another geom.
CLAWG = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{t}g_{s}_pad_{c}ext")
             for s in ("left", "right") for c in ("f1", "f2")] for t in SIDES}
PAD1G = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{t}g_{s}_pad1") for s in ("left", "right")]
         for t in SIDES}
assert all(g >= 0 for t in SIDES for g in CLAWG[t] + PAD1G[t]), "claw/pad geom name lookup failed"
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


# Desired tool orientation, from the spec module (§6.4f): closing axis along world y, approach
# along world z.  It reads as three rows of 0 and ±1, which is exactly why no literal rule
# would ever have flagged it -- p5 placed it by decision instead.
_R_DES = np.array(R_DES)      # the imported rows, in the form the error term needs


def tool_R(t):
    return np.array(d.xmat[TOOLB[t]]).reshape(3, 3)


def ik(t, target, gain=0.45, lam=0.06, dq_max=0.030, lag=0.35, wrot=0.6):
    Jp, Jr = pinch_jac(t)
    ep = target - pinch(t)
    Rerr = (_R_DES @ AXFIX[t]) @ tool_R(t).T
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


def clamp_faces(t):
    """Which named gripper geoms of arm `t` are touching the cable, split by side and role.

    The clamp face is pad1 on BOTH pads (banked GD-KoShape-Finger.md:95: the flat-pad pinch is the
    dominant contact).  The claws straddle the cable rather than pinch it, so claw contact is
    RECORDED but not required -- requiring it would reject a real pad clamp.

    pad2 is reported SEPARATELY and never counts.  It is the lower box, pad-local z 0 to 18.75,
    entirely below the slot at 27 to 37 -- a cable touching only pad2 is held below the ko, not in
    it.  Rs watched a run where one hand had pad1 plus all four claws and the other had pad2 alone,
    and called it one hand succeeding; the predicate had called it two.
    """
    pad, low, claw = set(), set(), set()
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        for a, b in ((g1, g2), (g2, g1)):
            if a in PADG[t] and b in CABG:
                nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, a) or ""
                side = "L" if "_left_" in nm else ("R" if "_right_" in nm else "?")
                if "ext" in nm:
                    claw.add(side)
                elif nm.endswith("pad2"):
                    low.add(side)      # the LOWER pad box: below the ko slot entirely
                else:
                    pad.add(side)      # pad1: the face that spans the slot
    return pad, low, claw


def grasped(t):
    """Clamped = the cable is COMPRESSED between the two pad1 faces, not merely touched by them.

    The touch-only version reported a clamp that Rs could see was not there: the jaw had closed to
    a 8.4 mm overlap, i.e. the faces had passed through where the cable was, and contacts existed
    the whole way through.  Contact says the geoms met; only the face gap says whether the cable is
    still between them.  A O8 cable held with the design's 2 mm/side compression leaves a 4 mm gap
    (task_config.py:277), so the gap has to be positive, under the cable diameter, and not so small
    that the faces have swallowed it.
    """
    pad, _low, _claw = clamp_faces(t)
    if not {"L", "R"} <= pad:
        return False
    gap, _claw = jaw_gaps(t)
    return 2.0 < gap < 8.0


def slot_centre(t, dd=None):
    """World point midway between the two claws -- where the cable must arrive to be inside the ko.

    Measured live from the claw geoms, so it follows the pads as the four-bar tilts them.
    """
    dd = dd if dd is not None else d
    return np.mean([np.array(dd.geom_xpos[g]) for g in CLAWG[t]], axis=0)



def cable_perp(sp, dd=None):
    """Perpendicular from a world point to the cable centreline, INTERPOLATED along each segment.

    Returns (distance, closest point, link index, fraction along that link).  Snapping to a link
    centre leaves up to CABLE_SEG = 30 mm of purely axial residual, several times the containment
    band, so the old reading could not tell a miss from a sample.

    A link's body origin is the START of its capsule (see cable_at), not its middle.
    """
    dd = dd if dd is not None else d
    best = (1e9, None, -1, 0.0)
    for k, b in enumerate(CAB):
        a = np.array(dd.xpos[b])
        v = np.array(dd.xmat[b]).reshape(3, 3)[:, 0] * CABLE_SEG
        u = float(np.clip(float(np.dot(sp - a, v)) / float(np.dot(v, v)), 0.0, 1.0))
        q = a + u * v
        dist = float(np.linalg.norm(sp - q))
        if dist < best[0]:
            best = (dist, q, k, u)
    return best


def jaw_axes(t, dd=None):
    """The jaw's own frame, MEASURED rather than assumed.

    z_hat runs from one claw of a pad to the other, i.e. across the mouth -- the direction
    containment is about.  y_hat runs from one pad to the other, the closing direction.  x_hat
    completes the frame and lies along the cable when the tool is square to it.
    """
    dd = dd if dd is not None else d
    z_hat = np.array(dd.geom_xpos[CLAWG[t][0]]) - np.array(dd.geom_xpos[CLAWG[t][1]])
    z_hat = z_hat / max(1e-12, float(np.linalg.norm(z_hat)))
    y_hat = np.array(dd.xpos[PAD[t][0]]) - np.array(dd.xpos[PAD[t][1]])
    y_hat = y_hat - z_hat * float(np.dot(y_hat, z_hat))
    y_hat = y_hat / max(1e-12, float(np.linalg.norm(y_hat)))
    return np.vstack([np.cross(y_hat, z_hat), y_hat, z_hat])


def mouth_clear(t="L", dd=None):
    """Clear opening between the two claw inner faces [m], read off the model.

    Rs widened this by 4 mm today.  Deriving it here means the band cannot disagree with the
    asset the run is actually reading -- which is the failure mode that put a stale 10.00 into
    the copy under the run directory.
    """
    dd = dd if dd is not None else d
    g1, g2 = CLAWG[t][0], CLAWG[t][1]
    centres = float(np.linalg.norm(np.array(dd.geom_xpos[g1]) - np.array(dd.geom_xpos[g2])))
    return centres - float(m.geom_size[g1][2]) - float(m.geom_size[g2][2])


def seat_point(t, dd=None):
    """Where the cable has to be: on the jaw centreline in x and y, at the slot height in z.

    Averaging the four claw positions gave a point up to 21 mm off the centreline, because the
    four-bar does not swing the two pads symmetrically.  Aiming at that point walked one open claw
    straight into the cable on the way down and knocked it 20-30 mm out of reach before the jaw
    closed.  The pinch is the midpoint of the two pad bodies, so it is on the centreline by
    construction; only the height has to come from the claws.
    """
    dd = dd if dd is not None else d
    p_w = pinch(t, dd)
    return np.array([p_w[0], p_w[1], slot_centre(t, dd)[2]])


def slot_after_close(t, qarm, ctrl_g):
    """Where the ko seat point of arm `t` actually ends up if the arm holds `qarm` and the fingers
    are driven to `ctrl_g` and allowed to settle.

    Run on a THROWAWAY MjData -- the live arms are never written to.  Both the pinch and the slot
    move as the four-bar swings the pads, so the only reliable way to aim is to simulate the close
    and read the result, rather than to reason about which frame the offset lives in.
    """
    sc = mujoco.MjData(m)
    sc.qpos[:] = d.qpos
    sc.qvel[:] = 0.0
    sc.ctrl[:] = d.ctrl
    for k, a in enumerate(QADR[t]):
        sc.qpos[a] = qarm[k]
    for k, i in enumerate(AIDX[t]):
        sc.ctrl[i] = qarm[k]
    sc.ctrl[GIDX[t]] = ctrl_g
    for _ in range(int(SETTLE_S / m.opt.timestep)):
        mujoco.mj_step(m, sc)
    return seat_point(t, sc)


def seat_offset(t, qarm):
    """seat(closed) - pinch(open), for arm `t` held at `qarm`.  Both are rigidly attached to the
    tool, and the IK fixes the tool orientation, so this vector is constant in world for any pose
    the IK returns with that orientation -- which is why ONE evaluation is enough and the seven
    correction rounds were never needed.  What they were compensating for was the tool orientation
    changing between rounds because each round picked a different IK branch.

    p5 §3: evaluate at the pose the jaw is in when it captures, not the pose it is in now; the
    four-bar moves the mouth ~13 mm between open and closed.
    """
    sc = mujoco.MjData(m)
    for k, a in enumerate(QADR[t]):
        sc.qpos[a] = qarm[k]
    mujoco.mj_forward(m, sc)
    pinch_open = pinch(t, sc)          # the frame solve_ik works in
    sc.ctrl[:] = 0.0
    for k, i in enumerate(AIDX[t]):
        sc.ctrl[i] = qarm[k]
    sc.ctrl[GIDX[t]] = CLAMP
    for _ in range(int(SETTLE_S / m.opt.timestep)):
        mujoco.mj_step(m, sc)
    return seat_point(t, sc) - pinch_open


def aim_slot_at(t, cable_w, prev_q, seed, pose_only=None, fix_x=None, pose_rd=None):
    """Solve the pose that puts the ko mouth on the cable once the jaw has closed.

    p5 §3: the hand-side aim point is the mouth centre, not the pinch.  p5 §4: x is NOT re-aimed --
    it is GRIP_HALF_SPAN from the clip, a design constant carrying the 88 mm span, and reading it
    off the cable would let the span drift.
    """
    # p5 §3 asks for the offset to be evaluated at the pose the jaw is in when it captures.  I was
    # evaluating it at prev_q -- the pose the arm is in BEFORE the move -- and the offset is a
    # ~30 mm vector carried in the tool frame, so measuring it at a different tool orientation puts
    # the seat somewhere else.  Solve once to find out where the hand will be, measure the offset
    # THERE, and solve again.  Two solves, not a loop: the second pose has the orientation the
    # offset was measured at, so there is nothing left to converge.
    off = seat_offset(t, prev_q)
    want = np.array(cable_w, dtype=float)
    if fix_x is not None:
        want[0] = fix_x
    tgt = want - off
    # The orientation tolerance has to be tight HERE, unlike the transit waypoints.  `off` is a
    # ~30 mm vector carried in the tool frame, so it only lands where it was measured if the
    # solved tool orientation matches the one it was measured at.  At the transit tolerance of
    # 0.30 rad -- 17 degrees -- that vector can swing ~9 mm, nine times the containment band, and
    # that is the whole of the miss on the hand that failed: 13.5 mm off along the containment
    # axis while the hand that held was 0.4 mm off.
    w = solve_ik(t, tgt, tries=44, iters=260, seed=seed, near=prev_q, warm=prev_q,
                 other=None, quiet=True, re_max=0.02, wide=True, pose_only=pose_only,
                 pose_rd=pose_rd)
    # A second solve with the offset re-measured at the solved pose was tried and dropped: it moves
    # the target far enough that the solver hands back an arm the servos cannot reach inside the
    # step, so the arm never settles, the settle gate never releases the fingers, and the jaw is
    # still 80 mm open at the grasp.  Rs on that version: the attitude looks good but the position
    # is bad.  One solve, and correct the position where it is measurably wrong.
    land = slot_after_close(t, w, CLAMP) - want
    return w, tgt, float(np.linalg.norm(land))




def aim_both(cl, cr, prev_q, seed):
    """Aim each hand at its seat point, taking whichever tool pose seats that hand best.

    An earlier version forced both hands onto the same menu entry to make them mirror images, on
    the strength of the two hands visibly moving differently.  Rs: the hands do not have to mirror
    each other, they have to clamp.  So the entry is chosen per arm -- what carried over from that
    version, and is worth keeping, is pinning the entry at all: it holds each arm on one IK branch
    across the correction rounds, which is what let the loop converge instead of wander.
    """
    got = {}
    for t, c in (("L", cl), ("R", cr)):
        best, chosen = None, None
        for (yaw, roll) in GRASP_ATTITUDES:
            try:
                r = aim_slot_at(t, c, prev_q[t], seed=seed + (t == "R"), pose_rd=(yaw, roll),
                                fix_x=GL[0] if t == "L" else GR[0])
            except RuntimeError:
                continue
            if best is None or r[2] < best[0][2]:
                best = (r, (yaw, roll))
            if r[2] < 0.002:          # first attitude that seats it, squarest tried first
                chosen = (r, (yaw, roll))
                break
        if best is None:
            raise RuntimeError(f"no attitude reaches the seat for {t}")
        r, att = chosen if chosen is not None else best
        got[t] = (r[0], r[1], att, r[2])
        print(f"[steps] aim {t}: yaw {att[0]:+.2f} roll {att[1]:+.2f} rad "
              f"({math.degrees(att[1]):+.0f} deg tilt), seat error {r[2]*1000:.2f} mm"
              f"{'' if chosen is not None else '   <- nothing seated it; best effort'}")
    return got


def jaw_gaps(t, dd=None):
    """The two opposing-face gaps of arm `t` in mm: (flat pad faces, opposing claws).

    Signed surface distance, so a negative value is a real overlap.  The pad gap is the one the
    design speaks about: task_config.py:277 says the clamp state is a 4 mm gap on a Ø8 cable,
    i.e. 2 mm of compression per side.
    """
    dd = dd if dd is not None else d
    pad = mujoco.mj_geomDistance(m, dd, PAD1G[t][0], PAD1G[t][1], 2.0, None) * 1000.0
    claw = mujoco.mj_geomDistance(m, dd, CLAWG[t][0], CLAWG[t][2], 2.0, None) * 1000.0
    return pad, claw




def groove_rest_z(clip):
    """World z at which a cable of this radius rests on this clip's floor, read off the geom."""
    g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{clip}_0")   # the base plate
    return float(d.geom_xpos[g][2]) + float(m.geom_size[g][2]) + CABLE_R


CLIP_BOXES = [(g, clip) for clip in ("C1", "C2") for g in CLIPG[clip]]


def cable_in_clip_solid(dd=None):
    """Deepest penetration of the cable into any clip box [mm], and where.

    Returns (depth, clip, geom name, link index, contacts) with depth <= 0 meaning no overlap.
    Samples each link along its own axis, and inflates the box by the cable radius so a grazing
    surface contact reads as ~0 rather than as a miss.
    """
    dd = dd if dd is not None else d
    worst = (0.0, "", "", -1)
    for g, clip in CLIP_BOXES:
        c = np.array(dd.geom_xpos[g])
        R = np.array(dd.geom_xmat[g]).reshape(3, 3)
        hs = np.array(m.geom_size[g]) + CABLE_R
        for k, b in enumerate(CAB):
            a = np.array(dd.xpos[b])
            v = np.array(dd.xmat[b]).reshape(3, 3)[:, 0] * CABLE_SEG
            for u in (0.0, 0.25, 0.5, 0.75, 1.0):
                pen = float(np.min(hs - np.abs(R.T @ ((a + u * v) - c))))
                if pen > worst[0]:
                    worst = (pen, clip,
                             mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or str(g), k)
    n_touch = sum(1 for i in range(dd.ncon)
                  if (dd.contact[i].geom1 in CABG and any(dd.contact[i].geom2 in CLIPG[c2]
                                                          for c2 in ("C1", "C2")))
                  or (dd.contact[i].geom2 in CABG and any(dd.contact[i].geom1 in CLIPG[c2]
                                                          for c2 in ("C1", "C2"))))
    return worst[0] * 1000.0, worst[1], worst[2], worst[3], n_touch


def seat_legs(clip, cx, cy, link):
    """Each conjunct of seated(), separately, so a false gate says which leg is false.

    Also reports whether ANY link satisfies the geometry, because the gate names one fixed link
    and the cable can slide along its own axis -- in which case a seated cable would still read
    as not seated, and that is an identity error rather than a placement one.
    """
    p = np.array(d.xpos[CAB[link]])
    legs = {"x": abs(p[0] - cx) < 0.022,
            "y": abs(p[1] - cy) < _spec.groove_width() / 2.0,
            "z": abs(p[2] - GROOVE_Z) < 0.006}
    touch = any((c.geom1 in CLIPG[clip] and c.geom2 in CABG)
                or (c.geom2 in CLIPG[clip] and c.geom1 in CABG)
                for c in (d.contact[i] for i in range(d.ncon)))
    others = [k for k, b in enumerate(CAB)
              if abs(np.array(d.xpos[b])[0] - cx) < 0.022
              and abs(np.array(d.xpos[b])[1] - cy) < GROOVE_W / 2.0
              and abs(np.array(d.xpos[b])[2] - (TABLE_TOP + CLIP_RISER + 0.030)) < 0.006]
    return legs, touch, p, others


def seated(clip, cx, cy, link):
    """Groove interior in all three axes AND the seated link touching the groove floor."""
    p = np.array(d.xpos[CAB[link]])
    inside = (abs(p[0] - cx) < 0.022 and abs(p[1] - cy) < _spec.groove_width() / 2.0
              and abs(p[2] - GROOVE_Z) < 0.006)
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
if _os.environ.get("P4_CLIP_DUMP") == "1":
    print("[clip] --- every geom whose name starts with C1 or C2, from the COMPILED model ---")
    for _g in range(m.ngeom):
        _n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, _g) or ""
        if not (_n.startswith("C1") or _n.startswith("C2")):
            continue
        _sz = m.geom_size[_g] * 1000.0
        _po = d.geom_xpos[_g] * 1000.0
        print(f"[clip] {_n:12s} type={int(m.geom_type[_g])} half-size=[{_sz[0]:6.1f}{_sz[1]:6.1f}"
              f"{_sz[2]:6.1f}] world=[{_po[0]:7.1f}{_po[1]:7.1f}{_po[2]:7.1f}] "
              f"z-table=[{_po[2]-TABLE_TOP*1000:+6.1f}] contype={int(m.geom_contype[_g])} "
              f"conaffinity={int(m.geom_conaffinity[_g])} group={int(m.geom_group[_g])} "
              f"rgba_a={m.geom_rgba[_g][3]:.2f}")
    _cb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "C1")
    print(f"[clip] C1 body: id={_cb} parent={int(m.body_parentid[_cb])} "
          f"jntnum={int(m.body_jntnum[_cb])} mass={float(m.body_mass[_cb]):.4f} kg "
          f"(jntnum 0 and parent 0 mean it is welded to the world)")
    print(f"[clip] cable geom sample: contype={int(m.geom_contype[sorted(CABG)[0]])} "
          f"conaffinity={int(m.geom_conaffinity[sorted(CABG)[0]])} "
          f"condim={int(m.geom_condim[sorted(CABG)[0]])} radius={m.geom_size[sorted(CABG)[0]][0]*1000:.1f} mm")
    _c1g = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) for n in
            ("C1_riser", "C1_base", "C1_wa", "C1_wb", "C1_floor")]
    print(f"[clip] C1 geoms in the driver's CLIPG set: {sorted(CLIPG['C1'])} "
          f"vs every C1 geom in the model: {sorted(x for x in _c1g if x >= 0)}")
    for _g in _c1g:
        if _g >= 0:
            print(f"[clip] {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, _g):12s} "
                  f"solref={m.geom_solref[_g]} solimp={m.geom_solimp[_g][:3]} "
                  f"condim={int(m.geom_condim[_g])} friction={m.geom_friction[_g]} "
                  f"priority={int(m.geom_priority[_g])}")
    print("[cell] --- how far does the WHOLE arm reach below the cable, wrist included? ---")
    print("[cell] the gripper-only probe said 35.7 mm at roll 0.55 with the fingers open, but the")
    print("[cell] driver comment at :66 says open fingers touch the table with the cable at 60 mm.")
    print("[cell] If the wrist hangs lower than the fingers, that is where the difference lives.")
    for _t in SIDES:
        _slot = slot_centre(_t)
        _worst, _who = -1e9, ""
        for _g in ARMG[_t]:
            _c = np.array(d.geom_xpos[_g])
            _sz = np.array(m.geom_size[_g])
            _Rg = np.array(d.geom_xmat[_g]).reshape(3, 3)
            if int(m.geom_type[_g]) == int(mujoco.mjtGeom.mjGEOM_BOX):
                _low = min((_c + _Rg @ (np.array(k) * _sz))[2]
                           for k in [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1)
                                     for sz in (-1, 1)])
            else:
                _low = _c[2] - float(m.geom_rbound[_g])
            _d = _slot[2] - _low
            if _d > _worst:
                _worst, _who = _d, (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, _g)
                                    or f"geom{_g}")
        print(f"[cell] arm {_t}: lowest point is {_worst*1000:6.1f} mm below the mouth "
              f"(reached by {_who}); mouth sits {(_slot[2]-TABLE_TOP)*1000:.1f} mm above the table")
    raise SystemExit(0)

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
Z_GRASP_REST = float(np.mean([gL[2], gR[2]]))
Y_GRASP_REST = float(np.mean([gL[1], gR[1]]))
print(f"[steps] measured grasp: L=cab{iL} {np.round(gL,4)}  R=cab{iR} {np.round(gR,4)}  "
      f"drop across the span = {abs(gL[2]-gR[2])*1000:.1f} mm")

# ---- start pose: solve full 6-DOF IK on a THROWAWAY MjData; the live d is never written ----
GRASP1 = {"L": np.array([GL[0], GL[1], Z_RISE_REST]), "R": np.array([GR[0], GR[1], Z_RISE_REST])}
LIM = np.array(LIMS)          # the URDF values, read by the spec module


def _wrap(q):
    q = q.copy()
    for k in range(6):
        while q[k] > math.pi and q[k] - 2 * math.pi >= LIM[k, 0]:
            q[k] -= 2 * math.pi
        while q[k] < -math.pi and q[k] + 2 * math.pi <= LIM[k, 1]:
            q[k] += 2 * math.pi
    return q


def _rdes(yaw, roll=0.0):
    """Closing axis across the cable, approach down; `yaw` spins the tool about the vertical and
    `roll` tips it about the closing axis, which walks the WRIST outboard while the pinch stays
    put.  Rolling is what lets two arms share an 88 mm span without their wrists meeting."""
    base = Rotation.from_euler("z", yaw) * Rotation.from_euler("z", math.pi / 2.0)
    return (base * Rotation.from_euler("y", roll)).as_matrix()


COLG = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) for n in ("stem", "foot")]


def wrist_jac(t, dd=None):
    """The 6x6 tool Jacobian of arm `t`: translation of the pinch stacked on tool rotation."""
    dd = dd if dd is not None else d
    Js = []
    for b in PAD[t]:
        jp = np.zeros((3, m.nv))
        mujoco.mj_jacBody(m, dd, jp, None, b)
        Js.append(jp[:, VADR[t]])
    jr = np.zeros((3, m.nv))
    mujoco.mj_jacBody(m, dd, None, jr, TOOLB[t])
    return np.vstack([0.5 * (Js[0] + Js[1]), jr[:, VADR[t]]])


def sigma_min(t, dd=None):
    """Smallest singular value of that Jacobian.  Near zero means the arm has lost a direction --
    a singularity -- and the servo command for a small tool motion becomes a huge joint motion."""
    return float(np.linalg.svd(wrist_jac(t, dd), compute_uv=False)[-1])


def column_gap(t, dd=None):
    """Closest signed distance from this arm's geoms to the yoke column, in mm.  Negative means the
    arm is inside the column.  mj_geomDistance is a geometry query, so it reports this whether or
    not the pair can collide -- which matters here because I had switched the column's collision
    off, so nothing was stopping the arm from sweeping through the mast."""
    dd = dd if dd is not None else d
    best = 1e9
    for g in ARMG[t]:
        for c in COLG:
            best = min(best, mujoco.mj_geomDistance(m, dd, g, c, 1.0, None))
    return best * 1000.0


def solve_ik(t, tgt, tries=26, iters=300, seed=1, near=None, quiet=False, warm=None, other=None, re_max=0.05, wide=False, pose_only=None, pose_rd=None):
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
    if pose_rd is not None:
        # An explicit (yaw, roll) rather than a menu entry.  Rs, on the second hand: it is only
        # just clamping -- adjust the attitude.  The coarse menu steps roll by 0.25 rad, which is
        # 14 degrees of tilt on a mouth 10 mm tall, so the ladder below is what "adjust" needs.
        POSES = [(pose_rd[0], sgn * pose_rd[1])]
    elif pose_only is not None:
        # Both hands must present the ko the same way to the cable.  Fixing the menu entry and
        # letting only `sgn` differ makes the two solutions mirror images: same yaw, same roll
        # magnitude, tipped away from each other.  Left free, the two arms picked unrelated
        # branches -- 20.1 deg of roll on one and 34.4 on the other -- and only one could seat the
        # cable in its slot.
        POSES = [POSES[pose_only % len(POSES)]]
    for _try in range(tries):
        RD = _rdes(*POSES[_try % len(POSES)])
        # warm-start EVERY tool pose from the previous waypoint before trying random
        # restarts, else the solver keeps handing back a different branch each STEP
        if warm is not None and pose_only is not None:
            # With the menu pinned to one entry there is only ever one warm try, and the other
            # restarts came back from random joint space -- same fingertip, wildly different arm,
            # which is exactly the asymmetry this is meant to remove.  Stay near the warm pose and
            # perturb, so every candidate is the same branch.
            q = np.asarray(warm) + (0.0 if _try == 0 else rg.normal(0.0, 0.06, 6))
        elif warm is not None and _try < len(POSES):
            q = np.asarray(warm)
        else:
            q = rg.uniform(LIM[:, 0], LIM[:, 1])
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
            qc = np.clip(np.array([sc.qpos[a] for a in QADR[t]]) + dq, LIM[:, 0], LIM[:, 1])
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
        # Manipulability of this candidate.  The solver had no notion of a singularity at all --
        # it ranked candidates by position error and by staying near the previous pose, so a
        # configuration that has lost a direction could win, and did: Rs saw two runs in a row
        # swing around through one.  Rejecting those is the missing criterion, not a workaround.
        for _k, _a in enumerate(QADR[t]):
            sc.qpos[_a] = qw[_k]
        mujoco.mj_forward(m, sc)
        sv = sigma_min(t, sc)
        cands.append((qw, pe, re_, hit, abs(POSES[_try % len(POSES)][1]), sv))
    free = [c for c in cands if not c[3]] or cands
    if not free:
        raise RuntimeError(f"no IK solution for {t} at {tgt}")
    well = [c for c in free if c[5] >= SIGMA_FLOOR] or free   # drop the near-singular ones
    ref = np.zeros(6) if near is None else np.asarray(near)
    near_only = [c for c in well if np.abs(c[0] - ref).max() <= 1.2] or \
                [c for c in well if np.abs(c[0] - ref).max() <= 2.2]
    pool = near_only or well
    q, pe, re_, hit, roll, sv = min(pool, key=lambda c: 2.0 * c[4] + float(np.linalg.norm(c[0] - ref)))
    if not quiet:
        print(f"[steps] start-pose IK {t}: {len(cands)} solved / {len(free)} collision-free / "
              f"{len(well)} away from a singularity, chosen pos {pe*1000:5.2f} mm "
              f"roll {math.degrees(roll):4.1f} deg sigma_min {sv:.4f} |q|max={np.abs(q).max():.2f} rad")
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
# ⚠ durations, not step counts: at the producer's timestep 4000 steps is 0.83 s, not the
# 8 s this ramp was measured at.
RAMP = int(START_RAMP_S / m.opt.timestep)
for s_ in range(RAMP + int(START_HOLD_S / m.opt.timestep)):
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
    print(f"          saturated   = {list(np.abs(af) >= np.array(EFFORT)*0.999)}")

# ---- STEP table 2-18.  (step, name, L target, R target, Lfinger, Rfinger, seconds, gate) ----
LX1, RX1 = C1[0] - GRIP_HALF_SPAN, C1[0] + GRIP_HALF_SPAN
LX2, RX2 = C2[0] - GRIP_HALF_SPAN, C2[0] + GRIP_HALF_SPAN
RX_MID = float(np.mean([C1[0], C2[0]]))  # table :1283 "R-hand Y はクリップ間中点"

def mouth_clear(t="L", dd=None):
    """Clear opening between the two claw inner faces [m], read off the model."""
    dd = dd if dd is not None else d
    g1, g2 = CLAWG[t][0], CLAWG[t][1]
    centres = float(np.linalg.norm(np.array(dd.geom_xpos[g1]) - np.array(dd.geom_xpos[g2])))
    return centres - float(m.geom_size[g1][2]) - float(m.geom_size[g2][2])


def release_ctrl(clearance=None, lo=120.0, hi=255.0):
    """The finger command at which the CLAW TIPS let the cable out [ctrl units].

    Not the pad faces: the ko claws stand proud of the flat pads, so the cable leaves between the
    tips.  Reading the pad gap instead is what made a 12 mm pad opening look like a release when
    the tips were still 1.8 mm apart.

    The clearance is NOT the cable diameter.  Opening exactly to the diameter puts the command on
    the crossing point with nothing to spare, which is a lower bound rather than a setting -- p5's
    correction.  So allow for the cable sitting off-centre inside the mouth: the mouth is wider
    than the cable, and half that surplus is how far off centre it can be.  Every term is read off
    the asset, so the margin follows the 4 mm Rs added to the mouth today rather than being a
    number someone chose.

        clearance = cable diameter + (mouth - cable diameter) / 2

    ⚠ That the margin should be the containment half-band is my reading, not p5's instruction;
    p5 said only "further open than the crossing".  Pass `clearance` to override.
    """
    want = clearance if clearance is not None else 0.5 * (mouth_clear() + 2.0 * CABLE_R)
    g1, g2 = CLAWG["L"][0], CLAWG["L"][2]   # same arm, opposing jaws

    def gap(c):
        sc = mujoco.MjData(m)
        sc.qpos[:] = d.qpos
        sc.ctrl[:] = d.ctrl
        for t in SIDES:
            sc.ctrl[GIDX[t]] = c
        for _ in range(int(SETTLE_S / m.opt.timestep)):
            mujoco.mj_step(m, sc)
        return mujoco.mj_geomDistance(m, sc, g1, g2, 1.0, None)

    if gap(hi) >= want:          # already clear at the tightest command -- nothing to solve
        return hi
    for _ in range(12):
        mid = 0.5 * (lo + hi)
        if gap(mid) >= want:
            lo = mid
        else:
            hi = mid
    return lo


RELEASE = None   # solved once below, after the model exists

STEPS = [
    (2, "cable上空へ", (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST), OPEN, OPEN, 2.2, None),
    (3, "cableへ下降", GL, GR, OPEN, OPEN, 4.5, None),
    (4, "cable把持", GL, GR, CLAMP, CLAMP, 4.5, "grasp"),
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
    # p5: the final release opens BOTH hands to the claw-clearing command.  HALF is not a
    # release -- measured, its claw tips are 1.82 mm apart on an 8 mm cable.
    (17, "解放", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), "RELEASE", "RELEASE", 1.4, None),
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
sig_min = {t: 1e9 for t in SIDES}     # worst manipulability over the whole run
col_min = {t: 1e9 for t in SIDES}     # worst approach to the column over the whole run
sig_where = {t: "" for t in SIDES}
col_where = {t: "" for t in SIDES}
claw_min = {t: 1e9 for t in SIDES}   # minimum opposing-claw gap over the whole run, per arm
grasp_pose = {}                      # the STEP3 descent solution, reused verbatim at STEP4
aim_cable = {}                       # where the cable was when the aim was computed
aim_seat = {}                        # where the aim predicted the seat would end up
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
gates = {}

# Pre-solve one joint waypoint per STEP per arm.  The IK runs offline on scratch data; the live
# arms are moved ONLY by their position servos interpolating between these waypoints.
qcmd = {t: START[t].copy() for t in SIDES}
prev = {t: START[t].copy() for t in SIDES}
if _os.environ.get("P4_RELEASE_ONLY") == "1":
    _r = release_ctrl()
    print(f"[rel] release opening solved from the asset: ctrl {_r:.1f}")
    print(f"[rel] mouth {mouth_clear()*1000:.2f} mm, cable {2*CABLE_R*1000:.1f} mm, "
          f"clearance asked {0.5*(mouth_clear()+2*CABLE_R)*1000:.2f} mm")
    for _c in (214.0, 197.5, _r, 18.0):
        _sc = mujoco.MjData(m); _sc.qpos[:] = d.qpos; _sc.ctrl[:] = d.ctrl
        for _t in SIDES: _sc.ctrl[GIDX[_t]] = _c
        for _ in range(int(SETTLE_S / m.opt.timestep)): mujoco.mj_step(m, _sc)
        _g = mujoco.mj_geomDistance(m, _sc, CLAWG["L"][0], CLAWG["L"][2], 1.0, None) * 1000
        print(f"[rel] ctrl {_c:6.1f} -> claw tips {_g:6.2f} mm apart"
              f"{'   <- solved release' if abs(_c-_r)<0.05 else ''}")
    raise SystemExit(0)

RELEASE = release_ctrl()
print(f"[steps] release opening solved from the asset: ctrl {RELEASE:.1f} "
      f"(claw tips reach {0.5*(mouth_clear()+2*CABLE_R)*1000:.2f} mm = cable {2*CABLE_R*1000:.1f} "
      f"plus the {(mouth_clear()-2*CABLE_R)*500:.2f} mm the cable can sit off centre)")
STEPS = [tuple(RELEASE if v == "RELEASE" else v for v in row) for row in STEPS]

for num, name, lt, rt, lf, rf, secs, gate in STEPS:
    tgt = {"L": np.array(lt), "R": np.array(rt)}
    # The pinch point is the midpoint of the two pad bodies, and the pads swing as they close, so
    # the pinch rises by CLOSE_RISE between OPEN and CLAMP.  Approach that much lower or the grip
    # closes just above the cable.
    aimed = {}
    if num in (2, 3, 4, 5):   # grasp steps: aim at where the cable IS, right now
        cl, _ = cable_at(GL[0])
        cr, _ = cable_at(GR[0])
        if num == 2:
            got = aim_both(cl, cr, prev, seed=30)
            for t, c in (("L", cl), ("R", cr)):
                grasp_pose[t] = got[t]      # (joints, pinch target, attitude, error)
                aim_seat[t] = slot_after_close(t, got[t][0], CLAMP)
                aim_cable[t] = np.asarray(c, dtype=float)
                tgt[t] = np.array([got[t][1][0], got[t][1][1], Z_RISE_REST])
        for t, c in (("L", cl), ("R", cr)):
            if num == 2:
                pass   # handled once, for both hands together, just below
            elif num == 3:
                # p5 §4: re-aim ONCE here, at the standoff, BEFORE anything touches the cable --
                # and only in y and z.  After this the descent is vertical and nothing is aimed
                # again: chasing the cable once contact has started is what diverged.
                wq, tg, mag = aim_slot_at(t, c, prev[t], seed=40 + (t == "R"),
                                          pose_rd=grasp_pose[t][2],
                                          fix_x=GL[0] if t == "L" else GR[0])
                aimed[t], tgt[t] = wq, tg
                grasp_pose[t] = (wq, tg, grasp_pose[t][2], mag)
                aim_cable[t] = np.asarray(c, dtype=float)
                aim_seat[t] = slot_after_close(t, wq, CLAMP)
                print(f"[steps] STEP3 {t}: standoff re-aim (y,z only), seat error "
                      f"{mag*1000:5.2f} mm")
            elif num == 4:
                # p5 §4: hold.  The clamp step is the fingers closing, not the arm moving.
                aimed[t], tgt[t] = grasp_pose[t][0], grasp_pose[t][1]
                print(f"[steps] STEP4 {t}: holding the seated pose, fingers only")
            else:
                tgt[t] = np.array([c[0], c[1], float(tgt[t][2])])
    # Aim the MOUTH at the groove, not the pinch.  Detect the seat steps by their commanded
    # height rather than by number, so C1 and C2 are covered by the same line.
    for t in SIDES:
        if abs(float(tgt[t][2]) - Z_SEAT) < 1e-9 and not OLD_SEAT_AIM:
            off = seat_offset(t, prev[t])
            _clip = "C1" if abs(float(tgt[t][1]) - C1[1]) < 1e-9 else "C2"
            # where the cable is sitting inside the mouth right now, measured
            _ride = np.asarray(cable_perp(seat_point(t))[1]) - seat_point(t)
            want = np.array([float(tgt[t][0]), float(tgt[t][1]), groove_rest_z(_clip)])
            tgt[t] = want - off - _ride
            print(f"[steps] STEP{num:2d} {t}: aiming the CABLE at the {_clip} floor "
                  f"(pinch->mouth {np.round(off*1000,1)}, mouth->cable "
                  f"{np.round(_ride*1000,1)} mm; rest height "
                  f"{(groove_rest_z(_clip)-TABLE_TOP)*1000:.1f} mm above the table; the old "
                  f"constant said [0,0,{CLAW_OFFSET*1000:+.1f}])")

    w = dict(prev)
    for _round in range(3):
        for t in SIDES:
            if t in aimed:          # already solved by the closed-loop aim; do not re-solve
                w[t] = aimed[t]
                continue
            w[t] = solve_ik(t, tgt[t], tries=44, iters=260, seed=num * 10 + (t == "R"),
                            near=prev[t], warm=prev[t], other=w["R" if t == "L" else "L"],
                            quiet=True, re_max=0.30, wide=True)
    prev = w
    q_from = {t: qcmd[t].copy() for t in SIDES}
    g_from = {"L": float(d.ctrl[GIDX["L"]]), "R": float(d.ctrl[GIDX["R"]])}
    g_to = {"L": lf, "R": rf}
    steps = int(secs / m.opt.timestep)
    ramp = int(0.72 * steps)
    fing = max(1, int(FINGER_RAMP / m.opt.timestep))
    # On the grasp step the arm finishes moving BEFORE the fingers start.  Overlapping them made
    # the outcome depend on how fast the jaw happened to shut: the run that clamped did so with the
    # command stepped, and slowing the close to half speed -- which is what Rs asked for -- moved
    # the arm further before the faces met and lost the seat.  Going there, then clamping, is both
    # what the step table says and the only version that does not depend on that race.
    # p5 §6: settling is a GATE, not a delay.  The fingers do not begin to move until every
    # commanded joint is within SETTLE_TOL of where it was told to be, so the half-speed close Rs
    # asked for cannot be undone by the arm still drifting through it.
    gate_open = gate != "grasp"
    opened_at = 0
    for s_ in range(steps):
        f = 0.5 - 0.5 * math.cos(math.pi * min(1.0, s_ / ramp))  # smooth start and stop
        if not gate_open:
            resid = max(float(np.abs(np.array([d.qpos[a] for a in QADR[t2]]) - w[t2]).max())
                        for t2 in SIDES)
            if s_ > ramp and resid < SETTLE_TOL:
                gate_open, opened_at = True, s_
                print(f"[steps] STEP{num}: arms settled to {resid*1000:.2f} mrad at "
                      f"t={s_*m.opt.timestep:.2f}s into the step -- fingers may close")
        gf = 0.0 if not gate_open else min(1.0, (s_ - opened_at) / fing)
        for t in SIDES:
            d.ctrl[GIDX[t]] = g_from[t] + gf * (g_to[t] - g_from[t])
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
        if n % 40 == 0:
            for t2 in SIDES:
                sv = sigma_min(t2)
                if sv < sig_min[t2]:
                    sig_min[t2], sig_where[t2] = sv, f"STEP{num} t={n*m.opt.timestep:.1f}s"
                cg = column_gap(t2)
                if cg < col_min[t2]:
                    col_min[t2], col_where[t2] = cg, f"STEP{num} t={n*m.opt.timestep:.1f}s"
        if n % 20 == 0:
            # pZ CLAMP-1 v0.3a: the question is whether the PATH to the grip passed through a
            # configuration the real hardware cannot reach, so track the minimum over the window,
            # not the value at the end.  A negative minimum means the claws interpenetrated.
            for t in SIDES:
                _p, _c = jaw_gaps(t)
                claw_min[t] = min(claw_min[t], _c)
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
            # Where the slot ACTUALLY ended up relative to the cable, live.  The aim loop predicts
            # this on scratch data; printing both tells us whether the descent is disturbing the
            # cable or the servos are simply not arriving.
            # Measure against the link the hand is actually near, not the link nearest an x
            # measured at STEP 1.  The old version compared the seat with whatever piece of cable
            # happened to sit at a fixed x, so once the cable slid along its own axis the
            # comparison changed identity rather than reporting motion -- one hand printed a 25 mm
            # miss while holding the cable on all six ko surfaces.  Those numbers are retracted.
            sp = seat_point(t)
            _dist, _q, _ci, _u = cable_perp(sp)
            _loc = jaw_axes(t) @ (np.asarray(_q) - sp) * 1000.0
            cw = np.asarray(_q)
            sc_err = (sp - cw) * 1000.0
            qerr = (np.array([d.qpos[a] for a in QADR[t]]) - w[t]) * 1000.0
            _half = 0.5 * (mouth_clear(t) - 2 * CABLE_R) * 1000.0
            print(f"[steps] GRASP {t}: cable centreline is {_dist*1000:5.2f} mm from the seat "
                  f"(perpendicular, interpolated on cab{_ci} at {_u:.2f} along it)")
            print(f"[steps] GRASP {t}: in the jaw's own axes: along cable {_loc[0]:+6.2f}  "
                  f"closing {_loc[1]:+6.2f}  across the mouth {_loc[2]:+6.2f} mm "
                  f"(containment wants |across| < {_half:4.2f}, derived from the asset; "
                  f"the along-cable term does not affect it)")
            # Root cause split, not a bias.  The aim predicts where the seat ENDS UP after the
            # jaw closes.  If the seat is where that predicted, the arm did its job and the cable
            # moved; if it is not, the arm did not arrive.  Those need opposite fixes, and a
            # constant offset would paper over whichever one it is.
            _sd = (seat_point(t) - aim_seat[t]) * 1000.0
            _cd = (np.asarray(cw) - aim_cable[t]) * 1000.0
            print(f"[steps] GRASP {t}: seat vs its own PREDICTION {np.round(_sd,1)} mm "
                  f"(|{np.linalg.norm(_sd):5.1f}|)  cable vs where it was aimed "
                  f"{np.round(_cd,1)} mm (|{np.linalg.norm(_cd):5.1f}|)")
            print(f"[steps] GRASP {t}: joints vs commanded {np.round(qerr,1)} mrad "
                  f"-> {'servo did not arrive' if np.abs(qerr).max() > 5 else 'servo arrived'}; "
                  f"nearest link is {np.linalg.norm(np.asarray(cw) - aim_cable[t])*1000:5.1f} mm "
                  f"from where the aimed link was (identity may differ -- not a drift)")
            padg, clawg = jaw_gaps(t)
            pf, lf, cf = clamp_faces(t)
            print(f"[steps] GRASP {t}: pad faces {padg:+6.2f} mm (design target 4.00 on a "
                  f"O8 cable, task_config.py:277), opposing claws {clawg:+6.2f} mm, "
                  f"claw min over the run {claw_min[t]:+6.2f} mm"
                  f"{'  <- NEGATIVE: non-conservative for transfer' if claw_min[t] < 0 else ''}")
            print(f"[steps] GRASP {t}: cable touched by pad1 {sorted(pf) or 'none'} "
                  f"/ claws {sorted(cf) or 'none'} / pad2-only {sorted(lf) or 'none'} "
                  f"  clamped={grasped(t)} "
                  f"(needs both pads AND a 2-8 mm face gap; touch alone passed on a jaw that had "
                  f"closed through the cable)")
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
    print(f"[steps] STEP{num:2d} sigma_min L={sigma_min('L'):.4f} R={sigma_min('R'):.4f}"
          f"  column gap L={column_gap('L'):+7.1f} R={column_gap('R'):+7.1f} mm")
    gc1 = np.array([C1[0], C1[1], TABLE_TOP + CLIP_RISER + 0.030])
    _d1, _q1, _k1, _u1 = cable_perp(gc1)
    miss1 = (_q1 - gc1) * 1000.0
    carry = []
    for t in SIDES:
        sc = slot_centre(t)
        j = int(np.argmin([np.linalg.norm(np.array(d.xpos[b]) - sc) for b in CAB]))
        off = (np.array(d.xpos[CAB[j]]) - sc) * 1000.0
        carry.append(f"{t} mouth[{sc[0]:+.3f} {sc[1]:+.3f} {sc[2]-TABLE_TOP:+.3f}] "
                     f"holds cab{j} at ({off[0]:+5.1f},{off[1]:+5.1f},{off[2]:+5.1f}) mm")
    low = []
    for t in SIDES:
        sc_ = slot_centre(t)
        worst_, who_ = -1e9, ""
        for g_ in ARMG[t]:
            c_ = np.array(d.geom_xpos[g_])
            if int(m.geom_type[g_]) == int(mujoco.mjtGeom.mjGEOM_BOX):
                Rg_ = np.array(d.geom_xmat[g_]).reshape(3, 3)
                bot = min((c_ + Rg_ @ (np.array(k) * m.geom_size[g_]))[2]
                          for k in [(a, b, c2) for a in (-1, 1) for b in (-1, 1) for c2 in (-1, 1)])
            else:
                bot = c_[2] - float(m.geom_rbound[g_])
            if sc_[2] - bot > worst_:
                worst_, who_ = sc_[2] - bot, (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g_)
                                              or f"geom{g_}")
        low.append(f"{t} {worst_*1000:5.1f} mm below the mouth ({who_})")
    print(f"[steps] STEP{num:2d} ARM REACH: " + " | ".join(low))
    print(f"[steps] STEP{num:2d} CARRY: " + " | ".join(carry))
    print(f"[steps] STEP{num:2d} C1 SEAT: nearest point ON THE CABLE (cab{_k1} at {_u1:.2f}) misses "
          f"the groove centre by "
          f"({miss1[0]:+6.1f},{miss1[1]:+6.1f},{miss1[2]:+6.1f}) mm "
          f"(gate wants |dx|<22 |dy|<8 |dz|<6 AND clip-cable contact)")
    for _clip, _c, _lk in (("C1", C1, SEAT1), ("C2", C2, SEAT2)):
        _legs, _touch, _pp, _oth = seat_legs(_clip, _c[0], _c[1], _lk)
        _fail = [k for k, v in _legs.items() if not v] + ([] if _touch else ["contact"])
        print(f"[steps] STEP{num:2d} {_clip} GATE: cab{_lk} at "
              f"[{_pp[0]:+.3f} {_pp[1]:+.3f} {_pp[2]-TABLE_TOP:+.3f}] -> "
              f"{'PASS' if not _fail else 'fails on ' + ','.join(_fail)}"
              f"   (links whose geometry alone would qualify: {_oth if _oth else 'none'})")
    _pen, _pc, _pg, _pk, _ptouch = cable_in_clip_solid()
    print(f"[steps] STEP{num:2d} PENETRATION: "
          f"{'clear' if _pen <= 0 else f'cab{_pk} is {_pen:.1f} mm INSIDE {_pc} {_pg}'}"
          f"   (clip-cable contacts now: {_ptouch})")
    print("[steps] " + row)
    log.append(row)

for t in SIDES:
    print(f"[steps] WORST {t}: sigma_min {sig_min[t]:.4f} at {sig_where[t]}"
          f"   (a singular pose is sigma_min -> 0)")
    print(f"[steps] WORST {t}: column gap {col_min[t]:+7.1f} mm at {col_where[t]}"
          f"{'   <- INSIDE THE COLUMN' if col_min[t] < 0 else ''}")
print(f"[steps] gates: {gates}")
import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=8, macro_block_size=None)
print(f"[steps] wrote {OUT} frames={len(frames)} {OUT.stat().st_size} bytes")
