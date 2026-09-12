"""Check each cell's duplication set against the fixed set, in the cell's own namespace.

Every one of v06's 76 fixed names carries B's prefix. Comparing them to cell A's unprefixed
names can only ever return empty, so the check as first written was structurally vacuous
(correction 11). The mapped form was added to the builder afterwards -- but the banked
selection JSON was observed at 03:22:05 and the mapping landed at 03:33, so the banked
disjoint_from_fixed is the naive result, and the claim that the mapped form is also empty had
no committed evidence behind it. That is what this closes.

Runs without Blender, on committed files only: it compares recorded name sets and nothing
else. It cannot see the scene, so it does not show that no duplicated object sits where a
fixed one does -- only that no fixed name, carried into the cell's namespace, is in the set
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


def main() -> int:
    v06 = json.loads(V06.read_text())
    cells = json.loads(CELLS.read_text())
    fixed = v06["all_kept_conveyor_fixture_objects"]
    unprefixed = [name for name in fixed if tail(name) is None]

    results = {}
    for cell, target in cells["targets"].items():
        # "(unprefixed original)" means the cell carries no prefix at all.
        prefix = "" if "unprefixed" in target["prefix"] else target["prefix"]
        mapped = {into_namespace(name, prefix) for name in fixed}
        selection = {entry["name"] for entry in target["selection"]}
        naive = sorted(selection & set(fixed))
        both = sorted(selection & mapped)
        # A prefix this script does not know about would slip past the set comparison, so also
        # ask whether any fixed name's tail appears anywhere inside a selected name.
        loose = sorted(
            {
                selected
                for name in fixed
                if (rest := tail(name)) is not None
                for selected in selection
                if rest in selected
            }
        )
        results[cell] = dict(
            prefix=prefix or "(none)",
            selection_count=len(selection),
            fixed_count=len(fixed),
            mapped_differs_from_naive=mapped != set(fixed),
            overlap_naive=len(naive),
            overlap_mapped=len(both),
            overlapping_names=both,
            selected_names_containing_a_fixed_name=loose,
        )

    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        what="each cell's duplication set against the fixed set carried into that cell's namespace",
        inputs={
            str(V06.relative_to(HERE)): v06["observed_at"],
            str(CELLS.relative_to(HERE)): cells["observed_at"],
        },
        bank_prefixes=list(BANK_PREFIXES),
        fixed_names_carrying_neither_prefix=unprefixed,
        cells=results,
        what_this_does_not_give=[
            "that no duplicated object occupies a fixed object's space: this compares names, not geometry",
            "anything about the scene; it reads committed files only",
            "a check on any prefix spelling this script does not know: the loose comparison is a guard, not a proof",
        ],
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    for cell, result in results.items():
        print(
            f"{cell}: prefix {result['prefix']}, {result['selection_count']} selected,"
            f" naive overlap {result['overlap_naive']}, mapped overlap {result['overlap_mapped']},"
            f" loose overlap {len(result['selected_names_containing_a_fixed_name'])}"
        )
    print(f"{len(unprefixed)} of {len(fixed)} fixed names carry neither bank prefix: {unprefixed}")
    print(f"report: {REPORT.relative_to(HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
