#!/usr/bin/env python3
"""AR Cable Retention Feasibility Test.

Determines whether VBD physics supports stable cable holding by the left arm
in the AerialRegrasp environment.

Test 1 (zero-action): Both arms zero actions for 200 steps.
  - If cable drops → VBD physics fundamentally can't hold cable stably.
Test 2 (right-arm approach): Right arm slowly approaches cable target,
  left arm zero actions. 200 steps.
  - If cable drops → approach-induced destabilization.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/test_ar_cable_retention.py --device cuda:1
"""

import argparse
import os
import sys
import time

import numpy as np
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_pkg_dir = os.path.join(_script_dir, "..")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _pkg_dir)


def run_test(env, test_name, actions_fn, n_steps=200):
    """Run a single test: n_steps with given action function.

    Args:
        env: NewtonAerialRegraspEnv instance.
        actions_fn: callable(step_idx, obs) -> torch.Tensor[world_count, 12].
        n_steps: number of RL steps.

    Returns:
        dict with per-step metrics.
    """
    print(f"\n{'='*60}")
    print(f"  TEST: {test_name} ({n_steps} steps)")
    print(f"{'='*60}")

    # Force full reset
    obs = env.reset()

    history = {
        "cable_z_min": [],
        "cable_drop_count": [],
        "cable_drop_count_r": [],
        "cable_drop_count_l": [],
        "left_ee_drift": [],
        "dist_pos_median": [],
        "done_count": [],
    }

    total_drops = 0
    total_resets = 0

    for step_i in range(n_steps):
        actions = actions_fn(step_i, obs)
        obs, rewards, dones, extras = env.step(actions)

        log = extras.get("log", {})
        cable_z = log.get("/metrics/cable_z_min", float("nan"))
        drops = log.get("/metrics/cable_drop_count", 0)
        drops_r = log.get("/metrics/cable_drop_count_r", 0)
        drops_l = log.get("/metrics/cable_drop_count_l", 0)
        drift = log.get("/metrics/left_ee_drift", 0.0)
        dist = log.get("/metrics/dist_pos_median", float("nan"))
        n_done = int(dones.sum().item())

        history["cable_z_min"].append(cable_z)
        history["cable_drop_count"].append(drops)
        history["cable_drop_count_r"].append(drops_r)
        history["cable_drop_count_l"].append(drops_l)
        history["left_ee_drift"].append(drift)
        history["dist_pos_median"].append(dist)
        history["done_count"].append(n_done)

        total_drops += drops
        total_resets += n_done

        if step_i % 20 == 0 or drops > 0:
            print(
                f"  step {step_i:3d}: cable_z_min={cable_z:.4f}m  "
                f"drops={drops}(R:{drops_r}/L:{drops_l})  "
                f"drift={drift:.4f}m  dist_pos={dist*1000:.1f}mm  "
                f"dones={n_done}"
            )

    # Summary
    cable_z_arr = np.array(history["cable_z_min"])
    drops_arr = np.array(history["cable_drop_count"])
    thresh = env.CABLE_DROP_Z_THRESH

    print(f"\n  --- {test_name} Summary ---")
    print(f"  Cable drop threshold: {thresh:.4f}m")
    print(f"  Cable Z min (overall): {np.nanmin(cable_z_arr):.4f}m")
    print(f"  Cable Z mean: {np.nanmean(cable_z_arr):.4f}m")
    print(f"  Total cable drops: {total_drops} across {n_steps} steps")
    print(f"  Total episode resets: {total_resets}")
    steps_with_drops = int(np.sum(drops_arr > 0))
    print(f"  Steps with ≥1 drop: {steps_with_drops}/{n_steps}")
    print(f"  Left EE drift (final): {history['left_ee_drift'][-1]:.4f}m")

    if total_drops == 0:
        print(f"  RESULT: PASS — cable held stably for {n_steps} steps")
    else:
        first_drop_step = int(np.argmax(drops_arr > 0))
        print(f"  RESULT: FAIL — first drop at step {first_drop_step}")

    return history


def main():
    parser = argparse.ArgumentParser(description="AR Cable Retention Test")
    parser.add_argument("--device", type=str, default="cuda:1")
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--steps", type=int, default=200)
    args = parser.parse_args()

    from newton_aerial_regrasp_env import NewtonAerialRegraspEnv

    print(f"[AR-RETENTION] Device: {args.device}, Worlds: {args.world_count}")

    env = NewtonAerialRegraspEnv(
        world_count=args.world_count,
        device=args.device,
    )

    wc = args.world_count
    dev = args.device

    # ---- Test 1: Zero actions (baseline stability) ----
    def zero_actions(step_i, obs):
        return torch.zeros(wc, 12, device=dev)

    h1 = run_test(env, "Zero Actions (baseline)", zero_actions, args.steps)

    # ---- Test 2: Right arm slow approach ----
    # Generate actions that slowly move right arm toward cable.
    # Action space: [r_pos(3), r_rot(3), l_pos(3), l_rot(3)] normalized [-1, 1].
    # We use small positive X action to push right arm toward cable.
    # The exact mapping depends on env DELTA_POS_SCALE, but a small constant
    # action (0.1) will produce a slow, steady approach.
    def slow_approach(step_i, obs):
        a = torch.zeros(wc, 12, device=dev)
        # Right arm: small action toward cable target (direction depends on obs)
        # Use obs-derived error if available, else constant small action
        # For simplicity: constant downward + inward action
        a[:, 0] = -0.1   # small X (toward cable, depends on robot config)
        a[:, 2] = -0.05  # small Z descent
        return a

    h2 = run_test(env, "Right Arm Slow Approach", slow_approach, args.steps)

    # ---- Test 3: Random small actions (noise stability) ----
    def random_small(step_i, obs):
        return 0.1 * torch.randn(wc, 12, device=dev)

    h3 = run_test(env, "Random Small Actions (noise)", random_small, args.steps)

    # ---- Overall verdict ----
    print(f"\n{'='*60}")
    print("  OVERALL VERDICT")
    print(f"{'='*60}")
    t1_drops = sum(h1["cable_drop_count"])
    t2_drops = sum(h2["cable_drop_count"])
    t3_drops = sum(h3["cable_drop_count"])
    print(f"  Test 1 (zero action):    {t1_drops} drops → {'PASS' if t1_drops == 0 else 'FAIL'}")
    print(f"  Test 2 (slow approach):  {t2_drops} drops → {'PASS' if t2_drops == 0 else 'FAIL'}")
    print(f"  Test 3 (random small):   {t3_drops} drops → {'PASS' if t3_drops == 0 else 'FAIL'}")

    if t1_drops > 0:
        print("\n  CONCLUSION: VBD physics cannot hold cable stably even with zero interaction.")
        print("  Cable retention is a PHYSICS LIMITATION, not a policy problem.")
        print("  → Reward/termination redesign alone cannot fix this.")
    elif t2_drops > 0 and t1_drops == 0:
        print("\n  CONCLUSION: Cable is stable at rest but destabilized by right arm approach.")
        print("  → Policy-induced destabilization. Termination redesign (grace period) may help.")
    else:
        print("\n  CONCLUSION: Cable retention is physically feasible.")
        print("  → cable_drop in training is a policy problem. Reward/termination tuning viable.")


if __name__ == "__main__":
    main()
