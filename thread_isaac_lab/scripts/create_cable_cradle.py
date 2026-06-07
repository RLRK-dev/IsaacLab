"""V字溝ケーブル置き台のUSDアセットを作成（SimulationApp不要）"""

from pxr import Usd, UsdGeom, UsdPhysics, Gf
import os

def create_v_groove_cradle(output_path: str):
    """
    V字溝ケーブル置き台を作成

    仕様:
    - 台サイズ: 4cm x 4cm x 1.5cm
    - V字溝深さ: 1cm
    - V字溝幅: 2cm
    """

    # 出力ディレクトリ作成
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ステージ作成
    stage = Usd.Stage.CreateNew(output_path)

    # デフォルトプリム設定
    root_prim = stage.DefinePrim("/CableCradle", "Xform")
    stage.SetDefaultPrim(root_prim)

    # メートル単位、Z-up
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    # サイズ定義 (メートル)
    base_width = 0.04   # 4cm
    base_depth = 0.04   # 4cm
    base_height = 0.015 # 1.5cm
    groove_depth = 0.01 # 1cm
    groove_width = 0.02 # 2cm

    hw = base_width / 2
    hd = base_depth / 2
    gw = groove_width / 2
    h = base_height
    gz = h - groove_depth

    # 頂点定義
    points = [
        # 底面 (Z=0)
        Gf.Vec3f(-hw, -hd, 0),  # 0
        Gf.Vec3f( hw, -hd, 0),  # 1
        Gf.Vec3f( hw,  hd, 0),  # 2
        Gf.Vec3f(-hw,  hd, 0),  # 3
        # 上面外周 (Z=h)
        Gf.Vec3f(-hw, -hd, h),  # 4
        Gf.Vec3f( hw, -hd, h),  # 5
        Gf.Vec3f( hw,  hd, h),  # 6
        Gf.Vec3f(-hw,  hd, h),  # 7
        # V溝上端
        Gf.Vec3f(-gw, -hd, h),  # 8
        Gf.Vec3f( gw, -hd, h),  # 9
        Gf.Vec3f( gw,  hd, h),  # 10
        Gf.Vec3f(-gw,  hd, h),  # 11
        # V溝底
        Gf.Vec3f(0, -hd, gz),   # 12
        Gf.Vec3f(0,  hd, gz),   # 13
    ]

    # 面定義
    face_counts = [4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3]
    face_indices = [
        # 底面
        3, 2, 1, 0,
        # 前面
        0, 1, 5, 4,
        # 右面
        1, 2, 6, 5,
        # 後面
        2, 3, 7, 6,
        # 左面
        3, 0, 4, 7,
        # 上面左
        7, 4, 8, 11,
        # 上面右
        5, 6, 10, 9,
        # V溝左斜面
        11, 8, 12, 13,
        # V溝右斜面
        9, 10, 13, 12,
        # 前面V溝
        8, 4, 12,
        4, 5, 12,
        5, 9, 12,
        # 後面V溝
        11, 13, 7,
        7, 13, 6,
        6, 13, 10,
    ]

    # メッシュ作成
    mesh = UsdGeom.Mesh.Define(stage, "/CableCradle/Mesh")
    mesh.GetPointsAttr().Set(points)
    mesh.GetFaceVertexCountsAttr().Set(face_counts)
    mesh.GetFaceVertexIndicesAttr().Set(face_indices)

    # 色設定 (グレー)
    mesh.GetDisplayColorAttr().Set([Gf.Vec3f(0.6, 0.6, 0.6)])

    # 物理コリジョン
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())

    stage.Save()
    print(f"Created: {output_path}")

if __name__ == "__main__":
    output_path = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/objects/cable_cradle.usd"
    create_v_groove_cradle(output_path)
    print("Done!")
