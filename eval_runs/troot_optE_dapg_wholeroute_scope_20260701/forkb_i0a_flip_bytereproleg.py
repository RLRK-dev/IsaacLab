# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B I0-a flip no-change proof -- a post-flip n1 workload must reproduce the PRE-flip banked traj sha.

The R5-1 flip changed only the world_count DEFAULT (4 -> 1); every live caller passes wc=1 explicitly, so the
live path must be byte-identical. Proof: rerun the E0v2a n1 child workload (same seed form SS([base,0,0]),
same recording, same 230 steps) and compare the trajectory .npy file sha256 against the E0v2a n1_a banked
value -- a byte-level pre/post-flip comparison at ~3 min instead of the hours-scale 81-grid (which remains
available at the verifier's call). The golden npz sha is also re-checked (static provenance leg).

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_i0a_flip_bytereproleg.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
OUT = _EVAL / "forkb_i0a_flip_bytereproleg_result.json"
RUNDIR = _EVAL / "forkb_i0a_flipleg_runs"

_spec = importlib.util.spec_from_file_location("e0v2a", _EVAL / "forkb_e0v2a_scaling.py")
e0v2a = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e0v2a)
d0cal = e0v2a.d0cal


def main():
    if "--child" in sys.argv:
        i = int(sys.argv[sys.argv.index("--child") + 1])
        e0v2a.E0DIR = RUNDIR  # redirect the child output away from the E0v2a artifacts
        sys.exit(e0v2a.child(i, sys.argv[sys.argv.index("--child") + 2]))

    _CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    assert _CVD == "0", f"flip leg runs on cuda:0 ONLY; got {_CVD!r}"
    banked = json.loads((_EVAL / "forkb_e0v2a_scaling_result.json").read_text())
    ref_sha = banked["phases"]["n1_a"]["final"][0]["traj_sha256"]
    ref_rec = banked["phases"]["n1_a"]["prov"][0]["recording_sha256"]

    rec_now = d0cal._sha256_file(d0cal.GOLDEN_NPZ)
    RUNDIR.mkdir(exist_ok=True)
    p = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--child", "0", "postflip_n1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    st_f = RUNDIR / "postflip_n1" / "proc_0" / "status.json"
    st = json.loads(st_f.read_text()) if st_f.exists() else {}
    got_sha = st.get("traj_sha256")
    r = {
        "MARK": "I0-a flip no-change proof (post-flip n1 vs the PRE-flip E0v2a banked n1_a)",
        "flip": "newton_route_env.py world_count default 4 -> 1 "
                "(this run passes wc=1 explicitly, as all live callers do)",
        "reference_traj_sha_preflip_banked": ref_sha,
        "postflip_traj_sha": got_sha,
        "byte_identical": bool(got_sha and got_sha == ref_sha),
        "recording_sha_now": rec_now,
        "recording_sha_banked": ref_rec,
        "recording_unchanged": rec_now == ref_rec,
        "child_rc": p.returncode,
        "note_full_grid": "the 81-cell test_routeexec_byte_repro harness remains available at the verifier's call",
    }
    ok = r["byte_identical"] and r["recording_unchanged"] and p.returncode == 0
    if not ok:
        r["FAIL_LOUD"] = [
            "post-flip traj sha != pre-flip banked" if not r["byte_identical"] else "",
            "recording changed" if not r["recording_unchanged"] else "",
            f"child rc {p.returncode}" if p.returncode != 0 else "",
        ]
        r["FAIL_LOUD"] = [e for e in r["FAIL_LOUD"] if e]
    OUT.write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
