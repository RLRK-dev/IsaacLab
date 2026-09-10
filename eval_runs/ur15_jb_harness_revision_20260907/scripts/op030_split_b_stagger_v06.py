# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Place the B robot opposite the unchanged product using retained geometry [m, rad, s]."""

import json
from copy import deepcopy

import numpy as np
from op020_jb_motion import weight
from op030_definition import CY, ROOT, pose
from op030_motion import tool_for, turn_frame
from op030_split_b_v05 import build_sequence as build_v05
from op030_split_wire_motion import WirePlacementConfig, WirePlacementSequence, _move_control
from scipy.spatial.transform import Rotation

SOURCE_BANK = ROOT / "data/op030_split_b_motion_v05.npz"
SOURCE_CONFIG = ROOT / "audit/op030_split_b_motion_v05.json"
SIDE_DELTA = pose(np.diag([-1.0, -1.0, 1.0]), (0.0, 2 * CY, 0.0))


class StaggerSequence(WirePlacementSequence):
    """Reuse wire material points while moving only robot/supply across the line [m]."""

    def __init__(
        self,
        config: WirePlacementConfig | None = None,
        *,
        work_yaw_degrees: float = 270.0,
        grasp_side_flip: bool = False,
        orbit_y_m: float | None = None,
        overbody: bool = False,
        swap_roles: bool = False,
        bend_during_turn: bool = False,
        h1_yaw_bias_degrees: float = 0.0,
        omit_formation_wait: bool = False,
    ):
        config = config or WirePlacementConfig(**json.loads(SOURCE_CONFIG.read_text())["config"])
        original = build_v05(config)
        self.__dict__.update(deepcopy(original.__dict__))
        self.original = original
        self.work_yaw_degrees = work_yaw_degrees
        self.grasp_side_flip = grasp_side_flip
        self.orbit_y_m = orbit_y_m
        self.overbody = overbody
        self.swap_roles = swap_roles
        self.bend_during_turn = bend_during_turn
        self.h1_yaw_bias_degrees = h1_yaw_bias_degrees
        self.omit_formation_wait = omit_formation_wait
        hand_delta = []
        for arm in (0, 1):
            rotation = Rotation.from_euler("y", 180 if arm == 0 else 160, degrees=True).as_matrix()
            hand_delta.append(rotation.T @ SIDE_DELTA[:3, :3] @ rotation if grasp_side_flip else np.eye(3))
        for number in (1, 2):
            for arm, end in ((0, "T"), (1, "J1")):
                self.calibration[number][end] = self.calibration[number][end] @ hand_delta[arm]
        self.transfer_phases = {
            number: next(p for p in original.phases if p["label"] == f"H03-{number}／両端保持で組付側へ旋回")
            for number in (1, 2)
        }
        self.park_phases = {
            number: next(p for p in original.phases if p["label"] == f"H03-{number}／両腕待機位置へ")
            for number in (1, 2)
        }
        for row in self.rows:
            row["shape"] = self._shape(
                row["number"], self._control(row["uid"], original.phases[0]["before"]["controls"][row["uid"]], 0.0)
            )
        for index, phase in enumerate(self.phases):
            old = original.phases[index]
            for key, time_key in (("before", "start"), ("after", "stop")):
                state = phase[key]
                time = phase[time_key]
                for arm in (0, 1):
                    state["hands"][arm][:3, :3] = state["hands"][arm][:3, :3] @ hand_delta[arm]
                fraction = (state["yaw"] + np.pi / 2) / np.pi
                state["yaw"] = np.pi / 2 + fraction * np.radians(work_yaw_degrees - 90.0)
                state["controls"] = {
                    uid: self._control(uid, control, time) for uid, control in state["controls"].items()
                }
                transformed = (
                    time <= self.transfer_phases[2]["start"]
                    or self.park_phases[2]["stop"] <= time <= self.transfer_phases[1]["start"]
                    or time >= self.park_phases[1]["stop"]
                )
                if transformed:
                    state["hands"] = [SIDE_DELTA @ hand for hand in state["hands"]]
                for arm, (uid, end) in state["holds"].items():
                    control = state["controls"][uid]
                    state["hands"][arm] = self._hand(control["number"], self._shape(control["number"], control), end)
            phase["original_turn"] = old["turn"]
            phase["turn"] = None
            phase["logical_yaw_before"] = old["before"]["yaw"]
            phase["logical_yaw_after"] = old["after"]["yaw"]
            phase["legacy_start"], phase["legacy_stop"] = old["start"], old["stop"]
            phase["original_phase_index"] = index
        if swap_roles:
            # Change the authored task assignment, never the robot identities,
            # joint arrays, meshes or endpoint names. Both arms require new IK.
            for phase in self.phases:
                for key, time_key in (("before", "start"), ("after", "stop")):
                    state = phase[key]
                    time = phase[time_key]
                    physical_park = (
                        time <= original.phases[0]["stop"]
                        or self.park_phases[2]["stop"]
                        <= time
                        <= next(p["start"] for p in original.phases if p["label"] == "H03-1／両指を両端の被覆上方へ")
                        or time >= self.park_phases[1]["stop"]
                    )
                    if not physical_park:
                        state["hands"] = [state["hands"][1], state["hands"][0]]
                    state["gaps"] = np.asarray(state["gaps"])[[1, 0]]
                    state["holds"] = {1 - arm: hold for arm, hold in state["holds"].items()}
                phase["free_hands"] = list(reversed(phase["free_hands"]))
        self.removed_intervals = []
        if omit_formation_wait:
            if not bend_during_turn:
                raise ValueError("Formation can only be omitted after it is completed during the turn")
            retained, clock = [], 0.0
            for phase in self.phases:
                if "両指を動かして所定経路へ曲げる" in phase["label"]:
                    self.removed_intervals.append((phase["start"], phase["stop"]))
                    continue
                duration = phase["stop"] - phase["start"]
                phase["start"], phase["stop"] = clock, clock + duration
                clock += duration
                if phase["original_turn"] is not None and phase["before"]["holds"]:
                    phase["label"] = phase["label"].replace("両端保持で組付側へ旋回", "両端保持で旋回しながら曲げる")
                retained.append(phase)
            self.phases, self.time = retained, clock
            self.source_phases = [original.source_phases[p["original_phase_index"]] for p in retained]
            self.phase_kinds = [original.phase_kinds[p["original_phase_index"]] for p in retained]

    def _control(self, uid: str, control: dict, time: float) -> dict:
        if uid not in self.active_uids.values():
            return _move_control(control, SIDE_DELTA)
        phase = self.transfer_phases[control["number"]]
        if time <= phase["start"]:
            return _move_control(control, SIDE_DELTA)
        if time <= phase["stop"]:
            result = _move_control(control, SIDE_DELTA)
            # Orbit the straight wire around the torso without reversing its
            # material direction; the product still requires Rz(pi).
            result["rotation"] = SIDE_DELTA[:3, :3] @ phase["before"]["controls"][uid]["rotation"]
            if self.bend_during_turn:
                result["progress"] = 1.0
            return result
        result = deepcopy(control)
        if self.bend_during_turn and result["mode"] == "bend":
            result["progress"] = 1.0
        return result

    def evaluate(self, time: float, *, y_offset: float = 0.0) -> dict:
        """Return baseline targets, with optional one-time global Y offset [m, s]."""
        result = super().evaluate(time)
        phase = self.phases[result["phase_index"]]
        turn = phase["original_turn"]
        if turn is not None and phase["label"].startswith("H03-1"):
            fraction = float(np.clip((time - phase["start"]) / (phase["stop"] - phase["start"]), 0, 1))
            result["yaw"] += np.radians(self.h1_yaw_bias_degrees) * np.sin(np.pi * fraction) ** 2
        if turn is not None:
            w = weight(time, phase["start"], phase["stop"])
            transform = SIDE_DELTA @ turn_frame(turn * w) @ SIDE_DELTA
            if result["holds"] and not self.overbody:
                for uid in {hold[0] for hold in result["holds"].values()}:
                    control = deepcopy(phase["before"]["controls"][uid])
                    if self.bend_during_turn:
                        control["progress"] = float(
                            np.clip((time - phase["start"]) / (phase["stop"] - phase["start"]), 0, 1)
                        )
                    start_center = control["center"].copy()
                    control["center"] = transform[:3, :3] @ control["center"] + transform[:3, 3]
                    if self.orbit_y_m is not None:
                        angle = turn * w
                        control["center"][1] = (
                            CY + (start_center[1] - CY) * np.cos(angle) + self.orbit_y_m * np.sin(angle)
                        )
                    wire = result["wires"][uid]
                    wire["control"], wire["shape"] = control, self._shape(wire["number"], control)
            elif not result["holds"]:
                result["hands"] = np.array([transform @ hand for hand in phase["before"]["hands"]])
        for arm, (uid, end) in result["holds"].items():
            wire = result["wires"][uid]
            result["hands"][arm] = self._hand(wire["number"], wire["shape"], end)
        tools, grips = zip(
            *(
                tool_for(np.eye(4), hand[:3, 3], hand[:3, :3], float(gap))
                for hand, gap in zip(result["hands"], result["gaps"], strict=True)
            ),
            strict=True,
        )
        result["tools"], result["grips"] = np.array(tools), np.array(grips)
        result["root"] = pose(Rotation.from_euler("z", result["yaw"]).as_matrix(), (0.9, CY, 0.0))
        fraction = weight(time, phase["start"], phase["stop"])
        result["work_side"] = bool(
            (1 - fraction) * phase["logical_yaw_before"] + fraction * phase["logical_yaw_after"] >= 0.0
        )
        if y_offset:
            offset = pose(location=(0.0, y_offset, 0.0))
            result["root"] = offset @ result["root"]
            result["product_pose"] = offset @ result["product_pose"]
            result["hands"] = offset @ result["hands"]
            result["tools"] = offset @ result["tools"]
            for wire in result["wires"].values():
                wire["control"] = _move_control(wire["control"], offset)
                wire["shape"] = self._shape(wire["number"], wire["control"])
        return result


def build_sequence(
    config: WirePlacementConfig | None = None,
    *,
    work_yaw_degrees: float = 270.0,
    grasp_side_flip: bool = False,
    orbit_y_m: float | None = None,
    overbody: bool = False,
    swap_roles: bool = False,
    bend_during_turn: bool = False,
    h1_yaw_bias_degrees: float = 0.0,
    omit_formation_wait: bool = False,
) -> StaggerSequence:
    """Build opposite-side B targets with the same product and ten wire UIDs [m, s]."""
    return StaggerSequence(
        config,
        work_yaw_degrees=work_yaw_degrees,
        grasp_side_flip=grasp_side_flip,
        orbit_y_m=orbit_y_m,
        overbody=overbody,
        swap_roles=swap_roles,
        bend_during_turn=bend_during_turn,
        h1_yaw_bias_degrees=h1_yaw_bias_degrees,
        omit_formation_wait=omit_formation_wait,
    )


def build_sequence_final(config: WirePlacementConfig | None = None) -> StaggerSequence:
    """Build the chosen normal-height physical-left-J1 task without duplicate forming waits [m, s]."""
    return StaggerSequence(
        config,
        work_yaw_degrees=270.0,
        grasp_side_flip=False,
        orbit_y_m=0.780,
        overbody=False,
        swap_roles=True,
        bend_during_turn=True,
        h1_yaw_bias_degrees=15.0,
        omit_formation_wait=True,
    )
