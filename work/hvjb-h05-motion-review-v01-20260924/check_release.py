# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back saved H05 poses and rendered PNGs; record auxiliary display observations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_model(model: dict, rows: list[dict], source: dict) -> dict:
    with np.load(ROOT / model["derived_bank"], allow_pickle=False) as saved:
        bank = {key: saved[key] for key in saved.files}
    count = model["source_sample_count"]
    assert [row["source_sample_index"] for row in rows] == list(range(count))
    assert [row["saved_frame"] for row in rows] == bank["saved_frames"].tolist()
    assert [row["source_phase"] for row in rows] == bank["source_phase"].tolist()
    assert [row["bank_index"] for row in model["source_samples"]] == bank["bank_indices"].tolist()
    assert np.array_equal(source["time_s"][bank["bank_indices"]], bank["source_time_s"])
    errors = []
    for column, name in enumerate(bank["object_names"]):
        poses = bank["matrices"][:, column]
        key = model["object_keys"][str(name)]
        if key is None:
            assert np.array_equal(poses, np.tile(poses[0], (count, 1, 1)))
            continue
        original = source[key][bank["bank_indices"]].copy()
        original[:, :3, 3] -= model["source_origin_m"]
        # Local model-to-source transform must remain constant over the complete window.
        local = np.linalg.inv(original) @ poses
        error = float(abs(local - local[0]).max())
        assert error < 1e-12, (name, error)
        errors.append(error)
    return {
        "feature": model["feature"],
        "saved_poses": count,
        "mesh_count": len(bank["object_names"]),
        "source_frame_first_last": [int(bank["saved_frames"][0]), int(bank["saved_frames"][-1])],
        "max_local_transform_readback_error": max(errors),
        "header_transform_constant": True,
        "pose_order_and_phases_match_source": True,
    }


def contacts(rows: list[dict], feature: str, output: Path) -> dict:
    sheet = Image.new("RGB", (1920, 1536), "#F2F6F8")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 15)
    for tile, row in enumerate(rows):
        x, y = tile % 5 * 384, tile // 5 * 256
        draw.text(
            (x + 6, y + 5), f"{feature} / frame {row['saved_frame']} / {row['source_phase']}", font=font, fill="#173B4D"
        )
        with Image.open(ROOT / "output/process" / row["file"]) as image:
            sheet.paste(image.resize((384, 216), Image.Resampling.LANCZOS), (x, y + 35))
    file = output / (feature + ".png")
    sheet.save(file)
    return {"file": str(file.relative_to(ROOT)), "sha256": sha(file), "images": len(rows)}


def main() -> None:
    output = ROOT / "audit"
    assert not output.exists()
    identity_path, manifest_path = ROOT / "data/release_identity.json", ROOT / "output/process/manifest.json"
    identity, manifest = json.loads(identity_path.read_text()), json.loads(manifest_path.read_text())
    assert manifest["unique_images"] == len(manifest["images"]) == 57 and not manifest["preview_only"]
    for group in (identity["source_sha256"], manifest["source_sha256"]):
        for path, digest in group.items():
            assert sha(Path(path)) == digest, path
    assert manifest["cameras"]["P16"] == manifest["cameras"]["P17"]
    for row in manifest["images"]:
        file = ROOT / "output/process" / row["file"]
        assert sha(file) == row["sha256"]
        with Image.open(file) as image:
            assert image.size == (1920, 1080)
            image.load()
        assert all(abs(np.asarray(bounds)).max() < 1 for bounds in row["projected_mesh_bounds_normalized"].values())
    with np.load(ROOT / "sources/motion.npz", allow_pickle=False) as saved:
        source = {key: saved[key] for key in saved.files}
    records = []
    output.mkdir()
    (output / "contacts").mkdir()
    sheets = []
    for model in identity["models"]:
        rows = [row for row in manifest["images"] if row["feature"] == model["feature"]]
        records.append(check_model(model, rows, source))
        sheets.append(contacts(rows, model["feature"], output / "contacts"))
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_identity_sha256": sha(identity_path),
        "manifest_sha256": sha(manifest_path),
        "script_sha256": sha(Path(__file__)),
        "readback_pngs": 57,
        "models": records,
        "contact_sheets": sheets,
        "all_source_digests_unchanged": True,
        "fixed_shared_camera_frames": True,
        "scope": "Saved-transform consistency and PNG readback; not grasp, collision, fastener or hardware validation.",
        "physical_acceptance_verdict": None,
    }
    (output / "release_readback.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("H05_RELEASE_READBACK pngs=57 source_poses=P16:28,P17:29 original_digests_unchanged=True", flush=True)
    print(json.dumps(records, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
