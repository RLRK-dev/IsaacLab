#!/usr/bin/env python3
"""
Orientation Lock Lift Test
- Explicitly maintain gripper orientation during lift
- Monitor orientation error
- Slower lift rate for better tracking
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
from isaaclab.utils.math import compute_pose_error
from scipy.spatial.transform import Rotation as R

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS

print("=" * 80)
print("ORIENTATION LOCK LIFT TEST")
print("=" * 80)

# Parameters
GRIPPER_CLOSE = 0.001
FRICTION = 5.0
LIFT_TOTAL = 0.15
NUM_STEPS = 600  # Slower: twice as many steps
LIFT_PER_STEP = LIFT_TOTAL / NUM_STEPS  # 0.25mm per step (half of before)

print(f"Lift speed: {LIFT_PER_STEP*1000:.3f}mm/step = {LIFT_PER_STEP*240*1000:.1f}mm/s (half of previous)")

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
def set_friction(asset, value):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = value
    materials[..., 1] = value
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FRICTION)
set_friction(robot_right, FRICTION)
set_friction(cable, FRICTION)

# Setup Diff IK with lower lambda for better tracking
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.05},  # Lower lambda = more aggressive tracking
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def quat_to_euler(quat_wxyz):
    q = quat_wxyz.cpu().numpy()
    r = R.from_quat([q[1], q[2], q[3], q[0]])
    return r.as_euler('xyz', degrees=True)

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_gripper_distance():
    pos_l = get_ee_pos(robot_left, jacobian_body_left)
    pos_r = get_ee_pos(robot_right, jacobian_body_right)
    return np.linalg.norm(pos_l - pos_r)

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

# Record Phase 2 state - LOCK these orientations
phase2_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase2_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase2_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase2_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

phase2_ee_z = phase2_ee_pos_left[0, 2].item()
phase2_force_l = get_contact_force(contact_left)
phase2_force_r = get_contact_force(contact_right)
phase2_dist = get_gripper_distance()

# Get initial orientation for reference
euler_init_l = quat_to_euler(phase2_ee_quat_left[0])
euler_init_r = quat_to_euler(phase2_ee_quat_right[0])

print(f"\n" + "=" * 80)
print("PHASE 2 COMPLETE")
print("=" * 80)
print(f"  EE Z: {phase2_ee_z:.4f}")
print(f"  Contact Force: L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"  Gripper Distance: {phase2_dist*100:.2f}cm")
print(f"  Locked Orientation L (RPY): [{euler_init_l[0]:+.1f}, {euler_init_l[1]:+.1f}, {euler_init_l[2]:+.1f}]")
print(f"  Locked Orientation R (RPY): [{euler_init_r[0]:+.1f}, {euler_init_r[1]:+.1f}, {euler_init_r[2]:+.1f}]")

# ============================================================
# PHASE 3: LIFT WITH ORIENTATION LOCK
# ============================================================
print(f"\n" + "=" * 80)
print("PHASE 3: ORIENTATION-LOCKED LIFT")
print(f"  Lift per step: {LIFT_PER_STEP*1000:.3f}mm (half speed)")
print(f"  lambda_val: 0.05 (lower = more aggressive)")
print("=" * 80)

target_pos_left = phase2_ee_pos_left.clone()
target_pos_right = phase2_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step = None

# Header
print(f"\n{'Step':>5} | {'EE Z':>6} | {'Lift':>5} | {'F_L':>5} | {'F_R':>5} | {'Dist':>6} | {'dRoll':>6} | {'dPitch':>7} | {'PosErr':>7} | {'OriErr':>7} | Status")
print("-" * 115)

for i in range(NUM_STEPS):
    # Update target position ONLY (orientation stays locked to phase2)
    target_pos_left[0, 2] += LIFT_PER_STEP
    target_pos_right[0, 2] += LIFT_PER_STEP

    # Command with LOCKED orientation (phase2 quaternion)
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
    lift = (ee_z - phase2_ee_z) * 100

    # Get current orientation and compute error from locked orientation
    current_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left]
    current_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]

    # Compute pose error (position and orientation)
    pos_err, ori_err = compute_pose_error(
        current_pos_l, current_quat_l,
        target_pos_left, phase2_ee_quat_left,
        rot_error_type="axis_angle"
    )
    pos_err_norm = torch.norm(pos_err).item() * 1000  # mm
    ori_err_norm = torch.norm(ori_err).item() * 180 / np.pi  # degrees

    # Current orientation
    euler_l = quat_to_euler(current_quat_l[0])
    droll = euler_l[0] - euler_init_l[0]
    dpitch = euler_l[1] - euler_init_l[1]

    # Detect contact loss
    status = "OK"
    if contact_lost_step is None and force_l < 1.0 and force_r < 1.0:
        contact_lost_step = i
        status = "*** LOST ***"
    elif contact_lost_step is not None:
        status = "lost"

    # Log every 20 steps or on contact loss
    if i % 20 == 0 or status == "*** LOST ***" or i == NUM_STEPS - 1:
        print(f"{i:>5} | {ee_z:>6.4f} | {lift:>4.1f}cm | {force_l:>4.0f}N | {force_r:>4.0f}N | {gripper_dist*100:>5.1f}cm | {droll:>+5.1f}° | {dpitch:>+6.1f}° | {pos_err_norm:>6.1f}mm | {ori_err_norm:>6.2f}° | {status}")

    # Early exit
    if contact_lost_step is not None and i > contact_lost_step + 30:
        print(f"\n  [Early exit: Contact lost at step {contact_lost_step}]")
        break

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

final_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
final_force_l = get_contact_force(contact_left)
final_force_r = get_contact_force(contact_right)
final_dist = get_gripper_distance()

if contact_lost_step is not None:
    lost_lift = contact_lost_step * LIFT_PER_STEP * 100
    print(f"\n  Contact Lost at Step {contact_lost_step}")
    print(f"  Lift at loss: {lost_lift:.2f}cm")
    print(f"  Improvement over previous: 4.2cm -> {lost_lift:.2f}cm = {lost_lift/4.2*100:.0f}%")
else:
    actual_lift = (final_ee_z - phase2_ee_z) * 100
    print(f"\n  SUCCESS: Contact maintained!")
    print(f"  Final lift: {actual_lift:.2f}cm")

print(f"\n  Gripper Distance: {phase2_dist*100:.2f}cm -> {final_dist*100:.2f}cm")
print(f"  Contact Force: L={final_force_l:.1f}N, R={final_force_r:.1f}N")

simulation_app.close()
