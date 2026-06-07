#!/usr/bin/env python3
"""
Quick camera test - add a bright red marker to verify camera visibility
"""
import argparse
import sys
import os

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=True)
args, _ = parser.parse_known_args()

print("[START] Quick Camera Test", flush=True)

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, enable_cameras=True)
simulation_app = app_launcher.app

import torch
import numpy as np
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.assets import RigidObjectCfg

sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.dual_arm_cfg import DualArmSceneCfg

output_dir = "/home/rlrk/IsaacLab/claude_code"
os.makedirs(output_dir, exist_ok=True)

print("[Setup] Creating scene...", flush=True)
scene_cfg = DualArmSceneCfg()
scene_cfg.num_envs = 1

sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
sim = sim_utils.SimulationContext(sim_cfg)
sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

scene = InteractiveScene(scene_cfg)
sim.reset()
print("[Setup] Scene created", flush=True)

# Add a bright red marker sphere at the target position
print("[Marker] Adding red marker at (0.4, 0, 0.85)...", flush=True)
import omni.usd
from pxr import Gf, UsdGeom, UsdShade, Sdf

stage = omni.usd.get_context().get_stage()

# Create a red sphere at target position
marker_path = "/World/envs/env_0/DebugMarker"
sphere_geom = UsdGeom.Sphere.Define(stage, marker_path)
sphere_geom.GetRadiusAttr().Set(0.05)  # 5cm radius

# Set position
xform = UsdGeom.Xformable(sphere_geom.GetPrim())
xform.AddTranslateOp().Set(Gf.Vec3d(0.4, 0.0, 0.85))

# Add red material
material_path = f"{marker_path}/RedMaterial"
material = UsdShade.Material.Define(stage, material_path)
shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(sphere_geom.GetPrim()).Bind(material)

print("[Marker] Red marker added", flush=True)

# Run simulation steps
print("[Sim] Running 30 steps...", flush=True)
for i in range(30):
    sim.step()
scene.update(dt=sim.get_physics_dt())

# Capture images
print("[Capture] Capturing...", flush=True)
camera_sensors = {
    'front_left': 'front_left_camera',
    'front_right': 'front_right_camera',
    'back': 'back_camera',
    'overhead': 'overhead_camera',
}

images = []
for name, sensor_name in camera_sensors.items():
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
            img_path = os.path.join(output_dir, f'test_{name}.png')
            Image.fromarray(img_np).save(img_path)
            print(f"  {name}: saved", flush=True)

# Create combined
if len(images) == 4:
    top_row = np.concatenate([images[0], images[1]], axis=1)
    bottom_row = np.concatenate([images[2], images[3]], axis=1)
    combined = np.concatenate([top_row, bottom_row], axis=0)
    combined_path = os.path.join(output_dir, 'test_combined.png')
    Image.fromarray(combined).save(combined_path)
    print(f"[Combined] {combined_path}", flush=True)

print("[Done]", flush=True)
simulation_app.close()
