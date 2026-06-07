#!/usr/bin/env python3
"""
格子線テクスチャ作成スクリプト
中心線強調 + 10cm格子のテクスチャを生成
"""
from PIL import Image, ImageDraw
import os


def create_grid_texture(
    size=(1024, 1024),
    grid_spacing=100,  # 10cm相当
    line_color=(120, 120, 120),  # 薄いグレー
    center_line_color=(180, 60, 60),  # 赤っぽい
    bg_color=(235, 230, 215),  # ベージュ（テーブル色）
    line_width=2,
    center_line_width=5,
):
    """中心線強調 + 10cm格子のテクスチャ"""
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)

    w, h = size

    # 通常の格子線（10cm間隔）
    for x in range(0, w + 1, grid_spacing):
        if x != w // 2:  # 中心線は後で描く
            draw.line([(x, 0), (x, h)], fill=line_color, width=line_width)
    for y in range(0, h + 1, grid_spacing):
        if y != h // 2:
            draw.line([(0, y), (w, y)], fill=line_color, width=line_width)

    # 中心線を強調（太く、濃い色）
    draw.line([(w//2, 0), (w//2, h)], fill=center_line_color, width=center_line_width)
    draw.line([(0, h//2), (w, h//2)], fill=center_line_color, width=center_line_width)

    return img


if __name__ == "__main__":
    # ディレクトリ作成
    os.makedirs('assets/textures', exist_ok=True)
    os.makedirs('training_debug', exist_ok=True)

    # テクスチャ生成
    img = create_grid_texture()

    # 保存
    img.save('assets/textures/table_grid.png')
    print('Created assets/textures/table_grid.png')

    # プレビュー保存
    img.save('training_debug/table_grid_preview.png')
    print('Preview: training_debug/table_grid_preview.png')

    # claude_code にもコピー
    os.makedirs('/home/rlrk/IsaacLab/claude_code', exist_ok=True)
    img.save('/home/rlrk/IsaacLab/claude_code/table_grid_preview.png')
    print('Also saved to: /home/rlrk/IsaacLab/claude_code/table_grid_preview.png')
