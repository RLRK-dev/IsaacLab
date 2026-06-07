#!/usr/bin/env python3
"""V字溝ケーブル置き台を可視化して画像保存"""

import argparse
import sys
import os
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--save_dir", type=str, default="/home/rlrk/IsaacLab/claude_code")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# 常にheadlessで実行
args_cli.headless = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import numpy as np
from PIL import Image
import omni.usd
from pxr import UsdGeom, UsdPhysics, UsdLux, Gf

import isaaclab.sim as sim_utils


def main():
    """置き台をレンダリングして画像を保存"""

    output_dir = args_cli.save_dir
    os.makedirs(output_dir, exist_ok=True)

    # シミュレーション設定
    sim_cfg = sim_utils.SimulationCfg(
        device="cuda:0",
        dt=1.0 / 60.0,
    )
    sim = sim_utils.SimulationContext(sim_cfg)

    # ステージを取得
    stage = omni.usd.get_context().get_stage()

    # 地面を追加（シンプルな平面）
    ground = UsdGeom.Mesh.Define(stage, "/World/Ground")
    ground.GetPointsAttr().Set([
        Gf.Vec3f(-5, -5, 0), Gf.Vec3f(5, -5, 0),
        Gf.Vec3f(5, 5, 0), Gf.Vec3f(-5, 5, 0)
    ])
    ground.GetFaceVertexCountsAttr().Set([4])
    ground.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3])
    ground.GetDisplayColorAttr().Set([Gf.Vec3f(0.3, 0.3, 0.3)])

    # ライトを追加
    light = UsdLux.SphereLight.Define(stage, "/World/Light")
    light.GetIntensityAttr().Set(50000)
    light.GetRadiusAttr().Set(0.5)
    xformable = UsdGeom.Xformable(light)
    xformable.AddTranslateOp().Set(Gf.Vec3d(1.0, 0.0, 2.0))

    # ドームライト
    dome = UsdLux.DomeLight.Define(stage, "/World/DomeLight")
    dome.GetIntensityAttr().Set(1500)

    # テーブル
    TABLE_HEIGHT = 0.75
    table = UsdGeom.Cube.Define(stage, "/World/Table")
    table.GetSizeAttr().Set(1.0)
    table_xform = UsdGeom.Xformable(table)
    table_xform.AddScaleOp().Set(Gf.Vec3d(0.8, 0.6, 0.02))
    table_xform.AddTranslateOp().Set(Gf.Vec3d(0.3, 0.0, TABLE_HEIGHT - 0.01))
    table.GetDisplayColorAttr().Set([Gf.Vec3f(0.6, 0.4, 0.2)])

    # V字溝ケーブル置き台をUSDからロード
    cradle_usd = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/objects/cable_cradle.usd"
    cradle_path = "/World/CableCradle"

    # USDを参照として追加
    cradle_prim = stage.DefinePrim(cradle_path, "Xform")
    cradle_prim.GetReferences().AddReference(cradle_usd)

    # 位置を設定
    cradle_xform = UsdGeom.Xformable(cradle_prim)
    cradle_xform.AddTranslateOp().Set(Gf.Vec3d(0.3, 0.0, TABLE_HEIGHT))

    # ケーブル代わりの円柱
    cable = UsdGeom.Cylinder.Define(stage, "/World/Cable")
    cable.GetRadiusAttr().Set(0.003)
    cable.GetHeightAttr().Set(0.08)
    cable.GetAxisAttr().Set("Y")
    cable_xform = UsdGeom.Xformable(cable)
    cable_xform.AddTranslateOp().Set(Gf.Vec3d(0.3, 0.0, TABLE_HEIGHT + 0.015))  # 置き台の上
    cable.GetDisplayColorAttr().Set([Gf.Vec3f(1.0, 0.5, 0.0)])  # オレンジ

    print("Scene created:")
    print(f"  Table at z={TABLE_HEIGHT}")
    print(f"  Cradle at (0.3, 0.0, {TABLE_HEIGHT})")
    print(f"  Cable at (0.3, 0.0, {TABLE_HEIGHT + 0.015})")

    # カメラビューを設定
    sim.set_camera_view(eye=(0.8, 0.5, 1.2), target=(0.3, 0.0, TABLE_HEIGHT))

    # シミュレーション開始
    sim.reset()

    # レンダリング
    print("Rendering...")
    for _ in range(60):
        sim.render()

    # Viewport画像をキャプチャ
    try:
        from omni.kit.viewport.utility import get_active_viewport
        import omni.kit.viewport.utility.capture as capture_utils

        viewport = get_active_viewport()
        if viewport:
            # View 1: 斜め上から
            sim.set_camera_view(eye=(0.6, 0.4, 1.0), target=(0.3, 0.0, TABLE_HEIGHT))
            for _ in range(20):
                sim.render()
            save_path = os.path.join(output_dir, "cable_cradle_view1.png")
            capture_utils.capture_viewport_to_file(viewport, save_path)
            print(f"Saved: {save_path}")

            # View 2: 正面から
            sim.set_camera_view(eye=(0.8, 0.0, 0.85), target=(0.3, 0.0, TABLE_HEIGHT))
            for _ in range(20):
                sim.render()
            save_path = os.path.join(output_dir, "cable_cradle_view2.png")
            capture_utils.capture_viewport_to_file(viewport, save_path)
            print(f"Saved: {save_path}")

            # View 3: 上から
            sim.set_camera_view(eye=(0.3, 0.0, 1.2), target=(0.3, 0.0, TABLE_HEIGHT))
            for _ in range(20):
                sim.render()
            save_path = os.path.join(output_dir, "cable_cradle_overhead.png")
            capture_utils.capture_viewport_to_file(viewport, save_path)
            print(f"Saved: {save_path}")

            print(f"\nAll images saved to: {output_dir}")
        else:
            print("No active viewport found")
    except Exception as e:
        print(f"Error capturing images: {e}")

    # 少し待機
    for _ in range(30):
        sim.render()

    # クリーンアップ
    simulation_app.close()


if __name__ == "__main__":
    main()
