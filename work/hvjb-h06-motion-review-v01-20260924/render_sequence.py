# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render the preserved FC02 translation comparison as PNGs, without generating a video."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from itertools import product
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import numpy as np
import pyrender
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FPS, DURATION = 15, 10
POSE_FIELDS = ("opening_per_jaw_mm", "hand_lift_mm", "clamp_toe_outward_mm", "case_lift_mm")
LABELS = {
    "loading": ["① ピンへ導入", "② 着座位置", "③ パレット保持", "④ 指を開く", "⑤ 手を上げる"],
    "pickup": ["① 指を開いて接近", "② 把持位置へ", "③ H06で保持", "④ パレットを開放", "⑤ ピンを抜けて上昇"],
}
NOTES = {
    "loading": [
        "筐体はH06で持ったまま下ろす。前面の向きと穴位置を確認する手順。",
        "筐体の下面を3点で受ける。着座確認前にクランプで押し込まない。",
        "H06はまだ開かない。着座とパレット側の保持確認が次の開放条件。",
        "筐体をパレット側で保持した後、指を外へ開く。切欠きからピンを逃がす。",
        "指を開いたまま上昇。手が退避してからST固定を解除し、パレットを動かす。",
    ],
    "pickup": [
        "パレットをSTで固定し、指を開いた状態で下ろす。パレット側の保持を続ける。",
        "指を四隅の把持位置まで下ろす。まだパレット側を開放しない。",
        "H06を閉じて保持を確認する手順。パレット側はまだ保持を続ける。",
        "H06の保持確認後、パレットのクランプを開放し、その退避を確認する。",
        "筐体とH06を一緒に上げる。両ピンを抜けてから横方向の搬送へ移る。",
    ],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def look_at(eye: np.ndarray, focus: np.ndarray) -> np.ndarray:
    z = np.asarray(eye) - focus
    z /= np.linalg.norm(z)
    x = np.cross([0, 0, 1], z)
    x /= np.linalg.norm(x)
    pose = np.eye(4)
    pose[:3, :3] = np.column_stack((x, np.cross(z, x), z))
    pose[:3, 3] = eye
    return pose


def state_at(states: list[dict], seconds: float) -> dict:
    """Interpolate only the four source pose fields [mm]; times are illustration seconds."""
    for index in range(5):
        start = index * 2.25
        if seconds <= start + 1 or index == 4:
            return dict(states[index], source_pose_index=index, next_pose_index=index, interpolation=0.0)
        if seconds < start + 2.25:
            u = (seconds - start - 1) / 1.25
            row = dict(states[index])
            row.update({key: states[index][key] * (1 - u) + states[index + 1][key] * u for key in POSE_FIELDS})
            row.update(source_pose_index=index, next_pose_index=index + 1, interpolation=u)
            return row
    raise AssertionError(seconds)


def mesh_group(name: str) -> str:
    if name.startswith("H06_"):
        return "hand"
    if "__" in name:
        return "product"
    return "fixture"


def moved_pose(name: str, saved: np.ndarray, row: dict) -> np.ndarray:
    pose = saved.copy()
    if name.startswith("H06_"):
        sign = 1 if name.startswith("H06_+1") else -1
        pose[:3, 3] += np.array([sign * row["opening_per_jaw_mm"], 0, row["hand_lift_mm"]]) / 1000
    elif name.endswith("toe_envelope"):
        pose[0, 3] += (-1 if name.startswith("C1") else 1) * row["clamp_toe_outward_mm"] / 1000
    elif mesh_group(name) == "product":
        pose[2, 3] += row["case_lift_mm"] / 1000
    return pose


def bounds_corners(part: trimesh.Trimesh) -> np.ndarray:
    return np.array(list(product(*part.bounds.T.tolist())))


def view_frame(
    model: trimesh.Scene, names: list[str], states: list[dict], direction: list[float], size: tuple[int, int]
):
    """Fit one camera to all preserved endpoint envelopes, without changing the model."""
    points = []
    for name in names:
        pose, geometry = model.graph[name]
        corners = bounds_corners(model.geometry[geometry])
        for row in states:
            moved = moved_pose(name, pose, row)
            points.append(corners @ moved[:3, :3].T + moved[:3, 3])
    points = np.concatenate(points)
    focus = (points.min(0) + points.max(0)) / 2
    camera = look_at(focus + direction, focus)
    projected = (points - focus) @ camera[:3, :3]
    span = 1.12 * max(abs(projected[:, 0]).max(), abs(projected[:, 1]).max() * size[0] / size[1])
    return focus, float(span)


class Views:
    """Reuse saved mesh rows in two fixed cameras; crop nothing out of the full assembly view."""

    def __init__(self, model: trimesh.Scene, operation: str, states: list[dict]):
        names = sorted(model.graph.nodes_geometry)
        detail_names = [name for name in names if name.startswith(("H06_+1_-1_", "B2_"))]
        focus, span = view_frame(model, names, states, [0.45, -0.65, 0.43], (1200, 760))
        self.main = self.scene(focus, [0.45, -0.65, 0.43], span, (1200, 760))
        focus, span = view_frame(model, detail_names, states, [-0.035, -0.14, 0.095], (620, 410))
        self.detail = self.scene(focus, [-0.035, -0.14, 0.095], span, (620, 410))
        self.main_nodes, self.detail_nodes, self.original = {}, {}, {}
        self.corners = {}
        for name in names:
            pose, geometry = model.graph[name]
            self.original[name] = pose.copy()
            part = model.geometry[geometry]
            self.corners[name] = bounds_corners(part)
            mesh = pyrender.Mesh.from_trimesh(part, smooth=False)
            if operation == "pickup" or mesh_group(name) != "product" or name.startswith("P01__"):
                self.main_nodes[name] = self.main.add(mesh, pose=pose)
            if name.startswith(("H06_+1_-1_", "B2_")):
                self.detail_nodes[name] = self.detail.add(mesh, pose=pose)
        # One GL context permits the same immutable mesh to appear in both views.
        self.renderer = pyrender.OffscreenRenderer(1200, 760)
        self.camera_record = {
            label: {
                "matrix": scene.get_pose(scene.main_camera_node).tolist(),
                "xmag_m": scene.main_camera_node.camera.xmag,
                "ymag_m": scene.main_camera_node.camera.ymag,
            }
            for label, scene in (("main", self.main), ("detail", self.detail))
        }
        self.last_framing = {}

    @staticmethod
    def scene(focus: list[float], direction: list[float], span: float, size: tuple[int, int]) -> pyrender.Scene:
        focus = np.array(focus)
        scene = pyrender.Scene(bg_color=[0.96, 0.978, 0.985, 1], ambient_light=[0.45, 0.45, 0.45])
        scene.add(
            pyrender.OrthographicCamera(xmag=span, ymag=span * size[1] / size[0], znear=0.001, zfar=5),
            pose=look_at(focus + direction, focus),
        )
        for direction, intensity in (([0.35, -0.5, 0.8], 2.8), ([-0.4, -0.25, 0.2], 1.1)):
            scene.add(
                pyrender.DirectionalLight(color=np.ones(3), intensity=intensity),
                pose=look_at(focus + direction, focus),
            )
        return scene

    def images(self, row: dict) -> tuple[Image.Image, Image.Image]:
        for label, nodes, scene in (("main", self.main_nodes, self.main), ("detail", self.detail_nodes, self.detail)):
            points = []
            for name, node in nodes.items():
                pose = moved_pose(name, self.original[name], row)
                scene.set_pose(node, pose)
                points.append(self.corners[name] @ pose[:3, :3].T + pose[:3, 3])
            points = np.concatenate(points)
            camera = scene.get_pose(scene.main_camera_node)
            assert camera.tolist() == self.camera_record[label]["matrix"]
            xy = ((points - camera[:3, 3]) @ camera[:3, :3])[:, :2]
            xy /= [scene.main_camera_node.camera.xmag, scene.main_camera_node.camera.ymag]
            bounds = [xy.min(0).tolist(), xy.max(0).tolist()]
            assert abs(xy).max() < 1, (label, bounds)
            self.last_framing[label] = bounds
        pictures = []
        for scene, size in ((self.main, (1200, 760)), (self.detail, (620, 410))):
            self.renderer.viewport_width, self.renderer.viewport_height = size
            color, depth = self.renderer.render(scene)
            assert np.isfinite(depth).all() and np.count_nonzero(depth) > 100
            pictures.append(Image.fromarray(color).convert("RGB"))
        return tuple(pictures)

    def close(self) -> None:
        self.renderer.delete()


class Composition:
    def __init__(self):
        self.fonts = {s: ImageFont.truetype(FONT, s) for s in (23, 25, 27, 29, 36)}
        self.text_bounds = []

    def text(self, draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size=27, color="#173B4D") -> None:
        box = draw.textbbox(xy, text, font=self.fonts[size])
        assert 0 <= box[0] < box[2] <= 1920 and 0 <= box[1] < box[3] <= 1080, (text, box)
        self.text_bounds.append(box)
        draw.text(xy, text, font=self.fonts[size], fill=color)

    def compose(self, pictures: tuple[Image.Image, Image.Image], operation: str, row: dict) -> Image.Image:
        image = Image.new("RGB", (1920, 1080), "#F2F6F8")
        draw = ImageDraw.Draw(image)
        is_load = operation == "loading"
        title = "空筐体をパレットへ載せる" if is_load else "内部付き筐体をパレットから受け取る"
        self.text(draw, (28, 23), f"H06 受け渡し拡大  |  {title}", 36)
        self.text(draw, (30, 76), "H06_FC02：筐体の四隅を受ける2本指／支持の引継ぎ／指の逃げ", 25)
        phase = row["next_pose_index"]
        for i, label in enumerate(LABELS[operation]):
            x = 26 + i * 379
            draw.rounded_rectangle((x, 129, x + 362, 184), 6, fill="#198772" if i == phase else "#E2EBF0")
            self.text(draw, (x + 14, 140), label, 25, "white" if i == phase else "#4D6573")
        image.paste(pictures[0].resize((1120, 709), Image.Resampling.LANCZOS), (40, 194))
        image.paste(pictures[1], (1260, 234))
        draw = ImageDraw.Draw(image)
        self.text(draw, (1281, 201), "ピンと指の切欠き（周囲は非表示）", 25)
        self.text(draw, (1281, 659), "青・緑青：H06の受けと接触パッド", 25)
        self.text(draw, (1281, 706), "橙：公称穴径によるピン包絡", 25)
        self.text(draw, (1281, 753), "紫：パレット保持部の配置予約", 25)
        self.text(draw, (1281, 816), "クランプ機構・ピンのはめ合い・", 25, "#657984")
        self.text(draw, (1281, 851), "着座／保持検出は未確定です。", 25, "#657984")
        draw.rounded_rectangle((25, 911, 1895, 1009), 7, fill="white", outline="#CADCE5", width=2)
        self.text(draw, (44, 926), NOTES[operation][phase], 27)
        self.text(draw, (44, 968), "確認の記載は必要な手順であり、測定済みのセンサ信号ではありません。", 23, "#657984")
        footer = "既存の形状・比較姿勢を再利用。実機の把持成立・干渉・タクトの判定ではありません。"
        self.text(draw, (32, 1031), footer, 23, "#657984")
        return image


def verify_inputs() -> dict[str, str]:
    record = json.loads((ROOT / "source_identity.json").read_text())
    pins = {str(ROOT / row["copy"]): row["sha256"] for row in record["source_files"]}
    pins[str(Path(__file__))] = sha(Path(__file__))
    for path, digest in pins.items():
        assert sha(Path(path)) == digest, path
    return pins


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output_name", default="process")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    output = ROOT / "output" / args.output_name
    assert not output.exists(), output
    pins = verify_inputs()
    saved = json.loads((ROOT / "sources/handoff_sequence_observations.json").read_text())
    model = trimesh.load(ROOT / "sources/H06_FC02_handoff_populated_comparison.glb", force="scene", process=False)
    names = sorted(model.graph.nodes_geometry)
    counts = {key: sum(mesh_group(name) == key for name in names) for key in ("product", "hand", "fixture")}
    assert counts == {"product": 465, "hand": 66, "fixture": 12}, counts
    assert sum(name.startswith("P01__") for name in names) == 56
    output.mkdir(parents=True)
    composition = Composition()
    frames, cameras = [], {}
    indices = [7, 41, 75, 108, 142] if args.preview else range(FPS * DURATION)
    for operation in ("loading", "pickup"):
        views = Views(model, operation, saved["states"]["loading"])
        cameras[operation] = views.camera_record
        try:
            for index in indices:
                row = state_at(saved["states"][operation], index / FPS)
                image = composition.compose(views.images(row), operation, row)
                file = output / f"{operation}_{index + 1:04d}.png"
                image.save(file)
                frames.append(
                    {
                        "operation": operation,
                        "local_frame": index + 1,
                        "local_time_s": index / FPS,
                        "file": file.name,
                        "sha256": sha(file),
                        "pose": row,
                        "projected_mesh_bounds_normalized": dict(views.last_framing),
                    }
                )
                if index % 30 == 0 or args.preview:
                    print(f"H06_PROCESS_PNG {operation} {index + 1}/{FPS * DURATION}", flush=True)
        finally:
            views.close()
    assert pins == verify_inputs()
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_sha256": pins,
        "source_geometry_counts": counts,
        "all_source_geometry_preserved": True,
        "loading_product_meshes_shown": 56,
        "pickup_product_meshes_shown": 465,
        "all_camera_poses_fixed": True,
        "cameras": cameras,
        "source_states": saved["states"],
        "frame_count": len(frames),
        "fps": FPS,
        "dimensions": [1920, 1080],
        "preview_only": args.preview,
        "physical_acceptance_verdict": None,
        "motions": "Linear translation between the existing five poses; display holds added, no new endpoints.",
        "timing_basis": "10 illustration seconds per operation, not actual machine timing.",
        "text_elements_checked": len(composition.text_bounds),
        "images": frames,
    }
    (output / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"H06_PROCESS_COMPLETE frames={len(frames)} source_unchanged=True video_files_created=0", flush=True)


if __name__ == "__main__":
    main()
