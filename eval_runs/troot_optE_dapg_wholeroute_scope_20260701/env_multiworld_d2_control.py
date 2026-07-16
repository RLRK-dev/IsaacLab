# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""D-2 control (design v1.9 §21.10.1): use_mujoco_cpu=False settle test at world_count=4. cuda:0, no training.

D-1 confirmed solver.use_mujoco_cpu=True on the production build path (CPU branch steps ONLY the single-world
template -> worlds>0 frozen, by construction). D-2 is the CONTROL: force use_mujoco_cpu=False (warp/mjw step)
via a probe-local make_solver monkeypatch (source unchanged) and re-run the settle test.

PRE-REGISTERED PREDICTION (p5 §21.10.1, recorded BEFORE the run):
  - worlds>0 START SETTLING (all 4 worlds' cables descend from spawn z=809 toward ~804) -> hypothesis fully
    confirmed (the freeze was the CPU branch, nothing else);
  - the grasp 4-bar MAY FLOP (finger coords drift): the mjw eq re-poke is DEFERRED (base:1357/:1437 -- the
    4-bar eq_solref stiffening was applied to the CPU mj_model template only). A flop here is NOT a D-2
    failure; it is the S8-gap list made real (charter fork-A work item #1).

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/env_multiworld_d2_control.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
assert _CVD == "0", f"D-2 runs the warp substrate on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env  # noqa: E402, F401  (side-effect: SOLVER_BACKEND="mujoco")
import newton_skill_env_base as base  # noqa: E402
import route_env_config as rc  # noqa: E402
from newton_route_env import physics_finger_obs  # noqa: E402
from task_config import FINGER_OPEN_POS  # noqa: E402

OUT = _EVAL / "env_multiworld_d2_control_result.json"
NW = 4
SEAT_SEG = 27

# --- probe-local monkeypatch: force the warp path (use_mujoco_cpu=False); source unchanged ---
_orig_make_solver = base.make_solver


def _make_solver_warp(model, backend=base.SOLVER_BACKEND, use_mujoco_cpu=None, enable_cable_contacts=False):  # noqa: ARG001
    return _orig_make_solver(model, backend=backend, use_mujoco_cpu=False, enable_cable_contacts=enable_cable_contacts)


base.make_solver = _make_solver_warp


def main():
    fkm, fks, _ = base.build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cuda:0"
    )
    scene = base.build_multiworld_scene(
        fkm, fks, NW, "cuda:0",
        add_support_clips=False, add_target_clip=True, target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z,
        add_c2_clip=True, c2_xy=rc.ROUTE_C2_XY, grasp_actuation=True, perclip_pin=True,
    )
    solver, model = scene["solver"], scene["model"]
    st0, st1, control, contacts = scene["state_0"], scene["state_1"], scene["control"], scene["contacts"]
    cable_bodies = scene["cable_bodies"]
    jws = scene["jws"]  # per-world joint_q start (arm block)
    r = {"world_count": NW, "seat_seg": SEAT_SEG,
         "solver_use_mujoco_cpu": bool(getattr(solver, "use_mujoco_cpu", None)),
         "prediction_preregistered": "all worlds settle 809->~804; 4-bar may flop (mjw eq re-poke DEFERRED)"}

    seat_ids = [int(cable_bodies[w][SEAT_SEG]) for w in range(NW)]
    # per-world joint_q start = joint_q_start[joint_world_start[w]] (env:718-722: the cable FREE root adds
    # 6 extra coords/world, so a joint-INDEX slice is wrong for world>=1)
    _jqs = model.joint_q_start.numpy()
    arm_q_start = [int(_jqs[int(jws[w])]) for w in range(NW)]

    def _read():
        bq = st0.body_q.numpy()
        jq = st0.joint_q.numpy()
        z = [round(float(bq[seat_ids[w], 2]) * 1e3, 2) for w in range(NW)]
        fingers = []
        for w in range(NW):
            try:
                rf, lf = physics_finger_obs(jq, arm_q_start[w])
                fingers.append([round(float(rf), 4), round(float(lf), 4)])
            except Exception:  # noqa: BLE001
                fingers.append(None)
        return z, fingers

    z0, f0 = _read()
    trace = {"t": [0], "seat_z_mm": [z0]}
    steps_ok, step_err = True, None
    try:
        for t in range(1, 301):
            st0.clear_forces()
            model.collide(st0, contacts)
            solver.step(st0, st1, control, contacts, base.SIM_DT)
            st0, st1 = st1, st0  # closure `_read` sees the rebound st0 (shared cell)
            if t % 60 == 0:
                z_mid, _ = _read()
                trace["t"].append(t)
                trace["seat_z_mm"].append(z_mid)
    except Exception as e:  # noqa: BLE001
        steps_ok, step_err = False, f"{type(e).__name__}: {str(e)[:160]}"

    # final read from the CURRENT st0 (post-swap)
    bq = st0.body_q.numpy()
    jq = st0.joint_q.numpy()
    z1 = [round(float(bq[seat_ids[w], 2]) * 1e3, 2) for w in range(NW)]
    f1 = []
    for w in range(NW):
        try:
            rf, lf = physics_finger_obs(jq, arm_q_start[w])
            f1.append([round(float(rf), 4), round(float(lf), 4)])
        except Exception:  # noqa: BLE001
            f1.append(None)
    trace["t"].append(300)
    trace["seat_z_mm"].append(z1)

    dz = [round(z1[w] - z0[w], 2) for w in range(NW)]
    settled = [bool(d < -2.0) for d in dz]  # descended >2mm from spawn = integrating
    finger_drift = []
    for w in range(NW):
        if f0[w] is not None and f1[w] is not None:
            finger_drift.append(round(max(abs(f1[w][0] - f0[w][0]), abs(f1[w][1] - f0[w][1])), 4))
        else:
            finger_drift.append(None)

    r["D2"] = {"steps_ok": steps_ok, "step_err": step_err, "seat_z0_mm": z0, "seat_z300_mm": z1,
               "dz_mm": dz, "per_world_settling": settled, "all_worlds_integrate": bool(all(settled)),
               "finger_sum_open0": f0, "finger_sum_300": f1, "finger_drift_rad": finger_drift,
               "flop_observed": bool(any(d is not None and d > 0.05 for d in finger_drift))}

    if not steps_ok:
        disp = f"WARP-STEP CRASH: {step_err} -> S8-gap (charter evidence; the warp path does not run this scene yet)"
    elif all(settled):
        disp = ("CONFIRMED: with use_mujoco_cpu=False ALL worlds integrate (settle) -> the freeze was the CPU "
                "branch, by construction. " + ("4-bar flop observed (S8-gap #1 made real)."
                                               if r["D2"]["flop_observed"] else "No 4-bar flop in the settle window."))
    elif settled[0] and not any(settled[1:]):
        disp = "REFUTED-PARTIAL: worlds>0 still frozen under warp step -> the CPU branch is NOT the whole story"
    else:
        disp = f"MIXED: per-world settling={settled} -> raw trace attached; p5 to rule"
    r["VERDICT"] = {"disposition": disp}
    OUT.write_text(json.dumps({**r, "trace": trace}, indent=2))
    print(json.dumps(r, indent=2))
    print(f"\n[D-2] use_mujoco_cpu={r['solver_use_mujoco_cpu']} dz={dz} settling={settled} "
          f"finger_drift={finger_drift}")
    print(f"[D-2] VERDICT: {disp}  -> {OUT}")
    return 0 if (steps_ok and all(settled)) else 2


if __name__ == "__main__":
    sys.exit(main())
