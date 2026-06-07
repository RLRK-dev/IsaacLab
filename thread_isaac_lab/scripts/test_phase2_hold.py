#!/usr/bin/env python3
"""
Phase 2 Hold Test - Check if contact force is maintained without lifting
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
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
)

print("=" * 60)
print("PHASE 2 HOLD TEST - Contact Force Maintenance")
print("=" * 60)

# Parameters
GRIPPER_CLOSE = 0.003  # 6mm gap as per CLAUDE.md
FRICTION = 5.0

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

@configclass
class TestSceneCfg(DualArmSceneCfg):
    """Scene with contact sensors"""
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0,
        history_length=1,
        track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"],
        debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0,
        history_length=1,
        track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"],
        debug_vis=False,
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

# Apply friction at runtime
print(f"\nApplying friction={FRICTION} at runtime...")

def set_friction(asset, value):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = value  # Static friction
    materials[..., 1] = value  # Dynamic friction
    env_ids = torch.arange(1, device="cpu")
    asset.root_physx_view.set_material_properties(materials, env_ids)

set_friction(robot_left, FRICTION)
set_friction(robot_right, FRICTION)
set_friction(cable, FRICTION)
print("  Friction applied to robot_left, robot_right, cable")

def get_contact_forces():
    left_force = contact_left.data.net_forces_w[0].cpu().numpy()
    right_force = contact_right.data.net_forces_w[0].cpu().numpy()
    return np.linalg.norm(left_force), np.linalg.norm(right_force)

def get_gripper_gap(robot):
    pos = robot.data.joint_pos[0, -2:].cpu().numpy()
    return sum(pos) * 1000  # mm

def get_cable_z():
    return cable.data.body_pos_w[0, :, 2].cpu().numpy().mean()

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

print(f"  Left gap: {get_gripper_gap(robot_left):.2f}mm")
print(f"  Right gap: {get_gripper_gap(robot_right):.2f}mm")

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

print(f"  Cable Z: {get_cable_z():.4f}")

# ============================================================
# PHASE 2B: CLOSE GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print(f"PHASE 2B: CLOSE GRIPPERS (GRIPPER_CLOSE={GRIPPER_CLOSE})")
print("=" * 60)

for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2] = GRIPPER_CLOSE
    target_left[0, -1] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2] = GRIPPER_CLOSE
    target_right[0, -1] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    if (i+1) % 100 == 0:
        force_l, force_r = get_contact_forces()
        print(f"  Step {i+1}/300: Force L={force_l:.3f}N R={force_r:.3f}N, Gap L={get_gripper_gap(robot_left):.2f}mm R={get_gripper_gap(robot_right):.2f}mm")

# Record initial state
force_l, force_r = get_contact_forces()
gap_l = get_gripper_gap(robot_left)
gap_r = get_gripper_gap(robot_right)
cable_z = get_cable_z()

print(f"\n  Initial (Step 0):")
print(f"    Contact Force: L={force_l:.4f}N, R={force_r:.4f}N")
print(f"    Gap: L={gap_l:.2f}mm, R={gap_r:.2f}mm")
print(f"    Cable Z: {cable_z:.4f}")

results = {
    0: {'force_l': force_l, 'force_r': force_r, 'gap_l': gap_l, 'gap_r': gap_r, 'cable_z': cable_z}
}

# ============================================================
# PHASE 2 HOLD: MAINTAIN POSITION FOR 1000 STEPS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2 HOLD: MAINTAIN POSITION FOR 1000 STEPS")
print("=" * 60)

for i in range(1000):
    # Keep Phase 2 joint positions
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2] = GRIPPER_CLOSE
    target_left[0, -1] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2] = GRIPPER_CLOSE
    target_right[0, -1] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    if (i+1) == 500:
        force_l, force_r = get_contact_forces()
        gap_l = get_gripper_gap(robot_left)
        gap_r = get_gripper_gap(robot_right)
        cable_z = get_cable_z()
        results[500] = {'force_l': force_l, 'force_r': force_r, 'gap_l': gap_l, 'gap_r': gap_r, 'cable_z': cable_z}
        print(f"  Step 500: Force L={force_l:.4f}N R={force_r:.4f}N, Gap L={gap_l:.2f}mm R={gap_r:.2f}mm, Cable Z={cable_z:.4f}")

    if (i+1) == 1000:
        force_l, force_r = get_contact_forces()
        gap_l = get_gripper_gap(robot_left)
        gap_r = get_gripper_gap(robot_right)
        cable_z = get_cable_z()
        results[1000] = {'force_l': force_l, 'force_r': force_r, 'gap_l': gap_l, 'gap_r': gap_r, 'cable_z': cable_z}
        print(f"  Step 1000: Force L={force_l:.4f}N R={force_r:.4f}N, Gap L={gap_l:.2f}mm R={gap_r:.2f}mm, Cable Z={cable_z:.4f}")

# ============================================================
# SUMMARY TABLE
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY TABLE")
print("=" * 60)

print(f"| Item | Step 0 | Step 500 | Step 1000 |")
print(f"|------|--------|----------|-----------|")
print(f"| Contact Force L (N) | {results[0]['force_l']:.4f} | {results[500]['force_l']:.4f} | {results[1000]['force_l']:.4f} |")
print(f"| Contact Force R (N) | {results[0]['force_r']:.4f} | {results[500]['force_r']:.4f} | {results[1000]['force_r']:.4f} |")
print(f"| Gap L (mm) | {results[0]['gap_l']:.2f} | {results[500]['gap_l']:.2f} | {results[1000]['gap_l']:.2f} |")
print(f"| Gap R (mm) | {results[0]['gap_r']:.2f} | {results[500]['gap_r']:.2f} | {results[1000]['gap_r']:.2f} |")
print(f"| Cable Z | {results[0]['cable_z']:.4f} | {results[500]['cable_z']:.4f} | {results[1000]['cable_z']:.4f} |")

# Cleanup
simulation_app.close()
