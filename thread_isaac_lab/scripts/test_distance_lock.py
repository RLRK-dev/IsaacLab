#!/usr/bin/env python3
"""
Distance Lock Lift Test
- Maintain gripper distance at 57cm during lift
- Apply Y-axis correction when grippers move inward
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
from thread_isaac_lab.configs.task_config import PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS

print("=" * 80)
print("DISTANCE LOCK LIFT TEST")
print("=" * 80)

# Parameters
GRIPPER_CLOSE = 0.001
FRICTION = 5.0
LIFT_TOTAL = 0.15
NUM_STEPS = 600
LIFT_PER_STEP = LIFT_TOTAL / NUM_STEPS
TARGET_DISTANCE = 0.57  # 57cm - maintain this
DISTANCE_TOLERANCE = 0.005  # 5mm tolerance

print(f"Target gripper distance: {TARGET_DISTANCE*100:.1f}cm")
print(f"Distance tolerance: {DISTANCE_TOLERANCE*1000:.1f}mm")

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

# Setup Diff IK
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.05},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_gripper_distance():
    pos_l = get_ee_pos(robot_left, jacobian_body_left)
    pos_r = get_ee_pos(robot_right, jacobian_body_right)
    return np.linalg.norm(pos_l - pos_r)

def get_gripper_y_positions():
    pos_l = get_ee_pos(robot_left, jacobian_body_left)
    pos_r = get_ee_pos(robot_right, jacobian_body_right)
    return pos_l[1], pos_r[1]

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
phase2_dist = get_gripper_distance()
phase2_y_l, phase2_y_r = get_gripper_y_positions()

print(f"\n" + "=" * 80)
print("PHASE 2 COMPLETE")
print("=" * 80)
print(f"  EE Z: {phase2_ee_z:.4f}")
print(f"  Contact Force: L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"  Gripper Distance: {phase2_dist*100:.2f}cm (target: {TARGET_DISTANCE*100:.1f}cm)")
print(f"  Gripper Y: L={phase2_y_l:.4f}, R={phase2_y_r:.4f}")

# ============================================================
# PHASE 3: LIFT WITH DISTANCE LOCK
# ============================================================
print(f"\n" + "=" * 80)
print("PHASE 3: DISTANCE-LOCKED LIFT")
print(f"  Lift per step: {LIFT_PER_STEP*1000:.3f}mm")
print(f"  Target distance: {TARGET_DISTANCE*100:.1f}cm")
print("=" * 80)

# Initialize target positions
target_pos_left = phase2_ee_pos_left.clone()
target_pos_right = phase2_ee_pos_right.clone()

# Lock initial Y positions (as tensors)
locked_y_left = torch.tensor(phase2_y_l, device=device)
locked_y_right = torch.tensor(phase2_y_r, device=device)

diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step = None
corrections_applied = 0

# Header
print(f"\n{'Step':>5} | {'EE Z':>6} | {'Lift':>5} | {'F_L':>5} | {'F_R':>5} | {'Dist':>6} | {'dDist':>6} | {'Corr':>5} | Status")
print("-" * 95)

for i in range(NUM_STEPS):
    # Get current gripper distance
    current_dist = get_gripper_distance()
    current_y_l, current_y_r = get_gripper_y_positions()

    # Calculate distance error
    dist_error = TARGET_DISTANCE - current_dist

    # Apply Y correction if distance is shrinking
    if dist_error > DISTANCE_TOLERANCE:
        # Grippers too close - push them apart
        correction = dist_error / 2
        corrections_applied += 1

        # Update target Y positions to push apart
        # Left gripper is at negative Y, right at positive Y
        target_pos_left[0, 1] = locked_y_left - torch.tensor(correction, device=device)
        target_pos_right[0, 1] = locked_y_right + torch.tensor(correction, device=device)
    else:
        # Maintain locked Y positions
        target_pos_left[0, 1] = locked_y_left.clone()
        target_pos_right[0, 1] = locked_y_right.clone()

    # Update Z position (lift)
    target_pos_left[0, 2] += LIFT_PER_STEP
    target_pos_right[0, 2] += LIFT_PER_STEP

    # Command with locked orientation
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
    lift = (ee_z - phase2_ee_z) * 100
    d_dist = (current_dist - phase2_dist) * 100  # cm change

    # Detect contact loss
    status = "OK"
    if contact_lost_step is None and force_l < 1.0 and force_r < 1.0:
        contact_lost_step = i
        status = "*** LOST ***"
    elif contact_lost_step is not None:
        status = "lost"

    # Log every 20 steps or on contact loss
    if i % 20 == 0 or status == "*** LOST ***" or i == NUM_STEPS - 1:
        corr_str = f"{corrections_applied:>4}" if dist_error > DISTANCE_TOLERANCE else "   -"
        print(f"{i:>5} | {ee_z:>6.4f} | {lift:>4.1f}cm | {force_l:>4.0f}N | {force_r:>4.0f}N | {current_dist*100:>5.1f}cm | {d_dist:>+5.2f}cm | {corr_str} | {status}")

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

print(f"\n  Total corrections applied: {corrections_applied}")
print(f"  Gripper Distance: {phase2_dist*100:.2f}cm -> {final_dist*100:.2f}cm")

if contact_lost_step is not None:
    lost_lift = contact_lost_step * LIFT_PER_STEP * 100
    print(f"\n  Contact Lost at Step {contact_lost_step}")
    print(f"  Lift at loss: {lost_lift:.2f}cm")
    print(f"  Previous best: 4.4cm")
    if lost_lift > 4.4:
        print(f"  Improvement: {lost_lift/4.4*100:.0f}%")
else:
    actual_lift = (final_ee_z - phase2_ee_z) * 100
    print(f"\n  SUCCESS: Contact maintained!")
    print(f"  Final lift: {actual_lift:.2f}cm")
    print(f"  Contact Force: L={final_force_l:.1f}N, R={final_force_r:.1f}N")

simulation_app.close()
