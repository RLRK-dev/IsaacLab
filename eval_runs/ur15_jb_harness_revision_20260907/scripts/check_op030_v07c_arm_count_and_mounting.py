# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Measure what fixes the arm count, and what room a mounting change would have [m].

Two questions were asked together, and they turn out to be one question. How many arms a cell
needs is set by how many things must happen at the same instant; where the arms can stand is
set by how much room there is next to the work. Past two arms the second answer starts
constraining the first, because four shoulders do not fit on a column sized for two.

Three things are measured here, all from committed files.

**What must happen at once.** Read out of each station's own sequence rather than argued: A
holds a support while the other arm drives its bolts, B holds one cable by both of its ends,
C carries a different tool on each arm and runs them one after the other. The anchors fail
loudly if any of those lines move.

**How close the work is.** Two supports 320 mm apart in X, each with two bolts 68 mm apart in
Y. That is the room a second fastening arm, or a second pair, would have to work in.

**What is overhead.** A mounting that is not a floor column has to come from somewhere, so
this maps what already occupies the space above the cell, band by band in Z, and reports the
free X gaps in each. The ceiling is really there in the model, at 7.200.

One caution carries through the overhead map and is repeated in the report: the service run
above the cell is modelled with a box far larger than the pipe inside it -- 291 box candidates
resolved to zero triangle contacts. Its box is an upper bound on what is in the way, not a
measurement of it.

Read-only. Positions, spans and concurrency, not a design: nothing here says an arm can reach,
a structure is stiff enough, or a mounting is safe.

    python3 scripts/check_op030_v07c_arm_count_and_mounting.py [--quiet]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EQUIPMENT = ROOT / "audit/op030_v06_equipment_ids.json"
DUAL_ARM = ROOT / "audit/op030_v07c_dual_arm_configuration.json"
TURN_FREE = ROOT / "audit/op030_v07c_turn_free_transport.json"
REPORT = ROOT / "audit/op030_v07c_arm_count_and_mounting.json"

# What each station's own sequence says has to happen at the same instant.
CONCURRENCY = {
    "A": {
        "source": "scripts/op030_support_motion_v04.py",
        "anchors": {
            "one arm holds through both drives": "／右保持のままM4",
            "the other arm owns the M4 tool": "fastener_drive_append(seq, receipt, seat,",
            "the two supports are done one after the other": "for number in (1, 2):",
            "the two bolts of one support": "seat = final @ pose(location=(0, sign * 0.034, 0))",
        },
        "simultaneous_arms": 2,
        "why": "one holds the support because nothing above the locating pin retains it; the other drives",
    },
    "B": {
        "source": "scripts/op030_split_wire_motion.py",
        "anchors": {
            "both arms hold one cable, one end each": 'self.state["holds"] = {0: (uid, "T"), 1: (uid, "J1")}',
            "the two cables are done one after the other": "for number in (2, 1):",
        },
        "simultaneous_arms": 2,
        "why": "the two ends of one cable are two points that must move independently",
    },
    "C": {
        "source": "scripts/op030_split_fastening_motion.py",
        "anchors": {
            "a tool is bolted to an arm, not shared": (
                'raise ValueError("This arm is not permanently fitted with the requested driver")'
            ),
        },
        "simultaneous_arms": 1,
        "why": "different tools on the two arms, M6 and M14, and the takt books the terminals serially",
    },
}
# The work the arms have to share, from op030_definition.py.
SEATS = (ROOT / "scripts/op030_definition.py", r"TERMINAL_X = \((-?[\d.]+), (-?[\d.]+)\)")
BOLTS = (ROOT / "scripts/op030_support_motion_v04.py", r"seat = final @ pose\(location=\(0, sign \* ([\d.]+), 0\)\)")
# The cell's own Y band, and the height above the arms where a mounting would have to pass.
CELL_Y_M = (-2.10, -1.30)
ARM_TOP_M = 2.05
BANDS = ((2.05, 3.40), (3.40, 4.03), (4.03, 5.80), (5.80, 7.20))
NEAR_LINE_X_M = (-4.0, 2.0)
# The overhead run whose box is known to be much larger than the pipe inside it.
COARSE = "line_services_01"


def load(path: Path) -> dict:
    """Return a committed JSON artifact."""
    return json.loads(path.read_text())


def check_anchors() -> tuple[dict, list[str]]:
    """Return each station's concurrency, with the source lines it rests on."""
    found, missing = {}, []
    for station, spec in CONCURRENCY.items():
        path = ROOT / spec["source"]
        lines = path.read_text().splitlines() if path.exists() else []
        rows = {}
        for meaning, needle in spec["anchors"].items():
            hits = [number for number, line in enumerate(lines, 1) if needle in line]
            rows[meaning] = hits
            if not hits:
                missing.append(f"{spec['source']}: {meaning}")
        found[station] = dict(
            source=spec["source"],
            simultaneous_arms=spec["simultaneous_arms"],
            why=spec["why"],
            anchors=rows,
        )
    return found, missing


def number_from(path: Path, pattern: str) -> list[float] | None:
    """Return the numbers a pattern captures in a committed source file."""
    match = re.search(pattern, path.read_text()) if path.exists() else None
    return [float(group) for group in match.groups()] if match else None


def overhead(objects: dict) -> dict:
    """Return what stands above the arms over the cell, and the free X gaps by band."""
    spans = []
    for name, record in objects.items():
        box = record.get("bounds_world_m")
        if not box or box[1][2] <= ARM_TOP_M:
            continue
        if box[1][1] < CELL_Y_M[0] or box[0][1] > CELL_Y_M[1]:
            continue
        if box[1][0] < NEAR_LINE_X_M[0] or box[0][0] > NEAR_LINE_X_M[1]:
            continue
        spans.append(
            dict(
                name=name,
                equipment_id=record.get("equipment_id"),
                x_m=[box[0][0], box[1][0]],
                z_m=[box[0][2], box[1][2]],
                box_is_coarse=record.get("equipment_id") == COARSE,
            )
        )
    spans.sort(key=lambda row: row["x_m"][0])

    bands = []
    for low, high in BANDS:
        blocking = sorted(
            (row["x_m"][0], row["x_m"][1], row["equipment_id"], row["box_is_coarse"])
            for row in spans
            if not (row["z_m"][1] <= low or row["z_m"][0] >= high)
        )
        merged: list[list] = []
        for x0, x1, tag, coarse in blocking:
            if merged and x0 <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], x1)
                merged[-1][2] = sorted(set(merged[-1][2] + [tag]))
                merged[-1][3] = merged[-1][3] or coarse
            else:
                merged.append([x0, x1, [tag], coarse])
        gaps, edge = [], NEAR_LINE_X_M[0]
        for x0, x1, _, _ in merged:
            if x0 - edge > 0.05:
                gaps.append([edge, x0])
            edge = max(edge, x1)
        if NEAR_LINE_X_M[1] - edge > 0.05:
            gaps.append([edge, NEAR_LINE_X_M[1]])
        bands.append(
            dict(
                z_m=[low, high],
                blocked_x_m=[dict(x_m=[x0, x1], by=tags, any_box_is_coarse=coarse) for x0, x1, tags, coarse in merged],
                free_x_m=gaps,
                anything_coarse=any(coarse for _, _, _, coarse in merged),
            )
        )
    return dict(objects_above_the_arms=spans, bands=bands)


def main() -> int:
    quiet = "--quiet" in sys.argv
    objects = load(EQUIPMENT)["objects"]
    arms = load(DUAL_ARM)
    turn_free = load(TURN_FREE)

    concurrency, failures = check_anchors()
    seats = number_from(*SEATS)
    bolt = number_from(*BOLTS)
    if seats is None or bolt is None:
        failures.append("the seat or bolt spacing is no longer where it was read from")

    shared = arms["mounting"]["A"]["shared_column"]
    column = arms["mounting"]["A"]["column"]["chosen"]
    above = overhead(objects)
    ceiling = max(
        (
            record["bounds_world_m"]
            for record in objects.values()
            if record.get("equipment_id") == "ceiling_01" and record.get("bounds_world_m")
        ),
        key=lambda box: box[1][2],
    )

    work = dict(
        two_supports_apart_in_x_m=abs(seats[1] - seats[0]) if seats else None,
        two_bolts_of_one_support_apart_in_y_m=2 * bolt[0] if bolt else None,
        shoulder_pitch_m=shared["base_pitch_m"],
        shoulder_height_m=shared["base_height_m"],
        column_footprint_m=[
            column["high_m"][0] - column["low_m"][0],
            column["high_m"][1] - column["low_m"][1],
        ],
        column_z_m=[column["low_m"][2], column["high_m"][2]],
        arms_reach_to_the_far_seat_m=turn_free["reach"]["furthest_seat_the_picking_arm_already_covers_m"],
    )

    minimum = {station: row["simultaneous_arms"] for station, row in concurrency.items()}
    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope="What fixes A/B/C's arm count, and what room a different mounting would have",
        read_from={
            str(path.relative_to(ROOT)): dict(observed_at=load(path).get("observed_at"))
            for path in (EQUIPMENT, DUAL_ARM, TURN_FREE)
        },
        what_this_does_not_give=[
            "reachability, joint limits, or any swept path",
            "stiffness, deflection, or whether a suspended structure could hold the relative accuracy",
            "safety, access, or maintenance, none of which are in the model",
            "a takt for any option: nothing here is a cycle-time calculation",
        ],
        concurrency=concurrency,
        minimum_simultaneous_arms=minimum,
        the_work_the_arms_share=work,
        overhead=above,
        ceiling_m=dict(underside_z_m=ceiling[0][2], top_z_m=ceiling[1][2]),
        headroom=dict(
            arms_top_z_m=ARM_TOP_M,
            ceiling_underside_z_m=ceiling[0][2],
            gross_gap_m=ceiling[0][2] - ARM_TOP_M,
            note=(
                "gross, not free: the bands below say what stands in it. A suspended mount over the"
                " cell centre would pass the service run and then the lighting."
            ),
        ),
        coarse_box_warning=(
            "The service run above the cell is modelled with a box much larger than its pipe: 291 box"
            " candidates against it resolved to zero triangle contacts. Treat its band as an upper"
            " bound on the obstruction, not a measurement."
        ),
        checks_failed=failures,
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print("what must happen at the same instant, from each station's own sequence:")
        for station, row in concurrency.items():
            print(f"  {station}: {row['simultaneous_arms']} arm(s) -- {row['why']}")
        print()
        print("the work they share:")
        print(f"  two supports        {work['two_supports_apart_in_x_m'] * 1000:.0f} mm apart in X")
        print(f"  two bolts of one    {work['two_bolts_of_one_support_apart_in_y_m'] * 1000:.0f} mm apart in Y")
        print(f"  shoulder pitch      {work['shoulder_pitch_m'] * 1000:.1f} mm at Z {work['shoulder_height_m']:.4f}")
        print(
            f"  column footprint    {work['column_footprint_m'][0]:.3f} x {work['column_footprint_m'][1]:.3f} m,"
            f" Z {work['column_z_m'][0]:.3f}..{work['column_z_m'][1]:.3f}"
        )
        print()
        print(f"overhead, over the cell's Y band, above Z {ARM_TOP_M}: ceiling underside at {ceiling[0][2]:.3f}")
        for band in above["bands"]:
            blocked = (
                " , ".join(
                    f"[{row['x_m'][0]:+.2f},{row['x_m'][1]:+.2f}]{'*' if row['any_box_is_coarse'] else ''}"
                    for row in band["blocked_x_m"]
                )
                or "（空き）"
            )
            print(f"  Z {band['z_m'][0]:.2f}-{band['z_m'][1]:.2f}  塞: {blocked}")
        print("  * その箱は実物より大きいことが分かっている（三角形接触 0 件）")
        print()
        print(f"minimum simultaneous arms: {minimum}")
        print(f"\nwrote {REPORT.relative_to(ROOT)}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
