#!/usr/bin/env python3
"""UR15 driven by a POSITION servo in MuJoCo -- every pose comes from integrating the physics.

No kinematic writes: the controller sets joint TARGETS, the actuators produce torque bounded by
the UR15 datasheet limits, and the arm arrives (or does not). Rotor inertia (armature) matches the
official UR5e MJCF reference value. Physical-validity judgment = Rs.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco  # noqa: E402
import numpy as np  # noqa: E402

S = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/scratchpad")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/rlrk/Downloads/ur15_pd.mp4")
ARMATURE = float(os.environ.get("ARMATURE", "0.1"))  # official ur5e.xml reference
KP_ARM, KP_WRI, KVR, DAMP = 10000.0, 1200.0, 0.06, 1.0

J = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
EFFORT = np.array([433.0, 433.0, 204.0, 70.0, 70.0, 70.0])  # UR15 joint_limits.yaml

x = (S / "ur15_base.xml").read_text()
for j in J:
    x = re.sub(rf'(<joint[^>]*name="{j}")', rf'\1 armature="{ARMATURE}" damping="{DAMP}"', x)

kps = np.array([KP_ARM] * 3 + [KP_WRI] * 3)
kvs = kps * KVR
act = "\n  <actuator>\n" + "\n".join(
    f'    <position name="{j}_act" joint="{j}" kp="{kps[i]:.1f}" kv="{kvs[i]:.1f}" '
    f'forcerange="{-EFFORT[i]:.1f} {EFFORT[i]:.1f}" ctrlrange="-6.3 6.3"/>'
    for i, j in enumerate(J)
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
(S / "ur15_final.xml").write_text(x)

m = mujoco.MjModel.from_xml_path(str(S / "ur15_final.xml"))
m.opt.timestep = 0.002
d = mujoco.MjData(m)
print(f"[ur15] nq={m.nq} nu={m.nu} nmesh={m.nmesh} armature={ARMATURE} kp={KP_ARM}/{KP_WRI} kv/kp={KVR}")

WAY = [
    (0.00, -1.57, 0.00, -1.57, 0.00, 0.00),
    (0.75, -1.15, 1.25, -1.65, -1.57, 0.00),
    (0.75, -0.78, 1.62, -2.40, -1.57, 0.00),
    (0.75, -1.15, 1.25, -1.65, -1.57, 0.00),
    (-0.85, -1.15, 1.25, -1.65, -1.57, 1.10),
    (-0.85, -0.78, 1.62, -2.40, -1.57, 1.10),
    (-0.85, -1.15, 1.25, -1.65, -1.57, 1.10),
    (0.00, -1.57, 0.00, -1.57, 0.00, 0.00),
]
HOLD_S, FPS, W, H = 2.0, 30, 1280, 960

d.qpos[:] = WAY[0]
d.ctrl[:] = WAY[0]
mujoco.mj_forward(m, d)

renderer = mujoco.Renderer(m, height=H, width=W)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:] = [0.0, 0.0, 0.45]
cam.distance = 2.6
cam.elevation = -14

frames, errs, sat = [], [], 0
steps_per_wp = int(HOLD_S / m.opt.timestep)
render_every = max(1, int(round(1.0 / (FPS * m.opt.timestep))))
n = 0
for wp_i in range(1, len(WAY)):
    tgt = np.array(WAY[wp_i])
    d.ctrl[:] = tgt
    for _ in range(steps_per_wp):
        mujoco.mj_step(m, d)
        n += 1
        sat += int(np.any(np.abs(d.actuator_force) >= EFFORT * 0.999))
        if n % render_every == 0:
            cam.azimuth = 130 + 30.0 * np.sin(n * 0.0011)
            renderer.update_scene(d, camera=cam)
            frames.append(renderer.render())
    errs.append(float(np.max(np.abs(d.qpos[:6] - tgt))))

print(f"[ur15] frames={len(frames)} steps={n} sim={n*m.opt.timestep:.1f}s saturated={100.0*sat/n:.1f}% of steps")
print("[ur15] per-waypoint final |q-target| [mrad]:", [round(e * 1000, 2) for e in errs])
print(f"[ur15] WORST steady-state joint error = {max(errs)*1000:.2f} mrad ({np.degrees(max(errs)):.3f} deg)")

import imageio.v2 as imageio  # noqa: E402

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=FPS, quality=8, macro_block_size=None)
print(f"[ur15] wrote {OUT} {OUT.stat().st_size} bytes")
