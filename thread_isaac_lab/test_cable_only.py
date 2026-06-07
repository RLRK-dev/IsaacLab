#!/usr/bin/env python3
"""
Simple test: Cable only (no robot)
- Ground + Light + Cable
- num_envs = 1
- Simulate 100 steps
"""

from __future__ import annotations
import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Cable-only test")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

print("=" * 60)
print("Test: Cable Only (No Robot)")
print("=" * 60)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

print("Isaac Sim initialized!")

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import AssetBaseCfg, RigidObject, RigidObjectCfg
from isaaclab.utils import configclass


@configclass
class CableOnlySceneCfg(InteractiveSceneCfg):
    """Minimal scene with just ground, light, and cable."""

    num_envs: int = 1
    env_spacing: float = 2.0

    # Ground plane - use AssetBaseCfg wrapper
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # Dome light - use AssetBaseCfg wrapper
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=500.0),
    )

    # Cable (simple cylinder as rigid object)
    cable: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=sim_utils.CylinderCfg(
            radius=0.01,  # 1cm radius
            height=0.30,  # 30cm length
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
                diffuse_color=(0.2, 0.2, 0.8),  # Blue
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.5),  # 50cm above ground
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )


def main():
    print("\n[1/3] Creating simulation context...")

    # Create simulation context
    sim_cfg = sim_utils.SimulationCfg(
        dt=1/120.0,
        device="cuda:0",
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(2.0, 2.0, 2.0), target=(0.0, 0.0, 0.5))

    print("\n[2/3] Creating scene with cable...")

    # Create scene
    scene_cfg = CableOnlySceneCfg()
    scene = InteractiveScene(scene_cfg)

    print("\n[3/3] Running simulation for 100 steps...")

    # Reset and step
    sim.reset()
    scene.reset()

    for step in range(100):
        # Write data to sim
        scene.write_data_to_sim()
        # Step simulation
        sim.step()
        # Update scene
        scene.update(dt=sim.get_physics_dt())

        # Get cable state
        cable: RigidObject = scene["cable"]
        pos = cable.data.root_pos_w[0]
        vel = cable.data.root_lin_vel_w[0]

        if step % 20 == 0:
            print(f"  Step {step:3d}: pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}), "
                  f"vel=({vel[0]:.3f}, {vel[1]:.3f}, {vel[2]:.3f})")

    # Final state
    final_pos = cable.data.root_pos_w[0]
    print(f"\n  Final position: ({final_pos[0]:.3f}, {final_pos[1]:.3f}, {final_pos[2]:.3f})")

    print("\n" + "=" * 60)
    print("[結果] テスト完了!")
    if final_pos[2] < 0.1:
        print("  ケーブルは重力で落下し、地面に到達しました。")
    else:
        print("  ケーブルはまだ落下中です。")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[エラー]: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulation_app.close()
