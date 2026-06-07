"""Newton Phase 5b: Grip Tuning for Particle Chain Cable Lift

Problem: Particles slip through kinematic fingers because:
- Particle spacing (15mm) > finger capsule width (6mm radius)
- Penalty-based contact alone insufficient for grip

Solutions tested:
1. Denser cable (5mm segments → 3x particles)
2. Wider fingers (larger capsule radius/height)
3. Higher friction and contact stiffness
4. Combination of above

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_phase5_grip_tuning.py
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
CABLE_MASS = 0.02       # per particle
DT = 1.0 / 1920.0       # stable settling dt

# ARM PD
ARM_KE = 8000.0
ARM_KD = 400.0

# UR10e URDF (simplified)
UR10E_URDF = """<?xml version="1.0"?>
<robot name="ur10e_simple">
  <link name="base_link"><inertial><mass value="4.0"/><origin xyz="0 0 0" rpy="0 0 0"/><inertia ixx="0.006" ixy="0" ixz="0" iyy="0.006" iyz="0" izz="0.011"/></inertial><collision><origin xyz="0 0 0.04" rpy="0 0 0"/><geometry><cylinder radius="0.075" length="0.08"/></geometry></collision></link>
  <link name="shoulder_link"><inertial><mass value="7.778"/><origin xyz="0 0 0" rpy="0 0 0"/><inertia ixx="0.031" ixy="0" ixz="0" iyy="0.031" iyz="0" izz="0.022"/></inertial><collision><origin xyz="0 0 0" rpy="0 0 0"/><geometry><cylinder radius="0.06" length="0.15"/></geometry></collision></link>
  <link name="upper_arm_link"><inertial><mass value="12.93"/><origin xyz="-0.306 0 0.176" rpy="0 0 0"/><inertia ixx="0.422" ixy="0" ixz="0" iyy="0.422" iyz="0" izz="0.036"/></inertial><collision><origin xyz="-0.306 0 0" rpy="0 1.5708 0"/><geometry><cylinder radius="0.06" length="0.6127"/></geometry></collision></link>
  <link name="forearm_link"><inertial><mass value="3.87"/><origin xyz="-0.286 0 0.039" rpy="0 0 0"/><inertia ixx="0.111" ixy="0" ixz="0" iyy="0.111" iyz="0" izz="0.011"/></inertial><collision><origin xyz="-0.286 0 0" rpy="0 1.5708 0"/><geometry><cylinder radius="0.05" length="0.57155"/></geometry></collision></link>
  <link name="wrist_1_link"><inertial><mass value="1.96"/><origin xyz="0 -0.06 0" rpy="0 0 0"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/></inertial><collision><origin xyz="0 -0.06 0" rpy="1.5708 0 0"/><geometry><cylinder radius="0.04" length="0.12"/></geometry></collision></link>
  <link name="wrist_2_link"><inertial><mass value="1.96"/><origin xyz="0 0 -0.06" rpy="0 0 0"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.006"/></inertial><collision><origin xyz="0 0 -0.06" rpy="0 0 0"/><geometry><cylinder radius="0.04" length="0.12"/></geometry></collision></link>
  <link name="wrist_3_link"><inertial><mass value="0.202"/><origin xyz="0 0 -0.058" rpy="0 0 0"/><inertia ixx="0.0005" ixy="0" ixz="0" iyy="0.0005" iyz="0" izz="0.0006"/></inertial><collision><origin xyz="0 0 -0.03" rpy="0 0 0"/><geometry><cylinder radius="0.035" length="0.06"/></geometry></collision></link>
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


def add_cable(builder, start_pos, direction=(1, 0, 0), seg_len=0.015, n_segments=20,
              mass=0.02, radius=0.005, spring_ke=1e4, spring_kd=10.0):
    dx, dy, dz = [d * seg_len for d in direction]
    particles = []
    for i in range(n_segments + 1):
        pos = (start_pos[0] + i * dx, start_pos[1] + i * dy, start_pos[2] + i * dz)
        p = builder.add_particle(pos=pos, vel=(0, 0, 0), mass=mass, radius=radius)
        particles.append(p)
    for i in range(n_segments):
        builder.add_spring(i=particles[i], j=particles[i + 1],
                           ke=spring_ke, kd=spring_kd, control=0.0)
    return particles


def sim_step_with_fk(model, state, state_out, solver, control, contacts, dt):
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    model.collide(state, contacts)
    solver.step(state, state_out, control, contacts, dt)
    return state_out, state


def run_grip_lift_test(label, seg_len, n_segments, cable_radius, finger_radius,
                        finger_half_h, finger_ke, finger_kd, p_ke, p_kd, p_mu,
                        cable_mass=0.02, dt=1/1920):
    """Run a single grip+lift test with given parameters."""
    print(f"\n  --- {label} ---")
    print(f"    cable: {n_segments} segs × {seg_len*1000:.0f}mm, r={cable_radius*1000:.1f}mm, m={cable_mass}")
    print(f"    finger: r={finger_radius*1000:.1f}mm, h={finger_half_h*1000:.1f}mm, ke={finger_ke:.0e}")
    print(f"    contact: p_ke={p_ke:.0e}, p_kd={p_kd}, mu={p_mu}")

    urdf_path = write_ur10e_urdf()
    try:
        builder = newton.ModelBuilder(gravity=GRAVITY)
        builder.add_ground_plane()

        add_ur10e_arm(builder, pos=(0, 0, 0), urdf_path=urdf_path)
        n_arm_bodies = 7

        cable = add_cable(builder, start_pos=(-seg_len * n_segments / 2, 0, 0.10),
                          direction=(1, 0, 0), seg_len=seg_len, n_segments=n_segments,
                          mass=cable_mass, radius=cable_radius)
        n_particles = n_segments + 1

        # Kinematic finger bodies
        for sign in [-1, 1]:
            f = builder.add_link(
                xform=wp.transform((sign * 0.05, 0, 0.15), wp.quat_identity()),
                mass=1.0, is_kinematic=True,
            )
            builder.add_shape_capsule(
                body=f, radius=finger_radius, half_height=finger_half_h,
                cfg=newton.ModelBuilder.ShapeConfig(
                    mu=p_mu, ke=finger_ke, kd=finger_kd, density=0.0),
            )

        LF_IDX = n_arm_bodies
        RF_IDX = n_arm_bodies + 1

        model = builder.finalize(device=DEVICE)
        model.particle_ke = p_ke
        model.particle_kd = p_kd
        model.particle_mu = p_mu

        state = model.state()
        newton.eval_fk(model, model.joint_q, model.joint_qd, state)
        contacts = model.contacts()
        control = model.control()
        solver = SolverSemiImplicit(model)
        state_out = model.state()

        # Settle (3s)
        settle_steps = int(3.0 / dt)
        for i in range(settle_steps):
            state, state_out = sim_step_with_fk(
                model, state, state_out, solver, control, contacts, dt)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"    NaN at settle step {i}")
                return {"label": label, "settled": False, "lifted": False, "nan": True}

        pq = state.particle_q.numpy()
        cable_z = np.mean(pq[:n_particles, 2])
        if abs(cable_z) > 0.1:
            print(f"    Cable NOT settled (z={cable_z:.4f})")
            return {"label": label, "settled": False, "lifted": False, "nan": False, "cable_z": cable_z}
        print(f"    Cable settled: z={cable_z:.4f}")

        # Close fingers (1s)
        grip_width = cable_radius * 2.5  # slightly wider than cable diameter
        close_steps = int(1.0 / dt)
        for i in range(close_steps):
            t = (i + 1) / close_steps
            fx = 0.05 + (grip_width - 0.05) * t
            fz = max(cable_z, cable_radius)

            bq = state.body_q.numpy()
            bq[LF_IDX][:3] = [-fx, 0, fz]
            bq[LF_IDX][3:] = [0, 0, 0, 1]
            bq[RF_IDX][:3] = [fx, 0, fz]
            bq[RF_IDX][3:] = [0, 0, 0, 1]
            state.body_q.assign(bq)

            state, state_out = sim_step_with_fk(
                model, state, state_out, solver, control, contacts, dt)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"    NaN at close step {i}")
                return {"label": label, "settled": True, "lifted": False, "nan": True}

        pq = state.particle_q.numpy()
        post_close_z = np.mean(pq[:n_particles, 2])
        center_idx = n_particles // 2
        center_z = pq[center_idx][2]
        print(f"    After close: mean_z={post_close_z:.4f}, center_z={center_z:.4f}")

        # Lift (2s)
        lift_steps = int(2.0 / dt)
        lift_target = 0.10
        for i in range(lift_steps):
            t = (i + 1) / lift_steps
            lift_z = max(cable_z, cable_radius) + lift_target * t

            bq = state.body_q.numpy()
            bq[LF_IDX][:3] = [-grip_width, 0, lift_z]
            bq[LF_IDX][3:] = [0, 0, 0, 1]
            bq[RF_IDX][:3] = [grip_width, 0, lift_z]
            bq[RF_IDX][3:] = [0, 0, 0, 1]
            state.body_q.assign(bq)

            state, state_out = sim_step_with_fk(
                model, state, state_out, solver, control, contacts, dt)
            if np.any(np.isnan(state.particle_q.numpy())):
                print(f"    NaN at lift step {i}")
                return {"label": label, "settled": True, "lifted": False, "nan": True}

        pq = state.particle_q.numpy()
        final_center_z = pq[center_idx][2]
        final_mean_z = np.mean(pq[:n_particles, 2])
        lifted = final_center_z > cable_z + 0.02

        print(f"    Lift result: init_z={cable_z:.4f} → final_center_z={final_center_z:.4f} "
              f"mean_z={final_mean_z:.4f}")
        print(f"    {'✅ LIFTED!' if lifted else '❌ NOT LIFTED'} "
              f"(delta={final_center_z - cable_z:.4f}m)")

        return {"label": label, "settled": True, "lifted": lifted, "nan": False,
                "cable_z": cable_z, "final_z": final_center_z, "delta": final_center_z - cable_z}
    finally:
        os.unlink(urdf_path)


def main():
    print("Newton Phase 5b: Grip Tuning for Cable Lift")
    print(f"Device: {DEVICE}")
    print(f"Newton: {newton.__version__}, Warp: {wp.__version__}")
    print()

    print("=" * 60)
    print("Grip Parameter Sweep")
    print("=" * 60)

    results = []

    # Config A: Baseline (Phase 4 params + working mass/dt)
    results.append(run_grip_lift_test(
        "A: Baseline", seg_len=0.015, n_segments=20, cable_radius=0.005,
        finger_radius=0.006, finger_half_h=0.02, finger_ke=2000, finger_kd=200,
        p_ke=5e4, p_kd=100, p_mu=1.0))

    # Config B: Dense cable (5mm segments, 60 segments)
    results.append(run_grip_lift_test(
        "B: Dense cable 5mm", seg_len=0.005, n_segments=60, cable_radius=0.004,
        finger_radius=0.006, finger_half_h=0.02, finger_ke=2000, finger_kd=200,
        p_ke=5e4, p_kd=100, p_mu=1.0))

    # Config C: Wide fingers (12mm radius, 30mm half-height)
    results.append(run_grip_lift_test(
        "C: Wide fingers", seg_len=0.015, n_segments=20, cable_radius=0.005,
        finger_radius=0.012, finger_half_h=0.03, finger_ke=5000, finger_kd=500,
        p_ke=5e4, p_kd=100, p_mu=1.0))

    # Config D: Dense cable + wide fingers
    results.append(run_grip_lift_test(
        "D: Dense+Wide", seg_len=0.005, n_segments=60, cable_radius=0.004,
        finger_radius=0.012, finger_half_h=0.03, finger_ke=5000, finger_kd=500,
        p_ke=5e4, p_kd=100, p_mu=1.0))

    # Config E: Dense cable + very high friction
    results.append(run_grip_lift_test(
        "E: Dense+HighFriction", seg_len=0.005, n_segments=60, cable_radius=0.004,
        finger_radius=0.008, finger_half_h=0.025, finger_ke=10000, finger_kd=1000,
        p_ke=1e5, p_kd=200, p_mu=2.0))

    # Config F: Dense cable + box fingers (wider grip surface)
    # Using larger radius capsule as proxy for box
    results.append(run_grip_lift_test(
        "F: Dense+LargeGrip", seg_len=0.005, n_segments=60, cable_radius=0.004,
        finger_radius=0.015, finger_half_h=0.04, finger_ke=10000, finger_kd=1000,
        p_ke=1e5, p_kd=200, p_mu=2.0))

    # Config G: Very dense cable (3mm segments)
    results.append(run_grip_lift_test(
        "G: VeryDense 3mm", seg_len=0.003, n_segments=100, cable_radius=0.003,
        finger_radius=0.008, finger_half_h=0.025, finger_ke=5000, finger_kd=500,
        p_ke=5e4, p_kd=100, p_mu=1.0))

    # Config H: Heavier particles for stronger contact
    results.append(run_grip_lift_test(
        "H: Dense+Heavy", seg_len=0.005, n_segments=60, cable_radius=0.004,
        finger_radius=0.010, finger_half_h=0.03, finger_ke=5000, finger_kd=500,
        p_ke=5e4, p_kd=100, p_mu=1.0, cable_mass=0.05))

    # Summary
    print()
    print("=" * 60)
    print("GRIP TUNING SUMMARY")
    print("=" * 60)
    for r in results:
        label = r["label"]
        if r.get("nan"):
            print(f"  {label}: NaN!")
        elif not r["settled"]:
            print(f"  {label}: NOT SETTLED (z={r.get('cable_z', '?')})")
        elif r["lifted"]:
            print(f"  {label}: ✅ LIFTED (delta={r['delta']:.4f}m)")
        else:
            print(f"  {label}: settled but NOT lifted")

    lifted_configs = [r for r in results if r.get("lifted")]
    if lifted_configs:
        print(f"\n  WORKING CONFIGS: {len(lifted_configs)}")
        for r in lifted_configs:
            print(f"    {r['label']}: delta={r['delta']:.4f}m")
    else:
        print("\n  No config achieved lift. Need different approach (FEM cable or spring attachment).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
