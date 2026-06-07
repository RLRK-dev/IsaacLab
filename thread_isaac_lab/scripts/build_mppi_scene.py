#!/usr/bin/env python3
"""Depend B: Newton VBD multi-world scene benchmark for MPPI demo generation.

Builds single-arm Franka + cable (40 segments) scenes at K={32,64,128,256}
and measures FPS, VRAM, and per-world state independence.

Usage:
    cd ~/IsaacLab
    ./isaaclab.sh -p thread_isaac_lab/scripts/build_mppi_scene.py --device cuda:0
"""

import argparse
import csv
import os
import subprocess
import sys
import time

import numpy as np
import torch

# Newton + Warp
import warp as wp
import newton
from newton.solvers import SolverVBD

# Add scripts dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))

from task_config import (
    TABLE_HEIGHT, ROBOT_LEFT_BASE,
    CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    CABLE_BEND_STIFFNESS, CABLE_BEND_DAMPING,
    CABLE_STRETCH_STIFFNESS, CABLE_STRETCH_DAMPING,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
    GRASP_X, CLIP1_Y, CLIP_BASE_HEIGHT,
    FINGER_OPEN_POS, SIM_SUBSTEPS, NJMAX,
)
from test_newton_clip_routing import (
    build_fk_model,
    add_kinematic_arm,
    FRANKA_NUM_JOINTS,
    GRAVITY,
)

RL_SIM_SUBSTEPS = 4
VBD_ITERATIONS = 20
DT = 1.0 / 480.0
BENCH_STEPS = 100
VRAM_HARD_LIMIT_MB = 40_000


def get_gpu_vram_mb(device_idx=0):
    """Get GPU VRAM usage via nvidia-smi (Warp uses its own allocator, not PyTorch)."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits",
             f"--id={device_idx}"],
            text=True,
        )
        return int(out.strip())
    except Exception:
        return -1


def add_cable_rod_simple(builder, start_pos, direction=(0, 1, 0)):
    """Add cable rod using task_config.py SSOT values."""
    n_points = CABLE_SEGMENTS + 1
    dir_np = np.array(direction, dtype=np.float64)
    dir_np = dir_np / np.linalg.norm(dir_np)
    positions = []
    for i in range(n_points):
        p = np.array(start_pos) + dir_np * (i * CABLE_SEG_LEN)
        positions.append(tuple(p))

    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = CABLE_CONTACT_KE
    cable_cfg.kd = CABLE_CONTACT_KD
    cable_cfg.mu = CABLE_CONTACT_MU
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002
    cable_cfg.density = 1100.0

    body_ids, joint_ids = builder.add_rod(
        positions=positions,
        radius=CABLE_RADIUS,
        stretch_stiffness=CABLE_STRETCH_STIFFNESS,
        stretch_damping=CABLE_STRETCH_DAMPING,
        bend_stiffness=CABLE_BEND_STIFFNESS,
        bend_damping=CABLE_BEND_DAMPING,
        cfg=cable_cfg,
    )
    total_length = CABLE_SEGMENTS * CABLE_SEG_LEN
    print(f"  [CABLE] add_rod: {len(body_ids)} bodies, {len(joint_ids)} joints, "
          f"total_length={total_length * 1000:.0f}mm")
    return body_ids, joint_ids


def build_proto(fk_model, fk_state, device):
    """Build single-world prototype: 1 arm (left) + cable."""
    proto = newton.ModelBuilder()

    # Single arm (left only for M1)
    arm_info = add_kinematic_arm(
        proto, fk_model, fk_state,
        arm_body_offset=0, label_prefix="left",
    )
    arm_body_start, arm_shape_start, arm_shape_end, finger_vis = arm_info
    finger_vis_set = set(finger_vis)

    # Contact filtering: arm 0-6 VISIBLE only, finger 7-8 COLLIDE
    for si in range(arm_shape_start, arm_shape_end):
        local = proto.shape_body[si] - arm_body_start
        if local < 7:
            proto.shape_flags[si] = 1  # VISIBLE only
        elif si in finger_vis_set:
            proto.shape_flags[si] = 1  # VISIBLE only
        elif local in (7, 8):
            proto.shape_flags[si] = 0x6  # COLLIDE | BROADPHASE

    # Cable
    cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
    cable_y_start = CLIP1_Y - cable_half_len
    cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS)
    cable_shape_start = proto.shape_count
    cable_bodies, cable_joints = add_cable_rod_simple(proto, start_pos=cable_start)
    cable_shape_end = proto.shape_count

    # Cable-arm collision filter (arm bodies 0-6 don't collide with cable)
    for cable_si in range(cable_shape_start, cable_shape_end):
        for arm_si in range(arm_shape_start, arm_shape_end):
            local = proto.shape_body[arm_si] - arm_body_start
            if local < 7:
                proto.add_shape_collision_filter_pair(cable_si, arm_si)

    bodies_per_world = proto.body_count
    print(f"  [PROTO] {proto.body_count} bodies, {proto.joint_count} joints, "
          f"{proto.shape_count} shapes")
    return proto, bodies_per_world, len(cable_bodies)


def build_scene(proto, world_count, device):
    """Build scene: ground + table + replicate proto."""
    scene = newton.ModelBuilder(gravity=GRAVITY)

    # Ground plane
    scene.add_ground_plane()

    # Table
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_xform = wp.transform((0.3, -0.05, TABLE_HEIGHT - 0.005), wp.quat_identity())
    scene.add_shape_box(body=-1, hx=0.35, hy=0.35, hz=0.005,
                        xform=table_xform, cfg=table_cfg)

    # Replicate
    scene.replicate(proto, world_count=world_count)
    scene.color()

    model = scene.finalize(device=device, requires_grad=False)
    print(f"  [SCENE] K={world_count}: {model.body_count} bodies, "
          f"{model.joint_count} joints, {model.shape_count} shapes")

    # Zero inv_mass for robot kinematic bodies (per world)
    bws = model.body_world_start.numpy()
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()
    for w in range(world_count):
        start = bws[w]
        for bi in range(FRANKA_NUM_JOINTS):
            inv_mass[start + bi] = 0.0
            inv_inertia[start + bi] = np.zeros(3, dtype=np.float32)
    model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=device)
    model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=device)

    return model, bws


def benchmark_world_count(K, fk_model, fk_state, device):
    """Build and benchmark scene at world_count=K."""
    print(f"\n{'=' * 60}")
    print(f"  Benchmarking K={K}")
    print(f"{'=' * 60}")

    # Parse GPU index from device string
    gpu_idx = int(device.split(":")[-1]) if ":" in device else 0

    # Check VRAM before build
    wp.synchronize_device(device)
    vram_before = get_gpu_vram_mb(gpu_idx)

    # Build
    proto, bodies_per_world, cable_bodies_per_world = build_proto(fk_model, fk_state, device)
    model, bws = build_scene(proto, K, device)

    # Solver + state
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    model.rigid_contact_max = NJMAX
    state_0 = model.state()
    state_1 = model.state()
    control = model.control()

    wp.synchronize_device(device)
    vram_after = get_gpu_vram_mb(gpu_idx)
    vram_used = vram_after - vram_before

    print(f"  VRAM: +{vram_used} MB (total: {vram_after} MB)")

    if vram_after > VRAM_HARD_LIMIT_MB:
        print(f"  ABORT: VRAM {vram_after:.0f} MB > hard limit {VRAM_HARD_LIMIT_MB} MB")
        return {
            "K": K,
            "cable_bodies": cable_bodies_per_world * K,
            "total_bodies": model.body_count,
            "vram_mb": vram_after,
            "fps": 0,
            "status": "OOM_ABORT",
        }

    # Verify state independence (before stepping)
    bq = state_0.body_q.numpy()
    cable_offset = FRANKA_NUM_JOINTS
    independence_ok = True
    for w in range(min(K, 5)):
        start = bws[w] + cable_offset
        end = start + cable_bodies_per_world
        cable_pos_w = bq[start:end, :3]
        if w > 0:
            start0 = bws[0] + cable_offset
            end0 = start0 + cable_bodies_per_world
            cable_pos_0 = bq[start0:end0, :3]
            if not np.allclose(cable_pos_w, cable_pos_0, atol=1e-6):
                print(f"  WARNING: World {w} cable state differs from world 0 at init")
                independence_ok = False
    print(f"  State independence (init): {'OK' if independence_ok else 'MISMATCH'}")

    # Benchmark: run BENCH_STEPS physics steps
    sim_dt = DT / RL_SIM_SUBSTEPS

    # Warm-up (5 steps)
    for _ in range(5):
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0

    torch.cuda.synchronize()
    t0 = time.perf_counter()

    for step in range(BENCH_STEPS):
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0

    torch.cuda.synchronize()
    t1 = time.perf_counter()

    elapsed = t1 - t0
    fps = BENCH_STEPS / elapsed
    ms_per_step = elapsed / BENCH_STEPS * 1000

    print(f"  FPS: {fps:.1f} ({ms_per_step:.2f} ms/step)")

    # Post-step state independence check
    bq_post = state_0.body_q.numpy()
    post_independence = True
    diffs = []
    for w in range(min(K, 5)):
        start = bws[w] + cable_offset
        end = start + cable_bodies_per_world
        cable_z_w = bq_post[start:end, 2]
        if w > 0:
            start0 = bws[0] + cable_offset
            end0 = start0 + cable_bodies_per_world
            cable_z_0 = bq_post[start0:end0, 2]
            diff = np.max(np.abs(cable_z_w - cable_z_0))
            diffs.append(diff)
            if diff > 1e-6:
                post_independence = False
    if diffs:
        print(f"  State independence (post-step): "
              f"{'OK (identical)' if post_independence else 'DIVERGED'} "
              f"max_diff={max(diffs):.2e}")

    # Check for NaN/inf
    has_nan = np.any(np.isnan(bq_post))
    has_inf = np.any(np.isinf(bq_post))
    print(f"  NaN: {has_nan}, Inf: {has_inf}")

    # Final VRAM
    wp.synchronize_device(device)
    vram_final = get_gpu_vram_mb(gpu_idx)

    status = "PASS"
    if has_nan or has_inf:
        status = "NaN_INF"
    elif vram_final > VRAM_HARD_LIMIT_MB:
        status = "OOM"

    return {
        "K": K,
        "cable_bodies": cable_bodies_per_world * K,
        "total_bodies": model.body_count,
        "vram_mb": round(vram_final),
        "fps": round(fps, 1),
        "status": status,
    }


def main():
    parser = argparse.ArgumentParser(description="MPPI scene benchmark (Depend B)")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--ramp", type=str, default="32,64,128,256",
                        help="Comma-separated K values for ramp-up")
    parser.add_argument("--csv", type=str, default="/tmp/mppi_m1_depB_vram_fps.csv")
    args = parser.parse_args()

    device = args.device
    k_values = [int(x) for x in args.ramp.split(",")]

    print(f"MPPI Scene Benchmark (Depend B)")
    print(f"  Device: {device}")
    print(f"  K values: {k_values}")
    print(f"  Cable segments: {CABLE_SEGMENTS}")
    print(f"  DT: {DT}, RL_SIM_SUBSTEPS: {RL_SIM_SUBSTEPS}")
    print(f"  Bench steps: {BENCH_STEPS}")
    print(f"  VRAM hard limit: {VRAM_HARD_LIMIT_MB} MB")

    wp.init()
    wp.set_device(device)

    # FK model (builds both arms; we only use left in proto)
    print("\n--- Building FK model ---")
    fk_model = build_fk_model(device=device)
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    fk_jq[7] = FINGER_OPEN_POS
    fk_jq[8] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Ramp-up benchmark
    results = []
    for K in k_values:
        try:
            result = benchmark_world_count(K, fk_model, fk_state, device)
        except Exception as e:
            print(f"  EXCEPTION at K={K}: {e}")
            result = {
                "K": K, "cable_bodies": 0, "total_bodies": 0,
                "vram_mb": 0, "fps": 0, "status": f"ERROR: {e}",
            }
        results.append(result)

        # Abort ramp if OOM
        if result["status"] in ("OOM_ABORT", "OOM"):
            print(f"\n  Stopping ramp-up: {result['status']} at K={K}")
            break

    # Summary table
    print(f"\n{'=' * 70}")
    print(f"  MPPI Scene Benchmark Results")
    print(f"{'=' * 70}")
    print(f"  {'K':>6} | {'Cable Bodies':>12} | {'Total Bodies':>12} | "
          f"{'VRAM (MB)':>10} | {'FPS':>8} | Status")
    print(f"  {'-' * 6}-+-{'-' * 12}-+-{'-' * 12}-+-{'-' * 10}-+-{'-' * 8}-+--------")
    for r in results:
        print(f"  {r['K']:>6} | {r['cable_bodies']:>12} | {r['total_bodies']:>12} | "
              f"{r['vram_mb']:>10} | {r['fps']:>8} | {r['status']}")

    # Write CSV
    csv_path = args.csv
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["K", "cable_bodies", "total_bodies",
                                                "vram_mb", "fps", "status"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n  CSV written to: {csv_path}")

    # Overall verdict
    all_pass = all(r["status"] == "PASS" for r in results)
    max_k_pass = max((r["K"] for r in results if r["status"] == "PASS"), default=0)
    print(f"\n  Overall: {'ALL PASS' if all_pass else f'MAX PASS K={max_k_pass}'}")


if __name__ == "__main__":
    main()
