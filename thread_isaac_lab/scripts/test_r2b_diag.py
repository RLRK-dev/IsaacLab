"""test_r2b_diag.py — R2b Ascend diagnosis: doubled steps to check convergence vs workspace limit.

Runs full pipeline up to R2b with n_steps doubled (1214 instead of 607).
Logs R2b right arm ee_error every 100 steps.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--output_dir", type=str, default="data/test_r2b_diag")
parser.add_argument("--headless", action="store_true", default=False)
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, device=args.device, enable_cameras=True)
sim_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    HOOK_X, HOOK_Y,
    ROUTE_SPEED_M_PER_STEP, ROUTE_IK_SUBSTEPS, ROUTE_MAX_STEPS,
    JOINT_VEL_LIMIT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
)

FINGERTIP_OFFSET = 0.1123
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001
LIFT_Z = 0.05
LIFT_STEPS = 200
CLOSE_STEPS = 100
SETTLE_STEPS = 50


def jt_ik_step(robot, jac_body, hand_body, target_pos, alpha, clip, device,
               vel_limit=None):
    ee_pos = robot.data.body_pos_w[:, hand_body, :3]
    error = target_pos - ee_pos
    jacobian = robot.root_physx_view.get_jacobians()[:, jac_body, :3, :7]
    dq = alpha * torch.bmm(jacobian.transpose(1, 2), error.unsqueeze(-1)).squeeze(-1)
    dq = dq.clamp(-clip, clip)
    if vel_limit is not None:
        dq = dq.clamp(-vel_limit, vel_limit)
    new_q = robot.data.joint_pos[:, :7] + dq
    nan_mask = torch.isnan(new_q).any(dim=1)
    return new_q, nan_mask


def apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx):
    tgt_l = robot_left.data.joint_pos.clone()
    tgt_l[env_idx, :7] = ik_l[env_idx]
    tgt_l[env_idx, 7] = finger_pos
    tgt_l[env_idx, 8] = finger_pos
    robot_left.set_joint_position_target(tgt_l)
    robot_left.write_data_to_sim()
    tgt_r = robot_right.data.joint_pos.clone()
    tgt_r[env_idx, :7] = ik_r[env_idx]
    tgt_r[env_idx, 7] = finger_pos
    tgt_r[env_idx, 8] = finger_pos
    robot_right.set_joint_position_target(tgt_r)
    robot_right.write_data_to_sim()


def main():
    device = f"cuda:{app_launcher.device_id}"
    print(f"[R2b-DIAG] Device: {device}")

    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=5.0)
    physx_cfg = sim_utils.PhysxCfg(
        solver_type=0,
        min_position_iteration_count=32,
        max_position_iteration_count=255,
        min_velocity_iteration_count=8,
        max_velocity_iteration_count=255,
        gpu_found_lost_pairs_capacity=2**23,
        gpu_total_aggregate_pairs_capacity=2**23,
    )
    sim_cfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT, render_interval=2, device=device,
        physx=physx_cfg,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()
    scene.reset()
    for _ in range(10):
        sim.step()
        scene.update(sim.get_physics_dt())

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]
    env_idx = 0
    N = 1

    # === R0: Teleport + Close + Lift ===
    p2_l = torch.tensor(PHASE2_LEFT_JOINTS, dtype=torch.float32, device=device)
    p2_r = torch.tensor(PHASE2_RIGHT_JOINTS, dtype=torch.float32, device=device)
    q_l = torch.zeros(N, 9, device=device)
    q_l[0, :7] = p2_l; q_l[0, 7] = GRIPPER_OPEN; q_l[0, 8] = GRIPPER_OPEN
    q_r = torch.zeros(N, 9, device=device)
    q_r[0, :7] = p2_r; q_r[0, 7] = GRIPPER_OPEN; q_r[0, 8] = GRIPPER_OPEN

    robot_left.write_joint_state_to_sim(q_l, torch.zeros_like(q_l))
    robot_right.write_joint_state_to_sim(q_r, torch.zeros_like(q_r))
    robot_left.set_joint_position_target(q_l)
    robot_right.set_joint_position_target(q_r)
    robot_left.write_data_to_sim()
    robot_right.write_data_to_sim()
    for _ in range(SETTLE_STEPS):
        sim.step(); scene.update(sim.get_physics_dt())

    hand_body_left = robot_left.find_bodies("panda_hand")[0][0]
    hand_body_right = robot_right.find_bodies("panda_hand")[0][0]
    jac_body_left = hand_body_left - 1
    jac_body_right = hand_body_right - 1

    # Close grippers
    grip_step = (GRIPPER_OPEN - GRIPPER_CLOSE) / CLOSE_STEPS
    grip_val = GRIPPER_OPEN
    for s in range(CLOSE_STEPS):
        grip_val = max(grip_val - grip_step, GRIPPER_CLOSE)
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[0, 7] = grip_val; tgt_l[0, 8] = grip_val
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[0, 7] = grip_val; tgt_r[0, 8] = grip_val
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        for _ in range(4):
            sim.step(); scene.update(sim.get_physics_dt())

    finger_pos = max(robot_left.data.joint_pos[0, 7].item(),
                     robot_right.data.joint_pos[0, 7].item(), 0.004)
    print(f"[R0] Grip done: {finger_pos*1000:.1f}mm")

    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[0, 7] = finger_pos; tgt_l[0, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[0, 7] = finger_pos; tgt_r[0, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        sim.step(); scene.update(sim.get_physics_dt())

    # Cable kinematic setup
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    kg_grip_z_0 = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                   robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
    kg_env_ids = torch.tensor([env_idx], dtype=torch.int32, device=device)

    # Lift
    print("[R0] Lifting 50mm...")
    ee_target_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_target_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_target_l[env_idx, 2] += LIFT_Z
    ee_target_r[env_idx, 2] += LIFT_Z
    for step in range(LIFT_STEPS):
        ik_l, _ = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                              ee_target_l, 10.0, 0.02, device)
        ik_r, _ = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                              ee_target_r, 10.0, 0.02, device)
        apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx)
        for _ in range(4):
            sim.step(); scene.update(sim.get_physics_dt())
            kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                        robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 2] += (kg_cur_z - kg_grip_z_0)
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
        z_err = max(abs(robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() - ee_target_l[env_idx, 2].item()),
                    abs(robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item() - ee_target_r[env_idx, 2].item()))
        if z_err < 0.002:
            print(f"[R0] Lift converged step {step}")
            break
    # settle
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l; tgt_l[env_idx, 7] = finger_pos; tgt_l[env_idx, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r; tgt_r[env_idx, 7] = finger_pos; tgt_r[env_idx, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        sim.step(); scene.update(sim.get_physics_dt())
        kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                    robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 2] += (kg_cur_z - kg_grip_z_0)
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)

    frozen_jp = cable.data.joint_pos.clone()
    frozen_jv = torch.zeros_like(frozen_jp)
    print(f"[R0] Lift done. Cable joints frozen.")

    # === R1: Route to hook XY ===
    approx_dx = HOOK_X - 0.295
    approx_dy = HOOK_Y - 0.001
    route_dist = math.sqrt(approx_dx**2 + approx_dy**2)
    n_route = max(int(route_dist / ROUTE_SPEED_M_PER_STEP), 10)
    n_route = min(n_route, ROUTE_MAX_STEPS)
    ee_ref_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_ref_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    mid_ref = (ee_ref_l[env_idx] + ee_ref_r[env_idx]) / 2.0

    print(f"[R1] Route {route_dist*1000:.1f}mm, {n_route} steps")
    for step in range(n_route):
        t = (step + 1) / n_route
        ee_tgt_l = ee_ref_l.clone()
        ee_tgt_l[env_idx, 0] += approx_dx * t
        ee_tgt_l[env_idx, 1] += approx_dy * t
        ee_tgt_r = ee_ref_r.clone()
        ee_tgt_r[env_idx, 0] += approx_dx * t
        ee_tgt_r[env_idx, 1] += approx_dy * t

        ik_l, _ = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                              ee_tgt_l, 10.0, 0.02, device, vel_limit=JOINT_VEL_LIMIT)
        ik_r, _ = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                              ee_tgt_r, 10.0, 0.02, device, vel_limit=JOINT_VEL_LIMIT)
        apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx)

        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step(); scene.update(sim.get_physics_dt())
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            mid_cur = (ee_cur_l + ee_cur_r) / 2.0
            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_ref[0].item())
            kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_ref[1].item())
            kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_ref[2].item())
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
            cable.write_joint_state_to_sim(frozen_jp, frozen_jv)

    # R1 settle
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l; tgt_l[env_idx, 7] = finger_pos; tgt_l[env_idx, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r; tgt_r[env_idx, 7] = finger_pos; tgt_r[env_idx, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        sim.step(); scene.update(sim.get_physics_dt())
        ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
        mid_cur = (ee_cur_l + ee_cur_r) / 2.0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_ref[0].item())
        kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_ref[1].item())
        kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_ref[2].item())
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
        cable.write_joint_state_to_sim(frozen_jp, frozen_jv)

    print(f"[R1] Done")

    # === R2a: Arm Separation (Phase 4.5) ===
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    mid_start = (ee_start_l[env_idx] + ee_start_r[env_idx]) / 2.0

    tgt_l_45 = torch.tensor(WAYPOINT_PHASE45_LEFT, device=device, dtype=torch.float32)
    tgt_r_45 = torch.tensor(WAYPOINT_PHASE45_RIGHT, device=device, dtype=torch.float32)
    dist_l = torch.norm(tgt_l_45 - ee_start_l[env_idx]).item()
    dist_r = torch.norm(tgt_r_45 - ee_start_r[env_idx]).item()
    n_2a = max(int(max(dist_l, dist_r) / ROUTE_SPEED_M_PER_STEP), 10)
    n_2a = min(n_2a, 1500)

    print(f"[R2a] Separation: {n_2a} steps (L={dist_l*1000:.0f}mm R={dist_r*1000:.0f}mm)")
    for step in range(n_2a):
        t = (step + 1) / n_2a
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx] = ee_start_l[env_idx] + (tgt_l_45 - ee_start_l[env_idx]) * t
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx] = ee_start_r[env_idx] + (tgt_r_45 - ee_start_r[env_idx]) * t

        ik_l, _ = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                              ee_tgt_l, 10.0, 0.02, device, vel_limit=JOINT_VEL_LIMIT)
        ik_r, _ = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                              ee_tgt_r, 10.0, 0.02, device, vel_limit=JOINT_VEL_LIMIT)
        apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx)

        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step(); scene.update(sim.get_physics_dt())
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            mid_cur = (ee_cur_l + ee_cur_r) / 2.0
            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_start[0].item())
            kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_start[1].item())
            kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_start[2].item())
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
            cable.write_joint_state_to_sim(frozen_jp, frozen_jv)

    # R2a settle
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l; tgt_l[env_idx, 7] = finger_pos; tgt_l[env_idx, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l); robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r; tgt_r[env_idx, 7] = finger_pos; tgt_r[env_idx, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r); robot_right.write_data_to_sim()
        sim.step(); scene.update(sim.get_physics_dt())
        ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
        mid_cur = (ee_cur_l + ee_cur_r) / 2.0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_start[0].item())
        kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_start[1].item())
        kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_start[2].item())
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
        cable.write_joint_state_to_sim(frozen_jp, frozen_jv)

    ee_r2a_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_r2a_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    print(f"[R2a] Done. L=({ee_r2a_l[0]:.4f},{ee_r2a_l[1]:.4f},{ee_r2a_l[2]:.4f}) "
          f"R=({ee_r2a_r[0]:.4f},{ee_r2a_r[1]:.4f},{ee_r2a_r[2]:.4f})")

    # === R2b: Ascend to Phase 5 — DOUBLED STEPS ===
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    mid_start = (ee_start_l[env_idx] + ee_start_r[env_idx]) / 2.0

    tgt_l_5 = torch.tensor(WAYPOINT_PHASE5_LEFT, device=device, dtype=torch.float32)
    tgt_r_5 = torch.tensor(WAYPOINT_PHASE5_RIGHT, device=device, dtype=torch.float32)
    dist_l = torch.norm(tgt_l_5 - ee_start_l[env_idx]).item()
    dist_r = torch.norm(tgt_r_5 - ee_start_r[env_idx]).item()

    # ORIGINAL: n_2b = max(int(max(dist_l, dist_r) / ROUTE_SPEED_M_PER_STEP), 10)
    # DOUBLED:
    n_2b_original = max(int(max(dist_l, dist_r) / ROUTE_SPEED_M_PER_STEP), 10)
    n_2b = n_2b_original * 2
    n_2b = min(n_2b, 1500)

    print(f"\n[R2b] Ascend: dist_L={dist_l*1000:.1f}mm dist_R={dist_r*1000:.1f}mm")
    print(f"[R2b] Steps: {n_2b_original} (original) → {n_2b} (doubled)")
    print(f"[R2b] Target L={WAYPOINT_PHASE5_LEFT} R={WAYPOINT_PHASE5_RIGHT}")

    # Detailed logging
    r2b_log = []

    for step in range(n_2b):
        t = (step + 1) / n_2b
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx] = ee_start_l[env_idx] + (tgt_l_5 - ee_start_l[env_idx]) * t
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx] = ee_start_r[env_idx] + (tgt_r_5 - ee_start_r[env_idx]) * t

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device, vel_limit=JOINT_VEL_LIMIT)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device, vel_limit=JOINT_VEL_LIMIT)

        if nan_l.any() or nan_r.any():
            continue

        apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx)

        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step(); scene.update(sim.get_physics_dt())
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            mid_cur = (ee_cur_l + ee_cur_r) / 2.0
            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_start[0].item())
            kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_start[1].item())
            kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_start[2].item())
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
            cable.write_joint_state_to_sim(frozen_jp, frozen_jv)

        # Log every 100 steps
        if step % 100 == 0 or step == n_2b - 1:
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            err_l = torch.norm(ee_cur_l - tgt_l_5).item()
            err_r = torch.norm(ee_cur_r - tgt_r_5).item()
            pos_r = [round(ee_cur_r[i].item(), 4) for i in range(3)]
            entry = {
                "step": step,
                "t": round(t, 3),
                "ee_err_l_mm": round(err_l * 1000, 1),
                "ee_err_r_mm": round(err_r * 1000, 1),
                "pos_r": pos_r,
            }
            r2b_log.append(entry)
            print(f"[R2b] step={step}/{n_2b} t={t:.3f} "
                  f"ee_err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm "
                  f"R_pos=({pos_r[0]},{pos_r[1]},{pos_r[2]})")

    # Final
    ee_final_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    err_l = torch.norm(ee_final_l - tgt_l_5).item()
    err_r = torch.norm(ee_final_r - tgt_r_5).item()

    # Stall detection: error change in last 200 steps
    if len(r2b_log) >= 3:
        last_entries = [e for e in r2b_log if e["step"] >= n_2b - 300]
        if len(last_entries) >= 2:
            err_change = abs(last_entries[-1]["ee_err_r_mm"] - last_entries[0]["ee_err_r_mm"])
        else:
            err_change = 999.0
    else:
        err_change = 999.0

    stalled = err_change < 1.0
    workspace_limit = (err_r * 1000 >= 25.0) and stalled

    print(f"\n[R2b] === DIAGNOSIS ===")
    print(f"[R2b] Final ee_err: L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm")
    print(f"[R2b] Last 200-step err_change (R): {err_change:.1f}mm")
    print(f"[R2b] Stalled: {stalled}")
    print(f"[R2b] Verdict: {'WORKSPACE_LIMIT' if workspace_limit else 'CONVERGENCE_OK' if err_r*1000 < 20 else 'SLOW_CONVERGENCE'}")

    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    diag = {
        "n_steps_original": n_2b_original,
        "n_steps_doubled": n_2b,
        "target_l": list(WAYPOINT_PHASE5_LEFT),
        "target_r": list(WAYPOINT_PHASE5_RIGHT),
        "final_ee_err_l_mm": round(err_l * 1000, 1),
        "final_ee_err_r_mm": round(err_r * 1000, 1),
        "final_pos_r": [round(ee_final_r[i].item(), 4) for i in range(3)],
        "last_200step_err_change_mm": round(err_change, 1),
        "stalled": stalled,
        "workspace_limit": workspace_limit,
        "verdict": "WORKSPACE_LIMIT" if workspace_limit else ("CONVERGENCE_OK" if err_r*1000 < 20 else "SLOW_CONVERGENCE"),
        "log": r2b_log,
    }
    with open(os.path.join(args.output_dir, "r2b_diag.json"), "w") as f:
        json.dump(diag, f, indent=2)
    print(f"\n[R2b] Saved: {args.output_dir}/r2b_diag.json")


if __name__ == "__main__":
    main()
