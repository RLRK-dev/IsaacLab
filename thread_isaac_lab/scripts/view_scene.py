#!/usr/bin/env python3
"""View dual arm scene with better camera angle."""
import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from envs.dual_arm_cfg import DualArmSceneCfg

def main():
    # Setup
    cfg = DualArmSceneCfg()
    cfg.num_envs = 1

    # Remove cameras
    delattr(cfg, 'overhead_camera')
    delattr(cfg, 'left_wrist_camera')
    delattr(cfg, 'right_wrist_camera')

    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=1/60)
    sim = sim_utils.SimulationContext(sim_cfg)

    # Camera looking at scene from side-top (to see robots and table)
    sim.set_camera_view(
        eye=(0.3, -1.5, 1.5),     # Side view (Y negative, elevated)
        target=(0.2, 0.0, 0.5)    # Look at center of workspace
    )

    scene = InteractiveScene(cfg)
    sim.reset()

    print("\n" + "="*50)
    print("SCENE LOADED")
    print("Hook: (0.5, 0, 0.9) - gray cylinder")
    print("Cable: (0.45, 0, 0.765) - blue cylinder")
    print("="*50)
    print("\nGUI Controls:")
    print("  Alt + Left drag: Rotate")
    print("  Alt + Right drag: Zoom")
    print("  Alt + Middle drag: Pan")
    print("\nPress Ctrl+C to exit")
    print("="*50 + "\n")

    while simulation_app.is_running():
        sim.step()

if __name__ == "__main__":
    main()
    simulation_app.close()
