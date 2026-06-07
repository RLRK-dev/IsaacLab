#!/usr/bin/env python3
"""
Goal Image Collection Script

Execute cable manipulation (grasp and drape on hook) and
capture goal images for each task phase.

Usage:
    python thread_isaac_lab/scripts/collect_goal_images.py \
        --device cuda:0 --headless --enable_cameras

    # GUI mode for visualization
    python thread_isaac_lab/scripts/collect_goal_images.py \
        --device cuda:0 --enable_cameras
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Collect Goal Images with Cable Manipulation")
parser.add_argument("--output_dir", type=str, default="data/goal_images", help="Output directory")
parser.add_argument("--skip_d6_joints", action="store_true", help="Skip D6 joint creation (use friction grasp only)")
parser.add_argument("--realtime_log_dir", type=str, default=None, help="Directory for realtime camera image logging (saves latest.png every 2s)")
parser.add_argument("--debug_mode", action="store_true", help="Enable debug mode with verbose output")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os
import torch
import numpy as np
import threading
import time
from PIL import Image
from datetime import datetime
from typing import Dict, Tuple, Optional
from enum import Enum
from scipy.spatial.transform import Rotation as R

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT
from configs.task_config import (
    GRASP_INWARD_OFFSET,
    GRIPPER_OPEN,
    GRIPPER_CLOSED,
    GRASP_DISTANCE_THRESHOLD,
)
from utils.d6_grasp_manager import D6GraspManager

# Cable segment indices (20-segment articulated cable)
# X-axis cable layout (SphericalJoint v5 with rigid body damping)
# NOTE: Articulation structure creates branching pattern, NOT linear ordering
# seg_0 is root (near center X=0.22)
# Actual physical positions (verified from simulation):
#   seg_17: X=0.477 (right end along X, MAX X)
#   seg_19: X=-0.068 (left end along X, MIN X)
# Plan B: Y-axis cable layout
# seg_17 is at min Y (left end), seg_19 is at max Y (right end)
CABLE_BASE_IDX = 17  # "Left" gripper target (MIN Y, left end)
CABLE_TIP_IDX = 19   # "Right" gripper target (MAX Y, right end)

# Grasp offset: move grippers 3cm inward from cable ends for stable grasping
# Cable is along Y-axis: seg_17 at min Y (left), seg_19 at max Y (right)
# Inward offset is applied along Y-axis toward cable center
# GRASP_INWARD_OFFSET imported from task_config.py (SSOT: 0.0, was hardcoded 0.03)


# =============================================================================
# NaN Detection Utilities
# =============================================================================

def check_tensor_nan(tensor: torch.Tensor, name: str = "tensor") -> bool:
    """
    Check if tensor contains NaN values.

    Args:
        tensor: Tensor to check
        name: Name for error message

    Returns:
        True if NaN detected, False otherwise
    """
    if tensor is None:
        return False
    if torch.isnan(tensor).any():
        print(f"[NaN ERROR] {name} contains NaN values!")
        print(f"  Shape: {tensor.shape}")
        print(f"  NaN count: {torch.isnan(tensor).sum().item()}")
        return True
    return False


def check_cable_nan(cable_positions: torch.Tensor) -> bool:
    """
    Check if cable segment positions contain NaN.

    Args:
        cable_positions: Cable segment positions tensor

    Returns:
        True if NaN detected (simulation unstable)
    """
    if check_tensor_nan(cable_positions, "cable_positions"):
        print("[CRITICAL] Cable physics state is corrupted (NaN detected)")
        print("  Possible causes:")
        print("    1. Cable position too close to table edge")
        print("    2. Physics simulation instability")
        print("    3. Collision detection failure")
        return True
    return False


class SimulationHealthChecker:
    """Monitor simulation health and detect NaN/instability."""

    def __init__(self, max_nan_warnings: int = 3):
        self.nan_count = 0
        self.max_nan_warnings = max_nan_warnings
        self.is_healthy = True

    def check(self, cable_pos: torch.Tensor, ee_left: torch.Tensor = None,
              ee_right: torch.Tensor = None) -> bool:
        """
        Check simulation health.

        Args:
            cable_pos: Cable segment positions
            ee_left: Left end effector position (optional)
            ee_right: Right end effector position (optional)

        Returns:
            True if healthy, False if should abort
        """
        nan_detected = False

        # Check cable
        if check_tensor_nan(cable_pos, "cable_positions"):
            nan_detected = True

        # Check end effectors if provided
        if ee_left is not None and check_tensor_nan(ee_left, "left_ee_pos"):
            nan_detected = True
        if ee_right is not None and check_tensor_nan(ee_right, "right_ee_pos"):
            nan_detected = True

        if nan_detected:
            self.nan_count += 1
            print(f"[WARNING] NaN detection count: {self.nan_count}/{self.max_nan_warnings}")

            if self.nan_count >= self.max_nan_warnings:
                print("[ABORT] Too many NaN detections. Simulation is unstable.")
                self.is_healthy = False
                return False

        return True

    def reset(self):
        """Reset health checker for new attempt."""
        self.nan_count = 0
        self.is_healthy = True


# =============================================================================
# Grasp Prim Paths
# =============================================================================

def get_gripper_prim_paths(env_idx: int = 0) -> Dict[str, str]:
    """Get gripper prim paths for D6GraspManager.

    Uses panda_hand instead of panda_leftfinger for better PhysX constraint stability.
    panda_leftfinger is a leaf link of the articulation which can cause issues with FixedJoints.

    Returns:
        Dict with left and right gripper paths
    """
    return {
        "left": f"/World/envs/env_{env_idx}/Robot_Left/panda_hand",
        "right": f"/World/envs/env_{env_idx}/Robot_Right/panda_hand",
    }


def get_cable_segment_prim_path(env_idx: int, seg_idx: int) -> str:
    """Get cable segment prim path.

    Args:
        env_idx: Environment index
        seg_idx: Segment index (0-9)

    Returns:
        USD prim path for the cable segment
    """
    return f"/World/envs/env_{env_idx}/Cable/seg_{seg_idx}"


# =============================================================================
# Task Phases
# =============================================================================

class TaskPhase(Enum):
    """6-phase simplified task state machine for cable transport.

    Simplified from 8-phase draping task to avoid D6 joint limitations during rotation.
    Focus on basic manipulation: reach, grasp, lift, transport, release.
    """
    REACH_CABLE = 1      # EE reaches cable ends
    GRASP_CABLE = 2      # Gripper grasps cable
    LIFT_CABLE = 3       # Cable lifted above table
    TRANSPORT = 4        # Transport cable to target position (replaces ROTATE)
    RELEASE = 5          # Gripper released
    DONE = 6             # Task complete


PHASE_DESCRIPTIONS = {
    TaskPhase.REACH_CABLE: "Both hands approach cable ends",
    TaskPhase.GRASP_CABLE: "Grippers grasp cable",
    TaskPhase.LIFT_CABLE: "Lift cable from table",
    TaskPhase.TRANSPORT: "Transport cable to target position",
    TaskPhase.RELEASE: "Release grippers",
    TaskPhase.DONE: "Task complete - retreat",
}


# =============================================================================
# Constants
# =============================================================================

# GRIPPER_OPEN, GRIPPER_CLOSED, GRASP_DISTANCE_THRESHOLD imported from task_config.py (SSOT)
# Previous hardcoded values: GRIPPER_OPEN=0.04, GRIPPER_CLOSED=0.002, GRASP_DISTANCE_THRESHOLD=0.05

# Grasp validation
# SphericalJoint v3 Y-axis cable layout - cable extends along Y axis
LEFT_CLAMP_SEGMENT = 17  # seg_17 = left end (Y min = -0.285), SphericalJoint v3
RIGHT_CLAMP_SEGMENT = 19 # seg_19 = right end (Y max = +0.285), SphericalJoint v3


# =============================================================================
# Dual Arm Controller
# =============================================================================


# =============================================================================
# Dual Arm Controller (DifferentialIK-based)
# =============================================================================


class DualArmController:
    """Controller for both arms using DifferentialIK."""

    def __init__(self, scene: InteractiveScene, device: str):
        self.scene = scene
        self.device = device

        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        # Resolve body and joint indices
        body_ids, _ = self.robot_left.find_bodies("panda_hand")
        self.ee_body_idx = body_ids[0]

        joint_ids, _ = self.robot_left.find_joints("panda_joint.*")
        self.arm_joint_ids = list(joint_ids)
        self.gripper_joint_ids = [7, 8]

        # Plan B: Y-axis cable layout
        # Cable runs along Y axis, so fingers must open along X axis (perpendicular)
        # X=180° makes gripper point down, Z=90° rotates fingers to open along X (perpendicular to Y-axis cable)
        from scipy.spatial.transform import Rotation as R
        final_rot = R.from_euler('xz', [180, 90], degrees=True)  # Z=90 for Y-axis cable
        quat_xyzw = final_rot.as_quat()  # scipy returns [x, y, z, w]
        quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
        print(f"[Controller] Gripper quaternion (wxyz): {quat_wxyz}")
        print(f"[Controller] Gripper orientation: pointing down, fingers perpendicular to Y-axis cable (Plan B)")
        self.default_quat = torch.tensor([quat_wxyz], device=device)

        # Initialize DifferentialIK controllers
        self._init_diff_ik_controllers()

        # Debug: Check actuator configuration
        print(f"[Controller] Left has_implicit_actuators: {self.robot_left._has_implicit_actuators}")
        print(f"[Controller] Right has_implicit_actuators: {self.robot_right._has_implicit_actuators}")
        print(f"[Controller] Left actuators: {list(self.robot_left.actuators.keys())}")

        # Debug: Print initial positions
        print(f"[Controller] Left arm joint pos: {self.robot_left.data.joint_pos[0, :7].cpu().tolist()}")
        print(f"[Controller] Right arm joint pos: {self.robot_right.data.joint_pos[0, :7].cpu().tolist()}")
        left_ee, _ = self.get_ee_pose(self.robot_left)
        right_ee, _ = self.get_ee_pose(self.robot_right)
        print(f"[Controller] Left EE (world): {left_ee[0].cpu().tolist()}")
        print(f"[Controller] Right EE (world): {right_ee[0].cpu().tolist()}")

    def _init_diff_ik_controllers(self):
        """Initialize DifferentialIK controllers for both arms."""
        # DifferentialIK configuration
        # command_type="pose" uses absolute world frame targets
        diff_ik_cfg = DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="dls",  # Damped Least Squares
            ik_params={"lambda_val": 0.01},  # Lower = more aggressive (ref CLAUDE.md)
        )

        # Create controllers for each arm - one per num_envs
        num_envs = 1  # Single environment
        self.left_ik = DifferentialIKController(diff_ik_cfg, num_envs=num_envs, device=self.device)
        self.right_ik = DifferentialIKController(diff_ik_cfg, num_envs=num_envs, device=self.device)

        # Get Jacobian body indices for EE frame
        self.ee_jacobi_idx = self.ee_body_idx - 1  # Jacobian is offset by 1 from body index

        # Joint limits for Franka Panda (radians) - used for clamping IK output
        # [panda_joint1, panda_joint2, ..., panda_joint7]
        self.joint_limits_lower = torch.tensor([
            [-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973]
        ], device=self.device)
        self.joint_limits_upper = torch.tensor([
            [2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973]
        ], device=self.device)

        print(f"[Controller] DifferentialIK controllers initialized")
        print(f"[Controller] EE body idx: {self.ee_body_idx}, Jacobian idx: {self.ee_jacobi_idx}")

    def get_ee_pose(self, robot) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get current EE position and quaternion in world frame."""
        ee_pos_w = robot.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat_w = robot.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos_w, ee_quat_w

    def get_fingertip_offset_world(self) -> float:
        """Get the Z offset from fingertip to panda_hand in world frame.

        When gripper points down, panda_hand is 10.7cm ABOVE the fingertip.
        To reach a fingertip target, panda_hand should be 10.7cm higher.
        """
        return 0.1123  # panda_hand is 10.7cm above fingertip when pointing down

    def set_targets(
        self,
        left_pos: Optional[torch.Tensor],
        right_pos: Optional[torch.Tensor],
        left_gripper: float,
        right_gripper: float,
        debug: bool = False,
        use_fixed_orientation: bool = False,
    ):
        """Set arm targets and gripper positions using DifferentialIK."""

        # Get target orientation
        target_quat = self.default_quat if use_fixed_orientation else None

        # Left arm
        if left_pos is not None:
            left_target = self._compute_diff_ik(
                self.robot_left, self.left_ik, left_pos, target_quat, debug
            )
        else:
            left_target = self.robot_left.data.joint_pos[:, self.arm_joint_ids]

        # Right arm
        if right_pos is not None:
            right_target = self._compute_diff_ik(
                self.robot_right, self.right_ik, right_pos, target_quat, debug
            )
        else:
            right_target = self.robot_right.data.joint_pos[:, self.arm_joint_ids]

        # Gripper positions
        left_grip = torch.full((1, 2), left_gripper, device=self.device)
        right_grip = torch.full((1, 2), right_gripper, device=self.device)

        # Set joint position targets
        self.robot_left.set_joint_position_target(torch.cat([left_target, left_grip], dim=-1))
        self.robot_right.set_joint_position_target(torch.cat([right_target, right_grip], dim=-1))

        # CRITICAL: Explicitly write targets to sim (like test_arm_reachability.py)
        # This ensures PhysX receives the position targets before sim.step()
        self.robot_left.write_data_to_sim()
        self.robot_right.write_data_to_sim()

        if debug:
            # Verify targets were set correctly
            print(f"      [Debug] Left joint_pos_target after set: {self.robot_left.data.joint_pos_target[0, :7].cpu().tolist()}")
            print(f"      [Debug] Left _joint_pos_target_sim: {self.robot_left._joint_pos_target_sim[0, :7].cpu().tolist()}")

    def _compute_diff_ik(
        self,
        robot,
        ik_controller: DifferentialIKController,
        target_pos: torch.Tensor,
        target_quat: Optional[torch.Tensor] = None,
        debug: bool = False,
    ) -> torch.Tensor:
        """Compute joint positions using DifferentialIK."""

        # Build command tensor: [pos_x, pos_y, pos_z, quat_w, quat_x, quat_y, quat_z]
        if target_quat is None:
            # Use current orientation
            _, current_quat = self.get_ee_pose(robot)
            target_quat = current_quat

        # Ensure tensors have correct shape: (num_envs, dim)
        if target_pos.dim() == 1:
            target_pos = target_pos.unsqueeze(0)  # (3,) -> (1, 3)
        if target_quat.dim() == 1:
            target_quat = target_quat.unsqueeze(0)  # (4,) -> (1, 4)

        # Command format: [pos(3), quat_wxyz(4)] -> shape (1, 7)
        command = torch.cat([target_pos, target_quat], dim=-1)

        # Set command
        ik_controller.set_command(command)

        # Get current joint positions and Jacobian from the robot
        current_joint_pos = robot.data.joint_pos[:, self.arm_joint_ids]
        ee_pos, ee_quat = self.get_ee_pose(robot)
        jacobian = robot.root_physx_view.get_jacobians()[:, self.ee_jacobi_idx, :, self.arm_joint_ids]

        # Compute IK
        joint_pos_target = ik_controller.compute(ee_pos, ee_quat, jacobian, current_joint_pos)

        # Clamp IK output to joint limits to prevent invalid targets
        joint_pos_clamped = torch.clamp(
            joint_pos_target,
            min=self.joint_limits_lower,
            max=self.joint_limits_upper
        )

        if debug:
            pos_error = torch.norm(ee_pos - target_pos).item()
            print(f"      [DiffIK Debug] Position error: {pos_error:.4f}m")
            print(f"      [DiffIK Debug] EE pos: {ee_pos[0].cpu().tolist()}")
            print(f"      [DiffIK Debug] Target pos: {target_pos[0].cpu().tolist()}")
            print(f"      [DiffIK Debug] Current joints: {current_joint_pos[0].cpu().tolist()}")
            print(f"      [DiffIK Debug] IK raw output: {joint_pos_target[0].cpu().tolist()}")
            print(f"      [DiffIK Debug] IK clamped: {joint_pos_clamped[0].cpu().tolist()}")

        return joint_pos_clamped

    def get_gripper_pos(self, robot) -> float:
        """Get current gripper position."""
        return robot.data.joint_pos[:, self.gripper_joint_ids].mean().item()

    def move_to_position_interpolated(
        self,
        left_target: torch.Tensor,
        right_target: torch.Tensor,
        left_gripper: float,
        right_gripper: float,
        sim,
        scene,
        num_steps: int = 30,
        steps_per_target: int = 5,
        use_fixed_orientation: bool = True,
        debug: bool = False,
    ):
        """
        Smoothly move to target positions using interpolation.

        Args:
            left_target: Left arm target EE position (3,)
            right_target: Right arm target EE position (3,)
            left_gripper: Left gripper open/close value
            right_gripper: Right gripper open/close value
            sim: Simulation context
            scene: Scene
            num_steps: Number of interpolation steps (position subdivisions)
            steps_per_target: Simulation steps per interpolated position
            use_fixed_orientation: Whether to use fixed orientation
            debug: Enable debug output
        """
        # Get current EE positions
        left_current, _ = self.get_ee_pose(self.robot_left)
        right_current, _ = self.get_ee_pose(self.robot_right)
        left_current = left_current[0].clone()  # (1, 3) → (3,)
        right_current = right_current[0].clone()

        # Verify target shape
        if left_target.dim() == 2:
            left_target = left_target[0]
        if right_target.dim() == 2:
            right_target = right_target[0]

        if debug:
            print(f"[Interpolated Move] Start: Left={left_current.cpu().numpy()}, Right={right_current.cpu().numpy()}")
            print(f"[Interpolated Move] Target: Left={left_target.cpu().numpy()}, Right={right_target.cpu().numpy()}")
            print(f"[Interpolated Move] Steps: {num_steps}, Steps per target: {steps_per_target}")

        # Interpolation
        for i in range(1, num_steps + 1):
            t = i / num_steps  # 0.0 → 1.0

            # Linear interpolation
            left_interp = left_current * (1 - t) + left_target * t
            right_interp = right_current * (1 - t) + right_target * t

            # Compute target joint angles via IK
            self.set_targets(
                left_interp.unsqueeze(0),
                right_interp.unsqueeze(0),
                left_gripper,
                right_gripper,
                debug=False,
                use_fixed_orientation=use_fixed_orientation,
            )

            # Simulation steps
            for _ in range(steps_per_target):
                sim.step()
                scene.update(sim.get_physics_dt())

        # Verify final position
        left_final, _ = self.get_ee_pose(self.robot_left)
        right_final, _ = self.get_ee_pose(self.robot_right)
        left_error = torch.norm(left_final[0] - left_target).item()
        right_error = torch.norm(right_final[0] - right_target).item()

        if debug:
            print(f"[Interpolated Move] Final error: Left={left_error*100:.2f}cm, Right={right_error*100:.2f}cm")

        return left_error, right_error


class GoalImageCollector:
    """Collects goal images by executing cable manipulation."""

    def __init__(self, scene: InteractiveScene, sim, output_dir: str, skip_d6_joints: bool = False, realtime_log_dir: str = None):
        self.scene = scene
        self.sim = sim
        self.output_dir = output_dir
        self.device = scene["robot_left"].device
        self.skip_d6_joints = skip_d6_joints
        self.realtime_log_dir = realtime_log_dir
        self.realtime_logger = None

        os.makedirs(output_dir, exist_ok=True)

        self.controller = DualArmController(scene, self.device)

        self.cameras = {
            'front_left': scene["front_left_camera"],
            'front_right': scene["front_right_camera"],
            'back': scene["back_camera"],
        }
        self.overhead = scene["overhead_camera"]

        # Get hook and cable references
        self.hook = scene["hook_stem"]
        self.cable = scene["cable"]

        # Initialize D6 grasp manager (joint-based, more stable than force-based)
        self.grasp_manager = D6GraspManager()
        # Note: set_stage() will be called after sim.reset() in main()

        # Gripper paths for D6 joint creation
        self.gripper_paths = get_gripper_prim_paths(env_idx=0)

        # Get initial positions
        self.hook_pos = self.hook.data.root_pos_w[0].clone()
        self.hook_v_pos = self.hook_pos.clone()
        self.hook_v_pos[2] += 0.07  # V part is 7cm above stem base

        print(f"[Collector] Hook position: {self.hook_pos.cpu().tolist()}")
        print(f"[Collector] Hook V position: {self.hook_v_pos.cpu().tolist()}")

        # Initialize simulation health checker for NaN detection
        self.health_checker = SimulationHealthChecker(max_nan_warnings=3)

    def step_sim(self, steps: int = 1):
        """Step simulation with proper updates.

        Note: D6GraspManager uses physics joints that are automatically maintained
        by the simulation, so no grasp update is needed here.
        """
        for _ in range(steps):
            self.scene.write_data_to_sim()
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

    def reset_arms_to_ready_position(self):
        """Reset arms to v19 configuration (retracted position for Reachability Map optimal).

        Explicitly sets joint angles to produce EE position closer to cable (X=0.23).
        The DifferentialIK controller will move arms to target positions during Phase 1.

        Robot positions (from Reachability Map optimization):
          - Robot Left:  X=0.20, Y=-0.18, Z=1.18
          - Robot Right: X=0.20, Y=0.12, Z=1.18
        """
        print("[Setup] Applying v24 joint configuration (higher EE)...")

        # v24: Joint angles for higher EE (avoid touching cable during hover)
        # joint2=0.0 (more upright), joint4=-1.5 (less bent), joint6=1.5 (match j4)
        v24_joint_pos = torch.tensor([
            [0.0, 0.0, 0.0, -1.5, 0.0, 1.5, 0.785, 0.04, 0.04]
        ], device=self.device)

        # CRITICAL: Do NOT use write_joint_state_to_sim() - it breaks PD tracking!
        # Only use set_joint_position_target() and let PD controller move the robot
        self.controller.robot_left.set_joint_position_target(v24_joint_pos)
        self.controller.robot_right.set_joint_position_target(v24_joint_pos)

        # Check cable position BEFORE arm movement
        cable_pos_pre_pd = self.cable.data.body_pos_w[0]
        cable_left_pre = cable_pos_pre_pd[17]  # seg_17 = left end
        print(f"[Setup] Cable position BEFORE PD control: seg_17 X={cable_left_pre[0].item():.4f}")

        # Allow PD controller to move arms to v24 position (needs ~200 steps)
        print("[Setup] Moving arms to v24 via PD control (200 steps)...")
        for step in range(200):
            self.controller.robot_left.write_data_to_sim()
            self.controller.robot_right.write_data_to_sim()
            self.scene.write_data_to_sim()
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

            # Progress update every 50 steps
            if step % 50 == 49:
                left_pos = self.controller.robot_left.data.joint_pos[0, :7].cpu().numpy()
                print(f"  [Step {step+1}] Left j2={left_pos[1]:.3f}, j4={left_pos[3]:.3f}")

        # Check cable position AFTER arm movement
        cable_pos_post_pd = self.cable.data.body_pos_w[0]
        cable_left_post = cable_pos_post_pd[17]  # seg_17 = left end
        cable_drift = abs(cable_left_post[0].item() - cable_left_pre[0].item())
        print(f"[Setup] Cable position AFTER PD control: seg_17 X={cable_left_post[0].item():.4f} (drift: {cable_drift:.4f}m)")

        # Print resulting positions
        left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
        print(f"[Setup] Left EE after reset: {left_ee[0].cpu().tolist()}")
        print(f"[Setup] Right EE after reset: {right_ee[0].cpu().tolist()}")

        # Debug: Robot base position check for left/right mapping
        left_base = self.controller.robot_left.data.root_pos_w[0]
        right_base = self.controller.robot_right.data.root_pos_w[0]
        print(f"  [Robot Base Check]")
        print(f"    Robot_Left base:  Y={left_base[1].item():.3f} (should be negative)")
        print(f"    Robot_Right base: Y={right_base[1].item():.3f} (should be positive)")

    def check_physics_health(self) -> Tuple[bool, str]:
        """Check if physics state is healthy (no NaN values).

        Returns:
            Tuple[bool, str]: (is_healthy, error_message)
        """
        # Check cable positions
        cable_pos = self.cable.data.body_pos_w[0]
        if torch.isnan(cable_pos).any():
            return False, "Cable positions contain NaN"

        # Check for extreme values (physics explosion)
        if torch.abs(cable_pos).max() > 100:
            return False, f"Cable positions are extreme: max={torch.abs(cable_pos).max().item():.1f}"

        # Check robot EE positions
        left_ee = self.controller.robot_left.data.body_pos_w[:, self.controller.ee_body_idx, :]
        right_ee = self.controller.robot_right.data.body_pos_w[:, self.controller.ee_body_idx, :]
        if torch.isnan(left_ee).any() or torch.isnan(right_ee).any():
            return False, "Robot EE positions contain NaN"

        return True, ""

    def reset_cable_position(self, x_pos: float = 0.40, y_pos: float = -0.05):
        """Reset cable to a new position.

        Args:
            x_pos: X position for cable (default 0.40, within robot reach)
            y_pos: Y position for cable (default -0.05, centered)

        Raises:
            RuntimeError: If physics becomes corrupted during reset
        """
        print(f"[Reset] Moving cable to X={x_pos:.2f}, Y={y_pos:.2f}")

        # CRITICAL: Create fresh root state tensor (don't clone potentially corrupted data)
        # root_state: [batch, 13] = [pos(3), quat(4), lin_vel(3), ang_vel(3)]
        table_height = 0.75  # TABLE_HEIGHT from dual_arm_cfg.py
        root_state = torch.zeros((1, 13), device=self.device)

        # Position - matches dual_arm_cfg.py cable init position
        root_state[0, 0] = x_pos      # X
        root_state[0, 1] = y_pos      # Y
        root_state[0, 2] = table_height + 0.03  # Z (cable radius above table)

        # Quaternion (cable lying along X axis - Plan A, -90° around Y)
        root_state[0, 3:7] = torch.tensor([0.7071, 0.0, -0.7071, 0.0], device=self.device)

        # Velocities already zero from zeros()

        print(f"[Reset] New root state: pos={root_state[0, :3].cpu().tolist()}, quat={root_state[0, 3:7].cpu().tolist()}")

        # Apply new state
        self.cable.write_root_state_to_sim(root_state)

        # Also reset joint positions to straight cable
        joint_pos = torch.zeros((1, self.cable.num_joints), device=self.device)
        joint_vel = torch.zeros((1, self.cable.num_joints), device=self.device)
        self.cable.write_joint_state_to_sim(joint_pos, joint_vel)

        # Step simulation to apply the new state
        self.scene.write_data_to_sim()
        self.sim.step()
        self.scene.update(self.sim.get_physics_dt())

        # Let physics settle with proper updates
        print(f"[Reset] Settling physics...")
        for i in range(100):
            self.step_sim(4)
            # Check periodically
            if i == 10 or i == 50:
                is_healthy, error_msg = self.check_physics_health()
                if not is_healthy:
                    print(f"[Reset] WARNING at step {i}: {error_msg}")

        # Check physics health after settling
        is_healthy, error_msg = self.check_physics_health()
        if not is_healthy:
            raise RuntimeError(f"Physics corrupted after cable reset: {error_msg}")

        # Verify new position
        cable_left, cable_right = self.get_cable_ends()
        print(f"[Reset] Cable ends after reset:")
        print(f"    Left end: {cable_left.cpu().tolist()}")
        print(f"    Right end: {cable_right.cpu().tolist()}")

    def set_stage(self, stage):
        """Set USD stage for D6GraspManager.

        Must be called after sim.reset() to ensure stage is available.
        """
        self.grasp_manager.set_stage(stage)
        print("[Collector] D6GraspManager stage set")

    def start_realtime_logging(self):
        """Start realtime image logging if configured."""
        if self.realtime_log_dir and self.realtime_logger is None:
            self.realtime_logger = RealtimeLogger(
                self.realtime_log_dir,
                self.get_camera_images
            )
            self.realtime_logger.start()

    def stop_realtime_logging(self):
        """Stop realtime image logging."""
        if self.realtime_logger:
            self.realtime_logger.stop()
            self.realtime_logger = None

    def get_cable_ends(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get cable end positions from articulated cable segments.

        Returns the cable ends mapped to robot positions based on proximity:
        - left_end: the end closer to left robot (at Y=-0.30)
        - right_end: the end closer to right robot (at Y=+0.30)

        Raises:
            RuntimeError: If cable positions contain NaN (simulation corrupted)
        """
        # Get body positions of all segments
        body_pos = self.cable.data.body_pos_w[0]  # [num_bodies, 3]

        # NaN check - detect simulation instability early
        if check_cable_nan(body_pos):
            raise RuntimeError("Cable simulation corrupted - NaN detected in segment positions")

        # Debug: Print all segment positions
        print(f"  [Cable Debug] All segment positions (num_bodies={body_pos.shape[0]}):")
        for i in range(body_pos.shape[0]):
            pos = body_pos[i].cpu().tolist()
            print(f"    seg_{i}: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}")

        # Plan A: X-axis layout - seg_19 is left end (MIN X), seg_17 is right end (MAX X)
        left_seg = body_pos[CABLE_BASE_IDX]   # seg_19 (left end X≈0.27)
        right_seg = body_pos[CABLE_TIP_IDX]   # seg_17 (right end X≈0.81)

        print(f"  [Cable Debug] seg_{CABLE_BASE_IDX} (left end): {left_seg.cpu().tolist()}")
        print(f"  [Cable Debug] seg_{CABLE_TIP_IDX} (right end): {right_seg.cpu().tolist()}")

        # Plan A X-axis layout: seg_19 is left end (MIN X), seg_17 is right end (MAX X)
        # Cable segments are NOT in physical order - verified by X coordinates
        left_end = left_seg     # seg_19 at X≈0.27 (left end)
        right_end = right_seg   # seg_17 at X≈0.81 (right end)
        self._left_seg_idx = CABLE_BASE_IDX   # 19 (Plan A)
        self._right_seg_idx = CABLE_TIP_IDX   # 17 (Plan A)

        # Debug: Coordinate check
        print(f"  [Coordinate Check]")
        print(f"    seg_{CABLE_BASE_IDX} (left end): {left_seg.cpu().tolist()} (Y={left_seg[1].item():.3f})")
        print(f"    seg_{CABLE_TIP_IDX} (right end): {right_seg.cpu().tolist()} (Y={right_seg[1].item():.3f})")
        print(f"    Left gripper -> seg_{self._left_seg_idx} (actual left end)")
        print(f"    Right gripper -> seg_{self._right_seg_idx} (actual right end)")

        return left_end, right_end

    def get_cable_segment_paths(self) -> Tuple[str, str]:
        """Get USD paths for cable segments to attach to each gripper.

        Must be called after get_cable_ends() to ensure correct mapping.
        """
        left_seg = self._left_seg_idx if hasattr(self, '_left_seg_idx') else CABLE_BASE_IDX
        right_seg = self._right_seg_idx if hasattr(self, '_right_seg_idx') else CABLE_TIP_IDX
        return (
            f"/World/envs/env_0/Cable/seg_{left_seg}",
            f"/World/envs/env_0/Cable/seg_{right_seg}"
        )

    def validate_grasp(self) -> Tuple[bool, str]:
        """Validate that both grippers have successfully grasped the cable.

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        # Get gripper positions (fingertip level)
        left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

        # Check for NaN in EE positions (indicates IK failure)
        if torch.isnan(left_ee).any() or torch.isnan(right_ee).any():
            return False, "EE positions contain NaN (IK failure)"

        # Fingertip is 10.7cm below panda_hand when pointing down
        left_fingertip_z = left_ee[0, 2].item() - 0.1123
        right_fingertip_z = right_ee[0, 2].item() - 0.1123

        # Get cable clamp segment positions
        cable_pos = self.cable.data.body_pos_w[0]  # (num_segments, 3)
        left_clamp_pos = cable_pos[LEFT_CLAMP_SEGMENT]
        right_clamp_pos = cable_pos[RIGHT_CLAMP_SEGMENT]

        # Check for NaN in cable positions
        if torch.isnan(left_clamp_pos).any() or torch.isnan(right_clamp_pos).any():
            return False, "Cable positions contain NaN (physics instability)"

        # Calculate distances (XY plane, ignore Z for now)
        left_dist_xy = torch.sqrt(
            (left_ee[0, 0] - left_clamp_pos[0])**2 +
            (left_ee[0, 1] - left_clamp_pos[1])**2
        ).item()
        right_dist_xy = torch.sqrt(
            (right_ee[0, 0] - right_clamp_pos[0])**2 +
            (right_ee[0, 1] - right_clamp_pos[1])**2
        ).item()

        # Check gripper positions
        left_gripper_pos = self.controller.get_gripper_pos(self.controller.robot_left)
        right_gripper_pos = self.controller.get_gripper_pos(self.controller.robot_right)

        # Check for NaN in computed values
        if np.isnan(left_dist_xy) or np.isnan(right_dist_xy):
            return False, "Distance calculation returned NaN"
        if np.isnan(left_gripper_pos) or np.isnan(right_gripper_pos):
            return False, "Gripper position returned NaN"

        errors = []

        # Relaxed gripper tolerance (Terminal 3: 0.025m instead of 0.01m)
        GRIPPER_TOLERANCE = 0.025

        # Validate left grasp
        if left_dist_xy > GRASP_DISTANCE_THRESHOLD:
            errors.append(f"Left gripper too far from seg_{LEFT_CLAMP_SEGMENT}: {left_dist_xy:.3f}m")
        if left_gripper_pos > GRIPPER_CLOSED + GRIPPER_TOLERANCE:
            errors.append(f"Left not closed: {left_gripper_pos:.3f}m (threshold: {GRIPPER_CLOSED + GRIPPER_TOLERANCE:.3f}m)")

        # Validate right grasp
        if right_dist_xy > GRASP_DISTANCE_THRESHOLD:
            errors.append(f"Right gripper too far from seg_{RIGHT_CLAMP_SEGMENT}: {right_dist_xy:.3f}m")
        if right_gripper_pos > GRIPPER_CLOSED + GRIPPER_TOLERANCE:
            errors.append(f"Right not closed: {right_gripper_pos:.3f}m (threshold: {GRIPPER_CLOSED + GRIPPER_TOLERANCE:.3f}m)")

        if errors:
            return False, "; ".join(errors)

        print(f"  [Grasp Validation] SUCCESS")
        print(f"    Left: dist={left_dist_xy:.3f}m, gripper={left_gripper_pos:.4f}m")
        print(f"    Right: dist={right_dist_xy:.3f}m, gripper={right_gripper_pos:.4f}m")
        return True, ""

    def verify_grasp_by_lifting(self, lift_height: float = 0.03) -> Tuple[bool, str]:
        """Verify grasp by physically lifting the cable and checking if it follows.

        This is the definitive test for successful grasp - if the cable doesn't
        move up with the grippers, the grasp has failed regardless of distance metrics.

        Args:
            lift_height: Height to lift (default 3cm)

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        print(f"\n  [Lift Verification] Testing grasp by lifting {lift_height*100:.0f}cm...")

        # Record cable positions BEFORE lift
        cable_pos_before = self.cable.data.body_pos_w[0].clone()  # (num_segments, 3)
        cable_left_z_before = cable_pos_before[LEFT_CLAMP_SEGMENT, 2].item()
        cable_right_z_before = cable_pos_before[RIGHT_CLAMP_SEGMENT, 2].item()

        print(f"    Cable Z before lift: Left={cable_left_z_before:.4f}m, Right={cable_right_z_before:.4f}m")

        # Get current EE positions
        left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

        # Target positions (lift up)
        left_target = left_ee[0].clone()
        left_target[2] += lift_height
        right_target = right_ee[0].clone()
        right_target[2] += lift_height

        # Perform lift (slow, controlled motion)
        print(f"    Lifting grippers to Z={left_target[2].item():.4f}m...")

        # Use interpolated motion for smooth lift
        steps = 30
        for i in range(steps):
            t = (i + 1) / steps
            left_interp = left_ee[0] + t * (left_target - left_ee[0])
            right_interp = right_ee[0] + t * (right_target - right_ee[0])

            # Keep grippers closed during lift
            self.controller.set_targets(
                left_interp.unsqueeze(0), right_interp.unsqueeze(0),
                GRIPPER_CLOSED, GRIPPER_CLOSED,
                use_fixed_orientation=True
            )
            self.step_sim(5)

        # Settle physics
        self.step_sim(30)

        # Check cable positions AFTER lift
        cable_pos_after = self.cable.data.body_pos_w[0]
        cable_left_z_after = cable_pos_after[LEFT_CLAMP_SEGMENT, 2].item()
        cable_right_z_after = cable_pos_after[RIGHT_CLAMP_SEGMENT, 2].item()

        # Calculate Z change
        left_z_change = cable_left_z_after - cable_left_z_before
        right_z_change = cable_right_z_after - cable_right_z_before

        print(f"    Cable Z after lift:  Left={cable_left_z_after:.4f}m, Right={cable_right_z_after:.4f}m")
        print(f"    Cable Z change:      Left={left_z_change*100:.1f}cm, Right={right_z_change*100:.1f}cm")

        # Success threshold: cable should lift at least 50% of gripper lift
        MIN_LIFT_RATIO = 0.5
        min_expected_lift = lift_height * MIN_LIFT_RATIO

        errors = []
        if left_z_change < min_expected_lift:
            errors.append(f"Left cable didn't lift: {left_z_change*100:.1f}cm (expected >{min_expected_lift*100:.0f}cm)")
        if right_z_change < min_expected_lift:
            errors.append(f"Right cable didn't lift: {right_z_change*100:.1f}cm (expected >{min_expected_lift*100:.0f}cm)")

        if errors:
            print(f"    [LIFT TEST FAILED] Cable did not follow grippers!")
            print(f"    This means the physical grasp failed - grippers closed above the cable.")
            return False, "; ".join(errors)

        print(f"    [LIFT TEST PASSED] ✅ Cable followed grippers - physical grasp confirmed!")
        return True, ""

    def validate_reach(self) -> Tuple[bool, str]:
        """Validate that grippers reached cable ends.

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        # Get gripper positions
        left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

        # Check for NaN in EE positions
        if torch.isnan(left_ee).any() or torch.isnan(right_ee).any():
            return False, "EE positions contain NaN (IK failure)"

        # Get cable ends
        cable_left, cable_right = self.get_cable_ends()

        # Check for NaN in cable positions
        if torch.isnan(cable_left).any() or torch.isnan(cable_right).any():
            return False, "Cable positions contain NaN (physics instability)"

        # Calculate XY distance to cable ends
        left_dist = torch.sqrt(
            (left_ee[0, 0] - cable_left[0])**2 +
            (left_ee[0, 1] - cable_left[1])**2
        ).item()
        right_dist = torch.sqrt(
            (right_ee[0, 0] - cable_right[0])**2 +
            (right_ee[0, 1] - cable_right[1])**2
        ).item()

        # Check for NaN in computed distances
        if np.isnan(left_dist) or np.isnan(right_dist):
            return False, "Distance calculation returned NaN"

        REACH_THRESHOLD = 0.05  # 5cm threshold

        errors = []
        if left_dist > REACH_THRESHOLD:
            errors.append(f"Left gripper too far from cable end: {left_dist:.3f}m (threshold: {REACH_THRESHOLD}m)")
        if right_dist > REACH_THRESHOLD:
            errors.append(f"Right gripper too far from cable end: {right_dist:.3f}m (threshold: {REACH_THRESHOLD}m)")

        if errors:
            # Report current positions for debugging
            print(f"  [Reach Debug] Left EE: {left_ee[0].cpu().tolist()}")
            print(f"  [Reach Debug] Right EE: {right_ee[0].cpu().tolist()}")
            print(f"  [Reach Debug] Cable left: {cable_left.cpu().tolist()}")
            print(f"  [Reach Debug] Cable right: {cable_right.cpu().tolist()}")
            return False, "; ".join(errors)

        print(f"  [Reach Validation] SUCCESS")
        print(f"    Left: {left_dist:.3f}m, Right: {right_dist:.3f}m")
        return True, ""

    def fingertip_to_panda_hand(self, fingertip_target: torch.Tensor) -> torch.Tensor:
        """Convert fingertip target to panda_hand target.

        When gripper points down, panda_hand is 10.7cm ABOVE the fingertip.
        So to reach fingertip position X, panda_hand should go to X + [0, 0, 0.1123].
        """
        offset = self.controller.get_fingertip_offset_world()
        target = fingertip_target.clone()
        target[..., 2] += offset
        return target

    def move_to_target(
        self,
        left_target: torch.Tensor,
        right_target: torch.Tensor,
        left_gripper: float,
        right_gripper: float,
        max_steps: int = 400,
        threshold: float = 0.01,
    ) -> bool:
        """Move arms to target positions with gripper control.

        Note: Targets are for panda_hand position (not fingertips).
        Use fingertip_to_panda_hand() to convert fingertip targets.
        """
        # Get starting positions
        left_ee_start, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee_start, _ = self.controller.get_ee_pose(self.controller.robot_right)

        for step in range(max_steps):
            # Interpolate target to avoid large jumps (smooth approach)
            t = min(1.0, (step + 1) / 50.0)  # Ramp up over 50 steps
            left_interp = left_ee_start + t * (left_target - left_ee_start)
            right_interp = right_ee_start + t * (right_target - right_ee_start)

            # Set targets (debug at start, periodically, and at end)
            debug = (step == 0) or (step == max_steps - 1) or (step > 0 and step % 100 == 0)
            # NOTE: use_fixed_orientation=True to maintain consistent gripper orientation
            # IK solver now uses the same orientation (Roll=180°, Yaw=90°) as runtime
            self.controller.set_targets(left_interp, right_interp, left_gripper, right_gripper, debug=debug, use_fixed_orientation=True)

            # Step simulation
            self.step_sim(4)

            # Check if reached (only after interpolation is complete)
            if t >= 1.0:
                left_ee, left_quat = self.controller.get_ee_pose(self.controller.robot_left)
                right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

                left_dist = torch.norm(left_ee - left_target).item()
                right_dist = torch.norm(right_ee - right_target).item()

                # Log progress at intervals (position-only control, no orientation target)
                if step % 50 == 0 or step == max_steps - 1:
                    max_dist = max(left_dist, right_dist)
                    print(f"    Step {step}: left_dist={left_dist:.4f}m, right_dist={right_dist:.4f}m, max={max_dist:.4f}m")

                if left_dist < threshold and right_dist < threshold:
                    return True

        return False

    def close_grippers_slowly(self, target_pos: float = GRIPPER_CLOSED, steps: int = 100):
        """Close grippers gradually for better grasp physics."""
        current_left_grip = self.controller.get_gripper_pos(self.controller.robot_left)
        current_right_grip = self.controller.get_gripper_pos(self.controller.robot_right)

        # CRITICAL: Capture EE positions at START to prevent drift during gripper closing
        left_ee_start, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee_start, _ = self.controller.get_ee_pose(self.controller.robot_right)

        # Monitor cable position during close - both ends
        cable_left_initial = self.cable.data.body_pos_w[0, CABLE_BASE_IDX].clone()
        cable_right_initial = self.cable.data.body_pos_w[0, CABLE_TIP_IDX].clone()
        print(f"[Gripper Close Debug] Initial left cable (seg_{CABLE_BASE_IDX}): {cable_left_initial.cpu().tolist()}")
        print(f"[Gripper Close Debug] Initial right cable (seg_{CABLE_TIP_IDX}): {cable_right_initial.cpu().tolist()}")
        print(f"[Gripper Close Debug] Left EE start: {left_ee_start.cpu().tolist()}")
        print(f"[Gripper Close Debug] Right EE start: {right_ee_start.cpu().tolist()}")

        # Debug: Check gripper orientations
        _, left_quat = self.controller.get_ee_pose(self.controller.robot_left)
        _, right_quat = self.controller.get_ee_pose(self.controller.robot_right)
        print(f"[Gripper Close Debug] Left quat: {left_quat.cpu().tolist()}")
        print(f"[Gripper Close Debug] Right quat: {right_quat.cpu().tolist()}")

        print(f"[Gripper Close Debug] Gripper: {current_left_grip:.4f} -> {target_pos:.4f}")

        for i in range(steps):
            t = (i + 1) / steps
            grip_pos = current_left_grip + t * (target_pos - current_left_grip)

            # Explicitly hold arm position using fixed EE targets (prevents drift)
            self.controller.set_targets(
                left_ee_start.clone(), right_ee_start.clone(),
                grip_pos, grip_pos,
                use_fixed_orientation=True
            )
            self.step_sim(5)  # NaN fix: more steps per gripper increment

            # Monitor cable every 50 steps (both ends) - more detailed for right
            if (i + 1) % 50 == 0 or i == 0:
                cable_left_pos = self.cable.data.body_pos_w[0, CABLE_BASE_IDX]
                cable_right_pos = self.cable.data.body_pos_w[0, CABLE_TIP_IDX]
                left_delta_z = (cable_left_pos[2] - cable_left_initial[2]).item()
                right_delta_z = (cable_right_pos[2] - cable_right_initial[2]).item()
                right_delta_x = (cable_right_pos[0] - cable_right_initial[0]).item()
                right_delta_y = (cable_right_pos[1] - cable_right_initial[1]).item()
                actual_grip_l = self.controller.get_gripper_pos(self.controller.robot_left)
                actual_grip_r = self.controller.get_gripper_pos(self.controller.robot_right)
                # Get right EE position to compare with cable
                right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
                right_ee_z = right_ee[0, 2].item() - 0.1123  # fingertip
                right_cable_z = cable_right_pos[2].item()
                print(f"[Gripper Close] Step {i+1}/{steps}: grip_L={actual_grip_l:.4f}m grip_R={actual_grip_r:.4f}m | L_dZ={left_delta_z*100:.2f}cm R_dX={right_delta_x*100:.2f}cm R_dY={right_delta_y*100:.2f}cm R_dZ={right_delta_z*100:.2f}cm | R_ftip_Z={right_ee_z:.4f} R_cable_Z={right_cable_z:.4f}")

                # Alert if cable moves too much
                cable_dist = torch.norm(cable_left_pos - cable_left_initial).item()
                if cable_dist > 0.1:
                    print(f"[ALERT] Left cable moved {cable_dist:.2f}m - possible physics instability!")
                    if torch.isnan(cable_left_pos).any():
                        print(f"[CRITICAL] Cable position is NaN!")
                        break

    def open_grippers_slowly(self, target_pos: float = GRIPPER_OPEN, steps: int = 50):
        """Open grippers gradually."""
        current_left_grip = self.controller.get_gripper_pos(self.controller.robot_left)
        current_right_grip = self.controller.get_gripper_pos(self.controller.robot_right)

        # CRITICAL: Capture EE positions at START to prevent drift during gripper opening
        left_ee_start, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee_start, _ = self.controller.get_ee_pose(self.controller.robot_right)

        for i in range(steps):
            t = (i + 1) / steps
            grip_pos = current_left_grip + t * (target_pos - current_left_grip)

            # Explicitly hold arm position using fixed EE targets (prevents drift)
            self.controller.set_targets(
                left_ee_start.clone(), right_ee_start.clone(),
                grip_pos, grip_pos,
                use_fixed_orientation=True
            )
            self.step_sim(2)

    def get_camera_images(self) -> Dict[str, np.ndarray]:
        """Get current camera images."""
        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"]
            img = rgb[0, ..., :3].cpu().numpy().astype(np.uint8)
            images[name] = img

        # Overhead
        rgb = self.overhead.data.output["rgb"]
        images['overhead'] = rgb[0, ..., :3].cpu().numpy().astype(np.uint8)

        return images

    def save_phase_images(self, phase: TaskPhase, images: Dict[str, np.ndarray]):
        """Save images for a phase."""
        phase_name = f"phase_{phase.value}_{phase.name.lower()}"
        phase_dir = os.path.join(self.output_dir, phase_name)
        os.makedirs(phase_dir, exist_ok=True)

        for cam_name, img in images.items():
            # Include phase name in filename
            filename = os.path.join(phase_dir, f"{phase_name}_{cam_name}.png")
            Image.fromarray(img).save(filename)
            print(f"    Saved: {filename}")

        # Create composite
        composite = self._create_composite(images)
        composite_file = os.path.join(phase_dir, f"{phase_name}_composite.png")
        Image.fromarray(composite).save(composite_file)

    def _create_composite(self, images: Dict[str, np.ndarray]) -> np.ndarray:
        """Create 2x2 composite image."""
        h, w = 256, 256
        composite = np.zeros((h * 2, w * 2, 3), dtype=np.uint8)

        positions = {
            'front_left': (0, 0),
            'front_right': (0, w),
            'back': (h, 0),
            'overhead': (h, w),
        }

        for name, (y, x) in positions.items():
            if name in images:
                img = images[name]
                if img.shape[:2] != (h, w):
                    img = np.array(Image.fromarray(img).resize((w, h)))
                composite[y:y+h, x:x+w] = img

        return composite

    def execute_phase(self, phase: TaskPhase) -> bool:
        """Execute a single phase and capture goal image."""
        print(f"\n[Phase {phase.value}] {phase.name}: {PHASE_DESCRIPTIONS[phase]}")

        # Get cable ends (includes NaN check)
        try:
            cable_left, cable_right = self.get_cable_ends()
        except RuntimeError as e:
            print(f"[ABORT] Phase {phase.name} failed: {e}")
            return False

        # Additional health check with EE positions
        cable_pos = self.cable.data.body_pos_w[0]
        left_ee_pos, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee_pos, _ = self.controller.get_ee_pose(self.controller.robot_right)

        if not self.health_checker.check(cable_pos, left_ee_pos, right_ee_pos):
            print(f"[ABORT] Phase {phase.name} aborted due to simulation instability")
            return False

        if phase == TaskPhase.REACH_CABLE:
            # Detailed debug: cable segment and gripper orientation analysis
            cable_pos = self.cable.data.body_pos_w[0]
            seg_0 = cable_pos[0]
            seg_1 = cable_pos[1]
            seg_8 = cable_pos[8] if cable_pos.shape[0] > 8 else cable_pos[-2]
            seg_9 = cable_pos[-1]

            print(f"\n{'='*60}")
            print(f"[DEBUG] Cable Segment Positions:")
            print(f"  seg_0: X={seg_0[0].item():.4f}, Y={seg_0[1].item():.4f}, Z={seg_0[2].item():.4f}")
            print(f"  seg_1: X={seg_1[0].item():.4f}, Y={seg_1[1].item():.4f}, Z={seg_1[2].item():.4f}")
            print(f"  seg_8: X={seg_8[0].item():.4f}, Y={seg_8[1].item():.4f}, Z={seg_8[2].item():.4f}")
            print(f"  seg_9: X={seg_9[0].item():.4f}, Y={seg_9[1].item():.4f}, Z={seg_9[2].item():.4f}")

            # Cable local direction (left end: seg_0→seg_1, right end: seg_8→seg_9)
            left_cable_dir = seg_1[:2] - seg_0[:2]
            right_cable_dir = seg_9[:2] - seg_8[:2]

            import math
            left_cable_yaw = math.atan2(left_cable_dir[1].item(), left_cable_dir[0].item())
            right_cable_yaw = math.atan2(right_cable_dir[1].item(), right_cable_dir[0].item())

            print(f"\n[DEBUG] Cable Local Direction (Yaw):")
            print(f"  Left end (seg_0→seg_1): {math.degrees(left_cable_yaw):.1f}°")
            print(f"  Right end (seg_8→seg_9): {math.degrees(right_cable_yaw):.1f}°")

            # Current gripper position and orientation
            left_ee_pos, left_ee_quat = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee_pos, right_ee_quat = self.controller.get_ee_pose(self.controller.robot_right)

            print(f"\n[DEBUG] Gripper Positions:")
            print(f"  Left EE:  X={left_ee_pos[0,0].item():.4f}, Y={left_ee_pos[0,1].item():.4f}, Z={left_ee_pos[0,2].item():.4f}")
            print(f"  Right EE: X={right_ee_pos[0,0].item():.4f}, Y={right_ee_pos[0,1].item():.4f}, Z={right_ee_pos[0,2].item():.4f}")

            print(f"\n[DEBUG] Gripper Orientations (Quaternion wxyz):")
            print(f"  Left EE:  {left_ee_quat[0].cpu().tolist()}")
            print(f"  Right EE: {right_ee_quat[0].cpu().tolist()}")

            # Extract Euler angles from quaternion
            left_euler = R.from_quat([left_ee_quat[0,1].item(), left_ee_quat[0,2].item(),
                                      left_ee_quat[0,3].item(), left_ee_quat[0,0].item()]).as_euler('xyz', degrees=True)
            right_euler = R.from_quat([right_ee_quat[0,1].item(), right_ee_quat[0,2].item(),
                                       right_ee_quat[0,3].item(), right_ee_quat[0,0].item()]).as_euler('xyz', degrees=True)

            print(f"\n[DEBUG] Gripper Orientations (Euler xyz degrees):")
            print(f"  Left EE:  Roll={left_euler[0]:.1f}°, Pitch={left_euler[1]:.1f}°, Yaw={left_euler[2]:.1f}°")
            print(f"  Right EE: Roll={right_euler[0]:.1f}°, Pitch={right_euler[1]:.1f}°, Yaw={right_euler[2]:.1f}°")

            # Finger opening direction analysis
            print(f"\n[DEBUG] Finger Opening Direction Analysis:")
            print(f"  Panda gripper fingers open along local Y-axis of panda_hand")
            print(f"  Cable direction at left end: {math.degrees(left_cable_yaw):.1f}°")
            print(f"  Gripper Yaw at left: {left_euler[2]:.1f}°")
            print(f"  Difference: {abs(math.degrees(left_cable_yaw) - left_euler[2]):.1f}°")
            print(f"  (Plan A: Should be ~0° for fingers perpendicular to X-axis cable)")
            print(f"{'='*60}\n")

            # VERTICAL DESCENT: Safe because gripper fingers are perpendicular to cable
            print(f"  Cable left: {cable_left.cpu().tolist()}")
            print(f"  Cable right: {cable_right.cpu().tolist()}")

            # Stage 1: Hover directly above cable (10cm above table)
            # Plan B: Y-axis cable layout
            # Cable extends along Y axis: seg_17 at min Y (left), seg_19 at max Y (right)
            # X is roughly constant at cable spawn X position
            # Apply inward offset to Y axis (toward cable center)
            HOVER_HEIGHT = 0.10
            # seg_17 (left) is at min Y, so inward = +Y
            # seg_19 (right) is at max Y, so inward = -Y
            left_grasp_x = cable_left[0].item()  # Keep X at cable position
            right_grasp_x = cable_right[0].item()  # Keep X at cable position
            left_grasp_y = cable_left[1].item() + GRASP_INWARD_OFFSET  # Move toward center (+Y)
            right_grasp_y = cable_right[1].item() - GRASP_INWARD_OFFSET  # Move toward center (-Y)
            print(f"  [Y-axis cable] Grasp position (inward offset applied to Y):")
            print(f"  [Grasp X] Left X: {left_grasp_x:.4f}, Right X: {right_grasp_x:.4f} (unchanged)")
            print(f"  [Grasp Offset] Left Y: {cable_left[1].item():.4f} -> {left_grasp_y:.4f} (+{GRASP_INWARD_OFFSET}m)")
            print(f"  [Grasp Offset] Right Y: {cable_right[1].item():.4f} -> {right_grasp_y:.4f} (-{GRASP_INWARD_OFFSET}m)")

            # Stage 0: First, rise straight up to avoid disturbing cable during horizontal movement
            # Get current EE positions
            left_ee_current, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee_current, _ = self.controller.get_ee_pose(self.controller.robot_right)

            SAFE_HEIGHT = 0.20  # Rise to 20cm above table for horizontal movement
            left_rise = torch.tensor([
                [left_ee_current[0,0].item(), left_ee_current[0,1].item(), TABLE_HEIGHT + SAFE_HEIGHT]
            ], device=self.device)
            right_rise = torch.tensor([
                [right_ee_current[0,0].item(), right_ee_current[0,1].item(), TABLE_HEIGHT + SAFE_HEIGHT]
            ], device=self.device)

            left_rise_target = self.fingertip_to_panda_hand(left_rise)
            right_rise_target = self.fingertip_to_panda_hand(right_rise)

            print(f"  Stage 0: Rising to safe height ({TABLE_HEIGHT + SAFE_HEIGHT:.3f}m)...")
            print(f"    Left current: Z={left_ee_current[0,2].item():.4f} -> {TABLE_HEIGHT + SAFE_HEIGHT:.4f}")
            self.move_to_target(left_rise_target, right_rise_target, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=150)
            self.step_sim(30)

            # Check cable position after Stage 0
            cable_pos_stage0 = self.cable.data.body_pos_w[0]
            cable_left_s0 = cable_pos_stage0[LEFT_CLAMP_SEGMENT]
            cable_move_s0 = abs(cable_left_s0[0].item() - cable_left[0].item())
            print(f"  [Cable Monitor] After Stage 0:")
            print(f"    seg_{LEFT_CLAMP_SEGMENT} X: {cable_left[0].item():.4f} -> {cable_left_s0[0].item():.4f} (moved {cable_move_s0:.4f}m)")

            # Stage 1: Now move horizontally at safe height to above cable
            left_fingertip_hover = torch.tensor([
                [left_grasp_x, left_grasp_y, TABLE_HEIGHT + SAFE_HEIGHT]  # Stay at safe height
            ], device=self.device)
            right_fingertip_hover = torch.tensor([
                [right_grasp_x, right_grasp_y, TABLE_HEIGHT + SAFE_HEIGHT]  # Stay at safe height
            ], device=self.device)

            left_hover = self.fingertip_to_panda_hand(left_fingertip_hover)
            right_hover = self.fingertip_to_panda_hand(right_fingertip_hover)

            print(f"  Stage 1: Moving horizontally to above cable at safe height...")
            print(f"    Left fingertip target: {left_fingertip_hover[0].cpu().tolist()}")
            print(f"    Right fingertip target: {right_fingertip_hover[0].cpu().tolist()}")

            self.move_to_target(left_hover, right_hover, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=300)
            self.step_sim(30)

            # Monitor cable position after Stage 1
            cable_pos_stage1 = self.cable.data.body_pos_w[0]
            cable_left_s1 = cable_pos_stage1[LEFT_CLAMP_SEGMENT]
            cable_right_s1 = cable_pos_stage1[RIGHT_CLAMP_SEGMENT]
            cable_move_x = abs(cable_left_s1[0].item() - cable_left[0].item())
            print(f"  [Cable Monitor] After Stage 1:")
            print(f"    seg_{LEFT_CLAMP_SEGMENT} X: {cable_left[0].item():.4f} -> {cable_left_s1[0].item():.4f} (moved {cable_move_x:.4f}m)")
            if cable_move_x > 0.05:
                print(f"    ⚠️ WARNING: Cable moved significantly ({cable_move_x:.3f}m > 0.05m)")

            # Stage 2: Descend to just above cable (3cm above table)
            # Use same inward Y offset as Stage 1
            APPROACH_HEIGHT = 0.03
            left_fingertip_above = torch.tensor([
                [left_grasp_x, left_grasp_y, TABLE_HEIGHT + APPROACH_HEIGHT]
            ], device=self.device)
            right_fingertip_above = torch.tensor([
                [right_grasp_x, right_grasp_y, TABLE_HEIGHT + APPROACH_HEIGHT]
            ], device=self.device)

            left_above = self.fingertip_to_panda_hand(left_fingertip_above)
            right_above = self.fingertip_to_panda_hand(right_fingertip_above)

            print(f"  Stage 2: Descending to above cable (3cm above table)...")
            print(f"    Left fingertip target: {left_fingertip_above[0].cpu().tolist()}")
            print(f"    Right fingertip target: {right_fingertip_above[0].cpu().tolist()}")

            self.move_to_target(left_above, right_above, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=200)
            self.step_sim(30)

            # Monitor cable position after Stage 2
            cable_pos_stage2 = self.cable.data.body_pos_w[0]
            cable_left_s2 = cable_pos_stage2[LEFT_CLAMP_SEGMENT]
            cable_right_s2 = cable_pos_stage2[RIGHT_CLAMP_SEGMENT]
            cable_move_x_s2 = abs(cable_left_s2[0].item() - cable_left[0].item())
            cable_move_s1_s2 = abs(cable_left_s2[0].item() - cable_left_s1[0].item())
            print(f"  [Cable Monitor] After Stage 2:")
            print(f"    seg_{LEFT_CLAMP_SEGMENT} X: {cable_left_s1[0].item():.4f} -> {cable_left_s2[0].item():.4f} (moved {cable_move_s1_s2:.4f}m)")
            print(f"    Total movement from start: {cable_move_x_s2:.4f}m")
            if cable_move_x_s2 > 0.05:
                print(f"    ⚠️ WARNING: Cable moved significantly ({cable_move_x_s2:.3f}m > 0.05m)")

            # Stage 3: Final descent to grasp height (fingertip at cable center)
            # IMPORTANT: Re-acquire cable position as it may have moved during approach
            cable_pos_updated = self.cable.data.body_pos_w[0]
            cable_left_updated = cable_pos_updated[LEFT_CLAMP_SEGMENT]
            cable_right_updated = cable_pos_updated[RIGHT_CLAMP_SEGMENT]
            print(f"  [Cable Position Update] Before Stage 3:")
            print(f"    seg_{LEFT_CLAMP_SEGMENT} (left end): X={cable_left_updated[0].item():.4f}, Y={cable_left_updated[1].item():.4f}")
            print(f"    seg_{RIGHT_CLAMP_SEGMENT} (right end): X={cable_right_updated[0].item():.4f}, Y={cable_right_updated[1].item():.4f}")

            # Update grasp positions based on current cable position
            # Y-axis cable: inward offset applied to Y, X unchanged
            left_grasp_x_updated = cable_left_updated[0].item()  # Keep X at cable position
            right_grasp_x_updated = cable_right_updated[0].item()  # Keep X at cable position
            left_grasp_y_updated = cable_left_updated[1].item() + GRASP_INWARD_OFFSET  # seg_17 at min Y, move +Y
            right_grasp_y_updated = cable_right_updated[1].item() - GRASP_INWARD_OFFSET  # seg_19 at max Y, move -Y
            print(f"    Updated targets: Left X={left_grasp_x_updated:.4f}, Y={left_grasp_y_updated:.4f} (inward +3cm)")
            print(f"    Updated targets: Right X={right_grasp_x_updated:.4f}, Y={right_grasp_y_updated:.4f} (inward -3cm)")

            # Cable sits at TABLE_HEIGHT + 0.005 = 0.755m
            # Fingertips should be at cable center height to straddle it
            # NEVER go below TABLE_HEIGHT (0.75m) to avoid table collision
            GRASP_HEIGHT = 0.005  # At cable center height (TABLE_HEIGHT + 0.005 = 0.755m)
            left_grasp = torch.tensor([
                [left_grasp_x_updated, left_grasp_y_updated, TABLE_HEIGHT + GRASP_HEIGHT]
            ], device=self.device)
            right_grasp = torch.tensor([
                [right_grasp_x_updated, right_grasp_y_updated, TABLE_HEIGHT + GRASP_HEIGHT]
            ], device=self.device)

            left_target = self.fingertip_to_panda_hand(left_grasp)
            right_target = self.fingertip_to_panda_hand(right_grasp)

            print(f"  Stage 3: Final descent to grasp height (at cable center Z={TABLE_HEIGHT + GRASP_HEIGHT:.3f}m)...")
            print(f"    Left fingertip target: {left_grasp[0].cpu().tolist()}")
            print(f"    Right fingertip target: {right_grasp[0].cpu().tolist()}")

            # Check for NaN in targets
            if torch.isnan(left_target).any() or torch.isnan(right_target).any():
                print(f"  [ERROR] NaN detected in target positions!")
                raise RuntimeError("NaN in target positions")

            reached = self.move_to_target(left_target, right_target, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=300)
            print(f"  Reached grasp position: {reached}")

            # Joint limit analysis
            import math
            left_joint_pos = self.controller.robot_left.data.joint_pos[0]
            right_joint_pos = self.controller.robot_right.data.joint_pos[0]

            PANDA_JOINT_LIMITS = [
                (-2.8973, 2.8973),   # joint1
                (-1.7628, 1.7628),   # joint2
                (-2.8973, 2.8973),   # joint3
                (-3.0718, -0.0698),  # joint4
                (-2.8973, 2.8973),   # joint5
                (-0.0175, 3.7525),   # joint6
                (-2.8973, 2.8973),   # joint7
            ]

            print(f"\n[DEBUG] Left Arm Joint Analysis:")
            print(f"{'Joint':<8} {'Angle(deg)':<12} {'Min':<10} {'Max':<10} {'Margin':<10} {'Status'}")
            print("-" * 70)
            for i in range(7):
                angle = left_joint_pos[i].item()
                angle_deg = math.degrees(angle)
                min_lim, max_lim = PANDA_JOINT_LIMITS[i]
                margin_to_min = angle - min_lim
                margin_to_max = max_lim - angle
                min_margin = min(margin_to_min, margin_to_max)
                status = "OK"
                if min_margin < 0.1:
                    status = "⚠️ NEAR LIMIT"
                if min_margin < 0.05:
                    status = "❌ AT LIMIT"
                print(f"joint{i+1:<3} {angle_deg:>10.1f}°  {math.degrees(min_lim):>8.1f}°  {math.degrees(max_lim):>8.1f}°  {math.degrees(min_margin):>8.1f}°  {status}")

            print(f"\n[DEBUG] Right Arm Joint Analysis:")
            print(f"{'Joint':<8} {'Angle(deg)':<12} {'Min':<10} {'Max':<10} {'Margin':<10} {'Status'}")
            print("-" * 70)
            for i in range(7):
                angle = right_joint_pos[i].item()
                angle_deg = math.degrees(angle)
                min_lim, max_lim = PANDA_JOINT_LIMITS[i]
                margin_to_min = angle - min_lim
                margin_to_max = max_lim - angle
                min_margin = min(margin_to_min, margin_to_max)
                status = "OK"
                if min_margin < 0.1:
                    status = "⚠️ NEAR LIMIT"
                if min_margin < 0.05:
                    status = "❌ AT LIMIT"
                print(f"joint{i+1:<3} {angle_deg:>10.1f}°  {math.degrees(min_lim):>8.1f}°  {math.degrees(max_lim):>8.1f}°  {math.degrees(min_margin):>8.1f}°  {status}")

            # Settle to let cable stabilize
            self.step_sim(50)

            # Validate reach before proceeding
            reach_ok, error_msg = self.validate_reach()
            if not reach_ok:
                print(f"  [REACH FAILED] {error_msg}")
                raise RuntimeError(f"Reach validation failed: {error_msg}")

            # Position comparison: gripper vs cable end
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
            cable_pos = self.cable.data.body_pos_w[0]
            seg_0 = cable_pos[0]
            seg_9 = cable_pos[-1]

            print(f"\n{'='*60}")
            print(f"[POSITION COMPARISON]")
            print(f"")
            print(f"Left side:")
            print(f"  seg_0 (cable end):  X={seg_0[0].item():.4f}, Y={seg_0[1].item():.4f}")
            print(f"  Left EE:            X={left_ee[0,0].item():.4f}, Y={left_ee[0,1].item():.4f}")
            print(f"  Difference:         dX={abs(seg_0[0].item()-left_ee[0,0].item()):.4f}, dY={abs(seg_0[1].item()-left_ee[0,1].item()):.4f}")
            print(f"  XY Distance:        {((seg_0[0]-left_ee[0,0])**2 + (seg_0[1]-left_ee[0,1])**2).sqrt().item():.4f}m")
            print(f"")
            print(f"Right side:")
            print(f"  seg_9 (cable end):  X={seg_9[0].item():.4f}, Y={seg_9[1].item():.4f}")
            print(f"  Right EE:           X={right_ee[0,0].item():.4f}, Y={right_ee[0,1].item():.4f}")
            print(f"  Difference:         dX={abs(seg_9[0].item()-right_ee[0,0].item()):.4f}, dY={abs(seg_9[1].item()-right_ee[0,1].item()):.4f}")
            print(f"  XY Distance:        {((seg_9[0]-right_ee[0,0])**2 + (seg_9[1]-right_ee[0,1])**2).sqrt().item():.4f}m")
            print(f"{'='*60}\n")

        elif phase == TaskPhase.GRASP_CABLE:
            # === DETAILED POSITION DEBUG ===
            print("\n" + "="*60)
            print("[Phase 2 DEBUG] Position Analysis at Phase 2 Start")
            print("="*60)

            # Get positions (EE = panda_hand frame)
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
            cable_left, cable_right = self.get_cable_ends()

            # Fingertip positions (10.7cm below panda_hand when pointing down)
            FINGERTIP_OFFSET = 0.1123
            left_fingertip = left_ee[0].clone()
            left_fingertip[2] -= FINGERTIP_OFFSET
            right_fingertip = right_ee[0].clone()
            right_fingertip[2] -= FINGERTIP_OFFSET

            # Calculate XY distances (horizontal plane only) - fingertip to cable END
            left_xy_dist = torch.sqrt(
                (left_fingertip[0] - cable_left[0])**2 +
                (left_fingertip[1] - cable_left[1])**2
            ).item()
            right_xy_dist = torch.sqrt(
                (right_fingertip[0] - cable_right[0])**2 +
                (right_fingertip[1] - cable_right[1])**2
            ).item()

            # Calculate target positions (3cm inward from cable ends)
            # Y-axis cable: seg_17 (left) at MIN Y, seg_19 (right) at MAX Y
            left_target_x = cable_left[0].item()  # Keep X at cable position
            right_target_x = cable_right[0].item()  # Keep X at cable position
            left_target_y = cable_left[1].item() + GRASP_INWARD_OFFSET  # Move toward center (+Y)
            right_target_y = cable_right[1].item() - GRASP_INWARD_OFFSET  # Move toward center (-Y)

            # Calculate distance from TARGET position (for alignment check)
            left_target_dist = torch.sqrt(
                (left_fingertip[0] - left_target_x)**2 +
                (left_fingertip[1] - left_target_y)**2
            ).item()
            right_target_dist = torch.sqrt(
                (right_fingertip[0] - right_target_x)**2 +
                (right_fingertip[1] - right_target_y)**2
            ).item()

            # Calculate Z distances (height) - fingertip to cable
            left_z_dist = (left_fingertip[2] - cable_left[2]).item()
            right_z_dist = (right_fingertip[2] - cable_right[2]).item()

            print(f"\n[Left Gripper]")
            print(f"  Fingertip Pos:   X={left_fingertip[0].item():.4f}, Y={left_fingertip[1].item():.4f}, Z={left_fingertip[2].item():.4f}")
            print(f"  Cable End:       X={cable_left[0].item():.4f}, Y={cable_left[1].item():.4f}, Z={cable_left[2].item():.4f}")
            print(f"  Target (3cm in): X={left_target_x:.4f}, Y={left_target_y:.4f}")
            # Distance from END (~3cm expected due to inward offset)
            print(f"  Dist from END:   {left_xy_dist:.4f}m ({left_xy_dist*100:.1f}cm)  {'✅ OK' if left_xy_dist < 0.035 else '❌ TOO FAR'}")
            # Distance from TARGET (should be <0.5cm for good alignment)
            print(f"  Dist from TARGET:{left_target_dist:.4f}m ({left_target_dist*100:.1f}cm)  {'✅ ALIGNED' if left_target_dist < 0.005 else '⚠️ needs align'}")
            print(f"  Z Distance:      {left_z_dist:.4f}m (fingertip is {left_z_dist*100:.1f}cm above cable)")

            print(f"\n[Right Gripper]")
            print(f"  Fingertip Pos:   X={right_fingertip[0].item():.4f}, Y={right_fingertip[1].item():.4f}, Z={right_fingertip[2].item():.4f}")
            print(f"  Cable End:       X={cable_right[0].item():.4f}, Y={cable_right[1].item():.4f}, Z={cable_right[2].item():.4f}")
            print(f"  Target (3cm in): X={right_target_x:.4f}, Y={right_target_y:.4f}")
            # Distance from END (~3cm expected due to inward offset)
            print(f"  Dist from END:   {right_xy_dist:.4f}m ({right_xy_dist*100:.1f}cm)  {'✅ OK' if right_xy_dist < 0.035 else '❌ TOO FAR'}")
            # Distance from TARGET (should be <0.5cm for good alignment)
            print(f"  Dist from TARGET:{right_target_dist:.4f}m ({right_target_dist*100:.1f}cm)  {'✅ ALIGNED' if right_target_dist < 0.005 else '⚠️ needs align'}")
            print(f"  Z Distance:      {right_z_dist:.4f}m (fingertip is {right_z_dist*100:.1f}cm above cable)")

            print(f"\n[Summary]")
            print(f"  Target pos accuracy: Left={left_target_dist*100:.1f}cm, Right={right_target_dist*100:.1f}cm (target<0.5cm)")
            print(f"  Cable end distance: Left={left_xy_dist*100:.1f}cm, Right={right_xy_dist*100:.1f}cm (expected~3cm)")
            print(f"  Z height:  Left={left_z_dist*100:.1f}cm, Right={right_z_dist*100:.1f}cm above cable")

            if left_target_dist < 0.005 and right_target_dist < 0.005:
                print(f"  Conclusion: ✅ Reached target position - grasp possible")
            elif left_xy_dist < 0.035 and right_xy_dist < 0.035:
                print(f"  Conclusion: ⚠️ Cable end distance OK - grasp possible with fine adjustment")
            else:
                print(f"  Conclusion: ❌ XY position offset - Phase 1 target position correction needed")
            print("="*60 + "\n")
            # === END DEBUG ===

            # === FINAL ALIGNMENT STEP ===
            # Check if grippers need alignment to target position (3cm inward from cable ends)
            # Threshold: 0.5cm tolerance from target position
            if left_target_dist > 0.005 or right_target_dist > 0.005:
                print(f"  [Alignment] Target offset detected (left={left_target_dist*100:.1f}cm, right={right_target_dist*100:.1f}cm)")
                print(f"  [Alignment] Re-aligning grippers to current cable position...")

                # Y-axis cable: Apply inward offset to Y, keep X at cable position
                # seg_17 (left) at MIN Y: move +Y (toward center)
                # seg_19 (right) at MAX Y: move -Y (toward center)
                left_align_x = cable_left[0].item()  # Keep X at cable position
                right_align_x = cable_right[0].item()  # Keep X at cable position
                left_align_y = cable_left[1].item() + GRASP_INWARD_OFFSET  # Move toward center (+Y)
                right_align_y = cable_right[1].item() - GRASP_INWARD_OFFSET  # Move toward center (-Y)
                print(f"    [X unchanged] Left X: {left_align_x:.4f}, Right X: {right_align_x:.4f}")
                print(f"    [Offset] Left Y: {cable_left[1].item():.4f} -> {left_align_y:.4f}")
                print(f"    [Offset] Right Y: {cable_right[1].item():.4f} -> {right_align_y:.4f}")

                # CRITICAL: Lower fingertips to cable center height for proper grasp
                # Previously kept current Z which was 1-2cm above cable, causing grippers
                # to close above the cable instead of around it
                left_align_fingertip = torch.tensor([
                    [left_align_x, left_align_y, cable_left[2].item()]  # Use cable Z for proper grasp
                ], device=self.device)
                right_align_fingertip = torch.tensor([
                    [right_align_x, right_align_y, cable_right[2].item()]  # Use cable Z for proper grasp
                ], device=self.device)

                # Convert to panda_hand targets
                left_align_target = self.fingertip_to_panda_hand(left_align_fingertip)
                right_align_target = self.fingertip_to_panda_hand(right_align_fingertip)

                print(f"    New left fingertip target: {left_align_fingertip[0].cpu().tolist()}")
                print(f"    New right fingertip target: {right_align_fingertip[0].cpu().tolist()}")

                # Move to aligned position (increased from 100 to 300 steps for better convergence)
                reached = self.move_to_target(left_align_target, right_align_target, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=300)
                print(f"  [Alignment] Reached aligned position: {reached}")

                # Update positions for debug
                left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
                right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
                left_fingertip_new = left_ee[0].clone()
                left_fingertip_new[2] -= FINGERTIP_OFFSET
                right_fingertip_new = right_ee[0].clone()
                right_fingertip_new[2] -= FINGERTIP_OFFSET

                # Recalculate target distances after alignment
                left_target_dist_new = torch.sqrt(
                    (left_fingertip_new[0] - left_target_x)**2 +
                    (left_fingertip_new[1] - left_target_y)**2
                ).item()
                right_target_dist_new = torch.sqrt(
                    (right_fingertip_new[0] - right_target_x)**2 +
                    (right_fingertip_new[1] - right_target_y)**2
                ).item()
                print(f"  [Alignment] After: Left={left_target_dist_new*100:.1f}cm, Right={right_target_dist_new*100:.1f}cm (target<0.5cm)")

            # Stabilize before grasp
            print(f"  Stabilizing before grasp...")
            self.step_sim(50)

            print(f"  Closing grippers slowly...")
            self.close_grippers_slowly(GRIPPER_CLOSED, steps=200)  # Reduced from 500 for faster test

            # Settle to let physics stabilize
            self.step_sim(100)  # Terminal 3: Increased from 50

            # Create D6 joint grasp constraints (optional)
            # D6 joints physically attach the cable to the gripper for stability
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
            cable_left, cable_right = self.get_cable_ends()

            # Calculate fingertip positions (EE is panda_hand, fingertip is 10.7cm below)
            FINGERTIP_OFFSET = 0.1123  # panda_hand to fingertip offset
            left_fingertip_pos = left_ee[0].clone()
            left_fingertip_pos[2] -= FINGERTIP_OFFSET
            right_fingertip_pos = right_ee[0].clone()
            right_fingertip_pos[2] -= FINGERTIP_OFFSET

            # Calculate 3D distance between fingertip and cable
            left_3d_dist = torch.norm(left_fingertip_pos - cable_left).item()
            right_3d_dist = torch.norm(right_fingertip_pos - cable_right).item()

            # Log detailed position info
            print(f"  [Grasp Position Check]")
            print(f"    Left panda_hand (EE):  {left_ee[0].cpu().tolist()}")
            print(f"    Left fingertip:        [{left_fingertip_pos[0].item():.4f}, {left_fingertip_pos[1].item():.4f}, {left_fingertip_pos[2].item():.4f}]")
            print(f"    Left cable (seg_{self._left_seg_idx}):     {cable_left.cpu().tolist()}")
            print(f"    Left 3D distance:      {left_3d_dist:.4f}m")
            print(f"    Right panda_hand (EE): {right_ee[0].cpu().tolist()}")
            print(f"    Right fingertip:       [{right_fingertip_pos[0].item():.4f}, {right_fingertip_pos[1].item():.4f}, {right_fingertip_pos[2].item():.4f}]")
            print(f"    Right cable (seg_{self._right_seg_idx}):    {cable_right.cpu().tolist()}")
            print(f"    Right 3D distance:     {right_3d_dist:.4f}m")

            # D6 joint distance threshold
            D6_JOINT_MAX_DISTANCE = 0.05  # 5cm max for safe D6 joint creation

            if self.skip_d6_joints:
                print(f"  Skipping D6 joint creation (friction grasp only mode)")
            elif left_3d_dist > D6_JOINT_MAX_DISTANCE or right_3d_dist > D6_JOINT_MAX_DISTANCE:
                print(f"  [WARNING] 3D distance too large for D6 joint!")
                print(f"    Left: {left_3d_dist:.4f}m, Right: {right_3d_dist:.4f}m (threshold: {D6_JOINT_MAX_DISTANCE}m)")
                print(f"    Falling back to friction grasp only (skipping D6 joints)")
                self.skip_d6_joints = True  # Auto-disable D6 joints for this run
            else:
                print(f"  Creating D6 joint grasp constraints...")
                print(f"    3D distances OK: Left={left_3d_dist:.4f}m, Right={right_3d_dist:.4f}m")

                # Get prim paths for D6 joint
                left_gripper_path = self.gripper_paths["left"]
                right_gripper_path = self.gripper_paths["right"]
                left_cable_path = get_cable_segment_prim_path(0, self._left_seg_idx)
                right_cable_path = get_cable_segment_prim_path(0, self._right_seg_idx)

                # Fingertip offset from panda_hand (0.1123m along local Z)
                # This places the D6 joint attachment at the fingertip position
                fingertip_offset = (0.0, 0.0, 0.1123)

                # Calculate cable-side offset to match fingertip position
                # local_pos1 = fingertip_world - cable_world (in cable's local frame, assuming ~world aligned)
                left_cable_offset = (left_fingertip_pos - cable_left).cpu().numpy()
                right_cable_offset = (right_fingertip_pos - cable_right).cpu().numpy()

                print(f"    Creating D6 joint: {left_gripper_path} <-> {left_cable_path}")
                print(f"      Gripper offset (local_pos0): {fingertip_offset}")
                print(f"      Cable offset (local_pos1): [{left_cable_offset[0]:.4f}, {left_cable_offset[1]:.4f}, {left_cable_offset[2]:.4f}]")
                self.grasp_manager.create_grasp("left", left_gripper_path, left_cable_path,
                                                local_pos0=fingertip_offset,
                                                local_pos1=tuple(left_cable_offset))

                print(f"    Creating D6 joint: {right_gripper_path} <-> {right_cable_path}")
                print(f"      Gripper offset (local_pos0): {fingertip_offset}")
                print(f"      Cable offset (local_pos1): [{right_cable_offset[0]:.4f}, {right_cable_offset[1]:.4f}, {right_cable_offset[2]:.4f}]")
                self.grasp_manager.create_grasp("right", right_gripper_path, right_cable_path,
                                                local_pos0=fingertip_offset,
                                                local_pos1=tuple(right_cable_offset))

            # Settle after grasp
            self.step_sim(50)

            # ALWAYS save images before validation (for debugging failed attempts)
            print("  [DEBUG] Saving Phase 2 images before validation...")
            debug_images = self.get_camera_images()
            self.save_phase_images(phase, debug_images)

            # Validate grasp before proceeding (distance-based check)
            grasp_ok, error_msg = self.validate_grasp()
            if not grasp_ok:
                print(f"  [GRASP FAILED] {error_msg}")
                print(f"  Aborting task - cannot proceed without valid grasp")
                raise RuntimeError(f"Grasp validation failed: {error_msg}")

            # CRITICAL: Physical lift test - verify cable actually moves with grippers
            # This is the definitive test - distance metrics alone can't confirm physical grasp
            # Note: Using small lift (1cm) to avoid physics instability with articulated cable
            lift_ok, lift_error = self.verify_grasp_by_lifting(lift_height=0.01)
            if not lift_ok:
                print(f"  [LIFT TEST FAILED] {lift_error}")
                print(f"  Aborting task - grippers closed but did not grasp cable")
                raise RuntimeError(f"Lift verification failed: {lift_error}")

            grasp_type = "friction grasp" if self.skip_d6_joints else "D6 joints"
            print(f"  Grasp complete and verified by lift test ({grasp_type} active)")

        elif phase == TaskPhase.LIFT_CABLE:
            # Coordinated lift: both grippers move to SAME height simultaneously
            # This prevents cable from being pulled apart

            # Get current EE positions
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

            # Target: same lift height for both grippers
            # CRITICAL: Must lift above hook to avoid collision during TRANSPORT
            # Hook max Z = 0.91 (arm tips), need 5cm clearance = 0.96
            HOOK_CLEARANCE_HEIGHT = 0.96  # Hook(0.91) + 5cm margin

            # Use the higher of: hook clearance height OR current position + 5cm
            current_max_z = max(left_ee[0, 2].item(), right_ee[0, 2].item())
            lift_height = max(HOOK_CLEARANCE_HEIGHT, current_max_z + 0.05)

            # Keep X and Y positions, only change Z
            left_target = left_ee.clone()
            left_target[0, 2] = lift_height
            right_target = right_ee.clone()
            right_target[0, 2] = lift_height

            print(f"  Coordinated lift to Z={lift_height:.3f}...")
            print(f"    Left: {left_ee[0].cpu().tolist()} -> {left_target[0].cpu().tolist()}")
            print(f"    Right: {right_ee[0].cpu().tolist()} -> {right_target[0].cpu().tolist()}")

            self.move_to_target(left_target, right_target, GRIPPER_CLOSED, GRIPPER_CLOSED, max_steps=300)

            # Settle
            self.step_sim(50)

            # CRITICAL: Verify cable is still held after lift
            grasp_ok, error_msg = self.validate_grasp()
            if not grasp_ok:
                print(f"  [LIFT PHASE FAILED] Lost grasp during lift: {error_msg}")
                raise RuntimeError(f"Lost grasp during LIFT_CABLE: {error_msg}")
            print(f"  [LIFT PHASE OK] Cable still held by both grippers")

            # === Phase 3 End Position Data (for Phase 4 planning) ===
            cable_pos = self.cable.data.body_pos_w[0]
            seg7 = cable_pos[LEFT_CLAMP_SEGMENT].cpu()
            seg8 = cable_pos[RIGHT_CLAMP_SEGMENT].cpu()
            left_ee_p3, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee_p3, _ = self.controller.get_ee_pose(self.controller.robot_right)
            hook = self.hook_v_pos.cpu()

            print("\n" + "=" * 60)
            print("=== Phase 3 End Position Data ===")
            print("=" * 60)
            print(f"  seg_7 (left clamp):  X={seg7[0]:.4f}, Y={seg7[1]:.4f}, Z={seg7[2]:.4f}")
            print(f"  seg_8 (right clamp): X={seg8[0]:.4f}, Y={seg8[1]:.4f}, Z={seg8[2]:.4f}")
            print(f"  Left EE:             X={left_ee_p3[0,0]:.4f}, Y={left_ee_p3[0,1]:.4f}, Z={left_ee_p3[0,2]:.4f}")
            print(f"  Right EE:            X={right_ee_p3[0,0]:.4f}, Y={right_ee_p3[0,1]:.4f}, Z={right_ee_p3[0,2]:.4f}")
            print(f"  Hook V:              X={hook[0]:.4f}, Y={hook[1]:.4f}, Z={hook[2]:.4f}")

            # Distance calculations
            import math
            cable_span = math.sqrt((seg8[0] - seg7[0])**2 + (seg8[1] - seg7[1])**2)
            left_to_hook = math.sqrt((seg7[0] - hook[0])**2 + (seg7[1] - hook[1])**2)
            right_to_hook = math.sqrt((seg8[0] - hook[0])**2 + (seg8[1] - hook[1])**2)
            cable_center_x = (seg7[0] + seg8[0]) / 2
            cable_center_y = (seg7[1] + seg8[1]) / 2
            center_to_hook = math.sqrt((cable_center_x - hook[0])**2 + (cable_center_y - hook[1])**2)

            print(f"\n  === Distance Analysis ===")
            print(f"  Cable span (seg7-seg8):    {cable_span:.4f}m")
            print(f"  Left (seg7) → Hook:        {left_to_hook:.4f}m")
            print(f"  Right (seg8) → Hook:       {right_to_hook:.4f}m")
            print(f"  Cable center:              X={cable_center_x:.4f}, Y={cable_center_y:.4f}")
            print(f"  Cable center → Hook:       {center_to_hook:.4f}m")

            # Check if rotation is feasible
            max_reach = 0.855  # Franka max reach
            print(f"\n  === Rotation Feasibility Check ===")
            print(f"  After 90° rotation around hook:")
            # After rotation: left at X+offset, right at X-offset, both at Y=hook_y
            rot_offset = 0.15
            rot_left_x = hook[0] + rot_offset
            rot_right_x = hook[0] - rot_offset
            rot_y = hook[1]
            print(f"    Left target:  X={rot_left_x:.4f}, Y={rot_y:.4f}")
            print(f"    Right target: X={rot_right_x:.4f}, Y={rot_y:.4f}")

            # Distance from robot bases to rotated targets
            left_base = torch.tensor([0.0, -0.20, 1.30])  # From dual_arm_cfg
            right_base = torch.tensor([0.0, 0.25, 1.30])
            left_rot_dist = math.sqrt((rot_left_x - left_base[0])**2 + (rot_y - left_base[1])**2 + (left_ee_p3[0,2] - left_base[2])**2)
            right_rot_dist = math.sqrt((rot_right_x - right_base[0])**2 + (rot_y - right_base[1])**2 + (right_ee_p3[0,2] - right_base[2])**2)
            print(f"    Left arm reach to target:  {left_rot_dist:.4f}m (max: {max_reach}m) {'⚠️ EXCEED!' if left_rot_dist > max_reach else '✅ OK'}")
            print(f"    Right arm reach to target: {right_rot_dist:.4f}m (max: {max_reach}m) {'⚠️ EXCEED!' if right_rot_dist > max_reach else '✅ OK'}")
            print("=" * 60 + "\n")

        elif phase == TaskPhase.TRANSPORT:
            # ================================================================
            # TRANSPORT: Move cable horizontally while maintaining grasp
            # Simplified from ROTATE_CABLE to avoid D6 joint limitations
            # ================================================================
            print("=" * 60)
            print("=== Phase 4 (TRANSPORT) Start ===")
            print("=" * 60)

            # D6 joint status
            d6_left_active = self.grasp_manager.is_grasping("left")
            d6_right_active = self.grasp_manager.is_grasping("right")
            print(f"  D6 Joint Status: Left={d6_left_active}, Right={d6_right_active}")

            # Get current positions
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
            cable_pos = self.cable.data.body_pos_w[0]
            seg7_before = cable_pos[LEFT_CLAMP_SEGMENT].cpu()
            seg8_before = cable_pos[RIGHT_CLAMP_SEGMENT].cpu()

            print(f"  Start positions:")
            print(f"    Left EE:  {left_ee[0].cpu().tolist()}")
            print(f"    Right EE: {right_ee[0].cpu().tolist()}")
            print(f"    seg_7:    Z={seg7_before[2]:.4f}m")
            print(f"    seg_8:    Z={seg8_before[2]:.4f}m")

            # Transport parameters: move backward (negative X direction)
            # This is a simple horizontal translation, no rotation
            TRANSPORT_DELTA_X = -0.15  # 15cm backward
            TRANSPORT_DELTA_Y = 0.0    # Maintain Y position

            # Target positions
            left_target = left_ee.clone()
            left_target[0, 0] += TRANSPORT_DELTA_X
            left_target[0, 1] += TRANSPORT_DELTA_Y

            right_target = right_ee.clone()
            right_target[0, 0] += TRANSPORT_DELTA_X
            right_target[0, 1] += TRANSPORT_DELTA_Y

            print(f"\n  Transport: moving {abs(TRANSPORT_DELTA_X)*100:.0f}cm backward")
            print(f"    Left:  {left_ee[0].cpu().tolist()} -> {left_target[0].cpu().tolist()}")
            print(f"    Right: {right_ee[0].cpu().tolist()} -> {right_target[0].cpu().tolist()}")

            # Smooth interpolated movement
            max_steps = 200
            sim_steps_per_move = 10
            for step in range(max_steps):
                t = (step + 1) / max_steps
                current_left = left_ee + t * (left_target - left_ee)
                current_right = right_ee + t * (right_target - right_ee)

                self.controller.set_targets(
                    current_left, current_right,
                    GRIPPER_CLOSED, GRIPPER_CLOSED,
                    use_fixed_orientation=True
                )
                self.step_sim(sim_steps_per_move)

                # Progress monitoring
                if step % 50 == 0 or step == max_steps - 1:
                    cable_pos = self.cable.data.body_pos_w[0]
                    seg7 = cable_pos[LEFT_CLAMP_SEGMENT].cpu()
                    seg8 = cable_pos[RIGHT_CLAMP_SEGMENT].cpu()
                    print(f"    Step {step:3d}/{max_steps}: "
                          f"seg7_Z={seg7[2]:.3f}m, seg8_Z={seg8[2]:.3f}m")

                    # Check for cable drop
                    if seg7[2] < 0.80 or seg8[2] < 0.80:
                        print(f"    ⚠️ WARNING: Cable sagging! Check D6 joint")

            # Settle
            self.step_sim(50)

            # End state
            print(f"\n  === Phase 4 End State ===")
            cable_pos_end = self.cable.data.body_pos_w[0]
            seg7_end = cable_pos_end[LEFT_CLAMP_SEGMENT].cpu()
            seg8_end = cable_pos_end[RIGHT_CLAMP_SEGMENT].cpu()
            left_ee_end, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee_end, _ = self.controller.get_ee_pose(self.controller.robot_right)

            print(f"    Left EE final:  {left_ee_end[0].cpu().tolist()}")
            print(f"    Right EE final: {right_ee_end[0].cpu().tolist()}")
            print(f"    seg_7 Z: {seg7_end[2]:.4f}m")
            print(f"    seg_8 Z: {seg8_end[2]:.4f}m")

            # Verify cable stayed elevated
            if seg7_end[2] < 0.80 or seg8_end[2] < 0.80:
                print(f"    ⚠️ Cable sagged during transport")
            else:
                print(f"    ✅ Transport completed successfully")
            print("=" * 60)

        elif phase == TaskPhase.RELEASE:
            # Release grasp constraints first
            print(f"  Releasing grasp constraints...")
            self.grasp_manager.release_all()

            # Settle briefly
            self.step_sim(10)

            # Open grippers
            print(f"  Opening grippers...")
            self.open_grippers_slowly(GRIPPER_OPEN, steps=80)

            # Settle to let cable fall
            self.step_sim(100)

            # Retreat upward and backward (cable is along Y-axis)
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

            left_target = left_ee.clone()
            left_target[0, 2] += 0.10  # Lift up

            right_target = right_ee.clone()
            right_target[0, 2] += 0.10  # Lift up

            self.move_to_target(left_target, right_target, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=100)

        elif phase == TaskPhase.DONE:
            # Retreat to home position
            left_home = torch.tensor([[0.2, -0.35, 1.1]], device=self.device)
            right_home = torch.tensor([[0.2, 0.35, 1.1]], device=self.device)

            print(f"  Retreating to home...")
            self.move_to_target(left_home, right_home, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=300)

            # Final settle
            self.step_sim(50)

        # Capture and save images
        images = self.get_camera_images()
        self.save_phase_images(phase, images)

        # Print final positions
        left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
        right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
        cable_left, cable_right = self.get_cable_ends()

        print(f"  Final Left EE: {left_ee[0].cpu().tolist()}")
        print(f"  Final Right EE: {right_ee[0].cpu().tolist()}")
        print(f"  Cable left end: {cable_left.cpu().tolist()}")
        print(f"  Cable right end: {cable_right.cpu().tolist()}")

        return True

    def full_sim_reset(self):
        """Perform full simulation reset to clear corrupted physics state.

        This is necessary when physics becomes unstable (NaN values).
        A simple write_root_state_to_sim() doesn't recover from corrupted state.
        """
        print("[Full Reset] Performing full simulation reset...")

        # Release any active grasps first
        self.grasp_manager.release_all()

        # Full simulation reset
        self.sim.reset()

        # Re-apply high friction materials (cleared by reset)
        apply_high_friction_materials()

        # Re-set the D6GraspManager stage
        stage = sim_utils.get_current_stage()
        self.grasp_manager.set_stage(stage)

        # CRITICAL: Update scene FIRST to refresh all data references
        self.scene.update(self.sim.get_physics_dt())

        # Warm up simulation with scene updates at each step
        print("[Full Reset] Warming up simulation...")
        for i in range(50):
            self.scene.write_data_to_sim()
            self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

        # Verify physics health after warm-up
        is_healthy, error_msg = self.check_physics_health()
        if not is_healthy:
            print(f"[Full Reset] WARNING: Physics unhealthy after reset: {error_msg}")
        else:
            print("[Full Reset] Physics healthy after reset")

        # Update hook position reference (may have changed after reset)
        self.hook_pos = self.hook.data.root_pos_w[0].clone()
        self.hook_v_pos = self.hook_pos.clone()
        self.hook_v_pos[2] += 0.07  # V part is 7cm above stem base
        print(f"[Full Reset] Hook position: {self.hook_pos.cpu().tolist()}")

        print("[Full Reset] Complete")

    def collect_all_phases(self) -> bool:
        """Execute all phases and collect goal images with autonomous retry.

        Returns:
            bool: True if all phases completed successfully, False if all retries failed
        """
        # Plan A: X-axis cable layout (-90° around Y)
        # Cable spawns at X=0.52, extends from X≈0.22 to X≈0.82 (60cm cable)
        # Cable center at X≈0.52 (closer to robot for better reach)
        # Use spawn position to avoid cable physics explosion during reset
        x_positions = [0.52]

        print(f"\n{'='*60}")
        print("Goal Image Collection - Cable Manipulation (Autonomous)")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"X positions to try: {x_positions}")

        # Start realtime logging if configured
        self.start_realtime_logging()

        for attempt, x_pos in enumerate(x_positions):
            print(f"\n{'='*60}")
            print(f"ATTEMPT {attempt + 1}/{len(x_positions)}: Cable X = {x_pos:.2f}")
            print(f"{'='*60}")

            # Full simulation reset between attempts to clear corrupted physics state
            # For first attempt, also do a reset to ensure clean state
            if attempt > 0:
                self.full_sim_reset()
            else:
                # First attempt: verify physics is healthy before proceeding
                print("[First Attempt] Verifying initial physics state...")
                is_healthy, error_msg = self.check_physics_health()
                if not is_healthy:
                    print(f"[First Attempt] WARNING: Initial physics unhealthy: {error_msg}")
                    print("[First Attempt] Performing initial reset...")
                    self.full_sim_reset()

            # Reset NaN detection health checker for new attempt
            self.health_checker.reset()
            print(f"[Health] NaN detection health checker reset for attempt {attempt + 1}")

            # Plan A: Skip cable reset to avoid physics explosion
            # Cable will stay at its spawn position (X=0.35 as per dual_arm_cfg.py)
            # The cable articulation reset via write_root_state_to_sim causes instability
            print("[Cable] Using cable at spawn position (no reset)")
            cable_pos = self.cable.data.body_pos_w[0]
            print(f"[Cable] Current cable center: X={cable_pos[:, 0].mean().item():.3f}, "
                  f"Y={cable_pos[:, 1].mean().item():.3f}, Z={cable_pos[:, 2].mean().item():.3f}")

            # Initial warm-up
            print("\n[Setup] Running initial simulation steps...")
            self.step_sim(50)

            # Reset arms to a proper manipulation-ready position
            self.reset_arms_to_ready_position()

            # Execute all phases with error handling
            try:
                for phase in TaskPhase:
                    self.execute_phase(phase)

                # Success!
                print(f"\n{'='*60}")
                print("Collection Complete!")
                print(f"{'='*60}")
                print(f"Output: {self.output_dir}")
                print(f"Successful X position: {x_pos:.2f}")
                print(f"Attempts used: {attempt + 1}/{len(x_positions)}")

                # Stop realtime logging
                self.stop_realtime_logging()

                # Create summary HTML
                self._create_summary()
                return True

            except RuntimeError as e:
                print(f"\n{'='*60}")
                print(f"ATTEMPT {attempt + 1} FAILED: {e}")
                print(f"{'='*60}")

                if attempt < len(x_positions) - 1:
                    print(f"[Auto-Retry] Will try next position: X={x_positions[attempt + 1]:.2f}")
                else:
                    print(f"[FAILED] All {len(x_positions)} positions exhausted.")
                    print(f"Positions tried: {x_positions}")

        # Stop realtime logging before returning
        self.stop_realtime_logging()
        return False

    def _create_summary(self):
        """Create summary HTML file."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Goal Images - Cable Manipulation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        h1 { color: #333; }
        .phase { background: white; margin: 20px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .phase h2 { color: #0066cc; margin-top: 0; }
        .images { display: flex; gap: 10px; flex-wrap: wrap; }
        .images img { width: 200px; height: 200px; object-fit: cover; border: 1px solid #ddd; }
        .composite { width: 400px; height: 400px; }
        .description { color: #666; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>Goal Images - Cable Draping Task</h1>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
"""
        for phase in TaskPhase:
            phase_dir = f"phase_{phase.value}_{phase.name.lower()}"
            phase_prefix = phase_dir  # e.g., "phase_1_reach_cable"
            html_content += f"""
    <div class="phase">
        <h2>Phase {phase.value}: {phase.name}</h2>
        <p class="description">{PHASE_DESCRIPTIONS[phase]}</p>
        <div class="images">
            <div>
                <h4>Front Left</h4>
                <img src="{phase_dir}/{phase_prefix}_front_left.png" alt="Front Left">
            </div>
            <div>
                <h4>Front Right</h4>
                <img src="{phase_dir}/{phase_prefix}_front_right.png" alt="Front Right">
            </div>
            <div>
                <h4>Back</h4>
                <img src="{phase_dir}/{phase_prefix}_back.png" alt="Back">
            </div>
            <div>
                <h4>Overhead</h4>
                <img src="{phase_dir}/{phase_prefix}_overhead.png" alt="Overhead">
            </div>
            <div>
                <h4>Composite</h4>
                <img src="{phase_dir}/{phase_prefix}_composite.png" alt="Composite" class="composite">
            </div>
        </div>
    </div>
"""

        html_content += """
</body>
</html>
"""
        html_file = os.path.join(self.output_dir, "index.html")
        with open(html_file, 'w') as f:
            f.write(html_content)
        print(f"Summary HTML: {html_file}")


# =============================================================================
# Main
# =============================================================================

def apply_high_friction_materials():
    """Apply high friction physics materials to cable and gripper fingers."""
    from pxr import UsdPhysics, UsdShade, Sdf, Usd, UsdGeom

    stage = sim_utils.get_current_stage()

    # Define high friction physics material
    material_path = "/World/Materials/HighFrictionPhys"
    material_prim = stage.DefinePrim(material_path, "Material")
    phys_material = UsdPhysics.MaterialAPI.Apply(material_prim)
    phys_material.CreateStaticFrictionAttr(5.0)
    phys_material.CreateDynamicFrictionAttr(5.0)
    phys_material.CreateRestitutionAttr(0.0)

    print("[Setup] Created high friction physics material (friction=5.0)")

    def bind_physics_material_to_collider(prim):
        """Bind physics material to a prim with collision."""
        # Apply collision API if not already
        if not prim.HasAPI(UsdPhysics.CollisionAPI):
            UsdPhysics.CollisionAPI.Apply(prim)

        # Use UsdShade.MaterialBindingAPI with physics purpose
        binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
        material = UsdShade.Material(material_prim)
        binding_api.Bind(material, UsdShade.Tokens.weakerThanDescendants, "physics")
        return True

    # Apply to cable segments
    cable_applied = 0
    cable_prim = stage.GetPrimAtPath("/World/envs/env_0/Cable")
    if cable_prim:
        for prim in Usd.PrimRange(cable_prim):
            if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Capsule) or prim.IsA(UsdGeom.Cylinder):
                if bind_physics_material_to_collider(prim):
                    cable_applied += 1
    print(f"[Setup] Applied high friction to {cable_applied} cable geometries")

    # Apply to gripper fingers (Note: Robot_Left and Robot_Right are capitalized)
    gripper_applied = 0
    finger_paths = [
        "/World/envs/env_0/Robot_Left/panda_leftfinger",
        "/World/envs/env_0/Robot_Left/panda_rightfinger",
        "/World/envs/env_0/Robot_Right/panda_leftfinger",
        "/World/envs/env_0/Robot_Right/panda_rightfinger",
    ]
    for finger_path in finger_paths:
        finger_prim = stage.GetPrimAtPath(finger_path)
        if finger_prim and finger_prim.IsValid():
            for prim in Usd.PrimRange(finger_prim):
                if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Capsule) or prim.IsA(UsdGeom.Cylinder):
                    if bind_physics_material_to_collider(prim):
                        gripper_applied += 1
    print(f"[Setup] Applied high friction to {gripper_applied} gripper geometries")


def apply_red_cable_material():
    """Apply red material to cable segments."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf
    stage = sim_utils.get_current_stage()
    cable_prim = stage.GetPrimAtPath("/World/envs/env_0/Cable")
    if cable_prim:
        material_path = "/World/Looks/RedCable"
        material = UsdShade.Material.Define(stage, material_path)
        shader = UsdShade.Shader.Define(stage, material_path + "/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.95, 0.1, 0.05))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        for prim in Usd.PrimRange(cable_prim):
            if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Cylinder) or prim.IsA(UsdGeom.Capsule):
                UsdShade.MaterialBindingAPI(prim).Bind(material)
        print("[Setup] Applied RED material to cable")


def main():
    # Setup scene
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = 1

    # Debug: Print joint positions from config
    print(f"[DEBUG] Left arm joint config: {scene_cfg.robot_left.init_state.joint_pos}")
    print(f"[DEBUG] Right arm joint config: {scene_cfg.robot_right.init_state.joint_pos}")

    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    scene = InteractiveScene(scene_cfg)

    # Apply red material to cable before reset
    apply_red_cable_material()

    # Apply high friction materials for physical grasping
    # Note: Call after sim.reset() to avoid initialization issues
    # apply_high_friction_materials()

    sim.reset()

    # Apply high friction AFTER reset for stable physics setup
    apply_high_friction_materials()

    # Initial setup
    print("[Setup] Initializing...")
    for _ in range(30):
        sim.step()
    scene.update(sim.get_physics_dt())

    # Create collector
    collector = GoalImageCollector(
        scene=scene,
        sim=sim,
        output_dir=args_cli.output_dir,
        skip_d6_joints=args_cli.skip_d6_joints,
        realtime_log_dir=args_cli.realtime_log_dir,
    )

    # Set USD stage for D6GraspManager (must be after sim.reset())
    stage = sim_utils.get_current_stage()
    collector.set_stage(stage)

    # Collect goal images
    collector.collect_all_phases()

    # Robust exit: close with timeout, then force exit
    import threading
    import os

    def force_exit():
        print("[EXIT] Forcing exit after timeout...")
        os._exit(0)

    # Start a timer to force exit after 10 seconds
    exit_timer = threading.Timer(10.0, force_exit)
    exit_timer.daemon = True
    exit_timer.start()

    try:
        simulation_app.close()
    except Exception as e:
        print(f"[EXIT] close() failed: {e}")

    exit_timer.cancel()
    os._exit(0)  # Force clean exit


if __name__ == "__main__":
    main()
