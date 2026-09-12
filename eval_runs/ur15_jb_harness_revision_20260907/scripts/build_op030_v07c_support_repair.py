# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bring A's M4 feeder supports and the A and C controller plates down to the floor [m].

Work 2 of v07c. The floor probe measured three defects the duplication must not carry into
three more cells:

* ``OP030A_feeder_M4_foot_*`` x2 float 33 mm. B and C were lowered already; A was not.
* ``OP030A_feeder_M4_stand_*`` x2 stand on those feet, so they follow by 33 mm (634 -> 667).
* The controller lower plate, welded component 2 of ``source_0693_m0120_p01``, floats 38 mm
  on A and on C. v06 extended only B's copy, 30 -> 68 mm.

The repair goes into the originals before anything is duplicated, so the copies inherit it.
Method and tolerances are v06's: ``extend_lower`` holds the upper surface and the footprint
and moves only the underside, and the feet translate. Nothing here is measured from a table;
every target is found in the scene, every distance is derived from what is measured there,
and the result is verified against the floor before the file is saved.

The controller plate is the one place where two objects may share a mesh datablock. If A and
C share one, the repair is applied once and C is pointed at the repaired data, so the two
stay identical. If they do not, each is repaired on its own. Either way both are measured
afterwards. Every other user of an edited datablock is recorded before the edit, and the
unchanged-object check will name it if the edit reached further than intended.

Run: ``blender --background --python scripts/build_op030_v07c_support_repair.py``

Reads the delivered v06 native and never writes to it. Writes one new candidate and one
manifest. A geometric construction at its recorded timestamp, not a physical-validity verdict.
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
from build_op030_stagger_static_v06 import digest, geometry, snapshot  # noqa: E402
from build_op030_stagger_supported_static_v06 import extend_lower  # noqa: E402

SOURCE = ROOT / "UR15_JB_OP030_split_v06.blend"
SOURCE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"
OUTPUT = ROOT / "analysis/op030_v07c_support_repair.blend"
MANIFEST = ROOT / "audit/op030_v07c_support_repair.json"

# The floor top the probe measured, uniform across the line.
FLOOR_Z = -0.033
# A's feeder, the only one still standing on the old datum.
FEEDER_ROOT = "OP030A_feeder_M4"
FEEDER_FOOT = FEEDER_ROOT + "_foot_"
FEEDER_STAND = FEEDER_ROOT + "_stand_"
FEEDER_FEET_EXPECTED = 2
# The controller lower plate, addressed exactly as v06 addressed B's.
PLATES = ("source_0693_m0120_p01", "OP030C__source_0693_m0120_p01")
PLATE_SIZE_M = (0.42, 0.44, 0.03)
PLATE_UNDERSIDE_M = 0.005
TOLERANCE = 2e-6


def users_of(obj: bpy.types.Object) -> list[str]:
    """Return every object sharing this object's mesh datablock, itself included."""
    return sorted(other.name for other in bpy.data.objects if other.data is obj.data)


def underside(obj: bpy.types.Object, indices: np.ndarray | None = None) -> float:
    """Return the lowest world Z of an object, or of one welded component [m]."""
    world = _world_vertices(obj)
    return float(world[:, 2].min() if indices is None else world[indices][:, 2].min())


def topside(obj: bpy.types.Object) -> float:
    """Return the highest world Z of an object [m]."""
    return float(_world_vertices(obj)[:, 2].max())


def feeder_pairs() -> list[tuple[bpy.types.Object, bpy.types.Object]]:
    """Return A's (foot, stand) pairs, matched by the position suffix that names them."""
    feet = {o.name[len(FEEDER_FOOT) :]: o for o in bpy.data.objects if o.name.startswith(FEEDER_FOOT)}
    stands = {o.name[len(FEEDER_STAND) :]: o for o in bpy.data.objects if o.name.startswith(FEEDER_STAND)}
    assert len(feet) == FEEDER_FEET_EXPECTED, f"{FEEDER_ROOT}: {len(feet)} feet, expected {FEEDER_FEET_EXPECTED}"
    assert set(feet) == set(stands), f"{FEEDER_ROOT}: feet and stands do not pair up"
    return [(feet[key], stands[key]) for key in sorted(feet)]


def lower_foot(foot: bpy.types.Object) -> dict:
    """Translate one foot down in world Z until its underside reaches the floor [m]."""
    before_low, before_high = underside(foot), topside(foot)
    drop = before_low - FLOOR_Z
    assert drop > TOLERANCE, f"{foot.name}: already at or below the floor"
    matrix = foot.matrix_world.copy()
    matrix.translation.z -= drop
    foot.matrix_world = matrix
    bpy.context.view_layer.update()
    return dict(
        name=foot.name,
        kind="foot_translation",
        displacement_world_m=[0.0, 0.0, -drop],
        before_underside_m=before_low,
        before_topside_m=before_high,
        after_underside_m=underside(foot),
        after_topside_m=topside(foot),
        shares_mesh_with=users_of(foot),
    )


def plate_component(obj: bpy.types.Object) -> np.ndarray:
    """Return the vertex indices of the controller lower plate, v06's own predicate."""
    world = _world_vertices(obj)
    picked = [
        indices
        for indices in _welded_components(obj.data)
        if np.allclose(np.ptp(world[indices], axis=0), PLATE_SIZE_M, atol=TOLERANCE)
        and abs(world[indices][:, 2].min() - PLATE_UNDERSIDE_M) < TOLERANCE
    ]
    assert len(picked) == 1, f"{obj.name}: {len(picked)} components match the lower plate, expected 1"
    return picked[0]


def repair_feeder(records: list[dict], verify: list[dict]) -> list[str]:
    """Lower A's feet to the floor and extend its stands down onto them."""
    moved = []
    for foot, stand in feeder_pairs():
        records.append(lower_foot(foot))
        moved.append(foot.name)
        target = topside(foot)
        indices = np.arange(len(stand.data.vertices))
        before_length = topside(stand) - underside(stand)
        record = extend_lower(stand, indices, target)
        record["shares_mesh_with"] = users_of(stand)
        record["before_length_m"] = before_length
        record["after_length_m"] = topside(stand) - underside(stand)
        records.append(record)
        verify.append(dict(name=foot.name, indices=None, expect_m=FLOOR_Z, why="foot on the floor"))
        verify.append(dict(name=stand.name, indices=None, expect_m=target, why="stand on its foot"))
    return moved


def repair_plates(records: list[dict], verify: list[dict]) -> None:
    """Extend the A and C controller lower plates down to the floor [m]."""
    first, second = (bpy.data.objects[name] for name in PLATES)
    shared = first.data is second.data
    indices = plate_component(first)
    second_indices = indices if shared else plate_component(second)
    record = extend_lower(first, indices, FLOOR_Z)
    record["shares_mesh_with_before_edit"] = sorted({*PLATES} if shared else users_of(first))
    record["shared_with_second"] = shared
    records.append(record)
    if shared:
        second.data = first.data
        records.append(
            dict(
                name=second.name,
                kind="shared_datablock_follow",
                follows=first.name,
                selected_vertex_indices=indices.tolist(),
                note="A and C held one mesh; the repair was applied once and C now points at it",
            )
        )
    else:
        records.append(extend_lower(second, second_indices, FLOOR_Z))
    for name, picked in ((first.name, indices), (second.name, second_indices)):
        verify.append(dict(name=name, indices=picked.tolist(), expect_m=FLOOR_Z, why="lower plate on the floor"))


def main() -> None:
    """Repair the four supports, verify every one against the floor, and save."""
    assert digest(SOURCE) == SOURCE_SHA, "Repair the delivered v06 native"
    assert not any(path.exists() for path in (OUTPUT, MANIFEST)), "Preserve existing candidates"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = snapshot()

    records: list[dict] = []
    verify: list[dict] = []
    moved = repair_feeder(records, verify)
    repair_plates(records, verify)
    bpy.context.view_layer.update()

    checks = []
    for row in verify:
        obj = bpy.data.objects[row["name"]]
        indices = None if row["indices"] is None else np.asarray(row["indices"])
        measured = underside(obj, indices)
        evaluated = float(geometry(obj)[0][:, 2].min()) if indices is None else None
        error = measured - row["expect_m"]
        checks.append(dict(row, measured_underside_m=measured, evaluated_underside_m=evaluated, error_m=error))
    for check in checks:
        assert abs(check["error_m"]) < TOLERANCE, f"{check['name']}: underside off by {check['error_m']} m"

    after = snapshot()
    changed = {record["name"] for record in records}
    assert set(before) == set(after), "The repair must not add or remove objects"
    for name in before:
        assert before[name]["parent"] == after[name]["parent"], name
        if name not in changed:
            assert before[name] == after[name], f"{name} changed without being a repair target"
        elif name not in moved:
            assert before[name]["world"] == after[name]["world"], f"{name} moved; only feet may move"

    binding = dict(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        scope="A feeder feet and stands, and the A and C controller lower plates; no other geometry",
        floor_z_m=FLOOR_Z,
        records=records,
        checks=checks,
        changed_objects=sorted(changed),
        translated_objects=sorted(moved),
        object_count_unchanged=len(before),
        unchanged_objects=len(before) - len(changed),
        added_objects_count=0,
        cabinet_body_float_left_open=["source_0693_m0120_p00", "source_0693_m0120_p04"],
        cabinet_body_note="Out of scope by v07c section 7.3; a line-wide item awaiting adjudication",
    )
    bpy.context.scene["op030_v07c_support_repair"] = json.dumps(binding)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)

    MANIFEST.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                builder=str(Path(__file__).relative_to(ROOT)),
                builder_sha256=digest(Path(__file__)),
                output=str(OUTPUT.relative_to(ROOT)),
                output_sha256=digest(OUTPUT),
                support_repair=binding,
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    assert digest(SOURCE) == SOURCE_SHA, "The delivered v06 native must be untouched"
    for record in records:
        print(f"  {record['kind']}: {record['name']}")
    for check in checks:
        print(f"  check {check['name']}: underside={check['measured_underside_m']:.6f} error={check['error_m']:.2e}")
    print(f"V07C_SUPPORT_REPAIR_SAVED {digest(OUTPUT)} changed={len(changed)}")
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
