# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Connect two changed A windows and retain all other saved v04 frames [m, rad, s]."""

import argparse
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import LIMITS
from op030_free_paths import plan_free_path
from op030_motion import SIDES
from op030_split_tools import driver_flange_to_tcp
from op030_support_motion_v04 import support_sequence_v04
from op030_support_plan_v04 import digest
from op030_support_plan_v05 import BANK, MESH, PlanningContext, bank_seed, solve_pair
from replay_op030_motion import path_sample, path_timing
from scipy.spatial.transform import Rotation
from solve_op030_motion import NODE_IDS
from split_tools_audit_a_bank_mesh_v04 import OutsideSupportCheck

PLAN = ROOT / "audit/op030_support_connected_v05.json"
PLAN_ARRAYS = ROOT / "analysis/op030_support_connected_v05.npz"


def write_json(path: Path, data: dict) -> None:
    """Write one new review record without replacing previous observations."""
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def plan_windows(mesh_file: Path) -> None:
    """Reuse accepted ascent and connect one stationary-other-arm transit at a time [rad, s]."""
    if PLAN.exists() or PLAN_ARRAYS.exists():
        raise FileExistsError(PLAN)
    local_report = ROOT / "audit/op030_support_ascent_v05.json"
    local = json.loads(local_report.read_text())
    assert local["passed"] and digest(Path(local["candidate_arrays"])) == local["candidate_arrays_sha256"]
    assert local["source_inputs_sha256"][str(mesh_file)] == digest(mesh_file)
    assert local["source_inputs_sha256"][str(ROOT / "scripts/op030_support_motion_v05.py")] == digest(
        ROOT / "scripts/op030_support_motion_v05.py"
    )
    with np.load(BANK) as saved:
        bank = {key: saved[key].copy() for key in ("author_times", "joints")}
    with np.load(local["candidate_arrays"]) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    old_connect = json.loads((ROOT / "audit/op030_support_connected_v04.json").read_text())
    old_seq = support_sequence_v04()
    context = PlanningContext(mesh_file)
    records, all_failures = [], []
    for window in context.sequence.simultaneous_retreats:
        number = window["number"]
        stamps = list(arrays[f"window_{number}_times"])
        values = list(arrays[f"window_{number}_joints"])
        q = values[-1].copy()
        tail_times = np.linspace(window["lift_stop_s"], window["tool_clear_s"], 91)
        failures = []
        for stamp in tail_times[1:]:
            solved, error = solve_pair(context, float(stamp), q)
            score, pairs = context.query(float(stamp), solved)
            if error.max() > 1e-5 or np.any(abs(solved) > LIMITS) or score:
                failures.append(dict(time_s=float(stamp), errors=error.tolist(), pairs=pairs))
                break
            stamps.append(float(stamp))
            values.append(solved.copy())
            q = solved
        arrays[f"window_{number}_times"] = np.asarray(stamps)
        arrays[f"window_{number}_joints"] = np.asarray(values)
        routes = []
        final_q = bank_seed(bank, window["old_stop_s"])
        phases = [
            p
            for p in context.sequence.phases
            if p.get("v05_window") == number and p["start"] >= window["tool_clear_s"] - 1e-8
        ]
        for arm, phase in enumerate(phases):
            if failures:
                break
            before = context.sequence.evaluate(phase["start"] + 1e-6)
            after = context.sequence.evaluate(phase["stop"] - 1e-6)
            if not np.allclose(before["root"], after["root"], atol=1e-7):
                raise ValueError("Free connection requires a stationary torso")
            if not np.allclose(before["tools"][1 - arm], after["tools"][1 - arm], atol=1e-7):
                raise ValueError("Free connection requires a stationary other arm")
            initial, endpoint, other = q[arm].copy(), final_q[arm].copy(), q[1 - arm].copy()
            midpoint = (phase["start"] + phase["stop"]) / 2

            @lru_cache(maxsize=20000)
            def cached_score(key):
                both = np.zeros((2, 6))
                both[arm], both[1 - arm] = np.asarray(key), other
                return context.query(midpoint, both, override_free=True)[0]

            def score(value):
                return cached_score(tuple(np.asarray(value)))

            route, reused = None, False
            if arm == 0:
                old_start = old_seq.support_hold_intervals[number - 1]["fasteners"][-1]["tool_clear_s"]
                row = next(p for p in old_connect["free_paths"] if p["arm"] == 0 and abs(p["start"] - old_start) < 1e-8)
                candidate = np.asarray(row["path"])
                assert abs(candidate[0] - initial).max() < 1e-5
                assert abs(candidate[-1] - endpoint).max() < 1e-5
                candidate[0], candidate[-1] = initial, endpoint
                clear = True
                for first, last in zip(candidate[:-1], candidate[1:], strict=True):
                    count = max(2, int(np.ceil(np.linalg.norm(last - first) / 0.0025)) + 1)
                    if any(score(value) for value in np.linspace(first, last, count)):
                        clear = False
                        break
                if clear:
                    route, reused = candidate, True
            if route is None:
                route = plan_free_path(initial, endpoint, score)
            if route is None:
                failures.append(
                    dict(phase=phase["label"], planner=plan_free_path.last_debug, pairs=context.screen.last_pairs)
                )
                break
            routes.append(
                dict(
                    arm=arm,
                    start=phase["start"],
                    stop=phase["stop"],
                    path=route.tolist(),
                    reused_v04_left_path=reused,
                    stationary_other_joints=other.tolist(),
                    checked_distinct_joint_states=cached_score.cache_info().misses,
                )
            )
            q[arm] = endpoint
            print("A_V05_FREE", number, arm, len(route), reused, flush=True)
        all_failures.extend(failures)
        records.append(
            dict(
                window=window,
                routes=routes,
                failures=failures,
                final_joint_delta_from_v04=float(abs(q - final_q).max()),
            )
        )
    np.savez_compressed(PLAN_ARRAYS, **arrays)
    record = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        passed=not all_failures,
        windows=records,
        failures=all_failures,
        mesh_file=str(mesh_file),
        mesh_sha256=digest(mesh_file),
        local_ascent_report=str(local_report),
        local_ascent_report_sha256=digest(local_report),
        bank=str(BANK),
        bank_sha256=digest(BANK),
        arrays=str(PLAN_ARRAYS),
        arrays_sha256=digest(PLAN_ARRAYS),
        motion_source_sha256=digest(ROOT / "scripts/op030_support_motion_v05.py"),
        stationary_other_assertions_retained=True,
        additional_contact_exceptions=[],
    )
    write_json(PLAN, record)
    if all_failures:
        raise SystemExit(1)


class LocalReplay:
    """Sample only the changed windows, keeping exact reused q outside them [m, rad, s]."""

    def __init__(self, context: PlanningContext):
        self.context = context
        self.record = json.loads(PLAN.read_text())
        assert self.record["passed"] and self.record["mesh_sha256"] == digest(Path(self.record["mesh_file"]))
        assert self.record["motion_source_sha256"] == digest(ROOT / "scripts/op030_support_motion_v05.py")
        assert self.record["arrays_sha256"] == digest(PLAN_ARRAYS)
        with np.load(PLAN_ARRAYS) as saved:
            self.arrays = {key: saved[key].copy() for key in saved.files}

    def sample(self, number: int, time: float) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate exact constrained tool frames or the screened stationary-other path [rad, s]."""
        record = self.record["windows"][number - 1]
        group = next((p for p in record["routes"] if p["start"] - 1e-9 <= time <= p["stop"] + 1e-9), None)
        if group:
            route = np.asarray(group["path"])
            knots = path_timing(route, 1.2, 2.0)
            q = np.zeros((2, 6))
            q[group["arm"]] = path_sample(route, knots, (time - group["start"]) / (group["stop"] - group["start"]))
            q[1 - group["arm"]] = group["stationary_other_joints"]
            free = np.zeros(2, dtype=bool)
            free[group["arm"]] = True
            return q, free
        stamps, values = self.arrays[f"window_{number}_times"], self.arrays[f"window_{number}_joints"]
        seed = np.asarray([[np.interp(time, stamps, values[:, arm, j]) for j in range(6)] for arm in (0, 1)])
        q, error = solve_pair(self.context, time, seed)
        if error.max() > 1e-5 or np.any(abs(q) > LIMITS):
            raise RuntimeError(f"Changed-window constrained IK failed at {time}")
        return q, np.zeros(2, dtype=bool)

    def timeline(self, window: dict) -> tuple[np.ndarray, dict]:
        """Reuse derivative-based phase timing and round each changed phase to 30 Hz [s]."""
        phases = [p for p in self.context.sequence.phases if p.get("v05_window") == window["number"]]
        boundaries = np.asarray([p["start"] for p in phases] + [phases[-1]["stop"]])
        stamps = np.unique(np.round(np.r_[np.arange(boundaries[0], boundaries[-1], 1 / 60), boundaries], 9))
        joints = np.asarray([self.sample(window["number"], float(t))[0] for t in stamps])
        velocity = np.gradient(joints, stamps, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, stamps, axis=0, edge_order=2)
        scales = []
        for phase in phases:
            use = (stamps >= phase["start"] - 1e-8) & (stamps <= phase["stop"] + 1e-8)
            scales.append(
                max(1.0, 1.25 * abs(velocity[use]).max() / 1.2, np.sqrt(1.25 * abs(acceleration[use]).max() / 2.0))
            )
        for route in self.record["windows"][window["number"] - 1]["routes"]:
            index = next(i for i, p in enumerate(phases) if abs(p["start"] - route["start"]) < 1e-8)
            scales[index] = max(
                scales[index], path_timing(np.asarray(route["path"]), 1.2, 2.0)[-1] / (route["stop"] - route["start"])
            )
        frame_durations = np.ceil(np.diff(boundaries) * np.asarray(scales) * 30).astype(int)
        frame_boundaries = np.r_[0, np.cumsum(frame_durations)]
        authored = np.interp(np.arange(frame_boundaries[-1] + 1), frame_boundaries, boundaries)
        return authored, dict(
            number=window["number"],
            phase_scales=np.asarray(scales).tolist(),
            frame_boundaries=frame_boundaries.tolist(),
            author_boundaries=boundaries.tolist(),
            frames=len(authored),
            duration_s=float(frame_boundaries[-1] / 30),
        )


def captured_row(
    context: PlanningContext,
    time: float,
    joints: np.ndarray,
    free: np.ndarray,
    names: list[str],
    ledger_uids: list[str],
) -> tuple[dict, list]:
    """Capture both actual FK arms, spindle and the same physical objects [m, rad, s]."""
    target = context.sequence.evaluate(time)
    _, pairs = context.query(time, joints, override_free=True)
    captures, actual, errors = {577: target["root"], 578: target["root"]}, [], []
    objects = {name: frame.copy() for name, frame in target["objects"].items()}
    for arm, side in enumerate(SIDES):
        robot, capture = context.robots[side]
        matrix = robot.update(joints[arm], float(target["grips"][arm]))
        captures.update(capture.poses)
        actual.append(matrix.copy())
        goal = target["tools"][arm]
        error = [
            float(np.linalg.norm(matrix[:3, 3] - goal[:3, 3])),
            float(np.linalg.norm(Rotation.from_matrix(matrix[:3, :3] @ goal[:3, :3].T).as_rotvec())),
        ]
        errors.append([0.0, 0.0] if free[arm] else error)
        if arm in context.sequence.driver_sizes:
            calibration = driver_flange_to_tcp(context.sequence.driver_sizes[arm])
            objects[context.sequence.driver_names[arm]] = matrix @ calibration
    owners = target["ledger"]["owners"]
    codes = [
        0 if owners[uid]["owner"] == "supply" else 3 if owners[uid]["owner"] == "installed" else owners[uid]["arm"] + 1
        for uid in ledger_uids
    ]
    return dict(
        joints=joints,
        tools=actual,
        grips=target["grips"],
        errors=errors,
        free_joint_motion=free,
        spindle_angles=target["spindle_angles"],
        poses=[captures[int(node)].copy() for node in NODE_IDS],
        object_poses=[objects[name] for name in names],
        labels=target["label"],
        ledger_owner=codes,
    ), pairs


def build_bank(mesh_file: Path) -> None:
    """Splice changed windows into a new bank and verify all changed native frames [m, rad, s]."""
    output = ROOT / "data/op030_split_a_motion_v05.npz"
    report_path = ROOT / "audit/op030_split_a_motion_v05.json"
    if output.exists() or report_path.exists():
        raise FileExistsError(output)
    with np.load(BANK) as saved:
        old = {key: saved[key].copy() for key in saved.files}
    context, inputs = PlanningContext(mesh_file), [BANK, mesh_file, mesh_file.with_suffix(".json"), PLAN, PLAN_ARRAYS]
    inputs += [
        ROOT / "scripts" / name
        for name in (
            "op030_support_motion_v05.py",
            "op030_support_replay_v05.py",
            "op030_support_plan_v05.py",
            "op030_support_motion_v04.py",
            "op030_split_ac_meshes.py",
        )
    ]
    hashes = {str(path): digest(path) for path in inputs}
    replay = LocalReplay(context)
    frame_fields = (
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
    )
    names, uids = old["object_names"].tolist(), old["ledger_uids"].tolist()
    rows, authors, reuse, timing, failures, seams = [], [], [], [], [], []
    outside_path = ROOT / "data/op030_duct_support_v04_world_02.npz"
    outside = OutsideSupportCheck(outside_path, context.screen, old["object_names"])
    background_path = ROOT / "data/op030_downstream_restored_v04_world.npz"
    # The restoration export may be named in its pinned diagnostic record.
    if not background_path.exists():
        background_report = json.loads((ROOT / "audit/op030_downstream_restored_v04_motion_delta.json").read_text())
        possible = [Path(v) for v in background_report.values() if isinstance(v, str) and v.endswith(".npz")]
        background_path = next(
            (p if p.is_absolute() else ROOT / p for p in possible if (p if p.is_absolute() else ROOT / p).exists()),
            None,
        )
    background = OutsideSupportCheck(background_path, context.screen, old["object_names"]) if background_path else None
    for segment in context.sequence.v04_segments:
        if segment["kind"] == "reused":
            use = old["author_times"] >= segment["old_start"] - 1e-8
            use &= old["author_times"] < segment["old_stop"] - 1e-8
            if abs(segment["old_stop"] - old["author_times"][-1]) < 1e-8:
                use |= np.arange(len(use)) == len(use) - 1
            for index in np.flatnonzero(use):
                rows.append({key: old[key][index] for key in frame_fields})
                authors.append(float(old["author_times"][index] - segment["old_start"] + segment["start"]))
                reuse.append(int(index))
            continue
        window = context.sequence.simultaneous_retreats[segment["number"] - 1]
        stamps, local_timing = replay.timeline(window)
        local_timing["start_frame_index"] = len(rows)
        for stamp in stamps:
            q, free = replay.sample(window["number"], float(stamp))
            row, hits = captured_row(context, float(stamp), q, free, names, uids)
            extra = outside.query(context.screen)
            if background:
                extra += background.query(context.screen)
            if hits or extra or np.max(row["errors"]) > 1e-5:
                failures.append(
                    dict(
                        frame=len(rows) + 1,
                        author_time_s=float(stamp),
                        pairs=hits + extra,
                        errors=np.asarray(row["errors"]).tolist(),
                    )
                )
            rows.append(row)
            authors.append(float(stamp))
            reuse.append(-1)
        local_timing["stop_frame_index"] = len(rows) - 1
        timing.append(local_timing)
        print("A_V05_WINDOW_NATIVE", window["number"], len(stamps), len(failures), flush=True)
    arrays = {key: np.asarray([row[key] for row in rows]) for key in frame_fields}
    arrays["ledger_owner"] = arrays["ledger_owner"].astype(np.uint8)
    times, authors, reuse = np.arange(len(rows)) / 30, np.asarray(authors), np.asarray(reuse)
    velocity = np.gradient(arrays["joints"], times, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
    for index in np.flatnonzero(np.diff(reuse >= 0)):
        seams.append(
            dict(
                frame_before=int(index + 1),
                frame_after=int(index + 2),
                joint_step_rad=float(abs(arrays["joints"][index + 1] - arrays["joints"][index]).max()),
            )
        )
    reused = reuse >= 0
    identity = {key: bool(np.array_equal(arrays[key][reused], old[key][reuse[reused]])) for key in frame_fields}
    work_index = int(np.searchsorted(authors, context.sequence.work_complete_author_time_s))
    unchanged = hashes == {str(path): digest(path) for path in inputs}
    peak_velocity, peak_acceleration = float(abs(velocity).max()), float(abs(acceleration).max())
    assert unchanged and all(identity.values())
    assert not failures, failures[:3]
    assert peak_velocity <= 1.2 and peak_acceleration <= 2.0, (peak_velocity, peak_acceleration)
    np.savez_compressed(
        output,
        times=times,
        author_times=authors,
        frames=np.arange(len(rows)) + 1,
        node_ids=old["node_ids"],
        object_names=old["object_names"],
        ledger_uids=old["ledger_uids"],
        assembled_uids=context.sequence.assembled_uids,
        end_loaded_uids=context.sequence.end_loaded_uids,
        work_complete_frame_count=work_index + 1,
        work_complete_author_time_s=context.sequence.work_complete_author_time_s,
        reused_v04_frame_indices=reuse,
        **arrays,
    )
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        candidate=str(output),
        candidate_sha256=digest(output),
        factory="op030_support_motion_v05:support_sequence_v05",
        frames=len(rows),
        duration_s=float(times[-1]),
        work_complete_time_s=float(times[work_index]),
        authored_duration_s=context.sequence.time,
        source_inputs_sha256=hashes,
        inputs_unchanged=unchanged,
        source_bank=str(BANK),
        source_bank_sha256=digest(BANK),
        reused_frames=int(reused.sum()),
        newly_checked_frames=int((~reused).sum()),
        exact_reused_array_identity=identity,
        seams=seams,
        changed_window_timing=timing,
        simultaneous_retreats=context.sequence.simultaneous_retreats,
        phases=[dict(start=p["start"], stop=p["stop"], label=p["label"]) for p in context.sequence.phases],
        maximum_fk_errors=np.max(arrays["errors"], axis=(0, 1)).tolist(),
        peak_velocity_rad_s=peak_velocity,
        peak_acceleration_rad_s2=peak_acceleration,
        failures=failures,
        additional_contact_exceptions=[],
        outside_support_aabb_separation_m=outside.minimum_aabb_separation_m,
        background_aabb_separation_m=background.minimum_aabb_separation_m if background else None,
        original_bank_modified=False,
        geometry_modified=False,
        scope="Changed windows FK/mesh checks plus exact v04 frame reuse; no formal physical verdict",
    )
    write_json(report_path, report)
    print("A_V05_BANK_COMPLETE", len(rows), times[-1], peak_velocity, peak_acceleration, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("plan", "bank"), required=True)
    parser.add_argument("--mesh_file", type=Path, default=MESH)
    args = parser.parse_args()
    (plan_windows if args.stage == "plan" else build_bank)(args.mesh_file)


if __name__ == "__main__":
    main()
