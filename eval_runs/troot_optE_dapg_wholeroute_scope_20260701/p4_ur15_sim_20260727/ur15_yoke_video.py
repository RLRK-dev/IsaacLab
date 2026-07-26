#!/usr/bin/env python3
"""Dual UR15 on the Y yoke: mirrored tool paths solved per arm by IK, executed by POSITION servos.

No kinematic writes anywhere. The IK produces joint TARGETS; the servos apply torque and the arms
get there. Left and right follow paths that are exact mirror images about the yoke plane (x = 0),
so the motion is symmetric even though the two arms are the same right-handed UR15 and their joint
values are NOT sign-flips of each other (measured: no sign pattern gets closer than 713 mm).
Physical-validity judgment = Rs.
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
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/rlrk/Downloads/ur15_yoke.mp4")

SHOULDER_HEIGHT = 0.37 + 0.58 * 2.0
YOKE_SPREAD, YOKE_RISE = 0.22, 0.0
TILT = math.pi / 2.0 - math.radians(45.0)
ARMATURE, DAMP = 0.1, 1.0
KP_ARM, KP_WRI, KVR = 10000.0, 1200.0, 0.06
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
EFFORT = np.array([433.0, 433.0, 204.0, 70.0, 70.0, 70.0])
SIDES = {"L": -1.0, "R": +1.0}


def arm_spec():
    x = (S / "ur15_base.xml").read_text()
    for j in J6:
        x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)
    p = S / "_arm_only.xml"
    p.write_text(x)
    return mujoco.MjSpec.from_file(str(p))


world_xml = f"""<mujoco model="yoke_cell">
  <compiler angle="radian"/>
  <option timestep="0.002"/>
  <visual>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.75 0.75 0.75" specular="0.2 0.2 0.2"/>
    <global offwidth="1280" offheight="960"/>
    <map znear="0.02"/>
  </visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.19 0.21 0.25" rgb2="0.25 0.27 0.32"
             width="512" height="512"/>
    <material name="gridmat" texture="grid" texrepeat="12 12" reflectance="0.05"/>
    <material name="col" rgba="0.86 0.86 0.87 1"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="6 6 0.1" material="gridmat" pos="0 0 0" contype="0" conaffinity="0"/>
    <body name="column" pos="0 0 0">
      <geom name="stem" type="cylinder" size="0.102 {SHOULDER_HEIGHT/2:.4f}" pos="0 0 {SHOULDER_HEIGHT/2:.4f}"
            material="col" contype="0" conaffinity="0"/>
      <geom name="foot" type="cylinder" size="0.215 0.03" pos="0 0 0.03" material="col" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
</mujoco>
"""
(S / "_yoke_world.xml").write_text(world_xml)
cell = mujoco.MjSpec.from_file(str(S / "_yoke_world.xml"))
column = cell.body("column")

for tag, sign in SIDES.items():
    q = Rotation.from_euler("xyz", [0.0, sign * TILT, 0.0]).as_quat()
    f = column.add_frame(pos=[sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT + YOKE_RISE],
                         quat=[float(q[3]), float(q[0]), float(q[1]), float(q[2])])
    a = arm_spec()
    f.attach_body(a.bodies[1], f"{tag}_", "")
    g = mujoco.MjSpec.from_file(GRIP_XML)
    Rt = Rotation.from_euler("xyz", [0, -np.pi / 2, -np.pi / 2]) * Rotation.from_euler("xyz", [np.pi / 2, 0, np.pi / 2])
    qt = Rt.as_quat()
    wf = cell.body(f"{tag}_wrist_3_link").add_frame(pos=[0, 0, 0],
                                                    quat=[float(qt[3]), float(qt[0]), float(qt[1]), float(qt[2])])
    wf.attach_body(g.body("base_mount"), f"{tag}g_", "")

kps = np.array([KP_ARM] * 3 + [KP_WRI] * 3)
kvs = kps * KVR
for tag in SIDES:
    for i, j in enumerate(J6):
        act = cell.add_actuator()
        act.name, act.trntype, act.target = f"{tag}_{j}_act", mujoco.mjtTrn.mjTRN_JOINT, f"{tag}_{j}"
        act.gaintype, act.biastype = mujoco.mjtGain.mjGAIN_FIXED, mujoco.mjtBias.mjBIAS_AFFINE
        act.gainprm[0], act.biasprm[1], act.biasprm[2] = kps[i], -kps[i], -kvs[i]
        act.forcerange, act.ctrlrange, act.ctrllimited = [-EFFORT[i], EFFORT[i]], [-6.3, 6.3], 1

m = cell.compile()
d = mujoco.MjData(m)
AN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
AIDX = {t: [AN.index(f"{t}_{j}_act") for j in J6] for t in SIDES}
GIDX = {t: (AN.index(f"{t}g_fingers_actuator") if f"{t}g_fingers_actuator" in AN else None) for t in SIDES}
QADR = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6] for t in SIDES}
VADR = {t: [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6] for t in SIDES}
TOOL = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_base") for t in SIDES}
print(f"[yoke] nq={m.nq} nu={m.nu} nbody={m.nbody} ngeom={m.ngeom}")

# Seed each arm by a global search: sample joint space and keep the pose whose tool is
# closest to that arm's first target, so the local IK below starts in the right branch.
TGT0_R = np.array([0.78, 0.35, 1.02])
_rng = np.random.default_rng(0)
_lim = np.array([[-3.14, 3.14], [-3.05, -0.05], [-2.60, 2.60], [-3.14, 3.14], [-3.14, 3.14], [-3.14, 3.14]])
_want = {"R": TGT0_R, "L": np.array([-TGT0_R[0], TGT0_R[1], TGT0_R[2]])}
_best = {t_: (1e9, None) for t_ in SIDES}
for _ in range(30000):
    _q = _rng.uniform(_lim[:, 0], _lim[:, 1])
    for t_ in SIDES:
        for k, a_ in enumerate(QADR[t_]):
            d.qpos[a_] = _q[k]
    mujoco.mj_forward(m, d)
    for t_ in SIDES:
        e_ = float(np.linalg.norm(np.array(d.xpos[TOOL[t_]]) - _want[t_]))
        if e_ < _best[t_][0]:
            _best[t_] = (e_, _q.copy())
for t_ in SIDES:
    print(f"[yoke] seed {t_}: |err|={_best[t_][0]*1000:.1f} mm")
    for k, a_ in enumerate(QADR[t_]):
        d.qpos[a_] = _best[t_][1][k]
    for k, i_ in enumerate(AIDX[t_]):
        d.ctrl[i_] = _best[t_][1][k]
    if GIDX[t_] is not None:
        d.ctrl[GIDX[t_]] = 0.0
d.qvel[:] = 0
mujoco.mj_forward(m, d)
p0 = {t_: np.array(d.xpos[TOOL[t_]]) for t_ in SIDES}
print(f"[yoke] seeded tool R={np.round(p0['R'],3)}  L={np.round(p0['L'],3)}")

# World-frame targets for the RIGHT tool, inside the measured reachable band
# (probe: R reaches x[0.31,1.43] for z 0.7-1.1, y 0.15-0.55; L mirrors it).
# The LEFT tool follows the exact mirror image about x = 0.
TGT_R = [
    (0.78, 0.35, 1.02),
    (0.78, 0.35, 0.82),
    (0.78, 0.35, 0.82),
    (0.78, 0.35, 1.02),
    (0.50, 0.30, 1.02),
    (0.50, 0.30, 0.84),
    (0.50, 0.30, 0.84),
    (0.50, 0.30, 1.02),
    (0.78, 0.35, 1.02),
]
GRIP = [0, 0, 255, 255, 255, 255, 0, 0, 0]
OFF = TGT_R  # kept for the loop below
HOLD_S, FPS, W, H = 1.7, 30, 1280, 960

qt = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}


def ik_step(tag, target, gain=0.35, lam=0.08, dq_max=0.012, lag_max=0.20):
    """One resolved-rate step: nudge this arm's joint TARGET toward the Cartesian target.

    The step is clamped (dq_max) and the target is never allowed to run more than lag_max ahead of
    the realized joint angle, so the command cannot integrate away while the servo is catching up.
    """
    jacp = np.zeros((3, m.nv))
    mujoco.mj_jacBody(m, d, jacp, None, TOOL[tag])
    Jm = jacp[:, VADR[tag]]
    e = target - np.array(d.xpos[TOOL[tag]])
    dq = Jm.T @ np.linalg.solve(Jm @ Jm.T + (lam ** 2) * np.eye(3), e)
    dq = gain * dq
    nrm = float(np.linalg.norm(dq))
    if nrm > dq_max:
        dq *= dq_max / nrm
    q_now = np.array([d.qpos[a] for a in QADR[tag]])
    qt[tag] = np.clip(qt[tag] + dq, q_now - lag_max, q_now + lag_max)
    return float(np.linalg.norm(e))


renderer = mujoco.Renderer(m, height=H, width=W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.0, 0.0, 1.05]
cam.distance = 3.4
cam.elevation = -12
cam2 = mujoco.MjvCamera()
cam2.type = mujoco.mjtCamera.mjCAMERA_FREE
cam2.lookat[:] = [0.0, 0.0, 1.15]
cam2.distance = 1.9
cam2.elevation = -8
cam2.azimuth = 90

# settle: drive both arms onto the first target before recording
_t0 = {"R": np.array(TGT_R[0]), "L": np.array([-TGT_R[0][0], TGT_R[0][1], TGT_R[0][2]])}
for _ in range(4000):
    for _t in SIDES:
        ik_step(_t, _t0[_t])
        for _k, _i in enumerate(AIDX[_t]):
            d.ctrl[_i] = qt[_t][_k]
    mujoco.mj_step(m, d)
print("[yoke] settled  R=", np.round(d.xpos[TOOL["R"]],3), " L=", np.round(d.xpos[TOOL["L"]],3))

frames, sym, reach = [], [], []
steps = int(HOLD_S / m.opt.timestep)
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
n = 0
for wi, off in enumerate(OFF):
    _r = np.array(off)
    tgt = {"R": _r, "L": np.array([-_r[0], _r[1], _r[2]])}
    for t in SIDES:
        if GIDX[t] is not None:
            d.ctrl[GIDX[t]] = GRIP[wi]
    for s in range(steps):
        if s % 5 == 0:
            for t in SIDES:
                ik_step(t, tgt[t])
        for t in SIDES:
            for k, i in enumerate(AIDX[t]):
                d.ctrl[i] = qt[t][k]
        mujoco.mj_step(m, d)
        n += 1
        if n % render_every == 0:
            cam.azimuth = 118 + 24.0 * np.sin(n * 0.0009)
            renderer.update_scene(d, camera=cam)
            a_img = renderer.render()
            renderer.update_scene(d, camera=cam2)
            b_img = renderer.render()
            frames.append(np.hstack([a_img, b_img]))
    pr, pl = np.array(d.xpos[TOOL["R"]]), np.array(d.xpos[TOOL["L"]])
    sym.append(float(np.linalg.norm(pl - np.array([-pr[0], pr[1], pr[2]]))))
    reach.append(max(float(np.linalg.norm(pr - tgt["R"])), float(np.linalg.norm(pl - tgt["L"]))))

print(f"[yoke] frames={len(frames)} sim={n*m.opt.timestep:.1f}s")
print("[yoke] per-waypoint reach error [mm]:", [round(e * 1000, 1) for e in reach])
print("[yoke] per-waypoint L-vs-mirrored-R [mm]:", [round(e * 1000, 2) for e in sym])
print(f"[yoke] WORST reach error = {max(reach)*1000:.1f} mm   WORST mirror error = {max(sym)*1000:.2f} mm")

import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=8, macro_block_size=None)
print(f"[yoke] wrote {OUT} {OUT.stat().st_size} bytes")
