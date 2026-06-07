#!/usr/bin/env python3
"""
Inspect finger USD structure to find collision geometry
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
print("FINGER USD STRUCTURE INSPECTION")
print("=" * 70)

def inspect_prim_recursive(prim, indent=0):
    """Recursively inspect prim and its children"""
    prefix = "  " * indent
    path = prim.GetPath().pathString
    prim_type = prim.GetTypeName()

    # Check APIs
    has_collision = prim.HasAPI(UsdPhysics.CollisionAPI)
    has_rigidbody = prim.HasAPI(UsdPhysics.RigidBodyAPI)
    has_material = prim.HasAPI(UsdPhysics.MaterialAPI)
    has_physx_collision = prim.HasAPI(PhysxSchema.PhysxCollisionAPI)

    # Check for mesh
    is_mesh = prim.IsA(UsdGeom.Mesh)

    apis = []
    if has_collision:
        apis.append("Collision")
    if has_rigidbody:
        apis.append("RigidBody")
    if has_material:
        apis.append("Material")
    if has_physx_collision:
        apis.append("PhysxCollision")
    if is_mesh:
        apis.append("MESH")

    api_str = f" [{', '.join(apis)}]" if apis else ""

    print(f"{prefix}{path.split('/')[-1]} ({prim_type}){api_str}")

    # If collision API, check properties
    if has_collision:
        collision_api = UsdPhysics.CollisionAPI(prim)
        enabled = collision_api.GetCollisionEnabledAttr().Get()
        print(f"{prefix}  -> collision_enabled: {enabled}")

    # If PhysX collision, check contact/rest offset
    if has_physx_collision:
        physx_api = PhysxSchema.PhysxCollisionAPI(prim)
        contact_offset = physx_api.GetContactOffsetAttr().Get()
        rest_offset = physx_api.GetRestOffsetAttr().Get()
        print(f"{prefix}  -> contact_offset: {contact_offset}, rest_offset: {rest_offset}")

    # Recurse into children
    for child in prim.GetChildren():
        inspect_prim_recursive(child, indent + 1)

# Inspect Left finger
print("\n" + "=" * 70)
print("LEFT FINGER (panda_leftfinger)")
print("=" * 70)
left_finger = stage.GetPrimAtPath("/World/envs/env_0/Robot_Left/panda_leftfinger")
if left_finger.IsValid():
    inspect_prim_recursive(left_finger)

# Inspect Right finger
print("\n" + "=" * 70)
print("RIGHT FINGER (panda_rightfinger)")
print("=" * 70)
right_finger = stage.GetPrimAtPath("/World/envs/env_0/Robot_Left/panda_rightfinger")
if right_finger.IsValid():
    inspect_prim_recursive(right_finger)

# Also check cable segment structure
print("\n" + "=" * 70)
print("CABLE SEGMENT (seg_17)")
print("=" * 70)
cable_seg = stage.GetPrimAtPath("/World/envs/env_0/Cable/seg_17")
if cable_seg.IsValid():
    inspect_prim_recursive(cable_seg)

# Summary: Find all prims with CollisionAPI under fingers
print("\n" + "=" * 70)
print("COLLISION PRIMS SUMMARY")
print("=" * 70)

finger_paths = [
    "/World/envs/env_0/Robot_Left/panda_leftfinger",
    "/World/envs/env_0/Robot_Left/panda_rightfinger",
    "/World/envs/env_0/Robot_Right/panda_leftfinger",
    "/World/envs/env_0/Robot_Right/panda_rightfinger",
]

for finger_path in finger_paths:
    finger_prim = stage.GetPrimAtPath(finger_path)
    if finger_prim.IsValid():
        print(f"\n{finger_path}:")
        # Find all collision prims
        for desc in Usd.PrimRange(finger_prim):
            if desc.HasAPI(UsdPhysics.CollisionAPI):
                print(f"  COLLISION: {desc.GetPath().pathString}")
                # Check material binding
                mat_api = UsdPhysics.MaterialAPI(desc)
                if mat_api:
                    binding = mat_api.GetMaterialBindingAPI()

simulation_app.close()
