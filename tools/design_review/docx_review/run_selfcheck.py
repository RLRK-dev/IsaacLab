# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Self-check for the docx review tools: builds two synthetic .docx files and runs the comparison.

The "next" file reproduces the regressions the review procedure is meant to catch (changed figure
bytes, tool-default creator, template creation date, revision not increased, a silently deleted
sentence, a new symbol that occurs only once) and the report is checked for each of them.

Usage::

    python3 run_selfcheck.py
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from docx_compare import IDENTICAL_MARK, NO_MEDIA_CHANGE_MARK, SINGLETON_MARK, build_report, sha256_of
from docx_extract import extract_lines, read_metadata

NS_DECL = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
)
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

CONTENT_TYPES = (
    XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/footnotes.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    "</Types>"
)
ROOT_RELS = (
    XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    '<Relationship Id="rId2" '
    'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
    'Target="docProps/core.xml"/>'
    '<Relationship Id="rId3" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
    'Target="docProps/app.xml"/>'
    "</Relationships>"
)
DOC_RELS = (
    XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="styles.xml"/>'
    '<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
    'Target="media/image1.png"/>'
    "</Relationships>"
)
STYLES = (
    XML_HEAD + f"<w:styles {NS_DECL}>"
    '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/></w:style>'
    "</w:styles>"
)
FOOTNOTES = (
    XML_HEAD + f"<w:footnotes {NS_DECL}>"
    '<w:footnote w:id="-1"><w:p><w:r><w:t>separator</w:t></w:r></w:p></w:footnote>'
    '<w:footnote w:id="1"><w:p><w:r><w:t>Footnote body text.</w:t></w:r></w:p></w:footnote>'
    "</w:footnotes>"
)


def run(text: str) -> str:
    return f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(*inner: str, style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{''.join(inner)}</w:p>"


def m_text(text: str) -> str:
    return f"<m:r><m:t>{escape(text)}</m:t></m:r>"


def m_sub(base: str, sub: str) -> str:
    return f"<m:oMath><m:sSub><m:e>{m_text(base)}</m:e><m:sub>{m_text(sub)}</m:sub></m:sSub></m:oMath>"


def m_sum_frac() -> str:
    return (
        "<m:oMath>"
        '<m:nary><m:naryPr><m:chr m:val="∑"/></m:naryPr>'
        "<m:sub>" + m_text("i=1") + "</m:sub><m:sup>" + m_text("N") + "</m:sup>"
        "<m:e><m:sSub><m:e>"
        + m_text("q")
        + "</m:e><m:sub>"
        + m_text("i")
        + "</m:sub></m:sSub></m:e></m:nary>"
        + m_text(" + ")
        + "<m:f><m:num>"
        + m_text("a")
        + "</m:num><m:den>"
        + m_text("b")
        + "</m:den></m:f>"
        "</m:oMath>"
    )


def image(rid: str) -> str:
    return (
        f'<w:r><w:drawing><a:graphic><a:graphicData uri="picture"><a:blip r:embed="{rid}"/>'
        "</a:graphicData></a:graphic></w:drawing></w:r>"
    )


def table(rows: list[list[str]]) -> str:
    body = "".join("<w:tr>" + "".join(f"<w:tc>{para(run(c))}</w:tc>" for c in row) + "</w:tr>" for row in rows)
    return f"<w:tbl>{body}</w:tbl>"


def text_box(choice: str, fallback: str) -> str:
    return (
        '<w:r><mc:AlternateContent><mc:Choice Requires="wps">'
        f"<w:p>{run(choice)}</w:p></mc:Choice><mc:Fallback><w:p>{run(fallback)}</w:p></mc:Fallback>"
        "</mc:AlternateContent></w:r>"
    )


def tracked(deleted: str, inserted: str) -> str:
    return (
        f"<w:del><w:r><w:delText>{escape(deleted)}</w:delText></w:r></w:del>"
        f"<w:ins><w:r><w:t>{escape(inserted)}</w:t></w:r></w:ins>"
    )


def core_xml(creator: str, created: str, revision: str) -> str:
    return (
        XML_HEAD + "<cp:coreProperties "
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>docx review selfcheck</dc:title><dc:creator>{escape(creator)}</dc:creator>"
        f"<cp:lastModifiedBy>{escape(creator)}</cp:lastModifiedBy><cp:revision>{revision}</cp:revision>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        '<dcterms:modified xsi:type="dcterms:W3CDTF">2026-09-13T00:00:00Z</dcterms:modified>'
        "</cp:coreProperties>"
    )


APP_XML = (
    XML_HEAD + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    "<Application>selfcheck</Application><Pages>1</Pages><Words>42</Words></Properties>"
)


def build_docx(path: Path, blocks: list[str], media: bytes, creator: str, created: str, revision: str) -> None:
    document = XML_HEAD + f"<w:document {NS_DECL}><w:body>{''.join(blocks)}<w:sectPr/></w:body></w:document>"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/document.xml", document)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/styles.xml", STYLES)
        zf.writestr("word/footnotes.xml", FOOTNOTES)
        zf.writestr("word/media/image1.png", media)
        zf.writestr("docProps/core.xml", core_xml(creator, created, revision))
        zf.writestr("docProps/app.xml", APP_XML)


def common_blocks(hold_sentence: str) -> list[str]:
    return [
        para(run("Design Document (selfcheck)"), style="Title"),
        para(run("1 Overview"), style="Heading1"),
        para(run(hold_sentence)),
        para(run("Value "), m_sub("V", "ref"), run(" is the reference; "), m_sum_frac()),
        para(run("def entry(o, x):"), style="Code"),
        table([["Item", "Status"], ["Row two", "Value two"]]),
        para(run("Figure 3: "), image("rId5")),
        para(tracked("old wording", "new wording"), run(" stays.")),
        para(text_box("box text", "box text")),
        para(run("See note"), '<w:r><w:footnoteReference w:id="1"/></w:r>'),
        para(),
    ]


def main() -> int:
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    with tempfile.TemporaryDirectory() as tmp:
        prev = Path(tmp) / "prev.docx"
        nxt = Path(tmp) / "next.docx"

        prev_blocks = common_blocks("The condition is checked before waiting.")
        prev_blocks.insert(3, para(run("This sentence is silently removed in the next version.")))
        build_docx(prev, prev_blocks, b"PNG-A", "THREAD Design Working Draft", "2026-09-12T21:24:00Z", "7")

        # -- extraction of the previous version ---------------------------------------
        lines, stats = extract_lines(str(prev))
        text = "\n".join(lines)
        check(lines[0] == "H0 Design Document (selfcheck)", f"title line: {lines[0]}")
        check("H1 1 Overview" in lines, "heading 1 line missing")
        check("P[Code] def entry(o, x):" in lines, "code paragraph missing")
        check("T[1.2] Row two | Value two" in lines, "table row missing")
        check("⟪V_{ref}⟫" in text, f"subscript rendering: {text}")
        check("⟪∑_{i=1}^{N}(q_{i}) + (a)/(b)⟫" in text, f"nary/fraction rendering: {text}")
        check("[image: media/image1.png]" in text, "image marker missing")
        check("old wording" not in text and "new wording stays." in text, "tracked changes handling")
        check(text.count("box text") == 1, "AlternateContent rendered twice or not at all")
        check("FN[1] Footnote body text." in lines, "footnote line missing")
        check(stats["heading"] == 2 and stats["table_row"] == 2 and stats["equation"] == 2, f"stats: {stats}")
        check(read_metadata(str(prev))["creator"] == "THREAD Design Working Draft", "metadata creator")

        # -- identical file ---------------------------------------------------------------
        report, summary = build_report(prev, prev, [], [])
        check(summary["identical"] and IDENTICAL_MARK in report, "identical files not detected")

        # -- next version with the regressions the procedure must catch --------------------
        prev_sha = sha256_of(prev)
        next_blocks = common_blocks("The condition is checked after waiting.")
        next_blocks.insert(3, para(run("1.1 New subsection"), style="Heading2"))
        next_blocks.insert(4, para(run("The new subsection introduces "), m_sub("k", "new")))
        next_blocks.append(para(run(f"Appendix: previous version SHA-256 {prev_sha[:16]}")))
        build_docx(nxt, next_blocks, b"PNG-B", "python-docx", "2013-12-23T23:15:00Z", "7")

        known = [{"version": "v1", "sha256_prefix": prev_sha[:16]}]
        report, summary = build_report(prev, nxt, known, ["V_{ref}"])
        check(not summary["identical"], "distinct files reported identical")
        check(summary["prev_known"]["version"] == "v1" and summary["next_known"] is None, "lineage lookup")
        check(summary["changed_media"] == ["word/media/image1.png"], f"media diff: {summary['changed_media']}")
        check(NO_MEDIA_CHANGE_MARK not in report, "media change not reported")
        warnings = "\n".join(summary["metadata_warnings"])
        check("creator が生成ツールの既定値" in warnings, f"creator regression not flagged: {warnings}")
        check("テンプレートの既定日付" in warnings, f"template date not flagged: {warnings}")
        check("revision が増えていない" in warnings, f"revision not flagged: {warnings}")
        check(summary["added_headings"] == ["H2 1.1 New subsection"], f"headings: {summary['added_headings']}")
        check(any("silently removed" in line for line in summary["removed"]), "silent deletion not listed")
        check(summary["new_symbols"] == {"k_{new}": 1}, f"new symbols: {summary['new_symbols']}")
        check(f"| `k_{{new}}` | 1 | {SINGLETON_MARK} |" in report, "singleton symbol not marked")
        check("| `V_{ref}` | 1 / 1 | 1 / 1 |" in report, "--symbol count table")
        check(summary["sha_chain_found"], "SHA-256 citation chain not found")

    print(f"selfcheck OK: {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
