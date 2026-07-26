# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause
"""p4 observation harness: render the POSITION-servo (PD) arm motion, no kinematic.

Wraps ``_physics_step_all`` (armpd_probe lineage) and renders every K-th physics frame with the
mujoco Renderer on the solver's live mj_data, so the arm / hand / fingers are drawn. Runs under
ARM_PD_DRIVE=1 (controller drive). If the P0 convergence gate raises, the frames captured up to
that point are still written -- the motion they show is servo-driven either way.
Physical-validity judgment = Rs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_WT = Path(__file__).resolve().parent / "wt_pd"
_TIL = _WT / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ["MUJOCO_GL"] = "egl"
for _k in ("ARM_XML_ACT_NEUTRALIZE", "ARM_PD_STALE_CTRL"):
    os.environ.pop(_k, None)
os.environ["ARM_PD_DRIVE"] = "1"
os.environ["ARM_PD_GAINS_SCALE"] = "1.0"
os.environ["ARM_PD_RAMP_FRAMES"] = "0"

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/rlrk/Downloads/pd_arm_servo.mp4")
EVERY = int(os.environ.get("RENDER_EVERY", "8"))
MAXF = int(os.environ.get("MAX_FRAMES", "600"))
REC = _WT / "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz"
if not REC.exists():
    REC = Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz")

import mujoco  # noqa: E402
import numpy as np  # noqa: E402

np.random.seed(0)
import imageio.v2 as imageio  # noqa: E402
import warp as wp  # noqa: E402

import newton_route_env as nre  # noqa: E402

W, H = 960, 720
_state = {"renderer": None, "n": 0, "frames": []}


def _render(env):
    if _state["renderer"] is None:
        m = env._solver.mj_model
        m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
        m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
        # brighten: the default headlight leaves the scene near-black in EGL offscreen
        m.vis.headlight.ambient[:] = [0.6, 0.6, 0.6]
        m.vis.headlight.diffuse[:] = [0.8, 0.8, 0.8]
        m.vis.headlight.specular[:] = [0.3, 0.3, 0.3]
        _state["renderer"] = mujoco.Renderer(m, height=H, width=W)
    r = _state["renderer"]
    d = env._solver.mj_data

    # The UR5e link bodies carry ZERO geoms in the compiled model (nmesh=0), so the solid arm
    # cannot be drawn. Turn on the joint / body-frame visualization so the arm's structure and
    # motion ARE visible; the gripper claws and the cable/clips have geoms and draw normally.
    m = env._solver.mj_model
    opt = mujoco.MjvOption()
    mujoco.mjv_defaultOption(opt)
    opt.flags[mujoco.mjtVisFlag.mjVIS_JOINT] = False
    opt.flags[mujoco.mjtVisFlag.mjVIS_ACTUATOR] = False
    opt.frame = mujoco.mjtFrame.mjFRAME_NONE
    m.vis.scale.jointlength = 0.12
    m.vis.scale.jointwidth = 0.02
    m.vis.scale.framelength = 0.09
    m.vis.scale.framewidth = 0.012

    # frame on the ARM bodies only (ids 1..6 = left arm links, 15..20 = right arm links)
    arm_ids = [i for i in list(range(1, 7)) + list(range(15, 21)) if i < m.nbody]
    P = np.asarray([d.xpos[i] for i in arm_ids], dtype=float)
    ctr = (P.min(0) + P.max(0)) / 2.0
    dist = max(float(np.max(P.max(0) - P.min(0))) * 1.7, 1.0)
    ee = list(np.asarray(d.xpos[6], dtype=float))  # left wrist_3

    # ---- ARM OVERLAY -------------------------------------------------------------------------
    # The UR5e link bodies carry no geoms, so the links are drawn here as capsules spanning the
    # REAL body origins reported by the physics (d.xpos). Nothing is written into the sim; this
    # is visualization only, and it shows where the links actually are.
    L_ARM = [1, 2, 3, 4, 5, 6]  # shoulder -> upper_arm -> forearm -> wrist_1/2/3 (left)
    R_ARM = [15, 16, 17, 18, 19, 20]  # same chain (right)
    L_GRIP = [7, 8, 9, 10, 11, 12, 13, 14]
    R_GRIP = [21, 22, 23, 24, 25, 26, 27, 28]

    def _link(sc, p0, p1, rad, rgba):
        if sc.ngeom >= sc.maxgeom:
            return
        g = sc.geoms[sc.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.zeros(9), np.asarray(rgba, dtype=np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, rad, np.asarray(p0, dtype=float), np.asarray(p1, dtype=float))
        sc.ngeom += 1

    def _draw_arms(sc):
        for chain, rad, rgba in (
            (L_ARM, 0.042, [0.55, 0.60, 0.68, 1.0]),
            (R_ARM, 0.042, [0.55, 0.60, 0.68, 1.0]),
            (L_GRIP, 0.014, [0.95, 0.55, 0.15, 1.0]),
            (R_GRIP, 0.014, [0.95, 0.55, 0.15, 1.0]),
        ):
            for a, b in zip(chain[:-1], chain[1:]):
                if a < m.nbody and b < m.nbody:
                    pa, pb = d.xpos[a], d.xpos[b]
                    if float(np.linalg.norm(np.asarray(pb) - np.asarray(pa))) > 1e-4:
                        _link(sc, pa, pb, rad, rgba)
        # base pedestals: drop a post from each shoulder to the table top
        for j in (1, 15):
            if j < m.nbody:
                p = np.asarray(d.xpos[j], dtype=float)
                _link(sc, [p[0], p[1], 0.80], p, 0.05, [0.35, 0.35, 0.38, 1.0])

    def shot(lookat, az, el, dd):
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.azimuth = az
        cam.elevation = el
        cam.distance = dd
        r.update_scene(d, camera=cam, scene_option=opt)
        _draw_arms(r.scene)
        return r.render()

    wide = shot(list(ctr), 215, -20, dist)  # both arms fully in frame
    hand = shot(ee, 200, -22, 0.95)  # hand / finger close-up on the left wrist
    return np.hstack([wide, hand])


_orig = nre.NewtonRouteEnv._physics_step_all


def _wrapped(self, *a, **k):
    out = _orig(self, *a, **k)
    _state["n"] += 1
    if _state["n"] % EVERY == 0 and len(_state["frames"]) < MAXF:
        try:
            wp.synchronize()
            _state["frames"].append(_render(self))
        except Exception as e:  # noqa: BLE001
            print(f"[render] skipped frame: {e}")
    return out


nre.NewtonRouteEnv._physics_step_all = _wrapped

err = None
env = None
try:
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(REC),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
        },
    )
except RuntimeError as e:  # P0 convergence gate
    err = str(e)
    print(f"[p4] env build raised (frames kept): {e}")

if env is not None:
    try:
        import torch

        env.INIT_XY_NOISE = 0.0
        env.reset()
        wp.synchronize()
        zero = torch.zeros((1, 6), dtype=torch.float32)
        for _ in range(300):
            if len(_state["frames"]) >= MAXF:
                break
            _obs, _r, dones, _x = env.step(zero)
            if bool(dones[0]):
                break
    except Exception as e:  # noqa: BLE001
        err = f"{err} | route: {e}" if err else f"route: {e}"
        print(f"[p4] route phase stopped: {e}")

frames = _state["frames"]
print(f"[p4] physics frames seen={_state['n']}  rendered={len(frames)}")
if not frames:
    print("[p4] NO FRAMES")
    raise SystemExit(2)

OUT.parent.mkdir(parents=True, exist_ok=True)
imageio.mimwrite(str(OUT), frames, fps=30, quality=8, macro_block_size=None)
print(f"[p4] wrote {OUT}  frames={len(frames)}  size={OUT.stat().st_size}")
if err:
    print(f"[p4] NOTE: {err}")
