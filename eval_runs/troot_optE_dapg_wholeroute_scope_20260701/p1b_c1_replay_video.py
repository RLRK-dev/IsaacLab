# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""P1-b: re-render a sha-pinned route recording as a C1 CROSS-SECTION video, for Rs's human ground truth.

WHAT THIS IS FOR (Rs 2026-07-14, via %12). Rs will watch these and say whether the cable is in the C1 groove.
That verdict becomes the project's FIRST sha-pinned, video-grounded human GT -- the thing every numeric metric
gets calibrated against. Until now no such GT existed: the belief that "Rs rejected cell 2037" turned out to be
hearsay (asked directly, Rs said he did not remember and asked for the video again), and an instrument, a DoD,
and four verdict-band locks had been stacked on top of it. ⭐ human-GT is not something you CITE. It is
something you GO GET. This script goes and gets it.

⛔ NO NUMERIC OVERLAY. The frames carry only the sha, the frame index, and the phase -- nothing evaluative.
Burning "|dx| = 0.78mm ✅" into a frame would anchor Rs's eyes to the very instrument the GT is meant to
calibrate, and we would have manufactured agreement instead of measuring it.

⭐ ARTIFACTS ARE ADDRESSED BY SHA, NEVER BY NAME. "2037" denotes at least four different files on disk; the
same bytes appear under 13 different paths. The sha8 is stamped into the video filename and burned into every
frame so this can never degenerate again.

THREE THINGS ARE PROVEN BEFORE A FRAME IS SHOWN (each fails loud):
  1. GROOVE IDENTITY (p1a_c1_camera_design.py) -- clips are STATIC geoms and contribute no qpos, so replaying
     the recording's pose inside the env model shows the recording's CABLE against the ENV's CLIP. Those are
     built by different code. Measured 2026-07-14: they are geometrically IDENTICAL (floor top 0.825, channel
     15.0mm, seated-cable centre 0.829). The 16x stiffness gap is contact-parameter only. So the groove in the
     picture IS the groove that was there.
  2. REPLAY FIDELITY -- the dump carries cable_xyz (the recorded body positions). After mj_forward we compare
     the POSED cable against them. If they disagree, this video is not the recording and must not be shown to
     Rs as one. (This also independently re-tests the Newton->MuJoCo body-id +1 offset.) comp3's author hit
     exactly this: a quat-convention slip (recording = XYZW, mujoco qpos = WXYZ) rendered the cable invisible.
  3. CAMERA SENSITIVITY -- a camera that cannot show a MIS-seated cable as mis-seated returns "looks fine" for
     every input. At frame 0 the cable lies ungrasped on the table, far outside the groove. If the camera
     cannot show THAT as out, it can show nothing. Frame 0 is therefore the camera's positive control, and it
     is rendered IN-BAND (the video starts there, so Rs sees the "before" with his own eyes).

⚠ WHAT THE VIDEO CAN AND CANNOT SETTLE (pC's standing caveat, carried verbatim to Rs): it shows POSITION --
whether the cable is between the walls and down in the channel, or outside/above them. Proximity is not
capture. The verdict is Rs's.

Offline replay only: qpos is written and mj_forward'd; NO physics is stepped (the CLAUDE.md offline-replay
exception -- post-hoc visualisation outside the control loop).

Run (CPU, offscreen GL, no GPU physics):
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p1b_c1_replay_video.py --sha 5f1c3f92
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parents[1] / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.pop("DISPLAY", None)  # reference-mujoco-headless-egl: BadWindow guard

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

DOWNLOADS = Path.home() / "Downloads"
OUT_DIR = _EVAL / "p1b_c1_replay"

# The two artifacts Rs is to judge, pinned by sha (NOT by name -- "2037" is four different files).
ARTIFACTS = {
    "5f1c3f92": {
        "path": _EVAL / "w0e_liftraise_smoke" / "2037_nominal" / "route_demo_raw.npz",
        "label": "nominal (x0,y0) -- byte-identical to the canonical golden (RUN1_REFERENCE_V2)",
    },
    "3a717010": {
        "path": _EVAL / "w0e_liftraise_smoke" / "2037_x-20_y-15_Fon" / "route_demo_raw.npz",
        "label": "cable offset x=-20mm y=-15mm (F-on)",
    },
    # ⭐ The DEFECT itself, for the first time on video. This run welded the cable 880.9mm -- 51.9mm ABOVE the
    # seat, clear of the wall tops -- and 57 siblings did the same (58/486, C1_PIN_SEAT_AUDIT...json). It is
    # PRE-FIX code (head_sha d65376bce3, 2026-07-05; the W0-e route fixes landed 07-06), so it is history, not
    # a live regression -- but nobody has ever SEEN it, and the seat gate's upper bar (836.0mm) is calibrated
    # to reject exactly this. Rs judges whether that cable is in the groove. If he says it is, the bar is wrong.
    "6f7d5561": {
        "path": _EVAL / "p3_grid" / "cell_x0_y5" / "route_demo_raw.npz",
        # ⛔ The label is BURNED INTO EVERY FRAME, so it obeys the no-overlay rule at the top of this file:
        # identity and provenance only. "MID-AIR WELD z=880.9mm" would hand Rs the verdict before he looked,
        # and his agreement would then be a measurement of my caption, not of the cable.
        "label": "p3_grid cell_x0_y5  --  code d65376bce3 (2026-07-05)",
        # ⛔ env is a SEPARATE AXIS from code sha (lesson banked 2026-07-15, b7553662a4): this run was recorded
        # with CLIP2_Y=0.075, the others with 0.000. Build the scene the recording was made in, or the CLIP in
        # the picture is not the CLIP that was there.
        "env": {"CLIP2_Y": "0.075"},
        # The default 75mm camera spans +-31mm about the seat. The weld sits at +51.9mm -- OFF THE TOP OF THE
        # FRAME. The instrument that proved the cable was IN the groove cannot show it OUT of it, upward.
        "view_dist": 0.160,  # +-66mm: the weld is in frame with 14mm to spare (asserted by CONTROL 4)
    },
}

W, H = 640, 480
FPS = 30
RENDER_EVERY = 10  # 7707 frames -> ~771 rendered -> ~26s at 30fps
REPLAY_TOL_MM = 1.0  # the posed cable must reproduce the recorded cable to this tolerance, or the video lies


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def clip_boxes_at(m, cx, cy, expect=5, xy_tol=0.030, z_min=0.815):
    """The clip's 5 boxes, by GEOMETRY. ⛔ Never by name: every geom here is `shape_<i>_<j>`; only pads are
    named, so a name-based selector returns the EMPTY SET and an empty set reads exactly like 'no clip'."""
    hits = [
        i
        for i in range(int(m.ngeom))
        if int(m.geom_type[i]) == int(mujoco.mjtGeom.mjGEOM_BOX)
        and int(m.geom_bodyid[i]) == 0
        and abs(float(m.geom_pos[i][0]) - cx) <= xy_tol
        and abs(float(m.geom_pos[i][1]) - cy) <= xy_tol
        and float(m.geom_pos[i][2]) >= z_min
    ]
    if len(hits) != expect:
        raise RuntimeError(f"clip selector at ({cx},{cy}) found {len(hits)} boxes, expected {expect} -- BROKEN SELECTOR.")
    return hits


def groove_from_built(m):
    """Seated-cable centre, derived from the boxes. ⛔ NOT from task_config.GROOVE_CENTER_Z (=0.809): the clip
    is FLOATED 20mm, so that constant is 20mm low. The producer's own scene log says the clip sits at 0.820."""
    b = clip_boxes_at(m, 0.35, 0.150)
    floor = max(b, key=lambda g: float(m.geom_size[g][0]))
    floor_top = float(m.geom_pos[floor][2]) + float(m.geom_size[floor][2])
    return (0.35, 0.150, floor_top + 0.004)  # + cable radius


def pose(m, d, q_row):
    """Write ONE recorded frame into qpos and mj_forward. No stepping (offline-replay exception)."""
    q = np.asarray(q_row, dtype=float).copy()
    for j in range(int(m.njnt)):  # recording = Newton joint_q: FREE quat is XYZW (w LAST); mujoco qpos is WXYZ
        if int(m.jnt_type[j]) == int(mujoco.mjtJoint.mjJNT_FREE):
            a = int(m.jnt_qposadr[j])
            x, y, zq, w = q[a + 3 : a + 7]
            q[a + 3 : a + 7] = [w, x, y, zq]
    d.qpos[:] = q
    mujoco.mj_forward(m, d)


def render(m, d, renderer, lookat, az, el, dist):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = lookat
    cam.azimuth, cam.elevation, cam.distance = az, el, dist
    renderer.update_scene(d, camera=cam)
    return renderer.render()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", required=True, choices=sorted(ARTIFACTS), help="sha8 of the artifact to render")
    ap.add_argument("--every", type=int, default=RENDER_EVERY)
    a = ap.parse_args()

    art = ARTIFACTS[a.sha]
    p = art["path"]
    full = sha256_of(p)
    if not full.startswith(a.sha):
        raise SystemExit(f"⛔ sha mismatch: {p} is {full[:12]}, expected {a.sha}... -- the name lied. Refusing.")
    print(f"[P1-b] artifact {a.sha} VERIFIED by sha256 ({full[:16]}...)\n       {p}\n       {art['label']}")

    # ── env is a SEPARATE AXIS from the code sha (lesson 2026-07-15): a matching as_run_sha256 does NOT mean a
    # matching scene. Build the scene THIS recording was made in, or the CLIP in the picture is not the CLIP
    # that was there. Artifacts without an "env" key are unaffected -- their output stays byte-identical.
    for _k, _v in art.get("env", {}).items():
        _prev = os.environ.get(_k)
        os.environ[_k] = _v
        print(f"[P1-b] env for the build: {_k}={_v}" + (f"  (was {_prev})" if _prev is not None else "  (was unset)"))

    rec = np.load(p, allow_pickle=True)
    arm_q, cxyz, phase = np.asarray(rec["arm_q"]), np.asarray(rec["cable_xyz"]), np.asarray(rec["phase_id"])
    F = arm_q.shape[0]

    golden = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
    print("[P1-b] building env on CPU (no route driven; the scene is the subject, not the sim) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(golden),
            "route_c2_scene": True,
        },
    )
    m = env._solver.mj_model
    cable_nb = list(env._cable_bodies[0])  # Newton body ids
    cable_mjc = [b + 1 for b in cable_nb]  # MuJoCo counts worldbody at 0 -> +1 (B3a index-space finding)
    if int(m.nq) != arm_q.shape[1]:
        raise SystemExit(f"⛔ qpos layout mismatch: mj nq={int(m.nq)} vs recording {arm_q.shape[1]}")

    seat = groove_from_built(m)
    print(f"[P1-b] groove (from the BUILT boxes, not from GROOVE_CENTER_Z): seated-cable centre z = {seat[2]:.4f}")

    m.vis.global_.offwidth = max(int(m.vis.global_.offwidth), W)
    m.vis.global_.offheight = max(int(m.vis.global_.offheight), H)
    renderer = mujoco.Renderer(m, height=H, width=W)
    d = mujoco.MjData(m)

    # ── CONTROL 2: does the POSED cable reproduce the RECORDED cable? If not, this video is not the recording.
    print(f"\n[P1-b] CONTROL 2 -- replay fidelity (posed vs recorded cable, tol {REPLAY_TOL_MM}mm):")
    worst = 0.0
    for f in (0, F // 4, F // 2, 3 * F // 4, F - 1):
        pose(m, d, arm_q[f])
        err = np.linalg.norm(d.xpos[cable_mjc] - cxyz[f], axis=1).max() * 1e3
        worst = max(worst, err)
        print(f"   frame {f:5d}: max body error = {err:.4f} mm")
    if worst > REPLAY_TOL_MM:
        raise SystemExit(
            f"\n⛔ REPLAY IS NOT THE RECORDING (max {worst:.2f}mm > {REPLAY_TOL_MM}mm). Showing this to Rs as "
            "'the recording' would put his ground truth on a pose that never happened. Check the free-joint "
            "quat convention (recording XYZW vs mujoco WXYZ) and the Newton->MuJoCo body-id +1 offset."
        )
    print(f"   ✅ replay reproduces the recording (worst {worst:.4f} mm) -- and the +1 body-id offset is confirmed.")

    # ── CONTROL 3: is the camera able to SHOW a mis-seated cable as mis-seated? Frame 0 is the known-off state.
    pose(m, d, arm_q[0])
    p0 = d.xpos[cable_mjc]
    i0 = int(np.argmin(np.abs(p0[:, 1] - seat[1])))
    dx0, dz0 = abs(float(p0[i0, 0]) - seat[0]) * 1e3, (float(p0[i0, 2]) - seat[2]) * 1e3
    print(f"\n[P1-b] CONTROL 3 -- camera sensitivity: at frame 0 the cable lies ungrasped on the table,")
    print(f"   |dx| = {dx0:.1f} mm across the groove, dz = {dz0:+.1f} mm below the seated height.")
    if abs(dz0) < 5.0 and dx0 < 5.0:
        raise SystemExit("⛔ frame 0 is NOT a known-off state -- the camera has no positive control. STOP.")
    print("   ✅ frame 0 is a genuine OUT-OF-GROOVE state, and it is rendered IN-BAND (the video starts there),")
    print("      so Rs sees with his own eyes what 'out' looks like in these views before judging 'in'.")

    _xd = float(art.get("view_dist", 0.075))  # widen when the subject sits outside the default +-31mm (CONTROL 4)
    VIEWS = [
        ("C1 cross-section  (view along +Y)", seat, 90.0, -12.0, _xd),
        ("C1 cross-section  (view along -Y)", seat, -90.0, -12.0, _xd),
        ("top-down (AUX -- shows X, BLIND to Z)", seat, 90.0, -89.0, max(0.090, _xd * 1.2)),
    ]
    frames_dir = OUT_DIR / f"frames_{a.sha}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("*.png"):
        old.unlink()

    idx = list(range(0, F, max(1, a.every)))

    # ── CONTROL 4: is the SUBJECT in the frame? A camera that cannot show the thing being judged reports "looks
    # fine" for it -- CONTROL 3's failure, one direction over. CONTROL 3 proves the camera can show a cable BELOW
    # the seat (frame 0, on the table, -25mm). It says NOTHING about above: the default 75mm view spans +-31mm and
    # the mid-air weld sits at +51.9mm -- off the top of the frame. Rs would have watched an empty groove and
    # concluded "not seated" from a cable he was never shown, which is agreement manufactured out of a crop.
    # ⛔ Check EVERY rendered frame, not the last one. The defect does not live at the end: in the mid-air-weld
    # recording the cable is pinned 51.9mm up from phase 5 to phase 11 and then comes DOWN to +25mm by the final
    # frame. A control that looked only at the end would have passed on +25mm and cropped the +51.9mm it exists
    # to catch. The subject is the run's most extreme state, not its last one.
    fovy = float(m.vis.global_.fovy)
    half_v_mm = _xd * np.tan(np.radians(fovy / 2.0)) * 1e3  # vertical half-extent at the lookat plane
    half_h_mm = half_v_mm * (W / H)
    worst_dz, worst_dx, worst_f = 0.0, 0.0, idx[0]
    for f in idx:
        pose(m, d, arm_q[f])
        pf = d.xpos[cable_mjc]
        i_f = int(np.argmin(np.abs(pf[:, 1] - seat[1])))
        dz_f, dx_f = (float(pf[i_f, 2]) - seat[2]) * 1e3, (float(pf[i_f, 0]) - seat[0]) * 1e3
        if abs(dz_f) > abs(worst_dz):
            worst_dz, worst_dx, worst_f = dz_f, dx_f, f
    print(f"\n[P1-b] CONTROL 4 -- subject in frame? (fovy {fovy:.0f} deg, dist {_xd * 1e3:.0f}mm"
          f" -> +-{half_v_mm:.1f}mm vertical / +-{half_h_mm:.1f}mm horizontal)")
    print(f"   most extreme rendered state = frame {worst_f} (phase {int(phase[worst_f])}): the seat-nearest cable"
          f" body sits dz = {worst_dz:+.1f} mm, dx = {worst_dx:+.1f} mm")
    if abs(worst_dz) > half_v_mm or abs(worst_dx) > half_h_mm:
        need = abs(worst_dz) / np.tan(np.radians(fovy / 2.0)) / 1e3
        raise SystemExit(
            f"\n⛔ THE SUBJECT LEAVES THE FRAME (dz {worst_dz:+.1f}mm vs +-{half_v_mm:.1f}mm). Showing this to Rs "
            f"would show him an empty groove and let him conclude 'not seated' from a cable he was never shown. "
            f"Widen this artifact's 'view_dist' to >= {need:.3f} m."
        )
    print(f"   ✅ the most extreme state is IN FRAME (vertical margin {half_v_mm - abs(worst_dz):.1f}mm).")

    print(f"\n[P1-b] rendering {len(idx)} frames x {len(VIEWS)} views ...")
    lab_h = 30
    for k, f in enumerate(idx):
        pose(m, d, arm_q[f])
        panels = [render(m, d, renderer, lk, az, el, di) for _, lk, az, el, di in VIEWS]
        canvas = Image.new("RGB", (W * len(VIEWS), H + 2 * lab_h), "black")
        dr = ImageDraw.Draw(canvas)
        # ⛔ nothing evaluative on the frame -- identity and time only.
        dr.text((8, 8), f"sha {a.sha}  |  frame {f}/{F - 1}  |  phase {int(phase[f])}  |  {art['label']}", fill="white")
        for i, (name, *_) in enumerate(VIEWS):
            canvas.paste(Image.fromarray(panels[i]), (i * W, lab_h))
            dr.text((i * W + 8, H + lab_h + 6), name, fill="#bbbbbb")
        canvas.save(frames_dir / f"f_{k:05d}.png")
        if k % 100 == 0:
            print(f"   {k}/{len(idx)}")

    out = DOWNLOADS / f"p1b_c1_xsec_{a.sha}.mp4"
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "f_%05d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise SystemExit(f"⛔ ffmpeg failed ({r.returncode}): {r.stderr[-400:]}")

    meta = {
        "sha256": full,
        "sha8": a.sha,
        "artifact": str(p),
        "label": art["label"],
        "video": str(out),
        "frames_rendered": len(idx),
        "replay_worst_error_mm": round(worst, 4),
        "frame0_control": {"dx_mm": round(dx0, 2), "dz_mm": round(dz0, 2)},
        "groove_seated_center_z": round(seat[2], 4),
        "caveat": "shows POSITION, not capture. proximity != capture. the verdict is Rs's.",
    }
    (OUT_DIR / f"p1b_{a.sha}.json").write_text(json.dumps(meta, indent=1))
    print(f"\n✅ delivered: {out}")
    print(f"   (sha8 in the filename AND burned into every frame -- the name can never degenerate again)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
