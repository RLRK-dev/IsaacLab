# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""SRG probe (Stage-B, node T-ROOT-optE-route-dapg-C1C2-P2-routeexec) — the grip-efficacy
go/no-go that resolves the 4-substep grip UNKNOWN BEFORE committing comp3/4/5 (CC6 "build on sand").

DESIGN = SRG_PROBE_DESIGN_DRAFT_COORD_20260707.md (%12 [VERIFY] PASS 19:06). Staged, early-exit,
cheapest-first; NOT "no-slip" (banked-UNREACHABLE, LL-G3-Vacuity) — creep-BUDGETED, PER-AXIS.

  S0  4-substep AXIAL creep-floor re-measure (isolated pinch, R6 production solref) + K regime-screen.
      Reuses the PROVEN s5 corrected-instrument (s5_calib_bench3r: landing_control rule-2 true-positive
      + pinch_axial_cell com_y creep + per-substep body_f readback), swapping SIM_SUBSTEPS->RL_SIM_SUBSTEPS
      AND SIM_DT->RL_SIM_DT so one physics frame stays = DT (frame-comparability, D1 caveat b).
  S1  DIRECT z/lateral cage-escape go/no-go on the REAL route grasp (creep-budgeted over W_svc).  [next chunk]
  S2  tail-cell screening (nominal + DR-corner +-16mm + known-hard; gate = worst-screened).         [next chunk]

⛔ RUN is HELD (build/GPU HOLD; %12 surfaces to Rs for first-GPU-spend auth). This file is BUILT +
ast-verified only; the measurement executes at authorized RUN. grasp_actuation=ON is a STANDALONE
temporary toggle (S1); locked file (_run_mujoco_grasp_route) and production config are NOT edited (D2).

Ground: BUILD_PLAN v0.2.2 §7 / LAYERB verdict CC3 / LL-Creep-Characterization / LL-G3-Vacuity /
route_env_config.py (retention 0.840m :105, C2 wall 0.5mm :114, horizon 900 :91).
"""

import argparse
import json
import os
import sys
import time

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
_S5_DIR = "/home/rlrk/IsaacLab/eval_runs/troot_optE_s5_grasp_0gpu_20260610"
_ENVS = "/home/rlrk/IsaacLab/thread_isaac_lab/envs"
_CONFIGS = "/home/rlrk/IsaacLab/thread_isaac_lab/configs"
for _p in (OUT_DIR, _ENVS, _CONFIGS, _S5_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# --- Banked reference (10-substep, R6, F=0) -------------------------------------------------------
# The floor the 4-substep re-measure is compared against. Source: LL-Creep-Characterization.md:11
# (R6 60.4 um/f @ F=0, 10-substep) == s5_calib_bench3r_result.json cells.R6_F00.creep_um_per_f.
BANK_10SUB_R6_UM_PER_F = 60.4
# K regime-change screen (DRAFT §13 D4): granularity-coarsening ALONE scales creep by <= the substep
# ratio SIM_SUBSTEPS/RL_SIM_SUBSTEPS = 10/4 = 2.5x; K = 2.5x + margin => 3.5x. Above K => a NEW
# mechanism appeared at 4-substep (not mere coarsening) => STOP+surface (NOT a task budget).
SUBSTEP_RATIO = 10.0 / 4.0  # 2.5
K_REGIME_SCREEN = 3.5


def _live_production_contact_ssot():
    """Live task_config production contact SSOT (the values S0's env MUST share, D1 caveat a)."""
    import task_config as C

    return {
        "pad_solref": tuple(float(v) for v in C.MUJOCO_PAD_SOLREF),  # :187 R6-bx4
        "condim": int(C.MUJOCO_CONTACT_CONDIM),                      # :176 = 6
        "impratio": float(C.MUJOCO_OPT_IMPRATIO),                    # :196 = 10.0
    }


def verify_contact_ssot_and_framecomp():
    """D1 HARD gate (fail-closed): (a) the s5 R6 cell + payload EXACT-share the live production
    contact SSOT, and (b) the 4-substep run keeps one physics frame = DT (frame-comparability).

    Runs at authorized RUN (builds a throwaway pinch env for the geom readback). Returns the readback
    dict; raises AssertionError (fail-closed) on any divergence -> the S0 floor is NOT representative.
    """
    import s5_calib_bench3r as B3
    import s5_p1_probe_rev5 as R5
    import s5_p1_probe_rev7 as R7
    from newton_skill_env_base import DT, RL_SIM_DT, RL_SIM_SUBSTEPS, SIM_DT, SIM_SUBSTEPS

    ssot = _live_production_contact_ssot()

    # (b) frame-comparability: N * substep_dt = DT in BOTH regimes (else um/f is not comparable).
    frame_10 = SIM_SUBSTEPS * SIM_DT
    frame_4 = RL_SIM_SUBSTEPS * RL_SIM_DT
    assert abs(frame_10 - DT) < 1e-12, f"10-substep frame {frame_10} != DT {DT}"
    assert abs(frame_4 - DT) < 1e-12, f"4-substep frame {frame_4} != DT {DT} (frame-comparability BROKEN)"

    # (a) static constant parity: the s5 R6 solref == the live production pad solref.
    assert tuple(float(v) for v in B3.R6_B4) == ssot["pad_solref"], (
        f"s5 R6_B4 {B3.R6_B4} != live MUJOCO_PAD_SOLREF {ssot['pad_solref']} — S0 not representative"
    )

    # (a) runtime geom readback: build the s5 pinch env + apply the production R7 payload, read back
    # the ACTUAL mujoco model contact params and assert == live task_config (fail-closed).
    env = R5.build_with_eq(with_cable=True, tag="srg_s0_ssot_verify")
    rb, pad_rows, _ = R7.apply_rev7_payload(env)
    m = env["solver"].mj_model
    for g in pad_rows:
        m.geom_solref[g] = B3.R6_B4  # pin the R6 production cell (pinch_axial_cell sets this per-cell)
    pad_solref_after = tuple(float(v) for v in m.geom_solref[pad_rows[0]])
    readback = {
        "impratio": float(rb["opt"]["impratio"]),
        "condim_pad": list(rb["condim_readback"]["pad"]),
        "pad_solref_after": pad_solref_after,
        "frame_dt_10sub": frame_10,
        "frame_dt_4sub": frame_4,
        "DT": float(DT),
    }
    assert readback["impratio"] == ssot["impratio"], f"impratio {readback['impratio']} != {ssot['impratio']}"
    assert readback["condim_pad"] == [ssot["condim"]], f"condim {readback['condim_pad']} != [{ssot['condim']}]"
    assert pad_solref_after == ssot["pad_solref"], f"pad_solref {pad_solref_after} != {ssot['pad_solref']}"
    return readback


def run_s0():
    """S0: 4-substep AXIAL creep-floor re-measure (isolated pinch, R6) + K regime-screen.

    Reuses s5_calib_bench3r.{landing_control, pinch_axial_cell} verbatim (proven corrected instrument),
    monkeypatching the substep count + substep dt to the RL fidelity FIRST (so both the landing check
    and the cells run at 4-substep, one frame = DT). Cells = R6 x {F=0 floor, F=0.44 service-load pair}.
    """
    import s5_calib_bench3r as B3
    import test_newton_clip_routing as T
    import warp as wp
    from newton_skill_env_base import RL_SIM_DT, RL_SIM_SUBSTEPS

    # D1 gate FIRST (fail-closed) — an unrepresentative floor must not be measured.
    ssot_readback = verify_contact_ssot_and_framecomp()

    # 4-substep monkeypatch: pinch_axial_cell/landing_control read T.SIM_SUBSTEPS + T.SIM_DT at CALL
    # time (s5_calib_bench3r.py:77,84,89,163,178), so this takes effect for the measurement.
    orig_substeps, orig_dt = T.SIM_SUBSTEPS, T.SIM_DT
    T.SIM_SUBSTEPS, T.SIM_DT = RL_SIM_SUBSTEPS, RL_SIM_DT
    try:
        wp.init()
        landing_ok, dy = B3.landing_control()  # rule-2 free-body true-positive, now at 4-substep
        cells = {}
        if landing_ok:
            for F in (0.0, 0.44):  # floor + service-load pair (5x overload dropped: floor is the S0 target)
                cells[f"R6_F{str(F).replace('.', '')}"] = B3.pinch_axial_cell(f"R6_F{F}", B3.R6_B4, F)
    finally:
        T.SIM_SUBSTEPS, T.SIM_DT = orig_substeps, orig_dt

    floor = cells.get("R6_F00", {})
    creep_4sub = floor.get("creep_um_per_f")
    transfer = (creep_4sub / BANK_10SUB_R6_UM_PER_F) if creep_4sub else None
    # K regime screen + qualitative-breakdown screen (s5 emits collapse/badqacc/abort).
    breakdown = bool(floor.get("abort")) or (floor.get("collapse", 0) > 0) or (floor.get("badqacc", 0) > 0)
    regime_change = (transfer is not None and transfer > K_REGIME_SCREEN)
    s0_verdict = "STOP_SURFACE" if (breakdown or regime_change or creep_4sub is None) else "PROCEED_TO_S1"

    return {
        "stage": "S0",
        "landing_control": {"ok": bool(landing_ok), "dy_mm": round(float(dy), 2)},
        "d1_contact_ssot_readback": ssot_readback,
        "cells": cells,
        "bank_10sub_r6_um_per_f": BANK_10SUB_R6_UM_PER_F,
        "creep_4sub_um_per_f": creep_4sub,
        "transfer_factor_4sub_over_10sub": round(transfer, 3) if transfer else None,
        "k_regime_screen": K_REGIME_SCREEN,
        "substep_ratio": SUBSTEP_RATIO,
        "qualitative_breakdown": breakdown,
        "regime_change_vs_K": regime_change,
        "s0_verdict": s0_verdict,
    }


def run_s1():
    """S1: DIRECT z/lateral cage-escape go/no-go on the REAL route grasp (creep-budgeted over W_svc).

    [BUILD PENDING — next chunk]. Spec (DRAFT §13, %12-VERIFIED): grasp_actuation=ON (standalone
    temporary) 4-substep servo-close at nominal C1 in the REAL route geometry (cuda:0-only, route
    device-fragile); hold over W_svc (conservative 900 RL x 10 = 9000 physics frames). Measure
    PER-AXIS: axial com-along-cable (benign slide, report) + LATERAL/z cage-escape (the gate).
    PASS (creep-budgeted, NOT no-slip): (a) rate_load/rate_unloaded <= ~1.2 (runaway) AND (b) lateral/z
    over W_svc within DIRECT cage-escape margins (DROP_LATERAL_DEV_MAX 60mm / DROP_LIFT_MARGIN 10mm /
    contact-loss debounce 8; newton_route_env.py:243-245) AND end-of-hold task predicates (C1 z<0.840,
    C2 wall<=0.5mm). Observable-bound (CC3-CH4): per-axis rates + slip-time-series + human-GT + video claw-zoom.
    """
    raise NotImplementedError("S1 build pending (next chunk) — spec in docstring; RUN HELD until %12/Rs auth.")


def run_s2():
    """S2: tail-cell screening — nominal + DR-corner (+-16mm table-void edge) + known-hard; gate = worst.

    [BUILD PENDING — next chunk]. nominal is easiest (non-conservative, CC3-CH5) so nominal-only cannot
    gate the 81-offset tail; the go/no-go verdict = the WORST screened cell.
    """
    raise NotImplementedError("S2 build pending (next chunk) — spec in docstring; RUN HELD until %12/Rs auth.")


_STAGES = {"s0": run_s0, "s1": run_s1, "s2": run_s2}


def main() -> int:
    ap = argparse.ArgumentParser(description="SRG probe (staged grip-efficacy go/no-go)")
    ap.add_argument("--stage", choices=sorted(_STAGES), required=True)
    args = ap.parse_args()
    t0 = time.time()
    out = _STAGES[args.stage]()
    out["elapsed_s"] = round(time.time() - t0, 1)
    out["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    path = os.path.join(OUT_DIR, f"srg_probe_{args.stage}_result.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[SRG {args.stage.upper()}] verdict={out.get('s0_verdict', out.get('verdict', 'n/a'))} -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
