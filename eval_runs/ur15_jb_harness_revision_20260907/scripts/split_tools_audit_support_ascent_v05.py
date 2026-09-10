# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read the stored A v05 bank to document paired ascent and unchanged payload [m, rad, s]."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_support_motion_v05 import support_sequence_v05
from op030_support_plan_v04 import digest


def main() -> None:
    """Compare saved data and record auxiliary evidence without modifying a bank [m, s]."""
    new_path = ROOT / "data/op030_split_a_motion_v05.npz"
    old_path = ROOT / "data/op030_split_a_motion_v04.npz"
    report_path = ROOT / "audit/op030_split_a_motion_v05.json"
    output = ROOT / "audit/op030_support_ascent_saved_v05.json"
    if output.exists():
        raise FileExistsError(output)
    references = [
        "audit/op030_split_a_motion_v04.json",
        "audit/op030_split_a_final_supported_v04_check.json",
        "audit/op030_downstream_restored_v04_motion_delta.json",
        "audit/op030_support_release_v05.json",
        "audit/op030_support_ascent_v05.json",
        "audit/op030_support_connected_v05.json",
    ]
    inputs = [new_path, old_path, report_path, Path(__file__), ROOT / "scripts/op030_support_motion_v05.py"]
    inputs += [ROOT / path for path in references]
    hashes = {str(path): digest(path) for path in inputs}
    with np.load(new_path) as saved:
        new = {key: saved[key].copy() for key in saved.files}
    with np.load(old_path) as saved:
        old = {key: saved[key].copy() for key in saved.files}
    metadata = json.loads(report_path.read_text())
    seq = support_sequence_v05()
    object_ids = {str(name): index for index, name in enumerate(new["object_names"])}
    events = []
    for record, window in zip(metadata["changed_window_timing"], seq.simultaneous_retreats, strict=True):
        first = record["start_frame_index"]
        start = first + record["frame_boundaries"][1]
        stop = first + record["frame_boundaries"][3]
        xyz = new["tools"][start : stop + 1, :, :3, 3]
        delta = xyz - xyz[0]
        ascent_frames = [int(np.flatnonzero(delta[:, arm, 2] > 1e-6)[0]) for arm in (0, 1)]
        rotation = new["tools"][start : stop + 1, :, :3, :3]
        names = ["JB_OP020_UID001", "source_0292", window["uid"]]
        held = seq.support_hold_intervals[window["number"] - 1]
        names += [row["uid"] for row in held["fasteners"]]
        use = slice(first, record["stop_frame_index"] + 1)
        static_delta = {
            name: float(
                abs(new["object_poses"][use, object_ids[name]] - new["object_poses"][first, object_ids[name]]).max()
            )
            for name in names
        }
        owner_columns = [new["ledger_uids"].tolist().index(row["uid"]) for row in held["fasteners"]]
        installed = bool(np.all(new["ledger_owner"][use][:, owner_columns] == 3))
        events.append(
            dict(
                support_uid=window["uid"],
                first_frame=first + 1,
                release_complete_frame=start + 1,
                ascent_complete_frame=stop + 1,
                release_duration_s=float(new["times"][start] - new["times"][first]),
                ascent_duration_s=float(new["times"][stop] - new["times"][start]),
                first_positive_ascent_frame=[start + index + 1 for index in ascent_frames],
                positive_ascent_threshold_m=1e-6,
                same_first_positive_ascent_frame=ascent_frames[0] == ascent_frames[1],
                xyz_displacement_m=delta[-1].tolist(),
                maximum_xy_drift_m=float(abs(delta[:, :, :2]).max()),
                maximum_rotation_matrix_delta=float(abs(rotation - rotation[0]).max()),
                maximum_left_right_z_increment_difference_m=float(abs(delta[:, 0, 2] - delta[:, 1, 2]).max()),
                minimum_frame_z_increment_m=float(np.diff(xyz[:, :, 2], axis=0).min()),
                maximum_fixed_payload_matrix_delta=static_delta,
                both_bolts_installed_before_release_and_during_ascent=installed,
            )
        )
    reused = new["reused_v04_frame_indices"] >= 0
    indices = new["reused_v04_frame_indices"][reused]
    fields = [
        "joints",
        "tools",
        "grips",
        "errors",
        "free_joint_motion",
        "spindle_angles",
        "poses",
        "object_poses",
        "labels",
        "ledger_owner",
    ]
    identity = {key: bool(np.array_equal(new[key][reused], old[key][indices])) for key in fields}
    ledger_matches = True
    for index, stamp in enumerate(new["author_times"]):
        owners = seq.evaluate(float(stamp))["ledger"]["owners"]
        codes = [
            0
            if owners[uid]["owner"] == "supply"
            else 3
            if owners[uid]["owner"] == "installed"
            else owners[uid]["arm"] + 1
            for uid in new["ledger_uids"]
        ]
        ledger_matches &= bool(np.array_equal(codes, new["ledger_owner"][index]))
    pallet_delta = float(abs(new["object_poses"][:, object_ids["source_0292"], 2, 3] - 0.789).max())
    product_delta = float(abs(new["object_poses"][:, object_ids["JB_OP020_UID001"], 2, 3] - 0.8845).max())
    first_385 = all(np.array_equal(new[key][:385], old[key][:385]) for key in fields)
    final_identity = all(np.array_equal(new[key][-1], old[key][-1]) for key in fields if key != "labels")
    elapsed = float(new["times"][-1])
    unchanged = hashes == {str(path): digest(path) for path in inputs}
    checks = dict(
        new_bank_matches_motion_report=digest(new_path) == metadata["candidate_sha256"],
        both_pairs_begin_ascent_together=all(row["same_first_positive_ascent_frame"] for row in events),
        both_arms_240mm_vertical=all(
            np.allclose(row["xyz_displacement_m"], [[0, 0, 0.240]] * 2, atol=1e-8) for row in events
        ),
        orientation_retained=all(row["maximum_rotation_matrix_delta"] < 1e-8 for row in events),
        no_downward_ascent_step=all(row["minimum_frame_z_increment_m"] >= -1e-8 for row in events),
        assembled_payload_static=all(max(row["maximum_fixed_payload_matrix_delta"].values()) < 1e-8 for row in events),
        both_bolts_installed_before_release=all(
            row["both_bolts_installed_before_release_and_during_ascent"] for row in events
        ),
        exact_v04_arrays_outside_changes=all(identity.values()),
        entire_bank_ledger_matches_factory=ledger_matches,
        fixed_pallet_and_jb_height=max(pallet_delta, product_delta) < 1e-10,
        first_385_prefill_overlap_identical=first_385,
        final_park_objects_and_loaded_uid005_identical=final_identity,
        author_times_monotone=bool(np.all(np.diff(new["author_times"]) >= -1e-8)),
        original_and_candidate_inputs_unchanged=unchanged,
    )
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        checks=checks,
        passed=all(checks.values()),
        source_inputs_sha256=hashes,
        events=events,
        reused_array_identity=identity,
        frames=len(new["times"]),
        reused_frames=int(reused.sum()),
        changed_frames=int((~reused).sum()),
        duration_s=elapsed,
        duration_reduction_s=float(old["times"][-1] - elapsed),
        final_counts=seq.evaluate(seq.time)["ledger"]["counts"],
        pallet_height_delta_m=pallet_delta,
        product_height_delta_m=product_delta,
        bank_modified=False,
        geometry_modified=False,
        limitations=[
            "Stored frames and FK triangle meshes only; not continuous collision proof.",
            "Holding force, friction, screw reaction, compliance and tolerances unverified.",
            "Existing narrow marked-face grasp calibration retained; no contact exceptions added.",
        ],
        formal_physical_validity_verdict=None,
    )
    write = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    output.write_text(write)
    print("A_V05_STORED_ASCENT", checks, flush=True)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
