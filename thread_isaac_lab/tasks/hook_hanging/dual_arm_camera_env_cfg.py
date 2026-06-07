#!/usr/bin/env python3
"""
THREAD: Dual Arm Camera Environment Configuration
==================================================

Integrates dual Franka Panda arms with multi-camera observations:
- Left wrist camera (224x224)
- Right wrist camera (224x224)
- Overhead camera (640x480)

Uses TiledCamera for efficient parallel rendering.

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import math
from dataclasses import MISSING

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sensors import TiledCameraCfg, ContactSensorCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.assets_cfg import CableSegmentedCfg, SimpleHookCfg


# =============================================================================
# Constants
# =============================================================================

FRANKA_PANDA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"

# Workspace dimensions
TABLE_WIDTH = 1.0
TABLE_DEPTH = 0.8
TABLE_HEIGHT = 0.75

# Robot positions
ARM_X_POS = 0.2
ARM_Y_OFFSET = 0.3


# =============================================================================
# Robot Configurations
# =============================================================================

@configclass
class LeftFrankaCameraCfg(ArticulationCfg):
    """Left Franka Panda with wrist camera mount."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Left"

    spawn: sim_utils.UsdFileCfg = sim_utils.UsdFileCfg(
        usd_path=FRANKA_PANDA_USD,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=12,
            solver_velocity_iteration_count=1,
        ),
    )

    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=(ARM_X_POS, -ARM_Y_OFFSET, 0.0),
        rot=(1.0, 0.0, 0.0, 0.0),
        joint_pos={
            "panda_joint1": 0.3,
            "panda_joint2": -0.569,
            "panda_joint3": 0.0,
            "panda_joint4": -2.810,
            "panda_joint5": 0.0,
            "panda_joint6": 3.037,
            "panda_joint7": 0.741,
            "panda_finger_joint1": 0.04,
            "panda_finger_joint2": 0.04,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit_sim=87.0,
            stiffness=80.0,
            damping=4.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit_sim=12.0,
            stiffness=80.0,
            damping=4.0,
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit_sim=200.0,
            stiffness=2000.0,
            damping=100.0,
        ),
    }


@configclass
class RightFrankaCameraCfg(ArticulationCfg):
    """Right Franka Panda with wrist camera mount."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Right"

    spawn: sim_utils.UsdFileCfg = sim_utils.UsdFileCfg(
        usd_path=FRANKA_PANDA_USD,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=12,
            solver_velocity_iteration_count=1,
        ),
    )

    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=(ARM_X_POS, ARM_Y_OFFSET, 0.0),
        rot=(1.0, 0.0, 0.0, 0.0),
        joint_pos={
            "panda_joint1": -0.3,
            "panda_joint2": -0.569,
            "panda_joint3": 0.0,
            "panda_joint4": -2.810,
            "panda_joint5": 0.0,
            "panda_joint6": 3.037,
            "panda_joint7": 0.741,
            "panda_finger_joint1": 0.04,
            "panda_finger_joint2": 0.04,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit_sim=87.0,
            stiffness=80.0,
            damping=4.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit_sim=12.0,
            stiffness=80.0,
            damping=4.0,
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit_sim=200.0,
            stiffness=2000.0,
            damping=100.0,
        ),
    }


# =============================================================================
# TiledCamera Configurations
# =============================================================================

@configclass
class LeftWristTiledCameraCfg(TiledCameraCfg):
    """Left wrist-mounted tiled camera for efficient parallel rendering."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Left/panda_hand/LeftWristCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=12.0,
        focus_distance=100.0,
        horizontal_aperture=15.0,
        clipping_range=(0.01, 2.0),
    )

    offset: TiledCameraCfg.OffsetCfg = TiledCameraCfg.OffsetCfg(
        pos=(0.05, 0.0, 0.04),
        rot=(0.707, 0.0, 0.707, 0.0),  # Looking forward
        convention="ros",
    )

    width: int = 224
    height: int = 224
    data_types: list[str] = ["rgb"]
    return_latest_camera_pose: bool = False


@configclass
class RightWristTiledCameraCfg(TiledCameraCfg):
    """Right wrist-mounted tiled camera."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Right/panda_hand/RightWristCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=12.0,
        focus_distance=100.0,
        horizontal_aperture=15.0,
        clipping_range=(0.01, 2.0),
    )

    offset: TiledCameraCfg.OffsetCfg = TiledCameraCfg.OffsetCfg(
        pos=(0.05, 0.0, 0.04),
        rot=(0.707, 0.0, 0.707, 0.0),
        convention="ros",
    )

    width: int = 224
    height: int = 224
    data_types: list[str] = ["rgb"]
    return_latest_camera_pose: bool = False


@configclass
class OverheadTiledCameraCfg(TiledCameraCfg):
    """Overhead tiled camera for workspace observation."""

    prim_path: str = "{ENV_REGEX_NS}/OverheadCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=18.0,
        focus_distance=400.0,
        horizontal_aperture=20.955,
        clipping_range=(0.1, 10.0),
    )

    offset: TiledCameraCfg.OffsetCfg = TiledCameraCfg.OffsetCfg(
        pos=(0.5, 0.0, 1.5),
        rot=(0.5, 0.5, -0.5, -0.5),  # Looking down
        convention="world",
    )

    width: int = 640
    height: int = 480
    data_types: list[str] = ["rgb"]
    return_latest_camera_pose: bool = False


# =============================================================================
# Table Configuration
# =============================================================================

@configclass
class DualArmTableCfg(RigidObjectCfg):
    """Workspace table."""

    prim_path: str = "{ENV_REGEX_NS}/Table"

    spawn: sim_utils.CuboidCfg = sim_utils.CuboidCfg(
        size=(TABLE_WIDTH, TABLE_DEPTH, 0.02),
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=True,
            disable_gravity=True,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.6, 0.5, 0.4),
            metallic=0.0,
            roughness=0.8,
        ),
        physics_material=sim_utils.RigidBodyMaterialCfg(
            static_friction=0.5,
            dynamic_friction=0.5,
            restitution=0.0,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.5, 0.0, TABLE_HEIGHT - 0.01),
        rot=(1.0, 0.0, 0.0, 0.0),
    )


# =============================================================================
# Scene Configuration
# =============================================================================

@configclass
class DualArmCameraSceneCfg(InteractiveSceneCfg):
    """
    Complete dual arm scene with cameras.

    Includes:
    - 2x Franka Panda robots
    - 3x TiledCameras (2 wrist + 1 overhead)
    - Table, Hook, Cable
    """

    num_envs: int = 128  # Reduced for camera memory
    env_spacing: float = 3.0

    # Ground plane
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # Lighting
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0)),
    )

    spot_light = AssetBaseCfg(
        prim_path="/World/SpotLight",
        spawn=sim_utils.SphereLightCfg(
            intensity=5000.0,
            color=(1.0, 0.98, 0.95),
            radius=0.1,
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.5, 0.0, 1.5)),
    )

    # Robots
    robot_left: LeftFrankaCameraCfg = LeftFrankaCameraCfg()
    robot_right: RightFrankaCameraCfg = RightFrankaCameraCfg()

    # Table
    table: DualArmTableCfg = DualArmTableCfg()

    # Hook
    hook: SimpleHookCfg = SimpleHookCfg(
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.5, 0.0, TABLE_HEIGHT + 0.15),
            rot=(1.0, 0.0, 0.0, 0.0),
        )
    )

    # Cable
    cable: CableSegmentedCfg = CableSegmentedCfg(
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.5, 0.0, TABLE_HEIGHT + 0.05),
            rot=(1.0, 0.0, 0.0, 0.0),
        )
    )

    # Cameras (TiledCamera for efficient rendering)
    left_wrist_camera: LeftWristTiledCameraCfg = LeftWristTiledCameraCfg()
    right_wrist_camera: RightWristTiledCameraCfg = RightWristTiledCameraCfg()
    overhead_camera: OverheadTiledCameraCfg = OverheadTiledCameraCfg()


# =============================================================================
# Environment Configuration
# =============================================================================

@configclass
class DualArmCameraEnvCfg(DirectRLEnvCfg):
    """
    Configuration for Dual Arm Camera Environment.

    Observation Space:
    - Proprioception: 46D (23 per arm)
    - Visual: 3 camera images

    Action Space: 18D (9 per arm)
    """

    # Scene
    scene: DualArmCameraSceneCfg = DualArmCameraSceneCfg()

    # Simulation
    decimation: int = 2
    episode_length_s: float = 10.0

    # Spaces
    num_actions: int = 18  # 9 joints per arm x 2
    num_observations: int = 46  # Proprioception only (images handled separately)

    # Reward scales
    approach_reward_scale: float = 0.35
    grasp_reward_scale: float = 0.15
    coordination_reward_scale: float = 0.10
    task_reward_scale: float = 0.35
    height_reward_scale: float = 0.05
    action_penalty_scale: float = 0.01

    # Task parameters
    grasp_threshold: float = 0.08
    optimal_arm_separation: float = 0.30
    max_arm_separation: float = 0.60


# =============================================================================
# Observation Helpers
# =============================================================================

def get_proprioceptive_obs_dim() -> int:
    """Return proprioceptive observation dimension."""
    # Per arm: 9 joint pos + 9 joint vel + 3 EE pos + 2 gripper width = 23
    # Total: 23 * 2 = 46
    return 46


def get_visual_obs_shapes() -> dict:
    """Return visual observation shapes."""
    return {
        "left_wrist": (224, 224, 3),
        "right_wrist": (224, 224, 3),
        "overhead": (640, 480, 3),
    }


def compute_proprioceptive_obs(robot_left, robot_right) -> dict:
    """
    Compute proprioceptive observations for both arms.

    Returns dict with:
    - left_joint_pos: (N, 9)
    - left_joint_vel: (N, 9)
    - left_ee_pos: (N, 3)
    - right_joint_pos: (N, 9)
    - right_joint_vel: (N, 9)
    - right_ee_pos: (N, 3)
    """
    return {
        "left_joint_pos": robot_left.data.joint_pos,
        "left_joint_vel": robot_left.data.joint_vel,
        "left_ee_pos": robot_left.data.body_pos_w[:, 8, :],
        "right_joint_pos": robot_right.data.joint_pos,
        "right_joint_vel": robot_right.data.joint_vel,
        "right_ee_pos": robot_right.data.body_pos_w[:, 8, :],
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Dual Arm Camera Environment Configuration")
    print("=" * 60)

    cfg = DualArmCameraEnvCfg()

    print(f"\n[Scene]")
    print(f"  Num environments: {cfg.scene.num_envs}")
    print(f"  Env spacing: {cfg.scene.env_spacing}m")

    print(f"\n[Observations]")
    print(f"  Proprioceptive dim: {get_proprioceptive_obs_dim()}")
    for name, shape in get_visual_obs_shapes().items():
        print(f"  {name}: {shape}")

    print(f"\n[Actions]")
    print(f"  Action dim: {cfg.num_actions}")

    print(f"\n[Rewards]")
    print(f"  Approach scale: {cfg.approach_reward_scale}")
    print(f"  Grasp scale: {cfg.grasp_reward_scale}")
    print(f"  Coordination scale: {cfg.coordination_reward_scale}")
    print(f"  Task scale: {cfg.task_reward_scale}")
    print(f"  Height scale: {cfg.height_reward_scale}")

    print(f"\n[Cameras]")
    print(f"  Left wrist: 224x224 RGB")
    print(f"  Right wrist: 224x224 RGB")
    print(f"  Overhead: 640x480 RGB")

    print("\n" + "=" * 60)
