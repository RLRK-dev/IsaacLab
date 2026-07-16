# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(c) E-1 v2 -- per-world hold via the REAL STEP 8-10 contrast (design v1.8 §21.9). cuda:0, no training.

E-1 v1 could not discriminate: at reset the cable RESTS ON THE TABLE (z~804, grippers empty at the P0 lift-point),
so "release the gripper -> free-fall" never had a held cable to release. v2 uses the production contrast instead:

  1. FF-drive the recorded route on ALL 4 worlds to the pin ONSET (RL step onset_frame//10; seat in the C1
     groove, z~828.7). This doubles as the HARNESS-VALIDITY gate: if worlds 1-3 never lift/seat (their physics or
     drive not stepping), that is its own critical finding -- surfaced, not blamed on the pin.
  2. Fire the pin on WORLD 2 ONLY via the (c) newton-API mechanism (equality_constraint_enabled[flat_eq]=True +
     notify(CONSTRAINT_PROPERTIES); anchor left as built). Verify inline that the mjw flip is exactly (2, eq).
  3. CONTINUE the recorded route (the recording itself performs STEP 8-10: R unclamps, then the route drags on
     toward C2). Banked behaviour without a pin = C1 is NOT retained (~52.87mm escape); with the pin the seat
     stays in the groove. So: world-2 seat HELD at the groove vs worlds 0/1/3 seats pulled out = the physical
     body-index proof p5 requires (E-2's count cannot see a mismap).

Outcomes it discriminates: PASS (w2 held, others escape) / BODY-INDEX BUG (a different world held) /
ANCHOR-SEMANTICS finding (w2 yanked to its build pose at fire) / ENV-MULTIWORLD finding (worlds 1-3 never drove)
/ REVIEW (weak contrast). Raw numbers are reported regardless.

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_multiworld_E1v2_release_contrast.py
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
# fork-B R5-3 opt-out (RECORDED USE, D1 sec 4): this probe INTENTIONALLY builds world_count=4 on the
# CPU path to exercise multi-world structure; the make_solver tripwire would otherwise refuse it.
os.environ.setdefault("THREAD_ALLOW_CPU_MULTIWORLD", "1")

assert _CVD == "0", f"E-1 v2 runs the real env on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import route_env_config as rc  # noqa: E402
import torch  # noqa: E402
import warp as wp  # noqa: E402
from newton._src.solvers.flags import SolverNotifyFlags  # noqa: E402

GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = _EVAL / "pin_multiworld_E1v2_release_contrast_result.json"
NW = 4
SEAT_SEG = 27
PIN_WORLD = 2
CP = int(SolverNotifyFlags.CONSTRAINT_PROPERTIES)
STOP_RL_STEP = 335  # stay short of the known coarse-substep drop/done (~343, g6_live) so no world resets mid-read


def _no_auto_fire(self):
    self._pin_onset_frame = None
    self._pin_seat_seg = None
    self._route_rec_step_f = None


def _seats(env):
    bq = env._state_0.body_q.numpy()
    return [bq[int(env._cable_bodies[w][SEAT_SEG]), :3].astype(float).copy() for w in range(NW)]


def main():
    raw = np.load(str(GOLDEN_NPZ), allow_pickle=True)
    pin = np.asarray(raw["pin_active"]).ravel()
    onset_frame = int(np.nonzero(pin > 0)[0][0])
    onset_rl = onset_frame // 10  # recorder cadence 10 (g6_live: fired_at_frame 2544 -> RL step 254)
    r = {
        "world_count": NW,
        "seat_seg": SEAT_SEG,
        "pin_world": PIN_WORLD,
        "onset_frame": onset_frame,
        "onset_rl_step": onset_rl,
    }

    nre.NewtonRouteEnv._wire_c1_pin_from_recording = _no_auto_fire
    print(f"[E-1v2] building real NewtonRouteEnv world_count={NW}; drive to onset RL step {onset_rl} ...")
    env = nre.NewtonRouteEnv(
        world_count=NW,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
            "route_c1_pin": True,
        },
    )
    env.reset()
    zero = torch.zeros((NW, 6), dtype=torch.float32)

    # locate world-2's pin eq in the newton model (connect-to-world on its seat body)
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

    trace = {"t": [], "seat_z_mm": []}  # per-world seat z at checkpoints (lift/transport evidence per world)

    def _snap(t):
        wp.synchronize()
        s = _seats(env)
        trace["t"].append(int(t))
        trace["seat_z_mm"].append([round(float(p[2]) * 1e3, 1) for p in s])
        return s

    _snap(0)  # rest pose (all worlds on the table ~804) -- the lift/transport contrast baseline in the trace

    # --- phase 1: FF-drive ALL worlds to the onset (also the harness-validity evidence) ---
    early = None
    for t in range(onset_rl + 1):
        _, _, dones, _ = env.step(zero)
        if bool(dones.any()):
            early = t
            break
        if t % 60 == 0:
            _snap(t)
    seats_onset = _snap(early if early is not None else onset_rl)
    r["early_done_during_drive"] = early
    z_onset = [round(float(p[2]) * 1e3, 1) for p in seats_onset]
    # HV: a driven+grasped world lifts its seat to the groove band (~828.7); an undriven world stays at rest (~804)
    hv_per_world = [bool(z > 815.0) for z in z_onset]
    hv_all = all(hv_per_world)
    r["HV"] = {"seat_z_at_onset_mm": z_onset, "per_world_driven": hv_per_world, "PASS": bool(hv_all and early is None)}
    if not r["HV"]["PASS"]:
        r["VERDICT"] = {
            "disposition": (
                f"ENV-MULTIWORLD finding: worlds {[w for w, ok in enumerate(hv_per_world) if not ok]} never "
                f"lifted/seated under the FF drive (early_done={early}) -> the multi-world drive/physics itself is "
                "the blocker (broader than the pin; surfaced to p5/Rs). Pin untested."
            ),
            "HV": False,
        }
        OUT.write_text(json.dumps({**r, "trace": trace}, indent=2))
        print(json.dumps(r, indent=2))
        return 3

    # --- phase 2: fire world 2 ONLY via the (c) newton-API mechanism; verify the mjw flip inline ---
    p0 = seats_onset
    ea_before = env._solver.mjw_data.eq_active.numpy().copy()
    en = env._model.equality_constraint_enabled.numpy()
    en[flat_eq] = True
    env._model.equality_constraint_enabled.assign(en)
    env._solver.notify_model_changed(CP)
    ea_after = env._solver.mjw_data.eq_active.numpy()
    flipped = [[int(w), int(e)] for w, e in np.argwhere((~ea_before) & ea_after)]
    map_ok = bool(len(flipped) == 1 and flipped[0][0] == PIN_WORLD)
    r["MAP"] = {"flipped_world_eq": flipped, "PASS": map_ok}
    print(f"[E-1v2] fired flat_eq {flat_eq} at onset; mjw flip={flipped} (expect [[{PIN_WORLD}, ...]])")

    # --- phase 3: CONTINUE the recording (STEP 8-10: R unclamp -> drag to C2). pre-step snapshots guard done. ---
    last = p0
    for t in range(onset_rl + 1, STOP_RL_STEP):
        wp.synchronize()
        last = _seats(env)  # state ENTERING step t (a done-reset never masks the terminal value)
        _, _, dones, _ = env.step(zero)
        if bool(dones.any()):
            r["early_done_after_fire"] = t
            break
        if t % 20 == 0:
            _snap(t)
    else:
        wp.synchronize()
        last = _seats(env)
    _snap(STOP_RL_STEP)

    move = [round(float(np.linalg.norm(last[w] - p0[w])) * 1e3, 2) for w in range(NW)]
    z_end = [round(float(last[w][2]) * 1e3, 1) for w in range(NW)]
    dx_groove = [round(abs(float(last[w][0]) - rc.ROUTE_C1_XY[0]) * 1e3, 2) for w in range(NW)]
    held_world = int(np.argmin(move))
    others = [move[w] for w in range(NW) if w != PIN_WORLD]
    in_groove_w2 = bool(dx_groove[PIN_WORLD] <= rc.SEAT_LAT_BAR_M * 1e3 and 821.0 < z_end[PIN_WORLD] < 836.0)
    e1_pass = bool(held_world == PIN_WORLD and move[PIN_WORLD] < 8.0 and min(others) > 15.0 and in_groove_w2)

    r["E1"] = {
        "seat_move_after_fire_mm": move,
        "seat_z_end_mm": z_end,
        "seat_dx_to_c1_axis_mm": dx_groove,
        "held_world_least_moved": held_world,
        "w2_still_in_groove": in_groove_w2,
        "others_move_mm": others,
        "PASS": e1_pass,
    }

    if map_ok and e1_pass:
        disp = "PASS: w2 held IN GROOVE, unpinned worlds escaped -> body-index + hold semantics proven -> (c) UNBLOCKED"
    elif map_ok and move[PIN_WORLD] > 15.0 and not in_groove_w2:
        disp = (
            f"ANCHOR-SEMANTICS finding: w2 moved {move[PIN_WORLD]}mm off the groove after fire "
            f"(z_end={z_end[PIN_WORLD]}) -> ref-pose anchor did not hold at fire pose; p5 redesigns the anchor"
        )
    elif map_ok and min(others) <= 15.0:
        disp = (
            f"REVIEW: weak contrast -- unpinned seats moved only {others}mm (banked no-pin escape expected "
            ">15mm); raw trace attached; verdict deferred to p5"
        )
    elif not map_ok:
        disp = f"BODY-INDEX BUG: mjw flip {flipped} != world {PIN_WORLD} -> fix replicate/index mapping before (c)"
    else:
        disp = f"REVIEW: held_world={held_world} move={move} -> mixed outcome; raw trace attached; p5 to rule"
    r["VERDICT"] = {"MAP": map_ok, "E1": e1_pass, "HV": True, "disposition": disp}

    OUT.write_text(json.dumps({**r, "trace": trace}, indent=2))
    print(json.dumps(r, indent=2))
    print(
        f"\n[E-1v2] HV z_onset={z_onset} | MAP flip={flipped} | move={move} z_end={z_end} dx_c1={dx_groove} "
        f"held={held_world} in_groove_w2={in_groove_w2}"
    )
    print(f"[E-1v2] VERDICT: {disp}  -> {OUT}")
    return 0 if (map_ok and e1_pass) else 2


if __name__ == "__main__":
    sys.exit(main())
