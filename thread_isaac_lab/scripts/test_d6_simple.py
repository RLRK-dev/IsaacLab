#!/usr/bin/env python3
"""
D6 Constraint Simple Test (No Camera)
======================================

Quick test for D6 constraint grasping without camera overhead.

Usage:
    CUDA_VISIBLE_DEVICES=0 env_isaaclab/bin/python \
        thread_isaac_lab/scripts/test_d6_simple.py --headless

Author: THREAD Research Team
Date: 2025-12-30
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="D6 Constraint Simple Test")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Isaac Lab imports
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

from thread_isaac_lab.utils.d6_grasp_manager import D6GraspManager
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# USD paths
FRANKA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"
CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v5.usd"

# =============================================================================
# NEW PARAMETERS
# =============================================================================
ROBOT_LEFT_BASE = (0.2467, -0.4200, 1.265)
ROBOT_RIGHT_BASE = (0.2467, 0.2000, 1.265)
ROBOT_BASE_QUAT = (0.7071, 0.0, 0.7071, 0.0)

PHASE2_LEFT_JOINTS = [1.5716, 1.1847, -0.8656, -2.3819, -2.2755, 2.1233, -0.1531]
PHASE2_RIGHT_JOINTS = [1.5109, 1.2197, -0.8629, -2.4314, -2.347, 2.0494, -0.051]

D6_LOCAL_POS0 = (0.0, 0.0, 0.1123)  # panda_hand local +Z = fingertip

GRIPPER_OPEN = 0.04
GRIPPER_CLOSED = 0.005


@configclass
class SimpleSceneCfg(InteractiveSceneCfg):
    """Minimal scene for D6 test."""
    num_envs = 1
    env_spacing = 4.0

    ground: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    light: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0),
    )

    table: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.CuboidCfg(
            size=(1.2, 0.8, 0.02),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.9, 0.9, 0.8)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.35, 0.0, 0.74)),
    )

    robot_left: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left",
        spawn=UsdFileCfg(
            usd_path=FRANKA_USD,
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=12,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=ROBOT_LEFT_BASE,
            rot=ROBOT_BASE_QUAT,
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
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                stiffness=800.0, damping=160.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                stiffness=800.0, damping=160.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                stiffness=2000.0, damping=100.0,
            ),
        },
    )

    robot_right: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right",
        spawn=UsdFileCfg(
            usd_path=FRANKA_USD,
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=12,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=ROBOT_RIGHT_BASE,
            rot=ROBOT_BASE_QUAT,
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
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                stiffness=800.0, damping=160.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                stiffness=800.0, damping=160.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                stiffness=2000.0, damping=100.0,
            ),
        },
    )

    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=CABLE_USD,
            activate_contact_sensors=False,
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=64,
                solver_velocity_iteration_count=16,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.35, -0.285, 0.77),  # seg_17 at left
            rot=(0.7071, -0.7071, 0.0, 0.0),  # Y-axis layout
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0, damping=1.0,
            ),
        },
    )


def main():
    import sys
    sys.stdout.flush()

    print("\n" + "=" * 60, flush=True)
    print("D6 CONSTRAINT SIMPLE TEST - Base Z = 1.265", flush=True)
    print("=" * 60, flush=True)

    print("\n[CONFIG]", flush=True)
    print(f"  Left Base:  {ROBOT_LEFT_BASE}", flush=True)
    print(f"  Right Base: {ROBOT_RIGHT_BASE}", flush=True)
    print(f"  D6 local_pos0: {D6_LOCAL_POS0}", flush=True)

    # Setup
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.0, 0.5, 1.5), target=(0.35, 0.0, 0.85))

    scene_cfg = SimpleSceneCfg()
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    robot_left: Articulation = scene["robot_left"]
    robot_right: Articulation = scene["robot_right"]
    cable: Articulation = scene["cable"]

    stage = sim_utils.get_current_stage()
    grasp_manager = D6GraspManager()
    grasp_manager.set_stage(stage)

    # Joint targets
    left_open = torch.tensor([PHASE2_LEFT_JOINTS + [GRIPPER_OPEN, GRIPPER_OPEN]], device="cuda:0")
    right_open = torch.tensor([PHASE2_RIGHT_JOINTS + [GRIPPER_OPEN, GRIPPER_OPEN]], device="cuda:0")
    left_closed = torch.tensor([PHASE2_LEFT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]], device="cuda:0")
    right_closed = torch.tensor([PHASE2_RIGHT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]], device="cuda:0")

    # ==========================================================================
    # Phase 1: Settle
    # ==========================================================================
    print("\n[Phase 1] Settling (100 steps)...")
    for _ in range(100):
        robot_left.set_joint_position_target(left_open)
        robot_right.set_joint_position_target(right_open)
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Print positions
    left_hand = robot_left.data.body_pos_w[0, -3].cpu().numpy()
    right_hand = robot_right.data.body_pos_w[0, -3].cpu().numpy()
    seg17 = cable.data.body_pos_w[0, 17].cpu().numpy()
    seg2 = cable.data.body_pos_w[0, 2].cpu().numpy()

    print(f"  Left hand:  ({left_hand[0]:.4f}, {left_hand[1]:.4f}, {left_hand[2]:.4f})")
    print(f"  Right hand: ({right_hand[0]:.4f}, {right_hand[1]:.4f}, {right_hand[2]:.4f})")
    print(f"  Seg17 (L):  ({seg17[0]:.4f}, {seg17[1]:.4f}, {seg17[2]:.4f})")
    print(f"  Seg2 (R):   ({seg2[0]:.4f}, {seg2[1]:.4f}, {seg2[2]:.4f})")

    # ==========================================================================
    # Phase 2: Close grippers
    # ==========================================================================
    print("\n[Phase 2] Closing grippers (50 steps)...")
    for _ in range(50):
        robot_left.set_joint_position_target(left_closed)
        robot_right.set_joint_position_target(right_closed)
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # ==========================================================================
    # Phase 3: Create D6 constraints
    # ==========================================================================
    print("\n[Phase 3] Creating D6 constraints...")

    left_grip = "/World/envs/env_0/Robot_Left/panda_hand"
    right_grip = "/World/envs/env_0/Robot_Right/panda_hand"
    left_seg = "/World/envs/env_0/Cable/seg_17"
    right_seg = "/World/envs/env_0/Cable/seg_2"

    ok_l = grasp_manager.create_grasp("left", left_grip, left_seg, D6_LOCAL_POS0, (0,0,0))
    ok_r = grasp_manager.create_grasp("right", right_grip, right_seg, D6_LOCAL_POS0, (0,0,0))

    print(f"  Left D6:  {'OK' if ok_l else 'FAIL'}")
    print(f"  Right D6: {'OK' if ok_r else 'FAIL'}")

    # Settle after D6
    for _ in range(30):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    init_z = cable.data.body_pos_w[0, :, 2].mean().item()
    print(f"  Initial cable Z: {init_z:.4f}")

    # ==========================================================================
    # Phase 4: Lift
    # ==========================================================================
    print("\n[Phase 4] Lifting (150 steps)...")

    LIFT_J2 = -0.3
    lift_left = torch.tensor([[
        PHASE2_LEFT_JOINTS[0],
        PHASE2_LEFT_JOINTS[1] + LIFT_J2,
        PHASE2_LEFT_JOINTS[2],
        PHASE2_LEFT_JOINTS[3],
        PHASE2_LEFT_JOINTS[4],
        PHASE2_LEFT_JOINTS[5],
        PHASE2_LEFT_JOINTS[6],
        GRIPPER_CLOSED, GRIPPER_CLOSED
    ]], device="cuda:0")

    lift_right = torch.tensor([[
        PHASE2_RIGHT_JOINTS[0],
        PHASE2_RIGHT_JOINTS[1] + LIFT_J2,
        PHASE2_RIGHT_JOINTS[2],
        PHASE2_RIGHT_JOINTS[3],
        PHASE2_RIGHT_JOINTS[4],
        PHASE2_RIGHT_JOINTS[5],
        PHASE2_RIGHT_JOINTS[6],
        GRIPPER_CLOSED, GRIPPER_CLOSED
    ]], device="cuda:0")

    for step in range(150):
        robot_left.set_joint_position_target(lift_left)
        robot_right.set_joint_position_target(lift_right)
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if step % 50 == 0:
            z = cable.data.body_pos_w[0, :, 2].mean().item()
            print(f"  Step {step}: Z={z:.4f}, lift={z-init_z:.4f}")

    final_z = cable.data.body_pos_w[0, :, 2].mean().item()
    lift = final_z - init_z

    # ==========================================================================
    # Phase 5: Release
    # ==========================================================================
    print("\n[Phase 5] Releasing...")
    grasp_manager.release_all()

    for _ in range(100):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    drop_z = cable.data.body_pos_w[0, :, 2].mean().item()
    drop = final_z - drop_z

    # ==========================================================================
    # Results
    # ==========================================================================
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Initial Z:   {init_z:.4f}")
    print(f"  After lift:  {final_z:.4f} (lift = {lift:.4f}m = {lift*100:.1f}cm)")
    print(f"  After drop:  {drop_z:.4f} (drop = {drop:.4f}m = {drop*100:.1f}cm)")

    lift_ok = lift > 0.03
    drop_ok = drop > 0.02

    print(f"\n  Lift:    {'PASS' if lift_ok else 'FAIL'} (need >3cm)")
    print(f"  Release: {'PASS' if drop_ok else 'FAIL'} (need >2cm)")

    if lift_ok and drop_ok:
        print("\n  [SUCCESS] D6 CONSTRAINT WORKS!")
    else:
        print("\n  [WARN] D6 constraint test had issues")

    print("=" * 60)

    simulation_app.close()


if __name__ == "__main__":
    main()
