# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe the saved header revision without a physical acceptance verdict."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from continuous_common import ROOT, digest, write_json
from probe_hand_line_review_v01 import arm_objects, compare, surface


def groups_and_pairs():
    scene = bpy.context.scene
    arm = arm_objects("OP020")
    groups = {
        "arm": arm,
        "arm_without_contact_pads": [o for o in arm if o.get("contact_role") != "contact_pad"],
        "distal_arm": arm_objects("OP020", distal=True),
        "headers": [o for o in scene.objects if o.name.startswith(("OP020_handled_TE_", "OP020_TE_supply_spare_"))],
        "driver": [o for o in scene.objects if o.name.startswith("OP020_screwdriver_")],
        "fixture": [
            o
            for o in scene.objects
            if o.name.startswith(
                (
                    "OP020_distinct_workpiece",
                    "OP020_header_supply",
                    "OP020_header_pick_support",
                    "OP020_header_spare_support",
                )
            )
        ],
        "column": [o for o in scene.objects if o.name.startswith("OP020_single_")],
        "driver_support": [o for o in scene.objects if o.name.startswith(("OP020_driver_", "OP020_M4_screw_feeder"))],
    }
    pairs = [
        ("arm", "driver"),
        ("arm_without_contact_pads", "headers"),
        ("arm", "fixture"),
        ("distal_arm", "column"),
        ("arm", "driver_support"),
        ("driver", "headers"),
    ]
    return groups, pairs


def snapshot_unchanged(frames, names):
    rows = {}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        rows[str(frame)] = {name: np.array(bpy.data.objects[name].matrix_world).tolist() for name in names}
    return rows


def contact_observations(schedule):
    records = []
    for index, item in enumerate(schedule):
        frame = round((12 + item["start"] + 0.3) * 30) + 1
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        root = bpy.data.objects["OP020_handled_TE_" + str(item["header"])]
        tool = bpy.data.objects["OP020_screwdriver"]
        bolt = bpy.data.objects[f"OP020_M4_{index + 1:02d}"]
        pads = [bpy.data.objects["OP020__hand__" + side + "_header_pad"] for side in ("left_left", "left_right")]
        width = (0.1132, 0.0793)[item["header"]]
        pad_rows = []
        for sign, obj in zip((-1, 1), pads, strict=True):
            m = np.array(root.matrix_world.inverted() @ obj.matrix_world)
            p = np.array([v.co[:] for v in obj.data.vertices]) @ m[:3, :3].T + m[:3, 3]
            inward_x = p[:, 0].max() if sign < 0 else p[:, 0].min()
            pad_rows.append(
                {
                    "name": obj.name,
                    "side_contact_x_error_m": float(inward_x - sign * width / 2),
                    "bounds_in_header_datum_m": [p.min(0).tolist(), p.max(0).tolist()],
                }
            )
        records.append(
            {
                "frame": frame,
                "screw": index + 1,
                "header": item["header"],
                "driver_reference_to_bolt_head_reference_m": (tool.location - bolt.location).length,
                "bit_end_forward_of_driver_reference_m": 0.003,
                "header_plane_y_m": root.location.y,
                "header_world_position_m": list(root.location),
                "pads": pad_rows,
            }
        )
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="p01")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    stem = "header_review_v03_" + args.revision
    build = json.loads((ROOT / ("audit/" + stem + "_build.json")).read_text())
    native = ROOT / build["native"]
    assert digest(native) == build["native_sha256"]
    schedule = json.loads((ROOT / "audit/header_review_v03_prepare.json").read_text())["display_bolt_schedule"]
    names = [
        f"{arm}__{link}"
        for arm in ("A_hold", "A_tool", "B_left", "B_right", "C")
        for link in ("base", "shoulder", "upper_arm", "forearm", "wrist_1", "wrist_2", "wrist_3", "flange")
    ]
    old_frames = [1, 181, 781, 973, 1111, 1201, 1417, 1549, 1801, 2039]
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "UR15_JB_initial_hands_v02.blend"))
    before = snapshot_unchanged(old_frames, names)
    bpy.ops.wm.open_mainfile(filepath=str(native))
    after = snapshot_unchanged([f + 780 if f >= 781 else f for f in old_frames], names)
    errors = []
    for frame in old_frames:
        shifted = frame + 780 if frame >= 781 else frame
        for name in names:
            errors.append(float(abs(np.array(before[str(frame)][name]) - np.array(after[str(shifted)][name])).max()))
    assert max(errors) < 1e-7, "Other arm transforms changed beyond retiming"
    groups, pairs = groups_and_pairs()
    times = sorted(
        set(
            [*np.arange(12, 46.1, 0.6), 13.8, 18.2, 26.8, 27.45, 28.6, 31.8, 36.8, 43.5, 44.15, 45.3]
            + [12 + r["start"] + 0.3 for r in schedule]
        )
    )
    results = {a + "/" + b: [] for a, b in pairs}
    for index, seconds in enumerate(times):
        frame = round(seconds * 30) + 1
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        dep = bpy.context.evaluated_depsgraph_get()
        surfaces = {name: surface(objects, dep) for name, objects in groups.items()}
        for a, b in pairs:
            hits = compare(surfaces[a], surfaces[b])
            if hits:
                results[a + "/" + b].append({"frame": frame, "object_surface_pairs": hits})
        if index % 10 == 0:
            print("HEADER_PROBE", index, "/", len(times), flush=True)
    report = {
        "native": native.name,
        "native_sha256": digest(native),
        "sampled_frames": [round(t * 30) + 1 for t in times],
        "group_counts": {k: len(v) for k, v in groups.items()},
        "surface_intersections": results,
        "fastening_alignment": contact_observations(schedule),
        "retimed_other_arms_max_matrix_difference": max(errors),
        "comparison_old_frames": old_frames,
        "physical_validity_verdict": None,
        "alignment_definition": (
            "Driver root datum versus screw-head front datum; the modeled bit end is 3 mm forward of this datum."
        ),
        "limits": (
            "Sampled surface intersections only; intended pad/header contacts are separately measured. "
            "No containment or continuous/load verdict."
        ),
    }
    write_json(ROOT / ("audit/" + stem + "_probe.json"), report)
    print("HEADER_PROBE_COMPLETE", {k: len(v) for k, v in results.items()}, flush=True)


if __name__ == "__main__":
    main()
