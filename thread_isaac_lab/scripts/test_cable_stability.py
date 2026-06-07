#!/usr/bin/env python3
"""
Cable Stability Test
====================

Tests SphericalJoint cable stability by running simulation and checking for NaN values.

Usage:
    # Test v2 (stabilized)
    CUDA_VISIBLE_DEVICES=1 python thread_isaac_lab/scripts/test_cable_stability.py --headless

    # Test v1 (original) for comparison
    CUDA_VISIBLE_DEVICES=1 python thread_isaac_lab/scripts/test_cable_stability.py --headless --v1

Author: THREAD Research Team
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Cable Stability Test")
parser.add_argument("--v1", action="store_true", help="Test v1 (original) cable")
parser.add_argument("--steps", type=int, default=1000, help="Number of simulation steps")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.assets import AssetBaseCfg


# Cable USD paths
V1_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable.usd"
V2_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v2.usd"


@configclass
class CableStabilitySceneCfg(InteractiveSceneCfg):
    """Scene configuration for cable stability test."""

    num_envs = 1
    env_spacing = 4.0

    ground: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    light: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/Light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0),
    )


def create_cable_config(usd_path: str) -> ArticulationCfg:
    """Create cable articulation config."""
    return ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=usd_path,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 1.5),  # Start high to test falling
            rot=(0.7071, 0.0, 0.7071, 0.0),  # Horizontal
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=0.1,
            ),
        },
    )


def check_nan(tensor: torch.Tensor, name: str) -> bool:
    """Check for NaN values in tensor."""
    if torch.isnan(tensor).any():
        print(f"  [ERROR] NaN detected in {name}!")
        return True
    if torch.isinf(tensor).any():
        print(f"  [ERROR] Inf detected in {name}!")
        return True
    return False


def main():
    print("\n" + "=" * 60)
    print("CABLE STABILITY TEST")
    print("=" * 60)

    # Select cable version
    if args_cli.v1:
        cable_usd = V1_USD
        version = "v1 (original)"
    else:
        cable_usd = V2_USD
        version = "v2 (stabilized)"

    print(f"  Version: {version}")
    print(f"  USD: {cable_usd}")
    print(f"  Steps: {args_cli.steps}")
    print()

    # Setup simulation with higher precision for stability
    sim_cfg = sim_utils.SimulationCfg(
        dt=1/240.0,  # 240Hz for stability
        device="cuda:0",
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.5, 1.0, 2.0), target=(0.0, 0.0, 1.0))

    # Create scene
    scene_cfg = CableStabilitySceneCfg()
    scene_cfg.cable = create_cable_config(cable_usd)
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    # Run simulation
    print("[Test] Running simulation...")
    nan_detected = False
    max_velocity = 0.0
    z_values = []

    cable: Articulation = scene["cable"]

    for step in range(args_cli.steps):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        # Check for NaN
        body_pos = cable.data.body_pos_w
        body_vel = cable.data.body_vel_w

        if check_nan(body_pos, f"body_pos (step {step})"):
            nan_detected = True
            break
        if check_nan(body_vel, f"body_vel (step {step})"):
            nan_detected = True
            break

        # Track max velocity
        vel_magnitude = torch.norm(body_vel[0, :, :3], dim=1).max().item()
        max_velocity = max(max_velocity, vel_magnitude)

        # Track z positions
        z_mean = body_pos[0, :, 2].mean().item()
        z_values.append(z_mean)

        # Progress report
        if step % 200 == 0:
            z_range = body_pos[0, :, 2].max().item() - body_pos[0, :, 2].min().item()
            print(f"  Step {step:4d}: z_mean={z_mean:.3f}, z_range={z_range:.3f}, vel={vel_magnitude:.3f}")

    # Final report
    print("\n" + "-" * 60)
    print("RESULTS:")
    print("-" * 60)

    if nan_detected:
        print(f"  Status: FAILED (NaN/Inf detected)")
        success = False
    else:
        print(f"  Status: STABLE (no NaN/Inf)")
        success = True

    print(f"  Max velocity: {max_velocity:.3f} m/s")
    print(f"  Final z_mean: {z_values[-1] if z_values else 'N/A':.3f} m")

    # Check if cable settled (not oscillating wildly)
    if len(z_values) > 100:
        z_std_last100 = np.std(z_values[-100:])
        print(f"  Z std (last 100 steps): {z_std_last100:.5f} m")
        if z_std_last100 < 0.01:
            print(f"  [OK] Cable settled (low oscillation)")
        else:
            print(f"  [WARN] Cable still oscillating")

    # Velocity check
    if max_velocity > 10.0:
        print(f"  [WARN] High max velocity (>10 m/s) - may be unstable")
    else:
        print(f"  [OK] Velocity reasonable (<10 m/s)")

    print("=" * 60)

    # Keep running for visual inspection
    if not args_cli.headless:
        print("\nSimulation running. Press Ctrl+C to exit.")
        try:
            while simulation_app.is_running():
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())
        except KeyboardInterrupt:
            pass

    simulation_app.close()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
