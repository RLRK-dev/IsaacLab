#!/usr/bin/env python3
"""
Simple Height Check - No Cameras
================================

Usage:
    CUDA_VISIBLE_DEVICES=1 python thread_isaac_lab/scripts/check_heights_simple.py --headless
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Check Heights")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR
from thread_isaac_lab.configs.task_config import PHYSICS_DT


# Constants from dual_arm_cfg.py
TABLE_HEIGHT = 0.75
ARM_Z_POS = 0.75
ARM_Y_OFFSET = 0.30
ARM_X_POS = 0.0

FRANKA_PANDA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"
CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v2.usd"


@configclass
class SimpleSceneCfg(InteractiveSceneCfg):
    """Simple scene without cameras."""

    num_envs = 1
    env_spacing = 3.0

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    light = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(intensity=1500.0),
    )

    # Left robot
    robot_left: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left",
        spawn=sim_utils.UsdFileCfg(
            usd_path=FRANKA_PANDA_USD,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(ARM_X_POS, -ARM_Y_OFFSET, ARM_Z_POS),
            rot=(1.0, 0.0, 0.0, 0.0),
            joint_pos={
                "panda_joint1": 0.3,
                "panda_joint2": -0.8,
                "panda_joint3": 0.0,
                "panda_joint4": -2.2,
                "panda_joint5": 0.0,
                "panda_joint6": 2.0,
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
                stiffness=2000.0,
                damping=100.0,
            ),
        },
    )

    # Cable
    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=CABLE_USD,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.30, -0.15, TABLE_HEIGHT + 0.02),
            rot=(0.7071, -0.7071, 0.0, 0.0),
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=0.1,
            ),
        },
    )

    # Table
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.CuboidCfg(
            size=(1.0, 0.8, 0.02),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.7, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.4, 0.0, TABLE_HEIGHT - 0.01),
        ),
    )


def main():
    print("\n" + "=" * 70)
    print("HEIGHT CHECK (SIMPLE)")
    print("=" * 70)

    print("\n[Configuration]")
    print(f"  TABLE_HEIGHT = {TABLE_HEIGHT:.3f} m")
    print(f"  ARM_Z_POS = {ARM_Z_POS:.3f} m")
    print(f"  Cable initial Z = {TABLE_HEIGHT + 0.02:.3f} m")

    # Setup
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)

    scene_cfg = SimpleSceneCfg()
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    print("\n[Settling 300 steps...]")
    for _ in range(300):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    print("\n[Actual Positions]")

    # Cable
    cable: Articulation = scene["cable"]
    cable_pos = cable.data.body_pos_w[0]
    cable_z = cable_pos[:, 2].cpu().numpy()
    print(f"\n  Cable Z values: min={cable_z.min():.4f}, max={cable_z.max():.4f}, mean={cable_z.mean():.4f}")

    cable_xy = cable_pos[:, :2].cpu().numpy()
    print(f"  Cable seg_0: ({cable_pos[0, 0].item():.3f}, {cable_pos[0, 1].item():.3f}, {cable_pos[0, 2].item():.3f})")
    print(f"  Cable seg_9: ({cable_pos[-1, 0].item():.3f}, {cable_pos[-1, 1].item():.3f}, {cable_pos[-1, 2].item():.3f})")

    # Robot
    robot: Articulation = scene["robot_left"]
    body_names = robot.data.body_names
    print(f"\n  Robot bodies: {list(body_names)}")

    # Find indices
    hand_idx = None
    finger_idx = None
    for i, name in enumerate(body_names):
        if name == "panda_hand":
            hand_idx = i
        if name == "panda_leftfinger":
            finger_idx = i

    robot_pos = robot.data.body_pos_w[0]

    if hand_idx is not None:
        hand_pos = robot_pos[hand_idx].cpu().numpy()
        print(f"\n  panda_hand: ({hand_pos[0]:.4f}, {hand_pos[1]:.4f}, {hand_pos[2]:.4f})")

    if finger_idx is not None:
        finger_pos = robot_pos[finger_idx].cpu().numpy()
        print(f"  panda_leftfinger: ({finger_pos[0]:.4f}, {finger_pos[1]:.4f}, {finger_pos[2]:.4f})")

    # Analysis
    print("\n" + "-" * 70)
    print("ANALYSIS")
    print("-" * 70)

    if finger_idx is not None:
        gripper_z = finger_pos[2]
        cable_mean_z = cable_z.mean()
        z_diff = gripper_z - cable_mean_z

        print(f"  Gripper Z: {gripper_z:.4f} m")
        print(f"  Cable mean Z: {cable_mean_z:.4f} m")
        print(f"  Z difference: {z_diff:.4f} m ({z_diff*100:.1f} cm)")

        if z_diff > 0.05:
            print(f"\n  [ISSUE] Gripper is {z_diff*100:.1f}cm ABOVE cable")
            print("  [FIX] Options:")
            print(f"    1. Lower robot: ARM_Z_POS = {ARM_Z_POS - z_diff:.3f}")
            print(f"    2. Raise cable: cable_z = {TABLE_HEIGHT + 0.02 + z_diff:.3f}")
            print(f"    3. Change initial joint angles to reach down")
        elif z_diff < -0.05:
            print(f"\n  [ISSUE] Gripper is {-z_diff*100:.1f}cm BELOW cable")
        else:
            print(f"\n  [OK] Heights are within 5cm")

        # XY analysis
        gripper_xy = finger_pos[:2]
        cable_center_xy = cable_xy.mean(axis=0)
        xy_dist = ((gripper_xy - cable_center_xy) ** 2).sum() ** 0.5
        print(f"\n  Gripper XY: ({gripper_xy[0]:.3f}, {gripper_xy[1]:.3f})")
        print(f"  Cable center XY: ({cable_center_xy[0]:.3f}, {cable_center_xy[1]:.3f})")
        print(f"  XY distance: {xy_dist:.3f} m")

    print("=" * 70)
    simulation_app.close()


if __name__ == "__main__":
    main()
