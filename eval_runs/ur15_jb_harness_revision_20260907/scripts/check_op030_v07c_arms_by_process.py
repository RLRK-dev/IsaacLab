# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Ask which kind of process each arm count suits, starting from the line's own answer [-].

The brief is a robot that stands in for a person, so the useful axis is not "how many arms can
we afford" but "how many points does this job need held or acted on at the same moment". A
person brings two hands to that question and no more.

The line has already answered it once, and this reads the answer off rather than proposing
one: eight stations carry two arms, the last two carry one, and nothing on the line carries
three or four. The two single-arm stations are also the two with no stocker and no operator
panel -- they take nothing and fit nothing, which is what the concept note calls the final
inspection pair.

Against that backdrop OP030's three sub-stations sort cleanly, and the sorting comes from
their own sequences rather than from judgement:

  A   one hand carries the support in and holds it, the other drives -- two-handed work
  B   two hands on the two ends of one cable, bending it while the waist turns -- two-handed
  C   two different tools, run one after the other -- a person would swap tools, one-handed

C is the interesting one: its second arm is not a second hand, it is a way of not changing
tools. That is why C is the station where splitting the pair costs least.

Read-only. Counts and tags out of the inventory, plus the concurrency the earlier check
anchored. It proposes no design and measures no reach.

    python3 scripts/check_op030_v07c_arms_by_process.py [--quiet]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EQUIPMENT = ROOT / "audit/op030_v06_equipment_ids.json"
COUNTS = ROOT / "audit/op030_v07c_arm_count_and_mounting.json"
REPORT = ROOT / "audit/op030_v07c_arms_by_process.json"

STATIONS = [f"OP{number:03d}" for number in range(10, 110, 10)]
# What a station's own equipment says about the kind of work it does.
TELLS = ("stocker", "operator_panel", "assembly_cell", "station_hardware")

# The axis: how many points a job needs held or acted on at the same moment.
LADDER = [
    dict(
        points="0 — 部品を持たない",
        arms=1,
        person="片手、あるいは手を使わない",
        suits="検査・計測。部品を取らず、嵌めず、締めない",
        example="OP090・OP100（ストッカも操作盤も無い）",
        on_the_line=True,
    ),
    dict(
        points="1 を押さえて 1 に作用",
        arms=2,
        person="両手。人の標準的な組立動作",
        suits="部品を保持しないと定まらず、別の工具で作用する工程",
        example="OP030-A（押さえ＋M4 締結）ほかライン 8 工程",
        on_the_line=True,
    ),
    dict(
        points="2 を独立に動かす",
        arms=2,
        person="両手。柔軟物を扱うときの人の動作",
        suits="柔軟物の 2 点を同時に。片方だけでは形が決まらない",
        example="OP030-B（ケーブル両端を持ち、旋回しながら曲げる）",
        on_the_line=True,
    ),
    dict(
        points="1 を押さえて 2 に同時作用",
        arms=3,
        person="人にはできない",
        suits="同時締結など、順番に作用すると結果が変わる工程",
        example="ライン上に無い",
        on_the_line=False,
    ),
    dict(
        points="独立した両手仕事 × 2",
        arms=4,
        person="人 2 人分",
        suits="1 工程に独立な作業点が 2 つある、または工程内で先行準備を回す",
        example="ライン上に無い（OP030-A の支持部 2 個がこの形）",
        on_the_line=False,
    ),
]


def load(path: Path) -> dict:
    """Return a committed JSON artifact."""
    return json.loads(path.read_text())


def main() -> int:
    quiet = "--quiet" in sys.argv
    equipment = load(EQUIPMENT)
    counts = equipment["equipment_counts"]
    concurrency = load(COUNTS)["minimum_simultaneous_arms"]

    failures: list[str] = []
    rows = []
    for index, station in enumerate(STATIONS, start=1):
        suffix = f"_{index:02d}"
        arms = sorted(match.group(1) for key in counts if (match := re.fullmatch(rf"robot_{station}_(\w+)", key)))
        tells = {tell: (tell + suffix) in counts for tell in TELLS}
        rows.append(
            dict(
                station=station,
                arm_count=len(arms),
                arms=arms,
                has_stocker=tells["stocker"],
                has_operator_panel=tells["operator_panel"],
                takes_parts=tells["stocker"],
            )
        )
    if not rows or any(row["arm_count"] == 0 for row in rows):
        failures.append("a station's arms could not be counted from the inventory")

    two_armed = [row["station"] for row in rows if row["arm_count"] == 2]
    one_armed = [row["station"] for row in rows if row["arm_count"] == 1]
    more = [row["station"] for row in rows if row["arm_count"] > 2]

    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope="Which kind of process each arm count suits, read off the line before proposing anything",
        read_from={
            str(path.relative_to(ROOT)): dict(observed_at=load(path).get("observed_at")) for path in (EQUIPMENT, COUNTS)
        },
        what_this_does_not_give=[
            "any takt, reach or interference result",
            "a verdict on OP040 onward, whose motion the checkpoint calls roughly modelled only",
            "anything about cost, safety or maintainability",
        ],
        the_line_as_built=dict(
            stations=rows,
            two_armed=two_armed,
            one_armed=one_armed,
            three_or_more=more,
            nothing_on_the_line_has_more_than_two=not more,
            the_single_armed_pair_takes_no_parts=all(
                not row["has_stocker"] and not row["has_operator_panel"] for row in rows if row["arm_count"] == 1
            ),
        ),
        op030_substations=dict(
            minimum_simultaneous_arms=concurrency,
            A="片手で供給から運び、そのまま押さえる。もう片手が締結 — 人の両手仕事",
            B="両手で同一ケーブルの両端。旋回しながら曲げる — 人の両手仕事",
            C="M6 と M14 を別腕に載せ、端子は直列 — 人なら工具を持ち替える片手仕事",
            C_is_the_exception=(
                "C の 2 本目は「もう一方の手」ではなく「工具を持ち替えないための手」である。"
                "だから C は対を分けても失うものが最も少ない"
            ),
        ),
        ladder=LADDER,
        finding=(
            f"The line answers it as built: {len(two_armed)} stations with two arms,"
            f" {len(one_armed)} with one, none with more. The single-armed pair is also the pair"
            " that takes no parts and has no operator panel -- inspection. So two arms is what"
            " picking a part up and fitting it costs, and one arm is what looking at it costs."
            " Three and four are not on the line at all: they are not a person's shape, and the"
            " case for them has to be made from what they parallelise rather than from what a"
            " person does."
        ),
        checks_failed=failures,
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print("ライン実装（equipment tag より）:")
        for row in rows:
            print(
                f"  {row['station']}  腕 {row['arm_count']}  "
                f"ストッカ {'有' if row['has_stocker'] else '—'}  "
                f"操作盤 {'有' if row['has_operator_panel'] else '—'}"
            )
        print()
        print(f"  双腕 {len(two_armed)} 工程 / 単腕 {len(one_armed)} 工程 / 3 本以上 {len(more)} 工程")
        print()
        print("同時に確定させる点の数 → 腕数:")
        for step in LADDER:
            mark = "実装あり" if step["on_the_line"] else "実装なし"
            print(f"  {step['points']:22s} → {step['arms']} 本  [{mark}]  {step['suits']}")
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
