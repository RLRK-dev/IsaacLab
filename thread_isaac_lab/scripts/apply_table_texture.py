#!/usr/bin/env python3
"""
テーブルに格子線テクスチャを適用するスクリプト
シーン作成後に呼び出す
"""
import os


def apply_grid_texture_to_table(stage, table_prim_path: str, texture_path: str = None):
    """
    テーブルのマテリアルに格子線テクスチャを適用

    Args:
        stage: USD stage
        table_prim_path: テーブルのprim path (例: /World/envs/env_0/Table)
        texture_path: テクスチャファイルのパス
    """
    from pxr import Usd, UsdShade, Sdf, UsdGeom
    import omni.usd

    if texture_path is None:
        texture_path = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/textures/table_grid.png"

    # テクスチャファイルの存在確認
    if not os.path.exists(texture_path):
        print(f"[WARN] Texture file not found: {texture_path}")
        print("       Creating grid texture...")
        create_grid_texture(texture_path)

    # テーブルのprimを取得
    table_prim = stage.GetPrimAtPath(table_prim_path)
    if not table_prim.IsValid():
        print(f"[ERROR] Table prim not found at: {table_prim_path}")
        return False

    print(f"[INFO] Applying texture to table: {table_prim_path}")

    # マテリアルを作成
    material_path = f"{table_prim_path}/GridMaterial"
    material = UsdShade.Material.Define(stage, material_path)

    # シェーダーを作成
    shader_path = f"{material_path}/Shader"
    shader = UsdShade.Shader.Define(stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")

    # テクスチャリーダーを作成
    texture_reader_path = f"{material_path}/DiffuseTexture"
    texture_reader = UsdShade.Shader.Define(stage, texture_reader_path)
    texture_reader.CreateIdAttr("UsdUVTexture")
    texture_reader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(texture_path)
    texture_reader.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("repeat")
    texture_reader.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("repeat")
    texture_reader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

    # UV座標用のprimvarリーダー
    st_reader_path = f"{material_path}/TexCoordReader"
    st_reader = UsdShade.Shader.Define(stage, st_reader_path)
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
    st_reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

    # 接続
    texture_reader.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        st_reader.ConnectableAPI(), "result"
    )

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        texture_reader.ConnectableAPI(), "rgb"
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.8)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    # テーブルにマテリアルをバインド
    UsdShade.MaterialBindingAPI(table_prim).Bind(material)

    print(f"[INFO] Grid texture applied successfully")
    return True


def create_grid_texture(output_path: str):
    """格子線テクスチャを作成"""
    from PIL import Image, ImageDraw
    import os

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    size = (1024, 1024)
    grid_spacing = 100  # 10cm相当
    line_color = (120, 120, 120)
    center_line_color = (180, 60, 60)
    bg_color = (235, 230, 215)  # ベージュ
    line_width = 2
    center_line_width = 5

    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)

    w, h = size

    # 通常の格子線
    for x in range(0, w + 1, grid_spacing):
        if x != w // 2:
            draw.line([(x, 0), (x, h)], fill=line_color, width=line_width)
    for y in range(0, h + 1, grid_spacing):
        if y != h // 2:
            draw.line([(0, y), (w, y)], fill=line_color, width=line_width)

    # 中心線を強調
    draw.line([(w//2, 0), (w//2, h)], fill=center_line_color, width=center_line_width)
    draw.line([(0, h//2), (w, h//2)], fill=center_line_color, width=center_line_width)

    img.save(output_path)
    print(f"[INFO] Grid texture created: {output_path}")


if __name__ == "__main__":
    # テクスチャファイルだけを作成
    texture_path = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/textures/table_grid.png"
    create_grid_texture(texture_path)
    print(f"Created: {texture_path}")
