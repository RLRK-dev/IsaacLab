#!/usr/bin/env python3
"""
Flexible Cable Configuration using Segmented Rigid Bodies
=========================================================

Implements a flexible cable as a chain of rigid body segments
connected by spherical joints. This provides realistic cable
behavior while maintaining simulation stability.

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import math
import torch
import numpy as np

import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObjectCfg, ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.utils import configclass

from thread_isaac_lab.configs.task_config import (
    CABLE_SEGMENT_COUNT,
    CABLE_SEGMENT_LENGTH as TASK_CABLE_SEGMENT_LENGTH,
    CABLE_TOTAL_LENGTH as TASK_CABLE_TOTAL_LENGTH,
    CABLE_RADIUS,
)


# =============================================================================
# Cable Parameters (imported from task_config.py for consistency)
# =============================================================================

CABLE_NUM_SEGMENTS = CABLE_SEGMENT_COUNT  # From task_config.py
CABLE_TOTAL_LENGTH = TASK_CABLE_TOTAL_LENGTH  # From task_config.py
# CABLE_RADIUS is imported directly from task_config.py
CABLE_SEGMENT_LENGTH = TASK_CABLE_SEGMENT_LENGTH  # From task_config.py
CABLE_SEGMENT_MASS = 0.006     # Mass per segment (60g total)


# =============================================================================
# Flexible Cable as Articulation (Chain of Segments)
# =============================================================================

@configclass
class FlexibleCableCfg(ArticulationCfg):
    """
    Flexible cable configuration using articulated rigid body chain.

    The cable is modeled as a chain of cylindrical segments connected
    by spherical joints (3-DOF rotation at each connection point).

    Physical properties:
    - Total length: 30cm
    - Diameter: 12mm
    - 10 segments with spherical joints
    - Total mass: ~30g
    """

    prim_path: str = "{ENV_REGEX_NS}/FlexibleCable"

    spawn: sim_utils.UsdFileCfg = sim_utils.UsdFileCfg(
        usd_path="",  # Will be generated procedurally
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=1.0,
            linear_damping=0.5,
            angular_damping=0.5,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=1,
        ),
    )

    init_state: ArticulationCfg.InitialStateCfg = ArticulationCfg.InitialStateCfg(
        pos=(0.45, 0.0, 0.80),  # Above table
        rot=(1.0, 0.0, 0.0, 0.0),
        joint_pos={".*": 0.0},  # All joints at neutral
        joint_vel={".*": 0.0},
    )

    # Soft joints for flexibility
    actuators: dict = {
        "cable_joints": ImplicitActuatorCfg(
            joint_names_expr=["joint_.*"],
            effort_limit_sim=0.1,   # Low effort - passive cable
            stiffness=0.5,          # Low stiffness for flexibility
            damping=0.1,            # Some damping for stability
        ),
    }


# =============================================================================
# Simple Flexible Cable (Single Soft Body Approximation)
# =============================================================================

@configclass
class SimpleCableSegmentsCfg:
    """
    Configuration for creating multiple cable segments.

    Each segment is a separate rigid body. They will be
    spawned and connected via code in the environment.
    """

    num_segments: int = CABLE_NUM_SEGMENTS
    segment_length: float = CABLE_SEGMENT_LENGTH
    segment_radius: float = CABLE_RADIUS
    segment_mass: float = CABLE_SEGMENT_MASS

    # Visual properties
    color: tuple = (0.9, 0.4, 0.1)  # Orange

    # Physics properties
    linear_damping: float = 0.5
    angular_damping: float = 0.5

    # Joint properties (for connections)
    joint_stiffness: float = 1.0    # Low stiffness
    joint_damping: float = 0.2      # Some damping


def create_cable_segment_cfg(
    segment_index: int,
    base_prim_path: str = "{ENV_REGEX_NS}/Cable",
) -> RigidObjectCfg:
    """
    Create configuration for a single cable segment.

    Args:
        segment_index: Index of the segment (0 to num_segments-1)
        base_prim_path: Base prim path for the cable

    Returns:
        RigidObjectCfg for this segment
    """

    return RigidObjectCfg(
        prim_path=f"{base_prim_path}/Segment_{segment_index:02d}",
        spawn=sim_utils.CylinderCfg(
            radius=CABLE_RADIUS,
            height=CABLE_SEGMENT_LENGTH,
            axis="X",  # Cable extends along X axis
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=1.0,
                linear_damping=0.5,
                angular_damping=0.5,
            ),
            mass_props=sim_utils.MassPropertiesCfg(
                mass=CABLE_SEGMENT_MASS,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.9, 0.4, 0.1),  # Orange
                metallic=0.0,
                roughness=0.8,
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            # Position each segment in a line
            pos=(
                0.45 + segment_index * CABLE_SEGMENT_LENGTH,
                0.0,
                0.80
            ),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )


# =============================================================================
# Capsule-based Cable (Better for Grasping)
# =============================================================================

@configclass
class CapsuleCableCfg(RigidObjectCfg):
    """
    Cable represented as a single capsule for simpler physics.

    This is a compromise between a rigid cylinder and full
    deformable simulation - the capsule shape works better
    for grasping interactions.
    """

    prim_path: str = "{ENV_REGEX_NS}/Cable"

    spawn: sim_utils.CapsuleCfg = sim_utils.CapsuleCfg(
        radius=CABLE_RADIUS,
        height=CABLE_TOTAL_LENGTH - 2 * CABLE_RADIUS,  # Total length minus end caps
        axis="X",
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=1.0,
            linear_damping=0.3,
            angular_damping=0.3,
        ),
        mass_props=sim_utils.MassPropertiesCfg(
            mass=0.03,  # 30g total
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            collision_enabled=True,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.9, 0.4, 0.1),  # Orange
            metallic=0.0,
            roughness=0.8,
        ),
    )

    init_state: RigidObjectCfg.InitialStateCfg = RigidObjectCfg.InitialStateCfg(
        pos=(0.45, 0.0, 0.80),  # Above table
        rot=(1.0, 0.0, 0.0, 0.0),
    )


# =============================================================================
# Helper Functions
# =============================================================================

def compute_cable_positions(
    center_pos: tuple,
    num_segments: int = CABLE_NUM_SEGMENTS,
    segment_length: float = CABLE_SEGMENT_LENGTH,
    orientation: str = "horizontal",
) -> list:
    """
    Compute positions for all cable segments.

    Args:
        center_pos: Center position (x, y, z)
        num_segments: Number of segments
        segment_length: Length of each segment
        orientation: "horizontal" (along X) or "vertical" (along Z)

    Returns:
        List of (x, y, z) positions for each segment
    """
    positions = []

    # Compute offset from center
    total_length = num_segments * segment_length
    start_offset = -total_length / 2 + segment_length / 2

    for i in range(num_segments):
        if orientation == "horizontal":
            pos = (
                center_pos[0] + start_offset + i * segment_length,
                center_pos[1],
                center_pos[2],
            )
        else:  # vertical
            pos = (
                center_pos[0],
                center_pos[1],
                center_pos[2] + start_offset + i * segment_length,
            )
        positions.append(pos)

    return positions


def get_cable_grasp_points(
    cable_pos: torch.Tensor,
    cable_rot: torch.Tensor,
    num_segments: int = CABLE_NUM_SEGMENTS,
) -> torch.Tensor:
    """
    Get optimal grasp points on the cable.

    For a bimanual grasp, returns positions at 1/3 and 2/3
    along the cable length.

    Args:
        cable_pos: Cable center position [batch, 3]
        cable_rot: Cable rotation quaternion [batch, 4]
        num_segments: Number of cable segments

    Returns:
        Grasp points [batch, 2, 3] for left and right grippers
    """
    batch_size = cable_pos.shape[0]
    device = cable_pos.device

    # Grasp points at 1/3 and 2/3 along cable
    offset_1 = CABLE_TOTAL_LENGTH / 3
    offset_2 = -CABLE_TOTAL_LENGTH / 3

    # Simple horizontal cable assumption
    # TODO: Apply rotation for arbitrary orientations
    left_grasp = cable_pos.clone()
    left_grasp[:, 0] += offset_1

    right_grasp = cable_pos.clone()
    right_grasp[:, 0] += offset_2

    return torch.stack([left_grasp, right_grasp], dim=1)


# =============================================================================
# Print Configuration Summary
# =============================================================================

def print_cable_config():
    """Print cable configuration summary."""
    print("=" * 60)
    print("FLEXIBLE CABLE CONFIGURATION")
    print("=" * 60)
    print(f"\n[Physical Properties]")
    print(f"  Total length: {CABLE_TOTAL_LENGTH * 100:.1f} cm")
    print(f"  Diameter: {CABLE_RADIUS * 2 * 1000:.1f} mm")
    print(f"  Number of segments: {CABLE_NUM_SEGMENTS}")
    print(f"  Segment length: {CABLE_SEGMENT_LENGTH * 100:.1f} cm")
    print(f"  Total mass: {CABLE_SEGMENT_MASS * CABLE_NUM_SEGMENTS * 1000:.1f} g")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_cable_config()
