"""カメラ画像確認スクリプト - シンプル版"""
import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from envs.dual_arm_cfg import DualArmSceneCfg

def main():
    print("[INFO] Creating simulation context...")
    sim_cfg = sim_utils.SimulationCfg(dt=0.01)
    sim = sim_utils.SimulationContext(sim_cfg)
    print("[INFO] Simulation context created")

    print("[INFO] Creating scene...")
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)
    print("[INFO] Scene created")

    print("[INFO] Resetting simulation...")
    sim.reset()
    print("[INFO] Simulation reset complete")

    # 数ステップ実行してカメラを安定化
    print("[INFO] Running 10 steps to stabilize...")
    for i in range(10):
        sim.step()
        scene.update(sim.get_physics_dt())
        print(f"  Step {i+1}/10")
    print("[INFO] Stabilization complete")

    # 各カメラの画像を取得
    cameras = ['front_camera', 'left_back_camera', 'right_back_camera']

    for cam_name in cameras:
        if hasattr(scene, cam_name):
            print(f"[INFO] Processing {cam_name}...")
            cam = getattr(scene, cam_name)
            cam.update(sim.get_physics_dt())

            if "rgb" in cam.data.output:
                img = cam.data.output["rgb"][0].cpu().numpy()
                Image.fromarray(img[:,:,:3].astype(np.uint8)).save(f'/tmp/{cam_name}.png')
                print(f"  Saved /tmp/{cam_name}.png - shape: {img.shape}")
            else:
                print(f"  Warning: No RGB output for {cam_name}")
        else:
            print(f"  Warning: {cam_name} not found in scene")

    print("[INFO] Closing simulation...")
    simulation_app.close()
    print("[INFO] Done")

if __name__ == "__main__":
    main()
