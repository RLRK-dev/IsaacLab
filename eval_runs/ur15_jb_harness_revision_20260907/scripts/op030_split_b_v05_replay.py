# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Replay the finite B v05 candidate and preserve v04 samples outside edits [s]."""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS, chain_for
from op030_motion import SIDES
from op030_split_b_plan import digest
from op030_split_b_v04 import load
from op030_split_b_v05 import DEFAULT_MESH, SOURCE_AUDIT, SOURCE_BANK, Candidate
from replay_op030_motion import path_sample
from solve_op030_motion import NODE_IDS, R


def write_replay(probe: str, output: str, mesh: Path) -> None:
    """Capture and check every native frame at 30 Hz against actual triangles [m, rad, s]."""
    audit_path = ROOT / "audit" / (output + ".json")
    bank_path = ROOT / "data" / (output + ".npz")
    if audit_path.exists() or bank_path.exists():
        raise FileExistsError(audit_path)
    probe_audit = ROOT / "audit" / (probe + ".json")
    probe_path = ROOT / "analysis" / (probe + ".npz")
    report = json.loads(probe_audit.read_text())
    if report["failures"] or digest(probe_path) != report["output_sha256"]:
        raise ValueError("Candidate has failures or changed arrays")
    saved = load(probe_path)
    planner = Candidate(mesh)
    seq = planner.sequence
    display = np.r_[0.0, np.cumsum([r["duration_s"] for r in report["records"]])]
    fps = 30
    phase_rows, rows, failures, hits = [], [], [], []
    max_fk, max_reuse_target, max_seam = 0.0, 0.0, 0.0
    previous_phase_end = planner.old["joints"][0].copy()
    old_row_keys = (
        "joints",
        "grips",
        "poses",
        "root_poses",
        "clips",
        "wire_points_1",
        "wire_points_2",
        "wire_lug_poses_1",
        "wire_lug_poses_2",
        "wire_control_root_1",
        "wire_control_root_2",
        "wire_parameter_1",
        "wire_parameter_2",
    )
    for index, phase in enumerate(seq.phases):
        kind = seq.phase_kinds[index]
        block = report["blocks"][str(index)]
        count = round(block["duration"] * fps)
        source_frames = saved.get(f"phase_{index}_source_indices")
        if kind == "reuse" and len(source_frames) != count + 1:
            raise ValueError("Unchanged phase duration/source sample mismatch")
        paths = []
        for path in block.get("paths", []):
            stem = f"phase_{index}_path_{path['order']}_"
            paths.append(dict(arm=path["arm"], points=saved[stem + "points"], knots=saved[stem + "knots"]))
        joints = saved[f"phase_{index}_joints"]
        previous = joints[0].copy()
        for local in range(count + (index == len(seq.phases) - 1)):
            u = local / count
            time = display[index] + local / fps
            author = phase["start"] + u * (phase["stop"] - phase["start"])
            state = seq.evaluate(float(author))
            source_frame = int(source_frames[local]) if kind == "reuse" else -1
            if source_frame >= 0:
                row = {key: planner.old[key][source_frame].copy() for key in old_row_keys}
                q = row["joints"]
                max_reuse_target = max(
                    max_reuse_target,
                    float(np.max(abs(row["grips"] - state["grips"]))),
                    float(np.max(abs(row["root_poses"] - state["root"]))),
                )
                for number, uid in seq.active_uids.items():
                    max_reuse_target = max(
                        max_reuse_target,
                        float(np.max(abs(row[f"wire_points_{number}"] - state["wires"][uid]["shape"].centerline))),
                    )
            else:
                if paths:
                    q = joints[0].copy()
                    if kind == "approach":
                        for path in paths:
                            q[path["arm"]] = path_sample(path["points"], path["knots"], u)
                    else:
                        cursor = u * sum(path["knots"][-1] for path in paths)
                        for path in paths:
                            q[path["arm"]] = path_sample(
                                path["points"], path["knots"], np.clip(cursor / path["knots"][-1], 0, 1)
                            )
                            cursor -= path["knots"][-1]
                else:
                    q = previous.copy()
                    for arm in (0, 1):
                        q[arm], residual = planner.solve(float(author), arm, previous[arm])
                        if residual > 1e-5:
                            failures.append(dict(frame=len(rows), kind="ik", arm=arm, residual=float(residual)))
                captures = {}
                for arm, side in enumerate(SIDES):
                    robot, capture = planner.robots[side]
                    robot.base_pose = state["root"] @ R.yoke_base_pose(side)
                    robot.update(q[arm], float(state["grips"][arm]))
                    captures.update(capture.poses)
                captures.update({577: state["root"], 578: state["root"]})
                row = dict(
                    joints=q.copy(),
                    grips=state["grips"],
                    poses=np.array([captures[int(n)] for n in NODE_IDS]),
                    root_poses=state["root"],
                    clips=np.array([state["clips"][n] for n in (1, 2)]),
                )
                for number, uid in seq.active_uids.items():
                    wire = state["wires"][uid]
                    control = wire["control"]
                    root = np.eye(4)
                    if control["mode"] == "bend":
                        root[:3, :3], root[:3, 3] = control["rotation"], control["center"]
                        parameter = control["progress"]
                    else:
                        center = np.eye(4)
                        center[:3, 3] = seq.bends[number].final_center
                        root = control["root"] @ center
                        parameter = 1 + control["t_raise"] / seq.config.terminal_raise
                    row[f"wire_points_{number}"] = wire["shape"].centerline
                    row[f"wire_lug_poses_{number}"] = np.array([wire["shape"].lug_frames[end] for end in ("J1", "T")])
                    row[f"wire_control_root_{number}"] = root
                    row[f"wire_parameter_{number}"] = parameter
            if local == 0 and rows:
                max_seam = max(max_seam, float(np.max(abs(q - previous_phase_end))))
            if np.any(abs(q) >= LIMITS) or not np.isfinite(q).all():
                failures.append(dict(frame=len(rows), kind="joint_bounds_or_nonfinite"))
            for arm, side in enumerate(SIDES):
                if not state["free_hands"][arm]:
                    chain = chain_for(tuple((state["root"] @ R.yoke_base_pose(side)).ravel()))
                    tool, _ = chain.forward(q[arm])
                    max_fk = max(max_fk, float(np.max(abs(tool - state["tools"][arm]))))
            pairs = planner.score_all(state, q)
            if pairs:
                hits.append(
                    dict(
                        frame=len(rows),
                        time_s=float(time),
                        author_time_s=float(author),
                        label=state["label"],
                        pairs=pairs,
                    )
                )
            row.update(
                times=float(time),
                author_times=float(author),
                phase_indices=index,
                free_joint_motion=state["free_hands"],
                source_frame_indices=source_frame,
            )
            rows.append(row)
            previous = q.copy()
            if len(rows) % 150 == 0:
                print("B_V05_NATIVE", len(rows), index, len(hits), len(failures), max_fk, flush=True)
        previous_phase_end = joints[-1].copy()
        phase_rows.append(
            dict(
                phase_index=index,
                label=phase["label"],
                kind=kind,
                source_phase=seq.source_phases[index],
                start=float(display[index]),
                stop=float(display[index + 1]),
                author_start=phase["start"],
                author_stop=phase["stop"],
                duration_s=float(block["duration"]),
            )
        )
    arrays = {key: np.array([row[key] for row in rows]) for key in rows[0]}
    arrays["times"] = np.arange(len(rows)) / fps
    arrays["node_ids"] = NODE_IDS
    arrays["source_times"] = np.where(
        arrays["source_frame_indices"] >= 0, planner.old["times"][np.maximum(arrays["source_frame_indices"], 0)], np.nan
    )
    arrays["labels"] = np.array([seq.phases[int(i)]["label"] for i in arrays["phase_indices"]])
    velocity = np.gradient(arrays["joints"], arrays["times"], axis=0, edge_order=2)
    acceleration = np.gradient(velocity, arrays["times"], axis=0, edge_order=2)
    reused = arrays["source_frame_indices"] >= 0
    reuse_errors = {
        key: float(np.max(abs(arrays[key][reused] - planner.old[key][arrays["source_frame_indices"][reused]])))
        for key in old_row_keys
    }
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        config=asdict(seq.config),
        factory="op030_split_b_v05:build_sequence",
        phases=phase_rows,
        frames=len(rows),
        fps=fps,
        duration_s=float(arrays["times"][-1]),
        authored_duration_s=seq.time,
        maximum_joint_velocity_rad_s=float(abs(velocity).max()),
        maximum_joint_acceleration_rad_s2=float(abs(acceleration).max()),
        maximum_phase_seam_joint_error_rad=max_seam,
        maximum_constrained_fk_matrix_error=max_fk,
        maximum_reused_target_error=max_reuse_target,
        reused_frame_count=int(reused.sum()),
        changed_frame_count=int((~reused).sum()),
        exact_reuse_errors=reuse_errors,
        failures=failures,
        mesh_hit_frame_count=len(hits),
        hits=hits,
        speed_caps_pass=bool(abs(velocity).max() <= 1.2 and abs(acceleration).max() <= 2.0),
        geometry_checked=True,
        mesh_sha256=digest(mesh),
        sources={
            str(p.relative_to(ROOT)): digest(p)
            for p in (
                SOURCE_BANK,
                SOURCE_AUDIT,
                probe_audit,
                probe_path,
                mesh,
                Path(__file__),
                ROOT / "scripts/op030_split_b_v05.py",
            )
        },
        formal_physical_validity_verdict=None,
    )
    passed = (
        not failures
        and not hits
        and report["speed_caps_pass"]
        and max_fk < 1e-5
        and max_seam < 1e-5
        and max_reuse_target < 1e-8
        and max(reuse_errors.values()) == 0
    )
    path = bank_path if passed else ROOT / "analysis" / (output + "_failed.npz")
    np.savez_compressed(path, **arrays)
    report.update(output_path=str(path.relative_to(ROOT)), output_sha256=digest(path), candidate_checks_pass=passed)
    audit_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "B_V05_NATIVE_COMPLETE",
        passed,
        len(rows),
        len(hits),
        report["duration_s"],
        report["maximum_joint_velocity_rad_s"],
        report["maximum_joint_acceleration_rad_s2"],
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", default="op030_split_b_parallel_v05_probe")
    parser.add_argument("--output", default="op030_split_b_motion_v05")
    parser.add_argument("--mesh", type=Path, default=DEFAULT_MESH)
    args = parser.parse_args()
    write_replay(args.probe, args.output, args.mesh)
