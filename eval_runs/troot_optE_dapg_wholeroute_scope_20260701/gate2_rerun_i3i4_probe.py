# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Gate-2 I3/I4 probe: canonical divergence-0 + routed-side positive control (81-cell) + new-guard escape.

Runs AGAINST the post-I3/I4 code. Legs pre-registered in GATE2_I3I4_IMPL_RSTECHLEAD_20260717.md:

  A. canonical anchors vs the banked v2 result (gate2_rerun_fm34_probe_v2_result.json), EXACT:
     c1 first-seated 2428 / pre-onset seated 116 / post-onset 5163/5163 / c2 first 7394 / 313/313 /
     c2 max dx 3.183mm. Equality here IS the per-frame divergence-0 leg: v2 ran the pre-fix instrument.
  B. new escape guard (identity-instrument dx), window pre-registered = post-onset (f >= 2544): 0 frames.
     (Pre-onset with latched=True forced would read MISS -> True by design; the live guard is latch-gated,
     so an all-frames count is not a valid leg -- [VERIFY] CC2 finding 2.)
  C. 81-cell positive control (ROUTE_C2_SIDE_FROM_PIN == -1 grounding; drift = loud): per cell, with that
     cell's OWN seat_k (route_c2_pin.json route_c2_freeze_scope), count feed-side (seg >= seat_k) C2Y
     straddles over ALL frames. Zero everywhere => the side restriction removes no candidate that ever
     straddles C2Y => the I4 instrument is BYTE-EQUAL to pre-fix on all 81 recorded cells (proof, not
     sample), and the routed side is < seat_k on every cell.
  D. obs[49]/[58]/[59] inheritance declaration: I4 propagates through _seat_metrics(active C2) into these
     dims (instrument attribute, ruling sec 11 auto-follow precedent). Canonical divergence 0 follows from
     leg A + leg C; declared here for the p5 delta verify surface ([VERIFY] CC2 finding 4).
  E. evidence closure (pN HOLD B3): git HEAD + per-file git status + sha256 of the sys.modules-derived
     source closure (probe + every loaded thread_isaac_lab file), sha256 manifest of all 81-cell inputs
     (route_demo_raw.npz + route_c2_pin.json) with an aggregate digest, and a pre/post run bracket over
     the source closure (changed must be [] -- fail-loud).

Usage: probe.py [--grid DIR] [--out FILE]. The grid inputs are git-untracked recorded data; the manifest
pins them by content hash. For an exact-landed run, execute from a clean worktree checkout and pass
--grid pointing at the recorded data directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TIL = _HERE.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL / "envs"), str(_TIL)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import newton_route_env as nre  # noqa: E402
import route_env_config as rc  # noqa: E402

DEFAULT_GRID = _HERE / "w0e_81rerun_snapdown_0537"
DEFAULT_OUT = _HERE / "gate2_rerun_i3i4_probe_result.json"

# Banked v2 anchors (gate2_rerun_fm34_probe_v2_result.json) -- leg A expected values, EXACT.
V2 = {
    "n_frames": 7707,
    "pin_onset_frame": 2544,
    "c1_first_seated_frame_ANY": 2428,
    "c1_pre_onset_seated_frames": 116,
    "c1_seated_post_onset": "5163/5163",
    "c2_first_seated_frame": 7394,
    "c2_seated_after_first": "313/313",
    "c2_max_dx_mm_while_seated_PER_FRAME": 3.183,
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _source_closure() -> dict[str, str]:
    """sha256 of this probe + every loaded thread_isaac_lab source (sys.modules-derived, not hand-listed)."""
    files = {Path(__file__).resolve()}
    for mod in list(sys.modules.values()):
        f = getattr(mod, "__file__", None)
        if f and "thread_isaac_lab" in f:
            files.add(Path(f).resolve())
    return {str(p): _sha256(p) for p in sorted(files)}


def _git_provenance(closure: dict[str, str]) -> dict:
    root = subprocess.run(
        ["git", "-C", str(_HERE), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip()
    head = subprocess.run(
        ["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-C", root, "status", "--porcelain", "--", *closure.keys()],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return {"git_root": root, "git_head": head, "closure_git_status_porcelain": status}


def leg_a_b_canonical(grid: Path):
    d = np.load(grid / "cell_x0_y0/route_demo_raw.npz")
    cable = d["cable_xyz"].astype(np.float64)
    n = cable.shape[0]
    onset = int(np.argmax(d["pin_active"].astype(int) == 1))
    env = object.__new__(nre.NewtonRouteEnv)
    env._pin_seat_seg = 27

    c1_seated = np.zeros(n, dtype=bool)
    c2_seated = np.zeros(n, dtype=bool)
    c2_dx = np.full(n, np.nan)
    esc = np.zeros(n, dtype=bool)
    for f in range(n):
        cp = cable[f]
        dx1, z1 = env._seat_metrics(cp, nre._C1_XY)
        c1_seated[f] = env._seated_in_groove(dx1, z1)
        dx2, z2 = env._seat_metrics(cp, nre._C2_XY)
        c2_seated[f] = env._seated_in_groove(dx2, z2)
        c2_dx[f] = dx2
        esc[f] = env._c1_escape_after_seat(dx1, True)  # new guard: identity dx

    first_c1 = int(np.argmax(c1_seated)) if c1_seated.any() else None
    first_c2 = int(np.argmax(c2_seated)) if c2_seated.any() else None
    got = {
        "n_frames": int(n),
        "pin_onset_frame": onset,
        "c1_first_seated_frame_ANY": first_c1,
        "c1_pre_onset_seated_frames": int(c1_seated[:onset].sum()),
        "c1_seated_post_onset": f"{int(c1_seated[onset:].sum())}/{n - onset}",
        "c2_first_seated_frame": first_c2,
        "c2_seated_after_first": (
            f"{int(c2_seated[first_c2:].sum())}/{n - first_c2}" if first_c2 is not None else None
        ),
        "c2_max_dx_mm_while_seated_PER_FRAME": (
            round(float(np.nanmax(c2_dx[c2_seated])) * 1000, 3) if c2_seated.any() else None
        ),
    }
    diffs = {k: (V2[k], got[k]) for k in V2 if got[k] != V2[k]}
    escape_post_onset = int(esc[onset:].sum())
    return got, diffs, escape_post_onset


def leg_c_grid(grid: Path):
    per_cell = {}
    manifest = {}
    for pin_json in sorted(grid.glob("cell_*/route_c2_pin.json")):
        cell = pin_json.parent.name
        npz = pin_json.parent / "route_demo_raw.npz"
        manifest[cell] = {"route_demo_raw.npz": _sha256(npz), "route_c2_pin.json": _sha256(pin_json)}
        fs = json.loads(pin_json.read_text())["route_c2_freeze_scope"]
        seat_k = int(fs["seat_k"])
        cable = np.load(npz)["cable_xyz"].astype(np.float64)
        ys = cable[:, :, 1]
        c2y = float(nre._C2_XY[1])
        y0 = ys[:, :-1]
        y1 = ys[:, 1:]
        strad = ((y0 - c2y) * (y1 - c2y) <= 0.0) & (y0 != y1)  # [frames, segs]
        feed = int(strad[:, seat_k:].sum())
        per_cell[cell] = {"seat_k": seat_k, "feed_side_straddle_frames_x_segs": feed}
    total_feed = sum(v["feed_side_straddle_frames_x_segs"] for v in per_cell.values())
    seat_k_hist: dict[int, int] = {}
    for v in per_cell.values():
        seat_k_hist[v["seat_k"]] = seat_k_hist.get(v["seat_k"], 0) + 1
    agg = hashlib.sha256(
        "".join(
            f"{c}:{m['route_demo_raw.npz']}:{m['route_c2_pin.json']};" for c, m in sorted(manifest.items())
        ).encode()
    ).hexdigest()
    return per_cell, total_feed, seat_k_hist, manifest, agg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=Path, default=DEFAULT_GRID)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    closure_pre = _source_closure()
    provenance = _git_provenance(closure_pre)

    got, diffs, escape_post_onset = leg_a_b_canonical(args.grid)
    per_cell, total_feed, seat_k_hist, manifest, agg = leg_c_grid(args.grid)

    closure_post = _source_closure()
    changed = sorted(
        set(k for k in closure_pre if closure_pre[k] != closure_post.get(k)) | set(closure_post) - set(closure_pre)
    )
    leg_a_pass = not diffs
    leg_b_pass = escape_post_onset == 0
    leg_c_pass = total_feed == 0 and int(rc.ROUTE_C2_SIDE_FROM_PIN) == -1
    leg_e_pass = changed == []
    out = {
        "ts": time.time(),
        "code_under_test": "post-I3/I4 (escape reads identity dx; C2 walk routed-side-restricted)",
        "route_c2_side_from_pin": int(rc.ROUTE_C2_SIDE_FROM_PIN),
        "provenance": provenance,
        "source_closure_sha256": closure_pre,
        "leg_A_canonical_anchor_equality": {"PASS": leg_a_pass, "got": got, "symmetric_diff": diffs},
        "leg_B_new_guard_escape_post_onset": {
            "PASS": leg_b_pass,
            "frames": escape_post_onset,
            "window": "f >= onset 2544 (pre-registered)",
        },
        "leg_C_81cell_positive_control": {
            "PASS": leg_c_pass,
            "cells": len(per_cell),
            "total_feed_side_straddles": total_feed,
            "seat_k_histogram": {str(k): v for k, v in sorted(seat_k_hist.items())},
            "note": "zero feed-side straddles => I4 restriction removes nothing on any recorded cell "
            "=> per-frame instrument equality on all 81 cells (proof); routed side < seat_k everywhere",
        },
        "leg_D_obs_inheritance_declaration": "I4 propagates into obs[49]/[58]/[59] via _seat_metrics"
        " (active clip = C2 post-G4); canonical divergence 0 by legs A+C; RATIFIED by ruling sec S3.5"
        " item 1 (inheritance is required by the same-instrument principle)",
        "leg_E_evidence_closure": {
            "PASS": leg_e_pass,
            "pre_post_source_bracket_changed": changed,
            "input_manifest_aggregate_sha256": agg,
            "input_manifest_sha256": manifest,
        },
        "ALL_PASS": bool(leg_a_pass and leg_b_pass and leg_c_pass and leg_e_pass),
    }
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    summary = {k: v for k, v in out.items() if k not in ("leg_E_evidence_closure", "source_closure_sha256")}
    summary["leg_E_evidence_closure"] = {
        "PASS": leg_e_pass,
        "pre_post_source_bracket_changed": changed,
        "input_manifest_aggregate_sha256": agg,
        "input_manifest": f"{len(manifest)} cells x 2 files, full map in the json",
    }
    print(json.dumps(summary, indent=1))
    return 0 if out["ALL_PASS"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
