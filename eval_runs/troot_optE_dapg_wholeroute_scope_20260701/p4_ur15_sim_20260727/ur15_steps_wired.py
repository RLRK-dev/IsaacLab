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
    C1, C2, CABLE_JOINT_RANGE, CELL_TIMESTEP, CLAW_RELEASE_GAP, CLIP_Y_EVEN,
    CLIP_Y_ODD, COLUMN_R,
    COLUMN_HZ, FINGER_RAMP, FLOAT_Z, FLOOR_HALF, FLOOR_SPACING, GRASP_ATTITUDES,
    KP_ARM, KP_WRI, KVR, LIMS, OPEN, PEDESTAL_HZ, PEDESTAL_R, REST_LIP_DY,
    REST_LIP_HY, REST_LIP_HZ, REST_POST_HALF, REST_TOP, REST_X, REST_Y, R_DES,
    ARM_CLEARANCE, ARM_DECIDE_CUTOFF, ARM_PAIR_CUTOFF, PIN_SETTLE_S, PREDICT_S, TILT_CAL_DEG, SETTLE_S, SETTLE_TOL, SIGMA_FLOOR, SIGMA_GOOD, SIGMA_PENALTY,
    VERTICAL_TOL_DEG,
    START_HOLD_S, START_RAMP_S,
    TABLE_HZ, TABLE_Y,
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
# A SENTINEL, not a height.  A step that carries this z is one whose target is computed from
# measurement further down (`aiming the CABLE at the floor`): the pinch-to-mouth offset is read
# per arm and per pose there, and this number never reaches an arm.
# ⛔ It used to be GROOVE_Z - CLAW_OFFSET, which reads like the seat height expressed at the pinch
# and is not: CLAW_OFFSET is wrist->claw-tip minus wrist->pinch (+20.9 mm), while the drop this
# needs is pinch->mouth, measured here at -44.4 / -39.8 mm.  Two different vectors, one numeral's
# worth of resemblance.  Harmless only because the override always fires -- which is a latent
# fault, not a safe design.
Z_SEAT = GROOVE_Z

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
            near = g1 if a1 else g2
            ob = m.geom_bodyid[other]
            # p18 -622(6): the near side used to be dropped, so a contact could be reported without
            # saying which of THIS arm's parts made it -- and the open question about STEP13 is
            # precisely whether a claw plate is one of them.  Both ends are named now.
            out.add(f"{mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, ob) or GNAME[other]}"
                    f" (via {GNAME[near]})")
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


def _cable_tangent(t, dd=None):
    """Unit tangent of the cable where this jaw meets it -- from the interpolated centreline."""
    dd = dd if dd is not None else d
    _, _, ci, _ = cable_perp(pinch(t, dd), dd)
    a = np.array(dd.xpos[CAB[max(0, ci - 1)]])
    b = np.array(dd.xpos[CAB[min(CABLE_N - 1, ci + 1)]])
    v = b - a
    return v / max(1e-12, float(np.linalg.norm(v)))


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

    ⚠ The 21 mm above is the error of the REJECTED construction, in a paragraph written to explain
    why it was rejected -- it is not a residual the aim carries.  The offset this function's own
    output has from the mouth, measured with nothing in the jaws at every opening from clamped to
    fully open, is 0.00 mm laterally on both arms (run_logs_20260728/mouth_offset.txt).  Two
    measurements of different things, both true; read either without the other and the mechanism
    looks like it has a built-in miss that it does not have.  Which one bears on a given question
    is not settled here.
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
    for _ in range(int(PREDICT_S / m.opt.timestep)):
        mujoco.mj_step(m, sc)
    return seat_point(t, sc)


def jaw_axes_after_close(t, qarm, ctrl_g):
    """The jaw's own frame at the pose `qarm` once the fingers have closed to `ctrl_g`.

    Measurement only.  Same throwaway simulation slot_after_close uses, so the axes and the seat
    it predicts belong to the same instant; reading jaw_axes live instead would return the frame
    of the pose the arm is leaving, not the one the aim just solved.
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
    for _ in range(int(PREDICT_S / m.opt.timestep)):
        mujoco.mj_step(m, sc)
    return jaw_axes(t, sc)


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
    for _ in range(int(PREDICT_S / m.opt.timestep)):
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
    # Rs, 2026-07-28: do not choose a pose that comes within a set distance of the other arm.
    # This solve is where the grasp poses come from, and it ran blind -- other=None, so the far arm
    # was not in the scratch data at all and no clearance could have been measured even in
    # principle.  The pose it returned is then inherited into a route step, past the route's own
    # far-arm test, which is how a pose sitting on the other arm's forearm survived to be commanded.
    # The far arm's CURRENT joints are what it is given: where that arm will be later is not known
    # here, and pretending otherwise would trade a blind test for a confident wrong one.
    w = solve_ik(t, tgt, tries=None, iters=260, seed=seed, near=prev_q, warm=prev_q,
                 other=np.array([d.qpos[a] for a in QADR["R" if t == "L" else "L"]]),
                 quiet=True, re_max=0.02, wide=True, pose_only=pose_only,
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
        # ⚠ P4_ROLL_CAP: a measurement hook, not a design change.  The right hand's attitude is
        # chosen at 32 degrees of roll and jams there every run; the left is chosen at 17 and
        # clamps.  Selection asks only where the SEAT lands, never whether the cable can enter the
        # mouth -- so capping the roll asks whether that is the difference.  Unset, nothing changes.
        _cap = _os.environ.get("P4_ROLL_CAP")
        _menu = ([a for a in GRASP_ATTITUDES if abs(a[1]) <= float(_cap)] if _cap
                 else GRASP_ATTITUDES)
        for (yaw, roll) in _menu:
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


def claw_gap(t, dd=None):
    """Claw-tip gap [mm] of arm `t`, read where the channel does not saturate.

    p5 -099: the tip-to-tip query clamps once the tips overlap, so near closure it reports a floor
    instead of a distance.  The backplate gap keeps reading, and the offset between the two is a
    measured function of the opening -- so measure there and convert.  At CLAMP this is the
    difference between "the claws are 2.6 mm through each other" (the floor) and 6.4 mm (real).
    """
    return _spec.claw_from_backplate(jaw_gaps(t, dd)[0])


def cable_in_mouth(t, dd=None):
    """(is the cable centre inside the mouth band, its pad-local z [mm]).

    R6(ii).  The datum is the PAD BODY's own frame, not the world and not the jaw frame I used
    first: p5 -102 gives the band as f2ext's top at 25.00 mm to f1ext's bottom at 39.00 mm in
    right_pad / left_pad coordinates (asset :95), so

        p_pad = R_pad^T (p_world - x_pad)

    ⚠ and the sign is not intuition's: a LARGER pad-local z is FURTHER DOWN in the world
    (GD-KoShape :58-59), so reading world z gives the band upside down.  My first version measured
    along the jaw's claw-to-claw axis from the pad origin and produced 162-1243 mm against a band
    of 25-39 -- far enough out that it could not tell a wrong datum from a jaw that was simply
    nowhere near the cable.  It was the datum.
    """
    dd = dd if dd is not None else d
    q = np.asarray(cable_perp(pinch(t, dd), dd)[1])
    b = PAD[t][0]
    R_pad = np.array(dd.xmat[b]).reshape(3, 3)
    z = float((R_pad.T @ (q - np.array(dd.xpos[b])))[2]) * 1000.0
    lo, hi = (v * 1000.0 for v in _spec.MOUTH_BAND_Z)
    return (lo <= z <= hi), z


def held(t, dd=None):
    """R6 (p5 -099): capture is the CONJUNCTION, not either half.

    (i) the jaw is closed past the floor at which the cable could leave.  p5 -100's form, with
        its two origins kept apart: the floor is 2 x CABLE_R (Tier A) PLUS offset(gap) (the
        measured sweep).  Compared at the backplate, because the claw-tip channel saturates, and
    (ii) the cable's centre is inside the mouth band.

    `grasped()` answers neither: p5 showed it says held when the claws have closed through each
    other and released when the cable is still surrounded by them.
    """
    # ⚠ WHY the conversion is here and not everywhere (p11 -094(2)).  The two phases are not the
    # same case.  At RELEASE the floor sits at a backplate gap of 18.19 mm, where the claw-tip
    # channel still reads honestly -- converting there is insurance.  At CAPTURE the jaw is at a
    # backplate gap around 7 mm with the tips about -2.9 mm, which is INSIDE the saturated band:
    # read directly it comes back -2.6 whatever the truth is.  So the conversion is mandatory here
    # and optional there, and anyone tempted to simplify this back to a direct tip reading should
    # know it silently stops discriminating exactly where this predicate is used.
    return jaw_gaps(t, dd)[0] < _spec.release_floor() and cable_in_mouth(t, dd)[0]


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


def seat_tolerances():
    """The three half-widths the seat gate tests against, in metres: (x, y, z).

    One definition, because the number a report gives for a gate has to be the number the gate
    used.  It was written out twice -- once here and once in the line that explains a failure --
    and the two had already drifted: the explanation said 8 mm across the groove while the gate
    was using half the groove width, 7.5 mm.  A cable 7.8 mm off would have been described as
    inside a gate that rejects it, in the very sentence meant to say why it failed.
    """
    return 0.022, _spec.groove_width() / 2.0, 0.006


def seat_legs(clip, cx, cy, link):
    """Each conjunct of seated(), separately, so a false gate says which leg is false.

    Also reports whether ANY link satisfies the geometry, because the gate names one fixed link
    and the cable can slide along its own axis -- in which case a seated cable would still read
    as not seated, and that is an identity error rather than a placement one.
    """
    _tx, _ty, _tz = seat_tolerances()
    p = np.array(d.xpos[CAB[link]])
    legs = {"x": abs(p[0] - cx) < _tx,
            "y": abs(p[1] - cy) < _ty,
            "z": abs(p[2] - GROOVE_Z) < _tz}
    touch = any((c.geom1 in CLIPG[clip] and c.geom2 in CABG)
                or (c.geom2 in CLIPG[clip] and c.geom1 in CABG)
                for c in (d.contact[i] for i in range(d.ncon)))
    others = [k for k, b in enumerate(CAB)
              if abs(np.array(d.xpos[b])[0] - cx) < _tx
              and abs(np.array(d.xpos[b])[1] - cy) < _ty
              and abs(np.array(d.xpos[b])[2] - GROOVE_Z) < _tz]
    return legs, touch, p, others


def seated(clip, cx, cy, link):
    """Groove interior in all three axes AND the seated link touching the groove floor."""
    p = np.array(d.xpos[CAB[link]])
    _tx, _ty, _tz = seat_tolerances()
    inside = (abs(p[0] - cx) < _tx and abs(p[1] - cy) < _ty
              and abs(p[2] - GROOVE_Z) < _tz)
    if not inside:
        return False, p
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        if (g1 in CLIPG[clip] and g2 in CABG) or (g2 in CLIPG[clip] and g1 in CABG):
            return True, p
    return False, p


def seated_any(clip, cx, cy):
    """The link that is ACTUALLY in this clip right now, or None.

    Rs, 2026-07-28, watching the cable lift back out of the clip it had reached: fix it.

    The clip retention asked whether ONE named link was seated -- the link that happened to sit at
    the clip's x when the model was built.  The cable slides along its own axis while it is carried,
    so by the time it arrives a different link occupies the groove.  The run showed that plainly:
    the cable centre was 0.5 mm from the groove centre and touching the clip at six contacts, while
    the gate reported failure because the link it was watching had moved 15 mm away.  With the gate
    false the retention never engaged, so the cable came back up with the arms.

    The question the clip is really asking is whether ANY of the cable is seated in it, which is
    what this returns.  The predicate per link is unchanged.
    """
    for k in range(len(CAB)):
        ok, p = seated(clip, cx, cy, k)
        if ok:
            return k, p
    return None, None


def pin_to(clip, link):
    """Point this clip's retention at `link`, holding it where it is at this instant.

    ⛔ The anchor has to be recomputed, and this is the whole safety of the change.  A connect
    stores an anchor in EACH body's frame, and the second one was computed at compile time from
    where the ORIGINAL link happened to be.  Retargeting the constraint without rewriting it would
    activate a constraint that is not satisfied -- and MuJoCo would fix that by dragging the cable
    to where the stale anchor says it should be.  That is a teleport, and it is exactly what this
    project forbids everywhere except this one authorised pin.

    So the clip-side anchor is read as a world point, and the cable-side anchor is written as that
    same world point in the new link's CURRENT frame.  The constraint is then exactly satisfied at
    the instant it turns on, and nothing moves because of it.
    """
    e = EQ[clip]
    cb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, clip)
    anchor_world = np.array(d.xpos[cb]) + np.array(d.xmat[cb]).reshape(3, 3) @ m.eq_data[e][:3]
    b = CAB[link]
    local = np.array(d.xmat[b]).reshape(3, 3).T @ (anchor_world - np.array(d.xpos[b]))
    m.eq_obj2id[e] = b
    m.eq_data[e][3:6] = local
    return anchor_world


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


def attitude_tilt_deg(yaw, roll):
    """How far off straight down a jaw commanded to (yaw, roll) would point [deg].

    p11 -137: the cap has to be derived in the quantity the CHECK measures, not in the parameter
    the menu is written in.  The menu is (yaw, roll) pairs, and whether a given yaw also tips the
    jaw is a fact about this wrist, not something a rule should have to know.  So each entry is
    turned into the thing the check reads -- the direction pinch-to-mouth points -- and the cap is
    the smallest non-zero tilt any entry produces.

    No IK: the commanded tool orientation IS the attitude, so the direction follows from it
    directly.  The pinch-to-mouth vector is read once in the tool's own frame from the model as it
    stands, which is where it is constant.
    """
    v = slot_centre("L") - pinch("L")
    v_tool = np.array(d.xmat[TOOLB["L"]]).reshape(3, 3).T @ v
    v_tool = v_tool / max(1e-12, float(np.linalg.norm(v_tool)))
    # ⛔ NOT transposed.  The IK drives the tool until (RD @ AXFIX) @ Rt.T is the identity, so at
    # the pose this attitude asks for, Rt IS RD @ AXFIX -- and a vector in the tool frame reaches
    # world by that matrix, not by its inverse.  With the transpose the cap printed 0.00 degrees
    # for every attitude in the menu, which is what sent me back to this line.
    world = (_rdes(yaw, roll) @ AXFIX["L"]) @ v_tool
    world = world / max(1e-12, float(np.linalg.norm(world)))
    return math.degrees(math.acos(min(1.0, max(-1.0, float(-world[2])))))


def vertical_cap_deg():
    """The smallest non-zero tilt the attitude menu can produce, in degrees."""
    tilts = [attitude_tilt_deg(y, r) for y, r in _spec.GRASP_ATTITUDES]
    # ⛔ TWO checks, and the second is the one that matters -- p11 -144 caught that the first alone
    # passes the exact bug it was written for.  With the rotation inverted every attitude came out
    # flat, so the upright one came out flat too and the zero check was satisfied: a dead
    # instrument reproduces its zero perfectly.  A calibration needs both ends.
    #
    # Same shape as the pin's two readings, which is where this belongs: engagement is the zero,
    # a step later is the span.  Here the zero is the upright entry and the span is every entry
    # that asks for a tilt.  Neither says tilt must EQUAL roll -- the two differ by a couple of
    # degrees and should -- only that a non-zero input produces a non-zero output.
    upright = [attitude_tilt_deg(y, r) for y, r in _spec.GRASP_ATTITUDES if abs(r) < 1e-9]
    if upright and max(upright) > TILT_CAL_DEG:
        raise RuntimeError(
            f"the attitude with zero roll comes out {max(upright):.2f} deg off vertical, so this "
            f"is not turning attitudes into the tilt the check reads -- the cap it would produce "
            f"would be a number about the arithmetic, not about the cell")
    tilted = [attitude_tilt_deg(y, r) for y, r in _spec.GRASP_ATTITUDES if abs(r) >= 1e-9]
    if tilted and min(tilted) < TILT_CAL_DEG:
        raise RuntimeError(
            f"an attitude that asks for a tilt comes back {min(tilted):.2f} deg off vertical, "
            f"which is flat.  A construction that turns every attitude into the same answer is "
            f"not measuring attitude at all -- an inverted rotation, a scale of zero and a "
            f"collapsed sign all look like this, and the zero check cannot tell them apart "
            f"because they all reproduce the zero")
    # ⛔ The cap is min(tilted), NOT min over everything that came back non-zero.  Those are two
    # different sets and I had defined them two different ways inside one function: the
    # calibration selected by the INPUT (the attitude asked for a roll) and the cap selected by
    # the OUTPUT (the tilt came back above 1e-6).  The upright entries leak through the second
    # one on numerical noise -- a few thousandths of a degree -- so the cap came out 0.00 while
    # the calibration, looking at the other set, saw nothing wrong and stayed quiet.
    #
    # Which is the same failure as measuring the convenient quantity instead of the deciding one,
    # one level down: the cap is about attitudes that ASK for a tilt, so it selects on the ask.
    if not tilted:
        raise RuntimeError("no menu attitude asks for a tilt, so the vertical check has nothing "
                           "it could fail to distinguish and the cap is undefined")
    return min(tilted)


def _rdes(yaw, roll=0.0):
    """Closing axis across the cable, approach down; `yaw` spins the tool about the vertical and
    `roll` tips it about the closing axis, which walks the WRIST outboard while the pinch stays
    put.  Rolling is what lets two arms share an 88 mm span without their wrists meeting."""
    base = Rotation.from_euler("z", yaw) * Rotation.from_euler("z", math.pi / 2.0)
    return (base * Rotation.from_euler("y", roll)).as_matrix()


COLG = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) for n in ("stem", "foot")]
COLB = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "column")
# Each arm is attached to the mast, so its first body is a CHILD of the column body and its geoms
# sit inside the mast by construction -- that is the mount, not a crash.  MuJoCo already ignores
# those contacts (a body and its parent are filtered by default); the distance query does not know
# it.  So the same exclusion is derived from the model here rather than written as a list of link
# names, which would go quiet the day a link is renamed.
MOUNTG = {g for g in range(m.ngeom) if m.body_parentid[m.geom_bodyid[g]] == COLB}
# Held as a list, once: this is walked for every IK candidate of every solve, and rebuilding a set
# difference in there is work that buys nothing.
COLFREE = {t: sorted(ARMG[t] - MOUNTG) for t in SIDES}
CLEARANCE_REPORT = {}   # per arm: (candidates the clearance removed, candidates kept,
                        #           the clearance the winning pose was predicted to have)


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


def column_gap(t, dd=None, want_who=False, cutoff=None):
    """Closest signed distance from this arm's geoms to the yoke mast, in mm.  Negative means the
    arm is inside the mast.  mj_geomDistance is a geometry query, so it reports this whether or not
    the pair can collide -- and here the two differ: the arm's mount is inside the mast and its
    contacts are filtered, while everything past the mount does collide.

    ⛔ The bolted-on geoms are excluded (MOUNTG), or the answer would be a constant that never
    moves and says nothing.  Rs, 2026-07-28, watching the run: "the left hand is slamming into the
    cylinder" -- so the name of the part comes out with the number.  Twenty runs reported this as a
    bare figure, and a bare figure cannot say whether a hand arrived or a mount never left."""
    dd = dd if dd is not None else d
    best, who = 1e9, None
    for g in COLFREE[t]:
        for c in COLG:
            # Same exact prefilter as the arm-to-arm query, and here for the same reason: this
            # runs for every IK candidate of every solve, and the unfiltered form is what once
            # made a run take hours.  Two geoms cannot be closer than the gap between their
            # bounding spheres, so a pair already past the cutoff cannot lower the minimum.
            if cutoff is not None and (
                    float(np.linalg.norm(dd.geom_xpos[g] - dd.geom_xpos[c]))
                    - m.geom_rbound[g] - m.geom_rbound[c]) >= cutoff:
                continue
            d_ = mujoco.mj_geomDistance(m, dd, g, c, 1.0, None)
            if d_ < best:
                best, who = d_, f"{GNAME[g]} vs {GNAME[c]}"
    # ⛔ None, not the cutoff, when nothing is in range -- the cutoff wearing a distance's clothes
    # is the failure this instrument already had once, at the arm-to-arm surface.
    # ⛔ Metres, like the arm-to-arm query, so that BOTH gaps format through gap_mm and nothing
    # multiplies one of them by a thousand at a call site.  This used to return mm, and the mixed
    # pair of units is what put a bare "* 1000" in four different places.
    if best > 1e8:
        return (None, None) if want_who else None
    return (best, who) if want_who else best


def arm_pair_min(dd, ta="L", tb="R", want_who=False, cutoff=None):
    """Smallest signed distance between any geom of arm `ta` and any of arm `tb` [m].

    ⚠ Written this way for speed, and the speed matters: the naive form is 38x38 = 1444 distance
    calls, and it runs for every IK candidate of every solve.  It made a run take hours.

    The prefilter is exact rather than approximate.  Two geoms cannot be closer than the gap
    between their bounding spheres, so any pair whose centres are farther apart than
    cutoff + rbound + rbound is already past the cutoff and cannot lower the minimum.  Those are
    dropped by one vectorised comparison, and only the survivors are measured properly.  The
    answer is identical to the exhaustive form; only the work is smaller.
    """
    # ARMG holds sets -- numpy cannot index with one, and the first run said so immediately.
    cut = ARM_PAIR_CUTOFF if cutoff is None else cutoff
    ga, gb = np.fromiter(sorted(ARMG[ta]), int), np.fromiter(sorted(ARMG[tb]), int)
    pa = np.asarray(dd.geom_xpos)[ga]
    pb = np.asarray(dd.geom_xpos)[gb]
    ra = np.asarray(m.geom_rbound)[ga]
    rb = np.asarray(m.geom_rbound)[gb]
    sep = np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2) - ra[:, None] - rb[None, :]
    # ⛔ None, not the cutoff, when nothing is within range.  Returning the cutoff made the report
    # read "+176.0 mm" with an empty pair name, which is the cutoff wearing a distance's clothes --
    # the same saturation the claw-tip reading has, and the same way of hiding it.  A caller that
    # wants a number for a comparison can substitute one knowingly; the reader gets told.
    best, who = None, ""
    for ia, ib in zip(*np.where(sep < cut)):
        dv = mujoco.mj_geomDistance(m, dd, int(ga[ia]), int(gb[ib]), cut, None)
        if dv >= cut:
            continue
        if best is None or dv < best:
            best = dv
            if want_who:
                who = (f"{mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(ga[ia])) or ga[ia]}"
                       f" <-> {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(gb[ib])) or gb[ib]}")
    return (best, who) if want_who else best


def arm_sets_disjoint():
    """Names of any geom claimed by BOTH arms.  Empty is the only healthy answer.

    A shared geom would read as zero distance between the arms forever, which is exactly the
    "+0.0 mm along the move" the path sampler reported at a step whose endpoints were beyond the
    search radius.  That reading is either a real transient or this -- and one grep settles which,
    so it is checked at startup instead of being wondered about later.
    """
    both = set(ARMG["L"]) & set(ARMG["R"])
    return sorted(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f"geom{g}" for g in both)


def gap_mm(x, absent="beyond the search radius"):
    """Format an arm-gap reading in mm, or say it was not measured.

    ⛔ Every arm-gap value can be absent -- arm_pair_min returns None when no pair is inside the
    search radius, which is a real and common state, not an error.  I guarded that at the sites I
    happened to be editing and missed the others, and runs died on it FOUR times in an afternoon:
    each fix protected one line and left its neighbours open.  Individual guards were not working.

    So the formatting goes through here and nothing else multiplies one of these by a thousand.
    The absence has a spelling, and a caller cannot forget to give it one.
    """
    return absent if x is None else f"{x * 1000.0:+.1f} mm"


def solve_ik(t, tgt, tries=26, iters=300, seed=1, near=None, quiet=False, warm=None, other=None, re_max=0.05, wide=False, pose_only=None, pose_rd=None):
    """Damped least-squares IK for position AND tool orientation on scratch MjData.  Keeps every
    solution that converges, wraps it to the nearest branch, drops the ones that would sit in
    collision, and returns the one closest to `near` (so the servo move stays short)."""
    sc = mujoco.MjData(m)
    _clear_dropped = 0
    _col_dropped = 0
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
    # p11 -147 (C): before deciding whether the clearance and the ranking really compete, find out
    # whether the answer is just thin sampling.  Measured: the menu holds 65 attitudes and tries
    # was 44, so the search did not complete ONE pass over it -- twenty-one attitudes were never
    # tried at all, and "the best surviving candidate was worse" was said about a sample that had
    # not seen the whole menu.  None means every attitude twice: once for coverage, twice so each
    # gets a second seed.  Not a round number; the menu's own length.
    n_try = tries if tries is not None else 2 * len(POSES)
    for _try in range(n_try):
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
        # Rs, 2026-07-28, approving the change this had been waiting for: do not choose a pose
        # that comes within a set distance of the other arm.  Contact was the only test before,
        # and "not touching" covers a millimetre as happily as a metre -- which is how a pose
        # resting on the far arm's forearm kept being selected and reported as clear.
        # ⚠ Only when the far arm is IN this scratch data.  With other=None there is nothing to
        # measure against, and a clearance of "no other arm" would read as infinite -- so the
        # near-miss test says so rather than passing silently.
        hit = bool(touching(t, sc))
        _by_clearance = False
        near_far_arm = None
        if other is not None:
            # p11 -146: this loop only ever asks whether anything is under the clearance, so it
            # can search a radius just wider than the clearance instead of the reporting radius.
            # Nothing it DECIDES changes -- a pair beyond the small radius is beyond the clearance
            # by construction -- and the far pairs stop being measured.  The reported minimum
            # still uses the wide radius, because that one is read as a distance.
            near_far_arm = arm_pair_min(sc, t, "R" if t == "L" else "L",
                                        cutoff=ARM_DECIDE_CUTOFF)
            if near_far_arm is not None and near_far_arm < ARM_CLEARANCE:
                hit = True
                _clear_dropped += 1
                _by_clearance = True
        # Rs, 2026-07-28, watching the run: "the left hand is slamming into the cylinder."  The
        # mast was never in this filter.  It was MEASURED every step and printed as "column gap",
        # and it read negative at EIGHT steps of thirteen -- nine counting the one that read
        # exactly zero -- while the selection went on choosing those poses: an instrument
        # reporting a fault to nobody.  (I first wrote ten, from memory of the printout rather
        # than from a count of it; p18 counted the banked trace.  The steps are 3, 4, 5, 6, 11,
        # 12, 13, 14 at -0.6 mm and 10 at -0.0.)  So the mast is now tested exactly
        # where the far arm is tested, and by the same rule Rs approved for the far arm.
        # ⚠ Unconditional, unlike the far arm: the mast is always in the scene, so there is no
        # case where it is absent from the scratch data and nothing to measure.
        # The distance is the same one -- a cable diameter, the smallest thing that has to fit
        # between two parts of this machine.  Reusing it rather than inventing a second number is
        # a design call and is flagged as one; it is not derived that the two should be equal.
        # The decision only ever asks whether anything is under the clearance, so it searches a
        # radius just wider than the clearance -- p11's cutoff split, the same one the far-arm test
        # takes.  Nothing it decides changes; the far pairs stop being measured.
        _cg = column_gap(t, sc, cutoff=ARM_DECIDE_CUTOFF)
        if _cg is not None and _cg < ARM_CLEARANCE:
            hit = True
            _col_dropped += 1
        # Manipulability of this candidate.  The solver had no notion of a singularity at all --
        # it ranked candidates by position error and by staying near the previous pose, so a
        # configuration that has lost a direction could win, and did: Rs saw two runs in a row
        # swing around through one.  Rejecting those is the missing criterion, not a workaround.
        for _k, _a in enumerate(QADR[t]):
            sc.qpos[_a] = qw[_k]
        mujoco.mj_forward(m, sc)
        sv = sigma_min(t, sc)
        cands.append((qw, pe, re_, hit, abs(POSES[_try % len(POSES)][1]), sv, near_far_arm,
                      _by_clearance))
    free = [c for c in cands if not c[3]] or cands
    if not free:
        raise RuntimeError(f"no IK solution for {t} at {tgt}")
    well = [c for c in free if c[5] >= SIGMA_FLOOR] or free   # drop the near-singular ones
    ref = np.zeros(6) if near is None else np.asarray(near)
    near_only = [c for c in well if np.abs(c[0] - ref).max() <= 1.2] or \
                [c for c in well if np.abs(c[0] - ref).max() <= 2.2]
    pool = near_only or well
    # The singularity now RANKS, which is what the note beside SIGMA_FLOOR promised and never did.
    # A candidate that has lost a direction pays for it; none is forbidden, so the solver cannot be
    # starved the way the hard floor starved it.
    def _cost(c):
        _short = max(0.0, SIGMA_GOOD - c[5]) / SIGMA_GOOD      # 0 when well conditioned, ->1 at 0
        return 2.0 * c[4] + float(np.linalg.norm(c[0] - ref)) + SIGMA_PENALTY * _short
    # p11 -154, and it separates two things the earlier pair was mixing.  The winner is chosen by
    # _cost, not by conditioning, so the set the selector COULD have chosen from may hold a better
    # conditioned pose than the one it took.  Printing the best in that set beside the winner's
    # says which of two different problems this is: the filter removing good candidates, or the
    # cost passing over a good survivor.  If the best survivor is about as good as the best the
    # filter dropped, the filter took nothing and the competition is inside the ranking.
    _pool_sv = max(c[5] for c in pool)
    q, pe, re_, hit, roll, sv, nfa, _bc = min(pool, key=_cost)
    # p11 -139: the conditioning of the candidates the clearance threw away is already computed --
    # sv is taken for every candidate, including the rejected ones, and then dropped on the floor.
    # Printing the best of them beside the winner's turns that into the one comparison that is
    # actually controlled: same state, same candidate set, the only difference being the filter.
    # Across runs it would not be, because four other things changed.
    _drop_sv = [c[5] for c in cands if c[7]]
    # p11 -152, one field: is there any pose with room, or is this step's target the problem?
    # ⚠ The literal maximum is NOT available and saying so is the point.  The decision loop
    # searches a radius of twice the clearance, so a candidate with plenty of room comes back as
    # None -- "further than 16 mm", not a distance.  Reporting a max over the ones that ARE inside
    # that radius would be a maximum over the crowded candidates only, which is the opposite of
    # what the question asks.  So the count of candidates that cleared the whole search radius is
    # what goes out: many of them means poses with room exist, which is the one-sided refutation
    # p11 wants, and it is stronger than a max because it does not depend on where they sit.
    _roomy = sum(1 for c in cands if c[6] is None)
    _inside = [c[6] for c in cands if c[6] is not None]
    # p5 -137 / p11 -138, prints (1) and (3): say how many candidates the clearance removed -- the
    # same instrument as the floor's "how many did it remove", for the same reason -- and what
    # clearance the pose that WON was predicted to have.  A rejection count of zero and a rejection
    # count of forty look identical from a pose alone.
    CLEARANCE_REPORT[t] = (_clear_dropped, len(cands), nfa, sv,
                           max(_drop_sv) if _drop_sv else None,
                           _roomy, max(_inside) if _inside else None, _pool_sv,
                           _col_dropped)
    if not quiet:
        # ⛔ This line used to report len(well) as "away from a singularity", beside len(free) as
        # "collision-free".  With the floor at zero those are the SAME candidates -- sigma is never
        # negative, so the comparison keeps everything -- and printing one number under two names
        # said a filter had run when none had.  It was wording left over from the hard floor after
        # the floor itself was withdrawn (p11 -120(1) found it; I had written it).  So the count
        # printed now is how many the floor actually removed, which is zero while it is zero and
        # cannot be read as a second filter.  The singularity ranks; it does not exclude.
        print(f"[steps] start-pose IK {t}: {len(cands)} solved / {len(free)} collision-free / "
              f"floor {SIGMA_FLOOR:.2f} removed {len(free) - len(well)} of them (it ranks, it does "
              f"not exclude), chosen pos {pe*1000:5.2f} mm "
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
# ⛔ Before anything moves: does every Tier A value the cell can measure agree with the cell?
# CLAW_OFFSET is carried as +20.9 mm and this cell measures about -44 mm at the same quantity.
# The driver has been PRINTING that disagreement ("the old constant said [0,0,+20.9]") since the
# offset was first measured, and a print stopped nothing.  This raises.
_measured_offsets = {t: float(seat_offset(t, np.array([d.qpos[a] for a in QADR[t]]))[2])
                     for t in SIDES}
print(f"[steps] measured pinch->mouth drop: " +
      "  ".join(f"{t} {_measured_offsets[t]*1000:+.1f} mm" for t in SIDES))
# ⛔ CLAW_OFFSET is NOT compared here, and the reason matters more than the check: it is
# wrist->claw-tip minus wrist->pinch, while what this cell measures is pinch->mouth.  Comparing
# them would fail on two different quantities that happen to be lengths -- the same mistake this
# check exists to prevent, made by the check itself.  So the measurable set is empty today, and
# saying so is better than filling it with a comparison that does not hold.
print(f"[steps] Tier A cross-check: {len(_spec.cross_check_measurable({}))} measurable values "
      f"(CLAW_OFFSET excluded -- the cell measures pinch->mouth, which is a different vector)")

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
    (14, "両手クランプ", (LX2, C2[1], Z_RISE_ROUTE), (RX_MID, C2[1], Z_RISE_ROUTE), CLAMP, CLAMP, 1.6, "regrasp"),
    (15, "C2へ押し込み", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), CLAMP, CLAMP, 2.6, None),
    (16, "C2固定", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), CLAMP, CLAMP, 1.6, "pinC2"),
    # p5: the final release opens BOTH hands to the claw-clearing command.  HALF is not a
    # release -- measured, its claw tips are 1.82 mm apart on an 8 mm cable.
    (17, "解放", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT), "RELEASE", "RELEASE", 1.4, None),
    (18, "上昇", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE), HALF, OPEN, 2.0, None),
]

FPS, W, H = 30, 1600, 900
# One encoder setting for both writes.  The watch-along file and the finished file are the
# same run seen at two moments, so they must not be able to drift into looking different.
VIDEO_QUALITY = 8
renderer = mujoco.Renderer(m, height=H, width=W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
# Rs, 2026-07-28: the whole robot is not in shot.  The framing was a hand-picked lookat and
# distance chosen when the interesting part was the gripper, and it cropped the arms.  Both now
# come from the model's own estimate of how big the scene is, so the frame holds if the cell
# changes: mjModel carries a centre and an extent for exactly this, and a distance of about three
# extents puts the whole of it inside a 45-degree field with room to spare.
cam.lookat[:] = m.stat.center
cam.distance, cam.elevation = 3.0 * m.stat.extent, -22
cam2 = mujoco.MjvCamera()
cam2.type = mujoco.mjtCamera.mjCAMERA_FREE
cam2.distance, cam2.elevation, cam2.azimuth = 0.40, -16, 250
# Rs, 2026-07-28: a third view, from straight above.  Two things it settles that the other two
# cannot: whether a claw is over the groove or beside it, and how much of the cable has slid along
# its own axis -- both of which are motions in the plane this looks down on.
# ⚠ Its azimuth matches the WIDE camera's on purpose, so left and right mean the same thing in
# panel one and panel three.  They do NOT in panel two: the close-up looks from azimuth 250, so
# world +x runs to the LEFT there, and a hand that is on the right in the wide view appears on the
# left in the close-up.  That mirroring cost most of an afternoon of mis-attributed reports.
# Elevation is 89 degrees rather than 90 because a camera looking exactly down has no defined
# right, and the frame would be free to spin.
cam3 = mujoco.MjvCamera()
cam3.type = mujoco.mjtCamera.mjCAMERA_FREE
cam3.lookat[:] = [0.15, 0.30, TABLE_TOP]
cam3.distance, cam3.elevation, cam3.azimuth = 0.95, -89, 90

frames, log, n = [], [], 0
sig_min = {t: 1e9 for t in SIDES}     # worst manipulability over the whole run
col_min = {t: 1e9 for t in SIDES}     # worst approach to the column over the whole run
sig_where = {t: "" for t in SIDES}
col_where = {t: "" for t in SIDES}
claw_min = {t: 1e9 for t in SIDES}
arm_gap_min = 1e9   # closest the two arms come to each other over the whole run
arm_gap_path = 1e9  # ... including BETWEEN the poses that were checked, not only at them
_pin_watch = []     # clips whose retention has just engaged, waiting for a second reading
PIN_SETTLE_STEPS = max(1, int(PIN_SETTLE_S / m.opt.timestep))
# (step, arm, t, sigma_min, dq/dx) at every sample.  ⛔ sigma_min is for RANKING and envelope
# comparison only -- it mixes units, so no absolute threshold can live on it; the bar goes on the
# rad/m column.  Written here as well as in the file header because a caution that travels apart
# from its numbers does not travel.
sigma_trace = []   # minimum opposing-claw gap over the whole run, per arm
grasp_pose = {}                      # the STEP3 descent solution, reused verbatim at STEP4
aim_cable = {}                       # where the cable was when the aim was computed
aim_seat = {}                        # where the aim predicted the seat would end up
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
gates = {}

# A file that can be opened while the run is still going (Rs, 2026-07-28).  A normal mp4 puts its
# index at the end, so it is unplayable until the writer closes -- which is the whole problem this
# is here to fix.  Fragmenting it means each chunk carries its own index and a player can start on
# what has arrived so far.  The name is stable on purpose: the same file can stay open across runs
# rather than having to be found again each time.
import imageio.v2 as _iio                                                            # noqa: E402

LIVE_OUT = Path.home() / "Downloads" / "ur15_live.mp4"
LIVE_OUT.parent.mkdir(parents=True, exist_ok=True)
# Fragmenting alone is not enough and I checked rather than assumed: with only the movflags, a
# reader 4 seconds in still got "moov atom not found" and 28 bytes, because the encoder was
# holding everything in its own buffer.  It needs to be told to flush, and to cut a fragment on a
# fixed wall of time; with both, a reader partway through gets a real duration back.  Half a
# second of keyframe spacing and of fragment length, taken from FPS so they stay half a second if
# the frame rate ever changes.
_live = _iio.get_writer(str(LIVE_OUT), fps=FPS, quality=VIDEO_QUALITY, macro_block_size=None,
                        output_params=["-g", str(max(1, FPS // 2)),
                                       "-movflags", "frag_keyframe+empty_moov+default_base_moof",
                                       "-flush_packets", "1",
                                       "-frag_duration", str(500 * 1000)])


def live_write(img):
    """Append one frame to the watch-along file.  Never let it take the run down with it.

    If the encoder dies -- disk full, ffmpeg gone -- the run still has to finish, because the
    measurements are the thing that cannot be re-made cheaply.  So this reports once and then
    stays quiet rather than raising.
    """
    global _live
    if _live is None:
        return
    try:
        _live.append_data(img)
    except Exception as exc:                                     # noqa: BLE001 -- see docstring
        print(f"[steps] watch-along file stopped: {exc!r}; the run and the final video continue")
        _live = None


# p11 -137 / p5: the cap, measured in the quantity the check reads.  Printed at the start so the
# allowance and the thing that bounds it are both on the record before any pose is judged by them.
print(f"[steps] vertical check: allowance {VERTICAL_TOL_DEG:4.2f} deg, "
      f"cap {vertical_cap_deg():4.2f} deg (the smallest non-zero tilt the attitude menu can make, "
      f"measured as pinch->mouth against world -z, not as a roll); the allowance is an interim "
      f"until a run reports the worst residual an upright command actually leaves")

_shared = arm_sets_disjoint()
print(f"[steps] arm geom sets: L={len(ARMG['L'])} R={len(ARMG['R'])}, "
      f"{'DISJOINT' if not _shared else f'⛔ SHARED: {_shared}'}"
      f"  (a shared geom would read as zero distance between the arms at every step)")

print(f"[steps] watch along here while it runs: {LIVE_OUT}")

# Write one frame straight away, so the file EXISTS from the start.  The encoder is only spawned
# by the first frame, and the first frame of the run proper is a quarter of an hour away: the
# attitude search happens before anything steps.  Rs went to open the file in that window and
# found nothing there.  A still of the starting cell is not much, but "empty" and "not yet" look
# identical from outside, and only one of them is true.
renderer.update_scene(d, camera=cam)
_a0 = renderer.render()
cam2.lookat[:] = 0.5 * (pinch("L") + pinch("R"))
renderer.update_scene(d, camera=cam2)
_b0 = renderer.render()
renderer.update_scene(d, camera=cam3)
live_write(np.hstack([_a0, _b0, renderer.render()]))
print("[steps] watch-along file opened with the starting frame; it stays on that frame until the "
      "attitude search finishes and the arms begin to move")

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

def grasp_diagnostics(gate, w, aim_seat, aim_cable, gates):
    """Measure a closure -- the first grasp, or the re-grasp.

    Extracted from the step loop so it can be CALLED.  Inline, the only way to find out
    whether this instrument works was to run the whole choreography, which needs an
    authorisation I do not have; an instrument I cannot demonstrate is the same shape as
    the reports it is meant to check.
    """
    gates[gate] = grasped("L") and grasped("R")
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
        print(f"[steps] {gate.upper()} {t}: cable centreline is {_dist*1000:5.2f} mm from the seat "
              f"(perpendicular, interpolated on cab{_ci} at {_u:.2f} along it)")
        print(f"[steps] {gate.upper()} {t}: in the jaw's own axes: along cable {_loc[0]:+6.2f}  "
              f"closing {_loc[1]:+6.2f}  across the mouth {_loc[2]:+6.2f} mm "
              f"(containment wants |across| < {_half:4.2f}, derived from the asset; "
              f"the along-cable term does not affect it)")
        # Root cause split, not a bias.  The aim predicts where the seat ENDS UP after the
        # jaw closes.  If the seat is where that predicted, the arm did its job and the cable
        # moved; if it is not, the arm did not arrive.  Those need opposite fixes, and a
        # constant offset would paper over whichever one it is.
        # ⛔ Only the FIRST grasp is aimed -- aiming runs at steps 2-5, and the re-grasp sends
        # the hand to RX_MID, a fixed midpoint between the clips, with no measurement of where
        # the cable is.  So at a re-grasp `aim_seat` still holds the first grasp's prediction,
        # and comparing against it would report a residual for a closure that never had an aim.
        if gate == "regrasp":
            print(f"[steps] {gate.upper()} {t}: this closure was NOT aimed -- the hand goes to a "
                  f"fixed x (RX_MID), so it has no prediction of its own.  The distance-from-seat "
                  f"line above is the quantity comparable with the first grasp.")
        _sd = (seat_point(t) - aim_seat[t]) * 1000.0
        _cd = (np.asarray(cw) - aim_cable[t]) * 1000.0
        print(f"[steps] {gate.upper()} {t}: "
              f"{'(the FIRST grasp aim, for reference only) ' if gate == 'regrasp' else ''}"
              f"seat vs its own PREDICTION {np.round(_sd,1)} mm "
              f"(|{np.linalg.norm(_sd):5.1f}|)  cable vs where it was aimed "
              f"{np.round(_cd,1)} mm (|{np.linalg.norm(_cd):5.1f}|)")
        print(f"[steps] {gate.upper()} {t}: joints vs commanded {np.round(qerr,1)} mrad "
              f"-> {'servo did not arrive' if np.abs(qerr).max() > 5 else 'servo arrived'}; "
              f"nearest link is {np.linalg.norm(np.asarray(cw) - aim_cable[t])*1000:5.1f} mm "
              f"from where the aimed link was (identity may differ -- not a drift)")
        if np.abs(qerr).max() > 5:
            # "The servo did not arrive" has been printed at both R closures of every run, always
            # on the same joint and always by 80-90 degrees, and the line never said WHY.  The IK
            # clips its solution to the URDF limits and the actuator's range IS those limits, so
            # the command is reachable on paper: something is stopping the arm.  Two things can,
            # and they need opposite fixes -- an obstruction, or not enough torque to hold the arm
            # up against gravity -- so both are read here rather than argued about.
            # ⛔ touching() unfiltered on purpose: the mast, the table and the cable are exactly
            # the candidates, and the arm-to-arm print upstairs would hide all three.
            _af = np.array([d.actuator_force[i] for i in AIDX[t]])
            _sat = np.abs(_af) >= np.array(EFFORT) * 0.999
            _worst = int(np.argmax(np.abs(qerr)))
            print(f"[steps] {gate.upper()} {t}: WHY IT DID NOT ARRIVE -- worst joint j{_worst} "
                  f"short by {qerr[_worst]/1000.0:+.3f} rad; act force {np.round(_af,1)} N.m "
                  f"of {EFFORT}; at its limit = {list(_sat)}; gravity load "
                  f"{np.round([d.qfrc_bias[v] for v in VADR[t]],1)} N.m; "
                  f"touching {sorted(touching(t, d)) or 'nothing'}")
        padg, clawg = jaw_gaps(t)
        pf, lf, cf = clamp_faces(t)
        print(f"[steps] {gate.upper()} {t}: pad faces {padg:+6.2f} mm (design target 4.00 on a "
              f"O8 cable, task_config.py:277), opposing claws {clawg:+6.2f} mm, "
              f"claw min over the run {claw_min[t]:+6.2f} mm"
              f"{'  <- NEGATIVE: non-conservative for transfer' if claw_min[t] < 0 else ''}")
        print(f"[steps] {gate.upper()} {t}: cable touched by pad1 {sorted(pf) or 'none'} "
              f"/ claws {sorted(cf) or 'none'} / pad2-only {sorted(lf) or 'none'} "
              f"  clamped={grasped(t)} "
              f"(needs both pads AND a 2-8 mm face gap; touch alone passed on a jaw that had "
              f"closed through the cable)")
        print(f"[steps] {gate.upper()} {t}: fingers blocked by {sorted(blk) if blk else 'nothing'}")
        print(f"[steps] {gate.upper()} {t}: nearest cable link cab{j} at {dists[j]*1000:5.1f} mm from the "
              f"pinch, pad separation {sep*1000:5.1f} mm, ctrl={d.ctrl[GIDX[t]]:.0f}, "
              f"pad geoms touching cable = {sorted(names) if names else 'none'}")


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
    # R3, clip design §13-3.  The re-grasp had no aim at all: the hand went to RX_MID -- a design
    # constant, the midpoint between the two clips -- and closed on whatever happened to be there,
    # with no call that reads the cable.  p5's fix is not a new mechanism; it is the ruling already
    # made for the first grasp at §4 Q2, applied here too: measure the cable at the NEW x, correct
    # y and z, leave x alone.
    if num == 13:      # STEPS row 13, the approach that precedes the "regrasp" closure
        for t in SIDES:
            if abs(float(tgt[t][0]) - RX_MID) > 1e-9:
                continue                     # the other hand is holding; it does not move
            before = np.array(tgt[t], dtype=float)   # the un-aimed target, for the R4 question
            c_re, _ = cable_at(RX_MID)       # <- the reading that was missing
            wq, tg, mag = aim_slot_at(t, c_re, prev[t], seed=40 + (t == "R"),
                                      pose_rd=grasp_pose[t][2], fix_x=RX_MID)
            aimed[t], tgt[t] = wq, tg
            grasp_pose[t] = (wq, tg, grasp_pose[t][2], mag)
            aim_cable[t] = np.asarray(c_re, dtype=float)
            aim_seat[t] = slot_after_close(t, wq, CLAMP)
            _dy, _dz = (np.array(tg, dtype=float) - before)[1] * 1000, \
                       (np.array(tg, dtype=float) - before)[2] * 1000
            print(f"[steps] STEP{num} {t}: re-grasp re-aim (y,z only, x fixed at RX_MID), "
                  f"seat error {mag*1000:5.2f} mm  (first grasp measured 1.45-4.89 mm)")
            # p11's R4 question: is a y,z correction ENOUGH, or does the step need a descent of
            # its own?  The correction actually applied is the evidence, so print it -- a z term
            # that keeps arriving at the edge of what this phase can do is what would revive R4.
            print(f"[steps] STEP{num} {t}: correction applied  y {_dy:+6.2f} mm  z {_dz:+6.2f} mm "
                  f"(x held at RX_MID by ruling; a large or clipped z is the R4 signal)")
            # p5 -099: print the MARGIN, not a pass mark against a number someone chose.  What is
            # left of the containment half-band after the aim residual and after the tilt term --
            # the claw is not a point, so a cable that leans costs half its length times the lean.
            _hb = 0.5 * (mouth_clear(t) - 2 * CABLE_R) * 1000.0
            _tilt = float(np.arcsin(min(1.0, abs(float(jaw_axes(t)[2] @ _cable_tangent(t))))))
            _claw_half = float(m.geom_size[CLAWG[t][0]][0]) * 1000.0
            _margin = _hb - abs(mag) * 1000.0 - _claw_half * np.sin(_tilt)
            # p11 -424(3): three numbers about z, printed as numbers.  Required is the z offset
            # THIS re-grasp has to cover -- ⛔ not the 8.7 mm from the judged run, which was a
            # different span on a different cable.  Available is what the phase can actually
            # deliver in the roll attitude it is in, taken by re-solving at offset targets rather
            # than from the solver's own opinion of itself.  The difference is the third.
            _req = abs(_dz)
            # ⚠ Ask the question through the SAME path the phase uses: shift the cable the aim is
            # solving for, and see how far the solve still lands.  My first version passed a
            # position as `pose_only`, which selects an ATTITUDE INDEX -- it would have reported a
            # number that measured nothing, which is the defect this whole day has been about.
            _avail, _step_mm = 0.0, 1.0
            for _k in range(1, 41):
                _c2 = np.array(c_re, dtype=float)
                _c2[2] += _k * _step_mm / 1000.0
                _w2, _t2, _mag2 = aim_slot_at(t, _c2, prev[t], seed=40 + (t == "R"),
                                              pose_rd=grasp_pose[t][2], fix_x=RX_MID)
                if _mag2 > mag + _step_mm / 1000.0:      # the solve stopped tracking the cable
                    break
                _avail = _k * _step_mm
            print(f"[steps] STEP{num} {t}: z required {_req:6.2f} mm | available {_avail:6.2f} mm "
                  f"| difference {_avail - _req:+6.2f} mm  (printed, not a verdict -- p11)")
            print(f"[steps] STEP{num} {t}: margin {_margin:+6.2f} mm = half-band {_hb:5.2f} "
                  f"- aim residual {abs(mag)*1000:5.2f} - claw half {_claw_half:5.2f} x sin(tilt "
                  f"{np.degrees(_tilt):4.1f} deg) -> {'clears' if _margin > 0 else 'DOES NOT CLEAR'}")
    if num in (2, 3, 4, 5):   # grasp steps: aim at where the cable IS, right now
        cl, _icl = cable_at(GL[0])
        cr, _icr = cable_at(GR[0])
        _aim_link = {"L": _icl, "R": _icr}
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
            elif num == 3 and not _os.environ.get("P4_NO_STANDOFF_REAIM"):
                # ⚠ P4_NO_STANDOFF_REAIM: a measurement hook.  The single-shot probe -- aim once,
                # drive there, close -- clamps BOTH hands in this cell at 21.7 mm.  The run, which
                # differs by aiming again here at the standoff, jams the right hand at 30.4.  So
                # the hook asks whether this re-aim is the difference.  Unset, nothing changes.
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
                # p11 -116(4): a scalar seat error cannot say which way the budget is spent, and
                # the band the containment budget is measured along is the across-the-mouth axis
                # alone.  So give the same three components the GRASP print gives, one step
                # earlier -- at the aim, before anything has touched the cable.
                # ⚠ Taken on the PREDICTED close, not on a live jaw: the axes and the seat both
                # come from the same throwaway simulation slot_after_close runs, because at this
                # instant the arm is still at the previous pose and its live axes are not the
                # ones this aim will hold.  p11 -116(1): the surface is the prediction, and it is
                # named here so nobody reads it as the closing moment itself.
                _ax = jaw_axes_after_close(t, wq, CLAMP)
                _w3 = (np.asarray(c, dtype=float) - aim_seat[t]) * 1000.0
                _r3 = _ax @ _w3
                print(f"[steps] STEP3 {t}: that residual in the jaw's own axes (PREDICTED close): "
                      f"along cable {_r3[0]:+6.2f}  closing {_r3[1]:+6.2f}  "
                      f"across the mouth {_r3[2]:+6.2f} mm")
                # p11 -121(1): the jaw-frame split cannot tell two different stories apart, because
                # the two arms hold different attitudes and each frame rotates with its own.  In
                # world they are comparable: if both arms miss the same way, the thing they aim at
                # moved; if they miss differently, each arm's own aim is off and the roll gap is
                # the candidate.  One line, and the two lines stop being confounded.
                print(f"[steps] STEP3 {t}: and in world "
                      f"[{_w3[0]:+6.2f} {_w3[1]:+6.2f} {_w3[2]:+6.2f}] mm "
                      f"(same vector, no frame of its own -- compare the two arms here)")
                # p11 -116(3): the two arms' closing axes came out with opposite signs, which is
                # either a real difference or a mirrored convention in the asset.  Printing the
                # world direction of each settles it by inspection rather than by argument.
                print(f"[steps] STEP3 {t}: closing axis in world "
                      f"[{_ax[1][0]:+.3f} {_ax[1][1]:+.3f} {_ax[1][2]:+.3f}]  "
                      f"across-mouth axis [{_ax[2][0]:+.3f} {_ax[2][1]:+.3f} {_ax[2][2]:+.3f}]")
                # p11 -126(5) / -127(2): compare what the aim assumed about the target against the
                # target itself, so the comparison does not have to be inferred from two arms.
                # Its three conditions, and how each is met here:
                #   same frame   -- both sides are world, printed as world.
                #   same instant -- `c` came from cable_at a few lines up, on this same d, and
                #                   nothing has stepped since; aim_slot_at and slot_after_close
                #                   both work on throwaway copies.
                #   the assumed side is the variable the aim USED -- `c` is passed verbatim, the
                #                   same object handed to aim_slot_at.  Nothing is recomputed.
                # The point is not the informative half: cable_at returns the link centre, so the
                # aim's point IS the link's point by construction and the two must agree.  What the
                # aim has no value for is the DIRECTION -- it holds x fixed and re-aims y and z, so
                # it treats the cable as lying along world x.  If the cable has turned, that shows
                # up here and nowhere else in this print.
                # p11 -132(ii): the reader should not have to hold the world residuals in mind
                # and do the arithmetic in the right order.  If the cable had rotated rigidly, the
                # antisymmetric half of the two arms' residuals would be that rotation crossed
                # with the half-separation, so the angle it implies is computable here -- and
                # printed beside the angle actually measured, on the same line.  Same shape as the
                # tautological filter's "how many did it remove": say the number that decides it.
                _lk = CAB[_aim_link[t]]
                _dir = np.array(d.xmat[_lk]).reshape(3, 3)[:, 0]
                _turn = math.degrees(math.acos(min(1.0, abs(float(_dir[0])))))
                _turn_by[t], _dir_by[t] = _turn, _dir
                _neigh = []
                for _o in (-1, 1):
                    _j = _aim_link[t] + _o
                    if 0 <= _j < len(CAB):
                        _nd = np.array(d.xmat[CAB[_j]]).reshape(3, 3)[:, 0]
                        _neigh.append(f"cab{_j} {math.degrees(math.acos(min(1.0, abs(float(_nd[0]))))):4.1f}")
                print(f"[steps] STEP3 {t}: the aim ASSUMED the cable at [{c[0]:+.4f} {c[1]:+.4f} "
                      f"{c[2]:+.4f}] running along world x (x held, y and z re-aimed); "
                      f"cab{_aim_link[t]} ACTUALLY runs [{_dir[0]:+.3f} {_dir[1]:+.3f} "
                      f"{_dir[2]:+.3f}] = {_turn:4.1f} deg off that axis "
                      f"(neighbours: {', '.join(_neigh) or 'none'} deg)")
                _pred_w[t] = _w3
                if len(_pred_w) == len(SIDES):
                    _anti = 0.5 * (_pred_w["L"] - _pred_w["R"])
                    _half = GRIP_HALF_SPAN * 1000.0
                    print(f"[steps] STEP3: if the cable had rotated rigidly, these residuals "
                          f"would need x-y {math.degrees(math.atan2(_anti[1], _half)):+5.2f} deg "
                          f"and x-z {math.degrees(math.atan2(-_anti[2], _half)):+5.2f} deg; "
                          f"the links measure {_turn_by['L']:4.1f} and {_turn_by['R']:4.1f} deg "
                          f"off world x, with x-y components "
                          f"{_dir_by['L'][1]:+.4f} and {_dir_by['R'][1]:+.4f}")
            elif num == 4:
                # p5 §4: hold.  The clamp step is the fingers closing, not the arm moving.
                aimed[t], tgt[t] = grasp_pose[t][0], grasp_pose[t][1]
                print(f"[steps] STEP4 {t}: holding the seated pose, fingers only")
            else:
                tgt[t] = np.array([c[0], c[1], float(tgt[t][2])])
    # Aim the MOUTH at the groove, not the pinch.  Detect the seat steps by their commanded
    # height rather than by number, so C1 and C2 are covered by the same line.
    _seating = set()
    _pred_w, _turn_by, _dir_by = {}, {}, {}
    for t in SIDES:
        if abs(float(tgt[t][2]) - Z_SEAT) < 1e-9 and not OLD_SEAT_AIM:
            _seating.add(t)
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
                # (i) p11 -110, REPORT ONLY -- this changes no choice and no motion.  The aim that
                # produced this pose ran with other=None, so it never saw the far arm; inheriting
                # it here skips the route solve, and with it the far-arm check the route solve
                # does.  So put the inherited pose and the far arm into scratch and say what the
                # arms would be touching.
                # ⚠ SCOPE: the LINE below is arm-to-arm only -- it keeps the names beginning L_,
                # R_, Lg, Rg and drops the rest -- so "clear" here means "not on the other arm",
                # NOT "clear of everything".
                # ⛔ The earlier note gave the wrong reason: it said the posts and the table were
                # contype=0 and therefore invisible.  They are not; neither carries contype, so
                # both collide and touching() does see them.  It is this print that narrows, and a
                # note that blames the scene for what the filter does will send the next reader to
                # the wrong file.
                _sc2 = mujoco.MjData(m)
                _sc2.qpos[:] = d.qpos
                for _k2, _a2 in enumerate(QADR[t]):
                    _sc2.qpos[_a2] = aimed[t][_k2]
                _far = "R" if t == "L" else "L"
                if _far in aimed:
                    for _k2, _a2 in enumerate(QADR[_far]):
                        _sc2.qpos[_a2] = aimed[_far][_k2]
                mujoco.mj_forward(m, _sc2)
                _tch = sorted(g for g in touching(t, _sc2) if g.startswith(("L_", "R_", "Lg", "Rg")))
                print(f"[steps] STEP{num} {t}: inherited aim pose, arm-to-arm check = "
                      f"{_tch or 'not on the other arm'} (⚠ arm-to-arm ONLY -- posts and table are "
                      f"invisible to this test)")
                w[t] = aimed[t]
                continue
            # Rs, 2026-07-28, watching the run: "when descending to a clip, all fingers have to
            # point straight down, so they do not hit the table."  A tilted jaw puts its lower
            # claw out sideways and down -- at 32 degrees the arm's lowest point sat 48.5 mm below
            # its own mouth, which was 25.5 mm THROUGH the table while the mouth was still 23 mm
            # above it.  Upright, the claws hang under the mouth instead of swinging beneath it.
            # Nothing is invented for this: (0, 0) is already the first entry of the attitude menu,
            # and pose_rd is the existing way to name one attitude instead of searching.
            if t in _seating:
                try:
                    w[t] = solve_ik(t, tgt[t], tries=44, iters=260, seed=num * 10 + (t == "R"),
                                    near=prev[t], warm=prev[t],
                                    other=w["R" if t == "L" else "L"],
                                    quiet=True, re_max=0.30, wide=True, pose_rd=(0.0, 0.0))
                except RuntimeError as exc:
                    # ⛔ Do not fall back to a tilted attitude.  The requirement is the point; a
                    # silent tilt would put the fingers back through the table and report success.
                    raise RuntimeError(
                        f"STEP{num} {t}: no IK solution with the fingers vertical, which is what "
                        f"the descent to a clip requires.  Tilting instead is not a fallback here "
                        f"-- it is the thing that drove the claws through the table.  ({exc})"
                    ) from exc
                continue
            w[t] = solve_ik(t, tgt[t], tries=44, iters=260, seed=num * 10 + (t == "R"),
                            near=prev[t], warm=prev[t], other=w["R" if t == "L" else "L"],
                            quiet=True, re_max=0.30, wide=True)
    # p11 -132(i): the vertical requirement was enforced where the pose is SOLVED, and the
    # inherited branch leaves before that point.  Today the two sets do not overlap, so nothing
    # slipped through -- but that is a fact about which steps inherit, not a property of the
    # check, and the day an aim is extended to a seat step it would go quiet without anything
    # looking wrong.  So the requirement is checked where both branches have arrived, against the
    # pose that will actually be commanded, and by measurement rather than by which code path ran.
    # "Fingers straight down" is read as the pinch-to-mouth vector pointing along world -z: that
    # is the thing the fingers do, and it can be measured on any pose however it was obtained.
    for t in _seating:
        # p11 -149: this check was reading a MIXED state.  QADR is the six arm joints only, so
        # overwriting them left the fingers at whatever the live sim had -- and the mouth's
        # direction depends on where the four-bar is.  The same commanded pose therefore got two
        # different answers at STEP8 and STEP9, and the r_max drawn from it was drawn from a
        # mixture.
        #
        # The state is chosen, not mixed.  This check asks "may this pose be COMMANDED?", which is
        # the requirement Rs stated, so it evaluates the fully commanded state: the arm at the
        # solved joints and the fingers driven to this step's own command, settled the same way the
        # aim settles its prediction.  The other question -- whether the arm ACTUALLY clears the
        # table once everything has moved -- is a different question with its own reading, and the
        # per-step table clearance answers that one.
        _sv = mujoco.MjData(m)
        _sv.qpos[:] = d.qpos
        _sv.qvel[:] = 0.0
        _sv.ctrl[:] = d.ctrl
        for _k3, _a3 in enumerate(QADR[t]):
            _sv.qpos[_a3] = w[t][_k3]
        for _k3, _i3 in enumerate(AIDX[t]):
            _sv.ctrl[_i3] = w[t][_k3]
        _sv.ctrl[GIDX[t]] = lf if t == "L" else rf
        for _ in range(int(PREDICT_S / m.opt.timestep)):
            mujoco.mj_step(m, _sv)
        # ⚠ The jaw's own state is part of this reading and has to be visible in it.  The scratch
        # copies the LIVE qpos and overwrites only the arm joints, so the fingers are wherever the
        # run has them -- open at one step, squeezed on a cable at the next.  The four-bar moves
        # the mouth relative to the pinch as that changes, so two steps with the same arm pose and
        # the same commanded jaw can still read different tilts.  Printing the vector's LENGTH and
        # the pad gap beside the angle is what lets that be seen instead of deduced.
        _mv = slot_centre(t, _sv) - pinch(t, _sv)
        _mlen = float(np.linalg.norm(_mv)) * 1000.0
        _mpad, _mclaw = jaw_gaps(t, _sv)
        _down = _mv / max(1e-12, float(np.linalg.norm(_mv)))
        _off = math.degrees(math.acos(min(1.0, max(-1.0, float(-_down[2])))))
        # p11/p5 -614(3), three prints, because the tolerance is being argued over a number
        # nobody has measured yet.  (1) the angle prints on PASS as well as on failure, so the
        # margin is observed rather than inferred from the absence of a stop.  (2) the tool's own
        # orientation residual against the vertical it was commanded, so an empty window -- a
        # solve that cannot reach upright at all -- is visible as itself rather than as a tilt.
        # (3) the arm's lowest point at this upright pose, which turns the 10.5-to-14.6 degree
        # range into one number measured on the pose actually used.
        _lowest, _who3 = 1e9, ""
        for _g3 in ARMG[t]:
            _c3 = np.array(_sv.geom_xpos[_g3])
            if int(m.geom_type[_g3]) == int(mujoco.mjtGeom.mjGEOM_BOX):
                _R3 = np.array(_sv.geom_xmat[_g3]).reshape(3, 3)
                _b3 = min((_c3 + _R3 @ (np.array(k) * m.geom_size[_g3]))[2]
                          for k in [(a, b, c2) for a in (-1, 1) for b in (-1, 1) for c2 in (-1, 1)])
            else:
                _b3 = _c3[2] - float(m.geom_rbound[_g3])
            if _b3 < _lowest:
                _lowest, _who3 = _b3, (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, _g3)
                                       or f"geom{_g3}")
        _tool = np.array(_sv.xmat[TOOLB[t]]).reshape(3, 3)
        _tres = math.degrees(math.acos(min(1.0, max(-1.0, float(-_tool[2, 2])))))
        print(f"[steps] STEP{num} {t}: fingers {_off:4.1f} deg off straight down "
              f"(pinch->mouth [{_down[0]:+.3f} {_down[1]:+.3f} {_down[2]:+.3f}]), "
              f"allowance {VERTICAL_TOL_DEG:4.2f} deg -- margin {VERTICAL_TOL_DEG - _off:+5.2f}; "
              f"tool axis {_tres:4.1f} deg off vertical; pinch->mouth {_mlen:5.1f} mm with the "
              f"pads {_mpad:+6.2f} mm apart at the COMMANDED opening "
              f"{(lf if t == 'L' else rf):.0f}; lowest point {_who3} at "
              f"{(_lowest - TABLE_TOP)*1000:+6.1f} mm vs the table")
        if _off > VERTICAL_TOL_DEG:
            raise RuntimeError(
                f"STEP{num} {t}: the descent to a clip requires the fingers straight down, and "
                f"this pose has them {_off:.1f} deg off it, past the {VERTICAL_TOL_DEG:.1f} deg "
                f"this check allows.  Reported here rather than at the solve, because the pose "
                f"can also arrive by inheritance, which does not pass through the solve."
            )
    prev = w
    step_gap_path, step_gap_who = 1e9, ""   # smallest arm-to-arm gap DURING this step's move
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
    touched_early = set()   # arms that hit the cable before the fingers were allowed to move
    touched_any = set()     # and arms that touch it at all during this step
    opened_at = 0
    for s_ in range(steps):
        f = 0.5 - 0.5 * math.cos(math.pi * min(1.0, s_ / ramp))  # smooth start and stop
        # ⛔ EVERY step, not only the grasp.  I first put this inside `if not gate_open:`, which
        # is False for every step whose gate is not "grasp" -- so the check that exists to watch
        # the DESCENT never ran on the descent, and its silence proved nothing.  Same defect as
        # the ones it was built to catch.
        for t2 in SIDES:
            _hit = {g for g in touching(t2, d) if g.startswith("cab")}
            if _hit and t2 not in touched_early and not gate_open:
                touched_early.add(t2)
                print(f"[steps] ⛔ STEP{num} {t2}: arm touched the cable BEFORE the fingers moved "
                      f"-- {sorted(_hit)}")
            elif _hit and t2 not in touched_any:
                touched_any.add(t2)
                print(f"[steps] STEP{num} {t2}: arm in contact with the cable at "
                      f"t={s_*m.opt.timestep:.2f}s -- {sorted(_hit)}")
        if not gate_open:
            # ⛔ The approach must not disturb what it is approaching.  In the first run of the
            # rebuilt cell the cable moved 10-13 mm between being aimed at and being closed on,
            # and one jaw then jammed on it two steps later -- the failure surfaced far from its
            # cause.  Touching the cable with the arm before the fingers move is the cause, so it
            # is reported HERE, at the step that does it.
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
        for _cg, _cc, _cn in (("pinC1", C1, "C1"), ("pinC2", C2, "C2")):
            if gate == _cg and not d.eq_active[EQ[_cn]]:
                _lk, pp = seated_any(_cn, *_cc)
                if _lk is not None:
                    _aw = pin_to(_cn, _lk)
                    d.eq_active[EQ[_cn]] = 1
                    gates[_cg] = (f"t={n*m.opt.timestep:.2f}s cab{_lk} seat={np.round(pp, 4)} "
                                  f"anchor={np.round(_aw, 4)}")
                    # P2 (p11 -141, the one that matters while §0#5 is open): the whole claim
                    # that this pin does not teleport anything rests on the constraint being
                    # ALREADY SATISFIED when it turns on.  That is checkable in one line -- the
                    # two anchors are the same world point or they are not -- so it is checked
                    # rather than asserted, at the instant of engagement and again after the
                    # solver has had a step to act.  A residual here is a distance the cable would
                    # be pulled.
                    _e = EQ[_cn]
                    _cb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, _cn)
                    _a1 = (np.array(d.xpos[_cb])
                           + np.array(d.xmat[_cb]).reshape(3, 3) @ m.eq_data[_e][:3])
                    _bb = int(m.eq_obj2id[_e])
                    _a2 = (np.array(d.xpos[_bb])
                           + np.array(d.xmat[_bb]).reshape(3, 3) @ m.eq_data[_e][3:6])
                    _res0 = float(np.linalg.norm(_a1 - _a2))
                    # P5: where the anchor sits along the cable's own axis relative to the groove
                    # centre.  The pin holds the point it was given; if that point is off along x
                    # the cable is held beside the groove rather than in it, and the seat gate and
                    # the pin would be talking about different places.
                    _axial = float(_a1[0] - _cc[0])
                    print(f"[steps] {_cn} RETAINED cab{_lk} at t={n*m.opt.timestep:.2f}s "
                          f"(the link actually in the groove; the build-time guess was "
                          f"cab{SEAT1 if _cn == 'C1' else SEAT2})")
                    print(f"[steps] {_cn} PIN RESIDUAL at engagement {_res0*1000:6.3f} mm "
                          f"(the two anchors as world points -- anything here is a distance the "
                          f"cable would be pulled); anchor sits {_axial*1000:+6.1f} mm from the "
                          f"groove centre along the cable's own axis")
                    _pin_watch.append((_cn, n))
        mujoco.mj_step(m, d)
        n += 1
        for _cn2, _n0 in list(_pin_watch):
            if n - _n0 >= PIN_SETTLE_STEPS:
                _e2 = EQ[_cn2]
                _cb2 = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, _cn2)
                _p1 = (np.array(d.xpos[_cb2])
                       + np.array(d.xmat[_cb2]).reshape(3, 3) @ m.eq_data[_e2][:3])
                _b2 = int(m.eq_obj2id[_e2])
                _p2 = (np.array(d.xpos[_b2])
                       + np.array(d.xmat[_b2]).reshape(3, 3) @ m.eq_data[_e2][3:6])
                print(f"[steps] {_cn2} PIN RESIDUAL after {PIN_SETTLE_STEPS} steps "
                      f"{float(np.linalg.norm(_p1 - _p2))*1000:6.3f} mm")
                _pin_watch.remove((_cn2, _n0))
        if n % 40 == 0:
            for t2 in SIDES:
                sv = sigma_min(t2)
                # p11 -106 (3): the bar for a path-sigma test has to come from measurement, not
                # from a round number.  So trace it -- every sample, per arm, with the step it
                # falls in.  ⛔ Measurement only: nothing here changes what the arms do.
                # p11 -108: the bar is not on sigma but on the translational block's
                # ||dq||/||dx|| [rad/m] -- how much joint motion a metre of tool motion costs.
                # It is 1/sigma of that block, so it is taken from the same decomposition.
                _jp = np.zeros((3, m.nv))
                mujoco.mj_jacBody(m, d, _jp, None, TOOLB[t2])
                _sv3 = np.linalg.svd(_jp[:, VADR[t2]], compute_uv=False)
                _amp = float(1.0 / max(_sv3[-1], 1e-12))       # rad per metre, worst direction
                sigma_trace.append((num, t2, n * m.opt.timestep, sv, _amp))
                if sv < sig_min[t2]:
                    sig_min[t2], sig_where[t2] = sv, f"STEP{num} t={n*m.opt.timestep:.1f}s"
                cg, cgw = column_gap(t2, want_who=True)
                if cg is not None and cg < col_min[t2]:
                    col_min[t2] = cg
                    col_where[t2] = f"{cgw}, STEP{num} t={n*m.opt.timestep:.1f}s"
            # p5 -137 / p11 -138, print (2): the clearance is enforced on the poses that were
            # solved, and the arms travel between them.  Endpoints are silent about the path, so
            # the smallest gap reached WHILE moving is tracked here rather than inferred from the
            # two ends of each move.
            _pp, _pw = arm_pair_min(d, want_who=True)
            if _pp is not None:
                # and WHERE, because a path minimum that disagrees with both endpoints is either a
                # real transient or a broken instrument, and a bare number cannot say which.
                if _pp < step_gap_path:
                    step_gap_path, step_gap_who = _pp, f"{_pw} at t={n*m.opt.timestep:.2f}s"
                arm_gap_path = min(arm_gap_path, _pp)
        if n % 20 == 0:
            # pZ CLAMP-1 v0.3a: the question is whether the PATH to the grip passed through a
            # configuration the real hardware cannot reach, so track the minimum over the window,
            # not the value at the end.  A negative minimum means the claws interpenetrated.
            for t in SIDES:
                _p, _c = jaw_gaps(t)
                claw_min[t] = min(claw_min[t], _c)
        if n % render_every == 0:
            # ⛔ The wide camera used to swing +-14 degrees continuously here.  Rs, watching the
            # video to judge whether a hand clamps: the left panel wobbles, and that gets in the
            # way of judging.  It served no measurement purpose -- a moving viewpoint cannot make
            # a grip easier to see, only harder -- and making the evidence judge-fit is the job of
            # whoever produces it, which is me.  The camera is fixed now.
            renderer.update_scene(d, camera=cam)
            a_img = renderer.render()
            # The close panel follows the hands, which it has to in order to stay on them, but it
            # is smoothed so it drifts instead of jittering between frames.
            _want = 0.5 * (pinch("L") + pinch("R"))
            cam2.lookat[:] = _want if n <= render_every else (0.85 * np.array(cam2.lookat) + 0.15 * _want)
            renderer.update_scene(d, camera=cam2)
            _b_img = renderer.render()
            renderer.update_scene(d, camera=cam3)
            frames.append(np.hstack([a_img, _b_img, renderer.render()]))
            # Rs, 2026-07-28: watch it WHILE it runs.  The finished file is only written when the
            # loop ends, half an hour later, and the log says the run has failed about ten minutes
            # in -- so the wait bought nothing and cost the feedback it was supposed to carry.
            # This writes a second, fragmented file as the frames arrive, which is playable before
            # the run is over.  The finished file below is untouched, so what gets judged at the
            # end is the same artifact in the same format it has always been.
            live_write(frames[-1])
    # The same block for the first grasp AND for the re-grasp.  It used to fire only at the first:
    # Rs watched the re-grasp fail in the video while the log had nothing to say about it beyond
    # `grip=L-`, because the one part that fails was the one part with no measurement.  p18 cleared
    # this as measurement, which is p4's court -- no control changes here, only instruments.
    if gate in ("grasp", "regrasp"):
        grasp_diagnostics(gate, w, aim_seat, aim_cable, gates)
    le = np.linalg.norm(pinch("L") - tgt["L"]) * 1000
    re_ = np.linalg.norm(pinch("R") - tgt["R"]) * 1000
    p1, p2 = np.array(d.xpos[CAB[SEAT1]]), np.array(d.xpos[CAB[SEAT2]])
    row = (f"STEP{num:2d} {name:12s} t={n*m.opt.timestep:5.1f}s L={le:6.1f}mm R={re_:6.1f}mm "
           f"c1[y{p1[1]:+.3f} z{p1[2]-TABLE_TOP:+.3f}] c2[y{p2[1]:+.3f} z{p2[2]-TABLE_TOP:+.3f}] "
           f"pin={'C1' if d.eq_active[EQ['C1']] else '--'}/{'C2' if d.eq_active[EQ['C2']] else '--'} "
           f"grip={'L' if held('L') else '-'}{'R' if held('R') else '-'}")   # R6 conjunction
    _cgl, _cwl = column_gap("L", want_who=True)
    _cgr, _cwr = column_gap("R", want_who=True)
    _inside = [v for v in (_cgl, _cgr) if v is not None and v < 0]
    print(f"[steps] STEP{num:2d} sigma_min L={sigma_min('L'):.4f} R={sigma_min('R'):.4f}"
          f"  mast L={gap_mm(_cgl)} ({_cwl}) R={gap_mm(_cgr)} ({_cwr})"
          f"{'   <- INSIDE THE MAST' if _inside else ''}")
    gc1 = np.array([C1[0], C1[1], GROOVE_Z])
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
        worst_, who_, bot_ = -1e9, "", 0.0
        for g_ in ARMG[t]:
            c_ = np.array(d.geom_xpos[g_])
            if int(m.geom_type[g_]) == int(mujoco.mjtGeom.mjGEOM_BOX):
                Rg_ = np.array(d.geom_xmat[g_]).reshape(3, 3)
                bot = min((c_ + Rg_ @ (np.array(k) * m.geom_size[g_]))[2]
                          for k in [(a, b, c2) for a in (-1, 1) for b in (-1, 1) for c2 in (-1, 1)])
            else:
                bot = c_[2] - float(m.geom_rbound[g_])
            if sc_[2] - bot > worst_:
                worst_, who_, bot_ = sc_[2] - bot, (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM,
                                                                     g_) or f"geom{g_}"), bot
        # Rs, 2026-07-28: the fingers must not hit the table on the way to a clip.  "Below the
        # mouth" cannot answer that -- it is measured from a mouth that is itself moving down.
        # The table is what the requirement is about, so the height above the table is what the
        # line reports, and a negative number means the arm is THROUGH it.
        _clear = (bot_ - TABLE_TOP) * 1000.0
        low.append(f"{t} {worst_*1000:5.1f} mm below the mouth ({who_}), "
                   f"{_clear:+6.1f} mm vs the table"
                   f"{' <- THROUGH THE TABLE' if _clear < 0 else ''}")
    print(f"[steps] STEP{num:2d} ARM REACH: " + " | ".join(low))
    # p11 -150 B, and the other half of the pair whose A is the gate.  The gate reads the state
    # about to be COMMANDED, at solve time; this reads what the arms and fingers actually ended up
    # in, at the end of the step.  Their difference is the commanded-to-realised gap itself, which
    # neither reading can report alone -- and mixing them, which is what the check used to do,
    # reports neither.  ⚠ Reported, not gated: nothing stops because of this line, and the bound
    # it would be gated against -- how far the arm may tilt before it reaches the table -- is not
    # this pane's to set.
    _real = []
    for t in SIDES:
        _rv = slot_centre(t) - pinch(t)
        _rn = _rv / max(1e-12, float(np.linalg.norm(_rv)))
        _rt = math.degrees(math.acos(min(1.0, max(-1.0, float(-_rn[2])))))
        _rp, _ = jaw_gaps(t)
        _real.append(f"{t} {_rt:4.1f} deg off straight down, pads {_rp:+6.2f} mm")
    print(f"[steps] STEP{num:2d} AS REALISED: " + " | ".join(_real)
          + "   (the gate read the commanded state at solve time; this is what the step ended in)")
    # Rs, 2026-07-28: the arms look like they are hitting each other, and even when they are not
    # they are too close.  Everything measuring this so far has been a yes/no -- touching() returns
    # a set of contacts, so "clear" covers a millimetre and a metre alike, and a warning that
    # cannot say how close cannot say it is getting worse.  So: the smallest signed distance
    # between any geom of one arm and any geom of the other, and the pair it belongs to.
    _pairmin, _pairwho = arm_pair_min(d, want_who=True)
    # ⛔ There were TWO of these, and the second had no guard.  I added the guarded form and left
    # the original sitting under it, so the run crashed on the first step where nothing was within
    # the search radius -- the exact case the guard was written for.  A guard placed BESIDE the
    # thing it guards is not a guard; it has to replace it.
    if _pairmin is not None:
        arm_gap_min = min(arm_gap_min, _pairmin)
    # (4) the realised clearance, beside (3) the predicted one: their difference IS the following
    # error the constant is currently missing, so printing them apart would leave it to be
    # reconstructed.  (2) rides along, because a pair that only meets mid-move is invisible here.
    _pred_txt = []
    for t in SIDES:
        if t in CLEARANCE_REPORT:
            _dr, _kept, _nfa, _wsv, _dsv, _rm, _mx, _psv, _cdr = CLEARANCE_REPORT[t]
            _mast = f"; the mast removed {_cdr}"
            if _nfa is None:
                _pred_txt.append(
                    f"{t}: the winning pose cleared the whole {ARM_DECIDE_CUTOFF*1000:.0f} mm "
                    f"search radius; clearance removed {_dr} of {_dr + _kept} candidates, "
                    f"{_rm} of them roomy, winner sigma {_wsv:.4f} (best survivor {_psv:.4f}) vs best dropped "
                    + (f"{_dsv:.4f}" if _dsv is not None else "none dropped") + _mast)
            else:
                _pred_txt.append(
                    f"{t}: clearance removed {_dr} of {_dr + _kept} candidates, winner predicted "
                    f"{gap_mm(_nfa)}, winner sigma {_wsv:.4f} (best survivor {_psv:.4f}) vs best dropped "
                    + (f"{_dsv:.4f}" if _dsv is not None else "none dropped")
                    + f"; {_rm} candidates cleared the whole {ARM_DECIDE_CUTOFF*1000:.0f} mm "
                      f"search radius"
                    + (f", widest inside it {gap_mm(_mx)}" if _mx is not None else "") + _mast)
    _worst = min(arm_gap_min, arm_gap_path)
    print(f"[steps] STEP{num:2d} ARM-TO-ARM: "
          + (f"closest {gap_mm(_pairmin)} ({_pairwho})"
             f"{'  <- TOUCHING OR THROUGH' if _pairmin <= 0 else ''}"
             if _pairmin is not None else
             f"nothing within the {ARM_PAIR_CUTOFF*1000:.0f} mm search radius at rest")
          + (f"   along the move {gap_mm(step_gap_path)} ({step_gap_who})"
             if step_gap_who else "   nothing within the radius during the move")
          + (f"   worst so far {gap_mm(_worst)}" if _worst < 1e8 else
             "   nothing within the radius yet, this run")
          + "   ⚠ measured between the two arms only; posts, table and cable are not in this")
    if _pred_txt:
        print(f"[steps] STEP{num:2d} CLEARANCE: " + " | ".join(_pred_txt)
              + f" ; realised at rest {gap_mm(_pairmin)}"
              + " (predicted minus realised = the following error the constant does not carry)")
    print(f"[steps] STEP{num:2d} CARRY: " + " | ".join(carry))
    _stx, _sty, _stz = seat_tolerances()
    print(f"[steps] STEP{num:2d} C1 SEAT: nearest point ON THE CABLE (cab{_k1} at {_u1:.2f}) misses "
          f"the groove centre by "
          f"({miss1[0]:+6.1f},{miss1[1]:+6.1f},{miss1[2]:+6.1f}) mm "
          f"(gate wants |dx|<{_stx*1000:.0f} |dy|<{_sty*1000:.1f} |dz|<{_stz*1000:.0f} mm, "
          f"read from the gate itself, AND clip-cable contact)")
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
    print(f"[steps] WORST {t}: mast "
          + (f"{gap_mm(col_min[t])} at {col_where[t]}"
             f"{'   <- INSIDE THE MAST' if col_min[t] < 0 else ''}"
             if col_min[t] < 1e8 else "never came within the search radius this run"))
print(f"[steps] gates: {gates}")
if _live is not None:
    _live.close()
    print(f"[steps] watch-along file closed: {LIVE_OUT} {LIVE_OUT.stat().st_size} bytes")
import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=VIDEO_QUALITY, macro_block_size=None)
# hand p11 the path, not a summary of it
_tr = S / "sigma_trace.txt"
with open(_tr, "w") as _f:
    # ⛔ WHY THE sigma_min COLUMN MUST NOT BECOME A BAR (p11 -112).  It is kept for ranking and
    # for envelope work, where comparing two arms of identical construction is valid because the
    # scale factors cancel.  It CANNOT carry an absolute threshold: the Jacobian block it comes
    # from mixes radians and metres, so a number like "sigma >= 0.12" is a quantity nobody has.
    # That is not hypothetical -- the 0.12 floor that used to sit here was above one arm's ENTIRE
    # range, so it rejected every pose that arm could reach.  The bar belongs on the rad/m column.
    _f.write("# sigma_min: RANKING ONLY -- mixed units, never an absolute bar.  Bar goes on"
             " dq_per_dx_rad_per_m.\n")
    _f.write("step arm t_s sigma_min dq_per_dx_rad_per_m\n")
    for _st, _a, _t, _sv, _am in sigma_trace:
        _f.write(f"{_st} {_a} {_t:.4f} {_sv:.6f} {_am:.3f}\n")
print(f"[steps] sigma trace: {len(sigma_trace)} samples -> {_tr}")
for _a in SIDES:
    _v = [x[3] for x in sigma_trace if x[1] == _a]
    _w = [x[4] for x in sigma_trace if x[1] == _a]
    if _v:
        _v2 = sorted(_v)
        print(f"[steps] sigma {_a}: min {min(_v):.4f}  p5 {_v2[len(_v2)//20]:.4f}  "
              f"median {_v2[len(_v2)//2]:.4f}  max {max(_v):.4f}  over {len(_v)} samples")
        _w2 = sorted(_w)
        print(f"[steps] dq/dx {_a}: median {_w2[len(_w2)//2]:8.1f}  p95 "
              f"{_w2[int(len(_w2)*0.95)]:8.1f}  max {max(_w):8.1f} rad/m")

print(f"[steps] wrote {OUT} frames={len(frames)} {OUT.stat().st_size} bytes")
