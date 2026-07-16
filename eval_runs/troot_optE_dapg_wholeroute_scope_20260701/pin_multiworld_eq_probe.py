# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""(c) multi-world pin-eq feasibility probe P-1..P-4 (design RLENV_PIN_DESIGN v1.6 §21.2). cuda:0, no training.

Gate for the permanent-wiring scaffold: the pin currently writes the CPU single-world template
(``mjd.eq_active[best]``); at world_count>1 the WARP State is what gets stepped (not CPU mj_data), so a CPU-only
eq write may be GPU-inert -- a silent, RAISE-proof failure (§21.1). This probe determines whether the per-world
mjw eq path is real AND effective, BEFORE any implementation.

  P-1  mjw_data.eq_active per-world?      shape (world_count, neq) => per-world PASS / (neq,) shared => BLOCK
  P-2  pin eq index layout                pin eqs = cable-seg ordinal; mjw replicates per world
  P-3  per-world write effectiveness      DISPLACED anchor (+80mm lateral) on world 2 only: a working per-world
                                          pin PULLS world-2's seat body to the anchor while worlds 0/1/3 do not
                                          (anchor=current-pos cannot discriminate -- a held cable looks pinned).
                                          grasp_actuation=False isolates the pin (no gripper confound).
  P-4  eq_data batching (anchor)          mjw_model.eq_data (world_count, neq, k) per-world / (neq, k) shared

P-1 or P-3 FAIL => multi-world independent pin infeasible on this substrate => Rs escalation (§21.2).

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_multiworld_eq_probe.py
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

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "0", "probe runs the warp substrate on cuda:0 ONLY"
# fork-B R5-3 opt-out (RECORDED USE, D1 sec 4): this probe INTENTIONALLY builds world_count=4 on the
# CPU path to exercise multi-world structure; the make_solver tripwire would otherwise refuse it.
os.environ.setdefault("THREAD_ALLOW_CPU_MULTIWORLD", "1")


import mujoco  # noqa: E402
import newton_route_env  # noqa: E402, F401  (side-effect: SOLVER_BACKEND="mujoco")
import numpy as np  # noqa: E402
import route_env_config as rc  # noqa: E402
from newton_skill_env_base import SIM_DT, build_fk_and_init, build_multiworld_scene  # noqa: E402
from task_config import FINGER_OPEN_POS  # noqa: E402

OUT = _EVAL / "pin_multiworld_eq_probe_result.json"
NW = 4
SEAT_SEG = 27  # C1 seat cable-seg ordinal (g6_live: eq_id 27 / body 56); pin eq index == seg ordinal (P-2)
PIN_WORLD = 2  # the single world we fire, to prove per-world isolation
DISP = np.array([0.08, 0.0, 0.0])  # displaced anchor: +80mm lateral (gravity-orthogonal) so the pull is unambiguous


def main():
    fkm, fks, _ = build_fk_and_init(left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cuda:0")
    scene = build_multiworld_scene(
        fkm,
        fks,
        NW,
        "cuda:0",
        add_support_clips=False,
        add_target_clip=True,
        target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z,
        add_c2_clip=True,
        c2_xy=rc.ROUTE_C2_XY,
        grasp_actuation=False,  # ISOLATE the pin: no gripper servo holding the cable (else "held" masks "pinned")
        perclip_pin=True,
    )
    solver, model = scene["solver"], scene["model"]
    st0, st1, control, contacts = scene["state_0"], scene["state_1"], scene["control"], scene["contacts"]
    mjm, mjwd, mjwm = solver.mj_model, solver.mjw_data, solver.mjw_model
    cable_bodies = scene["cable_bodies"]
    r = {"world_count": NW, "seat_seg": SEAT_SEG, "pin_world": PIN_WORLD, "grasp_actuation": False}

    # --- P-1: mjw_data.eq_active per-world? ---
    ea = mjwd.eq_active.numpy()
    r["P1"] = {
        "mjw_data.eq_active_shape": list(ea.shape),
        "cpu_mj_data.eq_active_shape": list(mjm.eq_data.shape[:1]),
        "PASS": bool(ea.ndim == 2 and ea.shape[0] == NW),
    }

    # --- P-2: pin eq index layout (CPU template) ---
    CONNECT = int(mujoco.mjtEq.mjEQ_CONNECT)
    pin_eqs = [
        (i, int(mjm.eq_obj1id[i]))
        for i in range(int(mjm.neq))
        if int(mjm.eq_type[i]) == CONNECT and int(mjm.eq_obj2id[i]) == 0 and int(mjm.eq_active0[i]) == 0
    ]
    eqid = pin_eqs[SEAT_SEG][0] if len(pin_eqs) > SEAT_SEG else None
    r["P2"] = {
        "n_pin_eq": len(pin_eqs),
        "seat_seg_eqid": eqid,
        "eqids_are_seg_ordinal": [e[0] for e in pin_eqs] == list(range(len(pin_eqs))),
        "PASS": eqid is not None,
    }

    # --- P-4: eq_data batching ---
    ed = mjwm.eq_data.numpy()
    r["P4"] = {"mjw_model.eq_data_shape": list(ed.shape), "per_world": bool(ed.ndim == 3 and ed.shape[0] == NW)}

    # --- P-3: per-world write effectiveness (DISPLACED anchor round-trip) ---
    if r["P1"]["PASS"] and eqid is not None:
        seat_ids = [int(cable_bodies[w][SEAT_SEG]) for w in range(NW)]
        p0 = [st0.body_q.numpy()[seat_ids[w], :3].astype(float).copy() for w in range(NW)]
        anchor = p0[PIN_WORLD] + DISP  # pull world-2's seat body 80mm laterally to HERE
        ed_w = mjwm.eq_data.numpy()
        ed_w[PIN_WORLD, eqid, 0:3] = [0.0, 0.0, 0.0]
        ed_w[PIN_WORLD, eqid, 3:6] = anchor
        mjwm.eq_data.assign(ed_w)
        ea_w = mjwd.eq_active.numpy()
        ea_w[PIN_WORLD, eqid] = True
        mjwd.eq_active.assign(ea_w)
        # readback: the write took to the warp array AND is isolated to PIN_WORLD
        ea_rb = mjwd.eq_active.numpy()
        rb_ok = bool(ea_rb[PIN_WORLD, eqid]) and not any(bool(ea_rb[w, eqid]) for w in range(NW) if w != PIN_WORLD)
        s0, s1 = st0, st1
        for _ in range(300):
            s0.clear_forces()
            model.collide(s0, contacts)
            solver.step(s0, s1, control, contacts, SIM_DT)
            s0, s1 = s1, s0
        p1 = [s0.body_q.numpy()[seat_ids[w], :3].astype(float) for w in range(NW)]
        dx = [round(float(p1[w][0] - p0[w][0]) * 1e3, 2) for w in range(NW)]  # lateral move (mm) toward the anchor
        dz = [round(float(p1[w][2] - p0[w][2]) * 1e3, 2) for w in range(NW)]  # z move (mm); free cables should fall
        dist = [round(float(np.linalg.norm(p1[w] - anchor)) * 1e3, 2) for w in range(NW)]  # to the displaced anchor
        # HARNESS VALIDITY: world 0 is the CPU-template mirror and ALWAYS moves; the mjw-only worlds (1..N-1) are
        # what a per-world pin must reach. If NO unpinned NON-world-0 world shows motion (free cable falls), this
        # minimal build+step harness does NOT step the mjw multi-world physics -> P-3 is untestable HERE (verified
        # by the no-pin baseline: only world 0 falls). This is NOT a pin verdict.
        harness_stepped = any(abs(dx[w]) > 1.0 or abs(dz[w]) > 1.0 for w in range(NW) if w not in (0, PIN_WORLD))
        pinned_reached = dist[PIN_WORLD] < 15.0
        others_not = all(dist[w] > 40.0 for w in range(NW) if w != PIN_WORLD)
        r["P3"] = {
            "anchor": [round(float(x), 4) for x in anchor],
            "readback_took_and_isolated": rb_ok,
            "dx_mm_per_world": dx,
            "dz_mm_per_world": dz,
            "dist_to_anchor_mm": dist,
            "harness_steps_nonzero_worlds": harness_stepped,
            "pinned_reached": pinned_reached,
            "others_not_pulled": others_not,
            "PASS": bool(rb_ok and harness_stepped and pinned_reached and others_not),
        }
    else:
        r["P3"] = {"PASS": False, "harness_steps_nonzero_worlds": None, "skipped": "P-1 failed or eqid absent"}

    p1p = r["P1"]["PASS"]
    harness_ok = r["P3"].get("harness_steps_nonzero_worlds")
    p3p = r["P3"].get("PASS", False)
    if not p1p:
        _disp = "INFEASIBLE: mjw eq_active is SHARED (not per-world) -> Rs escalation (§21.2)"
    elif harness_ok is False:
        _disp = (
            "INCONCLUSIVE-HARNESS: per-world eq STRUCTURE exists (P-1/P-4 PASS) but this minimal "
            "build+step harness steps only world 0 -> per-world EFFECTIVENESS untestable here. NOT a "
            "GPU-inert verdict. Needs a validated multi-world stepping harness (real NewtonRouteEnv "
            "world_count>1) and/or p5's mjw eq re-poke mechanism (§21.1 DEFERRED)."
        )
    elif p3p:
        _disp = "FEASIBLE: per-world mjw eq write propagates -> proceed to (c) design (groove-anchor/eqid/batching)"
    else:
        _disp = "INFEASIBLE: per-world eq write reads back but does NOT constrain -> Rs escalation (§21.2)"
    r["VERDICT"] = {
        "P1_pass": bool(p1p),
        "harness_valid": harness_ok,
        "P3_effectiveness_pass": bool(p3p),
        "disposition": _disp,
    }
    OUT.write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
    print(
        f"\n[probe] P-1={p1p} P-2 eqid={eqid} P-4 per-world={r['P4']['per_world']} | "
        f"P-3 readback={r['P3'].get('readback_took_and_isolated')} harness_valid={harness_ok} "
        f"pinned_reached={r['P3'].get('pinned_reached')} PASS={p3p}"
    )
    print(f"[probe] VERDICT: {r['VERDICT']['disposition']}  -> {OUT}")
    return 0 if (p1p and p3p) else (3 if harness_ok is False else 2)


if __name__ == "__main__":
    sys.exit(main())
