# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build continuous nearby-feeder C tracks with synchronous fastening [m, rad, s]."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_c_front_roll_v05 import HALF_TURN, FrontContext
from op030_c_refill_v05 import refill_phases
from op030_c_replay_v05 import aligned_pairs
from op030_definition import ROOT, pose
from op030_fk_fast import LIMITS, chain_for
from op030_split_c_v04 import digest
from op030_split_c_v05 import combined_row, drive_phases, source_tracks
from solve_op030_motion import R

BANK = ROOT / "data/op030_split_c_front_indexed_motion_v05.npz"
AUDIT = ROOT / "audit/op030_c_front_indexed_replay_v05.json"
MESH = ROOT / "data/op030_split_c_front_feeders_v05_meshes.npz"


def timed_polyline(path: np.ndarray) -> tuple[np.ndarray, dict]:
    """Interpolate a dense screened joint path with stopped quintic progress [rad, s]."""
    grid = np.linspace(0, 1, len(path))
    duration = max(1.0, float(np.max(np.sum(abs(np.diff(path, axis=0)), axis=0))) * 1.875 / 0.9)
    history = []
    for attempt in range(3):
        count = int(np.ceil(duration * 30))
        u = np.linspace(0, 1, count + 1)
        w = u**3 * (10 - 15 * u + 6 * u * u)
        values = np.asarray([np.interp(w, grid, path[:, j]) for j in range(6)]).T
        velocity = np.gradient(values, 1 / 30, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, 1 / 30, axis=0, edge_order=2)
        pv, pa = float(abs(velocity).max()), float(abs(acceleration).max())
        history.append(dict(attempt=attempt, duration_s=count / 30, peak_v=pv, peak_a=pa))
        if pv <= 1.15 and pa <= 1.9:
            return values, dict(history=history, interpolation="dense joint polyline, quintic progress")
        duration = count / 30 * max(pv / 1.1, np.sqrt(pa / 1.8), 1.05)
    raise ValueError(f"Finite path timing failed: {history}")


def prepare() -> None:
    """Save a finite-UID C bank and actual-frame construction evidence [s]."""
    if BANK.exists() or AUDIT.exists():
        raise FileExistsError(BANK)
    data, _, tracks = source_tracks()
    context = FrontContext(data["object_names"])
    routes_paths = [ROOT / "audit/op030_c_front_roll_v05.json"]
    inputs = [
        Path(__file__),
        ROOT / "scripts/op030_c_front_roll_v05.py",
        MESH,
        MESH.with_suffix(".json"),
        *routes_paths,
    ]
    hashes = {str(p): digest(p) for p in inputs}
    report = json.loads(routes_paths[0].read_text())
    routes = {record["number"]: record["returns"] for record in report["records"]}
    if not all(r["passed"] for rs in routes.values() for r in rs):
        raise ValueError("Unscreened source path")
    receipt = np.asarray(routes[2][-1]["joints"][-1])
    np.testing.assert_allclose(receipt, np.asarray(routes[1][-1]["joints"][-1]), atol=1e-6, rtol=0)
    root = data["poses"][0, 0]
    chains = [chain_for(tuple((root @ R.yoke_base_pose(s)).ravel())) for s in ("left", "right")]
    delta = [pose(location=(0.45, 0.20, 0)), pose(location=(0.45, -0.20, 0))]
    rows, events, failures, seams, timing = [], [], [], [], []
    q_current = receipt.copy()

    def control(pair):
        row = combined_row(data, tracks, *pair)
        row["control_local_indices"] = np.asarray(pair)
        row["motion_local_indices"] = np.asarray([-1, -1])
        return row

    def make_row(pair, q, label, free=(False, False)):
        row = control(pair)
        hits, actual = context.query(row, q)
        row.update({key: actual[key] for key in ("poses", "tools", "object_poses")})
        row.update(joints=q.copy(), labels=label, free_joint_motion=np.asarray(free))
        row["spindle_angles"] = context.source_row(control(pair))["spindle_angles"]
        row["source_frame_indices"] = row["source_sample_indices"] = np.array([-1, -1])
        if hits:
            failures.append(dict(label=label, local=pair, pairs=hits))
            raise ValueError(f"Actual mesh failure: {label}: {hits[:3]}")
        return row

    def append(label, new_rows, kind):
        nonlocal q_current
        if rows:
            dq = float(abs(rows[-1]["joints"] - new_rows[0]["joints"]).max())
            seams.append(
                dict(
                    label=label,
                    joint_delta_rad=dq,
                    object_matrix_delta=float(abs(rows[-1]["object_poses"] - new_rows[0]["object_poses"]).max()),
                )
            )
            if dq > 1e-6:
                raise ValueError(f"Disconnected branch {label}: {dq}")
            new_rows = new_rows[1:]
        first = max(0, len(rows) - 1)
        rows.extend(new_rows)
        q_current = rows[-1]["joints"].copy()
        events.append(
            dict(
                label=label,
                kind=kind,
                start_frame=first,
                stop_frame=len(rows) - 1,
                start_s=first / 30,
                stop_s=(len(rows) - 1) / 30,
            )
        )
        print("C_FRONT_STAGE", label, len(rows), flush=True)

    def constrained(label, pairs, targets, kind):
        q = q_current.copy()
        result = []
        for index, pair in enumerate(pairs):
            desired = targets(index, pair)
            for arm in (0, 1):
                value, residual = chains[arm].solve_continuous(desired[arm], q[arm])
                if residual > 1e-5 or abs(value - q[arm]).max() > 0.3 or np.any(abs(value) >= LIMITS):
                    raise ValueError(f"Continuous IK {label} {index}/{arm}: {residual}")
                q[arm] = value
            result.append(make_row(pair, q, label))
        append(label, result, kind)

    def pickup(number, initial=False):
        if initial:
            phases = [t["phases"][:6] for t in tracks]
            above = [p[1]["stop_frame"] for p in phases]
            last = [p[-1]["stop_frame"] for p in phases]
        else:
            phases = refill_phases(tracks, number)
            above = [p[3]["stop_frame"] for p in phases]
            last = [p[-1]["stop_frame"] for p in phases]
        pairs = aligned_pairs(above, last)

        def targets(_, pair):
            row = combined_row(data, tracks, *pair)
            result = np.asarray([delta[a] @ row["tools"][a] for a in (0, 1)])
            # Retain the 140 mm extraction; the final lift ends at the 230 mm supply clearance.
            for arm in (0, 1):
                lift = phases[arm][-1]
                if pair[arm] >= lift["start_frame"]:
                    begin = combined_row(data, tracks, *[lift["start_frame"] if a == arm else pair[a] for a in (0, 1)])[
                        "tools"
                    ][arm]
                    result[arm, 2, 3] = begin[2, 3] + 0.5625 * (row["tools"][arm, 2, 3] - begin[2, 3])
            calibration = np.asarray(context.metadata["fixed_tools"]["OP030C_M6"]["flange_to_tcp"])
            result[0] = result[0] @ calibration @ HALF_TURN @ np.linalg.inv(calibration)
            return result

        constrained("両工具に次の締結部品を装填・230 mm上方で待機", pairs, targets, "paired_pickup")

    def route(number, reverse, held_pair=None):
        selected = routes[number][::-1] if reverse else routes[number]
        refill = refill_phases(tracks, number)
        gate_start = [p[0]["start_frame"] for p in refill]
        gate_stop = [p[2]["stop_frame"] for p in refill]
        clock = 0
        for item in selected:
            arm = item["arm"]
            path = np.asarray(item["joints"])[:: (-1 if reverse else 1), arm]
            if abs(path[0] - q_current[arm]).max() > 1e-6:
                raise ValueError("Route branch seam")
            values, measured = timed_polyline(path)
            timing.append(dict(number=number, reverse=reverse, arm=arm, **measured))
            label = f"H03-{number}／{'M6' if arm == 0 else 'M14'}を{'締結位置へ' if reverse else '近接フィーダへ'}直行"
            new = []
            for index, value in enumerate(values):
                pair = (
                    held_pair
                    if reverse
                    else [min(a + clock + index, b) for a, b in zip(gate_start, gate_stop, strict=True)]
                )
                q = q_current.copy()
                q[arm] = value
                new.append(make_row(pair, q, label, (arm == 0, arm == 1)))
            append(label, new, "direct_approach" if reverse else "direct_refill")
            clock += len(values) - 1

    try:
        confirm = [t["phases"][0]["stop_frame"] for t in tracks]
        pairs = aligned_pairs([0, 0], confirm)
        append(
            "受取座上方で両フィーダ先頭を確認",
            [make_row(p, receipt, "受取座上方で両フィーダ先頭を確認") for p in pairs],
            "initial_confirm",
        )
        pickup(2, initial=True)
        preload_count = len(rows)
        for number in (2, 1):
            drive = drive_phases(tracks, number)
            held = [p[2]["start_frame"] for p in drive]
            route(number, True, held)
            start_tools = np.asarray([chains[a].forward(q_current[a])[0] for a in (0, 1)])
            target_tools = combined_row(data, tracks, *held)["tools"]
            # Both loaded tools approach on the original stud axes from the screened clearance.
            count = 96

            def approach(index, _):
                u = index / count
                w = u**3 * (10 - 15 * u + 6 * u * u)
                tools = start_tools.copy()
                tools[:, :3, 3] = start_tools[:, :3, 3] * (1 - w) + target_tools[:, :3, 3] * w
                return tools

            constrained(
                f"H03-{number}／両工具をスタッド先端へ同時位置合わせ", [held] * (count + 1), approach, "paired_align"
            )
            pairs = aligned_pairs([p[2]["start_frame"] for p in drive], [p[2]["stop_frame"] for p in drive])
            constrained(
                f"H03-{number}／大小を同時に締付",
                pairs,
                lambda _, pair: combined_row(data, tracks, *pair)["tools"],
                "paired_spin",
            )
            pairs = aligned_pairs([p[3]["start_frame"] for p in drive], [p[3]["stop_frame"] for p in drive])
            constrained(
                f"H03-{number}／両工具を同時に80 mm軸抜き",
                pairs,
                lambda _, pair: combined_row(data, tracks, *pair)["tools"],
                "paired_withdraw80",
            )
            count = drive[0][4]["stop_frame"] - drive[0][4]["start_frame"]
            pairs = [[min(p[5]["start_frame"] + i, p[5]["stop_frame"]) for p in drive] for i in range(count + 1)]

            def rise(index, _):
                pair = [drive[0][4]["start_frame"] + index, drive[1][3]["stop_frame"]]
                return combined_row(data, tracks, *pair)["tools"]

            constrained(f"H03-{number}／M6追加160 mm上昇・空ソケット復帰", pairs, rise, "M6_raise_and_index")
            route(number, False)
            pickup(number)
        keys = (
            "joints",
            "poses",
            "tools",
            "spindle_angles",
            "free_joint_motion",
            "local_author_times",
            "source_frame_indices",
            "source_sample_indices",
            "source_author_times",
            "object_poses",
            "ledger_owner",
            "labels",
            "motion_local_indices",
            "control_local_indices",
        )
        arrays = {key: np.asarray([r[key] for r in rows]) for key in keys}
        count = len(rows)
        stamps = np.arange(count) / 30
        arrays.update(
            times=stamps,
            author_times=stamps.copy(),
            frames=np.arange(count) + 1,
            node_ids=data["node_ids"],
            grips=np.zeros((count, 2)),
            errors=np.zeros((count, 2, 2)),
            clips=np.zeros((count, 2, 2)),
            object_names=data["object_names"],
            ledger_uids=data["ledger_uids"],
            assembled_uids=data["assembled_uids"],
            end_loaded_uids=data["end_loaded_uids"],
            preload_frame_count=np.array(preload_count),
            preload_author_time_s=np.array((preload_count - 1) / 30),
        )
        velocity = np.gradient(arrays["joints"], 1 / 30, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, 1 / 30, axis=0, edge_order=2)
        pv, pa = float(abs(velocity).max()), float(abs(acceleration).max())
        if pv > 1.2 or pa > 2.0:
            raise ValueError(f"Whole-bank timing caps: {pv}, {pa}")
        if hashes != {str(p): digest(p) for p in inputs}:
            raise ValueError("Inputs changed")
        np.savez_compressed(BANK, **arrays)
        report = dict(
            passed=True,
            output=str(BANK),
            output_sha256=digest(BANK),
            frames=count,
            duration_s=stamps[-1],
            preload_frame_count=preload_count,
            peak_velocity_rad_s=pv,
            peak_acceleration_rad_s2=pa,
        )
        print("C_FRONT_BANK_COMPLETE", count, stamps[-1], flush=True)
    except Exception as error:
        report = dict(passed=False, error=str(error), completed_frames=len(rows))
        raise
    finally:
        report.update(
            observed_at=datetime.now().astimezone().isoformat(),
            source_inputs_sha256=hashes,
            events=events,
            seams=seams,
            timing=timing,
            failures=failures,
            formal_physical_verdict=False,
            additional_contact_exceptions=[],
        )
        AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda x: x.tolist()) + "\n")


if __name__ == "__main__":
    prepare()
