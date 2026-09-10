# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode only complete v06 renders matching an explicit final native digest."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native_sha256", required=True)
    args = parser.parse_args()
    plan_path = ROOT / "data/op030_split_shots_v06.json"
    plan = json.loads(plan_path.read_text())
    plan_sha = digest(plan_path)
    expected = args.native_sha256
    if plan["native_sha256"] != expected or digest(ROOT / plan["native"]) != expected:
        raise ValueError("Plan and explicit final native digest differ")
    pending = {"process", "wide"}
    while pending:
        if (ROOT / "analysis/STOP_split_encode_v06").exists():
            raise SystemExit("Cooperative encoder stop requested")
        for view in sorted(pending):
            folder = "op030_split_" + view + "_v06"
            finished = ROOT / "audit" / (folder + "_render_finished")
            if not finished.is_file() or finished.read_text().strip() != expected:
                continue
            path = ROOT / "previews" / folder / "manifest.json"
            manifest = json.loads(path.read_text())
            if not manifest["complete"]:
                continue
            if manifest["native_sha256"] != expected:
                raise ValueError("Final native changed before encode")
            if [row["frame"] for row in manifest["images"]] != list(range(1, plan["frame_end"] + 1, 2)):
                raise ValueError("Completed render does not cover all native samples")
            if digest(ROOT / plan["native"]) != expected or digest(plan_path) != plan_sha:
                raise ValueError("Pinned inputs changed before encode")
            stem = "UR15_JB_OP030_split_" + view + "_v06"
            log = ROOT / "audit" / (stem + "_encode.log")
            command = [
                str(REPO / "isaaclab.sh"),
                "-p",
                str(ROOT / "scripts/encode_op030_v02.py"),
                "--folders",
                folder,
                "--view",
                view,
                "--plan",
                plan_path.name,
                "--basename",
                stem,
            ]
            print("SPLIT_ENCODE_START", view, flush=True)
            with log.open("w") as stream:
                result = subprocess.run(command, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT, check=False)
            if result.returncode or "OP030_VIDEO_ENCODED " + stem not in log.read_text():
                raise RuntimeError("Encode failed; inspect " + str(log))
            print("SPLIT_ENCODE_COMPLETE", view, flush=True)
            pending.remove(view)
        if pending:
            time.sleep(15)
    print("SPLIT_BOTH_VIDEOS_ENCODED_V06", flush=True)


if __name__ == "__main__":
    main()
