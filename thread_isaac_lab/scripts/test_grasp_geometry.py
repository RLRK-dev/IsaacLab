#!/usr/bin/env python3
"""
Grasp Geometry Verification
Check if fingers are actually touching the cable
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

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS, CABLE_RADIUS

print("=" * 70)
print("GRASP GEOMETRY VERIFICATION")
print("=" * 70)

# Parameters
GRIPPER_CLOSE = 0.001
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
def set_friction(asset, value):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = value
    materials[..., 1] = value
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FRICTION)
set_friction(robot_right, FRICTION)
set_friction(cable, FRICTION)

# Get body indices
print("\n1. Robot Body Names:")
body_names_left = robot_left.body_names
print(f"   Left robot bodies: {body_names_left}")

# Find finger indices
leftfinger_idx_l = robot_left.find_bodies("panda_leftfinger")[0][0]
rightfinger_idx_l = robot_left.find_bodies("panda_rightfinger")[0][0]
leftfinger_idx_r = robot_right.find_bodies("panda_leftfinger")[0][0]
rightfinger_idx_r = robot_right.find_bodies("panda_rightfinger")[0][0]
hand_idx_l = robot_left.find_bodies("panda_hand")[0][0]
hand_idx_r = robot_right.find_bodies("panda_hand")[0][0]

print(f"\n   Left robot finger indices: leftfinger={leftfinger_idx_l}, rightfinger={rightfinger_idx_l}, hand={hand_idx_l}")
print(f"   Right robot finger indices: leftfinger={leftfinger_idx_r}, rightfinger={rightfinger_idx_r}, hand={hand_idx_r}")

# Cable body names
print(f"\n2. Cable Body Names:")
cable_body_names = cable.body_names
print(f"   {cable_body_names}")

# ============================================================
# Setup phases
# ============================================================
print("\n3. Running setup phases...")

# Phase 1: Open grippers
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

# Phase 2A: Teleport
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

# Phase 2B: Close grippers
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

# ============================================================
# Detailed geometry check
# ============================================================
print("\n" + "=" * 70)
print("GRASP GEOMETRY ANALYSIS")
print("=" * 70)

# 1. Finger joint positions
print("\n4. Gripper Joint Positions (last 2 joints = finger prismatic):")
joint_pos_left = robot_left.data.joint_pos[0].cpu().numpy()
joint_pos_right = robot_right.data.joint_pos[0].cpu().numpy()
print(f"   Left robot:  finger_left={joint_pos_left[-2]*1000:.3f}mm, finger_right={joint_pos_left[-1]*1000:.3f}mm")
print(f"   Right robot: finger_left={joint_pos_right[-2]*1000:.3f}mm, finger_right={joint_pos_right[-1]*1000:.3f}mm")
print(f"   Left gap:  {(joint_pos_left[-2] + joint_pos_left[-1])*1000:.2f}mm")
print(f"   Right gap: {(joint_pos_right[-2] + joint_pos_right[-1])*1000:.2f}mm")

# 2. Finger body positions
print("\n5. Finger Body Positions (world frame):")
pos_leftfinger_l = robot_left.data.body_pos_w[0, leftfinger_idx_l].cpu().numpy()
pos_rightfinger_l = robot_left.data.body_pos_w[0, rightfinger_idx_l].cpu().numpy()
pos_leftfinger_r = robot_right.data.body_pos_w[0, leftfinger_idx_r].cpu().numpy()
pos_rightfinger_r = robot_right.data.body_pos_w[0, rightfinger_idx_r].cpu().numpy()
pos_hand_l = robot_left.data.body_pos_w[0, hand_idx_l].cpu().numpy()
pos_hand_r = robot_right.data.body_pos_w[0, hand_idx_r].cpu().numpy()

print(f"   LEFT ROBOT:")
print(f"     hand:        X={pos_hand_l[0]:.4f}, Y={pos_hand_l[1]:.4f}, Z={pos_hand_l[2]:.4f}")
print(f"     leftfinger:  X={pos_leftfinger_l[0]:.4f}, Y={pos_leftfinger_l[1]:.4f}, Z={pos_leftfinger_l[2]:.4f}")
print(f"     rightfinger: X={pos_rightfinger_l[0]:.4f}, Y={pos_rightfinger_l[1]:.4f}, Z={pos_rightfinger_l[2]:.4f}")
print(f"     finger gap (Y): {abs(pos_leftfinger_l[1] - pos_rightfinger_l[1])*1000:.2f}mm")

print(f"\n   RIGHT ROBOT:")
print(f"     hand:        X={pos_hand_r[0]:.4f}, Y={pos_hand_r[1]:.4f}, Z={pos_hand_r[2]:.4f}")
print(f"     leftfinger:  X={pos_leftfinger_r[0]:.4f}, Y={pos_leftfinger_r[1]:.4f}, Z={pos_leftfinger_r[2]:.4f}")
print(f"     rightfinger: X={pos_rightfinger_r[0]:.4f}, Y={pos_rightfinger_r[1]:.4f}, Z={pos_rightfinger_r[2]:.4f}")
print(f"     finger gap (Y): {abs(pos_leftfinger_r[1] - pos_rightfinger_r[1])*1000:.2f}mm")

# 3. Cable segment positions
print("\n6. Cable Segment Positions:")
cable_positions = cable.data.body_pos_w[0].cpu().numpy()
print(f"   Total segments: {len(cable_positions)}")

# Find segments closest to each gripper
for seg_idx in [4, 5, 6, 14, 15, 16]:
    if seg_idx < len(cable_positions):
        pos = cable_positions[seg_idx]
        print(f"   seg_{seg_idx}: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}")

# 4. Distance from finger to cable
print("\n7. Distance from Finger to Cable Segments:")

# Left robot - find closest cable segment
finger_center_l = (pos_leftfinger_l + pos_rightfinger_l) / 2
min_dist_l = float('inf')
closest_seg_l = -1
for i, pos in enumerate(cable_positions):
    dist = np.linalg.norm(finger_center_l - pos)
    if dist < min_dist_l:
        min_dist_l = dist
        closest_seg_l = i

print(f"   LEFT ROBOT:")
print(f"     Finger center: X={finger_center_l[0]:.4f}, Y={finger_center_l[1]:.4f}, Z={finger_center_l[2]:.4f}")
print(f"     Closest cable seg: seg_{closest_seg_l}")
print(f"     Distance to closest: {min_dist_l*1000:.2f}mm")

# Check seg_5 specifically
seg5_pos = cable_positions[5]
dist_to_seg5 = np.linalg.norm(finger_center_l - seg5_pos)
print(f"     Distance to seg_5: {dist_to_seg5*1000:.2f}mm")

# Right robot
finger_center_r = (pos_leftfinger_r + pos_rightfinger_r) / 2
min_dist_r = float('inf')
closest_seg_r = -1
for i, pos in enumerate(cable_positions):
    dist = np.linalg.norm(finger_center_r - pos)
    if dist < min_dist_r:
        min_dist_r = dist
        closest_seg_r = i

print(f"\n   RIGHT ROBOT:")
print(f"     Finger center: X={finger_center_r[0]:.4f}, Y={finger_center_r[1]:.4f}, Z={finger_center_r[2]:.4f}")
print(f"     Closest cable seg: seg_{closest_seg_r}")
print(f"     Distance to closest: {min_dist_r*1000:.2f}mm")

# Check seg_14 specifically
seg14_pos = cable_positions[14]
dist_to_seg14 = np.linalg.norm(finger_center_r - seg14_pos)
print(f"     Distance to seg_14: {dist_to_seg14*1000:.2f}mm")

# 5. Check if cable is between fingers
print("\n8. Cable Position Relative to Fingers:")

# For left robot - check if cable Y is between left and right finger Y
cable_y_at_left = cable_positions[closest_seg_l][1]
leftfinger_y_l = pos_leftfinger_l[1]
rightfinger_y_l = pos_rightfinger_l[1]

print(f"   LEFT ROBOT (Y-axis check):")
print(f"     leftfinger Y:  {leftfinger_y_l:.4f}")
print(f"     cable seg_{closest_seg_l} Y: {cable_y_at_left:.4f}")
print(f"     rightfinger Y: {rightfinger_y_l:.4f}")
if min(leftfinger_y_l, rightfinger_y_l) < cable_y_at_left < max(leftfinger_y_l, rightfinger_y_l):
    print(f"     -> Cable IS between fingers (Y-axis)")
else:
    print(f"     -> Cable NOT between fingers (Y-axis)")

# For right robot
cable_y_at_right = cable_positions[closest_seg_r][1]
leftfinger_y_r = pos_leftfinger_r[1]
rightfinger_y_r = pos_rightfinger_r[1]

print(f"\n   RIGHT ROBOT (Y-axis check):")
print(f"     leftfinger Y:  {leftfinger_y_r:.4f}")
print(f"     cable seg_{closest_seg_r} Y: {cable_y_at_right:.4f}")
print(f"     rightfinger Y: {rightfinger_y_r:.4f}")
if min(leftfinger_y_r, rightfinger_y_r) < cable_y_at_right < max(leftfinger_y_r, rightfinger_y_r):
    print(f"     -> Cable IS between fingers (Y-axis)")
else:
    print(f"     -> Cable NOT between fingers (Y-axis)")

# 6. Contact sensor verification
print("\n9. Contact Sensor Reading:")
force_l = np.linalg.norm(contact_left.data.net_forces_w[0].cpu().numpy())
force_r = np.linalg.norm(contact_right.data.net_forces_w[0].cpu().numpy())
print(f"   Left robot contact force:  {force_l:.3f}N")
print(f"   Right robot contact force: {force_r:.3f}N")

# Cable radius (from task_config.py)
print(f"\n10. Geometry Check (cable radius {CABLE_RADIUS*1000}mm from task_config.py):")
finger_gap_l = abs(pos_leftfinger_l[1] - pos_rightfinger_l[1])
finger_gap_r = abs(pos_leftfinger_r[1] - pos_rightfinger_r[1])
print(f"   LEFT: finger gap={finger_gap_l*1000:.2f}mm, cable diameter={CABLE_RADIUS*2*1000:.1f}mm")
print(f"         Gap - diameter = {(finger_gap_l - CABLE_RADIUS*2)*1000:.2f}mm")
if finger_gap_l < CABLE_RADIUS * 2:
    print(f"         -> Fingers SHOULD be squeezing cable")
else:
    print(f"         -> Gap larger than cable - NOT squeezing")

print(f"\n   RIGHT: finger gap={finger_gap_r*1000:.2f}mm, cable diameter={CABLE_RADIUS*2*1000:.1f}mm")
print(f"         Gap - diameter = {(finger_gap_r - CABLE_RADIUS*2)*1000:.2f}mm")
if finger_gap_r < CABLE_RADIUS * 2:
    print(f"         -> Fingers SHOULD be squeezing cable")
else:
    print(f"         -> Gap larger than cable - NOT squeezing")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Contact Force:  L={force_l:.1f}N, R={force_r:.1f}N")
print(f"  Finger Gap:     L={finger_gap_l*1000:.1f}mm, R={finger_gap_r*1000:.1f}mm")
print(f"  Cable Diameter: {CABLE_RADIUS*2*1000:.1f}mm")
print(f"  Closest Cable:  L=seg_{closest_seg_l} ({min_dist_l*1000:.1f}mm), R=seg_{closest_seg_r} ({min_dist_r*1000:.1f}mm)")

if force_l > 1.0 and force_r > 1.0:
    if finger_gap_l > CABLE_RADIUS * 2 or finger_gap_r > CABLE_RADIUS * 2:
        print("\n  WARNING: Contact force detected but finger gap > cable diameter!")
        print("  -> Contact may be from collision, not squeezing")
    else:
        print("\n  OK: Contact force detected and geometry confirms squeeze")
else:
    print("\n  WARNING: Low/no contact force detected")

simulation_app.close()
