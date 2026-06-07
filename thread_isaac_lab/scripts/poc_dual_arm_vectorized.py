#!/usr/bin/env python3
"""poc_dual_arm_vectorized.py

Vectorized (num_envs > 1) dual-arm ball-reaching demonstration collection.

Based on poc_single_arm_redball_gpt.py but rewritten so that ALL tensor
operations use full ``(num_envs, ...)`` batch dimensions.  Each environment
runs an independent target sequence with its own seed, and the simulation
steps are shared across all environments.

Key design decisions:
  - No ``[0, ...]`` indexing anywhere.  Every read from Isaac Lab data
    tensors uses the full batch (``[:, ...]``).
  - Per-env state is tracked via ``EnvState`` (phase, target idx, etc.).
  - Environments that finish all targets are masked out (zero action)
    while the remaining environments continue stepping.
  - HDF5 output is per-environment, compatible with the existing dual-arm
    demo format from poc_single_arm_redball_gpt.py.

Usage:
  python thread_isaac_lab/scripts/poc_dual_arm_vectorized.py \\
      --num_envs 8 --num_targets 10 --seed_start 1 --device cuda:0
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import subprocess

import numpy as np
from PIL import Image

# Ensure repo root is on sys.path for thread_isaac_lab imports.
_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]  # .../IsaacLab
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Early import of pure-Python config (no Isaac Lab dependency)
from thread_isaac_lab.configs.task_config import PHASE_TRANSITION, PHASE_TIMEOUT  # noqa: E402

# ---------------------------------------------------------------------------
# CLI  (must come before AppLauncher so add_app_launcher_args works)
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Vectorized dual-arm ball-reaching demo collection."
)
parser.add_argument("--num_envs", type=int, default=8, help="Number of parallel environments")
parser.add_argument("--num_targets", type=int, default=10, help="Targets per environment")
parser.add_argument("--seed_start", type=int, default=1, help="Starting seed (env_i uses seed_start + i)")
parser.add_argument("--max_macro_steps", type=int, default=120, help="Max macro steps per target")
parser.add_argument("--hold_steps", type=int, default=96, help="Physics steps per macro step (reference: 96 = settle_steps)")
parser.add_argument("--success_threshold_m", type=float, default=0.008, help="Fingertip-to-ball success threshold")
parser.add_argument("--output_dir", type=str, default="", help="Output directory (default: data/vectorized_demos)")
parser.add_argument("--save_hdf5", action="store_true", default=True, help="Save per-env HDF5 demo files")
parser.add_argument("--no_save_hdf5", dest="save_hdf5", action="store_false")
parser.add_argument("--jt_alpha", type=float, default=10.0, help="JT IK position gain")
parser.add_argument("--jt_alpha_ori", type=float, default=3.0, help="JT IK orientation gain")
parser.add_argument("--ori_enable_dist", type=float, default=0.10, help="Enable orientation control below this distance")
parser.add_argument("--clip_rad", type=float, default=0.02, help="Joint delta clipping (rad)")
parser.add_argument("--standoff_dist", type=float, default=0.15, help="Y standoff for passive arm (m)")
parser.add_argument("--approach_slowdown_dist", type=float, default=0.10, help="Slow down approach below this distance")
parser.add_argument("--prepos_max_macros", type=int, default=150, help="Max macros for preposition phase")
parser.add_argument("--prepos_jt_alpha", type=float, default=20.0, help="JT alpha for preposition")
parser.add_argument("--prepos_clip_rad", type=float, default=0.05, help="Clip for preposition")
parser.add_argument("--prepos_converge_m", type=float, default=0.03, help="Convergence threshold for preposition")
parser.add_argument("--env_spacing", type=float, default=3.0, help="Spacing between environments")
parser.add_argument("--save_video", action="store_true", default=False, help="Save contact-sheet video (mp4)")
parser.add_argument("--no_save_video", dest="save_video", action="store_false")
parser.add_argument("--video_fps", type=int, default=10, help="Video output FPS")
parser.add_argument("--contact_sheet_res", type=int, default=256, help="Contact sheet per-camera resolution")
parser.add_argument("--trans_delta_clip_m", type=float, default=0.05, help="Position delta clipping (m)")
parser.add_argument("--collision_min_dist", type=float, default=0.15, help="Collision avoidance min EE distance (m)")
parser.add_argument(
    "--backend", type=str, default="dual_heuristic",
    choices=["dual_heuristic", "dual_camera"],
    help="Policy backend. 'dual_camera' uses camera-based ball detection instead of ground truth.",
)
parser.add_argument(
    "--target_mode", type=str, default="random",
    choices=["random", "table_triangle", "table_triangle_narrow"],
    help="Target generation mode. 'table_triangle' uses 3 fixed table-level targets. "
         "'table_triangle_narrow' uses tighter Y spacing (±0.03).",
)
parser.add_argument("--target_z", type=float, default=0.90,
                    help="Z height for table_triangle targets (default: 0.90m)")
parser.add_argument("--with_table", action="store_true", default=False,
                    help="Keep table/hook/cable in scene (default: removed)")
parser.add_argument("--approach", type=str, default="y_axis",
                    choices=["y_axis", "overhead"],
                    help="Approach strategy. 'overhead' descends from above before Y-axis approach.")
parser.add_argument("--table_z_min", type=float, default=0.755,
                    help="Minimum fingertip Z (table surface + safety margin, default: 0.755m)")
parser.add_argument("--log_min_z", action="store_true", default=False,
                    help="Track minimum fingertip Z during approach (table collision check)")
parser.add_argument("--finger_table_contact", action="store_true", default=False,
                    help="Enable finger-table collision: fingers can touch table, arm links cannot")
parser.add_argument("--finger_z_min", type=float, default=0.745,
                    help="Minimum fingertip Z when finger_table_contact enabled (table - 5mm, default: 0.745m)")
parser.add_argument("--grasp", action="store_true", default=False,
                    help="Enable cable grasp sequence: close grippers after reaching, then lift to verify")
parser.add_argument("--cable_x", type=float, default=0.45,
                    help="Cable X position override (default: 0.45 for IK reachability)")
parser.add_argument("--grasp_close_steps", type=int, default=PHASE_TIMEOUT.get("P3_close", 100),
                    help="Number of sim steps to close grippers (from PHASE_TIMEOUT)")
parser.add_argument("--grasp_lift_z", type=float, default=0.05,
                    help="Z lift distance (m) for grasp verification (default: 0.05)")
parser.add_argument("--fine_rl_checkpoint", type=str, default="",
                    help="Fine-RL policy checkpoint (.pt) for precision refinement after heuristic")
parser.add_argument("--rl_blend_center", type=float, default=0.10,
                    help="Sigmoid blend center distance (m) for RL/heuristic blend")
parser.add_argument("--rl_blend_temp", type=float, default=0.02,
                    help="Sigmoid blend temperature for RL/heuristic blend")
parser.add_argument("--rl_action_clip", type=float, default=0.02,
                    help="RL action clipping (m, default ±0.02)")
parser.add_argument("--rl_relative_obs", action="store_true", default=False,
                    help="Use relative observations for RL (matches --relative_obs in train_fine_rl.py)")
parser.add_argument("--contact_sensor", action="store_true", default=False,
                    help="Use ContactSensor API for finger-cable contact detection (fix25m)")
parser.add_argument("--solver_default", action="store_true", default=False,
                    help="Use TGS default solver instead of PGS 32 (for CPU diagnostic)")
parser.add_argument("--kinematic_grasp", action="store_true", default=False,
                    help="Kinematic cable attachment during lift — bypass PhysX collision (fix25n)")
parser.add_argument("--collect_obs_stats", action="store_true", default=False,
                    help="B1: Collect 24D obs statistics across all phases for normalization")
parser.add_argument("--obs_stats_dir", type=str, default=None,
                    help="B1: Output directory for obs stats (default: output_dir/heuristic_logs)")

from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

if not args.output_dir:
    args.output_dir = os.path.join(str(_REPO_ROOT), "data", "vectorized_demos")
os.makedirs(args.output_dir, exist_ok=True)

# Table/hook/cable: removed by default, kept with --with_table
if args.with_table:
    os.environ["POC_REMOVE_TABLE_HOOK_CABLE"] = "0"
else:
    os.environ.setdefault("POC_REMOVE_TABLE_HOOK_CABLE", "1")

# Scene config always includes cameras; enable them
args.enable_cameras = True

# dual_camera requires cameras and num_envs=1
_USE_CAMERA = (args.backend == "dual_camera")
if _USE_CAMERA:
    if args.num_envs != 1:
        print(f"[VEC] WARNING: dual_camera requires num_envs=1, overriding {args.num_envs} -> 1")
        args.num_envs = 1

np.random.seed(args.seed_start)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Isaac Lab imports (after AppLauncher)
# ---------------------------------------------------------------------------

import torch

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.scripts.camera_utils import estimate_target_from_cameras
from thread_isaac_lab.scripts.franka_analytical_ik import solve_ik_best_near_current
from thread_isaac_lab.configs.task_config import (
    ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ,
    GRIPPER_DOWN_QUAT_WXYZ,
    PHASE_TRANSITION, PHASE_TIMEOUT,
    OBS_DIM,
)
from thread_isaac_lab.models.obs_builder import ObsBuilder24D
from thread_isaac_lab.models.obs_collector import ObsCollector

# Pre-convert base positions/quaternions to numpy for analytical IK
_BASE_POS_LEFT_NP = np.array(ROBOT_LEFT_BASE)
_BASE_POS_RIGHT_NP = np.array(ROBOT_RIGHT_BASE)
_BASE_QUAT_NP = np.array(ROBOT_BASE_QUAT_WXYZ)

# USD imports for collision filtering + red ball marker
from pxr import Usd, UsdPhysics, Sdf

# Additional USD imports for red ball marker (camera backend only)
if _USE_CAMERA:
    import omni.usd
    from pxr import Gf, UsdGeom, UsdShade

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STOP_REQUESTED = False

FINGERTIP_OFFSET = 0.1123  # panda_hand -> fingertip (m)
BALL_RADIUS = 0.03
APPROACH_MARGIN = 0.01
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001  # target finger width for grasping

# Franka "ready" bent-elbow joints (non-singular)
BENT_JOINTS = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]

# Dual base positions
DUAL_LEFT_BASE_Y = -0.55
DUAL_RIGHT_BASE_Y = +0.55
BASE_X = 0.2467
BASE_Z = 1.265
BASE_QUAT = [0.7071, 0.0, 0.7071, 0.0]  # (w, x, y, z)

# Target generation center
DUAL_CENTER = np.array([0.75, 0.00, 1.05], dtype=np.float32)


def _request_stop(signum: int, _frame) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    print(f"[VEC] Stop requested (signal={signum})", flush=True)


signal.signal(signal.SIGTERM, _request_stop)
signal.signal(signal.SIGINT, _request_stop)

# Franka body names: non-finger links (to be filtered from table collision)
_FRANKA_NON_FINGER_BODIES = [
    "panda_link0", "panda_link1", "panda_link2", "panda_link3",
    "panda_link4", "panda_link5", "panda_link6", "panda_link7",
    "panda_hand",
]
# Finger bodies (allowed to collide with table)
_FRANKA_FINGER_BODIES = ["panda_leftfinger", "panda_rightfinger"]


def setup_finger_table_collision_filtering(
    sim: "sim_utils.SimulationContext",
    scene: "InteractiveScene",
    num_envs: int,
) -> None:
    """Set up collision groups so only fingers can touch the table.

    Creates two collision groups:
    - arm_bodies: panda_link0-7 + panda_hand (both arms) — filtered against table
    - table: Table prim
    Fingers (panda_leftfinger, panda_rightfinger) are NOT in any filtered group,
    so they collide normally with the table.
    """
    stage = sim.stage

    # Define collision groups
    arm_group_path = "/World/cg_arm_bodies"
    table_group_path = "/World/cg_table"
    arm_group = UsdPhysics.CollisionGroup.Define(stage, arm_group_path)
    table_group = UsdPhysics.CollisionGroup.Define(stage, table_group_path)

    # arm_bodies should NOT collide with table
    arm_group.GetFilteredGroupsRel().AddTarget(table_group_path)

    # Get collection APIs for adding members
    arm_coll = Usd.CollectionAPI(arm_group.GetPrim(), "colliders")
    table_coll = Usd.CollectionAPI(table_group.GetPrim(), "colliders")

    n_filtered = 0
    for env_i in range(num_envs):
        env_path = f"/World/envs/env_{env_i}"

        # Add table to table group
        table_prim_path = f"{env_path}/Table"
        table_coll.GetIncludesRel().AddTarget(Sdf.Path(table_prim_path))

        # Add non-finger arm bodies to arm_bodies group
        for arm_name in ("Robot_Left", "Robot_Right"):
            for body_name in _FRANKA_NON_FINGER_BODIES:
                body_path = f"{env_path}/{arm_name}/{body_name}"
                arm_coll.GetIncludesRel().AddTarget(Sdf.Path(body_path))
                n_filtered += 1

    print(f"[FINGER_CONTACT] Collision filtering set up: "
          f"{n_filtered} arm body-table pairs filtered, "
          f"fingers ({', '.join(_FRANKA_FINGER_BODIES)}) can touch table")


def setup_finger_hand_collision_filtering(
    sim: "sim_utils.SimulationContext",
    scene: "InteractiveScene",
    num_envs: int,
) -> None:
    """Filter collisions between finger bodies and panda_hand body.

    The v_groove_real.stl collision mesh extends 5mm backward into the hand body,
    causing the fingers to stall at ~12mm joint position. This filter allows the
    fingers to close through the hand collision geometry.
    """
    stage = sim.stage

    finger_group_path = "/World/cg_finger_bodies"
    hand_group_path = "/World/cg_hand_bodies"
    finger_group = UsdPhysics.CollisionGroup.Define(stage, finger_group_path)
    hand_group = UsdPhysics.CollisionGroup.Define(stage, hand_group_path)

    # fingers should NOT collide with hand
    finger_group.GetFilteredGroupsRel().AddTarget(hand_group_path)

    finger_coll = Usd.CollectionAPI(finger_group.GetPrim(), "colliders")
    hand_coll = Usd.CollectionAPI(hand_group.GetPrim(), "colliders")

    n_filtered = 0
    for env_i in range(num_envs):
        env_path = f"/World/envs/env_{env_i}"
        for arm_name in ("Robot_Left", "Robot_Right"):
            # Add fingers to finger group
            for fname in _FRANKA_FINGER_BODIES:
                finger_coll.GetIncludesRel().AddTarget(
                    Sdf.Path(f"{env_path}/{arm_name}/{fname}"))
            # Add hand to hand group
            hand_coll.GetIncludesRel().AddTarget(
                Sdf.Path(f"{env_path}/{arm_name}/panda_hand"))
            n_filtered += 1

    print(f"[FINGER_HAND] Collision filter: {n_filtered} arm finger-hand pairs filtered "
          f"(allows fingers to close past hand collision geometry)")


def apply_finger_physics_material(
    sim: "sim_utils.SimulationContext",
    num_envs: int,
) -> None:
    """Apply low-friction physics material to finger collision meshes.

    Sets static_friction=0.5, dynamic_friction=0.3, restitution=0.0
    for gentle table contact.
    """
    stage = sim.stage

    # Create a shared physics material for finger-table contact
    mat_path = "/World/Materials/FingerTableContact"
    mat_prim = stage.DefinePrim(mat_path)
    UsdPhysics.MaterialAPI.Apply(mat_prim)
    mat_api = UsdPhysics.MaterialAPI(mat_prim)
    mat_api.CreateStaticFrictionAttr().Set(0.5)
    mat_api.CreateDynamicFrictionAttr().Set(0.3)
    mat_api.CreateRestitutionAttr().Set(0.0)

    # Bind material to finger prims
    n_bound = 0
    for env_i in range(num_envs):
        env_path = f"/World/envs/env_{env_i}"
        for arm_name in ("Robot_Left", "Robot_Right"):
            for finger in _FRANKA_FINGER_BODIES:
                finger_path = f"{env_path}/{arm_name}/{finger}"
                finger_prim = stage.GetPrimAtPath(finger_path)
                if finger_prim.IsValid():
                    # Bind physics material
                    binding_api = UsdPhysics.MaterialAPI.Apply(finger_prim)
                    binding_api.CreateStaticFrictionAttr().Set(0.5)
                    binding_api.CreateDynamicFrictionAttr().Set(0.3)
                    binding_api.CreateRestitutionAttr().Set(0.0)
                    n_bound += 1

    print(f"[FINGER_CONTACT] Physics material applied to {n_bound} finger prims "
          f"(friction: static=0.5, dynamic=0.3, restitution=0.0)")


def apply_cable_table_friction(
    sim: "sim_utils.SimulationContext",
    num_envs: int,
    cable_static: float = 2.0,
    cable_dynamic: float = 1.5,
    table_static: float = 2.0,
    table_dynamic: float = 1.5,
) -> None:
    """Apply high-friction PhysicsMaterial to cable segments and table.

    Increases friction to prevent cable drift during arm approach.
    """
    stage = sim.stage
    n_cable = 0
    n_table = 0

    for env_i in range(num_envs):
        env_path = f"/World/envs/env_{env_i}"

        # --- Cable segments (only body prims, skip joints) ---
        cable_root = stage.GetPrimAtPath(f"{env_path}/Cable")
        if cable_root.IsValid():
            for child in cable_root.GetChildren():
                # Skip joint prims — only apply to rigid body link/segment prims
                if UsdPhysics.Joint(child) or not UsdPhysics.RigidBodyAPI(child):
                    continue
                UsdPhysics.MaterialAPI.Apply(child)
                mat_api = UsdPhysics.MaterialAPI(child)
                mat_api.CreateStaticFrictionAttr().Set(cable_static)
                mat_api.CreateDynamicFrictionAttr().Set(cable_dynamic)
                mat_api.CreateRestitutionAttr().Set(0.1)
                n_cable += 1
                # Also apply to collision sub-prims
                for sub in child.GetAllChildren():
                    if UsdPhysics.CollisionAPI(sub):
                        UsdPhysics.MaterialAPI.Apply(sub)
                        sub_api = UsdPhysics.MaterialAPI(sub)
                        sub_api.CreateStaticFrictionAttr().Set(cable_static)
                        sub_api.CreateDynamicFrictionAttr().Set(cable_dynamic)
                        sub_api.CreateRestitutionAttr().Set(0.1)

        # --- Table ---
        table_prim = stage.GetPrimAtPath(f"{env_path}/Table")
        if table_prim.IsValid():
            UsdPhysics.MaterialAPI.Apply(table_prim)
            mat_api = UsdPhysics.MaterialAPI(table_prim)
            mat_api.CreateStaticFrictionAttr().Set(table_static)
            mat_api.CreateDynamicFrictionAttr().Set(table_dynamic)
            mat_api.CreateRestitutionAttr().Set(0.0)
            n_table += 1
            # Also apply to table children (geometry/collision sub-prims)
            for sub in table_prim.GetAllChildren():
                UsdPhysics.MaterialAPI.Apply(sub)
                sub_api = UsdPhysics.MaterialAPI(sub)
                sub_api.CreateStaticFrictionAttr().Set(table_static)
                sub_api.CreateDynamicFrictionAttr().Set(table_dynamic)
                sub_api.CreateRestitutionAttr().Set(0.0)

    print(f"[FRICTION] Applied high friction: cable={n_cable} prims "
          f"(static={cable_static}, dynamic={cable_dynamic}), "
          f"table={n_table} prims (static={table_static}, dynamic={table_dynamic})")


# ---------------------------------------------------------------------------
# Fine-RL Actor (matches train_fine_rl.py architecture)
# ---------------------------------------------------------------------------

class FineRLActor(torch.nn.Module):
    """Actor network: obs[12] -> 128(ELU) -> 64(ELU) -> action[6].

    Observation: [ft_left(3), ft_right(3), left_ft_target(3), right_ft_target(3)]
    Action: [delta_ft_left(3), delta_ft_right(3)]  clipped to [-clip, +clip]
    """

    def __init__(self):
        super().__init__()
        self.actor = torch.nn.Sequential(
            torch.nn.Linear(12, 128),
            torch.nn.ELU(),
            torch.nn.Linear(128, 64),
            torch.nn.ELU(),
            torch.nn.Linear(64, 6),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.actor(obs)


def load_fine_rl_actor(checkpoint_path: str, device: torch.device) -> Optional[FineRLActor]:
    """Load FineRLActor from checkpoint. Returns None on failure."""
    if not checkpoint_path:
        return None
    if not os.path.exists(checkpoint_path):
        print(f"[FINE_RL] Checkpoint not found: {checkpoint_path}")
        return None
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=True)
    actor = FineRLActor().to(device)
    # Extract actor weights from model_state_dict (train_fine_rl.py format)
    state = ckpt.get("model_state_dict", ckpt)
    actor_state = {}
    for k, v in state.items():
        if k.startswith("actor."):
            actor_state[k] = v
    if not actor_state:
        print(f"[FINE_RL] No actor weights found in checkpoint")
        return None
    actor.load_state_dict(actor_state)
    actor.eval()
    print(f"[FINE_RL] Loaded actor from {checkpoint_path} ({sum(p.numel() for p in actor.parameters())} params)")
    return actor


# ---------------------------------------------------------------------------
# Batched math utilities (pure torch, no [0] indexing)
# ---------------------------------------------------------------------------


def quat_rotate_vec_batch(q_wxyz: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Rotate vec by quaternion.  q_wxyz: (N, 4), vec: (N, 3) -> (N, 3)."""
    w = q_wxyz[:, 0:1]
    xyz = q_wxyz[:, 1:4]
    t = 2.0 * torch.cross(xyz, vec, dim=-1)
    return vec + w * t + torch.cross(xyz, t, dim=-1)


def ee_to_fingertip_batch(ee_pos: torch.Tensor, ee_quat_wxyz: torch.Tensor,
                          offset: float = FINGERTIP_OFFSET) -> torch.Tensor:
    """Compute fingertip positions.  (N, 3) each -> (N, 3)."""
    z_local = torch.zeros_like(ee_pos)
    z_local[:, 2] = offset
    z_world = quat_rotate_vec_batch(ee_quat_wxyz, z_local)
    return ee_pos + z_world


def fingertip_to_ee_batch(ft_pos: torch.Tensor, ee_quat_wxyz: torch.Tensor,
                          offset: float = FINGERTIP_OFFSET) -> torch.Tensor:
    """Convert fingertip target to EE target.  (N, 3) each -> (N, 3)."""
    z_local = torch.zeros_like(ft_pos)
    z_local[:, 2] = offset
    z_world = quat_rotate_vec_batch(ee_quat_wxyz, z_local)
    return ft_pos - z_world


def compute_desired_orientation_batch(ball_pos: torch.Tensor,
                                      ee_pos: torch.Tensor,
                                      fingers_vertical: bool = False,
                                      cable_along_y: bool = False) -> torch.Tensor:
    """Compute desired gripper quaternion so +Z points EE->ball.  (N,3) -> (N,4) wxyz.

    If fingers_vertical=True, the finger open/close direction (+X axis) is
    rotated toward world-Z (vertical), reducing table interference when
    approaching from the side at low heights.

    If cable_along_y=True, use ref_vec=[0,1,0] (cable direction) so that
    desired_x (finger-open) ends up along world-X, perpendicular to cable.
    For overhead descent (desired_z ≈ [0,0,-1]): desired_x = [-1,0,0].
    """
    N = ball_pos.shape[0]
    device = ball_pos.device

    desired_z = ball_pos - ee_pos  # (N, 3)
    nz = torch.norm(desired_z, dim=-1, keepdim=True).clamp(min=1e-8)
    desired_z = desired_z / nz

    if cable_along_y:
        # Cable runs along Y. cross(Y, desired_z) gives X-perpendicular direction.
        ref_vec = torch.tensor([0.0, 1.0, 0.0], device=device).expand(N, 3).clone()
        parallel_mask = (torch.abs(torch.sum(desired_z * ref_vec, dim=-1)) > 0.99)
        ref_vec[parallel_mask] = torch.tensor([1.0, 0.0, 0.0], device=device)
    elif fingers_vertical:
        # Use world-X as reference so that desired_x ends up near world-Z
        # desired_x = cross(ref, desired_z), with ref=[1,0,0]:
        #   if desired_z is mostly in Y, desired_x ≈ [0,0,1] (vertical fingers)
        ref_vec = torch.tensor([1.0, 0.0, 0.0], device=device).expand(N, 3).clone()
        parallel_mask = (torch.abs(torch.sum(desired_z * ref_vec, dim=-1)) > 0.99)
        ref_vec[parallel_mask] = torch.tensor([0.0, 0.0, 1.0], device=device)
    else:
        ref_vec = torch.tensor([0.0, 0.0, 1.0], device=device).expand(N, 3).clone()
        parallel_mask = (torch.abs(torch.sum(desired_z * ref_vec, dim=-1)) > 0.99)
        ref_vec[parallel_mask] = torch.tensor([1.0, 0.0, 0.0], device=device)

    desired_x = torch.cross(ref_vec, desired_z, dim=-1)
    nx = torch.norm(desired_x, dim=-1, keepdim=True).clamp(min=1e-8)
    desired_x = desired_x / nx

    desired_y = torch.cross(desired_z, desired_x, dim=-1)

    # Rotation matrix to quaternion (batch)
    R = torch.stack([desired_x, desired_y, desired_z], dim=-1)  # (N, 3, 3)
    return _rotation_matrix_to_quat_batch(R)


def _rotation_matrix_to_quat_batch(R: torch.Tensor) -> torch.Tensor:
    """Convert (N, 3, 3) rotation matrices to (N, 4) quaternions (w,x,y,z)."""
    N = R.shape[0]
    q = torch.zeros(N, 4, device=R.device, dtype=R.dtype)

    trace = R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2]

    # Case 1: trace > 0
    mask1 = trace > 0
    if mask1.any():
        s = 0.5 / torch.sqrt(trace[mask1] + 1.0)
        q[mask1, 0] = 0.25 / s
        q[mask1, 1] = (R[mask1, 2, 1] - R[mask1, 1, 2]) * s
        q[mask1, 2] = (R[mask1, 0, 2] - R[mask1, 2, 0]) * s
        q[mask1, 3] = (R[mask1, 1, 0] - R[mask1, 0, 1]) * s

    # Case 2: R[0,0] is largest diagonal
    mask2 = (~mask1) & (R[:, 0, 0] > R[:, 1, 1]) & (R[:, 0, 0] > R[:, 2, 2])
    if mask2.any():
        s = 2.0 * torch.sqrt(1.0 + R[mask2, 0, 0] - R[mask2, 1, 1] - R[mask2, 2, 2])
        q[mask2, 0] = (R[mask2, 2, 1] - R[mask2, 1, 2]) / s
        q[mask2, 1] = 0.25 * s
        q[mask2, 2] = (R[mask2, 0, 1] + R[mask2, 1, 0]) / s
        q[mask2, 3] = (R[mask2, 0, 2] + R[mask2, 2, 0]) / s

    # Case 3: R[1,1] is largest diagonal
    mask3 = (~mask1) & (~mask2) & (R[:, 1, 1] > R[:, 2, 2])
    if mask3.any():
        s = 2.0 * torch.sqrt(1.0 + R[mask3, 1, 1] - R[mask3, 0, 0] - R[mask3, 2, 2])
        q[mask3, 0] = (R[mask3, 0, 2] - R[mask3, 2, 0]) / s
        q[mask3, 1] = (R[mask3, 0, 1] + R[mask3, 1, 0]) / s
        q[mask3, 2] = 0.25 * s
        q[mask3, 3] = (R[mask3, 1, 2] + R[mask3, 2, 1]) / s

    # Case 4: R[2,2] is largest diagonal
    mask4 = (~mask1) & (~mask2) & (~mask3)
    if mask4.any():
        s = 2.0 * torch.sqrt(1.0 + R[mask4, 2, 2] - R[mask4, 0, 0] - R[mask4, 1, 1])
        q[mask4, 0] = (R[mask4, 1, 0] - R[mask4, 0, 1]) / s
        q[mask4, 1] = (R[mask4, 0, 2] + R[mask4, 2, 0]) / s
        q[mask4, 2] = (R[mask4, 1, 2] + R[mask4, 2, 1]) / s
        q[mask4, 3] = 0.25 * s

    # Normalize
    q = q / torch.norm(q, dim=-1, keepdim=True).clamp(min=1e-8)
    return q


def orientation_error_axis_angle_batch(desired_wxyz: torch.Tensor,
                                       current_wxyz: torch.Tensor) -> torch.Tensor:
    """Compute orientation error as axis-angle.  (N,4), (N,4) -> (N,3)."""
    # q_err = desired * conj(current)
    conj_current = current_wxyz.clone()
    conj_current[:, 1:4] = -conj_current[:, 1:4]

    # Quaternion multiply: desired * conj(current)
    q_err = _quat_multiply_batch(desired_wxyz, conj_current)

    # Ensure w > 0 for shortest path
    neg_w = q_err[:, 0] < 0
    q_err[neg_w] = -q_err[neg_w]

    # Axis-angle: 2 * arccos(w) * axis
    w = q_err[:, 0].clamp(-1.0, 1.0)
    angle = 2.0 * torch.acos(w)  # (N,)
    sin_half = torch.sqrt(1.0 - w * w).clamp(min=1e-8)
    axis = q_err[:, 1:4] / sin_half.unsqueeze(-1)

    return axis * angle.unsqueeze(-1)  # (N, 3)


def _quat_multiply_batch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Multiply quaternions (w,x,y,z).  (N,4), (N,4) -> (N,4)."""
    aw, ax, ay, az = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    bw, bx, by, bz = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    return torch.stack([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ], dim=-1)


# ---------------------------------------------------------------------------
# Target generation (per-env, returns list of lists)
# ---------------------------------------------------------------------------

def make_targets_per_env(num_envs: int, num_targets: int,
                         seed_start: int,
                         target_mode: str = "random",
                         target_z: float = 0.90) -> list[list[np.ndarray]]:
    """Generate targets for each environment with different seeds.

    Returns: list of length num_envs, each element is a list of num_targets
             np.ndarray targets of shape (3,).
    """
    if target_mode in ("table_triangle", "table_triangle_narrow"):
        # Fixed 3-point triangle above table (Z configurable via target_z)
        TABLE_Z = target_z
        if target_mode == "table_triangle_narrow":
            fixed_targets = [
                np.array([0.40, -0.03, TABLE_Z], dtype=np.float32),  # A: left-front (narrow)
                np.array([0.40, +0.03, TABLE_Z], dtype=np.float32),  # B: right-front (narrow)
                np.array([0.30,  0.00, TABLE_Z], dtype=np.float32),  # C: center-back
            ]
        else:
            fixed_targets = [
                np.array([0.45, -0.05, TABLE_Z], dtype=np.float32),  # A: left-front
                np.array([0.45, +0.05, TABLE_Z], dtype=np.float32),  # B: right-front
                np.array([0.45,  0.00, TABLE_Z], dtype=np.float32),  # C: center (X=0.45, Y=0.00)
            ]
        all_targets: list[list[np.ndarray]] = []
        for _env_i in range(num_envs):
            # Repeat triangle pattern to fill num_targets
            targets = [fixed_targets[i % len(fixed_targets)].copy() for i in range(num_targets)]
            all_targets.append(targets)
        return all_targets

    all_targets: list[list[np.ndarray]] = []
    for env_i in range(num_envs):
        seed = seed_start + env_i
        rng = np.random.RandomState(seed)
        targets: list[np.ndarray] = []
        target_range = 0.05
        min_dist_m = 0.02
        max_attempts = num_targets * 50
        attempts = 0
        while len(targets) < num_targets and attempts < max_attempts:
            dx = rng.uniform(-0.03, 0.03)
            dy = rng.uniform(-target_range, target_range)
            dz = rng.uniform(-target_range, target_range)
            candidate = np.array([
                DUAL_CENTER[0] + dx,
                DUAL_CENTER[1] + dy,
                DUAL_CENTER[2] + dz,
            ], dtype=np.float32)
            too_close = any(np.linalg.norm(candidate - e) < min_dist_m for e in targets)
            if not too_close:
                targets.append(candidate)
            attempts += 1
        all_targets.append(targets)
    return all_targets


def compute_dual_targets_batch(ball_pos: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute left and right FINGERTIP targets from ball positions.

    ball_pos: (N, 3) -> left_ft: (N, 3), right_ft: (N, 3)
    Y-axis approach: left from Y-, right from Y+.
    """
    grasp_offset = BALL_RADIUS + APPROACH_MARGIN  # 0.04
    left_ft = ball_pos.clone()
    left_ft[:, 1] -= grasp_offset
    right_ft = ball_pos.clone()
    right_ft[:, 1] += grasp_offset
    return left_ft, right_ft


# ---------------------------------------------------------------------------
# Collision avoidance (matches reference check_arm_separation)
# ---------------------------------------------------------------------------

def check_arm_separation_batch(
    ee_left: torch.Tensor,   # (N, 3)
    ee_right: torch.Tensor,  # (N, 3)
    min_dist: float = 0.15,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Check distance between arms and return (distance, scale_factor).

    If arms are closer than min_dist, returns scale_factor < 1.0.
    Returns: (dist: (N,), scale: (N,))
    """
    dist = torch.norm(ee_left - ee_right, dim=-1)  # (N,)
    scale = torch.clamp(dist / min_dist, min=0.0, max=1.0)
    return dist, scale


# ---------------------------------------------------------------------------
# Red ball marker (for camera-based detection)
# ---------------------------------------------------------------------------

def create_or_update_red_marker(
    position_xyz: tuple[float, float, float], radius: float = 0.03
) -> None:
    """Create or move a red sphere marker in the scene (env 0)."""
    stage = omni.usd.get_context().get_stage()
    marker_path = "/World/envs/env_0/DebugMarker"
    sphere_geom = UsdGeom.Sphere.Define(stage, marker_path)
    sphere_geom.GetRadiusAttr().Set(radius)

    xform = UsdGeom.Xformable(sphere_geom.GetPrim())
    ops = xform.GetOrderedXformOps()
    if len(ops) == 0:
        xform.AddTranslateOp().Set(Gf.Vec3d(*position_xyz))
    else:
        updated = False
        for op in ops:
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                op.Set(Gf.Vec3d(*position_xyz))
                updated = True
                break
        if not updated:
            xform.AddTranslateOp().Set(Gf.Vec3d(*position_xyz))

    material_path = f"{marker_path}/RedMaterial"
    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        (1.0, 0.0, 0.0)
    )
    shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(
        (1.0, 0.0, 0.0)
    )
    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    UsdShade.MaterialBindingAPI(sphere_geom.GetPrim()).Bind(material)


# ---------------------------------------------------------------------------
# Video recording utilities
# ---------------------------------------------------------------------------

def get_four_camera_images(scene, sim) -> dict[str, np.ndarray]:
    """Read 4 cameras from scene and return dict of RGB images (env 0 only)."""
    cam_names = {
        "overhead": "overhead_camera",
        "front_center": "front_center_camera",
        "front_left": "front_left_camera",
        "front_right": "front_right_camera",
    }
    images: dict[str, np.ndarray] = {}
    for key, scene_key in cam_names.items():
        try:
            cam = scene[scene_key]
            cam.update(sim.get_physics_dt())
            rgb = cam.data.output["rgb"][0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            images[key] = rgb.astype(np.uint8)
        except Exception:
            pass
    return images


def build_contact_sheet(images: dict[str, np.ndarray], resolution: int) -> Image.Image:
    """Build a 4-camera contact sheet."""
    order = ["overhead", "front_center", "front_left", "front_right"]
    cols = len(order)
    canvas = Image.new("RGB", (resolution * cols, resolution))
    for i, name in enumerate(order):
        if name not in images:
            continue
        img = Image.fromarray(images[name]).resize(
            (resolution, resolution), Image.LANCZOS
        )
        canvas.paste(img, (i * resolution, 0))
    return canvas


def finalize_video(frames_dir: str, video_out: str, fps: int) -> None:
    """Compile PNG frames into mp4 via ffmpeg."""
    if not os.path.isdir(frames_dir):
        print(f"[VEC] Video finalize skipped (no frames dir): {frames_dir}")
        return
    frames = [fn for fn in os.listdir(frames_dir) if fn.endswith(".png")]
    if len(frames) == 0:
        print(f"[VEC] Video finalize skipped (no frames)")
        return
    os.makedirs(os.path.dirname(video_out) or ".", exist_ok=True)
    ffmpeg_log = os.path.join(os.path.dirname(video_out), "video_ffmpeg.log")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(fps), "-start_number", "0",
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        video_out,
    ]
    min_video_size = 1 * 1024 * 1024
    try:
        with open(ffmpeg_log, "w") as f:
            p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=False)
        if p.returncode == 0 and os.path.exists(video_out):
            sz = os.path.getsize(video_out)
            if sz >= min_video_size:
                print(f"[VEC] Video saved: {video_out} ({sz} bytes)")
                return
            # Fallback: high bitrate re-encode
            tmp_out = f"{video_out}.tmp_cbr.mp4"
            cmd2 = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-framerate", str(fps), "-start_number", "0",
                "-i", os.path.join(frames_dir, "frame_%06d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-b:v", "50M", "-minrate", "50M", "-maxrate", "50M",
                "-bufsize", "100M", "-x264-params", "nal-hrd=cbr:force-cfr=1",
                tmp_out,
            ]
            with open(ffmpeg_log, "a") as f:
                f.write("\n# --- fallback: cbr ---\n")
                p2 = subprocess.run(cmd2, stdout=f, stderr=subprocess.STDOUT, check=False)
            if p2.returncode == 0 and os.path.exists(tmp_out):
                sz2 = os.path.getsize(tmp_out)
                os.replace(tmp_out, video_out)
                print(f"[VEC] Video saved (fallback): {video_out} ({sz2} bytes)")
            else:
                print(f"[VEC] Video fallback failed; see {ffmpeg_log}")
        else:
            print(f"[VEC] Video finalize failed (rc={p.returncode}); see {ffmpeg_log}")
    except FileNotFoundError:
        print("[VEC] Video finalize failed: ffmpeg not found")
    except Exception as e:
        print(f"[VEC] Video finalize failed: {e}")


# ---------------------------------------------------------------------------
# Per-environment state
# ---------------------------------------------------------------------------

@dataclass
class EnvState:
    """Tracks per-environment state for the vectorized reaching loop."""

    num_envs: int
    device: torch.device

    # Phase: 0=Phase_A (right arm active), 1=Phase_B (left arm active), 2=done_target, 3=all_done
    phase: torch.Tensor = field(init=False)
    current_target_idx: torch.Tensor = field(init=False)
    macro_step: torch.Tensor = field(init=False)
    left_reached: torch.Tensor = field(init=False)
    right_reached: torch.Tensor = field(init=False)
    targets_completed: torch.Tensor = field(init=False)

    # Per-env target lists (CPU, heterogeneous lengths possible)
    all_targets: list[list[np.ndarray]] = field(default_factory=list)
    num_targets_per_env: list[int] = field(default_factory=list)

    # Current ball positions for active targets: (N, 3)
    ball_pos: torch.Tensor = field(init=False)
    left_ft_target: torch.Tensor = field(init=False)
    right_ft_target: torch.Tensor = field(init=False)

    # Passive arm standoff target (Phase A): left arm parks Y- of ball
    left_standoff_ft: torch.Tensor = field(init=False)
    # Passive arm hold target (Phase B): right arm holds current FT position
    right_hold_ft: torch.Tensor = field(init=False)

    # Demo buffers per env
    demo_buffers: list[list[dict]] = field(default_factory=list)

    # Statistics per env
    stats: list[dict] = field(default_factory=list)

    def __post_init__(self):
        N = self.num_envs
        dev = self.device
        self.phase = torch.zeros(N, dtype=torch.int32, device=dev)
        self.current_target_idx = torch.zeros(N, dtype=torch.int32, device=dev)
        self.macro_step = torch.zeros(N, dtype=torch.int32, device=dev)
        self.left_reached = torch.zeros(N, dtype=torch.bool, device=dev)
        self.right_reached = torch.zeros(N, dtype=torch.bool, device=dev)
        self.targets_completed = torch.zeros(N, dtype=torch.int32, device=dev)

        self.ball_pos = torch.zeros(N, 3, dtype=torch.float32, device=dev)
        self.left_ft_target = torch.zeros(N, 3, dtype=torch.float32, device=dev)
        self.right_ft_target = torch.zeros(N, 3, dtype=torch.float32, device=dev)
        self.left_standoff_ft = torch.zeros(N, 3, dtype=torch.float32, device=dev)
        self.right_hold_ft = torch.zeros(N, 3, dtype=torch.float32, device=dev)

        self.demo_buffers = [[] for _ in range(N)]
        self.stats = [
            {
                "targets_reached": 0,
                "targets_total": 0,
                "nan_count": 0,
                "phase_a_macros_total": 0,
                "phase_b_macros_total": 0,
                "_last_phase_a_macros": 0,
            }
            for _ in range(N)
        ]

    def set_targets(self, targets_per_env: list[list[np.ndarray]]):
        """Initialize targets from the target generation output."""
        self.all_targets = targets_per_env
        self.num_targets_per_env = [len(t) for t in targets_per_env]
        for i in range(self.num_envs):
            self.stats[i]["targets_total"] = len(targets_per_env[i])
        self._load_current_targets()

    def _load_current_targets(self):
        """Load the current target for each env based on current_target_idx."""
        for i in range(self.num_envs):
            idx = int(self.current_target_idx[i].item())
            if idx < len(self.all_targets[i]):
                ball = self.all_targets[i][idx]
                self.ball_pos[i] = torch.tensor(ball, device=self.device)
            # else: env is done, ball_pos stays stale (masked by phase=3)

        left_ft, right_ft = compute_dual_targets_batch(self.ball_pos)
        self.left_ft_target = left_ft
        self.right_ft_target = right_ft
        # Left standoff: Y- offset from ball
        self.left_standoff_ft = self.ball_pos.clone()
        self.left_standoff_ft[:, 1] -= 0.15  # standoff_dist

    def advance_to_next_target(self, env_mask: torch.Tensor):
        """Move specified envs to the next target, or mark them all_done."""
        for i in range(self.num_envs):
            if not env_mask[i]:
                continue
            next_idx = int(self.current_target_idx[i].item()) + 1
            if next_idx >= len(self.all_targets[i]):
                self.phase[i] = 3  # all_done
            else:
                self.current_target_idx[i] = next_idx
                self.phase[i] = 0  # restart Phase A
                self.macro_step[i] = 0
                self.left_reached[i] = False
                self.right_reached[i] = False
        self._load_current_targets()


# ---------------------------------------------------------------------------
# Batched JT IK step
# ---------------------------------------------------------------------------

def jt_ik_step_6dof_batch(
    robot,
    jacobian_body: int,
    hand_body: int,
    cmd_pos_w: torch.Tensor,       # (N, 3)
    ball_pos: torch.Tensor,         # (N, 3)
    enable_ori_mask: torch.Tensor,  # (N,) bool
    jt_alpha: float,
    jt_alpha_ori: float,
    ori_enable_dist: float,
    clip_rad: float,
    device: torch.device,
    fingers_vertical: bool = False,
    cable_along_y: bool = False,
) -> tuple[Optional[torch.Tensor], torch.Tensor]:
    """Batched 6-DOF Jacobian Transpose IK step.

    Returns (ik_target_joints: (N, 7), nan_mask: (N,) bool).
    ik_target_joints is None if ALL environments produced NaN.
    """
    N = cmd_pos_w.shape[0]
    joint_pos = robot.data.joint_pos[:, :7]  # (N, 7)
    jac_w = robot.root_physx_view.get_jacobians()[:, jacobian_body, :, :7]  # (N, 6, 7)
    ee_pos_w = robot.data.body_pose_w[:, hand_body, :3]  # (N, 3)
    ee_quat_w = robot.data.body_quat_w[:, hand_body, :]  # (N, 4)

    # Position error
    pos_error = cmd_pos_w - ee_pos_w  # (N, 3)
    pos_err_mag = torch.norm(pos_error, dim=-1)  # (N,)

    # Decide which envs use orientation control
    ori_active = enable_ori_mask & (pos_err_mag < ori_enable_dist)  # (N,)

    # Compute orientation error for envs that need it
    desired_quat = compute_desired_orientation_batch(ball_pos, ee_pos_w,
                                                     fingers_vertical=fingers_vertical,
                                                     cable_along_y=cable_along_y)  # (N, 4)
    ori_err_aa = orientation_error_axis_angle_batch(desired_quat, ee_quat_w)  # (N, 3)

    # Scale orientation gain based on distance
    ori_scale = torch.clamp(1.0 - pos_err_mag / ori_enable_dist, min=0.0)  # (N,)
    effective_alpha_ori = jt_alpha_ori * ori_scale  # (N,)

    # Build 6D error
    error_6d = torch.zeros(N, 6, device=device)
    error_6d[:, :3] = jt_alpha * pos_error
    # Only add orientation for envs with ori_active
    ori_contribution = effective_alpha_ori.unsqueeze(-1) * ori_err_aa  # (N, 3)
    error_6d[:, 3:6] = torch.where(
        ori_active.unsqueeze(-1).expand_as(ori_contribution),
        ori_contribution,
        torch.zeros_like(ori_contribution),
    )

    # Select which Jacobian rows to use: 6 for ori, 3 for pos-only
    J_full = jac_w[:, :6, :]  # (N, 6, 7)

    # For pos-only envs, zero out the orientation rows in the error
    # (already done above by masking ori_contribution)

    # dq = J^T @ error_6d
    dq = torch.bmm(J_full.transpose(1, 2), error_6d.unsqueeze(2)).squeeze(2)  # (N, 7)

    # Check for NaN
    nan_mask = torch.any(torch.isnan(dq), dim=-1)  # (N,)

    # Clip
    dq_clipped = dq.clamp(-clip_rad, clip_rad)
    # Zero out NaN envs
    dq_clipped[nan_mask] = 0.0

    ik_targets = (joint_pos + dq_clipped).clone()
    return ik_targets, nan_mask


# ---------------------------------------------------------------------------
# Analytical IK (batch wrapper) — replaces J^T IK for precise positioning
# ---------------------------------------------------------------------------

def analytical_ik_batch(
    robot,
    hand_body: int,
    cmd_pos_w: torch.Tensor,       # (N, 3) EE target position in world
    ball_pos: torch.Tensor,         # (N, 3) orientation reference
    enable_ori_mask: torch.Tensor,  # (N,) bool
    device: torch.device,
    base_pos_np: np.ndarray,        # (3,) robot base position (numpy)
    base_quat_np: np.ndarray,       # (4,) robot base quat wxyz (numpy)
    fingers_vertical: bool = False,
    cable_along_y: bool = False,
    q7_steps: int = 40,
    min_margin_deg: float = 3.0,
    max_joint_change_deg: Optional[float] = None,
    debug: bool = False,
) -> tuple[Optional[torch.Tensor], torch.Tensor]:
    """Batch analytical IK for Franka Panda.

    Drop-in replacement for jt_ik_step_6dof_batch — computes exact joint
    solutions instead of iterative J^T steps.

    Returns (ik_target_joints: (N, 7), fail_mask: (N,) bool).
    ik_target_joints falls back to current joints where analytical IK fails.
    """
    N = cmd_pos_w.shape[0]
    joint_pos = robot.data.joint_pos[:, :7]  # (N, 7)
    ee_pos_w = robot.data.body_pos_w[:, hand_body, :3]  # (N, 3)

    # Compute desired orientation quaternion (same logic as J^T IK)
    desired_quat = compute_desired_orientation_batch(
        ball_pos, ee_pos_w,
        fingers_vertical=fingers_vertical,
        cable_along_y=cable_along_y,
    )  # (N, 4) wxyz

    # For envs without orientation control, use CURRENT EE orientation
    # (equivalent to J^T IK skipping orientation: arm maintains its pose)
    ee_quat_w = robot.data.body_quat_w[:, hand_body, :]  # (N, 4) wxyz
    for i in range(N):
        if not enable_ori_mask[i]:
            desired_quat[i] = ee_quat_w[i]

    # Output tensors
    ik_targets = joint_pos.clone()  # fallback = current joints
    fail_mask = torch.zeros(N, dtype=torch.bool, device=device)

    # Solve per environment (N is typically 1 for POC)
    for i in range(N):
        target_pos_np = cmd_pos_w[i].detach().cpu().numpy()
        target_quat_np = desired_quat[i].detach().cpu().numpy()
        current_joints_np = joint_pos[i].detach().cpu().numpy()

        success, joints, margin, distance = solve_ik_best_near_current(
            target_pos=target_pos_np,
            base_pos=base_pos_np,
            base_quat=base_quat_np,
            current_joints=current_joints_np,
            target_quat=target_quat_np,
            q7_range=(-2.8, 2.8),
            q7_steps=q7_steps,
            min_margin_deg=min_margin_deg,
            max_joint_change_deg=max_joint_change_deg,
        )

        if success and joints is not None:
            ik_targets[i] = torch.tensor(joints, device=device, dtype=torch.float32)
        else:
            fail_mask[i] = True
            if debug:
                ee_cur = ee_pos_w[i].detach().cpu().numpy()
                print(f"[AIK FAIL] env={i} target=({target_pos_np[0]:.4f},{target_pos_np[1]:.4f},{target_pos_np[2]:.4f}) "
                      f"ee_cur=({ee_cur[0]:.4f},{ee_cur[1]:.4f},{ee_cur[2]:.4f}) "
                      f"quat=({target_quat_np[0]:.3f},{target_quat_np[1]:.3f},{target_quat_np[2]:.3f},{target_quat_np[3]:.3f})")

    return ik_targets, fail_mask


# ---------------------------------------------------------------------------
# Apply joint targets (batched)
# ---------------------------------------------------------------------------

def apply_joints_batch(robot, ik_joints: torch.Tensor, action_mask: torch.Tensor):
    """Apply IK joint targets + open gripper for all envs.

    ik_joints: (N, 7)
    action_mask: (N,) bool -- only apply to envs where True
    """
    tgt = robot.data.joint_pos.clone()  # (N, n_joints)
    # Only update envs in the mask
    mask_expanded = action_mask.unsqueeze(-1)  # (N, 1)
    tgt[:, :7] = torch.where(mask_expanded.expand_as(tgt[:, :7]),
                              ik_joints, tgt[:, :7])
    if tgt.shape[1] >= 9:
        tgt[:, 7] = torch.where(action_mask, torch.full_like(tgt[:, 7], GRIPPER_OPEN), tgt[:, 7])
        tgt[:, 8] = torch.where(action_mask, torch.full_like(tgt[:, 8], GRIPPER_OPEN), tgt[:, 8])
    robot.set_joint_position_target(tgt)
    robot.write_data_to_sim()


def set_gripper_width(robot, width: float, device: torch.device):
    """Set both finger joints to the given width."""
    tgt = robot.data.joint_pos.clone()
    tgt[:, 7] = width
    tgt[:, 8] = width
    robot.set_joint_position_target(tgt)
    robot.write_data_to_sim()


def grasp_and_lift_sequence(
    robot_left, robot_right, sim, scene, device,
    cable, close_steps: int, lift_z: float,
    cable_pos_before_reaching: Optional[torch.Tensor] = None,
    env_origin: Optional[torch.Tensor] = None,
    env_idx: int = 0,
    on_step=None,
    contact_sensors: Optional[dict] = None,
    kinematic_grasp: bool = False,
    obs_builder=None,
    hand_body_left: int = -1,
    hand_body_right: int = -1,
    all_env_origins: Optional[torch.Tensor] = None,
    obs_collector=None,
) -> dict:
    """Execute grasp sequence: close grippers → settle → lift → check cable.

    Returns dict with grasp results.
    """
    TABLE_Z = 0.75
    GRIP_SUCCESS_THRESHOLD = 0.0025  # 2.5mm — cable between fingers
    # Reset obs_builder state for this grasp sequence
    if obs_builder is not None:
        obs_builder.reset()

    # B1: obs collection helper
    _obs_step_counter = [0]  # mutable counter for global step across phases

    def _collect_obs(phase_id):
        """Record obs if collector is active."""
        if obs_collector is not None and cable is not None:
            obs_collector.record(phase_id, _obs_step_counter[0],
                                robot_left, robot_right, cable)
        _obs_step_counter[0] += 1
    results = {
        "gripper_closed": False,
        "cable_lifted": False,
        "cable_z_before": [],
        "cable_z_after": [],
        "cable_z_delta": 0.0,
        "nan_detected": False,
        "close_steps_used": 0,
        "lift_steps_used": 0,
        "grip_width_left": 0.0,
        "grip_width_right": 0.0,
        "ft_z_after_p29_left": None,
        "ft_z_after_p29_right": None,
        "fo_x_after_p299_left": None,
        "fo_x_after_p299_right": None,
        "grip_success_left": False,
        "grip_success_right": False,
        "grip_failed_reason": None,
        "cable_drift_xyz": None,
    }

    # --- Record cable positions before grasp (convert to local frame) ---
    _cable_raw = cable.data.body_pos_w[env_idx, :, :3].clone()  # (n_segs, 3) world frame
    if env_origin is not None:
        cable_pos_all = _cable_raw - env_origin.unsqueeze(0)  # (n_segs, 3) local frame
    else:
        cable_pos_all = _cable_raw
    cable_z_before = cable_pos_all[:, 2].clone()  # (n_segs,)
    results["cable_z_before"] = cable_z_before.cpu().tolist()
    cable_z_mean = cable_z_before.mean().item()
    print(f"[GRASP] Cable Z before: mean={cable_z_mean:.4f}m "
          f"min={cable_z_before.min().item():.4f}m max={cable_z_before.max().item():.4f}m")
    # Log all cable segment XYZ positions
    _body_names = cable.body_names if hasattr(cable, 'body_names') else [f"seg_{i}" for i in range(cable_pos_all.shape[0])]
    for si in range(cable_pos_all.shape[0]):
        _name = _body_names[si] if si < len(_body_names) else f"seg_{si}"
        print(f"[GRASP]   cable[{si}] ({_name}): "
              f"X={cable_pos_all[si, 0].item():.4f} Y={cable_pos_all[si, 1].item():.4f} "
              f"Z={cable_pos_all[si, 2].item():.4f}")

    # --- Cable drift: compare current positions to before reaching ---
    if cable_pos_before_reaching is not None:
        _drift = cable_pos_all.cpu() - cable_pos_before_reaching.cpu()
        _drift_mean = _drift.mean(dim=0)  # (3,)
        _drift_max = _drift.abs().max(dim=0).values  # (3,)
        results["cable_drift_xyz"] = {
            "mean": [round(_drift_mean[j].item(), 5) for j in range(3)],
            "max_abs": [round(_drift_max[j].item(), 5) for j in range(3)],
            "per_segment": [[round(_drift[si, j].item(), 5) for j in range(3)]
                            for si in range(_drift.shape[0])],
        }
        print(f"[GRASP] Cable drift (reaching→grip): "
              f"mean=({_drift_mean[0].item()*1000:.1f}, {_drift_mean[1].item()*1000:.1f}, {_drift_mean[2].item()*1000:.1f})mm "
              f"max_abs=({_drift_max[0].item()*1000:.1f}, {_drift_max[1].item()*1000:.1f}, {_drift_max[2].item()*1000:.1f})mm")

    # --- Phase 2.5: Z-only descent + finger rotation alignment ---
    hand_body_left = int(robot_left.find_bodies("panda_hand")[0][0])
    hand_body_right = int(robot_right.find_bodies("panda_hand")[0][0])
    is_fixed_left = bool(getattr(robot_left, "is_fixed_base", False))
    is_fixed_right = bool(getattr(robot_right, "is_fixed_base", False))
    jac_body_left = hand_body_left - 1 if is_fixed_left else hand_body_left
    jac_body_right = hand_body_right - 1 if is_fixed_right else hand_body_right

    # Get current EE and fingertip positions
    ee_pos_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_pos_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_quat_l = robot_left.data.body_quat_w[:, hand_body_left, :]
    ee_quat_r = robot_right.data.body_quat_w[:, hand_body_right, :]
    ft_l = ee_to_fingertip_batch(ee_pos_l, ee_quat_l)
    ft_r = ee_to_fingertip_batch(ee_pos_r, ee_quat_r)
    print(f"[GRASP] Current fingertip: "
          f"L=({ft_l[0,0].item():.4f}, {ft_l[0,1].item():.4f}, {ft_l[0,2].item():.4f}) "
          f"R=({ft_r[0,0].item():.4f}, {ft_r[0,1].item():.4f}, {ft_r[0,2].item():.4f})")

    # Find nearest cable segment to each arm
    _ft_xy_l = ft_l[0, :2]
    _ft_xy_r = ft_r[0, :2]
    _cable_xy = cable_pos_all[:, :2]
    _dist_l = torch.norm(_cable_xy - _ft_xy_l.unsqueeze(0), dim=1)
    _dist_r = torch.norm(_cable_xy - _ft_xy_r.unsqueeze(0), dim=1)
    _nearest_l = int(_dist_l.argmin().item())
    _nearest_r = int(_dist_r.argmin().item())
    _seg_pos_l = cable_pos_all[_nearest_l]
    _seg_pos_r = cable_pos_all[_nearest_r]
    print(f"[GRASP] Nearest cable seg to L: [{_nearest_l}] "
          f"({_seg_pos_l[0].item():.4f},{_seg_pos_l[1].item():.4f},{_seg_pos_l[2].item():.4f}) "
          f"XY dist={_dist_l[_nearest_l].item()*1000:.1f}mm")
    print(f"[GRASP] Nearest cable seg to R: [{_nearest_r}] "
          f"({_seg_pos_r[0].item():.4f},{_seg_pos_r[1].item():.4f},{_seg_pos_r[2].item():.4f}) "
          f"XY dist={_dist_r[_nearest_r].item()*1000:.1f}mm")

    # Fine-positioning: closed-loop control using ACTUAL finger body positions
    # The computed fingertip (EE + Z offset) doesn't match the actual grip center
    # because the hand is tilted. Use real finger midpoint for targeting.
    _lf_idx = int(robot_left.find_bodies("panda_leftfinger")[0][0])
    _rf_idx = int(robot_left.find_bodies("panda_rightfinger")[0][0])

    no_ori = torch.zeros(1, dtype=torch.bool, device=device)

    # Cable targets are in LOCAL frame; body_pos_w also returns env-local positions
    # Z offset: grip center target relative to cable center Z.
    # IK cannot lower grip center below ~0.778m (table collision constraint on hand).
    # Keep at 0 and rely on IK-tracked close for Z contact.
    # Detect if hand is pointing downward (from overhead descent Phase 1.5)
    _eq_l = robot_left.data.body_quat_w[:, hand_body_left, :]
    _eq_r = robot_right.data.body_quat_w[:, hand_body_right, :]
    _z_unit = torch.tensor([[0.0, 0.0, 1.0]], device=device)
    _hand_z_l = quat_rotate_vec_batch(_eq_l, _z_unit)
    _hand_z_r = quat_rotate_vec_batch(_eq_r, _z_unit)
    _hand_down = (_hand_z_l[env_idx, 2].item() < -0.7) and (_hand_z_r[env_idx, 2].item() < -0.7)
    if _hand_down:
        # Hand pointing down: grip center is above cable, only correct XY
        _GRIP_Z_OFFSET = 0.000  # will zero out Z error below
        print(f"[GRASP] Phase 2.5: Hand down mode (hz_z_L={_hand_z_l[0,2].item():.3f} "
              f"hz_z_R={_hand_z_r[0,2].item():.3f}) — XY-only correction, orientation maintained")
    else:
        _GRIP_Z_OFFSET = 0.000
    _cable_target_l = _seg_pos_l.to(device).clone()  # (3,) local frame — original cable pos
    _cable_target_r = _seg_pos_r.to(device).clone()  # (3,) local frame
    _cable_target_l[2] += _GRIP_Z_OFFSET
    _cable_target_r[2] += _GRIP_Z_OFFSET
    _CONVERGE_THRESH = PHASE_TRANSITION.get("P25_to_P29_xy_mm", 3.0) / 1000.0
    _IK_ALPHA = 20.0
    _IK_CLIP = 0.03
    _IK_ORI_GAIN = 0.0  # No orientation control during Phase 2.5 — Phase 2.99 handles finger alignment
    _MAX_PASSES = 2  # pass 1: converge to target; pass 2: correct residual
    # Orientation-enabled IK mask (when hand is pointing down)
    _ori_mask = no_ori  # Orientation disabled during Phase 2.5 — preserves fo_X from overhead descent
    # --- Lock j6 (wrist rotation) throughout Phases 2.5/2.9/2.95/3 ---
    # After overhead descent, finger-open direction is correct (X-axis, ⊥ cable).
    # J^T IK freely rotates j6, drifting fingers to Y-axis (∥ cable) → grip fails.
    _j6_lock_l = robot_left.data.joint_pos[env_idx, 6].clone()
    _j6_lock_r = robot_right.data.joint_pos[env_idx, 6].clone()
    # Verify finger-open direction at lock point
    _x_local = torch.tensor([[1.0, 0.0, 0.0]], device=device)
    _fo_l_lock = quat_rotate_vec_batch(robot_left.data.body_quat_w[:, hand_body_left, :], _x_local)
    _fo_r_lock = quat_rotate_vec_batch(robot_right.data.body_quat_w[:, hand_body_right, :], _x_local)
    print(f"[GRASP] j6 LOCKED: L={_j6_lock_l.item():.4f} R={_j6_lock_r.item():.4f}  "
          f"finger_open_X: L={_fo_l_lock[0,0].item():.3f} R={_fo_r_lock[0,0].item():.3f}")

    print(f"[GRASP] Phase 2.5: Two-pass fine-positioning (Z offset={_GRIP_Z_OFFSET*1000:+.0f}mm, "
          f"convergence={_CONVERGE_THRESH*1000:.0f}mm, passes={_MAX_PASSES}, "
          f"ori_gain={_IK_ORI_GAIN})")

    _total_steps = 0
    for _pass in range(_MAX_PASSES):
        if _pass == 0:
            _seg_target_l = _cable_target_l.clone()
            _seg_target_r = _cable_target_r.clone()
        else:
            # Pass 2: measure residual from pass 1 and correct the target
            _lf_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
            _lf_r = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
            _gc_l = (_lf_l + _rf_l) / 2.0
            _gc_r = (_lf_r + _rf_r) / 2.0
            _residual_l = _gc_l - _cable_target_l  # grip - target = systematic bias
            _residual_r = _gc_r - _cable_target_r
            _residual_xy_l = torch.norm(_residual_l[:2]).item()
            _residual_xy_r = torch.norm(_residual_r[:2]).item()
            if _residual_xy_l < _CONVERGE_THRESH and _residual_xy_r < _CONVERGE_THRESH:
                print(f"[GRASP] Pass 1 already within {_CONVERGE_THRESH*1000:.0f}mm, skipping pass 2")
                break
            # Correct: new target = cable_target - residual (so grip ends up at cable)
            _seg_target_l = _cable_target_l - _residual_l
            _seg_target_r = _cable_target_r - _residual_r
            print(f"[GRASP] Pass 2: correcting by residual "
                  f"L=({_residual_l[0].item()*1000:.1f},{_residual_l[1].item()*1000:.1f},{_residual_l[2].item()*1000:.1f})mm "
                  f"R=({_residual_r[0].item()*1000:.1f},{_residual_r[1].item()*1000:.1f},{_residual_r[2].item()*1000:.1f})mm "
                  f"new_target_L=({_seg_target_l[0].item():.4f},{_seg_target_l[1].item():.4f},{_seg_target_l[2].item():.4f}) "
                  f"new_target_R=({_seg_target_r[0].item():.4f},{_seg_target_r[1].item():.4f},{_seg_target_r[2].item():.4f})")

        _p25_budget = PHASE_TIMEOUT.get("P25", 200)
        _pass_steps = int(_p25_budget * 0.75) if _pass == 0 else int(_p25_budget * 0.50)
        for step in range(_pass_steps):
            if STOP_REQUESTED:
                break

            # Read actual finger positions (use env_idx, not hardcoded 0)
            _lf_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
            _lf_r = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]

            # Actual grip center = midpoint of left and right fingers
            _grip_center_l = (_lf_l + _rf_l) / 2.0
            _grip_center_r = (_lf_r + _rf_r) / 2.0

            # Error from grip center to corrected target
            _err_l = _seg_target_l - _grip_center_l
            _err_r = _seg_target_r - _grip_center_r
            _err_mag_l = torch.norm(_err_l).item()
            _err_mag_r = torch.norm(_err_r).item()

            # Also measure XY distance to actual cable (for reporting)
            _gc_cable_xy_l = torch.norm(_grip_center_l[:2] - _cable_target_l[:2]).item()
            _gc_cable_xy_r = torch.norm(_grip_center_r[:2] - _cable_target_r[:2]).item()

            if step % 20 == 0:
                print(f"[GRASP] pass{_pass+1} step={step} "
                      f"grip_L=({_grip_center_l[0].item():.4f},{_grip_center_l[1].item():.4f},{_grip_center_l[2].item():.4f}) "
                      f"grip_R=({_grip_center_r[0].item():.4f},{_grip_center_r[1].item():.4f},{_grip_center_r[2].item():.4f}) "
                      f"err_L={_err_mag_l*1000:.1f}mm err_R={_err_mag_r*1000:.1f}mm "
                      f"gc2cable_L={_gc_cable_xy_l*1000:.1f}mm gc2cable_R={_gc_cable_xy_r*1000:.1f}mm")

            if _err_mag_l < _CONVERGE_THRESH and _err_mag_r < _CONVERGE_THRESH:
                print(f"[GRASP] Pass {_pass+1} converged at step {step}: "
                      f"err_L={_err_mag_l*1000:.1f}mm err_R={_err_mag_r*1000:.1f}mm "
                      f"gc2cable_L={_gc_cable_xy_l*1000:.1f}mm gc2cable_R={_gc_cable_xy_r*1000:.1f}mm")
                break

            # Move EE by the grip center error (clamped to avoid large jumps)
            _clamp = 0.01  # max 10mm per step
            _delta_l = torch.clamp(_err_l, -_clamp, _clamp)
            _delta_r = torch.clamp(_err_r, -_clamp, _clamp)
            # When hand points down, only correct XY (Z is correct from descent)
            if _hand_down:
                _delta_l[2] = 0.0
                _delta_r[2] = 0.0

            ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
            _ee_tgt_l = ee_cur_l + _delta_l.unsqueeze(0)
            _ee_tgt_r = ee_cur_r + _delta_r.unsqueeze(0)

            # Orientation reference: point below current EE (maintain downward tool axis)
            _ori_ref_l = ee_cur_l.clone()
            _ori_ref_l[:, 2] -= 0.1
            _ori_ref_r = ee_cur_r.clone()
            _ori_ref_r[:, 2] -= 0.1

            ik_l, nan_l = jt_ik_step_6dof_batch(
                robot_left, jac_body_left, hand_body_left,
                _ee_tgt_l, _ori_ref_l, _ori_mask,
                _IK_ALPHA, _IK_ORI_GAIN, 999.0, _IK_CLIP, device,
                cable_along_y=_hand_down,
            )
            ik_r, nan_r = jt_ik_step_6dof_batch(
                robot_right, jac_body_right, hand_body_right,
                _ee_tgt_r, _ori_ref_r, _ori_mask,
                _IK_ALPHA, _IK_ORI_GAIN, 999.0, _IK_CLIP, device,
                cable_along_y=_hand_down,
            )
            if nan_l.any() or nan_r.any():
                print(f"[GRASP] IK NaN at pass {_pass+1} step {step}")
                break

            # Lock j6 (wrist rotation) to prevent finger yaw drift
            ik_l[:, 6] = _j6_lock_l
            ik_r[:, 6] = _j6_lock_r

            tgt_l = robot_left.data.joint_pos.clone()
            tgt_l[env_idx, :7] = ik_l[env_idx]
            tgt_l[env_idx, 7] = GRIPPER_OPEN
            tgt_l[env_idx, 8] = GRIPPER_OPEN
            robot_left.set_joint_position_target(tgt_l)
            robot_left.write_data_to_sim()
            tgt_r = robot_right.data.joint_pos.clone()
            tgt_r[env_idx, :7] = ik_r[env_idx]
            tgt_r[env_idx, 7] = GRIPPER_OPEN
            tgt_r[env_idx, 8] = GRIPPER_OPEN
            robot_right.set_joint_position_target(tgt_r)
            robot_right.write_data_to_sim()

            for _ in range(4):
                sim.step()
                scene.update(sim.get_physics_dt())
            if on_step is not None and step % 5 == 0:
                on_step()
            if step % 5 == 0:
                _collect_obs(2.5)

            if torch.isnan(cable.data.body_pos_w).any():
                print(f"[GRASP] Cable NaN at pass {_pass+1} step {step}!")
                results["nan_detected"] = True
                return results

            _total_steps += 1

    results["fine_position_steps"] = _total_steps

    # Settle after fine-positioning (reduced from 50 to minimize cable drift)
    for _ in range(15):
        sim.step()
        scene.update(sim.get_physics_dt())
    if on_step is not None:
        on_step()

    # --- Diagnostic: confirm fingertip vs cable positions before grip ---
    ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
    ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
    _q_l = robot_left.data.body_quat_w[:, hand_body_left, :]
    _q_r = robot_right.data.body_quat_w[:, hand_body_right, :]
    _ft_pre_l = ee_to_fingertip_batch(ee_cur_l, _q_l)
    _ft_pre_r = ee_to_fingertip_batch(ee_cur_r, _q_r)
    # Check actual finger body positions (left finger and right finger of each hand)
    _lf_idx = int(robot_left.find_bodies("panda_leftfinger")[0][0])
    _rf_idx = int(robot_left.find_bodies("panda_rightfinger")[0][0])
    _lf_pos_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
    _rf_pos_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
    _lf_pos_r = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
    _rf_pos_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
    print(f"[GRASP] PRE-GRIP diagnostic:")
    print(f"[GRASP]   Left arm  ft=({_ft_pre_l[0,0].item():.4f},{_ft_pre_l[0,1].item():.4f},{_ft_pre_l[0,2].item():.4f})")
    print(f"[GRASP]   Left arm  leftfinger= ({_lf_pos_l[0].item():.4f},{_lf_pos_l[1].item():.4f},{_lf_pos_l[2].item():.4f})")
    print(f"[GRASP]   Left arm  rightfinger=({_rf_pos_l[0].item():.4f},{_rf_pos_l[1].item():.4f},{_rf_pos_l[2].item():.4f})")
    print(f"[GRASP]   Right arm ft=({_ft_pre_r[0,0].item():.4f},{_ft_pre_r[0,1].item():.4f},{_ft_pre_r[0,2].item():.4f})")
    print(f"[GRASP]   Right arm leftfinger= ({_lf_pos_r[0].item():.4f},{_lf_pos_r[1].item():.4f},{_lf_pos_r[2].item():.4f})")
    print(f"[GRASP]   Right arm rightfinger=({_rf_pos_r[0].item():.4f},{_rf_pos_r[1].item():.4f},{_rf_pos_r[2].item():.4f})")
    # Cable segment re-check (local frame)
    _cable_now_raw = cable.data.body_pos_w[env_idx, :, :3]
    _cable_now = _cable_now_raw - env_origin.unsqueeze(0) if env_origin is not None else _cable_now_raw
    _nearest_cable_l = _cable_now[_nearest_l]
    _nearest_cable_r = _cable_now[_nearest_r]
    _ft_cable_dist_l = torch.norm(_ft_pre_l[0] - _nearest_cable_l).item()
    _ft_cable_dist_r = torch.norm(_ft_pre_r[0] - _nearest_cable_r).item()
    print(f"[GRASP]   Target cable seg L[{_nearest_l}]=({_nearest_cable_l[0].item():.4f},{_nearest_cable_l[1].item():.4f},{_nearest_cable_l[2].item():.4f}) dist={_ft_cable_dist_l*1000:.1f}mm")
    print(f"[GRASP]   Target cable seg R[{_nearest_r}]=({_nearest_cable_r[0].item():.4f},{_nearest_cable_r[1].item():.4f},{_nearest_cable_r[2].item():.4f}) dist={_ft_cable_dist_r*1000:.1f}mm")
    # Finger-open direction (vector from leftfinger to rightfinger body) — should be perpendicular to cable
    _finger_open_l = _rf_pos_l - _lf_pos_l  # left arm finger-open direction
    _finger_open_r = _rf_pos_r - _lf_pos_r  # right arm finger-open direction
    _fo_norm_l = _finger_open_l / (torch.norm(_finger_open_l) + 1e-8)
    _fo_norm_r = _finger_open_r / (torch.norm(_finger_open_r) + 1e-8)
    # Cable runs ~along Y. Finger-open should be along X for perpendicular grip.
    print(f"[GRASP]   Finger-open dir L: ({_fo_norm_l[0].item():.3f},{_fo_norm_l[1].item():.3f},{_fo_norm_l[2].item():.3f}) "
          f"gap={torch.norm(_finger_open_l).item()*1000:.1f}mm")
    print(f"[GRASP]   Finger-open dir R: ({_fo_norm_r[0].item():.3f},{_fo_norm_r[1].item():.3f},{_fo_norm_r[2].item():.3f}) "
          f"gap={torch.norm(_finger_open_r).item()*1000:.1f}mm")
    print(f"[GRASP]   (Cable along Y. Ideal finger-open: X=±1.0. If Y-dominant, fingers parallel to cable → grip fails)")

    # --- Phase 2.6: Direct wrist rotation to align fingers ⊥ cable ---
    # Skip when hand is already oriented correctly (from overhead Phase 1.5).
    # Phase 2.6 only rotates joint7, which can UNDO the full 6DOF orientation convergence.
    _skip_phase_26 = False
    if _hand_down:
        # Always skip Phase 2.6 when hand-down: joint7 rotation destroys
        # the 6DOF orientation from overhead descent. Finger-open yaw drift
        # during Phase 2.5 is acceptable (small XY corrections with ori constraint).
        _skip_phase_26 = True
        print(f"[GRASP] Phase 2.6: SKIPPED (hand_down mode — wrist rotation would destroy overhead orientation)")

    # Cable along Y. Finger-open direction must be along ±X.
    # Directly control joint7 (wrist rotation) with closed-loop feedback.
    # Hold joints 0-5 at current values; only rotate joint7.
    _hold_j_l = robot_left.data.joint_pos[env_idx, :6].clone()
    _hold_j_r = robot_right.data.joint_pos[env_idx, :6].clone()

    def _fo_angle_and_norm(robot, _env_idx, _lf_i, _rf_i):
        lf = robot.data.body_pos_w[_env_idx, _lf_i, :3]
        rf = robot.data.body_pos_w[_env_idx, _rf_i, :3]
        fo = rf - lf
        angle = torch.atan2(fo[1], fo[0]).item()
        norm = fo / (torch.norm(fo) + 1e-8)
        return angle, norm

    _a_l, _fn_l = _fo_angle_and_norm(robot_left, env_idx, _lf_idx, _rf_idx)
    _a_r, _fn_r = _fo_angle_and_norm(robot_right, env_idx, _lf_idx, _rf_idx)

    _PI = 3.141593

    def _nearest_x_target(a):
        candidates = [0.0, _PI, -_PI]
        return min(candidates, key=lambda c: abs(a - c))

    _tgt_l = _nearest_x_target(_a_l)
    _tgt_r = _nearest_x_target(_a_r)
    _err_l = _tgt_l - _a_l
    _err_r = _tgt_r - _a_r

    print(f"[GRASP] Phase 2.6: Wrist rotation (direct joint7 control)")
    print(f"[GRASP]   L: angle={_a_l*180/_PI:.1f}° target={_tgt_l*180/_PI:.1f}° "
          f"correction={_err_l*180/_PI:.1f}° finger=({_fn_l[0].item():.3f},{_fn_l[1].item():.3f},{_fn_l[2].item():.3f})")
    print(f"[GRASP]   R: angle={_a_r*180/_PI:.1f}° target={_tgt_r*180/_PI:.1f}° "
          f"correction={_err_r*180/_PI:.1f}° finger=({_fn_r[0].item():.3f},{_fn_r[1].item():.3f},{_fn_r[2].item():.3f})")

    _SKIP_THRESH = 0.17  # ~10°
    if _skip_phase_26:
        pass  # Already printed skip message above
    elif abs(_err_l) < _SKIP_THRESH and abs(_err_r) < _SKIP_THRESH:
        print(f"[GRASP] Phase 2.6: Already aligned (< 10°), skipping")
    else:
        _SIGN = -1.0  # joint7↑ → angle↓ in overhead config
        _GAIN = 0.4
        _WRIST_STEPS = 60
        _CONVERGE = 0.17  # ~10°

        _sign_l = _SIGN
        _sign_r = _SIGN
        _prev_err_l = abs(_err_l)
        _prev_err_r = abs(_err_r)
        _flip_l = 0
        _flip_r = 0

        for step in range(_WRIST_STEPS):
            if STOP_REQUESTED:
                break

            _a_l, _ = _fo_angle_and_norm(robot_left, env_idx, _lf_idx, _rf_idx)
            _a_r, _ = _fo_angle_and_norm(robot_right, env_idx, _lf_idx, _rf_idx)
            _err_l = _tgt_l - _a_l
            _err_r = _tgt_r - _a_r

            # Auto-detect sign: if error magnitude increasing, flip once
            if step > 1:
                if abs(_err_l) > _prev_err_l + 0.03 and _flip_l < 2:
                    _sign_l *= -1
                    _flip_l += 1
                    print(f"[GRASP] Phase 2.6: Flipping L sign (err {abs(_err_l)*180/_PI:.1f}°→{_prev_err_l*180/_PI:.1f}°)")
                if abs(_err_r) > _prev_err_r + 0.03 and _flip_r < 2:
                    _sign_r *= -1
                    _flip_r += 1
                    print(f"[GRASP] Phase 2.6: Flipping R sign (err {abs(_err_r)*180/_PI:.1f}°→{_prev_err_r*180/_PI:.1f}°)")

            _conv_l = abs(_err_l) < _CONVERGE
            _conv_r = abs(_err_r) < _CONVERGE
            if _conv_l and _conv_r:
                print(f"[GRASP] Phase 2.6: Converged at step {step} "
                      f"(L={abs(_err_l)*180/_PI:.1f}° R={abs(_err_r)*180/_PI:.1f}°)")
                break

            _j7_l = robot_left.data.joint_pos[env_idx, 6].item()
            _j7_r = robot_right.data.joint_pos[env_idx, 6].item()
            _dj7_l = _sign_l * _GAIN * _err_l if not _conv_l else 0.0
            _dj7_r = _sign_r * _GAIN * _err_r if not _conv_r else 0.0
            _j7_new_l = max(-2.8973, min(2.8973, _j7_l + _dj7_l))
            _j7_new_r = max(-2.8973, min(2.8973, _j7_r + _dj7_r))

            tgt_l = robot_left.data.joint_pos.clone()
            tgt_l[env_idx, :6] = _hold_j_l
            tgt_l[env_idx, 6] = _j7_new_l
            tgt_l[env_idx, 7] = GRIPPER_OPEN
            tgt_l[env_idx, 8] = GRIPPER_OPEN
            robot_left.set_joint_position_target(tgt_l)
            robot_left.write_data_to_sim()

            tgt_r = robot_right.data.joint_pos.clone()
            tgt_r[env_idx, :6] = _hold_j_r
            tgt_r[env_idx, 6] = _j7_new_r
            tgt_r[env_idx, 7] = GRIPPER_OPEN
            tgt_r[env_idx, 8] = GRIPPER_OPEN
            robot_right.set_joint_position_target(tgt_r)
            robot_right.write_data_to_sim()

            for _ in range(4):
                sim.step()
                scene.update(sim.get_physics_dt())

            _prev_err_l = abs(_err_l)
            _prev_err_r = abs(_err_r)

            if step % 10 == 0:
                print(f"[GRASP] Phase 2.6 step={step} "
                      f"L: angle={_a_l*180/_PI:.1f}° err={abs(_err_l)*180/_PI:.1f}° j7={_j7_new_l:.3f} "
                      f"R: angle={_a_r*180/_PI:.1f}° err={abs(_err_r)*180/_PI:.1f}° j7={_j7_new_r:.3f}")

    # Final measurement
    _a_l, _fn_l = _fo_angle_and_norm(robot_left, env_idx, _lf_idx, _rf_idx)
    _a_r, _fn_r = _fo_angle_and_norm(robot_right, env_idx, _lf_idx, _rf_idx)
    _gc_l = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
             robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
    _gc_r = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
             robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
    _gc2c_l = torch.norm(_gc_l[:2] - _cable_target_l[:2]).item()
    _gc2c_r = torch.norm(_gc_r[:2] - _cable_target_r[:2]).item()
    print(f"[GRASP] Phase 2.6 done: finger-open L=({_fn_l[0].item():.3f},{_fn_l[1].item():.3f},{_fn_l[2].item():.3f}) "
          f"R=({_fn_r[0].item():.3f},{_fn_r[1].item():.3f},{_fn_r[2].item():.3f})")
    print(f"[GRASP] Phase 2.6 done: gc2cable L={_gc2c_l*1000:.1f}mm R={_gc2c_r*1000:.1f}mm "
          f"(position drift from rotation → Phase 2.7 will correct)")

    # --- Phase 2.7: Single-shot drift correction (NO multi-step loop) ---
    # Old approach: 50-step correction loop × 4 substeps = 200 sim steps causing MORE drift.
    # New approach: Re-read cable position, compute a single IK correction, apply it as the
    # frozen arm hold position for Phase 3. Zero additional sim steps.
    _cable_now_raw = cable.data.body_pos_w[env_idx, :, :3].clone()
    _cable_now_local = _cable_now_raw - env_origin.unsqueeze(0) if env_origin is not None else _cable_now_raw
    _seg_now_l = _cable_now_local[_nearest_l]
    _seg_now_r = _cable_now_local[_nearest_r]
    _drift_l = torch.norm(_seg_now_l[:2] - _cable_target_l[:2]).item()
    _drift_r = torch.norm(_seg_now_r[:2] - _cable_target_r[:2]).item()
    _gc_l = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
             robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
    _gc_r = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
             robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
    _gc2c_now_l = torch.norm(_gc_l[:2] - _seg_now_l[:2]).item()
    _gc2c_now_r = torch.norm(_gc_r[:2] - _seg_now_r[:2]).item()
    print(f"[GRASP] Phase 2.7: Cable re-read (single-shot). seg[{_nearest_l}] drifted {_drift_l*1000:.1f}mm, "
          f"seg[{_nearest_r}] drifted {_drift_r*1000:.1f}mm since Phase 2.5 start")
    print(f"[GRASP] Phase 2.7: gc2cable L={_gc2c_now_l*1000:.1f}mm R={_gc2c_now_r*1000:.1f}mm")

    # Compute single IK correction: shift EE by (cable_now - grip_center) to align grip to cable
    _drift_correction_applied = False
    if _gc2c_now_l > 3.0e-3 or _gc2c_now_r > 3.0e-3:  # >3mm → worth correcting
        _ee_delta_l = _seg_now_l - _gc_l  # XYZ error from grip center to current cable
        _ee_delta_r = _seg_now_r - _gc_r
        _ee_delta_l[2] = 0.0  # Don't change Z (already at table height)
        _ee_delta_r[2] = 0.0
        # Single IK step to compute corrected arm joints
        _ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
        _ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
        _ee_corrected_l = _ee_cur_l + _ee_delta_l.unsqueeze(0)
        _ee_corrected_r = _ee_cur_r + _ee_delta_r.unsqueeze(0)
        # Orientation reference: point below EE (maintain downward when _hand_down)
        _ori27_l = _ee_cur_l.clone(); _ori27_l[:, 2] -= 0.1
        _ori27_r = _ee_cur_r.clone(); _ori27_r[:, 2] -= 0.1
        _ik_corr_l, _nan_l = jt_ik_step_6dof_batch(
            robot_left, jac_body_left, hand_body_left,
            _ee_corrected_l, _ori27_l, _ori_mask,
            _IK_ALPHA, _IK_ORI_GAIN, 999.0, _IK_CLIP, device,
            cable_along_y=_hand_down)
        _ik_corr_r, _nan_r = jt_ik_step_6dof_batch(
            robot_right, jac_body_right, hand_body_right,
            _ee_corrected_r, _ori27_r, _ori_mask,
            _IK_ALPHA, _IK_ORI_GAIN, 999.0, _IK_CLIP, device,
            cable_along_y=_hand_down)
        if not _nan_l.any() and not _nan_r.any():
            # Apply corrected joints + short settle (10 substeps, not 200)
            tgt_l = robot_left.data.joint_pos.clone()
            tgt_l[env_idx, :7] = _ik_corr_l[env_idx]
            tgt_l[env_idx, 7] = GRIPPER_OPEN
            tgt_l[env_idx, 8] = GRIPPER_OPEN
            robot_left.set_joint_position_target(tgt_l)
            robot_left.write_data_to_sim()
            tgt_r = robot_right.data.joint_pos.clone()
            tgt_r[env_idx, :7] = _ik_corr_r[env_idx]
            tgt_r[env_idx, 7] = GRIPPER_OPEN
            tgt_r[env_idx, 8] = GRIPPER_OPEN
            robot_right.set_joint_position_target(tgt_r)
            robot_right.write_data_to_sim()
            for _ in range(10):
                sim.step()
                scene.update(sim.get_physics_dt())
            _drift_correction_applied = True
            # Report final gc2cable after correction
            _gc_l2 = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
                       robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
            _gc_r2 = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
                       robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
            _cable_fresh = cable.data.body_pos_w[env_idx, :, :3].clone()
            if env_origin is not None:
                _cable_fresh = _cable_fresh - env_origin.unsqueeze(0)
            _gc2c_final_l = torch.norm(_cable_fresh[_nearest_l, :2] - _gc_l2[:2]).item()
            _gc2c_final_r = torch.norm(_cable_fresh[_nearest_r, :2] - _gc_r2[:2]).item()
            print(f"[GRASP] Phase 2.7: Single-shot correction applied "
                  f"(delta_L={torch.norm(_ee_delta_l[:2]).item()*1000:.1f}mm "
                  f"delta_R={torch.norm(_ee_delta_r[:2]).item()*1000:.1f}mm)")
            print(f"[GRASP] Phase 2.7: gc2cable after correction L={_gc2c_final_l*1000:.1f}mm R={_gc2c_final_r*1000:.1f}mm")
        else:
            print(f"[GRASP] Phase 2.7: IK correction produced NaN, skipping")
    else:
        print(f"[GRASP] Phase 2.7: gc2cable < 3mm, skipping correction")

    # --- Phase 2.9 sequential: Z descent → XY correction → j6 wrist rotation (v13e) ---
    # Three sequential phases with round-based convergence.
    if _hand_down:
        import math
        def _nearest_x_angle(a):
            candidates = [0.0, math.pi, -math.pi]
            return min(candidates, key=lambda c: abs(a - c))

        _cable_pos_29 = cable.data.body_pos_w[env_idx, :, :3].clone()
        if env_origin is not None:
            _cable_pos_29 -= env_origin.unsqueeze(0)
        _cable_z_29 = _cable_pos_29[_nearest_l, 2].item()
        _CABLE_RADIUS = 0.005

        _ee_z_l_pre = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item()
        _ee_z_r_pre = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()
        _ft_z_l_pre = _ee_z_l_pre - FINGERTIP_OFFSET
        _ft_z_r_pre = _ee_z_r_pre - FINGERTIP_OFFSET

        print(f"[GRASP] Phase 2.9 sequential (v13e): Z descent → XY correction → j6 rotation")
        print(f"[GRASP]   ft_above_cable: L={(_ft_z_l_pre-_cable_z_29)*1000:.1f}mm R={(_ft_z_r_pre-_cable_z_29)*1000:.1f}mm")

        # --- Phase 2.9 + 2.95 rounds: Z descent with 10% XY, then full XY correction ---
        _N_envs = robot_left.data.joint_pos.shape[0]
        _ori_mask_29 = torch.zeros(_N_envs, dtype=torch.bool, device=device)  # orientation disabled
        _P29_MAX_ROUNDS = PHASE_TIMEOUT.get("P29_rounds", 5)
        _P29_STEPS = PHASE_TIMEOUT.get("P29", 150)
        _P295_STEPS = PHASE_TIMEOUT.get("P295", 100)
        _ee_init_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
        _ee_init_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

        for _round in range(_P29_MAX_ROUNDS):
            if STOP_REQUESTED:
                break

            # Re-read cable
            _cable_pos_29 = cable.data.body_pos_w[env_idx, :, :3].clone()
            if env_origin is not None:
                _cable_pos_29 -= env_origin.unsqueeze(0)
            _cable_z_29 = _cable_pos_29[_nearest_l, 2].item()
            _ee_tgt_z_29 = _cable_z_29 + FINGERTIP_OFFSET  # FT at cable center

            # Phase 2.9: Z descent with 10% XY hold
            print(f"[GRASP] Phase 2.9 round={_round}: Z descent (10% XY hold)")
            for _s29 in range(_P29_STEPS):
                if STOP_REQUESTED:
                    break
                _ee_l_now = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
                _ee_r_now = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
                _gc_l_29 = (robot_left.data.body_pos_w[env_idx, _lf_idx, :2] +
                            robot_left.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
                _gc_r_29 = (robot_right.data.body_pos_w[env_idx, _lf_idx, :2] +
                            robot_right.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0

                # XY target: 10% correction toward cable XY
                _tgt_l = _ee_l_now.clone()
                _tgt_r = _ee_r_now.clone()
                _xy_err_l = _cable_pos_29[_nearest_l, :2] - _gc_l_29
                _xy_err_r = _cable_pos_29[_nearest_r, :2] - _gc_r_29
                _tgt_l[:, :2] += 0.1 * _xy_err_l.unsqueeze(0)
                _tgt_r[:, :2] += 0.1 * _xy_err_r.unsqueeze(0)
                _tgt_l[:, 2] = _ee_tgt_z_29
                _tgt_r[:, 2] = _ee_tgt_z_29

                _ori_ref_l = _tgt_l.clone(); _ori_ref_l[:, 2] -= 0.1
                _ori_ref_r = _tgt_r.clone(); _ori_ref_r[:, 2] -= 0.1
                ik_l_29, _nan_l = jt_ik_step_6dof_batch(
                    robot_left, jac_body_left, hand_body_left,
                    _tgt_l, _ori_ref_l, _ori_mask_29,
                    40.0, 0.0, 999.0, 0.015, device, cable_along_y=True)
                ik_r_29, _nan_r = jt_ik_step_6dof_batch(
                    robot_right, jac_body_right, hand_body_right,
                    _tgt_r, _ori_ref_r, _ori_mask_29,
                    40.0, 0.0, 999.0, 0.015, device, cable_along_y=True)
                if _nan_l.any() or _nan_r.any():
                    break
                tgt_l = robot_left.data.joint_pos.clone()
                tgt_l[env_idx, :7] = ik_l_29[env_idx]; tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
                robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
                tgt_r = robot_right.data.joint_pos.clone()
                tgt_r[env_idx, :7] = ik_r_29[env_idx]; tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
                robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
                for _ in range(4):
                    sim.step(); scene.update(sim.get_physics_dt())
                if on_step is not None and _s29 % 5 == 0:
                    on_step()
                if _s29 % 5 == 0:
                    _collect_obs(2.9)
                if _s29 % 30 == 0:
                    _ft_z_l_ck = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - FINGERTIP_OFFSET
                    _ft_z_r_ck = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - FINGERTIP_OFFSET
                    _gc2c_l_ck = torch.norm(_gc_l_29 - _cable_pos_29[_nearest_l, :2]).item()
                    _gc2c_r_ck = torch.norm(_gc_r_29 - _cable_pos_29[_nearest_r, :2]).item()
                    print(f"[GRASP] Phase 2.9 r={_round} s={_s29} "
                          f"gap: L={(_ft_z_l_ck-_cable_z_29)*1000:.1f}mm R={(_ft_z_r_ck-_cable_z_29)*1000:.1f}mm "
                          f"gc2cable: L={_gc2c_l_ck*1000:.1f}mm R={_gc2c_r_ck*1000:.1f}mm")
                    _p29_z_thresh = PHASE_TRANSITION.get("P29_z_converge_mm", 3.0) / 1000.0
                    if abs(_ft_z_l_ck - _cable_z_29) < _p29_z_thresh and abs(_ft_z_r_ck - _cable_z_29) < _p29_z_thresh:
                        print(f"[GRASP] Phase 2.9: Z converged at step {_s29}")
                        break

            # Phase 2.95: Full XY correction (re-read cable, correct gc2cable)
            _cable_pos_295 = cable.data.body_pos_w[env_idx, :, :3].clone()
            if env_origin is not None:
                _cable_pos_295 -= env_origin.unsqueeze(0)
            _cable_z_295 = _cable_pos_295[_nearest_l, 2].item()
            print(f"[GRASP] Phase 2.95 round={_round}: Full XY correction")
            for _s295 in range(_P295_STEPS):
                if STOP_REQUESTED:
                    break
                _gc_l_295 = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
                             robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
                _gc_r_295 = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
                             robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
                _ee_l_295 = robot_left.data.body_pos_w[:, hand_body_left, :3]
                _ee_r_295 = robot_right.data.body_pos_w[:, hand_body_right, :3]
                _tgt_l_295 = _ee_l_295.clone()
                _tgt_r_295 = _ee_r_295.clone()
                _tgt_l_295[:, :2] += (_cable_pos_295[_nearest_l, :2] - _gc_l_295[:2]).unsqueeze(0)
                _tgt_r_295[:, :2] += (_cable_pos_295[_nearest_r, :2] - _gc_r_295[:2]).unsqueeze(0)
                _tgt_l_295[:, 2] = _cable_z_295 + FINGERTIP_OFFSET
                _tgt_r_295[:, 2] = _cable_z_295 + FINGERTIP_OFFSET
                _ori_ref_l_295 = _tgt_l_295.clone(); _ori_ref_l_295[:, 2] -= 0.1
                _ori_ref_r_295 = _tgt_r_295.clone(); _ori_ref_r_295[:, 2] -= 0.1
                ik_l_295, _nan_l = jt_ik_step_6dof_batch(
                    robot_left, jac_body_left, hand_body_left,
                    _tgt_l_295, _ori_ref_l_295, _ori_mask_29,
                    20.0, 0.0, 999.0, 0.015, device, cable_along_y=True)
                ik_r_295, _nan_r = jt_ik_step_6dof_batch(
                    robot_right, jac_body_right, hand_body_right,
                    _tgt_r_295, _ori_ref_r_295, _ori_mask_29,
                    20.0, 0.0, 999.0, 0.015, device, cable_along_y=True)
                if _nan_l.any() or _nan_r.any():
                    break
                tgt_l = robot_left.data.joint_pos.clone()
                tgt_l[env_idx, :7] = ik_l_295[env_idx]; tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
                robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
                tgt_r = robot_right.data.joint_pos.clone()
                tgt_r[env_idx, :7] = ik_r_295[env_idx]; tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
                robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
                for _ in range(4):
                    sim.step(); scene.update(sim.get_physics_dt())
                if on_step is not None and _s295 % 5 == 0:
                    on_step()
                if _s295 % 5 == 0:
                    _collect_obs(2.95)
                if _s295 % 30 == 0:
                    _gc2c_l_295 = torch.norm(_gc_l_295[:2] - _cable_pos_295[_nearest_l, :2]).item()
                    _gc2c_r_295 = torch.norm(_gc_r_295[:2] - _cable_pos_295[_nearest_r, :2]).item()
                    _ft_z_l_295 = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - FINGERTIP_OFFSET
                    _ft_z_r_295 = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - FINGERTIP_OFFSET
                    print(f"[GRASP] Phase 2.95 r={_round} s={_s295} "
                          f"gc2cable: L={_gc2c_l_295*1000:.1f}mm R={_gc2c_r_295*1000:.1f}mm "
                          f"gap: L={(_ft_z_l_295-_cable_z_295)*1000:.1f}mm R={(_ft_z_r_295-_cable_z_295)*1000:.1f}mm")
                    _p295_xy_thresh = PHASE_TRANSITION.get("P295_xy_converge_mm", 5.0) / 1000.0
                    if _gc2c_l_295 < _p295_xy_thresh and _gc2c_r_295 < _p295_xy_thresh:
                        print(f"[GRASP] Phase 2.95: XY converged at step {_s295}")
                        break

            # Round convergence check
            _ft_z_l_rck = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - FINGERTIP_OFFSET
            _ft_z_r_rck = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - FINGERTIP_OFFSET
            _gc_l_rck = (robot_left.data.body_pos_w[env_idx, _lf_idx, :2] +
                         robot_left.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
            _gc_r_rck = (robot_right.data.body_pos_w[env_idx, _lf_idx, :2] +
                         robot_right.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
            _cable_pos_rck = cable.data.body_pos_w[env_idx, :, :3].clone()
            if env_origin is not None:
                _cable_pos_rck -= env_origin.unsqueeze(0)
            _gc2c_l_rck = torch.norm(_gc_l_rck - _cable_pos_rck[_nearest_l, :2]).item()
            _gc2c_r_rck = torch.norm(_gc_r_rck - _cable_pos_rck[_nearest_r, :2]).item()
            _cable_z_rck = _cable_pos_rck[_nearest_l, 2].item()
            print(f"[GRASP] Round {_round} done: Z gap L={(_ft_z_l_rck-_cable_z_rck)*1000:.1f}mm "
                  f"R={(_ft_z_r_rck-_cable_z_rck)*1000:.1f}mm "
                  f"gc2cable L={_gc2c_l_rck*1000:.1f}mm R={_gc2c_r_rck*1000:.1f}mm")
            _p29_rnd_z_thresh = PHASE_TRANSITION.get("P29_round_z_mm", 3.0) / 1000.0
            _p29_rnd_xy_thresh = PHASE_TRANSITION.get("P29_round_xy_mm", 5.0) / 1000.0
            if abs(_ft_z_l_rck - _cable_z_rck) < _p29_rnd_z_thresh and abs(_ft_z_r_rck - _cable_z_rck) < _p29_rnd_z_thresh and \
               _gc2c_l_rck < _p29_rnd_xy_thresh and _gc2c_r_rck < _p29_rnd_xy_thresh:
                print(f"[GRASP] Rounds converged at round {_round}")
                break

        # Record Phase 2.9 completion fingertip Z
        _ft_z_p29_l = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - FINGERTIP_OFFSET
        _ft_z_p29_r = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - FINGERTIP_OFFSET
        results["ft_z_after_p29_left"] = round(_ft_z_p29_l, 6)
        results["ft_z_after_p29_right"] = round(_ft_z_p29_r, 6)
        print(f"[MEASURE] Phase 2.9 done: ft_z L={_ft_z_p29_l:.4f}m R={_ft_z_p29_r:.4f}m")

        # --- Phase 2.99: Interleaved j6 rotation + position re-centering ---
        # Probe-based j6 sign detection
        _fo_pre_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3] - robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
        _fo_pre_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3] - robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
        _fo_angle_l = torch.atan2(_fo_pre_l[1], _fo_pre_l[0]).item()
        _fo_angle_r = torch.atan2(_fo_pre_r[1], _fo_pre_r[0]).item()
        _tgt_angle_l = _nearest_x_angle(_fo_angle_l)
        _tgt_angle_r = _nearest_x_angle(_fo_angle_r)
        _fox_pre_l = (_fo_pre_l[0] / (torch.norm(_fo_pre_l) + 1e-8)).item()
        _fox_pre_r = (_fo_pre_r[0] / (torch.norm(_fo_pre_r) + 1e-8)).item()

        _hold_l_probe = robot_left.data.joint_pos[env_idx, :6].clone()
        _hold_r_probe = robot_right.data.joint_pos[env_idx, :6].clone()
        _j6_save_l = robot_left.data.joint_pos[env_idx, 6].clone()
        _j6_save_r = robot_right.data.joint_pos[env_idx, 6].clone()
        _PROBE_SIZE = 0.15
        _err_before_l = abs(_tgt_angle_l - _fo_angle_l)
        _err_before_r = abs(_tgt_angle_r - _fo_angle_r)
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :6] = _hold_l_probe; tgt_l[env_idx, 6] = _j6_save_l.item() + _PROBE_SIZE
        tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :6] = _hold_r_probe; tgt_r[env_idx, 6] = _j6_save_r.item() + _PROBE_SIZE
        tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        for _ in range(8):
            sim.step(); scene.update(sim.get_physics_dt())
        _fo_pr_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3] - robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
        _fo_pr_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3] - robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
        _probe_sign_l = 1.0 if abs(_tgt_angle_l - torch.atan2(_fo_pr_l[1], _fo_pr_l[0]).item()) < _err_before_l else -1.0
        _probe_sign_r = 1.0 if abs(_tgt_angle_r - torch.atan2(_fo_pr_r[1], _fo_pr_r[0]).item()) < _err_before_r else -1.0
        # Hardcode signs for ceiling-mounted Franka:
        # Left arm: +1 (j6 increase → fo_X toward -1.0)
        # Right arm: -1 (j6 decrease → fo_X toward +1.0)
        _sign_l = 1.0
        _sign_r = -1.0
        print(f"[GRASP] Phase 2.99: j6 signs: L={_sign_l:+.0f} R={_sign_r:+.0f} (probe: L={_probe_sign_l:+.0f} R={_probe_sign_r:+.0f}) "
              f"fo_X: L={_fox_pre_l:.3f} R={_fox_pre_r:.3f}")
        # Restore probe
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :6] = _hold_l_probe; tgt_l[env_idx, 6] = _j6_save_l.item()
        tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :6] = _hold_r_probe; tgt_r[env_idx, 6] = _j6_save_r.item()
        tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        for _ in range(8):
            sim.step(); scene.update(sim.get_physics_dt())

        # Interleaved j6 rotation + position re-centering
        _P299_MAX_ITERS = PHASE_TIMEOUT.get("P299", 200)
        _P299_J6_STEPS = 20
        _P299_J6_RATE = 0.06  # rad/step (v13e original)
        _P299_XY_STEPS = 40  # v13e original
        _P299_XY_ALPHA = 30.0
        _P299_XY_CLIP = 0.015
        _p299_total = 0

        for _p299_iter in range(_P299_MAX_ITERS):
            if STOP_REQUESTED:
                break
            # Measure current state
            _fo_299_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3] - robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
            _fo_299_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3] - robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
            _fox_299_l = (_fo_299_l[0] / (torch.norm(_fo_299_l) + 1e-8)).item()
            _fox_299_r = (_fo_299_r[0] / (torch.norm(_fo_299_r) + 1e-8)).item()
            _gc_299_l = (robot_left.data.body_pos_w[env_idx, _lf_idx, :2] +
                         robot_left.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
            _gc_299_r = (robot_right.data.body_pos_w[env_idx, _lf_idx, :2] +
                         robot_right.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
            _cable_pos_299 = cable.data.body_pos_w[env_idx, :, :3].clone()
            if env_origin is not None:
                _cable_pos_299 -= env_origin.unsqueeze(0)
            _gc2c_299_l = torch.norm(_gc_299_l - _cable_pos_299[_nearest_l, :2]).item()
            _gc2c_299_r = torch.norm(_gc_299_r - _cable_pos_299[_nearest_r, :2]).item()
            _ft_z_299_l = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - FINGERTIP_OFFSET
            _ft_z_299_r = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - FINGERTIP_OFFSET
            _cable_z_299 = _cable_pos_299[_nearest_l, 2].item()

            print(f"[GRASP] Phase 2.99 iter={_p299_iter} fo_X: L={_fox_299_l:.3f} R={_fox_299_r:.3f} "
                  f"gc2cable: L={_gc2c_299_l*1000:.1f}mm R={_gc2c_299_r*1000:.1f}mm "
                  f"ft_gap: L={(_ft_z_299_l-_cable_z_299)*1000:.1f}mm R={(_ft_z_299_r-_cable_z_299)*1000:.1f}mm")

            # Convergence: fo_X > threshold AND gc2cable < threshold AND ft_gap < threshold
            _p299_fox_thresh = PHASE_TRANSITION.get("P299_fo_x_min", 0.80)
            _p299_z_thresh = PHASE_TRANSITION.get("P299_z_gap_mm", 3.0) / 1000.0
            _p299_xy_thresh = PHASE_TRANSITION.get("P299_xy_mm", 3.0) / 1000.0
            if abs(_fox_299_l) > _p299_fox_thresh and abs(_fox_299_r) > _p299_fox_thresh and \
               _gc2c_299_l < _p299_xy_thresh and _gc2c_299_r < _p299_xy_thresh and \
               abs(_ft_z_299_l - _cable_z_299) < _p299_z_thresh and abs(_ft_z_299_r - _cable_z_299) < _p299_z_thresh:
                print(f"[GRASP] Phase 2.99: CONVERGED at iter {_p299_iter} ({_p299_total} total steps)")
                break

            # Guard: stop if gc2cable drift exceeds 10mm after initial iterations
            if _p299_iter >= 3 and (_gc2c_299_l > 0.010 or _gc2c_299_r > 0.010):
                print(f"[GRASP] Phase 2.99: gc2cable drift guard triggered at iter {_p299_iter} "
                      f"(L={_gc2c_299_l*1000:.1f}mm R={_gc2c_299_r*1000:.1f}mm > 10mm)")
                break

            # Step A: j6 rotation (20 steps, j0-j5 held)
            _J6_FOX_STOP = 0.83  # Close to convergence threshold (0.80) to minimize single-arm drift
            if abs(_fox_299_l) < _J6_FOX_STOP or abs(_fox_299_r) < _J6_FOX_STOP:
                _j0_5_hold_l = robot_left.data.joint_pos[env_idx, :6].clone()
                _j0_5_hold_r = robot_right.data.joint_pos[env_idx, :6].clone()
                for _jr in range(_P299_J6_STEPS):
                    _j6_cur_l = robot_left.data.joint_pos[env_idx, 6].item()
                    _j6_cur_r = robot_right.data.joint_pos[env_idx, 6].item()
                    _fo_jr_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3] - robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
                    _fo_jr_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3] - robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
                    _fox_jr_l = (_fo_jr_l[0] / (torch.norm(_fo_jr_l) + 1e-8)).item()
                    _fox_jr_r = (_fo_jr_r[0] / (torch.norm(_fo_jr_r) + 1e-8)).item()
                    _new_j6_l = _j6_cur_l + (_sign_l * _P299_J6_RATE if abs(_fox_jr_l) < _J6_FOX_STOP else 0.0)
                    _new_j6_r = _j6_cur_r + (_sign_r * _P299_J6_RATE if abs(_fox_jr_r) < _J6_FOX_STOP else 0.0)
                    tgt_l = robot_left.data.joint_pos.clone()
                    tgt_l[env_idx, :6] = _j0_5_hold_l
                    tgt_l[env_idx, 6] = _new_j6_l
                    tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
                    robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
                    tgt_r = robot_right.data.joint_pos.clone()
                    tgt_r[env_idx, :6] = _j0_5_hold_r
                    tgt_r[env_idx, 6] = _new_j6_r
                    tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
                    robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
                    sim.step(); scene.update(sim.get_physics_dt())
                    _p299_total += 1
                    if _jr % 5 == 0:
                        _collect_obs(2.99)

            # Step B: Position re-centering (40 steps, j6 locked, no orientation)
            _j6_lock_iter_l = robot_left.data.joint_pos[env_idx, 6].clone()
            _j6_lock_iter_r = robot_right.data.joint_pos[env_idx, 6].clone()
            for _xys in range(_P299_XY_STEPS):
                _cable_pos_xy = cable.data.body_pos_w[env_idx, :, :3].clone()
                if env_origin is not None:
                    _cable_pos_xy -= env_origin.unsqueeze(0)
                _gc_l_xy = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
                            robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
                _gc_r_xy = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
                            robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
                _ee_l_xy = robot_left.data.body_pos_w[:, hand_body_left, :3]
                _ee_r_xy = robot_right.data.body_pos_w[:, hand_body_right, :3]
                _tgt_l_xy = _ee_l_xy.clone()
                _tgt_r_xy = _ee_r_xy.clone()
                _tgt_l_xy[:, :2] += (_cable_pos_xy[_nearest_l, :2] - _gc_l_xy[:2]).unsqueeze(0)
                _tgt_r_xy[:, :2] += (_cable_pos_xy[_nearest_r, :2] - _gc_r_xy[:2]).unsqueeze(0)
                _cable_z_xy = _cable_pos_xy[_nearest_l, 2].item()
                _tgt_l_xy[:, 2] = _cable_z_xy + FINGERTIP_OFFSET
                _tgt_r_xy[:, 2] = _cable_z_xy + FINGERTIP_OFFSET
                _ori_ref_l_xy = _tgt_l_xy.clone(); _ori_ref_l_xy[:, 2] -= 0.1
                _ori_ref_r_xy = _tgt_r_xy.clone(); _ori_ref_r_xy[:, 2] -= 0.1
                ik_l_xy, _nan_l = jt_ik_step_6dof_batch(
                    robot_left, jac_body_left, hand_body_left,
                    _tgt_l_xy, _ori_ref_l_xy, _ori_mask_29,
                    _P299_XY_ALPHA, 0.0, 999.0, _P299_XY_CLIP, device, cable_along_y=True)
                ik_r_xy, _nan_r = jt_ik_step_6dof_batch(
                    robot_right, jac_body_right, hand_body_right,
                    _tgt_r_xy, _ori_ref_r_xy, _ori_mask_29,
                    _P299_XY_ALPHA, 0.0, 999.0, _P299_XY_CLIP, device, cable_along_y=True)
                if not _nan_l.any():
                    ik_l_xy[:, 6] = _j6_lock_iter_l
                if not _nan_r.any():
                    ik_r_xy[:, 6] = _j6_lock_iter_r
                tgt_l = robot_left.data.joint_pos.clone()
                tgt_l[env_idx, :7] = ik_l_xy[env_idx] if not _nan_l.any() else tgt_l[env_idx, :7]
                tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
                robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
                tgt_r = robot_right.data.joint_pos.clone()
                tgt_r[env_idx, :7] = ik_r_xy[env_idx] if not _nan_r.any() else tgt_r[env_idx, :7]
                tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
                robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
                sim.step(); scene.update(sim.get_physics_dt())
                _p299_total += 1
                if _xys % 10 == 0:
                    _collect_obs(2.99)

        # Final j6 lock
        _j6_lock_l = robot_left.data.joint_pos[env_idx, 6].clone()
        _j6_lock_r = robot_right.data.joint_pos[env_idx, 6].clone()
        _fo_fin_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3] - robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
        _fo_fin_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3] - robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
        _fox_fin_l = (_fo_fin_l[0] / (torch.norm(_fo_fin_l) + 1e-8)).item()
        _fox_fin_r = (_fo_fin_r[0] / (torch.norm(_fo_fin_r) + 1e-8)).item()
        _gc_fin_l = (robot_left.data.body_pos_w[env_idx, _lf_idx, :2] + robot_left.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
        _gc_fin_r = (robot_right.data.body_pos_w[env_idx, _lf_idx, :2] + robot_right.data.body_pos_w[env_idx, _rf_idx, :2]) / 2.0
        _cable_pos_fin = cable.data.body_pos_w[env_idx, :, :3].clone()
        if env_origin is not None:
            _cable_pos_fin -= env_origin.unsqueeze(0)
        _gc2c_fin_l = torch.norm(_gc_fin_l - _cable_pos_fin[_nearest_l, :2]).item()
        _gc2c_fin_r = torch.norm(_gc_fin_r - _cable_pos_fin[_nearest_r, :2]).item()
        _ft_z_fin_l = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - FINGERTIP_OFFSET
        _ft_z_fin_r = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - FINGERTIP_OFFSET
        _cable_z_fin = _cable_pos_fin[_nearest_l, 2].item()
        print(f"[GRASP] Phase 2.99 done: fo_X: L={_fox_fin_l:.3f} R={_fox_fin_r:.3f} "
              f"gc2cable: L={_gc2c_fin_l*1000:.1f}mm R={_gc2c_fin_r*1000:.1f}mm "
              f"ft_gap: L={(_ft_z_fin_l-_cable_z_fin)*1000:.1f}mm R={(_ft_z_fin_r-_cable_z_fin)*1000:.1f}mm")
        results["fo_x_after_p299_left"] = round(_fox_fin_l, 4)
        results["fo_x_after_p299_right"] = round(_fox_fin_r, 4)
        print(f"[MEASURE] Phase 2.99 done: fo_X L={_fox_fin_l:.3f} R={_fox_fin_r:.3f}")

        # --- Phase 2.995: Final position correction (j6 locked, ori disabled) ---
        # Fix residual gc2cable and ft_gap drift from Phase 2.99 rotation
        if _gc2c_fin_l > 0.002 or _gc2c_fin_r > 0.002 or \
           abs(_ft_z_fin_l - _cable_z_fin) > 0.002 or abs(_ft_z_fin_r - _cable_z_fin) > 0.002:
            _p2995_max = PHASE_TIMEOUT.get("P2995", 100)
            print(f"[GRASP] Phase 2.995: Final position correction ({_p2995_max} steps, j6 locked)")
            for _p2995 in range(_p2995_max):
                _cable_pos_fc = cable.data.body_pos_w[env_idx, :, :3].clone()
                if env_origin is not None:
                    _cable_pos_fc -= env_origin.unsqueeze(0)
                _gc_fc_l = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
                            robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
                _gc_fc_r = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
                            robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
                _ee_fc_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
                _ee_fc_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
                _tgt_fc_l = _ee_fc_l.clone()
                _tgt_fc_r = _ee_fc_r.clone()
                _tgt_fc_l[:, :2] += (_cable_pos_fc[_nearest_l, :2] - _gc_fc_l[:2]).unsqueeze(0)
                _tgt_fc_r[:, :2] += (_cable_pos_fc[_nearest_r, :2] - _gc_fc_r[:2]).unsqueeze(0)
                _cable_z_fc = _cable_pos_fc[_nearest_l, 2].item()
                _tgt_fc_l[:, 2] = _cable_z_fc + FINGERTIP_OFFSET
                _tgt_fc_r[:, 2] = _cable_z_fc + FINGERTIP_OFFSET
                _ori_fc_l = _tgt_fc_l.clone(); _ori_fc_l[:, 2] -= 0.1
                _ori_fc_r = _tgt_fc_r.clone(); _ori_fc_r[:, 2] -= 0.1
                ik_fc_l, _nan_l = jt_ik_step_6dof_batch(
                    robot_left, jac_body_left, hand_body_left,
                    _tgt_fc_l, _ori_fc_l, _ori_mask_29,
                    _P299_XY_ALPHA, 0.0, 999.0, _P299_XY_CLIP, device, cable_along_y=True)
                ik_fc_r, _nan_r = jt_ik_step_6dof_batch(
                    robot_right, jac_body_right, hand_body_right,
                    _tgt_fc_r, _ori_fc_r, _ori_mask_29,
                    _P299_XY_ALPHA, 0.0, 999.0, _P299_XY_CLIP, device, cable_along_y=True)
                if not _nan_l.any():
                    ik_fc_l[:, 6] = _j6_lock_l
                if not _nan_r.any():
                    ik_fc_r[:, 6] = _j6_lock_r
                tgt_l = robot_left.data.joint_pos.clone()
                tgt_l[env_idx, :7] = ik_fc_l[env_idx] if not _nan_l.any() else tgt_l[env_idx, :7]
                tgt_l[env_idx, 7] = GRIPPER_OPEN; tgt_l[env_idx, 8] = GRIPPER_OPEN
                robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
                tgt_r = robot_right.data.joint_pos.clone()
                tgt_r[env_idx, :7] = ik_fc_r[env_idx] if not _nan_r.any() else tgt_r[env_idx, :7]
                tgt_r[env_idx, 7] = GRIPPER_OPEN; tgt_r[env_idx, 8] = GRIPPER_OPEN
                robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
                sim.step(); scene.update(sim.get_physics_dt())
                if _p2995 % 5 == 0:
                    _collect_obs(2.995)
                if _p2995 % 30 == 0:
                    _gc2c_fc_l = torch.norm(_gc_fc_l[:2] - _cable_pos_fc[_nearest_l, :2]).item()
                    _gc2c_fc_r = torch.norm(_gc_fc_r[:2] - _cable_pos_fc[_nearest_r, :2]).item()
                    _ft_z_fc_l = _ee_fc_l[env_idx, 2].item() - FINGERTIP_OFFSET
                    _ft_z_fc_r = _ee_fc_r[env_idx, 2].item() - FINGERTIP_OFFSET
                    print(f"[GRASP] Phase 2.995 s={_p2995} gc2cable: L={_gc2c_fc_l*1000:.1f}mm R={_gc2c_fc_r*1000:.1f}mm "
                          f"ft_gap: L={(_ft_z_fc_l-_cable_z_fc)*1000:.1f}mm R={(_ft_z_fc_r-_cable_z_fc)*1000:.1f}mm")
                    if _gc2c_fc_l < 0.002 and _gc2c_fc_r < 0.002 and \
                       abs(_ft_z_fc_l - _cable_z_fc) < 0.002 and abs(_ft_z_fc_r - _cable_z_fc) < 0.002:
                        print(f"[GRASP] Phase 2.995: Converged at step {_p2995}")
                        break

    # --- Phase 3: Close ---
    _SIM_SUBSTEPS_CLOSE = 4
    grip_step = (GRIPPER_OPEN - GRIPPER_CLOSE) / close_steps
    grip_val = GRIPPER_OPEN

    # Measure current finger-to-cable Z gap
    _lf_l_now = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
    _rf_l_now = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
    _lf_r_now = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
    _rf_r_now = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
    _gc_z_l = ((_lf_l_now[2] + _rf_l_now[2]) / 2.0).item()
    _gc_z_r = ((_lf_r_now[2] + _rf_r_now[2]) / 2.0).item()
    _cable_z_now = cable.data.body_pos_w[env_idx, _nearest_l, 2].item()
    if env_origin is not None:
        _cable_z_now -= env_origin[2].item()
    _z_gap_l = _gc_z_l - _cable_z_now
    _z_gap_r = _gc_z_r - _cable_z_now
    if _hand_down:
        # fix25b: gc-closed-loop + minimal Z ramp + deferred finger close.
        # Phase 3 close: kinematic arm descent with gc tracking, fingers STAY OPEN.
        # Settle phase: PD arm hold + PD finger close → cable gripped.
        # This separates Z descent (N-independent) from finger closing (PD with compliance).
        _FINGER_REACH = 0.020  # 20mm: deep descent for robust finger-cable contact
        _z_ramp_per_arm = True
        _z_ramp_l = max(_z_gap_l - _FINGER_REACH + 0.005, 0.003)
        _z_ramp_r = max(_z_gap_r - _FINGER_REACH + 0.005, 0.003)
        _z_ramp_total = max(_z_ramp_l, _z_ramp_r)
        _gc_start_z_l = _gc_z_l
        _gc_start_z_r = _gc_z_r
        _TRACK_FRAC = 0.15
        _DEFER_FINGER_CLOSE = True  # keep fingers open during descent
        print(f"[GRASP] fix25b: gc-closed-loop + deferred finger close ({_TRACK_FRAC*100:.0f}%). "
              f"Z gap: L={_z_gap_l*1000:.1f}mm R={_z_gap_r*1000:.1f}mm "
              f"Finger reach: {_FINGER_REACH*1000:.0f}mm "
              f"Z ramp: L={_z_ramp_l*1000:.1f}mm R={_z_ramp_r*1000:.1f}mm")
    else:
        _z_ramp_total = max(_z_gap_l, _z_gap_r, 0.0) + 0.005  # ramp down by gap + 5mm extra
        _z_ramp_per_arm = False

    # EE start positions for Z ramp
    _ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    _ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    # Also capture arm joints for fallback (partial freeze: keep j0-5, allow j6 for Z)
    _arm_hold_left = robot_left.data.joint_pos[env_idx, :7].clone()
    _arm_hold_right = robot_right.data.joint_pos[env_idx, :7].clone()

    print(f"[GRASP] Phase 3: Close with Z-ramp ({GRIPPER_OPEN:.3f} -> {GRIPPER_CLOSE:.3f}) "
          f"over {close_steps} steps x{_SIM_SUBSTEPS_CLOSE} substeps")
    print(f"[GRASP] Phase 3: finger Z gap: L={_z_gap_l*1000:.1f}mm R={_z_gap_r*1000:.1f}mm "
          f"ramp_total={_z_ramp_total*1000:.1f}mm")

    # Phase 3 uses J^T IK to hold position during grip close
    _p3_aik = None

    for step in range(close_steps):
        if STOP_REQUESTED:
            break
        grip_val = max(grip_val - grip_step, GRIPPER_CLOSE)

        # Z-ramp schedule
        _ramp_frac = min(step / max(close_steps * 0.6, 1), 1.0)

        if _hand_down:
            # fix25: Closed-loop gc tracking.
            # Read current gc (finger center) and cable positions each step.
            # Compute correction to move gc toward cable XY + ramped Z target.
            # Apply correction to EE target, then fractional kinematic tracking.
            _lf_l_cur = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_l_cur = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
            _gc_now_l = (_lf_l_cur + _rf_l_cur) / 2.0  # (3,)
            _lf_r_cur = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_r_cur = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
            _gc_now_r = (_lf_r_cur + _rf_r_cur) / 2.0
            _cable_now_l = cable.data.body_pos_w[env_idx, _nearest_l, :3]
            _cable_now_r = cable.data.body_pos_w[env_idx, _nearest_r, :3]
            if env_origin is not None:
                _cable_now_l = _cable_now_l - env_origin
                _cable_now_r = _cable_now_r - env_origin
            # gc target: XY = cable, Z = ramped from start
            _gc_tgt_z_l = _gc_start_z_l - _z_ramp_l * _ramp_frac
            _gc_tgt_z_r = _gc_start_z_r - _z_ramp_r * _ramp_frac
            # gc correction: move EE by (target - current gc)
            _ee_corr_l = torch.zeros(3, device=device)
            _ee_corr_l[0] = _cable_now_l[0] - _gc_now_l[0]
            _ee_corr_l[1] = _cable_now_l[1] - _gc_now_l[1]
            _ee_corr_l[2] = _gc_tgt_z_l - _gc_now_l[2].item()
            _ee_corr_r = torch.zeros(3, device=device)
            _ee_corr_r[0] = _cable_now_r[0] - _gc_now_r[0]
            _ee_corr_r[1] = _cable_now_r[1] - _gc_now_r[1]
            _ee_corr_r[2] = _gc_tgt_z_r - _gc_now_r[2].item()
            # EE target = current EE + gc correction
            _ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
            _ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
            _ee_target_l = _ee_cur_l.clone()
            _ee_target_r = _ee_cur_r.clone()
            _ee_target_l[env_idx] += _ee_corr_l
            _ee_target_r[env_idx] += _ee_corr_r
            # J^T IK to gc-corrected target
            _p3_ori_ref_l = _ee_target_l.clone()
            _p3_ori_ref_l[:, 2] -= 0.1
            _p3_ori_ref_r = _ee_target_r.clone()
            _p3_ori_ref_r[:, 2] -= 0.1
            ik_l, _nan_l = jt_ik_step_6dof_batch(
                robot_left, jac_body_left, hand_body_left,
                _ee_target_l, _p3_ori_ref_l, no_ori,
                15.0, 0.0, 999.0, 0.01, device, cable_along_y=True)
            ik_r, _nan_r = jt_ik_step_6dof_batch(
                robot_right, jac_body_right, hand_body_right,
                _ee_target_r, _p3_ori_ref_r, no_ori,
                15.0, 0.0, 999.0, 0.01, device, cable_along_y=True)
            # Fractional tracking
            _q_cur_l = robot_left.data.joint_pos[env_idx, :7].clone()
            _q_cur_r = robot_right.data.joint_pos[env_idx, :7].clone()
            _q_arm_l = _q_cur_l.clone()
            _q_arm_r = _q_cur_r.clone()
            if not _nan_l.any():
                ik_l[:, 6] = _j6_lock_l
                _dq_l = ik_l[env_idx, :7] - _q_cur_l
                _q_arm_l = _q_cur_l + _TRACK_FRAC * _dq_l
            if not _nan_r.any():
                ik_r[:, 6] = _j6_lock_r
                _dq_r = ik_r[env_idx, :7] - _q_cur_r
                _q_arm_r = _q_cur_r + _TRACK_FRAC * _dq_r
            # Apply kinematically (N-independent)
            _pos_l = robot_left.data.joint_pos.clone()
            _pos_l[env_idx, :7] = _q_arm_l
            robot_left.write_joint_position_to_sim(_pos_l)
            _vel_l = robot_left.data.joint_vel.clone()
            _vel_l[env_idx, :7] = 0.0
            robot_left.write_joint_velocity_to_sim(_vel_l)
            _pos_r = robot_right.data.joint_pos.clone()
            _pos_r[env_idx, :7] = _q_arm_r
            robot_right.write_joint_position_to_sim(_pos_r)
            _vel_r = robot_right.data.joint_vel.clone()
            _vel_r[env_idx, :7] = 0.0
            robot_right.write_joint_velocity_to_sim(_vel_r)
            # PD targets: arm at IK position, fingers open (defer close to settle)
            _finger_cmd = GRIPPER_OPEN if _DEFER_FINGER_CLOSE else grip_val
            tgt_l = robot_left.data.joint_pos.clone()
            tgt_l[env_idx, :7] = _q_arm_l
            tgt_l[env_idx, 7] = _finger_cmd
            tgt_l[env_idx, 8] = _finger_cmd
            robot_left.set_joint_position_target(tgt_l)
            robot_left.write_data_to_sim()
            tgt_r = robot_right.data.joint_pos.clone()
            tgt_r[env_idx, :7] = _q_arm_r
            tgt_r[env_idx, 7] = _finger_cmd
            tgt_r[env_idx, 8] = _finger_cmd
            robot_right.set_joint_position_target(tgt_r)
            robot_right.write_data_to_sim()
            for _ss in range(_SIM_SUBSTEPS_CLOSE):
                sim.step()
                scene.update(sim.get_physics_dt())
                # Re-apply arm position + zero velocity per substep
                _pos_l = robot_left.data.joint_pos.clone()
                _pos_l[env_idx, :7] = _q_arm_l
                robot_left.write_joint_position_to_sim(_pos_l)
                _vel_l = robot_left.data.joint_vel.clone()
                _vel_l[env_idx, :7] = 0.0
                robot_left.write_joint_velocity_to_sim(_vel_l)
                _pos_r = robot_right.data.joint_pos.clone()
                _pos_r[env_idx, :7] = _q_arm_r
                robot_right.write_joint_position_to_sim(_pos_r)
                _vel_r = robot_right.data.joint_vel.clone()
                _vel_r[env_idx, :7] = 0.0
                robot_right.write_joint_velocity_to_sim(_vel_r)
            if on_step is not None and step % 5 == 0:
                on_step()
            if step % 5 == 0:
                _collect_obs(3.0)
            # NaN check
            if torch.isnan(robot_left.data.joint_pos).any() or torch.isnan(robot_right.data.joint_pos).any():
                print(f"[GRASP] NaN detected at close step {step}!")
                results["nan_detected"] = True
                return results
            if torch.isnan(cable.data.body_pos_w).any():
                print(f"[GRASP] Cable NaN detected at close step {step}!")
                results["nan_detected"] = True
                return results
            if step % 10 == 0:
                _actual_l7 = robot_left.data.joint_pos[env_idx, 7].item()
                _actual_r7 = robot_right.data.joint_pos[env_idx, 7].item()
                _lf_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
                _rf_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
                _lf_r = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
                _rf_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
                _finger_gap_l = torch.norm(_lf_l - _rf_l).item()
                _finger_gap_r = torch.norm(_lf_r - _rf_r).item()
                _gc_l = (_lf_l + _rf_l) / 2.0
                _gc_r = (_lf_r + _rf_r) / 2.0
                _cable_now_l = cable.data.body_pos_w[env_idx, _nearest_l, :3]
                _cable_now_r = cable.data.body_pos_w[env_idx, _nearest_r, :3]
                if env_origin is not None:
                    _cable_now_l = _cable_now_l - env_origin
                    _cable_now_r = _cable_now_r - env_origin
                _gc2c_l = torch.norm(_cable_now_l[:2] - _gc_l[:2]).item()
                _gc2c_r = torch.norm(_cable_now_r[:2] - _gc_r[:2]).item()
                _force_l = 8000 * max(_actual_l7 - grip_val, 0)
                _force_r = 8000 * max(_actual_r7 - grip_val, 0)
                # --- SOMA A2: Read actual applied_torque from sim ---
                _at_l7 = robot_left.data.applied_torque[env_idx, 7].item()
                _at_l8 = robot_left.data.applied_torque[env_idx, 8].item()
                _at_r7 = robot_right.data.applied_torque[env_idx, 7].item()
                _at_r8 = robot_right.data.applied_torque[env_idx, 8].item()
                _ct_l7 = robot_left.data.computed_torque[env_idx, 7].item()
                _ct_l8 = robot_left.data.computed_torque[env_idx, 8].item()
                _ct_r7 = robot_right.data.computed_torque[env_idx, 7].item()
                _ct_r8 = robot_right.data.computed_torque[env_idx, 8].item()
                _fo_c_l = _rf_l - _lf_l
                _fo_c_r = _rf_r - _lf_r
                _fox_c_l = (_fo_c_l[0] / (torch.norm(_fo_c_l) + 1e-8)).item()
                _fox_c_r = (_fo_c_r[0] / (torch.norm(_fo_c_r) + 1e-8)).item()
                print(f"[GRASP] close step={step}/{close_steps} "
                      f"cmd={grip_val:.4f} actual_L={_actual_l7:.4f} actual_R={_actual_r7:.4f} "
                      f"F_L={_force_l:.1f}N F_R={_force_r:.1f}N "
                      f"gap_L={_finger_gap_l*1000:.1f}mm gap_R={_finger_gap_r*1000:.1f}mm "
                      f"gc2cable_L={_gc2c_l*1000:.1f}mm gc2cable_R={_gc2c_r*1000:.1f}mm "
                      f"gc_z_L={_gc_l[2].item():.4f} gc_z_R={_gc_r[2].item():.4f} "
                      f"fo_X: L={_fox_c_l:.3f} R={_fox_c_r:.3f} "
                      f"ramp={_ramp_frac:.2f}")
                print(f"[EFFORT] step={step} "
                      f"applied_L=({_at_l7:.2f},{_at_l8:.2f}) applied_R=({_at_r7:.2f},{_at_r8:.2f}) "
                      f"computed_L=({_ct_l7:.2f},{_ct_l8:.2f}) computed_R=({_ct_r7:.2f},{_ct_r8:.2f})")
                # --- SOMA A4: 24D obs ---
                if obs_builder is not None and step in (0, 30, 60, 90):
                    _obs = obs_builder.build(
                        robot_left, robot_right, cable,
                        hand_body_left, hand_body_right,
                        env_origins=all_env_origins,
                        sim_steps_elapsed=30 if step > 0 else 1,
                    )
                    print(f"[OBS24] step={step} shape={_obs.shape} " + obs_builder.format_obs(_obs, env_idx))
                    if torch.isnan(_obs).any() or torch.isinf(_obs).any():
                        print(f"[OBS24] WARNING: NaN/Inf detected at step {step}!")
            continue  # skip normal joint application + NaN check below
        else:
            # Non-hand-down: use fixed EE start + Z ramp
            _z_lower = _z_ramp_total * _ramp_frac
            _ee_target_l = _ee_start_l.clone()
            _ee_target_r = _ee_start_r.clone()
            if _z_ramp_per_arm:
                _ee_target_l[:, 2] -= _z_ramp_l * _ramp_frac
                _ee_target_r[:, 2] -= _z_ramp_r * _ramp_frac
            else:
                _ee_target_l[:, 2] -= _z_lower
                _ee_target_r[:, 2] -= _z_lower
            # Orientation control during close: maintain hand-down when applicable
            _p3_ori_ref_l = _ee_target_l.clone()
            _p3_ori_ref_l[:, 2] -= 0.1
            _p3_ori_ref_r = _ee_target_r.clone()
            _p3_ori_ref_r[:, 2] -= 0.1
            ik_l, _nan_l = jt_ik_step_6dof_batch(
                robot_left, jac_body_left, hand_body_left,
                _ee_target_l, _p3_ori_ref_l, no_ori,
                _IK_ALPHA, 0.0, 999.0, _IK_CLIP, device,
                cable_along_y=False)
            ik_r, _nan_r = jt_ik_step_6dof_batch(
                robot_right, jac_body_right, hand_body_right,
                _ee_target_r, _p3_ori_ref_r, no_ori,
                _IK_ALPHA, 0.0, 999.0, _IK_CLIP, device,
                cable_along_y=False)
            _arm_l = ik_l[env_idx] if not _nan_l.any() else _arm_hold_left
            _arm_r = ik_r[env_idx] if not _nan_r.any() else _arm_hold_right

        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = _arm_l
        tgt_l[env_idx, 7] = grip_val
        tgt_l[env_idx, 8] = grip_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = _arm_r
        tgt_r[env_idx, 7] = grip_val
        tgt_r[env_idx, 8] = grip_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        for _ in range(_SIM_SUBSTEPS_CLOSE):
            sim.step()
            scene.update(sim.get_physics_dt())
        if on_step is not None and step % 5 == 0:
            on_step()
        if step % 5 == 0:
            _collect_obs(3.0)

        # NaN check
        if torch.isnan(robot_left.data.joint_pos).any() or torch.isnan(robot_right.data.joint_pos).any():
            print(f"[GRASP] NaN detected at close step {step}!")
            results["nan_detected"] = True
            return results
        if torch.isnan(cable.data.body_pos_w).any():
            print(f"[GRASP] Cable NaN detected at close step {step}!")
            results["nan_detected"] = True
            return results

        if step % 20 == 0:
            _actual_l7 = robot_left.data.joint_pos[env_idx, 7].item()
            _actual_r7 = robot_right.data.joint_pos[env_idx, 7].item()
            _lf_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
            _lf_r = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
            _finger_gap_l = torch.norm(_lf_l - _rf_l).item()
            _finger_gap_r = torch.norm(_lf_r - _rf_r).item()
            _gc_l = (_lf_l + _rf_l) / 2.0
            _gc_r = (_lf_r + _rf_r) / 2.0
            _cable_now_l = cable.data.body_pos_w[env_idx, _nearest_l, :3]
            _cable_now_r = cable.data.body_pos_w[env_idx, _nearest_r, :3]
            if env_origin is not None:
                _cable_now_l = _cable_now_l - env_origin
                _cable_now_r = _cable_now_r - env_origin
            _gc2c_l = torch.norm(_cable_now_l[:2] - _gc_l[:2]).item()
            _gc2c_r = torch.norm(_cable_now_r[:2] - _gc_r[:2]).item()
            _force_l = 8000 * max(_actual_l7 - grip_val, 0)
            _force_r = 8000 * max(_actual_r7 - grip_val, 0)
            # --- SOMA A2: Read actual applied_torque from sim ---
            _at_l7 = robot_left.data.applied_torque[env_idx, 7].item()
            _at_l8 = robot_left.data.applied_torque[env_idx, 8].item()
            _at_r7 = robot_right.data.applied_torque[env_idx, 7].item()
            _at_r8 = robot_right.data.applied_torque[env_idx, 8].item()
            _ct_l7 = robot_left.data.computed_torque[env_idx, 7].item()
            _ct_l8 = robot_left.data.computed_torque[env_idx, 8].item()
            _ct_r7 = robot_right.data.computed_torque[env_idx, 7].item()
            _ct_r8 = robot_right.data.computed_torque[env_idx, 8].item()
            _fo_c_l = _rf_l - _lf_l
            _fo_c_r = _rf_r - _lf_r
            _fox_c_l = (_fo_c_l[0] / (torch.norm(_fo_c_l) + 1e-8)).item()
            _fox_c_r = (_fo_c_r[0] / (torch.norm(_fo_c_r) + 1e-8)).item()
            print(f"[GRASP] close step={step}/{close_steps} "
                  f"cmd={grip_val:.4f} actual_L={_actual_l7:.4f} actual_R={_actual_r7:.4f} "
                  f"F_L={_force_l:.1f}N F_R={_force_r:.1f}N "
                  f"gap_L={_finger_gap_l*1000:.1f}mm gap_R={_finger_gap_r*1000:.1f}mm "
                  f"gc2cable_L={_gc2c_l*1000:.1f}mm gc2cable_R={_gc2c_r*1000:.1f}mm "
                  f"gc_z_L={_gc_l[2].item():.4f} gc_z_R={_gc_r[2].item():.4f} "
                  f"fo_X: L={_fox_c_l:.3f} R={_fox_c_r:.3f}")
            print(f"[EFFORT] step={step} "
                  f"applied_L=({_at_l7:.2f},{_at_l8:.2f}) applied_R=({_at_r7:.2f},{_at_r8:.2f}) "
                  f"computed_L=({_ct_l7:.2f},{_ct_l8:.2f}) computed_R=({_ct_r7:.2f},{_ct_r8:.2f})")
            # --- SOMA A4: 24D obs ---
            if obs_builder is not None and step in (0, 30, 60, 90):
                _obs = obs_builder.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right,
                    env_origins=all_env_origins,
                    sim_steps_elapsed=30 if step > 0 else 1,
                )
                print(f"[OBS24] step={step} shape={_obs.shape} " + obs_builder.format_obs(_obs, env_idx))
                if torch.isnan(_obs).any() or torch.isinf(_obs).any():
                    print(f"[OBS24] WARNING: NaN/Inf detected at step {step}!")

    results["gripper_closed"] = True
    results["close_steps_used"] = close_steps

    # --- Settle: kinematic contact detection (fix25i) ---
    # Close fingers kinematically in small steps while holding arm position.
    # Detect cable contact by monitoring cable segment displacement.
    # This works at any N because it's position-based, not PD-force-based.
    _arm_final_left = robot_left.data.joint_pos[env_idx, :7].clone()
    _arm_final_right = robot_right.data.joint_pos[env_idx, :7].clone()
    _FINGER_STEP = 0.0002  # 0.2mm per kinematic step
    _GRIP_TARGET = 0.004  # 4mm per finger (grip on 10mm cable)
    _SETTLE_STEPS = int(0.040 / _FINGER_STEP) + 20  # enough to close from 40mm to target
    _CONTACT_THRESHOLD = 0.0005  # 0.5mm cable displacement → contact (informational)
    _finger_pos = float(robot_left.data.joint_pos[env_idx, 7].item())
    _cable_ref_l = cable.data.body_pos_w[env_idx, _nearest_l, :3].clone()
    _cable_ref_r = cable.data.body_pos_w[env_idx, _nearest_r, :3].clone()
    if env_origin is not None:
        _cable_ref_l = _cable_ref_l - env_origin
        _cable_ref_r = _cable_ref_r - env_origin
    _contact_l = False
    _contact_r = False
    _contact_finger_l = GRIPPER_CLOSE
    _contact_finger_r = GRIPPER_CLOSE
    print(f"[GRASP] Settle: kinematic contact detection "
          f"(step={_FINGER_STEP*1000:.1f}mm, threshold={_CONTACT_THRESHOLD*1000:.1f}mm) "
          f"from {_finger_pos*1000:.1f}mm ({_SETTLE_STEPS} steps)")
    for _s in range(_SETTLE_STEPS):
        _finger_pos = max(_finger_pos - _FINGER_STEP, GRIPPER_CLOSE)
        # Kinematic write: arm + fingers
        _pos_l = robot_left.data.joint_pos.clone()
        _pos_l[env_idx, :7] = _arm_final_left
        _pos_l[env_idx, 7] = _finger_pos
        _pos_l[env_idx, 8] = _finger_pos
        robot_left.write_joint_position_to_sim(_pos_l)
        _vel_l = robot_left.data.joint_vel.clone()
        _vel_l[env_idx] = 0.0
        robot_left.write_joint_velocity_to_sim(_vel_l)
        _pos_r = robot_right.data.joint_pos.clone()
        _pos_r[env_idx, :7] = _arm_final_right
        _pos_r[env_idx, 7] = _finger_pos
        _pos_r[env_idx, 8] = _finger_pos
        robot_right.write_joint_position_to_sim(_pos_r)
        _vel_r = robot_right.data.joint_vel.clone()
        _vel_r[env_idx] = 0.0
        robot_right.write_joint_velocity_to_sim(_vel_r)
        # PD targets at kinematic positions (for write_data_to_sim)
        tgt_l = _pos_l.clone()
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = _pos_r.clone()
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        for _ in range(_SIM_SUBSTEPS_CLOSE):
            sim.step()
            scene.update(sim.get_physics_dt())
            # Re-apply arm + finger positions per substep
            _pos_l2 = robot_left.data.joint_pos.clone()
            _pos_l2[env_idx, :7] = _arm_final_left
            _pos_l2[env_idx, 7] = _finger_pos
            _pos_l2[env_idx, 8] = _finger_pos
            robot_left.write_joint_position_to_sim(_pos_l2)
            _vel_l2 = robot_left.data.joint_vel.clone()
            _vel_l2[env_idx] = 0.0
            robot_left.write_joint_velocity_to_sim(_vel_l2)
            _pos_r2 = robot_right.data.joint_pos.clone()
            _pos_r2[env_idx, :7] = _arm_final_right
            _pos_r2[env_idx, 7] = _finger_pos
            _pos_r2[env_idx, 8] = _finger_pos
            robot_right.write_joint_position_to_sim(_pos_r2)
            _vel_r2 = robot_right.data.joint_vel.clone()
            _vel_r2[env_idx] = 0.0
            robot_right.write_joint_velocity_to_sim(_vel_r2)
        if _s % 10 == 0:
            _collect_obs(3.5)
        # Check cable displacement for contact detection
        _cable_now_l = cable.data.body_pos_w[env_idx, _nearest_l, :3].clone()
        _cable_now_r = cable.data.body_pos_w[env_idx, _nearest_r, :3].clone()
        if env_origin is not None:
            _cable_now_l = _cable_now_l - env_origin
            _cable_now_r = _cable_now_r - env_origin
        _disp_l = torch.norm(_cable_now_l - _cable_ref_l).item()
        _disp_r = torch.norm(_cable_now_r - _cable_ref_r).item()
        if not _contact_l and _disp_l > _CONTACT_THRESHOLD:
            _contact_l = True
            _contact_finger_l = _finger_pos
            print(f"[GRASP] settle s={_s}: LEFT contact! finger={_finger_pos*1000:.1f}mm "
                  f"cable_disp={_disp_l*1000:.1f}mm")
        if not _contact_r and _disp_r > _CONTACT_THRESHOLD:
            _contact_r = True
            _contact_finger_r = _finger_pos
            print(f"[GRASP] settle s={_s}: RIGHT contact! finger={_finger_pos*1000:.1f}mm "
                  f"cable_disp={_disp_r*1000:.1f}mm")
        # --- ContactSensor force reading (fix25m) ---
        if contact_sensors:
            _cs_forces = {}    # net forces (all contacts)
            _cs_filtered = {}  # filtered forces (cable only via force_matrix_w)
            for _cs_name, _cs in contact_sensors.items():
                # net_forces_w = ALL contacts (not cable-specific)
                _f_net = _cs.data.net_forces_w[env_idx]  # (B, 3)
                _cs_forces[_cs_name] = torch.norm(_f_net, dim=-1).sum().item()
                # force_matrix_w = FILTERED (cable only) — (N, B, M, 3)
                _fm = _cs.data.force_matrix_w
                if _fm is not None:
                    _f_filt = _fm[env_idx]  # (B, M, 3)
                    _cs_filtered[_cs_name] = torch.norm(_f_filt, dim=-1).sum().item()
                else:
                    _cs_filtered[_cs_name] = -1.0  # unavailable
            _cs_cable_l = _cs_filtered.get("contact_left_lf", 0) + _cs_filtered.get("contact_left_rf", 0)
            _cs_cable_r = _cs_filtered.get("contact_right_lf", 0) + _cs_filtered.get("contact_right_rf", 0)
            # ContactSensor-based contact detection (cable-filtered forces)
            _CS_FORCE_THRESHOLD = 0.01  # 0.01N minimum
            if not _contact_l and _cs_cable_l > _CS_FORCE_THRESHOLD:
                _contact_l = True
                _contact_finger_l = _finger_pos
                print(f"[FIX25m] settle s={_s}: LEFT CONTACT (sensor)! "
                      f"cable_force={_cs_cable_l:.3f}N finger={_finger_pos*1000:.1f}mm")
            if not _contact_r and _cs_cable_r > _CS_FORCE_THRESHOLD:
                _contact_r = True
                _contact_finger_r = _finger_pos
                print(f"[FIX25m] settle s={_s}: RIGHT CONTACT (sensor)! "
                      f"cable_force={_cs_cable_r:.3f}N finger={_finger_pos*1000:.1f}mm")
            if _s % 30 == 0 or (_cs_cable_l > 0 or _cs_cable_r > 0):
                print(f"[FIX25m] settle s={_s} cable_forces: "
                      f"L_lf={_cs_filtered.get('contact_left_lf', 0):.3f}N "
                      f"L_rf={_cs_filtered.get('contact_left_rf', 0):.3f}N "
                      f"R_lf={_cs_filtered.get('contact_right_lf', 0):.3f}N "
                      f"R_rf={_cs_filtered.get('contact_right_rf', 0):.3f}N "
                      f"(net: L_lf={_cs_forces.get('contact_left_lf', 0):.1f} "
                      f"R_lf={_cs_forces.get('contact_right_lf', 0):.1f}) "
                      f"finger={_finger_pos*1000:.1f}mm")
        if _finger_pos <= _GRIP_TARGET:
            print(f"[GRASP] settle s={_s}: Reached grip target {_GRIP_TARGET*1000:.0f}mm. "
                  f"Contact: L={_contact_l} R={_contact_r}")
            break
        if _s % 30 == 0:
            _sl = robot_left.data.joint_pos[env_idx, 7].item()
            _sr = robot_right.data.joint_pos[env_idx, 7].item()
            _gc_s_l2 = (robot_left.data.body_pos_w[env_idx, _lf_idx, :3] +
                        robot_left.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
            _gc_s_r2 = (robot_right.data.body_pos_w[env_idx, _lf_idx, :3] +
                        robot_right.data.body_pos_w[env_idx, _rf_idx, :3]) / 2.0
            print(f"[GRASP] settle s={_s}/{_SETTLE_STEPS} finger={_finger_pos*1000:.1f}mm "
                  f"actual_L={_sl*1000:.1f}mm actual_R={_sr*1000:.1f}mm "
                  f"disp_L={_disp_l*1000:.1f}mm disp_R={_disp_r*1000:.1f}mm "
                  f"gc_z_L={_gc_s_l2[2].item():.4f} gc_z_R={_gc_s_r2[2].item():.4f}")
        if torch.isnan(cable.data.body_pos_w).any():
            print(f"[GRASP] Cable NaN during settle step {_s}!")
            results["nan_detected"] = True
            return results
        if _finger_pos <= GRIPPER_CLOSE:
            break  # fully closed without contact
    print(f"[GRASP] Settle done: contact L={_contact_l} R={_contact_r} "
          f"finger_pos={_finger_pos*1000:.1f}mm "
          f"contact_at L={_contact_finger_l*1000:.1f}mm R={_contact_finger_r*1000:.1f}mm")
    # Final ContactSensor force reading
    if contact_sensors:
        _cs_final_net = {}
        _cs_final_cable = {}
        for _cs_name, _cs in contact_sensors.items():
            _f_net = _cs.data.net_forces_w[env_idx]
            _cs_final_net[_cs_name] = torch.norm(_f_net, dim=-1).sum().item()
            _fm = _cs.data.force_matrix_w
            if _fm is not None:
                _f_filt = _fm[env_idx]
                _cs_final_cable[_cs_name] = torch.norm(_f_filt, dim=-1).sum().item()
            else:
                _cs_final_cable[_cs_name] = -1.0
        print(f"[FIX25m] Settle final CABLE forces (force_matrix_w): "
              f"L_lf={_cs_final_cable.get('contact_left_lf', 0):.3f}N "
              f"L_rf={_cs_final_cable.get('contact_left_rf', 0):.3f}N "
              f"R_lf={_cs_final_cable.get('contact_right_lf', 0):.3f}N "
              f"R_rf={_cs_final_cable.get('contact_right_rf', 0):.3f}N")
        print(f"[FIX25m] Settle final NET forces (all contacts): "
              f"L_lf={_cs_final_net.get('contact_left_lf', 0):.1f}N "
              f"L_rf={_cs_final_net.get('contact_left_rf', 0):.1f}N "
              f"R_lf={_cs_final_net.get('contact_right_lf', 0):.1f}N "
              f"R_rf={_cs_final_net.get('contact_right_rf', 0):.1f}N")
        results["contact_sensor_cable_forces"] = _cs_final_cable
        results["contact_sensor_net_forces"] = _cs_final_net

    _grip_l = float(robot_left.data.joint_pos[env_idx, 7].item())
    _grip_r = float(robot_right.data.joint_pos[env_idx, 7].item())
    _grip_l_both = float(robot_left.data.joint_pos[env_idx, 7].item() +
                         robot_left.data.joint_pos[env_idx, 8].item())
    _grip_r_both = float(robot_right.data.joint_pos[env_idx, 7].item() +
                         robot_right.data.joint_pos[env_idx, 8].item())
    print(f"[GRASP] Final grip: L_j7={_grip_l*1000:.1f}mm R_j7={_grip_r*1000:.1f}mm "
          f"L_total={_grip_l_both*1000:.1f}mm R_total={_grip_r_both*1000:.1f}mm")

    # --- Grip success check ---
    _CABLE_DIAMETER = 0.010  # 10mm
    _GRIP_MAX_FOR_SUCCESS = _CABLE_DIAMETER + 0.010  # 20mm total max
    results["grip_width_left"] = _grip_l
    results["grip_width_right"] = _grip_r
    results["grip_total_left"] = _grip_l_both
    results["grip_total_right"] = _grip_r_both
    grip_success_l = _grip_l > GRIP_SUCCESS_THRESHOLD and _grip_l_both < _GRIP_MAX_FOR_SUCCESS
    grip_success_r = _grip_r > GRIP_SUCCESS_THRESHOLD and _grip_r_both < _GRIP_MAX_FOR_SUCCESS
    results["grip_success_left"] = grip_success_l
    results["grip_success_right"] = grip_success_r

    if not grip_success_l or not grip_success_r:
        _fail_reasons = []
        if not grip_success_l:
            if _grip_l <= GRIP_SUCCESS_THRESHOLD:
                _fail_reasons.append(f"left_j7={_grip_l*1000:.1f}mm<{GRIP_SUCCESS_THRESHOLD*1000:.1f}mm(tunneled)")
            elif _grip_l_both >= _GRIP_MAX_FOR_SUCCESS:
                _fail_reasons.append(f"left_total={_grip_l_both*1000:.1f}mm>{_GRIP_MAX_FOR_SUCCESS*1000:.0f}mm(no contact)")
        if not grip_success_r:
            if _grip_r <= GRIP_SUCCESS_THRESHOLD:
                _fail_reasons.append(f"right_j7={_grip_r*1000:.1f}mm<{GRIP_SUCCESS_THRESHOLD*1000:.1f}mm(tunneled)")
            elif _grip_r_both >= _GRIP_MAX_FOR_SUCCESS:
                _fail_reasons.append(f"right_total={_grip_r_both*1000:.1f}mm>{_GRIP_MAX_FOR_SUCCESS*1000:.0f}mm(no contact)")
        results["grip_failed_reason"] = ", ".join(_fail_reasons)
        print(f"[GRASP] Grip FAILED: {results['grip_failed_reason']} — skipping lift")
        return results

    print(f"[GRASP] Grip SUCCESS: L_total={_grip_l_both*1000:.1f}mm R_total={_grip_r_both*1000:.1f}mm "
          f"(cable ~{_CABLE_DIAMETER*1000:.0f}mm, max={_GRIP_MAX_FOR_SUCCESS*1000:.0f}mm)")

    # --- PD stabilization: transition from kinematic to PD (fix25k) ---
    # After kinematic settle, PD internal state needs time to converge to grip position
    _stab_arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    _stab_arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    print(f"[GRASP] PD stabilization: 80 steps at finger_target={_finger_pos*1000:.1f}mm")
    for _stab_s in range(80):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = _stab_arm_l
        tgt_l[env_idx, 7] = _finger_pos
        tgt_l[env_idx, 8] = _finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = _stab_arm_r
        tgt_r[env_idx, 7] = _finger_pos
        tgt_r[env_idx, 8] = _finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        if _stab_s % 20 == 0:
            _g_l = robot_left.data.joint_pos[env_idx, 7].item()
            _g_r = robot_right.data.joint_pos[env_idx, 7].item()
            print(f"[GRASP] PD stab s={_stab_s} grip_L={_g_l*1000:.1f}mm grip_R={_g_r*1000:.1f}mm")
    _g_l_final = robot_left.data.joint_pos[env_idx, 7].item()
    _g_r_final = robot_right.data.joint_pos[env_idx, 7].item()
    print(f"[GRASP] PD stab done: grip_L={_g_l_final*1000:.1f}mm grip_R={_g_r_final*1000:.1f}mm")

    # --- Phase 4: Lift (PD arm + PD finger at settle position, fix25k) ---
    print(f"[GRASP] Phase 4: Lifting Z by +{lift_z}m")

    # PD for arms (gradual lift) + PD fingers at settle grip position
    # Fingers stay at _finger_pos (4mm) instead of GRIPPER_CLOSE (1mm) to avoid tunneling
    _lift_finger_pos = _finger_pos  # from settle (typically 4mm)
    ee_pos_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_pos_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_target_l = ee_pos_l.clone()
    ee_target_r = ee_pos_r.clone()
    ee_target_l[env_idx, 2] += lift_z
    ee_target_r[env_idx, 2] += lift_z

    # --- fix25n: Kinematic cable attachment during lift ---
    _kg_enabled = kinematic_grasp
    if _kg_enabled:
        _kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()  # (7,) pos + quat(wxyz)
        _kg_grip_z_0 = (ee_pos_l[env_idx, 2].item() + ee_pos_r[env_idx, 2].item()) / 2.0
        _kg_env_ids = torch.tensor([env_idx], dtype=torch.int32, device=device)
        print(f"[FIX25n] Kinematic grasp ENABLED: cable_root_z={_kg_root_pose_0[2].item():.4f}m "
              f"grip_z_0={_kg_grip_z_0:.4f}m")

    print(f"[GRASP] Lifting with PD IK + PD grip at {_lift_finger_pos*1000:.1f}mm"
          f"{' + kinematic cable' if _kg_enabled else ''}")
    _p4_lift_steps = PHASE_TIMEOUT.get("P4_lift", 200)
    for step in range(_p4_lift_steps):
        if STOP_REQUESTED:
            break

        ik_l, nan_l = jt_ik_step_6dof_batch(
            robot_left, jac_body_left, hand_body_left,
            ee_target_l, ee_target_l, no_ori,
            10.0, 5.0, 0.5, 0.02, device,
            fingers_vertical=True,
        )
        ik_r, nan_r = jt_ik_step_6dof_batch(
            robot_right, jac_body_right, hand_body_right,
            ee_target_r, ee_target_r, no_ori,
            10.0, 5.0, 0.5, 0.02, device,
            fingers_vertical=True,
        )

        if nan_l.any() or nan_r.any():
            print(f"[GRASP] IK NaN at lift step {step}")
            break

        # PD targets: arm (IK) + fingers at settle grip position
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = ik_l[env_idx]
        tgt_l[env_idx, 7] = _lift_finger_pos
        tgt_l[env_idx, 8] = _lift_finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = ik_r[env_idx]
        tgt_r[env_idx, 7] = _lift_finger_pos
        tgt_r[env_idx, 8] = _lift_finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        for _sub in range(4):
            sim.step()
            scene.update(sim.get_physics_dt())
            # fix25n: Override cable root position to follow gripper Z
            if _kg_enabled:
                _kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                             robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
                _kg_z_delta = _kg_cur_z - _kg_grip_z_0
                _kg_new_pose = _kg_root_pose_0.clone().unsqueeze(0)  # (1, 7)
                _kg_new_pose[0, 2] += _kg_z_delta
                cable.write_root_pose_to_sim(_kg_new_pose, env_ids=_kg_env_ids)
                cable.write_root_velocity_to_sim(
                    torch.zeros(1, 6, device=device), env_ids=_kg_env_ids)
        if on_step is not None and step % 5 == 0:
            on_step()
        if step % 5 == 0:
            _collect_obs(4.0)

        if torch.isnan(cable.data.body_pos_w).any():
            print(f"[GRASP] Cable NaN at lift IK step {step}!")
            results["nan_detected"] = True
            return results

        # Check convergence
        ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
        z_err_l = abs(ee_cur_l[env_idx, 2].item() - ee_target_l[env_idx, 2].item())
        z_err_r = abs(ee_cur_r[env_idx, 2].item() - ee_target_r[env_idx, 2].item())
        _grip_l_cur = robot_left.data.joint_pos[env_idx, 7].item()
        _grip_r_cur = robot_right.data.joint_pos[env_idx, 7].item()
        if step % 20 == 0:
            _kg_log = ""
            if _kg_enabled:
                _kg_cable_z = cable.data.root_pos_w[env_idx, 2].item()
                _kg_log = f" cable_root_z={_kg_cable_z:.4f} z_delta={_kg_cable_z - _kg_root_pose_0[2].item():.4f}"
            print(f"[GRASP] lift step={step} z_err_L={z_err_l:.4f} z_err_R={z_err_r:.4f} "
                  f"grip_L={_grip_l_cur*1000:.1f}mm grip_R={_grip_r_cur*1000:.1f}mm{_kg_log}")
        if z_err_l < 0.01 and z_err_r < 0.01:
            print(f"[GRASP] Lift converged at step {step}")
            break

    results["lift_steps_used"] = step + 1

    # --- Settle after lift (50 steps, PD hold at grip position) ---
    _arm_post_lift_l = robot_left.data.joint_pos[env_idx, :7].clone()
    _arm_post_lift_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(50):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = _arm_post_lift_l
        tgt_l[env_idx, 7] = _lift_finger_pos
        tgt_l[env_idx, 8] = _lift_finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = _arm_post_lift_r
        tgt_r[env_idx, 7] = _lift_finger_pos
        tgt_r[env_idx, 8] = _lift_finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        # fix25n: maintain kinematic cable attachment during settle
        if _kg_enabled:
            _kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                         robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
            _kg_z_delta = _kg_cur_z - _kg_grip_z_0
            _kg_new_pose = _kg_root_pose_0.clone().unsqueeze(0)
            _kg_new_pose[0, 2] += _kg_z_delta
            cable.write_root_pose_to_sim(_kg_new_pose, env_ids=_kg_env_ids)
            cable.write_root_velocity_to_sim(
                torch.zeros(1, 6, device=device), env_ids=_kg_env_ids)

    # Log final kinematic grasp state
    if _kg_enabled:
        _kg_final_z = cable.data.root_pos_w[env_idx, 2].item()
        _kg_final_delta = _kg_final_z - _kg_root_pose_0[2].item()
        print(f"[FIX25n] Kinematic grasp done: cable_root_z_delta={_kg_final_delta*1000:.1f}mm "
              f"(target lift={lift_z*1000:.0f}mm)")

    # --- Check cable Z after lift ---
    cable_z_after = cable.data.body_pos_w[env_idx, :, 2].clone()
    if env_origin is not None:
        cable_z_after = cable_z_after - env_origin[2]
    results["cable_z_after"] = cable_z_after.cpu().tolist()
    _czb = cable_z_before
    if env_origin is not None:
        _czb = cable_z_before - env_origin[2]
    z_delta = (cable_z_after - _czb).mean().item()
    results["cable_z_delta"] = z_delta
    _lift_thresh = PHASE_TRANSITION.get("P4_lift_success_mm", 10.0) / 1000.0
    results["cable_lifted"] = z_delta > _lift_thresh

    print(f"[GRASP] Cable Z after:  mean={cable_z_after.mean().item():.4f}m "
          f"min={cable_z_after.min().item():.4f}m max={cable_z_after.max().item():.4f}m")
    print(f"[GRASP] Cable Z delta:  mean={z_delta:.4f}m "
          f"({'LIFTED' if results['cable_lifted'] else 'NOT LIFTED'})")
    _seg_deltas = cable_z_after - _czb
    _top3 = torch.topk(_seg_deltas, min(3, len(_seg_deltas)))
    print(f"[GRASP] Top segment Z deltas: {[f'{d:.4f}m' for d in _top3.values.tolist()]}")
    _grip_l_post = robot_left.data.joint_pos[env_idx, 7].item()
    _grip_r_post = robot_right.data.joint_pos[env_idx, 7].item()
    _ee_z_l = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item()
    _ee_z_r = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()
    print(f"[GRASP] Post-lift: grip L={_grip_l_post*1000:.1f}mm R={_grip_r_post*1000:.1f}mm "
          f"EE_Z L={_ee_z_l:.4f}m R={_ee_z_r:.4f}m")

    return results


# ---------------------------------------------------------------------------
# Preposition (batched)
# ---------------------------------------------------------------------------

def dual_preposition_batch(
    robot_left, robot_right, sim, scene, device,
    hand_body_left: int, hand_body_right: int,
    jacobian_body_left: int, jacobian_body_right: int,
    left_start: torch.Tensor, right_start: torch.Tensor,
    num_envs: int,
    max_macros: int = 150,
    hold_steps: int = 20,
    jt_alpha: float = 20.0,
    clip_rad: float = 0.05,
    converge_m: float = 0.03,
) -> dict:
    """Batched preposition: bent-elbow teleport then JT IK to start positions.

    left_start, right_start: (N, 3) world-frame EE targets.
    """
    N = num_envs

    # Phase 1: Write bent-elbow joints to all envs
    bent = torch.tensor(BENT_JOINTS, dtype=torch.float32, device=device)

    n_joints_l = robot_left.data.joint_pos.shape[1]
    n_joints_r = robot_right.data.joint_pos.shape[1]

    bent_state_l = torch.zeros(N, n_joints_l, dtype=torch.float32, device=device)
    bent_state_l[:, :7] = bent.unsqueeze(0).expand(N, -1)
    if n_joints_l >= 9:
        bent_state_l[:, 7] = GRIPPER_OPEN
        bent_state_l[:, 8] = GRIPPER_OPEN

    bent_state_r = torch.zeros(N, n_joints_r, dtype=torch.float32, device=device)
    bent_state_r[:, :7] = bent.unsqueeze(0).expand(N, -1)
    if n_joints_r >= 9:
        bent_state_r[:, 7] = GRIPPER_OPEN
        bent_state_r[:, 8] = GRIPPER_OPEN

    print(f"[VEC][PREPOS] Phase 1: Writing bent-elbow joints to {N} envs")

    robot_left.write_joint_state_to_sim(
        position=bent_state_l,
        velocity=torch.zeros_like(bent_state_l),
    )
    robot_left.set_joint_position_target(bent_state_l)
    robot_left.write_data_to_sim()

    robot_right.write_joint_state_to_sim(
        position=bent_state_r,
        velocity=torch.zeros_like(bent_state_r),
    )
    robot_right.set_joint_position_target(bent_state_r)
    robot_right.write_data_to_sim()

    # Phase 2: Settle physics
    print(f"[VEC][PREPOS] Phase 2: Settling physics (100 steps)")
    for _ in range(100):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 3: JT IK to start positions
    print(f"[VEC][PREPOS] Phase 3: JT IK to start positions ({max_macros} max macros)")

    left_converged = torch.zeros(N, dtype=torch.bool, device=device)
    right_converged = torch.zeros(N, dtype=torch.bool, device=device)
    all_mask = torch.ones(N, dtype=torch.bool, device=device)

    for macro in range(max_macros):
        ee_left = robot_left.data.body_pos_w[:, hand_body_left, :3]  # (N, 3)
        ee_right = robot_right.data.body_pos_w[:, hand_body_right, :3]  # (N, 3)
        err_left = torch.norm(left_start - ee_left, dim=-1)  # (N,)
        err_right = torch.norm(right_start - ee_right, dim=-1)  # (N,)

        left_converged = err_left < converge_m
        right_converged = err_right < converge_m

        if macro % 30 == 0 or (left_converged.all() and right_converged.all()):
            print(
                f"[VEC][PREPOS] macro={macro} "
                f"L_err_mean={err_left.mean().item():.4f}m "
                f"R_err_mean={err_right.mean().item():.4f}m "
                f"L_conv={left_converged.sum().item()}/{N} "
                f"R_conv={right_converged.sum().item()}/{N}"
            )

        if left_converged.all() and right_converged.all():
            print(f"[VEC][PREPOS] All envs converged at macro={macro}")
            break

        for _ in range(hold_steps):
            # Left arm IK
            need_left = ~left_converged
            if need_left.any():
                jac_l = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left, :, :7]
                ee_pos_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
                error_l = left_start - ee_pos_l
                J_l = jac_l[:, :3, :]
                dq_l = jt_alpha * torch.bmm(J_l.transpose(1, 2), error_l.unsqueeze(2)).squeeze(2)
                dq_l = dq_l.clamp(-clip_rad, clip_rad)
                # Zero out converged envs
                dq_l[left_converged] = 0.0
                jp_l = robot_left.data.joint_pos[:, :7]
                new_joints_l = jp_l + dq_l

                tgt_l = robot_left.data.joint_pos.clone()
                tgt_l[:, :7] = torch.where(need_left.unsqueeze(-1).expand_as(new_joints_l),
                                            new_joints_l, tgt_l[:, :7])
                robot_left.set_joint_position_target(tgt_l)
                robot_left.write_data_to_sim()

            # Right arm IK
            need_right = ~right_converged
            if need_right.any():
                jac_r = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right, :, :7]
                ee_pos_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
                error_r = right_start - ee_pos_r
                J_r = jac_r[:, :3, :]
                dq_r = jt_alpha * torch.bmm(J_r.transpose(1, 2), error_r.unsqueeze(2)).squeeze(2)
                dq_r = dq_r.clamp(-clip_rad, clip_rad)
                dq_r[right_converged] = 0.0
                jp_r = robot_right.data.joint_pos[:, :7]
                new_joints_r = jp_r + dq_r

                tgt_r = robot_right.data.joint_pos.clone()
                tgt_r[:, :7] = torch.where(need_right.unsqueeze(-1).expand_as(new_joints_r),
                                            new_joints_r, tgt_r[:, :7])
                robot_right.set_joint_position_target(tgt_r)
                robot_right.write_data_to_sim()

            sim.step()
            scene.update(sim.get_physics_dt())

    return {
        "method": "hybrid_bent_elbow_then_jt_ik_batch",
        "macros_used": macro + 1,
        "left_converged_count": int(left_converged.sum().item()),
        "right_converged_count": int(right_converged.sum().item()),
    }


# ---------------------------------------------------------------------------
# Overhead descent (for --approach overhead)
# ---------------------------------------------------------------------------

def overhead_descent_batch(
    robot_left, robot_right, sim, scene, device,
    hand_body_left: int, hand_body_right: int,
    jacobian_body_left: int, jacobian_body_right: int,
    env_state: "EnvState",
    num_envs: int,
    standoff_y: float = 0.15,
    start_z: float = 0.90,
    z_delta_clip: float = 0.02,
    xy_converge_m: float = 0.05,
    z_converge_m: float = 0.02,
    max_macros: int = 200,
    hold_steps: int = 96,
    jt_alpha: float = 10.0,
    clip_rad: float = 0.02,
    table_z_min: float = 0.755,
    cable=None,
    cable_push_threshold: float = 0.002,
    soft_landing_zone: float = 0.02,
    soft_landing_clip: float = 0.005,
    left_ft_override: Optional[torch.Tensor] = None,
    right_ft_override: Optional[torch.Tensor] = None,
    on_step=None,
) -> dict:
    """Overhead descent: position fingertips above target, then descend Z.

    Phase 1: Move both fingertips to overhead positions at start_z
    Phase 2: Descend Z toward ball_z with Z-axis compliance

    If left_ft_override / right_ft_override are provided (cable grasping),
    use them as per-arm XY targets instead of ball ± standoff.
    Orientation control is enabled when overrides are provided.
    """
    N = num_envs
    ball = env_state.ball_pos  # (N, 3)
    grasp_offset = BALL_RADIUS + APPROACH_MARGIN  # 0.04

    # Target positions above ball at start_z
    if left_ft_override is not None and right_ft_override is not None:
        # Cable grasping: each arm goes directly above its cable segment
        overhead_left = left_ft_override.unsqueeze(0).expand(N, 3).clone()
        overhead_left[:, 2] = start_z
        overhead_right = right_ft_override.unsqueeze(0).expand(N, 3).clone()
        overhead_right[:, 2] = start_z
        _cable_grasp_mode = True
        print(f"[OVERHEAD] Cable grasp mode: L=({left_ft_override[0]:.4f},{left_ft_override[1]:.4f}) "
              f"R=({right_ft_override[0]:.4f},{right_ft_override[1]:.4f})")
    else:
        # Ball grasping: offset from ball center
        overhead_left = ball.clone()
        overhead_left[:, 1] -= (grasp_offset + standoff_y)
        overhead_left[:, 2] = start_z
        overhead_right = ball.clone()
        overhead_right[:, 1] += (grasp_offset + standoff_y)
        overhead_right[:, 2] = start_z
        _cable_grasp_mode = False

    # Descent target Z = ball_z (clamped to table_z_min)
    descent_z = ball[:, 2].clone().clamp(min=table_z_min)

    # Phases: 0=XY position, 10=orientation convergence, 1=Z descent, 2=done
    phase = torch.zeros(N, dtype=torch.int32, device=device)
    # Orientation control strategy (v11):
    #   Phase 0 (XY approach): moderate gain 0.7 throughout
    #   Phase 10 (NEW, cable only): dedicated orientation convergence at Z=start_z
    #     - high ori gain 5.0, clip 0.05 → converge hand Z-axis to [0,0,-1]
    #   Phase 1 (Z descent): moderate gain 1.5 to maintain converged orientation
    # Previous attempts without Phase 10:
    #   v4-v9: orientation gain 0.7 achieved finger-open X=0.985 but hand_Z stayed horizontal
    #   Root cause: J^T 14:1 position/orientation ratio can't converge pitch at workspace boundary
    _cable_ori_alpha = 0.0
    _cable_ori_dist = 999.0
    _ori_conv_start_macro = 0
    if _cable_grasp_mode:
        _cable_ori_alpha = 0.2  # Phase 0: low gain (FT→EE stability, 2% of pos gain)
        _cable_ori_dist = 999.0
        ori_enable = torch.ones(N, dtype=torch.bool, device=device)  # ON from start
        print(f"[OVERHEAD] Phase 0: low ori_gain={_cable_ori_alpha}, Phase 10 handles orientation")
        print(f"[OVERHEAD] Phase 1.5 orientation convergence enabled (gain=5.0)")
    else:
        ori_enable = torch.zeros(N, dtype=torch.bool, device=device)

    stats = {"macros_used": 0, "phase1_macros": 0, "phase2_macros": 0}
    phase1_done = False

    # --- Z-axis compliance: cable push monitoring ---
    _cable_ref_z = None  # reference cable Z positions (recorded at Phase 2 start)
    _cable_push_stopped = False
    _cable_push_stop_z = None  # Z where we stopped due to cable push
    _compliance_log = []

    print(f"[OVERHEAD] Starting overhead descent for {N} envs")
    print(f"[OVERHEAD] ball_z={ball[0, 2].item():.4f} start_z={start_z} "
          f"descent_z={descent_z[0].item():.4f} table_z_min={table_z_min}")
    if cable is not None:
        print(f"[OVERHEAD] Z-compliance: push_threshold={cable_push_threshold*1000:.1f}mm "
              f"soft_landing_zone={soft_landing_zone*1000:.0f}mm "
              f"soft_landing_clip={soft_landing_clip*1000:.1f}mm/step")

    for macro in range(max_macros):
        if STOP_REQUESTED:
            break

        # Current positions
        ee_pos_left = robot_left.data.body_pos_w[:, hand_body_left, :3]
        ee_quat_left = robot_left.data.body_quat_w[:, hand_body_left, :]
        ee_pos_right = robot_right.data.body_pos_w[:, hand_body_right, :3]
        ee_quat_right = robot_right.data.body_quat_w[:, hand_body_right, :]
        ft_left = ee_to_fingertip_batch(ee_pos_left, ee_quat_left)
        ft_right = ee_to_fingertip_batch(ee_pos_right, ee_quat_right)

        if phase[0] == 0:
            # Phase 1: move XY to overhead positions (Z stays at start_z)
            ft_target_left = overhead_left.clone()
            ft_target_right = overhead_right.clone()

            # Check XY convergence
            xy_err_left = torch.norm(ft_left[:, :2] - overhead_left[:, :2], dim=-1)
            xy_err_right = torch.norm(ft_right[:, :2] - overhead_right[:, :2], dim=-1)
            z_err_left = torch.abs(ft_left[:, 2] - start_z)
            z_err_right = torch.abs(ft_right[:, 2] - start_z)
            total_err_left = torch.norm(ft_left - overhead_left, dim=-1)
            total_err_right = torch.norm(ft_right - overhead_right, dim=-1)

            converged = (total_err_left < xy_converge_m) & (total_err_right < xy_converge_m)

            if macro % 20 == 0:
                print(f"[OVERHEAD] Ph1 macro={macro} "
                      f"L_err={total_err_left[0].item():.4f} R_err={total_err_right[0].item():.4f} "
                      f"conv={converged.sum().item()}/{N}")

            if converged.all():
                stats["phase1_macros"] = macro + 1
                if _cable_grasp_mode:
                    # → Phase 1.5: dedicated orientation convergence before descent
                    phase[:] = 10
                    _ori_conv_start_macro = macro + 1
                    print(f"[OVERHEAD] Phase 1 done at macro={macro}, "
                          f"starting orientation convergence (Phase 1.5)")
                else:
                    # Non-cable: skip Phase 1.5, go directly to descent
                    phase[:] = 1
                    print(f"[OVERHEAD] Phase 1 done at macro={macro}, starting Z descent")
                    overhead_left[:, 2] = descent_z
                    overhead_right[:, 2] = descent_z
                    if cable is not None:
                        _cable_ref_z = cable.data.body_pos_w[0, :, 2].clone()
                        _cable_ref_mean = _cable_ref_z.mean().item()
                        print(f"[COMPLIANCE] Cable ref Z at descent start: "
                              f"mean={_cable_ref_mean:.4f}m")

        elif phase[0] == 10:
            # Phase 1.5: Orientation convergence at Z=start_z (cable grasp only)
            # Hold fingertip at overhead position while converging hand orientation
            # to point tool axis (hand Z) downward [0,0,-1].
            ft_target_left = overhead_left.clone()   # still at start_z
            ft_target_right = overhead_right.clone()

            # Measure current hand Z-axis (tool direction) in world frame
            _z_local = torch.tensor([[0.0, 0.0, 1.0]], device=device).expand(N, 3)
            _hand_z_l = quat_rotate_vec_batch(ee_quat_left, _z_local)
            _hand_z_r = quat_rotate_vec_batch(ee_quat_right, _z_local)
            _hz_z_l = _hand_z_l[0, 2].item()
            _hz_z_r = _hand_z_r[0, 2].item()

            # Also measure finger-open direction (hand X-axis)
            _x_local = torch.tensor([[1.0, 0.0, 0.0]], device=device).expand(N, 3)
            _hand_x_l = quat_rotate_vec_batch(ee_quat_left, _x_local)
            _hand_x_r = quat_rotate_vec_batch(ee_quat_right, _x_local)

            _ori_macros = macro - _ori_conv_start_macro
            if _ori_macros % 5 == 0:
                print(f"[ORI_CONV] macro={macro} ({_ori_macros} iters) "
                      f"hand_z_L=({_hand_z_l[0,0]:.3f},{_hand_z_l[0,1]:.3f},{_hz_z_l:.3f}) "
                      f"hand_z_R=({_hand_z_r[0,0]:.3f},{_hand_z_r[0,1]:.3f},{_hand_z_r[0,2].item():.3f})")
                print(f"[ORI_CONV]   finger_open_L=({_hand_x_l[0,0]:.3f},{_hand_x_l[0,1]:.3f},{_hand_x_l[0,2].item():.3f}) "
                      f"finger_open_R=({_hand_x_r[0,0]:.3f},{_hand_x_r[0,1]:.3f},{_hand_x_r[0,2].item():.3f})")

            # Convergence check: hand Z-axis Z-component < -0.7 (pointing mostly down)
            _ORI_CONV_THRESHOLD = -0.7
            if _hz_z_l < _ORI_CONV_THRESHOLD and _hz_z_r < _ORI_CONV_THRESHOLD:
                print(f"[ORI_CONV] Orientation converged at macro={macro} ({_ori_macros} iters)! "
                      f"hand_z_Z: L={_hz_z_l:.3f} R={_hz_z_r:.3f}")
                stats["ori_conv_macros"] = _ori_macros
                phase[:] = 1  # → Phase 2: Z descent
                # NOW set descent targets
                overhead_left[:, 2] = descent_z
                overhead_right[:, 2] = descent_z
                if cable is not None:
                    _cable_ref_z = cable.data.body_pos_w[0, :, 2].clone()
                    _cable_ref_mean = _cable_ref_z.mean().item()
                    print(f"[COMPLIANCE] Cable ref Z at descent start: "
                          f"mean={_cable_ref_mean:.4f}m")
            elif _ori_macros > 80:
                # Timeout — proceed with warning
                print(f"[ORI_CONV] WARNING: Orientation NOT converged after {_ori_macros} macros! "
                      f"hand_z_Z: L={_hz_z_l:.3f} R={_hz_z_r:.3f}")
                stats["ori_conv_macros"] = _ori_macros
                stats["ori_conv_timeout"] = True
                phase[:] = 1
                overhead_left[:, 2] = descent_z
                overhead_right[:, 2] = descent_z
                if cable is not None:
                    _cable_ref_z = cable.data.body_pos_w[0, :, 2].clone()
                    _cable_ref_mean = _cable_ref_z.mean().item()
                    print(f"[COMPLIANCE] Cable ref Z at descent start: "
                          f"mean={_cable_ref_mean:.4f}m")

        elif phase[0] == 1:
            # Phase 2: descend Z toward ball_z with Z-axis compliance
            ft_target_left = overhead_left.clone()  # already has descent_z
            ft_target_right = overhead_right.clone()

            # --- Z-axis compliance: cable push detection ---
            _effective_z_clip = z_delta_clip
            if cable is not None and _cable_ref_z is not None and not _cable_push_stopped:
                _cable_cur_z = cable.data.body_pos_w[0, :, 2]
                _cable_z_drop = (_cable_ref_z - _cable_cur_z)  # positive = pushed down
                _max_drop = _cable_z_drop.max().item()
                _max_drop_seg = int(_cable_z_drop.argmax().item())
                _ft_z_mean = (ft_left[0, 2].item() + ft_right[0, 2].item()) / 2.0
                _cable_mean_z = _cable_cur_z.mean().item()
                _z_above_cable = _ft_z_mean - _cable_mean_z

                # Soft landing: reduce speed near cable
                if _z_above_cable < soft_landing_zone:
                    _effective_z_clip = soft_landing_clip
                    if macro % 10 == 0:
                        print(f"[COMPLIANCE] Soft landing: z_above_cable="
                              f"{_z_above_cable*1000:.1f}mm clip={_effective_z_clip*1000:.1f}mm/step")

                # Cable push detection
                if _max_drop > cable_push_threshold:
                    _cable_push_stopped = True
                    _cable_push_stop_z = _ft_z_mean
                    _compliance_log.append({
                        "macro": macro,
                        "event": "cable_push_stop",
                        "max_drop_mm": round(_max_drop * 1000, 2),
                        "max_drop_seg": _max_drop_seg,
                        "ft_z_mean": round(_ft_z_mean, 5),
                        "cable_mean_z": round(_cable_mean_z, 5),
                    })
                    print(f"[COMPLIANCE] *** Cable push detected at macro={macro}! "
                          f"seg[{_max_drop_seg}] dropped {_max_drop*1000:.1f}mm > "
                          f"{cable_push_threshold*1000:.1f}mm threshold")
                    print(f"[COMPLIANCE] Z descent STOPPED at ft_z={_ft_z_mean:.4f}m "
                          f"(cable_z={_cable_mean_z:.4f}m)")
                    # Lock descent targets to current Z (stop descending)
                    overhead_left[:, 2] = ft_left[:, 2].clone()
                    overhead_right[:, 2] = ft_right[:, 2].clone()
                    descent_z[:] = ft_left[:, 2].clone()  # Update for convergence check
                    # Mark as converged (done)
                    phase[:] = 2
                    stats["phase2_macros"] = macro + 1 - stats["phase1_macros"]
                    print(f"[OVERHEAD] Phase 2 done (compliance stop) at macro={macro}")
                    break

                if macro % 10 == 0 and _z_above_cable < soft_landing_zone:
                    print(f"[COMPLIANCE] macro={macro} cable_drop={_max_drop*1000:.1f}mm "
                          f"z_above={_z_above_cable*1000:.1f}mm")

            # Clamp Z delta to prevent overshooting (uses compliance-adjusted clip)
            z_delta_left = ft_target_left[:, 2] - ft_left[:, 2]
            z_delta_right = ft_target_right[:, 2] - ft_right[:, 2]
            z_delta_left = z_delta_left.clamp(-_effective_z_clip, _effective_z_clip)
            z_delta_right = z_delta_right.clamp(-_effective_z_clip, _effective_z_clip)
            # Modify target to only allow incremental Z change
            ft_target_left[:, 2] = ft_left[:, 2] + z_delta_left
            ft_target_right[:, 2] = ft_right[:, 2] + z_delta_right
            # Enforce Z floor
            ft_target_left[:, 2] = ft_target_left[:, 2].clamp(min=table_z_min)
            ft_target_right[:, 2] = ft_target_right[:, 2].clamp(min=table_z_min)

            z_err_left = torch.abs(ft_left[:, 2] - descent_z)
            z_err_right = torch.abs(ft_right[:, 2] - descent_z)
            converged = (z_err_left < z_converge_m) & (z_err_right < z_converge_m)

            if macro % 20 == 0:
                # Track hand Z-axis during descent
                _z_loc = torch.tensor([[0.0, 0.0, 1.0]], device=device).expand(N, 3)
                _hz_l_ph2 = quat_rotate_vec_batch(ee_quat_left, _z_loc)
                _hz_r_ph2 = quat_rotate_vec_batch(ee_quat_right, _z_loc)
                print(f"[OVERHEAD] Ph2 macro={macro} "
                      f"ft_z_L={ft_left[0, 2].item():.4f} ft_z_R={ft_right[0, 2].item():.4f} "
                      f"z_err_L={z_err_left[0].item():.4f} z_err_R={z_err_right[0].item():.4f} "
                      f"conv={converged.sum().item()}/{N} "
                      f"hz_z_L={_hz_l_ph2[0,2].item():.3f} hz_z_R={_hz_r_ph2[0,2].item():.3f}")

            if converged.all():
                phase[:] = 2
                _ph2_start = stats["phase1_macros"] + stats.get("ori_conv_macros", 0)
                stats["phase2_macros"] = macro + 1 - _ph2_start
                print(f"[OVERHEAD] Phase 2 done at macro={macro}, descent complete")
                # Log final hand orientation after descent
                _z_local_d = torch.tensor([[0.0, 0.0, 1.0]], device=device).expand(N, 3)
                _hz_l_d = quat_rotate_vec_batch(ee_quat_left, _z_local_d)
                _hz_r_d = quat_rotate_vec_batch(ee_quat_right, _z_local_d)
                print(f"[OVERHEAD] Final hand_z_L=({_hz_l_d[0,0]:.3f},{_hz_l_d[0,1]:.3f},{_hz_l_d[0,2].item():.3f}) "
                      f"hand_z_R=({_hz_r_d[0,0]:.3f},{_hz_r_d[0,1]:.3f},{_hz_r_d[0,2].item():.3f})")
                break

        else:
            break  # phase 2 done

        # Convert FT targets to EE targets
        ee_target_left = fingertip_to_ee_batch(ft_target_left, ee_quat_left)
        ee_target_right = fingertip_to_ee_batch(ft_target_right, ee_quat_right)

        # Dynamic IK gains based on phase
        # Phase 10 (ori convergence): high ori gain, larger clip for faster convergence
        # Phase 1 (descent): moderate ori gain to maintain converged orientation
        # Phase 0 (XY approach): default gains
        if phase[0] == 10 and _cable_grasp_mode:
            _ik_ori_gain = 5.0    # High: force orientation convergence
            _ik_clip = 0.05       # Larger clip for faster joint movement
        elif phase[0] == 1 and _cable_grasp_mode:
            _ik_ori_gain = 1.5    # Moderate: maintain orientation during descent
            _ik_clip = clip_rad   # Normal clip
        else:
            _ik_ori_gain = _cable_ori_alpha  # 0.7 or 0.0
            _ik_clip = clip_rad

        # IK inner loop
        for _ in range(hold_steps):
            if STOP_REQUESTED:
                break
            # Orientation ref: point directly below EE → clean downward direction
            _ee_l_cur = robot_left.data.body_pos_w[:, hand_body_left, :3]
            _ee_r_cur = robot_right.data.body_pos_w[:, hand_body_right, :3]
            _ori_ref_l = _ee_l_cur.clone()
            _ori_ref_l[:, 2] -= 0.1
            _ori_ref_r = _ee_r_cur.clone()
            _ori_ref_r[:, 2] -= 0.1

            # For Phase 10: recompute EE target from FT target using CURRENT quaternion
            # (hand is rotating, so FT→EE offset direction changes each step)
            if phase[0] == 10:
                _eq_l = robot_left.data.body_quat_w[:, hand_body_left, :]
                _eq_r = robot_right.data.body_quat_w[:, hand_body_right, :]
                ee_target_left = fingertip_to_ee_batch(ft_target_left, _eq_l)
                ee_target_right = fingertip_to_ee_batch(ft_target_right, _eq_r)

            ik_left, nan_left = jt_ik_step_6dof_batch(
                robot_left, jacobian_body_left, hand_body_left,
                ee_target_left, _ori_ref_l, ori_enable,
                jt_alpha, _ik_ori_gain, _cable_ori_dist,
                _ik_clip, device,
                cable_along_y=_cable_grasp_mode,
            )
            ik_right, nan_right = jt_ik_step_6dof_batch(
                robot_right, jacobian_body_right, hand_body_right,
                ee_target_right, _ori_ref_r, ori_enable,
                jt_alpha, _ik_ori_gain, _cable_ori_dist,
                _ik_clip, device,
                cable_along_y=_cable_grasp_mode,
            )
            apply_mask = torch.ones(N, dtype=torch.bool, device=device)
            apply_joints_batch(robot_left, ik_left, apply_mask & (~nan_left))
            apply_joints_batch(robot_right, ik_right, apply_mask & (~nan_right))
            sim.step()
            scene.update(sim.get_physics_dt())
        # Capture video frame once per macro step (after hold_steps inner iterations)
        if on_step is not None:
            on_step()

    stats["macros_used"] = macro + 1
    stats["final_phase"] = int(phase[0].item())
    stats["cable_push_stopped"] = _cable_push_stopped
    if _cable_push_stop_z is not None:
        stats["cable_push_stop_z"] = round(_cable_push_stop_z, 5)
    if _compliance_log:
        stats["compliance_log"] = _compliance_log

    # Report final fingertip positions
    ee_pos_left = robot_left.data.body_pos_w[:, hand_body_left, :3]
    ee_quat_left = robot_left.data.body_quat_w[:, hand_body_left, :]
    ee_pos_right = robot_right.data.body_pos_w[:, hand_body_right, :3]
    ee_quat_right = robot_right.data.body_quat_w[:, hand_body_right, :]
    ft_l = ee_to_fingertip_batch(ee_pos_left, ee_quat_left)
    ft_r = ee_to_fingertip_batch(ee_pos_right, ee_quat_right)
    print(f"[OVERHEAD] Final FT: L=({ft_l[0, 0].item():.4f}, {ft_l[0, 1].item():.4f}, {ft_l[0, 2].item():.4f}) "
          f"R=({ft_r[0, 0].item():.4f}, {ft_r[0, 1].item():.4f}, {ft_r[0, 2].item():.4f})")

    return stats


# ---------------------------------------------------------------------------
# Demo recording helpers
# ---------------------------------------------------------------------------

def record_demo_step(
    env_state: EnvState,
    robot_left, robot_right,
    hand_body_left: int, hand_body_right: int,
    active_mask: torch.Tensor,
    act_left_delta: torch.Tensor,  # (N, 3)
    act_right_delta: torch.Tensor,  # (N, 3)
):
    """Record one demo transition for each active (non-done) environment."""
    N = env_state.num_envs
    device = env_state.device

    l_jp = robot_left.data.joint_pos[:, :7].detach().cpu().numpy()  # (N, 7)
    l_jv = robot_left.data.joint_vel[:, :7].detach().cpu().numpy()
    l_ee = robot_left.data.body_pos_w[:, hand_body_left, :3].detach().cpu().numpy()  # (N, 3)
    l_eq = robot_left.data.body_quat_w[:, hand_body_left, :].detach().cpu().numpy()  # (N, 4)

    r_jp = robot_right.data.joint_pos[:, :7].detach().cpu().numpy()
    r_jv = robot_right.data.joint_vel[:, :7].detach().cpu().numpy()
    r_ee = robot_right.data.body_pos_w[:, hand_body_right, :3].detach().cpu().numpy()
    r_eq = robot_right.data.body_quat_w[:, hand_body_right, :].detach().cpu().numpy()

    # Fingertip positions (CPU numpy)
    l_ft_t = ee_to_fingertip_batch(
        robot_left.data.body_pos_w[:, hand_body_left, :3],
        robot_left.data.body_quat_w[:, hand_body_left, :],
    ).detach().cpu().numpy()
    r_ft_t = ee_to_fingertip_batch(
        robot_right.data.body_pos_w[:, hand_body_right, :3],
        robot_right.data.body_quat_w[:, hand_body_right, :],
    ).detach().cpu().numpy()

    ball_np = env_state.ball_pos.detach().cpu().numpy()  # (N, 3)
    l_delta_np = act_left_delta.detach().cpu().numpy()  # (N, 3)
    r_delta_np = act_right_delta.detach().cpu().numpy()

    active_np = active_mask.cpu().numpy()

    for i in range(N):
        if not active_np[i]:
            continue
        # Get or create current episode buffer for this env
        tidx = int(env_state.current_target_idx[i].item())
        # Ensure there is a buffer for this target
        while len(env_state.demo_buffers[i]) <= tidx:
            env_state.demo_buffers[i].append({
                "left_joint_pos": [], "left_joint_vel": [],
                "left_ee_pos": [], "left_ee_quat": [], "left_fingertip_pos": [],
                "right_joint_pos": [], "right_joint_vel": [],
                "right_ee_pos": [], "right_ee_quat": [], "right_fingertip_pos": [],
                "ball_pos": [],
                "left_action_delta": [], "right_action_delta": [],
                "left_distance": [], "right_distance": [],
                "left_reached": [], "right_reached": [],
                "phase": [], "macro_step": [],
            })
        buf = env_state.demo_buffers[i][tidx]

        l_dist = float(np.linalg.norm(ball_np[i] - l_ft_t[i]))
        r_dist = float(np.linalg.norm(ball_np[i] - r_ft_t[i]))

        buf["left_joint_pos"].append(l_jp[i].copy())
        buf["left_joint_vel"].append(l_jv[i].copy())
        buf["left_ee_pos"].append(l_ee[i].copy())
        buf["left_ee_quat"].append(l_eq[i].copy())
        buf["left_fingertip_pos"].append(l_ft_t[i].copy())
        buf["right_joint_pos"].append(r_jp[i].copy())
        buf["right_joint_vel"].append(r_jv[i].copy())
        buf["right_ee_pos"].append(r_ee[i].copy())
        buf["right_ee_quat"].append(r_eq[i].copy())
        buf["right_fingertip_pos"].append(r_ft_t[i].copy())
        buf["ball_pos"].append(ball_np[i].copy())
        buf["left_action_delta"].append(l_delta_np[i].copy().astype(np.float32))
        buf["right_action_delta"].append(r_delta_np[i].copy().astype(np.float32))
        buf["left_distance"].append(l_dist)
        buf["right_distance"].append(r_dist)
        buf["left_reached"].append(l_dist <= args.success_threshold_m)
        buf["right_reached"].append(r_dist <= args.success_threshold_m)
        buf["phase"].append(int(env_state.phase[i].item()))
        buf["macro_step"].append(int(env_state.macro_step[i].item()))


# ---------------------------------------------------------------------------
# HDF5 saving
# ---------------------------------------------------------------------------

def save_demos_hdf5(env_state: EnvState, output_dir: str, seed_start: int):
    """Save per-env demo HDF5 files compatible with existing dual-arm format."""
    import h5py

    demo_dir = os.path.join(output_dir, "hdf5")
    os.makedirs(demo_dir, exist_ok=True)

    ts = time.strftime("%Y%m%d_%H%M%S")
    for env_i in range(env_state.num_envs):
        episodes = env_state.demo_buffers[env_i]
        # Filter out empty episodes
        episodes = [ep for ep in episodes if len(ep.get("left_joint_pos", [])) > 0]
        if not episodes:
            continue

        seed = seed_start + env_i
        path = os.path.join(demo_dir, f"demo_dual_seed{seed}_{len(episodes)}t_{ts}.hdf5")
        total_steps = 0

        with h5py.File(path, "w") as hf:
            for ei, ep in enumerate(episodes):
                grp = hf.create_group(f"episode_{ei}")
                n = len(ep["left_joint_pos"])
                total_steps += n

                for key in [
                    "left_joint_pos", "left_joint_vel",
                    "left_ee_pos", "left_ee_quat", "left_fingertip_pos",
                    "right_joint_pos", "right_joint_vel",
                    "right_ee_pos", "right_ee_quat", "right_fingertip_pos",
                    "ball_pos", "left_action_delta", "right_action_delta",
                ]:
                    grp.create_dataset(key, data=np.stack(ep[key], axis=0).astype(np.float32))
                grp.create_dataset("left_distance", data=np.array(ep["left_distance"], dtype=np.float32))
                grp.create_dataset("right_distance", data=np.array(ep["right_distance"], dtype=np.float32))
                grp.create_dataset("left_reached", data=np.array(ep["left_reached"], dtype=np.bool_))
                grp.create_dataset("right_reached", data=np.array(ep["right_reached"], dtype=np.bool_))
                grp.create_dataset("phase", data=np.array(ep["phase"], dtype=np.int32))
                grp.create_dataset("macro_step", data=np.array(ep["macro_step"], dtype=np.int32))
                grp.attrs["num_steps"] = n
                # Check if both arms reached at least once in the episode
                both_reached = any(ep["left_reached"]) and any(ep["right_reached"])
                grp.attrs["both_reached"] = both_reached

            meta = hf.create_group("metadata")
            meta.attrs["seed"] = seed
            meta.attrs["num_episodes"] = len(episodes)
            meta.attrs["total_steps"] = total_steps
            meta.attrs["record_hz"] = "macro_5hz"
            meta.attrs["hz"] = 5.0
            meta.attrs["sim_dt"] = PHYSICS_DT
            meta.attrs["success_threshold_m"] = args.success_threshold_m
            meta.attrs["ik_mode"] = "jt_raw"
            meta.attrs["policy_backend"] = args.backend
            meta.attrs["backend"] = args.backend
            meta.attrs["base_left_y"] = DUAL_LEFT_BASE_Y
            meta.attrs["base_right_y"] = DUAL_RIGHT_BASE_Y
            meta.attrs["grasp_offset"] = BALL_RADIUS + APPROACH_MARGIN
            meta.attrs["fingertip_offset"] = FINGERTIP_OFFSET

        print(f"[VEC][HDF5] env={env_i} seed={seed} episodes={len(episodes)} steps={total_steps} -> {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    N = args.num_envs
    print(f"[VEC] Starting vectorized dual-arm reaching: num_envs={N} num_targets={args.num_targets}")
    print(f"[VEC] Seeds: {args.seed_start} to {args.seed_start + N - 1}")
    print(f"[VEC] Output: {args.output_dir}")

    # --- Scene setup ---
    scene_cfg = DualArmSceneCfg(num_envs=N, env_spacing=args.env_spacing)

    # Camera position overrides for dual workspace (matches reference)
    _need_cameras = args.save_video or _USE_CAMERA
    if _need_cameras:
        from isaaclab.sensors import CameraCfg as _CamCfg
        scene_cfg.overhead_camera.offset = _CamCfg.OffsetCfg(
            pos=(0.75, 0.0, 2.2), rot=(0.7071, 0.0, 0.7071, 0.0), convention="world",
        )
        scene_cfg.front_center_camera.offset = _CamCfg.OffsetCfg(
            pos=(2.0, 0.0, 1.1), rot=(0.0, 0.0, 0.0, 1.0), convention="world",
        )
        scene_cfg.front_left_camera.offset = _CamCfg.OffsetCfg(
            pos=(0.75, -1.2, 1.1), rot=(0.7071, 0.0, 0.0, 0.7071), convention="world",
        )
        scene_cfg.front_right_camera.offset = _CamCfg.OffsetCfg(
            pos=(0.75, 1.2, 1.1), rot=(0.7071, 0.0, 0.0, -0.7071), convention="world",
        )
        # Upgrade resolution to 512x512 for all 4 cameras
        for _cam_attr in ("overhead_camera", "front_center_camera",
                          "front_left_camera", "front_right_camera"):
            _cam_obj = getattr(scene_cfg, _cam_attr)
            _cam_obj.width = 512
            _cam_obj.height = 512
        print("[VEC] Camera positions overridden for dual workspace [4 cameras, 512px]")

    # --- Cable position override (before scene creation) ---
    if args.grasp and args.with_table and hasattr(scene_cfg, 'cable'):
        _cable_y_start = -0.285  # CABLE_SEG17_Y from task_config.py
        scene_cfg.cable.init_state.pos = (args.cable_x, _cable_y_start, 0.77)
        print(f"[GRASP] Cable position overridden: X={args.cable_x}, Y_start={_cable_y_start}, Z=0.77")

    # Support CPU device for diagnostic testing
    if hasattr(args, 'device') and args.device == "cpu":
        _sim_device = "cpu"
    else:
        _sim_device = f"cuda:{app_launcher.device_id}"
    if args.solver_default:
        _physx_cfg = sim_utils.PhysxCfg(
            gpu_found_lost_pairs_capacity=2**23,
            gpu_total_aggregate_pairs_capacity=2**23,
        )
        print("[SOLVER] Using TGS defaults (--solver_default)")
    else:
        _physx_cfg = sim_utils.PhysxCfg(
            # fix25l/m: PGS 32 iterations (TGS defaults cause cable NaN during close)
            solver_type=0,
            min_position_iteration_count=32,
            max_position_iteration_count=255,
            min_velocity_iteration_count=8,
            max_velocity_iteration_count=255,
            gpu_found_lost_pairs_capacity=2**23,
            gpu_total_aggregate_pairs_capacity=2**23,
        )
        print("[SOLVER] Using PGS 32 iterations")
    sim_cfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT, render_interval=2, device=_sim_device,
        physx=_physx_cfg,
    )
    # --- ContactSensor for finger-cable contact (fix25m) ---
    if args.contact_sensor and args.grasp:
        scene_cfg.contact_left_lf = ContactSensorCfg(
            prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
            update_period=0.0,
            filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"],
        )
        scene_cfg.contact_left_rf = ContactSensorCfg(
            prim_path="{ENV_REGEX_NS}/Robot_Left/panda_rightfinger",
            update_period=0.0,
            filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"],
        )
        scene_cfg.contact_right_lf = ContactSensorCfg(
            prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
            update_period=0.0,
            filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"],
        )
        scene_cfg.contact_right_rf = ContactSensorCfg(
            prim_path="{ENV_REGEX_NS}/Robot_Right/panda_rightfinger",
            update_period=0.0,
            filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"],
        )
        print("[FIX25m] ContactSensor added: 4 sensors (L_lf, L_rf, R_lf, R_rf) filtered vs Cable")

    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)

    # --- Finger-table collision filtering (before sim.reset) ---
    if args.finger_table_contact and args.with_table:
        setup_finger_table_collision_filtering(sim, scene, N)
        setup_finger_hand_collision_filtering(sim, scene, N)
        apply_finger_physics_material(sim, N)
        print(f"[FINGER_CONTACT] Z-floor relaxed: fingers={args.finger_z_min}m, "
              f"hand/links={args.table_z_min}m (table surface=0.75m)")

    # --- High-friction for cable/table (before sim.reset) ---
    if args.grasp and args.with_table:
        apply_cable_table_friction(sim, N)

    sim.reset()
    scene.reset()

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    device = robot_left.device
    print(f"[VEC] Device: {device}")
    print(f"[VEC] Robot joint shapes: L={robot_left.data.joint_pos.shape} R={robot_right.data.joint_pos.shape}")

    # --- Finger body indices (for contact force monitoring) ---
    _finger_body_indices = {}
    if args.finger_table_contact:
        for _arm_name, _robot in [("left", robot_left), ("right", robot_right)]:
            for _fb in _FRANKA_FINGER_BODIES:
                _idx = _robot.find_bodies(_fb)
                # find_bodies returns (indices_list, names_list)
                if len(_idx[0]) > 0:
                    _finger_body_indices[f"{_arm_name}_{_fb}"] = int(_idx[0][0])
        # Also get hand body index for non-finger Z clamping
        _hand_body_idx_left = int(robot_left.find_bodies("panda_hand")[0][0])
        _hand_body_idx_right = int(robot_right.find_bodies("panda_hand")[0][0])
        print(f"[FINGER_CONTACT] Finger body indices: {_finger_body_indices}")
        # Contact force tracking
        _max_finger_force = 0.0
        _total_finger_contacts = 0
        _non_finger_table_violations = 0

    # --- Cable reference (for grasp mode) ---
    _cable = None
    _grasp_results = []
    if args.grasp and args.with_table:
        try:
            _cable = scene["cable"]
            print(f"[GRASP] Cable loaded: body_names={_cable.body_names} "
                  f"n_bodies={_cable.data.body_pos_w.shape[1]}")
        except KeyError:
            print("[GRASP] WARNING: Cable not found in scene. Grasp mode disabled.")
            args.grasp = False

    # --- 24D ObsBuilder (SOMA A4) ---
    _obs_builder = None
    _obs_collector = None
    if args.grasp and _cable is not None:
        _hand_idx_l = int(robot_left.find_bodies("panda_hand")[0][0])
        _hand_idx_r = int(robot_right.find_bodies("panda_hand")[0][0])
        _obs_builder = ObsBuilder24D(num_envs=N, device=str(device))
        print(f"[OBS24] ObsBuilder24D created: N={N} dim={OBS_DIM} "
              f"hand_body L={_hand_idx_l} R={_hand_idx_r}")
        # B1: obs stats collector
        if args.collect_obs_stats:
            _obs_collector = ObsCollector(
                _obs_builder, scene.env_origins,
                _hand_idx_l, _hand_idx_r)
            print(f"[B1] ObsCollector created for obs stats collection")

    # --- ContactSensor retrieval (fix25m) ---
    _contact_sensors = {}
    if args.contact_sensor and args.grasp:
        for _cs_name in ["contact_left_lf", "contact_left_rf",
                         "contact_right_lf", "contact_right_rf"]:
            try:
                _contact_sensors[_cs_name] = scene[_cs_name]
                print(f"[FIX25m] ContactSensor '{_cs_name}' loaded: "
                      f"shape={scene[_cs_name].data.net_forces_w.shape}")
            except KeyError:
                print(f"[FIX25m] WARNING: ContactSensor '{_cs_name}' not found in scene")
        if _contact_sensors:
            print(f"[FIX25m] {len(_contact_sensors)} ContactSensors active")
        else:
            print("[FIX25m] WARNING: No ContactSensors loaded — falling back to displacement")
            args.contact_sensor = False

    # --- Fine-RL actor loading ---
    _fine_rl_actor = load_fine_rl_actor(args.fine_rl_checkpoint, device)
    _rl_refinement_count = 0  # track how many macro steps used RL

    # --- Relocate robot bases for dual-arm reaching ---
    left_pose = torch.zeros(N, 7, dtype=torch.float32, device=device)
    left_pose[:, 0] = BASE_X
    left_pose[:, 1] = DUAL_LEFT_BASE_Y
    left_pose[:, 2] = BASE_Z
    left_pose[:, 3] = BASE_QUAT[0]  # w
    left_pose[:, 4] = BASE_QUAT[1]  # x
    left_pose[:, 5] = BASE_QUAT[2]  # y
    left_pose[:, 6] = BASE_QUAT[3]  # z

    right_pose = torch.zeros(N, 7, dtype=torch.float32, device=device)
    right_pose[:, 0] = BASE_X
    right_pose[:, 1] = DUAL_RIGHT_BASE_Y
    right_pose[:, 2] = BASE_Z
    right_pose[:, 3] = BASE_QUAT[0]
    right_pose[:, 4] = BASE_QUAT[1]
    right_pose[:, 5] = BASE_QUAT[2]
    right_pose[:, 6] = BASE_QUAT[3]

    robot_left.write_root_pose_to_sim(left_pose)
    robot_right.write_root_pose_to_sim(right_pose)

    # Settle physics
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

    print(f"[VEC] Base positions settled (50 steps)")

    # --- IK body indices ---
    hand_body_left = int(robot_left.find_bodies("panda_hand")[0][0])
    hand_body_right = int(robot_right.find_bodies("panda_hand")[0][0])
    is_fixed_left = bool(getattr(robot_left, "is_fixed_base", False))
    is_fixed_right = bool(getattr(robot_right, "is_fixed_base", False))
    jacobian_body_left = hand_body_left - 1 if is_fixed_left else hand_body_left
    jacobian_body_right = hand_body_right - 1 if is_fixed_right else hand_body_right
    print(
        f"[VEC] IK setup: hand_L={hand_body_left} jac_L={jacobian_body_left} "
        f"hand_R={hand_body_right} jac_R={jacobian_body_right} "
        f"fixed_L={is_fixed_left} fixed_R={is_fixed_right}"
    )

    # --- Preposition ---
    if args.target_mode in ("table_triangle", "table_triangle_narrow"):
        # Table-level targets: preposition above target height
        # EE = fingertip + FINGERTIP_OFFSET_Z ≈ target_z + 0.1123
        _prepos_z = args.target_z + 0.11
        prepos_left_start = torch.tensor(
            [0.40, -0.15, _prepos_z], dtype=torch.float32, device=device
        ).unsqueeze(0).expand(N, -1)
        prepos_right_start = torch.tensor(
            [0.40, +0.15, _prepos_z], dtype=torch.float32, device=device
        ).unsqueeze(0).expand(N, -1)
        print(f"[VEC] table_triangle: target_z={args.target_z}m prepos_z={_prepos_z:.2f}m")
    else:
        prepos_left_start = torch.tensor(
            [0.75, -0.15, 1.05], dtype=torch.float32, device=device
        ).unsqueeze(0).expand(N, -1)
        prepos_right_start = torch.tensor(
            [0.75, +0.15, 1.05], dtype=torch.float32, device=device
        ).unsqueeze(0).expand(N, -1)

    prepos_stats = dual_preposition_batch(
        robot_left=robot_left,
        robot_right=robot_right,
        sim=sim, scene=scene, device=device,
        hand_body_left=hand_body_left,
        hand_body_right=hand_body_right,
        jacobian_body_left=jacobian_body_left,
        jacobian_body_right=jacobian_body_right,
        left_start=prepos_left_start,
        right_start=prepos_right_start,
        num_envs=N,
        max_macros=args.prepos_max_macros,
        hold_steps=args.hold_steps,
        jt_alpha=args.prepos_jt_alpha,
        clip_rad=args.prepos_clip_rad,
        converge_m=args.prepos_converge_m,
    )
    print(f"[VEC][PREPOS] Done: {prepos_stats}")

    # --- Generate targets ---
    targets_per_env = make_targets_per_env(N, args.num_targets, args.seed_start,
                                              target_mode=args.target_mode,
                                              target_z=args.target_z)

    # --- Grasp mode: record cable positions BEFORE reaching & override targets ---
    _cable_pos_before_reaching = None  # tensor for drift computation (LOCAL frame)
    _env_origins = scene.env_origins  # (N, 3)
    if args.grasp and _cable is not None:
        _cable_pos_world = _cable.data.body_pos_w[0, :, :3].cpu().numpy()  # (n_segs, 3) world frame
        # Store cable positions in LOCAL frame for consistent drift comparison
        _cable_pos_before_reaching = (_cable.data.body_pos_w[0, :, :3] - _env_origins[0]).clone().cpu()
        _n_segs = _cable_pos_world.shape[0]
        # Convert to LOCAL coordinates by subtracting env_0 origin
        _env0_origin = _env_origins[0].cpu().numpy()  # (3,)
        _cable_pos_local = _cable_pos_world - _env0_origin  # (n_segs, 3) local frame
        _y_local = _cable_pos_local[:, 1]

        # Pick per-arm cable segments: target segments closer to each arm base
        # Wider spacing reduces reach distance (L base Y=-0.42, R base Y=0.20)
        _left_target_y = -0.16  # closer to left arm base (seg_2 Y≈-0.165)
        _right_target_y = +0.08  # closer to right arm base (seg_6 Y≈0.075)
        _left_seg_idx = int(np.argmin(np.abs(_y_local - _left_target_y)))
        _right_seg_idx = int(np.argmin(np.abs(_y_local - _right_target_y)))
        _left_seg_pos = _cable_pos_local[_left_seg_idx]
        _right_seg_pos = _cable_pos_local[_right_seg_idx]

        # Ball target = midpoint of left/right segments (for overhead descent positioning)
        _cable_mid = (_left_seg_pos + _right_seg_pos) / 2.0
        _grasp_target = np.array([_cable_mid[0], _cable_mid[1], _cable_mid[2]], dtype=np.float32)

        print(f"[GRASP] env_0 origin: ({_env0_origin[0]:.4f}, {_env0_origin[1]:.4f}, {_env0_origin[2]:.4f})")
        print(f"[GRASP] Cable positions BEFORE reaching (LOCAL coords, drift reference):")
        for si in range(_n_segs):
            _bname = _cable.body_names[si] if si < len(_cable.body_names) else f"seg_{si}"
            print(f"[GRASP]   [{si}] ({_bname}): X={_cable_pos_local[si,0]:.4f} "
                  f"Y={_cable_pos_local[si,1]:.4f} Z={_cable_pos_local[si,2]:.4f}")
        print(f"[GRASP] Left arm  → seg[{_left_seg_idx}] Y={_left_seg_pos[1]:.4f}")
        print(f"[GRASP] Right arm → seg[{_right_seg_idx}] Y={_right_seg_pos[1]:.4f}")
        print(f"[GRASP] Ball midpoint: ({_grasp_target[0]:.4f}, {_grasp_target[1]:.4f}, {_grasp_target[2]:.4f})")
        # Override ball target (for overhead descent initial positioning)
        for i in range(N):
            targets_per_env[i] = [_grasp_target.copy() for _ in range(len(targets_per_env[i]))]
        print(f"[GRASP] Targets overridden (local coords)")

    for i in range(min(N, 3)):
        print(f"[VEC] env={i} seed={args.seed_start + i} targets={len(targets_per_env[i])} "
              f"first={targets_per_env[i][0].tolist() if targets_per_env[i] else 'N/A'}")

    # --- Initialize env state ---
    env_state = EnvState(num_envs=N, device=device)
    env_state.set_targets(targets_per_env)

    # --- Grasp mode: override per-arm FT targets to cable segment positions ---
    if args.grasp and _cable is not None:
        # left_ft_target/right_ft_target from compute_dual_targets_batch have ±40mm Y offset.
        # For cable, arms must be AT the cable, not offset from it.
        _lft = torch.tensor(_left_seg_pos, dtype=torch.float32, device=device)
        _rft = torch.tensor(_right_seg_pos, dtype=torch.float32, device=device)
        for i in range(N):
            env_state.left_ft_target[i] = _lft
            env_state.right_ft_target[i] = _rft
        print(f"[GRASP] FT targets overridden: L=({_lft[0]:.4f},{_lft[1]:.4f},{_lft[2]:.4f}) "
              f"R=({_rft[0]:.4f},{_rft[1]:.4f},{_rft[2]:.4f})")

    # --- Camera backend setup (before overhead descent so it uses camera coords) ---
    _cam_accuracy_log: list[dict] = []
    _last_cam_estimate: Optional[np.ndarray] = None
    _cam_fallback_count = 0
    _cam_gt_fallback_count = 0
    if _USE_CAMERA:
        print(f"[VEC] Backend: dual_camera (camera-based ball detection)")
        _initial_ball = env_state.ball_pos[0].cpu().numpy()
        create_or_update_red_marker(tuple(float(x) for x in _initial_ball))
        for _ in range(5):
            sim.step()
            sim.render()
            scene.update(sim.get_physics_dt())
        print(f"[VEC] Red marker created at ({_initial_ball[0]:.4f}, {_initial_ball[1]:.4f}, {_initial_ball[2]:.4f})")
        # Camera estimation BEFORE overhead descent
        gt_ball = _initial_ball
        cam_est = estimate_target_from_cameras(scene, sim, ground_truth=gt_ball)
        if cam_est is not None:
            _last_cam_estimate = cam_est.copy()
            cam_err = float(np.linalg.norm(cam_est - gt_ball))
            _cam_accuracy_log.append({
                "tidx": 0, "macro": -1,
                "gt": gt_ball.copy(), "est": cam_est.copy(), "err_m": cam_err,
            })
            env_state.ball_pos[0] = torch.tensor(cam_est, dtype=torch.float32, device=device)
            left_ft, right_ft = compute_dual_targets_batch(env_state.ball_pos)
            env_state.left_ft_target = left_ft
            env_state.right_ft_target = right_ft
            env_state.left_standoff_ft = env_state.ball_pos.clone()
            env_state.left_standoff_ft[:, 1] -= 0.15
            print(f"[VEC][CAM] Pre-overhead estimate: err={cam_err*100:.1f}cm -> ball_pos overridden")
        else:
            _cam_gt_fallback_count += 1
            print(f"[VEC][CAM] Pre-overhead estimation FAILED, using GT fallback")
    else:
        print(f"[VEC] Backend: dual_heuristic (ground truth positions)")

    # --- Video setup (before overhead descent so frames are captured during grasp) ---
    video_frame_idx = [0]  # mutable for closure
    frames_dir = ""
    video_out = ""
    if args.save_video:
        frames_dir = os.path.join(args.output_dir, "video_frames")
        video_out = os.path.join(args.output_dir, "video.mp4")
        os.makedirs(frames_dir, exist_ok=True)
        print(f"[VEC] Video: {video_out} ({args.video_fps} fps)")

    def _video_on_step():
        """Callback to capture a video frame."""
        if not args.save_video or not frames_dir:
            return
        try:
            images = get_four_camera_images(scene, sim)
            if images:
                sheet = build_contact_sheet(images, resolution=args.contact_sheet_res)
                sheet.save(os.path.join(frames_dir, f"frame_{video_frame_idx[0]:06d}.png"))
                video_frame_idx[0] += 1
        except Exception:
            pass

    # --- Overhead descent (--approach overhead) ---
    overhead_stats = None
    _overhead_rerun_count = 0
    if args.approach == "overhead":
        _descent_z_min = args.finger_z_min if args.finger_table_contact else args.table_z_min
        overhead_stats = overhead_descent_batch(
            robot_left=robot_left, robot_right=robot_right,
            sim=sim, scene=scene, device=device,
            hand_body_left=hand_body_left, hand_body_right=hand_body_right,
            jacobian_body_left=jacobian_body_left,
            jacobian_body_right=jacobian_body_right,
            env_state=env_state, num_envs=N,
            standoff_y=args.standoff_dist,
            start_z=0.90,
            z_delta_clip=0.02,
            xy_converge_m=0.015,  # 15mm: tight for cable grasping
            z_converge_m=0.040,  # fix15: relaxed (Phase 2.9 handles Z convergence)
            max_macros=100,  # fix15: Phase 2.9 handles remaining Z gap
            hold_steps=args.hold_steps,
            jt_alpha=args.jt_alpha,
            clip_rad=args.clip_rad,
            table_z_min=_descent_z_min,
            cable=_cable if args.grasp else None,
            left_ft_override=env_state.left_ft_target[0] if args.grasp and _cable is not None else None,
            right_ft_override=env_state.right_ft_target[0] if args.grasp and _cable is not None else None,
            on_step=_video_on_step if args.save_video else None,
        )
        print(f"[VEC] Overhead descent done: {overhead_stats}")

        # For cable grasping: skip main reaching loop, go directly to grasp sequence.
        # The overhead descent already positioned fingers at cable with correct orientation.
        # The main reaching loop uses fingers_vertical=True which RUINS the cable orientation.
        if args.grasp and _cable is not None:
            for i in range(N):
                env_state.phase[i] = 2      # Mark as both-arms-reached
                env_state.right_reached[i] = True
                env_state.left_reached[i] = True
            print(f"[VEC] Cable grasp: skipping main reaching loop (overhead descent already positioned)")

    # --- Per-target result tracking ---
    # For each env, store per-target results: {tidx: {result, ft_err_L, ft_err_R, phA_steps, phB_steps}}
    per_target_results: list[dict] = [{} for _ in range(N)]

    # --- Min-Z tracking (table collision check) ---
    _min_z_left = float("inf")
    _min_z_right = float("inf")
    _min_z_per_target: list[dict] = []  # per-target min Z records

    # (Camera setup already done before overhead descent -- see above)

    # --- Main reaching loop ---
    total_macro_steps = 0
    t_start = time.time()

    while True:
        if STOP_REQUESTED:
            print("[VEC] Stop requested; exiting main loop.")
            break

        # Check if all envs are done
        all_done = (env_state.phase >= 3).all()
        if all_done:
            print("[VEC] All environments completed all targets.")
            break

        # Active envs: not all_done (phase < 3)
        active = (env_state.phase < 3)  # (N,) bool

        # Check for timeout (macro_step >= max_macro_steps) for envs in Phase A or B
        in_phase_ab = (env_state.phase == 0) | (env_state.phase == 1)
        timeout = in_phase_ab & (env_state.macro_step >= args.max_macro_steps)
        if timeout.any():
            # Compute current ft errors for timeout reporting
            _to_ee_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
            _to_eq_l = robot_left.data.body_quat_w[:, hand_body_left, :]
            _to_ee_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
            _to_eq_r = robot_right.data.body_quat_w[:, hand_body_right, :]
            _to_ft_l = ee_to_fingertip_batch(_to_ee_l, _to_eq_l)
            _to_ft_r = ee_to_fingertip_batch(_to_ee_r, _to_eq_r)
            _to_err_l = torch.norm(env_state.left_ft_target - _to_ft_l, dim=-1)
            _to_err_r = torch.norm(env_state.right_ft_target - _to_ft_r, dim=-1)

            # Mark timed-out targets as done_target (phase=2)
            env_state.phase[timeout] = 2
            for i in range(N):
                if timeout[i]:
                    tidx = int(env_state.current_target_idx[i].item())
                    macro = int(env_state.macro_step[i].item())
                    _phase_str = "A" if not env_state.right_reached[i] else "B"
                    _ft_err_r = float(_to_err_r[i].item())
                    _ft_err_l = float(_to_err_l[i].item())
                    _fail_dict = {
                        "result": "FAILED", "ft_err_L": _ft_err_l, "ft_err_R": _ft_err_r,
                        "phA": env_state.stats[i].get("_last_phase_a_macros", macro),
                        "phB": macro if _phase_str == "B" else 0,
                        "timeout_phase": _phase_str,
                    }
                    _minz_str = ""
                    if args.log_min_z and i == 0:
                        _fail_dict["min_z_left"] = _min_z_left
                        _fail_dict["min_z_right"] = _min_z_right
                        _minz_str = f" min_z_L={_min_z_left:.4f} min_z_R={_min_z_right:.4f}"
                        _min_z_left = float("inf")
                        _min_z_right = float("inf")
                    per_target_results[i][tidx] = _fail_dict
                    print(
                        f"[VEC] env={i} target={tidx} FAILED  "
                        f"phase={_phase_str} macro={macro} "
                        f"ft_err_L={_ft_err_l:.4f} ft_err_R={_ft_err_r:.4f}{_minz_str}"
                    )

        # --- Grasp sequence (after both arms reached) ---
        if args.grasp and _cable is not None:
            done_target_pre_grasp = (env_state.phase == 2)
            if done_target_pre_grasp.any():
                for i in range(N):
                    if done_target_pre_grasp[i]:
                        tidx = int(env_state.current_target_idx[i].item())
                        print(f"\n[GRASP] env={i} target={tidx}: Starting grasp sequence")
                        if _obs_collector is not None:
                            _obs_collector.start_episode(i)
                        _grasp_res = grasp_and_lift_sequence(
                            robot_left, robot_right, sim, scene, device,
                            _cable, args.grasp_close_steps, args.grasp_lift_z,
                            cable_pos_before_reaching=_cable_pos_before_reaching,
                            env_origin=_env_origins[i],
                            env_idx=i,
                            on_step=_video_on_step if args.save_video else None,
                            contact_sensors=_contact_sensors if args.contact_sensor else None,
                            kinematic_grasp=args.kinematic_grasp,
                            obs_builder=_obs_builder,
                            hand_body_left=_hand_idx_l if _obs_builder else -1,
                            hand_body_right=_hand_idx_r if _obs_builder else -1,
                            all_env_origins=_env_origins,
                            obs_collector=_obs_collector,
                        )
                        _grasp_results.append({"env": i, "target": tidx, **_grasp_res})
                        # Update per-target results
                        if tidx in per_target_results[i]:
                            per_target_results[i][tidx]["grasp"] = _grasp_res
                        _status = "LIFTED" if _grasp_res["cable_lifted"] else "FAILED"
                        if _grasp_res["nan_detected"]:
                            _status = "NaN"
                        if _grasp_res.get("grip_failed_reason"):
                            _status = f"GRIP_FAIL({_grasp_res['grip_failed_reason']})"
                        print(f"[GRASP] env={i} target={tidx}: {_status} "
                              f"cable_z_delta={_grasp_res['cable_z_delta']:.4f}m")

        # Advance envs with phase=2 (target done) to next target
        done_target = (env_state.phase == 2)
        if done_target.any():
            env_state.advance_to_next_target(done_target)
            # Update red marker for camera backend (env 0 only)
            if _USE_CAMERA and done_target[0] and env_state.phase[0] < 3:
                _new_ball = env_state.ball_pos[0].cpu().numpy()
                create_or_update_red_marker(tuple(float(x) for x in _new_ball))
                for _ in range(5):
                    sim.step()
                    sim.render()
                    scene.update(sim.get_physics_dt())
                # Camera estimation before overhead re-run
                _tidx_cam = int(env_state.current_target_idx[0].item())
                gt_ball = _new_ball
                cam_est = estimate_target_from_cameras(scene, sim, ground_truth=gt_ball)
                if cam_est is not None:
                    _last_cam_estimate = cam_est.copy()
                    cam_err = float(np.linalg.norm(cam_est - gt_ball))
                    _cam_accuracy_log.append({
                        "tidx": _tidx_cam, "macro": -1,
                        "gt": gt_ball.copy(), "est": cam_est.copy(), "err_m": cam_err,
                    })
                    env_state.ball_pos[0] = torch.tensor(cam_est, dtype=torch.float32, device=device)
                    left_ft, right_ft = compute_dual_targets_batch(env_state.ball_pos)
                    env_state.left_ft_target = left_ft
                    env_state.right_ft_target = right_ft
                    env_state.left_standoff_ft = env_state.ball_pos.clone()
                    env_state.left_standoff_ft[:, 1] -= 0.15
                    print(f"[VEC][CAM] Target {_tidx_cam} camera estimate: err={cam_err*100:.1f}cm -> ball_pos overridden")
                elif _last_cam_estimate is not None:
                    _cam_fallback_count += 1
                    env_state.ball_pos[0] = torch.tensor(_last_cam_estimate, dtype=torch.float32, device=device)
                    left_ft, right_ft = compute_dual_targets_batch(env_state.ball_pos)
                    env_state.left_ft_target = left_ft
                    env_state.right_ft_target = right_ft
                    env_state.left_standoff_ft = env_state.ball_pos.clone()
                    env_state.left_standoff_ft[:, 1] -= 0.15
                    print(f"[VEC][CAM] Target {_tidx_cam} estimation failed, using previous estimate")
                else:
                    _cam_gt_fallback_count += 1
                    print(f"[VEC][CAM] Target {_tidx_cam} estimation failed, no prior, using GT")

            # Re-run overhead descent for new target (position above ball -> descend)
            if args.approach == "overhead" and (env_state.phase < 3).any():
                _ovh_stats = overhead_descent_batch(
                    robot_left=robot_left, robot_right=robot_right,
                    sim=sim, scene=scene, device=device,
                    hand_body_left=hand_body_left, hand_body_right=hand_body_right,
                    jacobian_body_left=jacobian_body_left,
                    jacobian_body_right=jacobian_body_right,
                    env_state=env_state, num_envs=N,
                    standoff_y=args.standoff_dist,
                    start_z=0.90,
                    z_delta_clip=0.02,
                    xy_converge_m=0.015,
                    z_converge_m=0.040,
                    max_macros=100,
                    hold_steps=args.hold_steps,
                    jt_alpha=args.jt_alpha,
                    clip_rad=args.clip_rad,
                    table_z_min=_descent_z_min,
                    cable=_cable if args.grasp else None,
                    left_ft_override=env_state.left_ft_target[0] if args.grasp and _cable is not None else None,
                    right_ft_override=env_state.right_ft_target[0] if args.grasp and _cable is not None else None,
                    on_step=_video_on_step if args.save_video else None,
                )
                _overhead_rerun_count += 1
                print(f"[VEC] Overhead descent re-run #{_overhead_rerun_count}: {_ovh_stats}")

        # Re-check active after advancing
        active = (env_state.phase < 2)  # (N,)
        if not active.any():
            # All envs waiting for next target or done -- check for all_done
            if (env_state.phase >= 3).all():
                break
            continue

        # --- Compute current states ---
        ee_pos_left = robot_left.data.body_pos_w[:, hand_body_left, :3]  # (N, 3)
        ee_quat_left = robot_left.data.body_quat_w[:, hand_body_left, :]  # (N, 4)
        ee_pos_right = robot_right.data.body_pos_w[:, hand_body_right, :3]
        ee_quat_right = robot_right.data.body_quat_w[:, hand_body_right, :]

        ft_left = ee_to_fingertip_batch(ee_pos_left, ee_quat_left)  # (N, 3)
        ft_right = ee_to_fingertip_batch(ee_pos_right, ee_quat_right)

        # --- Track min Z for table collision check ---
        if args.log_min_z:
            _ft_z_l = float(ft_left[0, 2].item())
            _ft_z_r = float(ft_right[0, 2].item())
            _min_z_left = min(_min_z_left, _ft_z_l)
            _min_z_right = min(_min_z_right, _ft_z_r)

        # --- Check success per phase ---
        in_phase_a = (env_state.phase == 0) & active  # Phase A: right arm active
        in_phase_b = (env_state.phase == 1) & active  # Phase B: left arm active

        # Phase A success: right fingertip reaches right_ft_target
        right_ft_err = torch.norm(env_state.right_ft_target - ft_right, dim=-1)  # (N,)
        phase_a_reached = in_phase_a & (right_ft_err <= args.success_threshold_m)
        if phase_a_reached.any():
            # Save macro_step BEFORE reset for reporting
            phase_a_macros_snapshot = env_state.macro_step.clone()
            # Transition Phase A -> Phase B for these envs
            env_state.phase[phase_a_reached] = 1
            env_state.right_reached[phase_a_reached] = True
            env_state.macro_step[phase_a_reached] = 0
            # Save right arm hold position (current FT pos)
            env_state.right_hold_ft[phase_a_reached] = ft_right[phase_a_reached].clone()
            for i in range(N):
                if phase_a_reached[i]:
                    tidx = int(env_state.current_target_idx[i].item())
                    macro = int(phase_a_macros_snapshot[i].item())
                    env_state.stats[i]["phase_a_macros_total"] += macro
                    env_state.stats[i]["_last_phase_a_macros"] = macro
                    print(f"[VEC] env={i} target={tidx} Phase_A REACHED (right arm) err={right_ft_err[i].item():.4f}m macros={macro}")

        # Phase B success: left fingertip reaches left_ft_target
        left_ft_err = torch.norm(env_state.left_ft_target - ft_left, dim=-1)  # (N,)
        phase_b_reached = in_phase_b & (left_ft_err <= args.success_threshold_m)
        if phase_b_reached.any():
            env_state.phase[phase_b_reached] = 2  # target done
            env_state.left_reached[phase_b_reached] = True
            for i in range(N):
                if phase_b_reached[i]:
                    tidx = int(env_state.current_target_idx[i].item())
                    macro = int(env_state.macro_step[i].item())
                    env_state.stats[i]["phase_b_macros_total"] += macro
                    env_state.stats[i]["targets_reached"] += 1
                    _ft_err_r = float(right_ft_err[i].item())
                    _ft_err_l = float(left_ft_err[i].item())
                    _ph_a = env_state.stats[i].get("_last_phase_a_macros", 0)
                    _result_dict = {
                        "result": "REACHED", "ft_err_L": _ft_err_l, "ft_err_R": _ft_err_r,
                        "phA": _ph_a, "phB": macro,
                    }
                    _minz_str = ""
                    if args.log_min_z and i == 0:
                        _ft_final_l = ft_left[0].cpu().numpy()
                        _ft_final_r = ft_right[0].cpu().numpy()
                        _result_dict["min_z_left"] = _min_z_left
                        _result_dict["min_z_right"] = _min_z_right
                        _result_dict["final_ft_left"] = _ft_final_l.tolist()
                        _result_dict["final_ft_right"] = _ft_final_r.tolist()
                        _minz_str = (
                            f" min_z_L={_min_z_left:.4f} min_z_R={_min_z_right:.4f}"
                            f" ft_L=({_ft_final_l[0]:.3f},{_ft_final_l[1]:.3f},{_ft_final_l[2]:.3f})"
                            f" ft_R=({_ft_final_r[0]:.3f},{_ft_final_r[1]:.3f},{_ft_final_r[2]:.3f})"
                        )
                        # Reset min-Z for next target
                        _min_z_left = float("inf")
                        _min_z_right = float("inf")
                    per_target_results[i][tidx] = _result_dict
                    print(
                        f"[VEC] env={i} target={tidx} REACHED  "
                        f"ft_err_L={_ft_err_l:.4f} ft_err_R={_ft_err_r:.4f} "
                        f"phA={_ph_a} phB={macro}{_minz_str}"
                    )

        # Refresh active masks after phase transitions
        in_phase_a = (env_state.phase == 0)
        in_phase_b = (env_state.phase == 1)
        active = in_phase_a | in_phase_b

        if not active.any():
            continue

        # --- Camera-based ball estimation (dual_camera only, env 0) ---
        # Only estimate once per target (macro_step == 0) since the ball is static.
        # Repeated estimation during approach causes jitter from arm occlusion.
        if _USE_CAMERA and int(env_state.macro_step[0].item()) == 0:
            tidx_0 = int(env_state.current_target_idx[0].item())
            if not any(r["tidx"] == tidx_0 for r in _cam_accuracy_log):
                gt_ball = env_state.ball_pos[0].cpu().numpy()
                cam_est = estimate_target_from_cameras(scene, sim, ground_truth=gt_ball)
                # Fix 3: if estimation fails, try previous estimate before GT fallback
                if cam_est is None and _last_cam_estimate is not None:
                    cam_est = _last_cam_estimate.copy()
                    _cam_fallback_count += 1
                    print(f"[VEC][CAM] Using previous estimate for target {tidx_0} (current detection failed)")
                elif cam_est is None:
                    _cam_gt_fallback_count += 1
                    print(f"[VEC][CAM] estimation failed for target {tidx_0}, no prior estimate, using ground truth")
                if cam_est is not None:
                    _last_cam_estimate = cam_est.copy()
                    cam_err = float(np.linalg.norm(cam_est - gt_ball))
                    macro_0 = int(env_state.macro_step[0].item())
                    _cam_accuracy_log.append({
                        "tidx": tidx_0, "macro": macro_0,
                        "gt": gt_ball.copy(), "est": cam_est.copy(),
                        "err_m": cam_err,
                    })
                    # Override ball_pos + targets with camera estimate
                    _cam_ball = torch.tensor(cam_est, dtype=torch.float32, device=device).unsqueeze(0)
                    env_state.ball_pos[0] = _cam_ball[0]
                    _cam_left_ft, _cam_right_ft = compute_dual_targets_batch(_cam_ball)
                    env_state.left_ft_target[0] = _cam_left_ft[0]
                    env_state.right_ft_target[0] = _cam_right_ft[0]
                    env_state.left_standoff_ft[0, 0] = _cam_ball[0, 0]
                    env_state.left_standoff_ft[0, 1] = _cam_ball[0, 1] - 0.15
                    env_state.left_standoff_ft[0, 2] = _cam_ball[0, 2]

        # --- Compute EE targets from FT targets ---
        # Phase A: active=right arm -> right_ft_target, passive=left arm -> left_standoff_ft
        # Phase B: active=left arm -> left_ft_target, passive=right arm -> right_hold_ft

        # Left arm command: Phase A -> standoff, Phase B -> left_ft_target
        left_ft_cmd = torch.where(
            in_phase_a.unsqueeze(-1).expand_as(env_state.left_standoff_ft),
            env_state.left_standoff_ft,
            env_state.left_ft_target,
        )
        left_ee_cmd = fingertip_to_ee_batch(left_ft_cmd, ee_quat_left)  # (N, 3)

        # Right arm command: Phase A -> right_ft_target, Phase B -> right_hold_ft
        right_ft_cmd = torch.where(
            in_phase_a.unsqueeze(-1).expand_as(env_state.right_ft_target),
            env_state.right_ft_target,
            env_state.right_hold_ft,
        )
        right_ee_cmd = fingertip_to_ee_batch(right_ft_cmd, ee_quat_right)  # (N, 3)

        # --- Heuristic delta (toward EE target) with clipping (matches reference) ---
        left_delta = left_ee_cmd - ee_pos_left  # (N, 3)
        right_delta = right_ee_cmd - ee_pos_right

        # Position delta clipping to ±trans_delta_clip_m (reference: ±0.05m)
        clip_m = args.trans_delta_clip_m
        left_delta = left_delta.clamp(-clip_m, clip_m)
        right_delta = right_delta.clamp(-clip_m, clip_m)

        # Approach slowdown (reference: 0.5x when ft_err < approach_slowdown_dist)
        left_ft_err_unsq = torch.norm(left_ft_cmd - ft_left, dim=-1)
        right_ft_err_unsq = torch.norm(right_ft_cmd - ft_right, dim=-1)
        left_slow = (left_ft_err_unsq < args.approach_slowdown_dist).unsqueeze(-1)
        right_slow = (right_ft_err_unsq < args.approach_slowdown_dist).unsqueeze(-1)
        left_delta = torch.where(left_slow.expand_as(left_delta), left_delta * 0.5, left_delta)
        right_delta = torch.where(right_slow.expand_as(right_delta), right_delta * 0.5, right_delta)

        # Collision avoidance (reference: check_arm_separation, linear scale)
        arm_dist, arm_scale = check_arm_separation_batch(
            ee_pos_left, ee_pos_right, min_dist=args.collision_min_dist,
        )
        arm_scale_3d = arm_scale.unsqueeze(-1).expand_as(left_delta)
        left_delta = left_delta * arm_scale_3d
        right_delta = right_delta * arm_scale_3d

        # Compute cmd positions
        cmd_left = ee_pos_left + left_delta
        cmd_right = ee_pos_right + right_delta

        # --- Fine-RL precision refinement (blend with heuristic) ---
        if _fine_rl_actor is not None and active.any():
            # Per-arm distance to respective FT targets
            _rl_err_l = torch.norm(env_state.left_ft_target - ft_left, dim=-1)   # (N,)
            _rl_err_r = torch.norm(env_state.right_ft_target - ft_right, dim=-1)  # (N,)
            # Per-arm sigmoid blending: alpha -> 1 as distance -> 0
            _alpha_l = torch.sigmoid(-(_rl_err_l - args.rl_blend_center) / args.rl_blend_temp)
            _alpha_r = torch.sigmoid(-(_rl_err_r - args.rl_blend_center) / args.rl_blend_temp)

            # Build observation (12D)
            if args.rl_relative_obs:
                # Relative: [err_l, err_r, arm_sep, target_sep] — position-invariant
                _rl_obs = torch.cat([
                    env_state.left_ft_target - ft_left,
                    env_state.right_ft_target - ft_right,
                    ft_right - ft_left,
                    env_state.right_ft_target - env_state.left_ft_target,
                ], dim=-1)  # (N, 12)
            else:
                # Absolute: [ft_left, ft_right, left_ft_target, right_ft_target]
                _rl_obs = torch.cat([ft_left, ft_right,
                                     env_state.left_ft_target, env_state.right_ft_target], dim=-1)  # (N, 12)
            with torch.no_grad():
                _rl_action = _fine_rl_actor(_rl_obs)  # (N, 6)
            _rl_action = _rl_action.clamp(-args.rl_action_clip, args.rl_action_clip)
            _rl_delta_ft_l = _rl_action[:, :3]  # (N, 3)
            _rl_delta_ft_r = _rl_action[:, 3:]  # (N, 3)

            # RL proposes: new FT = current FT + delta -> convert to EE target
            _rl_ft_l = ft_left + _rl_delta_ft_l
            _rl_ft_r = ft_right + _rl_delta_ft_r
            _rl_ee_l = fingertip_to_ee_batch(_rl_ft_l, ee_quat_left)
            _rl_ee_r = fingertip_to_ee_batch(_rl_ft_r, ee_quat_right)

            # Blend heuristic and RL EE commands per arm
            _al3 = _alpha_l.unsqueeze(-1).expand_as(cmd_left)
            _ar3 = _alpha_r.unsqueeze(-1).expand_as(cmd_right)
            cmd_left = (1.0 - _al3) * cmd_left + _al3 * _rl_ee_l
            cmd_right = (1.0 - _ar3) * cmd_right + _ar3 * _rl_ee_r

            _rl_refinement_count += 1
            if total_macro_steps % 50 == 0:
                print(f"[FINE_RL] macro={total_macro_steps} "
                      f"alpha_L={_alpha_l[0].item():.3f} alpha_R={_alpha_r[0].item():.3f} "
                      f"err_L={_rl_err_l[0].item()*1000:.1f}mm err_R={_rl_err_r[0].item()*1000:.1f}mm")

        # --- Z-floor clamping (overhead approach: prevent going below table) ---
        if args.approach == "overhead":
            # Compute would-be fingertip Z from proposed EE command
            # (accounts for orientation: FT offset is along gripper +Z, not world Z)
            ft_cmd_left = ee_to_fingertip_batch(cmd_left, ee_quat_left)
            ft_cmd_right = ee_to_fingertip_batch(cmd_right, ee_quat_right)
            # Z-floor: use relaxed finger_z_min when finger contact enabled
            _z_floor = args.finger_z_min if args.finger_table_contact else args.table_z_min
            # If fingertip Z would go below floor, push EE Z up by the violation
            z_viol_left = (_z_floor - ft_cmd_left[:, 2]).clamp(min=0.0)
            z_viol_right = (_z_floor - ft_cmd_right[:, 2]).clamp(min=0.0)
            cmd_left[:, 2] = cmd_left[:, 2] + z_viol_left
            cmd_right[:, 2] = cmd_right[:, 2] + z_viol_right

        # --- Orientation control masks ---
        # Phase A: orientation for right (active), pos-only for left (passive)
        # Phase B: orientation for both
        left_ori_mask = in_phase_b  # Only in Phase B
        right_ori_mask = in_phase_a | in_phase_b  # Always for right when active

        # --- IK inner loop ---
        _fingers_vert = (args.approach == "overhead")
        for hold_i in range(args.hold_steps):
            if STOP_REQUESTED:
                break

            # Left arm IK
            ik_left, nan_left = jt_ik_step_6dof_batch(
                robot_left, jacobian_body_left, hand_body_left,
                cmd_left, env_state.ball_pos, left_ori_mask,
                args.jt_alpha, args.jt_alpha_ori, args.ori_enable_dist,
                args.clip_rad, device,
                fingers_vertical=_fingers_vert,
            )
            # Right arm IK
            ik_right, nan_right = jt_ik_step_6dof_batch(
                robot_right, jacobian_body_right, hand_body_right,
                cmd_right, env_state.ball_pos, right_ori_mask,
                args.jt_alpha, args.jt_alpha_ori, args.ori_enable_dist,
                args.clip_rad, device,
                fingers_vertical=_fingers_vert,
            )

            # Track NaN
            nan_any = nan_left | nan_right
            if nan_any.any():
                for i in range(N):
                    if nan_any[i] and active[i]:
                        env_state.stats[i]["nan_count"] += 1

            # Apply joints (only for active envs without NaN)
            apply_mask_left = active & (~nan_left)
            apply_mask_right = active & (~nan_right)
            apply_joints_batch(robot_left, ik_left, apply_mask_left)
            apply_joints_batch(robot_right, ik_right, apply_mask_right)

            sim.step()
            scene.update(sim.get_physics_dt())

        # --- Finger-table contact monitoring (position-based, after hold loop) ---
        if args.finger_table_contact and active.any():
            _table_z = 0.75  # table surface Z
            _contact_threshold = 0.005  # 5mm from table = contact

            # Fingertip positions (already computed as ft_left, ft_right)
            _ft_z_l = ft_left[:, 2]  # (N,)
            _ft_z_r = ft_right[:, 2]

            # Finger contact: fingertip Z within contact_threshold of table
            _finger_near_table_l = (_ft_z_l - _table_z) < _contact_threshold
            _finger_near_table_r = (_ft_z_r - _table_z) < _contact_threshold
            if (_finger_near_table_l & active).any() or (_finger_near_table_r & active).any():
                _total_finger_contacts += 1
                # Estimate contact "force" from penetration (spring model: F = k * penetration)
                _pen_l = (_table_z - _ft_z_l).clamp(min=0.0)  # penetration depth
                _pen_r = (_table_z - _ft_z_r).clamp(min=0.0)
                _est_force = float(max(_pen_l.max().item(), _pen_r.max().item())) * 1000.0  # k=1000 N/m
                _max_finger_force = max(_max_finger_force, _est_force)

            # Non-finger violation: check hand (panda_hand) Z position
            _hand_z_l = robot_left.data.body_pos_w[:, _hand_body_idx_left, 2]
            _hand_z_r = robot_right.data.body_pos_w[:, _hand_body_idx_right, 2]
            # panda_hand center is FINGERTIP_OFFSET (~0.1123m) above fingertip
            # In overhead mode, hand is at ft_z + 0.1123 ≈ 0.87m, far above table
            # Violation only if hand Z actually approaches table surface (< table_z + 0.02)
            _hand_near_table = ((_hand_z_l - _table_z) < 0.02) | ((_hand_z_r - _table_z) < 0.02)
            if (_hand_near_table & active).any():
                _non_finger_table_violations += 1

            # Periodic log
            if total_macro_steps % 50 == 0:
                _min_ft_z = min(float(_ft_z_l[active].min().item()),
                               float(_ft_z_r[active].min().item())) if active.any() else 0.0
                print(f"[FINGER_CONTACT] macro={total_macro_steps} "
                      f"finger_contacts={_total_finger_contacts} "
                      f"max_est_force={_max_finger_force:.3f}N "
                      f"min_ft_z={_min_ft_z:.4f}m "
                      f"hand_violations={_non_finger_table_violations}")

        # --- Demo recording (macro-level, after hold loop) ---
        if args.save_hdf5:
            record_demo_step(
                env_state, robot_left, robot_right,
                hand_body_left, hand_body_right,
                active, left_delta, right_delta,
            )

        # --- Video frame capture ---
        if args.save_video and frames_dir:
            _video_on_step()

        # --- Camera accuracy periodic report ---
        if _USE_CAMERA and _cam_accuracy_log and total_macro_steps % 50 == 0:
            _recent_errs = [r["err_m"] * 100 for r in _cam_accuracy_log]
            print(
                f"[VEC][CAM] accuracy so far: n={len(_recent_errs)} "
                f"mean={np.mean(_recent_errs):.2f}cm max={np.max(_recent_errs):.2f}cm"
            )

        # Increment macro step for active envs
        env_state.macro_step[active] += 1
        total_macro_steps += 1

        # Periodic progress report
        if total_macro_steps % 50 == 0:
            elapsed = time.time() - t_start
            done_count = (env_state.phase >= 3).sum().item()
            targets_done = env_state.targets_completed.sum().item()
            total_reached = sum(s["targets_reached"] for s in env_state.stats)
            print(
                f"[VEC][PROGRESS] macro_steps={total_macro_steps} elapsed={elapsed:.1f}s "
                f"envs_done={done_count}/{N} reached={total_reached} "
                f"phase_dist=A:{(env_state.phase == 0).sum().item()} "
                f"B:{(env_state.phase == 1).sum().item()} "
                f"done:{(env_state.phase == 2).sum().item()} "
                f"all_done:{(env_state.phase >= 3).sum().item()}"
            )

    # --- Finalize video ---
    if args.save_video and frames_dir:
        finalize_video(frames_dir, video_out, args.video_fps)

    # --- Summary ---
    elapsed = time.time() - t_start
    print(f"\n{'='*72}")
    print(f"[VEC] SUMMARY  num_envs={N} elapsed={elapsed:.1f}s total_macro_steps={total_macro_steps}")
    print(f"{'='*72}")
    total_reached = 0
    total_targets = 0
    total_nans = 0
    for i in range(N):
        s = env_state.stats[i]
        total_reached += s["targets_reached"]
        total_targets += s["targets_total"]
        total_nans += s["nan_count"]
        print(
            f"  env={i} seed={args.seed_start + i} "
            f"reached={s['targets_reached']}/{s['targets_total']} "
            f"nan={s['nan_count']}"
        )
    print(f"  TOTAL: {total_reached}/{total_targets} reached, {total_nans} NaN events")
    if _fine_rl_actor is not None:
        print(f"  Fine-RL: {_rl_refinement_count} macro steps with RL blending")
    if args.finger_table_contact:
        print(f"  Finger-Table Contact: finger_contacts={_total_finger_contacts} "
              f"max_est_force={_max_finger_force:.3f}N "
              f"hand_violations={_non_finger_table_violations}")
    if args.grasp and _grasp_results:
        _g_lifted = sum(1 for g in _grasp_results if g.get("cable_lifted", False))
        _g_grip_ok = sum(1 for g in _grasp_results if g.get("grip_success_left") and g.get("grip_success_right"))
        _g_nan = sum(1 for g in _grasp_results if g.get("nan_detected", False))
        print(f"  Grasp: {_g_lifted}/{len(_grasp_results)} lifted, "
              f"{_g_grip_ok}/{len(_grasp_results)} grip_ok, {_g_nan} NaN")
        for g in _grasp_results:
            _gs = "LIFTED" if g["cable_lifted"] else ("NaN" if g["nan_detected"] else "FAILED")
            if g.get("grip_failed_reason"):
                _gs = f"GRIP_FAIL"
            _gw_l = g.get("grip_width_left", 0) * 1000
            _gw_r = g.get("grip_width_right", 0) * 1000
            _zb = sum(g["cable_z_before"]) / max(len(g["cable_z_before"]), 1) if g["cable_z_before"] else 0.0
            _za = sum(g["cable_z_after"]) / max(len(g["cable_z_after"]), 1) if g["cable_z_after"] else 0.0
            _drift_str = ""
            if g.get("cable_drift_xyz"):
                _dm = g["cable_drift_xyz"]["mean"]
                _drift_str = f" drift=({_dm[0]*1000:.1f},{_dm[1]*1000:.1f},{_dm[2]*1000:.1f})mm"
            print(f"    env={g['env']} tgt={g['target']} {_gs} "
                  f"grip_L={_gw_l:.1f}mm grip_R={_gw_r:.1f}mm "
                  f"cable_z_before={_zb:.4f} cable_z_after={_za:.4f} "
                  f"delta={g['cable_z_delta']:.4f}m{_drift_str}")
    print(f"  Throughput: {total_targets / max(elapsed, 0.01):.1f} targets/s")
    print(f"{'='*72}")

    # --- Comprehensive per-env measurement table ---
    if args.grasp and _grasp_results:
        print(f"\n{'='*90}")
        print("[VEC] PER-ENV MEASUREMENT TABLE")
        print(f"{'='*90}")
        print(f"{'env':>3} {'status':>10} {'ft_z_p29_L':>11} {'ft_z_p29_R':>11} "
              f"{'fo_X_p299_L':>12} {'fo_X_p299_R':>12} {'grip_L_mm':>10} {'grip_R_mm':>10} "
              f"{'cable_dZ':>9}")
        print(f"{'-'*90}")
        _n10_lifted = 0
        for g in _grasp_results:
            _gs = "LIFTED" if g["cable_lifted"] else ("NaN" if g["nan_detected"] else "FAILED")
            if g.get("grip_failed_reason"):
                _gs = f"GRIP_FAIL"
            if g["cable_lifted"]:
                _n10_lifted += 1
            _p29_l = f"{g['ft_z_after_p29_left']:.4f}" if g.get('ft_z_after_p29_left') is not None else "N/A"
            _p29_r = f"{g['ft_z_after_p29_right']:.4f}" if g.get('ft_z_after_p29_right') is not None else "N/A"
            _fox_l = f"{g['fo_x_after_p299_left']:.3f}" if g.get('fo_x_after_p299_left') is not None else "N/A"
            _fox_r = f"{g['fo_x_after_p299_right']:.3f}" if g.get('fo_x_after_p299_right') is not None else "N/A"
            _gw_l = g.get("grip_width_left", 0) * 1000
            _gw_r = g.get("grip_width_right", 0) * 1000
            print(f"{g['env']:>3} {_gs:>10} {_p29_l:>11} {_p29_r:>11} "
                  f"{_fox_l:>12} {_fox_r:>12} {_gw_l:>10.1f} {_gw_r:>10.1f} "
                  f"{g['cable_z_delta']:>9.4f}")
        print(f"{'-'*90}")
        print(f"SUCCESS RATE: {_n10_lifted}/{len(_grasp_results)}")
        # Reaching phase failures
        _reach_failures = []
        for i in range(N):
            for tidx in sorted(per_target_results[i].keys()):
                r = per_target_results[i][tidx]
                if r["result"] in ("FAILED", "TIMEOUT"):
                    _reach_failures.append((i, tidx, r))
        if _reach_failures:
            print(f"\n  REACHING FAILURES:")
            for _ei, _ti, _rf in _reach_failures:
                print(f"    env={_ei} target={_ti} result={_rf['result']} "
                      f"ft_err_L={_rf['ft_err_L']:.4f} ft_err_R={_rf['ft_err_R']:.4f}"
                      f"{' timeout_phase=' + _rf['timeout_phase'] if 'timeout_phase' in _rf else ''}")
        print(f"{'='*90}")

    # --- Per-target results table ---
    print(f"\n{'='*72}")
    print("[VEC] PER-TARGET RESULTS")
    print(f"{'='*72}")
    for i in range(N):
        print(f"  env={i} seed={args.seed_start + i}:")
        for tidx in sorted(per_target_results[i].keys()):
            r = per_target_results[i][tidx]
            result = r["result"]
            ft_l = r["ft_err_L"]
            ft_r = r["ft_err_R"]
            ph_a = r.get("phA", 0)
            ph_b = r.get("phB", 0)
            extra = f" timeout_phase={r['timeout_phase']}" if "timeout_phase" in r else ""
            print(
                f"    target={tidx} {result}  "
                f"ft_err_L={ft_l:.4f} ft_err_R={ft_r:.4f} "
                f"phA={ph_a} phB={ph_b}{extra}"
            )
    print(f"{'='*72}\n")

    # --- Camera accuracy summary ---
    if _USE_CAMERA and _cam_accuracy_log:
        errs = [r["err_m"] * 100 for r in _cam_accuracy_log]
        print(f"{'='*72}")
        print(f"[CAM_ACCURACY] Camera estimation accuracy summary ({len(_cam_accuracy_log)} targets)")
        print(f"{'='*72}")
        print(f"{'Tgt':>3} {'Macro':>5} {'GT_X':>8} {'GT_Y':>8} {'GT_Z':>8} "
              f"{'Est_X':>8} {'Est_Y':>8} {'Est_Z':>8} {'Err_cm':>7}")
        print(f"{'-'*72}")
        for r in _cam_accuracy_log:
            gt, est = r["gt"], r["est"]
            print(
                f"{r['tidx']:>3} {r['macro']:>5} "
                f"{gt[0]:>8.4f} {gt[1]:>8.4f} {gt[2]:>8.4f} "
                f"{est[0]:>8.4f} {est[1]:>8.4f} {est[2]:>8.4f} "
                f"{r['err_m']*100:>7.2f}"
            )
        print(f"{'-'*72}")
        print(
            f"[CAM_ACCURACY] mean={np.mean(errs):.2f}cm  max={np.max(errs):.2f}cm  "
            f"min={np.min(errs):.2f}cm  std={np.std(errs):.2f}cm"
        )
        print(f"[CAM_ACCURACY] prev_estimate_reuse={_cam_fallback_count}  gt_fallback={_cam_gt_fallback_count}")
        print(f"{'='*72}\n")

    # --- Save HDF5 ---
    if args.save_hdf5:
        save_demos_hdf5(env_state, args.output_dir, args.seed_start)

    # --- Save summary JSON ---
    summary = {
        "script": "poc_dual_arm_vectorized.py",
        "backend": args.backend,
        "num_envs": N,
        "num_targets": args.num_targets,
        "seed_start": args.seed_start,
        "total_reached": total_reached,
        "total_targets": total_targets,
        "total_nan": total_nans,
        "elapsed_s": round(elapsed, 2),
        "throughput_targets_per_s": round(total_targets / max(elapsed, 0.01), 2),
        "per_env": [
            {
                "env_id": i,
                "seed": args.seed_start + i,
                "reached": env_state.stats[i]["targets_reached"],
                "total": env_state.stats[i]["targets_total"],
                "nan_count": env_state.stats[i]["nan_count"],
                "per_target": per_target_results[i],
            }
            for i in range(N)
        ],
        "preposition": prepos_stats,
        "overhead_descent": overhead_stats,
        "overhead_rerun_count": _overhead_rerun_count,
        "args": {
            "backend": args.backend,
            "approach": args.approach,
            "target_mode": args.target_mode,
            "target_z": args.target_z,
            "table_z_min": args.table_z_min,
            "with_table": args.with_table,
            "jt_alpha": args.jt_alpha,
            "jt_alpha_ori": args.jt_alpha_ori,
            "clip_rad": args.clip_rad,
            "hold_steps": args.hold_steps,
            "max_macro_steps": args.max_macro_steps,
            "success_threshold_m": args.success_threshold_m,
            "trans_delta_clip_m": args.trans_delta_clip_m,
            "collision_min_dist": args.collision_min_dist,
            "approach_slowdown_dist": args.approach_slowdown_dist,
            "env_spacing": args.env_spacing,
            "fine_rl_checkpoint": args.fine_rl_checkpoint or None,
            "rl_blend_center": args.rl_blend_center,
            "rl_blend_temp": args.rl_blend_temp,
            "rl_action_clip": args.rl_action_clip,
        },
        "fine_rl": {
            "enabled": _fine_rl_actor is not None,
            "rl_macro_steps": _rl_refinement_count,
        },
        "finger_table_contact": {
            "enabled": args.finger_table_contact,
            "finger_z_min": args.finger_z_min if args.finger_table_contact else None,
            "finger_contacts": _total_finger_contacts if args.finger_table_contact else 0,
            "max_finger_force_N": round(_max_finger_force, 4) if args.finger_table_contact else 0,
            "hand_violations": _non_finger_table_violations if args.finger_table_contact else 0,
        },
        "grasp": {
            "enabled": args.grasp,
            "cable_x": args.cable_x if args.grasp else None,
            "close_steps": args.grasp_close_steps if args.grasp else None,
            "lift_z": args.grasp_lift_z if args.grasp else None,
            "total_attempts": len(_grasp_results),
            "total_lifted": sum(1 for g in _grasp_results if g.get("cable_lifted", False)),
            "total_nan": sum(1 for g in _grasp_results if g.get("nan_detected", False)),
            "results": _grasp_results,
        },
    }
    # Add camera accuracy to summary if available
    if _USE_CAMERA and _cam_accuracy_log:
        errs = [r["err_m"] * 100 for r in _cam_accuracy_log]
        summary["camera_accuracy"] = {
            "num_estimates": len(_cam_accuracy_log),
            "prev_estimate_reuse": _cam_fallback_count,
            "gt_fallback": _cam_gt_fallback_count,
            "mean_cm": round(float(np.mean(errs)), 2),
            "max_cm": round(float(np.max(errs)), 2),
            "min_cm": round(float(np.min(errs)), 2),
            "std_cm": round(float(np.std(errs)), 2),
            "per_target": [
                {
                    "tidx": r["tidx"],
                    "gt": r["gt"].tolist(),
                    "est": r["est"].tolist(),
                    "err_cm": round(r["err_m"] * 100, 2),
                }
                for r in _cam_accuracy_log
            ],
        }
    summary_path = os.path.join(args.output_dir, "vectorized_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[VEC] Summary saved: {summary_path}")

    # B1: Save obs stats if collected
    if _obs_collector is not None and _obs_collector._records:
        _obs_stats_dir = args.obs_stats_dir or os.path.join(args.output_dir, "heuristic_logs")
        _obs_collector.save(_obs_stats_dir)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        import traceback
        traceback.print_exc()
    finally:
        try:
            simulation_app.close()
        except Exception:
            pass
