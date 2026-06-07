#!/usr/bin/env python3
"""
IK Stability Test: verify DiffIK tracking accuracy under different solver settings.

Moves both arms through a trajectory and measures EE position error.
Compares baseline vs optimized solver settings.

Usage:
  POC_SOLVER_POS_ITERS=16 POC_SOLVER_VEL_ITERS=0 POC_PHYSICS_DT=0.008333 \
    python this_script.py --device cuda:0
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

import time
import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import GRIPPER_OPEN

# --- Config from env ---
physics_dt = float(os.environ.get("POC_PHYSICS_DT", str(1/240)))
solver_pos = os.environ.get("POC_SOLVER_POS_ITERS", "32")
solver_vel = os.environ.get("POC_SOLVER_VEL_ITERS", "4")
label = f"dt={physics_dt:.6f}({1/physics_dt:.0f}Hz) solver={solver_pos}/{solver_vel}"

print(f"\n=== IK Stability Test: {label} ===\n")

# --- Scene ---
sim_cfg = sim_utils.SimulationCfg(dt=physics_dt, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)
scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
device = robot_left.device

# --- IK ---
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose", use_relative_mode=False,
    ik_method="dls", ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

body_idx_left = robot_left.find_bodies("panda_hand")[0][0]
body_idx_right = robot_right.find_bodies("panda_hand")[0][0]

# --- Warmup ---
for _ in range(20):
    sim.step()
    scene.update(sim.get_physics_dt())

# --- Get initial EE positions ---
ee_pos_left_init = robot_left.data.body_pos_w[:, body_idx_left].clone()
ee_quat_left_init = robot_left.data.body_quat_w[:, body_idx_left].clone()
ee_pos_right_init = robot_right.data.body_pos_w[:, body_idx_right].clone()
ee_quat_right_init = robot_right.data.body_quat_w[:, body_idx_right].clone()

print(f"Initial EE Left:  {ee_pos_left_init[0].cpu().numpy()}")
print(f"Initial EE Right: {ee_pos_right_init[0].cpu().numpy()}")

# --- Define trajectory: move both arms down 5cm, across 5cm, then back ---
waypoints = [
    (np.array([0.0, 0.0, -0.05]), "down 5cm"),
    (np.array([0.0, 0.05, -0.05]), "down+Y 5cm"),
    (np.array([0.0, 0.05, 0.0]), "Y only"),
    (np.array([0.0, 0.0, 0.0]), "back to start"),
]

STEPS_PER_WP = 200
errors_per_wp = []
total_start = time.perf_counter()

for wp_idx, (offset, desc) in enumerate(waypoints):
    target_left = ee_pos_left_init.clone()
    target_right = ee_pos_right_init.clone()
    target_left[0] += torch.tensor(offset, device=device, dtype=torch.float32)
    # Mirror Y for right arm
    mirror_offset = offset.copy()
    mirror_offset[1] *= -1
    target_right[0] += torch.tensor(mirror_offset, device=device, dtype=torch.float32)

    cmd_left = torch.cat([target_left, ee_quat_left_init], dim=1)
    cmd_right = torch.cat([target_right, ee_quat_right_init], dim=1)

    diff_ik_left.reset()
    diff_ik_right.reset()

    step_errors = []
    for i in range(STEPS_PER_WP):
        # Read state
        jac_left = robot_left.root_physx_view.get_jacobians()[:, body_idx_left - 1, :, :7]
        jac_right = robot_right.root_physx_view.get_jacobians()[:, body_idx_right - 1, :, :7]
        ee_pos_l = robot_left.data.body_pos_w[:, body_idx_left]
        ee_quat_l = robot_left.data.body_quat_w[:, body_idx_left]
        ee_pos_r = robot_right.data.body_pos_w[:, body_idx_right]
        ee_quat_r = robot_right.data.body_quat_w[:, body_idx_right]
        jp_l = robot_left.data.joint_pos[:, :7]
        jp_r = robot_right.data.joint_pos[:, :7]

        # IK
        diff_ik_left.set_command(cmd_left)
        diff_ik_right.set_command(cmd_right)
        jcmd_l = diff_ik_left.compute(ee_pos_l, ee_quat_l, jac_left, jp_l)
        jcmd_r = diff_ik_right.compute(ee_pos_r, ee_quat_r, jac_right, jp_r)

        # Apply
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = jcmd_l[0]
        tgt_l[0, -2:] = GRIPPER_OPEN
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = jcmd_r[0]
        tgt_r[0, -2:] = GRIPPER_OPEN
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # Measure error
        ee_now_l = robot_left.data.body_pos_w[:, body_idx_left]
        ee_now_r = robot_right.data.body_pos_w[:, body_idx_right]
        err_l = torch.norm(ee_now_l - target_left).item() * 1000  # mm
        err_r = torch.norm(ee_now_r - target_right).item() * 1000
        step_errors.append((err_l, err_r))

    final_err_l, final_err_r = step_errors[-1]
    avg_err = np.mean([max(e) for e in step_errors[-20:]])  # last 20 steps avg
    errors_per_wp.append((desc, final_err_l, final_err_r, avg_err))
    print(f"  WP{wp_idx} [{desc:>15}]: final_err L={final_err_l:.2f}mm R={final_err_r:.2f}mm  avg_last20={avg_err:.2f}mm")

total_time = time.perf_counter() - total_start
total_steps = len(waypoints) * STEPS_PER_WP
fps = total_steps / total_time

# --- Summary ---
print(f"\n{'='*60}")
print(f"RESULTS: {label}")
print(f"{'='*60}")
print(f"Total steps: {total_steps}, Wall time: {total_time:.1f}s, FPS: {fps:.1f}")
print(f"Sim time: {total_steps * physics_dt:.2f}s")
print()
print(f"{'Waypoint':<20} {'ErrL (mm)':>10} {'ErrR (mm)':>10} {'AvgLast20':>10}")
print("-" * 50)
max_err = 0
for desc, el, er, avg in errors_per_wp:
    print(f"{desc:<20} {el:>10.2f} {er:>10.2f} {avg:>10.2f}")
    max_err = max(max_err, el, er)
print("-" * 50)
print(f"Max error: {max_err:.2f}mm")
if max_err < 5.0:
    print("PASS: IK tracking within 5mm tolerance")
else:
    print(f"WARN: IK tracking error {max_err:.2f}mm exceeds 5mm")

os._exit(0)
