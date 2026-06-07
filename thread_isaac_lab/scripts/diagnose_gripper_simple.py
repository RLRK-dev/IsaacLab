#!/usr/bin/env python3
"""
簡易グリッパーフレーム診断（カメラなし）
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Simple gripper frame diagnosis")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.scene import InteractiveSceneCfg, InteractiveScene
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

FRANKA_USD = f"{ISAACLAB_NUCLEUS_DIR}/Robots/FrankaEmika/panda_instanceable.usd"


@configclass
class SimpleRobotSceneCfg(InteractiveSceneCfg):
    """Simple scene with just one Franka robot."""

    num_envs: int = 1
    env_spacing: float = 2.0

    robot = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=FRANKA_USD,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.0),
            rot=(1.0, 0.0, 0.0, 0.0),
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
                stiffness=400.0,
                damping=80.0,
            ),
            "panda_forearm": ImplicitActuatorCfg(
                joint_names_expr=["panda_joint[5-7]"],
                effort_limit_sim=12.0,
                stiffness=400.0,
                damping=80.0,
            ),
            "panda_hand": ImplicitActuatorCfg(
                joint_names_expr=["panda_finger_joint.*"],
                effort_limit_sim=200.0,
                stiffness=2000.0,
                damping=100.0,
            ),
        },
    )


def main():
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
    sim = sim_utils.SimulationContext(sim_cfg)

    scene_cfg = SimpleRobotSceneCfg()
    scene = InteractiveScene(scene_cfg)

    sim.reset()
    for _ in range(30):
        sim.step()
    scene.update(sim.get_physics_dt())

    robot = scene["robot"]

    print("\n" + "=" * 70)
    print("FRANKA PANDA GRIPPER FRAME DIAGNOSIS")
    print("=" * 70)

    # Body names
    print("\n[1] Body Names:")
    print("-" * 50)
    for i, name in enumerate(robot.body_names):
        print(f"  {i:2d}: {name}")

    # Body positions
    print("\n[2] Key Body Positions:")
    print("-" * 50)
    body_pos = robot.data.body_pos_w[0]

    key_bodies = ["panda_link7", "panda_link8", "panda_hand",
                  "panda_leftfinger", "panda_rightfinger"]

    indices = {}
    for name in key_bodies:
        if name in robot.body_names:
            idx = robot.body_names.index(name)
            indices[name] = idx
            pos = body_pos[idx]
            print(f"  {name:20s}: [{pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}]")

    # Offsets
    print("\n[3] Offsets from panda_hand:")
    print("-" * 50)

    if "panda_hand" in indices:
        hand_pos = body_pos[indices["panda_hand"]]
        hand_z = hand_pos[2].item()

        for name in ["panda_leftfinger", "panda_rightfinger"]:
            if name in indices:
                other_pos = body_pos[indices[name]]
                offset = other_pos - hand_pos
                print(f"  -> {name}:")
                print(f"     X: {offset[0]:.4f}m, Y: {offset[1]:.4f}m, Z: {offset[2]:.4f}m")
                print(f"     Distance: {torch.norm(offset).item():.4f}m")

    # Finger center
    print("\n[4] Finger Center (Clamp Position):")
    print("-" * 50)

    if "panda_leftfinger" in indices and "panda_rightfinger" in indices:
        left = body_pos[indices["panda_leftfinger"]]
        right = body_pos[indices["panda_rightfinger"]]
        center = (left + right) / 2

        print(f"  Left finger:  Z = {left[2]:.4f}m")
        print(f"  Right finger: Z = {right[2]:.4f}m")
        print(f"  Center:       Z = {center[2]:.4f}m")

        if "panda_hand" in indices:
            hand_z = body_pos[indices["panda_hand"]][2]
            z_offset = center[2] - hand_z
            print(f"\n  Z offset (panda_hand -> finger_center):")
            print(f"     {z_offset.item():.4f}m ({z_offset.item()*100:.2f}cm)")
            print(f"\n  Current FINGERTIP_OFFSET = 0.1123m (11.23cm)")

            if z_offset.item() < 0:
                print(f"  NOTE: Negative offset means fingers are BELOW panda_hand")
                print(f"  Recommended FINGERTIP_OFFSET: {abs(z_offset.item()):.4f}m")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70 + "\n")

    simulation_app.close()


if __name__ == "__main__":
    main()
