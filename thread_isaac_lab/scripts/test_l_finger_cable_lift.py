"""Test: Franka-style BOX finger (body + upper/lower claw) lifts cable rod.

Verifies that the existing scoop claw design from create_grooved_finger.py
can lift a cable rod via normal force when represented as BOX primitives
(instead of CONVEX_MESH which destroys the concave claw geometry).

Finger cross-section (YZ, looking along cable X-axis):
  Left finger:            Right finger:
  ┌─ upper claw           upper claw ─┐
  │                                    │
  │  Wall (main body)      Wall        │
  │                                    │
  └─ lower claw           lower claw ─┘

  Claws protrude inward (toward cable) from inner face.
  Lower claw = ledge that slides under cable → normal force lift.
  Upper claw = containment preventing cable escape upward.

  Claw dimensions from create_grooved_finger.py:
    CLAW_PROTRUSION = 3mm (inward from inner face)
    CLAW_THICKNESS  = 0.5mm (Z extension beyond finger body)

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_l_finger_cable_lift.py
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

# Table
TABLE_HEIGHT = 0.80
TABLE_HALF = (0.30, 0.30, 0.005)

# Cable (short rod for focused test)
CABLE_SEGMENTS = 5
CABLE_SEG_LEN = 0.015       # 15mm per segment → 75mm total
CABLE_RADIUS = 0.004         # 4mm

# Finger geometry: wall (main body) + upper/lower claw (from create_grooved_finger.py)
# Wall: main finger body (simplified from 54mm to 20mm height for test)
WALL_HX = 0.00525            # 10.5mm width (half = 5.25mm, Franka finger)
WALL_HY = 0.002              # 4mm thick wall (simplified from 13mm depth)
WALL_HZ = 0.010              # 20mm tall (contains cable + headroom)

# Claws: scoop claws from create_grooved_finger.py design
CLAW_PROTRUSION = 0.003      # 3mm inward from inner face
CLAW_THICKNESS = 0.0005      # 0.5mm thick (Z extension beyond wall)
CLAW_HX = WALL_HX            # same width as wall
CLAW_HY = CLAW_PROTRUSION / 2  # 1.5mm half-extent
CLAW_HZ = CLAW_THICKNESS / 2   # 0.25mm half-extent

# Finger motion
FINGER_Y_OPEN = 0.030        # 30mm from center (60mm span, well clear of cable)
FINGER_Y_CLOSE = WALL_HY + CABLE_RADIUS  # wall inner face at cable surface (8mm gap)
CLOSE_STEPS = 300
LIFT_HEIGHT = 0.050           # 50mm lift target
LIFT_STEPS = 500


def build_scene():
    """Build minimal scene: table + cable rod + 2 L-shaped fingers."""
    builder = newton.ModelBuilder(gravity=GRAVITY)

    # ── Table (static, body=-1) ──
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.is_hydroelastic = False
    table_cfg.gap = 0.002      # 2mm (matches clip routing test)

    table_xf = wp.transform(
        wp.vec3(0.0, 0.0, TABLE_HEIGHT - TABLE_HALF[2]),
        wp.quat_identity(),
    )
    builder.add_shape_box(
        body=-1, xform=table_xf,
        hx=TABLE_HALF[0], hy=TABLE_HALF[1], hz=TABLE_HALF[2],
        cfg=table_cfg,
    )

    # ── Cable rod along X axis, centered at origin ──
    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = 2500.0
    cable_cfg.kd = 100.0
    cable_cfg.mu = 1.0
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002      # 2mm (matches clip routing test)
    cable_cfg.density = 1100.0  # rubber cable

    cable_x_start = -(CABLE_SEGMENTS * CABLE_SEG_LEN) / 2.0
    cable_z_init = TABLE_HEIGHT + CABLE_RADIUS + 0.005  # will settle
    positions = []
    for i in range(CABLE_SEGMENTS + 1):
        x = cable_x_start + i * CABLE_SEG_LEN
        positions.append((x, 0.0, cable_z_init))

    cable_body_ids, cable_joint_ids = builder.add_rod(
        positions=positions,
        radius=CABLE_RADIUS,
        stretch_stiffness=1.0e6,
        stretch_damping=0.0,
        bend_stiffness=0.1,
        bend_damping=0.01,
        cfg=cable_cfg,
    )
    seg_mass = cable_cfg.density * np.pi * CABLE_RADIUS**2 * CABLE_SEG_LEN
    print(f"  [CABLE] {len(cable_body_ids)} bodies, seg_mass={seg_mass * 1000:.2f}g")

    # ── Franka-style fingers: wall (body) + upper/lower claw ──
    finger_cfg = newton.ModelBuilder.ShapeConfig()
    finger_cfg.ke = 2500.0
    finger_cfg.kd = 100.0
    finger_cfg.mu = 1.0
    finger_cfg.is_hydroelastic = False
    finger_cfg.gap = 0.001     # 1mm (smaller than cable, avoids launch)
    finger_cfg.density = 0.0

    # Finger body Z: lower claw bottom at TABLE_HEIGHT
    # finger_z = center of wall, so lower claw bottom = finger_z - WALL_HZ - CLAW_THICKNESS
    finger_z = TABLE_HEIGHT + WALL_HZ + CLAW_THICKNESS  # wall center

    def add_finger(label, y_sign):
        """Add finger with wall + upper/lower claw.

        y_sign: -1 for left finger, +1 for right finger.
        Claws extend INWARD (toward cable at Y=0) from wall inner face.
        """
        body = builder.add_link(
            xform=wp.transform(
                wp.vec3(0.0, y_sign * FINGER_Y_OPEN, finger_z),
                wp.quat_identity(),
            ),
            mass=100.0, is_kinematic=True, label=label,
        )

        # Wall (main body): centered on body
        builder.add_shape_box(
            body=body,
            xform=wp.transform(wp.vec3(0.0, 0.0, 0.0), wp.quat_identity()),
            hx=WALL_HX, hy=WALL_HY, hz=WALL_HZ,
            cfg=finger_cfg,
        )

        # Claw Y offset: from body center, toward cable (inward)
        # Wall inner face = body_Y + (-y_sign * WALL_HY)
        # Claw center = inner_face + (-y_sign * CLAW_HY)
        claw_y_offset = -y_sign * (WALL_HY + CLAW_HY)

        # Lower claw (at wall bottom → near table, slides under cable)
        builder.add_shape_box(
            body=body,
            xform=wp.transform(
                wp.vec3(0.0, claw_y_offset, -(WALL_HZ + CLAW_HZ)),
                wp.quat_identity(),
            ),
            hx=CLAW_HX, hy=CLAW_HY, hz=CLAW_HZ,
            cfg=finger_cfg,
        )

        # Upper claw (at wall top → containment, prevents cable escape)
        builder.add_shape_box(
            body=body,
            xform=wp.transform(
                wp.vec3(0.0, claw_y_offset, +(WALL_HZ + CLAW_HZ)),
                wp.quat_identity(),
            ),
            hx=CLAW_HX, hy=CLAW_HY, hz=CLAW_HZ,
            cfg=finger_cfg,
        )

        return body

    left_finger = add_finger("left_finger", y_sign=-1)
    right_finger = add_finger("right_finger", y_sign=+1)

    builder.color()
    model = builder.finalize(device=DEVICE, requires_grad=False)

    # Ensure kinematic bodies have inv_mass=0
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()
    for bi in [left_finger, right_finger]:
        if inv_mass[bi] > 0:
            inv_mass[bi] = 0.0
            inv_inertia[bi] = np.zeros((3, 3))
    model.body_inv_mass = wp.array(
        inv_mass, dtype=model.body_inv_mass.dtype, device=DEVICE)
    model.body_inv_inertia = wp.array(
        inv_inertia, dtype=model.body_inv_inertia.dtype, device=DEVICE)

    print(f"  [SCENE] {model.body_count} bodies:")
    for bi in range(model.body_count):
        im = model.body_inv_mass.numpy()[bi]
        kind = "kinematic" if im == 0 else "dynamic"
        print(f"    body {bi}: inv_mass={im:.6f} ({kind})")

    return model, left_finger, right_finger, cable_body_ids


def run_test():
    wp.init()
    wp.set_device(DEVICE)

    print("=" * 60)
    print("TEST: L-shaped finger cable lift (wall + ledge BOX)")
    print("=" * 60)
    inner_face_gap = (FINGER_Y_CLOSE - WALL_HY) * 2
    print(f"  Cable: {CABLE_SEGMENTS} segs × {CABLE_SEG_LEN * 1000:.0f}mm, "
          f"r={CABLE_RADIUS * 1000:.0f}mm")
    print(f"  Wall:  {WALL_HX * 2000:.0f}×{WALL_HY * 2000:.0f}×{WALL_HZ * 2000:.0f}mm "
          f"(X×Y×Z)")
    print(f"  Claw:  {CLAW_PROTRUSION * 1000:.0f}mm protrusion, "
          f"{CLAW_THICKNESS * 1000:.1f}mm thick (from create_grooved_finger.py)")
    print(f"  Close: body Y {FINGER_Y_OPEN * 1000:.0f}mm → {FINGER_Y_CLOSE * 1000:.0f}mm "
          f"(inner face gap={inner_face_gap * 1000:.0f}mm)")

    model, left_bi, right_bi, cable_bis = build_scene()

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

    def get_cable_mid_z():
        mid = cable_bis[len(cable_bis) // 2]
        return float(state.body_q.numpy()[mid][2])

    def get_cable_avg_z():
        bq = state.body_q.numpy()
        return np.mean([bq[bi][2] for bi in cable_bis])

    def get_body_z(bi):
        return float(state.body_q.numpy()[bi][2])

    def set_finger_positions(y_offset, z_offset=0.0):
        """Move both fingers to symmetric Y position with optional Z lift."""
        bq = state.body_q.numpy()
        fz = TABLE_HEIGHT + WALL_HZ + CLAW_THICKNESS + z_offset
        bq[left_bi][1] = -y_offset
        bq[left_bi][2] = fz
        bq[right_bi][1] = y_offset
        bq[right_bi][2] = fz
        state.body_q = wp.array(bq, dtype=state.body_q.dtype, device=DEVICE)

    # ── Phase 0: Settle cable on table ──
    print("\n--- Phase 0: Settle (500 frames) ---")
    for i in range(500):
        set_finger_positions(FINGER_Y_OPEN)
        step_physics()
        if (i + 1) % 100 == 0:
            cz = get_cable_mid_z()
            gap = (cz - CABLE_RADIUS - TABLE_HEIGHT) * 1000
            print(f"  Frame {i + 1}: cable_mid_z={cz:.6f} "
                  f"(surface gap above table: {gap:.2f}mm)")

    cable_z_settled = get_cable_mid_z()
    cable_bottom = cable_z_settled - CABLE_RADIUS
    # Lower claw top = finger_z - WALL_HZ - CLAW_THICKNESS + 2*CLAW_HZ = finger_z - WALL_HZ
    claw_top = TABLE_HEIGHT + CLAW_THICKNESS  # = finger_z - WALL_HZ
    contact_dist = 0.001 + 0.002  # finger_gap + cable_gap
    print(f"\n  Geometry check:")
    print(f"    Cable center:     {cable_z_settled * 1000:.2f}mm")
    print(f"    Cable bottom:     {cable_bottom * 1000:.2f}mm")
    print(f"    Lower claw top:   {claw_top * 1000:.2f}mm")
    print(f"    Gap (cable→claw): {(cable_bottom - claw_top) * 1000:.2f}mm")
    print(f"    Contact distance: {contact_dist * 1000:.1f}mm")
    in_range = cable_bottom - claw_top < contact_dist
    print(f"    Claw in contact range: {'YES' if in_range else 'NO'}")

    # ── Phase 1: Close fingers ──
    print("\n--- Phase 1: Close fingers ---")
    for i in range(CLOSE_STEPS):
        t = (i + 1) / CLOSE_STEPS
        y = FINGER_Y_OPEN + (FINGER_Y_CLOSE - FINGER_Y_OPEN) * t
        set_finger_positions(y)
        step_physics()

        if (i + 1) % 100 == 0:
            cz = get_cable_mid_z()
            # Left wall inner face Y (absolute) and claw inner edge
            wall_inner = -y + WALL_HY
            claw_inner = wall_inner + CLAW_PROTRUSION
            print(f"  Step {i + 1}: body_y={y * 1000:.1f}mm, "
                  f"cable_z={cz:.6f}, "
                  f"wall_inner_Y={wall_inner * 1000:.1f}mm, "
                  f"claw_tip_Y={claw_inner * 1000:.1f}mm")

    cable_z_after_close = get_cable_mid_z()
    print(f"  Cable after close: z={cable_z_after_close:.6f}")

    # Brief settle at closed position
    print("\n--- Settle at closed (200 frames) ---")
    for i in range(200):
        set_finger_positions(FINGER_Y_CLOSE)
        step_physics()
    cable_z_pre_lift = get_cable_mid_z()
    print(f"  Cable pre-lift: z={cable_z_pre_lift:.6f}")

    # ── Phase 2: Lift fingers ──
    print(f"\n--- Phase 2: Lift +{LIFT_HEIGHT * 1000:.0f}mm ---")

    for i in range(LIFT_STEPS):
        t = (i + 1) / LIFT_STEPS
        z_off = LIFT_HEIGHT * t
        set_finger_positions(FINGER_Y_CLOSE, z_off)
        step_physics()

        if (i + 1) % 100 == 0:
            cz = get_cable_mid_z()
            fz = get_body_z(left_bi)
            delta = cz - cable_z_pre_lift
            print(f"  Step {i + 1}: finger_z={fz:.4f}, "
                  f"cable_z={cz:.6f}, lift={delta * 1000:.1f}mm")

    cable_z_final = get_cable_mid_z()
    cable_lift = cable_z_final - cable_z_pre_lift

    # ── Phase 3: Hold ──
    print("\n--- Phase 3: Hold (200 frames) ---")
    for i in range(200):
        set_finger_positions(FINGER_Y_CLOSE, LIFT_HEIGHT)
        step_physics()
    cable_z_hold = get_cable_mid_z()
    cable_avg_hold = get_cable_avg_z()

    # ── Results ──
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  Cable Z settled:   {cable_z_settled:.6f}")
    print(f"  Cable Z pre-lift:  {cable_z_pre_lift:.6f}")
    print(f"  Cable Z final:     {cable_z_final:.6f}")
    print(f"  Cable Z hold:      {cable_z_hold:.6f}")
    print(f"  Cable avg hold:    {cable_avg_hold:.6f}")
    print(f"  Cable lift (mid):  {cable_lift * 1000:.1f}mm")
    print(f"  Target lift:       {LIFT_HEIGHT * 1000:.0f}mm")
    if LIFT_HEIGHT > 0:
        print(f"  Tracking:          {cable_lift / LIFT_HEIGHT * 100:.1f}%")

    # Per-segment Z
    bq = state.body_q.numpy()
    print(f"\n  Per-segment Z (hold):")
    for idx, bi in enumerate(cable_bis):
        z = bq[bi][2]
        lift_mm = (z - cable_z_settled) * 1000
        x = bq[bi][0]
        print(f"    seg {idx}: x={x * 1000:.1f}mm, z={z:.6f}, "
              f"lift={lift_mm:.1f}mm")

    if cable_lift > LIFT_HEIGHT * 0.5:
        print(f"\n  >> PASS: Cable lifted {cable_lift * 1000:.0f}mm "
              f"({cable_lift / LIFT_HEIGHT * 100:.0f}% tracking)")
        return True
    elif cable_lift > 5.0e-3:
        print(f"\n  >> PARTIAL: Cable lifted {cable_lift * 1000:.1f}mm")
        return False
    else:
        print(f"\n  >> FAIL: Cable lift {cable_lift * 1000:.1f}mm")
        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
