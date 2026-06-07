#!/usr/bin/env python3
"""V字溝ケーブル置き台の画像をキャプチャ (TiledCamera使用)"""

import argparse
import sys
import os

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
from PIL import Image
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

import isaaclab.sim as sim_utils
from isaaclab.sensors import TiledCamera, TiledCameraCfg


def main():
    output_dir = "/home/rlrk/IsaacLab/claude_code"
    os.makedirs(output_dir, exist_ok=True)

    # シミュレーション設定
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=1.0/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)

    stage = omni.usd.get_context().get_stage()

    # ドームライト
    dome = UsdLux.DomeLight.Define(stage, "/World/DomeLight")
    dome.GetIntensityAttr().Set(2000)

    # 地面
    ground = UsdGeom.Mesh.Define(stage, "/World/Ground")
    ground.GetPointsAttr().Set([
        Gf.Vec3f(-2, -2, 0), Gf.Vec3f(2, -2, 0),
        Gf.Vec3f(2, 2, 0), Gf.Vec3f(-2, 2, 0)
    ])
    ground.GetFaceVertexCountsAttr().Set([4])
    ground.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3])
    ground.GetDisplayColorAttr().Set([Gf.Vec3f(0.3, 0.3, 0.3)])

    # テーブル
    TABLE_HEIGHT = 0.75
    table = UsdGeom.Cube.Define(stage, "/World/Table")
    table.GetSizeAttr().Set(1.0)
    table_xform = UsdGeom.Xformable(table)
    table_xform.AddScaleOp().Set(Gf.Vec3d(0.5, 0.4, 0.02))
    table_xform.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, TABLE_HEIGHT - 0.01))
    table.GetDisplayColorAttr().Set([Gf.Vec3f(0.6, 0.4, 0.2)])

    # V字溝置き台
    cradle_usd = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/objects/cable_cradle.usd"
    cradle_prim = stage.DefinePrim("/World/CableCradle", "Xform")
    cradle_prim.GetReferences().AddReference(cradle_usd)
    UsdGeom.Xformable(cradle_prim).AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, TABLE_HEIGHT))

    # オレンジの円柱（ケーブル代わり）
    cable = UsdGeom.Cylinder.Define(stage, "/World/Cable")
    cable.GetRadiusAttr().Set(0.004)
    cable.GetHeightAttr().Set(0.06)
    cable.GetAxisAttr().Set("Y")
    UsdGeom.Xformable(cable).AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, TABLE_HEIGHT + 0.012))
    cable.GetDisplayColorAttr().Set([Gf.Vec3f(1.0, 0.5, 0.0)])

    print("Scene created")

    # TiledCamera設定
    camera_cfg = TiledCameraCfg(
        prim_path="/World/Camera",
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            horizontal_aperture=20.955,
        ),
        offset=TiledCameraCfg.OffsetCfg(
            pos=(0.25, 0.15, TABLE_HEIGHT + 0.15),
            rot=(0.85, 0.35, -0.15, -0.35),
            convention="world",
        ),
        width=512,
        height=512,
        data_types=["rgb"],
    )

    # シミュレーション開始
    sim.reset()

    # カメラ作成
    camera = TiledCamera(camera_cfg)
    camera.reset()

    # レンダリング
    print("Rendering...")
    for _ in range(60):
        sim.step()
        camera.update(sim.get_physics_dt())

    # 画像取得
    rgb_data = camera.data.output["rgb"]
    if rgb_data is not None and len(rgb_data) > 0:
        img_array = rgb_data[0].cpu().numpy()
        if img_array.shape[-1] == 4:
            img_array = img_array[:, :, :3]
        if img_array.max() <= 1.0:
            img_array = (img_array * 255).astype(np.uint8)
        else:
            img_array = img_array.astype(np.uint8)

        img = Image.fromarray(img_array)
        save_path = os.path.join(output_dir, "cable_cradle.png")
        img.save(save_path)
        print(f"Saved: {save_path}")
    else:
        print("No image data")

    simulation_app.close()


if __name__ == "__main__":
    main()
