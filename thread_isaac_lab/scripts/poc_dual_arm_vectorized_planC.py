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
parser.add_argument("--grasp_close_steps", type=int, default=100,
                    help="Number of sim steps to close grippers (default: 100)")
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

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.scripts.camera_utils import estimate_target_from_cameras

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
FINGER_JOINT_Z_OFFSET = 0.0584  # panda_hand -> finger body origin along hand Z (URDF)
# finger body origin -> fingertip = FINGERTIP_OFFSET - FINGER_JOINT_Z_OFFSET = 0.0539m
FINGER_BODY_TO_TIP = FINGERTIP_OFFSET - FINGER_JOINT_Z_OFFSET  # 0.0539m
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
                                      fingers_vertical: bool = False) -> torch.Tensor:
    """Compute desired gripper quaternion so +Z points EE->ball.  (N,3) -> (N,4) wxyz.

    If fingers_vertical=True, the finger open/close direction (+X axis) is
    rotated toward world-Z (vertical), reducing table interference when
    approaching from the side at low heights.
    """
    N = ball_pos.shape[0]
    device = ball_pos.device

    desired_z = ball_pos - ee_pos  # (N, 3)
    nz = torch.norm(desired_z, dim=-1, keepdim=True).clamp(min=1e-8)
    desired_z = desired_z / nz

    if fingers_vertical:
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
                                                     fingers_vertical=fingers_vertical)  # (N, 4)
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
) -> dict:
    """Execute grasp sequence: close grippers → settle → lift → check cable.

    Returns dict with grasp results.
    """
    TABLE_Z = 0.75
    GRIP_SUCCESS_THRESHOLD = 0.0025  # 2.5mm — cable between fingers
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

    # Fine-positioning: closed-loop control targeting FINGERTIP position (Plan C)
    # Instead of static Z offset on grip_center, dynamically compute fingertip
    # from grip_center + finger_body_to_tip projected along hand Z-axis.
    _lf_idx = int(robot_left.find_bodies("panda_leftfinger")[0][0])
    _rf_idx = int(robot_left.find_bodies("panda_rightfinger")[0][0])

    no_ori = torch.zeros(1, dtype=torch.bool, device=device)

    # --- Measure finger_length at runtime (verify against URDF constant) ---
    # Project (finger_body_origin - hand_origin) onto hand Z-axis to get joint offset,
    # then finger_length = FINGERTIP_OFFSET - measured_joint_offset
    _hand_pos_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    _hand_quat_l = robot_left.data.body_quat_w[env_idx:env_idx+1, hand_body_left, :]  # (1,4)
    _finger_body_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
    _z_local = torch.zeros(1, 3, device=device)
    _z_local[0, 2] = 1.0
    _hand_z_l = quat_rotate_vec_batch(_hand_quat_l, _z_local)[0]  # (3,) hand Z in world
    _hand_to_finger = _finger_body_l - _hand_pos_l  # (3,)
    _measured_joint_offset = torch.dot(_hand_to_finger, _hand_z_l).item()
    _measured_finger_length = FINGERTIP_OFFSET - _measured_joint_offset
    print(f"[GRASP][PlanC] Finger geometry measurement:")
    print(f"[GRASP][PlanC]   URDF finger_joint_z_offset = {FINGER_JOINT_Z_OFFSET*1000:.1f}mm")
    print(f"[GRASP][PlanC]   Measured joint_offset      = {_measured_joint_offset*1000:.1f}mm")
    print(f"[GRASP][PlanC]   FINGER_BODY_TO_TIP (URDF)  = {FINGER_BODY_TO_TIP*1000:.1f}mm")
    print(f"[GRASP][PlanC]   Measured finger_length      = {_measured_finger_length*1000:.1f}mm")
    print(f"[GRASP][PlanC]   hand_Z_world_L = ({_hand_z_l[0].item():.4f},{_hand_z_l[1].item():.4f},{_hand_z_l[2].item():.4f})")
    # Use measured value (falls back to URDF constant if measurement is unreasonable)
    _finger_length = _measured_finger_length
    if abs(_finger_length - FINGER_BODY_TO_TIP) > 0.01:  # >10mm deviation = suspect
        print(f"[GRASP][PlanC] WARNING: measured finger_length deviates >10mm from URDF, using URDF constant")
        _finger_length = FINGER_BODY_TO_TIP

    # Cable target = actual cable position (NO static Z offset — fingertip targeting handles it)
    _cable_target_l = _seg_pos_l.to(device).clone()  # (3,) local frame — exact cable pos
    _cable_target_r = _seg_pos_r.to(device).clone()  # (3,) local frame
    _CONVERGE_THRESH = 0.003  # 3mm — well within cable radius (5mm)
    _IK_ALPHA = 20.0
    _IK_CLIP = 0.03
    _MAX_PASSES = 2  # pass 1: converge to target; pass 2: correct residual
    print(f"[GRASP][PlanC] Phase 2.5: Fingertip-targeted fine-positioning "
          f"(finger_length={_finger_length*1000:.1f}mm, "
          f"convergence={_CONVERGE_THRESH*1000:.0f}mm, passes={_MAX_PASSES})")

    _total_steps = 0
    _bias_correction_l = torch.zeros(3, device=device)
    _bias_correction_r = torch.zeros(3, device=device)
    for _pass in range(_MAX_PASSES):
        if _pass == 0:
            _bias_correction_l.zero_()
            _bias_correction_r.zero_()
        else:
            # Pass 2: measure residual (fingertip vs cable) and correct
            _lf_l = robot_left.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_l = robot_left.data.body_pos_w[env_idx, _rf_idx, :3]
            _lf_r = robot_right.data.body_pos_w[env_idx, _lf_idx, :3]
            _rf_r = robot_right.data.body_pos_w[env_idx, _rf_idx, :3]
            _gc_l = (_lf_l + _rf_l) / 2.0
            _gc_r = (_lf_r + _rf_r) / 2.0
            # Get current hand Z-axes
            _hq_l = robot_left.data.body_quat_w[env_idx:env_idx+1, hand_body_left, :]
            _hq_r = robot_right.data.body_quat_w[env_idx:env_idx+1, hand_body_right, :]
            _hz_l = quat_rotate_vec_batch(_hq_l, _z_local)[0]
            _hz_r = quat_rotate_vec_batch(_hq_r, _z_local)[0]
            _ft_est_l = _gc_l + _finger_length * _hz_l
            _ft_est_r = _gc_r + _finger_length * _hz_r
            _residual_l = _ft_est_l - _cable_target_l  # fingertip - cable = bias
            _residual_r = _ft_est_r - _cable_target_r
            _residual_mag_l = torch.norm(_residual_l).item()
            _residual_mag_r = torch.norm(_residual_r).item()
            if _residual_mag_l < _CONVERGE_THRESH and _residual_mag_r < _CONVERGE_THRESH:
                print(f"[GRASP][PlanC] Pass 1 fingertip already within {_CONVERGE_THRESH*1000:.0f}mm, skipping pass 2")
                break
            _bias_correction_l = _residual_l.clone()
            _bias_correction_r = _residual_r.clone()
            print(f"[GRASP][PlanC] Pass 2: fingertip residual "
                  f"L=({_residual_l[0].item()*1000:.1f},{_residual_l[1].item()*1000:.1f},{_residual_l[2].item()*1000:.1f})mm "
                  f"R=({_residual_r[0].item()*1000:.1f},{_residual_r[1].item()*1000:.1f},{_residual_r[2].item()*1000:.1f})mm")

        _pass_steps = 150 if _pass == 0 else 100
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

            # Compute hand Z-axis in world frame (direction from hand toward fingertip)
            _hq_l = robot_left.data.body_quat_w[env_idx:env_idx+1, hand_body_left, :]
            _hq_r = robot_right.data.body_quat_w[env_idx:env_idx+1, hand_body_right, :]
            _hz_l = quat_rotate_vec_batch(_hq_l, _z_local)[0]  # (3,)
            _hz_r = quat_rotate_vec_batch(_hq_r, _z_local)[0]  # (3,)

            # Estimated fingertip = grip_center + finger_length * hand_Z_world
            _fingertip_l = _grip_center_l + _finger_length * _hz_l
            _fingertip_r = _grip_center_r + _finger_length * _hz_r

            # Error = cable_target - fingertip - bias_correction
            # Pass 1: bias=0 → err = cable - fingertip
            # Pass 2: bias = (fingertip_end_pass1 - cable) → doubles correction to cancel IK bias
            _err_l = _cable_target_l - _fingertip_l - _bias_correction_l
            _err_r = _cable_target_r - _fingertip_r - _bias_correction_r
            _err_mag_l = torch.norm(_err_l).item()
            _err_mag_r = torch.norm(_err_r).item()

            # Measure fingertip-to-cable distance (primary metric for Plan C)
            _ft2cable_l = torch.norm(_fingertip_l - _cable_target_l).item()
            _ft2cable_r = torch.norm(_fingertip_r - _cable_target_r).item()
            _ft2cable_z_l = (_fingertip_l[2] - _cable_target_l[2]).item()
            _ft2cable_z_r = (_fingertip_r[2] - _cable_target_r[2]).item()

            if step % 20 == 0:
                print(f"[GRASP][PlanC] pass{_pass+1} step={step} "
                      f"ft_L=({_fingertip_l[0].item():.4f},{_fingertip_l[1].item():.4f},{_fingertip_l[2].item():.4f}) "
                      f"ft_R=({_fingertip_r[0].item():.4f},{_fingertip_r[1].item():.4f},{_fingertip_r[2].item():.4f}) "
                      f"ft2cable_L={_ft2cable_l*1000:.1f}mm(dZ={_ft2cable_z_l*1000:+.1f}mm) "
                      f"ft2cable_R={_ft2cable_r*1000:.1f}mm(dZ={_ft2cable_z_r*1000:+.1f}mm) "
                      f"err_L={_err_mag_l*1000:.1f}mm err_R={_err_mag_r*1000:.1f}mm")

            if _err_mag_l < _CONVERGE_THRESH and _err_mag_r < _CONVERGE_THRESH:
                print(f"[GRASP][PlanC] Pass {_pass+1} converged at step {step}: "
                      f"ft2cable_L={_ft2cable_l*1000:.1f}mm(dZ={_ft2cable_z_l*1000:+.1f}mm) "
                      f"ft2cable_R={_ft2cable_r*1000:.1f}mm(dZ={_ft2cable_z_r*1000:+.1f}mm)")
                break

            # Move EE by the fingertip error (clamped to avoid large jumps)
            _clamp = 0.01  # max 10mm per step
            _delta_l = torch.clamp(_err_l, -_clamp, _clamp)
            _delta_r = torch.clamp(_err_r, -_clamp, _clamp)

            ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
            _ee_tgt_l = ee_cur_l + _delta_l.unsqueeze(0)
            _ee_tgt_r = ee_cur_r + _delta_r.unsqueeze(0)

            ik_l, nan_l = jt_ik_step_6dof_batch(
                robot_left, jac_body_left, hand_body_left,
                _ee_tgt_l, _ee_tgt_l, no_ori,
                _IK_ALPHA, 0.0, 999.0, _IK_CLIP, device,
            )
            ik_r, nan_r = jt_ik_step_6dof_batch(
                robot_right, jac_body_right, hand_body_right,
                _ee_tgt_r, _ee_tgt_r, no_ori,
                _IK_ALPHA, 0.0, 999.0, _IK_CLIP, device,
            )
            if nan_l.any() or nan_r.any():
                print(f"[GRASP][PlanC] IK NaN at pass {_pass+1} step {step}")
                break

            tgt_l = robot_left.data.joint_pos.clone()
            tgt_l[:, :7] = ik_l
            tgt_l[:, 7] = GRIPPER_OPEN
            tgt_l[:, 8] = GRIPPER_OPEN
            robot_left.set_joint_position_target(tgt_l)
            robot_left.write_data_to_sim()
            tgt_r = robot_right.data.joint_pos.clone()
            tgt_r[:, :7] = ik_r
            tgt_r[:, 7] = GRIPPER_OPEN
            tgt_r[:, 8] = GRIPPER_OPEN
            robot_right.set_joint_position_target(tgt_r)
            robot_right.write_data_to_sim()

            for _ in range(4):
                sim.step()
                scene.update(sim.get_physics_dt())

            if torch.isnan(cable.data.body_pos_w).any():
                print(f"[GRASP][PlanC] Cable NaN at pass {_pass+1} step {step}!")
                results["nan_detected"] = True
                return results

            _total_steps += 1

    results["fine_position_steps"] = _total_steps

    # Settle after fine-positioning
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

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
    print(f"[GRASP]   Left arm  ft(ee+offset)=({_ft_pre_l[0,0].item():.4f},{_ft_pre_l[0,1].item():.4f},{_ft_pre_l[0,2].item():.4f})")
    print(f"[GRASP]   Left arm  leftfinger= ({_lf_pos_l[0].item():.4f},{_lf_pos_l[1].item():.4f},{_lf_pos_l[2].item():.4f})")
    print(f"[GRASP]   Left arm  rightfinger=({_rf_pos_l[0].item():.4f},{_rf_pos_l[1].item():.4f},{_rf_pos_l[2].item():.4f})")
    # Plan C: fingertip from grip_center + finger_length * hand_Z
    _gc_diag_l = (_lf_pos_l + _rf_pos_l) / 2.0
    _hz_diag_l = quat_rotate_vec_batch(_q_l, _z_local)[0]
    _ft_planc_l = _gc_diag_l + _finger_length * _hz_diag_l
    print(f"[GRASP]   Left arm  ft(PlanC)    =({_ft_planc_l[0].item():.4f},{_ft_planc_l[1].item():.4f},{_ft_planc_l[2].item():.4f})")
    print(f"[GRASP]   Right arm ft(ee+offset)=({_ft_pre_r[0,0].item():.4f},{_ft_pre_r[0,1].item():.4f},{_ft_pre_r[0,2].item():.4f})")
    print(f"[GRASP]   Right arm leftfinger= ({_lf_pos_r[0].item():.4f},{_lf_pos_r[1].item():.4f},{_lf_pos_r[2].item():.4f})")
    print(f"[GRASP]   Right arm rightfinger=({_rf_pos_r[0].item():.4f},{_rf_pos_r[1].item():.4f},{_rf_pos_r[2].item():.4f})")
    _gc_diag_r = (_lf_pos_r + _rf_pos_r) / 2.0
    _hz_diag_r = quat_rotate_vec_batch(_q_r, _z_local)[0]
    _ft_planc_r = _gc_diag_r + _finger_length * _hz_diag_r
    print(f"[GRASP]   Right arm ft(PlanC)    =({_ft_planc_r[0].item():.4f},{_ft_planc_r[1].item():.4f},{_ft_planc_r[2].item():.4f})")
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

    # Phase 2.6 (wrist rotation) removed — rotating joint7 to reduce |Y| caused |Z|
    # to spike (fingers tilt vertically), making grip worse. Original orientation has
    # dominant X component (~0.87) which is adequate for cable grip.

    # --- Phase 3: Simple linear close (NO IK during close) ---
    # Tests v8j/v8k showed that cable-tracking IK during close interferes with
    # finger closing (wrist moves → transient forces → fingers bounce back).
    # This version uses a simple linear ramp with NO arm IK during close.
    _SIM_SUBSTEPS_CLOSE = 4
    grip_step = (GRIPPER_OPEN - GRIPPER_CLOSE) / close_steps
    grip_val = GRIPPER_OPEN
    print(f"[GRASP] Phase 3: SIMPLE LINEAR close ({GRIPPER_OPEN:.3f} -> {GRIPPER_CLOSE:.3f}) "
          f"over {close_steps} steps x{_SIM_SUBSTEPS_CLOSE} substeps, NO IK tracking")

    for step in range(close_steps):
        if STOP_REQUESTED:
            break
        grip_val = max(grip_val - grip_step, GRIPPER_CLOSE)

        # Just close grippers — no arm movement
        set_gripper_width(robot_left, grip_val, device)
        set_gripper_width(robot_right, grip_val, device)

        for _ in range(_SIM_SUBSTEPS_CLOSE):
            sim.step()
            scene.update(sim.get_physics_dt())

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
            print(f"[GRASP] close step={step}/{close_steps} "
                  f"cmd={grip_val:.4f} actual_L={_actual_l7:.4f} actual_R={_actual_r7:.4f} "
                  f"F_L={_force_l:.1f}N F_R={_force_r:.1f}N "
                  f"gap_L={_finger_gap_l*1000:.1f}mm gap_R={_finger_gap_r*1000:.1f}mm "
                  f"gc2cable_L={_gc2c_l*1000:.1f}mm gc2cable_R={_gc2c_r*1000:.1f}mm")

    results["gripper_closed"] = True
    results["close_steps_used"] = close_steps

    # --- Settle with maintained gripper target (100 steps) ---
    print("[GRASP] Settling after close (100 steps, maintaining close target)")
    for _ in range(100):
        set_gripper_width(robot_left, GRIPPER_CLOSE, device)
        set_gripper_width(robot_right, GRIPPER_CLOSE, device)
        sim.step()
        scene.update(sim.get_physics_dt())

    _grip_l = float(robot_left.data.joint_pos[env_idx, 7].item())
    _grip_r = float(robot_right.data.joint_pos[env_idx, 7].item())
    _grip_l_both = float(robot_left.data.joint_pos[env_idx, 7].item() +
                         robot_left.data.joint_pos[env_idx, 8].item())
    _grip_r_both = float(robot_right.data.joint_pos[env_idx, 7].item() +
                         robot_right.data.joint_pos[env_idx, 8].item())
    print(f"[GRASP] Final grip: L_j7={_grip_l*1000:.1f}mm R_j7={_grip_r*1000:.1f}mm "
          f"L_total={_grip_l_both*1000:.1f}mm R_total={_grip_r_both*1000:.1f}mm")

    # --- DIAGNOSTIC: Force-write finger joints to 0.005 and check physics response ---
    _FORCE_GRIP = 0.005
    print(f"[DIAG] Force-writing finger joints to {_FORCE_GRIP*1000:.1f}mm per finger...")
    _pos_l = robot_left.data.joint_pos.clone()
    _pos_r = robot_right.data.joint_pos.clone()
    _vel_l = robot_left.data.joint_vel.clone() * 0
    _vel_r = robot_right.data.joint_vel.clone() * 0
    _pos_l[:, 7] = _FORCE_GRIP
    _pos_l[:, 8] = _FORCE_GRIP
    _pos_r[:, 7] = _FORCE_GRIP
    _pos_r[:, 8] = _FORCE_GRIP
    robot_left.write_joint_state_to_sim(_pos_l, _vel_l)
    robot_right.write_joint_state_to_sim(_pos_r, _vel_r)
    # Set targets too
    set_gripper_width(robot_left, _FORCE_GRIP, device)
    set_gripper_width(robot_right, _FORCE_GRIP, device)
    for _ in range(4):
        sim.step()
        scene.update(sim.get_physics_dt())
    _diag_l = robot_left.data.joint_pos[env_idx, 7].item()
    _diag_r = robot_right.data.joint_pos[env_idx, 7].item()
    print(f"[DIAG] After force-write+4steps: L_j7={_diag_l*1000:.1f}mm R_j7={_diag_r*1000:.1f}mm "
          f"(wrote {_FORCE_GRIP*1000:.1f}mm → physics pushed to L={_diag_l*1000:.1f}/R={_diag_r*1000:.1f})")
    # Let it settle 50 steps
    for _ in range(50):
        set_gripper_width(robot_left, _FORCE_GRIP, device)
        set_gripper_width(robot_right, _FORCE_GRIP, device)
        sim.step()
        scene.update(sim.get_physics_dt())
    _diag_l2 = robot_left.data.joint_pos[env_idx, 7].item()
    _diag_r2 = robot_right.data.joint_pos[env_idx, 7].item()
    print(f"[DIAG] After 50 more settle: L_j7={_diag_l2*1000:.1f}mm R_j7={_diag_r2*1000:.1f}mm")

    # --- Grip success check ---
    # Use total grip (both fingers) for success: cable diameter ~10mm → total gap should be ~10mm
    # Success: total grip width between GRIP_SUCCESS_THRESHOLD*2 and cable_diameter + margin
    _CABLE_DIAMETER = 0.010  # 10mm
    _GRIP_MAX_FOR_SUCCESS = _CABLE_DIAMETER + 0.010  # 20mm total max (cable + 5mm each side)
    results["grip_width_left"] = _grip_l
    results["grip_width_right"] = _grip_r
    results["grip_total_left"] = _grip_l_both
    results["grip_total_right"] = _grip_r_both
    # Per-finger check: finger should be stopped by cable at ~cable_radius (5mm)
    grip_success_l = _grip_l > GRIP_SUCCESS_THRESHOLD and _grip_l_both < _GRIP_MAX_FOR_SUCCESS
    grip_success_r = _grip_r > GRIP_SUCCESS_THRESHOLD and _grip_r_both < _GRIP_MAX_FOR_SUCCESS
    results["grip_success_left"] = grip_success_l
    results["grip_success_right"] = grip_success_r

    if not grip_success_l or not grip_success_r:
        _fail_reasons = []
        if not grip_success_l:
            if _grip_l <= GRIP_SUCCESS_THRESHOLD:
                _fail_reasons.append(f"left_j7={_grip_l*1000:.1f}mm<{GRIP_SUCCESS_THRESHOLD*1000:.1f}mm")
            elif _grip_l_both >= _GRIP_MAX_FOR_SUCCESS:
                _fail_reasons.append(f"left_total={_grip_l_both*1000:.1f}mm>{_GRIP_MAX_FOR_SUCCESS*1000:.0f}mm(fingers not contacting cable)")
        if not grip_success_r:
            if _grip_r <= GRIP_SUCCESS_THRESHOLD:
                _fail_reasons.append(f"right_j7={_grip_r*1000:.1f}mm<{GRIP_SUCCESS_THRESHOLD*1000:.1f}mm")
            elif _grip_r_both >= _GRIP_MAX_FOR_SUCCESS:
                _fail_reasons.append(f"right_total={_grip_r_both*1000:.1f}mm>{_GRIP_MAX_FOR_SUCCESS*1000:.0f}mm(fingers not contacting cable)")
        results["grip_failed_reason"] = ", ".join(_fail_reasons)
        print(f"[GRASP] Grip FAILED: {results['grip_failed_reason']} — skipping lift")
        return results

    print(f"[GRASP] Grip SUCCESS: L_total={_grip_l_both*1000:.1f}mm R_total={_grip_r_both*1000:.1f}mm "
          f"(cable ~{_CABLE_DIAMETER*1000:.0f}mm, max={_GRIP_MAX_FOR_SUCCESS*1000:.0f}mm)")

    # --- Phase 4: Lift ---
    print(f"[GRASP] Phase 4: Lifting Z by +{lift_z}m")
    # hand_body_left/right, jac_body_left/right already computed in Phase 2.5

    lift_steps = 100  # 100 sim steps for lift
    for step in range(lift_steps):
        if STOP_REQUESTED:
            break

        # Incrementally raise Z target
        z_increment = lift_z / lift_steps
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_r = robot_right.data.joint_pos.clone()
        # Keep grip closed
        tgt_l[:, 7] = GRIPPER_CLOSE
        tgt_l[:, 8] = GRIPPER_CLOSE
        tgt_r[:, 7] = GRIPPER_CLOSE
        tgt_r[:, 8] = GRIPPER_CLOSE
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if torch.isnan(cable.data.body_pos_w).any():
            print(f"[GRASP] Cable NaN at lift step {step}!")
            results["nan_detected"] = True
            return results

    # Actually lift using IK: compute new EE target Z
    ee_pos_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
    ee_pos_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
    ee_target_l = ee_pos_l.clone()
    ee_target_r = ee_pos_r.clone()
    ee_target_l[:, 2] += lift_z
    ee_target_r[:, 2] += lift_z

    # is_fixed_*, jac_body_*, no_ori already computed in Phase 2.5

    print(f"[GRASP] Lifting with IK: target Z delta=+{lift_z}m")
    for step in range(200):  # 200 macro steps for lift
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

        # Apply joints but keep gripper closed
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[:, :7] = ik_l
        tgt_l[:, 7] = GRIPPER_CLOSE
        tgt_l[:, 8] = GRIPPER_CLOSE
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[:, :7] = ik_r
        tgt_r[:, 7] = GRIPPER_CLOSE
        tgt_r[:, 8] = GRIPPER_CLOSE
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        for _ in range(4):
            sim.step()
            scene.update(sim.get_physics_dt())

        if torch.isnan(cable.data.body_pos_w).any():
            print(f"[GRASP] Cable NaN at lift IK step {step}!")
            results["nan_detected"] = True
            return results

        # Check convergence
        ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
        z_err_l = abs(ee_cur_l[0, 2].item() - ee_target_l[0, 2].item())
        z_err_r = abs(ee_cur_r[0, 2].item() - ee_target_r[0, 2].item())
        if step % 50 == 0:
            print(f"[GRASP] lift step={step} z_err_L={z_err_l:.4f} z_err_R={z_err_r:.4f}")
        if z_err_l < 0.01 and z_err_r < 0.01:
            print(f"[GRASP] Lift converged at step {step}")
            break

    results["lift_steps_used"] = step + 1

    # --- Settle after lift ---
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

    # --- Check cable Z after lift ---
    cable_z_after = cable.data.body_pos_w[env_idx, :, 2].clone()
    results["cable_z_after"] = cable_z_after.cpu().tolist()
    z_delta = (cable_z_after - cable_z_before).mean().item()
    results["cable_z_delta"] = z_delta

    # Success: cable lifted above table (any segment lifted > 1cm average)
    results["cable_lifted"] = z_delta > 0.01  # at least 1cm average lift

    print(f"[GRASP] Cable Z after:  mean={cable_z_after.mean().item():.4f}m "
          f"min={cable_z_after.min().item():.4f}m max={cable_z_after.max().item():.4f}m")
    print(f"[GRASP] Cable Z delta:  mean={z_delta:.4f}m "
          f"({'LIFTED' if results['cable_lifted'] else 'NOT LIFTED'})")

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

    phase = torch.zeros(N, dtype=torch.int32, device=device)  # 0=XY position, 1=Z descent, 2=done
    # No orientation control during overhead descent (handled in grasp alignment phase)
    ori_enable = torch.zeros(N, dtype=torch.bool, device=device)
    _cable_ori_alpha = 0.0
    _cable_ori_dist = 999.0

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
                phase[:] = 1
                stats["phase1_macros"] = macro + 1
                print(f"[OVERHEAD] Phase 1 done at macro={macro}, starting Z descent")
                # Update overhead targets to include descent Z
                overhead_left[:, 2] = descent_z
                overhead_right[:, 2] = descent_z
                # Record cable reference Z at start of descent
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
                print(f"[OVERHEAD] Ph2 macro={macro} "
                      f"ft_z_L={ft_left[0, 2].item():.4f} ft_z_R={ft_right[0, 2].item():.4f} "
                      f"z_err_L={z_err_left[0].item():.4f} z_err_R={z_err_right[0].item():.4f} "
                      f"conv={converged.sum().item()}/{N}")

            if converged.all():
                phase[:] = 2
                stats["phase2_macros"] = macro + 1 - stats["phase1_macros"]
                print(f"[OVERHEAD] Phase 2 done at macro={macro}, descent complete")
                break

        else:
            break  # phase 2 done

        # Convert FT targets to EE targets
        ee_target_left = fingertip_to_ee_batch(ft_target_left, ee_quat_left)
        ee_target_right = fingertip_to_ee_batch(ft_target_right, ee_quat_right)

        # IK inner loop (position-only during overhead)
        for _ in range(hold_steps):
            if STOP_REQUESTED:
                break
            ik_left, nan_left = jt_ik_step_6dof_batch(
                robot_left, jacobian_body_left, hand_body_left,
                ee_target_left, ball, ori_enable,
                jt_alpha, _cable_ori_alpha, _cable_ori_dist,
                clip_rad, device,
            )
            ik_right, nan_right = jt_ik_step_6dof_batch(
                robot_right, jacobian_body_right, hand_body_right,
                ee_target_right, ball, ori_enable,
                jt_alpha, _cable_ori_alpha, _cable_ori_dist,
                clip_rad, device,
            )
            apply_mask = torch.ones(N, dtype=torch.bool, device=device)
            apply_joints_batch(robot_left, ik_left, apply_mask & (~nan_left))
            apply_joints_batch(robot_right, ik_right, apply_mask & (~nan_right))
            sim.step()
            scene.update(sim.get_physics_dt())

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

    _sim_device = f"cuda:{app_launcher.device_id}"
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, render_interval=2, device=_sim_device)
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

        # Pick per-arm cable segments: left arm → Y<0 segment, right arm → Y>0 segment
        # Target Y positions: ±0.04 from center for moderate spacing
        _left_target_y = -0.04  # Y- side for left arm
        _right_target_y = +0.04  # Y+ side for right arm
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
            xy_converge_m=0.05,
            z_converge_m=0.02,
            max_macros=200,
            hold_steps=args.hold_steps,
            jt_alpha=args.jt_alpha,
            clip_rad=args.clip_rad,
            table_z_min=_descent_z_min,
            cable=_cable if args.grasp else None,
            left_ft_override=env_state.left_ft_target[0] if args.grasp and _cable is not None else None,
            right_ft_override=env_state.right_ft_target[0] if args.grasp and _cable is not None else None,
        )
        print(f"[VEC] Overhead descent done: {overhead_stats}")

    # --- Video setup ---
    video_frame_idx = 0
    frames_dir = ""
    video_out = ""
    if args.save_video:
        frames_dir = os.path.join(args.output_dir, "video_frames")
        video_out = os.path.join(args.output_dir, "video.mp4")
        os.makedirs(frames_dir, exist_ok=True)
        print(f"[VEC] Video: {video_out} ({args.video_fps} fps)")

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
                        _grasp_res = grasp_and_lift_sequence(
                            robot_left, robot_right, sim, scene, device,
                            _cable, args.grasp_close_steps, args.grasp_lift_z,
                            cable_pos_before_reaching=_cable_pos_before_reaching,
                            env_origin=_env_origins[i],
                            env_idx=i,
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
                    xy_converge_m=0.05,
                    z_converge_m=0.02,
                    max_macros=200,
                    hold_steps=args.hold_steps,
                    jt_alpha=args.jt_alpha,
                    clip_rad=args.clip_rad,
                    table_z_min=_descent_z_min,
                    cable=_cable if args.grasp else None,
                    left_ft_override=env_state.left_ft_target[0] if args.grasp and _cable is not None else None,
                    right_ft_override=env_state.right_ft_target[0] if args.grasp and _cable is not None else None,
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
            try:
                images = get_four_camera_images(scene, sim)
                if images:
                    sheet = build_contact_sheet(images, resolution=args.contact_sheet_res)
                    sheet.save(os.path.join(frames_dir, f"frame_{video_frame_idx:06d}.png"))
                    video_frame_idx += 1
            except Exception as e:
                if video_frame_idx == 0:
                    print(f"[VEC] Video frame capture failed: {e}")

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
