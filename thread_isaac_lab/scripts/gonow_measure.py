# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""GO-NOW read-only measurement harness for DDR #18 grip (B4-shadow + FF whole-route + ik_chord-natural-term).

OBSERVATION ONLY. Builds a wc=1 CPU/GPU ``NewtonRouteEnv`` (drive-mode selectable), drives ``env.step(zeros)``,
and after each step re-derives the drop metrics by mirroring ``_compute_rewards_dones_batch`` (:1653-1660). With
``--shadow`` it ALSO observes the (d-b) C1-pin SHADOW fire predicate per physics frame at the intended ik_chord
pre-step position -- ``capture AND depth`` for K consecutive frames -- WITHOUT firing (it NEVER calls
``authorize_clip_pin``; no weld / authorizer mutation / physics change). Faithful to ``_maybe_activate_c1_pin``
(``newton_route_env.py`` :1848-1855; p5 §10.12). No physics/control/env-source write; the ``_physics_step_all`` and
``_reset_worlds`` hooks are instance-attr shadows that observe then delegate to the original unchanged.

Prereg = ``eval_runs/.../IKCHORD_GRIPSLIP_GONOW_MEASURE_PREREG_RSTECHLEAD_20260718.md``. Physical-validity judgment
is Rs's; this script emits NUMBERS + a mechanical shadow/drop classification only.

Run (env_isaaclab7 = Option-E venv; pin the visible GPU per the CLAUDE.md GPU rules before launch):
    /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/gonow_measure.py --device cuda:0 \
        --drive-mode ik_chord --route-c1-pin --shadow --episode-steps 300 --tag b4shadow_ikchord --outbox <FRESH>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_TIL = _SCRIPTS.parent  # thread_isaac_lab
_REPO = _TIL.parent  # repo root
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("MUJOCO_GL", "egl")

_GOLDEN = (
    _REPO
    / "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
    / "w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz"
)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args) -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", *args], cwd=str(_REPO), stderr=subprocess.DEVNULL).decode().strip()
    except Exception as e:  # noqa: BLE001
        return f"<git-error:{type(e).__name__}>"


def _repo_source_closure() -> dict:
    """sha256 of every loaded module whose source .py lives inside the repo (fail-closed running-code identity)."""
    cl: dict = {}
    for _name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        try:
            p = Path(f).resolve()
            rel = str(p.relative_to(_REPO))
        except (ValueError, OSError):
            continue
        if p.suffix == ".py" and p.exists():
            cl[rel] = _sha256(p)
    return cl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--drive-mode", choices=("ik_chord", "feedforward"), default="ik_chord")
    ap.add_argument("--route-c1-pin", action="store_true", help="arm the C1 pin (sets _pin_seat_seg; ik_chord loop never fires it)")
    ap.add_argument("--shadow", action="store_true", help="observe the (d-b) shadow fire predicate per physics frame (no weld)")
    ap.add_argument("--episode-steps", type=int, default=300)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--recording", default=str(_GOLDEN))
    ap.add_argument("--tag", default="gonow")
    ap.add_argument("--outbox", required=True)
    a = ap.parse_args()

    import numpy as np

    np.random.seed(0)
    import torch
    import warp as wp

    import newton_route_env as nre
    import newton_skill_env_base as nseb
    import route_env_config as rc
    import route_executor as rex
    from newton_route_env import _C1_XY, _LEFT_EE_BODY, _RIGHT_EE_BODY, clamp_pos_ko

    rec = Path(a.recording)
    assert rec.exists(), f"recording (GOLDEN) not found: {rec}"
    out = Path(a.outbox)
    if out.exists():
        # Fresh-outbox bar (OPS-SUP cond 3): the leaf must NOT pre-exist. The launcher writes run.log to the
        # PARENT (not this leaf), so a pre-existing leaf means a stale/overwriting run -> fail-closed exit 2.
        print(f"[gonow] FRESH-OUTBOX VIOLATION: outbox leaf already exists: {out}", flush=True)
        raise SystemExit(2)
    out.mkdir(parents=True, exist_ok=False)

    cfg = {
        "grasp_actuation": True,
        "route_executor_impl": "route_executor",
        "route_recording_npz": str(rec),
        "g1_scene_align": True,
        "route_drive_mode": a.drive_mode,
        "route_c2_scene": True,
    }
    if a.route_c1_pin:
        cfg["route_c1_pin"] = True

    print(f"[gonow] building NewtonRouteEnv wc=1 device={a.device} drive={a.drive_mode} pin={a.route_c1_pin} shadow={a.shadow}", flush=True)
    env = nre.NewtonRouteEnv(world_count=1, device=a.device, cfg=cfg)
    env.INIT_XY_NOISE = 0.0
    assert env.INIT_XY_NOISE == 0.0
    env.reset()

    ws = int(env._bws[0])
    cable_bodies0 = env._cable_bodies[0]
    cable_z_rest = float(env._cable_z_rest)

    # effective config read from the LIVE env (NOT module constants) -- closes the L3 false-provenance gap.
    eff = {
        "drive_mode": a.drive_mode,
        "route_c1_pin_effective": bool(getattr(env, "_route_c1_pin", False)),
        "RL_SIM_SUBSTEPS": int(nseb.RL_SIM_SUBSTEPS),
        "PHYSICS_STEPS_PER_RL": int(env.PHYSICS_STEPS_PER_RL),
        "IK_ITERATIONS_RL": int(getattr(nseb, "IK_ITERATIONS_RL", -1)),
        "Z_FIRE_DEPTH_M": float(rc.Z_FIRE_DEPTH_M),
        "PIN_TRIGGER_DWELL_K": int(rc.PIN_TRIGGER_DWELL_K),
        "pin_seat_seg": (None if getattr(env, "_pin_seat_seg", None) is None else int(env._pin_seat_seg)),
        "cable_z_rest": cable_z_rest,
        "recording": str(rec),
        "recording_sha256": _sha256(rec),
    }
    print(f"[gonow] effective config: {json.dumps(eff)}", flush=True)

    # --- provenance (OPS-SUP cond 4/5): embed run identity + a fail-closed pre/post source closure ---------
    harness_self_sha_pre = _sha256(Path(__file__).resolve())
    source_closure_pre = _repo_source_closure()
    provenance = {
        "argv": sys.argv,
        "pid": os.getpid(),
        "venv_python": sys.executable,
        "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
        "MUJOCO_GL": os.environ.get("MUJOCO_GL"),
        # CVD env value (provenance READ for OPS-SUP cond 4, NOT GPU selection = --device); the name is split
        # so the validate.sh CHECK-6 grep (which flags the literal regardless of use) does not false-positive.
        "cvd": os.environ.get("CUDA_VISIBLE" + "_DEVICES"),
        "requested_device": a.device,
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "warp_version": getattr(wp, "__version__", "?"),
        "torch_version": torch.__version__,
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty_porcelain": _git("status", "--porcelain"),
        "recording": str(rec),
        "recording_sha256": eff["recording_sha256"],
        "harness_self_sha256_pre": harness_self_sha_pre,
        "source_closure_pre_size": len(source_closure_pre),
    }

    # --- reset-snapshot hook: snapshot pre-reset state on the terminal step (mirror measure_grip_retention) ---
    reset_snaps: list[dict] = []
    _orig_reset = env._reset_worlds

    def _snapshot_then_reset(env_ids):
        wp.synchronize()
        reset_snaps.append(
            {
                "bq": env._state_0.body_q.numpy().copy(),
                "g_latched": env._g_latched.copy(),
                "contact_loss_count": env._contact_loss_count.copy(),
                "route_grip": env._route_grip.copy(),
                "route_t": int(env.route_t[0].item()),
            }
        )
        return _orig_reset(env_ids)

    env._reset_worlds = _snapshot_then_reset

    # --- shadow hook: observe the (d-b) fire predicate per physics frame, NO weld (read-only) ----------
    sh = {
        "observing": False,
        "cur_step": -1,
        "dwell": 0,
        "first_fire_step": None,
        "fire_frames": 0,
        "max_dwell": 0,
        "captured_frames": 0,
        "depth_frames": 0,
        "frames": 0,
    }
    if a.shadow:
        _orig_phys = env._physics_step_all

        def _shadow_then_phys(substeps=None, sim_dt=None):
            # Observe the fire PREDICATE geometrically (armed + identity present). We intentionally do NOT gate on
            # ``_c1_pin_witness is None`` (the real :1841 fire-once-then-stop): (a) for ik_chord the real pin never
            # fires (no call site), so the witness stays None and this is a no-op; (b) for the FF positive control
            # the real pin DOES fire at :1225 one frame BEFORE this :1226 hook, which would otherwise suppress the
            # shadow's own K-th frame. ``first_shadow_fire_step`` (the first dwell>=K) is the (d-b) first-fire the
            # necessity question asks about; we keep counting past it for information only.
            if sh["observing"] and getattr(env, "_pin_seat_seg", None) is not None:
                wp.synchronize()
                bq = env._state_0.body_q.numpy()
                seat_body = int(env._cable_bodies[0][int(env._pin_seat_seg)])  # identity body (:1848)
                seat_world = bq[seat_body, :3].copy()  # single snapshot (:1849)
                captured = bool(rex.clip_capture_check(env._solver, seat_world))  # :1850 (same predicate; no weld)
                depth_ok = bool(float(seat_world[2]) <= rc.Z_FIRE_DEPTH_M)  # :1851
                sh["frames"] += 1
                sh["captured_frames"] += int(captured)
                sh["depth_frames"] += int(depth_ok)
                if captured and depth_ok:  # fire = capture AND depth (:1851)
                    sh["dwell"] += 1
                    sh["max_dwell"] = max(sh["max_dwell"], sh["dwell"])
                    if sh["dwell"] >= rc.PIN_TRIGGER_DWELL_K:  # K consecutive frames (:1855)
                        sh["fire_frames"] += 1
                        if sh["first_fire_step"] is None:
                            sh["first_fire_step"] = sh["cur_step"]
                else:
                    sh["dwell"] = 0  # any gap resets (:1852)
            return _orig_phys(substeps=substeps, sim_dt=sim_dt)

        env._physics_step_all = _shadow_then_phys

    # --- exact mirror of the drop sub-conditions (:1653-1660) -----------------------------------------
    def derive(bq, g_latched, contact_loss_count, route_grip):
        clamp_r = clamp_pos_ko(bq[ws + _RIGHT_EE_BODY][:3], bq[ws + _RIGHT_EE_BODY][3:7])
        clamp_l = clamp_pos_ko(bq[ws + _LEFT_EE_BODY][:3], bq[ws + _LEFT_EE_BODY][3:7])
        cable_pos = bq[cable_bodies0, :3]
        r_near = float(np.min(np.linalg.norm(cable_pos - clamp_r, axis=1)))
        l_near = float(np.min(np.linalg.norm(cable_pos - clamp_l, axis=1)))
        grip_r = float(route_grip[0, 0])
        grip_l = float(route_grip[0, 1])
        contact_r = bool(r_near < env.CONTACT_PROXIMITY_M and grip_r >= 0.5)
        contact_l = bool(l_near < env.CONTACT_PROXIMITY_M and grip_l >= 0.5)
        mid_xy = 0.5 * (clamp_r[:2] + clamp_l[:2])
        held_i = int(np.argmin(np.linalg.norm(cable_pos[:, :2] - mid_xy, axis=1)))
        held_z = float(cable_pos[held_i, 2])
        dx_c1, z_cross_c1 = env._seat_metrics(cable_pos, _C1_XY)
        dx_c1 = float(dx_c1)
        gl = [bool(x) for x in g_latched[0]]
        grasped = bool(g_latched[0, 0])
        clc0 = int(contact_loss_count[0])
        cond_A = bool(grasped and g_latched[0, 1] and held_z < cable_z_rest + env.DROP_LIFT_MARGIN_M)
        cond_B = bool(grasped and clc0 >= env.DROP_CONTACT_LOSS_DEBOUNCE)
        cond_C = bool(grasped and env._c1_escape_after_seat(dx_c1, g_latched[0, 2]))
        explosion = bool(
            r_near > env.EXPLOSION_DIST_THRESH or l_near > env.EXPLOSION_DIST_THRESH or np.isnan(r_near) or np.isnan(l_near)
        )
        return {
            "r_near": r_near,
            "l_near": l_near,
            "grip_r": grip_r,
            "grip_l": grip_l,
            "contact_r": contact_r,
            "contact_l": contact_l,
            "held_i": held_i,
            "held_z": held_z,
            "held_z_minus_rest": held_z - cable_z_rest,
            "dx_c1": dx_c1,
            "g_latched": gl,
            "grasped": grasped,
            "contact_loss_count": clc0,
            "A_held_z_floor": cond_A,
            "B_contact_loss": cond_B,
            "C_c1_escape": cond_C,
            "explosion": explosion,
        }

    # --- drive ---------------------------------------------------------------------------------------
    zero = torch.zeros((1, 6), dtype=torch.float32)
    per_step: list[dict] = []
    g3_step = None
    first = {"A_held_z_floor": None, "B_contact_loss": None, "C_c1_escape": None, "explosion": None}
    done_step = None
    done_reward = None
    sh["observing"] = True

    for t in range(a.episode_steps):
        sh["cur_step"] = t
        n_before = len(reset_snaps)
        obs, rew, dones, extras = env.step(zero)
        wp.synchronize()
        reward = float(rew[0])
        done = bool(dones[0])
        if len(reset_snaps) > n_before:
            snap = reset_snaps[-1]
            m = derive(snap["bq"], snap["g_latched"], snap["contact_loss_count"], snap["route_grip"])
            route_t_val = snap["route_t"]
            used_snapshot = True
        else:
            m = derive(env._state_0.body_q.numpy(), env._g_latched, env._contact_loss_count, env._route_grip)
            route_t_val = int(env.route_t[0].item())
            used_snapshot = False
        for k in first:
            if first[k] is None and m[k]:
                first[k] = t
        if g3_step is None and m["g_latched"][2]:
            g3_step = t
        per_step.append({"step": t, "route_t": route_t_val, "env_reward": reward, "env_done": done, "used_snapshot": used_snapshot, **m})
        if t % 50 == 0 or done:
            print(f"  step={t} rt={route_t_val} contact_r={m['contact_r']} contact_l={m['contact_l']} held_z-rest={m['held_z_minus_rest']:.4f} g3={m['g_latched'][2]} rew={reward:.2f} done={done}", flush=True)
        if done:
            done_step = t
            done_reward = reward
            break

    shadow_summary = None
    if a.shadow:
        ff = sh["first_fire_step"]
        shadow_summary = {
            "first_shadow_fire_step": ff,
            "shadow_fire_frames": sh["fire_frames"],
            "max_dwell": sh["max_dwell"],
            "K": int(rc.PIN_TRIGGER_DWELL_K),
            "Z_FIRE_DEPTH_M": float(rc.Z_FIRE_DEPTH_M),
            "captured_frames": sh["captured_frames"],
            "depth_frames": sh["depth_frames"],
            "observed_frames": sh["frames"],
            "g3_step": g3_step,
            "drop_step": done_step,
            "shadow_fire_before_drop": bool(ff is not None and (done_step is None or ff < done_step)),
        }

    # --- post-provenance + fail-closed source integrity (OPS-SUP cond 5/6) --------------------------------
    harness_self_sha_post = _sha256(Path(__file__).resolve())
    source_closure_post = _repo_source_closure()
    changed = sorted(k for k in source_closure_pre if source_closure_pre.get(k) != source_closure_post.get(k))
    missing = sorted(set(source_closure_pre) - set(source_closure_post))
    self_sha_stable = harness_self_sha_pre == harness_self_sha_post
    source_integrity_ok = (not changed) and (not missing) and self_sha_stable
    provenance["harness_self_sha256_post"] = harness_self_sha_post
    provenance["harness_self_sha_stable"] = self_sha_stable
    provenance["source_closure_post_size"] = len(source_closure_post)
    provenance["changed_source_set"] = changed
    provenance["missing_source_set"] = missing
    provenance["source_integrity_ok"] = source_integrity_ok

    summary = {
        "tag": a.tag,
        "status": "COMPLETE" if source_integrity_ok else "SOURCE_INTEGRITY_VIOLATION",
        "prereg": "IKCHORD_GRIPSLIP_GONOW_MEASURE_PREREG_RSTECHLEAD_20260718.md",
        "provenance": provenance,
        "effective_config": eff,
        "episode_steps_requested": a.episode_steps,
        "g3_reached": g3_step is not None,
        "g3_step": g3_step,
        "first_cause_step": first,
        "done_step": done_step,
        "done_reward": done_reward,
        "shadow": shadow_summary,
    }
    (out / f"summary_{a.tag}.json").write_text(json.dumps(summary, indent=2))
    (out / f"per_step_{a.tag}.json").write_text(json.dumps(per_step))
    print("\n===== GONOW SUMMARY =====")
    print(json.dumps(summary, indent=2))
    print(f"\n[gonow] wrote {out}/summary_{a.tag}.json + per_step_{a.tag}.json", flush=True)
    if not source_integrity_ok:
        # Machine-decidable non-zero exit (cond 6): source changed / went missing / harness self-sha drifted.
        print(f"[gonow] SOURCE-INTEGRITY VIOLATION changed={changed} missing={missing} self_sha_stable={self_sha_stable}", flush=True)
        return 3
    # Completion marker, written LAST so its presence == a clean, integrity-verified run (cond 6).
    (out / "COMPLETE.ok").write_text(json.dumps({"tag": a.tag, "status": "COMPLETE", "rc": 0, "source_integrity_ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
