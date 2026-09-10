# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Share actual fixed-shape FK and ten-wire context for the pipe-layout delta [m, rad, s]."""

import json
from datetime import datetime

import numpy as np
from op030_definition import ROOT
from op030_motion import SIDES
from op030_split_b_plan import digest
from op030_split_b_stagger_v06_plan import Candidate
from op030_split_b_v04 import load
from op030_split_wire_motion import WirePlacementConfig
from solve_op030_motion import NODE_IDS, R


def main() -> None:
    """Capture solved constrained states in global B coordinates, without filling free gaps [m]."""
    stem = "op030_split_b_stagger_v06_constraints_10"
    bank = load(ROOT / "analysis" / (stem + ".npz"))
    record = json.loads((ROOT / "audit" / (stem + ".json")).read_text())
    candidate = Candidate(config=WirePlacementConfig(**record["config"]), **record["variant"])
    indices = np.flatnonzero(np.isfinite(bank["joints"]).all(axis=(1, 2)))
    arrays = {key: [] for key in ("poses", "grips", "root_poses", "wire_points", "wire_lugs", "world_bounds")}
    uids = list(candidate.start_state["wires"])
    offset = np.eye(4)
    offset[1, 3] = 2.3
    for count, index in enumerate(indices):
        state = candidate.sequence.evaluate(float(bank["times"][index]))
        capture_poses = {577: state["root"], 578: state["root"]}
        candidate.screen.set_state(state)
        for arm, side in enumerate(SIDES):
            robot, capture = candidate.robots[side]
            robot.base_pose = state["root"] @ R.yoke_base_pose(side)
            robot.update(bank["joints"][index, arm], float(state["grips"][arm]))
            capture_poses.update(capture.poses)
            candidate.screen.set_poses(capture.poses)
        screen = candidate.screen
        centers = np.einsum("nij,nj->ni", screen.world[:, :3, :3], screen.centers) + screen.world[:, :3, 3]
        extents = np.einsum("nij,nj->ni", abs(screen.world[:, :3, :3]), screen.extents)
        arrays["world_bounds"].append(np.stack((centers - extents, centers + extents), axis=1) + (0, 2.3, 0))
        arrays["poses"].append(np.array([offset @ capture_poses[int(node)] for node in NODE_IDS]))
        arrays["grips"].append(state["grips"])
        arrays["root_poses"].append(offset @ state["root"])
        arrays["wire_points"].append(np.array([state["wires"][uid]["shape"].centerline + (0, 2.3, 0) for uid in uids]))
        arrays["wire_lugs"].append(
            np.array([[offset @ state["wires"][uid]["shape"].lug_frames[end] for end in ("J1", "T")] for uid in uids])
        )
        if count % 150 == 0:
            print("STAGGER_CONTEXT", count, len(indices), flush=True)
    arrays = {key: np.asarray(value) for key, value in arrays.items()}
    arrays.update(
        times=bank["times"][indices],
        joints=bank["joints"][indices],
        node_ids=NODE_IDS,
        wire_uids=np.array(uids),
        wire_numbers=np.array([candidate.start_state["wires"][uid]["number"] for uid in uids]),
        mesh_names=candidate.screen.names,
        fixed_base=offset @ candidate.screen.fixed_base,
    )
    path = ROOT / "analysis/op030_split_b_stagger_v06_world_context_10.npz"
    np.savez_compressed(path, **arrays)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        frames=len(indices),
        coordinate_frame="Global B, Y+2.30 applied exactly once",
        scope="All finite constrained q and free endpoints; free interiors are not filled or checked",
        wire_count=len(uids),
        mesh_bounds_count=len(candidate.screen.names),
        source_connection_sha256=digest(ROOT / "analysis" / (stem + ".npz")),
        mesh_sha256=digest(candidate.mesh),
        variant=record["variant"],
        config=record["config"],
        output_sha256=digest(path),
        formal_physical_verdict=None,
    )
    (ROOT / "audit/op030_split_b_stagger_v06_world_context_10.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print("STAGGER_CONTEXT_COMPLETE", len(indices), report["output_sha256"], flush=True)


if __name__ == "__main__":
    main()
