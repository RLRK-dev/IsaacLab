"""Newton VBD Multi-World Verification — replicate(world_count=N) + add_rod() cable.

Minimal test: 4 worlds, each with a VBD Cosserat rod cable + ground plane.
No robot, no IK — pure cable physics only.

Verifications:
  T1: Model construction (world_start arrays, body/joint counts per world)
  T2: Simulation stability (100 frames, no NaN)
  T3: Per-world isolation (perturb world 0, verify worlds 1-3 unchanged)
  T4: Per-world reset (reset world 0, verify worlds 1-3 unaffected)
  T5: Performance metrics (VRAM, step timing)

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_vbd_multiworld.py
    # Custom world count:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_vbd_multiworld.py --world-count 8
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD

# Import cable parameters from task_config (SSOT)
_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    CABLE_BEND_STIFFNESS, CABLE_BEND_DAMPING,
    CABLE_STRETCH_STIFFNESS, CABLE_STRETCH_DAMPING,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0             # Frame dt
SIM_SUBSTEPS = 4              # Lighter than full THREAD (10) — sufficient for cable-only
SIM_DT = DT / SIM_SUBSTEPS
GRAVITY = -9.81
VBD_ITERATIONS = 20
TABLE_HEIGHT = 0.80
N_SETTLE_FRAMES = 50          # Frames to let cable settle under gravity
N_TEST_FRAMES = 100           # Frames for isolation/stability test


def build_single_world_cable():
    """Build a single-world prototype: ground plane + table + VBD cable.

    Returns a ModelBuilder (not finalized) suitable for replicate().
    """
    builder = newton.ModelBuilder(gravity=GRAVITY)

    # Ground plane (will become global entity, world=-1)
    builder.add_ground_plane()

    # Table BOX (kinematic, body=-1)
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_xform = wp.transform((0.3, -0.05, TABLE_HEIGHT - 0.005), wp.quat_identity())
    builder.add_shape_box(
        body=-1,
        hx=0.35, hy=0.35, hz=0.005,
        xform=table_xform,
        cfg=table_cfg,
    )

    # Cable: Cosserat Rod (add_rod)
    n_points = CABLE_SEGMENTS + 1
    cable_start = np.array([0.25, -0.20, TABLE_HEIGHT + CABLE_RADIUS + 0.001])
    cable_dir = np.array([0.0, 1.0, 0.0])  # Along Y-axis
    positions = []
    for i in range(n_points):
        p = cable_start + cable_dir * (i * CABLE_SEG_LEN)
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

    print(f"  [PROTO] Single-world cable: {len(body_ids)} bodies, {len(joint_ids)} joints")
    return builder


def test_construction(model, world_count):
    """T1: Verify model construction — world_start arrays and per-world counts."""
    print(f"\n{'='*60}")
    print(f"  T1: Model Construction Verification (world_count={world_count})")
    print(f"{'='*60}")

    errors = []

    # Check world_start arrays exist and have correct shape
    bws = model.body_world_start.numpy()
    jws = model.joint_world_start.numpy()
    sws = model.shape_world_start.numpy()

    print(f"  body_world_start:  {bws}")
    print(f"  joint_world_start: {jws}")
    print(f"  shape_world_start: {sws}")
    print(f"  Total: bodies={model.body_count}, joints={model.joint_count}, "
          f"shapes={model.shape_count}")

    # Per-world body count should be uniform
    bodies_per_world = []
    joints_per_world = []
    for w in range(world_count):
        nb = bws[w + 1] - bws[w]
        nj = jws[w + 1] - jws[w]
        bodies_per_world.append(nb)
        joints_per_world.append(nj)
        print(f"  World {w}: bodies=[{bws[w]}:{bws[w+1]}] ({nb}), "
              f"joints=[{jws[w]}:{jws[w+1]}] ({nj})")

    # All worlds should have the same count
    if len(set(bodies_per_world)) != 1:
        errors.append(f"Non-uniform bodies per world: {bodies_per_world}")
    if len(set(joints_per_world)) != 1:
        errors.append(f"Non-uniform joints per world: {joints_per_world}")

    # Global entities (ground plane, table)
    global_start = bws[world_count]  # Second-to-last element
    global_end = bws[world_count + 1]  # Last element = total
    n_global_bodies = global_end - global_start
    print(f"  Global bodies: [{global_start}:{global_end}] ({n_global_bodies})")

    # Expected: each world has CABLE_SEGMENTS bodies (from add_rod)
    expected_bodies = CABLE_SEGMENTS
    if bodies_per_world[0] != expected_bodies:
        errors.append(f"Expected {expected_bodies} bodies/world, got {bodies_per_world[0]}")

    if errors:
        print(f"\n  T1 FAIL: {errors}")
    else:
        print(f"\n  T1 PASS: {world_count} worlds × {bodies_per_world[0]} bodies/world, "
              f"construction correct")
    return len(errors) == 0


def test_stability(model, solver, world_count, n_frames=N_TEST_FRAMES):
    """T2: Run simulation and verify no NaN/crash."""
    print(f"\n{'='*60}")
    print(f"  T2: Simulation Stability ({n_frames} frames)")
    print(f"{'='*60}")

    state_0 = model.state()
    state_1 = model.state()
    control = model.control()
    contacts = model.contacts()

    errors = []
    nan_frame = -1

    t_start = time.perf_counter()
    for frame in range(n_frames):
        for sub in range(SIM_SUBSTEPS):
            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, control, contacts, SIM_DT)
            state_0, state_1 = state_1, state_0

        # Check NaN every 10 frames
        if (frame + 1) % 10 == 0 or frame == n_frames - 1:
            wp.synchronize()
            bq = state_0.body_q.numpy()
            if np.any(np.isnan(bq)):
                nan_frame = frame
                errors.append(f"NaN detected at frame {frame}")
                break
    t_elapsed = time.perf_counter() - t_start

    wp.synchronize()
    bq = state_0.body_q.numpy()

    # Report per-world cable Z positions (should have settled on table)
    bws = model.body_world_start.numpy()
    for w in range(world_count):
        start, end = bws[w], bws[w + 1]
        cable_z = bq[start:end, 2]  # Z component of position (index 2 in transform)
        print(f"  World {w}: cable Z mean={np.mean(cable_z):.4f}, "
              f"min={np.min(cable_z):.4f}, max={np.max(cable_z):.4f}")

    fps = n_frames / t_elapsed if t_elapsed > 0 else 0
    print(f"  Timing: {n_frames} frames in {t_elapsed:.2f}s ({fps:.1f} FPS)")

    if errors:
        print(f"\n  T2 FAIL: {errors}")
    else:
        print(f"\n  T2 PASS: {n_frames} frames without NaN")
    return len(errors) == 0, state_0


def test_isolation(model, solver, world_count, settled_state):
    """T3: Per-world isolation — perturb world 0, verify worlds 1-3 unchanged."""
    print(f"\n{'='*60}")
    print(f"  T3: Per-World Isolation")
    print(f"{'='*60}")

    # Snapshot all worlds' cable positions before perturbation
    wp.synchronize()
    bws = model.body_world_start.numpy()
    bq_before = settled_state.body_q.numpy().copy()

    # Record world 1-3 positions
    ref_positions = {}
    for w in range(1, world_count):
        start, end = bws[w], bws[w + 1]
        ref_positions[w] = bq_before[start:end].copy()

    # Perturb world 0: teleport cable bodies upward by 0.1m
    state_perturbed = model.state()
    bq_pert = bq_before.copy()
    w0_start, w0_end = bws[0], bws[1]
    bq_pert[w0_start:w0_end, 2] += 0.1  # Z += 100mm
    state_perturbed.body_q.assign(bq_pert)

    # Also copy velocities from settled state
    bqd = settled_state.body_qd.numpy().copy()
    state_perturbed.body_qd.assign(bqd)

    print(f"  Perturbed world 0: bodies [{w0_start}:{w0_end}] Z += 100mm")

    # Run 20 frames with perturbation
    state_0 = state_perturbed
    state_1 = model.state()
    control = model.control()
    contacts = model.contacts()

    n_isolation_frames = 20
    for frame in range(n_isolation_frames):
        for sub in range(SIM_SUBSTEPS):
            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, control, contacts, SIM_DT)
            state_0, state_1 = state_1, state_0

    wp.synchronize()
    bq_after = state_0.body_q.numpy()

    # Check: worlds 1-3 should be within tolerance of their pre-perturbation positions
    errors = []
    tol = 1e-3  # 1mm tolerance (some drift from continued simulation is acceptable)
    for w in range(1, world_count):
        start, end = bws[w], bws[w + 1]
        pos_after = bq_after[start:end]
        pos_ref = ref_positions[w]
        # Compare XYZ positions (first 3 elements of transform)
        max_diff = np.max(np.abs(pos_after[:, :3] - pos_ref[:, :3]))
        print(f"  World {w}: max position diff = {max_diff*1000:.3f}mm "
              f"({'PASS' if max_diff < tol else 'FAIL'})")
        if max_diff >= tol:
            errors.append(f"World {w} moved {max_diff*1000:.3f}mm (tol={tol*1000}mm)")

    # World 0 should have changed significantly
    w0_diff = np.max(np.abs(bq_after[w0_start:w0_end, :3] - bq_before[w0_start:w0_end, :3]))
    print(f"  World 0: max position diff = {w0_diff*1000:.3f}mm (expected large)")

    if errors:
        print(f"\n  T3 FAIL: {errors}")
    else:
        print(f"\n  T3 PASS: Perturbation in world 0 did not affect worlds 1-{world_count-1}")
    return len(errors) == 0


def test_reset(model, solver, world_count, settled_state):
    """T4: Per-world reset — reset world 0 to initial, verify worlds 1-3 untouched."""
    print(f"\n{'='*60}")
    print(f"  T4: Per-World Reset")
    print(f"{'='*60}")

    wp.synchronize()
    bws = model.body_world_start.numpy()
    jws = model.joint_world_start.numpy()

    # Save settled state as the "initial" reference
    settled_bq = settled_state.body_q.numpy().copy()
    settled_bqd = settled_state.body_qd.numpy().copy()

    # Evolve for 50 frames to create diverged state
    state_0 = model.state()
    state_0.body_q.assign(settled_bq)
    state_0.body_qd.assign(settled_bqd)

    # Apply a downward force to world 0 cable for 50 frames to make it differ
    state_1 = model.state()
    control = model.control()
    contacts = model.contacts()
    w0_start, w0_end = bws[0], bws[1]

    for frame in range(50):
        # Apply external force to world 0 only
        bf = state_0.body_f.numpy()
        bf[w0_start:w0_end, 2] = -5.0  # Downward force on Z
        state_0.body_f.assign(bf)

        for sub in range(SIM_SUBSTEPS):
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, control, contacts, SIM_DT)
            state_0, state_1 = state_1, state_0
            if sub < SIM_SUBSTEPS - 1:
                state_0.clear_forces()

    wp.synchronize()
    bq_diverged = state_0.body_q.numpy().copy()
    w0_diverged_diff = np.max(np.abs(bq_diverged[w0_start:w0_end, :3] - settled_bq[w0_start:w0_end, :3]))
    print(f"  After 50 frames with force: world 0 max diff = {w0_diverged_diff*1000:.3f}mm")

    # Record worlds 1-3 positions before reset
    other_bq_before_reset = {}
    for w in range(1, world_count):
        start, end = bws[w], bws[w + 1]
        other_bq_before_reset[w] = bq_diverged[start:end].copy()

    # Reset world 0: body_q, body_qd, solver.body_q_prev
    bq_reset = bq_diverged.copy()
    bqd_reset = state_0.body_qd.numpy().copy()
    bq_reset[w0_start:w0_end] = settled_bq[w0_start:w0_end]
    bqd_reset[w0_start:w0_end] = 0.0  # Zero velocity
    state_0.body_q.assign(bq_reset)
    state_0.body_qd.assign(bqd_reset)

    # Reset solver internal state for world 0
    if hasattr(solver, 'body_q_prev'):
        prev = solver.body_q_prev.numpy()
        prev[w0_start:w0_end] = settled_bq[w0_start:w0_end]
        solver.body_q_prev.assign(prev)
        print(f"  Reset solver.body_q_prev for world 0 [{w0_start}:{w0_end}]")

    # Reset Dahl friction state for world 0 joints
    if hasattr(solver, 'enable_dahl_friction') and solver.enable_dahl_friction:
        j0_start, j0_end = jws[0], jws[1]
        if hasattr(solver, 'joint_C_fric'):
            cf = solver.joint_C_fric.numpy()
            cf[j0_start:j0_end] = 0.0
            solver.joint_C_fric.assign(cf)
        if hasattr(solver, 'joint_sigma_prev'):
            sp = solver.joint_sigma_prev.numpy()
            sp[j0_start:j0_end] = 0.0
            solver.joint_sigma_prev.assign(sp)
        print(f"  Reset Dahl friction for world 0 joints [{j0_start}:{j0_end}]")

    # Run 10 frames after reset
    for frame in range(10):
        for sub in range(SIM_SUBSTEPS):
            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, control, contacts, SIM_DT)
            state_0, state_1 = state_1, state_0

    wp.synchronize()
    bq_after_reset = state_0.body_q.numpy()

    # Check: world 0 should be close to settled state (it was reset to it)
    w0_reset_diff = np.max(np.abs(bq_after_reset[w0_start:w0_end, :3] - settled_bq[w0_start:w0_end, :3]))
    print(f"  World 0 after reset+10frames: max diff from settled = {w0_reset_diff*1000:.3f}mm")

    # Check: worlds 1-3 should be close to their pre-reset positions (only 10 frames of drift)
    errors = []
    tol = 2.0e-3  # 2mm tolerance (gravity drift over 10 frames)
    for w in range(1, world_count):
        start, end = bws[w], bws[w + 1]
        pos_after = bq_after_reset[start:end]
        pos_before = other_bq_before_reset[w]
        max_diff = np.max(np.abs(pos_after[:, :3] - pos_before[:, :3]))
        print(f"  World {w}: max diff from pre-reset = {max_diff*1000:.3f}mm "
              f"({'PASS' if max_diff < tol else 'FAIL'})")
        if max_diff >= tol:
            errors.append(f"World {w} drifted {max_diff*1000:.3f}mm (tol={tol*1000}mm)")

    # World 0 reset quality
    w0_pass = w0_reset_diff < 0.01  # 10mm tolerance (cable bounces after reset)
    if not w0_pass:
        errors.append(f"World 0 reset quality: {w0_reset_diff*1000:.1f}mm from settled")
        print(f"  World 0 reset quality: FAIL ({w0_reset_diff*1000:.1f}mm)")
    else:
        print(f"  World 0 reset quality: PASS ({w0_reset_diff*1000:.1f}mm)")

    if errors:
        print(f"\n  T4 FAIL: {errors}")
    else:
        print(f"\n  T4 PASS: World 0 reset succeeded without affecting worlds 1-{world_count-1}")
    return len(errors) == 0


def test_performance(model, solver, world_count):
    """T5: Performance metrics — VRAM usage and step timing."""
    print(f"\n{'='*60}")
    print(f"  T5: Performance Metrics")
    print(f"{'='*60}")

    state_0 = model.state()
    state_1 = model.state()
    control = model.control()
    contacts = model.contacts()

    # Warm up (5 frames)
    for _ in range(5):
        for sub in range(SIM_SUBSTEPS):
            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, control, contacts, SIM_DT)
            state_0, state_1 = state_1, state_0

    wp.synchronize()

    # Measure step timing (50 frames)
    n_bench = 50
    t_start = time.perf_counter()
    for _ in range(n_bench):
        for sub in range(SIM_SUBSTEPS):
            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, control, contacts, SIM_DT)
            state_0, state_1 = state_1, state_0
    wp.synchronize()
    t_elapsed = time.perf_counter() - t_start

    fps = n_bench / t_elapsed
    ms_per_frame = (t_elapsed / n_bench) * 1000
    ms_per_substep = ms_per_frame / SIM_SUBSTEPS

    # VRAM usage (via warp)
    try:
        import torch
        vram_alloc_mb = torch.cuda.memory_allocated() / 1024**2
        vram_reserved_mb = torch.cuda.memory_reserved() / 1024**2
    except Exception:
        vram_alloc_mb = -1
        vram_reserved_mb = -1

    metrics = {
        "world_count": world_count,
        "bodies_total": model.body_count,
        "joints_total": model.joint_count,
        "shapes_total": model.shape_count,
        "bodies_per_world": model.body_count // max(world_count, 1),
        "fps": round(fps, 1),
        "ms_per_frame": round(ms_per_frame, 2),
        "ms_per_substep": round(ms_per_substep, 3),
        "vram_allocated_mb": round(vram_alloc_mb, 1),
        "vram_reserved_mb": round(vram_reserved_mb, 1),
    }

    for k, v in metrics.items():
        print(f"  {k}: {v}")

    print(f"\n  T5 DONE: {fps:.1f} FPS, {ms_per_frame:.2f} ms/frame")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="VBD Multi-World Verification")
    parser.add_argument("--world-count", type=int, default=4, help="Number of worlds")
    parser.add_argument("--device", type=str, default=DEVICE, help="CUDA device")
    args = parser.parse_args()

    world_count = args.world_count
    device = args.device

    print(f"\n{'#'*60}")
    print(f"  Newton VBD Multi-World Verification")
    print(f"  world_count={world_count}, device={device}")
    print(f"{'#'*60}")

    wp.init()

    # -----------------------------------------------------------------------
    # Build scene: single-world prototype → replicate to N worlds
    # -----------------------------------------------------------------------
    print(f"\n  Building single-world cable prototype...")
    proto = build_single_world_cable()

    print(f"\n  Replicating to {world_count} worlds...")
    scene = newton.ModelBuilder(gravity=GRAVITY)
    scene.replicate(proto, world_count=world_count)

    # Color for VBD solver (required: body_color_groups)
    print(f"  Coloring model for VBD...")
    scene.color()

    print(f"  Finalizing model on {device}...")
    model = scene.finalize(device=device)

    print(f"  Creating SolverVBD (iterations={VBD_ITERATIONS})...")
    solver = SolverVBD(
        model,
        iterations=VBD_ITERATIONS,
        integrate_with_external_rigid_solver=False,  # VBD handles everything
        rigid_enable_dahl_friction=False,             # Not needed for cable-only test
    )

    # -----------------------------------------------------------------------
    # T1: Construction
    # -----------------------------------------------------------------------
    t1_pass = test_construction(model, world_count)

    # -----------------------------------------------------------------------
    # T2: Stability
    # -----------------------------------------------------------------------
    t2_pass, settled_state = test_stability(model, solver, world_count)

    # -----------------------------------------------------------------------
    # T3: Isolation (requires settled state)
    # -----------------------------------------------------------------------
    if t2_pass:
        t3_pass = test_isolation(model, solver, world_count, settled_state)
    else:
        print(f"\n  T3 SKIP: T2 failed (no stable settled state)")
        t3_pass = False

    # -----------------------------------------------------------------------
    # T4: Reset (requires settled state)
    # -----------------------------------------------------------------------
    if t2_pass:
        t4_pass = test_reset(model, solver, world_count, settled_state)
    else:
        print(f"\n  T4 SKIP: T2 failed")
        t4_pass = False

    # -----------------------------------------------------------------------
    # T5: Performance
    # -----------------------------------------------------------------------
    perf_metrics = test_performance(model, solver, world_count)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    results = {
        "T1_construction": "PASS" if t1_pass else "FAIL",
        "T2_stability": "PASS" if t2_pass else "FAIL",
        "T3_isolation": "PASS" if t3_pass else "FAIL",
        "T4_reset": "PASS" if t4_pass else "FAIL",
        "performance": perf_metrics,
    }

    print(f"\n{'#'*60}")
    print(f"  SUMMARY")
    print(f"{'#'*60}")
    all_pass = t1_pass and t2_pass and t3_pass and t4_pass
    for k, v in results.items():
        if k != "performance":
            status = v
            print(f"  {k}: {status}")
    print(f"  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    print(f"{'#'*60}\n")

    # Save results
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                           "data", f"newton_multiworld_w{world_count}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved: {out_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
