# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Resolve the user-selected hand for subsequent static tooling work [m]."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

REVISION = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REVISION / "data/hand_working_default_v01.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_working_default(config: Path = DEFAULT_CONFIG, source_directory: Path | None = None) -> tuple[dict, dict]:
    """Read the selected candidate without altering source geometry [m].

    Args:
        config: Current user decision and pinned artifact identities.
        source_directory: Optional relocated copy of the same pinned inputs.

    Returns:
        Selected payload and the input/provenance record; no physical verdict.
    """
    settings = json.loads(config.read_text())
    source_directory = source_directory or Path(settings["source_directory"])
    paths = {key: source_directory / row["name"] for key, row in settings["source_files"].items()}
    for key, path in paths.items():
        if _sha(path) != settings["source_files"][key]["sha256"]:
            raise ValueError(f"Pinned {key} identity differs: {path}")
    payload = json.loads(paths["mesh"].read_text())
    observed = json.loads(paths["observations"].read_text())
    native = json.loads(paths["native_observations"].read_text())
    name = settings["candidate"]
    candidate = payload["candidates"][name]
    angle = observed["construction"][name]["invariants"]["signed_world_x_rotation_deg"]
    if abs(angle - settings["signed_world_x_rotation_deg"]) > 1e-9:
        raise ValueError("Measured source angle differs from the current default")
    if settings["default_state"] not in candidate["states"]:
        raise ValueError("Default state is not present")
    if native["mesh_counts"][settings["native_scene"]] != 20:
        raise ValueError("Unexpected native scene")
    payload["candidates"] = {name: candidate}
    payload["working_default"] = settings
    payload["config"]["status"] = "User-selected 15-degree working hand; physical conditions remain separate"
    record = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "config_sha256": _sha(config),
        "candidate": name,
        "default_state": settings["default_state"],
        "signed_world_x_rotation_deg": angle,
        "mesh_count_excluding_guide": sum(o["category"] != "guide" for o in candidate["objects"].values()),
        "states": list(candidate["states"]),
        "input_paths": {key: str(path) for key, path in paths.items()},
        "input_sha256": {key: _sha(path) for key, path in paths.items()},
        "source_candidate_objects_and_all_transforms_preserved": True,
        "geometry_rebuilt": False,
        "physical_acceptance_verdict": None,
    }
    return payload, record


def main() -> None:
    """Write only the selected input and its provenance into a new directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source_directory", type=Path)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists():
        raise FileExistsError(args.output_directory)
    payload, record = load_working_default(args.config, args.source_directory)
    args.output_directory.mkdir(parents=True)
    mesh = args.output_directory / "hand_default_meshes_v01.json"
    mesh.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    loaded = json.loads(mesh.read_text())
    assert loaded["candidates"] == payload["candidates"]
    source = Path(record["input_paths"]["mesh"])
    original = json.loads(source.read_text())
    name = record["candidate"]
    assert loaded["candidates"][name] == original["candidates"][name]
    assert _sha(source) == record["input_sha256"]["mesh"]
    record["output_sha256"] = _sha(mesh)
    record["serialized_candidate_readback_identical"] = True
    shutil.copy2(args.config, args.output_directory / "hand_working_default_v01.json")
    (args.output_directory / "hand_working_default_resolution_v01.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps({"candidate": name, "angle_deg": record["signed_world_x_rotation_deg"], "states": record["states"]})
    )
    print("HAND_WORKING_DEFAULT_READY")


if __name__ == "__main__":
    main()
