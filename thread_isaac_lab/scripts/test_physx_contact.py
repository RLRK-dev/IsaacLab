#!/usr/bin/env python3
"""
PhysX Contact Force Test - Direct query of contact forces
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
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    CABLE_Z, CABLE_RADIUS
)

# PhysX contact query
import omni.physx
from pxr import UsdPhysics, PhysxSchema

print("=" * 60)
print("PHYSX CONTACT FORCE TEST")
print("=" * 60)

# Setup simulation
sim_cfg = sim_utils.SimulationCfg(
    dt=1/240,
    render_interval=1,
    physics_material=sim_utils.RigidBodyMaterialCfg(
        static_friction=3.0,
        dynamic_friction=3.0,
        restitution=0.0,
        friction_combine_mode="multiply",
    ),
)
sim = sim_utils.SimulationContext(sim_cfg)
scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]

device = robot_left.device

def get_gripper_state(robot, name):
    pos = robot.data.joint_pos[0, -2:].cpu().numpy()
    return f"{name}: gap={sum(pos)*1000:.2f}mm"

def get_cable_z():
    cable_pos = cable.data.body_pos_w[0, :, 2].cpu().numpy()
    return np.nanmean(cable_pos)

# Get PhysX interface
physx_interface = omni.physx.get_physx_interface()
physx_scene_query = omni.physx.get_physx_scene_query_interface()

print(f"\nInitial cable Z: {get_cable_z():.4f}")

# ============================================================
# PHASE 2: GRASP
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2: GRASP")
print("=" * 60)

# Step 1: Open grippers
print("\n--- Step 1: Open grippers ---")
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

# Step 2: Teleport to Phase 2
print("\n--- Step 2: Teleport ARM to Phase 2 ---")
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

# Step 3: Close grippers and monitor contact
print("\n--- Step 3: Close grippers (monitor contact) ---")

# Try to get contact data using articulation view
try:
    from omni.isaac.core.articulations import ArticulationView
    print("  ArticulationView available")
except ImportError:
    print("  ArticulationView not available")

# Monitor grip closing
for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2] = 0.0
    target_left[0, -1] = 0.0
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2] = 0.0
    target_right[0, -1] = 0.0
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    # Check gap convergence
    if (i+1) % 50 == 0:
        left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
        right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
        cable_z = get_cable_z()

        # Get gripper joint efforts (force feedback)
        left_effort = robot_left.data.applied_torque[0, -2:].cpu().numpy()
        right_effort = robot_right.data.applied_torque[0, -2:].cpu().numpy()

        print(f"  Step {i+1}/300:")
        print(f"    Left gap: {sum(left_pos)*1000:.2f}mm, effort: {left_effort}")
        print(f"    Right gap: {sum(right_pos)*1000:.2f}mm, effort: {right_effort}")
        print(f"    Cable Z: {cable_z:.4f}")

# Final state
left_pos = robot_left.data.joint_pos[0, -2:].cpu().numpy()
right_pos = robot_right.data.joint_pos[0, -2:].cpu().numpy()
left_effort = robot_left.data.applied_torque[0, -2:].cpu().numpy()
right_effort = robot_right.data.applied_torque[0, -2:].cpu().numpy()

print(f"\n--- Grasp Complete ---")
print(f"  Left gap: {sum(left_pos)*1000:.2f}mm")
print(f"  Right gap: {sum(right_pos)*1000:.2f}mm")
print(f"  Left effort: {left_effort}")
print(f"  Right effort: {right_effort}")
print(f"  Cable Z: {get_cable_z():.4f}")

# Check if contact exists based on effort
print(f"\n--- Contact Analysis ---")
print(f"  Effort magnitude (Left):  {np.linalg.norm(left_effort):.4f}")
print(f"  Effort magnitude (Right): {np.linalg.norm(right_effort):.4f}")

# Expected: If cable is being squeezed, effort should be non-zero
if np.linalg.norm(left_effort) > 0.01 or np.linalg.norm(right_effort) > 0.01:
    print(f"  --> Contact detected (non-zero effort)")
else:
    print(f"  --> NO contact (zero effort) - fingers closed without resistance")

# ============================================================
# Additional: Check collision geometry
# ============================================================
print("\n" + "=" * 60)
print("COLLISION GEOMETRY CHECK")
print("=" * 60)

from pxr import Usd, UsdGeom
stage = omni.usd.get_context().get_stage()

# Check finger collision prims
finger_paths = [
    "/World/envs/env_0/Robot_Left/panda_leftfinger",
    "/World/envs/env_0/Robot_Left/panda_rightfinger",
    "/World/envs/env_0/Robot_Right/panda_leftfinger",
    "/World/envs/env_0/Robot_Right/panda_rightfinger",
]

for path in finger_paths:
    prim = stage.GetPrimAtPath(path)
    if prim.IsValid():
        # Check for collision API
        has_collision = prim.HasAPI(UsdPhysics.CollisionAPI)
        # Check for rigid body
        has_rigidbody = prim.HasAPI(UsdPhysics.RigidBodyAPI)
        # Check for material
        has_material = prim.HasAPI(UsdPhysics.MaterialAPI)

        # Find collision children
        collision_children = []
        for child in prim.GetAllChildren():
            if "collision" in child.GetPath().pathString.lower():
                collision_children.append(child.GetPath().pathString)

        print(f"\n{path}:")
        print(f"  HasCollisionAPI: {has_collision}")
        print(f"  HasRigidBodyAPI: {has_rigidbody}")
        print(f"  HasMaterialAPI: {has_material}")
        print(f"  Collision children: {collision_children[:3]}...")

# Check cable collision
cable_path = "/World/envs/env_0/Cable"
cable_prim = stage.GetPrimAtPath(cable_path)
if cable_prim.IsValid():
    print(f"\n{cable_path}:")
    # Check first segment
    seg0 = stage.GetPrimAtPath(f"{cable_path}/seg_0")
    if seg0.IsValid():
        has_collision = seg0.HasAPI(UsdPhysics.CollisionAPI)
        has_rigidbody = seg0.HasAPI(UsdPhysics.RigidBodyAPI)
        print(f"  seg_0 HasCollisionAPI: {has_collision}")
        print(f"  seg_0 HasRigidBodyAPI: {has_rigidbody}")

        # Check collision geometry
        for child in seg0.GetAllChildren():
            child_path = child.GetPath().pathString
            if "collision" in child_path.lower() or "geom" in child_path.lower():
                print(f"  Found: {child_path}")

# Cleanup
simulation_app.close()
