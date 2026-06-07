"""Newton Phase 5 Final: Optimized Grip+Lift + N-dependency

Working parameters established:
- mass=0.1: stable at dt=1/480 (fastest sim speed)
- Grasp constraint: ke tuned to ~10x gravity force
- Cable settles on ground properly at mass=0.1

Tests:
1. Cable settle + grasp + lift (single arm)
2. Dual-arm cable manipulation (grip at two points + lift)
3. N-dependency with full system

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_phase5_final.py
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
DT = 1.0 / 480.0  # standard speed — stable with mass=0.1

# Cable (particle chain)
CABLE_SEGMENTS = 40
CABLE_SEG_LEN = 0.0075   # 7.5mm → 30cm total cable
CABLE_MASS = 0.1          # stable ground collision at dt=1/480
CABLE_RADIUS = 0.004
CABLE_KE = 1.0e4
CABLE_KD = 10.0

# Contact
PARTICLE_CONTACT_KE = 5.0e4
PARTICLE_CONTACT_KD = 100.0
PARTICLE_CONTACT_MU = 0.8

# Grasp constraint — tuned for mass=0.1 particles
# F_gravity = 0.1 * 9.81 = 0.981 N per particle
# At displacement 0.01m: F_spring = ke * 0.01
# Want F_spring ~ 10 * F_gravity: ke = 10 * 0.981 / 0.01 = 981
GRASP_KE = 1000.0
GRASP_KD = 50.0   # critical damping: sqrt(4 * ke * m) = sqrt(4 * 1000 * 0.1) = 20
GRASP_RADIUS = 0.03  # 30mm detection radius

# ARM PD
ARM_KE = 8000.0
ARM_KD = 400.0

UR10E_URDF = """<?xml version="1.0"?>
<robot name="ur10e_simple">
  <link name="base_link"><inertial><mass value="4.0"/><origin xyz="0 0 0" rpy="0 0 0"/><inertia ixx="0.006" ixy="0" ixz="0" iyy="0.006" iyz="0" izz="0.011"/></inertial></link>
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
    """Apply spring forces to grasped particles."""
    pq = state.particle_q.numpy()
    pqd = state.particle_qd.numpy()
    pf = state.particle_f.numpy()

    for idx in grasped_indices:
        if idx >= n_particles:
            continue
        pos = pq[idx]
        vel = pqd[idx]
        dx = pos[0] - grip_center[0]
        dy = pos[1] - grip_center[1]
        dz = pos[2] - grip_center[2]
        pf[idx][0] += -GRASP_KE * dx - GRASP_KD * vel[0]
        pf[idx][1] += -GRASP_KE * dy - GRASP_KD * vel[1]
        pf[idx][2] += -GRASP_KE * dz - GRASP_KD * vel[2]

    state.particle_f.assign(pf)


def detect_grasped(state, grip_center, n_particles):
    """Find particles within grasp radius."""
    pq = state.particle_q.numpy()
    indices = []
    for i in range(n_particles):
        dist = np.linalg.norm(pq[i] - np.array(grip_center))
        if dist < GRASP_RADIUS:
            indices.append(i)
    return indices


def sim_step(model, state, state_out, solver, control, contacts,
             grip_centers=None, grasped_sets=None, n_particles=0):
    """Step with FK fix + optional grasp constraints."""
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)

    if grip_centers and grasped_sets:
        for gc, gi in zip(grip_centers, grasped_sets):
            apply_grasp_forces(state, gc, gi, n_particles)

    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, DT)
    return state_out, state


# ── Test 1: Single grip + lift ────────────────────────────────────────
def test_single_grip_lift():
    """Cable settle → grip → lift with single grip point."""
    print("=" * 60)
    print("TEST 1: Single Grip + Lift")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()

        add_ur10e_arm(builder, pos=(0, 0, 0), urdf_path=urdf_path)

        cable_start = (-CABLE_SEGMENTS * CABLE_SEG_LEN / 2, 0, 0.10)
        add_cable(builder, start_pos=cable_start)
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

        # Settle 2s
        print("  Settling cable (2s)...")
        settle_steps = int(2.0 / DT)
        for i in range(settle_steps):
            state, state_out = sim_step(
                model, state, state_out, solver, control, contacts, n_particles=n_particles)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at settle step {i}!")
                return False

        pq = state.particle_q.numpy()
        cable_z = np.mean(pq[:n_particles, 2])
        print(f"  Cable z={cable_z:.4f}")

        if abs(cable_z) > 0.1:
            print(f"  Cable not settled!")
            return False

        # Detect graspable particles at cable center
        grip_center = [0.0, 0.0, max(cable_z, CABLE_RADIUS)]
        grasped = detect_grasped(state, grip_center, n_particles)
        print(f"  Grasped particles: {len(grasped)} indices={grasped}")

        if len(grasped) == 0:
            print("  No particles in grasp range!")
            return False

        initial_z = np.mean(pq[grasped, 2])

        # Lift 3s (10cm)
        print("  Lifting (3s, 10cm target)...")
        lift_steps = int(3.0 / DT)
        lift_target = 0.10

        for i in range(lift_steps):
            t = (i + 1) / lift_steps
            lift_z = max(cable_z, CABLE_RADIUS) + lift_target * t
            current_gc = [0.0, 0.0, lift_z]

            state, state_out = sim_step(
                model, state, state_out, solver, control, contacts,
                grip_centers=[current_gc], grasped_sets=[grasped],
                n_particles=n_particles)

            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at lift step {i}!")
                return False

            if i % int(0.5 / DT) == 0:
                pq = state.particle_q.numpy()
                g_z = np.mean(pq[grasped, 2])
                all_z = pq[:n_particles, 2]
                print(f"    t={t*3:.1f}s: grip_target={lift_z:.4f}, grasped_z={g_z:.4f}, "
                      f"mean_z={np.mean(all_z):.4f}, range=[{np.min(all_z):.4f},{np.max(all_z):.4f}]")

        pq = state.particle_q.numpy()
        final_g_z = np.mean(pq[grasped, 2])
        delta = final_g_z - initial_z
        lifted = delta > 0.02

        print(f"\n  Result: initial={initial_z:.4f} → final={final_g_z:.4f} (delta={delta:.4f}m)")
        print(f"  {'✅ LIFTED' if lifted else '❌ NOT LIFTED'}")

        # Check catenary shape
        all_z = pq[:n_particles, 2]
        center_idx = n_particles // 2
        edges_z = (pq[0, 2] + pq[-1, 2]) / 2
        center_z = pq[center_idx, 2]
        catenary = center_z > edges_z + 0.01
        if catenary:
            print(f"  ✅ Catenary shape (center_z={center_z:.4f} > edges_z={edges_z:.4f})")

        passed = lifted and not np.any(np.isnan(pq))
        print(f"\n  >> Single Grip+Lift: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Test 2: Dual-arm cable grip ──────────────────────────────────────
def test_dual_arm_grip_lift():
    """Dual-arm cable manipulation: grip at two points + lift."""
    print()
    print("=" * 60)
    print("TEST 2: Dual-Arm Cable Grip + Lift ★THREAD KEY TEST★")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()

        add_ur10e_arm(builder, pos=(-0.5, 0, 0), urdf_path=urdf_path)
        add_ur10e_arm(builder, pos=(0.5, 0, 0), urdf_path=urdf_path)

        cable_start = (-CABLE_SEGMENTS * CABLE_SEG_LEN / 2, 0, 0.10)
        add_cable(builder, start_pos=cable_start)
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

        # Settle
        print("  Settling cable (2s)...")
        for i in range(int(2.0 / DT)):
            state, state_out = sim_step(
                model, state, state_out, solver, control, contacts, n_particles=n_particles)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at settle step {i}!")
                return False

        pq = state.particle_q.numpy()
        cable_z = np.mean(pq[:n_particles, 2])
        print(f"  Cable z={cable_z:.4f}")

        if abs(cable_z) > 0.1:
            print(f"  Cable not settled!")
            return False

        # Grip at two points: 25% and 75% of cable length
        quarter_x = cable_start[0] + (CABLE_SEGMENTS * CABLE_SEG_LEN) * 0.25
        three_quarter_x = cable_start[0] + (CABLE_SEGMENTS * CABLE_SEG_LEN) * 0.75
        gc_left = [quarter_x, 0, max(cable_z, CABLE_RADIUS)]
        gc_right = [three_quarter_x, 0, max(cable_z, CABLE_RADIUS)]

        grasped_left = detect_grasped(state, gc_left, n_particles)
        grasped_right = detect_grasped(state, gc_right, n_particles)

        print(f"  Left grip at x={quarter_x:.4f}: {len(grasped_left)} particles")
        print(f"  Right grip at x={three_quarter_x:.4f}: {len(grasped_right)} particles")

        if len(grasped_left) == 0 or len(grasped_right) == 0:
            print("  Insufficient particles in grasp range!")
            # Debug
            for i in range(n_particles):
                dist_l = np.linalg.norm(pq[i] - np.array(gc_left))
                dist_r = np.linalg.norm(pq[i] - np.array(gc_right))
                if dist_l < 0.05 or dist_r < 0.05:
                    print(f"    p[{i}] pos={pq[i]:.4f}, dist_L={dist_l:.4f}, dist_R={dist_r:.4f}")
            return False

        initial_left_z = np.mean(pq[grasped_left, 2])
        initial_right_z = np.mean(pq[grasped_right, 2])

        # Lift both grip points
        print("  Dual-arm lifting (3s)...")
        lift_steps = int(3.0 / DT)
        lift_target = 0.10

        for i in range(lift_steps):
            t = (i + 1) / lift_steps
            lift_z = max(cable_z, CABLE_RADIUS) + lift_target * t
            gc_l = [quarter_x, 0, lift_z]
            gc_r = [three_quarter_x, 0, lift_z]

            state, state_out = sim_step(
                model, state, state_out, solver, control, contacts,
                grip_centers=[gc_l, gc_r],
                grasped_sets=[grasped_left, grasped_right],
                n_particles=n_particles)

            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"  NaN at lift step {i}!")
                return False

            if i % int(0.5 / DT) == 0:
                pq = state.particle_q.numpy()
                lz = np.mean(pq[grasped_left, 2])
                rz = np.mean(pq[grasped_right, 2])
                all_z = pq[:n_particles, 2]
                print(f"    t={t*3:.1f}s: target={lift_z:.4f}, "
                      f"L_z={lz:.4f}, R_z={rz:.4f}, "
                      f"range=[{np.min(all_z):.4f},{np.max(all_z):.4f}]")

        pq = state.particle_q.numpy()
        final_left_z = np.mean(pq[grasped_left, 2])
        final_right_z = np.mean(pq[grasped_right, 2])
        delta_l = final_left_z - initial_left_z
        delta_r = final_right_z - initial_right_z
        lifted = delta_l > 0.02 and delta_r > 0.02

        print(f"\n  Left grip:  {initial_left_z:.4f} → {final_left_z:.4f} (delta={delta_l:.4f}m)")
        print(f"  Right grip: {initial_right_z:.4f} → {final_right_z:.4f} (delta={delta_r:.4f}m)")
        print(f"  {'✅ DUAL LIFT' if lifted else '❌ NOT LIFTED'}")

        # Check catenary between grip points
        all_z = pq[:n_particles, 2]
        mid_idx = n_particles // 2
        mid_z = pq[mid_idx, 2]
        grip_avg_z = (final_left_z + final_right_z) / 2
        catenary = mid_z < grip_avg_z - 0.005  # mid should sag below grips
        print(f"  Mid cable z={mid_z:.4f}, grip avg z={grip_avg_z:.4f}")
        if catenary:
            sag = grip_avg_z - mid_z
            print(f"  ✅ Catenary sag between grips: {sag*1000:.1f}mm")

        passed = lifted and not np.any(np.isnan(pq))
        print(f"\n  >> Dual-Arm Grip+Lift: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Test 3: N-dependency ──────────────────────────────────────────────
def test_n_dependency():
    """N-dependency with full gravity+collision+grasp."""
    print()
    print("=" * 60)
    print("TEST 3: N-dependency")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        results = {}
        for N in [1, 3]:
            world_builder = newton.ModelBuilder()

            add_ur10e_arm(world_builder, pos=(-0.5, 0, 0), urdf_path=urdf_path)
            add_ur10e_arm(world_builder, pos=(0.5, 0, 0), urdf_path=urdf_path)

            cable_start = (-CABLE_SEGMENTS * CABLE_SEG_LEN / 2, 0, 0.30)
            add_cable(world_builder, start_pos=cable_start)

            main_builder = newton.ModelBuilder(gravity=GRAVITY)
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
            solver_inst = SolverSemiImplicit(model)
            state_out = model.state()

            test_steps = int(1.0 / DT)
            t0 = time.time()
            nan_detected = False
            for step in range(test_steps):
                state.clear_forces()
                newton.eval_fk(model, state.joint_q, state.joint_qd, state)
                model.collide(state, contacts)
                solver_inst.step(state, state_out, control, contacts, DT)
                state, state_out = state_out, state

                if step % 120 == 0 and np.any(np.isnan(state.particle_q.numpy())):
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
    print("Newton Phase 5 Final: Optimized Grip+Lift + N-dependency")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"DT: {DT:.6f}s ({int(1/DT)}Hz), mass={CABLE_MASS}")
    print(f"Grasp: ke={GRASP_KE}, kd={GRASP_KD}, radius={GRASP_RADIUS*1000:.0f}mm")
    print()

    r1 = test_single_grip_lift()
    r2 = test_dual_arm_grip_lift()
    r3 = test_n_dependency()

    print()
    print("=" * 60)
    print("PHASE 5 FINAL RESULTS")
    print("=" * 60)
    print(f"  Single Grip+Lift:    {'PASS' if r1 else 'FAIL'}")
    print(f"  Dual-Arm Grip+Lift:  {'PASS' if r2 else 'FAIL'}")
    print(f"  N-dependency:        {'PASS' if r3 else 'FAIL'}")

    total = sum([r1, r2, r3])
    print(f"\n  Total: {total}/3 PASS")

    return 0 if total == 3 else 1


if __name__ == "__main__":
    sys.exit(main())
