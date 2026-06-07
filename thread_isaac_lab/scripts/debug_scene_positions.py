#!/usr/bin/env python3
"""
シーンオブジェクト位置検証スクリプト
テーブル、フック、カメラの正確な位置を確認
"""
import argparse
import sys
sys.stdout = sys.__stdout__

def log(msg):
    print(msg, flush=True)

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=True)
args, _ = parser.parse_known_args()

log("[START] debug_scene_positions.py")

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, enable_cameras=True)
simulation_app = app_launcher.app

import torch
import numpy as np
from PIL import Image
import os
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT

log("[SETUP] Creating scene...")

scene_cfg = DualArmSceneCfg()
scene_cfg.num_envs = 1

sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
sim = sim_utils.SimulationContext(sim_cfg)
scene = InteractiveScene(scene_cfg)
sim.reset()

# Simulate a few steps
log("[SIM] Running simulation steps...")
for i in range(30):
    sim.step()
scene.update(dt=sim.get_physics_dt())

log("\n" + "="*70)
log("SCENE OBJECT POSITIONS")
log("="*70)

# Table position
if hasattr(scene, '_rigid_objects') and 'table' in scene._rigid_objects:
    table = scene._rigid_objects['table']
    pos = table.data.root_pos_w[0].cpu().numpy()
    log(f"\n[TABLE]")
    log(f"  Position (X, Y, Z): ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")
    log(f"  Expected Z (TABLE_HEIGHT - 0.01): {TABLE_HEIGHT - 0.01:.4f}")

# Y-hook
for name in ['hook_stem', 'hook_left_arm', 'hook_right_arm']:
    if hasattr(scene, '_rigid_objects') and name in scene._rigid_objects:
        obj = scene._rigid_objects[name]
        pos = obj.data.root_pos_w[0].cpu().numpy()
        log(f"\n[{name.upper()}]")
        log(f"  Position (X, Y, Z): ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")

# Cable
if hasattr(scene, '_rigid_objects') and 'cable' in scene._rigid_objects:
    cable = scene._rigid_objects['cable']
    pos = cable.data.root_pos_w[0].cpu().numpy()
    log(f"\n[CABLE]")
    log(f"  Position (X, Y, Z): ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")

# Robots
for name in ['robot_left', 'robot_right']:
    if hasattr(scene, '_articulations') and name in scene._articulations:
        robot = scene._articulations[name]
        pos = robot.data.root_pos_w[0].cpu().numpy()
        log(f"\n[{name.upper()}]")
        log(f"  Base Position (X, Y, Z): ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")

log("\n" + "-"*70)
log("CAMERA POSITIONS (World Frame)")
log("-"*70)

camera_info = []
for cam_name in ['front_left_camera', 'front_right_camera', 'back_camera', 'overhead_camera']:
    if hasattr(scene, '_sensors') and cam_name in scene._sensors:
        cam = scene._sensors[cam_name]
        if hasattr(cam, 'data') and hasattr(cam.data, 'pos_w'):
            pos = cam.data.pos_w[0].cpu().numpy()
            log(f"\n[{cam_name.upper()}]")
            log(f"  World Position: ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")
            camera_info.append((cam_name, pos))

            # Also get orientation
            if hasattr(cam.data, 'quat_w_world'):
                quat = cam.data.quat_w_world[0].cpu().numpy()
                log(f"  World Quaternion (w,x,y,z): ({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f})")

log("\n" + "-"*70)
log("CAMERA IMAGES")
log("-"*70)

output_dir = "/home/rlrk/IsaacLab/claude_code"
os.makedirs(output_dir, exist_ok=True)

images = {}
for cam_name in ['front_left_camera', 'front_right_camera', 'back_camera', 'overhead_camera']:
    if hasattr(scene, '_sensors') and cam_name in scene._sensors:
        cam = scene._sensors[cam_name]
        rgb = cam.data.output.get('rgb', None)
        if rgb is not None and len(rgb) > 0:
            img_np = rgb[0].cpu().numpy()
            if img_np.dtype != np.uint8:
                img_np = (img_np * 255).astype(np.uint8) if img_np.max() <= 1.0 else img_np.astype(np.uint8)
            if img_np.shape[-1] == 4:
                img_np = img_np[:, :, :3]

            short_name = cam_name.replace('_camera', '')
            img_path = os.path.join(output_dir, f'debug_{short_name}.png')
            Image.fromarray(img_np).save(img_path)
            images[short_name] = img_np
            log(f"  {cam_name}: saved to {img_path}")

# Create combined image
if len(images) == 4:
    top = np.concatenate([images['front_left'], images['front_right']], axis=1)
    bottom = np.concatenate([images['back'], images['overhead']], axis=1)
    combined = np.concatenate([top, bottom], axis=0)
    combined_path = os.path.join(output_dir, 'debug_combined.png')
    Image.fromarray(combined).save(combined_path)
    log(f"\n  Combined: {combined_path}")

log("\n" + "="*70)
log("[DONE]")
log("="*70)

simulation_app.close()
