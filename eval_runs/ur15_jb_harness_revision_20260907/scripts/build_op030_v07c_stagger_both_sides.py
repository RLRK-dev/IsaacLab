# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build S1R, S2L and S3R by mirroring A, B and C across their station lines [m].

Work 3. The three empty bases get a copy of the cell opposite them, turned through M(y0),
which is ``diag(-1, -1, 1)`` with a translation of 2*y0 along Y: a half turn about a vertical
axis, determinant +1, so it is a rigid motion and forward kinematics carry over unchanged.

The copy set is the work 1 selection plus the cell's own supply, matched by prefix. The
mapping starts from B's names and B has no M4 feeder, so nothing in it could reach A's 72
feeder objects or C's 120; the completeness probe measured all three counts. Transport,
fixtures and the conveyor stay put, which is the shared line the mirrored cell works over.

``duplicate_set`` already places each copied root at ``parent.matrix_world @ source_world``,
so the mirror is applied once, as the pose of the new cell's parent empty, and every copy
follows. Mesh data stays shared with the original, as adjudicated, which is also how work 2's
repair reaches the copies.

A copy whose source parent is not itself copied needs care. ``duplicate_set`` hands it the
source's world matrix as its basis, which holds until an action writes ``location`` back --
values authored against the old parent -- and then the copy jumps. B's wire supply drawer and
its fifty children moved up to 1.100 m that way, and only on reload, because the build had
never evaluated a frame. Such copies are re-expressed with the old parent's world carried in
the parent inverse, so the basis stays exactly the source's and the same action means the same
thing, and placement is verified across the scene's frame range rather than at one frame.

Placement is verified against M(y0) applied to each source's world matrix, but not to the
last bit: Blender holds those matrices in single precision, where one step at these
coordinates is 2.4e-7 m. The tolerance is 1e-5 m, twenty times the rounding actually measured
and four orders below anything that matters, and the run also reports whether the worst error
stayed inside rounding at all, so a real placement error cannot hide behind a loose bound.

Two things this does not do. The cable from cabinet to pedestal crosses the neighbouring
station's cable at S1R and S3R, over 0.405 m and 1.206 m along Y; rerouting belongs with work
4 and is left visible rather than papered over. And the naming is ``duplicate_set``'s own ``OP030_S1R__<source>``,
the existing convention, while the single-underscore form is still awaiting adjudication.

Run: ``blender --background --python scripts/build_op030_v07c_stagger_both_sides.py``

Reads the repaired candidate and never writes to it. Writes one new candidate and one
manifest. A geometric construction at its recorded timestamp, not a physical-validity verdict.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_stagger_static_v06 import digest, snapshot  # noqa: E402
from op030_split_layout import duplicate_set  # noqa: E402
from probe_op030_v07c_mirror_clearance import (  # noqa: E402
    MIRRORS,
    SOURCE,
    SOURCE_SHA,
    covered_sets,
    moving_names,
)

OUTPUT = ROOT / "analysis/op030_v07c_stagger_both_sides.blend"
MANIFEST = ROOT / "audit/op030_v07c_stagger_both_sides.json"

# The name each new cell carries. duplicate_set appends "__" to this, which is the convention
# every existing copy follows; the single-underscore form is still awaiting adjudication.
CELL_PREFIXES = {"A": "OP030_S1R", "B": "OP030_S2L", "C": "OP030_S3R"}
# Blender keeps object matrices in single precision. One step at these coordinates is about
# 2.4e-7 m, and 4.8e-7 m out past 4 m, so the placement cannot be exact and the first version
# of this check asked for 1e-9 m and could never pass. The measured spread was 1.0e-7 to
# 5.1e-7 m, which is that rounding and nothing else. This is twenty times the spread and still
# ten micrometres: a mirror applied wrongly would be out by metres, not by this.
PLACEMENT_TOLERANCE_M = 1e-5
# Above this the error is no longer rounding and the run says so rather than passing quietly.
ROUNDING_CEILING_M = 1e-6


def mirror_matrix(station_y: float) -> Matrix:
    """Return M(y0): a half turn about the vertical through the station line [m]."""
    return Matrix(
        (
            (-1.0, 0.0, 0.0, 0.0),
            (0.0, -1.0, 0.0, 2.0 * station_y),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def ordered(names: set[str]) -> list[bpy.types.Object]:
    """Return the objects of a selection, parents before children."""
    objects = [bpy.data.objects[name] for name in sorted(names) if name in bpy.data.objects]
    depth = {}

    def rank(obj: bpy.types.Object) -> int:
        if obj.name not in depth:
            depth[obj.name] = 0 if obj.parent is None else rank(obj.parent) + 1
        return depth[obj.name]

    return sorted(objects, key=lambda obj: (rank(obj), obj.name))


def rebase_outside_roots(copies: dict[str, bpy.types.Object]) -> list[dict]:
    """Re-express copies whose source parent was not copied, so animation stays right.

    ``duplicate_set`` gives such a copy ``matrix_basis = source.matrix_world`` and an identity
    parent inverse. That is correct while nothing touches the basis, and wrong the moment an
    action does: the action writes ``location`` values authored against the old parent, and the
    copy jumps. B's wire supply drawer and its fifty children moved up to 1.100 m that way, and
    only on reload, because the build had not evaluated a frame.

    Carrying the old parent's world in the parent inverse instead leaves the basis exactly as
    the source's, so the same action means the same thing. The world pose is unchanged:
    cell_root @ (old_parent_world @ source_inverse) @ source_basis is M(y0) @ source_world.
    """
    rebased = []
    for source_name, obj in copies.items():
        source = bpy.data.objects[source_name]
        if source.parent is None or source.parent.name in copies:
            continue
        obj.matrix_parent_inverse = source.parent.matrix_world @ source.matrix_parent_inverse
        obj.matrix_basis = source.matrix_basis.copy()
        rebased.append(
            dict(
                copy=obj.name,
                source=source_name,
                source_parent=source.parent.name,
                animated=bool(source.animation_data and source.animation_data.action),
            )
        )
    return sorted(rebased, key=lambda row: row["copy"])


def placement_error(copies: dict[str, bpy.types.Object], matrix: Matrix, world: dict) -> tuple[str | None, float]:
    """Return the copy furthest from where M(y0) puts its source, and by how much [m]."""
    worst_name, worst_error = None, 0.0
    for source_name, obj in copies.items():
        expected = np.asarray(matrix @ Matrix(world[source_name]))
        error = float(np.abs(np.asarray(obj.matrix_world) - expected).max())
        if error > worst_error:
            worst_name, worst_error = obj.name, error
    return worst_name, worst_error


def checked_frames(copies: dict[str, bpy.types.Object]) -> list[int]:
    """Return the frames to test: the ends and middle of whatever is actually animated.

    Not the scene range. ``op030_split_layout`` pins frame_start and frame_end to 1, so asking
    the scene would test one frame and miss exactly what this check exists to catch. The
    actions carry the real range.
    """
    scene = bpy.context.scene
    low, high = float(scene.frame_start), float(scene.frame_end)
    for source_name in copies:
        animation = bpy.data.objects[source_name].animation_data
        action = animation.action if animation else None
        if action is None:
            continue
        start, end = action.frame_range
        low, high = min(low, float(start)), max(high, float(end))
    first, last = int(round(low)), int(round(high))
    return sorted({first, (first + last) // 2, last})


def verify(copies: dict[str, bpy.types.Object], matrix: Matrix) -> dict:
    """Check every copy sits where M(y0) puts its source, at several frames [m].

    Checking only the frame the build ran on is what let the drawer through. An action does
    not speak until a frame is evaluated.
    """
    scene = bpy.context.scene
    frames = checked_frames(copies)
    first = frames[0]
    per_frame, worst_name, worst_error = [], None, 0.0
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        world = {name: np.asarray(bpy.data.objects[name].matrix_world).tolist() for name in copies}
        name, error = placement_error(copies, matrix, world)
        per_frame.append(dict(frame=frame, worst_placed=name, worst_placement_error_m=error))
        if error > worst_error:
            worst_name, worst_error = name, error
    scene.frame_set(first)
    bpy.context.view_layer.update()
    return dict(
        frames_checked=frames,
        per_frame=per_frame,
        copy_count=len(copies),
        worst_placement_error_m=worst_error,
        worst_placed=worst_name,
        within_single_precision_rounding=bool(worst_error <= ROUNDING_CEILING_M),
        single_precision_step_m=float(np.spacing(np.float32(4.0))),
        determinant=float(np.linalg.det(np.asarray(matrix)[:3, :3])),
    )


def main() -> None:
    """Duplicate each cell onto its mirror base and save the six-cell candidate."""
    assert digest(SOURCE) == SOURCE_SHA, "Build from the repaired candidate"
    assert not any(path.exists() for path in (OUTPUT, MANIFEST)), "Preserve existing candidates"
    covered, read_from = covered_sets()

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = snapshot()
    original_names = set(before)

    cells = {}
    for cell, (destination, station_y) in MIRRORS.items():
        moving = moving_names(cell, covered[cell])
        objects = ordered(set(moving["names"]))
        matrix = mirror_matrix(station_y)
        root = bpy.data.objects.new(CELL_PREFIXES[cell] + "_root", None)
        bpy.context.scene.collection.objects.link(root)
        root.matrix_world = matrix
        copies = duplicate_set(objects, CELL_PREFIXES[cell], root)
        rebased = rebase_outside_roots(copies)
        bpy.context.view_layer.update()
        cells[cell] = dict(
            destination=destination,
            station_y_m=station_y,
            mirror_rule=f"M({station_y}): (x, y) -> (-x, {2.0 * station_y:.3f} - y)",
            cell_root=root.name,
            prefix=CELL_PREFIXES[cell],
            selection_count=moving["selection_count"],
            supply_added_count=moving["supply_added_count"],
            requested=len(moving["names"]),
            duplicated=len(copies),
            not_in_scene=sorted(set(moving["names"]) - {obj.name for obj in objects}),
            rebased_roots=len(rebased),
            rebased_animated=sum(row["animated"] for row in rebased),
            rebased=rebased,
            placement=verify(copies, matrix),
            names=sorted(obj.name for obj in copies.values()),
        )

    # verify() walks the frame range, so come back to where the first snapshot was taken
    # before comparing: an animated source reads differently at a different frame.
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    after = snapshot()
    added = sorted(set(after) - original_names)
    for name in original_names:
        assert before[name] == after[name], f"{name} changed; the sources must not move"
    for cell in cells.values():
        placement = cell["placement"]
        assert placement["worst_placement_error_m"] < PLACEMENT_TOLERANCE_M, (
            f"{cell['cell_root']}: worst placement error {placement['worst_placement_error_m']:.2e} m"
        )
        assert cell["duplicated"] == cell["requested"] - len(cell["not_in_scene"]), cell["cell_root"]

    binding = dict(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        read_from=read_from,
        scope="Three mirrored cell copies onto S1R, S2L and S3R; nothing existing is moved",
        moving_set_rule="work 1 selection plus the cell's own supply by prefix; line hardware stays",
        naming="duplicate_set convention, OP030_S1R__<source>; the single-underscore form is unadjudicated",
        mesh_data="shared with the sources, so work 2's repair reaches the copies",
        cells=cells,
        objects_before=len(original_names),
        objects_after=len(after),
        added_count=len(added),
        known_unresolved=[
            "the cabinet-to-pedestal cable crosses the neighbour's at S1R (0.405 m) and S3R (1.206 m)",
            "arm to arm at S3R measured 0.0059 m at frame 1, an upper bound, with both robots moving",
            "C's two M6 feeder legs rest on OP040's pedestal end face at S3R, with no clearance",
            "the cable also crosses OP020_direct_mating_station_foot1.33_-2.23 at S1R",
            "air drops are bay service only; each cell still needs its own set (work 4)",
        ],
    )
    bpy.context.scene["op030_v07c_stagger_both_sides"] = json.dumps(binding)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    MANIFEST.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                builder=str(Path(__file__).relative_to(ROOT)),
                builder_sha256=digest(Path(__file__)),
                output=str(OUTPUT.relative_to(ROOT)),
                output_sha256=digest(OUTPUT),
                stagger_both_sides=binding,
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    assert digest(SOURCE) == SOURCE_SHA, "The repaired candidate must be untouched"
    for cell, row in cells.items():
        rounding = "" if row["placement"]["within_single_precision_rounding"] else "  ABOVE ROUNDING"
        print(
            f"  {cell} -> {row['destination']}: duplicated {row['duplicated']} of {row['requested']} "
            f"(selection {row['selection_count']} + supply {row['supply_added_count']}) "
            f"worst placement error {row['placement']['worst_placement_error_m']:.2e} m{rounding} "
            f"over frames {row['placement']['frames_checked']}, rebased {row['rebased_roots']} roots "
            f"({row['rebased_animated']} animated)"
        )
    print(f"objects {len(original_names)} -> {len(after)} (+{len(added)})")
    print(f"V07C_STAGGER_BOTH_SIDES_SAVED {digest(OUTPUT)}")
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
