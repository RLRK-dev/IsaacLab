# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Measure floor contact per welded component around every v07c cell position [m].

Supersedes ``probe_op030_floor_datum_v07c.py``, whose three defects this avoids.

1. It classified by whole-object bounding box, so a controller whose body is a metre tall
   never reached the floor band. The one part v06 actually extended,
   ``OP030B__source_0693_m0120_p01``, was therefore invisible. This probe uses welded
   components, the same decomposition ``build_op030_stagger_supported_static_v06.py`` used
   to select that part.
2. It collected only names containing ``_foot``, missing the legs and the controller plate,
   and every gap it reported was the foot hitting its own top face.
3. Its mirrored probe points flipped X while keeping Y. The v07c mirror is
   ``M(y0): (x, y) -> (-x, 2*y0 - y)``, so the true mirror of the A feeder is 1.900 m away
   from the point that was measured.

Run: ``blender --background --python scripts/probe_op030_floor_contact_v07c.py``

Read-only. The scene is never saved and world transforms are compared before and after.
A geometric observation at its recorded timestamp, not a physical-validity verdict.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_split_v04 import _welded_components, _world_vertices  # noqa: E402
from build_op030_stagger_static_v06 import digest  # noqa: E402

SOURCE = ROOT / "UR15_JB_OP030_split_v06.blend"
SOURCE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"
REPORT = ROOT / "audit/op030_v07c_floor_contact_probe.json"

# Station Y values and the six v07c cell bases. ST pitch 2.300 m.
STATION_Y = {"ST1": -1.700, "ST2": 0.600, "ST3": 2.900}
CELL_BASES = {
    "S1L": (-0.900, -1.700),
    "S1R": (0.900, -1.700),
    "S2L": (-0.900, 0.600),
    "S2R": (0.900, 0.600),
    "S3L": (-0.900, 2.900),
    "S3R": (0.900, 2.900),
}
# Feeder and supply roots read from the scene by name, so no stale table is trusted.
SUPPLY_ROOTS = {
    "A_feeder_M4": ("OP030A_feeder_M4", "ST1"),
    "B_wire_supply": ("OP030B_wire_supply", "ST2"),
    "C_feeder_M6": ("OP030C_feeder_M6", "ST3"),
    "C_feeder_M14": ("OP030C_feeder_M14", "ST3"),
}
# A component counts as floor hardware when its underside sits within this of the floor.
CONTACT_BAND = 0.150
# Ignore slivers: a floor-bearing component covers at least this footprint.
MIN_FOOTPRINT = 0.0016
# Report components within this radius of a cell base.
CELL_RADIUS = 2.500


def mirror(point: tuple[float, float], station_y: float) -> tuple[float, float]:
    """Return the v07c mirror of a world XY across the station centre line [m]."""
    return (-point[0], 2.0 * station_y - point[1])


def flat_area(low: np.ndarray, high: np.ndarray) -> float:
    """Return the XY footprint area of a world bounding box [m^2]."""
    return float((high[0] - low[0]) * (high[1] - low[1]))


def floor_plane() -> dict:
    """Return the flat mesh with the largest footprint, taken as the floor [m]."""
    best = None
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not len(obj.data.vertices):
            continue
        world = _world_vertices(obj)
        low, high = world.min(0), world.max(0)
        if high[2] - low[2] > 1e-6 or high[2] > 0.5:
            continue
        area = flat_area(low, high)
        if best is None or area > best["area_m2"]:
            best = dict(
                name=obj.name,
                top_z_m=float(high[2]),
                area_m2=area,
                world_low_m=low.tolist(),
                world_high_m=high.tolist(),
            )
    assert best is not None, "No flat floor mesh found"
    return best


def components_near_floor(floor_z: float) -> list[dict]:
    """Return every welded component whose underside lies near the floor plane [m]."""
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not len(obj.data.vertices):
            continue
        world = _world_vertices(obj)
        if world[:, 2].min() > floor_z + CONTACT_BAND or world[:, 2].max() < floor_z - CONTACT_BAND:
            continue
        for index, indices in enumerate(_welded_components(obj.data)):
            points = world[indices]
            low, high = points.min(0), points.max(0)
            if abs(low[2] - floor_z) > CONTACT_BAND or flat_area(low, high) < MIN_FOOTPRINT:
                continue
            rows.append(
                dict(
                    object=obj.name,
                    component=index,
                    underside_z_m=float(low[2]),
                    signed_gap_m=float(low[2] - floor_z),
                    size_m=(high - low).tolist(),
                    center_xy_m=[float((low[0] + high[0]) / 2), float((low[1] + high[1]) / 2)],
                    world_low_m=low.tolist(),
                    world_high_m=high.tolist(),
                )
            )
    return rows


def near(rows: list[dict], xy: tuple[float, float]) -> list[dict]:
    """Return floor components whose centre lies within the cell radius of xy [m]."""
    picked = []
    for row in rows:
        offset = np.asarray(row["center_xy_m"]) - np.asarray(xy)
        if float(np.hypot(*offset)) <= CELL_RADIUS:
            picked.append(dict(row, distance_m=float(np.hypot(*offset))))
    return sorted(picked, key=lambda r: (round(r["signed_gap_m"], 6), r["distance_m"]))


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Measure floor contact for every cell and every mirrored supply destination."""
    assert digest(SOURCE) == SOURCE_SHA, "Probe the delivered v06 native"
    assert not REPORT.exists(), "Preserve the existing report"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    floor = floor_plane()
    floor_z = floor["top_z_m"]
    rows = components_near_floor(floor_z)

    cells = {}
    for label, xy in CELL_BASES.items():
        picked = near(rows, xy)
        cells[label] = dict(
            xy_m=list(xy),
            occupied=bool(picked),
            grounded=[r for r in picked if abs(r["signed_gap_m"]) <= 1e-5],
            floating=[r for r in picked if r["signed_gap_m"] > 1e-5],
            embedded=[r for r in picked if r["signed_gap_m"] < -1e-5],
        )

    supplies = {}
    for label, (name, station_key) in SUPPLY_ROOTS.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            supplies[label] = dict(present=False, root=name)
            continue
        origin = np.asarray(obj.matrix_world)[:3, 3]
        xy = (float(origin[0]), float(origin[1]))
        station = STATION_Y[station_key]
        supplies[label] = dict(
            present=True,
            root=name,
            world_xy_m=list(xy),
            station_y_m=station,
            mirrored_xy_m=list(mirror(xy, station)),
            components_here=near(rows, xy),
            components_at_mirror=near(rows, mirror(xy, station)),
        )

    after = transforms()
    unchanged = after == before
    gaps = sorted({round(r["signed_gap_m"], 6) for r in rows})
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                supersedes="audit/op030_v07c_floor_datum_probe.json",
                floor=floor,
                contact_band_m=CONTACT_BAND,
                min_footprint_m2=MIN_FOOTPRINT,
                cell_radius_m=CELL_RADIUS,
                mirror_rule="M(y0): (x, y) -> (-x, 2*y0 - y)",
                distinct_signed_gaps_m=gaps,
                floor_components_total=len(rows),
                cells=cells,
                supplies=supplies,
                floor_components=sorted(rows, key=lambda r: (r["object"], r["component"])),
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only welded-component floor-contact measurement at recorded positions",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
    )
    assert unchanged, "The probe must not move anything"
    print(f"floor: {floor['name']} top_z={floor_z}")
    print(f"floor components: {len(rows)}  distinct gaps [m]: {gaps}")
    for label, row in cells.items():
        counts = (len(row["grounded"]), len(row["floating"]), len(row["embedded"]))
        print(f"  {label}: grounded={counts[0]} floating={counts[1]} embedded={counts[2]}")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
