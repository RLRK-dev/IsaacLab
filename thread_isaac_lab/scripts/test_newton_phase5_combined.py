"""Newton Phase 5: Combined Parameter Search + Grip/Lift Test

Findings from ground collision sweep:
- SemiImplicit solver has explicit contact integration → light particles overshoot
- mass=0.1 @ dt=1/480: STABLE
- mass=0.05: nearly stable (z=0.83)
- dt=1/7680 @ mass=0.005: STABLE (but 16x slower)

This script:
1. Find optimal mass/dt combo for cable settling
2. Test grip+lift with working parameters
3. Test N-dependency with working parameters

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_phase5_combined.py
"""

import time
import sys
import tempfile
import os
import numpy as np
import warp as wp
import newton
from newton.solvers import SolverSemiImplicit

DEVICE = "cuda:0"

# Cable parameters (tuned for ground collision stability)
CABLE_SEGMENTS = 20
CABLE_SEG_LEN = 0.015   # 15mm per segment
CABLE_RADIUS = 0.005     # 5mm
CABLE_KE = 1.0e4         # spring stiffness
CABLE_KD = 10.0          # spring damping

# Contact parameters
PARTICLE_CONTACT_KE = 5.0e4
PARTICLE_CONTACT_KD = 100.0
PARTICLE_CONTACT_MU = 0.8

# ARM PD
ARM_KE = 8000.0
ARM_KD = 400.0

# UR10e URDF
UR10E_URDF = """<?xml version="1.0"?>
<robot name="ur10e_simple">
  <link name="base_link">
    <inertial><mass value="4.0"/><origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.006" ixy="0" ixz="0" iyy="0.006" iyz="0" izz="0.011"/></inertial>
    <collision><origin xyz="0 0 0.04" rpy="0 0 0"/><geometry><cylinder radius="0.075" length="0.08"/></geometry></collision>
  </link>
  <link name="shoulder_link">
    <inertial><mass value="7.778"/><origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.031" ixy="0" ixz="0" iyy="0.031" iyz="0" izz="0.022"/></inertial>
    <collision><origin xyz="0 0 0" rpy="0 0 0"/><geometry><cylinder radius="0.06" length="0.15"/></geometry></collision>
  </link>
  <link name="upper_arm_link">
    <inertial><mass value="12.93"/><origin xyz="-0.306 0 0.176" rpy="0 0 0"/>
      <inertia ixx="0.422" ixy="0" ixz="0" iyy="0.422" iyz="0" izz="0.036"/></inertial>
    <collision><origin xyz="-0.306 0 0" rpy="0 1.5708 0"/><geometry><cylinder radius="0.06" length="0.6127"/></geometry></collision>
  </link>
  <link name="forearm_link">
    <inertial><mass value="3.87"/><origin xyz="-0.286 0 0.039" rpy="0 0 0"/>
      <inertia ixx="0.111" ixy="0" ixz="0" iyy="0.111" iyz="0" izz="0.011"/></inertial>
    <collision><origin xyz="-0.286 0 0" rpy="0 1.5708 0"/><geometry><cylinder radius="0.05" length="0.57155"/></geometry></collision>
  </link>
  <link name="wrist_1_link">
    <inertial><mass value="1.96"/><origin xyz="0 -0.06 0" rpy="0 0 0"/>
      <inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/></inertial>
    <collision><origin xyz="0 -0.06 0" rpy="1.5708 0 0"/><geometry><cylinder radius="0.04" length="0.12"/></geometry></collision>
  </link>
  <link name="wrist_2_link">
    <inertial><mass value="1.96"/><origin xyz="0 0 -0.06" rpy="0 0 0"/>
      <inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/></inertial>
    <collision><origin xyz="0 0 -0.06" rpy="0 0 0"/><geometry><cylinder radius="0.04" length="0.12"/></geometry></collision>
  </link>
  <link name="wrist_3_link">
    <inertial><mass value="0.202"/><origin xyz="0 0 -0.058" rpy="0 0 0"/>
      <inertia ixx="0.0005" ixy="0" ixz="0" iyy="0.0005" iyz="0" izz="0.0006"/></inertial>
    <collision><origin xyz="0 0 -0.03" rpy="0 0 0"/><geometry><cylinder radius="0.035" length="0.06"/></geometry></collision>
  </link>
  <joint name="shoulder_pan_joint" type="revolute">
    <parent link="base_link"/><child link="shoulder_link"/>
    <origin xyz="0 0 0.1807" rpy="0 0 0"/><axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/>
  </joint>
  <joint name="shoulder_lift_joint" type="revolute">
    <parent link="shoulder_link"/><child link="upper_arm_link"/>
    <origin xyz="0 0 0" rpy="1.570796327 0 0"/><axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/>
  </joint>
  <joint name="elbow_joint" type="revolute">
    <parent link="upper_arm_link"/><child link="forearm_link"/>
    <origin xyz="-0.6127 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/>
    <limit lower="-3.1416" upper="3.1416" effort="150.0" velocity="3.1416"/>
  </joint>
  <joint name="wrist_1_joint" type="revolute">
    <parent link="forearm_link"/><child link="wrist_1_link"/>
    <origin xyz="-0.57155 0 0.17415" rpy="0 0 0"/><axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
  </joint>
  <joint name="wrist_2_joint" type="revolute">
    <parent link="wrist_1_link"/><child link="wrist_2_link"/>
    <origin xyz="0 -0.11985 0" rpy="1.570796327 0 0"/><axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
  </joint>
  <joint name="wrist_3_joint" type="revolute">
    <parent link="wrist_2_link"/><child link="wrist_3_link"/>
    <origin xyz="0 0.11655 0" rpy="1.570796327 3.14159265 3.14159265"/><axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
  </joint>
</robot>"""


def write_ur10e_urdf():
    fd, path = tempfile.mkstemp(suffix=".urdf", prefix="ur10e_simple_")
    with os.fdopen(fd, "w") as f:
        f.write(UR10E_URDF)
    return path


def add_ur10e_arm(builder, pos, urdf_path, rot=wp.quat_identity()):
    n_dofs_before = len(builder.joint_target_ke)
    builder.add_urdf(urdf_path, xform=wp.transform(pos, rot),
                     floating=False, enable_self_collisions=False)
    n_dofs_after = len(builder.joint_target_ke)
    for i in range(n_dofs_before, n_dofs_after):
        builder.joint_target_ke[i] = ARM_KE
        builder.joint_target_kd[i] = ARM_KD
        builder.joint_target_mode[i] = newton.JointTargetMode.POSITION_VELOCITY.value


def add_particle_chain_cable(builder, start_pos, direction=(1.0, 0.0, 0.0),
                              n_segments=CABLE_SEGMENTS, mass=0.005):
    dx, dy, dz = [d * CABLE_SEG_LEN for d in direction]
    particles = []
    for i in range(n_segments + 1):
        pos = (start_pos[0] + i * dx, start_pos[1] + i * dy, start_pos[2] + i * dz)
        p = builder.add_particle(pos=pos, vel=(0, 0, 0), mass=mass, radius=CABLE_RADIUS)
        particles.append(p)
    for i in range(n_segments):
        builder.add_spring(i=particles[i], j=particles[i + 1],
                           ke=CABLE_KE, kd=CABLE_KD, control=0.0)
    return particles


def sim_step_with_fk(model, state, state_out, solver, control, contacts, dt):
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, dt)
    return state_out, state


# ── Test 1: Mass/DT grid search ──────────────────────────────────────
def test_mass_dt_grid():
    """Find optimal mass/DT combination for cable settling."""
    print("=" * 60)
    print("TEST 1: Mass/DT Grid Search for Cable Settling")
    print("=" * 60)

    results = []
    for mass in [0.005, 0.01, 0.02, 0.05, 0.1]:
        for dt in [1/480, 1/960, 1/1920]:
            builder = newton.ModelBuilder(gravity=-9.81)
            builder.add_ground_plane()

            add_particle_chain_cable(builder, start_pos=(-0.15, 0.0, 0.10), mass=mass)

            model = builder.finalize(device=DEVICE)
            model.particle_ke = PARTICLE_CONTACT_KE
            model.particle_kd = PARTICLE_CONTACT_KD
            model.particle_mu = PARTICLE_CONTACT_MU

            state = model.state()
            contacts = model.contacts()
            control = model.control()
            solver = SolverSemiImplicit(model)
            state_out = model.state()

            steps = int(2.0 / dt)
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
            settled = abs(mean_z - CABLE_RADIUS) < 0.02 and std_z < 0.02 and not nan_detected
            status = "NaN" if nan_detected else ("✅" if settled else f"z={mean_z:.3f}")
            print(f"  mass={mass:.3f} dt=1/{int(1/dt):4d}: mean_z={mean_z:8.4f} std={std_z:.4f} → {status} ({elapsed:.1f}s)")

            results.append({"mass": mass, "dt": dt, "mean_z": mean_z, "settled": settled})

    settled = [r for r in results if r["settled"]]
    if settled:
        # Prefer lowest mass for realism, then highest dt for speed
        best = min(settled, key=lambda r: (r["mass"], -r["dt"]))
        print(f"\n  BEST: mass={best['mass']}, dt=1/{int(1/best['dt'])}")
        return best["mass"], best["dt"]
    else:
        print("\n  No settling found in grid!")
        return 0.1, 1 / 480  # fallback


# ── Test 2: Grip+Lift with working parameters ────────────────────────
def test_grip_lift(cable_mass, dt):
    """Test gripper-cable lift with stable parameters."""
    print()
    print("=" * 60)
    print(f"TEST 2: Grip+Lift (mass={cable_mass}, dt=1/{int(1/dt)})")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=-9.81)
        builder.add_ground_plane()

        add_ur10e_arm(builder, pos=(0, 0, 0), urdf_path=urdf_path)
        n_arm_bodies = 7

        cable = add_particle_chain_cable(
            builder, start_pos=(-0.15, 0.0, 0.10),
            direction=(1, 0, 0), mass=cable_mass,
        )

        # Kinematic fingers
        FINGER_RADIUS = 0.006
        FINGER_HALF_H = 0.02
        for sign, label in [(-1, "LF"), (1, "RF")]:
            f = builder.add_link(
                xform=wp.transform((sign * 0.05, 0, 0.15), wp.quat_identity()),
                mass=1.0, is_kinematic=True,
            )
            builder.add_shape_capsule(
                body=f, radius=FINGER_RADIUS, half_height=FINGER_HALF_H,
                cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=2000.0, kd=200.0, density=0.0),
            )

        LF_IDX = n_arm_bodies
        RF_IDX = n_arm_bodies + 1

        model = builder.finalize(device=DEVICE)
        model.particle_ke = PARTICLE_CONTACT_KE
        model.particle_kd = PARTICLE_CONTACT_KD
        model.particle_mu = 1.0

        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        # Phase 1: Settle cable on ground
        settle_steps = int(3.0 / dt)  # 3 seconds
        print(f"  Phase 1: Settling cable ({settle_steps} steps, 3s)...")
        for i in range(settle_steps):
            state, state_out = sim_step_with_fk(
                model, state, state_out, solver, control, contacts, dt)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at settle step {i}!")
                return False

        pq = state.particle_q.numpy()
        cable_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
        all_z = pq[:CABLE_SEGMENTS + 1, 2]
        print(f"  Cable settled: mean_z={cable_z:.4f}, range=[{np.min(all_z):.4f}, {np.max(all_z):.4f}]")

        settled = abs(cable_z) < 0.1
        if not settled:
            print(f"  ❌ Cable did not settle on ground (mean_z={cable_z:.4f})")
            return False
        print(f"  ✅ Cable on ground")

        # Phase 2: Close fingers at cable height
        print("  Phase 2: Closing fingers...")
        grip_fx = 0.008
        close_steps = int(1.0 / dt)  # 1 second
        for i in range(close_steps):
            t = (i + 1) / close_steps
            fx = 0.05 + (grip_fx - 0.05) * t
            fz = max(cable_z, CABLE_RADIUS)

            bq = state.body_q.numpy()
            bq[LF_IDX][:3] = [-fx, 0.0, fz]
            bq[LF_IDX][3:] = [0, 0, 0, 1]
            bq[RF_IDX][:3] = [fx, 0.0, fz]
            bq[RF_IDX][3:] = [0, 0, 0, 1]
            state.body_q.assign(bq)

            state, state_out = sim_step_with_fk(
                model, state, state_out, solver, control, contacts, dt)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at close step {i}")
                return False

        pq = state.particle_q.numpy()
        post_close_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
        center_z = pq[CABLE_SEGMENTS // 2][2]
        print(f"  After close: mean_z={post_close_z:.4f}, center_z={center_z:.4f}")

        # Phase 3: Lift
        print("  Phase 3: Lifting cable...")
        lift_steps = int(2.0 / dt)  # 2 seconds
        lift_target = 0.10  # 10cm lift
        for i in range(lift_steps):
            t = (i + 1) / lift_steps
            lift_z = max(cable_z, CABLE_RADIUS) + lift_target * t

            bq = state.body_q.numpy()
            bq[LF_IDX][:3] = [-grip_fx, 0.0, lift_z]
            bq[LF_IDX][3:] = [0, 0, 0, 1]
            bq[RF_IDX][:3] = [grip_fx, 0.0, lift_z]
            bq[RF_IDX][3:] = [0, 0, 0, 1]
            state.body_q.assign(bq)

            state, state_out = sim_step_with_fk(
                model, state, state_out, solver, control, contacts, dt)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at lift step {i}")
                return False

            if i % (lift_steps // 4) == 0:
                pq = state.particle_q.numpy()
                center = pq[CABLE_SEGMENTS // 2]
                mean_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
                all_z = pq[:CABLE_SEGMENTS + 1, 2]
                print(f"    Step {i:5d}/{lift_steps}: fingers_z={lift_z:.4f}, "
                      f"center_z={center[2]:.4f}, mean_z={mean_z:.4f}, "
                      f"range=[{np.min(all_z):.4f},{np.max(all_z):.4f}]")

        # Final measurement
        pq = state.particle_q.numpy()
        final_center_z = pq[CABLE_SEGMENTS // 2][2]
        final_mean_z = np.mean(pq[:CABLE_SEGMENTS + 1, 2])
        lifted = final_center_z > cable_z + 0.02

        print(f"\n  RESULT: initial_z={cable_z:.4f}, final_center_z={final_center_z:.4f}, "
              f"final_mean_z={final_mean_z:.4f}")
        print(f"  Cable lifted: {'YES' if lifted else 'NO'} "
              f"(delta={final_center_z - cable_z:.4f}m)")
        print(f"  All particle z: {pq[:CABLE_SEGMENTS+1, 2]}")

        passed = not np.any(np.isnan(pq))
        print(f"\n  >> Grip+Lift: {'PASS' if passed else 'FAIL'} "
              f"{'(LIFTED!)' if lifted else '(stable but no lift)'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Test 3: N-dependency with working parameters ─────────────────────
def test_n_dependency(cable_mass, dt):
    """Test N-dependency with stable parameters."""
    print()
    print("=" * 60)
    print(f"TEST 3: N-dependency (mass={cable_mass}, dt=1/{int(1/dt)})")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        results = {}
        for N in [1, 3]:
            world_builder = newton.ModelBuilder()

            add_ur10e_arm(world_builder, pos=(-0.5, 0, 0), urdf_path=urdf_path)
            add_ur10e_arm(world_builder, pos=(0.5, 0, 0), urdf_path=urdf_path)
            add_particle_chain_cable(
                world_builder, start_pos=(-0.15, 0, 0.30),
                direction=(1, 0, 0), mass=cable_mass,
            )

            main_builder = newton.ModelBuilder(gravity=-9.81)
            main_builder.add_ground_plane()
            main_builder.replicate(world_builder, world_count=N)

            model = main_builder.finalize(device=DEVICE)
            model.particle_ke = PARTICLE_CONTACT_KE
            model.particle_kd = PARTICLE_CONTACT_KD
            model.particle_mu = PARTICLE_CONTACT_MU

            state = model.state()
            newton.eval_fk(model, model.joint_q, model.joint_qd, state)
            contacts = model.contacts()
            control = model.control()
            solver = SolverSemiImplicit(model)
            state_out = model.state()

            test_steps = int(1.0 / dt)  # 1 second
            t0 = time.time()
            nan_detected = False
            for step in range(test_steps):
                state, state_out = sim_step_with_fk(
                    model, state, state_out, solver, control, contacts, dt)
                if step % (test_steps // 4) == 0:
                    if np.any(np.isnan(state.particle_q.numpy())):
                        nan_detected = True
                        break
            elapsed = time.time() - t0

            if nan_detected:
                results[N] = float('nan')
                print(f"  N={N}: NaN ({elapsed:.2f}s)")
            else:
                pq = state.particle_q.numpy()
                center_idx = CABLE_SEGMENTS // 2
                z = pq[center_idx][2]
                jq = state.joint_q.numpy()
                jdrift = np.max(np.abs(jq[:6]))
                results[N] = z
                print(f"  N={N}: cable_center z = {z:.10f}, j_drift={jdrift:.6f}  ({elapsed:.2f}s)")

        ref = results.get(1, float('nan'))
        cmp = results.get(3, float('nan'))
        if np.isnan(ref) or np.isnan(cmp):
            passed = False
            print(f"\n  Cannot compare (NaN)")
        else:
            diff = abs(cmp - ref)
            status = "IDENTICAL" if diff == 0.0 else f"diff={diff:.2e}"
            passed = diff < 1e-4
            print(f"\n  N=3 vs N=1: {status} {'PASS' if passed else 'FAIL'}")

        print(f"\n  >> N-dependency: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("Newton Phase 5: Combined Parameter Optimization + Tests")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print()

    # Find optimal parameters
    best_mass, best_dt = test_mass_dt_grid()
    print(f"\nUsing: mass={best_mass}, dt=1/{int(1/best_dt)}")

    # Run grip+lift
    grip_pass = test_grip_lift(best_mass, best_dt)

    # Run N-dependency
    ndep_pass = test_n_dependency(best_mass, best_dt)

    # Summary
    print()
    print("=" * 60)
    print("PHASE 5 COMBINED RESULTS")
    print("=" * 60)
    print(f"  Optimal params: mass={best_mass}, dt=1/{int(1/best_dt)}")
    print(f"  Grip+Lift:      {'PASS' if grip_pass else 'FAIL'}")
    print(f"  N-dependency:   {'PASS' if ndep_pass else 'FAIL'}")

    return 0 if grip_pass and ndep_pass else 1


if __name__ == "__main__":
    sys.exit(main())
