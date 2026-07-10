# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Per-arm depth confirmation cell (Rs directive #5): R(near)+3mm / L(far)+0, FLAT ik_chord.

Rs #5 (01:54 verbatim '手前だけ修正すればいいだけだろうが' = just fix the near side): per-arm park depth.
After the z-sweep + seesaw re-verify established NEAR/手前 = R arm (tgt[2]=ee_pos_r z) and FAR/奥 = L arm
(tgt[5]=ee_pos_l z), this cell gives the NEAR arm (R) its +3mm shallower park while the FAR arm (L) stays
at nominal (+0), on the FLAT production scene, production ik_chord 4-sub.

PRE-REGISTERED predictions (%12 01:56; this is NOT a both-arm-hold attempt):
  (i)  R z_drop ~= 0mm (== uniform dz3 R) -> per-arm park is COUPLING-HARMLESS (R's clamp does not depend
       on L's park; per-arm depth is a clean lever = the VN-2 R-only-+3..4mm refinement).
  (ii) L continues to FAIL (ik_chord fails the far arm at ALL depths -- established; feedforward is the L
       fix, f8b1ff6b4c). Both-arm hold is NOT expected; the cell's purpose = coupling verification + R
       margin-lever confirmation, NOT L rescue. State this loudly so a NOGO is not read as a lever failure.

Target-index mapping VERIFIED (route_executor.py:3271): target_6d = [ee_pos_r(0:3), ee_pos_l(3:6)] ->
tgt[2] = R_z (手前), tgt[5] = L_z (奥). So R+3 = tgt[2]+=0.003, L+0 = tgt[5]+=0.0.

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
from task_config import WIDE_LEFT_Y, WIDE_RIGHT_Y  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
# retry naming (lane-floor fix chain): run-1 artifacts (comp3_g1_grasplift_result.json + its mp4s) are the
# banked FAIL evidence (Rs human-GT) -- the retry writes distinct names instead of clobbering them.
OUT_JSON = _EVAL_DIR / "comp3_perarm_result.json"
CELLS = [(3, 0)]  # (dz_R_mm, dz_L_mm): R(near)+3 / L(far)+0
FRAMES_DIR = _EVAL_DIR / "comp3_perarm_frames"
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


def _bend_deg(cable_pos, seg):
    a = cable_pos[seg] - cable_pos[seg - 1]
    b = cable_pos[seg + 1] - cable_pos[seg]
    c = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def _run_cell(env, dz_pair_mm, m, d, pads, cables, renderer):
    """One per-arm cell: reset -> per-arm dz-wrapped step_target -> grasp+lift loop -> legs + frames.

    dz_pair_mm = (dz_R_mm, dz_L_mm); R=tgt[2] (near/手前), L=tgt[5] (far/奥) -- verified route_executor:3271.
    """

    env.reset()
    dz_r, dz_l = dz_pair_mm[0] * 1e-3, dz_pair_mm[1] * 1e-3
    route = env._route
    base_st = type(route).step_target

    def st_dz(t):
        tgt, ph, grip, dual = base_st(route, t)
        tgt = tgt.copy()
        tgt[2] += dz_r  # R (near/手前)
        tgt[5] += dz_l  # L (far/奥)
        return tgt, ph, grip, dual

    route.step_target = st_dz  # instance attr; cleared after the cell

    aq0 = env._arm_q_start[0]
    cable_ids = env._cable_bodies[0]
    rest_z = float(np.mean(env._state_0.body_q.numpy()[cable_ids, 2]))
    cell_tag = f"R{dz_pair_mm[0]}_L{dz_pair_mm[1]}"
    cell_frames = FRAMES_DIR / cell_tag
    cell_frames.mkdir(parents=True, exist_ok=True)
    for old in cell_frames.glob("*.png"):
        old.unlink()

    series = {k: [] for k in ("t", "l_drv_q", "r_drv_q", "pad_cable_contacts", "bend_l_deg", "bend_r_deg")}
    series.update({k: [] for k in ("held_z_l", "held_z_r", "slip_l_mm", "slip_r_mm")})
    # instrumentation rider (Rs 01:10): per-arm claw z + Dz(L,R) + lane cable z time series.
    series.update({k: [] for k in ("claw_z_l", "claw_z_r", "claw_dz_lr_mm", "cable_z_lane_l", "cable_z_lane_r")})
    latch_t = None
    held_l = held_r = None
    off_l = off_r = None
    loss_streak = max_loss_streak = 0
    done_early = None
    zero = torch.zeros((1, 6), dtype=torch.float32)
    import warp as wp

    t = 0
    while True:
        _, phase_peek, _, _ = env._route.step_target(t)
        if phase_peek >= 2:
            break
        _, _, dones, _ = env.step(zero)
        if bool(dones[0]):
            done_early = t
            print(f"[PERARM {cell_tag}] EARLY DONE at t={t} -- row DROPPED (post-reset state)")
            break
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        jq = env._state_0.joint_q.numpy()
        l_q = [float(jq[aq0 + i]) for i in _DRV_L]
        r_q = [float(jq[aq0 + i]) for i in _DRV_R]
        claw_l = np.asarray(nre.clamp_pos_ko(bq[nre._LEFT_EE_BODY][:3], bq[nre._LEFT_EE_BODY][3:7]))
        claw_r = np.asarray(nre.clamp_pos_ko(bq[nre._RIGHT_EE_BODY][:3], bq[nre._RIGHT_EE_BODY][3:7]))
        cable_pos = bq[cable_ids, :3]
        ncon_pc = _pad_cable_contacts(d, pads, cables)
        if latch_t is None and min(l_q) > CLOSE_LATCH_Q and min(r_q) > CLOSE_LATCH_Q and ncon_pc > 0:
            latch_t = t
            held_l = int(np.argmin(np.linalg.norm(cable_pos - claw_l, axis=1)))
            held_r = int(np.argmin(np.linalg.norm(cable_pos - claw_r, axis=1)))
            off_l = cable_pos[held_l] - claw_l
            off_r = cable_pos[held_r] - claw_r
            print(f"[PERARM {cell_tag}] CLOSE LATCH at t={t}: held L={held_l} R={held_r}")
        series["t"].append(t)
        series["l_drv_q"].append(round(min(l_q), 4))
        series["r_drv_q"].append(round(min(r_q), 4))
        series["pad_cable_contacts"].append(int(ncon_pc))
        series["claw_z_l"].append(round(float(claw_l[2]), 5))
        series["claw_z_r"].append(round(float(claw_r[2]), 5))
        series["claw_dz_lr_mm"].append(round(float(claw_l[2] - claw_r[2]) * 1e3, 2))
        seg_l = int(np.argmin(np.abs(cable_pos[:, 1] - WIDE_LEFT_Y)))
        seg_r = int(np.argmin(np.abs(cable_pos[:, 1] - WIDE_RIGHT_Y)))
        series["cable_z_lane_l"].append(round(float(cable_pos[seg_l, 2]), 5))
        series["cable_z_lane_r"].append(round(float(cable_pos[seg_r, 2]), 5))
        bl = held_l if held_l is not None else 27
        br = held_r if held_r is not None else 33
        series["bend_l_deg"].append(round(_bend_deg(cable_pos, bl), 2))
        series["bend_r_deg"].append(round(_bend_deg(cable_pos, br), 2))
        if latch_t is not None:
            slip_l = (cable_pos[held_l] - claw_l) - off_l
            slip_r = (cable_pos[held_r] - claw_r) - off_r
            series["slip_l_mm"].append([round(float(x) * 1e3, 3) for x in slip_l])
            series["slip_r_mm"].append([round(float(x) * 1e3, 3) for x in slip_r])
            series["held_z_l"].append(round(float(cable_pos[held_l, 2]), 5))
            series["held_z_r"].append(round(float(cable_pos[held_r, 2]), 5))
            loss_streak = loss_streak + 1 if ncon_pc == 0 else 0
            max_loss_streak = max(max_loss_streak, loss_streak)
        mid = 0.5 * (claw_l + claw_r)
        ctx = _render(renderer, d, (0.30, 0.10, 0.85), 100, -20, 0.9)
        zoom = _render(renderer, d, tuple(mid), 120, -12, 0.16)
        from PIL import Image

        Image.fromarray(ctx).save(cell_frames / f"ctx_{t:04d}.png")
        Image.fromarray(zoom).save(cell_frames / f"zoom_{t:04d}.png")
        if t % 40 == 0:
            print(
                f"[PERARM {cell_tag}] t={t} drv L={min(l_q):.3f} R={min(r_q):.3f}"
                f" pc={ncon_pc} bend L={series['bend_l_deg'][-1]:.1f}"
            )
        t += 1

    del route.step_target  # restore the class method for the next cell
    legs = {}
    n_post = len(series["slip_l_mm"])
    legs["no_early_termination"] = {"pass": done_early is None, "done_at": done_early}
    legs["close_latched"] = {"pass": latch_t is not None, "latch_t": latch_t, "held_l": held_l, "held_r": held_r}
    if latch_t is not None and n_post > 8:
        sl = np.asarray(series["slip_l_mm"], dtype=float)
        sr = np.asarray(series["slip_r_mm"], dtype=float)
        frames = np.arange(n_post) * 10.0
        budget = {}
        for name, arr in (("L", sl), ("R", sr)):
            for ax, margin in (("x_lateral", LAT_MARGIN_M * 1e3), ("z_drop", ZDROP_MARGIN_M * 1e3)):
                col = {"x_lateral": 0, "z_drop": 2}[ax]
                v = arr[:, col] if ax == "x_lateral" else -arr[:, col]
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
            budget[f"{name}_y_axial_end_mm"] = round(float(arr[-1, 1]), 3)
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
    return {
        "dz_R_mm": dz_pair_mm[0],
        "dz_L_mm": dz_pair_mm[1],
        "numeric_cell_verdict": "NUMERIC_GO_CANDIDATE" if ok else "NUMERIC_NOGO",
        "legs": legs,
        "series": series,
        "bend_close_peak_deg": {
            "L": max(series["bend_l_deg"][85:] or [0.0]),
            "R": max(series["bend_r_deg"][85:] or [0.0]),
        },
        "steps": t,
    }


def main():
    print("[PERARM] building FLAT production scene (standard g1_scene_align; parity assert ACTIVE) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
        },
    )
    m = env._solver.mj_model
    d = env._solver.mj_data
    # R1 flat readback: the standard flag-ON void = 4 static table boxes (hz 0.005, z-center 0.795).
    n_table = sum(
        1
        for g in range(int(m.ngeom))
        if int(m.geom_bodyid[g]) == 0
        and abs(float(m.geom_size[g][2]) - 0.005) < 1e-6
        and abs(float(m.geom_pos[g][2]) - 0.795) < 1e-6
    )
    assert n_table == 4, f"flat scene expected 4 table boxes, got {n_table}"
    pads, cables = _pad_and_cable_geoms(m)
    m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
    renderer = mujoco.Renderer(m, height=H, width=W)
    FRAMES_DIR.mkdir(exist_ok=True)

    cells = []
    for dz_pair in CELLS:
        print(f"[PERARM] ===== cell R+{dz_pair[0]}mm / L+{dz_pair[1]}mm =====")
        cells.append(_run_cell(env, dz_pair, m, d, pads, cables, renderer))

    for c in cells:
        s2 = c["series"]
        cw = slice(85, None)
        c["close_window_claw_dz_lr_mm"] = {
            "mean": round(float(np.mean(s2["claw_dz_lr_mm"][cw] or [0.0])), 2),
            "max_abs": round(float(np.max(np.abs(s2["claw_dz_lr_mm"][cw] or [0.0]))), 2),
        }
    result = {
        "context": "FLAT-scene z_grasp depth sweep (Rs option-3 GO 01:06): isolate depth from support."
        " PRODUCTION ik_chord 4-sub, flat scene. Interpretation PER CELL (rule 30); numeric never a"
        " standalone PASS -- final = Rs human-GT on videos.",
        "scene": {
            "type": "FLAT production (standard g1_scene_align void)",
            "table_boxes": int(n_table),
            "parity_assert": "ACTIVE + PASS (not bypassed -- flat scene is the guard's expected 4-box shape)",
        },
        "context_extra": "Rs directive #5 (01:54): per-arm park -- R(near/手前)+3mm / L(far/奥)+0. Mapping"
        " verified route_executor:3271 (tgt[2]=R_z, tgt[5]=L_z). NOT a both-arm-hold attempt.",
        "cells": cells,
        "prereg_predictions": "(i) R z_drop ~=0mm (== uniform dz3 R) -> per-arm park COUPLING-HARMLESS, R"
        " margin lever confirmed / (ii) L continues to FAIL (ik_chord fails the far arm at all depths;"
        " feedforward f8b1ff6b4c is the L fix). Both-arm hold NOT expected -- a NOGO here is EXPECTED and"
        " is NOT a lever failure. PER CELL, rule 30. Final grasp verdict = Rs human-GT on videos.",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    for c in cells:
        lr = c["legs"].get("lift_rise", {})
        cb = c["legs"].get("creep_budget", {})
        print(
            f"[PERARM] R+{c['dz_R_mm']}/L+{c['dz_L_mm']}mm: {c['numeric_cell_verdict']}"
            f" latch={c['legs']['close_latched']['latch_t']}"
            f" rise L={lr.get('rise_l_m')} R={lr.get('rise_r_m')}"
            f" z_drop L={cb.get('L_z_drop', {}).get('end_mm')} R={cb.get('R_z_drop', {}).get('end_mm')}"
            f" (prereg: R z_drop~0 coupling-harmless / L fails)"
        )
    print(f"-> {OUT_JSON}")

    # per-cell videos (ctx + zoom)
    VIDEO_DIR.mkdir(exist_ok=True)
    for dz_pair in CELLS:
        cell_tag = f"R{dz_pair[0]}_L{dz_pair[1]}"
        cf = FRAMES_DIR / cell_tag
        for tag in ("ctx", "zoom"):
            name = f"comp3_perarm_{cell_tag}_{tag}_20260711.mp4"
            out = VIDEO_DIR / name
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(FPS),
                    "-i",
                    str(cf / (tag + "_%04d.png")),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-crf",
                    "23",
                    str(out),
                ],
                check=True,
                capture_output=True,
            )
            (DOWNLOADS / name).write_bytes(out.read_bytes())
    print("[PERARM] videos -> ~/Downloads + comp3_g1_videos/ (8 files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
