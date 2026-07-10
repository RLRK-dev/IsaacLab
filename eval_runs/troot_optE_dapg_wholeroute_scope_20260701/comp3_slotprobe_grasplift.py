# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Slot falsification probe: 2-slot central-support scene + z_grasp sweep, PRODUCTION ik_chord drive.

Rs GO 2026-07-11 00:15 (verbatim '3 go', bank 2b818b6f2f) authorizing the pre-registered probe
(SLOT_REDESIGN_STUDY_COORD_20260710.md sec5). Question: does removing the bend source (central support
under the inter-claw span; Rs hypothesis bank 20a94d19fa) let the CURRENT PRODUCTION drive (ik_chord,
step-level batched IK + 10-frame chord, 4-sub) hold the cable -- per z_grasp cell {+0,+3,+4,+5}mm?

Pre-registration interpretation (pinged to %12 BEFORE launch; no silent deviation):
- 'production drive as-is' is honored LITERALLY by running the G1 route-replay harness in the default
  ik_chord mode (the sec5 'self-contained scripted' wording is subsumed: the recording IS the script and
  the env drive is the production path -- a re-implemented scripted probe would NOT be the production
  drive and would weaken the falsification).
- scene variant is PROBE-LEVEL (base/locked untouched, SRG option-B precedent): newton.ModelBuilder
  .add_shape_box is wrapped during the build; the 4 flag-ON table boxes (static, hz 0.005, z-center
  0.795) are suppressed and the 5-box 2-SLOT layout is emitted instead (slots exactly the study sec3a
  dims: L [0.093,0.122] / R [0.181,0.210] x X window [0.234,0.366]; central solid [0.122,0.181]).
- nre.lane_void_parity_assert is BYPASSED for this probe (loud): the assert firing on a variant scene is
  the drift guard working as designed; the variant is Rs-sanctioned.
- z_grasp cell dz: UNIFORM +dz on both step-target z's (probe-level step_target wrap) = the whole
  trajectory raised dz -> grasp depth shallower by dz with minimal confound (lift legs are relative).
- Bend leg added to the series: per-RL-step local bend angle at the held segs (27/33), the sec1 metric.
- 4 cells run sequentially in ONE env (scene identical across cells; per-cell env.reset() -- the R1
  reset re-seeds grip OPEN by design). Judgment legs identical to G1 per cell; per-cell videos.
- No comparisons against OLD-floor-era numbers (re-bank rule); references = the post-fix run family.

Prior-art guard disposition (loud): check_thread_vault_prior_art.sh flagged BLOCKER_CONTEXT on the
probe's OWN pre-registration doc (study F-B fork rows) -- not a prior failed path; the explicit new
directive is the Rs GO above.

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
OUT_JSON = _EVAL_DIR / "comp3_slotprobe_result.json"
DZ_CELLS_MM = (0, 3, 4, 5)
FRAMES_DIR = _EVAL_DIR / "comp3_slotprobe_frames"
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


# 2-slot probe table layout (study sec3a; base literals: table_cx=0.3, half=(0.35,0.35), cz=0.795):
# Y: solid[-0.40,0.093] | L slot[0.093,0.122] | central solid[0.122,0.181] | R slot[0.181,0.210] | solid[0.210,0.30]
# X: slots only within the window [0.234,0.366]; outside = fill boxes (overlap with central solid is fine).
_PROBE_BOXES = [
    # (hx, hy, cx, cy)
    (0.35, 0.2465, 0.3, -0.1535),  # -Y solid up to L slot lo (0.093)
    (0.35, 0.0295, 0.3, 0.1515),  # CENTRAL solid [0.122,0.181] (the Rs central support)
    (0.35, 0.045, 0.3, 0.255),  # +Y solid from R slot hi (0.210)
    (0.142, 0.0585, 0.092, 0.1515),  # -X fill (Y band [0.093,0.210], X [-0.05,0.234])
    (0.142, 0.0585, 0.508, 0.1515),  # +X fill (X [0.366,0.65])
]


def _install_scene_patch():
    """Wrap ModelBuilder.add_shape_box: suppress the 4 flag-ON table boxes, emit the 2-slot layout."""
    import newton

    orig = newton.ModelBuilder.add_shape_box
    state = {"suppressed": 0, "emitted": False}

    def patched(self, body=-1, hx=None, hy=None, hz=None, xform=None, cfg=None, **kw):
        import warp as wp

        # float32 tol 1e-6 (probe leg-C lesson: wp.transform stores float32 -- 0.795 -> 0.7950000167,
        # a 1e-9 tol silently misses it; the first launch fail-fast caught exactly this).
        is_table = (
            body == -1
            and hz is not None
            and abs(float(hz) - 0.005) < 1e-6
            and xform is not None
            and abs(float(xform.p[2]) - 0.795) < 1e-6
        )
        if is_table:
            state["suppressed"] += 1
            if not state["emitted"]:
                state["emitted"] = True
                for bhx, bhy, bcx, bcy in _PROBE_BOXES:
                    xf = wp.transform((bcx, bcy, float(xform.p[2])), wp.quat_identity())
                    orig(self, body=-1, hx=bhx, hy=bhy, hz=hz, xform=xf, cfg=cfg)
                print(
                    f"[SLOTPROBE] 2-slot table emitted ({len(_PROBE_BOXES)} boxes;"
                    " slots Y[0.093,0.122]+[0.181,0.210] x X[0.234,0.366])"
                )
            return None
        return orig(self, body=body, hx=hx, hy=hy, hz=hz, xform=xform, cfg=cfg, **kw)

    newton.ModelBuilder.add_shape_box = patched
    return state


def _bend_deg(cable_pos, seg):
    a = cable_pos[seg] - cable_pos[seg - 1]
    b = cable_pos[seg + 1] - cable_pos[seg]
    c = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def _run_cell(env, dz_mm, m, d, pads, cables, renderer):
    """One sweep cell: reset -> dz-wrapped step_target -> grasp+lift loop -> legs + frames."""

    env.reset()
    dz = dz_mm * 1e-3
    route = env._route
    base_st = type(route).step_target

    def st_dz(t):
        tgt, ph, grip, dual = base_st(route, t)
        tgt = tgt.copy()
        tgt[2] += dz
        tgt[5] += dz
        return tgt, ph, grip, dual

    route.step_target = st_dz  # instance attr; cleared after the cell

    aq0 = env._arm_q_start[0]
    cable_ids = env._cable_bodies[0]
    rest_z = float(np.mean(env._state_0.body_q.numpy()[cable_ids, 2]))
    cell_frames = FRAMES_DIR / f"dz{dz_mm}"
    cell_frames.mkdir(parents=True, exist_ok=True)
    for old in cell_frames.glob("*.png"):
        old.unlink()

    series = {k: [] for k in ("t", "l_drv_q", "r_drv_q", "pad_cable_contacts", "bend_l_deg", "bend_r_deg")}
    series.update({k: [] for k in ("held_z_l", "held_z_r", "slip_l_mm", "slip_r_mm")})
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
            print(f"[SLOTPROBE dz{dz_mm}] EARLY DONE at t={t} -- row DROPPED (post-reset state)")
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
            print(f"[SLOTPROBE dz{dz_mm}] CLOSE LATCH at t={t}: held L={held_l} R={held_r}")
        series["t"].append(t)
        series["l_drv_q"].append(round(min(l_q), 4))
        series["r_drv_q"].append(round(min(r_q), 4))
        series["pad_cable_contacts"].append(int(ncon_pc))
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
                f"[SLOTPROBE dz{dz_mm}] t={t} drv L={min(l_q):.3f} R={min(r_q):.3f}"
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
        "dz_mm": dz_mm,
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
    print("[SLOTPROBE] installing 2-slot scene patch + parity-assert bypass ...")
    patch_state = _install_scene_patch()
    orig_parity = nre.lane_void_parity_assert
    nre.lane_void_parity_assert = lambda m: print(
        "[SLOTPROBE] lane_void_parity_assert BYPASSED (sanctioned variant scene; the guard firing on a"
        " variant is by-design -- Rs GO 2b818b6f2f)"
    )
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
    assert patch_state["suppressed"] == 4 and patch_state["emitted"], (
        f"scene patch did not engage as expected: {patch_state}"
    )
    m = env._solver.mj_model
    d = env._solver.mj_data
    pads, cables = _pad_and_cable_geoms(m)
    m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
    renderer = mujoco.Renderer(m, height=H, width=W)
    FRAMES_DIR.mkdir(exist_ok=True)

    cells = []
    for dz_mm in DZ_CELLS_MM:
        print(f"[SLOTPROBE] ===== cell dz=+{dz_mm}mm =====")
        cells.append(_run_cell(env, dz_mm, m, d, pads, cables, renderer))
    nre.lane_void_parity_assert = orig_parity

    result = {
        "context": "slot falsification probe (Rs GO 2b818b6f2f; prereg study sec5): 2-slot central-support"
        " scene + z_grasp sweep, PRODUCTION ik_chord 4-sub drive. Interpretation is PER CELL (rule 30);"
        " numeric verdicts are never a standalone PASS -- final = Rs human-GT on videos.",
        "scene": {
            "slots_y": [[0.093, 0.122], [0.181, 0.21]],
            "central_solid_y": [0.122, 0.181],
            "x_window": [0.234, 0.366],
            "boxes": 5,
            "parity_assert": "BYPASSED (sanctioned variant, loud)",
        },
        "prior_art_disposition": "guard hit = the probe's own prereg doc (study F-B rows), not a prior"
        " failed path; explicit new directive = Rs GO 00:15 (bank 2b818b6f2f)",
        "cells": cells,
        "grid_interpretation_prereg": "any cell both-arms PASS -> bend hypothesis PROVEN + trainer D-b"
        " window may be unnecessary / all cells fail -> bend not the dominant cause; D-b window design"
        " returns as the fixed path",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    for c in cells:
        lr = c["legs"].get("lift_rise", {})
        print(
            f"[SLOTPROBE] dz+{c['dz_mm']}mm: {c['numeric_cell_verdict']}"
            f" latch={c['legs']['close_latched']['latch_t']}"
            f" rise L={lr.get('rise_l_m')} R={lr.get('rise_r_m')}"
            f" bend_peak L={c['bend_close_peak_deg']['L']} R={c['bend_close_peak_deg']['R']} steps={c['steps']}"
        )
    print(f"-> {OUT_JSON}")

    # per-cell videos (ctx + zoom)
    VIDEO_DIR.mkdir(exist_ok=True)
    for dz_mm in DZ_CELLS_MM:
        cf = FRAMES_DIR / f"dz{dz_mm}"
        for tag in ("ctx", "zoom"):
            name = f"comp3_slotprobe_dz{dz_mm}_{tag}_20260711.mp4"
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
    print("[SLOTPROBE] videos -> ~/Downloads + comp3_g1_videos/ (8 files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
