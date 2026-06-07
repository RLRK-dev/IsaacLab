"""test_grip_diag.py — Grip Friction Diagnostic (minimal pipeline).

Teleport → PD close → vertical lift 200mm.
Records contact force + finger joint pos + grasped segment Z every step.
10 episodes, each completes in seconds.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=str, default="cuda:0")
parser.add_argument("--output_dir", type=str, default="data/test_grip_diag")
parser.add_argument("--headless", action="store_true", default=True)
parser.add_argument("--num_episodes", type=int, default=10)
parser.add_argument("--lift_mm", type=float, default=200.0)
parser.add_argument("--enable_ccd", action="store_true", default=False,
                    help="Enable PhysX Continuous Collision Detection")
parser.add_argument("--kin_finger_hold", action="store_true", default=False,
                    help="Kinematic finger hold during lift (override PD)")
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, device=args.device,
                           enable_cameras=True)
sim_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    JOINT_VEL_LIMIT,
)

# ---------------------------------------------------------------------------
# Constants (same as test_physical_pipeline.py)
# ---------------------------------------------------------------------------
GRIPPER_OPEN = 0.04
KIN_FINGER_STEP = 0.0002
KIN_GRIP_TARGET = 0.004
KIN_CLOSE_SUBSTEPS = 4
PD_STABILIZE_STEPS = 80
SETTLE_STEPS = 80
LIFT_SUBSTEPS = 4

# ---------------------------------------------------------------------------
# Scene with contact sensors
# ---------------------------------------------------------------------------
@configclass
class GripDiagSceneCfg(DualArmSceneCfg):
    """Scene with contact sensors for grip diagnostics."""
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0,
        history_length=1,
        track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"],
        debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0,
        history_length=1,
        track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"],
        debug_vis=False,
    )


# ---------------------------------------------------------------------------
# JT IK step (same as test_physical_pipeline.py)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
print("=" * 60)
print("GRIP FRICTION DIAGNOSTIC")
print(f"Lift: {args.lift_mm}mm, Episodes: {args.num_episodes}")
print("=" * 60)

physx_cfg = sim_utils.PhysxCfg(enable_ccd=args.enable_ccd)
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1, physx=physx_cfg)
sim = sim_utils.SimulationContext(sim_cfg)
if args.enable_ccd:
    print("[CCD] Continuous Collision Detection ENABLED")
if args.kin_finger_hold:
    print("[KIN_HOLD] Kinematic finger hold during lift ENABLED")

scene_cfg = GripDiagSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
contact_left = scene["contact_left"]
contact_right = scene["contact_right"]
device = robot_left.device
env_idx = 0

hand_body_left = robot_left.find_bodies("panda_hand")[0][0]
hand_body_right = robot_right.find_bodies("panda_hand")[0][0]
jac_body_left = hand_body_left - 1
jac_body_right = hand_body_right - 1

n_bodies = cable.data.body_pos_w.shape[1]
grasp_l_idx = n_bodies // 2   # seg5
grasp_r_idx = n_bodies - 1    # seg9

os.makedirs(args.output_dir, exist_ok=True)

all_results = []

for ep in range(args.num_episodes):
    print(f"\n{'='*60}")
    print(f"  EPISODE {ep+1}/{args.num_episodes}")
    print(f"{'='*60}")
    t0 = time.time()

    # ---- Reset scene ----
    scene.reset()
    for _ in range(20):
        sim.step()
        scene.update(sim.get_physics_dt())

    # ---- Phase 2 Teleport ----
    p2_l = torch.tensor(PHASE2_LEFT_JOINTS, dtype=torch.float32, device=device)
    p2_r = torch.tensor(PHASE2_RIGHT_JOINTS, dtype=torch.float32, device=device)

    q_l = torch.zeros(1, 9, device=device)
    q_l[0, :7] = p2_l
    q_l[0, 7] = GRIPPER_OPEN
    q_l[0, 8] = GRIPPER_OPEN
    q_r = torch.zeros(1, 9, device=device)
    q_r[0, :7] = p2_r
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

    ee_l = robot_left.data.body_pos_w[0, hand_body_left, :3]
    ee_r = robot_right.data.body_pos_w[0, hand_body_right, :3]
    print(f"  [TELEPORT] EE L=({ee_l[0]:.4f},{ee_l[1]:.4f},{ee_l[2]:.4f}) "
          f"R=({ee_r[0]:.4f},{ee_r[1]:.4f},{ee_r[2]:.4f})")

    # ---- Kinematic Close ----
    arm_hold_l = robot_left.data.joint_pos[env_idx, :7].clone()
    arm_hold_r = robot_right.data.joint_pos[env_idx, :7].clone()
    finger_pos_val = float(robot_left.data.joint_pos[env_idx, 7].item())
    n_kin_steps = int(0.040 / KIN_FINGER_STEP) + 20

    print(f"  [CLOSE] Kinematic close from {finger_pos_val*1000:.1f}mm to {KIN_GRIP_TARGET*1000:.0f}mm")

    for s in range(n_kin_steps):
        finger_pos_val = max(finger_pos_val - KIN_FINGER_STEP, 0.001)

        pos_l = robot_left.data.joint_pos.clone()
        pos_l[env_idx, :7] = arm_hold_l
        pos_l[env_idx, 7] = finger_pos_val
        pos_l[env_idx, 8] = finger_pos_val
        robot_left.write_joint_position_to_sim(pos_l)
        vel_l = robot_left.data.joint_vel.clone()
        vel_l[env_idx] = 0.0
        robot_left.write_joint_velocity_to_sim(vel_l)
        robot_left.set_joint_position_target(pos_l)
        robot_left.write_data_to_sim()

        pos_r = robot_right.data.joint_pos.clone()
        pos_r[env_idx, :7] = arm_hold_r
        pos_r[env_idx, 7] = finger_pos_val
        pos_r[env_idx, 8] = finger_pos_val
        robot_right.write_joint_position_to_sim(pos_r)
        vel_r = robot_right.data.joint_vel.clone()
        vel_r[env_idx] = 0.0
        robot_right.write_joint_velocity_to_sim(vel_r)
        robot_right.set_joint_position_target(pos_r)
        robot_right.write_data_to_sim()

        for _ in range(KIN_CLOSE_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())
            # Re-apply kinematic positions each substep
            pos_l2 = robot_left.data.joint_pos.clone()
            pos_l2[env_idx, :7] = arm_hold_l
            pos_l2[env_idx, 7] = finger_pos_val
            pos_l2[env_idx, 8] = finger_pos_val
            robot_left.write_joint_position_to_sim(pos_l2)
            vel_l2 = robot_left.data.joint_vel.clone()
            vel_l2[env_idx] = 0.0
            robot_left.write_joint_velocity_to_sim(vel_l2)
            pos_r2 = robot_right.data.joint_pos.clone()
            pos_r2[env_idx, :7] = arm_hold_r
            pos_r2[env_idx, 7] = finger_pos_val
            pos_r2[env_idx, 8] = finger_pos_val
            robot_right.write_joint_position_to_sim(pos_r2)
            vel_r2 = robot_right.data.joint_vel.clone()
            vel_r2[env_idx] = 0.0
            robot_right.write_joint_velocity_to_sim(vel_r2)

        if finger_pos_val <= KIN_GRIP_TARGET:
            break

    grip_l = robot_left.data.joint_pos[0, 7].item()
    grip_r = robot_right.data.joint_pos[0, 7].item()
    print(f"  [CLOSE] Done: L={grip_l*1000:.1f}mm R={grip_r*1000:.1f}mm")

    # ---- PD Stabilization ----
    finger_pos = KIN_GRIP_TARGET
    print(f"  [PD_STAB] {PD_STABILIZE_STEPS} steps at target={finger_pos*1000:.1f}mm")
    for _ in range(PD_STABILIZE_STEPS):
        tgt_l = robot_left.data.joint_pos.clone()
        tgt_l[env_idx, :7] = arm_hold_l
        tgt_l[env_idx, 7] = finger_pos
        tgt_l[env_idx, 8] = finger_pos
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos.clone()
        tgt_r[env_idx, :7] = arm_hold_r
        tgt_r[env_idx, 7] = finger_pos
        tgt_r[env_idx, 8] = finger_pos
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    grip_l_pd = robot_left.data.joint_pos[0, 7].item()
    grip_r_pd = robot_right.data.joint_pos[0, 7].item()
    print(f"  [PD_STAB] Done: L={grip_l_pd*1000:.1f}mm R={grip_r_pd*1000:.1f}mm")

    # ---- Record initial state ----
    seg_z_init = cable.data.body_pos_w[env_idx, :, 2].cpu().numpy().copy()
    gz_l_init = seg_z_init[grasp_l_idx]
    gz_r_init = seg_z_init[grasp_r_idx]
    ee_z_l_init = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item()
    ee_z_r_init = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()

    cf_l_init = contact_left.data.net_forces_w[0].cpu().numpy()
    cf_r_init = contact_right.data.net_forces_w[0].cpu().numpy()
    print(f"  [INIT] ee_z L={ee_z_l_init:.4f} R={ee_z_r_init:.4f}")
    print(f"  [INIT] grasped_z L(s{grasp_l_idx})={gz_l_init:.4f} R(s{grasp_r_idx})={gz_r_init:.4f}")
    print(f"  [INIT] contact_force L={np.linalg.norm(cf_l_init):.3f}N R={np.linalg.norm(cf_r_init):.3f}N")

    # ---- Vertical Lift ----
    lift_m = args.lift_mm / 1000.0
    n_lift_steps = int(lift_m / 0.0005)  # 0.5mm per step
    print(f"\n  [LIFT] {args.lift_mm}mm vertical lift ({n_lift_steps} steps, 0.5mm/step)")

    ee_start_l = robot_left.data.body_pos_w[:, hand_body_left, :3].clone()
    ee_start_r = robot_right.data.body_pos_w[:, hand_body_right, :3].clone()

    time_series = []

    for step in range(n_lift_steps):
        t = (step + 1) / n_lift_steps
        z_offset = lift_m * t

        # IK target: same XY, Z + offset
        ee_tgt_l = ee_start_l.clone()
        ee_tgt_l[env_idx, 2] += z_offset
        ee_tgt_r = ee_start_r.clone()
        ee_tgt_r[env_idx, 2] += z_offset

        ik_l, nan_l = jt_ik_step(robot_left, jac_body_left, hand_body_left,
                                  ee_tgt_l, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT)
        ik_r, nan_r = jt_ik_step(robot_right, jac_body_right, hand_body_right,
                                  ee_tgt_r, 10.0, 0.02, device,
                                  vel_limit=JOINT_VEL_LIMIT)

        if nan_l.any() or nan_r.any():
            print(f"  [LIFT] IK NaN at step {step}, skip")
            continue

        # Apply arm IK + finger PD
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

        for _ in range(LIFT_SUBSTEPS):
            sim.step()
            scene.update(sim.get_physics_dt())
            if args.kin_finger_hold:
                # Kinematic finger reset: force fingers to grip target
                pos_lk = robot_left.data.joint_pos.clone()
                pos_lk[env_idx, 7] = finger_pos
                pos_lk[env_idx, 8] = finger_pos
                robot_left.write_joint_position_to_sim(pos_lk)
                vel_lk = robot_left.data.joint_vel.clone()
                vel_lk[env_idx, 7] = 0.0
                vel_lk[env_idx, 8] = 0.0
                robot_left.write_joint_velocity_to_sim(vel_lk)
                pos_rk = robot_right.data.joint_pos.clone()
                pos_rk[env_idx, 7] = finger_pos
                pos_rk[env_idx, 8] = finger_pos
                robot_right.write_joint_position_to_sim(pos_rk)
                vel_rk = robot_right.data.joint_vel.clone()
                vel_rk[env_idx, 7] = 0.0
                vel_rk[env_idx, 8] = 0.0
                robot_right.write_joint_velocity_to_sim(vel_rk)

        # Record every step
        ee_z_l = robot_left.data.body_pos_w[env_idx, hand_body_left, 2].item()
        ee_z_r = robot_right.data.body_pos_w[env_idx, hand_body_right, 2].item()
        seg_z = cable.data.body_pos_w[env_idx, :, 2]
        gz_l = seg_z[grasp_l_idx].item()
        gz_r = seg_z[grasp_r_idx].item()
        cable_z_mean = seg_z.mean().item()

        fj_l7 = robot_left.data.joint_pos[env_idx, 7].item()
        fj_l8 = robot_left.data.joint_pos[env_idx, 8].item()
        fj_r7 = robot_right.data.joint_pos[env_idx, 7].item()
        fj_r8 = robot_right.data.joint_pos[env_idx, 8].item()

        cf_l = contact_left.data.net_forces_w[0].cpu().numpy()
        cf_r = contact_right.data.net_forces_w[0].cpu().numpy()
        cf_l_mag = float(np.linalg.norm(cf_l))
        cf_r_mag = float(np.linalg.norm(cf_r))

        record = {
            "step": step,
            "t": round(t, 4),
            "z_target_mm": round(z_offset * 1000, 2),
            "ee_z_l": round(ee_z_l, 5),
            "ee_z_r": round(ee_z_r, 5),
            "grasped_z_l": round(gz_l, 5),
            "grasped_z_r": round(gz_r, 5),
            "ee_gz_gap_l_mm": round((ee_z_l - gz_l) * 1000, 2),
            "ee_gz_gap_r_mm": round((ee_z_r - gz_r) * 1000, 2),
            "cable_z_mean": round(cable_z_mean, 5),
            "fj_l7_mm": round(fj_l7 * 1000, 2),
            "fj_l8_mm": round(fj_l8 * 1000, 2),
            "fj_r7_mm": round(fj_r7 * 1000, 2),
            "fj_r8_mm": round(fj_r8 * 1000, 2),
            "contact_l_N": round(cf_l_mag, 4),
            "contact_r_N": round(cf_r_mag, 4),
            "contact_l_xyz": [round(float(x), 4) for x in cf_l.flatten()],
            "contact_r_xyz": [round(float(x), 4) for x in cf_r.flatten()],
        }
        time_series.append(record)

        # Print summary every 10% + first/last
        if step % (n_lift_steps // 10 + 1) == 0 or step == n_lift_steps - 1:
            slip_l = "OK" if abs(ee_z_l - gz_l) < 0.050 else "SLIP"
            slip_r = "OK" if abs(ee_z_r - gz_r) < 0.050 else "SLIP"
            print(f"  [LIFT] step={step}/{n_lift_steps} z_tgt=+{z_offset*1000:.0f}mm "
                  f"ee_z L={ee_z_l:.4f} R={ee_z_r:.4f} "
                  f"gz L={gz_l:.4f}({slip_l}) R={gz_r:.4f}({slip_r}) "
                  f"fj L={fj_l7*1000:.1f}mm R={fj_r7*1000:.1f}mm "
                  f"cf L={cf_l_mag:.2f}N R={cf_r_mag:.2f}N")

    # ---- Analyze results ----
    elapsed = time.time() - t0

    # Find slip point: where ee_z - grasped_z > 50mm
    slip_step_l = None
    slip_step_r = None
    zero_contact_steps_l = 0
    zero_contact_steps_r = 0

    for rec in time_series:
        if rec["ee_gz_gap_l_mm"] > 50 and slip_step_l is None:
            slip_step_l = rec["step"]
        if rec["ee_gz_gap_r_mm"] > 50 and slip_step_r is None:
            slip_step_r = rec["step"]
        if rec["contact_l_N"] < 0.01:
            zero_contact_steps_l += 1
        if rec["contact_r_N"] < 0.01:
            zero_contact_steps_r += 1

    ep_result = {
        "episode": ep,
        "elapsed_s": round(elapsed, 1),
        "lift_mm": args.lift_mm,
        "n_steps": n_lift_steps,
        "grip_after_pd_l_mm": round(grip_l_pd * 1000, 2),
        "grip_after_pd_r_mm": round(grip_r_pd * 1000, 2),
        "ee_z_init_l": round(ee_z_l_init, 5),
        "ee_z_init_r": round(ee_z_r_init, 5),
        "grasped_z_init_l": round(float(gz_l_init), 5),
        "grasped_z_init_r": round(float(gz_r_init), 5),
        "slip_step_l": slip_step_l,
        "slip_step_r": slip_step_r,
        "slip_z_mm_l": round(time_series[slip_step_l]["z_target_mm"], 1) if slip_step_l else None,
        "slip_z_mm_r": round(time_series[slip_step_r]["z_target_mm"], 1) if slip_step_r else None,
        "zero_contact_steps_l": zero_contact_steps_l,
        "zero_contact_steps_r": zero_contact_steps_r,
        "total_steps": len(time_series),
        "final_ee_z_l": time_series[-1]["ee_z_l"] if time_series else None,
        "final_ee_z_r": time_series[-1]["ee_z_r"] if time_series else None,
        "final_grasped_z_l": time_series[-1]["grasped_z_l"] if time_series else None,
        "final_grasped_z_r": time_series[-1]["grasped_z_r"] if time_series else None,
        "final_contact_l_N": time_series[-1]["contact_l_N"] if time_series else None,
        "final_contact_r_N": time_series[-1]["contact_r_N"] if time_series else None,
    }

    print(f"\n  [SUMMARY] Episode {ep+1}:")
    print(f"    Slip L: {'step ' + str(slip_step_l) + ' (z+' + str(ep_result['slip_z_mm_l']) + 'mm)' if slip_step_l else 'NONE'}")
    print(f"    Slip R: {'step ' + str(slip_step_r) + ' (z+' + str(ep_result['slip_z_mm_r']) + 'mm)' if slip_step_r else 'NONE'}")
    print(f"    Zero contact L: {zero_contact_steps_l}/{len(time_series)} steps")
    print(f"    Zero contact R: {zero_contact_steps_r}/{len(time_series)} steps")
    print(f"    Time: {elapsed:.1f}s")

    # Save per-episode time series
    ts_path = os.path.join(args.output_dir, f"timeseries_ep{ep}.json")
    with open(ts_path, "w") as f:
        json.dump(time_series, f, indent=1)

    all_results.append(ep_result)

# ---- Save summary ----
summary = {
    "lift_mm": args.lift_mm,
    "n_episodes": args.num_episodes,
    "finger_pd_target_mm": KIN_GRIP_TARGET * 1000,
    "episodes": all_results,
}
summary_path = os.path.join(args.output_dir, "DIAG_SUMMARY.json")
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print(f"DIAGNOSTIC COMPLETE: {args.num_episodes} episodes")
print(f"Results: {summary_path}")
print(f"{'='*60}")

# Shutdown
sim_app.close()
