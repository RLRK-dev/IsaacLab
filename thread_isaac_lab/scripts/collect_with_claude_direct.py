#!/usr/bin/env python3
"""
Claude API座標直接方式によるデータ収集

座標情報をClaude APIに送信し、目標EE位置を取得。
DifferentialIKControllerで関節角度に変換してアクション実行。

Usage (Debug mode - no Claude API):
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/collect_with_claude_direct.py \
        --num_envs 1 --debug_mode --headless --enable_cameras

Usage (Full mode with Claude API):
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/collect_with_claude_direct.py \
        --num_envs 1 --num_episodes 100 --headless --enable_cameras
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Claude API Direct Coordinate Data Collection")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments (recommend 1 for API mode)")
parser.add_argument("--num_episodes", type=int, default=100, help="Total episodes to collect")
parser.add_argument("--max_steps", type=int, default=200, help="Max steps per episode")
parser.add_argument("--output_dir", type=str, default="data/claude_direct", help="Output directory")
parser.add_argument("--api_interval", type=int, default=10, help="Steps between API calls")
parser.add_argument("--debug_mode", action="store_true", help="Run without Claude API (random targets)")
parser.add_argument("--seed", type=int, default=42, help="Random seed")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os
import io
import h5py
import torch
import numpy as np
from datetime import datetime
from PIL import Image
from typing import Optional, Dict, Tuple
from enum import Enum

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.utils.math import subtract_frame_transforms

from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT
from envs.flexible_cable_cfg import CABLE_TOTAL_LENGTH, CABLE_NUM_SEGMENTS


# =============================================================================
# Constants
# =============================================================================

GRIPPER_OPEN = 0.04
GRIPPER_CLOSED = 0.005
GRIPPER_THRESHOLD = 0.02  # Below this = closed

# Workspace boundaries
WORKSPACE_X_MIN, WORKSPACE_X_MAX = 0.1, 0.7
WORKSPACE_Y_MIN, WORKSPACE_Y_MAX = -0.4, 0.4
WORKSPACE_Z_MIN, WORKSPACE_Z_MAX = TABLE_HEIGHT, TABLE_HEIGHT + 0.4

# Task success threshold
CABLE_HOOK_DIST_THRESHOLD = 0.05

# Phase transition thresholds
REACH_CABLE_DIST_THRESHOLD = 0.03      # EE to cable end distance
LIFT_HEIGHT_THRESHOLD = 0.10           # Cable lift height above table
APPROACH_HOOK_DIST_THRESHOLD = 0.05    # EE to hook distance
DRAPE_CABLE_HOOK_DIST_THRESHOLD = 0.03 # Cable center to hook distance


# =============================================================================
# Task Phase State Machine
# =============================================================================

class TaskPhase(Enum):
    """7-phase task state machine for cable draping."""
    REACH_CABLE = 1      # Goal 1: EE reaches cable ends
    GRASP_CABLE = 2      # Goal 2: Gripper grasps cable
    LIFT_CABLE = 3       # Goal 3: Cable lifted above table
    APPROACH_HOOK = 4    # Goal 4: EE reaches hook position
    DRAPE_ON_HOOK = 5    # Goal 5: Cable draped on hook
    RELEASE = 6          # Goal 6: Gripper released
    DONE = 7             # Goal 7: Task complete


# =============================================================================
# Dual Arm IK Controller
# =============================================================================

class DualArmIKController:
    """Wrapper for controlling both arms with Differential IK."""

    def __init__(self, scene: InteractiveScene, device: str):
        self.scene = scene
        self.device = device

        # IK configuration
        ik_cfg = DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="dls",
            ik_params={"lambda_val": 0.05},
        )

        # Create controllers for each arm
        self.left_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)
        self.right_ik = DifferentialIKController(ik_cfg, num_envs=1, device=device)

        # Robot references
        self.robot_left = scene["robot_left"]
        self.robot_right = scene["robot_right"]

        # EE body index (panda_hand = index 8 for Franka)
        self.ee_body_idx = 8
        self.jacobi_body_idx = self.ee_body_idx - 1  # Fixed base adjustment

        # Joint indices for arm (0-6) and gripper (7-8)
        self.arm_joint_ids = list(range(7))
        self.gripper_joint_ids = [7, 8]

        # Default orientation (gripper pointing down, fingers open in X)
        self.default_quat = torch.tensor([[0.0, 0.7071, -0.7071, 0.0]], device=device)  # w, x, y, z

        print(f"[IK] Initialized DualArmIKController")
        print(f"[IK] EE body index: {self.ee_body_idx}, Jacobi index: {self.jacobi_body_idx}")

    def get_ee_pose(self, robot) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get current EE position and quaternion in world frame."""
        ee_pos_w = robot.data.body_pos_w[:, self.ee_body_idx, :]
        ee_quat_w = robot.data.body_quat_w[:, self.ee_body_idx, :]
        return ee_pos_w, ee_quat_w

    def compute_ik(
        self,
        robot,
        ik_controller: DifferentialIKController,
        target_pos: torch.Tensor,
        target_quat: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Compute joint positions for target EE pose using IK."""
        if target_quat is None:
            target_quat = self.default_quat

        # Get current state
        joint_pos = robot.data.joint_pos[:, self.arm_joint_ids]

        # Get Jacobian
        jacobian = robot.root_physx_view.get_jacobians()[:, self.jacobi_body_idx, :, self.arm_joint_ids]

        # Get current EE pose in world frame
        ee_pos_w, ee_quat_w = self.get_ee_pose(robot)

        # Get root pose
        root_pos_w = robot.data.root_pos_w
        root_quat_w = robot.data.root_quat_w

        # Transform EE pose to root frame
        ee_pos_b, ee_quat_b = subtract_frame_transforms(
            root_pos_w, root_quat_w, ee_pos_w, ee_quat_w
        )

        # Transform target to root frame
        target_pos_b, target_quat_b = subtract_frame_transforms(
            root_pos_w, root_quat_w, target_pos, target_quat
        )

        # Set command and compute IK
        command = torch.cat([target_pos_b, target_quat_b], dim=-1)
        ik_controller.reset()
        ik_controller.set_command(command)

        joint_pos_des = ik_controller.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

        return joint_pos_des

    def apply_targets(
        self,
        left_target_pos: Optional[torch.Tensor],
        right_target_pos: Optional[torch.Tensor],
        left_gripper_close: bool,
        right_gripper_close: bool,
    ):
        """Apply IK targets and gripper commands to both arms."""
        # Left arm
        if left_target_pos is not None:
            left_joint_targets = self.compute_ik(
                self.robot_left, self.left_ik, left_target_pos
            )
        else:
            left_joint_targets = self.robot_left.data.joint_pos[:, self.arm_joint_ids]

        # Right arm
        if right_target_pos is not None:
            right_joint_targets = self.compute_ik(
                self.robot_right, self.right_ik, right_target_pos
            )
        else:
            right_joint_targets = self.robot_right.data.joint_pos[:, self.arm_joint_ids]

        # Gripper targets
        left_gripper = torch.full((1, 2), GRIPPER_CLOSED if left_gripper_close else GRIPPER_OPEN, device=self.device)
        right_gripper = torch.full((1, 2), GRIPPER_CLOSED if right_gripper_close else GRIPPER_OPEN, device=self.device)

        # Apply to robots
        self.robot_left.set_joint_position_target(
            torch.cat([left_joint_targets, left_gripper], dim=-1)
        )
        self.robot_right.set_joint_position_target(
            torch.cat([right_joint_targets, right_gripper], dim=-1)
        )

    def is_gripper_closed(self, robot) -> bool:
        """Check if gripper is closed."""
        finger_pos = robot.data.joint_pos[:, self.gripper_joint_ids].mean().item()
        return finger_pos < GRIPPER_THRESHOLD


# =============================================================================
# Image Compression
# =============================================================================

def compress_image_jpeg(img_array: np.ndarray, quality: int = 85) -> bytes:
    """Compress numpy image array to JPEG bytes."""
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


# =============================================================================
# Data Collector
# =============================================================================

class ClaudeDirectCollector:
    """Collects data using Claude API coordinate-based control."""

    def __init__(
        self,
        scene: InteractiveScene,
        sim,
        output_dir: str,
        num_envs: int = 1,
        max_steps: int = 200,
        api_interval: int = 10,
        debug_mode: bool = False,
    ):
        self.scene = scene
        self.sim = sim
        self.output_dir = output_dir
        self.num_envs = num_envs
        self.max_steps = max_steps
        self.api_interval = api_interval
        self.debug_mode = debug_mode
        self.device = scene["robot_left"].device

        os.makedirs(output_dir, exist_ok=True)

        # IK Controller
        self.ik_controller = DualArmIKController(scene, self.device)

        # Dimensions
        self.action_dim = 18
        self.proprio_dim = 34
        self.task_state_dim = 44

        # 3 Cameras for training data (overhead for API monitoring only)
        self.train_cameras = {
            'front_left': scene["front_left_camera"],
            'front_right': scene["front_right_camera"],
            'back': scene["back_camera"],
        }
        self.overhead_camera = scene["overhead_camera"]  # For API monitoring

        print(f"[Cameras] Training: {list(self.train_cameras.keys())}")
        print(f"[Cameras] Monitoring: overhead")
        print(f"[Mode] {'DEBUG (random targets)' if debug_mode else 'Claude API'}")

        # Current targets (persistent between API calls)
        self.current_left_target = None
        self.current_right_target = None
        self.current_left_gripper_close = False
        self.current_right_gripper_close = False

        # Phase state machine
        self.current_phase = TaskPhase.REACH_CABLE
        self.phase_start_step = 0
        self.last_phase_transition_step = 0

        # Goal images directory
        self.goal_images_dir = os.path.join(output_dir, "goal_images")
        os.makedirs(self.goal_images_dir, exist_ok=True)
        for phase in TaskPhase:
            phase_dir = os.path.join(self.goal_images_dir, f"phase_{phase.value}_{phase.name.lower()}")
            os.makedirs(phase_dir, exist_ok=True)

        self.reset_buffers()

    def reset_buffers(self):
        """Reset data collection buffers."""
        # 3 camera images (training data)
        self.front_left_imgs = []
        self.front_right_imgs = []
        self.back_imgs = []

        self.next_front_left_imgs = []
        self.next_front_right_imgs = []
        self.next_back_imgs = []

        # State
        self.proprios = []
        self.next_proprios = []
        self.task_states = []
        self.next_task_states = []

        # Actions and rewards
        self.actions = []
        self.rewards = []
        self.dones = []

        # Phase tracking
        self.phases = []  # Track phase at each step

        # Episode stats
        self.episode_lengths = []
        self.episode_rewards = []
        self.episode_successes = []

    def reset_episode_state(self):
        """Reset state for new episode."""
        self.current_phase = TaskPhase.REACH_CABLE
        self.phase_start_step = 0
        self.last_phase_transition_step = 0
        self.current_left_target = None
        self.current_right_target = None
        self.current_left_gripper_close = False
        self.current_right_gripper_close = False

    def get_camera_images(self) -> Dict[str, np.ndarray]:
        """Get current camera images from 3 training cameras."""
        images = {}
        for name, cam in self.train_cameras.items():
            rgb = cam.data.output["rgb"]
            img = rgb[..., :3].cpu().numpy().astype(np.uint8)
            images[name] = img[0]  # Single env
        return images

    def get_overhead_image(self) -> np.ndarray:
        """Get overhead camera image for API monitoring."""
        rgb = self.overhead_camera.data.output["rgb"]
        return rgb[0, ..., :3].cpu().numpy().astype(np.uint8)

    def get_proprio(self) -> torch.Tensor:
        """Get proprioceptive observation (34D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        left_joint_pos = robot_left.data.joint_pos[:, :7]
        right_joint_pos = robot_right.data.joint_pos[:, :7]
        left_joint_vel = robot_left.data.joint_vel[:, :7]
        right_joint_vel = robot_right.data.joint_vel[:, :7]
        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]

        proprio = torch.cat([
            left_joint_pos, left_joint_vel, left_ee_pos,
            right_joint_pos, right_joint_vel, right_ee_pos,
        ], dim=-1)

        return proprio

    def get_task_state(self) -> torch.Tensor:
        """Get task-relevant state information (44D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        hook_stem = self.scene["hook_stem"]
        hook_pos = hook_stem.data.root_pos_w

        cable = self.scene["cable"]
        cable_pos = cable.data.root_pos_w
        cable_quat = cable.data.root_quat_w

        segment_positions = self._compute_cable_segments(cable_pos, cable_quat)

        left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[:, 8, :]

        cable_center = cable_pos
        cable_hook_dist = torch.norm(cable_center - hook_pos, dim=-1, keepdim=True)
        left_ee_cable_dist = torch.norm(left_ee_pos - cable_center, dim=-1, keepdim=True)
        right_ee_cable_dist = torch.norm(right_ee_pos - cable_center, dim=-1, keepdim=True)
        left_ee_hook_dist = torch.norm(left_ee_pos - hook_pos, dim=-1, keepdim=True)
        right_ee_hook_dist = torch.norm(right_ee_pos - hook_pos, dim=-1, keepdim=True)

        task_state = torch.cat([
            segment_positions.view(self.num_envs, -1),
            hook_pos, left_ee_pos, right_ee_pos,
            cable_hook_dist, left_ee_cable_dist, right_ee_cable_dist,
            left_ee_hook_dist, right_ee_hook_dist,
        ], dim=-1)

        return task_state

    def _compute_cable_segments(self, cable_pos, cable_quat) -> torch.Tensor:
        """Compute virtual cable segment positions."""
        batch_size = cable_pos.shape[0]
        device = cable_pos.device

        segment_offsets = torch.linspace(
            -CABLE_TOTAL_LENGTH / 2,
            CABLE_TOTAL_LENGTH / 2,
            CABLE_NUM_SEGMENTS,
            device=device
        )

        w, x, y, z = cable_quat[:, 0], cable_quat[:, 1], cable_quat[:, 2], cable_quat[:, 3]
        R00 = 1 - 2 * (y * y + z * z)
        R10 = 2 * (x * y + z * w)
        R20 = 2 * (x * z - y * w)

        local_x = torch.stack([R00, R10, R20], dim=-1)
        segment_positions = cable_pos.unsqueeze(1) + segment_offsets.unsqueeze(0).unsqueeze(-1) * local_x.unsqueeze(1)

        return segment_positions

    def get_state_for_api(self) -> Dict:
        """Get state information formatted for Claude API."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]
        cable = self.scene["cable"]
        hook_stem = self.scene["hook_stem"]

        cable_pos = cable.data.root_pos_w[0]
        cable_quat = cable.data.root_quat_w[0]
        segments = self._compute_cable_segments(cable_pos.unsqueeze(0), cable_quat.unsqueeze(0))[0]

        # Hook V position (top of Y-hook)
        hook_pos = hook_stem.data.root_pos_w[0]
        hook_v_pos = hook_pos.clone()
        hook_v_pos[2] += 0.07  # Offset to V part

        left_ee_pos = robot_left.data.body_pos_w[0, 8, :]
        right_ee_pos = robot_right.data.body_pos_w[0, 8, :]

        return {
            "cable_left_end": segments[0].cpu().tolist(),
            "cable_center": cable_pos.cpu().tolist(),
            "cable_right_end": segments[-1].cpu().tolist(),
            "hook_v_pos": hook_v_pos.cpu().tolist(),
            "left_gripper_pos": left_ee_pos.cpu().tolist(),
            "right_gripper_pos": right_ee_pos.cpu().tolist(),
            "left_gripper_closed": self.ik_controller.is_gripper_closed(robot_left),
            "right_gripper_closed": self.ik_controller.is_gripper_closed(robot_right),
        }

    def check_phase_transition(self, state: Dict, step: int) -> Optional[TaskPhase]:
        """Check if phase transition conditions are met."""
        left_ee = state["left_gripper_pos"]
        right_ee = state["right_gripper_pos"]
        cable_left = state["cable_left_end"]
        cable_right = state["cable_right_end"]
        cable_center = state["cable_center"]
        hook_pos = state["hook_v_pos"]
        left_closed = state["left_gripper_closed"]
        right_closed = state["right_gripper_closed"]

        # Calculate distances
        left_to_cable = np.linalg.norm(np.array(left_ee) - np.array(cable_left))
        right_to_cable = np.linalg.norm(np.array(right_ee) - np.array(cable_right))
        cable_height = cable_center[2] - TABLE_HEIGHT
        left_to_hook = np.linalg.norm(np.array(left_ee) - np.array(hook_pos))
        right_to_hook = np.linalg.norm(np.array(right_ee) - np.array(hook_pos))
        cable_to_hook = np.linalg.norm(np.array(cable_center) - np.array(hook_pos))

        current = self.current_phase

        if current == TaskPhase.REACH_CABLE:
            # Both EEs near cable ends
            if left_to_cable < REACH_CABLE_DIST_THRESHOLD and right_to_cable < REACH_CABLE_DIST_THRESHOLD:
                return TaskPhase.GRASP_CABLE

        elif current == TaskPhase.GRASP_CABLE:
            # Both grippers closed
            if left_closed and right_closed:
                return TaskPhase.LIFT_CABLE

        elif current == TaskPhase.LIFT_CABLE:
            # Cable lifted above threshold
            if cable_height > LIFT_HEIGHT_THRESHOLD:
                return TaskPhase.APPROACH_HOOK

        elif current == TaskPhase.APPROACH_HOOK:
            # EEs near hook position
            if left_to_hook < APPROACH_HOOK_DIST_THRESHOLD or right_to_hook < APPROACH_HOOK_DIST_THRESHOLD:
                return TaskPhase.DRAPE_ON_HOOK

        elif current == TaskPhase.DRAPE_ON_HOOK:
            # Cable on hook
            if cable_to_hook < DRAPE_CABLE_HOOK_DIST_THRESHOLD:
                return TaskPhase.RELEASE

        elif current == TaskPhase.RELEASE:
            # Grippers released
            if not left_closed and not right_closed:
                return TaskPhase.DONE

        return None

    def save_goal_images(self, images: Dict[str, np.ndarray], phase: TaskPhase, episode_id: int):
        """Save goal images when phase transition occurs."""
        phase_dir = os.path.join(
            self.goal_images_dir,
            f"phase_{phase.value}_{phase.name.lower()}"
        )

        for cam_name, img in images.items():
            filename = os.path.join(phase_dir, f"ep{episode_id:04d}_{cam_name}.jpg")
            Image.fromarray(img).save(filename, quality=90)

        print(f"  [Goal] Saved goal images for {phase.name}")

    def get_phase_based_targets(self, state: Dict) -> Dict:
        """Generate targets based on current phase (rule-based for debug mode)."""
        phase = self.current_phase

        if phase == TaskPhase.REACH_CABLE:
            # Move both hands to cable ends (approach from above)
            left_target = state["cable_left_end"].copy()
            left_target[2] += 0.05  # 5cm above
            right_target = state["cable_right_end"].copy()
            right_target[2] += 0.05
            return {
                "left_target": left_target,
                "right_target": right_target,
                "left_gripper_close": False,
                "right_gripper_close": False,
                "reasoning": f"Phase {phase.value}: Reaching cable ends",
            }

        elif phase == TaskPhase.GRASP_CABLE:
            # Move down to cable and close grippers
            left_target = state["cable_left_end"].copy()
            right_target = state["cable_right_end"].copy()
            return {
                "left_target": left_target,
                "right_target": right_target,
                "left_gripper_close": True,
                "right_gripper_close": True,
                "reasoning": f"Phase {phase.value}: Grasping cable",
            }

        elif phase == TaskPhase.LIFT_CABLE:
            # Lift cable up
            left_target = state["left_gripper_pos"].copy()
            left_target[2] = TABLE_HEIGHT + 0.15  # Lift to 15cm above table
            right_target = state["right_gripper_pos"].copy()
            right_target[2] = TABLE_HEIGHT + 0.15
            return {
                "left_target": left_target,
                "right_target": right_target,
                "left_gripper_close": True,
                "right_gripper_close": True,
                "reasoning": f"Phase {phase.value}: Lifting cable",
            }

        elif phase == TaskPhase.APPROACH_HOOK:
            # Move toward hook (maintain grip)
            hook_pos = state["hook_v_pos"].copy()
            # Approach from above
            left_target = hook_pos.copy()
            left_target[1] -= 0.05  # Offset left
            left_target[2] += 0.05
            right_target = hook_pos.copy()
            right_target[1] += 0.05  # Offset right
            right_target[2] += 0.05
            return {
                "left_target": left_target,
                "right_target": right_target,
                "left_gripper_close": True,
                "right_gripper_close": True,
                "reasoning": f"Phase {phase.value}: Approaching hook",
            }

        elif phase == TaskPhase.DRAPE_ON_HOOK:
            # Lower cable onto hook V
            hook_pos = state["hook_v_pos"].copy()
            left_target = hook_pos.copy()
            left_target[1] -= 0.03
            right_target = hook_pos.copy()
            right_target[1] += 0.03
            return {
                "left_target": left_target,
                "right_target": right_target,
                "left_gripper_close": True,
                "right_gripper_close": True,
                "reasoning": f"Phase {phase.value}: Draping on hook",
            }

        elif phase == TaskPhase.RELEASE:
            # Open grippers
            return {
                "left_target": None,
                "right_target": None,
                "left_gripper_close": False,
                "right_gripper_close": False,
                "reasoning": f"Phase {phase.value}: Releasing grippers",
            }

        else:  # DONE
            return {
                "left_target": None,
                "right_target": None,
                "left_gripper_close": False,
                "right_gripper_close": False,
                "reasoning": f"Phase {phase.value}: Task complete",
            }

    def call_claude_api(self, state: Dict, images: Dict[str, np.ndarray]) -> Dict:
        """Call Claude API for next action (stub - to be implemented)."""
        # TODO: Implement actual Claude API call
        # For now, return phase-based targets
        return self.get_phase_based_targets(state)

    def compute_reward(self, task_state: torch.Tensor) -> float:
        """Compute reward based on cable-hook distance."""
        cable_hook_dist = task_state[0, 39].item()
        return -cable_hook_dist

    def is_task_complete(self, task_state: torch.Tensor) -> bool:
        """Check if task is complete (cable on hook)."""
        cable_hook_dist = task_state[0, 39].item()
        return cable_hook_dist < CABLE_HOOK_DIST_THRESHOLD

    def get_action_from_targets(self) -> torch.Tensor:
        """Convert current targets to 18D action for recording."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        # Get current joint positions
        left_joint = robot_left.data.joint_pos[0, :7]
        right_joint = robot_right.data.joint_pos[0, :7]

        # Get target joint positions
        left_target_joint = robot_left.data.joint_position_target[0, :7] if hasattr(robot_left.data, 'joint_position_target') else left_joint
        right_target_joint = robot_right.data.joint_position_target[0, :7] if hasattr(robot_right.data, 'joint_position_target') else right_joint

        # Compute delta (normalized)
        left_delta = (left_target_joint - left_joint) / 0.05
        right_delta = (right_target_joint - right_joint) / 0.05

        # Gripper action (-1 = close, +1 = open)
        left_gripper_action = torch.tensor([-1.0, -1.0] if self.current_left_gripper_close else [0.0, 0.0], device=self.device)
        right_gripper_action = torch.tensor([-1.0, -1.0] if self.current_right_gripper_close else [0.0, 0.0], device=self.device)

        action = torch.cat([
            left_delta, left_gripper_action,
            right_delta, right_gripper_action,
        ])

        return action.clamp(-1.0, 1.0)

    def collect_episode(self, episode_id: int):
        """Collect one episode of data."""
        print(f"\n[Episode {episode_id}] Starting...")

        episode_reward = 0.0
        success = False

        # Reset episode state
        self.reset_episode_state()

        # Initial state
        images = self.get_camera_images()
        proprio = self.get_proprio()
        task_state = self.get_task_state()

        for step in range(self.max_steps):
            state_for_api = self.get_state_for_api()

            # Check phase transition
            next_phase = self.check_phase_transition(state_for_api, step)
            if next_phase is not None:
                # Save goal images for completed phase
                self.save_goal_images(images, self.current_phase, episode_id)

                # Transition to next phase
                old_phase = self.current_phase
                self.current_phase = next_phase
                self.last_phase_transition_step = step
                print(f"  [Step {step}] Phase transition: {old_phase.name} -> {next_phase.name}")

                # API call at phase transition (stub)
                if not self.debug_mode:
                    response = self.call_claude_api(state_for_api, images)
                else:
                    response = self.get_phase_based_targets(state_for_api)
            elif step % self.api_interval == 0:
                # Regular interval update
                if self.debug_mode:
                    response = self.get_phase_based_targets(state_for_api)
                else:
                    response = self.call_claude_api(state_for_api, images)
            else:
                response = None  # Keep current targets

            # Update targets if new response
            if response is not None:
                if response["left_target"]:
                    self.current_left_target = torch.tensor(
                        [response["left_target"]], device=self.device
                    )
                else:
                    self.current_left_target = None

                if response["right_target"]:
                    self.current_right_target = torch.tensor(
                        [response["right_target"]], device=self.device
                    )
                else:
                    self.current_right_target = None

                self.current_left_gripper_close = response["left_gripper_close"]
                self.current_right_gripper_close = response["right_gripper_close"]

                if step % 50 == 0:
                    print(f"  [Step {step}] {response['reasoning']}")

            # Apply IK targets
            self.ik_controller.apply_targets(
                self.current_left_target,
                self.current_right_target,
                self.current_left_gripper_close,
                self.current_right_gripper_close,
            )

            # Record current state
            action = self.get_action_from_targets()
            self.front_left_imgs.append(compress_image_jpeg(images['front_left']))
            self.front_right_imgs.append(compress_image_jpeg(images['front_right']))
            self.back_imgs.append(compress_image_jpeg(images['back']))
            self.proprios.append(proprio[0].cpu().numpy())
            self.task_states.append(task_state[0].cpu().numpy())
            self.actions.append(action.cpu().numpy())
            self.phases.append(self.current_phase.value)  # Track phase

            # Step simulation
            for _ in range(4):
                self.sim.step()
            self.scene.update(self.sim.get_physics_dt())

            # Get next state
            next_images = self.get_camera_images()
            next_proprio = self.get_proprio()
            next_task_state = self.get_task_state()

            reward = self.compute_reward(next_task_state)
            episode_reward += reward

            self.next_front_left_imgs.append(compress_image_jpeg(next_images['front_left']))
            self.next_front_right_imgs.append(compress_image_jpeg(next_images['front_right']))
            self.next_back_imgs.append(compress_image_jpeg(next_images['back']))
            self.next_proprios.append(next_proprio[0].cpu().numpy())
            self.next_task_states.append(next_task_state[0].cpu().numpy())
            self.rewards.append(reward)
            self.dones.append(False)

            # Check task completion (phase reaches DONE or cable on hook)
            if self.current_phase == TaskPhase.DONE or self.is_task_complete(next_task_state):
                success = True
                print(f"  [Step {step}] Task complete! Final phase: {self.current_phase.name}")
                break

            # Update for next iteration
            images = next_images
            proprio = next_proprio
            task_state = next_task_state

        # Mark last step as done
        if self.dones:
            self.dones[-1] = True

        self.episode_lengths.append(step + 1)
        self.episode_rewards.append(episode_reward / (step + 1))
        self.episode_successes.append(success)

        print(f"[Episode {episode_id}] Steps: {step + 1}, Reward: {episode_reward / (step + 1):.4f}, Success: {success}")

    def save_batch(self, batch_id: int):
        """Save collected data to HDF5 file."""
        if not self.proprios:
            print("[Save] No data to save")
            return

        filename = os.path.join(self.output_dir, f"claude_direct_batch{batch_id:04d}.h5")
        print(f"[Save] Saving {len(self.proprios)} samples to {filename}")

        with h5py.File(filename, 'w') as f:
            # Images (variable length)
            dt = h5py.special_dtype(vlen=np.uint8)
            f.create_dataset('front_left_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.front_left_imgs], dtype=object), dtype=dt)
            f.create_dataset('front_right_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.front_right_imgs], dtype=object), dtype=dt)
            f.create_dataset('back_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.back_imgs], dtype=object), dtype=dt)

            f.create_dataset('next_front_left_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_front_left_imgs], dtype=object), dtype=dt)
            f.create_dataset('next_front_right_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_front_right_imgs], dtype=object), dtype=dt)
            f.create_dataset('next_back_img', data=np.array([np.frombuffer(x, dtype=np.uint8) for x in self.next_back_imgs], dtype=object), dtype=dt)

            # State data
            f.create_dataset('proprio', data=np.array(self.proprios), dtype=np.float32)
            f.create_dataset('next_proprio', data=np.array(self.next_proprios), dtype=np.float32)
            f.create_dataset('task_state', data=np.array(self.task_states), dtype=np.float32)
            f.create_dataset('next_task_state', data=np.array(self.next_task_states), dtype=np.float32)
            f.create_dataset('action', data=np.array(self.actions), dtype=np.float32)
            f.create_dataset('reward', data=np.array(self.rewards), dtype=np.float32)
            f.create_dataset('done', data=np.array(self.dones), dtype=bool)
            f.create_dataset('phase', data=np.array(self.phases), dtype=np.int32)  # Phase info

            # Metadata
            f.attrs['num_cameras'] = 3
            f.attrs['camera_names'] = ['front_left', 'front_right', 'back']
            f.attrs['proprio_dim'] = self.proprio_dim
            f.attrs['task_state_dim'] = self.task_state_dim
            f.attrs['action_dim'] = self.action_dim
            f.attrs['debug_mode'] = self.debug_mode
            f.attrs['timestamp'] = datetime.now().isoformat()

        self.reset_buffers()
        print(f"[Save] Done: {filename}")


# =============================================================================
# Main
# =============================================================================

def main():
    print(f"\n{'='*60}")
    print(f"Claude API Direct Coordinate Data Collection")
    print(f"{'='*60}")
    print(f"num_envs: {args_cli.num_envs}")
    print(f"num_episodes: {args_cli.num_episodes}")
    print(f"max_steps: {args_cli.max_steps}")
    print(f"api_interval: {args_cli.api_interval}")
    print(f"debug_mode: {args_cli.debug_mode}")
    print(f"output_dir: {args_cli.output_dir}")
    print(f"{'='*60}\n")

    # Setup scene
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = args_cli.num_envs

    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Create collector
    collector = ClaudeDirectCollector(
        scene=scene,
        sim=sim,
        output_dir=args_cli.output_dir,
        num_envs=args_cli.num_envs,
        max_steps=args_cli.max_steps,
        api_interval=args_cli.api_interval,
        debug_mode=args_cli.debug_mode,
    )

    # Warm up simulation
    print("[Setup] Running initial simulation steps...")
    for i in range(30):
        sim.step()
    scene.update(sim.get_physics_dt())
    print("[Setup] Initial setup complete!")

    # Collect episodes
    batch_id = 0
    save_frequency = 10

    for episode in range(args_cli.num_episodes):
        collector.collect_episode(episode)

        if (episode + 1) % save_frequency == 0:
            success_rate = np.mean(collector.episode_successes[-save_frequency:]) if collector.episode_successes else 0
            avg_reward = np.mean(collector.episode_rewards[-save_frequency:]) if collector.episode_rewards else 0
            print(f"\n[Progress] Episodes: {episode + 1}/{args_cli.num_episodes}, Success: {success_rate:.1%}, Avg Reward: {avg_reward:.4f}")
            collector.save_batch(batch_id)
            batch_id += 1

    # Save remaining data
    if collector.proprios:
        collector.save_batch(batch_id)

    print(f"\n[Done] Data collection complete!")
    print(f"Total episodes: {args_cli.num_episodes}")
    print(f"Output directory: {args_cli.output_dir}")

    simulation_app.close()


if __name__ == "__main__":
    main()
