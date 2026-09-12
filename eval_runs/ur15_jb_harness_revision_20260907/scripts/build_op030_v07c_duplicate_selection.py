# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Derive the v07c duplicate selection for A and C from v06's own B selection [m].

Replaces ``build_op030_v07c_layout_inventory.py``, whose rule counted 64 objects for B
against v06's 420. That rule assumed the relocated set lives under ``OP030B_cell``. It does
not. ``build_op030_stagger_static_v06.py`` re-parented 104 curated roots onto a new empty,
``OP030B_robot_supply_stagger_root``, leaving the cell root in place as a fixed anchor, and
some of those roots were never cell children at all: the four
``Split_bay_1__source_0783_m0210_p*`` air drops are bay service hardware.

So the selection is not derivable from the cell hierarchy. It is instead already recorded in
the scene, as the contents of that relocation group. This reads that group as the template,
then maps each member to its A and C counterpart through the naming ``duplicate_set``
established: a copy is ``OP030B__<source>``, A keeps ``<source>`` unprefixed, and C holds
``OP030C__<source>``. Members with no counterpart -- B-only hardware and bay service -- are
reported separately, because those need new geometry rather than a copy.

Run: ``blender --background --python scripts/build_op030_v07c_duplicate_selection.py``

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
REPORT = ROOT / "analysis/op030_v07c_duplicate_selection.json"

# The empty v06 re-parented B's relocated roots onto.
TEMPLATE_GROUP = "OP030B_robot_supply_stagger_root"
V06_MOVED_COUNT = 420
V06_ROOT_COUNT = 104
COPY_PREFIX = "OP030B__"
BONLY_PREFIX = "OP030B_"
TARGETS = {"A": "", "C": "OP030C__"}


def source_name(obj: bpy.types.Object) -> str:
    """Return the original name this object was copied from, or its own name."""
    stamped = obj.get("split_source_name")
    if stamped:
        return str(stamped)
    if obj.name.startswith(COPY_PREFIX):
        return obj.name[len(COPY_PREFIX) :]
    return obj.name


def kind_of(obj: bpy.types.Object) -> str:
    """Classify a template member by whether a per-cell counterpart can exist."""
    if obj.name.startswith(COPY_PREFIX):
        return "cell_copy"
    if obj.name.startswith(BONLY_PREFIX):
        return "b_only_hardware"
    return "bay_service"


def describe(obj: bpy.types.Object) -> dict:
    """Return the identity fields needed to rebuild this object elsewhere [m]."""
    return dict(
        name=obj.name,
        type=obj.type,
        parent=obj.parent.name if obj.parent else None,
        world_translation_m=np.asarray(obj.matrix_world)[:3, 3].tolist(),
    )


def structure(selection: list[bpy.types.Object]) -> dict:
    """Apply v06's structural conditions to one derived selection."""
    names = {obj.name for obj in selection}
    roots = [obj for obj in selection if obj.parent is None or obj.parent.name not in names]
    reached = {o.name for root in roots for o in descendants(root)}
    return dict(
        count=len(selection),
        root_count=len(roots),
        root_names=sorted(obj.name for obj in roots),
        closure_matches_selection=reached == names,
        closure_brings_extra=sorted(reached - names),
        selection_not_reached=sorted(names - reached),
    )


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Write the template selection, its per-cell counterparts, and the gaps."""
    assert digest(SOURCE) == SOURCE_SHA, "Read the delivered v06 native"
    assert not REPORT.exists(), "Preserve the existing selection"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    group = bpy.data.objects.get(TEMPLATE_GROUP)
    assert group is not None, f"{TEMPLATE_GROUP} is missing; v06 relocation not present"
    members = [obj for obj in descendants(group) if obj is not group]
    by_kind = {"cell_copy": [], "b_only_hardware": [], "bay_service": []}
    for obj in members:
        by_kind[kind_of(obj)].append(obj)

    template = dict(
        group=TEMPLATE_GROUP,
        member_count=len(members),
        matches_v06_moved_count=len(members) == V06_MOVED_COUNT,
        v06_moved_count=V06_MOVED_COUNT,
        v06_root_count=V06_ROOT_COUNT,
        structure=structure(members),
        counts_by_kind={kind: len(rows) for kind, rows in by_kind.items()},
        b_only_hardware=[obj.name for obj in by_kind["b_only_hardware"]],
        bay_service=[obj.name for obj in by_kind["bay_service"]],
    )

    targets = {}
    for label, prefix in TARGETS.items():
        found, missing = [], []
        for obj in by_kind["cell_copy"]:
            counterpart = bpy.data.objects.get(prefix + source_name(obj))
            if counterpart is None:
                missing.append(dict(template=obj.name, expected=prefix + source_name(obj)))
            else:
                found.append(counterpart)
        targets[label] = dict(
            prefix=prefix or "(unprefixed original)",
            matched_count=len(found),
            missing_count=len(missing),
            missing=missing,
            structure=structure(found),
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
                supersedes="analysis/op030_v07c_layout_inventory.json",
                derivation=(
                    "v06 re-parented its curated B selection onto "
                    f"{TEMPLATE_GROUP}. That group is the template. A and C counterparts follow "
                    "duplicate_set naming: OP030B__<source> maps to <source> and OP030C__<source>."
                ),
                template=template,
                targets=targets,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only derivation of per-cell duplicate selections from the v06 template",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
    )
    assert unchanged, "The derivation must not move anything"
    print(f"template {TEMPLATE_GROUP}: {len(members)} members (v06 recorded {V06_MOVED_COUNT})")
    print(f"  matches v06 count: {template['matches_v06_moved_count']}")
    print(f"  by kind: {template['counts_by_kind']}")
    print(f"  roots={template['structure']['root_count']} closure={template['structure']['closure_matches_selection']}")
    for label, row in targets.items():
        print(
            f"  {label}: matched={row['matched_count']} missing={row['missing_count']} "
            f"roots={row['structure']['root_count']} closure={row['structure']['closure_matches_selection']}"
        )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
