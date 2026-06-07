#!/usr/bin/env python3
"""
Blackwell GPU Camera Rendering Test
Tests various configurations to fix black camera output on RTX PRO 4000 Blackwell
"""

import argparse
import sys
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Test camera rendering on Blackwell GPU")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--num_cameras", type=int, default=1, help="Number of cameras (1-4)")
    parser.add_argument("--renderer", type=str, default="RayTracedLighting",
                        choices=["RayTracedLighting", "PathTracing"],
                        help="Renderer mode")
    parser.add_argument("--disable_dlss", action="store_true", help="Disable DLSS")
    parser.add_argument("--output", type=str, default="blackwell_camera_test.png",
                        help="Output image file")
    args = parser.parse_args()

    print("=" * 60)
    print("Blackwell Camera Rendering Test")
    print("=" * 60)
    print(f"Headless: {args.headless}")
    print(f"Num Cameras: {args.num_cameras}")
    print(f"Renderer: {args.renderer}")
    print(f"DLSS Disabled: {args.disable_dlss}")
    print("=" * 60)

    # Configure SimulationApp
    config = {
        "headless": args.headless,
        "anti_aliasing": 0 if args.disable_dlss else 1,  # 0 = off, 1 = FXAA, 2 = DLAA, 3 = DLSS
        "width": 512,
        "height": 512,
    }

    print("\nInitializing SimulationApp...")
    from isaacsim import SimulationApp
    simulation_app = SimulationApp(config)

    print("SimulationApp initialized!")

    # Imports after SimulationApp
    import torch
    import isaaclab.sim as sim_utils
    from isaaclab.sim import SimulationCfg, SimulationContext
    from isaaclab.sensors import CameraCfg, Camera
    from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
    from isaaclab.assets import AssetBaseCfg
    from isaaclab.utils import configclass
    import omni.replicator.core as rep

    # Set renderer mode
    print(f"\nSetting renderer to: {args.renderer}")
    import carb.settings
    settings = carb.settings.get_settings()

    if args.renderer == "PathTracing":
        settings.set("/rtx/rendermode", "PathTracing")
        settings.set("/rtx/pathtracing/optixDenoiser/enabled", False)
    else:
        settings.set("/rtx/rendermode", "RayTracedLighting")

    # Disable DLSS if requested
    if args.disable_dlss:
        print("Disabling DLSS/DLAA...")
        settings.set("/rtx/post/dlss/enabled", False)
        settings.set("/rtx/post/aa/op", 0)  # Disable AA

    # Check GPU info
    print(f"\nPyTorch CUDA device: {torch.cuda.get_device_name(0)}")

    # Create scene config
    @configclass
    class TestSceneCfg(InteractiveSceneCfg):
        """Simple scene with ground plane and cameras"""

        ground = AssetBaseCfg(
            prim_path="/World/Ground",
            spawn=sim_utils.GroundPlaneCfg(),
        )

        # Light
        dome_light = AssetBaseCfg(
            prim_path="/World/DomeLight",
            spawn=sim_utils.DomeLightCfg(
                intensity=1000.0,
                color=(1.0, 1.0, 1.0),
            ),
        )

        # Add a visible object (cube)
        cube = AssetBaseCfg(
            prim_path="/World/Cube",
            spawn=sim_utils.CuboidCfg(
                size=(0.5, 0.5, 0.5),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(1.0, 0.0, 0.0),
                ),
            ),
            init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 0.25)),
        )

    # Create simulation context
    sim_cfg = SimulationCfg(
        dt=1/60.0,
        device="cuda:0",
    )
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(3.0, 3.0, 3.0), target=(0.0, 0.0, 0.0))

    # Create scene
    print("\nCreating scene...")
    scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    # Create cameras
    print(f"\nCreating {args.num_cameras} camera(s)...")
    cameras = []
    camera_positions = [
        ((2.0, 0.0, 1.5), (0.0, 0.0, 0.0)),   # Front
        ((0.0, 2.0, 1.5), (0.0, 0.0, 0.0)),   # Side
        ((0.0, 0.0, 3.0), (0.0, 0.0, 0.0)),   # Top
        ((-2.0, 0.0, 1.5), (0.0, 0.0, 0.0)),  # Back
    ]

    for i in range(min(args.num_cameras, 4)):
        pos, target = camera_positions[i]
        cam_cfg = CameraCfg(
            prim_path=f"/World/Camera_{i}",
            update_period=0.0,
            height=256,
            width=256,
            data_types=["rgb"],
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=24.0,
                horizontal_aperture=20.955,
            ),
        )
        camera = Camera(cam_cfg)
        cameras.append(camera)
        print(f"  Camera {i}: pos={pos}, target={target}")

    # Reset simulation
    print("\nResetting simulation...")
    sim.reset()
    scene.reset()

    # Position cameras
    for i, camera in enumerate(cameras):
        pos, target = camera_positions[i]
        camera.set_world_poses(
            positions=torch.tensor([[pos[0], pos[1], pos[2]]], device="cuda:0"),
            orientations=None,
            env_ids=torch.tensor([0], device="cuda:0"),
        )

    # Warm-up steps
    print("\nRunning warm-up steps...")
    for _ in range(30):
        sim.step()
        scene.update(sim.get_physics_dt())
        for camera in cameras:
            camera.update(sim.get_physics_dt())

    # Capture images
    print("\nCapturing images...")
    images = []
    for i, camera in enumerate(cameras):
        camera.update(sim.get_physics_dt())
        rgb_data = camera.data.output["rgb"]
        if rgb_data is not None:
            img = rgb_data[0].cpu().numpy()
            images.append(img)

            # Check if image is black
            mean_val = img.mean()
            max_val = img.max()
            print(f"  Camera {i}: shape={img.shape}, mean={mean_val:.2f}, max={max_val}")

            if mean_val < 1.0:
                print(f"    ⚠️  WARNING: Camera {i} appears to be BLACK!")
            else:
                print(f"    ✅ Camera {i} has valid data")
        else:
            print(f"  Camera {i}: NO DATA (None)")
            images.append(np.zeros((256, 256, 4), dtype=np.uint8))

    # Save composite image
    if images:
        print(f"\nSaving image to {args.output}...")
        from PIL import Image

        if len(images) == 1:
            composite = images[0][:, :, :3]  # Remove alpha
        else:
            # Create 2x2 grid
            h, w = 256, 256
            composite = np.zeros((h*2, w*2, 3), dtype=np.uint8)
            for i, img in enumerate(images[:4]):
                row = i // 2
                col = i % 2
                composite[row*h:(row+1)*h, col*w:(col+1)*w] = img[:, :, :3]

        Image.fromarray(composite).save(args.output)
        print(f"Saved: {args.output}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    all_valid = True
    for i, img in enumerate(images):
        mean_val = img.mean() if img is not None else 0
        if mean_val < 1.0:
            print(f"Camera {i}: ❌ BLACK (mean={mean_val:.2f})")
            all_valid = False
        else:
            print(f"Camera {i}: ✅ OK (mean={mean_val:.2f})")

    if all_valid:
        print("\n✅ ALL CAMERAS WORKING!")
    else:
        print("\n❌ SOME CAMERAS ARE BLACK - RENDERING ISSUE DETECTED")

    print("=" * 60)

    # Cleanup
    simulation_app.close()

    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
