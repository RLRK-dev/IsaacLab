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

import numpy as np
import trimesh
import warp as wp
import newton
from newton.solvers import SolverMuJoCo, SolverVBD
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit
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
    FRANKA_NUM_JOINTS, EE_BODY_OFFSET, BODIES_PER_ARM, JOINTS_PER_ARM, N_ARM_BODIES,
    TABLE_HEIGHT, ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE, SOLVER_BACKEND,
    EE_TO_FINGERTIP, APPROACH_Z, GRASP_Z, LIFT_Z, PUSH_Z,
    SIM_SUBSTEPS, NJMAX,
    MUJOCO_CONTACT_KE, MUJOCO_CONTACT_KD,
    CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    CABLE_BEND_STIFFNESS, CABLE_BEND_DAMPING,
    CABLE_STRETCH_STIFFNESS, CABLE_STRETCH_DAMPING,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
    GRASP_X, CLIP_X, CLIP_GROOVE_INNER_RADIUS, P3_X_OFFSET, WIDE_LEFT_Y, WIDE_RIGHT_Y,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_CLOSE_STEPS,
    GRIPPER_JOINT_RANGE, GRIPPER_PAD_BODY_IDX, GRIPPER_CLOSE_QPOS, ARM_DOF, EE_TO_PINCH_TIP_CLOSED,
    STEPS_PER_CM, MAX_MOVE_STEPS, SETTLE_STEPS,
    GROOVE_BODIES_MIN,
)

# ---------------------------------------------------------------------------
# Constants (non-tunable)
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0             # Frame dt (outer step)
SIM_DT = DT / SIM_SUBSTEPS   # Solver dt (inner substep)
GRAVITY = -9.81
VBD_ITERATIONS = 20           # VBD constraint solver iterations per substep

# Clip position — from task_config SSOT
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z

# Franka
FRANKA_URDF = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "source", "extensions", "isaaclab_tasks_thread", "data", "robots",
    "panda_independent_fingers.urdf",
))

# UR5e + Robotiq 2f85 (Option-E substrate, S1 assets) — S2a FK/scene source.
_UR5E_ASSET = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ur5e_robotiq",
))
UR5E_XML = os.path.join(_UR5E_ASSET, "ur5e", "ur5e.xml")
ROBOTIQ_XML = os.path.join(_UR5E_ASSET, "robotiq_2f85", "2f85.xml")
# Path-A (Option-E Opt-1): 2f85 with the <tendon> node removed so the combined add_mjcf build
# constructs under SolverMuJoCo (the WITH-tendon build OOBs _init_tendons). Byte-copy of 2f85.xml
# minus <tendon>; <equality> is dropped at parse via skip_equality_constraints. Faithful 4-bar = S5.
ROBOTIQ_STRIPPED_XML = os.path.join(_UR5E_ASSET, "robotiq_2f85", "2f85_tendon_stripped.xml")
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
HAND_OFFSET_Z = 0.107              # link7 → link8 (panda_joint8 xyz)
HAND_OFFSET_RZ = -0.785398163397   # link8 → hand (panda_hand_joint rpy)

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
    ("overhead",    (0.35, -0.05, 2.20), (0.35, -0.05, 0.82)),  # top-down: XY overview (Z=2.2 for full workspace FOV)
    ("front",       (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),  # +X→-X: Z-height, table penetration
    ("diag_upper",  (0.65, -0.40, 1.00), (0.35, -0.05, 0.82)),  # 45° upper: shifted +Y to reduce R-arm occlusion
    ("left",        (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),  # -Y→+Y: closer & lower (table+13cm)
    ("right",       (0.35,  0.55, 0.93), (0.35, -0.05, 0.82)),  # +Y→-Y: closer & lower (table+13cm)
    ("clip_close",  (0.50, -0.05, 0.83), (0.35, -0.05, 0.82)),  # groove-level profile: horizontal view of groove insertion
]

# On-hand camera: local offsets in body 6 (link7/panda_hand) frame.
# Mounted at 7th-axis rotation point, moves with fingers.
# ~45° diagonal view of finger clamp area (opening/closing visible).
# Body 6 frame: Z toward fingertips, Y = finger open/close axis.
# NOTE: Must match eval_skill.py ONHAND_LOCAL_OFFSET/TARGET.
ONHAND_LOCAL_OFFSET = np.array([0.05, 0.05, 0.10])   # 5cm X, 5cm Y, 10cm along Z
ONHAND_LOCAL_TARGET = np.array([0.0, 0.0, 0.17])      # finger mid-area (EE_TO_FINGERTIP≈0.22)

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
        print(f"  [VIDEO] Per-camera recorder initialized "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {n_static} static"
              f"{f' + {n_onhand} on-hand' if n_onhand else ''}"
              f" = {n_static + n_onhand} cameras)")

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
            (lb + 7, xf_id),      # left finger 7
            (lb + 8, xf_180z),    # left finger 8 (180° Z)
            (rb + 7, xf_id),      # right finger 7
            (rb + 8, xf_180z),    # right finger 8 (180° Z)
        ]
        print(f"  [VIDEO] finger visuals: mesh verts={self._finger_mesh.vertices.shape}, "
              f"bodies={[bi for bi, _ in self._finger_body_indices]}")

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
            dtype=wp.vec3, device=DEVICE,
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

        _enc_elapsed = time.time() - _enc_t0
        self.total_encode_s += _enc_elapsed
        print(f"  [VIDEO] Saved {len(video_paths)} camera videos "
              f"({VIDEO_CAM_W}x{VIDEO_CAM_H}, {n_frames} frames each, "
              f"encode={_enc_elapsed:.1f}s)")
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
COLOR_FINGER = (1.0, 0.2, 0.2)    # RED — highest priority for table-penetration detection
COLOR_TABLE  = (0.65, 0.50, 0.35)  # TAN/BROWN — distinct from white/gray defaults
COLOR_HAND   = (0.3, 0.3, 0.6)    # BLUE-GRAY — distinguish hand body from fingers
COLOR_ARM    = (0.9, 0.9, 0.9)    # WHITE — Franka Panda standard color
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
        shape_colors[table_idx] = COLOR_TABLE

    # Clip V-groove parts (world-attached, explicit indices)
    for clip_idx in scene_info.get("clip_shape_indices", []):
        shape_colors[clip_idx] = COLOR_CLIP

    if shape_colors:
        recorder.viewer.update_shape_colors(shape_colors)
        n_arm = sum(1 for c in shape_colors.values() if c == COLOR_ARM)
        n_finger = sum(1 for c in shape_colors.values() if c == COLOR_FINGER)
        n_hand = sum(1 for c in shape_colors.values() if c == COLOR_HAND)
        print(f"  [VIDEO] Scene colors: {n_arm} arm(white), {n_hand} hand(blue-gray), "
              f"{n_finger} finger(red), 1 table(tan), "
              f"{len(scene_info.get('clip_shape_indices', []))} clip(green)")


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
            "franka_description", "meshes", "visual",
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
            print(f"  [MESH] Finger visual: {nv:,} verts, {nf:,} faces"
                  f" (bounds Y=[{fb_min[1]:.4f},{fb_max[1]:.4f}] "
                  f"Z=[{fb_min[2]:.4f},{fb_max[2]:.4f}])")

        _load_arm_meshes._cache = cache
        total_meshes = sum(len(v) for v in cache.values() if isinstance(v, list))
        print(f"  [MESH] Loaded {total_meshes} visual DAE meshes for {len(cache)} bodies "
              f"({total_verts:,} total vertices)")
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
                body=sb, xform=local_xf, radius=float(scl[0]), half_height=float(scl[1]), cfg=arm_cfg)
        elif gname == "CYLINDER":
            sid = builder.add_shape_cylinder(
                body=sb, xform=local_xf, radius=float(scl[0]), half_height=float(scl[1]), cfg=arm_cfg)
        elif gname == "SPHERE":
            sid = builder.add_shape_sphere(body=sb, xform=local_xf, radius=float(scl[0]), cfg=arm_cfg)
        else:
            continue  # unknown primitive — skip (visual-only; no collision role in S2)
        builder.shape_flags[sid] = 1  # VISIBLE only (strip COLLIDE — arm has no collision role)
        n_arm_shapes += 1

    shape_end = builder.shape_count
    print(f"  [ARM-{label_prefix}] {BODIES_PER_ARM} kinematic bodies (UR5e+Robotiq), "
          f"arm visual primitives={n_arm_shapes} (VISIBLE-only), gripper bare (pads=S5), "
          f"shapes=[{shape_start}:{shape_end}]")

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
    cable_cfg.gap = 0.002                 # 2mm contact gap
    cable_cfg.density = 1100.0            # Rubber cable density (kg/m³)

    body_ids, joint_ids = builder.add_rod(
        positions=positions,
        radius=CABLE_RADIUS,
        stretch_stiffness=CABLE_STRETCH_STIFFNESS,   # EA [N] (divided by L internally)
        stretch_damping=CABLE_STRETCH_DAMPING,
        bend_stiffness=CABLE_BEND_STIFFNESS,         # EI [N·m²] (divided by L internally)
        bend_damping=CABLE_BEND_DAMPING,
        cfg=cable_cfg,
    )

    seg_mass = cable_cfg.density * np.pi * CABLE_RADIUS**2 * CABLE_SEG_LEN
    print(f"  [CABLE] add_rod: {len(body_ids)} bodies, {len(joint_ids)} joints "
          f"(CABLE+FREE), EI={CABLE_BEND_STIFFNESS}, EA={CABLE_STRETCH_STIFFNESS}, "
          f"density={cable_cfg.density:.0f}, seg_mass={seg_mass*1000:.1f}g, "
          f"total_length={total_length*1000:.0f}mm")

    return body_ids, joint_ids


# D-S4a-3 (S4a, MuJoCo path): MUJOCO_CONTACT_KE/KD now live in task_config (SSOT relocation,
# human-Rs-approved 2026-06-10; provenance + the convert_solref derivation are documented there).
# Cable bend spring (S4a probe-decided contract, S4_CYCLE4_DESIGN.md §C2): k = EI/L = 66.67
# N·m/rad DIRECT (Newton 1.2 #6) + the LOAD-BEARING real damping (B1) + straight rest.
CABLE_MUJOCO_BEND_K = CABLE_BEND_STIFFNESS / CABLE_SEG_LEN  # 1.0/0.015 = 66.67


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
    cable_cfg.mu = CABLE_CONTACT_MU
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
            b, xform=wp.transform(wp.vec3(0.0, 0.0, half), wp.quat_identity()),
            radius=CABLE_RADIUS, half_height=half, cfg=cable_cfg,
        )
        body_ids.append(b)
    shape_end = builder.shape_count

    # FREE root + segment REVOLUTE joints, CONSECUTIVE (contiguous ids for add_articulation).
    free_jid = builder.add_joint_free(child=body_ids[0], parent=-1)
    joint_ids = [free_jid]
    for e in range(1, CABLE_SEGMENTS):
        joint_ids.append(builder.add_joint_revolute(
            parent=body_ids[e - 1], child=body_ids[e],
            parent_xform=wp.transform(wp.vec3(0.0, 0.0, CABLE_SEG_LEN), wp.quat_identity()),
            child_xform=wp.transform(wp.vec3(0.0, 0.0, 0.0), wp.quat_identity()),
            axis=wp.vec3(1.0, 0.0, 0.0),  # local-X bend axis ⟂ cable → vertical sag plane
            collision_filter_parent=True,  # EXPLICIT (builder.py:3898; adjacent segments don't collide)
            custom_attributes={
                "mujoco:dof_passive_stiffness": CABLE_MUJOCO_BEND_K,
                "mujoco:dof_passive_damping": CABLE_BEND_DAMPING,
                "mujoco:dof_springref": 0.0,
            },
        ))
    builder.add_articulation(joint_ids)

    seg_mass = cable_cfg.density * np.pi * CABLE_RADIUS**2 * CABLE_SEG_LEN
    print(f"  [CABLE] add_revolute_cable: {len(body_ids)} bodies, {len(joint_ids)} joints "
          f"(FREE+REVOLUTE), k={CABLE_MUJOCO_BEND_K:.2f} N·m/rad, damping={CABLE_BEND_DAMPING}, "
          f"springref=0, solref=({2.0/MUJOCO_CONTACT_KD:.3f},1.0), seg_mass={seg_mass*1000:.1f}g")

    return body_ids, joint_ids, (shape_start, shape_end)


def build_scene(use_cable=True, fk_model=None, fk_state=None, solver_backend="vbd"):
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
    table_xform = wp.transform((0.3, -0.05, TABLE_HEIGHT - table_half[2]), wp.quat_identity())
    table_idx = builder.add_shape_box(
        body=-1,
        hx=table_half[0], hy=table_half[1], hz=table_half[2],
        xform=table_xform,
        cfg=table_cfg,
    )
    print(f"  [SCENE] Table at z={TABLE_HEIGHT} (BOX primitive)")

    # Clip V-groove (visual-only)
    cx, cy, cz = CLIP1_X, CLIP1_Y, CLIP1_Z
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
    print(f"  [SCENE] Clip V-groove at ({cx}, {cy}, {cz}), 5 parts")

    # Robot arms: VBD = jointless kinematic bodies (FK body_q); MuJoCo = articulated UR5e+Robotiq.
    if solver_backend == "mujoco":
        # Option-E Opt-1 (SC2b-part2, D-Opt1-1): articulated UR5e+Robotiq per arm via the probe-
        # validated add_mjcf recipe (Robotiq <tendon> stripped so SolverMuJoCo constructs; the
        # _init_tendons OOB is avoided). S4a (D-S4a-3): contacts are now ENABLED for the cable, so
        # the A-1 VISIBLE-only pass below is LOAD-BEARING — without it the whole UR5e+Robotiq
        # collision set goes live and the fixed-arm-over-table explodes (cycle-2 CRITICAL).
        left_shape_start = builder.shape_count
        add_ur5e_robotiq(
            builder, wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()),
            robotiq_xml=ROBOTIQ_STRIPPED_XML, skip_equality_constraints=True)
        left_shape_end = builder.shape_count
        right_shape_start = left_shape_end
        add_ur5e_robotiq(
            builder, wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
            robotiq_xml=ROBOTIQ_STRIPPED_XML, skip_equality_constraints=True)
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
            else:
                builder.shape_flags[si] = int(newton.ShapeFlags.VISIBLE)
                arm_cleared += 1
        print(f"  [SCENE] A-1 VISIBLE-only pass (mujoco): {arm_cleared} arm shapes COLLIDE-cleared, "
              f"{pads_kept} pad shapes kept")
        all_finger_visual = set()
    else:
        # Left arm (kinematic bodies, no joints)
        left_body_start, left_shape_start, left_shape_end, left_fv = add_kinematic_arm(
            builder, fk_model, fk_state, arm_body_offset=0, label_prefix="left")

        # Right arm (kinematic bodies, no joints)
        right_body_start, right_shape_start, right_shape_end, right_fv = add_kinematic_arm(
            builder, fk_model, fk_state, arm_body_offset=FRANKA_NUM_JOINTS, label_prefix="right")

        # All finger visual DAE shape indices (to exclude from approximate_meshes)
        all_finger_visual = set(left_fv + right_fv)

        # Contact filtering for arm bodies
        ground_planes = [floor_shape_idx, table_idx]
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
        print(f"  [SCENE] Contact filtering: {filter_count} arm+finger-visual shapes flagged, "
              f"finger collision → COLLIDE only (not visible)")

    # Cable: VBD = Cosserat rod (add_rod, CABLE joints); MuJoCo = rigid-link REVOLUTE chain
    # (S4a D-S4a-4 — CABLE joints are MuJoCo-rejected, solver_mujoco.py:292).
    cable_bodies = []
    cable_joints = []
    if use_cable:
        cable_shape_start = builder.shape_count
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = CLIP1_Y - cable_half_len
        cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CABLE_RADIUS)
        if solver_backend == "mujoco":
            cable_bodies, cable_joints, _cable_sr = add_revolute_cable(
                builder, start_pos=cable_start, direction=(0, 1, 0))
            cable_shape_start, cable_shape_end = _cable_sr
        else:
            cable_bodies, cable_joints = add_cable_rod(builder, start_pos=cable_start, direction=(0, 1, 0))
            cable_shape_end = builder.shape_count
        cable_y_end = cable_start[1] + CABLE_SEGMENTS * CABLE_SEG_LEN
        print(f"  [SCENE] Cable: {len(cable_bodies)} bodies, {len(cable_joints)} joints, "
              f"Y=[{cable_y_start:.3f}, {cable_y_end:.3f}], Z={cable_start[2]:.4f}")

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
            print(f"  [SCENE] Cable contact filters (mujoco): "
                  f"{cable_shape_end - cable_shape_start} cable-floor, "
                  f"{cable_arm_filters} cable-(non-pad-arm) (pads keep cable contacts)")
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
            print(f"  [SCENE] Cable contact filters: "
                  f"{cable_shape_end - cable_shape_start} cable-floor, "
                  f"{cable_arm_filters} cable-arm (fingers keep cable contacts)")
    else:
        print(f"  [SCENE] Cable: DISABLED (--no-cable)")

    # A-3 backend-conditional from the LIVE right_body_start: VBD kinematic = 18, mujoco articulated = 28.
    robot_body_count = right_body_start + FRANKA_NUM_JOINTS

    # Finger collision is now BOX primitives (no approximate_meshes needed)
    print(f"  [SHAPES] Finger collision: BOX×3 per finger (wall+claws), "
          f"{len(all_finger_visual)} finger visual DAE preserved")

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
        print(f"  [SCENE] Kinematic bodies: inv_mass=0 for bodies 0-{robot_body_count-1}")

    print(f"  [SCENE] Model: bodies={model.body_count}, joints={model.joint_count}, "
          f"articulations={model.articulation_count}, "
          f"joint_coords={model.joint_coord_count}, joint_dofs={model.joint_dof_count}")

    # D-S4a-4 joint-layout assert (mujoco): arm joints [0:28] + cable FREE+REVOLUTE — guards the
    # arm joint_q slice (physics_step overwrites [:2*JOINTS_PER_ARM]) against layout drift.
    if solver_backend == "mujoco" and use_cable:
        expected = 2 * JOINTS_PER_ARM + len(cable_joints)
        assert model.joint_count == expected, (
            f"mujoco joint layout drift: joint_count={model.joint_count} != "
            f"2*JOINTS_PER_ARM + cable joints = {expected}")

    # Shape diagnostics
    # (VBD only -- §28 #3: indexes the kinematic-arm finger bodies [7,8]; N/A to the mujoco articulated arm.)
    if solver_backend != "mujoco":
        shape_types = model.shape_type.numpy()
        shape_bodies = model.shape_body.numpy()
        shape_flags = model.shape_flags.numpy()
        shape_collision_group = model.shape_collision_group.numpy()
        TYPE_NAMES = {0: "NONE", 1: "PLANE", 2: "HFIELD", 3: "SPHERE", 4: "CAPSULE",
                      5: "ELLIPSOID", 6: "CYLINDER", 7: "BOX", 8: "MESH", 9: "CONE", 10: "CONVEX_MESH"}
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
                    print(f"  [SHAPE] {arm_label} body{local_body} shape#{si}: type={name}, "
                          f"flags={flags:#x}(COLLIDE={has_collide}), cgroup={cgroup}")
                if arm_label == "Left":
                    break
        if cable_bodies:
            si0 = [si for si in range(len(shape_bodies)) if shape_bodies[si] == cable_bodies[0]]
            if si0:
                si = si0[0]
                print(f"  [SHAPE] Cable body0 shape#{si}: type={TYPE_NAMES.get(shape_types[si],'?')}, "
                      f"flags={shape_flags[si]:#x}(COLLIDE={bool(shape_flags[si] & COLLIDE_SHAPES)}), "
                      f"cgroup={shape_collision_group[si]}")

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
        "clip_shape_indices": clip_shape_indices,
        "solver_backend": solver_backend,
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
    print(f"  [FK] Robot-only model: bodies={model.body_count}, "
          f"joints={model.joint_count}, "
          f"joint_coords={model.joint_coord_count}, joint_dofs={model.joint_dof_count}")
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
_physics_state_buffer = None   # Pre-allocated double-buffer state (created on first call)


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

    for i in range(SIM_SUBSTEPS):
        if solver_backend == "mujoco":
            # MuJoCo articulated kinematic re-pose (D-Opt1-2): per-substep OVERWRITE joint_q=FK +
            # zero joint_qd (the STEP-1 probe-validated driving; MuJoCo poses bodies from joint_q).
            # disable_contacts=True -> no model.collide (contacts None), mirroring the base mujoco branch.
            n = 2 * JOINTS_PER_ARM
            phys_jq = state_0.joint_q.numpy()
            phys_jqd = state_0.joint_qd.numpy()
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

    return state_0


# ---------------------------------------------------------------------------
# IK helpers
# ---------------------------------------------------------------------------
def solve_ik_dual(scene_info, target_left, target_right):
    """Solve IK for both arms using the FK model.

    Returns (fk_joint_q, cost) — the FK model joint positions with IK solution.
    """
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    # EE body indices in FK model (body 6 = panda_hand for each arm)
    left_ee_body = EE_BODY_OFFSET                       # 5 (UR5e wrist_3; S2a aliased EE_BODY_OFFSET=EE_BODY_IDX=5)
    right_ee_body = FRANKA_NUM_JOINTS + EE_BODY_OFFSET   # 19 (FRANKA_NUM_JOINTS aliased to ROBOT_NUM_JOINTS=14)

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
    target_rot = wp.array([wp.vec4(-0.7071067811865476, 0.0, 0.0, 0.7071067811865476)],
                          dtype=wp.vec4, device=DEVICE)
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

    ik_solver = IKSolver(fk_model, n_problems=1,
                         objectives=[obj_l, obj_r, rot_l, rot_r, *collision_objs, obj_joint_limits])

    # Current FK joint positions as initial guess
    fk_jq = fk_state.joint_q.numpy().copy()
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
def ik_move_both(model, state, scene_info, solver, contacts,
                 target_left, target_right, label="MOVE",
                 converge_mm=5.0,
                 speed_factor=1.0):
    """Move both EEs to target positions using IK + VBD stepping.

    Strategy: Solve IK ONCE for the final target, then interpolate FK joint
    positions over physics steps. Kinematic bodies follow FK instantly.

    Args:
        speed_factor: multiplier for step count (>1 = slower motion).

    Returns (final_state, success).
    """
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

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
    jq_target, ik_cost = solve_ik_dual(scene_info, tuple(tgt_l), tuple(tgt_r))
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
                diag_str += f" fingers=[{fj[0]*1000:.1f},{fj[1]*1000:.1f},{fj[2]*1000:.1f},{fj[3]*1000:.1f}]mm"
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
    print(f"  [{label}] Penalty contacts: {n} (finger-cable={fc}, finger-other={fo}, cable-other={co}, other={oo})")


def do_p1_grasp(model, state, scene_info, solver, contacts):
    """P1: Wide-stance approach + descend + grasp.

    ⚠ S6 RESIDUAL-FRANKA (flag-only, debate M7): this legacy VBD episode (do_p1_grasp/p2/p3/p4) is
    DEFAULT-reachable (SOLVER_BACKEND="vbd") but still Franka-indexed for the gripper (the close ramps
    {+7,+8}, not GRIPPER_JOINT_RANGE -> closes 0 pads on the UR5e 2f85). PRE-EXISTING-broken-for-UR5e
    (NOT introduced by S6); S6 only corrects the SHARED solve_ik_dual/ik_move_both IK. Full VBD-episode
    retarget = a separate flagged legacy task. The S6 deliverable is the mujoco IK-motion smoke.
    """
    print(f"\n  {'='*50}")
    print(f"  [P1] Wide-Stance Approach + Grasp")
    print(f"  {'='*50}")

    cable_bodies = scene_info.get("cable_bodies", [])
    has_cable = len(cable_bodies) > 0
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    # Step 1: Approach (move to above cable)
    print(f"\n  [P1-APPROACH] Target: L=({grasp_x:.3f},{WIDE_LEFT_Y},{APPROACH_Z}) "
          f"R=({grasp_x:.3f},{WIDE_RIGHT_Y},{APPROACH_Z})")
    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
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
        model, state, scene_info, solver, contacts,
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

    # Step 3: Close fingers (kinematic interpolation via FK model)
    # Fingers move kinematically regardless of cable resistance.
    # Cable responds via VBD contacts (BOX-CAPSULE).
    print(f"\n  [P1-CLOSE] Closing fingers to {FINGER_CLOSE_POS*1000:.1f}mm (kinematic)")

    # Pre-close diagnostics
    fk_jq_pre = fk_state.joint_q.numpy()
    bq_pre = state.body_q.numpy()
    nan_bq = np.any(np.isnan(bq_pre))
    print(f"  [P1-CLOSE] Pre-close state: bq NaN={nan_bq}")
    print(f"  [P1-CLOSE] Pre-close fingers: L_j7={fk_jq_pre[7]*1000:.1f}mm "
          f"L_j8={fk_jq_pre[8]*1000:.1f}mm "
          f"R_j7={fk_jq_pre[FRANKA_NUM_JOINTS+7]*1000:.1f}mm "
          f"R_j8={fk_jq_pre[FRANKA_NUM_JOINTS+8]*1000:.1f}mm")
    if cable_bodies:
        cable_z = [bq_pre[b][2] for b in cable_bodies[:5]]
        print(f"  [P1-CLOSE] Pre-close cable Z[0:5]: {['%.3f'%z for z in cable_z]}")

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
            robot_nan = np.any(np.isnan(bq[:scene_info["robot_body_count"]]))
            cable_nan = np.any(np.isnan(bq[cable_bodies]))
            if robot_nan or cable_nan:
                print(f"    [CLOSE-NAN] step={step}: robot_nan={robot_nan}, cable_nan={cable_nan}")
                for bi in range(len(bq)):
                    if np.any(np.isnan(bq[bi])):
                        blabel = model.body_label[bi] if bi < len(model.body_label) else f"body{bi}"
                        print(f"      NaN body {bi} ({blabel}): {bq[bi][:3]}")
                        if bi >= 5:
                            print(f"      ... (showing first 5 NaN bodies)")
                            break
                nan_detected_step = step
                break
            cz = bq[cable_bodies, 2]
            b0 = bq[cable_bodies[0]]
            fj7 = fk_jq[7]
            fj8 = fk_jq[8]
            if step < 5 or step % 50 == 0 or abs(np.mean(cz) - TABLE_HEIGHT) > 0.005:
                print(f"    [CLOSE-DIAG] step={step}: cable_z={np.mean(cz):.4f} "
                      f"finger=[{fj7*1000:.1f},{fj8*1000:.1f}]mm "
                      f"body0=[{b0[0]:.3f},{b0[1]:.3f},{b0[2]:.3f}]")
    if nan_detected_step >= 0:
        print(f"  [P1-CLOSE] NaN detected at step {nan_detected_step}/{FINGER_CLOSE_STEPS}")

    # Read finger positions from FK state
    fk_jq = fk_state.joint_q.numpy()
    grip_l = fk_jq[7] + fk_jq[8]
    grip_r = fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8]
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


    pos_l, pos_r = get_ee_positions(state, scene_info)

    # Raw evidence: P1 completion snapshot
    evidence = scene_info.get("evidence")
    if evidence:
        evidence.log("P1_complete", state, scene_info, extra={
            "grip_l_mm": round(grip_l * 1000, 2),
            "grip_r_mm": round(grip_r * 1000, 2),
        })

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
        model, state, scene_info, solver, contacts,
        target_left=(grasp_x, WIDE_LEFT_Y, LIFT_Z),
        target_right=(grasp_x, WIDE_RIGHT_Y, LIFT_Z),
        label="P2-LIFT",
    )

    # Settle
    state = hold_position(model, state, scene_info, solver, contacts,
                          SETTLE_STEPS)

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
    print(f"  [P2] Lift {'OK' if lifted else 'INSUFFICIENT'}: delta={cable_z_delta_mm}mm, "
          f"cable_z={cable_z_mean:.4f}, target={cable_target_z:.4f}")

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


def do_p3_move(model, state, scene_info, solver, contacts):
    """P3: Move from cable X to clip X."""
    print(f"\n  {'='*50}")
    grasp_x = scene_info.get("settled_grasp_x", GRASP_X)
    move_target_x = CLIP_X + P3_X_OFFSET
    print(f"  [P3] Move to Clip X ({grasp_x:.3f} → {move_target_x:.3f}  [CLIP_X={CLIP_X} + offset={P3_X_OFFSET}])")
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


def do_p4_push(model, state, scene_info, solver, contacts):
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
    print(f"  [P4] Current EE X: L={pos_l[0]:.4f} R={pos_r[0]:.4f}")
    print(f"  [P4] Push target: X={CLIP_X} (realign from P3 overshoot), Z={PUSH_Z} (dZ={((PUSH_Z - pos_l[2])*1000):.1f}mm)")

    # P3 overshoots to CLIP_X+P3_X_OFFSET; P4 re-centers on CLIP_X during push-down.
    state, ok = ik_move_both(
        model, state, scene_info, solver, contacts,
        target_left=(CLIP_X, pos_l[1], PUSH_Z),
        target_right=(CLIP_X, pos_r[1], PUSH_Z),
        label="P4-PUSH",
        speed_factor=2.0,  # slower push reduces cable XY inertia
    )

    # Longer settle for push (3x base: cable XY equilibration after push-down)
    state = hold_position(model, state, scene_info, solver, contacts,
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
def run_episode(model, state, scene_info, solver, contacts, episode_idx):
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
        evidence.log("episode_end", state, scene_info, extra={
            "episode": episode_idx,
            "overall": results["overall"],
        })

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
    z_grasp = TABLE_HEIGHT + EE_TO_PINCH_TIP_CLOSED + 0.02   # descend: CLOSED tip clears the table (+20mm)
    z_approach = z_grasp + 0.05
    z_hover = z_grasp + 0.15
    x_wp, y_wp = 0.30, 0.20

    def tgt(z):
        return (x_wp, -y_wp, z), (x_wp, y_wp, z)            # (left, right) wrist_3 targets

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
    fk_jq[JOINTS_PER_ARM:JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    state = model.state()
    for _ in range(10):   # pose the mujoco scene from the hover seed (kinematic re-pose)
        state = physics_step(model, state, solver, contacts, scene_info)

    keyframes = {}

    def _triad(bq, w3):
        q = bq[w3][3:7]
        qq = wp.quat(float(q[0]), float(q[1]), float(q[2]), float(q[3]))
        ap = wp.quat_rotate(qq, wp.vec3(0.0, 1.0, 0.0))   # local +Y (approach) -> world
        sp = wp.quat_rotate(qq, wp.vec3(1.0, 0.0, 0.0))   # local X (finger-sep) -> world
        return float(-ap[2]), float(abs(sp[0]))           # down_dot(-Z), perp_|x|

    def _snap(name, bq):
        dl, pl = _triad(bq, w3_l)
        dr, pr = _triad(bq, w3_r)
        keyframes[name] = {
            "wrist3_L": [round(float(v), 4) for v in bq[w3_l][:3]],
            "wrist3_R": [round(float(v), 4) for v in bq[w3_r][:3]],
            "down_dot_L": round(dl, 4), "perp_L": round(pl, 4),
            "down_dot_R": round(dr, 4), "perp_R": round(pr, 4),
        }

    _snap("seed", state.body_q.numpy())   # raw IK seed pose (pre-IK initial guess; NOT a target/down-pose)

    # IK moves (speed_factor 0.2 -> ~1mm/step, fast on 0-GPU; DiffIK-safe). converge_mm gates each move.
    # First HOVER move turns the raw seed into a converged, gripper-down hover pose.
    ok = {}
    state, ok["hover"] = ik_move_both(model, state, scene_info, solver, contacts,
                                      *tgt(z_hover), label="S6-HOVER", converge_mm=5.0, speed_factor=0.2)
    _snap("hover", state.body_q.numpy())
    state, ok["approach"] = ik_move_both(model, state, scene_info, solver, contacts,
                                         *tgt(z_approach), label="S6-APPROACH", converge_mm=5.0, speed_factor=0.2)
    _snap("approach", state.body_q.numpy())
    state, ok["descend"] = ik_move_both(model, state, scene_info, solver, contacts,
                                        *tgt(z_grasp), label="S6-DESCEND", converge_mm=5.0, speed_factor=0.2)
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
    state, ok["lift"] = ik_move_both(model, state, scene_info, solver, contacts,
                                     *tgt(z_hover), label="S6-LIFT", converge_mm=5.0, speed_factor=0.2)
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
    smoke_ok = bool(moves_ok and triad_ok and pad_ok and finite and qvel_ok)

    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "s6_ik_motion_smoke.json"), "w") as f:
                json.dump({"smoke_ok": smoke_ok, "moves_ok": moves_ok, "triad_ok": triad_ok,
                           "pad_disp_mm": round(pad_disp, 2), "pad_ok": pad_ok, "finite": finite,
                           "qvel_max": round(qvel_max, 4), "keyframes": keyframes}, f, indent=2)
            print(f"  [S6_IK_SMOKE] keyframe trajectory -> {os.path.join(output_dir, 's6_ik_motion_smoke.json')}")
        except Exception as e:  # noqa: BLE001 (diagnostic dump must not fail the gate)
            print(f"  [S6_IK_SMOKE] (keyframe dump skipped: {e})")

    print(f"  [S6_IK_SMOKE] moves_ok={moves_ok} (hover={ok.get('hover')},approach={ok.get('approach')},"
          f"descend={ok.get('descend')},lift={ok.get('lift')}) triad_ok={triad_ok} (L down={dd_l:.3f}/perp={pp_l:.3f}, "
          f"R down={dd_r:.3f}/perp={pp_r:.3f}) pad_disp={pad_disp:.1f}mm (>20={pad_ok}) "
          f"finite={finite} qvel_max={qvel_max:.3f} (<100={qvel_ok})")
    print(f"  [S6_IK_SMOKE] smoke_ok={smoke_ok} "
          f"({'PASS -- S6 dual-arm IK episode runs (hover->approach->descend->close->lift)' if smoke_ok else 'FAIL'})")
    sys.exit(0 if smoke_ok else 2)


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

    print(f"  [MUJOCO_SMOKE] n_frames={n_frames} arm_track_err={arm_track_err:.6f} (<0.05) "
          f"finite={finite} qvel_max={qvel_max:.6f} (bounded<100={qvel_bounded}) "
          f"attribute_error={attribute_error}")
    print(f"  [MUJOCO_SMOKE] tracking_ok={tracking_ok} "
          f"({'PASS -- K2 false-green fixed' if tracking_ok else 'FAIL'})")
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


def _run_mujoco_cable_settle_smoke(model, solver, contacts, scene_info, fk_state,
                                   n_frames=600, restore_frames=2400, reset_frames=300,
                                   output_dir=None):
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
        finite and jnt_stiffness_ok and dof_damping_ok
        and badqacc_settle == 0
        and fell_ok
        and abs(com_z - (TABLE_HEIGHT + CABLE_RADIUS)) <= 0.02
        and surf_min >= TABLE_HEIGHT - 0.0015
        and cable_qvel < 5.0
        and drift_xy <= 0.05 and drift_rot <= 0.30
        and arm_track_err < 0.05
    )
    print(f"  [MUJOCO_CABLE_SMOKE] settle: n_frames={n_frames} drop_com_z={drop_com_z:.4f} "
          f"com_z={com_z:.4f} (0.804±0.02) surf_min={surf_min:.4f} (>={TABLE_HEIGHT - 0.0015:.4f}) "
          f"fell={fell_ok} qvel={cable_qvel:.4f} drift_xy={drift_xy:.4f} drift_rot={drift_rot:.4f} "
          f"arm_track={arm_track_err:.4f} ncon_max={ncon_max} badqacc={badqacc_settle} "
          f"jnt_k({CABLE_MUJOCO_BEND_K:.2f})x{cable_k_count}/{n_seg_joints} "
          f"dof_d({CABLE_BEND_DAMPING})x{cable_d_count}/{n_seg_joints} finite={finite} "
          f"settle_ok={settle_ok}")

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
    envelope = [float(np.max(tarr[b * env_block:(b + 1) * env_block])) for b in range(n_blocks)]
    env_end = envelope[-1]
    restore_ok = bool(
        finite_r and badqacc_restore == 0
        and len(envelope) >= 2
        and env_end < 0.5 * curl_start  # B3: halving OBSERVED in-window, not extrapolated
    )
    if output_dir is not None:
        traj_path = os.path.join(output_dir, "s4a_restore_traj.json")
        with open(traj_path, "w") as f:
            json.dump({"curl_start": curl_start, "restore_frames": restore_frames,
                       "curl_traj_per_frame": [float(t) for t in traj],
                       "envelope_block60": envelope, "badqacc_restore": badqacc_restore,
                       "finite": finite_r}, f)
    else:
        traj_path = "(not written: no output_dir)"
    print(f"  [MUJOCO_CABLE_SMOKE] restore: frames={restore_frames} curl_start={curl_start:.4f} "
          f"env_end={env_end:.5f} (<{0.5 * curl_start:.4f} observed) badqacc={badqacc_restore} "
          f"ncon={ncon_restore} (margin-proximity contacts persist at g=0; decay is spring-driven) "
          f"finite={finite_r} restore_ok={restore_ok} traj={traj_path}")

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
        finite_rs and badqacc_reset == 0
        and derive_err <= 0.005
        and abs(com_z_r - (TABLE_HEIGHT + CABLE_RADIUS)) <= 0.02
        and surf_min_r >= TABLE_HEIGHT - 0.0015
        and qvel_r < 5.0
        and xy_err <= 0.05
    )
    print(f"  [MUJOCO_CABLE_SMOKE] reset: frames={reset_frames} derive_err={derive_err:.5f} "
          f"(<=0.005, C-1 floor) dr_xy={dr_xy} xy_err={xy_err:.4f} com_z={com_z_r:.4f} "
          f"surf_min={surf_min_r:.4f} qvel={qvel_r:.4f} badqacc={badqacc_reset} "
          f"finite={finite_rs} reset_ok={reset_ok}")

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
    parser.add_argument("--solver-backend", type=str, default=SOLVER_BACKEND, choices=["vbd", "mujoco"],
                        help="Physics solver (Option-E Opt-1): vbd (default) | mujoco (articulated-arm smoke)")
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
    print(f"[NEWTON_CLIP_ROUTING] DT={DT:.6f}s ({int(1/DT)}Hz)")
    print(f"[NEWTON_CLIP_ROUTING] URDF: {FRANKA_URDF}")
    print(f"[NEWTON_CLIP_ROUTING] Architecture: VBD (Cosserat Rod cable + kinematic robot bodies)")
    print(f"[NEWTON_CLIP_ROUTING] Substeps: {SIM_SUBSTEPS}, SIM_DT={SIM_DT:.6f}s")
    print(f"[NEWTON_CLIP_ROUTING] VBD iterations: {VBD_ITERATIONS}")
    print(f"[NEWTON_CLIP_ROUTING] IK: Newton IKSolver (LM) on FK model")
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
    print(f"  [FK] Initial joint_q set from URDF home config, fingers open={FINGER_OPEN_POS*1000:.1f}mm")

    # Build physics scene (VBD cable + kinematic robot bodies positioned from FK)
    print("[BUILD] Building physics scene...")
    scene_info = build_scene(use_cable=use_cable, fk_model=fk_model, fk_state=fk_state,
                             solver_backend=solver_backend)
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
    from newton_skill_env_base import make_solver  # noqa: E402  (lazy: avoid circular import at load)
    solver = make_solver(model, backend=solver_backend,
                         enable_cable_contacts=(solver_backend == "mujoco" and use_cable))
    print(f"  [SOLVER] {solver_backend} solver created via make_solver")

    # Option-E mujoco smokes (the standalone gates; the full VBD episode below is NOT ported, S5-S7):
    # --no-cable -> the Opt-1 SC2b-part2 joint_q tracking smoke (K2 false-green gate, unchanged);
    # with cable -> the S4a cable-settle + curl-restore smoke (D-S4a-5, B2/B3 posture). Both exit.
    if solver_backend == "mujoco":
        if use_cable:
            _run_mujoco_cable_settle_smoke(model, solver, contacts, scene_info, fk_state,
                                           output_dir=args.output_dir)
        elif os.environ.get("S6_IK_MOTION_SMOKE") == "1":
            # S6 dual-arm IK-motion infra smoke (env-gated; the default --no-cable mujoco path keeps the
            # K2 tracking gate below UNCHANGED). sys.exit(0/2). (debate A3/H3; no new CLI arg, debate alt#5)
            _run_mujoco_ik_motion_smoke(model, solver, contacts, scene_info, fk_state,
                                        output_dir=args.output_dir)
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
                    print(f"  [CONTACT] {arm_label}_body{local} shape#{si}: "
                          f"ke={shape_ke[si]:.0f}, kd={shape_kd[si]:.0f}, mu={shape_mu[si]:.2f}")
                    break
    if cable_bodies:
        cb0 = cable_bodies[0]
        for si in range(model.shape_count):
            if shape_bodies_arr[si] == cb0:
                print(f"  [CONTACT] Cable body0 shape#{si}: "
                      f"ke={shape_ke[si]:.0f}, kd={shape_kd[si]:.0f}, mu={shape_mu[si]:.2f}")
                break

    # Video recorder
    recorder = VideoRecorder(args.output_dir, model, enabled=args.record_video,
                             scene_info=scene_info)
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
        print(f"[INIT] Cable settled: mean_z={cable_z:.4f}, mean_x={cable_x:.4f} "
              f"(drift={((cable_x - GRASP_X)*1000):.1f}mm, std={cable_x_std*1000:.1f}mm)")
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
        print(f"\n{'='*60}")
        print(f"  EPISODE {ep+1}/{args.num_episodes}")
        print(f"{'='*60}")

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
            if hasattr(solver, 'body_q_prev') and solver.body_q_prev is not None:
                solver.body_q_prev.assign(settled_body_q)
            if hasattr(solver, 'particle_q_prev') and solver.particle_q_prev is not None:
                solver.particle_q_prev.zero_()
            # Dahl friction state (if enabled)
            if hasattr(solver, 'joint_sigma_prev') and solver.joint_sigma_prev is not None:
                solver.joint_sigma_prev.zero_()
            if hasattr(solver, 'joint_kappa_prev') and solver.joint_kappa_prev is not None:
                solver.joint_kappa_prev.zero_()
            if hasattr(solver, 'joint_dkappa_prev') and solver.joint_dkappa_prev is not None:
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

            print(f"  [RESET] Scene restored to settled state")

        recorder.reset()

        try:
            state, ep_result = run_episode(model, state, scene_info, solver,
                                           contacts, ep)
        except Exception as e:
            print(f"\n  [ERROR] Episode {ep+1} crashed: {e}")
            import traceback
            traceback.print_exc()
            ep_result = {"episode": ep, "overall": "CRASH", "error": str(e)}

        # Fingertip penetration gate (z-check before finalizing verdict)
        pen = recorder.check_penetration()
        if pen and pen["penetration_detected"]:
            ep_result["penetration"] = pen
            print(f"  [ZCHECK] Fingertip penetration detected: "
                  f"{pen['max_penetration_mm']:.1f}mm below table "
                  f"({pen['penetration_pct']:.0f}% of frames)")
            if ep_result["overall"] == "PASS":
                ep_result["overall"] = "FAIL"
                ep_result["fail_reason"] = (
                    f"fingertip_penetration_{pen['max_penetration_mm']:.1f}mm"
                )

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

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  Pass rate: {all_results['pass_rate']}")
    print(f"  Overall: {all_results['overall']}")
    print(f"  Elapsed: {elapsed:.1f}s (sim={sim_elapsed_s}s, video={video_encode_s}s)")
    print(f"  Metrics: {metrics_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
