#!/usr/bin/env python3
"""
Test Flexible Cable and L-Shape Hook
=====================================

Visualizes the segmented flexible cable and L-shape hook.
"""
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
from isaaclab.assets import RigidObject, RigidObjectCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Cable parameters
NUM_SEGMENTS = 10
SEGMENT_LENGTH = 0.03
SEGMENT_RADIUS = 0.006
SEGMENT_MASS = 0.003


@configclass
class FlexibleCableSceneCfg(InteractiveSceneCfg):
    """Scene with flexible cable segments and L-hook"""

    num_envs = 1
    env_spacing = 3.0


def create_cable_segments(scene_cfg):
    """Add cable segment configurations to scene"""
    for i in range(NUM_SEGMENTS):
        seg_name = f"cable_seg_{i:02d}"
        x_pos = 0.3 + i * SEGMENT_LENGTH

        setattr(scene_cfg, seg_name, RigidObjectCfg(
            prim_path=f"{{ENV_REGEX_NS}}/{seg_name}",
            spawn=sim_utils.CapsuleCfg(
                radius=SEGMENT_RADIUS,
                height=SEGMENT_LENGTH,
                axis="X",
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=False,
                    linear_damping=0.5,
                    angular_damping=0.5,
                ),
                mass_props=sim_utils.MassPropertiesCfg(mass=SEGMENT_MASS),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(1.0, 0.4, 0.0),  # Orange
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(x_pos, 0.0, 0.5),
            ),
        ))

    return scene_cfg


def create_l_hook(scene_cfg):
    """Add L-shape hook to scene"""
    HOOK_VERTICAL = 0.08
    HOOK_HORIZONTAL = 0.04
    HOOK_RADIUS = 0.005

    # Vertical part
    setattr(scene_cfg, "hook_vertical", RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/hook_vertical",
        spawn=sim_utils.CylinderCfg(
            radius=HOOK_RADIUS,
            height=HOOK_VERTICAL,
            axis="Z",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=True,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.2, 0.4, 0.8),  # Blue
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.7, 0.0, 0.5 + HOOK_VERTICAL/2),
        ),
    ))

    # Horizontal part
    setattr(scene_cfg, "hook_horizontal", RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/hook_horizontal",
        spawn=sim_utils.CylinderCfg(
            radius=HOOK_RADIUS,
            height=HOOK_HORIZONTAL,
            axis="Y",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=True,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.2, 0.4, 0.8),  # Blue
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.7, 0.0, 0.5 + HOOK_VERTICAL),
        ),
    ))

    return scene_cfg


def main():
    import sys
    print("\n" + "="*50, flush=True)
    print("FLEXIBLE CABLE & L-HOOK TEST", flush=True)
    print("="*50, flush=True)

    # Setup simulation
    print("\n[Status] Setting up simulation...", flush=True)
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(1.0, -0.5, 1.0),
        target=(0.5, 0.0, 0.5)
    )
    print("[Status] Simulation context created", flush=True)

    # Spawn ground plane manually
    print("[Status] Spawning ground plane...", flush=True)
    ground_cfg = sim_utils.GroundPlaneCfg(size=(10.0, 10.0))
    ground_cfg.func("/World/ground", ground_cfg)
    print("[Status] Ground plane spawned", flush=True)

    # Spawn dome light manually
    print("[Status] Spawning dome light...", flush=True)
    light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(1.0, 1.0, 1.0))
    light_cfg.func("/World/dome_light", light_cfg)
    print("[Status] Dome light spawned", flush=True)

    # Create scene config
    cfg = FlexibleCableSceneCfg()
    cfg = create_cable_segments(cfg)
    cfg = create_l_hook(cfg)

    print("[Status] Creating scene...", flush=True)
    scene = InteractiveScene(cfg)
    print("[Status] Scene created", flush=True)

    print("[Status] Starting simulation...", flush=True)
    sim.reset()
    print("[Status] Simulation started!", flush=True)

    print(f"\n[Cable] {NUM_SEGMENTS} segments", flush=True)
    print(f"  Total length: {NUM_SEGMENTS * SEGMENT_LENGTH * 100:.0f} cm", flush=True)
    print(f"  Segment radius: {SEGMENT_RADIUS * 1000:.0f} mm", flush=True)

    print("\n[Hook] L-shape", flush=True)
    print("  Vertical: 8 cm", flush=True)
    print("  Horizontal: 4 cm", flush=True)

    print("\n" + "="*50, flush=True)
    print("Simulation running. Press Ctrl+C to exit.", flush=True)
    print("="*50 + "\n", flush=True)

    step = 0
    while simulation_app.is_running():
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        step += 1
        if step % 500 == 0:
            # Print cable segment positions
            seg0 = scene["cable_seg_00"]
            seg9 = scene["cable_seg_09"]
            pos0 = seg0.data.root_pos_w[0].cpu().numpy()
            pos9 = seg9.data.root_pos_w[0].cpu().numpy()
            print(f"[Step {step}] Seg0: ({pos0[0]:.3f}, {pos0[1]:.3f}, {pos0[2]:.3f})", flush=True)
            print(f"          Seg9: ({pos9[0]:.3f}, {pos9[1]:.3f}, {pos9[2]:.3f})", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
