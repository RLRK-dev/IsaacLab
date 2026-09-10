# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Keep encoded PNG caches in RAM and package manifests inside the project."""

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native_sha256", required=True)
    args = parser.parse_args()
    assert digest(ROOT / "UR15_JB_OP030_split_v06.blend") == args.native_sha256
    saved = json.loads((ROOT / "audit/op030_v06_render_cache.json").read_text())
    prepared = []
    for view in ("process", "wide"):
        name = f"op030_split_{view}_v06"
        logical = ROOT / "previews" / name
        ram = Path(saved["folders"][name]["ram_cache"])
        assert logical.is_symlink() and logical.resolve() == ram
        manifest_path = ram / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["complete"] and manifest["native_sha256"] == args.native_sha256
        report = json.loads((ROOT / f"audit/UR15_JB_OP030_split_{view}_v06_video.json").read_text())
        assert report["native_sha256"] == args.native_sha256
        assert report["frame_count"] == len(manifest["images"])
        for file, check in report["videos"].items():
            assert check["full_decode_exit_code"] == 0 and not check["full_black_intervals"]
            assert digest(ROOT / file) == check["sha256"]
        local = logical.with_name(logical.name + "_links_ready")
        local.mkdir(exist_ok=False)
        shutil.copy2(manifest_path, local / "manifest.json")
        assert digest(local / "manifest.json") == digest(manifest_path)
        for row in manifest["images"]:
            source = ram / row["file"]
            assert source.is_file()
            (local / row["file"]).symlink_to(source)
        prepared.append((logical, local, ram, manifest))
    records = []
    for logical, local, ram, manifest in prepared:
        logical.unlink()
        local.rename(logical)
        assert (logical / "manifest.json").resolve().is_relative_to(ROOT)
        for row in manifest["images"]:
            assert (logical / row["file"]).resolve() == ram / row["file"]
        records.append(dict(folder=str(logical), ram_cache=str(ram), frames=len(manifest["images"])))
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        native_sha256=args.native_sha256,
        folders=records,
        png_cache_preserved=True,
        manifests_inside_package_root=True,
    )
    (ROOT / "audit/op030_v06_render_cache_finalized.json").write_text(json.dumps(report, indent=2) + "\n")
    print("OP030_V06_RENDER_CACHE_FINALIZED", flush=True)


if __name__ == "__main__":
    main()
