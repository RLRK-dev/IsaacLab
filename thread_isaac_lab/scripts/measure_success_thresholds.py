#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Scripted grip test for C1-C5 threshold measurement.

Runs N=1 Newton env with scripted actions (descend -> close -> lift),
logging all SUCCESS condition values at each RL step.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/measure_success_thresholds.py --device cuda:1
"""

import argparse
import os
import sys

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)

from newton_approach_cable_env import (
    NewtonApproachCableEnv,
    EE_BODY_OFFSET,
    EE_TO_FINGERTIP,
    FRANKA_NUM_JOINTS,
)


def measure(env):
    """Compute C1-C5 condition values for world 0."""
    wp.synchronize()
    bq = env._state_0.body_q.numpy()
    w = 0
    ws = env._bws[w]

    # EE + fingertip position
    ee_pos = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
    fingertip_pos = ee_pos.copy()
    fingertip_pos[2] -= EE_TO_FINGERTIP

    # Cable positions + nearest body
    cable_pos = bq[env._cable_bodies[w], :3]
    dists_to_ft = np.linalg.norm(cable_pos - fingertip_pos, axis=1)
    nearest_idx = int(np.argmin(dists_to_ft))
    nearest_pos = cable_pos[nearest_idx]
    z_nearest = float(nearest_pos[2])

    # Finger opening
    fk_jq = env._per_world_fk_jq[w]
    finger_opening = float(fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8])

    # Fingertip-cable distance (same metric as C2 in reward function)
    dist_tip_cable = float(np.min(dists_to_ft))

    # Derived values
    cable_z_init = float(env._cable_z_init[w])
    cable_z_gain = max(0.0, z_nearest - cable_z_init)
    co_movement = abs(z_nearest - fingertip_pos[2])

    return {
        "finger_opening": finger_opening,
        "dtc": dist_tip_cable,
        "z_nearest": z_nearest,
        "fingertip_z": float(fingertip_pos[2]),
        "ee_xyz": ee_pos.copy(),
        "cable_nearest_xyz": nearest_pos.copy(),
        "cable_z_init": cable_z_init,
        "cable_z_gain": cable_z_gain,
        "co_movement": co_movement,
        "nearest_idx": nearest_idx,
        "c1": finger_opening < env.C1_FINGER_THRESH,
        "c2": dist_tip_cable < env.GRASP_DIST_THRESH,
        "c3": cable_z_gain > env.C3_LIFT_THRESH,
        "c4": co_movement < env.C4_COMOVEMENT_THRESH,
        "sustain": int(env._success_sustain_count[w]),
    }


def main():
    parser = argparse.ArgumentParser(description="Measure C1-C5 thresholds with scripted grip")
    parser.add_argument("--device", type=str, default="cuda:1")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    print("[MEASURE] Creating 1-world env...")
    env = NewtonApproachCableEnv(world_count=1, device=args.device)
    obs, _ = env.reset()

    # Print initial state
    m0 = measure(env)
    ee = m0["ee_xyz"]
    cn = m0["cable_nearest_xyz"]
    print(f"\n[MEASURE] Initial state:")
    print(f"  EE            = ({ee[0]:.4f}, {ee[1]:.4f}, {ee[2]:.4f})")
    print(f"  fingertip     = ({ee[0]:.4f}, {ee[1]:.4f}, {m0['fingertip_z']:.4f})")
    print(f"  cable_nearest = ({cn[0]:.4f}, {cn[1]:.4f}, {cn[2]:.4f}) idx={m0['nearest_idx']}")
    print(f"  cable_z_init  = {m0['cable_z_init']:.4f}")
    print(f"  finger_opening= {m0['finger_opening']:.4f}")
    print(f"  dtc          = {m0['dtc']:.4f}")

    # Compute approach direction: EE XY → cable nearest XY
    # ACTION_SCALE = 5mm, so action=1.0 → 5mm per step
    dx = cn[0] - ee[0]
    dy = cn[1] - ee[1]
    dist_xy = np.sqrt(dx * dx + dy * dy)
    approach_steps = max(1, int(np.ceil(dist_xy / env.ACTION_SCALE)))
    ax_norm = dx / (dist_xy + 1e-8)
    ay_norm = dy / (dist_xy + 1e-8)
    print(f"  XY offset     = ({dx * 1000:.1f}, {dy * 1000:.1f}) mm, "
          f"dist={dist_xy * 1000:.1f} mm → {approach_steps} approach steps")

    # Table header
    print(f"\n{'step':>4} {'phase':>8} {'f_open':>7} {'dtc':>7} {'z_gain':>7} "
          f"{'co_mv':>7} {'ft_z':>7} {'zn':>7} "
          f"{'C1':>3} {'C2':>3} {'C3':>3} {'C4':>3} {'sus':>3} {'rew':>7}")
    print("-" * 95)

    # Scripted phases
    # 1. Approach: move EE XY toward cable
    # 2. Descend: lower fingertip to cable Z
    # 3. Close: close fingers around cable
    # 4. Lift: raise while gripping
    phases = [
        ("approach", [ax_norm, ay_norm, 0, 0, 0, 0], approach_steps),
        ("descend",  [0, 0, -1, 0, 0, 0], 2),
        ("close",    [0, 0, 0, 1, 0, 0], 40),
        ("lift",     [0, 0, 1, 1, 0, 0], 50),
    ]

    step = 0
    for phase_name, action_list, n_steps in phases:
        action = torch.tensor([action_list], dtype=torch.float32, device=args.device)
        for _ in range(n_steps):
            obs, rewards, dones, extras = env.step(action)
            m = measure(env)
            step += 1
            rew = float(rewards[0])
            print(
                f"{step:4d} {phase_name:>8} "
                f"{m['finger_opening']:7.4f} {m['dtc']:7.4f} "
                f"{m['cable_z_gain']:7.4f} {m['co_movement']:7.4f} "
                f"{m['fingertip_z']:7.4f} {m['z_nearest']:7.4f} "
                f"{'T' if m['c1'] else '.':>3} {'T' if m['c2'] else '.':>3} "
                f"{'T' if m['c3'] else '.':>3} {'T' if m['c4'] else '.':>3} "
                f"{m['sustain']:3d} {rew:7.3f}"
            )
            if dones.any():
                print(f"\n[DONE at step {step} — SUCCESS achieved]")
                break
        else:
            continue
        break

    # Summary
    print(f"\n[MEASURE] === Threshold Analysis ===")
    print(f"  C1 threshold: {env.C1_FINGER_THRESH} (finger_opening)")
    print(f"  C2 threshold: {env.GRASP_DIST_THRESH} (dtc)")
    print(f"  C3 threshold: {env.C3_LIFT_THRESH} (cable_z_gain)")
    print(f"  C4 threshold: {env.C4_COMOVEMENT_THRESH} (co_movement)")
    print(f"  C5 threshold: {env.C5_SUSTAIN_STEPS} steps")
    print(f"\n  Final sustain count: {m['sustain']}")

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
