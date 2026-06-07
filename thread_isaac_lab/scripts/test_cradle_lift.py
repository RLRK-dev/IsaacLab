"""Ultra-minimal test: kinematic BOX platform lifts dynamic SPHERE upward.

Answers the fundamental question: does VBD generate upward normal force
from a kinematic body (inv_mass=0) to a dynamic body?

Setup:
  - No table. No walls. Just a platform (BOX) and a sphere.
  - Sphere rests on platform.
  - Platform moves up → does sphere follow?

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_cradle_lift.py
"""

import os
import sys

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD

DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
GRAVITY = -9.81
DT = 1.0 / 480.0
SIM_SUBSTEPS = 10
SIM_DT = DT / SIM_SUBSTEPS
VBD_ITERATIONS = 20

SPHERE_RADIUS = 0.010   # 10mm sphere
PLATFORM_HALF = 0.050   # 50mm half-extent


def build_scene():
    builder = newton.ModelBuilder(gravity=GRAVITY)

    cfg = newton.ModelBuilder.ShapeConfig()
    cfg.ke = 2500.0
    cfg.kd = 100.0
    cfg.mu = 1.0
    cfg.is_hydroelastic = False
    cfg.gap = 0.001

    # Platform: kinematic BOX
    platform_z = 0.50  # arbitrary height
    platform_body = builder.add_link(
        xform=wp.transform((0.0, 0.0, platform_z), wp.quat_identity()),
        mass=100.0, is_kinematic=True, label="platform",
    )
    builder.add_shape_box(
        body=platform_body,
        hx=PLATFORM_HALF, hy=PLATFORM_HALF, hz=0.005,
        cfg=cfg,
    )

    # Sphere: dynamic, resting on platform
    # Sphere center at platform_z + half_thickness + sphere_radius + tiny_gap
    sphere_z = platform_z + 0.005 + SPHERE_RADIUS + 0.002
    sphere_body = builder.add_link(
        xform=wp.transform((0.0, 0.0, sphere_z), wp.quat_identity()),
        mass=0.100,  # 100g (heavier than cable for stability)
        label="sphere",
    )
    builder.add_shape_sphere(
        body=sphere_body,
        radius=SPHERE_RADIUS,
        cfg=cfg,
    )

    builder.color()
    model = builder.finalize(device=DEVICE, requires_grad=False)

    # Ensure platform is kinematic
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()
    if inv_mass[platform_body] > 0:
        inv_mass[platform_body] = 0.0
        inv_inertia[platform_body] = np.zeros_like(inv_inertia[platform_body])
        model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=DEVICE)
        model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype,
                                           device=DEVICE)

    print(f"  Platform Z={platform_z}, Sphere Z={sphere_z}")
    for bi in range(model.body_count):
        im = model.body_inv_mass.numpy()[bi]
        print(f"  body {bi}: inv_mass={im:.6f} ({'kinematic' if im == 0 else 'dynamic'})")

    return model, platform_body, sphere_body, platform_z


def run_test():
    wp.init()
    wp.set_device(DEVICE)

    print("=" * 60)
    print("TEST: Kinematic platform lifts dynamic sphere")
    print("=" * 60)

    model, plat_bi, sphere_bi, plat_z0 = build_scene()

    state = model.state()
    state_out = model.state()
    contacts = model.contacts()
    control = model.control()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)

    solver = SolverVBD(model, iterations=VBD_ITERATIONS)

    def step_physics():
        nonlocal state, state_out
        for _ in range(SIM_SUBSTEPS):
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_out, control, contacts, SIM_DT)
            state, state_out = state_out, state

    def get_z(bi):
        return float(state.body_q.numpy()[bi][2])

    def set_platform_z(z):
        bq = state.body_q.numpy()
        bq[plat_bi][2] = z
        state.body_q = wp.array(bq, dtype=state.body_q.dtype, device=DEVICE)

    # ── Phase 0: Settle (sphere falls onto platform) ──
    print("\n--- Phase 0: Settle (300 frames) ---")
    for i in range(300):
        set_platform_z(plat_z0)
        step_physics()
        if (i + 1) % 100 == 0:
            sz = get_z(sphere_bi)
            print(f"  Frame {i + 1}: sphere_z={sz:.6f}")

    sphere_z_settled = get_z(sphere_bi)
    print(f"  Sphere settled: {sphere_z_settled:.6f}")

    # ── Phase 1: Lift platform +100mm (500 frames) ──
    print("\n--- Phase 1: Lift platform +100mm ---")
    lift = 0.100
    n_lift = 500
    sphere_z_pre = sphere_z_settled

    for i in range(n_lift):
        t = (i + 1) / n_lift
        pz = plat_z0 + lift * t
        set_platform_z(pz)
        step_physics()

        if (i + 1) % 100 == 0:
            sz = get_z(sphere_bi)
            pz_actual = get_z(plat_bi)
            delta = sz - sphere_z_pre
            print(f"  Step {i + 1}: platform_z={pz_actual:.4f}, "
                  f"sphere_z={sz:.6f}, lift={delta * 1000:.1f}mm")

    sphere_z_final = get_z(sphere_bi)
    sphere_lift = sphere_z_final - sphere_z_pre

    # ── Phase 2: Hold (sphere stays on platform?) ──
    print("\n--- Phase 2: Hold (100 frames) ---")
    for i in range(100):
        set_platform_z(plat_z0 + lift)
        step_physics()
    sphere_z_hold = get_z(sphere_bi)

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  Sphere Z pre-lift: {sphere_z_pre:.6f}")
    print(f"  Sphere Z final:    {sphere_z_final:.6f}")
    print(f"  Sphere Z hold:     {sphere_z_hold:.6f}")
    print(f"  Sphere lift:       {sphere_lift * 1000:.1f}mm")
    print(f"  Platform lift:     {lift * 1000:.0f}mm")
    if lift > 0:
        print(f"  Tracking:          {sphere_lift / lift * 100:.1f}%")

    if sphere_lift > 50.0:
        print(f"\n  >> PASS: Sphere lifted {sphere_lift * 1000:.0f}mm "
              f"({sphere_lift / lift * 100:.0f}% tracking)")
        return True
    elif sphere_lift > 10.0:
        print(f"\n  >> PARTIAL: Sphere lifted {sphere_lift * 1000:.0f}mm")
        return False
    else:
        print(f"\n  >> FAIL: Sphere lift {sphere_lift * 1000:.1f}mm")
        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
