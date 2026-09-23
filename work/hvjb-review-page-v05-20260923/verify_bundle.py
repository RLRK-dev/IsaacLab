# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Read back the offline v05 package and its unchanged job/feature relationships."""

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "hvjb-review-page-v04-20260923/verify_page.py"
spec = importlib.util.spec_from_file_location("original_page_verifier", ORIGINAL)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def main():
    output = ROOT / "qa_receipt.json"
    assert not output.exists()
    folder = ROOT / "output"
    manifest = json.loads((folder / "review_manifest.json").read_text())
    verify.check_files(folder, manifest)
    page = verify.PageReader()
    page.feed((folder / "index.html").read_text())
    payload = json.loads(page.payload)
    counts = verify.check_records(payload)
    external = verify.check_links(folder, page, payload)
    previous = verify.PageReader()
    previous.feed((ROOT.parent / "hvjb-parallel-roles-v01-20260923/entry/index_v04_2.html").read_text())
    assert payload == json.loads(previous.payload)
    htmls, links = [], 0
    for path in folder.rglob("*.html"):
        parsed = verify.PageReader()
        parsed.feed(path.read_text())
        htmls.append(str(path.relative_to(folder)))
        for link in parsed.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                assert url.scheme == "https", link
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
            assert target.is_relative_to(folder.resolve()) and target.is_file(), (path, link)
            links += 1
    document = json.loads((folder / "delivery_manifest.json").read_text())
    for row in document["files"]:
        assert verify.sha(folder / row["path"]) == row["sha256"]
    mp4s = [str(path.relative_to(folder)) for path in folder.rglob("*.mp4")]
    assert mp4s == manifest["mp4_files"] and len(mp4s) == 1
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": verify.sha(folder / "review_manifest.json"),
        "counts": counts,
        "files_read_back": len(manifest["files"]) + 1,
        "inherited_document_files_unchanged": len(document["files"]),
        "job_feature_scene_payload_unchanged": True,
        "html_files_checked": htmls,
        "static_local_links_checked": links,
        "mp4_files": mp4s,
        "external_links_on_entry": external,
        "browser_ui_observed": False,
        "browser_limit": "CUA apps and browsers inventory was empty; these checks inspect files and links.",
        "formal_physical_validity_verdict": None,
        "script_sha256": verify.sha(Path(__file__)),
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"V05_PACKAGE_READBACK files={result['files_read_back']} html={len(htmls)} links={links} mp4=1")


if __name__ == "__main__":
    main()
