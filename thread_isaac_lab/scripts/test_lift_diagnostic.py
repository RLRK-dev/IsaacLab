#!/usr/bin/env python3
"""
Lift Diagnostic Test - Detailed logging to identify slip cause
Logs every 10 steps:
1. Gripper orientation (Roll/Pitch/Yaw)
2. Actual friction coefficients
3. Cable segment positions at grasp points
4. Distance between left/right grippers
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
from scipy.spatial.transform import Rotation as R

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS

print("=" * 80)
print("LIFT DIAGNOSTIC TEST - DETAILED LOGGING")
print("=" * 80)

# Parameters
GRIPPER_CLOSE = 0.001
FRICTION = 5.0
LIFT_TOTAL = 0.15
NUM_STEPS = 300
LIFT_PER_STEP = LIFT_TOTAL / NUM_STEPS

# Setup
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)

@configclass
class TestSceneCfg(DualArmSceneCfg):
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )

scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
contact_left = scene["contact_left"]
contact_right = scene["contact_right"]

device = robot_left.device

# Apply friction
print("\nApplying friction=5.0...")
def set_friction(asset, value):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = value
    materials[..., 1] = value
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FRICTION)
set_friction(robot_right, FRICTION)
set_friction(cable, FRICTION)

# Setup Diff IK
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

# Helper functions
def quat_to_euler(quat_wxyz):
    """Convert quaternion (w,x,y,z) to euler angles (roll, pitch, yaw) in degrees"""
    q = quat_wxyz.cpu().numpy()
    # scipy expects (x,y,z,w) format
    r = R.from_quat([q[1], q[2], q[3], q[0]])
    return r.as_euler('xyz', degrees=True)

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_ee_quat(robot, idx):
    return robot.data.body_quat_w[0, idx]

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_segment_positions():
    """Get positions of cable segments 8-12 (center region near grasp)"""
    positions = cable.data.body_pos_w[0].cpu().numpy()
    return positions[8:13]  # seg_8 to seg_12

def get_gripper_distance():
    """Distance between left and right EE positions"""
    pos_l = get_ee_pos(robot_left, jacobian_body_left)
    pos_r = get_ee_pos(robot_right, jacobian_body_right)
    return np.linalg.norm(pos_l - pos_r)

def get_friction_coeffs():
    """Get actual friction coefficients"""
    mat_left = robot_left.root_physx_view.get_material_properties()
    mat_cable = cable.root_physx_view.get_material_properties()
    # [static, dynamic, restitution]
    return {
        'robot_static': mat_left[0, 0, 0].item(),
        'robot_dynamic': mat_left[0, 0, 1].item(),
        'cable_static': mat_cable[0, 0, 0].item(),
        'cable_dynamic': mat_cable[0, 0, 1].item(),
    }

def get_gripper_gap(robot):
    return robot.data.joint_pos[0, -2:].sum().item() * 1000

# ============================================================
# PHASES 1-2: Setup
# ============================================================
print("\nPhase 1: Open grippers...")
for _ in range(100):
    target = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target[0, -2:] = 0.04
    robot_left.set_joint_position_target(target)
    robot_left.write_data_to_sim()
    target = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target[0, -2:] = 0.04
    robot_right.set_joint_position_target(target)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

print("Phase 2A: Teleport to grasp position...")
arm_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
arm_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
arm_left[0, -2:] = 0.04
robot_left.write_joint_state_to_sim(arm_left, robot_left.data.joint_vel[0].unsqueeze(0))

arm_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
arm_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
arm_right[0, -2:] = 0.04
robot_right.write_joint_state_to_sim(arm_right, robot_right.data.joint_vel[0].unsqueeze(0))

for _ in range(50):
    robot_left.set_joint_position_target(arm_left)
    robot_left.write_data_to_sim()
    robot_right.set_joint_position_target(arm_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

print(f"Phase 2B: Close grippers (GRIPPER_CLOSE={GRIPPER_CLOSE})...")
for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()
    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

# Record Phase 2 state
phase2_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase2_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase2_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase2_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

phase2_ee_z = phase2_ee_pos_left[0, 2].item()
phase2_force_l = get_contact_force(contact_left)
phase2_force_r = get_contact_force(contact_right)
phase2_gripper_dist = get_gripper_distance()
phase2_cable_segs = get_cable_segment_positions()

# Get friction coefficients
friction_coeffs = get_friction_coeffs()

print("\n" + "=" * 80)
print("PHASE 2 COMPLETE - INITIAL STATE")
print("=" * 80)
print(f"  EE Z: {phase2_ee_z:.4f}")
print(f"  Contact Force: L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"  Gripper Distance: {phase2_gripper_dist:.4f}m ({phase2_gripper_dist*100:.2f}cm)")
print(f"  Gripper Gap: L={get_gripper_gap(robot_left):.2f}mm, R={get_gripper_gap(robot_right):.2f}mm")
print(f"\n  Friction Coefficients:")
print(f"    Robot: static={friction_coeffs['robot_static']:.2f}, dynamic={friction_coeffs['robot_dynamic']:.2f}")
print(f"    Cable: static={friction_coeffs['cable_static']:.2f}, dynamic={friction_coeffs['cable_dynamic']:.2f}")

# Gripper orientation
euler_l = quat_to_euler(phase2_ee_quat_left[0])
euler_r = quat_to_euler(phase2_ee_quat_right[0])
print(f"\n  Gripper Orientation (R/P/Y in degrees):")
print(f"    Left:  [{euler_l[0]:+7.2f}, {euler_l[1]:+7.2f}, {euler_l[2]:+7.2f}]")
print(f"    Right: [{euler_r[0]:+7.2f}, {euler_r[1]:+7.2f}, {euler_r[2]:+7.2f}]")

print(f"\n  Cable Segments 8-12 Z positions:")
for i, pos in enumerate(phase2_cable_segs):
    print(f"    seg_{i+8}: Z={pos[2]:.4f}")

# ============================================================
# PHASE 3: CUMULATIVE LIFT WITH DETAILED DIAGNOSTICS
# ============================================================
print("\n" + "=" * 80)
print("PHASE 3: LIFT WITH DIAGNOSTICS")
print("=" * 80)

target_pos_left = phase2_ee_pos_left.clone()
target_pos_right = phase2_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step = None

# Header
print(f"\n{'Step':>5} | {'EE Z':>6} | {'Lift':>5} | {'F_L':>6} | {'F_R':>6} | {'Dist':>6} | {'Gap_L':>5} | {'Roll_L':>6} | {'Pitch_L':>7} | {'CabZ_10':>7} | Status")
print("-" * 110)

for i in range(NUM_STEPS):
    # Update target
    target_pos_left[0, 2] += LIFT_PER_STEP
    target_pos_right[0, 2] += LIFT_PER_STEP

    command_left = torch.cat([target_pos_left, phase2_ee_quat_left], dim=1)
    command_right = torch.cat([target_pos_right, phase2_ee_quat_right], dim=1)

    diff_ik_left.set_command(command_left)
    diff_ik_right.set_command(command_right)

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

    # Get state
    ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)
    gripper_dist = get_gripper_distance()
    gap_l = get_gripper_gap(robot_left)
    lift = (ee_z - phase2_ee_z) * 100

    # Gripper orientation
    euler_l = quat_to_euler(robot_left.data.body_quat_w[0, jacobian_body_left])

    # Cable segment 10 Z
    cable_segs = get_cable_segment_positions()
    cab_z_10 = cable_segs[2, 2] if len(cable_segs) > 2 else float('nan')

    # Detect contact loss
    status = "OK"
    if contact_lost_step is None and force_l < 1.0 and force_r < 1.0:
        contact_lost_step = i
        status = "*** LOST ***"
    elif contact_lost_step is not None:
        status = "lost"

    # Log every 10 steps or on contact loss
    if i % 10 == 0 or status == "*** LOST ***" or i == NUM_STEPS - 1:
        print(f"{i:>5} | {ee_z:>6.4f} | {lift:>4.1f}cm | {force_l:>5.1f}N | {force_r:>5.1f}N | {gripper_dist*100:>5.2f}cm | {gap_l:>4.1f}mm | {euler_l[0]:>+6.1f} | {euler_l[1]:>+7.1f} | {cab_z_10:>7.4f} | {status}")

    # Early exit after contact loss is detected (20 more steps for analysis)
    if contact_lost_step is not None and i > contact_lost_step + 20:
        print(f"\n  [Early exit: Contact lost at step {contact_lost_step}]")
        break

# ============================================================
# FINAL ANALYSIS
# ============================================================
print("\n" + "=" * 80)
print("DIAGNOSTIC ANALYSIS")
print("=" * 80)

if contact_lost_step is not None:
    lost_lift = contact_lost_step * LIFT_PER_STEP * 100
    print(f"\n1. Contact Lost:")
    print(f"   Step: {contact_lost_step}")
    print(f"   Lift at loss: {lost_lift:.2f}cm")

    print(f"\n2. Possible Causes:")

    # Check gripper distance change
    final_dist = get_gripper_distance()
    dist_change = (final_dist - phase2_gripper_dist) * 100
    print(f"   a) Gripper separation: {phase2_gripper_dist*100:.2f}cm -> current (check log)")
    if abs(dist_change) > 0.5:
        print(f"      -> ISSUE: Grippers moved apart by {dist_change:.2f}cm")

    # Check friction
    print(f"   b) Friction: static={friction_coeffs['robot_static']:.1f}, dynamic={friction_coeffs['robot_dynamic']:.1f}")

    # Check grip force vs lift dynamics
    print(f"   c) Phase 2 force: L={phase2_force_l:.1f}N, R={phase2_force_r:.1f}N")
    print(f"      Lift speed: {LIFT_PER_STEP*1000:.2f}mm/step = {LIFT_PER_STEP*240*1000:.1f}mm/s")

else:
    final_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
    print(f"\n SUCCESS: Contact maintained!")
    print(f"   Final lift: {(final_ee_z - phase2_ee_z)*100:.2f}cm")

simulation_app.close()
