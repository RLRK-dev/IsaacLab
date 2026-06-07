#!/usr/bin/env python3
"""
Cable NaN Diagnostic Script
============================

Detailed logging of all 20 cable segments during lift to identify:
1. Which segment becomes NaN first
2. At which step NaN occurs
3. Position/velocity patterns before NaN

Usage:
    DISPLAY=:1 CUDA_VISIBLE_DEVICES=0 timeout 180 env_isaaclab/bin/python \
        thread_isaac_lab/scripts/diagnose_cable_nan.py 2>&1 | tee /tmp/cable_nan_diag.log
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
args.enable_cameras = True  # Required: DualArmSceneCfg contains camera definitions
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    GRIPPER_CLOSE, GRIPPER_OPEN,
)

# Diagnostic parameters
LIFT_CM = 10.0
LIFT_STEPS = 800
GRASP_CLOSE_STEPS = 100
STABILIZE_STEPS = 50

print("=" * 70)
print("CABLE NaN DIAGNOSTIC")
print("=" * 70)

# Setup simulation (same pattern as collect_demo_data.py)
device = "cuda:0"
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)

# Create scene config
scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)
sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]

# Get cable segment count
num_segments = cable.data.body_pos_w.shape[1]
print(f"[Info] Cable has {num_segments} segments")

# Diff IK setup
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


def check_cable_nan_detailed():
    """Check each segment for NaN and return details."""
    pos = cable.data.body_pos_w[0]  # (num_segments, 3)
    vel = cable.data.body_lin_vel_w[0]  # (num_segments, 3)

    nan_segments = []
    for i in range(num_segments):
        pos_nan = torch.any(torch.isnan(pos[i])).item()
        vel_nan = torch.any(torch.isnan(vel[i])).item()
        if pos_nan or vel_nan:
            nan_segments.append({
                'seg': i,
                'pos_nan': pos_nan,
                'vel_nan': vel_nan,
                'pos': pos[i].cpu().numpy() if not pos_nan else [float('nan')]*3,
                'vel': vel[i].cpu().numpy() if not vel_nan else [float('nan')]*3,
            })
    return nan_segments


def log_cable_state(step, phase=""):
    """Log all segment positions and velocities."""
    pos = cable.data.body_pos_w[0].cpu().numpy()  # (num_segments, 3)
    vel = cable.data.body_lin_vel_w[0].cpu().numpy()

    # Check for NaN
    nan_segs = check_cable_nan_detailed()
    if nan_segs:
        print(f"\n{'!'*70}")
        print(f"[STEP {step}] {phase} - NaN DETECTED!")
        for info in nan_segs:
            print(f"  Segment {info['seg']}: pos_nan={info['pos_nan']}, vel_nan={info['vel_nan']}")
        print(f"{'!'*70}\n")
        return True  # NaN found

    # Log summary statistics
    z_positions = pos[:, 2]
    z_velocities = vel[:, 2]
    speeds = np.linalg.norm(vel, axis=1)

    print(f"[Step {step:4d}] {phase:15s} | "
          f"Z: min={z_positions.min():.4f} max={z_positions.max():.4f} | "
          f"Vz: min={z_velocities.min():+.4f} max={z_velocities.max():+.4f} | "
          f"Speed: max={speeds.max():.4f}")

    return False  # No NaN


def log_cable_full_state(step, phase=""):
    """Log complete state of all segments."""
    pos = cable.data.body_pos_w[0].cpu().numpy()
    vel = cable.data.body_lin_vel_w[0].cpu().numpy()

    print(f"\n[Step {step}] {phase} - FULL CABLE STATE:")
    print(f"{'Seg':>4} | {'X':>8} {'Y':>8} {'Z':>8} | {'Vx':>8} {'Vy':>8} {'Vz':>8} | {'Speed':>8}")
    print("-" * 80)
    for i in range(num_segments):
        speed = np.linalg.norm(vel[i])
        print(f"{i:4d} | {pos[i,0]:8.4f} {pos[i,1]:8.4f} {pos[i,2]:8.4f} | "
              f"{vel[i,0]:+8.4f} {vel[i,1]:+8.4f} {vel[i,2]:+8.4f} | {speed:8.4f}")


def set_robot_joints(robot, arm_joints, gripper_val):
    """Set robot joint positions."""
    state = robot.data.joint_pos[0].unsqueeze(0).clone()
    state[0, :7] = torch.tensor(arm_joints, device=device)
    state[0, -2:] = gripper_val
    robot.write_joint_state_to_sim(state, robot.data.joint_vel[0].unsqueeze(0))


# Initialize robots to grasp position
print("\n[Phase 1] Moving to grasp position...")
set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)

for _ in range(STABILIZE_STEPS):
    sim.step()
    scene.update(sim.get_physics_dt())

# Log initial cable state
log_cable_full_state(0, "INITIAL")

# Grasp
print("\n[Phase 2] Closing grippers...")
for i in range(GRASP_CLOSE_STEPS):
    alpha = (i + 1) / GRASP_CLOSE_STEPS
    grip = GRIPPER_OPEN + alpha * (GRIPPER_CLOSE - GRIPPER_OPEN)

    tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    tgt_l[0, -2:] = grip
    robot_left.set_joint_position_target(tgt_l)
    robot_left.write_data_to_sim()

    tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    tgt_r[0, -2:] = grip
    robot_right.set_joint_position_target(tgt_r)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    if i % 25 == 0:
        log_cable_state(i, "GRASP")

# Stabilize after grasp
print("\n[Phase 2.5] Stabilizing grasp...")
for i in range(STABILIZE_STEPS):
    sim.step()
    scene.update(sim.get_physics_dt())

log_cable_full_state(0, "POST-GRASP")

# Get current EE positions for lift
p2_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
p2_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
p2_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
p2_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

# Lift targets
p3_target_l = p2_pos_l.clone()
p3_target_l[0, 2] += LIFT_CM / 100.0
p3_target_r = p2_pos_r.clone()
p3_target_r[0, 2] += LIFT_CM / 100.0

print(f"\n[Phase 3] LIFT ({LIFT_CM}cm over {LIFT_STEPS} steps)")
print(f"  Start EE L: {p2_pos_l[0].cpu().numpy()}")
print(f"  Start EE R: {p2_pos_r[0].cpu().numpy()}")
print(f"  Target EE L: {p3_target_l[0].cpu().numpy()}")
print(f"  Target EE R: {p3_target_r[0].cpu().numpy()}")
print()

# Reset Diff IK
diff_ik_left.reset()
diff_ik_right.reset()

nan_detected = False
nan_step = -1
last_good_state = None

for i in range(LIFT_STEPS):
    alpha = (i + 1) / LIFT_STEPS

    pos_left = p2_pos_l + alpha * (p3_target_l - p2_pos_l)
    pos_right = p2_pos_r + alpha * (p3_target_r - p2_pos_r)

    cmd_left = torch.cat([pos_left, p2_quat_l], dim=1)
    cmd_right = torch.cat([pos_right, p2_quat_r], dim=1)

    diff_ik_left.set_command(cmd_left)
    diff_ik_right.set_command(cmd_right)

    jac_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jac_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

    ee_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right]

    joint_pos_l = robot_left.data.joint_pos[:, :7]
    joint_pos_r = robot_right.data.joint_pos[:, :7]

    joint_cmd_l = diff_ik_left.compute(ee_pos_l, ee_quat_l, jac_left, joint_pos_l)
    joint_cmd_r = diff_ik_right.compute(ee_pos_r, ee_quat_r, jac_right, joint_pos_r)

    tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    tgt_l[0, :7] = joint_cmd_l[0]
    tgt_l[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(tgt_l)
    robot_left.write_data_to_sim()

    tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    tgt_r[0, :7] = joint_cmd_r[0]
    tgt_r[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(tgt_r)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    # Check for NaN every step
    nan_segs = check_cable_nan_detailed()
    if nan_segs and not nan_detected:
        nan_detected = True
        nan_step = i
        print(f"\n{'='*70}")
        print(f"NaN FIRST DETECTED AT STEP {i}")
        print(f"{'='*70}")
        print(f"Affected segments:")
        for info in nan_segs:
            print(f"  Segment {info['seg']}: pos_nan={info['pos_nan']}, vel_nan={info['vel_nan']}")

        print(f"\nLast good state (step {i-1}):")
        if last_good_state is not None:
            pos, vel = last_good_state
            print(f"{'Seg':>4} | {'X':>8} {'Y':>8} {'Z':>8} | {'Vx':>8} {'Vy':>8} {'Vz':>8}")
            for j in range(num_segments):
                print(f"{j:4d} | {pos[j,0]:8.4f} {pos[j,1]:8.4f} {pos[j,2]:8.4f} | "
                      f"{vel[j,0]:+8.4f} {vel[j,1]:+8.4f} {vel[j,2]:+8.4f}")

        # Get EE positions
        ee_l = robot_left.data.body_pos_w[0, jacobian_body_left].cpu().numpy()
        ee_r = robot_right.data.body_pos_w[0, jacobian_body_right].cpu().numpy()
        print(f"\nEE positions at NaN:")
        print(f"  Left:  {ee_l}")
        print(f"  Right: {ee_r}")
        print(f"  Lift progress: {alpha*100:.1f}% ({alpha*LIFT_CM:.2f}cm)")
        break

    # Store last good state
    if not nan_segs:
        last_good_state = (
            cable.data.body_pos_w[0].cpu().numpy().copy(),
            cable.data.body_lin_vel_w[0].cpu().numpy().copy()
        )

    # Log every 50 steps or when speed is high
    if i % 50 == 0:
        log_cable_state(i, "LIFT")

if not nan_detected:
    print("\n[SUCCESS] No NaN detected during lift!")
    log_cable_full_state(LIFT_STEPS, "FINAL")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

simulation_app.close()
