# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render saved H05 release samples and a stationary contour-detail view into process PNGs."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
HELPER = ROOT.parent / "hvjb-h06-motion-review-v01-20260924/render_sequence.py"
spec = importlib.util.spec_from_file_location("h06_display_helpers", HELPER)
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
np, pyrender, trimesh = H.np, H.pyrender, H.trimesh
Image, ImageDraw = H.Image, H.ImageDraw
PHASES = ["held", "opening", "upward_withdrawal"]
LABELS = ["① 固定後も保持", "② 指を開く", "③ 上方へ退避"]
NOTES = [
    "側面の輪郭受けで向きを保つ方針。ヘッダーの固定を確認するまで指は開かない。",
    "既存の開閉機構に従い、指が外側・上方へ動く。ヘッダーは固定位置に残す。",
    "指を開いた状態で上方へ退避。受けの内側に部品を引っ掛けない形状を比較する。",
]


def load_inputs():
    identity = json.loads((ROOT / "data/release_identity.json").read_text())
    data, pins = {}, {str(HELPER): H.sha(HELPER), str(Path(__file__)): H.sha(Path(__file__))}
    for path, digest in identity["source_sha256"].items():
        copy = ROOT / "sources" / Path(path).name
        assert H.sha(copy) == digest
        pins[str(copy)] = digest
    for row in identity["models"]:
        bank, glb = ROOT / row["derived_bank"], ROOT / row["copied_geometry"]
        assert H.sha(bank) == row["derived_bank_sha256"] and H.sha(glb) == row["copied_geometry_sha256"]
        pins[str(bank)] = H.sha(bank)
        with np.load(bank, allow_pickle=False) as saved:
            arrays = {key: saved[key] for key in saved.files}
        data[row["feature"]] = {"identity": row, "scene": trimesh.load(glb, force="scene", process=False), **arrays}
    return data, pins


def detail_name(name: str) -> bool:
    return name.startswith("official_header_") or name.endswith(("contour_pad", "contour_backing", "front_thrust_pad"))


def camera_frame(data: dict, detail: bool):
    points = []
    direction = [0.18, -0.7, 0.16] if detail else [0.25, -0.8, 0.25]
    size = (620, 410) if detail else (1200, 760)
    for row in data.values():
        for column, name in enumerate(row["object_names"]):
            if detail and not detail_name(name):
                continue
            _, geometry = row["scene"].graph[name]
            corners = H.bounds_corners(row["scene"].geometry[geometry])
            poses = row["matrices"][:1, column] if detail else row["matrices"][:, column]
            for pose in poses:
                points.append(corners @ pose[:3, :3].T + pose[:3, 3])
    points = np.concatenate(points)
    focus = (points.min(0) + points.max(0)) / 2
    camera = H.look_at(focus + direction, focus)
    projected = (points - focus) @ camera[:3, :3]
    span = 1.12 * max(abs(projected[:, 0]).max(), abs(projected[:, 1]).max() * size[0] / size[1])
    return {"focus": focus, "direction": direction, "span": float(span), "size": size}


class Views:
    def __init__(self, data: dict, frames: dict):
        self.data = data
        self.scenes, self.nodes, self.corners, self.cameras = {}, {}, {}, {}
        for label, config in frames.items():
            scene = H.Views.scene(config["focus"], config["direction"], config["span"], config["size"])
            self.nodes[label] = {}
            for column, name in enumerate(data["object_names"]):
                if label == "detail" and not detail_name(name):
                    continue
                _, geometry = data["scene"].graph[name]
                part = data["scene"].geometry[geometry]
                self.corners[name] = H.bounds_corners(part)
                mesh = pyrender.Mesh.from_trimesh(part, smooth=False)
                node = scene.add(mesh, pose=data["matrices"][0, column])
                self.nodes[label][name] = (node, column)
            self.scenes[label] = scene
            self.cameras[label] = {"matrix": scene.get_pose(scene.main_camera_node).tolist(), "span_m": config["span"]}
        self.renderer = pyrender.OffscreenRenderer(1200, 760)
        self.last_framing = {}

    def images(self, index: int):
        images = []
        for label, size in (("main", (1200, 760)), ("detail", (620, 410))):
            scene, points = self.scenes[label], []
            pose_index = index if label == "main" else 0
            for name, (node, column) in self.nodes[label].items():
                pose = self.data["matrices"][pose_index, column]
                scene.set_pose(node, pose)
                points.append(self.corners[name] @ pose[:3, :3].T + pose[:3, 3])
            camera = scene.get_pose(scene.main_camera_node)
            assert camera.tolist() == self.cameras[label]["matrix"]
            xy = ((np.concatenate(points) - camera[:3, 3]) @ camera[:3, :3])[:, :2]
            xy /= [scene.main_camera_node.camera.xmag, scene.main_camera_node.camera.ymag]
            assert abs(xy).max() < 1
            self.last_framing[label] = [xy.min(0).tolist(), xy.max(0).tolist()]
            self.renderer.viewport_width, self.renderer.viewport_height = size
            pixels, depth = self.renderer.render(scene)
            assert np.isfinite(depth).all() and np.count_nonzero(depth) > 100
            images.append(Image.fromarray(pixels).convert("RGB"))
        return images


class Composition(H.Composition):
    def compose(self, pictures, feature, row, index):
        phase = PHASES.index(str(row["source_phase"][index]))
        image = Image.new("RGB", (1920, 1080), "#F2F6F8")
        draw = ImageDraw.Draw(image)
        model = "3口／TE 2103340-1" if feature == "P16" else "2口／TE 2103346-2"
        self.text(draw, (28, 23), f"H05 外側ヘッダー  |  {model}", 36)
        self.text(draw, (30, 76), "外形に沿う受けで保持し、固定後に指を開いて退避する比較", 25)
        for i, label in enumerate(LABELS):
            x = 26 + i * 631
            draw.rounded_rectangle((x, 129, x + 615, 184), 6, fill="#198772" if i == phase else "#E2EBF0")
            self.text(draw, (x + 24, 140), label, 25, "white" if i == phase else "#4D6573")
        image.paste(pictures[0].resize((1120, 709), Image.Resampling.LANCZOS), (40, 194))
        image.paste(pictures[1], (1260, 250))
        draw = ImageDraw.Draw(image)
        self.text(draw, (55, 201), "ハンド全体：保存姿勢の順送り", 25)
        self.text(draw, (1278, 201), "受けの形状：保持位置を固定表示", 25)
        self.text(draw, (1280, 683), "緑青：輪郭に沿う受けと前側の当て", 25)
        self.text(draw, (1280, 730), "青：受けを支える部材", 25)
        self.text(draw, (1280, 788), "3口・2口は、それぞれのCADから", 25, "#657984")
        self.text(draw, (1280, 824), "別の輪郭受けを作った比較形状。", 25, "#657984")
        draw.rounded_rectangle((25, 911, 1895, 1009), 7, fill="white", outline="#CADCE5", width=2)
        self.text(draw, (44, 926), NOTES[phase], 27)
        self.text(
            draw,
            (44, 968),
            "固定後の局所表示。筐体・ねじ・工具は非表示で、締結検出を示す映像ではありません。",
            23,
            "#657984",
        )
        frame = int(row["saved_frames"][index])
        self.text(
            draw,
            (32, 1031),
            f"{feature} 保存frame {frame} ｜比較形状と姿勢の説明。実機の把持・干渉・タクトは未判定。",
            23,
            "#657984",
        )
        return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output_name", default="process")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    output = ROOT / "output" / args.output_name
    assert not output.exists()
    data, pins = load_inputs()
    frames = {label: camera_frame(data, label == "detail") for label in ("main", "detail")}
    output.mkdir(parents=True)
    records, cameras = [], {}
    composition = Composition()
    for feature, row in data.items():
        views = Views(row, frames)
        cameras[feature] = views.cameras
        indices = [0, 6, 10, len(row["matrices"]) - 1] if args.preview else range(len(row["matrices"]))
        try:
            for index in indices:
                pictures = views.images(index)
                file = output / f"{feature}_{index + 1:04d}.png"
                composition.compose(pictures, feature, row, index).save(file)
                records.append(
                    {
                        "feature": feature,
                        "source_sample_index": int(index),
                        "saved_frame": int(row["saved_frames"][index]),
                        "source_phase": str(row["source_phase"][index]),
                        "file": file.name,
                        "sha256": H.sha(file),
                        "projected_mesh_bounds_normalized": dict(views.last_framing),
                    }
                )
                print(f"H05_PROCESS_PNG {feature} {index + 1}/{len(row['matrices'])}", flush=True)
        finally:
            views.renderer.delete()
    assert all(H.sha(Path(path)) == digest for path, digest in pins.items())
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_sha256": pins,
        "unique_images": len(records),
        "preview_only": args.preview,
        "dimensions": [1920, 1080],
        "cameras": cameras,
        "all_saved_geometry_preserved": True,
        "interpolated_joint_or_object_poses": False,
        "right_detail_is_static_at_first_saved_pose": True,
        "intended_display": "Repeat each saved pose for 3 frames, with 18 extra first/last frames; at 15 fps.",
        "timing_is_real_takt": False,
        "physical_acceptance_verdict": None,
        "text_elements_checked": len(composition.text_bounds),
        "images": records,
    }
    (output / "manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"H05_PROCESS_COMPLETE unique_pngs={len(records)} sources_unchanged=True video_files_created=0", flush=True)


if __name__ == "__main__":
    main()
