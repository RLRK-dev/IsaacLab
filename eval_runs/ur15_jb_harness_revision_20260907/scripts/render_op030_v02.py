# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render saved OP030 frames with native/PNG hash pairing [s]."""

import argparse
import bisect
import json
import math
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from continuous_common import ROOT, digest, write_json

parser = argparse.ArgumentParser()
parser.add_argument("--blend", default="UR15_JB_OP030_geometry_candidate_v02.blend")
parser.add_argument("--output_folder", default="op030_geometry_candidate_v02")
parser.add_argument("--views", nargs="+", default=["work", "top", "wide", "rear"])
parser.add_argument("--frames", nargs="+", type=int, default=[1])
parser.add_argument("--video", action="store_true")
parser.add_argument("--first_frame", type=int, default=1)
parser.add_argument("--last_frame", type=int)
parser.add_argument("--frame_step", type=int, default=2)
parser.add_argument("--width", type=int, default=1280)
parser.add_argument("--samples", type=int, default=16)
parser.add_argument("--engine", choices=("CYCLES", "BLENDER_EEVEE_NEXT"), default="CYCLES")
parser.add_argument(
    "--shadow_resolution_scale",
    type=float,
    default=1.0,
    help="EEVEE shadow pixel-size multiplier; larger values reduce memory and shadow detail (default: unchanged)",
)
parser.add_argument("--shot_plan")
parser.add_argument("--batch_frames", type=int, default=120)
parser.add_argument("--resume", action="store_true")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
if not math.isfinite(args.shadow_resolution_scale) or args.shadow_resolution_scale <= 0:
    parser.error("--shadow_resolution_scale must be finite and greater than zero")
if args.shadow_resolution_scale != 1.0 and args.engine != "BLENDER_EEVEE_NEXT":
    parser.error("--shadow_resolution_scale requires BLENDER_EEVEE_NEXT")
native = ROOT / args.blend
bpy.ops.wm.open_mainfile(filepath=str(native))
scene = bpy.context.scene
scene.render.engine = args.engine
if args.engine == "CYCLES":
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "OPTIX"
    preferences.get_devices()
    assert any(device.type == "OPTIX" for device in preferences.devices), "OPTIX required"
    for device in preferences.devices:
        device.use = device.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.cycles.samples = args.samples
    scene.cycles.adaptive_min_samples = min(4, args.samples)
else:
    scene.eevee.taa_render_samples = args.samples
    scene.eevee.use_raytracing = True
    scene.eevee.shadow_pool_size = "1024"
shadow_lights = []
if args.shadow_resolution_scale != 1.0:
    light_objects = [obj for obj in scene.objects if obj.type == "LIGHT"]
    lights = {obj.data.name: obj.data for obj in light_objects}
    for name, light in sorted(lights.items()):
        before = light.shadow_maximum_resolution
        energy = light.energy
        light.shadow_maximum_resolution = before * args.shadow_resolution_scale
        assert light.energy == energy
        shadow_lights.append(
            {
                "data": name,
                "type": light.type,
                "resolution_limit_before": before,
                "resolution_limit_after": light.shadow_maximum_resolution,
                "absolute_resolution": getattr(light, "use_absolute_resolution", False),
                "energy_before": energy,
                "energy_after": light.energy,
                "color": list(light.color),
                "shape": getattr(light, "shape", None),
                "size": getattr(light, "size", None),
                "size_y": getattr(light, "size_y", None),
                "use_shadow": light.use_shadow,
                "objects": [
                    {"name": obj.name, "matrix_world": [list(row) for row in obj.matrix_world]}
                    for obj in light_objects
                    if obj.data == light
                ],
            }
        )
    print("OP030_SHADOW_RESOLUTION", args.shadow_resolution_scale, len(shadow_lights), flush=True)
scene.render.use_persistent_data = True
scene.render.use_lock_interface = True
scene.render.resolution_x, scene.render.resolution_y = args.width, args.width * 9 // 16
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.compression = 15
output = ROOT / "previews" / args.output_folder
output.mkdir(parents=True, exist_ok=True)
native_frame_end = scene.frame_end
frames = (
    list(range(args.first_frame, (args.last_frame or scene.frame_end) + 1, args.frame_step))
    if args.video
    else args.frames
)
assert args.batch_frames > 0 and args.frame_step > 0 and all(1 <= frame <= native_frame_end for frame in frames)
shots = None
if "process" in args.views:
    assert args.shot_plan
    shots = json.loads((ROOT / "data" / args.shot_plan).read_text())
    assert shots["native_sha256"] == digest(native)
    assert shots["ranges"][0]["first_frame"] == 1 and shots["ranges"][-1]["last_frame"] == native_frame_end
    assert all(
        a["last_frame"] + 1 == b["first_frame"] for a, b in zip(shots["ranges"][:-1], shots["ranges"][1:], strict=True)
    )
    shot_ends = [row["last_frame"] for row in shots["ranges"]]
manifest = {
    "native": str(native.relative_to(ROOT)),
    "native_sha256": digest(native),
    "renderer_sha256": digest(Path(__file__)),
    "blender_version": bpy.app.version_string,
    "native_frame_end": native_frame_end,
    "output_fps": 30 / args.frame_step,
    "settings": {
        "width": args.width,
        "height": args.width * 9 // 16,
        "samples": args.samples,
        "engine": args.engine,
        "device": "OPTIX" if args.engine == "CYCLES" else "EEVEE",
        "native_fps": 30,
        "png_compression": 15,
        "animation_operator": bool(args.video),
        "shadow_pool_mb": 1024 if args.engine == "BLENDER_EEVEE_NEXT" else None,
    },
    "images": [],
    "complete": False,
}
if shadow_lights:
    manifest["settings"]["shadow_resolution_scale"] = args.shadow_resolution_scale
    manifest["shadow_lights"] = shadow_lights
if shots:
    manifest["shot_plan_sha256"] = digest(ROOT / "data" / args.shot_plan)
if args.resume and (output / "manifest.json").exists():
    previous = json.loads((output / "manifest.json").read_text())
    for key in ("native_sha256", "renderer_sha256", "settings", "shot_plan_sha256"):
        assert previous.get(key) == manifest.get(key), "Resume inputs differ: " + key
    for row in previous["images"]:
        assert digest(output / row["file"]) == row["sha256"]
    manifest["images"] = previous["images"]
done = {(row["view"], row["frame"]) for row in manifest["images"]}


def persist():
    temporary = output / "manifest.tmp.json"
    write_json(temporary, manifest)
    temporary.replace(output / "manifest.json")


def select_camera(scene, *_):
    selected = (
        shots["ranges"][bisect.bisect_left(shot_ends, scene.frame_current)]["camera"] if view == "process" else view
    )
    camera = bpy.data.objects["Review_OP030_" + selected]
    if scene.camera != camera:
        scene.camera = camera


def record_image(scene, *_):
    global previous_write
    path = Path(scene.render.frame_path())
    assert path.parent.resolve() == output.resolve() and path.is_file()
    frame = scene.frame_current
    assert (view, frame) not in done
    now = time.monotonic()
    manifest["images"].append(
        dict(
            file=path.name,
            frame=frame,
            view=view,
            camera=scene.camera.name.removeprefix("Review_OP030_"),
            sha256=digest(path),
            render_seconds=now - previous_write,
        )
    )
    done.add((view, frame))
    previous_write = now
    persist()
    print("OP030_FRAME", view, frame, flush=True)


for view in args.views:
    selected_frames = [frame for frame in frames if (view, frame) not in done]
    if not selected_frames:
        continue
    if args.video:
        scene.render.filepath = str(output / (view + "_#####"))
        scene.frame_step = args.frame_step
        bpy.app.handlers.frame_change_pre.append(select_camera)
        bpy.app.handlers.render_write.append(record_image)
        try:
            # Native animation rendering reuses the renderer between frames.
            # Batches leave regular cooperative stop points without dropping
            # any frames from the requested sequence.
            chunks = []
            for frame in selected_frames:
                if not chunks or len(chunks[-1]) == args.batch_frames or frame != chunks[-1][-1] + args.frame_step:
                    chunks.append([])
                chunks[-1].append(frame)
            for chunk in chunks:
                if (output / "STOP").exists():
                    raise RuntimeError("Cooperative render stop requested")
                scene.frame_start, scene.frame_end = chunk[0], chunk[-1]
                scene.frame_set(chunk[0])
                select_camera(scene)
                previous_write = time.monotonic()
                bpy.ops.render.render(animation=True)
                assert all((view, frame) in done for frame in chunk), "Render callback missed requested frames"
        finally:
            bpy.app.handlers.frame_change_pre.remove(select_camera)
            bpy.app.handlers.render_write.remove(record_image)
    else:
        for frame in selected_frames:
            if (output / "STOP").exists():
                raise RuntimeError("Cooperative render stop requested")
            scene.frame_set(frame)
            select_camera(scene)
            bpy.context.view_layer.update()
            name = f"{view}_{frame:05d}.png"
            scene.render.filepath = str(output / name)
            started = time.monotonic()
            bpy.ops.render.render(write_still=True)
            manifest["images"].append(
                {
                    "file": name,
                    "frame": frame,
                    "view": view,
                    "camera": scene.camera.name.removeprefix("Review_OP030_"),
                    "sha256": digest(output / name),
                    "render_seconds": time.monotonic() - started,
                }
            )
            done.add((view, frame))
            persist()
            print("OP030_FRAME", view, frame, flush=True)
assert all((view, frame) in done for view in args.views for frame in frames)
manifest["complete"] = True
persist()
print("OP030_RENDER_COMPLETE", len(manifest["images"]), flush=True)
