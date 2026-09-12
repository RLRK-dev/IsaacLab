# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Check each cell's duplication set against the fixed set, in the cell's own namespace.

Every one of v06's 76 fixed names carries B's prefix. Comparing them to cell A's unprefixed
names can only ever return empty, so the check as first written was structurally vacuous
(correction 11). The mapped form was added to the builder afterwards -- but the banked
selection JSON was observed at 03:22:05 and the mapping landed at 03:33, so the banked
disjoint_from_fixed is the naive result, and the claim that the mapped form is also empty had
no committed evidence behind it. That is what this closes.

The first version of this check then made a narrower version of the same mistake: it compared
only the 201 and 180 names the mapping matched, while the build duplicates 300 and 354, and
the handover claims 228 and 234 (correction 34). The extra objects are the cell's own tools,
which the closure brings in, and the cell's own supply, which the build adds by prefix, and
neither had ever been compared. So this version assembles the whole set from committed files
and refuses to pass unless that set is the same size as what the build recorded duplicating.
A check that silently tests less than what was built is the failure being closed here, so it
is now the check's own first assertion and its exit code.

Cell B is included as well. Its namespace is the bank's own, so for B the naive form is the
right form and the mapping is the identity; saying so is the point, because B is the one cell
where an empty naive result means something.

Runs without Blender, on committed files only: it compares recorded name sets and nothing
else. It cannot see the scene, so it does not show that no duplicated object sits where a
fixed one does, only that no fixed name, carried into the cell's namespace, is in the set
about to be duplicated. Geometry is the interference probes' job, not this one's.

    python3 scripts/check_fixed_set_mapped.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
V06 = HERE / "analysis" / "op030_v06_relocation_selection.json"
CELLS = HERE / "analysis" / "op030_v07c_cell_selection.json"
COMPLETENESS = HERE / "audit" / "op030_v07c_cell_completeness.json"
BUILT = HERE / "audit" / "op030_v07c_stagger_both_sides.json"
REPORT = HERE / "analysis" / "op030_v07c_fixed_set_mapped_check.json"
# Both spellings occur in v06's fixed set: 71 names use the double underscore and 5 use a
# single one. Testing only the double one leaves those 5 unmapped, which would make the check
# quietly incomplete in the same way the naive form was wholly vacuous.
BANK_PREFIXES = ("OP030B__", "OP030B_")


def tail(name: str) -> str | None:
    """Return the part of a fixed name after the bank's prefix, or None if it carries neither."""
    for prefix in BANK_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix) :]
    return None


def into_namespace(name: str, prefix: str) -> str:
    """Return a fixed name as it would be spelled inside the cell using this prefix."""
    rest = tail(name)
    return name if rest is None else prefix + rest


def duplicated_sets(cells: dict, completeness: dict, v06: dict) -> dict[str, dict]:
    """Assemble what each cell actually duplicates, from committed files only.

    A and C are work 1's mapping, plus the tools that cell's own closure brings in, plus the
    supply the build adds by prefix. B is v06's recorded moved set, carried over whole.
    """
    parts: dict[str, dict] = {}
    for cell, target in cells["targets"].items():
        supply = completeness["cells"][cell]["supply"]
        parts[cell] = dict(
            # "(unprefixed original)" means the cell carries no prefix at all.
            prefix="" if "unprefixed" in target["prefix"] else target["prefix"],
            mapped_selection={entry["name"] for entry in target["selection"]},
            closure_tools=set(target["structure"]["closure_brings_extra"]),
            own_supply=set(supply["not_carried"]),
            supply_prefixes=list(supply["prefixes"]),
        )
    parts["B"] = dict(
        prefix=BANK_PREFIXES[0],
        mapped_selection=set(v06["all_selected_object_names"]),
        closure_tools=set(),
        own_supply=set(),
        supply_prefixes=[],
    )
    for part in parts.values():
        part["names"] = part["mapped_selection"] | part["closure_tools"] | part["own_supply"]
    return parts


def compare(names: set[str], fixed: list[str], prefix: str) -> dict:
    """Compare one duplication set against the fixed set, literally and in the cell's namespace."""
    mapped = {into_namespace(name, prefix) for name in fixed}
    # A prefix this script does not know about would slip past the set comparison, so also
    # ask whether any fixed name's tail appears anywhere inside a name being duplicated.
    loose = sorted({chosen for name in fixed if (rest := tail(name)) is not None for chosen in names if rest in chosen})
    return dict(
        mapped_differs_from_naive=mapped != set(fixed),
        overlap_naive=len(names & set(fixed)),
        overlap_mapped=len(names & mapped),
        overlapping_names=sorted(names & mapped),
        names_containing_a_fixed_name=loose,
    )


def _without_timestamp(report: dict) -> dict:
    """The report minus the field that changes on every run."""
    return {key: value for key, value in report.items() if key != "observed_at"}


def main() -> int:
    v06 = json.loads(V06.read_text())
    cells = json.loads(CELLS.read_text())
    completeness = json.loads(COMPLETENESS.read_text())
    built_report = json.loads(BUILT.read_text())
    built = built_report["stagger_both_sides"]
    fixed = v06["all_kept_conveyor_fixture_objects"]
    unprefixed = [name for name in fixed if tail(name) is None]

    parts = duplicated_sets(cells, completeness, v06)
    results = {}
    covers_the_build = True
    for cell, part in sorted(parts.items()):
        duplicated = built["cells"][cell]["duplicated"]
        covered = len(part["names"]) == duplicated
        covers_the_build = covers_the_build and covered
        results[cell] = dict(
            prefix=part["prefix"] or "(none)",
            mapped_selection_count=len(part["mapped_selection"]),
            closure_tools_count=len(part["closure_tools"]),
            own_supply_count=len(part["own_supply"]),
            supply_prefixes=part["supply_prefixes"],
            checked_count=len(part["names"]),
            build_duplicated_count=duplicated,
            checks_the_whole_duplicated_set=covered,
            fixed_count=len(fixed),
            **compare(part["names"], fixed, part["prefix"]),
        )

    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        what="each cell's whole duplication set against the fixed set carried into that cell's namespace",
        inputs={
            str(V06.relative_to(HERE)): v06["observed_at"],
            str(CELLS.relative_to(HERE)): cells["observed_at"],
            str(COMPLETENESS.relative_to(HERE)): completeness["observed_at"],
            str(BUILT.relative_to(HERE)): built_report["observed_at"],
        },
        bank_prefixes=list(BANK_PREFIXES),
        fixed_names_carrying_neither_prefix=unprefixed,
        set_under_test=(
            "work 1's mapping, plus the closure's tools, plus the supply added by prefix; B is v06's moved set"
        ),
        every_cell_checks_its_whole_duplicated_set=covers_the_build,
        cells=results,
        what_this_does_not_give=[
            "that no duplicated object occupies a fixed object's space: this compares names, not geometry",
            "anything about the scene; it reads committed files only",
            "a check on any prefix spelling this script does not know: the loose comparison is a guard, not a proof",
            "anything about B beyond the naive form, which for B is the right form: its namespace is the bank's",
        ],
        formal_physical_validity_verdict=None,
    )
    # Only when the finding itself changed. Stamping a fresh observed_at on every run means
    # running the check dirties the tree, which blocked a merge and puts a spurious diff in
    # front of whoever runs it next. A check should be free to run.
    written = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if REPORT.exists() and _without_timestamp(json.loads(REPORT.read_text())) == _without_timestamp(report):
        print(f"unchanged: {REPORT.relative_to(HERE)}")
    else:
        REPORT.write_text(written)
        print(f"report: {REPORT.relative_to(HERE)}")

    for cell, result in results.items():
        print(
            f"{cell}: prefix {result['prefix']},"
            f" {result['checked_count']} checked of {result['build_duplicated_count']} duplicated"
            f" ({result['mapped_selection_count']}+{result['closure_tools_count']}+{result['own_supply_count']}),"
            f" naive {result['overlap_naive']}, mapped {result['overlap_mapped']},"
            f" loose {len(result['names_containing_a_fixed_name'])}"
        )
    print(f"{len(unprefixed)} of {len(fixed)} fixed names carry neither bank prefix: {unprefixed}")
    print(f"every cell checks its whole duplicated set: {covers_the_build}")
    return 0 if covers_the_build else 1


if __name__ == "__main__":
    sys.exit(main())
