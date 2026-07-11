# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""gate-6 diagnostic CONTROL: full-fire with route_c2_scene=False (no C2 clip).

Confirmation-bias guard for the gate-6 NUMERIC_NOGO read. The main gate-6 run (route_c2_scene=True) stalls at
phase-3 with a grip-loss. Two competing causes: (a) comp5 C2-clip PRESENCE perturbs the route grip, vs (b) FORK-1
= the MW env-core close-kinematics diverges from the recording source substrate (C2-independent). This control
replays the SAME recording + SAME D rho=0 feedforward on the SAME MW env-core but with the C2 clip REMOVED. If
the phase-3 grip-loss / early-done ALSO occurs here, the C2-clip is exonerated (FORK-1 confirmed). If the grip
holds through phase-3 here, the C2-clip presence is implicated (comp5 defect). Numeric-only (no render): the
control question is a coarse binary (does phase-3 grip-loss occur without C2), above pixel scale; the mechanism
was already video-established in the main run.

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp5_c2seat_control_noC2.py
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

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "0", (
    f"control runs the as-coded substrate on cuda:0 ONLY; got {os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')!r}"
)
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.pop("DISPLAY", None)

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402
import route_env_config as rc  # noqa: E402
import torch  # noqa: E402
import warp as wp  # noqa: E402

GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT_JSON = _EVAL / "comp5_c2seat_control_noC2_result.json"


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


def main():
    print("[control] building full-fire env (route_c2_scene=False = NO C2 clip, feedforward, cuda:0) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": False,  # CONTROL: C2 clip REMOVED (vs the gate-6 run's True)
        },
    )
    m = env._solver.mj_model
    d = env._solver.mj_data
    pads, cables = _pad_and_cable_geoms(m)

    env.reset()
    cable_ids = env._cable_bodies[0]
    n_phases = int(rc.N_ROUTE_PHASES)
    zero = torch.zeros((1, 6), dtype=torch.float32)

    series = {"t": [], "phase": [], "z_c1_mm": [], "pad_cable": []}
    max_phase = -1
    early_done = None
    t = 0
    while t < env.MAX_EPISODE_STEPS:
        _, phase_peek, _, _ = env._route.step_target(t)
        _, _, dones, _ = env.step(zero)
        if bool(dones[0]):
            early_done = t
            print(f"[control] EARLY DONE at t={t}")
            break
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        cable_pos = bq[cable_ids, :3]
        z_c1, _flank = env._c1_retention_m(cable_pos)
        ncon = _pad_cable_contacts(d, pads, cables)
        max_phase = max(max_phase, int(phase_peek))
        series["t"].append(t)
        series["phase"].append(int(phase_peek))
        series["z_c1_mm"].append(round(float(z_c1) * 1e3, 3))
        series["pad_cable"].append(int(ncon))
        if t % 60 == 0:
            print(f"[control] t={t} phase={phase_peek} z_c1={z_c1 * 1e3:.1f}mm pad={ncon}")
        t += 1

    # phase at which pad-cable contact first collapses to 0 after grasp (grip-loss onset), for cross-run compare
    grip_loss_t = None
    grasped = False
    for i, pc in enumerate(series["pad_cable"]):
        if pc >= 10:
            grasped = True
        elif grasped and pc == 0:
            grip_loss_t = series["t"][i]
            break

    result = {
        "control": "route_c2_scene=False (NO C2 clip)",
        "cell": "x0_y0",
        "drive": "feedforward (D rho=0)",
        "steps_run": t,
        "early_done": early_done,
        "n_phases": n_phases,
        "max_phase_reached": max_phase,
        "full_fire": (early_done is None) and (max_phase >= n_phases - 1),
        "grip_loss_first_zero_pad_t": grip_loss_t,
        "grip_loss_phase": (series["phase"][series["t"].index(grip_loss_t)] if grip_loss_t is not None else None),
        "pad_cable_max": max(series["pad_cable"]) if series["pad_cable"] else 0,
        "z_c1_end_mm": series["z_c1_mm"][-1] if series["z_c1_mm"] else None,
        "interpretation": (
            "If early-done/phase-3-stall matches the route_c2_scene=True run -> C2-clip exonerated (FORK-1). "
            "If full-fire completes here -> C2-clip presence implicated."
        ),
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
