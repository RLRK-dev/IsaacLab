"""test_physical_pipeline.py — Physical Grasp Pipeline Test (Step 0).

Tests cable manipulation with PHYSICAL grip (finger friction only).
NO cable teleport — cable.write_root_pose_to_sim() and
cable.write_joint_state_to_sim() are never called.

Fix 2 (Joint Velocity Clamping) is active throughout.
Fix 1 (Cable Kinematic Transport) is REMOVED.

Stages:
  0a: EXP-036 baseline (teleport+close+lift 20mm)
  0b: Physical lift 50mm
  0c: Physical route 50mm
  0d: Physical route 131mm (full route to hook)
  0e: Physical R2a-R2d (hook placement)
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
parser.add_argument("--output_dir", type=str, default="data/test_physical")
parser.add_argument("--headless", action="store_true", default=False)
parser.add_argument("--num_episodes", type=int, default=3)
parser.add_argument("--stage", type=str, default=None,
                    help="Run only this stage: 0a|0b|0c|0d|0e|all")
parser.add_argument("--record_video", action="store_true", default=False)
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, device=args.device,
                           enable_cameras=True)
sim_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    # HOOK_X, HOOK_Y, HOOK_Z,  # DEPRECATED — replaced by Clip configuration
    ROUTE_SPEED_M_PER_STEP, ROUTE_IK_SUBSTEPS,
    ROUTE_MAX_STEPS,
    JOINT_VEL_LIMIT,
    # WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,  # Hook-era waypoints (commented out)
    # WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    # WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    # WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS,
    FINGER_GRIP_VEL, FINGER_OPEN_VEL,
    PANDA_HAND_DAMPING,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FINGERTIP_OFFSET = 0.1123
GRIPPER_OPEN = 0.04
CLOSE_STEPS = 100
CLOSE_SUBSTEPS = 4        # sim substeps per close step
SETTLE_STEPS = 80
LIFT_STEPS_PER_CM = 40    # IK steps per cm of lift
LIFT_SUBSTEPS = 4         # sim substeps per lift IK step
SLIP_THRESHOLD_MM = 3.0   # grip_width increase > 3mm = slip


# ---------------------------------------------------------------------------
# JT IK step (with Fix 2: joint velocity clamping)
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
# Video utilities
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
    tmpdir = "/tmp/phys_video_frames"
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir)
    for i, frame in enumerate(frame_list):
        Image.fromarray(frame).save(os.path.join(tmpdir, f"frame_{i:06d}.jpg"),
                                    quality=85)
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
# Helpers
# ---------------------------------------------------------------------------
def _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_vel, env_idx):
    # Arm joints (0-6): position target
    tgt_l = robot_left.data.joint_pos.clone()
    tgt_l[env_idx, :7] = ik_l[env_idx]
    robot_left.set_joint_position_target(tgt_l)
    # Finger velocity target (v22o: velocity mode — force = damping × target_vel)
    vel_tgt_l = torch.zeros_like(robot_left.data.joint_pos)
    vel_tgt_l[env_idx, 7] = finger_vel
    vel_tgt_l[env_idx, 8] = finger_vel
    robot_left.set_joint_velocity_target(vel_tgt_l)
    robot_left.write_data_to_sim()

    tgt_r = robot_right.data.joint_pos.clone()
    tgt_r[env_idx, :7] = ik_r[env_idx]
    robot_right.set_joint_position_target(tgt_r)
    vel_tgt_r = torch.zeros_like(robot_right.data.joint_pos)
    vel_tgt_r[env_idx, 7] = finger_vel
    vel_tgt_r[env_idx, 8] = finger_vel
    robot_right.set_joint_velocity_target(vel_tgt_r)
    robot_right.write_data_to_sim()


def _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                   env_idx, n_steps):
    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(n_steps):
        # Arm: position target (hold current)
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_l
        robot_left.set_joint_position_target(tgt_l)
        # Finger: velocity target (v22o: force = damping × target_vel)
        vel_tgt_l = torch.zeros_like(robot_left.data.joint_pos)
        vel_tgt_l[env_idx, 7] = finger_vel
        vel_tgt_l[env_idx, 8] = finger_vel
        robot_left.set_joint_velocity_target(vel_tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_r
        robot_right.set_joint_position_target(tgt_r)
        vel_tgt_r = torch.zeros_like(robot_right.data.joint_pos)
        vel_tgt_r[env_idx, 7] = finger_vel
        vel_tgt_r[env_idx, 8] = finger_vel
        robot_right.set_joint_velocity_target(vel_tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())


def get_grip_width(robot_left, robot_right, env_idx=0):
    """Actual finger position (mm)."""
    gl = robot_left.data.joint_pos[env_idx, 7].item() * 1000
    gr = robot_right.data.joint_pos[env_idx, 7].item() * 1000
    return gl, gr


def get_cable_midpoint(cable, env_idx=0):
    """Position of cable middle segment."""
    n_bodies = cable.data.body_pos_w.shape[1]
    mid_idx = n_bodies // 2
    return cable.data.body_pos_w[env_idx, mid_idx, :3].clone()


def check_cable_nan(cable):
    return torch.isnan(cable.data.body_pos_w).any().item()


# ---------------------------------------------------------------------------
# Grasp tracking helpers
# ---------------------------------------------------------------------------
def find_nearest_segments(cable, robot_left, robot_right, hand_body_left,
                          hand_body_right, env_idx=0):
    """Find the cable segment nearest to each gripper center (dynamic tracking).

    Returns (seg_id_l, dist_l_mm, seg_id_r, dist_r_mm).
    """
    seg_xyz = cable.data.body_pos_w[env_idx]  # (N, 3)
    gc_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    gc_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    dists_l = torch.norm(seg_xyz - gc_l.unsqueeze(0), dim=1)
    dists_r = torch.norm(seg_xyz - gc_r.unsqueeze(0), dim=1)
    seg_id_l = dists_l.argmin().item()
    seg_id_r = dists_r.argmin().item()
    return seg_id_l, dists_l[seg_id_l].item() * 1000, seg_id_r, dists_r[seg_id_r].item() * 1000


def log_seg_xyz(cable, phase_label, env_idx=0):
    """Print XYZ of all cable segments for a given phase."""
    n = cable.data.body_pos_w.shape[1]
    for i in range(n):
        x, y, z = cable.data.body_pos_w[env_idx, i].tolist()
        print(f"  [SEG_XYZ {phase_label}] seg{i}: X={x:.4f} Y={y:.4f} Z={z:.4f}")


def log_grasp_track(cable, robot_left, robot_right, hbl, hbr, phase_label,
                    env_idx=0):
    """Log nearest-segment tracking for both grippers."""
    sl, dl, sr, dr = find_nearest_segments(cable, robot_left, robot_right,
                                           hbl, hbr, env_idx)
    print(f"  [GRASP_TRACK {phase_label}] L: seg{sl} dist={dl:.1f}mm  "
          f"R: seg{sr} dist={dr:.1f}mm")


# ---------------------------------------------------------------------------
# TELEPORT + CLOSE: Set arms to Phase 2 joints, PD-close grippers
# ---------------------------------------------------------------------------
def do_teleport_and_close(sim, scene, device, env_idx=0):
    """Teleport arms to Phase 2 grasp position, close grippers via kinematic writes.

    Returns (finger_vel, hand_body_left, hand_body_right, jac_body_left,
             jac_body_right, grip_l_mm, grip_r_mm)
    """
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    N = 1

    # v19: PHASE2 joints now come from task_config.py SSOT
    # Left: Y-aligned to seg5 (Y=-0.225), Right: Y-aligned to seg8 (Y=+0.195, bilateral tension)
    p2_joints_l = torch.tensor(PHASE2_LEFT_JOINTS, dtype=torch.float32, device=device)
    p2_joints_r = torch.tensor(PHASE2_RIGHT_JOINTS, dtype=torch.float32, device=device)

    # Teleport: write joint state + set PD target
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

    # Settle
    for _ in range(SETTLE_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    hand_body_left = robot_left.find_bodies("panda_hand")[0][0]
    hand_body_right = robot_right.find_bodies("panda_hand")[0][0]
    jac_body_left = hand_body_left - 1
    jac_body_right = hand_body_right - 1

    ee_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
    ee_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
    print(f"  [SETUP] EE after teleport: "
          f"L=({ee_l[0,0]:.4f},{ee_l[0,1]:.4f},{ee_l[0,2]:.4f}) "
          f"R=({ee_r[0,0]:.4f},{ee_r[0,1]:.4f},{ee_r[0,2]:.4f})")

    # Diagnostic: check finger center (gc) vs cable position
    cable = scene["cable"]
    cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()
    n_bodies = cable.data.body_pos_w.shape[1]
    for i in range(n_bodies):
        seg_pos = cable.data.body_pos_w[env_idx, i, :3]
        print(f"  [DIAG] Cable seg {i}: "
              f"({seg_pos[0].item():.4f}, {seg_pos[1].item():.4f}, {seg_pos[2].item():.4f})")

    lf_idx = robot_left.find_bodies("panda_leftfinger")[0][0]
    rf_idx = robot_left.find_bodies("panda_rightfinger")[0][0]
    gc_l = (robot_left.data.body_pos_w[env_idx, lf_idx, :3] +
            robot_left.data.body_pos_w[env_idx, rf_idx, :3]) / 2.0
    gc_r = (robot_right.data.body_pos_w[env_idx, lf_idx, :3] +
            robot_right.data.body_pos_w[env_idx, rf_idx, :3]) / 2.0
    print(f"  [DIAG] gc L=({gc_l[0].item():.4f},{gc_l[1].item():.4f},{gc_l[2].item():.4f})")
    print(f"  [DIAG] gc R=({gc_r[0].item():.4f},{gc_r[1].item():.4f},{gc_r[2].item():.4f})")
    print(f"  [DIAG] Cable Z={cable_z:.4f}, gc_z L={gc_l[2].item():.4f} R={gc_r[2].item():.4f}")
    gc_z_gap_l = gc_l[2].item() - cable_z
    gc_z_gap_r = gc_r[2].item() - cable_z
    print(f"  [DIAG] Z gap: gc_L - cable = {gc_z_gap_l*1000:.1f}mm, "
          f"gc_R - cable = {gc_z_gap_r*1000:.1f}mm")

    # NOTE: Descent removed — fingertip (EE - FINGERTIP_OFFSET) is already at cable Z.
    # gc (finger body center) appears 48mm above cable, but actual contact point (fingertip)
    # is at EE_Z - 0.1123 ≈ cable_Z. The working pipeline confirms no descent needed.

    # --- v16b: Y-alignment — move grippers to nearest cable segment Y ---
    # After teleport, grippers may not Y-align with cable segments (24mm gap observed).
    # Use JT IK to adjust each arm's Y to match the nearest cable segment.
    cable_y = [cable.data.body_pos_w[env_idx, i, 1].item() for i in range(n_bodies)]
    ee_l_cur = robot_left.data.body_pos_w[:, hand_body_left, :3]
    ee_r_cur = robot_right.data.body_pos_w[:, hand_body_right, :3]
    ee_y_l = ee_l_cur[env_idx, 1].item()
    ee_y_r = ee_r_cur[env_idx, 1].item()
    # Find nearest cable segment Y for each gripper
    nearest_l = min(range(n_bodies), key=lambda i: abs(cable_y[i] - ee_y_l))
    nearest_r = min(range(n_bodies), key=lambda i: abs(cable_y[i] - ee_y_r))
    target_y_l = cable_y[nearest_l]
    target_y_r = cable_y[nearest_r]
    y_gap_l = abs(target_y_l - ee_y_l) * 1000
    y_gap_r = abs(target_y_r - ee_y_r) * 1000
    print(f"  [Y_ALIGN] L: ee_Y={ee_y_l:.4f} → seg{nearest_l} Y={target_y_l:.4f} "
          f"(gap={y_gap_l:.1f}mm)")
    print(f"  [Y_ALIGN] R: ee_Y={ee_y_r:.4f} → seg{nearest_r} Y={target_y_r:.4f} "
          f"(gap={y_gap_r:.1f}mm)")

    # Y-alignment skipped — direct joint1 adjustment and JT IK both failed.
    # The cable layout must be adjusted to match gripper positions, or
    # PHASE2 joints recalculated via analytical IK for correct Y targets.

    # --- Velocity close: apply FINGER_GRIP_VEL until grip converges ---
    # v22o: Velocity mode — force = damping × target_vel (ImplicitActuator).
    # Velocity target drives fingers inward; cable collision blocks at physical equilibrium.
    finger_vel = FINGER_GRIP_VEL
    grip_l_init = robot_left.data.joint_pos[env_idx, 7].item()
    grip_r_init = robot_right.data.joint_pos[env_idx, 7].item()
    VEL_CLOSE_MAX_STEPS = 2000     # max steps for velocity close (~4.2s @ 480Hz)
    # 40mm→5mm = 35mm travel at 0.021mm/step = ~1680 steps needed
    VEL_CLOSE_GRIP_THRESH = 0.006  # 6mm — cable radius 5mm, expect block around here
    VEL_CLOSE_LOG_INTERVAL = 100

    print(f"  [CLOSE] Velocity close from L={grip_l_init*1000:.1f}mm R={grip_r_init*1000:.1f}mm "
          f"(vel={finger_vel}m/s, damping={PANDA_HAND_DAMPING}, "
          f"force={PANDA_HAND_DAMPING * abs(finger_vel):.0f}N, "
          f"threshold={VEL_CLOSE_GRIP_THRESH*1000:.0f}mm, "
          f"max_steps={VEL_CLOSE_MAX_STEPS})")

    for s in range(VEL_CLOSE_MAX_STEPS):
        _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                       env_idx, 1)
        grip_l = robot_left.data.joint_pos[env_idx, 7].item()
        grip_r = robot_right.data.joint_pos[env_idx, 7].item()

        if s % VEL_CLOSE_LOG_INTERVAL == 0 and s > 0:
            print(f"  [CLOSE] step {s}: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

        if grip_l <= VEL_CLOSE_GRIP_THRESH and grip_r <= VEL_CLOSE_GRIP_THRESH:
            print(f"  [CLOSE] Converged at step {s}: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")
            break

    grip_l = robot_left.data.joint_pos[env_idx, 7].item()
    grip_r = robot_right.data.joint_pos[env_idx, 7].item()
    print(f"  [CLOSE] Velocity close done: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

    # Grip check: cable between fingers?
    grip_ok_l = grip_l > 0.0025
    grip_ok_r = grip_r > 0.0025
    if not (grip_ok_l and grip_ok_r):
        print(f"  [CLOSE] GRIP FAILED: cable tunneled through fingers")

    # Read actual grip after stabilization (cable-blocked equilibrium)
    grip_l_final = robot_left.data.joint_pos[0, 7].item()
    grip_r_final = robot_right.data.joint_pos[0, 7].item()
    ee_l_post = robot_left.data.body_pos_w[:, hand_body_left, :3]
    ee_r_post = robot_right.data.body_pos_w[:, hand_body_right, :3]
    print(f"  [VEL_STAB] Done: actual L={grip_l_final*1000:.1f}mm R={grip_r_final*1000:.1f}mm "
          f"(vel={finger_vel}m/s, clamp_force={PANDA_HAND_DAMPING * abs(finger_vel):.0f}N)")
    print(f"  [VEL_STAB] EE after stabilization: "
          f"L=({ee_l_post[0,0]:.4f},{ee_l_post[0,1]:.4f},{ee_l_post[0,2]:.4f}) "
          f"R=({ee_r_post[0,0]:.4f},{ee_r_post[0,1]:.4f},{ee_r_post[0,2]:.4f})")

    return (finger_vel, hand_body_left, hand_body_right,
            jac_body_left, jac_body_right,
            round(grip_l_final * 1000, 2), round(grip_r_final * 1000, 2))


# ---------------------------------------------------------------------------
# LIFT: JT IK lift — NO cable teleport
# ---------------------------------------------------------------------------
def do_lift(sim, scene, device, lift_z,
            hand_body_left, hand_body_right,
            jac_body_left, jac_body_right,
            finger_vel, env_idx=0,
            frames=None, cameras=None):
    """Physical lift: JT IK arms + velocity finger grip. Cable follows via friction only.

    Returns dict with cable_z_delta, grip_width evolution, convergence, NaN status.
    """
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    # Record initial state — use grasped segments (near grippers) not mean of all
    cable = scene["cable"]
    n_bodies = cable.data.body_pos_w.shape[1]
    seg_z = [cable.data.body_pos_w[env_idx, i, 2].item() for i in range(n_bodies)]

    # Find grasped segments: nearest to each gripper by Y coordinate
    gc_y_l = robot_left.data.body_pos_w[env_idx,
               robot_left.find_bodies("panda_leftfinger")[0][0], 1].item()
    gc_y_r = robot_right.data.body_pos_w[env_idx,
               robot_right.find_bodies("panda_leftfinger")[0][0], 1].item()
    cable_y = [cable.data.body_pos_w[env_idx, i, 1].item() for i in range(n_bodies)]
    grasp_seg_l = min(range(n_bodies), key=lambda i: abs(cable_y[i] - gc_y_l))
    grasp_seg_r = min(range(n_bodies), key=lambda i: abs(cable_y[i] - gc_y_r))
    # Use average of the two grasped segments' Z as the reference
    cable_z_before = (seg_z[grasp_seg_l] + seg_z[grasp_seg_r]) / 2.0
    cable_z_mean_before = sum(seg_z) / len(seg_z)

    grip_l_init, grip_r_init = get_grip_width(robot_left, robot_right, env_idx)
    # v20 diag: report both finger joints at lift start
    lj7_i = robot_left.data.joint_pos[env_idx, 7].item() * 1000
    lj8_i = robot_left.data.joint_pos[env_idx, 8].item() * 1000
    rj7_i = robot_right.data.joint_pos[env_idx, 7].item() * 1000
    rj8_i = robot_right.data.joint_pos[env_idx, 8].item() * 1000
    print(f"  [LIFT_DIAG] Finger joints at lift start:")
    print(f"    Left:  j7={lj7_i:.2f}mm j8={lj8_i:.2f}mm (gap=j7+j8={lj7_i+lj8_i:.2f}mm)")
    print(f"    Right: j7={rj7_i:.2f}mm j8={rj7_i:.2f}mm (gap=j7+j8={rj7_i+rj8_i:.2f}mm)")
    cable_mid_before = get_cable_midpoint(cable, env_idx)

    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_final_l = ee_start_l.clone()
    ee_final_r = ee_start_r.clone()
    ee_final_l[env_idx, 2] += lift_z
    ee_final_r[env_idx, 2] += lift_z

    n_steps = int(lift_z * 100 * LIFT_STEPS_PER_CM)  # steps proportional to lift height
    n_steps = max(n_steps, 50)

    # Per-segment cable Z for diagnostics
    seg_z_str = " ".join(f"{z:.4f}" for z in seg_z)
    print(f"  [LIFT] Cable segments ({n_bodies}): Z = [{seg_z_str}]")
    print(f"  [LIFT] Grasped segs: L=seg{grasp_seg_l}(Y={cable_y[grasp_seg_l]:.4f}) "
          f"R=seg{grasp_seg_r}(Y={cable_y[grasp_seg_r]:.4f})")
    print(f"  [LIFT] cable_z_before={cable_z_before:.4f} (grasped avg) "
          f"mean={cable_z_mean_before:.4f}")
    print(f"  [LIFT] Target: +{lift_z*1000:.0f}mm, steps={n_steps}, "
          f"NO cable teleport (physical friction only)")

    grip_history = []
    converged = False
    nan_detected = False
    fix2_count = 0
    clamp_log = []

    for step in range(n_steps):
        # Interpolated target: gradual lift to prevent IK overshoot
        t = min((step + 1) / n_steps, 1.0)
        ee_target_l = ee_start_l.clone()
        ee_target_l[env_idx, 2] = ee_start_l[env_idx, 2] + lift_z * t
        ee_target_r = ee_start_r.clone()
        ee_target_r[env_idx, 2] = ee_start_r[env_idx, 2] + lift_z * t

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_target_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_target_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log)
        if nan_l.any() or nan_r.any():
            print(f"  [LIFT] IK NaN at step {step}")
            break

        # v17: PD targets for force generation + velocity damping to prevent overshoot.
        # PD generates contact forces during sim.step(), then we zero arm velocities
        # to prevent momentum accumulation (overshoot). Arm moves incrementally
        # but can't build up speed.
        _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_vel, env_idx)

        # Sim substeps — NO cable writes
        for _ in range(LIFT_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())
            # Zero arm velocities to prevent PD overshoot accumulation
            vel_l = robot_left.data.joint_vel.clone()
            vel_l[env_idx, :7] = 0.0
            robot_left.write_joint_velocity_to_sim(vel_l)
            vel_r = robot_right.data.joint_vel.clone()
            vel_r[env_idx, :7] = 0.0
            robot_right.write_joint_velocity_to_sim(vel_r)

        # NaN check
        if check_cable_nan(cable):
            print(f"  [LIFT] Cable NaN at step {step}!")
            nan_detected = True
            break

        # Track grip width
        gl, gr = get_grip_width(robot_left, robot_right, env_idx)
        grip_history.append({"step": step, "grip_l_mm": gl, "grip_r_mm": gr})

        # Video (every step for short lifts)
        if frames is not None and cameras is not None:
            capture_frame(scene, cameras, frames)

        # Convergence check against FINAL target (not interpolated)
        ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
        z_err_l = abs(ee_cur_l[env_idx, 2].item() - ee_final_l[env_idx, 2].item())
        z_err_r = abs(ee_cur_r[env_idx, 2].item() - ee_final_r[env_idx, 2].item())

        # Step-level diagnostic for first 5 steps
        if step < 5:
            ee_z_l = ee_cur_l[env_idx, 2].item()
            ee_z_r = ee_cur_r[env_idx, 2].item()
            tgt_z_l = ee_target_l[env_idx, 2].item()
            tgt_z_r = ee_target_r[env_idx, 2].item()
            print(f"  [LIFT_DIAG] step={step} t={t:.4f} "
                  f"tgt_z_L={tgt_z_l:.4f} cur_z_L={ee_z_l:.4f} "
                  f"tgt_z_R={tgt_z_r:.4f} cur_z_R={ee_z_r:.4f} "
                  f"dq_L_max={ik_l[env_idx].abs().max().item():.6f} "
                  f"dq_R_max={ik_r[env_idx].abs().max().item():.6f}")

        if step % 40 == 0:
            cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()
            print(f"  [LIFT] step={step} z_err_L={z_err_l:.4f} R={z_err_r:.4f} "
                  f"cable_z={cable_z:.4f} grip_L={gl:.1f}mm R={gr:.1f}mm")

        if z_err_l < 0.002 and z_err_r < 0.002:
            print(f"  [LIFT] Converged at step {step}")
            converged = True
            break

    # Settle
    _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                   env_idx, SETTLE_STEPS)

    # Final measurements — use same grasped segments as before
    seg_z_final = [cable.data.body_pos_w[env_idx, i, 2].item() for i in range(n_bodies)]
    cable_z_after = (seg_z_final[grasp_seg_l] + seg_z_final[grasp_seg_r]) / 2.0
    cable_z_delta = cable_z_after - cable_z_before
    grip_l_final, grip_r_final = get_grip_width(robot_left, robot_right, env_idx)
    grip_increase_l = grip_l_final - grip_l_init
    grip_increase_r = grip_r_final - grip_r_init

    # v20 diag: report both finger joints (j7=finger1, j8=finger2)
    lj7 = robot_left.data.joint_pos[env_idx, 7].item() * 1000
    lj8 = robot_left.data.joint_pos[env_idx, 8].item() * 1000
    rj7 = robot_right.data.joint_pos[env_idx, 7].item() * 1000
    rj8 = robot_right.data.joint_pos[env_idx, 8].item() * 1000
    print(f"  [LIFT_DIAG] Finger joints after lift:")
    print(f"    Left:  j7={lj7:.2f}mm j8={lj8:.2f}mm (gap=j7+j8={lj7+lj8:.2f}mm)")
    print(f"    Right: j7={rj7:.2f}mm j8={rj8:.2f}mm (gap=j7+j8={rj7+rj8:.2f}mm)")

    fix2_count = sum(1 for c in clamp_log if c)

    seg_z_final_str = " ".join(f"{z:.4f}" for z in seg_z_final)
    seg_deltas = [seg_z_final[i] - seg_z[i] for i in range(n_bodies)]
    seg_delta_str = " ".join(f"{d*1000:+.1f}" for d in seg_deltas)
    print(f"  [LIFT] Cable segments Z after: [{seg_z_final_str}]")
    print(f"  [LIFT] Cable segment deltas (mm): [{seg_delta_str}]")
    print(f"  [LIFT] cable_z_delta={cable_z_delta*1000:.1f}mm "
          f"(target={lift_z*1000:.0f}mm)")
    print(f"  [LIFT] grip change: L={grip_increase_l:+.1f}mm R={grip_increase_r:+.1f}mm")
    if fix2_count:
        print(f"  [LIFT] Fix2 activated {fix2_count} times")

    return {
        "cable_z_delta_mm": round(cable_z_delta * 1000, 2),
        "target_mm": round(lift_z * 1000, 0),
        "converged": converged,
        "nan_detected": nan_detected,
        "grip_l_init_mm": round(grip_l_init, 2),
        "grip_r_init_mm": round(grip_r_init, 2),
        "grip_l_final_mm": round(grip_l_final, 2),
        "grip_r_final_mm": round(grip_r_final, 2),
        "grip_increase_l_mm": round(grip_increase_l, 2),
        "grip_increase_r_mm": round(grip_increase_r, 2),
        "fix2_vel_clamp_count": fix2_count,
        "steps_used": step + 1 if 'step' in dir() else 0,
    }


# ---------------------------------------------------------------------------
# ROUTE: JT IK horizontal move — NO cable teleport
# ---------------------------------------------------------------------------
def do_route(sim, scene, device, route_dx, route_dy,
             hand_body_left, hand_body_right,
             jac_body_left, jac_body_right,
             finger_vel, env_idx=0,
             frames=None, cameras=None):
    """Physical route: move arms horizontally. Cable follows via friction only."""
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

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

    init_sep_y = abs(ee_start_l[env_idx, 1].item() - ee_start_r[env_idx, 1].item())

    # Initial cable midpoint
    cable_mid_init = get_cable_midpoint(cable, env_idx)
    grip_l_init, grip_r_init = get_grip_width(robot_left, robot_right, env_idx)

    print(f"  [ROUTE] Distance={route_dist*1000:.1f}mm, steps={n_interp}, "
          f"speed={route_dist/n_interp*1000:.2f}mm/step")
    print(f"  [ROUTE] NO cable teleport (physical friction only)")

    clamp_log_l = []
    clamp_log_r = []
    ik_failures = 0
    max_sep_drift = 0.0
    cable_mid_history = []
    grip_history = []
    dynamic_lift_applied = False
    dynamic_lift_z = 0.0  # cumulative Z offset from dynamic lift

    # Dynamic grasped segment tracking
    TABLE_Z_THRESHOLD = 0.78  # TABLE_HEIGHT(0.75) + 30mm clearance

    for step in range(n_interp):
        t = (step + 1) / n_interp

        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx, 0] = ee_start_l[env_idx, 0] + route_dx * t
        ee_tgt_l[env_idx, 1] = ee_start_l[env_idx, 1] + route_dy * t
        ee_tgt_l[env_idx, 2] = ee_start_l[env_idx, 2] + dynamic_lift_z
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx, 0] = ee_start_r[env_idx, 0] + route_dx * t
        ee_tgt_r[env_idx, 1] = ee_start_r[env_idx, 1] + route_dy * t
        ee_tgt_r[env_idx, 2] = ee_start_r[env_idx, 2] + dynamic_lift_z

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_l)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_r)
        if nan_l.any() or nan_r.any():
            ik_failures += 1
            if ik_failures > 10:
                print(f"  [ROUTE] Too many IK NaN ({ik_failures}), abort at step {step}")
                break
            continue

        _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_vel, env_idx)

        # Sim substeps — NO cable writes, NO velocity damping (kills route movement)
        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())

        # NaN check
        if check_cable_nan(cable):
            print(f"  [ROUTE] Cable NaN at step {step}!")
            break

        # Track metrics
        gl, gr = get_grip_width(robot_left, robot_right, env_idx)
        grip_history.append({"step": step, "grip_l_mm": gl, "grip_r_mm": gr})

        # Dynamic lift: check nearest grasped segments, lift +10mm once if below threshold
        if not dynamic_lift_applied:
            sl_dyn, _, sr_dyn, _ = find_nearest_segments(
                cable, robot_left, robot_right,
                hand_body_left, hand_body_right, env_idx)
            seg_z = cable.data.body_pos_w[env_idx, :, 2]
            grasped_z_avg = (seg_z[sl_dyn].item() + seg_z[sr_dyn].item()) / 2.0
            if grasped_z_avg < TABLE_Z_THRESHOLD:
                dynamic_lift_z = 0.010  # +10mm
                dynamic_lift_applied = True
                print(f"  [ROUTE] DYNAMIC LIFT triggered at step {step}: "
                      f"grasped_z_avg={grasped_z_avg:.4f} < {TABLE_Z_THRESHOLD:.2f}, "
                      f"applying +{dynamic_lift_z*1000:.0f}mm Z offset")

        cable_mid = get_cable_midpoint(cable, env_idx)
        cable_mid_history.append({
            "step": step,
            "x": round(cable_mid[0].item(), 4),
            "y": round(cable_mid[1].item(), 4),
            "z": round(cable_mid[2].item(), 4),
        })

        # Separation drift
        cur_sep_y = abs(robot_left.data.body_pos_w[env_idx, hand_body_left, 1].item() -
                        robot_right.data.body_pos_w[env_idx, hand_body_right, 1].item())
        sep_drift = abs(cur_sep_y - init_sep_y)
        max_sep_drift = max(max_sep_drift, sep_drift)

        # Video
        if frames is not None and cameras is not None and step % 2 == 0:
            capture_frame(scene, cameras, frames)

        # Dynamic grasp tracking every 100 steps in route
        if step % 100 == 0:
            sl_rt, dl_rt, sr_rt, dr_rt = find_nearest_segments(
                cable, robot_left, robot_right,
                hand_body_left, hand_body_right, env_idx)
            seg_z_l_rt = cable.data.body_pos_w[env_idx, sl_rt, 2].item()
            seg_z_r_rt = cable.data.body_pos_w[env_idx, sr_rt, 2].item()
            print(f"  [ROUTE step={step}] GRASP: L=seg{sl_rt}(d={dl_rt:.1f}mm z={seg_z_l_rt:.4f}) "
                  f"R=seg{sr_rt}(d={dr_rt:.1f}mm z={seg_z_r_rt:.4f})")

        # Progress
        if step % (n_interp // 5 + 1) == 0 or step == n_interp - 1:
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            xy_err_l = math.sqrt((ee_cur_l[0].item() - ee_end_l[env_idx, 0].item())**2 +
                                 (ee_cur_l[1].item() - ee_end_l[env_idx, 1].item())**2)
            xy_err_r = math.sqrt((ee_cur_r[0].item() - ee_end_r[env_idx, 0].item())**2 +
                                 (ee_cur_r[1].item() - ee_end_r[env_idx, 1].item())**2)
            cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()
            print(f"  [ROUTE] step={step}/{n_interp} t={t:.2f} "
                  f"xy_err L={xy_err_l*1000:.1f}mm R={xy_err_r*1000:.1f}mm "
                  f"cable_z={cable_z:.4f} grip L={gl:.1f}mm R={gr:.1f}mm")

    # Settle
    _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                   env_idx, SETTLE_STEPS)

    # Final measurements
    cable_nan = check_cable_nan(cable)
    ee_final_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    xy_err_l = math.sqrt((ee_final_l[0].item() - ee_end_l[env_idx, 0].item())**2 +
                         (ee_final_l[1].item() - ee_end_l[env_idx, 1].item())**2)
    xy_err_r = math.sqrt((ee_final_r[0].item() - ee_end_r[env_idx, 0].item())**2 +
                         (ee_final_r[1].item() - ee_end_r[env_idx, 1].item())**2)

    cable_mid_final = get_cable_midpoint(cable, env_idx)
    cable_mid_disp = math.sqrt(
        (cable_mid_final[0].item() - cable_mid_init[0].item())**2 +
        (cable_mid_final[1].item() - cable_mid_init[1].item())**2)

    grip_l_final, grip_r_final = get_grip_width(robot_left, robot_right, env_idx)
    cable_z_final = cable.data.body_pos_w[env_idx, :, 2].mean().item()

    n_clamp_l = sum(1 for c in clamp_log_l if c)
    n_clamp_r = sum(1 for c in clamp_log_r if c)

    # Cable Z min tracking (catenary sag diagnostic)
    cable_z_min = min(h["z"] for h in cable_mid_history) if cable_mid_history else cable_z_final
    cable_z_init_route = cable_mid_history[0]["z"] if cable_mid_history else cable_z_final

    print(f"  [ROUTE] Final: xy_err L={xy_err_l*1000:.1f}mm R={xy_err_r*1000:.1f}mm")
    print(f"  [ROUTE] Cable midpoint displacement: {cable_mid_disp*1000:.1f}mm "
          f"(target={route_dist*1000:.1f}mm)")
    print(f"  [ROUTE] Grip: L={grip_l_final:.1f}mm R={grip_r_final:.1f}mm "
          f"(init L={grip_l_init:.1f}mm R={grip_r_init:.1f}mm)")
    print(f"  [ROUTE] Cable Z: init={cable_z_init_route:.4f} min={cable_z_min:.4f} "
          f"final={cable_z_final:.4f} (sag={cable_z_init_route-cable_z_min:.4f})")
    if n_clamp_l + n_clamp_r > 0:
        print(f"  [ROUTE] Fix2 vel clamp: L={n_clamp_l} R={n_clamp_r}")

    return {
        "xy_error_l_mm": round(xy_err_l * 1000, 2),
        "xy_error_r_mm": round(xy_err_r * 1000, 2),
        "cable_midpoint_disp_mm": round(cable_mid_disp * 1000, 2),
        "cable_z_final": round(cable_z_final, 4),
        "grip_l_final_mm": round(grip_l_final, 2),
        "grip_r_final_mm": round(grip_r_final, 2),
        "grip_increase_l_mm": round(grip_l_final - grip_l_init, 2),
        "grip_increase_r_mm": round(grip_r_final - grip_r_init, 2),
        "sep_drift_max_mm": round(max_sep_drift * 1000, 2),
        "ik_failures": ik_failures,
        "cable_nan": cable_nan,
        "fix2_vel_clamp_l": n_clamp_l,
        "fix2_vel_clamp_r": n_clamp_r,
        "route_steps_used": step + 1 if 'step' in dir() else 0,
        "cable_z_min": round(cable_z_min, 4),
        "cable_z_sag_mm": round((cable_z_init_route - cable_z_min) * 1000, 2),
        "dynamic_lift_applied": dynamic_lift_applied,
        "dynamic_lift_mm": round(dynamic_lift_z * 1000, 1),
    }


# ---------------------------------------------------------------------------
# R2 MOVE: Generic arm move — NO cable teleport
# ---------------------------------------------------------------------------
def do_r2_move(sim, scene, device,
               hand_body_left, hand_body_right,
               jac_body_left, jac_body_right,
               finger_vel, target_l, target_r, speed,
               label="MOVE", env_idx=0,
               frames=None, cameras=None):
    """Move arms independently. Cable is fully under physics (no kinematic writes)."""
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

    tgt_pos_l = ee_start_l.clone()
    tgt_pos_l[env_idx] = torch.tensor(target_l, device=device, dtype=torch.float32)
    tgt_pos_r = ee_start_r.clone()
    tgt_pos_r[env_idx] = torch.tensor(target_r, device=device, dtype=torch.float32)

    dist_l = torch.norm(tgt_pos_l[env_idx] - ee_start_l[env_idx]).item()
    dist_r = torch.norm(tgt_pos_r[env_idx] - ee_start_r[env_idx]).item()
    max_dist = max(dist_l, dist_r)

    if max_dist < 0.001:
        print(f"  [{label}] Already at target")
        return {"success": True, "ee_error_l_mm": 0.0, "ee_error_r_mm": 0.0,
                "cable_nan": False, "cable_z": 0.0, "steps_used": 0}

    n_steps_l = max(int(dist_l / speed), 10)
    n_steps_r = max(int(dist_r / speed), 10)
    n_steps = max(n_steps_l, n_steps_r)
    n_steps = min(n_steps, 3000)

    print(f"  [{label}] dist_L={dist_l*1000:.1f}mm R={dist_r*1000:.1f}mm "
          f"steps={n_steps} (NO cable teleport)")

    clamp_log_l = []
    clamp_log_r = []
    ik_failures = 0

    # v22k: Grip recovery pause interval (every PAUSE_INTERVAL steps, hold for PAUSE_STEPS)
    GRIP_PAUSE_INTERVAL = 400
    GRIP_PAUSE_STEPS = 30

    for step in range(n_steps):
        # v22k: Periodic grip recovery pause
        if step > 0 and step % GRIP_PAUSE_INTERVAL == 0:
            gl_pre, gr_pre = get_grip_width(robot_left, robot_right, env_idx)
            _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                           env_idx, n_steps=GRIP_PAUSE_STEPS)
            gl_post, gr_post = get_grip_width(robot_left, robot_right, env_idx)
            print(f"  [{label} GRIP_PAUSE step={step}] grip L={gl_pre:.1f}→{gl_post:.1f}mm "
                  f"R={gr_pre:.1f}→{gr_post:.1f}mm")

        # v22j: Synchronize arm arrival — both arms reach target at same step
        t_l = min((step + 1) / n_steps, 1.0)
        t_r = min((step + 1) / n_steps, 1.0)

        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx] = ee_start_l[env_idx] + (tgt_pos_l[env_idx] - ee_start_l[env_idx]) * t_l
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx] = ee_start_r[env_idx] + (tgt_pos_r[env_idx] - ee_start_r[env_idx]) * t_r

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_l)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT, clamp_log=clamp_log_r)

        if nan_l.any() or nan_r.any():
            ik_failures += 1
            if ik_failures > 10:
                print(f"  [{label}] Too many IK NaN, abort at step {step}")
                return {"success": False, "ee_error_l_mm": 999, "ee_error_r_mm": 999,
                        "cable_nan": False, "cable_z": 0.0, "steps_used": step}
            continue

        _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_vel, env_idx)

        # Sim substeps — NO cable writes
        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())

        if check_cable_nan(cable):
            print(f"  [{label}] Cable NaN at step {step}!")
            return {"success": False, "ee_error_l_mm": 999, "ee_error_r_mm": 999,
                    "cable_nan": True, "cable_z": 0.0, "steps_used": step,
                    "nan_step": step}

        if frames is not None and cameras is not None and step % 2 == 0:
            capture_frame(scene, cameras, frames)

        # Dynamic grasp tracking + grip loss detection every 100 steps
        if step % 100 == 0:
            sl, dl, sr, dr = find_nearest_segments(
                cable, robot_left, robot_right,
                hand_body_left, hand_body_right, env_idx)
            seg_z_l = cable.data.body_pos_w[env_idx, sl, 2].item()
            seg_z_r = cable.data.body_pos_w[env_idx, sr, 2].item()
            fj_l7 = robot_left.data.joint_pos[env_idx, 7].item() * 1000
            fj_r7 = robot_right.data.joint_pos[env_idx, 7].item() * 1000
            # Contact force (if available)
            cf_l_mag = cf_r_mag = None
            cf_l_str = cf_r_str = "N/A"
            if "contact_left_cable" in scene.keys():
                cf_l = scene["contact_left_cable"].data.net_forces_w[env_idx]
                cf_l_mag = torch.norm(cf_l).item()
                cf_l_str = f"{cf_l_mag:.1f}N"
            if "contact_right_cable" in scene.keys():
                cf_r = scene["contact_right_cable"].data.net_forces_w[env_idx]
                cf_r_mag = torch.norm(cf_r).item()
                cf_r_str = f"{cf_r_mag:.1f}N"
            print(f"  [{label} step={step}] GRASP: L=seg{sl}(d={dl:.1f}mm z={seg_z_l:.4f}) "
                  f"R=seg{sr}(d={dr:.1f}mm z={seg_z_r:.4f}) "
                  f"fj L={fj_l7:.1f}mm R={fj_r7:.1f}mm "
                  f"contact L={cf_l_str} R={cf_r_str}")
            # Grip loss check: contact force primary, distance fallback
            # hand_body center is ~100mm above fingertips, so 3D dist includes Z offset
            grip_lost = False
            grip_loss_side = ""
            if cf_l_mag is not None and cf_r_mag is not None:
                # Contact force available: < 1.0N = loss
                if cf_l_mag < 1.0:
                    grip_lost, grip_loss_side = True, "L(contact<1N)"
                elif cf_r_mag < 1.0:
                    grip_lost, grip_loss_side = True, "R(contact<1N)"
            else:
                # Fallback: distance-based (v18f: 250mm threshold — cable axially slides
                # through fingers during arm separation but stays within friction cone)
                if dl > 250.0:
                    grip_lost, grip_loss_side = True, "L(dist>250mm)"
                elif dr > 250.0:
                    grip_lost, grip_loss_side = True, "R(dist>250mm)"
            if grip_lost:
                print(f"  [GRIP_LOSS] step={step} source={grip_loss_side} "
                      f"L: seg{sl} d={dl:.1f}mm cf={cf_l_str} "
                      f"R: seg{sr} d={dr:.1f}mm cf={cf_r_str} -> cycle abort")
                return {"success": False, "ee_error_l_mm": 999, "ee_error_r_mm": 999,
                        "cable_nan": False, "cable_z": 0.0, "steps_used": step,
                        "grip_loss": True, "grip_loss_step": step,
                        "grip_loss_side": grip_loss_side}

        if step % (n_steps // 5 + 1) == 0 or step == n_steps - 1:
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            err_l = torch.norm(ee_cur_l - tgt_pos_l[env_idx]).item()
            err_r = torch.norm(ee_cur_r - tgt_pos_r[env_idx]).item()
            cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()
            gl, gr = get_grip_width(robot_left, robot_right, env_idx)
            # Dynamic nearest-segment tracking
            sl, dl, sr, dr = find_nearest_segments(
                cable, robot_left, robot_right,
                hand_body_left, hand_body_right, env_idx)
            gz_l = cable.data.body_pos_w[env_idx, sl, 2].item()
            gz_r = cable.data.body_pos_w[env_idx, sr, 2].item()
            ee_z_l = ee_cur_l[2].item()
            ee_z_r = ee_cur_r[2].item()
            t_progress = (step + 1) / n_steps
            print(f"  [{label}] step={step}/{n_steps} t={t_progress:.2f} "
                  f"ee_err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm "
                  f"cable_z={cable_z:.4f} grip L={gl:.1f}mm R={gr:.1f}mm")
            print(f"  [{label}]   DIAG: ee_z L={ee_z_l:.4f} R={ee_z_r:.4f} "
                  f"nearest L=seg{sl}(z={gz_l:.4f},d={dl:.1f}mm) "
                  f"R=seg{sr}(z={gz_r:.4f},d={dr:.1f}mm)")

    # Post-interpolation convergence: target fixed at final position
    CONVERGE_EXTRA_MAX = 500
    CONVERGE_THRESHOLD = 0.015  # 15mm (with margin for settle drift)
    ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    err_l = torch.norm(ee_cur_l - tgt_pos_l[env_idx]).item()
    err_r = torch.norm(ee_cur_r - tgt_pos_r[env_idx]).item()
    if err_l > CONVERGE_THRESHOLD or err_r > CONVERGE_THRESHOLD:
        print(f"  [{label}] Post-interp convergence: err L={err_l*1000:.1f}mm "
              f"R={err_r*1000:.1f}mm, running up to {CONVERGE_EXTRA_MAX} extra steps")
        for extra in range(CONVERGE_EXTRA_MAX):
            # v19e: alpha=2.0 (was 10.0) to prevent IK oscillation during convergence.
            # At Phase 5 configuration, alpha=10.0 causes left arm to oscillate ±270mm.
            ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                      tgt_pos_l, 2.0, 0.02, device,
                                      vel_limit=JOINT_VEL_LIMIT)
            ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                      tgt_pos_r, 2.0, 0.02, device,
                                      vel_limit=JOINT_VEL_LIMIT)
            if nan_l.any() or nan_r.any():
                break
            _apply_joints(robot_left, robot_right, ik_l, ik_r, finger_vel, env_idx)
            for _ in range(ROUTE_IK_SUBSTEPS):
                sim.step()
                scene.update(sim.get_physics_dt())
            if check_cable_nan(cable):
                print(f"  [{label}] Cable NaN during convergence at extra step {extra}!")
                break
            if frames is not None and cameras is not None and extra % 4 == 0:
                capture_frame(scene, cameras, frames)
            ee_cur_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
            ee_cur_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
            err_l = torch.norm(ee_cur_l - tgt_pos_l[env_idx]).item()
            err_r = torch.norm(ee_cur_r - tgt_pos_r[env_idx]).item()
            if extra % 50 == 0:
                print(f"  [{label}] converge step={extra} err L={err_l*1000:.1f}mm "
                      f"R={err_r*1000:.1f}mm")
            # v19e: GRASP_TRACK + ee_pos every 100 steps (was missing)
            if extra % 100 == 0 or extra == CONVERGE_EXTRA_MAX - 1:
                sl, dl, sr, dr = find_nearest_segments(
                    cable, robot_left, robot_right,
                    hand_body_left, hand_body_right, env_idx)
                print(f"  [{label}] converge GRASP_TRACK step={extra}: "
                      f"L=seg{sl} dist={dl:.1f}mm  R=seg{sr} dist={dr:.1f}mm")
                print(f"  [{label}] converge ee_pos step={extra}: "
                      f"L=({ee_cur_l[0].item():.4f},{ee_cur_l[1].item():.4f},{ee_cur_l[2].item():.4f}) "
                      f"R=({ee_cur_r[0].item():.4f},{ee_cur_r[1].item():.4f},{ee_cur_r[2].item():.4f})")
            if err_l < CONVERGE_THRESHOLD and err_r < CONVERGE_THRESHOLD:
                print(f"  [{label}] Converged at extra step {extra}: "
                      f"err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm")
                break

    # Settle
    _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                   env_idx, SETTLE_STEPS)

    # Final
    ee_final_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3]
    ee_final_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3]
    err_l = torch.norm(ee_final_l - tgt_pos_l[env_idx]).item()
    err_r = torch.norm(ee_final_r - tgt_pos_r[env_idx]).item()
    cable_nan = check_cable_nan(cable)
    cable_z = cable.data.body_pos_w[env_idx, :, 2].mean().item()

    success = (err_l < 0.020 and err_r < 0.020 and not cable_nan)
    n_clamp_l = sum(1 for c in clamp_log_l if c)
    n_clamp_r = sum(1 for c in clamp_log_r if c)
    if n_clamp_l + n_clamp_r > 0:
        print(f"  [{label}] Fix2: L={n_clamp_l} R={n_clamp_r}")

    print(f"  [{label}] Final: ee_err L={err_l*1000:.1f}mm R={err_r*1000:.1f}mm "
          f"cable_z={cable_z:.4f}")

    return {
        "success": success,
        "ee_error_l_mm": round(err_l * 1000, 2),
        "ee_error_r_mm": round(err_r * 1000, 2),
        "cable_nan": cable_nan,
        "cable_z": round(cable_z, 4),
        "steps_used": n_steps,
        "ik_failures": ik_failures,
        "vel_clamp_l": n_clamp_l,
        "vel_clamp_r": n_clamp_r,
    }


# ---------------------------------------------------------------------------
# RELEASE: Open grippers, wait, check cable
# ---------------------------------------------------------------------------
def do_release(sim, scene, device,
               hand_body_left, hand_body_right, env_idx=0):
    """Open grippers gradually, wait 5s, check cable on hook."""
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    arm_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_r = robot_right.data.joint_pos[env_idx, :7].clone()

    print(f"  [R2d-RELEASE] Stabilize {RELEASE_STABILIZE_STEPS} steps (grip hold)...")
    _hold_position(sim, scene, robot_left, robot_right, FINGER_GRIP_VEL,
                   env_idx, RELEASE_STABILIZE_STEPS)

    # Open grippers: velocity = FINGER_OPEN_VEL (positive = opening)
    print(f"  [R2d-RELEASE] Opening grippers ({RELEASE_GRIPPER_STEPS} steps, "
          f"vel={FINGER_OPEN_VEL}m/s)...")
    _hold_position(sim, scene, robot_left, robot_right, FINGER_OPEN_VEL,
                   env_idx, RELEASE_GRIPPER_STEPS)

    # Wait 5 seconds for cable to settle (fingers open, vel=0)
    wait_steps = 2400  # ~5s @ 480Hz
    print(f"  [R2d-RELEASE] Waiting {wait_steps} steps (~5s)...")
    _hold_position(sim, scene, robot_left, robot_right, 0.0,
                   env_idx, wait_steps)

    cable_nan = check_cable_nan(cable)
    cable_z_final = cable.data.body_pos_w[env_idx, :, 2].mean().item()
    cable_mid = get_cable_midpoint(cable, env_idx)
    cable_mid_xy_dist = math.sqrt((cable_mid[0].item() - HOOK_X)**2 +
                                  (cable_mid[1].item() - HOOK_Y)**2)

    # Success: cable_z > 0.78 (HOOK_Z - 0.02) AND cable near hook XY
    cable_on_hook = (not cable_nan and
                     cable_z_final > 0.78 and
                     cable_mid_xy_dist < 0.020)

    print(f"  [R2d-RELEASE] cable_z={cable_z_final:.4f} hook_z={HOOK_Z:.2f} "
          f"mid_xy_dist={cable_mid_xy_dist*1000:.1f}mm on_hook={cable_on_hook}")

    return {
        "gripper_opened": True,
        "cable_on_hook": cable_on_hook,
        "cable_z_final": round(cable_z_final, 4),
        "cable_mid_xy_dist_mm": round(cable_mid_xy_dist * 1000, 2),
        "hook_z": HOOK_Z,
        "cable_nan": cable_nan,
    }


# ---------------------------------------------------------------------------
# RUN_EPISODE: orchestrate stages
# ---------------------------------------------------------------------------
def run_episode(sim, scene, device, stage, episode_idx, output_dir):
    """Run physical pipeline for a given stage."""
    cable = scene["cable"]
    env_idx = 0

    frames = [] if args.record_video else None
    cameras = ["overhead_camera", "front_left_camera"] if args.record_video else None

    results = {"stage": stage, "episode": episode_idx, "overall": "FAIL"}

    # === TELEPORT + CLOSE (common to all stages) ===
    print(f"\n  [TELEPORT+CLOSE] Phase 2 teleport + PD close")
    (finger_vel, hbl, hbr, jbl, jbr,
     grip_l_mm, grip_r_mm) = do_teleport_and_close(sim, scene, device)
    results["grip_l_mm"] = grip_l_mm
    results["grip_r_mm"] = grip_r_mm

    # Gate: grip check
    if grip_l_mm > 7.0 or grip_r_mm > 7.0:
        print(f"  [GATE] FAIL: grip too wide L={grip_l_mm}mm R={grip_r_mm}mm (>7mm)")
        results["fail_reason"] = "grip_too_wide"
        return results

    # Record initial cable Z
    cable_z_init = cable.data.body_pos_w[env_idx, :, 2].mean().item()
    results["cable_z_init"] = round(cable_z_init, 4)

    # === STAGE 0a: Lift 20mm ===
    if stage in ("0a", "0b", "0c", "0d", "0e", "all"):
        print(f"\n  {'='*50}")
        print(f"  [STAGE 0a] Physical lift 20mm")
        print(f"  {'='*50}")
        lift_0a = do_lift(sim, scene, device, 0.020,
                          hbl, hbr, jbl, jbr, finger_vel,
                          frames=frames, cameras=cameras)
        results["stage_0a"] = lift_0a

        # Gate
        if lift_0a["nan_detected"]:
            results["fail_reason"] = "0a_nan"
            return results
        if lift_0a["cable_z_delta_mm"] < 15.0:
            print(f"  [GATE 0a] FAIL: cable_z_delta={lift_0a['cable_z_delta_mm']:.1f}mm < 15mm")
            results["fail_reason"] = "0a_lift_insufficient"
            return results

        print(f"  [GATE 0a] PASS: cable_z_delta={lift_0a['cable_z_delta_mm']:.1f}mm")
        log_seg_xyz(cable, "after_0a", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_0a", env_idx)

        if stage == "0a":
            results["overall"] = "PASS"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0a_ep{episode_idx}.mp4"))
            return results

    # === STAGE 0b: Lift to 70mm total (continue from 20mm) ===
    if stage in ("0b", "0c", "0d", "0e", "all"):
        print(f"\n  {'='*50}")
        print(f"  [STAGE 0b] Physical lift additional 50mm (total 70mm)")
        print(f"  {'='*50}")
        lift_0b = do_lift(sim, scene, device, 0.050,  # additional 50mm (catenary fix)
                          hbl, hbr, jbl, jbr, finger_vel,
                          frames=frames, cameras=cameras)
        results["stage_0b"] = lift_0b

        # Gate: total cable lift > 40mm (sum of grasped-segment deltas)
        total_lift = lift_0a["cable_z_delta_mm"] + lift_0b["cable_z_delta_mm"]
        results["total_lift_mm"] = round(total_lift, 2)

        if lift_0b["nan_detected"]:
            results["fail_reason"] = "0b_nan"
            return results

        # Check grip slip
        grip_inc_l = lift_0b["grip_increase_l_mm"]
        grip_inc_r = lift_0b["grip_increase_r_mm"]
        if grip_inc_l > SLIP_THRESHOLD_MM or grip_inc_r > SLIP_THRESHOLD_MM:
            print(f"  [GATE 0b] WARN: possible slip "
                  f"(grip_inc L={grip_inc_l:+.1f}mm R={grip_inc_r:+.1f}mm)")

        if total_lift < 55.0:
            print(f"  [GATE 0b] FAIL: total_lift={total_lift:.1f}mm < 55mm")
            results["fail_reason"] = "0b_lift_insufficient"
            return results

        print(f"  [GATE 0b] PASS: total_lift={total_lift:.1f}mm")
        log_seg_xyz(cable, "after_0b", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_0b", env_idx)

        if stage == "0b":
            results["overall"] = "PASS"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0b_ep{episode_idx}.mp4"))
            return results

    # === STAGE 0c: Route 50mm ===
    if stage in ("0c", "0d", "0e", "all"):
        # Approximate route to hook direction (50mm)
        ee_l = scene["robot_left"].data.body_pos_w[env_idx, hbl, :3]
        ee_r = scene["robot_right"].data.body_pos_w[env_idx, hbr, :3]
        mid = (ee_l + ee_r) / 2.0
        full_dx = HOOK_X - mid[0].item()
        full_dy = HOOK_Y - mid[1].item()
        full_dist = math.sqrt(full_dx**2 + full_dy**2)
        scale_50 = 0.050 / full_dist if full_dist > 0.001 else 0.0
        dx_50 = full_dx * scale_50
        dy_50 = full_dy * scale_50

        print(f"\n  {'='*50}")
        print(f"  [STAGE 0c] Physical route 50mm toward hook")
        print(f"  {'='*50}")
        route_0c = do_route(sim, scene, device, dx_50, dy_50,
                            hbl, hbr, jbl, jbr, finger_vel,
                            frames=frames, cameras=cameras)
        results["stage_0c"] = route_0c

        if route_0c["cable_nan"]:
            results["fail_reason"] = "0c_nan"
            return results

        # Gate: cable midpoint displacement > 30mm
        if route_0c["cable_midpoint_disp_mm"] < 30.0:
            print(f"  [GATE 0c] FAIL: cable_disp={route_0c['cable_midpoint_disp_mm']:.1f}mm < 30mm")
            results["fail_reason"] = "0c_cable_not_following"
            return results

        grip_inc = max(route_0c["grip_increase_l_mm"], route_0c["grip_increase_r_mm"])
        if grip_inc > SLIP_THRESHOLD_MM:
            print(f"  [GATE 0c] WARN: possible slip (grip_inc={grip_inc:.1f}mm)")

        print(f"  [GATE 0c] PASS: cable_disp={route_0c['cable_midpoint_disp_mm']:.1f}mm")
        log_seg_xyz(cable, "after_0c", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_0c", env_idx)

        if stage == "0c":
            results["overall"] = "PASS"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0c_ep{episode_idx}.mp4"))
            return results

    # === STAGE 0d: Route remaining distance (total ~131mm from grasp) ===
    if stage in ("0d", "0e", "all"):
        # Compute remaining distance to hook
        ee_l = scene["robot_left"].data.body_pos_w[env_idx, hbl, :3]
        ee_r = scene["robot_right"].data.body_pos_w[env_idx, hbr, :3]
        mid = (ee_l + ee_r) / 2.0
        remain_dx = HOOK_X - mid[0].item()
        remain_dy = HOOK_Y - mid[1].item()
        remain_dist = math.sqrt(remain_dx**2 + remain_dy**2)

        print(f"\n  {'='*50}")
        print(f"  [STAGE 0d] Physical route remaining {remain_dist*1000:.1f}mm to hook")
        print(f"  {'='*50}")
        route_0d = do_route(sim, scene, device, remain_dx, remain_dy,
                            hbl, hbr, jbl, jbr, finger_vel,
                            frames=frames, cameras=cameras)
        results["stage_0d"] = route_0d

        if route_0d["cable_nan"]:
            results["fail_reason"] = "0d_nan"
            return results

        # Gate: cable midpoint displacement > 60% of remaining distance
        min_disp = remain_dist * 0.6 * 1000
        if route_0d["cable_midpoint_disp_mm"] < min_disp:
            print(f"  [GATE 0d] FAIL: cable_disp={route_0d['cable_midpoint_disp_mm']:.1f}mm "
                  f"< {min_disp:.1f}mm")
            results["fail_reason"] = "0d_cable_not_following"
            return results

        grip_inc = max(route_0d["grip_increase_l_mm"], route_0d["grip_increase_r_mm"])
        if grip_inc > 5.0:  # relaxed threshold for long route
            print(f"  [GATE 0d] WARN: grip increase {grip_inc:.1f}mm > 5mm")

        print(f"  [GATE 0d] PASS: cable_disp={route_0d['cable_midpoint_disp_mm']:.1f}mm")
        log_seg_xyz(cable, "after_0d", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_0d", env_idx)

        if stage == "0d":
            results["overall"] = "PASS"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0d_ep{episode_idx}.mp4"))
            return results

    # === STAGE 0e: R2a-R2d ===
    if stage in ("0e", "all"):
        print(f"\n  {'='*50}")
        print(f"  [STAGE 0e] Physical R2a-R2d (hook placement)")
        print(f"  {'='*50}")

        # Grip re-tightening before R2a (catenary fix)
        robot_left = scene["robot_left"]
        robot_right = scene["robot_right"]
        gl_pre, gr_pre = get_grip_width(robot_left, robot_right, env_idx)
        print(f"\n  [RE-TIGHTEN] Before R2a: grip L={gl_pre:.1f}mm R={gr_pre:.1f}mm")
        # v22: retighten with grip velocity (squeeze inward)
        _hold_position(sim, scene, robot_left, robot_right, FINGER_GRIP_VEL,
                       env_idx, 50)
        gl_post, gr_post = get_grip_width(robot_left, robot_right, env_idx)
        print(f"  [RE-TIGHTEN] After 50 steps: grip L={gl_post:.1f}mm R={gr_post:.1f}mm "
              f"(delta L={gl_post-gl_pre:+.2f}mm R={gr_post-gr_pre:+.2f}mm)")
        results["retighten"] = {
            "grip_l_before_mm": round(gl_pre, 2),
            "grip_r_before_mm": round(gr_pre, 2),
            "grip_l_after_mm": round(gl_post, 2),
            "grip_r_after_mm": round(gr_post, 2),
        }

        # R2a: Arm Separation
        print(f"\n  [R2a] Arm Separation -> Phase 4.5")
        r2a = do_r2_move(sim, scene, device, hbl, hbr, jbl, jbr, finger_vel,
                         target_l=WAYPOINT_PHASE45_LEFT,
                         target_r=WAYPOINT_PHASE45_RIGHT,
                         speed=ROUTE_SPEED_M_PER_STEP, label="R2a",
                         frames=frames, cameras=cameras)
        results["r2a"] = r2a
        if r2a.get("grip_loss"):
            print(f"  [R2a] GRIP_LOSS at step {r2a['grip_loss_step']} ({r2a['grip_loss_side']})")
            results["fail_reason"] = "r2a_grip_loss"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))
            return results
        if not r2a["success"]:
            print(f"  [R2a] FAIL")
            results["fail_reason"] = "r2a_fail"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))
            return results
        print(f"  [R2a] PASS")
        log_seg_xyz(cable, "after_R2a", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_R2a", env_idx)

        # v22j: Re-tighten grip between R2a and R2b
        gl_pre, gr_pre = get_grip_width(robot_left, robot_right, env_idx)
        _hold_position(sim, scene, robot_left, robot_right, finger_vel,
                       env_idx, n_steps=50)
        gl_post, gr_post = get_grip_width(robot_left, robot_right, env_idx)
        print(f"\n  [RE-TIGHTEN R2a→R2b] grip L={gl_pre:.1f}→{gl_post:.1f}mm "
              f"R={gr_pre:.1f}→{gr_post:.1f}mm")

        # R2b: Ascend (speed /4 for IK convergence)
        print(f"\n  [R2b] Ascend -> Phase 5 (Z=1.09)")
        r2b = do_r2_move(sim, scene, device, hbl, hbr, jbl, jbr, finger_vel,
                         target_l=WAYPOINT_PHASE5_LEFT,
                         target_r=WAYPOINT_PHASE5_RIGHT,
                         speed=ROUTE_SPEED_M_PER_STEP / 4, label="R2b",
                         frames=frames, cameras=cameras)
        results["r2b"] = r2b
        if r2b.get("grip_loss"):
            print(f"  [R2b] GRIP_LOSS at step {r2b['grip_loss_step']} ({r2b['grip_loss_side']})")
            results["fail_reason"] = "r2b_grip_loss"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))
            return results
        if not r2b["success"]:
            print(f"  [R2b] FAIL")
            results["fail_reason"] = "r2b_fail"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))
            return results
        print(f"  [R2b] PASS")
        log_seg_xyz(cable, "after_R2b", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_R2b", env_idx)

        # R2c: Descend (cable physics always active — no mode switch needed)
        print(f"\n  [R2c] Descend -> Phase 5.5 (Z=1.02)")
        r2c = do_r2_move(sim, scene, device, hbl, hbr, jbl, jbr, finger_vel,
                         target_l=WAYPOINT_PHASE55_LEFT,
                         target_r=WAYPOINT_PHASE55_RIGHT,
                         speed=ROUTE_SPEED_M_PER_STEP / 2, label="R2c",
                         frames=frames, cameras=cameras)
        results["r2c"] = r2c
        cable_z = r2c.get("cable_z", 0.0)
        if r2c.get("grip_loss"):
            print(f"  [R2c] GRIP_LOSS at step {r2c['grip_loss_step']} ({r2c['grip_loss_side']})")
            results["fail_reason"] = "r2c_grip_loss"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))
            return results
        if r2c["cable_nan"]:
            results["fail_reason"] = "r2c_nan"
            if frames and output_dir:
                save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))
            return results
        print(f"  [R2c] cable_z={cable_z:.4f}")
        log_seg_xyz(cable, "after_R2c", env_idx)
        log_grasp_track(cable, scene["robot_left"], scene["robot_right"],
                        hbl, hbr, "after_R2c", env_idx)

        # R2d: Move to retreat position
        print(f"\n  [R2d] Retreat -> Phase 6")
        r2d_move = do_r2_move(sim, scene, device, hbl, hbr, jbl, jbr,
                              finger_vel,
                              target_l=WAYPOINT_PHASE6_LEFT,
                              target_r=WAYPOINT_PHASE6_RIGHT,
                              speed=ROUTE_SPEED_M_PER_STEP, label="R2d-MOVE",
                              frames=frames, cameras=cameras)
        results["r2d_move"] = r2d_move

        # Release
        release = do_release(sim, scene, device, hbl, hbr)
        results["r2d_release"] = release

        if frames and output_dir:
            # Capture final state
            if cameras:
                for _ in range(10):
                    capture_frame(scene, cameras, frames)
            save_video(frames, os.path.join(output_dir, f"stage0e_ep{episode_idx}.mp4"))

        # Final gate: cable on hook
        if release["cable_on_hook"]:
            print(f"  [GATE 0e] PASS: cable on hook!")
            results["overall"] = "PASS"
        else:
            print(f"  [GATE 0e] FAIL: cable NOT on hook "
                  f"(z={release['cable_z_final']:.4f}, "
                  f"mid_dist={release['cable_mid_xy_dist_mm']:.1f}mm)")
            results["fail_reason"] = "0e_cable_not_on_hook"

        return results

    results["overall"] = "PASS"
    return results


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    device = f"cuda:{app_launcher.device_id}"
    stage = args.stage or "0a"  # default: start with 0a
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print(f"[PHYSICAL PIPELINE] Stage={stage} Device={device} "
          f"Episodes={args.num_episodes}")
    print(f"[PHYSICAL PIPELINE] Fix 1 REMOVED. Fix 2 active (JOINT_VEL_LIMIT={JOINT_VEL_LIMIT})")
    print(f"[PHYSICAL PIPELINE] NO cable.write_root_pose_to_sim()")
    print(f"[PHYSICAL PIPELINE] NO cable.write_joint_state_to_sim()")

    # Scene setup — use default cable (v17_highdamp, 10 segments)
    # v19_seg5 only spans 0.48m (5 bodies, 4 joints × 0.12m) — doesn't reach grippers at Y=±0.250
    # v17 has 10 segments with finer spacing that covers the full grip span
    # N=1 avoids the PhysX N-dependency bug, so v17 is safe here
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=5.0)
    print(f"[PHYSICAL PIPELINE] Using default cable (v17_highdamp, 10 segments)")

    physx_cfg = sim_utils.PhysxCfg(
        solver_type=0,  # PGS
        max_position_iteration_count=32,
        max_velocity_iteration_count=1,
        bounce_threshold_velocity=0.5,
        enable_stabilization=True,
    )
    sim_cfg = sim_utils.SimulationCfg(
        device=device,
        dt=PHYSICS_DT,
        physx=physx_cfg,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)

    # Reset
    sim.reset()
    scene.reset()

    all_results = {
        "stage": stage,
        "device": device,
        "fix1_removed": True,
        "fix2_active": True,
        "joint_vel_limit": JOINT_VEL_LIMIT,
        "episodes": [],
        "n_pass": 0,
        "n_fail": 0,
    }

    start_time = time.time()

    for ep in range(args.num_episodes):
        print(f"\n{'='*60}")
        print(f"  EPISODE {ep+1}/{args.num_episodes} — Stage {stage}")
        print(f"{'='*60}")

        # Reset scene
        sim.reset()
        scene.reset()

        # Run episode
        ep_result = run_episode(sim, scene, device, stage, ep, output_dir)
        all_results["episodes"].append(ep_result)

        if ep_result["overall"] == "PASS":
            all_results["n_pass"] += 1
            print(f"\n  >>> EPISODE {ep+1}: PASS <<<")
        else:
            all_results["n_fail"] += 1
            reason = ep_result.get("fail_reason", "unknown")
            print(f"\n  >>> EPISODE {ep+1}: FAIL ({reason}) <<<")

    elapsed = time.time() - start_time
    all_results["elapsed_s"] = round(elapsed, 1)
    all_results["overall"] = "PASS" if all_results["n_fail"] == 0 else "FAIL"
    all_results["pass_rate"] = f"{all_results['n_pass']}/{args.num_episodes}"

    # Save metrics
    metrics_path = os.path.join(output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[PHYSICAL PIPELINE] Results saved to {metrics_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY: Stage {stage}")
    print(f"  Pass rate: {all_results['pass_rate']}")
    print(f"  Overall: {all_results['overall']}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
    sim_app.close()
