#!/usr/bin/env python3
"""Check asset positions in dual arm scene."""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT
from thread_isaac_lab.configs.task_config import PHYSICS_DT

def main():
    device = torch.device("cuda:0")

    cfg = DualArmSceneCfg()
    cfg.num_envs = 1
    cfg.env_spacing = 3.0

    # Remove cameras
    delattr(cfg, 'overhead_camera')
    delattr(cfg, 'left_wrist_camera')
    delattr(cfg, 'right_wrist_camera')

    sim_cfg = sim_utils.SimulationCfg(device=str(device), dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)

    print("\n[Status] Creating scene...")
    scene = InteractiveScene(cfg)

    print("[Status] Starting simulation...")
    sim.reset()

    # Step a few times to let physics settle
    for _ in range(60):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get positions
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    hook = scene["hook"]
    cable = scene["cable"]
    table = scene["table"]

    left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
    right_ee_pos = robot_right.data.body_pos_w[:, 8, :]
    left_base_pos = robot_left.data.root_pos_w
    right_base_pos = robot_right.data.root_pos_w
    hook_pos = hook.data.root_pos_w
    cable_pos = cable.data.root_pos_w
    table_pos = table.data.root_pos_w

    print("\n" + "=" * 60)
    print("ASSET POSITIONS (after physics settle)")
    print("=" * 60)

    print(f"\n[Config Values]")
    print(f"  TABLE_HEIGHT: {TABLE_HEIGHT}")

    print(f"\n[Robot Bases]")
    print(f"  Left arm base:  ({left_base_pos[0,0]:.3f}, {left_base_pos[0,1]:.3f}, {left_base_pos[0,2]:.3f})")
    print(f"  Right arm base: ({right_base_pos[0,0]:.3f}, {right_base_pos[0,1]:.3f}, {right_base_pos[0,2]:.3f})")

    print(f"\n[End Effectors]")
    print(f"  Left EE:  ({left_ee_pos[0,0]:.3f}, {left_ee_pos[0,1]:.3f}, {left_ee_pos[0,2]:.3f})")
    print(f"  Right EE: ({right_ee_pos[0,0]:.3f}, {right_ee_pos[0,1]:.3f}, {right_ee_pos[0,2]:.3f})")

    print(f"\n[Objects]")
    print(f"  Table:  ({table_pos[0,0]:.3f}, {table_pos[0,1]:.3f}, {table_pos[0,2]:.3f})")
    print(f"  Cable:  ({cable_pos[0,0]:.3f}, {cable_pos[0,1]:.3f}, {cable_pos[0,2]:.3f})")
    print(f"  Hook:   ({hook_pos[0,0]:.3f}, {hook_pos[0,1]:.3f}, {hook_pos[0,2]:.3f})")

    print(f"\n[Distances]")
    left_to_cable = torch.norm(left_ee_pos - cable_pos, dim=-1).item()
    right_to_cable = torch.norm(right_ee_pos - cable_pos, dim=-1).item()
    cable_to_hook = torch.norm(cable_pos - hook_pos, dim=-1).item()
    ee_separation = torch.norm(left_ee_pos - right_ee_pos, dim=-1).item()

    print(f"  Left EE to Cable:  {left_to_cable:.3f} m")
    print(f"  Right EE to Cable: {right_to_cable:.3f} m")
    print(f"  Cable to Hook:     {cable_to_hook:.3f} m")
    print(f"  EE Separation:     {ee_separation:.3f} m")

    print(f"\n[Height Analysis]")
    print(f"  Table surface:    Z = {table_pos[0,2].item():.3f}")
    print(f"  Cable position:   Z = {cable_pos[0,2].item():.3f}")
    print(f"  Hook position:    Z = {hook_pos[0,2].item():.3f}")
    print(f"  Left EE height:   Z = {left_ee_pos[0,2].item():.3f}")
    print(f"  Right EE height:  Z = {right_ee_pos[0,2].item():.3f}")

    cable_above_table = cable_pos[0,2].item() - table_pos[0,2].item()
    print(f"\n  Cable above table: {cable_above_table:.3f} m")
    if cable_above_table < 0:
        print("  ⚠️  WARNING: Cable is BELOW table surface!")
    elif cable_above_table < 0.02:
        print("  ⚠️  WARNING: Cable may be resting on/through table!")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
    simulation_app.close()
