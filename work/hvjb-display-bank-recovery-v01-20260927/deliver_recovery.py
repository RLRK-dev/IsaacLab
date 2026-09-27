# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Add the recovered data to the existing review without replacing its files or video."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import recover_bank as recovery

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "hvjb-handoff-trace-v01-20260927/delivery_receipt.json"


def verify_previous(destination: Path, prior: dict) -> None:
    for row in prior["delivered_files"]:
        relative = Path(row["path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        assert recovery.sha(destination / relative) == row["sha256"], relative
    movies = list(destination.rglob("*.mp4"))
    assert len(movies) == 1
    assert recovery.sha(movies[0]) == prior["video_sha256"]


def sources() -> dict[str, Path]:
    paths = {
        "data/source_v05b.npz": ROOT / "recovered/source_v05b.npz",
        "data/panel_v05d.npz": ROOT / "recovered/panel_v05d.npz",
        "audit/recovery.json": ROOT / "recovery.json",
        "audit/render_readback.json": ROOT / "render_readback.json",
        "contact_1.jpg": ROOT / "contact_1.jpg",
        "contact_2.jpg": ROOT / "contact_2.jpg",
        "README.md": ROOT / "README.md",
        "PRIOR_ART_DELTA.md": ROOT / "PRIOR_ART_DELTA.md",
    }
    record = json.loads((ROOT / "render_readback.json").read_text())
    for row in record["images"]:
        source = ROOT / "previews" / row["file"]
        assert recovery.sha(source) == row["sha256"]
        paths["previews/" + row["file"]] = source
    assert recovery.sha(paths["data/source_v05b.npz"]) == recovery.SOURCE_SHA
    restored = json.loads((ROOT / "recovery.json").read_text())
    assert recovery.sha(paths["data/panel_v05d.npz"]) == restored["recovered_stages"][-1]["sha256"]
    return paths


def main() -> None:
    prior = json.loads(PRIOR.read_text())
    destination = Path(prior["entry"]).parent
    output = destination / "replay_data_20260927"
    assert destination.is_dir() and not output.exists()
    verify_previous(destination, prior)
    paths = sources()
    pins = {name: recovery.sha(path) for name, path in paths.items()}
    output.mkdir()
    for name, path in paths.items():
        target = output / name
        target.parent.mkdir(exist_ok=True)
        with path.open("rb") as source, target.open("xb") as sink:
            shutil.copyfileobj(source, sink)
        assert recovery.sha(target) == pins[name]
    verify_previous(destination, prior)
    assert all(recovery.sha(path) == pins[name] for name, path in paths.items())
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(output),
        "script_sha256": recovery.sha(Path(__file__)),
        "prior_receipt_sha256": recovery.sha(PRIOR),
        "existing_files_unchanged": len(prior["delivered_files"]),
        "added_data_files": len(paths),
        "mp4_count": 1,
        "video_sha256": prior["video_sha256"],
        "new_video_created": False,
        "files": [{"path": name, "source": str(paths[name]), "sha256": digest} for name, digest in pins.items()],
    }
    recovery.write(output / "manifest.json", report)
    recovery.write(ROOT / "delivery_receipt.json", report)
    assert recovery.sha(output / "manifest.json") == recovery.sha(ROOT / "delivery_receipt.json")
    print(f"RECOVERY_DELIVERED data_files={len(paths)} existing_unchanged=529 mp4=1", flush=True)


if __name__ == "__main__":
    main()
