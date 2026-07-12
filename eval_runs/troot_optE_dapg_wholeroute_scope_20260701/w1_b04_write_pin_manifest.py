# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1 B0-4: write the pinned flag-OFF byte-preserve baseline manifest (29-cell union).

Collects the per-cell npz sha256 from the w1_b04_baseline mod outputs, verifies each equals the banked
golden (w0e_81rerun_snapdown_0537), and pins the two-layer baseline (charter B0-4 + %12 conditions 14:26):
  - per-chunk layer  = 5 cells (canonical x0_y0 + DR corners x±20_y±20) — every chunk's flag-OFF subset
  - gate-iii layer   = 25 cells (w1_b04_gateiii_25set.json membership) — B7 final flag-OFF leg, with the
    B7 set-equality re-derivation assert (condition b)
Union = 29 unique cells (x-20_y-20 is in both layers). Records the derivation script + membership json
sha256 (condition a), the route_executor.py sha256, and the HEAD commit at pin time.

Run (CPU): /home/rlrk/env_isaaclab7/bin/python \
    eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b04_write_pin_manifest.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
_REPO = _EVAL.parent.parent
BASELINE = _EVAL / "w1_b04_baseline"
GOLDEN = _EVAL / "w0e_81rerun_snapdown_0537"
MEMBERSHIP = _EVAL / "w1_b04_gateiii_25set.json"
DERIVE_SCRIPT = _EVAL / "w1_b04_derive_gateiii_25set.py"
OUT = _EVAL / "w1_b04_pin_manifest.json"

PER_CHUNK_5 = ["x0_y0", "x-20_y-20", "x-20_y20", "x20_y-20", "x20_y20"]


def sha256_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    gateiii = json.loads(MEMBERSHIP.read_text())["gateiii_25set"]
    union = sorted(set(PER_CHUNK_5) | set(gateiii))
    cells = {}
    fails = []
    for tag in union:
        mod = sha256_file(BASELINE / "mod" / f"cell_{tag}" / "route_demo_raw.npz")
        gold = sha256_file(GOLDEN / f"cell_{tag}" / "route_demo_raw.npz")
        ok = mod is not None and mod == gold
        cells[tag] = {"npz_sha256": mod, "golden_match": ok}
        if not ok:
            fails.append(tag)

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_REPO, capture_output=True, text=True).stdout.strip()
    manifest = {
        "what": "W1 pinned flag-OFF byte-preserve baseline (charter B0-4, pre-B1 anchor)",
        "layers": {
            "per_chunk_5": PER_CHUNK_5,
            "gateiii_25": gateiii,
            "union_count": len(union),
        },
        "cells": cells,
        "all_golden_match": not fails,
        "fails": fails,
        "provenance": {
            "head_at_pin": head,
            "route_executor_py_sha256": sha256_file(_REPO / "thread_isaac_lab" / "envs" / "route_executor.py"),
            "derive_script_sha256": sha256_file(DERIVE_SCRIPT),
            "membership_json_sha256": sha256_file(MEMBERSHIP),
            "golden_dir": str(GOLDEN.name),
            "runs": ["w1_b04_baseline_run.log (5-cell + ref self-check x0_y0)", "w1_b04_baseline_run2.log (24-cell)"],
        },
        "b7_condition_b": (
            "B7 gate-iii leg re-derives the 25-set from the then-current predicate and asserts SET-EQUALITY "
            "vs layers.gateiii_25; mismatch = loud STOP"
        ),
        "usage": (
            "per-chunk flag-OFF leg: rerun byte-repro on per_chunk_5, compare npz sha256 to cells[tag].npz_sha256 "
            "(== golden). B7 final leg: same over gateiii_25 + the condition-b set-equality assert."
        ),
    }
    OUT.write_text(json.dumps(manifest, indent=1))
    print(json.dumps({"union_count": len(union), "all_golden_match": not fails, "fails": fails}, indent=1))
    print(f"-> {OUT}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
