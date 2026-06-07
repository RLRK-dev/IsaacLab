#!/usr/bin/env python3
"""
Test camera orientations using Euler angles
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

log("[START] Camera Euler Test")

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

TARGET = (0.4, 0.0, 0.85)

def euler_to_quat(roll, pitch, yaw, degrees=True):
    """Convert Euler angles to quaternion (w, x, y, z)"""
    rot = R.from_euler('xyz', [roll, pitch, yaw], degrees=degrees)
    q = rot.as_quat()  # [x, y, z, w]
    return (q[3], q[0], q[1], q[2])

# Test different orientations
# Camera at (1.0, 0, 1.0) looking at (0.4, 0, 0.85)
# Direction: (-0.6, 0, -0.15) -> angle = atan2(-0.15, -0.6) ≈ -166 deg (mostly -X with slight -Z)
CAM_POS = (1.0, 0.0, 1.0)

test_configs = [
    # (name, (roll, pitch, yaw), convention)
    ("pitch_neg90", (0, -90, 0), "world"),  # Looking down
    ("pitch_neg45", (0, -45, 0), "world"),  # Looking 45 deg down
    ("yaw_180", (0, 0, 180), "world"),  # Looking backward (-X)
    ("yaw_180_pitch_neg14", (0, -14, 180), "world"),  # Looking back and slightly down
    ("yaw_180_pitch_neg14_ros", (0, -14, 180), "ros"),  # Same with ROS
    ("identity_world", (0, 0, 0), "world"),  # Identity
]

log(f"\nCamera pos: {CAM_POS}")
log(f"Target: {TARGET}")
log("\nTest configurations:")

configs_with_quat = []
for name, (roll, pitch, yaw), conv in test_configs:
    quat = euler_to_quat(roll, pitch, yaw)
    log(f"  {name}: euler=({roll},{pitch},{yaw}), quat=({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f}), conv={conv}")
    configs_with_quat.append((name, quat, conv))

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

    # Large red marker at target
    marker = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Marker",
        spawn=sim_utils.SphereCfg(
            radius=0.1,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(1.0, 0.0, 0.0),
                emissive_color=(1.0, 0.0, 0.0),
            ),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=TARGET),
    )

for i, (name, quat, conv) in enumerate(configs_with_quat):
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

for i, (name, _, _) in enumerate(configs_with_quat):
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

            img_path = os.path.join(output_dir, f'euler_{name}.png')
            Image.fromarray(img_np).save(img_path)
            marker_status = "VISIBLE!" if red_count > 100 else "not visible"
            log(f"  {name}: red pixels={red_count}, marker {marker_status}")

if len(images) >= 4:
    while len(images) < 6:
        blank = np.ones((256, 256, 3), dtype=np.uint8) * 200
        images.append(blank)
        labels.append("blank")

    row1 = np.concatenate(images[:3], axis=1)
    row2 = np.concatenate(images[3:6], axis=1)
    combined = np.concatenate([row1, row2], axis=0)
    combined_path = os.path.join(output_dir, 'euler_test.png')
    Image.fromarray(combined).save(combined_path)
    log(f"\n[Combined] {combined_path}")
    log(f"Row 1: {labels[:3]}")
    log(f"Row 2: {labels[3:6]}")

log("\n[Done]")
simulation_app.close()
