# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Connect individually screened ST A branches using retained OMPL [rad, s]."""

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS
from op030_free_paths import plan_free_path
from op030_split_a_plan import PlanningContext


def assignments(report, data, limit=128):
    """Enumerate a finite set of compatible full branch assignments."""
    sections = report["sections"]
    candidates = {
        row["section"]: [branch["array_key"] for branch in row["branches"] if branch["mesh_clear"]] for row in sections
    }
    incompatible = {frozenset((row["left"], row["right"])) for row in report["compatibility"] if not row["compatible"]}
    order = sorted(candidates, key=lambda section: len(candidates[section]))
    results = []

    def search(selected):
        if len(results) >= limit:
            return
        if len(selected) == len(order):
            cost = 0.0
            for arm in (0, 1):
                previous = None
                for row in (row for row in sections if row["arm"] == arm):
                    values = data[selected[row["section"]]]
                    cost += 0.01 * float(np.linalg.norm(values[0]))
                    if previous is not None:
                        difference = values[0] - previous
                        cost += float(np.linalg.norm(np.arctan2(np.sin(difference), np.cos(difference))))
                    previous = values[-1]
            results.append((cost, selected.copy()))
            return
        section = order[len(selected)]
        for choice in candidates[section]:
            if any(frozenset((choice, value)) in incompatible for value in selected.values()):
                continue
            selected[section] = choice
            search(selected)
            del selected[section]

    search({})
    return sorted(results, key=lambda row: row[0])


def align_turns(sections, assignment, data):
    """Choose whole-section 2π representatives within original URDF bounds."""
    result = {}
    for arm in (0, 1):
        previous = np.zeros(6)
        for row in (row for row in sections if row["arm"] == arm):
            values = data[assignment[row["section"]]].copy()
            for joint in range(6):
                shifts = [
                    turn * 2 * np.pi
                    for turn in (-1, 0, 1)
                    if np.all(abs(values[:, joint] + turn * 2 * np.pi) < LIMITS[joint])
                ]
                shift = min(shifts, key=lambda value: abs(values[0, joint] + value - previous[joint]))
                values[:, joint] += shift
            previous = values[-1]
            result[row["section"]] = values
    return result


def sample_constrained(sections, values, data, arm, time):
    possible = [row for row in sections if row["arm"] == arm and row["start"] - 1e-7 <= time <= row["stop"] + 1e-7]
    if not possible:
        raise ValueError((arm, time, "No constrained endpoint"))
    row = possible[0]
    times = data[f"section_{row['section']}_times"]
    return np.array([np.interp(time, times, values[row["section"]][:, joint]) for joint in range(6)])


def connect(context, report, data, assignment, checkpoint=None):
    sections = report["sections"]
    selected = align_turns(sections, assignment, data)
    free_paths = []
    groups = []
    for arm in (0, 1):
        current = None
        for index, phase in enumerate(context.sequence.phases):
            free = context.sequence.evaluate((phase["start"] + phase["stop"]) / 2)["free"][arm]
            if free:
                if current is None:
                    current = dict(arm=arm, phases=[index], start=phase["start"], stop=phase["stop"])
                else:
                    current["phases"].append(index)
                    current["stop"] = phase["stop"]
            elif current:
                groups.append(current)
                current = None
        if current:
            groups.append(current)
    for group in sorted(groups, key=lambda row: row["start"]):
        arm = group["arm"]
        midpoint = (group["start"] + group["stop"]) / 2
        first = sample_constrained(sections, selected, data, arm, group["start"])
        last = sample_constrained(sections, selected, data, arm, group["stop"])
        other = sample_constrained(sections, selected, data, 1 - arm, midpoint)
        before = context.sequence.evaluate(group["start"] + 1e-6)
        after = context.sequence.evaluate(group["stop"] - 1e-6)
        if not np.allclose(before["root"], after["root"], atol=1e-7):
            raise ValueError("A free transit requires a stationary torso")
        if not np.allclose(before["tools"][1 - arm], after["tools"][1 - arm], atol=1e-7):
            raise ValueError("Independent free transit requires a stationary other arm")

        clocks = (group["start"] + 1e-6, midpoint, group["stop"] - 1e-6)
        worlds, signatures = [], []
        both = np.empty((2, 6))
        both[arm], both[1 - arm] = first, other
        for stamp in clocks:
            target, _, grasp, extra = context.state(stamp)
            context.query(stamp, both, side=arm, override_free=True)
            worlds.append(context.screen.world.copy())
            signatures.append((tuple(target["grips"]), grasp, extra))
        # Only eliminate duplicate scene queries after checking every native
        # collision-mesh pose, both openings, and the contact/held actor sets.
        # The articulated q and carried-object rigid transform then vary in
        # exactly the same way in each frozen query scene.
        equivalent = all(np.allclose(worlds[0], world, atol=1e-10, rtol=0) for world in worlds[1:])
        equivalent &= signatures[0] == signatures[1] == signatures[2]
        query_times = (midpoint,) if equivalent else clocks
        calls, began = 0, time.monotonic()

        def score(q):
            nonlocal calls
            both = np.empty((2, 6))
            both[arm], both[1 - arm] = q, other
            calls += 1
            if calls % 1000 == 0:
                print("SPLIT_A_FREE_PROGRESS", group["phases"], calls, round(time.monotonic() - began, 1), flush=True)
            return max(context.query(stamp, both, side=arm, override_free=True)[0] for stamp in query_times)

        path = plan_free_path(first, last, score)
        if path is None:
            return None, dict(
                phases=group["phases"], arm=arm, reason=plan_free_path.last_debug, pairs=context.screen.last_pairs
            )
        free_paths.append(dict(**group, path=path.tolist(), query_scene_count=len(query_times), score_calls=calls))
        if checkpoint:
            Path(checkpoint).write_text(json.dumps(dict(assignment=assignment, free_paths=free_paths), indent=2) + "\n")
        print("SPLIT_A_FREE_PATH", group["phases"], arm, len(path), flush=True)
    return dict(assignment=assignment, selected=selected, free_paths=free_paths), None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "audit/op030_split_a_native_branches.json")
    parser.add_argument("--output", default="op030_split_a_connected")
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    assert report["mesh_sha256"] == hashlib.sha256(Path(report["mesh_file"]).read_bytes()).hexdigest()
    if not report["all_sections_have_individually_clear_branch"]:
        raise RuntimeError("A constrained section lacks a clear native-mesh branch; do not plan transits")
    with np.load(ROOT / "analysis/op030_split_a_branches.npz") as saved:
        data = {key: saved[key].copy() for key in saved.files}
    candidates = assignments(report, data)
    context = PlanningContext(report["mesh_file"])
    failures, accepted = [], None
    attempts = 0
    for index, (_, assignment) in enumerate(candidates[:8]):
        attempts += 1
        result, failure = connect(context, report, data, assignment, ROOT / "audit" / (args.output + "_progress.json"))
        if result:
            accepted = result
            break
        failures.append(dict(assignment=index, **failure))
    output = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        finite_assignment_candidates=len(candidates),
        attempts=attempts,
        branch_report=str(args.report),
        branch_report_sha256=hashlib.sha256(args.report.read_bytes()).hexdigest(),
        mesh_file=report["mesh_file"],
        mesh_sha256=report["mesh_sha256"],
        failures=failures,
        connected=accepted is not None,
        scope="Finite mesh-screened constrained sections and OMPL free paths; dense retiming/native checking remains",
    )
    if accepted:
        arrays = {f"section_{section}_joints": values for section, values in accepted.pop("selected").items()}
        arrays.update({key: value for key, value in data.items() if key.endswith("_times")})
        np.savez_compressed(ROOT / "analysis" / (args.output + ".npz"), **arrays)
        output.update(accepted)
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print("SPLIT_A_CONNECTED", output["connected"], flush=True)
    if not accepted:
        raise RuntimeError("No complete connection within the finite assignment set")


if __name__ == "__main__":
    main()
