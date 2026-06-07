#!/usr/bin/env python3
"""
Phase 5-6 Hook Placement Test

Tests the updated waypoints for proper hook placement:
- Phase 5: Cable above hook (X=0.25, Y centered at 0, Z=0.90)
- Phase 5.5: Lower onto hook V-valley (Z=0.85)
- Phase 6: Release and retreat

Captures images at each phase for verification.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import os
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
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
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    GRIPPER_CLOSE, GRIPPER_OPEN,
    TABLE_HEIGHT,
)

# Output directory
OUTPUT_DIR = "/tmp/phase5_6_hook_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("PHASE 5-6 HOOK PLACEMENT TEST")
print(f"Images saved to: {OUTPUT_DIR}")
print("=" * 70)

# High friction settings (from successful 13.6cm lift)
HIGH_FRICTION = 5.0

# Phase step counts
LIFT_STEPS = 200       # Phase 2->3
PHASE34_STEPS = 400    # Phase 3->4
PHASE45_STEPS = 400    # Phase 4->5
PHASE55_STEPS = 200    # Phase 5->5.5 (lower)
STABILIZE_STEPS = 100  # Stabilize before release (Option B)
RELEASE_STEPS = 150    # Gripper release (gradual)
PHASE56_STEPS = 200    # Phase 5.5->6 (retreat)

Z_OFFSET = 0.1034      # IK vs Isaac Lab kinematics offset
LIFT_CM = 5.0          # Lift target

# Hook position for reference
HOOK_X = 0.25
HOOK_Y = 0.0
HOOK_V_Z = 0.83  # V-valley Z position (stem top)
HOOK_TARGET_Z = 0.82  # Target Z for cable placement (1cm below V-valley)

print(f"\nConfiguration:")
print(f"  FRICTION: {HIGH_FRICTION}")
print(f"  Hook center: ({HOOK_X}, {HOOK_Y}, {HOOK_V_Z})")
print(f"  Phase 5:   {WAYPOINT_PHASE5_LEFT} / {WAYPOINT_PHASE5_RIGHT}")
print(f"  Phase 5.5: {WAYPOINT_PHASE55_LEFT} / {WAYPOINT_PHASE55_RIGHT}")
print(f"  Phase 6:   {WAYPOINT_PHASE6_LEFT} / {WAYPOINT_PHASE6_RIGHT}")
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

def save_camera_images(phase_name):
    """Save images from all 4 cameras."""
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

    for cam_name, cam in cameras:
        rgb = cam.data.output["rgb"][0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        img = Image.fromarray(rgb.astype(np.uint8))
        filepath = os.path.join(OUTPUT_DIR, f"{phase_name}_{cam_name}.png")
        img.save(filepath)
    print(f"  Saved {phase_name} images")

def run_diff_ik_motion(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                       target_pos_left, target_pos_right, num_steps, gripper_val):
    """Run Diff IK interpolated motion."""
    diff_ik_left.reset()
    diff_ik_right.reset()

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Interpolate position
        pos_left = start_pos_left + alpha * (target_pos_left - start_pos_left)
        pos_right = start_pos_right + alpha * (target_pos_right - start_pos_right)

        # Commands
        cmd_left = torch.cat([pos_left, start_quat_left], dim=1)
        cmd_right = torch.cat([pos_right, start_quat_right], dim=1)

        diff_ik_left.set_command(cmd_left)
        diff_ik_right.set_command(cmd_right)

        # Compute IK
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

        # Apply
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

    # Return final state
    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())

# ============================================================
# PHASE 2: GRASP
# ============================================================
print("\n" + "=" * 70)
print("PHASE 2: GRASP")
print("=" * 70)

teleport_robot(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
teleport_robot(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)

for _ in range(50):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_OPEN)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_OPEN)
    sim.step()
    scene.update(sim.get_physics_dt())

# Close grippers
for _ in range(300):
    set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, GRIPPER_CLOSE)
    set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, GRIPPER_CLOSE)
    sim.step()
    scene.update(sim.get_physics_dt())

# Stabilize
for _ in range(100):
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
print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
save_camera_images("phase2_grasp")

# ============================================================
# PHASE 3: LIFT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 3: LIFT")
print("=" * 70)

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
print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
save_camera_images("phase3_lift")

# ============================================================
# PHASE 4: HOOK APPROACH
# ============================================================
print("\n" + "=" * 70)
print("PHASE 4: HOOK APPROACH")
print("=" * 70)

p4_target_l = torch.tensor([[WAYPOINT_PHASE4_LEFT[0], WAYPOINT_PHASE4_LEFT[1], WAYPOINT_PHASE4_LEFT[2] + Z_OFFSET]],
                           device=device, dtype=torch.float32)
p4_target_r = torch.tensor([[WAYPOINT_PHASE4_RIGHT[0], WAYPOINT_PHASE4_RIGHT[1], WAYPOINT_PHASE4_RIGHT[2] + Z_OFFSET]],
                           device=device, dtype=torch.float32)

p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r = run_diff_ik_motion(
    p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r,
    p4_target_l, p4_target_r, PHASE34_STEPS, GRIPPER_CLOSE
)

f_l = get_contact_force(contact_left)
f_r = get_contact_force(contact_right)
print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
save_camera_images("phase4_approach")

# ============================================================
# PHASE 5: ABOVE HOOK (NEW WAYPOINTS)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 5: CABLE ABOVE HOOK")
print(f"  Target: L={WAYPOINT_PHASE5_LEFT}, R={WAYPOINT_PHASE5_RIGHT}")
print("=" * 70)

p5_target_l = torch.tensor([[WAYPOINT_PHASE5_LEFT[0], WAYPOINT_PHASE5_LEFT[1], WAYPOINT_PHASE5_LEFT[2] + Z_OFFSET]],
                           device=device, dtype=torch.float32)
p5_target_r = torch.tensor([[WAYPOINT_PHASE5_RIGHT[0], WAYPOINT_PHASE5_RIGHT[1], WAYPOINT_PHASE5_RIGHT[2] + Z_OFFSET]],
                           device=device, dtype=torch.float32)

p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r = run_diff_ik_motion(
    p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r,
    p5_target_l, p5_target_r, PHASE45_STEPS, GRIPPER_CLOSE
)

ee_l = get_ee_pos(robot_left, jacobian_body_left)
ee_r = get_ee_pos(robot_right, jacobian_body_right)
cable_c = get_cable_center()
f_l = get_contact_force(contact_left)
f_r = get_contact_force(contact_right)

print(f"  EE Left:  ({ee_l[0]:.3f}, {ee_l[1]:.3f}, {ee_l[2]:.3f})")
print(f"  EE Right: ({ee_r[0]:.3f}, {ee_r[1]:.3f}, {ee_r[2]:.3f})")
print(f"  Cable:    ({cable_c[0]:.3f}, {cable_c[1]:.3f}, {cable_c[2]:.3f})")
print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")

# Check alignment with hook
cable_to_hook_xy = np.sqrt((cable_c[0] - HOOK_X)**2 + (cable_c[1] - HOOK_Y)**2)
print(f"  Cable-Hook XY distance: {cable_to_hook_xy*100:.1f}cm")
save_camera_images("phase5_above_hook")

# ============================================================
# PHASE 5.5: LOWER ONTO HOOK
# ============================================================
print("\n" + "=" * 70)
print("PHASE 5.5: LOWER ONTO HOOK V-VALLEY")
print(f"  Target: L={WAYPOINT_PHASE55_LEFT}, R={WAYPOINT_PHASE55_RIGHT}")
print("=" * 70)

p55_target_l = torch.tensor([[WAYPOINT_PHASE55_LEFT[0], WAYPOINT_PHASE55_LEFT[1], WAYPOINT_PHASE55_LEFT[2] + Z_OFFSET]],
                            device=device, dtype=torch.float32)
p55_target_r = torch.tensor([[WAYPOINT_PHASE55_RIGHT[0], WAYPOINT_PHASE55_RIGHT[1], WAYPOINT_PHASE55_RIGHT[2] + Z_OFFSET]],
                            device=device, dtype=torch.float32)

p55_pos_l, p55_pos_r, p55_quat_l, p55_quat_r = run_diff_ik_motion(
    p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r,
    p55_target_l, p55_target_r, PHASE55_STEPS, GRIPPER_CLOSE
)

ee_l = get_ee_pos(robot_left, jacobian_body_left)
ee_r = get_ee_pos(robot_right, jacobian_body_right)
cable_c = get_cable_center()
f_l = get_contact_force(contact_left)
f_r = get_contact_force(contact_right)

print(f"  EE Left:  ({ee_l[0]:.3f}, {ee_l[1]:.3f}, {ee_l[2]:.3f})")
print(f"  EE Right: ({ee_r[0]:.3f}, {ee_r[1]:.3f}, {ee_r[2]:.3f})")
print(f"  Cable:    ({cable_c[0]:.3f}, {cable_c[1]:.3f}, {cable_c[2]:.3f})")
print(f"  Force: L={f_l:.1f}N, R={f_r:.1f}N")
save_camera_images("phase55_on_hook")

# ============================================================
# PHASE 6: STABILIZE, RELEASE AND RETREAT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 6: STABILIZE, RELEASE AND RETREAT")
print("=" * 70)

# Step 0: Stabilize before release (Option B)
print(f"  Stabilizing for {STABILIZE_STEPS} steps...")
for _ in range(STABILIZE_STEPS):
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

save_camera_images("phase55_stabilized")

# Step 1: Gradual gripper opening (release cable)
print(f"  Opening grippers gradually over {RELEASE_STEPS} steps...")
for i in range(RELEASE_STEPS):
    # Gradual opening from GRIPPER_CLOSE to GRIPPER_OPEN
    alpha = (i + 1) / RELEASE_STEPS
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

cable_after_release = get_cable_center()
print(f"  Cable after release: ({cable_after_release[0]:.3f}, {cable_after_release[1]:.3f}, {cable_after_release[2]:.3f})")
save_camera_images("phase6_release")

# Step 2: Retreat
print(f"  Retreating to: L={WAYPOINT_PHASE6_LEFT}, R={WAYPOINT_PHASE6_RIGHT}")

p6_target_l = torch.tensor([[WAYPOINT_PHASE6_LEFT[0], WAYPOINT_PHASE6_LEFT[1], WAYPOINT_PHASE6_LEFT[2] + Z_OFFSET]],
                           device=device, dtype=torch.float32)
p6_target_r = torch.tensor([[WAYPOINT_PHASE6_RIGHT[0], WAYPOINT_PHASE6_RIGHT[1], WAYPOINT_PHASE6_RIGHT[2] + Z_OFFSET]],
                           device=device, dtype=torch.float32)

# Current position after release
p55_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
p55_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

p6_pos_l, p6_pos_r, _, _ = run_diff_ik_motion(
    p55_pos_l, p55_pos_r, p55_quat_l, p55_quat_r,
    p6_target_l, p6_target_r, PHASE56_STEPS, GRIPPER_OPEN
)

# Stabilize
print("  Stabilizing...")
for _ in range(200):
    sim.step()
    scene.update(sim.get_physics_dt())

save_camera_images("phase6_retreat")

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)

final_cable = get_cable_center()
final_ee_l = get_ee_pos(robot_left, jacobian_body_left)
final_ee_r = get_ee_pos(robot_right, jacobian_body_right)

# Check if cable is on hook
cable_to_hook_xy = np.sqrt((final_cable[0] - HOOK_X)**2 + (final_cable[1] - HOOK_Y)**2)
cable_above_table = final_cable[2] - TABLE_HEIGHT
cable_near_hook_z = abs(final_cable[2] - HOOK_V_Z) < 0.10

print(f"\nCable position: ({final_cable[0]:.3f}, {final_cable[1]:.3f}, {final_cable[2]:.3f})")
print(f"Hook V-valley:  ({HOOK_X:.3f}, {HOOK_Y:.3f}, {HOOK_V_Z:.3f})")
print(f"Cable-Hook XY:  {cable_to_hook_xy*100:.1f}cm")
print(f"Cable above table: {cable_above_table*100:.1f}cm")
print(f"Cable near hook Z: {'YES' if cable_near_hook_z else 'NO'}")

# Success criteria
xy_aligned = cable_to_hook_xy < 0.10  # Within 10cm XY
z_on_hook = cable_above_table > 0.05 and cable_near_hook_z  # Above table, near hook Z

print(f"\nVerification:")
print(f"  1. XY aligned (<10cm):  {'PASS' if xy_aligned else 'FAIL'} ({cable_to_hook_xy*100:.1f}cm)")
print(f"  2. Cable on hook:       {'PASS' if z_on_hook else 'FAIL'} (Z={final_cable[2]:.3f})")

print("\n" + "=" * 70)
if xy_aligned and z_on_hook:
    print("SUCCESS: Cable appears to be on hook!")
else:
    print("PARTIAL: Cable may not be properly on hook")
print("=" * 70)

print(f"\nImages saved to: {OUTPUT_DIR}")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  - {f}")

simulation_app.close()
