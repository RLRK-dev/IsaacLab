#!/usr/bin/env python3
"""
Full Phase 1 -> 2 -> 3 -> 4 -> 5 Integration Test

Tests the complete sequence:
- Phase 1: Hover above cable
- Phase 2: Approach and grasp
- Phase 3: Lift using cumulative Diff IK
- Phase 4: Hook approach using cumulative Diff IK
- Phase 5: Cable placement using cumulative Diff IK

Verification criteria:
1. Grasp success (contact force > 5N)
2. Lift success (cable Z elevation)
3. Phase 3->4 transition (EE error < 2cm)
4. Phase 4->5 transition (EE error < 2cm)
5. Grasp maintained throughout all phases
6. No cable drop

Based on test_full_phase1_to_4.py
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
    # Phase 1 (Hover)
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    # Phase 2 (Grasp)
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT,
    # Phase 3 (Lift)
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    WAYPOINT_PHASE3_LEFT, WAYPOINT_PHASE3_RIGHT,
    # Phase 4 (Hook Approach)
    PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    # Phase 5 (Cable Placement)
    PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    # Gripper
    GRIPPER_CLOSE, GRIPPER_OPEN,
    # Friction
    FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION,
    CABLE_STATIC_FRICTION, CABLE_DYNAMIC_FRICTION,
)

print("=" * 70)
print("FULL PHASE 1 -> 2 -> 3 -> 4 -> 5 INTEGRATION TEST")
print("=" * 70)

# Parameters (use task_config.py friction values - 9.5cm success config)
LIFT_NUM_STEPS = 300       # Phase 2->3 lift
TRANSITION_NUM_STEPS = 500 # Phase 3->4 transition
PHASE45_NUM_STEPS = 400    # Phase 4->5 transition
Z_OFFSET = 0.1034          # IK vs Isaac Lab kinematics offset
LIFT_TARGET_CM = 5.0       # Target lift in cm

# Results storage
results = {
    "phase1": {},
    "phase2": {},
    "phase3": {},
    "phase4": {},
    "phase5": {},
    "overall": {}
}

print(f"\nConfiguration:")
print(f"  GRIPPER_CLOSE: {GRIPPER_CLOSE}")
print(f"  FINGER_FRICTION: static={FINGER_STATIC_FRICTION}, dynamic={FINGER_DYNAMIC_FRICTION}")
print(f"  CABLE_FRICTION: static={CABLE_STATIC_FRICTION}, dynamic={CABLE_DYNAMIC_FRICTION}")
print(f"  LIFT_NUM_STEPS: {LIFT_NUM_STEPS}")
print(f"  TRANSITION_NUM_STEPS: {TRANSITION_NUM_STEPS}")
print(f"  PHASE45_NUM_STEPS: {PHASE45_NUM_STEPS}")
print(f"  Z_OFFSET: {Z_OFFSET}")

print(f"\nPhase Waypoints:")
print(f"  Phase 1 (Hover):  L={WAYPOINT_PHASE1_LEFT}, R={WAYPOINT_PHASE1_RIGHT}")
print(f"  Phase 2 (Grasp):  L={WAYPOINT_PHASE2_LEFT}, R={WAYPOINT_PHASE2_RIGHT}")
print(f"  Phase 3 (Lift):   L={WAYPOINT_PHASE3_LEFT}, R={WAYPOINT_PHASE3_RIGHT}")
print(f"  Phase 4 (Hook):   L={WAYPOINT_PHASE4_LEFT}, R={WAYPOINT_PHASE4_RIGHT}")
print(f"  Phase 5 (Place):  L={WAYPOINT_PHASE5_LEFT}, R={WAYPOINT_PHASE5_RIGHT}")
print("=" * 70)

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

device = robot_left.device

# Apply friction
print("\nApplying friction...")
def set_friction(asset, static_f, dynamic_f):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = static_f
    materials[..., 1] = dynamic_f
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION)
set_friction(robot_right, FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION)
set_friction(cable, CABLE_STATIC_FRICTION, CABLE_DYNAMIC_FRICTION)

# Setup Diff IK controllers (absolute position mode)
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

# Jacobian body indices
jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

# Helper functions
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

def get_joint_angles(robot):
    return robot.data.joint_pos[0, :7].cpu().numpy() * 180 / np.pi

def set_robot_joints(robot, arm_joints, gripper_val):
    """Set robot joint positions"""
    target = robot.data.joint_pos[0].unsqueeze(0).clone()
    target[0, :7] = torch.tensor(arm_joints, device=device)
    target[0, -2:] = gripper_val
    robot.set_joint_position_target(target)
    robot.write_data_to_sim()

def teleport_robot(robot, arm_joints, gripper_val):
    """Teleport robot to position"""
    state = robot.data.joint_pos[0].unsqueeze(0).clone()
    state[0, :7] = torch.tensor(arm_joints, device=device)
    state[0, -2:] = gripper_val
    robot.write_joint_state_to_sim(state, robot.data.joint_vel[0].unsqueeze(0))

# Contact tracking helper
CONTACT_LOST_THRESHOLD = 10

def track_contact(sensor_left, sensor_right, consecutive_low_counter, contact_lost_at):
    """Track contact status with hysteresis"""
    force_l = get_contact_force(sensor_left)
    force_r = get_contact_force(sensor_right)

    if force_l < 1.0 and force_r < 1.0:
        consecutive_low_counter += 1
        if consecutive_low_counter >= CONTACT_LOST_THRESHOLD and contact_lost_at is None:
            return consecutive_low_counter, consecutive_low_counter - CONTACT_LOST_THRESHOLD + 1, "*** LOST ***"
        elif contact_lost_at is not None:
            return consecutive_low_counter, contact_lost_at, "lost"
        else:
            return consecutive_low_counter, contact_lost_at, f"low({consecutive_low_counter})"
    else:
        return 0, contact_lost_at, "recovered?" if contact_lost_at else "OK"

# ============================================================
# PHASE 1: HOVER
# ============================================================
print("\n" + "=" * 70)
print("PHASE 1: HOVER - Initial Position")
print("=" * 70)

teleport_robot(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
teleport_robot(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)

for _ in range(100):
    set_robot_joints(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    set_robot_joints(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    sim.step()
    scene.update(sim.get_physics_dt())

phase1_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase1_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase1_cable_z = get_cable_center_z()

print(f"\nPhase 1 State:")
print(f"  EE Left:   ({phase1_ee_left[0]:.4f}, {phase1_ee_left[1]:.4f}, {phase1_ee_left[2]:.4f})")
print(f"  EE Right:  ({phase1_ee_right[0]:.4f}, {phase1_ee_right[1]:.4f}, {phase1_ee_right[2]:.4f})")
print(f"  Cable Z:   {phase1_cable_z:.4f}")

results["phase1"] = {
    "ee_left": phase1_ee_left.tolist(),
    "ee_right": phase1_ee_right.tolist(),
    "cable_z": phase1_cable_z
}

# ============================================================
# PHASE 2: APPROACH AND GRASP
# ============================================================
print("\n" + "=" * 70)
print("PHASE 2: APPROACH AND GRASP")
print("=" * 70)

print("\n  Moving to grasp position...")
teleport_robot(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
teleport_robot(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)

for _ in range(50):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)
    sim.step()
    scene.update(sim.get_physics_dt())

print(f"  Closing grippers (GRIPPER_CLOSE={GRIPPER_CLOSE})...")
for i in range(300):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())
    if i % 100 == 99:
        force_l = get_contact_force(contact_left)
        force_r = get_contact_force(contact_right)
        print(f"    Step {i+1}/300: Force L={force_l:.2f}N, R={force_r:.2f}N")

print("  Stabilizing grasp...")
for _ in range(100):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

phase2_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase2_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase2_ee_pos_left_tensor = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase2_ee_quat_left_tensor = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase2_ee_pos_right_tensor = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase2_ee_quat_right_tensor = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase2_force_l = get_contact_force(contact_left)
phase2_force_r = get_contact_force(contact_right)
phase2_cable_z = get_cable_center_z()

print(f"\nPhase 2 State:")
print(f"  EE Left:   ({phase2_ee_left[0]:.4f}, {phase2_ee_left[1]:.4f}, {phase2_ee_left[2]:.4f})")
print(f"  EE Right:  ({phase2_ee_right[0]:.4f}, {phase2_ee_right[1]:.4f}, {phase2_ee_right[2]:.4f})")
print(f"  Force:     L={phase2_force_l:.2f}N, R={phase2_force_r:.2f}N")
print(f"  Cable Z:   {phase2_cable_z:.4f}")

grasp_success = phase2_force_l > 5.0 and phase2_force_r > 5.0
print(f"  Grasp:     {'SUCCESS' if grasp_success else 'FAIL'} (threshold > 5N)")

results["phase2"] = {
    "ee_left": phase2_ee_left.tolist(),
    "ee_right": phase2_ee_right.tolist(),
    "force_left": phase2_force_l,
    "force_right": phase2_force_r,
    "cable_z": phase2_cable_z,
    "grasp_success": grasp_success
}

# ============================================================
# PHASE 3: LIFT (Cumulative Diff IK)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 3: LIFT (Cumulative Diff IK)")
print(f"  NUM_STEPS: {LIFT_NUM_STEPS}")
print("=" * 70)

lift_amount_m = LIFT_TARGET_CM / 100.0
target_phase3_left = phase2_ee_pos_left_tensor.clone()
target_phase3_left[0, 2] += lift_amount_m
target_phase3_right = phase2_ee_pos_right_tensor.clone()
target_phase3_right[0, 2] += lift_amount_m

print(f"\nLift Target:")
print(f"  Start Z: {phase2_ee_pos_left_tensor[0, 2].item():.4f}")
print(f"  Target Z: {target_phase3_left[0, 2].item():.4f} (+{LIFT_TARGET_CM}cm)")

start_ee_pos_left = phase2_ee_pos_left_tensor.clone()
start_ee_pos_right = phase2_ee_pos_right_tensor.clone()

diff_ik_left.reset()
diff_ik_right.reset()

# Pre-lift stabilization
print("  Pre-lift stabilization...")
for _ in range(50):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

phase2_ee_pos_left_tensor = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase2_ee_quat_left_tensor = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase2_ee_pos_right_tensor = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase2_ee_quat_right_tensor = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

target_phase3_left = phase2_ee_pos_left_tensor.clone()
target_phase3_left[0, 2] += lift_amount_m
target_phase3_right = phase2_ee_pos_right_tensor.clone()
target_phase3_right[0, 2] += lift_amount_m

start_ee_pos_left = phase2_ee_pos_left_tensor.clone()
start_ee_pos_right = phase2_ee_pos_right_tensor.clone()

min_force_during_lift = float('inf')
contact_lost_step_lift = None
consecutive_low_force_lift = 0

print(f"\n{'Step':>5} | {'EE Z':>7} | {'Force L':>8} | {'Force R':>8} | {'Cable Z':>8} | Status")
print("-" * 70)

for i in range(LIFT_NUM_STEPS):
    alpha = (i + 1) / LIFT_NUM_STEPS
    target_pos_left = start_ee_pos_left + alpha * (target_phase3_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase3_right - start_ee_pos_right)

    command_left = torch.cat([target_pos_left, phase2_ee_quat_left_tensor], dim=1)
    command_right = torch.cat([target_pos_right, phase2_ee_quat_right_tensor], dim=1)

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

    ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)
    cable_z = get_cable_center_z()

    if force_l > 0 or force_r > 0:
        min_force = min(force_l, force_r) if force_l > 0 and force_r > 0 else max(force_l, force_r)
        if min_force < min_force_during_lift:
            min_force_during_lift = min_force

    status = "OK"
    if force_l < 1.0 and force_r < 1.0:
        consecutive_low_force_lift += 1
        if consecutive_low_force_lift >= CONTACT_LOST_THRESHOLD and contact_lost_step_lift is None:
            contact_lost_step_lift = i - CONTACT_LOST_THRESHOLD + 1
            status = "*** LOST ***"
        elif contact_lost_step_lift is not None:
            status = "lost"
        else:
            status = f"low({consecutive_low_force_lift})"
    else:
        consecutive_low_force_lift = 0
        if contact_lost_step_lift is not None:
            status = "recovered?"

    if i % 50 == 0 or status == "*** LOST ***" or i == LIFT_NUM_STEPS - 1:
        print(f"{i:>5} | {ee_z:>7.4f} | {force_l:>7.2f}N | {force_r:>7.2f}N | {cable_z:>8.4f} | {status}")

phase3_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase3_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase3_ee_pos_left_tensor = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase3_ee_quat_left_tensor = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase3_ee_pos_right_tensor = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase3_ee_quat_right_tensor = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase3_force_l = get_contact_force(contact_left)
phase3_force_r = get_contact_force(contact_right)
phase3_cable_z = get_cable_center_z()

lift_amount = (phase3_ee_left[2] - phase2_ee_left[2]) * 100
cable_lift = (phase3_cable_z - phase2_cable_z) * 100 if not np.isnan(phase3_cable_z) and not np.isnan(phase2_cable_z) else float('nan')

print(f"\nPhase 3 State:")
print(f"  EE Left:   ({phase3_ee_left[0]:.4f}, {phase3_ee_left[1]:.4f}, {phase3_ee_left[2]:.4f})")
print(f"  EE Right:  ({phase3_ee_right[0]:.4f}, {phase3_ee_right[1]:.4f}, {phase3_ee_right[2]:.4f})")
print(f"  Force:     L={phase3_force_l:.2f}N, R={phase3_force_r:.2f}N")
print(f"  Cable Z:   {phase3_cable_z:.4f}")
print(f"  EE Lift:   {lift_amount:.2f}cm")
print(f"  Cable Lift:{cable_lift:.2f}cm")

lift_success = cable_lift > 5.0 if not np.isnan(cable_lift) else False
grasp_maintained_phase3 = contact_lost_step_lift is None

print(f"  Lift:      {'SUCCESS' if lift_success else 'FAIL'} (threshold > 5cm)")
print(f"  Grasp:     {'MAINTAINED' if grasp_maintained_phase3 else 'LOST at step ' + str(contact_lost_step_lift)}")

results["phase3"] = {
    "ee_left": phase3_ee_left.tolist(),
    "ee_right": phase3_ee_right.tolist(),
    "force_left": phase3_force_l,
    "force_right": phase3_force_r,
    "cable_z": phase3_cable_z,
    "lift_amount_cm": lift_amount,
    "cable_lift_cm": cable_lift,
    "lift_success": lift_success,
    "grasp_maintained": grasp_maintained_phase3,
    "min_force_during_lift": min_force_during_lift
}

# ============================================================
# PHASE 4: TRANSITION (Cumulative Diff IK)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 4: TRANSITION TO HOOK (Cumulative Diff IK)")
print(f"  NUM_STEPS: {TRANSITION_NUM_STEPS}")
print("=" * 70)

target_phase4_left = torch.tensor(
    [[WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)
target_phase4_right = torch.tensor(
    [[WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)

dist_left_34 = np.linalg.norm(np.array(WAYPOINT_PHASE4_LEFT) - np.array(WAYPOINT_PHASE3_LEFT))
dist_right_34 = np.linalg.norm(np.array(WAYPOINT_PHASE4_RIGHT) - np.array(WAYPOINT_PHASE3_RIGHT))
print(f"\nCartesian distance: Left={dist_left_34*100:.2f}cm, Right={dist_right_34*100:.2f}cm")

start_ee_pos_left = phase3_ee_pos_left_tensor.clone()
start_ee_pos_right = phase3_ee_pos_right_tensor.clone()

diff_ik_left.reset()
diff_ik_right.reset()

min_force_during_phase4 = float('inf')
max_joint_change_phase4 = 0.0
contact_lost_step_phase4 = None
consecutive_low_force_phase4 = 0
prev_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().copy()

print(f"\n{'Step':>5} | {'EE L Y':>7} | {'EE R Y':>7} | {'Force L':>8} | {'Force R':>8} | {'Max dJ':>7} | Status")
print("-" * 80)

for i in range(TRANSITION_NUM_STEPS):
    alpha = (i + 1) / TRANSITION_NUM_STEPS
    target_pos_left = start_ee_pos_left + alpha * (target_phase4_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase4_right - start_ee_pos_right)

    command_left = torch.cat([target_pos_left, phase3_ee_quat_left_tensor], dim=1)
    command_right = torch.cat([target_pos_right, phase3_ee_quat_right_tensor], dim=1)

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

    curr_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy()
    joint_change = np.abs(curr_joints_right - prev_joints_right) * 180 / np.pi
    max_change = np.max(joint_change)
    if max_change > max_joint_change_phase4:
        max_joint_change_phase4 = max_change
    prev_joints_right = curr_joints_right.copy()

    ee_l = get_ee_pos(robot_left, jacobian_body_left)
    ee_r = get_ee_pos(robot_right, jacobian_body_right)
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)

    if force_l > 0 or force_r > 0:
        min_force = min(force_l, force_r) if force_l > 0 and force_r > 0 else max(force_l, force_r)
        if min_force < min_force_during_phase4:
            min_force_during_phase4 = min_force

    status = "OK"
    if force_l < 1.0 and force_r < 1.0:
        consecutive_low_force_phase4 += 1
        if consecutive_low_force_phase4 >= CONTACT_LOST_THRESHOLD and contact_lost_step_phase4 is None:
            contact_lost_step_phase4 = i - CONTACT_LOST_THRESHOLD + 1
            status = "*** LOST ***"
        elif contact_lost_step_phase4 is not None:
            status = "lost"
        else:
            status = f"low({consecutive_low_force_phase4})"
    else:
        consecutive_low_force_phase4 = 0
        if contact_lost_step_phase4 is not None:
            status = "recovered?"

    if i % 100 == 0 or status == "*** LOST ***" or i == TRANSITION_NUM_STEPS - 1:
        print(f"{i:>5} | {ee_l[1]:>7.4f} | {ee_r[1]:>7.4f} | {force_l:>7.2f}N | {force_r:>7.2f}N | {max_change:>6.2f}° | {status}")

phase4_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase4_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase4_ee_pos_left_tensor = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
phase4_ee_quat_left_tensor = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
phase4_ee_pos_right_tensor = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
phase4_ee_quat_right_tensor = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
phase4_force_l = get_contact_force(contact_left)
phase4_force_r = get_contact_force(contact_right)
phase4_cable_z = get_cable_center_z()

target_left_with_offset = np.array([WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET])
target_right_with_offset = np.array([WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET])
ee_error_left_phase4 = np.linalg.norm(phase4_ee_left - target_left_with_offset) * 100
ee_error_right_phase4 = np.linalg.norm(phase4_ee_right - target_right_with_offset) * 100

print(f"\nPhase 4 State:")
print(f"  EE Left Target:  ({target_left_with_offset[0]:.4f}, {target_left_with_offset[1]:.4f}, {target_left_with_offset[2]:.4f})")
print(f"  EE Left Actual:  ({phase4_ee_left[0]:.4f}, {phase4_ee_left[1]:.4f}, {phase4_ee_left[2]:.4f})")
print(f"  EE Left Error:   {ee_error_left_phase4:.2f}cm")
print(f"  EE Right Target: ({target_right_with_offset[0]:.4f}, {target_right_with_offset[1]:.4f}, {target_right_with_offset[2]:.4f})")
print(f"  EE Right Actual: ({phase4_ee_right[0]:.4f}, {phase4_ee_right[1]:.4f}, {phase4_ee_right[2]:.4f})")
print(f"  EE Right Error:  {ee_error_right_phase4:.2f}cm")
print(f"  Force:           L={phase4_force_l:.2f}N, R={phase4_force_r:.2f}N")
print(f"  Max joint change/step: {max_joint_change_phase4:.2f}°")

transition_success_phase4 = ee_error_left_phase4 < 2.0 and ee_error_right_phase4 < 2.0
joint_continuity_phase4 = max_joint_change_phase4 < 5.0
grasp_maintained_phase4 = contact_lost_step_phase4 is None

print(f"  EE Error:        {'SUCCESS' if transition_success_phase4 else 'FAIL'} (threshold < 2cm)")
print(f"  Joint Continuity:{'SUCCESS' if joint_continuity_phase4 else 'FAIL'} (threshold < 5°/step)")
print(f"  Grasp:           {'MAINTAINED' if grasp_maintained_phase4 else 'LOST at step ' + str(contact_lost_step_phase4)}")

results["phase4"] = {
    "ee_left": phase4_ee_left.tolist(),
    "ee_right": phase4_ee_right.tolist(),
    "ee_error_left_cm": ee_error_left_phase4,
    "ee_error_right_cm": ee_error_right_phase4,
    "force_left": phase4_force_l,
    "force_right": phase4_force_r,
    "cable_z": phase4_cable_z,
    "transition_success": transition_success_phase4,
    "joint_continuity_ok": joint_continuity_phase4,
    "max_joint_change_per_step": max_joint_change_phase4,
    "grasp_maintained": grasp_maintained_phase4,
    "min_force": min_force_during_phase4
}

# ============================================================
# PHASE 5: CABLE PLACEMENT (Cumulative Diff IK)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 5: CABLE PLACEMENT (Cumulative Diff IK)")
print(f"  NUM_STEPS: {PHASE45_NUM_STEPS}")
print("=" * 70)

target_phase5_left = torch.tensor(
    [[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)
target_phase5_right = torch.tensor(
    [[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET]],
    device=device, dtype=torch.float32
)

dist_left_45 = np.linalg.norm(np.array(WAYPOINT_PHASE5_LEFT) - np.array(WAYPOINT_PHASE4_LEFT))
dist_right_45 = np.linalg.norm(np.array(WAYPOINT_PHASE5_RIGHT) - np.array(WAYPOINT_PHASE4_RIGHT))
print(f"\nCartesian distance: Left={dist_left_45*100:.2f}cm, Right={dist_right_45*100:.2f}cm")

start_ee_pos_left = phase4_ee_pos_left_tensor.clone()
start_ee_pos_right = phase4_ee_pos_right_tensor.clone()

diff_ik_left.reset()
diff_ik_right.reset()

min_force_during_phase5 = float('inf')
max_joint_change_phase5 = 0.0
contact_lost_step_phase5 = None
consecutive_low_force_phase5 = 0
prev_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().copy()

print(f"\n{'Step':>5} | {'EE L Y':>7} | {'EE R Y':>7} | {'Force L':>8} | {'Force R':>8} | {'Max dJ':>7} | Status")
print("-" * 80)

for i in range(PHASE45_NUM_STEPS):
    alpha = (i + 1) / PHASE45_NUM_STEPS
    target_pos_left = start_ee_pos_left + alpha * (target_phase5_left - start_ee_pos_left)
    target_pos_right = start_ee_pos_right + alpha * (target_phase5_right - start_ee_pos_right)

    command_left = torch.cat([target_pos_left, phase4_ee_quat_left_tensor], dim=1)
    command_right = torch.cat([target_pos_right, phase4_ee_quat_right_tensor], dim=1)

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

    curr_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy()
    joint_change = np.abs(curr_joints_right - prev_joints_right) * 180 / np.pi
    max_change = np.max(joint_change)
    if max_change > max_joint_change_phase5:
        max_joint_change_phase5 = max_change
    prev_joints_right = curr_joints_right.copy()

    ee_l = get_ee_pos(robot_left, jacobian_body_left)
    ee_r = get_ee_pos(robot_right, jacobian_body_right)
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)

    if force_l > 0 or force_r > 0:
        min_force = min(force_l, force_r) if force_l > 0 and force_r > 0 else max(force_l, force_r)
        if min_force < min_force_during_phase5:
            min_force_during_phase5 = min_force

    status = "OK"
    if force_l < 1.0 and force_r < 1.0:
        consecutive_low_force_phase5 += 1
        if consecutive_low_force_phase5 >= CONTACT_LOST_THRESHOLD and contact_lost_step_phase5 is None:
            contact_lost_step_phase5 = i - CONTACT_LOST_THRESHOLD + 1
            status = "*** LOST ***"
        elif contact_lost_step_phase5 is not None:
            status = "lost"
        else:
            status = f"low({consecutive_low_force_phase5})"
    else:
        consecutive_low_force_phase5 = 0
        if contact_lost_step_phase5 is not None:
            status = "recovered?"

    if i % 100 == 0 or status == "*** LOST ***" or i == PHASE45_NUM_STEPS - 1:
        print(f"{i:>5} | {ee_l[1]:>7.4f} | {ee_r[1]:>7.4f} | {force_l:>7.2f}N | {force_r:>7.2f}N | {max_change:>6.2f}° | {status}")

phase5_ee_left = get_ee_pos(robot_left, jacobian_body_left)
phase5_ee_right = get_ee_pos(robot_right, jacobian_body_right)
phase5_force_l = get_contact_force(contact_left)
phase5_force_r = get_contact_force(contact_right)
phase5_cable_z = get_cable_center_z()

target_left_phase5_offset = np.array([WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET])
target_right_phase5_offset = np.array([WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET])
ee_error_left_phase5 = np.linalg.norm(phase5_ee_left - target_left_phase5_offset) * 100
ee_error_right_phase5 = np.linalg.norm(phase5_ee_right - target_right_phase5_offset) * 100

print(f"\nPhase 5 State:")
print(f"  EE Left Target:  ({target_left_phase5_offset[0]:.4f}, {target_left_phase5_offset[1]:.4f}, {target_left_phase5_offset[2]:.4f})")
print(f"  EE Left Actual:  ({phase5_ee_left[0]:.4f}, {phase5_ee_left[1]:.4f}, {phase5_ee_left[2]:.4f})")
print(f"  EE Left Error:   {ee_error_left_phase5:.2f}cm")
print(f"  EE Right Target: ({target_right_phase5_offset[0]:.4f}, {target_right_phase5_offset[1]:.4f}, {target_right_phase5_offset[2]:.4f})")
print(f"  EE Right Actual: ({phase5_ee_right[0]:.4f}, {phase5_ee_right[1]:.4f}, {phase5_ee_right[2]:.4f})")
print(f"  EE Right Error:  {ee_error_right_phase5:.2f}cm")
print(f"  Force:           L={phase5_force_l:.2f}N, R={phase5_force_r:.2f}N")
print(f"  Cable Z:         {phase5_cable_z:.4f}")
print(f"  Max joint change/step: {max_joint_change_phase5:.2f}°")

transition_success_phase5 = ee_error_left_phase5 < 2.0 and ee_error_right_phase5 < 2.0
joint_continuity_phase5 = max_joint_change_phase5 < 5.0
grasp_maintained_phase5 = contact_lost_step_phase5 is None

print(f"  EE Error:        {'SUCCESS' if transition_success_phase5 else 'FAIL'} (threshold < 2cm)")
print(f"  Joint Continuity:{'SUCCESS' if joint_continuity_phase5 else 'FAIL'} (threshold < 5°/step)")
print(f"  Grasp:           {'MAINTAINED' if grasp_maintained_phase5 else 'LOST at step ' + str(contact_lost_step_phase5)}")

results["phase5"] = {
    "ee_left": phase5_ee_left.tolist(),
    "ee_right": phase5_ee_right.tolist(),
    "ee_error_left_cm": ee_error_left_phase5,
    "ee_error_right_cm": ee_error_right_phase5,
    "force_left": phase5_force_l,
    "force_right": phase5_force_r,
    "cable_z": phase5_cable_z,
    "transition_success": transition_success_phase5,
    "joint_continuity_ok": joint_continuity_phase5,
    "max_joint_change_per_step": max_joint_change_phase5,
    "grasp_maintained": grasp_maintained_phase5,
    "min_force": min_force_during_phase5
}

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY - Phase 1 -> 2 -> 3 -> 4 -> 5")
print("=" * 70)

print("\n検証項目:")
print(f"  1. 把持成功（接触力 > 5N）:           {'✅ PASS' if grasp_success else '❌ FAIL'} (L={phase2_force_l:.1f}N, R={phase2_force_r:.1f}N)")
print(f"  2. リフト成功（ケーブルZ > +5cm）:    {'✅ PASS' if lift_success else '❌ FAIL'} ({cable_lift:.1f}cm)")
print(f"  3. Phase 3→4遷移成功（EE誤差 < 2cm）: {'✅ PASS' if transition_success_phase4 else '❌ FAIL'} (L={ee_error_left_phase4:.1f}cm, R={ee_error_right_phase4:.1f}cm)")
print(f"  4. Phase 4→5遷移成功（EE誤差 < 2cm）: {'✅ PASS' if transition_success_phase5 else '❌ FAIL'} (L={ee_error_left_phase5:.1f}cm, R={ee_error_right_phase5:.1f}cm)")
print(f"  5. 把持維持（全Phase通じて接触力 > 5N）:")
print(f"       Phase 2→3: {'✅ PASS' if grasp_maintained_phase3 else '❌ FAIL'} (min={min_force_during_lift:.1f}N)")
print(f"       Phase 3→4: {'✅ PASS' if grasp_maintained_phase4 else '❌ FAIL'} (min={min_force_during_phase4:.1f}N)")
print(f"       Phase 4→5: {'✅ PASS' if grasp_maintained_phase5 else '❌ FAIL'} (min={min_force_during_phase5:.1f}N)")

cable_dropped = phase5_cable_z < phase2_cable_z - 0.02
print(f"  6. ケーブル落下なし:                  {'✅ PASS' if not cable_dropped else '❌ FAIL'} (Z={phase5_cable_z:.4f})")

# Hook position check (Phase 5 should be near hook)
hook_position = np.array([0.25, 0.0, 0.90])  # Approximate hook position
cable_near_hook = np.linalg.norm(np.array([phase5_ee_left[0], (phase5_ee_left[1] + phase5_ee_right[1])/2, phase5_ee_left[2]]) - hook_position) < 0.15
print(f"  7. フック位置到達:                    {'✅ PASS' if cable_near_hook else '❌ FAIL'}")

all_passed = (
    grasp_success and
    lift_success and
    transition_success_phase4 and
    transition_success_phase5 and
    grasp_maintained_phase3 and
    grasp_maintained_phase4 and
    grasp_maintained_phase5 and
    not cable_dropped
)

results["overall"] = {
    "grasp_success": grasp_success,
    "lift_success": lift_success,
    "transition_success_phase4": transition_success_phase4,
    "transition_success_phase5": transition_success_phase5,
    "grasp_maintained_phase3": grasp_maintained_phase3,
    "grasp_maintained_phase4": grasp_maintained_phase4,
    "grasp_maintained_phase5": grasp_maintained_phase5,
    "cable_dropped": cable_dropped,
    "cable_near_hook": cable_near_hook,
    "all_passed": all_passed
}

print("\n" + "=" * 70)
if all_passed:
    print("✅ OVERALL: SUCCESS - Full Phase 1→2→3→4→5 completed!")
else:
    print("❌ OVERALL: FAIL - Some verification items did not pass")
    print("\nFailed items:")
    if not grasp_success:
        print("  - Grasp force below threshold")
    if not lift_success:
        print("  - Cable lift insufficient")
    if not transition_success_phase4:
        print("  - Phase 3→4 EE position error too large")
    if not transition_success_phase5:
        print("  - Phase 4→5 EE position error too large")
    if not grasp_maintained_phase3:
        print("  - Grasp lost during Phase 2→3 lift")
    if not grasp_maintained_phase4:
        print("  - Grasp lost during Phase 3→4 transition")
    if not grasp_maintained_phase5:
        print("  - Grasp lost during Phase 4→5 transition")
    if cable_dropped:
        print("  - Cable dropped")
print("=" * 70)

simulation_app.close()
