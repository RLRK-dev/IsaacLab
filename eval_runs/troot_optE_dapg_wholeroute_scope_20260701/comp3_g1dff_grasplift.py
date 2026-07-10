# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 D rho=0 acceptance run: G1 harness on the OFFICIAL feedforward drive mode (no monkeypatch).

Rs GO 23:5x (D acceptance): identical G1 config with cfg route_drive_mode='feedforward' -- the formalized
env path (cdac6b6972: RouteExecutor.apply_recorded_arm_ff + drive-loop branch), NOT a probe-level bypass.
Acceptance bar = armqdirect-equivalent (c2045a9a1a): both arms lift_rise PASS / symmetric axial settling /
taut inter-claw span. Known convention delta vs the armqdirect probe: the official mode indexes frames at
cf[t]+sub_i (grip-consistent) where the probe used +1 -- a <=1-frame / <=1.14mm bound; this run is the
empirical face of that delta (if it diverges, re-check the index convention FIRST per rule 15).

Original G1 spec below (world-0 / align / grasp+lift only / videos / Rs human-GT final):

Runs the route env AS-CODED (device cuda:0 = warp arrays on cuda:0, mujoco-CPU newton stepping -- the R3
production substrate, SAME substrate the recording ran on) with grasp_actuation=True + g1_scene_align=True
(Rs adjudication A: no support clips, cable at the recording's start Y), world_count=1 (world-0 nominal),
ZERO policy actions (residual 0 -> the commanded targets are exactly the recorded waypoints; the gripper
replays the recorded grip_cmd staircase per physics frame).

SCOPE (G-F3 gate redefinition): GRASP + LIFT legs ONLY. The loop STOPS before the first G3 (C1-route/seat)
step -- C1-seat onward is NOT DRIVEN and NOT judged. Verdict = SRG-style per-axis creep budget (lateral /
z-drop vs env DROP margins + retention + contact debounce) + lift-rise leg. GROVE 2.2 conservatism
direction stated per axis in the result JSON. LOUD preconditions recorded: mjw-eq-deferred (G1 runs the
CPU-substrate mj_model-authoritative config; any future GPU-cg leg needs the mjw eq re-poke first) +
/production-launch-gate NON-APPLICABLE (GPU << 10h + explicit Rs approval 2026-07-10).

⚠ The numeric legs NEVER constitute a standalone PASS: the final grasp verdict = Rs human-GT on the videos
(numeric-grasp-unreliable lesson). This runner emits NUMERIC_GO_CANDIDATE / NUMERIC_NOGO only.

Video leg: per-RL-step offscreen renders (context + claw zoom) -> mp4 (ffmpeg) -> ~/Downloads
(Rs-discoverable comp3_g1_grasplift_*.mp4) + eval_runs evidence copies + intra-finger slip time-series in
the result JSON.

Run (cuda:0 pinned in the shell layer; MUJOCO_GL=egl for offscreen render):
    CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_g1_grasplift.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "0", (
    "G1 runs the as-coded substrate on cuda:0 ONLY (device-pinned in the shell layer); got "
    f"{os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')!r}"
)
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.pop("DISPLAY", None)

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402
import torch  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
# retry naming (lane-floor fix chain): run-1 artifacts (comp3_g1_grasplift_result.json + its mp4s) are the
# banked FAIL evidence (Rs human-GT) -- the retry writes distinct names instead of clobbering them.
OUT_JSON = _EVAL_DIR / "comp3_g1dff_grasplift_result.json"
FRAMES_DIR = _EVAL_DIR / "comp3_g1dff_frames"
VIDEO_DIR = _EVAL_DIR / "comp3_g1_videos"
DOWNLOADS = Path.home() / "Downloads"
W, H = 960, 720
FPS = 10  # 1 rendered frame per RL step (10 physics frames) -> real-time-ish playback

# SRG-style budget constants (env DROP margins; service window mirrors SRG W_svc).
W_SVC_FRAMES = 9000
LAT_MARGIN_M = 0.060  # env DROP_LATERAL_DEV_MAX_M
ZDROP_MARGIN_M = 0.010  # env DROP_LIFT_MARGIN_M
CONTACT_DEBOUNCE = 8  # env DROP_CONTACT_LOSS_DEBOUNCE
LIFT_RISE_MIN_M = 0.040  # env LIFT_RISE_MIN_M
CLOSE_LATCH_Q = 0.6  # driver q past cage90 (0.667 commanded) => cage latched

_DRV_L = [6, 10]
_DRV_R = [20, 24]


def _pad_and_cable_geoms(m):
    pads, cables = [], []
    for g in range(m.ngeom):
        gname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or "").lower()
        if "pad" in (gname + bname):
            pads.append(g)
        elif int(m.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_CAPSULE) and int(m.geom_bodyid[g]) != 0:
            cables.append(g)
    return set(pads), set(cables)


def _pad_cable_contacts(d, pads, cables):
    n = 0
    for i in range(int(d.ncon)):
        pair = {int(d.contact[i].geom1), int(d.contact[i].geom2)}
        if pair & pads and pair & cables:
            n += 1
    return n


def _render(renderer, d, lookat, az, el, dist):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = lookat
    cam.azimuth = az
    cam.elevation = el
    cam.distance = dist
    renderer.update_scene(d, camera=cam)
    return renderer.render()


def main():
    print("[DFF] building flag-ON + g1_scene_align env (world_count=1, device=cuda:0 as-coded substrate) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",  # D rho=0 official mode (cdac6b6972) -- the acceptance object
        },
    )
    m = env._solver.mj_model
    d = env._solver.mj_data
    pads, cables = _pad_and_cable_geoms(m)
    m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
    renderer = mujoco.Renderer(m, height=H, width=W)
    FRAMES_DIR.mkdir(exist_ok=True)
    for old in FRAMES_DIR.glob("*.png"):
        old.unlink()

    env.reset()
    aq0 = env._arm_q_start[0]
    cable_ids = env._cable_bodies[0]
    rest_z = float(np.mean(env._state_0.body_q.numpy()[cable_ids, 2]))  # settled table-resting reference

    series = {
        "t": [],
        "phase": [],
        "l_drv_q": [],
        "r_drv_q": [],
        "pad_cable_contacts": [],
        "held_z_l": [],
        "held_z_r": [],
        "slip_l_mm": [],
        "slip_r_mm": [],  # per-axis [dx, dy, dz] vs latch offset, mm
    }
    latch_t = None
    held_l = held_r = None
    off_l = off_r = None
    loss_streak = 0
    max_loss_streak = 0
    done_early = None
    zero = torch.zeros((1, 6), dtype=torch.float32)

    t = 0
    while True:
        _, phase_peek, _, _ = env._route.step_target(t)
        if phase_peek >= 2:
            print(f"[G1] STOP before t={t}: next phase = G3 (C1-seat onward EXCLUDED per G-F3)")
            break
        _, _, dones, _ = env.step(zero)
        if bool(dones[0]):
            # done-step fix: env.step() resets done worlds BEFORE returning, so any state read past this
            # point is POST-RESET contamination (the t=132 row in the first G1 run) -- record the
            # termination loud and DROP the row (the pre-reset state is not recoverable here).
            done_early = t
            print(f"[G1] EARLY DONE at t={t} (drop/explosion/termination) -- row DROPPED (post-reset state)")
            break
        import warp as wp

        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        jq = env._state_0.joint_q.numpy()
        l_q = [float(jq[aq0 + i]) for i in _DRV_L]
        r_q = [float(jq[aq0 + i]) for i in _DRV_R]
        claw_l = nre.clamp_pos_ko(bq[nre._LEFT_EE_BODY][:3], bq[nre._LEFT_EE_BODY][3:7])
        claw_r = nre.clamp_pos_ko(bq[nre._RIGHT_EE_BODY][:3], bq[nre._RIGHT_EE_BODY][3:7])
        cable_pos = bq[cable_ids, :3]
        ncon_pc = _pad_cable_contacts(d, pads, cables)

        if latch_t is None and min(l_q) > CLOSE_LATCH_Q and min(r_q) > CLOSE_LATCH_Q and ncon_pc > 0:
            latch_t = t
            held_l = int(np.argmin(np.linalg.norm(cable_pos - claw_l, axis=1)))
            held_r = int(np.argmin(np.linalg.norm(cable_pos - claw_r, axis=1)))
            off_l = cable_pos[held_l] - claw_l
            off_r = cable_pos[held_r] - claw_r
            print(f"[G1] CLOSE LATCH at t={t}: held segs L={held_l} R={held_r}, pad-cable contacts={ncon_pc}")

        series["t"].append(t)
        series["phase"].append(int(phase_peek))
        series["l_drv_q"].append(round(min(l_q), 4))
        series["r_drv_q"].append(round(min(r_q), 4))
        series["pad_cable_contacts"].append(int(ncon_pc))
        if latch_t is not None:
            slip_l = (cable_pos[held_l] - claw_l) - off_l
            slip_r = (cable_pos[held_r] - claw_r) - off_r
            series["slip_l_mm"].append([round(float(x) * 1e3, 3) for x in slip_l])
            series["slip_r_mm"].append([round(float(x) * 1e3, 3) for x in slip_r])
            series["held_z_l"].append(round(float(cable_pos[held_l, 2]), 5))
            series["held_z_r"].append(round(float(cable_pos[held_r, 2]), 5))
            loss_streak = loss_streak + 1 if ncon_pc == 0 else 0
            max_loss_streak = max(max_loss_streak, loss_streak)

        # video leg: 1 frame per RL step, context + claw zoom (tracks the claw midpoint).
        mid = 0.5 * (np.asarray(claw_l) + np.asarray(claw_r))
        ctx = _render(renderer, d, (0.30, 0.10, 0.85), 100, -20, 0.9)
        zoom = _render(renderer, d, tuple(mid), 120, -12, 0.16)
        from PIL import Image

        Image.fromarray(ctx).save(FRAMES_DIR / f"ctx_{t:04d}.png")
        Image.fromarray(zoom).save(FRAMES_DIR / f"zoom_{t:04d}.png")

        if t % 40 == 0:
            print(f"[G1] t={t} phase={phase_peek} drv L={min(l_q):.3f} R={min(r_q):.3f} pad-cable={ncon_pc}")
        t += 1

    # ---- verdict legs (numeric; NEVER a standalone PASS -- Rs human-GT is final) ----
    result = {"legs": {}, "series": series, "numeric_verdict": None}
    n_post = len(series["slip_l_mm"])
    legs = result["legs"]
    legs["no_early_termination"] = {"pass": done_early is None, "done_at": done_early}
    legs["close_latched"] = {"pass": latch_t is not None, "latch_t": latch_t, "held_l": held_l, "held_r": held_r}
    if latch_t is not None and n_post > 8:
        sl = np.asarray(series["slip_l_mm"], dtype=float)
        sr = np.asarray(series["slip_r_mm"], dtype=float)
        frames = np.arange(n_post) * 10.0  # physics frames since latch
        budget = {}
        for name, arr in (("L", sl), ("R", sr)):
            for ax, margin in (("x_lateral", LAT_MARGIN_M * 1e3), ("z_drop", ZDROP_MARGIN_M * 1e3)):
                col = {"x_lateral": 0, "z_drop": 2}[ax]
                v = arr[:, col] if ax == "x_lateral" else -arr[:, col]  # z_drop = downward slip positive
                v = np.abs(v) if ax == "x_lateral" else np.maximum(v, 0.0)
                rate = float(np.polyfit(frames, v, 1)[0]) if n_post > 1 else 0.0
                extrap = max(rate, 0.0) * W_SVC_FRAMES + float(v[-1])
                budget[f"{name}_{ax}"] = {
                    "end_mm": round(float(v[-1]), 3),
                    "rate_mm_per_frame": round(rate, 6),
                    "extrap_w_svc_mm": round(extrap, 2),
                    "margin_mm": margin,
                    "within": bool(extrap < margin),
                }
            budget[f"{name}_y_axial_end_mm"] = round(float(arr[-1, 1]), 3)  # benign axis, recorded
        legs["creep_budget"] = {"pass": all(v["within"] for k, v in budget.items() if isinstance(v, dict)), **budget}
        rise_l = float(series["held_z_l"][-1]) - rest_z
        rise_r = float(series["held_z_r"][-1]) - rest_z
        legs["lift_rise"] = {
            "pass": rise_l >= LIFT_RISE_MIN_M and rise_r >= LIFT_RISE_MIN_M,
            "rise_l_m": round(rise_l, 4),
            "rise_r_m": round(rise_r, 4),
            "min_m": LIFT_RISE_MIN_M,
        }
        legs["contact_retention"] = {
            "pass": max_loss_streak < CONTACT_DEBOUNCE,
            "max_contact_loss_streak": max_loss_streak,
            "debounce": CONTACT_DEBOUNCE,
        }
    ok = all(v.get("pass") for v in legs.values())
    result["numeric_verdict"] = "NUMERIC_GO_CANDIDATE" if ok else "NUMERIC_NOGO"
    result["conservatism_grove22"] = {
        "substrate": "NEUTRAL -- same substrate as the recording runner (mujoco-CPU newton, warp cuda:0);"
        " replay-faithful, neither conservative nor non-conservative vs the banked 0.716 standard",
        "env_drive_delta": "UNKNOWN -- the env drives arms via 10-frame LINEAR joint interp vs the recorded"
        " per-frame IK path (close-on-transient risk, plan sec13 ISSUE3); covered by the close-frame video"
        " zoom + Rs human-GT",
        "creep_extrapolation": "CONSERVATIVE (pessimistic) -- linear extrapolation of the post-latch creep"
        " rate over W_svc=9000 frames; SRG showed plateauing creep reads high under this extrapolation",
        "scene_align": "NEUTRAL -- g1_scene_align places the cable as the recording (leg G2: dz 0.15mm)",
    }
    result["preconditions_loud"] = {
        "mjw_eq_deferred": "G1 runs the CPU-substrate mj_model-authoritative config; the 4-bar eq stiffen"
        " exists on mj_model ONLY -- any future GPU-cg leg requires the mjw eq re-poke FIRST (P-F6)",
        "plg": "/production-launch-gate NON-APPLICABLE: GPU wall-clock << 10h and explicit Rs approval"
        " (2026-07-10 11:49 + final GO 12:15) -- recorded loud per CLAUDE.md HIGH-COST-GATE threshold",
        "scope": "GRASP+LIFT ONLY; loop stopped before the first G3 step (C1-seat onward NOT driven)",
        "final_verdict": "Rs human-GT on the videos; this JSON is the numeric leg only",
        "d_ff_acceptance": "OFFICIAL route_drive_mode=feedforward (no monkeypatch); acceptance bar ="
        " armqdirect-equivalent; known <=1-frame index-convention delta (cf[t]+sub_i vs probe +1)",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(f"[G1] numeric_verdict={result['numeric_verdict']} (NOT a standalone PASS) -> {OUT_JSON}")

    # ---- assemble videos ----
    VIDEO_DIR.mkdir(exist_ok=True)
    vids = []
    for tag in ("ctx", "zoom"):
        name = {
            "ctx": "comp3_g1dff_grasplift_context_20260710.mp4",
            "zoom": "comp3_g1dff_grasplift_clawzoom_20260710.mp4",
        }[tag]
        out = VIDEO_DIR / name
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(FRAMES_DIR / f"{tag}_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "23",
            str(out),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        (DOWNLOADS / name).write_bytes(out.read_bytes())
        vids.append(name)
        print(f"[G1] video {name} -> ~/Downloads + {VIDEO_DIR.name}/")
    print(f"[G1] DONE: steps={t}, latch_t={latch_t}, videos={vids}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
