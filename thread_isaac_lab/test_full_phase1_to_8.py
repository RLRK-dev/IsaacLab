#!/usr/bin/env python3
"""
Full Phase 1 -> 2 -> 3 -> 4 -> 4.5 -> 5 -> 6 -> 7 -> 8 Integration Test

Complete cable hooking sequence with cycle reset:
- Phase 1: Hover above cable
- Phase 2: Approach and grasp
- Phase 3: Lift using cumulative Diff IK
- Phase 4: Transition using cumulative Diff IK
- Phase 4.5: Intermediate position
- Phase 5: Cable placement near hook
- Phase 6: Release and retreat
- Phase 7: Return to home position
- Phase 8: Cycle reset (prepare for next cycle)

Supports multi-cycle operation for RL training.

Based on test_full_phase1_to_6.py
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
    # Phase 4.5 (Intermediate)
    PHASE45_LEFT_JOINTS, PHASE45_RIGHT_JOINTS,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    # Phase 5 (Place)
    PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    # Phase 6 (Release & Retreat)
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    # Phase 7 (Home)
    WAYPOINT_PHASE7_LEFT, WAYPOINT_PHASE7_RIGHT,
    PHASE7_LEFT_JOINTS, PHASE7_RIGHT_JOINTS,
    # Phase 8 (Cycle Reset)
    ENABLE_CONTINUOUS_CYCLE, MAX_CYCLES,
    CYCLE_RESET_STABILIZATION_STEPS,
    # Gripper
    GRIPPER_CLOSE, GRIPPER_OPEN,
    # Friction
    FINGER_STATIC_FRICTION, FINGER_DYNAMIC_FRICTION,
    CABLE_STATIC_FRICTION, CABLE_DYNAMIC_FRICTION,
)

print("=" * 70)
print("FULL PHASE 1 -> 2 -> 3 -> 4 -> 4.5 -> 5 -> 6 -> 7 -> 8 INTEGRATION TEST")
print("=" * 70)

# Parameters (use task_config.py friction values - 9.5cm success config)
LIFT_NUM_STEPS = 300       # Phase 2->3 lift
TRANSITION_NUM_STEPS = 500 # Phase 3->4, 4->4.5, 4.5->5, 5->6 transitions
PHASE67_NUM_STEPS = 400    # Phase 6->7 transition
Z_OFFSET = 0.1034          # IK vs Isaac Lab kinematics offset
LIFT_TARGET_CM = 5.0       # Target lift in cm
CONTACT_LOST_THRESHOLD = 10  # Consecutive low-force steps to declare contact lost

# Results storage
results = {
    "phase1": {},
    "phase2": {},
    "phase3": {},
    "phase4": {},
    "phase45": {},
    "phase5": {},
    "phase6": {},
    "phase7": {},
    "phase8": {},
    "overall": {},
    "cycles": []
}

print(f"\nConfiguration:")
print(f"  GRIPPER_CLOSE: {GRIPPER_CLOSE}")
print(f"  FINGER_FRICTION: static={FINGER_STATIC_FRICTION}, dynamic={FINGER_DYNAMIC_FRICTION}")
print(f"  CABLE_FRICTION: static={CABLE_STATIC_FRICTION}, dynamic={CABLE_DYNAMIC_FRICTION}")
print(f"  LIFT_NUM_STEPS: {LIFT_NUM_STEPS}")
print(f"  TRANSITION_NUM_STEPS: {TRANSITION_NUM_STEPS}")
print(f"  PHASE67_NUM_STEPS: {PHASE67_NUM_STEPS}")
print(f"  Z_OFFSET: {Z_OFFSET}")
print(f"  ENABLE_CONTINUOUS_CYCLE: {ENABLE_CONTINUOUS_CYCLE}")
print(f"  MAX_CYCLES: {MAX_CYCLES}")

print(f"\nPhase Waypoints:")
print(f"  Phase 1 (Hover):     L={WAYPOINT_PHASE1_LEFT}, R={WAYPOINT_PHASE1_RIGHT}")
print(f"  Phase 2 (Grasp):     L={WAYPOINT_PHASE2_LEFT}, R={WAYPOINT_PHASE2_RIGHT}")
print(f"  Phase 3 (Lift):      L={WAYPOINT_PHASE3_LEFT}, R={WAYPOINT_PHASE3_RIGHT}")
print(f"  Phase 4 (Hook):      L={WAYPOINT_PHASE4_LEFT}, R={WAYPOINT_PHASE4_RIGHT}")
print(f"  Phase 4.5 (Inter):   L={WAYPOINT_PHASE45_LEFT}, R={WAYPOINT_PHASE45_RIGHT}")
print(f"  Phase 5 (Place):     L={WAYPOINT_PHASE5_LEFT}, R={WAYPOINT_PHASE5_RIGHT}")
print(f"  Phase 6 (Retreat):   L={WAYPOINT_PHASE6_LEFT}, R={WAYPOINT_PHASE6_RIGHT}")
print(f"  Phase 7 (Home):      L={WAYPOINT_PHASE7_LEFT}, R={WAYPOINT_PHASE7_RIGHT}")
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

def run_diff_ik_transition(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                           target_waypoint_left, target_waypoint_right, num_steps, phase_name,
                           gripper_val=GRIPPER_CLOSE, track_contact=True, log_interval=100):
    """Run cumulative Diff IK transition between phases"""

    # Apply Z offset to targets
    target_left = torch.tensor(
        [[target_waypoint_left[0], target_waypoint_left[1], target_waypoint_left[2] + Z_OFFSET]],
        device=device, dtype=torch.float32
    )
    target_right = torch.tensor(
        [[target_waypoint_right[0], target_waypoint_right[1], target_waypoint_right[2] + Z_OFFSET]],
        device=device, dtype=torch.float32
    )

    # Reset IK controllers
    diff_ik_left.reset()
    diff_ik_right.reset()

    # Tracking variables
    min_force = float('inf')
    max_joint_change = 0.0
    contact_lost_step = None
    consecutive_low_force = 0
    prev_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().copy()

    print(f"\n{'Step':>5} | {'EE L Y':>7} | {'EE R Y':>7} | {'Force L':>8} | {'Force R':>8} | {'Max dJ':>7} | Status")
    print("-" * 80)

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Linear interpolation
        target_pos_left = start_pos_left + alpha * (target_left - start_pos_left)
        target_pos_right = start_pos_right + alpha * (target_right - start_pos_right)

        # Create command
        command_left = torch.cat([target_pos_left, start_quat_left], dim=1)
        command_right = torch.cat([target_pos_right, start_quat_right], dim=1)

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
        target_left_joints[0, -2:] = gripper_val
        robot_left.set_joint_position_target(target_left_joints)
        robot_left.write_data_to_sim()

        target_right_joints = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        target_right_joints[0, :7] = joint_cmd_right[0]
        target_right_joints[0, -2:] = gripper_val
        robot_right.set_joint_position_target(target_right_joints)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # Track joint change
        curr_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy()
        joint_change = np.abs(curr_joints_right - prev_joints_right) * 180 / np.pi
        step_max_change = np.max(joint_change)
        if step_max_change > max_joint_change:
            max_joint_change = step_max_change
        prev_joints_right = curr_joints_right.copy()

        # Get current state
        ee_l = get_ee_pos(robot_left, jacobian_body_left)
        ee_r = get_ee_pos(robot_right, jacobian_body_right)
        force_l = get_contact_force(contact_left)
        force_r = get_contact_force(contact_right)

        # Track force
        if track_contact and (force_l > 0 or force_r > 0):
            curr_min = min(force_l, force_r) if force_l > 0 and force_r > 0 else max(force_l, force_r)
            if curr_min < min_force:
                min_force = curr_min

        # Contact loss detection
        status = "OK"
        if track_contact:
            if force_l < 1.0 and force_r < 1.0:
                consecutive_low_force += 1
                if consecutive_low_force >= CONTACT_LOST_THRESHOLD and contact_lost_step is None:
                    contact_lost_step = i - CONTACT_LOST_THRESHOLD + 1
                    status = "*** LOST ***"
                elif contact_lost_step is not None:
                    status = "lost"
                else:
                    status = f"low({consecutive_low_force})"
            else:
                consecutive_low_force = 0
                if contact_lost_step is not None:
                    status = "recovered?"

        # Log
        if i % log_interval == 0 or status == "*** LOST ***" or i == num_steps - 1:
            print(f"{i:>5} | {ee_l[1]:>7.4f} | {ee_r[1]:>7.4f} | {force_l:>7.2f}N | {force_r:>7.2f}N | {step_max_change:>6.2f}° | {status}")

    # Get final state
    final_ee_left = get_ee_pos(robot_left, jacobian_body_left)
    final_ee_right = get_ee_pos(robot_right, jacobian_body_right)
    final_ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    final_ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    final_ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    final_ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Calculate error
    target_with_offset_left = np.array([target_waypoint_left[0], target_waypoint_left[1], target_waypoint_left[2] + Z_OFFSET])
    target_with_offset_right = np.array([target_waypoint_right[0], target_waypoint_right[1], target_waypoint_right[2] + Z_OFFSET])
    ee_error_left = np.linalg.norm(final_ee_left - target_with_offset_left) * 100
    ee_error_right = np.linalg.norm(final_ee_right - target_with_offset_right) * 100

    return {
        "ee_left": final_ee_left,
        "ee_right": final_ee_right,
        "ee_pos_left_tensor": final_ee_pos_left,
        "ee_quat_left_tensor": final_ee_quat_left,
        "ee_pos_right_tensor": final_ee_pos_right,
        "ee_quat_right_tensor": final_ee_quat_right,
        "ee_error_left_cm": ee_error_left,
        "ee_error_right_cm": ee_error_right,
        "force_left": get_contact_force(contact_left),
        "force_right": get_contact_force(contact_right),
        "cable_z": get_cable_center_z(),
        "min_force": min_force,
        "max_joint_change": max_joint_change,
        "contact_lost_step": contact_lost_step,
        "grasp_maintained": contact_lost_step is None
    }


def execute_cycle(cycle_num):
    """Execute one complete cycle (Phase 1 -> 7)"""
    print(f"\n{'#' * 70}")
    print(f"# CYCLE {cycle_num + 1}")
    print(f"{'#' * 70}")

    cycle_result = {"cycle": cycle_num + 1}

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

    print(f"  Closing grippers...")
    for i in range(300):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    print("  Stabilizing grasp...")
    for _ in range(100):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    phase2_force_l = get_contact_force(contact_left)
    phase2_force_r = get_contact_force(contact_right)
    phase2_cable_z = get_cable_center_z()
    grasp_success = phase2_force_l > 5.0 and phase2_force_r > 5.0

    print(f"\nPhase 2 State:")
    print(f"  Force: L={phase2_force_l:.2f}N, R={phase2_force_r:.2f}N")
    print(f"  Grasp: {'SUCCESS' if grasp_success else 'FAIL'}")

    cycle_result["grasp_success"] = grasp_success

    # ============================================================
    # PHASE 3: LIFT
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 3: LIFT")
    print("=" * 70)

    # Pre-lift stabilization
    for _ in range(50):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    phase2_ee_pos_left_tensor = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    phase2_ee_quat_left_tensor = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    phase2_ee_pos_right_tensor = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    phase2_ee_quat_right_tensor = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    lift_amount_m = LIFT_TARGET_CM / 100.0
    target_phase3_left = phase2_ee_pos_left_tensor.clone()
    target_phase3_left[0, 2] += lift_amount_m
    target_phase3_right = phase2_ee_pos_right_tensor.clone()
    target_phase3_right[0, 2] += lift_amount_m

    start_ee_pos_left = phase2_ee_pos_left_tensor.clone()
    start_ee_pos_right = phase2_ee_pos_right_tensor.clone()

    diff_ik_left.reset()
    diff_ik_right.reset()

    contact_lost_step_lift = None
    consecutive_low_force = 0

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

        force_l = get_contact_force(contact_left)
        force_r = get_contact_force(contact_right)

        if force_l < 1.0 and force_r < 1.0:
            consecutive_low_force += 1
            if consecutive_low_force >= CONTACT_LOST_THRESHOLD and contact_lost_step_lift is None:
                contact_lost_step_lift = i - CONTACT_LOST_THRESHOLD + 1
        else:
            consecutive_low_force = 0

    phase3_cable_z = get_cable_center_z()
    cable_lift = (phase3_cable_z - phase2_cable_z) * 100 if not np.isnan(phase3_cable_z) and not np.isnan(phase2_cable_z) else float('nan')
    lift_success = cable_lift > 3.0 if not np.isnan(cable_lift) else False
    grasp_maintained_phase3 = contact_lost_step_lift is None

    print(f"\nPhase 3 State:")
    print(f"  Cable Lift: {cable_lift:.2f}cm")
    print(f"  Lift: {'SUCCESS' if lift_success else 'FAIL'}")
    print(f"  Grasp: {'MAINTAINED' if grasp_maintained_phase3 else 'LOST'}")

    phase3_ee_pos_left_tensor = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    phase3_ee_quat_left_tensor = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    phase3_ee_pos_right_tensor = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    phase3_ee_quat_right_tensor = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    cycle_result["lift_success"] = lift_success
    cycle_result["grasp_maintained_phase3"] = grasp_maintained_phase3

    # ============================================================
    # PHASE 4: HOOK APPROACH
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 4: HOOK APPROACH")
    print("=" * 70)

    phase4_result = run_diff_ik_transition(
        phase3_ee_pos_left_tensor, phase3_ee_pos_right_tensor,
        phase3_ee_quat_left_tensor, phase3_ee_quat_right_tensor,
        WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
        TRANSITION_NUM_STEPS, "Phase 4"
    )

    print(f"\nPhase 4 State: EE Error L={phase4_result['ee_error_left_cm']:.2f}cm, R={phase4_result['ee_error_right_cm']:.2f}cm")

    # ============================================================
    # PHASE 4.5: INTERMEDIATE
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 4.5: INTERMEDIATE")
    print("=" * 70)

    phase45_result = run_diff_ik_transition(
        phase4_result["ee_pos_left_tensor"], phase4_result["ee_pos_right_tensor"],
        phase4_result["ee_quat_left_tensor"], phase4_result["ee_quat_right_tensor"],
        WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
        TRANSITION_NUM_STEPS, "Phase 4.5"
    )

    print(f"\nPhase 4.5 State: EE Error L={phase45_result['ee_error_left_cm']:.2f}cm, R={phase45_result['ee_error_right_cm']:.2f}cm")

    # ============================================================
    # PHASE 5: CABLE PLACEMENT
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 5: CABLE PLACEMENT")
    print("=" * 70)

    phase5_result = run_diff_ik_transition(
        phase45_result["ee_pos_left_tensor"], phase45_result["ee_pos_right_tensor"],
        phase45_result["ee_quat_left_tensor"], phase45_result["ee_quat_right_tensor"],
        WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
        TRANSITION_NUM_STEPS, "Phase 5"
    )

    print(f"\nPhase 5 State: EE Error L={phase5_result['ee_error_left_cm']:.2f}cm, R={phase5_result['ee_error_right_cm']:.2f}cm")

    # ============================================================
    # PHASE 6: RELEASE AND RETREAT
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 6: RELEASE AND RETREAT")
    print("=" * 70)

    # Open grippers
    print("\n  Opening grippers...")
    phase5_joints_left = robot_left.data.joint_pos[0, :7].cpu().numpy().tolist()
    phase5_joints_right = robot_right.data.joint_pos[0, :7].cpu().numpy().tolist()

    for _ in range(200):
        set_robot_joints(robot_left, phase5_joints_left, GRIPPER_OPEN)
        set_robot_joints(robot_right, phase5_joints_right, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    # Retreat
    print("\n  Retreating...")
    retreat_start_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    retreat_start_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    retreat_start_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    retreat_start_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    phase6_result = run_diff_ik_transition(
        retreat_start_pos_left, retreat_start_pos_right,
        retreat_start_quat_left, retreat_start_quat_right,
        WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
        TRANSITION_NUM_STEPS, "Phase 6",
        gripper_val=GRIPPER_OPEN,
        track_contact=False
    )

    final_cable_z = get_cable_center_z()
    cable_on_hook = final_cable_z > 0.80

    print(f"\nPhase 6 State:")
    print(f"  Final Cable Z: {final_cable_z:.4f}")
    print(f"  Cable on hook: {'YES' if cable_on_hook else 'NO'}")

    cycle_result["cable_on_hook"] = cable_on_hook

    # ============================================================
    # PHASE 7: RETURN TO HOME
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 7: RETURN TO HOME")
    print("=" * 70)

    phase7_result = run_diff_ik_transition(
        phase6_result["ee_pos_left_tensor"], phase6_result["ee_pos_right_tensor"],
        phase6_result["ee_quat_left_tensor"], phase6_result["ee_quat_right_tensor"],
        WAYPOINT_PHASE7_LEFT, WAYPOINT_PHASE7_RIGHT,
        PHASE67_NUM_STEPS, "Phase 7",
        gripper_val=GRIPPER_OPEN,
        track_contact=False
    )

    print(f"\nPhase 7 State:")
    print(f"  EE Left Error:  {phase7_result['ee_error_left_cm']:.2f}cm")
    print(f"  EE Right Error: {phase7_result['ee_error_right_cm']:.2f}cm")

    phase7_ee_ok = phase7_result['ee_error_left_cm'] < 2.0 and phase7_result['ee_error_right_cm'] < 2.0
    cycle_result["phase7_success"] = phase7_ee_ok

    print(f"  Home position: {'SUCCESS' if phase7_ee_ok else 'FAIL'}")

    return cycle_result


def execute_phase8_cycle_reset():
    """Execute Phase 8: Cycle reset"""
    print("\n" + "=" * 70)
    print("PHASE 8: CYCLE RESET")
    print("=" * 70)

    # 1. Verify grippers are open
    print("\n  Verifying gripper state...")
    for _ in range(50):
        set_robot_joints(robot_left, PHASE7_LEFT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, PHASE7_RIGHT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    # 2. Note: In a full implementation, cable would be reset here
    # For now, we just wait for stabilization
    print(f"\n  Stabilization ({CYCLE_RESET_STABILIZATION_STEPS} steps)...")
    for _ in range(CYCLE_RESET_STABILIZATION_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    cable_z = get_cable_center_z()
    print(f"\n  Cable Z after reset: {cable_z:.4f}")

    # 3. Ready for next cycle
    print("\n  Phase 8 complete - ready for next cycle")

    return True


# ============================================================
# MAIN EXECUTION
# ============================================================
print("\n" + "#" * 70)
print("# STARTING MULTI-CYCLE TEST")
print(f"# MAX_CYCLES: {MAX_CYCLES}")
print("#" * 70)

cycle_count = 0
all_cycles_passed = True

while cycle_count < MAX_CYCLES:
    # Execute one complete cycle
    cycle_result = execute_cycle(cycle_count)
    results["cycles"].append(cycle_result)

    # Check if cycle was successful
    cycle_passed = (
        cycle_result.get("grasp_success", False) and
        cycle_result.get("phase7_success", False)
    )

    if not cycle_passed:
        print(f"\n⚠️ Cycle {cycle_count + 1} had issues, continuing anyway...")
        all_cycles_passed = False

    cycle_count += 1

    # Execute Phase 8 (cycle reset) if not last cycle
    if cycle_count < MAX_CYCLES and ENABLE_CONTINUOUS_CYCLE:
        if not execute_phase8_cycle_reset():
            print("\n❌ Phase 8 failed, stopping test")
            break

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY - Full Phase 1 -> 8 Multi-Cycle Test")
print("=" * 70)

print(f"\nCycles completed: {cycle_count}/{MAX_CYCLES}")

for i, cycle_res in enumerate(results["cycles"]):
    grasp = "✅" if cycle_res.get("grasp_success", False) else "❌"
    lift = "✅" if cycle_res.get("lift_success", False) else "❌"
    hook = "✅" if cycle_res.get("cable_on_hook", False) else "❌"
    home = "✅" if cycle_res.get("phase7_success", False) else "❌"
    print(f"  Cycle {i+1}: Grasp={grasp} Lift={lift} Hook={hook} Home={home}")

results["overall"] = {
    "cycles_completed": cycle_count,
    "all_cycles_passed": all_cycles_passed
}

print("\n" + "=" * 70)
if all_cycles_passed and cycle_count == MAX_CYCLES:
    print("✅ OVERALL: SUCCESS - All cycles completed!")
else:
    print("❌ OVERALL: Some issues encountered")
print("=" * 70)

simulation_app.close()
