# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Map v06's recorded B selection onto A and C, for the v07c mirror copies [m].

Third attempt, and the first that stops inferring the selection from the scene. Two readings
of the scene were tried and both missed:

* ``descendants(OP030B_cell)`` gave 64 objects against v06's 420. The relocated set is not
  the cell subtree; ``build_op030_stagger_static_v06.py`` re-parented curated roots away from
  it, and four of them were never cell children at all.
* ``descendants(OP030B_robot_supply_stagger_root)`` gave 125 with only 16 direct children
  against the 108 roots v06 parented there. The delivered native is several steps past that
  candidate -- support repair, air clearance, then a portable rebake -- and the hierarchy no
  longer matches.

The selection does not need inferring. v06 read it from
``analysis/op040_stagger_layout_inventory.json`` and recorded that file's SHA alongside the
result. This reads the same key, checks it against the scene, and maps each member to its A
and C counterpart through the naming ``duplicate_set`` established: ``OP030B__<source>``
corresponds to ``<source>`` on A and ``OP030C__<source>`` on C.

The inventory is local working material and is not in Git. A missing file stops the run.

Run: ``blender --background --python scripts/build_op030_v07c_cell_selection.py``

Read-only. The scene is never saved and world transforms are compared before and after.
A structural observation at its recorded timestamp, not a physical-validity verdict.
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
from op030_split_layout import descendants  # noqa: E402

SOURCE = ROOT / "UR15_JB_OP030_split_v06.blend"
SOURCE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"
INVENTORY = ROOT / "analysis/op040_stagger_layout_inventory.json"
REPORT = ROOT / "analysis/op030_v07c_cell_selection.json"

# The air drops v06 appended to the inventory roots before relocating.
DROPS = [f"Split_bay_1__source_0783_m0210_p{index:02d}" for index in range(4)]
V06_ROOTS = 104
V06_MOVED = 420
V06_FIXED = 76
# The candidate group v06 created. Read only to record how far the native has drifted.
STAGGER_GROUP = "OP030B_robot_supply_stagger_root"
COPY_PREFIX = "OP030B__"
BONLY_PREFIX = "OP030B_"
TARGETS = {"A": "", "C": "OP030C__"}


def kind_of(name: str) -> str:
    """Classify a selected name by whether a per-cell counterpart can exist."""
    if name.startswith(COPY_PREFIX):
        return "cell_copy"
    if name.startswith(BONLY_PREFIX):
        return "b_only_hardware"
    return "bay_service"


def source_of(name: str) -> str:
    """Return the original name a B copy was made from."""
    return name[len(COPY_PREFIX) :] if name.startswith(COPY_PREFIX) else name


def describe(obj: bpy.types.Object) -> dict:
    """Return the identity fields needed to rebuild this object elsewhere [m]."""
    return dict(
        name=obj.name,
        type=obj.type,
        parent=obj.parent.name if obj.parent else None,
        world_translation_m=np.asarray(obj.matrix_world)[:3, 3].tolist(),
    )


def structure(names: set[str]) -> dict:
    """Apply v06's structural conditions to a set of existing object names."""
    objects = [bpy.data.objects[name] for name in sorted(names) if name in bpy.data.objects]
    roots = [obj for obj in objects if obj.parent is None or obj.parent.name not in names]
    reached = {o.name for root in roots for o in descendants(root)}
    return dict(
        count=len(objects),
        root_count=len(roots),
        root_names=sorted(obj.name for obj in roots),
        closure_matches_selection=reached == {obj.name for obj in objects},
        closure_brings_extra=sorted(reached - names),
        selection_not_reached=sorted(names - reached),
    )


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Write v06's selection, its per-cell counterparts, and what has no counterpart."""
    assert digest(SOURCE) == SOURCE_SHA, "Read the delivered v06 native"
    assert INVENTORY.exists(), f"Local working material missing: {INVENTORY}"
    assert not REPORT.exists(), "Preserve the existing selection"
    inventory = json.loads(INVENTORY.read_text())
    selection = inventory["B_candidate_exact_selection"]
    # v06 appended the drops to the inventory roots before counting 104.
    roots = list(selection["move_rigid_subtree_roots"]) + DROPS
    moved = set(selection["all_selected_object_names"]) | set(DROPS)
    fixed = set(selection["all_kept_conveyor_fixture_objects"])

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    present = {name for name in moved if name in bpy.data.objects}
    by_kind = {"cell_copy": [], "b_only_hardware": [], "bay_service": []}
    for name in sorted(moved):
        by_kind[kind_of(name)].append(name)

    group = bpy.data.objects.get(STAGGER_GROUP)
    group_members = {o.name for o in descendants(group) if o is not group} if group else set()

    source = dict(
        inventory=str(INVENTORY.relative_to(ROOT)),
        inventory_sha256=digest(INVENTORY),
        root_count=len(roots),
        moved_count=len(moved),
        fixed_count=len(fixed),
        matches_v06_counts=len(roots) == V06_ROOTS and len(moved) == V06_MOVED and len(fixed) == V06_FIXED,
        moved_disjoint_from_fixed=not (moved & fixed),
        present_in_native=len(present),
        absent_from_native=sorted(moved - present),
        counts_by_kind={kind: len(names) for kind, names in by_kind.items()},
        b_only_hardware=by_kind["b_only_hardware"],
        bay_service=by_kind["bay_service"],
        structure=structure(present),
    )

    drift = dict(
        group=STAGGER_GROUP,
        group_present=group is not None,
        group_member_count=len(group_members),
        selection_also_in_group=len(present & group_members),
        selection_not_in_group=sorted(present - group_members),
        group_not_in_selection=sorted(group_members - present),
        note=(
            "v06 parented its roots onto this group in the static candidate. The delivered "
            "native is several steps later, so a difference here records hierarchy drift, "
            "not an error in the selection."
        ),
    )

    targets = {}
    for label, prefix in TARGETS.items():
        found, missing = [], []
        for name in by_kind["cell_copy"]:
            counterpart = bpy.data.objects.get(prefix + source_of(name))
            if counterpart is None:
                missing.append(dict(template=name, expected=prefix + source_of(name)))
            else:
                found.append(counterpart)
        targets[label] = dict(
            prefix=prefix or "(unprefixed original)",
            matched_count=len(found),
            missing_count=len(missing),
            missing=missing,
            structure=structure({obj.name for obj in found}),
            selection=[describe(obj) for obj in found],
        )

    after = transforms()
    unchanged = after == before
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                supersedes=[
                    "analysis/op030_v07c_layout_inventory.json",
                    "analysis/op030_v07c_duplicate_selection.json",
                ],
                selection_source=source,
                hierarchy_drift=drift,
                targets=targets,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only mapping of the v06 recorded B selection onto A and C",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
    )
    assert unchanged, "The mapping must not move anything"
    print(f"inventory {INVENTORY.name}: roots={len(roots)} moved={len(moved)} fixed={len(fixed)}")
    print(f"  matches v06 counts (104/420/76): {source['matches_v06_counts']}")
    print(f"  present in native: {len(present)} / {len(moved)}  disjoint: {source['moved_disjoint_from_fixed']}")
    print(f"  by kind: {source['counts_by_kind']}")
    print(f"  drift: group has {len(group_members)}, shares {drift['selection_also_in_group']} with the selection")
    for label, row in targets.items():
        print(
            f"  {label}: matched={row['matched_count']} missing={row['missing_count']} "
            f"roots={row['structure']['root_count']} closure={row['structure']['closure_matches_selection']}"
        )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
