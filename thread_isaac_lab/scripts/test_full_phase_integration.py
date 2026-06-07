#!/usr/bin/env python3
"""
Full Phase Integration Test (Phase 1 -> 6)

Tests the complete cable-on-hook workflow:
- Phase 1: Approach (hover above cable)
- Phase 2: Grasp (close grippers on cable)
- Phase 3: Lift (lift cable)
- Phase 4: Hook approach
- Phase 4.5: Intermediate
- Phase 5: Cable above hook
- Phase 5.5: Lower onto hook V-valley
- Phase 6: Release and retreat

Run multiple times to verify reproducibility.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_runs", type=int, default=1, help="Number of test runs")
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
    # Waypoints
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    # Gripper
    GRIPPER_CLOSE, GRIPPER_OPEN,
    # Release sequence
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS, PHASE55_TO_6_STEPS,
    # Hook
    HOOK_X, HOOK_Y, HOOK_Z,
    TABLE_HEIGHT,
    # Lift
    LIFT_HEIGHT,
)

# Output directory
OUTPUT_DIR = "/tmp/full_phase_integration"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# High friction settings (from successful tests)
HIGH_FRICTION = 5.0

# Phase step counts
PHASE1_STEPS = 100     # Stabilize at Phase 1
PHASE12_STEPS = 300    # Phase 1->2 descent
GRASP_STEPS = 300      # Gripper close
GRASP_STABILIZE = 100  # After grasp stabilize
LIFT_STEPS = 200       # Phase 2->3 lift
PHASE34_STEPS = 400    # Phase 3->4
PHASE445_STEPS = 300   # Phase 4->4.5
PHASE455_STEPS = 300   # Phase 4.5->5
PHASE55_STEPS = 200    # Phase 5->5.5
POST_RETREAT_STEPS = 200  # Stabilize after retreat

Z_OFFSET = 0.1034      # IK vs Isaac Lab kinematics offset
LIFT_CM = LIFT_HEIGHT * 100  # Lift target from task_config (cm)

# Hook position
HOOK_V_Z = 0.83  # V-valley Z position

print("=" * 70)
print("FULL PHASE INTEGRATION TEST (Phase 1 -> 6)")
print(f"Number of runs: {args.num_runs}")
print(f"Save images: {args.save_images}")
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

# Get cameras
front_left_cam = scene["front_left_camera"]
front_right_cam = scene["front_right_camera"]
back_cam = scene["back_camera"]
overhead_cam = scene["overhead_camera"]

device = robot_left.device

# Apply HIGH FRICTION
print(f"\nApplying FRICTION={HIGH_FRICTION}...")
def set_friction(asset, sf, df):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = sf
    materials[..., 1] = df
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)

# Setup Diff IK
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

def get_cable_center():
    """Get cable center position (average of all segments)."""
    pos = cable.data.body_pos_w[0].cpu().numpy()
    valid = pos[~np.isnan(pos).any(axis=1)]
    if len(valid) > 0:
        return np.mean(valid, axis=0)
    return np.array([np.nan, np.nan, np.nan])

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

def save_camera_images(phase_name, run_idx):
    """Save images from all 4 cameras."""
    if not args.save_images:
        return

    front_left_cam.update(sim.get_physics_dt())
    front_right_cam.update(sim.get_physics_dt())
    back_cam.update(sim.get_physics_dt())
    overhead_cam.update(sim.get_physics_dt())

    cameras = [
        ("front_left", front_left_cam),
        ("front_right", front_right_cam),
        ("back", back_cam),
        ("overhead", overhead_cam),
    ]

    run_dir = os.path.join(OUTPUT_DIR, f"run_{run_idx:02d}")
    os.makedirs(run_dir, exist_ok=True)

    for cam_name, cam in cameras:
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        img = Image.fromarray(rgb.astype(np.uint8))
        filepath = os.path.join(run_dir, f"{phase_name}_{cam_name}.png")
        img.save(filepath)

def run_diff_ik_motion(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                       target_pos_left, target_pos_right, num_steps, gripper_val):
    """Run Diff IK interpolated motion."""
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

def reset_scene():
    """Reset scene for next run."""
    scene.reset()
    # Re-apply friction
    set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
    set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
    set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)
    # Stabilize
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

def run_single_test(run_idx):
    """Run a single full phase test."""
    print(f"\n{'='*70}")
    print(f"RUN {run_idx + 1}/{args.num_runs}")
    print("=" * 70)

    results = {
        "run": run_idx + 1,
        "phase2_force_l": 0, "phase2_force_r": 0,
        "phase3_force_l": 0, "phase3_force_r": 0,
        "final_cable_pos": None,
        "cable_on_hook": False,
        "success": False,
    }

    # ============================================================
    # PHASE 1: APPROACH (Teleport to hover position)
    # ============================================================
    print("\n[Phase 1] Approach - Teleporting to hover position...")
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

    ee_l = get_ee_pos(robot_left, jacobian_body_left)
    ee_r = get_ee_pos(robot_right, jacobian_body_right)
    print(f"  EE L: ({ee_l[0]:.3f}, {ee_l[1]:.3f}, {ee_l[2]:.3f})")
    print(f"  EE R: ({ee_r[0]:.3f}, {ee_r[1]:.3f}, {ee_r[2]:.3f})")
    save_camera_images("phase1_approach", run_idx)

    # ============================================================
    # PHASE 2: GRASP (Descend and close grippers)
    # ============================================================
    print("\n[Phase 2] Grasp - Descending to cable...")

    # Descend using joint angles
    for _ in range(PHASE12_STEPS):
        alpha = (_ + 1) / PHASE12_STEPS
        # Interpolate joints
        left_joints = [l + alpha * (p - l) for l, p in zip(LEFT_ARM_INIT_JOINTS, PHASE2_LEFT_JOINTS)]
        right_joints = [l + alpha * (p - l) for l, p in zip(RIGHT_ARM_INIT_JOINTS, PHASE2_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())

    # Close grippers
    print("  Closing grippers...")
    for _ in range(GRASP_STEPS):
        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())

    # Stabilize
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
    results["phase2_force_l"] = f_l
    results["phase2_force_r"] = f_r
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase2_grasp", run_idx)

    # ============================================================
    # PHASE 3: LIFT
    # ============================================================
    print(f"\n[Phase 3] Lift - Lifting {LIFT_CM}cm...")

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
    results["phase3_force_l"] = f_l
    results["phase3_force_r"] = f_r
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase3_lift", run_idx)

    # ============================================================
    # PHASE 4: HOOK APPROACH
    # ============================================================
    print("\n[Phase 4] Hook Approach...")

    p4_target_l = torch.tensor([[WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1],
                                  WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p4_target_r = torch.tensor([[WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1],
                                  WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r = run_diff_ik_motion(
        p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r,
        p4_target_l, p4_target_r, PHASE34_STEPS, GRIPPER_CLOSE
    )

    f_l = get_contact_force(contact_left)
    f_r = get_contact_force(contact_right)
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase4_approach", run_idx)

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

    f_l = get_contact_force(contact_left)
    f_r = get_contact_force(contact_right)
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase45_intermediate", run_idx)

    # ============================================================
    # PHASE 5: ABOVE HOOK
    # ============================================================
    print("\n[Phase 5] Cable Above Hook...")

    p5_target_l = torch.tensor([[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1],
                                  WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p5_target_r = torch.tensor([[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1],
                                  WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r = run_diff_ik_motion(
        p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r,
        p5_target_l, p5_target_r, PHASE455_STEPS, GRIPPER_CLOSE
    )

    f_l = get_contact_force(contact_left)
    f_r = get_contact_force(contact_right)
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase5_above_hook", run_idx)

    # ============================================================
    # PHASE 5.5: LOWER ONTO HOOK
    # ============================================================
    print("\n[Phase 5.5] Lower Onto Hook V-valley...")

    p55_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1],
                                   WAYPOINT_PHASE55_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p55_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], WAYPOINT_PHASE55_RIGHT[1],
                                   WAYPOINT_PHASE55_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    p55_pos_l, p55_pos_r, p55_quat_l, p55_quat_r = run_diff_ik_motion(
        p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r,
        p55_target_l, p55_target_r, PHASE55_STEPS, GRIPPER_CLOSE
    )

    f_l = get_contact_force(contact_left)
    f_r = get_contact_force(contact_right)
    print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
    save_camera_images("phase55_on_hook", run_idx)

    # ============================================================
    # PHASE 6: STABILIZE, RELEASE AND RETREAT
    # ============================================================
    print("\n[Phase 6] Stabilize, Release and Retreat...")

    # Step 1: Stabilize
    print(f"  Stabilizing for {RELEASE_STABILIZE_STEPS} steps...")
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

    save_camera_images("phase55_stabilized", run_idx)

    # Step 2: Gradual gripper release
    print(f"  Releasing grippers over {RELEASE_GRIPPER_STEPS} steps...")
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

    save_camera_images("phase6_release", run_idx)

    # Step 3: Retreat
    print("  Retreating...")
    p55_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p55_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    p6_target_l = torch.tensor([[WAYPOINT_PHASE6_LEFT[0], WAYPOINT_PHASE6_LEFT[1],
                                  WAYPOINT_PHASE6_LEFT[2] + Z_OFFSET]], device=device, dtype=torch.float32)
    p6_target_r = torch.tensor([[WAYPOINT_PHASE6_RIGHT[0], WAYPOINT_PHASE6_RIGHT[1],
                                  WAYPOINT_PHASE6_RIGHT[2] + Z_OFFSET]], device=device, dtype=torch.float32)

    _, _, _, _ = run_diff_ik_motion(
        p55_pos_l, p55_pos_r, p55_quat_l, p55_quat_r,
        p6_target_l, p6_target_r, PHASE55_TO_6_STEPS, GRIPPER_OPEN
    )

    # Stabilize after retreat
    for _ in range(POST_RETREAT_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())

    save_camera_images("phase6_retreat", run_idx)

    # ============================================================
    # FINAL RESULTS
    # ============================================================
    final_cable = get_cable_center()
    results["final_cable_pos"] = final_cable

    # Check if cable is on hook
    if not np.isnan(final_cable).any():
        cable_to_hook_xy = np.sqrt((final_cable[0] - HOOK_X)**2 + (final_cable[1] - HOOK_Y)**2)
        cable_above_table = final_cable[2] - TABLE_HEIGHT
        cable_near_hook_z = abs(final_cable[2] - HOOK_V_Z) < 0.10

        xy_aligned = cable_to_hook_xy < 0.10
        z_on_hook = cable_above_table > 0.05 and cable_near_hook_z

        results["cable_on_hook"] = xy_aligned and z_on_hook
        results["success"] = xy_aligned and z_on_hook

        print(f"\n  Cable: ({final_cable[0]:.3f}, {final_cable[1]:.3f}, {final_cable[2]:.3f})")
        print(f"  Cable-Hook XY: {cable_to_hook_xy*100:.1f}cm")
        print(f"  Cable Z above table: {cable_above_table*100:.1f}cm")
    else:
        print("\n  Cable position: NaN (tracking lost)")

    status = "SUCCESS" if results["success"] else "PARTIAL"
    print(f"\n  Result: {status}")

    return results

# ============================================================
# MAIN TEST LOOP
# ============================================================
all_results = []

for run_idx in range(args.num_runs):
    if run_idx > 0:
        reset_scene()

    results = run_single_test(run_idx)
    all_results.append(results)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

success_count = sum(1 for r in all_results if r["success"])
print(f"\nTotal runs: {args.num_runs}")
print(f"Successful: {success_count}")
print(f"Success rate: {success_count/args.num_runs*100:.1f}%")

print("\nPer-run results:")
print("-" * 50)
for r in all_results:
    status = "OK" if r["success"] else "FAIL"
    f2 = f"L={r['phase2_force_l']:.1f}N, R={r['phase2_force_r']:.1f}N"
    f3 = f"L={r['phase3_force_l']:.1f}N, R={r['phase3_force_r']:.1f}N"
    print(f"Run {r['run']}: [{status}] P2 Force: {f2}, P3 Force: {f3}")

if args.save_images:
    print(f"\nImages saved to: {OUTPUT_DIR}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

simulation_app.close()
