# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Ask whether A could fetch its supports without turning the yoke [m, s].

A turns its yoke 180 degrees to the supply and 180 degrees back, twice per support. The
question is whether the turn is doing work that could not be done standing still.

It is not doing it for reach. Every distance here is computed from constants that are in the
committed source: the cell centre and the product datum from ``op030_definition.py``, the two
support nests from ``supply_kit()`` in ``op030_geometry.py``, the 340 mm the kit is drawn out
by from the sequence, and the two shoulders measured in
``audit/op030_v07c_dual_arm_configuration.json``. The arm that fetches already reaches further
than the nest when it seats the far terminal, so the nest is inside a distance it covers anyway.

What the turn does is swap which arm stands over what. The turn is about the cell centre, and
the cell centre is the shoulder midpoint, so 180 degrees maps each shoulder onto the other's
place. The nests are on the left arm's side while the right arm is the one that picks, so
standing still would have the right arm reaching across the left. Turning puts the picking arm
over the nests and takes the tool arm out of the way, and neither crosses the other.

That gives the question a shape. Reach does not force the turn; the arms being in each other's
way does. And whether they would actually be in each other's way is the measurement that has
never been made -- question f, added to §6 by the dual-arm check.

One thing this can price. The supply plate is 0.80 m of Y centred on the cell centre, so it
already reaches the picking arm's side; only the two nests sit in its left half. Mirroring them
across the centre line puts them at the same distance from the un-turned picking arm that the
turn currently buys, and changes no robot.

Read-only. Positions and distances, not a reachability proof: this says nothing about
orientation, joint limits, or what the arms sweep through on the way.

    python3 scripts/check_op030_v07c_turn_free_transport.py [--quiet]
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFINITION = ROOT / "scripts/op030_definition.py"
GEOMETRY = ROOT / "scripts/op030_geometry.py"
SEQUENCE = ROOT / "scripts/op030_support_motion_v04.py"
MOTION = ROOT / "scripts/op030_motion.py"
ARMS = ROOT / "audit/op030_v07c_dual_arm_configuration.json"
REPORT = ROOT / "audit/op030_v07c_turn_free_transport.json"

# Each constant is lifted out of the committed source by an exact pattern, so the check fails
# rather than reporting a stale number if the source moves.
CONSTANTS = {
    "cell_and_datum": (DEFINITION, r"CX, CY, JB_Z = (-?[\d.]+), (-?[\d.]+), (-?[\d.]+)"),
    "lift": (DEFINITION, r"LIFT = ([\d.]+)"),
    "terminal_x": (DEFINITION, r"TERMINAL_X = \((-?[\d.]+), (-?[\d.]+)\)"),
    "terminal_y": (DEFINITION, r"TERMINAL_Y = (-?[\d.]+)"),
    "terminal_z": (DEFINITION, r"TERMINAL_Z = (-?[\d.]+)"),
    "nest": (GEOMETRY, r"location = np\.array\(\[(-?[\d.]+), (-?[\d.]+) \+ \(number - 1\) \* ([\d.]+), ([\d.]+)\]\)"),
    "kit_plate": (
        GEOMETRY,
        r'box\("OP030_supply_kit_plate", \(([\d.]+), ([\d.]+), ([\d.]+)\), \((-?[\d.]+), (-?[\d.]+),',
    ),
    "withdrawal": (SEQUENCE, r'supplied\["OP030_supply_kit"\] = pose\(location=\(([\d.]+), 0, 0\)\)'),
    "turn_seconds": (MOTION, r"self\.phase\(label, ([\d.]+), turn=angle\)"),
}
# The takt document's factor from authored seconds to saved bank seconds.
BANK_FACTOR = 0.955
# Two turns per support, two supports per A cycle.
TURNS_PER_CYCLE = 4
A_BANK_S = 238.8


def read_constants() -> tuple[dict, list[str]]:
    """Return the numbers this rests on, taken out of the committed source."""
    values, missing = {}, []
    for name, (path, pattern) in CONSTANTS.items():
        text = path.read_text() if path.exists() else ""
        match = re.search(pattern, text)
        if match is None:
            missing.append(f"{path.name}: {name}")
            continue
        values[name] = dict(
            source=str(path.relative_to(ROOT)),
            line=text[: match.start()].count("\n") + 1,
            numbers=[float(group) for group in match.groups()],
            text=match.group(0),
        )
    return values, missing


def distance(a: tuple, b: tuple) -> float:
    """Return the straight-line distance between two points [m]."""
    return math.dist(a, b)


def main() -> int:
    quiet = "--quiet" in sys.argv
    values, failures = read_constants()
    if failures:
        print("FAILED: the source moved:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    centre_x, centre_y, datum_z = values["cell_and_datum"]["numbers"]
    lift = values["lift"]["numbers"][0]
    terminal_x = values["terminal_x"]["numbers"]
    terminal_y = values["terminal_y"]["numbers"][0]
    terminal_z = values["terminal_z"]["numbers"][0]
    nest_x, nest_y0, nest_pitch, nest_z = values["nest"]["numbers"]
    plate_dy, plate_cy = values["kit_plate"]["numbers"][1], values["kit_plate"]["numbers"][4]
    withdrawal = values["withdrawal"]["numbers"][0]
    turn_s = values["turn_seconds"]["numbers"][0]

    # The product frame turns a half turn about the vertical, so a local (x, y) lands at (-x, -y).
    product_z = datum_z + lift
    seats = {
        f"T{index + 1:02d}": (-terminal_x[index], centre_y - terminal_y, product_z + terminal_z) for index in range(2)
    }
    # The nests as built, and where the kit presents them once it is drawn out.
    nests = {f"T{number:02d}": (nest_x + withdrawal, nest_y0 + (number - 1) * nest_pitch, nest_z) for number in (1, 2)}
    mirrored = {name: (x, 2.0 * centre_y - y, z) for name, (x, y, z) in nests.items()}

    arms = json.loads(ARMS.read_text())["mounting"]["A"]["mounts"]
    shoulders = {side: (row["x_m"], row["y_m"], row["z_m"]) for side, row in arms.items()}
    # A half turn about the cell centre maps each shoulder onto the other's place.
    turned = {side: (2.0 * centre_x - x, 2.0 * centre_y - y, z) for side, (x, y, z) in shoulders.items()}
    picking, tooled = "right", "left"

    rows = []
    for name in ("T01", "T02"):
        rows.append(
            dict(
                target=f"{name} nest, kit drawn out",
                point=list(nests[name]),
                from_picking_arm_standing_still_m=distance(shoulders[picking], nests[name]),
                from_picking_arm_after_the_turn_m=distance(turned[picking], nests[name]),
                from_picking_arm_if_the_nest_were_mirrored_m=distance(shoulders[picking], mirrored[name]),
            )
        )
    for name in ("T01", "T02"):
        rows.append(
            dict(
                target=f"{name} seat, on the product",
                point=list(seats[name]),
                from_picking_arm_standing_still_m=distance(shoulders[picking], seats[name]),
                from_picking_arm_after_the_turn_m=None,
                from_picking_arm_if_the_nest_were_mirrored_m=None,
            )
        )

    furthest_seat = max(row["from_picking_arm_standing_still_m"] for row in rows if "seat" in row["target"])
    furthest_nest = max(row["from_picking_arm_standing_still_m"] for row in rows if "nest" in row["target"])

    plate_low_y, plate_high_y = plate_cy - plate_dy / 2.0, plate_cy + plate_dy / 2.0
    nests_on_the_tool_arms_side = all(y < centre_y for _, y, _ in nests.values())

    moves = ", ".join(f"{name} by {abs(mirrored[name][1] - nests[name][1]):.2f} m" for name in nests)
    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope="Whether A's supports could be fetched without the yoke turn, from committed constants",
        read_from=dict(
            constants={name: dict(row) for name, row in values.items()},
            shoulders=str(ARMS.relative_to(ROOT)),
        ),
        what_this_does_not_give=[
            "a reachability proof: no orientation, no joint limits, no swept path",
            "whether the arms would foul each other standing still, which is question f and unmeasured",
            "any change to the kit's guides, its withdrawal, or how the parts are presented",
        ],
        geometry=dict(
            cell_centre_xy_m=[centre_x, centre_y],
            turn_is_about_the_cell_centre=True,
            cell_centre_is_the_shoulder_midpoint=(
                abs((shoulders["left"][0] + shoulders["right"][0]) / 2 - centre_x) < 1e-3
                and abs((shoulders["left"][1] + shoulders["right"][1]) / 2 - centre_y) < 1e-3
            ),
            shoulders={side: list(point) for side, point in shoulders.items()},
            shoulders_after_a_half_turn={side: list(point) for side, point in turned.items()},
            a_half_turn_swaps_the_two_shoulders=(
                distance(turned["right"], shoulders["left"]) < 1e-3
                and distance(turned["left"], shoulders["right"]) < 1e-3
            ),
            nests_as_built={name: [nest_x, y - 0.0, z] for name, (_, y, z) in nests.items()},
            nests_when_presented={name: list(point) for name, point in nests.items()},
            seats={name: list(point) for name, point in seats.items()},
        ),
        distances=rows,
        reach=dict(
            furthest_seat_the_picking_arm_already_covers_m=furthest_seat,
            furthest_nest_standing_still_m=furthest_nest,
            the_nest_is_inside_the_reach_already_used=furthest_nest < furthest_seat,
            margin_m=furthest_seat - furthest_nest,
        ),
        why_the_turn_then=dict(
            nests_sit_on_the_tool_arms_side=nests_on_the_tool_arms_side,
            picking_arm_is=picking,
            tool_arm_is=tooled,
            reading=(
                "The turn is not buying distance. It swaps which arm stands where: the nests are on the"
                " tool arm's side of the centre line, and the picking arm is on the other. Standing"
                " still, the picking arm has to reach across the tool arm. Turning puts the picking arm"
                " over the nests and moves the tool arm clear."
            ),
            what_would_settle_it=(
                "question f -- whether the two arms actually foul each other. Nothing has measured it,"
                " and the probes cannot, so 'reach across' cannot yet be priced."
            ),
        ),
        mirroring_the_nests=dict(
            kit_plate_y_span_m=[plate_low_y, plate_high_y],
            plate_already_reaches_the_picking_arms_side=plate_high_y > centre_y,
            mirrored_nests={name: list(point) for name, point in mirrored.items()},
            move_in_y_m={name: abs(mirrored[name][1] - nests[name][1]) for name in nests},
            distance_matches_what_the_turn_buys=all(
                abs(distance(shoulders[picking], mirrored[name]) - distance(turned[picking], nests[name])) < 5e-3
                for name in nests
            ),
            note=(
                "The plate is 0.80 m of Y centred on the cell centre, so both mirrored positions are on"
                " it. This is the position half of the change only: the guides, the nests' own"
                " orientation and the withdrawal direction are not examined here."
            ),
        ),
        what_the_turn_costs=dict(
            seconds_each=turn_s,
            turns_per_cycle=TURNS_PER_CYCLE,
            authored_seconds_per_cycle=turn_s * TURNS_PER_CYCLE,
            bank_seconds_per_cycle=turn_s * TURNS_PER_CYCLE * BANK_FACTOR,
            share_of_a_bank=turn_s * TURNS_PER_CYCLE * BANK_FACTOR / A_BANK_S,
            a_bank_s=A_BANK_S,
        ),
        answer=(
            "Yes on distance, unsettled on interference. The picking arm already reaches"
            f" {furthest_seat:.3f} m to seat the far terminal, and the furthest nest is"
            f" {furthest_nest:.3f} m away standing still -- inside the reach it uses anyway, by"
            f" {furthest_seat - furthest_nest:.3f} m. The turn buys position, not distance: it swaps the"
            " two shoulders so the picking arm stands over nests that sit on the tool arm's side."
            " Standing still means reaching across the other arm, and whether that fouls is question f,"
            " which nothing has measured. The cheapest way to make the question go away is not a robot"
            " change: the supply plate already spans both sides of the centre line, and mirroring the"
            f" two nests across it ({moves})"
            " puts them at the same distance from the un-turned picking arm that the turn currently"
            f" buys. The turn is worth {turn_s * TURNS_PER_CYCLE * BANK_FACTOR:.1f} s of A's {A_BANK_S} s bank."
        ),
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print("constants, all read out of committed source:")
        for name, row in values.items():
            print(f"  {row['source']}:{row['line']:<4} {name} = {row['numbers']}")
        print()
        print(
            f"cell centre {centre_x, centre_y} is the shoulder midpoint:"
            f" {report['geometry']['cell_centre_is_the_shoulder_midpoint']}"
        )
        print(f"a half turn swaps the two shoulders: {report['geometry']['a_half_turn_swaps_the_two_shoulders']}")
        print()
        print(f"distances from the {picking} arm's shoulder:")
        for row in rows:
            still = row["from_picking_arm_standing_still_m"]
            after = row["from_picking_arm_after_the_turn_m"]
            mirror = row["from_picking_arm_if_the_nest_were_mirrored_m"]
            extra = f"   turned {after:.3f}   nest mirrored {mirror:.3f}" if after else ""
            print(f"  {row['target']:28s} standing still {still:.3f} m{extra}")
        print()
        print(
            f"the furthest nest is {furthest_nest:.3f} m, the furthest seat {furthest_seat:.3f} m:"
            f" the nest is inside the reach already used by {furthest_seat - furthest_nest:.3f} m"
        )
        print(f"nests sit on the tool arm's side of the centre line: {nests_on_the_tool_arms_side}")
        print(
            f"mirroring them moves T01 by {abs(mirrored['T01'][1] - nests['T01'][1]):.2f} m and"
            f" T02 by {abs(mirrored['T02'][1] - nests['T02'][1]):.2f} m, on a plate that spans"
            f" {plate_low_y:.2f}..{plate_high_y:.2f} in Y"
        )
        print(
            f"the turn costs {turn_s * TURNS_PER_CYCLE * BANK_FACTOR:.1f} s of A's {A_BANK_S} s bank"
            f" ({turn_s * TURNS_PER_CYCLE * BANK_FACTOR / A_BANK_S:.1%})"
        )
        print()
        print(report["answer"])
        print(f"\nwrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
