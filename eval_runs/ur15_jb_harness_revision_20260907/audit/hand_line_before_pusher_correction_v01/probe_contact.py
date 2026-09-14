# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare saved OP020 pusher and connector planes before and after correction [m]."""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bounds(name):
    obj = bpy.context.scene.objects[name]
    return [obj.matrix_world @ Vector(vertex) for vertex in obj.bound_box]


report = {"units": "m", "formal_physical_validity_verdict": None, "versions": {}}
for version in ("v01", "v02"):
    native = ROOT / f"UR15_JB_initial_hands_{version}.blend"
    identity = digest(native)
    bpy.ops.wm.open_mainfile(filepath=str(native))
    rows = []
    for frame in range(625, 662, 3):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        face = bounds("OP020_push_face")
        shell = bounds("OP020_handled_connector_shell")
        rod = bounds("OP020_push_rod_mesh")
        cylinder = bounds("OP020_fixed_pusher_-1_body")
        rows.append(
            {
                "frame": frame,
                "signed_plane_gap_y_m": min(v.y for v in shell) - max(v.y for v in face),
                "rod_cylinder_axial_overlap_m": min(max(v.y for v in rod), max(v.y for v in cylinder))
                - max(min(v.y for v in rod), min(v.y for v in cylinder)),
            }
        )
    assert digest(native) == identity
    report["versions"][version] = {"native_sha256": identity, "read_only": True, "samples": rows}
output = ROOT / "audit/hand_line_review_v01_pusher_correction.json"
assert not output.exists(), output
output.write_text(json.dumps(report, indent=2) + "\n")
print("PUSHER_CORRECTION_OBSERVED", output, flush=True)
