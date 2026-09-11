# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read the floor top under every v07c cell position without changing the scene [m].

Two floor datums disagree by 33 mm. ``feeder_stand`` in ``build_op030_split_v03.py`` places
each feeder foot underside at world Z 0.000, and the saved C record measures those feet
touching the floor top with a 3.632e-08 m gap. The v06 B support repair instead took the
floor to be at Z -0.033. This probe reads the actual floor top at each cell and under every
existing foot so the disagreement can be settled before v07c duplicates anything.

Run: ``blender --background --python scripts/probe_op030_floor_datum_v07c.py``

The probe opens the delivered v06 native read-only, never saves it, and writes one report.
It is a geometric observation at its recorded timestamp, not a physical-validity verdict.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_stagger_static_v06 import digest  # noqa: E402

SOURCE = ROOT / "UR15_JB_OP030_split_v06.blend"
SOURCE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"
REPORT = ROOT / "audit/op030_v07c_floor_datum_probe.json"

# Cell floor bases. ST spacing 2.300 m; the v07c mirror M(y) keeps Z, so each side is read.
CELL_BASES = {
    "S1L": (-0.900, -1.700),
    "S1R": (0.900, -1.700),
    "S2L": (-0.900, 0.600),
    "S2R": (0.900, 0.600),
    "S3L": (-0.900, 2.900),
    "S3R": (0.900, 2.900),
}
# Feeder roots from FEEDER_POSITIONS in op030_split_fastening_motion.py, with their mirrors.
FEEDER_BASES = {
    "A_M4": (-0.730, -2.650),
    "A_M4_mirrored": (0.730, -2.650),
    "C_M6": (-1.000, -2.650),
    "C_M6_mirrored": (1.000, -2.650),
    "C_M14": (-1.000, -0.750),
    "C_M14_mirrored": (1.000, -0.750),
}
PROBE_HEIGHT = 0.500
PROBE_DEPTH = 2.000
# A floor part stays below this; taller meshes are equipment and are not read as floor.
FLOOR_CEILING = 0.100
FEEDER_STAND_UNDERSIDE = 0.000
SUPPORT_REPAIR_FLOOR_Z = -0.033


def world_bounds(obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph) -> tuple[np.ndarray, np.ndarray] | None:
    """Return evaluated world bounding box corners [m], or None for non-geometry."""
    evaluated = obj.evaluated_get(depsgraph)
    try:
        mesh = evaluated.to_mesh()
    except RuntimeError:
        return None
    if mesh is None or not len(mesh.vertices):
        evaluated.to_mesh_clear()
        return None
    local = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
    matrix = np.asarray(evaluated.matrix_world)
    world = local @ matrix[:3, :3].T + matrix[:3, 3]
    evaluated.to_mesh_clear()
    return world.min(0), world.max(0)


def downward_hit(obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph, xy: tuple[float, float]) -> float | None:
    """Return the world Z where a downward ray at xy meets this object [m]."""
    evaluated = obj.evaluated_get(depsgraph)
    matrix = np.asarray(evaluated.matrix_world)
    inverse = np.linalg.inv(matrix)
    origin = inverse[:3, :3] @ np.array([xy[0], xy[1], PROBE_HEIGHT]) + inverse[:3, 3]
    direction = inverse[:3, :3] @ np.array([0.0, 0.0, -1.0])
    norm = float(np.linalg.norm(direction))
    if norm == 0.0:
        return None
    hit, location, _, _ = evaluated.ray_cast(origin.tolist(), (direction / norm).tolist(), distance=PROBE_DEPTH)
    if not hit:
        return None
    return float((matrix[:3, :3] @ np.asarray(location[:]) + matrix[:3, 3])[2])


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Probe the floor top at each cell and under each existing foot."""
    assert digest(SOURCE) == SOURCE_SHA, "Probe the delivered v06 native"
    assert not REPORT.exists(), "Preserve the existing report"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    before = transforms()
    depsgraph = bpy.context.evaluated_depsgraph_get()

    candidates, feet = [], []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        bounds = world_bounds(obj, depsgraph)
        if bounds is None:
            continue
        low, high = bounds
        if high[2] <= FLOOR_CEILING:
            candidates.append(dict(name=obj.name, world_low_m=low.tolist(), world_high_m=high.tolist()))
        if "_foot" in obj.name:
            feet.append(dict(name=obj.name, underside_z_m=float(low[2]), center_xy_m=[*((low + high) / 2)[:2]]))
    candidate_objects = [bpy.data.objects[row["name"]] for row in candidates]

    def top_at(xy: tuple[float, float]) -> dict:
        """Return every floor candidate hit under xy, highest first [m]."""
        hits = []
        for obj in candidate_objects:
            z = downward_hit(obj, depsgraph, xy)
            if z is not None:
                hits.append(dict(object=obj.name, top_z_m=z))
        hits.sort(key=lambda row: row["top_z_m"], reverse=True)
        return dict(xy_m=list(xy), hits=hits, top_z_m=hits[0]["top_z_m"] if hits else None)

    cells = {label: top_at(xy) for label, xy in CELL_BASES.items()}
    feeders = {label: top_at(xy) for label, xy in FEEDER_BASES.items()}
    for row in feet:
        beneath = top_at(tuple(row["center_xy_m"]))
        row["floor_top_z_m"] = beneath["top_z_m"]
        row["signed_gap_m"] = None if beneath["top_z_m"] is None else row["underside_z_m"] - beneath["top_z_m"]

    after = transforms()
    unchanged = after == before
    tops = [row["top_z_m"] for row in (*cells.values(), *feeders.values()) if row["top_z_m"] is not None]
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                probe_height_m=PROBE_HEIGHT,
                probe_depth_m=PROBE_DEPTH,
                floor_ceiling_m=FLOOR_CEILING,
                floor_candidates=sorted(candidates, key=lambda row: row["name"]),
                cells=cells,
                feeders=feeders,
                feet=sorted(feet, key=lambda row: row["name"]),
                distinct_floor_tops_m=sorted({round(z, 6) for z in tops}),
                datums_under_test=dict(
                    feeder_stand_underside_m=FEEDER_STAND_UNDERSIDE,
                    support_repair_floor_z_m=SUPPORT_REPAIR_FLOOR_Z,
                    difference_m=FEEDER_STAND_UNDERSIDE - SUPPORT_REPAIR_FLOOR_Z,
                ),
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only downward ray probe of floor candidates at recorded positions",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
    )
    assert unchanged, "The probe must not move anything"
    print(f"distinct floor tops [m]: {sorted({round(z, 6) for z in tops})}")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
