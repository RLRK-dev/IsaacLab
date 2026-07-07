# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""SRG S0 claw-zoom offscreen render (§運用14 visual sanity leg, no-GPU CPU).

Rebuilds the SRG S0 headline cell (koshape N4_F00) via srg_probe.build_koshape_pinch + grasp_cable
(the PROVEN r_s66 cradle grasp), then renders CLAW-ZOOM frames of the HELD grasp from the CPU
mujoco.Renderer on the built mj_model/mj_data — to confirm engaged=True is a REAL pad-cradle-on-cable,
NOT an 空中close (numeric-grasp-unreliable lesson). CPU render (MUJOCO_GL=egl headless); no CUDA compute.
"""
import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("NEWTON_DEVICE", "cpu")
os.environ.setdefault("MUJOCO_GL", "egl")  # headless offscreen (memory: egl + no DISPLAY)
os.environ.pop("DISPLAY", None)

import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import mujoco  # noqa: E402
import srg_probe as S  # noqa: E402
import task_config as C  # noqa: E402
import test_newton_clip_routing as T  # noqa: E402
import warp as wp  # noqa: E402
from newton_skill_env_base import DT  # noqa: E402

SCRATCH = "/tmp/claude-1000/-home-rlrk-IsaacLab/377de041-042a-48b2-9f0d-e96422c545ec/scratchpad"
DOWNLOADS = os.path.expanduser("~/Downloads")
H, W = 900, 1200


def main():
    wp.init()
    T.SIM_SUBSTEPS, T.SIM_DT = 4, DT / 4  # the N4 regime (headline 1.29um/f cell)
    env = S.build_koshape_pinch("N4F0_render")
    ssot = S._live_production_contact_ssot()
    S.d1_contact_readback(env, ssot)  # fail-closed: same representative build as the measured cell
    state, engaged, ncon_max = S.grasp_cable(env)
    print(f"[RENDER] grasp engaged={engaged} ncon_max_close={ncon_max}")

    m, d = env["solver"].mj_model, env["solver"].mj_data
    mujoco.mj_forward(m, d)  # sync geom_xpos from the stepped mj_data (ar_close_dir pattern)

    # lookat = the grasped cable segment nearest the R grasp center (gx, yr); robust cradle center.
    bq = state.body_q.numpy()
    cidx = np.array(env["cable_bodies"])
    gx, yr = C.GRASP_X, C.WIDE_RIGHT_Y
    dists = (bq[cidx][:, 0] - gx) ** 2 + (bq[cidx][:, 1] - yr) ** 2
    seg = int(np.argmin(dists))
    lookat = [float(bq[cidx[seg]][0]), float(bq[cidx[seg]][1]), float(bq[cidx[seg]][2])]
    print(f"[RENDER] cradle lookat (R grasp seg) = {[round(v, 4) for v in lookat]}")

    # The default offscreen framebuffer is 640x480 (koshape XML sets no <global offwidth>). Bump the
    # model's offscreen buffer so the claw-zoom renders at H x W; fall back to 640x480 if the GL context
    # rejects it.
    global H, W
    try:
        m.vis.global_.offwidth = W
        m.vis.global_.offheight = H
        renderer = mujoco.Renderer(m, height=H, width=W)
    except Exception as exc:  # noqa: BLE001
        print(f"[RENDER] offbuffer bump failed ({exc}); falling back to 640x480")
        H, W = 480, 640
        renderer = mujoco.Renderer(m, height=H, width=W)

    def cam(az, el, dist):
        c = mujoco.MjvCamera()
        c.lookat[:] = lookat
        c.distance = dist
        c.azimuth = az
        c.elevation = el
        return c

    # scene options: (vis) default groups; (col) collision claws only (hide visual meshes group 2).
    opt_vis = mujoco.MjvOption()
    opt_col = mujoco.MjvOption()
    for gi in range(len(opt_col.geomgroup)):
        opt_col.geomgroup[gi] = 0
    opt_col.geomgroup[0] = 1  # f1ext/f2ext claws (group 0)
    opt_col.geomgroup[3] = 1  # pad_box1/2 collision (group 3)

    shots = [
        ("zoom_side_x", cam(0, -18, 0.085), opt_vis),
        ("zoom_downcable_y", cam(90, -12, 0.085), opt_vis),
        ("zoom_3q", cam(40, -25, 0.095), opt_vis),
        ("zoom_col_side", cam(0, -18, 0.075), opt_col),
        ("zoom_col_3q", cam(40, -25, 0.085), opt_col),
        ("context", cam(45, -20, 0.35), opt_vis),
    ]
    saved = []
    for name, c, opt in shots:
        renderer.update_scene(d, camera=c, scene_option=opt)
        img = renderer.render()
        nonblack = float((img.sum(axis=2) > 15).mean())  # fraction of non-near-black px
        p = os.path.join(SCRATCH, f"srg_s0_N4F0_{name}.png")
        Image.fromarray(img).save(p)
        saved.append((name, p, round(nonblack, 3)))
        print(f"[RENDER] {name}: {p} nonblack_frac={nonblack:.3f}")
    renderer.close()

    print("\n[RENDER] saved:")
    for name, p, nb in saved:
        print(f"  {name}: nonblack={nb} -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
