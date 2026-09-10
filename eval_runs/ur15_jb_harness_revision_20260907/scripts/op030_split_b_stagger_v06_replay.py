# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Retime and capture simultaneous B stagger paths with retained FK/meshes [m, rad, s].

Reuse the original timing and native replay contract. Only simultaneous 12D
free interpolation and the explicit final factory differ from the legacy
station replay. No arm-only score replacement or contact exemption is added.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS
from op030_motion import SIDES
from op030_split_b_plan import digest
from op030_split_b_replay import timing as legacy_timing
from op030_split_b_stagger_v06 import build_sequence_final
from op030_split_b_stagger_v06_connect import ConnectedCandidate
from op030_split_wire_motion import WirePlacementConfig
from replay_op030_motion import path_sample
from solve_op030_motion import NODE_IDS, R


def load_connection(prefix: str) -> tuple[ConnectedCandidate, dict]:
    """Read a completed simultaneous connection without solving a new path [rad, s]."""
    audit, path = ROOT / "audit" / (prefix + ".json"), ROOT / "analysis" / (prefix + ".npz")
    record = json.loads(audit.read_text())
    if record["failures"] or record.get("constraints", {}).get("hits"):
        raise ValueError("Connection has unresolved IK/mesh failures")
    if digest(path) != record["output_sha256"]:
        raise ValueError("Connection NPZ digest changed")
    mesh = Path(record["mesh"])
    mesh = mesh if mesh.is_absolute() else ROOT / mesh
    if digest(mesh) != record["mesh_sha256"]:
        raise ValueError("Actual connection mesh digest changed")
    variant = record["variant"]
    planner = ConnectedCandidate(record["survey"], mesh, float(variant.get("h1_yaw_bias_degrees", 0.0)))
    if json.loads(json.dumps(asdict(planner.sequence.config))) != record["config"]:
        raise ValueError("Survey and connected-source configs differ")
    planner.sequence = build_sequence_final(WirePlacementConfig(**record["config"]))
    planner.screen.sequence = planner.sequence
    planner.start_state = planner.sequence.evaluate(0.0)
    for key, value in variant.items():
        if getattr(planner.sequence, key) != value:
            raise ValueError("Final factory variant differs: " + key)
    phases = [{key: phase[key] for key in ("label", "start", "stop")} for phase in planner.sequence.phases]
    if phases != record["phases"]:
        raise ValueError("Final factory phase timing/labels differ from the connected source")
    planner.free_paths, planner.combined_free = {}, {}
    with np.load(path, allow_pickle=False) as saved:
        planner.times, planner.q = saved["times"].copy(), saved["joints"].copy()
        for key in saved.files:
            if not key.startswith("free_") or not key.endswith("_points"):
                continue
            _, number, _ = key.split("_")
            index = int(number)
            points, knots = saved[key].copy(), saved[f"free_{index}_knots"].copy()
            if points.ndim != 3 or points.shape[1:] != (2, 6) or len(points) < 2:
                raise ValueError("Combined free path must have shape [K, 2, 6]")
            if not np.all(np.isfinite(points)) or np.any(abs(points) >= LIMITS):
                raise ValueError("Combined free path has invalid joints")
            if knots.shape != (len(points),) or knots[0] != 0 or np.any(np.diff(knots) <= 0):
                raise ValueError("Combined free knots must increase from zero")
            planner.combined_free[index] = dict(points=points, knots=knots)
    if planner.q.shape != (len(planner.times), 2, 6) or np.any(np.diff(planner.times) <= 0):
        raise ValueError("Invalid constrained source array shape/time order")
    required = set()
    for index, phase in enumerate(planner.sequence.phases):
        if any(phase["free_hands"]):
            if not all(phase["free_hands"]):
                raise ValueError("Unexpected unilateral free phase")
            required.add(index)
            first, last = planner.sequence.evaluate(phase["start"]), planner.sequence.evaluate(phase["stop"] - 1e-9)
            if np.max(abs(first["root"] - last["root"])) > 1e-8 or first["holds"] or last["holds"]:
                raise ValueError("Combined free phase must have an unchanged torso and empty hands")
    if set(planner.combined_free) != required:
        raise ValueError("Missing or unexpected simultaneous free paths")
    return planner, dict(
        connection_report=str(audit),
        connection_report_sha256=digest(audit),
        connection_npz=str(path),
        connection_npz_sha256=digest(path),
        mesh=str(mesh),
        mesh_sha256=digest(mesh),
        factory="op030_split_b_stagger_v06:build_sequence_final",
        variant=variant,
        factory_sha256=digest(ROOT / "scripts/op030_split_b_stagger_v06.py"),
    )


def timing(planner: ConnectedCandidate, velocity_cap: float, acceleration_cap: float) -> tuple[np.ndarray, list]:
    """Reuse stopped-quintic timing with joint/torso caps [rad/s, rad/s²]."""
    if not 0 < velocity_cap <= 1.2 or not 0 < acceleration_cap <= 2.0:
        raise ValueError("v06 visualization caps must be positive and at most 1.2 rad/s and 2 rad/s²")
    # Legacy timing is dimension independent for its path calculation. A
    # single flattened record represents one simultaneous path, not two arms
    # summed in sequence. Its legacy arm label is replaced in the audit below.
    records = {
        index: [dict(points=record["points"].reshape(-1, 12), arm=0)] for index, record in planner.combined_free.items()
    }
    proxy = SimpleNamespace(sequence=planner.sequence, times=planner.times, q=planner.q, free_paths=records)
    _, rows = legacy_timing(proxy, velocity_cap, acceleration_cap)
    for index, (phase, row) in enumerate(zip(planner.sequence.phases, rows, strict=True)):
        authored_duration = phase["stop"] - phase["start"]
        sample_times = np.unique(
            np.r_[
                np.linspace(phase["start"], phase["stop"], max(5, int(np.ceil(authored_duration / 0.1)) + 1)),
                planner.times[(planner.times >= phase["start"]) & (planner.times <= phase["stop"])],
            ]
        )
        # Round numerical duplicate boundary timestamps before differentiation.
        sample_times = np.unique(np.round(sample_times, 10))
        yaw = np.unwrap([planner.sequence.evaluate(float(time))["yaw"] for time in sample_times])
        velocity = np.gradient(yaw, sample_times, edge_order=2)
        acceleration = np.gradient(velocity, sample_times, edge_order=2)
        peak_v, peak_a = float(np.max(abs(velocity))), float(np.max(abs(acceleration)))
        factor = max(1.0, 1.4 * peak_v / velocity_cap, np.sqrt(1.4 * peak_a / acceleration_cap))
        row["duration_s"] = float(np.ceil(max(row["duration_s"], authored_duration * factor) * 30) / 30)
        row.update(initial_peak_torso_velocity_rad_s=peak_v, initial_peak_torso_acceleration_rad_s2=peak_a)
        if index in planner.combined_free:
            planner.combined_free[index]["knots"] = records[index][0]["knots"]
            row.pop("sequential_free_arms")
            row.pop("sequential_required_durations_s")
            row["simultaneous_free_arms"] = list(SIDES)
            row["state_dimension"] = 12
    display = np.r_[0.0, np.cumsum([row["duration_s"] for row in rows])]
    for index, row in enumerate(rows):
        row.update(start=float(display[index]), stop=float(display[index + 1]))
    return display, rows


def replay(planner: ConnectedCandidate, display: np.ndarray, check_meshes: bool = True) -> tuple[dict, dict]:
    """Capture original-FK 30 Hz frames and simultaneous actual-mesh scores [m, rad, s]."""
    sequence = planner.sequence
    authored = np.array([phase["start"] for phase in sequence.phases] + [sequence.time])
    if display.shape != authored.shape or np.any(np.diff(display) <= 0):
        raise ValueError("Display phase boundaries must strictly increase and match the factory")
    times = np.arange(int(round(display[-1] * 30)) + 1) / 30
    author_times = np.interp(times, display, authored)
    rows, failures, hits, pair_counts = [], [], [], {}
    maximum_residual, maximum_original_fk, checked_frames = 0.0, 0.0, 0
    for frame, (time, author) in enumerate(zip(times, author_times, strict=True)):
        target = sequence.evaluate(float(author))
        index = target["phase_index"]
        fraction = float(np.clip((time - display[index]) / (display[index + 1] - display[index]), 0, 1))
        q = planner.at(float(author)).copy()
        if index in planner.combined_free:
            free = planner.combined_free[index]
            q = path_sample(free["points"].reshape(-1, 12), free["knots"], fraction).reshape(2, 6)
        captures = {}
        valid = True
        for arm, side in enumerate(SIDES):
            if not target["free_hands"][arm]:
                q[arm], residual = planner.solve(float(author), arm, q[arm])
                maximum_residual = max(maximum_residual, float(residual))
                if residual > 1e-5:
                    failures.append(
                        dict(frame=frame, author_time=float(author), kind="ik", arm=arm, residual=float(residual))
                    )
            if not np.all(np.isfinite(q[arm])) or np.any(abs(q[arm]) >= LIMITS):
                failures.append(dict(frame=frame, kind="joint_bounds_or_nonfinite", arm=arm))
                valid = False
            if not np.all(np.isfinite(q[arm])):
                raise ValueError("Nonfinite native joints cannot be passed to FK/mesh capture")
            robot, capture = planner.robots[side]
            robot.base_pose = target["root"] @ R.yoke_base_pose(side)
            robot.update(q[arm], float(target["grips"][arm]))
            captures.update(capture.poses)
            if not target["free_hands"][arm]:
                actual = R.UR15.forward(robot.base_pose, q[arm])[1]
                matrix_error = float(np.max(abs(actual - target["tools"][arm])))
                maximum_original_fk = max(maximum_original_fk, matrix_error)
                if matrix_error > 1e-5:
                    failures.append(dict(frame=frame, kind="original_fk_target", arm=arm, matrix_error=matrix_error))
        captures.update({577: target["root"], 578: target["root"]})
        if check_meshes and valid:
            # score_all calls the original score internally; overriding score
            # with this method would recurse and is deliberately avoided.
            pairs = planner.score_all(target, q)
            checked_frames += 1
            if pairs:
                hits.append(
                    dict(
                        frame=frame,
                        time_s=float(time),
                        author_time_s=float(author),
                        label=target["label"],
                        pairs=[list(pair) for pair in pairs],
                    )
                )
                for pair in pairs:
                    key = " | ".join(pair)
                    pair_counts[key] = pair_counts.get(key, 0) + 1
        wires = {}
        for number, uid in sequence.active_uids.items():
            wire = target["wires"][uid]
            control = wire["control"]
            root = np.eye(4)
            if control["mode"] == "bend":
                root[:3, :3], root[:3, 3] = control["rotation"], control["center"]
                parameter = control["progress"]
            else:
                center = np.eye(4)
                center[:3, 3] = sequence.bends[number].final_center
                root = control["root"] @ center
                parameter = 1.0 + control["t_raise"] / sequence.config.terminal_raise
            wires[number] = dict(
                points=wire["shape"].centerline,
                lugs=np.array([wire["shape"].lug_frames[end] for end in ("J1", "T")]),
                root=root,
                parameter=parameter,
            )
        rows.append(
            dict(
                q=q.copy(),
                grips=target["grips"],
                poses=np.array([captures[int(node)] for node in NODE_IDS]),
                root=target["root"],
                yaw=float(target["yaw"]),
                clips=np.array([target["clips"][n] for n in (1, 2)]),
                phase=index,
                free=target["free_hands"],
                wires=wires,
                label=target["label"],
            )
        )
        if frame % 150 == 0:
            print(
                "B_STAGGER_NATIVE_FRAME",
                frame,
                len(times),
                round(float(author), 3),
                len(hits),
                len(failures),
                flush=True,
            )
    arrays = dict(
        times=times,
        author_times=author_times,
        joints=np.array([row["q"] for row in rows]),
        grips=np.array([row["grips"] for row in rows]),
        poses=np.array([row["poses"] for row in rows]),
        node_ids=NODE_IDS,
        root_poses=np.array([row["root"] for row in rows]),
        torso_yaw=np.array([row["yaw"] for row in rows]),
        clips=np.array([row["clips"] for row in rows]),
        phase_indices=np.array([row["phase"] for row in rows]),
        free_joint_motion=np.array([row["free"] for row in rows]),
        labels=np.array([row["label"] for row in rows]),
    )
    for number in (1, 2):
        for key, source in (
            ("wire_points", "points"),
            ("wire_lug_poses", "lugs"),
            ("wire_control_root", "root"),
            ("wire_parameter", "parameter"),
        ):
            arrays[f"{key}_{number}"] = np.array([row["wires"][number][source] for row in rows])
    velocity = np.gradient(arrays["joints"], times, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
    torso_velocity = np.gradient(np.unwrap(arrays["torso_yaw"]), times, edge_order=2)
    torso_acceleration = np.gradient(torso_velocity, times, edge_order=2)
    report = dict(
        frames=len(times),
        duration_s=float(times[-1]),
        fps=30,
        maximum_joint_velocity_rad_s=float(np.max(abs(velocity))),
        maximum_joint_acceleration_rad_s2=float(np.max(abs(acceleration))),
        maximum_torso_velocity_rad_s=float(np.max(abs(torso_velocity))),
        maximum_torso_acceleration_rad_s2=float(np.max(abs(torso_acceleration))),
        maximum_frame_joint_delta_rad=float(np.max(abs(np.diff(arrays["joints"], axis=0)))),
        maximum_ik_residual=maximum_residual,
        maximum_original_fk_matrix_error=maximum_original_fk,
        failures=failures,
        mesh_hits=hits,
        mesh_hit_frame_count=len(hits),
        mesh_pair_counts=pair_counts,
        exact_supply_support_contacts=planner.support_contacts,
        meshes_checked=check_meshes,
        actual_mesh_frames=checked_frames,
        all_frames_mesh_checked=bool(check_meshes and checked_frames == len(times)),
        simultaneous_free_phases=sorted(planner.combined_free),
        contact_exemptions_added=[],
    )
    return report, arrays


def main() -> None:
    """Save one new B bank/audit, retaining failures and all prior versions [m, rad, s]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection", required=True)
    parser.add_argument("--output", default="op030_split_b_stagger_motion_v06")
    parser.add_argument("--output_dir", choices=("analysis", "data"), default="data")
    parser.add_argument("--velocity_cap", type=float, default=1.2)
    parser.add_argument("--acceleration_cap", type=float, default=2.0)
    args = parser.parse_args()
    output, audit = ROOT / args.output_dir / (args.output + ".npz"), ROOT / "audit" / (args.output + ".json")
    if output.exists() or audit.exists():
        raise FileExistsError(output)
    planner, inputs = load_connection(args.connection)
    display, phases = timing(planner, args.velocity_cap, args.acceleration_cap)
    report, arrays = replay(planner, display)
    unchanged = {
        "connection_npz": digest(Path(inputs["connection_npz"])) == inputs["connection_npz_sha256"],
        "connection_report": digest(Path(inputs["connection_report"])) == inputs["connection_report_sha256"],
        "mesh": digest(Path(inputs["mesh"])) == inputs["mesh_sha256"],
        "factory": digest(ROOT / "scripts/op030_split_b_stagger_v06.py") == inputs["factory_sha256"],
    }
    if not all(unchanged.values()):
        report["failures"].append(dict(kind="source_changed_during_replay", unchanged=unchanged))
    np.savez_compressed(output, **arrays)
    caps = (
        report["maximum_joint_velocity_rad_s"] <= args.velocity_cap
        and report["maximum_joint_acceleration_rad_s2"] <= args.acceleration_cap
        and report["maximum_torso_velocity_rad_s"] <= args.velocity_cap
        and report["maximum_torso_acceleration_rad_s2"] <= args.acceleration_cap
    )
    report.update(
        observed_at=datetime.now().astimezone().isoformat(),
        config=asdict(planner.sequence.config),
        factory="op030_split_b_stagger_v06:build_sequence_final",
        variant=inputs["variant"],
        phases=phases,
        authored_duration_s=planner.sequence.time,
        velocity_cap_rad_s=args.velocity_cap,
        acceleration_cap_rad_s2=args.acceleration_cap,
        speed_caps_pass=bool(caps),
        passed=bool(caps and not report["failures"] and not report["mesh_hits"] and report["all_frames_mesh_checked"]),
        formal_physical_verdict=None,
        output_sha256=digest(output),
        inputs=inputs,
        input_digests_unchanged=unchanged,
        geometry_scope=planner.screen.export.get("scope"),
        source_sha256=digest(Path(__file__)),
        reused_timing_sha256=digest(ROOT / "scripts/op030_split_b_replay.py"),
        sequence_sha256=digest(ROOT / "scripts/op030_split_b_stagger_v06.py"),
    )
    audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("B_STAGGER_NATIVE_COMPLETE", report["passed"], report["frames"], report["duration_s"], flush=True)


if __name__ == "__main__":
    main()
