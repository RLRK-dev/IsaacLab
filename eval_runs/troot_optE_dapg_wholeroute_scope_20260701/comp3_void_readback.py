# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 chunk-3 L2 probe: env-path flag-ON build readback (void parity + servo discriminating + solref pin).

No-GPU / CPU-FORCED (plan v2 sec 15 L2; %12 chunk-3 dispatch). Builds the ROUTE ENV (the FORK-1 surface:
``NewtonRouteEnv._build_model`` -> ``build_multiworld_scene``) twice on the CPU substrate and reads back the
as-built model -- no rollout, no GPU (G1 stays behind /production-launch-gate + Rs).

Legs:
  (A) flag-OFF build + ``servo_readback_assert`` -> MUST RAISE (the REAL-build discriminating proof, K6:
      an unwired build fails the readback; the mock-level proof lives in test_routeexec_writesite.py).
  (B) flag-ON build (grasp_actuation + route_executor + golden recording) -> build completes; the readback
      runs INSIDE ``_build_model`` and is re-run here explicitly for the record.
  (C) void readback (as-BUILT mj_model geoms): table = 4 static boxes; Y void == [WIDE_LEFT_Y - 0.016,
      WIDE_RIGHT_Y + 0.016] == [0.090, 0.210]; X footprint window == [0.234, 0.366] (base void formula).
  (D) claw/pad <-> STATIC contact artifact: NONE at the settled P0 (claws hover clear of table AND clips);
      non-vacuity = cable<->static contacts > 0 (route scene: the cable rides the SUPPORT CLIPS, not the
      bare table -- premise corrected from SRG's clip-less isolated-grasp scene at probe run 3).
  (E) mj_model pad solref == MUJOCO_PAD_SOLREF (AUTHORITATIVE per R3, CPU substrate); mjw solref RECORDED
      (inert on the CPU path, CC3-CH7 -- no hard assert); mjw-eq-DEFERRED pin recorded (base _wire doc:
      the 4-bar eq stiffen is mj_model-template-only; comp3 FORBIDS an mjw eq re-poke).

Run (CPU forced; the probe fail-louds if CUDA_VISIBLE_DEVICES is not empty):
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_void_readback.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# CPU-forced gate (fail loud BEFORE any warp/newton import initializes a device).
assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", (
    "comp3_void_readback is a no-GPU CPU probe: run with CUDA_VISIBLE_DEVICES='' (empty), got "
    f"{os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')!r}"
)

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402
import route_executor as rex  # noqa: E402
from configs.task_config import (  # noqa: E402
    MUJOCO_PAD_SOLREF,
    TABLE_HEIGHT,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT_JSON = _EVAL_DIR / "comp3_void_readback_result.json"
_TABLE_HZ = 0.005  # base table_half[2] (box half-thickness; the static-table identifier)
_TABLE_HX_FULL = 0.35  # base table_half[0] (the 2 full-X Y-side boxes)


def _static_table_boxes(m):
    """(geom_id, center xyz, half-size xyz) of the TABLE boxes: worldbody BOX geoms at the table center-z.

    hz alone is too loose (clip-base statics share hz=0.005; probe run 1 counted 11): the table boxes are
    the ONLY statics centered at ``TABLE_HEIGHT - 0.005`` (base ``table_cz``; clip geoms sit ON the table,
    z >= TABLE_HEIGHT).
    """
    table_cz = TABLE_HEIGHT - 0.005  # base table_cz
    boxes = []
    for g in range(m.ngeom):
        if int(m.geom_type[g]) != int(mujoco.mjtGeom.mjGEOM_BOX):
            continue
        if int(m.geom_bodyid[g]) != 0:  # worldbody / static
            continue
        size = m.geom_size[g]
        pos = m.geom_pos[g]
        if abs(float(size[2]) - _TABLE_HZ) < 1e-6 and abs(float(pos[2]) - table_cz) < 1e-6:
            boxes.append((g, np.array(pos, dtype=float), np.array(size, dtype=float)))
    return boxes


def _pad_geoms(m):
    """Pad geom ids by the _wire_s6_grasp_solref by-NAME rule ('pad' in geom+body name, lowered)."""
    pads = []
    for g in range(m.ngeom):
        gname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or "").lower()
        if "pad" in (gname + bname):
            pads.append(g)
    return pads


def main():
    result = {"legs": {}, "verdict": None}

    def leg(name, ok, detail):
        result["legs"][name] = {"pass": bool(ok), "detail": detail}
        print(f"  [{name}] {'PASS' if ok else 'FAIL'}: {detail}")
        return ok

    print("[comp3_void_readback] L2 env-path readback probe (CPU, no rollout)")

    # ---- (A) flag-OFF build: the readback MUST RAISE (real-build discriminating proof, K6). ----
    print("[A] building flag-OFF env (world_count=1, cpu, stub route) ...")
    env_off = nre.NewtonRouteEnv(world_count=1, device="cpu", cfg={})
    maps_off = rex.build_perworld_index_maps(env_off._arm_q_start, env_off._arm_qd_start)
    neg_off = [env_off._arm_qd_start[0] + off for off in (0, 7, 21)]
    raised = False
    try:
        nre.servo_readback_assert(env_off._model, env_off._solver.mj_model, maps_off["all_driver_dofs"], neg_off)
    except AssertionError as e:
        raised = True
        raised_msg = str(e).splitlines()[0][:160]
    leg(
        "A_flagoff_readback_raises",
        raised,
        f"flag-OFF build readback raised={raised}" + (f" ({raised_msg})" if raised else " -- VACUOUS (K6 FAIL)"),
    )
    off_boxes = _static_table_boxes(env_off._solver.mj_model)
    leg("A2_flagoff_table_solid", len(off_boxes) == 1, f"flag-OFF static table boxes = {len(off_boxes)} (exp 1)")

    # ---- (B) flag-ON build (the FORK-1 close-kinematics build surface). ----
    print("[B] building flag-ON env (world_count=1, cpu, route_executor + golden recording) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
        },
    )
    m = env._solver.mj_model
    # re-run the readback explicitly for the record (it already gated _build_model).
    neg_on = [env._arm_qd_start[w] + off for w in range(env._world_count) for off in (0, 7, 21)]
    nre.servo_readback_assert(env._model, m, env._arm_ow_maps["all_driver_dofs"], neg_on)
    nu = int(m.nu)
    leg("B_flagon_build_and_readback", True, f"flag-ON build complete; servo readback PASS (mj nu={nu})")

    # ---- (C) void readback from the as-built mj_model. ----
    boxes = _static_table_boxes(m)
    c_ok = len(boxes) == 4
    y_void = x_win = None
    if c_ok:
        fullx = sorted([b for b in boxes if abs(b[2][0] - _TABLE_HX_FULL) < 1e-6], key=lambda b: b[1][1])
        xfill = sorted([b for b in boxes if abs(b[2][0] - _TABLE_HX_FULL) >= 1e-6], key=lambda b: b[1][0])
        c_ok = len(fullx) == 2 and len(xfill) == 2
        if c_ok:
            y_void = (float(fullx[0][1][1] + fullx[0][2][1]), float(fullx[1][1][1] - fullx[1][2][1]))
            x_win = (float(xfill[0][1][0] + xfill[0][2][0]), float(xfill[1][1][0] - xfill[1][2][0]))
            exp_y = (WIDE_LEFT_Y - 0.016, WIDE_RIGHT_Y + 0.016)  # base void formula == [0.090, 0.210]
            exp_x = (0.3 - 0.066, 0.3 + 0.066)  # gripper footprint window == [0.234, 0.366]
            c_ok = (
                abs(y_void[0] - exp_y[0]) < 1e-6
                and abs(y_void[1] - exp_y[1]) < 1e-6
                and abs(x_win[0] - exp_x[0]) < 1e-6
                and abs(x_win[1] - exp_x[1]) < 1e-6
            )
    c_ok = leg(
        "C_void_parity",
        c_ok,
        f"table boxes={len(boxes)} (exp 4); Y void={y_void} (exp [{WIDE_LEFT_Y - 0.016:.3f},"
        f"{WIDE_RIGHT_Y + 0.016:.3f}]); X window={x_win} (exp [0.234,0.366])",
    )

    # ---- (D) pad/claw <-> static contact artifact at settled P0. ----
    # Premise corrected after probe run 3 (verify-premises-first): in the ROUTE scene the cable is
    # SUPPORT-CLIP-supported (add_support_clips=True; contacts land on the clip statics at z~0.825), NOT
    # bare-table-supported (that premise was SRG's isolated-grasp scene, no clips). Artifact check widened:
    # the hovering claws must touch NO static at P0 (table OR clip). Non-vacuity (GROVE appearance-only
    # guard): cable<->static contacts > 0 REQUIRED (proves cable<->static collision is live, non-vacuous).
    d = env._solver.mj_data
    pads = set(_pad_geoms(m))
    table_ids = {b[0] for b in boxes}
    static_ids = {g for g in range(m.ngeom) if int(m.geom_bodyid[g]) == 0}
    ncon = int(d.ncon)
    pad_static = 0
    cable_table = 0
    cable_static = 0
    for i in range(ncon):
        g1, g2 = int(d.contact[i].geom1), int(d.contact[i].geom2)
        pair = {g1, g2}
        if pair & pads and pair & static_ids:
            pad_static += 1
        elif pair & table_ids:
            cable_table += 1
            cable_static += 1
        elif pair & static_ids:
            cable_static += 1
    leg(
        "D_no_pad_static_artifact",
        pad_static == 0 and cable_static > 0,
        f"settled P0 contacts: ncon={ncon}, pad<->static={pad_static} (exp 0: claws hover clear), "
        f"cable<->static={cable_static} (exp >0 non-vacuity; clip-supported route scene), "
        f"cable<->bare-table={cable_table} (informative; 0 is physical: cable rides the support clips)",
    )

    # ---- (E) solref pin: mj authoritative == PAD_SOLREF; mjw RECORDED (inert, CPU path); eq DEFERRED pin. ----
    pad_list = sorted(pads)
    mj_solref = [float(x) for x in np.asarray(m.geom_solref[pad_list[0]]).ravel()[:2]] if pad_list else None
    e_ok = (
        pad_list and abs(mj_solref[0] - MUJOCO_PAD_SOLREF[0]) < 1e-6 and abs(mj_solref[1] - MUJOCO_PAD_SOLREF[1]) < 1e-6
    )
    mjw = getattr(env._solver, "mjw_model", None)
    mjw_solref = None
    if mjw is not None:
        arr = mjw.geom_solref.numpy()
        row = arr[0][pad_list[0]] if arr.ndim == 3 else arr[pad_list[0]]
        mjw_solref = [float(x) for x in np.asarray(row).ravel()[:2]]
    e_ok = leg(
        "E_solref_pin",
        bool(e_ok),
        f"mj pad solref={mj_solref} == PAD_SOLREF {tuple(MUJOCO_PAD_SOLREF)} (AUTHORITATIVE, R3); "
        f"mjw={'ABSENT (CPU path)' if mjw is None else mjw_solref} (RECORDED-INERT, CC3-CH7); "
        f"mj neq={int(m.neq)}; PIN: 4-bar eq stiffen is mj_model-template-only, mjw eq re-poke DEFERRED "
        "(base _wire doc) -- comp3 FORBIDS an mjw eq re-poke",
    )

    all_ok = all(v["pass"] for v in result["legs"].values())
    result["verdict"] = "PASS" if all_ok else "FAIL"
    result["meta"] = {
        "world_count": 1,
        "device": "cpu (CUDA_VISIBLE_DEVICES='')",
        "golden_npz": str(GOLDEN_NPZ),
        "scope": "build+readback ONLY (no rollout; G1 GPU behind /production-launch-gate + Rs)",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(f"[comp3_void_readback] verdict={result['verdict']} -> {OUT_JSON}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
