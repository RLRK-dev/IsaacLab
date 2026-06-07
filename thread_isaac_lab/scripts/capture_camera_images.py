#!/usr/bin/env python3
"""
Camera Image Capture Script for THREAD Dual Arm Environment

Captures images from all 4 cameras (front_left, front_right, back, overhead)
and saves them for verification.

Usage:
    ./isaaclab.sh -p scripts/capture_camera_images.py \
        --output_dir training_debug/camera_check_4cam
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import numpy as np
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(description="Capture camera images from dual arm environment")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="training_debug/camera_check_4cam",
        help="Output directory for captured images",
    )
    parser.add_argument(
        "--num_envs",
        type=int,
        default=1,
        help="Number of environments",
    )
    parser.add_argument(
        "--num_frames",
        type=int,
        default=5,
        help="Number of frames to capture",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Output] Saving images to: {output_dir}")

    # Import Isaac Lab modules after parsing args to avoid isaacsim initialization issues
    from omni.isaac.lab.app import AppLauncher

    # Launch the simulator
    app_launcher = AppLauncher(headless=True)
    simulation_app = app_launcher.app

    # Import after launching
    import omni.isaac.lab.sim as sim_utils
    from omni.isaac.lab.scene import InteractiveScene

    # Import our configuration
    from envs.dual_arm_cfg import DualArmSceneCfg

    # Create scene configuration
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = args.num_envs

    # Set up simulation context
    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

    # Create scene
    print("[Scene] Creating dual arm scene...")
    scene = InteractiveScene(scene_cfg)

    # Reset simulation
    sim.reset()

    # Camera names
    camera_names = ["front_left", "front_right", "back", "overhead"]

    print(f"[Capture] Starting capture of {args.num_frames} frames...")

    for frame_idx in range(args.num_frames):
        # Step simulation
        for _ in range(10):  # Let physics settle
            sim.step()

        # Update scene
        scene.update(dt=sim.get_physics_dt())

        # Capture from each camera
        for cam_name in camera_names:
            camera_attr = f"{cam_name}_camera"
            if hasattr(scene, camera_attr):
                camera = getattr(scene, camera_attr)

                # Get RGB data
                rgb_data = camera.data.output["rgb"]

                if rgb_data is not None and len(rgb_data) > 0:
                    # Convert to numpy and save
                    img_np = rgb_data[0].cpu().numpy()

                    # Handle different formats
                    if img_np.dtype != np.uint8:
                        if img_np.max() <= 1.0:
                            img_np = (img_np * 255).astype(np.uint8)
                        else:
                            img_np = img_np.astype(np.uint8)

                    # Remove alpha channel if present
                    if img_np.shape[-1] == 4:
                        img_np = img_np[:, :, :3]

                    # Save image
                    img = Image.fromarray(img_np)
                    img_path = output_dir / f"frame{frame_idx:02d}_{cam_name}.png"
                    img.save(img_path)
                    print(f"  [Saved] {img_path}")
            else:
                print(f"  [WARN] Camera {camera_attr} not found in scene")

        print(f"[Frame {frame_idx + 1}/{args.num_frames}] Complete")

    # Create combined view
    print("\n[Combine] Creating combined camera view...")
    for frame_idx in range(args.num_frames):
        images = []
        for cam_name in camera_names:
            img_path = output_dir / f"frame{frame_idx:02d}_{cam_name}.png"
            if img_path.exists():
                images.append(np.array(Image.open(img_path)))

        if len(images) == 4:
            # Create 2x2 grid
            top_row = np.concatenate([images[0], images[1]], axis=1)
            bottom_row = np.concatenate([images[2], images[3]], axis=1)
            combined = np.concatenate([top_row, bottom_row], axis=0)

            combined_img = Image.fromarray(combined)
            combined_path = output_dir / f"frame{frame_idx:02d}_combined.png"
            combined_img.save(combined_path)
            print(f"  [Combined] {combined_path}")

    print(f"\n[Done] Images saved to: {output_dir}")
    print("\nCamera layout in combined image:")
    print("  +---------------+---------------+")
    print("  |  front_left   |  front_right  |")
    print("  +---------------+---------------+")
    print("  |     back      |   overhead    |")
    print("  +---------------+---------------+")

    # Shutdown
    simulation_app.close()


if __name__ == "__main__":
    main()
