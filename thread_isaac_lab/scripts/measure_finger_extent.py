#!/usr/bin/env python3
"""Measure finger world-Y extent at IC insert position.

Builds FK model, solves IK for insert precondition, reads body transforms.
CPU only — no GPU required, safe to run during training.
"""
import os, sys, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))
sys.path.insert(0, os.path.dirname(__file__))

import warp as wp
wp.init()

import newton
from test_newton_clip_routing import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    build_fk_model,
)
from task_config import (
    CLIP1_X, CLIP1_Y, GRIP_HALF_SPAN, LIFT_Z,
    EE_TO_FINGERTIP, CLIP_BASE_HEIGHT, TABLE_HEIGHT,
    FINGER_CLOSE_POS,
)

DEVICE = "cpu"

# Build FK model
print("Building FK model (CPU)...")
fk_model = build_fk_model(device=DEVICE)
fk_state = fk_model.state()

# Set home config
fk_jq = fk_state.joint_q.numpy()
fk_tp = fk_model.joint_target_pos.numpy()
fk_jq[:] = fk_tp[:]
# Close fingers
fk_jq[7] = FINGER_CLOSE_POS
fk_jq[8] = FINGER_CLOSE_POS
fk_jq[FRANKA_NUM_JOINTS + 7] = FINGER_CLOSE_POS
fk_jq[FRANKA_NUM_JOINTS + 8] = FINGER_CLOSE_POS

# IK solve for insert position
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)
target_left = (CLIP1_X, CLIP1_Y - GRIP_HALF_SPAN, LIFT_Z)
target_right = (CLIP1_X, CLIP1_Y + GRIP_HALF_SPAN, LIFT_Z)

print(f"IK targets:")
print(f"  Left EE:  {target_left}")
print(f"  Right EE: {target_right}")
print(f"  GRIP_HALF_SPAN: {GRIP_HALF_SPAN*1000:.0f}mm")
print(f"  Clip center Y: {CLIP1_Y}")

from newton.ik import IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit, IKSolver

left_ee = EE_BODY_OFFSET  # 6
right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET  # 15

objectives = [
    IKObjectivePosition(
        link_index=left_ee, link_offset=wp.vec3(0, 0, 0),
        target_positions=wp.array([target_left], dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    ),
    IKObjectivePosition(
        link_index=right_ee, link_offset=wp.vec3(0, 0, 0),
        target_positions=wp.array([target_right], dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    ),
    IKObjectiveRotation(
        link_index=left_ee, link_offset_rotation=wp.quat_identity(),
        target_rotations=wp.array([wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)], dtype=wp.vec4, device=DEVICE),
        weight=0.5,
    ),
    IKObjectiveRotation(
        link_index=right_ee, link_offset_rotation=wp.quat_identity(),
        target_rotations=wp.array([wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)], dtype=wp.vec4, device=DEVICE),
        weight=0.5,
    ),
    IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper,
        weight=10.0,
    ),
]

ik_solver = IKSolver(fk_model, n_problems=1, objectives=objectives)
jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=DEVICE)
jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=DEVICE)
ik_solver.step(jq_in, jq_out, iterations=100, step_size=1.0)

# Apply IK result and run FK
fk_state.joint_q.assign(jq_out.numpy()[0])
newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

# Read body transforms
body_q = fk_state.body_q.numpy()  # (n_bodies, 7) — pos(3) + quat(4)

print("\n=== Body Positions (Insert Precondition) ===")
labels = {
    0: "L_link0", 1: "L_link1", 2: "L_link2", 3: "L_link3",
    4: "L_link4", 5: "L_link5", 6: "L_hand(EE)", 7: "L_finger_L", 8: "L_finger_R",
    9: "R_link0", 10: "R_link1", 11: "R_link2", 12: "R_link3",
    13: "R_link4", 14: "R_link5", 15: "R_hand(EE)", 16: "R_finger_L", 17: "R_finger_R",
}
for i in [6, 7, 8, 15, 16, 17]:
    pos = body_q[i, :3]
    quat = body_q[i, 3:7]  # (x, y, z, w) or (w, x, y, z) depending on convention
    print(f"  {labels[i]:>12}: pos=({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})  quat=({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f})")

# Key measurements
clip_half_depth = 0.030 / 2  # 15mm

print("\n=== Finger Y-Position Analysis ===")
for arm_name, ee_idx, f1_idx, f2_idx, ee_target_y in [
    ("LEFT", 6, 7, 8, CLIP1_Y - GRIP_HALF_SPAN),
    ("RIGHT", 15, 16, 17, CLIP1_Y + GRIP_HALF_SPAN),
]:
    ee_y = body_q[ee_idx, 1]
    f1_y = body_q[f1_idx, 1]
    f2_y = body_q[f2_idx, 1]

    # Finger Y positions relative to clip center
    f1_rel = (f1_y - CLIP1_Y) * 1000  # mm from clip center
    f2_rel = (f2_y - CLIP1_Y) * 1000
    ee_rel = (ee_y - CLIP1_Y) * 1000

    # Closest finger Y to clip center
    finger_ys = [f1_y, f2_y]
    closest_to_clip = min(abs(fy - CLIP1_Y) for fy in finger_ys)

    print(f"\n  {arm_name} arm (EE target Y={ee_target_y:.3f}):")
    print(f"    EE actual Y:     {ee_y:.4f} ({ee_rel:+.1f}mm from clip)")
    print(f"    Finger_L Y:      {f1_y:.4f} ({f1_rel:+.1f}mm from clip)")
    print(f"    Finger_R Y:      {f2_y:.4f} ({f2_rel:+.1f}mm from clip)")
    print(f"    Finger_L Z:      {body_q[f1_idx, 2]:.4f}")
    print(f"    Finger_R Z:      {body_q[f2_idx, 2]:.4f}")
    print(f"    Closest finger to clip center: {closest_to_clip*1000:.1f}mm")
    print(f"    Clearance to clip edge (15mm): {(closest_to_clip - clip_half_depth)*1000:.1f}mm")

# Fingertip Z analysis
print("\n=== Fingertip Z Analysis ===")
for arm_name, ee_idx, f1_idx, f2_idx in [("LEFT", 6, 7, 8), ("RIGHT", 15, 16, 17)]:
    ee_z = body_q[ee_idx, 2]
    f1_z = body_q[f1_idx, 2]
    f2_z = body_q[f2_idx, 2]
    print(f"  {arm_name}: EE_Z={ee_z:.4f}, Finger_L_Z={f1_z:.4f}, Finger_R_Z={f2_z:.4f}")
    print(f"    EE-to-FingerJoint: {(ee_z - f1_z)*1000:.1f}mm (config EE_TO_FINGERTIP={EE_TO_FINGERTIP*1000:.0f}mm)")

# Finger body quaternions -> world-frame extents
print("\n=== Finger Orientation (world frame) ===")
# Load finger mesh bounds
# Y: [-0.0001, 0.0263], Z: [0.0001, 0.0539]
finger_local_bounds = {
    'y_min': -0.0001, 'y_max': 0.0263,
    'z_min': 0.0001, 'z_max': 0.0539,
    'x_min': -0.01, 'x_max': 0.01,  # estimate ~20mm width, will refine
}

def quat_to_rotation_matrix(q):
    """Convert quaternion (x,y,z,w) to rotation matrix."""
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
        [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
        [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)],
    ])

# Check if Newton uses xyzw or wxyz for body_q quaternions
# Try both and see which makes physical sense
for arm_name, f_idx in [("LEFT_finger_L", 7), ("RIGHT_finger_L", 16)]:
    q = body_q[f_idx, 3:7]
    pos = body_q[f_idx, :3]

    # Try xyzw
    R_xyzw = quat_to_rotation_matrix(q)
    # Try wxyz (swap)
    R_wxyz = quat_to_rotation_matrix([q[1], q[2], q[3], q[0]])

    print(f"\n  {arm_name} at pos=({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")
    print(f"    quat raw: ({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})")

    # For each interpretation, compute finger tip world position
    # Finger mesh tip is at local (0, ~13mm, ~54mm) from joint
    local_tip = np.array([0, 0.013, 0.054])

    world_tip_xyzw = pos + R_xyzw @ local_tip
    world_tip_wxyz = pos + R_wxyz @ local_tip

    print(f"    Tip world (if xyzw): ({world_tip_xyzw[0]:.4f}, {world_tip_xyzw[1]:.4f}, {world_tip_xyzw[2]:.4f})")
    print(f"    Tip world (if wxyz): ({world_tip_wxyz[0]:.4f}, {world_tip_wxyz[1]:.4f}, {world_tip_wxyz[2]:.4f})")

    # The fingertip should be below the EE (~220mm below) and near table height
    # Table at 0.80, LIFT_Z = 1.12, fingertip ~ 0.90
    print(f"    Expected tip Z ~ {LIFT_Z - EE_TO_FINGERTIP:.3f} (LIFT_Z - EE_TO_FINGERTIP)")

# Sweep analysis
print("\n=== GRIP_HALF_SPAN Sweep (using measured finger Y) ===")
# Use actual finger joint Y positions to estimate finger extent
l_f1_y = body_q[7, 1]
l_f2_y = body_q[8, 1]
r_f1_y = body_q[16, 1]
r_f2_y = body_q[17, 1]

# The finger closest to clip (inner finger)
# Left arm: the finger closer to clip center (larger Y)
l_inner_y = max(l_f1_y, l_f2_y)
r_inner_y = min(r_f1_y, r_f2_y)

# These are finger JOINT positions. The finger mesh extends further.
# We'll use the FK-measured joint positions as the reference, then add mesh extent.
print(f"  Left arm inner finger joint Y:  {l_inner_y:.4f} ({(l_inner_y - CLIP1_Y)*1000:+.1f}mm from clip)")
print(f"  Right arm inner finger joint Y: {r_inner_y:.4f} ({(r_inner_y - CLIP1_Y)*1000:+.1f}mm from clip)")
print(f"  Clip Y range: [{CLIP1_Y - clip_half_depth:.4f}, {CLIP1_Y + clip_half_depth:.4f}]")

print("\nDone.")
