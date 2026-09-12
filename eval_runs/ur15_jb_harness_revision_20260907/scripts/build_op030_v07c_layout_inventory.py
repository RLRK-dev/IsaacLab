# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerate the exact object set each v07c mirror copy must carry, per cell [m].

v06 relocated B from one curated selection recorded as 420 objects. v07c needs the same
selection for A and C as well, and none exists. Rather than curate three lists by hand,
this reads the membership the scene already carries: ``op030_split_layout.py`` parents every
cell under ``OP030A_cell`` / ``OP030B_cell`` / ``OP030C_cell``, attaching the originals to A
and copying them for B and C through ``duplicate_set``.

The rule is therefore: a cell's descendants, minus the families that must keep their world
pose. The rule is validated against B, whose duplicate count must land on v06's 420. The
comparison is reported rather than asserted, so a mismatch is visible instead of fatal.

Run: ``blender --background --python scripts/build_op030_v07c_layout_inventory.py``

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
REPORT = ROOT / "analysis/op030_v07c_layout_inventory.json"

CELL_ROOTS = {"A": "OP030A_cell", "B": "OP030B_cell", "C": "OP030C_cell"}
# v06 relocated this many objects for B. The same rule must reproduce it.
V06_B_MOVED_COUNT = 420
# Families that keep their world pose: the product, its pallet and the transport that
# carries them, plus the shared enclosure. Matched against the name a copy was made from.
KEEP_EXACT = {
    "JB_OP020_UID001",
    "source_0292",
}
KEEP_SUBSTRINGS = (
    "Enclosure",
    "Review_OP030",
    "Split_bay",
    "conveyor",
    "roller",
    "positioner",
    "platen",
    "stopper",
    "_pin",
    "sensor",
)


def origin_name(obj: bpy.types.Object) -> str:
    """Return the name this object was copied from, or its own name."""
    return str(obj.get("split_source_name") or obj.name)


def keeps(obj: bpy.types.Object) -> str | None:
    """Return why this object keeps its world pose, or None when it duplicates."""
    name = origin_name(obj)
    if name in KEEP_EXACT:
        return "product_or_pallet"
    for token in KEEP_SUBSTRINGS:
        if token in name or token in obj.name:
            return f"family:{token}"
    return None


def describe(obj: bpy.types.Object) -> dict:
    """Return the identity fields needed to rebuild this object elsewhere [m]."""
    return dict(
        name=obj.name,
        origin=origin_name(obj),
        type=obj.type,
        parent=obj.parent.name if obj.parent else None,
        world_translation_m=np.asarray(obj.matrix_world)[:3, 3].tolist(),
    )


def validate(duplicate: list[bpy.types.Object], keep: list[bpy.types.Object]) -> dict:
    """Apply v06's three structural conditions to one cell's selection."""
    moved = {obj.name for obj in duplicate}
    fixed = {obj.name for obj in keep}
    roots = [obj for obj in duplicate if obj.parent is None or obj.parent.name not in moved]
    reached = {o.name for root in roots for o in descendants(root)}
    return dict(
        root_count=len(roots),
        root_names=sorted(obj.name for obj in roots),
        roots_have_no_parent_inside=all(obj.parent is None or obj.parent.name not in moved for obj in roots),
        closure_matches_selection=reached == moved,
        closure_only_in_reached=sorted(reached - moved),
        closure_only_in_selection=sorted(moved - reached),
        selection_disjoint_from_kept=not (moved & fixed),
        overlap=sorted(moved & fixed),
    )


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Write the per-cell duplicate selection and its structural validation."""
    assert digest(SOURCE) == SOURCE_SHA, "Read the delivered v06 native"
    assert not REPORT.exists(), "Preserve the existing inventory"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cells = {}
    for label, root_name in CELL_ROOTS.items():
        root = bpy.data.objects.get(root_name)
        if root is None:
            cells[label] = dict(present=False, root=root_name)
            continue
        members = [obj for obj in descendants(root) if obj is not root]
        duplicate = [obj for obj in members if keeps(obj) is None]
        keep = [obj for obj in members if keeps(obj) is not None]
        cells[label] = dict(
            present=True,
            root=root_name,
            member_count=len(members),
            duplicate_count=len(duplicate),
            keep_count=len(keep),
            keep_reasons={obj.name: keeps(obj) for obj in keep},
            validation=validate(duplicate, keep),
            duplicate=[describe(obj) for obj in duplicate],
            keep=[describe(obj) for obj in keep],
        )

    b_count = cells.get("B", {}).get("duplicate_count")
    rule_check = dict(
        v06_moved_object_count=V06_B_MOVED_COUNT,
        this_rule_b_duplicate_count=b_count,
        matches=b_count == V06_B_MOVED_COUNT,
        difference=None if b_count is None else b_count - V06_B_MOVED_COUNT,
        note=(
            "v06 moved a curated selection for B. A matching count means this rule reproduces "
            "it and can be trusted for A and C. A mismatch must be resolved before duplicating."
        ),
    )

    after = transforms()
    unchanged = after == before
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                membership_rule="descendants(OP030X_cell) minus product, pallet, transport and enclosure",
                keep_exact=sorted(KEEP_EXACT),
                keep_substrings=list(KEEP_SUBSTRINGS),
                rule_check=rule_check,
                cells=cells,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only structural enumeration of per-cell duplicate selections",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
    )
    assert unchanged, "The enumeration must not move anything"
    for label, row in cells.items():
        if not row.get("present"):
            print(f"  {label}: cell root missing ({row['root']})")
            continue
        check = row["validation"]
        print(
            f"  {label}: members={row['member_count']} duplicate={row['duplicate_count']} "
            f"keep={row['keep_count']} roots={check['root_count']} "
            f"closure={check['closure_matches_selection']} disjoint={check['selection_disjoint_from_kept']}"
        )
    print(f"rule check against v06 B={V06_B_MOVED_COUNT}: {rule_check['matches']} (got {b_count})")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
