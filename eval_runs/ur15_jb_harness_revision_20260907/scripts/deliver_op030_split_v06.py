# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Deliver a new v06 directory and verify every archive entry before publishing."""

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "UR15_JB_OP030_20260910_v06"
PAGE = "review_OP030_split_v06.html"
INVENTORY = "DELIVERY_SHA256.json"
NATIVE = "UR15_JB_OP030_split_v06.blend"


def digest(path: Path) -> str:
    """Return a file's SHA-256."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_directory(folder: Path) -> dict:
    """Check exact relative paths, sizes and hashes, including nested inventories."""
    inventory = json.loads((folder / INVENTORY).read_text())
    actual = {path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()}
    if actual != set(inventory) | {INVENTORY}:
        raise ValueError("Inventory and actual relative file names differ")
    for name, record in inventory.items():
        path = folder / name
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError(f"Path escapes package: {name}")
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            raise ValueError(f"File size or SHA differs: {name}")
    return inventory


def main() -> None:
    """Copy an explicitly pinned, browser-verified stage to Downloads."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--native_sha256", required=True)
    parser.add_argument(
        "--browser_report", type=Path, default=ROOT / "audit/op030_split_page_browser_v06/completion.json"
    )
    args = parser.parse_args()
    stage = ROOT / "deliverables" / PACKAGE
    browser = json.loads(args.browser_report.read_text())
    if browser["checks_succeeded"] is not True or not all(value is True for value in browser["checks"].values()):
        raise ValueError("Browser playback, chapters, links or layout checks failed")
    for name in ("main", "details"):
        report = browser["reports"][name]
        if report["exit_code"] != 0 or digest(Path(report["path"])) != report["sha256"]:
            raise ValueError(f"Browser component evidence differs: {name}")
    for name, expected in browser["page_plan_inventory_videos_sha256"].items():
        if digest(stage / name) != expected:
            raise ValueError(f"Browser evidence differs from the final stage: {name}")
    inventory = verify_directory(stage)
    if inventory[NATIVE]["sha256"] != args.native_sha256:
        raise ValueError("Stage differs from the explicit final native digest")
    destination = Path("/home/rlrk/Downloads") / PACKAGE
    archive = destination.with_suffix(".zip")
    pending = destination.with_name("." + PACKAGE + "_copying")
    pending_archive = archive.with_name("." + archive.name + "_creating")
    if any(path.exists() for path in (destination, archive, pending, pending_archive)):
        raise FileExistsError("Keep existing deliveries and partial copies unchanged")
    total_bytes = sum(record["bytes"] for record in inventory.values()) + (stage / INVENTORY).stat().st_size
    if shutil.disk_usage(destination.parent).free < 2 * total_bytes + 512 * 1024**2:
        raise OSError("Insufficient space for the verified copy, archive and reserve")
    shutil.copytree(stage, pending)
    if verify_directory(pending) != inventory or digest(pending / INVENTORY) != digest(stage / INVENTORY):
        raise ValueError("Copied inventory differs")
    pending.rename(destination)
    print("SPLIT_V06_DIRECTORY_COPIED", destination, flush=True)
    with zipfile.ZipFile(pending_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=4) as bundle:
        for name in sorted((*inventory, INVENTORY)):
            bundle.write(destination / name, f"{PACKAGE}/{name}")
    hashes = {name: record["sha256"] for name, record in inventory.items()}
    hashes[INVENTORY] = digest(destination / INVENTORY)
    with zipfile.ZipFile(pending_archive) as bundle:
        expected_names = {f"{PACKAGE}/{name}" for name in hashes}
        if len(bundle.namelist()) != len(expected_names) or set(bundle.namelist()) != expected_names:
            raise ValueError("ZIP relative names differ")
        if bundle.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
        for name, expected_sha in hashes.items():
            with bundle.open(f"{PACKAGE}/{name}") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != expected_sha:
                    raise ValueError(f"ZIP entry SHA differs: {name}")
    pending_archive.rename(archive)
    previous = {}
    previous_native = "UR15_JB_OP030_20260910_v05/UR15_JB_OP030_split_v05.blend"
    for name, expected in {
        "UR15_JB_OP030_20260910_v05.zip": "ee592e8c33faf3c596259419c48127c36cf3c5ee4311b61a49789241ef49eb87",
        previous_native: "985c7edf11a80f0e1e15ba5176b3040b9d733c30315ae6b732b4c359239afc3d",
    }.items():
        path = destination.parent / name
        actual = digest(path) if path.is_file() else None
        previous[name] = dict(sha256=actual, matches_prior=actual == expected)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        directory=str(destination),
        archive=str(archive),
        archive_sha256=digest(archive),
        archive_bytes=archive.stat().st_size,
        native_sha256=args.native_sha256,
        inventory_sha256=digest(destination / INVENTORY),
        files=len(inventory) + 1,
        file_bytes=total_bytes,
        checks=dict(
            directory_names=True, directory_sha256=True, archive_names=True, archive_crc=True, archive_entry_sha256=True
        ),
        browser=dict(
            path=str(args.browser_report),
            sha256=digest(args.browser_report),
            page_sha256=browser["page_plan_inventory_videos_sha256"][PAGE],
            passed=True,
        ),
        previous_delivery_observation=previous,
        formal_physical_validity_verdict=None,
    )
    (ROOT / "audit/op030_split_delivery_v06.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP030_SPLIT_DELIVERY_V06_COMPLETE", archive, report["archive_sha256"], flush=True)


if __name__ == "__main__":
    main()
