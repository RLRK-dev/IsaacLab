# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build a native, persistent single-end harness assembly review [m, s]."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allocation_product import empty  # noqa: E402
from build_allocation_review import camera  # noqa: E402
from continuous_common import (  # noqa: E402
    ROOT,
    action_world,
    camera_settings,
    delete_tree,
    digest,
    look_at,
    write_json,
)
from jb_harness import build_jb_product, frame_object  # noqa: E402
from op020_jb_geometry import box, harness, lever_clip, magazine, materials, protective_cap, support_tray  # noqa: E402

PLAYBACK_SCALE = 1.5
BLEND_NAME = "UR15_JB_OP020_v09.blend"
LEVER_PIVOT = np.array([0, -0.022, 0.0563])


def animate_channels(obj, property_name, values, frames):
    """Bake local scalar/vector channels at explicit animation frames."""
    values = np.asarray(values)
    if values.ndim == 1:
        values = values[:, None]
    if obj.animation_data is None:
        obj.animation_data_create()
    action = obj.animation_data.action
    if action is None:
        action = bpy.data.actions.new(obj.name + "_local_motion")
        obj.animation_data.action = action
    for index in range(values.shape[1]):
        curve = action.fcurves.new(property_name, index=index)
        curve.keyframe_points.add(len(frames))
        curve.keyframe_points.foreach_set("co", np.column_stack((frames, values[:, index])).astype(np.float32).ravel())
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"
        curve.update()
    if action.slots:
        obj.animation_data.action_slot = action.slots[0]


def smooth(times, start, stop):
    x = np.clip((times - start) / (stop - start), 0, 1)
    return x**3 * (10 - 15 * x + 6 * x * x)


def freeze_background(scene):
    """Freeze reference stations at the previous review pose."""
    scene.frame_set(595)
    bpy.context.view_layer.update()
    for obj in list(scene.objects):
        basis = obj.matrix_basis.copy()
        obj.animation_data_clear()
        obj.matrix_basis = basis
        if obj.type == "MESH" and obj.data.shape_keys:
            obj.data.shape_keys.animation_data_clear()
    scene["background_scope"] = "Other stations frozen at the source frame 595; not a continuous full-line run"


def cap_receiver():
    """Support both cap edges with the pull-tab and finger corridor open [m]."""
    root = empty("OP020_cap_recovery_pocket")
    mats = materials()
    cx, cy = 0.45, -2.85 + 0.85
    box(root.name + "_foot", (0.18, 0.20, 0.012), (cx - 0.10, cy, 0.006), mats["metal"], root)
    box(root.name + "_post", (0.06, 0.06, 0.844), (cx - 0.10, cy, 0.434), mats["metal"], root)
    box(root.name + "_rear_beam", (0.075, 0.020, 0.014), (cx - 0.0675, cy, 0.863), mats["blue"], root)
    box(root.name + "_rear_crossbar", (0.016, 0.084, 0.014), (cx - 0.035, cy, 0.863), mats["blue"], root)
    for sign in (-1, 1):
        y = cy + sign * 0.026
        box(root.name + f"_seat_post{sign}", (0.016, 0.010, 0.0175), (cx - 0.035, y, 0.87875), mats["blue"], root)
        box(root.name + f"_edge_seat{sign}", (0.039, 0.010, 0.006), (cx - 0.0185, y, 0.8875), mats["black"], root)
        for label, x in (("back", cx - 0.0029),):
            box(root.name + f"_edge_guide_{label}{sign}", (0.0028, 0.010, 0.028), (x, y, 0.9045), mats["blue"], root, 0)
    root["fixture_scope"] = "provisional open edge cradle; retention and rigidity require engineering"
    return root


def main():
    source = ROOT / "UR15_JB_line_enclosed_v05.blend"
    motion_path = ROOT / "data/op020_jb_motion.npz"
    checks = json.loads((ROOT / "audit/op020_jb_motion_checks.json").read_text())
    if checks["failures"]:
        raise RuntimeError("The motion still contains unresolved IK targets")
    with np.load(motion_path) as data:
        motion = {key: data[key].copy() for key in data.files}
    times = motion["times"]
    # Slow unloaded reorientation to an explicit animation speed envelope.
    # This is review timing, not a prediction of production takt or dynamics.
    delta_q = np.diff(motion["joints"], axis=0)
    review_limits = np.array([1.5, 1.5, 2.0, 2.5, 2.5, 2.5])
    dt = np.maximum(np.diff(times) * PLAYBACK_SCALE, (abs(delta_q) / review_limits).max(axis=(1, 2)))
    padded = np.pad(dt, 6, mode="edge")
    widened = np.maximum.reduce([padded[i : i + len(dt)] for i in range(13)])
    softened = np.convolve(np.pad(widened, 3, mode="edge"), np.ones(7) / 7, mode="valid")
    dt = np.maximum(dt, softened)
    seconds = np.r_[0, np.cumsum(dt)]
    frames = seconds * 30 + 1
    np.savez_compressed(ROOT / "data/op020_timeline.npz", author_times=times, seconds=seconds, frames=frames)
    velocity = delta_q / dt[:, None, None]
    joint_limits = np.radians([360, 360, 180, 360, 360, 360])
    velocity_limits = np.radians([180, 180, 240, 300, 300, 300])
    assert (abs(motion["joints"]) <= joint_limits).all()
    assert (abs(velocity) <= velocity_limits).all()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.name = "OP020_JB_single_end_review"
    freeze_background(scene)
    removed_panels = sorted(obj.name for obj in scene.objects if obj.name.startswith("Enclosure_clear_"))
    assert len(removed_panels) == 91
    for name in removed_panels:
        obj = bpy.data.objects[name]
        assert not obj.children, "Panel removal must preserve separate frame objects"
        bpy.data.objects.remove(obj, do_unlink=True)
    scene["enclosure_scope"] = "Transparent panels removed by user request; frame structure retained"
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= 2.0
    scene["external_led_power_relative_v06"] = 2.0
    eyes = sorted(obj.name for obj in scene.objects if obj.type == "CAMERA" and obj.name.startswith("Eye_"))
    eye_settings = camera_settings(eyes)
    product = build_jb_product(bpy.data.objects["source_0293"], "JB_OP020_UID001", stage=1)
    frame_object(product, np.diag([-1, -1, 1]), (0, -2.85, 0.5345))
    product["persistent_assembly"] = "Housing stays on the same pallet throughout this isolated OP020 review"
    removed = []
    for number in [*range(293, 316), 997, 1037, 1683]:
        obj = bpy.data.objects.get(f"source_{number:04d}")
        if obj:
            removed.append(obj.name)
            delete_tree(obj)
    stock_roots = [
        obj
        for obj in scene.objects
        if obj.name.startswith("stocker10_") and not (obj.parent and obj.parent.name.startswith("stocker10_"))
    ]
    for obj in stock_roots:
        removed.append(obj.name)
        delete_tree(obj)
    pallet = bpy.data.objects["source_0292"]
    pallet.location = (0, -2.85, 0.439)
    assembly, plug_a, _ = harness("OP020_harness_UID001")
    tray, clamp_pivots, recovery = support_tray("OP020_active_support_tray")
    cap = protective_cap("OP020_recovered_A_cap")
    clip = lever_clip("OP020_recovered_lever_tool")
    for obj, key in ((assembly, "harness"), (tray, "tray"), (cap, "cap"), (clip, "clip")):
        action_world(obj, motion[key], frames)
    lever = bpy.data.objects[plug_a.name + "_lever"]
    lever.rotation_mode = "XYZ"
    rotations = np.zeros((len(times), 3))
    rotations[:, 0] = motion["lever"]
    animate_channels(lever, "rotation_euler", rotations, frames)
    animate_channels(bpy.data.objects[plug_a.name + "_CPA"], "location", motion["cpa"], frames)
    for pivot in clamp_pivots:
        positions = np.zeros((len(times), 3))
        positions[:, 2] = 0.060 * smooth(times, 46, 48)
        animate_channels(pivot, "location", positions, frames)
    for obj, sign, center in recovery:
        positions = np.repeat(np.asarray(obj.location)[None, :], len(times), axis=0)
        positions[:, 2] = center + sign * (0.022 - 0.014 * smooth(times, 47.6, 47.9))
        animate_channels(obj, "location", positions, frames)
    slide = bpy.data.objects["OP020_active_support_tray_tool_recovery_slide"]
    positions = np.zeros((len(times), 3))
    positions[:, 1] = 0.20 * (1 - smooth(times, 47.2, 47.4))
    animate_channels(slide, "location", positions, frames)
    insertion = bpy.data.objects["OP020_active_support_tray_tool_recovery_insertion"]
    positions = np.zeros((len(times), 3))
    positions[:, 0] = -0.06 * smooth(times, 47, 47.2) * (1 - smooth(times, 47.4, 47.6))
    animate_channels(insertion, "location", positions, frames)
    for index, node in enumerate(motion["node_ids"]):
        obj = bpy.data.objects[f"source_{int(node):04d}"]
        if obj.parent:
            raise RuntimeError(f"Source node unexpectedly parented: {obj.name}")
        action_world(obj, motion["poses"][:, index], frames)
    _, receiver = magazine()
    for pivot in receiver:
        angles = np.zeros((len(times), 3))
        angles[:, 1] = -math.pi / 2 * (1 - smooth(times, 64, 65))
        animate_channels(pivot, "rotation_euler", angles, frames)
    cap_receiver()
    rotation_stock = np.asarray(Matrix.Rotation(-math.pi / 2, 3, "Y"))
    for level in range(9):
        height = 0.12 + 0.110 * level
        stock_tray, _, _ = support_tray(f"OP020_stock_tray_{level + 1:02d}")
        stock_harness, stock_a, _ = harness(f"OP020_stock_harness_{level + 1:02d}")
        for obj in (stock_tray, stock_harness):
            frame_object(obj, rotation_stock, (1.98, -2.79, height + 0.338))
        stock_cap = protective_cap(f"OP020_stock_cap_{level + 1:02d}")
        stock_cap.parent = stock_a
        stock_clip = lever_clip(f"OP020_stock_lever_tool_{level + 1:02d}")
        stock_clip.parent = stock_a
        stock_clip.location = LEVER_PIVOT
    # Review cameras are separate from the unchanged on-hand camera calibration.
    views = {
        "wide": ((2.78, -5.08, 2.45), (0.78, -2.85, 1.05), 32),
        "stock": ((2.78, -4.30, 2.0), (1.72, -2.84, 1.05), 34),
        "mate": ((-0.18, -2.25, 1.00), (0.32, -2.55, 0.59), 45),
        "lock": ((0.08, -2.05, 1.22), (0.36, -2.55, 0.62), 53),
        "cap": ((1.02, -2.78, 1.32), (0.45, -2.00, 0.91), 48),
        "finished": ((-0.08, -1.95, 1.60), (0.18, -2.65, 0.64), 36),
        "return": ((3.36, -2.83, 3.03), (1.56, -2.68, 1.33), 40),
    }
    for suffix, (eye, target, lens) in views.items():
        obj = camera(scene, "Review_OP020_" + suffix, eye, target, lens)
        if suffix in {"mate", "lock"}:
            poses = []
            for height in motion["harness"][:, 2, 3]:
                delta = np.array([0, 0, height - 0.5345])
                poses.append(np.asarray(look_at(np.asarray(eye) + delta, np.asarray(target) + delta)))
            action_world(obj, np.asarray(poses), frames)
        elif suffix == "return":
            poses = []
            for tray_pose in motion["tray"]:
                target = (tray_pose @ np.array([-0.340, 0.1075, 0.215, 1]))[:3]
                eye = target + np.array([1.8, -0.15, 1.7])
                poses.append(np.asarray(look_at(eye, target)))
            action_world(obj, np.asarray(poses), frames)
    for obj in scene.objects:
        if obj.type in {"MESH", "CURVE"} and not obj.name.startswith("Enclosure_clear_"):
            obj.cycles.is_caustics_receiver = True
    assert camera_settings(eyes) == eye_settings
    assert len(eyes) == 19
    assert not any(obj.type == "LIGHT" and obj.data.type in {"POINT", "SPOT"} for obj in scene.objects)
    scene.frame_start, scene.frame_end = 1, math.ceil(frames[-1])
    scene.render.fps = 30
    scene.camera = bpy.data.objects["Review_OP020_wide"]
    scene["review_scope"] = "One supported harness assembly; 9 reserve trays; lower pallet return not modeled"
    scene["playback_time_scale"] = PLAYBACK_SCALE
    scene["cycle_time_is_production_takt"] = False
    scene.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / BLEND_NAME), compress=True)
    write_json(
        ROOT / "audit/op020_native_build.json",
        {
            "input_scene": source.name,
            "input_sha256": digest(source),
            "motion_sha256": digest(motion_path),
            "output_scene": BLEND_NAME,
            "output_sha256": digest(ROOT / BLEND_NAME),
            "duration_s": float(seconds[-1]),
            "timeline_fps": 30,
            "last_frame": scene.frame_end,
            "motion_samples": len(times),
            "max_joint_speed_rad_s": abs(velocity).max(axis=0).tolist(),
            "camera_count": len(eyes),
            "camera_mounts_intrinsics_preserved": True,
            "external_led_power_relative_v06": 2.0,
            "removed_transparent_panels": removed_panels,
            "bimanual_empty_tray_return_author_s": [48, 66],
            "removed_old_objects": removed,
            "assembly_uid": assembly.name,
            "stock_capacity": 10,
            "remaining_stock": 9,
            "two_level_pallet_return_implemented": False,
            "views": views,
            "phases": [[float(np.interp(t, times, seconds)), label] for t, label in checks["phases"]],
            "timing": "At least 1.5 times authoring time; slower where needed to meet the review speed envelope",
            "limitations": [
                "Other stations are a static reference",
                "One cycle only; magazine indexing not animated",
                "Clamp actuation and connector lock are provisional geometry",
                "No contact-force or physical-validity verdict",
            ],
        },
    )
    print("OP020_NATIVE_SCENE_SAVED", ROOT / BLEND_NAME, flush=True)


if __name__ == "__main__":
    main()
