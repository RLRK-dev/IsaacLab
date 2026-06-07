#!/usr/bin/env python3
"""
カメラビューのデバッグ - テーブルが見えない問題の調査
"""
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=True)
args, _ = parser.parse_known_args()

print("[START] Debug Camera View")

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
from envs.dual_arm_cfg import DualArmSceneCfg

output_dir = "/home/rlrk/IsaacLab/claude_code"
os.makedirs(output_dir, exist_ok=True)

# Setup scene
print("[Setup] Creating scene...")
scene_cfg = DualArmSceneCfg()
scene_cfg.num_envs = 1

sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
sim = sim_utils.SimulationContext(sim_cfg)
sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

scene = InteractiveScene(scene_cfg)
sim.reset()

# Debug: Check USD stage for table
print("\n[Debug] Checking USD stage...")
import omni.usd
stage = omni.usd.get_context().get_stage()

# List all prims in the scene
print("\n[Debug] All prims in /World/envs/env_0:")
env_path = "/World/envs/env_0"
env_prim = stage.GetPrimAtPath(env_path)
if env_prim.IsValid():
    for child in env_prim.GetChildren():
        print(f"  - {child.GetPath()}")
        # Check position if it's a transformable
        from pxr import UsdGeom
        xformable = UsdGeom.Xformable(child)
        if xformable:
            try:
                xform_ops = xformable.GetOrderedXformOps()
                for op in xform_ops:
                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                        val = op.Get()
                        print(f"      Position: ({val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f})")
            except:
                pass

# Check table specifically
print("\n[Debug] Table prim check:")
table_path = "/World/envs/env_0/Table"
table_prim = stage.GetPrimAtPath(table_path)
if table_prim.IsValid():
    print(f"  Table exists: YES")
    print(f"  Prim type: {table_prim.GetTypeName()}")

    # Get bounding box
    from pxr import UsdGeom
    bbox_cache = UsdGeom.BBoxCache(0, ["default", "render"])
    bbox = bbox_cache.ComputeWorldBound(table_prim)
    bbox_range = bbox.GetRange()
    print(f"  Bounding box: {bbox_range}")

    # Check visibility
    imageable = UsdGeom.Imageable(table_prim)
    if imageable:
        vis = imageable.ComputeVisibility()
        print(f"  Visibility: {vis}")
else:
    print(f"  Table exists: NO - THIS IS THE PROBLEM!")

# Check cameras
print("\n[Debug] Camera prims:")
camera_names = ['FrontLeftCamera', 'FrontRightCamera', 'BackCamera', 'OverheadCamera']
for cam_name in camera_names:
    cam_path = f"/World/envs/env_0/{cam_name}"
    cam_prim = stage.GetPrimAtPath(cam_path)
    if cam_prim.IsValid():
        print(f"  {cam_name}: EXISTS")
        from pxr import UsdGeom
        xformable = UsdGeom.Xformable(cam_prim)
        if xformable:
            world_transform = xformable.ComputeLocalToWorldTransform(0)
            translation = world_transform.ExtractTranslation()
            print(f"    World Position: ({translation[0]:.2f}, {translation[1]:.2f}, {translation[2]:.2f})")
    else:
        print(f"  {cam_name}: NOT FOUND")

# Run a few simulation steps
print("\n[Sim] Running simulation steps...")
for i in range(30):
    sim.step()
scene.update(dt=sim.get_physics_dt())

# Take pictures
print("\n[Capture] Taking camera images...")
camera_sensors = {
    'front_left': 'front_left_camera',
    'front_right': 'front_right_camera',
    'back': 'back_camera',
    'overhead': 'overhead_camera',
}

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

            img_path = os.path.join(output_dir, f'debug_{name}.png')
            Image.fromarray(img_np).save(img_path)
            print(f"  {name}: saved to {img_path}")

print("\n[Done]")
simulation_app.close()
