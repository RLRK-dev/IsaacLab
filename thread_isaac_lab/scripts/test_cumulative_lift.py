#!/usr/bin/env python3
"""
Cumulative Lift Test - Fixed Diff IK approach
- Don't reset each step
- Use absolute position mode OR cumulative delta
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
    FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION,
    CABLE_STATIC_FRICTION, CABLE_DYNAMIC_FRICTION,
    GRIPPER_CLOSE,
)

print("=" * 60)
print("CUMULATIVE LIFT TEST (FIXED)")
print("Using absolute position mode")
print("=" * 60)

# Parameters - using task_config.py values
# GRIPPER_CLOSE imported from task_config.py (0.002)
# FRICTION imported from task_config.py
LIFT_TOTAL = 0.15  # 15cm total lift
NUM_STEPS = 300
LIFT_PER_STEP = LIFT_TOTAL / NUM_STEPS  # 0.5mm per step

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

# Apply high friction for V-groove test
HIGH_FRICTION = 5.0
print(f"\nApplying high friction: {HIGH_FRICTION}...")
def set_friction(asset, static_friction, dynamic_friction):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = static_friction
    materials[..., 1] = dynamic_friction
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)

# Setup Diff IK with ABSOLUTE position mode (not relative)
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,  # Use absolute position
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_ee_quat(robot, idx):
    return robot.data.body_quat_w[0, idx]

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_center_z():
    z_vals = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    valid = z_vals[~np.isnan(z_vals)]
    if len(valid) > 0:
        return np.mean(valid[len(valid)//3:2*len(valid)//3])
    return float('nan')

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
phase2_cable_z = get_cable_center_z()

print(f"\n" + "=" * 60)
print("PHASE 2 COMPLETE")
print("=" * 60)
print(f"  EE Z: {phase2_ee_z:.4f}")
print(f"  Contact Force: L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"  Cable Z: {phase2_cable_z:.4f}")

# ============================================================
# PHASE 3: CUMULATIVE LIFT WITH ABSOLUTE POSITION
# ============================================================
print(f"\n" + "=" * 60)
print("PHASE 3: CUMULATIVE LIFT (ABSOLUTE POSITION MODE)")
print(f"  Lift per step: {LIFT_PER_STEP*1000:.2f}mm")
print(f"  Total steps: {NUM_STEPS}")
print(f"  Total lift: {LIFT_TOTAL*100:.1f}cm")
print("=" * 60)

# Initialize target positions (start from Phase 2 positions)
target_pos_left = phase2_ee_pos_left.clone()
target_pos_right = phase2_ee_pos_right.clone()

# Reset controllers once at the beginning
diff_ik_left.reset()
diff_ik_right.reset()

contact_lost_step = None

print(f"\n  {'Step':>5} | {'Target Z':>8} | {'EE Z':>7} | {'Lift':>7} | {'Force L':>8} | {'Force R':>8} | {'Cable Z':>8} | Status")
print("-" * 100)

for i in range(NUM_STEPS):
    # Update target Z position (cumulative)
    target_pos_left[0, 2] += LIFT_PER_STEP
    target_pos_right[0, 2] += LIFT_PER_STEP

    # Create command: [x, y, z, qw, qx, qy, qz] for absolute mode
    command_left = torch.cat([target_pos_left, phase2_ee_quat_left], dim=1)
    command_right = torch.cat([target_pos_right, phase2_ee_quat_right], dim=1)

    # Set command (no reset, just update target)
    diff_ik_left.set_command(command_left)
    diff_ik_right.set_command(command_right)

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

    # Get current state
    ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)
    cable_z = get_cable_center_z()
    lift = (ee_z - phase2_ee_z) * 100
    target_z = target_pos_left[0, 2].item()

    # Detect contact loss
    status = "OK"
    if contact_lost_step is None and force_l < 1.0 and force_r < 1.0:
        contact_lost_step = i
        status = "*** LOST ***"
    elif contact_lost_step is not None:
        status = "lost"

    # Log every 20 steps or on contact loss
    if i % 20 == 0 or status == "*** LOST ***" or i == NUM_STEPS - 1:
        print(f"  {i:>5} | {target_z:>8.4f} | {ee_z:>7.4f} | {lift:>6.2f}cm | {force_l:>7.3f}N | {force_r:>7.3f}N | {cable_z:>8.4f} | {status}")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

final_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
final_force_l = get_contact_force(contact_left)
final_force_r = get_contact_force(contact_right)
final_cable_z = get_cable_center_z()

actual_lift = (final_ee_z - phase2_ee_z) * 100
expected_lift = LIFT_TOTAL * 100

print(f"\n1. リフト量:")
print(f"   期待値: {expected_lift:.1f}cm")
print(f"   実際値: {actual_lift:.2f}cm")
print(f"   達成率: {actual_lift/expected_lift*100:.1f}%")

print(f"\n2. 接触力:")
print(f"   Phase 2: L={phase2_force_l:.3f}N, R={phase2_force_r:.3f}N")
print(f"   Final:   L={final_force_l:.3f}N, R={final_force_r:.3f}N")
if contact_lost_step is not None:
    lost_lift = contact_lost_step * LIFT_PER_STEP * 100
    print(f"   喪失: Step {contact_lost_step} (リフト{lost_lift:.2f}cm時点)")
else:
    print(f"   維持: ✅ 全ステップで接触維持！")

print(f"\n3. ケーブルZ:")
print(f"   Phase 2: {phase2_cable_z:.4f}")
print(f"   Final:   {final_cable_z:.4f}")
if not np.isnan(final_cable_z) and not np.isnan(phase2_cable_z):
    cable_lift = (final_cable_z - phase2_cable_z) * 100
    print(f"   上昇量: {cable_lift:.2f}cm")

print("\n" + "=" * 60)
if contact_lost_step is None and actual_lift > 10:
    print(f"✅ SUCCESS: 接触維持しながら{actual_lift:.1f}cmリフト完了！")
elif contact_lost_step is None:
    print(f"⚠️ PARTIAL: 接触維持、リフト{actual_lift:.1f}cm（目標未達）")
else:
    print(f"❌ FAILED: Step {contact_lost_step}で接触喪失")
print("=" * 60)

simulation_app.close()
