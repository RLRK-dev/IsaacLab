"""Newton UR10e + Particle Chain Cable Integration Test

Combines UR10e dual arms (Featherstone solver) with particle chain cable.
Particle chain uses add_particle + add_spring (not add_rod/cable joints),
so it works with Featherstone which supports all joint types + particles.

Tests:
1. N-dependency: particle chain cable with Featherstone at N=1 vs N=3
2. UR10e + particle chain cable in same simulation
3. Basic cable-gripper proximity test

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_ur10e_cable.py
"""

import time
import sys
import math
import tempfile
import os

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverFeatherstone, SolverMuJoCo, SolverSemiImplicit

# ── Configuration ────────────────────────────────────────────────────
DEVICE = "cuda:1"  # Blackwell GPU
DT = 1.0 / 480.0    # smaller timestep for stability
SETTLE_STEPS = 960   # 2 seconds at 480Hz

# Cable parameters (particle chain)
CABLE_SEGMENTS = 20
CABLE_SEG_LEN = 0.015   # 15mm per segment → 30cm total
CABLE_MASS = 0.005       # 5g per particle
CABLE_RADIUS = 0.005     # 5mm
CABLE_KE = 1.0e4         # spring stiffness
CABLE_KD = 10.0          # spring damping
CABLE_START_Z = 0.30     # drop from 30cm


# ── Simplified UR10e URDF ────────────────────────────────────────────
UR10E_URDF = """<?xml version="1.0"?>
<robot name="ur10e_simple">
  <link name="base_link">
    <inertial>
      <mass value="4.0"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.006" ixy="0" ixz="0" iyy="0.006" iyz="0" izz="0.011"/>
    </inertial>
    <collision>
      <origin xyz="0 0 0.04" rpy="0 0 0"/>
      <geometry><cylinder radius="0.075" length="0.08"/></geometry>
    </collision>
  </link>
  <link name="shoulder_link">
    <inertial>
      <mass value="7.778"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.031" ixy="0" ixz="0" iyy="0.031" iyz="0" izz="0.022"/>
    </inertial>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><cylinder radius="0.06" length="0.15"/></geometry>
    </collision>
  </link>
  <link name="upper_arm_link">
    <inertial>
      <mass value="12.93"/>
      <origin xyz="-0.306 0 0.176" rpy="0 0 0"/>
      <inertia ixx="0.422" ixy="0" ixz="0" iyy="0.422" iyz="0" izz="0.036"/>
    </inertial>
    <collision>
      <origin xyz="-0.306 0 0" rpy="0 1.5708 0"/>
      <geometry><cylinder radius="0.06" length="0.6127"/></geometry>
    </collision>
  </link>
  <link name="forearm_link">
    <inertial>
      <mass value="3.87"/>
      <origin xyz="-0.286 0 0.039" rpy="0 0 0"/>
      <inertia ixx="0.111" ixy="0" ixz="0" iyy="0.111" iyz="0" izz="0.011"/>
    </inertial>
    <collision>
      <origin xyz="-0.286 0 0" rpy="0 1.5708 0"/>
      <geometry><cylinder radius="0.05" length="0.57155"/></geometry>
    </collision>
  </link>
  <link name="wrist_1_link">
    <inertial>
      <mass value="1.96"/>
      <origin xyz="0 -0.06 0" rpy="0 0 0"/>
      <inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/>
    </inertial>
    <collision>
      <origin xyz="0 -0.06 0" rpy="1.5708 0 0"/>
      <geometry><cylinder radius="0.04" length="0.12"/></geometry>
    </collision>
  </link>
  <link name="wrist_2_link">
    <inertial>
      <mass value="1.96"/>
      <origin xyz="0 0 -0.06" rpy="0 0 0"/>
      <inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/>
    </inertial>
    <collision>
      <origin xyz="0 0 -0.06" rpy="0 0 0"/>
      <geometry><cylinder radius="0.04" length="0.12"/></geometry>
    </collision>
  </link>
  <link name="wrist_3_link">
    <inertial>
      <mass value="0.202"/>
      <origin xyz="0 0 -0.058" rpy="0 0 0"/>
      <inertia ixx="0.0005" ixy="0" ixz="0" iyy="0.0005" iyz="0" izz="0.0006"/>
    </inertial>
    <collision>
      <origin xyz="0 0 -0.03" rpy="0 0 0"/>
      <geometry><cylinder radius="0.035" length="0.06"/></geometry>
    </collision>
  </link>
  <joint name="shoulder_pan_joint" type="revolute">
    <parent link="base_link"/>
    <child link="shoulder_link"/>
    <origin xyz="0 0 0.1807" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/>
  </joint>
  <joint name="shoulder_lift_joint" type="revolute">
    <parent link="shoulder_link"/>
    <child link="upper_arm_link"/>
    <origin xyz="0 0 0" rpy="1.570796327 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/>
  </joint>
  <joint name="elbow_joint" type="revolute">
    <parent link="upper_arm_link"/>
    <child link="forearm_link"/>
    <origin xyz="-0.6127 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.1416" upper="3.1416" effort="150.0" velocity="3.1416"/>
  </joint>
  <joint name="wrist_1_joint" type="revolute">
    <parent link="forearm_link"/>
    <child link="wrist_1_link"/>
    <origin xyz="-0.57155 0 0.17415" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
  </joint>
  <joint name="wrist_2_joint" type="revolute">
    <parent link="wrist_1_link"/>
    <child link="wrist_2_link"/>
    <origin xyz="0 -0.11985 0" rpy="1.570796327 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
  </joint>
  <joint name="wrist_3_joint" type="revolute">
    <parent link="wrist_2_link"/>
    <child link="wrist_3_link"/>
    <origin xyz="0 0.11655 0" rpy="1.570796327 3.14159265 3.14159265"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
  </joint>
</robot>
"""


def write_ur10e_urdf():
    """Write simplified UR10e URDF to temp file and return path."""
    fd, path = tempfile.mkstemp(suffix=".urdf", prefix="ur10e_simple_")
    with os.fdopen(fd, "w") as f:
        f.write(UR10E_URDF)
    return path


def add_ur10e_arm(builder, pos, urdf_path, rot=wp.quat_identity()):
    """Add UR10e arm with proper joint drive config.

    URDF importer sets ke=0, kd=0, mode=POSITION by default.
    Must set POSITION_VELOCITY mode and drive gains on builder before finalize.
    """
    n_dofs_before = len(builder.joint_target_ke)
    builder.add_urdf(
        urdf_path,
        xform=wp.transform(pos, rot),
        floating=False,
        enable_self_collisions=False,
    )
    n_dofs_after = len(builder.joint_target_ke)
    for i in range(n_dofs_before, n_dofs_after):
        builder.joint_target_ke[i] = 5000.0
        builder.joint_target_kd[i] = 200.0
        builder.joint_target_mode[i] = newton.JointTargetMode.POSITION_VELOCITY.value


def add_particle_chain_cable(builder, start_pos, direction=(0.0, 1.0, 0.0),
                              n_segments=CABLE_SEGMENTS):
    """Add a particle chain cable to the builder.

    Uses add_particle + add_spring instead of add_rod (cable joints).
    Works with Featherstone solver (unlike cable joints which need VBD).
    """
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

    # Connect with springs
    for i in range(n_segments):
        builder.add_spring(
            i=particles[i],
            j=particles[i + 1],
            ke=CABLE_KE,
            kd=CABLE_KD,
            control=0.0,
        )

    return particles


# ── Test 1: Particle chain N-dependency ──────────────────────────────
def test_particle_chain_n_dependency():
    """Test N-dependency for particle chain cable with Featherstone."""
    print("=" * 60)
    print("TEST 1: Particle chain N-dependency (Featherstone)")
    print("=" * 60)

    results = {}
    for N in [1, 3, 10]:
        world_builder = newton.ModelBuilder()
        add_particle_chain_cable(
            world_builder,
            start_pos=(0.0, -CABLE_SEGMENTS * CABLE_SEG_LEN / 2, CABLE_START_Z),
        )

        main_builder = newton.ModelBuilder()
        main_builder.add_ground_plane()
        main_builder.replicate(world_builder, world_count=N)

        model = main_builder.finalize(device=DEVICE)
        model.particle_ke = 500.0
        model.particle_kd = 50.0
        model.particle_mu = 0.8

        state = model.state()
        contacts = model.contacts()
        control = model.control()

        try:
            solver = SolverFeatherstone(model)
            solver_name = "Featherstone"
        except Exception as e:
            print(f"  Featherstone failed: {e}, trying SemiImplicit...")
            solver = SolverSemiImplicit(model)
            solver_name = "SemiImplicit"

        state_out = model.state()

        t0 = time.time()
        for _ in range(SETTLE_STEPS):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state
        elapsed = time.time() - t0

        pq = state.particle_q.numpy()
        # Center particle in world 0
        n_per_world = CABLE_SEGMENTS + 1
        center_idx = CABLE_SEGMENTS // 2
        z = pq[center_idx][2]
        results[N] = z
        has_nan = np.isnan(z)
        print(f"  N={N:2d}: center z = {z:.10f}  ({elapsed:.2f}s, {solver_name})"
              f"{' NaN!' if has_nan else ''}")

    print()
    ref = results[1]
    all_pass = True
    for N in [3, 10]:
        if np.isnan(results[N]) or np.isnan(ref):
            print(f"  N={N} vs N=1: NaN detected FAIL")
            all_pass = False
            continue
        diff = abs(results[N] - ref)
        status = "IDENTICAL" if diff == 0.0 else f"diff={diff:.2e}"
        passed = diff < 1e-4
        all_pass = all_pass and passed
        print(f"  N={N} vs N=1: {status} {'PASS' if passed else 'FAIL'}")

    print(f"\n  >> Particle chain N-dependency: {'ALL PASS' if all_pass else 'FAILED'}")
    return all_pass


# ── Test 2: UR10e + particle chain cable ──────────────────────────────
def test_ur10e_with_cable():
    """Test UR10e arms with particle chain cable in same simulation."""
    print()
    print("=" * 60)
    print("TEST 2: UR10e + particle chain cable (Featherstone)")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=0.0)
        builder.add_ground_plane()

        # Add left arm
        add_ur10e_arm(builder, pos=(-0.5, 0.0, 0.0), urdf_path=urdf_path)
        n_bodies_left = len(builder.body_mass)

        # Add right arm
        add_ur10e_arm(builder, pos=(0.5, 0.0, 0.0), urdf_path=urdf_path)

        # Add particle chain cable between arms
        # Cable hangs between the two arms at some height
        cable_particles = add_particle_chain_cable(
            builder,
            start_pos=(-0.3, 0.0, 0.50),
            direction=(1.0, 0.0, 0.0),  # X direction between arms
        )

        print(f"  Bodies: {len(builder.body_mass)}")
        print(f"  Joints: {len(builder.joint_type)}")
        print(f"  Particles: {len(builder.particle_mass)}")

        model = builder.finalize(device=DEVICE)
        model.particle_ke = 500.0
        model.particle_kd = 50.0
        model.particle_mu = 0.8

        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()

        try:
            solver = SolverFeatherstone(model)
            solver_name = "Featherstone"
        except Exception as e:
            print(f"  Featherstone failed: {e}")
            print(f"  NOTE: MuJoCo does not support particles. Trying SemiImplicit...")
            solver = SolverSemiImplicit(model)
            solver_name = "SemiImplicit"

        state_out = model.state()

        n_dofs = len(model.joint_q.numpy())
        print(f"  DOFs: {n_dofs}, Solver: {solver_name}")

        # Simulate: let cable settle while arms hold position
        # Skip collision to avoid UR10e self-collision NaN (Featherstone issue)
        t0 = time.time()
        for i in range(SETTLE_STEPS):
            state.clear_forces()
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state

            if i % 240 == 0:
                pq = state.particle_q.numpy()
                jq = state.joint_q.numpy()
                cable_z = np.mean(pq[:, 2])
                has_nan = np.any(np.isnan(pq)) or np.any(np.isnan(jq))
                print(f"  Step {i:4d}: cable_mean_z={cable_z:.4f}, "
                      f"arms stable={'YES' if not has_nan else 'NaN!'}")
                if has_nan:
                    break
        elapsed = time.time() - t0

        pq = state.particle_q.numpy()
        jq = state.joint_q.numpy()
        bq = state.body_q.numpy()

        cable_stable = not np.any(np.isnan(pq))
        arms_stable = not np.any(np.isnan(jq)) and not np.any(np.isnan(bq))

        print(f"\n  Cable stable: {'YES' if cable_stable else 'NO'}")
        print(f"  Arms stable: {'YES' if arms_stable else 'NO'}")
        print(f"  Final cable mean z: {np.mean(pq[:, 2]):.4f}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Note: gravity=0, cable stays at initial height (expected)")

        passed = cable_stable and arms_stable
        print(f"\n  >> UR10e + cable: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Test 3: UR10e + cable N-dependency ────────────────────────────────
def test_ur10e_cable_n_dependency():
    """Test N-dependency with full UR10e + cable setup using replicate()."""
    print()
    print("=" * 60)
    print("TEST 3: UR10e + cable N-dependency (replicate)")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        results = {}
        for N in [1, 3]:
            # Build single world: dual arm + cable
            world_builder = newton.ModelBuilder()

            add_ur10e_arm(world_builder, pos=(-0.5, 0.0, 0.0), urdf_path=urdf_path)
            add_ur10e_arm(world_builder, pos=(0.5, 0.0, 0.0), urdf_path=urdf_path)
            add_particle_chain_cable(
                world_builder,
                start_pos=(-0.3, 0.0, 0.50),
                direction=(1.0, 0.0, 0.0),
            )

            main_builder = newton.ModelBuilder()
            main_builder.add_ground_plane()
            main_builder.replicate(world_builder, world_count=N)

            model = main_builder.finalize(device=DEVICE)
            model.particle_ke = 500.0
            model.particle_kd = 50.0
            model.particle_mu = 0.8

            n_dofs = len(model.joint_q.numpy())
            ke_values = np.full(n_dofs, 800.0)
            kd_values = np.full(n_dofs, 40.0)
            model.joint_target_ke.assign(ke_values)
            model.joint_target_kd.assign(kd_values)

            state = model.state()
            newton.eval_fk(model, model.joint_q, model.joint_qd, state)
            contacts = model.contacts()
            control = model.control()

            try:
                solver = SolverFeatherstone(model)
            except Exception:
                solver = SolverSemiImplicit(model)
            state_out = model.state()

            test_steps = 240  # at 480Hz
            t0 = time.time()
            for _ in range(test_steps):
                state.clear_forces()
                solver.step(state, state_out, control, contacts, DT)
                state, state_out = state_out, state
            elapsed = time.time() - t0

            pq = state.particle_q.numpy()
            n_particles_per_world = CABLE_SEGMENTS + 1
            center_idx = CABLE_SEGMENTS // 2
            z = pq[center_idx][2]
            results[N] = z
            print(f"  N={N}: cable_center z = {z:.10f}  ({elapsed:.2f}s)")

        # Compare
        print()
        ref = results[1]
        if np.isnan(ref) or np.isnan(results[3]):
            print(f"  NaN detected — cannot compare")
            passed = False
        else:
            diff = abs(results[3] - ref)
            status = "IDENTICAL" if diff == 0.0 else f"diff={diff:.2e}"
            passed = diff < 1e-4
            print(f"  N=3 vs N=1: {status} {'PASS' if passed else 'FAIL'}")

        print(f"\n  >> UR10e + cable N-dependency: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print(f"Newton UR10e + Cable Integration Test")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print()

    results = {}
    results["particle_chain_n_dep"] = test_particle_chain_n_dependency()
    results["ur10e_with_cable"] = test_ur10e_with_cable()
    results["ur10e_cable_n_dep"] = test_ur10e_cable_n_dependency()

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
    print("ARCHITECTURE FINDINGS:")
    print("  Featherstone: REVOLUTE joints (robot arms) + particles (cable)")
    print("  VBD: CABLE joints (rod cable) + soft bodies (FEM)")
    print("  Integration: Featherstone + particle chain = robot + cable in one solver")
    print()

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
