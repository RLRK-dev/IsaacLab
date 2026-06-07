#!/usr/bin/env python3
"""Test D6 grasp using panda_hand with fingertip offset."""
# /home/rlrk/Claudecode/terminal2/test_d6_panda_hand.py

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab")

from isaaclab.app import AppLauncher
import argparse

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.utils.d6_grasp_manager import D6GraspManager
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    GRIPPER_INIT, GRIPPER_CLOSED,
)

def main():
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    grasp_manager = D6GraspManager()

    sim.reset()
    scene.reset()
    grasp_manager.set_stage(sim.stage)

    # Phase 1: Initialize
    print("\n[Phase 1] Initializing...")
    left_joints = torch.tensor([LEFT_ARM_INIT_JOINTS + [GRIPPER_INIT, GRIPPER_INIT]],
                               dtype=torch.float32, device=sim.device)
    right_joints = torch.tensor([RIGHT_ARM_INIT_JOINTS + [GRIPPER_INIT, GRIPPER_INIT]],
                                dtype=torch.float32, device=sim.device)

    robot_left.write_joint_state_to_sim(left_joints, torch.zeros_like(left_joints))
    robot_right.write_joint_state_to_sim(right_joints, torch.zeros_like(right_joints))
    robot_left.set_joint_position_target(left_joints)
    robot_right.set_joint_position_target(right_joints)
    robot_left.write_data_to_sim()
    robot_right.write_data_to_sim()

    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 2: Move to grasp
    print("[Phase 2] Moving to grasp position...")
    left_target = torch.tensor([PHASE2_LEFT_JOINTS + [GRIPPER_INIT, GRIPPER_INIT]],
                               dtype=torch.float32, device=sim.device)
    right_target = torch.tensor([PHASE2_RIGHT_JOINTS + [GRIPPER_INIT, GRIPPER_INIT]],
                                dtype=torch.float32, device=sim.device)

    for _ in range(150):
        robot_left.set_joint_position_target(left_target)
        robot_right.set_joint_position_target(right_target)
        robot_left.write_data_to_sim()
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Close grippers
    print("[Phase 2.5] Closing grippers...")
    left_closed = torch.tensor([PHASE2_LEFT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]],
                               dtype=torch.float32, device=sim.device)
    right_closed = torch.tensor([PHASE2_RIGHT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]],
                                dtype=torch.float32, device=sim.device)

    for _ in range(50):
        robot_left.set_joint_position_target(left_closed)
        robot_right.set_joint_position_target(right_closed)
        robot_left.write_data_to_sim()
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Check positions
    print("\n" + "="*60)
    print("POSITION CHECK (using panda_hand)")
    print("="*60)

    hand_left_idx = robot_left.find_bodies("panda_hand")[0][0]
    hand_right_idx = robot_right.find_bodies("panda_hand")[0][0]

    hand_left_pos = robot_left.data.body_pos_w[0, hand_left_idx].cpu().numpy()
    hand_right_pos = robot_right.data.body_pos_w[0, hand_right_idx].cpu().numpy()

    cable_pos = cable.data.body_pos_w[0].cpu().numpy()
    seg17_pos = cable_pos[17]
    seg19_pos = cable_pos[19]

    # Fingertip position (hand + offset)
    # Wall-mount: fingertip is -0.1123m in Z from panda_hand
    fingertip_offset = np.array([0.0, 0.0, -0.1123])
    fingertip_left = hand_left_pos + fingertip_offset
    fingertip_right = hand_right_pos + fingertip_offset

    print(f"panda_hand (left):  {hand_left_pos}")
    print(f"Fingertip (left):   {fingertip_left}")
    print(f"seg_17:             {seg17_pos}")
    print(f"Fingertip-Cable dist: {np.linalg.norm(fingertip_left - seg17_pos)*100:.2f}cm")

    print(f"\npanda_hand (right): {hand_right_pos}")
    print(f"Fingertip (right):  {fingertip_right}")
    print(f"seg_19:             {seg19_pos}")
    print(f"Fingertip-Cable dist: {np.linalg.norm(fingertip_right - seg19_pos)*100:.2f}cm")

    # Create D6 constraints using panda_hand with fingertip offset
    print("\n[D6] Creating constraints with panda_hand + fingertip offset...")

    try:
        grasp_manager.create_grasp(
            "left",
            "/World/envs/env_0/Robot_Left/panda_hand",  # panda_hand instead of panda_leftfinger
            "/World/envs/env_0/Cable/seg_17",
            local_pos0=(0.0, 0.0, -0.1123),  # Fingertip offset in wall-mount config
            local_pos1=(0.0, 0.0, 0.0)
        )
        print("  D6 constraint created: LEFT panda_hand -> seg_17")
    except Exception as e:
        print(f"  WARNING: Left D6 constraint failed: {e}")

    try:
        grasp_manager.create_grasp(
            "right",
            "/World/envs/env_0/Robot_Right/panda_hand",
            "/World/envs/env_0/Cable/seg_19",
            local_pos0=(0.0, 0.0, -0.1123),
            local_pos1=(0.0, 0.0, 0.0)
        )
        print("  D6 constraint created: RIGHT panda_hand -> seg_19")
    except Exception as e:
        print(f"  WARNING: Right D6 constraint failed: {e}")

    # Phase 3: Lift
    print("\n[Phase 3] Lifting...")
    left_lift = torch.tensor([PHASE3_LEFT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]],
                             dtype=torch.float32, device=sim.device)
    right_lift = torch.tensor([PHASE3_RIGHT_JOINTS + [GRIPPER_CLOSED, GRIPPER_CLOSED]],
                              dtype=torch.float32, device=sim.device)

    for step in range(150):
        robot_left.set_joint_position_target(left_lift)
        robot_right.set_joint_position_target(right_lift)
        robot_left.write_data_to_sim()
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if (step + 1) % 50 == 0:
            cable_z = cable.data.body_pos_w[0, 17, 2].item()
            print(f"  Step {step+1}: Cable seg_17 Z = {cable_z:.4f}")

    # Final check
    print("\n" + "="*60)
    print("LIFT RESULT")
    print("="*60)

    final_cable_pos = cable.data.body_pos_w[0].cpu().numpy()
    initial_z = 0.755  # Expected initial cable Z

    seg17_z = final_cable_pos[17, 2]
    seg19_z = final_cable_pos[19, 2]

    lift_left = seg17_z - initial_z
    lift_right = seg19_z - initial_z

    print(f"seg_17 Z: {seg17_z:.4f} (lift: {lift_left*100:.2f}cm)")
    print(f"seg_19 Z: {seg19_z:.4f} (lift: {lift_right*100:.2f}cm)")

    if lift_left > 0.01 or lift_right > 0.01:
        print("\n✅ CABLE LIFTED SUCCESSFULLY!")
    else:
        print("\n❌ Cable did not lift")

    print("="*60)
    simulation_app.close()


if __name__ == "__main__":
    main()
