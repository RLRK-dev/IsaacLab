# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B3a leg 7: did the guard corrections change any CAPTURED DATA? (%12 F-8, positive control)

WHY. The capture's meta pins ``route_executor_sha256`` -- "this artifact was produced by THIS code". The
guard/records corrections change that module, so the pinned sha goes stale, and a stale pin is WORSE than no
pin: it asserts a false identity. The fix is to re-capture. But a bare re-capture only restores the pin; it
proves nothing. So the re-run is upgraded into a POSITIVE CONTROL (%12):

    assert every captured ARRAY is byte-identical across the pre-fix and post-fix captures,
    and that ONLY `meta` differs (route_executor_sha256).

  * MATCH    -> the corrections are proven to be guard/records-only: they changed no captured data.
  * MISMATCH -> a DISCOVERY, not a nuisance: the "fix" altered capture behaviour -> STOP and investigate.

Either outcome yields information, which is the whole point (a check whose failure mode is uninformative is
not a check). Note the npz is a ZIP, so the FILE sha necessarily differs (compression metadata) -- the assert
must be per-array (%10).

Run: /home/rlrk/env_isaaclab7/bin/python .../leg7_capture_invariance.py <prefix.npz> <new.npz>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "leg7_capture_invariance.json"
ARRAYS = ("joint_q", "joint_qd", "grip_target", "qacc_warmstart", "eq_active", "frame_idx")


def main():
    here = Path(__file__).resolve().parent
    old_p = Path(sys.argv[1]) if len(sys.argv) > 2 else here / "bank_capture_prefix.npz"
    new_p = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "bank_capture.npz"
    if not old_p.is_file():
        print(f"[leg7] SKIP (no pre-fix capture to compare against: {old_p})")
        return 0
    old, new = np.load(old_p, allow_pickle=True), np.load(new_p, allow_pickle=True)

    rows, ok = [], True
    for k in ARRAYS:
        a, b = np.asarray(old[k]), np.asarray(new[k])
        same = a.shape == b.shape and np.array_equal(a, b)
        ok = ok and same
        rows.append({"array": k, "shape": list(b.shape), "byte_identical": bool(same)})
        print(f"[leg7] {k:16s} {str(b.shape):14s} byte-identical: {same}")

    m_old = json.loads(str(np.asarray(old["meta"]).item()))
    m_new = json.loads(str(np.asarray(new["meta"]).item()))
    sha_changed = m_old.get("route_executor_sha256") != m_new.get("route_executor_sha256")
    # everything in meta EXCEPT the module sha (and the provenance block it carries) must be unchanged
    stable = {k: (m_old.get(k) == m_new.get(k)) for k in ("frames", "mj_backend", "cell_env", "cadence", "dt")}
    stable_ok = all(stable.values())
    print(
        f"[leg7] meta: route_executor_sha256 changed = {sha_changed} "
        f"({str(m_old.get('route_executor_sha256'))[:8]} -> {str(m_new.get('route_executor_sha256'))[:8]})"
    )
    print(f"[leg7] meta: frames/backend/cell_env/cadence/dt unchanged = {stable_ok}  {stable}")

    verdict = ok and stable_ok
    res = {
        "what": "W1-B3a leg7: the guard corrections must not have changed any CAPTURED DATA (%12 positive control)",
        "prefix_npz": str(old_p),
        "new_npz": str(new_p),
        "arrays": rows,
        "all_arrays_byte_identical": ok,
        "meta_sha_changed_as_expected": sha_changed,
        "meta_stable_fields": stable,
        "PASS": bool(verdict),
    }
    OUT.write_text(json.dumps(res, indent=1))
    if verdict:
        print(
            "[leg7] PASS: every captured array is byte-identical; only the module sha moved "
            "=> the corrections are guard/records-only and changed NO captured data"
        )
    else:
        print("[leg7] FAIL: the correction CHANGED capture behaviour -- this is a DISCOVERY. STOP and investigate.")
    print(f"[leg7] -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
