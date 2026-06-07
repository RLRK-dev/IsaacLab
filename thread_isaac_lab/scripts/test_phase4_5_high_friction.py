#!/usr/bin/env python3
"""
Phase 4 (Hook) -> Phase 5 (Placement) Test with High Friction

Using the V-groove finger configuration that achieved 13.6cm lift success.
Key settings:
- HIGH_FRICTION = 5.0 (not task_config.py 1.2/1.0)
- GRIPPER_CLOSE = 0.002 (from task_config.py)
- V-groove STL with 5mm groove depth

Test flow:
1. Phase 2: Grasp cable
2. Phase 3: Lift 5cm
3. Phase 4: Transition to hook approach
4. Phase 5: Cable placement

Based on test_cumulative_lift.py success configuration.
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
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    WAYPOINT_PHASE3_LEFT, WAYPOINT_PHASE3_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    GRIPPER_CLOSE, GRIPPER_OPEN,
)

print("=" * 70)
print("PHASE 4-5 TEST (HIGH FRICTION V-GROOVE)")
print("=" * 70)

# High friction settings (from 13.6cm lift success)
HIGH_FRICTION = 5.0

# Parameters
LIFT_NUM_STEPS = 300       # Phase 2->3 lift
PHASE34_NUM_STEPS = 500    # Phase 3->4 transition
PHASE45_NUM_STEPS = 400    # Phase 4->5 transition
Z_OFFSET = 0.1034          # IK vs Isaac Lab kinematics offset
LIFT_TARGET_CM = 5.0       # Target lift in cm

CONTACT_LOST_THRESHOLD = 10

print(f"\nConfiguration:")
print(f"  HIGH_FRICTION: {HIGH_FRICTION}")
print(f"  GRIPPER_CLOSE: {GRIPPER_CLOSE}")
print(f"  LIFT_TARGET: {LIFT_TARGET_CM}cm")
print(f"  Z_OFFSET: {Z_OFFSET}")
print("=" * 70)

# Setup simulation
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

# Apply HIGH FRICTION (key to success)
print(f"\nApplying HIGH_FRICTION={HIGH_FRICTION}...")
def set_friction(asset, static_f, dynamic_f):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = static_f
    materials[..., 1] = dynamic_f
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)

# Setup Diff IK controllers
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

# Jacobian body indices
jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

# Helper functions
def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_center_z():
    z_vals = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    valid = z_vals[~np.isnan(z_vals)]
    if len(valid) > 0:
        return np.mean(valid[len(valid)//3:2*len(valid)//3])
    return float('nan')

def set_robot_joints(robot, arm_joints, gripper_val):
    target = robot.data.joint_pos[0].unsqueeze(0).clone()
    target[0, :7] = torch.tensor(arm_joints, device=device)
    target[0, -2:] = gripper_val
    robot.set_joint_position_target(target)
    robot.write_data_to_sim()

def teleport_robot(robot, arm_joints, gripper_val):
    state = robot.data.joint_pos[0].unsqueeze(0).clone()
    state[0, :7] = torch.tensor(arm_joints, device=device)
    state[0, -2:] = gripper_val
    robot.write_joint_state_to_sim(state, robot.data.joint_vel[0].unsqueeze(0))

# ============================================================
# PHASE 2: GRASP
# ============================================================
print("\n" + "=" * 70)
print("PHASE 2: GRASP")
print("=" * 70)

teleport_robot(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
teleport_robot(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)

for _ in range(50):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)
    sim.step()
    scene.update(sim.get_physics_dt())

print(f"  Closing grippers...")
for i in range(300):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

# Stabilize
for _ in range(100):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

phase2_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase2_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase2_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase2_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase2_force_l = get_contact_force(contact_left)
phase2_force_r = get_contact_force(contact_right)
phase2_cable_z = get_cable_center_z()

print(f"  Force: L={phase2_force_l:.2f}N, R={phase2_force_r:.2f}N")
print(f"  Cable Z: {phase2_cable_z:.4f}")

# ============================================================
# PHASE 3: LIFT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 3: LIFT")
print("=" * 70)

lift_amount_m = LIFT_TARGET_CM / 100.0
target_phase3_left = phase2_ee_pos_left.clone()
target_phase3_left[0, 2] += lift_amount_m
target_phase3_right = phase2_ee_pos_right.clone()
target_phase3_right[0, 2] += lift_amount_m

start_ee_pos_left = phase2_ee_pos_left.clone()
start_ee_pos_right = phase2_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step_lift = None
consecutive_low = 0

for i in range(LIFT_NUM_STEPS):
    alpha = (i + 1) / LIFT_NUM_STEPS
    target_pos_left = start_ee_pos_left + alpha * (target_phase3_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase3_right - start_ee_pos_right)

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

    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)

    if force_l < 1.0 and force_r < 1.0:
        consecutive_low += 1
        if consecutive_low >= CONTACT_LOST_THRESHOLD and contact_lost_step_lift is None:
            contact_lost_step_lift = i
    else:
        consecutive_low = 0

    if i % 100 == 0 or i == LIFT_NUM_STEPS - 1:
        cable_z = get_cable_center_z()
        print(f"  Step {i}: Force L={force_l:.2f}N, R={force_r:.2f}N, Cable Z={cable_z:.4f}")

phase3_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase3_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase3_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase3_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase3_force_l = get_contact_force(contact_left)
phase3_force_r = get_contact_force(contact_right)
phase3_cable_z = get_cable_center_z()

cable_lift_cm = (phase3_cable_z - phase2_cable_z) * 100

print(f"\nPhase 3 Result:")
print(f"  Force: L={phase3_force_l:.2f}N, R={phase3_force_r:.2f}N")
print(f"  Cable Lift: {cable_lift_cm:.2f}cm")
print(f"  Contact: {'MAINTAINED' if contact_lost_step_lift is None else f'LOST at step {contact_lost_step_lift}'}")

# ============================================================
# PHASE 4: HOOK APPROACH
# ============================================================
print("\n" + "=" * 70)
print("PHASE 4: HOOK APPROACH")
print("=" * 70)

target_phase4_left = torch.tensor(
    [[WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)
target_phase4_right = torch.tensor(
    [[WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)

print(f"  Target Left:  {WAYPOINT_PHASE4_LEFT}")
print(f"  Target Right: {WAYPOINT_PHASE4_RIGHT}")

start_ee_pos_left = phase3_ee_pos_left.clone()
start_ee_pos_right = phase3_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step_phase4 = None
consecutive_low = 0
max_joint_change = 0.0
prev_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().copy()

for i in range(PHASE34_NUM_STEPS):
    alpha = (i + 1) / PHASE34_NUM_STEPS
    target_pos_left = start_ee_pos_left + alpha * (target_phase4_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase4_right - start_ee_pos_right)

    command_left = torch.cat([target_pos_left, phase3_ee_quat_left], dim=1)
    command_right = torch.cat([target_pos_right, phase3_ee_quat_right], dim=1)

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

    # Track joint change
    curr_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy()
    joint_change = np.max(np.abs(curr_joints_right - prev_joints_right)) * 180 / np.pi
    if joint_change > max_joint_change:
        max_joint_change = joint_change
    prev_joints_right = curr_joints_right.copy()

    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)

    if force_l < 1.0 and force_r < 1.0:
        consecutive_low += 1
        if consecutive_low >= CONTACT_LOST_THRESHOLD and contact_lost_step_phase4 is None:
            contact_lost_step_phase4 = i
    else:
        consecutive_low = 0

    if i % 100 == 0 or i == PHASE34_NUM_STEPS - 1:
        ee_l = get_ee_pos(robot_left, jacobian_body_left)
        ee_r = get_ee_pos(robot_right, jacobian_body_right)
        print(f"  Step {i}: L=({ee_l[0]:.3f},{ee_l[1]:.3f},{ee_l[2]:.3f}) R=({ee_r[0]:.3f},{ee_r[1]:.3f},{ee_r[2]:.3f}) Force={force_l:.1f}/{force_r:.1f}N")

phase4_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase4_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase4_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase4_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase4_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase4_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase4_force_l = get_contact_force(contact_left)
phase4_force_r = get_contact_force(contact_right)
phase4_cable_z = get_cable_center_z()

target_left_with_offset = np.array([WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET])
target_right_with_offset = np.array([WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET])
ee_error_left_4 = np.linalg.norm(phase4_ee_left - target_left_with_offset) * 100
ee_error_right_4 = np.linalg.norm(phase4_ee_right - target_right_with_offset) * 100

print(f"\nPhase 4 Result:")
print(f"  EE Error: L={ee_error_left_4:.2f}cm, R={ee_error_right_4:.2f}cm")
print(f"  Force: L={phase4_force_l:.2f}N, R={phase4_force_r:.2f}N")
print(f"  Max Joint Change/step: {max_joint_change:.2f}")
print(f"  Contact: {'MAINTAINED' if contact_lost_step_phase4 is None else f'LOST at step {contact_lost_step_phase4}'}")

# ============================================================
# PHASE 5: CABLE PLACEMENT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 5: CABLE PLACEMENT")
print("=" * 70)

target_phase5_left = torch.tensor(
    [[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)
target_phase5_right = torch.tensor(
    [[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)

print(f"  Target Left:  {WAYPOINT_PHASE5_LEFT}")
print(f"  Target Right: {WAYPOINT_PHASE5_RIGHT}")

start_ee_pos_left = phase4_ee_pos_left.clone()
start_ee_pos_right = phase4_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step_phase5 = None
consecutive_low = 0
max_joint_change_5 = 0.0
prev_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().copy()

for i in range(PHASE45_NUM_STEPS):
    alpha = (i + 1) / PHASE45_NUM_STEPS
    target_pos_left = start_ee_pos_left + alpha * (target_phase5_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase5_right - start_ee_pos_right)

    command_left = torch.cat([target_pos_left, phase4_ee_quat_left], dim=1)
    command_right = torch.cat([target_pos_right, phase4_ee_quat_right], dim=1)

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

    # Track joint change
    curr_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy()
    joint_change = np.max(np.abs(curr_joints_right - prev_joints_right)) * 180 / np.pi
    if joint_change > max_joint_change_5:
        max_joint_change_5 = joint_change
    prev_joints_right = curr_joints_right.copy()

    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)

    if force_l < 1.0 and force_r < 1.0:
        consecutive_low += 1
        if consecutive_low >= CONTACT_LOST_THRESHOLD and contact_lost_step_phase5 is None:
            contact_lost_step_phase5 = i
    else:
        consecutive_low = 0

    if i % 100 == 0 or i == PHASE45_NUM_STEPS - 1:
        ee_l = get_ee_pos(robot_left, jacobian_body_left)
        ee_r = get_ee_pos(robot_right, jacobian_body_right)
        print(f"  Step {i}: L=({ee_l[0]:.3f},{ee_l[1]:.3f},{ee_l[2]:.3f}) R=({ee_r[0]:.3f},{ee_r[1]:.3f},{ee_r[2]:.3f}) Force={force_l:.1f}/{force_r:.1f}N")

phase5_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase5_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase5_force_l = get_contact_force(contact_left)
phase5_force_r = get_contact_force(contact_right)
phase5_cable_z = get_cable_center_z()

target_left_phase5_offset = np.array([WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET])
target_right_phase5_offset = np.array([WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET])
ee_error_left_5 = np.linalg.norm(phase5_ee_left - target_left_phase5_offset) * 100
ee_error_right_5 = np.linalg.norm(phase5_ee_right - target_right_phase5_offset) * 100

print(f"\nPhase 5 Result:")
print(f"  EE Error: L={ee_error_left_5:.2f}cm, R={ee_error_right_5:.2f}cm")
print(f"  Force: L={phase5_force_l:.2f}N, R={phase5_force_r:.2f}N")
print(f"  Max Joint Change/step: {max_joint_change_5:.2f}")
print(f"  Contact: {'MAINTAINED' if contact_lost_step_phase5 is None else f'LOST at step {contact_lost_step_phase5}'}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

# Verification items
grasp_success = phase2_force_l > 5.0 and phase2_force_r > 5.0
lift_success = cable_lift_cm > 3.0  # Lower threshold since we're testing transition
phase4_success = ee_error_left_4 < 3.0 and ee_error_right_4 < 3.0
phase5_success = ee_error_left_5 < 3.0 and ee_error_right_5 < 3.0
contact_maintained = (contact_lost_step_lift is None and
                     contact_lost_step_phase4 is None and
                     contact_lost_step_phase5 is None)

print(f"\n1. Grasp (>5N):        {'PASS' if grasp_success else 'FAIL'} (L={phase2_force_l:.1f}N, R={phase2_force_r:.1f}N)")
print(f"2. Lift (>3cm):        {'PASS' if lift_success else 'FAIL'} ({cable_lift_cm:.1f}cm)")
print(f"3. Phase 4 EE (<3cm):  {'PASS' if phase4_success else 'FAIL'} (L={ee_error_left_4:.1f}cm, R={ee_error_right_4:.1f}cm)")
print(f"4. Phase 5 EE (<3cm):  {'PASS' if phase5_success else 'FAIL'} (L={ee_error_left_5:.1f}cm, R={ee_error_right_5:.1f}cm)")
print(f"5. Contact Maintained: {'PASS' if contact_maintained else 'FAIL'}")

# Hook proximity check
hook_center = np.array([0.25, 0.0, 0.90])
cable_center_y = (phase5_ee_left[1] + phase5_ee_right[1]) / 2
cable_center = np.array([phase5_ee_left[0], cable_center_y, phase5_ee_left[2]])
hook_distance = np.linalg.norm(cable_center[:2] - hook_center[:2]) * 100
print(f"6. Hook Proximity:     {hook_distance:.1f}cm (XY distance to hook)")

all_passed = grasp_success and lift_success and phase4_success and phase5_success and contact_maintained

print("\n" + "=" * 70)
if all_passed:
    print("SUCCESS: Phase 2->3->4->5 completed with V-groove high friction!")
else:
    print("FAIL: Some verification items did not pass")
print("=" * 70)

simulation_app.close()
