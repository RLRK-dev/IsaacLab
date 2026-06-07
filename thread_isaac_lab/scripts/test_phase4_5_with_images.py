#!/usr/bin/env python3
"""
Phase 4-5 Test with Image Capture

Captures camera images at:
- Phase 2 end (grasp)
- Phase 3 end (lift)
- Phase 4 end (hook approach)
- Phase 5 end (cable placement)

Images saved to: /tmp/phase4_5_images/
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
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
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    GRIPPER_CLOSE, GRIPPER_OPEN,
)

# Output directory
OUTPUT_DIR = "/tmp/phase4_5_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("PHASE 4-5 TEST WITH IMAGE CAPTURE")
print(f"Images will be saved to: {OUTPUT_DIR}")
print("=" * 70)

# High friction settings
HIGH_FRICTION = 5.0

# Parameters
LIFT_NUM_STEPS = 300
PHASE34_NUM_STEPS = 500
PHASE45_NUM_STEPS = 400
Z_OFFSET = 0.1034
LIFT_TARGET_CM = 5.0
CONTACT_LOST_THRESHOLD = 10

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

# Get cameras
front_left_cam = scene["front_left_camera"]
front_right_cam = scene["front_right_camera"]
back_cam = scene["back_camera"]
overhead_cam = scene["overhead_camera"]

device = robot_left.device

# Apply HIGH FRICTION
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

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

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

def save_camera_images(phase_name):
    """Save images from all 4 cameras"""
    # Update cameras
    front_left_cam.update(sim.get_physics_dt())
    front_right_cam.update(sim.get_physics_dt())
    back_cam.update(sim.get_physics_dt())
    overhead_cam.update(sim.get_physics_dt())

    cameras = [
        ("front_left", front_left_cam),
        ("front_right", front_right_cam),
        ("back", back_cam),
        ("overhead", overhead_cam),
    ]

    for cam_name, cam in cameras:
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        # RGB is RGBA, convert to RGB
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        img = Image.fromarray(rgb.astype(np.uint8))
        filepath = os.path.join(OUTPUT_DIR, f"{phase_name}_{cam_name}.png")
        img.save(filepath)
        print(f"  Saved: {filepath}")

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

for i in range(300):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

for _ in range(100):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

phase2_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase2_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase2_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase2_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

print("\nSaving Phase 2 images...")
save_camera_images("phase2_grasp")

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

phase3_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase3_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase3_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase3_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

print("\nSaving Phase 3 images...")
save_camera_images("phase3_lift")

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

start_ee_pos_left = phase3_ee_pos_left.clone()
start_ee_pos_right = phase3_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

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

phase4_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase4_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase4_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase4_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase4_force_l = get_contact_force(contact_left)
phase4_force_r = get_contact_force(contact_right)

phase4_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase4_ee_right = get_ee_pos(robot_right, jacobian_body_right)

print(f"\nPhase 4 End State:")
print(f"  EE Left:  ({phase4_ee_left[0]:.3f}, {phase4_ee_left[1]:.3f}, {phase4_ee_left[2]:.3f})")
print(f"  EE Right: ({phase4_ee_right[0]:.3f}, {phase4_ee_right[1]:.3f}, {phase4_ee_right[2]:.3f})")
print(f"  Force: L={phase4_force_l:.2f}N, R={phase4_force_r:.2f}N")

print("\nSaving Phase 4 images...")
save_camera_images("phase4_hook_approach")

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

start_ee_pos_left = phase4_ee_pos_left.clone()
start_ee_pos_right = phase4_ee_pos_right.clone()

diff_ik_left.reset()
diff_ik_right.reset()

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

phase5_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase5_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase5_force_l = get_contact_force(contact_left)
phase5_force_r = get_contact_force(contact_right)

print(f"\nPhase 5 End State:")
print(f"  EE Left:  ({phase5_ee_left[0]:.3f}, {phase5_ee_left[1]:.3f}, {phase5_ee_left[2]:.3f})")
print(f"  EE Right: ({phase5_ee_right[0]:.3f}, {phase5_ee_right[1]:.3f}, {phase5_ee_right[2]:.3f})")
print(f"  Force: L={phase5_force_l:.2f}N, R={phase5_force_r:.2f}N")

print("\nSaving Phase 5 images...")
save_camera_images("phase5_placement")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("IMAGE CAPTURE COMPLETE")
print("=" * 70)
print(f"\nImages saved to: {OUTPUT_DIR}")
print("\nFiles:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  - {f}")

# Calculate hook proximity
hook_center = np.array([0.25, 0.0])
cable_center_y = (phase5_ee_left[1] + phase5_ee_right[1]) / 2
cable_center_xy = np.array([phase5_ee_left[0], cable_center_y])
hook_distance = np.linalg.norm(cable_center_xy - hook_center) * 100

print(f"\nHook proximity (XY): {hook_distance:.1f}cm")
print(f"Hook position: (0.25, 0.0, {0.75 + 0.11})")  # stem + arm height
print(f"Cable center: ({phase5_ee_left[0]:.3f}, {cable_center_y:.3f})")

simulation_app.close()
