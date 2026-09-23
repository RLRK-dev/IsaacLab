# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Copy the H05 comparison assets and extract saved release transforms, without new kinematics."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
PREVIOUS = Path("/home/rlrk/IsaacLab/work/hvjb-contour-grasp-v01-20260920")
REV = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907")
BANK = REV / "data/header_review_v03/motion.npz"
RELEASE = REV / "audit/hvjb_header_release_v01.json"
GLB_PINS = {
    "P16": "577451c02afe65d62ffcd13edd37f7158ac6a8e930c95c5ed1d4607a695719a3",
    "P17": "8c63b5b3e85d18c7e935849b145caecd30c39886dcf5d72fa337495280a1e0bf",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_key(name: str) -> str | None:
    if name.startswith("official_header_"):
        return None
    for side in ("left_left", "left_right"):
        if name.startswith(side) and name.endswith(("contour_pad", "contour_backing", "front_thrust_pad")):
            return "OP020_hand_" + side + "_header_pad"
    return "OP020_hand_" + name


def relative(matrix: np.ndarray, origin: np.ndarray) -> np.ndarray:
    result = matrix.copy()
    result[:3, 3] -= origin
    return result


def extract(feature: str, header_index: int, model: dict, bank: dict, glb: Path) -> dict:
    scene = trimesh.load(glb, force="scene", process=False)
    names = sorted(scene.graph.nodes_geometry)
    assert len(names) == len(scene.geometry) == 19
    samples = model["samples"]
    indices = np.array([row["bank_index"] for row in samples])
    header_positions = bank[f"header_{header_index}_position"][indices]
    origin = header_positions[0]
    assert np.array_equal(header_positions, np.tile(origin, (len(indices), 1)))
    matrices = np.zeros((len(indices), len(names), 4, 4))
    keys = []
    for column, name in enumerate(names):
        graph_matrix, _ = scene.graph[name]
        key = source_key(name)
        keys.append(key)
        if key is None:
            matrices[:, column] = graph_matrix
            continue
        first = relative(bank[key][indices[0]], origin)
        for row, index in enumerate(indices):
            matrices[row, column] = relative(bank[key][index], origin) @ np.linalg.inv(first) @ graph_matrix
    assert np.isfinite(matrices).all()
    file = ROOT / "data" / f"{feature}_saved_release.npz"
    np.savez_compressed(
        file,
        matrices=matrices,
        object_names=np.array(names),
        bank_indices=indices,
        saved_frames=np.array([row["saved_frame"] for row in samples]),
        source_time_s=bank["time_s"][indices],
        source_phase=np.array([row["source_phase"] for row in samples]),
    )
    with np.load(file, allow_pickle=False) as restored:
        assert np.array_equal(matrices, restored["matrices"])
        assert np.array_equal(restored["bank_indices"], indices)
        assert names == restored["object_names"].tolist()
    return {
        "feature": feature,
        "source_origin_m": origin.tolist(),
        "source_header_position_constant": True,
        "source_sample_count": len(samples),
        "source_samples": samples,
        "object_keys": dict(zip(names, keys, strict=True)),
        "meshes": len(names),
        "derived_bank": str(file.relative_to(ROOT)),
        "derived_bank_sha256": sha(file),
        "copied_geometry": str(glb.relative_to(ROOT)),
        "copied_geometry_sha256": sha(glb),
        "basis": "Per-object saved relative transforms; added contour meshes follow their saved pad transform.",
        "physical_acceptance_verdict": None,
    }


def main() -> None:
    assert not (ROOT / "data").exists() and not (ROOT / "sources").exists()
    old = json.loads((PREVIOUS / "output/contour_observations.json").read_text())
    paths = [BANK, RELEASE, PREVIOUS / "output/contour_observations.json", PREVIOUS / "README.md"]
    paths.extend(PREVIOUS / "output/models" / (key + "_contour_comparison.glb") for key in GLB_PINS)
    pins = {str(path): sha(path) for path in paths}
    assert pins[str(BANK)] == "b84b0f77a20cf2dd61c512514f4183c70bd3486e44b5c47dbcc8146b1be1b1e9"
    assert pins[str(RELEASE)] == "02963ae778e91d3aaf45e2b603395672b09fc756388a6dcabfaf72b85790ba14"
    for model in old["models"]:
        file = PREVIOUS / "output" / model["model"]
        assert sha(file) == model["glb_sha256"] == GLB_PINS[model["feature"]]
    (ROOT / "sources").mkdir()
    (ROOT / "data").mkdir()
    for path in paths:
        target = ROOT / "sources" / path.name
        shutil.copy2(path, target)
        assert sha(target) == pins[str(path)]
    with np.load(ROOT / "sources/motion.npz", allow_pickle=False) as source:
        bank = {key: source[key] for key in source.files}
    release = json.loads((ROOT / "sources/hvjb_header_release_v01.json").read_text())
    rows = [
        extract(
            model["feature_id"], i, model, bank, ROOT / "sources" / (model["feature_id"] + "_contour_comparison.glb")
        )
        for i, model in enumerate(release["models"])
    ]
    assert [row["source_sample_count"] for row in rows] == [28, 29]
    assert pins == {str(path): sha(path) for path in paths}
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_sha256": pins,
        "script_sha256": sha(Path(__file__)),
        "originals_unchanged": True,
        "models": rows,
        "new_ik_or_joint_interpolation": False,
        "formal_physical_verdict": None,
    }
    (ROOT / "data/release_identity.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("H05_SAVED_RELEASE_REUSED P16=28 P17=29 objects_each=19 originals_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
