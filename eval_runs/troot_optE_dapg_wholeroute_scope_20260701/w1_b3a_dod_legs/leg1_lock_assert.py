# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B3a leg 1: Rs-LOCK assert -- ``run_route`` is byte-identical to HEAD (ZERO lines changed).

The route_executor twin carries its own lock banner (route_executor.py, above ``def run_route``):
"ANTI-REVERT / Rs-LOCKED -- do NOT edit any line of run_route without Rs", with the ANTI-REVERT marker
lines living inside the function. The P3 demo recorder's ctor/finalize sit INSIDE that span, so mirroring
the recorder pattern for the B3a bank capture would have required editing a locked function. The capture
was therefore placed entirely in ``physics_step`` (outside the lock) + an atexit finalize.

This leg proves the claim mechanically instead of by inspection: it extracts the ``run_route`` source from
git HEAD and from the working tree and compares them byte-for-byte.

Run: /home/rlrk/env_isaaclab7/bin/python eval_runs/.../w1_b3a_dod_legs/leg1_lock_assert.py [--base <rev>]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent
_REPO = _EVAL.parent.parent
SRC = "thread_isaac_lab/envs/route_executor.py"
OUT = Path(__file__).resolve().parent / "leg1_lock_assert.json"
LOCKED_FNS = ("run_route",)


def _extract(src: str, name: str) -> str:
    """The full source of a top-level ``def name(...)`` block (up to the next top-level def/class)."""
    lines = src.splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines) if ln.startswith(f"def {name}(")]
    if not starts:
        raise AssertionError(f"top-level 'def {name}(' not found")
    s = starts[0]
    e = next(
        (i for i in range(s + 1, len(lines)) if lines[i].startswith("def ") or lines[i].startswith("class ")),
        len(lines),
    )
    return "".join(lines[s:e])


def main():
    base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "HEAD"
    head_src = subprocess.run(
        ["git", "-C", str(_REPO), "show", f"{base}:{SRC}"], capture_output=True, text=True, check=True
    ).stdout
    work_src = (_REPO / SRC).read_text()
    res = {"base": base, "file": SRC, "functions": {}}
    ok = True
    for fn in LOCKED_FNS:
        a, b = _extract(head_src, fn), _extract(work_src, fn)
        same = a == b
        res["functions"][fn] = {
            "head_lines": a.count("\n"),
            "work_lines": b.count("\n"),
            "head_sha256": hashlib.sha256(a.encode()).hexdigest(),
            "work_sha256": hashlib.sha256(b.encode()).hexdigest(),
            "byte_identical": same,
        }
        ok = ok and same
        print(f"[leg1] {fn}: {'BYTE-IDENTICAL' if same else 'CHANGED'} vs {base} ({b.count(chr(10))} lines)")
    res["PASS"] = ok
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[leg1] {'PASS' if ok else 'FAIL'} (Rs-LOCKED span untouched) -> {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
