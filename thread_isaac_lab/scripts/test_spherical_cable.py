#!/usr/bin/env python3
"""
Test SphericalJoint Cable Flexibility
======================================

Tests that the new SphericalJoint cable bends properly under gravity.
Compares with the old revolute joint cable if requested.
"""
import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test SphericalJoint Cable")
parser.add_argument("--old", action="store_true", help="Use old revolute joint cable")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Cable paths
SPHERICAL_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v2.usd"
OLD_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/segmented_cable.usd"
V1_CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable.usd"


@configclass
class CableTestSceneCfg(InteractiveSceneCfg):
    """Scene configuration for cable test."""

    num_envs = 1
    env_spacing = 4.0

    # Ground plane
    ground: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    # Light
    light: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(1.0, 1.0, 1.0)),
    )

    # Table
    table: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.CuboidCfg(
            size=(0.8, 0.6, 0.02),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.7, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.4, 0.0, 0.74)),
    )


def create_cable_config(usd_path: str, start_height: float = 1.0) -> ArticulationCfg:
    """Create cable articulation config."""
    return ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=usd_path,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            # Start above table, horizontal orientation
            pos=(0.4, 0.0, start_height),
            rot=(0.7071, 0.0, 0.7071, 0.0),  # Rotate to lie horizontal
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=0.1,
            ),
        },
    )


def measure_curvature(body_positions: torch.Tensor) -> dict:
    """
    Measure cable curvature from body positions.

    Returns:
        dict with curvature metrics
    """
    # Get positions
    positions = body_positions[0].cpu().numpy()  # [num_bodies, 3]
    num_bodies = positions.shape[0]

    if num_bodies < 3:
        return {"error": "Not enough bodies"}

    # Z-height variation (indicator of bending)
    z_values = positions[:, 2]
    z_range = z_values.max() - z_values.min()

    # Calculate angles between consecutive segments
    angles = []
    for i in range(1, num_bodies - 1):
        v1 = positions[i] - positions[i-1]
        v2 = positions[i+1] - positions[i]

        # Normalize
        v1_norm = v1 / (torch.norm(torch.tensor(v1)) + 1e-6)
        v2_norm = v2 / (torch.norm(torch.tensor(v2)) + 1e-6)

        # Angle in degrees
        cos_angle = max(-1, min(1, (v1_norm * v2_norm).sum()))
        angle = torch.acos(torch.tensor(cos_angle)) * 180 / 3.14159
        angles.append(float(angle))

    max_angle = max(angles) if angles else 0
    avg_angle = sum(angles) / len(angles) if angles else 0

    return {
        "z_range": float(z_range),
        "max_angle": max_angle,
        "avg_angle": avg_angle,
        "num_bodies": num_bodies,
    }


def main():
    print("\n" + "=" * 60)
    print("SPHERICAL CABLE FLEXIBILITY TEST")
    print("=" * 60)

    # Select cable USD
    if args_cli.old:
        cable_usd = OLD_CABLE_USD
        cable_type = "OLD (Revolute)"
    else:
        cable_usd = SPHERICAL_CABLE_USD
        cable_type = "NEW (SphericalJoint)"

    print(f"\nCable type: {cable_type}")
    print(f"USD: {cable_usd}")

    # Create scene config
    scene_cfg = CableTestSceneCfg()
    scene_cfg.cable = create_cable_config(cable_usd, start_height=1.2)

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.5, 1.0, 1.5), target=(0.4, 0.0, 0.8))

    # Create scene
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    print("\n[Test] Running 600 steps (5 seconds)...")
    print("       Cable starts at z=1.2m, should fall and bend under gravity")

    # Run simulation
    for step in range(600):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        cable: Articulation = scene["cable"]

        if step % 100 == 0:
            try:
                body_pos = cable.data.body_pos_w
                metrics = measure_curvature(body_pos)

                first_z = body_pos[0, 0, 2].item()
                last_z = body_pos[0, -1, 2].item()

                print(f"  Step {step:3d}: first_z={first_z:.3f}, last_z={last_z:.3f}, "
                      f"z_range={metrics['z_range']:.3f}m, max_angle={metrics['max_angle']:.1f}°")
            except Exception as e:
                print(f"  Step {step:3d}: Error measuring - {e}")

    # Final measurement
    print("\n" + "-" * 60)
    print("FINAL RESULTS:")
    print("-" * 60)

    try:
        body_pos = cable.data.body_pos_w
        metrics = measure_curvature(body_pos)

        print(f"  Number of bodies: {metrics['num_bodies']}")
        print(f"  Z height range: {metrics['z_range']:.4f} m")
        print(f"  Max joint angle: {metrics['max_angle']:.2f}°")
        print(f"  Avg joint angle: {metrics['avg_angle']:.2f}°")

        # Flexibility assessment
        if metrics['z_range'] > 0.05:
            print(f"\n  [OK] Cable is FLEXIBLE (z_range > 5cm)")
            flexible = True
        else:
            print(f"\n  [WARN] Cable appears RIGID (z_range < 5cm)")
            flexible = False

        if metrics['max_angle'] > 10:
            print(f"  [OK] Joints are bending (max_angle > 10°)")
        else:
            print(f"  [WARN] Joints barely bending (max_angle < 10°)")

    except Exception as e:
        print(f"  Error in final measurement: {e}")
        flexible = False

    print("\n" + "=" * 60)

    # Keep running for visual inspection if not headless
    if not args_cli.headless:
        print("Simulation running. Press Ctrl+C to exit.")
        try:
            while simulation_app.is_running():
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())
        except KeyboardInterrupt:
            pass

    simulation_app.close()
    return flexible


if __name__ == "__main__":
    main()
