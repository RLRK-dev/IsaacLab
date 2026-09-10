# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check saved v06 station paths against actual fixed/parked line geometry [m, s].

Reuse the existing Station application and DeltaCheck triangle query, with an
explicit v06 B factory. Same-name meshes are skipped only when their evaluated
world triangles match. Thus an old B placement cannot disappear through naming.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_split_b_check import SplitBMeshes
from op030_split_product_delta import DeltaCheck, digest, load, mesh_points
from op030_split_wire_motion import WirePlacementConfig
from probe_op030_stagger_integration_v06 import read_prepared
from probe_op030_v05_background import Station, subset
from probe_op030_v05_integration import absolute, write

ROOT = Path(__file__).resolve().parents[1]


class StationV06(Station):
    """Apply frozen A/C or the explicitly selected staggered B bank [m, rad]."""

    def __init__(self, cell: str, mesh: Path, bank: Path, config: Path | None):
        if cell != "B":
            super().__init__(cell, mesh, bank, config)
            return
        from op030_split_b_stagger_v06 import build_sequence_final

        self.cell, self.mesh_file, self.bank_file = cell, mesh, bank
        self.bank, self.offset = load(bank), 2.3
        config_data = json.loads(config.read_text())
        self.sequence = build_sequence_final(WirePlacementConfig(**config_data.get("config", config_data)))
        if abs(float(self.bank["author_times"][-1]) - self.sequence.time) > 1e-6:
            raise ValueError("B bank author time does not match the final stagger factory")
        self.screen = SplitBMeshes(self.sequence, mesh)
        wire_actors = [uid + suffix for uid in self.screen.wire_indices for suffix in ("_J1", "_T", "_insulation")]
        self.active = (
            (self.screen.nodes >= 0)
            | np.isin(self.screen.actors, wire_actors)
            | np.array([str(name).startswith("JB_OP020_") for name in self.screen.names])
        )
        if np.max(abs(self.screen.fixed_base[:2, 3] - [0.9, -1.7])) > 1e-6:
            raise ValueError("B checker geometry has the old base or a duplicated world Y offset")


def screen_world(station: StationV06, world_data: dict, frames: range, *, skip_equal_context: bool) -> dict:
    """Screen conservative swept bounds then exact native triangles at saved times [m, s]."""
    screen, targets = station.screen, np.flatnonzero(station.active)
    initial_world = station.apply(frames.start)
    matching, mismatched = [], []
    if skip_equal_context:
        raw_mesh = load(station.mesh_file)
        lookup = {str(name): index for index, name in enumerate(screen.names)}
        for index, name in enumerate(world_data["names"]):
            if str(name) not in lookup:
                continue
            ci = lookup[str(name)]
            points, triangles = mesh_points(raw_mesh, ci)
            actual, actual_faces = mesh_points(world_data, index)
            expected = points @ initial_world[ci, :3, :3].T + initial_world[ci, :3, 3]
            equal = (
                expected.shape == actual.shape
                and np.array_equal(triangles, actual_faces)
                and np.max(abs(expected - actual), initial=0.0) < 5e-6
            )
            (matching if equal else mismatched).append(str(name))
        del raw_mesh
    outside = np.flatnonzero(~np.isin(world_data["names"], matching))
    sweep_low, sweep_high = np.full((len(targets), 3), np.inf), np.full((len(targets), 3), -np.inf)
    for frame in frames:
        world = station.apply(frame)[targets]
        centers = np.einsum("nij,nj->ni", world[:, :3, :3], screen.centers[targets]) + world[:, :3, 3]
        extents = np.einsum("nij,nj->ni", abs(world[:, :3, :3]), screen.extents[targets])
        sweep_low, sweep_high = np.minimum(sweep_low, centers - extents), np.maximum(sweep_high, centers + extents)
        if (frame - frames.start) % 1000 == 0:
            print("V06_WORLD_SWEEP", station.cell, frame, frames.stop, flush=True)
    low, high = [], []
    for index in outside:
        points, _ = mesh_points(world_data, int(index))
        low.append(points.min(0))
        high.append(points.max(0))
    low, high = np.asarray(low), np.asarray(high)
    if len(outside):
        separation = np.maximum(sweep_low[:, None] - high[None], low[None] - sweep_high[:, None])
        distance = np.linalg.norm(np.maximum(separation, 0), axis=-1)
        candidates = outside[np.any(np.all(separation <= 1e-6, axis=-1), axis=0)]
    else:
        distance, candidates = np.array([np.inf]), np.array([], dtype=int)
    results = dict(hit_frames=[], pairs=[], narrow_phase_queries=0)
    if len(candidates):
        probe = DeltaCheck(subset(world_data, candidates), screen, [])
        probe.indices = targets
        for frame in frames:
            world = station.apply(frame, exact_wire=True)
            probe.sample(frame + 1, float(station.bank["times"][frame]), np.eye(4), world)
        results = probe.record()
    return dict(
        frames=len(frames),
        bank_frame_range_one_based=[frames.start + 1, frames.stop],
        active_meshes=screen.names[targets].tolist(),
        already_in_station_context=matching,
        same_name_different_geometry_rechecked=mismatched,
        outside_mesh_count=len(outside),
        candidate_background_names=world_data["names"][candidates].tolist(),
        minimum_swept_aabb_distance_m=float(distance.min(initial=np.inf)),
        results=results,
        contact_exemptions=[],
    )


def waiting_check(args) -> None:
    """Check the actual parked neighbor over the contemporaneous station bank [m, s]."""
    metadata, banks = read_prepared(args.prepared)
    waiting = load(args.data)
    exported = json.loads(args.metadata.read_text())
    if digest(args.data) != exported["output_sha256"] or exported["prepared_sha256"] != digest(args.prepared):
        raise ValueError("Parked export is not bound to this prepared timeline")
    bank = absolute(metadata["banks"][args.cell]["path"])
    station = StationV06(args.cell, args.mesh, bank, args.config)
    first = 0
    if args.window == "b_initial":
        if args.cell != "A":
            raise ValueError("Initial B park belongs to A work")
        scope = (
            "B parked robot and fully presented ten-wire drawer versus all A frames. "
            "Earlier drawer positions are checked by the separate native drawer overlap."
        )
    elif args.window == "b_final":
        if args.cell != "C":
            raise ValueError("Final B park belongs to C main work")
        first = int(banks["C"]["preload_frame_count"]) - 1
        scope = (
            "B final parked robot and returned eight-wire stock versus C main work. "
            "C prefill occurs earlier and has its own concurrent native check."
        )
    elif args.window == "c_loaded":
        if args.cell == "C":
            raise ValueError("C cannot be checked against its own parked export")
        if args.cell == "A":
            first = int(banks["C"]["preload_frame_count"]) - 1
        scope = "Loaded C tools/UIDs and feeder stock versus A/B after C prefill completion."
    else:
        raise ValueError(args.window)
    result = screen_world(station, waiting, range(first, len(station.bank["times"])), skip_equal_context=False)
    write(
        args.report,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            cell=args.cell,
            window=args.window,
            bank=str(bank),
            bank_sha256=digest(bank),
            mesh=str(args.mesh),
            mesh_sha256=digest(args.mesh),
            parked_export=str(args.data),
            parked_export_sha256=digest(args.data),
            native=exported["native"],
            native_sha256=exported["native_sha256"],
            prepared_sha256=digest(args.prepared),
            scope=scope,
            **result,
            formal_physical_validity_verdict=None,
        ),
    )
    print(
        "V06_WAIT_COMPLETE", args.window, args.cell, result["frames"], len(result["results"]["hit_frames"]), flush=True
    )


def background_check(args) -> None:
    """Check omitted or changed fixed native geometry against complete station motion [m, s]."""
    data = load(args.background)
    metadata = json.loads(args.background_metadata.read_text())
    if digest(args.background) != metadata["output_sha256"]:
        raise ValueError("Background export digest changed")
    station = StationV06(args.cell, args.mesh, args.bank, args.config)
    result = screen_world(station, data, range(len(station.bank["times"])), skip_equal_context=True)
    write(
        args.output,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            cell=args.cell,
            bank=str(args.bank),
            bank_sha256=digest(args.bank),
            mesh=str(args.mesh),
            mesh_sha256=digest(args.mesh),
            background=str(args.background),
            background_sha256=digest(args.background),
            native=metadata["native"],
            native_sha256=metadata["native_sha256"],
            prepared_sha256=metadata["prepared_sha256"],
            **result,
            scope=(
                "Saved station motion versus actual fixed native geometry outside its equal-triangle context. "
                "Parked B/C and concurrent prefill/drawer are checked separately."
            ),
            formal_physical_validity_verdict=None,
        ),
    )
    print("V06_BACKGROUND_COMPLETE", args.cell, result["frames"], len(result["results"]["hit_frames"]), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", choices=("A", "B", "C"), required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "audit/op030_split_b_stagger_motion_v06.json")
    parser.add_argument(
        "--background", type=Path, default=ROOT / "analysis/op030_stagger_v06_integration_background_meshes.npz"
    )
    parser.add_argument(
        "--background_metadata", type=Path, default=ROOT / "audit/op030_stagger_v06_integration_background_export.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    background_check(parser.parse_args())
