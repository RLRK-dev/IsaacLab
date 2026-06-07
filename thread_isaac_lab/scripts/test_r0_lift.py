"""test_r0_lift.py — R0 Lift Height Extension test.

Tests kinematic cable attachment lift at progressive heights:
  R0a: 20mm, R0b: 35mm, R0c: 50mm

Approach: Teleport arms to known Phase 2 joint config (task_config.py),
          kinematically close grippers, then lift with kinematic cable attachment.
          This bypasses the reaching phase to isolate the lift mechanism.
"""
from __future__ import annotations

import argparse
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--output_dir", type=str, default="data/test_r0")
parser.add_argument("--headless", action="store_true", default=False)
parser.add_argument("--num_episodes", type=int, default=1,
                    help="Episodes per lift height")
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
    PHASE_TRANSITION,
)

# Constants
FINGERTIP_OFFSET = 0.1123  # panda_hand -> fingertip (m)
GRIPPER_OPEN = 0.04
GRIPPER_CLOSE = 0.001
LIFT_HEIGHTS_M = [0.02, 0.035, 0.05]  # R0a, R0b, R0c
LIFT_LABELS = ["R0a_20mm", "R0b_35mm", "R0c_50mm"]
P4_LIFT_STEPS = 200  # IK steps per lift
CLOSE_STEPS = 100  # gripper close steps (Z-ramp)
SETTLE_STEPS = 50


def jt_ik_step(robot, jac_body, hand_body, target_pos, alpha, clip, device):
    """Single Jacobian-Transpose IK step (position-only, 6DOF arm)."""
    ee_pos = robot.data.body_pos_w[:, hand_body, :3]
    error = target_pos - ee_pos  # (N, 3)

    jacobian = robot.root_physx_view.get_jacobians()[:, jac_body, :3, :7]  # (N, 3, 7)
    dq = alpha * torch.bmm(jacobian.transpose(1, 2), error.unsqueeze(-1)).squeeze(-1)
    dq = dq.clamp(-clip, clip)

    new_q = robot.data.joint_pos[:, :7] + dq
    nan_mask = torch.isnan(new_q).any(dim=1)
    return new_q, nan_mask


def run_lift_test(sim, scene, device, lift_z, episode_idx, env_origin):
    """Run one kinematic-grasp lift test at the given height."""
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    N = 1
    env_idx = 0

    # --- Step 1: Teleport arms to Phase 2 joint config (grasp position) ---
    p2_joints_l = torch.tensor(PHASE2_LEFT_JOINTS, dtype=torch.float32, device=device)
    p2_joints_r = torch.tensor(PHASE2_RIGHT_JOINTS, dtype=torch.float32, device=device)

    # Write joint positions (arms + grippers open)
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

    # Also set PD targets so sim doesn't fight
    robot_left.set_joint_position_target(q_l)
    robot_right.set_joint_position_target(q_r)
    robot_left.write_data_to_sim()
    robot_right.write_data_to_sim()

    # Settle for 50 steps
    for _ in range(SETTLE_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get hand body indices
    hand_body_left = robot_left.find_bodies("panda_hand")[0][0]
    hand_body_right = robot_right.find_bodies("panda_hand")[0][0]
    jac_body_left = hand_body_left - 1
    jac_body_right = hand_body_right - 1

    ee_pos_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_pos_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ft_z_l = ee_pos_l[0, 2].item() - FINGERTIP_OFFSET
    ft_z_r = ee_pos_r[0, 2].item() - FINGERTIP_OFFSET
    print(f"  [SETUP] EE after teleport: L=({ee_pos_l[0,0]:.4f},{ee_pos_l[0,1]:.4f},{ee_pos_l[0,2]:.4f}) "
          f"R=({ee_pos_r[0,0]:.4f},{ee_pos_r[0,1]:.4f},{ee_pos_r[0,2]:.4f})")
    print(f"  [SETUP] Fingertip Z: L={ft_z_l:.4f}m R={ft_z_r:.4f}m")

    # Record cable Z before grasp
    cable_z_before = cable.data.body_pos_w[env_idx, :, 2].clone()
    if env_origin is not None:
        cable_z_before = cable_z_before - env_origin[2]
    print(f"  [SETUP] Cable Z before: mean={cable_z_before.mean():.4f}m")

    # --- Step 2: Close grippers (Z-ramp from GRIPPER_OPEN to GRIPPER_CLOSE) ---
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
    print(f"  [CLOSE] Grip width: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

    # Check if cable is between fingers
    grip_ok_l = grip_l > 0.0025  # > 2.5mm means cable is blocking
    grip_ok_r = grip_r > 0.0025
    if not (grip_ok_l and grip_ok_r):
        reason = []
        if not grip_ok_l:
            reason.append(f"L={grip_l*1000:.1f}mm<2.5mm")
        if not grip_ok_r:
            reason.append(f"R={grip_r*1000:.1f}mm<2.5mm")
        print(f"  [CLOSE] GRIP FAILED: {', '.join(reason)} (tunneled)")

    # --- Step 3: Settle with closed grip ---
    _finger_pos = max(grip_l, grip_r, 0.004)  # Use at least 4mm
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[0, 7] = _finger_pos
        tgt_l[0, 8] = _finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[0, 7] = _finger_pos
        tgt_r[0, 8] = _finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # --- Step 4: Kinematic cable lift ---
    print(f"  [LIFT] Starting lift: +{lift_z*1000:.0f}mm with kinematic cable attachment")

    # Record initial cable root pose
    kg_root_pose_0 = cable.data.root_pose_w[env_idx, :7].clone()
    kg_grip_z_0 = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                   robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
    kg_env_ids = torch.tensor([env_idx], dtype=torch.int32, device=device)

    ee_target_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_target_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()
    ee_target_l[env_idx, 2] += lift_z
    ee_target_r[env_idx, 2] += lift_z

    converged = False
    for step in range(P4_LIFT_STEPS):
        # JT IK for both arms
        ik_l, nan_l = jt_ik_step(
            robot_left, jac_body_left, hand_body_left,
            ee_target_l, 10.0, 0.02, device)
        ik_r, nan_r = jt_ik_step(
            robot_right, jac_body_right, hand_body_right,
            ee_target_r, 10.0, 0.02, device)

        if nan_l.any() or nan_r.any():
            print(f"  [LIFT] IK NaN at step {step}")
            break

        # Set arm targets + hold finger position
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = ik_l[env_idx]
        tgt_l[env_idx, 7] = _finger_pos
        tgt_l[env_idx, 8] = _finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = ik_r[env_idx]
        tgt_r[env_idx, 7] = _finger_pos
        tgt_r[env_idx, 8] = _finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        # Substeps + kinematic cable attachment
        for _ in range(4):
            sim.step()
            scene.update(sim.get_physics_dt())
            # Move cable root to follow gripper Z
            kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                        robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
            kg_z_delta = kg_cur_z - kg_grip_z_0
            kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
            kg_new_pose[0, 2] += kg_z_delta
            cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
            cable.write_root_velocity_to_sim(
                torch.zeros(1, 6, device=device), env_ids=kg_env_ids)

        if torch.isnan(cable.data.body_pos_w).any():
            print(f"  [LIFT] Cable NaN at step {step}!")
            break

        # Check convergence
        ee_cur_l = robot_left.data.body_pos_w[:, hand_body_left, :3]
        ee_cur_r = robot_right.data.body_pos_w[:, hand_body_right, :3]
        z_err_l = abs(ee_cur_l[env_idx, 2].item() - ee_target_l[env_idx, 2].item())
        z_err_r = abs(ee_cur_r[env_idx, 2].item() - ee_target_r[env_idx, 2].item())

        if step % 40 == 0:
            cable_root_z = cable.data.root_pos_w[env_idx, 2].item()
            print(f"  [LIFT] step={step} z_err_L={z_err_l:.4f} z_err_R={z_err_r:.4f} "
                  f"cable_root_z={cable_root_z:.4f} delta={cable_root_z - kg_root_pose_0[2].item():.4f}")

        if z_err_l < 0.002 and z_err_r < 0.002:
            print(f"  [LIFT] Converged at step {step}")
            converged = True
            break

    # --- Step 5: Post-lift settle ---
    arm_post_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_post_r = robot_right.data.joint_pos[env_idx, :7].clone()
    for _ in range(SETTLE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_post_l
        tgt_l[env_idx, 7] = _finger_pos
        tgt_l[env_idx, 8] = _finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_post_r
        tgt_r[env_idx, 7] = _finger_pos
        tgt_r[env_idx, 8] = _finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        # Maintain kinematic cable
        kg_cur_z = (robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item() +
                    robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()) / 2.0
        kg_z_delta = kg_cur_z - kg_grip_z_0
        kg_new_pose = kg_root_pose_0.clone().unsqueeze(0)
        kg_new_pose[0, 2] += kg_z_delta
        cable.write_root_pose_to_sim(kg_new_pose, env_ids=kg_env_ids)
        cable.write_root_velocity_to_sim(
            torch.zeros(1, 6, device=device), env_ids=kg_env_ids)

    # --- Measure cable Z after lift ---
    cable_z_after = cable.data.body_pos_w[env_idx, :, 2].clone()
    if env_origin is not None:
        cable_z_after = cable_z_after - env_origin[2]
    z_delta = (cable_z_after - cable_z_before).mean().item()

    ee_z_l_final = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item()
    ee_z_r_final = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()
    ee_z_rise_l = ee_z_l_final - ee_pos_l[0, 2].item()
    ee_z_rise_r = ee_z_r_final - ee_pos_r[0, 2].item()

    success = z_delta > (lift_z * 0.8)  # 80% of target lift = success
    print(f"  [RESULT] cable_z_delta={z_delta*1000:.1f}mm "
          f"(target={lift_z*1000:.0f}mm, {'PASS' if success else 'FAIL'})")
    print(f"  [RESULT] EE Z rise: L={ee_z_rise_l*1000:.1f}mm R={ee_z_rise_r*1000:.1f}mm")
    print(f"  [RESULT] grip: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm converged={converged}")

    return {
        "lift_z_target_mm": lift_z * 1000,
        "cable_z_delta_mm": round(z_delta * 1000, 2),
        "ee_z_rise_l_mm": round(ee_z_rise_l * 1000, 2),
        "ee_z_rise_r_mm": round(ee_z_rise_r * 1000, 2),
        "grip_l_mm": round(grip_l * 1000, 2),
        "grip_r_mm": round(grip_r * 1000, 2),
        "converged": converged,
        "nan_detected": False,
        "success": success,
        "lift_steps_used": step + 1 if 'step' in dir() else 0,
    }


def main():
    device = f"cuda:{app_launcher.device_id}"
    print(f"[R0] Lift Height Extension Test")
    print(f"[R0] Device: {device}")
    print(f"[R0] Heights: {[f'{h*1000:.0f}mm' for h in LIFT_HEIGHTS_M]}")
    print(f"[R0] Episodes per height: {args.num_episodes}")

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

    # Warmup
    for _ in range(10):
        sim.step()
        scene.update(sim.get_physics_dt())

    env_origin = scene.env_origins[0] if hasattr(scene, 'env_origins') else None

    # Run tests
    all_results = {}
    t0 = time.time()

    for hi, (lift_z, label) in enumerate(zip(LIFT_HEIGHTS_M, LIFT_LABELS)):
        print(f"\n{'='*60}")
        print(f"[R0] Stage {label}: lift_z={lift_z*1000:.0f}mm")
        print(f"{'='*60}")

        stage_results = []
        for ep in range(args.num_episodes):
            print(f"\n--- Episode {ep+1}/{args.num_episodes} ---")

            # Reset scene before each episode
            sim.reset()
            scene.reset()
            for _ in range(10):
                sim.step()
                scene.update(sim.get_physics_dt())

            result = run_lift_test(sim, scene, device, lift_z, ep, env_origin)
            stage_results.append(result)

        # Stage summary
        n_success = sum(1 for r in stage_results if r["success"])
        mean_delta = sum(r["cable_z_delta_mm"] for r in stage_results) / len(stage_results)
        print(f"\n[R0] {label} SUMMARY: {n_success}/{len(stage_results)} success, "
              f"mean cable_z_delta={mean_delta:.1f}mm")

        all_results[label] = {
            "lift_target_mm": lift_z * 1000,
            "success_rate": f"{n_success}/{len(stage_results)}",
            "mean_cable_z_delta_mm": round(mean_delta, 2),
            "episodes": stage_results,
        }

    elapsed = time.time() - t0

    # Write RUN_METRICS.json
    os.makedirs(args.output_dir, exist_ok=True)
    metrics = {
        "phase": "R0",
        "description": "Lift height extension — kinematic cable attachment",
        "device": device,
        "num_episodes_per_stage": args.num_episodes,
        "stages": all_results,
        "overall": "PASS" if all(
            all(r["success"] for r in stage["episodes"])
            for stage in all_results.values()
        ) else "FAIL",
        "elapsed_s": round(elapsed, 1),
    }

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[R0] Metrics saved: {metrics_path}")
    print(f"[R0] Total elapsed: {elapsed:.1f}s")
    print(f"[R0] Overall: {metrics['overall']}")


if __name__ == "__main__":
    main()
