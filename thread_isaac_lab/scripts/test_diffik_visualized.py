#!/usr/bin/env python3
"""
Diff IK Lift Test with Camera Capture
- Captures images to identify when/why contact is lost
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = False  # Enable rendering
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
import os
from datetime import datetime
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg, CameraCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS

# Output directory for images
OUTPUT_DIR = "/tmp/diffik_visualized"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("DIFF IK LIFT TEST WITH VISUALIZATION")
print(f"Images saved to: {OUTPUT_DIR}")
print("=" * 60)

# Parameters
GRIPPER_CLOSE = 0.003
FRICTION = 5.0
CAPTURE_INTERVAL = 120  # 0.5 sec at 240Hz

# Setup
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
    # Camera for visualization
    camera: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/Camera",
        update_period=0.0,
        height=480,
        width=640,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=400.0,
            horizontal_aperture=20.955,
            clipping_range=(0.1, 10.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(1.5, 0.0, 1.5),
            rot=(0.853, 0.0, 0.522, 0.0),
            convention="world",
        ),
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
camera = scene["camera"]

device = robot_left.device

# Apply friction
print("\nApplying friction=5.0...")
def set_friction(asset, value):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = value
    materials[..., 1] = value
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, FRICTION)
set_friction(robot_right, FRICTION)
set_friction(cable, FRICTION)

# Setup Diff IK controllers
diff_ik_cfg = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=True,
    ik_method="dls",
    ik_params={"lambda_val": 0.1},
)
diff_ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

def get_ee_pos(robot, jacobian_body_idx):
    return robot.data.body_pos_w[0, jacobian_body_idx].cpu().numpy()

def get_contact_force(sensor):
    return np.linalg.norm(sensor.data.net_forces_w[0].cpu().numpy())

def get_cable_seg10_z():
    """Get Z position of cable segment 10 (center)"""
    # Cable has 20 segments (seg_0 to seg_19), seg_10 is center
    try:
        z_values = cable.data.body_pos_w[0, :, 2].cpu().numpy()
        if len(z_values) >= 11:
            return z_values[10]  # seg_10
        return np.nanmean(z_values)
    except:
        return float('nan')

def save_camera_image(frame_name):
    """Save camera image"""
    try:
        camera.update(sim.get_physics_dt())
        rgb_data = camera.data.output["rgb"][0].cpu().numpy()
        if rgb_data is not None and rgb_data.size > 0:
            from PIL import Image
            img = Image.fromarray(rgb_data[:, :, :3].astype(np.uint8))
            filepath = os.path.join(OUTPUT_DIR, f"{frame_name}.png")
            img.save(filepath)
            print(f"  Saved: {filepath}")
            return filepath
    except Exception as e:
        print(f"  Camera error: {e}")
    return None

# Data log
log_data = []

def log_state(step, phase, save_img=False, img_name=None):
    ee_left = get_ee_pos(robot_left, jacobian_body_left)
    ee_right = get_ee_pos(robot_right, jacobian_body_right)
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)
    cable_z = get_cable_seg10_z()

    entry = {
        'step': step,
        'phase': phase,
        'ee_left_z': ee_left[2],
        'ee_right_z': ee_right[2],
        'force_l': force_l,
        'force_r': force_r,
        'cable_z': cable_z,
    }
    log_data.append(entry)

    print(f"  [{phase}] Step {step}: EE_Z={ee_left[2]:.4f}, Force L={force_l:.3f}N R={force_r:.3f}N, Cable_Z={cable_z:.4f}")

    if save_img and img_name:
        save_camera_image(img_name)

    return entry

# ============================================================
# PHASE 1: OPEN GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 1: OPEN GRIPPERS")
print("=" * 60)

for _ in range(100):
    target = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target[0, -2:] = 0.04
    robot_left.set_joint_position_target(target)
    robot_left.write_data_to_sim()

    target = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target[0, -2:] = 0.04
    robot_right.set_joint_position_target(target)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

# ============================================================
# PHASE 2A: TELEPORT TO GRASP POSITION
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2A: TELEPORT TO GRASP POSITION")
print("=" * 60)

arm_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
arm_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
arm_left[0, -2:] = 0.04
robot_left.write_joint_state_to_sim(arm_left, robot_left.data.joint_vel[0].unsqueeze(0))

arm_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
arm_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
arm_right[0, -2:] = 0.04
robot_right.write_joint_state_to_sim(arm_right, robot_right.data.joint_vel[0].unsqueeze(0))

for _ in range(50):
    robot_left.set_joint_position_target(arm_left)
    robot_left.write_data_to_sim()
    robot_right.set_joint_position_target(arm_right)
    robot_right.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

# ============================================================
# PHASE 2B: CLOSE GRIPPERS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 2B: CLOSE GRIPPERS")
print("=" * 60)

for i in range(300):
    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = torch.tensor(PHASE2_LEFT_JOINTS, device=device)
    target_left[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = torch.tensor(PHASE2_RIGHT_JOINTS, device=device)
    target_right[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

# Capture Phase 2 complete
print("\n  Phase 2 Complete - Capturing image...")
log_state(0, "PHASE2_COMPLETE", save_img=True, img_name="phase2_complete")

phase2_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
phase2_force_l = get_contact_force(contact_left)
phase2_cable_z = get_cable_seg10_z()

# ============================================================
# PHASE 3: DIFF IK LIFT WITH DETAILED LOGGING
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: DIFF IK LIFT WITH VISUALIZATION")
print("=" * 60)

diff_ik_left.reset()
diff_ik_right.reset()

command = torch.tensor([[0.0, 0.0, 0.15, 0.0, 0.0, 0.0]], device=device)

ee_pos_left_t = robot_left.data.body_pos_w[:, jacobian_body_left]
ee_quat_left_t = robot_left.data.body_quat_w[:, jacobian_body_left]
ee_pos_right_t = robot_right.data.body_pos_w[:, jacobian_body_right]
ee_quat_right_t = robot_right.data.body_quat_w[:, jacobian_body_right]

diff_ik_left.set_command(command, ee_pos_left_t, ee_quat_left_t)
diff_ik_right.set_command(command, ee_pos_right_t, ee_quat_right_t)

contact_lost_step = None
contact_lost_ee_z = None
frame_count = 0

for i in range(600):
    jacobian_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jacobian_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

    ee_pos_left = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_left = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_right = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_right = robot_right.data.body_quat_w[:, jacobian_body_right]

    joint_pos_left = robot_left.data.joint_pos[:, :7]
    joint_pos_right = robot_right.data.joint_pos[:, :7]

    joint_cmd_left = diff_ik_left.compute(ee_pos_left, ee_quat_left, jacobian_left, joint_pos_left)
    joint_cmd_right = diff_ik_right.compute(ee_pos_right, ee_quat_right, jacobian_right, joint_pos_right)

    target_left = robot_left.data.joint_pos[0].unsqueeze(0).clone()
    target_left[0, :7] = joint_cmd_left[0]
    target_left[0, -2:] = GRIPPER_CLOSE
    robot_left.set_joint_position_target(target_left)
    robot_left.write_data_to_sim()

    target_right = robot_right.data.joint_pos[0].unsqueeze(0).clone()
    target_right[0, :7] = joint_cmd_right[0]
    target_right[0, -2:] = GRIPPER_CLOSE
    robot_right.set_joint_position_target(target_right)
    robot_right.write_data_to_sim()

    sim.step()
    scene.update(sim.get_physics_dt())

    # Check for contact loss
    force_l = get_contact_force(contact_left)
    force_r = get_contact_force(contact_right)

    if contact_lost_step is None and force_l < 0.5 and force_r < 0.5:
        contact_lost_step = i
        contact_lost_ee_z = get_ee_pos(robot_left, jacobian_body_left)[2]
        print(f"\n  *** CONTACT LOST at step {i} ***")
        log_state(i, "CONTACT_LOST", save_img=True, img_name=f"contact_lost_step{i:04d}")

    # Capture every 0.5 seconds (120 steps)
    if (i + 1) % CAPTURE_INTERVAL == 0:
        frame_count += 1
        log_state(i+1, f"LIFT_FRAME{frame_count}", save_img=True, img_name=f"lift_frame{frame_count:02d}_step{i+1:04d}")

# Final capture
print("\n  Phase 3 Complete - Capturing final image...")
log_state(600, "PHASE3_COMPLETE", save_img=True, img_name="phase3_complete")

# ============================================================
# ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)

if contact_lost_step is not None:
    lift_at_loss = contact_lost_ee_z - phase2_ee_z
    print(f"\n1. 接触喪失フレーム: Step {contact_lost_step} (約{contact_lost_step/240:.2f}秒)")
    print(f"2. 喪失時のEE Z: {contact_lost_ee_z:.4f} (リフト開始から {lift_at_loss*100:.2f}cm)")

    # Check cable position at contact loss
    cable_z_at_loss = None
    for entry in log_data:
        if entry['step'] == contact_lost_step:
            cable_z_at_loss = entry['cable_z']
            break

    if cable_z_at_loss is not None:
        cable_drop = phase2_cable_z - cable_z_at_loss
        print(f"3. 喪失時のケーブルZ: {cable_z_at_loss:.4f} (落下量: {cable_drop*100:.2f}cm)")

        if cable_drop > 0.01:
            print(f"4. 結論: ケーブルが先に落下（グリッパーより先にケーブルが下がった）")
        else:
            print(f"4. 結論: グリッパーがケーブルから離れた（ケーブル位置は維持）")
else:
    print("\n接触は維持されました！")

print("\n" + "=" * 60)
print(f"画像は {OUTPUT_DIR} に保存されています")
print("=" * 60)

# List saved images
import glob
images = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.png")))
print(f"\n保存された画像 ({len(images)}枚):")
for img in images:
    print(f"  {os.path.basename(img)}")

simulation_app.close()
