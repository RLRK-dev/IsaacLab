#!/usr/bin/env python3
"""
Multi-Cycle Hook Hanging Test (Phase 1 -> 6 -> 7 -> 8 -> repeat)

Tests multiple cycles of the complete cable-on-hook workflow:
- Phase 1: Approach (hover above cable)
- Phase 2: Grasp (close grippers on cable)
- Phase 3: Lift
- Phase 4-5.5: Hook placement
- Phase 6: Release and retreat
- Phase 7: Return to home position
- Phase 8: Cycle reset (reset cable to initial position)

For RL/World Model training.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_cycles", type=int, default=3, help="Number of cycles to run")
parser.add_argument("--save_images", action="store_true", help="Save images at each phase")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    # Phase 1-2 joint angles
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    # Phase 7 (same as Phase 1)
    PHASE7_LEFT_JOINTS, PHASE7_RIGHT_JOINTS,
    # Waypoints
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    WAYPOINT_PHASE7_LEFT, WAYPOINT_PHASE7_RIGHT,
    # Gripper
    GRIPPER_CLOSE, GRIPPER_OPEN,
    # Release sequence
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS, PHASE55_TO_6_STEPS,
    # Cycle reset
    CYCLE_RESET_STABILIZATION_STEPS,
    # Cable initial position
    CABLE_X, CABLE_Z,
    # Hook
    HOOK_X, HOOK_Y, HOOK_Z,
    TABLE_HEIGHT,
)

# Output directory
OUTPUT_DIR = "/tmp/multi_cycle_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# High friction
HIGH_FRICTION = 5.0

# Phase step counts
PHASE1_STEPS = 100
PHASE12_STEPS = 300
GRASP_STEPS = 300
GRASP_STABILIZE = 100
LIFT_STEPS = 200
PHASE34_STEPS = 400
PHASE445_STEPS = 300
PHASE455_STEPS = 300
PHASE55_STEPS = 200
POST_RETREAT_STEPS = 200
PHASE67_STEPS = 400

Z_OFFSET = 0.1034
LIFT_CM = 5.0
HOOK_V_Z = 0.83

print("=" * 70)
print("MULTI-CYCLE HOOK HANGING TEST")
print(f"Number of cycles: {args.num_cycles}")
print(f"Output dir: {OUTPUT_DIR}")
print("=" * 70)

# Setup simulation
sim_cfg = sim_utils.SimulationCfg(dt=1/240, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)

@configclass
class TestSceneCfg(DualArmSceneCfg):
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.0, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"], debug_vis=False,
    )

scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)

sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
cable = scene["cable"]
contact_left = scene["contact_left"]
contact_right = scene["contact_right"]

# Cameras
front_left_cam = scene["front_left_camera"]
front_right_cam = scene["front_right_camera"]
back_cam = scene["back_camera"]
overhead_cam = scene["overhead_camera"]

device = robot_left.device

# Store initial cable state for reset
initial_cable_root_state = cable.data.root_state_w.clone()
initial_cable_body_state = cable.data.body_state_w.clone()

print(f"\nInitial cable state saved")
print(f"  Root state shape: {initial_cable_root_state.shape}")
print(f"  Body state shape: {initial_cable_body_state.shape}")

# Apply friction
def set_friction(asset, sf, df):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = sf
    materials[..., 1] = df
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)

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

def get_ee_pos(robot, idx):
    return robot.data.body_pos_w[0, idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def set_robot_joints(robot, arm_joints, gripper_val):
    target = robot.data.joint_pos[0].unsqueeze(0).clone()
    target[0, :7] = torch.tensor(arm_joints, device=device)
    target[0, -2:] = gripper_val
    robot.set_joint_position_target(target)
    robot.write_data_to_sim()

def teleport_robot(robot, arm_joints, gripper_val):
    state = robot.data.joint_pos[0].unsqueeze(0).clone()
    state[0, :7] = torch.tensor(arm_joints, device=device)
    state[0, -2:] = gripper_val
    robot.write_joint_state_to_sim(state, robot.data.joint_vel[0].unsqueeze(0))

def save_camera_images(phase_name, cycle_idx):
    if not args.save_images:
        return

    front_left_cam.update(sim.get_physics_dt())
    front_right_cam.update(sim.get_physics_dt())
    back_cam.update(sim.get_physics_dt())
    overhead_cam.update(sim.get_physics_dt())

    cycle_dir = os.path.join(OUTPUT_DIR, f"cycle_{cycle_idx:02d}")
    os.makedirs(cycle_dir, exist_ok=True)

    cameras = [("front_left", front_left_cam), ("front_right", front_right_cam),
               ("back", back_cam), ("overhead", overhead_cam)]

    for cam_name, cam in cameras:
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        img = Image.fromarray(rgb.astype(np.uint8))
        img.save(os.path.join(cycle_dir, f"{phase_name}_{cam_name}.png"))

def run_diff_ik_motion(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                       target_pos_left, target_pos_right, num_steps, gripper_val):
    diff_ik_left.reset()
    diff_ik_right.reset()

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        pos_left = start_pos_left + alpha * (target_pos_left - start_pos_left)
        pos_right = start_pos_right + alpha * (target_pos_right - start_pos_right)

        cmd_left = torch.cat([pos_left, start_quat_left], dim=1)
        cmd_right = torch.cat([pos_right, start_quat_right], dim=1)

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
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())

def reset_cable_to_initial():
    """Reset cable to initial position using stored state."""
    # Reset all body states
    cable.write_root_state_to_sim(initial_cable_root_state)

    # Stabilize
    for _ in range(CYCLE_RESET_STABILIZATION_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

def run_cycle(cycle_idx):
    """Run one complete cycle (Phase 1-8)."""
    print(f"\n{'='*70}")
    print(f"CYCLE {cycle_idx + 1}/{args.num_cycles}")
    print("=" * 70)

    cycle_result = {"cycle": cycle_idx + 1, "success": False}

    # ============================================================
    # PHASE 1: APPROACH
    # ============================================================
    print("\n[Phase 1] Approach...")
    teleport_robot(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    teleport_robot(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)

    for _ in range(PHASE1_STEPS):
        set_robot_joints(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    p1_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p1_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p1_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p1_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
    save_camera_images("phase1_approach", cycle_idx)

    # ============================================================
    # PHASE 2: GRASP
    # ============================================================
    print("\n[Phase 2] Grasp...")
    for step in range(PHASE12_STEPS):
        alpha = (step + 1) / PHASE12_STEPS
        left_joints = [l + alpha * (p - l) for l, p in zip(LEFT_ARM_INIT_JOINTS, PHASE2_LEFT_JOINTS)]
        right_joints = [l + alpha * (p - l) for l, p in zip(RIGHT_ARM_INIT_JOINTS, PHASE2_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    for _ in range(GRASP_STEPS):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    for _ in range(GRASP_STABILIZE):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    p2_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p2_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p2_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p2_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    f_l = get_contact_force(contact_left)
    f_r = get_contact_force(contact_right)
    cycle_result["phase2_force"] = (f_l, f_r)
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase2_grasp", cycle_idx)

    # ============================================================
    # PHASE 3: LIFT
    # ============================================================
    print(f"\n[Phase 3] Lift ({LIFT_CM}cm)...")
    p3_target_l = p2_pos_l.clone()
    p3_target_l[0, 2] += LIFT_CM / 100.0
    p3_target_r = p2_pos_r.clone()
    p3_target_r[0, 2] += LIFT_CM / 100.0

    p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r = run_diff_ik_motion(
        p2_pos_l, p2_pos_r, p2_quat_l, p2_quat_r,
        p3_target_l, p3_target_r, LIFT_STEPS, GRIPPER_CLOSE
    )

    f_l = get_contact_force(contact_left)
    f_r = get_contact_force(contact_right)
    cycle_result["phase3_force"] = (f_l, f_r)
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase3_lift", cycle_idx)

    # ============================================================
    # PHASE 4: HOOK APPROACH
    # ============================================================
    print("\n[Phase 4] Hook approach...")
    p4_target_l = torch.tensor([[WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1],
                                  WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p4_target_r = torch.tensor([[WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1],
                                  WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r = run_diff_ik_motion(
        p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r,
        p4_target_l, p4_target_r, PHASE34_STEPS, GRIPPER_CLOSE
    )
    save_camera_images("phase4_approach", cycle_idx)

    # ============================================================
    # PHASE 4.5: INTERMEDIATE
    # ============================================================
    print("\n[Phase 4.5] Intermediate...")
    p45_target_l = torch.tensor([[WAYPOINT_PHASE45_LEFT[0], WAYPOINT_PHASE45_LEFT[1],
                                   WAYPOINT_PHASE45_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p45_target_r = torch.tensor([[WAYPOINT_PHASE45_RIGHT[0], WAYPOINT_PHASE45_RIGHT[1],
                                   WAYPOINT_PHASE45_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r = run_diff_ik_motion(
        p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r,
        p45_target_l, p45_target_r, PHASE445_STEPS, GRIPPER_CLOSE
    )

    # ============================================================
    # PHASE 5: ABOVE HOOK
    # ============================================================
    print("\n[Phase 5] Above hook...")
    p5_target_l = torch.tensor([[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1],
                                  WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p5_target_r = torch.tensor([[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1],
                                  WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r = run_diff_ik_motion(
        p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r,
        p5_target_l, p5_target_r, PHASE455_STEPS, GRIPPER_CLOSE
    )
    save_camera_images("phase5_above", cycle_idx)

    # ============================================================
    # PHASE 5.5: LOWER ONTO HOOK
    # ============================================================
    print("\n[Phase 5.5] Lower onto hook...")
    p55_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1],
                                   WAYPOINT_PHASE55_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p55_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], WAYPOINT_PHASE55_RIGHT[1],
                                   WAYPOINT_PHASE55_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p55_pos_l, p55_pos_r, p55_quat_l, p55_quat_r = run_diff_ik_motion(
        p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r,
        p55_target_l, p55_target_r, PHASE55_STEPS, GRIPPER_CLOSE
    )
    save_camera_images("phase55_hook", cycle_idx)

    # ============================================================
    # PHASE 6: RELEASE AND RETREAT
    # ============================================================
    print("\n[Phase 6] Release and retreat...")

    # Stabilize
    for _ in range(RELEASE_STABILIZE_STEPS):
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, -2:] = GRIPPER_CLOSE
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, -2:] = GRIPPER_CLOSE
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Release
    for i in range(RELEASE_GRIPPER_STEPS):
        alpha = (i + 1) / RELEASE_GRIPPER_STEPS
        gripper_val = GRIPPER_CLOSE + alpha * (GRIPPER_OPEN - GRIPPER_CLOSE)
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()
        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    save_camera_images("phase6_release", cycle_idx)

    # Retreat
    p6_current_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p6_current_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p6_target_l = torch.tensor([[WAYPOINT_PHASE6_LEFT[0], WAYPOINT_PHASE6_LEFT[1],
                                  WAYPOINT_PHASE6_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p6_target_r = torch.tensor([[WAYPOINT_PHASE6_RIGHT[0], WAYPOINT_PHASE6_RIGHT[1],
                                  WAYPOINT_PHASE6_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p6_pos_l, p6_pos_r, p6_quat_l, p6_quat_r = run_diff_ik_motion(
        p6_current_l, p6_current_r, p55_quat_l, p55_quat_r,
        p6_target_l, p6_target_r, PHASE55_TO_6_STEPS, GRIPPER_OPEN
    )

    for _ in range(POST_RETREAT_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    save_camera_images("phase6_retreat", cycle_idx)

    # ============================================================
    # PHASE 7: HOME RETURN
    # ============================================================
    print("\n[Phase 7] Home return...")
    p7_target_l = torch.tensor([[WAYPOINT_PHASE7_LEFT[0], WAYPOINT_PHASE7_LEFT[1],
                                  WAYPOINT_PHASE7_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p7_target_r = torch.tensor([[WAYPOINT_PHASE7_RIGHT[0], WAYPOINT_PHASE7_RIGHT[1],
                                  WAYPOINT_PHASE7_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    _, _, _, _ = run_diff_ik_motion(
        p6_pos_l, p6_pos_r, p6_quat_l, p6_quat_r,
        p7_target_l, p7_target_r, PHASE67_STEPS, GRIPPER_OPEN
    )

    # Stabilize at home
    for _ in range(100):
        set_robot_joints(robot_left, PHASE7_LEFT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, PHASE7_RIGHT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    save_camera_images("phase7_home", cycle_idx)
    print("  Home position reached")

    # ============================================================
    # PHASE 8: CYCLE RESET
    # ============================================================
    print("\n[Phase 8] Cycle reset...")
    reset_cable_to_initial()
    save_camera_images("phase8_reset", cycle_idx)
    print("  Cable reset complete")

    cycle_result["success"] = True
    return cycle_result

# ============================================================
# MAIN LOOP
# ============================================================
all_results = []

for cycle_idx in range(args.num_cycles):
    result = run_cycle(cycle_idx)
    all_results.append(result)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("MULTI-CYCLE SUMMARY")
print("=" * 70)

success_count = sum(1 for r in all_results if r["success"])
print(f"\nCycles completed: {len(all_results)}/{args.num_cycles}")
print(f"Success rate: {success_count}/{args.num_cycles} ({success_count/args.num_cycles*100:.0f}%)")

print("\nPer-cycle results:")
for r in all_results:
    status = "OK" if r["success"] else "FAIL"
    f2 = r.get("phase2_force", (0, 0))
    f3 = r.get("phase3_force", (0, 0))
    print(f"  Cycle {r['cycle']}: [{status}] P2: L={f2[0]:.1f}N R={f2[1]:.1f}N | P3: L={f3[0]:.1f}N R={f3[1]:.1f}N")

if args.save_images:
    print(f"\nImages saved to: {OUTPUT_DIR}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

simulation_app.close()
