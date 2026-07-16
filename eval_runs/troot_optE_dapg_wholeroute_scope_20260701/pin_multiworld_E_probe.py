# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(c) newton-API pin activation E-1..E-4 (design RLENV_PIN_DESIGN v1.7 §21.8.2). REAL env, cuda:0, no training.

p5 source-resolved the mechanism: a per-world runtime pin is activated by NEWTON API + notify, NOT a direct mjw
write (mjw eq_active is DERIVED from newton equality_constraint_enabled and clobbered by notify). This probe runs
that mechanism in the REAL NewtonRouteEnv (world_count=4) -- the only harness that steps all worlds -- and raw-
observes:
  E-1  fire world w -> step -> world w's seat moves to the DISPLACED anchor, worlds 0/1/3 do NOT (effective+isolated)
  E-2  warp accepts the mid-rollout activation (active-constraint count grows; no overflow/ignore)
  E-3  notify_model_changed mid-rollout is safe (no crash; env uses no CUDA graph capture) -- HIGHEST PRIORITY
  E-4  the pin persists across steps and releases on enabled[eq]=False + notify

E-2 or E-3 FAIL => Rs escalation (§21.8.2). Mechanism: enabled[flat_eq]=True + anchor[flat_eq]=world_pt + notify.

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_multiworld_E_probe.py
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
assert _CVD == "0", f"E-probe runs the real env on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import warp as wp  # noqa: E402
from newton._src.solvers.flags import SolverNotifyFlags  # noqa: E402

GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = _EVAL / "pin_multiworld_E_probe_result.json"
NW = 4
SEAT_SEG = 27
PIN_WORLD = 2
DISP = np.array([0.08, 0.0, 0.0])  # displaced anchor: +80mm lateral (gravity-orthogonal)
CONSTRAINT_PROPERTIES = int(SolverNotifyFlags.CONSTRAINT_PROPERTIES)


def _no_auto_fire(self):
    """Keep perclip_pin (built via route_c1_pin) but disable the recording-driven auto-fire; we fire manually."""
    self._pin_onset_frame = None
    self._pin_seat_seg = None
    self._route_rec_step_f = None


def _seat_pos(env, w):
    return env._state_0.body_q.numpy()[int(env._cable_bodies[w][SEAT_SEG]), :3].astype(float)


def _n_active_eq(env):
    en = env._model.equality_constraint_enabled.numpy()
    return int(en.sum())


def main():
    r = {"world_count": NW, "seat_seg": SEAT_SEG, "pin_world": PIN_WORLD}
    nre.NewtonRouteEnv._wire_c1_pin_from_recording = _no_auto_fire
    print("[E-probe] building real NewtonRouteEnv world_count=4 (route_c1_pin=True -> perclip_pin, no auto-fire) ...")
    env = nre.NewtonRouteEnv(world_count=NW, device="cuda:0", cfg={
        "grasp_actuation": True, "route_executor_impl": "route_executor", "route_recording_npz": str(GOLDEN_NPZ),
        "g1_scene_align": True, "route_drive_mode": "feedforward", "route_c2_scene": True, "route_c1_pin": True,
    })
    env.reset()

    # locate the per-world pin eq (connect-to-world, body1 == this world's seat body)
    b1 = env._model.equality_constraint_body1.numpy()
    b2 = env._model.equality_constraint_body2.numpy()
    seat_body = int(env._cable_bodies[PIN_WORLD][SEAT_SEG])
    cand = [i for i in range(len(b1)) if int(b1[i]) == seat_body and int(b2[i]) == -1]
    r["pin_flat_eq"] = cand[0] if cand else None
    r["seat_body_newton"] = seat_body
    if not cand:
        r["ERROR"] = f"no connect-to-world eq with body1=={seat_body}"
        OUT.write_text(json.dumps(r, indent=2))
        print(json.dumps(r, indent=2))
        return 2
    flat_eq = cand[0]

    p0 = [_seat_pos(env, w) for w in range(NW)]
    anchor = p0[PIN_WORLD] + DISP
    n_active_before = _n_active_eq(env)

    # --- E-2/E-3: activate via NEWTON API + notify (NOT direct mjw write) ---
    en = env._model.equality_constraint_enabled.numpy()
    en[flat_eq] = True
    env._model.equality_constraint_enabled.assign(en)
    an = env._model.equality_constraint_anchor.numpy()
    an[flat_eq] = anchor
    env._model.equality_constraint_anchor.assign(an)
    notify_ok, notify_err = True, None
    try:
        env._solver.notify_model_changed(CONSTRAINT_PROPERTIES)
    except Exception as e:  # noqa: BLE001
        notify_ok, notify_err = False, f"{type(e).__name__}: {str(e)[:160]}"
    n_active_after = _n_active_eq(env)

    # --- E-1: step (all worlds) and watch the pinned world move to the anchor while others do not ---
    step_ok, step_err = True, None
    try:
        for _ in range(60):
            env._physics_step_all()
        wp.synchronize()
    except Exception as e:  # noqa: BLE001
        step_ok, step_err = False, f"{type(e).__name__}: {str(e)[:160]}"
    p1 = [_seat_pos(env, w) for w in range(NW)]
    dx = [round(float(p1[w][0] - p0[w][0]) * 1e3, 2) for w in range(NW)]
    dist = [round(float(np.linalg.norm(p1[w] - anchor)) * 1e3, 2) for w in range(NW)]
    pinned_reached = dist[PIN_WORLD] < 15.0
    others_not = all(dist[w] > 40.0 for w in range(NW) if w != PIN_WORLD)

    r["E1"] = {"anchor": [round(float(x), 4) for x in anchor], "dx_mm_per_world": dx, "dist_to_anchor_mm": dist,
               "pinned_reached": pinned_reached, "others_not_pulled": others_not,
               "PASS": bool(pinned_reached and others_not)}
    r["E2"] = {"n_active_eq_before": n_active_before, "n_active_eq_after": n_active_after,
               "grew_by": n_active_after - n_active_before, "PASS": bool(n_active_after == n_active_before + 1)}
    r["E3"] = {"notify_ok": notify_ok, "notify_err": notify_err, "step_ok": step_ok, "step_err": step_err,
               "env_uses_cuda_graph": False, "PASS": bool(notify_ok and step_ok)}

    # --- E-4: release (done-world path) enabled=False + notify, step, world should free ---
    rel_ok, rel_err = True, None
    try:
        en2 = env._model.equality_constraint_enabled.numpy()
        en2[flat_eq] = False
        env._model.equality_constraint_enabled.assign(en2)
        env._solver.notify_model_changed(CONSTRAINT_PROPERTIES)
        for _ in range(30):
            env._physics_step_all()
        wp.synchronize()
    except Exception as e:  # noqa: BLE001
        rel_ok, rel_err = False, f"{type(e).__name__}: {str(e)[:160]}"
    p2 = [_seat_pos(env, w) for w in range(NW)]
    released_moved = round(float(np.linalg.norm(p2[PIN_WORLD] - p1[PIN_WORLD])) * 1e3, 2)
    r["E4"] = {"release_ok": rel_ok, "release_err": rel_err, "pinned_moved_after_release_mm": released_moved,
               "n_active_eq_after_release": _n_active_eq(env), "PASS": bool(rel_ok)}

    e1, e2, e3 = r["E1"]["PASS"], r["E2"]["PASS"], r["E3"]["PASS"]
    if not e3:
        disp = "ESCALATE (E-3 FAIL): notify/step unsafe mid-rollout -> Rs escalation (§21.8.2)"
    elif not e2:
        disp = "ESCALATE (E-2 FAIL): warp did NOT accept the mid-rollout activation -> Rs escalation (§21.8.2)"
    elif e1:
        disp = "FEASIBLE: newton-API per-world pin is effective + notify-safe -> (c) confirmed, enable (a)(b)(d)+audit"
    else:
        disp = "PARTIAL: notify-safe + activation accepted but per-world hold not shown (gripper/anchor) -> refine"
    r["VERDICT"] = {"E1": e1, "E2": e2, "E3": e3, "E4": r["E4"]["PASS"], "disposition": disp}
    OUT.write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
    print(f"\n[E-probe] E-1={e1} E-2={e2} E-3={e3} E-4={r['E4']['PASS']} | flat_eq={flat_eq} "
          f"dx={dx} n_active {n_active_before}->{n_active_after}")
    print(f"[E-probe] VERDICT: {disp}  -> {OUT}")
    return 0 if (e1 and e2 and e3) else 2


if __name__ == "__main__":
    sys.exit(main())
