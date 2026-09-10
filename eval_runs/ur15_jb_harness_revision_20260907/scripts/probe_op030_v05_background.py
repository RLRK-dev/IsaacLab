# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Screen new station paths against omitted fixed whole-line background [m, rad, s].

The station audits already cover named context meshes. This helper checks only
fixed native meshes outside that context, including downstream parked robots.
It starts with conservative swept AABBs, then uses the retained FCL delta query
only where those bounds overlap. No installation exceptions are introduced.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import WIRE_RADIUS, pose
from op030_split_ac_meshes import BranchMeshes
from op030_split_b_check import SplitBMeshes
from op030_split_b_v05 import build_sequence
from op030_split_product_delta import DeltaCheck, digest, load, mesh_points
from op030_split_wire_motion import WirePlacementConfig
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]


def subset(data: dict, indices: np.ndarray) -> dict:
    """Select exact original world triangles, preserving their named identities [m]."""
    vertices, faces, vo, mesh_face_offsets = [], [], [0], [0]
    for index in indices:
        v, f = mesh_points(data, int(index))
        vertices.extend(v)
        faces.extend(f)
        vo.append(len(vertices))
        mesh_face_offsets.append(len(faces))
    return dict(
        names=data["names"][indices],
        vertices=np.array(vertices),
        faces=np.array(faces),
        vertex_offsets=np.array(vo),
        face_offsets=np.array(mesh_face_offsets),
    )


class Station:
    """Read source FK and tool/wire geometry from the final station bank [m, rad]."""

    def __init__(self, cell: str, mesh: Path, bank: Path, config: Path | None):
        self.cell, self.mesh_file, self.bank_file = cell, mesh, bank
        self.bank = load(bank)
        self.offset = {"A": 0.0, "B": 2.3, "C": 4.6}[cell]
        if cell == "B":
            config_data = json.loads(config.read_text())
            self.sequence = build_sequence(WirePlacementConfig(**config_data.get("config", config_data)))
            self.screen = SplitBMeshes(self.sequence, mesh)
            wire_actors = [uid + suffix for uid in self.screen.wire_indices for suffix in ("_J1", "_T", "_insulation")]
            self.active = (
                (self.screen.nodes >= 0)
                | np.isin(self.screen.actors, wire_actors)
                | np.array([str(n).startswith("JB_OP020_") for n in self.screen.names])
            )
        else:
            self.screen = BranchMeshes(mesh)
            self.metadata = json.loads(mesh.with_suffix(".json").read_text())
            actors = [self.screen._name(name) for name in self.bank["object_names"]]
            self.active = (
                (self.screen.side >= 0)
                | np.isin(self.screen.actors, actors)
                | np.isin(self.screen.nodes, [576, 577, 578])
            )

    def apply(self, frame: int, *, exact_wire: bool = False) -> np.ndarray:
        """Apply one saved original-FK state and return global rigid matrices [m]."""
        bank, screen = self.bank, self.screen
        values = dict(zip(bank["node_ids"], bank["poses"][frame], strict=True))
        if self.cell == "B":
            if exact_wire:
                screen.set_state(self.sequence.evaluate(float(bank["author_times"][frame])))
            values.update({576: screen.fixed_base, 577: bank["root_poses"][frame], 578: bank["root_poses"][frame]})
            for number, uid in self.sequence.active_uids.items():
                values.update(
                    {
                        uid + "_" + end: bank[f"wire_lug_poses_{number}"][frame, index]
                        for index, end in enumerate(("J1", "T"))
                    }
                )
                if not exact_wire:
                    points = bank[f"wire_points_{number}"][frame]
                    low, high = points.min(0) - WIRE_RADIUS, points.max(0) + WIRE_RADIUS
                    index = screen.wire_indices[uid]
                    screen.centers[index], screen.extents[index] = (low + high) / 2, (high - low) / 2
                values[uid + "_insulation"] = np.eye(4)
            screen.set_poses(values)
        else:
            values.update(zip(bank["object_names"], bank["object_poses"][frame], strict=True))
            screen.set_poses(values)
            for tool in self.metadata["fixed_tools"].values():
                arm = 0 if tool["side"] == "left" else 1
                tcp = bank["tools"][frame, arm] @ np.asarray(tool["flange_to_tcp"])
                spindle = (
                    tcp
                    @ np.asarray(tool["spindle_relative_to_tcp"])
                    @ pose(Rotation.from_euler("z", bank["spindle_angles"][frame, arm]).as_matrix())
                )
                screen.set_poses({tool["spindle"]: spindle})
        world = screen.world.copy()
        world[:, 1, 3] += self.offset
        return world


def background_check(args) -> None:
    """Check each omitted fixed mesh against all supplied native station frames [m, s]."""
    if args.output.exists():
        raise FileExistsError(args.output)
    background = load(args.background)
    metadata = json.loads(args.background_metadata.read_text())
    if digest(args.background) != metadata["output_sha256"]:
        raise ValueError("Fixed background export changed")
    station = Station(args.cell, args.mesh, args.bank, args.config)
    screen, active = station.screen, station.active
    raw_mesh = load(args.mesh)
    initial_world = station.apply(0)
    context_lookup = {str(name): index for index, name in enumerate(screen.names)}
    matching_context, mismatched_context = [], []
    for index, name in enumerate(background["names"]):
        if str(name) not in context_lookup:
            continue
        ci = context_lookup[str(name)]
        original, original_faces = mesh_points(raw_mesh, ci)
        actual, actual_faces = mesh_points(background, index)
        expected = original @ initial_world[ci, :3, :3].T + initial_world[ci, :3, 3]
        if (
            expected.shape == actual.shape
            and np.array_equal(original_faces, actual_faces)
            and np.max(abs(expected - actual), initial=0.0) < 5e-6
        ):
            matching_context.append(str(name))
        else:
            mismatched_context.append(str(name))
    del raw_mesh
    targets = np.flatnonzero(active)
    sweep_low = np.full((len(screen.names), 3), np.inf)
    sweep_high = np.full((len(screen.names), 3), -np.inf)
    for frame in range(len(station.bank["times"])):
        world = station.apply(frame)
        centers = np.einsum("nij,nj->ni", world[:, :3, :3], screen.centers) + world[:, :3, 3]
        extents = np.einsum("nij,nj->ni", abs(world[:, :3, :3]), screen.extents)
        sweep_low = np.minimum(sweep_low, centers - extents)
        sweep_high = np.maximum(sweep_high, centers + extents)
        if frame % 1000 == 0:
            print("V05_BACKGROUND_SWEEP", args.cell, frame, flush=True)
    outside = np.flatnonzero(~np.isin(background["names"], matching_context))
    low, high = [], []
    for index in outside:
        points, _ = mesh_points(background, int(index))
        low.append(points.min(0))
        high.append(points.max(0))
    low, high = np.asarray(low), np.asarray(high)
    separation = np.maximum(sweep_low[targets, None] - high[None], low[None] - sweep_high[targets, None])
    distance = np.linalg.norm(np.maximum(separation, 0), axis=-1)
    candidates = outside[np.any(np.all(separation <= 1e-6, axis=-1), axis=0)]
    results = dict(hit_frames=[], pairs=[], narrow_phase_queries=0)
    if len(candidates):
        delta = subset(background, candidates)
        probe = DeltaCheck(delta, screen, [])
        probe.indices = targets
        for frame, time in enumerate(station.bank["times"]):
            world = station.apply(frame, exact_wire=True)
            probe.sample(frame + 1, float(time), np.eye(4), world)
        results = probe.record()
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        cell=args.cell,
        bank=str(args.bank),
        bank_sha256=digest(args.bank),
        mesh=str(args.mesh),
        mesh_sha256=digest(args.mesh),
        background=str(args.background),
        background_sha256=digest(args.background),
        background_native=metadata["native"],
        background_native_sha256=metadata["native_sha256"],
        frames=len(station.bank["times"]),
        active_meshes=screen.names[targets].tolist(),
        already_in_station_context=matching_context,
        same_name_different_geometry_rechecked=mismatched_context,
        omitted_background_mesh_count=len(outside),
        candidate_background_names=background["names"][candidates].tolist(),
        minimum_swept_aabb_distance_m=float(distance.min(initial=np.inf)),
        results=results,
        contact_exemptions=[],
        scope="New saved station motion versus fixed background omitted from the station mesh context. "
        "Station internals and overlapping A/C preload are checked separately.",
        formal_physical_validity_verdict=None,
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("V05_BACKGROUND_COMPLETE", args.cell, len(outside), len(candidates), len(results["hit_frames"]), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", choices=("A", "B", "C"), required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "audit/op030_split_b_motion_v05.json")
    parser.add_argument(
        "--background", type=Path, default=ROOT / "analysis/op030_v05_integration_background_meshes.npz"
    )
    parser.add_argument(
        "--background_metadata", type=Path, default=ROOT / "audit/op030_v05_integration_background_export.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    background_check(parser.parse_args())
