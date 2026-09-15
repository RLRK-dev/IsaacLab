# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package nominal header geometry and source-separated assembly observations."""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import build_hvjb_preassembly_review_v01 as base
import numpy as np
from scipy.spatial import ConvexHull

ROOT = base.ROOT
INPUT = "data/hvjb_header_interface_inputs_v01.json"
MODEL_AUDIT = "audit/hvjb_header_interface_model_v01.json"
EVIDENCE = "data/hvjb_header_evidence_v01.json"
OUTPUT = "data/hvjb_header_interface_review_v01.json"
AUDIT = "audit/hvjb_header_interface_delivery_v01.json"
EVIDENCE_SHA = "8655f7b0959849755a03709aa67379c82e88f623591d881ec7c9b01a74285891"


def prepare() -> tuple[dict, dict]:
    """Verify the pinned source chain and retain all registered photo features."""
    report, audit, evidence = (base.read_json(name) for name in (INPUT, MODEL_AUDIT, EVIDENCE))
    assert base.digest(ROOT / INPUT) == audit["input_sha256"]
    assert base.digest(ROOT / EVIDENCE) == EVIDENCE_SHA
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    report["model_audit"] = audit
    report["source_evidence"] = evidence
    expected = dict(audit["source_sha256_before"])
    expected[audit["native"]] = audit["native_sha256"]
    expected[audit["mesh"]] = audit["mesh_sha256"]
    expected[evidence["source"]["file"]] = evidence["source"]["sha256"]
    expected[EVIDENCE] = EVIDENCE_SHA
    expected[INPUT] = audit["input_sha256"]
    frames = {row["requested_seek_s"]: row for row in evidence["frames"]}
    for frame in evidence["frames"]:
        expected[frame["file"]] = frame["sha256"]
    for row in report["observations"]:
        frame = frames[row["time_s"]]
        row.update({"image": "evidence/" + Path(frame["file"]).name, "source_url": frame["url"]})
    cad = json.loads(gzip.decompress((ROOT / "data/hvjb_photo_cad_v01.json.gz").read_bytes()))
    for row, measured in zip(report["apertures"], audit["nominal_bare_housing_projection"], strict=True):
        assert row["id"] == measured["id"]
        vertices = np.asarray(cad[row["part_number"]]["vertices"])
        outline = vertices[ConvexHull(vertices[:, :2]).vertices, :2]
        row["projection_hull_m"] = outline.tolist()
        row["projection"] = measured
    catalog = base.read_json(base.CATALOG)
    assert base.digest(ROOT / base.CATALOG) == base.PINNED[base.CATALOG]
    report["preserved_catalog"] = {"file": base.CATALOG, "sha256": base.PINNED[base.CATALOG]}
    report["feature_ids"] = [row["id"] for key in base.FEATURE_COLLECTIONS for row in catalog[key]]
    report["registered_feature_counts"] = {key: len(catalog[key]) for key in base.FEATURE_COLLECTIONS}
    assert len(report["feature_ids"]) == len(set(report["feature_ids"])) == 92
    assert {row["id"] for row in report["apertures"]} <= set(report["feature_ids"])
    before = {name: base.digest(ROOT / name) for name in expected}
    assert before == expected, "Source identity mismatch"
    return report, before


def package(directory: Path, report: dict) -> list[dict]:
    """Copy unchanged reference files and the new native into a fresh local package."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    (directory / "documents").mkdir()
    names = {
        INPUT: "inputs.json",
        OUTPUT: "interface_review.json",
        EVIDENCE: "evidence_index.json",
        base.CATALOG: "photo_catalog.json",
        MODEL_AUDIT: "model_audit.json",
        "analysis/hvjb_header_interface_v01.md": "notes.md",
        report["model_audit"]["native"]: report["model_audit"]["native"],
        report["model_audit"]["mesh"]: "model.json.gz",
        "previews/hvjb_header_interface_v01/model.png": "model.png",
    }
    for source in report["sources"]:
        source["local_pdf"] = "documents/" + Path(source["file"]).name
        names[source["file"]] = source["local_pdf"]
    for frame in report["source_evidence"]["frames"]:
        names[frame["file"]] = "evidence/" + Path(frame["file"]).name
    copied = []
    for source, target in names.items():
        shutil.copy2(ROOT / source, directory / target)
        actual = base.digest(directory / target)
        assert actual == base.digest(ROOT / source)
        copied.append({"source": source, "file": target, "sha256": actual})
    template = (ROOT / "scripts/hvjb_header_interface_v01.html").read_text()
    assert template.count("__PAYLOAD__") == 1
    body = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", body))
    (directory / "README.txt").write_text(
        "HVJB 開口・ヘッダー工程 v01\nreview.html をブラウザーで開いてください。\n"
        "TE公称開口幅：3口側23.0/22.8/23.0 mm、2口側22.8/23.0 mmへ修正。\n"
        "元の92特徴・配線台帳を保持。新nativeはv03_p03、元のp02は変更していません。\n"
        "裸ハウジングの公称投影とフィンガを含む実組付けを区別しています。\n"
        "公式作業映像19枚を収録。8場面を解説し、TE記載手順を別欄にしています。\n"
        "下板・ヒューズ板の固定法、実端末の保持位置は未確定。新工程動画は含みません。\n"
    )
    return copied


def main() -> None:
    """Deliver one guarded static revision and its complete source identity record."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_開口ヘッダー照合_v01_20260916")
    )
    directory = parser.parse_args().output_dir
    for path in (ROOT / OUTPUT, ROOT / AUDIT, directory):
        assert not path.exists(), f"Refusing to overwrite {path}"
    report, before = prepare()
    for source in report["sources"]:
        source["local_pdf"] = "documents/" + Path(source["file"]).name
    base.write_new_json(ROOT / OUTPUT, report)
    copied = package(directory, report)
    after = {name: base.digest(ROOT / name) for name in before}
    assert before == after
    audit = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(directory),
        "source_sha256_before": before,
        "source_sha256_after": after,
        "copied_files": copied,
        "review_json_sha256": base.digest(ROOT / OUTPUT),
        "page_sha256": base.digest(directory / "review.html"),
        "photo_features_retained": len(report["feature_ids"]),
        "reference_frames": len(report["source_evidence"]["frames"]),
        "explained_frames": len(report["observations"]),
        "movie_created": False,
        "formal_physical_verdict": None,
    }
    base.write_new_json(ROOT / AUDIT, audit)
    base.write_new_json(directory / "audit.json", audit)
    print(
        "HEADER_INTERFACE_PACKAGED", directory, "features=92 frames=19 explained=8 sources_unchanged=True", flush=True
    )


if __name__ == "__main__":
    main()
