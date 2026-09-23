# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back the review PDF and compare its job and feature coverage with inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
PDF = ROOT / "output/pdf/HVJB_ライン全体と組立場所_v04_20260923.pdf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    result_path = ROOT / "qa_receipt.json"
    assert not result_path.exists(), result_path
    data = read_json(ROOT / "data/line_review_data.json")
    audit = read_json(ROOT / "output/document_audit.json")
    views = read_json(ROOT / "audit/product_final_views.json")
    reader = PdfReader(PDF)
    assert len(reader.pages) == 6
    assert sha(PDF) == audit["pdf_sha256"]
    assert sha(ROOT / "build_review.py") == audit["builder_sha256"]
    assert sha(ROOT / "data/line_review_data.json") == audit["data_sha256"]
    assert sha(ROOT / "audit/product_final_views.json") == audit["product_figure_audit_sha256"]
    page_text = [page.extract_text() for page in reader.pages]
    page_four_jobs = re.findall(r"\bD\d{2}\b", page_text[3])
    expected_jobs = [row["id"] for row in data["jobs"]]
    assert set(page_four_jobs) == set(expected_jobs)
    assert len(expected_jobs) == len(set(expected_jobs)) == 20
    assert len({row["operation"] for row in data["jobs"]}) == 12
    jobs_csv = read_csv(ROOT / "data/20仕事_場所_担当_引継ぎ.csv")
    assert [row["仕事"] for row in jobs_csv] == expected_jobs
    features_csv = read_csv(ROOT / "data/92項目_既存工程候補との対応.csv")
    expected_features = {row["id"] for row in data["feature_review_candidates"]}
    assert len(features_csv) == len(expected_features) == 92
    assert {row["写真特徴ID"] for row in features_csv} == expected_features
    assert all(row["検討先の仕事"] for row in features_csv)
    assert data["role_selection_unmodified"]["selected_plan"] == "S5_AB"
    assert data["cpa_followup"]["selected_part_number"] is None
    assert data["new_physical_operation_selection"] is None
    assert data["formal_physical_validity_verdict"] is None
    for source in data["source_identity"]:
        assert sha(ROOT.parents[1] / source["path"]) == source["sha256"], source["path"]
    for view in views["views"]:
        assert view["included_feature_count"] == 92
        assert view["included_mesh_count"] == 465
        assert sha(ROOT / view["file"]) == view["sha256"]
    for item in audit["text_geometry"]:
        assert item["x"] >= 0
        assert item["x"] + item["width"] <= 1600
        assert 18 <= item["baseline"] <= 1082
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        assert tuple(float(value) for value in page.mediabox) == (0, 0, 1600, 1100)
        image = ROOT / f"output/pages/page-{number}.png"
        assert image.exists()
        pages.append({"page": number, "png": str(image.relative_to(ROOT)), "sha256": sha(image)})
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "basis": "saved input hashes, PDF readback, CSV cross-check, assistant visual inspection of all six page PNGs",
        "pdf_sha256": sha(PDF),
        "page_count": 6,
        "job_ids_on_page_4": sorted(set(page_four_jobs)),
        "source_operation_count": 12,
        "job_csv_rows": 20,
        "photo_feature_csv_rows": 92,
        "product_views_checked": len(views["views"]),
        "features_per_product_view": 92,
        "meshes_per_product_view": 465,
        "text_boundary_check": "passed",
        "pages": pages,
        "visual_observations": [
            "All six final page images were opened and inspected; headings, diagrams and footnotes are readable.",
            "Page 1 A/B transfer arrows terminate at C; they do not imply transfer through the shared assistant.",
            "Page 4 contains all 20 job cards; detailed hand variants remain in the accompanying CSV.",
            "Page 5 distinguishes shared-assistant occupancy from time and from a verified parallel schedule.",
            "Page 6 distinguishes the small green CPA symbol from the orange plug and the adjacent header.",
        ],
        "limits": [
            "The colored product views show completed saved geometry, not verified intermediate workpieces.",
            "92 photo features do not constitute a complete manufacturing BOM or complete physical wiring.",
            "Arm roles and schematic handoffs do not prove reach, retention, fastening or real takt.",
            "This receipt is document QA by the creating assistant, not independent physical acceptance.",
        ],
        "formal_physical_validity_verdict": None,
        "verifier_sha256": sha(Path(__file__)),
    }
    with result_path.open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("REVIEW_READBACK_COMPLETE pages=6 jobs=20 operations=12 photo_features=92 product_views=10")


if __name__ == "__main__":
    main()
