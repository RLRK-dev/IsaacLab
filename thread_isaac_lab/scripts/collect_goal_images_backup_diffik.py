#!/usr/bin/env python3
"""
Goal Image Collection Script

Execute cable manipulation (grasp and drape on hook) and
capture goal images for each task phase.

Usage:
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/collect_goal_images.py \
        --headless --enable_cameras

    # GUI mode for visualization
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/collect_goal_images.py \
        --enable_cameras
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
from utils.d6_grasp_manager import D6GraspManager

# Cable segment indices (10-segment articulated cable)
CABLE_BASE_IDX = 0   # First segment (left end when lying along Y-axis)
CABLE_TIP_IDX = 9    # Last segment (right end)


# =============================================================================
# Grasp Prim Paths
# =============================================================================

def get_gripper_prim_paths(env_idx: int = 0) -> Dict[str, str]:
    """Get gripper prim paths for D6GraspManager.

    Returns:
        Dict with left and right gripper paths
    """
    return {
        "left": f"/World/envs/env_{env_idx}/Robot_Left/panda_leftfinger",
        "right": f"/World/envs/env_{env_idx}/Robot_Right/panda_leftfinger",
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
    """8-phase task state machine for cable draping."""
    REACH_CABLE = 1      # EE reaches cable ends
    GRASP_CABLE = 2      # Gripper grasps cable
    LIFT_CABLE = 3       # Cable lifted above table
    ROTATE_CABLE = 4     # Rotate cable 90° (Y-axis -> X-axis)
    APPROACH_HOOK = 5    # EE reaches hook position
    DRAPE_ON_HOOK = 6    # Cable draped on hook
    RELEASE = 7          # Gripper released
    DONE = 8             # Task complete


PHASE_DESCRIPTIONS = {
    TaskPhase.REACH_CABLE: "Both hands approach cable ends",
    TaskPhase.GRASP_CABLE: "Grippers grasp cable",
    TaskPhase.LIFT_CABLE: "Lift cable from table",
    TaskPhase.ROTATE_CABLE: "Rotate cable 90 degrees to X-axis",
    TaskPhase.APPROACH_HOOK: "Approach hook",
    TaskPhase.DRAPE_ON_HOOK: "Drape cable on hook",
    TaskPhase.RELEASE: "Release grippers",
    TaskPhase.DONE: "Task complete - retreat",
}


# =============================================================================
# Constants
# =============================================================================

GRIPPER_OPEN = 0.04
GRIPPER_CLOSED = 0.002  # Squeeze cable (diameter 0.01m) tightly for friction grip

# Grasp validation
LEFT_CLAMP_SEGMENT = 0   # seg_0 grasped by left hand
RIGHT_CLAMP_SEGMENT = 9  # seg_9 grasped by right hand
GRASP_DISTANCE_THRESHOLD = 0.03  # Grasp success within 3cm (aggressive approach: loose threshold)


# =============================================================================
# Dual Arm Controller
# =============================================================================

class DualArmController:
    """Controller for both arms with IK and gripper control."""

    def __init__(self, scene: InteractiveScene, device: str):
        self.scene = scene
        self.device = device

        # IK configuration - position-only control for simpler convergence
        # This ignores orientation constraints and only moves to target position
        ik_cfg = DifferentialIKControllerCfg(
            command_type="position",  # Position-only control (no orientation)
            use_relative_mode=False,
            ik_method="dls",
            ik_params={"lambda_val": 0.05},  # Lower value for tighter position control
        )

        self.left_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)
        self.right_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)

        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        # Resolve body and joint indices using robot API
        body_ids, _ = self.robot_left.find_bodies("panda_hand")
        self.ee_body_idx = body_ids[0]
        # For fixed base robot, jacobian index is body_idx - 1
        self.jacobi_body_idx = self.ee_body_idx - 1

        joint_ids, _ = self.robot_left.find_joints("panda_joint.*")
        self.arm_joint_ids = list(joint_ids)
        self.gripper_joint_ids = [7, 8]

        # EE offset from panda_hand to gripper fingertips (10.7cm in Z)
        # This is critical for IK - panda_hand is the palm, not the fingertips
        self.ee_offset = torch.tensor([[0.0, 0.0, 0.107]], device=device)
        # Identity quaternion (wxyz) for offset transform - pure translation, no rotation
        self.identity_quat_wxyz = torch.tensor([[1.0, 0.0, 0.0, 0.0]], device=device)

        # Default orientation: gripper pointing down (180° around X axis)
        # ケーブルがY軸方向に配置されているため、Z軸回転は不要
        # IKはワールド座標系で目標姿勢を受け取る
        final_rot = R.from_euler('x', 180, degrees=True)
        quat_xyzw = final_rot.as_quat()  # scipy returns [x, y, z, w]
        quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]  # Convert to [w, x, y, z]
        # Expected: [0, 1, 0, 0] (w, x, y, z)
        print(f"[Controller] Gripper quaternion (wxyz): {quat_wxyz}")
        self.default_quat = torch.tensor([quat_wxyz], device=device)

        # Debug: Print initial joint positions and EE positions
        print(f"[Controller] Left arm joint pos: {self.robot_left.data.joint_pos[0, :7].cpu().tolist()}")
        print(f"[Controller] Right arm joint pos: {self.robot_right.data.joint_pos[0, :7].cpu().tolist()}")
        left_ee, _ = self.get_ee_pose(self.robot_left)
        right_ee, _ = self.get_ee_pose(self.robot_right)
        print(f"[Controller] Left EE (world): {left_ee[0].cpu().tolist()}")
        print(f"[Controller] Right EE (world): {right_ee[0].cpu().tolist()}")

    def get_ee_pose(self, robot) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get current EE position and quaternion in world frame.

        Returns panda_hand position (not fingertip) since we control panda_hand with IK.
        The 10.7cm offset to fingertips is handled by adjusting targets.
        """
        ee_pos_w = robot.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat_w = robot.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos_w, ee_quat_w

    def get_fingertip_offset_world(self) -> float:
        """Get the Z offset from panda_hand to fingertip in world frame.

        When gripper points down (180° around X), local +Z becomes world -Z.
        So fingertip is 10.7cm BELOW panda_hand in world frame.
        To reach fingertip position Z, panda_hand should be at Z + 0.107.
        """
        return 0.107

    def compute_ik(self, robot, ik_controller, target_pos, target_quat=None, debug=False):
        """Compute joint positions for target EE pose.

        For position-only control mode, target_quat is ignored.
        """
        joint_pos = robot.data.joint_pos[:, self.arm_joint_ids]
        jacobian = robot.root_physx_view.get_jacobians()[:, self.jacobi_body_idx, :, self.arm_joint_ids]
        ee_pos_w, ee_quat_w = self.get_ee_pose(robot)

        root_pos_w = robot.data.root_pos_w
        root_quat_w = robot.data.root_quat_w

        ee_pos_b, ee_quat_b = subtract_frame_transforms(
            root_pos_w, root_quat_w, ee_pos_w, ee_quat_w
        )
        # Transform target position to robot base frame
        target_pos_b, _ = subtract_frame_transforms(
            root_pos_w, root_quat_w, target_pos, ee_quat_w  # Use current orientation for transform
        )

        if debug:
            pos_error = torch.norm(target_pos_b - ee_pos_b).item()
            print(f"      [IK Debug] Position error: {pos_error:.4f}m")

        # For position-only control, command is 3D position but ee_quat is still needed
        command = target_pos_b
        ik_controller.reset()
        ik_controller.set_command(command, ee_quat=ee_quat_b)

        try:
            result = ik_controller.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

            # Clamp joint delta to prevent very large jumps
            joint_delta = result - joint_pos
            max_delta = 0.3  # Max radians per step (increased for faster convergence)
            joint_delta_clamped = torch.clamp(joint_delta, -max_delta, max_delta)
            result = joint_pos + joint_delta_clamped

            if debug:
                delta_norm = torch.norm(joint_delta).item()
                clamped_norm = torch.norm(joint_delta_clamped).item()
                if delta_norm > clamped_norm * 1.1:  # If clamping was significant
                    print(f"      [IK Debug] Joint delta clamped: {delta_norm:.4f} -> {clamped_norm:.4f}")
                else:
                    print(f"      [IK Debug] Joint delta: {clamped_norm:.4f}")
            return result
        except Exception as e:
            # Return current joint positions if IK fails (singularity)
            print(f"    [IK Warning] Singularity detected, using current position: {e}")
            return joint_pos

    def set_targets(
        self,
        left_pos: Optional[torch.Tensor],
        right_pos: Optional[torch.Tensor],
        left_gripper: float,
        right_gripper: float,
        debug: bool = False,
        use_fixed_orientation: bool = False,
    ):
        """Set arm targets and gripper positions.

        Args:
            use_fixed_orientation: If True, use default_quat (gripper pointing down).
                                   If False, use current EE orientation (position-only).
        """
        target_quat = self.default_quat if use_fixed_orientation else None

        # Left arm
        if left_pos is not None:
            left_joint = self.compute_ik(self.robot_left, self.left_ik, left_pos,
                                         target_quat=target_quat, debug=debug)
        else:
            left_joint = self.robot_left.data.joint_pos[:, self.arm_joint_ids]

        # Right arm
        if right_pos is not None:
            right_joint = self.compute_ik(self.robot_right, self.right_ik, right_pos,
                                          target_quat=target_quat, debug=debug)
        else:
            right_joint = self.robot_right.data.joint_pos[:, self.arm_joint_ids]

        # Gripper positions
        left_grip = torch.full((1, 2), left_gripper, device=self.device)
        right_grip = torch.full((1, 2), right_gripper, device=self.device)

        self.robot_left.set_joint_position_target(torch.cat([left_joint, left_grip], dim=-1))
        self.robot_right.set_joint_position_target(torch.cat([right_joint, right_grip], dim=-1))

    def get_gripper_pos(self, robot) -> float:
        """Get current gripper position."""
        return robot.data.joint_pos[:, self.gripper_joint_ids].mean().item()


# =============================================================================
# Goal Image Collector
# =============================================================================

class RealtimeLogger:
    """Logs camera images every 2 seconds in a background thread."""

    def __init__(self, log_dir: str, get_image_func):
        self.log_dir = log_dir
        self.get_image_func = get_image_func
        self.running = False
        self.thread = None
        self.interval = 2.0  # 2 seconds
        os.makedirs(log_dir, exist_ok=True)
        print(f"[RealtimeLogger] Saving images to {log_dir}/latest.png every {self.interval}s")

    def start(self):
        """Start the background logging thread."""
        self.running = True
        self.thread = threading.Thread(target=self._log_loop, daemon=True)
        self.thread.start()
        print("[RealtimeLogger] Started")

    def stop(self):
        """Stop the background logging thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=3.0)
        print("[RealtimeLogger] Stopped")

    def _log_loop(self):
        """Main loop that saves images every interval."""
        while self.running:
            try:
                images = self.get_image_func()
                if images:
                    # Create a 2x2 composite for quick overview
                    composite = self._create_composite(images)
                    save_path = os.path.join(self.log_dir, "latest.png")
                    Image.fromarray(composite).save(save_path)

                    # Also save individual camera images
                    for name, img in images.items():
                        cam_path = os.path.join(self.log_dir, f"latest_{name}.png")
                        Image.fromarray(img).save(cam_path)

            except Exception as e:
                print(f"[RealtimeLogger] Error: {e}")

            time.sleep(self.interval)

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
        """Reset arms to a proper ready position for manipulation.

        The default initialization seems to put arms in a bad configuration.
        This explicitly sets joint positions to a good starting pose.
        """
        # Ready pose joint values for Franka arm (wall-mounted, arms above table)
        # joint2: -0.8 (shoulder up), joint4: -1.2 (elbow slightly bent)
        ready_joint_pos = torch.tensor([
            [0.0, -0.8, 0.0, -1.2, 0.0, 1.8, 0.785, 0.04, 0.04]
        ], device=self.device)

        # Left arm (rotate joint1 toward center)
        left_joint_pos = ready_joint_pos.clone()
        left_joint_pos[0, 0] = 0.3  # joint1: rotate right toward center

        # Right arm (mirror rotation)
        right_joint_pos = ready_joint_pos.clone()
        right_joint_pos[0, 0] = -0.3  # joint1: rotate left toward center

        print("[Setup] Resetting arms to ready position...")

        # Apply joint positions and settle
        for _ in range(100):
            self.controller.robot_left.set_joint_position_target(left_joint_pos)
            self.controller.robot_right.set_joint_position_target(right_joint_pos)
            self.step_sim(4)

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
        table_height = 0.87  # TABLE_HEIGHT constant
        root_state = torch.zeros((1, 13), device=self.device)

        # Position
        root_state[0, 0] = x_pos      # X
        root_state[0, 1] = y_pos      # Y
        root_state[0, 2] = table_height + 0.02  # Z

        # Quaternion (cable lying along Y axis)
        root_state[0, 3:7] = torch.tensor([0.7071, -0.7071, 0.0, 0.0], device=self.device)

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
        """
        # Get body positions of all segments
        body_pos = self.cable.data.body_pos_w[0]  # [num_bodies, 3]

        # Debug: Print all segment positions
        print(f"  [Cable Debug] All segment positions (num_bodies={body_pos.shape[0]}):")
        for i in range(body_pos.shape[0]):
            pos = body_pos[i].cpu().tolist()
            print(f"    seg_{i}: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}")

        # Get both ends
        seg_0 = body_pos[CABLE_BASE_IDX]  # seg_0
        seg_9 = body_pos[CABLE_TIP_IDX]   # seg_9

        print(f"  [Cable Debug] seg_0 (left candidate): {seg_0.cpu().tolist()}")
        print(f"  [Cable Debug] seg_9 (right candidate): {seg_9.cpu().tolist()}")

        # Robot positions (Y coordinates)
        LEFT_ROBOT_Y = -0.30
        RIGHT_ROBOT_Y = 0.30

        # Calculate distances from each segment to each robot (in Y)
        seg_0_to_left = abs(seg_0[1].item() - LEFT_ROBOT_Y)
        seg_0_to_right = abs(seg_0[1].item() - RIGHT_ROBOT_Y)
        seg_9_to_left = abs(seg_9[1].item() - LEFT_ROBOT_Y)
        seg_9_to_right = abs(seg_9[1].item() - RIGHT_ROBOT_Y)

        # Assign each cable end to the closest robot
        if seg_0_to_left + seg_9_to_right < seg_9_to_left + seg_0_to_right:
            # seg_0 closer to left robot, seg_9 closer to right robot
            left_end = seg_0
            right_end = seg_9
            self._left_seg_idx = CABLE_BASE_IDX  # seg_0
            self._right_seg_idx = CABLE_TIP_IDX  # seg_9
        else:
            # seg_9 closer to left robot, seg_0 closer to right robot
            left_end = seg_9
            right_end = seg_0
            self._left_seg_idx = CABLE_TIP_IDX   # seg_9
            self._right_seg_idx = CABLE_BASE_IDX # seg_0

        # Debug: Coordinate check for left/right mapping
        print(f"  [Coordinate Check]")
        print(f"    seg_0 pos: {seg_0.cpu().tolist()} (Y={seg_0[1].item():.3f})")
        print(f"    seg_9 pos: {seg_9.cpu().tolist()} (Y={seg_9[1].item():.3f})")
        print(f"    Left end: seg_{self._left_seg_idx} (Y negative side, closer to Robot_Left)")
        print(f"    Right end: seg_{self._right_seg_idx} (Y positive side, closer to Robot_Right)")

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
        left_fingertip_z = left_ee[0, 2].item() - 0.107
        right_fingertip_z = right_ee[0, 2].item() - 0.107

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
        So to reach fingertip position X, panda_hand should go to X + [0, 0, 0.107].
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
        max_steps: int = 200,
        threshold: float = 0.02,
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
            self.controller.set_targets(left_interp, right_interp, left_gripper, right_gripper, debug=debug)

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
        current_left = self.controller.get_gripper_pos(self.controller.robot_left)
        current_right = self.controller.get_gripper_pos(self.controller.robot_right)

        for i in range(steps):
            t = (i + 1) / steps
            grip_pos = current_left + t * (target_pos - current_left)

            # Keep arm position, only change gripper
            self.controller.set_targets(None, None, grip_pos, grip_pos)
            self.step_sim(2)

    def open_grippers_slowly(self, target_pos: float = GRIPPER_OPEN, steps: int = 50):
        """Open grippers gradually."""
        current_left = self.controller.get_gripper_pos(self.controller.robot_left)
        current_right = self.controller.get_gripper_pos(self.controller.robot_right)

        for i in range(steps):
            t = (i + 1) / steps
            grip_pos = current_left + t * (target_pos - current_left)

            self.controller.set_targets(None, None, grip_pos, grip_pos)
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

        cable_left, cable_right = self.get_cable_ends()

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
            print(f"  (Should be ~90° for fingers perpendicular to cable)")
            print(f"{'='*60}\n")

            # 2-stage approach to avoid bumping into cable
            print(f"  Cable left: {cable_left.cpu().tolist()}")
            print(f"  Cable right: {cable_right.cpu().tolist()}")

            # 3-stage approach: hover high → above cable → grasp position

            # Stage 1: Move to high hover position (15cm above table)
            HOVER_HEIGHT = 0.15  # 15cm above table for fingertips (avoid table collision)
            left_fingertip_hover = torch.tensor([
                [cable_left[0].item(), cable_left[1].item(), TABLE_HEIGHT + HOVER_HEIGHT]
            ], device=self.device)
            right_fingertip_hover = torch.tensor([
                [cable_right[0].item(), cable_right[1].item(), TABLE_HEIGHT + HOVER_HEIGHT]
            ], device=self.device)

            # Convert fingertip targets to panda_hand targets (10.7cm higher)
            left_hover = self.fingertip_to_panda_hand(left_fingertip_hover)
            right_hover = self.fingertip_to_panda_hand(right_fingertip_hover)

            print(f"  Stage 1: Moving to hover position (15cm above table)...")
            print(f"    Left fingertip target: {left_fingertip_hover[0].cpu().tolist()}")
            print(f"    Right fingertip target: {right_fingertip_hover[0].cpu().tolist()}")
            print(f"    Left panda_hand target: {left_hover[0].cpu().tolist()}")
            print(f"    Right panda_hand target: {right_hover[0].cpu().tolist()}")

            self.move_to_target(left_hover, right_hover, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=300)
            self.step_sim(30)

            # Stage 2: Descend to just above cable (5cm above table)
            APPROACH_HEIGHT = 0.05  # 5cm above table for fingertips
            left_fingertip_above = torch.tensor([
                [cable_left[0].item(), cable_left[1].item(), TABLE_HEIGHT + APPROACH_HEIGHT]
            ], device=self.device)
            right_fingertip_above = torch.tensor([
                [cable_right[0].item(), cable_right[1].item(), TABLE_HEIGHT + APPROACH_HEIGHT]
            ], device=self.device)

            left_above = self.fingertip_to_panda_hand(left_fingertip_above)
            right_above = self.fingertip_to_panda_hand(right_fingertip_above)

            print(f"  Stage 2: Descending to above cable (5cm above table)...")
            print(f"    Left fingertip target: {left_fingertip_above[0].cpu().tolist()}")
            print(f"    Right fingertip target: {right_fingertip_above[0].cpu().tolist()}")
            print(f"    Left panda_hand target: {left_above[0].cpu().tolist()}")
            print(f"    Right panda_hand target: {right_above[0].cpu().tolist()}")

            self.move_to_target(left_above, right_above, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=200)
            self.step_sim(30)

            # Stage 3: Final descent to grasp position
            GRASP_HEIGHT = 0.03  # 3cm above table (fingertip level)
            left_grasp = torch.tensor([
                [cable_left[0].item(), cable_left[1].item(), TABLE_HEIGHT + GRASP_HEIGHT]
            ], device=self.device)
            right_grasp = torch.tensor([
                [cable_right[0].item(), cable_right[1].item(), TABLE_HEIGHT + GRASP_HEIGHT]
            ], device=self.device)

            # Convert to panda_hand targets (10.7cm higher)
            left_target = self.fingertip_to_panda_hand(left_grasp)
            right_target = self.fingertip_to_panda_hand(right_grasp)

            print(f"  Stage 3: Final descent to grasp position (3cm above table)...")
            print(f"    Left fingertip target: {left_grasp[0].cpu().tolist()}")
            print(f"    Right fingertip target: {right_grasp[0].cpu().tolist()}")
            print(f"    Left panda_hand target: {left_target[0].cpu().tolist()}")
            print(f"    Right panda_hand target: {right_target[0].cpu().tolist()}")

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
            # Re-align with current cable position before closing
            # This is necessary because IK may not have fully converged in Phase 1

            # Terminal 3: Extra stabilization before grasp
            print(f"  Stabilizing before grasp...")
            self.step_sim(100)

            print(f"  Re-aligning with current cable position...")

            # Get current cable ends
            cable_left, cable_right = self.get_cable_ends()

            # Calculate alignment targets (directly above cable)
            left_fingertip_target = cable_left.clone().unsqueeze(0)
            left_fingertip_target[0, 2] += 0.02  # 2cm above cable
            right_fingertip_target = cable_right.clone().unsqueeze(0)
            right_fingertip_target[0, 2] += 0.02

            left_target = self.fingertip_to_panda_hand(left_fingertip_target)
            right_target = self.fingertip_to_panda_hand(right_fingertip_target)

            # Short alignment move with grippers open
            self.move_to_target(left_target, right_target, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=100)

            # Descend to grasp height (fingertip at cable level)
            print(f"  Descending to grasp height...")
            # Re-read cable position (may have moved during alignment)
            cable_left, cable_right = self.get_cable_ends()

            left_fingertip_grasp = cable_left.clone().unsqueeze(0)
            right_fingertip_grasp = cable_right.clone().unsqueeze(0)
            left_grasp = self.fingertip_to_panda_hand(left_fingertip_grasp)
            right_grasp = self.fingertip_to_panda_hand(right_fingertip_grasp)

            print(f"    Target fingertip Z: {cable_left[2].item():.4f}m (left), {cable_right[2].item():.4f}m (right)")
            print(f"    Target panda_hand Z: {left_grasp[0, 2].item():.4f}m (left), {right_grasp[0, 2].item():.4f}m (right)")

            # Move down to grasp position with more steps for better convergence
            self.move_to_target(left_grasp, right_grasp, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=200)
            self.step_sim(50)  # Terminal 3: Increased from 30

            # Verify descent completion
            left_ee_post, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee_post, _ = self.controller.get_ee_pose(self.controller.robot_right)
            cable_left_post, cable_right_post = self.get_cable_ends()

            # Calculate fingertip Z after descent
            left_fingertip_z = left_ee_post[0, 2].item() - 0.107
            right_fingertip_z = right_ee_post[0, 2].item() - 0.107
            left_z_diff = abs(left_fingertip_z - cable_left_post[2].item())
            right_z_diff = abs(right_fingertip_z - cable_right_post[2].item())

            print(f"  [Descent Verification]")
            print(f"    Left fingertip Z:  {left_fingertip_z:.4f}m, Cable Z: {cable_left_post[2].item():.4f}m, ΔZ: {left_z_diff:.4f}m")
            print(f"    Right fingertip Z: {right_fingertip_z:.4f}m, Cable Z: {cable_right_post[2].item():.4f}m, ΔZ: {right_z_diff:.4f}m")

            # If descent incomplete, try additional descent
            MAX_Z_DIFF = 0.03  # 3cm tolerance
            if left_z_diff > MAX_Z_DIFF or right_z_diff > MAX_Z_DIFF:
                print(f"  [WARNING] Descent incomplete! Attempting additional descent...")
                # Update cable position and retry
                cable_left, cable_right = self.get_cable_ends()
                left_fingertip_grasp = cable_left.clone().unsqueeze(0)
                right_fingertip_grasp = cable_right.clone().unsqueeze(0)
                left_grasp = self.fingertip_to_panda_hand(left_fingertip_grasp)
                right_grasp = self.fingertip_to_panda_hand(right_fingertip_grasp)
                self.move_to_target(left_grasp, right_grasp, GRIPPER_OPEN, GRIPPER_OPEN, max_steps=200)
                self.step_sim(50)

                # Re-verify
                left_ee_post, _ = self.controller.get_ee_pose(self.controller.robot_left)
                right_ee_post, _ = self.controller.get_ee_pose(self.controller.robot_right)
                left_fingertip_z = left_ee_post[0, 2].item() - 0.107
                right_fingertip_z = right_ee_post[0, 2].item() - 0.107
                cable_left_post, cable_right_post = self.get_cable_ends()
                left_z_diff = abs(left_fingertip_z - cable_left_post[2].item())
                right_z_diff = abs(right_fingertip_z - cable_right_post[2].item())
                print(f"  [Descent Re-verification]")
                print(f"    Left fingertip Z:  {left_fingertip_z:.4f}m, Cable Z: {cable_left_post[2].item():.4f}m, ΔZ: {left_z_diff:.4f}m")
                print(f"    Right fingertip Z: {right_fingertip_z:.4f}m, Cable Z: {cable_right_post[2].item():.4f}m, ΔZ: {right_z_diff:.4f}m")

            print(f"  Closing grippers slowly...")
            self.close_grippers_slowly(GRIPPER_CLOSED, steps=300)  # Terminal 3: Slower close

            # Settle to let physics stabilize
            self.step_sim(100)  # Terminal 3: Increased from 50

            # Create D6 joint grasp constraints (optional)
            # D6 joints physically attach the cable to the gripper for stability
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)
            cable_left, cable_right = self.get_cable_ends()

            # Calculate fingertip positions (EE is panda_hand, fingertip is 10.7cm below)
            FINGERTIP_OFFSET = 0.107  # panda_hand to fingertip offset
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

                print(f"    Creating D6 joint: {left_gripper_path} <-> {left_cable_path}")
                self.grasp_manager.create_grasp("left", left_gripper_path, left_cable_path)

                print(f"    Creating D6 joint: {right_gripper_path} <-> {right_cable_path}")
                self.grasp_manager.create_grasp("right", right_gripper_path, right_cable_path)

            # Settle after grasp
            self.step_sim(50)

            # Validate grasp before proceeding
            grasp_ok, error_msg = self.validate_grasp()
            if not grasp_ok:
                print(f"  [GRASP FAILED] {error_msg}")
                print(f"  Aborting task - cannot proceed without valid grasp")
                raise RuntimeError(f"Grasp validation failed: {error_msg}")

            grasp_type = "friction grasp" if self.skip_d6_joints else "D6 joints"
            print(f"  Grasp complete and validated ({grasp_type} active)")

        elif phase == TaskPhase.LIFT_CABLE:
            # Coordinated lift: both grippers move to SAME height simultaneously
            # This prevents cable from being pulled apart

            # Get current EE positions
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

            # Target: same lift height for both grippers
            lift_height = TABLE_HEIGHT + 0.18  # 18cm above table

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

        elif phase == TaskPhase.ROTATE_CABLE:
            # Rotate cable 90° around hook center (Y-axis -> X-axis)
            # This positions the cable to be draped on the hook's V shape

            # Get current EE positions
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

            # Hook center as rotation pivot
            hook_center = self.hook_v_pos.clone()

            # Rotated target positions
            # Before: cable along Y-axis (left at Y-, right at Y+)
            # After: cable along X-axis (left at X+, right at X-)
            offset = 0.15  # Cable half-length
            lift_z = left_ee[0, 2].item()  # Maintain current height

            # Left hand: Y- side -> X+ side (front)
            left_target = torch.tensor([[
                hook_center[0].item() + offset,  # X positive (front)
                hook_center[1].item(),            # Y center
                lift_z
            ]], device=self.device)

            # Right hand: Y+ side -> X- side (back)
            right_target = torch.tensor([[
                hook_center[0].item() - offset,  # X negative (back)
                hook_center[1].item(),            # Y center
                lift_z
            ]], device=self.device)

            print(f"  Rotating cable 90° around hook center...")
            print(f"    Hook center: {hook_center.cpu().tolist()}")
            print(f"    Left: {left_ee[0].cpu().tolist()} -> {left_target[0].cpu().tolist()}")
            print(f"    Right: {right_ee[0].cpu().tolist()} -> {right_target[0].cpu().tolist()}")

            # Slow coordinated move for stable rotation
            self.move_to_target(left_target, right_target, GRIPPER_CLOSED, GRIPPER_CLOSED, max_steps=400)

            # Settle
            self.step_sim(50)

        elif phase == TaskPhase.APPROACH_HOOK:
            # Move towards hook, maintaining grip
            # After rotation, cable is along X-axis:
            # - Left hand at X+ (front)
            # - Right hand at X- (back)
            hook_v = self.hook_v_pos.clone()

            # Target: fingertips above hook (X-axis offsets now)
            left_fingertip_target = hook_v.clone().unsqueeze(0)
            left_fingertip_target[0, 0] += 0.12  # X positive (front)
            left_fingertip_target[0, 1] = hook_v[1].item()  # Y at hook center
            left_fingertip_target[0, 2] += 0.10  # Above hook

            right_fingertip_target = hook_v.clone().unsqueeze(0)
            right_fingertip_target[0, 0] -= 0.12  # X negative (back)
            right_fingertip_target[0, 1] = hook_v[1].item()  # Y at hook center
            right_fingertip_target[0, 2] += 0.10

            # Convert to panda_hand targets
            left_target = self.fingertip_to_panda_hand(left_fingertip_target)
            right_target = self.fingertip_to_panda_hand(right_fingertip_target)

            print(f"  Approaching hook at {hook_v.cpu().tolist()}...")
            print(f"    Cable now along X-axis")
            print(f"    Left (front): {left_fingertip_target[0].cpu().tolist()}")
            print(f"    Right (back): {right_fingertip_target[0].cpu().tolist()}")
            self.move_to_target(left_target, right_target, GRIPPER_CLOSED, GRIPPER_CLOSED, max_steps=300)

            # Settle
            self.step_sim(50)

        elif phase == TaskPhase.DRAPE_ON_HOOK:
            # Lower cable onto hook V
            # Cable is along X-axis:
            # - Left hand at X+ (front)
            # - Right hand at X- (back)
            hook_v = self.hook_v_pos.clone()

            # Target: fingertips just above hook V (X-axis offsets)
            left_fingertip_target = hook_v.clone().unsqueeze(0)
            left_fingertip_target[0, 0] += 0.06  # X positive (front), closer to hook
            left_fingertip_target[0, 1] = hook_v[1].item()  # Y at hook center
            left_fingertip_target[0, 2] += 0.02  # Just above hook V

            right_fingertip_target = hook_v.clone().unsqueeze(0)
            right_fingertip_target[0, 0] -= 0.06  # X negative (back), closer to hook
            right_fingertip_target[0, 1] = hook_v[1].item()  # Y at hook center
            right_fingertip_target[0, 2] += 0.02

            # Convert to panda_hand targets
            left_target = self.fingertip_to_panda_hand(left_fingertip_target)
            right_target = self.fingertip_to_panda_hand(right_fingertip_target)

            print(f"  Draping on hook...")
            print(f"    Left (front): {left_fingertip_target[0].cpu().tolist()}")
            print(f"    Right (back): {right_fingertip_target[0].cpu().tolist()}")
            self.move_to_target(left_target, right_target, GRIPPER_CLOSED, GRIPPER_CLOSED, max_steps=200)

            # Settle
            self.step_sim(50)

        elif phase == TaskPhase.RELEASE:
            # Release grasp constraints first
            print(f"  Releasing grasp constraints...")
            self.grasp_manager.release_all()

            # Settle briefly
            self.step_sim(10)

            # Open grippers
            print(f"  Opening grippers...")
            self.open_grippers_slowly(GRIPPER_OPEN, steps=80)

            # Settle to let cable rest on hook
            self.step_sim(100)

            # Retreat slightly along X-axis (cable is along X-axis now)
            left_ee, _ = self.controller.get_ee_pose(self.controller.robot_left)
            right_ee, _ = self.controller.get_ee_pose(self.controller.robot_right)

            left_target = left_ee.clone()
            left_target[0, 0] += 0.05  # Retreat in X+ direction (front)
            left_target[0, 2] += 0.05

            right_target = right_ee.clone()
            right_target[0, 0] -= 0.05  # Retreat in X- direction (back)
            right_target[0, 2] += 0.05

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
        # X positions to try (ケーブルをEEの自然な位置に配置)
        # EE自然位置: X≈0.69, ケーブル: X=0.35 (テーブル中央付近)
        x_positions = [0.35]

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

            # Reset cable to new position
            try:
                self.reset_cable_position(x_pos=x_pos, y_pos=-0.15)
            except RuntimeError as e:
                print(f"[Cable Reset Failed] {e}")
                print(f"[Auto-Retry] Skipping to next X position...")
                continue

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

    simulation_app.close()


if __name__ == "__main__":
    main()
