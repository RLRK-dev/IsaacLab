#!/usr/bin/env python3
"""
THREAD: Isaac Lab Environment Implementation
=============================================

Isaac Sim 5.1.0 / Isaac Lab 2.3.0 compatible implementation
for the Hook Hanging Task described in the THREAD paper.

This module defines:
- Robot configuration (Dual Franka Panda)
- Cable (Deformable Linear Object) configuration  
- Hook and Table assets
- Scene configuration

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import torch
from dataclasses import MISSING
from typing import Literal

# Isaac Lab imports (isaaclab package for Isaac Lab 2.3.0)
import isaaclab.sim as sim_utils
from isaaclab.assets import (
    Articulation,
    ArticulationCfg,
    RigidObject,
    RigidObjectCfg,
)
from isaaclab_physx.assets import DeformableObject, DeformableObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sensors import (
    Camera,
    CameraCfg,
    ContactSensor,
    ContactSensorCfg,
)
from isaaclab.assets import AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR


# =============================================================================
# Constants
# =============================================================================

# Franka Panda USD paths (Isaac Lab assets)
FRANKA_PANDA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"


# =============================================================================
# Robot Configuration: Franka Panda
# =============================================================================

@configclass
class FrankaPandaCfg(ArticulationCfg):
    """Configuration for a single Franka Panda robot arm with Franka Hand gripper."""
    
    # USD asset path
    prim_path: str = MISSING
    
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
    
    # Initial state
    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        # Default home position for Franka
        joint_pos={
            "panda_joint1": 0.0,
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
    
    # Actuator configuration (Isaac Lab 2.3.0 API)
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
class DualFrankaCfg:
    """Configuration for dual Franka Panda setup."""
    
    # Left arm configuration
    left_arm: FrankaPandaCfg = FrankaPandaCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left",
    )
    
    # Right arm configuration  
    right_arm: FrankaPandaCfg = FrankaPandaCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right",
    )
    
    # Base positions (world frame)
    left_base_pos: tuple[float, float, float] = (-0.5, 0.0, 0.0)
    left_base_rot: tuple[float, float, float, float] = (0.707, 0.0, 0.0, 0.707)  # 90° yaw
    
    right_base_pos: tuple[float, float, float] = (0.5, 0.0, 0.0)
    right_base_rot: tuple[float, float, float, float] = (0.707, 0.0, 0.0, -0.707)  # -90° yaw


# =============================================================================
# Cable Configuration (Deformable Linear Object)
# =============================================================================

@configclass  
class CableAssetCfg(DeformableObjectCfg):
    """
    Configuration for deformable cable asset.
    
    The cable is modeled as a chain of connected rigid segments
    with spherical joints. This approximation works well for
    cables that don't require extreme bending.
    
    Physical properties:
    - Length: 30cm
    - Diameter: 8mm
    - Material: PVC-like (density ~1100 kg/m³)
    - 10 segments for computational efficiency
    """
    
    prim_path: str = "{ENV_REGEX_NS}/Cable"
    
    # Cable geometry parameters
    num_segments: int = 20
    segment_length: float = 0.03  # 3cm per segment = 30cm total
    segment_radius: float = 0.004  # 4mm radius = 8mm diameter
    
    spawn: sim_utils.CylinderCfg = sim_utils.CylinderCfg(
        radius=0.004,
        height=0.03,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            max_depenetration_velocity=1.0,
        ),
        mass_props=sim_utils.MassPropertiesCfg(
            mass=0.0017,  # ~17g total / 10 segments
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.2, 0.2, 0.8),  # Blue
        ),
    )
    
    # Deformable properties
    deformable_props: sim_utils.DeformableBodyPropertiesCfg = sim_utils.DeformableBodyPropertiesCfg(
        kinematic_enabled=False,
        simulation_hexahedral_resolution=4,
        collision_simplification=True,
    )
    
    # Initial state
    init_state: DeformableObjectCfg.InitialStateCfg = DeformableObjectCfg.InitialStateCfg(
        pos=(-0.15, 0.4, 0.77),  # On table, left side
        rot=(1.0, 0.0, 0.0, 0.0),  # Identity rotation
    )


@configclass
class CableSegmentedCfg(RigidObjectCfg):
    """
    Alternative cable configuration using segmented rigid bodies.
    
    This is more stable for simulation and easier to work with
    in Isaac Lab. The cable is a chain of rigid cylinders
    connected by fixed joints that allow rotation.
    """
    
    prim_path: str = "{ENV_REGEX_NS}/Cable"
    
    spawn: sim_utils.CylinderCfg = sim_utils.CylinderCfg(
        radius=0.004,
        height=0.03,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=1.0,
            linear_damping=0.1,
            angular_damping=0.5,
        ),
        mass_props=sim_utils.MassPropertiesCfg(
            mass=0.0017,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.9, 0.3, 0.1),  # Orange-red for visibility
            metallic=0.0,
            roughness=0.7,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.4, 0.0, 0.4),  # Height near EE initial position (40cm)
        rot=(1.0, 0.0, 0.0, 0.0),
    )


# =============================================================================
# Hook Configuration
# =============================================================================

@configclass
class HookCfg(RigidObjectCfg):
    """
    Configuration for the hook target.
    
    Hook geometry (side view):
        ┌───┐  ← top (3cm wide)
        │   │
        │   │  ← stem (8cm tall, 1cm diameter)
        │   │
        ────  ← base (fixed to table/stand)
    """
    
    prim_path: str = "{ENV_REGEX_NS}/Hook"
    
    spawn: sim_utils.MultiAssetSpawnerCfg = sim_utils.MultiAssetSpawnerCfg(
        assets_cfg=[
            # Stem (vertical cylinder)
            sim_utils.CylinderCfg(
                radius=0.005,  # 1cm diameter
                height=0.08,   # 8cm tall
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True,  # Fixed in place
                ),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.4, 0.4, 0.4),
                    metallic=0.8,
                    roughness=0.3,
                ),
            ),
            # Top horizontal part
            sim_utils.CylinderCfg(
                radius=0.005,
                height=0.03,  # 3cm wide
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True,
                ),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.4, 0.4, 0.4),
                    metallic=0.8,
                    roughness=0.3,
                ),
            ),
        ],
        random_choice=False,
    )
    
    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.0, 0.45, 0.85),  # 10cm above table (75cm table + 10cm)
        rot=(1.0, 0.0, 0.0, 0.0),
    )


@configclass
class SimpleHookCfg(RigidObjectCfg):
    """Simplified hook using a single cylinder (deprecated - use YHookCfg)."""

    prim_path: str = "{ENV_REGEX_NS}/Hook"

    spawn: sim_utils.CylinderCfg = sim_utils.CylinderCfg(
        radius=0.008,
        height=0.10,
        axis="Z",
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=True,
            disable_gravity=True,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.2, 0.4, 0.8),
            metallic=0.7,
            roughness=0.3,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.4, 0.25, 0.88),
        rot=(1.0, 0.0, 0.0, 0.0),
    )


@configclass
class YHookStemCfg(RigidObjectCfg):
    """Y-hook vertical stem"""

    prim_path: str = "{ENV_REGEX_NS}/YHook_Stem"

    spawn: sim_utils.CylinderCfg = sim_utils.CylinderCfg(
        radius=0.006,     # Diameter 1.2cm
        height=0.04,      # H259: Height 4cm (halved from 8cm)
        axis="Z",
        semantic_tags=[("class", "hook")],  # A6a: semantic label for segmentation
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=True,
            disable_gravity=True,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.3, 0.3, 0.8),  # Blue
            metallic=0.7,
            roughness=0.3,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.4, 0.15, 0.79),  # 4cm above table (75cm + 4cm)
        rot=(1.0, 0.0, 0.0, 0.0),
    )


@configclass
class YHookLeftArmCfg(RigidObjectCfg):
    """Y-hook left arm (angled)"""

    prim_path: str = "{ENV_REGEX_NS}/YHook_LeftArm"

    spawn: sim_utils.CylinderCfg = sim_utils.CylinderCfg(
        radius=0.006,
        height=0.03,      # H259: Length 3cm (halved from 6cm)
        axis="Z",
        semantic_tags=[("class", "hook")],  # A6a: semantic label for segmentation
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=True,
            disable_gravity=True,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.3, 0.3, 0.8),
            metallic=0.7,
            roughness=0.3,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.4, 0.12, 0.86),  # Above stem, tilted left
        rot=(0.966, 0.259, 0.0, 0.0),  # -30 degrees around Y-axis
    )


@configclass
class YHookRightArmCfg(RigidObjectCfg):
    """Y-hook right arm (angled)"""

    prim_path: str = "{ENV_REGEX_NS}/YHook_RightArm"

    spawn: sim_utils.CylinderCfg = sim_utils.CylinderCfg(
        radius=0.006,
        height=0.03,      # H259: Length 3cm (halved from 6cm)
        axis="Z",
        semantic_tags=[("class", "hook")],  # A6a: semantic label for segmentation
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=True,
            disable_gravity=True,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.3, 0.3, 0.8),
            metallic=0.7,
            roughness=0.3,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.4, 0.18, 0.86),  # Above stem, tilted right
        rot=(0.966, -0.259, 0.0, 0.0),  # +30 degrees around Y-axis
    )


@configclass
class YHookCfg:
    """
    Y-hook (3-part assembly)

    Shape (front view):
        \   /  <- Left/right arms (30-degree tilt)
         \ /
          |    <- Vertical stem
          |

    Cable rests in the V-shaped valley.
    """
    stem: YHookStemCfg = YHookStemCfg()
    left_arm: YHookLeftArmCfg = YHookLeftArmCfg()
    right_arm: YHookRightArmCfg = YHookRightArmCfg()


# =============================================================================
# Table Configuration
# =============================================================================

@configclass
class TableCfg(RigidObjectCfg):
    """Configuration for the workspace table."""

    prim_path: str = "{ENV_REGEX_NS}/Table"

    spawn: sim_utils.CuboidCfg = sim_utils.CuboidCfg(
        size=(0.8, 0.6, 0.02),  # 80cm x 60cm x 2cm thick
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
        pos=(0.4, 0.0, 0.74),  # In front of robot, 75cm height (table center at 74cm with 2cm thickness)
        rot=(1.0, 0.0, 0.0, 0.0),
    )


# =============================================================================
# Camera Configuration
# =============================================================================

@configclass
class OverheadCameraCfg(CameraCfg):
    """Overhead RGB-D camera configuration."""
    
    prim_path: str = "{ENV_REGEX_NS}/OverheadCamera"
    
    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=24.0,
        focus_distance=400.0,
        horizontal_aperture=20.955,
        clipping_range=(0.1, 10.0),
    )
    
    # Camera position: above workspace looking down
    offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
        pos=(0.0, 0.4, 1.5),  # 1.5m above table center
        rot=(0.0, 0.707, 0.0, 0.707),  # Looking down
        convention="world",
    )
    
    # Output configuration
    width: int = 640
    height: int = 480
    data_types: list[str] = ["rgb", "distance_to_image_plane"]
    
    update_period: float = 0.0  # Every frame


@configclass
class WristCameraCfg(CameraCfg):
    """Wrist-mounted camera configuration."""
    
    prim_path: str = MISSING  # Set per-arm
    
    spawn: sim_utils.PinholeCameraCfg = sim_utils.PinholeCameraCfg(
        focal_length=18.0,
        focus_distance=200.0,
        horizontal_aperture=15.0,
        clipping_range=(0.01, 5.0),
    )
    
    # Mounted on end-effector link
    offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
        pos=(0.0, 0.0, 0.05),
        rot=(0.0, 0.0, 0.0, 1.0),
        convention="ros",
    )
    
    width: int = 224
    height: int = 224
    data_types: list[str] = ["rgb", "distance_to_image_plane"]
    
    update_period: float = 0.0


# =============================================================================
# Contact Sensor Configuration
# =============================================================================

@configclass
class GripperContactSensorCfg(ContactSensorCfg):
    """Contact sensor for gripper fingers."""
    
    prim_path: str = MISSING
    
    update_period: float = 0.0  # Every physics step
    
    # Track contacts with cable
    track_air_time: bool = False
    
    # Filter settings
    filter_prim_paths_expr: list[str] = ["{ENV_REGEX_NS}/Cable.*"]


# =============================================================================
# Frame Transformer (for F/T sensing simulation) - Disabled for now
# =============================================================================
# Note: FrameTransformerCfg API changed in Isaac Lab 2.3.0
# TODO: Update when F/T sensing is implemented

# =============================================================================
# Complete Scene Configuration
# =============================================================================

@configclass
class HookHangingSceneCfg(InteractiveSceneCfg):
    """
    Complete scene configuration for the Hook Hanging task.
    
    Includes:
    - Dual Franka Panda robots
    - Table workspace
    - Hook target
    - Cable (deformable object)
    - Cameras (overhead + wrist-mounted)
    - Contact sensors
    """
    
    # Environment settings
    num_envs: int = 256
    env_spacing: float = 2.5

    # Ground plane (Isaac Lab 2.3.0 requires AssetBaseCfg wrapper)
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # Lighting (Isaac Lab 2.3.0 requires AssetBaseCfg wrapper)
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=1000.0, color=(1.0, 1.0, 1.0)),
    )
    
    # Robots - Left arm only for initial testing
    robot: FrankaPandaCfg = FrankaPandaCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
    )
    
    # Table
    table: TableCfg = TableCfg()
    
    # Hook
    hook: SimpleHookCfg = SimpleHookCfg()
    
    # Cable (using segmented rigid body approach)
    cable: CableSegmentedCfg = CableSegmentedCfg()
    
    # Overhead camera
    overhead_camera: OverheadCameraCfg = OverheadCameraCfg()


@configclass
class HookHangingSceneCfgSingleArm(InteractiveSceneCfg):
    """
    Simplified scene with single arm for Phase 1-4 testing.
    """
    
    num_envs: int = 256
    env_spacing: float = 2.0

    # Ground (Isaac Lab 2.3.0 requires AssetBaseCfg wrapper)
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # Lighting (Isaac Lab 2.3.0 requires AssetBaseCfg wrapper)
    light = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DistantLightCfg(intensity=3000.0, color=(1.0, 1.0, 1.0)),
    )
    
    # Single Franka robot
    robot: FrankaPandaCfg = FrankaPandaCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
    )
    
    # Workspace table
    table: TableCfg = TableCfg()
    
    # Hook target
    hook: SimpleHookCfg = SimpleHookCfg()
    
    # Cable object
    cable: CableSegmentedCfg = CableSegmentedCfg()


# =============================================================================
# Helper Functions
# =============================================================================

def create_cable_segments(
    num_segments: int = 10,
    segment_length: float = 0.03,
    segment_radius: float = 0.004,
    start_pos: tuple[float, float, float] = (-0.15, 0.4, 0.77),
) -> list[dict]:
    """
    Create configuration for cable segments.
    
    Returns a list of segment configurations with positions
    calculated to form a straight cable initially.
    """
    segments = []
    
    for i in range(num_segments):
        # Position each segment along X axis
        pos_x = start_pos[0] + i * segment_length
        pos_y = start_pos[1]
        pos_z = start_pos[2]
        
        segments.append({
            "index": i,
            "position": (pos_x, pos_y, pos_z),
            "rotation": (1.0, 0.0, 0.0, 0.0),
            "length": segment_length,
            "radius": segment_radius,
        })
    
    return segments


def get_robot_joint_limits() -> dict:
    """
    Get Franka Panda joint limits.
    
    Returns:
        Dictionary with joint names and their (min, max) limits in radians.
    """
    return {
        "panda_joint1": (-2.8973, 2.8973),
        "panda_joint2": (-1.7628, 1.7628),
        "panda_joint3": (-2.8973, 2.8973),
        "panda_joint4": (-3.0718, -0.0698),
        "panda_joint5": (-2.8973, 2.8973),
        "panda_joint6": (-0.0175, 3.7525),
        "panda_joint7": (-2.8973, 2.8973),
        "panda_finger_joint1": (0.0, 0.04),
        "panda_finger_joint2": (0.0, 0.04),
    }


def get_default_joint_positions() -> dict:
    """
    Get default (home) joint positions for Franka Panda.
    
    This configuration places the arm in a pose suitable
    for reaching the table workspace.
    """
    return {
        "panda_joint1": 0.0,
        "panda_joint2": -0.569,
        "panda_joint3": 0.0,
        "panda_joint4": -2.810,
        "panda_joint5": 0.0,
        "panda_joint6": 3.037,
        "panda_joint7": 0.741,
        "panda_finger_joint1": 0.04,
        "panda_finger_joint2": 0.04,
    }


# =============================================================================
# Print Configuration Summary
# =============================================================================

def print_scene_config(cfg: HookHangingSceneCfg = None):
    """Print scene configuration summary."""
    if cfg is None:
        cfg = HookHangingSceneCfg()
    
    print("=" * 60)
    print("THREAD HOOK HANGING SCENE CONFIGURATION")
    print("=" * 60)
    
    print(f"\n[Environment]")
    print(f"  Num environments: {cfg.num_envs}")
    print(f"  Environment spacing: {cfg.env_spacing}m")
    
    print(f"\n[Robot: Franka Panda]")
    print(f"  Prim path: {cfg.robot.prim_path}")
    print(f"  Joints: 7 arm + 2 gripper = 9 total")
    
    print(f"\n[Table]")
    print(f"  Size: 80 x 60 x 2 cm")
    print(f"  Height: 75 cm")
    
    print(f"\n[Hook]")
    print(f"  Position: (0.0, 0.45, 0.85)m")
    print(f"  Height above table: 10 cm")
    
    print(f"\n[Cable]")
    print(f"  Length: 30 cm (10 segments)")
    print(f"  Diameter: 8 mm")
    print(f"  Initial position: (-0.15, 0.4, 0.77)m")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_scene_config()
    
    # Print cable segments
    print("\n[Cable Segments]")
    segments = create_cable_segments()
    for seg in segments[:3]:
        print(f"  Segment {seg['index']}: pos={seg['position']}")
    print("  ...")
    
    # Print joint limits
    print("\n[Joint Limits]")
    limits = get_robot_joint_limits()
    for joint, (lo, hi) in list(limits.items())[:3]:
        print(f"  {joint}: [{lo:.3f}, {hi:.3f}] rad")
    print("  ...")
