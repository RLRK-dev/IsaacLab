# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""authorize_clip_pin positive/negative controls (P1/P2 + N1-N7) -- design §15.5. No-GPU (CPU scene).

A guard that never fires cannot be told from one that CANNOT fire (design §12): so every leg below asserts a
DIFFERENT outcome, the reject legs must actually reject, and each control names the hole it catches.

  pure clip_capture_predicate (boundary legs):  P1/P2 ACCEPT  |  N1(aerial) N2(under) N3(lateral) N4(domain) REJECT
  mechanism (set + selector, the identity legs): N5 support-clip seat -> NotInAnyRouteClip
                                                 N6 built C2 seat     -> captured (authorized set content)
                                                 N7 task_config C2 in set -> BrokenSelector (scene<->task drift)
  episode-end audit_pin_anchors:                 A(no pin) pass | B(off-clip weld) RAISE | C(legit C1 weld) pass

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/authorize_clip_pin_controls.py
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

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "no-GPU control: run with CUDA_VISIBLE_DEVICES=''"

import newton_route_env  # noqa: E402, F401  (side-effect: forces SOLVER_BACKEND="mujoco" like the route env)
import route_env_config as rc  # noqa: E402
import route_executor as rex  # noqa: E402
from newton_skill_env_base import build_fk_and_init, build_multiworld_scene  # noqa: E402
from task_config import FINGER_OPEN_POS  # noqa: E402

OUT = _EVAL / "authorize_clip_pin_controls_result.json"


class _Shim:
    """Minimal stand-in for the env's SolverMuJoCo -- authorize_clip_pin only reads mj_model / mj_data."""

    def __init__(self, mjm, mjd):
        self.mj_model = mjm
        self.mj_data = mjd


def _build():
    import mujoco

    fkm, fks, _ = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu"
    )
    scene = build_multiworld_scene(
        fkm,
        fks,
        1,
        "cpu",
        add_support_clips=True,  # jigs at x=0.30 -> the selector at x=0.35 must exclude them (N5 depth)
        add_target_clip=True,
        target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z,
        add_c2_clip=True,
        c2_xy=rc.ROUTE_C2_XY,
        grasp_actuation=True,
        perclip_pin=True,  # pre-allocate the DISABLED connect-to-world eqs (audit tests need candidates)
    )
    mjm = scene["solver"].mj_model
    mjd = mujoco.MjData(mjm)
    mujoco.mj_forward(mjm, mjd)
    return mjm, mjd


def main():
    c1x, c1y = rc.ROUTE_C1_XY
    c2x, c2y = rc.ROUTE_C2_XY
    mjm, mjd = _build()
    results = {}

    # --- built-model bar witnesses (what the authorizer actually uses) ---
    g_c1 = rex.clip_geoms_at(mjm, mjd, c1x, c1y)
    g_c2 = rex.clip_geoms_at(mjm, mjd, c2x, c2y)
    y_win_c1 = max((float(mjm.geom_size[gi][1]) for gi in g_c1), default=0.0)
    results["bars"] = {
        "SEAT_LAT_BAR_M": rc.SEAT_LAT_BAR_M,
        "SEAT_Z_LO_M": rc.SEAT_Z_LO_M,
        "SEAT_Z_HI_M": rc.SEAT_Z_HI_M,
        "y_win_c1_m_from_model": round(y_win_c1, 5),
        "n_geoms_c1": len(g_c1),
        "n_geoms_c2": len(g_c2),
    }

    def _pred(seat):
        return rex.clip_capture_predicate(seat, c1x, c1y, rc.SEAT_LAT_BAR_M, y_win_c1, rc.SEAT_Z_LO_M, rc.SEAT_Z_HI_M)

    # --- pure clip_capture_predicate: P1/P2 ACCEPT, N1-N4 REJECT (design §15.5) ---
    pure = [
        ("P1_golden", (c1x, c1y, 0.82968), True, "golden seat (pB k28)"),
        ("P2_arch", (c1x, c1y, 0.830), True, "arch float, old contact-leg trap"),
        ("N1_aerial", (c1x, c1y, 0.8809), False, "880.9mm aerial weld (historic max)"),
        ("N2_under", (c1x, c1y, 0.816), False, "under the clip (support-band top)"),
        ("N3_lateral", (c1x + 0.004, c1y, 0.829), False, "4.0mm off-axis > 3.5mm wall"),
        ("N4_domain", (c1x, c1y + 0.020, 0.829), False, "20mm off in Y > 15mm window"),
    ]
    pure_out = []
    for name, seat, expect_accept, catches in pure:
        ok, why = _pred(seat)
        passed = ok == expect_accept
        pure_out.append(
            {"leg": name, "seat": [round(v, 5) for v in seat], "expect_accept": expect_accept,
             "got_accept": ok, "reason": why, "PASS": passed, "catches": catches}
        )
    results["pure_predicate"] = pure_out

    # --- mechanism: N5 (support seat -> NotInAnyRouteClip), N7 (task_config C2 in set -> BrokenSelector) ---
    mech_out = []

    # N5: a seat inside a SUPPORT clip (x=0.30) -- authorized set is (C1, C2), so it must be REFUSED (§14.1/§15.5).
    n5_seat = (0.300, 0.050, 0.810)
    try:
        rex.authorize_clip_pin(_Shim(mjm, mjd), 1, n5_seat)
        mech_out.append({"leg": "N5_support_seat", "expect": "NotInAnyRouteClip", "got": "NO RAISE", "PASS": False})
    except rex.NotInAnyRouteClip as e:
        mech_out.append({"leg": "N5_support_seat", "expect": "NotInAnyRouteClip", "got": str(e)[:90], "PASS": True,
                         "catches": "support-clip trap (z-only controls are blind to it)"})
    except Exception as e:  # noqa: BLE001
        mech_out.append({"leg": "N5_support_seat", "expect": "NotInAnyRouteClip",
                         "got": f"WRONG EXC {type(e).__name__}: {str(e)[:70]}", "PASS": False})

    # N5-depth: the selector at C1 (x=0.35) must EXCLUDE the support clip geoms (x=0.30, 50mm > 30mm gate).
    support_in_c1 = any(abs(float(mjd.geom_xpos[gi][0]) - 0.30) < 1e-4 for gi in g_c1)
    mech_out.append({"leg": "N5_selector_excludes_support", "expect": "no x=0.30 geom in C1 selector",
                     "got": f"support_geom_in_c1={support_in_c1}", "PASS": not support_in_c1})

    # N6: the built C2 seat IS captured (authorized set content) -- selector finds it AND the predicate accepts.
    n6_ok, n6_why = rex.clip_capture_predicate(
        (c2x, c2y, 0.829), c2x, c2y, rc.SEAT_LAT_BAR_M,
        max((float(mjm.geom_size[gi][1]) for gi in g_c2), default=0.0), rc.SEAT_Z_LO_M, rc.SEAT_Z_HI_M,
    )
    mech_out.append({"leg": "N6_built_c2_captured", "expect": "captured & 5-6 geoms",
                     "got": f"captured={n6_ok} ({n6_why}) n_geoms={len(g_c2)}",
                     "PASS": bool(n6_ok and len(g_c2) in (5, 6)), "catches": "authorized-set content witness"})

    # N7: task_config C2 (0.40, 0.075) -- built C2 is at y=0.000, so the selector there finds NO clip -> the count
    #     assert (5,6) fails -> BrokenSelector. A scene<->task drift must NOT be printed as "cable not seated".
    g_taskcfg_c2 = rex.clip_geoms_at(mjm, mjd, 0.40, 0.075)
    n7_pass = len(g_taskcfg_c2) not in (5, 6)  # authorize_clip_pin would RAISE BrokenSelector on this count
    mech_out.append({"leg": "N7_taskcfg_c2_broken_selector", "expect": "count not in {5,6} -> BrokenSelector",
                     "got": f"n_geoms_at_(0.40,0.075)={len(g_taskcfg_c2)}", "PASS": n7_pass,
                     "catches": "scene<->task drift (built C2 y=0.000 != task_config y=0.075)"})
    results["mechanism"] = mech_out

    # --- episode-end audit_pin_anchors: A(no pin) pass, B(off-clip weld) RAISE, C(legit weld) pass (§15.4) ---
    import mujoco

    audit_out = []

    # A: no pin fired -> audit is a no-op.
    try:
        rex.audit_pin_anchors(mjm, mjd)
        audit_out.append({"leg": "A_no_pin", "expect": "pass (no-op)", "got": "pass", "PASS": True})
    except Exception as e:  # noqa: BLE001
        audit_out.append({"leg": "A_no_pin", "expect": "pass (no-op)", "got": f"RAISE {str(e)[:70]}", "PASS": False})

    # find a pre-allocated pin candidate (connect-to-world, initially disabled) to drive the audit.
    cand = [
        i for i in range(int(mjm.neq))
        if int(mjm.eq_type[i]) == int(mujoco.mjtEq.mjEQ_CONNECT)
        and int(mjm.eq_obj2id[i]) == 0
        and int(mjm.eq_active0[i]) == 0
    ]
    audit_out.append({"leg": "pin_candidates_present", "expect": ">0", "got": len(cand), "PASS": len(cand) > 0})

    if cand:
        i = cand[0]
        # B: bypass-weld an off-clip anchor (880.9mm aerial) -> audit MUST raise (who-wrote-it-agnostic, §15.4).
        mjm.eq_data[i][3:6] = [c1x, c1y, 0.8809]
        mjd.eq_active[i] = 1
        try:
            rex.audit_pin_anchors(mjm, mjd)
            audit_out.append({"leg": "B_offclip_weld", "expect": "AssertionError", "got": "NO RAISE", "PASS": False})
        except AssertionError as e:
            audit_out.append({"leg": "B_offclip_weld", "expect": "AssertionError", "got": str(e)[:90], "PASS": True})
        # C: move the SAME eq's anchor to a legit C1 seat -> audit passes.
        mjm.eq_data[i][3:6] = [c1x, c1y, 0.829]
        try:
            rex.audit_pin_anchors(mjm, mjd)
            audit_out.append({"leg": "C_legit_weld", "expect": "pass", "got": "pass", "PASS": True})
        except Exception as e:  # noqa: BLE001
            audit_out.append({"leg": "C_legit_weld", "expect": "pass", "got": f"RAISE {str(e)[:70]}", "PASS": False})
        mjd.eq_active[i] = 0  # leave the model as we found it
    results["audit"] = audit_out

    all_legs = pure_out + mech_out + audit_out
    n_pass = sum(1 for r in all_legs if r.get("PASS"))
    n_tot = len(all_legs)
    results["summary"] = {"passed": n_pass, "total": n_tot, "ALL_PASS": n_pass == n_tot}

    OUT.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\n[authorize_clip_pin controls] {n_pass}/{n_tot} PASS -> {'ALL PASS' if n_pass == n_tot else 'FAIL'}")
    print(f"  bars: lat={rc.SEAT_LAT_BAR_M * 1e3:.2f}mm z=({rc.SEAT_Z_LO_M * 1e3:.0f},{rc.SEAT_Z_HI_M * 1e3:.0f})mm "
          f"y_win={y_win_c1 * 1e3:.2f}mm | geoms C1={len(g_c1)} C2={len(g_c2)}")
    print(f"  result -> {OUT}")
    return 0 if n_pass == n_tot else 1


if __name__ == "__main__":
    sys.exit(main())
