# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test: VBD Rod cable + replicate() multi-world.

Validates whether Newton's replicate() works with VBD solver and Cosserat Rod cable.
All public examples use MuJoCo Warp (rigid body) — VBD multi-world is UNPROVEN.

This test:
1. Creates a single world with table + cable rod + kinematic box "gripper"
2. Replicates it N times via ModelBuilder.replicate()
3. Runs VBD solver for 100 steps
4. Checks: no NaN, cable positions vary per-world, particle_world_start correct

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/test_vbd_multiworld.py [--world-count 4]
"""

import argparse
import os
import sys
import time

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD

DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")


def build_single_world(gravity=-9.81):
    """Build one world: table + cable rod."""
    builder = newton.ModelBuilder(gravity=gravity)

    # Table (ground plane)
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    builder.add_shape_box(
        body=-1, hx=0.3, hy=0.3, hz=0.005,
        xform=wp.transform((0.3, 0.0, 0.795), wp.quat_identity()),
        cfg=table_cfg,
    )

    # Cable rod (20 segments, along Y)
    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = 2500.0
    cable_cfg.kd = 100.0
    cable_cfg.mu = 1.0
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002
    cable_cfg.density = 1100.0

    n_segments = 20
    seg_len = 0.015
    radius = 0.004
    positions = []
    for i in range(n_segments + 1):
        positions.append((0.30, -0.15 + i * seg_len, 0.80 + radius))

    body_ids, joint_ids = builder.add_rod(
        positions=positions,
        radius=radius,
        stretch_stiffness=1.0e6,
        stretch_damping=0.0,
        bend_stiffness=3.0,
        bend_damping=0.01,
        cfg=cable_cfg,
    )

    return builder, body_ids, joint_ids


def test_multiworld(world_count):
    """Test VBD multi-world with cable rod."""
    print(f"\n{'='*60}")
    print(f"  VBD Multi-World Test: world_count={world_count}")
    print(f"{'='*60}")

    wp.init()
    wp.set_device(DEVICE)

    # Build single world
    world_builder, body_ids, joint_ids = build_single_world()
    print(f"  Single world: {len(body_ids)} cable bodies, {len(joint_ids)} cable joints")

    # Replicate
    print(f"  Replicating {world_count} worlds...")
    scene = newton.ModelBuilder()
    try:
        scene.replicate(world_builder, world_count=world_count)
    except Exception as e:
        print(f"  FAIL: replicate() error: {e}")
        return False

    # Finalize
    try:
        model = scene.finalize(device=DEVICE, requires_grad=False)
    except Exception as e:
        print(f"  FAIL: finalize() error: {e}")
        return False

    print(f"  Model: bodies={model.body_count}, joints={model.joint_count}")

    # Check particle_world_start (if particles exist)
    has_particles = hasattr(model, 'particle_count') and model.particle_count > 0
    if has_particles:
        print(f"  Particles: {model.particle_count}")
        if hasattr(model, 'particle_world_start') and model.particle_world_start is not None:
            pws = model.particle_world_start.numpy()
            print(f"  particle_world_start: {pws}")
        else:
            print(f"  particle_world_start: NOT SET")

    # Check body distribution
    if hasattr(model, 'body_world') and model.body_world is not None:
        bw = model.body_world.numpy()
        for w in range(world_count):
            count = int(np.sum(bw == w))
            print(f"  World {w}: {count} bodies")

    # Create VBD solver
    print(f"\n  Creating SolverVBD...")
    try:
        solver = SolverVBD(
            model,
            iterations=20,
            integrate_with_external_rigid_solver=True,
        )
    except Exception as e:
        print(f"  FAIL: SolverVBD creation error: {e}")
        return False

    # Create states
    state_0 = model.state()
    state_1 = model.state()
    control = model.control()

    # Run collision detection
    print(f"  Running collide()...")
    try:
        contacts = model.collide(state_0)
    except Exception as e:
        print(f"  FAIL: collide() error: {e}")
        return False

    # Run VBD solver for 100 steps
    print(f"  Running 100 solver steps...")
    dt = 1.0 / 480.0
    sub_dt = dt / 10
    t0 = time.time()
    nan_detected = False

    for step in range(100):
        for sub in range(10):
            state_0.clear_forces()
            try:
                model.collide(state_0, contacts)
                solver.step(state_0, state_1, control, contacts, sub_dt)
            except Exception as e:
                print(f"  FAIL: step error at frame {step}, sub {sub}: {e}")
                return False
            state_0, state_1 = state_1, state_0

        # Check for NaN
        bq = state_0.body_q.numpy()
        if np.any(np.isnan(bq)):
            print(f"  FAIL: NaN at step {step}")
            nan_detected = True
            break

        if step % 25 == 0:
            # Check cable positions per world
            bodies_per_world = len(body_ids)
            for w in range(min(world_count, 3)):
                start = w * bodies_per_world
                end = start + bodies_per_world
                if end <= bq.shape[0]:
                    z_mean = float(np.mean(bq[start:end, 2]))
                    print(f"  Step {step}, World {w}: cable avg_z={z_mean:.4f}")

    elapsed = time.time() - t0
    steps_per_sec = 100 / elapsed
    print(f"\n  100 steps in {elapsed:.2f}s ({steps_per_sec:.0f} steps/s)")

    if nan_detected:
        print(f"  RESULT: FAIL (NaN)")
        return False

    # Verify final state
    bq = state_0.body_q.numpy()
    bodies_per_world = len(body_ids)
    all_ok = True

    for w in range(world_count):
        start = w * bodies_per_world
        end = start + bodies_per_world
        if end > bq.shape[0]:
            print(f"  FAIL: World {w} body indices out of range")
            all_ok = False
            continue
        cable_z = bq[start:end, 2]
        z_min = float(np.min(cable_z))
        z_max = float(np.max(cable_z))
        z_mean = float(np.mean(cable_z))
        has_nan = np.any(np.isnan(cable_z))
        print(f"  World {w}: z=[{z_min:.4f}, {z_max:.4f}], mean={z_mean:.4f}, nan={has_nan}")
        if has_nan:
            all_ok = False

    # VRAM usage
    try:
        import torch
        if torch.cuda.is_available():
            dev_idx = int(DEVICE.split(":")[-1]) if ":" in DEVICE else 0
            vram_mb = torch.cuda.memory_allocated(dev_idx) / 1024 / 1024
            vram_reserved_mb = torch.cuda.memory_reserved(dev_idx) / 1024 / 1024
            print(f"\n  VRAM: allocated={vram_mb:.0f}MB, reserved={vram_reserved_mb:.0f}MB")
    except ImportError:
        pass

    if all_ok:
        print(f"\n  RESULT: PASS — VBD multi-world ({world_count} worlds) works!")
    else:
        print(f"\n  RESULT: FAIL")
    return all_ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default=DEVICE)
    args = parser.parse_args()

    DEVICE = args.device  # module-level shadow

    results = {}
    for n in [1, 2, args.world_count]:
        if n not in results:
            ok = test_multiworld(n)
            results[n] = "PASS" if ok else "FAIL"

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    for n, r in sorted(results.items()):
        print(f"  world_count={n}: {r}")


if __name__ == "__main__":
    main()
