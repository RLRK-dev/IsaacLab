#!/usr/bin/env python3
"""
4カメラ画像キャプチャスクリプト
front_left, front_right, back, overhead の4カメラ画像を保存
"""
import argparse
import os
import sys
import traceback

# Unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

def log(msg):
    print(msg, flush=True)

# Parse args before importing Isaac Lab
parser = argparse.ArgumentParser()
parser.add_argument("--output_dir", type=str, default="/home/rlrk/IsaacLab/claude_code")
parser.add_argument("--headless", action="store_true", default=True)
args, _ = parser.parse_known_args()

log(f"[START] capture_4cam_images.py")
log(f"[ARGS] output_dir={args.output_dir}, headless={args.headless}")

try:
    # Isaac Lab setup
    log("[IMPORT] Importing Isaac Lab...")
    from isaaclab.app import AppLauncher
    app_launcher = AppLauncher(headless=args.headless, enable_cameras=True)
    simulation_app = app_launcher.app
    log("[IMPORT] Isaac Lab imported successfully")

    import torch
    import numpy as np
    from PIL import Image
    import isaaclab.sim as sim_utils
    from isaaclab.scene import InteractiveScene

    sys.path.insert(0, os.path.expanduser("~/IsaacLab/thread_isaac_lab"))
    from envs.dual_arm_cfg import DualArmSceneCfg

    def main():
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
        log(f"[Output] {output_dir}")

        # Setup scene
        log("[Setup] Creating scene...")
        scene_cfg = DualArmSceneCfg()
        scene_cfg.num_envs = 1

        sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
        sim = sim_utils.SimulationContext(sim_cfg)
        sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])
        log("[Setup] SimulationContext created")

        scene = InteractiveScene(scene_cfg)
        log("[Setup] InteractiveScene created")
        sim.reset()
        log("[Setup] Simulation reset")

        # Apply grid texture to table
        try:
            from scripts.apply_table_texture import apply_grid_texture_to_table
            import omni.usd
            stage = omni.usd.get_context().get_stage()
            table_prim_path = "/World/envs/env_0/Table"
            apply_grid_texture_to_table(stage, table_prim_path)
            log("[Setup] Grid texture applied to table")
        except Exception as e:
            log(f"[WARN] Could not apply texture: {e}")

        # Let physics settle
        log("[Sim] Running 60 simulation steps...")
        for i in range(60):
            sim.step()
            if i % 20 == 0:
                log(f"  step {i}/60")
        scene.update(dt=sim.get_physics_dt())
        log("[Sim] Scene updated")

        # Debug: List all scene attributes
        log("[Debug] Scene attributes:")
        scene_attrs = [attr for attr in dir(scene) if not attr.startswith('_')]
        camera_attrs = [attr for attr in scene_attrs if 'camera' in attr.lower()]
        log(f"  Camera-related: {camera_attrs}")
        log(f"  All attrs count: {len(scene_attrs)}")

        # Also check the scene's sensors dict
        if hasattr(scene, '_sensors'):
            log(f"  Sensors dict: {list(scene._sensors.keys())}")

        # Capture cameras - access via scene._sensors dict
        log("[Capture] Capturing 4-camera images...")
        camera_names = ['front_left', 'front_right', 'back', 'overhead']
        images = []

        for cam_name in camera_names:
            camera_attr = f'{cam_name}_camera'
            log(f"  [CHECK] Looking for {camera_attr}...")

            # Try to access via _sensors dict
            camera = None
            if hasattr(scene, '_sensors') and camera_attr in scene._sensors:
                camera = scene._sensors[camera_attr]
                log(f"    [FOUND] {camera_attr} in _sensors")
            elif hasattr(scene, camera_attr):
                camera = getattr(scene, camera_attr)
                log(f"    [FOUND] {camera_attr} as attribute")
            else:
                # Try using scene[key] accessor
                try:
                    camera = scene[camera_attr]
                    log(f"    [FOUND] {camera_attr} via scene[key]")
                except (KeyError, TypeError):
                    pass

            if camera is not None:
                rgb_data = camera.data.output.get('rgb', None)

                if rgb_data is not None and len(rgb_data) > 0:
                    img_np = rgb_data[0].cpu().numpy()
                    log(f"    [DATA] shape={img_np.shape}, dtype={img_np.dtype}")
                    if img_np.dtype != np.uint8:
                        if img_np.max() <= 1.0:
                            img_np = (img_np * 255).astype(np.uint8)
                        else:
                            img_np = img_np.astype(np.uint8)
                    if img_np.shape[-1] == 4:
                        img_np = img_np[:, :, :3]

                    img_path = os.path.join(output_dir, f'4cam_{cam_name}.png')
                    Image.fromarray(img_np).save(img_path)
                    images.append(img_np)
                    log(f'  [OK] {cam_name}: {img_np.shape} -> {img_path}')
                else:
                    log(f'  [WARN] {cam_name}: No RGB data available')
            else:
                log(f'  [WARN] {camera_attr} not found in scene')

        # Create combined 2x2 view
        if len(images) == 4:
            top_row = np.concatenate([images[0], images[1]], axis=1)
            bottom_row = np.concatenate([images[2], images[3]], axis=1)
            combined = np.concatenate([top_row, bottom_row], axis=0)
            combined_path = os.path.join(output_dir, '4cam_combined.png')
            Image.fromarray(combined).save(combined_path)
            log(f'[Combined] {combined_path}')
            log('')
            log('Layout:')
            log('  +-------------+-------------+')
            log('  | front_left  | front_right |')
            log('  +-------------+-------------+')
            log('  |    back     |  overhead   |')
            log('  +-------------+-------------+')
        else:
            log(f'[WARN] Only captured {len(images)} images, expected 4')

        log(f'\n[Done] Images saved to {output_dir}')
        simulation_app.close()

    main()

except Exception as e:
    log(f"[ERROR] Exception occurred: {e}")
    log(traceback.format_exc())
    sys.exit(1)
