# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build a static contact-concept index from the preserved requirements and jobs."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def read(path: Path):
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def sources_unchanged() -> dict:
    identity = read(ROOT / "source_identity.json")
    for row in identity["files"]:
        assert sha(ROOT / row["copy"]) == row["sha256"], row["copy"]
    return identity


def collect_data() -> dict:
    requirements = read(ROOT / "sources/requirements.json")
    hand_plan = read(ROOT / "sources/hand_plan.json")
    line = read(ROOT / "sources/line_review_data.json")
    default = read(ROOT / "sources/working_default.json")
    variants = read(ROOT / "variants.json")
    family_map = {row["id"]: row for row in requirements["families"]}
    cards = {row["id"]: row for row in hand_plan["cards"]}
    jobs = []
    for row in line["jobs"]:
        item = dict(row)
        item["families"] = cards[row["id"]]["hand_families"]
        item["variants"] = [variant["id"] for variant in variants if row["id"] in variant["jobs"]]
        item["unmatched_families"] = sorted(
            set(item["families"]) - {variant["family"] for variant in variants if row["id"] in variant["jobs"]}
        )
        jobs.append(item)
    assert len(jobs) == 20 and len(family_map) == 8 and len(variants) == 12
    for variant in variants:
        assert variant["family"] in family_map
        assert all(variant["family"] in cards[job]["hand_families"] for job in variant["jobs"])
        variant["physical_target_to_job_assignment"] = None
        variant["new_gripper_model_selected"] = None
    assert default["clockwise_angle_deg"] == 15 and default["setback_before_rotation_m"] == 0.04
    assert hand_plan["selected_role_allocation"]["selected_plan"] == "S5_AB"
    assert hand_plan["selected_role_allocation"]["selected_assembly_arm_count"] == 5
    return {
        "requirements": requirements,
        "families": list(family_map.values()),
        "variants": variants,
        "jobs": jobs,
        "roles": hand_plan["resources"],
        "selected_role_allocation": hand_plan["selected_role_allocation"],
        "working_default": default,
        "unit_support_sequence": read(ROOT / "sources/unit_support_sequence.json"),
        "formal_physical_validity_verdict": None,
    }


def variant_html(row: dict, families: dict) -> str:
    family = families[row["family"]]
    jobs = "、".join(f'<a href="#job-{job}">{job}</a>' for job in row["jobs"])
    features = []
    for identifier in row["features"]:
        suffix = "（工程未定）" if identifier in row.get("unassigned_features", []) else ""
        features.append(escape(identifier + suffix))
    feature_text = "、".join(features) or "実物対象の個別対応は未確定、または写真台帳の範囲外"
    extra = ""
    if row.get("extra_image"):
        extra = (
            '<details class="extra"><summary>補足の保存図を開く</summary>'
            f'<img src="figures/{escape(row["extra_image"])}" alt="{escape(row["title"])}の補足比較図"></details>'
        )
    fields = [
        ("基準面の考え方", family["datum_ja"]),
        ("支えている間", row["support"]),
        ("工具・接続用に空ける場所", row["tool"]),
        ("開く前の引継ぎ", row["open"]),
        ("残っている確認", row["unresolved"]),
    ]
    details = "".join(f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>" for label, value in fields)
    return f'''<article id="{row["id"]}" class="hand-card">
      <div class="eyebrow">{escape(row["family"])} · {escape(row["status"])}</div>
      <h2>{escape(row["title"])}</h2>
      <img class="main-figure" src="figures/{escape(row["image"])}" alt="{escape(row["title"])}の既存比較・構成図">
      <p class="caption">{escape(row["image_note"])}</p>{extra}
      <dl>{details}</dl><p class="job-links">検討先の仕事：{jobs}</p>
      <p class="caption">同族の写真特徴：{feature_text}。この一覧は個々の施工採用を意味しません。</p>
    </article>'''


def job_rows(jobs: list[dict]) -> str:
    rows = []
    for job in jobs:
        variants = " / ".join(f'<a href="#{identifier}">{escape(identifier)}</a>' for identifier in job["variants"])
        if not variants:
            variants = "手先・対象の個別形状は未確定"
        missing = " / ".join(job["unmatched_families"])
        if missing:
            variants += f"<p class=caption>{escape(missing)}：この個別図で対象を網羅していません。</p>"
        rows.append(
            f'<tr id="job-{job["id"]}"><th>{job["id"]}<br>{escape(job["title_ja"])}</th>'
            f"<td>{escape(job['location_ja'])}<br>{escape(job['primary_ja'])}</td>"
            f"<td>{variants}</td><td>{escape(job['assistance_ja'])}</td>"
            f"<td>{escape(job['transfer_ja'])}</td></tr>"
        )
    return "".join(rows)


def write_csv(data: dict, destination: Path) -> None:
    with destination.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["仕事", "名称", "場所", "主担当", "手先系統", "今回の用途図", "個別図のない系統", "補助", "引継ぎ"]
        )
        for job in data["jobs"]:
            writer.writerow(
                [
                    job["id"],
                    job["title_ja"],
                    job["location_ja"],
                    job["primary_ja"],
                    "/".join(job["families"]),
                    "/".join(job["variants"]),
                    "/".join(job["unmatched_families"]),
                    job["assistance_ja"],
                    job["transfer_ja"],
                ]
            )


def main() -> None:
    destination = ROOT / "output"
    assert not destination.exists(), destination
    identity = sources_unchanged()
    data = collect_data()
    families = {row["id"]: row for row in data["families"]}
    cards = "".join(variant_html(row, families) for row in data["variants"])
    navigation = "".join(
        f'<a href="#{row["id"]}">{escape(row["id"])} · {escape(row["title"])}</a>' for row in data["variants"]
    )
    template = (ROOT / "template.html").read_text()
    content = template.replace("__CARDS__", cards).replace("__NAVIGATION__", navigation)
    content = content.replace("__JOB_ROWS__", job_rows(data["jobs"]))
    assert "__CARDS__" not in content and "__JOB_ROWS__" not in content
    destination.mkdir()
    (destination / "figures").mkdir()
    for source in sorted((ROOT / "figures").glob("*.png")):
        shutil.copy2(source, destination / "figures" / source.name)
        assert sha(source) == sha(destination / "figures" / source.name)
    for name in ("hands.css", "source_identity.json", "schematic_receipt.json"):
        shutil.copy2(ROOT / name, destination / name)
    (destination / "index.html").write_text(content)
    (destination / "hand_review_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    write_csv(data, destination / "20仕事と手先用途.csv")
    assert identity == sources_unchanged()
    files = [
        {"path": str(path.relative_to(destination)), "sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(destination.rglob("*"))
        if path.is_file()
    ]
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "files": files,
        "families": 8,
        "application_cards": 12,
        "jobs": 20,
        "source_identity_sha256": sha(ROOT / "source_identity.json"),
        "script_sha256": sha(Path(__file__)),
        "physical_acceptance_verdict": None,
    }
    (destination / "hand_manifest.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(f"HAND_PAGE_BUILT files={len(files)} families=8 applications=12 jobs=20", flush=True)


if __name__ == "__main__":
    main()
