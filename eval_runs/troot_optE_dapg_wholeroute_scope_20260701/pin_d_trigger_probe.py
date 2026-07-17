# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""pin (d-a) live-geometric trigger probe -- legs L-D(d) / L-D2(d) / L-E + L-F trace (prereg v0.6 sec 5).

Adapts pin_ab_lifecycle_probe.py for the K-dwell geometric trigger: the pin no longer fires at the recording's
pin_active onset but when the identity seat body DWELLS in a route clip's capture volume AT DEPTH
(``clip_capture_check`` AND ``z <= Z_FIRE_DEPTH_M``) for ``PIN_TRIGGER_DWELL_K`` consecutive physics frames.

Legs (bars preregistered in PIN_D_TRIGGER_PREREG_RSTECHLEAD_20260717.md sec 5, v0.6):
  L-D(d)  ep1: geometric fire -> hard bars {fire_step in [242,250]; latch < fire; fire_label non-gate (sec 8.13);
          anchor z in [830.604, 830.899] mm; dwell == K; eq_active == 1; audit PASS; retention z<836 fire->done}
          -> done-reset clears eq + witness None -> ep2: re-fire, same bars. characterization-only: seat z @ done,
          residual push (min seat z below anchor), reward trace.
  L-D2(d) ep1/ep2 event timeline (fire_step / G first-latch steps / done step / term flags) EXACT = hard.
          reward per-step trace diff = characterization-only (recorded; not a PASS gate, prereg pN B5).
  L-E     eq_active adjacency across the done-reset: symmetric diff outside the fired eq = empty.
  L-F     --trace N: fixed-length flag-OFF stepping with per-step phys/obs/reward/done digests (L-F1 byte
          identity vs baseline; L-F2 flag-ON declared delta -- the cross-tree compare is done by the caller).

Bypass legs L-C3/L-C4/L-C5 are INHERITED (re-run pin_ab_lifecycle_probe.py --bypass against the extended
_clear_c1_pin, prereg sec 5 L-C3-5).

Run (cuda:0 pinned, CPU mujoco stepping; one cell per process):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_d_trigger_probe.py --cell cell_x0_y0
"""

from __future__ import annotations

import argparse
import hashlib
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
assert _CVD == "0", f"(d-a) trigger probe runs the as-coded substrate on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import route_env_config as rc  # noqa: E402
import route_executor as rex  # noqa: E402
import torch  # noqa: E402
import warp as wp  # noqa: E402

GRID = _EVAL / "w0e_81rerun_snapdown_0537"

# (d-a) hard timing bars (prereg v0.6 sec 2-11 / sec 5 L-D; charter sec 8.13). fire_label is a RECORDED standing
# anchor, NOT a PASS gate: the live env RE-SIMS the cable (it does not byte-replay the recording), so the route-clock
# fire frame differs from the offline npz-index (2468, RETIRED) by a live-physics amount (charter sec 8.13). The hard
# protection is fire_step-band + anchor-band + latch-precedes-fire + retention (coarse, robust to sub-frame drift).
FIRE_LABEL_STANDING_ANCHOR = 2462  # live route-clock standing anchor (charter sec 8.13; drift is loud, not gated)
FIRE_STEP_BAND = (242, 250)  # HARD timing bar (episode-relative RL step; canonical 246)
ANCHOR_Z_BAND_M = (0.830604, 0.830899)  # HARD anchor band; canonical 830.640 mm
RETENTION_CEILING_M = rc.SEAT_Z_HI_M  # 0.836: the pin must keep the seat below the rim fire->done


def _scalarize(extras) -> dict:
    """Defensively flatten (1,)-shaped tensor entries of extras (one nested level) for the timeline."""
    out = {}
    for key, val in extras.items():
        if isinstance(val, dict):
            for k2, v2 in val.items():
                if hasattr(v2, "shape") and tuple(getattr(v2, "shape", ())) == (1,):
                    out[f"{key}.{k2}"] = float(v2[0])
        elif hasattr(val, "shape") and tuple(getattr(val, "shape", ())) == (1,):
            out[key] = float(val[0])
    return out


def _seat_z(env) -> float:
    """World z [m] of the identity seat body (the (d-a) trigger body), post-step."""
    wp.synchronize()
    bq = env._state_0.body_q.numpy()
    seat_body = int(env._cable_bodies[0][int(env._pin_seat_seg)])
    return float(bq[seat_body, 2])


def run_episode(env, label: str) -> dict:
    zero = torch.zeros((1, 6), dtype=torch.float32)
    mjd = env._solver.mj_data
    out = {
        "label": label,
        "fire_step": None,  # witness fire_step (episode-relative, prereg sec 2-D)
        "fire_step_loop_t": None,  # the RL-step index the probe first saw the witness (consistency cross-check)
        "fire_label": None,  # witness fired_at_frame (physics frame)
        "anchor_z_mm": None,
        "dwell_at_fire": None,
        "eq_id": None,
        "eq_active_at_fire": None,
        "audit_at_fire": None,
        "g_first_latch": [None] * 6,
        "done_step": None,
        "term": None,
        "reward_sum": 0.0,
        "reward_trace": [],
        "seat_z_trace_mm": [],
        "post_reset_witness_none": None,
        "post_reset_eq_cleared": None,
        "adjacency_sym_diff_empty": None,
        "retention_max_seat_z_after_fire_mm": None,  # <= 836 => held below the rim
        "seat_z_at_done_mm": None,
        "residual_push_mm": None,  # anchor_z - min(seat z after fire): how much deeper it settled past the weld
    }
    max_seat_after_fire = -1e9
    min_seat_after_fire = 1e9
    for t in range(env.MAX_EPISODE_STEPS + 1):
        eq_pre = np.asarray(mjd.eq_active).copy()  # state ENTERING step t (pre-reset at the done step)
        g_pre = np.asarray(env._g_latched[0]).copy()
        for gi in range(6):
            if out["g_first_latch"][gi] is None and bool(g_pre[gi]):
                out["g_first_latch"][gi] = t - 1  # latched during step t-1 (pre-step read; symmetric across eps)
        _obs, rew, dones, extras = env.step(zero)
        r = float(rew[0])
        out["reward_trace"].append(r)
        out["reward_sum"] += r
        sz = _seat_z(env)
        out["seat_z_trace_mm"].append(round(sz * 1e3, 4))
        if out["fire_step"] is None and env._c1_pin_witness is not None:
            w = env._c1_pin_witness
            out["fire_step"] = int(w.get("fire_step", -1))
            out["fire_step_loop_t"] = t
            out["fire_label"] = int(w.get("fired_at_frame", -1))
            out["anchor_z_mm"] = round(float(w["seat_world"][2]) * 1e3, 4)
            out["dwell_at_fire"] = int(w.get("dwell_count", -1))
            out["eq_id"] = int(w["eq_id"])
            out["eq_active_at_fire"] = int(mjd.eq_active[out["eq_id"]])
            try:
                rex.audit_pin_anchors(env._solver.mj_model, mjd)
                out["audit_at_fire"] = "PASS"
            except AssertionError as e:
                out["audit_at_fire"] = f"RAISE {str(e)[:120]}"
        if out["fire_step"] is not None and out["done_step"] is None:
            max_seat_after_fire = max(max_seat_after_fire, sz)
            min_seat_after_fire = min(min_seat_after_fire, sz)
        if bool(dones[0]):
            out["done_step"] = t
            out["term"] = _scalarize(extras)
            eq_post = np.asarray(mjd.eq_active).copy()  # step() already ran the done-reset for world 0
            out["post_reset_witness_none"] = env._c1_pin_witness is None
            if out["eq_id"] is not None:
                out["post_reset_eq_cleared"] = int(eq_post[out["eq_id"]]) == 0
                mask = np.ones(eq_pre.shape[0], dtype=bool)
                mask[out["eq_id"]] = False
            else:
                mask = np.ones(eq_pre.shape[0], dtype=bool)
            out["adjacency_sym_diff_empty"] = bool(np.array_equal(eq_pre[mask], eq_post[mask]))
            out["seat_z_at_done_mm"] = round(sz * 1e3, 4)
            break
    if out["fire_step"] is not None and max_seat_after_fire > -1e8:
        out["retention_max_seat_z_after_fire_mm"] = round(max_seat_after_fire * 1e3, 4)
        if out["anchor_z_mm"] is not None and min_seat_after_fire < 1e8:
            out["residual_push_mm"] = round(out["anchor_z_mm"] - min_seat_after_fire * 1e3, 4)
    return out


def run_trace(env, steps: int) -> dict:
    """L-F1/L-F2 instrument: fixed-length flag-OFF stepping with 4-channel per-step digests (through done-resets)."""
    zero = torch.zeros((1, 6), dtype=torch.float32)
    phys_h, obs_h, rew, done_steps, term_at_done, obs_dump = [], [], [], [], [], []
    for _t in range(steps):
        obs, r, dones, extras = env.step(zero)
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        obs_np = obs.cpu().numpy().ravel()
        obs_dump.append(obs_np.copy())
        phys_h.append(hashlib.sha256(bq.tobytes()).hexdigest()[:16])
        obs_h.append(hashlib.sha256(obs_np.tobytes()).hexdigest()[:16])
        rew.append(round(float(r[0]), 10))
        if bool(dones[0]):
            done_steps.append(_t)
            term_at_done.append(_scalarize(extras))
    final = hashlib.sha256(
        ("".join(phys_h) + "".join(obs_h) + json.dumps(rew) + json.dumps(done_steps)).encode()
    ).hexdigest()
    return {
        "steps": steps,
        "phys": phys_h,
        "obs": obs_h,
        "reward": rew,
        "done_steps": done_steps,
        "term_at_done": term_at_done,
        "final_digest": final,
        "_obs_dump": obs_dump,
    }


def _ld_ep_pass(ep: dict) -> dict:
    """The L-D(d) PASS logic for one episode (prereg sec 5 L-D, corrected by charter sec 8.13, 2026-07-17).

    fire_label is NOT a PASS gate: per sec 2-11 it is drift-loud / standing-anchor, and an exact-frame bar is
    physically unattainable because the live env re-sims the cable (charter sec 8.13). PASS is the coarse hard
    timing protection: fire_step-band AND anchor-band AND latch-precedes-fire AND the behavioral bars (dwell,
    audit, eq_active, reset, witness, retention). fire_label is recorded as the standing anchor (loud on drift).
    """
    latches = [g for g in ep["g_first_latch"] if g is not None]
    checks = {
        "fired": ep["fire_step"] is not None,
        "fire_step_in_band": ep["fire_step"] is not None and FIRE_STEP_BAND[0] <= ep["fire_step"] <= FIRE_STEP_BAND[1],
        "anchor_z_in_band": ep["anchor_z_mm"] is not None
        and ANCHOR_Z_BAND_M[0] * 1e3 <= ep["anchor_z_mm"] <= ANCHOR_Z_BAND_M[1] * 1e3,
        "latch_precedes_fire": ep["fire_step"] is not None and len(latches) > 0 and max(latches) < ep["fire_step"],
        "dwell_eq_K": ep["dwell_at_fire"] == rc.PIN_TRIGGER_DWELL_K,
        "eq_active_at_fire": ep["eq_active_at_fire"] == 1,
        "audit_pass": ep["audit_at_fire"] == "PASS",
        "reset_cleared": ep["post_reset_eq_cleared"] is True,
        "reset_witness_none": ep["post_reset_witness_none"] is True,
        "retention_below_rim": ep["retention_max_seat_z_after_fire_mm"] is not None
        and ep["retention_max_seat_z_after_fire_mm"] < RETENTION_CEILING_M * 1e3,
    }
    checks["PASS"] = all(checks.values())
    # sec 8.13: recorded/loud, NOT a gate. offline npz-index 2468 RETIRED; live route-clock is the standing anchor.
    checks["fire_label_standing_anchor"] = ep["fire_label"]
    checks["fire_label_drift_vs_anchor"] = (
        None if ep["fire_label"] is None else ep["fire_label"] - FIRE_LABEL_STANDING_ANCHOR
    )
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True, help="e.g. cell_x0_y0")
    ap.add_argument("--trace", type=int, default=0, help="L-F mode: run N fixed flag-OFF steps and dump digests")
    ap.add_argument("--tag", default="bundle", help="trace output tag (bundle | f1base | head)")
    args = ap.parse_args()
    npz = GRID / args.cell / "route_demo_raw.npz"
    assert npz.exists(), f"recording missing: {npz}"
    out_path = _EVAL / f"pin_d_trigger_probe_result_{args.cell}.json"

    trace_mode = args.trace > 0
    print(f"[pin_d] building route env (route_c1_pin={not trace_mode}, feedforward, cuda:0) recording={npz}")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(npz),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
            "route_c1_pin": not trace_mode,  # L-F trace legs are flag-OFF by prereg
        },
    )
    env.INIT_XY_NOISE = 0.0  # L-D determinism pin (class default would break the L-D2 timeline bar)
    env.reset()

    if trace_mode:
        tr = run_trace(env, args.trace)
        obs_dump = tr.pop("_obs_dump")
        tp = _EVAL / f"pin_d_trace_{args.cell}_{args.tag}.json"
        tp.write_text(json.dumps(tr, indent=2))
        np.save(str(tp).replace(".json", "_obs.npy"), np.stack(obs_dump))
        print(
            f"[pin_d] trace tag={args.tag} steps={tr['steps']} done_steps={tr['done_steps']} "
            f"term_at_done={tr['term_at_done']} final={tr['final_digest'][:16]} -> {tp}"
        )
        return 0

    result = {"cell": args.cell, "Z_FIRE_DEPTH_M": rc.Z_FIRE_DEPTH_M, "K": rc.PIN_TRIGGER_DWELL_K}
    ep1 = run_episode(env, "ep1")
    print(
        f"[pin_d] ep1: fire_step={ep1['fire_step']} label={ep1['fire_label']} anchor_z={ep1['anchor_z_mm']}mm "
        f"dwell={ep1['dwell_at_fire']} audit={ep1['audit_at_fire']} done={ep1['done_step']}"
    )
    ep2 = run_episode(env, "ep2")
    print(
        f"[pin_d] ep2: fire_step={ep2['fire_step']} label={ep2['fire_label']} anchor_z={ep2['anchor_z_mm']}mm "
        f"dwell={ep2['dwell_at_fire']} audit={ep2['audit_at_fire']} done={ep2['done_step']}"
    )

    trace1, trace2 = ep1.pop("reward_trace"), ep2.pop("reward_trace")
    n = min(len(trace1), len(trace2))
    reward_diff = [abs(a - b) for a, b in zip(trace1[:n], trace2[:n])]
    result["ep1"], result["ep2"] = ep1, ep2

    ld1, ld2 = _ld_ep_pass(ep1), _ld_ep_pass(ep2)
    result["L_D"] = {"ep1": ld1, "ep2": ld2, "PASS": bool(ld1["PASS"] and ld2["PASS"])}
    timeline_equal = (
        ep1["fire_step"] == ep2["fire_step"]
        and ep1["g_first_latch"] == ep2["g_first_latch"]
        and ep1["done_step"] == ep2["done_step"]
        and ep1["term"] == ep2["term"]
    )
    result["L_D2"] = {
        "PASS_hard_timeline": bool(timeline_equal),
        "reward_trace_len": [len(trace1), len(trace2)],
        "reward_max_abs_step_diff": max(reward_diff) if reward_diff else 0.0,  # characterization-only (pN B5)
        "reward_sum_diff": abs(ep1["reward_sum"] - ep2["reward_sum"]),
    }
    result["L_E"] = {"PASS": bool(ep1["adjacency_sym_diff_empty"] and ep2["adjacency_sym_diff_empty"])}

    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("ep1", "ep2")}, indent=2))
    print(
        f"[pin_d] L-D={result['L_D']['PASS']} L-D2(hard)={result['L_D2']['PASS_hard_timeline']} "
        f"L-E={result['L_E']['PASS']} -> {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
