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
  (G) P0 cable-parity MEASUREMENT vs the golden pre-grasp frame (G-F1a, fold 3): quantifies the
      support-clip topology difference (clip-suspended env vs table-resting recording) for the Rs
      G-F1b A/B adjudication. Measurement leg -- PARITY=False is the EXPECTED current state.
  (G2) G1-prework DoD (Rs 裁定 A): the g1_scene_align build (support clips OFF + cable start Y
      re-seeded to the recording frame-0 value) settles to the recording's table-resting pre-grasp
      cable within 2 mm per segment (GATED) + exactly the 4 REST clips' statics removed.
  (F) N=2 flag-ON per-world grip ctrl routing at RUNTIME (P-F1, fold 2): write-side per-world routing
      (stride detector) + WORLD-0 (the stepped template world) closes physically while world-1 targets
      stay OPEN; the inverse write then MEASURES the world-1 freeze (K3 worlds>=1-frozen, banked) at the
      grip level as Rs escalation material.

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
    # G-F5 (fold 8c): identify the CABLE geoms explicitly (dynamic capsules -- the cable is the
    # rigid-capsule chain; non-pad arm shapes are VISIBLE-only so they cannot contact) instead of
    # counting every non-pad pair as "cable".
    cable_geom_ids = {
        g
        for g in range(m.ngeom)
        if int(m.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_CAPSULE) and int(m.geom_bodyid[g]) != 0
    }
    ncon = int(d.ncon)
    pad_static = 0
    cable_table = 0
    cable_static = 0
    other_static = 0
    for i in range(ncon):
        g1, g2 = int(d.contact[i].geom1), int(d.contact[i].geom2)
        pair = {g1, g2}
        if pair & pads and pair & static_ids:
            pad_static += 1
        elif pair & cable_geom_ids and pair & table_ids:
            cable_table += 1
            cable_static += 1
        elif pair & cable_geom_ids and pair & static_ids:
            cable_static += 1
        elif pair & static_ids:
            other_static += 1
    leg(
        "D_no_pad_static_artifact",
        pad_static == 0 and cable_static > 0 and other_static == 0,
        f"settled P0 contacts: ncon={ncon}, pad<->static={pad_static} (exp 0: claws hover clear), "
        f"cable<->static={cable_static} (exp >0 non-vacuity; clip-supported route scene), "
        f"cable<->bare-table={cable_table} (informative; 0 is physical: cable rides the support clips), "
        f"other<->static={other_static} (exp 0: only the cable may touch statics at P0)",
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

    # ---- (G) P0 cable-parity MEASUREMENT vs the golden recording pre-grasp frame (G-F1a, fold 3). ----
    # This leg QUANTIFIES the support-clip topology difference for the Rs surface (G-F1b A/B adjudication);
    # it is a MEASUREMENT leg (pass = measurement completed + recorded LOUD), NOT a parity gate -- the
    # recording scene has NO support clips (table-resting z~0.804) while the env flag-ON scene clip-suspends
    # the cable, so PARITY=False is the EXPECTED current state.
    z = np.load(GOLDEN_NPZ, allow_pickle=True)
    gold_xyz = np.asarray(z["cable_xyz"][0], dtype=float)  # [40, 3] pre-grasp frame 0
    bq = env._state_0.body_q.numpy()
    env_xyz = np.asarray(bq[env._cable_bodies[0], :3], dtype=float)  # world-0 settled cable
    n_seg = min(len(gold_xyz), len(env_xyz))
    dz = env_xyz[:n_seg, 2] - gold_xyz[:n_seg, 2]
    dy = env_xyz[:n_seg, 1] - gold_xyz[:n_seg, 1]
    parity = bool(np.max(np.abs(dz)) < 0.002 and np.max(np.abs(dy)) < 0.002)
    result["p0_cable_parity"] = {
        "parity_2mm": parity,
        "max_abs_dz_mm": float(np.max(np.abs(dz)) * 1e3),
        "mean_dz_mm": float(np.mean(dz) * 1e3),
        "max_abs_dy_mm": float(np.max(np.abs(dy)) * 1e3),
        "env_z_mean": float(np.mean(env_xyz[:n_seg, 2])),
        "gold_z_mean": float(np.mean(gold_xyz[:n_seg, 2])),
        "n_seg": int(n_seg),
    }
    result["p0_cable_parity"]["dy_seg0_mm"] = float(dy[0] * 1e3)
    result["p0_cable_parity"]["dy_mid_mm"] = float(dy[n_seg // 2] * 1e3)
    result["p0_cable_parity"]["dy_last_mm"] = float(dy[n_seg - 1] * 1e3)
    leg(
        "G_p0_cable_parity_MEASURE",
        True,  # measurement leg: quantifies G-F1 for Rs; parity itself is NOT gated here
        f"PARITY(2mm)={parity} [EXPECTED False: clip-suspended env vs table-resting recording]; "
        f"max|dz|={result['p0_cable_parity']['max_abs_dz_mm']:.1f}mm mean dz="
        f"{result['p0_cable_parity']['mean_dz_mm']:.1f}mm max|dy|="
        f"{result['p0_cable_parity']['max_abs_dy_mm']:.1f}mm "
        f"(dy seg0/mid/last = {result['p0_cable_parity']['dy_seg0_mm']:.1f}/"
        f"{result['p0_cable_parity']['dy_mid_mm']:.1f}/{result['p0_cable_parity']['dy_last_mm']:.1f}mm); "
        f"env z-mean={result['p0_cable_parity']['env_z_mean']:.4f} vs gold z-mean="
        f"{result['p0_cable_parity']['gold_z_mean']:.4f} -> Rs surface material (G-F1b A/B)",
    )

    # ---- (G2) G1-prework DoD: ALIGNED build parity vs the recording (Rs 裁定 A; GATED). ----
    # g1_scene_align = support clips OFF + cable start Y re-seeded to the recording's frame-0 value.
    # DoD: the aligned settled P0 cable matches the recording pre-grasp per-segment within 2 mm.
    print("[G2] building flag-ON + g1_scene_align env (world_count=1, cpu) ...")
    env_al = nre.NewtonRouteEnv(
        world_count=1,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
        },
    )
    bq_al = env_al._state_0.body_q.numpy()
    al_xyz = np.asarray(bq_al[env_al._cable_bodies[0], :3], dtype=float)
    dz2 = al_xyz[:n_seg, 2] - gold_xyz[:n_seg, 2]
    dy2 = al_xyz[:n_seg, 1] - gold_xyz[:n_seg, 1]
    aligned = bool(np.max(np.abs(dz2)) < 0.002 and np.max(np.abs(dy2)) < 0.002)

    # support clips absent: the flag-ON build had 4 REST clips x 5 static boxes = 20 more non-table statics.
    def _nontable_static_boxes(mm):
        total = 0
        for g in range(mm.ngeom):
            if int(mm.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_BOX) and int(mm.geom_bodyid[g]) == 0:
                total += 1
        return total

    delta_statics = _nontable_static_boxes(m) - _nontable_static_boxes(env_al._solver.mj_model)
    result["p0_cable_parity_aligned"] = {
        "aligned_2mm": aligned,
        "max_abs_dz_mm": float(np.max(np.abs(dz2)) * 1e3),
        "max_abs_dy_mm": float(np.max(np.abs(dy2)) * 1e3),
        "support_clip_static_boxes_removed": int(delta_statics),
    }
    leg(
        "G2_p0_cable_parity_ALIGNED",
        aligned and delta_statics == 20,
        f"ALIGNED(2mm)={aligned}: max|dz|={result['p0_cable_parity_aligned']['max_abs_dz_mm']:.2f}mm "
        f"max|dy|={result['p0_cable_parity_aligned']['max_abs_dy_mm']:.2f}mm (exp <2mm both; prework DoD); "
        f"support-clip statics removed={delta_statics} (exp 20 = 4 REST clips x 5 boxes; C1/C2 stay)",
    )

    # ---- (F) N=2 flag-ON per-world grip ctrl routing, RUNTIME (P-F1, fold 2). ----
    # world_count=1 structurally hides q/qd stride errors. Substrate truth (K3/R3, banked): on the as-coded
    # CPU path only the single-world TEMPLATE (= world-0) is physics-stepped; worlds>=1 are FROZEN. So the
    # runtime leg drives WORLD-0 to CLOSE (route step 112 -> frame 1120 [0.7407, 0.7407]) with world-1 held
    # OPEN: world-0 must MOVE physically, world-1 targets must be routed per-world (write-side stride
    # detector), and the INVERSE write (world-1 CLOSE) is then MEASURED to document the world-1 freeze
    # empirically at grip level (Rs worlds>=1 escalation material; probe run 5 initially mis-expected
    # world-1 to close and FAILED -- verify-premises-first: the freeze is the banked substrate state).
    print("[F] building flag-ON env (world_count=2, cpu) for per-world grip routing ...")
    env2 = nre.NewtonRouteEnv(
        world_count=2,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
        },
    )
    maps2 = env2._route._maps
    drv_local = [6, 10, 20, 24]
    # phase 1: w0 CLOSE (t=112) / w1 OPEN (t=0) -- write-side routing + stepped-world physical close.
    env2._route.apply_recorded_grip([112, 0], 0)
    jtp2 = env2._control.joint_target_pos.numpy()
    w0_dofs = maps2["l_driver_dofs"][0] + maps2["r_driver_dofs"][0]
    w1_dofs = maps2["l_driver_dofs"][1] + maps2["r_driver_dofs"][1]
    route_ok = all(abs(float(jtp2[dd]) - 0.7407) < 1e-4 for dd in w0_dofs) and all(
        abs(float(jtp2[dd])) < 1e-6 for dd in w1_dofs
    )
    env2._hold_all_worlds(120)  # arms held (flag-ON = arm-only write); world-0 servo closes free-air
    jq2 = env2._state_0.joint_q.numpy()
    w0_q = [float(jq2[env2._arm_q_start[0] + li]) for li in drv_local]
    w1_q = [float(jq2[env2._arm_q_start[1] + li]) for li in drv_local]
    moved_ok = all(q > 0.3 for q in w0_q) and all(abs(q) < 0.05 for q in w1_q)
    # phase 2 (MEASUREMENT, not gated): INVERSE write w1 CLOSE / w0 OPEN -> w1 stays frozen (K3 empirical).
    env2._route.apply_recorded_grip([0, 112], 0)
    jtp2b = env2._control.joint_target_pos.numpy()
    inverse_routed = all(abs(float(jtp2b[dd]) - 0.7407) < 1e-4 for dd in w1_dofs)
    env2._hold_all_worlds(60)
    jq2b = env2._state_0.joint_q.numpy()
    w1_q_after = [float(jq2b[env2._arm_q_start[1] + li]) for li in drv_local]
    w1_frozen = all(abs(q) < 1e-6 for q in w1_q_after)
    result["worlds_ge1_freeze_empirical"] = {
        "w1_close_target_routed": bool(inverse_routed),
        "w1_driver_q_after_60_frames": w1_q_after,
        "w1_frozen": bool(w1_frozen),
        "note": "K3/R3 banked worlds>=1-frozen CONFIRMED at grip level: w1 CLOSE target routed correctly "
        "(write side) but w1 physics never steps on the as-coded CPU path -> Rs escalation material",
    }
    leg(
        "F_n2_perworld_grip_routing",
        route_ok and moved_ok,
        f"write-side routing (w0 CLOSE/w1 OPEN) -> {route_ok}; after 120 held frames w0 drivers "
        f"q={[round(q, 3) for q in w0_q]} (exp >0.3: stepped world closes) vs w1 "
        f"q={[round(q, 3) for q in w1_q]} (exp ~0 OPEN) -> {moved_ok}. INVERSE (w1 CLOSE) MEASURED: "
        f"routed={inverse_routed}, w1 q after 60f={[round(q, 4) for q in w1_q_after]} -> "
        f"frozen={w1_frozen} (K3 worlds>=1-frozen EMPIRICAL at grip level; Rs escalation material)",
    )

    all_ok = all(v["pass"] for v in result["legs"].values())
    result["verdict"] = "PASS" if all_ok else "FAIL"
    result["meta"] = {
        "world_count": "1 (legs A-E, G, G2) + 2 (leg F)",
        "device": "cpu (CUDA_VISIBLE_DEVICES='')",
        "golden_npz": str(GOLDEN_NPZ),
        "scope": "build+readback+grip-routing ONLY (no route rollout; G1 GPU behind PLG + Rs)",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(f"[comp3_void_readback] verdict={result['verdict']} -> {OUT_JSON}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
