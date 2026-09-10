# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Finite continuous branch survey between ST A free transits [m, rad, s]."""

import json
from datetime import datetime

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS, chain_for
from op030_motion import SIDES
from op030_split_support_motion import build_sequence
from solve_op030_motion import R


def constrained_sections(seq):
    """Return maximal constrained intervals separated by free arm transits [s]."""
    result = []
    for arm in (0, 1):
        current = None
        for phase in seq.phases:
            target = seq.evaluate((phase["start"] + phase["stop"]) / 2)
            if target["free"][arm]:
                if current:
                    result.append(current)
                    current = None
            elif current is None:
                current = dict(arm=arm, start=phase["start"], stop=phase["stop"], labels=[phase["label"]])
            else:
                current["stop"] = phase["stop"]
                current["labels"].append(phase["label"])
        if current:
            result.append(current)
    return result


def main():
    seq = build_sequence()
    with np.load(ROOT / "data/op030_motion_v02.npz") as data:
        indices = np.linspace(0, len(data["joints"]) - 1, 8, dtype=int)
        seeds = data["joints"][indices]
    arrays, records = {}, []
    for section, interval in enumerate(constrained_sections(seq)):
        arm = interval["arm"]
        times = np.unique(
            np.r_[
                np.arange(interval["start"], interval["stop"], 0.5),
                interval["stop"],
                [p["start"] for p in seq.phases if interval["start"] < p["start"] < interval["stop"]],
            ]
        )
        targets = [seq.evaluate(t) for t in times]
        chains = [chain_for(tuple((target["root"] @ R.yoke_base_pose(SIDES[arm])).ravel())) for target in targets]
        rows, seen = [], []
        for reverse in (False, True):
            order = list(range(len(times)))
            if reverse:
                order.reverse()
            first = order[0]
            for seed_index, seed in zip(indices, seeds[:, arm], strict=True):
                q, error = chains[first].solve(targets[first]["tools"][arm], seed, max_nfev=100)
                if error > 1e-5:
                    rows.append(
                        dict(
                            reverse=reverse, seed=int(seed_index), feasible=False, failure="endpoint_ik", residual=error
                        )
                    )
                    continue
                if any(direction == reverse and np.max(abs(old - q)) < 1e-4 for direction, old in seen):
                    continue
                seen.append((reverse, q.copy()))
                samples, failure, maximum = {first: q.copy()}, None, 0.0
                for index in order[1:]:
                    next_q, residual = chains[index].solve_continuous(targets[index]["tools"][arm], q)
                    delta = float(np.max(abs(next_q - q)))
                    maximum = max(delta, maximum)
                    if residual > 1e-5 or np.any(abs(next_q) >= LIMITS) or delta > 0.8:
                        failure = dict(
                            time=float(times[index]),
                            residual=residual,
                            delta=delta,
                            within_limits=bool(np.all(abs(next_q) < LIMITS)),
                        )
                        break
                    q = next_q
                    samples[index] = q.copy()
                row = dict(
                    reverse=reverse,
                    seed=int(seed_index),
                    feasible=failure is None,
                    failure=failure,
                    max_adjacent_delta=maximum,
                )
                if failure is None:
                    key = f"section_{section}_branch_{len(rows)}"
                    arrays[key] = np.asarray([samples[index] for index in range(len(times))])
                    row["array_key"] = key
                rows.append(row)
        arrays[f"section_{section}_times"] = times
        records.append(dict(**interval, branches=rows, feasible_count=sum(row["feasible"] for row in rows)))
        print(
            "SPLIT_A_BRANCH",
            section,
            SIDES[arm],
            interval["start"],
            interval["stop"],
            records[-1]["feasible_count"],
            flush=True,
        )
    np.savez_compressed(ROOT / "analysis/op030_split_a_branches.npz", **arrays)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        sections=records,
        all_sections_have_ik_branch=all(row["feasible_count"] for row in records),
        seed_indices=indices.tolist(),
        collisions_checked=False,
        scope="Finite IK survey; branch selection, free-transit connections and native-frame checks remain",
    )
    (ROOT / "audit/op030_split_a_branches.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("SPLIT_A_BRANCH_SURVEY_COMPLETE", report["all_sections_have_ik_branch"], flush=True)


if __name__ == "__main__":
    main()
