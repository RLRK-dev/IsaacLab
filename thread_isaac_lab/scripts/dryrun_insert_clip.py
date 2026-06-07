#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""InsertIntoClip dry-run: scripted descent to verify IK reachability + physical feasibility.

Steps:
  1. Load InsertIntoClip env (precondition: cable at LIFT_Z above clip)
  2. Scripted descent: EE from LIFT_Z → PUSH_Z (95mm over ~63 RL steps)
  3. Hold at PUSH_Z for settle
  4. Check success conditions (seated pos/ori + groove bodies)
  5. Report waypoints + (obs, action) pairs for wet-run demo collection

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    python thread_isaac_lab/scripts/dryrun_insert_clip.py --device cuda:0
"""

import argparse
import math
import os
import sys
import time

import numpy as np
import torch
import warp as wp

# Import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "envs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))

from newton_insert_clip_env import NewtonInsertClipEnv
from task_config import (
    LIFT_Z, PUSH_Z, GRASP_X, CLIP1_X, CLIP1_Y, CLIP1_Z,
    TABLE_HEIGHT, CLIP_BASE_HEIGHT, CABLE_RADIUS, EE_TO_FINGERTIP,
    GRIP_HALF_SPAN, T_GROOVE, T_SEAT, K_INSERT, GROOVE_BODIES_MIN,
    CLIP_GROOVE_INNER_RADIUS, CABLE_SEG_LEN,
)


GROOVE_CHECK_RADIUS = CABLE_SEG_LEN + CABLE_RADIUS  # 19mm (matches env)
GROOVE_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS  # 0.809m


def check_groove_state(env, label=""):
    """Check cable state relative to clip groove. Returns metrics dict."""
    wp.synchronize()
    bq = env._state_0.body_q.numpy()
    results = []

    for w in range(env._world_count):
        cb = env._cable_bodies[w]
        cable_pos = bq[cb, :3]
        cable_z = cable_pos[:, 2]

        # Bodies in groove (XY < 10mm and Z near groove)
        dists_xy = np.linalg.norm(cable_pos[:, :2] - np.array([CLIP1_X, CLIP1_Y]), axis=1)
        z_near = np.abs(cable_z - GROOVE_Z) < 0.015
        in_groove = int(np.sum((dists_xy < GROOVE_CHECK_RADIUS) & z_near))

        # Nearest segment to clip
        dists_3d = np.linalg.norm(cable_pos - np.array([CLIP1_X, CLIP1_Y, CLIP1_Z]), axis=1)
        nearest_idx = np.argmin(dists_3d)
        nearest_dist = float(dists_3d[nearest_idx])

        results.append({
            "world": w,
            "cable_z_min": float(cable_z.min()),
            "cable_z_max": float(cable_z.max()),
            "cable_z_mean": float(cable_z.mean()),
            "in_groove": in_groove,
            "nearest_dist_mm": nearest_dist * 1000,
        })

    if label:
        print(f"\n  [{label}]")
    for r in results:
        print(f"    W{r['world']}: z=[{r['cable_z_min']:.4f},{r['cable_z_max']:.4f}] "
              f"groove={r['in_groove']} nearest={r['nearest_dist_mm']:.1f}mm")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--world-count", type=int, default=4)
    args = parser.parse_args()

    device = args.device
    world_count = args.world_count

    print(f"=== InsertIntoClip Dry-Run ===")
    print(f"  Device: {device}, Worlds: {world_count}")
    print(f"  LIFT_Z={LIFT_Z}, PUSH_Z={PUSH_Z}, GROOVE_Z={GROOVE_Z:.3f}")
    print(f"  Descent: {(LIFT_Z - PUSH_Z)*1000:.0f}mm EE, "
          f"fingertip {LIFT_Z - EE_TO_FINGERTIP:.3f} → {PUSH_Z - EE_TO_FINGERTIP:.3f}")

    # --- Phase 1: Construct env ---
    print("\n[Phase 1] Constructing env...")
    env = NewtonInsertClipEnv(world_count=world_count, device=device)
    obs, info = env.reset()
    print(f"  obs shape: {obs.shape}, reward range check...")

    check_groove_state(env, "INITIAL (LIFT_Z)")

    # --- Phase 2: Scripted descent ---
    # Action: 12D = [L_dx, L_dy, L_dz, L_ax, L_ay, L_az, R_dx, R_dy, R_dz, R_ax, R_ay, R_az]
    # POS_ACTION_SCALE = 0.015m per unit. Descent = 95mm. Steps = 95/15 ≈ 6.3 units.
    # But we don't want to descend in 1 step. Use small -Z increments.
    #
    # Strategy: pure -Z descent, no XY/rotation change.
    # descent_per_step = -1.5mm (action_z = -0.1 * POS_ACTION_SCALE → -1.5mm per step)
    # Total steps to descend 95mm: 95 / 1.5 ≈ 63 steps

    # Overshoot by 10mm past PUSH_Z to ensure cable reaches groove (GROOVE_Z=0.809)
    descent_target_z = PUSH_Z - 0.010  # 1.015m (fingertip → 0.795, 14mm below groove)
    descent_total = LIFT_Z - descent_target_z  # 0.105m
    action_z_unit = -0.1  # conservative: 1.5mm per step
    step_descent = abs(action_z_unit) * env.POS_ACTION_SCALE  # 0.0015m
    n_descent_steps = int(math.ceil(descent_total / step_descent))

    print(f"\n[Phase 2] Scripted descent: {n_descent_steps} steps × {step_descent*1000:.1f}mm = {n_descent_steps * step_descent * 1000:.0f}mm")
    print(f"  Target EE Z: {descent_target_z:.3f} (fingertip {descent_target_z - EE_TO_FINGERTIP:.3f}, "
          f"groove {GROOVE_Z:.3f})")

    # Collect trajectory
    obs_list = [obs.cpu().numpy()]
    act_list = []
    rew_list = []

    descent_action = torch.zeros(world_count, 12, device=device)
    # Both arms descend equally in Z
    descent_action[:, 2] = action_z_unit   # L_dz
    descent_action[:, 8] = action_z_unit   # R_dz

    for step_i in range(n_descent_steps):
        obs_i, rew_i, done_i, extras_i = env.step(descent_action)
        act_list.append(descent_action[0].cpu().numpy())
        obs_list.append(obs_i.cpu().numpy())
        rew_list.append(rew_i.cpu().numpy())

        if step_i % 20 == 0 or step_i == n_descent_steps - 1:
            print(f"  step {step_i+1}/{n_descent_steps}: rew={rew_i[0].item():.4f} "
                  f"ep_len={env.episode_length_buf[0].item()}")

        # Check for done (drop or success)
        if done_i.any().item():
            print(f"  Done at step {step_i+1}: done={done_i.tolist()}")
            break

    check_groove_state(env, f"AFTER DESCENT ({step_i+1} steps)")

    # --- Phase 3: Hold at PUSH_Z ---
    print(f"\n[Phase 3] Hold at PUSH_Z for 50 steps...")
    hold_action = torch.zeros(world_count, 12, device=device)
    for step_i in range(50):
        obs_i, rew_i, done_i, extras_i = env.step(hold_action)
        act_list.append(hold_action[0].cpu().numpy())
        obs_list.append(obs_i.cpu().numpy())
        rew_list.append(rew_i.cpu().numpy())

        if step_i == 49:
            print(f"  step {step_i+1}: rew={rew_i[0].item():.4f}")

        if done_i.any().item():
            print(f"  Done at hold step {step_i+1}: done={done_i.tolist()}")
            break

    results = check_groove_state(env, "AFTER HOLD")

    # --- Phase 4: Summary ---
    print(f"\n=== DRY-RUN SUMMARY ===")
    total_steps = len(act_list)
    print(f"  Total RL steps: {total_steps}")
    print(f"  Trajectory: obs[{len(obs_list)}x{obs_list[0].shape}], act[{len(act_list)}x12]")

    all_pass = True
    for r in results:
        passed = r["in_groove"] >= GROOVE_BODIES_MIN
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  World {r['world']}: groove_bodies={r['in_groove']} "
              f"(need≥{GROOVE_BODIES_MIN}) nearest={r['nearest_dist_mm']:.1f}mm → {status}")

    if all_pass:
        print(f"\n  ✓ ALL WORLDS PASS: cable reached groove")
    else:
        print(f"\n  ✗ SOME WORLDS FAILED: cable did not reach groove")

    # Detailed groove segment diagnostics
    print(f"\n=== GROOVE SEGMENT DETAIL (World 0) ===")
    wp.synchronize()
    bq_final = env._state_0.body_q.numpy()
    cb0 = env._cable_bodies[0]
    groove_segs = env._groove_seg_indices[0]
    print(f"  groove_seg_indices: {groove_segs}")
    print(f"  CLIP1: ({CLIP1_X}, {CLIP1_Y}, {CLIP1_Z}), GROOVE_Z: {GROOVE_Z:.3f}")
    print(f"  GROOVE_CHECK_RADIUS: {GROOVE_CHECK_RADIUS*1000:.0f}mm, Z_window: ±15mm")
    for si in range(max(0, groove_segs[0]-3), min(len(cb0), groove_segs[-1]+4)):
        bi = cb0[si]
        pos = bq_final[bi, :3]
        dist_xy = np.linalg.norm(pos[:2] - np.array([CLIP1_X, CLIP1_Y]))
        dist_z = abs(pos[2] - GROOVE_Z)
        in_xy = dist_xy < GROOVE_CHECK_RADIUS
        in_z = dist_z < 0.015
        in_groove = in_xy and in_z
        marker = "★" if in_groove else " "
        print(f"  {marker} seg {si:2d}: pos=({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}) "
              f"dXY={dist_xy*1000:.1f}mm dZ={dist_z*1000:.1f}mm {'IN' if in_groove else '--'}")

    # Save waypoints
    waypoints_dir = os.path.join(os.path.dirname(__file__), "..", "data", "waypoints")
    os.makedirs(waypoints_dir, exist_ok=True)
    waypoints_path = os.path.join(waypoints_dir, "insert_clip_c1_dryrun.npz")
    np.savez(
        waypoints_path,
        obs=np.array(obs_list),
        actions=np.array(act_list),
        rewards=np.concatenate(rew_list) if rew_list else np.array([]),
    )
    print(f"  Saved: {waypoints_path}")


if __name__ == "__main__":
    main()
