"""Newton Phase 7: Franka Panda URDF Import + PD Control + Cable Integration

Architecture decision:
- MuJoCo solver: handles articulated body PD joint drive
- SemiImplicit solver: handles particle chain cable (gravity + collision)
- Hybrid stepping: MuJoCo(joints) → SemiImplicit(particles) → merge state
- This is necessary because SemiImplicit does not support PD joint drive,
  and MuJoCo does not advance particles.

Staged verification:
1. URDF import — load panda_independent_fingers.urdf, verify joint/link counts
2. Joint PD control — drive arm joints to targets via MuJoCo, verify convergence
3. Finger prismatic control — open/close fingers via MuJoCo PD
4. Dual-arm — two Franka arms, independent control
5. Franka + cable — hybrid solver, grip + lift with particle chain cable

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_phase7_franka.py
"""

import time
import sys
import os
import numpy as np
import warp as wp
import newton
from newton.solvers import SolverSemiImplicit, SolverMuJoCo

DEVICE = "cuda:0"
GRAVITY = -9.81
DT = 1.0 / 480.0

# Franka URDF path
FRANKA_URDF = os.path.normpath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "source", "extensions", "isaaclab_tasks_thread", "data", "robots",
    "panda_independent_fingers.urdf",
))

# Arm PD (joints 1-7: revolute)
ARM_KE = 8000.0
ARM_KD = 400.0

# Finger PD (joints 8-9: prismatic)
FINGER_KE = 2000.0
FINGER_KD = 100.0

# Cable parameters (from Phase 5)
CABLE_SEGMENTS = 40
CABLE_SEG_LEN = 0.0075
CABLE_MASS = 0.1
CABLE_RADIUS = 0.004
CABLE_KE = 1.0e4
CABLE_KD = 10.0

# Contact
PARTICLE_CONTACT_KE = 5.0e4
PARTICLE_CONTACT_KD = 100.0
PARTICLE_CONTACT_MU = 0.8

# Grasp constraint
GRASP_KE = 1000.0
GRASP_KD = 50.0
GRASP_RADIUS = 0.03

# Franka-legacy standalone (NOT the UR5e substrate of S2): this Phase-7 Franka test
# keeps its own 9-DOF / EE-body-6 layout; do not confuse with the task_config UR5e SSOT.
FRANKA_NUM_REVOLUTE = 7
FRANKA_NUM_PRISMATIC = 2
FRANKA_NUM_JOINTS = 9


def add_franka_arm(builder, pos, arm_ke=ARM_KE, arm_kd=ARM_KD,
                   finger_ke=FINGER_KE, finger_kd=FINGER_KD):
    """Add a Franka Panda arm to the builder."""
    n_before = len(builder.joint_target_ke)
    builder.add_urdf(
        FRANKA_URDF,
        xform=wp.transform(pos, wp.quat_identity()),
        floating=False,
        enable_self_collisions=False,
        collapse_fixed_joints=True,
    )
    n_after = len(builder.joint_target_ke)
    for i in range(n_before, n_after):
        jt = builder.joint_type[i]
        if jt == newton.JointType.REVOLUTE:
            builder.joint_target_ke[i] = arm_ke
            builder.joint_target_kd[i] = arm_kd
        elif jt == newton.JointType.PRISMATIC:
            builder.joint_target_ke[i] = finger_ke
            builder.joint_target_kd[i] = finger_kd
        builder.joint_target_mode[i] = newton.JointTargetMode.POSITION_VELOCITY.value
    return n_before, n_after, n_after - n_before


def add_cable(builder, start_pos, direction=(1, 0, 0)):
    """Add a particle chain cable."""
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
        for c in range(3):
            pf[idx][c] += -GRASP_KE * (pos[c] - grip_center[c]) - GRASP_KD * vel[c]
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


def mujoco_step(model, state, state_out, solver, control, contacts):
    """MuJoCo step for articulated bodies (joints only)."""
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, DT)
    return state_out


def semi_step(model, state, state_out, solver, control, contacts,
              grip_centers=None, grasped_sets=None, n_particles=0):
    """SemiImplicit step for particles (cable)."""
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    if grip_centers and grasped_sets:
        for gc, gi in zip(grip_centers, grasped_sets):
            apply_grasp_forces(state, gc, gi, n_particles)
    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, DT)
    return state_out


def hybrid_step(model, state, state_mj, state_semi,
                mujoco_solver, semi_solver, control, contacts,
                grip_centers=None, grasped_sets=None, n_particles=0):
    """Hybrid step: MuJoCo for joints, SemiImplicit for particles, merge."""
    # Step 1: MuJoCo (joints)
    mujoco_step(model, state, state_mj, mujoco_solver, control, contacts)

    # Step 2: SemiImplicit (particles)
    semi_step(model, state, state_semi, semi_solver, control, contacts,
              grip_centers, grasped_sets, n_particles)

    # Step 3: Merge — MuJoCo joints + SemiImplicit particles into state_semi
    state_semi.joint_q.assign(state_mj.joint_q.numpy())
    state_semi.joint_qd.assign(state_mj.joint_qd.numpy())
    newton.eval_fk(model, state_semi.joint_q, state_semi.joint_qd, state_semi)

    return state_semi


# ── Test 1: URDF Import ─────────────────────────────────────────────
def test_urdf_import():
    """Load Franka Panda URDF and verify structure."""
    print("=" * 60)
    print("TEST 1: Franka Panda URDF Import")
    print("=" * 60)

    if not os.path.isfile(FRANKA_URDF):
        print(f"  URDF not found: {FRANKA_URDF}")
        return False

    print(f"  URDF: {FRANKA_URDF}")

    builder = newton.ModelBuilder(gravity=GRAVITY)
    builder.add_ground_plane()
    j_start, j_end, n_added = add_franka_arm(builder, pos=(0, 0, 0))
    print(f"  Joints added: {n_added}")

    revolute_count = sum(1 for i in range(j_start, j_end)
                         if builder.joint_type[i] == newton.JointType.REVOLUTE)
    prismatic_count = sum(1 for i in range(j_start, j_end)
                          if builder.joint_type[i] == newton.JointType.PRISMATIC)

    print(f"  Revolute: {revolute_count}, Prismatic: {prismatic_count}")

    try:
        model = builder.finalize(device=DEVICE)
        print(f"  Model finalized: joint_q={model.joint_q.shape}, body_count={model.body_count}")
    except Exception as e:
        print(f"  Finalize failed: {e}")
        return False

    try:
        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        body_q = state.body_q.numpy()
        ee_pos = body_q[-1][:3]
        print(f"  FK OK, EE pos: ({ee_pos[0]:.4f}, {ee_pos[1]:.4f}, {ee_pos[2]:.4f})")
    except Exception as e:
        print(f"  FK failed: {e}")
        return False

    passed = revolute_count >= FRANKA_NUM_REVOLUTE and prismatic_count >= FRANKA_NUM_PRISMATIC
    print(f"\n  >> URDF Import: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Test 2: Arm Joint PD Control (MuJoCo) ────────────────────────────
def test_arm_pd_control():
    """Drive arm joints to targets via MuJoCo solver."""
    print()
    print("=" * 60)
    print("TEST 2: Arm Joint PD Control (MuJoCo)")
    print("=" * 60)

    builder = newton.ModelBuilder(gravity=GRAVITY)
    builder.add_ground_plane()
    j_start, j_end, n_added = add_franka_arm(builder, pos=(0, 0, 0))

    model = builder.finalize(device=DEVICE)
    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    contacts = model.contacts()
    control = model.control()
    solver = SolverMuJoCo(model, iterations=4, ls_iterations=4, disable_contacts=True)
    state_out = model.state()

    arm_targets = [0.3, -0.3, 0.2, -1.5, 0.1, 1.0, 0.5]
    target_pos = control.joint_target_pos.numpy()
    for i, target in enumerate(arm_targets):
        if j_start + i < len(target_pos):
            target_pos[j_start + i] = target
    control.joint_target_pos.assign(target_pos)

    print(f"  Targets: {arm_targets}")
    print("  Simulating 3s...")
    steps = int(3.0 / DT)

    for step in range(steps):
        state_out = mujoco_step(model, state, state_out, solver, control, contacts)
        state, state_out = state_out, state

        if step % int(0.5 / DT) == 0:
            jq = state.joint_q.numpy()
            errors = [abs(jq[j_start + i] - t) for i, t in enumerate(arm_targets)
                      if j_start + i < len(jq)]
            print(f"    t={step*DT:.1f}s: max_err={max(errors):.6f} rad")

        if np.any(np.isnan(state.joint_q.numpy())):
            print(f"  NaN at step {step}")
            return False

    jq = state.joint_q.numpy()
    errors = []
    for i, target in enumerate(arm_targets):
        if j_start + i < len(jq):
            err = abs(jq[j_start + i] - target)
            errors.append(err)
            print(f"  J{i+1}: target={target:.4f}, actual={jq[j_start+i]:.6f}, err={err:.6f}")

    max_err = max(errors) if errors else float('inf')
    converged = max_err < 0.01
    print(f"\n  Max error: {max_err:.6f} rad")
    print(f"  >> Arm PD Control: {'PASS' if converged else 'FAIL'}")
    return converged


# ── Test 3: Finger Prismatic Control (MuJoCo) ────────────────────────
def test_finger_control():
    """Open/close fingers via MuJoCo PD control."""
    print()
    print("=" * 60)
    print("TEST 3: Finger Prismatic Control (MuJoCo)")
    print("=" * 60)

    builder = newton.ModelBuilder(gravity=GRAVITY)
    builder.add_ground_plane()
    j_start, j_end, n_added = add_franka_arm(builder, pos=(0, 0, 0))

    prismatic_indices = [i for i in range(j_start, j_end)
                         if builder.joint_type[i] == newton.JointType.PRISMATIC]
    print(f"  Prismatic joints: {prismatic_indices}")
    if len(prismatic_indices) < 2:
        print(f"  Expected 2 prismatic, found {len(prismatic_indices)}")
        return False

    model = builder.finalize(device=DEVICE)
    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    contacts = model.contacts()
    control = model.control()
    solver = SolverMuJoCo(model, iterations=4, ls_iterations=4, disable_contacts=True)
    state_out = model.state()

    # Phase 1: Open
    print("  Phase 1: Opening (target=0.04m)...")
    target_pos = control.joint_target_pos.numpy()
    for pi in prismatic_indices:
        target_pos[pi] = 0.04
    control.joint_target_pos.assign(target_pos)

    for step in range(int(2.0 / DT)):
        state_out = mujoco_step(model, state, state_out, solver, control, contacts)
        state, state_out = state_out, state
        if np.any(np.isnan(state.joint_q.numpy())):
            print(f"  NaN at step {step}")
            return False

    jq = state.joint_q.numpy()
    open_pos = [jq[pi] for pi in prismatic_indices]
    print(f"  Open: {[f'{p:.4f}' for p in open_pos]}")
    open_ok = all(abs(p - 0.04) < 0.005 for p in open_pos)

    # Phase 2: Close
    print("  Phase 2: Closing (target=0.0m)...")
    target_pos = control.joint_target_pos.numpy()
    for pi in prismatic_indices:
        target_pos[pi] = 0.0
    control.joint_target_pos.assign(target_pos)

    for step in range(int(2.0 / DT)):
        state_out = mujoco_step(model, state, state_out, solver, control, contacts)
        state, state_out = state_out, state
        if np.any(np.isnan(state.joint_q.numpy())):
            print(f"  NaN at step {step}")
            return False

    jq = state.joint_q.numpy()
    close_pos = [jq[pi] for pi in prismatic_indices]
    print(f"  Close: {[f'{p:.4f}' for p in close_pos]}")
    close_ok = all(abs(p) < 0.005 for p in close_pos)

    passed = open_ok and close_ok
    print(f"  Open: {'OK' if open_ok else 'FAIL'}, Close: {'OK' if close_ok else 'FAIL'}")
    print(f"\n  >> Finger Control: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Test 4: Dual-Arm Franka (MuJoCo) ─────────────────────────────────
def test_dual_arm():
    """Two Franka arms with independent MuJoCo PD control."""
    print()
    print("=" * 60)
    print("TEST 4: Dual-Arm Franka Control (MuJoCo)")
    print("=" * 60)

    builder = newton.ModelBuilder(gravity=GRAVITY)
    builder.add_ground_plane()
    left_start, left_end, left_n = add_franka_arm(builder, pos=(0, -0.5, 0))
    right_start, right_end, right_n = add_franka_arm(builder, pos=(0, 0.5, 0))

    print(f"  Left: [{left_start}:{left_end}], Right: [{right_start}:{right_end}]")

    model = builder.finalize(device=DEVICE)
    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    contacts = model.contacts()
    control = model.control()
    solver = SolverMuJoCo(model, iterations=4, ls_iterations=4, disable_contacts=True)
    state_out = model.state()

    left_targets = [0.3, -0.3, 0.2, -1.5, 0.1, 1.0, 0.5]
    right_targets = [-0.3, 0.3, -0.2, -1.5, -0.1, 1.0, -0.5]

    target_pos = control.joint_target_pos.numpy()
    for i, t in enumerate(left_targets):
        idx = left_start + i
        if idx < len(target_pos):
            target_pos[idx] = t
    for i, t in enumerate(right_targets):
        idx = right_start + i
        if idx < len(target_pos):
            target_pos[idx] = t
    control.joint_target_pos.assign(target_pos)

    print("  Simulating 3s...")
    for step in range(int(3.0 / DT)):
        state_out = mujoco_step(model, state, state_out, solver, control, contacts)
        state, state_out = state_out, state
        if np.any(np.isnan(state.joint_q.numpy())):
            print(f"  NaN at step {step}")
            return False

    jq = state.joint_q.numpy()
    left_errors = [abs(jq[left_start + i] - t) for i, t in enumerate(left_targets)
                   if left_start + i < len(jq)]
    right_errors = [abs(jq[right_start + i] - t) for i, t in enumerate(right_targets)
                    if right_start + i < len(jq)]

    max_left = max(left_errors) if left_errors else float('inf')
    max_right = max(right_errors) if right_errors else float('inf')
    print(f"  Left max err: {max_left:.6f}, Right max err: {max_right:.6f}")

    # Independence check
    independent = True
    for i in range(min(len(left_targets), len(right_targets))):
        if abs(left_targets[i] - right_targets[i]) > 0.1:
            l_val = jq[left_start + i] if left_start + i < len(jq) else 0
            r_val = jq[right_start + i] if right_start + i < len(jq) else 0
            if abs(l_val - r_val) < 0.05:
                independent = False

    converged = max_left < 0.01 and max_right < 0.01
    passed = converged and independent
    print(f"  Converged: {'OK' if converged else 'FAIL'}, Independent: {'OK' if independent else 'FAIL'}")
    print(f"\n  >> Dual-Arm: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Test 5: Franka + Cable (Hybrid) ──────────────────────────────────
def test_franka_cable_lift():
    """Dual-arm Franka + cable: hybrid MuJoCo+SemiImplicit solver."""
    print()
    print("=" * 60)
    print("TEST 5: Franka + Cable Grip+Lift (Hybrid) ★THREAD KEY★")
    print("=" * 60)

    builder = newton.ModelBuilder(gravity=GRAVITY)
    builder.add_ground_plane()
    left_start, left_end, left_n = add_franka_arm(builder, pos=(0, -0.3, 0))
    right_start, right_end, right_n = add_franka_arm(builder, pos=(0, 0.3, 0))

    cable_start = (0, -0.15, 0.10)
    particles = add_cable(builder, start_pos=cable_start, direction=(0, 1, 0))
    n_particles = len(particles)

    model = builder.finalize(device=DEVICE)
    model.particle_ke = PARTICLE_CONTACT_KE
    model.particle_kd = PARTICLE_CONTACT_KD
    model.particle_mu = PARTICLE_CONTACT_MU

    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    contacts = model.contacts()
    control = model.control()

    mujoco_solver = SolverMuJoCo(model, iterations=4, ls_iterations=4, disable_contacts=True)
    semi_solver = SolverSemiImplicit(model)

    state_mj = model.state()
    state_semi = model.state()

    # Settle cable 2s (SemiImplicit only — arms are kinematic/static)
    print("  Settling cable (2s)...")
    state_out = model.state()
    for i in range(int(2.0 / DT)):
        state.clear_forces()
        newton.eval_fk(model, state.joint_q, state.joint_qd, state)
        model.collide(state, contacts)
        semi_solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state
        if np.any(np.isnan(state.particle_q.numpy())):
            print(f"  NaN at settle step {i}")
            return False

    pq = state.particle_q.numpy()
    cable_z = np.mean(pq[:n_particles, 2])
    print(f"  Cable settled: mean z={cable_z:.4f}")

    if abs(cable_z) > 0.15:
        print(f"  Cable not settled")
        return False

    # Detect graspable particles
    quarter_y = cable_start[1] + (CABLE_SEGMENTS * CABLE_SEG_LEN) * 0.25
    three_quarter_y = cable_start[1] + (CABLE_SEGMENTS * CABLE_SEG_LEN) * 0.75
    gc_left = [0, quarter_y, max(cable_z, CABLE_RADIUS)]
    gc_right = [0, three_quarter_y, max(cable_z, CABLE_RADIUS)]

    grasped_left = detect_grasped(state, gc_left, n_particles)
    grasped_right = detect_grasped(state, gc_right, n_particles)

    print(f"  Left grip: {len(grasped_left)} particles")
    print(f"  Right grip: {len(grasped_right)} particles")

    if len(grasped_left) == 0 or len(grasped_right) == 0:
        print("  No particles in grasp range")
        return False

    initial_left_z = np.mean(pq[grasped_left, 2])
    initial_right_z = np.mean(pq[grasped_right, 2])

    # Lift 3s using hybrid solver
    print("  Hybrid lifting (3s, 10cm target)...")
    lift_steps = int(3.0 / DT)
    lift_target = 0.10

    for i in range(lift_steps):
        t = (i + 1) / lift_steps
        lift_z = max(cable_z, CABLE_RADIUS) + lift_target * t
        gc_l = [0, quarter_y, lift_z]
        gc_r = [0, three_quarter_y, lift_z]

        result = hybrid_step(
            model, state, state_mj, state_semi,
            mujoco_solver, semi_solver, control, contacts,
            grip_centers=[gc_l, gc_r],
            grasped_sets=[grasped_left, grasped_right],
            n_particles=n_particles)

        # Rotate states
        state, state_semi = result, state
        state_mj = model.state()

        if np.any(np.isnan(state.particle_q.numpy())):
            print(f"  NaN at lift step {i}")
            return False

        if i % int(0.5 / DT) == 0:
            pq = state.particle_q.numpy()
            lz = np.mean(pq[grasped_left, 2])
            rz = np.mean(pq[grasped_right, 2])
            print(f"    t={t*3:.1f}s: target_z={lift_z:.4f}, L_z={lz:.4f}, R_z={rz:.4f}")

    pq = state.particle_q.numpy()
    final_left_z = np.mean(pq[grasped_left, 2])
    final_right_z = np.mean(pq[grasped_right, 2])
    delta_l = final_left_z - initial_left_z
    delta_r = final_right_z - initial_right_z

    lifted = delta_l > 0.02 and delta_r > 0.02

    print(f"\n  Left:  {initial_left_z:.4f} -> {final_left_z:.4f} (+{delta_l*1000:.1f}mm)")
    print(f"  Right: {initial_right_z:.4f} -> {final_right_z:.4f} (+{delta_r*1000:.1f}mm)")

    # Check catenary
    mid_idx = n_particles // 2
    mid_z = pq[mid_idx, 2]
    grip_avg_z = (final_left_z + final_right_z) / 2
    if mid_z < grip_avg_z - 0.005:
        sag = grip_avg_z - mid_z
        print(f"  Catenary sag: {sag*1000:.1f}mm")

    print(f"  {'DUAL LIFT OK' if lifted else 'NOT LIFTED'}")

    passed = lifted and not np.any(np.isnan(pq))
    print(f"\n  >> Franka + Cable Lift: {'PASS' if passed else 'FAIL'}")
    return passed


# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("Newton Phase 7: Franka Panda URDF + Hybrid Solver")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"DT: {DT:.6f}s ({int(1/DT)}Hz)")
    print(f"URDF: {FRANKA_URDF} (exists={os.path.isfile(FRANKA_URDF)})")
    print(f"Architecture: MuJoCo(joints) + SemiImplicit(particles)")
    print()

    results = {}
    results["urdf_import"] = test_urdf_import()
    results["arm_pd"] = test_arm_pd_control()
    results["finger_ctrl"] = test_finger_control()
    results["dual_arm"] = test_dual_arm()
    results["cable_lift"] = test_franka_cable_lift()

    print()
    print("=" * 60)
    print("PHASE 7 RESULTS")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {name:20s}: {'PASS' if passed else 'FAIL'}")

    total = sum(results.values())
    count = len(results)
    print(f"\n  Total: {total}/{count} PASS")

    return 0 if total == count else 1


if __name__ == "__main__":
    sys.exit(main())
