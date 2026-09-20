# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Preserve the full saved product in lossless grouped arrays [m]."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PINS = {
    "hvjb_photo_model_v03_p03.json.gz": "6687b12ec1b3db24babf75f8fef1b6f6bc123c288b713824b9763d9214553ba6",
    "hvjb_pge_finger_v01_meshes.json.gz": "c9171a968fd38b263099b21627a31fe37cab61a5e98b8d494ea3a38abfef4570",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_of(key):
    if key == "P01":
        return "case"
    if key in ("P16", "P17"):
        return key
    if key.startswith("I"):
        return "inner_housings"
    if key.startswith("W"):
        return "wires"
    return "internals"


def archive_group(rows, name):
    arrays, keys, records = {}, {}, {}
    for feature, row in rows.items():
        meshes = []
        for source in row["meshes"]:
            record = {key: value for key, value in source.items() if key not in ("vertices", "faces")}
            for field, dtype in (("vertices", np.float64), ("faces", np.int64)):
                array = np.asarray(source[field], dtype=dtype)
                identity = field + hashlib.sha256(array.tobytes()).hexdigest()
                if identity not in keys:
                    keys[identity] = "a" + str(len(arrays))
                    arrays[keys[identity]] = array
                record[field + "_array"] = keys[identity]
            meshes.append(record)
        records[feature] = {**{k: v for k, v in row.items() if k != "meshes"}, "meshes": meshes, "archive": name}
    path = DATA / (name + ".npz")
    np.savez_compressed(path, **arrays)
    with np.load(path, allow_pickle=False) as restored:
        for feature, row in rows.items():
            for original, record in zip(row["meshes"], records[feature]["meshes"], strict=True):
                for field in ("vertices", "faces"):
                    assert np.array_equal(restored[record[field + "_array"]], original[field])
    return records, {"file": path.name, "sha256": sha(path), "bytes": path.stat().st_size}


def load_product():
    manifest = json.loads((DATA / "product_manifest.json").read_text())
    banks = {}
    for archive in manifest["archives"]:
        path = DATA / archive["file"]
        assert sha(path) == archive["sha256"]
        with np.load(path, allow_pickle=False) as saved:
            banks[path.stem] = {key: saved[key] for key in saved.files}
    rows = {}
    for key, row in manifest["features"].items():
        meshes = []
        for source in row["meshes"]:
            mesh = {k: v for k, v in source.items() if not k.endswith("_array")}
            mesh.update({field: banks[row["archive"]][source[field + "_array"]] for field in ("vertices", "faces")})
            meshes.append(mesh)
        rows[key] = {**row, "meshes": meshes}
    return rows, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_root", type=Path, required=True)
    args = parser.parse_args()
    assert not (DATA / "product_manifest.json").exists()
    DATA.mkdir(parents=True, exist_ok=True)
    for filename, expected in PINS.items():
        assert sha(args.source_root / "data" / filename) == expected
    source = args.source_root / "data/hvjb_photo_model_v03_p03.json.gz"
    product = json.loads(gzip.decompress(source.read_bytes()))
    features, archives = {}, []
    for name in ("case", "P16", "P17", "inner_housings", "internals", "wires"):
        rows, archive = archive_group({key: row for key, row in product.items() if group_of(key) == name}, name)
        features.update(rows)
        archives.append(archive)
    shutil.copy2(args.source_root / "data/hvjb_pge_finger_v01_meshes.json.gz", DATA)
    manifest = {
        "parent_product": str(source),
        "parent_sha256": sha(source),
        "features": features,
        "archives": archives,
        "feature_count": len(product),
        "mesh_count": sum(len(row["meshes"]) for row in product.values()),
        "lossless_array_readback_equal": True,
        "pge_parent_sha256": PINS["hvjb_pge_finger_v01_meshes.json.gz"],
        "script_sha256": sha(Path(__file__)),
    }
    (DATA / "product_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("LOSSLESS_INPUTS_COMPLETE", len(product), archives, flush=True)


if __name__ == "__main__":
    main()
