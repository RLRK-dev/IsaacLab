#!/usr/bin/env python3
"""
THREAD: Dual Arm Configuration for Isaac Lab
=============================================

Dual Franka Panda configuration with:
- Symmetric left/right arm placement
- 4x Fixed cameras: front_left, front_right, back, overhead

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import math
from dataclasses import MISSING

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sensors import CameraCfg, ContactSensorCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

from isaaclab.sim.spawners import UsdFileCfg, UrdfFileCfg

from .assets_cfg import (
    CableSegmentedCfg,
    SimpleHookCfg,
    YHookStemCfg,
    YHookLeftArmCfg,
    YHookRightArmCfg,
    TableCfg,
)

# Segmented cable USD path (20 segments, articulated)
# Original revolute joint cable (limited flexibility) - zigzag pattern, NOT Y-axis:
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/segmented_cable.usd"
# SphericalJoint cable v1 (3-axis flexibility) - unstable, do not use:
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable.usd"
# SphericalJoint cable v2 (stabilized: heavier mass, reduced cone angle, increased solver iterations) - still causes NaN:
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v2.usd"
# SphericalJoint cable v3 (Y-axis layout, DriveAPI damping fixed, 20 segments x 3cm = 60cm):
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v3.usd"
# SphericalJoint cable v4 (ultra-high damping=50.0, solver iterations 64/16):
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v4.usd"
# SphericalJoint cable v5 (rigid body damping: linear=10, angular=10 per segment):
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v5.usd"
# SphericalJoint cable v6 (moderate damping=2.0 for D6 joint compatibility) - TOO LOW, immediate NaN:
# SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v6.usd"
# v5 works for Phase 1+2, investigate lift issue separately
SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v5.usd"

# V字溝ケーブル置き台 USD path
CABLE_CRADLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/objects/cable_cradle.usd"


# =============================================================================
# Constants
# =============================================================================

FRANKA_PANDA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"

# Workspace dimensions (meters)
TABLE_WIDTH = 0.8
TABLE_DEPTH = 0.6
TABLE_HEIGHT = 0.75

# Robot base positions - wall-mounted configuration
# Option C: X-axis cable layout - robots at sides, cable along X-axis
ARM_X_POS = -0.10    # X position: wall-mounted behind table
ARM_Z_POS = 1.00     # Z position: lowered from 1.10 to allow reaching cable at Z=0.756
# Y positions: robots at Y=±0.35 (wider spacing for X-axis cable reach)
ARM_LEFT_Y = -0.35   # Left arm at Y=-0.35
ARM_RIGHT_Y = 0.35   # Right arm at Y=+0.35


# =============================================================================
# Left Arm Configuration
# =============================================================================

@configclass
class LeftFrankaCfg(ArticulationCfg):
    """Configuration for Left Franka Panda arm."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Left"

    spawn: sim_utils.UsdFileCfg = sim_utils.UsdFileCfg(
        usd_path=FRANKA_PANDA_USD,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,  # CRITICAL: Must be True for IK tracking!
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=12,
            solver_velocity_iteration_count=1,
        ),
    )

    # Initial state - v24: Higher EE to avoid touching cable
    # joint2=0.0 (was 0.5) -> raises EE by ~10cm
    # joint4=-1.5 (was -2.2) -> extends arm less, keeps EE higher
    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=(ARM_X_POS, ARM_LEFT_Y, ARM_Z_POS),
        rot=(0.7071, 0.0, 0.7071, 0.0),  # Y+90° only: 前方（+X）を向く
        joint_pos={
            "panda_joint1": 0.0,   # Neutral
            "panda_joint2": 0.0,   # v24: More upright = EE higher
            "panda_joint3": 0.0,
            "panda_joint4": -1.5,  # v24: Less bent = EE higher and more forward
            "panda_joint5": 0.0,
            "panda_joint6": 1.5,   # v24: Match joint4 for smooth arm shape
            "panda_joint7": 0.785, # 45 deg rotation
            "panda_finger_joint1": 0.04,
            "panda_finger_joint2": 0.04,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
        # HIGH PD gains for IK tracking (same as FRANKA_PANDA_HIGH_PD_CFG)
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit_sim=87.0,
            stiffness=400.0,  # 5x higher for IK
            damping=80.0,     # 20x higher for IK
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit_sim=12.0,
            stiffness=400.0,  # 5x higher for IK
            damping=80.0,     # 20x higher for IK
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit_sim=200.0,
            stiffness=2000.0,
            damping=100.0,
        ),
    }


# =============================================================================
# Right Arm Configuration
# =============================================================================

@configclass
class RightFrankaCfg(ArticulationCfg):
    """Configuration for Right Franka Panda arm (mirror of left)."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Right"

    spawn: sim_utils.UsdFileCfg = sim_utils.UsdFileCfg(
        usd_path=FRANKA_PANDA_USD,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,  # CRITICAL: Must be True for IK tracking!
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=12,
            solver_velocity_iteration_count=1,
        ),
    )

    # Initial state - same as left arm for symmetry
    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=(ARM_X_POS, ARM_RIGHT_Y, ARM_Z_POS),
        rot=(0.7071, 0.0, 0.7071, 0.0),  # Y+90° only: 前方（+X）を向く
        joint_pos={
            "panda_joint1": 0.0,   # Neutral
            "panda_joint2": 0.0,   # Upright
            "panda_joint3": 0.0,
            "panda_joint4": -1.5,  # Less bent = EE higher and more forward
            "panda_joint5": 0.0,
            "panda_joint6": 1.5,   # Match joint4 for smooth arm shape
            "panda_joint7": 0.785, # 45 deg rotation
            "panda_finger_joint1": 0.04,
            "panda_finger_joint2": 0.04,
        },
        joint_vel={".*": 0.0},
    )

    actuators: dict = {
        # HIGH PD gains for IK tracking (same as FRANKA_PANDA_HIGH_PD_CFG)
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit_sim=87.0,
            stiffness=400.0,  # 5x higher for IK
            damping=80.0,     # 20x higher for IK
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit_sim=12.0,
            stiffness=400.0,  # 5x higher for IK
            damping=80.0,     # 20x higher for IK
        ),
        "panda_hand": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger_joint.*"],
            effort_limit_sim=200.0,
            stiffness=2000.0,
            damping=100.0,
        ),
    }


# =============================================================================
# Camera Configurations (4カメラ: front_left, front_right, back, overhead)
# ターゲット: テーブル中心 (0.4, 0, 0.85)
# =============================================================================

@configclass
class FrontLeftCameraCfg(CameraCfg):
    """Front-Left camera - 左前方からワークスペースを見る

    位置: (0.7, -0.40, 1.15)
    向き: yaw=127°, pitch=31° (中心方向 + 下向き)
    用途: 右アーム・ケーブル右側の観察
    """

    prim_path: str = "{ENV_REGEX_NS}/FrontLeftCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=18.0,  # 広角化
        horizontal_aperture=25.0,  # 広い視野
        clipping_range=(0.1, 10.0),
    )

    offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
        pos=(0.7, -0.35, 0.90),  # フック方向に向ける
        rot=(0.1802, -0.1268, 0.0436, 0.9744),  # フック(0.25,0,0.86)向き
        convention="world",
    )

    width: int = 256
    height: int = 256
    data_types: list[str] = ["rgb"]
    update_period: float = 0.0


@configclass
class FrontRightCameraCfg(CameraCfg):
    """Front-Right camera - 右前方からワークスペースを見る

    位置: (0.8, 0.35, 0.95)
    向き: yaw=-127°, pitch=20° (浅い角度)
    用途: 左アーム・ケーブル左側の観察
    """

    prim_path: str = "{ENV_REGEX_NS}/FrontRightCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=18.0,  # 広角化
        horizontal_aperture=25.0,  # 広い視野
        clipping_range=(0.1, 10.0),
    )

    offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
        pos=(0.7, 0.35, 0.90),  # フック方向に向ける
        rot=(0.1802, 0.1268, 0.0436, -0.9744),  # フック(0.25,0,0.86)向き（ミラー）
        convention="world",
    )

    width: int = 256
    height: int = 256
    data_types: list[str] = ["rgb"]
    update_period: float = 0.0


@configclass
class BackCameraCfg(CameraCfg):
    """Back camera - 後方からターゲットを見る

    位置: (0.0, 0.0, 0.95)
    向き: yaw=0°, pitch=14° (前方向き + 下向き)
    用途: 全体の後方視点、両アームとケーブルの位置関係
    """

    prim_path: str = "{ENV_REGEX_NS}/BackCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=18.0,  # 広角化
        horizontal_aperture=25.0,  # 広い視野
        clipping_range=(0.1, 10.0),
    )

    offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
        pos=(-0.5, 0.0, 1.0),  # 後ろから見る
        rot=(0.9659, 0.0, 0.2588, 0.0),  # pitch 30° to look down
        convention="world",
    )

    width: int = 256
    height: int = 256
    data_types: list[str] = ["rgb"]
    update_period: float = 0.0


@configclass
class OverheadCameraCfg(CameraCfg):
    """Overhead camera - 真上から広角でワークスペース全体を見る

    位置: (0.4, 0.0, 1.6)
    向き: yaw=0°, pitch=-90° (真下向き)
    用途: 全体俯瞰、ケーブル形状・フック位置の把握
    """

    prim_path: str = "{ENV_REGEX_NS}/OverheadCamera"

    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=18.0,  # 広角レンズ
        horizontal_aperture=25.0,  # 広い視野
        clipping_range=(0.1, 10.0),
    )

    offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
        pos=(0.4, 0.0, 1.6),
        rot=(0.7071, 0.0, 0.7071, 0.0),  # world convention: pitch 90° to look down
        convention="world",
    )

    width: int = 256
    height: int = 256
    data_types: list[str] = ["rgb"]
    update_period: float = 0.0


# =============================================================================
# Contact Sensor Configurations
# =============================================================================

@configclass
class LeftGripperContactCfg(ContactSensorCfg):
    """Contact sensor for Left gripper fingers."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Left/panda_leftfinger"
    update_period: float = 0.0
    track_air_time: bool = False
    filter_prim_paths_expr: list[str] = ["{ENV_REGEX_NS}/Cable.*"]


@configclass
class RightGripperContactCfg(ContactSensorCfg):
    """Contact sensor for Right gripper fingers."""

    prim_path: str = "{ENV_REGEX_NS}/Robot_Right/panda_leftfinger"
    update_period: float = 0.0
    track_air_time: bool = False
    filter_prim_paths_expr: list[str] = ["{ENV_REGEX_NS}/Cable.*"]


# =============================================================================
# Table Configuration for Dual Arm
# =============================================================================

@configclass
class DualArmTableCfg(RigidObjectCfg):
    """
    Workspace table for dual arm configuration.

    Larger table to accommodate both arms' workspaces.
    Grid texture applied for visual calibration.
    """

    prim_path: str = "{ENV_REGEX_NS}/Table"

    spawn: sim_utils.CuboidCfg = sim_utils.CuboidCfg(
        size=(1.2, 0.8, 0.02),  # 120cm x 80cm x 2cm (extended forward 20%)
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=True,
            disable_gravity=True,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.92, 0.90, 0.84),  # ベージュ
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
        pos=(0.35, 0.0, TABLE_HEIGHT - 0.01),  # Extended forward: center shifted from 0.25 to 0.35
        rot=(1.0, 0.0, 0.0, 0.0),
    )


# =============================================================================
# Complete Dual Arm Scene Configuration
# =============================================================================

@configclass
class DualArmSceneCfg(InteractiveSceneCfg):
    """
    Complete scene configuration for Dual Arm Hook Hanging task.

    Layout (top view):
                        Table
                    ┌───────────┐
         Robot_Left │   Cable   │ Robot_Right
              ●     │     ○     │     ●
              │     │   Hook    │     │
              │     └───────────┘     │
              └───────────┬───────────┘
                    Workspace

    Components:
    - 2x Franka Panda robots (symmetric placement)
    - 4x Fixed cameras: front_left, front_right, back, overhead
    - Table workspace
    - Hook target
    - Cable object
    """

    num_envs: int = 256
    env_spacing: float = 3.0  # Larger spacing for dual arm

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

    # Spot light above workspace
    spot_light = AssetBaseCfg(
        prim_path="/World/SpotLight",
        spawn=sim_utils.SphereLightCfg(
            intensity=5000.0,
            color=(1.0, 0.98, 0.95),
            radius=0.1,
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.4, 0.0, 1.5),  # Above table
        ),
    )

    # Robots
    robot_left: LeftFrankaCfg = LeftFrankaCfg()
    robot_right: RightFrankaCfg = RightFrankaCfg()

    # Table
    table: DualArmTableCfg = DualArmTableCfg()

    # Y字フック (3パーツ: 茎 + 左腕 + 右腕)
    # Plan A: Hook at cable center for X-axis cable layout
    # Cable spawn at X=0.50 puts both ends in front of robot at X=-0.10
    hook_stem: YHookStemCfg = YHookStemCfg(
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.25, 0.0, TABLE_HEIGHT + 0.04),  # 茎: 推定ケーブル中央
            rot=(1.0, 0.0, 0.0, 0.0),
        )
    )
    hook_left_arm: YHookLeftArmCfg = YHookLeftArmCfg(
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.25, -0.025, TABLE_HEIGHT + 0.11),  # 左腕: 茎の上、左に傾斜
            rot=(0.966, 0.259, 0.0, 0.0),  # X軸周り30度
        )
    )
    hook_right_arm: YHookRightArmCfg = YHookRightArmCfg(
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.25, 0.025, TABLE_HEIGHT + 0.11),  # 右腕: 茎の上、右に傾斜
            rot=(0.966, -0.259, 0.0, 0.0),  # X軸周り-30度
        )
    )

    # Cable (articulated 20-segment chain)
    # Plan A: X-axis cable layout - cable lies along X direction
    # Cable spawn at X=0.50 puts both ends in front of robot at X=-0.10
    # Expected cable ends: left≈-0.08, right≈0.49 (both in front of robot)
    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=SEGMENTED_CABLE_USD,
            activate_contact_sensors=False,
            # Add articulation root properties for physics stability
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=128,  # Option C: Ultra high for X-axis stability
                solver_velocity_iteration_count=32,   # Option C: Ultra high for X-axis stability
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            # Option C: X-axis cable layout
            pos=(0.50, 0.0, TABLE_HEIGHT + 0.02),
            rot=(0.7071, 0.0, -0.7071, 0.0),  # Y-axis -90° (cable extends along X-axis)
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],  # Match all joint names (works with both USD versions)
                stiffness=0.0,  # Passive cable (no active control)
                damping=5.0,    # Option C: Higher damping for X-axis stability
            ),
        },
    )

    # V字溝ケーブル置き台 (固定、テーブル上)
    # ケーブルを安定して置くための台
    # TODO: USD file needs RigidBodyAPI applied - temporarily disabled
    # cable_cradle: RigidObjectCfg = RigidObjectCfg(
    #     prim_path="{ENV_REGEX_NS}/CableCradle",
    #     spawn=sim_utils.UsdFileCfg(
    #         usd_path=CABLE_CRADLE_USD,
    #         rigid_props=sim_utils.RigidBodyPropertiesCfg(
    #             kinematic_enabled=True,  # 固定（動かない）
    #         ),
    #     ),
    #     init_state=RigidObjectCfg.InitialStateCfg(
    #         pos=(0.225, 0.0, TABLE_HEIGHT),  # ケーブル中央下、テーブル面
    #         rot=(1.0, 0.0, 0.0, 0.0),  # 回転なし（溝がY方向）
    #     ),
    # )

    # Cameras (4カメラ: front_left, front_right, back, overhead)
    front_left_camera: FrontLeftCameraCfg = FrontLeftCameraCfg()
    front_right_camera: FrontRightCameraCfg = FrontRightCameraCfg()
    back_camera: BackCameraCfg = BackCameraCfg()
    overhead_camera: OverheadCameraCfg = OverheadCameraCfg()


# =============================================================================
# Helper Functions
# =============================================================================

def get_camera_intrinsics(camera_cfg: CameraCfg) -> dict:
    """
    Get camera intrinsic parameters from configuration.

    Returns:
        Dictionary with fx, fy, cx, cy, width, height
    """
    focal_length = camera_cfg.spawn.focal_length
    horizontal_aperture = camera_cfg.spawn.horizontal_aperture
    width = camera_cfg.width
    height = camera_cfg.height

    # Compute focal length in pixels
    fx = focal_length * width / horizontal_aperture
    fy = fx  # Assume square pixels

    # Principal point at image center
    cx = width / 2.0
    cy = height / 2.0

    return {
        "fx": fx,
        "fy": fy,
        "cx": cx,
        "cy": cy,
        "width": width,
        "height": height,
    }


def print_dual_arm_config():
    """Print dual arm configuration summary."""
    cfg = DualArmSceneCfg()

    print("=" * 70)
    print("THREAD DUAL ARM SCENE CONFIGURATION")
    print("=" * 70)

    print(f"\n[Environment]")
    print(f"  Num environments: {cfg.num_envs}")
    print(f"  Environment spacing: {cfg.env_spacing}m")

    print(f"\n[Robots]")
    print(f"  Left arm:")
    print(f"    Position: ({cfg.robot_left.init_state.pos[0]:.2f}, "
          f"{cfg.robot_left.init_state.pos[1]:.2f}, "
          f"{cfg.robot_left.init_state.pos[2]:.2f})")
    print(f"  Right arm:")
    print(f"    Position: ({cfg.robot_right.init_state.pos[0]:.2f}, "
          f"{cfg.robot_right.init_state.pos[1]:.2f}, "
          f"{cfg.robot_right.init_state.pos[2]:.2f})")
    print(f"  Arm separation: {abs(ARM_LEFT_Y) + abs(ARM_RIGHT_Y):.2f}m")

    print(f"\n[Table]")
    print(f"  Size: {cfg.table.spawn.size[0]}m x {cfg.table.spawn.size[1]}m")
    print(f"  Height: {TABLE_HEIGHT}m")

    print(f"\n[Cameras] (4カメラ構成)")
    for name, cam in [("Front-Left", cfg.front_left_camera), ("Front-Right", cfg.front_right_camera),
                      ("Back", cfg.back_camera), ("Overhead", cfg.overhead_camera)]:
        print(f"  {name} camera:")
        print(f"    Resolution: {cam.width}x{cam.height}")
        print(f"    Position: {cam.offset.pos}")

    # Camera intrinsics
    print(f"\n[Camera Intrinsics]")
    for name, cam_cfg in [
        ("Front-Left", cfg.front_left_camera),
        ("Front-Right", cfg.front_right_camera),
        ("Back", cfg.back_camera),
        ("Overhead", cfg.overhead_camera),
    ]:
        intrinsics = get_camera_intrinsics(cam_cfg)
        print(f"  {name}: fx={intrinsics['fx']:.1f}, fy={intrinsics['fy']:.1f}, "
              f"cx={intrinsics['cx']:.1f}, cy={intrinsics['cy']:.1f}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_dual_arm_config()
