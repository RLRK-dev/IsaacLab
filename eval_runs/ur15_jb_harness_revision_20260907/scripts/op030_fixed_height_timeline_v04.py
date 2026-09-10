# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Schedule the three stations on one fixed-height pallet [m, s]."""

from dataclasses import dataclass

import numpy as np
from op030_definition import CY, LIFT

FPS = 30
CONVEYOR_RISE = 0.364
PALLET_Z = 0.789
OFFSETS = {"A": 0.0, "B": 2.3, "C": 4.6}


@dataclass(frozen=True)
class BankChunk:
    """Map inclusive bank samples into the global native frame sequence."""

    global_start: int
    local_start: int
    local_stop: int
    purpose: str

    @property
    def count(self):
        return self.local_stop - self.local_start

    @property
    def global_stop(self):
        return self.global_start + self.count

    @property
    def global_slice(self):
        return slice(self.global_start, self.global_stop)

    @property
    def local_slice(self):
        return slice(self.local_start, self.local_stop)


class Timeline:
    """Maintain a fixed workpiece Z while only positioner pins move [m]."""

    def __init__(self):
        self.values = {
            "y": [-2.85],
            "lift": [LIFT],
            "A": [-0.051],
            "B": [-0.051],
            "C": [-0.051],
            "drawer_B": [0.0],
            "op020_carriage_z": [0.378 + CONVEYOR_RISE],
            "entry_slide_x": [0.0],
            **{"stopper_" + name: [1.0] for name in ("OP020", "OP030A", "OP030B", "OP030C")},
        }
        self.segments = []
        self.banks = {}
        self.chunks = {name: [] for name in OFFSETS}
        self.overlaps = []

    @property
    def frame(self):
        return len(self.values["y"])

    def transition(self, label, duration, **targets):
        if "lift" in targets and targets["lift"] != LIFT:
            raise ValueError("The workpiece must stay at the fixed conveyor height")
        first = self.frame
        count = int(np.ceil(duration * FPS))
        u = np.arange(1, count + 1) / count
        weight = u**3 * (10 - 15 * u + 6 * u * u)
        for name, values in self.values.items():
            start, end = values[-1], targets.get(name, values[-1])
            values.extend((start + (end - start) * weight).tolist())
        self.segments.append(dict(label=label, first_frame=first, last_frame=self.frame, kind="transfer"))

    def station(self, name, bank, local_start=0):
        first = self.frame
        sample_count = len(bank["times"]) - local_start
        if sample_count < 2:
            raise ValueError("A station needs a start and an end sample")
        for values in self.values.values():
            values.extend([values[-1]] * (sample_count - 1))
        self.chunks[name].append(BankChunk(first - 1, local_start, len(bank["times"]), "work"))
        self.banks[name] = dict(first_frame=first, last_frame=self.frame)
        self.segments.append(
            dict(label="OP030" + name, first_frame=first, last_frame=self.frame, kind="station", station=name)
        )

    def arrive(self, station):
        self.transition(f"OP030{station}／高さを保ち位置決めピンを差し込む", 1.5, **{station: -0.014})

    def leave(self, station):
        self.transition(
            f"OP030{station}／位置決めピンを抜きストッパを退避",
            1.5,
            **{station: -0.051, "stopper_OP030" + station: 0.0},
        )


def assemble_timeline(banks):
    """Start C preloading and B tray presentation while A works [s]."""
    timeline = Timeline()
    timeline.transition("OP020／組付け治具を285mm外側へ退避・搬送高さ一定", 2.5, entry_slide_x=0.285)
    timeline.transition(
        "OP020／パレットを上げず位置決めピンを抜く",
        1.5,
        op020_carriage_z=0.341 + CONVEYOR_RISE,
        stopper_OP020=0.0,
    )
    timeline.transition("OP030Aへ本体・外部ハーネス・パレットを同じ高さで搬入", 6.0, y=CY)
    timeline.arrive("A")
    timeline.station("A", banks["A"])
    timeline.leave("A")
    timeline.transition("支持部と4本の取付ボルトを保持してOP030Bへ", 6.0, y=CY + OFFSETS["B"])
    timeline.arrive("B")
    timeline.station("B", banks["B"])
    timeline.leave("B")
    timeline.transition("両端を着座した2本のケーブルと同じ本体をOP030Cへ", 6.0, y=CY + OFFSETS["C"])
    timeline.arrive("C")
    preload_count = int(np.asarray(banks["C"]["preload_frame_count"]).item())
    if preload_count < 2 or preload_count >= len(banks["C"]["times"]):
        raise ValueError("C needs a complete prefill section and a subsequent work section")
    timeline.station("C", banks["C"], local_start=preload_count - 1)
    timeline.transition("3ST完了・次ワーク用ボルトを装填済み・搬送高さ一定", 2.0)
    start = timeline.banks["A"]["first_frame"] - 1
    prefill = BankChunk(start, 0, preload_count, "prefill_before_arrival")
    if prefill.global_stop >= timeline.banks["B"]["last_frame"]:
        raise ValueError("C prefill is not complete before the incoming workpiece transfer")
    timeline.chunks["C"].insert(0, prefill)
    timeline.overlaps.append(
        dict(station="C", purpose=prefill.purpose, first_frame=prefill.global_start + 1, last_frame=prefill.global_stop)
    )
    # This schedule must also be checked against the simultaneous A/C poses
    # and the incoming payload; the time mapping alone is not that check.
    from op030_split_b_v04_drawer import drawer_extension

    return_start = (timeline.banks["B"]["last_frame"] - 1) / FPS
    timeline.values["drawer_B"] = drawer_extension(
        np.arange(timeline.frame) / FPS, supply_start=start / FPS, return_start=return_start
    ).tolist()
    timeline.overlaps.extend(
        [
            dict(
                station="B",
                purpose="present_10_wires_while_A_works",
                first_frame=start + 1,
                last_frame=start + 1 + int(2.5 * FPS),
            ),
            dict(
                station="B",
                purpose="return_remaining_8_during_outfeed",
                first_frame=timeline.banks["B"]["last_frame"],
                last_frame=timeline.banks["B"]["last_frame"] + int(2.5 * FPS),
            ),
        ]
    )
    if np.ptp(timeline.values["lift"]) > 1e-12:
        raise AssertionError("An unrequested pallet lift entered the timeline")
    return timeline


def bank_track(values, chunks, count):
    """Hold the last state during idle gaps between mapped bank sections."""
    values = np.asarray(values)
    result = np.repeat(values[:1], count, axis=0)
    for chunk in chunks:
        result[chunk.global_slice] = values[chunk.local_slice]
        result[chunk.global_stop :] = values[chunk.local_stop - 1]
    return result


def bank_sparse_track(values, chunks, count):
    """Keep long waiting periods sparse when baking the robot meshes."""
    frames, indices = [0], [0]
    previous = 0
    for chunk in chunks:
        if chunk.global_start > frames[-1]:
            frames.append(chunk.global_start - 1)
            indices.append(previous)
        frames.extend(range(chunk.global_start, chunk.global_stop))
        indices.extend(range(chunk.local_start, chunk.local_stop))
        previous = chunk.local_stop - 1
    frames.append(count - 1)
    indices.append(previous)
    mapping = dict(zip(frames, indices, strict=True))
    ordered = np.array(sorted(mapping))
    return ordered + 1, np.asarray(values)[[mapping[key] for key in ordered]]
