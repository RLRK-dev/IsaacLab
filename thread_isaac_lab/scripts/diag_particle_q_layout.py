"""Diagnostic: Check particle_q layout and intermediate cable_center_z values.

Purpose: Investigate why Test 4 (Phase 4) reported cable_center_z=254-256
during lift phase while final value was 49.3.

Key questions:
1. Is particle_q shape (n_particles, 3) or flat?
2. Does eval_fk() overwrite kinematic body positions?
3. What happens to center particle z during settle/close/lift?
"""

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverSemiImplicit

DEVICE = "cuda:0"
DT = 1.0 / 480.0
GRAVITY = -9.81
CABLE_SEGMENTS = 20
CABLE_SEG_LEN = 0.015
CABLE_MASS = 0.005
CABLE_RADIUS = 0.005
CABLE_KE = 1.0e4
CABLE_KD = 10.0
PARTICLE_CONTACT_KE = 5.0e4
PARTICLE_CONTACT_KD = 100.0
SETTLE_STEPS = 960


def sim_step_with_fk(model, state, state_out, solver, control, contacts):
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, DT)
    return state_out, state


def main():
    print("=== Diagnostic: particle_q layout & cable_center_z ===\n")

    builder = newton.ModelBuilder(gravity=GRAVITY)
    builder.add_ground_plane()

    # Cable particles
    particles = []
    for i in range(CABLE_SEGMENTS + 1):
        p = builder.add_particle(
            pos=(i * CABLE_SEG_LEN, 0.0, 0.10),
            vel=(0.0, 0.0, 0.0),
            mass=CABLE_MASS,
            radius=CABLE_RADIUS,
        )
        particles.append(p)

    for i in range(CABLE_SEGMENTS):
        builder.add_spring(i=particles[i], j=particles[i + 1], ke=CABLE_KE, kd=CABLE_KD, control=0.0)

    # Kinematic fingers (same as Test 4)
    lf = builder.add_link(
        xform=wp.transform((-0.05, 0.0, 0.15), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(
        body=lf, radius=0.006, half_height=0.02,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=2000.0, kd=200.0, density=0.0),
    )
    rf = builder.add_link(
        xform=wp.transform((0.05, 0.0, 0.15), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(
        body=rf, radius=0.006, half_height=0.02,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=2000.0, kd=200.0, density=0.0),
    )

    model = builder.finalize(device=DEVICE)
    model.particle_ke = PARTICLE_CONTACT_KE
    model.particle_kd = PARTICLE_CONTACT_KD
    model.particle_mu = 1.0

    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)

    # === Part 1: particle_q layout ===
    pq = state.particle_q.numpy()
    print(f"[LAYOUT] particle_q.shape = {pq.shape}")
    print(f"[LAYOUT] particle_q.dtype = {pq.dtype}")
    print(f"[LAYOUT] model.particle_count = {model.particle_count}")
    print(f"[LAYOUT] CABLE_SEGMENTS = {CABLE_SEGMENTS}, n_particles = {CABLE_SEGMENTS + 1}")
    print(f"[LAYOUT] Center index = CABLE_SEGMENTS // 2 = {CABLE_SEGMENTS // 2}")

    if len(pq.shape) == 2:
        print(f"[LAYOUT] 2D array: {pq.shape[0]} particles x {pq.shape[1]} components")
        for i in range(min(pq.shape[0], 25)):
            print(f"  pq[{i:2d}] = [{pq[i][0]:.6f}, {pq[i][1]:.6f}, {pq[i][2]:.6f}]")
    elif len(pq.shape) == 1:
        print(f"[LAYOUT] 1D flat array: length={pq.shape[0]}")
        print(f"  If 3-component: {pq.shape[0]//3} particles")
        print(f"  If 7-component: {pq.shape[0]//7} particles")
        for i in range(min(5, CABLE_SEGMENTS + 1)):
            print(f"  Particle {i} (3-comp): [{pq[i*3]:.6f}, {pq[i*3+1]:.6f}, {pq[i*3+2]:.6f}]")

    # === Part 2: body_q layout ===
    bq = state.body_q.numpy()
    print(f"\n[BODY_Q] body_q.shape = {bq.shape}")
    print(f"[BODY_Q] model.body_count = {model.body_count}")
    for i in range(min(bq.shape[0], 5)):
        print(f"  bq[{i}] = {bq[i]}")
    print(f"  LF (idx={bq.shape[0]-2}) = {bq[-2]}")
    print(f"  RF (idx={bq.shape[0]-1}) = {bq[-1]}")

    # === Part 3: eval_fk effect on kinematic bodies ===
    print("\n[FK TEST] Setting LF to [-0.008, 0, 0.12], RF to [0.008, 0, 0.12]...")
    bq = state.body_q.numpy()
    bq[-2][:3] = [-0.008, 0.0, 0.12]
    bq[-2][3:] = [0, 0, 0, 1]
    bq[-1][:3] = [0.008, 0.0, 0.12]
    bq[-1][3:] = [0, 0, 0, 1]
    state.body_q.assign(bq)

    print(f"[FK TEST] Before eval_fk: LF={state.body_q.numpy()[-2][:3]}")

    newton.eval_fk(model, state.joint_q, state.joint_qd, state)

    bq_after = state.body_q.numpy()
    print(f"[FK TEST] After eval_fk:  LF={bq_after[-2][:3]}")
    print(f"[FK TEST] Overwritten by eval_fk? {not np.allclose(bq_after[-2][:3], [-0.008, 0.0, 0.12])}")

    # === Part 4: Reproduce Test 4 with detailed logging ===
    print("\n" + "=" * 60)
    print("Reproducing Test 4 lift with detailed particle logging")
    print("=" * 60)

    contacts = model.contacts()
    control = model.control()
    solver = SolverSemiImplicit(model)
    state_out = model.state()

    # Settle
    print("  Settling cable...")
    for i in range(SETTLE_STEPS):
        state, state_out = sim_step_with_fk(model, state, state_out, solver, control, contacts)

    pq = state.particle_q.numpy()
    if len(pq.shape) == 2:
        cable_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
    else:
        cable_z = np.mean([pq[i * 3 + 2] for i in range(CABLE_SEGMENTS + 1)])
    print(f"  Cable settled: z={cable_z:.4f}")

    # Close
    print("  Closing fingers...")
    grip_fx = 0.008
    close_steps = 480
    for i in range(close_steps):
        t = (i + 1) / close_steps
        fx = 0.05 + (grip_fx - 0.05) * t
        fz = max(cable_z, 0.005 + CABLE_RADIUS)

        bq = state.body_q.numpy()
        bq[-2][:3] = [-fx, 0.0, fz]
        bq[-2][3:] = [0, 0, 0, 1]
        bq[-1][:3] = [fx, 0.0, fz]
        bq[-1][3:] = [0, 0, 0, 1]
        state.body_q.assign(bq)

        state, state_out = sim_step_with_fk(model, state, state_out, solver, control, contacts)

    pq = state.particle_q.numpy()
    center_idx = CABLE_SEGMENTS // 2
    if len(pq.shape) == 2:
        print(f"  After close: mean_z={np.mean(pq[:CABLE_SEGMENTS+1, 2]):.4f}, "
              f"center_z={pq[center_idx][2]:.4f}")
    else:
        z_vals = [pq[i * 3 + 2] for i in range(CABLE_SEGMENTS + 1)]
        print(f"  After close: mean_z={np.mean(z_vals):.4f}, "
              f"center_z={pq[center_idx*3+2]:.4f}")

    # Lift with detailed logging
    print("  Lifting with detailed logging...")
    lift_steps = 960
    lift_target = 0.10
    for i in range(lift_steps):
        t = (i + 1) / lift_steps
        lift_z = max(cable_z, 0.005 + CABLE_RADIUS) + lift_target * t

        bq = state.body_q.numpy()
        bq[-2][:3] = [-grip_fx, 0.0, lift_z]
        bq[-2][3:] = [0, 0, 0, 1]
        bq[-1][:3] = [grip_fx, 0.0, lift_z]
        bq[-1][3:] = [0, 0, 0, 1]
        state.body_q.assign(bq)

        state, state_out = sim_step_with_fk(model, state, state_out, solver, control, contacts)

        if i % 240 == 0:
            pq = state.particle_q.numpy()
            if len(pq.shape) == 2:
                center_z = pq[center_idx][2]
                mean_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
                all_z = pq[:CABLE_SEGMENTS + 1, 2]
                print(f"  Step {i:4d}: fingers_z={lift_z:.4f}, "
                      f"center_z={center_z:.4f}, "
                      f"mean_z={mean_z:.4f}, "
                      f"min_z={np.min(all_z):.4f}, "
                      f"max_z={np.max(all_z):.4f}")
            else:
                z_val = pq[center_idx * 3 + 2] if len(pq.shape) == 1 else pq[center_idx][2]
                print(f"  Step {i:4d}: fingers_z={lift_z:.4f}, center_z(flat)={z_val:.4f}")

    # Final
    pq = state.particle_q.numpy()
    if len(pq.shape) == 2:
        center_z = pq[center_idx][2]
        mean_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
        print(f"\n  FINAL: center_z={center_z:.4f}, mean_z={mean_z:.4f}")
        print(f"  All particle z: {pq[:CABLE_SEGMENTS+1, 2]}")
    else:
        z_vals = [pq[i * 3 + 2] for i in range(CABLE_SEGMENTS + 1)]
        print(f"\n  FINAL: center_z={z_vals[center_idx]:.4f}, mean_z={np.mean(z_vals):.4f}")

    print("\n=== Diagnostic complete ===")


if __name__ == "__main__":
    main()
