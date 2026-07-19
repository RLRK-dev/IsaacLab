# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""P-D1 arm-PD de-risk probe harness for the (d) control-method remediation (gonow_measure lineage).

Design: ``eval_runs/.../ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md`` sec 5 (P-D1).
Builds a wc=1 ``NewtonRouteEnv`` FF whole-route (cable ON / grasp ON / pin ON, nominal recording,
cadence = RL path @4 per design correction #1) and drives ``env.step(zeros)``. With ``--arm-pd`` the
env's per-step arm drive runs through the POSITION-servo ctrl path (``ARM_PD_DRIVE=1``, the probe
branch in ``newton_route_env.py``) instead of the kinematic joint_q write; without it the SAME build
runs the kinematic baseline (one-variable contrast, same seed/recording).

Measurement legs (design sec 5): the harness wraps ``_physics_step_all`` and logs per PHYSICS FRAME
the realized arm q / qd and the commanded ctrl (``control.joint_target_pos`` readback, qd-indexed)
into an npz (L-P1 tracking; L-P3 effort is derived offline as ke*(ctrl-q)-kd*qd clipped at the cap,
exact for the affine servo). Predicate parity fields (L-P2: g_latched / pin fire / drop causes)
mirror gonow_measure's ``derive()``. L-P6 build readback runs inside the env (``[ARMPD]`` line).

OBSERVATION + probe-branch drive only; no landing. Physical-validity judgment is Rs's; this script
emits NUMBERS. Run (env_isaaclab7 venv, CVD pinned):
    CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \\
        thread_isaac_lab/scripts/armpd_probe.py --device cuda:0 --episode-steps 900 \\
        --arm-pd --tag r1_pd --outbox <FRESH>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
    ap.add_argument("--arm-pd", action="store_true", help="drive the arm via the POSITION-servo ctrl path (probe branch)")
    ap.add_argument(
        "--neutralize-only",
        action="store_true",
        help="L-P0 mode: neutralize the imported XML arm actuators, keep the kinematic drive (design v1.2)",
    )
    ap.add_argument(
        "--neg-stale",
        action="store_true",
        help="R3 negative control (v1.5 sec12.1): freeze arm ctrl at the route-start pose; score |q - rec[t]| offline",
    )
    ap.add_argument("--gains-scale", type=float, default=1.0, help="ke/kd scale (L-P5 negative control = 0.1); caps NOT scaled")
    ap.add_argument("--ramp-frames", type=int, default=0, help="M-5 activation ramp length in physics frames (0 = off)")
    ap.add_argument("--episode-steps", type=int, default=900)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--recording", default=str(_GOLDEN))
    ap.add_argument("--tag", default="armpd")
    ap.add_argument("--outbox", required=True)
    a = ap.parse_args()

    # Probe flags MUST be exported before env construction (the builder + __init__ read os.environ).
    assert not (a.arm_pd and a.neutralize_only), "--arm-pd and --neutralize-only are mutually exclusive"
    assert not (a.neg_stale and not a.arm_pd), "--neg-stale requires --arm-pd (frozen-ctrl PD run)"
    for _k in ("ARM_PD_DRIVE", "ARM_XML_ACT_NEUTRALIZE", "ARM_PD_GAINS_SCALE", "ARM_PD_RAMP_FRAMES", "ARM_PD_STALE_CTRL"):
        os.environ.pop(_k, None)  # defensive: never inherit a probe flag from the launcher's shell
    if a.arm_pd:
        os.environ["ARM_PD_DRIVE"] = "1"
        os.environ["ARM_PD_GAINS_SCALE"] = str(a.gains_scale)
        os.environ["ARM_PD_RAMP_FRAMES"] = str(a.ramp_frames)
        if a.neg_stale:
            os.environ["ARM_PD_STALE_CTRL"] = "1"
    elif a.neutralize_only:
        os.environ["ARM_XML_ACT_NEUTRALIZE"] = "1"

    import numpy as np

    np.random.seed(0)
    import torch
    import warp as wp

    import newton_route_env as nre
    import newton_skill_env_base as nseb
    import route_env_config as rc
    from newton_route_env import _C1_XY, _LEFT_EE_BODY, _RIGHT_EE_BODY, clamp_pos_ko

    # --- pre-build provenance (gonow B2/B3/B4 bars, unchanged) -------------------------------------------
    cvd = os.environ.get("CUDA_VISIBLE_DEVICES")
    if not cvd:
        print("[armpd] CVD-UNPINNED VIOLATION: CUDA_VISIBLE_DEVICES is null/empty. exit 2", flush=True)
        raise SystemExit(2)
    if sys.prefix != "/home/rlrk/env_isaaclab7":
        print(f"[armpd] INTERPRETER VIOLATION: sys.prefix must be /home/rlrk/env_isaaclab7, got {sys.prefix}. exit 2", flush=True)
        raise SystemExit(2)
    _m = re.fullmatch(r"cuda:(\d+)", a.device)
    if _m is None:
        print(f"[armpd] DEVICE VIOLATION: --device must be cuda:N, got {a.device!r}. exit 2", flush=True)
        raise SystemExit(2)
    requested_cuda_index = int(_m.group(1))
    harness_self_sha_pre = _sha256(Path(__file__).resolve())
    source_closure_import = _repo_source_closure()

    rec = Path(a.recording)
    assert rec.exists(), f"recording (GOLDEN) not found: {rec}"
    out = Path(a.outbox)
    if out.exists():
        print(f"[armpd] FRESH-OUTBOX VIOLATION: outbox leaf already exists: {out}", flush=True)
        raise SystemExit(2)
    out.mkdir(parents=True, exist_ok=False)

    cfg = {
        "grasp_actuation": True,
        "route_executor_impl": "route_executor",
        "route_recording_npz": str(rec),
        "g1_scene_align": True,
        "route_drive_mode": "feedforward",  # P-D1 = FF whole-route (design sec 5)
        "route_c2_scene": True,
        "route_c1_pin": True,  # pin ON (real fire, no shadow)
    }

    print(
        f"[armpd] building NewtonRouteEnv wc=1 device={a.device} arm_pd={a.arm_pd} "
        f"gains_scale={a.gains_scale} ramp_frames={a.ramp_frames}",
        flush=True,
    )
    env = nre.NewtonRouteEnv(world_count=1, device=a.device, cfg=cfg)
    env.INIT_XY_NOISE = 0.0
    assert env.INIT_XY_NOISE == 0.0
    # Flag readback: the env must have taken the SAME path the args requested (K6 anti-vacuous).
    assert bool(getattr(env, "_arm_pd_drive", False)) == bool(a.arm_pd), (
        f"env._arm_pd_drive={getattr(env, '_arm_pd_drive', None)} != --arm-pd {a.arm_pd}"
    )
    assert bool(getattr(env, "_arm_xml_act_neutralize", False)) == bool(a.arm_pd or a.neutralize_only), (
        f"env._arm_xml_act_neutralize={getattr(env, '_arm_xml_act_neutralize', None)} != requested"
    )
    env.reset()

    ws = int(env._bws[0])
    cable_bodies0 = env._cable_bodies[0]
    cable_z_rest = float(env._cable_z_rest)
    arm_q_idx = env._arm_ow_maps["arm_ow_q_idx"]  # 12 arm joint_q coords (world 0)
    arm_qd_idx = env._arm_ow_maps["arm_ow_qd_idx"]  # 12 arm DOF coords = joint_target_pos index space

    # --- M-4 boundary sync (harness-side, one-time): the servo target seeded at build = the build pose;
    # reset moved the arms (settle + P0 + grasp prep) under the per-frame kinematic hold. Sync ctrl :=
    # realized q once so the route starts from a matched target (no stale-target step at frame 0).
    if a.arm_pd:
        wp.synchronize()
        _q_now = env._state_0.joint_q.numpy()[arm_q_idx]
        _jtp = env._control.joint_target_pos.numpy()
        _jtp[arm_qd_idx] = _q_now
        env._control.joint_target_pos.assign(_jtp)
        _rb = env._control.joint_target_pos.numpy()[arm_qd_idx]
        assert np.allclose(_rb, _q_now, atol=1e-9), "post-reset ctrl sync readback mismatch (write did not land)"
        print(f"[armpd] post-reset ctrl sync: |q|max={float(np.max(np.abs(_q_now))):.4f} (12 dofs)", flush=True)

    # Arm servo gains readback (world 0) for the offline effort derivation (L-P3) -- from the BUILT model.
    arm_gains = None
    if a.arm_pd:
        arm_gains = {
            "ke": [float(x) for x in env._model.joint_target_ke.numpy()[arm_qd_idx]],
            "kd": [float(x) for x in env._model.joint_target_kd.numpy()[arm_qd_idx]],
            "effort_cap": [float(x) for x in env._model.joint_effort_limit.numpy()[arm_qd_idx]],
        }

    eff = {
        "mode": (
            ("arm_pd_stale_neg" if a.neg_stale else "arm_pd")
            if a.arm_pd
            else ("l_p0_neutralize" if a.neutralize_only else "kinematic_baseline")
        ),
        "arm_pd_effective": bool(getattr(env, "_arm_pd_drive", False)),
        "neutralize_effective": bool(getattr(env, "_arm_xml_act_neutralize", False)),
        "stale_ctrl_effective": bool(getattr(env._route, "_arm_pd_stale_ctrl", False)),
        "repose_frame_index": int(getattr(env, "_armpd_repose_frame_index", -1)),
        "gains_scale": float(a.gains_scale),
        "ramp_frames": int(a.ramp_frames),
        "drive_mode": "feedforward",
        "route_c1_pin_effective": bool(getattr(env, "_route_c1_pin", False)),
        "RL_SIM_SUBSTEPS": int(nseb.RL_SIM_SUBSTEPS),
        "PHYSICS_STEPS_PER_RL": int(env.PHYSICS_STEPS_PER_RL),
        "Z_FIRE_DEPTH_M": float(rc.Z_FIRE_DEPTH_M),
        "PIN_TRIGGER_DWELL_K": int(rc.PIN_TRIGGER_DWELL_K),
        "pin_seat_seg": (None if getattr(env, "_pin_seat_seg", None) is None else int(env._pin_seat_seg)),
        "cable_z_rest": cable_z_rest,
        "recording": str(rec),
        "recording_sha256": _sha256(rec),
        "arm_gains": arm_gains,
    }
    print(f"[armpd] effective config: {json.dumps(eff)}", flush=True)

    # --- post-build device provenance (gonow B4 hard bar, unchanged) -------------------------------------
    torch_cuda: dict = {}
    try:
        if torch.cuda.is_available():
            _idx = torch.cuda.current_device()
            _props = torch.cuda.get_device_properties(_idx)
            torch_cuda = {
                "current_device": int(_idx),
                "device_name": torch.cuda.get_device_name(_idx),
                "uuid": str(getattr(_props, "uuid", "")),
                "device_count": int(torch.cuda.device_count()),
            }
    except Exception as e:  # noqa: BLE001
        torch_cuda = {"error": type(e).__name__}
    source_closure_run_start = _repo_source_closure()
    provenance = {
        "argv": sys.argv,
        "pid": os.getpid(),
        "venv_python": sys.executable,
        "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
        "MUJOCO_GL": os.environ.get("MUJOCO_GL"),
        "cvd": cvd,
        "requested_device": a.device,
        "env_device": str(getattr(env, "device", None)),
        "torch_cuda": torch_cuda,
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "warp_version": getattr(wp, "__version__", "?"),
        "torch_version": torch.__version__,
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty_porcelain": _git("status", "--porcelain"),
        "recording": str(rec),
        "recording_sha256": eff["recording_sha256"],
        "harness_self_sha256_pre": harness_self_sha_pre,
        "source_closure_import": source_closure_import,
        "source_closure_run_start": source_closure_run_start,
    }

    _dev_fail = None
    if not torch.cuda.is_available():
        _dev_fail = "torch.cuda not available"
    elif "error" in torch_cuda:
        _dev_fail = f"device probe error: {torch_cuda.get('error')}"
    elif str(getattr(env, "device", None)) != a.device:
        _dev_fail = f"env.device {getattr(env, 'device', None)!r} != requested {a.device!r}"
    elif int(torch_cuda.get("current_device", -1)) != requested_cuda_index:
        _dev_fail = f"current_device {torch_cuda.get('current_device')} != requested index {requested_cuda_index}"
    elif int(torch_cuda.get("device_count", 0)) <= requested_cuda_index:
        _dev_fail = f"device_count {torch_cuda.get('device_count')} <= requested index {requested_cuda_index}"
    device_provenance_ok = _dev_fail is None
    provenance["requested_cuda_index"] = requested_cuda_index
    provenance["device_provenance_ok"] = device_provenance_ok
    if not device_provenance_ok:
        print(f"[armpd] DEVICE-PROVENANCE VIOLATION: {_dev_fail}. exit 2 before drive", flush=True)
        raise SystemExit(2)

    # --- reset-snapshot hook (terminal-step state, mirror gonow) -----------------------------------------
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

    # --- per-physics-frame tracking logger (L-P1/L-P3 raw): wrap _physics_step_all -----------------------
    fr = {"observing": False, "cur_step": -1}
    fr_q: list = []
    fr_qd: list = []
    fr_ctrl: list = []
    fr_intended: list = []  # sec12.1 scoring source: the per-frame intended (recorded) arm target
    fr_cable_vmax: list = []  # A-4: per-frame max |cable body velocity| (world 0)
    fr_pen_min: list = []  # A-4: per-frame min contact dist (negative = penetration), nan if unavailable
    fr_rl_step: list = []
    fr_route_t: list = []
    _nan12 = np.full(12, np.nan)
    cable_b0 = np.asarray(cable_bodies0, dtype=np.int64)
    _orig_phys = env._physics_step_all

    def _pen_min_dist():
        # A-4 raw: min contact dist over ACTIVE contacts (mujoco_warp: nacon + contact.dist prefix).
        # No active contact -> 0.0 (no penetration). Global (all pairs) = conservative superset of
        # "arm-involved" (declared as the implemented form in the prereg).
        try:
            d = env._solver.mjw_data
            nacon = int(np.ravel(d.nacon.numpy())[0])
            if nacon <= 0:
                return 0.0
            dist = np.ravel(d.contact.dist.numpy())[:nacon]
            return float(np.min(dist))
        except Exception:  # noqa: BLE001
            return float("nan")

    def _log_then_phys(substeps=None, sim_dt=None):
        r = _orig_phys(substeps=substeps, sim_dt=sim_dt)
        if fr["observing"]:
            wp.synchronize()
            fr_q.append(env._state_0.joint_q.numpy()[arm_q_idx].copy())
            fr_qd.append(env._state_0.joint_qd.numpy()[arm_qd_idx].copy())
            fr_ctrl.append(env._control.joint_target_pos.numpy()[arm_qd_idx].copy())
            _it = getattr(env._route, "_last_ff_arm_target", None)
            fr_intended.append(_it.copy() if _it is not None else _nan12)
            fr_cable_vmax.append(float(np.max(np.abs(env._state_0.body_qd.numpy()[cable_b0]))))
            fr_pen_min.append(_pen_min_dist())
            fr_rl_step.append(fr["cur_step"])
            fr_route_t.append(int(env.route_t[0].item()))
        return r

    env._physics_step_all = _log_then_phys

    # --- exact mirror of the drop sub-conditions (gonow derive, unchanged) -------------------------------
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

    # --- drive -------------------------------------------------------------------------------------------
    zero = torch.zeros((1, 6), dtype=torch.float32)
    per_step: list[dict] = []
    bq_steps: list = []  # per-RL-step full body_q [nbody, 7] -- the offline video-replay source (design sec5 video leg)
    g3_step = None
    first = {"A_held_z_floor": None, "B_contact_loss": None, "C_c1_escape": None, "explosion": None}
    done_step = None
    done_reward = None
    pin_fire_step = None
    fr["observing"] = True

    for t in range(a.episode_steps):
        fr["cur_step"] = t
        n_before = len(reset_snaps)
        obs, rew, dones, extras = env.step(zero)
        wp.synchronize()
        bq_steps.append(env._state_0.body_q.numpy().copy())
        reward = float(rew[0])
        done = bool(dones[0])
        if pin_fire_step is None and getattr(env, "_c1_pin_witness", None) is not None:
            pin_fire_step = t  # first RL step at which the real pin fire witness exists
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
            print(
                f"  step={t} rt={route_t_val} contact_r={m['contact_r']} contact_l={m['contact_l']} "
                f"held_z-rest={m['held_z_minus_rest']:.4f} g3={m['g_latched'][2]} rew={reward:.2f} done={done}",
                flush=True,
            )
        if done:
            done_step = t
            done_reward = reward
            break

    fr["observing"] = False

    # --- frame arrays + in-harness quick tracking stats (bar SCORING happens offline vs the frozen bars) --
    q_arr = np.asarray(fr_q, dtype=np.float64)
    qd_arr = np.asarray(fr_qd, dtype=np.float64)
    ctrl_arr = np.asarray(fr_ctrl, dtype=np.float64)
    track = None
    if a.arm_pd and len(q_arr):
        err = np.abs(q_arr - ctrl_arr)
        track = {
            "frames": int(err.shape[0]),
            "max_abs_err_rad": float(np.max(err)),
            "p99_abs_err_rad": float(np.percentile(err, 99)),
            "per_joint_max_rad": [float(x) for x in np.max(err, axis=0)],
        }
        print(f"[armpd] quick tracking: frames={track['frames']} max={track['max_abs_err_rad']:.5f} p99={track['p99_abs_err_rad']:.5f}", flush=True)
    np.savez_compressed(
        out / f"armpd_frames_{a.tag}.npz",
        q=q_arr,
        qd=qd_arr,
        ctrl=ctrl_arr,
        bq_steps=np.asarray(bq_steps, dtype=np.float32),
        intended=np.asarray(fr_intended, dtype=np.float64),
        cable_vmax=np.asarray(fr_cable_vmax, dtype=np.float64),
        pen_min=np.asarray(fr_pen_min, dtype=np.float64),
        rl_step=np.asarray(fr_rl_step, dtype=np.int64),
        route_t=np.asarray(fr_route_t, dtype=np.int64),
        arm_q_idx=np.asarray(arm_q_idx, dtype=np.int64),
        arm_qd_idx=np.asarray(arm_qd_idx, dtype=np.int64),
        ke=np.asarray(arm_gains["ke"] if arm_gains else [], dtype=np.float64),
        kd=np.asarray(arm_gains["kd"] if arm_gains else [], dtype=np.float64),
        effort_cap=np.asarray(arm_gains["effort_cap"] if arm_gains else [], dtype=np.float64),
    )

    # --- post-drive source integrity (gonow B1/B2, unchanged) --------------------------------------------
    harness_self_sha_post = _sha256(Path(__file__).resolve())
    source_closure_run_end = _repo_source_closure()
    changed = sorted(k for k in source_closure_import if source_closure_import.get(k) != source_closure_run_end.get(k))
    missing = sorted(set(source_closure_import) - set(source_closure_run_end))
    added_during_build = sorted(set(source_closure_run_start) - set(source_closure_import))
    added_during_drive = sorted(set(source_closure_run_end) - set(source_closure_run_start))
    build_added_unstable = sorted(
        k for k in added_during_build if source_closure_run_start.get(k) != source_closure_run_end.get(k)
    )
    self_sha_stable = harness_self_sha_pre == harness_self_sha_post
    source_integrity_ok = (
        (not changed) and (not missing) and (not added_during_drive) and (not build_added_unstable)
        and self_sha_stable and device_provenance_ok
    )
    provenance["harness_self_sha256_post"] = harness_self_sha_post
    provenance["harness_self_sha_stable"] = self_sha_stable
    provenance["source_closure_run_end"] = source_closure_run_end
    provenance["changed_source_set"] = changed
    provenance["missing_source_set"] = missing
    provenance["added_during_build"] = added_during_build
    provenance["added_during_drive"] = added_during_drive
    provenance["build_added_unstable"] = build_added_unstable
    provenance["source_integrity_ok"] = source_integrity_ok

    summary = {
        "tag": a.tag,
        "status": "COMPLETE" if source_integrity_ok else "SOURCE_INTEGRITY_VIOLATION",
        "prereg": "ARM_CONTROL_PD1_PROBE_PREREG_RSTECHLEAD_20260719.md",
        "provenance": provenance,
        "effective_config": eff,
        "episode_steps_requested": a.episode_steps,
        "g3_reached": g3_step is not None,
        "g3_step": g3_step,
        "first_cause_step": first,
        "done_step": done_step,
        "done_reward": done_reward,
        "pin_fire_step": pin_fire_step,
        "route_start_repose_count": int(getattr(env, "_armpd_repose_count", 0)),
        "quick_tracking": track,
        "frames_logged": int(q_arr.shape[0]) if len(q_arr) else 0,
    }
    (out / f"summary_{a.tag}.json").write_text(json.dumps(summary, indent=2))
    (out / f"per_step_{a.tag}.json").write_text(json.dumps(per_step))
    print("\n===== ARMPD SUMMARY =====")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("provenance",)}, indent=2))
    print(f"\n[armpd] wrote {out}/summary_{a.tag}.json + per_step_{a.tag}.json + armpd_frames_{a.tag}.npz", flush=True)
    if not source_integrity_ok:
        print(f"[armpd] SOURCE-INTEGRITY VIOLATION changed={changed} missing={missing} self_sha_stable={self_sha_stable}", flush=True)
        return 3
    (out / "COMPLETE.ok").write_text(json.dumps({"tag": a.tag, "status": "COMPLETE", "rc": 0, "source_integrity_ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
