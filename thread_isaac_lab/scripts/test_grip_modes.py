#!/usr/bin/env python3
"""Grip mode experiment: 4 approaches for kinematic finger grip limitation.

Tests:
  1: high-friction   -- 20x contact ke/kd/mu (ke=50000, kd=5000, mu=10.0)
  2: dynamic-finger  -- finger bodies made dynamic + spring force to FK position
  3: spring-attach   -- spring constraints link cable bodies to grip center after close
  4: box-cable       -- additional BOX collision shapes on cable bodies (CAPSULE->BOX overlay)

Only runs P1 (grasp) + P2 (lift). Reports cable_z_delta for each mode.

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_grip_modes.py
    # Single mode:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_grip_modes.py --mode high-friction
"""

import argparse
import gc
import json
import math
import os
import sys
import time

import numpy as np
import trimesh
import warp as wp
import newton
from newton.solvers import SolverVBD
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit

# ---------------------------------------------------------------------------
# Config imports (SSOT)
# ---------------------------------------------------------------------------
_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    FRANKA_NUM_JOINTS, EE_BODY_OFFSET,
    TABLE_HEIGHT, ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE,
    EE_TO_FINGERTIP, APPROACH_Z, GRASP_Z, LIFT_Z,
    SIM_SUBSTEPS, NJMAX,
    CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    CABLE_BEND_STIFFNESS, CABLE_BEND_DAMPING,
    CABLE_STRETCH_STIFFNESS, CABLE_STRETCH_DAMPING,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
    GRASP_X, WIDE_LEFT_Y, WIDE_RIGHT_Y, CLIP1_Y,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_CLOSE_STEPS,
    STEPS_PER_CM, MAX_MOVE_STEPS, SETTLE_STEPS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0
SIM_DT = DT / SIM_SUBSTEPS
GRAVITY = -9.81
VBD_ITERATIONS = 20

FRANKA_URDF = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "source", "extensions", "isaaclab_tasks_thread", "data", "robots",
    "panda_independent_fingers.urdf",
))
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0

# ---------------------------------------------------------------------------
# Mode configs
# ---------------------------------------------------------------------------
MODE_CONFIGS = {
    "high-friction": {
        "contact_ke": 50000.0,
        "contact_kd": 5000.0,
        "contact_mu": 10.0,
        "dynamic_fingers": False,
        "spring_attach": False,
        "box_cable": False,
    },
    "dynamic-finger": {
        "contact_ke": CABLE_CONTACT_KE,
        "contact_kd": CABLE_CONTACT_KD,
        "contact_mu": CABLE_CONTACT_MU,
        "dynamic_fingers": True,
        "spring_attach": False,
        "box_cable": False,
    },
    "spring-attach": {
        "contact_ke": CABLE_CONTACT_KE,
        "contact_kd": CABLE_CONTACT_KD,
        "contact_mu": CABLE_CONTACT_MU,
        "dynamic_fingers": False,
        "spring_attach": True,
        "box_cable": False,
    },
    "box-cable": {
        "contact_ke": CABLE_CONTACT_KE,
        "contact_kd": CABLE_CONTACT_KD,
        "contact_mu": CABLE_CONTACT_MU,
        "dynamic_fingers": False,
        "spring_attach": False,
        "box_cable": True,
    },
}


# ---------------------------------------------------------------------------
# Finger mesh loader (cached)
# ---------------------------------------------------------------------------
def _load_finger_mesh():
    if not hasattr(_load_finger_mesh, "_cache"):
        stl_path = os.path.join(
            os.path.dirname(FRANKA_URDF),
            "franka_description", "meshes", "collision", "finger_v_groove_60deg.stl",
        )
        tm = trimesh.load(stl_path)
        verts = np.array(tm.vertices, dtype=np.float32)
        faces = np.array(tm.faces, dtype=np.int32).flatten()
        _load_finger_mesh._cache = newton.Mesh(verts, faces)
    return _load_finger_mesh._cache


# ---------------------------------------------------------------------------
# FK model builder (same for all modes)
# ---------------------------------------------------------------------------
def build_fk_model():
    builder = newton.ModelBuilder(gravity=GRAVITY)
    urdf_cfg = newton.ModelBuilder.ShapeConfig()
    urdf_cfg.gap = 0.0
    urdf_cfg.density = 0.0
    builder.default_shape_cfg = urdf_cfg
    builder.add_urdf(FRANKA_URDF, xform=wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()),
                     floating=False, enable_self_collisions=False, collapse_fixed_joints=True)
    builder.add_urdf(FRANKA_URDF, xform=wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
                     floating=False, enable_self_collisions=False, collapse_fixed_joints=True)
    model = builder.finalize(device=DEVICE, requires_grad=True)
    return model


# ---------------------------------------------------------------------------
# Scene builder (mode-aware)
# ---------------------------------------------------------------------------
def add_kinematic_arm(builder, fk_state, arm_body_offset, label_prefix, mcfg):
    """Add Franka arm as kinematic bodies. mcfg = mode config dict."""
    body_start = len(builder.body_mass)
    shape_start = builder.shape_count
    fk_body_q = fk_state.body_q.numpy()

    finger_mesh = _load_finger_mesh()
    finger_cfg = newton.ModelBuilder.ShapeConfig()
    finger_cfg.ke = mcfg["contact_ke"]
    finger_cfg.kd = mcfg["contact_kd"]
    finger_cfg.mu = mcfg["contact_mu"]
    finger_cfg.is_hydroelastic = False
    finger_cfg.gap = 0.005
    finger_cfg.density = 0.0

    arm_cfg = newton.ModelBuilder.ShapeConfig()
    arm_cfg.density = 0.0
    arm_cfg.gap = 0.0

    for local_body in range(FRANKA_NUM_JOINTS):
        fk_bi = arm_body_offset + local_body
        bq = fk_body_q[fk_bi]
        pos = wp.vec3(float(bq[0]), float(bq[1]), float(bq[2]))
        quat = wp.quat(float(bq[3]), float(bq[4]), float(bq[5]), float(bq[6]))
        xform = wp.transform(pos, quat)

        body_id = builder.add_link(
            xform=xform, mass=100.0, is_kinematic=True,
            label=f"{label_prefix}_body{local_body}",
        )
        # Franka-legacy finger indices, NOT UR5e-swapped (S2); port for UR5e (see S2_DEFERRED_OBLIGATIONS.md)
        if local_body in (7, 8):
            mesh_xf = wp.transform_identity()
            if local_body == 8:
                mesh_rot = wp.quat_from_axis_angle(wp.vec3(0.0, 0.0, 1.0), np.pi)
                mesh_xf = wp.transform(wp.vec3(0.0, 0.0, 0.0), mesh_rot)
            builder.add_shape_mesh(body=body_id, mesh=finger_mesh, xform=mesh_xf, cfg=finger_cfg)
        else:
            builder.add_shape_capsule(body=body_id, radius=0.04, half_height=0.05, cfg=arm_cfg)

    shape_end = builder.shape_count
    return body_start, shape_start, shape_end


def add_cable_rod(builder, start_pos, mcfg, direction=(0, 1, 0)):
    """Add cable as Cosserat Rod via add_rod(). Returns (body_ids, joint_ids)."""
    n_points = CABLE_SEGMENTS + 1
    dir_np = np.array(direction, dtype=np.float64)
    dir_np = dir_np / np.linalg.norm(dir_np)
    positions = [tuple(np.array(start_pos) + dir_np * (i * CABLE_SEG_LEN)) for i in range(n_points)]

    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = mcfg["contact_ke"]
    cable_cfg.kd = mcfg["contact_kd"]
    cable_cfg.mu = mcfg["contact_mu"]
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002
    cable_cfg.density = 1100.0

    body_ids, joint_ids = builder.add_rod(
        positions=positions, radius=CABLE_RADIUS,
        stretch_stiffness=CABLE_STRETCH_STIFFNESS, stretch_damping=CABLE_STRETCH_DAMPING,
        bend_stiffness=CABLE_BEND_STIFFNESS, bend_damping=CABLE_BEND_DAMPING,
        cfg=cable_cfg,
    )
    return body_ids, joint_ids


def build_scene(fk_model, fk_state, mcfg):
    """Build Newton scene with mode-specific modifications."""
    builder = newton.ModelBuilder(gravity=GRAVITY)
    floor_shape_idx = builder.add_ground_plane()

    # Table
    table_half = (0.35, 0.35, 0.005)
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_xform = wp.transform((0.3, -0.05, TABLE_HEIGHT - table_half[2]), wp.quat_identity())
    table_idx = builder.add_shape_box(body=-1, hx=table_half[0], hy=table_half[1],
                                       hz=table_half[2], xform=table_xform, cfg=table_cfg)

    # Arms
    left_bs, left_ss, left_se = add_kinematic_arm(builder, fk_state, 0, "left", mcfg)
    right_bs, right_ss, right_se = add_kinematic_arm(builder, fk_state, FRANKA_NUM_JOINTS, "right", mcfg)

    # Arm body shapes (0-6) → VISIBLE only
    for arm_label, ss, se, bs in [("left", left_ss, left_se, left_bs), ("right", right_ss, right_se, right_bs)]:
        for si in range(ss, se):
            local_body = builder.shape_body[si] - bs
            if local_body < 7:
                builder.shape_flags[si] = 1

    # Cable
    cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
    cable_y_start = CLIP1_Y - cable_half_len
    cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CABLE_RADIUS)

    cable_shape_start = builder.shape_count
    cable_bodies, cable_joints = add_cable_rod(builder, cable_start, mcfg)
    cable_shape_end = builder.shape_count

    # Mode 4: add BOX overlay shapes on cable bodies
    box_cable_shape_start = None
    if mcfg["box_cable"]:
        box_cable_shape_start = builder.shape_count
        box_cfg = newton.ModelBuilder.ShapeConfig()
        box_cfg.ke = mcfg["contact_ke"]
        box_cfg.kd = mcfg["contact_kd"]
        box_cfg.mu = mcfg["contact_mu"]
        box_cfg.is_hydroelastic = False
        box_cfg.gap = 0.002
        box_cfg.density = 0.0  # no extra mass
        for bi in cable_bodies:
            builder.add_shape_box(
                body=bi, hx=CABLE_SEG_LEN / 2,
                hy=CABLE_RADIUS * 1.5, hz=CABLE_RADIUS * 1.5,
                xform=wp.transform_identity(), cfg=box_cfg,
            )
        # Disable collision on original capsule shapes
        for si in range(cable_shape_start, cable_shape_end):
            builder.shape_flags[si] = 1  # VISIBLE only
        cable_shape_start = box_cable_shape_start
        cable_shape_end = builder.shape_count
        print(f"  [BOX-CABLE] Added {len(cable_bodies)} BOX shapes, disabled capsule collision")

    # Contact filters: cable vs floor, cable vs arm bodies 0-6
    for si in range(cable_shape_start, cable_shape_end):
        builder.add_shape_collision_filter_pair(si, floor_shape_idx)
    for cable_si in range(cable_shape_start, cable_shape_end):
        for arm_ss, arm_se, arm_bs in [(left_ss, left_se, left_bs), (right_ss, right_se, right_bs)]:
            for arm_si in range(arm_ss, arm_se):
                local_body = builder.shape_body[arm_si] - arm_bs
                if local_body < 7:
                    builder.add_shape_collision_filter_pair(cable_si, arm_si)

    robot_body_count = right_bs + FRANKA_NUM_JOINTS

    # Approximate finger meshes → CONVEX_MESH
    finger_mesh_indices = []
    for si in range(builder.shape_count):
        bi = builder.shape_body[si]
        if bi >= 0 and bi < robot_body_count:
            lb = bi - left_bs
            rb = bi - right_bs
            if lb in (7, 8) or rb in (7, 8):
                if builder.shape_type[si] == newton.GeoType.MESH:
                    finger_mesh_indices.append(si)
    if finger_mesh_indices:
        builder.approximate_meshes(method="convex_hull", shape_indices=finger_mesh_indices,
                                    keep_visual_shapes=True)

    builder.color()
    model = builder.finalize(device=DEVICE, requires_grad=False)

    # Zero inv_mass for kinematic bodies
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()

    if mcfg["dynamic_fingers"]:
        # Mode 2: keep finger bodies dynamic (inv_mass > 0)
        finger_body_indices = [left_bs + 7, left_bs + 8, right_bs + 7, right_bs + 8]
        for bi in range(robot_body_count):
            if bi in finger_body_indices:
                # Give fingers realistic mass: 0.05 kg → inv_mass = 20
                inv_mass[bi] = 20.0
                inv_inertia[bi] = np.array([100.0, 100.0, 100.0], dtype=np.float32)
            else:
                inv_mass[bi] = 0.0
                inv_inertia[bi] = np.zeros(3, dtype=np.float32)
        print(f"  [DYNAMIC-FINGER] Finger bodies {finger_body_indices} kept dynamic (inv_mass=20)")
    else:
        for bi in range(robot_body_count):
            inv_mass[bi] = 0.0
            inv_inertia[bi] = np.zeros(3, dtype=np.float32)

    model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=DEVICE)
    model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=DEVICE)

    scene_info = {
        "model": model,
        "left_body_start": left_bs,
        "right_body_start": right_bs,
        "cable_bodies": cable_bodies,
        "cable_joints": cable_joints,
        "robot_body_count": robot_body_count,
        "fk_model": fk_model,
        "fk_state": fk_state,
    }
    return scene_info


# ---------------------------------------------------------------------------
# Physics step (mode-aware)
# ---------------------------------------------------------------------------
def update_kinematic_bodies(physics_state, fk_state, robot_body_count, skip_bodies=None):
    """Copy robot body transforms from FK to physics. skip_bodies: set of body indices to skip."""
    fk_bq = fk_state.body_q.numpy()
    phys_bq = physics_state.body_q.numpy()
    for bi in range(robot_body_count):
        if skip_bodies and bi in skip_bodies:
            continue
        phys_bq[bi] = fk_bq[bi]
    physics_state.body_q.assign(phys_bq)


def apply_spring_forces(state, targets, k=5000.0, d=200.0):
    """Apply spring forces on specified bodies toward target positions.

    targets: dict {body_index: (tx, ty, tz)}
    Forces applied as body_f[bi][3:6] = -k * (pos - target) - d * vel
    """
    if not targets:
        return
    body_q = state.body_q.numpy()
    body_qd = state.body_qd.numpy()
    body_f = state.body_f.numpy()
    for bi, target in targets.items():
        pos = body_q[bi][:3]
        vel = body_qd[bi][3:6]  # linear velocity [3:6]
        tgt = np.array(target, dtype=np.float64)
        force = -k * (pos - tgt) - d * vel
        body_f[bi][3:6] += force  # linear force
    state.body_f.assign(body_f)


_phys_buf = None


def physics_step(model, state, solver, contacts, scene_info, mcfg,
                 spring_targets=None,
                 skip_finger_update=False):
    """VBD physics step with mode-specific modifications."""
    global _phys_buf
    if _phys_buf is None:
        _phys_buf = model.state()

    state_0 = state
    state_1 = _phys_buf
    fk_state = scene_info["fk_state"]
    rbc = scene_info["robot_body_count"]
    vbd_control = scene_info["vbd_control"]

    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    finger_bodies = {lb + 7, lb + 8, rb + 7, rb + 8}
    skip = finger_bodies if skip_finger_update else None

    for _ in range(SIM_SUBSTEPS):
        update_kinematic_bodies(state_0, fk_state, rbc, skip_bodies=skip)

        state_0.clear_forces()

        # Mode 2: spring force on dynamic fingers toward FK position
        if mcfg["dynamic_fingers"] and skip_finger_update:
            fk_bq = fk_state.body_q.numpy()
            finger_targets = {bi: fk_bq[bi][:3] for bi in finger_bodies}
            apply_spring_forces(state_0, finger_targets, k=10000.0, d=500.0)

        # Mode 3 (spring): spring force on cable bodies (with per-body offsets)
        if spring_targets:
            apply_spring_forces(state_0, spring_targets, k=2000.0, d=50.0)

        model.collide(state_0, contacts)
        solver.step(state_0, state_1, vbd_control, contacts, SIM_DT)

        state_0, state_1 = state_1, state_0

    return state_0


# ---------------------------------------------------------------------------
# IK helpers
# ---------------------------------------------------------------------------
def solve_ik_dual(scene_info, target_left, target_right):
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    left_ee = EE_BODY_OFFSET
    right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    tl = np.array([target_left], dtype=np.float32)
    tr = np.array([target_right], dtype=np.float32)

    obj_l = IKObjectivePosition(link_index=left_ee, link_offset=wp.vec3(0, 0, 0),
                                 target_positions=wp.array(tl, dtype=wp.vec3, device=DEVICE), weight=1.0)
    obj_r = IKObjectivePosition(link_index=right_ee, link_offset=wp.vec3(0, 0, 0),
                                 target_positions=wp.array(tr, dtype=wp.vec3, device=DEVICE), weight=1.0)

    c8 = math.cos(math.pi / 8)
    s8 = math.sin(math.pi / 8)
    target_rot = wp.array([wp.vec4(c8, s8, 0.0, 0.0)], dtype=wp.vec4, device=DEVICE)
    rot_l = IKObjectiveRotation(link_index=left_ee, link_offset_rotation=wp.quat_identity(),
                                 target_rotations=target_rot, weight=0.5)
    rot_r = IKObjectiveRotation(link_index=right_ee, link_offset_rotation=wp.quat_identity(),
                                 target_rotations=target_rot, weight=0.5)
    obj_jl = IKObjectiveJointLimit(joint_limit_lower=fk_model.joint_limit_lower,
                                    joint_limit_upper=fk_model.joint_limit_upper, weight=10.0)

    ik_solver = IKSolver(fk_model, n_problems=1, objectives=[obj_l, obj_r, rot_l, rot_r, obj_jl])
    fk_jq = fk_state.joint_q.numpy().copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=DEVICE)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=DEVICE)
    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
    return jq_out.numpy()[0], ik_solver.costs.numpy()[0]


def get_ee_positions(state, scene_info):
    bq = state.body_q.numpy()
    left_ee = scene_info["left_body_start"] + EE_BODY_OFFSET
    right_ee = scene_info["right_body_start"] + EE_BODY_OFFSET
    return bq[left_ee][:3], bq[right_ee][:3]


# ---------------------------------------------------------------------------
# Motion helpers
# ---------------------------------------------------------------------------
def ik_move_both(model, state, scene_info, solver, contacts, mcfg,
                 target_left, target_right, label="MOVE",
                 spring_targets=None,
                 skip_finger_update=False):
    """Move both EEs to target via IK interpolation."""
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    cable_bodies = scene_info["cable_bodies"]

    pos_l, pos_r = get_ee_positions(state, scene_info)
    dist = max(np.linalg.norm(np.array(target_left) - pos_l),
               np.linalg.norm(np.array(target_right) - pos_r))
    n_steps = max(int(dist * 100 * STEPS_PER_CM), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)

    tgt_l = np.array(target_left, dtype=np.float32)
    tgt_r = np.array(target_right, dtype=np.float32)

    jq_target, ik_cost = solve_ik_dual(scene_info, tuple(tgt_l), tuple(tgt_r))
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False

    fk_coord_count = fk_model.joint_coord_count
    jq_start = fk_state.joint_q.numpy().copy()
    finger_coords = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)
        jq_interp = jq_start.copy()
        for d in range(fk_coord_count):
            if d not in finger_coords:
                jq_interp[d] = jq_start[d] + (jq_target[d] - jq_start[d]) * t
        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

        # Update spring targets for Mode 3 (grip center moves with arm)
        active_springs = spring_targets
        if active_springs and callable(active_springs):
            active_springs = active_springs(state, scene_info)

        state = physics_step(model, state, solver, contacts, scene_info, mcfg,
                             spring_targets=active_springs,
                             skip_finger_update=skip_finger_update)

        if np.any(np.isnan(state.body_q.numpy()[cable_bodies])):
            print(f"  [{label}] Cable NaN at step {step}!")
            return state, False

        if step % max(n_steps // 4, 1) == 0:
            cur_l, cur_r = get_ee_positions(state, scene_info)
            err_l = np.linalg.norm(cur_l - tgt_l) * 1000
            err_r = np.linalg.norm(cur_r - tgt_r) * 1000
            bq = state.body_q.numpy()
            cz = bq[cable_bodies, 2]
            # Contact count
            model_obj = scene_info["model"]
            model_obj.collide(state, contacts)
            wp.synchronize()
            nc = contacts.rigid_contact_count.numpy()[0]
            fc = 0
            if nc > 0:
                s0 = contacts.rigid_contact_shape0.numpy()[:nc]
                s1 = contacts.rigid_contact_shape1.numpy()[:nc]
                sb = model_obj.shape_body.numpy()
                lb = scene_info["left_body_start"]
                rb = scene_info["right_body_start"]
                fset = {lb + 7, lb + 8, rb + 7, rb + 8}
                cset = set(cable_bodies)
                fc = sum(1 for ci in range(nc)
                         if (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                         and (sb[s0[ci]] in cset or sb[s1[ci]] in cset))
            print(f"  [{label}] step {step}/{n_steps}: err L={err_l:.1f}mm R={err_r:.1f}mm "
                  f"cable_z={np.mean(cz):.4f} fc={fc}")

    pos_l, pos_r = get_ee_positions(state, scene_info)
    err_l = np.linalg.norm(pos_l - tgt_l) * 1000
    err_r = np.linalg.norm(pos_r - tgt_r) * 1000
    converged = err_l < 10.0 and err_r < 10.0
    print(f"  [{label}] Final: err L={err_l:.1f}mm R={err_r:.1f}mm converged={converged}")
    return state, converged


def hold_position(model, state, scene_info, solver, contacts, mcfg,
                  n_steps, spring_targets=None,
                  skip_finger_update=False):
    """Hold current position for n_steps."""
    for _ in range(n_steps):
        active_springs = spring_targets
        if active_springs and callable(active_springs):
            active_springs = active_springs(state, scene_info)
        state = physics_step(model, state, solver, contacts, scene_info, mcfg,
                             spring_targets=active_springs,
                             skip_finger_update=skip_finger_update)
    return state


# ---------------------------------------------------------------------------
# P1 + P2 sequence
# ---------------------------------------------------------------------------
def run_grip_test(scene_info, mcfg, output_dir):
    """Run P1 (grasp) + P2 (lift) and return cable_z_delta."""
    model = scene_info["model"]
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    cable_bodies = scene_info["cable_bodies"]
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]

    state = model.state()
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control
    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)

    # Settle (2s)
    print("  [SETTLE] 2s...")
    for i in range(int(2.0 / DT)):
        state = physics_step(model, state, solver, contacts, scene_info, mcfg)
        if i % int(0.5 / DT) == 0:
            bq = state.body_q.numpy()
            cz = np.mean(bq[cable_bodies, 2])
            print(f"    t={i * DT:.1f}s cable_z={cz:.4f}")

    # Measure settled cable X for approach target
    bq = state.body_q.numpy()
    grasp_x = float(np.mean(bq[cable_bodies, 0]))

    # P1: Approach
    print(f"\n  [P1-APPROACH] → ({grasp_x:.3f}, Y, {APPROACH_Z})")
    state, _ = ik_move_both(model, state, scene_info, solver, contacts, mcfg,
                             target_left=(grasp_x, WIDE_LEFT_Y, APPROACH_Z),
                             target_right=(grasp_x, WIDE_RIGHT_Y, APPROACH_Z),
                             label="P1-APPROACH")

    # P1: Descend
    print(f"\n  [P1-DESCEND] → Z={GRASP_Z}")
    state, _ = ik_move_both(model, state, scene_info, solver, contacts, mcfg,
                             target_left=(grasp_x, WIDE_LEFT_Y, GRASP_Z),
                             target_right=(grasp_x, WIDE_RIGHT_Y, GRASP_Z),
                             label="P1-DESCEND")

    # P1: Close fingers (kinematic interpolation)
    print(f"\n  [P1-CLOSE] Closing fingers to {FINGER_CLOSE_POS * 1000:.1f}mm")
    fk_jq_pre = fk_state.joint_q.numpy().copy()
    for step in range(FINGER_CLOSE_STEPS):
        t = min((step + 1) / FINGER_CLOSE_STEPS, 1.0)
        fk_jq = fk_state.joint_q.numpy()
        for arm_offset in [0, FRANKA_NUM_JOINTS]:
            fk_jq[arm_offset + 7] = fk_jq_pre[arm_offset + 7] + (FINGER_CLOSE_POS - fk_jq_pre[arm_offset + 7]) * t
            fk_jq[arm_offset + 8] = fk_jq_pre[arm_offset + 8] + (FINGER_CLOSE_POS - fk_jq_pre[arm_offset + 8]) * t
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        state = physics_step(model, state, solver, contacts, scene_info, mcfg)

        if step % 100 == 0:
            bq = state.body_q.numpy()
            cz = np.mean(bq[cable_bodies, 2])
            model.collide(state, contacts)
            wp.synchronize()
            nc = contacts.rigid_contact_count.numpy()[0]
            fc = 0
            if nc > 0:
                s0 = contacts.rigid_contact_shape0.numpy()[:nc]
                s1 = contacts.rigid_contact_shape1.numpy()[:nc]
                sb = model.shape_body.numpy()
                fset = {lb + 7, lb + 8, rb + 7, rb + 8}
                cset = set(cable_bodies)
                fc = sum(1 for ci in range(nc)
                         if (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                         and (sb[s0[ci]] in cset or sb[s1[ci]] in cset))
            print(f"    close step {step}/{FINGER_CLOSE_STEPS}: cable_z={cz:.4f} fc={fc}")

    # Post-close contact check
    model.collide(state, contacts)
    wp.synchronize()
    nc = contacts.rigid_contact_count.numpy()[0]
    fc_final = 0
    if nc > 0:
        s0 = contacts.rigid_contact_shape0.numpy()[:nc]
        s1 = contacts.rigid_contact_shape1.numpy()[:nc]
        sb = model.shape_body.numpy()
        fset = {lb + 7, lb + 8, rb + 7, rb + 8}
        cset = set(cable_bodies)
        fc_final = sum(1 for ci in range(nc)
                       if (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                       and (sb[s0[ci]] in cset or sb[s1[ci]] in cset))
    print(f"  [P1-CLOSE] Final: finger-cable contacts={fc_final}, total={nc}")

    # Record cable Z before lift
    bq = state.body_q.numpy()
    cable_z_before = float(np.mean(bq[cable_bodies, 2]))
    print(f"  [P1-CLOSE] Cable Z before lift: {cable_z_before:.4f}")

    # --- Mode-specific P2 setup ---
    spring_targets = None
    skip_finger_update = False

    # Mode 2: switch fingers to dynamic for P2
    if mcfg["dynamic_fingers"]:
        skip_finger_update = True
        print("  [DYNAMIC-FINGER] Switching to dynamic finger mode for P2")

    # Mode 3 (spring): set up spring attachment with per-body relative offsets
    if mcfg["spring_attach"]:
        pos_l, pos_r = get_ee_positions(state, scene_info)
        grip_center = (pos_l + pos_r) / 2
        grip_center[2] -= EE_TO_FINGERTIP

        grasped_offsets = {}  # bi → offset from grip center at grasp time
        for bi in cable_bodies:
            pos = bq[bi][:3]
            dist = np.linalg.norm(pos - grip_center)
            if dist < 0.08:  # 80mm from grip center
                grasped_offsets[bi] = pos - grip_center

        if grasped_offsets:
            print(f"  [SPRING-ATTACH] Attaching {len(grasped_offsets)} cable bodies "
                  f"(relative offset, k=2000)")
            grasped_off = dict(grasped_offsets)  # capture for closure

            def make_spring_targets(state, scene_info):
                pos_l, pos_r = get_ee_positions(state, scene_info)
                gc = (pos_l + pos_r) / 2
                gc[2] -= EE_TO_FINGERTIP
                return {bi: tuple(gc + off) for bi, off in grasped_off.items()}

            spring_targets = make_spring_targets
        else:
            print("  [SPRING-ATTACH] WARNING: no cable bodies near grip!")

    # P2: Lift
    print(f"\n  [P2-LIFT] → Z={LIFT_Z} (dZ=+{(LIFT_Z - GRASP_Z) * 1000:.0f}mm)")
    state, _ = ik_move_both(model, state, scene_info, solver, contacts, mcfg,
                             target_left=(grasp_x, WIDE_LEFT_Y, LIFT_Z),
                             target_right=(grasp_x, WIDE_RIGHT_Y, LIFT_Z),
                             label="P2-LIFT",
                             spring_targets=spring_targets,
                             skip_finger_update=skip_finger_update)

    # Settle
    state = hold_position(model, state, scene_info, solver, contacts, mcfg,
                          SETTLE_STEPS, spring_targets=spring_targets,
                          skip_finger_update=skip_finger_update)

    # Measure result
    bq = state.body_q.numpy()
    cable_z_after = float(np.mean(bq[cable_bodies, 2]))
    cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)

    # Final contact check
    model.collide(state, contacts)
    wp.synchronize()
    nc_final = contacts.rigid_contact_count.numpy()[0]
    fc_p2 = 0
    if nc_final > 0:
        s0 = contacts.rigid_contact_shape0.numpy()[:nc_final]
        s1 = contacts.rigid_contact_shape1.numpy()[:nc_final]
        sb = model.shape_body.numpy()
        fset = {lb + 7, lb + 8, rb + 7, rb + 8}
        cset = set(cable_bodies)
        fc_p2 = sum(1 for ci in range(nc_final)
                    if (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                    and (sb[s0[ci]] in cset or sb[s1[ci]] in cset))

    print(f"\n  [RESULT] Cable Z: before={cable_z_before:.4f} after={cable_z_after:.4f}")
    print(f"  [RESULT] cable_z_delta = {cable_z_delta_mm} mm (threshold: 5mm)")
    print(f"  [RESULT] P2 finger-cable contacts: {fc_p2}")
    print(f"  [RESULT] {'PASS' if cable_z_delta_mm > 5.0 else 'FAIL'}")

    result = {
        "cable_z_before": cable_z_before,
        "cable_z_after": cable_z_after,
        "cable_z_delta_mm": cable_z_delta_mm,
        "p1_finger_cable_contacts": fc_final,
        "p2_finger_cable_contacts": fc_p2,
        "pass": cable_z_delta_mm > 5.0,
    }
    return result


# ---------------------------------------------------------------------------
# Mode runner
# ---------------------------------------------------------------------------
def run_mode(mode_name, output_dir):
    """Run one grip mode experiment."""
    global _phys_buf
    _phys_buf = None  # Reset physics buffer

    mcfg = MODE_CONFIGS[mode_name]
    print(f"\n{'=' * 60}")
    print(f"  MODE: {mode_name}")
    print(f"  ke={mcfg['contact_ke']}, kd={mcfg['contact_kd']}, mu={mcfg['contact_mu']}")
    print(f"  dynamic_fingers={mcfg['dynamic_fingers']}, spring_attach={mcfg['spring_attach']}, "
          f"box_cable={mcfg['box_cable']}")
    print(f"{'=' * 60}")

    mode_dir = os.path.join(output_dir, mode_name)
    os.makedirs(mode_dir, exist_ok=True)

    t0 = time.time()

    # Build FK model
    print("\n  [BUILD] FK model...")
    fk_model = build_fk_model()
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    for arm_offset in [0, FRANKA_NUM_JOINTS]:
        fk_jq[arm_offset + 7] = FINGER_OPEN_POS
        fk_jq[arm_offset + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Build scene
    print("  [BUILD] Physics scene...")
    scene_info = build_scene(fk_model, fk_state, mcfg)

    # Run P1 + P2
    result = run_grip_test(scene_info, mcfg, mode_dir)
    result["elapsed_s"] = round(time.time() - t0, 1)
    result["mode"] = mode_name

    # Save result
    with open(os.path.join(mode_dir, "result.json"), "w") as f:
        json.dump(result, f, indent=2)

    # Cleanup
    del scene_info, fk_model, fk_state
    gc.collect()
    wp.synchronize()

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Grip mode experiment")
    parser.add_argument("--mode", type=str, default=None,
                        choices=list(MODE_CONFIGS.keys()),
                        help="Run single mode (default: all)")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/grip_experiment_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    modes = [args.mode] if args.mode else list(MODE_CONFIGS.keys())
    print(f"[GRIP-EXPERIMENT] Modes: {modes}")
    print(f"[GRIP-EXPERIMENT] Device: {DEVICE}")
    print(f"[GRIP-EXPERIMENT] Output: {args.output_dir}")

    results = {}
    for mode_name in modes:
        try:
            results[mode_name] = run_mode(mode_name, args.output_dir)
        except Exception as e:
            print(f"\n  [ERROR] Mode {mode_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[mode_name] = {"mode": mode_name, "pass": False, "error": str(e)}

    # Print comparison table
    print(f"\n{'=' * 80}")
    print(f"  GRIP EXPERIMENT RESULTS")
    print(f"{'=' * 80}")
    print(f"  {'Mode':<20} {'delta_mm':>10} {'P1_fc':>8} {'P2_fc':>8} {'Time':>8} {'Result':>8}")
    print(f"  {'-' * 70}")
    for mode_name in modes:
        r = results.get(mode_name, {})
        delta = r.get("cable_z_delta_mm", "N/A")
        p1fc = r.get("p1_finger_cable_contacts", "N/A")
        p2fc = r.get("p2_finger_cable_contacts", "N/A")
        elapsed = r.get("elapsed_s", "N/A")
        passed = "PASS" if r.get("pass") else "FAIL"
        if "error" in r:
            passed = "CRASH"
        print(f"  {mode_name:<20} {delta:>10} {p1fc:>8} {p2fc:>8} {elapsed:>8} {passed:>8}")
    print(f"{'=' * 80}")

    # Save combined results
    combined_path = os.path.join(args.output_dir, "all_results.json")
    with open(combined_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved: {combined_path}")


if __name__ == "__main__":
    main()
