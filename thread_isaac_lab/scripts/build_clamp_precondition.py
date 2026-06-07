#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build Clamp P0 precondition cache.

Creates the initial state for the Clamp env:
  - Cable settled on table with support clips
  - Both arms IK-solved to cable-proximal position (fingertip at cable center)
  - Both fingers OPEN
  - VBD settled with arms in place

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/build_clamp_precondition.py \
        --world-count 4 --device cuda:0
"""

import argparse
import os
import sys
import time

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "configs"))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "envs"))


def main():
    parser = argparse.ArgumentParser(description="Build Clamp P0 cache")
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default=os.environ.get("NEWTON_DEVICE", "auto"))
    args = parser.parse_args()

    from gpu_utils import resolve_device
    args.device = resolve_device(args.device)
    os.environ["NEWTON_DEVICE"] = args.device

    print(f"[BUILD-CLAMP-P0] Device: {args.device}, worlds: {args.world_count}")
    t0 = time.perf_counter()

    # Import env (triggers scene build + P0 construction + cache save)
    from newton_clamp_env import NewtonClampEnv

    env = NewtonClampEnv(world_count=args.world_count, device=args.device)

    # Verify cache was saved
    cache_path = env._cache_path()
    if os.path.exists(cache_path):
        size_mb = os.path.getsize(cache_path) / (1024 * 1024)
        print(f"[BUILD-CLAMP-P0] Cache: {cache_path} ({size_mb:.1f} MB)")
    else:
        print(f"[BUILD-CLAMP-P0] WARNING: Cache not found at {cache_path}")

    # Quick sanity: run one step
    obs, _ = env.reset()
    print(f"[BUILD-CLAMP-P0] Obs shape: {obs.shape}")
    print(f"[BUILD-CLAMP-P0] Finger R (obs[7]): {obs[0, 7].item()*1000:.1f}mm")
    print(f"[BUILD-CLAMP-P0] Finger L (obs[15]): {obs[0, 15].item()*1000:.1f}mm")
    print(f"[BUILD-CLAMP-P0] Pos error R: {obs[0, 33:36].cpu().numpy()*1000} mm")
    print(f"[BUILD-CLAMP-P0] Pos error L: {obs[0, 39:42].cpu().numpy()*1000} mm")

    print(f"[BUILD-CLAMP-P0] Done in {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    main()
