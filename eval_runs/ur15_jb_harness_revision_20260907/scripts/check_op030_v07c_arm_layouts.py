# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Lay out one, two, three and four arms against the work they have to reach [m].

The earlier check answered how many arms each station needs. This one answers where they
would stand, which is the part that decides whether a count is buildable.

Two measurements set the whole thing. The shoulder base is 0.204 by 0.180 m, so two shoulders
cannot be closer than that even touching; the pair that exists stands at 0.4655 m, which is
the only pitch proven to work for these motions. Put N shoulders in a line at that pitch and
the base has to be (N-1) x 0.4655 + 0.180 long -- past two arms that outgrows the column.

The second measurement is the one that opens a way out. A's two supports are 0.320 m apart
**across** the conveyor, at X -0.16 and +0.16, while the shoulders sit in a line **along** it
at X -0.9. So the far support is the one the present arms strain for, and a second pair on
the other side of the conveyor reaches it at the same distance the near pair reaches the near
one. Four arms as two opposed pairs need no extra shoulder line at all.

Each layout below is tested the same way: every arm is assigned a work point, and the check
reports the distance from its shoulder, whether that is inside the reach the cell already
uses, and how much shoulder line the layout needs against what the column and the station
pitch have.

Read-only. Distances and spans. It does not test reachability, orientation, self-interference
between the arms -- which is question f and still unmeasured -- or anything structural.

    python3 scripts/check_op030_v07c_arm_layouts.py [--quiet]
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EQUIPMENT = ROOT / "audit/op030_v06_equipment_ids.json"
DUAL_ARM = ROOT / "audit/op030_v07c_dual_arm_configuration.json"
TURN_FREE = ROOT / "audit/op030_v07c_turn_free_transport.json"
COUNTS = ROOT / "audit/op030_v07c_arm_count_and_mounting.json"
REPORT = ROOT / "audit/op030_v07c_arm_layouts.json"

# The first link of a chain: what a shoulder physically occupies.
SHOULDER_LINK = "source_1046_m0301_p00"
# The three stations' centre lines give the pitch a cell may not outgrow.
STATION_Y_M = (-1.700, 0.600, 2.900)
DEFINITION = ROOT / "scripts/op030_definition.py"


def load(path: Path) -> dict:
    """Return a committed JSON artifact."""
    return json.loads(path.read_text())


def layouts(near_x: float, seats: dict, pitch: float, reach_used: float) -> list[dict]:
    """Return the arrangements worth putting numbers against, per arm count."""
    far_x = -near_x  # the mirror of the cell across the conveyor centre line
    near, far = "T02", "T01"  # the seat each side is closest to
    return [
        dict(
            count=1,
            key="1-A",
            name="現行支柱に 1 本（同側）",
            side_of_each_arm=[near_x],
            work_of_each_arm=[near],
            rows=1,
            note="A は押さえながら締結できず、B は両端を持てない。C のみ成立",
        ),
        dict(
            count=1,
            key="1-B",
            name="単腕 1 台に 2 連工具（利用者の制約 3）",
            side_of_each_arm=[near_x],
            work_of_each_arm=[near],
            rows=1,
            note="C 向けの案として利用者が挙げたもの。A・B には効かない",
        ),
        dict(
            count=2,
            key="2-A",
            name="共有支柱・同側・旋回軸を共有（現行）",
            side_of_each_arm=[near_x, near_x],
            work_of_each_arm=[near, near],
            rows=1,
            note="A・B が要求する最小構成。1 個ずつ順に。B の旋回中の曲げが成立する唯一の形",
        ),
        dict(
            count=2,
            key="2-C",
            name="対向（コンベヤ両側に 1 本ずつ）",
            side_of_each_arm=[near_x, far_x],
            work_of_each_arm=[near, far],
            rows=1,
            note="旋回軸を共有できない。A の背面供給と B の旋回中の曲げが崩れる",
        ),
        dict(
            count=3,
            key="3-A",
            name="共有支柱に 3 本を一列",
            side_of_each_arm=[near_x] * 3,
            work_of_each_arm=[near, near, near],
            rows=1,
            note="締結 2 本が同じ支持部の 68 mm に寄る。肩線が支柱を超える",
        ),
        dict(
            count=3,
            key="3-B",
            name="同側に 2 本＋対向に 1 本",
            side_of_each_arm=[near_x, near_x, far_x],
            work_of_each_arm=[near, near, far],
            rows=1,
            note="現行の対を残したまま遠い支持部を対向側から取る",
        ),
        dict(
            count=4,
            key="4-A",
            name="共有支柱に 4 本を一列",
            side_of_each_arm=[near_x] * 4,
            work_of_each_arm=[near, near, far, far],
            rows=1,
            note="肩線が最も長くなる。遠い支持部まで 2 本が伸びる",
        ),
        dict(
            count=4,
            key="4-B",
            name="対向 2 対（各側に押さえ＋締結）",
            side_of_each_arm=[near_x, near_x, far_x, far_x],
            work_of_each_arm=[near, near, far, far],
            rows=1,
            note="支持部が X ±0.16 に分かれているので、各対は自分の側の 1 個だけを見る",
        ),
        dict(
            count=4,
            key="4-C",
            name="同側に 2 対（上下 2 段）",
            side_of_each_arm=[near_x] * 4,
            work_of_each_arm=[near, near, far, far],
            rows=2,
            note="肩線は 2 段に分ける。段間の高さは本書では決めない",
        ),
    ]


def main() -> int:
    quiet = "--quiet" in sys.argv
    objects = load(EQUIPMENT)["objects"]
    arms = load(DUAL_ARM)
    turn_free = load(TURN_FREE)
    counts = load(COUNTS)

    failures: list[str] = []
    link = objects.get(SHOULDER_LINK, {}).get("size_m")
    if link is None:
        failures.append(f"{SHOULDER_LINK} is no longer in the inventory")
        link = [0.0, 0.0, 0.0]

    shared = arms["mounting"]["A"]["shared_column"]
    column = arms["mounting"]["A"]["column"]["chosen"]
    pitch = shared["base_pitch_m"]
    shoulder_z = shared["base_height_m"]
    near_x = shared["midpoint_xy_m"][0]
    centre_y = shared["midpoint_xy_m"][1]
    seats = {name: tuple(point) for name, point in turn_free["geometry"]["seats"].items()}
    reach_used = turn_free["reach"]["furthest_seat_the_picking_arm_already_covers_m"]
    column_span_y = column["high_m"][1] - column["low_m"][1]
    station_pitch = STATION_Y_M[1] - STATION_Y_M[0]

    text = DEFINITION.read_text()
    seat_span = re.search(r"TERMINAL_X = \((-?[\d.]+), (-?[\d.]+)\)", text)
    if seat_span is None:
        failures.append("TERMINAL_X moved")
    seat_gap = abs(float(seat_span.group(2)) - float(seat_span.group(1))) if seat_span else 0.0

    rows = []
    for layout in layouts(near_x, seats, pitch, reach_used):
        sides = layout["side_of_each_arm"]
        per_row = math.ceil(len(sides) / layout["rows"])
        # Shoulders sit in a line along Y, centred on the station, at the proven pitch.
        by_side: dict[float, list[int]] = {}
        for index, side in enumerate(sides):
            by_side.setdefault(side, []).append(index)

        arm_rows, needed = [], {}
        for side, indices in by_side.items():
            count_here = len(indices)
            in_line = min(count_here, per_row) if layout["rows"] > 1 else count_here
            span = (in_line - 1) * pitch + link[1]
            needed[side] = span
            for position, index in enumerate(indices):
                slot = position % in_line
                offset = (slot - (in_line - 1) / 2) * pitch
                shoulder = (side, centre_y + offset, shoulder_z)
                seat = seats[layout["work_of_each_arm"][index]]
                arm_rows.append(
                    dict(
                        shoulder_xyz_m=list(shoulder),
                        works_on=layout["work_of_each_arm"][index],
                        distance_m=math.dist(shoulder, seat),
                        inside_the_reach_already_used=math.dist(shoulder, seat) <= reach_used,
                    )
                )
        widest = max(needed.values())
        rows.append(
            dict(
                key=layout["key"],
                count=layout["count"],
                name=layout["name"],
                rows_of_shoulders=layout["rows"],
                sides_used=sorted(set(sides)),
                shoulder_line_needed_m=needed,
                widest_shoulder_line_m=widest,
                fits_the_present_column=widest <= column_span_y,
                fits_within_the_station_pitch=widest <= station_pitch,
                over_the_column_by_m=max(0.0, widest - column_span_y),
                arms=arm_rows,
                furthest_reach_m=max(row["distance_m"] for row in arm_rows),
                every_arm_inside_the_reach_already_used=all(row["inside_the_reach_already_used"] for row in arm_rows),
                note=layout["note"],
            )
        )

    buildable = [
        row for row in rows if row["fits_the_present_column"] and row["every_arm_inside_the_reach_already_used"]
    ]
    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope="Where one, two, three and four arms could stand, against the work they must reach",
        read_from={
            str(path.relative_to(ROOT)): dict(observed_at=load(path).get("observed_at"))
            for path in (EQUIPMENT, DUAL_ARM, TURN_FREE, COUNTS)
        },
        what_this_does_not_give=[
            "reachability: no orientation, no joint limits, no swept path",
            "self-interference between the arms, which is question f and unmeasured",
            "anything structural: no load, stiffness or deflection is in the model",
            "a takt: the counts document says what each arrangement would parallelise, not by how much",
        ],
        the_measurements_that_decide=dict(
            shoulder_base_size_m=link,
            shoulders_cannot_be_closer_than_m=link[1],
            proven_pitch_m=pitch,
            proven_pitch_is_the_only_one_demonstrated=True,
            shoulder_height_m=shoulder_z,
            column_span_along_the_line_m=column_span_y,
            station_pitch_m=station_pitch,
            reach_already_used_m=reach_used,
            two_supports_apart_m=seat_gap,
            the_supports_are_apart_across_the_conveyor=True,
            seats=dict(seats),
            minimum_simultaneous_arms=counts["minimum_simultaneous_arms"],
        ),
        shoulder_line_by_count={str(n): (n - 1) * pitch + link[1] for n in (1, 2, 3, 4)},
        layouts=rows,
        buildable_without_a_bigger_base=[row["key"] for row in buildable],
        finding=(
            "In a line, the base grows by one pitch per arm: two fit the column, three and four do not."
            " The way out is that A's two supports are apart across the conveyor rather than along it,"
            " so a second pair standing on the far side reaches the far support at the same distance"
            " the present pair reaches the near one. Four arms as two opposed pairs need no extra"
            " shoulder line, and each pair keeps a column of its own -- which is what B's two-ended"
            " hold and A's turn to the rear supply both depend on. What it costs is a second cell"
            " footprint on the far side, which is the same floor the case ② question is about."
        ),
        checks_failed=failures,
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print(f"shoulder base {link[0]:.3f} x {link[1]:.3f} m; proven pitch {pitch * 1000:.1f} mm")
        print(f"column along the line {column_span_y * 1000:.0f} mm; station pitch {station_pitch * 1000:.0f} mm")
        print(f"supports {seat_gap * 1000:.0f} mm apart ACROSS the conveyor; reach already used {reach_used:.3f} m")
        print()
        print("shoulder line needed, arms in one row:")
        for n in (1, 2, 3, 4):
            span = (n - 1) * pitch + link[1]
            verdict = "支柱に載る" if span <= column_span_y else f"支柱を {(span - column_span_y) * 1000:.0f} mm 超える"
            print(f"  {n} 本  {span * 1000:7.1f} mm   {verdict}")
        print()
        for row in rows:
            mark = "○" if row["key"] in report["buildable_without_a_bigger_base"] else "×"
            print(
                f"  {mark} {row['key']:4s} {row['name'][:30]:32s}"
                f" 肩線 {row['widest_shoulder_line_m'] * 1000:6.0f} mm"
                f"  最遠 {row['furthest_reach_m']:.3f} m"
            )
        print()
        print("現行の支柱のまま建つもの:", ", ".join(report["buildable_without_a_bigger_base"]))
        print()
        print(report["finding"])
        print(f"\nwrote {REPORT.relative_to(ROOT)}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
