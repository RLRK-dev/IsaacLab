#!/usr/bin/env python3
"""
THREAD: Hook Hanging Environment for Isaac Lab
===============================================

This module implements the ManagerBasedRLEnv for the Hook Hanging task.
It defines observations, actions, rewards, and terminations.

Compatible with:
- Isaac Sim 5.1.0
- Isaac Lab 2.3.0
- RSL-RL (PPO training)

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import math
import torch
from dataclasses import MISSING
from typing import Sequence

# Isaac Lab imports (isaaclab package for Isaac Lab 2.3.0)
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.envs import ManagerBasedEnv, ManagerBasedRLEnv, ManagerBasedRLEnvCfg
from isaaclab.managers import (
    ActionTerm,
    ActionTermCfg,
    EventTermCfg,
    ObservationGroupCfg,
    ObservationTermCfg,
    RewardTermCfg,
    SceneEntityCfg,
    TerminationTermCfg,
)
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import (
    combine_frame_transforms,
    quat_from_euler_xyz,
    quat_rotate_inverse,
    subtract_frame_transforms,
)

# Local imports
from .assets_cfg import (
    HookHangingSceneCfg,
    HookHangingSceneCfgSingleArm,
    FrankaPandaCfg,
    SimpleHookCfg,
    CableSegmentedCfg,
    TableCfg,
)


# =============================================================================
# Observation Functions
# =============================================================================

def joint_pos(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get normalized joint positions of the robot.
    
    Returns:
        Joint positions normalized to [-1, 1] based on joint limits.
        Shape: (num_envs, num_joints)
    """
    asset: Articulation = env.scene[asset_cfg.name]
    # Get joint positions and normalize
    joint_pos = asset.data.joint_pos
    joint_pos_limits = asset.data.soft_joint_pos_limits
    
    # Normalize to [-1, 1]
    joint_pos_normalized = 2.0 * (joint_pos - joint_pos_limits[..., 0]) / (
        joint_pos_limits[..., 1] - joint_pos_limits[..., 0]
    ) - 1.0
    
    return joint_pos_normalized


def joint_vel(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get joint velocities of the robot.
    
    Returns:
        Joint velocities in rad/s.
        Shape: (num_envs, num_joints)
    """
    asset: Articulation = env.scene[asset_cfg.name]
    return asset.data.joint_vel


def ee_pos_w(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get end-effector position in world frame.
    
    Returns:
        EE position (x, y, z).
        Shape: (num_envs, 3)
    """
    asset: Articulation = env.scene[asset_cfg.name]
    # End-effector is typically the last link before gripper
    ee_pos = asset.data.body_pos_w[:, -1, :]  # Assuming last body is EE
    return ee_pos


def ee_quat_w(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get end-effector orientation in world frame.
    
    Returns:
        EE quaternion (w, x, y, z).
        Shape: (num_envs, 4)
    """
    asset: Articulation = env.scene[asset_cfg.name]
    ee_quat = asset.data.body_quat_w[:, -1, :]
    return ee_quat


def gripper_pos(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get gripper finger positions.
    
    Returns:
        Gripper opening (average of both fingers).
        Shape: (num_envs, 1)
    """
    asset: Articulation = env.scene[asset_cfg.name]
    # Gripper joints are typically the last 2 joints
    gripper_joints = asset.data.joint_pos[:, -2:]
    # Return average opening
    return gripper_joints.mean(dim=-1, keepdim=True)


def cable_pos_w(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get cable center position in world frame.
    
    Returns:
        Cable center position (x, y, z).
        Shape: (num_envs, 3)
    """
    asset: RigidObject = env.scene[asset_cfg.name]
    return asset.data.root_pos_w


def cable_vel_w(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get cable velocity in world frame.
    
    Returns:
        Cable linear velocity.
        Shape: (num_envs, 3)
    """
    asset: RigidObject = env.scene[asset_cfg.name]
    return asset.data.root_lin_vel_w


def hook_pos_w(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get hook position in world frame.
    
    Returns:
        Hook position (x, y, z).
        Shape: (num_envs, 3)
    """
    asset: RigidObject = env.scene[asset_cfg.name]
    return asset.data.root_pos_w


def ee_to_cable_vec(env: ManagerBasedEnv, robot_cfg: SceneEntityCfg, cable_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get vector from end-effector to cable center.
    
    Returns:
        Vector (dx, dy, dz) from EE to cable.
        Shape: (num_envs, 3)
    """
    robot: Articulation = env.scene[robot_cfg.name]
    cable: RigidObject = env.scene[cable_cfg.name]
    
    ee_pos = robot.data.body_pos_w[:, -1, :]
    cable_pos = cable.data.root_pos_w
    
    return cable_pos - ee_pos


def cable_to_hook_vec(env: ManagerBasedEnv, cable_cfg: SceneEntityCfg, hook_cfg: SceneEntityCfg) -> torch.Tensor:
    """
    Get vector from cable center to hook.
    
    Returns:
        Vector (dx, dy, dz) from cable to hook.
        Shape: (num_envs, 3)
    """
    cable: RigidObject = env.scene[cable_cfg.name]
    hook: RigidObject = env.scene[hook_cfg.name]
    
    cable_pos = cable.data.root_pos_w
    hook_pos = hook.data.root_pos_w
    
    return hook_pos - cable_pos


def is_gripper_closed(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg, threshold: float = 0.01) -> torch.Tensor:
    """
    Check if gripper is closed (grasping).
    
    Returns:
        Boolean tensor indicating closed gripper.
        Shape: (num_envs, 1)
    """
    asset: Articulation = env.scene[asset_cfg.name]
    gripper_joints = asset.data.joint_pos[:, -2:]
    avg_opening = gripper_joints.mean(dim=-1, keepdim=True)
    return (avg_opening < threshold).float()


# =============================================================================
# Action Functions
# =============================================================================

class JointPositionAction(ActionTerm):
    """
    Action term for joint position control.
    
    Applies joint position targets with configurable scaling.
    """
    
    cfg: "JointPositionActionCfg"
    _asset: Articulation
    
    def __init__(self, cfg: "JointPositionActionCfg", env: ManagerBasedEnv):
        super().__init__(cfg, env)
        self._asset = env.scene[cfg.asset_name]
        
        # Get joint indices
        self._joint_ids, _ = self._asset.find_joints(cfg.joint_names)
        
        # Action scaling
        self._scale = cfg.scale
        
        # Default positions
        self._default_pos = self._asset.data.default_joint_pos[:, self._joint_ids].clone()
    
    @property
    def action_dim(self) -> int:
        return len(self._joint_ids)
    
    @property
    def raw_actions(self) -> torch.Tensor:
        return self._raw_actions
    
    @property
    def processed_actions(self) -> torch.Tensor:
        return self._processed_actions
    
    def process_actions(self, actions: torch.Tensor):
        self._raw_actions = actions
        # Scale actions and add to default positions
        self._processed_actions = self._default_pos + self._scale * actions
    
    def apply_actions(self):
        self._asset.set_joint_position_target(
            self._processed_actions, joint_ids=self._joint_ids
        )


@configclass
class JointPositionActionCfg(ActionTermCfg):
    """Configuration for joint position action term."""
    
    class_type: type = JointPositionAction
    
    asset_name: str = "robot"
    joint_names: list[str] = ["panda_joint.*"]  # Regex for all joints
    scale: float = 0.1  # Action scaling factor


class GripperAction(ActionTerm):
    """
    Action term for gripper control.
    
    Binary or continuous gripper control.
    """
    
    cfg: "GripperActionCfg"
    _asset: Articulation
    
    def __init__(self, cfg: "GripperActionCfg", env: ManagerBasedEnv):
        super().__init__(cfg, env)
        self._asset = env.scene[cfg.asset_name]
        
        # Gripper joint indices
        self._joint_ids, _ = self._asset.find_joints(cfg.joint_names)
        
        # Gripper limits
        self._open_pos = cfg.open_pos
        self._close_pos = cfg.close_pos
        self._binary = cfg.binary
    
    @property
    def action_dim(self) -> int:
        return 1  # Single gripper command
    
    @property
    def raw_actions(self) -> torch.Tensor:
        return self._raw_actions
    
    @property
    def processed_actions(self) -> torch.Tensor:
        return self._processed_actions
    
    def process_actions(self, actions: torch.Tensor):
        self._raw_actions = actions
        
        if self._binary:
            # Binary: >0 = close, <=0 = open
            gripper_cmd = torch.where(
                actions > 0,
                torch.full_like(actions, self._close_pos),
                torch.full_like(actions, self._open_pos),
            )
        else:
            # Continuous: map [-1, 1] to [close, open]
            gripper_cmd = (actions + 1) / 2 * (self._open_pos - self._close_pos) + self._close_pos
        
        # Apply to both fingers
        self._processed_actions = gripper_cmd.repeat(1, 2)
    
    def apply_actions(self):
        self._asset.set_joint_position_target(
            self._processed_actions, joint_ids=self._joint_ids
        )


@configclass
class GripperActionCfg(ActionTermCfg):
    """Configuration for gripper action term."""
    
    class_type: type = GripperAction
    
    asset_name: str = "robot"
    joint_names: list[str] = ["panda_finger_joint.*"]
    open_pos: float = 0.04
    close_pos: float = 0.0
    binary: bool = False  # Continuous control by default


# =============================================================================
# Reward Functions
# =============================================================================

_debug_counter = [0]  # Mutable counter for debug logging

def approach_cable_reward(
    env: ManagerBasedEnv,
    robot_cfg: SceneEntityCfg,
    cable_cfg: SceneEntityCfg,
    std: float = 0.1,
) -> torch.Tensor:
    """
    Reward for moving end-effector towards cable.

    Gaussian reward based on EE-to-cable distance.
    Uses world coordinates directly (distance is translation-invariant).
    """
    robot: Articulation = env.scene[robot_cfg.name]
    cable: RigidObject = env.scene[cable_cfg.name]

    # Get world coordinates
    ee_pos_w = robot.data.body_pos_w[:, -1, :]  # [num_envs, 3]
    cable_pos_w = cable.data.root_pos_w  # [num_envs, 3]

    # Compute distance directly in world coordinates
    # (distance is translation-invariant, so env_origins don't matter)
    distance = torch.norm(cable_pos_w - ee_pos_w, dim=-1)
    reward = torch.exp(-distance / std)

    # Debug log every 10000 calls
    _debug_counter[0] += 1
    if _debug_counter[0] % 10000 == 1:
        mean_dist = distance.mean().item()
        min_dist = distance.min().item()
        max_dist = distance.max().item()
        mean_reward = reward.mean().item()
        print(f"[DEBUG] EE world[0]: ({ee_pos_w[0, 0]:.3f}, {ee_pos_w[0, 1]:.3f}, {ee_pos_w[0, 2]:.3f})")
        print(f"[DEBUG] Cable world[0]: ({cable_pos_w[0, 0]:.3f}, {cable_pos_w[0, 1]:.3f}, {cable_pos_w[0, 2]:.3f})")
        print(f"[DEBUG] Distance: mean={mean_dist:.3f}, min={min_dist:.3f}, max={max_dist:.3f}")
        print(f"[DEBUG] Reward: mean={mean_reward:.4f}, std={std}")

    return reward


def grasp_reward(
    env: ManagerBasedEnv,
    robot_cfg: SceneEntityCfg,
    cable_cfg: SceneEntityCfg,
    grasp_threshold: float = 0.02,
    gripper_threshold: float = 0.01,
) -> torch.Tensor:
    """
    Reward for successfully grasping the cable.

    Checks if:
    1. Gripper is closed
    2. Cable is close to gripper
    Uses world coordinates directly.
    """
    robot: Articulation = env.scene[robot_cfg.name]
    cable: RigidObject = env.scene[cable_cfg.name]

    # Check gripper state
    gripper_joints = robot.data.joint_pos[:, -2:]
    gripper_closed = (gripper_joints.mean(dim=-1) < gripper_threshold)

    # Check cable proximity using world coordinates
    ee_pos_w = robot.data.body_pos_w[:, -1, :]
    cable_pos_w = cable.data.root_pos_w
    distance = torch.norm(cable_pos_w - ee_pos_w, dim=-1)
    cable_close = (distance < grasp_threshold)

    # Reward only when both conditions met
    reward = (gripper_closed & cable_close).float()

    return reward


def lift_reward(
    env: ManagerBasedEnv,
    cable_cfg: SceneEntityCfg,
    table_height: float = 0.75,
    target_lift: float = 0.15,
    std: float = 0.05,
) -> torch.Tensor:
    """
    Reward for lifting the cable above the table.
    """
    cable: RigidObject = env.scene[cable_cfg.name]
    
    cable_height = cable.data.root_pos_w[:, 2]  # Z coordinate
    lift_amount = cable_height - table_height
    
    # Reward for reaching target lift height
    height_error = torch.abs(lift_amount - target_lift)
    reward = torch.exp(-height_error / std)
    
    # Only reward positive lift
    reward = reward * (lift_amount > 0).float()
    
    return reward


def approach_hook_reward(
    env: ManagerBasedEnv,
    cable_cfg: SceneEntityCfg,
    hook_cfg: SceneEntityCfg,
    std: float = 0.1,
) -> torch.Tensor:
    """
    Reward for moving cable towards hook.
    Uses world coordinates directly.
    """
    cable: RigidObject = env.scene[cable_cfg.name]
    hook: RigidObject = env.scene[hook_cfg.name]

    cable_pos_w = cable.data.root_pos_w
    hook_pos_w = hook.data.root_pos_w

    distance = torch.norm(hook_pos_w - cable_pos_w, dim=-1)
    reward = torch.exp(-distance / std)

    return reward


def alignment_reward(
    env: ManagerBasedEnv,
    cable_cfg: SceneEntityCfg,
    hook_cfg: SceneEntityCfg,
    horizontal_threshold: float = 0.03,
) -> torch.Tensor:
    """
    Reward for aligning cable above hook.

    Cable should be directly above hook in XY plane.
    Uses world coordinates directly.
    """
    cable: RigidObject = env.scene[cable_cfg.name]
    hook: RigidObject = env.scene[hook_cfg.name]

    cable_pos_w = cable.data.root_pos_w
    hook_pos_w = hook.data.root_pos_w

    # Horizontal distance only (XY) in world coords
    horizontal_dist = torch.norm(cable_pos_w[:, :2] - hook_pos_w[:, :2], dim=-1)

    # Binary reward for alignment
    aligned = (horizontal_dist < horizontal_threshold).float()

    # Additional check: cable should be above hook (Z comparison)
    above_hook = (cable_pos_w[:, 2] > hook_pos_w[:, 2]).float()

    return aligned * above_hook


def hanging_success_reward(
    env: ManagerBasedEnv,
    robot_cfg: SceneEntityCfg,
    cable_cfg: SceneEntityCfg,
    hook_cfg: SceneEntityCfg,
    position_threshold: float = 0.03,
    gripper_open_threshold: float = 0.02,
    bonus: float = 10.0,
) -> torch.Tensor:
    """
    Large reward for successfully hanging cable on hook.
    
    Success criteria:
    1. Cable is near hook position (within threshold)
    2. Gripper is open
    3. Cable is below hook top (hanging)
    """
    robot: Articulation = env.scene[robot_cfg.name]
    cable: RigidObject = env.scene[cable_cfg.name]
    hook: RigidObject = env.scene[hook_cfg.name]
    
    # Check gripper is open
    gripper_joints = robot.data.joint_pos[:, -2:]
    gripper_open = (gripper_joints.mean(dim=-1) > gripper_open_threshold)
    
    # Check cable position relative to hook
    cable_pos = cable.data.root_pos_w
    hook_pos = hook.data.root_pos_w
    
    # Horizontal distance
    horizontal_dist = torch.norm(cable_pos[:, :2] - hook_pos[:, :2], dim=-1)
    near_hook = (horizontal_dist < position_threshold)
    
    # Cable should be at or below hook height (hanging)
    cable_below_hook = (cable_pos[:, 2] <= hook_pos[:, 2] + 0.05)
    
    # All conditions
    success = gripper_open & near_hook & cable_below_hook
    
    return success.float() * bonus


def time_penalty(env: ManagerBasedEnv, penalty: float = -0.01) -> torch.Tensor:
    """Small penalty per timestep to encourage efficiency."""
    return torch.full((env.num_envs,), penalty, device=env.device)


def drop_penalty(
    env: ManagerBasedEnv,
    cable_cfg: SceneEntityCfg,
    table_height: float = 0.75,
    penalty: float = -2.0,
) -> torch.Tensor:
    """
    Penalty for dropping the cable on the table.
    
    Applied when cable is on table and should be lifted.
    """
    cable: RigidObject = env.scene[cable_cfg.name]
    
    cable_height = cable.data.root_pos_w[:, 2]
    on_table = (cable_height < table_height + 0.02)
    
    # Only penalize if we've previously lifted (use episode info)
    # For simplicity, just check if on table
    return on_table.float() * penalty


# =============================================================================
# Termination Functions
# =============================================================================

def time_out(env: ManagerBasedEnv, max_episode_length: int) -> torch.Tensor:
    """Terminate if episode exceeds maximum length."""
    return env.episode_length_buf >= max_episode_length


def cable_dropped(
    env: ManagerBasedEnv,
    cable_cfg: SceneEntityCfg,
    min_height: float = 0.1,
) -> torch.Tensor:
    """Terminate if cable falls below minimum height (near floor)."""
    cable: RigidObject = env.scene[cable_cfg.name]
    cable_height = cable.data.root_pos_w[:, 2]
    # ケーブルが床近く(10cm以下)に落ちたら終了
    return cable_height < min_height


def task_success(
    env: ManagerBasedEnv,
    robot_cfg: SceneEntityCfg,
    cable_cfg: SceneEntityCfg,
    hook_cfg: SceneEntityCfg,
    position_threshold: float = 0.03,
    stability_steps: int = 30,
) -> torch.Tensor:
    """
    Terminate (successfully) if cable is hanging on hook.
    
    Requires cable to be stable near hook for multiple steps.
    """
    robot: Articulation = env.scene[robot_cfg.name]
    cable: RigidObject = env.scene[cable_cfg.name]
    hook: RigidObject = env.scene[hook_cfg.name]
    
    # Check gripper is open
    gripper_joints = robot.data.joint_pos[:, -2:]
    gripper_open = (gripper_joints.mean(dim=-1) > 0.02)
    
    # Check cable near hook
    cable_pos = cable.data.root_pos_w
    hook_pos = hook.data.root_pos_w
    horizontal_dist = torch.norm(cable_pos[:, :2] - hook_pos[:, :2], dim=-1)
    near_hook = (horizontal_dist < position_threshold)
    
    # Check cable velocity (stability)
    cable_vel = cable.data.root_lin_vel_w
    cable_stable = (torch.norm(cable_vel, dim=-1) < 0.1)
    
    # All conditions
    success = gripper_open & near_hook & cable_stable
    
    return success


# =============================================================================
# Event Functions (Reset, Randomization)
# =============================================================================

def reset_robot_to_default(
    env: ManagerBasedEnv,
    env_ids: Sequence[int],
    asset_cfg: SceneEntityCfg,
):
    """Reset robot to default joint positions."""
    asset: Articulation = env.scene[asset_cfg.name]
    
    # Reset to default positions
    default_pos = asset.data.default_joint_pos[env_ids].clone()
    default_vel = torch.zeros_like(default_pos)
    
    asset.write_joint_state_to_sim(default_pos, default_vel, env_ids=env_ids)


def reset_cable_on_table(
    env: ManagerBasedEnv,
    env_ids: Sequence[int],
    asset_cfg: SceneEntityCfg,
    position: tuple[float, float, float] = (0.4, 0.0, 0.78),  # テーブル上 (75cm + 3cm)
    position_noise: float = 0.02,
):
    """Reset cable to initial position on table with optional noise.

    IMPORTANT: Position is in local (environment) coordinates.
    We must add env_origins to get world coordinates for write_root_state_to_sim.
    """
    asset: RigidObject = env.scene[asset_cfg.name]

    num_resets = len(env_ids)
    device = env.device

    # Get environment origins for the reset environments
    env_origins = env.scene.env_origins[env_ids]  # [num_resets, 3]

    # Base position in local coordinates with noise
    pos_local = torch.tensor(position, device=device).unsqueeze(0).repeat(num_resets, 1)
    if position_noise > 0:
        pos_local[:, :2] += torch.randn(num_resets, 2, device=device) * position_noise

    # Convert to world coordinates by adding env_origins
    pos_world = pos_local + env_origins

    # Identity rotation
    rot = torch.tensor([1.0, 0.0, 0.0, 0.0], device=device).unsqueeze(0).repeat(num_resets, 1)

    # Zero velocity
    vel = torch.zeros(num_resets, 6, device=device)

    asset.write_root_state_to_sim(
        root_state=torch.cat([pos_world, rot, vel], dim=-1),
        env_ids=env_ids,
    )


def reset_scene(
    env: ManagerBasedEnv,
    env_ids: Sequence[int],
):
    """Reset entire scene for specified environments."""
    # Reset robot
    reset_robot_to_default(env, env_ids, SceneEntityCfg(name="robot"))
    
    # Reset cable
    reset_cable_on_table(env, env_ids, SceneEntityCfg(name="cable"))


# =============================================================================
# Environment Configuration (Isaac Lab 2.3.0 API)
# =============================================================================

@configclass
class ActionsCfg:
    """Action specifications for the MDP."""
    joint_pos = JointPositionActionCfg(
        asset_name="robot",
        joint_names=["panda_joint[1-7]"],
        scale=0.5,  # 増加: 0.1 → 0.5
    )
    gripper = GripperActionCfg(
        asset_name="robot",
        joint_names=["panda_finger_joint.*"],
        binary=False,
    )


@configclass
class ObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class PolicyCfg(ObservationGroupCfg):
        """Observations for policy group."""
        # Robot state
        joint_pos_obs = ObservationTermCfg(
            func=joint_pos,
            params={"asset_cfg": SceneEntityCfg(name="robot")},
        )
        joint_vel_obs = ObservationTermCfg(
            func=joint_vel,
            params={"asset_cfg": SceneEntityCfg(name="robot")},
            scale=0.1,
        )
        gripper_pos_obs = ObservationTermCfg(
            func=gripper_pos,
            params={"asset_cfg": SceneEntityCfg(name="robot")},
        )
        # Task state
        ee_to_cable_obs = ObservationTermCfg(
            func=ee_to_cable_vec,
            params={
                "robot_cfg": SceneEntityCfg(name="robot"),
                "cable_cfg": SceneEntityCfg(name="cable"),
            },
        )
        cable_to_hook_obs = ObservationTermCfg(
            func=cable_to_hook_vec,
            params={
                "cable_cfg": SceneEntityCfg(name="cable"),
                "hook_cfg": SceneEntityCfg(name="hook"),
            },
        )
        cable_vel_obs = ObservationTermCfg(
            func=cable_vel_w,
            params={"asset_cfg": SceneEntityCfg(name="cable")},
            scale=0.1,
        )

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    # observation groups
    policy: PolicyCfg = PolicyCfg()


@configclass
class EventsCfg:
    """Configuration for events."""
    reset_scene_event = EventTermCfg(
        func=reset_scene,
        mode="reset",
    )


@configclass
class RewardsCfg:
    """Reward terms for the MDP."""
    # 主要報酬: ケーブルへの接近を強化
    approach_cable = RewardTermCfg(
        func=approach_cable_reward,
        weight=5.0,
        params={
            "robot_cfg": SceneEntityCfg(name="robot"),
            "cable_cfg": SceneEntityCfg(name="cable"),
            "std": 2.0,  # 大幅増加: 0.5 → 2.0 (遠距離でも勾配を得る)
        },
    )
    grasp = RewardTermCfg(
        func=grasp_reward,
        weight=2.0,  # 増加: 1.0 → 2.0
        params={
            "robot_cfg": SceneEntityCfg(name="robot"),
            "cable_cfg": SceneEntityCfg(name="cable"),
        },
    )
    lift = RewardTermCfg(
        func=lift_reward,
        weight=1.0,  # 増加: 0.5 → 1.0
        params={
            "cable_cfg": SceneEntityCfg(name="cable"),
            "target_lift": 0.15,
        },
    )
    approach_hook = RewardTermCfg(
        func=approach_hook_reward,
        weight=1.0,
        params={
            "cable_cfg": SceneEntityCfg(name="cable"),
            "hook_cfg": SceneEntityCfg(name="hook"),
            "std": 0.1,
        },
    )
    alignment = RewardTermCfg(
        func=alignment_reward,
        weight=2.0,
        params={
            "cable_cfg": SceneEntityCfg(name="cable"),
            "hook_cfg": SceneEntityCfg(name="hook"),
        },
    )
    success = RewardTermCfg(
        func=hanging_success_reward,
        weight=1.0,
        params={
            "robot_cfg": SceneEntityCfg(name="robot"),
            "cable_cfg": SceneEntityCfg(name="cable"),
            "hook_cfg": SceneEntityCfg(name="hook"),
            "bonus": 10.0,
        },
    )
    time_penalty_term = RewardTermCfg(
        func=time_penalty,
        weight=0.5,  # 減少: 1.0 → 0.5
        params={"penalty": -0.01},
    )


@configclass
class TerminationsCfg:
    """Termination terms for the MDP."""
    time_out_term = TerminationTermCfg(
        func=time_out,
        time_out=True,
        params={"max_episode_length": 200},  # 短いエピソードで学習
    )
    # cable_dropped_term - 無効化（ケーブルは重力で落下する）
    # cable_dropped_term = TerminationTermCfg(
    #     func=cable_dropped,
    #     params={"cable_cfg": SceneEntityCfg(name="cable")},
    # )
    success_term = TerminationTermCfg(
        func=task_success,
        params={
            "robot_cfg": SceneEntityCfg(name="robot"),
            "cable_cfg": SceneEntityCfg(name="cable"),
            "hook_cfg": SceneEntityCfg(name="hook"),
        },
    )


@configclass
class HookHangingEnvCfg(ManagerBasedRLEnvCfg):
    """
    Configuration for Hook Hanging RL environment.

    This defines the complete environment including:
    - Scene configuration
    - Observation space
    - Action space
    - Reward function
    - Termination conditions
    - Domain randomization
    """

    # Scene
    scene: HookHangingSceneCfgSingleArm = HookHangingSceneCfgSingleArm(num_envs=256, env_spacing=2.0)

    # MDP settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventsCfg = EventsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    def __post_init__(self) -> None:
        """Post initialization."""
        # general settings
        self.decimation = 2
        self.episode_length_s = 8.0
        # simulation settings
        self.sim.dt = 1/120.0
        self.sim.render_interval = self.decimation
        self.sim.gravity = (0.0, 0.0, -9.81)
        self.sim.physx.solver_type = 1  # TGS


# =============================================================================
# Environment Class
# =============================================================================

class HookHangingEnv(ManagerBasedRLEnv):
    """
    Hook Hanging Environment for THREAD.
    
    This environment implements the hook hanging task where a robot
    must grasp a cable from a table and hang it on a hook.
    
    Task phases:
    1. Approach - Move gripper to cable
    2. Grasp - Close gripper on cable
    3. Lift - Raise cable above table
    4. Move - Transport to hook position
    5. Hang - Release cable on hook
    
    Observation space (concatenated):
    - Joint positions (9): normalized arm + gripper joints
    - Joint velocities (9): scaled velocities
    - Gripper position (1): average finger opening
    - EE to cable vector (3): direction to grasp
    - Cable to hook vector (3): direction to goal
    - Cable velocity (3): for stability estimation
    Total: 28 dimensions
    
    Action space:
    - Joint positions (7): arm joint targets
    - Gripper (1): gripper opening command
    Total: 8 dimensions
    """
    
    cfg: HookHangingEnvCfg
    
    def __init__(self, cfg: HookHangingEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        
        # Store references for convenience
        self.robot = self.scene["robot"]
        self.cable = self.scene["cable"]
        self.hook = self.scene["hook"]
        
        # Task phase tracking
        self.phase = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        # 0: approach, 1: grasp, 2: lift, 3: move, 4: hang
        
        # Success tracking
        self.success_count = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
    
    def _get_observations(self) -> dict:
        """Get observations for all environments."""
        return super()._get_observations()
    
    def _get_rewards(self) -> torch.Tensor:
        """Compute rewards for all environments."""
        return super()._get_rewards()
    
    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Get termination flags."""
        return super()._get_dones()
    
    def _reset_idx(self, env_ids: Sequence[int]):
        """Reset specified environments."""
        super()._reset_idx(env_ids)
        
        # Reset phase tracking
        self.phase[env_ids] = 0
        self.success_count[env_ids] = 0


# =============================================================================
# Print Configuration
# =============================================================================

def print_env_config():
    """Print environment configuration summary."""
    cfg = HookHangingEnvCfg()
    
    print("=" * 70)
    print("THREAD HOOK HANGING ENVIRONMENT CONFIGURATION")
    print("=" * 70)
    
    print(f"\n[Simulation]")
    print(f"  Physics dt: {cfg.sim.dt:.4f}s ({1/cfg.sim.dt:.0f} Hz)")
    print(f"  Control decimation: {cfg.decimation}")
    print(f"  Control rate: {1/(cfg.sim.dt * cfg.decimation):.0f} Hz")
    print(f"  Episode length: {cfg.episode_length_s}s")
    print(f"  Max steps: {int(cfg.episode_length_s / (cfg.sim.dt * cfg.decimation))}")
    
    print(f"\n[Scene]")
    print(f"  Num environments: {cfg.scene.num_envs}")
    print(f"  Environment spacing: {cfg.scene.env_spacing}m")
    
    print(f"\n[Observations]")
    obs_dim = 28  # Approximate
    print(f"  Dimension: ~{obs_dim}")
    print(f"  Components: joint_pos, joint_vel, gripper_pos,")
    print(f"              ee_to_cable, cable_to_hook, cable_vel")
    
    print(f"\n[Actions]")
    print(f"  Dimension: 8 (7 arm joints + 1 gripper)")
    print(f"  Type: Joint position targets")
    
    print(f"\n[Rewards]")
    for name, term in cfg.rewards.items():
        print(f"  {name}: weight={term.weight}")
    
    print(f"\n[Terminations]")
    for name in cfg.terminations.keys():
        print(f"  - {name}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_env_config()
