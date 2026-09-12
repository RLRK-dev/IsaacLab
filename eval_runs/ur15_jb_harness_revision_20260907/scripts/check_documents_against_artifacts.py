# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Check what the documents claim against the files committed beside them.

Written for the checking seat. Every rule here exists because that exact mistake was made and
had to be corrected, so a rule that has never caught anything does not belong in it:

  row 26  a measured figure transcribed off a screen, 0.6398, that appears in no JSON
  row 27  a section naming JSON fields that the committed JSON does not have
  row 28  a claim whose evidence was never committed
  row 32  a digest pointing at a superseded version of a file
  ---     four places saying "23 corrections" against a table of 25

It reads committed files only and never opens Blender, so it checks whether a document agrees
with the artifacts, not whether the artifacts are right. A clean run means the numbers are
traceable, not that they are true.

    python3 scripts/check_documents_against_artifacts.py [--quiet]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
# v06's documents are frozen history and cite working files that were never committed. A
# checker that reports those every run teaches everyone to ignore it, so v07 is the default
# scope and --all widens it.
IN_SCOPE = ("HANDOFF_v07", "OP030_v07")
# Files a document may rest on that cannot be in the repository, with the reason. They still
# get reported, because a claim resting on one of these is not reproducible from a checkout --
# that is finding F, and section 5's mistake in a new coat. Anything absent and not declared
# here is a failure.
DECLARED_ABSENT = {
    "audit/op030_stagger_static_v06.json": "the 2.2 MB manifest, over the 2 MB pre-commit limit",
    "analysis/op040_stagger_layout_inventory.json": "10.5 MB, over the 2 MB pre-commit limit",
    "audit/op030_stagger_static_v06_geometry.json": "written beside the manifest, never committed",
}


def documents(everything: bool) -> list[Path]:
    found = sorted(HERE.glob("*.md")) + sorted(HERE.glob("analysis/*.md"))
    return found if everything else [path for path in found if path.name.startswith(IN_SCOPE)]


DATA = sorted(HERE.glob("audit/*.json")) + sorted(HERE.glob("analysis/*.json"))
# A figure quoted to this many decimals came off an instrument, not out of a design decision.
MEASURED_DECIMALS = 4
CITED_PATH = re.compile(r"`([\w./-]+\.(?:json|py|md|blend|mp4|zip))`")
DIGEST = re.compile(r"`([0-9a-f]{8})[0-9a-f]*…`")
FIELD = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+){2,})`")
# Not preceded by a colon: the seconds of a timestamp are not a measurement.
MEASURED = re.compile(rf"(?<![\w.:])(\d+\.\d{{{MEASURED_DECIMALS},}})")
STATED_ROWS = re.compile(r"訂正表[（(]?\s*(\d+)\s*件")
TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)


class Report:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str, str]] = []

    def fail(self, rule: str, document: str, detail: str) -> None:
        self.findings.append(("FAIL", f"{rule} · {document}", detail))

    def warn(self, rule: str, document: str, detail: str) -> None:
        self.findings.append(("WARN", f"{rule} · {document}", detail))


def numbers_in(value: object, into: set[str]) -> None:
    """Collect every number anywhere in a decoded JSON document, as text."""
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        into.add(f"{value!r}")
    elif isinstance(value, dict):
        for key, item in value.items():
            into.add(str(key))
            numbers_in(item, into)
    elif isinstance(value, list):
        for item in value:
            numbers_in(item, into)
    elif isinstance(value, str):
        into.add(value)


def committed() -> tuple[set[str], set[str], set[str]]:
    """Return the numbers, keys and digests that appear anywhere in the committed JSON."""
    texts: set[str] = set()
    keys: set[str] = set()
    for path in DATA:
        try:
            loaded = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        collected: set[str] = set()
        numbers_in(loaded, collected)
        texts |= collected
        keys |= {item for item in collected if FIELD.fullmatch(f"`{item}`")}
    digests = {item[:8] for item in texts if re.fullmatch(r"[0-9a-f]{64}", item)}
    return texts, keys, digests


def rounds_to(text: str, quoted: str) -> bool:
    """Whether a committed number, printed at the quoted precision, gives the quoted figure."""
    try:
        value = float(text)
    except ValueError:
        return False
    places = len(quoted.split(".")[1])
    # Documents quote "-8.085" as "8.0850" inside prose, so compare the magnitude.
    return quoted in (f"{value:.{places}f}", f"{abs(value):.{places}f}")


def main() -> int:
    quiet = "--quiet" in sys.argv
    in_scope = documents("--all" in sys.argv)
    report = Report()
    texts, keys, digests = committed()
    # Not this file. Its own docstring quotes the defects it exists to catch, so counting it
    # as a script would let every one of them through as "recorded in a script".
    script_text = "\n".join(
        path.read_text() for path in sorted(HERE.glob("scripts/*.py")) if path.name != Path(__file__).name
    )

    for document in in_scope:
        body = document.read_text()
        name = document.relative_to(HERE).as_posix()

        # Row 28, and finding F: a document must not rest on a file that is not here.
        for cited in set(CITED_PATH.findall(body)):
            # An absolute path or an elided one names something outside this checkout by
            # design; only repository-relative citations are this checker's business.
            if cited.startswith(("http", "~", "/")) or "..." in cited or "/" not in cited:
                continue
            if (HERE / cited).exists():
                continue
            if cited in DECLARED_ABSENT:
                report.warn("rests on a file no checkout has", name, f"{cited} ({DECLARED_ABSENT[cited]})")
            elif cited.endswith(".blend"):
                report.warn("rests on a scene file", name, cited)
            else:
                report.fail("cited file is absent", name, cited)

        # Row 26: a measured figure has to exist in some committed JSON.
        corrections = {row for row in body.splitlines() if TABLE_ROW.match(row)}
        for figure in set(MEASURED.findall(body)):
            if any(rounds_to(text, figure) for text in texts):
                continue
            # Only if EVERY occurrence is inside a correction row. The first form of this
            # read "for rows containing the figure, the figure is in the row", which is true
            # of nothing, and let a live figure through because the table also quoted it.
            occurrences = body.count(figure)
            quoted = sum(row.count(figure) for row in corrections)
            if quoted and quoted == occurrences:
                report.warn("figure appears only as a quoted mistake", name, figure)
            elif figure in script_text:
                report.warn("figure is in a script but in no committed JSON", name, figure)
            else:
                report.fail("measured figure is in no committed JSON", name, figure)

        # Row 27: a field named in prose has to exist in the JSON, not only in a script.
        for field in set(FIELD.findall(body)):
            if field in keys:
                continue
            where = "in a script but not in any committed JSON" if field in script_text else "nowhere"
            report.warn("named field is not in the data", name, f"{field} ({where})")

        # Row 32: a digest should be corroborated by a committed file.
        for digest in set(DIGEST.findall(body)):
            if digest not in digests:
                report.warn("digest is not corroborated here", name, digest)

        # The count drift: "N corrections" against the table that follows.
        # A count that names another document is about that document's table, not this one's.
        stated = {
            int(found)
            for found in STATED_ROWS.findall(body)
            if not re.search(r"HANDOFF[^。\n]{0,40}訂正表[（(]?\s*" + found, body)
        }
        rows = [int(found) for found in TABLE_ROW.findall(body) if found.isdigit()]
        actual = max(rows) if rows else None
        for claim in stated:
            if actual is not None and claim != actual:
                report.fail("stated count disagrees with the table", name, f"says {claim}, table ends at {actual}")
            elif actual is None:
                report.warn("stated count has no table here", name, f"says {claim}")

    fails = [finding for finding in report.findings if finding[0] == "FAIL"]
    for level, rule, detail in report.findings:
        if quiet and level == "WARN":
            continue
        print(f"{level}  {rule}: {detail}")
    print(
        f"\n{len(in_scope)} documents against {len(DATA)} JSON files: {len(fails)} FAIL, "
        f"{len(report.findings) - len(fails)} WARN"
    )
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
