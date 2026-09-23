# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Package the role diagrams as a standalone, offline comparison page."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT / "output"
    out.mkdir(exist_ok=False)
    data = json.loads((ROOT / "data/parallel_review_data.json").read_text())
    commands = []
    for path in sorted((ROOT / "figures").glob("*.svg")):
        target = path.with_suffix(".png")
        assert not target.exists(), target
        command = ["convert", "-font", FONT, "-background", "white", str(path), str(target)]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        commands.append(
            {"argv": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        )
    shutil.copytree(ROOT / "figures", out / "figures")
    for name in ("parallel.css", "parallel.js", "README.md"):
        shutil.copy2(ROOT / name, out / name)
    shutil.copy2(ROOT / "data/parallel_review_data.json", out / "parallel_review_data.json")
    for name in ("manual_scope_20260923.md", "manual_source_identity.json"):
        shutil.copy2(ROOT.parent / "hvjb-line-progress-20260923/research" / name, out / name)
    buttons = []
    for row in data["scenarios"]:
        selected = str(row["id"] == data["default_scenario"]).lower()
        label = "補助なし" if row["id"] == "NONE" else "＋".join(row["id"])
        buttons.append(
            f'<button type="button" data-scenario="{row["id"]}" aria-pressed="{selected}"'
            f' aria-label="{html.escape(row["title_ja"])}">{label}</button>'
        )
    default = next(row for row in data["scenarios"] if row["id"] == data["default_scenario"])
    jobs = {row["id"]: row for row in data["jobs_unmodified"]}
    links = []
    for key in ("D31", "D40", "D42", "D45", "D50", "D60", "D61"):
        label = jobs[key]["title_ja"] if "title_ja" in jobs[key] else jobs[key]["work_ja"]
        links.append(f'<a href="../hand_review/index.html#job-{key}">{key}：{html.escape(label)}</a>')
    page = (ROOT / "template.html").read_text()
    replacements = {
        "BUTTONS": "\n".join(buttons),
        "DEFAULT_NOTE": html.escape(default["note_ja"]),
        "DEFAULT_TITLE": html.escape(default["title_ja"]),
        "JOB_LINKS": "\n".join(links),
        "DATA": json.dumps(
            {"default_scenario": data["default_scenario"], "scenarios": data["scenarios"]}, ensure_ascii=False
        ),
    }
    for key, value in replacements.items():
        page = page.replace("{{" + key + "}}", value)
    assert "{{" not in page
    (out / "index.html").write_text(page, encoding="utf-8")
    cards = []
    for row in data["scenarios"]:
        cards.append(
            f'<article><h2>{html.escape(row["title_ja"])}</h2><figure><a href="{row["png"]}">'
            f'<img src="{row["png"]}" alt="{html.escape(row["title_ja"])}の担当図" width="1400" height="850">'
            f"</a></figure><p>{html.escape(row['note_ja'])}</p></article>"
        )
    overview = (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>3STの8条件一覧</title><link rel="stylesheet" href="parallel.css"></head><body><main>'
        '<nav><a href="index.html">← 3STの図へ</a></nav><h1>補助が必要なセル：8つの独立条件</h1>'
        "<p>時系列ではありません。図を選ぶと原寸PNGを開きます。担当IDの重複の有無と、実機成立は別です。</p>"
        '<div class="case-list">' + "\n".join(cards) + "</div></main></body></html>\n"
    )
    (out / "all_cases.html").write_text(overview, encoding="utf-8")
    files = [
        {"path": str(path.relative_to(out)), "bytes": path.stat().st_size, "sha256": sha(path)}
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    manifest = {
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "files": files,
        "png_rasterization": commands,
        "new_motion_or_video": False,
        "inputs": {"data": sha(ROOT / "data/parallel_review_data.json"), "font": sha(Path(FONT))},
        "build_sources": {
            path.name: sha(path) for path in sorted(ROOT.iterdir()) if path.suffix in (".py", ".html", ".css", ".js")
        },
    }
    (out / "parallel_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"PARALLEL_PAGE_READY files={len(files)} diagrams=10 cases=8", flush=True)


if __name__ == "__main__":
    main()
