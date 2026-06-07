#!/usr/bin/env python3
"""
Deep inspect collision geometry under finger prims
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema

# Setup
sim_cfg = sim_utils.SimulationCfg(dt=1/240)
sim = sim_utils.SimulationContext(sim_cfg)
scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
scene = InteractiveScene(scene_cfg)
sim.reset()

stage = sim.stage

print("=" * 70)
print("DEEP COLLISION INSPECTION")
print("=" * 70)

# Inspect all descendants of left finger
finger_path = "/World/envs/env_0/Robot_Left/panda_leftfinger"
print(f"\nAll descendants of {finger_path}:")
print("-" * 70)

finger_prim = stage.GetPrimAtPath(finger_path)
if finger_prim.IsValid():
    for desc in Usd.PrimRange(finger_prim):
        path = desc.GetPath().pathString
        prim_type = desc.GetTypeName()

        # Check all relevant APIs
        apis = []
        if desc.HasAPI(UsdPhysics.CollisionAPI):
            apis.append("CollisionAPI")
        if desc.HasAPI(UsdPhysics.RigidBodyAPI):
            apis.append("RigidBodyAPI")
        if desc.HasAPI(UsdPhysics.MaterialAPI):
            apis.append("MaterialAPI")
        if desc.HasAPI(PhysxSchema.PhysxCollisionAPI):
            apis.append("PhysxCollisionAPI")
        if desc.IsA(UsdGeom.Mesh):
            apis.append("MESH")
        if desc.IsA(UsdGeom.Capsule):
            apis.append("CAPSULE")
        if desc.IsA(UsdGeom.Sphere):
            apis.append("SPHERE")

        indent = "  " * (path.count("/") - finger_path.count("/"))
        api_str = f" [{', '.join(apis)}]" if apis else ""
        print(f"{indent}{path.split('/')[-1]} ({prim_type}){api_str}")

# Look for material bindings
print("\n" + "=" * 70)
print("MATERIAL BINDINGS")
print("=" * 70)

from pxr import UsdShade

# Check material binding on collision prims
collision_paths = [
    "/World/envs/env_0/Robot_Left/panda_leftfinger/collisions",
    "/World/envs/env_0/Robot_Left/panda_rightfinger/collisions",
]

for coll_path in collision_paths:
    coll_prim = stage.GetPrimAtPath(coll_path)
    if coll_prim.IsValid():
        print(f"\n{coll_path}:")
        for desc in Usd.PrimRange(coll_prim):
            path = desc.GetPath().pathString

            # Check for material binding
            binding_api = UsdShade.MaterialBindingAPI(desc)
            if binding_api:
                mat_path = binding_api.GetDirectBinding().GetMaterialPath()
                if mat_path:
                    print(f"  {path.split('/')[-1]}: bound to {mat_path}")

            # Check for physics material
            if desc.HasAPI(UsdPhysics.MaterialAPI):
                print(f"  {path.split('/')[-1]}: has PhysicsMaterialAPI")

# Check the high friction material we created
print("\n" + "=" * 70)
print("HIGH FRICTION MATERIAL CHECK")
print("=" * 70)

mat_path = "/World/Materials/HighFrictionPhys"
mat_prim = stage.GetPrimAtPath(mat_path)
if mat_prim and mat_prim.IsValid():
    print(f"Found: {mat_path}")
    if mat_prim.HasAPI(UsdPhysics.MaterialAPI):
        mat_api = UsdPhysics.MaterialAPI(mat_prim)
        static_friction = mat_api.GetStaticFrictionAttr().Get()
        dynamic_friction = mat_api.GetDynamicFrictionAttr().Get()
        print(f"  static_friction: {static_friction}")
        print(f"  dynamic_friction: {dynamic_friction}")
else:
    print(f"NOT FOUND: {mat_path}")

simulation_app.close()
