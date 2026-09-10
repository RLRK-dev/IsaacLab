# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Retime connected ST B paths and capture native 30 fps FK poses [m, rad, s].

Uses the retained stopped-quintic timing and exact UR15 FK implementation.
Speed caps are visualization settings, not torque or contact specifications.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS
from op030_motion import SIDES
from op030_split_b_plan import Planner, digest
from op030_split_wire_motion import WirePlacementConfig
from replay_op030_motion import path_sample, path_timing
from solve_op030_motion import NODE_IDS, R


def load_connection(prefix: str) -> tuple[Planner, dict]:
    """Load a completed connection without repeating its search [rad, s]."""
    report_path = ROOT / "audit" / (prefix + ".json")
    record = json.loads(report_path.read_text())
    if record["failures"]:
        raise ValueError("Connection contains failures; do not retime")
    path = ROOT / "analysis" / (prefix + ".npz")
    if digest(path) != record["npz_sha256"]:
        raise ValueError("Connection arrays changed")
    planner = Planner(
        record.get("prefix", "op030_split_wire_h1delta"),
        ROOT / record.get("mesh", "data/op030_split_b_meshes_angle90.npz"),
        record["config"],
    )
    expected_config = asdict(WirePlacementConfig(**record["config"]))
    if asdict(planner.sequence.config) != expected_config:
        # JSON serializes the harmless tuple dimensions as lists.
        if json.loads(json.dumps(asdict(planner.sequence.config))) != json.loads(json.dumps(expected_config)):
            raise ValueError("Sequence config changed")
    with np.load(path) as saved:
        planner.times, planner.q = saved["times"].copy(), saved["joints"].copy()
        for key in saved.files:
            if key.startswith("free_") and key.endswith("_points"):
                _, phase, order, _ = key.split("_")
                stem = f"free_{phase}_{order}_"
                planner.free_paths.setdefault(int(phase), []).append(
                    {
                        "order": int(order),
                        "arm": int(saved[stem + "arm"]),
                        "points": saved[key].copy(),
                        "fixed": saved[stem + "fixed"].copy(),
                    }
                )
    for paths in planner.free_paths.values():
        paths.sort(key=lambda item: item["order"])
    return planner, {"connection_report_sha256": digest(report_path), "connection_npz_sha256": digest(path)}


def timing(planner: Planner, velocity_cap: float, acceleration_cap: float) -> tuple[np.ndarray, list]:
    """Allocate stopped free-path timing and conservative constrained durations [s]."""
    rows, durations = [], []
    for index, phase in enumerate(planner.sequence.phases):
        authored_duration = phase["stop"] - phase["start"]
        duration = authored_duration
        if index in planner.free_paths:
            paths = planner.free_paths[index]
            for record in paths:
                record["knots"] = path_timing(record["points"], velocity_cap * 0.9, acceleration_cap * 0.9)
            total = sum(record["knots"][-1] for record in paths)
            duration = max(duration, total)
            row = {
                "free_path_segments": [len(record["points"]) - 1 for record in paths],
                "quintic_required_duration_s": float(total),
                "sequential_free_arms": [SIDES[record["arm"]] for record in paths],
                "sequential_required_durations_s": [float(record["knots"][-1]) for record in paths],
            }
        else:
            mask = (planner.times >= phase["start"] - 1e-8) & (planner.times <= phase["stop"] + 1e-8)
            t, q = planner.times[mask], planner.q[mask]
            velocity = np.gradient(q, t, axis=0, edge_order=2)
            acceleration = np.gradient(velocity, t, axis=0, edge_order=2)
            peak_v, peak_a = float(np.max(abs(velocity))), float(np.max(abs(acceleration)))
            factor = max(1.0, 1.4 * peak_v / velocity_cap, np.sqrt(1.4 * peak_a / acceleration_cap))
            if phase["turn"] is not None:
                theta = abs(phase["turn"])
                factor = max(
                    factor,
                    1.1 * 1.875 * theta / authored_duration / velocity_cap,
                    np.sqrt(1.1 * 10 / np.sqrt(3) * theta / authored_duration**2 / acceleration_cap),
                )
            duration *= factor
            row = {"initial_peak_velocity_rad_s": peak_v, "initial_peak_acceleration_rad_s2": peak_a, "scale": factor}
        # Exact display phase boundaries also fall on a native video frame.
        duration = float(np.ceil(duration * 30) / 30)
        durations.append(duration)
        rows.append(
            {
                "phase_index": index,
                "label": phase["label"],
                "author_start": phase["start"],
                "author_stop": phase["stop"],
                "duration_s": duration,
                **row,
            }
        )
    display = np.r_[0.0, np.cumsum(durations)]
    for i, row in enumerate(rows):
        row.update(start=float(display[i]), stop=float(display[i + 1]))
    return display, rows


def replay(planner: Planner, display: np.ndarray, check_meshes: bool = True) -> tuple[dict, dict]:
    """Capture native frames, recomputing exact FK and all moving geometry [s]."""
    sequence = planner.sequence
    authored = np.array([p["start"] for p in sequence.phases] + [sequence.time])
    times = np.arange(int(round(display[-1] * 30)) + 1) / 30
    author_times = np.interp(times, display, authored)
    rows, failures, hits, pair_counts = [], [], [], {}
    max_residual = 0.0
    for frame, (time, author) in enumerate(zip(times, author_times, strict=True)):
        target = sequence.evaluate(float(author))
        index = target["phase_index"]
        u = np.clip((time - display[index]) / (display[index + 1] - display[index]), 0, 1)
        q = planner.at(float(author))
        if index in planner.free_paths:
            paths = planner.free_paths[index]
            total = sum(record["knots"][-1] for record in paths)
            cursor = u * total
            for record in paths:
                duration = record["knots"][-1]
                q[record["arm"]] = path_sample(record["points"], record["knots"], np.clip(cursor / duration, 0, 1))
                cursor -= duration
        captures = {}
        for arm, side in enumerate(SIDES):
            if not target["free_hands"][arm]:
                q[arm], residual = planner.solve(float(author), arm, q[arm])
                max_residual = max(max_residual, float(residual))
                if residual > 1e-5:
                    failures.append(
                        {
                            "frame": frame,
                            "author_time": float(author),
                            "kind": "ik",
                            "arm": arm,
                            "residual": float(residual),
                        }
                    )
            if not np.all(np.isfinite(q[arm])) or np.any(abs(q[arm]) >= LIMITS):
                failures.append({"frame": frame, "kind": "joint_bounds_or_nonfinite", "arm": arm})
            robot, capture = planner.robots[side]
            robot.base_pose = target["root"] @ R.yoke_base_pose(side)
            robot.update(q[arm], float(target["grips"][arm]))
            captures.update(capture.poses)
        captures.update({577: target["root"], 578: target["root"]})
        if check_meshes:
            _, pairs = planner.score(target, q)
            if pairs:
                hits.append(
                    {
                        "frame": frame,
                        "time_s": float(time),
                        "author_time_s": float(author),
                        "label": target["label"],
                        "pairs": pairs,
                    }
                )
                for pair in pairs:
                    key = " | ".join(pair)
                    pair_counts[key] = pair_counts.get(key, 0) + 1
        wire_records = {}
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
            wire_records[number] = {
                "points": wire["shape"].centerline,
                "lugs": np.array([wire["shape"].lug_frames[end] for end in ("J1", "T")]),
                "root": root,
                "parameter": parameter,
            }
        rows.append(
            {
                "q": q.copy(),
                "grips": target["grips"],
                "poses": np.array([captures[int(node)] for node in NODE_IDS]),
                "root": target["root"],
                "clips": np.array([target["clips"][n] for n in (1, 2)]),
                "phase": index,
                "free": target["free_hands"],
                "wires": wire_records,
            }
        )
        if frame % 150 == 0:
            print(
                "OP030B_NATIVE_FRAME", frame, len(times), round(float(author), 3), len(hits), len(failures), flush=True
            )
    arrays = {
        "times": times,
        "author_times": author_times,
        "joints": np.array([row["q"] for row in rows]),
        "grips": np.array([row["grips"] for row in rows]),
        "poses": np.array([row["poses"] for row in rows]),
        "node_ids": NODE_IDS,
        "root_poses": np.array([row["root"] for row in rows]),
        "clips": np.array([row["clips"] for row in rows]),
        "phase_indices": np.array([row["phase"] for row in rows]),
        "free_joint_motion": np.array([row["free"] for row in rows]),
    }
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
    report = {
        "frames": len(times),
        "duration_s": float(times[-1]),
        "fps": 30,
        "maximum_joint_velocity_rad_s": float(np.max(abs(velocity))),
        "maximum_joint_acceleration_rad_s2": float(np.max(abs(acceleration))),
        "maximum_frame_joint_delta_rad": float(np.max(abs(np.diff(arrays["joints"], axis=0)))),
        "maximum_ik_residual": max_residual,
        "failures": failures,
        "mesh_hits": hits,
        "mesh_hit_frame_count": len(hits),
        "mesh_pair_counts": pair_counts,
        "exact_supply_support_contacts": planner.support_contacts,
        "meshes_checked": check_meshes,
    }
    return report, arrays


def main() -> None:
    """Write one immutable retimed candidate and its auxiliary audit [m, rad, s]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection", default="op030_split_b_h1delta_connection_r1")
    parser.add_argument("--output", default="op030_split_b_h1delta_native30")
    parser.add_argument("--velocity_cap", type=float, default=1.2)
    parser.add_argument("--acceleration_cap", type=float, default=2.0)
    parser.add_argument("--skip_meshes", action="store_true")
    args = parser.parse_args()
    output = ROOT / "analysis" / (args.output + ".npz")
    audit = ROOT / "audit" / (args.output + ".json")
    if output.exists() or audit.exists():
        raise FileExistsError(output)
    planner, inputs = load_connection(args.connection)
    display, phases = timing(planner, args.velocity_cap, args.acceleration_cap)
    report, arrays = replay(planner, display, not args.skip_meshes)
    np.savez_compressed(output, **arrays)
    report.update(
        observed_at=datetime.now().astimezone().isoformat(),
        config=asdict(planner.sequence.config),
        phases=phases,
        authored_duration_s=planner.sequence.time,
        clip_open_hinge_degrees=90.0,
        velocity_cap_rad_s=args.velocity_cap,
        acceleration_cap_rad_s2=args.acceleration_cap,
        speed_caps_pass=(
            report["maximum_joint_velocity_rad_s"] <= args.velocity_cap
            and report["maximum_joint_acceleration_rad_s2"] <= args.acceleration_cap
        ),
        formal_physical_verdict=None,
        output_sha256=digest(output),
        inputs=inputs,
        geometry_scope=planner.screen.export.get("scope"),
        source_sha256=digest(Path(__file__)),
        sequence_sha256=digest(ROOT / "scripts/op030_split_wire_motion.py"),
    )
    audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "OP030B_NATIVE_COMPLETE",
        report["speed_caps_pass"],
        len(report["failures"]),
        report["mesh_hit_frame_count"],
        flush=True,
    )


if __name__ == "__main__":
    main()
