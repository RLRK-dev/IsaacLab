# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""S4b reset-scoping audit (Option-E S4b) -- read-only scan, no mutation.

Asserts ZERO unguarded ``body_q_prev`` call-forms on the mujoco reset path: the SC3 audit
(``sc3_body_q_prev_guard_audit.py``) covered the STANDALONE ``.assign`` sites and exempted the 17
reset-coupled B sites as the S4 TODO; this audit closes that TODO. Every ``body_q_prev.numpy()``
READ must be hasattr-CONDITIONAL on the same line (the S4b guard form:
``prev = solver.body_q_prev.numpy() if hasattr(solver, "body_q_prev") else None``) and every
``body_q_prev.assign(`` must sit under a ``hasattr`` or ``prev is not None`` guard within the
preceding 3 lines. Under SolverMuJoCo (no ``body_q_prev`` -- a VBD-only previous-position buffer)
the reads yield ``None`` and the writes are skipped; the reset is carried by joint_q seeding
(``derive_cable_joint_q_from_tangents`` + ``seed_cable_joint_state``, C-1 primary). Run:
    ./isaaclab.sh -p thread_isaac_lab/scripts/s4b_reset_scoping_audit.py
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
_ASSIGN = re.compile(r"body_q_prev\.assign\(")
_NUMPY = re.compile(r"body_q_prev\.numpy\(")
_GUARD = re.compile(r"hasattr\([^)]*body_q_prev|prev is not None")


def main() -> int:
    fail = 0
    reads_ok: list[str] = []
    assigns_ok: list[str] = []
    for rel in FILES:
        path = os.path.join(_REPO, rel)
        with open(path) as _fh:
            lines = _fh.read().splitlines()
        for i, ln in enumerate(lines):
            if _NUMPY.search(ln):
                # guard forms: same-line conditional expression, or an enclosing
                # ``if hasattr(...body_q_prev...)`` block opened within the preceding 3 lines
                ctx = "\n".join(lines[max(0, i - 3): i])
                if "hasattr" in ln or _GUARD.search(ctx):
                    reads_ok.append(f"{rel}:{i + 1}")
                else:
                    print(f"FAIL: UNCONDITIONAL body_q_prev.numpy() read at {rel}:{i + 1}")
                    fail = 1
            if _ASSIGN.search(ln):
                ctx = "\n".join(lines[max(0, i - 3): i])
                if _GUARD.search(ctx):
                    assigns_ok.append(f"{rel}:{i + 1}")
                else:
                    print(f"FAIL: UNGUARDED body_q_prev.assign at {rel}:{i + 1}")
                    fail = 1

    print("--- S4b reset-scoping audit (base + 6 envs + script) ---")
    print(f"hasattr-CONDITIONAL .numpy() reads: {len(reads_ok)}")
    print(f"guarded .assign sites: {len(assigns_ok)}")
    print("mujoco reset path: ZERO unguarded body_q_prev call-forms" if not fail else "REGRESSION present")
    print("S4B_RESET_SCOPING_AUDIT=" + ("PASS" if not fail else "FAIL"))
    return fail


if __name__ == "__main__":
    sys.exit(main())
