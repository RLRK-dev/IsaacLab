# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Re-derive §5 of the line review: what the dual-arm configuration actually is [m].

``HANDOFF_v07_ライン構成見直し.md`` §5 is the open question the user wants next, and it has
never been inspected. §5.2 says the cost of the present configuration "has been measured" and
puts 5.9 mm against it; §5.3 carries that same 5.9 mm in the current row's self-interference
column. It is the only measured number in the whole section, so it is the one to check first.

It does not measure the present configuration. The pair behind it is
``OP030C__source_1054_m0309_p00`` against ``source_1136_m0304_p00``, which the equipment
inventory tags ``robot_OP030_left`` and ``robot_OP040_left``. Both halves are wrong for the
use §5 puts it to: it is OP030's arm against **OP040's** arm, not one arm against the other on
the same column, and it is the **mirrored S3R copy** that case ② would build, not anything
standing today.

Nothing measures the two arms against each other, and nothing can, as the probes are built.
``obstacles(exclude)`` returns every object that is **not** moving, and a cell's moving set
holds both of its arms, so left against right is never a candidate. The probe also mirrors
only the moving side: it is a tool for asking what a copy would be built into, not for asking
what a cell does to itself. This sweeps every committed pair list to confirm the count is zero
rather than asserting it from the code alone.

What can be measured from committed artifacts is the geometry the choice between §5.3's
options turns on, and none of it is written down anywhere:

  the column       one per cell, and both arms stand on it
  the base pitch   how far apart the two shoulders are
  the reach in     how far each arm must come back toward the station centre to work

The envelopes here come from the v06 layout inventory, which is **one saved pose**, not a
swept volume. In that pose the arms are splayed away from each other, which is why their
boxes stand apart while the working overlap is real. A pose is not a sweep, and this reports
the pose.

Read-only. A derivation from artifacts at their recorded timestamps, not a physical-validity
verdict, and not a takt.

    python3 scripts/check_op030_v07c_dual_arm_configuration.py [--quiet]
"""

from __future__ import annotations

import glob
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EQUIPMENT = ROOT / "audit/op030_v06_equipment_ids.json"
SELECTION = ROOT / "analysis/op030_v07c_cell_selection.json"
RELOCATION = ROOT / "analysis/op030_v06_relocation_selection.json"
CLEARANCE = ROOT / "audit/op030_v07c_mirror_clearance.json"
CONTACT = ROOT / "audit/op030_v07c_mesh_contact.json"
REPORT = ROOT / "audit/op030_v07c_dual_arm_configuration.json"

LEFT, RIGHT = "robot_OP030_left", "robot_OP030_right"
# Each cell's station centre line, the same values the mirror probe uses.
STATION_Y_M = {"A": -1.700, "B": 0.600, "C": 2.900}
# The column: tagged with the cell, standing on the floor and carrying the shoulders. It is an
# assembly of parts (p00..p08), not one object, so the members are grouped by their source id.
COLUMN_TAG = "assembly_cell_03"
COLUMN_FOOT_MAX_Z_M = 0.500
# The shoulders sit near Z 1.54, so the group that carries them has to reach past this.
COLUMN_HEAD_MIN_Z_M = 1.400
SOURCE_ID = re.compile(r"(source_\d+)")
# The figure §5.2 and §5.3 attribute to the present configuration.
DISPUTED_M = 0.0059
# The committed motion source, which is where the arms' division of labour is actually written.
# Each anchor is an exact line that must still be there; the check fails loudly if one moves.
MOTION_ANCHORS = {
    # The takt source. OP030_v07_刷新仕様案 §2 names this file, and its sequence is not the base
    # class's: the base releases the support before fastening, this one holds through it.
    "scripts/op030_support_motion_v04.py": {
        "the takt source authors its own sequence": "def support_sequence_v04() -> SupportSequenceV04:",
        "the yoke turns to the supply side": 'seq.turn(-np.pi, f"T{number:02d}／供給側へ旋回")',
        "the yoke turns back with the support held": 'seq.turn(np.pi, f"T{number:02d}／保持して組付側へ旋回")',
        "arm 1 grasps the support out of the kit": "seq.grasp(1, name, relative, seq.support_grasp_gap_m,",
        "the support is lifted off the grid": "objects={name: offset(seq.objects[name], (0, 0, 0.40))})",
        "the first M4 is fetched while the support is placed": "／設置と並行してM4を受取る",
        "placing runs as a track beside that fetch": "seq.parallel_placements.append(track)",
        "the placing motion is seven seconds long": "seat_stop_s=receipt.receive_start_s + 7,",
        "the second M4 is fetched while the right arm holds": "／右保持中に2本目を補充",
        "both bolts are driven with the right still holding": "／右保持のままM4",
        "the support is let go only after both are driven": "／2本締結・左工具退避後に支持を解放",
    },
    # The base class, for what it defines rather than what it sequences.
    "scripts/op030_split_support_motion.py": {
        "the M4 tool is permanent, not fetched": (
            '"""ST A support placement with a permanent left-arm M4 spindle [m, rad, s]."""'
        ),
        "arm 0 carries the M4 tool": 'self.driver_names = {0: "OP030A_driver_M4"}',
        "the tool has a park pose, not a stocker cell": "def driver_home(self, arm):",
        "its own sequence is the superseded one: it lets go first": (
            'seq.release(1, f"T{number:02d}／支持面へ移管", gap=0.060)'
        ),
    },
    # B's irreducible pair, in one line: each arm holds one end of the same cable.
    "scripts/op030_split_wire_motion.py": {
        "both arms hold the two ends of one cable": 'self.state["holds"] = {0: (uid, "T"), 1: (uid, "J1")}',
        "B turns to the supply": '"OP030B／次の直線ケーブル供給へ旋回", 5.0, turn=-np.pi',
        "B turns back holding both ends": '／両端保持で組付側へ旋回", 6.0, turn=np.pi',
    },
    "scripts/op030_split_b_stagger_v06.py": {
        "v06 bends the cable during that turn": '"両端保持で組付側へ旋回", "両端保持で旋回しながら曲げる"',
    },
    "scripts/op030_motion.py": {
        "a turn moves both hands, not one": "self.hands = [transform @ hand for hand in self.hands]",
        "the turn angle is a single shared scalar": "self.yaw += turn",
        "the turn is about the cell centre": "center = np.array([CX, CY, 0])",
        "a turn lasts six seconds": "self.phase(label, 6.0, turn=angle)",
    },
}
# Every station's motion source, swept for turns. The first version looked for ".turn(" alone
# and reported that only A turns. B turns too: it passes turn= straight to phase() instead of
# going through the Sequence.turn helper, so that pattern missed it.
STATION_SOURCES = {
    "A (v04, the takt source)": "scripts/op030_support_motion_v04.py",
    "A (superseded base)": "scripts/op030_split_support_motion.py",
    "B (authored)": "scripts/op030_split_wire_motion.py",
    "B (v06 wrapper)": "scripts/op030_split_b_stagger_v06.py",
    "C (v04)": "scripts/op030_split_c_v04.py",
    "C (v05)": "scripts/op030_split_c_v05.py",
    "C (fastening ops)": "scripts/op030_split_fastening_motion.py",
    "pre-split, one cell did both": "scripts/op030_motion.py",
}
# Both ways a turn is asked for. Missing the second is what produced the wrong sweep.
TURN_CALLS = (".turn(", "turn=np.pi", "turn=-np.pi")
# Where the fastening round trip is authored. It turns nothing, so that wait is a real wait.
FASTENER_SOURCE = "scripts/op030_fastener_operations_v04.py"


def load(path: Path) -> dict:
    """Return a committed JSON artifact."""
    return json.loads(path.read_text())


def cell_names(selection: dict, relocation: dict) -> dict[str, dict]:
    """Return each cell's selected objects, with the parent and placement each carries."""
    cells = {}
    for cell in ("A", "C"):
        cells[cell] = {entry["name"]: entry for entry in selection["targets"][cell]["selection"]}
    cells["B"] = {name: {"name": name} for name in relocation["all_selected_object_names"]}
    return cells


def envelope(boxes: list) -> dict | None:
    """Return the combined box of a set of world boxes [m]."""
    if not boxes:
        return None
    return dict(
        low_m=[min(box[0][axis] for box in boxes) for axis in range(3)],
        high_m=[max(box[1][axis] for box in boxes) for axis in range(3)],
        member_count=len(boxes),
    )


def separation(low_a: list, high_a: list, low_b: list, high_b: list) -> tuple[float, int]:
    """Return the gap on the axis that separates two boxes most, and that axis [m]."""
    gaps = [max(low_b[axis] - high_a[axis], low_a[axis] - high_b[axis]) for axis in range(3)]
    widest = max(range(3), key=lambda axis: gaps[axis])
    return gaps[widest], widest


def find_column(objects: dict, names: dict, station_y: float) -> dict | None:
    """Return the cell's floor-standing assembly that reaches the shoulders [m].

    The column is an assembly, so its parts are grouped by the source id in their names and the
    group that stands on the floor and reaches highest is the one carrying the arms.
    """
    groups: dict[str, list] = {}
    for name in names:
        record = objects.get(name, {})
        box = record.get("bounds_world_m")
        if not box or record.get("equipment_id") != COLUMN_TAG:
            continue
        match = SOURCE_ID.search(name)
        if match:
            groups.setdefault(match.group(1), []).append(box)

    standing = {}
    for source, boxes in groups.items():
        low = [min(box[0][axis] for box in boxes) for axis in range(3)]
        high = [max(box[1][axis] for box in boxes) for axis in range(3)]
        if low[2] <= COLUMN_FOOT_MAX_Z_M and high[2] >= COLUMN_HEAD_MIN_Z_M:
            standing[source] = dict(
                source=source,
                part_count=len(boxes),
                low_m=low,
                high_m=high,
                centre_x_m=(low[0] + high[0]) / 2.0,
                centre_y_m=(low[1] + high[1]) / 2.0,
                centred_on_station=abs((low[1] + high[1]) / 2.0 - station_y) < 1e-3,
            )
    if not standing:
        return None
    tallest = max(standing.values(), key=lambda row: row["high_m"][2])
    return dict(count=len(standing), chosen=tallest, others=[row["source"] for row in standing.values()])


def find_mount(objects: dict, entries: dict, side: str, column: dict) -> dict | None:
    """Return an arm's shoulder: the first link of its chain [m].

    The source ids run along the chain from the base outward, so the lowest id on a side is its
    shoulder. Unlike "the lowest link over the column" this does not move with the pose, and the
    caller checks it: the shoulder has to stand inside the column footprint, and the two sides
    have to come out symmetric about the station centre.
    """
    numbered = []
    for name, entry in entries.items():
        translation = entry.get("world_translation_m")
        match = SOURCE_ID.search(name)
        if translation is None or match is None:
            continue
        if objects.get(name, {}).get("equipment_id") != side:
            continue
        numbered.append((int(match.group(1)[len("source_") :]), name, translation))
    if not numbered:
        return None
    first = min(identifier for identifier, _, _ in numbered)
    links = sorted(name for identifier, name, _ in numbered if identifier == first)
    x_m, y_m, z_m = next(translation for identifier, _, translation in numbered if identifier == first)
    return dict(
        chain_starts_at=f"source_{first}",
        links=links,
        x_m=x_m,
        y_m=y_m,
        z_m=z_m,
        inside_column_footprint=bool(
            column["low_m"][0] <= x_m <= column["high_m"][0] and column["low_m"][1] <= y_m <= column["high_m"][1]
        ),
    )


def sweep_for_arm_pairs(objects: dict) -> dict:
    """Return every committed pair whose two sides are the two arms of one OP030 cell."""
    tagged = 0
    arm_pairs = []
    files = sorted(glob.glob(str(ROOT / "audit/*.json"))) + sorted(glob.glob(str(ROOT / "analysis/*.json")))
    for path in files:
        try:
            body = json.loads(Path(path).read_text())
        except (ValueError, OSError):
            continue

        def walk(node, source=path) -> None:
            nonlocal tagged
            if isinstance(node, dict):
                moving, obstacle = node.get("moving"), node.get("obstacle")
                if isinstance(moving, str) and isinstance(obstacle, str):
                    left = objects.get(moving, {}).get("equipment_id")
                    right = objects.get(obstacle, {}).get("equipment_id")
                    if left and right:
                        tagged += 1
                        if {left, right} == {LEFT, RIGHT}:
                            arm_pairs.append(dict(file=Path(source).name, moving=moving, obstacle=obstacle))
                for value in node.values():
                    walk(value, source)
            elif isinstance(node, list):
                for value in node:
                    walk(value, source)

        walk(body)
    return dict(
        files_scanned=len(files),
        tagged_pairs_seen=tagged,
        left_against_right_pairs=len(arm_pairs),
        pairs=arm_pairs,
        why_zero=(
            "obstacles(exclude) returns every object that is not moving, and a cell's moving set holds"
            " both arms, so the box stage never forms the pair. The probe also mirrors only the moving"
            " side: it asks what a copy would be built into, not what a cell does to itself."
        ),
    )


def trace_disputed(contact: dict, objects: dict) -> dict:
    """Return what the 5.9 mm figure actually measured."""
    found = []

    def walk(node) -> None:
        if isinstance(node, dict):
            nearest = node.get("nearest_m")
            named = isinstance(node.get("moving"), str) and isinstance(node.get("obstacle"), str)
            if named and isinstance(nearest, float) and abs(nearest - DISPUTED_M) < 5e-5:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(contact)
    rows = [
        dict(
            moving=row["moving"],
            moving_tag=objects.get(row["moving"], {}).get("equipment_id"),
            obstacle=row["obstacle"],
            obstacle_tag=objects.get(row["obstacle"], {}).get("equipment_id"),
            nearest_m=row["nearest_m"],
            nearest_from_moving_m=row.get("nearest_from_moving_m"),
            nearest_from_obstacle_m=row.get("nearest_from_obstacle_m"),
        )
        for row in found
    ]
    same_robot = [row for row in rows if {row["moving_tag"], row["obstacle_tag"]} == {LEFT, RIGHT}]
    return dict(
        matches=rows,
        measures_one_arm_against_the_other=bool(same_robot),
        moving_side_is_a_mirrored_copy=all(row["moving"].startswith("OP030C__") for row in rows) if rows else None,
        finding=(
            "§5.2 and §5.3 put this against the present configuration. It is OP030's left arm in the"
            " mirrored S3R copy against OP040's left arm: a different station's robot, and a copy that"
            " case ② would build rather than anything standing today."
            if rows and not same_robot
            else "no match found"
        ),
    )


def read_the_motion_source() -> dict:
    """Return what the committed motion source says about the two arms' division of labour.

    §5 reasons about the arms from the documents. The sequence is committed, so it can be read
    instead. Anchors are exact lines: if one is gone the check fails rather than reporting a
    stale conclusion.
    """
    anchors: dict = {}
    missing = []
    for source, wanted in MOTION_ANCHORS.items():
        path = ROOT / source
        text = path.read_text() if path.exists() else ""
        lines = text.splitlines()
        found = {}
        for meaning, needle in wanted.items():
            hits = [number for number, line in enumerate(lines, 1) if needle in line]
            found[meaning] = dict(needle=needle, lines=hits)
            if not hits:
                missing.append(f"{source}: {meaning}")
        anchors[source] = found

    turning = {}
    for station, source in STATION_SOURCES.items():
        path = ROOT / source
        lines = path.read_text().splitlines() if path.exists() else []
        calls = [
            dict(line=number, text=line.strip())
            for number, line in enumerate(lines, 1)
            if any(pattern in line for pattern in TURN_CALLS) and "def turn" not in line
        ]
        turning[station] = dict(source=source, turn_calls=len(calls), calls=calls)

    fastener = ROOT / FASTENER_SOURCE
    fastener_lines = fastener.read_text().splitlines() if fastener.exists() else []
    fastener_turns = [number for number, line in enumerate(fastener_lines, 1) if any(p in line for p in TURN_CALLS)]

    turners = [station for station, row in turning.items() if row["turn_calls"]]
    return dict(
        anchors=anchors,
        anchors_missing=missing,
        turning=turning,
        stations_that_turn=turners,
        fastening_round_trip_turns=len(fastener_turns),
        reading=dict(
            the_M4_spindle_is_permanent=True,
            the_right_arm_also_transports=(
                "arm 1 grasps the support out of the withdrawn kit, lifts it 0.40 m, and is still"
                " holding it through the 180 degree turn back to the assembly side. It transports and"
                " then holds; it does not only hold."
            ),
            the_turn_is_shared=(
                "phase() applies one turn_frame to both entries of self.hands and advances a single"
                " self.yaw, about the cell centre. A turn is the yoke moving, not an arm moving, so the"
                " M4 driver rides to the supply side and back on every support."
            ),
            what_that_costs=(
                "§2.6 books 43.2 s as the holding arm doing nothing but hold: 31.7 s of feeder round"
                " trips plus 11.5 s of turning. Neither part reads that way in the takt source. The"
                " turning is the yoke carrying both arms, so it is not one arm waiting for the other"
                " and feeder integration cannot recover it. Of the two round trips per support, only"
                " the second is a wait -- the first is labelled 設置と並行して and runs beside the"
                " placing track, whose motion is seven seconds inside a 16.6 s fetch. So the holding"
                " arm is placing for part of the first fetch, not waiting through it."
            ),
            which_file_the_takt_came_from=(
                "OP030_v07_刷新仕様案 §2 names op030_support_motion_v04.py. Its sequence differs from"
                " the base class in op030_split_support_motion.py, which releases the support before"
                " fastening instead of holding through it. Reading the base for A's division of labour"
                " gives the superseded answer."
            ),
            which_stations_turn=(
                "A and B both turn. B's is the stronger case: its two arms hold one cable by its two"
                " ends and v06 renames the turning phase to 両端保持で旋回しながら曲げる, so for B the"
                " turn is part of forming the bend rather than only carrying. C's sequence is a"
                " recorded bank and no authored turn appears in its sources, which is weaker than"
                " saying C never turns."
            ),
            corrected=(
                "An earlier run of this check reported that only A turns. It searched for '.turn('"
                " and B passes turn= to phase() directly, so B was missed."
            ),
        ),
    )


def main() -> int:
    quiet = "--quiet" in sys.argv

    equipment = load(EQUIPMENT)
    objects = equipment["objects"]
    selection = load(SELECTION)
    relocation = load(RELOCATION)
    contact = load(CONTACT)
    load(CLEARANCE)

    failures: list[str] = []
    cells = cell_names(selection, relocation)

    disputed = trace_disputed(contact, objects)
    if not disputed["matches"]:
        failures.append("the 5.9 mm figure was not found in the contact report")

    swept = sweep_for_arm_pairs(objects)

    source = read_the_motion_source()
    for line in source["anchors_missing"]:
        failures.append(f"the motion source moved: {line}")

    mounting: dict[str, dict] = {}
    for cell, entries in cells.items():
        station_y = STATION_Y_M[cell]
        column = find_column(objects, entries, station_y)
        row: dict = dict(station_y_m=station_y, column=column)
        if column:
            one = column["chosen"]
            left = find_mount(objects, entries, LEFT, one)
            right = find_mount(objects, entries, RIGHT, one)
            row["mounts"] = dict(left=left, right=right)
            if left and right:
                span_x = right["x_m"] - left["x_m"]
                span_y = right["y_m"] - left["y_m"]
                pitch = math.hypot(span_x, span_y)
                midpoint = ((left["x_m"] + right["x_m"]) / 2.0, (left["y_m"] + right["y_m"]) / 2.0)
                row["shared_column"] = dict(
                    both_on_one_column=bool(left["inside_column_footprint"] and right["inside_column_footprint"]),
                    base_pitch_m=pitch,
                    same_height=abs(left["z_m"] - right["z_m"]) < 1e-6,
                    base_height_m=left["z_m"],
                    midpoint_xy_m=list(midpoint),
                    midpoint_is_the_station_centre=abs(midpoint[1] - station_y) < 1e-3,
                    # A's shoulder line runs along Y; C's is the same pair turned about the vertical.
                    shoulder_line_yaw_deg=math.degrees(math.atan2(abs(span_x), abs(span_y))),
                    # Both tools have to meet over the station centre, which is the midpoint.
                    reach_back_to_centre_m=pitch / 2.0,
                )

        arms = {}
        for side in (LEFT, RIGHT):
            boxes = [
                objects[name]["bounds_world_m"]
                for name in entries
                if objects.get(name, {}).get("equipment_id") == side and objects[name].get("bounds_world_m")
            ]
            arms[side] = envelope(boxes)
        row["saved_pose_envelope"] = arms
        if arms[LEFT] and arms[RIGHT]:
            gap_m, axis = separation(
                arms[LEFT]["low_m"], arms[LEFT]["high_m"], arms[RIGHT]["low_m"], arms[RIGHT]["high_m"]
            )
            row["saved_pose_gap"] = dict(
                gap_m=gap_m,
                deciding_axis="xyz"[axis],
                boxes_overlap=gap_m < 0.0,
                this_is_one_pose_not_a_sweep=True,
            )
        mounting[cell] = row

    pitches = {cell: row.get("shared_column", {}).get("base_pitch_m") for cell, row in mounting.items()}
    for cell, value in pitches.items():
        if value is not None:
            continue
        placed = any(entry.get("world_translation_m") for entry in cells[cell].values())
        if placed:
            failures.append(f"cell {cell} has placements but its two arms could not be put on its column")
        else:
            mounting[cell]["not_established"] = (
                "op030_v06_relocation_selection.json commits B's object names but not their placements,"
                " so B's shoulders cannot be located from a checkout"
            )
    for cell, row in mounting.items():
        shared = row.get("shared_column")
        if shared and not (shared["both_on_one_column"] and shared["midpoint_is_the_station_centre"]):
            failures.append(f"cell {cell}: the shoulders are not symmetric on one column, so the rule misread them")

    report = dict(
        observed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        scope="Re-derivation of HANDOFF_v07_ライン構成見直し §5 from committed artifacts only",
        read_from={
            str(path.relative_to(ROOT)): dict(observed_at=load(path).get("observed_at"))
            for path in (EQUIPMENT, SELECTION, RELOCATION, CLEARANCE, CONTACT)
        },
        what_this_does_not_give=[
            "any swept-volume or whole-motion result; the inventory is one saved pose",
            "the relative accuracy B's two-ended hold needs, which is a property of the real cable",
            "a takt, a cycle time, or a physical-validity verdict",
        ],
        disputed_figure=disputed,
        arm_against_arm_in_committed_artifacts=swept,
        division_of_labour_from_the_motion_source=source,
        mounting=mounting,
        answer=dict(
            the_5_9_mm_measures_the_present_configuration=disputed["measures_one_arm_against_the_other"],
            self_interference_measurements_that_exist=swept["left_against_right_pairs"],
            the_two_arms_share_a_yaw_axis=True,
            stations_that_use_it=source["stations_that_turn"],
            configuration=(
                "one column per cell, both arms on it, shoulders"
                f" {pitches['A'] * 1000:.1f} mm apart at Z {mounting['A']['shared_column']['base_height_m']:.4f},"
                f" each reaching {mounting['A']['shared_column']['reach_back_to_centre_m'] * 1000:.1f} mm back"
                " toward the station centre to work"
                if pitches.get("A")
                else "not established"
            ),
            verdict=(
                "§5.2's description of the configuration holds -- the two arms do share one column. Its"
                " evidence does not. The 5.9 mm belongs to a different pair entirely, and the present"
                " configuration's self-interference has never been measured. It also cannot be, with the"
                " probes as written, because they only ever test a mirrored copy against what is not"
                " moving. §5.3's current row therefore has no measured entry in its self-interference"
                " column, and the table's one number should come out."
            ),
        ),
        checks_failed=failures,
        formal_physical_validity_verdict=None,
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not quiet:
        print("the 5.9 mm figure:")
        for row in disputed["matches"]:
            print(f"  {row['moving']} ({row['moving_tag']})")
            print(f"    x {row['obstacle']} ({row['obstacle_tag']})   nearest {row['nearest_m']:.7f} m")
        print(f"  measures one arm against the other: {disputed['measures_one_arm_against_the_other']}")
        print()
        print(
            f"left-against-right pairs in {swept['files_scanned']} committed JSON files:"
            f" {swept['left_against_right_pairs']} (of {swept['tagged_pairs_seen']} tagged pairs)"
        )
        print(f"stations whose motion turns the shared yoke: {', '.join(source['stations_that_turn'])}")
        print(f"  the fastening round trip turns nothing ({source['fastening_round_trip_turns']} turn calls)")
        print("  of the two fetches per support, only the second waits on the hold; the first runs")
        print("  beside the placing track, and the 11.5 s of turning is the yoke carrying both arms")
        print()
        for cell, row in mounting.items():
            shared = row.get("shared_column")
            if not shared:
                print(f"cell {cell}: not established")
                continue
            print(
                f"cell {cell}: one column, both arms on it: {shared['both_on_one_column']};"
                f" pitch {shared['base_pitch_m'] * 1000:.1f} mm; base Z {shared['base_height_m']:.4f} m;"
                f" reach back to centre {shared['reach_back_to_centre_m'] * 1000:.1f} mm"
            )
            gap = row.get("saved_pose_gap")
            if gap:
                print(
                    f"         saved pose: arms {gap['gap_m'] * 1000:+.1f} mm apart on"
                    f" {gap['deciding_axis']} -- one pose, not a sweep"
                )
        print()
        print(report["answer"]["verdict"])
        print(f"\nwrote {REPORT.relative_to(ROOT)}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
