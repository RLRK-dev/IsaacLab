"""Newton Phase 5: Particle-Ground Collision Tuning

Phase 4 finding: Particles fly through ground plane, accumulating extreme positions.
Diagnosis (historical; the diagnostic script diag_particle_q_layout.py was deleted under the
kinematic-removal directive — evidence = git blob 0ef8a4b31249): particle z values range from
-121 to +223, alternating chaotically. Ground collision with particle_ke=50000 is insufficient.

This script systematically tests particle-ground collision parameters:
1. Ground collision basic test (no arm, no fingers)
2. Parameter sweep: ke, kd, mu, DT
3. Alternative: explicit ground box collision shape
4. Full system test with optimal parameters

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_phase5_ground_collision.py
"""

import time
import sys
import numpy as np
import warp as wp
import newton
from newton.solvers import SolverSemiImplicit

DEVICE = "cuda:0"

# Cable parameters
CABLE_SEGMENTS = 20
CABLE_SEG_LEN = 0.015
CABLE_MASS = 0.005
CABLE_RADIUS = 0.005
CABLE_KE = 1.0e4
CABLE_KD = 10.0


def add_particle_chain_cable(builder, start_pos, direction=(1.0, 0.0, 0.0),
                              n_segments=CABLE_SEGMENTS):
    """Add a particle chain cable."""
    dx = direction[0] * CABLE_SEG_LEN
    dy = direction[1] * CABLE_SEG_LEN
    dz = direction[2] * CABLE_SEG_LEN

    particles = []
    for i in range(n_segments + 1):
        pos = (
            start_pos[0] + i * dx,
            start_pos[1] + i * dy,
            start_pos[2] + i * dz,
        )
        p = builder.add_particle(
            pos=pos,
            vel=(0.0, 0.0, 0.0),
            mass=CABLE_MASS,
            radius=CABLE_RADIUS,
        )
        particles.append(p)

    for i in range(n_segments):
        builder.add_spring(
            i=particles[i], j=particles[i + 1],
            ke=CABLE_KE, kd=CABLE_KD, control=0.0,
        )
    return particles


def sim_step_with_fk(model, state, state_out, solver, control, contacts, dt):
    """Step with FK fix for SemiImplicit solver."""
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, dt)
    return state_out, state


# ── Test 1: Basic ground collision sweep ──────────────────────────────
def test_ground_collision_sweep():
    """Test particle settling on ground with different parameters."""
    print("=" * 60)
    print("TEST 1: Particle-Ground Collision Parameter Sweep")
    print("=" * 60)

    configs = [
        # (dt, p_ke, p_kd, p_mu, ground_ke, label)
        (1/480,  5e4, 100, 0.8, None, "baseline (Phase4)"),
        (1/480,  5e5, 1000, 0.8, None, "ke=5e5 kd=1000"),
        (1/480,  5e6, 5000, 0.8, None, "ke=5e6 kd=5000"),
        (1/960,  5e4, 100, 0.8, None, "dt=1/960 baseline ke"),
        (1/960,  5e5, 1000, 0.8, None, "dt=1/960 ke=5e5"),
        (1/1920, 5e4, 100, 0.8, None, "dt=1/1920 baseline ke"),
        # ground_ke variants removed — add_ground_plane() does not accept ke
    ]

    results = []
    for dt, p_ke, p_kd, p_mu, g_ke, label in configs:
        builder = newton.ModelBuilder(gravity=-9.81)
        builder.add_ground_plane()

        cable = add_particle_chain_cable(builder, start_pos=(-0.15, 0.0, 0.10))

        model = builder.finalize(device=DEVICE)
        model.particle_ke = p_ke
        model.particle_kd = p_kd
        model.particle_mu = p_mu

        state = model.state()
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        steps = int(2.0 / dt)  # 2 seconds
        nan_detected = False
        t0 = time.time()
        for i in range(steps):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, dt)
            state, state_out = state_out, state

            pq = state.particle_q.numpy()
            if np.any(np.isnan(pq)):
                nan_detected = True
                print(f"  [{label}] NaN at step {i}")
                break

        elapsed = time.time() - t0
        pq = state.particle_q.numpy()
        z_vals = pq[:, 2]
        mean_z = np.mean(z_vals)
        min_z = np.min(z_vals)
        max_z = np.max(z_vals)
        std_z = np.std(z_vals)
        on_ground = abs(mean_z) < 0.05 and std_z < 0.02 and not nan_detected

        status = "NaN!" if nan_detected else ("GROUND" if on_ground else "FLYING")
        print(f"  [{label}] dt={dt:.6f}: mean_z={mean_z:.4f}, "
              f"std={std_z:.4f}, range=[{min_z:.4f},{max_z:.4f}] "
              f"→ {status} ({elapsed:.1f}s)")

        results.append({
            "label": label,
            "dt": dt,
            "p_ke": p_ke,
            "p_kd": p_kd,
            "mean_z": mean_z,
            "std_z": std_z,
            "min_z": min_z,
            "max_z": max_z,
            "on_ground": on_ground,
            "nan": nan_detected,
        })

    # Find best configuration
    settled = [r for r in results if r["on_ground"]]
    if settled:
        best = min(settled, key=lambda r: r["std_z"])
        print(f"\n  BEST: {best['label']} (std={best['std_z']:.6f})")
    else:
        closest = min(results, key=lambda r: abs(r["mean_z"]) if not r["nan"] else 999)
        print(f"\n  No settling found. Closest: {closest['label']} (mean_z={closest['mean_z']:.4f})")

    return results


# ── Test 2: Ground box instead of plane ───────────────────────────────
def test_ground_box():
    """Test using a ground box shape instead of ground plane."""
    print()
    print("=" * 60)
    print("TEST 2: Ground Box Shape (alternative to ground plane)")
    print("=" * 60)

    dt = 1.0 / 480.0

    for ke, kd, label in [(5e4, 100, "baseline"), (5e5, 1000, "high"), (5e6, 5000, "very high")]:
        builder = newton.ModelBuilder(gravity=-9.81)
        # NO ground plane — use a kinematic box body instead
        ground = builder.add_link(
            xform=wp.transform((0.0, 0.0, -0.05), wp.quat_identity()),
            mass=0.0,
            is_kinematic=True,
        )
        builder.add_shape_box(
            body=ground,
            hx=2.0, hy=2.0, hz=0.05,
            cfg=newton.ModelBuilder.ShapeConfig(mu=0.8, ke=ke, kd=kd, density=0.0),
        )

        cable = add_particle_chain_cable(builder, start_pos=(-0.15, 0.0, 0.10))

        model = builder.finalize(device=DEVICE)
        model.particle_ke = ke
        model.particle_kd = kd
        model.particle_mu = 0.8

        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        steps = int(2.0 / dt)
        nan_detected = False
        for i in range(steps):
            state.clear_forces()
            newton.eval_fk(model, state.joint_q, state.joint_qd, state)
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, dt)
            state, state_out = state_out, state

            pq = state.particle_q.numpy()
            if np.any(np.isnan(pq)):
                nan_detected = True
                print(f"  [box {label}] NaN at step {i}")
                break

        pq = state.particle_q.numpy()
        z_vals = pq[:, 2]
        mean_z = np.mean(z_vals)
        std_z = np.std(z_vals)
        on_ground = abs(mean_z) < 0.05 and std_z < 0.02 and not nan_detected

        status = "NaN!" if nan_detected else ("GROUND" if on_ground else "FLYING")
        print(f"  [box {label}] ke={ke:.0e} kd={kd}: mean_z={mean_z:.4f}, "
              f"std={std_z:.4f}, range=[{np.min(z_vals):.4f},{np.max(z_vals):.4f}] → {status}")


# ── Test 3: Particle-particle spring analysis ─────────────────────────
def test_particle_stability():
    """Test if spring forces cause instability (energy gain)."""
    print()
    print("=" * 60)
    print("TEST 3: Particle Stability (spring energy analysis)")
    print("=" * 60)

    dt = 1.0 / 480.0

    builder = newton.ModelBuilder(gravity=-9.81)
    builder.add_ground_plane()

    # Single particle (no spring) as control
    builder.add_particle(
        pos=(0.5, 0.0, 0.10), vel=(0.0, 0.0, 0.0),
        mass=CABLE_MASS, radius=CABLE_RADIUS,
    )

    cable = add_particle_chain_cable(builder, start_pos=(-0.15, 0.0, 0.10))

    model = builder.finalize(device=DEVICE)
    model.particle_ke = 5e4
    model.particle_kd = 100.0
    model.particle_mu = 0.8

    state = model.state()
    contacts = model.contacts()
    control = model.control()
    solver = SolverSemiImplicit(model)
    state_out = model.state()

    print(f"  Single particle at index 0, cable at indices 1-21")
    print(f"  Tracking z and velocity over 2 seconds...")

    for i in range(960):
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, dt)
        state, state_out = state_out, state

        if i % 120 == 0:
            pq = state.particle_q.numpy()
            pqd = state.particle_qd.numpy()
            single_z = pq[0, 2]
            single_vz = pqd[0, 2]
            cable_mean_z = np.mean(pq[1:, 2])
            cable_max_vz = np.max(np.abs(pqd[1:, 2]))
            print(f"  Step {i:4d}: single_z={single_z:.4f} vz={single_vz:.4f} | "
                  f"cable_mean_z={cable_mean_z:.4f} cable_max_vz={cable_max_vz:.4f}")

    pq = state.particle_q.numpy()
    pqd = state.particle_qd.numpy()
    print(f"\n  Final single particle: z={pq[0,2]:.6f}, vz={pqd[0,2]:.6f}")
    print(f"  Final cable mean z: {np.mean(pq[1:, 2]):.6f}")
    print(f"  Final cable z range: [{np.min(pq[1:, 2]):.6f}, {np.max(pq[1:, 2]):.6f}]")
    print(f"  Final cable max |vz|: {np.max(np.abs(pqd[1:, 2])):.6f}")

    single_ok = abs(pq[0, 2]) < 0.05
    cable_ok = abs(np.mean(pq[1:, 2])) < 0.05
    print(f"\n  Single particle settled: {'YES' if single_ok else 'NO'}")
    print(f"  Cable settled: {'YES' if cable_ok else 'NO'}")
    if not cable_ok and single_ok:
        print("  → Springs are causing instability (energy injection)")


# ── Test 4: Reduced DT sweep with energy tracking ────────────────────
def test_dt_sweep():
    """Sweep timestep to find stable DT for particle chain + ground."""
    print()
    print("=" * 60)
    print("TEST 4: DT Sweep for Stable Cable Settling")
    print("=" * 60)

    for dt in [1/480, 1/960, 1/1920, 1/3840, 1/7680]:
        builder = newton.ModelBuilder(gravity=-9.81)
        builder.add_ground_plane()

        cable = add_particle_chain_cable(builder, start_pos=(-0.15, 0.0, 0.10))

        model = builder.finalize(device=DEVICE)
        model.particle_ke = 5e4
        model.particle_kd = 100.0
        model.particle_mu = 0.8

        state = model.state()
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        steps = int(2.0 / dt)  # 2 seconds
        nan_detected = False
        t0 = time.time()
        for i in range(steps):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, dt)
            state, state_out = state_out, state

            if np.any(np.isnan(state.particle_q.numpy())):
                nan_detected = True
                break

        elapsed = time.time() - t0
        pq = state.particle_q.numpy()
        z_vals = pq[:, 2]
        mean_z = np.mean(z_vals)
        std_z = np.std(z_vals)
        on_ground = abs(mean_z) < 0.05 and std_z < 0.02 and not nan_detected

        status = "NaN!" if nan_detected else ("SETTLED" if on_ground else f"FLYING(z={mean_z:.1f})")
        print(f"  dt=1/{int(1/dt):5d}: mean_z={mean_z:8.4f}, std={std_z:8.4f} → {status} ({elapsed:.2f}s)")

        if on_ground:
            print(f"  ★ Stable at dt=1/{int(1/dt)}!")
            break


# ── Test 5: Reduced spring stiffness ─────────────────────────────────
def test_spring_stiffness_sweep():
    """Test if reducing cable spring stiffness helps stability."""
    print()
    print("=" * 60)
    print("TEST 5: Cable Spring Stiffness Sweep")
    print("=" * 60)

    dt = 1.0 / 480.0

    for cable_ke, cable_kd in [(1e4, 10), (1e3, 5), (1e2, 2), (5e1, 1)]:
        builder = newton.ModelBuilder(gravity=-9.81)
        builder.add_ground_plane()

        particles = []
        for i in range(CABLE_SEGMENTS + 1):
            p = builder.add_particle(
                pos=(i * CABLE_SEG_LEN, 0.0, 0.10),
                vel=(0.0, 0.0, 0.0),
                mass=CABLE_MASS, radius=CABLE_RADIUS,
            )
            particles.append(p)
        for i in range(CABLE_SEGMENTS):
            builder.add_spring(i=particles[i], j=particles[i + 1],
                               ke=cable_ke, kd=cable_kd, control=0.0)

        model = builder.finalize(device=DEVICE)
        model.particle_ke = 5e4
        model.particle_kd = 100.0
        model.particle_mu = 0.8

        state = model.state()
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        steps = int(2.0 / dt)
        nan_detected = False
        for i in range(steps):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, dt)
            state, state_out = state_out, state

            if np.any(np.isnan(state.particle_q.numpy())):
                nan_detected = True
                break

        pq = state.particle_q.numpy()
        z_vals = pq[:, 2]
        mean_z = np.mean(z_vals)
        std_z = np.std(z_vals)
        on_ground = abs(mean_z) < 0.05 and std_z < 0.02 and not nan_detected

        status = "NaN!" if nan_detected else ("SETTLED" if on_ground else f"FLYING(z={mean_z:.1f})")
        print(f"  spring_ke={cable_ke:.0e} kd={cable_kd}: mean_z={mean_z:8.4f}, std={std_z:8.4f} → {status}")


# ── Test 6: Increased mass + lower stiffness ──────────────────────────
def test_mass_sweep():
    """Test heavier particles for better ground collision response."""
    print()
    print("=" * 60)
    print("TEST 6: Particle Mass Sweep")
    print("=" * 60)

    dt = 1.0 / 480.0

    for mass in [0.005, 0.01, 0.05, 0.1, 0.5]:
        builder = newton.ModelBuilder(gravity=-9.81)
        builder.add_ground_plane()

        particles = []
        for i in range(CABLE_SEGMENTS + 1):
            p = builder.add_particle(
                pos=(i * CABLE_SEG_LEN, 0.0, 0.10),
                vel=(0.0, 0.0, 0.0),
                mass=mass, radius=CABLE_RADIUS,
            )
            particles.append(p)
        for i in range(CABLE_SEGMENTS):
            builder.add_spring(i=particles[i], j=particles[i + 1],
                               ke=CABLE_KE, kd=CABLE_KD, control=0.0)

        model = builder.finalize(device=DEVICE)
        model.particle_ke = 5e4
        model.particle_kd = 100.0
        model.particle_mu = 0.8

        state = model.state()
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        steps = int(2.0 / dt)
        nan_detected = False
        for i in range(steps):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, dt)
            state, state_out = state_out, state

            if np.any(np.isnan(state.particle_q.numpy())):
                nan_detected = True
                break

        pq = state.particle_q.numpy()
        z_vals = pq[:, 2]
        mean_z = np.mean(z_vals)
        std_z = np.std(z_vals)
        on_ground = abs(mean_z) < 0.05 and std_z < 0.02 and not nan_detected

        status = "NaN!" if nan_detected else ("SETTLED" if on_ground else f"FLYING(z={mean_z:.1f})")
        print(f"  mass={mass:.3f}: mean_z={mean_z:8.4f}, std={std_z:8.4f} → {status}")


# ── Test 7: No collide() — pure free-fall check ──────────────────────
def test_free_fall():
    """Test particle free fall WITHOUT collision to check basic physics."""
    print()
    print("=" * 60)
    print("TEST 7: Free Fall (no collision) — physics sanity check")
    print("=" * 60)

    dt = 1.0 / 480.0

    # Single particle free fall
    builder = newton.ModelBuilder(gravity=-9.81)
    # NO ground plane
    builder.add_particle(
        pos=(0.0, 0.0, 1.0), vel=(0.0, 0.0, 0.0),
        mass=0.005, radius=0.005,
    )

    model = builder.finalize(device=DEVICE)
    state = model.state()
    contacts = model.contacts()
    control = model.control()
    solver = SolverSemiImplicit(model)
    state_out = model.state()

    # Expected: z(t) = 1.0 - 0.5 * 9.81 * t^2
    for i in range(480):
        state.clear_forces()
        # No collide — just gravity
        solver.step(state, state_out, control, contacts, dt)
        state, state_out = state_out, state

        if i % 48 == 0:
            t = (i + 1) * dt
            pq = state.particle_q.numpy()
            z_actual = pq[0, 2]
            z_expected = 1.0 - 0.5 * 9.81 * t * t
            print(f"  t={t:.3f}s: z_actual={z_actual:.6f}, z_expected={z_expected:.6f}, "
                  f"diff={abs(z_actual - z_expected):.6e}")


# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("Newton Phase 5: Particle-Ground Collision Tuning")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print()

    test_free_fall()
    test_particle_stability()
    test_ground_collision_sweep()
    test_ground_box()
    test_dt_sweep()
    test_spring_stiffness_sweep()
    test_mass_sweep()

    print()
    print("=" * 60)
    print("PHASE 5 GROUND COLLISION TUNING COMPLETE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
