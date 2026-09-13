# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Extract the body of a Word (.docx) file into one text element per line.

The output is meant to be diffed between two versions of a design document, so every
paragraph, table row and footnote becomes exactly one line:

* ``H<n> <text>``           heading paragraph (Word style "Heading n"; "Title" is ``H0``)
* ``P[<style>] <text>``     any other paragraph, prefixed with its Word style name
* ``T[<t>.<r>] c1 | c2``    row ``r`` of table ``t`` (cells joined by `` | ``)
* ``FN[<id>] <text>``       footnote paragraphs, ``EN[<id>]`` endnotes (after the body)
* ``HDR/FTR[<part>] <text>`` header and footer paragraphs
* ``CM[<id>|<author>|<date>] <text>``  Word comments; ``[c<id>]`` marks where a comment is anchored

A manual line break inside a paragraph (Shift+Enter, ``<w:br/>``) starts a new output line with the
same prefix, so pseudocode typed as one paragraph per block is still diffed line by line.

Office Math (OMML) equations are rendered inline between ``⟪`` and ``⟫`` in a linear
form (``x_{t}``, ``a^{b}``, ``(num)/(den)``, ``∑_{i}^{n}(...)``) so that subscripts and
superscripts survive the flattening and can be grepped. Images are rendered as
``[image: media/imageN.png]`` so figure replacements show up in the text diff as well.

Only the Python standard library is used.

Usage::

    python3 docx_extract.py DESIGN.docx > design.txt
    python3 docx_extract.py DESIGN.docx --stats      # element counts on stderr
    python3 docx_extract.py DESIGN.docx --metadata   # docProps summary instead of text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
DC = "{http://purl.org/dc/elements/1.1/}"
DCTERMS = "{http://purl.org/dc/terms/}"
APP = "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}"

MATH_OPEN = "⟪"
MATH_CLOSE = "⟫"
BREAK = "\u2028"  # placeholder for a manual line break inside a paragraph

# Inline nodes that never contribute visible text (tracked deletions, field codes, markers).
_SKIP_INLINE = {
    W + "del",
    W + "delText",
    W + "instrText",
    W + "fldChar",
    W + "proofErr",
    W + "bookmarkStart",
    W + "bookmarkEnd",
    W + "commentRangeStart",
    W + "commentRangeEnd",
    W + "lastRenderedPageBreak",
}

_HEADING_RE = re.compile(r"(?i)^heading\s*(\d+)$")
_WS_RE = re.compile(r"[ \t  ​]+")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if _local(c.tag) == name]


def _first(el: ET.Element, name: str) -> ET.Element | None:
    for c in el:
        if _local(c.tag) == name:
            return c
    return None


def _pr_val(el: ET.Element, pr_name: str, child: str, default: str) -> str:
    """Read ``<m:{pr_name}><m:{child} m:val="..."/></m:{pr_name}>`` with a default."""
    pr = _first(el, pr_name)
    if pr is None:
        return default
    node = _first(pr, child)
    if node is None:
        return default
    return node.get(M + "val", default)


def render_omml(el: ET.Element) -> str:
    """Render an Office Math (OMML) node into a linear, grep-able string."""
    tag = _local(el.tag)
    if tag == "t":
        return el.text or ""
    if tag.endswith("Pr"):
        return ""

    def part(name: str) -> str:
        node = _first(el, name)
        return render_omml(node) if node is not None else ""

    if tag == "sSub":
        return f"{part('e')}_{{{part('sub')}}}"
    if tag == "sSup":
        return f"{part('e')}^{{{part('sup')}}}"
    if tag == "sSubSup":
        return f"{part('e')}_{{{part('sub')}}}^{{{part('sup')}}}"
    if tag == "sPre":
        return f"_{{{part('sub')}}}^{{{part('sup')}}}{part('e')}"
    if tag == "f":
        return f"({part('num')})/({part('den')})"
    if tag == "d":
        beg = _pr_val(el, "dPr", "begChr", "(")
        end = _pr_val(el, "dPr", "endChr", ")")
        sep = _pr_val(el, "dPr", "sepChr", "|")
        return beg + f" {sep} ".join(render_omml(c) for c in _children(el, "e")) + end
    if tag == "rad":
        deg = part("deg")
        return f"root[{deg}]({part('e')})" if deg else f"sqrt({part('e')})"
    if tag == "nary":
        op = _pr_val(el, "naryPr", "chr", "∫")
        lo, hi = part("sub"), part("sup")
        limits = (f"_{{{lo}}}" if lo else "") + (f"^{{{hi}}}" if hi else "")
        return f"{op}{limits}({part('e')})"
    if tag == "func":
        return f"{part('fName')}({part('e')})"
    if tag == "limLow":
        return f"{part('e')}_{{{part('lim')}}}"
    if tag == "limUpp":
        return f"{part('e')}^{{{part('lim')}}}"
    if tag == "acc":
        return part("e") + _pr_val(el, "accPr", "chr", "̂")
    if tag == "bar":
        return f"bar({part('e')})"
    if tag == "m":
        rows = [", ".join(render_omml(c) for c in _children(row, "e")) for row in _children(el, "mr")]
        return "[" + "; ".join(rows) + "]"
    if tag == "eqArr":
        return " ; ".join(render_omml(c) for c in _children(el, "e"))
    return "".join(render_omml(c) for c in el)


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _split_breaks(text: str) -> list[str]:
    """Split rendered paragraph text at manual line breaks, dropping empty pieces."""
    return [piece for piece in (_normalize(t) for t in text.split(BREAK)) if piece]


class DocxExtractor:
    """Walks ``word/document.xml`` (plus footnotes/endnotes) and yields one line per element."""

    def __init__(self, zf: zipfile.ZipFile) -> None:
        self.zf = zf
        self.styles = self._load_styles(zf)
        self.rels = self._load_rels(zf, "word/_rels/document.xml.rels")
        self.stats: dict[str, int] = {
            "heading": 0,
            "paragraph": 0,
            "table_row": 0,
            "footnote": 0,
            "equation": 0,
            "image": 0,
            "comment": 0,
        }

    @staticmethod
    def _load_styles(zf: zipfile.ZipFile) -> dict[str, str]:
        if "word/styles.xml" not in zf.namelist():
            return {}
        root = ET.fromstring(zf.read("word/styles.xml"))
        styles: dict[str, str] = {}
        for style in root.iter(W + "style"):
            style_id = style.get(W + "styleId")
            name = style.find(W + "name")
            if style_id and name is not None:
                styles[style_id] = name.get(W + "val", style_id)
        return styles

    @staticmethod
    def _load_rels(zf: zipfile.ZipFile, path: str) -> dict[str, str]:
        if path not in zf.namelist():
            return {}
        root = ET.fromstring(zf.read(path))
        return {rel.get("Id", ""): rel.get("Target", "") for rel in root.iter(PKG_REL + "Relationship")}

    # -- inline content ---------------------------------------------------------------

    def style_name(self, p: ET.Element) -> str:
        ppr = _first(p, "pPr")
        if ppr is not None:
            pstyle = _first(ppr, "pStyle")
            if pstyle is not None:
                style_id = pstyle.get(W + "val", "")
                return self.styles.get(style_id, style_id)
        return "Normal"

    def render_inline(self, el: ET.Element, parts: list[str]) -> None:
        tag = el.tag
        if tag == W + "t":
            parts.append(el.text or "")
        elif tag == M + "oMath":
            self.stats["equation"] += 1
            parts.append(MATH_OPEN + render_omml(el) + MATH_CLOSE)
        elif tag == W + "tab":
            parts.append(" ")
        elif tag in (W + "br", W + "cr"):
            parts.append(BREAK if el.get(W + "type", "textWrapping") == "textWrapping" else " ")
        elif tag == W + "noBreakHyphen":
            parts.append("-")
        elif tag == W + "sym":
            parts.append(f"[sym:{el.get(W + 'font', '?')}:{el.get(W + 'char', '?')}]")
        elif tag in (W + "footnoteReference", W + "endnoteReference"):
            parts.append(f"[fn{el.get(W + 'id', '?')}]")
        elif tag == W + "commentReference":
            parts.append(f"[c{el.get(W + 'id', '?')}]")
        elif tag == A + "blip":
            self.stats["image"] += 1
            rid = el.get(R + "embed", "")
            parts.append(f"[image: {self.rels.get(rid, rid)}]")
        elif tag == MC + "AlternateContent":
            # Word stores drawings twice (Choice + Fallback); render only the primary copy.
            choice = _first(el, "Choice")
            if choice is not None:
                for c in choice:
                    self.render_inline(c, parts)
        elif tag == W + "p":
            # A paragraph nested in a text box: keep it inline with the anchoring paragraph.
            parts.append(" ")
            for c in el:
                self.render_inline(c, parts)
        elif tag in _SKIP_INLINE or tag.endswith("Pr"):
            return
        else:
            for c in el:
                self.render_inline(c, parts)

    def paragraph_pieces(self, p: ET.Element) -> list[str]:
        parts: list[str] = []
        for c in p:
            self.render_inline(c, parts)
        return _split_breaks("".join(parts))

    def paragraph_text(self, p: ET.Element) -> str:
        return " ".join(self.paragraph_pieces(p))

    # -- block content ----------------------------------------------------------------

    def iter_blocks(self, parent: ET.Element) -> Iterator[tuple[str, ET.Element]]:
        for child in parent:
            tag = child.tag
            if tag == W + "p":
                yield "p", child
            elif tag == W + "tbl":
                yield "tbl", child
            elif tag == W + "sectPr":
                continue
            elif tag == W + "sdt":
                content = _first(child, "sdtContent")
                if content is not None:
                    yield from self.iter_blocks(content)
            else:
                yield from self.iter_blocks(child)

    def paragraph_lines(self, p: ET.Element) -> list[str]:
        pieces = self.paragraph_pieces(p)
        if not pieces:
            return []
        style = self.style_name(p)
        match = _HEADING_RE.match(style)
        if match:
            self.stats["heading"] += 1
            return [f"H{match.group(1)} {' '.join(pieces)}"]
        if style.lower() == "title":
            self.stats["heading"] += 1
            return [f"H0 {' '.join(pieces)}"]
        self.stats["paragraph"] += len(pieces)
        return [f"P[{style}] {piece}" for piece in pieces]

    def cell_text(self, tc: ET.Element) -> str:
        parts: list[str] = []
        for kind, block in self.iter_blocks(tc):
            if kind == "p":
                text = self.paragraph_text(block)
                if text:
                    parts.append(text)
            else:
                rows = [" | ".join(self.cell_text(c) for c in _children(tr, "tc")) for tr in _children(block, "tr")]
                parts.append("[table] " + " ; ".join(rows))
        return " // ".join(parts)

    def table_lines(self, tbl: ET.Element, index: int) -> list[str]:
        lines: list[str] = []
        for row_no, tr in enumerate(_children(tbl, "tr"), start=1):
            cells = [self.cell_text(tc) for tc in _children(tr, "tc")]
            self.stats["table_row"] += 1
            lines.append(f"T[{index}.{row_no}] " + " | ".join(cells))
        return lines

    def note_lines(self, part: str, prefix: str) -> list[str]:
        if part not in self.zf.namelist():
            return []
        lines: list[str] = []
        root = ET.fromstring(self.zf.read(part))
        for note in root:
            note_id = note.get(W + "id", "?")
            if note_id in ("-1", "0"):  # separator / continuation separator
                continue
            for kind, block in self.iter_blocks(note):
                if kind != "p":
                    continue
                text = self.paragraph_text(block)
                if text:
                    self.stats["footnote"] += 1
                    lines.append(f"{prefix}[{note_id}] {text}")
        return lines

    def extract(self) -> list[str]:
        root = ET.fromstring(self.zf.read("word/document.xml"))
        body = root.find(W + "body")
        if body is None:
            raise ValueError("word/document.xml has no <w:body>")
        lines: list[str] = []
        table_index = 0
        for kind, block in self.iter_blocks(body):
            if kind == "p":
                lines.extend(self.paragraph_lines(block))
            else:
                table_index += 1
                lines.extend(self.table_lines(block, table_index))
        lines.extend(self.note_lines("word/footnotes.xml", "FN"))
        lines.extend(self.note_lines("word/endnotes.xml", "EN"))
        lines.extend(self.header_footer_lines())
        lines.extend(self.comment_lines())
        return lines

    def header_footer_lines(self) -> list[str]:
        lines: list[str] = []
        for part in sorted(self.zf.namelist()):
            if not re.fullmatch(r"word/(header|footer)\d*\.xml", part):
                continue
            prefix = "HDR" if "header" in part else "FTR"
            root = ET.fromstring(self.zf.read(part))
            for kind, block in self.iter_blocks(root):
                if kind == "p":
                    text = self.paragraph_text(block)
                    if text:
                        lines.append(f"{prefix}[{part.rsplit('/', 1)[-1]}] {text}")
                else:
                    lines.extend(f"{prefix}[{part.rsplit('/', 1)[-1]}] {row}" for row in self.table_lines(block, 0))
        return lines

    def comment_lines(self) -> list[str]:
        if "word/comments.xml" not in self.zf.namelist():
            return []
        lines: list[str] = []
        root = ET.fromstring(self.zf.read("word/comments.xml"))
        for comment in root:
            cid = comment.get(W + "id", "?")
            author = comment.get(W + "author", "")
            date = comment.get(W + "date", "")[:10]
            texts = [self.paragraph_text(b) for k, b in self.iter_blocks(comment) if k == "p"]
            text = " / ".join(t for t in texts if t)
            if text:
                self.stats["comment"] += 1
                lines.append(f"CM[{cid}|{author}|{date}] {text}")
        return lines


def extract_lines(path: str) -> tuple[list[str], dict[str, int]]:
    """Return ``(lines, stats)`` for a .docx file."""
    with zipfile.ZipFile(path) as zf:
        extractor = DocxExtractor(zf)
        lines = extractor.extract()
        return lines, extractor.stats


def read_metadata(path: str) -> dict[str, str]:
    """Return the docProps (core + app) properties that matter for provenance checks."""
    meta: dict[str, str] = {}
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if "docProps/core.xml" in names:
            root = ET.fromstring(zf.read("docProps/core.xml"))
            for key, tag in (
                ("title", DC + "title"),
                ("creator", DC + "creator"),
                ("lastModifiedBy", CP + "lastModifiedBy"),
                ("revision", CP + "revision"),
                ("created", DCTERMS + "created"),
                ("modified", DCTERMS + "modified"),
            ):
                node = root.find(tag)
                meta[key] = (node.text or "").strip() if node is not None else ""
        if "docProps/app.xml" in names:
            root = ET.fromstring(zf.read("docProps/app.xml"))
            for key in ("Application", "AppVersion", "Pages", "Words"):
                node = root.find(APP + key)
                meta[key] = (node.text or "").strip() if node is not None else ""
    return meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("docx", help="path to the .docx file")
    parser.add_argument("--stats", action="store_true", help="print element counts to stderr")
    parser.add_argument("--metadata", action="store_true", help="print docProps metadata as JSON instead of text")
    args = parser.parse_args(argv)

    if args.metadata:
        print(json.dumps(read_metadata(args.docx), ensure_ascii=False, indent=2))
        return 0

    lines, stats = extract_lines(args.docx)
    for line in lines:
        print(line)
    if args.stats:
        stats = dict(stats, total_lines=len(lines))
        print(json.dumps(stats, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
