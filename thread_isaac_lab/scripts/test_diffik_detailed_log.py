#!/usr/bin/env python3
"""
Diff IK Lift Test with Detailed Logging
- Logs every step to identify contact loss timing
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

print("=" * 60)
print("DIFF IK LIFT - DETAILED TIMING ANALYSIS")
print("=" * 60)

# Parameters
GRIPPER_CLOSE = 0.003
FRICTION = 5.0

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
    use_relative_mode=True,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_center_z():
    z_vals = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    return np.nanmean(z_vals[8:12])  # seg_8 to seg_11 (center region)

# ============================================================
# PHASES 1-2: Setup (same as before)
# ============================================================
print("\nPhase 1-2: Setup...")

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
phase2_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
phase2_force = get_contact_force(contact_left)
phase2_cable_z = get_cable_center_z()

print(f"\n  Phase 2 Complete:")
print(f"    EE Z: {phase2_ee_z:.4f}")
print(f"    Contact Force: {phase2_force:.3f}N")
print(f"    Cable Center Z: {phase2_cable_z:.4f}")

# ============================================================
# PHASE 3: DETAILED LIFT LOGGING
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: DIFF IK LIFT - STEP BY STEP")
print("=" * 60)

diff_ik_left.reset()
diff_ik_right.reset()

command = torch.tensor([[0.0, 0.0, 0.15, 0.0, 0.0, 0.0]], device=device)

ee_pos_left_t = robot_left.data.body_pos_w[:, jacobian_body_left]
ee_quat_left_t = robot_left.data.body_quat_w[:, jacobian_body_left]
ee_pos_right_t = robot_right.data.body_pos_w[:, jacobian_body_right]
ee_quat_right_t = robot_right.data.body_quat_w[:, jacobian_body_right]

diff_ik_left.set_command(command, ee_pos_left_t, ee_quat_left_t)
diff_ik_right.set_command(command, ee_pos_right_t, ee_quat_right_t)

# Tracking variables
contact_lost_step = None
prev_force = phase2_force
force_drop_detected = False

print(f"\n  {'Step':>5} | {'EE Z':>7} | {'Lift':>7} | {'Force L':>8} | {'Force R':>8} | {'Cable Z':>8} | {'Status'}")
print("-" * 80)

for i in range(600):
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

    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = joint_cmd_left[0]
    target_left[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = joint_cmd_right[0]
    target_right[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    # Get current state
    ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)
    cable_z = get_cable_center_z()
    lift = (ee_z - phase2_ee_z) * 100  # cm

    # Detect contact loss
    status = "OK"
    if contact_lost_step is None and force_l < 1.0 and force_r < 1.0:
        contact_lost_step = i
        status = "*** LOST ***"
    elif contact_lost_step is not None:
        status = "lost"

    # Detect force drop (early warning)
    if not force_drop_detected and prev_force > 5.0 and force_l < 5.0:
        force_drop_detected = True
        print(f"  {'---':>5} | {'FORCE DROP DETECTED':^60}")

    # Log every 10 steps for first 100, then every 50
    log_interval = 10 if i < 100 else 50
    if i % log_interval == 0 or status == "*** LOST ***":
        print(f"  {i:>5} | {ee_z:>7.4f} | {lift:>6.2f}cm | {force_l:>7.3f}N | {force_r:>7.3f}N | {cable_z:>8.4f} | {status}")

    prev_force = force_l

# ============================================================
# ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)

final_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
final_cable_z = get_cable_center_z()

if contact_lost_step is not None:
    # Calculate state at contact loss
    lost_time = contact_lost_step / 240.0
    print(f"\n1. 接触喪失タイミング:")
    print(f"   Step: {contact_lost_step}")
    print(f"   Time: {lost_time:.3f}秒")

    # Rough estimate of EE Z at loss (linear interpolation)
    lift_rate = 0.15 / 600  # m per step (approximate)
    ee_z_at_loss = phase2_ee_z + contact_lost_step * lift_rate
    lift_at_loss = (ee_z_at_loss - phase2_ee_z) * 100

    print(f"\n2. 喪失時のEE状態:")
    print(f"   EE Z (推定): {ee_z_at_loss:.4f}")
    print(f"   リフト量: 約{lift_at_loss:.2f}cm")

    print(f"\n3. ケーブル状態:")
    print(f"   Phase 2 Cable Z: {phase2_cable_z:.4f}")
    print(f"   Final Cable Z: {final_cable_z:.4f}")
    if not np.isnan(final_cable_z):
        cable_drop = (phase2_cable_z - final_cable_z) * 100
        print(f"   落下量: {cable_drop:.2f}cm")

    print(f"\n4. 結論:")
    if contact_lost_step < 50:
        print(f"   → リフト直後（{lift_at_loss:.1f}cm時点）で接触喪失")
        print(f"   → Diff IKの加速度が高すぎる可能性")
    else:
        print(f"   → リフト途中（{lift_at_loss:.1f}cm時点）で接触喪失")
else:
    print("\n接触は維持されました！")
    print(f"Final EE Z: {final_ee_z:.4f}")
    print(f"Final Cable Z: {final_cable_z:.4f}")
    print(f"Total lift: {(final_ee_z - phase2_ee_z)*100:.2f}cm")

simulation_app.close()
