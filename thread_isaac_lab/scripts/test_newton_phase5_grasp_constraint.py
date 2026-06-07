"""Newton Phase 5c: Soft Grasp Constraint for Cable Lift

Problem: SemiImplicit penalty contact cannot provide stable grip:
- High ke → particle launch (energy injection)
- Low ke → particle slip-through
- No stable middle ground

Solution: Apply explicit spring forces to particles near finger positions.
During lift, these forces resist gravity and keep particles "attached" to fingers.

This is physically more realistic than kinematic position setting, and
demonstrates the concept for THREAD PoC.

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_phase5_grasp_constraint.py
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
GRAVITY = -9.81

# Working parameters from Phase 5a
CABLE_MASS = 0.02
DT = 1.0 / 1920.0

# Cable
CABLE_SEGMENTS = 40  # denser cable for better grip
CABLE_SEG_LEN = 0.0075  # 7.5mm per segment (30cm total)
CABLE_RADIUS = 0.004
CABLE_KE = 1e4
CABLE_KD = 10.0

# Contact
PARTICLE_CONTACT_KE = 5e4
PARTICLE_CONTACT_KD = 100.0
PARTICLE_CONTACT_MU = 0.8

# Grasp constraint
GRASP_RADIUS = 0.02  # particles within 20mm of grip center are grasped
GRASP_KE = 5000.0     # spring stiffness for grasp constraint
GRASP_KD = 200.0       # spring damping for grasp constraint

# ARM
ARM_KE = 8000.0
ARM_KD = 400.0

UR10E_URDF = """<?xml version="1.0"?>
<robot name="ur10e_simple">
  <link name="base_link"><inertial><mass value="4.0"/><origin xyz="0 0 0" rpy="0 0 0"/><inertia ixx="0.006" ixy="0" ixz="0" iyy="0.006" iyz="0" izz="0.011"/></inertial><collision><origin xyz="0 0 0.04" rpy="0 0 0"/><geometry><cylinder radius="0.075" length="0.08"/></geometry></collision></link>
  <link name="shoulder_link"><inertial><mass value="7.778"/><origin xyz="0 0 0" rpy="0 0 0"/><inertia ixx="0.031" ixy="0" ixz="0" iyy="0.031" iyz="0" izz="0.022"/></inertial></link>
  <link name="upper_arm_link"><inertial><mass value="12.93"/><origin xyz="-0.306 0 0.176" rpy="0 0 0"/><inertia ixx="0.422" ixy="0" ixz="0" iyy="0.422" iyz="0" izz="0.036"/></inertial></link>
  <link name="forearm_link"><inertial><mass value="3.87"/><origin xyz="-0.286 0 0.039" rpy="0 0 0"/><inertia ixx="0.111" ixy="0" ixz="0" iyy="0.111" iyz="0" izz="0.011"/></inertial></link>
  <link name="wrist_1_link"><inertial><mass value="1.96"/><origin xyz="0 -0.06 0" rpy="0 0 0"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/></inertial></link>
  <link name="wrist_2_link"><inertial><mass value="1.96"/><origin xyz="0 0 -0.06" rpy="0 0 0"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/></inertial></link>
  <link name="wrist_3_link"><inertial><mass value="0.202"/><origin xyz="0 0 -0.058" rpy="0 0 0"/><inertia ixx="0.0005" ixy="0" ixz="0" iyy="0.0005" iyz="0" izz="0.0006"/></inertial></link>
  <joint name="shoulder_pan_joint" type="revolute"><parent link="base_link"/><child link="shoulder_link"/><origin xyz="0 0 0.1807" rpy="0 0 0"/><axis xyz="0 0 1"/><limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/></joint>
  <joint name="shoulder_lift_joint" type="revolute"><parent link="shoulder_link"/><child link="upper_arm_link"/><origin xyz="0 0 0" rpy="1.570796327 0 0"/><axis xyz="0 0 1"/><limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/></joint>
  <joint name="elbow_joint" type="revolute"><parent link="upper_arm_link"/><child link="forearm_link"/><origin xyz="-0.6127 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/><limit lower="-3.1416" upper="3.1416" effort="150.0" velocity="3.1416"/></joint>
  <joint name="wrist_1_joint" type="revolute"><parent link="forearm_link"/><child link="wrist_1_link"/><origin xyz="-0.57155 0 0.17415" rpy="0 0 0"/><axis xyz="0 0 1"/><limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/></joint>
  <joint name="wrist_2_joint" type="revolute"><parent link="wrist_1_link"/><child link="wrist_2_link"/><origin xyz="0 -0.11985 0" rpy="1.570796327 0 0"/><axis xyz="0 0 1"/><limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/></joint>
  <joint name="wrist_3_joint" type="revolute"><parent link="wrist_2_link"/><child link="wrist_3_link"/><origin xyz="0 0.11655 0" rpy="1.570796327 3.14159265 3.14159265"/><axis xyz="0 0 1"/><limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/></joint>
</robot>"""


def write_ur10e_urdf():
    fd, path = tempfile.mkstemp(suffix=".urdf", prefix="ur10e_")
    with os.fdopen(fd, "w") as f:
        f.write(UR10E_URDF)
    return path


def add_ur10e_arm(builder, pos, urdf_path):
    n_before = len(builder.joint_target_ke)
    builder.add_urdf(urdf_path, xform=wp.transform(pos, wp.quat_identity()),
                     floating=False, enable_self_collisions=False)
    n_after = len(builder.joint_target_ke)
    for i in range(n_before, n_after):
        builder.joint_target_ke[i] = ARM_KE
        builder.joint_target_kd[i] = ARM_KD
        builder.joint_target_mode[i] = newton.JointTargetMode.POSITION_VELOCITY.value


def add_cable(builder, start_pos, direction=(1, 0, 0)):
    dx, dy, dz = [d * CABLE_SEG_LEN for d in direction]
    particles = []
    for i in range(CABLE_SEGMENTS + 1):
        pos = (start_pos[0] + i * dx, start_pos[1] + i * dy, start_pos[2] + i * dz)
        p = builder.add_particle(pos=pos, vel=(0, 0, 0), mass=CABLE_MASS, radius=CABLE_RADIUS)
        particles.append(p)
    for i in range(CABLE_SEGMENTS):
        builder.add_spring(i=particles[i], j=particles[i + 1],
                           ke=CABLE_KE, kd=CABLE_KD, control=0.0)
    return particles


def apply_grasp_forces(state, grip_center, grasped_indices, n_particles):
    """Apply spring forces pulling grasped particles toward grip center.

    F = -ke * (pos - target) - kd * vel
    """
    pq = state.particle_q.numpy()
    pqd = state.particle_qd.numpy()
    pf = state.particle_f.numpy()

    for idx in grasped_indices:
        if idx >= n_particles:
            continue
        pos = pq[idx]
        vel = pqd[idx]
        # Spring force toward grip center (x=0, y=0 only, z follows grip)
        dx = pos[0] - grip_center[0]
        dy = pos[1] - grip_center[1]
        dz = pos[2] - grip_center[2]
        fx = -GRASP_KE * dx - GRASP_KD * vel[0]
        fy = -GRASP_KE * dy - GRASP_KD * vel[1]
        fz = -GRASP_KE * dz - GRASP_KD * vel[2]
        pf[idx][0] += fx
        pf[idx][1] += fy
        pf[idx][2] += fz

    state.particle_f.assign(pf)


def detect_graspable_particles(state, grip_center, n_particles, radius=GRASP_RADIUS):
    """Find particles within grasp radius of grip center."""
    pq = state.particle_q.numpy()
    indices = []
    for i in range(n_particles):
        dist = np.linalg.norm(pq[i] - np.array(grip_center))
        if dist < radius:
            indices.append(i)
    return indices


def sim_step_grasp(model, state, state_out, solver, control, contacts, dt,
                    grip_center=None, grasped_indices=None, n_particles=0):
    """Step with FK fix + optional grasp constraint."""
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)

    # Apply grasp forces before collision/integration
    if grip_center is not None and grasped_indices:
        apply_grasp_forces(state, grip_center, grasped_indices, n_particles)

    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, dt)
    return state_out, state


def main():
    print("Newton Phase 5c: Soft Grasp Constraint Cable Lift")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"Cable: {CABLE_SEGMENTS} segs × {CABLE_SEG_LEN*1000:.1f}mm, "
          f"mass={CABLE_MASS}, radius={CABLE_RADIUS*1000:.1f}mm")
    print(f"Grasp: radius={GRASP_RADIUS*1000:.0f}mm, ke={GRASP_KE}, kd={GRASP_KD}")
    print()

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()

        add_ur10e_arm(builder, pos=(0, 0, 0), urdf_path=urdf_path)

        cable_start = (-CABLE_SEGMENTS * CABLE_SEG_LEN / 2, 0, 0.10)
        cable = add_cable(builder, start_pos=cable_start)
        n_particles = CABLE_SEGMENTS + 1

        model = builder.finalize(device=DEVICE)
        model.particle_ke = PARTICLE_CONTACT_KE
        model.particle_kd = PARTICLE_CONTACT_KD
        model.particle_mu = PARTICLE_CONTACT_MU

        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        # ── Phase 1: Settle cable ────────────────────────────────
        print("=" * 60)
        print("PHASE 1: Cable settling")
        print("=" * 60)
        settle_steps = int(3.0 / DT)
        for i in range(settle_steps):
            state.clear_forces()
            newton.eval_fk(model, state.joint_q, state.joint_qd, state)
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state

            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at step {i}!")
                return 1

        pq = state.particle_q.numpy()
        cable_z = np.mean(pq[:n_particles, 2])
        all_z = pq[:n_particles, 2]
        print(f"  Cable settled: mean_z={cable_z:.4f}, "
              f"range=[{np.min(all_z):.4f}, {np.max(all_z):.4f}]")

        if abs(cable_z) > 0.1:
            print(f"  ❌ Cable didn't settle (z={cable_z:.4f})")
            return 1

        # ── Phase 2: Detect graspable particles ──────────────────
        print()
        print("=" * 60)
        print("PHASE 2: Detect graspable particles")
        print("=" * 60)

        # Grip center at cable midpoint, at cable height
        grip_center = [0.0, 0.0, max(cable_z, CABLE_RADIUS)]
        grasped = detect_graspable_particles(state, grip_center, n_particles, GRASP_RADIUS)
        print(f"  Grip center: {grip_center}")
        print(f"  Grasped particles: {len(grasped)} / {n_particles}")
        print(f"  Grasped indices: {grasped}")

        if len(grasped) == 0:
            print("  ❌ No particles in grasp range!")
            # Try larger radius
            for r in [0.03, 0.05, 0.10]:
                grasped = detect_graspable_particles(state, grip_center, n_particles, r)
                if len(grasped) > 0:
                    print(f"  Retry with r={r*1000:.0f}mm: found {len(grasped)} particles")
                    break
            if len(grasped) == 0:
                print("  ❌ Still no particles in range!")
                pq = state.particle_q.numpy()
                for i in range(n_particles):
                    dist = np.linalg.norm(pq[i] - np.array(grip_center))
                    if i < 5 or dist < 0.2:
                        print(f"    p[{i}] pos={pq[i]}, dist={dist:.4f}")
                return 1

        # ── Phase 3: Lift with grasp constraint ──────────────────
        print()
        print("=" * 60)
        print("PHASE 3: Lift with grasp constraint")
        print("=" * 60)

        lift_steps = int(3.0 / DT)  # 3 seconds
        lift_target = 0.10  # lift 10cm

        initial_center_z = np.mean(pq[grasped, 2]) if len(grasped) > 0 else cable_z
        print(f"  Initial grasped particle mean z: {initial_center_z:.4f}")

        for i in range(lift_steps):
            t = (i + 1) / lift_steps
            lift_z = max(cable_z, CABLE_RADIUS) + lift_target * t
            current_grip_center = [0.0, 0.0, lift_z]

            state, state_out = sim_step_grasp(
                model, state, state_out, solver, control, contacts, DT,
                grip_center=current_grip_center,
                grasped_indices=grasped,
                n_particles=n_particles,
            )

            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at lift step {i}!")
                return 1

            # Report every 0.5s
            if i % int(0.5 / DT) == 0:
                pq = state.particle_q.numpy()
                grasped_z = np.mean(pq[grasped, 2]) if len(grasped) > 0 else 0
                all_mean_z = np.mean(pq[:n_particles, 2])
                all_z = pq[:n_particles, 2]
                print(f"  t={t*3:.1f}s: grip_z={lift_z:.4f}, "
                      f"grasped_z={grasped_z:.4f}, "
                      f"all_mean_z={all_mean_z:.4f}, "
                      f"range=[{np.min(all_z):.4f},{np.max(all_z):.4f}]")

        # ── Final measurement ────────────────────────────────────
        pq = state.particle_q.numpy()
        final_grasped_z = np.mean(pq[grasped, 2])
        final_all_mean_z = np.mean(pq[:n_particles, 2])
        final_all_z = pq[:n_particles, 2]

        lifted = final_grasped_z > initial_center_z + 0.02
        catenary = final_all_mean_z > initial_center_z  # ungrasped particles pulled up by springs

        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"  Initial z:        {initial_center_z:.4f}m")
        print(f"  Final grasped z:  {final_grasped_z:.4f}m (delta={final_grasped_z - initial_center_z:.4f}m)")
        print(f"  Final all mean z: {final_all_mean_z:.4f}m")
        print(f"  Z range:          [{np.min(final_all_z):.4f}, {np.max(final_all_z):.4f}]")
        print(f"  Grasped lifted:   {'YES' if lifted else 'NO'}")
        print(f"  Catenary formed:  {'YES' if catenary else 'NO'}")

        # Per-particle z for visualization
        print(f"\n  Per-particle z (grasped marked with *):")
        for i in range(n_particles):
            marker = "*" if i in grasped else " "
            print(f"    {marker}p[{i:2d}] z={pq[i][2]:.4f}")

        print()
        if lifted:
            print("  ★ CABLE GRIP+LIFT SUCCESS with soft grasp constraint! ★")
            if catenary:
                print("  ★ Catenary shape formed (ungrasped ends hanging down)! ★")
        else:
            print("  Cable stable but not lifted. Grasp constraint may need tuning.")

        passed = not np.any(np.isnan(pq)) and lifted
        print(f"\n  >> Phase 5c Grip+Lift: {'PASS' if passed else 'FAIL'}")
        return 0 if passed else 1
    finally:
        os.unlink(urdf_path)


if __name__ == "__main__":
    sys.exit(main())
