# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""P-D1 video leg: deterministic re-run visualization of the v1.2 evidence runs (R0/R1/R2).

Renders the comp3-proven way (mujoco Renderer on the solver's live mj_data mirror, two free
cameras hstacked) while re-running the run's exact flags, and CROSS-CHECKS faithfulness per RL
step against the banked evidence npz (`bq_steps`): the max body_q deviation is printed and written
to a sidecar json, and the video is labeled a REPLAY VISUALIZATION (GPU nondeterminism means it is
a re-run, not the evidence bytes; the sidecar quantifies the gap). Physical-validity judgment = Rs.

Usage (env_isaaclab7, CVD pinned):
    ... armpd_video.py --mode r2 --evidence-npz <run>/armpd_frames_r2v12_pd.npz --out ~/Downloads/pd1_r2_replay.mp4
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_TIL = _SCRIPTS.parent
_REPO = _TIL.parent
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("MUJOCO_GL", "egl")

_GOLDEN = (
    _REPO
    / "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
    / "w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz"
)

MODES = {
    "r0": {},  # contaminated kinematic baseline
    "r1": {"ARM_XML_ACT_NEUTRALIZE": "1"},  # clean kinematic (L-P0)
    "r2": {"ARM_PD_DRIVE": "1", "ARM_PD_GAINS_SCALE": "1.0", "ARM_PD_RAMP_FRAMES": "0"},  # PD nominal
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=tuple(MODES), required=True)
    ap.add_argument("--episode-steps", type=int, default=900)
    ap.add_argument("--recording", default=str(_GOLDEN))
    ap.add_argument("--evidence-npz", required=True, help="the banked run's armpd_frames_*.npz (bq_steps cross-check)")
    ap.add_argument("--out", required=True, help="output mp4 path")
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()

    for _k in ("ARM_PD_DRIVE", "ARM_XML_ACT_NEUTRALIZE", "ARM_PD_GAINS_SCALE", "ARM_PD_RAMP_FRAMES", "ARM_PD_STALE_CTRL"):
        os.environ.pop(_k, None)
    os.environ.update(MODES[a.mode])

    import mujoco
    import numpy as np

    np.random.seed(0)
    import torch
    import warp as wp

    import newton_route_env as nre

    ev = np.load(a.evidence_npz)
    ev_bq = np.asarray(ev["bq_steps"])  # [steps, nbody, 7]
    n_steps = min(int(a.episode_steps), ev_bq.shape[0])

    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(a.recording),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
            # route_c1_pin: REMOVED (Rs 2026-07-19 kinematic complete-removal)
        },
    )
    env.INIT_XY_NOISE = 0.0
    env.reset()
    wp.synchronize()

    m = env._solver.mj_model
    d = env._solver.mj_data
    W, H = 960, 720
    m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
    renderer = mujoco.Renderer(m, height=H, width=W)

    def render(lookat, az, el, dist):
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.azimuth = az
        cam.elevation = el
        cam.distance = dist
        renderer.update_scene(d, camera=cam)
        return renderer.render()

    frames_dir = Path(a.out).with_suffix("")
    frames_dir = frames_dir.parent / (frames_dir.name + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("*.png"):
        old.unlink()

    import imageio.v2 as imageio

    zero = torch.zeros((1, 6), dtype=torch.float32)
    max_dev = 0.0
    done_at = None
    for t in range(n_steps):
        obs, rew, dones, extras = env.step(zero)
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        if t < ev_bq.shape[0]:
            n = min(bq.shape[0], ev_bq.shape[1])
            max_dev = max(max_dev, float(np.max(np.abs(bq[:n, :3] - ev_bq[t, :n, :3]))))
        ctx = render([0.35, 0.0, 0.90], 232, -22, 1.2)  # front-oblique context (comp3 lineage)
        sec = render([0.37, 0.0, 0.86], 0, -12, 0.7)  # Y-Z section (slot/groove view)
        imageio.imwrite(frames_dir / f"f{t:05d}.png", np.hstack([ctx, sec]))
        if bool(dones[0]):
            done_at = t
            break

    n_frames = len(list(frames_dir.glob("*.png")))
    subprocess.run(
        [
            "ffmpeg", "-y", "-r", str(a.fps), "-i", str(frames_dir / "f%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(a.out),
        ],
        check=True,
        capture_output=True,
    )
    sidecar = {
        "mode": a.mode,
        "label": "REPLAY VISUALIZATION (deterministic re-run; NOT the evidence bytes)",
        "evidence_npz": str(a.evidence_npz),
        "frames": n_frames,
        "done_at": done_at,
        "max_bodyq_pos_dev_vs_evidence_m": max_dev,
        "cameras": "ctx az232/el-22 d1.2 lookat[0.35,0,0.90] | yz az0/el-12 d0.7 lookat[0.37,0,0.86]",
    }
    Path(str(a.out) + ".json").write_text(json.dumps(sidecar, indent=2))
    print(json.dumps(sidecar, indent=2))
    print(f"[armpd_video] wrote {a.out} ({n_frames} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
