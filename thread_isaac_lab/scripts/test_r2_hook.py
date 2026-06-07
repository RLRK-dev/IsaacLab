"""test_r2_hook.py — R2 Hook Placement Test (R2a→R2d).

Full pipeline: Teleport → Close → Lift → Route (R1b) → R2a-R2d.
  R2a: Arm Separation (Phase 4.5 — X-axis spread)
  R2b: Ascend to Hook Top (Phase 5 — Z=1.09)
  R2c: Descend + Cable Drape (Phase 5.5 — cable physics released)
  R2d: Release + Retreat (Phase 6 — gripper open, verify cable on hook)

Builds on test_r1_route.py infrastructure (jt_ik_step, do_lift, do_route).
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
parser.add_argument("--output_dir", type=str, default="data/test_r2")
parser.add_argument("--headless", action="store_true", default=False)
parser.add_argument("--num_episodes", type=int, default=3)
parser.add_argument("--record_video", action="store_true", default=False,
                    help="Record overhead+front_left video")
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
    HOOK_X, HOOK_Y, HOOK_Z,
    ROUTE_SPEED_M_PER_STEP, ROUTE_IK_SUBSTEPS,
    ROUTE_XY_SUCCESS_M, ROUTE_Z_MAINTAIN_M, ROUTE_MAX_STEPS,
    JOINT_VEL_LIMIT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS,
)

# Constants (from R0/R1)
FINGERTIP_OFFSET = 0.1123
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001
LIFT_Z = 0.05
LIFT_STEPS = 200
CLOSE_STEPS = 100
SETTLE_STEPS = 50


# ---------------------------------------------------------------------------
# Utility: JT IK step (from test_r1_route.py, with Fix 2)
# ---------------------------------------------------------------------------
def jt_ik_step(robot, jac_body, hand_body, target_pos, alpha, clip, device,
               vel_limit=None, clamp_log=None):
    """Jacobian-Transpose IK step (position-only, 6DOF arm)."""
    ee_pos = robot.data.body_pos_w[:, hand_body, :3]
    error = target_pos - ee_pos
    jacobian = robot.root_physx_view.get_jacobians()[:, jac_body, :3, :7]
    dq = alpha * torch.bmm(jacobian.transpose(1, 2), error.unsqueeze(-1)).squeeze(-1)
    dq = dq.clamp(-clip, clip)

    if vel_limit is not None:
        clamped_mask = (dq.abs() > vel_limit).any(dim=1)
        if clamped_mask.any():
            dq = dq.clamp(-vel_limit, vel_limit)
            if clamp_log is not None:
                clamp_log.append(True)
        elif clamp_log is not None:
            clamp_log.append(False)

    new_q = robot.data.joint_pos[:, :7] + dq
    nan_mask = torch.isnan(new_q).any(dim=1)
    return new_q, nan_mask


# ---------------------------------------------------------------------------
# Video utilities (from test_r1_route.py)
# ---------------------------------------------------------------------------
def capture_frame(scene, cameras, frame_list):
    imgs = []
    for cam_name in cameras:
        cam = scene[cam_name]
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        if rgb.dtype != np.uint8:
            rgb = (rgb * 255).astype(np.uint8) if rgb.max() <= 1.0 else rgb.astype(np.uint8)
        imgs.append(rgb)
    combined = np.concatenate(imgs, axis=1)
    frame_list.append(combined)


def save_video(frame_list, output_path, fps=30):
    if not frame_list:
        return
    tmpdir = "/tmp/r2_video_frames"
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
    print(f"  [VIDEO] Saved {len(frame_list)} frames -> {output_path}")


# ---------------------------------------------------------------------------
# do_lift (from test_r1_route.py)
# ---------------------------------------------------------------------------
def do_lift(sim, scene, device, robot_left, robot_right, cable,
            hand_body_left, hand_body_right, jac_body_left, jac_body_right,
            finger_pos, kg_root_pose_0, kg_grip_z_0, kg_env_ids):
    """Lift phase — 50mm vertical lift with kinematic cable root."""
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


# ---------------------------------------------------------------------------
# do_route (from test_r1_route.py — R1b parallel arm move)
# ---------------------------------------------------------------------------
def do_route(sim, scene, device, robot_left, robot_right, cable,
             hand_body_left, hand_body_right, jac_body_left, jac_body_right,
             finger_pos, route_dx, route_dy,
             kg_root_pose_0, kg_grip_z_0, kg_env_ids,
             frozen_cable_joint_pos, frozen_cable_joint_vel,
             frames=None, cameras=None):
    """R1b: Horizontal route — both arms shift by (dx,dy), cable kinematic."""
    env_idx = 0
    route_dist = math.sqrt(route_dx**2 + route_dy**2)

    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

    ee_end_l = ee_start_l.clone()
    ee_end_l[env_idx, 0] += route_dx
    ee_end_l[env_idx, 1] += route_dy
    ee_end_r = ee_start_r.clone()
    ee_end_r[env_idx, 0] += route_dx
    ee_end_r[env_idx, 1] += route_dy

    n_interp = max(int(route_dist / ROUTE_SPEED_M_PER_STEP), 10)
    n_interp = min(n_interp, ROUTE_MAX_STEPS)

    print(f"  [ROUTE] Distance={route_dist*1000:.1f}mm, steps={n_interp}")

    ik_failures = 0
    for step in range(n_interp):
        t = (step + 1) / n_interp
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx, 0] = ee_start_l[env_idx, 0] + route_dx * t
        ee_tgt_l[env_idx, 1] = ee_start_l[env_idx, 1] + route_dy * t
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx, 0] = ee_start_r[env_idx, 0] + route_dx * t
        ee_tgt_r[env_idx, 1] = ee_start_r[env_idx, 1] + route_dy * t

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT)
        if nan_l.any() or nan_r.any():
            ik_failures += 1
            if ik_failures > 10:
                print(f"  [ROUTE] Too many IK NaN ({ik_failures}), aborting at step {step}")
                break
            continue

        _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx)

        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())
            _write_cable_kinematic(robot_left, robot_right, cable,
                                   hand_body_left, hand_body_right,
                                   ee_start_l, ee_start_r,
                                   kg_root_pose_0, kg_grip_z_0, kg_env_ids,
                                   frozen_cable_joint_pos, frozen_cable_joint_vel,
                                   device, env_idx)

        if torch.isnan(cable.data.body_pos_w).any():
            print(f"  [ROUTE] Cable NaN at step {step}!")
            return {"success": False, "ik_failures": ik_failures, "nan_step": step}

        if frames is not None and cameras is not None and step % 2 == 0:
            capture_frame(scene, cameras, frames)

        if step % (n_interp // 5 + 1) == 0 or step == n_interp - 1:
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            xy_err_l = math.sqrt((ee_cur_l[0].item() - ee_end_l[env_idx, 0].item())**2 +
                                 (ee_cur_l[1].item() - ee_end_l[env_idx, 1].item())**2)
            xy_err_r = math.sqrt((ee_cur_r[0].item() - ee_end_r[env_idx, 0].item())**2 +
                                 (ee_cur_r[1].item() - ee_end_r[env_idx, 1].item())**2)
            print(f"  [ROUTE] step={step}/{n_interp} t={t:.2f} "
                  f"xy_err L={xy_err_l*1000:.1f}mm R={xy_err_r*1000:.1f}mm")

    # Settle
    _settle(sim, scene, robot_left, robot_right, cable, hand_body_left, hand_body_right,
            finger_pos, ee_start_l, ee_start_r,
            kg_root_pose_0, kg_grip_z_0, kg_env_ids,
            frozen_cable_joint_pos, frozen_cable_joint_vel, device, env_idx)

    ee_final_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    xy_err_l = math.sqrt((ee_final_l[0].item() - ee_end_l[env_idx, 0].item())**2 +
                         (ee_final_l[1].item() - ee_end_l[env_idx, 1].item())**2)
    xy_err_r = math.sqrt((ee_final_r[0].item() - ee_end_r[env_idx, 0].item())**2 +
                         (ee_final_r[1].item() - ee_end_r[env_idx, 1].item())**2)
    print(f"  [ROUTE] Final: xy_err L={xy_err_l*1000:.1f}mm R={xy_err_r*1000:.1f}mm")

    return {"success": True, "ik_failures": ik_failures,
            "xy_err_l_mm": round(xy_err_l * 1000, 2),
            "xy_err_r_mm": round(xy_err_r * 1000, 2)}


# ---------------------------------------------------------------------------
# do_move — Generic asymmetric arm move (R2a/R2b/R2c/R2d)
# ---------------------------------------------------------------------------
def do_move(sim, scene, device, robot_left, robot_right, cable,
            hand_body_left, hand_body_right, jac_body_left, jac_body_right,
            finger_pos, target_l, target_r, speed,
            kg_root_pose_0, kg_grip_z_0, kg_env_ids,
            frozen_cable_joint_pos, frozen_cable_joint_vel,
            cable_mode="kinematic", label="MOVE",
            frames=None, cameras=None):
    """Move arms independently to target positions.

    cable_mode:
      "kinematic" — frozen cable joints, root follows arm midpoint
      "release"   — kinematic for first half, then release cable to physics
      "physics"   — cable free (no kinematic writes)

    Returns dict with success, ee errors, cable state.
    """
    env_idx = 0
    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

    # Reference midpoint for cable kinematic tracking
    mid_start = ((ee_start_l[env_idx] + ee_start_r[env_idx]) / 2.0).clone()

    # Target positions as tensors
    tgt_pos_l = ee_start_l.clone()
    tgt_pos_l[env_idx] = torch.tensor(target_l, device=device, dtype=torch.float32)
    tgt_pos_r = ee_start_r.clone()
    tgt_pos_r[env_idx] = torch.tensor(target_r, device=device, dtype=torch.float32)

    # Compute distances
    dist_l = torch.norm(tgt_pos_l[env_idx] - ee_start_l[env_idx]).item()
    dist_r = torch.norm(tgt_pos_r[env_idx] - ee_start_r[env_idx]).item()
    max_dist = max(dist_l, dist_r)

    if max_dist < 0.001:
        print(f"  [{label}] Already at target (dist < 1mm)")
        return {"success": True, "ee_error_l_mm": 0.0, "ee_error_r_mm": 0.0,
                "cable_nan": False, "steps_used": 0}

    n_steps = max(int(max_dist / speed), 10)
    n_steps = min(n_steps, 1500)  # safety cap

    print(f"  [{label}] dist_L={dist_l*1000:.1f}mm dist_R={dist_r*1000:.1f}mm "
          f"steps={n_steps} speed={speed*1000:.2f}mm/step")
    print(f"  [{label}] Start L=({ee_start_l[env_idx,0]:.4f},{ee_start_l[env_idx,1]:.4f},"
          f"{ee_start_l[env_idx,2]:.4f}) "
          f"R=({ee_start_r[env_idx,0]:.4f},{ee_start_r[env_idx,1]:.4f},"
          f"{ee_start_r[env_idx,2]:.4f})")
    print(f"  [{label}] Target L=({target_l[0]:.4f},{target_l[1]:.4f},{target_l[2]:.4f}) "
          f"R=({target_r[0]:.4f},{target_r[1]:.4f},{target_r[2]:.4f})")

    if cable_mode == "kinematic":
        print(f"  [{label}] Cable mode: kinematic (frozen joints)")
    elif cable_mode == "release":
        release_step = n_steps // 2
        print(f"  [{label}] Cable mode: release at step {release_step}/{n_steps}")
    else:
        print(f"  [{label}] Cable mode: physics (free)")

    cable_released = (cable_mode == "physics")
    ik_failures = 0
    clamp_log_l = []
    clamp_log_r = []

    for step in range(n_steps):
        t = (step + 1) / n_steps

        # Interpolated targets
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx] = ee_start_l[env_idx] + (tgt_pos_l[env_idx] - ee_start_l[env_idx]) * t
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx] = ee_start_r[env_idx] + (tgt_pos_r[env_idx] - ee_start_r[env_idx]) * t

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_l)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_r)

        if nan_l.any() or nan_r.any():
            ik_failures += 1
            if ik_failures > 10:
                print(f"  [{label}] Too many IK NaN ({ik_failures}), abort at step {step}")
                return {"success": False, "ee_error_l_mm": 999.0, "ee_error_r_mm": 999.0,
                        "cable_nan": False, "steps_used": step, "ik_failures": ik_failures,
                        "abort_reason": "ik_nan"}
            continue

        _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx)

        # Check for cable release transition (R2c)
        if cable_mode == "release" and not cable_released and step >= release_step:
            cable_released = True
            print(f"  [{label}] Cable physics RELEASED at step {step}")

        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())

            if not cable_released:
                # Kinematic cable transport: root follows arm midpoint
                ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
                ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
                mid_cur = (ee_cur_l + ee_cur_r) / 2.0

                kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
                kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_start[0].item())
                kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_start[1].item())
                kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_start[2].item())
                cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
                cable.write_root_velocity_to_sim(
                    torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
                cable.write_joint_state_to_sim(frozen_cable_joint_pos, frozen_cable_joint_vel)

        # NaN check
        if torch.isnan(cable.data.body_pos_w).any():
            print(f"  [{label}] Cable NaN at step {step}!")
            return {"success": False, "ee_error_l_mm": 999.0, "ee_error_r_mm": 999.0,
                    "cable_nan": True, "nan_step": step, "steps_used": step,
                    "ik_failures": ik_failures, "abort_reason": "cable_nan"}

        # Video capture
        if frames is not None and cameras is not None and step % 2 == 0:
            capture_frame(scene, cameras, frames)

        # Progress log (every 20%)
        if step % (n_steps // 5 + 1) == 0 or step == n_steps - 1:
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            err_l = torch.norm(ee_cur_l - tgt_pos_l[env_idx]).item()
            err_r = torch.norm(ee_cur_r - tgt_pos_r[env_idx]).item()
            cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()
            print(f"  [{label}] step={step}/{n_steps} t={t:.2f} "
                  f"ee_err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm cable_z={cable_z:.4f}")

    # Settle at final position
    if not cable_released:
        _settle(sim, scene, robot_left, robot_right, cable,
                hand_body_left, hand_body_right, finger_pos,
                ee_start_l, ee_start_r,  # not used for midpoint in _settle_generic
                kg_root_pose_0, kg_grip_z_0, kg_env_ids,
                frozen_cable_joint_pos, frozen_cable_joint_vel, device, env_idx,
                mid_start=mid_start)
    else:
        _settle_physics(sim, scene, robot_left, robot_right,
                        hand_body_left, hand_body_right, finger_pos, env_idx)

    # Final measurements
    ee_final_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    err_l = torch.norm(ee_final_l - tgt_pos_l[env_idx]).item()
    err_r = torch.norm(ee_final_r - tgt_pos_r[env_idx]).item()

    cable_nan = torch.isnan(cable.data.body_pos_w).any().item()
    cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()

    n_clamp_l = sum(1 for c in clamp_log_l if c)
    n_clamp_r = sum(1 for c in clamp_log_r if c)
    if n_clamp_l + n_clamp_r > 0:
        print(f"  [{label}] Fix2 vel clamp: L={n_clamp_l} R={n_clamp_r}")

    print(f"  [{label}] Final: ee_err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm "
          f"cable_z={cable_z:.4f} nan={cable_nan}")

    success = (err_l < 0.020 and err_r < 0.020 and not cable_nan)

    return {
        "success": success,
        "ee_error_l_mm": round(err_l * 1000, 2),
        "ee_error_r_mm": round(err_r * 1000, 2),
        "cable_nan": cable_nan,
        "cable_z": round(cable_z, 4),
        "steps_used": n_steps,
        "ik_failures": ik_failures,
        "final_pos_l": [round(ee_final_l[i].item(), 4) for i in range(3)],
        "final_pos_r": [round(ee_final_r[i].item(), 4) for i in range(3)],
        "vel_clamp_l": n_clamp_l,
        "vel_clamp_r": n_clamp_r,
    }


# ---------------------------------------------------------------------------
# do_release — R2d: open grippers, wait, check cable on hook
# ---------------------------------------------------------------------------
def do_release(sim, scene, device, robot_left, robot_right, cable,
               hand_body_left, hand_body_right, env_idx=0):
    """Open grippers gradually, wait 5 seconds (2400 steps @ 480Hz), check cable."""
    print(f"  [R2d-RELEASE] Stabilize {RELEASE_STABILIZE_STEPS} steps...")

    # Hold position
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    finger_pos = robot_left.data.joint_pos[env_idx, 7].item()

    for _ in range(RELEASE_STABILIZE_STEPS):
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

    # Gradually open grippers
    print(f"  [R2d-RELEASE] Opening grippers ({RELEASE_GRIPPER_STEPS} steps)...")
    grip_cur = finger_pos
    grip_step = (GRIPPER_OPEN - grip_cur) / RELEASE_GRIPPER_STEPS
    for s in range(RELEASE_GRIPPER_STEPS):
        grip_cur = min(grip_cur + grip_step, GRIPPER_OPEN)
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l
        tgt_l[env_idx, 7] = grip_cur
        tgt_l[env_idx, 8] = grip_cur
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r
        tgt_r[env_idx, 7] = grip_cur
        tgt_r[env_idx, 8] = grip_cur
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Wait 5 seconds (2400 steps @ 480Hz) for cable to settle
    wait_steps = 2400
    print(f"  [R2d-RELEASE] Waiting {wait_steps} steps (~5s) for cable settle...")
    for _ in range(wait_steps):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l
        tgt_l[env_idx, 7] = GRIPPER_OPEN
        tgt_l[env_idx, 8] = GRIPPER_OPEN
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r
        tgt_r[env_idx, 7] = GRIPPER_OPEN
        tgt_r[env_idx, 8] = GRIPPER_OPEN
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Check cable state
    cable_nan = torch.isnan(cable.data.body_pos_w).any().item()
    cable_z_final = cable.data.body_pos_w[env_idx, :, 2].mean().item()

    # Cable on hook: cable center Z should be near hook Z (0.80)
    # Success: cable_z > HOOK_Z - 0.050 (within 50mm below hook top)
    cable_on_hook = (not cable_nan) and (cable_z_final > HOOK_Z - 0.050)

    print(f"  [R2d-RELEASE] cable_z_final={cable_z_final:.4f} hook_z={HOOK_Z:.2f} "
          f"on_hook={cable_on_hook} nan={cable_nan}")

    return {
        "gripper_opened": True,
        "cable_on_hook": cable_on_hook,
        "cable_z_final": round(cable_z_final, 4),
        "hook_z": HOOK_Z,
        "cable_nan": cable_nan,
    }


# ---------------------------------------------------------------------------
# Helper: apply joint targets to both robots
# ---------------------------------------------------------------------------
def _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_pos, env_idx):
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


# ---------------------------------------------------------------------------
# Helper: write cable kinematic state (root + frozen joints)
# ---------------------------------------------------------------------------
def _write_cable_kinematic(robot_left, robot_right, cable,
                           hand_body_left, hand_body_right,
                           ee_ref_l, ee_ref_r,
                           kg_root_pose_0, kg_grip_z_0, kg_env_ids,
                           frozen_cable_joint_pos, frozen_cable_joint_vel,
                           device, env_idx):
    ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    mid_cur = (ee_cur_l + ee_cur_r) / 2.0
    mid_ref = (ee_ref_l[env_idx, :3] + ee_ref_r[env_idx, :3]) / 2.0

    kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
    kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - mid_ref[0].item())
    kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - mid_ref[1].item())
    kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - mid_ref[2].item())
    cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
    cable.write_root_velocity_to_sim(
        torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
    cable.write_joint_state_to_sim(frozen_cable_joint_pos, frozen_cable_joint_vel)


# ---------------------------------------------------------------------------
# Helper: settle with kinematic cable
# ---------------------------------------------------------------------------
def _settle(sim, scene, robot_left, robot_right, cable,
            hand_body_left, hand_body_right, finger_pos,
            ee_ref_l, ee_ref_r,
            kg_root_pose_0, kg_grip_z_0, kg_env_ids,
            frozen_cable_joint_pos, frozen_cable_joint_vel,
            device, env_idx, mid_start=None):
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

        # Cable kinematic: use mid_start for reference
        ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
        mid_cur = (ee_cur_l + ee_cur_r) / 2.0
        ref = mid_start if mid_start is not None else (ee_ref_l[env_idx] + ee_ref_r[env_idx]) / 2.0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 0] = kg_root_pose_0[0] + (mid_cur[0].item() - ref[0].item())
        kg_new_pose[0, 1] = kg_root_pose_0[1] + (mid_cur[1].item() - ref[1].item())
        kg_new_pose[0, 2] = kg_root_pose_0[2] + (mid_cur[2].item() - ref[2].item())
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(
            torch.zeros(1, 6, device=device), env_ids=kg_env_ids)
        cable.write_joint_state_to_sim(frozen_cable_joint_pos, frozen_cable_joint_vel)


# ---------------------------------------------------------------------------
# Helper: settle with cable physics (free cable)
# ---------------------------------------------------------------------------
def _settle_physics(sim, scene, robot_left, robot_right,
                    hand_body_left, hand_body_right, finger_pos, env_idx):
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


# ---------------------------------------------------------------------------
# run_episode — Full pipeline: R0 + R1 + R2a-R2d
# ---------------------------------------------------------------------------
def run_episode(sim, scene, device, episode_idx,
                record_video=False, output_dir=None):
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]
    env_idx = 0
    N = 1

    results = {
        "r2a_arm_separation": None,
        "r2b_ascend": None,
        "r2c_descend_drape": None,
        "r2d_release": None,
        "furthest_stage": "none",
        "overall": "FAIL",
    }

    # === R0: Teleport + Close + Lift ===
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

    # Close grippers
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
    print(f"  [R0] Grip: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

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

    # Kinematic cable setup
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    kg_grip_z_0 = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                   robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
    kg_env_ids = torch.tensor([env_idx], dtype=torch.int32, device=device)

    # Lift
    print(f"  [R0] Lift 50mm...")
    do_lift(sim, scene, device, robot_left, robot_right, cable,
            hand_body_left, hand_body_right, jac_body_left, jac_body_right,
            finger_pos, kg_root_pose_0, kg_grip_z_0, kg_env_ids)

    ee_post_lift_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3].clone()
    ee_post_lift_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3].clone()
    print(f"  [R0] EE post-lift: L=({ee_post_lift_l[0]:.4f},{ee_post_lift_l[1]:.4f},"
          f"{ee_post_lift_l[2]:.4f}) R=({ee_post_lift_r[0]:.4f},{ee_post_lift_r[1]:.4f},"
          f"{ee_post_lift_r[2]:.4f})")

    # Freeze cable joints for kinematic transport (Fix 1)
    frozen_cable_joint_pos = cable.data.joint_pos.clone()
    frozen_cable_joint_vel = torch.zeros_like(frozen_cable_joint_pos)

    # Video frames
    frames = [] if record_video else None
    cameras = ["overhead_camera", "front_left_camera"] if record_video else None

    # === R1: Route to hook XY ===
    approx_dx = HOOK_X - 0.295
    approx_dy = HOOK_Y - 0.001
    print(f"  [R1] Route to hook: dx={approx_dx*1000:.1f}mm dy={approx_dy*1000:.1f}mm")

    # Store reference positions for cable kinematic tracking
    ee_ref_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_ref_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

    route_result = do_route(
        sim, scene, device, robot_left, robot_right, cable,
        hand_body_left, hand_body_right, jac_body_left, jac_body_right,
        finger_pos, approx_dx, approx_dy,
        kg_root_pose_0, kg_grip_z_0, kg_env_ids,
        frozen_cable_joint_pos, frozen_cable_joint_vel,
        frames=frames, cameras=cameras)

    if not route_result.get("success", False):
        print(f"  [R1] FAIL — aborting R2")
        results["furthest_stage"] = "R1_fail"
        if record_video and frames and output_dir:
            save_video(frames, os.path.join(output_dir, f"R2_ep{episode_idx}.mp4"))
        return results

    print(f"  [R1] PASS")

    # Update kg_root_pose_0 for R2 stages (cable root has moved)
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    # Re-read frozen cable joint state (root has moved, but joints are still frozen)
    # Cable midpoint reference for do_move
    mid_ref_r2 = ((robot_left.data.body_pos_w[env_idx, hand_body_left, :3] +
                   robot_right.data.body_pos_w[env_idx, hand_body_right, :3]) / 2.0).clone()

    # === R2a: Arm Separation (Phase 4.5) ===
    print(f"\n  {'='*50}")
    print(f"  [R2a] Arm Separation → Phase 4.5")
    print(f"  {'='*50}")

    r2a = do_move(
        sim, scene, device, robot_left, robot_right, cable,
        hand_body_left, hand_body_right, jac_body_left, jac_body_right,
        finger_pos,
        target_l=WAYPOINT_PHASE45_LEFT, target_r=WAYPOINT_PHASE45_RIGHT,
        speed=ROUTE_SPEED_M_PER_STEP,
        kg_root_pose_0=kg_root_pose_0, kg_grip_z_0=kg_grip_z_0, kg_env_ids=kg_env_ids,
        frozen_cable_joint_pos=frozen_cable_joint_pos,
        frozen_cable_joint_vel=frozen_cable_joint_vel,
        cable_mode="kinematic", label="R2a",
        frames=frames, cameras=cameras)

    results["r2a_arm_separation"] = {
        "left_ee_error_mm": r2a["ee_error_l_mm"],
        "right_ee_error_mm": r2a["ee_error_r_mm"],
        "cable_nan": r2a["cable_nan"],
        "pass": r2a["success"],
    }

    if not r2a["success"]:
        print(f"  [R2a] FAIL")
        results["furthest_stage"] = "r2a"
        if record_video and frames and output_dir:
            save_video(frames, os.path.join(output_dir, f"R2_ep{episode_idx}.mp4"))
        return results
    print(f"  [R2a] PASS")

    # Update cable root reference
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()

    # === R2b: Ascend to Hook Top (Phase 5) ===
    print(f"\n  {'='*50}")
    print(f"  [R2b] Ascend to Hook Top → Phase 5 (Z=1.09)")
    print(f"  {'='*50}")

    r2b = do_move(
        sim, scene, device, robot_left, robot_right, cable,
        hand_body_left, hand_body_right, jac_body_left, jac_body_right,
        finger_pos,
        target_l=WAYPOINT_PHASE5_LEFT, target_r=WAYPOINT_PHASE5_RIGHT,
        speed=ROUTE_SPEED_M_PER_STEP / 2,  # Half speed: R arm needs ~1200 steps to converge
        kg_root_pose_0=kg_root_pose_0, kg_grip_z_0=kg_grip_z_0, kg_env_ids=kg_env_ids,
        frozen_cable_joint_pos=frozen_cable_joint_pos,
        frozen_cable_joint_vel=frozen_cable_joint_vel,
        cable_mode="kinematic", label="R2b",
        frames=frames, cameras=cameras)

    results["r2b_ascend"] = {
        "left_ee_error_mm": r2b["ee_error_l_mm"],
        "right_ee_error_mm": r2b["ee_error_r_mm"],
        "cable_nan": r2b["cable_nan"],
        "pass": r2b["success"],
    }

    if not r2b["success"]:
        print(f"  [R2b] FAIL")
        results["furthest_stage"] = "r2b"
        if record_video and frames and output_dir:
            save_video(frames, os.path.join(output_dir, f"R2_ep{episode_idx}.mp4"))
        return results
    print(f"  [R2b] PASS")

    # Update cable root reference
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()

    # === R2c: Descend + Cable Drape (Phase 5.5) ===
    print(f"\n  {'='*50}")
    print(f"  [R2c] Descend + Cable Drape → Phase 5.5 (Z=1.02)")
    print(f"  [R2c] Cable physics released mid-descent")
    print(f"  {'='*50}")

    r2c = do_move(
        sim, scene, device, robot_left, robot_right, cable,
        hand_body_left, hand_body_right, jac_body_left, jac_body_right,
        finger_pos,
        target_l=WAYPOINT_PHASE55_LEFT, target_r=WAYPOINT_PHASE55_RIGHT,
        speed=ROUTE_SPEED_M_PER_STEP / 2,  # half speed for safety
        kg_root_pose_0=kg_root_pose_0, kg_grip_z_0=kg_grip_z_0, kg_env_ids=kg_env_ids,
        frozen_cable_joint_pos=frozen_cable_joint_pos,
        frozen_cable_joint_vel=frozen_cable_joint_vel,
        cable_mode="release", label="R2c",
        frames=frames, cameras=cameras)

    # Check for cable-hook contact (cable center Z near hook level)
    cable_z = r2c.get("cable_z", 0.0)
    cable_near_hook = abs(cable_z - HOOK_Z) < 0.10  # within 100mm of hook

    results["r2c_descend_drape"] = {
        "left_ee_error_mm": r2c["ee_error_l_mm"],
        "right_ee_error_mm": r2c["ee_error_r_mm"],
        "cable_physics_resumed": True,
        "cable_nan_after_resume": r2c["cable_nan"],
        "cable_hook_contact": cable_near_hook,
        "cable_z": cable_z,
        "pass": r2c["success"],
    }

    if not r2c["success"]:
        print(f"  [R2c] FAIL")
        results["furthest_stage"] = "r2c"
        if record_video and frames and output_dir:
            save_video(frames, os.path.join(output_dir, f"R2_ep{episode_idx}.mp4"))
        return results
    print(f"  [R2c] PASS (cable_z={cable_z:.4f}, near_hook={cable_near_hook})")

    # === R2d: Release + Retreat (Phase 6) ===
    print(f"\n  {'='*50}")
    print(f"  [R2d] Release → Phase 6")
    print(f"  {'='*50}")

    # Move to Phase 6 retreat position (cable physics free)
    r2d_move = do_move(
        sim, scene, device, robot_left, robot_right, cable,
        hand_body_left, hand_body_right, jac_body_left, jac_body_right,
        finger_pos,
        target_l=WAYPOINT_PHASE6_LEFT, target_r=WAYPOINT_PHASE6_RIGHT,
        speed=ROUTE_SPEED_M_PER_STEP,
        kg_root_pose_0=kg_root_pose_0, kg_grip_z_0=kg_grip_z_0, kg_env_ids=kg_env_ids,
        frozen_cable_joint_pos=frozen_cable_joint_pos,
        frozen_cable_joint_vel=frozen_cable_joint_vel,
        cable_mode="physics", label="R2d-MOVE",
        frames=frames, cameras=cameras)

    if not r2d_move["success"]:
        print(f"  [R2d] Move to retreat FAIL")
        results["r2d_release"] = {
            "gripper_opened": False,
            "cable_on_hook_after_5s": False,
            "cable_z_final": r2d_move.get("cable_z", 0.0),
            "hook_z": HOOK_Z,
            "pass": False,
        }
        results["furthest_stage"] = "r2d"
        if record_video and frames and output_dir:
            save_video(frames, os.path.join(output_dir, f"R2_ep{episode_idx}.mp4"))
        return results

    # Release grippers and wait
    release = do_release(sim, scene, device, robot_left, robot_right, cable,
                         hand_body_left, hand_body_right)

    results["r2d_release"] = {
        "gripper_opened": release["gripper_opened"],
        "cable_on_hook_after_5s": release["cable_on_hook"],
        "cable_z_final": release["cable_z_final"],
        "hook_z": HOOK_Z,
        "pass": release["cable_on_hook"],
    }

    # Video capture final frames
    if frames is not None and cameras is not None:
        for _ in range(10):
            capture_frame(scene, cameras, frames)

    if record_video and frames and output_dir:
        save_video(frames, os.path.join(output_dir, f"R2_ep{episode_idx}.mp4"))

    # Overall
    all_pass = all([
        results["r2a_arm_separation"]["pass"],
        results["r2b_ascend"]["pass"],
        results["r2c_descend_drape"]["pass"],
        results["r2d_release"]["pass"],
    ])
    results["furthest_stage"] = "r2d"
    results["overall"] = "PASS" if all_pass else "FAIL"
    return results


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    device = f"cuda:{app_launcher.device_id}"
    print(f"\n[R2] Hook Placement Test")
    print(f"[R2] Device: {device}")
    print(f"[R2] Hook: ({HOOK_X}, {HOOK_Y}, {HOOK_Z})")
    print(f"[R2] Waypoints:")
    print(f"  Phase 4.5 L={WAYPOINT_PHASE45_LEFT} R={WAYPOINT_PHASE45_RIGHT}")
    print(f"  Phase 5   L={WAYPOINT_PHASE5_LEFT} R={WAYPOINT_PHASE5_RIGHT}")
    print(f"  Phase 5.5 L={WAYPOINT_PHASE55_LEFT} R={WAYPOINT_PHASE55_RIGHT}")
    print(f"  Phase 6   L={WAYPOINT_PHASE6_LEFT} R={WAYPOINT_PHASE6_RIGHT}")

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

    os.makedirs(args.output_dir, exist_ok=True)
    all_episodes = []
    t0 = time.time()

    for ep in range(args.num_episodes):
        print(f"\n{'='*60}")
        print(f"[R2] Episode {ep+1}/{args.num_episodes}")
        print(f"{'='*60}")
        sim.reset()
        scene.reset()
        for _ in range(10):
            sim.step()
            scene.update(sim.get_physics_dt())

        result = run_episode(sim, scene, device, ep,
                             record_video=args.record_video, output_dir=args.output_dir)
        all_episodes.append(result)

        # If first episode fails early, still try remaining episodes
        print(f"\n[R2] Episode {ep+1} result: furthest={result['furthest_stage']} "
              f"overall={result['overall']}")

    elapsed = time.time() - t0

    # Summary
    furthest_stages = [r["furthest_stage"] for r in all_episodes]
    n_full_pass = sum(1 for r in all_episodes if r["overall"] == "PASS")

    # Per-stage pass rates
    stage_stats = {}
    for stage_key in ["r2a_arm_separation", "r2b_ascend", "r2c_descend_drape", "r2d_release"]:
        reached = [r[stage_key] for r in all_episodes if r[stage_key] is not None]
        passed = sum(1 for s in reached if s["pass"])
        stage_stats[stage_key] = {
            "reached": len(reached),
            "passed": passed,
            "rate": f"{passed}/{len(reached)}" if reached else "0/0",
        }

    print(f"\n[R2] SUMMARY: {n_full_pass}/{args.num_episodes} full PASS")
    for sk, sv in stage_stats.items():
        print(f"  {sk}: {sv['rate']}")
    print(f"  Furthest stages: {furthest_stages}")

    metrics = {
        "phase": "R2",
        "description": "Hook placement — R2a separation, R2b ascend, R2c drape, R2d release",
        "device": device,
        "hook_pos": [HOOK_X, HOOK_Y, HOOK_Z],
        "waypoints": {
            "phase45_l": list(WAYPOINT_PHASE45_LEFT),
            "phase45_r": list(WAYPOINT_PHASE45_RIGHT),
            "phase5_l": list(WAYPOINT_PHASE5_LEFT),
            "phase5_r": list(WAYPOINT_PHASE5_RIGHT),
            "phase55_l": list(WAYPOINT_PHASE55_LEFT),
            "phase55_r": list(WAYPOINT_PHASE55_RIGHT),
            "phase6_l": list(WAYPOINT_PHASE6_LEFT),
            "phase6_r": list(WAYPOINT_PHASE6_RIGHT),
        },
        "stage_stats": stage_stats,
        "episodes": all_episodes,
        "n_full_pass": n_full_pass,
        "overall": "PASS" if n_full_pass == args.num_episodes else "FAIL",
        "elapsed_s": round(elapsed, 1),
    }

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[R2] Metrics saved: {metrics_path}")
    print(f"[R2] Total elapsed: {elapsed:.1f}s")
    print(f"[R2] Overall: {metrics['overall']}")


if __name__ == "__main__":
    main()
