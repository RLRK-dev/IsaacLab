# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Collect digest-bound, finite-frame v06 integration evidence without rerunning probes.

Only complete, mutually consistent reports produce output. This module imports no
Blender, collision checker, motion factory, or other report-producing module.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "op030_stagger_v06_integration"
PREPARED = "data/op030_split_animation_v06.npz"
PREPARED_SHA = "660d47df3dac122337e4ff82c3c4ce92c8e15ef3edf68dbc9dd9b24ed943f296"
STATIC_SHA = "0de256bcfa2c377ac3c5048d0ae2d3a88ae057e7b6dd501ae58da821530f46d6"
NATIVE_SHA = "8674c2483ac1fe7e3dc42e6b1d14fdc4919f28818784de4f53f878477714d338"
B_SHA = "41b353e220db025f432b06f384e9a256262fd9f76fa30b31da7353c4b5b4854d"
B_FACTORY = "op030_split_b_stagger_v06:build_sequence_final"
ROUTES = ("entry", "a_b", "b_c")
PARKS = {"b_initial": ("A",), "b_final": ("C",), "c_loaded": ("A", "B")}
BINDING_CHECKS = {
    "original_b_nodes_match_prepared",
    "retained_a_c_nodes_match_prepared",
    "proper_stagger_parent_rotation",
    "drawer_moves_world_minus_x",
    "ten_uids_present",
    "ten_uids_follow_drawer",
    "eight_remaining_uids_follow_returning_drawer",
    "remaining_uids_and_drawer_match_prepared",
}


def require(condition: bool, message: str) -> None:
    """Reject incomplete or inconsistent evidence even under Python optimization."""
    if not condition:
        raise ValueError(message)


def small(values: list | np.ndarray | float, limit: float, message: str) -> None:
    """Require finite errors smaller than the explicit threshold."""
    array = np.asarray(values, dtype=float)
    require(bool(np.all(np.isfinite(array)) and np.all(abs(array) < limit)), message)


def report_names() -> list[str]:
    """Return the required report inventory, without reading or writing artifacts."""
    names = [
        "op030_split_native_v06.json",
        PREFIX + "_prefill_plan.json",
        PREFIX + "_entry_binding.json",
        PREFIX + "_entry_binding_parent_assert.json",
    ]
    for window in ROUTES:
        names.extend(PREFIX + "_" + window + "_" + suffix + ".json" for suffix in ("export", "check", "check_fixtures"))
    for window, suffixes in {
        "prefill": ("export", "check", "classified"),
        "drawer": ("export", "check"),
        "background": ("export", "classified"),
    }.items():
        names.extend(PREFIX + "_" + window + "_" + suffix + ".json" for suffix in suffixes)
    names.extend("op030_stagger_v06_background_" + cell + ".json" for cell in "ABC")
    for window, cells in PARKS.items():
        names.append(PREFIX + "_" + window + "_export.json")
        names.extend(PREFIX + "_" + window + "_" + cell + "_check_wait.json" for cell in cells)
    names.extend(("op030_air_drop_ac_v06_completion.json", "op030_air_drop_a_v06.json", "op030_air_drop_c_v06.json"))
    return names


class Collector:
    """Validate saved evidence and assemble auxiliary integration observations."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.inputs: dict[Path, dict] = {}
        self.reports: dict[str, dict] = {}
        self.bank_counts: dict[str, int] = {}

    def path(self, value: str | Path) -> Path:
        """Resolve absolute, run-relative, or explicitly prefixed repository paths."""
        path = Path(value)
        if path.is_absolute():
            return path.resolve()
        if self.root.parent.name == "eval_runs" and path.parts[:2] == ("eval_runs", self.root.name):
            return (self.root.parent.parent / path).resolve()
        return (self.root / path).resolve()

    def pin(self, value: str | Path, expected: str | None = None) -> str:
        """Read and register a file's SHA256, rejecting a changed expected digest."""
        path = self.path(value)
        require(path.is_file(), "Missing input: " + str(path))
        if path not in self.inputs:
            before = path.stat()
            sha = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    sha.update(block)
            after = path.stat()
            require(
                (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
                "Input changed while hashing: " + str(path),
            )
            label = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)
            self.inputs[path] = dict(
                path=label, sha256=sha.hexdigest(), size_bytes=after.st_size, mtime_ns=after.st_mtime_ns
            )
        actual = self.inputs[path]["sha256"]
        require(expected is None or actual == expected, "SHA256 mismatch: " + str(path))
        return actual

    def read(self, value: str | Path) -> dict:
        """Read a registered JSON object without accepting a physical-validity verdict."""
        self.pin(value)
        data = json.loads(self.path(value).read_text(encoding="utf-8"))
        require(isinstance(data, dict), "Expected JSON object: " + str(value))
        require(data.get("formal_physical_validity_verdict") is None, "Unexpected formal verdict: " + str(value))
        return data

    def same_path(self, actual: str, expected: str | Path) -> None:
        """Require two report references to identify the same file."""
        require(self.path(actual) == self.path(expected), "Source path mismatch: " + actual)

    def bound(self, report: dict) -> None:
        """Require a report to reference this exact final native and prepared data."""
        require(report["native_sha256"] == self.native["output_sha256"], "Native report mismatch")
        require(report["prepared_sha256"] == PREPARED_SHA, "Prepared report mismatch")
        self.same_path(report["native"], self.native["output"])

    def interval(self, purpose: str) -> dict:
        """Read the unique prepared concurrent-operation interval."""
        rows = [row for row in self.prepared["parallel_operations"] if row["purpose"] == purpose]
        require(len(rows) == 1, "Missing or duplicated operation: " + purpose)
        return rows[0]

    def frame_ids(self, window: str) -> list[int]:
        """Derive the exact global frame sequence from the prepared schedule."""
        stations = self.prepared["station_ranges"]
        if window == "entry":
            return list(range(1, stations["A"]["first_frame"] + 1))
        if window in ("a_b", "b_c"):
            before, after = ("A", "B") if window == "a_b" else ("B", "C")
            return list(range(stations[before]["last_frame"], stations[after]["first_frame"] + 1))
        if window in ("prefill", "drawer"):
            purpose = "prefill_before_arrival" if window == "prefill" else "present_10_wires_while_A_works"
            row = self.interval(purpose)
            return list(range(row["first_frame"], row["last_frame"] + 1))
        if window == "background":
            return [1]
        if window == "c_loaded":
            return [self.interval("prefill_before_arrival")["last_frame"]]
        return [stations["B" if window == "b_initial" else "C"]["first_frame"]]

    def arrays(self) -> dict:
        """Verify saved station pose tracks and single world offsets [m, s]."""
        summary = {}
        count = self.prepared["frames"]
        with np.load(self.path(PREPARED), allow_pickle=False) as saved:
            require(np.array_equal(saved["frames"], np.arange(1, count + 1)), "Incomplete prepared frame array")
            for name in (
                "product",
                "pallet",
                "drawer_B",
                "drawer_B_world",
                "op020_carriage",
                "entry_slide_x",
                "lift_A",
                "lift_B",
                "lift_C",
                "stopper_poses",
            ):
                require(len(saved[name]) == count and np.isfinite(saved[name]).all(), "Invalid prepared array: " + name)
            small(saved["product"][:, 2, 3] - 0.8845, 2e-12, "Product height changed")
            small(saved["pallet"][:, 2, 3] - 0.789, 2e-12, "Pallet height changed")
            small(saved["product"][:, :3, :3] - saved["product"][:1, :3, :3], 2e-12, "Product rotation changed")
            for cell, offset in (("A", 0.0), ("B", 2.3), ("C", 4.6)):
                with np.load(self.path(self.prepared["banks"][cell]["path"]), allow_pickle=False) as bank:
                    total = len(bank["times"])
                    self.bank_counts[cell] = total
                    require(total > 1, "Empty station bank: " + cell)
                    small(bank["times"] - np.arange(total) / self.prepared["fps"], 1e-8, "Bank time sampling mismatch")
                    frames = saved["robot_frames_" + cell]
                    require(
                        frames[0] == 1 and frames[-1] == count and np.all(np.diff(frames) > 0),
                        "Invalid sparse station frame coverage",
                    )
                    require(np.array_equal(saved["robot_nodes_" + cell], bank["node_ids"]), "Station node IDs changed")
                    start = self.prepared["station_ranges"][cell]["first_frame"]
                    indices = np.clip(frames - start, 0, total - 1)
                    if cell == "C":
                        self.preload = int(bank["preload_frame_count"])
                        preload = self.interval("prefill_before_arrival")
                        require(
                            preload["last_frame"] - preload["first_frame"] + 1 == self.preload,
                            "Prefill coverage mismatch",
                        )
                        indices = np.where(
                            frames <= preload["last_frame"],
                            np.clip(frames - preload["first_frame"], 0, self.preload - 1),
                            np.clip(frames - start + self.preload - 1, self.preload - 1, total - 1),
                        )
                    expected = bank["poses"][indices].copy()
                    expected[:, :, 1, 3] += offset
                    actual = saved["robot_poses_" + cell]
                    require(actual.shape == expected.shape, "Prepared station pose shape mismatch")
                    small(actual - expected, 2e-12, "Prepared station poses or world offset mismatch: " + cell)
                    if cell == "B":
                        small(bank["root_poses"][:, :3, 3] - [0.9, -1.7, 0.0], 2e-12, "B baseline root mismatch")
                        rotations = bank["root_poses"][:, :3, :3]
                        small(np.linalg.det(rotations) - 1, 2e-12, "Improper B root rotation")
                        small(
                            np.swapaxes(rotations, -1, -2) @ rotations - np.eye(3),
                            2e-12,
                            "Nonorthogonal B root rotation",
                        )
                        old_metadata = self.read("data/op030_split_animation_v05.json")
                        old_b = old_metadata["banks"]["B"]
                        self.pin(old_b["path"], old_b["sha256"])
                        with np.load(self.path(old_b["path"]), allow_pickle=False) as old_bank:
                            for endpoint in (0, -1):
                                delta = rotations[endpoint] @ old_bank["root_poses"][endpoint, :3, :3].T
                                small(
                                    delta - np.diag([-1.0, -1.0, 1.0]), 2e-12, "B endpoint placement is not 180 degrees"
                                )
                    station = self.prepared["station_ranges"][cell]
                    expected_count = total - self.preload + 1 if cell == "C" else total
                    require(station["last_frame"] - start + 1 == expected_count, "Station schedule count mismatch")
                    summary[cell] = dict(
                        frames=total,
                        duration_s=float(bank["times"][-1]),
                        sparse_native_samples=len(frames),
                        global_y_offset_m=offset,
                        maximum_saved_pose_error=float(np.max(abs(actual - expected))),
                    )
        return summary

    def export(self, window: str) -> dict:
        """Bind an actual mesh export and its frame arrays to the final native [m, s]."""
        row = self.reports[PREFIX + "_" + window + "_export.json"]
        self.bound(row)
        require(row["window"] == window, "Export window mismatch")
        frames = self.frame_ids(window)
        require(row["global_frames"] == frames, "Export frame coverage mismatch: " + window)
        mesh = "analysis/" + PREFIX + "_" + window + "_meshes.npz"
        self.pin(mesh, row["output_sha256"])
        with np.load(self.path(mesh), allow_pickle=False) as data:
            names = data["names"]
            require(len(names) > 0 and len(set(names.tolist())) == len(names), "Empty or duplicated export mesh names")
            for key in ("vertices", "faces", "vertex_offsets", "face_offsets"):
                require(np.isfinite(data[key]).all(), "Nonfinite mesh array: " + key)
            require(
                len(data["vertex_offsets"]) == len(names) + 1 and len(data["face_offsets"]) == len(names) + 1,
                "Mesh offset count mismatch",
            )
            for key, values in (("vertex_offsets", "vertices"), ("face_offsets", "faces")):
                require(
                    data[key][0] == 0 and data[key][-1] == len(data[values]) and np.all(np.diff(data[key]) > 0),
                    "Invalid mesh offsets",
                )
            reported_meshes = row.get("selected_meshes", row.get("meshes"))
            require(reported_meshes == len(names), "Export mesh count mismatch")
            moving_families = []
            if window in (*ROUTES, "prefill", "drawer"):
                require(np.array_equal(data["global_frames"], frames), "Export NPZ frame mismatch")
                require(data["matrices"].shape == (len(frames), len(names), 4, 4), "Export matrix shape mismatch")
                require(np.isfinite(data["matrices"]).all(), "Nonfinite exported matrices")
                small(
                    data["times"] - (np.asarray(frames) - frames[0]) / self.prepared["fps"],
                    1e-8,
                    "Export time mismatch",
                )
                require(data["payload"].shape == (len(names),) and data["payload"].any(), "Empty payload selection")
                if window in ROUTES:
                    moved = np.max(abs(data["matrices"] - data["matrices"][:1]), axis=(0, 2, 3)) > 1e-7
                    moving_families = [
                        family for family in row["moving_families"] if np.any((data["families"] == family) & moved)
                    ]
        return dict(report=row, mesh=mesh, frames=frames, moving_families=moving_families)

    def raw_check(self, window: str, exported: dict, *, allow_fixed: bool = False) -> dict:
        """Require the exact export's raw report and preserve its contact inventory."""
        row = self.reports[PREFIX + "_" + window + "_check.json"]
        require(row["mesh_sha256"] == exported["report"]["output_sha256"], "Raw check mesh mismatch")
        require(row["frames"] == len(exported["frames"]), "Raw check frame count mismatch")
        require(row["support_contact_exemptions"] == [], "New raw contact exemptions")
        require(allow_fixed or not row["hits"], "Unclassified dynamic hits: " + window)
        return row

    def station_check(self, row: dict, cell: str, first: int) -> None:
        """Bind a station checker report to its full expected bank interval."""
        self.bound(row)
        require(row["cell"] == cell, "Station cell mismatch")
        bank = self.prepared["banks"][cell]
        self.same_path(row["bank"], bank["path"])
        require(row["bank_sha256"] == bank["sha256"], "Station bank mismatch")
        self.pin(row["mesh"], row["mesh_sha256"])
        require(row["frames"] == self.bank_counts[cell] - first, "Station frame count mismatch")
        require(row["bank_frame_range_one_based"] == [first + 1, self.bank_counts[cell]], "Station interval mismatch")
        require(bool(row["active_meshes"]), "Empty station moving selection")
        require(row["contact_exemptions"] == [], "New station contact exemptions")

    def prefill(self, exported: dict, raw: dict, background: dict) -> dict:
        """Verify that the classifier accounts for every raw prefill contact pair."""
        row = self.reports[PREFIX + "_prefill_classified.json"]
        raw_path = "audit/" + PREFIX + "_prefill_check.json"
        self.same_path(row["raw_report"], raw_path)
        self.pin(raw_path, row["raw_report_sha256"])
        require(row["mesh_sha256"] == exported["report"]["output_sha256"], "Prefill classified mesh mismatch")
        require(
            row["native_sha256"] == self.native["output_sha256"] and row["pinned_static_sha256"] == STATIC_SHA,
            "Prefill classified source mismatch",
        )
        self.same_path(row["pinned_static"], background["fixed_source_comparison"]["source"])
        require(row["frames"] == raw["frames"], "Prefill classified frame mismatch")
        require(row["moving_contact_pair_count"] == 0 and row["moving_contact_pairs"] == [], "Dynamic prefill contact")
        require(row["unchanged_fixed_pair_count"] == len(row["unchanged_fixed_pairs"]), "Fixed prefill count mismatch")
        require(
            row["raw_contacts_preserved"] is True and row["added_contact_exemptions"] == [],
            "Prefill raw contact preservation mismatch",
        )
        observed = Counter(
            (pair["payload"], pair["environment"], hit["frame"]) for hit in raw["hits"] for pair in hit["pairs"]
        )
        classified = Counter()
        fixed_summary = []
        for pair in row["unchanged_fixed_pairs"]:
            small(pair["maximum_matrix_variation"], 1.000001e-7, "Classified fixed pair moves")
            require(
                len(pair["source_comparisons"]) == 2
                and {item["name"] for item in pair["source_comparisons"]} == set(pair["pair"]),
                "Missing fixed pair source comparison",
            )
            require(bool(pair["local_frames"]), "Empty fixed-pair contact record")
            for comparison in pair["source_comparisons"]:
                if "world_vertex_error_m" in comparison:
                    small(comparison["world_vertex_error_m"], 5.000001e-6, "Fixed prefill source differs")
                    require(comparison["topology_equal"] is True, "Fixed prefill topology differs")
                else:
                    require(comparison["name"] == "OP030C__source_0576_m0050_p00", "Unbound fixed prefill mesh")
            classified.update((*pair["pair"], frame) for frame in pair["local_frames"])
            fixed_summary.append(
                dict(
                    pair=pair["pair"],
                    contact_frame_count=len(pair["local_frames"]),
                    local_frame_range=[min(pair["local_frames"]), max(pair["local_frames"])],
                    maximum_matrix_variation=pair["maximum_matrix_variation"],
                    source_comparisons=pair["source_comparisons"],
                )
            )
        require(classified == observed, "Prefill classification omits or invents raw contacts")
        return dict(
            frames=raw["frames"],
            global_frames=[exported["frames"][0], exported["frames"][-1]],
            moving_contact_pairs=0,
            unchanged_fixed_pairs=fixed_summary,
        )

    def background(self, exported: dict) -> dict:
        """Preserve only the classified original fixed floor interfaces separately."""
        row = self.reports[PREFIX + "_background_classified.json"]
        require(row["candidate_native_sha256"] == self.native["output_sha256"], "Background classifier native mismatch")
        require(row["background_sha256"] == exported["report"]["output_sha256"], "Background classifier mesh mismatch")
        self.pin(row["original_definition"], row["original_definition_sha256"])
        self.pin(row["prior_record"])
        require(row["unexpected_pair_count"] == 0, "Unexpected background contacts")
        require(
            len(row["rows"]) == 3 and {r["cell"] for r in row["rows"]} == set("ABC"),
            "Incomplete background classification",
        )
        summary = {}
        for classified in row["rows"]:
            cell = classified["cell"]
            raw_path = "audit/op030_stagger_v06_background_" + cell + ".json"
            raw = self.reports[Path(raw_path).name]
            self.same_path(classified["raw_report"], raw_path)
            self.pin(raw_path, classified["raw_sha256"])
            self.station_check(raw, cell, 0)
            self.same_path(raw["background"], exported["mesh"])
            require(raw["background_sha256"] == row["background_sha256"], "Station background mesh mismatch")
            require(classified["frames"] == raw["frames"], "Classified background frame mismatch")
            require(classified["unexpected_motion_or_static_pairs"] == [], "Unexpected classified background contact")
            require(
                classified["fixed_base_has_no_bank_track"] is True
                and classified["original_raw_data_preserved"] is True,
                "Fixed floor evidence incomplete",
            )
            fixed_name = ("" if cell == "A" else "OP030" + cell + "__") + "source_0576_m0050_p00"
            require(classified["fixed_base_mesh"] == fixed_name, "Fixed floor mesh mismatch")
            small(classified["geometric_overlap_m"] - 0.007, 1e-6, "Original fixed floor overlap differs")
            expected = []
            for pair in raw["results"]["pairs"]:
                require(
                    [pair["changed"], pair["other"]] == ["source_0001_m0001_p00", fixed_name],
                    "Unclassified raw background contact",
                )
                expected.append(
                    dict(
                        pair=[pair["changed"], pair["other"]],
                        frames=len(pair["frames"]),
                        reported_fcl_depth_m=pair["maximum_depth_m"],
                    )
                )
            require(
                classified["original_fixed_installation_pairs"] == expected,
                "Background classifier omits raw floor contacts",
            )
            require(
                set(raw["results"]["hit_frames"])
                == {frame for pair in raw["results"]["pairs"] for frame in pair["frames"]},
                "Unclassified background hit frames",
            )
            summary[cell] = dict(
                frames=raw["frames"],
                unexpected_pairs=0,
                original_fixed_installation_pairs=expected,
                candidate_background_names=raw["candidate_background_names"],
                equal_context_mesh_count=len(raw["already_in_station_context"]),
                same_name_different_geometry_rechecked=raw["same_name_different_geometry_rechecked"],
                inherited_complete_delta_checks=self.inherited_pipe(cell, raw, exported),
            )
        return summary

    def inherited_pipe(self, cell: str, raw: dict, exported: dict) -> list[dict]:
        """Bind reused A/C pipe evidence to the exact four exported world meshes [m]."""
        inherited = raw["inherited_complete_delta_checks"]
        require(len(inherited) == (0 if cell == "B" else 1), "Incomplete inherited pipe evidence scope")
        for entry in inherited:
            report_path = "audit/op030_air_drop_" + cell.lower() + "_v06.json"
            self.same_path(entry["report"], report_path)
            self.pin(report_path, entry["report_sha256"])
            previous = self.reports[Path(report_path).name]
            self.pin(entry["world_meshes"], entry["world_meshes_sha256"])
            require(
                entry["frames"] == previous["frames"] == self.bank_counts[cell], "Inherited pipe bank coverage mismatch"
            )
            require(
                entry["bank_sha256"] == raw["bank_sha256"] and entry["mesh_sha256"] == raw["mesh_sha256"],
                "Inherited pipe station source mismatch",
            )
            require(
                entry["static_sha256"] == STATIC_SHA and entry["geometry_matches"] is True,
                "Inherited pipe static mismatch",
            )
            for path, sha in (
                (raw["bank"], raw["bank_sha256"]),
                (raw["mesh"], raw["mesh_sha256"]),
                (entry["world_meshes"], entry["world_meshes_sha256"]),
                (self.prepared["static_native"]["path"], STATIC_SHA),
            ):
                relative = str(self.path(path).relative_to(self.root))
                require(previous["input_digests"][relative] == sha, "Inherited pipe input digest mismatch")
            require(
                previous["results"]["hit_frames"] == [] and previous["results"]["pairs"] == [],
                "Inherited pipe contacts",
            )
            with (
                np.load(self.path(entry["world_meshes"]), allow_pickle=False) as delta,
                np.load(self.path(exported["mesh"]), allow_pickle=False) as world,
            ):
                names = delta["names"].tolist()
                require(
                    len(names) == 4
                    and set(names) == set(entry["mesh_names"]) == set(entry["maximum_world_vertex_errors_m"]),
                    "Inherited pipe mesh selection mismatch",
                )
                lookup = {str(name): index for index, name in enumerate(world["names"])}
                for index, name in enumerate(names):
                    other = lookup[name]
                    points = delta["vertices"][delta["vertex_offsets"][index] : delta["vertex_offsets"][index + 1]]
                    actual = world["vertices"][world["vertex_offsets"][other] : world["vertex_offsets"][other + 1]]
                    faces = delta["faces"][delta["face_offsets"][index] : delta["face_offsets"][index + 1]]
                    actual_faces = world["faces"][world["face_offsets"][other] : world["face_offsets"][other + 1]]
                    require(
                        points.shape == actual.shape and np.array_equal(faces, actual_faces),
                        "Inherited pipe topology differs",
                    )
                    error = float(np.max(abs(points - actual)))
                    small(error, 5.000001e-6, "Inherited pipe world geometry differs")
                    small(
                        error - entry["maximum_world_vertex_errors_m"][name],
                        2e-12,
                        "Inherited pipe geometry error report mismatch",
                    )
                require(
                    not set(names).intersection(raw["candidate_background_names"]), "Inherited pipe was queried again"
                )
        return inherited

    def air_drop(self) -> dict:
        """Reuse the digest-bound completed A/C new-pipe checks without recomputation."""
        row = self.reports["op030_air_drop_ac_v06_completion.json"]
        self.same_path(row["static_native"], self.prepared["static_native"]["path"])
        require(row["static_sha256"] == STATIC_SHA, "Air-drop static mismatch")
        require(
            len(row["reports"]) == 2 and {r["cell"] for r in row["reports"]} == set("AC"),
            "Missing completed air-drop cell",
        )
        for entry in row["reports"]:
            cell = entry["cell"]
            raw_path = "audit/op030_air_drop_" + cell.lower() + "_v06.json"
            self.same_path(entry["report"], raw_path)
            self.pin(raw_path, entry["report_sha256"])
            raw = self.reports[Path(raw_path).name]
            for path, sha in raw["input_digests"].items():
                self.pin(path, sha)
            require(
                raw["input_digests"][self.prepared["banks"][cell]["path"]] == self.prepared["banks"][cell]["sha256"],
                "Air-drop bank mismatch",
            )
            require(row["four_part_world_sha256"] in raw["input_digests"].values(), "Air-drop world mesh mismatch")
            require(entry["frames"] == raw["frames"] == self.bank_counts[cell], "Air-drop full bank coverage mismatch")
            require(raw["bank_frame_range_one_based"] == [1, self.bank_counts[cell]], "Air-drop bank interval mismatch")
            require(entry["inputs_unchanged"] is True and raw["inputs_unchanged"] is True, "Air-drop inputs changed")
            require(
                entry["collision_frames"] == 0 and not raw["results"]["hit_frames"] and not raw["results"]["pairs"],
                "Air-drop collision evidence",
            )
            require(
                entry["minimum_swept_aabb_distance_m"] == raw["minimum_swept_aabb_distance_m"] > 0,
                "Air-drop separation mismatch",
            )
            require(
                entry["candidate_background_names"] == raw["candidate_background_names"] == []
                and raw["contact_exemptions"] == [],
                "Air-drop broad-phase scope mismatch",
            )
        return dict(
            reused_existing_evidence=True, observed_at=row["observed_at"], reports=row["reports"], scope=row["scope"]
        )

    def collect(self) -> dict:
        """Validate all inputs and return a summary without writing any files."""
        missing = [name for name in report_names() if not self.path("audit/" + name).is_file()]
        require(not missing, "Missing required reports; no collection performed:\n" + "\n".join(missing))
        self.reports = {name: self.read("audit/" + name) for name in report_names()}
        self.native = self.reports["op030_split_native_v06.json"]
        self.prepared = self.read(Path(PREPARED).with_suffix(".json"))
        self.pin(PREPARED, PREPARED_SHA)
        require(
            self.prepared["output_sha256"] == self.native["prepared_sha256"] == PREPARED_SHA,
            "Prepared identity mismatch",
        )
        self.same_path(self.native["prepared_motion"], PREPARED)
        require(self.native["output_sha256"] == NATIVE_SHA, "Final native identity mismatch")
        self.pin(self.native["output"], NATIVE_SHA)
        require(self.prepared["b_factory"] == B_FACTORY, "Wrong B factory")
        static = self.prepared["static_native"]
        require(static == self.native["source"] and static["sha256"] == STATIC_SHA, "Static identity mismatch")
        self.pin(static["path"], STATIC_SHA)
        self.pin(static["manifest"], static["manifest_sha256"])
        static_manifest = self.read(static["manifest"])
        require(
            self.native["frames"] == self.prepared["frames"] and self.native["fps"] == self.prepared["fps"],
            "Native schedule mismatch",
        )
        require(self.native["matrix_readback"]["failures"] == [], "Native readback failed")
        require(bool(self.native["matrix_readback"]["frames"]), "Native readback has no samples")
        old = self.read("data/op030_split_animation_v05.json")
        self.pin("data/op030_split_animation_v05.npz", old["output_sha256"])
        for cell, bank in self.prepared["banks"].items():
            self.pin(bank["path"], bank["sha256"])
            require(
                bank == old["banks"][cell] if cell in "AC" else bank["sha256"] == B_SHA != old["banks"][cell]["sha256"],
                "Frozen A/C or final B bank mismatch",
            )
        array_summary = self.arrays()
        plan = self.reports[PREFIX + "_prefill_plan.json"]
        require(
            plan["prepared_sha256"] == PREPARED_SHA
            and plan["prepared_json_sha256"] == self.pin(Path(PREPARED).with_suffix(".json")),
            "Plan prepared mismatch",
        )
        require(plan["source_static"] == static and plan["banks"] == self.prepared["banks"], "Plan source mismatch")
        require(plan["frozen_v05_prepared_sha256"] == old["output_sha256"], "Plan v05 reference mismatch")
        require(
            plan["unchanged_bank_sha256"] == {"A": True, "C": True} and plan["transfer_reuse_claim"] is False,
            "Plan scope mismatch",
        )
        require(
            plan["station_ranges"] == self.prepared["station_ranges"]
            and plan["parallel_operations"] == self.prepared["parallel_operations"],
            "Plan schedule mismatch",
        )
        require(plan["preload_frame_count"] == self.preload, "Plan preload mismatch")
        require(
            set(plan["required_native_checks"]) == {*ROUTES, "prefill", "drawer", "background", *PARKS},
            "Plan native-check scope mismatch",
        )
        mechanical_keys = {
            "product",
            "pallet",
            "drawer_B",
            "op020_carriage",
            "entry_slide_x",
            "lift_A",
            "lift_B",
            "lift_C",
            "stopper_poses",
        }
        require(
            set(plan["mechanical_track_errors"])
            == {row["label"] for row in self.prepared["segments"] if row["kind"] == "transfer"}
            and all(set(row) == mechanical_keys for row in plan["mechanical_track_errors"].values()),
            "Incomplete local mechanical-track plan",
        )
        require(
            set(plan["fixed_height"]) == {"product_z_error_m", "pallet_z_error_m", "product_rotation_error"},
            "Incomplete fixed-height plan",
        )
        small(
            [value for row in plan["mechanical_track_errors"].values() for value in row.values()],
            2e-12,
            "Local mechanical tracks changed",
        )
        small(list(plan["fixed_height"].values()), 2e-12, "Fixed-height plan failed")
        small(plan["b_root"]["baseline_xy_error_m"], 2e-12, "B baseline plan failed")
        small(plan["b_root"]["minimum_root_rotation_determinant"] - 1, 2e-12, "B rotation plan failed")
        require(plan["b_root"]["global_robot_array_present"] is True, "B prepared track absent")
        binding = self.reports[PREFIX + "_entry_binding.json"]
        self.bound(binding)
        require(
            binding["source_static"] == static and set(binding["checks"]) == BINDING_CHECKS, "Binding scope mismatch"
        )
        require(
            binding["failed_checks"] == [] and all(value is True for value in binding["checks"].values()),
            "Native binding checks failed",
        )
        metrics = binding["results"]
        self.pin(metrics["baker_source"], metrics["baker_source_sha256"])
        require(set(metrics["retained_a_c_maximum_pose_errors"]) == set("AC"), "Missing A/C binding metrics")
        small(
            [
                metrics["b_pose_maximum_error"],
                *metrics["retained_a_c_maximum_pose_errors"].values(),
                metrics["drawer_world_minus_x_error_m"],
                metrics["stock_relative_to_drawer_maximum_error"],
                metrics["positive_stagger_parent_determinant_minimum"] - 1,
                metrics["remaining_stock_return_relative_maximum_error"],
                metrics["remaining_stock_prepared_pose_maximum_error"],
                metrics["return_drawer_prepared_pose_maximum_error"],
            ],
            2e-6,
            "Binding numeric checks failed",
        )
        small(
            np.asarray(metrics["drawer_world_displacement_m"]) - [-0.340, 0, 0],
            2e-6,
            "Native drawer world direction mismatch",
        )
        require(
            metrics["stock_uid_count"] == len(set(metrics["ten_stock_uids"])) == 10
            and len(metrics["remaining_stock_after_B"]) == 8,
            "Native stock UID mismatch",
        )
        stock_uids = {row["uid"] for row in static_manifest["wires"]}
        installed_uids = {row["uid"] for row in self.prepared["wires"]}
        require(set(metrics["ten_stock_uids"]) == stock_uids, "Native stock differs from static UID list")
        require(set(metrics["remaining_stock_after_B"]) == stock_uids - installed_uids, "Wrong stock returned after B")
        returned = self.interval("return_remaining_8_during_outfeed")
        require(
            metrics["remaining_stock_return_frames"]
            == list(range(returned["first_frame"], returned["last_frame"] + 1)),
            "Remaining stock return frame coverage mismatch",
        )
        require(
            metrics["drawer_present_frames"] == len(self.frame_ids("drawer")), "Native drawer binding coverage mismatch"
        )
        require(
            metrics["b_pose_sample_frames"] == len(metrics["sampled_global_frames"]) > 0,
            "Native B binding sample count mismatch",
        )
        historical_binding = self.reports[PREFIX + "_entry_binding_parent_assert.json"]
        self.bound(historical_binding)
        require(
            historical_binding["failed_checks"] == ["eight_remaining_uids_parented_to_drawer"]
            and historical_binding["checks"]["eight_remaining_uids_parented_to_drawer"] is False,
            "Historical hierarchy-assertion evidence mismatch",
        )
        exports = {window: self.export(window) for window in (*ROUTES, "prefill", "drawer", "background", *PARKS)}
        transfers = {}
        for route in ROUTES:
            exported = exports[route]
            raw = self.raw_check(route, exported)
            fixtures = self.reports[PREFIX + "_" + route + "_check_fixtures.json"]
            self.same_path(fixtures["source"], exported["mesh"])
            require(
                fixtures["source_sha256"] == exported["report"]["output_sha256"] and fixtures["route"] == route,
                "Fixture source mismatch",
            )
            require(
                fixtures["frames"] == raw["frames"] and set(fixtures["fixtures"]) == set(exported["moving_families"]),
                "Incomplete fixture coverage",
            )
            for fixture in fixtures["fixtures"].values():
                require(
                    fixture["frames"] == raw["frames"]
                    and fixture["hits"] == []
                    and fixture["support_contact_exemptions"] == [],
                    "Moving fixture contact or incomplete report",
                )
            transfers[route] = dict(
                frames=raw["frames"],
                global_frames=[exported["frames"][0], exported["frames"][-1]],
                payload_hit_frames=0,
                fixture_hit_frames={key: 0 for key in fixtures["fixtures"]},
                within_assembly_scope=fixtures["within_assembly_scope"],
            )
        background = exports["background"]["report"]
        identity = background["fixed_source_comparison"]
        self.same_path(identity["source"], static["path"])
        require(
            identity["source_sha256"] == STATIC_SHA
            and identity["fixed_background_reuse"] is True
            and identity["differences"] == [],
            "Fixed background differs from pinned static",
        )
        require(identity["compared_meshes"] == background["meshes"], "Incomplete background source comparison")
        small(identity["maximum_world_vertex_error_m"], 5.000001e-6, "Fixed background source vertex mismatch")
        prefill = self.prefill(
            exports["prefill"], self.raw_check("prefill", exports["prefill"], allow_fixed=True), background
        )
        drawer = self.raw_check("drawer", exports["drawer"])
        waits = {}
        for window, cells in PARKS.items():
            waits[window] = {}
            for cell in cells:
                raw = self.reports[PREFIX + "_" + window + "_" + cell + "_check_wait.json"]
                first = self.preload - 1 if window == "b_final" or (window == "c_loaded" and cell == "A") else 0
                self.station_check(raw, cell, first)
                require(raw["window"] == window, "Park window mismatch")
                self.same_path(raw["parked_export"], exports[window]["mesh"])
                require(
                    raw["parked_export_sha256"] == exports[window]["report"]["output_sha256"], "Park export mismatch"
                )
                require(raw["results"]["hit_frames"] == [] and raw["results"]["pairs"] == [], "Parked-neighbor contact")
                waits[window][cell] = {
                    key: raw[key]
                    for key in (
                        "frames",
                        "bank_frame_range_one_based",
                        "minimum_swept_aabb_distance_m",
                        "candidate_background_names",
                    )
                }
        result = dict(
            observed_at=datetime.now().astimezone().isoformat(),
            basis=(
                "Files read and SHA256-verified saved reports/arrays; existing A/C pipe evidence reused. "
                "No simulation, native export or collision query rerun by this collector."
            ),
            native=dict(path=self.native["output"], sha256=self.native["output_sha256"]),
            prepared=dict(
                path=PREPARED,
                sha256=PREPARED_SHA,
                frames=self.prepared["frames"],
                duration_s=self.prepared["duration_s"],
            ),
            static=static,
            banks=self.prepared["banks"],
            saved_station_array_identity=array_summary,
            transfer_and_drawer_return=transfers,
            initial_drawer_presentation=dict(frames=drawer["frames"], hit_frames=0),
            concurrent_C_prefill=prefill,
            parked_neighbors_against_station_motion=waits,
            station_motion_against_fixed_background=self.background(exports["background"]),
            fixed_background_identity=identity,
            native_prepared_readback=metrics,
            historical_binding_assertion=dict(
                report="audit/" + PREFIX + "_entry_binding_parent_assert.json",
                observed_at=historical_binding["observed_at"],
                failed_checks=historical_binding["failed_checks"],
                disposition=(
                    "Preserved failed hierarchy assertion. Native uses individual world tracks; "
                    "final binding checks exact prepared poses and drawer-relative motion for all return frames. "
                    "Parent names remain descriptive."
                ),
            ),
            reused_A_C_pipe_clearance=self.air_drop(),
            fixed_pair_scope=(
                "Original fixed floor/base and stationary pipe/bracket contacts remain separately recorded "
                "with raw report digests. No new contact acceptance exception."
            ),
            limitations=(
                "Saved-frame matrix and FCL/AABB geometry observations only. No continuous-time collision "
                "guarantee, force, fastening quality, hardware safety or formal physical-validity verdict. "
                "Fixture checks retain their explicitly recorded within-mechanism omissions."
            ),
            added_contact_exemptions=[],
            formal_physical_validity_verdict=None,
        )
        self.pin(Path(__file__))
        for path, pinned in self.inputs.items():
            state = path.stat()
            require(
                (state.st_size, state.st_mtime_ns) == (pinned["size_bytes"], pinned["mtime_ns"]),
                "Input changed during collection: " + str(path),
            )
        result["evidence"] = sorted(self.inputs.values(), key=lambda item: item["path"])
        return result


def markdown(result: dict) -> str:
    """Render concise auxiliary observations with counts derived from validated inputs."""
    rows = []
    for route, row in result["transfer_and_drawer_return"].items():
        label = f"{route} transfer" + (" / drawer return" if route == "b_c" else "")
        rows.append(f"| {label} | {row['frames']:,} frames; payload and fixture hits 0 |")
    prefill = result["concurrent_C_prefill"]
    rows.append(
        f"| Concurrent C prefill | {prefill['frames']:,} frames; moving pairs 0; "
        f"{len(prefill['unchanged_fixed_pairs'])} fixed pairs recorded separately |"
    )
    rows.append(
        f"| Initial B drawer presentation | {result['initial_drawer_presentation']['frames']:,} frames; hits 0 |"
    )
    for window, cells in result["parked_neighbors_against_station_motion"].items():
        for cell, row in cells.items():
            rows.append(f"| {window} against {cell} | {row['frames']:,} frames; hits 0 |")
    for cell, row in result["station_motion_against_fixed_background"].items():
        rows.append(
            f"| {cell} against fixed background | {row['frames']:,} frames; unexpected pairs 0; "
            f"{len(row['original_fixed_installation_pairs'])} original floor pairs separate |"
        )
    return (
        "# OP030 B stagger v06 integration observations\n\n"
        f"Observed: {result['observed_at']}. Native SHA256 `{result['native']['sha256']}`.\n\n"
        f"Prepared timeline: {result['prepared']['frames']:,} frames / {result['prepared']['duration_s']:g} s. "
        "Frozen A/C and final B saved poses match the prepared tracks with the station Y offset applied once.\n\n"
        "| Scope | Saved evidence |\n|---|---|\n" + "\n".join(rows) + "\n\n"
        "Native readback covers B poses, retained A/C poses, proper rotation, world −X drawer travel, "
        "ten presented UIDs and eight returned stock UIDs. Existing full-bank A/C clearance against "
        "the relocated four-part pipe is reused with its original observation timestamps.\n\n"
        + result["fixed_pair_scope"]
        + "\n\n"
        + result["limitations"]
        + "\n\n"
        f"All source digests, exact intervals, fixed-pair records and scope limits: `audit/{PREFIX}_evidence.json`.\n"
    )


def main() -> None:
    """Check the inventory or collect complete evidence without overwriting outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--inventory", action="store_true", help="List required report presence only; never collect or write"
    )
    modes.add_argument("--check_inputs_only", action="store_true", help="Validate all inputs without writing a summary")
    args = parser.parse_args()
    collector = Collector(args.root)
    if args.inventory:
        present = {"audit/" + name: collector.path("audit/" + name).is_file() for name in report_names()}
        print(
            json.dumps(
                dict(
                    observed_at=datetime.now().astimezone().isoformat(),
                    required_reports=present,
                    collection_performed=False,
                ),
                indent=2,
            )
        )
        return
    output = collector.path("audit/" + PREFIX + "_evidence.json")
    note = collector.path("analysis/" + PREFIX + "_evidence.md")
    if not args.check_inputs_only and (output.exists() or note.exists()):
        parser.exit(1, "Output already exists; no files replaced.\n")
    created = []
    try:
        result = collector.collect()
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        rendered = markdown(result)
        if args.check_inputs_only:
            print("V06_INTEGRATION_INPUTS_VERIFIED", result["native"]["sha256"], "no output written")
            return
        for path, contents in ((output, text), (note, rendered)):
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                stream.write(contents)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        for path in created:
            path.unlink(missing_ok=True)
        parser.exit(1, "V06_INTEGRATION_COLLECTION_REJECTED: " + str(error) + "\n")
    print("V06_INTEGRATION_EVIDENCE_COMPLETE", result["native"]["sha256"])


if __name__ == "__main__":
    main()
