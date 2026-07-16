# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(c) E-1 clean demo -- per-world hold + BODY-INDEX correctness (design v1.8 §21.9). REAL env, cuda:0, no training.

p5's final (c) gate: E-2 proved activation is per-world (count 24->25) but NOT that the active eq constrains the
CORRECT world's cable body (flat_eq for world 2 must hold world-2's body, not world-0's -- a replicate/body-index
mismap is invisible to E-2 and would silently corrupt training). Two checks:
  MAP  enable newton flat_eq (world 2's seat pin) + notify -> the flipped mjw_data.eq_active[world, eq] must be at
       WORLD 2 (positional mapping check, no physics).
  E-1  release the gripper (all worlds) + step -> the PINNED world's seat body is HELD while non-pin worlds fall;
       the least-moved world must be WORLD 2 (physical body-index proof = STEP 8-10 behaviour).
Mechanism per §21.9.2: equality_constraint_enabled[flat_eq]=True + notify(CONSTRAINT_PROPERTIES) (ref-pose anchor
is computed at notify -> hold-in-place; no world anchor to set). E-1 FAIL => replicate/body-index bug, fix before (c).

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_multiworld_E1_bodyindex.py
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
assert _CVD == "0", f"E-1 demo runs the real env on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import route_executor as rex  # noqa: E402
import warp as wp  # noqa: E402
from newton._src.solvers.flags import SolverNotifyFlags  # noqa: E402
from task_config import GRIPPER_DRIVER_OPEN_RAD  # noqa: E402

GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = _EVAL / "pin_multiworld_E1_bodyindex_result.json"
NW = 4
SEAT_SEG = 27
PIN_WORLD = 2
CP = int(SolverNotifyFlags.CONSTRAINT_PROPERTIES)


def _no_auto_fire(self):
    self._pin_onset_frame = None
    self._pin_seat_seg = None
    self._route_rec_step_f = None


def _seat(env, w):
    return env._state_0.body_q.numpy()[int(env._cable_bodies[w][SEAT_SEG]), :3].astype(float)


def main():
    r = {"world_count": NW, "seat_seg": SEAT_SEG, "pin_world": PIN_WORLD}
    nre.NewtonRouteEnv._wire_c1_pin_from_recording = _no_auto_fire
    print("[E-1] building real NewtonRouteEnv world_count=4 ...")
    env = nre.NewtonRouteEnv(world_count=NW, device="cuda:0", cfg={
        "grasp_actuation": True, "route_executor_impl": "route_executor", "route_recording_npz": str(GOLDEN_NPZ),
        "g1_scene_align": True, "route_drive_mode": "feedforward", "route_c2_scene": True, "route_c1_pin": True,
    })
    env.reset()

    b1 = env._model.equality_constraint_body1.numpy()
    b2 = env._model.equality_constraint_body2.numpy()
    seat_body = int(env._cable_bodies[PIN_WORLD][SEAT_SEG])
    cand = [i for i in range(len(b1)) if int(b1[i]) == seat_body and int(b2[i]) == -1]
    if not cand:
        r["ERROR"] = f"no connect-to-world eq with body1=={seat_body}"
        OUT.write_text(json.dumps(r, indent=2))
        print(json.dumps(r, indent=2))
        return 2
    flat_eq = cand[0]
    r["pin_flat_eq"] = flat_eq
    r["seat_body_newton"] = seat_body

    # --- MAP: enable newton flat_eq + notify -> which mjw (world, eq) flips? must be WORLD 2 ---
    ea_before = env._solver.mjw_data.eq_active.numpy().copy()
    en = env._model.equality_constraint_enabled.numpy()
    en[flat_eq] = True
    env._model.equality_constraint_enabled.assign(en)
    env._solver.notify_model_changed(CP)  # ref-pose anchor computed here (hold-in-place); no world anchor set
    ea_after = env._solver.mjw_data.eq_active.numpy()
    flipped = np.argwhere((~ea_before) & ea_after)  # (world, eq) pairs newly active
    flipped_list = [[int(w), int(e)] for w, e in flipped]
    map_world = int(flipped[0][0]) if len(flipped) == 1 else None
    r["MAP"] = {"flipped_world_eq": flipped_list, "maps_to_world": map_world,
                "PASS": bool(len(flipped) == 1 and map_world == PIN_WORLD)}

    # --- E-1: release the gripper (all worlds), step, find the HELD (least-moved) world ---
    p0 = [_seat(env, w) for w in range(NW)]
    rex._set_gripper_target(env._control, env._arm_ow_maps["all_driver_dofs"], GRIPPER_DRIVER_OPEN_RAD)
    step_ok, step_err = True, None
    try:
        for _ in range(200):
            env._physics_step_all()
        wp.synchronize()
    except Exception as e:  # noqa: BLE001
        step_ok, step_err = False, f"{type(e).__name__}: {str(e)[:150]}"
    p1 = [_seat(env, w) for w in range(NW)]
    move = [round(float(np.linalg.norm(p1[w] - p0[w])) * 1e3, 2) for w in range(NW)]
    held_world = int(np.argmin(move))
    others = [move[w] for w in range(NW) if w != PIN_WORLD]
    # PASS: the pinned world is the least-moved (held) AND clearly held vs the moving others
    e1_pass = bool(held_world == PIN_WORLD and move[PIN_WORLD] < 5.0 and min(others) > 10.0)
    r["E1"] = {"step_ok": step_ok, "step_err": step_err, "seat_move_mm_per_world": move,
               "held_world_least_moved": held_world, "pinned_move_mm": move[PIN_WORLD],
               "others_move_mm": others, "PASS": e1_pass}

    map_ok, e1 = r["MAP"]["PASS"], r["E1"]["PASS"]
    if not step_ok:
        disp = f"INCONCLUSIVE: physics step failed ({step_err})"
    elif map_ok and e1:
        disp = "PASS: newton-API pin holds the CORRECT world's body (map->w2 + w2 held/others fell) -> (c) UNBLOCKED"
    elif map_ok and not e1:
        disp = (f"REVIEW: mjw maps to world 2 but physics did not show a clean hold (held_world={held_world}, "
                f"move={move}) -> gripper-release contrast weak; body-index likely OK via MAP")
    else:
        disp = f"BODY-INDEX BUG: flat_eq for world 2 maps to {map_world}/held {held_world} != world 2 -> fix before (c)"
    r["VERDICT"] = {"MAP": map_ok, "E1": e1, "disposition": disp}
    OUT.write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
    print(f"\n[E-1] flat_eq={flat_eq} MAP->world {map_world} (PASS={map_ok}) | seat_move={move} "
          f"held_world={held_world} E1_PASS={e1}")
    print(f"[E-1] VERDICT: {disp}  -> {OUT}")
    return 0 if (map_ok and e1) else 2


if __name__ == "__main__":
    sys.exit(main())
