# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bounded direct C refill candidates from the mandatory axial-clear position [m, rad]."""

import json
from datetime import datetime

import numpy as np
from op030_definition import ROOT
from op030_split_c_v05 import combined_row, drive_phases, source_tracks
from op030_split_c_v05_check import Context


def refill_phases(tracks: list[dict], number: int) -> list[list[dict]]:
    """Return the next physical queue UID's original feed and pickup phases [s]."""
    uid = 2 if number == 2 else 3
    return [
        [p for p in track["phases"] if p["label"].startswith(f"{size}／UID{uid:03d}装填")]
        for track, size in zip(tracks, ("M6", "M14"), strict=True)
    ]


def main() -> None:
    output = ROOT / "audit/op030_c_refill_direct_v05.json"
    if output.exists():
        raise FileExistsError(output)
    data, _, tracks = source_tracks()
    context = Context(data["object_names"])
    records = []
    for number in (2, 1):
        drive, refill = drive_phases(tracks, number), refill_phases(tracks, number)
        begin = [p[3]["stop_frame"] for p in drive]
        goal = [
            next(p["stop_frame"] for p in phases if p["label"].endswith("／固定工具を供給上方へ")) for phases in refill
        ]
        first_row, control = combined_row(data, tracks, *begin), combined_row(data, tracks, *goal)
        first, last = first_row["joints"], control["joints"]
        candidates = [("direct_together", np.asarray([first, last]))]
        for arm in (0, 1):
            middle = first.copy()
            middle[arm] = last[arm]
            candidates.append((f"direct_arm{arm}_first", np.asarray([first, middle, last])))
        tried, selected = [], None
        for label, path in candidates:
            failures, checked = [], 0
            for a, b in zip(path[:-1], path[1:], strict=True):
                count = max(2, int(np.ceil(np.linalg.norm(b - a) / 0.0025)) + 1)
                for fraction in np.linspace(0, 1, count):
                    q = a * (1 - fraction) + b * fraction
                    hits, _ = context.query(control, q)
                    checked += 1
                    if hits:
                        failures.append(dict(fraction=float(fraction), joints=q.tolist(), hits=hits))
                        if len(failures) >= 3:
                            break
                if failures:
                    break
            tried.append(dict(candidate=label, sampled_states=checked, failures=failures))
            print("C_V05_REFILL", number, label, checked, len(failures), flush=True)
            if not failures:
                selected = dict(candidate=label, path=path.tolist(), start_local=begin, goal_local=goal)
                break
        records.append(dict(number=number, selected=selected, tried=tried))
    output.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                records=records,
                passed=all(row["selected"] for row in records),
                geometry_modified=False,
                additional_contact_exceptions=[],
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
