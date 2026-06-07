"""test_r1_route.py — R1 Horizontal Route Test.

Tests horizontal cable transport after kinematic lift:
  R1a: 50mm horizontal move toward hook
  R1b: Full route to hook XY (~131mm)

Approach: Teleport → close → lift 50mm → horizontal move with kinematic cable.
Based on test_r0_lift.py.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import time

import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--output_dir", type=str, default="data/test_r1")
parser.add_argument("--headless", action="store_true", default=False)
parser.add_argument("--num_episodes", type=int, default=3)
parser.add_argument("--stage", type=str, default=None, help="Run only this stage (e.g. R1b_full)")
parser.add_argument("--record_video", action="store_true", default=False, help="Record overhead+front_left video")
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
    ROUTE_SPEED_M_PER_STEP, ROUTE_IK_SUBSTEPS, ROUTE_CONVERGENCE_M,
    ROUTE_MAX_STEPS, ROUTE_XY_SUCCESS_M, ROUTE_Z_MAINTAIN_M,
    JOINT_VEL_LIMIT,
)

# Constants
FINGERTIP_OFFSET = 0.1123
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001
LIFT_Z = 0.05  # 50mm lift (from R0)
LIFT_STEPS = 200
CLOSE_STEPS = 100
SETTLE_STEPS = 50


def jt_ik_step(robot, jac_body, hand_body, target_pos, alpha, clip, device,
               vel_limit=None, clamp_log=None):
    """Jacobian-Transpose IK step (position-only, 6DOF arm).

    Fix 2: If vel_limit is set, clamp per-joint delta to prevent
    singularity-triggered velocity spikes (e.g. wrist j5 at 2.6 rad/s).
    """
    ee_pos = robot.data.body_pos_w[:, hand_body, :3]
    error = target_pos - ee_pos
    jacobian = robot.root_physx_view.get_jacobians()[:, jac_body, :3, :7]
    dq = alpha * torch.bmm(jacobian.transpose(1, 2), error.unsqueeze(-1)).squeeze(-1)
    dq = dq.clamp(-clip, clip)

    # Fix 2: Joint velocity safety guard
    if vel_limit is not None:
        clamped_mask = (dq.abs() > vel_limit).any(dim=1)
        if clamped_mask.any():
            dq = dq.clamp(-vel_limit, vel_limit)
            if clamp_log is not None:
                # Record which joints were clamped
                clamp_log.append(True)
            # Don't return nan — the clamped result is valid
        elif clamp_log is not None:
            clamp_log.append(False)

    new_q = robot.data.joint_pos[:, :7] + dq
    nan_mask = torch.isnan(new_q).any(dim=1)
    return new_q, nan_mask


def do_lift(sim, scene, device, robot_left, robot_right, cable,
            hand_body_left, hand_body_right, jac_body_left, jac_body_right,
            finger_pos, env_origin, kg_root_pose_0, kg_grip_z_0, kg_env_ids):
    """Lift phase (same as R0)."""
    env_idx = 0

    ee_target_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_target_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_target_l[env_idx, 2] += LIFT_Z
    ee_target_r[env_idx, 2] += LIFT_Z

    for step in range(LIFT_STEPS):
        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_target_l, 10.0, 0.02, device)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_target_r, 10.0, 0.02, device)
        if nan_l.any() or nan_r.any():
            print(f"  [LIFT] IK NaN at step {step}")
            break

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

        for _ in range(4):
            sim.step()
            scene.update(sim.get_physics_dt())
            kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                        robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
            kg_z_delta = kg_cur_z - kg_grip_z_0
            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 2] += kg_z_delta
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(
                torch.zeros(1, 6, device=device), env_ids=kg_env_ids)

        ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
        z_err_l = abs(ee_cur_l[env_idx, 2].item() - ee_target_l[env_idx, 2].item())
        z_err_r = abs(ee_cur_r[env_idx, 2].item() - ee_target_r[env_idx, 2].item())
        if z_err_l < 0.002 and z_err_r < 0.002:
            print(f"  [LIFT] Converged at step {step}")
            break

    # Settle
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l
        tgt_l[env_idx, 7] = finger_pos
        tgt_l[env_idx, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r
        tgt_r[env_idx, 7] = finger_pos
        tgt_r[env_idx, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                    robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
        kg_z_delta = kg_cur_z - kg_grip_z_0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 2] += kg_z_delta
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(
            torch.zeros(1, 6, device=device), env_ids=kg_env_ids)


def capture_frame(scene, cameras, frame_list):
    """Capture overhead + front_left into a side-by-side frame."""
    imgs = []
    for cam_name in cameras:
        cam = scene[cam_name]
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        if rgb.dtype != np.uint8:
            rgb = (rgb * 255).astype(np.uint8) if rgb.max() <= 1.0 else rgb.astype(np.uint8)
        imgs.append(rgb)
    # Side by side
    combined = np.concatenate(imgs, axis=1)
    frame_list.append(combined)


def save_video(frame_list, output_path, fps=30):
    """Save frames to MP4 via FFmpeg."""
    if not frame_list:
        return
    tmpdir = "/tmp/r1_video_frames"
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir)
    for i, frame in enumerate(frame_list):
        Image.fromarray(frame).save(os.path.join(tmpdir, f"frame_{i:06d}.jpg"), quality=85)
    cmd = [
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(tmpdir, "frame_%06d.jpg"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", output_path,
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(tmpdir)
    print(f"  [VIDEO] Saved {len(frame_list)} frames → {output_path}")


def do_route(sim, scene, device, robot_left, robot_right, cable,
             hand_body_left, hand_body_right, jac_body_left, jac_body_right,
             finger_pos, env_origin, route_dx, route_dy,
             kg_root_pose_0, kg_grip_z_0, kg_env_ids, frames=None, cameras=None):
    """Horizontal route phase: move both arms by (route_dx, route_dy) in XY.

    Fix 1: Cable kinematic transport — freeze cable joint state and move
    all segments together with root (prevents 471mm segment stretch).
    Fix 2: Joint velocity clamping via JOINT_VEL_LIMIT.
    """
    env_idx = 0
    route_dist = math.sqrt(route_dx**2 + route_dy**2)

    # Current EE positions
    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

    # Route target: shift both by (dx, dy), keep Z
    ee_end_l = ee_start_l.clone()
    ee_end_l[env_idx, 0] += route_dx
    ee_end_l[env_idx, 1] += route_dy
    ee_end_r = ee_start_r.clone()
    ee_end_r[env_idx, 0] += route_dx
    ee_end_r[env_idx, 1] += route_dy

    # Initial arm separation
    init_sep_y = abs(ee_start_l[env_idx, 1].item() - ee_start_r[env_idx, 1].item())

    # Number of interpolation steps based on speed
    n_interp = max(int(route_dist / ROUTE_SPEED_M_PER_STEP), 10)
    n_interp = min(n_interp, ROUTE_MAX_STEPS)

    print(f"  [ROUTE] Distance={route_dist*1000:.1f}mm, steps={n_interp}, "
          f"speed={route_dist/n_interp*1000:.2f}mm/step")
    print(f"  [ROUTE] Start L=({ee_start_l[env_idx,0]:.4f},{ee_start_l[env_idx,1]:.4f},{ee_start_l[env_idx,2]:.4f}) "
          f"R=({ee_start_r[env_idx,0]:.4f},{ee_start_r[env_idx,1]:.4f},{ee_start_r[env_idx,2]:.4f})")
    print(f"  [ROUTE] Target L=({ee_end_l[env_idx,0]:.4f},{ee_end_l[env_idx,1]:.4f},{ee_end_l[env_idx,2]:.4f}) "
          f"R=({ee_end_r[env_idx,0]:.4f},{ee_end_r[env_idx,1]:.4f},{ee_end_r[env_idx,2]:.4f})")

    # Fix 1: Freeze cable joint state at lift-complete shape
    frozen_cable_joint_pos = cable.data.joint_pos.clone()
    frozen_cable_joint_vel = torch.zeros_like(frozen_cable_joint_pos)
    print(f"  [ROUTE] Fix1: Cable joints frozen (shape={frozen_cable_joint_pos.shape})")

    # Fix 2: velocity clamp tracking
    clamp_log_l = []
    clamp_log_r = []

    ik_failures = 0
    max_sep_drift = 0.0
    z_vals = []

    for step in range(n_interp):
        t = (step + 1) / n_interp  # 0→1 linear interpolation

        # Interpolated targets
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx, 0] = ee_start_l[env_idx, 0] + route_dx * t
        ee_tgt_l[env_idx, 1] = ee_start_l[env_idx, 1] + route_dy * t
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx, 0] = ee_start_r[env_idx, 0] + route_dx * t
        ee_tgt_r[env_idx, 1] = ee_start_r[env_idx, 1] + route_dy * t

        # JT IK with Fix 2: joint velocity clamping
        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_l)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_r)
        if nan_l.any() or nan_r.any():
            ik_failures += 1
            if ik_failures > 10:
                print(f"  [ROUTE] Too many IK NaN ({ik_failures}), aborting at step {step}")
                break
            continue

        # Apply joint targets
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

        # Substeps + Fix 1: kinematic cable transport (root + frozen joints)
        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())

            # Cable root follows gripper midpoint in XY and Z
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            mid_xyz = (ee_cur_l + ee_cur_r) / 2.0

            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_xyz[0].item() -
                                (ee_start_l[env_idx, 0].item() + ee_start_r[env_idx, 0].item()) / 2.0)
            kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_xyz[1].item() -
                                (ee_start_l[env_idx, 1].item() + ee_start_r[env_idx, 1].item()) / 2.0)
            kg_cur_z = mid_xyz[2].item()
            kg_new_pose[0, 2] = kg_root_pose_0[2] + (kg_cur_z - kg_grip_z_0)
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(
                torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
            # Fix 1: Write frozen joint state to keep segments in place
            cable.write_joint_state_to_sim(frozen_cable_joint_pos, frozen_cable_joint_vel)

        # Track arm separation drift
        cur_sep_y = abs(robot_left.data.body_pos_w[env_idx, hand_body_left, 1].item() -
                        robot_right.data.body_pos_w[env_idx, hand_body_right, 1].item())
        sep_drift = abs(cur_sep_y - init_sep_y)
        max_sep_drift = max(max_sep_drift, sep_drift)

        # Track cable Z
        cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()
        if env_origin is not None:
            cable_z -= env_origin[2].item()
        z_vals.append(cable_z)

        # NaN check
        if torch.isnan(cable.data.body_pos_w).any():
            print(f"  [ROUTE] Cable NaN at step {step}!")
            break

        # Video capture (every 2nd step to balance quality vs file size)
        if frames is not None and cameras is not None and step % 2 == 0:
            capture_frame(scene, cameras, frames)

        # Progress log
        if step % (n_interp // 5 + 1) == 0 or step == n_interp - 1:
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            xy_err_l = math.sqrt((ee_cur_l[0].item() - ee_end_l[env_idx, 0].item())**2 +
                                 (ee_cur_l[1].item() - ee_end_l[env_idx, 1].item())**2)
            xy_err_r = math.sqrt((ee_cur_r[0].item() - ee_end_r[env_idx, 0].item())**2 +
                                 (ee_cur_r[1].item() - ee_end_r[env_idx, 1].item())**2)
            print(f"  [ROUTE] step={step}/{n_interp} t={t:.2f} xy_err L={xy_err_l*1000:.1f}mm "
                  f"R={xy_err_r*1000:.1f}mm sep_drift={sep_drift*1000:.1f}mm cable_z={cable_z:.4f}")

    # Settle at final position
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l
        tgt_l[env_idx, 7] = finger_pos
        tgt_l[env_idx, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r
        tgt_r[env_idx, 7] = finger_pos
        tgt_r[env_idx, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        # Maintain cable position
        ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
        mid_xyz = (ee_cur_l + ee_cur_r) / 2.0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_xyz[0].item() -
                            (ee_start_l[env_idx, 0].item() + ee_start_r[env_idx, 0].item()) / 2.0)
        kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_xyz[1].item() -
                            (ee_start_l[env_idx, 1].item() + ee_start_r[env_idx, 1].item()) / 2.0)
        kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_xyz[2].item() - kg_grip_z_0)
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(
            torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
        # Fix 1: maintain frozen cable joints during settle
        cable.write_joint_state_to_sim(frozen_cable_joint_pos, frozen_cable_joint_vel)

    # Fix 2 stats
    n_clamp_l = sum(1 for c in clamp_log_l if c)
    n_clamp_r = sum(1 for c in clamp_log_r if c)
    if n_clamp_l + n_clamp_r > 0:
        print(f"  [ROUTE] Fix2: vel clamp activated L={n_clamp_l} R={n_clamp_r} times")

    # Final measurements
    ee_final_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    mid_final = ((ee_final_l + ee_final_r) / 2.0)

    xy_err_l = math.sqrt((ee_final_l[0].item() - ee_end_l[env_idx, 0].item())**2 +
                         (ee_final_l[1].item() - ee_end_l[env_idx, 1].item())**2)
    xy_err_r = math.sqrt((ee_final_r[0].item() - ee_end_r[env_idx, 0].item())**2 +
                         (ee_final_r[1].item() - ee_end_r[env_idx, 1].item())**2)
    xy_err_avg = (xy_err_l + xy_err_r) / 2.0

    final_sep = abs(ee_final_l[1].item() - ee_final_r[1].item())
    sep_drift_final = abs(final_sep - init_sep_y)

    return {
        "xy_error_l_mm": round(xy_err_l * 1000, 2),
        "xy_error_r_mm": round(xy_err_r * 1000, 2),
        "xy_error_avg_mm": round(xy_err_avg * 1000, 2),
        "arm_separation_drift_mm": round(max_sep_drift * 1000, 2),
        "arm_separation_final_drift_mm": round(sep_drift_final * 1000, 2),
        "ik_failures": ik_failures,
        "route_steps_used": step + 1 if 'step' in dir() else 0,
        "final_pos_l": [round(ee_final_l[i].item(), 4) for i in range(3)],
        "final_pos_r": [round(ee_final_r[i].item(), 4) for i in range(3)],
        "final_midpoint": [round(mid_final[i].item(), 4) for i in range(3)],
        "fix2_vel_clamp_l": n_clamp_l,
        "fix2_vel_clamp_r": n_clamp_r,
    }


def run_episode(sim, scene, device, route_dx, route_dy, route_label, episode_idx, env_origin,
                record_video=False, output_dir=None):
    """Run one complete episode: teleport → close → lift → route."""
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]
    env_idx = 0
    N = 1

    # --- Teleport to Phase 2 joints ---
    p2_joints_l = torch.tensor(PHASE2_LEFT_JOINTS, dtype=torch.float32, device=device)
    p2_joints_r = torch.tensor(PHASE2_RIGHT_JOINTS, dtype=torch.float32, device=device)

    q_l = torch.zeros(N, 9, device=device)
    q_l[0, :7] = p2_joints_l
    q_l[0, 7] = GRIPPER_OPEN
    q_l[0, 8] = GRIPPER_OPEN
    q_r = torch.zeros(N, 9, device=device)
    q_r[0, :7] = p2_joints_r
    q_r[0, 7] = GRIPPER_OPEN
    q_r[0, 8] = GRIPPER_OPEN

    robot_left.write_joint_state_to_sim(q_l, torch.zeros_like(q_l))
    robot_right.write_joint_state_to_sim(q_r, torch.zeros_like(q_r))
    robot_left.set_joint_position_target(q_l)
    robot_right.set_joint_position_target(q_r)
    robot_left.write_data_to_sim()
    robot_right.write_data_to_sim()

    for _ in range(SETTLE_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    hand_body_left = robot_left.find_bodies("panda_hand")[0][0]
    hand_body_right = robot_right.find_bodies("panda_hand")[0][0]
    jac_body_left = hand_body_left - 1
    jac_body_right = hand_body_right - 1

    # Record cable Z before
    cable_z_before = cable.data.body_pos_w[env_idx, :, 2].clone()
    if env_origin is not None:
        cable_z_before = cable_z_before - env_origin[2]

    # --- Close grippers ---
    grip_step = (GRIPPER_OPEN - GRIPPER_CLOSE) / CLOSE_STEPS
    grip_val = GRIPPER_OPEN
    for s in range(CLOSE_STEPS):
        grip_val = max(grip_val - grip_step, GRIPPER_CLOSE)
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[0, 7] = grip_val
        tgt_l[0, 8] = grip_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[0, 7] = grip_val
        tgt_r[0, 8] = grip_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        for _ in range(4):
            sim.step()
            scene.update(sim.get_physics_dt())

    grip_l = robot_left.data.joint_pos[0, 7].item()
    grip_r = robot_right.data.joint_pos[0, 7].item()
    finger_pos = max(grip_l, grip_r, 0.004)
    print(f"  [CLOSE] Grip: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

    # Settle
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[0, 7] = finger_pos
        tgt_l[0, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[0, 7] = finger_pos
        tgt_r[0, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # --- Kinematic cable setup ---
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    kg_grip_z_0 = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                   robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
    kg_env_ids = torch.tensor([env_idx], dtype=torch.int32, device=device)

    # --- Lift 50mm ---
    print(f"  [LIFT] Starting 50mm lift...")
    do_lift(sim, scene, device, robot_left, robot_right, cable,
            hand_body_left, hand_body_right, jac_body_left, jac_body_right,
            finger_pos, env_origin, kg_root_pose_0, kg_grip_z_0, kg_env_ids)

    # Check cable Z after lift
    cable_z_after_lift = cable.data.body_pos_w[env_idx, :, 2].clone()
    if env_origin is not None:
        cable_z_after_lift = cable_z_after_lift - env_origin[2]
    lift_delta = (cable_z_after_lift - cable_z_before).mean().item()
    print(f"  [LIFT] cable_z_delta={lift_delta*1000:.1f}mm")

    ee_post_lift_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3].clone()
    ee_post_lift_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3].clone()
    print(f"  [LIFT] EE post-lift: L=({ee_post_lift_l[0]:.4f},{ee_post_lift_l[1]:.4f},{ee_post_lift_l[2]:.4f}) "
          f"R=({ee_post_lift_r[0]:.4f},{ee_post_lift_r[1]:.4f},{ee_post_lift_r[2]:.4f})")

    # --- Route ---
    print(f"  [ROUTE] Starting horizontal move: dx={route_dx*1000:.1f}mm dy={route_dy*1000:.1f}mm")
    frames = [] if record_video else None
    cameras = ["overhead_camera", "front_left_camera"] if record_video else None
    route_result = do_route(
        sim, scene, device, robot_left, robot_right, cable,
        hand_body_left, hand_body_right, jac_body_left, jac_body_right,
        finger_pos, env_origin, route_dx, route_dy,
        kg_root_pose_0, kg_grip_z_0, kg_env_ids, frames=frames, cameras=cameras)

    if record_video and frames and output_dir:
        vid_path = os.path.join(output_dir, f"{route_label}_ep{episode_idx}.mp4")
        save_video(frames, vid_path, fps=30)

    # Cable Z after route
    cable_z_after_route = cable.data.body_pos_w[env_idx, :, 2].clone()
    if env_origin is not None:
        cable_z_after_route = cable_z_after_route - env_origin[2]
    final_cable_z_delta = (cable_z_after_route - cable_z_before).mean().item()

    # Cable drop check: did cable Z drop significantly from lift?
    cable_nan = math.isnan(final_cable_z_delta)
    cable_drop = cable_nan or final_cable_z_delta < ROUTE_Z_MAINTAIN_M

    # Success criteria
    xy_ok = route_result["xy_error_avg_mm"] < ROUTE_XY_SUCCESS_M * 1000
    z_ok = not cable_drop
    success = xy_ok and z_ok

    print(f"  [RESULT] xy_err_avg={route_result['xy_error_avg_mm']:.1f}mm "
          f"cable_z_delta={final_cable_z_delta*1000:.1f}mm "
          f"sep_drift={route_result['arm_separation_drift_mm']:.1f}mm "
          f"ik_fail={route_result['ik_failures']} "
          f"{'PASS' if success else 'FAIL'}")

    return {
        "success": success,
        "xy_error_avg_mm": route_result["xy_error_avg_mm"],
        "xy_error_l_mm": route_result["xy_error_l_mm"],
        "xy_error_r_mm": route_result["xy_error_r_mm"],
        "cable_z_delta_mm": round(final_cable_z_delta * 1000, 2),
        "lift_delta_mm": round(lift_delta * 1000, 2),
        "arm_separation_drift_mm": route_result["arm_separation_drift_mm"],
        "ik_failures": route_result["ik_failures"],
        "cable_drop": cable_drop,
        "route_steps_used": route_result["route_steps_used"],
        "final_pos_l": route_result["final_pos_l"],
        "final_pos_r": route_result["final_pos_r"],
        "final_midpoint": route_result["final_midpoint"],
    }


def main():
    device = f"cuda:{app_launcher.device_id}"
    print(f"[R1] Horizontal Route Test")
    print(f"[R1] Device: {device}")
    print(f"[R1] Hook: ({HOOK_X}, {HOOK_Y})")

    # Scene setup
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

    env_origin = scene.env_origins[0] if hasattr(scene, 'env_origins') else None

    # Compute grasp midpoint after teleport (approximate from R0 data)
    # Will be computed precisely in first episode
    # Route full vector: grasp midpoint → hook XY
    # Grasp midpoint ≈ (0.295, 0.001, 0.915)
    # Hook: (0.35, 0.12)
    # Full dx ≈ 0.055, dy ≈ 0.119

    # Precise: get actual EE positions after teleport+lift
    # For now, compute from PHASE2 joints. Route direction is constant.
    # We'll compute dx/dy after the first teleport to get exact values.

    # R1a: 50mm horizontal (38% of full route ~131mm)
    # R1b: full route to hook XY
    # Direction vector: normalize (HOOK_X - 0.295, HOOK_Y - 0.001)
    approx_dx = HOOK_X - 0.295
    approx_dy = HOOK_Y - 0.001
    route_full_dist = math.sqrt(approx_dx**2 + approx_dy**2)
    dir_x = approx_dx / route_full_dist
    dir_y = approx_dy / route_full_dist

    stages = [
        ("R1a_50mm", 0.050 * dir_x, 0.050 * dir_y, 0.050),
        ("R1b_full", approx_dx, approx_dy, route_full_dist),
    ]
    if args.stage:
        stages = [(l, dx, dy, d) for l, dx, dy, d in stages if l == args.stage]

    all_results = {}
    t0 = time.time()

    # Scene layout info
    scene_layout = {
        "hook_pos": [HOOK_X, HOOK_Y, 0.80],
        "grasp_midpoint_approx": [0.295, 0.001, 0.915],
        "route_distance_mm": round(route_full_dist * 1000, 1),
        "route_direction_deg": round(math.degrees(math.atan2(approx_dy, approx_dx)), 1),
    }

    for label, dx, dy, dist in stages:
        print(f"\n{'='*60}")
        print(f"[R1] Stage {label}: dx={dx*1000:.1f}mm dy={dy*1000:.1f}mm dist={dist*1000:.1f}mm")
        print(f"{'='*60}")

        stage_episodes = []
        for ep in range(args.num_episodes):
            print(f"\n--- Episode {ep+1}/{args.num_episodes} ---")
            sim.reset()
            scene.reset()
            for _ in range(10):
                sim.step()
                scene.update(sim.get_physics_dt())

            result = run_episode(sim, scene, device, dx, dy, label, ep, env_origin,
                                record_video=args.record_video, output_dir=args.output_dir)
            stage_episodes.append(result)

        n_success = sum(1 for r in stage_episodes if r["success"])
        mean_xy = sum(r["xy_error_avg_mm"] for r in stage_episodes) / len(stage_episodes)
        mean_cz = sum(r["cable_z_delta_mm"] for r in stage_episodes) / len(stage_episodes)
        mean_sep = sum(r["arm_separation_drift_mm"] for r in stage_episodes) / len(stage_episodes)
        total_ik_fail = sum(r["ik_failures"] for r in stage_episodes)
        any_drop = any(r["cable_drop"] for r in stage_episodes)

        print(f"\n[R1] {label} SUMMARY: {n_success}/{len(stage_episodes)} success, "
              f"xy_err={mean_xy:.1f}mm, cable_z={mean_cz:.1f}mm, sep_drift={mean_sep:.1f}mm")

        all_results[label] = {
            "success_rate": f"{n_success}/{len(stage_episodes)}",
            "xy_error_mean_mm": round(mean_xy, 2),
            "cable_z_delta_mean_mm": round(mean_cz, 2),
            "arm_separation_drift_mm": round(mean_sep, 2),
            "ik_failures": total_ik_fail,
            "cable_drop": any_drop,
            "episodes": stage_episodes,
        }

    elapsed = time.time() - t0

    os.makedirs(args.output_dir, exist_ok=True)
    metrics = {
        "phase": "R1",
        "description": "Horizontal cable route — kinematic grasp + parallel arm move",
        "device": device,
        "num_episodes_per_stage": args.num_episodes,
        "scene_layout": scene_layout,
        **{k: {kk: vv for kk, vv in v.items() if kk != "episodes"}
           for k, v in all_results.items()},
        "stages_detail": all_results,
        "overall": "PASS" if all(
            all(r["success"] for r in stage["episodes"])
            for stage in all_results.values()
        ) else "FAIL",
        "elapsed_s": round(elapsed, 1),
    }

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[R1] Metrics saved: {metrics_path}")
    print(f"[R1] Total elapsed: {elapsed:.1f}s")
    print(f"[R1] Overall: {metrics['overall']}")


if __name__ == "__main__":
    main()
