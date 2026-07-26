#!/usr/bin/env python3
"""UR15 + Robotiq 2F-85 driven by POSITION servos in MuJoCo -- no kinematic writes.

Arm: UR15 URDF generated from the official Universal_Robots_ROS2_Description (ur_type:=ur15),
torque limits from its joint_limits.yaml, rotor inertia at the official UR5e MJCF reference.
Gripper: the proven Robotiq 2F-85 MJCF (4-bar loops as equality constraints + coupling tendon),
attached at the UR tool flange. The fingers are driven by their own actuator.
Every pose in the video is the result of integrating the physics. Judgment = Rs.
"""

from __future__ import annotations

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
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/rlrk/Downloads/ur15_grip.mp4")

ARMATURE, DAMP = 0.1, 1.0
KP_ARM, KP_WRI, KVR = 10000.0, 1200.0, 0.06
J = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
EFFORT = np.array([433.0, 433.0, 204.0, 70.0, 70.0, 70.0])

# ---- arm spec (from the URDF we generated) ------------------------------------------------------
x = (S / "ur15_base.xml").read_text()
for j in J:
    x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)
kps = np.array([KP_ARM] * 3 + [KP_WRI] * 3)
kvs = kps * KVR
act = "\n  <actuator>\n" + "\n".join(
    f'    <position name="{j}_act" joint="{j}" kp="{kps[i]:.1f}" kv="{kvs[i]:.1f}" '
    f'forcerange="{-EFFORT[i]:.1f} {EFFORT[i]:.1f}" ctrlrange="-6.3 6.3"/>' for i, j in enumerate(J)
) + "\n  </actuator>\n"
vis = """
  <visual>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.75 0.75 0.75" specular="0.25 0.25 0.25"/>
    <global offwidth="1280" offheight="960"/>
    <map znear="0.02"/>
  </visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.20 0.22 0.26" rgb2="0.26 0.28 0.33"
             width="512" height="512"/>
    <material name="gridmat" texture="grid" texrepeat="10 10" reflectance="0.05"/>
  </asset>
"""
floor = '    <geom name="floor" type="plane" size="5 5 0.1" material="gridmat" pos="0 0 -0.9" contype="0" conaffinity="0"/>\n'
x = x.replace("<worldbody>", vis + "  <worldbody>\n" + floor, 1)
x = x.replace("</mujoco>", act + "</mujoco>")
(S / "ur15_arm_for_attach.xml").write_text(x)

arm = mujoco.MjSpec.from_file(str(S / "ur15_arm_for_attach.xml"))
grip = mujoco.MjSpec.from_file(GRIP_XML)

# UR tool flange: wrist_3_link -> flange (rpy 0,-pi/2,-pi/2) -> tool0 (rpy pi/2,0,pi/2)
R = Rotation.from_euler("xyz", [0, -np.pi / 2, -np.pi / 2]) * Rotation.from_euler("xyz", [np.pi / 2, 0, np.pi / 2])
q = R.as_quat()  # x,y,z,w
quat = [float(q[3]), float(q[0]), float(q[1]), float(q[2])]  # mujoco wants w,x,y,z

wrist3 = arm.body("wrist_3_link")
frame = wrist3.add_frame(pos=[0.0, 0.0, 0.0], quat=quat)
frame.attach_body(grip.body("base_mount"), "grip_", "")
print("[ur15] gripper attached at the tool flange")

m = arm.compile()
m.opt.timestep = 0.002
d = mujoco.MjData(m)
names_a = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
print(f"[ur15] nq={m.nq} nu={m.nu} ngeom={m.ngeom} nmesh={m.nmesh}")
print(f"[ur15] actuators={names_a}")
GRIP_A = [i for i, n in enumerate(names_a) if n and "finger" in n]
ARM_A = [i for i, n in enumerate(names_a) if n and n.endswith("_act")]
grip_range = m.actuator_ctrlrange[GRIP_A[0]] if GRIP_A else np.array([0.0, 255.0])
print(f"[ur15] arm actuators={ARM_A}  gripper actuator={GRIP_A} range={grip_range}")

# ---- motion programme: reach, close fingers, lift, traverse, open ---------------------------------
OPEN, CLOSE = float(grip_range[0]), float(grip_range[1])
WAY = [
    ((0.00, -1.57, 0.00, -1.57, 0.00, 0.00), OPEN),
    ((0.75, -1.15, 1.25, -1.65, -1.57, 0.00), OPEN),
    ((0.75, -0.78, 1.62, -2.40, -1.57, 0.00), OPEN),
    ((0.75, -0.78, 1.62, -2.40, -1.57, 0.00), CLOSE),
    ((0.75, -1.15, 1.25, -1.65, -1.57, 0.00), CLOSE),
    ((-0.85, -1.15, 1.25, -1.65, -1.57, 1.10), CLOSE),
    ((-0.85, -0.78, 1.62, -2.40, -1.57, 1.10), CLOSE),
    ((-0.85, -0.78, 1.62, -2.40, -1.57, 1.10), OPEN),
    ((-0.85, -1.15, 1.25, -1.65, -1.57, 1.10), OPEN),
    ((0.00, -1.57, 0.00, -1.57, 0.00, 0.00), OPEN),
]
HOLD_S, FPS, W, H = 1.8, 30, 1280, 960

qadr = [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in J]
for k, a in enumerate(qadr):
    d.qpos[a] = WAY[0][0][k]
for k, i in enumerate(ARM_A):
    d.ctrl[i] = WAY[0][0][k]
if GRIP_A:
    d.ctrl[GRIP_A[0]] = OPEN
mujoco.mj_forward(m, d)


_gb = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, i) for i in range(m.nbody)]
_cand = [i for i, nm in enumerate(_gb) if nm and "grip_base" == nm] or [i for i, nm in enumerate(_gb) if nm and nm.startswith("grip_")]
GRIP_BODY = _cand[0] if _cand else m.nbody - 1
print(f"[ur15] close-up follows body #{GRIP_BODY} = {_gb[GRIP_BODY]}")

renderer = mujoco.Renderer(m, height=H, width=W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.0, 0.0, 0.45]
cam.distance = 2.6
cam.elevation = -14

frames, errs = [], []
steps = int(HOLD_S / m.opt.timestep)
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
n = 0
for tgt, g in WAY[1:]:
    for k, i in enumerate(ARM_A):
        d.ctrl[i] = tgt[k]
    if GRIP_A:
        d.ctrl[GRIP_A[0]] = g
    for _ in range(steps):
        mujoco.mj_step(m, d)
        n += 1
        if n % render_every == 0:
            cam.azimuth = 130 + 30.0 * np.sin(n * 0.0011)
            renderer.update_scene(d, camera=cam)
            wide = renderer.render()
            # close-up that follows the gripper so the fingers are clearly visible
            cam2 = mujoco.MjvCamera()
            cam2.type = mujoco.mjtCamera.mjCAMERA_FREE
            cam2.lookat[:] = d.xpos[GRIP_BODY]
            cam2.distance = 0.42
            cam2.elevation = -12
            cam2.azimuth = cam.azimuth + 35.0
            renderer.update_scene(d, camera=cam2)
            near = renderer.render()
            frames.append(np.hstack([wide, near]))
    errs.append(float(np.max(np.abs(np.array([d.qpos[a] for a in qadr]) - np.array(tgt)))))

print(f"[ur15] frames={len(frames)} sim={n*m.opt.timestep:.1f}s")
print("[ur15] per-waypoint final |q-target| [mrad]:", [round(e * 1000, 2) for e in errs])
print(f"[ur15] WORST arm steady-state error = {max(errs)*1000:.2f} mrad ({np.degrees(max(errs)):.3f} deg)")

import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=8, macro_block_size=None)
print(f"[ur15] wrote {OUT} {OUT.stat().st_size} bytes")
