#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Handoff verification test for M3-AR precondition cache (F4).

Verifies that `build_ar_precondition` (from generate_demos_mppi_m3_ar) produces
a cache matching AR env's `_load_and_restore_cache` expectations. Detects FM-10
(scene topology mismatch) and FM-7 (cache format regression) before F5 smoke.

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs:thread_isaac_lab/envs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/test_m3_ar_handoff.py \\
        --world-count 4 --device cuda:1
"""

import argparse
import os
import sys

import numpy as np
import warp as wp

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "envs"))

from generate_demos_mppi_m3_ar import (
    CABLE_DROP_Z_THR,
    FINGERTIP_Z,
    build_ar_precondition,
)
from newton_skill_env_base import EE_BODY_OFFSET, FRANKA_NUM_JOINTS, load_precondition_cache
from task_config import GRASP_X, LIFT_Z, WIDE_LEFT_Y, WIDE_RIGHT_Y


def _check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}{':  ' + detail if detail else ''}")
    return condition


def main():
    parser = argparse.ArgumentParser(description="M3-AR precondition handoff verification (F4)")
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default="cuda:1")
    parser.add_argument("--tolerance-mm", type=float, default=20.0, help="EE pos tolerance [mm]")
    args = parser.parse_args()

    wp.init()
    wp.set_device(args.device)

    print(f"=== F4 Handoff Test: build + verify (w={args.world_count}, device={args.device}) ===")

    # Build precondition (this writes the cache).
    fk_model, fk_state, scene = build_ar_precondition(args.world_count, args.device)

    cache_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_aerial_regrasp_cache",
    )
    cache_path = os.path.join(cache_dir, f"aerial_regrasp_w{args.world_count}_p0_v2.npz")

    print("\n[F4] Cache file checks")
    if not _check("cache file exists", os.path.exists(cache_path), cache_path):
        print("[F4] ABORT: cache not created")
        sys.exit(1)

    data = load_precondition_cache(cache_path)
    checks = []

    # Required keys.
    required = {"body_q", "body_qd", "fk_jq", "inv_mass", "inv_inertia", "world_count", "body_count"}
    extras = {"left_ee_hold", "right_ee_start", "settled_grasp_x"}
    checks.append(_check("required keys present", required.issubset(data.keys()),
                         f"missing: {required - data.keys()}"))
    checks.append(_check("extra keys present (AR-specific)", extras.issubset(data.keys()),
                         f"missing: {extras - data.keys()}"))

    # Shape + count checks.
    wc = int(data["world_count"][0])
    bc = int(data["body_count"][0])
    checks.append(_check("world_count matches", wc == args.world_count, f"cache={wc}, expected={args.world_count}"))
    checks.append(_check("body_count > 0", bc > 0, f"body_count={bc}"))
    checks.append(_check("body_q shape consistent", data["body_q"].shape[0] == bc))

    # NaN/Inf checks.
    checks.append(_check("body_q finite", np.all(np.isfinite(data["body_q"].view(np.float32)))))
    checks.append(_check("body_qd finite", np.all(np.isfinite(data["body_qd"].view(np.float32)))))
    checks.append(_check("fk_jq finite", np.all(np.isfinite(data["fk_jq"]))))

    # EE pose checks (world 0).
    bws = scene["bws"]
    w0 = bws[0]
    body_q_flat = data["body_q"].view(np.float32).reshape(-1, 7)
    left_ee_pos = body_q_flat[w0 + EE_BODY_OFFSET, :3]
    right_ee_pos = body_q_flat[w0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, :3]

    expected_left = np.array([GRASP_X, WIDE_LEFT_Y, LIFT_Z], dtype=np.float32)
    expected_right = np.array([GRASP_X, WIDE_RIGHT_Y, LIFT_Z], dtype=np.float32)
    l_err_mm = float(np.linalg.norm(left_ee_pos - expected_left) * 1000)
    r_err_mm = float(np.linalg.norm(right_ee_pos - expected_right) * 1000)

    print("\n[F4] EE pose checks (world 0)")
    print(f"  L EE pos: {left_ee_pos}  expected {expected_left}  err={l_err_mm:.1f}mm")
    print(f"  R EE pos: {right_ee_pos}  expected {expected_right}  err={r_err_mm:.1f}mm")
    checks.append(_check(f"L EE within {args.tolerance_mm}mm", l_err_mm < args.tolerance_mm))
    checks.append(_check(f"R EE within {args.tolerance_mm}mm", r_err_mm < args.tolerance_mm))

    # Extra keys cross-check.
    cache_left_hold = data["left_ee_hold"]
    cache_right_start = data["right_ee_start"]
    dl_mm = float(np.linalg.norm(left_ee_pos - cache_left_hold) * 1000)
    dr_mm = float(np.linalg.norm(right_ee_pos - cache_right_start) * 1000)
    checks.append(_check("left_ee_hold matches body_q L EE", dl_mm < 1.0, f"{dl_mm:.2f}mm"))
    checks.append(_check("right_ee_start matches body_q R EE", dr_mm < 1.0, f"{dr_mm:.2f}mm"))

    # Cable validity: L-exclusive segs above drop threshold; FINGERTIP_Z region populated.
    print("\n[F4] Cable state checks (world 0)")
    cable_indices = scene["cable_bodies"][0]
    cable_z = body_q_flat[cable_indices, 2]
    cable_z_min = float(cable_z.min())
    cable_z_max = float(cable_z.max())
    cable_z_mean = float(cable_z.mean())
    print(f"  cable_z: min={cable_z_min:.4f}m, max={cable_z_max:.4f}m, mean={cable_z_mean:.4f}m")
    checks.append(_check("cable min z > drop threshold (fallback)", cable_z_min > CABLE_DROP_Z_THR - 0.050,
                         f"min={cable_z_min:.4f}, thr-50mm={CABLE_DROP_Z_THR - 0.050:.4f}"))
    near_fingertip = int(np.sum(np.abs(cable_z - FINGERTIP_Z) < 0.050))
    checks.append(_check(f"cable near fingertip_z=LIFT-EE2FT ({FINGERTIP_Z:.3f}m) +-50mm", near_fingertip >= 2,
                         f"{near_fingertip} segs"))

    # settled_grasp_x sanity.
    sgx = float(data["settled_grasp_x"][0])
    sgx_err_mm = abs(sgx - GRASP_X) * 1000
    checks.append(_check("settled_grasp_x within 30mm of GRASP_X",
                         sgx_err_mm < 30.0, f"sgx={sgx:.4f}m, expected={GRASP_X}, err={sgx_err_mm:.1f}mm"))

    # Summary.
    n_pass = sum(1 for c in checks if c)
    n_total = len(checks)
    print(f"\n[F4] Result: {n_pass}/{n_total} checks passed")
    if n_pass == n_total:
        print("[F4] ALL PASS -- precondition handoff verified")
        sys.exit(0)
    else:
        print("[F4] FAIL -- inspect cache build / scene topology")
        sys.exit(1)


if __name__ == "__main__":
    main()
