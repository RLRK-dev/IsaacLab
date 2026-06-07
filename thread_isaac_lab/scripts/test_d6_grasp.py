#!/usr/bin/env python3
"""
D6 Joint Grasp Test Script
==========================

Tests the D6GraspManager for constraint-based grasping between
gripper fingers and cable segments.

Usage:
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/test_d6_grasp.py --headless

Author: THREAD Research Team
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test D6 Joint Grasping")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Now import Isaac Lab modules
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg

from thread_isaac_lab.utils.d6_grasp_manager import D6GraspManager, get_grasp_prim_paths
from thread_isaac_lab.configs.task_config import PHYSICS_DT


# USD paths
FRANKA_USD = "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.0/Isaac/Robots/Franka/franka_instanceable.usd"
SPHERICAL_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable.usd"


@configclass
class D6GraspTestSceneCfg(InteractiveSceneCfg):
    """Scene configuration for D6 grasp test."""

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
            size=(0.8, 0.6, 0.02),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.7, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.4, 0.0, 0.74)),
    )

    # Robot (Franka Panda)
    robot: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
        spawn=UsdFileCfg(
            usd_path=FRANKA_USD,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.75),
            joint_pos={
                "panda_joint1": 0.0,
                "panda_joint2": -0.785,
                "panda_joint3": 0.0,
                "panda_joint4": -2.356,
                "panda_joint5": 0.0,
                "panda_joint6": 1.571,
                "panda_joint7": 0.785,
                "panda_finger_joint1": 0.04,
                "panda_finger_joint2": 0.04,
            },
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                stiffness=400.0,
                damping=80.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                stiffness=400.0,
                damping=80.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                stiffness=400.0,
                damping=40.0,
            ),
        },
    )

    # Cable (SphericalJoint)
    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=SPHERICAL_CABLE_USD,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.4, 0.0, 0.90),  # Above table
            rot=(0.7071, 0.0, 0.7071, 0.0),  # Horizontal
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=0.1,
            ),
        },
    )


def main():
    print("\n" + "=" * 60)
    print("D6 JOINT GRASP TEST")
    print("=" * 60)

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.2, 0.8, 1.2), target=(0.4, 0.0, 0.85))

    # Create scene
    scene_cfg = D6GraspTestSceneCfg()
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Get stage for D6GraspManager
    stage = sim_utils.get_current_stage()

    # Initialize D6GraspManager
    grasp_manager = D6GraspManager()
    grasp_manager.set_stage(stage)

    # Get robot and cable references
    robot: Articulation = scene["robot"]
    cable: Articulation = scene["cable"]

    print("\n[Phase 1] Let cable settle (200 steps)...")
    for step in range(200):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get cable segment 0 position
    cable_pos = cable.data.body_pos_w[0]
    seg0_pos = cable_pos[0].cpu().numpy()
    print(f"  Cable seg_0 position: {seg0_pos}")

    # Get gripper position (panda_leftfinger)
    ee_pos = robot.data.body_pos_w[0, -2].cpu().numpy()  # leftfinger
    print(f"  Gripper position: {ee_pos}")

    print("\n[Phase 2] Move gripper to cable (manual joint control)...")
    # Set target joint positions to reach cable
    # This is a simplified approach - in practice you'd use IK
    target_joints = torch.tensor([
        [0.0, 0.3, 0.0, -1.8, 0.0, 2.0, 0.785, 0.04, 0.04]
    ], device="cuda:0")

    for step in range(300):
        # Simple P control to reach target
        current_pos = robot.data.joint_pos
        error = target_joints - current_pos
        robot.set_joint_position_target(current_pos + 0.01 * error)

        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if step % 100 == 0:
            ee_pos = robot.data.body_pos_w[0, -2].cpu().numpy()
            print(f"  Step {step}: Gripper at {ee_pos}")

    print("\n[Phase 3] Close gripper...")
    # Close gripper (finger joints)
    for step in range(100):
        current_pos = robot.data.joint_pos.clone()
        current_pos[0, 7:9] = 0.005  # Close fingers
        robot.set_joint_position_target(current_pos)

        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    print("\n[Phase 4] Create D6 Joint grasp...")
    # Get actual prim paths
    gripper_path = "/World/envs/env_0/Robot/panda_leftfinger"
    cable_path = "/World/envs/env_0/Cable/seg_0"

    # Check if prims exist
    gripper_prim = stage.GetPrimAtPath(gripper_path)
    cable_prim = stage.GetPrimAtPath(cable_path)
    print(f"  Gripper prim exists: {gripper_prim.IsValid()}")
    print(f"  Cable prim exists: {cable_prim.IsValid()}")

    if gripper_prim.IsValid() and cable_prim.IsValid():
        success = grasp_manager.create_grasp(
            "left",
            gripper_prim_path=gripper_path,
            cable_prim_path=cable_path,
            local_pos0=(0.0, 0.0, 0.02),  # Offset from finger
            local_pos1=(0.0, 0.0, 0.0),
        )
        print(f"  D6 Joint creation: {'SUCCESS' if success else 'FAILED'}")
    else:
        print("  WARNING: Prim paths not found, skipping D6 joint creation")
        # Try to find actual paths
        print("\n  Looking for actual prim paths...")
        def find_prims(prim, depth=0):
            if depth > 3:
                return
            for child in prim.GetChildren():
                print(f"  {'  ' * depth}{child.GetPath()}")
                find_prims(child, depth + 1)

        env_prim = stage.GetPrimAtPath("/World/envs/env_0")
        if env_prim.IsValid():
            find_prims(env_prim)

    print(f"\n  Grasp state: left={grasp_manager.left_grasping}, right={grasp_manager.right_grasping}")

    print("\n[Phase 5] Lift with D6 joint (300 steps)...")
    # Lift target
    lift_target = torch.tensor([
        [0.0, 0.0, 0.0, -1.5, 0.0, 1.5, 0.785, 0.005, 0.005]
    ], device="cuda:0")

    initial_cable_z = cable.data.body_pos_w[0, 0, 2].item()

    for step in range(300):
        current_pos = robot.data.joint_pos
        error = lift_target - current_pos
        robot.set_joint_position_target(current_pos + 0.01 * error)

        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if step % 100 == 0:
            cable_z = cable.data.body_pos_w[0, 0, 2].item()
            ee_z = robot.data.body_pos_w[0, -2, 2].item()
            lift_delta = cable_z - initial_cable_z
            print(f"  Step {step}: Cable seg_0 z={cable_z:.3f} (lift={lift_delta:.3f}), EE z={ee_z:.3f}")

    final_cable_z = cable.data.body_pos_w[0, 0, 2].item()
    lift_amount = final_cable_z - initial_cable_z

    print(f"\n[Phase 6] Release grasp...")
    grasp_manager.release_grasp("left")
    print(f"  Grasp released. State: left={grasp_manager.left_grasping}")

    print("\n[Phase 7] Let cable fall (200 steps)...")
    for step in range(200):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    final_z_after_release = cable.data.body_pos_w[0, 0, 2].item()

    print("\n" + "-" * 60)
    print("RESULTS:")
    print("-" * 60)
    print(f"  Initial cable z: {initial_cable_z:.3f} m")
    print(f"  Cable z after lift: {final_cable_z:.3f} m")
    print(f"  Lift amount: {lift_amount:.3f} m")
    print(f"  Cable z after release: {final_z_after_release:.3f} m")

    if lift_amount > 0.05:
        print(f"\n  [OK] D6 Joint grasp WORKED (lift > 5cm)")
    else:
        print(f"\n  [WARN] D6 Joint grasp may not have worked (lift < 5cm)")

    print("=" * 60)

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
