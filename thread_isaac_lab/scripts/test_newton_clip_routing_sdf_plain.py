"""Newton Phase 8: Franka Dual-Arm Cable Clip Routing (1 Clip)

Ports test_clip_routing.py (PhysX/Isaac Sim 5.1) to Newton.
Architecture: Single MuJoCo solver with BALL joint cable + CollisionPipeline (plain SDF).
Cable = capsule rigid bodies connected by BALL joints (bend stiffness via PD gains).
MuJoCo handles ALL dynamics: robot PD control (REVOLUTE/PRISMATIC) + cable (FREE/BALL).
Contacts: CollisionPipeline with SDF narrowphase for MESH shapes (pattern: example_nut_bolt_sdf.py).
IK: Newton IKSolver (Levenberg-Marquardt) for Cartesian EE control.

Phase structure:
  P1: Wide-stance approach + grasp (IK approach → descend → finger close)
  P2: Micro-lift (grip confirmation via cable z-delta)
  P3: Move to clip X position (GRASP_X → CLIP_X)
  P4: Push down into clip (descend to PUSH_Z)

Coordinate system (matches PhysX version):
  Robot bases elevated at TABLE_HEIGHT (0.80m), facing +X.
  Cable along Y axis at table surface height.
  Clip at (CLIP_X, CLIP_Y, TABLE_HEIGHT).

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_clip_routing.py
    # With cable removed (IK-only test):
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_clip_routing.py --no-cable
"""

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverMuJoCo
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation
from newton.viewer import ViewerGL
# SensorRaycast removed: OpenGL(ViewerGL) + CUDA(Raycast) context conflict causes hang.
# Depth overlay now generated post-hoc from z-height ground truth in preprocessor.

# Import tunable parameters from task_config (SSOT for Code A harness)
# THREAD_CONFIG_DIR env var allows per-GPU config isolation in dual harness
_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    TABLE_HEIGHT, ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE,
    EE_TO_FINGERTIP, APPROACH_Z, GRASP_Z, LIFT_Z, PUSH_Z,
    MUJOCO_ITERATIONS, MUJOCO_LS_ITERATIONS, DISABLE_CONTACTS, NJMAX,
    ARM_KE, ARM_KD, FINGER_KE, FINGER_KD,
    CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    CABLE_BEND_STIFFNESS, CABLE_BEND_DAMPING,
    CABLE_STRETCH_STIFFNESS, CABLE_STRETCH_DAMPING,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
    GRASP_X, CLIP_X, CLIP_GROOVE_INNER_RADIUS, P3_X_OFFSET, WIDE_LEFT_Y, WIDE_RIGHT_Y,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_CLOSE_STEPS,
    STEPS_PER_CM, CONVERGE_MM, MAX_MOVE_STEPS, SETTLE_STEPS,
)

# ---------------------------------------------------------------------------
# Constants (non-tunable)
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0
GRAVITY = -9.81

# Clip position — from task_config SSOT
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z

# Franka
FRANKA_URDF = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "source", "extensions", "isaaclab_tasks_thread", "data", "robots",
    "panda_independent_fingers.urdf",
))
FRANKA_NUM_JOINTS = 9
# Body indices in the model (per arm, relative to arm's first body)
# Body 6 = panda_hand (flange), Body 7/8 = finger links
EE_BODY_OFFSET = 6  # panda_hand relative to arm start

# IK
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0

# CollisionPipeline (set in main() — replaces model.collide for MESH-CAPSULE contacts)
_collision_pipeline = None

# (Motion & Finger parameters imported from task_config)

# Video — per-camera MP4 (matches PhysX test_clip_routing.py camera positions)
VIDEO_FPS = 30
VIDEO_CAPTURE_EVERY = 16  # Capture every N physics steps (480/16=30fps)
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960

# Camera definitions: (name, position, target)
# v3.1: clip_close lowered to groove-level profile, diag_upper shifted +Y to reduce R-arm occlusion
CAMERAS = [
    ("overhead",    (0.35, -0.05, 1.50), (0.35, -0.05, 0.80)),  # top-down: XY overview
    ("front",       (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),  # +X→-X: Z-height, table penetration
    ("diag_upper",  (0.65, -0.40, 1.00), (0.35, -0.05, 0.82)),  # 45° upper: shifted +Y to reduce R-arm occlusion
    ("left",        (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),  # -Y→+Y: closer & lower (table+13cm)
    ("right",       (0.35,  0.55, 0.93), (0.35, -0.05, 0.82)),  # +Y→-Y: closer & lower (table+13cm)
    ("clip_close",  (0.50, -0.05, 0.83), (0.35, -0.05, 0.82)),  # groove-level profile: horizontal view of groove insertion
]

import math as _math


def _cam_angles(pos, tgt):
    """Compute (pitch_deg, yaw_deg) for ViewerGL.set_camera from pos→target."""
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = _math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = _math.degrees(_math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = _math.degrees(_math.atan2(dy, dx))
    return pitch, yaw


# ---------------------------------------------------------------------------
# Video recorder — per-camera MP4 (5 separate files)
# ---------------------------------------------------------------------------
class VideoRecorder:
    """Records per-camera MP4 videos from Newton ViewerGL headless.

    Generates 5 separate MP4 files, one per camera (640×480 each).
    Matches PhysX FrameRecorder output format for /video-analyzer compatibility.
    Also records per-frame z-heights for computational pre-checks (Code C).
    """

    def __init__(self, output_dir, model, enabled=False, scene_info=None):
        self.enabled = enabled
        self.output_dir = output_dir
        self.viewer = None
        self.step_count = 0
        self.sim_time = 0.0
        # Per-camera frame buffers: {name: [np.array, ...]}
        self._cam_frames = {}
        self._cam_params = []
        # Z-height ground truth for Code C computational pre-checks
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
        # Rod cable uses rigid body capsules (no particles to show)
        for name, pos, tgt in CAMERAS:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cam_params.append((name, wp.vec3(*pos), pitch, yaw))
            self._cam_frames[name] = []
        print(f"  [VIDEO] Per-camera recorder initialized "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {len(CAMERAS)} cameras)")

    def capture(self, state):
        """Capture one frame per camera + z-height ground truth (call every physics step)."""
        if not self.enabled or self.viewer is None:
            return
        self.step_count += 1
        self.sim_time += DT
        if self.step_count % VIDEO_CAPTURE_EVERY != 0:
            return
        # RGB capture
        for name, pos, pitch, yaw in self._cam_params:
            self.viewer.set_camera(pos, pitch, yaw)
            self.viewer.begin_frame(self.sim_time)
            self.viewer.log_state(state)
            self.viewer.end_frame()
            frame = self.viewer.get_frame().numpy().copy()
            self._cam_frames[name].append(frame)
        # Z-height ground truth capture (no GPU contention — reads state only)
        self._capture_zheights(state)

    def _capture_zheights(self, state):
        """Record z-heights of finger/hand bodies and cable rod bodies."""
        si = self._scene_info
        if si is None:
            return
        body_q = state.body_q.numpy()
        cable_bodies = si.get("cable_bodies", [])
        frame_idx = len(self._zheight_frames)

        entry = {"idx": frame_idx}
        # Hand z (body offset 6 = panda_hand)
        for arm, label in [("left", "left"), ("right", "right")]:
            bs = si[f"{arm}_body_start"]
            entry[f"{label}_hand_z"] = float(body_q[bs + EE_BODY_OFFSET][2])
            # Finger z (body offset 7, 8 = left/right prismatic fingers)
            entry[f"{label}_finger_z"] = [
                float(body_q[bs + 7][2]),
                float(body_q[bs + 8][2]),
            ]

        # Cable body z-heights (rod capsules)
        if cable_bodies:
            cable_pos = body_q[cable_bodies, :3]
            cable_z = cable_pos[:, 2]
            entry["cable_z_min"] = float(np.min(cable_z))
            entry["cable_z_max"] = float(np.max(cable_z))
            entry["cable_z_mean"] = float(np.mean(cable_z))
            # Cable-clip XY distance
            clip_xy = np.array([CLIP1_X, CLIP1_Y])
            dists = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
            entry["cable_clip_dist_xy"] = float(np.min(dists))

        self._zheight_frames.append(entry)

    def finalize(self, episode_idx):
        """Encode per-camera frames to separate MP4 files + save z-heights."""
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
                self.output_dir,
                f"ep{episode_idx}_{name}.mp4")
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

        # Save z-height ground truth JSON
        self._save_zheights(episode_idx, n_frames)

        print(f"  [VIDEO] Saved {len(video_paths)} camera videos "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {n_frames} frames each)")
        for p in video_paths:
            print(f"    {p}")
        return video_paths

    def _save_zheights(self, episode_idx, n_frames):
        """Save z-height ground truth to JSON for Code C pre-checks."""
        if not self._zheight_frames:
            return
        # Add time percentage to each frame
        for i, entry in enumerate(self._zheight_frames):
            entry["pct"] = int(100 * i / max(n_frames - 1, 1))
        zheight_data = {
            "table_z": float(TABLE_HEIGHT),
            "clip_pos": [float(CLIP1_X), float(CLIP1_Y)],
            "clip_groove_inner_radius_m": CLIP_GROOVE_INNER_RADIUS,
            "n_frames": n_frames,
            "frames": self._zheight_frames,
        }
        path = os.path.join(self.output_dir, f"ep{episode_idx}_zheights.json")
        with open(path, "w") as f:
            json.dump(zheight_data, f, indent=2)
        print(f"  [VIDEO] Z-heights saved: {path} ({len(self._zheight_frames)} frames)")

    def reset(self):
        """Reset for next episode."""
        for name in self._cam_frames:
            self._cam_frames[name] = []
        self._zheight_frames = []
        self.step_count = 0
        self.sim_time = 0.0


# ---------------------------------------------------------------------------
# Scene colors — visual distinction for multimodal video analysis
# ---------------------------------------------------------------------------
COLOR_FINGER = (1.0, 0.2, 0.2)    # RED — highest priority for table-penetration detection
COLOR_TABLE  = (0.65, 0.50, 0.35)  # TAN/BROWN — distinct from white/gray defaults
COLOR_HAND   = (0.3, 0.3, 0.6)    # BLUE-GRAY — distinguish hand body from fingers
COLOR_CLIP   = (0.2, 0.7, 0.3)    # GREEN — clip V-groove


def set_scene_colors(recorder, scene_info):
    """Set per-shape colors so fingers/table/clip are visually distinct in video.

    Uses model.body_label + model.shape_body to map robot body names to shape
    indices.  Table and clip use explicit indices tracked in build_scene().
    """
    if not recorder.enabled or recorder.viewer is None:
        return
    model = scene_info["model"]
    shape_colors = {}

    # Robot shapes: identify via body_label → shape_body mapping
    shape_body = model.shape_body.numpy()
    for s_idx in range(len(shape_body)):
        body_idx = int(shape_body[s_idx])
        if body_idx < 0:
            continue  # world-attached (table, clip) — handled below
        body_name = model.body_label[body_idx].lower()
        if "finger" in body_name:
            shape_colors[s_idx] = COLOR_FINGER
        elif "hand" in body_name:
            shape_colors[s_idx] = COLOR_HAND

    # Table (world-attached, explicit index from build_scene)
    table_idx = scene_info.get("table_shape_idx")
    if table_idx is not None:
        shape_colors[table_idx] = COLOR_TABLE

    # Clip V-groove parts (world-attached, explicit indices)
    for clip_idx in scene_info.get("clip_shape_indices", []):
        shape_colors[clip_idx] = COLOR_CLIP

    if shape_colors:
        recorder.viewer.update_shape_colors(shape_colors)
        n_finger = sum(1 for c in shape_colors.values() if c == COLOR_FINGER)
        n_hand = sum(1 for c in shape_colors.values() if c == COLOR_HAND)
        print(f"  [VIDEO] Scene colors: {n_finger} finger(red), {n_hand} hand(blue-gray), "
              f"1 table(tan), {len(scene_info.get('clip_shape_indices', []))} clip(green)")


# ---------------------------------------------------------------------------
# Scene builder
# ---------------------------------------------------------------------------
def add_franka_arm(builder, pos, arm_ke=ARM_KE, arm_kd=ARM_KD,
                   finger_ke=FINGER_KE, finger_kd=FINGER_KD):
    """Add a Franka Panda arm to the builder.

    Returns (j_start, j_end, body_start, shape_start, shape_end).
    Uses joint_target_ke indexing — works because all Franka joints are 1-DOF.
    """
    body_start = len(builder.body_mass)
    j_start = len(builder.joint_target_ke)
    shape_start = builder.shape_count
    # Set shape config for URDF import: gap for early contact detection.
    # Finger shapes get SDF built explicitly in build_scene() after import.
    prev_cfg = builder.default_shape_cfg
    urdf_cfg = newton.ModelBuilder.ShapeConfig()
    urdf_cfg.gap = 0.005            # 5mm contact gap
    builder.default_shape_cfg = urdf_cfg
    builder.add_urdf(
        FRANKA_URDF,
        xform=wp.transform(pos, wp.quat_identity()),
        floating=False,
        enable_self_collisions=False,
        collapse_fixed_joints=True,
    )
    builder.default_shape_cfg = prev_cfg  # restore
    j_end = len(builder.joint_target_ke)
    shape_end = builder.shape_count
    for i in range(j_start, j_end):
        jt = builder.joint_type[i]
        if jt == newton.JointType.REVOLUTE:
            builder.joint_target_ke[i] = arm_ke
            builder.joint_target_kd[i] = arm_kd
        elif jt == newton.JointType.PRISMATIC:
            builder.joint_target_ke[i] = finger_ke
            builder.joint_target_kd[i] = finger_kd
            # Finger joint limits: allow negative (finger-to-finger compression)
            # Lower limit at -0.025 so PD target of -0.02 doesn't fight limit force.
            # Without this, fingers at -10mm generate 105N opening from limit ke=1e4.
            builder.joint_limit_lower[i] = -0.025
            builder.joint_limit_upper[i] = 0.04
            builder.joint_limit_ke[i] = 1e4
            builder.joint_limit_kd[i] = 1e2
        builder.joint_target_mode[i] = newton.JointTargetMode.POSITION_VELOCITY.value

    return j_start, j_end, body_start, shape_start, shape_end


def add_cable(builder, start_pos, direction=(0, 1, 0)):
    """Add cable as capsule bodies + BALL joints (MuJoCo-compatible).

    Replicates add_rod() geometry but uses BALL joints instead of CABLE joints,
    allowing a single MuJoCo solver to handle both robot and cable dynamics.
    Bend stiffness is approximated via BALL joint PD gains (ke = EI / L).
    Stretch constraint is implicit in the BALL joint positional constraint.

    Returns (body_indices, joint_indices).
    """
    total_length = CABLE_SEGMENTS * CABLE_SEG_LEN
    seg_length = CABLE_SEG_LEN
    half_height = 0.5 * seg_length

    # Generate straight cable centerline points and per-segment quaternions
    dir_vec = wp.vec3(float(direction[0]), float(direction[1]), float(direction[2]))
    points, quats = newton.utils.create_straight_cable_points_and_quaternions(
        start=wp.vec3(start_pos[0], start_pos[1], start_pos[2]),
        direction=dir_vec,
        length=float(total_length),
        num_segments=int(CABLE_SEGMENTS),
    )

    # Cable contact config — plain SDF pattern (no hydroelastic)
    # Pattern: example_nut_bolt_sdf.py — is_hydroelastic=False
    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = CABLE_CONTACT_KE
    cable_cfg.kd = CABLE_CONTACT_KD
    cable_cfg.mu = CABLE_CONTACT_MU
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.005                 # 5mm contact gap for early detection
    cable_cfg.density = 5000.0  # 5x water, ~5g/segment (realistic rubber/copper cable)

    body_ids = []
    joint_ids = []

    for i in range(CABLE_SEGMENTS):
        # Body at segment start position (same geometry as add_rod)
        body_pos = wp.vec3(float(points[i][0]), float(points[i][1]), float(points[i][2]))
        body_quat = quats[i] if quats else wp.quat_identity()
        body_xform = wp.transform(body_pos, body_quat)
        com = wp.vec3(0.0, 0.0, half_height)  # COM at segment midpoint

        # Armature adds virtual inertia to mass matrix diagonal.
        # Improves MuJoCo PGS conditioning for light bodies (mass ratio arm:cable ≈ 2600:1).
        # Without armature, contact forces on 5g cable bodies cause solver divergence.
        body_id = builder.add_link(
            xform=body_xform,
            com=com,
            armature=0.01,
            label=f"cable_{i}",
        )

        # Capsule shape: centered at midpoint, extends along +Z (same as add_rod)
        capsule_xf = wp.transform(wp.vec3(0.0, 0.0, half_height), wp.quat_identity())
        builder.add_shape_capsule(
            body=body_id,
            xform=capsule_xf,
            radius=CABLE_RADIUS,
            half_height=half_height,
            cfg=cable_cfg,
        )

        if i == 0:
            # First body: FREE joint to world (cable root, 6 DOF)
            # No PD gains — cable stays on table via gravity + friction contact.
            j_id = builder.add_joint_free(
                child=body_id,
                parent=-1,
            )
        else:
            # Connect to previous body with BALL joint (3 rotational DOF)
            # Parent anchor at end of parent capsule, child anchor at start of child
            # Light bend stiffness: ke=10 with armature=0.01 gives ke*dt²/I_eff = 0.004 < 1.
            # Prevents loose-chain behavior (cable drifting sideways during finger close)
            # while remaining stable. Much lower than task_config CABLE_BEND_STIFFNESS=3.0
            # (which was for VBD solver with different dynamics).
            parent_xf = wp.transform(wp.vec3(0.0, 0.0, seg_length), wp.quat_identity())
            child_xf = wp.transform(wp.vec3(0.0, 0.0, 0.0), wp.quat_identity())
            j_id = builder.add_joint_ball(
                parent=body_ids[-1],
                child=body_id,
                parent_xform=parent_xf,
                child_xform=child_xf,
                armature=0.01,
                label=f"cable_joint_{i}",
            )
            # Set BALL joint PD for bend resistance
            # ke=50 with armature=0.01: ke*dt²/I_eff = 50*(1/480)²/0.01 = 0.022 < 1 ✅
            builder.joint_target_ke[j_id] = 50.0   # N·m/rad (moderate)
            builder.joint_target_kd[j_id] = 1.0    # N·m·s/rad (damped)

        body_ids.append(body_id)
        joint_ids.append(j_id)

    # Wrap cable bodies+joints into single articulation
    builder.add_articulation(joint_ids)

    body_mass = cable_cfg.density * (3.14159 * CABLE_RADIUS**2 * seg_length +
                                      4/3 * 3.14159 * CABLE_RADIUS**3)
    print(f"  [CABLE] {len(body_ids)} bodies, {len(joint_ids)} joints "
          f"(1 FREE + {len(joint_ids)-1} BALL), ke={50.0}, kd={1.0}, "
          f"density={cable_cfg.density:.0f}, body_mass={body_mass*1000:.1f}g, "
          f"sdf_res=64")

    return body_ids, joint_ids


def build_scene(use_cable=True):
    """Build the full Newton scene.

    Table = PLANE at TABLE_HEIGHT (pattern: example_nut_bolt_sdf.py).
    CollisionPipeline handles CAPSULE-PLANE (cable-table) and MESH-CAPSULE (finger-cable).
    """
    builder = newton.ModelBuilder(gravity=GRAVITY)

    # Table surface as PLANE at TABLE_HEIGHT (n·x + d = 0 → z = -d → d = -TABLE_HEIGHT)
    # Pattern: example_nut_bolt_sdf.py — PLANE shape, CollisionPipeline primitive narrowphase
    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 1e4     # Contact stiffness (rigid table)
    table_cfg.kd = 1e2     # Contact damping
    table_cfg.mu = 1.0     # High friction for cable traction
    table_cfg.gap = 0.005  # 5mm contact gap
    table_idx = builder.add_shape_plane(
        plane=(0.0, 0.0, 1.0, -TABLE_HEIGHT),
        width=0.0, length=0.0,
        cfg=table_cfg,
        label="table",
    )
    print(f"  [SCENE] Table PLANE at z={TABLE_HEIGHT}")

    # Clip V-groove (visual-only, built from boxes)
    # USD reference: routing_clip_v1.usd — base 40x30x5mm, walls at x=±9mm, V-tips at x=±13mm
    cx, cy, cz = CLIP1_X, CLIP1_Y, CLIP1_Z
    clip_parts = [
        # (dx, dy, dz, hx, hy, hz) — offset from clip base center
        (0, 0, 0.0025, 0.020, 0.015, 0.0025),        # Base plate
        (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),   # Left wall
        (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),   # Right wall
        (-0.013, 0, 0.025, 0.002, 0.015, 0.005),      # Left V-tip
        (+0.013, 0, 0.025, 0.002, 0.015, 0.005),      # Right V-tip
    ]
    clip_shape_indices = []
    for dx, dy, dz, hx, hy, hz in clip_parts:
        xf = wp.transform((cx + dx, cy + dy, cz + dz), wp.quat_identity())
        idx = builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz)
        builder.shape_flags[idx] = 1  # VISIBLE only
        clip_shape_indices.append(idx)
    print(f"  [SCENE] Clip V-groove at ({cx}, {cy}, {cz}), 5 parts")

    # Left arm
    left_j_start, left_j_end, left_body_start, left_shape_start, left_shape_end = add_franka_arm(builder, pos=ROBOT_LEFT_BASE)
    print(f"  [SCENE] Left arm: joints=[{left_j_start}:{left_j_end}], body_start={left_body_start}, shapes=[{left_shape_start}:{left_shape_end}]")

    # Right arm
    right_j_start, right_j_end, right_body_start, right_shape_start, right_shape_end = add_franka_arm(builder, pos=ROBOT_RIGHT_BASE)
    print(f"  [SCENE] Right arm: joints=[{right_j_start}:{right_j_end}], body_start={right_body_start}, shapes=[{right_shape_start}:{right_shape_end}]")

    # Selective contact filtering: arm bodies (0-6) filtered against ground planes,
    # finger bodies (7-8) keep contacts for physical table interaction.
    # Body indices per arm: 0-6 = arm links + hand, 7 = left finger, 8 = right finger
    # (from Phase 7: collapse_fixed_joints=True → body 6 = panda_hand, 7/8 = fingers)
    ground_planes = [table_idx]
    filter_count = 0
    for arm_label, shape_start, shape_end, body_start in [
        ("left", left_shape_start, left_shape_end, left_body_start),
        ("right", right_shape_start, right_shape_end, right_body_start),
    ]:
        for si in range(shape_start, shape_end):
            body_idx = builder.shape_body[si]
            local_body = body_idx - body_start
            # Filter arm bodies (0-6) against ground planes; keep fingers (7, 8)
            if local_body < 7:
                for gp in ground_planes:
                    builder.add_shape_collision_filter_pair(si, gp)
                    filter_count += 1
    print(f"  [SCENE] Contact filtering: {filter_count} arm-table pairs filtered, "
          f"finger shapes keep table contacts (DISABLE_CONTACTS={DISABLE_CONTACTS})")

    # Cable (capsule bodies + BALL joints — MuJoCo-compatible)
    cable_bodies = []
    cable_joints = []
    # Save robot DOF/coord counts before cable (used to separate robot/cable in control targets)
    # For robot joints (all 1-DOF REVOLUTE/PRISMATIC), dof_count == coord_count
    robot_joint_dof_count = builder.joint_dof_count
    robot_joint_coord_count = builder.joint_coord_count
    if use_cable:
        cable_shape_start = builder.shape_count
        cable_y_start = WIDE_LEFT_Y - 0.03
        cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CABLE_RADIUS + 0.01)
        cable_bodies, cable_joints = add_cable(builder, start_pos=cable_start, direction=(0, 1, 0))
        cable_shape_end = builder.shape_count
        cable_y_end = cable_start[1] + CABLE_SEGMENTS * CABLE_SEG_LEN
        print(f"  [SCENE] Cable: {len(cable_bodies)} bodies, {len(cable_joints)} joints, "
              f"Y=[{cable_y_start:.3f}, {cable_y_end:.3f}], Z={cable_start[2]:.4f}")
        # Filter cable vs arm bodies 0-6 (only finger bodies 7-8 should contact cable)
        cable_arm_filters = 0
        for cable_si in range(cable_shape_start, cable_shape_end):
            for arm_label, arm_shape_start, arm_shape_end, arm_body_start in [
                ("left", left_shape_start, left_shape_end, left_body_start),
                ("right", right_shape_start, right_shape_end, right_body_start),
            ]:
                for arm_si in range(arm_shape_start, arm_shape_end):
                    body_idx = builder.shape_body[arm_si]
                    local_body = body_idx - arm_body_start
                    if local_body < 7:  # arm bodies only, not fingers
                        builder.add_shape_collision_filter_pair(cable_si, arm_si)
                        cable_arm_filters += 1
        print(f"  [SCENE] Cable contact filters: "
              f"{cable_arm_filters} cable-arm (fingers keep cable contacts)")
    else:
        print(f"  [SCENE] Cable: DISABLED (--no-cable)")

    robot_body_count = right_body_start + FRANKA_NUM_JOINTS  # 18 robot bodies

    # === Convex hull approximation for ALL robot MESH shapes ===
    # CollisionPipeline narrowphase handles CONVEX_MESH-CAPSULE via GJK/MPR,
    # but NOT MESH-CAPSULE (no matching narrowphase path).
    # Converting finger MESHes to CONVEX_MESH enables finger-cable contacts.
    # Franka finger pads are roughly convex, so hull is a good approximation.
    all_robot_mesh_indices = []
    for shape_idx in range(builder.shape_count):
        body_idx = builder.shape_body[shape_idx]
        if body_idx >= 0 and body_idx < robot_body_count:
            if builder.shape_type[shape_idx] == newton.GeoType.MESH:
                all_robot_mesh_indices.append(shape_idx)
    if all_robot_mesh_indices:
        builder.approximate_meshes(
            method="convex_hull", shape_indices=all_robot_mesh_indices, keep_visual_shapes=True
        )
    print(f"  [CONVEX] {len(all_robot_mesh_indices)} robot MESH shapes → convex hull "
          f"(enables GJK/MPR for CONVEX_MESH-CAPSULE finger-cable contacts)")

    # Color shapes for collision group assignment (required for MuJoCo contype/conaffinity)
    builder.color()

    # requires_grad=False: CollisionPipeline skips rigid contacts when requires_grad=True
    # (collide.py:703). IK uses a separate model (build_ik_model) with requires_grad=True.
    model = builder.finalize(device=DEVICE, requires_grad=False)

    print(f"  [SCENE] Model: bodies={model.body_count}, joints={model.joint_count}, "
          f"articulations={model.articulation_count}, "
          f"joint_coords={model.joint_coord_count}, joint_dofs={model.joint_dof_count}")

    # Shape diagnostics for finger and cable bodies
    shape_types = model.shape_type.numpy()
    shape_bodies = model.shape_body.numpy()
    shape_xforms = model.shape_transform.numpy()
    aabb_lo = model.shape_collision_aabb_lower.numpy()
    aabb_hi = model.shape_collision_aabb_upper.numpy()
    shape_flags = model.shape_flags.numpy()
    shape_collision_group = model.shape_collision_group.numpy()
    TYPE_NAMES = {0: "NONE", 1: "PLANE", 2: "HFIELD", 3: "SPHERE", 4: "CAPSULE",
                  5: "ELLIPSOID", 6: "CYLINDER", 7: "BOX", 8: "MESH", 9: "CONE", 10: "CONVEX_MESH"}
    COLLIDE_SHAPES = newton.ShapeFlags.COLLIDE_SHAPES
    for arm_label, body_start_v in [("Left", left_body_start), ("Right", right_body_start)]:
        for local_body in [7, 8]:  # finger bodies
            bi = body_start_v + local_body
            shapes_for_body = [si for si in range(len(shape_bodies)) if shape_bodies[si] == bi]
            for si in shapes_for_body:
                st = shape_types[si]
                name = TYPE_NAMES.get(st, f"UNKNOWN({st})")
                flags = shape_flags[si]
                cgroup = shape_collision_group[si]
                has_collide = bool(flags & COLLIDE_SHAPES)
                print(f"  [SHAPE] {arm_label} body{local_body} shape#{si}: type={name}, "
                      f"flags={flags:#x}(COLLIDE={has_collide}), cgroup={cgroup}")
            if arm_label == "Left":
                break  # Only show left arm details
    if cable_bodies:
        si0 = [si for si in range(len(shape_bodies)) if shape_bodies[si] == cable_bodies[0]]
        if si0:
            si = si0[0]
            print(f"  [SHAPE] Cable body0 shape#{si}: type={TYPE_NAMES.get(shape_types[si],'?')}, "
                  f"flags={shape_flags[si]:#x}(COLLIDE={bool(shape_flags[si] & COLLIDE_SHAPES)}), "
                  f"cgroup={shape_collision_group[si]}")

    scene_info = {
        "model": model,
        "left_j_start": left_j_start,
        "left_j_end": left_j_end,
        "left_body_start": left_body_start,
        "right_j_start": right_j_start,
        "right_j_end": right_j_end,
        "right_body_start": right_body_start,
        "cable_bodies": cable_bodies,
        "cable_joints": cable_joints,
        "n_cable_bodies": len(cable_bodies),
        "robot_joint_dof_count": robot_joint_dof_count,
        "robot_joint_coord_count": robot_joint_coord_count,
        "robot_body_count": robot_body_count,
        "table_shape_idx": table_idx,
        "clip_shape_indices": clip_shape_indices,
    }
    return scene_info


def build_ik_model():
    """Build a robot-only model for IK solving (no cable, no collision geometry).

    Newton IKSolver has no joint masking — using the full model causes it to
    optimize cable BALL/FREE joints too (163 extra DOFs), diluting the gradient
    and producing unusable IK solutions (cost=1.6 instead of <1e-12).

    This model has identical robot body indices (left arm bodies 0-8, right arm
    bodies 9-17) since ground planes and world-attached shapes create no bodies.
    """
    builder = newton.ModelBuilder(gravity=GRAVITY)
    add_franka_arm(builder, pos=ROBOT_LEFT_BASE)
    add_franka_arm(builder, pos=ROBOT_RIGHT_BASE)
    ik_model = builder.finalize(device=DEVICE, requires_grad=True)
    print(f"  [IK] Robot-only model: bodies={ik_model.body_count}, "
          f"joint_coords={ik_model.joint_coord_count}, joint_dofs={ik_model.joint_dof_count}")
    return ik_model


# ---------------------------------------------------------------------------
# Physics step: single MuJoCo solver (robot PD + cable BALL joints + contacts)
# ---------------------------------------------------------------------------
def physics_step(model, state, solver, control, contacts):
    """Single-solver physics step.

    MuJoCo handles robot dynamics (REVOLUTE/PRISMATIC PD control,
    cable FREE/BALL joints with bend stiffness).
    CollisionPipeline handles all contacts via SDF narrowphase
    (MESH-CAPSULE finger-cable, CAPSULE-PLANE cable-table).

    Returns new state.
    """
    state.clear_forces()
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)

    # CollisionPipeline handles MESH-CAPSULE contacts (SDF narrowphase)
    if _collision_pipeline is not None:
        _collision_pipeline.collide(state, contacts)
    else:
        model.collide(state, contacts)
    state_out = model.state()
    solver.step(state, state_out, control, contacts, DT)
    return state_out


def detect_grasped(state, grip_center, cable_bodies, grasp_radius=0.10):
    """Find cable bodies within grasp radius of grip center."""
    wp.synchronize()
    bq = state.body_q.numpy()
    gc = np.array(grip_center)
    indices = []
    for bi in cable_bodies:
        pos = bq[bi][:3]
        dist = np.linalg.norm(pos - gc)
        if dist < grasp_radius:
            indices.append(bi)
    return indices


# ---------------------------------------------------------------------------
# IK helpers
# ---------------------------------------------------------------------------
def solve_ik_dual(model, state, scene_info,
                  target_left, target_right):
    """Solve IK for both arms using the robot-only IK model.

    Uses a separate model without cable joints so the IK solver only
    optimizes robot DOFs (18 coords vs 181 in full model).

    Args:
        target_left: (x, y, z) target for left EE
        target_right: (x, y, z) target for right EE

    Returns:
        joint_q array (full model size) with IK solution for robot joints,
        cable joint coords unchanged from current state.
    """
    ik_model = scene_info["ik_model"]
    robot_coords = scene_info["robot_joint_coord_count"]

    left_ee_body = scene_info["left_body_start"] + EE_BODY_OFFSET
    right_ee_body = scene_info["right_body_start"] + EE_BODY_OFFSET

    target_l = np.array([target_left], dtype=np.float32)
    target_r = np.array([target_right], dtype=np.float32)

    obj_l = IKObjectivePosition(
        link_index=left_ee_body,
        link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_l, dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    )
    obj_r = IKObjectivePosition(
        link_index=right_ee_body,
        link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_r, dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    )

    # Rotation objectives: hand pointing down (180° around X-axis)
    # Quaternion xyzw: (1, 0, 0, 0) = 180° rotation around X
    target_rot = wp.array([wp.vec4(1.0, 0.0, 0.0, 0.0)], dtype=wp.vec4, device=DEVICE)
    rot_l = IKObjectiveRotation(
        link_index=left_ee_body,
        link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot,
        weight=0.5,
    )
    rot_r = IKObjectiveRotation(
        link_index=right_ee_body,
        link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot,
        weight=0.5,
    )

    ik_solver = IKSolver(ik_model, n_problems=1, objectives=[obj_l, obj_r, rot_l, rot_r])

    # Copy robot joint coords from full state as initial guess
    jq_full = state.joint_q.numpy()
    jq_robot = jq_full[:robot_coords].copy()
    jq_in = wp.array(jq_robot.reshape(1, -1), dtype=float, device=DEVICE)
    jq_out = wp.zeros((1, ik_model.joint_coord_count), dtype=float, device=DEVICE)

    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)

    cost = ik_solver.costs.numpy()[0]
    result_robot = jq_out.numpy()[0]

    # Build full joint_q: robot IK result + original cable coords
    result_full = jq_full.copy()
    result_full[:robot_coords] = result_robot

    return result_full, cost


def get_ee_positions(state, scene_info):
    """Get current EE positions for both arms."""
    body_q = state.body_q.numpy()
    left_ee = scene_info["left_body_start"] + EE_BODY_OFFSET
    right_ee = scene_info["right_body_start"] + EE_BODY_OFFSET
    pos_l = body_q[left_ee][:3]
    pos_r = body_q[right_ee][:3]
    return pos_l, pos_r


# ---------------------------------------------------------------------------
# Motion helpers
# ---------------------------------------------------------------------------
def ik_move_both(model, state, scene_info, solver, control, contacts,
                 target_left, target_right, label="MOVE",
                 converge_mm=5.0,
                 speed_factor=1.0):
    """Move both EEs to target positions using IK + MuJoCo stepping.

    Strategy: Solve IK ONCE for the final target, then interpolate joint targets
    over physics steps. This is ~1000x faster than solving IK per step.

    Args:
        speed_factor: multiplier for step count (>1 = slower motion).

    Returns (final_state, success).
    """
    cable_bodies = scene_info.get("cable_bodies", [])

    pos_l, pos_r = get_ee_positions(state, scene_info)
    dist = max(np.linalg.norm(np.array(target_left) - pos_l),
               np.linalg.norm(np.array(target_right) - pos_r))
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)

    print(f"  [{label}] Moving: L=({pos_l[0]:.3f},{pos_l[1]:.3f},{pos_l[2]:.3f}) "
          f"→ ({target_left[0]:.3f},{target_left[1]:.3f},{target_left[2]:.3f})")
    print(f"  [{label}] Moving: R=({pos_r[0]:.3f},{pos_r[1]:.3f},{pos_r[2]:.3f}) "
          f"→ ({target_right[0]:.3f},{target_right[1]:.3f},{target_right[2]:.3f})")
    print(f"  [{label}] dist={dist*1000:.1f}mm, steps={n_steps}")

    tgt_l = np.array(target_left, dtype=np.float32)
    tgt_r = np.array(target_right, dtype=np.float32)

    # Solve IK once for final target
    jq_target, ik_cost = solve_ik_dual(model, state, scene_info,
                                       tuple(tgt_l), tuple(tgt_r))
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False
    print(f"  [{label}] IK solved: cost={ik_cost:.2e}")

    # Interpolate ROBOT joint targets only (cable BALL joints have passive PD for bend stiffness)
    # For all-1-DOF robot joints: dof_count == coord_count, so indexing is interchangeable
    robot_dofs = scene_info["robot_joint_dof_count"]
    jq_start = state.joint_q.numpy().copy()
    jq_end = jq_target.copy()

    # Identify finger DOF indices to exclude from IK interpolation
    # (finger targets must be preserved — IK solution defaults to open position)
    left_j = scene_info["left_j_start"]
    right_j = scene_info["right_j_start"]
    finger_dofs = {left_j + 7, left_j + 8, right_j + 7, right_j + 8}

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)

        # Interpolate ARM joint targets only (j0-j6), preserve FINGER targets (j7-j8)
        jq_interp = jq_start[:robot_dofs] + (jq_end[:robot_dofs] - jq_start[:robot_dofs]) * t
        target_pos = control.joint_target_pos.numpy()
        for d in range(robot_dofs):
            if d not in finger_dofs:
                target_pos[d] = jq_interp[d]
        control.joint_target_pos.assign(target_pos)

        # MuJoCo step (robot PD + cable dynamics + all contacts)
        state = physics_step(model, state, solver, control, contacts)

        # Video frame capture
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)

        # Check cable NaN
        if cable_bodies:
            bq = state.body_q.numpy()
            if np.any(np.isnan(bq[cable_bodies])):
                print(f"  [{label}] Cable NaN at step {step}!")
                return state, False

        # Log progress
        if step % max(n_steps // 5, 1) == 0:
            cur_l, cur_r = get_ee_positions(state, scene_info)
            err_l = np.linalg.norm(cur_l - tgt_l) * 1000
            err_r = np.linalg.norm(cur_r - tgt_r) * 1000
            cable_str = ""
            if cable_bodies:
                bq = state.body_q.numpy()
                cz = bq[cable_bodies, 2]
                cz_nan = np.any(np.isnan(cz))
                cable_str = f" cable_z=[{np.nanmin(cz):.4f},{np.nanmean(cz):.4f}] nan={cz_nan}"
            # Extended diagnostics during lift phases: contacts + finger positions
            diag_str = ""
            if label.startswith("P2") and cable_bodies:
                jq = state.joint_q.numpy()
                lj = scene_info["left_j_start"]
                rj = scene_info["right_j_start"]
                fj = [jq[lj+7], jq[lj+8], jq[rj+7], jq[rj+8]]
                diag_str += f" fingers=[{fj[0]*1000:.1f},{fj[1]*1000:.1f},{fj[2]*1000:.1f},{fj[3]*1000:.1f}]mm"
                # Check contacts (CollisionPipeline already ran in physics_step)
                if _collision_pipeline is not None:
                    _collision_pipeline.collide(state, contacts)
                else:
                    solver.update_contacts(contacts)
                wp.synchronize()
                nc = contacts.rigid_contact_count.numpy()[0]
                if nc > 0:
                    s0 = contacts.rigid_contact_shape0.numpy()[:nc]
                    s1 = contacts.rigid_contact_shape1.numpy()[:nc]
                    sb = model.shape_body.numpy()
                    lb = scene_info["left_body_start"]
                    rb = scene_info["right_body_start"]
                    fset = {lb+7, lb+8, rb+7, rb+8}
                    cset = set(cable_bodies)
                    fc_cnt = sum(1 for ci in range(nc)
                                if (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                                and (sb[s0[ci]] in cset or sb[s1[ci]] in cset))
                    co_cnt = sum(1 for ci in range(nc)
                                if (sb[s0[ci]] in cset or sb[s1[ci]] in cset)
                                and not (sb[s0[ci]] in fset or sb[s1[ci]] in fset))
                    diag_str += f" contacts={nc}(fc={fc_cnt},co={co_cnt})"
                else:
                    diag_str += " contacts=0"
            print(f"  [{label}] step {step}/{n_steps}: err L={err_l:.1f}mm R={err_r:.1f}mm{cable_str}{diag_str}")

    # Final error
    pos_l, pos_r = get_ee_positions(state, scene_info)
    err_l = np.linalg.norm(pos_l - tgt_l) * 1000
    err_r = np.linalg.norm(pos_r - tgt_r) * 1000
    converged = err_l < converge_mm and err_r < converge_mm
    print(f"  [{label}] Final: err L={err_l:.1f}mm R={err_r:.1f}mm "
          f"converged={converged} (thresh={converge_mm}mm)")

    return state, converged


def hold_position(model, state, scene_info, solver, control, contacts,
                  n_steps):
    """Hold current position for n_steps (settle)."""
    for step in range(n_steps):
        state = physics_step(model, state, solver, control, contacts)

        # Video frame capture
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)

    return state


# ---------------------------------------------------------------------------
# Raw evidence logger (for independent verification by Code B)
# ---------------------------------------------------------------------------
class RawEvidenceLogger:
    """Logs raw state snapshots at phase boundaries.

    Code B uses this data to independently re-compute metrics,
    rather than trusting Code A's RUN_METRICS.json.
    """

    def __init__(self, output_dir):
        self.path = os.path.join(output_dir, "raw_evidence.jsonl")
        self.fh = open(self.path, "w")

    def log(self, event, state, scene_info, extra=None):
        """Log a raw state snapshot."""
        cable_bodies = scene_info.get("cable_bodies", [])
        entry = {"event": event, "t": time.time()}

        # EE positions (raw body_q)
        pos_l, pos_r = get_ee_positions(state, scene_info)
        entry["ee_left"] = pos_l.tolist()
        entry["ee_right"] = pos_r.tolist()

        # EE orientations (raw quaternion xyzw)
        body_q = state.body_q.numpy()
        left_ee = scene_info["left_body_start"] + EE_BODY_OFFSET
        right_ee = scene_info["right_body_start"] + EE_BODY_OFFSET
        entry["ee_left_quat"] = body_q[left_ee][3:7].tolist()
        entry["ee_right_quat"] = body_q[right_ee][3:7].tolist()

        # Cable body positions (rod capsules)
        if cable_bodies:
            cable_pos = body_q[cable_bodies, :3]
            entry["cable_body_positions"] = cable_pos.tolist()
            entry["cable_z_mean"] = float(np.mean(cable_pos[:, 2]))
            entry["cable_z_min"] = float(np.min(cable_pos[:, 2]))
            entry["cable_z_max"] = float(np.max(cable_pos[:, 2]))
            # Per-body distance to clip XY
            clip_xy = np.array([CLIP1_X, CLIP1_Y])
            dists = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
            entry["cable_min_dist_to_clip_xy"] = float(np.min(dists))
            entry["bodies_near_clip_30mm"] = int(np.sum(dists < 0.030))

        # Joint state (raw)
        jq = state.joint_q.numpy()
        entry["joint_q"] = jq.tolist()

        if extra:
            entry.update(extra)

        self.fh.write(json.dumps(entry, default=json_default) + "\n")
        self.fh.flush()

    def close(self):
        self.fh.close()


def json_default(obj):
    """JSON serializer for numpy types."""
    if isinstance(obj, (np.floating, np.integer)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# ---------------------------------------------------------------------------
# Phase functions
# ---------------------------------------------------------------------------
def _check_contacts(solver, contacts, model, scene_info, label, state=None):
    """Print contact breakdown at a checkpoint."""
    cable_bodies = scene_info.get("cable_bodies", [])
    # Use CollisionPipeline if available (handles MESH-CAPSULE via SDF)
    if _collision_pipeline is not None and state is not None:
        _collision_pipeline.collide(state, contacts)
    else:
        solver.update_contacts(contacts)
    wp.synchronize()
    n = contacts.rigid_contact_count.numpy()[0]
    if n == 0:
        print(f"  [{label}] MuJoCo contacts: 0")
        return
    shape0 = contacts.rigid_contact_shape0.numpy()[:n]
    shape1 = contacts.rigid_contact_shape1.numpy()[:n]
    sb = model.shape_body.numpy()
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    finger_set = {lb+7, lb+8, rb+7, rb+8}
    cable_set = set(cable_bodies)
    fc, fo, co, oo = 0, 0, 0, 0
    for ci in range(n):
        b0 = sb[shape0[ci]] if shape0[ci] >= 0 else -1
        b1 = sb[shape1[ci]] if shape1[ci] >= 0 else -1
        is_f = b0 in finger_set or b1 in finger_set
        is_c = b0 in cable_set or b1 in cable_set
        if is_f and is_c:
            fc += 1
        elif is_f:
            fo += 1
        elif is_c:
            co += 1
        else:
            oo += 1
    print(f"  [{label}] MuJoCo contacts: {n} (finger-cable={fc}, finger-other={fo}, cable-other={co}, other={oo})")


def do_p1_grasp(model, state, scene_info, solver, control, contacts):
    """P1: Wide-stance approach + descend + grasp."""
    print(f"\n  {'='*50}")
    print(f"  [P1] Wide-Stance Approach + Grasp")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)

    # Step 1: Approach (move to above cable)
    print(f"\n  [P1-APPROACH] Target: L=({grasp_x:.3f},{WIDE_LEFT_Y},{APPROACH_Z}) "
          f"R=({grasp_x:.3f},{WIDE_RIGHT_Y},{APPROACH_Z})")
    state, ok = ik_move_both(
        model, state, scene_info, solver, control, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, APPROACH_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, APPROACH_Z),
        label="P1-APPROACH", converge_mm=10.0,
    )
    if not ok:
        print(f"  [P1-APPROACH] WARN: not converged, continuing anyway")

    # Contact check after approach
    if has_cable:
        _check_contacts(solver, contacts, model, scene_info, "P1-APPROACH-END", state=state)

    # Step 2: Descend to cable level
    print(f"\n  [P1-DESCEND] Target Z={GRASP_Z}")
    state, ok = ik_move_both(
        model, state, scene_info, solver, control, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, GRASP_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, GRASP_Z),
        label="P1-DESCEND", converge_mm=5.0,
    )
    if not ok:
        print(f"  [P1-DESCEND] WARN: not converged, continuing anyway")

    # Contact check after descend
    if has_cable:
        _check_contacts(solver, contacts, model, scene_info, "P1-DESCEND-END", state=state)
        bq_d = state.body_q.numpy()
        cz_d = bq_d[cable_bodies, 2]
        print(f"  [P1-DESCEND-END] Cable Z: min={np.min(cz_d):.4f}, mean={np.mean(cz_d):.4f}, "
              f"max={np.max(cz_d):.4f}, nan={np.any(np.isnan(cz_d))}")

    # Step 3: Close fingers (PD target) — physical contact grasps the cable
    print(f"\n  [P1-CLOSE] Closing fingers to {FINGER_CLOSE_POS*1000:.1f}mm")
    left_j_start = scene_info["left_j_start"]
    right_j_start = scene_info["right_j_start"]
    robot_dofs = scene_info["robot_joint_dof_count"]

    # Pre-close diagnostics: check state health
    jq_pre = state.joint_q.numpy()
    bq_pre = state.body_q.numpy()
    nan_jq = np.any(np.isnan(jq_pre))
    nan_bq = np.any(np.isnan(bq_pre))
    print(f"  [P1-CLOSE] Pre-close state: jq NaN={nan_jq}, bq NaN={nan_bq}")
    print(f"  [P1-CLOSE] Pre-close fingers: L_j7={jq_pre[left_j_start+7]*1000:.1f}mm "
          f"L_j8={jq_pre[left_j_start+8]*1000:.1f}mm "
          f"R_j7={jq_pre[right_j_start+7]*1000:.1f}mm "
          f"R_j8={jq_pre[right_j_start+8]*1000:.1f}mm")
    cable_bodies = scene_info.get("cable_bodies", [])
    if cable_bodies:
        cable_z = [bq_pre[b][2] for b in cable_bodies[:5]]
        print(f"  [P1-CLOSE] Pre-close cable Z[0:5]: {['%.3f'%z for z in cable_z]}")

    target_pos = control.joint_target_pos.numpy()
    target_vel = control.joint_target_vel.numpy()

    # Set finger targets: position=-0.02 (squeeze past zero), velocity=-0.5 m/s
    # Negative position target ensures PD ke force pushes CLOSED even when fingers
    # are at -10mm (0 target would create 21N opening force, -20mm target creates
    # 19N closing force). Joint limit lower=-0.025 prevents limit restoring force.
    finger_target_pos = -0.02  # 20mm past zero — both PD and limit push closed
    for arm_start in [left_j_start, right_j_start]:
        finger_j7 = arm_start + 7
        finger_j8 = arm_start + 8
        if finger_j7 < robot_dofs:
            target_pos[finger_j7] = finger_target_pos
            target_vel[finger_j7] = -0.5
        if finger_j8 < robot_dofs:
            target_pos[finger_j8] = finger_target_pos
            target_vel[finger_j8] = -0.5
    control.joint_target_pos.assign(target_pos)
    control.joint_target_vel.assign(target_vel)

    # Step physics to close fingers — with cable + robot NaN monitoring
    robot_dofs = scene_info["robot_joint_dof_count"]
    robot_coords = scene_info["robot_joint_coord_count"]
    lb = scene_info["left_body_start"]
    nan_detected_step = -1
    for step in range(FINGER_CLOSE_STEPS):
        state = physics_step(model, state, solver, control, contacts)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)
        # Monitor every 10 steps (+ first 5) for NaN and cable state
        if has_cable and (step < 5 or step % 10 == 0):
            bq = state.body_q.numpy()
            robot_nan = np.any(np.isnan(bq[:scene_info["robot_body_count"]]))
            cable_nan = np.any(np.isnan(bq[cable_bodies]))
            if robot_nan or cable_nan:
                # NaN detected — print and break
                print(f"    [CLOSE-NAN] step={step}: robot_nan={robot_nan}, cable_nan={cable_nan}")
                # Show which body went NaN first
                for bi in range(len(bq)):
                    if np.any(np.isnan(bq[bi])):
                        label = model.body_label[bi] if bi < len(model.body_label) else f"body{bi}"
                        print(f"      NaN body {bi} ({label}): {bq[bi][:3]}")
                        if bi >= 5:
                            print(f"      ... (showing first 5 NaN bodies)")
                            break
                nan_detected_step = step
                break
            cz = bq[cable_bodies, 2]
            b0 = bq[cable_bodies[0]]
            jqd = state.joint_qd.numpy()
            # Check finger joint positions
            fj7 = state.joint_q.numpy()[left_j_start + 7]
            fj8 = state.joint_q.numpy()[left_j_start + 8]
            if step < 5 or step % 50 == 0 or abs(np.mean(cz) - TABLE_HEIGHT) > 0.005:
                free_qd = jqd[robot_dofs:robot_dofs+6]
                print(f"    [CLOSE-DIAG] step={step}: cable_z={np.mean(cz):.4f} "
                      f"finger=[{fj7*1000:.1f},{fj8*1000:.1f}]mm "
                      f"body0=[{b0[0]:.3f},{b0[1]:.3f},{b0[2]:.3f}] "
                      f"free_qd_max={np.max(np.abs(free_qd)):.2f}")
    if nan_detected_step >= 0:
        print(f"  [P1-CLOSE] NaN detected at step {nan_detected_step}/{FINGER_CLOSE_STEPS}")

    # Read finger positions
    jq = state.joint_q.numpy()
    grip_l = jq[left_j_start + 7] + jq[left_j_start + 8]
    grip_r = jq[right_j_start + 7] + jq[right_j_start + 8]
    print(f"  [P1-CLOSE] Grip: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

    # Step 4: Detailed position diagnostics
    wp.synchronize()
    bq = state.body_q.numpy()
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(f"  [P1-DIAG] Left arm body positions:")
    print(f"    body6(hand): Z={bq[lb+6][2]:.4f}")
    print(f"    body7(Lfin): Z={bq[lb+7][2]:.4f}, Y={bq[lb+7][1]:.4f}")
    print(f"    body8(Rfin): Z={bq[lb+8][2]:.4f}, Y={bq[lb+8][1]:.4f}")
    print(f"    b6-b7 offset: {(bq[lb+6][2]-bq[lb+7][2])*1000:.1f}mm")
    print(f"  [P1-DIAG] Right arm body positions:")
    print(f"    body6(hand): Z={bq[rb+6][2]:.4f}")
    print(f"    body7(Lfin): Z={bq[rb+7][2]:.4f}, Y={bq[rb+7][1]:.4f}")
    print(f"    body8(Rfin): Z={bq[rb+8][2]:.4f}, Y={bq[rb+8][1]:.4f}")
    if has_cable:
        cable_z = [bq[b][2] for b in cable_bodies]
        cable_y = [bq[b][1] for b in cable_bodies]
        print(f"  [P1-DIAG] Cable: Z_mean={np.mean(cable_z):.4f}, Y_range=[{min(cable_y):.3f},{max(cable_y):.3f}]")

        # Compute finger shape world-space positions using body quaternion
        # body_q format: [x,y,z, qw,qx,qy,qz]
        b7_pos = bq[lb+7][:3]
        b7_quat_raw = bq[lb+7][3:7]  # Warp: [qx, qy, qz, qw]
        qx, qy, qz, qw = b7_quat_raw
        b7_quat = np.array([qw, qx, qy, qz])  # Convert to [qw, qx, qy, qz] for rotation
        # Local AABB corners for finger mesh (from model data)
        aabb_lo_local = model.shape_collision_aabb_lower.numpy()
        aabb_hi_local = model.shape_collision_aabb_upper.numpy()
        # Find shapes for left body7
        shape_bodies_arr = model.shape_body.numpy()
        for si in range(len(shape_bodies_arr)):
            if shape_bodies_arr[si] == lb + 7:
                lo = aabb_lo_local[si]
                hi = aabb_hi_local[si]
                # Transform 8 AABB corners to world
                corners = []
                for x in [lo[0], hi[0]]:
                    for y in [lo[1], hi[1]]:
                        for z in [lo[2], hi[2]]:
                            # Rotate by body quaternion then translate
                            p = np.array([x, y, z])
                            # Quaternion rotation: q * p * q_inv
                            qw, qx, qy, qz = b7_quat
                            # Using rotation matrix from quaternion
                            R = np.array([
                                [1-2*(qy*qy+qz*qz), 2*(qx*qy-qw*qz), 2*(qx*qz+qw*qy)],
                                [2*(qx*qy+qw*qz), 1-2*(qx*qx+qz*qz), 2*(qy*qz-qw*qx)],
                                [2*(qx*qz-qw*qy), 2*(qy*qz+qw*qx), 1-2*(qx*qx+qy*qy)]
                            ])
                            world_p = R @ p + b7_pos
                            corners.append(world_p)
                corners = np.array(corners)
                world_z_min = corners[:, 2].min()
                world_z_max = corners[:, 2].max()
                print(f"  [P1-DIAG] L-finger7 shape#{si} world Z: [{world_z_min:.4f}, {world_z_max:.4f}]")
                break
        print(f"  [P1-DIAG] Gap finger_world_bottom to cable: {(world_z_min - np.mean(cable_z))*1000:.1f}mm")

    # Check contacts (CollisionPipeline for MESH-CAPSULE, else MuJoCo internal)
    if has_cable:
        if _collision_pipeline is not None:
            _collision_pipeline.collide(state, contacts)
        else:
            solver.update_contacts(contacts)
        wp.synchronize()
        n_contacts = contacts.rigid_contact_count.numpy()[0]
        max_contacts = NJMAX  # CollisionPipeline doesn't have get_max_contact_count
        print(f"  [P1-CONTACTS] contacts: {n_contacts} (max={max_contacts})")
        if n_contacts > 0:
            shape0 = contacts.rigid_contact_shape0.numpy()[:n_contacts]
            shape1 = contacts.rigid_contact_shape1.numpy()[:n_contacts]
            shape_bodies_arr = model.shape_body.numpy()
            lb = scene_info["left_body_start"]
            rb = scene_info["right_body_start"]
            finger_bodies_set = {lb+7, lb+8, rb+7, rb+8}
            cable_bodies_set = set(cable_bodies)
            finger_cable = 0
            finger_other = 0
            cable_other = 0
            other = 0
            for ci in range(n_contacts):
                b0 = shape_bodies_arr[shape0[ci]] if shape0[ci] >= 0 else -1
                b1 = shape_bodies_arr[shape1[ci]] if shape1[ci] >= 0 else -1
                is_finger = b0 in finger_bodies_set or b1 in finger_bodies_set
                is_cable = b0 in cable_bodies_set or b1 in cable_bodies_set
                if is_finger and is_cable:
                    finger_cable += 1
                elif is_finger:
                    finger_other += 1
                elif is_cable:
                    cable_other += 1
                else:
                    other += 1
            print(f"  [P1-CONTACTS] breakdown: finger-cable={finger_cable}, "
                  f"finger-other={finger_other}, cable-other={cable_other}, other={other}")
            # Show first few contact pairs for debugging
            for ci in range(min(5, n_contacts)):
                b0 = shape_bodies_arr[shape0[ci]] if shape0[ci] >= 0 else -1
                b1 = shape_bodies_arr[shape1[ci]] if shape1[ci] >= 0 else -1
                print(f"    contact {ci}: shape({shape0[ci]},{shape1[ci]}) body({b0},{b1})")

    # Check which cable bodies are near fingertips
    grasped_left = []
    grasped_right = []
    if has_cable:
        gc_l = list(pos_l)
        gc_r = list(pos_r)
        gc_l[2] -= EE_TO_FINGERTIP
        gc_r[2] -= EE_TO_FINGERTIP
        grasped_left = detect_grasped(state, gc_l, cable_bodies)
        grasped_right = detect_grasped(state, gc_r, cable_bodies)
        print(f"  [P1-GRASP] Cable bodies near grippers: L={len(grasped_left)} R={len(grasped_right)}")
        print(f"  [P1-GRASP] Grip center estimate: L=({gc_l[0]:.3f},{gc_l[1]:.3f},{gc_l[2]:.3f}) "
              f"R=({gc_r[0]:.3f},{gc_r[1]:.3f},{gc_r[2]:.3f})")

    pos_l, pos_r = get_ee_positions(state, scene_info)

    # Raw evidence: P1 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log("P1_complete", state, scene_info, extra={
            "grasped_left": grasped_left,
            "grasped_right": grasped_right,
            "grip_l_mm": round(grip_l * 1000, 2),
            "grip_r_mm": round(grip_r * 1000, 2),
        })

    result = {
        "pass": True,
        "grip_l_mm": round(grip_l * 1000, 2),
        "grip_r_mm": round(grip_r * 1000, 2),
        "grasped_left": grasped_left,
        "grasped_right": grasped_right,
        "ee_left": pos_l.tolist(),
        "ee_right": pos_r.tolist(),
    }
    return state, result


def do_p2_lift(model, state, scene_info, solver, control, contacts):
    """P2: Micro-lift to confirm grip."""
    print(f"\n  {'='*50}")
    print(f"  [P2] Micro-Lift (grip confirmation)")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)

    # Record cable Z before lift
    cable_z_before = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_before = np.mean(bq[cable_bodies, 2])
        print(f"  [P2] Cable Z before: {cable_z_before:.4f}")

    # Lift to LIFT_Z
    print(f"  [P2-LIFT] Target Z={LIFT_Z} (+{(LIFT_Z-GRASP_Z)*1000:.0f}mm)")
    state, ok = ik_move_both(
        model, state, scene_info, solver, control, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, LIFT_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, LIFT_Z),
        label="P2-LIFT",
    )

    # Settle
    state = hold_position(model, state, scene_info, solver, control, contacts,
                          SETTLE_STEPS)

    # Check cable lift
    cable_z_delta_mm = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_after = np.mean(bq[cable_bodies, 2])
        cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)
        print(f"  [P2] Cable Z after: {cable_z_after:.4f}, delta={cable_z_delta_mm}mm")

    lifted = cable_z_delta_mm > 5.0 if has_cable else True
    print(f"  [P2] Lift {'OK' if lifted else 'INSUFFICIENT'}: {cable_z_delta_mm}mm")

    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log("P2_complete", state, scene_info, extra={
            "cable_z_delta_mm": cable_z_delta_mm,
            "lifted": lifted,
        })

    result = {
        "pass": lifted,
        "cable_z_delta_mm": cable_z_delta_mm,
    }
    return state, result


def do_p3_move(model, state, scene_info, solver, control, contacts):
    """P3: Move from cable X to clip X."""
    print(f"\n  {'='*50}")
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    move_target_x = CLIP_X + P3_X_OFFSET
    print(f"  [P3] Move to Clip X ({grasp_x:.3f} → {move_target_x:.3f}  [CLIP_X={CLIP_X} + offset={P3_X_OFFSET}])")
    print(f"  {'='*50}")

    pos_l, pos_r = get_ee_positions(state, scene_info)

    state, ok = ik_move_both(
        model, state, scene_info, solver, control, contacts,
        target_left=(move_target_x, pos_l[1], pos_l[2]),
        target_right=(move_target_x, pos_r[1], pos_r[2]),
        label="P3-MOVE", converge_mm=8.0,
    )

    state = hold_position(model, state, scene_info, solver, control, contacts,
                          SETTLE_STEPS)

    # Raw evidence: P3 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        pos_l_final, pos_r_final = get_ee_positions(state, scene_info)
        evidence.log("P3_complete", state, scene_info, extra={
            "target_x": move_target_x,
            "ee_left_final": pos_l_final.tolist(),
            "ee_right_final": pos_r_final.tolist(),
            "converged": ok,
        })

    result = {"pass": ok}
    return state, result


def do_p4_push(model, state, scene_info, solver, control, contacts):
    """P4: Push both arms down to PUSH_Z."""
    print(f"\n  {'='*50}")
    print(f"  [P4] Push Down to Z={PUSH_Z}")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0

    cable_z_before = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_before = np.mean(bq[cable_bodies, 2])

    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(f"  [P4] Current EE Z: L={pos_l[2]:.4f} R={pos_r[2]:.4f}")
    print(f"  [P4] Push target Z={PUSH_Z} (dZ={((PUSH_Z - pos_l[2])*1000):.1f}mm)")

    state, ok = ik_move_both(
        model, state, scene_info, solver, control, contacts,
        target_left=(pos_l[0], pos_l[1], PUSH_Z),
        target_right=(pos_r[0], pos_r[1], PUSH_Z),
        label="P4-PUSH",
        speed_factor=2.0,  # slower push reduces cable XY inertia
    )

    # Longer settle for push (3x base: cable XY equilibration after push-down)
    state = hold_position(model, state, scene_info, solver, control, contacts,
                          SETTLE_STEPS * 3)

    # Diagnostics
    cable_z_min = 0.0
    cable_z_delta_mm = 0.0
    particles_near_clip = 0
    min_dist_xy_mm = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_pos = bq[cable_bodies, :3]
        cable_z_after = np.mean(cable_pos[:, 2])
        cable_z_min = np.min(cable_pos[:, 2])
        cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)
        print(f"  [P4] Cable Z min={cable_z_min:.4f}, delta={cable_z_delta_mm}mm")
        print(f"  [P4] Cable X range: [{np.min(cable_pos[:,0]):.3f}, {np.max(cable_pos[:,0]):.3f}]")
        print(f"  [P4] Cable Y range: [{np.min(cable_pos[:,1]):.3f}, {np.max(cable_pos[:,1]):.3f}]")

        # Check if cable is in clip groove (Z below top AND XY near clip)
        clip_top_z = CLIP1_Z + 0.030
        clip_xy = np.array([CLIP1_X, CLIP1_Y])
        dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
        groove_radius = CLIP_GROOVE_INNER_RADIUS
        bodies_in_groove = int(np.sum(dists_xy < groove_radius))
        bodies_near_clip = int(np.sum(dists_xy < 0.030))  # 30mm
        min_dist_xy_mm = round(float(np.min(dists_xy)) * 1000, 1)
        z_ok = cable_z_min < clip_top_z
        xy_ok = bodies_in_groove >= 1  # strict: body must be within groove radius
        cable_in_groove = z_ok and xy_ok
        print(f"  [P4] Clip top Z={clip_top_z:.4f}, z_ok={z_ok}, "
              f"xy_dist_min={min_dist_xy_mm}mm, bodies_in_groove={bodies_in_groove}, "
              f"bodies_near_30mm={bodies_near_clip}, cable_in_groove={cable_in_groove}")
    else:
        cable_in_groove = True  # No cable → pass

    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(f"  [P4] Final EE: L=({pos_l[0]:.4f},{pos_l[1]:.4f},{pos_l[2]:.4f}) "
          f"R=({pos_r[0]:.4f},{pos_r[1]:.4f},{pos_r[2]:.4f})")

    # Raw evidence: P4 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log("P4_complete", state, scene_info, extra={
            "cable_z_min": round(cable_z_min, 4) if has_cable else None,
            "cable_z_delta_mm": cable_z_delta_mm,
            "cable_in_groove": cable_in_groove,
            "clip_top_z": CLIP1_Z + 0.030 if has_cable else None,
            "bodies_in_groove_6mm": bodies_in_groove if has_cable else None,
            "bodies_near_clip_30mm": bodies_near_clip if has_cable else None,
            "min_dist_xy_mm": min_dist_xy_mm if has_cable else None,
        })

    result = {
        "pass": ok and cable_in_groove,
        "cable_z_min": round(cable_z_min, 4) if has_cable else None,
        "cable_z_delta_mm": cable_z_delta_mm,
        "cable_in_groove": cable_in_groove,
        "bodies_in_groove_6mm": bodies_in_groove if has_cable else None,
        "bodies_near_clip_30mm": bodies_near_clip if has_cable else None,
        "min_dist_xy_mm": min_dist_xy_mm if has_cable else None,
    }
    return state, result


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------
def run_episode(model, state, scene_info, solver, control, contacts, episode_idx):
    """Run P1-P4 clip routing episode."""
    results = {"episode": episode_idx, "overall": "FAIL"}

    # Raw evidence: episode start
    evidence = scene_info.get("evidence")
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    if evidence:
        evidence.log("episode_start", state, scene_info, extra={
            "episode": episode_idx,
            "settled_grasp_x": grasp_x,
            "original_grasp_x": GRASP_X,
            "grasp_x_drift_mm": round((grasp_x - GRASP_X) * 1000, 1),
        })

    # === P1: Grasp ===
    state, p1 = do_p1_grasp(model, state, scene_info, solver, control, contacts)
    results["P1_grasp"] = {k: v for k, v in p1.items() if k not in ("grasped_left", "grasped_right")}
    if not p1["pass"]:
        results["fail_reason"] = "P1_grasp_fail"
        return state, results

    # === P2: Micro-lift ===
    state, p2 = do_p2_lift(model, state, scene_info, solver, control, contacts)
    results["P2_lift"] = p2
    if not p2["pass"]:
        results["fail_reason"] = "P2_lift_insufficient"
        print(f"  [P2] WARN: lift={p2['cable_z_delta_mm']}mm, continuing anyway")

    # === P3: Move to clip ===
    state, p3 = do_p3_move(model, state, scene_info, solver, control, contacts)
    results["P3_move"] = p3
    if not p3["pass"]:
        results["fail_reason"] = "P3_move_fail"

    # === P4: Push down ===
    state, p4 = do_p4_push(model, state, scene_info, solver, control, contacts)
    results["P4_push"] = p4

    # All phases must pass for overall PASS
    all_pass = p1["pass"] and p2["pass"] and p3["pass"] and p4["pass"]
    if all_pass:
        results["overall"] = "PASS"
    else:
        results["overall"] = "FAIL"
        results.setdefault("fail_reason", "P4_push_fail")

    # Raw evidence: episode end
    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log("episode_end", state, scene_info, extra={
            "episode": episode_idx,
            "overall": results["overall"],
        })

    return state, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Newton clip routing test")
    parser.add_argument("--no-cable", action="store_true", help="Remove cable (IK isolation test)")
    parser.add_argument("--num-episodes", type=int, default=1, help="Number of episodes")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--record-video", action="store_true", help="Record video (ViewerGL headless)")
    parser.add_argument("--no-video", action="store_true", help="Disable video even when HARNESS_RECORD_VIDEO=1")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (enables per-episode perturbation)")
    args = parser.parse_args()

    use_cable = not args.no_cable
    # Harness mode: HARNESS_RECORD_VIDEO=1 enables video by default
    if not args.no_video and os.environ.get("HARNESS_RECORD_VIDEO", "") == "1":
        args.record_video = True

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/newton_clip_routing_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[NEWTON_CLIP_ROUTING] Device={DEVICE}")
    print(f"[NEWTON_CLIP_ROUTING] Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"[NEWTON_CLIP_ROUTING] DT={DT:.6f}s ({int(1/DT)}Hz)")
    print(f"[NEWTON_CLIP_ROUTING] URDF: {FRANKA_URDF}")
    print(f"[NEWTON_CLIP_ROUTING] Architecture: MuJoCo-only (robot PD + BALL joint cable + contacts)")
    print(f"[NEWTON_CLIP_ROUTING] IK: Newton IKSolver (LM)")
    print(f"[NEWTON_CLIP_ROUTING] Cable: {'ON' if use_cable else 'OFF'}")
    print(f"[NEWTON_CLIP_ROUTING] Coordinates (body6 Z / fingertip Z):")
    print(f"  EE_TO_FINGERTIP: {EE_TO_FINGERTIP*1000:.0f}mm")
    print(f"  Approach: body6={APPROACH_Z:.3f} fingertip={APPROACH_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Grasp:    body6={GRASP_Z:.3f} fingertip={GRASP_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Lift:     body6={LIFT_Z:.3f} fingertip={LIFT_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Push:     body6={PUSH_Z:.3f} fingertip={PUSH_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Table:    {TABLE_HEIGHT:.3f}")
    print(f"  L_Y={WIDE_LEFT_Y}, R_Y={WIDE_RIGHT_Y}")
    print(f"  Clip1: ({CLIP1_X}, {CLIP1_Y}, {CLIP1_Z})")
    print()

    # Build scene (single model — MuJoCo handles everything)
    print("[BUILD] Building scene...")
    scene_info = build_scene(use_cable=use_cable)
    model = scene_info["model"]
    cable_bodies = scene_info.get("cable_bodies", [])

    # Build robot-only model for IK (avoids IK solver optimizing cable joints)
    print("[BUILD] Building IK model...")
    ik_model = build_ik_model()
    scene_info["ik_model"] = ik_model

    # Initialize state
    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    control = model.control()

    # Create CollisionPipeline — plain SDF (pattern: example_nut_bolt_sdf.py)
    # No hydroelastic. SDF on finger MESHes enables MESH-CAPSULE narrowphase.
    global _collision_pipeline
    model.rigid_contact_max = NJMAX
    collision_pipeline = newton.CollisionPipeline(
        model,
        reduce_contacts=True,
        rigid_contact_max=NJMAX,
        broad_phase="sap",
    )
    _collision_pipeline = collision_pipeline
    contacts = collision_pipeline.contacts()
    print(f"  [COLLISION] CollisionPipeline created (plain SDF, broad_phase=sap, "
          f"rigid_contact_max={NJMAX})")

    # Create MuJoCo solver with external contacts (CollisionPipeline provides them)
    # Pattern: example_nut_bolt_sdf.py — use_mujoco_contacts=False
    mujoco_iters = max(MUJOCO_ITERATIONS, 32)
    solver = SolverMuJoCo(
        model,
        use_mujoco_contacts=False,
        solver="newton",
        integrator="implicitfast",
        cone="elliptic",
        iterations=mujoco_iters,
        ls_iterations=MUJOCO_LS_ITERATIONS,
        njmax=NJMAX,
        nconmax=NJMAX,
        impratio=1000.0,
    )
    print(f"  [SOLVER] MuJoCo created (use_mujoco_contacts=False, solver=newton, "
          f"iterations={mujoco_iters}, njmax={NJMAX}, nconmax={NJMAX})")

    # Check collision graph coloring for finger-cable contact diagnosis
    shape_flags_arr = model.shape_flags.numpy()
    colliding_shapes = np.where(shape_flags_arr & newton.ShapeFlags.COLLIDE_SHAPES != 0)[0].astype(np.int32)
    shape_color = SolverMuJoCo._color_collision_shapes(model, colliding_shapes)
    shape_bodies_arr = model.shape_body.numpy()
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    for arm, bs in [("L", lb), ("R", rb)]:
        for local in [7, 8]:
            bi = bs + local
            sids = [si for si in colliding_shapes if shape_bodies_arr[si] == bi]
            if sids:
                print(f"  [COLOR] {arm} finger{local}: shapes={sids}, colors={[shape_color[s] for s in sids]}")
    if cable_bodies:
        cable_sids = [si for si in colliding_shapes if shape_bodies_arr[si] in cable_bodies[:3]]
        if cable_sids:
            print(f"  [COLOR] Cable[0:3]: shapes={cable_sids}, colors={[shape_color[s] for s in cable_sids]}")

    # Video recorder
    recorder = VideoRecorder(args.output_dir, model, enabled=args.record_video,
                             scene_info=scene_info)
    scene_info["recorder"] = recorder
    set_scene_colors(recorder, scene_info)

    # Raw evidence logger (independent verification channel for Code B)
    evidence = RawEvidenceLogger(args.output_dir)
    scene_info["evidence"] = evidence

    # Open fingers at start
    target_pos = control.joint_target_pos.numpy()
    for arm_start in [scene_info["left_j_start"], scene_info["right_j_start"]]:
        target_pos[arm_start + 7] = FINGER_OPEN_POS
        target_pos[arm_start + 8] = FINGER_OPEN_POS

    control.joint_target_pos.assign(target_pos)

    # Settle cable and stabilize arms (2s)
    print("[INIT] Settling (2s)...")
    settle_steps = int(2.0 / DT)
    nan_detected = False
    for i in range(settle_steps):
        state = physics_step(model, state, solver, control, contacts)

        # Early NaN detection (first 50 steps)
        if i < 50 and not nan_detected:
            bq = state.body_q.numpy()
            if np.any(np.isnan(bq)):
                nan_body = np.where(np.isnan(bq[:, 0]))[0]
                nc = contacts.rigid_contact_count.numpy()[0] if hasattr(contacts, 'rigid_contact_count') else -1
                print(f"  [NaN] Step {i}: NaN first in bodies {nan_body[:5]}... contacts={nc}")
                nan_detected = True

        if i % int(0.5 / DT) == 0:
            pos_l, pos_r = get_ee_positions(state, scene_info)
            cable_info = ""
            if cable_bodies:
                bq = state.body_q.numpy()
                cable_z = np.mean(bq[cable_bodies, 2])
                cable_info = f" cable_z={cable_z:.4f}"
            print(f"  settle t={i*DT:.1f}s: EE L=({pos_l[0]:.3f},{pos_l[1]:.3f},{pos_l[2]:.3f}) "
                  f"R=({pos_r[0]:.3f},{pos_r[1]:.3f},{pos_r[2]:.3f}){cable_info}")

    # Verify initial EE positions and measure actual EE_TO_FINGERTIP
    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(f"[INIT] Final EE: L=({pos_l[0]:.4f},{pos_l[1]:.4f},{pos_l[2]:.4f}) "
          f"R=({pos_r[0]:.4f},{pos_r[1]:.4f},{pos_r[2]:.4f})")

    # Diagnostic: actual body positions for EE_TO_FINGERTIP verification
    body_q = state.body_q.numpy()
    for arm, bs in [("L", scene_info["left_body_start"]), ("R", scene_info["right_body_start"])]:
        hand_z = body_q[bs + 6][2]
        f7_z = body_q[bs + 7][2]
        f8_z = body_q[bs + 8][2]
        print(f"[INIT] {arm} body Z: hand(b6)={hand_z:.4f}, finger7={f7_z:.4f}, finger8={f8_z:.4f}")
        print(f"[INIT] {arm} EE_TO_FINGER: b6-b7={((hand_z-f7_z)*1000):.1f}mm, "
              f"b6-b8={((hand_z-f8_z)*1000):.1f}mm (config={EE_TO_FINGERTIP*1000:.0f}mm)")

    # Check contacts after settle
    if _collision_pipeline is not None:
        _collision_pipeline.collide(state, contacts)
    else:
        solver.update_contacts(contacts)
    wp.synchronize()
    n_settle_contacts = contacts.rigid_contact_count.numpy()[0]
    print(f"[INIT] contacts after settle: {n_settle_contacts}")
    if cable_bodies:
        _check_contacts(solver, contacts, model, scene_info, "INIT-SETTLE", state=state)

    if cable_bodies:
        bq = state.body_q.numpy()
        cable_pos = bq[cable_bodies, :3]
        cable_z = np.mean(cable_pos[:, 2])
        cable_x = np.mean(cable_pos[:, 0])
        cable_x_std = np.std(cable_pos[:, 0])
        print(f"[INIT] Cable settled: mean_z={cable_z:.4f}, mean_x={cable_x:.4f} "
              f"(drift={((cable_x - GRASP_X)*1000):.1f}mm, std={cable_x_std*1000:.1f}mm)")
        scene_info["settled_grasp_x"] = float(cable_x)
    else:
        scene_info["settled_grasp_x"] = GRASP_X

    # Save settled state snapshot for episode reset (joint_q includes both robot + cable coords)
    settled_joint_q = state.joint_q.numpy().copy()
    settled_joint_qd = state.joint_qd.numpy().copy()

    # Per-episode perturbation RNG (None = deterministic, same as before)
    rng = np.random.RandomState(args.seed) if args.seed is not None else None
    if rng is not None:
        print(f"[PERTURB] Seed={args.seed}, cable joint perturbation per episode")

    # Run episodes
    all_results = {
        "test": "newton_clip_routing",
        "device": DEVICE,
        "dt": DT,
        "solver": "MuJoCo-only",
        "cable_model": "Capsule chain (BALL joints)",
        "ik": "Newton IKSolver LM",
        "cable": use_cable,
        "episodes": [],
        "n_pass": 0,
        "n_fail": 0,
    }

    start_time = time.time()

    for ep in range(args.num_episodes):
        print(f"\n{'='*60}")
        print(f"  EPISODE {ep+1}/{args.num_episodes}")
        print(f"{'='*60}")

        # Reset scene to settled state for each episode
        if ep > 0:
            state = model.state()
            state.joint_q.assign(settled_joint_q)
            state.joint_qd.assign(settled_joint_qd)
            newton.eval_fk(model, state.joint_q, state.joint_qd, state)

            # Reset control targets (open fingers)
            target_pos = control.joint_target_pos.numpy()
            robot_dofs = scene_info["robot_joint_dof_count"]
            target_pos[:robot_dofs] = settled_joint_q[:robot_dofs]
            for arm_start in [scene_info["left_j_start"], scene_info["right_j_start"]]:
                target_pos[arm_start + 7] = FINGER_OPEN_POS
                target_pos[arm_start + 8] = FINGER_OPEN_POS
            control.joint_target_pos.assign(target_pos)

            print(f"  [RESET] Scene restored to settled state")

        recorder.reset()

        try:
            state, ep_result = run_episode(model, state, scene_info, solver,
                                           control, contacts, ep)
        except Exception as e:
            print(f"\n  [ERROR] Episode {ep+1} crashed: {e}")
            import traceback
            traceback.print_exc()
            ep_result = {"episode": ep, "overall": "CRASH", "error": str(e)}

        # Finalize video for this episode (returns list of per-camera MP4 paths)
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

    # Close evidence logger
    evidence.close()

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(all_results, f, indent=2, default=json_default)

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  Pass rate: {all_results['pass_rate']}")
    print(f"  Overall: {all_results['overall']}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Metrics: {metrics_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
