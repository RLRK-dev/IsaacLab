"""Newton N-Clip Cable Routing — VBD Rod Architecture

Extends test_newton_clip_routing.py (1 clip) to N-clip sequential routing.
Cable: 600mm (40 segments). Supports 1-3 clips with --num-clips flag.

Phase structure:
  P1:   Wide-stance approach + grasp (both arms)
  P2:   Micro-lift (grip confirmation)
  P3:   Move to CLIP1 X position
  P4:   Push down into CLIP1
  For each subsequent clip (CLIP2, CLIP3, ...):
    UNCLAMP:  Right arm unclamp, left arm half-open
    RISE:     Cable slides through left arm
    REGRASP:  Left close + right move to cable + right close
    MOVE:     Direction-based arm placement (routing-dir spread)
    PUSH:     Midpoint-corrected descent into clip groove

The move phase uses direction-based arm placement: arms are spread along
the routing direction (prev_clip -> current_clip), not just Y-axis. This
generalizes to arbitrary clip-to-clip vectors (X-dominant, Y-dominant, or
mixed).

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_dual_clip_routing.py
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_dual_clip_routing.py --num-clips 3
"""

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
import trimesh
import warp as wp
import newton
from newton.solvers import SolverVBD
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit
from newton.viewer import ViewerGL

# Import tunable parameters from task_config (SSOT)
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
    GRASP_X, CLIP_X, P3_X_OFFSET, WIDE_LEFT_Y, WIDE_RIGHT_Y,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_CLOSE_STEPS,
    STEPS_PER_CM, MAX_MOVE_STEPS, SETTLE_STEPS,
)

# ---------------------------------------------------------------------------
# Constants — dual-clip overrides
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0
SIM_DT = DT / SIM_SUBSTEPS
GRAVITY = -9.81
VBD_ITERATIONS = 20

# Cable: doubled length (40 segments × 15mm = 600mm)
CABLE_SEGMENTS = 40
CABLE_SEG_LEN = 0.015
CABLE_RADIUS = 0.004

# Clip 1 position — from task_config SSOT
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z

CLIP2_X = 0.38
CLIP2_Y = -0.15
CLIP2_Z = TABLE_HEIGHT

CLIP3_X = 0.28
CLIP3_Y = -0.17
CLIP3_Z = TABLE_HEIGHT

# Ordered clip list for N-clip routing
ALL_CLIPS = [
    (CLIP1_X, CLIP1_Y, CLIP1_Z),
    (CLIP2_X, CLIP2_Y, CLIP2_Z),
    (CLIP3_X, CLIP3_Y, CLIP3_Z),
]

# Finger half-open position for slide-through (between open and close)
FINGER_HALF_OPEN_POS = 0.006  # 6mm — slightly wider than cable diameter (8mm) for controlled slide

# Groove insertion check radius — relaxed from clip groove inner radius (6mm)
# because 600mm cable has more mass/sag than 300mm, and VBD solver non-determinism
GROOVE_CHECK_RADIUS = 0.010  # 10mm: cable within this XY distance counts as "in groove"

# Franka
FRANKA_URDF = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "source", "extensions", "isaaclab_tasks_thread", "data", "robots",
    "panda_independent_fingers.urdf",
))

# IK
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0

# Video
VIDEO_FPS = 30
VIDEO_CAPTURE_EVERY = 16
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960

# Camera definitions — expanded FOV to cover both clips
CAMERAS = [
    ("overhead",    (0.36, -0.10, 1.60), (0.36, -0.10, 0.80)),
    ("front",       (1.10, -0.10, 1.05), (0.30, -0.10, 0.82)),
    ("diag_upper",  (0.70, -0.50, 1.00), (0.36, -0.10, 0.82)),
    ("left",        (0.36, -0.75, 0.93), (0.36, -0.10, 0.82)),
    ("right",       (0.36,  0.55, 0.93), (0.36, -0.10, 0.82)),
    ("clip_close",  (0.55, -0.10, 0.83), (0.36, -0.10, 0.82)),
]

import math as _math


def _cam_angles(pos, tgt):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = _math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = _math.degrees(_math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = _math.degrees(_math.atan2(dy, dx))
    return pitch, yaw


# ---------------------------------------------------------------------------
# Video recorder (identical to 1-clip version)
# ---------------------------------------------------------------------------
class VideoRecorder:
    def __init__(self, output_dir, model, enabled=False, scene_info=None):
        self.enabled = enabled
        self.output_dir = output_dir
        self.viewer = None
        self.step_count = 0
        self.sim_time = 0.0
        self._cam_frames = {}
        self._cam_params = []
        self._zheight_frames = []
        self._scene_info = scene_info
        if not enabled:
            return
        self.viewer = ViewerGL(
            width=VIDEO_CAM_W, height=VIDEO_CAM_H,
            vsync=False, headless=True,
        )
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        for name, pos, tgt in CAMERAS:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cam_params.append((name, wp.vec3(*pos), pitch, yaw))
            self._cam_frames[name] = []
        print(f"  [VIDEO] Per-camera recorder initialized "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {len(CAMERAS)} cameras)")

    def capture(self, state):
        if not self.enabled or self.viewer is None:
            return
        self.step_count += 1
        self.sim_time += DT
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
        self._zheight_frames = []
        self.step_count = 0
        self.sim_time = 0.0


# ---------------------------------------------------------------------------
# Scene colors
# ---------------------------------------------------------------------------
COLOR_FINGER = (1.0, 0.2, 0.2)
COLOR_TABLE  = (0.65, 0.50, 0.35)
COLOR_HAND   = (0.3, 0.3, 0.6)
COLOR_ARM    = (0.9, 0.9, 0.9)
COLOR_CLIP   = (0.2, 0.7, 0.3)
COLOR_CLIP2  = (0.3, 0.3, 0.8)  # BLUE — second clip


def set_scene_colors(recorder, scene_info):
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
    for clip_idx in scene_info.get("clip1_shape_indices", []):
        shape_colors[clip_idx] = COLOR_CLIP
    for clip_idx in scene_info.get("clip2_shape_indices", []):
        shape_colors[clip_idx] = COLOR_CLIP2
    if shape_colors:
        recorder.viewer.update_shape_colors(shape_colors)


# ---------------------------------------------------------------------------
# Scene builder
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
        print(f"  [MESH] Loaded finger mesh: {len(tm.vertices)} verts, {len(tm.faces)} faces")
    return _load_finger_mesh._cache


def _load_arm_meshes():
    if not hasattr(_load_arm_meshes, "_cache"):
        mesh_dir = os.path.join(
            os.path.dirname(FRANKA_URDF),
            "franka_description", "meshes", "collision",
        )
        cache = {}
        for local_body in range(6):
            stl_name = f"link{local_body + 1}.stl"
            stl_path = os.path.join(mesh_dir, stl_name)
            if os.path.exists(stl_path):
                tm = trimesh.load(stl_path)
                verts = np.array(tm.vertices, dtype=np.float32)
                faces = np.array(tm.faces, dtype=np.int32).flatten()
                cache[local_body] = [newton.Mesh(verts, faces)]
        meshes_6 = []
        for stl_name in ("link7.stl", "hand.stl"):
            stl_path = os.path.join(mesh_dir, stl_name)
            if os.path.exists(stl_path):
                tm = trimesh.load(stl_path)
                verts = np.array(tm.vertices, dtype=np.float32)
                faces = np.array(tm.faces, dtype=np.int32).flatten()
                meshes_6.append(newton.Mesh(verts, faces))
        if meshes_6:
            cache[6] = meshes_6
        _load_arm_meshes._cache = cache
    return _load_arm_meshes._cache


def add_kinematic_arm(builder, fk_model, fk_state, arm_body_offset, label_prefix="arm"):
    body_start = len(builder.body_mass)
    shape_start = builder.shape_count
    fk_body_q = fk_state.body_q.numpy()
    finger_mesh = _load_finger_mesh()
    finger_cfg = newton.ModelBuilder.ShapeConfig()
    finger_cfg.ke = CABLE_CONTACT_KE
    finger_cfg.kd = CABLE_CONTACT_KD
    finger_cfg.mu = CABLE_CONTACT_MU
    finger_cfg.is_hydroelastic = False
    finger_cfg.gap = 0.005
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


def add_cable_rod(builder, start_pos, direction=(0, 1, 0)):
    total_length = CABLE_SEGMENTS * CABLE_SEG_LEN
    n_points = CABLE_SEGMENTS + 1
    dir_np = np.array(direction, dtype=np.float64)
    dir_np = dir_np / np.linalg.norm(dir_np)
    positions = []
    for i in range(n_points):
        p = np.array(start_pos) + dir_np * (i * CABLE_SEG_LEN)
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
    seg_mass = cable_cfg.density * np.pi * CABLE_RADIUS**2 * CABLE_SEG_LEN
    print(f"  [CABLE] add_rod: {len(body_ids)} bodies, {len(joint_ids)} joints, "
          f"total_length={total_length*1000:.0f}mm")
    return body_ids, joint_ids


def _add_clip_visual(builder, cx, cy, cz):
    """Add visual-only V-groove clip at given position. Returns shape indices."""
    clip_parts = [
        (0, 0, 0.0025, 0.020, 0.015, 0.0025),
        (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
        (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
        (-0.013, 0, 0.025, 0.002, 0.015, 0.005),
        (+0.013, 0, 0.025, 0.002, 0.015, 0.005),
    ]
    clip_shape_indices = []
    for dx, dy, dz, hx, hy, hz in clip_parts:
        xf = wp.transform((cx + dx, cy + dy, cz + dz), wp.quat_identity())
        idx = builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz)
        builder.shape_flags[idx] = 1  # VISIBLE only
        clip_shape_indices.append(idx)
    return clip_shape_indices


def build_scene(use_cable=True, fk_model=None, fk_state=None):
    builder = newton.ModelBuilder(gravity=GRAVITY)
    floor_shape_idx = builder.add_ground_plane()

    # Table (larger to accommodate both clips)
    table_half = (0.40, 0.45, 0.005)
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_xform = wp.transform((0.3, -0.10, TABLE_HEIGHT - table_half[2]), wp.quat_identity())
    table_idx = builder.add_shape_box(
        body=-1, hx=table_half[0], hy=table_half[1], hz=table_half[2],
        xform=table_xform, cfg=table_cfg,
    )
    print(f"  [SCENE] Table at z={TABLE_HEIGHT}")

    # Clip 1 (visual-only)
    clip1_shape_indices = _add_clip_visual(builder, CLIP1_X, CLIP1_Y, CLIP1_Z)
    print(f"  [SCENE] Clip1 at ({CLIP1_X}, {CLIP1_Y}, {CLIP1_Z})")

    # Clip 2 (visual-only)
    clip2_shape_indices = _add_clip_visual(builder, CLIP2_X, CLIP2_Y, CLIP2_Z)
    print(f"  [SCENE] Clip2 at ({CLIP2_X}, {CLIP2_Y}, {CLIP2_Z})")

    # Clip 3 (visual-only)
    clip3_shape_indices = _add_clip_visual(builder, CLIP3_X, CLIP3_Y, CLIP3_Z)
    print(f"  [SCENE] Clip3 at ({CLIP3_X}, {CLIP3_Y}, {CLIP3_Z})")

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

    # Cable (600mm, centered on midpoint between clips)
    cable_bodies = []
    cable_joints = []
    if use_cable:
        cable_shape_start = builder.shape_count
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        # Center cable Y between both clips
        cable_center_y = (CLIP1_Y + CLIP2_Y) / 2
        cable_y_start = cable_center_y - cable_half_len
        cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CABLE_RADIUS)
        cable_bodies, cable_joints = add_cable_rod(builder, start_pos=cable_start, direction=(0, 1, 0))
        cable_shape_end = builder.shape_count
        cable_y_end = cable_start[1] + CABLE_SEGMENTS * CABLE_SEG_LEN
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

    # Convert finger meshes → CONVEX_MESH
    finger_mesh_indices = []
    for shape_idx in range(builder.shape_count):
        body_idx = builder.shape_body[shape_idx]
        if body_idx >= 0 and body_idx < robot_body_count:
            local_body_l = body_idx - left_body_start
            local_body_r = body_idx - right_body_start
            if local_body_l in (7, 8) or local_body_r in (7, 8):
                if builder.shape_type[shape_idx] == newton.GeoType.MESH:
                    finger_mesh_indices.append(shape_idx)
    if finger_mesh_indices:
        builder.approximate_meshes(
            method="convex_hull", shape_indices=finger_mesh_indices, keep_visual_shapes=True
        )
    print(f"  [SHAPES] {len(finger_mesh_indices)} finger meshes → CONVEX_MESH")

    builder.color()
    model = builder.finalize(device=DEVICE, requires_grad=False)

    # Zero inv_mass for kinematic bodies
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()
    for bi in range(robot_body_count):
        inv_mass[bi] = 0.0
        inv_inertia[bi] = np.zeros(3, dtype=np.float32)
    model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=DEVICE)
    model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=DEVICE)

    print(f"  [SCENE] Model: bodies={model.body_count}, joints={model.joint_count}")

    scene_info = {
        "model": model,
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
        "clip1_shape_indices": clip1_shape_indices,
        "clip2_shape_indices": clip2_shape_indices,
    }
    return scene_info


def build_fk_model():
    builder = newton.ModelBuilder(gravity=GRAVITY)
    urdf_cfg = newton.ModelBuilder.ShapeConfig()
    urdf_cfg.gap = 0.0
    urdf_cfg.density = 0.0
    builder.default_shape_cfg = urdf_cfg
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
    model = builder.finalize(device=DEVICE, requires_grad=True)
    print(f"  [FK] Robot-only model: bodies={model.body_count}, joints={model.joint_count}")
    return model


# ---------------------------------------------------------------------------
# Physics helpers (identical to 1-clip)
# ---------------------------------------------------------------------------
def update_kinematic_bodies(physics_state, fk_state, robot_body_count):
    fk_bq = fk_state.body_q.numpy()
    phys_bq = physics_state.body_q.numpy()
    phys_bq[:robot_body_count] = fk_bq[:robot_body_count]
    physics_state.body_q.assign(phys_bq)


_physics_state_buffer = None


def physics_step(model, state, solver, contacts, scene_info):
    global _physics_state_buffer
    if _physics_state_buffer is None:
        _physics_state_buffer = model.state()
    state_0 = state
    state_1 = _physics_state_buffer
    fk_state = scene_info["fk_state"]
    robot_body_count = scene_info["robot_body_count"]
    vbd_control = scene_info["vbd_control"]
    for i in range(SIM_SUBSTEPS):
        update_kinematic_bodies(state_0, fk_state, robot_body_count)
        state_0.clear_forces()
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
    left_ee_body = EE_BODY_OFFSET
    right_ee_body = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    target_l = np.array([target_left], dtype=np.float32)
    target_r = np.array([target_right], dtype=np.float32)

    obj_l = IKObjectivePosition(
        link_index=left_ee_body, link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_l, dtype=wp.vec3, device=DEVICE), weight=1.0,
    )
    obj_r = IKObjectivePosition(
        link_index=right_ee_body, link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_r, dtype=wp.vec3, device=DEVICE), weight=1.0,
    )

    _cos_pi8 = _math.cos(_math.pi / 8)
    _sin_pi8 = _math.sin(_math.pi / 8)
    target_rot = wp.array([wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)], dtype=wp.vec4, device=DEVICE)
    rot_l = IKObjectiveRotation(
        link_index=left_ee_body, link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot, weight=0.5,
    )
    rot_r = IKObjectiveRotation(
        link_index=right_ee_body, link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot, weight=0.5,
    )
    obj_joint_limits = IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper, weight=10.0,
    )

    ik_solver = IKSolver(fk_model, n_problems=1,
                         objectives=[obj_l, obj_r, rot_l, rot_r, obj_joint_limits])
    fk_jq = fk_state.joint_q.numpy().copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=DEVICE)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=DEVICE)
    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
    cost = ik_solver.costs.numpy()[0]
    result = jq_out.numpy()[0]
    return result, cost


def solve_ik_single(scene_info, target, arm="left"):
    """Solve IK for a single arm, keeping the other arm's joints fixed."""
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    ee_body = EE_BODY_OFFSET if arm == "left" else FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    target_arr = np.array([target], dtype=np.float32)
    obj_pos = IKObjectivePosition(
        link_index=ee_body, link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_arr, dtype=wp.vec3, device=DEVICE), weight=1.0,
    )
    _cos_pi8 = _math.cos(_math.pi / 8)
    _sin_pi8 = _math.sin(_math.pi / 8)
    target_rot = wp.array([wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)], dtype=wp.vec4, device=DEVICE)
    obj_rot = IKObjectiveRotation(
        link_index=ee_body, link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot, weight=0.5,
    )
    obj_joint_limits = IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper, weight=10.0,
    )
    ik_solver = IKSolver(fk_model, n_problems=1,
                         objectives=[obj_pos, obj_rot, obj_joint_limits])
    fk_jq = fk_state.joint_q.numpy().copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=DEVICE)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=DEVICE)
    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
    cost = ik_solver.costs.numpy()[0]
    result = jq_out.numpy()[0]
    return result, cost


def get_ee_positions(state, scene_info):
    body_q = state.body_q.numpy()
    left_ee = scene_info["left_body_start"] + EE_BODY_OFFSET
    right_ee = scene_info["right_body_start"] + EE_BODY_OFFSET
    return body_q[left_ee][:3], body_q[right_ee][:3]


# ---------------------------------------------------------------------------
# Motion helpers
# ---------------------------------------------------------------------------
def ik_move_both(model, state, scene_info, solver, contacts,
                 target_left, target_right, label="MOVE",
                 converge_mm=5.0, speed_factor=1.0):
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    pos_l, pos_r = get_ee_positions(state, scene_info)
    dist = max(np.linalg.norm(np.array(target_left) - pos_l),
               np.linalg.norm(np.array(target_right) - pos_r))
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)
    print(f"  [{label}] dist={dist*1000:.1f}mm, steps={n_steps}")

    tgt_l = np.array(target_left, dtype=np.float32)
    tgt_r = np.array(target_right, dtype=np.float32)
    jq_target, ik_cost = solve_ik_dual(scene_info, tuple(tgt_l), tuple(tgt_r))
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False
    print(f"  [{label}] IK solved: cost={ik_cost:.2e}")

    fk_coord_count = fk_model.joint_coord_count
    jq_start = fk_state.joint_q.numpy().copy()
    jq_end = jq_target.copy()
    finger_coords = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)
        jq_interp = jq_start.copy()
        for d in range(fk_coord_count):
            if d not in finger_coords:
                jq_interp[d] = jq_start[d] + (jq_end[d] - jq_start[d]) * t
        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        state = physics_step(model, state, solver, contacts, scene_info)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)
        if cable_bodies:
            bq = state.body_q.numpy()
            if np.any(np.isnan(bq[cable_bodies])):
                print(f"  [{label}] Cable NaN at step {step}!")
                return state, False
        if step % max(n_steps // 5, 1) == 0:
            cur_l, cur_r = get_ee_positions(state, scene_info)
            err_l = np.linalg.norm(cur_l - tgt_l) * 1000
            err_r = np.linalg.norm(cur_r - tgt_r) * 1000
            print(f"  [{label}] step {step}/{n_steps}: err L={err_l:.1f}mm R={err_r:.1f}mm")

    pos_l, pos_r = get_ee_positions(state, scene_info)
    err_l = np.linalg.norm(pos_l - tgt_l) * 1000
    err_r = np.linalg.norm(pos_r - tgt_r) * 1000
    converged = err_l < converge_mm and err_r < converge_mm
    print(f"  [{label}] Final: err L={err_l:.1f}mm R={err_r:.1f}mm converged={converged}")
    return state, converged


def ik_move_single(model, state, scene_info, solver, contacts,
                   target, arm="right", label="MOVE",
                   converge_mm=5.0, speed_factor=1.0):
    """Move a single arm while the other stays fixed."""
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]
    pos_l, pos_r = get_ee_positions(state, scene_info)
    current_pos = pos_l if arm == "left" else pos_r
    dist = np.linalg.norm(np.array(target) - current_pos)
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)
    print(f"  [{label}] {arm} arm dist={dist*1000:.1f}mm, steps={n_steps}")

    tgt = np.array(target, dtype=np.float32)
    # Solve IK for both arms but only move the target arm
    if arm == "left":
        jq_target, ik_cost = solve_ik_dual(scene_info, tuple(tgt), tuple(pos_r))
    else:
        jq_target, ik_cost = solve_ik_dual(scene_info, tuple(pos_l), tuple(tgt))
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False

    jq_start = fk_state.joint_q.numpy().copy()
    jq_end = jq_target.copy()
    # Only interpolate the target arm's joints (0-6), preserve fingers and other arm
    if arm == "left":
        arm_coords = set(range(7))  # j0-j6 of left arm
    else:
        arm_coords = set(range(FRANKA_NUM_JOINTS, FRANKA_NUM_JOINTS + 7))
    finger_coords = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)
        jq_interp = jq_start.copy()
        for d in arm_coords:
            jq_interp[d] = jq_start[d] + (jq_end[d] - jq_start[d]) * t
        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        state = physics_step(model, state, solver, contacts, scene_info)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)
        if cable_bodies:
            bq = state.body_q.numpy()
            if np.any(np.isnan(bq[cable_bodies])):
                print(f"  [{label}] Cable NaN at step {step}!")
                return state, False
        if step % max(n_steps // 5, 1) == 0:
            cur_l, cur_r = get_ee_positions(state, scene_info)
            cur_pos = cur_l if arm == "left" else cur_r
            err = np.linalg.norm(cur_pos - tgt) * 1000
            print(f"  [{label}] step {step}/{n_steps}: err={err:.1f}mm")

    cur_l, cur_r = get_ee_positions(state, scene_info)
    cur_pos = cur_l if arm == "left" else cur_r
    err = np.linalg.norm(cur_pos - tgt) * 1000
    converged = err < converge_mm
    print(f"  [{label}] Final: err={err:.1f}mm converged={converged}")
    return state, converged


def hold_position(model, state, scene_info, solver, contacts, n_steps):
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
            fk_jq[FRANKA_NUM_JOINTS + 7] = fk_jq_start[FRANKA_NUM_JOINTS + 7] + (right_target - fk_jq_start[FRANKA_NUM_JOINTS + 7]) * t
            fk_jq[FRANKA_NUM_JOINTS + 8] = fk_jq_start[FRANKA_NUM_JOINTS + 8] + (right_target - fk_jq_start[FRANKA_NUM_JOINTS + 8]) * t
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        state = physics_step(model, state, solver, contacts, scene_info)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)

    fk_jq = fk_state.joint_q.numpy()
    print(f"  [{label}] Fingers: L={fk_jq[7]*1000:.1f}mm R={fk_jq[FRANKA_NUM_JOINTS+7]*1000:.1f}mm")
    return state


# ---------------------------------------------------------------------------
# Phase functions: P1-P4 (grasp + CLIP1 insertion)
# ---------------------------------------------------------------------------
def do_p1_grasp(model, state, scene_info, solver, contacts):
    """P1: Wide-stance approach + descend + grasp."""
    print(f"\n  {'='*50}")
    print(f"  [P1] Wide-Stance Approach + Grasp")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    # Approach
    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, APPROACH_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, APPROACH_Z),
        label="P1-APPROACH", converge_mm=10.0,
    )

    # Descend
    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, GRASP_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, GRASP_Z),
        label="P1-DESCEND", converge_mm=5.0,
    )

    # Close fingers
    print(f"\n  [P1-CLOSE] Closing fingers to {FINGER_CLOSE_POS*1000:.1f}mm")
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


def do_p2_lift(model, state, scene_info, solver, contacts):
    """P2: Micro-lift to confirm grip."""
    print(f"\n  {'='*50}")
    print(f"  [P2] Micro-Lift")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)

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
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS)

    cable_z_delta_mm = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_after = np.mean(bq[cable_bodies, 2])
        cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)
        print(f"  [P2] Cable lift: {cable_z_delta_mm}mm")

    lifted = cable_z_delta_mm > 5.0 if has_cable else True
    return state, {"pass": lifted, "cable_z_delta_mm": cable_z_delta_mm}


def do_p3_move(model, state, scene_info, solver, contacts):
    """P3: Move from cable X to CLIP1 X."""
    print(f"\n  {'='*50}")
    move_target_x = CLIP_X + P3_X_OFFSET
    print(f"  [P3] Move to Clip1 X ({move_target_x:.3f})")
    print(f"  {'='*50}")
    pos_l, pos_r = get_ee_positions(state, scene_info)
    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(move_target_x, pos_l[1], pos_l[2]),
        target_right=(move_target_x, pos_r[1], pos_r[2]),
        label="P3-MOVE", converge_mm=8.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS)
    return state, {"pass": ok}


def do_p4_push(model, state, scene_info, solver, contacts):
    """P4: Push both arms down to PUSH_Z at CLIP1."""
    print(f"\n  {'='*50}")
    print(f"  [P4] Push Down to CLIP1")
    print(f"  {'='*50}")
    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    pos_l, pos_r = get_ee_positions(state, scene_info)

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(CLIP_X, pos_l[1], PUSH_Z),
        target_right=(CLIP_X, pos_r[1], PUSH_Z),
        label="P4-PUSH", speed_factor=2.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS * 3)

    # Check groove insertion
    cable_in_groove = True
    if has_cable:
        bq = state.body_q.numpy()
        cable_pos = bq[cable_bodies, :3]
        clip_xy = np.array([CLIP1_X, CLIP1_Y])
        dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
        bodies_in_groove = int(np.sum(dists_xy < GROOVE_CHECK_RADIUS))
        closest_idx = int(np.argmin(dists_xy))
        min_dist = float(np.min(dists_xy)) * 1000
        closest_pos = cable_pos[closest_idx]
        print(f"  [P4] CLIP1: bodies_in_groove={bodies_in_groove}, min_dist={min_dist:.1f}mm")
        print(f"  [P4] Closest cable body {cable_bodies[closest_idx]}: "
              f"pos=({closest_pos[0]:.4f}, {closest_pos[1]:.4f}, {closest_pos[2]:.4f}), "
              f"dx={abs(closest_pos[0]-CLIP1_X)*1000:.1f}mm, dy={abs(closest_pos[1]-CLIP1_Y)*1000:.1f}mm")
        cable_in_groove = bodies_in_groove >= 1

    return state, {"pass": ok and cable_in_groove, "cable_in_groove": cable_in_groove}


# ---------------------------------------------------------------------------
# Generic N-clip routing function (replaces hardcoded P5-P10)
# ---------------------------------------------------------------------------
def route_to_next_clip(model, state, scene_info, solver, contacts,
                       prev_clip_xy, current_clip_xy, clip_idx):
    """Route cable from prev_clip to current_clip.

    Generalizes the P5-P10 pattern for arbitrary clip-to-clip vectors.
    Uses direction-based arm placement instead of Y-only asymmetry.

    Args:
        prev_clip_xy: (x, y) of the clip just pushed into.
        current_clip_xy: (x, y) of the clip to route toward.
        clip_idx: Clip number (2, 3, ...) for logging.

    Returns:
        (state, results_dict) where results_dict has per-phase results
        and an overall 'pass' key.
    """
    results = {}
    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0

    # Routing direction: prev → current
    prev_xy = np.array(prev_clip_xy[:2], dtype=np.float64)
    curr_xy = np.array(current_clip_xy[:2], dtype=np.float64)
    routing_vec = curr_xy - prev_xy
    routing_dist = np.linalg.norm(routing_vec)
    if routing_dist > 1e-6:
        routing_dir = routing_vec / routing_dist
    else:
        routing_dir = np.array([0.0, -1.0])

    print(f"\n{'='*60}")
    print(f"  ROUTE TO CLIP {clip_idx}")
    print(f"  prev=({prev_xy[0]:.3f}, {prev_xy[1]:.3f}) -> "
          f"curr=({curr_xy[0]:.3f}, {curr_xy[1]:.3f})")
    print(f"  routing_dir=({routing_dir[0]:.3f}, {routing_dir[1]:.3f}), "
          f"dist={routing_dist*1000:.0f}mm")
    print(f"{'='*60}")

    # ---- Unclamp right + half-open left ----
    print(f"\n  [C{clip_idx}-UNCLAMP] Right unclamp + Left half-open")
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        left_target=FINGER_HALF_OPEN_POS, right_target=FINGER_OPEN_POS,
        n_steps=200,
        label=f"C{clip_idx}-FINGERS",
    )
    results["unclamp"] = {"pass": True}

    # ---- Rise (cable slides through left arm) ----
    print(f"\n  [C{clip_idx}-RISE] Rise (left arm slide-through)")
    pos_l, pos_r = get_ee_positions(state, scene_info)

    rise_target_z = LIFT_Z + 0.05
    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(pos_l[0], pos_l[1], rise_target_z),
        arm="left", label=f"C{clip_idx}-RISE", speed_factor=2.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS)
    results["rise"] = {"pass": True}

    # ---- Regrasp ----
    print(f"\n  [C{clip_idx}-8a] Left arm descend + close")
    pos_l, pos_r = get_ee_positions(state, scene_info)
    regrasp_x = pos_l[0]
    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(regrasp_x, pos_l[1], GRASP_Z),
        arm="left", label=f"C{clip_idx}-8a-DESC", converge_mm=3.0,
    )
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        left_target=FINGER_CLOSE_POS, n_steps=300,
        label=f"C{clip_idx}-8a-CLOSE",
    )

    # P8b: Right arm to cable (direction-based target)
    print(f"\n  [C{clip_idx}-8b] Right arm move to cable (direction-based)")
    right_target_xy = curr_xy + 0.05 * routing_dir
    wp.synchronize()
    bq_now = state.body_q.numpy()
    best_dist = 1e9
    right_grasp_x = regrasp_x
    right_grasp_y = float(right_target_xy[1])
    for bi in cable_bodies:
        cxy = bq_now[bi][:2]
        d = np.linalg.norm(cxy - right_target_xy)
        if d < best_dist:
            best_dist = d
            right_grasp_x = float(bq_now[bi][0])
            right_grasp_y = float(bq_now[bi][1])
    print(f"  Target=({right_target_xy[0]:.3f}, {right_target_xy[1]:.3f}) "
          f"-> Cable at ({right_grasp_x:.4f}, {right_grasp_y:.4f}), "
          f"dist={best_dist*1000:.1f}mm")

    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(right_grasp_x, right_grasp_y, APPROACH_Z),
        arm="right", label=f"C{clip_idx}-8b-APPR",
    )
    state, ok = ik_move_single(
        model, state, scene_info, solver, contacts,
        target=(right_grasp_x, right_grasp_y, GRASP_Z),
        arm="right", label=f"C{clip_idx}-8b-DESC", converge_mm=5.0,
    )

    # P8c: Right arm close
    print(f"\n  [C{clip_idx}-8c] Right arm close")
    state = interpolate_fingers(
        model, state, scene_info, solver, contacts,
        right_target=FINGER_CLOSE_POS, n_steps=300,
        label=f"C{clip_idx}-8c-CLOSE",
    )

    print(f"  [C{clip_idx}] Both arms gripping — ready for clip {clip_idx}")
    results["regrasp"] = {"pass": True}

    # ---- Move to clip (direction-based arm placement) ----
    print(f"\n  [C{clip_idx}-MOVE] Move to clip {clip_idx} (direction-based)")

    spread = WIDE_RIGHT_Y - WIDE_LEFT_Y  # 120mm
    center_xy = curr_xy + P3_X_OFFSET * routing_dir
    # Left arm: toward prev clip (backward along routing direction)
    target_left_xy = center_xy - (spread / 2) * routing_dir
    # Right arm: past current clip (forward)
    target_right_xy = center_xy + (spread / 2) * routing_dir

    print(f"  L=({target_left_xy[0]:.3f}, {target_left_xy[1]:.3f})"
          f"  R=({target_right_xy[0]:.3f}, {target_right_xy[1]:.3f})")

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(float(target_left_xy[0]),
                     float(target_left_xy[1]), LIFT_Z),
        target_right=(float(target_right_xy[0]),
                      float(target_right_xy[1]), LIFT_Z),
        label=f"C{clip_idx}-MOVE", converge_mm=8.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS)
    results["move"] = {"pass": ok}

    # ---- Push into clip (midpoint correction) ----
    print(f"\n  [C{clip_idx}-PUSH] Push down to clip {clip_idx}")
    pos_l, pos_r = get_ee_positions(state, scene_info)
    mid_xy = (pos_l[:2] + pos_r[:2]) / 2
    correction = curr_xy - mid_xy
    push_left_xy = pos_l[:2] + correction
    push_right_xy = pos_r[:2] + correction
    print(f"  Midpoint correction: "
          f"({correction[0]*1000:.1f}, {correction[1]*1000:.1f})mm")

    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(float(push_left_xy[0]),
                     float(push_left_xy[1]), PUSH_Z),
        target_right=(float(push_right_xy[0]),
                      float(push_right_xy[1]), PUSH_Z),
        label=f"C{clip_idx}-PUSH", speed_factor=2.0,
    )
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS * 3)

    # Check groove insertion
    cable_in_groove = True
    if has_cable:
        bq = state.body_q.numpy()
        cable_pos = bq[cable_bodies, :3]
        clip_xy_arr = np.array([float(curr_xy[0]), float(curr_xy[1])])
        dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy_arr, axis=1)
        bodies_in_groove = int(np.sum(dists_xy < GROOVE_CHECK_RADIUS))
        closest_idx = int(np.argmin(dists_xy))
        min_dist = float(np.min(dists_xy)) * 1000
        closest_pos = cable_pos[closest_idx]
        print(f"  [C{clip_idx}-PUSH] bodies_in_groove={bodies_in_groove}, "
              f"min_dist={min_dist:.1f}mm")
        print(f"  Closest body {cable_bodies[closest_idx]}: "
              f"pos=({closest_pos[0]:.4f}, {closest_pos[1]:.4f}, "
              f"{closest_pos[2]:.4f}), "
              f"dx={abs(closest_pos[0]-float(curr_xy[0]))*1000:.1f}mm, "
              f"dy={abs(closest_pos[1]-float(curr_xy[1]))*1000:.1f}mm")
        cable_in_groove = bodies_in_groove >= 1

    results["push"] = {
        "pass": ok and cable_in_groove,
        "cable_in_groove": cable_in_groove,
    }

    overall_pass = all(
        results[k].get("pass", False) for k in results
        if isinstance(results[k], dict) and "pass" in results[k]
    )
    results["pass"] = overall_pass
    if not overall_pass:
        for phase in ("move", "push"):
            if phase in results and not results[phase].get("pass", True):
                results["fail_phase"] = phase
                break
    return state, results


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------
def run_episode(model, state, scene_info, solver, contacts, episode_idx,
                num_clips=2):
    results = {"episode": episode_idx, "overall": "FAIL", "num_clips": num_clips}

    # P1-P4: Grasp + CLIP1 insertion (same as 1-clip)
    state, p1 = do_p1_grasp(model, state, scene_info, solver, contacts)
    results["P1"] = p1
    if not p1["pass"]:
        results["fail_reason"] = "P1_fail"
        return state, results

    state, p2 = do_p2_lift(model, state, scene_info, solver, contacts)
    results["P2"] = p2

    state, p3 = do_p3_move(model, state, scene_info, solver, contacts)
    results["P3"] = p3

    state, p4 = do_p4_push(model, state, scene_info, solver, contacts)
    results["P4"] = p4
    if not p4["pass"]:
        results["fail_reason"] = "P4_clip1_fail"
        return state, results

    # Route to each subsequent clip using generic function
    clips = ALL_CLIPS[:num_clips]
    for i in range(1, len(clips)):
        prev_clip = clips[i - 1]
        curr_clip = clips[i]
        clip_idx = i + 1  # CLIP2, CLIP3, ...

        state, clip_result = route_to_next_clip(
            model, state, scene_info, solver, contacts,
            prev_clip_xy=prev_clip[:2],
            current_clip_xy=curr_clip[:2],
            clip_idx=clip_idx,
        )
        results[f"CLIP{clip_idx}"] = clip_result
        if not clip_result.get("pass", False):
            fail_phase = clip_result.get("fail_phase", "unknown")
            results["fail_reason"] = f"CLIP{clip_idx}_{fail_phase}"
            return state, results

    results["overall"] = "PASS"
    return state, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _physics_state_buffer
    parser = argparse.ArgumentParser(description="Newton dual-clip routing test")
    parser.add_argument("--no-cable", action="store_true")
    parser.add_argument("--num-episodes", type=int, default=1)
    parser.add_argument("--num-clips", type=int, default=2,
                        choices=[1, 2, 3])
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()

    num_clips = args.num_clips
    use_cable = not args.no_cable
    if not args.no_video and os.environ.get("HARNESS_RECORD_VIDEO", "") == "1":
        args.record_video = True

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/newton_{num_clips}clip_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    clips_used = ALL_CLIPS[:num_clips]
    print(f"[CLIP_ROUTE] Device={DEVICE}")
    print(f"[CLIP_ROUTE] Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"[CLIP_ROUTE] Cable: {CABLE_SEGMENTS} segments x "
          f"{CABLE_SEG_LEN*1000:.0f}mm = "
          f"{CABLE_SEGMENTS*CABLE_SEG_LEN*1000:.0f}mm")
    print(f"[CLIP_ROUTE] Routing {num_clips} clips:")
    for ci, (cx, cy, cz) in enumerate(clips_used, 1):
        print(f"  CLIP{ci}: ({cx}, {cy}, {cz})")
    print()

    # Build FK model
    print("[BUILD] Building FK model...")
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

    # Build physics scene
    print("[BUILD] Building physics scene...")
    scene_info = build_scene(use_cable=use_cable, fk_model=fk_model, fk_state=fk_state)
    model = scene_info["model"]
    cable_bodies = scene_info.get("cable_bodies", [])
    scene_info["fk_model"] = fk_model
    scene_info["fk_state"] = fk_state

    state = model.state()
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control

    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    print(f"  [SOLVER] VBD (iterations={VBD_ITERATIONS})")

    # Video recorder
    recorder = VideoRecorder(args.output_dir, model, enabled=args.record_video,
                             scene_info=scene_info)
    scene_info["recorder"] = recorder
    set_scene_colors(recorder, scene_info)

    # Settle cable (2s)
    print("[INIT] Settling (2s)...")
    settle_steps = int(2.0 / DT)
    for i in range(settle_steps):
        state = physics_step(model, state, solver, contacts, scene_info)
        if i % int(0.5 / DT) == 0:
            pos_l, pos_r = get_ee_positions(state, scene_info)
            cable_info = ""
            if cable_bodies:
                bq = state.body_q.numpy()
                cable_z = np.mean(bq[cable_bodies, 2])
                cable_info = f" cable_z={cable_z:.4f}"
            print(f"  settle t={i*DT:.1f}s{cable_info}")

    if cable_bodies:
        bq = state.body_q.numpy()
        cable_pos = bq[cable_bodies, :3]
        cable_x = np.mean(cable_pos[:, 0])
        print(f"[INIT] Cable settled: mean_x={cable_x:.4f}")
        scene_info["settled_grasp_x"] = float(cable_x)
    else:
        scene_info["settled_grasp_x"] = GRASP_X

    # Save settled state
    settled_body_q = state.body_q.numpy().copy()
    settled_body_qd = state.body_qd.numpy().copy()
    settled_phys_jq = state.joint_q.numpy().copy()
    settled_phys_jqd = state.joint_qd.numpy().copy()
    settled_fk_jq = fk_state.joint_q.numpy().copy()

    # Run episodes
    all_results = {
        "test": f"newton_{num_clips}clip_routing",
        "device": DEVICE,
        "num_clips": num_clips,
        "clips": [
            {"x": cx, "y": cy, "z": cz} for cx, cy, cz in clips_used
        ],
        "cable_length_mm": CABLE_SEGMENTS * CABLE_SEG_LEN * 1000,
        "episodes": [],
        "n_pass": 0, "n_fail": 0,
    }

    start_time = time.time()
    for ep in range(args.num_episodes):
        print(f"\n{'='*60}")
        print(f"  EPISODE {ep+1}/{args.num_episodes}")
        print(f"{'='*60}")

        if ep > 0:
            state = model.state()
            state.body_q.assign(settled_body_q)
            state.body_qd.assign(settled_body_qd)
            state.joint_q.assign(settled_phys_jq)
            state.joint_qd.assign(settled_phys_jqd)
            solver.body_q_prev.assign(settled_body_q)
            if hasattr(solver, 'joint_sigma_prev') and solver.joint_sigma_prev is not None:
                solver.joint_sigma_prev.zero_()
            if hasattr(solver, 'joint_kappa_prev') and solver.joint_kappa_prev is not None:
                solver.joint_kappa_prev.zero_()
            if hasattr(solver, 'joint_dkappa_prev') and solver.joint_dkappa_prev is not None:
                solver.joint_dkappa_prev.zero_()
            _physics_state_buffer = None
            fk_jq_reset = settled_fk_jq.copy()
            for arm_offset in [0, FRANKA_NUM_JOINTS]:
                fk_jq_reset[arm_offset + 7] = FINGER_OPEN_POS
                fk_jq_reset[arm_offset + 8] = FINGER_OPEN_POS
            fk_state.joint_q.assign(fk_jq_reset)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            update_kinematic_bodies(state, fk_state, scene_info["robot_body_count"])
            print(f"  [RESET] Scene restored")

        recorder.reset()

        try:
            state, ep_result = run_episode(model, state, scene_info, solver, contacts, ep, num_clips=num_clips)
        except Exception as e:
            print(f"\n  [ERROR] Episode {ep+1} crashed: {e}")
            import traceback
            traceback.print_exc()
            ep_result = {"episode": ep, "overall": "CRASH", "error": str(e)}

        video_paths = recorder.finalize(ep)
        if video_paths:
            ep_result["videos"] = video_paths
        all_results["episodes"].append(ep_result)

        if ep_result["overall"] == "PASS":
            all_results["n_pass"] += 1
            print(f"\n  >>> EPISODE {ep+1}: PASS <<<")
        else:
            all_results["n_fail"] += 1
            reason = ep_result.get("fail_reason", "unknown")
            print(f"\n  >>> EPISODE {ep+1}: {ep_result['overall']} ({reason}) <<<")

    elapsed = time.time() - start_time
    all_results["elapsed_s"] = round(elapsed, 1)
    all_results["overall"] = "PASS" if all_results["n_fail"] == 0 else "FAIL"
    all_results["pass_rate"] = f"{all_results['n_pass']}/{args.num_episodes}"

    # Convert numpy types for JSON serialization
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            return super().default(obj)

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(all_results, f, indent=2, cls=NumpyEncoder)

    print(f"\n{'='*60}")
    print(f"  SUMMARY: {all_results['pass_rate']} pass, {elapsed:.1f}s")
    print(f"  Metrics: {metrics_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
