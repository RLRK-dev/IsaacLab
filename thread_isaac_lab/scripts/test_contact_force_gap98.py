#!/usr/bin/env python3
"""
Contact Force Test - Gap=9.8mm
Measure contact force between gripper fingers and cable using ContactSensor
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
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg, ContactSensor
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.utils import configclass
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    CABLE_Z, CABLE_RADIUS
)

print("=" * 60)
print("CONTACT FORCE TEST - Gap=9.8mm")
print("=" * 60)

# Target gap
TARGET_GAP_MM = 9.8
GRASP_JOINT_POS = TARGET_GAP_MM / 2.0 / 1000.0  # 0.0049

# Setup simulation
sim_cfg = sim_utils.SimulationCfg(
    dt=1/240,
    render_interval=1,
    physics_material=sim_utils.RigidBodyMaterialCfg(
        static_friction=2.0,
        dynamic_friction=2.0,
        restitution=0.0,
        friction_combine_mode="multiply",
    ),
)
sim = sim_utils.SimulationContext(sim_cfg)

# Create scene with ContactSensor
@configclass
class ContactTestSceneCfg(DualArmSceneCfg):
    """Scene with contact sensors on gripper fingers"""

    # Contact sensor for left gripper
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0,
        history_length=1,
        track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"],
        debug_vis=False,
    )

    # Contact sensor for right gripper
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0,
        history_length=1,
        track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"],
        debug_vis=False,
    )

scene_cfg = ContactTestSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
contact_left = scene["contact_left"]
contact_right = scene["contact_right"]

device = robot_left.device

def get_gripper_state(robot, name):
    pos = robot.data.joint_pos[0, -2:].cpu().numpy()
    return f"{name}: gap={sum(pos)*1000:.2f}mm"

def get_cable_z():
    cable_pos = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    return np.nanmean(cable_pos)

def get_contact_forces():
    """Get contact forces from sensors"""
    # Force data shape: (num_envs, num_bodies, 3) for net_forces_w
    left_force = contact_left.data.net_forces_w[0].cpu().numpy()
    right_force = contact_right.data.net_forces_w[0].cpu().numpy()

    left_mag = np.linalg.norm(left_force)
    right_mag = np.linalg.norm(right_force)

    return {
        'left_force': left_force,
        'right_force': right_force,
        'left_mag': left_mag,
        'right_mag': right_mag,
    }

print(f"\nTarget gap: {TARGET_GAP_MM}mm (GRASP_JOINT_POS={GRASP_JOINT_POS:.4f})")
print(f"Initial cable Z: {get_cable_z():.4f}")
print(f"Cable diameter: {CABLE_RADIUS * 2 * 1000:.1f}mm")

# ============================================================
# PHASE 1: OPEN GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 1: OPEN GRIPPERS")
print("=" * 60)

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

# ============================================================
# PHASE 2A: TELEPORT TO GRASP POSITION
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2A: TELEPORT TO GRASP POSITION")
print("=" * 60)

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

print(f"  {get_gripper_state(robot_left, 'Left')}")
print(f"  {get_gripper_state(robot_right, 'Right')}")
print(f"  Cable Z: {get_cable_z():.4f}")

# ============================================================
# PHASE 2B: CLOSE GRIPPERS TO TARGET GAP
# ============================================================
print("\n" + "=" * 60)
print(f"PHASE 2B: CLOSE GRIPPERS TO {TARGET_GAP_MM}mm GAP")
print("=" * 60)

for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2] = GRASP_JOINT_POS
    target_left[0, -1] = GRASP_JOINT_POS
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2] = GRASP_JOINT_POS
    target_right[0, -1] = GRASP_JOINT_POS
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    if (i+1) % 100 == 0:
        left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
        right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
        forces = get_contact_forces()
        print(f"  Step {i+1}/300:")
        print(f"    Left gap: {sum(left_pos)*1000:.2f}mm")
        print(f"    Right gap: {sum(right_pos)*1000:.2f}mm")
        print(f"    Left force: {forces['left_mag']:.4f}N")
        print(f"    Right force: {forces['right_mag']:.4f}N")

# ============================================================
# PHASE 2C: STABILIZATION (maintain gap)
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2C: STABILIZATION (50 steps)")
print("=" * 60)

for i in range(50):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2] = GRASP_JOINT_POS
    target_left[0, -1] = GRASP_JOINT_POS
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2] = GRASP_JOINT_POS
    target_right[0, -1] = GRASP_JOINT_POS
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS (Phase 2 Complete)")
print("=" * 60)

left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
left_gap = sum(left_pos) * 1000
right_gap = sum(right_pos) * 1000

forces = get_contact_forces()

print(f"\nGripper State:")
print(f"  Left gap:  {left_gap:.2f}mm (target: {TARGET_GAP_MM}mm)")
print(f"  Right gap: {right_gap:.2f}mm (target: {TARGET_GAP_MM}mm)")

print(f"\nContact Forces:")
print(f"  Left force:  {forces['left_force']} (mag: {forces['left_mag']:.4f}N)")
print(f"  Right force: {forces['right_force']} (mag: {forces['right_mag']:.4f}N)")

print(f"\nCable State:")
print(f"  Cable Z: {get_cable_z():.4f}")

# Check contact detection
contact_detected = forces['left_mag'] > 0.01 or forces['right_mag'] > 0.01

print("\n" + "=" * 60)
print("SUMMARY TABLE")
print("=" * 60)
print(f"| Item             | Value       |")
print(f"|------------------|-------------|")
print(f"| Target Gap       | {TARGET_GAP_MM}mm       |")
print(f"| Actual Gap (L)   | {left_gap:.2f}mm      |")
print(f"| Actual Gap (R)   | {right_gap:.2f}mm      |")
print(f"| Contact Detected | {contact_detected}     |")
print(f"| Left Force (N)   | {forces['left_mag']:.4f}      |")
print(f"| Right Force (N)  | {forces['right_mag']:.4f}      |")

# Additional: Check joint efforts as backup
left_effort = robot_left.data.applied_torque[0, -2:].cpu().numpy()
right_effort = robot_right.data.applied_torque[0, -2:].cpu().numpy()
print(f"\nJoint Efforts (backup):")
print(f"  Left effort:  {left_effort}")
print(f"  Right effort: {right_effort}")

# Cleanup
simulation_app.close()
