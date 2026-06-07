#!/usr/bin/env python3
"""
Test different camera quaternion conventions to find what works
"""
import argparse
import sys
import os
import numpy as np
from scipy.spatial.transform import Rotation as R

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

def log(msg):
    print(msg, flush=True)

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=True)
args, _ = parser.parse_known_args()

log("[START] Camera Convention Test")

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, enable_cameras=True)
simulation_app = app_launcher.app

import torch
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.sensors import CameraCfg
from isaaclab.scene import InteractiveSceneCfg, InteractiveScene
from isaaclab.assets import AssetBaseCfg
from isaaclab.utils import configclass

output_dir = "/home/rlrk/IsaacLab/claude_code"
os.makedirs(output_dir, exist_ok=True)

# Camera position and target
CAM_POS = (1.0, 0.0, 1.0)
TARGET = (0.4, 0.0, 0.85)

def look_at_quat_ros(cam_pos, target):
    """ROS convention: +Y is forward"""
    forward = np.array(target) - np.array(cam_pos)
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0, 0, 1])
    right = np.cross(forward, world_up)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1, 0, 0])
    right = right / np.linalg.norm(right)
    up = np.cross(right, forward)
    up = up / np.linalg.norm(up)
    rot_matrix = np.column_stack([right, forward, up])
    rot = R.from_matrix(rot_matrix)
    q = rot.as_quat()
    w, x, y, z = q[3], q[0], q[1], q[2]
    if w < 0:
        w, x, y, z = -w, -x, -y, -z
    return (w, x, y, z)

def look_at_quat_opengl(cam_pos, target):
    """OpenGL convention: -Z is forward, +Y is up"""
    forward = np.array(target) - np.array(cam_pos)
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0, 0, 1])
    right = np.cross(forward, world_up)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1, 0, 0])
    right = right / np.linalg.norm(right)
    up = np.cross(right, forward)
    up = up / np.linalg.norm(up)
    rot_matrix = np.column_stack([right, up, -forward])
    rot = R.from_matrix(rot_matrix)
    q = rot.as_quat()
    w, x, y, z = q[3], q[0], q[1], q[2]
    if w < 0:
        w, x, y, z = -w, -x, -y, -z
    return (w, x, y, z)

log(f"\nCamera pos: {CAM_POS}")
log(f"Target: {TARGET}")

# Calculate quaternions
q_ros = look_at_quat_ros(CAM_POS, TARGET)
q_opengl = look_at_quat_opengl(CAM_POS, TARGET)

test_configs = [
    ("ros_y_fwd", q_ros, "ros"),
    ("opengl_negz", q_opengl, "ros"),
    ("ros_identity", (1.0, 0.0, 0.0, 0.0), "ros"),
    ("world_opengl", q_opengl, "world"),
    ("world_identity", (1.0, 0.0, 0.0, 0.0), "world"),
]

log("\nTest configurations:")
for name, q, conv in test_configs:
    log(f"  {name}: quat=({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f}), conv={conv}")

# Create scene
@configclass
class TestSceneCfg(InteractiveSceneCfg):
    num_envs = 1
    env_spacing = 3.0

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(10.0, 10.0)),
    )

    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0),
    )

    marker = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Marker",
        spawn=sim_utils.SphereCfg(
            radius=0.08,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(1.0, 0.0, 0.0),
                emissive_color=(1.0, 0.0, 0.0),
            ),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=TARGET),
    )

# Add cameras
for i, (name, quat, conv) in enumerate(test_configs):
    @configclass
    class DynCam(CameraCfg):
        prim_path = f"{{ENV_REGEX_NS}}/Cam{i}"
        spawn = sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            horizontal_aperture=20.955,
            clipping_range=(0.1, 20.0),
        )
        offset = CameraCfg.OffsetCfg(
            pos=CAM_POS,
            rot=quat,
            convention=conv,
        )
        width = 256
        height = 256
        data_types = ["rgb"]
        update_period = 0.0
    setattr(TestSceneCfg, f"cam{i}", DynCam())

log("\n[Setup] Creating scene...")
scene_cfg = TestSceneCfg()
sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
sim = sim_utils.SimulationContext(sim_cfg)
sim.set_camera_view([2.0, 0.0, 1.5], TARGET)

scene = InteractiveScene(scene_cfg)
sim.reset()

for _ in range(30):
    sim.step()
scene.update(dt=sim.get_physics_dt())

log("\n[Capture] Taking images...")
images = []
labels = []
results = []

for i, (name, _, _) in enumerate(test_configs):
    sensor_name = f"cam{i}"
    if sensor_name in scene._sensors:
        camera = scene._sensors[sensor_name]
        rgb_data = camera.data.output.get('rgb', None)
        if rgb_data is not None and len(rgb_data) > 0:
            img_np = rgb_data[0].cpu().numpy()
            if img_np.dtype != np.uint8:
                if img_np.max() <= 1.0:
                    img_np = (img_np * 255).astype(np.uint8)
                else:
                    img_np = img_np.astype(np.uint8)
            if img_np.shape[-1] == 4:
                img_np = img_np[:, :, :3]
            images.append(img_np)
            labels.append(name)

            red_mask = (img_np[:,:,0] > 200) & (img_np[:,:,1] < 100) & (img_np[:,:,2] < 100)
            red_count = np.sum(red_mask)

            img_path = os.path.join(output_dir, f'conv_{name}.png')
            Image.fromarray(img_np).save(img_path)
            marker_status = "VISIBLE!" if red_count > 100 else "not visible"
            log(f"  {name}: red pixels={red_count}, marker {marker_status}")
            results.append((name, red_count, marker_status))

if len(images) >= 4:
    while len(images) < 6:
        blank = np.ones((256, 256, 3), dtype=np.uint8) * 200
        images.append(blank)
        labels.append("blank")

    row1 = np.concatenate(images[:3], axis=1)
    row2 = np.concatenate(images[3:6], axis=1)
    combined = np.concatenate([row1, row2], axis=0)
    combined_path = os.path.join(output_dir, 'convention_test.png')
    Image.fromarray(combined).save(combined_path)
    log(f"\n[Combined] {combined_path}")
    log(f"Row 1: {labels[:3]}")
    log(f"Row 2: {labels[3:6]}")

log("\n" + "="*60)
log("SUMMARY - Working conventions:")
for name, count, status in results:
    if count > 100:
        log(f"  *** {name}: {count} red pixels - WORKING! ***")
log("="*60)

log("\n[Done]")
simulation_app.close()
