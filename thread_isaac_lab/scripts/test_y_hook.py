#!/usr/bin/env python3
"""
Y字フックとケーブルのゴール状態を可視化
Y-Hook with Cable Goal State Visualization
"""
import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=1)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import math
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf, Sdf

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.utils import configclass
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def create_y_hook(
    base_path: str = "/World/envs/env_0",
    hook_name: str = "y_hook",
    position: tuple = (0.6, 0.0, 0.85),
    arm_angle: float = 45.0,
    arm_length: float = 0.06,
    stem_length: float = 0.10,
    radius: float = 0.008,
    color: tuple = (0.2, 0.5, 0.9),
):
    """
    Create a Y-shaped hook using USD primitives.

    Structure:
         ╲   ╱  ← left arm, right arm (angled)
          ╲ ╱
           │    ← stem (vertical)
           │

    Args:
        base_path: Base USD path
        hook_name: Name for the hook
        position: Base position (x, y, z) - bottom of stem
        arm_angle: Angle of arms from vertical (degrees)
        arm_length: Length of each arm
        stem_length: Length of vertical stem
        radius: Radius of cylinders
        color: RGB color tuple

    Returns:
        Tuple of prim paths (stem, arm_left, arm_right)
    """
    stage = omni.usd.get_context().get_stage()

    hook_root_path = f"{base_path}/{hook_name}"
    UsdGeom.Xform.Define(stage, hook_root_path)

    angle_rad = math.radians(arm_angle)

    # Stem top position (where arms connect)
    stem_top_z = position[2] + stem_length

    # Arm offsets from stem top
    arm_offset_x = (arm_length / 2) * math.sin(angle_rad)
    arm_offset_z = (arm_length / 2) * math.cos(angle_rad)

    paths = []

    # 1. Stem (vertical part)
    stem_path = f"{hook_root_path}/stem"
    stem = UsdGeom.Cylinder.Define(stage, stem_path)
    stem.GetRadiusAttr().Set(radius)
    stem.GetHeightAttr().Set(stem_length)
    stem.GetAxisAttr().Set("Z")

    stem_xform = UsdGeom.Xformable(stem)
    stem_xform.AddTranslateOp().Set(Gf.Vec3d(
        position[0],
        position[1],
        position[2] + stem_length / 2  # Center of stem
    ))

    UsdPhysics.RigidBodyAPI.Apply(stem.GetPrim())
    stem.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(stem.GetPrim())
    stem.GetDisplayColorAttr().Set([color])
    paths.append(stem_path)

    # 2. Left arm (angled left-up)
    arm_left_path = f"{hook_root_path}/arm_left"
    arm_left = UsdGeom.Cylinder.Define(stage, arm_left_path)
    arm_left.GetRadiusAttr().Set(radius)
    arm_left.GetHeightAttr().Set(arm_length)
    arm_left.GetAxisAttr().Set("Z")

    arm_left_xform = UsdGeom.Xformable(arm_left)
    arm_left_xform.AddTranslateOp().Set(Gf.Vec3d(
        position[0] - arm_offset_x,
        position[1],
        stem_top_z + arm_offset_z
    ))
    # Rotate around Y axis
    arm_left_xform.AddRotateYOp().Set(-arm_angle)

    UsdPhysics.RigidBodyAPI.Apply(arm_left.GetPrim())
    arm_left.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(arm_left.GetPrim())
    arm_left.GetDisplayColorAttr().Set([color])
    paths.append(arm_left_path)

    # 3. Right arm (angled right-up)
    arm_right_path = f"{hook_root_path}/arm_right"
    arm_right = UsdGeom.Cylinder.Define(stage, arm_right_path)
    arm_right.GetRadiusAttr().Set(radius)
    arm_right.GetHeightAttr().Set(arm_length)
    arm_right.GetAxisAttr().Set("Z")

    arm_right_xform = UsdGeom.Xformable(arm_right)
    arm_right_xform.AddTranslateOp().Set(Gf.Vec3d(
        position[0] + arm_offset_x,
        position[1],
        stem_top_z + arm_offset_z
    ))
    # Rotate around Y axis
    arm_right_xform.AddRotateYOp().Set(arm_angle)

    UsdPhysics.RigidBodyAPI.Apply(arm_right.GetPrim())
    arm_right.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(arm_right.GetPrim())
    arm_right.GetDisplayColorAttr().Set([color])
    paths.append(arm_right_path)

    print(f"[Y-Hook] Created at {position}")
    print(f"  Stem: height={stem_length}m")
    print(f"  Arms: length={arm_length}m, angle={arm_angle}°")

    return tuple(paths)


def create_cable_on_y_hook(
    base_path: str = "/World/envs/env_0",
    cable_name: str = "cable_goal",
    hook_position: tuple = (0.6, 0.0, 0.85),
    hook_stem_length: float = 0.10,
    num_segments: int = 10,
    segment_radius: float = 0.006,
    color: tuple = (1.0, 0.5, 0.0),
):
    """
    Create cable segments positioned in a U-shape around Y-hook.

    The cable hangs in the V-part of the Y-hook.

    Args:
        base_path: Base USD path
        cable_name: Name for cable group
        hook_position: Y-hook base position
        hook_stem_length: Height of hook stem
        num_segments: Number of cable segments
        segment_radius: Radius of cable segments
        color: RGB color tuple

    Returns:
        List of segment prim paths
    """
    stage = omni.usd.get_context().get_stage()

    cable_root_path = f"{base_path}/{cable_name}"
    UsdGeom.Xform.Define(stage, cable_root_path)

    # Y-hook junction point (where arms meet stem)
    junction_x = hook_position[0]
    junction_y = hook_position[1]
    junction_z = hook_position[2] + hook_stem_length

    segment_paths = []
    segment_length = 0.025

    for i in range(num_segments):
        seg_path = f"{cable_root_path}/seg_{i:02d}"

        # U-shape around hook junction
        # Progress from left side, down through junction, up right side
        t = i / (num_segments - 1)  # 0 to 1

        if t < 0.4:
            # Left side - descending
            progress = t / 0.4
            x_offset = -0.06 + progress * 0.03
            y_offset = 0.0
            z_offset = 0.08 - progress * 0.10
        elif t < 0.6:
            # Bottom of U - at junction level
            progress = (t - 0.4) / 0.2
            x_offset = -0.03 + progress * 0.06
            y_offset = 0.0
            z_offset = -0.02
        else:
            # Right side - ascending
            progress = (t - 0.6) / 0.4
            x_offset = 0.03 + progress * 0.03
            y_offset = 0.0
            z_offset = -0.02 + progress * 0.10

        seg_pos = Gf.Vec3d(
            junction_x + x_offset,
            junction_y + y_offset,
            junction_z + z_offset
        )

        # Create capsule segment
        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(segment_radius)
        capsule.GetHeightAttr().Set(segment_length)
        capsule.GetAxisAttr().Set("X")  # Horizontal orientation

        xform = UsdGeom.Xformable(capsule)
        xform.AddTranslateOp().Set(seg_pos)

        # Add physics (dynamic)
        UsdPhysics.RigidBodyAPI.Apply(capsule.GetPrim())
        UsdPhysics.MassAPI.Apply(capsule.GetPrim()).GetMassAttr().Set(0.003)
        UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())

        capsule.GetDisplayColorAttr().Set([color])

        segment_paths.append(seg_path)

    print(f"[Cable] Created {num_segments} segments in goal position")

    return segment_paths


@configclass
class YHookGoalSceneCfg:
    """Scene configuration for Y-hook goal state visualization."""

    num_envs: int = 1
    env_spacing: float = 3.0

    # Ground
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    # Light
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0)),
    )

    # Table
    table = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/table",
        spawn=sim_utils.CuboidCfg(
            size=(0.8, 1.0, 0.03),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.7, 0.6, 0.5)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.5, 0.0, 0.735),
        ),
    )


def main():
    print("\n" + "="*60)
    print("Y-HOOK GOAL STATE VISUALIZATION")
    print("Cable hanging on Y-shaped hook")
    print("="*60)

    # Setup simulation
    print("\n[Status] Setting up simulation...")
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(1.0, -0.6, 1.1),
        target=(0.6, 0.0, 0.85)
    )

    # Spawn ground and light manually
    print("[Status] Creating ground and lights...")
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/ground", ground_cfg)

    light_cfg = sim_utils.DomeLightCfg(intensity=1500.0)
    light_cfg.func("/World/DomeLight", light_cfg)

    # Spawn table
    print("[Status] Creating table...")
    table_cfg = sim_utils.CuboidCfg(
        size=(0.8, 1.0, 0.03),
        rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.7, 0.6, 0.5)),
    )
    table_cfg.func("/World/envs/env_0/table", table_cfg, translation=(0.5, 0.0, 0.735))

    # Create Y-hook
    print("[Status] Creating Y-hook...")
    hook_pos = (0.6, 0.0, 0.75)
    y_hook_paths = create_y_hook(
        base_path="/World/envs/env_0",
        hook_name="y_hook",
        position=hook_pos,
        arm_angle=45.0,
        arm_length=0.06,
        stem_length=0.10,
        radius=0.008,
        color=(0.2, 0.5, 0.9),
    )

    # Create cable in goal position (on hook)
    print("[Status] Creating cable in goal position...")
    cable_paths = create_cable_on_y_hook(
        base_path="/World/envs/env_0",
        cable_name="cable_goal",
        hook_position=hook_pos,
        hook_stem_length=0.10,
        num_segments=10,
        segment_radius=0.006,
        color=(1.0, 0.5, 0.0),
    )

    # Reset simulation
    print("[Status] Starting simulation...")
    sim.reset()

    # Let physics settle
    print("[Status] Letting physics settle...")
    for _ in range(60):
        sim.step()

    print("\n" + "="*60)
    print("GOAL STATE DISPLAYED!")
    print("")
    print("This shows the target state for the cable manipulation task:")
    print("  - Orange cable hanging in the V-part of the Y-hook")
    print("  - Y-hook (blue) mounted on table")
    print("")
    print("Hook structure:")
    print("     ╲   ╱  ← Left/Right arms (45° angle)")
    print("      ╲ ╱")
    print("       │    ← Stem (vertical)")
    print("       │")
    print("")
    print("Close window to exit.")
    print("="*60 + "\n")

    # Keep running for visualization
    step = 0
    while simulation_app.is_running():
        sim.step()
        step += 1

        if step % 1200 == 0:
            print(f"[Step {step}] Simulation running...")


if __name__ == "__main__":
    main()
    simulation_app.close()
