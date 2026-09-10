# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read stored C v05 timing, finite ownership and actual path distances [m, rad, s]."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_c_refill_v05 import refill_phases
from op030_definition import ROOT
from op030_split_c_front_v05 import BANK, MESH, build_sequence
from op030_split_c_v04 import digest, load
from op030_split_c_v05 import combined_row, drive_phases, source_tracks
from op030_split_tools import SIZES
from scipy.spatial.transform import Rotation


def main() -> None:
    """Audit completed arrays without modifying motion, mesh or input reports [m, rad, s]."""
    output = ROOT / "audit/op030_c_front_saved_identity_v05_02.json"
    if output.exists():
        raise FileExistsError(output)
    data = load(BANK)
    old_path = ROOT / "data/op030_split_c_motion_v04.npz"
    old = load(old_path)
    source, _, tracks = source_tracks()
    report_path = ROOT / "audit/op030_c_front_indexed_replay_v05.json"
    mesh_report_path = ROOT / "audit/op030_c_front_final_mesh_v05.json"
    report = json.loads(report_path.read_text())
    mesh_report = json.loads(mesh_report_path.read_text())
    mesh_metadata = json.loads(MESH.with_suffix(".json").read_text())
    paths = [Path(__file__), BANK, old_path, report_path, mesh_report_path, MESH, MESH.with_suffix(".json")]
    hashes = {str(path): digest(path) for path in paths}
    names = {str(name): index for index, name in enumerate(data["object_names"])}
    times, ledger = data["times"], data["ledger_owner"]
    uids = [str(uid) for uid in data["ledger_uids"]]
    preload = int(data["preload_frame_count"])
    checks = {}
    checks["prefill_264_frames_and_two_loaded_tools"] = preload == 264 and (
        np.sum(ledger[preload - 1] == 1) == 1 and np.sum(ledger[preload - 1] == 2) == 1
    )
    checks["initial_and_final_same_waiting_joint_branch"] = bool(
        abs(data["joints"][0] - data["joints"][-1]).max() < 1e-6
    )
    checks["single_30hz_clock"] = bool(np.array_equal(times, np.arange(len(times)) / 30))
    checks["all_24_physical_uids_once"] = len(uids) == len(set(uids)) == 24 and all(uid in names for uid in uids)
    checks["all_poses_finite_rigid"] = bool(
        np.isfinite(data["object_poses"]).all()
        and abs(np.linalg.det(data["object_poses"][..., :3, :3]) - 1).max() < 1e-6
        and abs(data["object_poses"][..., 3, :] - [0, 0, 0, 1]).max() < 1e-9
    )
    owners, transitions = {}, []
    relative_errors, installed_drifts = [], []
    for column, uid in enumerate(uids):
        arm, size = (1, "M14") if "M14" in uid else (0, "M6")
        changes = np.flatnonzero(np.r_[True, np.diff(ledger[:, column]) != 0])
        states = ledger[changes, column].tolist()
        owners[uid] = states
        transitions.append(
            dict(uid=uid, states=states, frames_1_based=(changes + 1).tolist(), times_s=times[changes].tolist())
        )
        selected = np.flatnonzero(ledger[:, column] == arm + 1)
        if len(selected):
            world = data["object_poses"][selected, names[uid]]
            driver = data["object_poses"][selected, names["OP030C_driver_" + size]]
            relative = np.linalg.inv(driver) @ world
            reverse_spin = np.tile(np.eye(4), (len(selected), 1, 1))
            reverse_spin[:, :3, :3] = Rotation.from_euler("z", -data["spindle_angles"][selected, arm, None]).as_matrix()
            unspun = reverse_spin @ relative
            relative_errors.append(
                dict(uid=uid, frames=len(selected), maximum_unspun_relative_error=float(abs(unspun - unspun[0]).max()))
            )
        installed = np.flatnonzero(ledger[:, column] == 3)
        if len(installed):
            matrices = data["object_poses"][installed, names[uid]]
            installed_drifts.append(dict(uid=uid, maximum_matrix_drift=float(abs(matrices - matrices[0]).max())))
    checks["legal_supply_tool_product_transitions"] = all(
        states in ([0], [0, 2 if "M14" in uid else 1], [0, 2 if "M14" in uid else 1, 3])
        for uid, states in owners.items()
    )
    checks["at_most_one_fastener_per_tool_every_frame"] = bool(
        (np.sum(ledger == 1, axis=1) <= 1).all() and (np.sum(ledger == 2, axis=1) <= 1).all()
    )
    checks["held_fastener_follows_independent_spindle"] = (
        max(row["maximum_unspun_relative_error"] for row in relative_errors) < 1e-6
    )
    checks["installed_fasteners_remain_static"] = max(row["maximum_matrix_drift"] for row in installed_drifts) < 1e-6
    inventory = {}
    for size in ("M6", "M14"):
        columns = [index for index, uid in enumerate(uids) if size in uid]
        arm_code = 1 if size == "M6" else 2
        inventory[size] = {
            label: {
                owner: int(np.sum(ledger[index, columns] == code))
                for owner, code in (("supply", 0), ("tool", arm_code), ("product", 3))
            }
            for label, index in (("initial", 0), ("preloaded", preload - 1), ("final", len(times) - 1))
        }
    checks["final_inventory_each_9_supply_1_tool_2_product"] = all(
        row["final"] == dict(supply=9, tool=1, product=2) for row in inventory.values()
    )
    synchronized = []
    for number in (2, 1):
        event = next(
            event
            for event in report["events"]
            if event["kind"] == "paired_spin" and event["label"].startswith(f"H03-{number}／")
        )
        start, stop = event["start_frame"], event["stop_frame"]
        record = dict(
            number=number,
            start_frame_1_based=start + 1,
            stop_frame_1_based=stop + 1,
            start_s=times[start],
            stop_s=times[stop],
            arms=[],
        )
        for arm, size in enumerate(("M6", "M14")):
            spin = data["spindle_angles"][start : stop + 1, arm]
            driver = data["object_poses"][start : stop + 1, names["OP030C_driver_" + size]]
            axis = driver[0, :3, 2]
            travel = -(driver[:, :3, 3] - driver[0, :3, 3]) @ axis
            first = np.flatnonzero(abs(spin - spin[0]) > 1e-8)[0]
            pitch_error = abs(travel + (spin - spin[0]) / (2 * np.pi) * SIZES[size]["pitch"]).max()
            record["arms"].append(
                dict(
                    size=size,
                    first_rotating_frame_1_based=int(start + first + 1),
                    travel_m=float(travel[-1]),
                    rotations=float((spin[-1] - spin[0]) / (2 * np.pi)),
                    pitch_translation_error_m=float(pitch_error),
                )
            )
        withdraw = next(
            event
            for event in report["events"]
            if event["kind"] == "paired_withdraw80" and event["label"].startswith(f"H03-{number}／")
        )
        first, last = withdraw["start_frame"], withdraw["stop_frame"]
        endpoints = data["object_poses"][[first, last]]
        p = np.take(endpoints, [names["OP030C_driver_M6"], names["OP030C_driver_M14"]], axis=1)[..., :3, 3]
        record["withdrawal_world_delta_m"] = (p[1] - p[0]).tolist()
        synchronized.append(record)
    checks["both_thread_advances_start_same_native_frame"] = all(
        row["arms"][0]["first_rotating_frame_1_based"] == row["arms"][1]["first_rotating_frame_1_based"]
        for row in synchronized
    )
    checks["pitch_consistent_with_both_native_spindles"] = (
        max(arm["pitch_translation_error_m"] for row in synchronized for arm in row["arms"]) < 1e-6
    )
    checks["both_mandatory_80mm_withdrawals"] = (
        max(abs(np.asarray(row["withdrawal_world_delta_m"]) - [0, 0, 0.080]).max() for row in synchronized) < 1e-6
    )
    distances = []
    for number in (2, 1):
        drive, refill = drive_phases(tracks, number), refill_phases(tracks, number)
        start = next(
            event["stop_frame"]
            for event in report["events"]
            if event["kind"] == "paired_withdraw80" and event["label"].startswith(f"H03-{number}／")
        )
        stop = max(
            event["stop_frame"]
            for event in report["events"]
            if event["kind"] == "direct_refill" and event["label"].startswith(f"H03-{number}／")
        )
        for arm, size in enumerate(("M6", "M14")):
            a = drive[arm][3]["stop_frame"]
            b = next(phase["stop_frame"] for phase in refill[arm] if phase["label"].endswith("／固定工具を供給上方へ"))
            local = [a, a]
            samples = []
            for index in range(a, b + 1):
                local[arm] = index
                local[1 - arm] = drive[1 - arm][3]["stop_frame"]
                samples.append(combined_row(source, tracks, *local))
            calibration = np.asarray(mesh_metadata["fixed_tools"]["OP030C_" + size]["flange_to_tcp"])
            old_q = np.asarray([row["joints"][arm] for row in samples])
            old_tcp = np.asarray([row["tools"][arm] @ calibration for row in samples])[:, :3, 3]
            new_q = data["joints"][start : stop + 1, arm]
            new_tcp = data["object_poses"][start : stop + 1, names["OP030C_driver_" + size], :3, 3]
            distances.append(
                dict(
                    number=number,
                    size=size,
                    original_joint_path_rad=float(np.linalg.norm(np.diff(old_q, axis=0), axis=1).sum()),
                    new_joint_path_rad=float(np.linalg.norm(np.diff(new_q, axis=0), axis=1).sum()),
                    original_tcp_path_m=float(np.linalg.norm(np.diff(old_tcp, axis=0), axis=1).sum()),
                    new_tcp_path_m=float(np.linalg.norm(np.diff(new_tcp, axis=0), axis=1).sum()),
                )
            )
    checks["all_refill_joint_and_tcp_paths_shorter"] = all(
        row["new_joint_path_rad"] < row["original_joint_path_rad"]
        and row["new_tcp_path_m"] < row["original_tcp_path_m"]
        for row in distances
    )
    transition_continuity = []
    for record in transitions:
        index = names[record["uid"]]
        arm = int("M14" in record["uid"])
        size = "M14" if arm else "M6"
        driver_index = names["OP030C_driver_" + size]
        for frame in record["frames_1_based"][1:]:
            k = frame - 1
            previous = data["object_poses"][k - 1, index]
            current = data["object_poses"][k, index]
            if ledger[k, index_uids := uids.index(record["uid"])] == 3:
                prior_tcp = data["object_poses"][k - 1, driver_index]
                current_tcp = data["object_poses"][k, driver_index]
                prior_spin, current_spin = np.eye(4), np.eye(4)
                prior_spin[:3, :3] = Rotation.from_euler("z", -data["spindle_angles"][k - 1, arm]).as_matrix()
                current_spin[:3, :3] = Rotation.from_euler("z", data["spindle_angles"][k, arm]).as_matrix()
                unspun = prior_spin @ np.linalg.inv(prior_tcp) @ previous
                expected = current_tcp @ current_spin @ unspun
                kind = "release after the final native thread increment"
            else:
                expected = previous
                kind = "attach stationary supply UID"
            transition_continuity.append(
                dict(
                    uid=record["uid"],
                    frame_1_based=frame,
                    kind=kind,
                    raw_frame_matrix_delta=float(abs(current - previous).max()),
                    handoff_prediction_error=float(abs(current - expected).max()),
                    old_owner=int(ledger[k - 1, index_uids]),
                    new_owner=int(ledger[k, index_uids]),
                )
            )
    checks["ownership_pose_matches_driver_spindle_at_transfer"] = (
        max(row["handoff_prediction_error"] for row in transition_continuity) < 1e-6
    )
    phase = data["spindle_angles"][[0, -1]] - [np.pi, 0]
    checks["initial_final_output_phase_pi_zero_modulo_full_turns"] = bool(
        abs(np.arctan2(np.sin(phase), np.cos(phase))).max() < 1e-8
    )
    factory = build_sequence()
    maximum = 0.0
    for index, time in enumerate(times):
        state = factory.evaluate(float(time))
        for key in ("tools", "spindle_angles"):
            maximum = max(maximum, float(abs(state[key] - data[key][index]).max()))
        maximum = max(
            maximum,
            float(
                abs(
                    np.asarray([state["objects"][str(name)] for name in data["object_names"]])
                    - data["object_poses"][index]
                ).max()
            ),
        )
    checks["factory_exact_saved_states"] = maximum == 0
    checks["full_native_mesh_report_matches_bank"] = mesh_report["passed"] and mesh_report["bank_sha256"] == digest(
        BANK
    )
    checks["inputs_unchanged"] = hashes == {str(path): digest(path) for path in paths}
    checks = {key: bool(value) for key, value in checks.items()}
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        source_inputs_sha256=hashes,
        checks=checks,
        passed=all(checks.values()),
        frames=len(times),
        duration_s=float(times[-1]),
        old_duration_s=float(old["times"][-1]),
        reduction_s=float(old["times"][-1] - times[-1]),
        prefill_frames=preload,
        inventory=inventory,
        transitions=transitions,
        ownership_transition_continuity=transition_continuity,
        held_unspun_relative=relative_errors,
        installed_drift=installed_drifts,
        simultaneous=synchronized,
        refill_path_comparison=distances,
        factory_maximum_error=maximum,
        scope=("Stored poses, timing and finite UID consistency; no formal physical validity or force/torque verdict."),
    )
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("C_V05_SAVED_IDENTITY", len(checks), [key for key, value in checks.items() if not value], flush=True)


if __name__ == "__main__":
    main()
