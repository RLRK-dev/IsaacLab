# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""SC3 body_q_prev capability-guard audit (Option-E Opt-1) -- read-only scan, no mutation.

Asserts that every STANDALONE ``solver.body_q_prev.assign(`` site (base + 6 envs + the standalone
script) is hasattr-guarded -- the SolverMuJoCo-has-no-body_q_prev capability guard, VBD-byte-identical.

A/B test (matches %12's SC3 adjudication, substance-based): a body_q_prev block is **reset-coupled
(B, S4-deferred)** iff its enclosing ``def`` also contains a ``body_q_prev.numpy()`` READ (the
read-modify-write reset/finger-support path that S4 ports to joint_q-seeding). Those B sites -- the
10 ``.numpy`` reads + their paired write-back ``.assign`` -- are EXEMPT here and listed as the S4 TODO.
Every OTHER (standalone) ``.assign`` MUST be guarded, else this is a regression -> exit 1.

This is a Python scan (not the bash grep of ``s2b_section5_6_audit.sh``) because the A/B split is
``def``-membership-based, which is far more robust than line-anchored grep (line numbers drift). Run:
    ./isaaclab.sh -p thread_isaac_lab/scripts/sc3_body_q_prev_guard_audit.py
"""

from __future__ import annotations

import os
import re
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FILES = [
    "thread_isaac_lab/envs/newton_skill_env_base.py",
    "thread_isaac_lab/envs/newton_approach_cable_env.py",
    "thread_isaac_lab/envs/newton_insert_clip_env.py",
    "thread_isaac_lab/envs/newton_unclamp_env.py",
    "thread_isaac_lab/envs/newton_grip_env.py",
    "thread_isaac_lab/envs/newton_clamp_env.py",
    "thread_isaac_lab/envs/newton_aerial_regrasp_env.py",
    "thread_isaac_lab/scripts/test_newton_clip_routing.py",
]
_DEF = re.compile(r"^(\s*)def (\w+)\(")
_ASSIGN = re.compile(r"body_q_prev\.assign\(")
_NUMPY = re.compile(r"body_q_prev\.numpy\(")
_GUARD = re.compile(r"hasattr\([^)]*body_q_prev")


def _enclosing_def(defs: list[dict], i: int) -> dict | None:
    """The method whose ``def`` is the last one starting at or before line ``i`` (methods don't nest)."""
    found = None
    for d in defs:
        if d["start"] <= i:
            found = d
        else:
            break
    return found


def main() -> int:
    fail = 0
    guarded: list[str] = []
    exempt_assign: list[str] = []
    numpy_reads: list[str] = []
    for rel in FILES:
        path = os.path.join(_REPO, rel)
        with open(path) as _fh:
            lines = _fh.read().splitlines()
        defs = [
            {"start": i, "name": m.group(2), "has_numpy": False} for i, ln in enumerate(lines) if (m := _DEF.match(ln))
        ]
        for i, ln in enumerate(lines):
            if _NUMPY.search(ln):
                d = _enclosing_def(defs, i)
                if d:
                    d["has_numpy"] = True
                numpy_reads.append(f"{rel}:{i + 1} (def {d['name'] if d else '?'})")
        for i, ln in enumerate(lines):
            if not _ASSIGN.search(ln):
                continue
            d = _enclosing_def(defs, i)
            if d and d["has_numpy"]:
                exempt_assign.append(f"{rel}:{i + 1} (def {d['name']})")
                continue
            ctx = "\n".join(lines[max(0, i - 2) : i])
            if _GUARD.search(ctx):
                guarded.append(f"{rel}:{i + 1}")
            else:
                print(f"FAIL: UNGUARDED standalone body_q_prev.assign at {rel}:{i + 1} (def {d['name'] if d else '?'})")
                fail = 1

    total = len(guarded) + len(exempt_assign) + len(numpy_reads)
    print("--- SC3 body_q_prev guard audit (base + 6 envs + script) ---")
    print(f"GUARDED standalone .assign: {len(guarded)} (expect 16 = 15 SC3-A + script:1 %13/P5)")
    print(f"EXEMPT-B paired-write .assign (S4 reset-path): {len(exempt_assign)}")
    print(f"B .numpy() reads (S4 reset-path): {len(numpy_reads)}")
    print(f"TOTAL = {len(guarded) + len(exempt_assign)} .assign + {len(numpy_reads)} .numpy = {total} call-forms")
    print("S4 DELIVERABLE (the 17 reset-coupled body_q_prev sites -> joint_q seeding + consumer-handle):")
    for e in exempt_assign + numpy_reads:
        print(f"  TODO-S4: {e}")
    print("SC3_BODY_Q_PREV_AUDIT=" + ("PASS" if not fail else "FAIL"))
    return fail


if __name__ == "__main__":
    sys.exit(main())
