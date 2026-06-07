"""test_clip_routing.py — Wide-stance Clip1 push test (P1-P4).

Tests whether wide-stance grip coordinates can push cable into Clip1.
Uses DifferentialIK (DLS) for all arm movements.
Arm PD gains: FRANKA_PANDA_HIGH_PD_CFG (stiffness=400, damping=80).

Phase structure:
  P1: DiffIK approach (position) to cable X=0.30 → descend (pose) → velocity close
  P2: Micro-lift (grip confirmation)
  P3: DiffIK move from cable X=0.30 to Clip1 X=0.35
  P4: Both arms push down to Z=0.74 (40mm below clip top)

Wide-stance coordinates (Clip1-specific):
  Left:  (grasp=0.30/push=0.35, -0.170, approach=0.912, grasp=0.882, push=0.832)
  Right: (grasp=0.30/push=0.35, +0.070, approach=0.912, grasp=0.882, push=0.832)
"""
# === CLAUDE.md v25.03.17a CRITICAL RULES (DO NOT REMOVE) ===
# - write_joint_position_to_sim: FORBIDDEN
# - write_joint_state_to_sim: reset初期化のみ許可、ランタイム禁止
# - Finger: set_joint_velocity_target ONLY
# - Arm: set_joint_position_target + write_data_to_sim ONLY
# - IK: DifferentialIKController のみ。JT IK 廃止済み
# - No control method changes without rs approval
# - After conversation compacted: run `cat ~/IsaacLab/CLAUDE.md`
# ============================================================
from __future__ import annotations

import argparse
import faulthandler
import json
import math
import os
import signal
import shutil
import subprocess
import sys
import time
import traceback

# --- Test C: Signal handler for C++ crash isolation ---
# Must be registered BEFORE Isaac Sim / PhysX loads
faulthandler.enable()

def _crash_signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
    sys.stderr.write(f"\n[CRASH_HANDLER] Caught signal {sig_name} (signum={signum})\n")
    sys.stderr.write(f"[CRASH_HANDLER] Python traceback at crash:\n")
    traceback.print_stack(frame, file=sys.stderr)
    sys.stderr.flush()
    sys.stdout.write(f"\n[CRASH_HANDLER] Signal {sig_name} caught. See stderr for traceback.\n")
    sys.stdout.flush()
    os._exit(128 + signum)

# Register for common C++ crash signals
for _sig in (signal.SIGABRT, signal.SIGFPE, signal.SIGBUS):
    try:
        signal.signal(_sig, _crash_signal_handler)
    except (OSError, ValueError):
        pass
# SIGSEGV: faulthandler.enable() already handles this (prints C-level traceback)

# Force line-buffered stdout + duplicate to log file (pipe/tee independent)
_builtin_print = print
_log_file = None

def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _builtin_print(*args, **kwargs)
    if _log_file is not None:
        kwargs_f = dict(kwargs)
        kwargs_f['file'] = _log_file
        kwargs_f['flush'] = True
        _builtin_print(*args, **kwargs_f)

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--output_dir", type=str, default="data/test_widestance_clip1")
parser.add_argument("--headless", action="store_true", default=False)
parser.add_argument("--num_episodes", type=int, default=1)
parser.add_argument("--record_video", action="store_true", default=True)
parser.add_argument("--no_record_video", dest="record_video", action="store_false")
parser.add_argument("--p1_only", action="store_true", default=False,
                    help="Stop after P1 grasp + P2 micro-lift (skip P3/P4)")
parser.add_argument("--no_cable", action="store_true", default=False,
                    help="Test A: Remove cable from scene (crash isolation)")
parser.add_argument("--single_camera", action="store_true", default=False,
                    help="Test B: Use 1 camera instead of 5 (crash isolation)")
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, device=args.device,
                           enable_cameras=True, multi_gpu=False)
sim_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.sensors import CameraCfg

from isaaclab.actuators import ImplicitActuatorCfg
from thread_isaac_lab.envs.dual_arm_cfg import (
    DualArmTableCfg,
    SEGMENTED_CABLE_USD,
)
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    FINGER_GRIP_VEL, FINGER_OPEN_VEL,
    PANDA_HAND_DAMPING, PANDA_HAND_STIFFNESS,
    TABLE_HEIGHT,
    CABLE_SEG17_Y,
    ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ,
    CLIP_APPROACH_LEFT_JOINTS, CLIP_APPROACH_RIGHT_JOINTS,
    GRIPPER_INIT,
    CLIP1_X, CLIP1_Y, CLIP1_Z,
    CLIP2_X, CLIP2_Y, CLIP2_Z,
    CLIP_BASE_DEPTH,
)
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import matrix_from_quat, quat_inv, subtract_frame_transforms

# ===========================================================================
# Wide-stance coordinates (Clip1-specific)
# ===========================================================================
WIDE_X = 0.35           # Clip1 X position (for P3/P4)
GRASP_X = 0.30          # Cable initial X position (for P1 grasp)
WIDE_LEFT_Y = -0.170
WIDE_RIGHT_Y = +0.070
APPROACH_Z = 0.912      # hand_body Z: fingertip at 0.800 (cable+30mm)
GRASP_Z = 0.858         # hand_body Z: claw tip at ~0.749 (cable-6mm, table-1mm)
LIFT_Z = 0.912          # hand_body Z: fingertip at 0.800 (=APPROACH_Z)
PUSH_Z = 0.832          # hand_body Z: fingertip at 0.720 (clip底部=0.75-0.03)

# Hand-down orientation quaternion (w, x, y, z) — fingers pointing -Z
HAND_DOWN_QUAT_WXYZ = (0.0, 0.7071, 0.7071, 0.0)

# ---------------------------------------------------------------------------
# V-groove Franka configurations (URDF with finger_v_groove_60deg.stl)
# ---------------------------------------------------------------------------
VGROOVE_URDF = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/robots/panda_independent_fingers.urdf"


@configclass
class VGrooveLeftFrankaCfg(ArticulationCfg):
    """Left Franka with V-groove fingers. Arm PD: FRANKA_PANDA_HIGH_PD_CFG."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Left"

    spawn: sim_utils.UrdfFileCfg = sim_utils.UrdfFileCfg(
        asset_path=VGROOVE_URDF,
        fix_base=True,
        make_instanceable=False,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=16,
            solver_velocity_iteration_count=0,
        ),
        joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
            gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                stiffness=None, damping=None,
            )
        ),
    )

    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=ROBOT_LEFT_BASE,
        rot=ROBOT_BASE_QUAT_WXYZ,
        joint_pos={
            "panda_joint1": CLIP_APPROACH_LEFT_JOINTS[0],
            "panda_joint2": CLIP_APPROACH_LEFT_JOINTS[1],
            "panda_joint3": CLIP_APPROACH_LEFT_JOINTS[2],
            "panda_joint4": CLIP_APPROACH_LEFT_JOINTS[3],
            "panda_joint5": CLIP_APPROACH_LEFT_JOINTS[4],
            "panda_joint6": CLIP_APPROACH_LEFT_JOINTS[5],
            "panda_joint7": CLIP_APPROACH_LEFT_JOINTS[6],
            "panda_finger_joint.*": GRIPPER_INIT,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
        # Arm gains: FRANKA_PANDA_HIGH_PD_CFG (stiffness=400, damping=80)
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit=87.0,
            velocity_limit=2.175,
            stiffness=400.0,
            damping=80.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit=12.0,
            velocity_limit=2.61,
            stiffness=400.0,
            damping=80.0,
        ),
        # Hand: velocity mode (stiffness=0)
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit=200.0,
            velocity_limit=0.2,
            stiffness=PANDA_HAND_STIFFNESS,
            damping=PANDA_HAND_DAMPING,
        ),
    }


@configclass
class VGrooveRightFrankaCfg(ArticulationCfg):
    """Right Franka with V-groove fingers. Arm PD: FRANKA_PANDA_HIGH_PD_CFG."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Right"

    spawn: sim_utils.UrdfFileCfg = sim_utils.UrdfFileCfg(
        asset_path=VGROOVE_URDF,
        fix_base=True,
        make_instanceable=False,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=16,
            solver_velocity_iteration_count=0,
        ),
        joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
            gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                stiffness=None, damping=None,
            )
        ),
    )

    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=ROBOT_RIGHT_BASE,
        rot=ROBOT_BASE_QUAT_WXYZ,
        joint_pos={
            "panda_joint1": CLIP_APPROACH_RIGHT_JOINTS[0],
            "panda_joint2": CLIP_APPROACH_RIGHT_JOINTS[1],
            "panda_joint3": CLIP_APPROACH_RIGHT_JOINTS[2],
            "panda_joint4": CLIP_APPROACH_RIGHT_JOINTS[3],
            "panda_joint5": CLIP_APPROACH_RIGHT_JOINTS[4],
            "panda_joint6": CLIP_APPROACH_RIGHT_JOINTS[5],
            "panda_joint7": CLIP_APPROACH_RIGHT_JOINTS[6],
            "panda_finger_joint.*": GRIPPER_INIT,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
        # Arm gains: FRANKA_PANDA_HIGH_PD_CFG (stiffness=400, damping=80)
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit=87.0,
            velocity_limit=2.175,
            stiffness=400.0,
            damping=80.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit=12.0,
            velocity_limit=2.61,
            stiffness=400.0,
            damping=80.0,
        ),
        # Hand: velocity mode (stiffness=0)
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit=200.0,
            velocity_limit=0.2,
            stiffness=PANDA_HAND_STIFFNESS,
            damping=PANDA_HAND_DAMPING,
        ),
    }

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FINGERTIP_OFFSET = 0.1123
GRIPPER_OPEN = 0.04
SETTLE_STEPS = 80
LIFT_STEPS_PER_CM = 40
LIFT_SUBSTEPS = 4
N_SIM_PER_IK = 4       # sim steps per IK solve (approach/descend/move)
SLIP_THRESHOLD_MM = 3.0

CLIP_USD_PATH = "/home/rlrk/IsaacLab/data/clip/routing_clip_v1.usd"

# Video recording
VIDEO_CAPTURE_EVERY = 4  # capture every N sim steps (480Hz/4=120fps)


if args.single_camera:
    CAMERA_NAMES = ["front_camera"]
else:
    CAMERA_NAMES = ["overhead_camera", "front_camera", "back_camera", "left_camera", "right_camera"]


class FrameRecorder:
    """Captures frames from multiple cameras every N steps, encodes to MP4 via ffmpeg."""

    def __init__(self, output_dir: str, enabled: bool = False, capture_every: int = VIDEO_CAPTURE_EVERY):
        self.enabled = enabled
        self.capture_every = capture_every
        self.output_dir = output_dir
        self.step_count = 0
        self.frame_count = 0
        self._cameras = {}
        self._frames_dirs = {}
        if enabled:
            for name in CAMERA_NAMES:
                d = os.path.join(output_dir, f"_frames_{name}")
                os.makedirs(d, exist_ok=True)
                self._frames_dirs[name] = d

    def set_camera(self, scene):
        if self.enabled:
            for name in CAMERA_NAMES:
                try:
                    self._cameras[name] = scene[name]
                except KeyError:
                    print(f"  [VIDEO] Camera '{name}' not found in scene")

    def on_step(self):
        if not self.enabled or not self._cameras:
            self.step_count += 1
            return
        self.step_count += 1
        if self.step_count % self.capture_every != 0:
            return
        from PIL import Image
        for name, cam in self._cameras.items():
            try:
                rgb = cam.data.output["rgb"][0].cpu().numpy()
                if rgb.shape[-1] == 4:
                    rgb = rgb[:, :, :3]
                img = Image.fromarray(rgb.astype(np.uint8))
                img.save(os.path.join(self._frames_dirs[name], f"frame_{self.frame_count:06d}.png"))
            except Exception as e:
                if self.frame_count == 0:
                    print(f"  [VIDEO] Frame capture error ({name}): {e}")
        self.frame_count += 1

    def finalize(self, episode_idx: int) -> list[str]:
        if not self.enabled or self.frame_count == 0:
            return []
        video_paths = []
        fps = int(480 / self.capture_every)
        for name in CAMERA_NAMES:
            frames_dir = self._frames_dirs.get(name)
            if not frames_dir or not os.path.exists(frames_dir):
                continue
            video_path = os.path.join(self.output_dir, f"episode_{episode_idx}_{name}.mp4")
            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", os.path.join(frames_dir, "frame_%06d.png"),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", video_path,
            ]
            print(f"  [VIDEO] Encoding {self.frame_count} frames ({name}) → {video_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  [VIDEO] ffmpeg error ({name}): {result.stderr[:200]}")
                continue
            shutil.rmtree(frames_dir, ignore_errors=True)
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"  [VIDEO] Saved: {video_path} ({size_mb:.1f} MB)")
            video_paths.append(video_path)
            # Copy to ~/Downloads for easy access
            dl_dir = os.path.expanduser("~/Downloads")
            os.makedirs(dl_dir, exist_ok=True)
            dl_path = os.path.join(dl_dir, os.path.basename(video_path))
            shutil.copy2(video_path, dl_path)
            print(f"  [VIDEO] Copied: {dl_path}")
        return video_paths

    def reset(self):
        self.step_count = 0
        self.frame_count = 0
        if self.enabled:
            for name in CAMERA_NAMES:
                d = os.path.join(self.output_dir, f"_frames_{name}")
                if os.path.exists(d):
                    shutil.rmtree(d, ignore_errors=True)
                os.makedirs(d, exist_ok=True)
                self._frames_dirs[name] = d


# Global recorder
_recorder: FrameRecorder | None = None

# Clip1/Clip2 positions as tuples
CLIP1_POS = (CLIP1_X, CLIP1_Y, CLIP1_Z)
CLIP2_POS = (CLIP2_X, CLIP2_Y, CLIP2_Z)


# ---------------------------------------------------------------------------
# Scene Configuration
# ---------------------------------------------------------------------------
@configclass
class ClipRoutingSceneCfg(InteractiveSceneCfg):
    """Scene with 2 Franka arms, table, cable, and 2 routing clips."""

    num_envs: int = 1
    env_spacing: float = 5.0

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0)),
    )

    robot_left: VGrooveLeftFrankaCfg = VGrooveLeftFrankaCfg()
    robot_right: VGrooveRightFrankaCfg = VGrooveRightFrankaCfg()

    table: DualArmTableCfg = DualArmTableCfg()

    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=SEGMENTED_CABLE_USD,
            activate_contact_sensors=False,
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=1,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.30, CABLE_SEG17_Y, TABLE_HEIGHT + 0.02),
            rot=(0.7071, -0.7071, 0.0, 0.0),
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=5.0,
            ),
        },
    )

    clip1: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Clip1",
        spawn=UsdFileCfg(usd_path=CLIP_USD_PATH),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(CLIP1_X, CLIP1_Y, CLIP1_Z),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    clip2: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Clip2",
        spawn=UsdFileCfg(usd_path=CLIP_USD_PATH),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(CLIP2_X, CLIP2_Y, CLIP2_Z),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    # Camera target: Clip1 work area (0.35, -0.05, 0.78)
    # convention="world": forward=+X, up=+Z
    # Proven quaternions from POC (poc_single_arm_redball_gpt.py:3944-3989):
    #   look -Z (down): (0.7071, 0, 0.7071, 0) = 90° about Y
    #   look +Y:        (0.7071, 0, 0, 0.7071)  = 90° about Z
    #   look -Y:        (0.7071, 0, 0, -0.7071)  = -90° about Z
    #   look -X:        (0, 0, 0, 1)             = 180° about Z
    #   look +X:        (1, 0, 0, 0)             = identity

    # Overhead: top-down view of both hands, clip, cable
    overhead_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/OverheadCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=9.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.35, -0.05, 1.3),
            rot=(0.7071, 0.0, 0.7071, 0.0),  # look -Z (down)
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )

    # Front: from +X looking -X — V-guide/U-groove view
    front_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/FrontCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=12.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.80, -0.05, 0.85),
            rot=(0.0, 0.0, 0.0, 1.0),  # look -X
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )

    # Back: from -X looking +X — push descent Z-axis view
    back_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/BackCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=12.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(-0.10, -0.05, 0.85),
            rot=(1.0, 0.0, 0.0, 0.0),  # look +X (identity)
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )

    # Left: from -Y looking +Y — finger-cable contact, grip state
    left_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/LeftCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=12.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.35, -0.50, 0.85),
            rot=(0.7071, 0.0, 0.0, 0.7071),  # look +Y
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )

    # Right: from +Y looking -Y — grip from opposite side
    right_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/RightCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=12.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.35, 0.40, 0.85),
            rot=(0.7071, 0.0, 0.0, -0.7071),  # look -Y
            convention="world",
        ),
        width=640, height=480,
        data_types=["rgb"], update_period=0.0,
    )


def sim_step(sim, scene):
    """Wrapper: sim.step() + scene.update() + video frame capture."""
    sim.step()
    scene.update(sim.get_physics_dt())
    if _recorder:
        _recorder.on_step()


# ---------------------------------------------------------------------------
# DifferentialIK controller (DLS method)
# ---------------------------------------------------------------------------
ARM_JOINT_IDS = list(range(7))  # panda_joint1-7

def _make_diff_ik(device, num_envs=1, command_type="position"):
    """Create a DifferentialIK controller instance.

    command_type: "position" (3DOF, P1-APPROACH/P3/P4) or "pose" (6DOF, P1-DESCEND).
    """
    cfg = DifferentialIKControllerCfg(
        command_type=command_type,
        use_relative_mode=False,
        ik_method="dls",
        ik_params={"lambda_val": 0.01},
    )
    return DifferentialIKController(cfg, num_envs=num_envs, device=device)


def _diff_ik_step(robot, ik_ctrl, hand_body, jac_body, target_pos_w, device,
                  target_quat_w=None, nullspace_q0=None, nullspace_gain=0.3):
    """One DifferentialIK step. Returns arm joint targets (N, 7).

    target_pos_w: (N, 3) world-frame EE position target.
    target_quat_w: (N, 4) world-frame EE orientation target (w,x,y,z).
                   Required for pose mode, ignored for position mode.
    nullspace_q0: (N, 7) null space attractor joint positions. If provided,
                  applies null space projection to bias joints toward q0
                  without affecting task-space motion.
    nullspace_gain: float, strength of null space correction (0.0-1.0).
    """
    # Get EE pose in world frame
    ee_pose_w = robot.data.body_pose_w[:, hand_body]
    root_pose_w = robot.data.root_pose_w

    # Convert EE pose to body frame (required by DiffIK)
    ee_pos_b, ee_quat_b = subtract_frame_transforms(
        root_pose_w[:, 0:3], root_pose_w[:, 3:7],
        ee_pose_w[:, 0:3], ee_pose_w[:, 3:7],
    )

    # Convert target position to body frame
    if target_quat_w is not None:
        # Pose mode: transform both position and orientation to body frame
        tgt_pos_b, tgt_quat_b = subtract_frame_transforms(
            root_pose_w[:, 0:3], root_pose_w[:, 3:7],
            target_pos_w, target_quat_w,
        )
        # Pose command: (x, y, z, qw, qx, qy, qz)
        ik_ctrl.set_command(
            torch.cat([tgt_pos_b, tgt_quat_b], dim=-1),
            ee_pos=ee_pos_b, ee_quat=ee_quat_b,
        )
    else:
        # Position-only mode
        dummy_quat = ee_pose_w[:, 3:7]
        tgt_pos_b, _ = subtract_frame_transforms(
            root_pose_w[:, 0:3], root_pose_w[:, 3:7],
            target_pos_w, dummy_quat,
        )
        ik_ctrl.set_command(tgt_pos_b, ee_pos=ee_pos_b, ee_quat=ee_quat_b)

    # Get Jacobian in body frame
    jacobian = robot.root_physx_view.get_jacobians()[:, jac_body, :, ARM_JOINT_IDS]
    base_rot = root_pose_w[:, 3:7]
    base_rot_matrix = matrix_from_quat(quat_inv(base_rot))
    jacobian[:, :3, :] = torch.bmm(base_rot_matrix, jacobian[:, :3, :])
    jacobian[:, 3:, :] = torch.bmm(base_rot_matrix, jacobian[:, 3:, :])

    # Compute IK
    joint_pos = robot.data.joint_pos[:, ARM_JOINT_IDS]
    joint_pos_des = ik_ctrl.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

    # Null space projection: bias joints toward q0 without affecting EE
    # q_des += α * (I - J† @ J) @ (q0 - q_current)
    if nullspace_q0 is not None:
        J = jacobian  # (N, 6, 7) or (N, 3, 7)
        # DLS pseudo-inverse: J† = J^T (J J^T + λ²I)^{-1}
        lam = 0.01
        JJT = torch.bmm(J, J.transpose(1, 2))  # (N, M, M)
        eye_m = torch.eye(JJT.shape[-1], device=device).unsqueeze(0)
        JJT_reg = JJT + lam**2 * eye_m
        # Use solve instead of inverse for numerical stability
        # J_pinv = J^T @ (JJT + λ²I)^{-1}  →  solve: (JJT+λ²I) X = J  →  J_pinv = X^T
        X = torch.linalg.solve(JJT_reg, J)  # (N, M, 7)
        J_pinv = X.transpose(1, 2)  # (N, 7, M)
        # Null space projector: N = I - J† @ J
        eye_7 = torch.eye(7, device=device).unsqueeze(0)
        N_proj = eye_7 - torch.bmm(J_pinv, J)  # (N, 7, 7)
        # Null space correction (clamped to prevent large joint jumps)
        q_err = (nullspace_q0 - joint_pos).unsqueeze(-1)  # (N, 7, 1)
        q_null = torch.bmm(N_proj, q_err).squeeze(-1)  # (N, 7)
        q_null = torch.clamp(q_null, -0.05, 0.05)  # max 0.05 rad per step
        joint_pos_des = joint_pos_des + nullspace_gain * q_null

    return joint_pos_des


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_vel_l,
                  finger_vel_r, env_idx):
    """Apply arm position targets and independent finger velocity targets."""
    tgt_l = robot_left.data.joint_pos.clone()
    tgt_l[env_idx, :7] = ik_l[env_idx]
    robot_left.set_joint_position_target(tgt_l)
    vel_tgt_l = torch.zeros_like(robot_left.data.joint_pos)
    vel_tgt_l[env_idx, 7] = finger_vel_l
    vel_tgt_l[env_idx, 8] = finger_vel_l
    robot_left.set_joint_velocity_target(vel_tgt_l)
    robot_left.write_data_to_sim()

    tgt_r = robot_right.data.joint_pos.clone()
    tgt_r[env_idx, :7] = ik_r[env_idx]
    robot_right.set_joint_position_target(tgt_r)
    vel_tgt_r = torch.zeros_like(robot_right.data.joint_pos)
    vel_tgt_r[env_idx, 7] = finger_vel_r
    vel_tgt_r[env_idx, 8] = finger_vel_r
    robot_right.set_joint_velocity_target(vel_tgt_r)
    robot_right.write_data_to_sim()


def _apply_joints_symmetric(robot_left, robot_right, ik_l, ik_r, finger_vel,
                            env_idx):
    _apply_joints(robot_left, robot_right, ik_l, ik_r,
                  finger_vel, finger_vel, env_idx)


def _hold_position(sim, scene, robot_left, robot_right, finger_vel_l,
                   finger_vel_r, env_idx, n_steps):
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(n_steps):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l
        robot_left.set_joint_position_target(tgt_l)
        vel_tgt_l = torch.zeros_like(robot_left.data.joint_pos)
        vel_tgt_l[env_idx, 7] = finger_vel_l
        vel_tgt_l[env_idx, 8] = finger_vel_l
        robot_left.set_joint_velocity_target(vel_tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r
        robot_right.set_joint_position_target(tgt_r)
        vel_tgt_r = torch.zeros_like(robot_right.data.joint_pos)
        vel_tgt_r[env_idx, 7] = finger_vel_r
        vel_tgt_r[env_idx, 8] = finger_vel_r
        robot_right.set_joint_velocity_target(vel_tgt_r)
        robot_right.write_data_to_sim()

        sim_step(sim, scene)


def _hold_symmetric(sim, scene, robot_left, robot_right, finger_vel,
                    env_idx, n_steps):
    _hold_position(sim, scene, robot_left, robot_right,
                   finger_vel, finger_vel, env_idx, n_steps)


def get_grip_width(robot, env_idx=0):
    """Actual finger gap = j7 (finger_joint1) + j8 (finger_joint2), in mm."""
    j7 = robot.data.joint_pos[env_idx, 7].item()
    j8 = robot.data.joint_pos[env_idx, 8].item()
    return (j7 + j8) * 1000


def get_cable_midpoint(cable, env_idx=0):
    n_bodies = cable.data.body_pos_w.shape[1]
    mid_idx = n_bodies // 2
    return cable.data.body_pos_w[env_idx, mid_idx, :3].clone()


def check_cable_nan(cable):
    return torch.isnan(cable.data.body_pos_w).any().item()


def _ik_move_both(sim, scene, device, robot_left, robot_right,
                  hbl, hbr, jbl, jbr, target_l, target_r,
                  finger_vel, env_idx, label="MOVE",
                  n_steps=None, speed=None,
                  converge_mm=5.0, max_steps=4000,
                  command_type="position", target_quat_wxyz=None,
                  nullspace_gain=0.3, max_step_mm=1.5):
    """DifferentialIK move both arms simultaneously to target positions.

    target_l, target_r: (x, y, z) tuples for hand body position (world frame).
    command_type: "position" (3DOF) or "pose" (6DOF with orientation).
    target_quat_wxyz: (w,x,y,z) orientation target for pose mode (same for both arms).
    nullspace_gain: strength of null space projection (0=off, 0.3=default).
    Runs until both arms converge within converge_mm, or max_steps reached.
    """
    cable = None if args.no_cable else scene["cable"]

    # Create DiffIK controllers
    ik_ctrl_l = _make_diff_ik(device, command_type=command_type)
    ik_ctrl_r = _make_diff_ik(device, command_type=command_type)

    tgt_pos_l = robot_left.data.body_pos_w[:, hbl, :3].clone()
    tgt_pos_l[env_idx] = torch.tensor(target_l, device=device, dtype=torch.float32)
    tgt_pos_r = robot_right.data.body_pos_w[:, hbr, :3].clone()
    tgt_pos_r[env_idx] = torch.tensor(target_r, device=device, dtype=torch.float32)

    # Prepare orientation target for pose mode
    tgt_quat_w = None
    if command_type == "pose" and target_quat_wxyz is not None:
        n_envs = robot_left.data.body_pos_w.shape[0]
        tgt_quat_w = torch.tensor(
            target_quat_wxyz, device=device, dtype=torch.float32
        ).unsqueeze(0).expand(n_envs, -1)

    # Null space attractor: snapshot current joint positions before motion
    ns_q0_l = robot_left.data.joint_pos[:, ARM_JOINT_IDS].clone()
    ns_q0_r = robot_right.data.joint_pos[:, ARM_JOINT_IDS].clone()

    dist_l = torch.norm(tgt_pos_l[env_idx] - robot_left.data.body_pos_w[env_idx, hbl, :3]).item()
    dist_r = torch.norm(tgt_pos_r[env_idx] - robot_right.data.body_pos_w[env_idx, hbr, :3]).item()

    converge_m = converge_mm / 1000.0
    ns_label = f"ns={nullspace_gain}" if nullspace_gain > 0 else "no-ns"
    print(f"  [{label}] DiffIK(dls,{command_type},{ns_label},step={max_step_mm}mm) "
          f"dist L={dist_l*1000:.1f}mm R={dist_r*1000:.1f}mm "
          f"max_steps={max_steps} converge={converge_mm}mm")

    max_step_m = max_step_mm / 1000.0

    for step in range(max_steps):
        # Incremental target stepping: limit per-step IK target to max_step_mm from current EE
        ee_now_l = robot_left.data.body_pos_w[:, hbl, :3]
        ee_now_r = robot_right.data.body_pos_w[:, hbr, :3]
        delta_l = tgt_pos_l - ee_now_l
        delta_r = tgt_pos_r - ee_now_r
        dist_l_step = torch.norm(delta_l[env_idx]).item()
        dist_r_step = torch.norm(delta_r[env_idx]).item()

        step_tgt_l = tgt_pos_l.clone()
        step_tgt_r = tgt_pos_r.clone()
        if dist_l_step > max_step_m:
            step_tgt_l[env_idx] = ee_now_l[env_idx] + delta_l[env_idx] * (max_step_m / dist_l_step)
        if dist_r_step > max_step_m:
            step_tgt_r[env_idx] = ee_now_r[env_idx] + delta_r[env_idx] * (max_step_m / dist_r_step)

        # Compute IK with null space projection
        arm_joints_l = _diff_ik_step(robot_left, ik_ctrl_l, hbl, jbl, step_tgt_l, device,
                                     target_quat_w=tgt_quat_w,
                                     nullspace_q0=ns_q0_l if nullspace_gain > 0 else None,
                                     nullspace_gain=nullspace_gain)
        arm_joints_r = _diff_ik_step(robot_right, ik_ctrl_r, hbr, jbr, step_tgt_r, device,
                                     target_quat_w=tgt_quat_w,
                                     nullspace_q0=ns_q0_r if nullspace_gain > 0 else None,
                                     nullspace_gain=nullspace_gain)

        # Diagnostic: first 5 steps
        if step < 5:
            cur_l = robot_left.data.joint_pos[env_idx, :7]
            cur_r = robot_right.data.joint_pos[env_idx, :7]
            jdelta_l = arm_joints_l[env_idx] - cur_l
            jdelta_r = arm_joints_r[env_idx] - cur_r
            ee_pre_l = robot_left.data.body_pos_w[env_idx, hbl, :3]
            ee_pre_r = robot_right.data.body_pos_w[env_idx, hbr, :3]
            err_pre_l = (tgt_pos_l[env_idx] - ee_pre_l)
            err_pre_r = (tgt_pos_r[env_idx] - ee_pre_r)
            step_dist_l = dist_l_step * 1000
            step_dist_r = dist_r_step * 1000
            print(f"  [{label}] DIAG step={step} "
                  f"max_jdelta L={jdelta_l.abs().max().item():.6f}rad "
                  f"R={jdelta_r.abs().max().item():.6f}rad "
                  f"step_tgt_dist L={step_dist_l:.1f}mm R={step_dist_r:.1f}mm "
                  f"cart_err L=({err_pre_l[0]:.4f},{err_pre_l[1]:.4f},{err_pre_l[2]:.4f}) "
                  f"R=({err_pre_r[0]:.4f},{err_pre_r[1]:.4f},{err_pre_r[2]:.4f})")

        # Apply arm joints + finger velocity, then N_SIM_PER_IK physics steps
        _apply_joints(robot_left, robot_right, arm_joints_l, arm_joints_r,
                      finger_vel, finger_vel, env_idx)
        for sub in range(N_SIM_PER_IK):
            sim_step(sim, scene)

        if cable is not None and check_cable_nan(cable):
            print(f"  [{label}] Cable NaN at step {step}!")
            return False

        # Check convergence
        ee_l = robot_left.data.body_pos_w[env_idx, hbl, :3]
        ee_r = robot_right.data.body_pos_w[env_idx, hbr, :3]
        err_l = torch.norm(ee_l - tgt_pos_l[env_idx]).item()
        err_r = torch.norm(ee_r - tgt_pos_r[env_idx]).item()

        if step < 5:
            actual_l = robot_left.data.joint_pos[env_idx, :7]
            actual_r = robot_right.data.joint_pos[env_idx, :7]
            track_l = (arm_joints_l[env_idx] - actual_l).abs().max().item()
            track_r = (arm_joints_r[env_idx] - actual_r).abs().max().item()
            print(f"  [{label}] DIAG step={step} AFTER sim.step: "
                  f"ee_err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm "
                  f"PD_track_max L={track_l:.6f}rad R={track_r:.6f}rad")

        if step % 100 == 0:
            gl = get_grip_width(robot_left, env_idx)
            gr = get_grip_width(robot_right, env_idx)
            # Per-axis error for drift monitoring
            xe_l = abs(ee_l[0].item() - target_l[0]) * 1000
            xe_r = abs(ee_r[0].item() - target_r[0]) * 1000
            print(f"  [{label}] step={step} "
                  f"L=({ee_l[0]:.3f},{ee_l[1]:.3f},{ee_l[2]:.3f}) err={err_l*1000:.1f}mm Xdrift={xe_l:.1f}mm "
                  f"R=({ee_r[0]:.3f},{ee_r[1]:.3f},{ee_r[2]:.3f}) err={err_r*1000:.1f}mm Xdrift={xe_r:.1f}mm "
                  f"grip L={gl:.1f}mm R={gr:.1f}mm")

        if err_l < converge_m and err_r < converge_m:
            print(f"  [{label}] Converged at step {step}: "
                  f"err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm")
            break
    else:
        print(f"  [{label}] WARNING: not converged after {max_steps} steps "
              f"err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm")

    _hold_symmetric(sim, scene, robot_left, robot_right,
                    finger_vel, env_idx, SETTLE_STEPS)

    ee_final_l = robot_left.data.body_pos_w[env_idx, hbl, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hbr, :3]
    err_l = torch.norm(ee_final_l - tgt_pos_l[env_idx]).item()
    err_r = torch.norm(ee_final_r - tgt_pos_r[env_idx]).item()
    print(f"  [{label}] Final error: L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm")
    return True


# ---------------------------------------------------------------------------
# P1: Wide-stance approach + grasp
# ---------------------------------------------------------------------------
def do_widestance_grasp(sim, scene, device, env_idx=0):
    """DiffIK approach to wide-stance positions, descend, velocity-close.

    1. DiffIK(position) approach to (GRASP_X, WIDE_Y, APPROACH_Z)
    2. DiffIK(pose) descend to GRASP_Z with hand-down orientation
    3. Velocity-close grippers
    """
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = None if args.no_cable else scene["cable"]

    # Find body indices
    hand_body_left = robot_left.find_bodies("panda_hand")[0][0]
    hand_body_right = robot_right.find_bodies("panda_hand")[0][0]
    jac_body_left = hand_body_left - 1
    jac_body_right = hand_body_right - 1

    hbl, hbr = hand_body_left, hand_body_right
    jbl, jbr = jac_body_left, jac_body_right

    # --- Diagnostic: initial EE and cable positions ---
    ee_l = robot_left.data.body_pos_w[:, hbl, :3]
    ee_r = robot_right.data.body_pos_w[:, hbr, :3]
    print(f"  [P1-INIT] EE: L=({ee_l[0,0]:.4f},{ee_l[0,1]:.4f},{ee_l[0,2]:.4f}) "
          f"R=({ee_r[0,0]:.4f},{ee_r[0,1]:.4f},{ee_r[0,2]:.4f})")

    # Safety check: panda_hand Z must be above table + margin before DiffIK starts
    for side, ee in [("LEFT", ee_l), ("RIGHT", ee_r)]:
        ee_z = ee[0, 2].item()
        assert ee_z > TABLE_HEIGHT + 0.02, (
            f"SAFETY: {side} panda_hand Z={ee_z:.4f} below table+2cm "
            f"(TABLE={TABLE_HEIGHT}). Init joints are wrong!"
        )
    print(f"  [P1-INIT] Safety OK: both hands above table+2cm")

    if cable is not None:
        n_seg = cable.data.body_pos_w.shape[1]
        print(f"  [P1-DIAG] Cable segments ({n_seg}):")
        for si in range(n_seg):
            sx, sy, sz = cable.data.body_pos_w[0, si].tolist()
            print(f"    seg{si}: ({sx:.4f}, {sy:.4f}, {sz:.4f})")

        # Check cable Y range vs grip Y
        cable_ys = cable.data.body_pos_w[0, :, 1].tolist()
        cable_y_min, cable_y_max = min(cable_ys), max(cable_ys)
        print(f"  [P1-DIAG] Cable Y range: [{cable_y_min:.4f}, {cable_y_max:.4f}]")
        print(f"  [P1-DIAG] Grip Y: L={WIDE_LEFT_Y} R={WIDE_RIGHT_Y}")
        if WIDE_LEFT_Y < cable_y_min - 0.02 or WIDE_RIGHT_Y > cable_y_max + 0.02:
            print(f"  [P1-WARN] Grip Y outside cable range!")
    else:
        print(f"  [P1-DIAG] Cable: REMOVED (--no_cable isolation test)")

    # --- Step 1: DiffIK move to approach position (at cable X=0.30) ---
    print(f"\n  [P1-APPROACH] Moving to cable-X approach: "
          f"L=({GRASP_X},{WIDE_LEFT_Y},{APPROACH_Z}) R=({GRASP_X},{WIDE_RIGHT_Y},{APPROACH_Z})")

    ok = _ik_move_both(sim, scene, device, robot_left, robot_right,
                       hbl, hbr, jbl, jbr,
                       (GRASP_X, WIDE_LEFT_Y, APPROACH_Z),
                       (GRASP_X, WIDE_RIGHT_Y, APPROACH_Z),
                       0.0, env_idx, label="P1-APPROACH")
    if not ok:
        return {"pass": False, "fail": "approach_cable_nan"}

    # --- Step 2: Descend to GRASP_Z (pose mode: maintain hand-down orientation) ---
    print(f"\n  [P1-DESCEND] Descending to Z={GRASP_Z} (pose mode, quat={HAND_DOWN_QUAT_WXYZ})")
    ok = _ik_move_both(sim, scene, device, robot_left, robot_right,
                       hbl, hbr, jbl, jbr,
                       (GRASP_X, WIDE_LEFT_Y, GRASP_Z),
                       (GRASP_X, WIDE_RIGHT_Y, GRASP_Z),
                       0.0, env_idx, label="P1-DESCEND",
                       command_type="pose",
                       target_quat_wxyz=HAND_DOWN_QUAT_WXYZ)
    if not ok:
        return {"pass": False, "fail": "descend_cable_nan"}

    # --- Step 3: Set finger damping and velocity-close ---
    TEST_DAMPING = 20000.0
    finger_joint_ids = [7, 8]
    for rob, name in [(robot_left, "LEFT"), (robot_right, "RIGHT")]:
        rob.write_joint_damping_to_sim(
            torch.tensor([[TEST_DAMPING, TEST_DAMPING]], device=device),
            joint_ids=finger_joint_ids,
        )
        actual = rob.data.joint_damping[0, finger_joint_ids].tolist()
        print(f"  [P1-GRASP] {name} finger damping set={TEST_DAMPING} actual={actual}")

    finger_vel = FINGER_GRIP_VEL
    VEL_CLOSE_THRESH = 0.006  # 6mm
    VEL_CLOSE_MAX_STEPS = 2500
    VEL_CLOSE_LOG_INTERVAL = 100

    grip_l_init = robot_left.data.joint_pos[env_idx, 7].item()
    grip_r_init = robot_right.data.joint_pos[env_idx, 7].item()
    print(f"  [P1-GRASP] Velocity close from L={grip_l_init*1000:.1f}mm R={grip_r_init*1000:.1f}mm")

    # Balanced close: if one finger (j7/j8) leads the other by >2mm,
    # pause the leading finger to keep them symmetric.
    BALANCE_THRESH = 0.002  # 2mm imbalance threshold

    # Lock arm joints at pre-close position to prevent X/Y drift from cable reaction forces
    arm_lock_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_lock_r = robot_right.data.joint_pos[env_idx, :7].clone()

    for s in range(VEL_CLOSE_MAX_STEPS):
        # Per-robot balanced velocity control
        for rob, arm_lock in [(robot_left, arm_lock_l), (robot_right, arm_lock_r)]:
            j7 = rob.data.joint_pos[env_idx, 7].item()
            j8 = rob.data.joint_pos[env_idx, 8].item()
            tgt = rob.data.joint_pos.clone()
            tgt[env_idx, :7] = arm_lock  # Fixed arm target (not current pos)
            rob.set_joint_position_target(tgt)
            vel = torch.zeros_like(rob.data.joint_pos)
            diff = j7 - j8  # positive = j7 more open than j8
            if abs(diff) > BALANCE_THRESH:
                # Only close the more-open finger
                if diff > 0:
                    vel[env_idx, 7] = finger_vel  # close j7
                    vel[env_idx, 8] = 0.0          # pause j8
                else:
                    vel[env_idx, 7] = 0.0          # pause j7
                    vel[env_idx, 8] = finger_vel   # close j8
            else:
                vel[env_idx, 7] = finger_vel
                vel[env_idx, 8] = finger_vel
            rob.set_joint_velocity_target(vel)
            rob.write_data_to_sim()
        sim_step(sim, scene)

        # Actual finger gap = j7 + j8 (both finger joints)
        grip_l = (robot_left.data.joint_pos[env_idx, 7].item()
                  + robot_left.data.joint_pos[env_idx, 8].item())
        grip_r = (robot_right.data.joint_pos[env_idx, 7].item()
                  + robot_right.data.joint_pos[env_idx, 8].item())

        if s % VEL_CLOSE_LOG_INTERVAL == 0 and s > 0:
            j7l = robot_left.data.joint_pos[env_idx, 7].item()
            j8l = robot_left.data.joint_pos[env_idx, 8].item()
            j7r = robot_right.data.joint_pos[env_idx, 7].item()
            j8r = robot_right.data.joint_pos[env_idx, 8].item()
            print(f"  [P1-GRASP] step {s}: L={grip_l*1000:.1f}mm(j7={j7l*1000:.1f},j8={j8l*1000:.1f}) "
                  f"R={grip_r*1000:.1f}mm(j7={j7r*1000:.1f},j8={j8r*1000:.1f})")

        if grip_l <= VEL_CLOSE_THRESH and grip_r <= VEL_CLOSE_THRESH:
            print(f"  [P1-GRASP] Converged at step {s}: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")
            break

    grip_l_final = (robot_left.data.joint_pos[0, 7].item()
                    + robot_left.data.joint_pos[0, 8].item())
    grip_r_final = (robot_right.data.joint_pos[0, 7].item()
                    + robot_right.data.joint_pos[0, 8].item())
    grip_l_mm = round(grip_l_final * 1000, 2)
    grip_r_mm = round(grip_r_final * 1000, 2)

    # Check: grip > 2.5mm means cable is between fingers
    grip_ok = grip_l_final > 0.0025 and grip_r_final > 0.0025
    print(f"  [P1-GRASP] Final: L={grip_l_mm}mm R={grip_r_mm}mm grip_ok={grip_ok}")

    # --- H4-DIAG: finger vs cable Y-position at P1 completion ---
    j7_l = robot_left.data.joint_pos[env_idx, 7].item()
    j8_l = robot_left.data.joint_pos[env_idx, 8].item()
    j7_r = robot_right.data.joint_pos[env_idx, 7].item()
    j8_r = robot_right.data.joint_pos[env_idx, 8].item()
    ee_l = robot_left.data.body_pos_w[env_idx, hbl, :3].tolist()
    ee_r = robot_right.data.body_pos_w[env_idx, hbr, :3].tolist()
    print(f"  [H4-DIAG] P1-END L: j7={j7_l*1000:.2f}mm j8={j8_l*1000:.2f}mm hand=({ee_l[0]:.4f},{ee_l[1]:.4f},{ee_l[2]:.4f})")
    print(f"  [H4-DIAG] P1-END R: j7={j7_r*1000:.2f}mm j8={j8_r*1000:.2f}mm hand=({ee_r[0]:.4f},{ee_r[1]:.4f},{ee_r[2]:.4f})")
    if cable is not None:
        n_seg = cable.data.body_pos_w.shape[1]
        cable_positions = []
        for si in range(n_seg):
            cx, cy, cz = cable.data.body_pos_w[env_idx, si].tolist()
            cable_positions.append((cx, cy, cz))
            dist_l_y = abs(cy - ee_l[1])
            dist_r_y = abs(cy - ee_r[1])
            print(f"  [H4-DIAG] seg{si}: ({cx:.4f},{cy:.4f},{cz:.4f}) "
                  f"dY_L={dist_l_y*1000:.1f}mm dY_R={dist_r_y*1000:.1f}mm")
    else:
        print(f"  [H4-DIAG] Cable: REMOVED (--no_cable)")

    return {
        "finger_vel": finger_vel,
        "hand_body_left": hbl,
        "hand_body_right": hbr,
        "jac_body_left": jbl,
        "jac_body_right": jbr,
        "grip_l_mm": grip_l_mm,
        "grip_r_mm": grip_r_mm,
        "pass": True,  # Always proceed to lift — claw catch is verified by P2 cable_z_delta
    }


# ---------------------------------------------------------------------------
# P2: Micro-lift (grip confirmation)
# ---------------------------------------------------------------------------
def do_microlift(sim, scene, device, hbl, hbr, jbl, jbr,
                 finger_vel, env_idx=0):
    """Lift both arms from GRASP_Z to LIFT_Z (30mm micro-lift)."""
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = None if args.no_cable else scene["cable"]

    cable_z_before = cable.data.body_pos_w[env_idx, :, 2].mean().item() if cable is not None else 0.0

    LIFT_FINGER_VEL = -0.02  # stronger during lift

    # --- H3-DIAG: Verify damping persists at P2 start ---
    for rob, name in [(robot_left, "LEFT"), (robot_right, "RIGHT")]:
        damp = rob.data.joint_damping[0, 7:9].tolist()
        stiff = rob.data.joint_stiffness[0, 7:9].tolist()
        print(f"  [H3-DIAG] P2-start {name}: damping j7,j8={damp} stiffness={stiff}")

    print(f"  [P2-LIFT] Micro-lift: Z {GRASP_Z} → {LIFT_Z} (+{(LIFT_Z-GRASP_Z)*1000:.0f}mm)")

    # Position mode (3DOF): Z-only lift does not need orientation tracking.
    # Null space OFF: null space projection was fighting Z motion (0.005mm/step → ~0).
    # max_step_mm=5.0: 1.5mm was overly conservative for pure Z movement.
    ok = _ik_move_both(sim, scene, device, robot_left, robot_right,
                       hbl, hbr, jbl, jbr,
                       (GRASP_X, WIDE_LEFT_Y, LIFT_Z),
                       (GRASP_X, WIDE_RIGHT_Y, LIFT_Z),
                       LIFT_FINGER_VEL, env_idx, label="P2-LIFT",
                       command_type="position",
                       nullspace_gain=0.0,
                       max_step_mm=5.0)
    if not ok:
        print(f"  [P2-LIFT] IK move failed (NaN)")

    # Log final hand positions for X drift check
    hl = robot_left.data.body_pos_w[env_idx, hbl, :3]
    hr = robot_right.data.body_pos_w[env_idx, hbr, :3]
    print(f"  [P2-LIFT] Final handX L={hl[0]:.4f} R={hr[0]:.4f} "
          f"(target={GRASP_X}, drift L={abs(hl[0].item()-GRASP_X)*1000:.1f}mm "
          f"R={abs(hr[0].item()-GRASP_X)*1000:.1f}mm)")

    _hold_symmetric(sim, scene, robot_left, robot_right,
                    LIFT_FINGER_VEL, env_idx, SETTLE_STEPS)

    cable_z_after = cable.data.body_pos_w[env_idx, :, 2].mean().item() if cable is not None else 0.0
    cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)
    gl = get_grip_width(robot_left, env_idx)
    gr = get_grip_width(robot_right, env_idx)
    print(f"  [P2-LIFT] cable_z_delta={cable_z_delta_mm}mm grip L={gl:.1f}mm R={gr:.1f}mm")

    return {
        "cable_z_delta_mm": cable_z_delta_mm,
        "grip_l_mm": round(gl, 2),
        "grip_r_mm": round(gr, 2),
        "pass": cable_z_delta_mm > 5.0 if cable is not None else True,
    }


# ---------------------------------------------------------------------------
# P4: Push both arms down to PUSH_Z
# ---------------------------------------------------------------------------
def do_push_both(sim, scene, device, hbl, hbr, jbl, jbr,
                 finger_vel, env_idx=0):
    """Both arms descend simultaneously to PUSH_Z.

    This pushes the cable into Clip1's V-guide and U-groove.
    """
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = None if args.no_cable else scene["cable"]

    PUSH_FINGER_VEL = -0.02  # maintain strong grip during push
    _ik_ctrl_l = _make_diff_ik(device)
    _ik_ctrl_r = _make_diff_ik(device)

    ee_start_l = robot_left.data.body_pos_w[:, hbl, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hbr, :3].clone()

    # Target: same XY, descend Z to PUSH_Z
    target_l = (ee_start_l[env_idx, 0].item(), ee_start_l[env_idx, 1].item(), PUSH_Z)
    target_r = (ee_start_r[env_idx, 0].item(), ee_start_r[env_idx, 1].item(), PUSH_Z)

    dz = PUSH_Z - ee_start_l[env_idx, 2].item()
    n_steps = max(int(abs(dz) * 100 * LIFT_STEPS_PER_CM), 50)

    print(f"  [P4-PUSH] Both arms descending to Z={PUSH_Z} "
          f"(dZ={dz*1000:.1f}mm, steps={n_steps})")
    print(f"  [P4-PUSH] Target L=({target_l[0]:.3f},{target_l[1]:.3f},{target_l[2]:.3f}) "
          f"R=({target_r[0]:.3f},{target_r[1]:.3f},{target_r[2]:.3f})")

    cable_z_before = cable.data.body_pos_w[env_idx, :, 2].mean().item() if cable is not None else 0.0

    tgt_pos_l = ee_start_l.clone()
    tgt_pos_l[env_idx] = torch.tensor(target_l, device=device, dtype=torch.float32)
    tgt_pos_r = ee_start_r.clone()
    tgt_pos_r[env_idx] = torch.tensor(target_r, device=device, dtype=torch.float32)

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)
        ee_tgt_l = ee_start_l + (tgt_pos_l - ee_start_l) * t
        ee_tgt_r = ee_start_r + (tgt_pos_r - ee_start_r) * t

        ik_l = _diff_ik_step(robot_left, _ik_ctrl_l, hbl, jbl, ee_tgt_l, device)
        ik_r = _diff_ik_step(robot_right, _ik_ctrl_r, hbr, jbr, ee_tgt_r, device)

        _apply_joints_symmetric(robot_left, robot_right, ik_l, ik_r,
                                PUSH_FINGER_VEL, env_idx)
        for _ in range(LIFT_SUBSTEPS):
            sim_step(sim, scene)

        if cable is not None and check_cable_nan(cable):
            print(f"  [P4-PUSH] Cable NaN at step {step}!")
            return {"pass": False, "cable_nan": True}

        if step % max(n_steps // 10, 1) == 0:
            cable_z = cable.data.body_pos_w[env_idx, :, 2].min().item() if cable is not None else 0.0
            gl = get_grip_width(robot_left, env_idx)
            gr = get_grip_width(robot_right, env_idx)
            ee_l = robot_left.data.body_pos_w[env_idx, hbl, :3]
            ee_r = robot_right.data.body_pos_w[env_idx, hbr, :3]
            print(f"  [P4-PUSH] step={step}/{n_steps} "
                  f"EE_Z L={ee_l[2]:.4f} R={ee_r[2]:.4f} "
                  f"cable_z_min={cable_z:.4f} "
                  f"grip L={gl:.1f}mm R={gr:.1f}mm")

            # Grip loss check
            if gl < 1.0 and gr < 1.0:
                print(f"  [P4-PUSH] GRIP LOSS at step {step}!")
                break

    _hold_symmetric(sim, scene, robot_left, robot_right,
                    PUSH_FINGER_VEL, env_idx, SETTLE_STEPS * 2)

    # --- Final diagnostics ---
    cable_z_after = cable.data.body_pos_w[env_idx, :, 2].mean().item() if cable is not None else 0.0
    cable_z_min = cable.data.body_pos_w[env_idx, :, 2].min().item() if cable is not None else 0.0
    cable_z_delta_mm = round((cable_z_after - cable_z_before) * 1000, 2)

    # Clip1 groove geometry
    clip_top_z = CLIP1_Z + 0.030  # base_height + groove
    clip_groove_z = CLIP1_Z + 0.005  # base only
    cable_in_groove = cable_z_min < clip_top_z

    gl = get_grip_width(robot_left, env_idx)
    gr = get_grip_width(robot_right, env_idx)
    ee_l = robot_left.data.body_pos_w[env_idx, hbl, :3]
    ee_r = robot_right.data.body_pos_w[env_idx, hbr, :3]

    print(f"  [P4-PUSH] Final EE: L=({ee_l[0]:.4f},{ee_l[1]:.4f},{ee_l[2]:.4f}) "
          f"R=({ee_r[0]:.4f},{ee_r[1]:.4f},{ee_r[2]:.4f})")
    print(f"  [P4-PUSH] cable_z_min={cable_z_min:.4f} clip_top_z={clip_top_z:.4f} "
          f"in_groove={cable_in_groove}")
    print(f"  [P4-PUSH] cable_z_delta={cable_z_delta_mm}mm")
    print(f"  [P4-PUSH] grip L={gl:.1f}mm R={gr:.1f}mm")

    # Check hand collision (distance between EE Y positions)
    hand_sep_mm = abs(ee_l[1].item() - ee_r[1].item()) * 1000
    print(f"  [P4-PUSH] Hand separation: {hand_sep_mm:.1f}mm")

    # Cable segment positions near clip
    if cable is not None:
        print(f"  [P4-PUSH] Cable segments (final):")
        n_seg = cable.data.body_pos_w.shape[1]
        for si in range(n_seg):
            sx, sy, sz = cable.data.body_pos_w[0, si].tolist()
            # Mark segments near clip1
            near_clip = abs(sy - CLIP1_Y) < 0.05
            marker = " ← near Clip1" if near_clip else ""
            print(f"    seg{si}: ({sx:.4f}, {sy:.4f}, {sz:.4f}){marker}")
    else:
        print(f"  [P4-PUSH] Cable: REMOVED (--no_cable)")

    return {
        "cable_z_min": round(cable_z_min, 4),
        "cable_z_delta_mm": cable_z_delta_mm,
        "cable_in_groove": cable_in_groove,
        "grip_l_mm": round(gl, 2),
        "grip_r_mm": round(gr, 2),
        "hand_sep_mm": round(hand_sep_mm, 2),
        "pass": cable_in_groove and gl > 1.0 and gr > 1.0,
    }


# ---------------------------------------------------------------------------
# run_episode: P1-P4 wide-stance clip1 push
# ---------------------------------------------------------------------------
def run_episode(sim, scene, device, episode_idx, output_dir):
    """P1-P4 wide-stance clip1 push test."""
    env_idx = 0
    results = {"episode": episode_idx, "overall": "FAIL"}

    # === P1: Wide-stance Grasp ===
    print(f"\n  {'='*50}")
    print(f"  [P1] Wide-Stance Grasp (DiffIK approach)")
    print(f"  {'='*50}")
    grasp = do_widestance_grasp(sim, scene, device, env_idx)
    results["P1_grasp"] = grasp
    if not grasp["pass"]:
        results["fail_reason"] = "P1_grip_fail"
        return results

    finger_vel = grasp["finger_vel"]
    hbl = grasp["hand_body_left"]
    hbr = grasp["hand_body_right"]
    jbl = grasp["jac_body_left"]
    jbr = grasp["jac_body_right"]

    # === P2: Micro-lift ===
    print(f"\n  {'='*50}")
    print(f"  [P2] Micro-Lift (grip confirmation)")
    print(f"  {'='*50}")
    lift = do_microlift(sim, scene, device, hbl, hbr, jbl, jbr,
                        finger_vel, env_idx)
    results["P2_lift"] = lift
    if not lift["pass"]:
        results["fail_reason"] = "P2_lift_insufficient"
        print(f"  [P2] WARN: lift={lift['cable_z_delta_mm']}mm, continuing anyway")

    if args.p1_only:
        if lift["pass"]:
            results["overall"] = "PASS"
        print(f"  [--p1_only] Stopping after P2. Overall={results['overall']}")
        return results

    # === P3: Move from cable X=0.30 to Clip1 X=0.35 ===
    print(f"\n  {'='*50}")
    print(f"  [P3] Move to Clip1 X ({GRASP_X} → {WIDE_X})")
    print(f"  {'='*50}")
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    ee_l = robot_left.data.body_pos_w[env_idx, hbl, :3]
    ee_r = robot_right.data.body_pos_w[env_idx, hbr, :3]
    p3_ok = _ik_move_both(sim, scene, device, robot_left, robot_right,
                          hbl, hbr, jbl, jbr,
                          (WIDE_X, ee_l[1].item(), ee_l[2].item()),
                          (WIDE_X, ee_r[1].item(), ee_r[2].item()),
                          finger_vel, env_idx, label="P3-MOVE",
                          converge_mm=5.0, max_steps=2000)
    results["P3_move"] = {"pass": p3_ok}
    if not p3_ok:
        results["fail_reason"] = "P3_move_fail"

    # === P4: Push both arms down ===
    print(f"\n  {'='*50}")
    print(f"  [P4] Push Both Arms to Z={PUSH_Z}")
    print(f"  {'='*50}")
    push = do_push_both(sim, scene, device, hbl, hbr, jbl, jbr,
                        finger_vel, env_idx)
    results["P4_push"] = push

    # Final assessment
    if push["pass"]:
        results["overall"] = "PASS"
    else:
        results["overall"] = "FAIL"
        results["fail_reason"] = "P4_push_fail"

    return results


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    global _recorder, _log_file
    device = f"cuda:{app_launcher.device_id}"
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Open log file for direct write (independent of pipe/tee)
    _log_file = open(os.path.join(output_dir, "run.log"), "w")

    print(f"[WIDESTANCE_CLIP1] Device={device}")
    print(f"[WIDESTANCE_CLIP1] Wide-stance: L=({WIDE_X},{WIDE_LEFT_Y}) R=({WIDE_X},{WIDE_RIGHT_Y})")
    print(f"[WIDESTANCE_CLIP1] Approach_Z={APPROACH_Z} Grasp_Z={GRASP_Z} Lift_Z={LIFT_Z} Push_Z={PUSH_Z}")
    print(f"[WIDESTANCE_CLIP1] Clip1=({CLIP1_X},{CLIP1_Y},{CLIP1_Z})")
    print(f"[WIDESTANCE_CLIP1] Clip USD={CLIP_USD_PATH}")
    print(f"[WIDESTANCE_CLIP1] Finger: V-groove 60deg (URDF)")
    print(f"[WIDESTANCE_CLIP1] Base: L={ROBOT_LEFT_BASE} R={ROBOT_RIGHT_BASE}")
    if args.record_video:
        print(f"[WIDESTANCE_CLIP1] Video recording ENABLED (5 cameras, every {VIDEO_CAPTURE_EVERY} steps)")

    scene_cfg = ClipRoutingSceneCfg(num_envs=1, env_spacing=5.0)

    # Test A: Remove cable from scene
    if args.no_cable:
        print("[ISOLATION] Test A: --no_cable → removing cable from scene")
        scene_cfg.cable = None
    # Test B: Single camera
    if args.single_camera:
        print("[ISOLATION] Test B: --single_camera → keeping front_camera only")
        scene_cfg.overhead_camera = None
        scene_cfg.back_camera = None
        scene_cfg.left_camera = None
        scene_cfg.right_camera = None

    physx_cfg = sim_utils.PhysxCfg(
        solver_type=0,
        max_position_iteration_count=32,
        max_velocity_iteration_count=1,
        bounce_threshold_velocity=0.5,
        enable_stabilization=True,
    )
    sim_cfg = sim_utils.SimulationCfg(
        device=device,
        dt=PHYSICS_DT,
        physx=physx_cfg,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)

    sim.reset()
    scene.reset()
    # Apply init_state joint positions (scene.reset() does NOT write them to sim)
    for robot_key in ("robot_left", "robot_right"):
        rob = scene[robot_key]
        rob.write_joint_state_to_sim(
            rob.data.default_joint_pos, rob.data.default_joint_vel
        )
        # Sync PD position target so controller doesn't fight init pose
        rob.set_joint_position_target(rob.data.default_joint_pos)
        rob.write_data_to_sim()  # Send PD targets to PhysX
    # Stabilize: let PD settle at init pose before DiffIK starts
    for _ in range(50):
        sim.step()
        scene.update(sim.cfg.dt)
    print(f"[INIT] PD stabilized (50 steps)")

    _recorder = FrameRecorder(output_dir, enabled=args.record_video)
    _recorder.set_camera(scene)

    all_results = {
        "test": "widestance_clip1_push",
        "wide_stance": {
            "left": {"x": WIDE_X, "y": WIDE_LEFT_Y},
            "right": {"x": WIDE_X, "y": WIDE_RIGHT_Y},
        },
        "clip1_pos": list(CLIP1_POS),
        "approach_z": APPROACH_Z,
        "grasp_z": GRASP_Z,
        "lift_z": LIFT_Z,
        "push_z": PUSH_Z,
        "device": device,
        "episodes": [],
        "n_pass": 0,
        "n_fail": 0,
    }

    start_time = time.time()

    for ep in range(args.num_episodes):
        print(f"\n{'='*60}")
        print(f"  EPISODE {ep+1}/{args.num_episodes}")
        print(f"{'='*60}")

        sim.reset()
        scene.reset()
        # Apply init_state joint positions (scene.reset() does NOT write them to sim)
        for robot_key in ("robot_left", "robot_right"):
            rob = scene[robot_key]
            rob.write_joint_state_to_sim(
                rob.data.default_joint_pos, rob.data.default_joint_vel
            )
            # Sync PD position target so controller doesn't fight init pose
            rob.set_joint_position_target(rob.data.default_joint_pos)
            rob.write_data_to_sim()  # Send PD targets to PhysX
        # Stabilize: let PD settle at init pose before DiffIK starts
        for _ in range(50):
            sim.step()
            scene.update(sim.cfg.dt)
        _recorder.reset()

        try:
            ep_result = run_episode(sim, scene, device, ep, output_dir)
        except Exception as e:
            print(f"\n  [ERROR] Episode {ep+1} crashed: {e}")
            ep_result = {"episode": ep, "overall": "CRASH", "error": str(e)}
        all_results["episodes"].append(ep_result)

        # Always encode video (even on crash — partial frames are useful)
        try:
            video_paths = _recorder.finalize(ep)
            if video_paths:
                ep_result["video_paths"] = video_paths
        except Exception as e:
            print(f"  [VIDEO] finalize error: {e}")

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

    # Always save RUN_METRICS (even partial)
    _save_metrics(all_results, output_dir, elapsed)


def _save_metrics(all_results, output_dir, elapsed):
    """Save RUN_METRICS.json — called from main and from finally block."""
    metrics_path = os.path.join(output_dir, "RUN_METRICS.json")
    try:
        with open(metrics_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n[WIDESTANCE_CLIP1] Results saved to {metrics_path}")
    except Exception as e:
        print(f"[WIDESTANCE_CLIP1] Failed to save metrics: {e}")

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  Pass rate: {all_results.get('pass_rate', 'N/A')}")
    print(f"  Overall: {all_results.get('overall', 'UNKNOWN')}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _builtin_print(f"[FATAL] main() exception: {e}", flush=True)
    finally:
        # Flush and close log file before shutdown
        if _log_file is not None:
            try:
                _log_file.flush()
                _log_file.close()
            except Exception:
                pass
        sim_app.close()
        # Isaac Sim sometimes leaves background threads alive after close().
        # Force-exit to prevent zombie GPU processes.
        os._exit(0)
