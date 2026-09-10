# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Run the existing isolated Chrome checks for the v05 delivery page [s, px]."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "UR15_JB_OP030_20260910_v05"
PAGE = "review_OP030_split_v05.html"
PLAN = "data/op030_split_shots_v05.json"
HELPERS = {
    "main": ROOT / "analysis/verify_op030_split_page.mjs",
    "details": ROOT / "analysis/verify_op030_split_details_wrapped_width.mjs",
}


def digest(path: Path) -> str:
    """Return one file digest without modifying the input."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path) -> dict:
    """Read one UTF-8 JSON record."""
    return json.loads(path.read_text(encoding="utf-8"))


def plan_check(path: Path) -> dict:
    """Read expected chapter count and encoded duration [s] from the plan."""
    plan = read_json(path)
    phases = plan["phases"]
    if not isinstance(phases, list) or not phases:
        raise ValueError("The presentation has no chapter definitions")
    expected_first = 1
    for phase in phases:
        first, last = phase["first_frame"], phase["last_frame"]
        if first != expected_first or not isinstance(last, int) or last < first or not phase["label"].strip():
            raise ValueError("Presentation phases are not consecutive, labelled frame intervals")
        for field, target in (("start_s", (first - 1) / 30), ("stop_s", last / 30)):
            if not math.isfinite(float(phase[field])) or abs(float(phase[field]) - target) > 1e-6:
                raise ValueError("A chapter time does not match its native 30 Hz frame")
        expected_first = last + 1
    if expected_first != plan["frame_end"] + 1:
        raise ValueError("Chapter definitions do not cover the whole native timeline")
    return {
        "path": str(path),
        "sha256": digest(path),
        "chapter_count": len(phases),
        "native_frames": plan["frame_end"],
        "native_sha256": plan["native_sha256"],
        "expected_encoded_duration_s": math.ceil(plan["frame_end"] / 2) / 15,
    }


def preflight(options: argparse.Namespace) -> dict:
    """Check local executable/helper availability without launching Chrome."""
    node = shutil.which(options.node)
    if node is None:
        raise FileNotFoundError("Node 22 or newer is required for the reused native WebSocket helper")
    version = subprocess.check_output([node, "--version"], text=True).strip()
    if int(version.lstrip("v").split(".")[0]) < 22:
        raise ValueError("The existing browser helper requires Node 22 or newer")
    browser = Path(options.browser).resolve()
    if not browser.is_file():
        raise FileNotFoundError(browser)
    helpers = {}
    for key, helper in HELPERS.items():
        subprocess.run([node, "--check", str(helper)], check=True, capture_output=True, text=True)
        helpers[key] = {"path": str(helper), "sha256": digest(helper)}
    plan_path = options.stage_path / PLAN
    if options.preflight and not plan_path.is_file():
        plan_path = ROOT / PLAN
    return {
        "observed_at": datetime.now().astimezone().isoformat(),
        "status": "runner_preflight_only",
        "browser_checks_executed": False,
        "node": node,
        "node_version": version,
        "browser": str(browser),
        "helpers": helpers,
        "plan": plan_check(plan_path),
        "stage_exists": options.stage_path.is_dir(),
        "page_exists": (options.stage_path / PAGE).is_file(),
        "note": "Executable, helper syntax and plan checks only; no claim about v05 video playback or page layout",
    }


def run_helper(key: str, options: argparse.Namespace, ready: dict) -> dict:
    """Run one unchanged v03 browser helper against explicit v05 inputs."""
    destination = options.output_dir / key
    command = [
        ready["node"],
        str(HELPERS[key]),
        "--stage_path",
        str(options.stage_path),
        "--page_path",
        str(options.stage_path / PAGE),
        "--plan_name",
        PLAN,
        "--chapter_field",
        "phases",
        "--output_dir",
        str(destination),
        "--browser",
        ready["browser"],
        "--timeout_ms",
        str(options.timeout_ms),
        "--label",
        f"OP030_split_v05_delivery_{key}",
    ]
    print(f"BROWSER_CHECK_START {key}", flush=True)
    result = subprocess.run(command, check=False)
    report_path = destination / "page_browser_report.json"
    return {
        "command": command,
        "exit_code": result.returncode,
        "path": str(report_path),
        "sha256": digest(report_path) if report_path.is_file() else None,
        "report": read_json(report_path) if report_path.is_file() else {},
    }


def summarize(ready: dict, results: dict, pinned: dict[str, str], stage_path: Path) -> dict:
    """Summarize real browser observations without accepting incomplete checks."""
    main = results["main"]["report"]
    details = results["details"]["report"]
    expected = ready["plan"]["chapter_count"]
    duration = ready["plan"]["expected_encoded_duration_s"]
    sources = {(stage_path / f"UR15_JB_OP030_split_{view}_v05_review.mp4").as_uri() for view in ("process", "wide")}
    videos = main.get("all_videos", [])
    links = main.get("local_links", [])
    layout = details.get("details_width_states", [])
    checks = {
        "both_helpers_completed": all(
            row["exit_code"] == 0 and row["report"].get("browser_checks_succeeded") for row in results.values()
        ),
        "same_page_in_both_checks": all(
            row["report"].get("page", {}).get("sha256") == pinned[PAGE] for row in results.values()
        ),
        "same_plan_in_main_check": main.get("presentation", {}).get("sha256") == pinned[PLAN],
        "plan_derived_chapter_count": main.get("seek_button_count")
        == main.get("expected_seek_button_count")
        == expected,
        "all_chapter_labels_times_and_seeks": (
            len(main.get("chapter_definitions", [])) == expected
            and all(row["matches"] for row in main["chapter_definitions"])
            and len(main.get("seek_results", [])) == expected
            and all(row["succeeded"] for row in main["seek_results"])
        ),
        "two_expected_video_sources": len(videos) == 2 and {row["source"] for row in videos} == sources,
        "both_video_durations_match_plan": len(videos) == 2
        and all(abs(row["duration_s"] - duration) <= 0.02 for row in videos),
        "both_videos_actually_played": len(main.get("playback_results", [])) == 2
        and all(row["succeeded"] for row in main["playback_results"]),
        "all_links_are_relative_and_resolve": bool(links)
        and all(
            row.get("succeeded") and not urlsplit(row["raw"]).scheme and not row["raw"].startswith(("/", "\\"))
            for row in links
        ),
        "no_javascript_exceptions": all(not row["report"].get("javascript_exceptions") for row in results.values()),
        "all_four_details_width_states": {(row["requested_width_px"], row["details_open"]) for row in layout}
        == {(390, False), (390, True), (1200, False), (1200, True)},
        "no_details_overflow_or_outside_links": bool(layout)
        and all(
            row["details_count"] > 0 and row["horizontal_overflow_px"] <= 1 and not row["overflow_links"]
            for row in layout
        ),
        "owned_browsers_cleaned_up": all(
            row["report"].get("cleanup", {}).get("owned_browser_exited")
            and row["report"]["cleanup"].get("temporary_profile_removed")
            for row in results.values()
        ),
        "page_plan_inventory_videos_unchanged": all(digest(stage_path / name) == sha for name, sha in pinned.items()),
    }
    return {
        "observed_at": datetime.now().astimezone().isoformat(),
        "checks_succeeded": all(checks.values()),
        "checks": checks,
        "runner_sha256": digest(Path(__file__)),
        "preflight": ready,
        "page_plan_inventory_videos_sha256": pinned,
        "reports": {key: {k: v for k, v in value.items() if k != "report"} for key, value in results.items()},
        "chapter_count": expected,
        "successful_chapters": sum(row["succeeded"] for row in main.get("seek_results", [])),
        "played_video_count": sum(row["succeeded"] for row in main.get("playback_results", [])),
        "local_link_count": len(links),
        "successful_links": sum(row.get("succeeded", False) for row in links),
        "javascript_exception_count": sum(
            len(row["report"].get("javascript_exceptions", [])) for row in results.values()
        ),
        "details_width_states": layout,
        "checked_stage_inputs_unchanged": checks["page_plan_inventory_videos_unchanged"],
        "runner_writes_stage_files": False,
        "formal_physical_validity_verdict": None,
        "scope": (
            "Actual isolated Chrome playback/seek/link/layout checks only; "
            "full-video decoding is a separate encoder audit"
        ),
        "media_cancellation_rule": (
            "The reused helper accepts only cancelled Media ERR_ABORTED for a source whose actual playback and all "
            "chapter seeks succeeded; raw events remain in the main report"
        ),
    }


def main() -> None:
    """Run preflight now or full read-only stage verification after encoding."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage_path", type=Path, default=ROOT / "deliverables" / PACKAGE)
    parser.add_argument("--output_dir", type=Path, default=ROOT / "audit/op030_split_page_browser_v05")
    parser.add_argument("--node", default="node")
    parser.add_argument("--browser", default="/opt/google/chrome/chrome")
    parser.add_argument("--timeout_ms", type=int, default=120000)
    parser.add_argument("--preflight", action="store_true", help="Check helpers/plan only; do not launch Chrome")
    parser.add_argument("--preflight_output", type=Path, help="Write the preflight JSON to a new file")
    options = parser.parse_args()
    options.stage_path, options.output_dir = options.stage_path.resolve(), options.output_dir.resolve()
    if not 1000 <= options.timeout_ms <= 180000:
        parser.error("timeout_ms must be between 1000 and 180000 per helper")
    ready = preflight(options)
    if options.preflight:
        if options.preflight_output:
            with options.preflight_output.open("x", encoding="utf-8") as stream:
                json.dump(ready, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        print(json.dumps(ready, ensure_ascii=False, indent=2))
        return
    if options.output_dir.is_relative_to(options.stage_path):
        raise ValueError("Keep browser evidence outside the staged package")
    required = [PAGE, PLAN, "DELIVERY_SHA256.json"]
    required += [f"UR15_JB_OP030_split_{view}_v05_review.mp4" for view in ("process", "wide")]
    for relative in required:
        path = options.stage_path / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Stage is not ready: {path}")
    pinned = {name: digest(options.stage_path / name) for name in required}
    options.output_dir.mkdir(parents=True, exist_ok=False)
    results = {key: run_helper(key, options, ready) for key in ("main", "details")}
    result = summarize(ready, results, pinned, options.stage_path)
    output = options.output_dir / "completion.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "checks_succeeded": result["checks_succeeded"]}), flush=True)
    if not result["checks_succeeded"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
