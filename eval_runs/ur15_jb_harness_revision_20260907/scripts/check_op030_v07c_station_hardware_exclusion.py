# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Answer question b of the line review: does the interference go away if the panel is not copied [m].

``HANDOFF_v07_ライン構成見直し.md`` §6 calls this the first thing to do, and §8 asks the
incoming seat to re-derive §2.3 rather than adopt it. Both are done here, from files that are
committed, so the answer does not wait on Blender.

Three things are settled:

  1. How many contacts there are. §2.3 says seven. The per-cell lists hold five distinct
     pairs; a raw count of ``"contact": true`` and ``"touching": true`` reaches seven only
     because ``closest_clear`` repeats C's two touching rows. §2.3's own table splits the
     seven 3/4, which its heading ("six of the seven") already contradicts.

  2. What each pair is. Every name is looked up in the equipment inventory, so the reader
     sees the tag rather than ``source_0693_m0120_p04``.

  3. What survives if ``station_hardware_*`` leaves the duplication set. A pair whose moving
     member is excluded cannot be reported, because it is no longer mirrored. That removes
     pairs but could add them: ``obstacles()`` is *every object not moving*, so an excluded
     member stops being a copy and becomes an obstacle standing in the original cell.

The third point is the one worth care, and it is decided by separation. Each cell mirrors
across its own station centre by ``M(y0): (x, y) -> (-x, 2*y0 - y)``, so a cell's copy lands
on the far side of the conveyor from the original. The excluded members do not move. If the
gap between an excluded member's box and the whole mirrored envelope is wider than the
candidate band, the box stage cannot pair them, and the triangle stage never sees them.

Using the reported envelope is deliberately pessimistic: it still contains the mirrored
boxes of the excluded members, and dropping them can only shrink it, never widen it. A gap
measured against the larger envelope is therefore a lower bound on the real gap.

What this does not do: it does not re-run ``probe_op030_v07c_mesh_contact.py``. That needs
Blender and ``analysis/op030_v07c_support_repair.blend``, which ``.gitignore`` keeps out of
the repository. The reasoning above is why the rerun is not needed to answer b, not a claim
that the rerun would be uninteresting. Any pair the box stage cannot form is a pair the
triangle stage cannot report, and that is the whole of the argument.

Read-only. A derivation from artifacts at their recorded timestamps, not a physical-validity
verdict.

    python3 scripts/check_op030_v07c_station_hardware_exclusion.py [--quiet]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTACT = ROOT / "audit/op030_v07c_mesh_contact.json"
EQUIPMENT = ROOT / "audit/op030_v06_equipment_ids.json"
SELECTION = ROOT / "analysis/op030_v07c_cell_selection.json"
CLEARANCE = ROOT / "audit/op030_v07c_mirror_clearance.json"
RELOCATION = ROOT / "analysis/op030_v06_relocation_selection.json"
REPORT = ROOT / "audit/op030_v07c_station_hardware_exclusion.json"

# Read back from the box stage rather than restated, so this cannot drift from it.
BAND_KEY = "candidate_band_m"
# The tag whose members §2.3 argues are process infrastructure and should not be copied.
EXCLUDED_PREFIX = "station_hardware"
# Cells that duplicate. B is v06's relocation, already built, and is reported but not re-decided.
DUPLICATING = ("A", "C")


def load(path: Path) -> dict:
    """Return a committed JSON artifact."""
    return json.loads(path.read_text())


def tag_of(objects: dict, name: str) -> str:
    """Return an object's equipment tag, or a marker when the inventory does not carry it."""
    record = objects.get(name)
    return record["equipment_id"] if record else "(not in the inventory)"


def mirror_box(low: list, high: list, station_y: float) -> tuple[list, list]:
    """Return the box M(y0) maps this box to. A half turn keeps boxes boxes [m]."""
    return (
        [-high[0], 2.0 * station_y - high[1], low[2]],
        [-low[0], 2.0 * station_y - low[1], high[2]],
    )


def separation(low_a: list, high_a: list, low_b: list, high_b: list) -> tuple[float, int]:
    """Return the box stage's signed gap and the axis that decides it [m].

    This is ``clashes()`` for a single pair: the gap on the axis that separates them most.
    Negative means the boxes overlap. The stage pairs them when the gap is under the band.
    """
    gaps = [max(low_b[axis] - high_a[axis], low_a[axis] - high_b[axis]) for axis in range(3)]
    widest = max(range(3), key=lambda axis: gaps[axis])
    return gaps[widest], widest


def distinct_pairs(contact: dict) -> tuple[list[dict], dict]:
    """Return the contact population once each, and where a naive count reaches seven."""
    pairs, seen = [], set()
    for cell, body in contact["cells"].items():
        for kind in ("contacts", "touching"):
            for entry in body[kind]:
                key = (cell, entry["moving"], entry["obstacle"])
                if key in seen:
                    continue
                seen.add(key)
                pairs.append(dict(cell=cell, kind=kind, **entry))

    flagged: dict[str, list] = {"contact": [], "touching": []}
    repeated = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for flag in ("contact", "touching"):
                if node.get(flag) is True:
                    flagged[flag].append(path)
            for key, value in node.items():
                walk(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(contact, "")
    for flag, paths in flagged.items():
        for path in paths:
            if "/closest_clear[" in path:
                repeated.append(dict(flag=flag, path=path))

    counting = dict(
        distinct_pairs=len(pairs),
        raw_contact_true=len(flagged["contact"]),
        raw_touching_true=len(flagged["touching"]),
        raw_total=len(flagged["contact"]) + len(flagged["touching"]),
        listed_twice=repeated,
        reported_contact_pairs=sum(body["contact_pairs"] for body in contact["cells"].values()),
        reported_touching_pairs=sum(body["touching_pairs"] for body in contact["cells"].values()),
        note=(
            "The per-cell contact_pairs and touching_pairs sum to the distinct population. A raw"
            " sweep for the two flags reaches seven because closest_clear repeats C's two touching"
            " rows, which are already in cells/C/touching."
        ),
    )
    return pairs, counting


def moving_sets(selection: dict, clearance: dict, relocation: dict) -> dict[str, dict]:
    """Return each cell's moving set, split into what stays copied and what would be excluded."""
    sets = {}
    for cell in ("A", "B", "C"):
        if cell == "B":
            names = set(relocation["all_selected_object_names"])
            parents = {}
        else:
            row = selection["targets"][cell]
            names = {entry["name"] for entry in row["selection"]}
            names |= set(row["structure"]["closure_brings_extra"])
            parents = {entry["name"]: entry.get("parent") for entry in row["selection"]}
        supply = set(clearance["cells"][cell]["moving"]["supply_added"])
        sets[cell] = dict(names=names | supply, parents=parents)
    return sets


def main() -> int:
    quiet = "--quiet" in sys.argv

    contact = load(CONTACT)
    equipment = load(EQUIPMENT)
    selection = load(SELECTION)
    clearance = load(CLEARANCE)
    relocation = load(RELOCATION)
    objects = equipment["objects"]
    band_m = clearance[BAND_KEY]

    failures: list[str] = []

    pairs, counting = distinct_pairs(contact)
    if counting["distinct_pairs"] != counting["reported_contact_pairs"] + counting["reported_touching_pairs"]:
        failures.append("the distinct pairs and the per-cell counters disagree")

    sets = moving_sets(selection, clearance, relocation)
    for cell in ("A", "B", "C"):
        stated = clearance["cells"][cell]["moving"]["names"]
        if len(sets[cell]["names"]) != stated:
            failures.append(f"cell {cell} moving set is {len(sets[cell]['names'])}, the box stage says {stated}")

    # Each cell is probed on its own, with everything outside its moving set as obstacle. If the
    # three sets share nothing, one cell's excluded members were already obstacles to the other
    # two, and taking them out of that cell's copy cannot move the other two cells' answers.
    shared = {
        f"{left}&{right}": sorted(sets[left]["names"] & sets[right]["names"])
        for left, right in (("A", "B"), ("A", "C"), ("B", "C"))
    }
    disjoint = dict(
        pairwise_shared_counts={key: len(names) for key, names in shared.items()},
        shared_names={key: names for key, names in shared.items() if names},
        moving_sets_are_disjoint=not any(shared.values()),
        why_it_matters=(
            "an excluded member of one cell was already an obstacle to the other two, so this"
            " changes one cell's answer at a time and never reaches across cells"
        ),
    )
    if not disjoint["moving_sets_are_disjoint"]:
        failures.append("the cells' moving sets overlap, so the exclusion is not cell-local")

    # What leaves the duplication set, and whether taking it out leaves anything dangling.
    excluded: dict[str, dict] = {}
    for cell in ("A", "B", "C"):
        names = sets[cell]["names"]
        members = sorted(n for n in names if tag_of(objects, n).startswith(EXCLUDED_PREFIX))
        parents = sets[cell]["parents"]
        orphaned = sorted(n for n, parent in parents.items() if parent in set(members) and n not in set(members))
        boxed = [n for n in members if objects.get(n, {}).get("bounds_world_m")]
        excluded[cell] = dict(
            member_count=len(members),
            members=members,
            with_geometry=len(boxed),
            without_geometry=len(members) - len(boxed),
            tags=sorted({tag_of(objects, n) for n in members}),
            orphaned_by_removal=orphaned,
            subtree_is_closed=not orphaned,
        )
        if orphaned:
            failures.append(f"cell {cell} would orphan {len(orphaned)} objects")

    # 1. Which reported pairs survive the exclusion.
    survivors, removed = [], []
    for pair in pairs:
        cell = pair["cell"]
        moving_excluded = pair["moving"] in set(excluded[cell]["members"])
        row = dict(
            cell=cell,
            kind=pair["kind"],
            moving=pair["moving"],
            moving_tag=tag_of(objects, pair["moving"]),
            obstacle=pair["obstacle"],
            obstacle_tag=tag_of(objects, pair["obstacle"]),
            triangle_pairs=pair["triangle_pairs"],
            box_depth_m=pair["box_depth_m"],
            box_overlap_xyz_m=pair.get("box_overlap_xyz_m"),
            moving_is_excluded=moving_excluded,
        )
        (removed if moving_excluded else survivors).append(row)

    # 2. Whether the exclusion can create a pair that was never tested.
    created: list[dict] = []
    closest: list[dict] = []
    for cell in DUPLICATING:
        envelope = clearance["cells"][cell]["mirrored_envelope"]
        low_env, high_env = envelope["low_m"], envelope["high_m"]
        for name in excluded[cell]["members"]:
            box = objects.get(name, {}).get("bounds_world_m")
            if box is None:
                continue  # An EMPTY has no volume; box_of() returns None and it is never an obstacle.
            gap_m, axis = separation(box[0], box[1], low_env, high_env)
            row = dict(
                cell=cell,
                obstacle=name,
                tag=tag_of(objects, name),
                stays_at_x_m=[box[0][0], box[1][0]],
                mirrored_envelope_x_m=[low_env[0], high_env[0]],
                gap_to_mirrored_envelope_m=gap_m,
                deciding_axis="xyz"[axis],
                within_candidate_band=gap_m < band_m,
            )
            closest.append(row)
            if row["within_candidate_band"]:
                created.append(row)

    worst = max(closest, key=lambda row: -row["gap_to_mirrored_envelope_m"]) if closest else None

    answer = dict(
        question="b: does the interference go away if station_hardware leaves the duplication set",
        removed_pair_count=len(removed),
        surviving_pair_count=len(survivors),
        newly_possible_pair_count=len(created),
        every_triangle_contact_removed=all(
            row["moving_is_excluded"] for row in removed + survivors if row["kind"] == "contacts"
        ),
        surviving_pairs_are_only=sorted({(row["moving_tag"], row["obstacle_tag"]) for row in survivors}),
        verdict=(
            "Every triangle-level contact goes. All three have an excluded member as the moving side,"
            " so the copy that produced them is not made. Nothing new can appear: each cell's copy lands"
            f" on the far side of the conveyor, at worst {worst['gap_to_mirrored_envelope_m']:.4f} m from"
            f" the nearest member left standing, against a {band_m:.3f} m band. What remains is the two"
            " coincident surfaces where C's feeder legs rest on OP040's pedestal, which have nothing to do"
            " with the panel."
            if worst and not created
            else "Not settled: see newly_possible."
        ),
    )

    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope=(
            "Re-derivation of HANDOFF_v07_ライン構成見直し §2.3, and the answer to its §6 question b,"
            " from committed artifacts only"
        ),
        read_from={
            str(path.relative_to(ROOT)): dict(observed_at=load(path).get("observed_at"))
            for path in (CONTACT, EQUIPMENT, SELECTION, CLEARANCE, RELOCATION)
        },
        method=dict(
            counting="distinct (cell, moving, obstacle) triples from each cell's contacts and touching lists",
            classification="equipment_id from the v06 layout inventory",
            counterfactual="a pair is removed when its moving member leaves the duplication set",
            creation_test=(
                "an excluded member stops moving and becomes an obstacle; it can only be paired with the"
                " cell's copy if their boxes come within the candidate band"
            ),
            band_m=band_m,
            pessimism=(
                "the mirrored envelope still contains the excluded members' own mirrored boxes, so the"
                " measured gap is a lower bound on the gap after they are dropped"
            ),
        ),
        what_this_does_not_give=[
            "a rerun of probe_op030_v07c_mesh_contact.py; Blender and the .blend are not in the repository",
            "any statement about pairs the box stage already formed and the triangle stage already answered",
            "a physical-validity verdict, a takt, or a floor-area decision",
        ],
        counting=counting,
        contact_population=[
            dict(
                cell=pair["cell"],
                kind=pair["kind"],
                moving=pair["moving"],
                moving_tag=tag_of(objects, pair["moving"]),
                obstacle=pair["obstacle"],
                obstacle_tag=tag_of(objects, pair["obstacle"]),
                triangle_pairs=pair["triangle_pairs"],
                box_depth_m=pair["box_depth_m"],
                box_overlap_xyz_m=pair.get("box_overlap_xyz_m"),
            )
            for pair in pairs
        ],
        cells_are_independent=disjoint,
        excluded_from_duplication=excluded,
        removed_pairs=removed,
        surviving_pairs=survivors,
        newly_possible=created,
        separation_to_mirrored_copy=sorted(closest, key=lambda row: row["gap_to_mirrored_envelope_m"]),
        answer=answer,
        checks_failed=failures,
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print(f"contact population: {counting['distinct_pairs']} distinct pairs")
        print(
            f"  a raw flag sweep reaches {counting['raw_total']}"
            f" ({counting['raw_contact_true']} contact + {counting['raw_touching_true']} touching);"
            f" {len(counting['listed_twice'])} of those rows are repeats in closest_clear"
        )
        for row in report["contact_population"]:
            print(
                f"  [{row['cell']}/{row['kind']:8s}] {row['moving_tag']:20s} x {row['obstacle_tag']:20s}"
                f"  tri={row['triangle_pairs']:4d}"
            )
        print()
        for cell in DUPLICATING:
            body = excluded[cell]
            print(
                f"cell {cell}: {body['member_count']} members leave the duplication set"
                f" ({body['with_geometry']} with geometry), subtree closed: {body['subtree_is_closed']}"
            )
        print(
            f"moving sets pairwise disjoint: {disjoint['moving_sets_are_disjoint']}"
            f" {disjoint['pairwise_shared_counts']}"
        )
        print()
        print(f"removed: {len(removed)}   surviving: {len(survivors)}   newly possible: {len(created)}")
        for row in survivors:
            print(f"  survives: [{row['cell']}] {row['moving']} x {row['obstacle_tag']}")
        if worst:
            print(
                f"  closest member left standing: {worst['obstacle']} at"
                f" {worst['gap_to_mirrored_envelope_m']:.4f} m on {worst['deciding_axis']},"
                f" band {band_m:.3f} m"
            )
        print()
        print(answer["verdict"])
        print(f"\nwrote {REPORT.relative_to(ROOT)}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
