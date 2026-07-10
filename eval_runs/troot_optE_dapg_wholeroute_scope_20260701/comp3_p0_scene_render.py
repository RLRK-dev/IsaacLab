# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 fold-3 VISUAL leg: env flag-ON settled P0 vs the golden recording P0 -- side-by-side render.

Rs adjudication material for G-F1b (support-clip A/B): make the clip-suspended (env as-coded) vs
table-resting (recording) cable difference VISIBLE (%12 dispatch 11:32, Rs「動画で確認できていない」).

Method (offline visualization ONLY -- no physics stepped after the pose write; the offline-replay
exception): build the flag-ON env once on CPU (world_count=1), then render TWO configurations of the
SAME mj_model with the SAME cameras:
  row 1 = env as-built settled P0 (mj_data as stepped by the build: cable RIDES the support clips);
  row 2 = the golden recording's frame-0 qpos (route_demo_raw.npz arm_q[0], 74 coords = arm 0:28 +
          cable 28:74) written into a fresh MjData + mj_forward: the recording's table-resting cable.
  ⚠ the support-clip STATICS are part of the env model so they appear in BOTH rows; the RECORDING's
  actual scene has NO support clips (run.log scene inventory) -- row 2 shows the recording's CABLE
  POSITION inside the env scene, annotated accordingly.
Views: overview / side (Z-height reads) / support-clip zoom (cable<->clip contact region).

Output: PNG panels -> ~/Downloads (Rs-discoverable comp3_p0_scene_env_vs_recording_*.png) + evidence
copies under eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_p0_scene_visual/.

Run (CPU physics; EGL offscreen GL):
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_p0_scene_render.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", (
    "comp3_p0_scene_render is a no-GPU-compute probe: run with CUDA_VISIBLE_DEVICES='' (empty)"
)
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.pop("DISPLAY", None)  # reference-mujoco-headless-egl: BadWindow guard

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT_DIR = _EVAL_DIR / "comp3_p0_scene_visual"
DOWNLOADS = Path.home() / "Downloads"
W, H = 960, 720

# (label, lookat, azimuth, elevation, distance)
VIEWS = [
    ("overview", (0.30, 0.10, 0.82), 100, -25, 0.85),
    ("side_z_read", (0.30, 0.10, 0.81), 0, -5, 0.55),
    ("clip_zoom", (0.30, 0.05, 0.815), 120, -15, 0.18),
]


def _render_config(m, d, renderer):
    """Render all VIEWS of one (model, data) config. Returns {label: np.ndarray HxWx3}."""
    out = {}
    for label, lookat, az, el, dist in VIEWS:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.azimuth = az
        cam.elevation = el
        cam.distance = dist
        renderer.update_scene(d, camera=cam)
        out[label] = renderer.render().copy()
    return out


def main():
    print("[p0-render] building flag-ON env (world_count=1, cpu) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
        },
    )
    m = env._solver.mj_model
    d_env = env._solver.mj_data  # settled P0 as stepped by the build (cable clip-suspended)
    mujoco.mj_forward(m, d_env)

    z = np.load(GOLDEN_NPZ)
    q0 = np.asarray(z["arm_q"][0], dtype=float).copy()  # recording frame-0 FULL joint_q (arm 0:28 + cable 28:74)
    assert int(m.nq) == len(q0), f"qpos layout mismatch: mj nq={int(m.nq)} vs recording {len(q0)}"
    # quat-convention fix (self-check run 1 caught the cable invisible): the recording is NEWTON joint_q --
    # FREE-root quat XYZW (w LAST) -- while the mujoco free-joint qpos quat is w FIRST. Reorder per FREE joint.
    for j in range(int(m.njnt)):
        if int(m.jnt_type[j]) == int(mujoco.mjtJoint.mjJNT_FREE):
            adr = int(m.jnt_qposadr[j])
            xyzw = q0[adr + 3 : adr + 7].copy()
            q0[adr + 3 : adr + 7] = [xyzw[3], xyzw[0], xyzw[1], xyzw[2]]  # -> wxyz
    d_rec = mujoco.MjData(m)
    d_rec.qpos[:] = q0
    mujoco.mj_forward(m, d_rec)  # pose-only visualization; NO stepping (offline-replay exception)

    m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
    renderer = mujoco.Renderer(m, height=H, width=W)

    imgs_env = _render_config(m, d_env, renderer)
    imgs_rec = _render_config(m, d_rec, renderer)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    label_h = 36
    saved = []
    for label, *_ in [(v[0],) for v in VIEWS]:
        top, bot = imgs_env[label], imgs_rec[label]
        canvas = Image.new("RGB", (W, 2 * H + 2 * label_h), "black")
        dr = ImageDraw.Draw(canvas)
        dr.text(
            (10, 8),
            f"ENV flag-ON settled P0 (as-coded: support clips -> cable CLIP-SUSPENDED) [{label}]",
            fill="yellow",
        )
        canvas.paste(Image.fromarray(top), (0, label_h))
        dr.text(
            (10, H + label_h + 8),
            f"RECORDING frame-0 qpos in the SAME model (table-resting cable z~0.804; the real recording "
            f"scene has NO support clips) [{label}]",
            fill="cyan",
        )
        canvas.paste(Image.fromarray(bot), (0, H + 2 * label_h))
        fname = f"comp3_p0_scene_env_vs_recording_{label}_20260710.png"
        for dst in (DOWNLOADS / fname, OUT_DIR / fname):
            canvas.save(dst)
        saved.append(fname)
        print(f"[p0-render] saved {fname} -> ~/Downloads + {OUT_DIR.name}/")
    print(f"[p0-render] DONE: {len(saved)} side-by-side panels ({', '.join(v[0] for v in VIEWS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
