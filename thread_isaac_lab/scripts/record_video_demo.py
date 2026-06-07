#!/usr/bin/env python3
"""
Record Phase 1-8 Robot Demo Video with 4-Camera 2x2 Grid

Records the complete cable-on-hook workflow with 4 synchronized camera views:
- Phase 1: Approach (hover above cable)
- Phase 2: Grasp (close grippers on cable)
- Phase 3: Lift
- Phase 4-5.5: Hook placement
- Phase 6: Release and retreat
- Phase 7: Return to home position
- Phase 8: Cycle reset

Output: 2x2 grid video (front_left, front_right, back, overhead)
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
import argparse
import subprocess
import shutil
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=str, default="data/videos/phase_1_8_demo.mp4",
                    help="Output video path")
parser.add_argument("--fps", type=int, default=30, help="Video frame rate")
parser.add_argument("--num_cycles", type=int, default=1, help="Number of cycles to record")
parser.add_argument("--resolution", type=int, default=512, help="Per-camera resolution (grid will be 2x)")
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
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE7_LEFT_JOINTS, PHASE7_RIGHT_JOINTS,
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    WAYPOINT_PHASE7_LEFT, WAYPOINT_PHASE7_RIGHT,
    GRIPPER_CLOSE, GRIPPER_OPEN,
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS, PHASE55_TO_6_STEPS,
    CYCLE_RESET_STABILIZATION_STEPS,
)

# Frame output directory
FRAME_DIR = "/tmp/video_frames"
os.makedirs(FRAME_DIR, exist_ok=True)

# Clear old frames
for f in os.listdir(FRAME_DIR):
    os.remove(os.path.join(FRAME_DIR, f))

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

# Frame counter
frame_count = 0

print("=" * 70)
print("PHASE 1-8 VIDEO RECORDING")
print(f"Output: {args.output}")
print(f"FPS: {args.fps}")
print(f"Cycles: {args.num_cycles}")
print(f"Resolution: {args.resolution}x{args.resolution} per camera")
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

# Apply friction
def set_friction(asset, sf, df):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = sf
    materials[..., 1] = df
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

print(f"\nApplying FRICTION={HIGH_FRICTION}...")
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

def capture_grid_frame():
    """Capture 4 cameras and create 2x2 grid image."""
    global frame_count

    # Update cameras
    front_left_cam.update(sim.get_physics_dt())
    front_right_cam.update(sim.get_physics_dt())
    back_cam.update(sim.get_physics_dt())
    overhead_cam.update(sim.get_physics_dt())

    # Get RGB images
    imgs = {}
    for name, cam in [("front_left", front_left_cam), ("front_right", front_right_cam),
                      ("back", back_cam), ("overhead", overhead_cam)]:
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        imgs[name] = Image.fromarray(rgb.astype(np.uint8))

    # Resize to target resolution
    res = args.resolution
    for name in imgs:
        imgs[name] = imgs[name].resize((res, res), Image.LANCZOS)

    # Create 2x2 grid
    # Layout:
    # front_left  | front_right
    # back        | overhead
    grid = Image.new('RGB', (res * 2, res * 2))
    grid.paste(imgs["front_left"], (0, 0))
    grid.paste(imgs["front_right"], (res, 0))
    grid.paste(imgs["back"], (0, res))
    grid.paste(imgs["overhead"], (res, res))

    # Save frame
    grid.save(os.path.join(FRAME_DIR, f"frame_{frame_count:06d}.png"))
    frame_count += 1

def run_diff_ik_motion(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                       target_pos_left, target_pos_right, num_steps, gripper_val,
                       capture_every=20):
    """Run Diff IK motion and capture frames."""
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

        # Capture frame every N steps (at 240Hz sim, capture_every=20 gives 12fps)
        if i % capture_every == 0:
            capture_grid_frame()

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())

def reset_cable_to_initial():
    """Reset cable to initial position."""
    cable.write_root_state_to_sim(initial_cable_root_state)
    for i in range(CYCLE_RESET_STABILIZATION_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % 20 == 0:
            capture_grid_frame()

def run_cycle(cycle_idx):
    """Run one complete cycle (Phase 1-8) with video capture."""
    print(f"\n{'='*70}")
    print(f"CYCLE {cycle_idx + 1}/{args.num_cycles}")
    print("=" * 70)

    # ============================================================
    # CABLE STABILIZATION (before Phase 1)
    # ============================================================
    print("\n[Stabilization] Resetting cable position...")
    cable.write_root_state_to_sim(initial_cable_root_state)
    for _ in range(CYCLE_RESET_STABILIZATION_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    # ============================================================
    # PHASE 1: APPROACH
    # ============================================================
    print("\n[Phase 1] Approach...")
    teleport_robot(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
    teleport_robot(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)

    for i in range(PHASE1_STEPS):
        set_robot_joints(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % 20 == 0:
            capture_grid_frame()

    p1_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p1_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p1_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p1_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # ============================================================
    # PHASE 2: GRASP (Using Diff IK to maintain Y position)
    # ============================================================
    print("\n[Phase 2] Grasp...")

    # Phase 2 approach: Use Diff IK for Cartesian-space straight line motion
    # This prevents Y-direction drift that occurs with joint-space interpolation
    p2_target_l = torch.tensor([[WAYPOINT_PHASE2_LEFT[0], WAYPOINT_PHASE2_LEFT[1],
                                  WAYPOINT_PHASE2_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p2_target_r = torch.tensor([[WAYPOINT_PHASE2_RIGHT[0], WAYPOINT_PHASE2_RIGHT[1],
                                  WAYPOINT_PHASE2_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p2_pos_l, p2_pos_r, p2_quat_l, p2_quat_r = run_diff_ik_motion(
        p1_pos_l, p1_pos_r, p1_quat_l, p1_quat_r,
        p2_target_l, p2_target_r, PHASE12_STEPS, GRIPPER_OPEN
    )

    # Grasp: Close grippers while maintaining position
    for i in range(GRASP_STEPS):
        # Use Diff IK to hold position while closing grippers
        cmd_left = torch.cat([p2_pos_l, p2_quat_l], dim=1)
        cmd_right = torch.cat([p2_pos_r, p2_quat_r], dim=1)

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
        tgt_l[0, -2:] = GRIPPER_CLOSE
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r[0]
        tgt_r[0, -2:] = GRIPPER_CLOSE
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())
        if i % 20 == 0:
            capture_grid_frame()

    # Stabilize: Hold position with grippers closed
    for i in range(GRASP_STABILIZE):
        cmd_left = torch.cat([p2_pos_l, p2_quat_l], dim=1)
        cmd_right = torch.cat([p2_pos_r, p2_quat_r], dim=1)

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
        tgt_l[0, -2:] = GRIPPER_CLOSE
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r[0]
        tgt_r[0, -2:] = GRIPPER_CLOSE
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())
        if i % 20 == 0:
            capture_grid_frame()

    # Update p2 positions after grasp stabilization
    p2_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p2_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p2_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p2_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

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

    # ============================================================
    # PHASE 6: RELEASE AND RETREAT
    # ============================================================
    print("\n[Phase 6] Release and retreat...")

    # Stabilize
    for i in range(RELEASE_STABILIZE_STEPS):
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
        if i % 20 == 0:
            capture_grid_frame()

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
        if i % 20 == 0:
            capture_grid_frame()

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

    for i in range(POST_RETREAT_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % 20 == 0:
            capture_grid_frame()

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
    for i in range(100):
        set_robot_joints(robot_left, PHASE7_LEFT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, PHASE7_RIGHT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % 20 == 0:
            capture_grid_frame()

    print("  Home position reached")

    # ============================================================
    # PHASE 8: CYCLE RESET
    # ============================================================
    print("\n[Phase 8] Cycle reset...")
    reset_cable_to_initial()
    print("  Cable reset complete")

# ============================================================
# MAIN LOOP
# ============================================================
for cycle_idx in range(args.num_cycles):
    run_cycle(cycle_idx)

# ============================================================
# CONVERT TO VIDEO
# ============================================================
print("\n" + "=" * 70)
print("CONVERTING TO VIDEO")
print("=" * 70)

print(f"Total frames captured: {frame_count}")

# Create output directory
output_dir = os.path.dirname(args.output)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

# Run ffmpeg
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-framerate", str(args.fps),
    "-i", os.path.join(FRAME_DIR, "frame_%06d.png"),
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    args.output
]

print(f"Running: {' '.join(ffmpeg_cmd)}")
result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

if result.returncode == 0:
    print(f"\nVideo saved: {args.output}")
    # Get file size
    if os.path.exists(args.output):
        size_mb = os.path.getsize(args.output) / (1024 * 1024)
        print(f"File size: {size_mb:.1f} MB")
else:
    print(f"FFmpeg error: {result.stderr}")

# Cleanup frames
print("\nCleaning up temporary frames...")
shutil.rmtree(FRAME_DIR)

print("\n" + "=" * 70)
print("RECORDING COMPLETE")
print("=" * 70)

simulation_app.close()
