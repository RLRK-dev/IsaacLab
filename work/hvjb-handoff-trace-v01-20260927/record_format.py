# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Preserve the executed generator and compare its formatter-only revision."""

import ast
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    repository = ROOT.parent.parent
    generator = ROOT / "build_trace.py"
    relative = generator.relative_to(repository)
    before = subprocess.run(["git", "show", f":{relative}"], cwd=repository, check=True, capture_output=True).stdout
    after = generator.read_bytes()
    manifest = json.loads((ROOT / "overlay/handoff_trace_manifest_v01.json").read_text())
    assert digest(before) == manifest["generator_sha256"]
    assert ast.dump(ast.parse(before)) == ast.dump(ast.parse(after))
    history = ROOT / "format_record"
    history.mkdir(exist_ok=False)
    (history / "executed_generator.py.txt").write_bytes(before)
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "executed_generator_sha256": digest(before),
        "formatted_generator_sha256": digest(after),
        "abstract_syntax_trees_equal": True,
        "change": "ruff-format joined two string-concatenation lines; one quote style changed",
        "generated_files_rewritten": False,
        "browser_entry_sha256_unchanged": manifest["files"][4]["sha256"],
    }
    assert manifest["files"][4]["path"] == "index_v05d_2.html"
    (history / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("GENERATOR_FORMAT_RECORDED executed_source_preserved=true AST_equal=true")


if __name__ == "__main__":
    main()
