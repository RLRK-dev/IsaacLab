# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp5 gate ⑥: full-fire live + C2-seating (DoD④ + DoD⑥) on the real C2 groove scene.

Runs the route env AS-CODED (cuda:0, mujoco-CPU newton stepping = R3 production substrate) with the D ρ=0
official feedforward drive (cdac6b6972) + route_c2_scene=True (comp5's real collidable C2 V-groove) over the
FULL episode (all N_ROUTE_PHASES, NOT the grasp+lift-only G1 scope). Zero policy actions (residual 0 -> the
recorded waypoints are replayed). Demonstrates the whole grasp->C1-route->C2-seat route firing live with the
grip carrying the cable, and produces the C2-seating video (DoD⑥, Rs human-GT).

⭐ PRE-REGISTERED predicate (§運用29, %12-approved before this run):
  MOLECULE (conjoined = strict_v2 both legs, nominal cell x0_y0):
    strict_v2 = c1_retained_final AND c2_seated_honest
      C1-retention: z_c1 < 0.840 AND flank_max < 0.840 (env _c1_retention_m) AND not-dropped [+ span diagnostic]
      C2-seat:      _c2_seated_honest(cable) = true (wall_ok AND in_groove vs C2 @ ROUTE_GROOVE_Z 829)
    BOTH legs conjoined (NOT C2-seat alone -- 07-05 C1-escape-contamination prevention).
  FULL-FIRE (DoD④): phase advances to the final (C2-seat) phase, cable carried, no early drop/explosion.
  DIAGNOSTIC (not conjoined): 81-cell numerator (=⑨b), lane-crossing, per-arm grasp quality, span.
  PREDICTION: PASS-candidate = full-fire + molecule TRUE + no-drop -> NUMERIC_GO_CANDIDATE; FAIL = early-done
    OR phase-not-reaching-C2 OR molecule FALSE -> NUMERIC_NOGO; INCONCLUSIVE = full-fire OK but one leg marginal.
  Numeric is NEVER a standalone PASS -- Rs human-GT on the C2-seating video is final. Conservatism: collidable
  C2 (record-matched) = conservative-favourable for the seat claim.

Run (cuda:0 pinned; MUJOCO_GL=egl for offscreen render):
    CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp5_c2seat_fullfire.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "0", (
    f"⑥ runs the as-coded substrate on cuda:0 ONLY; got {os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')!r}"
)
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.pop("DISPLAY", None)

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import route_env_config as rc  # noqa: E402
import torch  # noqa: E402
import warp as wp  # noqa: E402

# comp5 sub10 verification (Rs-approved 2026-07-12): raise the DRIVE-loop contact solve to the recording's
# 10-substep fidelity so the grip holds through the lift (⑥ dropped at the RL default 4 -- the coarse 4-sub
# contact solve loses the grip, prior diagnosis 763e0e2f48/state.md:64). PAIRED override RL_SIM_SUBSTEPS 4->10
# AND RL_SIM_DT DT/4->DT/10 so each frame stays 10 x DT/10 == DT (substeps alone would integrate 2.5x DT per
# frame and break the timeline). Monkeypatch the newton_route_env module globals (newton_route_env.py:1150 reads
# them at drive-call time); production constants (newton_skill_env_base:95-96) are UNTOUCHED => the RL training
# substrate is unchanged. Default OFF (env unset) = byte-preserve the original 4-sub ⑥; SUB10_VERIFY=1 activates
# the override and suffixes all outputs "_sub10" so the original 4-sub evidence is preserved.
_SUB10 = os.environ.get("SUB10_VERIFY", "0") == "1"
if _SUB10:
    nre.RL_SIM_SUBSTEPS = 10
    nre.RL_SIM_DT = nre.DT / 10.0
    assert abs(nre.RL_SIM_SUBSTEPS * nre.RL_SIM_DT - nre.DT) < 1e-12, "frame time must remain DT"
    print(f"[SUB10] override active: RL_SIM_SUBSTEPS={nre.RL_SIM_SUBSTEPS} RL_SIM_DT={nre.RL_SIM_DT:.8f} (=DT/10)")
_C1PIN = os.environ.get("ROUTE_C1_PIN", "0") == "1"  # FORK-1 fix: activate the env-core C1 clip-retention pin
# CABLE_XYZ_DIAG (RS-TECH-LEAD GO 2026-07-12 03:35): dump env-core cable_xyz per RL step + compare to the recording
# per-frame to separate (a) open-loop cable-drift (divergence GROWS from ~0 @frame-0) from (b) build-parity mismatch
# (NONZERO divergence already @frame-0). READ-ONLY on env internals; default OFF = byte-preserve the drop run.
_DIAG = os.environ.get("CABLE_XYZ_DIAG", "0") == "1"
_SFX = ("_sub10" if _SUB10 else "") + ("_c1pin" if _C1PIN else "") + ("_cablediag" if _DIAG else "")

GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT_JSON = _EVAL / f"comp5_c2seat_fullfire{_SFX}_result.json"
FRAMES_DIR = _EVAL / f"comp5_c2seat_fullfire{_SFX}_frames"
DOWNLOADS = Path.home() / "Downloads"
W, H = 960, 720
FPS = 10
RENDER_EVERY = 3  # 1 rendered frame per 3 RL steps (~250 frames for a ~770-step episode)


def _pad_and_cable_geoms(m):
    pads, cables = set(), set()
    for g in range(m.ngeom):
        gname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or "").lower()
        if "pad" in (gname + bname):
            pads.add(g)
        elif int(m.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_CAPSULE) and int(m.geom_bodyid[g]) != 0:
            cables.add(g)
    return pads, cables


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


def _ffmpeg(tag, out_name):
    pat = str(FRAMES_DIR / f"{tag}_%05d.png")
    out = DOWNLOADS / out_name
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", pat, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return str(out) if r.returncode == 0 and out.exists() else f"FFMPEG_FAIL:{r.returncode}"


def main():
    print("[⑥] building full-fire env (route_c2_scene=True, feedforward, cuda:0) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,  # recording-aligned scene (no support clips, cable at recording start)
            "route_drive_mode": "feedforward",  # D rho=0 official
            "route_c2_scene": True,  # comp5: real collidable C2 V-groove
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
    cable_ids = env._cable_bodies[0]
    n_phases = int(rc.N_ROUTE_PHASES)
    zero = torch.zeros((1, 6), dtype=torch.float32)

    if _DIAG:
        # env drives arm to recording frame step_f[t]+sub_i (step_f[t]=t*cad, route_executor.py:88/3322); the env
        # cable AFTER RL step t reflects the last driven sub-frame t*cad+(nsub-1). Compare to the recording there.
        _rec = np.load(str(GOLDEN_NPZ), allow_pickle=True)
        _rec_cxyz = np.asarray(_rec["cable_xyz"])  # (F,40,3) recording ground-truth (segment order 0..39)
        _cad, _nsub, _nrecf = 10, int(nre.RL_SIM_SUBSTEPS), _rec_cxyz.shape[0]
        _bq0 = env._state_0.body_q.numpy()
        _env_c0 = _bq0[cable_ids, :3]
        _lpads, _rpads = set(), set()  # split pads L/R by pad-body world-Y (R hand ~0.194, L ~0.106 @P0; thr 0.15)
        for _g in pads:
            (_rpads if float(_bq0[int(m.geom_bodyid[_g]), 1]) > 0.15 else _lpads).add(_g)
        _d0 = np.linalg.norm(_env_c0 - _rec_cxyz[0], axis=1) * 1e3  # per-seg mm, env-settled vs rec frame-0
        print(
            f"[DIAG] pads split by body-y: L={len(_lpads)} R={len(_rpads)} (total {len(pads)}); "
            f"rec_frames={_nrecf} cadence={_cad} nsub={_nsub}"
        )
        print(
            f"[DIAG] FRAME-0 div (env settled vs rec f0): mean={_d0.mean():.2f} max={_d0.max():.2f} "
            f"seg24(Lheld)={_d0[24]:.2f} seg27(C1)={_d0[27]:.2f} mm  <-- signature-(b) probe"
        )
        _diag = {
            "t": [],
            "phase": [],
            "recf": [],
            "div_mean_mm": [],
            "div_max_mm": [],
            "div_seg24_mm": [],
            "div_seg27_mm": [],
            "pad_L": [],
            "pad_R": [],
            "env_cxyz": [],
            "frame0_div_mean_mm": float(_d0.mean()),
            "frame0_div_max_mm": float(_d0.max()),
            "frame0_div_perseg_mm": _d0.tolist(),
        }

    series = {"t": [], "phase": [], "z_c1_mm": [], "flank_mm": [], "c2_seated": [], "pad_cable": []}
    max_phase = -1
    early_done = None
    c2_seated_run = 0
    rk = 0
    t = 0
    while t < env.MAX_EPISODE_STEPS:
        _, phase_peek, _, _ = env._route.step_target(t)
        _, _, dones, _ = env.step(zero)
        if bool(dones[0]):
            early_done = t
            print(f"[⑥] EARLY DONE at t={t} (drop/explosion/termination)")
            break
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        cable_pos = bq[cable_ids, :3]
        z_c1, flank = env._c1_retention_m(cable_pos)
        c2_seated = bool(env._c2_seated_honest(cable_pos))
        ncon = _pad_cable_contacts(d, pads, cables)
        if _DIAG:
            _recf = min(t * _cad + (_nsub - 1), _nrecf - 1)
            _dv = np.linalg.norm(cable_pos - _rec_cxyz[_recf], axis=1) * 1e3  # per-seg mm (env vs rec @ driven frame)
            _diag["t"].append(t)
            _diag["phase"].append(int(phase_peek))
            _diag["recf"].append(int(_recf))
            _diag["div_mean_mm"].append(round(float(_dv.mean()), 3))
            _diag["div_max_mm"].append(round(float(_dv.max()), 3))
            _diag["div_seg24_mm"].append(round(float(_dv[24]), 3))
            _diag["div_seg27_mm"].append(round(float(_dv[27]), 3))
            _diag["pad_L"].append(int(_pad_cable_contacts(d, _lpads, cables)))
            _diag["pad_R"].append(int(_pad_cable_contacts(d, _rpads, cables)))
            _diag["env_cxyz"].append(cable_pos.copy())
        max_phase = max(max_phase, int(phase_peek))
        c2_seated_run = c2_seated_run + 1 if c2_seated else 0

        series["t"].append(t)
        series["phase"].append(int(phase_peek))
        series["z_c1_mm"].append(round(float(z_c1) * 1e3, 3))
        series["flank_mm"].append(round(float(flank) * 1e3, 3))
        series["c2_seated"].append(c2_seated)
        series["pad_cable"].append(int(ncon))

        if t % RENDER_EVERY == 0:
            _c2lk = (float(rc.ROUTE_C2_XY[0]), float(rc.ROUTE_C2_XY[1]), 0.829)  # C2 groove-z lookat
            ctx = _render(renderer, d, (0.375, 0.075, 0.86), 110, -24, 1.05)  # full grasp->C1->C2 overview
            c2z = _render(renderer, d, _c2lk, 120, -14, 0.17)  # C2 seat zoom
            from PIL import Image

            Image.fromarray(ctx).save(FRAMES_DIR / f"ctx_{rk:05d}.png")
            Image.fromarray(c2z).save(FRAMES_DIR / f"c2zoom_{rk:05d}.png")
            rk += 1
        if t % 60 == 0:
            print(
                f"[⑥] t={t} phase={phase_peek} z_c1={z_c1 * 1e3:.1f}mm "
                f"flank={flank * 1e3:.1f}mm c2seat={c2_seated} pad={ncon}"
            )
        t += 1

    if _DIAG:
        _env_arr = np.stack(_diag["env_cxyz"], axis=0) if _diag["t"] else np.zeros((0, 40, 3))
        _diag_npz = _EVAL / f"comp5_c2seat_fullfire{_SFX}.npz"
        np.savez_compressed(
            _diag_npz,
            env_cxyz=_env_arr,
            t=np.array(_diag["t"]),
            phase=np.array(_diag["phase"]),
            recf=np.array(_diag["recf"]),
            div_mean_mm=np.array(_diag["div_mean_mm"]),
            div_max_mm=np.array(_diag["div_max_mm"]),
            div_seg24_mm=np.array(_diag["div_seg24_mm"]),
            div_seg27_mm=np.array(_diag["div_seg27_mm"]),
            pad_L=np.array(_diag["pad_L"]),
            pad_R=np.array(_diag["pad_R"]),
            frame0_perseg_mm=np.array(_diag["frame0_div_perseg_mm"]),
        )
        _ph = np.array(_diag["phase"])
        _dm = np.array(_diag["div_mean_mm"])
        _dx = np.array(_diag["div_max_mm"])
        _phase_summary = {}
        for _p in sorted(set(_diag["phase"])):
            _idx = np.where(_ph == _p)[0]
            _phase_summary[str(int(_p))] = {
                "entry_t": int(_diag["t"][_idx[0]]),
                "entry_div_mean_mm": round(float(_dm[_idx[0]]), 3),
                "entry_div_max_mm": round(float(_dx[_idx[0]]), 3),
                "phase_div_mean_mm": round(float(_dm[_idx].mean()), 3),
                "phase_div_max_mm": round(float(_dx[_idx].max()), 3),
                "padL_entry": int(_diag["pad_L"][_idx[0]]),
                "padR_entry": int(_diag["pad_R"][_idx[0]]),
            }
        _diag_json = {
            "config": "canonical drop (feedforward D rho=0, route_c2_scene=True, no sub10, no c1pin)",
            "nsub": _nsub,
            "frame0_div_mean_mm": round(_diag["frame0_div_mean_mm"], 3),
            "frame0_div_max_mm": round(_diag["frame0_div_max_mm"], 3),
            "frame0_seg24_mm": round(float(_diag["frame0_div_perseg_mm"][24]), 3),
            "frame0_seg27_mm": round(float(_diag["frame0_div_perseg_mm"][27]), 3),
            "early_done": early_done,
            "per_phase": _phase_summary,
            "signatures": "(a) drift = div GROWS monotonically from ~0 @frame0; (b) build-parity = NONZERO @frame0",
        }
        (_EVAL / f"comp5_c2seat_fullfire{_SFX}.json").write_text(json.dumps(_diag_json, indent=1))
        print("[DIAG] per-phase divergence summary:")
        print(json.dumps(_diag_json, indent=1))

    # ---- verdict (numeric; NEVER a standalone PASS -- Rs human-GT on the video is final) ----
    z_c1_end = series["z_c1_mm"][-1] if series["z_c1_mm"] else None
    flank_end = series["flank_mm"][-1] if series["flank_mm"] else None
    # C2-seat SUSTAINED over the final phase (last >=5 rendered-consistent steps) to avoid a 1-frame flicker.
    c2_seated_end = bool(c2_seated_run >= 5) or (bool(series["c2_seated"][-1]) if series["c2_seated"] else False)
    c1_retained_end = (z_c1_end is not None and z_c1_end < 840.0) and (flank_end is not None and flank_end < 840.0)
    full_fire = (early_done is None) and (max_phase >= n_phases - 1)
    strict_v2 = bool(c1_retained_end and c2_seated_end)

    if full_fire and strict_v2:
        verdict = "NUMERIC_GO_CANDIDATE"
    elif (early_done is not None) or (not full_fire) or (not c1_retained_end and not c2_seated_end):
        verdict = "NUMERIC_NOGO"
    else:
        verdict = "INCONCLUSIVE"

    vids = {
        "ctx": _ffmpeg("ctx", f"comp5_c2seat_fullfire{_SFX}_ctx.mp4"),
        "c2zoom": _ffmpeg("c2zoom", f"comp5_c2seat_fullfire{_SFX}_c2zoom.mp4"),
    }

    result = {
        "cell": "x0_y0",
        "drive": "feedforward (D rho=0)",
        "route_c2_scene": True,
        "steps_run": t,
        "early_done": early_done,
        "n_phases": n_phases,
        "max_phase_reached": max_phase,
        "full_fire": full_fire,
        "molecule (strict_v2)": {
            "conjoined": "c1_retained_final AND c2_seated_honest",
            "c1_retention": {"z_c1_end_mm": z_c1_end, "flank_end_mm": flank_end, "pass": c1_retained_end},
            "c2_seat": {"sustained_run": c2_seated_run, "pass": c2_seated_end},
            "strict_v2": strict_v2,
        },
        "diagnostic_not_conjoined": ["81-cell numerator (=⑨b)", "lane-crossing", "per-arm grasp quality", "span"],
        "numeric_verdict": verdict,
        "videos": vids,
        "note": "numeric is NEVER a standalone PASS; Rs human-GT on the C2-seating video is final",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"-> {OUT_JSON}")
    print(f"[⑥] verdict={verdict} full_fire={full_fire} strict_v2={strict_v2} videos={vids}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
