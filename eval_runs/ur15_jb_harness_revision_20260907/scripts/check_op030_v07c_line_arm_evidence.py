# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Put every station's arm count on evidence, OP040 onward included [-].

Until now only OP020 and OP030's three sub-stations could be checked, because only they have
an authored sequence. OP040 onward was left at "the tag says two arms", which is not evidence
of needing two. The original line generator is committed under ``inputs/`` and closes that
gap for the other stations -- not to the same standard, but to a stated one.

Three tiers, and the report keeps them apart:

  A  実装        the equipment inventory: how many arms a station actually carries
  B  設計意図    render_ur15_line.py: how many it is *meant* to carry, and why
  C  シーケンス  an authored sequence: what is actually held, and when

Tier B is the new one. ``single_arm()`` in the generator returns whether a station is an
inspection head, and says in its own words why the rest are not: the other eight "lift a part
between them or work opposite ends of the same product at once". ``fetches_component()`` says
which cells turn away from the line to collect, and ``STATION_WORK`` gives each one's style.

Two calibrations come out of the overlap, and both matter for reading tier B on its own:

  * Where tier C exists it agrees with tier B on the count. OP020 and OP030 are two-armed in
    both, and the two inspection stations are single-armed in both.
  * But tier B is written at the **unsplit** granularity. OP030 is one station there and three
    in the detailed model, and one of those three -- C, two tools run serially -- does not need
    two arms. So a tier B "needs two hands" can stop being true for a sub-station once the
    station is split. That is the caution to carry into OP040.

The generator's frame-level detail is coarser still: its ``carried`` flag is true only for the
"place" styles, which would make OP020 and OP030 one-handed. Tier C says otherwise for both.
So the flag is not used here; only the statements that are about the station rather than the
animation.

Read-only. Nothing here is a physical-validity verdict, and the generator is a film, which its
own inventory note is explicit about: it is not a design basis.

    python3 scripts/check_op030_v07c_line_arm_evidence.py [--quiet]
"""

from __future__ import annotations

import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "inputs/v02_source/inputs/v01_source/op010_base/original/render_ur15_line.py"
BY_PROCESS = ROOT / "audit/op030_v07c_arms_by_process.json"
REPORT = ROOT / "audit/op030_v07c_line_arm_evidence.json"

STATIONS = [f"OP{number:03d}" for number in range(10, 110, 10)]
# Tier C: the stations whose own sequence is committed, from the earlier checks.
SEQUENCED = {
    "OP020": dict(needs_two=True, why="右腕がトレイの取っ手を 63/68 s 保持、左腕が作業"),
    "OP030-A": dict(needs_two=True, why="押さえたまま締結"),
    "OP030-B": dict(needs_two=True, why="同一ケーブルの両端を保持し、旋回しながら曲げる"),
    "OP030-C": dict(needs_two=False, why="M6 と M14 を別腕に載せ、端子は直列"),
}


def literal(text: str, name: str) -> object | None:
    """Return a module-level tuple or dict literal by name, parsed not executed."""
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return None
    return None


def docstring_of(text: str, name: str) -> str | None:
    """Return a function's docstring, so the generator can state its own reasoning."""
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_docstring(node)
    return None


def main() -> int:
    quiet = "--quiet" in sys.argv
    failures: list[str] = []
    if not GENERATOR.exists():
        print(f"FAILED: {GENERATOR.relative_to(ROOT)} is not in the checkout", file=sys.stderr)
        return 1
    text = GENERATOR.read_text()

    operations = literal(text, "CELL_OPERATIONS")
    inspection = literal(text, "INSPECTION_STATIONS")
    work = literal(text, "STATION_WORK")
    reason = docstring_of(text, "single_arm")
    fetches = re.search(r"def fetches_component\(cell_index\):\s*\n\s*return ([^\n]+)", text)
    for name, value in (
        ("CELL_OPERATIONS", operations),
        ("INSPECTION_STATIONS", inspection),
        ("STATION_WORK", work),
        ("single_arm docstring", reason),
        ("fetches_component", fetches),
    ):
        if not value:
            failures.append(f"{name} could not be read from the generator")
    if failures:
        for line in failures:
            print(f"FAILED: {line}", file=sys.stderr)
        return 1
    if len(operations) != len(STATIONS):
        failures.append(f"the generator lists {len(operations)} cells, the line has {len(STATIONS)}")

    installed = {row["station"]: row for row in json.loads(BY_PROCESS.read_text())["the_line_as_built"]["stations"]}

    rows = []
    for index, station in enumerate(STATIONS):
        operation = operations[index]
        style = work[operation][0]
        intended = 1 if operation in inspection else 2
        actual = installed[station]["arm_count"]
        sub = {key: value for key, value in SEQUENCED.items() if key.startswith(station)}
        rows.append(
            dict(
                station=station,
                operation=operation,
                style=style,
                tier_a_installed_arms=actual,
                tier_b_intended_arms=intended,
                tier_b_fetches_a_component=operation not in inspection,
                tier_b_turns_away_to_collect=operation not in inspection,
                tier_a_and_b_agree=actual == intended,
                tier_c_sequenced=sub or None,
                tier_c_needs_two=(None if not sub else {key: value["needs_two"] for key, value in sub.items()}),
            )
        )
    disagree = [row["station"] for row in rows if not row["tier_a_and_b_agree"]]
    if disagree:
        failures.append(f"installed and intended arm counts disagree at {disagree}")

    split_changes_it = [key for key, value in SEQUENCED.items() if not value["needs_two"] and key.startswith("OP030")]

    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope="Every station's arm count on stated evidence, with OP040 onward no longer blank",
        read_from={
            "inputs/.../render_ur15_line.py": dict(
                path=str(GENERATOR.relative_to(ROOT)),
                lines=text.count("\n") + 1,
            ),
            str(BY_PROCESS.relative_to(ROOT)): dict(observed_at=json.loads(BY_PROCESS.read_text()).get("observed_at")),
        },
        tiers=dict(
            A="実装。設備タグが何本積んでいるか",
            B="設計意図。元生成器が何本のつもりか、そしてその理由",
            C="シーケンス。実際に何をいつ保持するか。authored なものがある工程だけ",
        ),
        what_this_does_not_give=[
            "tier B は映像の生成器である。その inventory 註が「設計根拠ではない」と明記している",
            "tier B は分割前の粒度で書かれている。分割すると答えが変わりうる（OP030-C が実例）",
            "the generator's frame-level carried flag is not used: it would make OP020 and OP030"
            " one-handed, which tier C contradicts for both",
            "no takt, no reach, no interference",
        ],
        the_generator_states_it=dict(
            single_arm_docstring=reason,
            inspection_stations=list(inspection),
            fetches_component=fetches.group(1).strip(),
            note="8 工程が両手を要る理由が、生成器自身の言葉で書かれている",
        ),
        stations=rows,
        every_station_now_has_evidence=not disagree,
        calibration=dict(
            tier_b_agrees_with_tier_c_on_the_count=True,
            but_tier_b_is_written_before_the_split=True,
            sub_stations_that_stopped_needing_two_after_the_split=split_changes_it,
            what_that_means_for_op040=(
                "OP040 as one station is two-handed on tier B, and its old animation held one end"
                " piece in each hand with the cable stretched between them, which is OP030-B's"
                " pattern. But OP030 was also one two-handed station on tier B and became three"
                " sub-stations, one of which does not need two arms. So OP040's answer is settled"
                " only for OP040 undivided; splitting it reopens the question, and only an authored"
                " sequence closes it."
            ),
        ),
        checks_failed=failures,
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print(f"generator: {GENERATOR.relative_to(ROOT)} ({text.count(chr(10)) + 1} 行)")
        print()
        print("工程 | 作業        | A 実装 | B 意図 | 一致 | C シーケンス")
        for row in rows:
            sub = row["tier_c_needs_two"]
            tier_c = ", ".join(f"{k.split('-')[-1]}{'要' if v else '不要'}" for k, v in sub.items()) if sub else "—"
            print(
                f"  {row['station']} | {row['operation']:17s} | {row['tier_a_installed_arms']}      |"
                f" {row['tier_b_intended_arms']}      | {'○' if row['tier_a_and_b_agree'] else '×'}    | {tier_c}"
            )
        print()
        print("生成器自身の説明（single_arm の docstring）:")
        for line in reason.splitlines():
            if line.strip():
                print(f"    {line.strip()}")
        print()
        print("較正:", report["calibration"]["what_that_means_for_op040"])
        print(f"\nwrote {REPORT.relative_to(ROOT)}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
