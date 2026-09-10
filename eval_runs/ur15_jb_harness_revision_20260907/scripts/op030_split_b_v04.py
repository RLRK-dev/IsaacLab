# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse the saved B motion with four removed clip-only dwell phases [m, rad, s]."""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import chain_for
from op030_motion import SIDES
from op030_split_b_plan import Planner, digest
from op030_split_wire_motion import WirePlacementConfig, build_sequence
from solve_op030_motion import R

OLD_BANK = ROOT / "analysis/op030_split_b_top_entry_clip_v03_native30.npz"
OLD_AUDIT = ROOT / "audit/op030_split_b_top_entry_clip_v03_native30.json"
BANK = ROOT / "data/op030_split_b_motion_v04.npz"
AUDIT = ROOT / "audit/op030_split_b_motion_v04.json"


def load(path: Path) -> dict:
    """Load immutable numeric arrays from one recorded artifact."""
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key].copy() for key in data.files}


def prepare() -> None:
    """Remove only verified stationary clip dwells and preserve saved poses [s]."""
    if BANK.exists() or AUDIT.exists():
        raise FileExistsError(BANK)
    old, metadata = load(OLD_BANK), json.loads(OLD_AUDIT.read_text())
    if digest(OLD_BANK) != metadata["output_sha256"]:
        raise ValueError("The accepted v03 motion artifact changed")
    config = WirePlacementConfig(**(metadata["config"] | {"transport_clips": False}))
    sequence = build_sequence(config)
    removed = [p for p in metadata["phases"] if "仮保持クリップ" in p["label"] or "仮保持パッド" in p["label"]]
    if len(removed) != 4 or abs(sum(p["duration_s"] for p in removed) - 3.0) > 1e-9:
        raise ValueError("Expected exactly four stationary clip dwells totaling 3 seconds")
    keep = np.ones(len(old["times"]), dtype=bool)
    stationary_errors = {}
    for phase in removed:
        interval = (old["times"] >= phase["start"] - 1e-8) & (old["times"] <= phase["stop"] + 1e-8)
        for key in (
            "joints",
            "poses",
            "grips",
            "wire_points_1",
            "wire_points_2",
            "wire_lug_poses_1",
            "wire_lug_poses_2",
        ):
            values = old[key][interval]
            error = float(np.max(abs(values - values[0])))
            stationary_errors[key] = max(stationary_errors.get(key, 0.0), error)
        keep &= ~((old["times"] > phase["start"] + 1e-8) & (old["times"] <= phase["stop"] + 1e-8))
    if max(stationary_errors.values()) > 1e-6:
        raise ValueError(f"A clip dwell includes nonstationary motion: {stationary_errors}")
    indices = np.flatnonzero(keep)
    arrays = {key: value[keep] if key != "node_ids" else value for key, value in old.items()}
    arrays["source_frame_indices"] = indices
    arrays["source_times"] = old["times"][keep]
    arrays["source_author_times"] = old["author_times"][keep]
    arrays["times"] = np.arange(len(indices)) / 30
    author = arrays["source_author_times"].copy()
    for phase in removed:
        author -= np.clip(
            arrays["source_author_times"] - phase["author_start"], 0, phase["author_stop"] - phase["author_start"]
        )
    arrays["author_times"] = author
    arrays["clips"] = np.zeros_like(arrays["clips"])
    stops = np.array([p["stop"] for p in sequence.phases])
    arrays["phase_indices"] = np.minimum(np.searchsorted(stops, author, side="right"), len(stops) - 1)
    arrays["free_joint_motion"] = np.array([sequence.phases[i]["free_hands"] for i in arrays["phase_indices"]])
    errors = dict(root=0.0, wire=0.0, lugs=0.0, grips=0.0)
    for frame, time in enumerate(author):
        state = sequence.evaluate(float(time))
        errors["root"] = max(errors["root"], float(np.max(abs(state["root"] - arrays["root_poses"][frame]))))
        errors["grips"] = max(errors["grips"], float(np.max(abs(state["grips"] - arrays["grips"][frame]))))
        for number, uid in sequence.active_uids.items():
            shape = state["wires"][uid]["shape"]
            errors["wire"] = max(
                errors["wire"], float(np.max(abs(shape.centerline - arrays[f"wire_points_{number}"][frame])))
            )
            lugs = np.array([shape.lug_frames[end] for end in ("J1", "T")])
            errors["lugs"] = max(errors["lugs"], float(np.max(abs(lugs - arrays[f"wire_lug_poses_{number}"][frame]))))
        if frame % 600 == 0:
            print("B_V04_TARGET_REUSE", frame, len(author), max(errors.values()), flush=True)
    if max(errors.values()) > 1e-8:
        raise ValueError(f"The new target sequence differs from selected source frames: {errors}")
    velocity = np.gradient(arrays["joints"], arrays["times"], axis=0, edge_order=2)
    acceleration = np.gradient(velocity, arrays["times"], axis=0, edge_order=2)
    phases = []
    cursor = 0.0
    old_by_label = {p["label"]: p for p in metadata["phases"]}
    for index, phase in enumerate(sequence.phases):
        row = old_by_label[phase["label"]].copy()
        duration = row["duration_s"]
        row.update(
            phase_index=index,
            start=cursor,
            stop=cursor + duration,
            author_start=phase["start"],
            author_stop=phase["stop"],
        )
        phases.append(row)
        cursor += duration
    np.savez_compressed(BANK, **arrays)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        config=asdict(config),
        phases=phases,
        frames=len(author),
        duration_s=float(arrays["times"][-1]),
        authored_duration_s=sequence.time,
        fps=30,
        removed_phases=removed,
        removed_native_frames=int((~keep).sum()),
        stationary_dwell_errors=stationary_errors,
        target_reuse_errors=errors,
        saved_q_and_poses_reused_exactly=True,
        maximum_joint_velocity_rad_s=float(np.max(abs(velocity))),
        maximum_joint_acceleration_rad_s2=float(np.max(abs(acceleration))),
        geometry_checked=False,
        output_sha256=digest(BANK),
        clip_array_scope="Zero compatibility field; no clip actors, actuators or substitute restraints in v04",
        support_scope="Both lugs seated on existing studs/seats before fingers release; retention forces unverified",
        sources={
            str(p.relative_to(ROOT)): digest(p)
            for p in (OLD_BANK, OLD_AUDIT, Path(__file__), ROOT / "scripts/op030_split_wire_motion.py")
        },
        formal_physical_validity_verdict=None,
    )
    AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("B_V04_REUSE_COMPLETE", report["frames"], report["duration_s"], flush=True)


def check(mesh: Path, output: Path | None = None) -> None:
    """Check retained native poses against the actual v04 environment [m, s]."""
    output = output or ROOT / "audit/op030_split_b_motion_v04_mesh.json"
    if output.exists():
        raise FileExistsError(output)
    if output.exists():
        raise FileExistsError(output)
    metadata, bank = json.loads(AUDIT.read_text()), load(BANK)
    planner = Planner("op030_split_wire_h1delta", mesh.resolve(), metadata["config"])
    if planner.screen.export["clip_actors"]:
        raise ValueError("The v04 mesh export still contains clip actors")
    maximum_fk_error, hits, supports = 0.0, [], []
    extra = tuple(uid + end for uid in planner.sequence.active_uids.values() for end in ("_J1", "_T", "_insulation"))
    for frame, author in enumerate(bank["author_times"]):
        state = planner.sequence.evaluate(float(author))
        _, pairs = planner.score(state, bank["joints"][frame])
        # Keep both installed wires in the external check after release too.
        planner.screen.score(0, extra)
        pairs = set(map(tuple, pairs)) | set(map(tuple, planner.screen.last_pairs))
        allowed = set()
        for row in planner.sequence.rows:
            uid = row["uid"]
            if (
                uid in planner.sequence.active_uids.values()
                and np.max(
                    abs(state["wires"][uid]["shape"].centerline - planner.start_state["wires"][uid]["shape"].centerline)
                )
                < 1e-10
            ):
                allowed.update(
                    frozenset((f"OP030B_wire_supply_row{row['row']:02d}_saddle{k}", uid + "_insulation"))
                    for k in (0, 1)
                )
        actual = [p for p in sorted(pairs) if frozenset(p) not in allowed]
        supports.extend(dict(frame=frame, pair=p) for p in sorted(pairs) if frozenset(p) in allowed)
        if actual:
            hits.append(
                dict(
                    frame=frame,
                    time_s=float(bank["times"][frame]),
                    author_time_s=float(author),
                    label=state["label"],
                    pairs=actual,
                )
            )
        for arm, side in enumerate(SIDES):
            if not state["free_hands"][arm]:
                chain = chain_for(tuple((state["root"] @ R.yoke_base_pose(side)).ravel()))
                tool, _ = chain.forward(bank["joints"][frame, arm])
                maximum_fk_error = max(maximum_fk_error, float(np.max(abs(tool - state["tools"][arm]))))
        if frame % 150 == 0:
            print("B_V04_NATIVE_MESH", frame, len(bank["times"]), len(hits), maximum_fk_error, flush=True)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        frames=len(bank["times"]),
        mesh_hit_frame_count=len(hits),
        hits=hits,
        maximum_constrained_fk_matrix_error=maximum_fk_error,
        exact_rest_supply_contacts=supports,
        mesh_sha256=digest(mesh),
        bank_sha256=digest(BANK),
        config_sha256=digest(AUDIT),
        formal_physical_validity_verdict=None,
    )
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("B_V04_NATIVE_COMPLETE", len(hits), maximum_fk_error, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    check(arguments.mesh, arguments.output) if arguments.mesh else prepare()
