# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B2 leg 7 (R3k env path, CC6-F3): per-world HOLD-state clear isolation through the REAL done-reset.

The executor-level neighbor isolation is unit-covered (test_clear_neighbor_isolation); this leg covers the
ENV wiring: world 1 times out through the real step() done branch -> _reset_worlds([1]) must clear ONLY
world 1's sync state/counters while world 0's survive byte-intact (a blanket clear here would silently
flip other held worlds to MARCH -- the FORK-1 failure HOLD exists to prevent).

Injection is invariant-preserving (leg6 precedent): world 0 gets nonzero PER-EPISODE COUNTERS (only
clear_sync_state may zero them -- update_sync never does), world 1 is put one step short of timeout.

Run: CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
    eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b2_dod_legs/leg7_hold_reset_isolation.py
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

assert os.environ.get("CUDA_VISIBLE_DEVICES") == "0", "leg7 runs on cuda:0 (route canonical)"

import torch  # noqa: E402

import newton_route_env as nre  # noqa: E402

GOLDEN = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = Path(__file__).resolve().parent / "leg7_hold_reset_isolation.json"


def main():
    env = nre.NewtonRouteEnv(
        world_count=2,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
            "route_t_clock": True,
        },
    )
    env.reset()
    ex = env._route
    zero = torch.zeros((2, 6), dtype=torch.float32)
    # invariant-preserving injection: per-episode counters only clear_sync_state may zero.
    ex._hold_fire_count[0], ex._chatter_count[0], ex._resume_count[0] = 7, 3, 2
    ex._hold_fire_count[1] = 5
    env.episode_length_buf[1] = env.max_episode_length - 1

    _, _, dones, _ = env.step(zero)
    d0, d1 = bool(dones[0]), bool(dones[1])
    w0_intact = (
        int(ex._hold_fire_count[0]) == 7 and int(ex._chatter_count[0]) == 3 and int(ex._resume_count[0]) == 2
    )
    w1_cleared = int(ex._hold_fire_count[1]) == 0
    env.step(zero)  # both worlds keep stepping fine post-reset
    verdict = (not d0) and d1 and w0_intact and w1_cleared
    result = {
        "what": "W1-B2 leg7 (R3k/CC6-F3): world-sliced HOLD clear through the REAL done-reset path",
        "dones": [d0, d1],
        "w0_counters_after": [int(ex._hold_fire_count[0]), int(ex._chatter_count[0]), int(ex._resume_count[0])],
        "w1_fire_count_after": int(ex._hold_fire_count[1]),
        "w0_intact": w0_intact,
        "w1_cleared": w1_cleared,
        "PASS": verdict,
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(f"[leg7] dones={[d0, d1]} w0_intact={w0_intact} w1_cleared={w1_cleared}")
    print(f"[leg7] {'PASS' if verdict else 'FAIL'} -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
