# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse finite branch and stationary-other transit planning for A v04 [m, rad, s]."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS, chain_for
from op030_motion import SIDES
from op030_split_a_branches import constrained_sections
from op030_split_a_connect import assignments, connect
from op030_split_a_plan import PlanningContext as PlanningContextBase
from op030_split_a_plan import compatibility, interpolate_branch, screen_branches, unique_branches
from op030_support_motion_v04 import support_sequence_v04
from solve_op030_motion import R


def digest(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_report(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


class PlanningContext(PlanningContextBase):
    """Set simultaneous actual-time targets and actual FK meshes for A v04 [m, rad, s]."""

    def __init__(self, mesh_file: str | Path):
        super().__init__(mesh_file)
        self.sequence = support_sequence_v04()


def authoring_audit() -> dict:
    """Check ownership, fixed height, held supports and world-time continuity [m, rad, s]."""
    seq = support_sequence_v04()
    times = np.unique(np.r_[np.arange(0, seq.time, 0.1), seq.time, [p["stop"] for p in seq.phases]])
    max_jump = 0.0
    for phase in seq.phases[:-1]:
        t = phase["stop"]
        before, after = seq.evaluate(t - 1e-7), seq.evaluate(t + 1e-7)
        max_jump = max(max_jump, float(abs(before["tools"] - after["tools"]).max()))
    assert max_jump < 1e-5, max_jump
    for t in times:
        state = seq.evaluate(t)
        assert abs(state["objects"]["JB_OP020_UID001"][2, 3] - 0.8845) < 1e-10
        assert abs(state["objects"]["source_0292"][2, 3] - 0.789) < 1e-10
        assert sum(state["ledger"]["counts"]["M4"].values()) == 12
        for hold in seq.support_hold_intervals:
            if hold["seat_s"] + 1e-7 < t < hold["release_s"] - 1e-7:
                phase = next(p for p in seq.phases if t <= p["stop"] + 1e-9)
                assert phase["before"]["holds"][1][0] == hold["uid"]
                assert not state["free"][1]
                assert phase["before"]["gaps"][1] == seq.support_grasp_gap_m
    for hold in seq.support_hold_intervals:
        assert len(hold["fasteners"]) == 2
        assert hold["release_s"] >= hold["fasteners"][-1]["tool_clear_s"] + 4 - 1e-8
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        factory="op030_support_motion_v04:support_sequence_v04",
        authored_duration_s=seq.time,
        work_complete_author_time_s=seq.work_complete_author_time_s,
        phases=len(seq.phases),
        sampled_states=len(times),
        maximum_boundary_target_jump=max_jump,
        support_hold_intervals=seq.support_hold_intervals,
        parallel_placement_intervals=[
            {key: value for key, value in track.items() if not isinstance(value, np.ndarray)}
            for track in seq.parallel_placements
        ],
        final_counts=seq.evaluate(seq.time)["ledger"]["counts"],
        grasp_calibration=dict(
            gap_m=seq.support_grasp_gap_m,
            height_m=seq.support_grasp_height_m,
            tilt_degrees=seq.support_grasp_tilt_degrees,
            endpoint_report="audit/split_tools_support_marked_face_v04_z016.json",
            additional_contact_exceptions=[],
        ),
        assembled_uids=seq.assembled_uids,
        end_loaded_uids=seq.end_loaded_uids,
        events=seq.fastener_events,
        scope="Target/UID authoring checks only; IK and native collision checks are separate.",
    )
    write_report(ROOT / "audit/op030_support_authoring_v04.json", result)
    print("A_V04_AUTHORING", seq.time, len(seq.phases), max_jump, flush=True)
    return result


def survey_branches() -> None:
    """Track the reused finite eight seeds in both directions per constrained section [rad, s]."""
    seq = support_sequence_v04()
    with np.load(ROOT / "data/op030_motion_v02.npz") as saved:
        indices = np.linspace(0, len(saved["joints"]) - 1, 8, dtype=int)
        seeds = saved["joints"][indices]
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
            order = list(range(len(times)))[:: -1 if reverse else 1]
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
            "A_V04_BRANCH",
            section,
            SIDES[arm],
            interval["start"],
            interval["stop"],
            records[-1]["feasible_count"],
            flush=True,
        )
    np.savez_compressed(ROOT / "analysis/op030_support_branches_v04.npz", **arrays)
    write_report(
        ROOT / "audit/op030_support_branches_v04.json",
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            sections=records,
            all_sections_have_ik_branch=all(row["feasible_count"] for row in records),
            seed_indices=indices.tolist(),
            source_sha256={
                name: digest(ROOT / "scripts" / name)
                for name in (
                    "op030_support_motion_v04.py",
                    "op030_fastener_operations_v04.py",
                    "op030_support_plan_v04.py",
                )
            },
            collisions_checked=False,
            scope="Finite continuous branch survey of concurrent placement and sustained right-arm holding.",
        ),
    )


def screen(mesh_file: Path) -> None:
    """Check individual branches and simultaneous constrained arm pairs [m, rad, s]."""
    context = PlanningContext(mesh_file)
    report = json.loads((ROOT / "audit/op030_support_branches_v04.json").read_text())
    with np.load(ROOT / "analysis/op030_support_branches_v04.npz") as saved:
        data = {key: saved[key].copy() for key in saved.files}
    sections = screen_branches(context, report, data)
    pairs = compatibility(context, sections, data) if all(row["clear_count"] for row in sections) else []
    write_report(
        ROOT / "audit/op030_support_native_branches_v04.json",
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            mesh_file=str(mesh_file),
            mesh_sha256=digest(mesh_file),
            sections=sections,
            compatibility=pairs,
            all_sections_have_individually_clear_branch=all(row["clear_count"] for row in sections),
            scope="Simultaneous actual-time constrained targets; complete native playback remains.",
        ),
    )


def endpoint_screen(mesh_file: Path) -> None:
    """Inspect four tightening endpoints with the supporting right arm present [m, rad, s]."""
    context = PlanningContext(mesh_file)
    report = json.loads((ROOT / "audit/op030_support_branches_v04.json").read_text())
    with np.load(ROOT / "analysis/op030_support_branches_v04.npz") as saved:
        data = {key: saved[key].copy() for key in saved.files}
    results = []
    for hold in context.sequence.support_hold_intervals:
        for fastener in hold["fasteners"]:
            time = fastener["tool_empty_s"] - 1e-7
            target = context.sequence.evaluate(time)
            candidates = {}
            for arm in (0, 1):
                index, section = next(
                    (i, row)
                    for i, row in enumerate(report["sections"])
                    if row["arm"] == arm and row["start"] <= time <= row["stop"]
                )
                chain = chain_for(tuple((target["root"] @ R.yoke_base_pose(SIDES[arm])).ravel()))
                candidates[arm] = []
                for branch in unique_branches(section, data):
                    seed = interpolate_branch(data, index, branch, time)
                    q, error = chain.solve_continuous(target["tools"][arm], seed)
                    assert error < 1e-5
                    candidates[arm].append((branch["array_key"], q))
            pairs = []
            for left, q_left in candidates[0]:
                for right, q_right in candidates[1]:
                    score, hits = context.query(time, np.asarray([q_left, q_right]))
                    pairs.append(dict(left=left, right=right, score=score, hits=hits))
            row = dict(
                uid=fastener["uid"], author_time_s=time, pairs=pairs, clear_count=sum(p["score"] == 0 for p in pairs)
            )
            results.append(row)
            print("A_V04_ENDPOINT", row["uid"], row["clear_count"], "/", len(pairs), flush=True)
    write_report(
        ROOT / "audit/op030_support_endpoints_v04.json",
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            mesh_file=str(mesh_file),
            mesh_sha256=digest(mesh_file),
            endpoints=results,
            scope="Four simultaneous tightening/support endpoint probes; old mesh if supplied, "
            "not full v04 geometry qualification.",
        ),
    )


def connect_branches(mesh_file: Path) -> None:
    """Reuse existing free connections with stationary other-arm assertions intact [rad, s]."""
    report = json.loads((ROOT / "audit/op030_support_native_branches_v04.json").read_text())
    assert report["mesh_sha256"] == digest(mesh_file)
    with np.load(ROOT / "analysis/op030_support_branches_v04.npz") as saved:
        data = {key: saved[key].copy() for key in saved.files}
    context, attempts = PlanningContext(mesh_file), []
    for index, (cost, assignment) in enumerate(assignments(report, data)[:4]):
        result, failure = connect(
            context, report, data, assignment, ROOT / "audit/op030_support_connect_progress_v04.json"
        )
        attempts.append(dict(index=index, cost=cost, failure=failure))
        if result is None:
            continue
        arrays = {f"section_{k}_joints": value for k, value in result.pop("selected").items()}
        arrays.update({key: value for key, value in data.items() if key.endswith("_times")})
        bank = ROOT / "analysis/op030_support_connected_v04.npz"
        np.savez_compressed(bank, **arrays)
        write_report(
            ROOT / "audit/op030_support_connected_v04.json",
            dict(
                **result,
                observed_at=datetime.now().astimezone().isoformat(),
                mesh_file=str(mesh_file),
                mesh_sha256=digest(mesh_file),
                branch_report=str(ROOT / "audit/op030_support_native_branches_v04.json"),
                branch_report_sha256=digest(ROOT / "audit/op030_support_native_branches_v04.json"),
                connected_bank=str(bank),
                connected_bank_sha256=digest(bank),
                sections=report["sections"],
                attempts=attempts,
                connected=True,
            ),
        )
        print("A_V04_CONNECTED", len(result["free_paths"]), flush=True)
        return
    write_report(ROOT / "audit/op030_support_connect_failure_v04.json", dict(attempts=attempts))
    raise RuntimeError("Finite four branch assignments did not connect")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("author", "branches", "endpoints", "screen", "connect"), required=True)
    parser.add_argument("--mesh_file", type=Path)
    args = parser.parse_args()
    if args.stage == "author":
        authoring_audit()
    elif args.stage == "branches":
        survey_branches()
    elif args.stage == "screen":
        screen(args.mesh_file)
    elif args.stage == "endpoints":
        endpoint_screen(args.mesh_file)
    else:
        connect_branches(args.mesh_file)


if __name__ == "__main__":
    main()
