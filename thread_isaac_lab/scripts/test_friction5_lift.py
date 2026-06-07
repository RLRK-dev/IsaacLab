#!/usr/bin/env python3
"""
Friction 5.0 Lift Test
- Apply friction=5.0 to gripper fingers and cable at runtime
- Use v9_mid cable (cone=30°, damping=20.0)
- GRIPPER_CLOSE = 0.003 (Gap≈6mm)
- Measure contact force and lift height
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
import omni.usd
from pxr import UsdShade, UsdPhysics, Sdf
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.utils import configclass

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    CABLE_Z, CABLE_RADIUS
)

print("=" * 60)
print("FRICTION 5.0 LIFT TEST")
print("=" * 60)

# Parameters
FRICTION = 5.0
GRASP_JOINT_POS = 0.003  # Gap=6mm (T1 test - tighter grip)
TARGET_GAP_MM = 6.0

# Setup simulation
sim_cfg = sim_utils.SimulationCfg(
    dt=1/240,
    render_interval=1,
    physics_material=sim_utils.RigidBodyMaterialCfg(
        static_friction=1.0,
        dynamic_friction=1.0,
        restitution=0.0,
    ),
)
sim = sim_utils.SimulationContext(sim_cfg)

# DualArmSceneCfg already uses v9_mid cable by default
@configclass
class FrictionTestSceneCfg(DualArmSceneCfg):
    """Scene with contact sensors (v9_mid cable is default)"""

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

scene_cfg = FrictionTestSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
contact_left = scene["contact_left"]
contact_right = scene["contact_right"]

device = robot_left.device

# ============================================================
# APPLY FRICTION=5.0 AT RUNTIME
# ============================================================
print("\n" + "=" * 60)
print(f"APPLYING FRICTION={FRICTION} AT RUNTIME")
print("=" * 60)

stage = omni.usd.get_context().get_stage()

# Create high friction material
mat_path = "/World/HighFrictionMaterial"
mat_prim = stage.DefinePrim(mat_path, "Material")
phys_material = UsdPhysics.MaterialAPI.Apply(mat_prim)
phys_material.CreateStaticFrictionAttr(FRICTION)
phys_material.CreateDynamicFrictionAttr(FRICTION)
phys_material.CreateRestitutionAttr(0.0)

material = UsdShade.Material(mat_prim)

# Apply to gripper fingers
finger_paths = [
    "/World/envs/env_0/Robot_Left/panda_leftfinger",
    "/World/envs/env_0/Robot_Left/panda_rightfinger",
    "/World/envs/env_0/Robot_Right/panda_leftfinger",
    "/World/envs/env_0/Robot_Right/panda_rightfinger",
]

for path in finger_paths:
    prim = stage.GetPrimAtPath(path)
    if prim.IsValid():
        binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
        binding_api.Bind(material, UsdShade.Tokens.weakerThanDescendants, "physics")
        print(f"  Applied friction to: {path}")

# Apply to cable segments
cable_applied = 0
for i in range(40):  # Check up to 40 segments
    seg_path = f"/World/envs/env_0/Cable/seg_{i}"
    prim = stage.GetPrimAtPath(seg_path)
    if prim.IsValid():
        binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
        binding_api.Bind(material, UsdShade.Tokens.weakerThanDescendants, "physics")
        cable_applied += 1

print(f"  Applied friction to {cable_applied} cable segments")

def get_gripper_state(robot, name):
    pos = robot.data.joint_pos[0, -2:].cpu().numpy()
    return f"{name}: gap={sum(pos)*1000:.2f}mm"

def get_cable_z():
    cable_pos = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    return np.nanmean(cable_pos), np.nanmin(cable_pos), np.nanmax(cable_pos)

def get_contact_forces():
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

print(f"\nFriction: {FRICTION}")
print(f"Target gap: {TARGET_GAP_MM}mm")
initial_cable_z = get_cable_z()[0]
print(f"Initial cable Z: {initial_cable_z:.4f}")

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
print(f"  Cable Z: {get_cable_z()[0]:.4f}")

# ============================================================
# PHASE 2B: CLOSE GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print(f"PHASE 2B: CLOSE GRIPPERS (target gap={TARGET_GAP_MM}mm)")
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
        print(f"  Step {i+1}/300: L={sum(left_pos)*1000:.2f}mm, R={sum(right_pos)*1000:.2f}mm, Force L={forces['left_mag']:.3f}N R={forces['right_mag']:.3f}N")

# Record grasp state
grasp_cable_z = get_cable_z()[0]
grasp_forces = get_contact_forces()
left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()

print(f"\n  After grasp:")
print(f"    Gap: L={sum(left_pos)*1000:.2f}mm, R={sum(right_pos)*1000:.2f}mm")
print(f"    Contact force: L={grasp_forces['left_mag']:.4f}N, R={grasp_forces['right_mag']:.4f}N")
print(f"    Cable Z: {grasp_cable_z:.4f}")

# ============================================================
# PHASE 3: LIFT
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: LIFT")
print("=" * 60)

for i in range(600):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE3_LEFT_JOINTS, device=device)
    target_left[0, -2] = GRASP_JOINT_POS
    target_left[0, -1] = GRASP_JOINT_POS
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE3_RIGHT_JOINTS, device=device)
    target_right[0, -2] = GRASP_JOINT_POS
    target_right[0, -1] = GRASP_JOINT_POS
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    if (i+1) % 200 == 0:
        cable_z = get_cable_z()[0]
        forces = get_contact_forces()
        left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
        right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
        print(f"  Step {i+1}/600: Cable Z={cable_z:.4f}, Force L={forces['left_mag']:.3f}N R={forces['right_mag']:.3f}N, Gap L={sum(left_pos)*1000:.2f}mm R={sum(right_pos)*1000:.2f}mm")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

final_cable_z = get_cable_z()[0]
final_forces = get_contact_forces()
left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()

lift_amount = final_cable_z - grasp_cable_z

print(f"\nFriction: {FRICTION}")
print(f"Gap: L={sum(left_pos)*1000:.2f}mm, R={sum(right_pos)*1000:.2f}mm")
print(f"Contact force: L={final_forces['left_mag']:.4f}N, R={final_forces['right_mag']:.4f}N")
print(f"Cable Z (grasp): {grasp_cable_z:.4f}")
print(f"Cable Z (lift):  {final_cable_z:.4f}")
print(f"Lift amount: {lift_amount*100:.2f}cm")

print("\n" + "=" * 60)
print("SUMMARY TABLE")
print("=" * 60)
print(f"| Item              | Value       |")
print(f"|-------------------|-------------|")
print(f"| Friction          | {FRICTION}         |")
print(f"| Contact Force (L) | {final_forces['left_mag']:.4f} N    |")
print(f"| Contact Force (R) | {final_forces['right_mag']:.4f} N    |")
print(f"| Cable Z (Lift)    | {final_cable_z:.4f}      |")
print(f"| Lift Amount       | {lift_amount*100:.2f} cm    |")

# Cleanup
simulation_app.close()
