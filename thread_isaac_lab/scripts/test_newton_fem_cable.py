"""Newton FEM (Soft Body) Cable + Kinematic Gripper Test

Tests whether VBD solver can handle FEM soft body + kinematic body CONTACT
without NaN. Previous test showed VBD + rod cable + kinematic body contact → NaN.
FEM soft body uses particle-based contact which may avoid this issue.

Tests:
1. FEM cable settling on ground
2. Kinematic gripper approach (no contact)
3. Kinematic gripper grip (squeeze contact)
4. N-dependency for FEM cable

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_fem_cable.py
"""

import time
import sys

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverVBD

# ── Configuration ────────────────────────────────────────────────────
DEVICE = "cuda:1"  # Blackwell GPU

# FEM cable parameters (elongated soft grid)
# Cross-section: 2x2 cells × 5mm = 10mm × 10mm
# Length: 20 cells × 15mm = 300mm
CABLE_DIM_X = 2
CABLE_DIM_Y = 20
CABLE_DIM_Z = 2
CABLE_CELL_X = 0.005  # 5mm
CABLE_CELL_Y = 0.015  # 15mm
CABLE_CELL_Z = 0.005  # 5mm

# Material (soft rubber-like)
CABLE_DENSITY = 1100.0
CABLE_K_MU = 1.0e4       # Lamé first parameter (soft)
CABLE_K_LAMBDA = 1.0e4   # Lamé second parameter
CABLE_K_DAMP = 0.1
CABLE_PARTICLE_RADIUS = 0.005  # 5mm contact radius

# Physics
DT = 1.0 / 480.0
SETTLE_STEPS = 960   # 2 seconds
VBD_ITERATIONS = 20

# Gripper
FINGER_RADIUS = 0.006   # 6mm
FINGER_HALF_H = 0.02    # 20mm half-height
CABLE_START_Z = 0.20    # drop from 20cm


# ── Helpers ──────────────────────────────────────────────────────────
def build_fem_cable_world():
    """Build a world with a FEM soft body cable."""
    b = newton.ModelBuilder()
    b.add_soft_grid(
        pos=wp.vec3(0.0, 0.0, CABLE_START_Z),
        rot=wp.quat_identity(),
        vel=wp.vec3(0.0, 0.0, 0.0),
        dim_x=CABLE_DIM_X,
        dim_y=CABLE_DIM_Y,
        dim_z=CABLE_DIM_Z,
        cell_x=CABLE_CELL_X,
        cell_y=CABLE_CELL_Y,
        cell_z=CABLE_CELL_Z,
        density=CABLE_DENSITY,
        k_mu=CABLE_K_MU,
        k_lambda=CABLE_K_LAMBDA,
        k_damp=CABLE_K_DAMP,
        particle_radius=CABLE_PARTICLE_RADIUS,
    )
    return b


# ── Test 1: FEM cable settling ───────────────────────────────────────
def test_fem_cable_settling():
    """Test FEM cable settles correctly under gravity."""
    print("=" * 60)
    print("TEST 1: FEM cable settling on ground (VBD)")
    print("=" * 60)

    builder = newton.ModelBuilder()
    builder.add_ground_plane()

    cable_builder = build_fem_cable_world()
    builder.add_builder(cable_builder)
    builder.color()

    model = builder.finalize(device=DEVICE)
    model.soft_contact_ke = 1.0e3
    model.soft_contact_kd = 10.0
    model.soft_contact_mu = 0.8

    state = model.state()
    contacts = model.contacts()
    control = model.control()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    state_out = model.state()

    t0 = time.time()
    for _ in range(SETTLE_STEPS):
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state
    elapsed = time.time() - t0

    particle_q = state.particle_q.numpy()
    n_particles = len(particle_q)
    z_values = particle_q[:, 2]
    mean_z = np.mean(z_values)
    max_z = np.max(z_values)
    min_z = np.min(z_values)
    has_nan = np.any(np.isnan(z_values))

    print(f"  Particles: {n_particles}")
    print(f"  Mean z: {mean_z:.6f}")
    print(f"  Range:  [{min_z:.6f}, {max_z:.6f}]")
    print(f"  Stable (no NaN): {'YES' if not has_nan else 'NO'}")
    print(f"  Time: {elapsed:.2f}s")

    near_ground = mean_z < 0.05
    passed = near_ground and not has_nan
    print(f"\n  >> FEM cable settling: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Test 2: FEM cable + kinematic gripper approach ────────────────────
def test_fem_gripper_approach():
    """Test FEM cable remains stable with nearby kinematic bodies."""
    print()
    print("=" * 60)
    print("TEST 2: FEM cable + kinematic gripper approach (VBD)")
    print("=" * 60)

    builder = newton.ModelBuilder()
    builder.add_ground_plane()

    # Add FEM cable
    cable_builder = build_fem_cable_world()
    builder.add_builder(cable_builder)

    # Add kinematic finger bodies (far from cable initially)
    lf = builder.add_link(
        xform=wp.transform((-0.10, 0.15, CABLE_START_Z), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(
        body=lf, radius=FINGER_RADIUS, half_height=FINGER_HALF_H,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=500.0, kd=50.0, density=0.0),
    )

    rf = builder.add_link(
        xform=wp.transform((0.10, 0.15, CABLE_START_Z), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(
        body=rf, radius=FINGER_RADIUS, half_height=FINGER_HALF_H,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=500.0, kd=50.0, density=0.0),
    )

    builder.color()
    model = builder.finalize(device=DEVICE)
    model.soft_contact_ke = 1.0e3
    model.soft_contact_kd = 10.0
    model.soft_contact_mu = 0.8

    state = model.state()
    contacts = model.contacts()
    control = model.control()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    state_out = model.state()

    n_particles = state.particle_q.numpy().shape[0]
    LF_IDX = 0  # first rigid body
    RF_IDX = 1  # second rigid body

    # Phase 1: Settle cable
    print("  Phase 1: Settling cable...")
    for _ in range(SETTLE_STEPS):
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state

    pq = state.particle_q.numpy()
    cable_mean_z = np.mean(pq[:, 2])
    has_nan = np.any(np.isnan(pq))
    print(f"  After settle: cable mean z={cable_mean_z:.6f}, NaN={has_nan}")

    if has_nan:
        print(f"\n  >> FEM gripper approach: FAIL (NaN during settle)")
        return False

    # Phase 2: Move fingers closer (approach)
    print("  Phase 2: Moving fingers closer...")
    approach_steps = 480
    stable = True
    for i in range(approach_steps):
        t = (i + 1) / approach_steps
        x = 0.10 + (0.02 - 0.10) * t   # 100mm → 20mm (cable at x≈0)

        q = state_out.body_q.numpy()
        q[LF_IDX][:3] = [-x, 0.15, 0.02]  # fingers near ground
        q[LF_IDX][3:] = [0, 0, 0, 1]
        q[RF_IDX][:3] = [x, 0.15, 0.02]
        q[RF_IDX][3:] = [0, 0, 0, 1]
        state_out.body_q.assign(q)

        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state

        pq = state.particle_q.numpy()
        if np.any(np.isnan(pq)):
            stable = False
            print(f"  NaN at approach step {i}, x=±{x:.4f}")
            break

    if stable:
        pq = state.particle_q.numpy()
        print(f"  After approach: cable mean z={np.mean(pq[:, 2]):.6f}")

    passed = not has_nan and stable
    print(f"\n  >> FEM gripper approach: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Test 3: FEM cable grip (squeeze contact) ──────────────────────────
def test_fem_grip():
    """Test kinematic grippers can squeeze FEM cable without NaN."""
    print()
    print("=" * 60)
    print("TEST 3: FEM cable grip / squeeze (VBD) ★KEY TEST★")
    print("=" * 60)

    builder = newton.ModelBuilder()
    builder.add_ground_plane()

    # FEM cable at center, slightly raised
    cable_builder = build_fem_cable_world()
    builder.add_builder(cable_builder)

    # Kinematic fingers at cable center (y≈0.15)
    lf = builder.add_link(
        xform=wp.transform((-0.05, 0.15, CABLE_START_Z), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(
        body=lf, radius=FINGER_RADIUS, half_height=FINGER_HALF_H,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=1000.0, kd=100.0, density=0.0),
    )

    rf = builder.add_link(
        xform=wp.transform((0.05, 0.15, CABLE_START_Z), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(
        body=rf, radius=FINGER_RADIUS, half_height=FINGER_HALF_H,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=1000.0, kd=100.0, density=0.0),
    )

    builder.color()
    model = builder.finalize(device=DEVICE)
    model.soft_contact_ke = 1.0e3
    model.soft_contact_kd = 10.0
    model.soft_contact_mu = 1.0

    state = model.state()
    contacts = model.contacts()
    control = model.control()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    state_out = model.state()

    LF_IDX = 0
    RF_IDX = 1

    # Phase 1: Settle cable
    print("  Phase 1: Settling cable...")
    for _ in range(SETTLE_STEPS):
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state

    pq = state.particle_q.numpy()
    settle_z = np.mean(pq[:, 2])
    print(f"  After settle: cable mean z={settle_z:.6f}")

    if np.any(np.isnan(pq)):
        print(f"\n  >> FEM grip: FAIL (NaN during settle)")
        return False

    # Phase 2: Close fingers to squeeze cable
    # Cable cross-section is ~10mm wide (x direction)
    # Fingers approach from ±50mm to ±3mm (penetrating cable)
    print("  Phase 2: Closing fingers onto cable...")
    grip_steps = 960  # 2 seconds
    squeeze_stable = True
    grip_log = []

    for i in range(grip_steps):
        t = (i + 1) / grip_steps
        # Squeeze from ±50mm to ±3mm (cable half-width ≈ 5mm)
        x = 0.05 + (0.003 - 0.05) * t
        fz = settle_z  # fingers at cable height

        q = state_out.body_q.numpy()
        q[LF_IDX][:3] = [-x, 0.15, fz]
        q[LF_IDX][3:] = [0, 0, 0, 1]
        q[RF_IDX][:3] = [x, 0.15, fz]
        q[RF_IDX][3:] = [0, 0, 0, 1]
        state_out.body_q.assign(q)

        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state

        pq = state.particle_q.numpy()
        if np.any(np.isnan(pq)):
            squeeze_stable = False
            print(f"  NaN at grip step {i}/{grip_steps}, x=±{x:.4f}m")
            break

        if i % 240 == 0 or i == grip_steps - 1:
            center_z = np.mean(pq[:, 2])
            center_x_range = np.max(pq[:, 0]) - np.min(pq[:, 0])
            grip_log.append((i, x, center_z, center_x_range))
            print(f"  Step {i:4d}: x=±{x:.4f}m, cable z={center_z:.4f}, x_range={center_x_range:.4f}")

    if squeeze_stable:
        # Phase 3: Lift while gripping
        print("  Phase 3: Lifting cable with grip...")
        lift_steps = 480
        lift_stable = True
        for i in range(lift_steps):
            t = (i + 1) / lift_steps
            lift_z = settle_z + 0.10 * t  # lift 10cm

            q = state_out.body_q.numpy()
            q[LF_IDX][:3] = [-0.003, 0.15, lift_z]
            q[LF_IDX][3:] = [0, 0, 0, 1]
            q[RF_IDX][:3] = [0.003, 0.15, lift_z]
            q[RF_IDX][3:] = [0, 0, 0, 1]
            state_out.body_q.assign(q)

            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state

            pq = state.particle_q.numpy()
            if np.any(np.isnan(pq)):
                lift_stable = False
                print(f"  NaN at lift step {i}, z={lift_z:.4f}")
                break

        if lift_stable:
            pq = state.particle_q.numpy()
            final_z = np.mean(pq[:, 2])
            lifted = final_z > settle_z + 0.02  # lifted at least 2cm
            print(f"  After lift: cable mean z={final_z:.4f} (was {settle_z:.4f})")
            print(f"  Cable lifted: {'YES' if lifted else 'NO'}")
    else:
        lift_stable = False
        lifted = False

    passed = squeeze_stable and lift_stable
    print(f"\n  >> FEM grip: {'PASS' if passed else 'FAIL'}")
    if passed and lifted:
        print("  ★ FEM cable grip+lift SUCCESS — VBD contact NaN resolved! ★")
    return passed


# ── Test 4: N-dependency for FEM cable ────────────────────────────────
def test_fem_n_dependency():
    """Test N-dependency for FEM cable with VBD."""
    print()
    print("=" * 60)
    print("TEST 4: N-dependency for FEM cable (VBD)")
    print("=" * 60)

    results = {}
    for N in [1, 3]:
        main_builder = newton.ModelBuilder()
        main_builder.add_ground_plane()

        cable_builder = build_fem_cable_world()
        main_builder.replicate(cable_builder, world_count=N)
        main_builder.color()

        model = main_builder.finalize(device=DEVICE)
        model.soft_contact_ke = 1.0e3
        model.soft_contact_kd = 10.0
        model.soft_contact_mu = 0.8

        state = model.state()
        contacts = model.contacts()
        control = model.control()
        solver = SolverVBD(model, iterations=VBD_ITERATIONS)
        state_out = model.state()

        t0 = time.time()
        for _ in range(SETTLE_STEPS):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state
        elapsed = time.time() - t0

        pq = state.particle_q.numpy()
        # Get particles from world 0 only
        n_particles_per_world = len(pq) // N
        world0_z = np.mean(pq[:n_particles_per_world, 2])
        results[N] = world0_z
        print(f"  N={N}: world0 mean_z = {world0_z:.10f}  ({elapsed:.2f}s)")

    # Compare
    print()
    ref = results[1]
    diff = abs(results[3] - ref)
    status = "IDENTICAL" if diff == 0.0 else f"diff={diff:.2e}"
    passed = diff < 1e-6
    print(f"  N=3 vs N=1: {status} {'PASS' if passed else 'FAIL'}")
    print(f"\n  >> FEM N-dependency: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print(f"Newton FEM Cable + Kinematic Gripper Test")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"Cable: {CABLE_DIM_X}x{CABLE_DIM_Y}x{CABLE_DIM_Z} cells "
          f"({CABLE_DIM_X * CABLE_CELL_X * 1000:.0f}mm x "
          f"{CABLE_DIM_Y * CABLE_CELL_Y * 1000:.0f}mm x "
          f"{CABLE_DIM_Z * CABLE_CELL_Z * 1000:.0f}mm)")
    print()

    results = {}
    results["fem_settling"] = test_fem_cable_settling()
    results["fem_approach"] = test_fem_gripper_approach()
    results["fem_grip"] = test_fem_grip()
    results["fem_n_dep"] = test_fem_n_dependency()

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, result in results.items():
        print(f"  {name:30s}: {'PASS' if result else 'FAIL'}")
    print(f"\n  Total: {passed}/{total} passed")

    print()
    if results["fem_grip"]:
        print("KEY FINDING: FEM soft body cable resolves VBD contact NaN!")
        print("  Rod cable (add_rod) → NaN on kinematic contact")
        print("  FEM cable (add_soft_grid) → STABLE kinematic contact")
        print("  → Use FEM cable for THREAD Newton integration")
    else:
        print("KEY FINDING: FEM cable also has VBD contact issues.")
        print("  Need alternative approach (particle chain + Featherstone)")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
