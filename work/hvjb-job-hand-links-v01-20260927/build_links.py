# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Add review links between the existing twenty jobs and twelve hand uses."""

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
SOURCE = WORK / "hvjb-resume-v05d-20260927/delivery_snapshot"
VARIANTS = WORK / "hvjb-hand-coverage-v01-20260923/variants.json"
ENTRY = "index_v05d_1.html"
SCRIPT = "review_job_hands_v01.js"
STYLE = "job_hands_v01.css"
DATA = "data/job_hand_links_v01.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def usage_data(payload: dict) -> dict:
    variants = json.loads(VARIANTS.read_text())
    jobs = []
    for job in payload["jobs"]:
        used = [row["id"] for row in variants if job["id"] in row["jobs"]]
        note = "既存の比較図・構成図です。実部品への適用と安定把持の確認は別に残っています。"
        if not used:
            note = "この仕事の対象と手先は、個別の比較図へまだ対応づけられていません。"
        if job["id"] in ("D11", "D21", "D61"):
            note += " H05の他端末は個別形状を未照合です。開口を通す内側ハウジング用の爪を転用した意味ではありません。"
        if job["id"] == "D60":
            note += " H08は元の候補です。主ヒューズP22の取付工程は未確定です。"
        if "H06_UNIT" in used:
            note += " H06_UNITは対象参照で、ユニット用の指形状はまだ表示していません。"
        jobs.append({"id": job["id"], "title_ja": job["title_ja"], "variant_ids": used, "note_ja": note})
    return {
        "source_variants_sha256": sha(VARIANTS),
        "source_entry_sha256": sha(SOURCE / "index.html"),
        "mapping_changed": False,
        "variants": variants,
        "jobs": jobs,
    }


def main_entry(out: Path, usage: dict) -> None:
    page = (SOURCE / "index.html").read_text()
    page = page.replace('src="review.js"', f'src="{SCRIPT}"')
    page = page.replace('href="hand_review/index.html"', 'href="hand_review/index_v02.html"')
    page = page.replace("レビュー v05d</title>", "レビュー v05d.1</title>")
    page = page.replace("工程の具体化 · 2026-09-24", "工程と手先の対応 · 2026-09-27")
    page = page.replace("</head>", f'  <link rel="stylesheet" href="{STYLE}">\n</head>', 1)
    marker = '<dl id="job-fields" class="field-list"></dl>'
    section = (
        '<h4 class="job-hand-heading">この仕事で検討している手先</h4>'
        '<div id="job-hand-links" aria-label="手先の比較図"></div>'
        '<p id="job-hand-note" class="secondary small"></p>\n          '
    )
    assert page.count(marker) == 1
    page = page.replace(marker, section + marker)
    label = "仕事を選ぶと対応場面と部品を表示します。"
    assert page.count(label) == 1
    page = page.replace(label, "仕事を選ぶと、手先の比較図・対応場面・部品を表示します。")
    encoded = json.dumps(usage, ensure_ascii=False, separators=(",", ":"))
    page = page.replace("</body>", f'<script id="hand-usage-data" type="application/json">{encoded}</script>\n</body>')
    (out / ENTRY).write_text(page)


def main_script(out: Path) -> None:
    script = (SOURCE / "review.js").read_text()
    marker = "  function chooseJob(id, navigate = true) {"
    assert script.count(marker) == 1
    script = script.replace(marker, (ROOT / "hand_links.js").read_text() + marker)
    marker = '    byId("job-scenes").replaceChildren('
    assert script.count(marker) == 1
    script = script.replace(marker, "    renderHandLinks(id);\n" + marker)
    marker = '    if (navigate) byId("panel-jobs").scrollIntoView({block:"start"});'
    assert script.count(marker) == 1
    script = script.replace(
        marker,
        '    if (navigate && location.hash !== `#job=${id}`) history.pushState(null, "", `#job=${id}`);\n' + marker,
    )
    marker = '    const node = button("", () => chooseJob(row.id, false));'
    assert script.count(marker) == 1
    script = script.replace(
        marker,
        '    const node = button("", () => {\n'
        "      chooseJob(row.id, false);\n"
        '      if (location.hash !== `#job=${row.id}`) history.pushState(null, "", `#job=${row.id}`);\n'
        "    });",
    )
    marker = '    const value = new URLSearchParams(location.hash.slice(1)).get("scene");'
    assert script.count(marker) == 1
    script = script.replace(
        marker,
        "    const params = new URLSearchParams(location.hash.slice(1));\n"
        '    const jobId = params.get("job");\n'
        "    if (jobId && jobs.has(jobId)) { chooseJob(jobId); return; }\n"
        '    const value = params.get("scene");',
    )
    script = script.replace("followSceneLink", "followReviewLink")
    (out / SCRIPT).write_text(script)


def hand_page(out: Path, usage: dict) -> None:
    page = (SOURCE / "hand_review/index.html").read_text().replace("../index.html", f"../{ENTRY}")
    page = page.replace('href="#job-', f'href="../{ENTRY}#job=')
    for job in usage["jobs"]:
        marker = f'<tr id="job-{job["id"]}"><th>{job["id"]}<br>'
        assert page.count(marker) == 1
        link = f'<a href="../{ENTRY}#job={job["id"]}">{job["id"]}</a><br>'
        page = page.replace(marker, f'<tr id="job-{job["id"]}"><th>{link}')
    note = (
        '<p class="caption">2026-09-27：各用途から全体ページの該当仕事へ戻れます。比較図の内容は変更していません。</p>'
    )
    page = page.replace("</header>", note + "</header>", 1)
    (out / "hand_review").mkdir()
    (out / "hand_review/index_v02.html").write_text(page)


def main() -> None:
    out = ROOT / "overlay"
    out.mkdir(exist_ok=False)
    page = (SOURCE / "index.html").read_text()
    match = re.search(r'<script id="review-data" type="application/json">(.*?)</script>', page, re.S)
    assert match
    payload = json.loads(match.group(1))
    assert len(payload["jobs"]) == 20 and len(payload["features"]) == 92 and len(payload["scenes"]) == 22
    usage = usage_data(payload)
    main_entry(out, usage)
    main_script(out)
    hand_page(out, usage)
    shutil.copy2(ROOT / "hand_links.css", out / STYLE)
    (out / "data").mkdir()
    (out / DATA).write_text(json.dumps(usage, ensure_ascii=False, indent=2) + "\n")
    (out / "2026-09-27_手先図への移動.md").write_text(
        "# 工程から手先の比較図を開く\n\n"
        f"入口は `{ENTRY}` です。「20仕事」で仕事を選び、手先の図をクリックしてください。\n"
        "手先図にある仕事番号から、全体ページの同じ仕事へ戻れます。\n\n"
        "動画は既存v05dの1本です。20仕事・92写真特徴・12用途の内容と対応は変更していません。\n"
        "個別図がない5仕事と、H05他端末・主ヒューズP22・内部ユニット用爪の未確定箇所も表示しています。\n"
    )
    files = [
        {"path": str(path.relative_to(out)), "sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    assert all(not (SOURCE / row["path"]).exists() for row in files)
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": ENTRY,
        "files": files,
        "source_manifest_sha256": sha(SOURCE / "review_manifest.json"),
        "source_video_sha256": "0cdcd4d43831c3f805aa4e5960b666e7965ee6f1ac38b59d31645630d1dd40da",
        "source_variants_sha256": sha(VARIANTS),
        "counts": {"jobs": 20, "hand_uses": len(usage["variants"]), "features": 92, "scenes": 22},
        "jobs_without_individual_comparison": [row["id"] for row in usage["jobs"] if not row["variant_ids"]],
        "generator_sha256": sha(Path(__file__)),
        "helper_sha256": sha(ROOT / "hand_links.js"),
        "css_sha256": sha(ROOT / "hand_links.css"),
        "new_video_generated": False,
        "new_mechanical_design_selected": False,
    }
    (out / "job_hand_links_manifest_v01.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    preview = ROOT / "preview"
    assert not preview.exists()
    shutil.copytree(SOURCE, preview)
    for path in out.rglob("*"):
        if path.is_file():
            destination = preview / path.relative_to(out)
            assert not destination.exists()
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    print("JOB_HAND_LINKS_BUILT jobs=20 hand_uses=12 new_videos=0")


if __name__ == "__main__":
    main()
