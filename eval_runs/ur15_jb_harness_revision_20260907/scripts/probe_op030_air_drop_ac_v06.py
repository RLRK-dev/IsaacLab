# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check frozen A/C banks against the four relocated air-drop surfaces [m, s].

Reuse the saved-pose Station and world-triangle delta check. The concrete delta
from the blocked original pipe is global Y -0.78 m; no arm trajectory, primitive
shape, or contact exemption changes. This is an auxiliary geometry observation.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from op030_split_product_delta import digest, load
from probe_op030_stagger_background_v06 import screen_world
from probe_op030_v05_background import Station

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "A": {
        "bank": "data/op030_split_a_motion_v05.npz",
        "bank_sha256": "e56b610e5ee4642b16c03f7fb321936e3d1d11183218fe3fd0dbd3851dcc6c96",
        "mesh": "data/op030_split_a_final_supported_v04_meshes.npz",
        "mesh_sha256": "4c11e13e1c14a11a4c2a3312a94830d98a74142926cf54c1dc06c533704aa180",
    },
    "C": {
        "bank": "data/op030_split_c_front_indexed_motion_v05.npz",
        "bank_sha256": "238c6b233871f25c0e95113b0d4d92124a569218ab8a40926773637e1ad96e38",
        "mesh": "data/op030_split_c_front_feeders_v05_meshes.npz",
        "mesh_sha256": "df89d0f56d0190d4abb35de251f172d0b817d0bca25a770211c36e05ea0982ac",
    },
}


def check(cell: str) -> dict:
    """Compare every saved station frame with the fixed four-part delta [m, s].

    Args:
        cell: Frozen station identifier, A or C.

    Returns:
        Input digests, checked frame interval, conservative swept separation
        [m], any exact triangle intersections, and the auxiliary scope.
    """
    spec = INPUTS[cell]
    bank, mesh = (ROOT / spec[key] for key in ("bank", "mesh"))
    for key, path in (("bank", bank), ("mesh", mesh)):
        if digest(path) != spec[key + "_sha256"]:
            raise ValueError(f"Frozen {cell} {key} changed")
    geometry_path = ROOT / "audit/op030_stagger_air_clearance_static_v06_geometry.json"
    completion_path = ROOT / "audit/op030_stagger_air_clearance_static_v06_completion.json"
    geometry = json.loads(geometry_path.read_text())
    completion = json.loads(completion_path.read_text())
    world_path = ROOT / geometry["meshes"]
    native_path = ROOT / completion["native"]
    pinned = {path: digest(path) for path in (bank, mesh, geometry_path, completion_path, world_path, native_path)}
    if pinned[world_path] != geometry["meshes_sha256"] or pinned[native_path] != completion["native_sha256"]:
        raise ValueError("Air-drop native/export digest mismatch")
    world = load(world_path)
    if set(world["names"].tolist()) != set(completion["moved_objects"]):
        raise ValueError("World delta must contain exactly the four relocated air-drop objects")
    station = Station(cell, mesh, bank, None)
    result = screen_world(station, world, range(len(station.bank["times"])), skip_equal_context=False)
    drift = [str(path) for path, sha in pinned.items() if digest(path) != sha]
    if drift:
        raise ValueError(f"Inputs changed during the saved-pose check: {drift}")
    return {
        "observed_at": datetime.now().astimezone().isoformat(),
        "cell": cell,
        "input_digests": {str(path.relative_to(ROOT)): sha for path, sha in pinned.items()},
        "global_station_offset_y_m": station.offset,
        "air_drop_displacement_global_m": completion["displacement_global_m"],
        "prior_art": {
            "report": "audit/op030_air_drop_ac_prior_art_v06.log",
            "findings": 30,
            "blockers": 2,
            "concrete_delta": "The original pipe-hit context is retained; test only the new Y -0.78 m pipe delta.",
        },
        **result,
        "inputs_unchanged": True,
        "scope": (
            "All saved A/C motion states, moving robot/tool/camera and bank-object surfaces, "
            "against the new four-part fixed pipe. Static installation contacts and B motion "
            "have separate reports. No new kinematics or contact exceptions are introduced."
        ),
        "formal_physical_validity_verdict": None,
    }


def main() -> None:
    """Write one new station-specific audit without overwriting prior evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", choices=tuple(INPUTS), required=True)
    args = parser.parse_args()
    output = ROOT / f"audit/op030_air_drop_{args.cell.lower()}_v06.json"
    if output.exists():
        raise FileExistsError(output)
    result = check(args.cell)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        "AIR_DROP_AC_COMPLETE",
        args.cell,
        result["frames"],
        len(result["results"]["hit_frames"]),
        result["minimum_swept_aabb_distance_m"],
        flush=True,
    )
    if result["results"]["hit_frames"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
