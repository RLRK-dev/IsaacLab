#!/usr/bin/env python3
"""
Corrected Diff IK Lift Test
- Uses proper coordinate transformation: World Z+0.15m → Base frame (-0.15, 0, 0)
- Both robots use same quaternion, so same delta
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
print("WORLD COORDINATE DIFF IK LIFT TEST")
print("Direct world Z+0.15m command")
print("=" * 60)

# Parameters
GRIPPER_CLOSE = 0.003
FRICTION = 5.0
LIFT_DELTA_WORLD = torch.tensor([[0.0, 0.0, 0.15]])  # World Z+15cm directly

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

# Setup Diff IK controllers
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=True,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

# Jacobian body indices
jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, jacobian_body_idx):
    """Get end-effector position in world frame"""
    return robot.data.body_pos_w[0, jacobian_body_idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_z():
    return cable.data.body_pos_w[0, :, 2].cpu().numpy().mean()

# ============================================================
# PHASE 1: OPEN GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 1: OPEN GRIPPERS")
print("=" * 60)

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

# ============================================================
# PHASE 2A: TELEPORT TO GRASP POSITION
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2A: TELEPORT TO GRASP POSITION")
print("=" * 60)

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

# ============================================================
# PHASE 2B: CLOSE GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2B: CLOSE GRIPPERS")
print("=" * 60)

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
ee_left_phase2 = get_ee_pos(robot_left, jacobian_body_left)
ee_right_phase2 = get_ee_pos(robot_right, jacobian_body_right)
force_left_phase2 = get_contact_force(contact_left)
force_right_phase2 = get_contact_force(contact_right)
cable_z_phase2 = get_cable_z()

print(f"\n  Phase 2 State:")
print(f"    EE Left:  ({ee_left_phase2[0]:.4f}, {ee_left_phase2[1]:.4f}, {ee_left_phase2[2]:.4f})")
print(f"    EE Right: ({ee_right_phase2[0]:.4f}, {ee_right_phase2[1]:.4f}, {ee_right_phase2[2]:.4f})")
print(f"    Contact Force: L={force_left_phase2:.4f}N, R={force_right_phase2:.4f}N")
print(f"    Cable Z: {cable_z_phase2:.4f}")

# ============================================================
# PHASE 3: DIFF IK LIFT (CORRECTED COORDINATES)
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: DIFF IK LIFT (WORLD COORDINATES)")
print(f"  Delta in world frame: {LIFT_DELTA_WORLD[0].tolist()}")
print(f"  Expected: X/Y維持, Z+15cm")
print("=" * 60)

# Reset IK controllers
diff_ik_left.reset()
diff_ik_right.reset()

# Command format for relative pose: [dx, dy, dz, droll, dpitch, dyaw] - 6 elements
# World Z+15cm, no rotation change
command = torch.tensor([[0.0, 0.0, 0.15, 0.0, 0.0, 0.0]], device=device)

# Get current EE poses for set_command (required for relative mode)
ee_pos_left_t = robot_left.data.body_pos_w[:, jacobian_body_left]
ee_quat_left_t = robot_left.data.body_quat_w[:, jacobian_body_left]
ee_pos_right_t = robot_right.data.body_pos_w[:, jacobian_body_right]
ee_quat_right_t = robot_right.data.body_quat_w[:, jacobian_body_right]

diff_ik_left.set_command(command, ee_pos_left_t, ee_quat_left_t)
diff_ik_right.set_command(command, ee_pos_right_t, ee_quat_right_t)

print(f"\n  IK Command (world frame): {command[0, :3].tolist()}")

for i in range(600):
    # Get current states
    jacobian_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jacobian_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

    ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right]

    joint_pos_left = robot_left.data.joint_pos[:, :7]
    joint_pos_right = robot_right.data.joint_pos[:, :7]

    # Compute IK
    joint_cmd_left = diff_ik_left.compute(ee_pos_left, ee_quat_left, jacobian_left, joint_pos_left)
    joint_cmd_right = diff_ik_right.compute(ee_pos_right, ee_quat_right, jacobian_right, joint_pos_right)

    # Apply commands (arm joints only, keep gripper closed)
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

    if (i+1) % 200 == 0:
        ee_left = get_ee_pos(robot_left, jacobian_body_left)
        ee_right = get_ee_pos(robot_right, jacobian_body_right)
        force_l = get_contact_force(contact_left)
        force_r = get_contact_force(contact_right)
        cable_z = get_cable_z()
        print(f"  Step {i+1}/600:")
        print(f"    EE Left:  ({ee_left[0]:.4f}, {ee_left[1]:.4f}, {ee_left[2]:.4f})")
        print(f"    EE Right: ({ee_right[0]:.4f}, {ee_right[1]:.4f}, {ee_right[2]:.4f})")
        print(f"    Contact: L={force_l:.3f}N, R={force_r:.3f}N, Cable Z={cable_z:.4f}")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

ee_left_phase3 = get_ee_pos(robot_left, jacobian_body_left)
ee_right_phase3 = get_ee_pos(robot_right, jacobian_body_right)
force_left_phase3 = get_contact_force(contact_left)
force_right_phase3 = get_contact_force(contact_right)
cable_z_phase3 = get_cable_z()

delta_left = ee_left_phase3 - ee_left_phase2
delta_right = ee_right_phase3 - ee_right_phase2

print(f"\n1. Phase 3後のEE位置:")
print(f"   Left:  ({ee_left_phase3[0]:.4f}, {ee_left_phase3[1]:.4f}, {ee_left_phase3[2]:.4f})")
print(f"   Right: ({ee_right_phase3[0]:.4f}, {ee_right_phase3[1]:.4f}, {ee_right_phase3[2]:.4f})")

print(f"\n2. Phase 2→3のΔ (ワールド座標):")
print(f"   Left:  ΔX={delta_left[0]*100:.2f}cm, ΔY={delta_left[1]*100:.2f}cm, ΔZ={delta_left[2]*100:.2f}cm")
print(f"   Right: ΔX={delta_right[0]*100:.2f}cm, ΔY={delta_right[1]*100:.2f}cm, ΔZ={delta_right[2]*100:.2f}cm")

print(f"\n3. 接触力:")
print(f"   Phase 2: L={force_left_phase2:.4f}N, R={force_right_phase2:.4f}N")
print(f"   Phase 3: L={force_left_phase3:.4f}N, R={force_right_phase3:.4f}N")
print(f"   維持: {'✅' if force_left_phase3 > 1.0 and force_right_phase3 > 1.0 else '❌'}")

print(f"\n4. ケーブルZ:")
print(f"   Phase 2: {cable_z_phase2:.4f}")
print(f"   Phase 3: {cable_z_phase3:.4f}")
print(f"   上昇量: {(cable_z_phase3 - cable_z_phase2)*100:.2f}cm")

print("\n" + "=" * 60)
print("SUMMARY TABLE")
print("=" * 60)
print(f"| 項目 | Phase 2 | Phase 3 | Δ |")
print(f"|------|---------|---------|-----|")
print(f"| EE Left X | {ee_left_phase2[0]:.4f} | {ee_left_phase3[0]:.4f} | {delta_left[0]*100:+.2f}cm |")
print(f"| EE Left Y | {ee_left_phase2[1]:.4f} | {ee_left_phase3[1]:.4f} | {delta_left[1]*100:+.2f}cm |")
print(f"| EE Left Z | {ee_left_phase2[2]:.4f} | {ee_left_phase3[2]:.4f} | {delta_left[2]*100:+.2f}cm |")
print(f"| EE Right X | {ee_right_phase2[0]:.4f} | {ee_right_phase3[0]:.4f} | {delta_right[0]*100:+.2f}cm |")
print(f"| EE Right Y | {ee_right_phase2[1]:.4f} | {ee_right_phase3[1]:.4f} | {delta_right[1]*100:+.2f}cm |")
print(f"| EE Right Z | {ee_right_phase2[2]:.4f} | {ee_right_phase3[2]:.4f} | {delta_right[2]*100:+.2f}cm |")
print(f"| Contact L | {force_left_phase2:.2f}N | {force_left_phase3:.2f}N | - |")
print(f"| Contact R | {force_right_phase2:.2f}N | {force_right_phase3:.2f}N | - |")
print(f"| Cable Z | {cable_z_phase2:.4f} | {cable_z_phase3:.4f} | {(cable_z_phase3-cable_z_phase2)*100:+.2f}cm |")

simulation_app.close()
