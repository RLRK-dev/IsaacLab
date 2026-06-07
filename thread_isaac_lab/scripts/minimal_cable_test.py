#!/usr/bin/env python3
"""Minimal cable test without cameras."""
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher
import argparse
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveSceneCfg, InteractiveScene
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg

# Use SphericalJoint cable v2 (stabilized: heavier mass, reduced cone angle)
USD_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v2.usd"
# Old revolute cable for comparison:
# USD_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/segmented_cable.usd"

# Minimal scene with just cable
@configclass
class MinimalSceneCfg(InteractiveSceneCfg):
    num_envs = 1
    env_spacing = 4.0

    # Ground plane (as AssetBaseCfg)
    ground: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    # Cable only - using USD file
    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=USD_PATH,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 1.0),  # 1m above ground
            rot=(0.7071, -0.7071, 0.0, 0.0),
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],  # Match all joints
                stiffness=0.0,
                damping=0.1,  # Low damping for flexibility
            ),
        },
    )


def main():
    print("\n" + "="*60)
    print("MINIMAL CABLE TEST (USD)")
    print("="*60)
    print(f"USD path: {USD_PATH}")

    scene_cfg = MinimalSceneCfg()
    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Run simulation for 300 steps (5 seconds at 60Hz)
    print("\nRunning 300 steps to let cable settle...")
    for step in range(300):
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % 50 == 0:
            cable = scene["cable"]
            try:
                body_pos = cable.data.body_pos_w[0]
                z_min = body_pos[:, 2].min().item()
                z_max = body_pos[:, 2].max().item()
                print(f"  Step {step}: z_range = {z_max - z_min:.4f}m (min={z_min:.3f}, max={z_max:.3f})")
            except Exception as e:
                print(f"  Step {step}: Error - {e}")

    print("\n--- CABLE DATA ---")
    cable = scene["cable"]
    print(f"Cable type: {type(cable).__name__}")

    try:
        body_pos = cable.data.body_pos_w[0]
        print(f"Number of bodies: {body_pos.shape[0]}")
        for i in range(min(10, body_pos.shape[0])):
            p = body_pos[i].cpu().tolist()
            print(f"  Body {i}: x={p[0]:.4f}, y={p[1]:.4f}, z={p[2]:.4f}")
    except Exception as e:
        print(f"Error accessing body_pos: {e}")
        import traceback
        traceback.print_exc()

    try:
        root_pos = cable.data.root_pos_w[0].cpu().tolist()
        print(f"\nRoot position: x={root_pos[0]:.4f}, y={root_pos[1]:.4f}, z={root_pos[2]:.4f}")
    except Exception as e:
        print(f"Error accessing root_pos: {e}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    simulation_app.close()


if __name__ == "__main__":
    main()
