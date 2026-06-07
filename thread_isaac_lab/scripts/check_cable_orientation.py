#!/usr/bin/env python3
"""Check cable USD native orientation without any rotation applied."""

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=True)
args, _ = parser.parse_known_args()

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=True)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext, SimulationCfg
from isaaclab.assets import ArticulationCfg, Articulation
from isaaclab.actuators import ImplicitActuatorCfg
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Cable USD path
CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v5.usd"
TABLE_HEIGHT = 0.75

def main():
    # Create simulation
    sim_cfg = SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = SimulationContext(sim_cfg)

    # Spawn ground plane
    cfg = sim_utils.GroundPlaneCfg()
    cfg.func("/World/Ground", cfg)

    # Spawn cable with no rotation
    cable_cfg = ArticulationCfg(
        prim_path="/World/Cable",
        spawn=sim_utils.UsdFileCfg(
            usd_path=CABLE_USD,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                rigid_body_enabled=True,
                max_linear_velocity=1.0,
                max_angular_velocity=1.0,
                max_depenetration_velocity=1.0,
                linear_damping=10.0,
                angular_damping=10.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=64,
                solver_velocity_iteration_count=16,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.40, 0.0, TABLE_HEIGHT + 0.02),
            rot=(1.0, 0.0, 0.0, 0.0),  # No rotation
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=1.0,
            ),
        },
    )

    cable = Articulation(cable_cfg)

    # Reset simulation
    sim.reset()
    cable.reset()

    # Run a few simulation steps to let physics settle
    print("\n[Setup] Running 120 simulation steps to settle physics...")
    for _ in range(120):
        cable.write_data_to_sim()
        sim.step()
        cable.update(sim.cfg.dt)

    # Get cable segment positions
    cable_pos = cable.data.body_pos_w[0]  # Shape: [20, 3]

    print("\n" + "=" * 60)
    print("Cable Segment Positions (No Rotation Applied)")
    print("=" * 60)
    print(f"Cable spawn position: X=0.40, Y=0.00, Z={TABLE_HEIGHT + 0.02:.2f}")
    print(f"Cable rotation: (1.0, 0.0, 0.0, 0.0) - Identity (no rotation)")
    print("-" * 60)

    # Find min/max for each axis
    x_coords = cable_pos[:, 0].cpu().numpy()
    y_coords = cable_pos[:, 1].cpu().numpy()
    z_coords = cable_pos[:, 2].cpu().numpy()

    print(f"\nAxis Ranges:")
    print(f"  X: min={x_coords.min():.3f}, max={x_coords.max():.3f}, span={x_coords.max()-x_coords.min():.3f}m")
    print(f"  Y: min={y_coords.min():.3f}, max={y_coords.max():.3f}, span={y_coords.max()-y_coords.min():.3f}m")
    print(f"  Z: min={z_coords.min():.3f}, max={z_coords.max():.3f}, span={z_coords.max()-z_coords.min():.3f}m")

    # Determine cable direction
    x_span = x_coords.max() - x_coords.min()
    y_span = y_coords.max() - y_coords.min()
    z_span = z_coords.max() - z_coords.min()

    print("\n" + "-" * 60)
    if x_span > y_span and x_span > z_span:
        print("CABLE DIRECTION: X-axis (horizontal, along table depth)")
    elif y_span > x_span and y_span > z_span:
        print("CABLE DIRECTION: Y-axis (horizontal, along table width)")
    elif z_span > x_span and z_span > y_span:
        print("CABLE DIRECTION: Z-axis (vertical)")
    else:
        print("CABLE DIRECTION: Diagonal or Unknown")
    print("-" * 60)

    # Print all segment positions
    print("\nAll Segment Positions:")
    for i in range(20):
        pos = cable_pos[i].cpu().numpy()
        y_sign = "+" if pos[1] >= 0 else ""
        print(f"  seg_{i:02d}: X={pos[0]:.4f}, Y={y_sign}{pos[1]:.4f}, Z={pos[2]:.4f}")

    # Key segments for grasping
    print("\n" + "-" * 60)
    print("Key Segments for Grasping:")
    seg17 = cable_pos[17].cpu().numpy()
    seg19 = cable_pos[19].cpu().numpy()
    print(f"  seg_17: X={seg17[0]:.4f}, Y={seg17[1]:.4f}, Z={seg17[2]:.4f}")
    print(f"  seg_19: X={seg19[0]:.4f}, Y={seg19[1]:.4f}, Z={seg19[2]:.4f}")

    # Y-sign analysis
    print("\n" + "-" * 60)
    print("Y-coordinate Sign Analysis:")
    y_positive = [i for i in range(20) if cable_pos[i, 1].item() > 0.01]
    y_negative = [i for i in range(20) if cable_pos[i, 1].item() < -0.01]
    y_center = [i for i in range(20) if abs(cable_pos[i, 1].item()) <= 0.01]

    print(f"  Y > 0 (positive): seg_{y_positive}" if y_positive else "  Y > 0 (positive): None")
    print(f"  Y < 0 (negative): seg_{y_negative}" if y_negative else "  Y < 0 (negative): None")
    print(f"  Y ≈ 0 (center):   seg_{y_center}" if y_center else "  Y ≈ 0 (center): None")

    print("\n" + "=" * 60)
    print("End of Cable Orientation Check")
    print("=" * 60 + "\n")

    # Cleanup
    simulation_app.close()

if __name__ == "__main__":
    main()
