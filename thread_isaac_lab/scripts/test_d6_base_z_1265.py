#!/usr/bin/env python3
"""
D6 Constraint Test with New Base Z = 1.265
==========================================

Tests D6 constraint grasping with:
- New robot base positions (Z = 1.265)
- New Phase 2 joint values from IK optimization
- Correct local_pos0 = (0, 0, 0.1123) for panda_hand to fingertip

Usage:
    DISPLAY=:1 CUDA_VISIBLE_DEVICES=0 env_isaaclab/bin/python \
        thread_isaac_lab/scripts/test_d6_base_z_1265.py --headless

Author: THREAD Research Team
Date: 2025-12-30
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import argparse
import os
from datetime import datetime

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="D6 Constraint Test (Base Z=1.265)")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Isaac Lab imports
import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg
from isaaclab.sensors import CameraCfg

from thread_isaac_lab.utils.d6_grasp_manager import D6GraspManager
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# PIL for image saving
from PIL import Image
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Franka USD (must be after isaaclab imports)
FRANKA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"

# =============================================================================
# NEW PARAMETERS (IK-optimized for Base Z = 1.265)
# =============================================================================

# Robot base positions (NEW)
ROBOT_LEFT_BASE = (0.2467, -0.4200, 1.265)
ROBOT_RIGHT_BASE = (0.2467, 0.2000, 1.265)
ROBOT_BASE_QUAT_WXYZ = (0.7071, 0.0, 0.7071, 0.0)  # Y-axis +90 deg (wall mount)

# Phase 2 (GRASP) joint values (NEW - from IK optimization)
PHASE2_LEFT_JOINTS = [1.5716, 1.1847, -0.8656, -2.3819, -2.2755, 2.1233, -0.1531]
PHASE2_RIGHT_JOINTS = [1.5109, 1.2197, -0.8629, -2.4314, -2.347, 2.0494, -0.051]

# D6 constraint local_pos0 (panda_hand local +Z = fingertip direction)
D6_LOCAL_POS0 = (0.0, 0.0, 0.1123)
D6_LOCAL_POS1 = (0.0, 0.0, 0.0)

# Cable parameters
CABLE_X = 0.35
CABLE_Z = 0.77  # On table
CABLE_SEG17_Y = -0.285  # Left grasp point

# Gripper positions
GRIPPER_OPEN = 0.04
GRIPPER_CLOSED = 0.005

# USD paths
SEGMENTED_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v5.usd"

# Output directory for images
OUTPUT_DIR = "/home/rlrk/Claudecode/terminal1"


# =============================================================================
# Scene Configuration
# =============================================================================

@configclass
class D6TestSceneCfg(InteractiveSceneCfg):
    """Scene configuration for D6 constraint test."""

    num_envs = 1
    env_spacing = 4.0

    # Ground plane
    ground: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    # Light
    light: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(1.0, 1.0, 1.0)),
    )

    # Table
    table: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.CuboidCfg(
            size=(1.2, 0.8, 0.02),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.92, 0.90, 0.84)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.35, 0.0, 0.74)),
    )

    # Left Robot (wall-mounted)
    robot_left: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left",
        spawn=UsdFileCfg(
            usd_path=FRANKA_USD,
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=True,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=12,
                solver_velocity_iteration_count=1,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=ROBOT_LEFT_BASE,
            rot=ROBOT_BASE_QUAT_WXYZ,
            joint_pos={
                "panda_joint1": PHASE2_LEFT_JOINTS[0],
                "panda_joint2": PHASE2_LEFT_JOINTS[1],
                "panda_joint3": PHASE2_LEFT_JOINTS[2],
                "panda_joint4": PHASE2_LEFT_JOINTS[3],
                "panda_joint5": PHASE2_LEFT_JOINTS[4],
                "panda_joint6": PHASE2_LEFT_JOINTS[5],
                "panda_joint7": PHASE2_LEFT_JOINTS[6],
                "panda_finger_joint1": GRIPPER_OPEN,
                "panda_finger_joint2": GRIPPER_OPEN,
            },
            joint_vel={".*": 0.0},
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                effort_limit_sim=87.0,
                stiffness=800.0,
                damping=160.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                effort_limit_sim=12.0,
                stiffness=800.0,
                damping=160.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                effort_limit_sim=200.0,
                stiffness=2000.0,
                damping=100.0,
            ),
        },
    )

    # Right Robot (wall-mounted)
    robot_right: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right",
        spawn=UsdFileCfg(
            usd_path=FRANKA_USD,
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=True,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=12,
                solver_velocity_iteration_count=1,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=ROBOT_RIGHT_BASE,
            rot=ROBOT_BASE_QUAT_WXYZ,
            joint_pos={
                "panda_joint1": PHASE2_RIGHT_JOINTS[0],
                "panda_joint2": PHASE2_RIGHT_JOINTS[1],
                "panda_joint3": PHASE2_RIGHT_JOINTS[2],
                "panda_joint4": PHASE2_RIGHT_JOINTS[3],
                "panda_joint5": PHASE2_RIGHT_JOINTS[4],
                "panda_joint6": PHASE2_RIGHT_JOINTS[5],
                "panda_joint7": PHASE2_RIGHT_JOINTS[6],
                "panda_finger_joint1": GRIPPER_OPEN,
                "panda_finger_joint2": GRIPPER_OPEN,
            },
            joint_vel={".*": 0.0},
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                effort_limit_sim=87.0,
                stiffness=800.0,
                damping=160.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                effort_limit_sim=12.0,
                stiffness=800.0,
                damping=160.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                effort_limit_sim=200.0,
                stiffness=2000.0,
                damping=100.0,
            ),
        },
    )

    # Cable (20-segment articulated)
    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=SEGMENTED_CABLE_USD,
            activate_contact_sensors=False,
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=64,
                solver_velocity_iteration_count=16,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(CABLE_X, CABLE_SEG17_Y, CABLE_Z),
            rot=(0.7071, -0.7071, 0.0, 0.0),  # X-axis -90 deg (extends in Y)
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=1.0,
            ),
        },
    )

    # Overhead camera for monitoring
    overhead_camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/OverheadCamera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=18.0,
            horizontal_aperture=25.0,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.35, 0.0, 1.8),
            rot=(0.7071, 0.0, 0.7071, 0.0),
            convention="world",
        ),
        width=512,
        height=512,
        data_types=["rgb"],
        update_period=0.0,
    )


def save_image(camera_data, filename: str, output_dir: str = OUTPUT_DIR):
    """Save camera image to file."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # Get RGB data
    rgb = camera_data["rgb"][0].cpu().numpy()

    # Convert to PIL Image and save
    if rgb.shape[-1] == 4:  # RGBA
        rgb = rgb[:, :, :3]  # Remove alpha

    img = Image.fromarray(rgb.astype(np.uint8))
    img.save(filepath)
    print(f"  Saved: {filepath}")
    return filepath


def main():
    print("\n" + "=" * 70)
    print("D6 CONSTRAINT TEST - Base Z = 1.265")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Print configuration
    print("\n[CONFIG]")
    print(f"  Robot Left Base:  {ROBOT_LEFT_BASE}")
    print(f"  Robot Right Base: {ROBOT_RIGHT_BASE}")
    print(f"  Phase 2 Left:  {PHASE2_LEFT_JOINTS}")
    print(f"  Phase 2 Right: {PHASE2_RIGHT_JOINTS}")
    print(f"  D6 local_pos0: {D6_LOCAL_POS0}")

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.0, 0.5, 1.5), target=(0.35, 0.0, 0.85))

    # Create scene
    scene_cfg = D6TestSceneCfg()
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Get references
    robot_left: Articulation = scene["robot_left"]
    robot_right: Articulation = scene["robot_right"]
    cable: Articulation = scene["cable"]
    camera = scene["overhead_camera"]

    # Get stage for D6GraspManager
    stage = sim_utils.get_current_stage()

    # Initialize D6GraspManager
    grasp_manager = D6GraspManager()
    grasp_manager.set_stage(stage)

    # Create joint target tensors
    left_joint_target = torch.tensor([
        PHASE2_LEFT_JOINTS + [GRIPPER_OPEN, GRIPPER_OPEN]
    ], device="cuda:0")
    right_joint_target = torch.tensor([
        PHASE2_RIGHT_JOINTS + [GRIPPER_OPEN, GRIPPER_OPEN]
    ], device="cuda:0")

    # ==========================================================================
    # Phase 1: Settle robots at Phase 2 position (open gripper)
    # ==========================================================================
    print("\n[Phase 1] Settling robots at Phase 2 position (200 steps)...")

    for step in range(200):
        robot_left.set_joint_position_target(left_joint_target)
        robot_right.set_joint_position_target(right_joint_target)

        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get positions
    left_hand_pos = robot_left.data.body_pos_w[0, -3].cpu().numpy()  # panda_hand
    right_hand_pos = robot_right.data.body_pos_w[0, -3].cpu().numpy()
    cable_seg17_pos = cable.data.body_pos_w[0, 17].cpu().numpy()
    cable_seg2_pos = cable.data.body_pos_w[0, 2].cpu().numpy()

    print(f"  Left hand pos:  ({left_hand_pos[0]:.4f}, {left_hand_pos[1]:.4f}, {left_hand_pos[2]:.4f})")
    print(f"  Right hand pos: ({right_hand_pos[0]:.4f}, {right_hand_pos[1]:.4f}, {right_hand_pos[2]:.4f})")
    print(f"  Cable seg17 (left):  ({cable_seg17_pos[0]:.4f}, {cable_seg17_pos[1]:.4f}, {cable_seg17_pos[2]:.4f})")
    print(f"  Cable seg2 (right):  ({cable_seg2_pos[0]:.4f}, {cable_seg2_pos[1]:.4f}, {cable_seg2_pos[2]:.4f})")

    # Save initial image
    camera.update(sim.get_physics_dt())
    save_image(camera.data.output, f"d6_test_{timestamp}_phase1_initial.png")

    # ==========================================================================
    # Phase 2: Close grippers
    # ==========================================================================
    print("\n[Phase 2] Closing grippers (100 steps)...")

    left_closed = torch.tensor([
        PHASE2_LEFT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]
    ], device="cuda:0")
    right_closed = torch.tensor([
        PHASE2_RIGHT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]
    ], device="cuda:0")

    for step in range(100):
        robot_left.set_joint_position_target(left_closed)
        robot_right.set_joint_position_target(right_closed)

        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Save after gripper close
    camera.update(sim.get_physics_dt())
    save_image(camera.data.output, f"d6_test_{timestamp}_phase2_closed.png")

    # ==========================================================================
    # Phase 3: Create D6 constraints
    # ==========================================================================
    print("\n[Phase 3] Creating D6 constraints...")

    # Prim paths (panda_hand, not panda_leftfinger)
    left_gripper_path = "/World/envs/env_0/Robot_Left/panda_hand"
    right_gripper_path = "/World/envs/env_0/Robot_Right/panda_hand"
    left_cable_path = "/World/envs/env_0/Cable/seg_17"  # Left end
    right_cable_path = "/World/envs/env_0/Cable/seg_2"   # Right end

    # Check prim existence
    for name, path in [("Left gripper", left_gripper_path),
                       ("Right gripper", right_gripper_path),
                       ("Cable seg17", left_cable_path),
                       ("Cable seg2", right_cable_path)]:
        prim = stage.GetPrimAtPath(path)
        print(f"  {name}: {'FOUND' if prim.IsValid() else 'NOT FOUND'} at {path}")

    # Create D6 constraints
    success_left = grasp_manager.create_grasp(
        "left",
        gripper_prim_path=left_gripper_path,
        cable_prim_path=left_cable_path,
        local_pos0=D6_LOCAL_POS0,
        local_pos1=D6_LOCAL_POS1,
    )
    success_right = grasp_manager.create_grasp(
        "right",
        gripper_prim_path=right_gripper_path,
        cable_prim_path=right_cable_path,
        local_pos0=D6_LOCAL_POS0,
        local_pos1=D6_LOCAL_POS1,
    )

    print(f"  D6 Left:  {'SUCCESS' if success_left else 'FAILED'}")
    print(f"  D6 Right: {'SUCCESS' if success_right else 'FAILED'}")

    # Settle after constraint creation
    for step in range(50):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Save after D6 creation
    camera.update(sim.get_physics_dt())
    save_image(camera.data.output, f"d6_test_{timestamp}_phase3_d6_created.png")

    # Record initial cable Z for lift measurement
    initial_cable_z = cable.data.body_pos_w[0, :, 2].mean().item()
    print(f"  Initial cable mean Z: {initial_cable_z:.4f}")

    # ==========================================================================
    # Phase 4: Lift test (move arms up by 10cm)
    # ==========================================================================
    print("\n[Phase 4] Lifting cable (300 steps)...")

    # Simple lift: increase joint2 angle to lift arm
    # Joint2 controls shoulder pitch - decreasing it lifts the arm
    LIFT_DELTA_J2 = -0.3  # Lift by decreasing joint2

    lift_left = torch.tensor([
        [PHASE2_LEFT_JOINTS[0],
         PHASE2_LEFT_JOINTS[1] + LIFT_DELTA_J2,  # Lift
         PHASE2_LEFT_JOINTS[2],
         PHASE2_LEFT_JOINTS[3],
         PHASE2_LEFT_JOINTS[4],
         PHASE2_LEFT_JOINTS[5],
         PHASE2_LEFT_JOINTS[6],
         GRIPPER_CLOSED, GRIPPER_CLOSED]
    ], device="cuda:0")

    lift_right = torch.tensor([
        [PHASE2_RIGHT_JOINTS[0],
         PHASE2_RIGHT_JOINTS[1] + LIFT_DELTA_J2,  # Lift
         PHASE2_RIGHT_JOINTS[2],
         PHASE2_RIGHT_JOINTS[3],
         PHASE2_RIGHT_JOINTS[4],
         PHASE2_RIGHT_JOINTS[5],
         PHASE2_RIGHT_JOINTS[6],
         GRIPPER_CLOSED, GRIPPER_CLOSED]
    ], device="cuda:0")

    for step in range(300):
        robot_left.set_joint_position_target(lift_left)
        robot_right.set_joint_position_target(lift_right)

        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if step % 100 == 0:
            cable_z = cable.data.body_pos_w[0, :, 2].mean().item()
            lift = cable_z - initial_cable_z
            print(f"  Step {step}: Cable mean Z = {cable_z:.4f} (lift = {lift:.4f}m)")

    # Final measurements
    final_cable_z = cable.data.body_pos_w[0, :, 2].mean().item()
    total_lift = final_cable_z - initial_cable_z

    # Save after lift
    camera.update(sim.get_physics_dt())
    save_image(camera.data.output, f"d6_test_{timestamp}_phase4_lifted.png")

    # ==========================================================================
    # Phase 5: Release and drop test
    # ==========================================================================
    print("\n[Phase 5] Releasing D6 constraints...")

    grasp_manager.release_grasp("left")
    grasp_manager.release_grasp("right")

    print(f"  Grasp state: left={grasp_manager.left_grasping}, right={grasp_manager.right_grasping}")

    # Let cable fall
    print("  Letting cable fall (200 steps)...")
    for step in range(200):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    dropped_cable_z = cable.data.body_pos_w[0, :, 2].mean().item()
    drop_distance = final_cable_z - dropped_cable_z

    # Save after release
    camera.update(sim.get_physics_dt())
    save_image(camera.data.output, f"d6_test_{timestamp}_phase5_released.png")

    # ==========================================================================
    # Results
    # ==========================================================================
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"  Initial cable Z: {initial_cable_z:.4f} m")
    print(f"  Lifted cable Z:  {final_cable_z:.4f} m")
    print(f"  Total lift:      {total_lift:.4f} m ({total_lift*100:.1f} cm)")
    print(f"  Dropped cable Z: {dropped_cable_z:.4f} m")
    print(f"  Drop distance:   {drop_distance:.4f} m ({drop_distance*100:.1f} cm)")

    # Success criteria
    lift_success = total_lift > 0.03  # Lifted at least 3cm
    drop_success = drop_distance > 0.02  # Dropped at least 2cm after release

    print(f"\n[VERDICT]")
    print(f"  Lift test:    {'PASS' if lift_success else 'FAIL'} (lifted {total_lift*100:.1f}cm, need >3cm)")
    print(f"  Release test: {'PASS' if drop_success else 'FAIL'} (dropped {drop_distance*100:.1f}cm, need >2cm)")

    if lift_success and drop_success:
        print(f"\n  [OK] D6 CONSTRAINT TEST PASSED!")
    else:
        print(f"\n  [WARN] D6 constraint test may have issues")

    print("=" * 70)
    print(f"\nImages saved to: {OUTPUT_DIR}")
    print(f"  - d6_test_{timestamp}_phase1_initial.png")
    print(f"  - d6_test_{timestamp}_phase2_closed.png")
    print(f"  - d6_test_{timestamp}_phase3_d6_created.png")
    print(f"  - d6_test_{timestamp}_phase4_lifted.png")
    print(f"  - d6_test_{timestamp}_phase5_released.png")

    # Keep running for visual inspection if not headless
    if not args_cli.headless:
        print("\nSimulation running. Press Ctrl+C to exit.")
        try:
            while simulation_app.is_running():
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())
        except KeyboardInterrupt:
            pass

    simulation_app.close()


if __name__ == "__main__":
    main()
