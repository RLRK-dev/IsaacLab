#!/usr/bin/env python3
"""
Simulation Step Profiler

Measures time breakdown per simulation step:
- Physics step (sim.step)
- IK computation (diff_ik.compute)
- State readback (Jacobian + body_pos)
- Command apply (set_joint_position_target + write_data_to_sim)
- Scene update (scene.update)
- Python overhead (everything else)

Usage:
  ./isaaclab.sh -p thread_isaac_lab/scripts/profile_sim_step.py --device cuda:0
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
parser.add_argument("--num_steps", type=int, default=500, help="Number of steps to profile")
parser.add_argument("--physics_dt", type=float, default=1/240, help="Physics timestep")
parser.add_argument("--render_interval", type=int, default=1, help="Render interval")
parser.add_argument("--label", type=str, default="default", help="Label for this run")
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import time
import torch
import numpy as np
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

import isaaclab.sim as sim_utils
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    GRIPPER_OPEN,
)

# --- Scene setup ---
sim_cfg = sim_utils.SimulationCfg(dt=args.physics_dt, render_interval=args.render_interval)
sim = sim_utils.SimulationContext(sim_cfg)
scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
device = robot_left.device


# --- IK setup ---
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

# --- Warmup (10 steps, not measured) ---
print("Warming up (10 steps)...")
for _ in range(10):
    sim.step()
    scene.update(sim.get_physics_dt())

# --- Set initial IK target (hold current pose) ---
ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left]
ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left]
ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right]
ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right]

hold_cmd_left = torch.cat([ee_pos_left, ee_quat_left], dim=1)
hold_cmd_right = torch.cat([ee_pos_right, ee_quat_right], dim=1)

# --- Profiling ---
NUM_STEPS = args.num_steps
timings = {
    "total": [],
    "state_readback": [],
    "ik_compute": [],
    "command_apply": [],
    "physics_step": [],
    "scene_update": [],
    "python_overhead": [],
}

print(f"\nProfiling {NUM_STEPS} steps with DiffIK (hold pose)...\n")

for i in range(NUM_STEPS):
    t_total_start = time.perf_counter_ns()

    # 1. State readback
    t0 = time.perf_counter_ns()
    jacobian_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jacobian_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]
    ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right]
    joint_pos_left = robot_left.data.joint_pos[:, :7]
    joint_pos_right = robot_right.data.joint_pos[:, :7]
    t1 = time.perf_counter_ns()
    timings["state_readback"].append(t1 - t0)

    # 2. IK computation
    t0 = time.perf_counter_ns()
    diff_ik_left.set_command(hold_cmd_left)
    diff_ik_right.set_command(hold_cmd_right)
    joint_cmd_left = diff_ik_left.compute(ee_pos_left, ee_quat_left, jacobian_left, joint_pos_left)
    joint_cmd_right = diff_ik_right.compute(ee_pos_right, ee_quat_right, jacobian_right, joint_pos_right)
    t1 = time.perf_counter_ns()
    timings["ik_compute"].append(t1 - t0)

    # 3. Command apply
    t0 = time.perf_counter_ns()
    target_left_joints = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left_joints[0, :7] = joint_cmd_left[0]
    target_left_joints[0, -2:] = GRIPPER_OPEN
    robot_left.set_joint_position_target(target_left_joints)
    robot_left.write_data_to_sim()

    target_right_joints = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right_joints[0, :7] = joint_cmd_right[0]
    target_right_joints[0, -2:] = GRIPPER_OPEN
    robot_right.set_joint_position_target(target_right_joints)
    robot_right.write_data_to_sim()
    t1 = time.perf_counter_ns()
    timings["command_apply"].append(t1 - t0)

    # 4. Physics step
    t0 = time.perf_counter_ns()
    sim.step()
    t1 = time.perf_counter_ns()
    timings["physics_step"].append(t1 - t0)

    # 5. Scene update
    t0 = time.perf_counter_ns()
    scene.update(sim.get_physics_dt())
    t1 = time.perf_counter_ns()
    timings["scene_update"].append(t1 - t0)

    t_total_end = time.perf_counter_ns()
    total = t_total_end - t_total_start
    measured = (timings["state_readback"][-1] + timings["ik_compute"][-1] +
                timings["command_apply"][-1] + timings["physics_step"][-1] +
                timings["scene_update"][-1])
    timings["total"].append(total)
    timings["python_overhead"].append(total - measured)

# --- Report ---
print("=" * 70)
print(f"PROFILING RESULTS: {args.label}")
print(f"  steps={NUM_STEPS}, dt={args.physics_dt:.6f}, render_interval={args.render_interval}")
print("=" * 70)

total_time_s = sum(timings["total"]) / 1e9
fps = NUM_STEPS / total_time_s

print(f"\nTotal time:  {total_time_s:.3f} s")
print(f"Avg FPS:     {fps:.1f}")
print(f"Avg step:    {total_time_s / NUM_STEPS * 1000:.2f} ms")
print()

print(f"{'Component':<20} {'Mean (ms)':>10} {'Std (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10} {'% of step':>10}")
print("-" * 70)

total_mean = np.mean(timings["total"])
for key in ["state_readback", "ik_compute", "command_apply", "physics_step", "scene_update", "python_overhead"]:
    arr = np.array(timings[key]) / 1e6  # ns -> ms
    pct = np.mean(timings[key]) / total_mean * 100
    print(f"{key:<20} {arr.mean():>10.3f} {arr.std():>10.3f} {arr.min():>10.3f} {arr.max():>10.3f} {pct:>9.1f}%")

print("-" * 70)
arr_total = np.array(timings["total"]) / 1e6
print(f"{'TOTAL':<20} {arr_total.mean():>10.3f} {arr_total.std():>10.3f} {arr_total.min():>10.3f} {arr_total.max():>10.3f} {'100.0%':>10}")

# --- Force exit (simulation_app.close() hangs) ---
import os
os._exit(0)
