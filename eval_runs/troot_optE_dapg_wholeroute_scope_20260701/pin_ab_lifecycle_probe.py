# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""pin (a)(b) lifecycle probe -- legs L-D / L-D2 / L-E + bypass legs L-C3/L-C4/L-C5 (prereg v0.3.1 sec 5).

Runs TWO CONSECUTIVE EPISODES per cell on the UNPATCHED source path: the bundled recording-prepare
change makes ``_prepare_recording`` carry the pin witness, so ``route_c1_pin=True`` boots without the
g6 harness patch (g6_live_rollout_pin.py:53 documents the pre-bundle plumbing bug this replaces).
Episode 2 exists BECAUSE of (a)(b): pre-bundle, the fired weld and the witness survived the done-reset,
so a second episode re-counted episode 1's pin (pre-check Finding 1).

Legs (bars preregistered in PIN_AB_SCOPE_PREREG_RSTECHLEAD_20260717.md sec 5):
  L-D   ep1: fire + eq_active==1 + audit PASS -> done-reset: eq cleared + witness None -> ep2: re-fire
        at the same recording onset with a fresh witness + audit PASS.
  L-D2  ep1/ep2 event timeline (pin fire step / G first-latch steps / termination flags / done step)
        EXACT match = hard bar; the per-step reward trace diff is recorded and reported (two-key judges).
        Trajectory BYTE equality is NOT claimed (qacc_warmstart carries across reset by design).
  L-E   eq_active adjacency: across the done-reset, the symmetric diff outside the fired eq = empty.
  L-C3  outside-clip bypass write + witness None -> the reset audit RAISES BEFORE any clear (eq stays 1).
  L-C4  inside-clip bypass write + witness None -> audited then CLEARED (model-state authority: the
        witness gate cannot hide a bypass weld).
  L-C5  multi-candidate: (i) all-legit -> ALL cleared; (ii) count > n_authorized -> RAISE, none cleared;
        (iii) any outside -> RAISE, no partial clear.

Bypass writes use the authorize_clip_pin_controls.py:223 pattern (direct ``eq_data``/``eq_active``
writes); the aerial z=0.8809 / legit z=0.829 anchors are the control probe's proven RAISE/pass pair.

Run (cuda:0 pinned, CPU mujoco stepping; one cell per process):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_ab_lifecycle_probe.py \
        --cell cell_x0_y0 --bypass
"""

from __future__ import annotations

import argparse
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
assert _CVD == "0", f"lifecycle probe runs the as-coded substrate on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import route_env_config as rc  # noqa: E402
import route_executor as rex  # noqa: E402
import torch  # noqa: E402

GRID = _EVAL / "w0e_81rerun_snapdown_0537"
LEGIT_Z = 0.829  # control probe leg C: audit pass
AERIAL_Z = 0.8809  # control probe leg B: off-clip weld -> audit RAISE


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


def run_episode(env, label: str) -> dict:
    zero = torch.zeros((1, 6), dtype=torch.float32)
    mjd = env._solver.mj_data
    out = {
        "label": label,
        "fire_step": None,
        "eq_id": None,
        "eq_active_at_fire": None,
        "audit_at_fire": None,
        "witness_fired_at_frame": None,
        "g_first_latch": [None] * 6,
        "done_step": None,
        "term": None,
        "reward_sum": 0.0,
        "reward_trace": [],
        "post_reset_witness_none": None,
        "post_reset_eq_cleared": None,
        "adjacency_sym_diff_empty": None,
    }
    for t in range(env.MAX_EPISODE_STEPS + 1):
        eq_pre = np.asarray(mjd.eq_active).copy()  # state ENTERING step t (pre-reset at the done step)
        g_pre = np.asarray(env._g_latched[0]).copy()
        for gi in range(6):
            if out["g_first_latch"][gi] is None and bool(g_pre[gi]):
                out["g_first_latch"][gi] = t - 1  # latched during step t-1 (read pre-step: the done-step
                # reset wipes latches before a post-step read could see them; symmetric across episodes)
        _obs, rew, dones, extras = env.step(zero)
        r = float(rew[0])
        out["reward_trace"].append(r)
        out["reward_sum"] += r
        if out["fire_step"] is None and env._c1_pin_witness is not None:
            wit = env._c1_pin_witness
            out["fire_step"] = t
            out["eq_id"] = int(wit["eq_id"])
            out["eq_active_at_fire"] = int(mjd.eq_active[out["eq_id"]])
            out["witness_fired_at_frame"] = int(wit.get("fired_at_frame", -1))
            try:
                rex.audit_pin_anchors(env._solver.mj_model, mjd)
                out["audit_at_fire"] = "PASS"
            except AssertionError as e:
                out["audit_at_fire"] = f"RAISE {str(e)[:120]}"
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
            break
    return out


def run_bypass_legs(env) -> dict:
    """L-C3/C4/C5: direct eq writes (controls probe :223 pattern) against _clear_c1_pin([0])."""
    import mujoco

    mjm, mjd = env._solver.mj_model, env._solver.mj_data
    connect = int(mujoco.mjtEq.mjEQ_CONNECT)
    cands = [
        i
        for i in range(int(mjm.neq))
        if int(mjm.eq_type[i]) == connect and int(mjm.eq_obj2id[i]) == 0 and int(mjm.eq_active0[i]) == 0
    ]
    n_auth = len(rc.ROUTE_CLIP_CENTERS)
    assert n_auth >= 2 and len(cands) >= n_auth + 1, f"need >= {n_auth + 1} candidates, have {len(cands)}"
    (c1x, c1y) = rc.ROUTE_CLIP_CENTERS[0]
    (c2x, c2y) = rc.ROUTE_CLIP_CENTERS[1]
    k1, k2, k3 = cands[0], cands[1], cands[2]
    saved = {k: np.array(mjm.eq_data[k]).copy() for k in (k1, k2, k3)}
    legs = {"candidates": {"n_pin_eqs": len(cands), "n_auth": n_auth, "used": [k1, k2, k3]}}

    def set_pin(k, x, y, z):
        mjm.eq_data[k][0:3] = [0.0, 0.0, 0.0]
        mjm.eq_data[k][3:6] = [x, y, z]
        mjd.eq_active[k] = 1

    def restore():
        for k in (k1, k2, k3):
            mjd.eq_active[k] = 0
            mjm.eq_data[k][:] = saved[k]

    # L-C3: outside-clip bypass + witness None -> RAISE before clear.
    env._c1_pin_witness = None
    set_pin(k1, c1x, c1y, AERIAL_Z)
    try:
        env._clear_c1_pin([0])
        legs["C3"] = {"PASS": False, "got": "no raise"}
    except AssertionError as e:
        legs["C3"] = {"PASS": int(mjd.eq_active[k1]) == 1, "got": f"RAISE {str(e)[:100]}"}
    restore()

    # L-C4: inside-clip bypass + witness None -> audited then cleared.
    env._c1_pin_witness = None
    set_pin(k1, c1x, c1y, LEGIT_Z)
    try:
        env._clear_c1_pin([0])
        legs["C4"] = {"PASS": int(mjd.eq_active[k1]) == 0 and env._c1_pin_witness is None}
    except Exception as e:  # noqa: BLE001
        legs["C4"] = {"PASS": False, "got": f"RAISE {str(e)[:100]}"}
    restore()

    # L-C5 (i): one legit pin per authorized clip -> ALL cleared.
    set_pin(k1, c1x, c1y, LEGIT_Z)
    set_pin(k2, c2x, c2y, LEGIT_Z)
    try:
        env._clear_c1_pin([0])
        legs["C5_i"] = {"PASS": int(mjd.eq_active[k1]) == 0 and int(mjd.eq_active[k2]) == 0}
    except Exception as e:  # noqa: BLE001
        legs["C5_i"] = {"PASS": False, "got": f"RAISE {str(e)[:100]}"}
    restore()

    # L-C5 (ii): count > n_auth -> RAISE (double-pin guard), none cleared.
    set_pin(k1, c1x, c1y, LEGIT_Z)
    set_pin(k2, c2x, c2y, LEGIT_Z)
    set_pin(k3, c1x, c1y, LEGIT_Z)
    try:
        env._clear_c1_pin([0])
        legs["C5_ii"] = {"PASS": False, "got": "no raise"}
    except AssertionError as e:
        legs["C5_ii"] = {
            "PASS": all(int(mjd.eq_active[k]) == 1 for k in (k1, k2, k3)),
            "got": f"RAISE {str(e)[:100]}",
        }
    restore()

    # L-C5 (iii): one legit + one outside -> RAISE, NO partial clear.
    set_pin(k1, c1x, c1y, LEGIT_Z)
    set_pin(k2, c2x, c2y, AERIAL_Z)
    try:
        env._clear_c1_pin([0])
        legs["C5_iii"] = {"PASS": False, "got": "no raise"}
    except AssertionError as e:
        legs["C5_iii"] = {
            "PASS": int(mjd.eq_active[k1]) == 1 and int(mjd.eq_active[k2]) == 1,
            "got": f"RAISE {str(e)[:100]}",
        }
    restore()
    return legs


def run_trace(env, steps: int) -> dict:
    """L-F1/L-F2 instrument: fixed-length flag-OFF stepping with 4-channel per-step digests.

    Done-independent (steps THROUGH done-resets): the two trees under comparison may terminate
    episodes at different steps -- that is itself a channel. Per-step: physics (body_q bytes),
    obs bytes, reward, done. Divergence localization = first index where a channel differs.
    """
    import hashlib

    import warp as wp

    zero = torch.zeros((1, 6), dtype=torch.float32)
    phys_h, obs_h, rew, done_steps, term_at_done, obs_dump = [], [], [], [], [], []
    for t in range(steps):
        obs, r, dones, extras = env.step(zero)
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        obs_np = obs.cpu().numpy().ravel()
        obs_dump.append(obs_np.copy())  # full vectors: L-F2 per-index attribution vs the sec 11 surface
        phys_h.append(hashlib.sha256(bq.tobytes()).hexdigest()[:16])
        obs_h.append(hashlib.sha256(obs_np.tobytes()).hexdigest()[:16])
        rew.append(round(float(r[0]), 10))
        if bool(dones[0]):
            done_steps.append(t)
            term_at_done.append(_scalarize(extras))
    final = hashlib.sha256(
        ("".join(phys_h) + "".join(obs_h) + json.dumps(rew) + json.dumps(done_steps)).encode()
    ).hexdigest()
    return {"steps": steps, "phys": phys_h, "obs": obs_h, "reward": rew, "done_steps": done_steps,
            "term_at_done": term_at_done, "final_digest": final, "_obs_dump": obs_dump}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True, help="e.g. cell_x0_y0")
    ap.add_argument("--bypass", action="store_true", help="run L-C3/C4/C5 after the two episodes")
    ap.add_argument("--trace", type=int, default=0, help="L-F mode: run N fixed flag-OFF steps and dump digests")
    ap.add_argument("--tag", default="bundle", help="trace output tag (bundle | f1base | head)")
    args = ap.parse_args()
    npz = GRID / args.cell / "route_demo_raw.npz"
    assert npz.exists(), f"recording missing: {npz}"
    out_path = _EVAL / f"pin_ab_lifecycle_probe_result_{args.cell}.json"

    trace_mode = args.trace > 0
    print(f"[pin_ab] building route env (route_c1_pin={not trace_mode}, feedforward, cuda:0) recording={npz}")
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
            "route_c1_pin": not trace_mode,  # trace legs L-F1/L-F2 are flag-OFF by prereg
        },
    )
    env.INIT_XY_NOISE = 0.0  # L-D determinism pin (class default 0.005 would break the L-D2 timeline bar)
    env.reset()

    if trace_mode:
        tr = run_trace(env, args.trace)
        obs_dump = tr.pop("_obs_dump")
        tp = _EVAL / f"pin_ab_trace_{args.cell}_{args.tag}.json"
        tp.write_text(json.dumps(tr, indent=2))
        np.save(str(tp).replace(".json", "_obs.npy"), np.stack(obs_dump))
        print(f"[pin_ab] trace tag={args.tag} steps={tr['steps']} done_steps={tr['done_steps']} "
              f"term_at_done={tr['term_at_done']} final={tr['final_digest'][:16]} -> {tp}")
        return 0

    result = {"cell": args.cell, "unpatched_source_boot": True}  # reaching here = no g6-style patch needed
    ep1 = run_episode(env, "ep1")
    print(f"[pin_ab] ep1: fire={ep1['fire_step']} done={ep1['done_step']} audit={ep1['audit_at_fire']}")
    ep2 = run_episode(env, "ep2")
    print(f"[pin_ab] ep2: fire={ep2['fire_step']} done={ep2['done_step']} audit={ep2['audit_at_fire']}")

    trace1, trace2 = ep1.pop("reward_trace"), ep2.pop("reward_trace")
    n = min(len(trace1), len(trace2))
    reward_diff = [abs(a - b) for a, b in zip(trace1[:n], trace2[:n])]
    result["ep1"], result["ep2"] = ep1, ep2

    result["L_D"] = {
        "PASS": bool(
            ep1["fire_step"] is not None
            and ep1["eq_active_at_fire"] == 1
            and ep1["audit_at_fire"] == "PASS"
            and ep1["post_reset_eq_cleared"] is True
            and ep1["post_reset_witness_none"] is True
            and ep2["fire_step"] is not None
            and ep2["eq_active_at_fire"] == 1
            and ep2["audit_at_fire"] == "PASS"
            and ep2["post_reset_eq_cleared"] is True
            and ep2["post_reset_witness_none"] is True
        )
    }
    timeline_equal = (
        ep1["fire_step"] == ep2["fire_step"]
        and ep1["g_first_latch"] == ep2["g_first_latch"]
        and ep1["done_step"] == ep2["done_step"]
        and ep1["term"] == ep2["term"]
    )
    result["L_D2"] = {
        "PASS_hard_timeline": bool(timeline_equal),
        "reward_trace_len": [len(trace1), len(trace2)],
        "reward_max_abs_step_diff": max(reward_diff) if reward_diff else 0.0,
        "reward_sum_diff": abs(ep1["reward_sum"] - ep2["reward_sum"]),
    }
    result["L_E"] = {
        "PASS": bool(ep1["adjacency_sym_diff_empty"] and ep2["adjacency_sym_diff_empty"])
    }
    if args.bypass:
        result["bypass"] = run_bypass_legs(env)
        result["bypass"]["PASS_all"] = all(
            bool(result["bypass"][leg]["PASS"]) for leg in ("C3", "C4", "C5_i", "C5_ii", "C5_iii")
        )

    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("ep1", "ep2")}, indent=2))
    print(f"[pin_ab] L-D={result['L_D']['PASS']} L-D2(hard)={result['L_D2']['PASS_hard_timeline']} "
          f"L-E={result['L_E']['PASS']} -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
