"""test_r1b_nan_debug.py — R1b Cable NaN diagnostic.

Runs R1b full route (131mm, 0.5mm/step) with detailed per-step logging
around steps 200-230 to diagnose cable NaN root cause.

Records: EE positions, IK targets, joint velocities, cable segment positions,
step-to-step deltas.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--output_dir", type=str, default="data/test_r1b_debug")
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
    ROUTE_SPEED_M_PER_STEP, ROUTE_IK_SUBSTEPS,
    ROUTE_MAX_STEPS,
)

# Constants
FINGERTIP_OFFSET = 0.1123
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001
LIFT_Z = 0.05
LIFT_STEPS = 200
CLOSE_STEPS = 100
SETTLE_STEPS = 50

# Debug range
DEBUG_START = 200
DEBUG_END = 230


def jt_ik_step(robot, jac_body, hand_body, target_pos, alpha, clip, device):
    ee_pos = robot.data.body_pos_w[:, hand_body, :3]
    error = target_pos - ee_pos
    jacobian = robot.root_physx_view.get_jacobians()[:, jac_body, :3, :7]
    dq = alpha * torch.bmm(jacobian.transpose(1, 2), error.unsqueeze(-1)).squeeze(-1)
    dq = dq.clamp(-clip, clip)
    new_q = robot.data.joint_pos[:, :7] + dq
    nan_mask = torch.isnan(new_q).any(dim=1)
    return new_q, nan_mask


def main():
    device = f"cuda:{app_launcher.device_id}"
    print(f"[NaN Debug] Device: {device}")
    print(f"[NaN Debug] Route speed: {ROUTE_SPEED_M_PER_STEP*1000:.1f}mm/step")

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
    env_idx = 0
    N = 1

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    # --- Teleport ---
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

        for _ in range(ROUTE_IK_SUBSTEPS):
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

        z_err = abs(robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() -
                    ee_target_l[env_idx, 2].item())
        if z_err < 0.002:
            print(f"  [LIFT] Converged at step {step}")
            break

    print(f"  [LIFT] EE post-lift: "
          f"L=({robot_left.data.body_pos_w[env_idx, hand_body_left, 0]:.4f},"
          f"{robot_left.data.body_pos_w[env_idx, hand_body_left, 1]:.4f},"
          f"{robot_left.data.body_pos_w[env_idx, hand_body_left, 2]:.4f}) "
          f"R=({robot_right.data.body_pos_w[env_idx, hand_body_right, 0]:.4f},"
          f"{robot_right.data.body_pos_w[env_idx, hand_body_right, 1]:.4f},"
          f"{robot_right.data.body_pos_w[env_idx, hand_body_right, 2]:.4f})")

    # --- Route with detailed debug logging ---
    approx_dx = HOOK_X - 0.295
    approx_dy = HOOK_Y - 0.001
    route_dist = math.sqrt(approx_dx**2 + approx_dy**2)

    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_end_l = ee_start_l.clone()
    ee_end_l[env_idx, 0] += approx_dx
    ee_end_l[env_idx, 1] += approx_dy
    ee_end_r = ee_start_r.clone()
    ee_end_r[env_idx, 0] += approx_dx
    ee_end_r[env_idx, 1] += approx_dy

    n_interp = max(int(route_dist / ROUTE_SPEED_M_PER_STEP), 10)
    n_interp = min(n_interp, ROUTE_MAX_STEPS)

    print(f"  [ROUTE] Distance={route_dist*1000:.1f}mm, steps={n_interp}")
    print(f"  [ROUTE] Debug range: steps {DEBUG_START}-{DEBUG_END}")

    # Previous step state for delta computation
    prev_ee_l = None
    prev_ee_r = None
    prev_ik_tgt_l = None
    prev_ik_tgt_r = None
    prev_cable_root = None

    debug_steps = []
    nan_step = None

    for step in range(n_interp):
        t = (step + 1) / n_interp

        # Interpolated IK targets
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx, 0] = ee_start_l[env_idx, 0] + approx_dx * t
        ee_tgt_l[env_idx, 1] = ee_start_l[env_idx, 1] + approx_dy * t
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx, 0] = ee_start_r[env_idx, 0] + approx_dx * t
        ee_tgt_r[env_idx, 1] = ee_start_r[env_idx, 1] + approx_dy * t

        # JT IK
        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device)
        if nan_l.any() or nan_r.any():
            print(f"  [ROUTE] IK NaN at step {step}")
            continue

        # Apply joints
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

        # Substeps + kinematic cable
        for _ in range(ROUTE_IK_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())
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

        # --- Gather debug data ---
        ee_l = robot_left.data.body_pos_w[env_idx, hand_body_left, :3].clone().cpu().tolist()
        ee_r = robot_right.data.body_pos_w[env_idx, hand_body_right, :3].clone().cpu().tolist()
        ik_tgt_l = [ee_tgt_l[env_idx, i].item() for i in range(3)]
        ik_tgt_r = [ee_tgt_r[env_idx, i].item() for i in range(3)]
        jv_l = robot_left.data.joint_vel[env_idx, :7].clone().cpu().tolist()
        jv_r = robot_right.data.joint_vel[env_idx, :7].clone().cpu().tolist()

        cable_root = cable.data.root_pos_w[env_idx, :3].clone().cpu().tolist()
        # Cable segment positions (all bodies)
        cable_seg_pos = cable.data.body_pos_w[env_idx, :, :3].clone().cpu()
        n_seg = cable_seg_pos.shape[0]
        cable_seg_list = cable_seg_pos.tolist()

        # Compute max segment stretch (distance between adjacent segments)
        max_stretch = 0.0
        seg_dists = []
        for si in range(n_seg - 1):
            d = torch.sqrt(((cable_seg_pos[si+1] - cable_seg_pos[si])**2).sum()).item()
            seg_dists.append(d)
            max_stretch = max(max_stretch, d)

        # Check NaN
        cable_has_nan = torch.isnan(cable.data.body_pos_w).any().item()

        # Compute deltas
        ee_delta_l = [abs(ee_l[i] - prev_ee_l[i]) for i in range(3)] if prev_ee_l else [0, 0, 0]
        ee_delta_r = [abs(ee_r[i] - prev_ee_r[i]) for i in range(3)] if prev_ee_r else [0, 0, 0]
        ik_tgt_delta_l = [abs(ik_tgt_l[i] - prev_ik_tgt_l[i]) for i in range(3)] if prev_ik_tgt_l else [0, 0, 0]
        ik_tgt_delta_r = [abs(ik_tgt_r[i] - prev_ik_tgt_r[i]) for i in range(3)] if prev_ik_tgt_r else [0, 0, 0]
        cable_root_delta = [abs(cable_root[i] - prev_cable_root[i]) for i in range(3)] if prev_cable_root else [0, 0, 0]

        # Displacement from start
        mid_start_x = (ee_start_l[env_idx, 0].item() + ee_start_r[env_idx, 0].item()) / 2.0
        mid_start_y = (ee_start_l[env_idx, 1].item() + ee_start_r[env_idx, 1].item()) / 2.0
        mid_cur_x = (ee_l[0] + ee_r[0]) / 2.0
        mid_cur_y = (ee_l[1] + ee_r[1]) / 2.0
        cumulative_disp = math.sqrt((mid_cur_x - mid_start_x)**2 + (mid_cur_y - mid_start_y)**2)

        # Log in debug range or at NaN
        if DEBUG_START <= step <= DEBUG_END or cable_has_nan:
            entry = {
                "step": step,
                "t": round(t, 4),
                "cumulative_displacement_mm": round(cumulative_disp * 1000, 2),
                "left_ee_pos": [round(v, 5) for v in ee_l],
                "left_ee_delta_mm": [round(v * 1000, 3) for v in ee_delta_l],
                "right_ee_pos": [round(v, 5) for v in ee_r],
                "right_ee_delta_mm": [round(v * 1000, 3) for v in ee_delta_r],
                "left_ik_target": [round(v, 5) for v in ik_tgt_l],
                "left_ik_target_delta_mm": [round(v * 1000, 3) for v in ik_tgt_delta_l],
                "right_ik_target": [round(v, 5) for v in ik_tgt_r],
                "right_ik_target_delta_mm": [round(v * 1000, 3) for v in ik_tgt_delta_r],
                "left_joint_vel_max": round(max(abs(v) for v in jv_l), 4),
                "right_joint_vel_max": round(max(abs(v) for v in jv_r), 4),
                "left_joint_vel": [round(v, 4) for v in jv_l],
                "right_joint_vel": [round(v, 4) for v in jv_r],
                "cable_root_pos": [round(v, 5) for v in cable_root],
                "cable_root_delta_mm": [round(v * 1000, 3) for v in cable_root_delta],
                "cable_n_segments": n_seg,
                "cable_max_segment_dist_mm": round(max_stretch * 1000, 3),
                "cable_segment_dists_mm": [round(d * 1000, 3) for d in seg_dists],
                "cable_segment_positions": [[round(v, 5) for v in seg] for seg in cable_seg_list],
                "nan_detected": cable_has_nan,
            }
            debug_steps.append(entry)
            disp_str = f"disp={cumulative_disp*1000:.1f}mm"
            ee_d_l = max(ee_delta_l) * 1000
            ee_d_r = max(ee_delta_r) * 1000
            jv_max_l = max(abs(v) for v in jv_l)
            jv_max_r = max(abs(v) for v in jv_r)
            print(f"  [DBG] step={step} {disp_str} "
                  f"ee_dL={ee_d_l:.2f}mm ee_dR={ee_d_r:.2f}mm "
                  f"jvL={jv_max_l:.3f} jvR={jv_max_r:.3f} "
                  f"seg_max={max_stretch*1000:.2f}mm "
                  f"{'NaN!' if cable_has_nan else ''}")

        if cable_has_nan:
            nan_step = step
            print(f"  [ROUTE] Cable NaN at step {step}! cumulative_disp={cumulative_disp*1000:.1f}mm")
            break

        # Progress (sparse log outside debug range)
        if step % (n_interp // 5 + 1) == 0:
            xy_err_l = math.sqrt((ee_l[0] - ee_end_l[env_idx, 0].item())**2 +
                                 (ee_l[1] - ee_end_l[env_idx, 1].item())**2)
            print(f"  [ROUTE] step={step}/{n_interp} t={t:.2f} "
                  f"xy_err_L={xy_err_l*1000:.1f}mm disp={cumulative_disp*1000:.1f}mm")

        # Update prev
        prev_ee_l = ee_l
        prev_ee_r = ee_r
        prev_ik_tgt_l = ik_tgt_l
        prev_ik_tgt_r = ik_tgt_r
        prev_cable_root = cable_root

    # --- Analysis ---
    analysis = {}
    if debug_steps:
        valid_steps = [s for s in debug_steps if not s["nan_detected"]]
        if valid_steps:
            analysis["max_ee_delta_l_mm"] = max(max(s["left_ee_delta_mm"]) for s in valid_steps)
            analysis["max_ee_delta_r_mm"] = max(max(s["right_ee_delta_mm"]) for s in valid_steps)
            analysis["max_joint_vel_l"] = max(s["left_joint_vel_max"] for s in valid_steps)
            analysis["max_joint_vel_r"] = max(s["right_joint_vel_max"] for s in valid_steps)
            analysis["max_ik_target_delta_l_mm"] = max(max(s["left_ik_target_delta_mm"]) for s in valid_steps)
            analysis["max_ik_target_delta_r_mm"] = max(max(s["right_ik_target_delta_mm"]) for s in valid_steps)
            analysis["max_cable_segment_dist_mm"] = max(s["cable_max_segment_dist_mm"] for s in valid_steps)

            last_valid = valid_steps[-1]
            analysis["last_valid_step"] = last_valid["step"]
            analysis["last_valid_displacement_mm"] = last_valid["cumulative_displacement_mm"]
            analysis["last_valid_cable_max_seg_dist_mm"] = last_valid["cable_max_segment_dist_mm"]

            # Hypothesis evaluation
            last_ee_d_l = max(last_valid["left_ee_delta_mm"])
            last_ee_d_r = max(last_valid["right_ee_delta_mm"])
            if last_ee_d_l < 2.0 and last_ee_d_r < 2.0:
                analysis["hypothesis_a_evidence"] = (
                    f"EE deltas small ({last_ee_d_l:.2f}/{last_ee_d_r:.2f}mm) at last valid step. "
                    "Supports cable cumulative displacement limit (Hypothesis A)."
                )
            else:
                analysis["hypothesis_b_evidence"] = (
                    f"EE deltas large ({last_ee_d_l:.2f}/{last_ee_d_r:.2f}mm) at last valid step. "
                    "Supports arm rapid motion (Hypothesis B)."
                )

            # Check for velocity spikes
            if len(valid_steps) > 3:
                mean_jv_l = sum(s["left_joint_vel_max"] for s in valid_steps[:3]) / 3
                mean_jv_r = sum(s["right_joint_vel_max"] for s in valid_steps[:3]) / 3
                for s in valid_steps:
                    if s["left_joint_vel_max"] > mean_jv_l * 3 or s["right_joint_vel_max"] > mean_jv_r * 3:
                        analysis["velocity_spike_detected"] = {
                            "step": s["step"],
                            "left_max": s["left_joint_vel_max"],
                            "right_max": s["right_joint_vel_max"],
                            "baseline_l": round(mean_jv_l, 4),
                            "baseline_r": round(mean_jv_r, 4),
                        }
                        break

    output = {
        "steps": debug_steps,
        "nan_step": nan_step,
        "last_valid_step": debug_steps[-2]["step"] if len(debug_steps) >= 2 and debug_steps[-1]["nan_detected"] else (debug_steps[-1]["step"] if debug_steps else None),
        "analysis": analysis,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, "nan_trace.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[NaN Debug] Trace saved: {out_path}")
    print(f"[NaN Debug] NaN step: {nan_step}")
    if analysis:
        print(f"[NaN Debug] Analysis: {json.dumps(analysis, indent=2)}")


if __name__ == "__main__":
    main()
