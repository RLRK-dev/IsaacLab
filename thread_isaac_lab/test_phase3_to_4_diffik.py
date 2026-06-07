#!/usr/bin/env python3
"""
Phase 3 -> 4 Cumulative Diff IK Transition Test

Background: T2 analysis shows Phase 3->4 has 240° joint change in right arm (IK branch switching).
Solution: Use cumulative Diff IK to transition continuously.

Implementation:
- Start from Phase 3 joint angles (after grasp and lift)
- NUM_STEPS = 1000 (0.24°/step)
- Linear interpolation in Cartesian EE space
- Diff IK to convert EE delta to joint commands
- No reset() between steps (cumulative)

Reference: TASKS_T3.md, CLAUDE.md
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
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    WAYPOINT_PHASE3_LEFT, WAYPOINT_PHASE3_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    GRIPPER_CLOSE,
    FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION,
    CABLE_STATIC_FRICTION, CABLE_DYNAMIC_FRICTION,
)

print("=" * 70)
print("PHASE 3 -> 4 CUMULATIVE DIFF IK TRANSITION TEST")
print("=" * 70)
print(f"Phase 3 Left EE:  {WAYPOINT_PHASE3_LEFT}")
print(f"Phase 3 Right EE: {WAYPOINT_PHASE3_RIGHT}")
print(f"Phase 4 Left EE:  {WAYPOINT_PHASE4_LEFT}")
print(f"Phase 4 Right EE: {WAYPOINT_PHASE4_RIGHT}")

# Calculate distances
p3_left = np.array(WAYPOINT_PHASE3_LEFT)
p3_right = np.array(WAYPOINT_PHASE3_RIGHT)
p4_left = np.array(WAYPOINT_PHASE4_LEFT)
p4_right = np.array(WAYPOINT_PHASE4_RIGHT)

dist_left = np.linalg.norm(p4_left - p3_left)
dist_right = np.linalg.norm(p4_right - p3_right)
print(f"\nCartesian distance: Left={dist_left*100:.2f}cm, Right={dist_right*100:.2f}cm")

# Parameters (use task_config.py friction values - 9.5cm success config)
NUM_STEPS = 1000  # 0.24°/step for 240° change

print(f"\nParameters:")
print(f"  NUM_STEPS: {NUM_STEPS}")
print(f"  GRIPPER_CLOSE: {GRIPPER_CLOSE}")
print(f"  FINGER_FRICTION: static={FINGER_STATIC_FRICTION}, dynamic={FINGER_DYNAMIC_FRICTION}")
print(f"  CABLE_FRICTION: static={CABLE_STATIC_FRICTION}, dynamic={CABLE_DYNAMIC_FRICTION}")
print("=" * 70)

# Setup simulation
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)

scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]

device = robot_left.device

# Apply friction
print("\nApplying friction...")
def set_friction(asset, static_f, dynamic_f):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = static_f
    materials[..., 1] = dynamic_f
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION)
set_friction(robot_right, FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION)
set_friction(cable, CABLE_STATIC_FRICTION, CABLE_DYNAMIC_FRICTION)

# Setup Diff IK controllers - ABSOLUTE position mode (not relative)
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,  # Use absolute position
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

# Jacobian body indices
jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_ee_quat(robot, idx):
    return robot.data.body_quat_w[0, idx]

def get_cable_center_z():
    z_vals = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    valid = z_vals[~np.isnan(z_vals)]
    if len(valid) > 0:
        return np.mean(valid[len(valid)//3:2*len(valid)//3])
    return float('nan')

def get_joint_angles(robot):
    """Get arm joint angles in degrees"""
    return robot.data.joint_pos[0, :7].cpu().numpy() * 180 / np.pi

# ============================================================
# SETUP: Teleport directly to Phase 3 position
# This simulates starting after successful grasp and lift
# ============================================================
print("\n" + "=" * 70)
print("SETUP: Teleport to Phase 3 position (simulating post-grasp state)")
print("=" * 70)

# Set Phase 3 joint angles directly
arm_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
arm_left[0, :7] = torch.tensor(PHASE3_LEFT_JOINTS, device=device)
arm_left[0, -2:] = GRIPPER_CLOSE
robot_left.write_joint_state_to_sim(arm_left, robot_left.data.joint_vel[0].unsqueeze(0))

arm_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
arm_right[0, :7] = torch.tensor(PHASE3_RIGHT_JOINTS, device=device)
arm_right[0, -2:] = GRIPPER_CLOSE
robot_right.write_joint_state_to_sim(arm_right, robot_right.data.joint_vel[0].unsqueeze(0))

# Stabilize
for _ in range(100):
    robot_left.set_joint_position_target(arm_left)
    robot_left.write_data_to_sim()
    robot_right.set_joint_position_target(arm_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

phase3_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase3_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase3_joints_left = get_joint_angles(robot_left)
phase3_joints_right = get_joint_angles(robot_right)

print(f"\nPhase 3 Starting State:")
print(f"  EE Left:  ({phase3_ee_left[0]:.4f}, {phase3_ee_left[1]:.4f}, {phase3_ee_left[2]:.4f})")
print(f"  EE Right: ({phase3_ee_right[0]:.4f}, {phase3_ee_right[1]:.4f}, {phase3_ee_right[2]:.4f})")
print(f"  Target:   Phase 3 = {WAYPOINT_PHASE3_LEFT}, {WAYPOINT_PHASE3_RIGHT}")
print(f"  Joint angles Left:  {phase3_joints_left}")
print(f"  Joint angles Right: {phase3_joints_right}")

# ============================================================
# PHASE 3->4: CUMULATIVE DIFF IK TRANSITION (Main test)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 3 -> 4: CUMULATIVE DIFF IK TRANSITION")
print(f"  NUM_STEPS: {NUM_STEPS}")
print(f"  Target Left:  {WAYPOINT_PHASE4_LEFT}")
print(f"  Target Right: {WAYPOINT_PHASE4_RIGHT}")
print("=" * 70)

# Record starting state (use actual current EE positions)
start_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
start_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
start_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
start_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

print(f"\nStarting EE positions:")
print(f"  Left:  {start_ee_pos_left[0].cpu().numpy()}")
print(f"  Right: {start_ee_pos_right[0].cpu().numpy()}")

# Phase 4 target positions - apply Z offset to match Isaac Sim coordinate system
# See CLAUDE.md: Z_OFFSET_COMPENSATION = 0.1034 (IK vs Isaac Lab kinematics差)
Z_OFFSET = 0.1034
target_phase4_left = torch.tensor(
    [[WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)
target_phase4_right = torch.tensor(
    [[WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)

# Reset IK controllers once at the beginning
diff_ik_left.reset()
diff_ik_right.reset()

# Track metrics
max_joint_change_per_step = 0.0
joint_history_right = []

print(f"\n{'Step':>5} | {'EE L X':>7} | {'EE L Y':>7} | {'EE L Z':>7} | {'EE R X':>7} | {'EE R Y':>7} | {'EE R Z':>7} | {'Max dJ':>7}")
print("-" * 95)

for i in range(NUM_STEPS):
    alpha = (i + 1) / NUM_STEPS

    # Linear interpolation to Phase 4 target
    target_pos_left = start_ee_pos_left + alpha * (target_phase4_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase4_right - start_ee_pos_right)

    # Create command: [x, y, z, qw, qx, qy, qz] for absolute mode
    command_left = torch.cat([target_pos_left, start_ee_quat_left], dim=1)
    command_right = torch.cat([target_pos_right, start_ee_quat_right], dim=1)

    # Set command (no reset, just update target - cumulative)
    diff_ik_left.set_command(command_left)
    diff_ik_right.set_command(command_right)

    # Get previous joint angles for comparison
    prev_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().copy()

    # Compute IK
    jacobian_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jacobian_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

    ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right]

    joint_pos_left = robot_left.data.joint_pos[:, :7]
    joint_pos_right = robot_right.data.joint_pos[:, :7]

    joint_cmd_left = diff_ik_left.compute(ee_pos_left, ee_quat_left, jacobian_left, joint_pos_left)
    joint_cmd_right = diff_ik_right.compute(ee_pos_right, ee_quat_right, jacobian_right, joint_pos_right)

    # Apply commands
    target_left_joints = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left_joints[0, :7] = joint_cmd_left[0]
    target_left_joints[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left_joints)
    robot_left.write_data_to_sim()

    target_right_joints = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right_joints[0, :7] = joint_cmd_right[0]
    target_right_joints[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right_joints)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    # Calculate joint change
    curr_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy()
    joint_change = np.abs(curr_joints_right - prev_joints_right) * 180 / np.pi
    max_change = np.max(joint_change)
    if max_change > max_joint_change_per_step:
        max_joint_change_per_step = max_change

    # Record joint history periodically
    if i % 100 == 0:
        joint_history_right.append(curr_joints_right * 180 / np.pi)

    # Get current state
    ee_l = get_ee_pos(robot_left, jacobian_body_left)
    ee_r = get_ee_pos(robot_right, jacobian_body_right)

    # Log every 100 steps
    if i % 100 == 0 or i == NUM_STEPS - 1:
        print(f"{i:>5} | {ee_l[0]:>7.4f} | {ee_l[1]:>7.4f} | {ee_l[2]:>7.4f} | {ee_r[0]:>7.4f} | {ee_r[1]:>7.4f} | {ee_r[2]:>7.4f} | {max_change:>6.2f}°")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)

final_ee_left = get_ee_pos(robot_left, jacobian_body_left)
final_ee_right = get_ee_pos(robot_right, jacobian_body_right)
final_joints_left = get_joint_angles(robot_left)
final_joints_right = get_joint_angles(robot_right)
final_cable_z = get_cable_center_z()

# EE position error (compare with Z_OFFSET applied target)
target_left_with_offset = np.array([WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET])
target_right_with_offset = np.array([WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET])
ee_error_left = np.linalg.norm(final_ee_left - target_left_with_offset) * 100
ee_error_right = np.linalg.norm(final_ee_right - target_right_with_offset) * 100

print(f"\n1. EE Positions (Target vs Actual - Isaac Sim coordinates with Z_OFFSET={Z_OFFSET}):")
print(f"   Left Target:  ({target_left_with_offset[0]:.4f}, {target_left_with_offset[1]:.4f}, {target_left_with_offset[2]:.4f})")
print(f"   Left Actual:  ({final_ee_left[0]:.4f}, {final_ee_left[1]:.4f}, {final_ee_left[2]:.4f})")
print(f"   Left Error:   {ee_error_left:.2f}cm")
print(f"   Right Target: ({target_right_with_offset[0]:.4f}, {target_right_with_offset[1]:.4f}, {target_right_with_offset[2]:.4f})")
print(f"   Right Actual: ({final_ee_right[0]:.4f}, {final_ee_right[1]:.4f}, {final_ee_right[2]:.4f})")
print(f"   Right Error:  {ee_error_right:.2f}cm")

print(f"\n2. Joint Angle Continuity (Right Arm):")
print(f"   Max change per step: {max_joint_change_per_step:.2f}°")
print(f"   Phase 3 joints: {phase3_joints_right}")
print(f"   Phase 4 joints: {final_joints_right}")
print(f"   Total change per joint:")
for j in range(7):
    change = final_joints_right[j] - phase3_joints_right[j]
    print(f"     Joint {j+1}: {change:+.1f}°")

print(f"\n3. Cable Z: {final_cable_z:.4f}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

success_ee = ee_error_left < 2.0 and ee_error_right < 2.0
success_continuity = max_joint_change_per_step < 5.0  # < 5° per step is smooth

print(f"  EE Position (error < 2cm):     {'PASS' if success_ee else 'FAIL'} (L={ee_error_left:.2f}cm, R={ee_error_right:.2f}cm)")
print(f"  Joint Continuity (<5°/step):   {'PASS' if success_continuity else 'FAIL'} (max={max_joint_change_per_step:.2f}°)")

if success_ee and success_continuity:
    print("\n  OVERALL: SUCCESS - Phase 3->4 transition completed smoothly")
    print("  The cumulative Diff IK approach successfully avoided the 240° joint jump!")
else:
    print("\n  OVERALL: NEEDS INVESTIGATION")
    if not success_ee:
        print("  - EE position did not reach target")
    if not success_continuity:
        print("  - Joint angles changed too rapidly")

print("=" * 70)

simulation_app.close()
