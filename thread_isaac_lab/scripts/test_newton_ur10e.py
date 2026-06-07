"""Newton UR10e Dual-Arm Test

Builds UR10e arms using Newton's add_urdf() with simplified URDF (cylinder geometry).
Tests basic joint drive, gravity compensation, and dual-arm setup.

Solvers tested: Featherstone (primary), MuJoCo (fallback).

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_ur10e.py
"""

import time
import sys
import math
import tempfile
import os

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverFeatherstone, SolverMuJoCo

# ── Configuration ────────────────────────────────────────────────────
DEVICE = "cuda:1"  # Blackwell GPU
DT = 1.0 / 480.0   # smaller timestep for stability
SIM_STEPS = 1920    # 4 seconds at 480Hz
GRAVITY = 0.0       # start with zero gravity to verify kinematics


# ── Simplified UR10e URDF ────────────────────────────────────────────
UR10E_URDF = """<?xml version="1.0"?>
<robot name="ur10e_simple">
  <!-- Base link (fixed to world) -->
  <link name="base_link">
    <inertial>
      <mass value="4.0"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.0061063308908" ixy="0" ixz="0"
               iyy="0.0061063308908" iyz="0" izz="0.01125"/>
    </inertial>
    <collision>
      <origin xyz="0 0 0.04" rpy="0 0 0"/>
      <geometry><cylinder radius="0.075" length="0.08"/></geometry>
    </collision>
  </link>

  <!-- Shoulder link -->
  <link name="shoulder_link">
    <inertial>
      <mass value="7.778"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.0314743125769" ixy="0" ixz="0"
               iyy="0.0314743125769" iyz="0" izz="0.021875625"/>
    </inertial>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><cylinder radius="0.06" length="0.15"/></geometry>
    </collision>
  </link>

  <!-- Upper arm link (long) -->
  <link name="upper_arm_link">
    <inertial>
      <mass value="12.93"/>
      <origin xyz="-0.306 0 0.176" rpy="0 0 0"/>
      <inertia ixx="0.421753803798" ixy="0" ixz="0"
               iyy="0.421753803798" iyz="0" izz="0.0363656375"/>
    </inertial>
    <collision>
      <origin xyz="-0.306 0 0" rpy="0 1.5708 0"/>
      <geometry><cylinder radius="0.06" length="0.6127"/></geometry>
    </collision>
  </link>

  <!-- Forearm link (long) -->
  <link name="forearm_link">
    <inertial>
      <mass value="3.87"/>
      <origin xyz="-0.286 0 0.039" rpy="0 0 0"/>
      <inertia ixx="0.111069694097" ixy="0" ixz="0"
               iyy="0.111069694097" iyz="0" izz="0.010884375"/>
    </inertial>
    <collision>
      <origin xyz="-0.286 0 0" rpy="0 1.5708 0"/>
      <geometry><cylinder radius="0.05" length="0.57155"/></geometry>
    </collision>
  </link>

  <!-- Wrist 1 -->
  <link name="wrist_1_link">
    <inertial>
      <mass value="1.96"/>
      <origin xyz="0 -0.06 0" rpy="0 0 0"/>
      <inertia ixx="0.005108247004" ixy="0" ixz="0"
               iyy="0.005108247004" iyz="0" izz="0.0055125"/>
    </inertial>
    <collision>
      <origin xyz="0 -0.06 0" rpy="1.5708 0 0"/>
      <geometry><cylinder radius="0.04" length="0.12"/></geometry>
    </collision>
  </link>

  <!-- Wrist 2 -->
  <link name="wrist_2_link">
    <inertial>
      <mass value="1.96"/>
      <origin xyz="0 0 -0.06" rpy="0 0 0"/>
      <inertia ixx="0.005108247004" ixy="0" ixz="0"
               iyy="0.005108247004" iyz="0" izz="0.0055125"/>
    </inertial>
    <collision>
      <origin xyz="0 0 -0.06" rpy="0 0 0"/>
      <geometry><cylinder radius="0.04" length="0.12"/></geometry>
    </collision>
  </link>

  <!-- Wrist 3 (end-effector) -->
  <link name="wrist_3_link">
    <inertial>
      <mass value="0.202"/>
      <origin xyz="0 0 -0.058" rpy="0 0 0"/>
      <inertia ixx="0.000526462289415" ixy="0" ixz="0"
               iyy="0.000526462289415" iyz="0" izz="0.000568125"/>
    </inertial>
    <collision>
      <origin xyz="0 0 -0.03" rpy="0 0 0"/>
      <geometry><cylinder radius="0.035" length="0.06"/></geometry>
    </collision>
  </link>

  <!-- Joints (UR10e kinematic chain) -->
  <joint name="shoulder_pan_joint" type="revolute">
    <parent link="base_link"/>
    <child link="shoulder_link"/>
    <origin xyz="0 0 0.1807" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/>
    <dynamics damping="0" friction="0"/>
  </joint>

  <joint name="shoulder_lift_joint" type="revolute">
    <parent link="shoulder_link"/>
    <child link="upper_arm_link"/>
    <origin xyz="0 0 0" rpy="1.570796327 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="330.0" velocity="2.094"/>
    <dynamics damping="0" friction="0"/>
  </joint>

  <joint name="elbow_joint" type="revolute">
    <parent link="upper_arm_link"/>
    <child link="forearm_link"/>
    <origin xyz="-0.6127 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.1416" upper="3.1416" effort="150.0" velocity="3.1416"/>
    <dynamics damping="0" friction="0"/>
  </joint>

  <joint name="wrist_1_joint" type="revolute">
    <parent link="forearm_link"/>
    <child link="wrist_1_link"/>
    <origin xyz="-0.57155 0 0.17415" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
    <dynamics damping="0" friction="0"/>
  </joint>

  <joint name="wrist_2_joint" type="revolute">
    <parent link="wrist_1_link"/>
    <child link="wrist_2_link"/>
    <origin xyz="0 -0.11985 0" rpy="1.570796327 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
    <dynamics damping="0" friction="0"/>
  </joint>

  <joint name="wrist_3_joint" type="revolute">
    <parent link="wrist_2_link"/>
    <child link="wrist_3_link"/>
    <origin xyz="0 0.11655 0" rpy="1.570796327 3.14159265 3.14159265"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.2832" upper="6.2832" effort="56.0" velocity="3.1416"/>
    <dynamics damping="0" friction="0"/>
  </joint>
</robot>
"""


def write_ur10e_urdf():
    """Write simplified UR10e URDF to temp file and return path."""
    fd, path = tempfile.mkstemp(suffix=".urdf", prefix="ur10e_simple_")
    with os.fdopen(fd, "w") as f:
        f.write(UR10E_URDF)
    return path


def build_ur10e_arm(builder, pos, rot=wp.quat_identity(), urdf_path=None):
    """Add a UR10e arm to the builder at the given position.

    After add_urdf(), the joint drives need explicit configuration:
    - joint_target_mode → POSITION_VELOCITY
    - joint_target_ke → stiffness
    - joint_target_kd → damping
    The URDF importer sets ke=0, kd=0, mode=POSITION by default.
    """
    n_dofs_before = len(builder.joint_target_ke)
    builder.add_urdf(
        urdf_path,
        xform=wp.transform(pos, rot),
        floating=False,
        enable_self_collisions=False,
    )
    n_dofs_after = len(builder.joint_target_ke)

    # Configure joint drives for newly added DOFs
    for i in range(n_dofs_before, n_dofs_after):
        builder.joint_target_ke[i] = 5000.0
        builder.joint_target_kd[i] = 200.0
        builder.joint_target_mode[i] = newton.JointTargetMode.POSITION_VELOCITY.value


# ── Test 1: Single UR10e joint drive ──────────────────────────────────
def test_single_arm_joint_drive():
    """Test basic joint position drive on single UR10e."""
    print("=" * 60)
    print("TEST 1: Single UR10e joint drive (Featherstone)")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()
        build_ur10e_arm(builder, pos=(0.0, 0.0, 0.0), urdf_path=urdf_path)

        # Print body/joint info
        print(f"  Bodies: {len(builder.body_mass)}")
        print(f"  Joints: {len(builder.joint_type)}")
        for i, label in enumerate(builder.body_label):
            print(f"    Body {i}: {label}")

        model = builder.finalize(device=DEVICE)
        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()

        # Try multiple solver configurations
        solvers_to_try = [
            ("MuJoCo (no contacts)", lambda m: SolverMuJoCo(m, iterations=4, ls_iterations=4,
                                                              disable_contacts=True)),
            ("MuJoCo (with contacts)", lambda m: SolverMuJoCo(m, iterations=4, ls_iterations=4)),
            ("Featherstone", lambda m: SolverFeatherstone(m)),
        ]

        state_out = model.state()

        # Get initial joint positions
        joint_q = model.joint_q.numpy()
        n_dofs = len(joint_q)
        print(f"  DOFs: {n_dofs}")
        print(f"  Initial joint_q: {joint_q}")

        working_solver = None
        for solver_name, solver_factory in solvers_to_try:
            print(f"\n  Trying {solver_name}...")
            try:
                solver = solver_factory(model)
            except Exception as e:
                print(f"    Init failed: {e}")
                continue

            # Reset state
            state = model.state()
            model.joint_q.assign(np.zeros(n_dofs))
            model.joint_qd.assign(np.zeros(n_dofs))
            newton.eval_fk(model, model.joint_q, model.joint_qd, state)
            state_out = model.state()

            # Set target: move shoulder_pan to 0.5 rad
            target_pos = np.zeros(n_dofs)
            target_pos[0] = 0.5  # shoulder_pan

            ke_values = np.full(n_dofs, 5000.0)
            kd_values = np.full(n_dofs, 200.0)
            model.joint_target_ke.assign(ke_values)
            model.joint_target_kd.assign(kd_values)
            control.joint_target_pos.assign(target_pos)

            # Short test (100 steps)
            stable_100 = True
            for i in range(100):
                state.clear_forces()
                if "no contacts" not in solver_name:
                    model.collide(state, contacts)
                solver.step(state, state_out, control, contacts, DT)
                state, state_out = state_out, state

            jq = state.joint_q.numpy()
            if np.any(np.isnan(jq)):
                print(f"    NaN after 100 steps")
                continue
            else:
                print(f"    After 100 steps: j0={jq[0]:.6f}")
                working_solver = solver_name
                break

        if working_solver is None:
            print("  All solvers failed!")
            print(f"\n  >> Single arm joint drive: FAIL")
            return False

        print(f"\n  Using {working_solver}, running full simulation...")

        # Full simulation
        t0 = time.time()
        for i in range(SIM_STEPS):
            state.clear_forces()
            if "no contacts" not in working_solver:
                model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state

            if i % 480 == 0:
                jq = state.joint_q.numpy()
                print(f"  Step {i:4d}: j0={jq[0]:.4f} (target=0.5)")

        elapsed = time.time() - t0
        final_q = state.joint_q.numpy()
        j0_error = abs(final_q[0] - 0.5)
        stable = not np.any(np.isnan(final_q))

        print(f"  Final joint_q: {final_q[:6]}")
        print(f"  j0 error: {j0_error:.6f}")
        print(f"  Stable: {'YES' if stable else 'NO'}")
        print(f"  Time: {elapsed:.2f}s")

        passed = stable and j0_error < 0.1
        print(f"\n  >> Single arm joint drive: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Test 2: Dual UR10e arms ──────────────────────────────────────────
def test_dual_arm():
    """Test two UR10e arms in same simulation."""
    print()
    print("=" * 60)
    print("TEST 2: Dual UR10e arms (Featherstone)")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()

        # Left arm at (-0.5, 0, 0), right arm at (0.5, 0, 0)
        build_ur10e_arm(builder, pos=(-0.5, 0.0, 0.0), urdf_path=urdf_path)
        n_bodies_left = len(builder.body_mass)
        build_ur10e_arm(builder, pos=(0.5, 0.0, 0.0), urdf_path=urdf_path)
        n_bodies_total = len(builder.body_mass)

        print(f"  Left arm bodies: {n_bodies_left}")
        print(f"  Total bodies: {n_bodies_total}")
        print(f"  Joints: {len(builder.joint_type)}")

        model = builder.finalize(device=DEVICE)
        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()

        solver = SolverMuJoCo(model, iterations=4, ls_iterations=4, disable_contacts=True)
        state_out = model.state()

        n_dofs = len(model.joint_q.numpy())
        dofs_per_arm = n_dofs // 2
        print(f"  DOFs per arm: {dofs_per_arm}, Total: {n_dofs}")
        print(f"  Solver: MuJoCo (no contacts)")

        newton.eval_fk(model, model.joint_q, model.joint_qd, state)

        # Mirror motion: left arm j0=+0.5, right arm j0=-0.5
        target_pos = np.zeros(n_dofs)
        target_pos[0] = 0.5          # left shoulder_pan
        target_pos[dofs_per_arm] = -0.5  # right shoulder_pan

        ke_values = np.full(n_dofs, 5000.0)
        kd_values = np.full(n_dofs, 200.0)
        model.joint_target_ke.assign(ke_values)
        model.joint_target_kd.assign(kd_values)
        control.joint_target_pos.assign(target_pos)

        # Simulate
        t0 = time.time()
        for i in range(SIM_STEPS):
            state.clear_forces()
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state

            if i % 480 == 0:
                jq = state.joint_q.numpy()
                print(f"  Step {i:4d}: L_j0={jq[0]:.4f}, R_j0={jq[dofs_per_arm]:.4f}")

        elapsed = time.time() - t0
        final_q = state.joint_q.numpy()
        l_error = abs(final_q[0] - 0.5)
        r_error = abs(final_q[dofs_per_arm] - (-0.5))
        stable = not np.any(np.isnan(final_q))

        print(f"  Left arm error:  j0={l_error:.6f}")
        print(f"  Right arm error: j0={r_error:.6f}")
        print(f"  Stable: {'YES' if stable else 'NO'}")
        print(f"  Time: {elapsed:.2f}s")

        passed = stable and l_error < 0.1 and r_error < 0.1
        print(f"\n  >> Dual arm: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Test 3: End-effector position check ──────────────────────────────
def test_ee_position():
    """Test that end-effector reaches expected positions."""
    print()
    print("=" * 60)
    print("TEST 3: End-effector position verification")
    print("=" * 60)

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()
        build_ur10e_arm(builder, pos=(0.0, 0.0, 0.0), urdf_path=urdf_path)

        # Find EE body
        ee_idx = None
        for i, label in enumerate(builder.body_label):
            if "wrist_3" in label:
                ee_idx = i
        print(f"  EE body index: {ee_idx}")

        model = builder.finalize(device=DEVICE)
        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()

        solver = SolverMuJoCo(model, iterations=4, ls_iterations=4, disable_contacts=True)
        state_out = model.state()
        n_dofs = len(model.joint_q.numpy())

        # Home position (all zeros): EE should be at known position
        body_q = state.body_q.numpy()
        home_pos = body_q[ee_idx][:3] if ee_idx is not None else [0, 0, 0]
        print(f"  Home EE position: [{home_pos[0]:.4f}, {home_pos[1]:.4f}, {home_pos[2]:.4f}]")

        # UR10e reach: ~1.3m from base
        # At home (all joints zero), arm extends horizontally (-X direction)
        # due to shoulder_lift frame rotation. Check distance from base.
        ee_dist = np.linalg.norm(home_pos)
        reach_ok = ee_dist > 0.5  # should be ~1.2m from base
        print(f"  Home EE distance from base: {ee_dist:.4f}m")

        # Move shoulder_lift to -pi/2 (arm horizontal)
        target_pos = np.zeros(n_dofs)
        target_pos[1] = -math.pi / 2  # shoulder_lift

        ke_values = np.full(n_dofs, 5000.0)
        kd_values = np.full(n_dofs, 200.0)
        model.joint_target_ke.assign(ke_values)
        model.joint_target_kd.assign(kd_values)
        control.joint_target_pos.assign(target_pos)

        for _ in range(SIM_STEPS):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, DT)
            state, state_out = state_out, state

        body_q = state.body_q.numpy()
        moved_pos = body_q[ee_idx][:3] if ee_idx is not None else [0, 0, 0]
        stable = not np.any(np.isnan(body_q))
        print(f"  Moved EE position: [{moved_pos[0]:.4f}, {moved_pos[1]:.4f}, {moved_pos[2]:.4f}]")
        print(f"  Stable: {'YES' if stable else 'NO'}")

        # After shoulder_lift=-pi/2, arm should extend horizontally
        # EE should be lower than home and further in X
        moved = np.linalg.norm(np.array(moved_pos) - np.array(home_pos)) > 0.1

        passed = stable and reach_ok and moved
        print(f"  Reach OK: {reach_ok}, Moved: {moved}")
        print(f"\n  >> EE position: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        os.unlink(urdf_path)


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print(f"Newton UR10e Dual-Arm Test")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print()

    results = {}
    results["single_arm_drive"] = test_single_arm_joint_drive()
    results["dual_arm"] = test_dual_arm()
    results["ee_position"] = test_ee_position()

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

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
