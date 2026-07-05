# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton Phase 8: Franka Dual-Arm Cable Clip Routing (1 Clip) — VBD Rod Architecture

Ports test_clip_routing.py (PhysX/Isaac Sim 5.1) to Newton.
Architecture: VBD solver with Cosserat Rod cable + kinematic robot bodies.
Cable = add_rod() capsule bodies connected by CABLE joints (EI material bend stiffness).
Robot = kinematic bodies (positions from FK model). No REVOLUTE/PRISMATIC joints in physics model.
VBD handles cable dynamics (CABLE joints). Robot bodies updated each step from FK computation.
Contacts: model.collide() with BOX-CAPSULE narrowphase (finger-cable).
IK: Newton IKSolver (Levenberg-Marquardt) on separate FK model with IKObjectiveJointLimit.

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

import newton
import numpy as np
import trimesh
import warp as wp
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver
from newton.solvers import SolverMuJoCo
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
    APPROACH_Z,
    ARM_DOF,
    BODIES_PER_ARM,
    CABLE_BEND_DAMPING,
    CABLE_BEND_STIFFNESS,
    CABLE_CONTACT_KD,
    CABLE_CONTACT_KE,
    CABLE_CONTACT_MU,
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CABLE_STRETCH_DAMPING,
    CABLE_STRETCH_STIFFNESS,
    CLIP_GROOVE_INNER_RADIUS,
    CLIP_X,
    EE_BODY_OFFSET,
    EE_TO_FINGERTIP,
    EE_TO_PINCH_TIP_CLOSED,
    FINGER_CLOSE_POS,
    FINGER_CLOSE_STEPS,
    FINGER_OPEN_POS,
    FRANKA_NUM_JOINTS,
    GRASP_X,
    GRASP_Z,
    GRIPPER_CLOSE_QPOS,
    GRIPPER_DRIVER_CLOSE_RAD,
    GRIPPER_DRIVER_EFFORT_LIMIT_NM,
    GRIPPER_DRIVER_HALF_OPEN_RAD,
    # R-S6.6 (S6_GRASP actuated grasp, env-gated): gripper POSITION-driver + S5 contact-family SSOT.
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_JOINT_RANGE,
    GRIPPER_PAD_BODY_IDX,
    GRIPPER_SERVO_TARGET_KD,
    GRIPPER_SERVO_TARGET_KE,
    GROOVE_BODIES_MIN,
    GROOVE_CENTER_Z,
    JOINTS_PER_ARM,
    LIFT_Z,
    MAX_MOVE_STEPS,
    MUJOCO_CONTACT_CONDIM,
    MUJOCO_CONTACT_KD,
    MUJOCO_CONTACT_KE,
    MUJOCO_PAD_ROLL_FRICTION,
    MUJOCO_PAD_SOLREF,
    N_ARM_BODIES,
    NJMAX,
    P3_X_OFFSET,
    PUSH_Z,
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    SETTLE_STEPS,
    SIM_SUBSTEPS,
    SOLVER_BACKEND,
    STEPS_PER_CM,
    TABLE_HEIGHT,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

# ---------------------------------------------------------------------------
# Constants (non-tunable)
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0  # Frame dt (outer step)
SIM_DT = DT / SIM_SUBSTEPS  # Solver dt (inner substep)
GRAVITY = -9.81
VBD_ITERATIONS = 20  # VBD constraint solver iterations per substep

# Clip position — from task_config SSOT
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z, CLIP_POSITIONS

# Franka
FRANKA_URDF = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "source",
        "extensions",
        "isaaclab_tasks_thread",
        "data",
        "robots",
        "panda_independent_fingers.urdf",
    )
)

# UR5e + Robotiq 2f85 (Option-E substrate, S1 assets) — S2a FK/scene source.
_UR5E_ASSET = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "assets",
        "ur5e_robotiq",
    )
)
UR5E_XML = os.path.join(_UR5E_ASSET, "ur5e", "ur5e.xml")
ROBOTIQ_XML = os.path.join(_UR5E_ASSET, "robotiq_2f85", "2f85.xml")
# Path-A (Option-E Opt-1): 2f85 with the <tendon> node removed so the combined add_mjcf build
# constructs under SolverMuJoCo (the WITH-tendon build OOBs _init_tendons). <equality> is dropped at
# parse via skip_equality_constraints. Faithful 4-bar = S5. ◇→コ swap (R-S7.1, Rs override 2026-06-23):
# now the コ-shape (C-bracket) finger asset; the ◇ V-groove is DISCARDED (LEDGER:50/51, INVARIANT 4).
ROBOTIQ_STRIPPED_XML = os.path.join(_UR5E_ASSET, "robotiq_2f85", "2f85_koshape.xml")
# UR5e wrist_3 attachment_site (ur5e.xml) — Robotiq base mounts here. MuJoCo quat (w, x, y, z).
UR5E_ATTACH_POS = (0.0, 0.1, 0.0)
UR5E_ATTACH_QUAT_MJCF_WXYZ = (-1.0, 1.0, 0.0, 0.0)


def mjcf_wxyz_to_wp(w, x, y, z):
    """Convert a MuJoCo quat (w, x, y, z) to a normalized warp ``wp.quat`` (x, y, z, w)."""
    n = float(np.linalg.norm([w, x, y, z]))
    return wp.quat(x / n, y / n, z / n, w / n)


def _geo_type_name(t):
    """Map a Newton shape geo-type int to its name (e.g. ``CAPSULE`` / ``CYLINDER`` / ``SPHERE``)."""
    gt = getattr(newton, "GeoType", None) or getattr(newton, "GeometryType", None)
    if gt is not None:
        try:
            return gt(int(t)).name
        except Exception:
            return str(int(t))
    return str(int(t))


def add_ur5e_robotiq(builder, base_xform, robotiq_xml=ROBOTIQ_XML, skip_equality_constraints=False):
    """Assemble one UR5e arm + Robotiq 2f85 gripper into ``builder`` at ``base_xform``.

    UR5e is fixed-based at ``base_xform``; the Robotiq gripper attaches via a fixed base
    joint to the UR5e ``wrist_3`` body at the ``attachment_site`` frame (``parent_body`` +
    ``floating=False`` = the documented Newton hierarchical-composition path). ``collapse_
    fixed_joints=True`` / ``parse_meshes=False`` reproduce the S1-derived production index
    space (14 bodies == 14 joints per arm, ``wrist_3`` = EE local index 5). Returns the
    ``wrist_3`` body index (absolute, in ``builder``).

    ``robotiq_xml`` selects the gripper MJCF (default the full 2f85; Path-A passes the tendon-stripped
    variant); ``skip_equality_constraints`` is forwarded to :meth:`add_mjcf` to drop the 4-bar
    ``<equality>`` at parse (the stripped Path-A build that constructs under SolverMuJoCo).
    """
    b0 = len(builder.body_mass)
    builder.add_mjcf(
        UR5E_XML,
        xform=base_xform,
        floating=False,
        collapse_fixed_joints=True,
        enable_self_collisions=False,
        parse_meshes=False,
    )
    body_key = list(getattr(builder, "body_label", None) or getattr(builder, "body_key", None) or [])
    n_now = len(builder.body_mass)
    wrist3 = next(
        (i for i in range(b0, n_now) if i < len(body_key) and "wrist_3" in str(body_key[i])),
        b0 + EE_BODY_OFFSET,
    )
    builder.add_mjcf(
        robotiq_xml,
        parent_body=wrist3,
        floating=False,
        xform=wp.transform(wp.vec3(*UR5E_ATTACH_POS), mjcf_wxyz_to_wp(*UR5E_ATTACH_QUAT_MJCF_WXYZ)),
        collapse_fixed_joints=True,
        enable_self_collisions=False,
        parse_meshes=False,
        skip_equality_constraints=skip_equality_constraints,
    )
    return wrist3


# Body indices in the model (per arm, relative to arm's first body)
# Body 6 = panda_hand (flange), Body 7/8 = finger links

# VESTIGIAL post-de-Franka (S2): HAND_OFFSET_Z/RZ are unused after the Franka claw/hand
# construction was removed in S2a (grep-confirmed: no remaining references). UR5e EE = wrist_3
# (body 5), no hand-offset. Safe to remove; kept flagged (S2c). [Franka-legacy]
# Collapsed fixed-joint offsets (link7 → link8 → hand)
HAND_OFFSET_Z = 0.107  # link7 → link8 (panda_joint8 xyz)
HAND_OFFSET_RZ = -0.785398163397  # link8 → hand (panda_hand_joint rpy)

# IK
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0

# Contact detection: model.collide() (BOX-CAPSULE narrowphase)

# (Motion & Finger parameters imported from task_config)

# Video — per-camera MP4 (matches PhysX test_clip_routing.py camera positions)
VIDEO_FPS = 30
VIDEO_CAPTURE_EVERY = 16  # Capture every N physics steps (480/16=30fps)
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960

# Camera definitions: (name, position, target)
# v3.1: clip_close lowered to groove-level profile, diag_upper shifted +Y to reduce R-arm occlusion
CAMERAS = [
    ("overhead", (0.35, -0.05, 2.20), (0.35, -0.05, 0.82)),  # top-down: XY overview (Z=2.2 for full workspace FOV)
    ("front", (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),  # +X→-X: Z-height, table penetration
    ("diag_upper", (0.65, -0.40, 1.00), (0.35, -0.05, 0.82)),  # 45° upper: shifted +Y to reduce R-arm occlusion
    ("left", (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),  # -Y→+Y: closer & lower (table+13cm)
    ("right", (0.35, 0.55, 0.93), (0.35, -0.05, 0.82)),  # +Y→-Y: closer & lower (table+13cm)
    (
        "clip_close",
        (0.50, -0.05, 0.83),
        (0.35, -0.05, 0.82),
    ),  # groove-level profile: horizontal view of groove insertion
]

# On-hand camera: local offsets in body 6 (link7/panda_hand) frame.
# Mounted at 7th-axis rotation point, moves with fingers.
# ~45° diagonal view of finger clamp area (opening/closing visible).
# Body 6 frame: Z toward fingertips, Y = finger open/close axis.
# NOTE: Must match eval_skill.py ONHAND_LOCAL_OFFSET/TARGET.
ONHAND_LOCAL_OFFSET = np.array([0.05, 0.05, 0.10])  # 5cm X, 5cm Y, 10cm along Z
ONHAND_LOCAL_TARGET = np.array([0.0, 0.0, 0.17])  # finger mid-area (EE_TO_FINGERTIP≈0.22)

import math as _math


def _cam_angles(pos, tgt):
    """Compute (pitch_deg, yaw_deg) for ViewerGL.set_camera from pos→target."""
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = _math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm < 1e-9 or _math.isnan(norm):
        return 0.0, 0.0
    pitch = _math.degrees(_math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = _math.degrees(_math.atan2(dy, dx))
    return pitch, yaw


def _quat_rotate_np(q_xyzw, v):
    """Rotate vector v by quaternion q (xyzw convention)."""
    qx, qy, qz, qw = q_xyzw[0], q_xyzw[1], q_xyzw[2], q_xyzw[3]
    u = np.array([qx, qy, qz])
    t = 2.0 * np.cross(u, v)
    return v + qw * t + np.cross(u, t)


# ---------------------------------------------------------------------------
# Video recorder — per-camera MP4 (5 separate files)
# ---------------------------------------------------------------------------
class VideoRecorder:
    """Records per-camera MP4 videos from Newton ViewerGL headless.

    Generates separate MP4 files, one per camera (640×480 each).
    Matches PhysX FrameRecorder output format for /video-analyzer compatibility.
    Also records per-frame z-heights for computational pre-checks (Code C).
    Supports on-hand cameras that track body 6 (link7/panda_hand) per arm.
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
        # On-hand dynamic cameras: [(name, body_index)]
        self._onhand_cams = []
        # Z-height ground truth for Code C computational pre-checks
        self._zheight_frames = []
        self._scene_info = scene_info
        # Cumulative video encoding time (D3: separate from sim time)
        self.total_encode_s = 0.0
        # Finger visual mesh for explicit rendering via log_shapes
        self._finger_mesh = None
        self._finger_body_indices = []  # [(body_idx, mesh_xf), ...]
        if not enabled:
            return
        self.viewer = ViewerGL(
            width=VIDEO_CAM_W,
            height=VIDEO_CAM_H,
            vsync=False,
            headless=True,
        )
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        # Rod cable uses rigid body capsules (no particles to show)
        for name, pos, tgt in CAMERAS:
            pitch, yaw = _cam_angles(pos, tgt)
            self._cam_params.append((name, wp.vec3(*pos), pitch, yaw))
            self._cam_frames[name] = []
        # On-hand cameras: track left/right hand body
        if scene_info is not None:
            lb = scene_info["left_body_start"]
            rb = scene_info["right_body_start"]
            self._onhand_cams = [
                ("hand_L", lb + EE_BODY_OFFSET),
                ("hand_R", rb + EE_BODY_OFFSET),
            ]
            for name, _ in self._onhand_cams:
                self._cam_frames[name] = []
        # Setup finger visual mesh rendering
        self._setup_finger_visuals(scene_info)
        n_static = len(CAMERAS)
        n_onhand = len(self._onhand_cams)
        print(
            f"  [VIDEO] Per-camera recorder initialized "
            f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {n_static} static"
            f"{f' + {n_onhand} on-hand' if n_onhand else ''}"
            f" = {n_static + n_onhand} cameras)"
        )

    def _setup_finger_visuals(self, scene_info):
        """Load finger.dae mesh for explicit rendering via viewer.log_shapes."""
        if scene_info is None:
            print("  [VIDEO] finger visuals: scene_info=None, skipping")
            return
        arm_meshes = _load_arm_meshes()
        if 7 not in arm_meshes:
            print("  [VIDEO] finger visuals: no mesh for body 7, skipping")
            return
        self._finger_mesh = arm_meshes[7][0]  # finger.dae newton.Mesh
        lb = scene_info["left_body_start"]
        rb = scene_info["right_body_start"]
        rot_180z = wp.quat_from_axis_angle(wp.vec3(0.0, 0.0, 1.0), np.pi)
        xf_id = wp.transform_identity()
        xf_180z = wp.transform(wp.vec3(0.0, 0.0, 0.0), rot_180z)
        self._finger_body_indices = [
            (lb + 7, xf_id),  # left finger 7
            (lb + 8, xf_180z),  # left finger 8 (180° Z)
            (rb + 7, xf_id),  # right finger 7
            (rb + 8, xf_180z),  # right finger 8 (180° Z)
        ]
        print(
            f"  [VIDEO] finger visuals: mesh verts={self._finger_mesh.vertices.shape}, "
            f"bodies={[bi for bi, _ in self._finger_body_indices]}"
        )

    def capture(self, state):
        """Capture one frame per camera + z-height ground truth (call every physics step)."""
        if not self.enabled or self.viewer is None:
            return
        self.step_count += 1
        self.sim_time += DT
        if self.step_count % VIDEO_CAPTURE_EVERY != 0:
            return
        # RGB capture — static cameras
        for name, pos, pitch, yaw in self._cam_params:
            self.viewer.set_camera(pos, pitch, yaw)
            self.viewer.begin_frame(self.sim_time)
            self.viewer.log_state(state)
            # Render finger visual DAE meshes explicitly
            self._render_finger_visuals(state)
            self.viewer.end_frame()
            frame = self.viewer.get_frame().numpy().copy()
            self._cam_frames[name].append(frame)
        # RGB capture — on-hand dynamic cameras
        if self._onhand_cams:
            body_q = state.body_q.numpy()
            for name, body_idx in self._onhand_cams:
                bq = body_q[body_idx]
                hand_pos = bq[:3]
                hand_quat = bq[3:7]  # xyzw
                cam_pos = hand_pos + _quat_rotate_np(hand_quat, ONHAND_LOCAL_OFFSET)
                cam_tgt = hand_pos + _quat_rotate_np(hand_quat, ONHAND_LOCAL_TARGET)
                pitch, yaw = _cam_angles(cam_pos, cam_tgt)
                self.viewer.set_camera(wp.vec3(*cam_pos), pitch, yaw)
                self.viewer.begin_frame(self.sim_time)
                self.viewer.log_state(state)
                self._render_finger_visuals(state)
                self.viewer.end_frame()
                frame = self.viewer.get_frame().numpy().copy()
                self._cam_frames[name].append(frame)
        # Z-height ground truth capture (no GPU contention — reads state only)
        self._capture_zheights(state)

    def _render_finger_visuals(self, state):
        """Render finger.dae meshes via log_shapes (bypassing log_state issue)."""
        if self._finger_mesh is None or not self._finger_body_indices:
            return
        body_q = state.body_q.numpy()
        xforms = []
        for body_idx, mesh_xf in self._finger_body_indices:
            bq = body_q[body_idx]
            body_pos = wp.vec3(float(bq[0]), float(bq[1]), float(bq[2]))
            body_rot = wp.quat(float(bq[3]), float(bq[4]), float(bq[5]), float(bq[6]))
            body_xf = wp.transform(body_pos, body_rot)
            # Compose body transform with mesh transform (identity or 180° Z rotation)
            final_xf = wp.transform_multiply(body_xf, mesh_xf)
            xforms.append(final_xf)
        xforms_wp = wp.array(xforms, dtype=wp.transform, device=DEVICE)
        # DEBUG: bright green for finger visual
        colors = wp.array(
            [wp.vec3(0.0, 1.0, 0.0)] * len(xforms),
            dtype=wp.vec3,
            device=DEVICE,
        )
        # Note: log_shapes after log_state doesn't render in ViewerGL.
        # With BOX collision shapes, visual MESH renders normally via log_state.
        # This method is kept as a no-op placeholder.
        pass

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
        """Encode per-camera frames to separate MP4 files + save z-heights.

        Returns list of video paths. Tracks encoding time in
        ``self.total_encode_s`` for timing separation (D3 fix).
        """
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

        _enc_t0 = time.time()
        video_paths = []
        # Collect all camera names (static + on-hand)
        all_cam_names = [name for name, _, _, _ in self._cam_params]
        all_cam_names.extend([name for name, _ in self._onhand_cams])
        for name in all_cam_names:
            frames = self._cam_frames.get(name, [])
            if not frames:
                continue
            frames_dir = os.path.join(self.output_dir, f"frames_ep{episode_idx}_{name}")
            os.makedirs(frames_dir, exist_ok=True)
            for i, f in enumerate(frames):
                Image.fromarray(f).save(os.path.join(frames_dir, f"frame_{i:05d}.png"))

            video_path = os.path.join(self.output_dir, f"ep{episode_idx}_{name}.mp4")
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate",
                str(VIDEO_FPS),
                "-i",
                os.path.join(frames_dir, "frame_%05d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "23",
                video_path,
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

        _enc_elapsed = time.time() - _enc_t0
        self.total_encode_s += _enc_elapsed
        print(
            f"  [VIDEO] Saved {len(video_paths)} camera videos "
            f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {n_frames} frames each, "
            f"encode={_enc_elapsed:.1f}s)"
        )
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

    def check_penetration(self):
        """Check accumulated z-height frames for fingertip table penetration.

        Returns dict with 'penetration_detected', 'max_penetration_mm',
        and 'penetration_pct' (percentage of frames with penetration).
        Returns None if no z-height data available.
        """
        if not self._zheight_frames:
            return None
        table_z = float(TABLE_HEIGHT)
        max_pen = 0.0
        pen_count = 0
        for frame in self._zheight_frames:
            found = False
            for key in ("left_finger_z", "right_finger_z"):
                if found:
                    break
                for fz in frame.get(key, []):
                    depth = table_z - fz
                    if depth > 0:
                        pen_count += 1
                        max_pen = max(max_pen, depth)
                        found = True
                        break  # one finger per frame is enough
        n = len(self._zheight_frames)
        return {
            "penetration_detected": pen_count > 0,
            "max_penetration_mm": round(max_pen * 1000, 2),
            "penetration_pct": round(100 * pen_count / n, 1) if n else 0,
            "frames_checked": n,
        }

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
COLOR_FINGER = (1.0, 0.2, 0.2)  # RED — highest priority for table-penetration detection
COLOR_TABLE = (0.65, 0.50, 0.35)  # TAN/BROWN — distinct from white/gray defaults
COLOR_HAND = (0.3, 0.3, 0.6)  # BLUE-GRAY — distinguish hand body from fingers
COLOR_ARM = (0.9, 0.9, 0.9)  # WHITE — Franka Panda standard color
COLOR_CLIP = (0.2, 0.7, 0.3)  # GREEN — clip V-groove (C1)
COLOR_CLIP2 = (0.1, 0.7, 0.9)  # CYAN — second clip C2 (Rs C1->C2 routing directive)


def set_scene_colors(recorder, scene_info):
    """Set per-shape colors so fingers/table/clip are visually distinct in video.

    Uses model.body_label + model.shape_body to map robot body names to shape
    indices.  Table and clip use explicit indices tracked in build_scene().
    """
    if not recorder.enabled or recorder.viewer is None:
        return
    model = scene_info["model"]
    shape_colors = {}

    # Robot shapes: identify via body index (local_body 0-5=arm, 6=hand, 7/8=finger)
    shape_body = model.shape_body.numpy()
    robot_body_count = scene_info.get("robot_body_count", 18)
    for s_idx in range(len(shape_body)):
        body_idx = int(shape_body[s_idx])
        if body_idx < 0:
            continue  # world-attached (table, clip) — handled below
        if body_idx >= robot_body_count:
            continue  # cable body
        # Franka-legacy finger filter; build_scene is script/smoke, not the RL path (S2); see S2_DEFERRED_OBLIGATIONS.md
        local_body = body_idx % FRANKA_NUM_JOINTS
        if local_body in (7, 8):
            shape_colors[s_idx] = COLOR_FINGER
        elif local_body == 6:
            shape_colors[s_idx] = COLOR_HAND
        elif local_body <= 5:
            shape_colors[s_idx] = COLOR_ARM

    # Table (world-attached, explicit index from build_scene)
    table_idx = scene_info.get("table_shape_idx")
    if table_idx is not None:
        for ti in table_idx:  # table_shape_idx is a LIST (1 box = solid; 2 = WIDE-VOID slot)
            shape_colors[ti] = COLOR_TABLE

    # Clip V-groove parts (world-attached, explicit indices)
    for clip_idx in scene_info.get("clip_shape_indices", []):
        shape_colors[clip_idx] = COLOR_CLIP
    for clip_idx in scene_info.get("clip2_shape_indices", []):  # C2 (Rs C1->C2 routing): cyan, distinct from C1 green
        shape_colors[clip_idx] = COLOR_CLIP2

    if shape_colors:
        recorder.viewer.update_shape_colors(shape_colors)
        n_arm = sum(1 for c in shape_colors.values() if c == COLOR_ARM)
        n_finger = sum(1 for c in shape_colors.values() if c == COLOR_FINGER)
        n_hand = sum(1 for c in shape_colors.values() if c == COLOR_HAND)
        print(
            f"  [VIDEO] Scene colors: {n_arm} arm(white), {n_hand} hand(blue-gray), "
            f"{n_finger} finger(red), 1 table(tan), "
            f"{len(scene_info.get('clip_shape_indices', []))} clip(green)"
        )


# ---------------------------------------------------------------------------
# Scene builder
# ---------------------------------------------------------------------------
# _load_finger_mesh() removed (Option-E S2a): Franka V-groove finger collision mesh,
# dead in this file (no live caller; the de-Franka scene builds no Franka finger geometry).


def _load_arm_meshes():
    """Load Franka arm link visual meshes (DAE) for high-quality rendering.

    Uses COLLADA (.dae) visual meshes instead of collision STL for smooth,
    high-polygon rendering matching Franka Panda CAD quality.

    Maps local_body index to newton.Mesh objects.
    collapse_fixed_joints=True merges link0→world, hand→link7.
    So: local_body 0=link1, 1=link2, ..., 5=link6, 6=link7+hand.
    """
    if not hasattr(_load_arm_meshes, "_cache"):
        visual_dir = os.path.join(
            os.path.dirname(FRANKA_URDF),
            "franka_description",
            "meshes",
            "visual",
        )
        cache = {}

        def _load_dae(dae_path):
            """Load a DAE file via trimesh, return newton.Mesh."""
            tm = trimesh.load(dae_path, force="mesh")
            verts = np.array(tm.vertices, dtype=np.float32)
            faces = np.array(tm.faces, dtype=np.int32).flatten()
            return newton.Mesh(verts, faces), len(tm.vertices), len(tm.faces)

        total_verts = 0
        # local_body 0-5 → link1-link6
        for local_body in range(6):
            dae_name = f"link{local_body + 1}.dae"
            dae_path = os.path.join(visual_dir, dae_name)
            if os.path.exists(dae_path):
                mesh, nv, nf = _load_dae(dae_path)
                cache[local_body] = [mesh]
                total_verts += nv

        # local_body 6 → link7 + hand (collapsed fixed joint)
        meshes_6 = []
        for dae_name in ("link7.dae", "hand.dae"):
            dae_path = os.path.join(visual_dir, dae_name)
            if os.path.exists(dae_path):
                mesh, nv, nf = _load_dae(dae_path)
                meshes_6.append(mesh)
                total_verts += nv
        if meshes_6:
            cache[6] = meshes_6

        # local_body 7, 8 → finger visual (finger.dae)
        # Collision uses BOX primitives (added in add_kinematic_arm), not mesh.
        finger_dae = os.path.join(visual_dir, "finger.dae")
        if os.path.exists(finger_dae):
            tm = trimesh.load(finger_dae, force="mesh")
            verts = np.array(tm.vertices, dtype=np.float32)
            faces = np.array(tm.faces, dtype=np.int32).flatten()
            # Visual mesh: original size
            finger_vis = newton.Mesh(verts, faces)
            nv, nf = len(tm.vertices), len(tm.faces)
            cache[7] = [finger_vis]
            cache[8] = [finger_vis]
            # Finger mesh bounding box for BOX collision shape positioning
            cache["finger_bounds"] = {
                "min": verts.min(axis=0),
                "max": verts.max(axis=0),
            }
            total_verts += nv
            fb_min, fb_max = cache["finger_bounds"]["min"], cache["finger_bounds"]["max"]
            print(
                f"  [MESH] Finger visual: {nv:,} verts, {nf:,} faces"
                f" (bounds Y=[{fb_min[1]:.4f},{fb_max[1]:.4f}] "
                f"Z=[{fb_min[2]:.4f},{fb_max[2]:.4f}])"
            )

        _load_arm_meshes._cache = cache
        total_meshes = sum(len(v) for v in cache.values() if isinstance(v, list))
        print(
            f"  [MESH] Loaded {total_meshes} visual DAE meshes for {len(cache)} bodies ({total_verts:,} total vertices)"
        )
    return _load_arm_meshes._cache


def add_kinematic_arm(builder, fk_model, fk_state, arm_body_offset, label_prefix="arm"):
    """Add one UR5e+Robotiq arm as kinematic bodies to the physics builder (Option-E S2a).

    Creates BODIES_PER_ARM (14) kinematic bodies (no joints — VBD supports none); their
    positions are updated each step from the FK model body_q. Arm bodies 0-5 carry the UR5e
    collision primitives REPLICATED from the swapped fk_model, set VISIBLE-only (the kinematic
    arm has no collision role; matches the de-Franka scene). Gripper bodies 6-13 are bare —
    the faithful Robotiq pad collision is built once, correctly, at S5 (the 4-bar cannot be
    posed closed by FK/VBD; closing needs the MuJoCo solver). De-Franka: no Franka claw boxes,
    no Franka DAE meshes, no fallback capsule.

    Args:
        fk_model: swapped UR5e+Robotiq FK model (dual-arm) — source of body poses and the
            arm collision primitives to replicate.
        fk_state: FK state with body_q computed via eval_fk.
        arm_body_offset: body index offset in the dual FK model (0 for left, JOINTS_PER_ARM for right).
        label_prefix: "left" or "right" for body labels.

    Returns (body_start, shape_start, shape_end, finger_visual_indices). finger_visual_indices
    is always [] (no Franka finger DAE in the UR5e substrate; kept for the 4-tuple contract).
    """
    body_start = len(builder.body_mass)
    shape_start = builder.shape_count
    finger_visual_indices = []

    fk_body_q = fk_state.body_q.numpy()

    # Arm-shape visual config (no collision contribution; flags forced VISIBLE below).
    arm_cfg = newton.ModelBuilder.ShapeConfig()
    arm_cfg.density = 0.0
    arm_cfg.gap = 0.0

    # 1. Kinematic bodies (one per robot body, posed from FK; inv_mass zeroed after finalize).
    scene_body_ids = []
    for local_body in range(BODIES_PER_ARM):
        bq = fk_body_q[arm_body_offset + local_body]
        # body_q format: [x, y, z, qx, qy, qz, qw]
        xform = wp.transform(
            wp.vec3(float(bq[0]), float(bq[1]), float(bq[2])),
            wp.quat(float(bq[3]), float(bq[4]), float(bq[5]), float(bq[6])),
        )
        body_id = builder.add_link(
            xform=xform,
            mass=100.0,
            is_kinematic=True,
            label=f"{label_prefix}_body{local_body}",
        )
        scene_body_ids.append(body_id)

    # 2. Replicate the UR5e arm collision primitives (fk bodies [arm_body_offset .. +N_ARM_BODIES))
    #    onto the kinematic arm bodies as VISIBLE-only (Delta-H2). Gripper bodies 6-13 stay BARE
    #    (Delta-H4: faithful Robotiq pad geometry deferred to S5). Per-arm remap (Delta-MED): select
    #    THIS arm's fk shapes (offset 0 / JOINTS_PER_ARM) and remap fk body -> scene-local index.
    fk_shape_body = fk_model.shape_body.numpy()
    fk_shape_type = fk_model.shape_type.numpy()
    fk_shape_scale = fk_model.shape_scale.numpy()
    fk_shape_xform = fk_model.shape_transform.numpy()
    fk_shape_flags = fk_model.shape_flags.numpy()
    n_arm_shapes = 0
    for si in range(len(fk_shape_body)):
        local = int(fk_shape_body[si]) - arm_body_offset
        if local < 0 or local >= N_ARM_BODIES:
            continue  # only UR5e arm bodies 0..5 of THIS arm (gripper bare; other arm skipped)
        if int(fk_shape_flags[si]) == 8:
            continue  # skip non-load-bearing MJCF site markers (as_site spheres)
        gname = _geo_type_name(int(fk_shape_type[si]))
        scl = fk_shape_scale[si]
        xf = fk_shape_xform[si]
        local_xf = wp.transform(
            wp.vec3(float(xf[0]), float(xf[1]), float(xf[2])),
            wp.quat(float(xf[3]), float(xf[4]), float(xf[5]), float(xf[6])),
        )
        sb = scene_body_ids[local]
        if gname == "CAPSULE":
            sid = builder.add_shape_capsule(
                body=sb, xform=local_xf, radius=float(scl[0]), half_height=float(scl[1]), cfg=arm_cfg
            )
        elif gname == "CYLINDER":
            sid = builder.add_shape_cylinder(
                body=sb, xform=local_xf, radius=float(scl[0]), half_height=float(scl[1]), cfg=arm_cfg
            )
        elif gname == "SPHERE":
            sid = builder.add_shape_sphere(body=sb, xform=local_xf, radius=float(scl[0]), cfg=arm_cfg)
        else:
            continue  # unknown primitive — skip (visual-only; no collision role in S2)
        builder.shape_flags[sid] = 1  # VISIBLE only (strip COLLIDE — arm has no collision role)
        n_arm_shapes += 1

    shape_end = builder.shape_count
    print(
        f"  [ARM-{label_prefix}] {BODIES_PER_ARM} kinematic bodies (UR5e+Robotiq), "
        f"arm visual primitives={n_arm_shapes} (VISIBLE-only), gripper bare (pads=S5), "
        f"shapes=[{shape_start}:{shape_end}]"
    )

    return body_start, shape_start, shape_end, finger_visual_indices


def add_cable_rod(builder, start_pos, direction=(0, 1, 0)):
    """Add cable as Cosserat Rod via builder.add_rod() (VBD-native).

    Creates capsule bodies connected by CABLE joints (2 DOF: stretch + bend).
    Bend stiffness is EI material property (divided by segment length internally).
    VBD solver handles CABLE joint constraints iteratively.

    Returns (body_indices, joint_indices).
    """
    total_length = CABLE_SEGMENTS * CABLE_SEG_LEN
    n_points = CABLE_SEGMENTS + 1

    # Generate rod centerline positions (N+1 points for N segments)
    dir_np = np.array(direction, dtype=np.float64)
    dir_np = dir_np / np.linalg.norm(dir_np)
    positions = []
    for i in range(n_points):
        p = np.array(start_pos) + dir_np * (i * CABLE_SEG_LEN)
        positions.append(tuple(p))

    # Cable contact config
    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = CABLE_CONTACT_KE
    cable_cfg.kd = CABLE_CONTACT_KD
    cable_cfg.mu = CABLE_CONTACT_MU
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002  # 2mm contact gap
    cable_cfg.density = 1100.0  # Rubber cable density (kg/m³)

    body_ids, joint_ids = builder.add_rod(
        positions=positions,
        radius=CABLE_RADIUS,
        stretch_stiffness=CABLE_STRETCH_STIFFNESS,  # EA [N] (divided by L internally)
        stretch_damping=CABLE_STRETCH_DAMPING,
        bend_stiffness=CABLE_BEND_STIFFNESS,  # EI [N·m²] (divided by L internally)
        bend_damping=CABLE_BEND_DAMPING,
        cfg=cable_cfg,
    )

    seg_mass = cable_cfg.density * np.pi * CABLE_RADIUS**2 * CABLE_SEG_LEN
    print(
        f"  [CABLE] add_rod: {len(body_ids)} bodies, {len(joint_ids)} joints "
        f"(CABLE+FREE), EI={CABLE_BEND_STIFFNESS}, EA={CABLE_STRETCH_STIFFNESS}, "
        f"density={cable_cfg.density:.0f}, seg_mass={seg_mass * 1000:.1f}g, "
        f"total_length={total_length * 1000:.0f}mm"
    )

    return body_ids, joint_ids


# D-S4a-3 (S4a, MuJoCo path): MUJOCO_CONTACT_KE/KD now live in task_config (SSOT relocation,
# human-Rs-approved 2026-06-10; provenance + the convert_solref derivation are documented there).
# Cable bend spring (S4a probe-decided contract, S4_CYCLE4_DESIGN.md §C2): k = EI/L = 66.67
# N·m/rad DIRECT (Newton 1.2 #6) + the LOAD-BEARING real damping (B1) + straight rest.
# 0-COMMIT EI override (DIRECTION-A cable-flexibility probe, %3 2026-06-30; NOT committed to task_config):
# CABLE_BEND_STIFFNESS_OVERRIDE env var rescales EI [N·m²] at runtime for the active mujoco-コ revolute
# joint passive spring K = EI/CABLE_SEG_LEN (the only EI consumer on the mujoco branch, used at
# add_revolute_cable below). Unset/empty -> task_config CABLE_BEND_STIFFNESS (byte-identical). Lower EI =
# more flexible cable. The realistic Ø8 EI window is 1e-3..5e-2 (task_config:147-148).
_CABLE_EI_ACTIVE = float(os.environ.get("CABLE_BEND_STIFFNESS_OVERRIDE", "") or CABLE_BEND_STIFFNESS)
CABLE_MUJOCO_BEND_K = _CABLE_EI_ACTIVE / CABLE_SEG_LEN  # default 0.005/0.015 = 0.333 N·m/rad
if abs(_CABLE_EI_ACTIVE - CABLE_BEND_STIFFNESS) > 1e-12:
    print(
        f"  [EI-OVERRIDE] CABLE_BEND_STIFFNESS {CABLE_BEND_STIFFNESS:.4g} -> {_CABLE_EI_ACTIVE:.4g} N·m^2 "
        f"(CABLE_MUJOCO_BEND_K -> {CABLE_MUJOCO_BEND_K:.4f} N·m/rad)"
    )


def add_revolute_cable(builder, start_pos, direction=(0, 1, 0)):
    """Add cable as a rigid-link REVOLUTE capsule chain (SolverMuJoCo path, S4a D-S4a-1).

    MuJoCo rejects CABLE joints (solver_mujoco.py:292), so the mujoco branch rebuilds the cable
    as ``add_link`` capsule bodies (the ``add_rod`` layout: body at the start node, capsule
    spanning +Z, COM at the midpoint) chained by REVOLUTE joints with the probe-decided passive
    bend spring set via NAMESPACED MuJoCo custom attributes (S4_CYCLE4_DESIGN.md §C2 contract:
    k=66.67 N·m/rad, damping=CABLE_BEND_DAMPING — load-bearing, springref=0). The root is a
    FREE joint (both cable ends free; the MuJoCo requirement that every body has an incoming
    joint). ``SolverMuJoCo.register_custom_attributes`` is called here BEFORE the cable joints
    (builder.py:1327 raises otherwise); the FREE root + all segment joints are issued
    CONSECUTIVELY so the articulation joint-id range stays contiguous (builder.py:2160).

    Returns (body_indices, joint_indices, shape_range) — joint_indices[0] is the FREE root;
    shape_range is the half-open capsule shape index range for contact-filter loops.
    """
    n_points = CABLE_SEGMENTS + 1
    dir_np = np.array(direction, dtype=np.float64)
    dir_np = dir_np / np.linalg.norm(dir_np)
    positions = [np.array(start_pos) + dir_np * (i * CABLE_SEG_LEN) for i in range(n_points)]

    # Capsule local +Z must align with the segment direction (the add_rod layout convention).
    z_axis = np.array([0.0, 0.0, 1.0])
    cross = np.cross(z_axis, dir_np)
    cn = float(np.linalg.norm(cross))
    if cn < 1e-12:
        seg_q = wp.quat_identity() if dir_np[2] > 0 else wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), float(np.pi))
    else:
        angle = float(np.arccos(np.clip(np.dot(z_axis, dir_np), -1.0, 1.0)))
        axis = cross / cn
        seg_q = wp.quat_from_axis_angle(wp.vec3(*axis), angle)

    # MuJoCo-tuned contact (D-S4a-3): ke/kd → solref=(0.005, 1.0); mu/gap/density as the VBD cable.
    cable_cfg = newton.ModelBuilder.ShapeConfig()
    cable_cfg.ke = MUJOCO_CONTACT_KE
    cable_cfg.kd = MUJOCO_CONTACT_KD
    # CABLE_MU env override (S13_FEED fidelity sweep, 0-commit): paired with CLIP_MU so the clip↔cable
    # PAIR friction = the swept value despite MuJoCo's element-wise-MAX mixing. Unset/empty ->
    # CABLE_CONTACT_MU (byte-identical). NOTE: this is the cable's GLOBAL mu so it also lowers cable↔pad
    # (grasp) traction toward max(pad_mu≈0.7, value); held=True is precheck-verified before any feed read.
    cable_cfg.mu = float(os.environ.get("CABLE_MU", "") or CABLE_CONTACT_MU)
    cable_cfg.is_hydroelastic = False
    cable_cfg.gap = 0.002
    cable_cfg.density = 1100.0  # rubber cable (matches add_cable_rod)

    # The passive-spring fields are MuJoCo-solver custom JOINT_DOF attributes — register FIRST.
    SolverMuJoCo.register_custom_attributes(builder)

    half = CABLE_SEG_LEN / 2.0
    shape_start = builder.shape_count
    body_ids = []
    for e in range(CABLE_SEGMENTS):
        b = builder.add_link(xform=wp.transform(wp.vec3(*positions[e]), seg_q), com=wp.vec3(0.0, 0.0, half))
        builder.add_shape_capsule(
            b,
            xform=wp.transform(wp.vec3(0.0, 0.0, half), wp.quat_identity()),
            radius=CABLE_RADIUS,
            half_height=half,
            cfg=cable_cfg,
        )
        body_ids.append(b)
    shape_end = builder.shape_count

    # FREE root + segment REVOLUTE joints, CONSECUTIVE (contiguous ids for add_articulation).
    free_jid = builder.add_joint_free(child=body_ids[0], parent=-1)
    joint_ids = [free_jid]
    for e in range(1, CABLE_SEGMENTS):
        joint_ids.append(
            builder.add_joint_revolute(
                parent=body_ids[e - 1],
                child=body_ids[e],
                parent_xform=wp.transform(wp.vec3(0.0, 0.0, CABLE_SEG_LEN), wp.quat_identity()),
                child_xform=wp.transform(wp.vec3(0.0, 0.0, 0.0), wp.quat_identity()),
                axis=wp.vec3(1.0, 0.0, 0.0),  # local-X bend axis ⟂ cable → vertical sag plane
                collision_filter_parent=True,  # EXPLICIT (builder.py:3898; adjacent segments don't collide)
                custom_attributes={
                    "mujoco:dof_passive_stiffness": CABLE_MUJOCO_BEND_K,
                    "mujoco:dof_passive_damping": CABLE_BEND_DAMPING,
                    "mujoco:dof_springref": 0.0,
                },
            )
        )
    builder.add_articulation(joint_ids)

    seg_mass = cable_cfg.density * np.pi * CABLE_RADIUS**2 * CABLE_SEG_LEN
    print(
        f"  [CABLE] add_revolute_cable: {len(body_ids)} bodies, {len(joint_ids)} joints "
        f"(FREE+REVOLUTE), k={CABLE_MUJOCO_BEND_K:.2f} N·m/rad, damping={CABLE_BEND_DAMPING}, "
        f"springref=0, solref=({2.0 / MUJOCO_CONTACT_KD:.3f},1.0), seg_mass={seg_mass * 1000:.1f}g"
    )

    return body_ids, joint_ids, (shape_start, shape_end)


def build_scene(
    use_cable=True, fk_model=None, fk_state=None, solver_backend="vbd", grasp_actuation=False, grasp_y=None, cable_xy_offset=None
):
    """Build the full Newton scene for VBD Rod architecture.

    Kinematic robot bodies (positions from FK model, no joints).
    Cable: add_rod() Cosserat rod (CABLE joints, VBD-native).
    Table: BOX primitive. model.collide() for contacts.

    ``solver_backend`` (Option-E Opt-1, D-Opt1-1): ``"vbd"`` (default) = the jointless
    ``add_kinematic_arm`` build EXACTLY as before (byte-identical A/B control); ``"mujoco"`` =
    the articulated UR5e+Robotiq ``add_mjcf`` build (Robotiq ``<tendon>`` stripped) the STEP-1
    probe validated, with REAL arm masses (inv_mass NOT zeroed) and the cable/flag passes skipped.
    Uses the LOCAL ``solver_backend`` (not the task_config constant) so the guards can't diverge
    from the build (§28 #1).

    ``grasp_actuation`` (R-S6.6 CHANGE 2/3, S6_GRASP env-gate): default ``False`` keeps the build
    byte-identical; ``True`` (mujoco only) additively wires the gripper POSITION drivers + restores
    the 4-bar connect equalities + the build-time S5 contact families (condim=6 / rolling friction)
    so the gripper can dynamically GRASP the cable (the negative PAD_SOLREF is poked post-make_solver
    by :func:`_wire_s6_grasp_solref`).
    """
    builder = newton.ModelBuilder(gravity=GRAVITY)
    floor_shape_idx = builder.add_ground_plane()

    # Table: BOX primitive
    table_half = (0.35, 0.35, 0.005)
    table_cfg = newton.ModelBuilder.ShapeConfig()
    if solver_backend == "mujoco":
        # D-S4a-3: ke/kd → solref=(2/kd, (kd/2)√(1/ke)); the VBD-era 500/100 maps to the soft
        # MuJoCo default-ish (0.02, ζ≈2.2). MuJoCo mixes BOTH geoms' solref per contact, so the
        # table must be stiffened alongside the cable for the ≤~mm rest compression.
        table_cfg.ke = MUJOCO_CONTACT_KE
        table_cfg.kd = MUJOCO_CONTACT_KD
    else:
        table_cfg.ke = 500.0
        table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_cx, table_cy, table_cz = 0.3, -0.05, TABLE_HEIGHT - table_half[2]
    table_xform = wp.transform((table_cx, table_cy, table_cz), wp.quat_identity())
    # `table_idx` is ALWAYS a LIST of shape indices (1 box = solid; 2 boxes = WIDE-VOID slot). The 3
    # consumers (color :scene_info reader, ground_planes filter [VBD branch], scene_info store) handle a list.
    if grasp_actuation:
        # R-S7.1 (A) STEP 2: the grasp+lift needs a WIDE table VOID so the gripper's lower flanks reach UNDER
        # the cable. Split the table into 2 boxes with a slot under the grasps; the cable SPANS the void,
        # supported by table on BOTH Y-sides (no droop). Void Y = the WIDE grasps ± 16mm. Proven:
        # FAITHFUL_SLOT_15 48mm RIGHT-arm lift (D14 2-box). The void is CARVED from the real table extent
        # (Y_CEIL = table edge +0.30 for the CENTERED cable; D14's 0.50 was the old overhang-era extension).
        y_floor, y_ceil = table_cy - table_half[1], table_cy + table_half[1]  # [-0.40, +0.30]
        # void Y bracket: default (grasp_y=None) = the EXACT C1 expression (byte-identical -> preserves the
        # BANKED single-arm RIGHT C1 lift); grasp_y given (e.g. 0 = symmetric centered, R-S7.1 B) re-centers
        # the void on grasp_y with the SAME half-width (= GRIP_HALF_SPAN + 16mm).
        if grasp_y is None:
            slot_lo, slot_hi = WIDE_LEFT_Y - 0.016, WIDE_RIGHT_Y + 0.016  # [0.09, 0.21] under the C1 grasps
        else:
            void_half = (WIDE_RIGHT_Y - WIDE_LEFT_Y) / 2.0 + 0.016  # GRIP_HALF_SPAN + 16mm margin
            slot_lo, slot_hi = grasp_y - void_half, grasp_y + void_half
        cyl, hyl = (y_floor + slot_lo) / 2.0, (slot_lo - y_floor) / 2.0
        cyh, hyh = (slot_hi + y_ceil) / 2.0, (y_ceil - slot_hi) / 2.0
        # R-S7.1 (human 2026-06-20): localize the slot to the gripper X-extent, NOT the full table width.
        # Measured open-descend gripper footprint into the slot = X[0.249,0.351] (101mm) about GRASP_X=0.30.
        # Keep the void only at X[slot_x_lo, slot_x_hi] (±66mm = 51mm half-extent + 15mm clearance) and FILL the
        # void elsewhere with 2 more boxes (cable at X=0.30 still bridges the void Y-range; the gripper still
        # descends with 15mm/side X clearance). table_idx stays a LIST (now 4) -> the 3 consumers are list-safe.
        x_floor, x_ceil = table_cx - table_half[0], table_cx + table_half[0]  # [-0.05, 0.65]
        slot_x_lo, slot_x_hi = table_cx - 0.066, table_cx + 0.066  # [0.234, 0.366]
        cyv, hyv = (slot_lo + slot_hi) / 2.0, (slot_hi - slot_lo) / 2.0  # void Y center/half
        cxc, hxc = (x_floor + slot_x_lo) / 2.0, (slot_x_lo - x_floor) / 2.0  # -X void fill
        cxd, hxd = (slot_x_hi + x_ceil) / 2.0, (x_ceil - slot_x_hi) / 2.0  # +X void fill
        table_idx = [
            builder.add_shape_box(
                body=-1,
                hx=table_half[0],
                hy=hyl,
                hz=table_half[2],
                xform=wp.transform((table_cx, cyl, table_cz), wp.quat_identity()),
                cfg=table_cfg,
            ),
            builder.add_shape_box(
                body=-1,
                hx=table_half[0],
                hy=hyh,
                hz=table_half[2],
                xform=wp.transform((table_cx, cyh, table_cz), wp.quat_identity()),
                cfg=table_cfg,
            ),
            builder.add_shape_box(
                body=-1,
                hx=hxc,
                hy=hyv,
                hz=table_half[2],
                xform=wp.transform((cxc, cyv, table_cz), wp.quat_identity()),
                cfg=table_cfg,
            ),
            builder.add_shape_box(
                body=-1,
                hx=hxd,
                hy=hyv,
                hz=table_half[2],
                xform=wp.transform((cxd, cyv, table_cz), wp.quat_identity()),
                cfg=table_cfg,
            ),
        ]
        print(
            f"  [SCENE] Table → 4 boxes (S6_GRASP slot localized to gripper X, grasp_y={'C1-default' if grasp_y is None else grasp_y}): "
            f"-Y[{y_floor:.2f},{slot_lo:.3f}] +Y[{slot_hi:.3f},{y_ceil:.2f}] VOID Y[{slot_lo:.3f},{slot_hi:.3f}] X[{slot_x_lo:.3f},{slot_x_hi:.3f}]"
        )
    else:
        table_idx = [
            builder.add_shape_box(
                body=-1, hx=table_half[0], hy=table_half[1], hz=table_half[2], xform=table_xform, cfg=table_cfg
            )
        ]
        print(f"  [SCENE] Table at z={TABLE_HEIGHT} (BOX primitive, solid)")

    # Clip V-groove. PRODUCTION default = visual-only at CLIP1 (BYTE-IDENTICAL when the env flags are unset).
    # R-S7.1.1 (B) clip-collision PROBE (human 2026-06-21 「実 clip collision を配線」): CLIP_COLLISION=1 wires REAL
    # collision (flag 0x6 COLLIDE|BROADPHASE) + the stiffened mujoco solref (the contact mixes BOTH geoms' solref,
    # test:941-943) so the cable physically SEATS on the clip floor/walls (the kinematic pin still RETAINS, not the
    # clip — F-1 form-closure stays infeasible). CLIP_X/CLIP_Y reposition the clip onto the centered grasp. All
    # env-gated -> unset = unchanged. mujoco-only.
    cx = float(os.environ.get("CLIP_X", CLIP1_X))
    cy = float(os.environ.get("CLIP_Y", CLIP1_Y))
    # CLIP_FLOAT_Z (human-Rs FLOAT-the-clips probe 2026-06-30, 0-commit): RAISE the clip(s) by h [m] above the table
    # so the コ bottom claw (f1ext ~0.7966) can reach UNDER the cable over SOLID table -- f1ext+h clears table-top
    # 0.80 for h > ~3.4mm (no table void / no staggered layout needed). DEFAULT 0.0 -> byte-identical (the clip stays
    # on the table). The cable SEAT target Z + retention wall criteria are floated by the SAME h in the route block
    # (S13_ROUTE_C2) so clip boxes + cable seat Z + gripper descent target all rise consistently (a PARTIAL raise =
    # clip up but cable target not = mis-seat = INVALID).
    _clip_float_z = float(os.environ.get("CLIP_FLOAT_Z", "0.0"))
    cz = CLIP1_Z + _clip_float_z
    _clip_collide = (os.environ.get("CLIP_COLLISION", "0") == "1") and (solver_backend == "mujoco")
    clip_parts = [
        (0, 0, 0.0025, 0.020, 0.015, 0.0025),
        (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
        (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
        (-0.013, 0, 0.025, 0.002, 0.015, 0.005),
        (+0.013, 0, 0.025, 0.002, 0.015, 0.005),
    ]
    _clip_cfg = None
    if _clip_collide:
        _clip_cfg = newton.ModelBuilder.ShapeConfig()
        _clip_cfg.ke = MUJOCO_CONTACT_KE
        _clip_cfg.kd = MUJOCO_CONTACT_KD
        # CLIP_MU env override (S13_FEED fidelity sweep, 0-commit): clip↔cable friction is the しごき-feed
        # impedance axis. Unset/empty -> 1.0 (byte-identical). MuJoCo mixes the PAIR friction as the
        # element-wise MAX of the two geoms, so a clean clip↔cable mu=X needs BOTH this and CABLE_MU=X.
        _clip_cfg.mu = float(os.environ.get("CLIP_MU", "") or "1.0")
        _clip_cfg.gap = 0.002
    clip_shape_indices = []
    for dx, dy, dz, hx, hy, hz in clip_parts:
        xf = wp.transform((cx + dx, cy + dy, cz + dz), wp.quat_identity())
        idx = (
            builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz, cfg=_clip_cfg)
            if _clip_cfg is not None
            else builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz)
        )
        builder.shape_flags[idx] = 0x6 if _clip_collide else 1  # 0x6=COLLIDE|BROADPHASE / 1=VISIBLE-only
        clip_shape_indices.append(idx)
    print(f"  [SCENE] Clip V-groove at ({cx}, {cy}, {cz}) [CLIP_FLOAT_Z={_clip_float_z * 1e3:.1f}mm above CLIP1_Z "
          f"{CLIP1_Z}], 5 parts, collide={_clip_collide}")

    # SPACER under the clip (env-gate SPACER=1 AND CLIP_FLOAT_Z>0; human-Rs directive 2026-06-30
    # 「クリップの下にスペーサをかましたほうが良い」 = the PHYSICAL realization of the float: a solid riser from
    # the table top (CLIP1_Z=0.80) up to the floated clip floor (cz=CLIP1_Z+h) so the floated clip is supported
    # instead of levitating. DEFAULT OFF -> byte-identical. Footprint = the clip base-plate (hx=0.020, hy=0.015 =
    # +-20x+-15mm) so it does NOT extend under the adjacent free-span where the コ bottom claw cages (claw-span
    # +-44mm > spacer +-15mm = 29mm margin = the H2 constraint from the geometric-design). collide ON. mujoco-only.
    _spacer_on = (os.environ.get("SPACER", "0") == "1") and (_clip_float_z > 0.0) and (solver_backend == "mujoco")
    if _spacer_on:
        _sp_cfg = newton.ModelBuilder.ShapeConfig()
        _sp_cfg.ke = MUJOCO_CONTACT_KE
        _sp_cfg.kd = MUJOCO_CONTACT_KD
        _sp_cfg.mu = 1.0
        _sp_cfg.gap = 0.002
        _sp_xf = wp.transform((cx, cy, CLIP1_Z + _clip_float_z / 2.0), wp.quat_identity())
        _sp_idx = builder.add_shape_box(body=-1, xform=_sp_xf, hx=0.020, hy=0.015, hz=_clip_float_z / 2.0, cfg=_sp_cfg)
        builder.shape_flags[_sp_idx] = 0x6  # COLLIDE|BROADPHASE
        print(f"  [SCENE] SPACER under C1 at ({cx}, {cy}, {CLIP1_Z + _clip_float_z / 2.0:.4f}) "
              f"h={_clip_float_z * 1e3:.1f}mm top={CLIP1_Z + _clip_float_z:.4f}(=clip-floor cz {cz:.4f}) "
              f"footprint hx0.020/hy0.015 (claw-span +-0.044 clear -> 29mm margin)")

    # SECOND clip C2 (env-gate CLIP2=1; %3 Rs C1->C2 routing directive 2026-06-30): add the NEXT clip toward -Y
    # (canonical CLIP_POSITIONS[1]=(0.40,+0.075), the 千鳥 even clip over SOLID table -- NO void is added under it,
    # per the project clip-layout). Same 5-box V-groove as C1; collide follows CLIP_COLLISION. All env-gated -> unset
    # = byte-identical. mujoco-only. ⚠ C2 X=0.40 > the grasp-void X-ceiling 0.366 (build:1094) = over SOLID: the コ
    # bottom claw cannot reach UNDER the cable at C2 -- surfaced as a FLAG, not silently fixed with a void.
    clip2_shape_indices = []
    _clip2_on = (os.environ.get("CLIP2", "0") == "1") and (solver_backend == "mujoco")
    if _clip2_on:
        c2x = float(os.environ.get("CLIP2_X", str(CLIP_POSITIONS[1][0])))  # 0.40
        c2y = float(os.environ.get("CLIP2_Y", str(CLIP_POSITIONS[1][1])))  # +0.075
        c2z = CLIP1_Z + _clip_float_z   # CLIP_FLOAT_Z: C2 floated by the SAME h as C1 (consistency)
        _clip2_collide = (os.environ.get("CLIP_COLLISION", "0") == "1") and (solver_backend == "mujoco")
        _clip2_cfg = None
        if _clip2_collide:
            _clip2_cfg = newton.ModelBuilder.ShapeConfig()
            _clip2_cfg.ke = MUJOCO_CONTACT_KE
            _clip2_cfg.kd = MUJOCO_CONTACT_KD
            _clip2_cfg.mu = float(os.environ.get("CLIP_MU", "") or "1.0")
            _clip2_cfg.gap = 0.002
        for dx, dy, dz, hx, hy, hz in clip_parts:
            xf = wp.transform((c2x + dx, c2y + dy, c2z + dz), wp.quat_identity())
            idx = (
                builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz, cfg=_clip2_cfg)
                if _clip2_cfg is not None
                else builder.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz)
            )
            builder.shape_flags[idx] = 0x6 if _clip2_collide else 1
            clip2_shape_indices.append(idx)
        print(f"  [SCENE] Clip2 V-groove at ({c2x}, {c2y}, {c2z}), 5 parts, collide={_clip2_collide} "
              f"(over-SOLID: X={c2x} > grasp-void X-ceiling 0.366 -> NO under-cable void at C2)")
        if _spacer_on:
            _sp2_cfg = newton.ModelBuilder.ShapeConfig()
            _sp2_cfg.ke = MUJOCO_CONTACT_KE
            _sp2_cfg.kd = MUJOCO_CONTACT_KD
            _sp2_cfg.mu = 1.0
            _sp2_cfg.gap = 0.002
            _sp2_xf = wp.transform((c2x, c2y, CLIP1_Z + _clip_float_z / 2.0), wp.quat_identity())
            _sp2_idx = builder.add_shape_box(body=-1, xform=_sp2_xf, hx=0.020, hy=0.015, hz=_clip_float_z / 2.0, cfg=_sp2_cfg)
            builder.shape_flags[_sp2_idx] = 0x6
            print(f"  [SCENE] SPACER under C2 at ({c2x}, {c2y}, {CLIP1_Z + _clip_float_z / 2.0:.4f}) "
                  f"h={_clip_float_z * 1e3:.1f}mm top={CLIP1_Z + _clip_float_z:.4f}")

    # R-S6.6: pad collision-shape indices (populated in the mujoco A-1 pass; [] on the VBD path).
    pad_shape_idx = []

    # Robot arms: VBD = jointless kinematic bodies (FK body_q); MuJoCo = articulated UR5e+Robotiq.
    if solver_backend == "mujoco":
        if grasp_actuation:
            # R-S6.6: warm-register the SHAPE custom attrs (mujoco:condim) before finalize so put_model
            # bakes condim into BOTH mj_model and mjw_model (add_revolute_cable also calls this; the
            # call is idempotent and covers the pad shapes added below).
            SolverMuJoCo.register_custom_attributes(builder)
        # Option-E Opt-1 (SC2b-part2, D-Opt1-1): articulated UR5e+Robotiq per arm via the probe-
        # validated add_mjcf recipe (Robotiq <tendon> stripped so SolverMuJoCo constructs; the
        # _init_tendons OOB is avoided). S4a (D-S4a-3): contacts are now ENABLED for the cable, so
        # the A-1 VISIBLE-only pass below is LOAD-BEARING — without it the whole UR5e+Robotiq
        # collision set goes live and the fixed-arm-over-table explodes (cycle-2 CRITICAL).
        left_shape_start = builder.shape_count
        add_ur5e_robotiq(
            builder,
            wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()),
            robotiq_xml=ROBOTIQ_STRIPPED_XML,
            skip_equality_constraints=True,
        )
        left_shape_end = builder.shape_count
        right_shape_start = left_shape_end
        add_ur5e_robotiq(
            builder,
            wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
            robotiq_xml=ROBOTIQ_STRIPPED_XML,
            skip_equality_constraints=True,
        )
        right_shape_end = builder.shape_count
        # body-range scene keys (§28 #4): left=0, right=BODIES_PER_ARM(14) -> robot_body_count=28.
        left_body_start, right_body_start = 0, BODIES_PER_ARM
        # A-1 VISIBLE-only pass (probe-proven, F4c): clear COLLIDE on every NON-PAD arm shape
        # (→ MuJoCo contype=conaffinity=0, solver_mujoco.py:4758-4762); KEEP COLLIDE on the gripper
        # PAD geoms (label-matched right/left_pad1/2 ← pad_box1/2 — needed for cable grasp, S5).
        _labels = list(getattr(builder, "shape_label", []) or [])
        pads_kept = arm_cleared = 0
        for si in range(left_shape_start, right_shape_end):
            lbl = str(_labels[si]) if si < len(_labels) else ""
            if "pad" in lbl.lower():
                pads_kept += 1
                pad_shape_idx.append(si)  # R-S6.6: keep pad shape idx for the build-time condim hook
            else:
                builder.shape_flags[si] = int(newton.ShapeFlags.VISIBLE)
                arm_cleared += 1
        print(
            f"  [SCENE] A-1 VISIBLE-only pass (mujoco): {arm_cleared} arm shapes COLLIDE-cleared, "
            f"{pads_kept} pad shapes kept"
        )
        all_finger_visual = set()
    else:
        # Left arm (kinematic bodies, no joints)
        left_body_start, left_shape_start, left_shape_end, left_fv = add_kinematic_arm(
            builder, fk_model, fk_state, arm_body_offset=0, label_prefix="left"
        )

        # Right arm (kinematic bodies, no joints)
        right_body_start, right_shape_start, right_shape_end, right_fv = add_kinematic_arm(
            builder, fk_model, fk_state, arm_body_offset=FRANKA_NUM_JOINTS, label_prefix="right"
        )

        # All finger visual DAE shape indices (to exclude from approximate_meshes)
        all_finger_visual = set(left_fv + right_fv)

        # Contact filtering for arm bodies
        ground_planes = [floor_shape_idx, *table_idx]  # table_idx is a LIST (1 solid box / 2 slot boxes)
        filter_count = 0
        for arm_label, shape_start, shape_end, body_start in [
            ("left", left_shape_start, left_shape_end, left_body_start),
            ("right", right_shape_start, right_shape_end, right_body_start),
        ]:
            for si in range(shape_start, shape_end):
                body_idx = builder.shape_body[si]
                local_body = body_idx - body_start
                # Arm bodies (0-6): visual only, no collision
                if local_body < 7:
                    builder.shape_flags[si] = 1  # VISIBLE only (remove COLLIDE)
                    filter_count += 1
                # Finger visual DAE shapes: VISIBLE only (same as arm shapes)
                elif si in all_finger_visual:
                    builder.shape_flags[si] = 1  # VISIBLE only
                    filter_count += 1
                elif local_body in (7, 8):
                    # Finger collision shapes: COLLIDE + BROADPHASE, NOT visible
                    # Visual rendering comes from finger.dae DAE meshes
                    builder.shape_flags[si] = 0x6  # COLLIDE | BROADPHASE (no VISIBLE)
                    filter_count += 1
        print(
            f"  [SCENE] Contact filtering: {filter_count} arm+finger-visual shapes flagged, "
            f"finger collision → COLLIDE only (not visible)"
        )

    # Cable: VBD = Cosserat rod (add_rod, CABLE joints); MuJoCo = rigid-link REVOLUTE chain
    # (S4a D-S4a-4 — CABLE joints are MuJoCo-rejected, solver_mujoco.py:292).
    cable_bodies = []
    cable_joints = []
    cable_shape_start = cable_shape_end = None  # R-S6.6: defined for the grasp-actuation condim hook
    # PERCLIP_PIN (b)-pin probe (%3 charter 2026-07-01): count of pre-allocated per-clip connect eqs
    # (0 unless PERCLIP_PIN=1) -- stashed into scene_info for the route-block mid-episode activation.
    _perclip_pin_n = 0
    if use_cable:
        cable_shape_start = builder.shape_count
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        # Center the cable on the CLIP-ARRAY center (midpoint of the first and last clips), NOT CLIP1_Y (the
        # +Y-most clip) — otherwise the cable Y[-0.15, +0.45] overhangs the table +Y edge (+0.30) by 150mm.
        # Array center = (C1.y + C5.y)/2 = 0.0 → cable Y[-0.30, +0.30], within table Y[-0.40, +0.30].
        clip_y_center = (CLIP_POSITIONS[0][1] + CLIP_POSITIONS[-1][1]) / 2
        cable_y_start = clip_y_center - cable_half_len
        _cxo = cable_xy_offset or (0.0, 0.0)  # ③ (B2 §2.2/§5.1): per-run rigid cable-XY offset; None -> (0,0) = byte-identical
        cable_start = (GRASP_X + _cxo[0], cable_y_start + _cxo[1], TABLE_HEIGHT + CABLE_RADIUS)
        if solver_backend == "mujoco":
            cable_bodies, cable_joints, _cable_sr = add_revolute_cable(
                builder, start_pos=cable_start, direction=(0, 1, 0)
            )
            cable_shape_start, cable_shape_end = _cable_sr
        else:
            cable_bodies, cable_joints = add_cable_rod(builder, start_pos=cable_start, direction=(0, 1, 0))
            cable_shape_end = builder.shape_count
        cable_y_end = cable_start[1] + CABLE_SEGMENTS * CABLE_SEG_LEN
        print(
            f"  [SCENE] Cable: {len(cable_bodies)} bodies, {len(cable_joints)} joints, "
            f"Y=[{cable_y_start:.3f}, {cable_y_end:.3f}], Z={cable_start[2]:.4f}"
        )

        # PERCLIP_PIN (b)-pin routing-compat probe (%3 charter 2026-07-01, Rs "A go"): pre-allocate a DISABLED
        # per-clip connect equality (the C1 seat cable body <-> WORLD; the clip is world-fixed add_shape_box(body=-1))
        # so the AUTHORIZED clip-retention pin (log:6534, INVARIANT#5) can be ACTIVATED mid-episode on the VERIFIED
        # C1 seat (restore-gate log:6814 C2 forbids pre-seat activation -> built enabled=False = eq_active0=0).
        # PER-CLIP (ONE body), NOT the (a) whole-cable jq[ARM_Q:] freeze (r_s71_clip_dropin_72.py). The eq_active
        # mid-episode toggle is API-de-risked (eq_active_smoke: fires + per-body + persists, no re-sync). DEFAULT off.
        if os.environ.get("PERCLIP_PIN", "0") == "1" and solver_backend == "mujoco":
            # Pre-allocate ONE DISABLED connect-to-world eq PER cable body. The route SHIFTS the cable, so the
            # build-time-nearest body != the runtime C1 seat body (~3-body offset observed); full per-body coverage
            # lets the route block activate the EXACT runtime seat body by position-match (no window guessing). All
            # enabled=False (eq_active0=0) -> inert until the verified seat (restore-gate log:6814 C2). PER-CLIP: at
            # runtime exactly ONE is activated (the seat body); the rest stay disabled. NOT the (a) whole-cable freeze.
            for _pb in cable_bodies:
                builder.add_equality_constraint_connect(
                    body1=int(_pb), body2=-1, anchor=wp.vec3(0.0, 0.0, 0.0),
                    label=f"perclip_pin_{int(_pb)}", enabled=False,
                )
            _perclip_pin_n = len(cable_bodies)
            print(f"  [PERCLIP_PIN] pre-allocated {_perclip_pin_n} DISABLED connect-to-world eqs (one per cable body); "
                  f"the route block activates the ONE matching the runtime C1 seat body (position-match, mid-episode)")

        # Filter cable vs floor (cable only needs table contacts)
        for si in range(cable_shape_start, cable_shape_end):
            builder.add_shape_collision_filter_pair(si, floor_shape_idx)

        cable_arm_filters = 0
        if solver_backend == "mujoco":
            # D-S4a-3: cable ↔ non-pad-arm filter pairs, EXPLICIT (label-based; pads excluded so
            # cable↔pad contact is kept). The A-1 pass already cleared COLLIDE on these shapes —
            # the pairs are belt-and-suspenders + audit-greppable parity with the VBD loop below.
            _labels = list(getattr(builder, "shape_label", []) or [])
            for cable_si in range(cable_shape_start, cable_shape_end):
                for arm_si in range(left_shape_start, right_shape_end):
                    lbl = str(_labels[arm_si]) if arm_si < len(_labels) else ""
                    if "pad" not in lbl.lower():
                        builder.add_shape_collision_filter_pair(cable_si, arm_si)
                        cable_arm_filters += 1
            print(
                f"  [SCENE] Cable contact filters (mujoco): "
                f"{cable_shape_end - cable_shape_start} cable-floor, "
                f"{cable_arm_filters} cable-(non-pad-arm) (pads keep cable contacts)"
            )
        else:
            # Filter cable vs arm bodies 0-6 (only finger bodies 7-8 contact cable)
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
            print(
                f"  [SCENE] Cable contact filters: "
                f"{cable_shape_end - cable_shape_start} cable-floor, "
                f"{cable_arm_filters} cable-arm (fingers keep cable contacts)"
            )
    else:
        print("  [SCENE] Cable: DISABLED (--no-cable)")

    # A-3 backend-conditional from the LIVE right_body_start: VBD kinematic = 18, mujoco articulated = 28.
    robot_body_count = right_body_start + FRANKA_NUM_JOINTS

    # Finger collision is now BOX primitives (no approximate_meshes needed)
    print(
        f"  [SHAPES] Finger collision: BOX×3 per finger (wall+claws), "
        f"{len(all_finger_visual)} finger visual DAE preserved"
    )

    # --- R-S6.6 CHANGE 2/3: S6_GRASP actuation + 4-bar equalities + build-time S5 families (gated) ---
    # All behind grasp_actuation (default False -> byte-identical). Reuses the validated shipped wiring
    # (r_s66_full_topo_inspect / r_s66_stage_d_probe; AGENTS.md reuse gate). SSOT-derived indices (I9).
    grasp_driver_joints = []
    grasp_connects = []
    grasp_mirrors = []
    if solver_backend == "mujoco" and grasp_actuation:
        # POSITION drivers on [6,10,20,24] = GRIPPER_DRIVER_JOINT_IDX + right arm (+JOINTS_PER_ARM).
        grasp_driver_joints = list(GRIPPER_DRIVER_JOINT_IDX) + [j + JOINTS_PER_ARM for j in GRIPPER_DRIVER_JOINT_IDX]
        assert grasp_driver_joints == [6, 10, 20, 24], f"S6_GRASP driver index drift: {grasp_driver_joints}"
        for dof in grasp_driver_joints:
            builder.joint_target_mode[dof] = int(newton.JointTargetMode.POSITION)
            builder.joint_target_ke[dof] = GRIPPER_SERVO_TARGET_KE
            builder.joint_target_kd[dof] = GRIPPER_SERVO_TARGET_KD
            builder.joint_effort_limit[dof] = GRIPPER_DRIVER_EFFORT_LIMIT_NM
            builder.joint_target_pos[dof] = GRIPPER_DRIVER_OPEN_RAD  # start OPEN; runner schedules CLOSE
        # Restore the 4 gripper 4-bar connect equalities (follower<->coupler), derived BY LABEL for both
        # arms (the shipped XML <connect> loaded with skip_equality_constraints=True). neq==4.
        _blabel = [str(x) for x in (getattr(builder, "body_label", None) or getattr(builder, "body_key", []))]

        def _bodies_ending(suffix, lo, hi):
            return [i for i in range(lo, hi) if _blabel[i].endswith(suffix)]

        for lo, hi in [(0, BODIES_PER_ARM), (BODIES_PER_ARM, 2 * BODIES_PER_ARM)]:
            for side in ("right", "left"):
                fb = _bodies_ending(f"{side}_follower", lo, hi)
                cb = _bodies_ending(f"{side}_coupler", lo, hi)
                if fb and cb:
                    grasp_connects.append((fb[0], cb[0]))
        for fb, cbb in grasp_connects:
            builder.add_equality_constraint_connect(
                body1=fb, body2=cbb, anchor=wp.vec3(0.0, 0.0, 0.0), label=f"fourbar_{fb}_{cbb}", enabled=True
            )
        # FAITHFUL coupling: restore the L-R FOLLOWER MIRROR equality per gripper (right_follower_joint =
        # left_follower_joint, polycoef [0,1,0,0,0]) — the tendon-stripped XML DROPPED the <joint> symmetric
        # coupling, letting the two fingers close asymmetrically (the _11 flop). MUST couple the FOLLOWERS,
        # NOT the drivers: the 4-bar is BISTABLE, so a driver mirror alone leaves each follower free to pick
        # its branch (verified: driver mirror -> follower_R=-0.71 vs follower_L=+0.87 sign-flip flop). The
        # follower mirror forces BOTH followers onto the same branch -> symmetric (proven FAITHFUL_SLOT_15).
        # Resolved BY LABEL (NOT a hardcoded idx 23/27) + cross-checked vs the SSOT driver indices (follower =
        # driver+3 in the per-finger driver/coupler/spring_link/follower order). With the stiffened 4-bar
        # connects (_wire_s6_grasp_solref) this gives symmetric 1-DOF closure. neq 4 -> 6 (the 2 mirror eqs
        # are joint equalities, NOT connect pairs -> NOT in grasp_connects).
        _jlabel = [str(x) for x in (getattr(builder, "joint_label", None) or [])]

        def _joints_ending(suffix, lo, hi):
            return [i for i in range(lo, hi) if _jlabel[i].endswith(suffix)]

        for lo, hi in [(0, JOINTS_PER_ARM), (JOINTS_PER_ARM, 2 * JOINTS_PER_ARM)]:
            rf = _joints_ending("right_follower_joint", lo, hi)
            lf = _joints_ending("left_follower_joint", lo, hi)
            assert rf and lf, f"S6_GRASP: follower-mirror joints unresolved by label in [{lo},{hi}): rf={rf} lf={lf}"
            builder.add_equality_constraint_joint(
                joint1=rf[0],
                joint2=lf[0],
                polycoef=[0.0, 1.0, 0.0, 0.0, 0.0],
                label=f"follower_mirror_{rf[0]}_{lf[0]}",
                enabled=True,
            )
            grasp_mirrors.append((rf[0], lf[0]))
        assert sorted(j for p in grasp_mirrors for j in p) == sorted(d + 3 for d in grasp_driver_joints), (
            f"S6_GRASP: follower-mirror by-label {grasp_mirrors} != SSOT followers {[d + 3 for d in grasp_driver_joints]}"
        )
        # Build-time S5 contact families: condim=6 (mujoco:condim SHAPE custom attr) on pad+cable shapes
        # + rolling friction (shape_material_mu_rolling) on pads -> baked into BOTH mj_model AND mjw_model
        # at put_model (the post-construct mj_model poke is GPU-inert, STAGE D). The negative PAD_SOLREF
        # has no build-time path -> poked post-make_solver (_wire_s6_grasp_solref).
        _condim_attr = builder.custom_attributes.get("mujoco:condim")
        assert _condim_attr is not None, "S6_GRASP: mujoco:condim custom attribute not registered"
        if _condim_attr.values is None:
            _condim_attr.values = {}
        _condim_shapes = list(pad_shape_idx)
        if cable_shape_start is not None:
            _condim_shapes += list(range(cable_shape_start, cable_shape_end))
        for si in _condim_shapes:
            _condim_attr.values[si] = int(MUJOCO_CONTACT_CONDIM)
        for si in pad_shape_idx:
            if si < len(builder.shape_material_mu_rolling):
                builder.shape_material_mu_rolling[si] = float(MUJOCO_PAD_ROLL_FRICTION)
        print(
            f"  [S6_GRASP] actuation wired: drivers={grasp_driver_joints} "
            f"servo(ke={GRIPPER_SERVO_TARGET_KE},kd={GRIPPER_SERVO_TARGET_KD},"
            f"eff={GRIPPER_DRIVER_EFFORT_LIMIT_NM}) connects={grasp_connects} condim6 on "
            f"{len(_condim_shapes)} shapes ({len(pad_shape_idx)} pad + cable) "
            f"rolling={MUJOCO_PAD_ROLL_FRICTION}"
        )

    # Color shapes for collision group assignment
    builder.color()

    # requires_grad=False: model.collide() skips rigid contacts when requires_grad=True
    model = builder.finalize(device=DEVICE, requires_grad=False)

    # Post-finalize: set shape flags for finger bodies
    # BOX collision shapes = COLLIDE | BROADPHASE (not visible — DAE renders instead)
    # MESH visual shapes = VISIBLE only (no collision)
    # (VBD only -- §28 #2: the mujoco articulated arm + disable_contacts has no kinematic-arm finger pass.)
    if solver_backend != "mujoco":
        model_shape_flags = model.shape_flags.numpy()
        model_shape_types = model.shape_type.numpy()
        model_shape_bodies = model.shape_body.numpy()
        hidden_count = 0
        for si in range(len(model_shape_types)):
            bi = model_shape_bodies[si]
            if bi < 0:
                continue
            local_l = bi - left_body_start
            local_r = bi - right_body_start
            if local_l in (7, 8) or local_r in (7, 8):
                if model_shape_types[si] == 7:  # BOX = collision only
                    model_shape_flags[si] = 0x6  # COLLIDE | BROADPHASE, no VISIBLE
                    hidden_count += 1
                elif model_shape_types[si] == 8:  # MESH = visual only (finger.dae)
                    model_shape_flags[si] = 0x1  # VISIBLE only
        model.shape_flags = wp.array(model_shape_flags, dtype=model.shape_flags.dtype, device=DEVICE)
        print(f"  [SCENE] Post-finalize: {hidden_count} finger BOX → hidden (model flags)")

    # Zero inv_mass/inv_inertia for kinematic robot bodies so VBD doesn't move them
    # VBD ONLY (§28 #1, the critical guard): the MuJoCo articulated arm keeps its REAL masses --
    # zeroing => infinite mass+inertia => degenerate joint-space M(q); the STEP-1 probe validated the
    # REAL-mass arm + per-step re-pose. Uses the LOCAL solver_backend, NOT the task_config constant.
    if solver_backend != "mujoco":
        inv_mass = model.body_inv_mass.numpy()
        inv_inertia = model.body_inv_inertia.numpy()
        for bi in range(robot_body_count):
            inv_mass[bi] = 0.0
            inv_inertia[bi] = np.zeros(3, dtype=np.float32)
        model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=DEVICE)
        model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=DEVICE)
        print(f"  [SCENE] Kinematic bodies: inv_mass=0 for bodies 0-{robot_body_count - 1}")

    print(
        f"  [SCENE] Model: bodies={model.body_count}, joints={model.joint_count}, "
        f"articulations={model.articulation_count}, "
        f"joint_coords={model.joint_coord_count}, joint_dofs={model.joint_dof_count}"
    )

    # D-S4a-4 joint-layout assert (mujoco): arm joints [0:28] + cable FREE+REVOLUTE — guards the
    # arm joint_q slice (physics_step overwrites [:2*JOINTS_PER_ARM]) against layout drift.
    if solver_backend == "mujoco" and use_cable:
        expected = 2 * JOINTS_PER_ARM + len(cable_joints)
        assert model.joint_count == expected, (
            f"mujoco joint layout drift: joint_count={model.joint_count} != "
            f"2*JOINTS_PER_ARM + cable joints = {expected}"
        )

    # R-S6.6 CHANGE 2 (I11) + R-S7.1 faithful: in-builder asserts -- the 4 gripper 4-bar connect equalities
    # + the 2 L-R follower-mirror equalities all register (neq=6) on the production topology (no rig cable-pins)
    # and the cable<->non-pad filter pairs were built (M1).
    if solver_backend == "mujoco" and grasp_actuation:
        _neq = int(getattr(model, "equality_constraint_count", 0) or 0)
        # PERCLIP_PIN pre-allocates _perclip_pin_n DISABLED per-clip connect eqs -> tolerate neq=6+_perclip_pin_n.
        _want_neq = 6 + _perclip_pin_n
        assert _neq == _want_neq, (
            f"S6_GRASP: 4-bar connects + follower mirrors did not all register: neq={_neq} "
            f"(want {_want_neq} = 4 connect + 2 follower-mirror{f' + {_perclip_pin_n} perclip-pins' if _perclip_pin_n else ''})"
        )
        assert len(grasp_connects) == 4, f"S6_GRASP: expected 4 connect pairs, got {len(grasp_connects)}"
        assert len(grasp_mirrors) == 2, f"S6_GRASP: expected 2 follower-mirror eqs, got {len(grasp_mirrors)}"
        if use_cable:
            assert cable_arm_filters > 0, "S6_GRASP: cable<->non-pad-arm filter pairs missing (M1)"
        print(
            f"  [S6_GRASP] in-builder asserts OK: neq={_neq}=={_want_neq} ({len(grasp_connects)} connect + "
            f"{len(grasp_mirrors)} follower-mirror), cable<->non-pad filters intact"
        )

    # Shape diagnostics
    # (VBD only -- §28 #3: indexes the kinematic-arm finger bodies [7,8]; N/A to the mujoco articulated arm.)
    if solver_backend != "mujoco":
        shape_types = model.shape_type.numpy()
        shape_bodies = model.shape_body.numpy()
        shape_flags = model.shape_flags.numpy()
        shape_collision_group = model.shape_collision_group.numpy()
        TYPE_NAMES = {
            0: "NONE",
            1: "PLANE",
            2: "HFIELD",
            3: "SPHERE",
            4: "CAPSULE",
            5: "ELLIPSOID",
            6: "CYLINDER",
            7: "BOX",
            8: "MESH",
            9: "CONE",
            10: "CONVEX_MESH",
        }
        COLLIDE_SHAPES = newton.ShapeFlags.COLLIDE_SHAPES
        for arm_label, body_start_v in [("Left", left_body_start), ("Right", right_body_start)]:
            for local_body in [7, 8]:
                bi = body_start_v + local_body
                shapes_for_body = [si for si in range(len(shape_bodies)) if shape_bodies[si] == bi]
                for si in shapes_for_body:
                    st = shape_types[si]
                    name = TYPE_NAMES.get(st, f"UNKNOWN({st})")
                    flags = shape_flags[si]
                    cgroup = shape_collision_group[si]
                    has_collide = bool(flags & COLLIDE_SHAPES)
                    print(
                        f"  [SHAPE] {arm_label} body{local_body} shape#{si}: type={name}, "
                        f"flags={flags:#x}(COLLIDE={has_collide}), cgroup={cgroup}"
                    )
                if arm_label == "Left":
                    break
        if cable_bodies:
            si0 = [si for si in range(len(shape_bodies)) if shape_bodies[si] == cable_bodies[0]]
            if si0:
                si = si0[0]
                print(
                    f"  [SHAPE] Cable body0 shape#{si}: type={TYPE_NAMES.get(shape_types[si], '?')}, "
                    f"flags={shape_flags[si]:#x}(COLLIDE={bool(shape_flags[si] & COLLIDE_SHAPES)}), "
                    f"cgroup={shape_collision_group[si]}"
                )

    scene_info = {
        "model": model,
        "cable_xy_offset": tuple(cable_xy_offset) if cable_xy_offset else (0.0, 0.0),  # ③ Y-follow source (0,0 = legacy)
        "left_body_start": left_body_start,
        "left_shape_start": left_shape_start,
        "left_shape_end": left_shape_end,
        "right_body_start": right_body_start,
        "right_shape_start": right_shape_start,
        "right_shape_end": right_shape_end,
        "cable_bodies": cable_bodies,
        "cable_joints": cable_joints,
        "n_cable_bodies": len(cable_bodies),
        "perclip_pin_n": _perclip_pin_n,
        "robot_body_count": robot_body_count,
        "table_shape_idx": table_idx,
        "clip_shape_indices": clip_shape_indices,
        "clip2_shape_indices": clip2_shape_indices,
        "solver_backend": solver_backend,
        "grasp_actuation": grasp_actuation,
        "pad_shape_idx": pad_shape_idx,
        "driver_joints": grasp_driver_joints,
    }
    return scene_info


def build_fk_model(device=None):
    """Build robot-only model for FK body position computation and IK solving.

    Uses the UR5e+Robotiq MJCF joints (REVOLUTE/FIXED) for FK/IK.  Body indices
    map 1:1 to the physics model (left arm 0-13, right arm 14-27).  No cable.

    The FK model is separate from the VBD physics model:
    - FK model: URDF joints → IK solving + FK body transform computation
    - Physics model: VBD cable + kinematic robot bodies (no joints)

    Args:
        device: Warp device string (e.g. "cuda:0"). Defaults to module DEVICE.
    """
    if device is None:
        device = DEVICE
    builder = newton.ModelBuilder(gravity=GRAVITY)
    # Minimal shape config (FK model doesn't need collision)
    urdf_cfg = newton.ModelBuilder.ShapeConfig()
    urdf_cfg.gap = 0.0
    urdf_cfg.density = 0.0
    builder.default_shape_cfg = urdf_cfg

    # Option-E substrate (S2a, C-a): UR5e + Robotiq 2f85 per arm via the S1 assembly
    # (collapse=True, parse_meshes=False = the derived 14-body/arm production index space).
    add_ur5e_robotiq(builder, wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()))
    add_ur5e_robotiq(builder, wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()))

    model = builder.finalize(device=device, requires_grad=True)
    print(
        f"  [FK] Robot-only model: bodies={model.body_count}, "
        f"joints={model.joint_count}, "
        f"joint_coords={model.joint_coord_count}, joint_dofs={model.joint_dof_count}"
    )
    return model


def update_kinematic_bodies(physics_state, fk_state, robot_body_count):
    """Copy robot body transforms from FK state to physics state.

    FK model body indices map 1:1 to physics model body indices (both start at 0).
    Called each substep to ensure kinematic bodies reflect current FK positions
    before contact detection.
    """
    fk_bq = fk_state.body_q.numpy()
    phys_bq = physics_state.body_q.numpy()
    phys_bq[:robot_body_count] = fk_bq[:robot_body_count]
    physics_state.body_q.assign(phys_bq)


# ---------------------------------------------------------------------------
# Physics step: VBD solver (cable dynamics) + kinematic robot body update
# ---------------------------------------------------------------------------
_physics_state_buffer = None  # Pre-allocated double-buffer state (created on first call)

# R-S6.6 CHANGE 1: arm-only FK-overwrite index set for the gripper_dynamic path. SSOT-derived from
# GRIPPER_JOINT_RANGE (M2 -- == the test:1470 finger_coords set {6-13,20-27}); the complement
# {0-5,14-19} is the arm coords overwritten each substep while the POSITION-actuated gripper stays
# dynamic. Computed once at import; unused unless a runner sets scene_info["gripper_dynamic"]=True
# (default False keeps the 5 legacy mujoco consumers byte-identical).
_GRIPPER_COORDS_BOTH = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}
_ARM_OVERWRITE_IDX = [i for i in range(2 * JOINTS_PER_ARM) if i not in _GRIPPER_COORDS_BOTH]

# Whole-route demo RECORDER (P3, env-gated DEMO_RECORD=1). None = default-off = byte-identical; the route
# fn (below) constructs a RouteDemoRecorder under the gate and the read-only hooks below tap it when set.
_demo_rec = None
# Line numbers of the 3 "⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01)" markers in THIS file, pinned into the demo meta
# for quick auditability. Keep in sync with the markers; as_run_sha256 of this file also cryptographically pins them.
_ANTI_REVERT_MARKER_LINES = [4477, 4493, 4593]  # DQ7 (ii) re-sync (grep of the ⛔ANTI-REVERT text, not arithmetic; markers byte-untouched)


def physics_step(model, state, solver, contacts, scene_info):
    """VBD physics step with kinematic body override (double-buffer pattern).

    1. Update kinematic robot bodies from FK state each substep
    2. model.collide() for contact detection (BOX-CAPSULE finger-cable)
    3. VBD solver step — cable CABLE joint dynamics only (kinematic bodies inv_mass=0)
    4. Double-buffer swap

    Substeps: SIM_SUBSTEPS per frame.
    External interface: 1 call = DT time advancement.
    Returns state with updated body_q (cable from VBD, robot from FK).
    """
    global _physics_state_buffer
    if _physics_state_buffer is None:
        _physics_state_buffer = model.state()

    state_0 = state
    state_1 = _physics_state_buffer

    fk_state = scene_info["fk_state"]
    robot_body_count = scene_info["robot_body_count"]
    vbd_control = scene_info["vbd_control"]
    solver_backend = scene_info.get("solver_backend", "vbd")
    gripper_dynamic = scene_info.get("gripper_dynamic", False)  # R-S6.6 CHANGE 1 (default False = legacy)

    for i in range(SIM_SUBSTEPS):
        if solver_backend == "mujoco":
            # MuJoCo articulated kinematic re-pose (D-Opt1-2): per-substep OVERWRITE joint_q=FK +
            # zero joint_qd (the STEP-1 probe-validated driving; MuJoCo poses bodies from joint_q).
            # disable_contacts=True -> no model.collide (contacts None), mirroring the base mujoco branch.
            n = 2 * JOINTS_PER_ARM
            phys_jq = state_0.joint_q.numpy()
            phys_jqd = state_0.joint_qd.numpy()
            if gripper_dynamic:
                # R-S6.6 CHANGE 1: the gripper is a POSITION actuator (S6_GRASP) -> overwrite ONLY the
                # arm coords ({0-5,14-19}); leave the gripper coords ({6-13,20-27}) DYNAMIC so the servo
                # drives them via control.joint_target_pos. _ARM_OVERWRITE_IDX is SSOT-derived (M2).
                phys_jq[_ARM_OVERWRITE_IDX] = fk_state.joint_q.numpy()[_ARM_OVERWRITE_IDX]
                phys_jqd[_ARM_OVERWRITE_IDX] = 0.0
            else:
                phys_jq[:n] = fk_state.joint_q.numpy()[:n]
                phys_jqd[:n] = 0.0
            state_0.joint_q.assign(phys_jq)
            state_0.joint_qd.assign(phys_jqd)
            state_0.clear_forces()
            solver.step(state_0, state_1, vbd_control, None, SIM_DT)
        else:
            # Ensure kinematic bodies reflect current FK positions
            update_kinematic_bodies(state_0, fk_state, robot_body_count)

            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, vbd_control, contacts, SIM_DT)

        state_0, state_1 = state_1, state_0

    if _demo_rec is not None:  # P3 recorder: sample the post-step frame (read-only, COPY-on-sample; spec §2.1)
        _demo_rec.sample(state_0, scene_info)
    return state_0


# ---------------------------------------------------------------------------
# IK helpers
# ---------------------------------------------------------------------------
def solve_ik_dual(scene_info, target_left, target_right, warmstart_jq=None):
    """Solve IK for both arms using the FK model.

    Args:
        warmstart_jq: optional full joint-config vector used as the LM solver's initial guess
            (R-S6.2 C2). Default ``None`` uses the current ``fk_state.joint_q`` (byte-identical to
            the prior behavior). Decouples the IK initial guess from the interpolation start so a
            move can re-seed from a known-good config (e.g. the converged hover) instead of a
            post-close LM-stuck point (RS6_1_FINDINGS §2.2).

    Returns (fk_joint_q, cost) — the FK model joint positions with IK solution.
    """
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    # EE body indices in FK model (body 6 = panda_hand for each arm)
    left_ee_body = EE_BODY_OFFSET  # 5 (UR5e wrist_3; S2a aliased EE_BODY_OFFSET=EE_BODY_IDX=5)
    right_ee_body = FRANKA_NUM_JOINTS + EE_BODY_OFFSET  # 19 (FRANKA_NUM_JOINTS aliased to ROBOT_NUM_JOINTS=14)

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

    # Rotation objectives: gripper pointing DOWN, fingers PERPENDICULAR to cable (world Y).
    # S6 retarget (UR5e+2F-85, NOT Franka): target = wrist_3 (body 5/19) world orientation
    # q = Rx(-90°), xyzw = (-√2/2, 0, 0, √2/2). Maps wrist_3 local +Y (approach) → world -Z (down)
    # and local X (finger-sep) → world ±X (⊥ cable Y). VALIDATED on the UR5e FK model: probe_ik_verify
    # (right arm down_dot=1.0/perp_|x|=1.0/z_leak=0) + probe_smoke_geom (BOTH arms down_dot=1.0/perp=1.0).
    # Convention seam: warp wp.vec4/IKObjectiveRotation = xyzw (newton ik_objectives.py:618,
    # target=wp.quat(vec[0..3]), w=vec[3]); the wrist_3 MuJoCo attachment_site is wxyz.
    # (The prior Franka π/8 quat was built for the collapsed panda_hand_joint frame → mis-orients the
    # UR5e wrist_3 = the S5 P1.3 horizontal-gripper failure; the S6 smoke now asserts this DOWN/⊥ TRIAD.)
    target_rot = wp.array([wp.vec4(-0.7071067811865476, 0.0, 0.0, 0.7071067811865476)], dtype=wp.vec4, device=DEVICE)
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

    # Joint limit objective: keeps IK solutions within URDF limits
    obj_joint_limits = IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper,
        weight=10.0,
    )

    # Dual-arm collision avoidance objectives
    from newton_routing_utils import _build_collision_objectives

    _use_collision = os.environ.get("COLLISION_AVOIDANCE", "1") != "0"
    collision_objs = _build_collision_objectives() if _use_collision else []

    ik_solver = IKSolver(
        fk_model, n_problems=1, objectives=[obj_l, obj_r, rot_l, rot_r, *collision_objs, obj_joint_limits]
    )

    # Initial guess for the LM solver: the warm-start config if provided (R-S6.2 C2, decoupled from
    # the interpolation start), else the current FK joint positions (byte-identical default).
    fk_jq = fk_state.joint_q.numpy().copy()
    if warmstart_jq is not None:
        fk_jq = np.asarray(warmstart_jq, dtype=fk_jq.dtype).reshape(-1).copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=DEVICE)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=DEVICE)

    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)

    cost = ik_solver.costs.numpy()[0]
    result = jq_out.numpy()[0]

    return result, cost


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
def ik_move_both(
    model,
    state,
    scene_info,
    solver,
    contacts,
    target_left,
    target_right,
    label="MOVE",
    converge_mm=5.0,
    speed_factor=1.0,
    warmstart_jq=None,
):
    """Move both EEs to target positions using IK + VBD stepping.

    Strategy: Solve IK ONCE for the final target, then interpolate FK joint
    positions over physics steps. Kinematic bodies follow FK instantly.

    Args:
        speed_factor: multiplier for step count (>1 = slower motion).

    Returns (final_state, success).
    """
    if _demo_rec is not None:  # P3 recorder: last-COMMANDED EE target positions (spec §2.3, positions only)
        _demo_rec.note_targets(target_left, target_right)
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    pos_l, pos_r = get_ee_positions(state, scene_info)
    dist = max(np.linalg.norm(np.array(target_left) - pos_l), np.linalg.norm(np.array(target_right) - pos_r))
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)

    print(
        f"  [{label}] Moving: L=({pos_l[0]:.3f},{pos_l[1]:.3f},{pos_l[2]:.3f}) "
        f"→ ({target_left[0]:.3f},{target_left[1]:.3f},{target_left[2]:.3f})"
    )
    print(
        f"  [{label}] Moving: R=({pos_r[0]:.3f},{pos_r[1]:.3f},{pos_r[2]:.3f}) "
        f"→ ({target_right[0]:.3f},{target_right[1]:.3f},{target_right[2]:.3f})"
    )
    print(f"  [{label}] dist={dist * 1000:.1f}mm, steps={n_steps}")

    tgt_l = np.array(target_left, dtype=np.float32)
    tgt_r = np.array(target_right, dtype=np.float32)

    # Solve IK once for final target (R-S6.2 C2: optional warm-start seed, default = current FK config)
    jq_target, ik_cost = solve_ik_dual(scene_info, tuple(tgt_l), tuple(tgt_r), warmstart_jq=warmstart_jq)
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False
    print(f"  [{label}] IK solved: cost={ik_cost:.2e}")

    # FK joint interpolation: arm joints only (j0-j6), preserve finger joints (j7-j8)
    fk_coord_count = fk_model.joint_coord_count
    jq_start = fk_state.joint_q.numpy().copy()
    jq_end = jq_target.copy()

    # Gripper coord indices to EXCLUDE from arm-IK interpolation (hold the gripper through arm moves).
    # S6: exclude ALL 8 gripper joints/arm via SSOT GRIPPER_JOINT_RANGE ([6..13]; right arm +JOINTS_PER_ARM
    # = [20..27]). The old {7,8,21,22} (Franka 2-finger) left 6/8 gripper joints/arm in the interpolation.
    # (IK leaves gripper joints ~unchanged — zero Jacobian on the arm-EE/collision objectives — so this is
    # SSOT-correctness + defense: it guarantees a scripted close is held through the post-close LIFT.)
    finger_coords = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)

        # Interpolate arm joints, preserve finger positions
        jq_interp = jq_start.copy()
        for d in range(fk_coord_count):
            if d not in finger_coords:
                jq_interp[d] = jq_start[d] + (jq_end[d] - jq_start[d]) * t

        # Update FK state → body transforms
        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

        # VBD step (kinematic bodies updated from FK inside physics_step)
        state = physics_step(model, state, solver, contacts, scene_info)

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
            # Extended diagnostics during lift phases
            diag_str = ""
            if label.startswith("P2") and cable_bodies:
                fk_jq = fk_state.joint_q.numpy()
                fj = [fk_jq[7], fk_jq[8], fk_jq[FRANKA_NUM_JOINTS + 7], fk_jq[FRANKA_NUM_JOINTS + 8]]
                diag_str += f" fingers=[{fj[0] * 1000:.1f},{fj[1] * 1000:.1f},{fj[2] * 1000:.1f},{fj[3] * 1000:.1f}]mm"
                # Contact diagnostics
                model.collide(state, contacts)
                wp.synchronize()
                nc = contacts.rigid_contact_count.numpy()[0]
                if nc > 0:
                    s0 = contacts.rigid_contact_shape0.numpy()[:nc]
                    s1 = contacts.rigid_contact_shape1.numpy()[:nc]
                    sb = model.shape_body.numpy()
                    lb = scene_info["left_body_start"]
                    rb = scene_info["right_body_start"]
                    fset = {lb + 7, lb + 8, rb + 7, rb + 8}
                    cset = set(cable_bodies)
                    fc_cnt = sum(
                        1
                        for ci in range(nc)
                        if (sb[s0[ci]] in fset or sb[s1[ci]] in fset) and (sb[s0[ci]] in cset or sb[s1[ci]] in cset)
                    )
                    co_cnt = sum(
                        1
                        for ci in range(nc)
                        if (sb[s0[ci]] in cset or sb[s1[ci]] in cset) and not (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                    )
                    diag_str += f" contacts={nc}(fc={fc_cnt},co={co_cnt})"
                else:
                    diag_str += " contacts=0"
            print(f"  [{label}] step {step}/{n_steps}: err L={err_l:.1f}mm R={err_r:.1f}mm{cable_str}{diag_str}")

    # Final error
    pos_l, pos_r = get_ee_positions(state, scene_info)
    err_l = np.linalg.norm(pos_l - tgt_l) * 1000
    err_r = np.linalg.norm(pos_r - tgt_r) * 1000
    converged = err_l < converge_mm and err_r < converge_mm
    print(f"  [{label}] Final: err L={err_l:.1f}mm R={err_r:.1f}mm converged={converged} (thresh={converge_mm}mm)")

    return state, converged


def hold_position(model, state, scene_info, solver, contacts, n_steps):
    """Hold current position for n_steps (settle).

    Kinematic bodies stay at current FK positions. Only cable moves via VBD.
    """
    for step in range(n_steps):
        state = physics_step(model, state, solver, contacts, scene_info)

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
    model.collide(state, contacts)
    wp.synchronize()
    n = contacts.rigid_contact_count.numpy()[0]
    if n == 0:
        print(f"  [{label}] Penalty contacts: 0")
        return
    shape0 = contacts.rigid_contact_shape0.numpy()[:n]
    shape1 = contacts.rigid_contact_shape1.numpy()[:n]
    sb = model.shape_body.numpy()
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    finger_set = {lb + 7, lb + 8, rb + 7, rb + 8}
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
    print(f"  [{label}] Penalty contacts: {n} (finger-cable={fc}, finger-other={fo}, cable-other={co}, other={oo})")


def do_p1_grasp(model, state, scene_info, solver, contacts):
    """P1: Wide-stance approach + descend + grasp.

    ⚠ S6 RESIDUAL-FRANKA (flag-only, debate M7): this legacy VBD episode (do_p1_grasp/p2/p3/p4) is
    DEFAULT-reachable (SOLVER_BACKEND="vbd") but still Franka-indexed for the gripper (the close ramps
    {+7,+8}, not GRIPPER_JOINT_RANGE -> closes 0 pads on the UR5e 2f85). PRE-EXISTING-broken-for-UR5e
    (NOT introduced by S6); S6 only corrects the SHARED solve_ik_dual/ik_move_both IK. Full VBD-episode
    retarget = a separate flagged legacy task. The S6 deliverable is the mujoco IK-motion smoke.
    """
    print(f"\n  {'=' * 50}")
    print("  [P1] Wide-Stance Approach + Grasp")
    print(f"  {'=' * 50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    grasp_dy = scene_info.get("cable_xy_offset", (0.0, 0.0))[1]  # ③ Y-follow (0.0 when unset = byte-identical)
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    # Step 1: Approach (move to above cable)
    print(
        f"\n  [P1-APPROACH] Target: L=({grasp_x:.3f},{WIDE_LEFT_Y},{APPROACH_Z}) "
        f"R=({grasp_x:.3f},{WIDE_RIGHT_Y},{APPROACH_Z})"
    )
    state, ok = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=(grasp_x, WIDE_LEFT_Y + grasp_dy, APPROACH_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y + grasp_dy, APPROACH_Z),
        label="P1-APPROACH",
        converge_mm=10.0,
    )
    if not ok:
        print("  [P1-APPROACH] WARN: not converged, continuing anyway")

    # Contact check after approach
    if has_cable:
        _check_contacts(solver, contacts, model, scene_info, "P1-APPROACH-END", state=state)

    # Step 2: Descend to cable level
    print(f"\n  [P1-DESCEND] Target Z={GRASP_Z}")
    state, ok = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=(grasp_x, WIDE_LEFT_Y + grasp_dy, GRASP_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y + grasp_dy, GRASP_Z),
        label="P1-DESCEND",
        converge_mm=5.0,
    )
    if not ok:
        print("  [P1-DESCEND] WARN: not converged, continuing anyway")

    # Contact check after descend
    if has_cable:
        _check_contacts(solver, contacts, model, scene_info, "P1-DESCEND-END", state=state)
        bq_d = state.body_q.numpy()
        cz_d = bq_d[cable_bodies, 2]
        print(
            f"  [P1-DESCEND-END] Cable Z: min={np.min(cz_d):.4f}, mean={np.mean(cz_d):.4f}, "
            f"max={np.max(cz_d):.4f}, nan={np.any(np.isnan(cz_d))}"
        )

    # Step 3: Close fingers (kinematic interpolation via FK model)
    # Fingers move kinematically regardless of cable resistance.
    # Cable responds via VBD contacts (BOX-CAPSULE).
    print(f"\n  [P1-CLOSE] Closing fingers to {FINGER_CLOSE_POS * 1000:.1f}mm (kinematic)")

    # Pre-close diagnostics
    fk_jq_pre = fk_state.joint_q.numpy()
    bq_pre = state.body_q.numpy()
    nan_bq = np.any(np.isnan(bq_pre))
    print(f"  [P1-CLOSE] Pre-close state: bq NaN={nan_bq}")
    print(
        f"  [P1-CLOSE] Pre-close fingers: L_j7={fk_jq_pre[7] * 1000:.1f}mm "
        f"L_j8={fk_jq_pre[8] * 1000:.1f}mm "
        f"R_j7={fk_jq_pre[FRANKA_NUM_JOINTS + 7] * 1000:.1f}mm "
        f"R_j8={fk_jq_pre[FRANKA_NUM_JOINTS + 8] * 1000:.1f}mm"
    )
    if cable_bodies:
        cable_z = [bq_pre[b][2] for b in cable_bodies[:5]]
        print(f"  [P1-CLOSE] Pre-close cable Z[0:5]: {['%.3f' % z for z in cable_z]}")

    # Interpolate finger positions from open → close over FINGER_CLOSE_STEPS
    finger_start = fk_jq_pre.copy()
    lb = scene_info["left_body_start"]
    nan_detected_step = -1

    for step in range(FINGER_CLOSE_STEPS):
        t = min((step + 1) / FINGER_CLOSE_STEPS, 1.0)

        # Interpolate finger joint positions in FK model
        fk_jq = fk_state.joint_q.numpy()
        for arm_offset in [0, FRANKA_NUM_JOINTS]:
            fk_jq[arm_offset + 7] = finger_start[arm_offset + 7] + (FINGER_CLOSE_POS - finger_start[arm_offset + 7]) * t
            fk_jq[arm_offset + 8] = finger_start[arm_offset + 8] + (FINGER_CLOSE_POS - finger_start[arm_offset + 8]) * t
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

        state = physics_step(model, state, solver, contacts, scene_info)
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)

        # Monitor NaN and cable state
        if has_cable and (step < 5 or step % 10 == 0):
            bq = state.body_q.numpy()
            robot_nan = np.any(np.isnan(bq[: scene_info["robot_body_count"]]))
            cable_nan = np.any(np.isnan(bq[cable_bodies]))
            if robot_nan or cable_nan:
                print(f"    [CLOSE-NAN] step={step}: robot_nan={robot_nan}, cable_nan={cable_nan}")
                for bi in range(len(bq)):
                    if np.any(np.isnan(bq[bi])):
                        blabel = model.body_label[bi] if bi < len(model.body_label) else f"body{bi}"
                        print(f"      NaN body {bi} ({blabel}): {bq[bi][:3]}")
                        if bi >= 5:
                            print("      ... (showing first 5 NaN bodies)")
                            break
                nan_detected_step = step
                break
            cz = bq[cable_bodies, 2]
            b0 = bq[cable_bodies[0]]
            fj7 = fk_jq[7]
            fj8 = fk_jq[8]
            if step < 5 or step % 50 == 0 or abs(np.mean(cz) - TABLE_HEIGHT) > 0.005:
                print(
                    f"    [CLOSE-DIAG] step={step}: cable_z={np.mean(cz):.4f} "
                    f"finger=[{fj7 * 1000:.1f},{fj8 * 1000:.1f}]mm "
                    f"body0=[{b0[0]:.3f},{b0[1]:.3f},{b0[2]:.3f}]"
                )
    if nan_detected_step >= 0:
        print(f"  [P1-CLOSE] NaN detected at step {nan_detected_step}/{FINGER_CLOSE_STEPS}")

    # Read finger positions from FK state
    fk_jq = fk_state.joint_q.numpy()
    grip_l = fk_jq[7] + fk_jq[8]
    grip_r = fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8]
    print(f"  [P1-CLOSE] Grip: L={grip_l * 1000:.1f}mm R={grip_r * 1000:.1f}mm")

    # Step 4: Detailed position diagnostics
    wp.synchronize()
    bq = state.body_q.numpy()
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    pos_l, pos_r = get_ee_positions(state, scene_info)
    print("  [P1-DIAG] Left arm body positions:")
    print(f"    body6(hand): Z={bq[lb + 6][2]:.4f}")
    print(f"    body7(Lfin): Z={bq[lb + 7][2]:.4f}, Y={bq[lb + 7][1]:.4f}")
    print(f"    body8(Rfin): Z={bq[lb + 8][2]:.4f}, Y={bq[lb + 8][1]:.4f}")
    print(f"    b6-b7 offset: {(bq[lb + 6][2] - bq[lb + 7][2]) * 1000:.1f}mm")
    print("  [P1-DIAG] Right arm body positions:")
    print(f"    body6(hand): Z={bq[rb + 6][2]:.4f}")
    print(f"    body7(Lfin): Z={bq[rb + 7][2]:.4f}, Y={bq[rb + 7][1]:.4f}")
    print(f"    body8(Rfin): Z={bq[rb + 8][2]:.4f}, Y={bq[rb + 8][1]:.4f}")
    if has_cable:
        cable_z = [bq[b][2] for b in cable_bodies]
        cable_y = [bq[b][1] for b in cable_bodies]
        print(f"  [P1-DIAG] Cable: Z_mean={np.mean(cable_z):.4f}, Y_range=[{min(cable_y):.3f},{max(cable_y):.3f}]")

        # Compute finger shape world-space positions using body quaternion
        # body_q format: [x,y,z, qw,qx,qy,qz]
        b7_pos = bq[lb + 7][:3]
        b7_quat_raw = bq[lb + 7][3:7]  # Warp: [qx, qy, qz, qw]
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
                            R = np.array(
                                [
                                    [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qw * qz), 2 * (qx * qz + qw * qy)],
                                    [2 * (qx * qy + qw * qz), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qw * qx)],
                                    [2 * (qx * qz - qw * qy), 2 * (qy * qz + qw * qx), 1 - 2 * (qx * qx + qy * qy)],
                                ]
                            )
                            world_p = R @ p + b7_pos
                            corners.append(world_p)
                corners = np.array(corners)
                world_z_min = corners[:, 2].min()
                world_z_max = corners[:, 2].max()
                print(f"  [P1-DIAG] L-finger7 shape#{si} world Z: [{world_z_min:.4f}, {world_z_max:.4f}]")
                break
        print(f"  [P1-DIAG] Gap finger_world_bottom to cable: {(world_z_min - np.mean(cable_z)) * 1000:.1f}mm")

    # Check contacts (model.collide for BOX-CAPSULE)
    if has_cable:
        model.collide(state, contacts)
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
            finger_bodies_set = {lb + 7, lb + 8, rb + 7, rb + 8}
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
            print(
                f"  [P1-CONTACTS] breakdown: finger-cable={finger_cable}, "
                f"finger-other={finger_other}, cable-other={cable_other}, other={other}"
            )
            # Show first few contact pairs for debugging
            for ci in range(min(5, n_contacts)):
                b0 = shape_bodies_arr[shape0[ci]] if shape0[ci] >= 0 else -1
                b1 = shape_bodies_arr[shape1[ci]] if shape1[ci] >= 0 else -1
                print(f"    contact {ci}: shape({shape0[ci]},{shape1[ci]}) body({b0},{b1})")

    pos_l, pos_r = get_ee_positions(state, scene_info)

    # Raw evidence: P1 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log(
            "P1_complete",
            state,
            scene_info,
            extra={
                "grip_l_mm": round(grip_l * 1000, 2),
                "grip_r_mm": round(grip_r * 1000, 2),
            },
        )

    result = {
        "pass": True,
        "grip_l_mm": round(grip_l * 1000, 2),
        "grip_r_mm": round(grip_r * 1000, 2),
        "ee_left": pos_l.tolist(),
        "ee_right": pos_r.tolist(),
    }
    return state, result


def do_p2_lift(model, state, scene_info, solver, contacts):
    """P2: Micro-lift to confirm grip."""
    print(f"\n  {'=' * 50}")
    print("  [P2] Micro-Lift (grip confirmation)")
    print(f"  {'=' * 50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    grasp_dy = scene_info.get("cable_xy_offset", (0.0, 0.0))[1]  # ③ Y-follow (0.0 when unset = byte-identical)

    # Record cable Z before lift
    cable_z_before = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_before = np.mean(bq[cable_bodies, 2])
        print(f"  [P2] Cable Z before: {cable_z_before:.4f}")

    # Lift to LIFT_Z
    print(f"  [P2-LIFT] Target Z={LIFT_Z} (+{(LIFT_Z - GRASP_Z) * 1000:.0f}mm)")
    state, ok = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=(grasp_x, WIDE_LEFT_Y + grasp_dy, LIFT_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y + grasp_dy, LIFT_Z),
        label="P2-LIFT",
    )

    # Settle
    state = hold_position(model, state, scene_info, solver, contacts, SETTLE_STEPS)

    # Check cable lift
    cable_z_delta_mm = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_after = np.mean(bq[cable_bodies, 2])
        cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)
        print(f"  [P2] Cable Z after: {cable_z_after:.4f}, delta={cable_z_delta_mm}mm")

    # 07-Design terminal: cable lifted to LIFT_Z (absolute height).
    # LIFT_Z is EE body6 height; cable at fingertip ≈ LIFT_Z - EE_TO_FINGERTIP.
    cable_target_z = LIFT_Z - EE_TO_FINGERTIP  # 1.120 - 0.220 = 0.900
    if has_cable:
        bq_lift = state.body_q.numpy()
        cable_z_mean = np.mean(bq_lift[cable_bodies, 2])
        lifted = cable_z_mean >= cable_target_z
    else:
        cable_z_mean = 0.0
        lifted = True
    print(
        f"  [P2] Lift {'OK' if lifted else 'INSUFFICIENT'}: delta={cable_z_delta_mm}mm, "
        f"cable_z={cable_z_mean:.4f}, target={cable_target_z:.4f}"
    )

    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log(
            "P2_complete",
            state,
            scene_info,
            extra={
                "cable_z_delta_mm": cable_z_delta_mm,
                "lifted": lifted,
            },
        )

    result = {
        "pass": lifted,
        "cable_z_delta_mm": cable_z_delta_mm,
    }
    return state, result


def do_p3_move(model, state, scene_info, solver, contacts):
    """P3: Move from cable X to clip X."""
    print(f"\n  {'=' * 50}")
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    move_target_x = CLIP_X + P3_X_OFFSET
    print(f"  [P3] Move to Clip X ({grasp_x:.3f} → {move_target_x:.3f}  [CLIP_X={CLIP_X} + offset={P3_X_OFFSET}])")
    print(f"  {'=' * 50}")

    pos_l, pos_r = get_ee_positions(state, scene_info)

    state, ok = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=(move_target_x, pos_l[1], pos_l[2]),
        target_right=(move_target_x, pos_r[1], pos_r[2]),
        label="P3-MOVE",
        converge_mm=8.0,
    )

    state = hold_position(model, state, scene_info, solver, contacts, SETTLE_STEPS)

    # Raw evidence: P3 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        pos_l_final, pos_r_final = get_ee_positions(state, scene_info)
        evidence.log(
            "P3_complete",
            state,
            scene_info,
            extra={
                "target_x": move_target_x,
                "ee_left_final": pos_l_final.tolist(),
                "ee_right_final": pos_r_final.tolist(),
                "converged": ok,
            },
        )

    result = {"pass": ok}
    return state, result


def do_p4_push(model, state, scene_info, solver, contacts):
    """P4: Push both arms down to PUSH_Z."""
    print(f"\n  {'=' * 50}")
    print(f"  [P4] Push Down to Z={PUSH_Z}")
    print(f"  {'=' * 50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0

    cable_z_before = 0.0
    if has_cable:
        bq = state.body_q.numpy()
        cable_z_before = np.mean(bq[cable_bodies, 2])

    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(f"  [P4] Current EE Z: L={pos_l[2]:.4f} R={pos_r[2]:.4f}")
    print(f"  [P4] Current EE X: L={pos_l[0]:.4f} R={pos_r[0]:.4f}")
    print(
        f"  [P4] Push target: X={CLIP_X} (realign from P3 overshoot), Z={PUSH_Z} (dZ={((PUSH_Z - pos_l[2]) * 1000):.1f}mm)"
    )

    # P3 overshoots to CLIP_X+P3_X_OFFSET; P4 re-centers on CLIP_X during push-down.
    state, ok = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=(CLIP_X, pos_l[1], PUSH_Z),
        target_right=(CLIP_X, pos_r[1], PUSH_Z),
        label="P4-PUSH",
        speed_factor=2.0,  # slower push reduces cable XY inertia
    )

    # Longer settle for push (3x base: cable XY equilibration after push-down)
    state = hold_position(model, state, scene_info, solver, contacts, SETTLE_STEPS * 3)

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
        print(f"  [P4] Cable X range: [{np.min(cable_pos[:, 0]):.3f}, {np.max(cable_pos[:, 0]):.3f}]")
        print(f"  [P4] Cable Y range: [{np.min(cable_pos[:, 1]):.3f}, {np.max(cable_pos[:, 1]):.3f}]")

        # Check if cable is in clip groove (Z below top AND XY near clip)
        # Use point-to-segment distance (not point-to-body-center) to avoid
        # discretization artifacts: with ~15mm body spacing a 6mm groove radius
        # can miss even when the cable clearly passes through the groove.
        clip_top_z = CLIP1_Z + 0.030
        clip_xy = np.array([CLIP1_X, CLIP1_Y])
        groove_radius = CLIP_GROOVE_INNER_RADIUS

        # Point-to-body-center distances (for diagnostics / near-clip count)
        dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
        bodies_near_clip = int(np.sum(dists_xy < 0.030))  # 30mm

        # Point-to-segment distances (accurate for continuous cable)
        seg_dists = []
        for i in range(len(cable_pos) - 1):
            a = cable_pos[i, :2]
            b = cable_pos[i + 1, :2]
            ab = b - a
            t = np.clip(np.dot(clip_xy - a, ab) / (np.dot(ab, ab) + 1e-12), 0.0, 1.0)
            closest = a + t * ab
            seg_dists.append(float(np.linalg.norm(clip_xy - closest)))
        min_seg_dist = min(seg_dists) if seg_dists else float(np.min(dists_xy))
        bodies_in_groove = int(np.sum(np.array(seg_dists) < groove_radius))
        min_dist_xy_mm = round(min_seg_dist * 1000, 1)
        z_ok = cable_z_min < clip_top_z
        xy_ok = bodies_in_groove >= GROOVE_BODIES_MIN  # 07-Design: bodies in groove >= 2
        cable_in_groove = z_ok and xy_ok
        print(
            f"  [P4] Clip top Z={clip_top_z:.4f}, z_ok={z_ok}, "
            f"xy_dist_min={min_dist_xy_mm}mm, bodies_in_groove={bodies_in_groove}, "
            f"bodies_near_30mm={bodies_near_clip}, cable_in_groove={cable_in_groove}"
        )
    else:
        cable_in_groove = True  # No cable → pass

    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(
        f"  [P4] Final EE: L=({pos_l[0]:.4f},{pos_l[1]:.4f},{pos_l[2]:.4f}) "
        f"R=({pos_r[0]:.4f},{pos_r[1]:.4f},{pos_r[2]:.4f})"
    )

    # Raw evidence: P4 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log(
            "P4_complete",
            state,
            scene_info,
            extra={
                "cable_z_min": round(cable_z_min, 4) if has_cable else None,
                "cable_z_delta_mm": cable_z_delta_mm,
                "cable_in_groove": cable_in_groove,
                "clip_top_z": CLIP1_Z + 0.030 if has_cable else None,
                "bodies_in_groove_6mm": bodies_in_groove if has_cable else None,
                "bodies_near_clip_30mm": bodies_near_clip if has_cable else None,
                "min_dist_xy_mm": min_dist_xy_mm if has_cable else None,
            },
        )

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
def run_episode(model, state, scene_info, solver, contacts, episode_idx):
    """Run P1-P4 clip routing episode."""
    results = {"episode": episode_idx, "overall": "FAIL"}

    # Raw evidence: episode start
    evidence = scene_info.get("evidence")
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    if evidence:
        evidence.log(
            "episode_start",
            state,
            scene_info,
            extra={
                "episode": episode_idx,
                "settled_grasp_x": grasp_x,
                "original_grasp_x": GRASP_X,
                "grasp_x_drift_mm": round((grasp_x - GRASP_X) * 1000, 1),
            },
        )

    # === P1: Grasp ===
    state, p1 = do_p1_grasp(model, state, scene_info, solver, contacts)
    results["P1_grasp"] = p1
    if not p1["pass"]:
        results["fail_reason"] = "P1_grasp_fail"
        return state, results

    # === P2: Micro-lift ===
    state, p2 = do_p2_lift(model, state, scene_info, solver, contacts)
    results["P2_lift"] = p2
    if not p2["pass"]:
        results["fail_reason"] = "P2_lift_insufficient"
        print(f"  [P2] WARN: lift={p2['cable_z_delta_mm']}mm, continuing anyway")

    # === P3: Move to clip ===
    state, p3 = do_p3_move(model, state, scene_info, solver, contacts)
    results["P3_move"] = p3
    if not p3["pass"]:
        results["fail_reason"] = "P3_move_fail"

    # === P4: Push down ===
    state, p4 = do_p4_push(model, state, scene_info, solver, contacts)
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
        evidence.log(
            "episode_end",
            state,
            scene_info,
            extra={
                "episode": episode_idx,
                "overall": results["overall"],
            },
        )

    return state, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _run_mujoco_ik_motion_smoke(model, solver, contacts, scene_info, fk_state, output_dir=None):
    """S6 dual-arm IK-motion INFRA smoke (env-gate S6_IK_MOTION_SMOKE=1) — the S6 deliverable.

    Drives the articulated UR5e+Robotiq mujoco scene through a minimal dual-arm IK episode
    (seed -> IK HOVER -> IK APPROACH -> IK DESCEND -> scripted-kinematic CLOSE -> IK LIFT) and gates on
    MECHANICAL asserts only. INFRASTRUCTURE: it proves the swapped env runs an IK-driven episode with
    the gripper correctly oriented + closed -- it makes NO grasp/retention/grip-force claim (no cable;
    the mujoco branch runs contacts=None so the close is a KINEMATIC pose, not a force grasp; the
    faithful actuated close is deferred, R-S6.6). Mirrors _run_mujoco_tracking_smoke's exit gate:
    sys.exit(0 = PASS, 2 = FAIL). All geometry/seeds are probe-derived (probe_smoke_geom/probe_seq_diag).
    """
    fk_model = scene_info["fk_model"]
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    w3_l, w3_r = lb + EE_BODY_OFFSET, rb + EE_BODY_OFFSET

    # Table-clearing co-pose geometry (debate M1: OPEN-Z descend drove the CLOSED tip 55.6mm INTO the
    # table; probe_smoke_geom). Targets are wrist_3 world Z (no cable in this infra smoke).
    z_grasp = TABLE_HEIGHT + EE_TO_PINCH_TIP_CLOSED + 0.02  # descend: CLOSED tip clears the table (+20mm)
    z_approach = z_grasp + 0.05
    z_hover = z_grasp + 0.15
    x_wp, y_wp = 0.30, 0.20

    def tgt(z):
        return (x_wp, -y_wp, z), (x_wp, y_wp, z)  # (left, right) wrist_3 targets

    # UR5e 6-DOF hover seeds (probe_seq_diag: SEQUENTIAL-verified — hover->approach->descend->lift all
    # converge <5mm). An earlier static seed (probe_smoke_geom) put wrist_2 at +-pi/2, an IK branch where
    # the converged APPROACH config TRAPS the LM for DESCEND (zero progress, ruled out as collision/
    # joint-limit/iterations by probe_seq_diag); this seed sets wrist_2=+-2.0 (0.43 rad off the +-pi/2 trap)
    # -> the converged trajectory then stays ~pi from +-pi/2 (probe_seq_diag sing_margin_rad=3.142, post-debate fix).
    seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]
    seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]

    # Self-contained init: arm = hover seed, gripper = open (0). (debate M6: the shared main-init is
    # flag-only; this smoke does NOT rely on it.)
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:ARM_DOF] = seed_l
    fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    state = model.state()
    for _ in range(10):  # pose the mujoco scene from the hover seed (kinematic re-pose)
        state = physics_step(model, state, solver, contacts, scene_info)

    keyframes = {}

    def _triad(bq, w3):
        q = bq[w3][3:7]
        qq = wp.quat(float(q[0]), float(q[1]), float(q[2]), float(q[3]))
        ap = wp.quat_rotate(qq, wp.vec3(0.0, 1.0, 0.0))  # local +Y (approach) -> world
        sp = wp.quat_rotate(qq, wp.vec3(1.0, 0.0, 0.0))  # local X (finger-sep) -> world
        return float(-ap[2]), float(abs(sp[0]))  # down_dot(-Z), perp_|x|

    def _snap(name, bq):
        dl, pl = _triad(bq, w3_l)
        dr, pr = _triad(bq, w3_r)
        keyframes[name] = {
            "wrist3_L": [round(float(v), 4) for v in bq[w3_l][:3]],
            "wrist3_R": [round(float(v), 4) for v in bq[w3_r][:3]],
            "down_dot_L": round(dl, 4),
            "perp_L": round(pl, 4),
            "down_dot_R": round(dr, 4),
            "perp_R": round(pr, 4),
        }

    _snap("seed", state.body_q.numpy())  # raw IK seed pose (pre-IK initial guess; NOT a target/down-pose)

    # IK moves (speed_factor 0.2 -> ~1mm/step, fast on 0-GPU; DiffIK-safe). converge_mm gates each move.
    # First HOVER move turns the raw seed into a converged, gripper-down hover pose.
    ok = {}
    state, ok["hover"] = ik_move_both(
        model, state, scene_info, solver, contacts, *tgt(z_hover), label="S6-HOVER", converge_mm=5.0, speed_factor=0.2
    )
    _snap("hover", state.body_q.numpy())
    hover_fk_jq = fk_state.joint_q.numpy().copy()  # R-S6.2 C3: robust warm-start source for the post-close LIFT
    state, ok["approach"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(z_approach),
        label="S6-APPROACH",
        converge_mm=5.0,
        speed_factor=0.2,
    )
    _snap("approach", state.body_q.numpy())
    state, ok["descend"] = ik_move_both(
        model, state, scene_info, solver, contacts, *tgt(z_grasp), label="S6-DESCEND", converge_mm=5.0, speed_factor=0.2
    )
    bq_preclose = state.body_q.numpy().copy()
    _snap("descend_open", bq_preclose)

    # Scripted-kinematic CLOSE: ramp gripper [6..13]/[20..27] -> GRIPPER_CLOSE_QPOS (loop-consistent,
    # probe_closed_config_v2). n_close is a kinematic interpolation count (NOT the PD FINGER_CLOSE_STEPS;
    # contacts=None on the mujoco branch -> this is geometric posing, no force convergence).
    gstart = fk_state.joint_q.numpy().copy()
    n_close = 60
    for step in range(n_close):
        t = (step + 1) / n_close
        fk_jq = fk_state.joint_q.numpy()
        for k, j in enumerate(GRIPPER_JOINT_RANGE):
            fk_jq[j] = gstart[j] + (GRIPPER_CLOSE_QPOS[k] - gstart[j]) * t
            jr = JOINTS_PER_ARM + j
            fk_jq[jr] = gstart[jr] + (GRIPPER_CLOSE_QPOS[k] - gstart[jr]) * t
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        state = physics_step(model, state, solver, contacts, scene_info)
    bq_closed = state.body_q.numpy().copy()
    _snap("closed", bq_closed)

    # IK LIFT (finger_coords excludes the gripper -> the scripted close is held through the lift).
    # R-S6.2 C3/M1: re-seed the LIFT IK from the converged HOVER arm config (NOT the post-close config,
    # which is a 150mm LM-stuck point at the landed EE value; RS6_1_FINDINGS §2.2). Keep the closed
    # gripper sub-vector (arm-IK has zero Jacobian on gripper coords); overwrite ONLY the arm coords.
    lift_warmstart = fk_state.joint_q.numpy().copy()
    lift_warmstart[0:ARM_DOF] = hover_fk_jq[0:ARM_DOF]
    lift_warmstart[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = hover_fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF]
    state, ok["lift"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(z_hover),
        label="S6-LIFT",
        converge_mm=5.0,
        speed_factor=0.2,
        warmstart_jq=lift_warmstart,
    )
    bq_lift = state.body_q.numpy()
    _snap("lift", bq_lift)

    # --- ASSERTS (mechanical only; no grasp/force claim) ---
    moves_ok = bool(ok.get("hover") and ok.get("approach") and ok.get("descend") and ok.get("lift"))
    dd_l, pp_l = _triad(bq_lift, w3_l)
    dd_r, pp_r = _triad(bq_lift, w3_r)
    # triad_ok = the ANTI-HORIZONTAL-gripper gate (S5 P1.3 prior failure; debate H2). 0.99 rejects >~8deg
    # off-vertical (down_dot) and >~8deg off-world-X (perp; perp>0.99 also bounds finger-sep leak off cable-Y
    # to <0.14). It is an anti-horizontal gate, NOT a fine-orientation gate (post-debate CC4/CC5 M: ~8deg slack
    # at 0.99 documented; this smoke's full-quat IK objective lands at ~1.000, far inside it).
    triad_ok = bool(dd_l > 0.99 and dd_r > 0.99 and pp_l > 0.99 and pp_r > 0.99)
    pad_bodies = [lb + b for b in GRIPPER_PAD_BODY_IDX] + [rb + b for b in GRIPPER_PAD_BODY_IDX]
    # MIN (not max) over all 4 pad bodies -> a one-sided/partial close (one arm's pads not moving) FAILS the
    # gate (post-debate CC2/CC4 M: max would pass a half-closed gripper). production disp ~41mm/pad
    # (probe_smoke_geom); 20mm = conservative floor (debate M3).
    pad_disp = min(float(np.linalg.norm(bq_closed[p][:3] - bq_preclose[p][:3])) for p in pad_bodies) * 1000.0
    pad_ok = bool(pad_disp > 20.0)
    jq = state.joint_q.numpy()
    jqd = state.joint_qd.numpy()
    finite = bool(np.all(np.isfinite(jq)) and np.all(np.isfinite(bq_lift)))
    qvel_max = float(np.max(np.abs(jqd)))
    qvel_ok = bool(qvel_max < 100.0)
    # R-S6.2 C3: the LIFT must converge at a ROBUST wrist_2 margin (>=3.0 rad from the ±π/2 singularity),
    # not a fragile margin-0 seed (RS6_1_FINDINGS §2.3; the landed EE value would otherwise only converge
    # via margin-0 seeds). jq tracks the FK config on the mujoco branch (per-step joint_q overwrite).
    w2_margin = float(min(abs(abs(jq[4]) - np.pi / 2), abs(abs(jq[JOINTS_PER_ARM + 4]) - np.pi / 2)))
    margin_ok = bool(w2_margin >= 3.0)
    smoke_ok = bool(moves_ok and triad_ok and pad_ok and finite and qvel_ok and margin_ok)

    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "s6_ik_motion_smoke.json"), "w") as f:
                json.dump(
                    {
                        "smoke_ok": smoke_ok,
                        "moves_ok": moves_ok,
                        "triad_ok": triad_ok,
                        "pad_disp_mm": round(pad_disp, 2),
                        "pad_ok": pad_ok,
                        "finite": finite,
                        "qvel_max": round(qvel_max, 4),
                        "w2_margin_rad": round(w2_margin, 3),
                        "margin_ok": margin_ok,
                        "keyframes": keyframes,
                    },
                    f,
                    indent=2,
                )
            print(f"  [S6_IK_SMOKE] keyframe trajectory -> {os.path.join(output_dir, 's6_ik_motion_smoke.json')}")
        except Exception as e:  # noqa: BLE001 (diagnostic dump must not fail the gate)
            print(f"  [S6_IK_SMOKE] (keyframe dump skipped: {e})")

    print(
        f"  [S6_IK_SMOKE] moves_ok={moves_ok} (hover={ok.get('hover')},approach={ok.get('approach')},"
        f"descend={ok.get('descend')},lift={ok.get('lift')}) triad_ok={triad_ok} (L down={dd_l:.3f}/perp={pp_l:.3f}, "
        f"R down={dd_r:.3f}/perp={pp_r:.3f}) pad_disp={pad_disp:.1f}mm (>20={pad_ok}) "
        f"finite={finite} qvel_max={qvel_max:.3f} (<100={qvel_ok}) w2_margin={w2_margin:.3f} (>=3.0={margin_ok})"
    )
    print(
        f"  [S6_IK_SMOKE] smoke_ok={smoke_ok} "
        f"({'PASS -- S6 dual-arm IK episode runs (hover->approach->descend->close->lift)' if smoke_ok else 'FAIL'})"
    )
    sys.exit(0 if smoke_ok else 2)


def _set_gripper_target(control, driver_joints, target_rad):
    """R-S6.6: schedule the gripper POSITION-servo target by writing ``control.joint_target_pos`` on the
    driver dofs (the array SolverMuJoCo reads each step, solver_mujoco.py:362/:3606 -- NOT model-level,
    so a runtime change takes effect). ``model.control()`` seeds it from the build-time OPEN target."""
    tp = control.joint_target_pos.numpy()
    for d in driver_joints:
        tp[d] = float(target_rad)
    control.joint_target_pos.assign(tp)
    if _demo_rec is not None:  # P3 recorder: gripper CHOKEPOINT -> per-arm servo command (spec §2.2)
        _demo_rec.note_grip(driver_joints, target_rad)


# _wire_s6_grasp_solref RELOCATED to newton_skill_env_base.py (2026-06-28, L3 base-infra) + generalized
# for multi-world (build_scene single-world + build_multiworld_scene N-world share one SSOT). Imported
# lazily at the make_solver call-site to avoid the base<->test circular import.


def _run_mujoco_grasp_episode(model, solver, contacts, scene_info, fk_state, output_dir=None):
    """R-S6.6 (env-gate S6_GRASP=1): ACTUATED dual-arm grasp episode on the mujoco backend.

    The S6_GRASP path runs the gripper as a POSITION-actuated DYNAMIC joint (not a kinematic pose):
    physics_step excludes the gripper coords from the FK-overwrite (``gripper_dynamic=True``) for EVERY
    phase ("全エピソード dynamic"), the 4-bar connect equalities + servo drivers are wired in build_scene,
    the build-time S5 contact families (condim=6 + rolling) + the post-make_solver PAD_SOLREF poke are
    applied, and the close is driven by scheduling ``control.joint_target_pos`` OPEN(approach/descend) ->
    CLOSE(grasp/hold/lift) -- this REPLACES the scripted ``_ramp_gripper`` on THIS path only (H3; the 5
    legacy consumers keep ``gripper_dynamic=False`` = kinematic).

    CONSERVATISM / SCOPE (CPU 0-GPU): this runner BANKS the MECHANISM only -- the actuated channel drives
    the gripper, the wiring reaches the mjw GPU arrays (:func:`_wire_s6_grasp_solref` I11 asserts), and the
    production topology steps FINITE with bounded qvel. The literal table-cable grip MAGNITUDE, contact
    ENGAGEMENT against the descended cable, and retention-through-lift are NON-conservative on CPU and are
    DEFERRED to the in-chain GPU HARD gate (R-S7.1): grip force vs like-for-like 47.3N (task_config:303 is
    a fixed-harness reaction, compare in-grip per :300-302), mujoco-core #3328 tangential creep
    (LL-Newton:696-702), GPU contact-buffer adequacy, mujoco_warp<->MuJoCo-C parity, solref durability
    under CUDA capture. Emits ``[S6_GRASP]`` metric lines and ``sys.exit``\\ s (0 = PASS, 2 = FAIL).
    """
    assert scene_info.get("grasp_actuation"), "S6_GRASP runner needs build_scene(grasp_actuation=True)"
    assert scene_info.get("cable_bodies"), "S6_GRASP runner needs a cable (run WITHOUT --no-cable)"
    fk_model = scene_info["fk_model"]
    control = scene_info["vbd_control"]
    driver_joints = scene_info["driver_joints"]

    # Whole-episode dynamic gripper: physics_step excludes the gripper coords for EVERY phase. Start OPEN.
    scene_info["gripper_dynamic"] = True
    _set_gripper_target(control, driver_joints, GRIPPER_DRIVER_OPEN_RAD)

    def _ncon():
        try:
            return int(solver.mj_data.ncon)
        except Exception:
            return -1

    # Reuse the probe-derived geometry/seeds of _run_mujoco_ik_motion_smoke (proven to converge). NOTE the
    # close here is FREE-AIR, NOT a cable grasp: the arm descends to the cable X-line (X=GRASP_X=0.30) but
    # z_grasp keeps the CLOSED pinch-tip +20mm ABOVE the table (the OPEN pads higher still, clear of the
    # cable at z~0.804); free-air rests on this Z clearance. (The LEFT target Y=-0.20 is now ON the cable —
    # within Y span [-0.30,+0.30] after the 2026-06-20 array-centering, no longer off-cable in Y, still clear
    # in Z.) Evidence: the driver reaches its free-air target (NO cable-loaded stall), cable_z stays ~0.804. Only
    # the actuated-channel MECHANISM (driver travel) is banked; contact ENGAGEMENT (lands-on-cable,
    # OPEN-vs-CLOSED tip-drop, lateral capture) is GPU-deferred to R-S7.1. z/Y/seeds are intentionally NOT
    # tuned for engagement (that is the GPU gate's job).
    z_grasp = TABLE_HEIGHT + EE_TO_PINCH_TIP_CLOSED + 0.02  # CLOSED tip clears the table +20mm (free-air)
    z_approach = z_grasp + 0.05
    z_hover = z_grasp + 0.15
    x_wp, y_wp = 0.30, 0.20

    def tgt(z):
        return (x_wp, -y_wp, z), (x_wp, y_wp, z)

    seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]
    seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]

    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:ARM_DOF] = seed_l
    fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    state = model.state()
    for _ in range(10):  # settle the posed scene (gripper held OPEN by the servo)
        state = physics_step(model, state, solver, contacts, scene_info)
    drv_open = [float(state.joint_q.numpy()[d]) for d in driver_joints]

    ok = {}
    state, ok["hover"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(z_hover),
        label="GRASP-HOVER",
        converge_mm=5.0,
        speed_factor=0.2,
    )
    hover_fk_jq = fk_state.joint_q.numpy().copy()
    state, ok["approach"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(z_approach),
        label="GRASP-APPROACH",
        converge_mm=5.0,
        speed_factor=0.2,
    )
    state, ok["descend"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(z_grasp),
        label="GRASP-DESCEND",
        converge_mm=5.0,
        speed_factor=0.2,
    )

    # ACTUATED CLOSE (replaces the scripted _ramp_gripper, H3): schedule the driver target -> CLOSE and let
    # the POSITION servo + 4-bar equality drive the DYNAMIC gripper shut. This is a FREE-AIR close (see the
    # geometry note above) -- it banks the actuated-channel MECHANISM, NOT a grip on the cable.
    _set_gripper_target(control, driver_joints, GRIPPER_DRIVER_CLOSE_RAD)
    ncon_close = 0
    for _ in range(120):
        state = physics_step(model, state, solver, contacts, scene_info)
        ncon_close = max(ncon_close, _ncon())
    drv_closed = [float(state.joint_q.numpy()[d]) for d in driver_joints]

    # IK LIFT with the gripper held CLOSE (dynamic; target stays CLOSE). Re-seed the arm IK from the
    # converged HOVER config (R-S6.2 C3/M1); arm-IK has zero Jacobian on the gripper coords.
    lift_warmstart = fk_state.joint_q.numpy().copy()
    lift_warmstart[0:ARM_DOF] = hover_fk_jq[0:ARM_DOF]
    lift_warmstart[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = hover_fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF]
    state, ok["lift"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(z_hover),
        label="GRASP-LIFT",
        converge_mm=5.0,
        speed_factor=0.2,
        warmstart_jq=lift_warmstart,
    )

    # --- ASSERTS: MECHANISM (banked, CPU) only; grip magnitude + retention DEFERRED to GPU (R-S7.1) ---
    jq = state.joint_q.numpy()
    jqd = state.joint_qd.numpy()
    finite = bool(np.all(np.isfinite(jq)) and np.all(np.isfinite(state.body_q.numpy())))
    qvel_max = float(np.max(np.abs(jqd))) if finite else float("inf")
    qvel_ok = bool(finite and qvel_max < 100.0)
    moves_ok = bool(ok.get("hover") and ok.get("approach") and ok.get("descend") and ok.get("lift"))
    # actuation MECHANISM: every driver moved from ~OPEN(0) toward CLOSE under the servo (the dynamic
    # channel works). NOT a grip-force / grasp-success claim (GPU-deferred).
    close_travel = min((drv_closed[k] - drv_open[k]) for k in range(len(driver_joints))) if finite else 0.0
    actuated_ok = bool(finite and close_travel > 0.05)
    smoke_ok = bool(finite and qvel_ok and moves_ok and actuated_ok)

    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "s6_grasp_episode.json"), "w") as f:
                json.dump(
                    {
                        "smoke_ok": smoke_ok,
                        "finite": finite,
                        "qvel_max": round(qvel_max, 4),
                        "qvel_ok": qvel_ok,
                        "moves_ok": moves_ok,
                        "actuated_ok": actuated_ok,
                        "driver_open": [round(v, 4) for v in drv_open],
                        "driver_closed": [round(v, 4) for v in drv_closed],
                        "close_travel_rad": round(close_travel, 4),
                        "close_target_rad": float(GRIPPER_DRIVER_CLOSE_RAD),
                        "ncon_close_max": ncon_close,
                        "ncon_close_note": "topology contacts (e.g. cable<->table), NOT cable-grip; "
                        "free-air close, engagement GPU-deferred (R-S7.1)",
                        "scope": "MECHANISM banked (CPU); grip magnitude + retention GPU-deferred (R-S7.1)",
                    },
                    f,
                    indent=2,
                )
            print(f"  [S6_GRASP] metrics -> {os.path.join(output_dir, 's6_grasp_episode.json')}")
        except Exception as e:  # noqa: BLE001 (diagnostic dump must not fail the gate)
            print(f"  [S6_GRASP] (metrics dump skipped: {e})")

    print(
        f"  [S6_GRASP] moves_ok={moves_ok} (hover={ok.get('hover')},approach={ok.get('approach')},"
        f"descend={ok.get('descend')},lift={ok.get('lift')}) finite={finite} qvel_max={qvel_max:.3f} "
        f"(<100={qvel_ok})"
    )
    print(
        f"  [S6_GRASP] driver open={['%.3f' % v for v in drv_open]} -> closed={['%.3f' % v for v in drv_closed]} "
        f"(target {GRIPPER_DRIVER_CLOSE_RAD}) close_travel={close_travel:.4f}rad actuated_ok={actuated_ok} "
        f"ncon_close_max={ncon_close} (topology contacts, NOT cable-grip; free-air close, engagement GPU-deferred)"
    )
    print(
        f"  [S6_GRASP] smoke_ok={smoke_ok} "
        f"({'PASS -- actuated dynamic gripper drives the close; MECHANISM banked (CPU)' if smoke_ok else 'FAIL'}). "
        f"SCOPE: grip MAGNITUDE + contact engagement + retention-through-lift are NON-conservative on CPU -> "
        f"DEFERRED to the in-chain GPU HARD gate (R-S7.1)."
    )
    sys.exit(0 if smoke_ok else 2)


def _run_mujoco_grasp_engage_episode(model, solver, contacts, scene_info, fk_state, output_dir=None, record_video=False):
    """M-Grasp-engage-1 (env-gate S6_GRASP_ENGAGE=1): chain the BANKED koshape WR cradle cable-ENGAGED
    grasp+lift into the harness, REPLACING the free-air S6_GRASP descend (:3026/:3075-3113).

    Reuses the banked WR recipe (``eval_runs/.../r_s66_lift_hold_video_82.py``) by INTENT: vertical descend
    to the cradle depth ``z_grasp=1.0668`` (claws STRADDLE the cable -- f1ext ~0.797 below / f2ext ~0.809
    above cable-centre 0.809; NOT the free-air +20mm-above-table no-engage), actuated full-clamp CLOSE
    (transfers from S6_GRASP), 12-substep GRADUAL lift (a single 50mm move SLIPS = empty rise). Grasp at the
    88mm span (Y=+-GHS) on the cable-array centre Y=0 (M1 void re-centred there). REUSES ``ik_move_both`` (do
    NOT re-author); 先祖返り-fenced (no VBD ``run_episode``). INVARIANTS 88mm/dual-arm/コ reused, not changed.

    RETENTION mechanical-gate (%2 design-gate VERIFY M2, log:6712) -- TWO SEPARATE metrics via
    ``mj_geomDistance`` (solver-independent, the banked %9<->%2 cross-PV primitive):
      (i)  PAD-CRUSH CEILING: max pad1/pad2 <-> cable penetration <= 1.5mm (over-squeeze guard, bound ABOVE).
      (ii) f1ext FORM-CLOSURE FLOOR: the bottom claw engages the cable (deeper = better, banked -3.97mm
           healthy; NOT capped at 1.5mm, else a good deep grasp false-fails). BOTH arms engage.
    + HOLD-not-SLIP (cable_z rises with the claws, >=+30mm of the banked +45mm) + no-drop HOLD (sag~0). M3 =
    IK reachability at the Y=0 grasp (moves_ok; if it fails -> FAIL -> caller STOPs to %9). CONSERVATISM
    (GROVE §2.2): CPU PASS is NON-conservative on grip-MAGNITUDE + penetration x3 vs GPU (R-S7.1 deferred);
    a CPU SLIP/FAIL is conservative/definitive. Emits ``[S6_ENGAGE]`` lines + ``sys.exit``\\ s (0 PASS / 2 FAIL).
    """
    import mujoco  # lazy: CPU-path mj_model/mj_data (vbd runs never import it)

    assert scene_info.get("grasp_actuation"), "S6_GRASP_ENGAGE needs build_scene(grasp_actuation=True)"
    assert scene_info.get("cable_bodies"), "S6_GRASP_ENGAGE needs a cable (run WITHOUT --no-cable)"
    fk_model = scene_info["fk_model"]
    control = scene_info["vbd_control"]
    driver_joints = scene_info["driver_joints"]
    cable_bodies = scene_info["cable_bodies"]

    scene_info["gripper_dynamic"] = True  # whole-episode dynamic gripper (servo close, NOT kinematic)
    _set_gripper_target(control, driver_joints, GRIPPER_DRIVER_OPEN_RAD)

    # --- BANKED WR cradle geometry (reuse, NOT re-author) ---
    GHS = (WIDE_RIGHT_Y - WIDE_LEFT_Y) / 2.0  # 0.044 = GRIP_HALF_SPAN (88mm two-EE span, INVARIANT#2)
    # GRASP-ARRAY-CENTRE Y: 0.0 = milestone (cable-array centre, %2 M1 grasp_y=0); S6_ENGAGE_YC=0.15 = the
    # banked C1 DIAGNOSTIC (the banked WR existence-proof r_s66:121 grasps at YC=0.15 -> arms at
    # WIDE_LEFT_Y/WIDE_RIGHT_Y 0.106/0.194). Lets the +30 asymmetric be DIRECT-COMPARED Y=0 vs banked-C1.
    GRASP_YC = float(os.environ.get("S6_ENGAGE_YC", "0.0"))
    # WR cradle DEPTH = banked-correct z_grasp=1.0668 = ZE(TABLE_HEIGHT+CABLE_RADIUS+EE_TO_PINCH_CLOSED=1.0588)
    # + 0.008 (r_s66_lift_hold_video_82:46-47), the -4mm cradle depth ANCHORED to the cable-ON-TABLE rest
    # 0.804 (=TABLE_HEIGHT+CABLE_RADIUS; the banked recipe ALSO grasps the cable on-table at 0.804, GD-KoShape:76).
    # %9 course-correction 2026-06-26 (log:6716 + %2 cross-PV): the on-table 0.804 is COMMON to banked+harness
    # (0.809=GROOVE_CENTER_Z=the CLIP SEAT, NOT the grasp); my earlier cable-rest-derived 1.0618 OVER-descended
    # 5mm into the "-5mm FAILS" regime (GD-KoShape:70-73) -> f1ext gap/pad-pinch (run-2). REVERT to banked 1.0668.
    z_grasp = 1.0668
    z_high = z_grasp + 0.10  # hover start; the 8-substep descend interpolates z_high -> z_grasp
    LIFT_M, LIFT_SUBSTEPS = 0.05, 12  # WR HOLD path (single 50mm move SLIPS = empty rise)
    x_wp = GRASP_X

    def tgt(z):  # grasp the 88mm span centred on GRASP_YC (0.0 milestone / 0.15 banked-C1 diagnostic)
        return (x_wp, GRASP_YC - GHS, z), (x_wp, GRASP_YC + GHS, z)

    seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]  # proven hover seeds (probe_seq_diag)
    seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:ARM_DOF] = seed_l
    fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    state = model.state()
    for _ in range(10):
        state = physics_step(model, state, solver, contacts, scene_info)
    print(f"  [S6_ENGAGE] z_grasp={z_grasp:.4f} (banked 1.0668, cable-on-table 0.804) GRASP_YC={GRASP_YC:.3f}")

    # --- M2 retention helpers: mj_geomDistance over named geom sets (CPU mj_model/mj_data) ---
    mjm, mjd = getattr(solver, "mj_model", None), getattr(solver, "mj_data", None)
    assert mjm is not None and mjd is not None, "S6_GRASP_ENGAGE needs the CPU mj_model/mj_data (run CPU)"
    _ft = np.zeros(6)
    _BOX, _CAP = int(mujoco.mjtGeom.mjGEOM_BOX), int(mujoco.mjtGeom.mjGEOM_CAPSULE)

    def _gn(gi):
        return (mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_GEOM, int(gi)) or "").lower()

    pad_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and ("pad1" in _gn(g) or "pad2" in _gn(g))]
    f1_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and "f1ext" in _gn(g)]
    cable_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _CAP]

    def _min_dist_mm(setA, setB):
        mujoco.mj_forward(mjm, mjd)
        d = 1e9
        for a in setA:
            for b in setB:
                d = min(d, mujoco.mj_geomDistance(mjm, mjd, a, b, 0.05, _ft))
        return d * 1000.0  # mm; negative = penetration/overlap

    def _cable_z():
        wp.synchronize()
        return float(np.mean(state.body_q.numpy()[cable_bodies, 2]))

    print(f"  [S6_ENGAGE] geoms: pad1/2={len(pad_geoms)} f1ext={len(f1_geoms)} cable={len(cable_geoms)} "
          f"| GHS={GHS:.3f} z_grasp={z_grasp:.4f} (free-air ref 1.0957)")

    # §運用14 video (option B, %9/%2 2026-06-26): GL-free mujoco.Renderer (EGL offscreen, like the banked
    # r_s66_lift_hold_video_82) + matplotlib composite -- the harness ViewerGL recorder SEGFAULTS on the CPU
    # physics run. Renders the solver collision geoms (claw BOXes + cable CAPSULEs) from 3 cameras per checkpoint.
    _renderer = None
    _frames_dir = os.path.join(output_dir or ".", "_engage_frames")
    _fidx = [0]
    _cams = []
    if record_video:
        import matplotlib
        matplotlib.use("Agg")
        os.makedirs(_frames_dir, exist_ok=True)
        for _old in os.listdir(_frames_dir):
            if _old.endswith(".png"):
                os.remove(os.path.join(_frames_dir, _old))
        _renderer = mujoco.Renderer(mjm, height=480, width=640)
        # brighten (Rs 2026-06-26: the render was too dark) -- raise the model headlight ambient+diffuse (visual-only)
        mjm.vis.headlight.ambient[:] = [0.5, 0.5, 0.5]
        mjm.vis.headlight.diffuse[:] = [0.85, 0.85, 0.85]
        for _la, _az, _el, _d, _t in [
            ([x_wp, GRASP_YC, 0.83], 90.0, -6.0, 0.30, "side X-Z: cable rises WITH the claws (HELD)?"),
            ([x_wp, GRASP_YC, 0.83], 0.0, -10.0, 0.18, "front Y-Z: both claws straddle the cable?"),
            ([x_wp, GRASP_YC, 0.84], 235.0, -18.0, 0.34, "oblique"),
        ]:
            _c = mujoco.MjvCamera()
            _c.type = mujoco.mjtCamera.mjCAMERA_FREE
            _c.lookat[:] = _la
            _c.distance, _c.azimuth, _c.elevation = _d, _az, _el
            _cams.append((_t, _c))

    def _cap(phase):
        if _renderer is None:
            return
        import matplotlib.pyplot as plt
        mujoco.mj_forward(mjm, mjd)
        imgs = []
        for _nm, _c in _cams:
            _renderer.update_scene(mjd, camera=_c)
            _im = _renderer.render().astype(np.float32) * 1.3  # exposure lift (Rs 2026-06-26: brighten)
            imgs.append(np.clip(_im, 0, 255).astype(np.uint8))
        fig, axes = plt.subplots(1, len(imgs), figsize=(15, 4.6))
        for ax, im, (nm, _c2) in zip(axes, imgs, _cams):
            ax.imshow(im)
            ax.axis("off")
            ax.set_title(nm, fontsize=7.5, color="0.3")
        fig.suptitle(f"M-Grasp-engage-1 §運用14 ({DEVICE}) — z_grasp 1.0668 cradle + 12-substep gradual lift — {phase}",
                     fontsize=9.0)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.01, wspace=0.02)
        fig.savefig(os.path.join(_frames_dir, f"f{_fidx[0]:05d}.png"), dpi=98)
        plt.close(fig)
        _fidx[0] += 1

    _cap("REST")

    # --- MOTION (reuse ik_move_both, the banked recipe BY INTENT) ---
    ok = {}
    state, ok["hover"] = ik_move_both(model, state, scene_info, solver, contacts, *tgt(z_high),
                                      label="ENGAGE-HOVER", converge_mm=8.0, speed_factor=0.2, warmstart_jq=fk_jq)
    _cap("HOVER")
    # GRADUAL 8-substep DESCEND z_high -> z_grasp (banked r_s66_lift_hold_video_82:129-135; converge_mm=2.5 so
    # the claws REACH the cradle depth). DIAGNOSED 2026-06-26: the coarse converge_mm=5.0 3-jump left the claws
    # ~5mm HIGH of the cradle -> shallow f1ext (pad-pinch, NOT コ-notch form-closure; YC=0 f1ext -0.73/+0.01 vs
    # banked -3.97) -> the cable slips ~20mm during lift (+30 not banked +45). This is the banked TEMPLATE-MATCH.
    ok["descend"] = True
    for k in range(1, 9):
        zk = z_high + (z_grasp - z_high) * k / 8
        state, ok_k = ik_move_both(model, state, scene_info, solver, contacts, *tgt(zk),
                                   label=f"ENGAGE-DESCEND{k}/8-cradle", converge_mm=2.5, speed_factor=0.25)
        ok["descend"] = ok["descend"] and bool(ok_k)
        _cap(f"DESCEND {k}/8 -> cradle 1.0668")
    ok["approach"] = ok["descend"]  # (M3 moves_ok continuity; the single APPROACH jump folded into the 8-step descend)
    cable_z_grasp = _cable_z()
    cbq_grasp = state.body_q.numpy()[cable_bodies].copy()  # per-body cable pose at grasp (per-side rise diag)

    # 2-PHASE CLOSE (%9 decision 2026-06-26, "capture-then-gentle"; ACTUATED servo, NOT kinematic): PHASE 1 = a
    # brief FAST partial-close to snap-CAGE the cable (the コ f1ext bottom-hooks get inboard/under the cable
    # before it can roll out of the spread-open claws -- the failure mode of a PURE-gradual close: f1ext R +12mm,
    # pad-crush-close -2mm). PHASE 2 = a GRADUAL full-clamp so the final pad CONTACT + force-build is gentle
    # (Rs "too fast" 2026-06-26 = the contact moment). CAGE_FRAC tunes the cage threshold (raise if it fails).
    CAGE_FRAC = 0.9  # phase-1 partial-close fraction of CLOSE_RAD (snap-cage; 0.5 was below the cage threshold)
    cage_rad = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * CAGE_FRAC
    _set_gripper_target(control, driver_joints, cage_rad)  # PHASE 1: FAST snap to the cage fraction
    for _ in range(30):
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap(f"CAGE {int(CAGE_FRAC * 100)}% (snap-capture)")
    N_FINISH, FINISH_STEPS_PER = 12, 12  # PHASE 2: GRADUAL gentle full-clamp cage_rad -> CLOSE_RAD
    for ck in range(1, N_FINISH + 1):
        ctgt = cage_rad + (GRIPPER_DRIVER_CLOSE_RAD - cage_rad) * ck / N_FINISH
        _set_gripper_target(control, driver_joints, ctgt)
        for _ in range(FINISH_STEPS_PER):
            state = physics_step(model, state, solver, contacts, scene_info)
        if ck % 3 == 0:
            _cap(f"CLAMP {ck}/{N_FINISH} (gentle)")
    for _ in range(40):  # settle at full clamp
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap("CLOSED (cradle grip)")
    pad_crush_close = -_min_dist_mm(pad_geoms, cable_geoms)  # mm into the cable (>0 = penetration)
    f1_close = _min_dist_mm(f1_geoms, cable_geoms)  # <=0 = f1ext engaged at/under the cable

    # 12-substep GRADUAL lift (WR HOLD path), gripper held CLOSED. Chain the IK from the post-close cradle
    # config (banked r_s66:143-147, converge_mm=3.0 / speed 0.3; NO hover re-warmstart -- the cradle grip holds).
    ok["lift"] = True
    for k in range(1, LIFT_SUBSTEPS + 1):
        zl = z_grasp + LIFT_M * k / LIFT_SUBSTEPS
        state, ok_k = ik_move_both(model, state, scene_info, solver, contacts, *tgt(zl),
                                   label=f"ENGAGE-LIFT{k}/{LIFT_SUBSTEPS}", converge_mm=3.0, speed_factor=0.3)
        ok["lift"] = ok["lift"] and bool(ok_k)
        _cap(f"LIFT {k}/{LIFT_SUBSTEPS} (cable held?)")
    cable_z_lift = _cable_z()
    pad_crush_lift = -_min_dist_mm(pad_geoms, cable_geoms)
    f1_lift = _min_dist_mm(f1_geoms, cable_geoms)  # GLOBAL min (best claw) -- kept for continuity

    # --- PER-ARM DIAGNOSIS (%9 course-correction: isolate the +30 asymmetric "LEFT not lifted") ---
    # The global-min f1_lift reports only the DEEPEST claw, so a single engaged arm masks the other arm's
    # slip (the %2 M2(ii) "BOTH arms" blind spot). Split f1ext + cable rise by world-Y about the grasp centre.
    mujoco.mj_forward(mjm, mjd)
    _gy = mjd.geom_xpos[:, 1]
    f1_L = [g for g in f1_geoms if _gy[g] < GRASP_YC]
    f1_R = [g for g in f1_geoms if _gy[g] >= GRASP_YC]
    f1L_lift = _min_dist_mm(f1_L, cable_geoms) if f1_L else 9e9
    f1R_lift = _min_dist_mm(f1_R, cable_geoms) if f1_R else 9e9
    clawZ_L = float(min((mjd.geom_xpos[g][2] for g in f1_L), default=9e9))  # lowest L claw Z (reach-lag tell)
    clawZ_R = float(min((mjd.geom_xpos[g][2] for g in f1_R), default=9e9))  # lowest R claw Z
    cbq_lift = state.body_q.numpy()[cable_bodies]
    _cy = cbq_grasp[:, 1]
    _rise_pb = (cbq_lift[:, 2] - cbq_grasp[:, 2]) * 1000.0
    riseL = float(np.mean(_rise_pb[_cy < GRASP_YC])) if np.any(_cy < GRASP_YC) else 0.0
    riseR = float(np.mean(_rise_pb[_cy >= GRASP_YC])) if np.any(_cy >= GRASP_YC) else 0.0
    # GRASP-SPAN rise = the banked metric (r_s66_lift_hold_video_82:70 measures the cable body AT the grasp,
    # NOT the whole-cable mean). The 600mm rod's far ends (Y=+-0.30, 256mm from the 88mm grasp) stay ON the
    # table when the middle lifts +50mm -> the whole-cable mean is diluted. Retention = does the GRASPED
    # segment rise with the claws (HOLD-not-SLIP), which is the grasp-span rise, not the diluted mean.
    grasp_mask = np.abs(_cy - GRASP_YC) <= GHS  # cable bodies WITHIN the 88mm grasp span
    n_grasp = int(np.sum(grasp_mask))
    rise_grasp_mm = float(np.mean(_rise_pb[grasp_mask])) if n_grasp else float(np.mean(_rise_pb))

    for _ in range(120):  # no-drop HOLD
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap("HOLD (no-drop)")
    cable_z_hold = _cable_z()

    # --- M2 / M3 GATES ---
    jq, jqd = state.joint_q.numpy(), state.joint_qd.numpy()
    finite = bool(np.all(np.isfinite(jq)) and np.all(np.isfinite(state.body_q.numpy())))
    qvel_ok = bool(finite and float(np.max(np.abs(jqd))) < 100.0)
    moves_ok = bool(ok.get("hover") and ok.get("approach") and ok.get("descend") and ok.get("lift"))  # M3
    cable_rise_mm = (cable_z_lift - cable_z_grasp) * 1000.0
    sag_mm = (cable_z_lift - cable_z_hold) * 1000.0
    crush_ok = bool(max(pad_crush_close, pad_crush_lift) <= 1.5)  # M2(i) ceiling (over-squeeze guard)
    f1_engaged_ok = bool(max(f1L_lift, f1R_lift) <= 0.5)  # M2(ii) BOTH arms: the WORSE claw must engage (global-min blind-spot fix)
    hold_ok = bool(rise_grasp_mm >= 30.0)  # HOLD-not-SLIP at the GRASP SPAN (banked metric r_s66:70; the
    #   whole-cable mean `cable_rise_mm` is diluted by the 600mm rod's far ends resting on the table)
    nodrop_ok = bool(abs(sag_mm) <= 10.0)
    engage_ok = bool(finite and qvel_ok and moves_ok and crush_ok and f1_engaged_ok and hold_ok and nodrop_ok)

    metrics = {
        "engage_ok": engage_ok, "finite": finite, "qvel_ok": qvel_ok, "moves_ok_M3": moves_ok,
        "z_grasp": z_grasp, "GHS": round(GHS, 4),
        "pad_crush_close_mm": round(pad_crush_close, 3), "pad_crush_lift_mm": round(pad_crush_lift, 3),
        "crush_ceiling_ok_M2i": crush_ok,
        "f1ext_close_mm": round(f1_close, 3), "f1ext_lift_mm": round(f1_lift, 3),
        "f1ext_engaged_ok_M2ii": f1_engaged_ok,
        "f1L_lift_mm": round(f1L_lift, 3), "f1R_lift_mm": round(f1R_lift, 3),
        "clawZ_L": round(clawZ_L, 4), "clawZ_R": round(clawZ_R, 4),
        "cable_riseL_mm": round(riseL, 2), "cable_riseR_mm": round(riseR, 2), "GRASP_YC": round(GRASP_YC, 3),
        "cable_z_grasp": round(cable_z_grasp, 5), "cable_z_lift": round(cable_z_lift, 5),
        "cable_z_hold": round(cable_z_hold, 5), "cable_rise_mm": round(cable_rise_mm, 2),
        "rise_grasp_span_mm": round(rise_grasp_mm, 2), "n_grasp_bodies": n_grasp,
        "hold_not_slip_ok": hold_ok, "sag_mm": round(sag_mm, 2), "nodrop_ok": nodrop_ok,
        "scope": "CPU; grip-MAGNITUDE + penetration MAGNITUDE NON-conservative x3 vs GPU (R-S7.1 deferred)",
    }
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "s6_grasp_engage.json"), "w") as f:
                json.dump(metrics, f, indent=2)
            print(f"  [S6_ENGAGE] metrics -> {os.path.join(output_dir, 's6_grasp_engage.json')}")
        except Exception as e:  # noqa: BLE001 (diagnostic dump must not fail the gate)
            print(f"  [S6_ENGAGE] (metrics dump skipped: {e})")

    print(f"  [S6_ENGAGE] M3 moves_ok={moves_ok} (hover={ok.get('hover')},approach={ok.get('approach')},"
          f"descend={ok.get('descend')},lift={ok.get('lift')}) finite={finite} qvel_ok={qvel_ok}")
    print(f"  [S6_ENGAGE] M2(i) pad-crush close/lift={pad_crush_close:.2f}/{pad_crush_lift:.2f}mm (<=1.5 ceiling={crush_ok})")
    print(f"  [S6_ENGAGE] M2(ii) f1ext close/lift={f1_close:.2f}/{f1_lift:.2f}mm (<=0.5 engaged={f1_engaged_ok}; deeper=healthier)")
    print(f"  [S6_ENGAGE] PER-ARM f1ext L/R={f1L_lift:.2f}/{f1R_lift:.2f}mm | clawZ L/R={clawZ_L:.4f}/{clawZ_R:.4f} | "
          f"cable-rise L/R={riseL:.1f}/{riseR:.1f}mm (asymmetry diag; cable on-table {cable_z_grasp:.4f})")
    print(f"  [S6_ENGAGE] cable_z grasp/lift/hold={cable_z_grasp:.4f}/{cable_z_lift:.4f}/{cable_z_hold:.4f} "
          f"rise_GRASP-SPAN={rise_grasp_mm:.1f}mm(HOLD>={hold_ok}, n={n_grasp}) whole-cable-mean={cable_rise_mm:.1f}mm "
          f"sag={sag_mm:.1f}mm(nodrop={nodrop_ok})")
    print(f"  [S6_ENGAGE] engage_ok={engage_ok} "
          f"({'PASS -- cable-ENGAGED grasp+lift+retention (CPU)' if engage_ok else 'FAIL'}). "
          f"SCOPE: grip MAGNITUDE + penetration NON-conservative x3 vs GPU -> R-S7.1 deferred.")
    if record_video and _fidx[0] > 0:
        import subprocess
        mp4 = os.path.join(output_dir or ".", "s6_engage.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "2", "-i",
                        os.path.join(_frames_dir, "f%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-pix_fmt", "yuv420p", mp4], check=False)
        try:
            import shutil
            shutil.copy(mp4, os.path.expanduser("~/Downloads/s6_engage.mp4"))
        except Exception:  # noqa: BLE001 (the §運用14 copy must not fail the gate)
            pass
        print(f"  [S6_ENGAGE] §運用14 video ({_fidx[0]} frames @2fps) -> {mp4} + ~/Downloads/s6_engage.mp4")
    sys.exit(0 if engage_ok else 2)


# --- DQ7 stage-(ii) perturb-and-recover: kick-and-recover injection (flag-gated PERTURB_INJECT, default-off) -------
# A scheduled EE-target detour is applied to ONE arm for kick_calls ik_move_both call(s) (the "kick"), then RELEASED;
# the script's subsequent same-phase loop calls restore the achieved EE toward the script path (the recovery). The
# offline converter DROPs the kick frames (anti-restoring) and KEEPs the recovery (restoring teacher). Eligible v1
# phases: GRASP_DESCEND {1}, C2_REGRASP {11} (loop phases with in-phase recovery). PERTURB_INJECT unset -> off ->
# _inject_detour is a LITERAL passthrough (byte-identity). Spec: dq7_ii_mini_spec_v2.md §A/§B; %9 C1/C2; Rs GO 12:11.
_PJ_ELIGIBLE = ("GRASP_DESCEND", "C2_REGRASP")
_PJ_RELEASE_MARGIN = {"C2_REGRASP": 2}  # {11}: force offset=0 for the final N RHOVER calls -> reach-check/regrasp_ok clean (U5)


def _pj_load_schedule(path):
    """Load the PERTURB_INJECT schedule [dict] or return None (off). Asserts every injection phase is eligible (v2 §B)."""
    if not path:
        return None
    import json
    with open(path) as fh:
        raw = json.load(fh)
    injs = raw.get("injections", [])
    for e in injs:
        assert e["phase"] in _PJ_ELIGIBLE, (
            f"PERTURB_INJECT STOP: phase {e['phase']!r} not in eligible {_PJ_ELIGIBLE} "
            f"(SKIP-phase injection forbidden -- mini-spec v2 §B _ph-eligibility assert)"
        )
    return {"by_key": {(e["phase"], int(e["kick_call_idx"])): e for e in injs}, "open": None, "seed": raw.get("seed")}


def _pj_step(sched, rec, phase, call_idx, loop_len, tgl, tgr):
    """Stateful kick-and-recover target wrap (v2 §A/§B): offsets ONE arm during the kick, passes through otherwise.

    Opens a window at the scheduled (phase, kick_call_idx) (``rec.mark_injection`` start), holds it for kick_calls
    calls, then closes it (``rec.mark_injection`` end) so the recorded ``[start_frame, end_frame)`` marks the kick.
    The regrasp_ok release-margin guard (U5) refuses a kick that would still be open within the phase's
    verdict-critical tail. NEVER offsets both arms (INVARIANT#1). Called ONLY when ``sched`` is not None (the
    None-path literal passthrough is handled by the caller ``_inject_detour``).
    """
    op = sched.get("open")
    if op is not None and call_idx >= op["end_call"]:  # release -> recovery begins
        if rec is not None:
            rec.mark_injection(event="end")
        sched["open"] = op = None
    if op is None:  # maybe start a new kick here
        e = sched["by_key"].get((phase, call_idx))
        if e is not None:
            kc = int(e["kick_calls"])
            if call_idx + kc <= loop_len - _PJ_RELEASE_MARGIN.get(phase, 0):
                sched["open"] = op = {
                    "phase": phase, "arm": e["arm"], "offset_m": list(e["offset_m"]), "end_call": call_idx + kc
                }
                if rec is not None:
                    rec.mark_injection(
                        phase=phase, arm=e["arm"], offset_m=e["offset_m"], kick_calls=kc, seed=e.get("seed"),
                        event="start",
                    )
            else:
                print(
                    f"  [PERTURB_INJECT] SKIP {phase} kick@call{call_idx} (+{kc}) breaches release-margin of "
                    f"loop_len {loop_len} -> passthrough (regrasp_ok guard)"
                )
    if op is not None and op["phase"] == phase and call_idx < op["end_call"]:  # within the kick -> offset ONE arm
        o = op["offset_m"]
        if op["arm"] == "R":
            return tgl, (tgr[0] + o[0], tgr[1] + o[1], tgr[2] + o[2])
        return (tgl[0] + o[0], tgl[1] + o[1], tgl[2] + o[2]), tgr
    return tgl, tgr


def _run_mujoco_grasp_route(model, solver, contacts, scene_info, fk_state, output_dir=None, record_video=False):
    """M-Route-1 / M-Route-2 C1 (env-gate S6_GRASP_ROUTE=1): the BANKED centred grasp+lift (M-Grasp-engage-1) +
    AERIAL TRANSPORT (GX 0.30 -> CLIP_X, both arms together) + a CONTINUOUS two-claw cage + drop-in seat@809.
    CLIP_Y=0 = M-Route-1 (centred, X-only). CLIP_Y!=0 = M-Route-2 (DIAGONAL drag to an OFF-CENTRE clip, e.g. C1
    (0.35,+0.150) CLIP_X=0.35 CLIP_Y=0.150): the route loop interpolates BOTH x and the grasp-centre yck while
    holding the 88mm span (yck+-GHS) -> the LEFT arm STRETCHES (lateral ~0.456 near-reach) / the RIGHT FOLDS
    (~0.156) = the asymmetric diagonal drag (INVARIANT#1-compliant: both arms move, neither parked). The seat
    refs follow the gripped seg to y_clip; the cable<->clip mj_geomDistance AT seat = the real-seat proof.

    FAITHFUL-TO-INTENT of the banked CPU r_s71_clip_dropin_72 (the ROUTE step :226-231: symmetric X move both
    arms at z_lift); NOT a port of the legacy VBD do_p3_move/do_p4_push (先祖返り-fenced). REUSES ik_move_both /
    the 2-phase コ close / the WR lift. The DROP-IN/seat (809) = M-Hook-1, a SEPARATE next milestone -- NOT here.
    INVARIANTS untouched: 88mm span (Y=+-GHS), dual-arm both arms route together, DiffIK (ik_move_both), コ.

    PRE-STEP caveat-a (%9 MANDATORY): centre the grasp on the SETTLED cable Y so BOTH arms contact symmetrically
    (the 0.74mm off-centre cable gave L-deep/R-12um-hairgap; the drag load-tests the marginal RIGHT harder).
    CONTINUOUS gate (%2 owns M2ii): at EVERY route waypoint, BOTH arms' f1ext must be UNDER the cable
    (mj_geomDistance fromto = dz-VERTICAL, not lateral=beside) AND within the cage; + nodrop (sag<=10mm through
    the WHOLE route); + caveat-d drag (the draping far-ends must not pull the span out / snag). CPU; grip-magnitude
    + penetration NON-conservative x3 vs GPU. Emits [S6_ROUTE] + sys.exit (0 PASS / 2 FAIL).
    """
    import mujoco  # lazy: CPU mj_model/mj_data

    assert scene_info.get("grasp_actuation"), "S6_GRASP_ROUTE needs build_scene(grasp_actuation=True)"
    assert scene_info.get("cable_bodies"), "S6_GRASP_ROUTE needs a cable (run WITHOUT --no-cable)"
    fk_model = scene_info["fk_model"]
    control = scene_info["vbd_control"]
    driver_joints = scene_info["driver_joints"]
    cable_bodies = scene_info["cable_bodies"]
    scene_info["gripper_dynamic"] = True
    _set_gripper_target(control, driver_joints, GRIPPER_DRIVER_OPEN_RAD)

    global _demo_rec
    if os.environ.get("DEMO_RECORD", "0") == "1":  # P3 whole-route demo RECORDER (env-gated, read-only; spec §2)
        from route_demo_recorder import RouteDemoRecorder

        _demo_rec = RouteDemoRecorder(
            scene_info, EE_BODY_OFFSET, driver_joints[:2], driver_joints[2:],  # per-arm drivers, SSOT :1461
            os.environ.get("DEMO_OUT", "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/demo_raw"),
            {"dt": DT, "sim_dt": SIM_DT, "sim_substeps": SIM_SUBSTEPS, "device": DEVICE,
             "solver_backend": scene_info.get("solver_backend"),
             # F2: physics-model joint_label (74=2*JPA+cable), not fk_model.joint_key (28, wrong obj)
             "joint_names": list(getattr(scene_info["model"], "joint_label", []) or []),
             "joint_names_source": "physics_model.joint_label",
             "arm_q_layout": {"l_arm": [0, JOINTS_PER_ARM], "r_arm": [JOINTS_PER_ARM, 2 * JOINTS_PER_ARM],
                              "cable": [2 * JOINTS_PER_ARM, None]},
             # env-resolved (no hardcode); mirrors the route's own resolution (c1 :3543-3544 / c2 :3591-3592)
             "resolved_clip_c1_xy": [float(os.environ.get("CLIP_X", "0.40")), float(os.environ.get("CLIP_Y", "0.0"))],
             "resolved_clip_c2_xy": [float(os.environ.get("CLIP2_X", str(CLIP_POSITIONS[1][0]))),
                                     float(os.environ.get("CLIP2_Y", str(CLIP_POSITIONS[1][1])))],
             "anti_revert_marker_lines": _ANTI_REVERT_MARKER_LINES})

    def _ph(name):  # P3 recorder: label the native route section (forward, at each block start; spec §2.6)
        if _demo_rec is not None:
            _demo_rec.set_phase(name)

    # DQ7 (ii): load the injection schedule ONCE (None when PERTURB_INJECT is unset -> hook = literal passthrough).
    _pj_sched = _pj_load_schedule(os.environ.get("PERTURB_INJECT", ""))

    def _inject_detour(phase_name, call_idx, loop_len, tgl, tgr):
        """kick-and-recover hook wrapping an ik_move_both target arg (v2 §B). None-path = LITERAL passthrough."""
        if _pj_sched is None:
            return tgl, tgr  # U11/C1 byte-identity: returns the EXACT target tuples unchanged (pure-Python, no round-trip)
        return _pj_step(_pj_sched, _demo_rec, phase_name, call_idx, loop_len, tgl, tgr)

    GHS = (WIDE_RIGHT_Y - WIDE_LEFT_Y) / 2.0  # 0.044 = 88mm span INVARIANT#2
    z_grasp = 1.0668  # banked WR cradle (M-Grasp-engage-1 validated)
    z_high = z_grasp + 0.10
    # W0-e transport-clearance raise (Rs 2026-07-05「c1 搬送で高さ不足→clip 上面かする」, /geometric-design gate):
    # 0.05->0.08 (+30mm) so the transported cable centre clears the clip high-wall top (850mm @float20) + cable r4 +
    # margin5 = >=859mm (measured baseline 831mm scraped). GLOBAL (nominal too = Rs baseline correction -> new sha).
    # Also lands the C1_SEAT-else descent START above the clip -> the existing v1 X-comp descent seats VERTICALLY (no
    # wall-ride) = the v2 physics re-expressed in COORDINATES, no new legs (step-table-faithful). env-overridable to tune.
    LIFT_M, LIFT_SUBSTEPS = float(os.environ.get("W0E_LIFT_M", "0.08")), 12
    z_lift = z_grasp + LIFT_M  # aerial transport height (lift end)
    x_grasp = GRASP_X  # 0.30
    x_clip = float(os.environ.get("CLIP_X", "0.40"))  # banked void-cleared target (NOT C3 0.35 on the void)
    y_clip = float(os.environ.get("CLIP_Y", "0.0"))  # M-Route-2: off-centre clip Y (C1=+0.150); 0.0 = centred M-Route-1
    N_ROUTE = 6  # banked r_s71:228 symmetric X waypoints
    GRASP_YC = 0.0  # nominal; caveat-a re-centres on the settled cable below

    mjm, mjd = getattr(solver, "mj_model", None), getattr(solver, "mj_data", None)
    assert mjm is not None and mjd is not None, "S6_GRASP_ROUTE needs CPU mj_model/mj_data"
    _freeze_scope_rec = None   # PERCLIP_PIN (b)-pin freeze-scope record (%3 charter); persisted into metrics below
    _c2_settle_rec = None   # C2_DUALSEAT release-and-settle record (%0 seat-capture concern, charter metric #3)
    _c2_regrasp_rec = None   # C2_DUALSEAT R re-grasp record (Rs guide-data charter: R-reach + R-grip-nonzero, %0 cross-PV)
    _BOX, _CAP = int(mujoco.mjtGeom.mjGEOM_BOX), int(mujoco.mjtGeom.mjGEOM_CAPSULE)

    def _gn(gi):
        return (mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_GEOM, int(gi)) or "").lower()

    pad_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and ("pad1" in _gn(g) or "pad2" in _gn(g))]
    f1_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and "f1ext" in _gn(g)]  # BOTTOM claw
    f2_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and "f2ext" in _gn(g)]  # TOP claw
    cable_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _CAP]

    # PART 1 GATE-FIX (%2 log:6738 two-claw cage): retention = the cable is SANDWICHED between the two claws
    # (f1ext bottom + f2ext top, mouth ~10mm, Ø8 cable -> ~2mm play; GD-KoShape-Finger.md:51-58) AND laterally
    # within the claw footprint. The OLD f1ext-only gate false-FAILed "cable risen to the TOP claw under drag"
    # (f1_gap grows but f2 holds it = still caged). New PASS = |f1_gap + Ø8 + f2_gap - mouth| <= tol  AND
    # |cable_x - claw_x| < claw half-extent. Real escape is LATERAL (out the open コ mouth, world X = route axis).
    CABLE_DIAM_MM = 2.0 * CABLE_RADIUS * 1e3  # 8.0
    MOUTH_MM = 10.0  # f1ext<->f2ext inner gap (GD-KoShape-Finger.md:58)
    SAND_TOL_MM = 3.0  # cable "between claws" if f1+Ø8+f2 in [7,13]mm (snug rests-on-bottom sum=10; drag-to-top sum=10)
    LATERAL_MAX_MM = 9.0  # claw half-extent in the closing axis (pad-local half_y 0.009; GD-KoShape-Finger.md:51-54)
    # PART 2 M-Hook-1 (banked r_s71_clip_dropin_72): drop-in onto the REAL collidable clip at (CLIP_X, CLIP_Y).
    REL_CABLE_Z = float(os.environ.get("REL_CABLE_Z", "0.820"))  # banked depth: lower the claw to the wall top
    # CLIP_FLOAT_Z (human-Rs FLOAT-the-clips probe, 0-commit): the SAME h read in build_scene (clip boxes). Here it
    # floats the cable SEAT target (GROOVE_CENTER_Z+h), the gripper DESCENT target (seat_ee_z/c2_seat_ee_z = seat+ee_off),
    # and the retention wall criterion (LOW_WALL_TOP = CLIP1_Z+h+0.020). TABLE_HEIGHT STAYS 0.80 (the table is what the
    # float clears). DEFAULT 0.0 -> byte-identical. NOTE: GRASP_Z/PUSH_Z (task_config) are the LEGACY P1-P4 path, NOT
    # used by route_c1_c2 -> the route descent target is GROOVE_CENTER_Z+ee_off (dynamic), floated below.
    _clip_float_z = float(os.environ.get("CLIP_FLOAT_Z", "0.0"))
    _ROUTE_C2 = os.environ.get("S13_ROUTE_C2", "0") == "1"  # %3 Rs C1->C2 routing directive (half-unclamp + guide)
    DO_HOOK = (os.environ.get("S6_HOOK", "1") == "1") and not _ROUTE_C2  # C1->C2 supplies its own clamped seat
    _clip_collidable = os.environ.get("CLIP_COLLISION", "0") == "1"
    # C2 (Rs directive): canonical CLIP_POSITIONS[1]=(0.40,+0.075); overridable for sweeps. Used by _clip2_geoms
    # (the cable<->C2 reach proof) and the §運用14 C2 label/camera. Built only when CLIP2=1 (build_scene).
    c2x = float(os.environ.get("CLIP2_X", str(CLIP_POSITIONS[1][0])))
    c2y = float(os.environ.get("CLIP2_Y", str(CLIP_POSITIONS[1][1])))

    def _min_dist_mm(setA, setB):
        mujoco.mj_forward(mjm, mjd)
        d = 1e9
        for a in setA:
            for b in setB:
                d = min(d, mujoco.mj_geomDistance(mjm, mjd, a, b, 0.05, np.zeros(6)))
        return d * 1000.0

    def _clip_geoms():
        # %9 ADD (real-seat proof): the clip's collision BOXes for the cable<->clip mj_geomDistance AT seat (vs an
        # ee_off-stale FALSE-seat; M-Hook-1 gave -0.053mm). The 5 clip parts are small worldbody (bodyid 0) BOXes
        # clustered at (x_clip, y_clip); the table (also worldbody) is centred far in Y -> excluded by the XY gate.
        mujoco.mj_forward(mjm, mjd)
        return [g for g in range(mjm.ngeom)
                if int(mjm.geom_type[g]) == _BOX and int(mjm.geom_bodyid[g]) == 0
                and abs(float(mjd.geom_xpos[g][0]) - x_clip) < 0.03
                and abs(float(mjd.geom_xpos[g][1]) - y_clip) < 0.03]

    def _clip2_geoms():
        # C2 (Rs C1->C2 routing): the SECOND clip's collision BOXes near (c2x, c2y) for the cable<->C2 mj_geomDistance
        # reach/seat proof. Same worldbody-BOX-near-XY filter as _clip_geoms but centred on C2 (C1 excluded: dx>=50mm).
        mujoco.mj_forward(mjm, mjd)
        return [g for g in range(mjm.ngeom)
                if int(mjm.geom_type[g]) == _BOX and int(mjm.geom_bodyid[g]) == 0
                and abs(float(mjd.geom_xpos[g][0]) - c2x) < 0.03
                and abs(float(mjd.geom_xpos[g][1]) - c2y) < 0.03]

    def _table_geoms():
        # the LARGE worldbody BOXes = the table (1 solid box, or the 4 grasp-slot boxes). Small clip BOXes (<=25mm)
        # are excluded by the size gate -> separates a "claw vs SOLID table JAM" from a "claw vs cable/clip" contact
        # (OPS-SUP cross-PV flag 2: the C2-over-solid jam is geometry, NOT the cable-physics drag).
        return [g for g in range(mjm.ngeom)
                if int(mjm.geom_type[g]) == _BOX and int(mjm.geom_bodyid[g]) == 0
                and float(np.max(mjm.geom_size[g])) > 0.05]

    def _cage_pair(arm_geoms):
        # closest (claw <-> cable) pair for this arm's claw-set: (dist_mm, fromto6, claw_gid, cable_gid).
        # fromto = [claw_pt(3), cable_pt(3)]; gap = cable_pt - claw_pt.
        mujoco.mj_forward(mjm, mjd)
        best_d, best_ft, best_claw, best_cab = 1e9, None, -1, -1
        for a in arm_geoms:
            for b in cable_geoms:
                ft = np.zeros(6)
                d = mujoco.mj_geomDistance(mjm, mjd, a, b, 0.06, ft)
                if d < best_d:
                    best_d, best_ft, best_claw, best_cab = d, ft.copy(), a, b
        return best_d * 1000.0, best_ft, best_claw, best_cab

    def _cage(f1set, f2set):
        # %2 two-claw cage (PART 1 GATE-FIX): the cable is HELD iff (a) it is SANDWICHED between the bottom
        # (f1ext) and top (f2ext) claws -- |f1_gap + Ø8 + f2_gap - mouth| <= tol -- AND (b) laterally within the
        # claw footprint -- |cable_x - claw_x| < claw half-extent (the open コ mouth faces world X = the route axis).
        d1, ft1, claw1, cab1 = _cage_pair(f1set)  # bottom claw
        d2, _ft2, _c2, _b2 = _cage_pair(f2set)  # top claw
        sand_sum = d1 + CABLE_DIAM_MM + d2
        sandwiched = bool(abs(sand_sum - MOUTH_MM) <= SAND_TOL_MM)
        vert1 = False  # f1ext fromto mostly-vertical = the bottom claw UNDER the cable (form-closure direction)
        if ft1 is not None:
            g = ft1[3:6] - ft1[0:3]
            gn = float(np.linalg.norm(g)) + 1e-9
            vert1 = bool(abs(g[2]) / gn > 0.6)
        lateral_mm = 9e9
        if claw1 >= 0 and cab1 >= 0:
            lateral_mm = abs(float(mjd.geom_xpos[cab1][0] - mjd.geom_xpos[claw1][0])) * 1e3
        lateral_ok = bool(lateral_mm < LATERAL_MAX_MM)
        held = bool(sandwiched and lateral_ok)
        return {"f1": round(d1, 3), "f2": round(d2, 3), "sand": round(sand_sum, 2),
                "sandwiched": sandwiched, "f1_vert": vert1, "lat": round(lateral_mm, 2),
                "lat_ok": lateral_ok, "held": held}

    def _cable_z():
        wp.synchronize()
        return float(np.mean(state.body_q.numpy()[cable_bodies, 2]))

    def _seg_z_mm(y_ref):
        # gripped-segment z [mm]: the cable bodies WITHIN the grasp span (|Y - y_ref| <= GHS) -- the held middle
        # that travels to the clip + seats. NOT the whole-cable mean (the 600mm rod's far ends dilute it = the
        # M-Grasp-engage artifact). Seated z~=809 (GROOVE_CENTER_Z); resting on the clip top ~834.
        wp.synchronize()
        bq = state.body_q.numpy()[cable_bodies]
        m = np.abs(bq[:, 1] - y_ref) <= GHS
        return float(np.mean(bq[m, 2]) if np.any(m) else np.mean(bq[:, 2])) * 1e3

    def _arm_split():
        # split BOTH claw-sets into (f1_L, f1_R, f2_L, f2_R) by world-Y about the grasp centre.
        mujoco.mj_forward(mjm, mjd)
        gy = mjd.geom_xpos[:, 1]
        return ([g for g in f1_geoms if gy[g] < GRASP_YC], [g for g in f1_geoms if gy[g] >= GRASP_YC],
                [g for g in f2_geoms if gy[g] < GRASP_YC], [g for g in f2_geoms if gy[g] >= GRASP_YC])

    # --- §運用14 GL-free render (mujoco.Renderer + matplotlib, like M-Grasp-engage-1) ---
    _renderer = None
    _frames_dir = os.path.join(output_dir or ".", "_route_frames")
    _fidx = [0]
    _cams = []
    if record_video:
        import matplotlib
        matplotlib.use("Agg")
        os.makedirs(_frames_dir, exist_ok=True)
        for _old in os.listdir(_frames_dir):
            if _old.endswith(".png"):
                os.remove(os.path.join(_frames_dir, _old))
        _renderer = mujoco.Renderer(mjm, height=480, width=640)
        mjm.vis.headlight.ambient[:] = [0.5, 0.5, 0.5]
        mjm.vis.headlight.diffuse[:] = [0.85, 0.85, 0.85]
        _mx = 0.5 * (x_grasp + x_clip)
        _my = 0.5 * (0.0 + y_clip)  # diagonal-route midpoint Y (grasp centre 0 -> off-centre clip y_clip)
        _camspec = [
            ([_mx, _my, 0.85], 90.0, -6.0, 0.46, "side X-Z: aerial diagonal transport, cable held?"),
            ([x_clip, y_clip, 0.83], 0.0, -14.0, 0.24, "front Y-Z @clip: steep slot-descent into the groove?"),
            ([_mx, _my, 0.86], 235.0, -22.0, 0.50, "oblique diagonal"),
        ]
        if os.environ.get("CLIP_DELTAH", "0") == "1" or os.environ.get("S13_TAIL_HOLD", "0") == "1":
            # %3 video-confirm probe (2026-06-30): add overhead + a tight FRONT zoom on body30<->clip (the delta-h
            # escape / B tail-hold retention) + a tight zoom on the adjacent-below region (claw <-> clip Y-edge =
            # the re-grasper claw). Shared by CLIP_DELTAH and the S13_TAIL_HOLD (direction-B) retention probe.
            _camspec += [
                ([x_clip, y_clip, 0.81], 90.0, -82.0, 0.30, "overhead: seat + claws (top-down)"),
                ([x_clip, y_clip, 0.815], 0.0, -10.0, 0.085, "ZOOM front: body30 in the OPEN-TOP groove (escape?)"),
                ([x_clip, y_clip - 0.013, 0.808], 28.0, -8.0, 0.11, "ZOOM: adjacent-below claw <-> clip Y-edge"),
            ]
        if os.environ.get("S13_FEED", "0") == "1":
            # しごき slide-through (option-1 CORRECTED): CLAW-LOCAL zoom on the FEED hand. (a) FRONT Y-Z spanning
            # the seat AND the feed lane -> the cable runs left-right (Y); SLIDE = the cable stays put while the
            # finger moves; DRAG = the cable moves with the finger. (b) SIDE X-Z tight on the feed claw -> the
            # cradle wrap. The seat (clip groove) is kept in (a) throughout.
            _camspec += [
                ([x_clip, y_clip - 0.020, 0.812], 0.0, -10.0, 0.17, "ZOOM front Y-Z: seat + FEED hand (cable SLIDE vs DRAG)"),
                ([x_clip, y_clip - 0.040, 0.810], 90.0, -10.0, 0.11, "ZOOM side X-Z: FEED claw cradles cable"),
            ]
        if _ROUTE_C2:
            # %3 Rs C1->C2 routing: (a) OVERHEAD over both clips + the cable path, (b) a FRONT Y-Z spanning the C1
            # seat and the L guide toward C2, (c) a CLAW-LOCAL zoom on the L half-clamp (slide vs drag), (d) an
            # oblique of both arms. lookat = the C1<->C2 midpoint so both clips stay in frame.
            _midx, _midy = 0.5 * (x_clip + c2x), 0.5 * (y_clip + c2y)
            _camspec += [
                ([_midx, _midy, 0.81], 90.0, -80.0, 0.42, "OVERHEAD: C1+C2 + cable path (both clips)"),
                ([_midx, _midy, 0.83], 0.0, -12.0, 0.36, "front Y-Z: C1 seat + L half-clamp GUIDE toward C2"),
                ([x_clip, y_clip - 0.030, 0.812], 35.0, -8.0, 0.13, "ZOOM L claw: half-clamp + cable SLIDE vs DRAG"),
                ([_midx, _midy, 0.85], 235.0, -22.0, 0.46, "oblique: both arms, C1->C2 route"),
            ]
            # §運用14 clip coloring for the mj render: C1 green / C2 cyan (geom_rgba is render-only, no physics).
            for _cg in _clip_geoms():
                mjm.geom_rgba[_cg] = [0.20, 0.80, 0.35, 1.0]
            for _cg in _clip2_geoms():
                mjm.geom_rgba[_cg] = [0.10, 0.70, 0.92, 1.0]
        for _la, _az, _el, _d, _t in _camspec:
            _c = mujoco.MjvCamera()
            _c.type = mujoco.mjtCamera.mjCAMERA_FREE
            _c.lookat[:] = _la
            _c.distance, _c.azimuth, _c.elevation = _d, _az, _el
            _cams.append((_t, _c))

    # L/R EE label overlay (Rs frame-clarity 2026-06-30): R = +Y-side arm (anchor/holder, ROBOT_RIGHT_BASE Y=+0.35),
    # L = -Y-side arm (mover/しごき, ROBOT_LEFT_BASE Y=-0.35). get_ee_positions returns (left, right).
    _LABEL_LR = bool(record_video and (os.environ.get("S13_FEED", "0") == "1" or _ROUTE_C2))
    _LABEL_CLIPS = bool(record_video and _ROUTE_C2)  # draw C1/C2 clip labels for the routing video
    _fovy = float(mjm.vis.global_.fovy) if (record_video and mjm is not None) else 45.0

    def _world_to_pixel(p, cam, W=640, H=480):  # project a world pt to image px for a FREE MjvCamera
        azr, elr = np.radians(cam.azimuth), np.radians(cam.elevation)
        fwd = np.array([np.cos(elr) * np.cos(azr), np.cos(elr) * np.sin(azr), np.sin(elr)])  # camera -> lookat
        eye = np.array(cam.lookat, dtype=float) - cam.distance * fwd
        right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
        rn = float(np.linalg.norm(right))
        if rn < 1e-9:
            return None
        right /= rn
        up = np.cross(right, fwd)
        rel = np.array(p, dtype=float) - eye
        zc = float(np.dot(rel, fwd))
        if zc <= 1e-6:
            return None
        f = (H / 2.0) / np.tan(np.radians(_fovy) / 2.0)
        px = W / 2.0 + f * float(np.dot(rel, right)) / zc
        py = H / 2.0 - f * float(np.dot(rel, up)) / zc
        if -25 <= px <= W + 25 and -25 <= py <= H + 25:
            return float(px), float(py)
        return None

    def _cap(phase):
        if _renderer is None:
            return
        import matplotlib.pyplot as plt
        mujoco.mj_forward(mjm, mjd)
        imgs = []
        for _nm, _c in _cams:
            _renderer.update_scene(mjd, camera=_c)
            _im = _renderer.render().astype(np.float32) * 1.3
            imgs.append(np.clip(_im, 0, 255).astype(np.uint8))
        _ncw = len(imgs)
        fig, axes = plt.subplots(1, _ncw, figsize=(15, 4.6) if _ncw <= 3 else (5.0 * _ncw, 4.6))
        for ax, im, (nm, _c2) in zip(axes, imgs, _cams):
            ax.imshow(im)
            ax.axis("off")
            ax.set_title(nm, fontsize=7.5, color="0.3")
            if _LABEL_LR:
                try:
                    _pl_ee, _pr_ee = get_ee_positions(state, scene_info)
                    # label at CLAW level (EE - ~0.24m in Z = the pinch/claw the zoom cameras frame), NOT the EE
                    # body (~0.25m higher -> off the tight zoom frames). X,Y still identify L(-Y) vs R(+Y).
                    _pl = (float(_pl_ee[0]), float(_pl_ee[1]), float(_pl_ee[2]) - 0.24)
                    _pr = (float(_pr_ee[0]), float(_pr_ee[1]), float(_pr_ee[2]) - 0.24)
                    for _pp, _lab, _col in ((_pl, "L", "#19e64b"), (_pr, "R", "#ff2bd6")):
                        _pxy = _world_to_pixel(_pp, _c2)
                        if _pxy is not None:
                            ax.text(_pxy[0], _pxy[1], _lab, color=_col, fontsize=11, fontweight="bold",
                                    ha="center", va="center", clip_on=True,
                                    bbox=dict(boxstyle="round,pad=0.12", fc="black", ec=_col, alpha=0.55))
                except Exception:  # noqa: BLE001
                    pass
            if _LABEL_CLIPS:
                try:
                    for _cp, _clab, _ccol in (((x_clip, y_clip, CLIP1_Z + _clip_float_z + 0.026), "C1", "#27e060"),
                                              ((c2x, c2y, CLIP1_Z + _clip_float_z + 0.026), "C2", "#19c8ee")):
                        _cpxy = _world_to_pixel(_cp, _c2)
                        if _cpxy is not None:
                            ax.text(_cpxy[0], _cpxy[1], _clab, color=_ccol, fontsize=10, fontweight="bold",
                                    ha="center", va="center", clip_on=True,
                                    bbox=dict(boxstyle="round,pad=0.12", fc="black", ec=_ccol, alpha=0.6))
                except Exception:  # noqa: BLE001
                    pass
        _supt = (f"C1->C2 §運用14 ({DEVICE}) — seat C1 (full-clamp) -> L HALF-unclamp -> guide toward C2 — {phase}"
                 if _ROUTE_C2 else
                 f"M-Route §運用14 ({DEVICE}) — centred grasp+lift + DIAGONAL transport "
                 f"GX0.30,Y0 -> clip({x_clip:.2f},{y_clip:+.2f}) + drop-in seat@809 — {phase}")
        fig.suptitle(_supt, fontsize=8.5)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.01, wspace=0.02)
        fig.savefig(os.path.join(_frames_dir, f"f{_fidx[0]:05d}.png"), dpi=98)
        plt.close(fig)
        _fidx[0] += 1

    # seeds + settle
    seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]
    seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:ARM_DOF] = seed_l
    fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    state = model.state()
    for _ in range(10):
        state = physics_step(model, state, solver, contacts, scene_info)

    # PRE-STEP caveat-a: re-centre GRASP_YC on the SETTLED cable Y (the cable bodies within the grasp region),
    # preserving the 88mm span (arms = GRASP_YC +- GHS). Symmetrises the L/R f1ext for the drag.
    # %3 over-void test (Rs (b) routing-port auth, 2026-06-29): re-centre the grasp on S6_ENGAGE_YC (= the
    # void+clip Y) so grasp+void+clip CO-LOCATE at C1-over-void (the banked grasp_y=None strategy-ii config,
    # build:1066). DEFAULT S6_ENGAGE_YC=0 -> _grasp_at=0 -> |Y-0|<0.10 = the array centre = BYTE-IDENTICAL.
    _grasp_at = float(os.environ.get("S6_ENGAGE_YC", "0.0"))
    wp.synchronize()
    _cy_all = state.body_q.numpy()[cable_bodies, 1]
    _near = _cy_all[np.abs(_cy_all - _grasp_at) < 0.10]  # grasp-region cable bodies (|Y - grasp_at|<100mm)
    GRASP_YC = float(np.mean(_near)) if _near.size else _grasp_at
    print(f"  [S6_ROUTE] caveat-a: settled-cable-centre GRASP_YC={GRASP_YC * 1e3:+.2f}mm "
          f"(grasp_at={_grasp_at * 1e3:+.0f}mm arms +-{GHS * 1e3:.0f}mm = 88 span)")

    # W0-e F-1b (Y-phase retreat, spec v0.9 + %12 (A)-injection 2026-07-05): shift the grasp centre GRASP_YC by
    # a common-mode Δy so the WHOLE route forms the buckle at the TARGET phase (== S6_ENGAGE_YC grasp-Y knob class;
    # the C1_SEAT descent target stays FULLY nominal). B1 = phase-periodic (floor_mod(dy,15)->7.5), B2 = absolute
    # one-sided ([10.5,13.5]->10.0). offset-gated (dy!=0) + W0E_F1B flag -> (0,0) BYTE-IDENTICAL (no shift/print).
    # config-derived operand (NO node-state read; bright-line 4). SIM-ONLY: node-lattice artifact (real cable has
    # no node phase) -- excluded from the real playbook. provenance: cuda:0 + build sha (PREREG U).
    _dy_off_mm = float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) * 1e3
    if _dy_off_mm != 0.0 and os.environ.get("W0E_F1B", "1") == "1":
        _dphase = _dy_off_mm % 15.0  # Python floor-mod (B1 operand; -10 -> 5)
        _dygr = None
        _f1b_mode = None
        # W0-e F-1b'' 150mm band re-derivation (mapping B, Rs "進めて" 2026-07-06, two-key agree): ADOPT snap-DOWN only.
        # phi in (0,7.5] -> Delta = -phi (snap grasp dy to the nearest LOWER 15-lattice node). phi>7.5 (snap-UP) NOT
        # adopted -> falls through to the committed B1/B2 bands (== 81-run behavior on phi10 cols, known fail annotated).
        # snap-down REPLACES B1 [2.5,6.5] (its 7.5 target is counterproductive at 150mm, PREREG-confirmed; snap-down's
        # if is FIRST -> precedence). production flag W0E_F1B_SNAPDOWN. offset-gated (dy!=0) -> C-0 (0,0) byte-id UNTOUCHED.
        if os.environ.get("W0E_F1B_SNAPDOWN", "0") == "1" and 0.0 < _dphase <= 7.5:
            _dygr = -_dphase; _f1b_mode = "SNAPDOWN(phi->0)"
        elif 2.5 <= _dphase <= 6.5:          # B1 phase-periodic band -> retreat phase to 7.5 (cross-period correct)
            _dygr = _dphase - 7.5; _f1b_mode = "B1-retreat"
        elif 10.5 <= _dy_off_mm <= 13.5:     # B2 absolute one-sided band (positive dy) -> retreat to dy 10.0
            _dygr = _dy_off_mm - 10.0; _f1b_mode = "B2-retreat"
        if _dygr is not None:
            _dygr = float(np.clip(_dygr, -7.5, 7.5))  # |Delta_y| <= 7.5mm (H2; observed max 5.0)
            GRASP_YC += _dygr * 1e-3
            print(f"  [W0E-F1B] {_f1b_mode}: dy={_dy_off_mm:+.2f}mm phi={_dphase:.2f} Delta={_dygr:+.2f}mm "
                  f"GRASP_YC={GRASP_YC * 1e3:+.2f}mm; SIM-ONLY node-lattice artifact")

    # fix-5 (Rs A / Opt-1, 2026-07-03): X analog of caveat-a -- re-centre x_grasp on the SETTLED cable X,
    # offset-gated (dx != 0 only; scene_info :1668 collapses None/(0,0) -> (0,0) so None / (0,dy) / nominal
    # keep the constant-X banked trajectory = byte-identical BY CONSTRUCTION). Cable || Y -> region X approx
    # const -> mean well-defined. Fixes b2_cpA_reach_screen_finding.md (canonical route had ZERO cable-X
    # follow; the legacy do_p1_grasp grasp_dy is inert on this path).
    if scene_info.get("cable_xy_offset", (0.0, 0.0))[0] != 0.0:
        _cx_near = state.body_q.numpy()[cable_bodies, 0][np.abs(_cy_all - _grasp_at) < 0.10]  # same mask as caveat-a
        if _cx_near.size:
            x_grasp = float(np.mean(_cx_near))
        print(f"  [S6_ROUTE] caveat-a-X: settled-cable-X x_grasp={x_grasp * 1e3:+.2f}mm "
              f"(nominal GRASP_X={GRASP_X * 1e3:+.0f}mm, delta={(x_grasp - GRASP_X) * 1e3:+.2f}mm)")

    def tgt(x, z):
        return (x, GRASP_YC - GHS, z), (x, GRASP_YC + GHS, z)

    def tgt2(x, yc, z):
        # M-Route-2 C1: diagonal target with a MOVING grasp centre yc (interp GRASP_YC -> y_clip); the 88mm span is
        # preserved (yc +- GHS = INVARIANT#2). For y_clip=0 (centred M-Route-1) tgt2(x, GRASP_YC, z) == tgt(x, z).
        return (x, yc - GHS, z), (x, yc + GHS, z)

    def _w0e_guarded_cx(y_ref, x_ref):
        # W0-e common guarded crossing-X selector (spec v0.9 cluster A): mean cable-body X within the Y window
        # |y-y_ref|<=7.5mm AND the X plausibility window |x-x_ref|<=30mm (offline-validated: n=1, 0 tail-hijack
        # on all 81 cells, validate_measurands.py:54-57). Returns (mean_x_m, n_nodes); (None, 0) if the window is
        # empty (plausibility reject). Reads the LIVE `state` by closure (same pattern as _zc1).
        wp.synchronize()
        _P = state.body_q.numpy()[cable_bodies]
        _m = (np.abs(_P[:, 1] - y_ref) <= 0.0075) & (np.abs(_P[:, 0] - x_ref) <= 0.030)
        if not _m.any():
            return None, 0
        return float(_P[_m, 0].mean()), int(_m.sum())

    # --- GRASP + LIFT (reuse the validated M-Grasp-engage-1 orchestration) ---
    _ph("GRASP_HOVER")
    ok = {}
    state, ok["hover"] = ik_move_both(model, state, scene_info, solver, contacts, *tgt(x_grasp, z_high),
                                      label="ROUTE-HOVER", converge_mm=8.0, speed_factor=0.2, warmstart_jq=fk_jq)
    _cap("HOVER")
    _ph("GRASP_DESCEND")
    ok["descend"] = True
    for k in range(1, 9):
        zk = z_high + (z_grasp - z_high) * k / 8
        _dl, _dr = _inject_detour("GRASP_DESCEND", k, 8, *tgt(x_grasp, zk))  # DQ7 (ii): kick-and-recover (None-path passthrough)
        state, okk = ik_move_both(model, state, scene_info, solver, contacts, _dl, _dr,
                                  label=f"ROUTE-DESCEND{k}/8", converge_mm=2.5, speed_factor=0.25)
        ok["descend"] = ok["descend"] and bool(okk)
        _cap(f"DESCEND {k}/8")
    # 2-PHASE cage90 close (validated capture-then-gentle)
    _ph("GRASP_CLOSE")
    CAGE_FRAC = 0.9
    cage_rad = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * CAGE_FRAC
    _set_gripper_target(control, driver_joints, cage_rad)
    for _ in range(30):
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap("CAGE 90%")
    for ck in range(1, 13):
        ctgt = cage_rad + (GRIPPER_DRIVER_CLOSE_RAD - cage_rad) * ck / 12
        _set_gripper_target(control, driver_joints, ctgt)
        for _ in range(12):
            state = physics_step(model, state, solver, contacts, scene_info)
        if ck % 3 == 0:
            _cap(f"CLAMP {ck}/12")
    for _ in range(40):
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap("CLOSED")
    # M-Hook-1: capture the EE->gripped-cable z offset at close (BEFORE the route), the banked
    # r_s71_clip_dropin_72:216-218 convention. NOT re-measured after the route, so the drag-loosening
    # (cable migrates UP in the cage) is NOT compensated -> the drop-in faithfully TESTS %9's integration
    # concern (does the loosened post-route cable still seat at 809, or rest high on the clip top ~834?).
    ee_off = float(get_ee_positions(state, scene_info)[1][2]) - _seg_z_mm(GRASP_YC) / 1e3
    _ph("LIFT")
    ok["lift"] = True
    for k in range(1, LIFT_SUBSTEPS + 1):
        zl = z_grasp + LIFT_M * k / LIFT_SUBSTEPS
        state, okk = ik_move_both(model, state, scene_info, solver, contacts, *tgt(x_grasp, zl),
                                  label=f"ROUTE-LIFT{k}/{LIFT_SUBSTEPS}", converge_mm=3.0, speed_factor=0.3)
        ok["lift"] = ok["lift"] and bool(okk)
        _cap(f"LIFT {k}/{LIFT_SUBSTEPS}")

    # --- CONTINUOUS RETENTION GATE (PART 1 GATE-FIX: %2 two-claw cage log:6738) sampled at EVERY waypoint ---
    f1_L, f1_R, f2_L, f2_R = _arm_split()
    wps = []  # per-waypoint dicts

    def _sample(label, xcur):
        cgL = _cage(f1_L, f2_L)
        cgR = _cage(f1_R, f2_R)
        cz = _cable_z() * 1e3
        okL, okR = cgL["held"], cgR["held"]  # %2 cage: SANDWICHED between both claws AND lateral within footprint
        rec = {"wp": label, "x": round(xcur, 3), "L": cgL, "R": cgR,
               "okL": okL, "okR": okR, "cable_z_mm": round(cz, 1)}
        wps.append(rec)
        print(f"  [S6_ROUTE] wp={label:12s} x={xcur:.3f} "
              f"L[f1/f2={cgL['f1']:+.2f}/{cgL['f2']:+.2f} sum={cgL['sand']:.1f} lat={cgL['lat']:.1f} held={okL}] "
              f"R[f1/f2={cgR['f1']:+.2f}/{cgR['f2']:+.2f} sum={cgR['sand']:.1f} lat={cgR['lat']:.1f} held={okR}] "
              f"cable_z={cz:.0f}mm")
        return rec

    cable_z_start = _cable_z() * 1e3
    _sample("START(lift)", x_grasp)
    # ROUTE: M-Route-2 C1 DIAGONAL drag -- both arms together from (GX, GRASP_YC) to (x_clip, y_clip) at z_lift,
    # interpolating BOTH xk AND the grasp-centre yck while preserving the 88mm span (yck +- GHS). For y_clip=0
    # (centred M-Route-1) yck stays GRASP_YC so this is byte-equivalent to the prior X-only route. INVARIANT#1:
    # both arms move (different MIRRORED joint-motions -- LEFT stretches, RIGHT folds -- neither parked);
    # INVARIANT#2: span fixed at 2*GHS, bases untouched. The y_clip drag is the off-centre TEST (5-CC reach wall).
    _ph("ROUTE_C1")
    ok["route"] = True
    for k in range(1, N_ROUTE + 1):
        xk = x_grasp + (x_clip - x_grasp) * k / N_ROUTE
        yck = GRASP_YC + (y_clip - GRASP_YC) * k / N_ROUTE
        state, okk = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(xk, yck, z_lift),
                                  label=f"ROUTE{k}/{N_ROUTE}", converge_mm=3.0, speed_factor=0.3)
        ok["route"] = ok["route"] and bool(okk)
        _sample(f"ROUTE{k}/{N_ROUTE}", xk)
        _cap(f"ROUTE {k}/{N_ROUTE} (X={xk:.3f} Y={yck:+.3f})")
    # per-arm reach residual at the C1 endpoint: under-cable realization of the MARGINAL 2.21mm aerial probe
    # (log:6750) + the asymmetric-drag WATCH. resid = ||EE - commanded target||; lateral = |EE_y - base_y| (the
    # LEFT arm stretches to ~0.456 = near reach, the RIGHT folds to ~0.156 = the asymmetry). A blown residual =
    # the marginal reach became a WALL under cable -> the route gate (ok["route"]) catches it -> STOP->%9.
    _pl, _pr = get_ee_positions(state, scene_info)
    _tl, _tr = tgt2(x_clip, y_clip, z_lift)
    resid_l_mm = float(np.linalg.norm(np.array(_pl) - np.array(_tl))) * 1e3
    resid_r_mm = float(np.linalg.norm(np.array(_pr) - np.array(_tr))) * 1e3
    lat_l_m = abs(float(_pl[1]) - ROBOT_LEFT_BASE[1])
    lat_r_m = abs(float(_pr[1]) - ROBOT_RIGHT_BASE[1])
    # the STRETCH arm = the larger-lateral (near-reach, fragile) one -- DERIVED from the data, not hardcoded: for a
    # +Y clip (C1) the LEFT stretches; for a -Y clip (C5) the RIGHT stretches (the mirror). The OTHER arm FOLDS.
    stretch_arm = "L" if lat_l_m > lat_r_m else "R"
    print(f"  [S6_ROUTE] endpoint per-arm reach: residual L={resid_l_mm:.2f}mm R={resid_r_mm:.2f}mm | "
          f"lateral L={lat_l_m:.3f}m R={lat_r_m:.3f}m -> {stretch_arm} STRETCHES (near-reach, fragile), the other "
          f"FOLDS -- asymmetric diagonal drag to clip Y={y_clip:+.3f}, both arms moving (INVARIANT#1)")
    # hold at the clip (aerial, pre-hook) + final sample
    for _ in range(60):
        state = physics_step(model, state, solver, contacts, scene_info)
    _sample("END(hold)", x_clip)
    _cap("END (aerial @ clipX, pre-hook=M-Hook-1)")

    # --- ROUTE C1->C2 with HALF-UNCLAMP GUIDE (env-gate S13_ROUTE_C2=1; %3 Rs directive 2026-06-30) -------------
    # FAITHFUL choreography (NOT the S6_HOOK full-release seat -> DO_HOOK forced False above):
    #   (1) both arms clamped at C1 (route end; L=-Y@y_clip-GHS, R=+Y@y_clip+GHS).
    #   (2) SEAT C1 by pushing the cable into the groove WHILE FULLY CLAMPED (lower both to GROOVE_CENTER_Z, NO
    #       release) = "full clamp seat / InsertIntoClip".
    #   (3) L HALF-UNCLAMP (CLOSE->GRIPPER_DRIVER_HALF_OPEN_RAD 0.69, NOT full open); R KEEPS its grasp = the +Y
    #       anchor above C1 (cross-PV flag 1; without it the open-top C1 escapes). L stays ON the cable.
    #   (4) L GUIDE (しごき) toward C2 (X,Y interp at cradle height); cable slides through the L half-clamp. R holds.
    #   (5) at C2: lower L to push the cable into C2's groove. MEASURE slip(slide/drag), C1 retention (frozen seat-z
    #       + cable<->C1), C2 reach (cable<->C2), held/cradle gates, AND SEPARATELY the claw-vs-SOLID-table JAM
    #       (C2 over solid; cross-PV flag 2 = a GEOMETRY jam, distinct from the cable-physics drag).
    if _ROUTE_C2 and _clip_collidable:
        import glob as _glob
        import shutil as _shutil
        import subprocess as _subp
        LOW_WALL_TOP = (CLIP1_Z + _clip_float_z + 0.020) * 1e3   # 820mm(+float): cable-centre escape crit (low-wall top)
        L_drv, R_drv = [6, 10], [20, 24]         # per-arm gripper drivers (test:1344-1345; L=-Y arm, R=+Y arm)
        _clip1g, _clip2g, _tabg = _clip_geoms(), _clip2_geoms(), _table_geoms()
        # CLIP_FLOAT_Z CONSISTENCY READBACK (guard: clip boxes + cable SEAT Z + EE DESCENT target all raise by the SAME
        # h; TABLE_HEIGHT STAYS 0.80). A partial raise = mis-seat = INVALID. GAP = floated cable Z - table 0.80 = the
        # empty space the f1ext bottom claw cages UNDER the cable (the コ rationale; must be EMPTY = no stray geom).
        _cab_seat_target = GROOVE_CENTER_Z + _clip_float_z          # (ii) cable seated Z target
        _ee_descent_target = _cab_seat_target + ee_off              # (iii) gripper EE descent target (= seat + ee_off)
        _c1_floor_z = float(np.min([mjd.geom_xpos[g][2] for g in _clip1g])) if _clip1g else float("nan")  # (i) actual
        _c2_floor_z = float(np.min([mjd.geom_xpos[g][2] for g in _clip2g])) if _clip2g else float("nan")  # clip box z
        _gap_mm = (_cab_seat_target - TABLE_HEIGHT) * 1e3
        print(f"  [C2-FLOAT] CLIP_FLOAT_Z={_clip_float_z * 1e3:.1f}mm (TABLE stays {TABLE_HEIGHT * 1e3:.0f}) | "
              f"(i) clip floor geom zmin C1={_c1_floor_z * 1e3:.1f} C2={_c2_floor_z * 1e3:.1f}mm "
              f"(expect {(CLIP1_Z + _clip_float_z + 0.0025) * 1e3:.1f}) | (ii) cable SEAT target="
              f"{_cab_seat_target * 1e3:.1f}mm (=809+float) | (iii) EE descent target={_ee_descent_target * 1e3:.1f}mm "
              f"(=seat+ee_off {ee_off * 1e3:.1f}) | GAP(cable-table)={_gap_mm:.1f}mm | LOW_WALL_TOP={LOW_WALL_TOP:.0f}mm")
        rc2 = {"clip1_geoms": len(_clip1g), "clip2_geoms": len(_clip2g), "table_geoms": len(_tabg),
               "void_x_ceiling": 0.366, "c2_over_solid": bool(c2x > 0.366 or not (0.090 <= c2y <= 0.210))}
        print(f"  [C2] geoms: C1={len(_clip1g)} C2={len(_clip2g)} table={len(_tabg)} | "
              f"C1@({x_clip:.3f},{y_clip:+.3f})over-void  C2@({c2x:.3f},{c2y:+.3f})over-SOLID "
              f"(X {c2x} vs void-ceil 0.366; Y {c2y:+.3f} vs void [0.090,0.210])")

        # item1 HAND-HAND clearance at ARM-LINK level (Rs core concern). MATCHES the active IK
        # DualArmLinkAvoidObjective (newton_routing_utils:192-193: dist=||pos_l-pos_r||, penetrate if dist<r_l+r_r) so
        # it is the SAME quantity COLLISION_AVOIDANCE=1 minimises. FK-model body_q (fk_state, refreshed by eval_fk in
        # ik_move_both): left link = body[l_local], right = body[FRANKA_NUM_JOINTS+r_local] (= _build_collision_objectives
        # mapping). UNCAPPED Euclidean (no 50mm mj_geomDistance ceiling) + forearm/wrist/EE spheres (NOT pad-only).
        from newton_routing_utils import COLLISION_PAIRS as _HH_PAIRS  # noqa: E402
        from newton_routing_utils import COLLISION_SPHERE_RADII as _HH_RAD  # noqa: E402
        _hh_avoid_on = os.environ.get("COLLISION_AVOIDANCE", "1") != "0"

        def _hh_clear_mm():
            bq = fk_state.body_q.numpy()
            best, bp = 9e9, None
            for _ll, _rl in _HH_PAIRS:
                _pl, _pr = np.asarray(bq[_ll][:3]), np.asarray(bq[FRANKA_NUM_JOINTS + _rl][:3])
                _c = (float(np.linalg.norm(_pl - _pr)) - (_HH_RAD[_ll] + _HH_RAD[_rl])) * 1e3
                if _c < best:
                    best, bp = _c, (_ll, _rl)
            return best, bp

        def _claw_cable_load(claw_set):   # (claw<->cable) NORMAL force + eff mu: low N=cradle, high N=grip
            mujoco.mj_forward(mjm, mjd)
            _cs, _cab = set(claw_set), set(cable_geoms)
            tot, peak, n, mu = 0.0, 0.0, 0, None
            f6 = np.zeros(6)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _cab) or (int(c.geom2) in _cs and int(c.geom1) in _cab):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    fn = abs(float(f6[0])); tot += fn; peak = max(peak, fn); n += 1
                    if mu is None:
                        mu = float(c.friction[0])
            return tot, peak, n, mu

        def _claw_table_load(claw_set):   # (claw<->SOLID-table) NORMAL force = the geometry JAM, NOT a cable drag
            mujoco.mj_forward(mjm, mjd)
            _cs, _tb = set(claw_set), set(_tabg)
            tot, n = 0.0, 0
            f6 = np.zeros(6)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _tb) or (int(c.geom2) in _cs and int(c.geom1) in _tb):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    tot += abs(float(f6[0])); n += 1
            return tot, n

        def _claw_c2_load(claw_set):   # (claw<->C2-clip) NORMAL force = the soft over-penetration reaction (Rs corrected-route metric; harness only logged claw-vs-table before)
            mujoco.mj_forward(mjm, mjd)
            _cs, _c2 = set(claw_set), set(_clip2g)
            tot, n = 0.0, 0
            f6 = np.zeros(6)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _c2) or (int(c.geom2) in _cs and int(c.geom1) in _c2):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    tot += abs(float(f6[0])); n += 1
            return tot, n

        def _f1_zmin_mm(claw_set):        # bottom-claw lowest z [mm] = can it reach UNDER the cable over solid?
            mujoco.mj_forward(mjm, mjd)
            return (float(np.min([mjd.geom_xpos[g][2] for g in claw_set])) * 1e3) if claw_set else 9e9

        # (2) FULL-CLAMP SEAT: lower both arms (still CLOSED) so the gripped cable centre -> GROOVE_CENTER_Z+float.
        _ph("C1_SEAT")
        seat_ee_z = GROOVE_CENTER_Z + _clip_float_z + ee_off   # CLIP_FLOAT_Z: descend to the FLOATED groove (consistency)
        # W0-e F-1a (C1-seat X-follow, spec v0.9; offset-gated + W0E_F1A). Measure guarded crossing dx at ROUTE_C1
        # end (settled, pre-seat; no physics_step since the aerial hold) -> common-mode compensate the C1_SEAT
        # descent x via tgt2's shared x arg (scalar clamp BEFORE fan-out). k=4 residual re-measure (30-step settle)
        # uses the (ii) MINUS/nominal form comp<-clamp(comp-(crossing-x_clip),+-22) (%12 2026-07-05; nominal-ref
        # self-cancels). plausibility: initial reject -> comp 0 (no-comp, monotone-safe) / k=4 reject -> comp
        # MAINTAINED + loud (mid-descent comp drop = +-16-22mm arm jump = non-monotone). (0,0) BYTE-IDENTICAL
        # (comp=0.0 -> x_clip+0.0==x_clip, prints gated). CLAMP22 provenance: cuda:0 + build sha (PREREG U).
        _f1a_on = (float(scene_info.get("cable_xy_offset", (0.0, 0.0))[0]) != 0.0
                   or float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) != 0.0) and os.environ.get("W0E_F1A", "1") == "1"
        # W0-e F-1a v2 (%12 §運用10 v2, clearance-lift): the g=0.5-only smoke showed the cable RIDES the wall-top
        # during a low-height X-shift -> LIFT clear of the wall, shift + settled re-measure at height (contact-free =
        # unbiased), then descend VERTICALLY. coeff c-i (%12): comp = -(1-lam)*bow, lam=0.5 (retention 0.552/0.506).
        # W0E_F1A_V2=0 falls back to the flat comp-descent (study). offset-gated + W0E_F1A -> (0,0) BYTE-IDENTICAL
        # (else-branch, comp=0.0 -> tgt2(x_clip,..)). prints gated. provenance: cuda:0 + build sha (PREREG U).
        _f1a_comp = 0.0
        _lam = float(os.environ.get("W0E_F1A_LAMBDA", "0.5"))
        _f1a_v2 = _f1a_on and os.environ.get("W0E_F1A_V2", "1") == "1"
        _dx0 = None
        if _f1a_on:
            _cx0, _n0 = _w0e_guarded_cx(y_clip, x_clip)
            if _cx0 is None or abs(_cx0 - x_clip) > 0.030:
                print(f"  [W0E-F1A] initial guarded measure REJECT (n={_n0}) -> comp=0 + no lift (nominal fallback)")
                _f1a_v2 = False
            else:
                _dx0 = _cx0 - x_clip
                _f1a_comp = float(np.clip(-(1.0 - _lam) * _dx0, -0.022, 0.022))  # comp1 (also the flat comp if V2 off)
                _cby0 = state.body_q.numpy()[cable_bodies, 1]
                _nny = float(_cby0[int(np.argmin(np.abs(_cby0 - y_clip)))] - y_clip) * 1e3
                print(f"  [W0E-F1A] guarded dx={_dx0 * 1e3:+.2f}mm (n={_n0}) lam={_lam} -> comp1={_f1a_comp * 1e3:+.2f}mm; "
                      f"pre-seat nearest-node Dy={_nny:+.2f}mm")
        ok["c2_seat_descend"] = True
        if _f1a_v2 and _dx0 is not None:
            _pl0, _ = get_ee_positions(state, scene_info)
            _z0 = float(_pl0[2])
            _zhi = _z0 + 0.015
            for kk in range(1, 3):  # (2) clearance lift +15mm at x_clip (2 leg) -> cable clears the wall-top
                _lz = _z0 + (_zhi - _z0) * kk / 2
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(x_clip, y_clip, _lz),
                                        label=f"C1v2-LIFT{kk}/2", converge_mm=2.5, speed_factor=0.22)
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _plL, _ = get_ee_positions(state, scene_info)  # (log 3) lift-pose IK residual
            _lresid = float(np.linalg.norm(np.array(_plL) - np.array((x_clip, y_clip - GHS, _zhi)))) * 1e3
            print(f"  [W0E-F1A-v2] clearance lift +15mm -> EE z={float(_plL[2]) * 1e3:.1f}mm, lift IK resid={_lresid:.2f}mm")
            for kk in range(1, 4):  # (3) high X-shift to x_clip+comp1 at height (3 leg)
                _xk = x_clip + _f1a_comp * kk / 3
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(_xk, y_clip, _zhi),
                                        label=f"C1v2-SHIFT{kk}/3", converge_mm=2.5, speed_factor=0.22)
            for _ in range(30):  # (4) settle -> clean contact-free re-measure at height
                state = physics_step(model, state, solver, contacts, scene_info)
            _arm_x = x_clip + _f1a_comp
            _cxh, _nh = _w0e_guarded_cx(y_clip, _arm_x)
            _b1 = None
            if _cxh is None or abs(_cxh - _arm_x) > 0.030:
                print(f"  [W0E-F1A-v2] high re-measure REJECT (n={_nh}) -> comp1 MAINTAINED {_f1a_comp * 1e3:+.2f}mm + FLAG")
            else:
                _b1 = _cxh - _arm_x  # (c-i) arm-relative bow at height (contact-free)
                _comp_final = float(np.clip(-(1.0 - _lam) * _b1, -0.022, 0.022))
                print(f"  [W0E-F1A-v2] high b1={_b1 * 1e3:+.2f}mm (crossing_h={_cxh:.4f} arm={_arm_x:.4f}) -> "
                      f"comp_final={_comp_final * 1e3:+.2f}mm")
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(x_clip + _comp_final, y_clip, _zhi),
                                        label="C1v2-TRIM", converge_mm=2.5, speed_factor=0.22)  # (5) 1-leg trim
                _f1a_comp = _comp_final
            for k in range(1, 9):  # (6) vertical descent 8 leg (X fixed, no mid-descent re-measure)
                zk = _zhi + (seat_ee_z - _zhi) * k / 8
                # deep-seat discriminator (%12 2026-07-05, offset-gated flag): SLOW the last 3 leg to test whether the
                # -1.6mm pin-frozen deep-seat is descent-dynamics (z->829 given settle time) or static equilibrium
                # (stays). ik_move_both:1960 n_steps=max(int(dist*100*STEPS_PER_CM*sf),50): STEPS_PER_CM=50 + leg
                # dist~5mm -> sf MUST be >1 to clear the 50-step floor (sf<1 = no-op = the INVALID byte-identical
                # smoke bgm2). %12: sf=8 -> ~208 steps (4.16x) = a real settle window (MAX_MOVE_STEPS=3000 headroom).
                # validity gate (else re-INVALID): :1971 print shows steps>50 on these legs + slowseat npz sha != fast f2 cell.
                _sf = 8.0 if (k >= 6 and os.environ.get("W0E_F1A_SLOWSEAT", "0") == "1") else 0.25
                state, okk = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(x_clip + _f1a_comp, y_clip, zk),
                                          label=f"C2-SEAT{k}/8", converge_mm=2.5, speed_factor=_sf)
                ok["c2_seat_descend"] = ok["c2_seat_descend"] and bool(okk)
                wp.synchronize()  # (log 1) during-descent crossing z-x trace (wall-contact-free mouth entry)
                _Pz = state.body_q.numpy()[cable_bodies]
                _mz = np.abs(_Pz[:, 1] - y_clip) <= 0.0075
                if _mz.any():
                    _iz = np.where(_mz)[0]
                    _ci = int(_iz[np.argmin(np.abs(_Pz[_iz, 0] - (x_clip + _f1a_comp)))])
                    print(f"  [W0E-F1A-v2] descend k={k}/8 crossing x={_Pz[_ci, 0]:.4f} z={_Pz[_ci, 2] * 1e3:.1f}mm")
                if k % 2 == 0:
                    _cap(f"C1 v2-seat {k}/8")
            for _ in range(30):  # (log 2) per-cell retention: b_final/b1
                state = physics_step(model, state, solver, contacts, scene_info)
            _cxf, _ = _w0e_guarded_cx(y_clip, x_clip + _f1a_comp)
            if _cxf is not None and _b1 is not None and abs(_b1) > 1e-6:
                _bfin = _cxf - (x_clip + _f1a_comp)
                print(f"  [W0E-F1A-v2] retention b_final/b1 = {(_bfin / _b1):.3f} (b_final={_bfin * 1e3:+.2f}mm, "
                      f"b1={_b1 * 1e3:+.2f}mm); crossing_final={_cxf:.4f}")
        else:
            for k in range(1, 9):  # v1 flat descent (V2 off / reject fallback; nominal comp=0.0 -> nominal path, NEW baseline post-LIFT_M raise)
                zk = z_lift + (seat_ee_z - z_lift) * k / 8   # z_lift raised (W0E_LIFT_M 0.08) -> descent STARTS above the clip -> vertical entry
                state, okk = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(x_clip + _f1a_comp, y_clip, zk),
                                          label=f"C2-SEAT{k}/8", converge_mm=2.5, speed_factor=0.25)
                ok["c2_seat_descend"] = ok["c2_seat_descend"] and bool(okk)
                if _f1a_on:   # (log 1) offset C1_SEAT z-x crossing trace (%12 2026-07-05: prove wall-contact-free VERTICAL entry from the raised clearance z; logging-only, offset-gated)
                    wp.synchronize()
                    _Pv1 = state.body_q.numpy()[cable_bodies]
                    _mv1 = np.abs(_Pv1[:, 1] - y_clip) <= 0.0075
                    if _mv1.any():
                        _iv1 = np.where(_mv1)[0]
                        _cv1 = int(_iv1[np.argmin(np.abs(_Pv1[_iv1, 0] - (x_clip + _f1a_comp)))])
                        print(f"  [W0E-F1A-v1] descend k={k}/8 crossing x={_Pv1[_cv1, 0]:.4f} z={_Pv1[_cv1, 2] * 1e3:.1f}mm")
                if k % 2 == 0:
                    _cap(f"C1 full-clamp seat {k}/8")
        for _ in range(60):
            state = physics_step(model, state, solver, contacts, scene_info)
        wp.synchronize()
        _cb_y = state.body_q.numpy()[cable_bodies, 1]
        _seat_k = int(np.argmin(np.abs(_cb_y - y_clip)))
        seat_body = int(cable_bodies[_seat_k])

        def _zc1():
            wp.synchronize()
            return float(state.body_q.numpy()[seat_body, 2]) * 1e3   # mm: FROZEN C1 seat body, the SSOT retention z

        f1L0, f1R0, f2L0, f2R0 = _arm_split()   # FREEZE the claw partition at the symmetric seat pose
        z_c1_seated = _zc1()
        c1_seat_dist = _min_dist_mm(cable_geoms, _clip1g)
        c2_dist_atseat = _min_dist_mm(cable_geoms, _clip2g)
        print(f"  [C2] C1 FULL-CLAMP seat: seat_body=idx{seat_body}(Y{_cb_y[_seat_k]:+.3f}) z_seat={z_c1_seated:.1f}mm "
              f"(groove 809 / low-wall {LOW_WALL_TOP:.0f}) cable<->C1={c1_seat_dist:+.3f}mm "
              f"cable<->C2={c2_dist_atseat:+.3f}mm (<=0=touching)")
        _cap("C1 SEATED (full-clamp, pre half-unclamp)")

        _ph("C1_PIN")
        # PERCLIP_PIN (b)-pin ACTIVATION on the VERIFIED C1 seat (%3 charter 2026-07-01) -- the headline freeze-scope
        # probe. Toggle the pre-allocated per-clip connect eq (seat_body <-> world@seat) ACTIVE now (mid-episode
        # eq_active; pre-seat activation forbidden per restore-gate log:6814 C2 -> gated on the verified seat above).
        # PER-CLIP: ONLY seat_body is anchored; body29/28.. stay articulated (measured over the guide below). The
        # anchor is set to the seat body's CURRENT world pos (~clip groove 809) so activation does NOT yank it.
        _perclip_on = os.environ.get("PERCLIP_PIN", "0") == "1"
        _fs_on = _perclip_on or os.environ.get("FREEZE_SCOPE", "0") == "1"
        _pin_eqid, _z_c1_after_pin = None, None
        # W0-e producer field (%9 pin-excluded floor bar / %12 pin-frame-onward, 2026-07-05): _seat_geom_mj = the
        # mujoco cable geom co-located with the pinned seat body -> EXCLUDED from the POST-pin cable<->C1 min-dist
        # (the free-neighbor "床" bar; pre-pin uses ALL geoms so the un-pinned body's penetration is NOT masked).
        # _c1_np_min/_c2_pen_min = per-clip episode-min penetration (mm, <0=penetration) = the planned producer field.
        _seat_geom_mj, _c1_np_min, _c2_pen_min = None, 9e9, 9e9
        if _perclip_on:
            assert scene_info.get("perclip_pin_n", 0) > 0, "PERCLIP_PIN=1 but build_scene pre-allocated no eqs"
            wp.synchronize()
            mujoco.mj_forward(mjm, mjd)   # refresh mjd.xpos so the seat-body position-match is current
            _seat_world = state.body_q.numpy()[seat_body, :3].astype(float).copy()
            # W0-e: the mujoco cable geom co-located with the pinned seat body (world-pos match, no Newton<->mjc index
            # assumption -- same primitive as the eq match below) -> excluded from the POST-pin free-neighbor floor bar.
            _seat_geom_mj = (min(cable_geoms, key=lambda g: float(np.linalg.norm(np.asarray(mjd.geom_xpos[g]) - _seat_world)))
                             if cable_geoms else None)
            # Activate the pre-allocated DISABLED connect-to-world eq whose body1 IS the runtime seat body, found by
            # WORLD-POSITION match (no Newton<->mjc index assumptions): mjd.xpos[eq_obj1id] == the seat body's pos.
            _best, _bestd = None, 9e9
            for i in range(int(mjm.neq)):
                if (int(mjm.eq_type[i]) == int(mujoco.mjtEq.mjEQ_CONNECT)
                        and int(mjm.eq_obj2id[i]) == 0 and int(mjm.eq_active0[i]) == 0):
                    _d = float(np.linalg.norm(np.asarray(mjd.xpos[int(mjm.eq_obj1id[i])]) - _seat_world))
                    if _d < _bestd:
                        _bestd, _best = _d, i
            assert _best is not None and _bestd < 5e-3, (
                f"PERCLIP_PIN: no disabled connect eq matches the runtime seat body (best dist {_bestd * 1e3:.2f}mm)")
            _pin_eqid = _best
            mjm.eq_data[_pin_eqid, 0:3] = [0.0, 0.0, 0.0]     # anchor in seat-body frame = its origin
            mjm.eq_data[_pin_eqid, 3:6] = _seat_world         # anchor in world frame = current seat pos (~clip groove)
            mjd.eq_active[_pin_eqid] = 1
            if _demo_rec is not None:  # P3 recorder: eq-pin AFTER activation (spec §2.5)
                _demo_rec.note_pin(_pin_eqid, seat_body)
            for _ in range(40):
                state = physics_step(model, state, solver, contacts, scene_info)
            _z_c1_after_pin = _zc1()
            print(f"  [PERCLIP_PIN] ACTIVATED eq#{_pin_eqid} on the EXACT runtime seat body idx{seat_body} "
                  f"(position-match {_bestd * 1e3:.3f}mm) @world{[round(v, 4) for v in _seat_world]}; "
                  f"z_c1 {z_c1_seated:.1f}->{_z_c1_after_pin:.1f}mm; eq_active={int(mjd.eq_active[_pin_eqid])} "
                  f"(does the pin hold the seat? body29/28.. freedom measured over the guide below)")
            _cap(f"PERCLIP_PIN ON seat idx{seat_body}: z_c1={_z_c1_after_pin:.1f}mm")

        _ph("L_HALF_UNCLAMP")
        # (3) L HALF-UNCLAMP: ramp L CLOSE->HALF (R stays CLOSED = the +Y anchor). MEASURE is_cradle through the
        # loosening -> the cable must NOT fall out of the L claw (else the guide starts from a dropped cable=artifact).
        HALF = GRIPPER_DRIVER_HALF_OPEN_RAD   # 0.69
        _trans = []
        _q = GRIPPER_DRIVER_CLOSE_RAD
        while _q >= HALF - 1e-6:
            _set_gripper_target(control, L_drv, _q)
            for _ in range(14):
                state = physics_step(model, state, solver, contacts, scene_info)
            _N, _, _, _ = _claw_cable_load(f1L0 + f2L0)
            _gap = _min_dist_mm(f1L0 + f2L0, cable_geoms)
            _cr = bool(-2.0 <= _gap <= 2.5 and 0.1 < _N < 60.0)
            _trans.append({"drv": round(_q, 4), "claw_cable_gap_mm": round(_gap, 3), "normal_N": round(_N, 2),
                           "is_cradle": _cr, "z_c1_mm": round(_zc1(), 1)})
            print(f"  [C2-HALF] L drv={_q:.4f} claw<->cable gap={_gap:+.3f}mm NORMAL={_N:.2f}N is_cradle={_cr} "
                  f"z_c1={_zc1():.1f}mm")
            _q -= 0.0125
        _set_gripper_target(control, L_drv, HALF)
        for _ in range(40):
            state = physics_step(model, state, solver, contacts, scene_info)
        _LhalfN, _, _, _Lmu = _claw_cable_load(f1L0 + f2L0)
        _Lhalfgap = _min_dist_mm(f1L0 + f2L0, cable_geoms)
        L_is_cradle = bool(-2.0 <= _Lhalfgap <= 2.5 and 0.1 < _LhalfN < 60.0)
        print(f"  [C2] AFTER half-unclamp (L drv={HALF}): claw<->cable gap={_Lhalfgap:+.3f}mm NORMAL={_LhalfN:.2f}N "
              f"eff_mu={_Lmu} is_cradle={L_is_cradle} z_c1={_zc1():.1f}mm (cable still held in L half-clamp?)")
        _cap(f"L HALF-unclamp (drv={HALF}): is_cradle={L_is_cradle}")
        # 43-step step 8: R FULL-UNCLAMP (R->open) once C1 is seated -- human-Rs 2026-07-01 「Rはケーブルがクリップに
        # 固定されたらアンクランプし上昇」 + full_43step.json step8 (R_finger 0.002->0.04). The OLD route kept R CLOSED
        # as a +Y anchor = a DEVIATION from the 43-step. ⭐ CRITICAL DE-RISK: the 43-step releases R here ASSUMING C1
        # stays seated by the clip; the open-top clip has zero up-retention -> if C1 ESCAPES when R lets go, the full
        # 43-step is BLOCKED on clip-retention (Rs design call). Measure z_c1 before vs after R-release. Gated SEAT_TOPDOWN.
        _ph("R_UNCLAMP_RISE")
        _route43_mode = os.environ.get("SEAT_TOPDOWN", "0") == "1"
        if _route43_mode:
            _zc1_preR = _zc1()
            _set_gripper_target(control, R_drv, GRIPPER_DRIVER_OPEN_RAD)   # R unclamp (43-step step8)
            for _ in range(40):
                state = physics_step(model, state, solver, contacts, scene_info)
            _zc1_postR = _zc1()
            _c1_held_noR = bool(_zc1_postR < LOW_WALL_TOP)   # C1 stayed below the low-wall escape crit after R let go?
            print(f"  [C2-43-RUNCLAMP] R released (step8): z_c1 {_zc1_preR:.1f}->{_zc1_postR:.1f}mm "
                  f"(low-wall {LOW_WALL_TOP:.0f}); C1_held_without_R={_c1_held_noR} "
                  f"(⭐ if False = open-top clip does NOT retain C1 w/o R = 43-step BLOCKED on clip-retention)")
            _cap(f"R unclamp (43-step step8): C1_held_without_R={_c1_held_noR} z_c1={_zc1_postR:.1f}")
            if os.environ.get("C2_DUALSEAT", "0") == "1":   # Rs corrected-route 2026-07-01: R RISES after unclamp (pin holds C1 -> R free); rejoins ABOVE C2 at the dual-finger seat
                _plRr, _prRr = get_ee_positions(state, scene_info)
                _Lhold_r = (float(_plRr[0]), float(_plRr[1]), float(_plRr[2]))   # L holds its C1-seat pose (cable in half-clamp)
                _Rz0, _Rz1 = float(_prRr[2]), float(_prRr[2]) + 0.045
                for kk in range(1, 9):
                    _rz = _Rz0 + (_Rz1 - _Rz0) * kk / 8
                    state, _ = ik_move_both(model, state, scene_info, solver, contacts, _Lhold_r,
                                            (float(_prRr[0]), float(_prRr[1]), _rz),
                                            label=f"C2-RRISE{kk}/8", converge_mm=2.5, speed_factor=0.22)
                    for _ in range(10):
                        state = physics_step(model, state, solver, contacts, scene_info)
                print(f"  [C2-RRISE] R risen {_Rz0:.3f}->{_Rz1:.3f} (+45mm; R free after pin holds C1, no longer anchors descended)")
                _cap("R rise +45mm (corrected-route)")

        _ph("GUIDE_C2")
        # (4) GUIDE (しごき) L toward C2; R HOLDS at +Y (anchor above C1). cable slides through the L half-clamp.
        _pl0, _pr0 = get_ee_positions(state, scene_info)
        R_hold = (float(_pr0[0]), float(_pr0[1]), float(_pr0[2]))   # R frozen at its achieved +Y anchor pose
        L_x0, L_y0, L_z0 = float(_pl0[0]), float(_pl0[1]), float(_pl0[2])
        print(f"  [C2] R ANCHOR held @({R_hold[0]:.3f},{R_hold[1]:+.3f},{R_hold[2]:.3f}) [+Y above C1 {y_clip:+.3f}]; "
              f"L guide ({L_x0:.3f},{L_y0:+.3f},{L_z0:.3f}) -> C2 ({c2x:.3f},{c2y:+.3f}), z held at cradle level")
        wp.synchronize()
        _gk = int(np.argmin(np.abs(state.body_q.numpy()[cable_bodies, 1] - L_y0)))
        guide_body = int(cable_bodies[_gk])
        gb_xy0 = state.body_q.numpy()[guide_body, :2].copy()
        ee_xy0 = np.array([L_x0, L_y0])
        N_GUIDE = 8
        guide_legs, cradle_break_x, jam_onset_x = [], None, None
        # FREEZE-SCOPE (%3 charter headline): snapshot every cable body's world pos at the guide START, vs the guide
        # END below -> per-body displacement. Pinned seat_body should ~freeze; body29/28.. should still move = (b)
        # viable (rest routes); ALL freeze = (a) degenerate; seat_body moves = pin not holding (or the no-pin control).
        if _fs_on:
            wp.synchronize()
            _fs_p0 = state.body_q.numpy()[cable_bodies, :3].astype(float).copy()
        # 43-step LIFT + HIGH TRAVERSE (gated SEAT_TOPDOWN; human-Rs 2026-07-01 + full_43step.json steps 10-11):
        # the C1->C2 transition LIFTS after the C1 seat (step 10: EE +45mm, 1.025->1.07) THEN traverses to ABOVE C2
        # at the lifted height (step 11: z=1.07, 上空移動) so the gripper CLEARS the C2 clip during the しごき
        # traverse. The OLD guide traversed at the cradle/insert height (L_z0) -> the finger drove INTO the C2 clip
        # (Rs video: 「クリップ下降点からそのまま横にスライド...フィンガがC2に衝突」). +45mm clears the floated wall
        # top 0.850 (bottom claw ~0.864 > 0.850 = 14mm margin). DEFAULT off (gate w/ the seat fix) -> byte-identical
        # low slide. Lead-implemented per the banked 43-step SSOT (authority layer; Rs directed 「43step表を確認」).
        # W0-e F-2 (GUIDE cable-line follow, spec v0.9 + %12 4-Q 2026-07-05): the L guide (しごき) follows the
        # cable's ACTUAL X at the look-ahead Y so the cable stays in the throat (RC-2 fix). Q1 = PLUS (lx tracks
        # cable), Q3 = rate-limited (a) c(k)=c(k-1)+clamp(dev-c(k-1),±8) then clamp(±cap), Q4 = update ONLY while
        # cradled (seed L_is_cradle) + FREEZE c on cradle loss (no 0-reset = jerk-safe). offset-gated + W0E_F2 ->
        # (0,0) BYTE-IDENTICAL (c=0). cap = W0E_F2_CAP_MM = 7mm (%12-confirmed conservative: pad X-half 11 - cable
        # r 4; geom-uncertainty logged, RUN-2 revisits via XML throat if guide authority is short). measures LIVE cable.
        _f2_on = (float(scene_info.get("cable_xy_offset", (0.0, 0.0))[0]) != 0.0
                  or float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) != 0.0) and os.environ.get("W0E_F2", "1") == "1"
        _f2_cap = float(os.environ.get("W0E_F2_CAP_MM", "7.0")) * 1e-3
        _f2_c = 0.0
        _f2_prev_cradle = bool(L_is_cradle)
        _f2_frozen = False
        _ph("GUIDE_PRELIFT")  # P3 label: step-10 lift as its own phase (future re-records; CC2-C1)
        _route43 = os.environ.get("SEAT_TOPDOWN", "0") == "1"
        _trav_z = (L_z0 + 0.045) if _route43 else L_z0   # 43-step lift delta (insert 1.025 -> traverse 1.07)
        if _route43:
            _npre = 8
            for kk in range(1, _npre + 1):
                _lz = L_z0 + (_trav_z - L_z0) * kk / _npre
                if _f2_on and _f2_prev_cradle and not _f2_frozen:  # F-2 follow during the lift (measure at L_y0)
                    _cxg, _ng = _w0e_guarded_cx(L_y0, L_x0)
                    if _cxg is not None and abs(_cxg - L_x0) <= 0.030:
                        _f2_c = _f2_c + float(np.clip((_cxg - L_x0) - _f2_c, -0.008, 0.008))
                        _f2_c = float(np.clip(_f2_c, -_f2_cap, _f2_cap))
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, (L_x0 + _f2_c, L_y0, _lz), R_hold,
                                        label=f"C2-PRELIFT{kk}/{_npre}", converge_mm=2.5, speed_factor=0.22)
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            print(f"  [C2-PRELIFT] L lifted {L_z0:.3f}->{_trav_z:.3f} (43-step step10 +45mm) before the high しごき traverse")
        for k in range(1, N_GUIDE + 1):
            lx = L_x0 + (c2x - L_x0) * k / N_GUIDE
            ly = L_y0 + (c2y - L_y0) * k / N_GUIDE
            if _f2_on and _f2_prev_cradle and not _f2_frozen:  # F-2: follow the cable X at the look-ahead Y (ly)
                _cxg, _ng = _w0e_guarded_cx(ly, lx)
                if _cxg is not None and abs(_cxg - lx) <= 0.030:
                    _dev = _cxg - lx  # Q1 PLUS: deviation of the cable from the nominal straight line
                    _f2_c = _f2_c + float(np.clip(_dev - _f2_c, -0.008, 0.008))  # Q3 (a) rate-limited follow
                    _f2_c = float(np.clip(_f2_c, -_f2_cap, _f2_cap))  # Q2 cap (throat half - cable r)
                    print(f"  [W0E-F2] guide{k} Y={ly:+.3f} dev={_dev * 1e3:+.2f}mm -> c={_f2_c * 1e3:+.2f}mm (cap{_f2_cap * 1e3:.0f})")
            lx = lx + _f2_c  # Q1 apply (a frozen c still applies)
            state, _ = ik_move_both(model, state, scene_info, solver, contacts, (lx, ly, _trav_z), R_hold,
                                    label=f"C2-GUIDE{k}/{N_GUIDE}", converge_mm=3.0, speed_factor=0.25)
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _plk, _ = get_ee_positions(state, scene_info)
            ee_xy = np.array([float(_plk[0]), float(_plk[1])])
            wp.synchronize()
            gb_xy = state.body_q.numpy()[guide_body, :2]
            ee_disp = float(np.linalg.norm(ee_xy - ee_xy0))
            cab_disp = float(np.linalg.norm(gb_xy - gb_xy0))
            slip_xy = (cab_disp / ee_disp) if ee_disp > 1e-6 else 0.0
            ee_dy, cab_dy = float(ee_xy0[1] - ee_xy[1]), float(gb_xy0[1] - gb_xy[1])
            slip_y = (cab_dy / ee_dy) if abs(ee_dy) > 1e-6 else 0.0
            _N, _pk, _n, _mu = _claw_cable_load(f1L0 + f2L0)
            _gap = _min_dist_mm(f1L0 + f2L0, cable_geoms)
            is_cradle = bool(-2.0 <= _gap <= 2.5 and 0.1 < _N < 60.0)
            if _f2_on and not _f2_frozen and not is_cradle:  # Q4: cradle lost -> FREEZE c at last value, stop updates
                _f2_frozen = True
                print(f"  [W0E-F2] cradle lost @guide{k} -> c FROZEN {_f2_c * 1e3:+.2f}mm (no re-capture, no 0-reset)")
            _f2_prev_cradle = is_cradle
            tabN, _tabn = _claw_table_load(f1L0)      # BOTTOM claw vs SOLID table = the geometry JAM
            tab_d = _min_dist_mm(f1L0, _tabg)
            f1z = _f1_zmin_mm(f1L0)
            zc1, c1d, c2d = _zc1(), _min_dist_mm(cable_geoms, _clip1g), _min_dist_mm(cable_geoms, _clip2g)
            _c1np = (_min_dist_mm([g for g in cable_geoms if g != _seat_geom_mj], _clip1g)  # %9 pin-excluded free-neighbor 床 bar (post-pin)
                     if _seat_geom_mj is not None else c1d)
            _c1_np_min = min(_c1_np_min, _c1np); _c2_pen_min = min(_c2_pen_min, c2d)  # W0-e per-clip episode-min penetration (producer)
            lgrip_c2 = _min_dist_mm(f1L0 + f2L0, _clip2g)   # FLAG-D: L-gripper claws <-> C2 clip (penetration PV; <0=overlap)
            lr_sep, _lr_pair = _hh_clear_mm()  # item1 HAND-HAND at ARM-LINK level (sphere model, matches IK avoid; uncapped)
            rpad_c1 = _min_dist_mm(f1R0 + f2R0, _clip1g)     # item4 FINGER-CLIP: R-anchor pad <-> C1 clip (<0=penetration)
            ret_low = bool(zc1 < LOW_WALL_TOP)
            jam = bool(tab_d <= 0.2 or tabN > 0.5)
            if (not is_cradle) and cradle_break_x is None:
                cradle_break_x = round(lx, 4)
            if jam and jam_onset_x is None:
                jam_onset_x = round(lx, 4)
            smode = ("SLIDE" if slip_xy < 0.35 else ("DRAG" if slip_xy > 0.65 else "PARTIAL"))
            guide_legs.append({"k": k, "L_ee_x": round(lx, 4), "L_ee_y": round(ly, 4),
                               "ee_disp_mm": round(ee_disp * 1e3, 2), "cable_disp_mm": round(cab_disp * 1e3, 2),
                               "slip_xy": round(slip_xy, 3), "slip_y": round(slip_y, 3), "slide_mode": smode,
                               "is_cradle": is_cradle, "claw_cable_gap_mm": round(_gap, 3), "claw_cable_N": round(_N, 2),
                               "bottom_claw_table_dist_mm": round(tab_d, 3), "bottom_claw_table_N": round(tabN, 2),
                               "bottom_claw_zmin_mm": round(f1z, 1), "JAM": jam, "z_c1_mm": round(zc1, 1),
                               "c1_retained_lowwall": ret_low, "cable_c1_dist_mm": round(c1d, 3),
                               "cable_c2_dist_mm": round(c2d, 3), "lgrip_c2_dist_mm": round(lgrip_c2, 3),
                               "lr_gripper_sep_mm": round(lr_sep, 3), "rpad_c1_dist_mm": round(rpad_c1, 3)})
            print(f"  [C2-GUIDE] k={k}/{N_GUIDE} Lx={lx:.3f} Ly={ly:+.3f} | slip_xy={slip_xy:.3f}({smode}) "
                  f"slip_y={slip_y:+.3f} cradle={is_cradle}(gap{_gap:+.2f}/N{_N:.1f}) | bottomclaw<->table={tab_d:+.2f}mm "
                  f"N={tabN:.1f} zmin={f1z:.1f} JAM={jam} | C1 z={zc1:.1f}({'IN' if ret_low else 'OUT'}) "
                  f"cable<->C1={c1d:+.2f} cable<->C2={c2d:+.2f} | Lgrip<->C2={lgrip_c2:+.2f} "
                  f"Rpad<->C1={rpad_c1:+.2f} | HH-armlink={lr_sep:+.2f}mm{_lr_pair} (sphere, <0=overlap)")
            _cap(f"GUIDE {k}/{N_GUIDE} Lx={lx:.3f}: slip={slip_xy:.2f}({smode}) cradle={is_cradle} JAM={jam} "
                 f"C1{'IN' if ret_low else 'OUT'}")

        # FREEZE-SCOPE compute (%3 charter headline) -- the (a)/(b) discriminator + C1-retention + route-reach summary.
        if _fs_on:
            wp.synchronize()
            _fs_p1 = state.body_q.numpy()[cable_bodies, :3].astype(float).copy()
            _fs_disp = (np.linalg.norm(_fs_p1 - _fs_p0, axis=1) * 1e3).astype(float)   # mm per cable body over guide
            _seat_arr = np.asarray(cable_bodies)
            _seat_kk = (int(np.where(_seat_arr == seat_body)[0][0]) if seat_body in _seat_arr
                        else int(np.argmin(np.abs(state.body_q.numpy()[cable_bodies, 1] - y_clip))))
            _MOVE_THR = 2.0
            _n_moved = int(np.sum(_fs_disp > _MOVE_THR))
            _seat_disp = float(_fs_disp[_seat_kk])
            _nbr_k = [k for k in (_seat_kk - 2, _seat_kk - 1, _seat_kk + 1, _seat_kk + 2) if 0 <= k < len(_fs_disp)]
            _nbr_disp = [round(float(_fs_disp[k]), 2) for k in _nbr_k]
            _max_disp = float(np.max(_fs_disp))
            if not _perclip_on:
                _scope = "CONTROL_NO_PIN(seat free)"
            elif _seat_disp >= _MOVE_THR:
                _scope = "SEAT_MOVED(pin-not-holding)"
            elif _n_moved == 0:
                _scope = "ALL_FROZEN(a-degenerate)"
            elif _n_moved >= 3:
                _scope = "SEAT_ONLY_FROZEN(b-viable)"
            else:
                _scope = "PARTIAL"
            _zc1_final = _zc1()
            _c1_ret_final = bool(_zc1_final < LOW_WALL_TOP)
            _c2_reach_final = _min_dist_mm(cable_geoms, _clip2g)
            print(f"  [FREEZE-SCOPE] pin={'ON' if _perclip_on else 'OFF(control)'} seat_k={_seat_kk} "
                  f"seat_disp={_seat_disp:.2f}mm nbr={_nbr_disp} max={_max_disp:.1f}mm "
                  f"n_moved(>{_MOVE_THR})={_n_moved}/{len(_fs_disp)} -> {_scope} | C1 z={_zc1_final:.1f}"
                  f"({'IN' if _c1_ret_final else 'OUT'} low-wall {LOW_WALL_TOP:.0f}) cable<->C2={_c2_reach_final:+.2f}mm")
            _freeze_scope_rec = {
                "pin_active": _perclip_on, "pin_eqid": _pin_eqid, "pin_body": (int(seat_body) if _perclip_on else None),
                "seat_k": _seat_kk, "seat_disp_mm": round(_seat_disp, 2), "neighbor_disp_mm": _nbr_disp,
                "max_disp_mm": round(_max_disp, 1), "n_moved_gt2mm": _n_moved, "n_cable_bodies": len(_fs_disp),
                "verdict": _scope, "z_c1_seated_mm": round(float(z_c1_seated), 1),
                "z_c1_after_pin_mm": (round(float(_z_c1_after_pin), 1) if _z_c1_after_pin is not None else None),
                "z_c1_final_mm": round(float(_zc1_final), 1), "c1_retained_lowwall": _c1_ret_final,
                "low_wall_top_mm": round(float(LOW_WALL_TOP), 1), "cable_c2_final_mm": round(float(_c2_reach_final), 2),
                "per_body_disp_mm": [round(float(d), 2) for d in _fs_disp], "guide_legs": guide_legs,
            }

        # (5) C2 SEAT ATTEMPT: lower L to push the cable into C2's groove. Over SOLID -> expect the bottom claw to
        # hit the table before the cable seats; MEASURE cable<->C2 + the table jam (do NOT add a void).
        _plg, _ = get_ee_positions(state, scene_info)
        # SEAT_TOPDOWN (penetration fix, human-Rs 2026-06-30 「クリップの壁面にフィンガ、ケーブルが貫通している」):
        # the default C2-PUSH descends the (half-open) gripper to the groove AT the clip (x,y) -> the claws + the
        # dragged cable are forced INTO the clip-wall envelope (a kinematic position-drive can't be stopped by
        # contact). SEAT_TOPDOWN=1 replaces it with a proper open-top insertion: LIFT the cable above the clip wall
        # tops, position over the groove X-centre, then OPEN the gripper (release) so the cable settles into the
        # open-top channel by gravity -- the gripper claws STAY above the wall tops, so neither finger nor cable is
        # forced into the walls (a drag-mis-delivered cable simply MISSES = physically valid, vs forced penetration).
        # DEFAULT 0 -> byte-identical old C2-PUSH. Lead-implemented (authority layer holds Rs's actual directive).
        _seat_topdown = os.environ.get("SEAT_TOPDOWN", "0") == "1"
        _c2_dualseat = (os.environ.get("C2_DUALSEAT", "0") == "1") and _seat_topdown   # Rs corrected-route 2026-07-01: R-rejoin + dual-finger clamp-push (replaces the L-single top-down slide)
        if _c2_dualseat:
            _GHS = (WIDE_RIGHT_Y - WIDE_LEFT_Y) / 2.0   # 0.044 = 88mm two-EE span (INVARIANT#2; tgt2 yc-+GHS: L=-GHS, R=+GHS)
            _wall_top_d = CLIP1_Z + _clip_float_z + 0.030
            _z_above_d = _wall_top_d + 0.012 + ee_off          # hold above the C2 wall tops before the top-down descent
            _seat_z_d = GROOVE_CENTER_Z + _clip_float_z + ee_off   # push the gripped cable centre to the FLOATED C2 groove
            # 1) RE-GRASP the ACTUAL cable (Rs guide-data charter fix). The OLD code moved both arms to the FIXED
            #    (c2x, c2y+-GHS) then CLOSED -> R closed at (c2x, c2y+GHS)=(0.40,0.119) but the cable BOWS to X~0.37
            #    there (between L's grip & the C1 pin) => R gripped EMPTY SPACE (Rs: "R is NOT re-grasping"). FIX:
            #    query the REAL cable body per side + target the EE to the actual world-XYZ. KEEP L holding (the +Y
            #    span stays SUSPENDED between L & the C1 pin -> R re-grasps it in the AIR, no drop onto the solid table).
            # 1a) L (still holding the cable in half-clamp) moves to the -Y grip side + full-clamp. Cable stays held.
            _pld, _prd = get_ee_positions(state, scene_info)
            _La = (c2x, c2y - _GHS, _z_above_d)
            for kk in range(1, 11):
                _fl = tuple(float(_pld[i]) + (_La[i] - float(_pld[i])) * kk / 10 for i in range(3))
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, _fl, R_hold,
                                        label=f"C2-LMOVE{kk}/10", converge_mm=3.0, speed_factor=0.22)
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            _set_gripper_target(control, L_drv, GRIPPER_DRIVER_CLOSE_RAD)   # L half->full clamp (already on the cable)
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _NLg1, _, _, _ = _claw_cable_load(f1L0 + f2L0)
            print(f"  [C2-REGRASP-L] L moved to -Y grip ({c2x:.3f},{c2y - _GHS:+.3f}) + full-clamp: claw<->cable L={_NLg1:.2f}N "
                  f"(L holds -> the +Y cable span is suspended for R to re-grasp)")
            _cap(f"C2 L -Y grip full-clamp: L={_NLg1:.1f}N")
            # 1b) R RE-GRASP the ACTUAL cable at the +Y side, with the BANKED TILT-FOLLOW recipe + SPAN-PRESERVING
            #     targeting (%3 refinements from GD-KoShape-Finger.md §Mid-air re-grasp, human-CONFIRMED 2026-06-21):
            #     - SPAN-PRESERVING (INVARIANT#2): HOLD R's target Y = c2y+GHS (88mm vs L at c2y-GHS); correct ONLY X
            #       to the ACTUAL cable X at that Y (follow the bow). Fixes 'R grips air' WITHOUT touching the span.
            #     - TILT-FOLLOW (banked Finding 2 :126-134): the suspended cable is locally TILTED; a square-on claw
            #       MISSES. Measure theta = cable local Y-Z pitch at R's lane; set R EE = Rx(-90+theta) so the claws
            #       ALIGN with the tilt. Faithful COPY of the _64 monkeypatch (GD-KoShape:157-160); R=re-grasp arm
            #       mirrors the banked L; production solve_ik_dual UNCHANGED (runtime monkeypatch, restored after).
            wp.synchronize()
            _cbq = state.body_q.numpy()[cable_bodies]
            # ⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01「先祖返りしないように」): R targets the ACTUAL cable X (the bow) via argmin
            #    over cable_bodies, NOT a fixed c2x. A FIXED geometric target = the air-grip "R not re-grasping" bug (Rs
            #    2026-07-01). Do NOT revert to a fixed geometric target. Y is HELD at c2y+GHS = 88mm INVARIANT#2 (span-preserving).
            _kR = int(np.argmin(np.abs(_cbq[:, 1] - (c2y + _GHS))))   # cable body nearest R's +Y grip lane (for the bow X/Z)
            _R_ty = c2y + _GHS                                        # HOLD Y = 88mm span (span-preserving, INVARIANT#2)
            _cRx, _cRz = float(_cbq[_kR, 0]), float(_cbq[_kR, 2])     # follow the ACTUAL cable X (bow) + Z at that lane
            _span_y_mm = float(abs(_R_ty - (c2y - _GHS))) * 1e3       # target Y-separation = 88mm by construction
            _picked_dy_mm = float(_cbq[_kR, 1] - _R_ty) * 1e3         # how far the picked body's Y is from the 88mm lane
            _cR = (_cRx, _R_ty, _cRz)
            _zgrip_R = _cRz + ee_off
            print(f"  [C2-REGRASP-R] span-preserving: R target=({_cR[0]:.3f},{_cR[1]:+.3f},{_cR[2]:.3f}) "
                  f"(HOLD Y={_R_ty:+.3f}=+GHS, X follows bow) vs OLD-FIXED X={c2x:.3f} [dX {(_cRx - c2x) * 1e3:+.0f}mm] "
                  f"| picked body idx{_kR} Y{_cbq[_kR, 1]:+.3f} (dY from lane {_picked_dy_mm:+.0f}mm) | target Y-span={_span_y_mm:.1f}mm (88, INVARIANT#2)")
            _ph("C2_REGRASP")
            # --- TILT-FOLLOW monkeypatch (byte-faithful copy of the banked _64, GD-KoShape:157-160; R=re-grasp arm) ---
            _BASE_RX = -_math.pi / 2      # default Rx(-90deg) = gripper down (test:1851)
            # ⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01「先祖返りしないように」): square-on DEFAULT (C2_TILT_SIGN=0). The banked
            #    tilt-follow is FLOATING-cable-specific (GD-KoShape:117) & does NOT transfer to this TAUT route (tilt -> R
            #    misses 0N). Do NOT revert the default to 1. The override + tilt machinery are KEPT for future floating cases.
            _TILT_SIGN = float(os.environ.get("C2_TILT_SIGN", "0"))   # DEFAULT 0 = SQUARE-ON (Rs-approved 2026-07-01「これでやってみて」: the banked tilt-follow is FLOATING-cable-specific & does NOT transfer to this TAUT C1->C2 route, §運用10). Override kept for future floating cases: 1 (banked tilt) / -1 (flip)
            _ROT = {}

            def _rot_quat_rx(angle):  # X-rotation target in solve_ik_dual's XYZW convention (w LAST)
                return wp.array([wp.vec4(_math.sin(angle / 2), 0.0, 0.0, _math.cos(angle / 2))], dtype=wp.vec4, device=DEVICE)

            def _cable_local_pitch(y_t):  # cable local Y-Z pitch theta [rad] at lane y_t (tangent of adjacent segments)
                wp.synchronize()
                cbs = state.body_q.numpy()[cable_bodies]
                cbs = cbs[np.argsort(cbs[:, 1])]
                ys = cbs[:, 1]
                j = int(np.argmin(np.abs(ys - y_t)))
                a, b = max(j - 1, 0), min(j + 1, len(ys) - 1)
                dY, dZ = float(ys[b] - ys[a]), float(cbs[b, 2] - cbs[a, 2])
                return _math.atan2(dZ, dY) if abs(dY) > 1e-9 else 0.0

            def _solve_ik_dual_rot(scene_info_, target_left, target_right, warmstart_jq=None):
                # Faithful copy of solve_ik_dual (test:1814) but with PER-ARM rotation targets _ROT['L']/_ROT['R'].
                fk_model_ = scene_info_["fk_model"]
                fk_state_ = scene_info_["fk_state"]
                le, re = EE_BODY_OFFSET, FRANKA_NUM_JOINTS + EE_BODY_OFFSET
                ol = IKObjectivePosition(link_index=le, link_offset=wp.vec3(0.0, 0.0, 0.0),
                                         target_positions=wp.array(np.array([target_left], dtype=np.float32),
                                                                   dtype=wp.vec3, device=DEVICE), weight=1.0)
                orr = IKObjectivePosition(link_index=re, link_offset=wp.vec3(0.0, 0.0, 0.0),
                                          target_positions=wp.array(np.array([target_right], dtype=np.float32),
                                                                    dtype=wp.vec3, device=DEVICE), weight=1.0)
                rl = IKObjectiveRotation(link_index=le, link_offset_rotation=wp.quat_identity(),
                                         target_rotations=_ROT["L"], weight=0.5)
                rr = IKObjectiveRotation(link_index=re, link_offset_rotation=wp.quat_identity(),
                                         target_rotations=_ROT["R"], weight=0.5)
                jl = IKObjectiveJointLimit(joint_limit_lower=fk_model_.joint_limit_lower,
                                           joint_limit_upper=fk_model_.joint_limit_upper, weight=10.0)
                from newton_routing_utils import _build_collision_objectives
                cobjs = _build_collision_objectives() if os.environ.get("COLLISION_AVOIDANCE", "1") != "0" else []
                iks = IKSolver(fk_model_, n_problems=1, objectives=[ol, orr, rl, rr, *cobjs, jl])
                fj = fk_state_.joint_q.numpy().copy()
                if warmstart_jq is not None:
                    fj = np.asarray(warmstart_jq, dtype=fj.dtype).reshape(-1).copy()
                qin = wp.array(fj.reshape(1, -1), dtype=float, device=DEVICE)
                qout = wp.zeros((1, fk_model_.joint_coord_count), dtype=float, device=DEVICE)
                iks.step(qin, qout, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
                return qout.numpy()[0], float(iks.costs.numpy()[0])

            _theta_R = _cable_local_pitch(_R_ty)   # cable local pitch at R's grip lane (measured at THIS route's geom)
            _ROT["R"] = _rot_quat_rx(_BASE_RX + _TILT_SIGN * _theta_R)   # R = re-grasp arm = TILT-FOLLOW
            _ROT["L"] = _rot_quat_rx(_BASE_RX)                           # L = anchor/holder = default down
            _ik_orig = globals()["solve_ik_dual"]
            globals()["solve_ik_dual"] = _solve_ik_dual_rot   # ik_move_both resolves solve_ik_dual as a module global
            if _demo_rec is not None:  # P3 recorder: effective-rotation register at C2 monkeypatch INSTALL (spec §2.4)
                _demo_rec.note_ik_rot(_ROT["L"].numpy()[0], _ROT["R"].numpy()[0], 1)
            print(f"  [C2-REGRASP-TILT] cable local pitch theta={_math.degrees(_theta_R):+.1f}deg at R lane Y={_R_ty:+.3f} "
                  f"-> R EE Rx({_math.degrees(_BASE_RX + _TILT_SIGN * _theta_R):+.1f}deg); L default (anchor) "
                  f"[banked _64 tilt-follow; a square-on claw MISSES the tilted cable, GD-KoShape:126-134]")
            _set_gripper_target(control, R_drv, GRIPPER_DRIVER_OPEN_RAD)   # R open before descending onto the cable
            for _ in range(15):
                state = physics_step(model, state, solver, contacts, scene_info)
            _prr = get_ee_positions(state, scene_info)[1]
            _hovR = (_cR[0], _cR[1], _z_above_d)
            for kk in range(1, 11):
                _fr = tuple(float(_prr[i]) + (_hovR[i] - float(_prr[i])) * kk / 10 for i in range(3))
                _La2, _fr2 = _inject_detour("C2_REGRASP", kk, 10, _La, _fr)  # DQ7 (ii): R-arm kick-and-recover (None-path passthrough; release-margin guards regrasp_ok)
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, _La2, _fr2,
                                        label=f"C2-RHOVER{kk}/10", converge_mm=3.0, speed_factor=0.22)
                for _ in range(10):
                    state = physics_step(model, state, solver, contacts, scene_info)
            # R-REACH check (LEDGER R-reach wall crux): achieved R XY vs the span-preserving target (Y=c2y+GHS)
            _paR = get_ee_positions(state, scene_info)[1]
            _reach_R_mm = float(np.hypot(_hovR[0] - float(_paR[0]), _hovR[1] - float(_paR[1]))) * 1e3
            print(f"  [C2-REGRASP-REACH] R achieved XY=({float(_paR[0]):.3f},{float(_paR[1]):+.3f}) vs tgt "
                  f"=({_hovR[0]:.3f},{_hovR[1]:+.3f}) resid={_reach_R_mm:.1f}mm "
                  f"(LEDGER R-reach wall: >20mm = R can't reach the 88mm lane = BLOCKED_FOR_USER)")
            _desR = (_cR[0], _cR[1], _zgrip_R)
            for kk in range(1, 9):
                _fr = tuple(float(_hovR[i]) + (_desR[i] - float(_hovR[i])) * kk / 8 for i in range(3))
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, _La, _fr,
                                        label=f"C2-RDESCEND{kk}/8", converge_mm=2.5, speed_factor=0.20)
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            _cap("C2 R re-grasp: descended onto ACTUAL cable (tilt-follow)")
            _cage_d = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * 0.9
            _set_gripper_target(control, R_drv, _cage_d)   # 2-phase cage close (capture-then-gentle, mirrors C1)
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _set_gripper_target(control, R_drv, GRIPPER_DRIVER_CLOSE_RAD)
            for _ in range(40):
                state = physics_step(model, state, solver, contacts, scene_info)
            # VERIFY grip: claw<->cable NORMAL force NONZERO for BOTH L AND R (old failure = R grips air = N_R~0).
            # Judge caveat (GD-KoShape:161): per-arm CAPTURE false-negatives when tilted -> the RELIABLE signal is the
            # claw<->cable NORMAL force (+ cable-tracks-EE) + the §運用14/human video, NOT the b<c<t capture window.
            _NLg, _, _nL, _ = _claw_cable_load(f1L0 + f2L0)
            _NRg, _pkR, _nR, _muR = _claw_cable_load(f1R0 + f2R0)
            _paL2, _paR2 = get_ee_positions(state, scene_info)
            _span_3d_mm = float(np.linalg.norm(np.array(_paL2) - np.array(_paR2))) * 1e3   # achieved L<->R 3D EE span
            _L_grips = bool(_NLg > 0.1)
            _R_grips = bool(_NRg > 0.1)
            _at_88 = bool(_reach_R_mm <= 20.0)
            # ⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01「先祖返りしないように」): regrasp_ok = (_at_88 AND _R_grips) = the charter
            #    core (R genuinely grips the ACTUAL cable @88mm). Do NOT revert to the both-hands-force gate (the
            #    "BLOCKED_INVARIANT2" misnomer, %0 records-vs-fact 2026-07-01): L=0N is a valid 0-normal CAGE, not a miss.
            # RE-GRASP VERDICT (re-spec per %0 GT cross-PV 2026-07-01, records-vs-fact): the charter's core = does R
            # genuinely GRIP the ACTUAL cable at the 88mm lane (not air)? The OLD gate required BOTH L AND R force >0.1N
            # -> it MISLABELED the R-grip + L-0-normal-cage case as "MISS" (R did NOT miss; L is an unloaded cage that
            # RETAINS the cable, video + GD-KoShape:161 "per-arm force misleads"). Split R-reach / R-grip / L-load state.
            if not _at_88:
                _regrasp_verdict = "BLOCKED_REACH_WALL"          # R cannot reach the 88mm lane (LEDGER reach wall)
            elif not _R_grips:
                _regrasp_verdict = "R_MISS_AT_88"                 # R reached the lane but gripped AIR (e.g. tilted claws off the taut cable)
            elif _L_grips:
                _regrasp_verdict = "SUCCESS_DUAL_LOADED_AT_88"    # R + L BOTH load-bearing at the 88mm span
            else:
                _regrasp_verdict = "SUCCESS_R_GRIP_L_CAGE_AT_88"  # R grips @88mm; L = 0-normal-load cage (verify RETAIN via video, GD-KoShape:161)
            _regrasp_ok = bool(_at_88 and _R_grips)               # charter core: R genuinely grips the ACTUAL cable @88mm (L-load-share = a separate Rs Q)
            print(f"  [C2-REGRASP-GRIP] claw<->cable NORMAL: L={_NLg:.2f}N(grips={_L_grips}) R={_NRg:.2f}N(n={_nR},grips={_R_grips}) "
                  f"| R-reach={_reach_R_mm:.1f}mm at_88={_at_88} | achieved 3D span={_span_3d_mm:.1f}mm (Y-sep tgt 88) "
                  f"=> VERDICT={_regrasp_verdict} regrasp_ok={_regrasp_ok}")
            print(f"  [C2-REGRASP-GATE] charter core = R grips the ACTUAL cable @88mm lane (regrasp_ok={_regrasp_ok}). "
                  f"labels: SUCCESS_DUAL_LOADED (R+L force) / SUCCESS_R_GRIP_L_CAGE (R force, L 0-normal cage=retain per video) / "
                  f"R_MISS_AT_88 (R reached but air) / BLOCKED_REACH_WALL. INVARIANT#2 Y-span held; L-load-share + 3D-chord excess = Rs Q. => {_regrasp_verdict}")
            _cap(f"C2 R re-grasp: {_regrasp_verdict} (L={_NLg:.1f} R={_NRg:.1f}N theta={_math.degrees(_theta_R):+.0f}deg)")
            _c2_regrasp_rec = {
                "r_target_x": round(_cRx, 3), "r_target_y": round(_R_ty, 3), "r_target_z": round(_cRz, 3),
                "r_old_fixed_x": round(float(c2x), 3), "r_x_offset_from_fixed_mm": round((_cRx - c2x) * 1e3, 1),
                "picked_body_dy_from_lane_mm": round(_picked_dy_mm, 1),
                "target_y_span_mm": round(_span_y_mm, 1), "achieved_3d_span_mm": round(_span_3d_mm, 1),
                "tilt_theta_deg": round(_math.degrees(_theta_R), 2), "tilt_sign": _TILT_SIGN,
                "r_reach_resid_mm": round(_reach_R_mm, 1), "reached_88mm_lane": _at_88,
                "l_grip_N": round(float(_NLg), 2), "r_grip_N": round(float(_NRg), 2),
                "l_grips": _L_grips, "r_grips": _R_grips, "regrasp_verdict": _regrasp_verdict, "regrasp_ok": _regrasp_ok}
            globals()["solve_ik_dual"] = _ik_orig   # RESTORE default square-on (tilt blast radius = the R re-grasp only)
            if _demo_rec is not None:  # P3 recorder: rotation register RESTORE to default Rx(-90) (spec §2.4)
                _demo_rec.note_ik_rot(None, None, 0)
            _ph("C2_TRANSPORT")  # P3 label: lateral carry to C2 as its own phase (future re-records; CC2-C1)
            # 2) TRANSPORT: carry R's gripped cable segment laterally to the C2 +Y seat point (L already at the -Y seat).
            #    The gripped cable comes WITH the hand -> the cable centre (between L & R) arrives over the C2 groove.
            _carR = (c2x, c2y + _GHS, _z_above_d)
            _prc = get_ee_positions(state, scene_info)[1]
            for kk in range(1, 11):
                _fr = tuple(float(_prc[i]) + (_carR[i] - float(_prc[i])) * kk / 10 for i in range(3))
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, _La, _fr,
                                        label=f"C2-TRANSPORT{kk}/10", converge_mm=3.0, speed_factor=0.20)
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            wp.synchronize()
            _cb_t = state.body_q.numpy()[cable_bodies]
            _nk_t = int(np.argmin(np.abs(_cb_t[:, 1] - c2y)))
            _NLt, _, _, _ = _claw_cable_load(f1L0 + f2L0)
            _NRt, _, _, _ = _claw_cable_load(f1R0 + f2R0)
            print(f"  [C2-TRANSPORT] R carried its grip to C2 +Y; near-c2y cable body X={_cb_t[_nk_t, 0]:.3f} (c2x={c2x:.3f}, "
                  f"dX={(float(_cb_t[_nk_t, 0]) - c2x) * 1e3:+.0f}mm) | still gripped: L={_NLt:.1f}N R={_NRt:.1f}N")
            if _c2_regrasp_rec is not None:
                _c2_regrasp_rec["transport_near_c2_dx_mm"] = round((float(_cb_t[_nk_t, 0]) - c2x) * 1e3, 1)
                _c2_regrasp_rec["transport_still_gripped_L_N"] = round(float(_NLt), 2)
                _c2_regrasp_rec["transport_still_gripped_R_N"] = round(float(_NRt), 2)
            _cap("C2 transport: R grip carried to C2 +Y seat point")
            _ph("C2_DUAL_SEAT")
            # W0-e F-3 (C2 X-follow, %12 2026-07-05, offset-gated + W0E_F3): C2_DUAL_SEAT is already TOP-DOWN (no
            # wall-ride) so a single _c2x_comp on BOTH L/R descent tuples suffices (the v2 crossing-comp insight; no
            # clearance-lift). (a) MEASURE at the post-transport sync via _w0e_guarded_cx (self-syncs, NO new physics
            # step) + plausibility (NOT bare argmin-Y). comp=clamp(-(1-lam)*(cx-c2x),+-22), lam=0.5 (F-1a coeff).
            # (b) log crossing z: z<=840 (wall-height) => PREMISE-FAIL loud (reconsider a lift variant). (0,0)/no-flag
            # -> comp=0.0 -> c2x+0.0==c2x = BYTE-IDENTICAL (gated off on nominal). provenance: cuda:0 + build sha.
            _c2x_comp = 0.0
            _f3_on = (float(scene_info.get("cable_xy_offset", (0.0, 0.0))[0]) != 0.0
                      or float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) != 0.0) and os.environ.get("W0E_F3", "1") == "1"
            if _f3_on:
                _cxc2, _nc2 = _w0e_guarded_cx(c2y, c2x)            # (a) guarded selector + plausibility (self-syncs)
                _cb_f3 = state.body_q.numpy()[cable_bodies]        # already synced by the call above (no new step)
                _mzc2 = np.abs(_cb_f3[:, 1] - c2y) <= 0.0075
                _zc2 = float(_cb_f3[_mzc2, 2].mean()) * 1e3 if _mzc2.any() else float("nan")
                if _cxc2 is None or abs(_cxc2 - c2x) > 0.030:
                    print(f"  [W0E-F3] guarded c2 crossing REJECT (n={_nc2}) -> _c2x_comp=0 (nominal fallback) + FLAG")
                else:
                    _lam3 = float(os.environ.get("W0E_F1A_LAMBDA", "0.5"))
                    _c2x_comp = float(np.clip(-(1.0 - _lam3) * (_cxc2 - c2x), -0.022, 0.022))
                    _pf3 = " ⚠PREMISE-FAIL(z<=840 wall-height -> reconsider lift)" if (_zc2 == _zc2 and _zc2 <= 840.0) else ""
                    print(f"  [W0E-F3] guarded c2 dx={(_cxc2 - c2x) * 1e3:+.2f}mm (n={_nc2}) lam={_lam3} -> "
                          f"_c2x_comp={_c2x_comp * 1e3:+.2f}mm; crossing z={_zc2:.1f}mm{_pf3}")
            # 3) both descend (CLOSED) from above -> clamp-push the cable into the C2 groove (top-down, NOT the lateral slide that drove the claw into the wall)
            for kk in range(1, 13):
                _zk = _z_above_d + (_seat_z_d - _z_above_d) * kk / 12
                state, _ = ik_move_both(model, state, scene_info, solver, contacts,
                                        (c2x + _c2x_comp, c2y - _GHS, _zk), (c2x + _c2x_comp, c2y + _GHS, _zk),
                                        label=f"C2-DUAL-SEAT{kk}/12", converge_mm=2.5, speed_factor=0.20)
                for _ in range(18):
                    state = physics_step(model, state, solver, contacts, scene_info)
                _lgc2 = _min_dist_mm(f1L0 + f2L0, _clip2g)
                _rgc2 = _min_dist_mm(f1R0 + f2R0, _clip2g)
                _NLc2, _ = _claw_c2_load(f1L0 + f2L0)
                _NRc2, _ = _claw_c2_load(f1R0 + f2R0)
                _cabc2 = _min_dist_mm(cable_geoms, _clip2g)
                print(f"  [C2-DUAL-SEAT] k={kk}/12 z={_zk:.3f} Lgrip<->C2={_lgc2:+.3f} Rgrip<->C2={_rgc2:+.3f}mm "
                      f"| claw<->C2 CONTACT-N: L={_NLc2:.2f} R={_NRc2:.2f} | cable<->C2={_cabc2:+.3f}mm")
                _cap(f"C2 dual-seat {kk}/12 Lgrip<->C2={_lgc2:+.2f}")
                if _f3_on:   # (c) F-3 during-descent crossing z-x trace (%12 (log 1) form; offset-gated -> nominal unaffected)
                    wp.synchronize()
                    _Pf3 = state.body_q.numpy()[cable_bodies]
                    _mf3 = np.abs(_Pf3[:, 1] - c2y) <= 0.0075
                    if _mf3.any():
                        _if3 = np.where(_mf3)[0]
                        _cif3 = int(_if3[np.argmin(np.abs(_Pf3[_if3, 0] - (c2x + _c2x_comp)))])
                        print(f"  [W0E-F3] dual-seat k={kk}/12 crossing x={_Pf3[_cif3, 0]:.4f} z={_Pf3[_cif3, 2] * 1e3:.1f}mm")
            _ph("C2_SETTLE")
            # 4) RELEASE both grippers + settle -> genuine NOTCH SETTLE vs claw-held / pop-out (%0 seat-capture concern, charter metric #3;
            #    the C2 clip is open-top w/ zero up-retention -> if the cable pops out on release it was claw-HELD, not settled)
            _cab_c2_held = _min_dist_mm(cable_geoms, _clip2g)
            for _drv in (L_drv, R_drv):
                _set_gripper_target(control, _drv, GRIPPER_DRIVER_OPEN_RAD)
            for _ in range(90):
                state = physics_step(model, state, solver, contacts, scene_info)
            _cab_c2_rel = _min_dist_mm(cable_geoms, _clip2g)
            wp.synchronize()
            _nk_c2 = int(np.argmin(np.abs(state.body_q.numpy()[cable_bodies, 1] - c2y)))
            _z_c2_rel = float(state.body_q.numpy()[cable_bodies][_nk_c2][2]) * 1e3
            _c2_settled = bool(_cab_c2_rel <= 0.5 and abs(_z_c2_rel - (GROOVE_CENTER_Z + _clip_float_z) * 1e3) <= 3.0)
            _c2_settle_rec = {"cable_c2_held_mm": round(_cab_c2_held, 3), "cable_c2_released_mm": round(_cab_c2_rel, 3),
                              "near_c2_cable_z_released_mm": round(_z_c2_rel, 1),
                              "groove_z_mm": round((GROOVE_CENTER_Z + _clip_float_z) * 1e3, 1), "settled_in_notch": _c2_settled}
            print(f"  [C2-DUAL-SETTLE] after RELEASE both grippers (+90 steps): cable<->C2 {_cab_c2_held:+.3f}(claw-held)->{_cab_c2_rel:+.3f}mm(released) "
                  f"| near-C2 cable z={_z_c2_rel:.1f} vs groove {(GROOVE_CENTER_Z + _clip_float_z) * 1e3:.1f} => SETTLED_IN_NOTCH={_c2_settled} "
                  f"(%0 seat-capture: True=genuine settle held by the groove / False=was claw-HELD, popped from the open-top clip)")
            _cap(f"C2 dual-settle: settled={_c2_settled} cable<->C2_released={_cab_c2_rel:+.2f}")
            print("  [C2-DUAL] dual-finger clamp-push complete (top-down; claw-C2 penetration + contact-force + release-settle logged above)")
        elif _seat_topdown:
            _wall_top = CLIP1_Z + _clip_float_z + 0.030    # clip_parts[3/4] dz0.025+hz0.005 = V-groove wall top
            _z_above_ee = _wall_top + 0.012 + ee_off       # hold the cable ~12mm above the wall tops (+ EE offset)
            _nlift = 14
            for k in range(1, _nlift + 1):
                _tx = float(_plg[0]) + (c2x - float(_plg[0])) * k / _nlift
                _ty = float(_plg[1]) + (c2y - float(_plg[1])) * k / _nlift
                _tz = float(_plg[2]) + (_z_above_ee - float(_plg[2])) * k / _nlift
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, (_tx, _ty, _tz), R_hold,
                                        label=f"C2-LIFT{k}/{_nlift}", converge_mm=2.5, speed_factor=0.22)
                for _ in range(15):
                    state = physics_step(model, state, solver, contacts, scene_info)
                _lgc2 = _min_dist_mm(f1L0 + f2L0, _clip2g)
                _lrsep, _ = _hh_clear_mm()
                print(f"  [C2-LIFT] k={k}/{_nlift} EE->({_tx:.3f},{_ty:+.3f},{_tz:.3f}) Lgrip<->C2={_lgc2:+.3f}mm "
                      f"HH-armlink={_lrsep:+.2f}mm (claws ABOVE walls; Lgrip>=0 = no penetration)")
                _cap(f"C2 lift-above-walls {k}/{_nlift}")
            _set_gripper_target(control, L_drv, GRIPPER_DRIVER_OPEN_RAD)   # release -> cable settles into open-top channel
            for _ in range(60):
                state = physics_step(model, state, solver, contacts, scene_info)
            _lgc2_rel = _min_dist_mm(f1L0 + f2L0, _clip2g)
            print(f"  [C2-RELEASE] gripper OPEN -> cable settles into groove (or MISSES if drag mis-delivered); "
                  f"Lgrip<->C2={_lgc2_rel:+.3f}mm (claws stayed above walls = no wall penetration)")
            _cap("C2 release-settle (open-top insertion)")
        else:
            c2_seat_ee_z = GROOVE_CENTER_Z + _clip_float_z + ee_off   # CLIP_FLOAT_Z: descend to the FLOATED C2 groove
            for k in range(1, 7):
                zk = float(_plg[2]) + (c2_seat_ee_z - float(_plg[2])) * k / 6
                state, _ = ik_move_both(model, state, scene_info, solver, contacts,
                                        (float(_plg[0]), float(_plg[1]), zk), R_hold,
                                        label=f"C2-PUSH{k}/6", converge_mm=2.5, speed_factor=0.22)
                for _ in range(20):
                    state = physics_step(model, state, solver, contacts, scene_info)
                _lgc2 = _min_dist_mm(f1L0 + f2L0, _clip2g)   # FLAG-D per-frame L-gripper claws <-> C2 (penetration PV)
                _lrsep, _ = _hh_clear_mm()   # item1 hand-hand ARM-LINK clearance (sphere, matches IK avoid; uncapped)
                print(f"  [C2-PUSH] k={k}/6 Lgrip<->C2={_lgc2:+.3f}mm cable<->C2={_min_dist_mm(cable_geoms, _clip2g):+.3f}mm "
                      f"HH-armlink={_lrsep:+.2f}mm (<0=penetration)")
                _cap(f"C2 seat attempt {k}/6")
        c2_seat_dist = _min_dist_mm(cable_geoms, _clip2g)
        c2_tabN, _ = _claw_table_load(f1L0)
        c2_tab_d = _min_dist_mm(f1L0, _tabg)
        c2_lgrip_dist = _min_dist_mm(f1L0 + f2L0, _clip2g)   # FLAG-D final L-gripper <-> C2 (penetration PV)
        c2_lclaw_c2_N, _ = _claw_c2_load(f1L0 + f2L0)        # Rs corrected-route metric: L-claw <-> C2 CONTACT FORCE (soft over-pen reaction)
        c2_rclaw_c2_N, _ = _claw_c2_load(f1R0 + f2R0)        # R-claw <-> C2 contact force (dual-finger)
        c2_rgrip_dist = _min_dist_mm(f1R0 + f2R0, _clip2g)   # R-gripper claws <-> C2 (penetration PV, dual-finger)
        print(f"  [C2-CLAW-FORCE] L-claw<->C2 pen={c2_lgrip_dist:+.3f}mm N={c2_lclaw_c2_N:.2f} | "
              f"R-claw<->C2 pen={c2_rgrip_dist:+.3f}mm N={c2_rclaw_c2_N:.2f} (N>0 + pen<0 = soft over-penetration; N=0 + pen>=0 = no claw-clip contact)")
        c2_seated = bool(c2_seat_dist <= 0.5)
        # SPACER-CONTAMINATION SPLIT: _clip2g (BOX near c2 XY, no size gate) INCLUDES the spacer box (z-center ~0.81)
        # when SPACER=1 -> cable<->C2 = MIN(cable<->clip-walls, cable<->spacer). Split by z: clip floor = CLIP1_Z+float.
        # If WALLS>>0 but the MIN is ~0/neg, the "seated" is SPACER-CONTACT (cable touches the riser), NOT in-groove.
        _floor_z = CLIP1_Z + _clip_float_z
        _c2_wall_g = [g for g in _clip2g if float(mjd.geom_xpos[g][2]) >= (_floor_z - 0.001)]   # clip V-groove boxes
        _c2_sp_g = [g for g in _clip2g if float(mjd.geom_xpos[g][2]) < (_floor_z - 0.001)]       # spacer riser (z~0.81)
        c2_wall_dist = _min_dist_mm(cable_geoms, _c2_wall_g) if _c2_wall_g else 9e9
        c2_sp_dist = _min_dist_mm(cable_geoms, _c2_sp_g) if _c2_sp_g else 9e9
        print(f"  [C2-SPACER-SPLIT] cable<->C2-clip-WALLS={c2_wall_dist:+.3f}mm cable<->C2-SPACER={c2_sp_dist:+.3f}mm "
              f"(n_walls={len(_c2_wall_g)} n_spacer={len(_c2_sp_g)}; c2_seated used MIN={c2_seat_dist:+.3f}. "
              f"WALLS>>0 + SPACER~0 => 'seated' is SPACER-CONTACT not groove = FALSE seat)")
        # item2 HONEST C2-SEAT verdict (fixes the false positive): (a) use the SPACER-EXCLUDED clip-wall distance,
        # (b) REQUIRE the near-C2 cable centre be at the floated GROOVE z (829+float), not the wall base / low z.
        wp.synchronize()
        _cb2 = state.body_q.numpy()[cable_bodies]
        _near_c2 = int(np.argmin(np.abs(_cb2[:, 1] - c2y)))   # cable body nearest C2 in Y
        cable_z_at_c2 = float(_cb2[_near_c2, 2]) * 1e3
        _groove_c2_mm = (GROOVE_CENTER_Z + _clip_float_z) * 1e3
        c2_in_groove = bool(abs(cable_z_at_c2 - _groove_c2_mm) <= 3.0)
        c2_seated_honest = bool(c2_wall_dist <= 0.5 and c2_in_groove)
        print(f"  [C2-SEAT-HONEST] cable<->C2-WALLS(spacer-excluded)={c2_wall_dist:+.3f}mm (<=0.5 needed) | "
              f"near-C2 cable z={cable_z_at_c2:.1f}mm vs groove {_groove_c2_mm:.1f} (|d|<=3 needed -> in_groove={c2_in_groove}) "
              f"=> c2_seated_HONEST={c2_seated_honest} (vs naive c2_seated={c2_seated} which counts wall/spacer contact)")
        zc1_final, c1_final_dist = _zc1(), _min_dist_mm(cable_geoms, _clip1g)
        # W0-e producer (%12 addendum 2026-07-05): FINAL settled-frame pin-excluded free-node cable<->C1 min = the ①/②
        # classifier input (%9 pre-read pin); _c1_np_min (episode-min over guide+final) = the separate validity diagnostic.
        _c1np_final = (_min_dist_mm([g for g in cable_geoms if g != _seat_geom_mj], _clip1g)
                       if _seat_geom_mj is not None else c1_final_dist)
        _c1_np_min = min(_c1_np_min, _c1np_final); _c2_pen_min = min(_c2_pen_min, c2_seat_dist)
        print(f"  [C2] C2 SEAT ATTEMPT: cable<->C2={c2_seat_dist:+.3f}mm seated={c2_seated} "
              f"bottomclaw<->table={c2_tab_d:+.2f}mm N={c2_tabN:.1f} | C1 final z={zc1_final:.1f}mm "
              f"cable<->C1={c1_final_dist:+.3f}mm (nonpin_final={_c1np_final:+.3f}mm classifier; epmin={_c1_np_min:+.3f}) "
              f"| FLAG-D Lgrip<->C2={c2_lgrip_dist:+.3f}mm (<0=penetration)")
        _cap(f"C2 seat attempt END: cable<->C2={c2_seat_dist:+.2f}mm seated={c2_seated}")

        # --- VERDICT (honest; the probe expects the negative per prior findings) ---
        wp.synchronize()
        _jq, _jqd = state.joint_q.numpy(), state.joint_qd.numpy()
        finite = bool(np.all(np.isfinite(_jq)) and np.all(np.isfinite(state.body_q.numpy())))
        qvel_ok = bool(finite and float(np.max(np.abs(_jqd))) < 100.0)
        _slips = [r["slip_xy"] for r in guide_legs]
        max_slip = max(_slips) if _slips else 9.9
        mean_slip = float(np.mean(_slips)) if _slips else 9.9
        any_drag = bool(max_slip > 0.5)
        all_cradle = bool(all(r["is_cradle"] for r in guide_legs)) if guide_legs else False
        all_c1_ret = bool(all(r["c1_retained_lowwall"] for r in guide_legs)) if guide_legs else False
        any_jam = bool(any(r["JAM"] for r in guide_legs)) or bool(c2_tab_d <= 0.2 or c2_tabN > 0.5)
        slide_through = bool(max_slip < 0.35 and all_cradle and all_c1_ret and not any_jam and finite)
        # item1/4 SPACER-config summary (min over the guide; <0 = penetration). lr MIN = closest HAND-HAND approach at
        # ARM-LINK level (sphere model = the SAME quantity the active IK COLLISION_AVOIDANCE minimises). rpad_c1/lgrip_c2
        # = finger-clip (pad<->clip). NOTE arm geoms are visible-only in sim -> arm-link sphere clearance is the real
        # IK-avoidance metric, but a sim-clear value is still NON-conservative for the true real-robot wrist envelope.
        _gl = guide_legs or []
        _min_lr = min((r.get("lr_gripper_sep_mm", 9e9) for r in _gl), default=9e9)
        _min_rpad_c1 = min((r.get("rpad_c1_dist_mm", 9e9) for r in _gl), default=9e9)
        _min_lgrip_c2 = min((r.get("lgrip_c2_dist_mm", 9e9) for r in _gl), default=9e9)
        print(f"  [C2-FINGERCLIP] min over guide: Rpad<->C1={_min_rpad_c1:+.3f}mm Lgrip<->C2={_min_lgrip_c2:+.3f}mm "
              f"(<0=finger-clip penetration) | min HAND-HAND arm-link clearance={_min_lr:+.3f}mm "
              f"(sphere model, IK avoidance {'ON' if _hh_avoid_on else 'OFF'}; <0=overlap; uncapped)")
        rc2.update({"min_handhand_armlink_mm": round(_min_lr, 3), "hh_avoidance_on": _hh_avoid_on,
                    "min_rpad_c1_mm": round(_min_rpad_c1, 3), "min_lgrip_c2_mm": round(_min_lgrip_c2, 3),
                    "c2_wall_dist_spacer_excluded_mm": round(c2_wall_dist, 3), "cable_z_at_c2_mm": round(cable_z_at_c2, 1),
                    "c2_seated_honest": c2_seated_honest, "c2_seated_naive": c2_seated,
                    "half_unclamp_transition": _trans, "L_cradle_after_halfunclamp": L_is_cradle,
                    "z_c1_seated_mm": round(z_c1_seated, 1), "z_c1_final_mm": round(zc1_final, 1),
                    "cable_c1_seat_dist_mm": round(c1_seat_dist, 3), "cable_c1_final_dist_mm": round(c1_final_dist, 3),
                    "cable_c1_nonpin_final_mm": round(_c1np_final, 3),   # %12 ①/② classifier input (final settled, pin-excluded free-node 床 bar)
                    "cable_c1_nonpin_epmin_mm": round(_c1_np_min, 3), "cable_c2_pen_epmin_mm": round(_c2_pen_min, 3),  # episode-min penetration diagnostic
                    "cable_c2_seat_dist_mm": round(c2_seat_dist, 3), "c2_seated": c2_seated,
                    "guide_legs": guide_legs, "max_abs_slip_xy": round(max_slip, 3),
                    "mean_slip_xy": round(mean_slip, 3), "any_drag": any_drag, "all_cradle_during_guide": all_cradle,
                    "all_c1_retained_lowwall": all_c1_ret, "any_table_jam": any_jam,
                    "cradle_break_x": cradle_break_x, "jam_onset_x": jam_onset_x,
                    "c2_lclaw_c2_contact_N": round(c2_lclaw_c2_N, 2), "c2_rclaw_c2_contact_N": round(c2_rclaw_c2_N, 2),
                    "c2_lgrip_c2_pen_mm": round(c2_lgrip_dist, 3), "c2_rgrip_c2_pen_mm": round(c2_rgrip_dist, 3),
                    "c2_dualseat_on": bool(os.environ.get("C2_DUALSEAT", "0") == "1"),
                    "c2_regrasp_verdict": (_c2_regrasp_rec or {}).get("regrasp_verdict"),
                    "c2_regrasp_r_reach_resid_mm": (_c2_regrasp_rec or {}).get("r_reach_resid_mm"),
                    "c2_regrasp_l_grip_N": (_c2_regrasp_rec or {}).get("l_grip_N"),
                    "c2_regrasp_r_grip_N": (_c2_regrasp_rec or {}).get("r_grip_N"),
                    "c2_regrasp_ok": (_c2_regrasp_rec or {}).get("regrasp_ok"),
                    "c2_regrasp_target_y_span_mm": (_c2_regrasp_rec or {}).get("target_y_span_mm"),
                    "c2_regrasp_tilt_theta_deg": (_c2_regrasp_rec or {}).get("tilt_theta_deg"),
                    "slide_through": slide_through, "finite": finite, "qvel_ok": qvel_ok})
        _cons = ("SLIDE-THROUGH @CPU-rigid+claw-mu~0.70 -> CONSERVATIVE for 'しごき works' (a flexible/lower-mu real "
                 "cable slides MORE) = bankable yes" if slide_through else
                 "FAILS, MIXED conservatism: (a) DRAG + (b) C2-unreached are NON-conservative @CPU-rigid (rigid cable "
                 "+ pad-pinned claw mu~0.70 OVERSTATE drag/unreach; a flexible/lower-mu/GPU cable may slide+reach "
                 "better -> confirm before banking the 'しごき' negative); (c) the C2-over-solid bottom-claw "
                 "ride-up/cradle-break (void X-ceiling 0.366 < C2 X 0.40) is CONSERVATIVE geometry = transfers")
        print(f"  [C2-VERDICT] half_unclamp_cradle={L_is_cradle} | GUIDE max|slip_xy|={max_slip:.3f} "
              f"(mean {mean_slip:+.3f}) -> {'SLIDE' if max_slip < 0.35 else ('DRAG' if max_slip > 0.65 else 'PARTIAL')} "
              f"| all_cradle={all_cradle} cradle_break@X={cradle_break_x} | C1_ret_all={all_c1_ret} "
              f"z_c1 {z_c1_seated:.1f}->{zc1_final:.1f}mm cable<->C1 {c1_seat_dist:+.2f}->{c1_final_dist:+.2f}mm")
        print(f"  [C2-VERDICT] C2 reach: cable<->C2 {c2_dist_atseat:+.2f}->{c2_seat_dist:+.2f}mm seated={c2_seated} "
              f"| TABLE-JAM (claw vs SOLID, NOT cable-drag): any_jam={any_jam} jam_onset@X={jam_onset_x} "
              f"(void X-ceil 0.366; C2 X={c2x}) | finite={finite} qvel_ok={qvel_ok}")
        print(f"  [C2-VERDICT] slide_through={slide_through} -> {_cons}")

        # §運用14 video: the FULL sequence (grasp->carry->seat C1->half-unclamp->guide->C2 attempt) + a summary PNG.
        if record_video:
            _out_mp4 = os.path.join(output_dir or ".", "route_c1_to_c2.mp4")
            _subp.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "1.5", "-i",
                       os.path.join(_frames_dir, "f%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                       "-pix_fmt", "yuv420p", _out_mp4], check=False)
            _frames = sorted(_glob.glob(os.path.join(_frames_dir, "f*.png")))
            _png = os.path.join(output_dir or ".", "route_c1_to_c2.png")
            if _frames:
                _shutil.copy(_frames[-1], _png)
            for _src, _dst in ((_out_mp4, "route_c1_to_c2.mp4"), (_png, "route_c1_to_c2.png")):
                try:
                    _shutil.copy(_src, os.path.expanduser(f"~/Downloads/{_dst}"))
                except Exception:  # noqa: BLE001
                    pass
            print(f"  [C2] §運用14 video -> {_out_mp4} (+ ~/Downloads/route_c1_to_c2.mp4); "
                  f"PNG -> {_png} (+ ~/Downloads/route_c1_to_c2.png) [{len(_frames)} frames]")
        # PERCLIP_PIN (b)-pin freeze-scope + route summary -> JSON. The route block exits HERE (before the
        # fn-level metrics dump at the end of _run_mujoco_grasp_route is reached), so persist the headline metrics
        # for %0 cross-PV. Only when the freeze-scope was measured (_fs_on); default route writes nothing extra.
        if output_dir and _fs_on:
            try:
                os.makedirs(output_dir, exist_ok=True)
                with open(os.path.join(output_dir, "route_c2_pin.json"), "w") as _jf:
                    json.dump({"route_c2_freeze_scope": _freeze_scope_rec,
                               "route_c2_regrasp": _c2_regrasp_rec,  # Rs guide-data charter: R re-grasp (R-reach + R-grip-nonzero, %0 cross-PV)
                               "route_c2_settle": _c2_settle_rec,  # C2_DUALSEAT release-and-settle (%0 seat-capture, charter metric #3)
                               "route_c2_metrics": rc2,  # %3 integrated-route charter: full 5-metric dict for A/B + %0 cross-PV
                               "x_clip": float(x_clip), "y_clip": float(y_clip), "c2x": float(c2x), "c2y": float(c2y),
                               "clip_float_z_mm": round(float(_clip_float_z) * 1e3, 1),
                               "spacer_on": bool(os.environ.get("SPACER", "0") == "1" and _clip_float_z > 0.0),
                               "finite": bool(finite), "qvel_ok": bool(qvel_ok)}, _jf, indent=2)
                print(f"  [C2-PIN] freeze-scope metrics -> {os.path.join(output_dir, 'route_c2_pin.json')}")
            except Exception as _e:  # noqa: BLE001
                print(f"  [C2-PIN] (json dump skipped: {_e})")
        if _demo_rec is not None:  # P3 recorder: finalize with the run verdict BEFORE the mid-fn sys.exit (spec §2.7)
            _demo_rec.finalize(verdict=_c2_regrasp_rec)
        sys.exit(0 if (finite and qvel_ok) else 2)

    # --- M-Hook-1 (PART 2): CONTINUOUS drop-in onto the REAL collidable clip (banked r_s71_clip_dropin_72) ---
    # MECHANISM = "lower into the mouth THEN release" (NOT release-high): lower the claw to REL_CABLE_Z (wall top)
    # so the cable (~claw+7) is INSIDE the mouth, UNCLAMP -> the cable drops the last ~18mm into the 809 groove
    # (the collidable clip floor catches it). DEPTH-critical: 0.820 seats / 0.842 fails. PIN=0 (no kinematic trick):
    # the real-collision floor is the PRIMARY vertical retainer (%9 directive; the authorized pin log:6534 =
    # Y-slide insurance only, NOT used here). ee_off was captured at CLOSE (above) -> the post-route drag-loosening
    # is NOT compensated -> faithfully tests %9's integration concern.
    hook = {"attempted": False}
    if DO_HOOK and _clip_collidable:
        hook["attempted"] = True
        release_ee_z = REL_CABLE_Z + ee_off  # EE z s.t. the (clean-grip) cable is at REL_CABLE_Z=0.820
        ok["hook_descend"] = True
        for k in range(1, 9):  # 2) LOWER into the clip mouth (banked conv 2.5 / sf 0.25)
            zk = z_lift + (release_ee_z - z_lift) * k / 8
            state, okk = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(x_clip, y_clip, zk),
                                      label=f"HOOK-DESCEND{k}/8", converge_mm=2.5, speed_factor=0.25)
            ok["hook_descend"] = ok["hook_descend"] and bool(okk)
            if k % 2 == 0:
                _cap(f"HOOK descend {k}/8")
        for _ in range(40):
            state = physics_step(model, state, solver, contacts, scene_info)
        cz_above = _seg_z_mm(y_clip)  # gripped seg now at the off-centre clip Y (y_clip), not GRASP_YC
        _cap("HOOK above-clip (pre-release)")
        _set_gripper_target(control, driver_joints, GRIPPER_DRIVER_OPEN_RAD)  # 2.5) DROP-IN: UNCLAMP
        for _ in range(150):
            state = physics_step(model, state, solver, contacts, scene_info)
        cz_seat = _seg_z_mm(y_clip)
        seated = bool(abs(cz_seat - GROOVE_CENTER_Z * 1e3) < 4.0)  # gripped seg IN the 809 groove (not clip top 834)
        _clipg = _clip_geoms()  # %9 ADD: cable<->clip mj_geomDistance AT seat = the REAL-seat proof (not ee_off-stale)
        seat_clip_dist_mm = _min_dist_mm(cable_geoms, _clipg) if _clipg else 9e9  # <=0 = touching/seated on the clip
        _cap("HOOK DROP-IN (released; seated in groove?)")
        for _ in range(60):  # 4) settle with the gripper OPEN
            state = physics_step(model, state, solver, contacts, scene_info)
        ok["hook_ascend"] = True
        for k in range(1, 7):  # 5) ASCEND -> the cable must STAY in the groove on the real floor ALONE
            zk = release_ee_z + 0.02 * k
            state, okk = ik_move_both(model, state, scene_info, solver, contacts, *tgt2(x_clip, y_clip, zk),
                                      label=f"HOOK-ASCEND{k}/6", converge_mm=4.0, speed_factor=0.3)
            ok["hook_ascend"] = ok["hook_ascend"] and bool(okk)
            _cap(f"HOOK ascend {k}/6")
        cz_final = _seg_z_mm(y_clip)
        retained = bool(abs(cz_final - GROOVE_CENTER_Z * 1e3) < 8.0)  # stays at 809 after the gripper retracts
        fell = bool(cz_final < (TABLE_HEIGHT * 1e3 + 7.0))  # dropped to the table 804
        final_clip_dist_mm = _min_dist_mm(cable_geoms, _clipg) if _clipg else 9e9  # cable<->clip AFTER claws retract
        hook_ok = bool(seated and retained and not fell and ok["hook_descend"] and ok["hook_ascend"])
        hook.update({"release_ee_z": round(release_ee_z, 4), "ee_off_mm": round(ee_off * 1e3, 1),
                     "cz_above_mm": round(cz_above, 1), "cz_seat_mm": round(cz_seat, 1), "seated_809": seated,
                     "cz_final_mm": round(cz_final, 1), "retained_809": retained, "fell_to_table": fell,
                     "n_clip_geoms": len(_clipg), "seat_clip_dist_mm": round(seat_clip_dist_mm, 3),
                     "final_clip_dist_mm": round(final_clip_dist_mm, 3), "hook_ok": hook_ok})
        print(f"  [S6_HOOK] release_ee_z={release_ee_z:.4f} (ee_off={ee_off * 1e3:.0f}mm) above={cz_above:.0f} "
              f"SEAT={cz_seat:.0f}mm (t809 seated={seated}) ASCEND-final={cz_final:.0f}mm "
              f"(retained@809={retained} fell={fell}) -> hook_ok={hook_ok}")
        print(f"  [S6_HOOK] %9-ADD real-seat proof: cable<->clip mj_geomDistance seat={seat_clip_dist_mm:+.3f}mm "
              f"final={final_clip_dist_mm:+.3f}mm ({len(_clipg)} clip geoms; <=0=touching the clip floor, "
              f">>0=FLOATING=ee_off-stale FALSE-seat) -> %2 cross-PV")
        # %3 over-void LONG-HOLD CREEP test (Rs (b) routing-port auth, 2026-06-29): after the claws fully retract,
        # does the seated segment CREEP out of the clip groove over >=4000f (the AR-killer failure mode)? + do the
        # adjacent segments OVER the table-void (Y[grasp_at +- 0.060], build:1068-1069) sag and pull the seated
        # body? PIN=0 (NATURAL seat+hold; the clip-pin is the C2 contingency IF creep occurs). DEFAULT
        # LONG_HOLD_F=0 -> skipped = byte-identical. throat_frac N/A post-release (claws retracted; clip-seat is
        # measured by cz vs 809 + mj_geomDistance cable<->clip, not a claw throat).
        LONG_HOLD_F = int(os.environ.get("LONG_HOLD_F", "0"))
        if LONG_HOLD_F > 0:
            _vlo, _vhi = _grasp_at - 0.060, _grasp_at + 0.060  # table-void Y span (build:1068-1069)
            _cy = state.body_q.numpy()[cable_bodies, 1]
            _adj = (np.abs(_cy - y_clip) > GHS) & (_cy >= _vlo) & (_cy <= _vhi)  # adj segs OVER the void
            creep = []
            for _hf in range(1, LONG_HOLD_F + 1):
                state = physics_step(model, state, solver, contacts, scene_info)
                if _hf % 250 == 0 or _hf == LONG_HOLD_F:
                    _czf = _seg_z_mm(y_clip)
                    _cd = _min_dist_mm(cable_geoms, _clipg)
                    _bz = state.body_q.numpy()[cable_bodies, 2]
                    _adjmin = float(np.min(_bz[_adj]) * 1e3) if _adj.any() else 9e9
                    _cmz = float(np.mean(_bz) * 1e3)
                    creep.append({"f": _hf, "cz_mm": round(_czf, 1), "clip_dist_mm": round(_cd, 3),
                                  "adj_min_mm": round(_adjmin, 1), "cable_mz_mm": round(_cmz, 1)})
                    if _hf % 1000 == 0 or _hf == LONG_HOLD_F:
                        _cap(f"LONG-HOLD {_hf}/{LONG_HOLD_F}")
            _cz0, _czN = creep[0]["cz_mm"], creep[-1]["cz_mm"]
            _crept = _cz0 - _czN
            _fell_long = bool(_czN < (TABLE_HEIGHT * 1e3 + 7.0))
            _held_long = bool(abs(_czN - GROOVE_CENTER_Z * 1e3) < 8.0 and not _fell_long)
            hook.update({"long_hold_f": LONG_HOLD_F, "creep_series": creep, "cz_start_mm": _cz0,
                         "cz_end_mm": _czN, "crept_mm": round(_crept, 1), "held_long": _held_long,
                         "fell_long": _fell_long})
            print(f"  [S6_HOOK] LONG-HOLD {LONG_HOLD_F}f: cz {_cz0:.0f}->{_czN:.0f}mm (crept {_crept:+.1f}mm) "
                  f"clip_dist {creep[0]['clip_dist_mm']:+.3f}->{creep[-1]['clip_dist_mm']:+.3f}mm "
                  f"adj_min {creep[0]['adj_min_mm']:.0f}->{creep[-1]['adj_min_mm']:.0f}mm "
                  f"held_long={_held_long} fell_long={_fell_long} -> %0/%2 creep cross-PV")
    elif DO_HOOK and not _clip_collidable:
        print("  [S6_HOOK] SKIPPED: S6_HOOK=1 but CLIP_COLLISION!=1 -> no collidable clip floor to seat on "
              "(run with CLIP_COLLISION=1 CLIP_X=0.40 CLIP_Y=0.0). Reporting route-only.")

    # --- STEP-13 RE-GRASP MINIMAL PROXY (env-gate STEP13_REGRASP=1; %3 Rs Option A 2026-06-29, post-5体) ---
    # Q: can R re-grasp the cable under [clip NATURAL-seat + L-clamp] DUAL support WITHIN 88mm, PIN=0, the seat
    # HOLDING through R's approach+close (the pull)? INVARIANT-SAFE BY DESIGN: PIN=0 (natural drop-in seat, NO
    # weld/new kinematic, INVARIANT#5), |R-L| span <= REGRASP_SPAN_MAX 88mm (INVARIANT#2), DiffIK-only arms
    # (ik_move_both, INVARIANT#3), NO forced cable placement (seat = the physics drop-in), コ untouched (#4).
    # ⚠ CC5 PROXY CAVEAT (RECORD): the co-located grasp+clip (S6_ENGAGE_YC) is a DEGENERATE X-route, NOT the
    # milestone diagonal route -> this isolates the RE-GRASP question ONLY, NOT the routed delivery.
    if os.environ.get("STEP13_REGRASP", "0") == "1" and hook.get("seated_809") and _clip_collidable:
        _SPAN_MAX = 2.0 * GHS  # 0.088 == the AR env's REGRASP_SPAN_MAX (newton_aerial_regrasp_mujoco_env.py:306)
        L_drv, R_drv = [6, 10], [20, 24]  # per-arm gripper drivers (test:1344-1345)
        z_off = z_grasp - (TABLE_HEIGHT + CABLE_RADIUS)  # EE-above-cable offset (route's grasp calibration)
        y_seat = y_clip            # clip-seated body Y (+0.150)
        # ARM-SIDE: L = the lower-Y arm (tgt = GRASP_YC-GHS), R = the higher-Y arm (GRASP_YC+GHS); R's target MUST be
        # >= L's (no cross-over reach). v3 DE-CONFOUND (%3 §運用28 on v1, 2026-06-29): v1 had L only 30mm from the
        # seat (adjacent clamp directly lifted it = proxy-compression artifact) AND R ABOVE the seat (wrong side --
        # real step-13 R@body29 is just BELOW seat@body30). v3 fixes BOTH: R re-grasps JUST BELOW the seat (the REAL
        # adjacent-below position), L clamps FAR BELOW R (>=75mm below the seat, no longer adjacent -> isolates whether
        # R's REAL adjacent re-grasp lifts the open-top seat, with the L-adjacent-lift confound removed). Both <=88mm.
        # v3.1 (both arms MUST be over the table-void Y[0.090,0.210] to コ-cage [f1ext reaches under]; v3 missed:
        # R@+0.135 hit the clip Y-edge [clip spans +0.135..+0.165] + over-fold, L@+0.075 was on the SOLID table
        # below the void so it could not cage). v3.1: R re-grasps ADJACENT-BELOW the seat but CLEAR of the clip edge
        # (+0.120, 6mm clear, over void); L clamps as FAR below as the void allows (+0.095, 55mm below the seat,
        # over the void's lower edge) -> de-confound (L not adjacent) preserved AND both can cage. span 25mm<=88.
        y_rgrasp = y_clip - 0.030  # R (higher arm) re-grasps ADJACENT-BELOW the seat, CLEAR of the clip (+0.120, over void)
        y_lhold = y_clip - 0.055   # L (lower arm) clamps FAR-ish below (+0.095, 55mm below seat, over the void edge)
        assert abs(y_lhold - y_rgrasp) <= _SPAN_MAX + 1e-9, \
            f"INVARIANT#2 VIOLATED: re-grasp span {abs(y_lhold - y_rgrasp) * 1e3:.0f}mm > 88mm -> STOP"
        print(f"  [S13] step-13 RE-GRASP PROXY: seat@Y{y_seat:+.3f} L-clamp@Y{y_lhold:+.3f} R-regrasp@Y{y_rgrasp:+.3f} "
              f"span={abs(y_lhold - y_rgrasp) * 1e3:.0f}mm<=88 PIN=0 DiffIK (CC5: co-located degenerate route)")

        def _cable_at(y_t):  # the REAL settled cable body nearest target Y (NOT a hand-placed pose)
            cb = state.body_q.numpy()[cable_bodies]
            i = int(np.argmin(np.abs(cb[:, 1] - y_t)))
            return float(cb[i][0]), float(cb[i][2])  # (x, z) of that body

        s13 = []

        def _s13(tag):
            cd = _min_dist_mm(cable_geoms, _clipg)  # (b) clip-seat retention through the manipulation
            czs = _seg_z_mm(y_seat)
            f1L, f1R, f2L, f2R = _arm_split()
            cgL, cgR = _cage(f1L, f2L), _cage(f1R, f2R)  # (c) L-hold / (a) R re-grasp cage
            rec = {"tag": tag, "clip_dist_mm": round(cd, 3), "seat_z_mm": round(czs, 1),
                   "L_held": cgL["held"], "L_f1": cgL["f1"], "L_f2": cgL["f2"],
                   "R_held": cgR["held"], "R_f1": cgR["f1"], "R_f2": cgR["f2"]}
            s13.append(rec)
            print(f"  [S13] {tag:14s} clip_dist={cd:+.3f}mm seat_z={czs:.0f}mm "
                  f"L[held={cgL['held']} {cgL['f1']:+.2f}/{cgL['f2']:+.2f}] "
                  f"R[held={cgR['held']} {cgR['f1']:+.2f}/{cgR['f2']:+.2f}]")
            return rec

        def _close(drv):  # proven 2-phase cage close (capture-then-gentle), per-arm
            cr = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * 0.9
            _set_gripper_target(control, drv, cr)
            for _ in range(30):
                _do_step()
            for ck in range(1, 13):
                _set_gripper_target(control, drv, cr + (GRIPPER_DRIVER_CLOSE_RAD - cr) * ck / 12)
                for _ in range(12):
                    _do_step()

        def _do_step():
            nonlocal state
            state = physics_step(model, state, solver, contacts, scene_info)

        _set_gripper_target(control, L_drv + R_drv, GRIPPER_DRIVER_OPEN_RAD)  # both open post-seat
        for _ in range(20):
            _do_step()
        _s13("post-seat")
        lx, lz = _cable_at(y_lhold)
        rx, rz = _cable_at(y_rgrasp)
        z_clear = max(lz, rz) + z_off + 0.10
        # 1) L descends to its adjacent body + CLAMP (R parks clear above its target -- L-clamp FIRST, step-13 order)
        for k in range(1, 7):
            lzk = z_clear + (lz + z_off - z_clear) * k / 6
            state, _ = ik_move_both(model, state, scene_info, solver, contacts,
                                    (lx, y_lhold, lzk), (rx, y_rgrasp, z_clear),
                                    label=f"S13-L-DESCEND{k}/6", converge_mm=3.0, speed_factor=0.25)
        _close(L_drv)
        for _ in range(60):
            _do_step()
        _s13("L-clamped")
        _cap("S13 L-clamped ([clip+L] dual support)")
        # 2) R DiffIK-approaches + re-grasps (the PULL/disturbance); L holds, clip holds
        for k in range(1, 7):
            rzk = z_clear + (rz + z_off - z_clear) * k / 6
            state, _ = ik_move_both(model, state, scene_info, solver, contacts,
                                    (lx, y_lhold, lz + z_off), (rx, y_rgrasp, rzk),
                                    label=f"S13-R-APPROACH{k}/6", converge_mm=3.0, speed_factor=0.25)
            if k % 2 == 0:
                _s13(f"R-approach{k}/6")
                _cap(f"S13 R-approach {k}/6")
        _close(R_drv)
        for _ in range(60):
            _do_step()
        _s13("R-regrasped")
        _cap("S13 R-regrasped (the pull)")
        # 3) settle hold -- does the seat survive the re-grasp?
        for _ in range(200):
            _do_step()
        _post = _s13("post-hold")
        # seat HELD = stayed touching the clip (clip_dist<=0.5, deepening OK) AND did not fall (seat_z>=805) THROUGH all.
        seat_held = bool(all(r["clip_dist_mm"] <= 0.5 and r["seat_z_mm"] >= 805.0 for r in s13))
        r_regrasped = bool(_post["R_held"])  # R caged the cable at the end (the re-grasp succeeded)
        l_held = bool(_post["L_held"])  # L still holds the cable AFTER R's re-grasp (no pull-out / intra-finger slip)
        hook["step13"] = {"seat_held_through": seat_held, "r_regrasped": r_regrasped, "l_held": l_held,
                          "span_mm": round(abs(y_lhold - y_rgrasp) * 1e3, 1), "y_seat": y_seat,
                          "y_lhold": y_lhold, "y_rgrasp": y_rgrasp, "series": s13,
                          "PROXY_CAVEAT": "co-located grasp+clip = degenerate X-route (CC5); isolates re-grasp ONLY"}
        print(f"  [S13] VERDICT seat_held_through={seat_held} r_regrasped={r_regrasped} l_held={l_held} "
              f"span={abs(y_lhold - y_rgrasp) * 1e3:.0f}mm PIN=0 -> %0/%2 GT cross-PV")

    # --- CLIP delta(h) / R-REACH-WALL VIDEO PROBE (env-gate CLIP_DELTAH=1; %3 Rs video-confirm 2026-06-30) ---
    # Rs wants VISUAL confirmation of the 2 foundational findings, with a BODY30-SPECIFIC z-track (the prior
    # debates' CC4-CRITICAL: NOT _seg_z_mm window-mean, NOT _min_dist_mm min-over-all). SHOW-the-behavior (NOT
    # a build/PASS of a design):
    #   F1 (R-reach wall): is R geometrically WALLED caging body29 (adjacent-BELOW seat, at the clip Y-edge)?
    #   F2 (delta ~ O(h)): lift the adjacent body to h in {3,10,30}mm; does body30 STAY in the OPEN-TOP clip
    #                      (z30 < low-wall-top 820) at route-LOW h and only ESCAPE at high h?  If so the current
    #                      clip (7mm wall above the cable) suffices for a low route -> clip redesign likely unneeded.
    # INVARIANT-SAFE (probe, not pipeline): PIN=0 natural drop-in seat (#5), DiffIK arms (#3), コ untouched (#4),
    # 0-commit; a single-body diagnostic lift = a MEASUREMENT of clip retention, NOT a single-arm pipeline (#1).
    # CC5: the co-located X-route is degenerate for DELIVERY but representative for the LOCAL lift-coupling (same
    # seg stiffness + the real clip walls); a FARTHER L-grasp UNDER-estimates the seat coupling (conservative).
    if os.environ.get("CLIP_DELTAH", "0") == "1" and hook.get("seated_809") and _clip_collidable:
        import glob
        import shutil
        import subprocess
        L_drv, R_drv = [6, 10], [20, 24]                       # per-arm gripper drivers (test:1344-1345)
        z_off_dh = z_grasp - (TABLE_HEIGHT + CABLE_RADIUS)     # EE-above-cable offset (route grasp calibration)
        y_seat = y_clip
        LOW_WALL_TOP = (CLIP1_Z + 0.020) * 1e3                 # 820mm low-wall top (clip_parts dz0.0125+hz0.0075)
        HIGH_WALL_TOP = (CLIP1_Z + 0.030) * 1e3               # 830mm high-wall top (clip_parts dz0.025+hz0.005)
        _clipg_dh = _clip_geoms()

        def _do_step():
            nonlocal state
            state = physics_step(model, state, solver, contacts, scene_info)

        # body30-SPECIFIC z-track (CC4): FREEZE the seat body index ONCE, then read body_q[seat_body,2] DIRECTLY.
        wp.synchronize()
        _cb_y = state.body_q.numpy()[cable_bodies, 1]
        _seat_k = int(np.argmin(np.abs(_cb_y - y_seat)))
        seat_body = int(cable_bodies[_seat_k])

        def _z30():
            wp.synchronize()
            return float(state.body_q.numpy()[seat_body, 2]) * 1e3  # mm — the FROZEN seat body, every call

        def _cable_xz(y_t):
            wp.synchronize()
            cb = state.body_q.numpy()[cable_bodies]
            i = int(np.argmin(np.abs(cb[:, 1] - y_t)))
            return float(cb[i, 0]), float(cb[i, 1]), float(cb[i, 2])

        def _close(drv):  # proven 2-phase コ cage close (capture-then-gentle), per-arm
            cr = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * 0.9
            _set_gripper_target(control, drv, cr)
            for _ in range(30):
                _do_step()
            for ck in range(1, 13):
                _set_gripper_target(control, drv, cr + (GRIPPER_DRIVER_CLOSE_RAD - cr) * ck / 12)
                for _ in range(12):
                    _do_step()

        _set_gripper_target(control, L_drv + R_drv, GRIPPER_DRIVER_OPEN_RAD)
        for _ in range(20):
            _do_step()
        z30_seated = _z30()
        bx_s, _, bz_s = _cable_xz(y_seat)
        z_park = bz_s + z_off_dh + 0.12
        Lpark = (bx_s, GRASP_YC - GHS, z_park)
        Rpark = (bx_s, GRASP_YC + GHS, z_park)
        # FREEZE the per-arm claw-geom partition ONCE at the symmetric straddle pose (names carry pad-not-arm id ->
        # _arm_split by world-Y is the only split; freeze the geom-ids here so later moves can't mis-classify).
        state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, Rpark,
                                label="DH-STRADDLE", converge_mm=4.0, speed_factor=0.25)
        for _ in range(20):
            _do_step()
        f1L0, f1R0, f2L0, f2R0 = _arm_split()  # f1R0/f2R0 = R-arm claws (FROZEN ids); f1L0/f2L0 = L-arm
        print(f"  [DH] seat_body=idx{seat_body} (cable[{_seat_k}] Y{_cb_y[_seat_k]:+.3f}) z30_seated={z30_seated:.1f}mm "
              f"(groove 809 / low-wall {LOW_WALL_TOP:.0f} / high-wall {HIGH_WALL_TOP:.0f}); "
              f"claw-geoms L=f1{len(f1L0)}/f2{len(f2L0)} R=f1{len(f1R0)}/f2{len(f2R0)}")

        # ===== FINDING 1: R (higher-Y arm) tries to cage body29 (adjacent-BELOW the seat, at the clip Y-edge) =====
        y_b29 = y_seat - 0.015            # one segment (~15mm) below the seat = body29 (the REAL step-13 R target)
        bx9, by9, bz9 = _cable_xz(y_b29)
        _f1s = _fidx[0]
        _cap("F1 R-reach: start (R above body29)")
        for k in range(1, 9):
            rzk = z_park + (bz9 + z_off_dh - z_park) * k / 8
            state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, (bx9, y_b29, rzk),
                                    label=f"DH-F1-R-DESCEND{k}/8", converge_mm=3.0, speed_factor=0.22)
            if k % 2 == 0:
                _cap(f"F1 R-descend {k}/8 (claw vs clip Y-edge)")
        _close(R_drv)
        for _ in range(40):
            _do_step()
        R_cage = _cage(f1R0, f2R0)
        R_claw_clip_mm = _min_dist_mm(f1R0, _clipg_dh) if (f1R0 and _clipg_dh) else 9e9  # <0 = R bottom claw INTO clip
        R_reached = bool(R_cage["held"])
        R_walled = bool(R_claw_clip_mm < 2.0 and not R_reached)
        _cap("F1 R-regrasp attempt (caged the cable? or walled by the clip?)")
        print(f"  [DH] F1 R-reach body29@Y{by9:+.3f}: held={R_reached} R[f1={R_cage['f1']:+.2f}/f2={R_cage['f2']:+.2f}] "
              f"R-bottom-claw<->clip={R_claw_clip_mm:+.2f}mm -> {'WALLED' if R_walled else ('caged' if R_reached else 'missed/clear')}")
        _set_gripper_target(control, R_drv, GRIPPER_DRIVER_OPEN_RAD)
        for _ in range(10):
            _do_step()
        for k in range(1, 7):
            rzk = (bz9 + z_off_dh) + (z_park - (bz9 + z_off_dh)) * k / 6
            state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, (bx9, y_b29, rzk),
                                    label=f"DH-F1-R-RETRACT{k}/6", converge_mm=3.0, speed_factor=0.25)
        for _ in range(40):
            _do_step()
        z30_after_R = _z30()
        print(f"  [DH] F1 post-R-retract z30={z30_after_R:.1f}mm (seat undisturbed if ~{z30_seated:.0f})")
        _f1e = _fidx[0]

        # ===== FINDING 2: lift the closest cage-able adjacent body to h in {3,10,30}mm; track z30 (delta ~ O(h)?) =====
        # L (lower-Y arm) cages from the -Y side. Try body29@+0.135 first; if the clip edge blocks the cage, step the
        # target DOWN to +0.120 (clear of the clip, over the void). Report the actual Y + the conservatism direction.
        y_lift, L_cage, bx_l, bz_l = None, None, None, None
        for _yt in (y_seat - 0.015, y_seat - 0.030):
            bxl, byl, bzl = _cable_xz(_yt)
            for k in range(1, 9):
                lzk = z_park + (bzl + z_off_dh - z_park) * k / 8
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, (bxl, _yt, lzk), Rpark,
                                        label=f"DH-F2-L-DESCEND{k}/8", converge_mm=3.0, speed_factor=0.22)
            _close(L_drv)
            for _ in range(40):
                _do_step()
            _lc = _cage(f1L0, f2L0)
            if _lc["held"]:
                y_lift, L_cage, bx_l, bz_l = byl, _lc, bxl, bzl
                break
            _set_gripper_target(control, L_drv, GRIPPER_DRIVER_OPEN_RAD)
            for _ in range(8):
                _do_step()
            state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, Rpark,
                                    label="DH-F2-L-RESET", converge_mm=4.0, speed_factor=0.25)
            for _ in range(20):
                _do_step()
        _f2s = _fidx[0]
        z30_grasped = _z30()
        deltah = []
        if y_lift is not None:
            print(f"  [DH] F2 L caged the adjacent body @Y{y_lift:+.3f} (held=True) z30_grasped={z30_grasped:.1f}mm "
                  f"(grasp-close lift {z30_grasped - z30_seated:+.1f}mm, SEPARATE from the deliberate lift)")
            _cap(f"F2 L caged adjacent body @Y{y_lift:+.3f}")
            ee_z0 = bz_l + z_off_dh
            _prev = 0.0
            for h in (0.003, 0.010, 0.030):
                _nsub = max(2, int(round((h - _prev) / 0.0015)))  # CONTINUOUS gradual lift (~1.5mm substeps)
                z30_h = _z30()
                for k in range(1, _nsub + 1):
                    ee_zk = ee_z0 + _prev + (h - _prev) * k / _nsub
                    state, _ = ik_move_both(model, state, scene_info, solver, contacts, (bx_l, y_lift, ee_zk), Rpark,
                                            label=f"DH-F2-LIFT-h{h * 1e3:.0f}-{k}", converge_mm=2.5, speed_factor=0.2)
                    z30_h = max(z30_h, _z30())
                for _ in range(30):  # hold at h, keep sampling z30
                    _do_step()
                    z30_h = max(z30_h, _z30())
                delta_total = z30_h - GROOVE_CENTER_Z * 1e3
                delta_lift = z30_h - z30_grasped
                retained = bool(z30_h < LOW_WALL_TOP)
                if retained:
                    _tag = "RETAINED (<820 low-wall)"
                elif z30_h < HIGH_WALL_TOP:
                    _tag = "cleared low-wall, <830 high-wall (marginal)"
                else:
                    _tag = ">830 ESCAPED both walls"
                deltah.append({"h_mm": round(h * 1e3, 1), "z30_max_mm": round(z30_h, 1),
                               "delta_total_mm": round(delta_total, 2), "delta_lift_mm": round(delta_lift, 2),
                               "retained_below_lowwall": retained, "below_highwall": bool(z30_h < HIGH_WALL_TOP)})
                print(f"  [DH] F2 lift h={h * 1e3:.0f}mm -> z30={z30_h:.1f}mm delta_total={delta_total:+.2f}mm "
                      f"delta_lift={delta_lift:+.2f}mm  {_tag}")
                _cap(f"F2 lift h={h * 1e3:.0f}mm: z30={z30_h:.0f}mm d={delta_total:+.1f}mm {'IN' if retained else 'OUT'}")
                _prev = h
            for k in range(1, 7):  # lower the adjacent body back + release -> does body30 re-settle (route-low return)?
                ee_zk = ee_z0 + 0.030 + (0.0 - 0.030) * k / 6
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, (bx_l, y_lift, ee_zk), Rpark,
                                        label=f"DH-F2-LOWER{k}/6", converge_mm=3.0, speed_factor=0.22)
            _set_gripper_target(control, L_drv, GRIPPER_DRIVER_OPEN_RAD)
            for _ in range(60):
                _do_step()
            z30_recovered = _z30()
            _cap(f"F2 lowered+released: z30={z30_recovered:.0f}mm (re-settled?)")
            print(f"  [DH] F2 recovered z30={z30_recovered:.1f}mm (re-settle to ~809 = route-low return holds)")
        else:
            z30_recovered = _z30()
            print("  [DH] F2 SKIPPED the lift: L could not cage any adjacent body clear of the clip edge "
                  "(that itself = a reach finding; see F1).")
        _f2e = _fidx[0]

        hook["clip_deltah"] = {
            "seat_body_idx": seat_body, "y_seat": round(y_seat, 4),
            "groove_center_z_mm": round(GROOVE_CENTER_Z * 1e3, 1),
            "low_wall_top_mm": round(LOW_WALL_TOP, 1), "high_wall_top_mm": round(HIGH_WALL_TOP, 1),
            "z30_seated_mm": round(z30_seated, 1),
            "F1_R_reach": {"y_target": round(by9, 4), "held": R_reached,
                           "R_bottom_claw_clip_mm": round(R_claw_clip_mm, 2), "walled": R_walled},
            "z30_after_R_retract_mm": round(z30_after_R, 1),
            "lift_arm": "L", "y_lifted": (round(y_lift, 4) if y_lift is not None else None),
            "z30_grasped_mm": round(z30_grasped, 1), "grasp_close_lift_mm": round(z30_grasped - z30_seated, 2),
            "deltah": deltah, "z30_recovered_mm": round(z30_recovered, 1),
            "PROBE_NOTE": "co-located X-route degenerate for DELIVERY (CC5) but representative for the LOCAL "
                          "lift-coupling; a farther L-grasp UNDER-estimates the seat coupling (conservative); "
                          "body30-SPECIFIC frozen-index z-track (CC4).",
        }

        def _encode_sub(name, f0, f1):  # two NAMED §運用14 sub-videos from the frame sub-ranges
            sub = os.path.join(_frames_dir, f"_sub_{name}")
            os.makedirs(sub, exist_ok=True)
            for _o in glob.glob(os.path.join(sub, "*.png")):
                os.remove(_o)
            j = 0
            for i in range(f0, f1):
                src = os.path.join(_frames_dir, f"f{i:05d}.png")
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(sub, f"f{j:05d}.png"))
                    j += 1
            if j == 0:
                return
            out = os.path.join(output_dir or ".", f"{name}.mp4")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "1.5", "-i",
                            os.path.join(sub, "f%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-pix_fmt", "yuv420p", out], check=False)
            try:
                shutil.copy(out, os.path.expanduser(f"~/Downloads/{name}.mp4"))
            except Exception:  # noqa: BLE001
                pass
            print(f"  [DH] §運用14 video {name}.mp4 ({j} frames) -> {out} + ~/Downloads/{name}.mp4")

        if record_video:
            _encode_sub("clip_regrasp_reach", _f1s, _f1e)
            _encode_sub("clip_delta_h_routelow", _f2s, _f2e)
        _summ = " | ".join("h{:.0f}:{:.0f}({:+.1f},{})".format(
            r["h_mm"], r["z30_max_mm"], r["delta_total_mm"], "IN" if r["retained_below_lowwall"] else "OUT")
            for r in deltah)
        print(f"  [DH] VERDICT body30-track: seated {z30_seated:.0f} -> {_summ} -> recovered {z30_recovered:.0f}.  "
              f"F1 R-wall={R_walled} -> %3/%0 GT cross-PV")

    # --- DIRECTION-B DUAL-ARM TAIL-HOLD RETENTION PROBE (env-gate S13_TAIL_HOLD=1; %3 Rs B-validation 2026-06-30) ---
    # Q: does holding the cable on the TAIL side of the seat (one arm, frozen-CLOSED) retain the seated body30 against
    #    the adjacent-BELOW re-grasp coupling (the other arm), keeping the seat below the clip's low wall (820mm)?
    #   HOLDER     = R (higher-Y arm): grip body32 @ Y_seat+0.030 (=+0.180; clip-clear, clip Y top edge +0.165),
    #                frozen-CLOSED at body32's SEATED height -- it must HOLD (NOT lift) the tail.
    #   RE-GRASPER = L (lower-Y arm):  close on body28 @ Y_seat-0.030 (=+0.120; clip-clear, clip Y bot edge +0.135),
    #                then lift h in {0(grasp-close),3,10}mm (the adjacent-below coupling that drags the seat up).
    # A/B via S13_HOLD: 0=OFF (R parked OPEN, no hold; reproduces the ~1:1 CLIP_DELTAH F2 coupling) / 1=ON (R tail-hold).
    # INVARIANT-SAFE: span |0.180-0.120|=60mm <= REGRASP_SPAN_MAX 88mm (#2); NO cross-over (R@0.180 > L@0.120); both
    # over the table-void Y[0.090,0.210] (cage-able); both NATURAL regions (R~0.194 / L~0.106); PIN=0 natural drop-in
    # seat (#5); DiffIK arms via ik_move_both (#3); コ untouched (#4); a diagnostic lift = a retention MEASUREMENT,
    # not a single-arm pipeline (#1). CC5 PROXY: the co-located X-route is degenerate for DELIVERY (ZERO Y-drag) but
    # representative for the LOCAL lift-coupling (same seg chain + the real clip walls). HONESTY: rigid cable -> the
    # tail @ body32 is 1 seg PAST the seat (body31@0.165 is clip-walled) -> EXPECT PARTIAL retention (rigid interp:
    # z30 ~ midpoint of held-body32 & lifted-body28 -> roughly HALF the lift). MEASURE the actual reduction; do NOT
    # assume full. CPU grip-strength + penetration NON-conservative x3 vs GPU; the retention MECHANISM (pinning the
    # tail caps the rigid lift) is GEOMETRIC -> should transfer; grip-strength is the soft part.
    if os.environ.get("S13_TAIL_HOLD", "0") == "1" and hook.get("seated_809") and _clip_collidable:
        HOLD_ON = os.environ.get("S13_HOLD", "1") == "1"
        L_drv, R_drv = [6, 10], [20, 24]                       # per-arm gripper drivers (test:1344-1345)
        z_off_b = z_grasp - (TABLE_HEIGHT + CABLE_RADIUS)      # EE-above-cable offset (route grasp calibration)
        y_seat = y_clip
        # WINDOW SWEEP (Q1): the anchor (R tail-hold) distance PAST the seat. Rs's physics: close anchor -> short
        # taut clip<->anchor span -> コ stiffens -> high クリップ-load -> しごき impeded; far anchor -> span たわむ ->
        # low クリップ-load -> しごき OK BUT retention weakens. Sweep .030/.045/.060 = body32/33/34 @ +0.180/.195/.210.
        ANCHOR_DY = float(os.environ.get("S13_ANCHOR_DY", "0.030"))
        y_tail = y_seat + ANCHOR_DY                                  # swept anchor lane (clip Y top edge +0.165)
        # S13_FEED (option-1 REAL しごき feed, %3 Rs 2026-06-30): REPLACE the L vertical-LIFT disturbance with
        # an AXIAL -Y STROKE that pulls the cable THROUGH the seated clip (the real feed) while R retains +Y.
        # Banked choreography = R-anchor(+Y, frozen-CLOSED)/L-mover(-Y) (r_s71_midair_clamp, handoff:36); the
        # feed is L stroking -Y = the Y-MIRROR of the task's generic "+Y feed" wording, physically identical by
        # the clip's Y-symmetry. Measures feed achieved/commanded + z30 retention + クリップ-load DURING feed
        # (vs the 12.4N re-grasp-LIFT proxy). 88mm span: R@+ANCHOR_DY(30) + L_feed@-FEED_DY(25) stroke 30 ->
        # |0.030-(-0.055)|=85mm <= 88 (#2). FEED_DY 25mm = 10mm clear of the clip Y-edge (±15mm) over the void.
        S13_FEED = os.environ.get("S13_FEED", "0") == "1"
        FEED_DY = float(os.environ.get("S13_FEED_DY", "0.025"))      # feed-grip start lane below the seat (-Y)
        FEED_STROKES = [float(s) for s in os.environ.get("S13_FEED_STROKES", "0.015,0.030").split(",")]
        # しごき slide-vs-drag (option-1 CORRECTED 2026-06-30): the GUIDE/FEED hand (L) HALF-CLAMPS (cradle) so
        # the cable SLIDES THROUGH the コ as the hand strokes -Y (the seated C1 stays put). S13_FEED_GRIP=half
        # (DEFAULT, corrected mechanism) ramps the L driver to a CRADLE value (does NOT axially grip); =full
        # reproduces the PRIOR misframed test (_close_b FULL close -> rigid drag). FEED_DRV = the half-clamp
        # driver (spec GRIPPER_DRIVER_HALF_OPEN_RAD=0.69 -> free-air pad gap ~10mm vs Ø8; sweepable looser to
        # lighten the cradle). ⚠ 0.69 grips ~66.6N CLOSED/arm (task_config:306) -> at mu=1.0 the axial friction
        # could DRAG even the cradle: MEASURE normal force + effective claw mu, SWEEP CABLE_MU/CLIP_MU (1.0 & 0.4).
        FEED_GRIP = os.environ.get("S13_FEED_GRIP", "half")
        FEED_DRV = float(os.environ.get("S13_FEED_DRV", str(GRIPPER_DRIVER_HALF_OPEN_RAD)))
        # ⚠ the cable<->CLAW contact mu is PAD-PRIORITY-pinned at ~0.70 (pad geom_priority=1 wins over the cable's
        # 1.0; newton_skill_env_base:1429) -> CABLE_MU/CLIP_MU do NOT lower the slide-governing claw friction (they
        # only lower cable<->clip grazing). FEED_PAD_MU overrides the L claw slide friction directly = the real
        # mu-sweep lever for "is the DRAG a high-(normal x mu) artifact?" (OPS-SUP cross-PV pt 1). Empty = no override.
        FEED_PAD_MU = os.environ.get("FEED_PAD_MU", "")

        def _gap_mm_from_drv(q):  # free-air pad gap [mm] estimate (linear e-curve anchors (0,85.394)&(0.7239,6.0))
            return 85.394 - 109.68 * q
        TILT_ON = os.environ.get("S13_TILT", "0") == "1"            # FIDELITY (Q2): L re-grasp TILT-FOLLOWS cable pitch
        TILT_SIGN = float(os.environ.get("S13_TILT_SIGN", "1"))     # (r_s71 _63/_65 port; +1 default)
        BASE_RX = -_math.pi / 2                                     # solve_ik_dual default EE rot = Rx(-90deg) (test:1730)
        LOW_WALL_TOP = (CLIP1_Z + 0.020) * 1e3                # 820mm low-wall top (cable-center criterion)
        RADCORR_TOP = LOW_WALL_TOP + CABLE_RADIUS * 1e3       # 824mm radius-corrected (cable BOTTOM clears 820 wall)
        HIGH_WALL_TOP = (CLIP1_Z + 0.030) * 1e3              # 830mm high-wall / V-guide top
        _clipg_b = _clip_geoms()

        def _do_step_b():
            nonlocal state
            state = physics_step(model, state, solver, contacts, scene_info)

        # body30-SPECIFIC z-track (CC4): FREEZE the seat body index ONCE, read body_q[seat_body,2] DIRECTLY (NOT
        # _seg_z_mm window-mean, NOT _min_dist_mm min-over-all) -- the SSOT seat metric.
        wp.synchronize()
        _cb_y = state.body_q.numpy()[cable_bodies, 1]
        _seat_k = int(np.argmin(np.abs(_cb_y - y_seat)))
        seat_body = int(cable_bodies[_seat_k])

        def _z30_b():
            wp.synchronize()
            return float(state.body_q.numpy()[seat_body, 2]) * 1e3  # mm — the FROZEN seat body, every call

        def _cable_xz_b(y_t):
            wp.synchronize()
            cb = state.body_q.numpy()[cable_bodies]
            i = int(np.argmin(np.abs(cb[:, 1] - y_t)))
            return float(cb[i, 0]), float(cb[i, 1]), float(cb[i, 2])

        def _close_b(drv):  # proven 2-phase コ cage close (capture-then-gentle), per-arm
            cr = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * 0.9
            _set_gripper_target(control, drv, cr)
            for _ in range(30):
                _do_step_b()
            for ck in range(1, 13):
                _set_gripper_target(control, drv, cr + (GRIPPER_DRIVER_CLOSE_RAD - cr) * ck / 12)
                for _ in range(12):
                    _do_step_b()

        def _halfclamp_b(drv, target):  # しごき CRADLE: ramp open->`target` (a HALF-clamp, NOT full close) so the
            # claws cradle the cable laterally but leave it AXIALLY free to slide. COARSE open->(target-0.06) then
            # FINE 0.005 steps to `target`, LOGGING the claw<->cable gap + NORMAL at each FINE step = the cradle-
            # CALIBRATION curve (the cradle = drv where the claws just touch Ø8: gap~0 + low force; deeper = grip).
            _curve = []
            _coarse = max(GRIPPER_DRIVER_OPEN_RAD, target - 0.06)
            for ck in range(1, 9):
                _set_gripper_target(control, drv, GRIPPER_DRIVER_OPEN_RAD + (_coarse - GRIPPER_DRIVER_OPEN_RAD) * ck / 8)
                for _ in range(10):
                    _do_step_b()
            _q = _coarse
            while _q <= target + 1e-6:
                _set_gripper_target(control, drv, _q)
                for _ in range(14):
                    _do_step_b()
                _g = _min_dist_mm(f1L0 + f2L0, cable_geoms) if cable_geoms else 9e9
                _n, _pk, _ncn, _mu = _feed_claw_cable_load_N(f1L0 + f2L0)
                _curve.append({"drv": round(_q, 4), "padgap_mm": round(_gap_mm_from_drv(_q), 2),
                               "claw_cable_gap_mm": round(_g, 3), "normal_N": round(_n, 2)})
                print(f"  [FEED-RAMP] drv={_q:.4f} (pad~{_gap_mm_from_drv(_q):.1f}mm) claw<->cable gap={_g:+.3f}mm "
                      f"NORMAL={_n:.2f}N peak={_pk:.2f} (mu={_mu})")
                _q += 0.005
            _set_gripper_target(control, drv, target)
            for _ in range(40):
                _do_step_b()
            hook["feed_ramp_curve"] = _curve

        def _feed_claw_cable_load_N(claw_set):  # (feed-claw <-> cable) NORMAL force + effective mu = cradle-vs-grip
            # discriminator. low N (few) = cradle (light lateral contact, low axial friction -> SLIDES); high N
            # (tens) = grip (high axial friction -> DRAGS). axial-friction ceiling ~= mu * normal. Paired with
            # claw<->cable mj_geomDistance (solver-independent gap). mu = the contact's tangential coefficient.
            mujoco.mj_forward(mjm, mjd)
            _cs, _cab = set(claw_set), set(cable_geoms)
            tot, peak, n, mu_eff = 0.0, 0.0, 0, None
            f6 = np.zeros(6, dtype=np.float64)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _cab) or (int(c.geom2) in _cs and int(c.geom1) in _cab):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    fn = abs(float(f6[0]))
                    tot += fn
                    peak = max(peak, fn)
                    n += 1
                    if mu_eff is None:
                        mu_eff = float(c.friction[0])
            return tot, peak, n, mu_eff

        # --- クリップ-load (Rs's コ-friction proxy) + たわみ (clip<->anchor span sag) + tilt-follow (r_s71 port) ---
        _clipset = set(_clipg_b)

        def _clip_load_N():
            # sum |normal force| over clip-involving contacts = Rs's コ-friction proxy (higher normal -> more しごき
            # friction). mj_forward populates mjd.contact + efc_force for the CURRENT settled qpos; mj_contactForce
            # returns the 6D wrench in the contact frame ([0]=normal). CPU-non-conservative on absolute magnitude;
            # the cross-anchor TREND is the robust part (paired with _min_dist_mm penetration as a solver-indep check).
            mujoco.mj_forward(mjm, mjd)
            tot, peak, n = 0.0, 0.0, 0
            f6 = np.zeros(6, dtype=np.float64)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if int(c.geom1) in _clipset or int(c.geom2) in _clipset:
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    fn = abs(float(f6[0]))
                    tot += fn
                    peak = max(peak, fn)
                    n += 1
            return tot, peak, n

        def _span_sag_mm(y_lo, y_hi):
            # たわみ: max DOWNWARD deflection of the cable below the chord between the span endpoints, over the
            # clip<->anchor Y-span. Rs: close anchor -> short taut span -> low たわみ -> rigid load to the clip;
            # far anchor -> long span -> more たわみ -> the slack absorbs load -> lower クリップ-load.
            wp.synchronize()
            cb = state.body_q.numpy()[cable_bodies]
            m = (cb[:, 1] >= y_lo) & (cb[:, 1] <= y_hi)
            if int(m.sum()) < 3:
                return None
            seg = cb[m]
            seg = seg[np.argsort(seg[:, 1])]
            y0, z0, y1, z1 = seg[0, 1], seg[0, 2], seg[-1, 1], seg[-1, 2]
            chord = z0 + (z1 - z0) * (seg[:, 1] - y0) / (y1 - y0 + 1e-9)
            return float(np.max(chord - seg[:, 2])) * 1e3

        def _load_sample(with_sag):
            cn, cp, ncc = _clip_load_N()
            pen = _min_dist_mm(_clipg_b, cable_geoms) if (cable_geoms and _clipg_b) else 9e9
            sag = _span_sag_mm(y_seat, y_tail) if (with_sag and HOLD_ON) else None  # seat->anchor span (>=3 bodies)
            return {"clip_N": round(cn, 3), "clip_peak_N": round(cp, 3), "clip_ncon": ncc,
                    "clip_pen_mm": round(pen, 3), "span_sag_mm": (round(sag, 2) if sag is not None else None)}

        # tilt-follow (Q2 FIDELITY, r_s71_midair_clamp port): the L re-grasp EE rotation FOLLOWS the cable's local
        # Y-Z pitch so the claws ALIGN with the locally-tilted cable (a square-on re-clamp squirts it out). Monkeypatch
        # solve_ik_dual (ik_move_both calls it as a module global) with PER-ARM rot targets; R keeps default (anchor).
        _ROT = {}

        def _rot_quat_rx(angle):  # X-rotation target in solve_ik_dual's XYZW convention (w LAST)
            return wp.array([wp.vec4(_math.sin(angle / 2), 0.0, 0.0, _math.cos(angle / 2))], dtype=wp.vec4, device=DEVICE)

        def _cable_local_pitch(y_t):  # cable local Y-Z pitch theta [rad] at lane y_t (tangent of adjacent segments)
            wp.synchronize()
            cbs = state.body_q.numpy()[cable_bodies]
            cbs = cbs[np.argsort(cbs[:, 1])]
            ys = cbs[:, 1]
            j = int(np.argmin(np.abs(ys - y_t)))
            a, b = max(j - 1, 0), min(j + 1, len(ys) - 1)
            dY, dZ = float(ys[b] - ys[a]), float(cbs[b, 2] - cbs[a, 2])
            return _math.atan2(dZ, dY) if abs(dY) > 1e-9 else 0.0

        def _solve_ik_dual_rot(scene_info_, target_left, target_right, warmstart_jq=None):
            # Faithful copy of solve_ik_dual (test:1693-1781) but with PER-ARM rotation targets _ROT['L']/_ROT['R'].
            fk_model_ = scene_info_["fk_model"]
            fk_state_ = scene_info_["fk_state"]
            le, re = EE_BODY_OFFSET, FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ol = IKObjectivePosition(link_index=le, link_offset=wp.vec3(0.0, 0.0, 0.0),
                                     target_positions=wp.array(np.array([target_left], dtype=np.float32),
                                                               dtype=wp.vec3, device=DEVICE), weight=1.0)
            orr = IKObjectivePosition(link_index=re, link_offset=wp.vec3(0.0, 0.0, 0.0),
                                      target_positions=wp.array(np.array([target_right], dtype=np.float32),
                                                                dtype=wp.vec3, device=DEVICE), weight=1.0)
            rl = IKObjectiveRotation(link_index=le, link_offset_rotation=wp.quat_identity(),
                                     target_rotations=_ROT["L"], weight=0.5)
            rr = IKObjectiveRotation(link_index=re, link_offset_rotation=wp.quat_identity(),
                                     target_rotations=_ROT["R"], weight=0.5)
            jl = IKObjectiveJointLimit(joint_limit_lower=fk_model_.joint_limit_lower,
                                       joint_limit_upper=fk_model_.joint_limit_upper, weight=10.0)
            from newton_routing_utils import _build_collision_objectives
            cobjs = _build_collision_objectives() if os.environ.get("COLLISION_AVOIDANCE", "1") != "0" else []
            iks = IKSolver(fk_model_, n_problems=1, objectives=[ol, orr, rl, rr, *cobjs, jl])
            fj = fk_state_.joint_q.numpy().copy()
            if warmstart_jq is not None:
                fj = np.asarray(warmstart_jq, dtype=fj.dtype).reshape(-1).copy()
            qin = wp.array(fj.reshape(1, -1), dtype=float, device=DEVICE)
            qout = wp.zeros((1, fk_model_.joint_coord_count), dtype=float, device=DEVICE)
            iks.step(qin, qout, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
            return qout.numpy()[0], float(iks.costs.numpy()[0])

        _set_gripper_target(control, L_drv + R_drv, GRIPPER_DRIVER_OPEN_RAD)  # both open post-seat
        for _ in range(20):
            _do_step_b()
        z30_seated = _z30_b()
        bx_s, _, bz_s = _cable_xz_b(y_seat)
        z_park = bz_s + z_off_b + 0.12
        Lpark = (bx_s, GRASP_YC - GHS, z_park)
        Rpark = (bx_s, GRASP_YC + GHS, z_park)
        # FREEZE the per-arm claw-geom partition ONCE at the symmetric straddle pose (names carry pad-not-arm id ->
        # _arm_split by world-Y is the only split; freeze the geom-ids here so later asymmetric moves can't mis-class).
        state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, Rpark,
                                label="B-STRADDLE", converge_mm=4.0, speed_factor=0.25)
        for _ in range(20):
            _do_step_b()
        f1L0, f1R0, f2L0, f2R0 = _arm_split()  # f1R0/f2R0 = R-arm claws (FROZEN); f1L0/f2L0 = L-arm
        _b_f0 = _fidx[0]
        print(f"  [B] mode={'ON (R tail-hold)' if HOLD_ON else 'OFF (baseline, no hold)'} seat_body=idx{seat_body} "
              f"(cable[{_seat_k}] Y{_cb_y[_seat_k]:+.3f}) z30_seated={z30_seated:.1f}mm "
              f"(groove 809 / low-wall {LOW_WALL_TOP:.0f} / radcorr {RADCORR_TOP:.0f} / high-wall {HIGH_WALL_TOP:.0f})")
        _seat_load = _load_sample(False)  # クリップ-load at the undisturbed seat (anchor-indep baseline + contact-force sanity)
        print(f"  [B] seated クリップ-load: clip_normal={_seat_load['clip_N']:.3f}N (peak {_seat_load['clip_peak_N']:.3f}N "
              f"ncon {_seat_load['clip_ncon']}) clip<->cable_pen={_seat_load['clip_pen_mm']:+.3f}mm "
              f"(ANCHOR_DY={ANCHOR_DY * 1e3:.0f}mm y_tail={y_tail:+.3f} TILT={int(TILT_ON)})")
        # S13_FEED tilt-baseline (cross-PV B): seat along-Y pitch BEFORE any clamp engages (claws parked OPEN at
        # the straddle pose). Discriminator: tilt already present here = REAL C1-over-void concern (transfers);
        # tilt only AFTER clamp + claw<->clip<=0 = proxy ARTIFACT (clamp+clip co-location, not the real pipeline).
        _seat_pitch_pre = _math.degrees(_cable_local_pitch(y_seat)) if S13_FEED else 0.0
        if S13_FEED:
            print(f"  [FEED] tilt-baseline PRE-clamp (over-void seat, claws parked OPEN): "
                  f"seat_pitch={_seat_pitch_pre:+.2f}deg frame={_b_f0}")

        # ===== HOLDER (R, higher-Y): grip body{32,33,34} @ Y_seat+ANCHOR_DY frozen-CLOSED at SEATED height (ON only) =====
        # y_tail already set above (= y_seat + ANCHOR_DY); the swept anchor lane, clip-clear (clip Y top edge +0.165).
        R_hold = None
        R_reach_resid_mm = None
        z30_after_hold = z30_seated
        z30_close = z30_seated
        pin_steps = 0
        _hold_load = None
        if HOLD_ON:
            PIN_SEATED = os.environ.get("S13_PIN_SEATED", "1") == "1"
            bxt, byt, bzt = _cable_xz_b(y_tail)
            R_desc = (bxt, y_tail, bzt + z_off_b)                   # cradle-at-rest descent target
            for k in range(1, 9):  # R descends to body32 (L parks clear) -- order vs L is irrelevant here
                rzk = z_park + (bzt + z_off_b - z_park) * k / 8
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, (bxt, y_tail, rzk),
                                        label=f"B-R-HOLD-DESCEND{k}/8", converge_mm=3.0, speed_factor=0.22)
            _pl, _pr = get_ee_positions(state, scene_info)
            R_reach_resid_mm = float(np.linalg.norm(np.array(_pr) - np.array(R_desc))) * 1e3
            _close_b(R_drv)
            for _ in range(60):
                _do_step_b()
            z30_close = _z30_b()
            # PIN-AT-SEATED (task intent "hold at the SEATED height, NOT lift it"): the 2-phase cage-close lifts the
            # caged body ~+11-13mm (the documented grasp-close coupling) -> body32 + the rigid seat rise. Feedback-
            # LOWER the (closed) holder via DiffIK until the seat returns to ~seated, so the holder PINS the tail at
            # ~809 (NOT a teleport; the claw stays closed and is lowered by IK). If z30 cannot be brought back, that
            # itself = the holder lifts the seat -> REPORT it (do NOT fake a pin).
            ee_zc = bzt + z_off_b
            if PIN_SEATED:
                for _s in range(14):
                    if _z30_b() <= z30_seated + 2.0:
                        break
                    ee_zc -= 0.0025
                    state, _ = ik_move_both(model, state, scene_info, solver, contacts, Lpark, (bxt, y_tail, ee_zc),
                                            label=f"B-R-PIN{_s}", converge_mm=2.0, speed_factor=0.25)
                    for _ in range(20):
                        _do_step_b()
                    pin_steps += 1
            R_hold = _cage(f1R0, f2R0)
            z30_after_hold = _z30_b()
            _pl3, _pr3 = get_ee_positions(state, scene_info)
            R_hold_target = (float(_pr3[0]), float(_pr3[1]), float(_pr3[2]))  # hold at R's ACHIEVED pose (don't fight it)
            print(f"  [B] R tail-hold body32@Y{byt:+.3f}: held={R_hold['held']} R[f1={R_hold['f1']:+.2f}/"
                  f"f2={R_hold['f2']:+.2f}] reach_resid={R_reach_resid_mm:.2f}mm  z30 close={z30_close:.1f}->"
                  f"pin({pin_steps}x)={z30_after_hold:.1f}mm (target ~{z30_seated:.0f}; "
                  f"holder_net_lift {z30_after_hold - z30_seated:+.1f}mm)")
            _hold_load = _load_sample(True)
            print(f"  [B] post-hold クリップ-load: clip_normal={_hold_load['clip_N']:.3f}N pen={_hold_load['clip_pen_mm']:+.3f}mm "
                  f"span_sag(clip->anchor)={_hold_load['span_sag_mm']}mm (anchor pins the tail; L not yet engaged)")
        else:
            R_hold_target = Rpark   # OFF: R parked OPEN, no hold (R does not disturb the seat)
        _cap(f"B {'ON R-tail-hold' if HOLD_ON else 'OFF baseline'}: z30={z30_after_hold:.0f}mm pre-regrasp")

        # ===== RE-GRASPER / FEED-HAND (L, lower-Y): close then EITHER lift h in {0,3,10}mm (vertical proxy) OR
        # axial -Y stroke (S13_FEED = real しごき feed); track z30 =====
        y_re = y_seat - (FEED_DY if S13_FEED else 0.030)   # feed/re-grasp lane, clip-clear, over the void
        bxl, byl, bzl = _cable_xz_b(y_re)
        _ik_orig = None
        theta_L = 0.0
        if TILT_ON:  # Q2 FIDELITY: measure cable pitch at the L lane, tilt the L EE to follow it (R stays anchor-default)
            theta_L = _cable_local_pitch(y_re)
            _ROT["L"] = _rot_quat_rx(BASE_RX + TILT_SIGN * theta_L)
            _ROT["R"] = _rot_quat_rx(BASE_RX)
            _ik_orig = globals()["solve_ik_dual"]
            globals()["solve_ik_dual"] = _solve_ik_dual_rot  # ik_move_both resolves solve_ik_dual as a module global
            print(f"  [B] TILT-FOLLOW theta={_math.degrees(theta_L):+.1f}deg (sign {TILT_SIGN:+.0f}) -> "
                  f"L EE Rx({_math.degrees(BASE_RX + TILT_SIGN * theta_L):.1f}deg); R default (anchor)")
        for k in range(1, 9):  # L descends to body28; R holds (ON) or stays parked (OFF)
            lzk = z_park + (bzl + z_off_b - z_park) * k / 8
            state, _ = ik_move_both(model, state, scene_info, solver, contacts, (bxl, y_re, lzk), R_hold_target,
                                    label=f"B-L-DESCEND{k}/8", converge_mm=3.0, speed_factor=0.22)
        _pl2, _pr2 = get_ee_positions(state, scene_info)
        L_reach_resid_mm = float(np.linalg.norm(np.array(_pl2) - np.array((bxl, y_re, bzl + z_off_b)))) * 1e3
        if S13_FEED and FEED_GRIP == "half":
            _halfclamp_b(L_drv, FEED_DRV)   # CORRECTED しごき cradle (slides), NOT a full grip (drags)
        else:
            _close_b(L_drv)                 # full-grip contrast (prior misframed option-1) OR non-FEED B re-grasp
        for _ in range(40):
            _do_step_b()
        L_cage = _cage(f1L0, f2L0)
        z30_grasped = _z30_b()
        print(f"  [B] L re-grasp body28@Y{byl:+.3f}: held={L_cage['held']} L[f1={L_cage['f1']:+.2f}/"
              f"f2={L_cage['f2']:+.2f}] reach_resid={L_reach_resid_mm:.2f}mm  z30_grasp_close={z30_grasped:.1f}mm "
              f"(grasp-close lift {z30_grasped - z30_seated:+.1f}mm vs seated)")
        # CRADLE EVIDENCE (option-1 corrected): is the L guide-hand a CRADLE (lateral contact, axial-free -> slide)
        # or a GRIP (drag) or EMPTY-AIR (artifact, cable untouched)? Report driver + pad-gap + claw<->cable gap +
        # NORMAL force + effective mu + axial-friction ceiling. _is_cradle/_is_air consumed by the feed validity.
        _is_cradle, _is_air = False, False
        if S13_FEED:
            _fcl_tot, _fcl_peak, _fcl_n, _fcl_mu = _feed_claw_cable_load_N(f1L0 + f2L0)
            _fcc_gap = _min_dist_mm(f1L0 + f2L0, cable_geoms) if cable_geoms else 9e9
            _axial_ceil = (_fcl_mu * _fcl_tot) if _fcl_mu is not None else float("nan")
            _grip_label = (("HALF-CLAMP/cradle drv=%.3f (~%.1fmm pad gap vs Ø8)" % (FEED_DRV, _gap_mm_from_drv(FEED_DRV)))
                           if FEED_GRIP == "half" else ("FULL-GRIP drv=%.3f (contrast = prior misframed)" % GRIPPER_DRIVER_CLOSE_RAD))
            _is_cradle = bool(FEED_GRIP == "half" and -2.0 <= _fcc_gap <= 2.5 and 0.1 < _fcl_tot < 60.0)
            _is_air = bool(_fcc_gap > 2.5 and _fcl_tot < 0.1)
            _cmode = ("CRADLE (lateral contact, axial-free)" if _is_cradle
                      else ("EMPTY-AIR ARTIFACT (cable untouched)" if _is_air else "GRIP/other"))
            print(f"  [FEED] L guide-hand grip = {_grip_label}")
            print(f"  [FEED] cradle-check: claw<->cable gap={_fcc_gap:+.3f}mm NORMAL={_fcl_tot:.2f}N (peak {_fcl_peak:.2f}, "
                  f"n={_fcl_n}) eff_mu={_fcl_mu} axial-fric-ceil~={_axial_ceil:.2f}N sandwiched={L_cage['sandwiched']} "
                  f"held={L_cage['held']} -> {_cmode}")
            hook["feed_cradle"] = {"feed_grip": FEED_GRIP, "feed_drv": round(FEED_DRV, 4),
                                   "padgap_est_mm": round(_gap_mm_from_drv(FEED_DRV), 2),
                                   "claw_cable_gap_mm": round(_fcc_gap, 3), "claw_cable_normal_N": round(_fcl_tot, 3),
                                   "claw_cable_peak_N": round(_fcl_peak, 3), "claw_cable_eff_mu": _fcl_mu,
                                   "axial_friction_ceiling_N": (round(_axial_ceil, 3) if _fcl_mu is not None else None),
                                   "sandwiched": L_cage["sandwiched"], "held": L_cage["held"],
                                   "is_cradle": _is_cradle, "is_empty_air": _is_air}
        _cap(f"B {'ON' if HOLD_ON else 'OFF'} L re-grasp closed: z30={z30_grasped:.0f}mm (h=0)")

        ee_z0 = bzl + z_off_b
        _h0_load = _load_sample(True)
        print(f"  [B] h0 クリップ-load: clip_normal={_h0_load['clip_N']:.3f}N pen={_h0_load['clip_pen_mm']:+.3f}mm "
              f"span_sag={_h0_load['span_sag_mm']}mm")
        sweep = [{"h_mm": 0.0, "z30_max_mm": round(z30_grasped, 1),
                  "delta_seated_mm": round(z30_grasped - z30_seated, 2),
                  "retained_lowwall": bool(z30_grasped < LOW_WALL_TOP),
                  "retained_radcorr": bool(z30_grasped < RADCORR_TOP),
                  "below_highwall": bool(z30_grasped < HIGH_WALL_TOP), **_h0_load}]
        _prev = 0.0
        for h in (() if S13_FEED else (0.003, 0.010)):   # S13_FEED: skip the vertical lift; the axial feed runs below
            _nsub = max(2, int(round((h - _prev) / 0.0015)))  # CONTINUOUS gradual lift (~1.5mm substeps)
            z30_h = _z30_b()
            for k in range(1, _nsub + 1):
                ee_zk = ee_z0 + _prev + (h - _prev) * k / _nsub
                state, _ = ik_move_both(model, state, scene_info, solver, contacts, (bxl, y_re, ee_zk), R_hold_target,
                                        label=f"B-LIFT-h{h * 1e3:.0f}-{k}", converge_mm=2.5, speed_factor=0.2)
                z30_h = max(z30_h, _z30_b())
            for _ in range(30):  # hold at h, keep sampling z30
                _do_step_b()
                z30_h = max(z30_h, _z30_b())
            retained_low = bool(z30_h < LOW_WALL_TOP)
            retained_rad = bool(z30_h < RADCORR_TOP)
            if retained_low:
                _tag = "RETAINED (<820 low-wall)"
            elif retained_rad:
                _tag = "center>820 but bottom<820 (<824 radcorr, marginal-IN)"
            elif z30_h < HIGH_WALL_TOP:
                _tag = "cleared low-wall, <830 high-wall"
            else:
                _tag = ">830 ESCAPED both walls"
            _hl = _load_sample(True)
            sweep.append({"h_mm": round(h * 1e3, 1), "z30_max_mm": round(z30_h, 1),
                          "delta_seated_mm": round(z30_h - z30_seated, 2),
                          "retained_lowwall": retained_low, "retained_radcorr": retained_rad,
                          "below_highwall": bool(z30_h < HIGH_WALL_TOP), **_hl})
            print(f"  [B] L lift h={h * 1e3:.0f}mm -> z30={z30_h:.1f}mm (delta_seated={z30_h - z30_seated:+.2f}mm)  {_tag}")
            print(f"  [B] h{h * 1e3:.0f} クリップ-load: clip_normal={_hl['clip_N']:.3f}N pen={_hl['clip_pen_mm']:+.3f}mm "
                  f"span_sag={_hl['span_sag_mm']}mm")
            _cap(f"B {'ON' if HOLD_ON else 'OFF'} L lift h={h * 1e3:.0f}mm: z30={z30_h:.0f}mm "
                 f"{'IN' if retained_low else ('IN*' if retained_rad else 'OUT')}")
            _prev = h
        if S13_FEED:
            # ===== AXIAL しごき FEED (option-1, %3 Rs 2026-06-30): L strokes -Y, pulling cable THROUGH the seated
            # clip while R retains +Y. Replaces the vertical-lift proxy. Measures (i) feed PROCEEDS? (cable body
            # achieved -Y vs commanded stroke + does the clip-nearest body change = cable slid through), (ii) C1
            # RETAINED (frozen-z30 < 820), (iii) クリップ-load DURING the actual feed. =====
            R_held_ok = bool(HOLD_ON and (R_hold is not None) and R_hold["held"])
            R_ok = bool(R_held_ok if HOLD_ON else True)            # R-OFF is INTENTIONAL (reframe: is a B hand needed?)
            # L validity is grip-mode dependent: full-grip = geometric cage held; HALF-clamp = a CRADLE (lateral
            # contact present, NOT empty-air, NOT crush) so the cable can slide (held=sandwiched is NOT required).
            L_held_ok = bool(_is_cradle) if (FEED_GRIP == "half") else bool(L_cage["held"])
            feed_valid = bool(R_ok and L_held_ok)
            mujoco.mj_forward(mjm, mjd)                            # friction READBACK (cross-PV A)
            _cabset = set(cable_geoms)
            _clip_g_mu = float(mjm.geom_friction[_clipg_b[0]][0]) if _clipg_b else float("nan")
            _cab_g_mu = float(mjm.geom_friction[cable_geoms[0]][0]) if cable_geoms else float("nan")
            _pair_mu = None
            for ci in range(int(mjd.ncon)):
                _c = mjd.contact[ci]
                if (int(_c.geom1) in _clipset and int(_c.geom2) in _cabset) or \
                   (int(_c.geom2) in _clipset and int(_c.geom1) in _cabset):
                    _pair_mu = round(float(_c.friction[0]), 3)
                    break
            print(f"  [FEED] friction readback: clip_geom_mu={_clip_g_mu:.3f} cable_geom_mu={_cab_g_mu:.3f} -> "
                  f"effective cable<->clip contact_mu={_pair_mu} (intended CLIP_MU={os.environ.get('CLIP_MU', '1.0')} "
                  f"CABLE_MU={os.environ.get('CABLE_MU', str(CABLE_CONTACT_MU))})")
            if FEED_PAD_MU != "":   # OPS-SUP mu-sweep lever: override the L claw slide friction (pad-priority pins it)
                _pm = float(FEED_PAD_MU)
                _claws_L = f1L0 + f2L0
                for _g in _claws_L:
                    mjm.geom_friction[_g][0] = _pm
                mujoco.mj_forward(mjm, mjd)
                _cl_mu_after = float(mjm.geom_friction[_claws_L[0]][0]) if _claws_L else float("nan")
                print(f"  [FEED] FEED_PAD_MU override: L claw slide friction -> {_pm} on {len(_claws_L)} geoms "
                      f"(readback {_cl_mu_after:.3f}); the cable<->claw contact mu now follows this (slide lever)")
            _claw_clip_h0 = _min_dist_mm(f1L0 + f2L0 + f1R0 + f2R0, _clipg_b) if _clipg_b else 9e9
            _seat_pitch_h0 = _math.degrees(_cable_local_pitch(y_seat))
            print(f"  [FEED] PRE-FEED artifact: held[R={R_held_ok} L={L_held_ok}] valid={feed_valid} | "
                  f"claw<->clip={_claw_clip_h0:+.3f}mm (MUST>0) seat_pitch={_seat_pitch_h0:+.2f}deg "
                  f"(pre-clamp {_seat_pitch_pre:+.2f}deg) clip<->cable_pen={_h0_load['clip_pen_mm']:+.3f}mm")
            wp.synchronize()
            _cyf0 = state.body_q.numpy()[cable_bodies, 1]
            feed_k = int(np.argmin(np.abs(_cyf0 - y_re)))
            feed_body = int(cable_bodies[feed_k])
            feed_body_y0 = float(_cyf0[feed_k])
            seat_body_y0 = float(_cyf0[_seat_k])
            ee_y_start = float(get_ee_positions(state, scene_info)[0][1])   # L EE Y at feed start

            def _clip_nearest_b():   # cable body currently nearest the clip Y (= the body "in the clip")
                wp.synchronize()
                _cy = state.body_q.numpy()[cable_bodies, 1]
                _k = int(np.argmin(np.abs(_cy - y_clip)))
                return int(cable_bodies[_k]), float(_cy[_k])

            cn_b0, cn_y0 = _clip_nearest_b()
            print(f"  [FEED] start: feed_body=idx{feed_body}(cable[{feed_k}] Y{feed_body_y0:+.4f}) "
                  f"seat_body Y{seat_body_y0:+.4f} clip-nearest=idx{cn_b0}(Y{cn_y0:+.4f}) L_EE_Y{ee_y_start:+.4f}")
            _pre_feed_frame = _fidx[0] - 1 if _fidx[0] > 0 else -1   # last frame before the feed = pre-feed (h0)
            _feed_frame_idx = []                                     # one saved-frame index per stroke (compare PNG)
            _prevf = 0.0
            for stroke in FEED_STROKES:
                _nsub = max(2, int(round((stroke - _prevf) / 0.0015)))
                for k in range(1, _nsub + 1):
                    ee_yk = y_re - (_prevf + (stroke - _prevf) * k / _nsub)   # axial -Y feed stroke (X,Z held)
                    state, _ = ik_move_both(model, state, scene_info, solver, contacts, (bxl, ee_yk, ee_z0),
                                            R_hold_target, label=f"B-FEED-s{stroke * 1e3:.0f}-{k}",
                                            converge_mm=2.5, speed_factor=0.2)
                for _ in range(40):
                    _do_step_b()
                wp.synchronize()
                _cyN = state.body_q.numpy()[cable_bodies, 1]
                ee_y_ach = float(get_ee_positions(state, scene_info)[0][1])
                ee_disp = ee_y_start - ee_y_ach                 # L EE -Y travel achieved
                feed_disp = feed_body_y0 - float(_cyN[feed_k])  # gripped cable body -Y translation achieved
                seat_disp = seat_body_y0 - float(_cyN[_seat_k]) # seat body -Y lateral slide (toward the feed)
                cn_bN, cn_yN = _clip_nearest_b()
                z30_f = _z30_b()
                _fl = _load_sample(True)
                Lh = _cage(f1L0, f2L0)
                Rh = _cage(f1R0, f2R0) if HOLD_ON else {"held": False, "f1": 9.9, "f2": 9.9}
                claw_clip = _min_dist_mm(f1L0 + f2L0 + f1R0 + f2R0, _clipg_b) if _clipg_b else 9e9
                seat_pitch = _math.degrees(_cable_local_pitch(y_seat))
                ret_low = bool(z30_f < LOW_WALL_TOP)
                feed_frac = (feed_disp / stroke) if stroke > 1e-6 else 0.0
                proceeded = bool(feed_frac >= 0.5 and Lh["held"])   # cable advanced >=50% of cmd under a HELD grip
                # slip_ratio = cable_Y-disp(guide pt) / hand_Y-disp: ~0 = cable SLIDES through the cradle (seat
                # STAYS = しごき works) ; ~1 = cable DRAGGED with the hand (dead しごき). The CORRECTED metric.
                slip_ratio = (feed_disp / ee_disp) if abs(ee_disp) > 1e-6 else 0.0
                fclN, fclpk, _fcln, fclmu = _feed_claw_cable_load_N(f1L0 + f2L0)   # cradle contact DURING the slide
                contact_present = bool(fclN > 0.5)                  # conjunction: lateral cradle-contact this stroke
                axial_friction_N = (fclmu * fclN) if fclmu is not None else float("nan")
                slide_ok = bool(slip_ratio < 0.35 and contact_present and ret_low)   # SLIDE = slip~0 AND contact AND C1 in
                _smode = ("SLIDE" if slip_ratio < 0.35 else ("DRAG" if slip_ratio > 0.65 else "PARTIAL"))
                sweep.append({"h_mm": round(stroke * 1e3, 1), "z30_max_mm": round(z30_f, 1),
                              "delta_seated_mm": round(z30_f - z30_seated, 2),
                              "retained_lowwall": ret_low, "retained_radcorr": bool(z30_f < RADCORR_TOP),
                              "below_highwall": bool(z30_f < HIGH_WALL_TOP),
                              "stroke_mm": round(stroke * 1e3, 1), "ee_disp_mm": round(ee_disp * 1e3, 2),
                              "feed_disp_mm": round(feed_disp * 1e3, 2), "feed_frac": round(feed_frac, 3),
                              "slip_ratio": round(slip_ratio, 3), "slide_mode": _smode, "slide_ok": slide_ok,
                              "feed_claw_normal_N": round(fclN, 3), "feed_claw_peak_N": round(fclpk, 3),
                              "feed_claw_eff_mu": fclmu, "axial_friction_N": (round(axial_friction_N, 3) if fclmu is not None else None),
                              "contact_present": contact_present,
                              "seat_slide_mm": round(seat_disp * 1e3, 2), "clip_nearest_idx": cn_bN,
                              "clip_nearest_dY_mm": round((cn_yN - cn_y0) * 1e3, 2),
                              "L_held": bool(Lh["held"]), "R_held": bool(Rh["held"]),
                              "claw_clip_mm": round(claw_clip, 3), "seat_pitch_deg": round(seat_pitch, 2),
                              "proceeded": proceeded, **_fl})
                print(f"  [FEED] stroke={stroke * 1e3:.0f}mm: EE_disp={ee_disp * 1e3:+.1f}mm "
                      f"feed_body_disp={feed_disp * 1e3:+.1f}mm ({feed_frac * 100:.0f}% of cmd) "
                      f"seat_slide={seat_disp * 1e3:+.1f}mm clip-near=idx{cn_bN}(dY{(cn_yN - cn_y0) * 1e3:+.1f}mm) "
                      f"-> {'PROCEEDS' if proceeded else 'IMPEDED'}")
                print(f"  [FEED-SLIDE] stroke={stroke * 1e3:.0f}mm slip_ratio={slip_ratio:.3f} -> {_smode} "
                      f"| claw<->cable NORMAL={fclN:.2f}N (mu={fclmu} axial-fric~={axial_friction_N:.2f}N) "
                      f"contact_present={contact_present} | C1 seat_dz={z30_f - z30_seated:+.2f}mm ({'IN<820' if ret_low else 'OUT'}) "
                      f"claw<->clip={claw_clip:+.3f}mm -> slide_ok={slide_ok}")
                print(f"  [FEED] stroke={stroke * 1e3:.0f}mm RETENTION: z30={z30_f:.1f}mm "
                      f"({'IN<820' if ret_low else 'OUT>=820'}) クリップ-load={_fl['clip_N']:.2f}N "
                      f"(peak {_fl['clip_peak_N']:.2f}) pen={_fl['clip_pen_mm']:+.3f}mm | held[L={Lh['held']} "
                      f"R={Rh['held']}] claw<->clip={claw_clip:+.3f}mm seat_pitch={seat_pitch:+.2f}deg")
                _cap(f"B FEED stroke={stroke * 1e3:.0f}mm: feed={feed_disp * 1e3:+.0f}mm z30={z30_f:.0f} "
                     f"{'PROCEED' if proceeded else 'IMPED'}")
                _feed_frame_idx.append(_fidx[0] - 1)   # saved-frame index for this stroke (compare PNG)
                _prevf = stroke
            _feed_legs = [r for r in sweep if "feed_disp_mm" in r]
            _any_proceed = any(r["proceeded"] for r in _feed_legs)
            _claw_pen = any(r["claw_clip_mm"] <= 0.0 for r in _feed_legs) or (_claw_clip_h0 <= 0.0)
            _crush = any(r["clip_pen_mm"] < -3.0 for r in _feed_legs)
            _tilt_onset_clamp = bool(abs(_seat_pitch_h0 - _seat_pitch_pre) > 5.0 and _claw_clip_h0 <= 0.0)
            _artifact = bool((not feed_valid) or _claw_pen or _crush or _tilt_onset_clamp)
            hook["b_feed"] = {
                "feed_valid": feed_valid, "R_held": R_held_ok, "L_held": L_held_ok,
                "effective_clip_cable_mu": _pair_mu, "clip_geom_mu": round(_clip_g_mu, 3),
                "cable_geom_mu": round(_cab_g_mu, 3), "feed_dy_mm": round(FEED_DY * 1e3, 1),
                "seat_pitch_pre_deg": round(_seat_pitch_pre, 2), "seat_pitch_h0_deg": round(_seat_pitch_h0, 2),
                "claw_clip_h0_mm": round(_claw_clip_h0, 3), "feed_legs": _feed_legs,
                "any_proceed": _any_proceed, "claw_clip_penetration": _claw_pen, "clip_cable_crush": _crush,
                "tilt_onset_at_clamp": _tilt_onset_clamp, "ARTIFACT": _artifact,
            }
            _retsumm = " ".join("s%d:%s" % (r["stroke_mm"], "IN" if r["retained_lowwall"] else "OUT") for r in _feed_legs)
            _consv = ("PROCEEDS (NON-conservative: rigid drags-as-unit easier + friction-fidelity unknown -> needs "
                      "GPU/real confirm)" if _any_proceed else
                      "IMPEDED (CONSERVATIVE-definite at this mu: even the easier CPU/rigid case is stuck -> bankable)")
            print(f"  [FEED] VERDICT mu={_pair_mu} feed_valid={feed_valid}: {_consv} | retention[{_retsumm}] | "
                  f"ARTIFACT={_artifact} (claw_pen={_claw_pen} crush={_crush} tilt_onset_clamp={_tilt_onset_clamp}) "
                  f"-> %0/%2 cross-PV")
            # ===== CORRECTED slide-frame VERDICT (slip∧cradle CONJUNCTION + C1 snag-retention + B-needed reframe) =====
            _slips = [r["slip_ratio"] for r in _feed_legs]
            _abs_slips = [abs(s) for s in _slips]
            _max_abs_slip = max(_abs_slips) if _abs_slips else 9.9   # HONEST aggregation: max deviation-from-stays.
            _mean_slip = float(np.mean(_slips)) if _slips else 9.9   # ⚠ mean can SIGN-CANCEL (drag+springback ~0) =
            # a FALSE "slide" -> the verdict uses max|slip|, NOT the mean.
            _max_seatslide = max((abs(r["seat_slide_mm"]) for r in _feed_legs), default=9.9)  # seated-pt Y-shift (mm)
            _all_contact = bool(all(r["contact_present"] for r in _feed_legs)) if _feed_legs else False
            _all_ret = bool(all(r["retained_lowwall"] for r in _feed_legs)) if _feed_legs else False
            _max_seatdz = max((r["delta_seated_mm"] for r in _feed_legs), default=9.9)
            _claw_mu_legs = [r.get("feed_claw_eff_mu") for r in _feed_legs]
            # SLIDE-THROUGH requires the FULL CONJUNCTION: EVERY stroke slip~0 (max|slip|<0.35) AND the seated cable
            # portion barely shifts along Y (<3mm) AND lateral cradle-contact every stroke AND C1 vertically retained
            # AND no artifact. (slip~0 with NO contact = cable untouched/fell out = ARTIFACT, NOT a slide.)
            _slide_through = bool(_max_abs_slip < 0.35 and _max_seatslide < 3.0 and _all_contact and _all_ret and not _artifact)
            _drag = bool(_max_abs_slip > 0.5 or _max_seatslide > 4.0)
            _verdict_slide = ("SLIDE-THROUGH (しごき WORKS: cable slides, the seated C1 cable-portion stays put, "
                              "cradle contact held)" if _slide_through else
                              ("DRAG/PARTIAL (dead-or-partial しごき: the rigid cable is dragged -> the seated "
                               "portion SHIFTS along Y)" if _drag else
                               "INCONCLUSIVE (check per-stroke slip/contact/seat-slide/artifact)"))
            _b_needed = (("B retention hand likely UNNEEDED (R was OFF and しごき alone kept C1 seated, ~no up-force)"
                          if _slide_through else "C1 NOT retained by しごき alone (R OFF) -> a B retention hand IS needed")
                         if not HOLD_ON else "B-question UNTESTED here (R ON); re-run S13_HOLD=0 to test しごき-alone")
            hook["b_feed"].update({
                "slip_ratios": _slips, "max_abs_slip": round(_max_abs_slip, 3), "mean_slip_ratio": round(_mean_slip, 3),
                "max_seat_slide_mm": round(_max_seatslide, 2), "all_contact_present": _all_contact,
                "all_C1_retained": _all_ret, "max_seat_dz_mm": round(_max_seatdz, 2), "feed_claw_eff_mu_legs": _claw_mu_legs,
                "feed_pad_mu_override": (float(FEED_PAD_MU) if FEED_PAD_MU != "" else None),
                "R_hold_on": bool(HOLD_ON), "SLIDE_THROUGH": _slide_through, "DRAG": _drag, "verdict_slide": _verdict_slide,
                "pre_feed_frame": _pre_feed_frame, "stroke_frames": _feed_frame_idx,
            })
            print(f"  [FEED-VERDICT-SLIDE] grip={FEED_GRIP} drv={FEED_DRV:.3f} R={'ON' if HOLD_ON else 'OFF'} "
                  f"mu_clip={_pair_mu} claw_mu={_claw_mu_legs}: max|slip|={_max_abs_slip:.3f} (mean {_mean_slip:+.3f}) "
                  f"max_seat_slide={_max_seatslide:.2f}mm contact_all={_all_contact} C1_ret_all={_all_ret} "
                  f"max_seat_dz={_max_seatdz:+.2f}mm artifact={_artifact} -> {_verdict_slide}")
            print(f"  [FEED-VERDICT-SLIDE] conservatism: SLIDE@claw_mu = CONSERVATIVE (real lower-mu slides MORE -> "
                  f"bankable); DRAG@claw_mu = NON-conservative (confirm at lower claw mu via FEED_PAD_MU). "
                  f"B-NEED: {_b_needed}")
        if _ik_orig is not None:
            globals()["solve_ik_dual"] = _ik_orig  # restore (tilt blast radius = L re-grasp + lift only)
        _b_f1 = _fidx[0]

        wp.synchronize()  # probe-local finite / explosion gate
        _jqb, _jqdb = state.joint_q.numpy(), state.joint_qd.numpy()
        finite_b = bool(np.all(np.isfinite(_jqb)) and np.all(np.isfinite(state.body_q.numpy())))
        qvel_ok_b = bool(finite_b and float(np.max(np.abs(_jqdb))) < 100.0)

        hook["b_tailhold"] = {
            "mode": ("ON" if HOLD_ON else "OFF"), "seat_body_idx": seat_body, "y_seat": round(y_seat, 4),
            "anchor_dy_mm": round(ANCHOR_DY * 1e3, 1), "tilt_follow": bool(TILT_ON),
            "tilt_theta_deg": round(_math.degrees(theta_L), 2),
            "seated_clip_load": _seat_load, "post_hold_clip_load": _hold_load,
            "y_tail_holder": round(y_tail, 4), "y_re_grasper": round(y_re, 4),
            "span_mm": round(abs(y_tail - y_re) * 1e3, 1),
            "low_wall_top_mm": round(LOW_WALL_TOP, 1), "radcorr_top_mm": round(RADCORR_TOP, 1),
            "high_wall_top_mm": round(HIGH_WALL_TOP, 1), "z30_seated_mm": round(z30_seated, 1),
            "R_tail_hold": ({"held": R_hold["held"], "f1": R_hold["f1"], "f2": R_hold["f2"],
                             "reach_resid_mm": round(R_reach_resid_mm, 2),
                             "z30_close_mm": round(z30_close, 1), "pin_lower_steps": pin_steps} if HOLD_ON else None),
            "z30_after_hold_mm": round(z30_after_hold, 1),
            "holder_net_lift_seat_mm": round(z30_after_hold - z30_seated, 2),
            "L_re_grasp": {"held": L_cage["held"], "f1": L_cage["f1"], "f2": L_cage["f2"],
                           "reach_resid_mm": round(L_reach_resid_mm, 2)},
            "z30_grasp_close_mm": round(z30_grasped, 1), "sweep": sweep,
            "finite": finite_b, "qvel_ok": qvel_ok_b,
            "PROXY_CAVEAT": "co-located X-route degenerate for DELIVERY (CC5, ZERO Y-drag) but representative for the "
                            "LOCAL lift-coupling; body30-SPECIFIC frozen-index z-track (CC4); CPU grip/penetration "
                            "NON-conservative x3, the GEOMETRIC tail-pin mechanism transfers, grip-strength is soft.",
        }

        def _encode_b(name, f0, f1):  # one NAMED §運用14 sub-video from the frame sub-range (claw-local + seat zoom)
            import glob
            import shutil
            import subprocess
            sub = os.path.join(_frames_dir, f"_sub_{name}")
            os.makedirs(sub, exist_ok=True)
            for _o in glob.glob(os.path.join(sub, "*.png")):
                os.remove(_o)
            j = 0
            for i in range(f0, f1):
                src = os.path.join(_frames_dir, f"f{i:05d}.png")
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(sub, f"f{j:05d}.png"))
                    j += 1
            if j == 0:
                return
            out = os.path.join(output_dir or ".", f"{name}.mp4")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "1.5", "-i",
                            os.path.join(sub, "f%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-pix_fmt", "yuv420p", out], check=False)
            try:
                shutil.copy(out, os.path.expanduser(f"~/Downloads/{name}.mp4"))
            except Exception:  # noqa: BLE001
                pass
            print(f"  [B] §運用14 video {name}.mp4 ({j} frames) -> {out} + ~/Downloads/{name}.mp4")

        # Video leg (§運用14): render the motion-bearing positive (B tail-hold ON, or the S13_FEED axial feed).
        if record_video and (HOLD_ON or S13_FEED):
            _encode_b("b_feed" if S13_FEED else "b_tailhold_on", _b_f0, _b_f1)
        _summ_b = " | ".join("h{:.0f}:{:.0f}({:+.1f},{})".format(
            r["h_mm"], r["z30_max_mm"], r["delta_seated_mm"],
            "IN" if r["retained_lowwall"] else ("IN*" if r["retained_radcorr"] else "OUT")) for r in sweep)
        print(f"  [B] VERDICT mode={'ON' if HOLD_ON else 'OFF'} body30-track: seated {z30_seated:.0f} -> {_summ_b} "
              f"(IN=<820 low-wall / IN*=<824 radcorr / OUT=>=824) finite={finite_b} qvel_ok={qvel_ok_b} -> %0/%2 GT cross-PV")
        _summ_load = " | ".join("h{:.0f}:{:.2f}N/pen{:+.2f}/sag{}".format(
            r["h_mm"], r["clip_N"], r["clip_pen_mm"], r["span_sag_mm"]) for r in sweep)
        print(f"  [B] VERDICT-LOAD mode={'ON' if HOLD_ON else 'OFF'} ANCHOR_DY={ANCHOR_DY * 1e3:.0f}mm TILT={int(TILT_ON)}: "
              f"seated_load={_seat_load['clip_N']:.2f}N/pen{_seat_load['clip_pen_mm']:+.2f} -> {_summ_load} "
              f"(クリップ-load = Rs しごき-friction proxy; ABSOLUTE N CPU-non-conservative, TREND robust)")

    # --- GATES ---
    jq, jqd = state.joint_q.numpy(), state.joint_qd.numpy()
    finite = bool(np.all(np.isfinite(jq)) and np.all(np.isfinite(state.body_q.numpy())))
    qvel_ok = bool(finite and float(np.max(np.abs(jqd))) < 100.0)
    moves_ok = bool(ok.get("hover") and ok.get("descend") and ok.get("lift") and ok.get("route"))
    cont_hold_ok = bool(all(w["okL"] and w["okR"] for w in wps))  # CONTINUOUS two-claw cage (every wp, both arms)
    cable_z_end = wps[-1]["cable_z_mm"]
    sag_mm = cable_z_start - min(w["cable_z_mm"] for w in wps)  # max drop below the start through the route
    nodrop_ok = bool(sag_mm <= 10.0)
    route_ok = bool(finite and qvel_ok and moves_ok and cont_hold_ok and nodrop_ok)
    hook_ok = bool(hook.get("hook_ok", False))
    hook_attempted = bool(hook.get("attempted", False))
    milestone_ok = bool(route_ok and hook_ok) if hook_attempted else route_ok

    metrics = {
        "milestone_ok": milestone_ok, "route_ok": route_ok, "hook_ok": hook_ok, "hook_attempted": hook_attempted,
        "finite": finite, "qvel_ok": qvel_ok, "moves_ok": moves_ok,
        "continuous_hold_ok": cont_hold_ok, "nodrop_ok": nodrop_ok, "sag_mm": round(sag_mm, 2),
        "GRASP_YC_mm": round(GRASP_YC * 1e3, 2), "x_grasp": x_grasp, "x_clip": x_clip, "y_clip": y_clip,
        "cable_z_start_mm": round(cable_z_start, 1), "cable_z_end_mm": round(cable_z_end, 1),
        "endpoint_reach": {  # %9 ADD (b): realized per-arm IK residual + the asymmetric stretch/fold at the clip
            "resid_l_mm": round(resid_l_mm, 2), "resid_r_mm": round(resid_r_mm, 2),
            "lat_l_m": round(lat_l_m, 3), "lat_r_m": round(lat_r_m, 3), "stretch_arm": stretch_arm,
            "note": "marginal 2.21mm aerial probe (log:6750) realized under cable; the larger-lateral arm STRETCHES "
                    "(near-reach, fragile), the other FOLDS -- C1(+Y)=L, C5(-Y)=R stretches (mirror)"},
        "waypoints": wps, "hook": hook, "route_c2_freeze_scope": _freeze_scope_rec,
        "scope": ("CPU; grip-MAGNITUDE + penetration NON-conservative x3 vs GPU; M-Hook-1 drop-in PIN=0 "
                  "(real-collision floor retains; depth REL_CABLE_Z hand-tuned = non-conservative)"),
    }
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "s6_grasp_route.json"), "w") as f:
                json.dump(metrics, f, indent=2)
            print(f"  [S6_ROUTE] metrics -> {os.path.join(output_dir, 's6_grasp_route.json')}")
        except Exception as e:  # noqa: BLE001
            print(f"  [S6_ROUTE] (metrics dump skipped: {e})")

    print(f"  [S6_ROUTE] moves_ok={moves_ok} finite={finite} qvel_ok={qvel_ok} "
          f"continuous_hold_ok={cont_hold_ok} nodrop_ok={nodrop_ok} (sag {sag_mm:.1f}mm)")
    n_fail = [w["wp"] for w in wps if not (w["okL"] and w["okR"])]
    if n_fail:
        print(f"  [S6_ROUTE] CONTINUOUS two-claw-cage FAIL waypoints: {n_fail}")
    if record_video and _fidx[0] > 0:
        import subprocess
        _offc = ("_c1" if y_clip > 1e-6 else "_c5") if abs(y_clip) > 1e-6 else ""  # +Y outer=C1 / -Y outer=C5 (mirror)
        _vname = f"s6{_offc}_route_hook.mp4" if hook_attempted else f"s6{_offc}_route.mp4"
        mp4 = os.path.join(output_dir or ".", _vname)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "2", "-i",
                        os.path.join(_frames_dir, "f%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-pix_fmt", "yuv420p", mp4], check=False)
        try:
            import shutil
            shutil.copy(mp4, os.path.expanduser(f"~/Downloads/{_vname}"))
        except Exception:  # noqa: BLE001 (the §運用14 copy must not fail the gate)
            pass
        print(f"  [S6_ROUTE] §運用14 video ({_fidx[0]} frames @2fps) -> {mp4} + ~/Downloads/{_vname}")
    if hook_attempted and route_ok and not hook_ok and not hook.get("seated_809", True):
        print("  [S6_HOOK] ⚠ INTEGRATION FINDING (%9 concern): the post-route LOOSENED cable did NOT seat at 809 "
              f"(cz_seat={hook.get('cz_seat_mm')}mm, rested high toward the clip top 834) -> the M-Route-1 "
              "drag-loosening PROPAGATES to the hook (retention robustness <-> hook). A real finding, NOT a bug "
              "to force -> STOP->%9.")
    _clip_tag = f"OFF-CENTRE clip ({x_clip:.2f},{y_clip:+.3f})" if abs(y_clip) > 1e-6 else f"centred clip ({x_clip:.2f},0)"
    print(f"  [S6_ROUTE/HOOK] milestone_ok={milestone_ok} (route_ok={route_ok} hook_ok={hook_ok} "
          f"attempted={hook_attempted}) "
          f"({'PASS -- grasp+lift+DIAGONAL transport+two-claw retention+drop-in seat@809 (CPU)' if milestone_ok else 'FAIL/STOP'}). "
          f"SCOPE: NON-conservative x3 vs GPU; {_clip_tag}; C2/C4 near-centre + multi-clip = LATER.")
    if _demo_rec is not None:  # P3 recorder: finalize before the fn-tail sys.exit too (M-Hook path; spec §2.7)
        _demo_rec.finalize(verdict={"milestone_ok": bool(milestone_ok)})
    sys.exit(0 if milestone_ok else 2)


def _run_mujoco_episode(model, solver, contacts, scene_info, fk_state, output_dir=None):
    """C4 (R-S6.2): dual-arm episode-level stepping loop on the mujoco backend (env-gate S6_EPISODE=1).

    A SYMMETRIC 3-stage INFRA skeleton (elevate -> scripted-close -> release), structural-inspiration-only
    from GD-S2A §1 -- NOT the asymmetric A-holder/B-retention choreography (deferred R-S7.1). Both arms
    execute the SAME motion to mirror targets. Extends _run_mujoco_ik_motion_smoke from a single grasp to
    an episode loop (default N_EP=1; env S6_EPISODE_N) with a release stage, the C3 hover-warmstart LIFT
    fix, an episode INFRA result dict, and MECHANICAL gates only -- NO grip-force/retention/success verdict
    (R3; contacts=None on the mujoco branch -> the close/open are KINEMATIC poses, not force grasps).

    R1 (asset-identity; ◇→コ swap R-S7.1 2026-06-23): z_grasp uses EE_TO_PINCH_TIP_CLOSED measured on
    ROBOTIQ_STRIPPED_XML = the コ-shape claw asset the mujoco physics build loads (test:975/980). The FK/IK model
    loads the un-clawed 2f85.xml, but the コ claw is geom-only (no new body/joint) so wrist_3 kinematics --
    hence the IK -- are identical; the コ f1ext claw tip (only in physics) drops EE_TO_PINCH_TIP_CLOSED below
    wrist_3, so landing wrist_3 at z_grasp clears the claw tip TABLE+20mm. The per-episode r1_ok gate
    asserts the descend reached z_grasp. Mirrors the smoke's exit gate (sys.exit 0=PASS, 2=FAIL). All
    geometry/seeds probe-derived (probe_c4_episode_convergence). Convergence H1-validated at the C1 value.
    """
    fk_model = scene_info["fk_model"]
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    w3_l, w3_r = lb + EE_BODY_OFFSET, rb + EE_BODY_OFFSET

    n_ep = int(os.environ.get("S6_EPISODE_N", "1"))  # episode count (default 1 for the regression smoke)

    z_grasp = TABLE_HEIGHT + EE_TO_PINCH_TIP_CLOSED + 0.02  # CLOSED コ claw tip clears the table (+20mm)
    z_approach = z_grasp + 0.05
    z_hover = z_grasp + 0.15
    x_wp, y_wp = 0.30, 0.20

    def tgt(z):
        return (x_wp, -y_wp, z), (x_wp, y_wp, z)  # (left, right) wrist_3 targets

    seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]  # robust seed (probe_seq_diag margin 3.142)
    seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]

    def _triad(bq, w3):
        q = bq[w3][3:7]
        qq = wp.quat(float(q[0]), float(q[1]), float(q[2]), float(q[3]))
        ap = wp.quat_rotate(qq, wp.vec3(0.0, 1.0, 0.0))  # local +Y (approach) -> world
        sp = wp.quat_rotate(qq, wp.vec3(1.0, 0.0, 0.0))  # local X (finger-sep) -> world
        return float(-ap[2]), float(abs(sp[0]))  # down_dot(-Z), perp_|x|

    def _snap(keyframes, name, bq):
        dl, pl = _triad(bq, w3_l)
        dr, pr = _triad(bq, w3_r)
        keyframes[name] = {
            "wrist3_L": [round(float(v), 4) for v in bq[w3_l][:3]],
            "wrist3_R": [round(float(v), 4) for v in bq[w3_r][:3]],
            "down_dot_L": round(dl, 4),
            "perp_L": round(pl, 4),
            "down_dot_R": round(dr, 4),
            "perp_R": round(pr, 4),
        }

    def _ramp_gripper(cur_state, target_qpos):  # scripted-kinematic close/open (NO IK; contacts=None -> geometric pose)
        gstart = fk_state.joint_q.numpy().copy()
        for step in range(60):
            t = (step + 1) / 60
            fk_jq = fk_state.joint_q.numpy()
            for k, j in enumerate(GRIPPER_JOINT_RANGE):
                fk_jq[j] = gstart[j] + (target_qpos[k] - gstart[j]) * t
                jr = JOINTS_PER_ARM + j
                fk_jq[jr] = gstart[jr] + (target_qpos[k] - gstart[jr]) * t
            fk_state.joint_q.assign(fk_jq)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            cur_state = physics_step(
                model, cur_state, solver, contacts, scene_info
            )  # step each increment (smoke :2278)
        return cur_state

    pad_bodies = [lb + b for b in GRIPPER_PAD_BODY_IDX] + [rb + b for b in GRIPPER_PAD_BODY_IDX]
    open_qpos = [0.0] * len(GRIPPER_JOINT_RANGE)

    # Self-contained init: arm = hover seed, gripper = open (0).
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:ARM_DOF] = seed_l
    fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    state = model.state()
    for _ in range(10):  # pose the mujoco scene from the hover seed
        state = physics_step(model, state, solver, contacts, scene_info)

    episodes = []
    all_ok = True

    for ep in range(n_ep):
        ok = {}
        keyframes = {}

        # --- STAGE 1: ELEVATE (hover -> approach -> descend; the next episode re-seeds from post-release) ---
        state, ok["hover"] = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            *tgt(z_hover),
            label=f"S6EP{ep}-HOVER",
            converge_mm=5.0,
            speed_factor=0.2,
        )
        _snap(keyframes, "hover", state.body_q.numpy())
        hover_fk_jq = fk_state.joint_q.numpy().copy()  # C3 warm-start source for the post-close LIFT
        state, ok["approach"] = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            *tgt(z_approach),
            label=f"S6EP{ep}-APPROACH",
            converge_mm=5.0,
            speed_factor=0.2,
        )
        _snap(keyframes, "approach", state.body_q.numpy())
        state, ok["descend"] = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            *tgt(z_grasp),
            label=f"S6EP{ep}-DESCEND",
            converge_mm=5.0,
            speed_factor=0.2,
        )
        bq_preclose = state.body_q.numpy().copy()
        _snap(keyframes, "descend_open", bq_preclose)
        # R1: descend landed wrist_3 at z_grasp -> the caged physics tip clears TABLE+20mm (asset-verified).
        wrist_z_err_mm = (
            max(abs(float(bq_preclose[w3_l][2]) - z_grasp), abs(float(bq_preclose[w3_r][2]) - z_grasp)) * 1000.0
        )
        r1_ok = bool(wrist_z_err_mm < 5.0)

        # --- STAGE 2: CLOSE (scripted-kinematic, no IK) ---
        state = _ramp_gripper(state, GRIPPER_CLOSE_QPOS)
        bq_closed = state.body_q.numpy().copy()
        _snap(keyframes, "closed", bq_closed)

        # --- STAGE 3: RELEASE (LIFT holding closed via C3/M1 hover-arm warmstart, then scripted OPEN) ---
        lift_warmstart = fk_state.joint_q.numpy().copy()
        lift_warmstart[0:ARM_DOF] = hover_fk_jq[0:ARM_DOF]
        lift_warmstart[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = hover_fk_jq[
            JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF
        ]
        state, ok["lift"] = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            *tgt(z_hover),
            label=f"S6EP{ep}-LIFT",
            converge_mm=5.0,
            speed_factor=0.2,
            warmstart_jq=lift_warmstart,
        )
        bq_lift = state.body_q.numpy().copy()
        _snap(keyframes, "lift", bq_lift)
        state = _ramp_gripper(state, open_qpos)  # release (kinematic open)
        _snap(keyframes, "released", state.body_q.numpy())

        # --- MECHANICAL GATES (no success/retention field, H2; same class as the smoke asserts) ---
        moves_ok = bool(ok.get("hover") and ok.get("approach") and ok.get("descend") and ok.get("lift"))
        dd_l, pp_l = _triad(bq_lift, w3_l)
        dd_r, pp_r = _triad(bq_lift, w3_r)
        triad_ok = bool(dd_l > 0.99 and dd_r > 0.99 and pp_l > 0.99 and pp_r > 0.99)
        pad_disp = min(float(np.linalg.norm(bq_closed[p][:3] - bq_preclose[p][:3])) for p in pad_bodies) * 1000.0
        pad_ok = bool(pad_disp > 20.0)
        jq = state.joint_q.numpy()
        jqd = state.joint_qd.numpy()
        finite = bool(np.all(np.isfinite(jq)) and np.all(np.isfinite(bq_lift)))
        qvel_ok = bool(float(np.max(np.abs(jqd))) < 100.0)
        w2_margin = float(min(abs(abs(jq[4]) - np.pi / 2), abs(abs(jq[JOINTS_PER_ARM + 4]) - np.pi / 2)))
        margin_ok = bool(w2_margin >= 3.0)
        kf_nondegen = bool(abs(keyframes["hover"]["wrist3_L"][2] - keyframes["descend_open"]["wrist3_L"][2]) > 0.01)
        episode_ok = bool(
            moves_ok and triad_ok and pad_ok and finite and qvel_ok and margin_ok and r1_ok and kf_nondegen
        )
        all_ok = all_ok and episode_ok
        episodes.append(
            {
                "ep": ep,
                "episode_ok": episode_ok,
                "moves_ok": moves_ok,
                "triad_ok": triad_ok,
                "pad_disp_mm": round(pad_disp, 2),
                "pad_ok": pad_ok,
                "finite": finite,
                "qvel_ok": qvel_ok,
                "w2_margin_rad": round(w2_margin, 3),
                "margin_ok": margin_ok,
                "wrist_z_err_mm": round(wrist_z_err_mm, 3),
                "r1_ok": r1_ok,
                "kf_nondegen": kf_nondegen,
                "keyframes": keyframes,
            }
        )
        print(
            f"  [S6_EPISODE] ep{ep}: episode_ok={episode_ok} moves={moves_ok} triad={triad_ok} "
            f"pad_disp={pad_disp:.1f}mm(>20={pad_ok}) margin={w2_margin:.3f}(>=3={margin_ok}) "
            f"wrist_z_err={wrist_z_err_mm:.2f}mm(<5={r1_ok}) finite={finite} qvel_ok={qvel_ok}"
        )

    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "s6_episode.json"), "w") as f:
                json.dump(
                    {
                        "all_ok": all_ok,
                        "n_ep": n_ep,
                        "z_grasp": round(z_grasp, 6),
                        "z_hover": round(z_hover, 6),
                        "episodes": episodes,
                    },
                    f,
                    indent=2,
                )
            print(f"  [S6_EPISODE] result -> {os.path.join(output_dir, 's6_episode.json')}")
        except Exception as e:  # noqa: BLE001 (diagnostic dump must not fail the gate)
            print(f"  [S6_EPISODE] (result dump skipped: {e})")

    print(
        f"  [S6_EPISODE] all_ok={all_ok} over {n_ep} episode(s) "
        f"({'PASS -- mujoco episode loop (elevate->close->release) runs' if all_ok else 'FAIL'})"
    )
    sys.exit(0 if all_ok else 2)


def _run_mujoco_tracking_smoke(model, solver, contacts, scene_info, fk_state, n_frames=60):
    """K2 false-green gate (Option-E Opt-1 SC2b-part2): per-step joint_q kinematic re-pose tracking.

    Drives the articulated UR5e arms via :func:`physics_step` (mujoco branch: OVERWRITE joint_q=FK +
    zero joint_qd every substep) for ``n_frames`` frames, then asserts the ARM joints track the FK
    target: ``max|joint_q[arm] - fk_target[arm]| < 0.05`` rad, all-finite, qvel bounded (<100 rad/s),
    and no AttributeError on the SolverMuJoCo step path. Prints a ``[MUJOCO_SMOKE]`` metrics + verdict
    line and ``sys.exit``s (0 = PASS, 2 = FAIL) so the exit code is the empirical gate.
    """
    n = 2 * JOINTS_PER_ARM
    fk_target = fk_state.joint_q.numpy()[:n].copy()
    # arm joints only (per-arm [0:N_ARM_BODIES] of each JOINTS_PER_ARM-joint arm; gripper held at 0)
    arm_idx = list(range(0, N_ARM_BODIES)) + list(range(JOINTS_PER_ARM, JOINTS_PER_ARM + N_ARM_BODIES))
    state = model.state()
    attribute_error = None
    qvel_max = 0.0
    finite = True
    try:
        for _ in range(n_frames):
            state = physics_step(model, state, solver, contacts, scene_info)
            jqd = state.joint_qd.numpy()
            if not (np.all(np.isfinite(jqd)) and np.all(np.isfinite(state.joint_q.numpy()))):
                finite = False
                break
            qvel_max = max(qvel_max, float(np.max(np.abs(jqd))))
    except AttributeError as e:
        attribute_error = f"{type(e).__name__}: {e}"

    if attribute_error is None and finite:
        jq_end = state.joint_q.numpy()[:n]
        arm_track_err = float(np.max(np.abs(jq_end[arm_idx] - fk_target[arm_idx])))
    else:
        arm_track_err = float("inf")
    qvel_bounded = bool(qvel_max < 100.0)
    tracking_ok = bool(attribute_error is None and finite and arm_track_err < 0.05 and qvel_bounded)

    print(
        f"  [MUJOCO_SMOKE] n_frames={n_frames} arm_track_err={arm_track_err:.6f} (<0.05) "
        f"finite={finite} qvel_max={qvel_max:.6f} (bounded<100={qvel_bounded}) "
        f"attribute_error={attribute_error}"
    )
    print(f"  [MUJOCO_SMOKE] tracking_ok={tracking_ok} ({'PASS -- K2 false-green fixed' if tracking_ok else 'FAIL'})")
    sys.exit(0 if tracking_ok else 2)


def _cable_max_curl(body_q_np, cable_bodies):
    """Max inter-segment tangent angle [rad] (solver-agnostic curl metric, probe-validated)."""
    tangs = []
    for b in cable_bodies:
        qx, qy, qz, qw = (float(x) for x in body_q_np[b][3:7])
        t = wp.quat_rotate(wp.quat(qx, qy, qz, qw), wp.vec3(0.0, 0.0, 1.0))
        tangs.append(np.array([t[0], t[1], t[2]]))
    ang = 0.0
    for i in range(len(tangs) - 1):
        d = float(np.clip(np.dot(tangs[i], tangs[i + 1]), -1.0, 1.0))
        ang = max(ang, float(np.arccos(d)))
    return ang


def _run_mujoco_cable_settle_smoke(
    model, solver, contacts, scene_info, fk_state, n_frames=600, restore_frames=2400, reset_frames=300, output_dir=None
):
    """S4a/S4b cable smoke (D-S4a-5 + the S4b reset-path; B2/B3 posture from the run-3 probe).

    Phase 1 — SETTLE (gravity ON): genuine free-fall (the straight cable is released 15 mm above
    its table rest via the FREE-root pz coord, ONCE, before the loop) driven through
    :func:`physics_step` (the mujoco branch overwrites ONLY the arm joint_q [:28] — the cable FREE
    root is NEVER snapped, the run-3 harness-bug lesson). Asserts: ``solver.mjw_model.
    jnt_stiffness`` AND ``dof_damping`` carry the cable spring+damping on every segment joint
    (the damping is load-bearing, B1 — symmetric runtime assert); no NaN; ``badqacc==0``
    (B2 BINDING — MuJoCo autoreset is DISABLED so an instability must fail loud, never be
    silently clamped to a plausible pose); the fall PROVABLY happened (``com_z ≤ drop_com_z −
    10 mm`` and ``surf_min ≤ TABLE_HEIGHT + 1 mm`` — closes the never-fell loophole); COM-Z ∈
    [0.804±tol]; surface no-penetration ``min(body_z−CABLE_RADIUS) ≥ TABLE_HEIGHT−1.5 mm`` (the
    D-S4a-3 solref tuning is what makes this floor reachable); FREE-root XY/rot drift bounded;
    arm still tracks (<0.05 rad). NO gravity-sag bend assert (F2).

    Phase 2 — RESTORE (B3, gravity OFF in-place via ``mj_model.opt.gravity``; restored for
    Phase 3): from a fresh state, a uniform ~0.08 rad/segment curl is set ONCE; the passive
    spring must decay the curl toward straight (springref=0). Window ``restore_frames`` ≥ 2400
    production frames; PASS = ring-down envelope-end < 0.5×curl_start OBSERVED in-window (no
    extrapolation) + ``badqacc==0`` + finite. Note: margin-proximity cable↔table contacts persist
    at g=0 (the curled chain presses into the contact margin), adding friction dissipation — the
    decay-to-STRAIGHT itself is spring-driven (probe N2 + contact-free restore established the
    spring independently). The FULL per-frame curl trajectory (no downsampling) is written to
    ``{output_dir}/s4a_restore_traj.json``.

    Phase 3 — RESET≥1× (S4b, gravity restored): the settled cable's joint_q is DERIVED from the
    Phase-1 segment TANGENTS (C-1 primary — no cross-script cache), re-seeded into a fresh state
    with a cable-XY-DR root offset, FK'd, and re-settled; asserts the derivation reproduces the
    settled geometry within the C-1 metric floor (~mm), the re-settled state matches the Phase-1
    bounds (COM-Z/surface/qvel), the DR offset persisted (root XY ≈ settled+DR), and
    ``badqacc==0`` (B2 inherited in EVERY phase).

    Emits ``[MUJOCO_CABLE_SMOKE]`` metric lines and ``sys.exit``\\ s (0 = PASS, 2 = FAIL).
    """
    import mujoco  # lazy: the CPU-path mj_model/mj_data handles; vbd runs never import it

    # B2 FAIL-LOUD posture (probe-inherited): disable autoreset; badqacc==0 is BINDING below.
    solver.mj_model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_AUTORESET)

    def _badqacc():
        return int(solver.mj_data.warning[mujoco.mjtWarning.mjWARN_BADQACC].number)

    def _ncon():
        try:
            return int(solver.mj_data.ncon)  # CPU path; mjw_data.nacon is NOT synced on CPU
        except Exception:
            return -1

    cable_bodies = scene_info["cable_bodies"]
    cable_joints = scene_info["cable_joints"]
    free_jid = cable_joints[0]
    n_seg_joints = len(cable_joints) - 1
    cidx = np.array(cable_bodies, dtype=int)
    n = 2 * JOINTS_PER_ARM
    fk_target = fk_state.joint_q.numpy()[:n].copy()
    arm_idx = list(range(0, N_ARM_BODIES)) + list(range(JOINTS_PER_ARM, JOINTS_PER_ARM + N_ARM_BODIES))

    # F1 + %3 binding 3: the passive spring is SET (solver mujoco-warp model; Newton Model lacks it).
    jk = solver.mjw_model.jnt_stiffness.numpy()
    cable_k_count = int(np.sum(np.abs(jk - CABLE_MUJOCO_BEND_K) < 0.1))
    jnt_stiffness_ok = bool(cable_k_count == n_seg_joints)
    # B1 symmetric runtime assert (S4b hardening c): the LOAD-BEARING damping is SET too —
    # jnt_stiffness≠0 does NOT catch a damping omission (the run-2 instability class). The cable
    # is built LAST, so its segment DOFs are the trailing n_seg_joints entries of dof_damping.
    dd = solver.mjw_model.dof_damping.numpy().flatten()
    cable_dd = dd[-n_seg_joints:]
    cable_d_count = int(np.sum(np.abs(cable_dd - CABLE_BEND_DAMPING) < 1e-6))
    dof_damping_ok = bool(cable_d_count == n_seg_joints)

    # --- Phase 1: SETTLE (genuine fall: lift the FREE-root pz ONCE, then hands-off the cable) ---
    jqs = model.joint_q_start.numpy()
    state = model.state()
    jq = state.joint_q.numpy()
    jq[int(jqs[free_jid]) + 2] += 0.015
    state.joint_q.assign(jq)
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)
    bq0 = state.body_q.numpy()
    root0_xy = bq0[cable_bodies[0]][:2].copy()
    root0_quat = bq0[cable_bodies[0]][3:7].copy()
    drop_com_z = float(bq0[cidx][:, 2].mean())

    finite = True
    ncon_max = 0
    for _ in range(n_frames):
        state = physics_step(model, state, solver, contacts, scene_info)
        ncon_max = max(ncon_max, _ncon())
        if not np.all(np.isfinite(state.body_q.numpy())):
            finite = False
            break
    badqacc_settle = _badqacc()

    bqf = state.body_q.numpy()
    bqdf = state.body_qd.numpy()
    cz = bqf[cidx][:, 2]
    com_z = float(cz.mean())
    surf_min = float((cz - CABLE_RADIUS).min())
    cable_qvel = float(np.max(np.abs(bqdf[cidx]))) if finite else float("inf")
    drift_xy = float(np.linalg.norm(bqf[cable_bodies[0]][:2] - root0_xy))
    dq = bqf[cable_bodies[0]][3:7]
    drift_rot = float(2.0 * np.arccos(min(1.0, abs(float(np.dot(dq, root0_quat))))))
    jq_end = state.joint_q.numpy()[:n]
    arm_track_err = float(np.max(np.abs(jq_end[arm_idx] - fk_target[arm_idx]))) if finite else float("inf")

    # S4b hardening (a): the fall PROVABLY happened — closes the loophole where a never-falling
    # cable (e.g. an accidental re-pose) could sit inside the COM-Z band without ever settling.
    fell_ok = bool(com_z <= drop_com_z - 0.010 and surf_min <= TABLE_HEIGHT + 0.001)
    settle_ok = bool(
        finite
        and jnt_stiffness_ok
        and dof_damping_ok
        and badqacc_settle == 0
        and fell_ok
        and abs(com_z - (TABLE_HEIGHT + CABLE_RADIUS)) <= 0.02
        and surf_min >= TABLE_HEIGHT - 0.0015
        and cable_qvel < 5.0
        and drift_xy <= 0.05
        and drift_rot <= 0.30
        and arm_track_err < 0.05
    )
    print(
        f"  [MUJOCO_CABLE_SMOKE] settle: n_frames={n_frames} drop_com_z={drop_com_z:.4f} "
        f"com_z={com_z:.4f} (0.804±0.02) surf_min={surf_min:.4f} (>={TABLE_HEIGHT - 0.0015:.4f}) "
        f"fell={fell_ok} qvel={cable_qvel:.4f} drift_xy={drift_xy:.4f} drift_rot={drift_rot:.4f} "
        f"arm_track={arm_track_err:.4f} ncon_max={ncon_max} badqacc={badqacc_settle} "
        f"jnt_k({CABLE_MUJOCO_BEND_K:.2f})x{cable_k_count}/{n_seg_joints} "
        f"dof_d({CABLE_BEND_DAMPING})x{cable_d_count}/{n_seg_joints} finite={finite} "
        f"settle_ok={settle_ok}"
    )

    # --- Phase 2: RESTORE (B3) — gravity OFF, fresh state, one-time curl IC, spring rings down ---
    gravity0 = solver.mj_model.opt.gravity.copy()  # (b) restored for Phase 3 / after the smoke
    solver.mj_model.opt.gravity[:] = 0.0
    bq_before_restore = _badqacc()
    state_r = model.state()
    jq = state_r.joint_q.numpy()
    seg_q0 = int(jqs[free_jid]) + 7  # segment coords start after the FREE root's 7 position coords
    curl0 = 0.08
    jq[seg_q0:] = curl0
    state_r.joint_q.assign(jq)
    newton.eval_fk(model, state_r.joint_q, state_r.joint_qd, state_r)
    curl_start = _cable_max_curl(state_r.body_q.numpy(), cable_bodies)

    traj = [curl_start]
    finite_r = True
    ncon_restore = 0
    for _ in range(restore_frames):
        state_r = physics_step(model, state_r, solver, contacts, scene_info)
        bq = state_r.body_q.numpy()
        if not np.all(np.isfinite(bq)):
            finite_r = False
            break
        traj.append(_cable_max_curl(bq, cable_bodies))
        ncon_restore = max(ncon_restore, _ncon())
    badqacc_restore = _badqacc() - bq_before_restore

    env_block = 60
    tarr = np.array(traj)
    n_blocks = max(1, len(tarr) // env_block)
    envelope = [float(np.max(tarr[b * env_block : (b + 1) * env_block])) for b in range(n_blocks)]
    env_end = envelope[-1]
    restore_ok = bool(
        finite_r
        and badqacc_restore == 0
        and len(envelope) >= 2
        and env_end < 0.5 * curl_start  # B3: halving OBSERVED in-window, not extrapolated
    )
    if output_dir is not None:
        traj_path = os.path.join(output_dir, "s4a_restore_traj.json")
        with open(traj_path, "w") as f:
            json.dump(
                {
                    "curl_start": curl_start,
                    "restore_frames": restore_frames,
                    "curl_traj_per_frame": [float(t) for t in traj],
                    "envelope_block60": envelope,
                    "badqacc_restore": badqacc_restore,
                    "finite": finite_r,
                },
                f,
            )
    else:
        traj_path = "(not written: no output_dir)"
    print(
        f"  [MUJOCO_CABLE_SMOKE] restore: frames={restore_frames} curl_start={curl_start:.4f} "
        f"env_end={env_end:.5f} (<{0.5 * curl_start:.4f} observed) badqacc={badqacc_restore} "
        f"ncon={ncon_restore} (margin-proximity contacts persist at g=0; decay is spring-driven) "
        f"finite={finite_r} restore_ok={restore_ok} traj={traj_path}"
    )

    # --- Phase 3 (S4b): reset≥1× — derive joint_q from the SETTLED tangents, re-seed (+XY-DR),
    # re-settle, and assert the re-settled state matches Phase 1. Gravity restored (b). ---
    solver.mj_model.opt.gravity[:] = gravity0
    from newton_skill_env_base import (  # noqa: E402  (lazy; envs/ on sys.path since make_solver)
        derive_cable_joint_q_from_tangents,
        seed_cable_joint_state,
    )

    root7, seg_angles = derive_cable_joint_q_from_tangents(bqf, cable_bodies)
    dr_xy = (0.010, -0.010)  # cable-XY-DR seam exercised deterministically
    state_rs = model.state()
    seed_cable_joint_state(state_rs, model, cable_joints, root7, seg_angles, dr_xy=dr_xy)
    # C-1 derivation fidelity: FK(seeded joint_q) − DR must reproduce the settled geometry (~mm
    # floor — the X-axis chain can't represent out-of-plane tangent components).
    bq_seed = state_rs.body_q.numpy()
    recon = bq_seed[cidx][:, :3] - np.array([dr_xy[0], dr_xy[1], 0.0])
    derive_err = float(np.max(np.linalg.norm(recon - bqf[cidx][:, :3], axis=1)))

    bq_before_reset = _badqacc()
    finite_rs = True
    for _ in range(reset_frames):
        state_rs = physics_step(model, state_rs, solver, contacts, scene_info)
        if not np.all(np.isfinite(state_rs.body_q.numpy())):
            finite_rs = False
            break
    badqacc_reset = _badqacc() - bq_before_reset

    bqr = state_rs.body_q.numpy()
    czr = bqr[cidx][:, 2]
    com_z_r = float(czr.mean())
    surf_min_r = float((czr - CABLE_RADIUS).min())
    qvel_r = float(np.max(np.abs(state_rs.body_qd.numpy()[cidx]))) if finite_rs else float("inf")
    xy_target = root0_xy + np.array(dr_xy)
    xy_err = float(np.linalg.norm(bqr[cable_bodies[0]][:2] - xy_target))
    reset_ok = bool(
        finite_rs
        and badqacc_reset == 0
        and derive_err <= 0.005
        and abs(com_z_r - (TABLE_HEIGHT + CABLE_RADIUS)) <= 0.02
        and surf_min_r >= TABLE_HEIGHT - 0.0015
        and qvel_r < 5.0
        and xy_err <= 0.05
    )
    print(
        f"  [MUJOCO_CABLE_SMOKE] reset: frames={reset_frames} derive_err={derive_err:.5f} "
        f"(<=0.005, C-1 floor) dr_xy={dr_xy} xy_err={xy_err:.4f} com_z={com_z_r:.4f} "
        f"surf_min={surf_min_r:.4f} qvel={qvel_r:.4f} badqacc={badqacc_reset} "
        f"finite={finite_rs} reset_ok={reset_ok}"
    )

    cable_ok = bool(settle_ok and restore_ok and reset_ok)
    print(f"  [MUJOCO_CABLE_SMOKE] cable_ok={cable_ok} ({'PASS' if cable_ok else 'FAIL'})")
    sys.exit(0 if cable_ok else 2)


def main():
    global _physics_state_buffer
    parser = argparse.ArgumentParser(description="Newton clip routing test")
    parser.add_argument("--no-cable", action="store_true", help="Remove cable (IK isolation test)")
    parser.add_argument("--num-episodes", type=int, default=1, help="Number of episodes")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--record-video", action="store_true", help="Record video (ViewerGL headless)")
    parser.add_argument("--no-video", action="store_true", help="Disable video even when HARNESS_RECORD_VIDEO=1")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (enables per-episode perturbation)")
    parser.add_argument(
        "--solver-backend",
        type=str,
        default=SOLVER_BACKEND,
        choices=["vbd", "mujoco"],
        help="Physics solver (Option-E Opt-1): vbd (default) | mujoco (articulated-arm smoke)",
    )
    args = parser.parse_args()

    use_cable = not args.no_cable
    solver_backend = args.solver_backend
    # Harness mode: HARNESS_RECORD_VIDEO=1 enables video by default
    if not args.no_video and os.environ.get("HARNESS_RECORD_VIDEO", "") == "1":
        args.record_video = True

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/newton_clip_routing_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[NEWTON_CLIP_ROUTING] Device={DEVICE}")
    print(f"[NEWTON_CLIP_ROUTING] Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"[NEWTON_CLIP_ROUTING] DT={DT:.6f}s ({int(1 / DT)}Hz)")
    print(f"[NEWTON_CLIP_ROUTING] URDF: {FRANKA_URDF}")
    print("[NEWTON_CLIP_ROUTING] Architecture: VBD (Cosserat Rod cable + kinematic robot bodies)")
    print(f"[NEWTON_CLIP_ROUTING] Substeps: {SIM_SUBSTEPS}, SIM_DT={SIM_DT:.6f}s")
    print(f"[NEWTON_CLIP_ROUTING] VBD iterations: {VBD_ITERATIONS}")
    print("[NEWTON_CLIP_ROUTING] IK: Newton IKSolver (LM) on FK model")
    print(f"[NEWTON_CLIP_ROUTING] Cable: {'ON' if use_cable else 'OFF'}")
    print("[NEWTON_CLIP_ROUTING] Coordinates (body6 Z / fingertip Z):")
    print(f"  EE_TO_FINGERTIP: {EE_TO_FINGERTIP * 1000:.0f}mm")
    print(f"  Approach: body6={APPROACH_Z:.3f} fingertip={APPROACH_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Grasp:    body6={GRASP_Z:.3f} fingertip={GRASP_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Lift:     body6={LIFT_Z:.3f} fingertip={LIFT_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Push:     body6={PUSH_Z:.3f} fingertip={PUSH_Z - EE_TO_FINGERTIP:.3f}")
    print(f"  Table:    {TABLE_HEIGHT:.3f}")
    print(f"  L_Y={WIDE_LEFT_Y}, R_Y={WIDE_RIGHT_Y}")
    print(f"  Clip1: ({CLIP1_X}, {CLIP1_Y}, {CLIP1_Z})")
    print()

    # Build FK model FIRST (needed for initial body positions in build_scene)
    print("[BUILD] Building FK model (robot-only, for IK + body transforms)...")
    fk_model = build_fk_model()
    fk_state = fk_model.state()

    # Initialize FK joint positions to URDF home config
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    # Open fingers.
    # ⚠ S6 RESIDUAL-FRANKA (flag-only, debate M6): {+7,+8}=FINGER_OPEN_POS is the Franka 2-finger open
    # applied to 2f85 joints 7,8 (=right_coupler/right_spring_link). This shared init runs for BOTH
    # backends, but the mujoco IK-motion smoke (_run_mujoco_ik_motion_smoke) self-inits the gripper open
    # via GRIPPER_JOINT_RANGE; this site is effective only on the VBD/legacy path. Full VBD-episode
    # retarget = a separate flagged legacy task (out of S6-min scope; see S6_5CC_DEBATE_DECIDE.md M7).
    for arm_offset in [0, FRANKA_NUM_JOINTS]:
        fk_jq[arm_offset + 7] = FINGER_OPEN_POS
        fk_jq[arm_offset + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    print(f"  [FK] Initial joint_q set from URDF home config, fingers open={FINGER_OPEN_POS * 1000:.1f}mm")

    # Build physics scene (VBD cable + kinematic robot bodies positioned from FK)
    # R-S6.6 CHANGE 4 (env-gate): S6_GRASP=1 (mujoco only) wires the actuated-grasp path additively;
    # OFF leaves the whole build + the 5 legacy consumers byte-identical.
    s6_grasp = solver_backend == "mujoco" and os.environ.get("S6_GRASP") == "1"
    # M-Grasp-engage-1 (env-gate S6_GRASP_ENGAGE=1, mujoco only): chains the BANKED koshape cable-ENGAGED
    # grasp+lift into the harness. Needs the actuated build (= S6_GRASP) AND the table-slot void
    # RE-CENTERED on the cable grasp Y (M1, %2 design-gate VERIFY: grasp_y=0 = clip-array center, log:6712;
    # the C1-default void [0.09,0.21] would collide a Y=0 grasp against the solid -Y box). OFF leaves the
    # S6_GRASP + legacy build byte-identical (s6_grasp_engage=False -> grasp_actuation=s6_grasp, grasp_y=None).
    s6_grasp_engage = solver_backend == "mujoco" and os.environ.get("S6_GRASP_ENGAGE") == "1"
    # M-Route-1 (env-gate S6_GRASP_ROUTE=1, mujoco only): centred grasp+lift + AERIAL transport (GX->clipX 0.40)
    # + a CONTINUOUS retention gate (faithful-to-intent of the banked CPU r_s71_clip_dropin ROUTE; NOT the VBD port).
    s6_grasp_route = solver_backend == "mujoco" and os.environ.get("S6_GRASP_ROUTE") == "1"
    print("[BUILD] Building physics scene...")
    scene_info = build_scene(
        use_cable=use_cable,
        fk_model=fk_model,
        fk_state=fk_state,
        solver_backend=solver_backend,
        grasp_actuation=s6_grasp or s6_grasp_engage or s6_grasp_route,
        grasp_y=(float(os.environ.get("S6_ENGAGE_YC", "0.0")) if (s6_grasp_engage or s6_grasp_route) else None),
        cable_xy_offset=(  # ③ B2 per-run rigid cable-XY offset via env "dx,dy" [m]; unset -> None = legacy
            tuple(float(v) for v in os.environ["CABLE_XY_OFFSET"].split(","))
            if os.environ.get("CABLE_XY_OFFSET")
            else None
        ),
    )
    model = scene_info["model"]
    cable_bodies = scene_info.get("cable_bodies", [])

    # Store FK model in scene_info (used by solve_ik_dual, ik_move_both, physics_step)
    scene_info["fk_model"] = fk_model
    scene_info["fk_state"] = fk_state

    # Initialize physics state (VBD: only cable joint coords, no robot joints)
    state = model.state()

    # VBD control object (required by solver.step, but no PD targets for kinematic bodies)
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control

    # model.collide() for contacts (BOX-CAPSULE narrowphase)
    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    print(f"  [COLLISION] model.collide() (BOX-CAPSULE, rigid_contact_max={NJMAX})")

    # Create solver via the Option-E factory (SC1 make_solver; lazy import avoids the base<->script
    # circular import). Default "vbd" => byte-identical to SolverVBD(model, iterations=VBD_ITERATIONS).
    _envs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "envs")
    if _envs_dir not in sys.path:
        sys.path.insert(0, _envs_dir)
    # _wire_s6_grasp_solref relocated to base (newton_skill_env_base.py) + generalized for multi-world
    # (shared by build_scene single-world + build_multiworld_scene N-world). Imported here, not redefined.
    from newton_skill_env_base import _wire_s6_grasp_solref, make_solver  # noqa: E402  (lazy: circular import)

    solver = make_solver(
        model, backend=solver_backend, enable_cable_contacts=(solver_backend == "mujoco" and use_cable)
    )
    print(f"  [SOLVER] {solver_backend} solver created via make_solver")

    # R-S6.6 CHANGE 3: poke the negative PAD_SOLREF into mj+mjw + run the I11 readback asserts (the
    # negative solref has no build-time path; the mj-only poke is GPU-inert). S6_GRASP-gated (+ engage).
    if s6_grasp or s6_grasp_engage or s6_grasp_route:
        _wire_s6_grasp_solref(solver, scene_info)

    # Option-E mujoco smokes (the standalone gates; the full VBD episode below is NOT ported, S5-S7):
    # --no-cable -> the Opt-1 SC2b-part2 joint_q tracking smoke (K2 false-green gate, unchanged);
    # with cable -> the S4a cable-settle + curl-restore smoke (D-S4a-5, B2/B3 posture). Both exit.
    if solver_backend == "mujoco":
        if s6_grasp_route:
            # M-Route-1 (env-gate S6_GRASP_ROUTE=1, needs cable): centred grasp+lift + AERIAL transport +
            # CONTINUOUS retention gate. Placed FIRST so OFF (route unset) leaves the existing branches
            # byte-identical. sys.exit(0/2).
            _run_mujoco_grasp_route(model, solver, contacts, scene_info, fk_state, output_dir=args.output_dir,
                                    record_video=args.record_video)
        elif s6_grasp_engage:
            # M-Grasp-engage-1 (env-gate S6_GRASP_ENGAGE=1, needs cable): chain the BANKED koshape cable-
            # ENGAGED grasp+lift into the harness. Placed FIRST so OFF (engage unset) leaves the existing
            # branches byte-identical. sys.exit(0/2).
            _run_mujoco_grasp_engage_episode(model, solver, contacts, scene_info, fk_state, output_dir=args.output_dir,
                                             record_video=args.record_video)
        elif s6_grasp:
            # R-S6.6: actuated dynamic-gripper grasp episode (env-gate S6_GRASP=1, needs cable). Placed
            # FIRST so OFF dispatch (the 4 existing branches) stays byte-identical. sys.exit(0/2).
            _run_mujoco_grasp_episode(model, solver, contacts, scene_info, fk_state, output_dir=args.output_dir)
        elif use_cable:
            _run_mujoco_cable_settle_smoke(model, solver, contacts, scene_info, fk_state, output_dir=args.output_dir)
        elif os.environ.get("S6_IK_MOTION_SMOKE") == "1":
            # S6 dual-arm IK-motion infra smoke (env-gated; the default --no-cable mujoco path keeps the
            # K2 tracking gate below UNCHANGED). sys.exit(0/2). (debate A3/H3; no new CLI arg, debate alt#5)
            _run_mujoco_ik_motion_smoke(model, solver, contacts, scene_info, fk_state, output_dir=args.output_dir)
        elif os.environ.get("S6_EPISODE") == "1":
            # C4 (R-S6.2): dual-arm episode loop (elevate->close->release) on the mujoco backend. Placed
            # AFTER the S6_IK_MOTION_SMOKE elif (deterministic precedence if both set) and BEFORE the K2
            # default else, so K2 + S6-smoke dispatch stay UNCHANGED. sys.exit(0/2). --no-cable infra.
            _run_mujoco_episode(model, solver, contacts, scene_info, fk_state, output_dir=args.output_dir)
        else:
            _run_mujoco_tracking_smoke(model, solver, contacts, scene_info, fk_state, n_frames=60)
        return  # both smokes sys.exit(); this return is a safety net

    # Contact material properties (set in build_scene ShapeConfig, verify here)
    shape_ke = model.shape_material_ke.numpy()
    shape_kd = model.shape_material_kd.numpy()
    shape_mu = model.shape_material_mu.numpy()
    shape_bodies_arr = model.shape_body.numpy()
    lb = scene_info["left_body_start"]
    rb = scene_info["right_body_start"]
    # Log finger/cable contact material for diagnostics
    for arm_label, arm_bs in [("L", lb), ("R", rb)]:
        for local in [7, 8]:
            bi = arm_bs + local
            for si in range(model.shape_count):
                if shape_bodies_arr[si] == bi:
                    print(
                        f"  [CONTACT] {arm_label}_body{local} shape#{si}: "
                        f"ke={shape_ke[si]:.0f}, kd={shape_kd[si]:.0f}, mu={shape_mu[si]:.2f}"
                    )
                    break
    if cable_bodies:
        cb0 = cable_bodies[0]
        for si in range(model.shape_count):
            if shape_bodies_arr[si] == cb0:
                print(
                    f"  [CONTACT] Cable body0 shape#{si}: "
                    f"ke={shape_ke[si]:.0f}, kd={shape_kd[si]:.0f}, mu={shape_mu[si]:.2f}"
                )
                break

    # Video recorder
    recorder = VideoRecorder(args.output_dir, model, enabled=args.record_video, scene_info=scene_info)
    scene_info["recorder"] = recorder
    set_scene_colors(recorder, scene_info)

    # Raw evidence logger (independent verification channel for Code B)
    evidence = RawEvidenceLogger(args.output_dir)
    scene_info["evidence"] = evidence

    # Settle cable via VBD (2s) — kinematic bodies already positioned from FK
    print("[INIT] Settling (2s)...")
    settle_steps = int(2.0 / DT)
    nan_detected = False
    for i in range(settle_steps):
        state = physics_step(model, state, solver, contacts, scene_info)

        # Early NaN detection (first 50 steps)
        if i < 50 and not nan_detected:
            bq = state.body_q.numpy()
            if np.any(np.isnan(bq)):
                nan_body = np.where(np.isnan(bq[:, 0]))[0]
                nc = contacts.rigid_contact_count.numpy()[0] if hasattr(contacts, "rigid_contact_count") else -1
                print(f"  [NaN] Step {i}: NaN first in bodies {nan_body[:5]}... contacts={nc}")
                nan_detected = True

        if i % int(0.5 / DT) == 0:
            pos_l, pos_r = get_ee_positions(state, scene_info)
            cable_info = ""
            if cable_bodies:
                bq = state.body_q.numpy()
                cable_z = np.mean(bq[cable_bodies, 2])
                cable_info = f" cable_z={cable_z:.4f}"
            print(
                f"  settle t={i * DT:.1f}s: EE L=({pos_l[0]:.3f},{pos_l[1]:.3f},{pos_l[2]:.3f}) "
                f"R=({pos_r[0]:.3f},{pos_r[1]:.3f},{pos_r[2]:.3f}){cable_info}"
            )

    # Verify initial EE positions and measure actual EE_TO_FINGERTIP
    pos_l, pos_r = get_ee_positions(state, scene_info)
    print(
        f"[INIT] Final EE: L=({pos_l[0]:.4f},{pos_l[1]:.4f},{pos_l[2]:.4f}) "
        f"R=({pos_r[0]:.4f},{pos_r[1]:.4f},{pos_r[2]:.4f})"
    )

    # Diagnostic: actual body positions for EE_TO_FINGERTIP verification
    body_q = state.body_q.numpy()
    for arm, bs in [("L", scene_info["left_body_start"]), ("R", scene_info["right_body_start"])]:
        hand_z = body_q[bs + 6][2]
        f7_z = body_q[bs + 7][2]
        f8_z = body_q[bs + 8][2]
        print(f"[INIT] {arm} body Z: hand(b6)={hand_z:.4f}, finger7={f7_z:.4f}, finger8={f8_z:.4f}")
        print(
            f"[INIT] {arm} EE_TO_FINGER: b6-b7={((hand_z - f7_z) * 1000):.1f}mm, "
            f"b6-b8={((hand_z - f8_z) * 1000):.1f}mm (config={EE_TO_FINGERTIP * 1000:.0f}mm)"
        )

    # Check contacts after settle
    model.collide(state, contacts)
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
        print(
            f"[INIT] Cable settled: mean_z={cable_z:.4f}, mean_x={cable_x:.4f} "
            f"(drift={((cable_x - GRASP_X) * 1000):.1f}mm, std={cable_x_std * 1000:.1f}mm)"
        )
        scene_info["settled_grasp_x"] = float(cable_x)
    else:
        scene_info["settled_grasp_x"] = GRASP_X

    # Save settled state for episode reset
    # Physics state: body transforms + cable joint coords
    settled_body_q = state.body_q.numpy().copy()
    settled_body_qd = state.body_qd.numpy().copy()
    settled_phys_jq = state.joint_q.numpy().copy()
    settled_phys_jqd = state.joint_qd.numpy().copy()
    # FK state: robot joint positions
    settled_fk_jq = fk_state.joint_q.numpy().copy()

    # Per-episode perturbation RNG (None = deterministic, same as before)
    rng = np.random.RandomState(args.seed) if args.seed is not None else None
    if rng is not None:
        print(f"[PERTURB] Seed={args.seed}, cable joint perturbation per episode")

    # Run episodes
    all_results = {
        "test": "newton_clip_routing",
        "device": DEVICE,
        "frame_dt": DT,
        "dt": DT,
        "solver": "VBD",
        "vbd_iterations": VBD_ITERATIONS,
        "sim_substeps": SIM_SUBSTEPS,
        "sim_dt": SIM_DT,
        "cable_model": "Cosserat Rod (add_rod, CABLE joints)",
        "robot_model": "Kinematic bodies (FK-driven)",
        "ik": "Newton IKSolver LM (FK model)",
        "cable": use_cable,
        "episodes": [],
        "n_pass": 0,
        "n_fail": 0,
    }

    start_time = time.time()

    for ep in range(args.num_episodes):
        print(f"\n{'=' * 60}")
        print(f"  EPISODE {ep + 1}/{args.num_episodes}")
        print(f"{'=' * 60}")

        # Reset scene to settled state for each episode
        if ep > 0:
            # Reset physics state: body transforms + cable joints
            state = model.state()
            state.body_q.assign(settled_body_q)
            state.body_qd.assign(settled_body_qd)
            state.joint_q.assign(settled_phys_jq)
            state.joint_qd.assign(settled_phys_jqd)

            # Reset VBD solver internal state (body_q_prev stores previous-step transforms;
            # stale values from previous episode cause huge velocity deltas → cable explosion)
            # P5: hasattr-guard (mujoco SolverMuJoCo has no body_q_prev; matches the guards below).
            if hasattr(solver, "body_q_prev") and solver.body_q_prev is not None:
                solver.body_q_prev.assign(settled_body_q)
            if hasattr(solver, "particle_q_prev") and solver.particle_q_prev is not None:
                solver.particle_q_prev.zero_()
            # Dahl friction state (if enabled)
            if hasattr(solver, "joint_sigma_prev") and solver.joint_sigma_prev is not None:
                solver.joint_sigma_prev.zero_()
            if hasattr(solver, "joint_kappa_prev") and solver.joint_kappa_prev is not None:
                solver.joint_kappa_prev.zero_()
            if hasattr(solver, "joint_dkappa_prev") and solver.joint_dkappa_prev is not None:
                solver.joint_dkappa_prev.zero_()

            # Reset double-buffer
            _physics_state_buffer = None

            # Reset FK state (robot joints with open fingers)
            # ⚠ S6 RESIDUAL-FRANKA (flag-only, debate M6, twin of the init site): Franka {+7,+8} open on
            # 2f85 joints; VBD-path only. Separate legacy-retarget task (out of S6-min scope).
            fk_jq_reset = settled_fk_jq.copy()
            for arm_offset in [0, FRANKA_NUM_JOINTS]:
                fk_jq_reset[arm_offset + 7] = FINGER_OPEN_POS
                fk_jq_reset[arm_offset + 8] = FINGER_OPEN_POS
            fk_state.joint_q.assign(fk_jq_reset)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

            # Sync kinematic bodies in physics state (overrides robot body_q from FK)
            update_kinematic_bodies(state, fk_state, scene_info["robot_body_count"])

            print("  [RESET] Scene restored to settled state")

        recorder.reset()

        try:
            state, ep_result = run_episode(model, state, scene_info, solver, contacts, ep)
        except Exception as e:
            print(f"\n  [ERROR] Episode {ep + 1} crashed: {e}")
            import traceback

            traceback.print_exc()
            ep_result = {"episode": ep, "overall": "CRASH", "error": str(e)}

        # Fingertip penetration gate (z-check before finalizing verdict)
        pen = recorder.check_penetration()
        if pen and pen["penetration_detected"]:
            ep_result["penetration"] = pen
            print(
                f"  [ZCHECK] Fingertip penetration detected: "
                f"{pen['max_penetration_mm']:.1f}mm below table "
                f"({pen['penetration_pct']:.0f}% of frames)"
            )
            if ep_result["overall"] == "PASS":
                ep_result["overall"] = "FAIL"
                ep_result["fail_reason"] = f"fingertip_penetration_{pen['max_penetration_mm']:.1f}mm"

        # Finalize video for this episode (returns list of per-camera MP4 paths)
        video_paths = recorder.finalize(ep)
        if video_paths:
            ep_result["videos"] = video_paths

        all_results["episodes"].append(ep_result)

        if ep_result["overall"] == "PASS":
            all_results["n_pass"] += 1
            print(f"\n  >>> EPISODE {ep + 1}: PASS <<<")
        else:
            all_results["n_fail"] += 1
            reason = ep_result.get("fail_reason", "unknown")
            print(f"\n  >>> EPISODE {ep + 1}: {ep_result['overall']} ({reason}) <<<")

    elapsed = time.time() - start_time
    video_encode_s = round(recorder.total_encode_s, 1)
    sim_elapsed_s = round(elapsed - recorder.total_encode_s, 1)
    all_results["elapsed_s"] = round(elapsed, 1)
    all_results["sim_elapsed_s"] = sim_elapsed_s
    all_results["video_elapsed_s"] = video_encode_s
    all_results["overall"] = "PASS" if all_results["n_fail"] == 0 else "FAIL"
    all_results["pass_rate"] = f"{all_results['n_pass']}/{args.num_episodes}"

    # Close evidence logger
    evidence.close()

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(all_results, f, indent=2, default=json_default)

    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"  Pass rate: {all_results['pass_rate']}")
    print(f"  Overall: {all_results['overall']}")
    print(f"  Elapsed: {elapsed:.1f}s (sim={sim_elapsed_s}s, video={video_encode_s}s)")
    print(f"  Metrics: {metrics_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
