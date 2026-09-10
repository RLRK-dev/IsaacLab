# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Fixed-driver target schedules with finite fastener identities [m, rad, s].

Coordinates are baseline OP030 cell coordinates. The integrating builder
applies each cell's translation once to robot, product and all target actors.
Saved v02 M6 socket approach paths are reused; the new fixed mounts require
new complete robot/fixture checks before any physical interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
from op030_definition import CY, LIFT, ROOT, TERMINAL_X, TERMINAL_Y, lug_frame, pose, product_frame
from op030_motion import Sequence, angle_tool_paths, evaluate_phase, offset
from op030_split_tools import SIZES, driver_flange_to_tcp, fastener_socket_offset, feeder_queue_poses
from scipy.spatial.transform import Rotation

FEEDER_POSITIONS = {
    "A": {"M4": (-0.73, -2.65, 0.82)},
    "C": {"M6": (-1.00, -2.65, 0.84), "M14": (-1.00, -0.75, 0.84)},
}


def configure_feeders(seq: Sequence, cell: str, counts: dict[str, int] | None = None) -> dict:
    """Register finite feeder queues before the first captured phase [m].

    Args:
        seq: Existing Sequence or subclass using logical driver TCP objects.
        cell: A/OP030A or C/OP030C; all poses remain baseline coordinates.
        counts: Optional initial finite count per nominal thread size.
    """
    cell = cell.removeprefix("OP030")
    if cell not in FEEDER_POSITIONS:
        raise ValueError(cell)
    if seq.phases:
        raise ValueError("Configure feeder identities before capturing phases")
    seq.feeder_specs = {}
    for size, xyz in FEEDER_POSITIONS[cell].items():
        name = f"OP030{cell}_feeder_{size}"
        count = (counts or {}).get(size, 12)
        world = pose(location=xyz)
        uids = [name + f"_UID{index + 1:03d}" for index in range(count)]
        for uid, local in zip(uids, feeder_queue_poses(size, count, advance=1), strict=True):
            seq.objects[uid] = world @ local
        seq.objects[name + "_escapement"] = world.copy()
        seq.feeder_specs[size] = {
            "name": name,
            "world": world,
            "count": count,
            "consumed": 0,
            "kind": "bolt" if size == "M4" else "nut",
            "uids": uids,
        }
    return seq.feeder_specs


def _phase(seq, label, seconds, arm, target=None, *, objects=None, spin=None, free=False):
    changes = dict(objects or {})
    if target is not None:
        changes[seq.driver_names[arm]] = target
    seq.phase(label, seconds, objects=changes, spin=spin)
    seq.phases[-1]["free"] = [free if index == arm else False for index in range(2)]
    seq.phases[-1]["fixed_driver_arm"] = arm


def append_fastening(
    seq: Sequence,
    arm: int,
    size: str,
    seat: np.ndarray,
    uid: str | None = None,
    *,
    label: str | None = None,
    wire_number: int | None = None,
) -> str:
    """Append automatic feed, pickup, thread advance, seating and retreat [m].

    Args:
        seq: Sequence configured with driver_names, driver_sizes and feeders.
        arm: Fixed-driver arm index, 0 left or 1 right.
        size: Nominal M4, M6 or M14.
        seat: Final fastener washer-seat world transform [m].
        uid: Next finite feeder UID; inferred from queue if omitted.
        label: Human-readable operation label.
        wire_number: H03 number required for reuse of the M6 route.

    Returns:
        The same fastener UID used from the queue through final assembly.
    """
    if seq.driver_sizes.get(arm) != size:
        raise ValueError("This arm is not permanently fitted with the requested driver")
    spec = seq.feeder_specs[size]
    used = spec["consumed"]
    if used >= spec["count"]:
        raise ValueError("Finite fastener supply exhausted")
    expected = spec["uids"][used]
    if uid is None:
        uid = expected
    if uid != expected:
        raise ValueError("Fastener must be the next single-file queue identity")
    label = label or f"{size} {'ボルト' if spec['kind'] == 'bolt' else 'ナット'}締結"
    driver = seq.driver_names[arm]
    angle_driver = size == "M6" and size not in getattr(seq, "straight_driver_sizes", set())
    mouth = fastener_socket_offset(size, spec["kind"])
    world = spec["world"]
    gate_name = spec["name"] + "_escapement"
    if used:
        _phase(seq, label + "／切出しゲートを開く", 0.5, arm, objects={gate_name: world @ pose(location=(0, 0.045, 0))})
        next_poses = {
            name: world @ frame
            for name, frame in zip(spec["uids"], feeder_queue_poses(size, spec["count"], used, 1), strict=True)
            if frame is not None
        }
        _phase(seq, label + "／単列供給を1個分送る", 1.0, arm, objects=next_poses)
        _phase(seq, label + "／次部品を切出して停止", 0.5, arm, objects={gate_name: world})
    else:
        _phase(seq, label + "／供給ユニットの先頭部品を確認", 0.6, arm)
    pickup = world @ pose(location=(0, 0, mouth))
    before = pickup @ pose(location=(0, 0, 0.080))
    _phase(seq, label + "／固定工具を供給上方へ", 4.0, arm, offset(before, (0, 0, 0.15)), free=True)
    _phase(seq, label + "／取得座と同軸に合わせる", 2.0, arm, before)
    _phase(seq, label + "／ソケットで先頭部品を保持", 2.0, arm, pickup)
    seq.driven_nuts[uid] = (driver, pose(location=(0, 0, -mouth)))
    _phase(seq, label + "／同じ部品を取得座から引き上げる", 2.0, arm, offset(pickup, (0, 0, 0.14)))
    spec["consumed"] += 1
    _phase(seq, label + "／工具を搬送高さへ", 2.0, arm, offset(seq.objects[driver], (0, 0, 0.16)))
    if angle_driver:
        if wire_number not in (1, 2):
            raise ValueError("M6 requires the retained H03 route number")
        alignment = pose(Rotation.from_euler("z", -30, degrees=True).as_matrix())
        travel = 0.011
        approach = seat @ alignment @ pose(location=(0, 0, mouth + travel))
        original = getattr(seq, "angle_routes", None)
        original = (angle_tool_paths() if original is None else original)[wire_number]
        # Original mouth clearance was washer+0.5 mm; the new retained tip
        # uses washer+0.3 mm. Apply only that rigid endpoint correction.
        path = np.asarray([approach @ np.linalg.inv(original[-1]) @ frame for frame in original])
        _phase(seq, label + "／配線上方で固定アングル工具を合わせる", 4.0, arm, path[0], free=True)
        for index, frame in enumerate(path[1:], 1):
            previous = seq.objects[driver]
            distance = np.linalg.norm(frame[:3, 3] - previous[:3, 3])
            angle = np.linalg.norm(Rotation.from_matrix(frame[:3, :3] @ previous[:3, :3].T).as_rotvec())
            _phase(
                seq,
                label + f"／端子進入路{index}",
                max(getattr(seq, "route_min_seconds", 0.8), (distance + 0.15 * angle) / 0.06),
                arm,
                frame,
            )
    else:
        alignment = pose(Rotation.from_euler("z", 180 if size == "M4" else 0, degrees=True).as_matrix())
        travel = {"M4": 0.0092, "M6": 0.011, "M14": 0.022}[size]
        approach = seat @ alignment @ pose(location=(0, 0, mouth + travel))
        _phase(seq, label + "／固定工具を締結部上方へ", 4.0, arm, offset(approach, (0, 0, 0.17)), free=True)
        if size == "M4":
            through_ear = seat @ alignment @ pose(location=(0, 0, mouth + 0.0152))
            _phase(seq, label + "／ボルト先端を取付耳の穴へ", 2.0, arm, through_ear)
            _phase(seq, label + "／耳の貫通穴を通してインサートへ", 1.5, arm, approach)
        else:
            _phase(seq, label + "／スタッド先端と同軸にする", 2.2, arm, approach)
    radians = -travel / SIZES[size]["pitch"] * 2 * np.pi
    seated_tcp = seat @ alignment @ pose(location=(0, 0, mouth))
    _phase(
        seq, label + "／低速ねじ進行・着座", 6.0, arm, seated_tcp, spin={"tool": driver, "nut": uid, "radians": radians}
    )
    # Preserve even the exact final hex orientation when releasing vacuum;
    # never snap the persistent fastener back to a canonical orientation.
    seq.objects[uid] = seat @ alignment @ pose(Rotation.from_euler("z", radians).as_matrix())
    del seq.driven_nuts[uid]
    _phase(
        seq,
        label + "／保持を解除して軸方向へ退避",
        1.8,
        arm,
        offset(seated_tcp, seat[:3, 2] * (0.011 if angle_driver else 0.080)),
    )
    if angle_driver:
        for index, frame in enumerate(path[-2::-1], 1):
            previous = seq.objects[driver]
            distance = np.linalg.norm(frame[:3, 3] - previous[:3, 3])
            angle = np.linalg.norm(Rotation.from_matrix(frame[:3, :3] @ previous[:3, :3].T).as_rotvec())
            _phase(
                seq,
                label + f"／端子退避路{index}",
                max(getattr(seq, "route_min_seconds", 0.8), (distance + 0.15 * angle) / 0.06),
                arm,
                frame,
            )
    _phase(seq, label + "／次工程のため上方退避", 2.0, arm, offset(seq.objects[driver], (0, 0, 0.16)))
    current_angle = _spindle_angles(seq, seq.time)[arm]
    reset = -float(np.arctan2(np.sin(current_angle), np.cos(current_angle)))
    _phase(seq, label + "／空ソケットを供給基準へ戻す", 1.0, arm)
    seq.phases[-1]["spindle_reset"] = {"arm": arm, "radians": reset}
    return uid


def _spindle_angles(seq: Sequence, t: float) -> np.ndarray:
    from op020_jb_motion import weight

    angles = np.zeros(2)
    for previous in seq.phases:
        if previous["start"] > t:
            break
        spin = previous["spin"]
        if spin:
            arm = next(arm for arm, driver in seq.driver_names.items() if driver == spin["tool"])
            angles[arm] += spin["radians"] * weight(t, previous["start"], previous["stop"])
        reset = previous.get("spindle_reset")
        if reset:
            angles[reset["arm"]] += reset["radians"] * weight(t, previous["start"], previous["stop"])
    return angles


def evaluate_fixed_phase(seq: Sequence, phase: dict, t: float) -> dict:
    """Evaluate mixed gripper/fixed-driver states with original FK tool0 [m]."""
    state = evaluate_phase(phase, t)
    for arm, size in seq.driver_sizes.items():
        calibration = getattr(seq, "driver_calibrations", {}).get(arm)
        if calibration is None:
            calibration = driver_flange_to_tcp(size)
        state["tools"][arm] = state["objects"][seq.driver_names[arm]] @ np.linalg.inv(calibration)
        state["grips"][arm] = 0.0
    state["free"] = np.asarray(phase.get("free", [False, False]), dtype=bool)
    angles = _spindle_angles(seq, t)
    state["spindle_angles"] = angles
    state["label"] = phase["label"]
    if "clips" in phase["before"]:
        from op020_jb_motion import weight

        w = weight(t, phase["start"], phase["stop"])
        state["clips"] = {
            number: (np.asarray(value) * (1 - w) + np.asarray(phase["after"]["clips"][number]) * w).tolist()
            for number, value in phase["before"]["clips"].items()
        }
        if hasattr(seq, "clip_calibration"):
            for number, values in state["clips"].items():
                state["objects"].update(_clip_frames(seq.clip_calibration, number, *values))
    return state


class FixedFasteningSequence(Sequence):
    """Standalone A/C driver target candidate in baseline cell coordinates."""

    def __init__(self, cell: str, initial_tools: np.ndarray | None = None):
        super().__init__()
        self.cell = cell.removeprefix("OP030")
        self.objects, self.holds, self.driven_nuts = {}, {}, {}
        self.driver_sizes = {0: "M4"} if self.cell == "A" else {0: "M6", 1: "M14"}
        self.driver_names = {arm: f"OP030{self.cell}_driver_{size}" for arm, size in self.driver_sizes.items()}
        for arm, size in self.driver_sizes.items():
            tcp = pose(location=(-0.55, CY + (-0.72 if arm == 0 else 0.72), 1.30))
            if initial_tools is not None:
                tcp = initial_tools[arm] @ driver_flange_to_tcp(size)
            self.objects[self.driver_names[arm]] = tcp
            self.holds[arm] = (self.driver_names[arm], np.linalg.inv(driver_flange_to_tcp(size)))
            self.hands[arm] = tcp @ np.linalg.inv(driver_flange_to_tcp(size))
        configure_feeders(self, self.cell)

    def snapshot(self):
        state = super().snapshot()
        if hasattr(self, "clips"):
            state["clips"] = deepcopy(self.clips)
        return state

    def evaluate(self, t: float) -> dict:
        """Evaluate the fixed-driver schedule at bounded time [s]."""
        if not self.phases or not 0 <= t <= self.time + 1e-9:
            raise ValueError("Time must lie inside the constructed schedule")
        phase = next((phase for phase in self.phases if t < phase["stop"]), self.phases[-1])
        return evaluate_fixed_phase(self, phase, min(t, self.time))


def _clip_frames(calibration: dict, number: int, hinge_closed: float, pads_closed: float) -> dict[str, np.ndarray]:
    row = next(row for row in calibration["metadata"]["clips"] if row["number"] == number)
    swing = row["swing"]
    local = calibration["local"][swing].copy()
    local[:3, :3] = local[:3, :3] @ Rotation.from_euler("y", -np.pi / 2 * (1 - hinge_closed)).as_matrix()
    world = calibration["world"][calibration["parents"][swing]] @ local
    result = {swing: world}
    for sign, pad in zip((-1, 1), row["pads"], strict=True):
        result[pad] = world @ calibration["local"][pad] @ pose(location=(sign * 0.011 * (1 - pads_closed), 0, 0))
    return result


def _clip_release(seq: FixedFasteningSequence, number: int) -> None:
    for label, seconds, values in (("パッドを開く", 0.8, [1.0, 0.0]), ("輸送クリップを90度開く", 3.0, [0.0, 0.0])):
        before = deepcopy(seq.clips)
        seq.clips[number] = values
        seq.phase(
            f"H03-{number}／静的支持へ移管・{label}",
            seconds,
            objects=_clip_frames(seq.clip_calibration, number, *values),
        )
        seq.phases[-1]["before"]["clips"] = before


def build_c_sequence_from_bank(path: Path, *, require_qualified: bool = True) -> FixedFasteningSequence:
    """Build explicit C actions from a digest-pinned route bank [m, rad, s].

    Args:
        path: Bank with exact route transforms, mesh export and SHA256.
        require_qualified: Require subsequent selected-branch mesh checks;
            false is only for producing the candidate used by those checks.
    """
    bank = json.loads(path.read_text())
    if require_qualified and bank.get("qualification") != "selected_branch_mesh_checked":
        raise ValueError("C route bank has not completed the selected-branch mesh checks")
    routes = bank["routes"]
    if len(routes) != 2 or any(not row.get("exact_solution") or row.get("failures") for row in routes):
        raise ValueError("C requires two exact routes with no recorded dense-query failures")
    mesh_file = Path(bank["mesh_file"])
    if hashlib.sha256(mesh_file.read_bytes()).hexdigest() != bank["mesh_sha256"]:
        raise ValueError("C route bank mesh export digest changed")
    metadata = json.loads(mesh_file.with_suffix(".json").read_text())["clip_metadata"]
    with np.load(mesh_file) as data:
        calibration = dict(
            metadata=metadata,
            world=dict(zip(data["actor_world_names"], data["actor_world"], strict=True)),
            local=dict(zip(data["actor_world_names"], data["actor_local"], strict=True)),
            parents=dict(zip(data["actor_world_names"], data["actor_parents"], strict=True)),
        )
    seq = FixedFasteningSequence("C")
    seq.angle_routes = {row["number"]: np.asarray(row["transforms"]) for row in routes}
    seq.route_min_seconds = float(bank.get("route_min_seconds", 0.02))
    seq.clip_calibration = calibration
    seq.clips = {1: [1.0, 1.0], 2: [1.0, 1.0]}
    for number in (1, 2):
        seq.objects.update(_clip_frames(calibration, number, 1.0, 1.0))
    seq.route_bank_path = str(path)
    seq.route_bank_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    seq.phase("OP030C／製品の位置決め・端子座面で静的支持", 1.0)
    _clip_release(seq, 2)
    if bank.get("h1_clip_open_before_fastening", False):
        _clip_release(seq, 1)
    work = product_frame(lift=LIFT)
    for number in (2, 1):
        for arm, size, end, washer_offset in ((0, "M6", "J1", 0.0038), (1, "M14", "T", 0.0032)):
            seat = work @ lug_frame(number, end) @ pose(location=(0, 0, washer_offset))
            append_fastening(seq, arm, size, seat, label=f"H03-{number}／{end}端子{size}", wire_number=number)
            park = pose(location=(-0.55, CY + (-0.72 if arm == 0 else 0.72), 1.30))
            _phase(seq, f"OP030C／{size}固定工具を待機位置へ", 4.0, arm, park, free=True)
    if seq.clips[1] != [0.0, 0.0]:
        _clip_release(seq, 1)
    seq.phase("OP030C／締結完了・両工具待機・輸送クリップ開放", 1.0)
    return seq


def integrated_c_sequence() -> FixedFasteningSequence:
    """Rebuild C only from the qualified explicit route bank [m, rad, s]."""
    path = ROOT / "data/op030_split_c_routes_v03.json"
    if not path.exists():
        raise FileNotFoundError("Qualified C bank is not published; do not replay the old socket routes")
    return build_c_sequence_from_bank(path)


def fixed_fastening_sequence(cell: str, initial_tools: np.ndarray | None = None) -> FixedFasteningSequence:
    """Build a finite A support-bolt or C cable-nut cycle [s]."""
    seq = FixedFasteningSequence(cell, initial_tools)
    seq.phase(f"OP030{seq.cell}／固定工具と供給装置の待機", 1.0)
    work = product_frame(lift=LIFT)
    if seq.cell == "A":
        for number, x in enumerate(TERMINAL_X, 1):
            for sign in (-1, 1):
                seat = work @ pose(location=(x, TERMINAL_Y + sign * 0.034, 0.013))
                append_fastening(seq, 0, "M4", seat, label=f"T{number:02d}／M4ボルト{sign:+d}")
    else:
        for number in (2, 1):
            for arm, size, end, washer_offset in ((0, "M6", "J1", 0.0038), (1, "M14", "T", 0.0032)):
                seat = work @ lug_frame(number, end) @ pose(location=(0, 0, washer_offset))
                append_fastening(seq, arm, size, seat, label=f"H03-{number}／{end}端子{size}", wire_number=number)
        for arm, size in seq.driver_sizes.items():
            park = pose(location=(-0.55, CY + (-0.72 if arm == 0 else 0.72), 1.30))
            _phase(seq, f"OP030C／{size}固定工具を搬出前の待機位置へ", 4.0, arm, park, free=True)
    seq.phase(f"OP030{seq.cell}／1組分の締結動作終了", 1.0)
    return seq


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", choices=("A", "C"), default="C")
    parser.add_argument("--report", default="split_tools_fastening_sequence.json")
    args = parser.parse_args()
    seq = fixed_fastening_sequence(args.cell)
    times = sorted({0.0, seq.time, *[float(phase[key]) for phase in seq.phases for key in ("start", "stop")]})
    errors = []
    for t in times:
        state = seq.evaluate(t)
        for arm, size in seq.driver_sizes.items():
            error = np.max(
                np.abs(state["tools"][arm] @ driver_flange_to_tcp(size) - state["objects"][seq.driver_names[arm]])
            )
            errors.append(float(error))
    report = {
        "cell": args.cell,
        "duration_s": seq.time,
        "phase_count": len(seq.phases),
        "maximum_fixed_tcp_roundtrip_error": max(errors),
        "driver_names": seq.driver_names,
        "used_uids": {size: spec["uids"][: spec["consumed"]] for size, spec in seq.feeder_specs.items()},
        "phases": [{key: phase[key] for key in ("start", "stop", "label")} for phase in seq.phases],
        "scope": "target sequence and finite actor identity; IK, complete mesh clearance and force unverified",
    }
    path = ROOT / "audit" / args.report
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("SPLIT_TOOLS_SEQUENCE_COMPLETE", path)


if __name__ == "__main__":
    main()
