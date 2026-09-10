# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Replace only the two post-fastening retreats with simultaneous ascent [m, s]."""

from copy import deepcopy
from dataclasses import replace

import numpy as np
from op030_motion import offset
from op030_support_motion_v04 import SupportSequenceV04, support_sequence_v04


class SupportSequenceV05(SupportSequenceV04):
    """Retain v04 geometry and ownership while lifting both released tools [m, s]."""

    def evaluate(self, time: float) -> dict:
        """Evaluate the same two-arm clock and explicitly constrained lift [m, rad, s]."""
        result = super().evaluate(time)
        phase = next((p for p in self.phases if time <= p["stop"] + 1e-9), self.phases[-1])
        if phase.get("simultaneous_ascent") or phase.get("v05_release"):
            result["free"][:] = False
        return result


def support_sequence_v05() -> SupportSequenceV05:
    """Return a v05 factory without changing the frozen v04 source or assets [m, s]."""
    old = support_sequence_v04()
    seq = SupportSequenceV05()
    seq.__dict__.update(deepcopy(old.__dict__))
    seq.phases = []
    seq.simultaneous_retreats = []
    seq.v04_segments = []
    clock, cursor = 0.0, 0
    windows = []
    for number, held in enumerate(old.support_hold_intervals, 1):
        start = held["fasteners"][-1]["tool_empty_s"]
        first = next(i for i, p in enumerate(old.phases) if abs(p["start"] - start) < 1e-8)
        last = next(
            i
            for i in range(first, len(old.phases))
            if old.phases[i]["start"] > held["release_s"] and old.phases[i]["label"] == "right／退避"
        )
        windows.append((number, first, last + 1))

    def keep(stop: int) -> None:
        nonlocal clock, cursor
        if cursor == stop:
            return
        begin = clock
        previous_start = old.phases[cursor]["start"]
        for index in range(cursor, stop):
            phase = deepcopy(old.phases[index])
            duration = phase["stop"] - phase["start"]
            phase.update(start=clock, stop=clock + duration, v04_phase_index=index)
            seq.phases.append(phase)
            clock += duration
        seq.v04_segments.append(
            dict(
                kind="reused", old_start=previous_start, old_stop=old.phases[stop - 1]["stop"], start=begin, stop=clock
            )
        )
        cursor = stop

    for number, first, stop in windows:
        keep(first)
        start = clock
        scratch = deepcopy(old)
        for key, value in old.phases[first]["before"].items():
            setattr(scratch, key, deepcopy(value))
        scratch.phases, scratch.time = [], clock
        uid = f"OP030_T{number:02d}_UID001"
        driver = scratch.driver_names[0]
        del scratch.holds[1]
        scratch.phase(f"T{number:02d}／2本締結完了・両腕停止のまま右指を開放", 0.7, gaps={1: 0.060})
        scratch.phases[-1].update(v05_release=True, free=[False, False])
        lift_start = scratch.time
        for height, duration in ((0.080, 1.8), (0.160, 2.0)):
            scratch.phase(
                f"T{number:02d}／左右同時に鉛直上昇・追加{height * 1000:.0f}mm",
                duration,
                objects={driver: offset(scratch.objects[driver], (0, 0, height))},
                hands={1: offset(scratch.hands[1], (0, 0, height))},
            )
            scratch.phases[-1].update(simultaneous_ascent=True, free=[False, False])
        lift_stop = scratch.time
        scratch.phase(f"T{number:02d}／上昇完了後に右指を全開", 0.5, gaps={1: 0.080})
        scratch.phase(f"T{number:02d}／上昇完了後に空ソケットの位相を戻す", 1.0)
        original_reset = next(p["spindle_reset"] for p in old.phases[first:stop] if "spindle_reset" in p)
        scratch.phases[-1]["spindle_reset"] = deepcopy(original_reset)
        clear = scratch.time
        scratch.park(0)
        scratch.park(1)
        clock = scratch.time
        for phase in scratch.phases:
            phase.update(v05_window=number)
        seq.phases.extend(scratch.phases)
        seq.simultaneous_retreats.append(
            dict(
                number=number,
                uid=uid,
                start_s=start,
                release_stop_s=lift_start,
                lift_start_s=lift_start,
                lift_stop_s=lift_stop,
                tool_clear_s=clear,
                stop_s=clock,
                world_lift_m=0.240,
                release_gap_m=0.060,
                old_start_s=old.phases[first]["start"],
                old_stop_s=old.phases[stop - 1]["stop"],
            )
        )
        seq.v04_segments.append(
            dict(
                kind="replacement",
                number=number,
                old_start=old.phases[first]["start"],
                old_stop=old.phases[stop - 1]["stop"],
                start=start,
                stop=clock,
            )
        )
        cursor = stop
    keep(len(old.phases))
    seq.time = clock

    def remap(time: float) -> float:
        segment = next((p for p in seq.v04_segments if time <= p["old_stop"] + 1e-8), seq.v04_segments[-1])
        if segment["kind"] == "replacement" and segment["old_start"] + 1e-8 < time < segment["old_stop"] - 1e-8:
            raise ValueError("Removed v04 interior time needs an explicit v05 event")
        return segment["start"] + np.clip(time - segment["old_start"], 0, segment["stop"] - segment["start"])

    for track in seq.parallel_placements:
        for key in ("start_s", "align_stop_s", "seat_stop_s", "stop_s"):
            track[key] = float(remap(track[key]))
    for record, window in zip(seq.support_hold_intervals, seq.simultaneous_retreats, strict=True):
        record["grasp_s"] = float(remap(record["grasp_s"]))
        record["seat_s"] = float(remap(record["seat_s"]))
        record["release_s"] = window["start_s"]
        for index, event in enumerate(record["fasteners"]):
            event["start_s"] = float(remap(event["start_s"]))
            event["tool_empty_s"] = float(remap(event["tool_empty_s"]))
            event["tool_clear_s"] = window["tool_clear_s"] if index else float(remap(event["tool_clear_s"]))
    for event in seq.fastener_events:
        event["time_s"] = float(remap(event["time_s"]))
    seq.work_complete_author_time_s = float(remap(old.work_complete_author_time_s))
    for arm, receipt in seq.tool_fasteners.items():
        seq.tool_fasteners[arm] = replace(
            receipt,
            **{
                key: float(remap(getattr(receipt, key)))
                for key in ("start_s", "receive_start_s", "attach_s", "clear_s")
            },
        )
    return seq
