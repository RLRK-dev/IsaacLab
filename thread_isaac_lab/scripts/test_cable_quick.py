#!/usr/bin/env python3
"""Quick cable test to diagnose NaN issue."""
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

# Use segmented cable (Revolute joints)
USD_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/segmented_cable.usd"
TABLE_HEIGHT = 0.75

@configclass
class QuickTestSceneCfg(InteractiveSceneCfg):
    num_envs = 1
    env_spacing = 4.0

    ground: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    cable: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cable",
        spawn=UsdFileCfg(
            usd_path=USD_PATH,
            activate_contact_sensors=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.60, -0.15, TABLE_HEIGHT + 0.02),  # Same as dual_arm_cfg
            rot=(0.7071, -0.7071, 0.0, 0.0),
        ),
        actuators={
            "cable_joints": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=0.0,
                damping=0.1,
            ),
        },
    )


def main():
    print("\n" + "="*60)
    print("QUICK CABLE TEST (segmented_cable.usd)")
    print("="*60)
    print(f"USD path: {USD_PATH}")
    print(f"Initial pos: (0.60, -0.15, {TABLE_HEIGHT + 0.02:.2f})")

    scene_cfg = QuickTestSceneCfg()
    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    print("\nRunning 100 steps to let cable settle...")
    for step in range(100):
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % 20 == 0:
            cable = scene["cable"]
            try:
                body_pos = cable.data.body_pos_w[0]
                seg_0 = body_pos[0].cpu().tolist()
                seg_9 = body_pos[9].cpu().tolist()
                print(f"  Step {step}: seg_0={seg_0}, seg_9={seg_9}")
                if any(str(v) == 'nan' for v in seg_0 + seg_9):
                    print("  ERROR: NaN detected!")
                    break
            except Exception as e:
                print(f"  Step {step}: Error - {e}")

    print("\n--- FINAL CABLE STATE ---")
    cable = scene["cable"]
    body_pos = cable.data.body_pos_w[0]
    for i in range(min(10, body_pos.shape[0])):
        p = body_pos[i].cpu().tolist()
        print(f"  seg_{i}: ({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f})")

    simulation_app.close()


if __name__ == "__main__":
    main()
