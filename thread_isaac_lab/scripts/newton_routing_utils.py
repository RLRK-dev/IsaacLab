# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton Routing Utilities — shared infrastructure for N-clip cable routing.

Provides reusable building blocks for Newton VBD cable routing tests:
  - FK model building and IK solving (dual-arm, single-arm)
  - Layout generation (random placement, nearest-neighbor + 2-opt routing, groove angles, bend analysis)
  - Scene building (kinematic arms, cable rod, clip visuals, table, collision filtering)
  - Physics stepping and kinematic body updates
  - Motion helpers (IK-driven arm movement, finger interpolation)
  - Groove insertion verification
  - Inchworm regrasp cycle (unclamp → rise → slide → regrasp)
  - Video recording (per-camera multi-angle)

Usage:
    from newton_routing_utils import (
        RoutingConfig, build_fk_model, build_scene, solve_ik_dual, ...
    )
"""

import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import trimesh
import warp as wp
import newton
from newton.solvers import SolverVBD
from newton.ik import (
    IKSolver, IKObjective, IKObjectivePosition, IKObjectiveRotation,
    IKObjectiveJointLimit,
)
from newton.viewer import ViewerGL

# ---------------------------------------------------------------------------
# Config imports (task_config.py SSOT)
# ---------------------------------------------------------------------------
_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    FRANKA_NUM_JOINTS, EE_BODY_OFFSET,
    TABLE_HEIGHT, ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE,
    APPROACH_Z, GRASP_Z, LIFT_Z, PUSH_Z,
    SIM_SUBSTEPS, NJMAX,
    CABLE_BEND_STIFFNESS, CABLE_BEND_DAMPING,
    CABLE_STRETCH_STIFFNESS, CABLE_STRETCH_DAMPING,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
    GRASP_X, CLIP_X, CLIP_GROOVE_INNER_RADIUS, P3_X_OFFSET,
    WIDE_LEFT_Y, WIDE_RIGHT_Y,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_CLOSE_STEPS,
    STEPS_PER_CM, CONVERGE_MM, MAX_MOVE_STEPS, SETTLE_STEPS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRANKA_URDF = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "source", "extensions", "isaaclab_tasks_thread", "data", "robots",
    "panda_independent_fingers.urdf",
))

# IK defaults
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0

# Cable defaults
CABLE_RADIUS = 0.004
CABLE_DIAMETER = 0.008
R_MIN_BEND = 5 * CABLE_DIAMETER   # 40mm

# Workspace bounds
WS_X_MIN = 0.22
WS_X_MAX = 0.48
WS_Y_MIN = -0.17
WS_Y_MAX = 0.17

# Layout defaults
MIN_CLIP_SPACING = 0.045    # 45mm min between clip centers
GRIP_OFFSET = 0.055         # 55mm from clip center to each grip position
MAX_GROOVE_DEVIATION_DEG = 55.0

# Finger half-open for slide-through
FINGER_HALF_OPEN_POS = 0.006

# Groove insertion check radius (relaxed for VBD non-determinism)
GROOVE_CHECK_RADIUS = 0.010  # 10mm

TENSION_COMPENSATION_GAIN = 1.3  # Amplify correction (cable doesn't follow arms 1:1 under tension)

# Post-push lateral correction: if cable min_dist exceeds this, slide arms to realign
LATERAL_CORRECTION_THRESHOLD_MM = 7.0

# Video defaults
VIDEO_FPS = 30
VIDEO_CAPTURE_EVERY = 16
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960

# Scene colors
COLOR_FINGER = (1.0, 0.2, 0.2)
COLOR_TABLE = (0.65, 0.50, 0.35)
COLOR_HAND = (0.3, 0.3, 0.6)
COLOR_ARM = (0.9, 0.9, 0.9)
COLOR_CLIP = (0.2, 0.7, 0.3)
COLOR_CLIP_PALETTE = [
    (0.2, 0.7, 0.3),   # green
    (0.3, 0.3, 0.8),   # blue
    (0.8, 0.6, 0.2),   # orange
    (0.7, 0.2, 0.7),   # purple
    (0.2, 0.7, 0.7),   # cyan
    (0.8, 0.2, 0.2),   # red
    (0.5, 0.8, 0.2),   # lime
    (0.8, 0.4, 0.6),   # pink
]

# JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# ===========================================================================
# Dual-arm IK collision avoidance
# ===========================================================================

# Collision sphere radii per local body index (link1=0, ..., EE/hand=6)
# Realistic link radii (not conservative bounds — just enough to prevent overlap)
COLLISION_SPHERE_RADII = {
    3: 0.035,  # link4 (forearm proximal)
    4: 0.030,  # link5 (forearm distal)
    5: 0.025,  # link6 (wrist)
    6: 0.035,  # link7+hand (EE)
}

# Cross-arm link pairs to check: (left_local_body, right_local_body)
# Focus on distal links most likely to collide during routing
COLLISION_PAIRS = [
    (4, 4),  # forearm dist vs forearm dist
    (5, 6),  # L wrist vs R EE
    (6, 5),  # L EE vs R wrist
    (6, 6),  # EE vs EE
    (4, 6),  # L forearm dist vs R EE
    (6, 4),  # L EE vs R forearm dist
]

COLLISION_WEIGHT = 5.0
COLLISION_MARGIN = 0.01  # 10mm softplus transition (near-zero far-field penalty)
CA_WAYPOINT_MM = 10.0    # Re-solve IK with CA every 10mm of task-space motion


@wp.kernel
def _dual_arm_pair_residual(
    body_q: wp.array2d(dtype=wp.transform),  # (batch_rows, n_bodies)
    left_link: int,
    right_link: int,
    left_radius: float,
    right_radius: float,
    start_idx: int,
    weight: float,
    margin: float,
    problem_idx: wp.array1d(dtype=wp.int32),  # (batch_rows,)
    # outputs
    residuals: wp.array2d(dtype=wp.float32),  # (batch_rows, total_residuals)
):
    row_idx = wp.tid()

    tf_l = body_q[row_idx, left_link]
    tf_r = body_q[row_idx, right_link]

    pos_l = wp.transform_get_translation(tf_l)
    pos_r = wp.transform_get_translation(tf_r)

    dist = wp.length(pos_l - pos_r)
    delta = (left_radius + right_radius) - dist
    pen = wp.log(1.0 + wp.exp(delta / margin)) * margin

    residuals[row_idx, start_idx] = weight * pen


@wp.kernel
def _jac_fill_1d(
    q_grad: wp.array2d(dtype=wp.float32),  # (n_batch, n_dofs)
    n_dofs: int,
    residual_idx: int,
    # outputs
    jacobian: wp.array3d(dtype=wp.float32),  # (n_batch, n_residuals, n_dofs)
):
    """Copy autodiff gradient into the Jacobian at the correct residual row."""
    batch_idx = wp.tid()
    for j in range(n_dofs):
        jacobian[batch_idx, residual_idx, j] = q_grad[batch_idx, j]


class DualArmLinkAvoidObjective(IKObjective):
    """Sphere-sphere collision avoidance between a left-arm link and a right-arm link.

    Produces a single residual per problem (softplus of penetration depth).
    Both link positions are read from body_q, so they update as IK iterates.
    """

    def __init__(self, left_link, right_link, left_radius, right_radius,
                 weight=COLLISION_WEIGHT, margin=COLLISION_MARGIN):
        super().__init__()
        self.left_link = left_link
        self.right_link = right_link
        self.left_radius = left_radius
        self.right_radius = right_radius
        self.weight = weight
        self.margin = margin
        self.device = None
        self._e_array = None

    def residual_dim(self):
        return 1

    def init_buffers(self, model, jacobian_mode):
        self._require_batch_layout()
        # Build unit-vector seed for autodiff: 1.0 at this objective's residual slot
        e = np.zeros((self.n_batch, self.total_residuals), dtype=np.float32)
        for prob_idx in range(self.n_batch):
            e[prob_idx, self.residual_offset] = 1.0
        self._e_array = wp.array(e.flatten(), dtype=wp.float32, device=self.device)

    def compute_residuals(self, body_q, joint_q, model, residuals, start_idx, problem_idx):
        count = body_q.shape[0]
        wp.launch(
            _dual_arm_pair_residual,
            dim=count,
            inputs=[
                body_q,
                self.left_link, self.right_link,
                self.left_radius, self.right_radius,
                start_idx, self.weight, self.margin,
                problem_idx,
            ],
            outputs=[residuals],
            device=self.device,
        )

    def compute_jacobian_autodiff(self, tape, model, jacobian, start_idx, dq_dof):
        self._require_batch_layout()
        tape.backward(grads={tape.outputs[0]: self._e_array})
        q_grad = tape.gradients[dq_dof]
        n_dofs = model.joint_dof_count
        wp.launch(
            _jac_fill_1d,
            dim=self.n_batch,
            inputs=[q_grad, n_dofs, start_idx],
            outputs=[jacobian],
            device=self.device,
        )
        tape.zero()


def _build_collision_objectives():
    """Build collision avoidance objectives for all configured link pairs."""
    objs = []
    for l_local, r_local in COLLISION_PAIRS:
        l_idx = l_local  # left arm FK body index = local body index
        r_idx = FRANKA_NUM_JOINTS + r_local  # right arm FK body index
        l_radius = COLLISION_SPHERE_RADII[l_local]
        r_radius = COLLISION_SPHERE_RADII[r_local]
        objs.append(DualArmLinkAvoidObjective(
            left_link=l_idx, right_link=r_idx,
            left_radius=l_radius, right_radius=r_radius,
        ))
    return objs


# ===========================================================================
# Angle helpers
# ===========================================================================
def normalize_angle(a):
    """Normalize angle to [-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def groove_cable_angle(groove_theta, cable_dir):
    """Min angle between groove axis and cable direction [0, pi/2]."""
    d1 = abs(normalize_angle(groove_theta - cable_dir))
    d2 = abs(normalize_angle(groove_theta + math.pi - cable_dir))
    return min(d1, d2)


# ===========================================================================
# Layout generation
# ===========================================================================
def generate_positions(n_clips=20, seed=42, max_attempts=5000,
                       x_range=(WS_X_MIN, WS_X_MAX),
                       y_range=(WS_Y_MIN, WS_Y_MAX),
                       min_spacing=MIN_CLIP_SPACING):
    """Place n_clips with random (x, y) respecting spacing constraint."""
    rng = np.random.RandomState(seed)
    positions = []
    attempts = 0
    while len(positions) < n_clips and attempts < max_attempts:
        attempts += 1
        x = rng.uniform(x_range[0], x_range[1])
        y = rng.uniform(y_range[0], y_range[1])
        too_close = any(
            math.hypot(x - px, y - py) < min_spacing
            for px, py in positions
        )
        if too_close:
            continue
        positions.append((x, y))
    if len(positions) < n_clips:
        print(f"  [WARN] Placed {len(positions)}/{n_clips} after {max_attempts} attempts")
    return positions


def compute_route_order(positions, r_min_bend=R_MIN_BEND):
    """Nearest-neighbor + 2-opt improvement for smooth cable path."""
    n = len(positions)
    pos = np.array(positions)

    # nearest-neighbor seed
    visited = [False] * n
    order = [0]
    visited[0] = True
    for _ in range(n - 1):
        last = order[-1]
        dists = np.linalg.norm(pos - pos[last], axis=1)
        dists[visited] = np.inf
        nxt = int(np.argmin(dists))
        order.append(nxt)
        visited[nxt] = True

    # 2-opt improvement
    def route_cost(route):
        total = 0.0
        for i in range(len(route) - 1):
            d = np.linalg.norm(pos[route[i]] - pos[route[i + 1]])
            total += d
            if i > 0:
                v1 = pos[route[i]] - pos[route[i - 1]]
                v2 = pos[route[i + 1]] - pos[route[i]]
                n1 = np.linalg.norm(v1)
                n2 = np.linalg.norm(v2)
                if n1 > 1e-9 and n2 > 1e-9:
                    cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1)
                    bend = math.acos(cos_a)
                    total += bend * bend * r_min_bend * 2.0
        return total

    best_cost = route_cost(order)
    improved = True
    passes = 0
    while improved and passes < 50:
        improved = False
        passes += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                new_order = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                c = route_cost(new_order)
                if c < best_cost - 1e-9:
                    order = new_order
                    best_cost = c
                    improved = True
    if passes > 1:
        print(f"  [ROUTE] 2-opt: {passes} passes, cost={best_cost:.4f}")

    return order


def assign_groove_angles(positions, route, seed=42,
                         r_min_bend=R_MIN_BEND,
                         max_groove_deviation_deg=MAX_GROOVE_DEVIATION_DEG):
    """Assign groove angles biased toward cable path direction + distance-adaptive perturbation."""
    rng = np.random.RandomState(seed + 7)
    n = len(route)
    thetas = [0.0] * len(positions)

    for j in range(n):
        idx = route[j]
        cx, cy = positions[idx]
        dirs = []
        neighbor_dists = []
        if j > 0:
            px, py = positions[route[j - 1]]
            dirs.append(math.atan2(cy - py, cx - px))
            neighbor_dists.append(math.hypot(cx - px, cy - py))
        if j < n - 1:
            nx, ny = positions[route[j + 1]]
            dirs.append(math.atan2(ny - cy, nx - cx))
            neighbor_dists.append(math.hypot(nx - cx, ny - cy))

        if dirs:
            avg_dir = math.atan2(
                sum(math.sin(d) for d in dirs),
                sum(math.cos(d) for d in dirs),
            )
            d_min = min(neighbor_dists)
            budget_rad = d_min / (2.0 * r_min_bend)
            max_dev = min(budget_rad, math.radians(max_groove_deviation_deg))
            perturbation = rng.uniform(-max_dev, max_dev)
            thetas[idx] = normalize_angle(avg_dir + perturbation)
        else:
            thetas[idx] = rng.uniform(-math.pi, math.pi)

    return thetas


def analyze_bends(positions, thetas, route, r_min_bend=R_MIN_BEND):
    """Analyze cable bend feasibility for each consecutive pair in route."""
    segments = []
    for j in range(len(route) - 1):
        ai = route[j]
        bi = route[j + 1]
        ax, ay = positions[ai]
        bx, by = positions[bi]
        dist = math.hypot(bx - ax, by - ay)
        phi = math.atan2(by - ay, bx - ax)
        exit_bend = groove_cable_angle(thetas[ai], phi)
        entry_bend = groove_cable_angle(thetas[bi], phi)
        exit_arc = exit_bend * r_min_bend
        entry_arc = entry_bend * r_min_bend
        total_arc = exit_arc + entry_arc
        feasible = total_arc <= dist
        segments.append({
            "from": ai, "to": bi,
            "dist_mm": round(dist * 1000, 1),
            "exit_bend_deg": round(math.degrees(exit_bend), 1),
            "entry_bend_deg": round(math.degrees(entry_bend), 1),
            "total_bend_deg": round(math.degrees(exit_bend + entry_bend), 1),
            "arc_needed_mm": round(total_arc * 1000, 1),
            "feasible": feasible,
        })
    return segments


def cable_path_length(positions, route):
    """Total Euclidean cable path length through routed clips."""
    total = 0.0
    for j in range(len(route) - 1):
        ax, ay = positions[route[j]]
        bx, by = positions[route[j + 1]]
        total += math.hypot(bx - ax, by - ay)
    return total


# ===========================================================================
# FK model
# ===========================================================================
def build_fk_model(device, gravity=-9.81):
    """Build a robot-only FK model (no cable, no physics)."""
    builder = newton.ModelBuilder(gravity=gravity)
    cfg = newton.ModelBuilder.ShapeConfig()
    cfg.gap = 0.0
    cfg.density = 0.0
    builder.default_shape_cfg = cfg
    builder.add_urdf(
        FRANKA_URDF,
        xform=wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()),
        floating=False, enable_self_collisions=False, collapse_fixed_joints=True,
    )
    builder.add_urdf(
        FRANKA_URDF,
        xform=wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
        floating=False, enable_self_collisions=False, collapse_fixed_joints=True,
    )
    model = builder.finalize(device=device, requires_grad=True)
    print(f"  [FK] Robot-only model: bodies={model.body_count}, joints={model.joint_count}")
    return model


def init_fk_state(fk_model, finger_open=True):
    """Initialize FK state at home position with optional finger open."""
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    if finger_open:
        for arm_offset in [0, FRANKA_NUM_JOINTS]:
            fk_jq[arm_offset + 7] = FINGER_OPEN_POS
            fk_jq[arm_offset + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    return fk_state


# ===========================================================================
# IK solving
# ===========================================================================
def _make_rotation_target(device):
    """Default EE rotation target: 22.5° pitch (pi/8)."""
    cos8 = math.cos(math.pi / 8)
    sin8 = math.sin(math.pi / 8)
    return wp.array([wp.vec4(cos8, sin8, 0.0, 0.0)], dtype=wp.vec4, device=device)


def solve_ik_dual(fk_model, fk_state, target_left, target_right, device,
                  iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE,
                  collision_avoidance=True):
    """Solve dual-arm IK with inter-arm collision avoidance. Returns (joint_q, cost)."""
    lee = EE_BODY_OFFSET
    ree = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    tl = np.array([target_left], dtype=np.float32)
    tr = np.array([target_right], dtype=np.float32)

    obj_l = IKObjectivePosition(
        link_index=lee, link_offset=wp.vec3(0, 0, 0),
        target_positions=wp.array(tl, dtype=wp.vec3, device=device), weight=1.0,
    )
    obj_r = IKObjectivePosition(
        link_index=ree, link_offset=wp.vec3(0, 0, 0),
        target_positions=wp.array(tr, dtype=wp.vec3, device=device), weight=1.0,
    )
    rot_tgt = _make_rotation_target(device)
    rot_l = IKObjectiveRotation(
        link_index=lee, link_offset_rotation=wp.quat_identity(),
        target_rotations=rot_tgt, weight=0.5,
    )
    rot_r = IKObjectiveRotation(
        link_index=ree, link_offset_rotation=wp.quat_identity(),
        target_rotations=rot_tgt, weight=0.5,
    )
    collision_objs = _build_collision_objectives() if collision_avoidance else []
    obj_jl = IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper, weight=10.0,
    )

    all_objs = [obj_l, obj_r, rot_l, rot_r, *collision_objs, obj_jl]
    solver = IKSolver(fk_model, n_problems=1, objectives=all_objs)
    fk_jq = fk_state.joint_q.numpy().copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=device)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=device)
    solver.step(jq_in, jq_out, iterations=iterations, step_size=step_size)
    cost = float(solver.costs.numpy()[0])
    result = jq_out.numpy()[0]
    return result, cost


def solve_ik_single(fk_model, fk_state, target, arm, device,
                    iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE):
    """Solve IK for a single arm, keeping the other arm's joints fixed. Returns (joint_q, cost)."""
    ee_body = EE_BODY_OFFSET if arm == "left" else FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    target_arr = np.array([target], dtype=np.float32)
    obj_pos = IKObjectivePosition(
        link_index=ee_body, link_offset=wp.vec3(0, 0, 0),
        target_positions=wp.array(target_arr, dtype=wp.vec3, device=device), weight=1.0,
    )
    rot_tgt = _make_rotation_target(device)
    obj_rot = IKObjectiveRotation(
        link_index=ee_body, link_offset_rotation=wp.quat_identity(),
        target_rotations=rot_tgt, weight=0.5,
    )
    obj_jl = IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper, weight=10.0,
    )

    solver = IKSolver(fk_model, n_problems=1,
                      objectives=[obj_pos, obj_rot, obj_jl])
    fk_jq = fk_state.joint_q.numpy().copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=device)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=device)
    solver.step(jq_in, jq_out, iterations=iterations, step_size=step_size)
    cost = float(solver.costs.numpy()[0])
    result = jq_out.numpy()[0]
    return result, cost


def eval_ik_errors(fk_model, fk_state, jq_result, target_left, target_right):
    """Evaluate IK position errors (mm) for both arms after setting joint_q."""
    lee = EE_BODY_OFFSET
    ree = FRANKA_NUM_JOINTS + EE_BODY_OFFSET
    fk_state.joint_q.assign(jq_result)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    bq = fk_state.body_q.numpy()
    err_l = float(np.linalg.norm(bq[lee][:3] - np.array(target_left))) * 1000
    err_r = float(np.linalg.norm(bq[ree][:3] - np.array(target_right))) * 1000
    return err_l, err_r


# ===========================================================================
# Scene building helpers
# ===========================================================================
def _load_finger_mesh():
    if not hasattr(_load_finger_mesh, "_cache"):
        stl_path = os.path.join(
            os.path.dirname(FRANKA_URDF),
            "franka_description", "meshes", "collision", "finger_v_groove_60deg_claw.stl",
        )
        tm = trimesh.load(stl_path)
        verts = np.array(tm.vertices, dtype=np.float32)
        faces = np.array(tm.faces, dtype=np.int32).flatten()
        _load_finger_mesh._cache = newton.Mesh(verts, faces)
        print(f"  [MESH] Loaded finger mesh: {len(tm.vertices)} verts, {len(tm.faces)} faces")
    return _load_finger_mesh._cache


def _load_arm_meshes():
    """Load Franka arm visual meshes (DAE) for high-quality rendering."""
    if not hasattr(_load_arm_meshes, "_cache"):
        visual_dir = os.path.join(
            os.path.dirname(FRANKA_URDF),
            "franka_description", "meshes", "visual",
        )
        cache = {}

        def _load_dae(dae_path):
            tm = trimesh.load(dae_path, force="mesh")
            verts = np.array(tm.vertices, dtype=np.float32)
            faces = np.array(tm.faces, dtype=np.int32).flatten()
            return newton.Mesh(verts, faces), len(tm.vertices)

        total_verts = 0
        for local_body in range(6):
            dae_name = f"link{local_body + 1}.dae"
            dae_path = os.path.join(visual_dir, dae_name)
            if os.path.exists(dae_path):
                mesh, nv = _load_dae(dae_path)
                cache[local_body] = [mesh]
                total_verts += nv
        meshes_6 = []
        for dae_name in ("link7.dae", "hand.dae"):
            dae_path = os.path.join(visual_dir, dae_name)
            if os.path.exists(dae_path):
                mesh, nv = _load_dae(dae_path)
                meshes_6.append(mesh)
                total_verts += nv
        if meshes_6:
            cache[6] = meshes_6
        _load_arm_meshes._cache = cache
        print(f"  [MESH] Loaded visual DAE meshes ({total_verts:,} total vertices)")
    return _load_arm_meshes._cache


def add_kinematic_arm(builder, fk_model, fk_state, arm_body_offset, label_prefix="arm"):
    """Add a kinematic Franka arm to the physics scene. Returns (body_start, shape_start, shape_end)."""
    body_start = len(builder.body_mass)
    shape_start = builder.shape_count
    fk_body_q = fk_state.body_q.numpy()
    finger_mesh = _load_finger_mesh()
    finger_cfg = newton.ModelBuilder.ShapeConfig()
    finger_cfg.ke = CABLE_CONTACT_KE
    finger_cfg.kd = CABLE_CONTACT_KD
    finger_cfg.mu = CABLE_CONTACT_MU
    finger_cfg.is_hydroelastic = False
    finger_cfg.gap = 0.003
    finger_cfg.density = 0.0
    arm_meshes = _load_arm_meshes()
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
        if local_body in (7, 8):
            if local_body == 8:
                mesh_rot = wp.quat_from_axis_angle(wp.vec3(0.0, 0.0, 1.0), np.pi)
                mesh_xf = wp.transform(wp.vec3(0.0, 0.0, 0.0), mesh_rot)
            else:
                mesh_xf = wp.transform_identity()
            builder.add_shape_mesh(
                body=body_id, mesh=finger_mesh, xform=mesh_xf, cfg=finger_cfg,
            )
        elif local_body in arm_meshes:
            for mesh in arm_meshes[local_body]:
                builder.add_shape_mesh(
                    body=body_id, mesh=mesh, xform=wp.transform_identity(), cfg=arm_cfg,
                )
        else:
            builder.add_shape_capsule(body=body_id, radius=0.04, half_height=0.05, cfg=arm_cfg)

    shape_end = builder.shape_count
    print(f"  [ARM-{label_prefix}] {FRANKA_NUM_JOINTS} kinematic bodies, "
          f"shapes=[{shape_start}:{shape_end}]")
    return body_start, shape_start, shape_end


def add_cable_rod(builder, start_pos, n_segments, seg_len=0.015, direction=(0, 1, 0)):
    """Add a VBD rod cable. Returns (body_ids, joint_ids)."""
    n_points = n_segments + 1
    dir_np = np.array(direction, dtype=np.float64)
    dir_np = dir_np / np.linalg.norm(dir_np)
    positions = []
    for i in range(n_points):
        p = np.array(start_pos) + dir_np * (i * seg_len)
        positions.append(tuple(p))
    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = CABLE_CONTACT_KE
    cable_cfg.kd = CABLE_CONTACT_KD
    cable_cfg.mu = CABLE_CONTACT_MU
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002
    cable_cfg.density = 1100.0
    body_ids, joint_ids = builder.add_rod(
        positions=positions, radius=CABLE_RADIUS,
        stretch_stiffness=CABLE_STRETCH_STIFFNESS,
        stretch_damping=CABLE_STRETCH_DAMPING,
        bend_stiffness=CABLE_BEND_STIFFNESS,
        bend_damping=CABLE_BEND_DAMPING,
        cfg=cable_cfg,
    )
    total_length = n_segments * seg_len
    print(f"  [CABLE] add_rod: {len(body_ids)} bodies, {len(joint_ids)} joints, "
          f"total_length={total_length*1000:.0f}mm")
    return body_ids, joint_ids


def add_clip_visual(builder, cx, cy, cz):
    """Add V-groove clip with physical collision at given position. Returns shape indices."""
    clip_parts = [
        (0, 0, 0.0025, 0.020, 0.015, 0.0025),
        (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
        (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
    ]
    clip_shape_indices = []
    for dx, dy, dz, hx, hy, hz in clip_parts:
        xf = wp.transform((cx + dx, cy + dy, cz + dz), wp.quat_identity())
        idx = builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz)
        clip_shape_indices.append(idx)
    return clip_shape_indices


def build_scene(device, clip_positions, fk_model, fk_state,
                use_cable=True, cable_segments=20, cable_seg_len=0.015,
                gravity=-9.81, table_half=(0.40, 0.45, 0.005)):
    """Build a complete Newton physics scene with table, clips, arms, and cable.

    Args:
        device: CUDA device string.
        clip_positions: list of (x, y, z) for each clip.
        fk_model: FK model for arm poses.
        fk_state: FK state with current joint positions.
        use_cable: whether to include cable rod.
        cable_segments: number of cable segments.
        cable_seg_len: segment length [m].
        gravity: gravity constant.
        table_half: table half-extents (hx, hy, hz).

    Returns:
        scene_info dict with model, body indices, shape indices, etc.
    """
    builder = newton.ModelBuilder(gravity=gravity)
    floor_shape_idx = builder.add_ground_plane()

    # Table
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_center_y = 0.0
    if clip_positions:
        table_center_y = np.mean([p[1] for p in clip_positions])
    table_xform = wp.transform(
        (0.3, table_center_y, TABLE_HEIGHT - table_half[2]), wp.quat_identity())
    table_idx = builder.add_shape_box(
        body=-1, hx=table_half[0], hy=table_half[1], hz=table_half[2],
        xform=table_xform, cfg=table_cfg,
    )
    print(f"  [SCENE] Table at z={TABLE_HEIGHT}")

    # Clips (visual-only)
    all_clip_shape_indices = []
    for i, (cx, cy, cz) in enumerate(clip_positions):
        indices = add_clip_visual(builder, cx, cy, cz)
        all_clip_shape_indices.append(indices)
        print(f"  [SCENE] Clip{i} at ({cx}, {cy}, {cz})")

    # Arms
    left_body_start, left_shape_start, left_shape_end = add_kinematic_arm(
        builder, fk_model, fk_state, arm_body_offset=0, label_prefix="left")
    right_body_start, right_shape_start, right_shape_end = add_kinematic_arm(
        builder, fk_model, fk_state, arm_body_offset=FRANKA_NUM_JOINTS, label_prefix="right")

    # Contact filtering: arm bodies 0-6 → VISIBLE only
    filter_count = 0
    for arm_label, shape_start, shape_end, body_start in [
        ("left", left_shape_start, left_shape_end, left_body_start),
        ("right", right_shape_start, right_shape_end, right_body_start),
    ]:
        for si in range(shape_start, shape_end):
            body_idx = builder.shape_body[si]
            local_body = body_idx - body_start
            if local_body < 7:
                builder.shape_flags[si] = 1
                filter_count += 1
    print(f"  [SCENE] Contact filtering: {filter_count} arm shapes → VISIBLE only")

    # Cable
    cable_bodies = []
    cable_joints = []
    cable_shape_start = builder.shape_count
    if use_cable:
        cable_half_len = cable_segments * cable_seg_len / 2
        if clip_positions:
            cable_center_y = np.mean([p[1] for p in clip_positions])
        else:
            cable_center_y = 0.0
        cable_y_start = cable_center_y - cable_half_len
        cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CABLE_RADIUS)
        cable_bodies, cable_joints = add_cable_rod(
            builder, start_pos=cable_start, n_segments=cable_segments,
            seg_len=cable_seg_len, direction=(0, 1, 0))
        cable_shape_end = builder.shape_count
        cable_y_end = cable_start[1] + cable_segments * cable_seg_len
        print(f"  [SCENE] Cable: {len(cable_bodies)} bodies, "
              f"Y=[{cable_y_start:.3f}, {cable_y_end:.3f}]")

        # Filter cable vs floor
        for si in range(cable_shape_start, cable_shape_end):
            builder.add_shape_collision_filter_pair(si, floor_shape_idx)

        # Filter cable vs arm bodies 0-6
        cable_arm_filters = 0
        for cable_si in range(cable_shape_start, cable_shape_end):
            for arm_label, arm_shape_start, arm_shape_end, arm_body_start in [
                ("left", left_shape_start, left_shape_end, left_body_start),
                ("right", right_shape_start, right_shape_end, right_body_start),
            ]:
                for arm_si in range(arm_shape_start, arm_shape_end):
                    body_idx = builder.shape_body[arm_si]
                    local_body = body_idx - arm_body_start
                    if local_body < 7:
                        builder.add_shape_collision_filter_pair(cable_si, arm_si)
                        cable_arm_filters += 1
        print(f"  [SCENE] Cable filters: {cable_arm_filters} cable-arm")

    robot_body_count = right_body_start + FRANKA_NUM_JOINTS

    # Keep finger meshes as MESH (GeoType=8) — preserve concave V-groove/claw geometry
    finger_mesh_count = 0
    for shape_idx in range(builder.shape_count):
        body_idx = builder.shape_body[shape_idx]
        if body_idx >= 0 and body_idx < robot_body_count:
            local_body_l = body_idx - left_body_start
            local_body_r = body_idx - right_body_start
            if local_body_l in (7, 8) or local_body_r in (7, 8):
                if builder.shape_type[shape_idx] == newton.GeoType.MESH:
                    finger_mesh_count += 1
    print(f"  [SHAPES] {finger_mesh_count} finger meshes kept as MESH (concave)")

    builder.color()
    model = builder.finalize(device=device, requires_grad=False)

    # Zero inv_mass for kinematic bodies
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()
    for bi in range(robot_body_count):
        inv_mass[bi] = 0.0
        inv_inertia[bi] = np.zeros(3, dtype=np.float32)
    model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=device)
    model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=device)

    print(f"  [SCENE] Model: bodies={model.body_count}, joints={model.joint_count}")

    scene_info = {
        "model": model,
        "device": device,
        "left_body_start": left_body_start,
        "left_shape_start": left_shape_start,
        "left_shape_end": left_shape_end,
        "right_body_start": right_body_start,
        "right_shape_start": right_shape_start,
        "right_shape_end": right_shape_end,
        "cable_bodies": cable_bodies,
        "cable_joints": cable_joints,
        "n_cable_bodies": len(cable_bodies),
        "robot_body_count": robot_body_count,
        "table_shape_idx": table_idx,
        "clip_shape_indices": all_clip_shape_indices,
        "clip_positions": clip_positions,
        "fk_model": fk_model,
        "fk_state": fk_state,
    }
    return scene_info


# ===========================================================================
# Physics helpers
# ===========================================================================
def update_kinematic_bodies(physics_state, fk_state, robot_body_count):
    """Copy FK body poses to physics state for kinematic bodies."""
    fk_bq = fk_state.body_q.numpy()
    phys_bq = physics_state.body_q.numpy()
    phys_bq[:robot_body_count] = fk_bq[:robot_body_count]
    physics_state.body_q.assign(phys_bq)


_physics_state_buffer = {}  # keyed by device string


def physics_step(model, state, solver, contacts, scene_info,
                 dt=None, sim_substeps=None):
    """Execute one physics frame (multiple substeps)."""
    global _physics_state_buffer
    device = scene_info["device"]
    if device not in _physics_state_buffer:
        _physics_state_buffer[device] = model.state()
    state_0 = state
    state_1 = _physics_state_buffer[device]
    fk_state = scene_info["fk_state"]
    robot_body_count = scene_info["robot_body_count"]
    vbd_control = scene_info["vbd_control"]
    n_sub = sim_substeps or SIM_SUBSTEPS
    frame_dt = dt or (1.0 / 480.0)
    sub_dt = frame_dt / n_sub

    for i in range(n_sub):
        update_kinematic_bodies(state_0, fk_state, robot_body_count)
        state_0.clear_forces()
        model.collide(state_0, contacts)
        solver.step(state_0, state_1, vbd_control, contacts, sub_dt)
        state_0, state_1 = state_1, state_0
    return state_0


def reset_physics_buffer(device):
    """Clear cached physics state buffer (call on episode reset)."""
    global _physics_state_buffer
    _physics_state_buffer.pop(device, None)


# ===========================================================================
# EE position helpers
# ===========================================================================
def get_ee_positions(state, scene_info):
    """Get (left_ee_pos, right_ee_pos) as numpy arrays [3]."""
    body_q = state.body_q.numpy()
    left_ee = scene_info["left_body_start"] + EE_BODY_OFFSET
    right_ee = scene_info["right_body_start"] + EE_BODY_OFFSET
    return body_q[left_ee][:3], body_q[right_ee][:3]


# ===========================================================================
# Motion helpers
# ===========================================================================
def ik_move_both(model, state, scene_info, solver, contacts,
                 target_left, target_right, label="MOVE",
                 converge_mm=5.0, speed_factor=1.0):
    """Move both arms via task-space waypoints with per-waypoint collision avoidance."""
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    device = scene_info["device"]
    pos_l, pos_r = get_ee_positions(state, scene_info)
    dist = max(np.linalg.norm(np.array(target_left) - pos_l),
               np.linalg.norm(np.array(target_right) - pos_r))
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)
    print(f"  [{label}] dist={dist*1000:.1f}mm, steps={n_steps}")

    start_l = pos_l.copy()
    start_r = pos_r.copy()
    tgt_l = np.array(target_left, dtype=np.float32)
    tgt_r = np.array(target_right, dtype=np.float32)

    # Multi-waypoint IK planning: solve CA-aware IK at each task-space waypoint
    n_wp = max(int(dist * 1000 / CA_WAYPOINT_MM) + 1, 2)
    wp_jqs = []
    fk_jq_save = fk_state.joint_q.numpy().copy()

    for wi in range(n_wp):
        wt = wi / max(n_wp - 1, 1)
        wp_l = tuple(float(v) for v in start_l + (tgt_l - start_l) * wt)
        wp_r = tuple(float(v) for v in start_r + (tgt_r - start_r) * wt)
        jq, cost = solve_ik_dual(fk_model, fk_state, wp_l, wp_r, device)
        if np.any(np.isnan(jq)):
            print(f"  [{label}] IK NaN at waypoint {wi}/{n_wp}!")
            fk_state.joint_q.assign(fk_jq_save)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            return state, False
        wp_jqs.append(jq.copy())
        # Warm-start next waypoint from this solution
        fk_state.joint_q.assign(jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    print(f"  [{label}] IK planned: {n_wp} waypoints, cost={cost:.2e}")

    # Restore fk_state to first waypoint for execution
    fk_state.joint_q.assign(wp_jqs[0])
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    fk_coord_count = fk_model.joint_coord_count
    finger_coords = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}

    # Execute: joint-space interpolation between consecutive CA-aware waypoints
    step_global = 0
    for seg in range(n_wp - 1):
        jq_a = wp_jqs[seg]
        jq_b = wp_jqs[seg + 1]
        if seg < n_wp - 2:
            seg_steps = n_steps // (n_wp - 1)
        else:
            seg_steps = n_steps - step_global
        seg_steps = max(seg_steps, 1)

        for s in range(seg_steps):
            t = min((s + 1) / seg_steps, 1.0)
            jq_interp = jq_a.copy()
            for d in range(fk_coord_count):
                if d not in finger_coords:
                    jq_interp[d] = jq_a[d] + (jq_b[d] - jq_a[d]) * t
            fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            state = physics_step(model, state, solver, contacts, scene_info)
            recorder = scene_info.get("recorder")
            if recorder:
                recorder.capture(state)
            if cable_bodies:
                bq = state.body_q.numpy()
                if np.any(np.isnan(bq[cable_bodies])):
                    print(f"  [{label}] Cable NaN at step {step_global}!")
                    return state, False
            if step_global % max(n_steps // 5, 1) == 0:
                cur_l, cur_r = get_ee_positions(state, scene_info)
                err_l = np.linalg.norm(cur_l - tgt_l) * 1000
                err_r = np.linalg.norm(cur_r - tgt_r) * 1000
                print(f"  [{label}] step {step_global}/{n_steps}: "
                      f"err L={err_l:.1f}mm R={err_r:.1f}mm")
            step_global += 1

    pos_l, pos_r = get_ee_positions(state, scene_info)
    err_l = np.linalg.norm(pos_l - tgt_l) * 1000
    err_r = np.linalg.norm(pos_r - tgt_r) * 1000
    converged = err_l < converge_mm and err_r < converge_mm
    print(f"  [{label}] Final: err L={err_l:.1f}mm R={err_r:.1f}mm converged={converged}")
    return state, converged


def ik_move_single(model, state, scene_info, solver, contacts,
                   target, arm="right", label="MOVE",
                   converge_mm=5.0, speed_factor=1.0):
    """Move a single arm via task-space waypoints with per-waypoint collision avoidance."""
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    device = scene_info["device"]
    pos_l, pos_r = get_ee_positions(state, scene_info)
    current_pos = pos_l if arm == "left" else pos_r
    fixed_pos = pos_r if arm == "left" else pos_l
    dist = np.linalg.norm(np.array(target) - current_pos)
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)
    print(f"  [{label}] {arm} arm dist={dist*1000:.1f}mm, steps={n_steps}")

    start_pos = current_pos.copy()
    tgt = np.array(target, dtype=np.float32)

    # Multi-waypoint IK planning: solve CA-aware IK at each task-space waypoint
    n_wp = max(int(dist * 1000 / CA_WAYPOINT_MM) + 1, 2)
    wp_jqs = []
    fk_jq_save = fk_state.joint_q.numpy().copy()

    fixed_tup = tuple(float(v) for v in fixed_pos)
    for wi in range(n_wp):
        wt = wi / max(n_wp - 1, 1)
        wp_pos = tuple(float(v) for v in start_pos + (tgt - start_pos) * wt)
        if arm == "left":
            jq, cost = solve_ik_dual(fk_model, fk_state, wp_pos, fixed_tup, device)
        else:
            jq, cost = solve_ik_dual(fk_model, fk_state, fixed_tup, wp_pos, device)
        if np.any(np.isnan(jq)):
            print(f"  [{label}] IK NaN at waypoint {wi}/{n_wp}!")
            fk_state.joint_q.assign(fk_jq_save)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            return state, False
        wp_jqs.append(jq.copy())
        # Warm-start next waypoint from this solution
        fk_state.joint_q.assign(jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    print(f"  [{label}] IK planned: {n_wp} waypoints, cost={cost:.2e}")

    # Restore fk_state for execution
    fk_state.joint_q.assign(fk_jq_save)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    fk_coord_count = fk_model.joint_coord_count
    jq_base = fk_jq_save.copy()  # non-moving arm + fingers stay at original
    if arm == "left":
        arm_coords = set(range(7))
    else:
        arm_coords = set(range(FRANKA_NUM_JOINTS, FRANKA_NUM_JOINTS + 7))

    # Execute: joint-space interpolation between consecutive CA-aware waypoints
    step_global = 0
    for seg in range(n_wp - 1):
        jq_a = wp_jqs[seg]
        jq_b = wp_jqs[seg + 1]
        if seg < n_wp - 2:
            seg_steps = n_steps // (n_wp - 1)
        else:
            seg_steps = n_steps - step_global
        seg_steps = max(seg_steps, 1)

        for s in range(seg_steps):
            t = min((s + 1) / seg_steps, 1.0)
            jq_interp = jq_base.copy()
            for d in arm_coords:
                jq_interp[d] = jq_a[d] + (jq_b[d] - jq_a[d]) * t
            fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            state = physics_step(model, state, solver, contacts, scene_info)
            recorder = scene_info.get("recorder")
            if recorder:
                recorder.capture(state)
            if cable_bodies:
                bq = state.body_q.numpy()
                if np.any(np.isnan(bq[cable_bodies])):
                    print(f"  [{label}] Cable NaN at step {step_global}!")
                    return state, False
            if step_global % max(n_steps // 5, 1) == 0:
                cur_l, cur_r = get_ee_positions(state, scene_info)
                cur_pos = cur_l if arm == "left" else cur_r
                err = np.linalg.norm(cur_pos - tgt) * 1000
                print(f"  [{label}] step {step_global}/{n_steps}: err={err:.1f}mm")
            step_global += 1

    cur_l, cur_r = get_ee_positions(state, scene_info)
    cur_pos = cur_l if arm == "left" else cur_r
    err = np.linalg.norm(cur_pos - tgt) * 1000
    converged = err < converge_mm
    print(f"  [{label}] Final: err={err:.1f}mm converged={converged}")
    return state, converged


def hold_position(model, state, scene_info, solver, contacts, n_steps):
    """Hold current position for n_steps (settle / stabilize)."""
    for step in range(n_steps):
        state = physics_step(model, state, solver, contacts, scene_info)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)
    return state


def set_finger_positions(scene_info, left_pos=None, right_pos=None):
    """Set finger joint positions in FK model. None = keep current."""
    fk_state = scene_info["fk_state"]
    fk_model = scene_info["fk_model"]
    fk_jq = fk_state.joint_q.numpy()
    if left_pos is not None:
        fk_jq[7] = left_pos
        fk_jq[8] = left_pos
    if right_pos is not None:
        fk_jq[FRANKA_NUM_JOINTS + 7] = right_pos
        fk_jq[FRANKA_NUM_JOINTS + 8] = right_pos
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)


def interpolate_fingers(model, state, scene_info, solver, contacts,
                        left_target=None, right_target=None,
                        n_steps=None, label="FINGER"):
    """Smoothly interpolate finger positions over n_steps."""
    if n_steps is None:
        n_steps = FINGER_CLOSE_STEPS
    fk_state = scene_info["fk_state"]
    fk_model = scene_info["fk_model"]
    fk_jq_start = fk_state.joint_q.numpy().copy()

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)
        fk_jq = fk_state.joint_q.numpy()
        if left_target is not None:
            fk_jq[7] = fk_jq_start[7] + (left_target - fk_jq_start[7]) * t
            fk_jq[8] = fk_jq_start[8] + (left_target - fk_jq_start[8]) * t
        if right_target is not None:
            fk_jq[FRANKA_NUM_JOINTS + 7] = fk_jq_start[FRANKA_NUM_JOINTS + 7] + \
                (right_target - fk_jq_start[FRANKA_NUM_JOINTS + 7]) * t
            fk_jq[FRANKA_NUM_JOINTS + 8] = fk_jq_start[FRANKA_NUM_JOINTS + 8] + \
                (right_target - fk_jq_start[FRANKA_NUM_JOINTS + 8]) * t
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        state = physics_step(model, state, solver, contacts, scene_info)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)

    fk_jq = fk_state.joint_q.numpy()
    print(f"  [{label}] Fingers: L={fk_jq[7]*1000:.1f}mm R={fk_jq[FRANKA_NUM_JOINTS+7]*1000:.1f}mm")
    return state


def check_groove_insertion(state, scene_info, clip_x, clip_y,
                           groove_radius=GROOVE_CHECK_RADIUS):
    """Check how many cable bodies are within groove_radius of clip center XY.

    Returns (bodies_in_groove, min_dist_mm, closest_body_idx, closest_pos).
    """
    cable_bodies = scene_info.get("cable_bodies", [])
    if not cable_bodies:
        return 0, 0.0, -1, None
    bq = state.body_q.numpy()
    cable_pos = bq[cable_bodies, :3]
    clip_xy = np.array([clip_x, clip_y])
    dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
    bodies_in_groove = int(np.sum(dists_xy < groove_radius))
    closest_idx = int(np.argmin(dists_xy))
    min_dist = float(np.min(dists_xy)) * 1000
    closest_pos = cable_pos[closest_idx]
    return bodies_in_groove, min_dist, cable_bodies[closest_idx], closest_pos


# ===========================================================================
# Inchworm regrasp cycle
# ===========================================================================
def do_inchworm_regrasp(model, state, scene_info, solver, contacts,
                        current_clip_xy, next_clip_xy,
                        label_prefix="INCH"):
    """Execute one inchworm regrasp cycle: unclamp → rise → regrasp.

    This is the generalized P5-P8 pattern for transitioning between any two clips.
    Cable is held in clips by VBD contact/friction (no kinematic locking).

    Args:
        model: Newton physics model.
        state: Current physics state.
        scene_info: Scene info dict.
        solver: VBD solver.
        contacts: Contact object.
        current_clip_xy: (x, y) of the clip just inserted.
        next_clip_xy: (x, y) of the next clip target (for arm placement).
        label_prefix: log label prefix.

    Returns:
        (state, result_dict)
    """
    cable_bodies = scene_info.get("cable_bodies", [])
    result = {"pass": True}

    # Step 1: Verify cable is in clip groove (VBD contact holds it)
    bodies_in_groove, min_dist, _, _ = check_groove_insertion(
        state, scene_info, current_clip_xy[0], current_clip_xy[1])
    result["bodies_in_groove"] = bodies_in_groove
    if bodies_in_groove == 0:
        result["pass"] = False
        result["fail_reason"] = "no_bodies_in_groove"
        return state, result

    # Step 2: Unclamp right, half-open left
    print(f"\n  [{label_prefix}-UNCLAMP] Right open + Left half-open")
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        left_target=FINGER_HALF_OPEN_POS, right_target=FINGER_OPEN_POS,
        n_steps=200, label=f"{label_prefix}-FINGERS",
    )

    # Step 3: Rise (cable slides through left arm)
    print(f"\n  [{label_prefix}-RISE] Left arm rises, cable slides through")
    pos_l, pos_r = get_ee_positions(state, scene_info)
    rise_z = LIFT_Z + 0.05
    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(pos_l[0], pos_l[1], rise_z),
        arm="left", label=f"{label_prefix}-RISE", speed_factor=2.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts, SETTLE_STEPS)

    # Step 4a: Left arm descends + closes to regrasp cable
    print(f"\n  [{label_prefix}-REGRASP] Left arm descend + close")
    pos_l, pos_r = get_ee_positions(state, scene_info)
    regrasp_x = pos_l[0]
    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(regrasp_x, pos_l[1], GRASP_Z),
        arm="left", label=f"{label_prefix}-L-DESCEND", converge_mm=3.0,
    )
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        left_target=FINGER_CLOSE_POS, n_steps=300,
        label=f"{label_prefix}-L-CLOSE",
    )

    # Step 4b: Right arm moves to cable — maximize grip span along routing dir
    print(f"\n  [{label_prefix}-REGRASP] Right arm -> cable near next clip")
    pos_l, pos_r = get_ee_positions(state, scene_info)
    routing_vec = np.array(next_clip_xy, dtype=np.float64) - np.array(current_clip_xy, dtype=np.float64)
    routing_dist = np.linalg.norm(routing_vec)
    if routing_dist > 1e-6:
        routing_dir = routing_vec / routing_dist
    else:
        routing_dir = np.array([0.0, -1.0])

    # Find cable body near target span along routing direction from left arm.
    # Target: ~spread width (120mm) past left arm along routing direction,
    # matching the arm spread used in do_move_to_clip.
    wp.synchronize()
    bq_now = state.body_q.numpy()
    left_xy = pos_l[:2]
    spread = WIDE_RIGHT_Y - WIDE_LEFT_Y  # 120mm
    ideal_right_xy = left_xy + spread * routing_dir

    right_grasp_x = float(ideal_right_xy[0])
    right_grasp_y = float(ideal_right_xy[1])
    best_dist = 1e9
    for bi in cable_bodies:
        cxy = bq_now[bi][:2]
        d = float(np.linalg.norm(cxy - ideal_right_xy))
        if d < best_dist:
            best_dist = d
            right_grasp_x = float(bq_now[bi][0])
            right_grasp_y = float(bq_now[bi][1])
    grip_span = float(np.linalg.norm(
        np.array([right_grasp_x, right_grasp_y]) - left_xy)) * 1000
    print(f"  [{label_prefix}] Cable at span target: "
          f"({right_grasp_x:.4f}, {right_grasp_y:.4f}), "
          f"span={grip_span:.0f}mm")

    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(right_grasp_x, right_grasp_y, APPROACH_Z),
        arm="right", label=f"{label_prefix}-R-APPROACH",
    )
    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(right_grasp_x, right_grasp_y, GRASP_Z),
        arm="right", label=f"{label_prefix}-R-DESCEND", converge_mm=5.0,
    )

    # Step 4c: Right arm closes
    print(f"\n  [{label_prefix}-REGRASP] Right arm close")
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        right_target=FINGER_CLOSE_POS, n_steps=300,
        label=f"{label_prefix}-R-CLOSE",
    )

    print(f"  [{label_prefix}] Both arms gripping — ready for next clip")
    return state, result


# ===========================================================================
# Grasp + push-to-clip (initial P1-P4 or subsequent clip insertion)
# ===========================================================================
def do_initial_grasp(model, state, scene_info, solver, contacts):
    """P1: Wide-stance approach + descend + grasp. Returns (state, result_dict)."""
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    fk_state = scene_info["fk_state"]

    print(f"\n  {'='*50}")
    print(f"  [P1] Wide-Stance Approach + Grasp")
    print(f"  {'='*50}")

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, APPROACH_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, APPROACH_Z),
        label="P1-APPROACH", converge_mm=10.0,
    )
    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, GRASP_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, GRASP_Z),
        label="P1-DESCEND", converge_mm=5.0,
    )

    # Close fingers
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        left_target=FINGER_CLOSE_POS, right_target=FINGER_CLOSE_POS,
        label="P1-CLOSE",
    )

    fk_jq = fk_state.joint_q.numpy()
    grip_l = fk_jq[7] + fk_jq[8]
    grip_r = fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8]
    print(f"  [P1] Grip: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")
    return state, {"pass": True}


def do_micro_lift(model, state, scene_info, solver, contacts):
    """P2: Micro-lift to confirm grip. Returns (state, result_dict)."""
    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)

    print(f"\n  {'='*50}")
    print(f"  [P2] Micro-Lift")
    print(f"  {'='*50}")

    cable_z_before = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_before = np.mean(bq[cable_bodies, 2])

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, LIFT_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, LIFT_Z),
        label="P2-LIFT",
    )
    state = hold_position(model, state, scene_info, solver, contacts, SETTLE_STEPS)

    cable_z_delta_mm = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_after = np.mean(bq[cable_bodies, 2])
        cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)
        print(f"  [P2] Cable lift: {cable_z_delta_mm}mm")

    lifted = cable_z_delta_mm > 5.0 if has_cable else True
    return state, {"pass": lifted, "cable_z_delta_mm": cable_z_delta_mm}


def do_move_to_clip(model, state, scene_info, solver, contacts,
                    clip_x, clip_y, label="P3", prev_clip_xy=None):
    """Move both arms from current position to above a clip. Returns (state, result_dict).

    Args:
        prev_clip_xy: (x, y) of the previously inserted clip. When provided, arms
            are placed using direction-based spread along the routing direction
            (prev_clip -> current_clip), so the cable crosses through the groove
            regardless of whether the transition is X-dominant, Y-dominant, or mixed.
    """
    print(f"\n  {'='*50}")
    print(f"  [{label}] Move to Clip ({clip_x:.3f}, {clip_y:.3f})")
    print(f"  {'='*50}")

    pos_l, pos_r = get_ee_positions(state, scene_info)

    spread = WIDE_RIGHT_Y - WIDE_LEFT_Y  # 120mm

    if prev_clip_xy is not None:
        # Direction-based arm placement: spread along routing direction.
        # This generalizes from Y-only asymmetry to arbitrary clip-to-clip
        # vectors (handles X-dominant, Y-dominant, and mixed transitions).
        curr_xy = np.array([clip_x, clip_y], dtype=np.float64)
        prev_xy = np.array([prev_clip_xy[0], prev_clip_xy[1]],
                           dtype=np.float64)
        routing_vec = curr_xy - prev_xy
        routing_dist = np.linalg.norm(routing_vec)
        if routing_dist > 1e-6:
            routing_dir = routing_vec / routing_dist
        else:
            routing_dir = np.array([0.0, -1.0])

        # Center with small overshoot along routing direction
        center_xy = curr_xy + P3_X_OFFSET * routing_dir
        # Left arm toward prev clip, right arm past current clip
        target_left_xy = center_xy - (spread / 2) * routing_dir
        target_right_xy = center_xy + (spread / 2) * routing_dir

        print(f"  [{label}] Direction-based: "
              f"prev=({prev_xy[0]:.3f},{prev_xy[1]:.3f}) "
              f"dir=({routing_dir[0]:.3f},{routing_dir[1]:.3f})")
        print(f"  [{label}] L=({target_left_xy[0]:.3f},{target_left_xy[1]:.3f})"
              f" R=({target_right_xy[0]:.3f},{target_right_xy[1]:.3f})")

        target_left = (float(target_left_xy[0]),
                       float(target_left_xy[1]), LIFT_Z)
        target_right = (float(target_right_xy[0]),
                        float(target_right_xy[1]), LIFT_Z)
    else:
        # First clip or no prior context: symmetric Y placement
        move_target_x = clip_x + P3_X_OFFSET
        target_left_y = clip_y - spread / 2
        target_right_y = clip_y + spread / 2
        target_left = (move_target_x, target_left_y, LIFT_Z)
        target_right = (move_target_x, target_right_y, LIFT_Z)

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=target_left, target_right=target_right,
        label=f"{label}-MOVE", converge_mm=8.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts, SETTLE_STEPS)
    return state, {"pass": ok}


def get_cable_midpoint_between_grips(state, scene_info):
    """Get the XY position of the cable body closest to the grip midpoint.

    When multiple clips are inserted, cable tension pulls the cable away from
    the EE geometric midpoint. This function reads the actual cable positions
    to determine where the cable really is.

    Returns: np.array([x, y]) of the cable midpoint, or None if no cable.
    """
    cable_bodies = scene_info.get("cable_bodies", [])
    if not cable_bodies:
        return None

    pos_l, pos_r = get_ee_positions(state, scene_info)
    ee_mid_xy = (pos_l[:2] + pos_r[:2]) / 2

    bq = state.body_q.numpy()
    cable_pos = bq[cable_bodies, :3]

    # Find cable body closest to the EE midpoint (this is the cable segment
    # between the grips that should cross through the clip groove)
    dists = np.linalg.norm(cable_pos[:, :2] - ee_mid_xy, axis=1)
    closest_idx = int(np.argmin(dists))

    return cable_pos[closest_idx, :2].copy()


def do_push_to_clip(model, state, scene_info, solver, contacts,
                    clip_x, clip_y, label="P4"):
    """Push both arms down to PUSH_Z at clip position.

    Uses midpoint correction: shifts both arms equally so their XY midpoint
    aligns with the clip center. This ensures the interpolated cable between
    grips passes through the clip groove regardless of arm spread direction.
    """
    print(f"\n  {'='*50}")
    print(f"  [{label}] Push Down to Clip ({clip_x:.3f}, {clip_y:.3f})")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    pos_l, pos_r = get_ee_positions(state, scene_info)

    # Dynamic cable midpoint correction: use actual cable XY (not EE midpoint)
    # to compensate for tension-induced drift from inserted clips.
    clip_xy = np.array([clip_x, clip_y])
    mid_xy = (pos_l[:2] + pos_r[:2]) / 2

    cable_mid_xy = get_cable_midpoint_between_grips(state, scene_info)
    if cable_mid_xy is not None:
        cable_offset = clip_xy - cable_mid_xy
        tension_drift = np.linalg.norm(cable_mid_xy - mid_xy) * 1000
        correction = cable_offset * TENSION_COMPENSATION_GAIN
        print(f"  [{label}] Cable midpoint correction: "
              f"cable_drift={tension_drift:.1f}mm, "
              f"correction=({correction[0]*1000:.1f}, {correction[1]*1000:.1f})mm "
              f"(gain={TENSION_COMPENSATION_GAIN})")
    else:
        correction = clip_xy - mid_xy
        if np.linalg.norm(correction) > 0.001:
            print(f"  [{label}] Midpoint correction (no cable): "
                  f"({correction[0]*1000:.1f}, {correction[1]*1000:.1f})mm")

    push_left_xy = pos_l[:2] + correction
    push_right_xy = pos_r[:2] + correction

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(float(push_left_xy[0]), float(push_left_xy[1]), PUSH_Z),
        target_right=(float(push_right_xy[0]), float(push_right_xy[1]), PUSH_Z),
        label=f"{label}-PUSH", speed_factor=2.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS * 3)

    bodies_in_groove, min_dist, closest_bi, closest_pos = check_groove_insertion(
        state, scene_info, clip_x, clip_y)
    cable_in_groove = True
    if has_cable:
        print(f"  [{label}] Clip ({clip_x:.3f},{clip_y:.3f}): "
              f"bodies_in_groove={bodies_in_groove}, min_dist={min_dist:.1f}mm")
        if closest_pos is not None:
            print(f"  [{label}] Closest body {closest_bi}: "
                  f"pos=({closest_pos[0]:.4f}, {closest_pos[1]:.4f}, {closest_pos[2]:.4f})")
        cable_in_groove = bodies_in_groove >= 1

        # Post-push lateral correction: if cable is close but not in groove,
        # slide both arms laterally at PUSH_Z to realign cable with clip center.
        if min_dist > LATERAL_CORRECTION_THRESHOLD_MM and closest_pos is not None:
            cable_xy = closest_pos[:2].copy()
            lateral_delta = clip_xy - cable_xy
            lateral_dist_mm = np.linalg.norm(lateral_delta) * 1000
            print(f"  [{label}] Lateral correction: cable→clip "
                  f"({lateral_delta[0]*1000:.1f}, {lateral_delta[1]*1000:.1f})mm "
                  f"(dist={lateral_dist_mm:.1f}mm)")

            pos_l, pos_r = get_ee_positions(state, scene_info)
            corr_left_xy = pos_l[:2] + lateral_delta
            corr_right_xy = pos_r[:2] + lateral_delta

            state, ok_lateral = ik_move_both(
                model, state, scene_info, solver, contacts,
                target_left=(float(corr_left_xy[0]), float(corr_left_xy[1]), PUSH_Z),
                target_right=(float(corr_right_xy[0]), float(corr_right_xy[1]), PUSH_Z),
                label=f"{label}-LATERAL", speed_factor=1.5,
            )
            ok = ok or ok_lateral  # lateral correction success overrides push failure
            state = hold_position(model, state, scene_info, solver, contacts,
                                  SETTLE_STEPS * 2)

            # Re-check groove insertion after correction
            bodies_in_groove, min_dist, closest_bi, closest_pos = check_groove_insertion(
                state, scene_info, clip_x, clip_y)
            cable_in_groove = bodies_in_groove >= 1
            print(f"  [{label}] After lateral: "
                  f"bodies_in_groove={bodies_in_groove}, min_dist={min_dist:.1f}mm")

    return state, {"pass": ok and cable_in_groove, "cable_in_groove": cable_in_groove,
                   "bodies_in_groove": bodies_in_groove, "min_dist_mm": min_dist}


# ===========================================================================
# Video recorder
# ===========================================================================
def _cam_angles(pos, tgt):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


class VideoRecorder:
    """Per-camera video recorder using Newton ViewerGL."""

    def __init__(self, output_dir, model, enabled=False, cameras=None, dt=1.0/480.0):
        self.enabled = enabled
        self.output_dir = output_dir
        self.viewer = None
        self.step_count = 0
        self.sim_time = 0.0
        self.dt = dt
        self._cam_frames = {}
        self._cam_params = []
        if not enabled:
            return
        if cameras is None:
            cameras = [
                ("overhead", (0.36, -0.10, 1.60), (0.36, -0.10, 0.80)),
                ("front",    (1.10, -0.10, 1.05), (0.30, -0.10, 0.82)),
                ("left",     (0.36, -0.75, 0.93), (0.36, -0.10, 0.82)),
                ("right",    (0.36,  0.55, 0.93), (0.36, -0.10, 0.82)),
                ("diag",     (0.70, -0.50, 1.00), (0.36, -0.10, 0.82)),
            ]
        self.viewer = ViewerGL(
            width=VIDEO_CAM_W, height=VIDEO_CAM_H,
            vsync=False, headless=True,
        )
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        for name, pos, tgt in cameras:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cam_params.append((name, wp.vec3(*pos), pitch, yaw))
            self._cam_frames[name] = []
        print(f"  [VIDEO] Recorder initialized "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {len(cameras)} cameras)")

    def capture(self, state):
        if not self.enabled or self.viewer is None:
            return
        self.step_count += 1
        self.sim_time += self.dt
        if self.step_count % VIDEO_CAPTURE_EVERY != 0:
            return
        for name, pos, pitch, yaw in self._cam_params:
            self.viewer.set_camera(pos, pitch, yaw)
            self.viewer.begin_frame(self.sim_time)
            self.viewer.log_state(state)
            self.viewer.end_frame()
            frame = self.viewer.get_frame().numpy().copy()
            self._cam_frames[name].append(frame)

    def finalize(self, episode_idx):
        if not self.enabled:
            return None
        n_frames = len(next(iter(self._cam_frames.values()), []))
        if n_frames == 0:
            return None
        try:
            from PIL import Image
        except ImportError:
            print("  [VIDEO] PIL not available")
            return None
        video_paths = []
        for name, _, _, _ in self._cam_params:
            frames = self._cam_frames[name]
            if not frames:
                continue
            frames_dir = os.path.join(
                self.output_dir, f"frames_ep{episode_idx}_{name}")
            os.makedirs(frames_dir, exist_ok=True)
            for i, f in enumerate(frames):
                Image.fromarray(f).save(
                    os.path.join(frames_dir, f"frame_{i:05d}.png"))
            video_path = os.path.join(
                self.output_dir, f"ep{episode_idx}_{name}.mp4")
            cmd = [
                "ffmpeg", "-y", "-framerate", str(VIDEO_FPS),
                "-i", os.path.join(frames_dir, "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "23", video_path,
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True, timeout=60)
                video_paths.append(video_path)
                import shutil
                shutil.rmtree(frames_dir, ignore_errors=True)
            except Exception as e:
                print(f"  [VIDEO] ffmpeg failed for {name}: {e}")
                video_paths.append(frames_dir)
        print(f"  [VIDEO] Saved {len(video_paths)} camera videos "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {n_frames} frames each)")
        return video_paths

    def reset(self):
        for name in self._cam_frames:
            self._cam_frames[name] = []
        self.step_count = 0
        self.sim_time = 0.0


def set_scene_colors(recorder, scene_info):
    """Apply semantic colors to scene shapes in the video recorder."""
    if not recorder.enabled or recorder.viewer is None:
        return
    model = scene_info["model"]
    shape_colors = {}
    shape_body = model.shape_body.numpy()
    robot_body_count = scene_info.get("robot_body_count", 18)
    for s_idx in range(len(shape_body)):
        body_idx = int(shape_body[s_idx])
        if body_idx < 0:
            continue
        if body_idx >= robot_body_count:
            continue
        local_body = body_idx % FRANKA_NUM_JOINTS
        if local_body in (7, 8):
            shape_colors[s_idx] = COLOR_FINGER
        elif local_body == 6:
            shape_colors[s_idx] = COLOR_HAND
        elif local_body <= 5:
            shape_colors[s_idx] = COLOR_ARM
    table_idx = scene_info.get("table_shape_idx")
    if table_idx is not None:
        shape_colors[table_idx] = COLOR_TABLE
    # Color each clip with palette
    for ci, clip_indices in enumerate(scene_info.get("clip_shape_indices", [])):
        color = COLOR_CLIP_PALETTE[ci % len(COLOR_CLIP_PALETTE)]
        for idx in clip_indices:
            shape_colors[idx] = color
    if shape_colors:
        recorder.viewer.update_shape_colors(shape_colors)


# ===========================================================================
# Settle + state snapshot
# ===========================================================================
def settle_scene(model, state, scene_info, solver, contacts, duration_s=2.0,
                 dt=1.0/480.0):
    """Settle physics scene for given duration. Returns state and settled cable X."""
    cable_bodies = scene_info.get("cable_bodies", [])
    n_steps = int(duration_s / dt)
    for i in range(n_steps):
        state = physics_step(model, state, solver, contacts, scene_info)
        if i % int(0.5 / dt) == 0:
            cable_info = ""
            if cable_bodies:
                bq = state.body_q.numpy()
                cable_z = np.mean(bq[cable_bodies, 2])
                cable_info = f" cable_z={cable_z:.4f}"
            print(f"  settle t={i*dt:.1f}s{cable_info}")

    settled_grasp_x = GRASP_X
    if cable_bodies:
        bq = state.body_q.numpy()
        cable_pos = bq[cable_bodies, :3]
        settled_grasp_x = float(np.mean(cable_pos[:, 0]))
        print(f"  Cable settled: mean_x={settled_grasp_x:.4f}")
    scene_info["settled_grasp_x"] = settled_grasp_x
    return state


def save_state_snapshot(model, state, fk_state):
    """Save a copy of all state arrays for episode reset."""
    snap = {
        "body_q": state.body_q.numpy().copy(),
        "body_qd": state.body_qd.numpy().copy(),
        "fk_jq": fk_state.joint_q.numpy().copy(),
    }
    if state.joint_q is not None:
        snap["joint_q"] = state.joint_q.numpy().copy()
        snap["joint_qd"] = state.joint_qd.numpy().copy()
    return snap


def restore_state_snapshot(model, state, solver, fk_state, fk_model, scene_info, snapshot):
    """Restore scene to a saved snapshot for episode reset."""
    device = scene_info["device"]
    state.body_q.assign(snapshot["body_q"])
    state.body_qd.assign(snapshot["body_qd"])
    if "joint_q" in snapshot and state.joint_q is not None:
        state.joint_q.assign(snapshot["joint_q"])
        state.joint_qd.assign(snapshot["joint_qd"])
    solver.body_q_prev.assign(snapshot["body_q"])
    if hasattr(solver, 'joint_sigma_prev') and solver.joint_sigma_prev is not None:
        solver.joint_sigma_prev.zero_()
    if hasattr(solver, 'joint_kappa_prev') and solver.joint_kappa_prev is not None:
        solver.joint_kappa_prev.zero_()
    if hasattr(solver, 'joint_dkappa_prev') and solver.joint_dkappa_prev is not None:
        solver.joint_dkappa_prev.zero_()
    reset_physics_buffer(device)

    fk_jq_reset = snapshot["fk_jq"].copy()
    for arm_offset in [0, FRANKA_NUM_JOINTS]:
        fk_jq_reset[arm_offset + 7] = FINGER_OPEN_POS
        fk_jq_reset[arm_offset + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq_reset)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    update_kinematic_bodies(state, fk_state, scene_info["robot_body_count"])

    print(f"  [RESET] Scene restored")
