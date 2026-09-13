# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare two versions of a .docx design document mechanically.

The steps of the review procedure that can be automated are run and written as a Markdown report:

1. SHA-256 of both files (identical file = re-upload) and lookup in ``known_versions.json``
2. per-part MD5 comparison inside the ZIP container (figures under ``word/media/`` listed separately)
3. ``docProps`` metadata with regression warnings (tool-default creator, template dates, revision)
4. unified diff of the extracted text, plus the deletion side on its own
5. headings added / removed (new or dropped sections)
6. symbol scan: tokens with sub-/superscripts that are new in the next version, flagged when they occur once
7. provenance chain: does the next version quote the previous version's SHA-256?

Usage::

    python3 docx_compare.py prev.docx next.docx --out review_v0.8 [--symbol "γ_W" ...]

The report goes to stdout; with ``--out DIR`` the extracted texts, the unified diff and the report are
saved as ``prev.txt``, ``next.txt``, ``diff.txt`` and ``report.md``. Exit status is 1 when the two files
are byte-identical (nothing to review), 0 otherwise.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from docx_extract import extract_lines, read_metadata

HERE = Path(__file__).resolve().parent
DEFAULT_KNOWN = HERE / "known_versions.json"

IDENTICAL_MARK = "同一ファイル（再アップロード）"
NO_MEDIA_CHANGE_MARK = "図の変更なし"
SINGLETON_MARK = "★出現1回"

# creator values that mean "the generating tool's default was left in place"
DEFAULT_CREATORS = {"", "python-docx", "openai", "chatgpt", "microsoft office user", "user", "unknown", "author"}
TEMPLATE_YEAR_BEFORE = 2020  # a created date before this is a template value, not a real creation date

# A symbol is a letter (Latin/Greek) followed by at least one sub- or superscript group: V_{open}, γ_W, Q_{chunk,o}^{κ}
SYMBOL_RE = re.compile(
    r"[A-Za-zΑ-Ωα-ωϑϵϕ][A-Za-z0-9Α-Ωα-ω]*"
    r"(?:[_^](?:\{(?:[^{}]|\{[^{}]*\})*\}|[A-Za-z0-9Α-Ωα-ω]+))+"
)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def part_digests(path: Path) -> dict[str, tuple[str, int]]:
    """MD5 and size of every part inside the .docx ZIP container."""
    parts: dict[str, tuple[str, int]] = {}
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            data = zf.read(name)
            parts[name] = (hashlib.md5(data).hexdigest(), len(data))
    return parts


def load_known(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("versions", [])


def match_known(sha: str, known: list[dict[str, Any]]) -> dict[str, Any] | None:
    for entry in known:
        prefix = str(entry.get("sha256_prefix", "")).lower()
        if prefix and sha.lower().startswith(prefix):
            return entry
    return None


def compare_parts(prev: dict[str, tuple[str, int]], nxt: dict[str, tuple[str, int]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"changed": [], "added": [], "removed": [], "same": []}
    for name in sorted(set(prev) | set(nxt)):
        if name not in prev:
            result["added"].append(name)
        elif name not in nxt:
            result["removed"].append(name)
        elif prev[name][0] != nxt[name][0]:
            result["changed"].append(name)
        else:
            result["same"].append(name)
    return result


def _year_of(value: str) -> int | None:
    match = re.match(r"(\d{4})", value or "")
    return int(match.group(1)) if match else None


def metadata_warnings(prev_meta: dict[str, str], next_meta: dict[str, str]) -> list[str]:
    warnings: list[str] = []
    creator = next_meta.get("creator", "")
    if creator.strip().lower() in DEFAULT_CREATORS:
        warnings.append(f"creator が生成ツールの既定値に戻っている: {creator!r}")
    year = _year_of(next_meta.get("created", ""))
    if year is not None and year < TEMPLATE_YEAR_BEFORE:
        warnings.append(f"created がテンプレートの既定日付: {next_meta.get('created')}")
    prev_rev, next_rev = prev_meta.get("revision", ""), next_meta.get("revision", "")
    if prev_rev.isdigit() and next_rev.isdigit() and int(next_rev) <= int(prev_rev):
        warnings.append(f"revision が増えていない: {prev_rev} → {next_rev}")
    if prev_meta.get("creator") and creator and creator != prev_meta["creator"]:
        warnings.append(f"creator が前版と異なる: {prev_meta['creator']!r} → {creator!r}")
    return warnings


def headings(lines: list[str]) -> list[str]:
    return [line for line in lines if re.match(r"H\d+ ", line)]


def symbol_counts(lines: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in lines:
        counts.update(SYMBOL_RE.findall(line))
    return counts


def count_substring(lines: list[str], needle: str) -> tuple[int, int]:
    """Return ``(occurrences, lines)`` of a literal string, like ``grep -o | wc -l`` and ``grep -c``."""
    occurrences = sum(line.count(needle) for line in lines)
    line_hits = sum(1 for line in lines if needle in line)
    return occurrences, line_hits


def _describe_known(entry: dict[str, Any] | None) -> str:
    if entry is None:
        return "未登録（known_versions.json に無い）"
    return f"{entry.get('version', '?')}（{entry.get('sha256_prefix', '')}…）"


def _fence(lines: list[str], limit: int) -> str:
    shown = lines[:limit]
    body = "\n".join(shown) if shown else "(なし)"
    more = f"\n... 他 {len(lines) - limit} 行" if len(lines) > limit else ""
    return f"```\n{body}{more}\n```"


def build_report(
    prev_path: Path,
    next_path: Path,
    known: list[dict[str, Any]],
    symbols: list[str],
    max_lines: int = 300,
) -> tuple[str, dict[str, Any]]:
    """Return ``(markdown_report, summary)``; ``summary`` carries the machine-readable findings."""
    prev_sha, next_sha = sha256_of(prev_path), sha256_of(next_path)
    prev_size, next_size = prev_path.stat().st_size, next_path.stat().st_size
    identical = prev_sha == next_sha
    prev_known, next_known = match_known(prev_sha, known), match_known(next_sha, known)

    out: list[str] = [f"# 版間比較レポート: {prev_path.name} → {next_path.name}", ""]
    out += ["## 1. ファイル同一性と来歴", ""]
    out += ["| | 前版 | 今版 |", "|---|---|---|"]
    out += [f"| ファイル | {prev_path.name} | {next_path.name} |"]
    out += [f"| SHA-256 | {prev_sha} | {next_sha} |"]
    out += [f"| サイズ (bytes) | {prev_size:,} | {next_size:,} |"]
    out += [f"| 既知の版 | {_describe_known(prev_known)} | {_describe_known(next_known)} |", ""]
    if identical:
        out += [f"**{IDENTICAL_MARK}**: 中身は前版と完全に同一（差分ゼロ）。レビュー対象にならない。", ""]
    elif next_known is not None:
        out += [f"**警告**: 今版は既知の {next_known.get('version')} と完全に同一。新版ではない。", ""]

    summary: dict[str, Any] = {
        "identical": identical,
        "prev_sha256": prev_sha,
        "next_sha256": next_sha,
        "prev_known": prev_known,
        "next_known": next_known,
    }
    if identical:
        return "\n".join(out) + "\n", summary

    # 2. parts
    parts = compare_parts(part_digests(prev_path), part_digests(next_path))
    media_changed = [n for n in parts["changed"] + parts["added"] + parts["removed"] if n.startswith("word/media/")]
    other_changed = [n for n in parts["changed"] if not n.startswith("word/media/")]
    out += ["## 2. パート比較（ZIP 内）", ""]
    counts = " / ".join(str(len(parts[k])) for k in ("changed", "added", "removed", "same"))
    out += [f"- 変更 / 追加 / 削除 / 同一: {counts}", ""]
    out += ["### 図（word/media）", ""]
    if media_changed:
        out += [f"- {name}  ← 目視で確認" for name in media_changed]
    else:
        out += [f"- {NO_MEDIA_CHANGE_MARK}（図の目視は不要。ただし本文で新設した機構が図に無いままかは別途確認）"]
    out += ["", "### その他の変更・追加・削除パート", ""]
    out += [f"- 変更: {n}" for n in other_changed]
    out += [f"- 追加: {n}" for n in parts["added"] if not n.startswith("word/media/")]
    out += [f"- 削除: {n}" for n in parts["removed"] if not n.startswith("word/media/")]
    out += [""]
    summary["changed_media"] = media_changed
    summary["changed_parts"] = other_changed

    # 3. metadata
    prev_meta, next_meta = read_metadata(str(prev_path)), read_metadata(str(next_path))
    warnings = metadata_warnings(prev_meta, next_meta)
    out += ["## 3. メタデータ（docProps）", ""]
    out += ["| 項目 | 前版 | 今版 |", "|---|---|---|"]
    for key in sorted(set(prev_meta) | set(next_meta)):
        out += [f"| {key} | {prev_meta.get(key, '')} | {next_meta.get(key, '')} |"]
    out += [""]
    out += [f"- 警告: {w}" for w in warnings] or ["- 回帰なし"]
    out += [""]
    summary["metadata_warnings"] = warnings

    # 4. text diff
    prev_lines, prev_stats = extract_lines(str(prev_path))
    next_lines, next_stats = extract_lines(str(next_path))
    diff = list(
        difflib.unified_diff(prev_lines, next_lines, fromfile=prev_path.name, tofile=next_path.name, n=1, lineterm="")
    )
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")]
    out += ["## 4. 本文差分", ""]
    out += [f"- 抽出行数: {len(prev_lines)} → {len(next_lines)}（{len(next_lines) - len(prev_lines):+d}）"]
    out += [f"- 要素数 前版: {json.dumps(prev_stats, ensure_ascii=False)}"]
    out += [f"- 要素数 今版: {json.dumps(next_stats, ensure_ascii=False)}"]
    out += [f"- 追加行 {len(added)} / 削除行 {len(removed)}（unified diff は diff.txt）", ""]
    out += ["### 削除された行（黙った削除の確認用。付録の対応表に無い削除を探す）", ""]
    out += [_fence(removed, max_lines), ""]
    summary.update(
        {"added": added, "removed": removed, "diff": diff, "prev_lines": prev_lines, "next_lines": next_lines}
    )

    # 5. headings
    prev_heads, next_heads = headings(prev_lines), headings(next_lines)
    added_heads = [h for h in next_heads if h not in set(prev_heads)]
    removed_heads = [h for h in prev_heads if h not in set(next_heads)]
    out += ["## 5. 見出しの変化", ""]
    out += ["### 追加された見出し", ""]
    out += [f"- {h}" for h in added_heads] or ["- なし"]
    out += ["", "### 削除・改題された見出し", ""]
    out += [f"- {h}" for h in removed_heads] or ["- なし"]
    out += [""]
    summary["added_headings"] = added_heads
    summary["removed_headings"] = removed_heads

    # 6. symbols
    prev_syms, next_syms = symbol_counts(prev_lines), symbol_counts(next_lines)
    new_syms = {s: c for s, c in next_syms.items() if s not in prev_syms}
    out += ["## 6. 記号スキャン", ""]
    out += [f"- 前版 {len(prev_syms)} 種 / 今版 {len(next_syms)} 種 / 新出 {len(new_syms)} 種", ""]
    out += ["### 新出記号（前版に無い）。出現1回は未定義の可能性が高い", ""]
    if new_syms:
        out += ["| 記号 | 今版の出現数 | 備考 |", "|---|---|---|"]
        for sym, cnt in sorted(new_syms.items(), key=lambda kv: (kv[1], kv[0])):
            out += [f"| `{sym}` | {cnt} | {SINGLETON_MARK if cnt == 1 else ''} |"]
    else:
        out += ["- なし"]
    if symbols:
        out += ["", "### 指定記号（--symbol）の出現数（出現数 / 行数）", ""]
        out += ["| 記号 | 前版 | 今版 |", "|---|---|---|"]
        for sym in symbols:
            p_occ, p_ln = count_substring(prev_lines, sym)
            n_occ, n_ln = count_substring(next_lines, sym)
            out += [f"| `{sym}` | {p_occ} / {p_ln} | {n_occ} / {n_ln} |"]
    out += [""]
    summary["new_symbols"] = new_syms

    # 7. provenance chain
    needle = prev_sha[:8].lower()
    hits = [line for line in next_lines if needle in line.lower()]
    out += ["## 7. SHA-256 引用の連鎖", ""]
    if hits:
        out += [f"- 前版 SHA-256（先頭 `{needle}`）を今版本文で確認: {len(hits)} 行", ""]
        out += [_fence(hits, 10)]
    else:
        out += [f"- 前版 SHA-256（先頭 `{needle}`）が今版本文に無い。付録の来歴引用を確認する。"]
    out += [""]
    summary["sha_chain_found"] = bool(hits)

    return "\n".join(out) + "\n", summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prev", type=Path, help="previous version (.docx)")
    parser.add_argument("next", type=Path, help="next version (.docx)")
    parser.add_argument("--out", type=Path, help="directory for prev.txt / next.txt / diff.txt / report.md")
    parser.add_argument("--known", type=Path, default=DEFAULT_KNOWN, help="known_versions.json for lineage lookup")
    parser.add_argument("--symbol", action="append", default=[], help="literal symbol to count in both versions")
    parser.add_argument("--max-lines", type=int, default=300, help="cap for line listings inside the report")
    args = parser.parse_args(argv)

    report, summary = build_report(args.prev, args.next, load_known(args.known), args.symbol, args.max_lines)
    print(report)
    if args.out is not None and not summary["identical"]:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "prev.txt").write_text("\n".join(summary["prev_lines"]) + "\n", encoding="utf-8")
        (args.out / "next.txt").write_text("\n".join(summary["next_lines"]) + "\n", encoding="utf-8")
        (args.out / "diff.txt").write_text("\n".join(summary["diff"]) + "\n", encoding="utf-8")
        (args.out / "report.md").write_text(report, encoding="utf-8")
        print(f"saved: {args.out}/prev.txt, next.txt, diff.txt, report.md", file=sys.stderr)
    return 1 if summary["identical"] else 0


if __name__ == "__main__":
    sys.exit(main())
