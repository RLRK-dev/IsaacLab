"""カメラ位置・姿勢確認用ビューア - 視線方向をコーンで表示"""
import argparse
import sys
import os
sys.path.insert(0, '/home/rlrk/IsaacLab/thread_isaac_lab')

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
from pxr import UsdGeom, Gf, UsdPhysics
from scipy.spatial.transform import Rotation as R

from envs.dual_arm_cfg import DualArmSceneCfg

# カメラ設定（dual_arm_cfg.pyと同じ）- convention="ros", テーブル中心(0.4, 0, 0.3)を向く
CAMERAS = {
    "FrontCamera": {
        "pos": (1.2, 0.0, 1.0),
        "rot": (0.2922, 0.6439, -0.6439, -0.2922),  # quaternion (w, x, y, z)
        "color": (1.0, 0.0, 0.0),  # 赤
    },
    "LeftBackCamera": {
        "pos": (-0.4, -0.7, 1.0),
        "rot": (0.196, 0.3638, 0.8017, 0.432),
        "color": (0.0, 1.0, 0.0),  # 緑
    },
    "RightBackCamera": {
        "pos": (-0.4, 0.7, 1.0),
        "rot": (0.432, 0.8017, 0.3638, 0.196),
        "color": (0.0, 0.0, 1.0),  # 青
    },
}

def quaternion_to_matrix(quat):
    """Convert quaternion (w, x, y, z) to rotation matrix"""
    w, x, y, z = quat
    r = R.from_quat([x, y, z, w])  # scipy uses (x, y, z, w)
    return r.as_matrix()

def create_camera_markers(stage):
    """カメラ位置に球とコーン（視線方向）を作成"""
    for name, cfg in CAMERAS.items():
        pos = cfg["pos"]
        rot = cfg["rot"]
        color = cfg["color"]

        # 球（カメラ位置）
        sphere_path = f"/World/CameraMarker_{name}_sphere"
        sphere = UsdGeom.Sphere.Define(stage, sphere_path)
        sphere.GetRadiusAttr().Set(0.03)
        xform = UsdGeom.Xformable(sphere.GetPrim())
        xform.ClearXformOpOrder()
        translate_op = xform.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(pos[0], pos[1], pos[2]))
        sphere.GetDisplayColorAttr().Set([Gf.Vec3f(color[0], color[1], color[2])])

        # コーン（視線方向）- カメラは-Z方向を向く
        cone_path = f"/World/CameraMarker_{name}_cone"
        cone = UsdGeom.Cone.Define(stage, cone_path)
        cone.GetRadiusAttr().Set(0.04)
        cone.GetHeightAttr().Set(0.15)

        # 回転行列を取得
        rot_matrix = quaternion_to_matrix(rot)

        # カメラの-Z方向（視線方向）
        look_dir = rot_matrix @ np.array([0, 0, -1])
        look_dir = look_dir / np.linalg.norm(look_dir)

        # コーンの位置（カメラから視線方向に少しオフセット）
        cone_pos = np.array(pos) + look_dir * 0.1

        # コーンの回転（デフォルトは+Y方向を向いている）
        # -Z方向を向くように回転
        default_dir = np.array([0, 1, 0])
        axis = np.cross(default_dir, look_dir)
        if np.linalg.norm(axis) > 1e-6:
            axis = axis / np.linalg.norm(axis)
            angle = np.arccos(np.clip(np.dot(default_dir, look_dir), -1, 1))
            cone_rot = R.from_rotvec(axis * angle)
        else:
            if np.dot(default_dir, look_dir) > 0:
                cone_rot = R.identity()
            else:
                cone_rot = R.from_rotvec([np.pi, 0, 0])

        cone_quat = cone_rot.as_quat()  # (x, y, z, w)

        xform_cone = UsdGeom.Xformable(cone.GetPrim())
        xform_cone.ClearXformOpOrder()
        translate_cone = xform_cone.AddTranslateOp()
        translate_cone.Set(Gf.Vec3d(cone_pos[0], cone_pos[1], cone_pos[2]))
        orient_cone = xform_cone.AddOrientOp()
        orient_cone.Set(Gf.Quatf(cone_quat[3], cone_quat[0], cone_quat[1], cone_quat[2]))

        cone.GetDisplayColorAttr().Set([Gf.Vec3f(color[0], color[1], color[2])])

        print(f"  {name}:")
        print(f"    pos={pos}, rot={rot}")
        print(f"    look_dir={look_dir.round(3)}")

def main():
    sim_cfg = sim_utils.SimulationCfg(dt=0.01, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 1.5, 1.5], [0.4, 0.0, 0.8])

    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    print("\n" + "="*60)
    print("カメラ位置・姿勢マーカーを作成中...")
    stage = sim_utils.get_current_stage()
    create_camera_markers(stage)

    sim.reset()

    front_cam = scene["front_camera"]
    left_back_cam = scene["left_back_camera"]
    right_back_cam = scene["right_back_camera"]

    print("\n" + "="*60)
    print("カメラ位置確認モード - 3カメラ120度配置")
    print("="*60)
    print("マーカー凡例:")
    print("  球: カメラ位置")
    print("  コーン: カメラ視線方向（尖った方が見ている方向）")
    print("  赤: Front Camera")
    print("  緑: Left Back Camera")
    print("  青: Right Back Camera")
    print("="*60)

    for _ in range(10):
        sim.step()
        scene.update(sim.get_physics_dt())

    output_dir = "/home/rlrk/IsaacLab/thread_isaac_lab/camera_test"
    os.makedirs(output_dir, exist_ok=True)

    cameras = [
        ("front", front_cam),
        ("left_back", left_back_cam),
        ("right_back", right_back_cam),
    ]

    print("\nカメラ画像を保存中...")
    for name, cam in cameras:
        try:
            rgb = cam.data.output["rgb"][0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[..., :3]
            if rgb.max() <= 1.0:
                rgb = (rgb * 255).astype(np.uint8)
            else:
                rgb = rgb.astype(np.uint8)
            img = Image.fromarray(rgb)
            filepath = os.path.join(output_dir, f"{name}_camera.png")
            img.save(filepath)
            print(f"  Saved: {filepath}")
        except Exception as e:
            print(f"  Error saving {name} camera: {e}")

    print("\n" + "="*60)
    print(f"カメラ画像: {output_dir}")
    print("Ctrl+C で終了")
    print("="*60 + "\n")

    while simulation_app.is_running():
        sim.step()
        scene.update(sim.get_physics_dt())

if __name__ == "__main__":
    main()
