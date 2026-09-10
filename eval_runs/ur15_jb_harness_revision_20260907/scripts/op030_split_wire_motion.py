# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""ST B spatial targets for straight supply and bimanual cable placement.

Coordinates [m], angles [rad], time [s]. This is a bounded kinematic candidate
using the existing UR15 FK and v11 finger calibration. FK reach diagnostics do
not establish collisions, grasp forces, material bend limits or physical
validity. A parent planner must screen and time the complete robot motion.
"""

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from op020_jb_motion import mix, weight
from op030_cable import coefficients, points_at
from op030_definition import CX, CY, LIFT, ROOT, lug_frame, pose, product_frame
from op030_fk_fast import LIMITS, chain_for
from op030_motion import SIDES, tool_for, turn_frame
from op030_split_top_entry import ConnectionMode
from op030_split_wire import WireBend, WireShape, supply_layout
from scipy.spatial.transform import Rotation
from solve_op030_motion import R, capture_robots, nearest_turn


@dataclass(frozen=True)
class WirePlacementConfig:
    """Provisional station coordinates [m], row spacing [m], and grip gap [m]."""

    stock_center: tuple[float, float, float] = (-1.68, CY, 1.04)
    stock_pitch: float = 0.065
    counts: tuple[int, int] = (5, 5)
    active_rows: tuple[int, int] = (5, 4)
    lift_clearance: float = 0.300
    above_work: float = 0.200
    insertion_x: float = 0.040
    terminal_raise: float = 0.040
    grasp_offset: float = 0.030
    grasp_gap: float = 0.014
    approach_gap: float = 0.024
    release_gap: float = 0.028
    h1_form_center_z: float | None = None
    h1_release_left_first: bool = False
    h1_release_gap: float | None = None
    connection_mode: ConnectionMode = "rear_entry"
    insertion_z: float = 0.020
    transport_clips: bool = True


def _translate(frame: np.ndarray, offset: tuple[float, float, float] | np.ndarray) -> np.ndarray:
    result = frame.copy()
    result[:3, 3] += offset
    return result


def _move_control(control: dict, transform: np.ndarray) -> dict:
    result = deepcopy(control)
    if control["mode"] == "bend":
        result["center"] = transform[:3, :3] @ control["center"] + transform[:3, 3]
        result["rotation"] = transform[:3, :3] @ control["rotation"]
    else:
        result["root"] = transform @ control["root"]
    return result


class WirePlacementSequence:
    """Persistent ten-wire supply and two-wire placement target schedule [s].

    Args:
        config: Candidate dimensions and grip positions [m].
    """

    def __init__(self, config: WirePlacementConfig | None = None):
        self.config = config or WirePlacementConfig()
        cfg = self.config
        self.bends = {
            number: WireBend(number, cfg.grasp_offset, connection_mode=cfg.connection_mode) for number in (1, 2)
        }
        self.work = product_frame(lift=LIFT)
        rows = supply_layout(cfg.counts, cfg.stock_pitch, cfg.stock_center, connection_mode=cfg.connection_mode)
        self.rows = rows
        selected = [rows[index] for index in cfg.active_rows]
        if [row["number"] for row in selected] != [2, 1]:
            raise ValueError("Active rows must select H03-2 followed by H03-1")
        self.active_uids = {row["number"]: row["uid"] for row in selected}
        self.calibration = {}
        for number, bend in self.bends.items():
            final = self._shape(number, {"mode": "insert", "root": self.work, "t_raise": 0.0})
            self.calibration[number] = {}
            for arm, end in ((0, "T"), (1, "J1")):
                desired = Rotation.from_euler("y", 180 if arm == 0 else 160, degrees=True).as_matrix()
                self.calibration[number][end] = final.grasp_frames[end][:3, :3].T @ desired
        work_hands = [
            pose(Rotation.from_euler("y", 140, degrees=True).as_matrix(), (-0.43, CY + y, 1.35)) for y in (-0.34, 0.34)
        ]
        stock_hands = [turn_frame(-np.pi) @ hand for hand in work_hands]
        controls = {}
        for row in rows:
            shape = row["shape"]
            controls[row["uid"]] = {
                "mode": "bend",
                "progress": 0.0,
                "center": (shape.centerline[0] + shape.centerline[-1]) / 2,
                "rotation": np.eye(3),
                "number": row["number"],
            }
        self.state = {
            "yaw": -np.pi / 2,
            "hands": stock_hands,
            "gaps": np.full(2, 0.080),
            "holds": {},
            "controls": controls,
            "supports": {row["uid"]: "supply_pallet" for row in rows},
            "clips": {1: np.zeros(2), 2: np.zeros(2)},
        }
        self.time = 0.0
        self.phases = []
        self.phase("OP030B／10本整列供給・両腕待機", 1.0)
        for number in (2, 1):
            uid = self.active_uids[number]
            if number == 1:
                self.phase("OP030B／次の直線ケーブル供給へ旋回", 5.0, turn=-np.pi)
            shape = self._shape(number, self.state["controls"][uid])
            contact = [self._hand(number, shape, end) for end in ("T", "J1")]
            above = [_translate(hand, (0.0, 0.0, 0.140)) for hand in contact]
            self.phase(
                f"H03-{number}／両指を両端の被覆上方へ",
                5.0,
                hands=above,
                gaps=[cfg.approach_gap] * 2,
                free=[True, True],
            )
            self.phase(f"H03-{number}／直線ケーブルの両端へ下降", 2.5, hands=contact)
            self.phase(f"H03-{number}／両指で被覆を把持", 1.0, gaps=[cfg.grasp_gap] * 2)
            self.state["holds"] = {0: (uid, "T"), 1: (uid, "J1")}
            self.state["supports"][uid] = "both_grippers"
            lifted = deepcopy(self.state["controls"][uid])
            lifted["center"] += (0.0, 0.0, cfg.lift_clearance)
            if number == 1 and cfg.h1_form_center_z is not None:
                lifted["center"][2] = cfg.h1_form_center_z
            self.phase(f"H03-{number}／両端保持で直線のまま持上げ", 3.0, controls={uid: lifted})
            self.phase(f"H03-{number}／両端保持で組付側へ旋回", 6.0, turn=np.pi)
            root_above = self.work @ pose(location=(cfg.insertion_x, 0.0, cfg.above_work))
            above_center = root_above[:3, :3] @ self.bends[number].final_center + root_above[:3, 3]
            if number == 1 and cfg.h1_form_center_z is not None:
                root_above[2, 3] += cfg.h1_form_center_z - above_center[2]
                above_center[2] = cfg.h1_form_center_z
            above_control = {
                "mode": "bend",
                "progress": 0.0,
                "center": above_center,
                "rotation": root_above[:3, :3],
                "number": number,
            }
            self.phase(f"H03-{number}／両端保持で筐体上方へ搬送", 5.0, controls={uid: above_control})
            bent = deepcopy(above_control)
            bent["progress"] = 1.0
            self.phase(f"H03-{number}／両指を動かして所定経路へ曲げる", 8.0, controls={uid: bent})
            # Change representation only at an exactly coincident endpoint.
            self.state["controls"][uid] = {"mode": "insert", "root": root_above, "t_raise": 0.0, "number": number}
            raised = deepcopy(self.state["controls"][uid])
            raised["t_raise"] = cfg.terminal_raise
            self.phase(f"H03-{number}／両端保持でT端子の進入高さを作る", 3.0, controls={uid: raised})
            low = deepcopy(raised)
            low_offset = (
                (0.0, 0.0, cfg.insertion_z) if cfg.connection_mode == "top_entry" else (cfg.insertion_x, 0.0, 0.0)
            )
            low["root"] = self.work @ pose(location=low_offset)
            self.phase(f"H03-{number}／J1ねじ先端の高さへ下ろす", 4.0, controls={uid: low})
            inserted = deepcopy(low)
            inserted["root"] = self.work.copy()
            insertion_label = (
                f"J1端子を上向きスタッドへ{cfg.insertion_z * 1000:g}mm下ろす"
                if cfg.connection_mode == "top_entry"
                else "J1端子を水平方向へ40mm差し込む"
            )
            self.phase(f"H03-{number}／{insertion_label}", 3.0, controls={uid: inserted})
            seated = deepcopy(inserted)
            seated["t_raise"] = 0.0
            self.phase(f"H03-{number}／T端子を40mm下ろして着座", 3.0, controls={uid: seated})
            self.state["supports"][uid] = "J1_stud_and_T_saddle_plus_both_grippers"
            self.phase(f"H03-{number}／両端の受けに支持を移す", 1.0)
            self.state["hands"] = [self._hand(number, self._shape(number, seated), end) for end in ("T", "J1")]
            first = 0 if number == 1 and cfg.h1_release_left_first else 1
            second = 1 - first
            labels = ("左", "右")
            names = ("left", "right")
            offsets = ((0.0, -0.160, 0.180), (0.0, 0.200, 0.150))
            del self.state["holds"][first]
            self.state["supports"][uid] = f"J1_stud_and_T_saddle_plus_{names[second]}_gripper"
            release_gaps = np.full(2, cfg.grasp_gap)
            release_gaps[first] = cfg.release_gap
            self.phase(f"H03-{number}／{labels[first]}指を開く", 1.0, gaps=release_gaps)
            retreat = self.state["hands"].copy()
            retreat[first] = _translate(retreat[first], offsets[first])
            self.phase(
                f"H03-{number}／{labels[first]}指を外側上方へ退避",
                3.0,
                hands=retreat,
                free=[first == arm for arm in (0, 1)],
            )
            if cfg.transport_clips:
                self.phase(
                    f"H03-{number}／{labels[second]}指保持中に仮保持クリップを旋回", 1.0, clips={number: (1.0, 0.0)}
                )
                self.phase(
                    f"H03-{number}／{labels[second]}指保持中に仮保持パッドを閉じる", 0.5, clips={number: (1.0, 1.0)}
                )
            del self.state["holds"][second]
            self.state["supports"][uid] = (
                "J1_stud_T_saddle_and_transport_clip" if cfg.transport_clips else "J1_stud_and_T_saddle"
            )
            final_release_gaps = [cfg.release_gap] * 2
            if number == 1 and cfg.h1_release_gap is not None:
                final_release_gaps[second] = cfg.h1_release_gap
            self.phase(f"H03-{number}／{labels[second]}指を開く", 1.0, gaps=final_release_gaps)
            retreat = self.state["hands"].copy()
            retreat[second] = _translate(retreat[second], offsets[second])
            self.phase(
                f"H03-{number}／{labels[second]}指を外側上方へ退避",
                3.0,
                hands=retreat,
                free=[second == arm for arm in (0, 1)],
            )
            self.phase(f"H03-{number}／両腕待機位置へ", 5.0, hands=work_hands, gaps=[0.080] * 2, free=[True, True])
        self.phase("OP030B／内部配線2本の設置完了・締結STへ引継ぎ", 2.0)

    def _shape(self, number: int, control: dict) -> WireShape:
        bend = self.bends[number]
        if control["mode"] == "bend":
            return bend.sample(float(control["progress"]), control["center"], control["rotation"])
        root = control["root"]
        end = root @ pose(location=(0.0, 0.0, control["t_raise"])) @ bend.final_frames["T"]
        values = _insertion_coefficients(number, float(control["t_raise"]), self.config.connection_mode)
        local = points_at(bend.final_points, np.asarray(values))
        points = local @ root[:3, :3].T + root[:3, 3]
        frames = {"J1": root @ bend.final_frames["J1"], "T": end}
        # Material points retain their original arclength parameter/index under
        # the legacy insertion basis. Its individual segments may redistribute
        # slightly, while total length and endpoint attachments are retained.
        reference = bend.sample(1.0)
        grips = {}
        for endpoint, distance in (("J1", bend.grasp_offset), ("T", bend.length - bend.grasp_offset)):
            index = min(np.searchsorted(bend.arc, distance, side="right") - 1, len(bend.lengths) - 1)
            alpha = (distance - bend.arc[index]) / bend.lengths[index]
            position = (1 - alpha) * points[index] + alpha * points[index + 1]
            tangent = points[index + 1] - points[index]
            tangent /= np.linalg.norm(tangent)
            z = root[:3, :3] @ reference.grasp_frames[endpoint][:3, 2]
            z -= np.dot(z, tangent) * tangent
            z /= np.linalg.norm(z)
            grips[endpoint] = pose(np.column_stack((tangent, np.cross(z, tangent), z)), position)
        return WireShape(points, frames, grips, 1.0)

    def _hand(self, number: int, shape: WireShape, end: str) -> np.ndarray:
        result = shape.grasp_frames[end].copy()
        result[:3, :3] = result[:3, :3] @ self.calibration[number][end]
        return result

    def phase(
        self, label: str, duration: float, *, hands=None, gaps=None, controls=None, turn=None, free=None, clips=None
    ) -> None:
        """Append one spatial target interval of ``duration`` [s]."""
        before = deepcopy(self.state)
        if hands is not None:
            self.state["hands"] = [hand.copy() for hand in hands]
        if gaps is not None:
            self.state["gaps"] = np.asarray(gaps, dtype=float)
        self.state["controls"].update(deepcopy(controls or {}))
        self.state["clips"].update({number: np.asarray(value) for number, value in (clips or {}).items()})
        if turn is not None:
            transform = turn_frame(turn)
            held = {entry[0] for entry in self.state["holds"].values()}
            for uid in held:
                self.state["controls"][uid] = _move_control(self.state["controls"][uid], transform)
            self.state["hands"] = [transform @ hand for hand in self.state["hands"]]
            self.state["yaw"] += turn
        for arm, (uid, end) in self.state["holds"].items():
            control = self.state["controls"][uid]
            self.state["hands"][arm] = self._hand(control["number"], self._shape(control["number"], control), end)
        self.phases.append(
            {
                "label": label,
                "start": self.time,
                "stop": self.time + duration,
                "before": before,
                "after": deepcopy(self.state),
                "turn": turn,
                "free_hands": free or [False, False],
            }
        )
        self.time += duration

    def evaluate(self, time: float, *, y_offset: float = 0.0) -> dict:
        """Evaluate tool targets and persistent component geometry at time [s].

        Args:
            time: Authored time [s], clamped to the sequence interval.
            y_offset: Final cell translation [m]. Default keeps the old OP030
                local coordinates; use 2.30 m for the provisional ST B location.

        Returns:
            Root/product poses [m], tool and pad-contact targets [m], normalized
            gripper fractions, per-wire centerlines [m]/rigid lug frames [m],
            held identities, support labels and free-hand path flags. Support
            labels document intended transfer order, not detected contact.
        """
        time = float(np.clip(time, 0.0, self.time))
        index = min(np.searchsorted([phase["stop"] for phase in self.phases], time, side="right"), len(self.phases) - 1)
        phase = self.phases[index]
        before, after = phase["before"], phase["after"]
        w = weight(time, phase["start"], phase["stop"])
        linear = np.clip((time - phase["start"]) / (phase["stop"] - phase["start"]), 0.0, 1.0)
        yaw = (1 - w) * before["yaw"] + w * after["yaw"]
        hands = [mix(a, b, w) for a, b in zip(before["hands"], after["hands"], strict=True)]
        controls = {}
        held = {entry[0] for entry in before["holds"].values()}
        for uid, a in before["controls"].items():
            b = after["controls"][uid]
            control = deepcopy(a)
            assert a["mode"] == b["mode"]
            if a["mode"] == "bend":
                control["center"] = (1 - w) * a["center"] + w * b["center"]
                control["rotation"] = mix(pose(a["rotation"]), pose(b["rotation"]), w)[:3, :3]
                control["progress"] = (1 - linear) * a["progress"] + linear * b["progress"]
            else:
                control["root"] = mix(a["root"], b["root"], w)
                control["t_raise"] = (1 - w) * a["t_raise"] + w * b["t_raise"]
            if phase["turn"] is not None and uid in held:
                control = _move_control(a, turn_frame(phase["turn"] * w))
            controls[uid] = control
        if phase["turn"] is not None:
            transform = turn_frame(phase["turn"] * w)
            hands = [transform @ hand for hand in before["hands"]]
        wires = {}
        for uid, control in controls.items():
            shape = self._shape(control["number"], control)
            wires[uid] = {
                "number": control["number"],
                "shape": shape,
                "control": control,
                "support": before["supports"][uid],
                "held_by": [],
            }
        for arm, (uid, end) in before["holds"].items():
            record = wires[uid]
            hands[arm] = self._hand(record["number"], record["shape"], end)
            record["held_by"].append(SIDES[arm])
        gaps = (1 - w) * before["gaps"] + w * after["gaps"]
        tools, grips = zip(
            *(
                tool_for(np.eye(4), hand[:3, 3], hand[:3, :3], float(gap))
                for hand, gap in zip(hands, gaps, strict=True)
            ),
            strict=True,
        )
        offset = np.array((0.0, y_offset, 0.0))
        root = pose(Rotation.from_euler("z", yaw).as_matrix(), (CX, CY + y_offset, 0.0))
        if y_offset:
            hands = [_translate(hand, offset) for hand in hands]
            tools = [_translate(tool, offset) for tool in tools]
            for record in wires.values():
                shape = record["shape"]
                record["shape"] = WireShape(
                    shape.centerline + offset,
                    {end: _translate(frame, offset) for end, frame in shape.lug_frames.items()},
                    {end: _translate(frame, offset) for end, frame in shape.grasp_frames.items()},
                    shape.progress,
                )
        return {
            "time": time,
            "phase_index": int(index),
            "label": phase["label"],
            "tools": np.asarray(tools),
            "grips": np.asarray(grips),
            "hands": np.asarray(hands),
            "gaps": gaps,
            "yaw": yaw,
            "root": root,
            "product_pose": _translate(self.work, offset),
            "wires": wires,
            "holds": before["holds"].copy(),
            "free_hands": phase["free_hands"],
            "support_is_intended_not_measured": True,
            "clips": {number: (1 - w) * before["clips"][number] + w * after["clips"][number] for number in (1, 2)},
        }


@lru_cache(maxsize=4096)
def _insertion_coefficients(
    number: int, terminal_raise: float, connection_mode: ConnectionMode = "rear_entry"
) -> tuple:
    rest = lug_frame(number, "T")
    return tuple(
        coefficients(
            WireBend(number, connection_mode=connection_mode).final_points,
            np.eye(4),
            pose(location=(0.0, 0.0, terminal_raise)) @ rest,
            rest,
        )
    )


def build_sequence(config: WirePlacementConfig | None = None) -> WirePlacementSequence:
    """Return the complete authored ST B spatial target schedule [m, rad, s]."""
    return WirePlacementSequence(config)


def reference_time(sequence: WirePlacementSequence, time: float) -> float:
    """Map current authored time [s] to the pre-clip finite IK survey [s].

    Added clip actuation intervals keep both robot target poses fixed. Their
    reference time is the preceding interval endpoint. All other interval
    labels and spatial targets are unchanged.
    """
    phases = json.loads((ROOT / "audit/op030_split_wire_motion_initial.json").read_text())["phases"]
    reference = {phase["label"]: phase for phase in phases}
    target = sequence.evaluate(time)
    phase = sequence.phases[target["phase_index"]]
    if phase["label"] in reference:
        old = reference[phase["label"]]
        u = np.clip((time - phase["start"]) / (phase["stop"] - phase["start"]), 0, 1)
        return float(old["start"] + u * (old["stop"] - old["start"]))
    preceding = sequence.phases[: target["phase_index"]]
    for previous in reversed(preceding):
        if previous["label"] in reference:
            return float(reference[previous["label"]]["stop"])
    raise ValueError("No matching pre-clip reference interval")


def current_time(sequence: WirePlacementSequence, old_time: float) -> float:
    """Map a pre-clip reference time [s] to current authored time [s]."""
    phases = json.loads((ROOT / "audit/op030_split_wire_motion_initial.json").read_text())["phases"]
    index = min(np.searchsorted([phase["stop"] for phase in phases], old_time, side="right"), len(phases) - 1)
    old = phases[index]
    new = next(phase for phase in sequence.phases if phase["label"] == old["label"])
    u = np.clip((old_time - old["start"]) / (old["stop"] - old["start"]), 0, 1)
    return float(new["start"] + u * (new["stop"] - new["start"]))


def target_checks(sequence: WirePlacementSequence) -> dict:
    """Check target continuity, rigid translation and final geometry [m, rad]."""
    epsilon = 1e-7
    max_hand_jump, max_wire_jump = 0.0, 0.0
    for phase in sequence.phases[:-1]:
        a = sequence.evaluate(phase["stop"] - epsilon)
        b = sequence.evaluate(phase["stop"] + epsilon)
        max_hand_jump = max(max_hand_jump, float(np.max(abs(a["hands"] - b["hands"]))))
        for uid in sequence.active_uids.values():
            max_wire_jump = max(
                max_wire_jump,
                float(np.max(abs(a["wires"][uid]["shape"].centerline - b["wires"][uid]["shape"].centerline))),
            )
    final, initial = sequence.evaluate(sequence.time), sequence.evaluate(0.0)
    maximum_final_error = 0.0
    for number, uid in sequence.active_uids.items():
        expected = sequence.bends[number].final_points @ sequence.work[:3, :3].T + sequence.work[:3, 3]
        maximum_final_error = max(
            maximum_final_error, float(np.max(abs(final["wires"][uid]["shape"].centerline - expected)))
        )
    for uid in set(initial["wires"]) - set(sequence.active_uids.values()):
        assert np.array_equal(initial["wires"][uid]["shape"].centerline, final["wires"][uid]["shape"].centerline)
    a, b = sequence.evaluate(34.321), sequence.evaluate(34.321, y_offset=2.3)
    offset_error = float(np.max(abs(b["tools"][:, :3, 3] - a["tools"][:, :3, 3] - (0, 2.3, 0))))
    assert max_hand_jump < 1e-6 and max_wire_jump < 1e-6 and maximum_final_error < 1e-12 and offset_error < 1e-12
    return {
        "maximum_boundary_hand_matrix_difference": max_hand_jump,
        "maximum_boundary_wire_coordinate_difference_m": max_wire_jump,
        "maximum_final_centerline_error_m": maximum_final_error,
        "global_y_offset_covariance_error_m": offset_error,
        "unchosen_eight_wires_unchanged": True,
        "passed": True,
        "geometry_only": True,
    }


def survey_branches(sequence: WirePlacementSequence, step: float = 0.5, branch_seeds: int = 4) -> tuple[dict, dict]:
    """Survey a finite set of continuous IK branches for each held interval.

    Args:
        sequence: Authored spatial targets.
        step: Maximum diagnostic sample spacing [s].
        branch_seeds: Accepted-v02 seed count per traversal direction.

    Returns:
        Every branch result and candidate joint arrays [rad]. Feasible here
        means only bounded continuous IK; all collision/force checks remain.
    """
    with np.load(ROOT / "data/op030_motion_v02.npz") as saved:
        accepted = saved["joints"].copy()
    seed_indices = np.linspace(0, len(accepted) - 1, max(2, branch_seeds), dtype=int)
    intervals = []
    for arm in (0, 1):
        current = None
        for phase in sequence.phases:
            hold = phase["before"]["holds"].get(arm)
            if hold is None or current is not None and current["uid"] != hold[0]:
                if current is not None:
                    intervals.append(current)
                    current = None
            if hold is not None:
                if current is None:
                    current = {"arm": arm, "uid": hold[0], "start": phase["start"], "stop": phase["stop"]}
                current["stop"] = phase["stop"]
        if current is not None:
            intervals.append(current)
    result, arrays = [], {}
    for section, interval in enumerate(intervals):
        arm = interval["arm"]
        times = np.unique(
            np.r_[
                np.arange(interval["start"], interval["stop"], step),
                interval["stop"],
                [p["start"] for p in sequence.phases if interval["start"] < p["start"] < interval["stop"]],
            ]
        )
        targets = [sequence.evaluate(float(time)) for time in times]
        chains = [chain_for(tuple((target["root"] @ R.yoke_base_pose(SIDES[arm])).ravel())) for target in targets]
        branch_records = []
        seen = []
        for reverse in (False, True):
            indices = list(range(len(times)))
            if reverse:
                indices.reverse()
            first = indices[0]
            for seed_index in seed_indices:
                q, error = chains[first].solve(targets[first]["tools"][arm], accepted[seed_index, arm], max_nfev=100)
                if error > 1e-5:
                    branch_records.append(
                        {
                            "reverse": reverse,
                            "reference_seed_index": int(seed_index),
                            "feasible": False,
                            "failure": "endpoint_ik",
                            "residual": error,
                        }
                    )
                    continue
                if any(direction == reverse and np.max(abs(old - q)) < 1e-4 for direction, old in seen):
                    continue
                seen.append((reverse, q.copy()))
                samples = {first: q.copy()}
                failure = None
                max_error, max_delta = float(error), 0.0
                for index in indices[1:]:
                    next_q, residual = chains[index].solve_continuous(targets[index]["tools"][arm], q)
                    delta = float(np.max(abs(next_q - q)))
                    max_delta, max_error = max(max_delta, delta), max(max_error, float(residual))
                    if residual > 1e-5 or np.any(abs(next_q) >= LIMITS) or delta > 0.8:
                        failure = {
                            "time_s": float(times[index]),
                            "residual": float(residual),
                            "joint_delta_rad": delta,
                            "within_limits": bool(np.all(abs(next_q) < LIMITS)),
                        }
                        break
                    q = next_q
                    samples[index] = q.copy()
                record = {
                    "reverse": reverse,
                    "reference_seed_index": int(seed_index),
                    "feasible": failure is None,
                    "failure": failure,
                    "maximum_residual": max_error,
                    "maximum_adjacent_joint_delta_rad": max_delta,
                }
                if failure is None:
                    key = f"section_{section}_branch_{len(branch_records)}"
                    arrays[key] = np.array([samples[index] for index in range(len(times))])
                    record["array_key"] = key
                    record["maximum_abs_joint_rad"] = float(np.max(abs(arrays[key])))
                branch_records.append(record)
        arrays[f"section_{section}_times"] = times
        result.append(
            {
                **interval,
                "side": SIDES[arm],
                "samples": len(times),
                "branches": branch_records,
                "feasible_branch_count": sum(record["feasible"] for record in branch_records),
            }
        )
        print(
            "OP030B_BRANCH_SECTION",
            section,
            interval["uid"],
            SIDES[arm],
            result[-1]["feasible_branch_count"],
            flush=True,
        )
    report = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "config": asdict(sequence.config),
        "sections": result,
        "all_held_sections_have_a_continuous_branch": all(section["feasible_branch_count"] > 0 for section in result),
        "step_s": step,
        "seed_indices": seed_indices.tolist(),
        "joint_delta_screen_rad": 0.8,
        "collisions_checked": False,
        "formal_physical_verdict": None,
        "target_checks": target_checks(sequence),
        "scope": "Finite IK seed survey only; no collision validity or continuous whole-cycle promotion",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return report, arrays


def reach_diagnostics(sequence: WirePlacementSequence, step: float = 0.5, branch_seeds: int = 4) -> tuple[dict, dict]:
    """Run one bounded FK/IK continuity diagnostic, without collision checks.

    Args:
        sequence: Target schedule.
        step: Maximum authored sample interval [s].
        branch_seeds: Additional accepted-v02 seeds tried only after local IK
            fails. No random or unbounded retry loop is used.

    Returns:
        JSON-compatible report and arrays suitable for a dedicated diagnostic
        NPZ. Failed samples remain visible; they are not promoted to motion.
    """
    capture_robots()  # Verify the existing unmodified robot capture is available.
    accepted_path = ROOT / "data/op030_motion_v02.npz"
    with np.load(accepted_path) as saved:
        accepted = saved["joints"].copy()
    seed_rows = np.linspace(0, len(accepted) - 1, branch_seeds + 1, dtype=int)
    seed = accepted[0].copy()
    times = np.unique(
        np.r_[
            np.arange(0.0, sequence.time, step),
            sequence.time,
            [p["start"] for p in sequence.phases],
            [p["stop"] for p in sequence.phases],
        ]
    )
    records, failures, branches = [], [], []
    max_length_error, max_endpoint_gap = 0.0, 0.0
    for sample, time in enumerate(times):
        state = sequence.evaluate(float(time))
        q_values, errors, positions, rotations = [], [], [], []
        for arm, side in enumerate(SIDES):
            base = state["root"] @ R.yoke_base_pose(side)
            chain = chain_for(tuple(base.ravel()))
            goal = state["tools"][arm]
            q, error = chain.solve_continuous(goal, seed[arm])
            q = nearest_turn(q, seed[arm])
            if error > 1e-5 or np.any(abs(q) >= LIMITS):
                alternatives = []
                for seed_index in seed_rows:
                    candidate, residual = chain.solve(goal, accepted[seed_index, arm], max_nfev=80)
                    candidate = nearest_turn(candidate, seed[arm])
                    alternatives.append(
                        (residual, float(np.linalg.norm(candidate - seed[arm])), candidate, int(seed_index))
                    )
                feasible = [entry for entry in alternatives if entry[0] <= 1e-5 and np.all(abs(entry[2]) < LIMITS)]
                choice = (
                    min(feasible, key=lambda entry: entry[1])
                    if feasible
                    else min(alternatives, key=lambda entry: entry[0])
                )
                if choice[0] < error or feasible:
                    error, _, q, seed_index = choice
                    branches.append(
                        {
                            "time_s": float(time),
                            "arm": side,
                            "reference_seed_index": seed_index,
                            "joint_delta_rad": float(np.max(abs(q - seed[arm]))),
                            "residual": float(error),
                        }
                    )
            actual = chain.forward(q)[0]
            position_error = float(np.linalg.norm(actual[:3, 3] - goal[:3, 3]))
            rotation_error = float(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ goal[:3, :3].T).as_rotvec()))
            if error > 1e-5 or np.any(abs(q) >= LIMITS):
                failures.append(
                    {
                        "time_s": float(time),
                        "phase_index": state["phase_index"],
                        "label": state["label"],
                        "arm": side,
                        "residual": float(error),
                        "position_error_m": position_error,
                        "orientation_error_rad": rotation_error,
                        "within_joint_bounds": bool(np.all(abs(q) < LIMITS)),
                    }
                )
            q_values.append(q)
            errors.append(error)
            positions.append(position_error)
            rotations.append(rotation_error)
        seed = np.asarray(q_values)
        for uid in sequence.active_uids.values():
            record = state["wires"][uid]
            bend = sequence.bends[record["number"]]
            shape = record["shape"]
            length = float(np.linalg.norm(np.diff(shape.centerline, axis=0), axis=1).sum())
            max_length_error = max(max_length_error, abs(length - bend.length))
            for end, index in (("J1", 0), ("T", -1)):
                frame = shape.lug_frames[end]
                point = frame[:3, :3] @ bend.barrel_points[end] + frame[:3, 3]
                max_endpoint_gap = max(max_endpoint_gap, float(np.linalg.norm(point - shape.centerline[index])))
        records.append((state, seed.copy(), errors, positions, rotations))
        if sample % 50 == 0:
            print("OP030B_TARGET_REACH", sample, round(float(time), 3), len(failures), flush=True)
    arrays = {
        "times": times,
        "joints": np.array([record[1] for record in records]),
        "target_tools": np.array([record[0]["tools"] for record in records]),
        "target_hands": np.array([record[0]["hands"] for record in records]),
        "grips": np.array([record[0]["grips"] for record in records]),
        "root_poses": np.array([record[0]["root"] for record in records]),
        "phase_indices": np.array([record[0]["phase_index"] for record in records]),
        "residuals": np.array([record[2] for record in records]),
    }
    for number, uid in sequence.active_uids.items():
        arrays[f"wire_{number}_centerlines"] = np.array(
            [record[0]["wires"][uid]["shape"].centerline for record in records]
        )
        arrays[f"wire_{number}_lug_frames"] = np.array(
            [[record[0]["wires"][uid]["shape"].lug_frames[end] for end in ("J1", "T")] for record in records]
        )
    report = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "config": asdict(sequence.config),
        "sample_count": len(times),
        "authored_duration_s": sequence.time,
        "failures": failures,
        "branch_restarts": branches,
        "maximum_position_error_m": float(np.max([record[3] for record in records])),
        "maximum_orientation_error_rad": float(np.max([record[4] for record in records])),
        "maximum_wire_length_error_m": max_length_error,
        "maximum_lug_attachment_gap_m": max_endpoint_gap,
        "maximum_adjacent_joint_delta_rad": float(np.max(abs(np.diff(arrays["joints"], axis=0)))),
        "active_uid_order": [sequence.active_uids[number] for number in (2, 1)],
        "phases": [{key: p[key] for key in ("start", "stop", "label", "free_hands")} for p in sequence.phases],
        "accepted_seed_sha256": hashlib.sha256(accepted_path.read_bytes()).hexdigest(),
        "collisions_checked": False,
        "formal_physical_verdict": None,
        "scope": "Spatial target and FK reach diagnostic only; joints are not collision-screened or retimed",
        "sources": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                ROOT / "scripts/op030_split_wire.py",
                ROOT / "scripts/op030_cable.py",
                ROOT / "scripts/op030_fk_fast.py",
                ROOT / "scripts/op030_motion.py",
            )
        },
    }
    return report, arrays


def main() -> None:
    """Write a bounded initial target/IK diagnostic; keep all failures visible."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--step_s", type=float, default=0.5)
    parser.add_argument("--branch_seeds", type=int, default=4)
    parser.add_argument("--output", default="op030_split_wire_motion_current")
    parser.add_argument("--branch_survey", action="store_true")
    parser.add_argument("--h1_form_center_z", type=float)
    parser.add_argument("--h1_release_left_first", action="store_true")
    parser.add_argument("--h1_release_gap", type=float)
    parser.add_argument("--connection_mode", choices=("rear_entry", "top_entry"), default="rear_entry")
    parser.add_argument("--insertion_z", type=float, default=0.020)
    args = parser.parse_args()
    if (ROOT / "analysis" / (args.output + ".npz")).exists() or (ROOT / "audit" / (args.output + ".json")).exists():
        raise FileExistsError("Use a new output name; existing diagnostics are immutable reference evidence")
    sequence = build_sequence(
        WirePlacementConfig(
            h1_form_center_z=args.h1_form_center_z,
            h1_release_left_first=args.h1_release_left_first,
            h1_release_gap=args.h1_release_gap,
            connection_mode=args.connection_mode,
            insertion_z=args.insertion_z,
        )
    )
    report, arrays = (
        survey_branches(sequence, args.step_s, args.branch_seeds)
        if args.branch_survey
        else reach_diagnostics(sequence, args.step_s, args.branch_seeds)
    )
    path = ROOT / "analysis" / (args.output + ".npz")
    np.savez_compressed(path, **arrays)
    report["diagnostic_npz_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.branch_survey:
        print("OP030B_BRANCH_SURVEY_COMPLETE", report["all_held_sections_have_a_continuous_branch"], flush=True)
    else:
        print("OP030B_TARGET_REACH_COMPLETE", len(report["failures"]), report["sample_count"], flush=True)


if __name__ == "__main__":
    main()
