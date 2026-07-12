# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B1 leg 6 (R-4 / CC6-condition, %9+%10 converged): flag-OFF route_t == episode_length_buf THROUGH
the real per-world done-reset path.

The mirror value-identity was empirically backed on exercised paths (legs 1-5), but every env leg ran
world_count=1, so the per-world reset mirror site (newton_route_env _reset_worlds) was never exercised
with a SUBSET of worlds -- exactly the done-mid-run hole CC6 flagged. This leg: 2 worlds, flag-OFF
(default cfg), inject an invariant-preserving near-timeout state into world 0 ONLY, step through the REAL
step() done branch (timeout -> _reset_worlds([0]) -> consumer-6 re-fork), and assert route_t equals
episode_length_buf element-wise at every step before/through/after.

Run: CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
    eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b1_dod_legs/leg6_route_t_mirror.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "0", "leg6 runs on cuda:0 (route canonical)"

import newton_route_env as nre  # noqa: E402
import torch  # noqa: E402

OUT = Path(__file__).resolve().parent / "leg6_route_t_mirror.json"


def main():
    env = nre.NewtonRouteEnv(world_count=2, device="cuda:0")  # default cfg: flag-OFF, stub route
    env.reset()
    zero = torch.zeros((2, 6), dtype=torch.float32)
    checks = []

    def snap(tag):
        eq = bool(torch.equal(env.route_t, env.episode_length_buf))
        rec = {
            "tag": tag,
            "route_t": env.route_t.tolist(),
            "episode": env.episode_length_buf.tolist(),
            "equal": eq,
        }
        checks.append(rec)
        print(f"[leg6] {tag}: route_t={rec['route_t']} episode={rec['episode']} equal={eq}")
        return eq

    ok = snap("post-reset")
    for _ in range(3):
        env.step(zero)
        ok = snap("pre-inject step") and ok

    # invariant-preserving injection: world 0 ONLY is put 1 step short of timeout (both clocks together,
    # so the invariant is not broken by the injection itself -- the test proves it SURVIVES the branch).
    env.episode_length_buf[0] = env.max_episode_length - 1
    env.route_t[0] = env.max_episode_length - 1
    ok = snap("post-inject") and ok

    _, _, dones, _ = env.step(zero)
    done0, done1 = bool(dones[0]), bool(dones[1])
    print(f"[leg6] timeout step: dones={[done0, done1]} (expect [True, False] = per-world branch fired)")
    ok = snap("post-done-reset (world 0 reset via REAL step() branch + consumer-6)") and ok

    for _ in range(3):
        env.step(zero)
        ok = snap("post-reset step") and ok

    branch_fired = done0 and not done1
    w0_restarted = checks[-1]["episode"][0] < checks[-1]["episode"][1]  # w0 re-counts from 0; w1 kept running
    verdict = ok and branch_fired and w0_restarted
    result = {
        "what": "W1-B1 leg6 (R-4/CC6): flag-OFF route_t == episode_length_buf through per-world done-reset",
        "world_count": 2,
        "mirror_equal_all_snapshots": ok,
        "per_world_done_branch_fired": branch_fired,
        "world0_restarted_world1_continued": w0_restarted,
        "snapshots": checks,
        "PASS": verdict,
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(f"[leg6] {'PASS' if verdict else 'FAIL'} -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
