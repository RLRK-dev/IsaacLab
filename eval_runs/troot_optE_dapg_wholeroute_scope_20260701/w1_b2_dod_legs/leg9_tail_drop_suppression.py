# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B2 leg 9 (R13b, %10 audit F-1c): tail (iv) post-release drop suppression -- 3 predicates measured.

  A (suppress):   flag ON, route_t >= release boundary, drop condition true -> NO terminal + event count.
  B (S5 preserve): flag ON, route_t PRE-release, same drop condition -> legacy terminal (-10, done).
  C (flag OFF):    same condition -> legacy terminal (byte-preserve semantics).

Injection is invariant-preserving (leg6/7 precedent): G1+G2 latches set true, so the held-z drop clause
(g_latched[w,1] and held_z < rest+margin) fires NATURALLY on the at-rest cable -- no physics faked; the
contact-loss counter path is NOT used (the reward pass zeroes an injected counter before the predicate).

Run: CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
    eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b2_dod_legs/leg9_tail_drop_suppression.py
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

assert os.environ.get("CUDA_VISIBLE_DEVICES") == "0", "leg9 runs on cuda:0 (route canonical)"

import torch  # noqa: E402

import newton_route_env as nre  # noqa: E402

GOLDEN = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = Path(__file__).resolve().parent / "leg9_tail_drop_suppression.json"
_BASE_CFG = {
    "grasp_actuation": True,
    "route_executor_impl": "route_executor",
    "route_recording_npz": str(GOLDEN),
    "g1_scene_align": True,
    "route_drive_mode": "feedforward",
    "route_c2_scene": True,
}


def _arm_drop(env, w=0):
    """G1+G2 latch injection: the held-z clause fires naturally on the at-rest cable."""
    env._g_latched[w, 0] = True
    env._g_latched[w, 1] = True


def main():
    zero = torch.zeros((1, 6), dtype=torch.float32)
    res = {}

    env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg=dict(_BASE_CFG, route_t_clock=True))
    rls = int(env._route_release_step)
    res["release_step"] = rls

    # --- A: post-release -> suppressed (no terminal) + event ---
    env.reset()
    _arm_drop(env)
    env.route_t[0] = rls  # at/after the scheduled release boundary
    _, rew, dones, _ = env.step(zero)
    res["A_post_release"] = {
        "done": bool(dones[0]),
        "reward": float(rew[0]),
        "suppressed_count": int(env._suppressed_drop_count[0]),
    }
    a_ok = (not res["A_post_release"]["done"]) and res["A_post_release"]["suppressed_count"] == 1

    # --- B: pre-release (same condition) -> legacy terminal (S5 preserved) ---
    env.reset()
    _arm_drop(env)
    env.route_t[0] = 100
    _, rew, dones, _ = env.step(zero)
    res["B_pre_release"] = {"done": bool(dones[0]), "reward": float(rew[0])}
    b_ok = res["B_pre_release"]["done"] and res["B_pre_release"]["reward"] == -10.0

    # --- C: flag OFF (same condition, same nominal timing) -> legacy terminal ---
    env2 = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg=dict(_BASE_CFG))  # route_t_clock default OFF
    env2.reset()
    _arm_drop(env2)
    env2.episode_length_buf[0] = rls  # mirror-invariant injection (flag OFF: both clocks together)
    env2.route_t[0] = rls
    _, rew, dones, _ = env2.step(zero)
    res["C_flag_off"] = {"done": bool(dones[0]), "reward": float(rew[0])}
    c_ok = res["C_flag_off"]["done"] and res["C_flag_off"]["reward"] == -10.0

    verdict = a_ok and b_ok and c_ok
    res.update({"A_ok": a_ok, "B_ok": b_ok, "C_ok": c_ok, "PASS": verdict})
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[leg9] release_step={rls} A(post,suppress)={res['A_post_release']} B(pre,S5)={res['B_pre_release']} C(off)={res['C_flag_off']}")
    print(f"[leg9] {'PASS' if verdict else 'FAIL'} -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
