#!/usr/bin/env python3
"""
Test: Robot + Cable (single environment)
- Franka Panda + Cable + Ground
- num_envs = 1 (exclude replicate_physics issues)
- headless mode
- 100 simulation steps
"""

from __future__ import annotations
import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Robot + Cable test")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

print("=" * 60)
print("Test: Robot + Cable (Single Environment)")
print("=" * 60)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

print("Isaac Sim initialized!")

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import AssetBaseCfg, Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# Franka Panda USD path (Isaac Lab assets)
FRANKA_PANDA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"


@configclass
class RobotCableSceneCfg(InteractiveSceneCfg):
    """Scene with Franka Panda robot and cable."""

    num_envs: int = 1
    env_spacing: float = 2.0

    # Ground plane
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # Dome light
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=500.0),
    )

    # Franka Panda robot
    robot: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=FRANKA_PANDA_USD,
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=12,
                solver_velocity_iteration_count=1,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            joint_pos={
                "panda_joint1": 0.0,
                "panda_joint2": -0.569,
                "panda_joint3": 0.0,
                "panda_joint4": -2.810,
                "panda_joint5": 0.0,
                "panda_joint6": 3.037,
                "panda_joint7": 0.741,
                "panda_finger_joint1": 0.04,
                "panda_finger_joint2": 0.04,
            },
        ),
        actuators={
            "panda_shoulder": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[1-4]"],
                effort_limit_sim=87.0,
                stiffness=80.0,
                damping=4.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                effort_limit_sim=12.0,
                stiffness=80.0,
                damping=4.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                effort_limit_sim=200.0,
                stiffness=2000.0,
                damping=100.0,
            ),
        },
    )

    # Cable (simple cylinder)
    cable: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=sim_utils.CylinderCfg(
            radius=0.01,
            height=0.30,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=1.0,
            ),
            mass_props=sim_utils.MassPropertiesCfg(
                mass=0.05,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.2, 0.2, 0.8),
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.5, 0.0, 0.5),  # 50cm in front of robot
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
    sim.set_camera_view(eye=(2.5, 2.5, 2.0), target=(0.0, 0.0, 0.5))

    print("\n[2/3] Creating scene with robot + cable...")

    scene_cfg = RobotCableSceneCfg()
    scene = InteractiveScene(scene_cfg)

    print("\n[3/3] Running simulation for 100 steps...")

    # Reset
    sim.reset()
    scene.reset()

    for step in range(100):
        # Write data to sim
        scene.write_data_to_sim()
        # Step simulation
        sim.step()
        # Update scene
        scene.update(dt=sim.get_physics_dt())

        # Get states
        robot: Articulation = scene["robot"]
        cable: RigidObject = scene["cable"]

        robot_pos = robot.data.root_pos_w[0]
        cable_pos = cable.data.root_pos_w[0]
        joint_pos = robot.data.joint_pos[0, :7]  # First 7 joints (arm)

        if step % 20 == 0:
            print(f"  Step {step:3d}:")
            print(f"    Robot base: ({robot_pos[0]:.3f}, {robot_pos[1]:.3f}, {robot_pos[2]:.3f})")
            print(f"    Cable pos:  ({cable_pos[0]:.3f}, {cable_pos[1]:.3f}, {cable_pos[2]:.3f})")
            print(f"    Joint[0-2]: ({joint_pos[0]:.3f}, {joint_pos[1]:.3f}, {joint_pos[2]:.3f})")

    print("\n" + "=" * 60)
    print("[結果] テスト完了!")
    print(f"  ロボット最終位置: ({robot_pos[0]:.3f}, {robot_pos[1]:.3f}, {robot_pos[2]:.3f})")
    print(f"  ケーブル最終位置: ({cable_pos[0]:.3f}, {cable_pos[1]:.3f}, {cable_pos[2]:.3f})")
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
