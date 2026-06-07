#!/usr/bin/env python3
"""
Contact Debug Test - Check physical contact between gripper fingers and cable
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.insert(0, "/home/rlrk/IsaacLab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg, ContactSensor
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    CABLE_Z, CABLE_RADIUS
)

# PhysX imports for contact detection
from pxr import UsdPhysics, PhysxSchema, Usd
from omni.physx import get_physx_scene_query_interface

print("=" * 60)
print("CONTACT DEBUG TEST")
print("=" * 60)

# Setup simulation
sim_cfg = sim_utils.SimulationCfg(
    dt=1/240,
    render_interval=1,
    physics_material=sim_utils.RigidBodyMaterialCfg(
        static_friction=1.0,
        dynamic_friction=1.0,
        restitution=0.0,
        friction_combine_mode="multiply",
    ),
)
sim = sim_utils.SimulationContext(sim_cfg)
scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]

device = robot_left.device
body_names = robot_left.body_names
hand_idx = body_names.index('panda_hand')

def get_gripper_state(robot, name):
    pos = robot.data.joint_pos[0, -2:].cpu().numpy()
    return f"{name}: j1={pos[0]:.6f}, j2={pos[1]:.6f}, gap={sum(pos)*1000:.2f}mm"

def get_cable_z():
    cable_pos = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    return np.nanmean(cable_pos), np.nanmin(cable_pos), np.nanmax(cable_pos)

def check_finger_cable_overlap():
    """Check if finger positions overlap with cable position (simple geometric check)"""
    # Get finger positions (using fingertip approximation)
    left_hand = robot_left.data.body_pos_w[0, hand_idx].cpu().numpy()
    right_hand = robot_right.data.body_pos_w[0, hand_idx].cpu().numpy()

    # Fingertip offset from hand (approximately 11.2cm below)
    fingertip_offset = 0.112
    left_fingertip_z = left_hand[2] - fingertip_offset
    right_fingertip_z = right_hand[2] - fingertip_offset

    # Cable position at seg17
    cable_pos = cable.data.body_pos_w[0, 17].cpu().numpy()
    cable_z = cable_pos[2]

    # Check Z overlap (fingertip should be at cable level +/- tolerance)
    z_tolerance = 0.02  # 2cm
    left_z_contact = abs(left_fingertip_z - cable_z) < z_tolerance
    right_z_contact = abs(right_fingertip_z - cable_z) < z_tolerance

    return {
        'left_fingertip_z': left_fingertip_z,
        'right_fingertip_z': right_fingertip_z,
        'cable_z': cable_z,
        'left_z_overlap': left_z_contact,
        'right_z_overlap': right_z_contact,
        'z_diff_left': left_fingertip_z - cable_z,
        'z_diff_right': right_fingertip_z - cable_z,
    }

print(f"\nInitial cable Z: {get_cable_z()[0]:.4f}")

# ============================================================
# PHASE 2: GRASP
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2: GRASP")
print("=" * 60)

# Step 1: Open grippers
print("\n--- Step 1: Open grippers ---")
for _ in range(100):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, -2] = 0.04
    target_left[0, -1] = 0.04
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, -2] = 0.04
    target_right[0, -1] = 0.04
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

print(f"  {get_gripper_state(robot_left, 'Left')}")
print(f"  {get_gripper_state(robot_right, 'Right')}")

# Step 2: Teleport to Phase 2
print("\n--- Step 2: Teleport ARM to Phase 2 ---")
arm_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
arm_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
arm_left[0, -2] = 0.04
arm_left[0, -1] = 0.04
robot_left.write_joint_state_to_sim(arm_left, robot_left.data.joint_vel[0].unsqueeze(0))

arm_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
arm_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
arm_right[0, -2] = 0.04
arm_right[0, -1] = 0.04
robot_right.write_joint_state_to_sim(arm_right, robot_right.data.joint_vel[0].unsqueeze(0))

for _ in range(50):
    robot_left.set_joint_position_target(arm_left)
    robot_left.write_data_to_sim()
    robot_right.set_joint_position_target(arm_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

# Check overlap before grasp
print("\n--- Contact Check (before grasp) ---")
overlap = check_finger_cable_overlap()
print(f"  Left fingertip Z:  {overlap['left_fingertip_z']:.4f}")
print(f"  Right fingertip Z: {overlap['right_fingertip_z']:.4f}")
print(f"  Cable Z:           {overlap['cable_z']:.4f}")
print(f"  Z diff (Left):     {overlap['z_diff_left']*100:.2f}cm")
print(f"  Z diff (Right):    {overlap['z_diff_right']*100:.2f}cm")
print(f"  Left Z overlap:    {overlap['left_z_overlap']}")
print(f"  Right Z overlap:   {overlap['right_z_overlap']}")

# Step 3: Close grippers
print("\n--- Step 3: Close grippers (grasp) ---")
for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2] = 0.0
    target_left[0, -1] = 0.0
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2] = 0.0
    target_right[0, -1] = 0.0
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    # Monitor gap during closing
    if (i+1) % 100 == 0:
        left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
        right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
        cable_z = get_cable_z()[0]
        print(f"  Step {i+1}/300: Left gap={sum(left_pos)*1000:.2f}mm, Right gap={sum(right_pos)*1000:.2f}mm, Cable Z={cable_z:.4f}")

# Final gripper state
left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
left_gap = sum(left_pos) * 1000
right_gap = sum(right_pos) * 1000

print(f"\n--- After Grasp Results ---")
print(f"  {get_gripper_state(robot_left, 'Left')}")
print(f"  {get_gripper_state(robot_right, 'Right')}")
print(f"  Cable Z: {get_cable_z()[0]:.4f}")

# Check overlap after grasp
print("\n--- Contact Check (after grasp) ---")
overlap = check_finger_cable_overlap()
print(f"  Left fingertip Z:  {overlap['left_fingertip_z']:.4f}")
print(f"  Right fingertip Z: {overlap['right_fingertip_z']:.4f}")
print(f"  Cable Z:           {overlap['cable_z']:.4f}")
print(f"  Z diff (Left):     {overlap['z_diff_left']*100:.2f}cm")
print(f"  Z diff (Right):    {overlap['z_diff_right']*100:.2f}cm")
print(f"  Left Z overlap:    {overlap['left_z_overlap']}")
print(f"  Right Z overlap:   {overlap['right_z_overlap']}")

# Check if gap indicates cable contact
cable_diameter_mm = CABLE_RADIUS * 2 * 1000  # 10mm
gap_indicates_contact = (abs(left_gap - cable_diameter_mm) < 3) and (abs(right_gap - cable_diameter_mm) < 3)
print(f"\n  Gap indicates cable contact: {gap_indicates_contact}")
print(f"  (Expected gap ~{cable_diameter_mm}mm, actual: Left={left_gap:.1f}mm, Right={right_gap:.1f}mm)")

# ============================================================
# PHASE 3: LIFT
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: LIFT")
print("=" * 60)

GRASP_JOINT_POS = 0.0052  # Maintain gap

target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
target_left[0, :7] = torch.tensor(PHASE3_LEFT_JOINTS, device=target_left.device)
target_left[0, -2] = GRASP_JOINT_POS
target_left[0, -1] = GRASP_JOINT_POS

target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
target_right[0, :7] = torch.tensor(PHASE3_RIGHT_JOINTS, device=target_right.device)
target_right[0, -2] = GRASP_JOINT_POS
target_right[0, -1] = GRASP_JOINT_POS

print("\n--- Lifting (600 steps) ---")
for i in range(600):
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

    if (i+1) % 200 == 0:
        overlap = check_finger_cable_overlap()
        left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
        right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
        print(f"  Step {i+1}/600:")
        print(f"    Cable Z: {overlap['cable_z']:.4f}")
        print(f"    Left fingertip Z: {overlap['left_fingertip_z']:.4f}, Z diff: {overlap['z_diff_left']*100:.2f}cm")
        print(f"    Right fingertip Z: {overlap['right_fingertip_z']:.4f}, Z diff: {overlap['z_diff_right']*100:.2f}cm")
        print(f"    Gaps: Left={sum(left_pos)*1000:.2f}mm, Right={sum(right_pos)*1000:.2f}mm")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

final_overlap = check_finger_cable_overlap()
final_cable_z = final_overlap['cable_z']
left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()

print(f"\nCable Z: {final_cable_z:.4f}")
print(f"Left fingertip Z: {final_overlap['left_fingertip_z']:.4f}")
print(f"Right fingertip Z: {final_overlap['right_fingertip_z']:.4f}")
print(f"Z diff (Left): {final_overlap['z_diff_left']*100:.2f}cm")
print(f"Z diff (Right): {final_overlap['z_diff_right']*100:.2f}cm")
print(f"Gaps: Left={sum(left_pos)*1000:.2f}mm, Right={sum(right_pos)*1000:.2f}mm")

# Summary table
print("\n" + "=" * 60)
print("CONTACT SUMMARY")
print("=" * 60)
print(f"| Phase          | Z diff (Left) | Z diff (Right) | Gap   |")
print(f"|----------------|---------------|----------------|-------|")
print(f"| After Grasp    | {overlap['z_diff_left']*100:+.2f}cm       | {overlap['z_diff_right']*100:+.2f}cm        | {left_gap:.1f}mm |")
print(f"| After Lift     | {final_overlap['z_diff_left']*100:+.2f}cm       | {final_overlap['z_diff_right']*100:+.2f}cm        | {sum(left_pos)*1000:.1f}mm |")

# Cleanup
simulation_app.close()
