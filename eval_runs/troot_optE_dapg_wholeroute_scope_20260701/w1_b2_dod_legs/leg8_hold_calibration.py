# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B2 leg 8: HOLD calibration -- hold-quiet-pre-onset + hold-fires-at-onset (charter B2 row DoD).

One 499-step residual==0 replay on the comp5-faithful env cfg (feedforward + route_c2_scene +
g1_scene_align -- the exact runner class the banked t343 bar was measured on), flag ON, cuda:0
(W-2 device pin: the f343+-1 bar is cuda:0-trace-specific).

Bars (CC4-1 corrected index reading -- spec :88 f-numbers are RL-STEP indices; %12+%9 double-key EXACT):
  quiet: zero HOLD fires over the armed healthy domain t in [g1_latch, 336] (+ g1 latch must occur).
  fires: SHADOW series (comp5-compatible: FIXED seg24 vs rec frame 10t+3) first >15mm crossing at
         t 343+-1 (%12 ask-B2 ruling: the shadow series carries the bar, apples-to-apples with the
         n=1 comp5 ground truth); the ALIGNED series (held-seg @ 10t+9, the actual HOLD metric) is
         recorded + attributed (systematic re-alignment budget ~0.6-0.7 step, %9 N-2: 6/10 x local ramp).
  zero dones over the leg (CC6-F4: a mid-leg done would silently contaminate the governs-data).

Run: CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
    eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b2_dod_legs/leg8_hold_calibration.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent
_REPO = _EVAL.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# W-2 device pin, IN-SCRIPT (CC4-8: a wrapper-only pin lets a direct invocation run off-device).
assert os.environ.get("CUDA_VISIBLE_DEVICES") == "0", "leg8 runs on cuda:0 (W-2 pin; charter B2 row)"

import numpy as np  # noqa: E402
import torch  # noqa: E402

import newton_route_env as nre  # noqa: E402

GOLDEN = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = Path(__file__).resolve().parent / "leg8_hold_calibration.json"
N_STEPS = 499
QUIET_END = 336  # healthy-domain end [RL steps] (spec :88; comp5 max 10.56mm over t<=336)
FIRE_BAR = (342, 344)  # t343 +- 1 chunk (charter B2 row; 1 chunk == 1 RL step)


def main():
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
            "route_t_clock": True,  # W1-B2: the machinery under test
        },
    )
    rec_cable = np.load(str(GOLDEN), allow_pickle=True)["cable_xyz"]
    env.reset()
    zero = torch.zeros((1, 6), dtype=torch.float32)
    ex = env._route
    rows = []
    g1_latch_t = None
    for i in range(N_STEPS):
        t_pre = int(env.route_t[0].item())
        _, _, dones, _ = env.step(zero)
        bq = env._state_0.body_q.numpy()
        cable = bq[env._cable_bodies[0], :3]
        f_sh = min(10 * t_pre + 3, rec_cable.shape[0] - 1)
        shadow = float(np.linalg.norm(cable[24] - rec_cable[f_sh, 24]) * 1000.0)
        armed = bool(env._g_latched[0, 0])  # post-reward-pass latch (sync uses it from the NEXT step)
        if g1_latch_t is None and armed:
            g1_latch_t = i
        d = float(ex._div_last[0])
        rows.append(
            {
                "i": i,
                "route_t_pre": t_pre,
                "div_aligned_mm": round(d, 3) if np.isfinite(d) else None,
                "shadow_seg24_t3_mm": round(shadow, 3),
                "mode": "HOLD" if bool(ex._sync_hold[0]) else "MARCH",
                "hold_count": int(ex._hold_count[0]),
                "armed": armed,
                "done": bool(dones[0]),
            }
        )

    # --- verdicts ---------------------------------------------------------------------------------------
    fires = [r["i"] for j, r in enumerate(rows) if r["mode"] == "HOLD" and (j == 0 or rows[j - 1]["mode"] == "MARCH")]
    dones_seen = [r["i"] for r in rows if r["done"]]
    g1_ok = g1_latch_t is not None and g1_latch_t <= QUIET_END
    quiet_ok = g1_ok and all(f > QUIET_END for f in fires)
    # shadow bar discharge (ask-B2 ruling, correctly formulated): the shadow series is comp5-comparable
    # ONLY on the pre-freeze prefix -- a CORRECT aligned HOLD fires ~0.6 step BEFORE the shadow crossing
    # (its reference leads by 6 frames), so the live crossing is COUNTERFACTUAL in a flag-ON run. The
    # apples-to-apples bar is therefore: (i) live shadow prefix == the BANKED comp5 div_seg24 series
    # (EXACT -> build reproduces the n=1 ground-truth trajectory), (ii) the BANKED series' first >15mm
    # crossing sits in the bar, (iii) the aligned fire is attributed within the re-alignment budget.
    import subprocess

    r = subprocess.run(
        ["git", "-C", str(_REPO), "show",
         "311f18cb9b:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp5_c2seat_fullfire_cablediag.npz"],
        capture_output=True,
    )
    _tmp = Path("/tmp/claude-1000/leg8_banked_cablediag.npz")
    _tmp.write_bytes(r.stdout)
    banked = np.load(_tmp)["div_seg24_mm"]
    prefix = np.array([r_["shadow_seg24_t3_mm"] for r_ in rows if r_["route_t_pre"] == r_["i"]])
    prefix_max_diff = float(np.abs(prefix - banked[: len(prefix)]).max()) if len(prefix) else float("inf")
    prefix_exact = prefix_max_diff <= 1e-6
    banked_cross = int(np.argmax(banked > 15.0))
    shadow_cross_live = next(
        (r_["i"] for r_ in rows if r_["route_t_pre"] == r_["i"] and r_["shadow_seg24_t3_mm"] > 15.0), None
    )  # None EXPECTED when the aligned HOLD correctly preempts the crossing
    shadow_ok = prefix_exact and FIRE_BAR[0] <= banked_cross <= FIRE_BAR[1]
    first_fire = fires[0] if fires else None
    attribution = None
    if first_fire is not None:
        attribution = {
            "delta_steps_vs_banked_cross": first_fire - banked_cross,
            "within_budget": abs(first_fire - banked_cross) <= 2,
        }
    fire_in_bar = first_fire is not None and FIRE_BAR[0] <= first_fire <= FIRE_BAR[1]
    dones_ok = len(dones_seen) == 0
    armed_quiet_max = max(
        (r_["div_aligned_mm"] or 0.0 for r_ in rows if r_["armed"] and r_["route_t_pre"] <= QUIET_END),
        default=None,
    )
    crossing_detail = [r_ for r_ in rows if abs(r_["i"] - (first_fire or -10)) <= 1]
    verdict = bool(quiet_ok and shadow_ok and fire_in_bar and dones_ok)
    result = {
        "what": "W1-B2 leg8 HOLD calibration (quiet + fires; shadow bar per %12 ask-B2 ruling)",
        "cfg": "comp5-faithful (feedforward, route_c2_scene, g1_scene_align) + route_t_clock=True, cuda:0",
        "g1_latch_t": g1_latch_t,
        "fires": fires,
        "first_fire_t": first_fire,
        "first_fire_in_bar": fire_in_bar,
        "shadow_prefix_vs_banked_max_diff_mm": prefix_max_diff,
        "shadow_prefix_exact": prefix_exact,
        "shadow_prefix_len": int(len(prefix)),
        "banked_comp5_crossing_t": banked_cross,
        "shadow_live_crossing_t": shadow_cross_live,
        "shadow_live_crossing_note": (
            "None is EXPECTED: the aligned HOLD (reference 6 frames ahead) correctly preempts the shadow "
            "crossing by ~1 step -- the bar is discharged via prefix==banked EXACT + banked crossing in-bar"
        ),
        "fire_bar": list(FIRE_BAR),
        "attribution_aligned_fire": attribution,
        "quiet_zero_fires_armed_domain": quiet_ok,
        "armed_quiet_max_aligned_mm": armed_quiet_max,
        "dones_seen": dones_seen,
        "staleness_budget_note": (
            "aligned ref (10t+9, held-seg) leads shadow (10t+3, seg24) by 6 frames = 0.6 step; at the "
            "measured local ramp ~1.0-1.2 mm/step the systematic offset is ~0.6-0.7 mm (~0.6 step) -- "
            "%9 N-2 derivation, pinned here (discrimination floor of the +-1-chunk bar)"
        ),
        "recovery_note": (
            "residual==0 -> no recovery mechanism exists (spec :89); hold_count series here is "
            "drift-under-HOLD data only. MAX_HOLD re-derivation = B7 bounded-delta-injection leg (CC2-2)."
        ),
        "rows": rows,
        "PASS": verdict,
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(
        f"[leg8] g1_latch_t={g1_latch_t} fires={fires[:5]}{'...' if len(fires) > 5 else ''} "
        f"aligned_first_fire={first_fire} (bar {FIRE_BAR}) | shadow prefix vs banked: "
        f"max_diff={prefix_max_diff:.6f}mm over {len(prefix)} steps, banked_cross={banked_cross} "
        f"| attribution={attribution} dones={dones_seen} quiet_max={armed_quiet_max}"
    )
    print(f"[leg8] crossing detail: {crossing_detail}")
    print(f"[leg8] {'PASS' if verdict else 'FAIL'} -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
