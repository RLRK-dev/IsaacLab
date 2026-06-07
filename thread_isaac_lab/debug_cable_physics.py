#!/usr/bin/env python3
"""
Debug script: Check cable and table collision
"""

from __future__ import annotations
import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Debug cable physics")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

print("=" * 60)
print("Debug: Cable Physics Test")
print("=" * 60)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import AssetBaseCfg, RigidObject, RigidObjectCfg
from isaaclab.utils import configclass


@configclass
class DebugSceneCfg(InteractiveSceneCfg):
    """Debug scene with table and cable."""

    num_envs: int = 1
    env_spacing: float = 2.0

    # Ground
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # Light
    light = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(intensity=1000.0, color=(1.0, 1.0, 1.0)),
    )

    # Table at height 75cm
    table: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.CuboidCfg(
            size=(0.8, 0.6, 0.02),  # 80cm x 60cm x 2cm
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=True,
                disable_gravity=True,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.6, 0.5, 0.4),
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.4, 0.0, 0.74),  # Table center at 74cm (top at 75cm)
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    # Cable on table
    cable: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=sim_utils.CylinderCfg(
            radius=0.01,  # 1cm radius
            height=0.05,  # 5cm height (shorter for testing)
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=1.0,
            ),
            mass_props=sim_utils.MassPropertiesCfg(
                mass=0.05,  # 50g
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.2, 0.2, 0.8),
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.4, 0.0, 0.80),  # Start above table (75cm + 5cm)
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )


def main():
    print("\n[1/3] Creating simulation context...")

    sim_cfg = sim_utils.SimulationCfg(
        dt=1/120.0,
        device="cuda:0",
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.5, 1.5, 1.5), target=(0.4, 0.0, 0.75))

    print("\n[2/3] Creating scene...")

    scene_cfg = DebugSceneCfg()
    scene = InteractiveScene(scene_cfg)

    print("\n[3/3] Running simulation for 500 steps (4 seconds)...")

    sim.reset()
    scene.reset()

    print(f"\n  Table position: (0.4, 0.0, 0.74) - top surface at z=0.75")
    print(f"  Cable initial:  (0.4, 0.0, 0.80)")
    print(f"  Expected: Cable should fall and rest on table (z ≈ 0.76)")
    print()

    for step in range(500):
        scene.write_data_to_sim()
        sim.step()
        scene.update(dt=sim.get_physics_dt())

        cable: RigidObject = scene["cable"]
        table: RigidObject = scene["table"]

        cable_pos = cable.data.root_pos_w[0]
        cable_vel = cable.data.root_lin_vel_w[0]
        table_pos = table.data.root_pos_w[0]

        if step % 50 == 0:
            print(f"  Step {step:3d}: cable z={cable_pos[2]:.4f}, vel_z={cable_vel[2]:.4f}")

    # Final state
    final_cable_z = cable.data.root_pos_w[0, 2].item()
    print(f"\n  Final cable z: {final_cable_z:.4f}")

    if final_cable_z > 0.75:
        print("  [OK] Cable resting on table!")
    elif final_cable_z > 0.70:
        print("  [WARN] Cable slightly below table surface")
    else:
        print("  [ERROR] Cable fell through table!")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulation_app.close()
