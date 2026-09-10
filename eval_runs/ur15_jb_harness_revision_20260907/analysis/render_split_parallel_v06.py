# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render disjoint remaining native ranges with the unchanged saved-frame renderer."""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLENDER = Path("/home/rlrk/.local/opt/blender-4.5.13-linux-x64/blender")
RENDERER = ROOT / "scripts/render_op030_v02.py"
PLAN = ROOT / "data/op030_split_shots_v06.json"
NATIVE = ROOT / "UR15_JB_OP030_split_v06.blend"
AUDIT = ROOT / "audit/op030_v06_render_shards"
PROGRESS = ROOT / "audit/op030_v06_render_parallel_progress.json"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def stamp() -> str:
    return datetime.now().astimezone().isoformat()


def check_images(folder: Path, manifest: dict, expected: list[int], plan: dict, view: str) -> None:
    if [row["frame"] for row in manifest["images"]] != expected:
        raise ValueError(f"Unexpected frame sequence in {folder}")
    for row in manifest["images"]:
        if row["view"] != view or digest(folder / row["file"]) != row["sha256"]:
            raise ValueError(f"Image or view differs in {folder}: {row}")
        camera = "wide"
        if view == "process":
            camera = next(
                shot["camera"] for shot in plan["ranges"] if shot["first_frame"] <= row["frame"] <= shot["last_frame"]
            )
        if row["camera"] != camera:
            raise ValueError(f"Camera differs in {folder}: {row}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native_sha256", required=True)
    parser.add_argument("--prefix_pids", nargs=2, type=int, required=True)
    args = parser.parse_args()
    expected_sha = args.native_sha256
    plan = read(PLAN)
    pins = {str(path.relative_to(ROOT)): digest(path) for path in (NATIVE, PLAN, RENDERER)}
    if pins[str(NATIVE.relative_to(ROOT))] != expected_sha or plan["native_sha256"] != expected_sha:
        raise ValueError("Final native digest differs")
    if plan["frame_end"] != 14062:
        raise ValueError("Unexpected native range")
    deadline = time.monotonic() + 600
    while any(Path(f"/proc/{pid}").exists() for pid in args.prefix_pids):
        if time.monotonic() > deadline:
            raise TimeoutError("Original renderers have not reached their cooperative stop")
        time.sleep(5)
    AUDIT.mkdir(exist_ok=False)
    prefixes, jobs = {}, []
    for view in ("process", "wide"):
        name = f"op030_split_{view}_v06"
        primary = ROOT / "previews" / name
        prefix_path = primary / "manifest.json"
        manifest = read(prefix_path)
        prefix_frames = [row["frame"] for row in manifest["images"]]
        if not prefix_frames or manifest["complete"]:
            raise ValueError("Expected a nonempty intentionally stopped prefix")
        if (
            manifest["native_sha256"] != expected_sha
            or manifest["renderer_sha256"] != pins[str(RENDERER.relative_to(ROOT))]
        ):
            raise ValueError("Prefix input digest differs")
        if not primary.is_symlink() or not (primary / "STOP").is_file():
            raise ValueError("Expected the owned RAM cache and cooperative stop marker")
        check_images(primary, manifest, list(range(1, prefix_frames[-1] + 1, 2)), plan, view)
        log_path = ROOT / "audit" / (name + "_render.log.gz")
        with gzip.open(log_path, "rt") as stream:
            stopped = any("Cooperative render stop requested" in line for line in stream)
        if not stopped or (ROOT / "audit" / (name + "_render_finished")).exists():
            raise ValueError("Original process did not terminate at the requested stop")
        archived = AUDIT / (view + "_prefix_manifest.json")
        archived_log = AUDIT / (view + "_prefix_render.log.gz")
        shutil.copy2(prefix_path, archived)
        shutil.copy2(log_path, archived_log)
        prefixes[view] = dict(
            folder=str(primary),
            manifest=manifest,
            record=dict(
                manifest=str(archived.relative_to(ROOT)),
                manifest_sha256=digest(archived),
                log=str(archived_log.relative_to(ROOT)),
                log_sha256=digest(archived_log),
                frames=len(prefix_frames),
                first=1,
                last=prefix_frames[-1],
                stop_request=(primary / "STOP").read_text(),
                intentional_cooperative_stop=True,
            ),
        )
        remaining = list(range(prefix_frames[-1] + 2, plan["frame_end"] + 1, 2))
        for part in range(3):
            frames = remaining[len(remaining) * part // 3 : len(remaining) * (part + 1) // 3]
            if not frames:
                raise ValueError("No remaining frames for this range")
            shard_name = name + f"_part{part + 1}"
            folder = ROOT / "previews" / shard_name
            ram = primary.resolve().with_name(shard_name)
            ram.mkdir(exist_ok=False)
            folder.symlink_to(ram, target_is_directory=True)
            log_path = ROOT / "audit" / (shard_name + "_render.log.gz")
            command = [
                str(BLENDER),
                "--background",
                "--threads",
                "16",
                "--python-exit-code",
                "1",
                "--python",
                str(RENDERER),
                "--",
                "--blend",
                NATIVE.name,
                "--output_folder",
                shard_name,
                "--views",
                view,
                "--video",
                "--shot_plan",
                PLAN.name,
                "--width",
                "1280" if view == "process" else "960",
                "--samples",
                "16",
                "--engine",
                "CYCLES",
                "--first_frame",
                str(frames[0]),
                "--last_frame",
                str(frames[-1]),
                "--frame_step",
                "2",
            ]
            jobs.append(dict(view=view, folder=folder, frames=frames, log=log_path, command=command))
    public_jobs = []
    for job in jobs:
        log_stream = job["log"].open("xb")
        compressor = subprocess.Popen(["gzip", "-1"], stdin=subprocess.PIPE, stdout=log_stream)
        process = subprocess.Popen(job["command"], stdout=compressor.stdin, stderr=subprocess.STDOUT)
        compressor.stdin.close()
        job.update(process=process, compressor=compressor, log_stream=log_stream)
        public_jobs.append(
            dict(
                view=job["view"],
                folder=str(job["folder"]),
                first=job["frames"][0],
                last=job["frames"][-1],
                expected_frames=len(job["frames"]),
                command=job["command"],
                pid=process.pid,
                log=str(job["log"].relative_to(ROOT)),
            )
        )
        print("RENDER_RANGE_STARTED", job["view"], job["frames"][0], job["frames"][-1], process.pid, flush=True)
    while True:
        observations = []
        for job, public in zip(jobs, public_jobs, strict=True):
            path = job["folder"] / "manifest.json"
            manifest = read(path) if path.is_file() else {"images": [], "complete": False}
            observations.append(
                dict(
                    **public,
                    exit_code=job["process"].poll(),
                    rendered_frames=len(manifest["images"]),
                    complete=manifest["complete"],
                )
            )
        save(PROGRESS, dict(observed_at=stamp(), native_sha256=expected_sha, jobs=observations))
        if all(job["process"].poll() is not None for job in jobs):
            break
        time.sleep(15)
    for job in jobs:
        code = job["process"].wait()
        compressed = job["compressor"].wait()
        job["log_stream"].close()
        if code or compressed:
            raise RuntimeError(f"Range failed: {job['folder']} render={code}, gzip={compressed}")
    if any(digest(ROOT / name) != sha for name, sha in pins.items()):
        raise ValueError("Pinned input changed during rendering")
    results = {}
    for view, prefix in prefixes.items():
        primary = Path(prefix["folder"])
        combined = dict(prefix["manifest"])
        combined["images"] = list(prefix["manifest"]["images"])
        sources = [prefix["record"]]
        for job in (job for job in jobs if job["view"] == view):
            manifest_path = job["folder"] / "manifest.json"
            manifest = read(manifest_path)
            for key in (
                "native_sha256",
                "renderer_sha256",
                "blender_version",
                "native_frame_end",
                "output_fps",
                "settings",
                "shot_plan_sha256",
            ):
                if manifest.get(key) != combined.get(key):
                    raise ValueError(f"Range differs from the original render settings: {key}")
            if not manifest["complete"]:
                raise ValueError("Incomplete render range")
            check_images(job["folder"], manifest, job["frames"], plan, view)
            with gzip.open(job["log"], "rt") as stream:
                if not any("OP030_RENDER_COMPLETE" in line for line in stream):
                    raise ValueError("Missing range completion marker")
            archived = AUDIT / (job["folder"].name + "_manifest.json")
            shutil.copy2(manifest_path, archived)
            sources.append(
                dict(
                    manifest=str(archived.relative_to(ROOT)),
                    manifest_sha256=digest(archived),
                    log=str(job["log"].relative_to(ROOT)),
                    log_sha256=digest(job["log"]),
                    frames=len(job["frames"]),
                    first=job["frames"][0],
                    last=job["frames"][-1],
                    render_exit_code=0,
                    gzip_exit_code=0,
                )
            )
            for row in manifest["images"]:
                target = primary / row["file"]
                if target.exists():
                    raise FileExistsError(f"Overlapping range: {target}")
                os.link(job["folder"] / row["file"], target)
            combined["images"].extend(manifest["images"])
        combined["images"].sort(key=lambda row: row["frame"])
        if [row["frame"] for row in combined["images"]] != list(range(1, plan["frame_end"] + 1, 2)):
            raise ValueError("Combined range has missing or duplicate native frames")
        combined["complete"] = False
        save(primary / "manifest.json", combined)
        (primary / "STOP").unlink()
        # The unchanged renderer validates every PNG SHA and emits its own full-range completion.
        resume = subprocess.run(
            [
                "bash",
                str(ROOT / "analysis/render_split_view_v06.sh"),
                view,
                expected_sha,
            ],
            check=False,
        )
        finished = read(primary / "manifest.json")
        if resume.returncode or not finished["complete"] or len(finished["images"]) != 7031:
            raise RuntimeError(f"Original full-range resume verification failed: {view}")
        if finished["images"] != combined["images"]:
            raise ValueError("Resume unexpectedly changed image records")
        results[view] = dict(
            sources=sources,
            sample_count=7031,
            expected_frame_set=True,
            all_png_sha256_checked=True,
            original_renderer_resume_exit_code=0,
            extra_rendered_frames=0,
            final_manifest=str((primary / "manifest.json").relative_to(ROOT)),
            final_manifest_sha256=digest(primary / "manifest.json"),
        )
        print("FULL_RENDER_RESUME_VERIFIED", view, flush=True)
    save(
        ROOT / "audit/op030_v06_render_parallel_completion.json",
        dict(
            observed_at=stamp(),
            native_sha256=expected_sha,
            input_sha256=pins,
            inputs_unchanged=all(digest(ROOT / name) == sha for name, sha in pins.items()),
            script_sha256=digest(Path(__file__)),
            views=results,
            rendering_settings_changed=False,
            motion_geometry_or_cameras_changed=False,
            formal_physical_validity_verdict=None,
        ),
    )
    print("OP030_V06_PARALLEL_RENDER_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
