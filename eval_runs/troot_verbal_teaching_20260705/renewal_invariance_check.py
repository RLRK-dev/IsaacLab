#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Canonical-invariance check for the 07-Design renewal.

Node: ``T-ROOT-DesignDoc-Renewal-20260711``. This is **prep artifact 1** (the
invariance script) of the batch-C freeze group, implementing the four-layer
design in ``RENEWAL_PLAN_07DESIGN.md`` §5. It verifies that a structural
renewal of a design doc changed *structure only* and left every canonical
value/decision/anchor intact.

Layers (see RENEWAL_PLAN §5):

* **Layer 1 — canonical-block verbatim hash (§5-1).** Each pre-registered
  canonical block is located by *content anchors* (not line numbers, so
  relocation within the doc is allowed), normalized, and SHA256-hashed;
  pre vs post mismatch = FAIL. Content change = FAIL, pure relocation = PASS.
* **Layer 2 — partition-aware multiset (§5-2).** Outside the canonical blocks
  (the "remainder"), number tokens (U+2212 / full-width aware) and hex anchors
  (whole-string) are compared as multisets pre vs post — a value swap or a
  digit-level sha corruption breaks equality. A separate *presence* guarantee
  requires every declared canonical value to still appear in the post ACTIVE
  partition, catching a silent ACTIVE->HISTORICAL demotion that a plain
  multiset would miss.
* **Layer 3 — prose preservation (§5-3).** The normalized non-empty-line
  multiset must not lose any pre line (relocation OK, deletion FAIL). Guards
  the silent disappearance of historical prose that carries no numbers.
* **Layer 4 — anchor semantics (§5-4).** Pluggable structural checks (e.g. the
  43-step table still parses as 43 rows) so a numerically-invariant edit that
  strips an anchor's meaning is still caught.

Enforcement (§5-5): the exclusion regexes (context-anchored only) and the
ALLOWED-ADDITIONS list live in a *separate* config file (prep artifact 2), so
this logic can be frozen and sha-pinned independently of the doc-specific data.
This script embeds no doc-specific values; everything comes from ``--config``.
Because the drafter is also the executor, the intended workflow is: commit this
script + the config, obtain a %12/%9 review, sha-pin both, and only then edit
the doc — any later list change re-runs the full gate loudly.

``--self-test`` runs synthetic fixtures proving each failure mode (value swap,
canonical-block edit, deletion, sha corruption, ACTIVE->HISTORICAL demotion)
FAILs and each allowed transform (relocation, allowed-addition) PASSes, so a
reviewer can confirm the logic without the real config.

Usage::

    renewal_invariance_check.py --config CFG.json --pre <gitref|file> --post <file>
    renewal_invariance_check.py --self-test

Exit status: ``0`` all layers PASS; ``1`` any layer FAIL (loud diff printed);
``2`` usage / IO / config error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter

# --------------------------------------------------------------------------- #
# Normalization (pre-registered; RENEWAL_PLAN §5-2 token classes)
# --------------------------------------------------------------------------- #

_U2212 = "−"  # MINUS SIGN -> ASCII '-'
_FULLWIDTH_DIGITS = {0xFF10 + i: str(i) for i in range(10)}  # '０'..'９' -> '0'..'9'
_ENDASH = "–"  # EN DASH (range separator)

# Number token AFTER digit/minus normalization (ASCII only at that point).
_NUMBER_RE = re.compile(r"[+-]?\d+\.?\d*(?:[eE][+-]?\d+)?")
# Hex anchor: whole-string 8..64 lowercase hex (sha class), not glued to more hex.
_HEX_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{8,64}(?![0-9a-fA-F])")
# Bare (context-free) exclusion patterns forbidden by §5-5.
_BARE_FORBIDDEN = (r":\d+", r"\d{4}-\d{2}-\d{2}", r":[0-9]+", r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def normalize_digits_minus(text: str, *, endash_range: bool = True) -> str:
    """Fold U+2212 and full-width digits (and optionally en-dash) to ASCII.

    Args:
        text: Raw text.
        endash_range: If set, fold en-dash to ASCII hyphen (range separator).

    Returns:
        Text with minus/digit variants folded to ASCII for token extraction.
    """
    text = text.replace(_U2212, "-")
    if endash_range:
        text = text.replace(_ENDASH, "-")
    return text.translate(_FULLWIDTH_DIGITS)


def normalize_line(line: str, *, endash_range: bool = True) -> str:
    """Normalize a line for the prose/line multiset (§5-3).

    Folds digit/minus variants, collapses internal whitespace runs to a single
    space, and strips leading/trailing whitespace. Chosen normalizations are
    fixed (pre-registered) so the comparison is stable.
    """
    line = normalize_digits_minus(line, endash_range=endash_range)
    return re.sub(r"[ \t　]+", " ", line).strip()


def normalize_number_token(tok: str, *, strip_trailing_zeros: bool) -> str:
    """Normalize a single numeric token (leading '+', optional trailing zeros)."""
    if tok.startswith("+"):
        tok = tok[1:]
    if strip_trailing_zeros and "." in tok and "e" not in tok.lower():
        tok = tok.rstrip("0").rstrip(".")
    return tok


# --------------------------------------------------------------------------- #
# IO / region helpers
# --------------------------------------------------------------------------- #


def load_pre(pre_arg: str, doc_path: str) -> str:
    """Load the pre-renewal text.

    If ``pre_arg`` is an existing file it is read directly; otherwise it is
    treated as a git ref and ``git show <ref>:<doc_path>`` is used.
    """
    if os.path.isfile(pre_arg):
        with open(pre_arg, encoding="utf-8") as handle:
            return handle.read()
    try:
        out = subprocess.run(
            ["git", "show", f"{pre_arg}:{doc_path}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - IO path
        raise SystemExit(f"[config] cannot load pre '{pre_arg}:{doc_path}': {exc.stderr.strip()}")
    return out.stdout


def _find_anchor(lines: list[str], anchor: str, *, what: str) -> int:
    """Return the unique 0-based index of the line containing ``anchor``."""
    hits = [i for i, ln in enumerate(lines) if anchor in ln]
    if not hits:
        raise SystemExit(f"[config] {what} anchor not found: {anchor!r}")
    if len(hits) > 1:
        raise SystemExit(f"[config] {what} anchor not unique ({len(hits)} hits): {anchor!r}")
    return hits[0]


def extract_block(text: str, start_anchor: str, end_anchor: str) -> tuple[str, tuple[int, int]]:
    """Extract the canonical block between (inclusive) start/end anchors.

    Returns the block text and the (start, end_exclusive) line indices so the
    caller can excise it from the remainder.
    """
    lines = text.splitlines()
    start = _find_anchor(lines, start_anchor, what="block-start")
    end = _find_anchor(lines, end_anchor, what="block-end")
    if end < start:
        raise SystemExit(f"[config] block end precedes start: {start_anchor!r} / {end_anchor!r}")
    return "\n".join(lines[start : end + 1]), (start, end + 1)


def remainder_after_blocks(text: str, block_spans: list[tuple[int, int]]) -> str:
    """Return the doc text with the given (start, end_exclusive) spans removed."""
    lines = text.splitlines()
    drop = set()
    for start, end in block_spans:
        drop.update(range(start, end))
    return "\n".join(ln for i, ln in enumerate(lines) if i not in drop)


def split_partition(text: str, marker: str | None) -> tuple[str, str]:
    """Split text into (ACTIVE, HISTORICAL) at the first line matching ``marker``."""
    if not marker:
        return text, ""
    pat = re.compile(marker)
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if pat.search(ln):
            return "\n".join(lines[:i]), "\n".join(lines[i:])
    return text, ""


def apply_exclusions(text: str, exclusions: list[str]) -> str:
    """Strip context-anchored exclusion matches (e.g. line cites) before tokenizing."""
    for pat in exclusions:
        text = re.sub(pat, " ", text)
    return text


# --------------------------------------------------------------------------- #
# Token multisets
# --------------------------------------------------------------------------- #


def number_multiset(text: str, exclusions: list[str], *, strip_trailing_zeros: bool, endash_range: bool) -> Counter:
    """Multiset of normalized numeric tokens after applying exclusions."""
    text = apply_exclusions(text, exclusions)
    text = normalize_digits_minus(text, endash_range=endash_range)
    toks = [normalize_number_token(t, strip_trailing_zeros=strip_trailing_zeros) for t in _NUMBER_RE.findall(text)]
    return Counter(t for t in toks if t not in ("", "-", "+"))


def hex_multiset(text: str, exclusions: list[str]) -> Counter:
    """Multiset of whole-string hex anchors (sha class) after exclusions."""
    return Counter(_HEX_RE.findall(apply_exclusions(text, exclusions)))


def nonempty_line_multiset(text: str, *, endash_range: bool, exclusions: list[str] | None = None) -> Counter:
    """Multiset of normalized non-empty lines (prose-preservation, §5-3).

    Context-anchored exclusions (§5-5) are applied per line so that a line whose
    only change is a legitimately-shifting cite line-number is treated as
    unchanged rather than as a deletion+addition.
    """
    exclusions = exclusions or []
    out: Counter = Counter()
    for ln in text.splitlines():
        nl = normalize_line(apply_exclusions(ln, exclusions), endash_range=endash_range)
        if nl:
            out[nl] += 1
    return out


# --------------------------------------------------------------------------- #
# Layers
# --------------------------------------------------------------------------- #


def _norm_block(text: str, *, endash_range: bool) -> str:
    """Normalize a canonical block for hashing (line-normalized, join)."""
    return "\n".join(normalize_line(ln, endash_range=endash_range) for ln in text.splitlines())


def layer1_blocks(pre: str, post: str, cfg: dict, fails: list[str]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Layer 1 (§5-1): canonical-block verbatim hash. Returns pre/post spans."""
    endash = cfg["normalization"].get("endash_range", True)
    pre_spans: list[tuple[int, int]] = []
    post_spans: list[tuple[int, int]] = []
    for block in cfg.get("canonical_blocks", []):
        bid = block["id"]
        pre_txt, pre_span = extract_block(pre, block["start_anchor"], block["end_anchor"])
        post_txt, post_span = extract_block(post, block["start_anchor"], block["end_anchor"])
        pre_spans.append(pre_span)
        post_spans.append(post_span)
        h_pre = hashlib.sha256(_norm_block(pre_txt, endash_range=endash).encode()).hexdigest()
        h_post = hashlib.sha256(_norm_block(post_txt, endash_range=endash).encode()).hexdigest()
        if h_pre != h_post:
            fails.append(f"L1 block '{bid}': content changed (pre {h_pre[:12]} != post {h_post[:12]})")
    return pre_spans, post_spans


def layer2_multiset(pre: str, post: str, cfg: dict, pre_spans, post_spans, fails: list[str]) -> None:
    """Layer 2 (§5-2): number/hex multiset equality + ACTIVE presence."""
    norm = cfg["normalization"]
    stz = norm.get("strip_trailing_zeros", False)
    endash = norm.get("endash_range", True)
    excl = cfg.get("exclusion_regexes", [])
    allowed_text = "\n".join(cfg.get("allowed_additions", []))

    pre_rem = remainder_after_blocks(pre, pre_spans)
    post_rem = remainder_after_blocks(post, post_spans)

    # 5-2a: number multiset equality (swap / corruption catch), allowed-additions credited.
    pre_num = number_multiset(pre_rem, excl, strip_trailing_zeros=stz, endash_range=endash)
    post_num = number_multiset(post_rem, excl, strip_trailing_zeros=stz, endash_range=endash)
    allow_num = number_multiset(allowed_text, excl, strip_trailing_zeros=stz, endash_range=endash)
    removed = pre_num - post_num
    added = post_num - pre_num - allow_num
    if removed:
        fails.append(f"L2 number removed/changed: {dict(removed)}")
    if added:
        fails.append(f"L2 number added (not in allowed-additions): {dict(added)}")

    # 5-2c: hex (sha anchor) multiset equality.
    pre_hex = hex_multiset(pre_rem, excl)
    post_hex = hex_multiset(post_rem, excl)
    allow_hex = hex_multiset(allowed_text, excl)
    hx_removed = pre_hex - post_hex
    hx_added = post_hex - pre_hex - allow_hex
    if hx_removed:
        fails.append(f"L2 hex anchor removed/changed: {dict(hx_removed)}")
    if hx_added:
        fails.append(f"L2 hex anchor added (not in allowed-additions): {dict(hx_added)}")

    # 5-2b: presence of canonical values in the post ACTIVE partition.
    # Token-boundary match (not bare substring): a canonical value must appear
    # as a standalone numeric token, so demoting e.g. "1.12" to HISTORICAL is
    # NOT masked by a superstring like "1.125" lingering in ACTIVE (verified
    # adversarial case ADV-2). Leading (?<![\d.]) rejects a preceding digit/dot
    # (11.12), trailing (?![\d]) rejects a following digit (1.125) while still
    # allowing a trailing period/space (value at end of sentence).
    active, _hist = split_partition(post_rem, cfg.get("partition_marker"))
    active_norm = normalize_digits_minus(active, endash_range=endash)
    for cv in cfg.get("canonical_values", []):
        val = normalize_digits_minus(str(cv["value"]), endash_range=endash)
        if not re.search(r"(?<![\d.])" + re.escape(val) + r"(?![\d])", active_norm):
            fails.append(f"L2 presence: canonical value '{cv['id']}'={cv['value']} absent from post ACTIVE partition")


def layer3_prose(pre: str, post: str, cfg: dict, fails: list[str]) -> None:
    """Layer 3 (§5-3): no non-empty pre line may vanish (relocation OK)."""
    endash = cfg["normalization"].get("endash_range", True)
    excl = cfg.get("exclusion_regexes", [])
    pre_lines = nonempty_line_multiset(pre, endash_range=endash, exclusions=excl)
    post_lines = nonempty_line_multiset(post, endash_range=endash, exclusions=excl)
    allow_lines = nonempty_line_multiset("\n".join(cfg.get("allowed_additions", [])), endash_range=endash, exclusions=excl)
    # A pre line may legitimately be dropped only if it is an allowed-addition
    # (e.g. a stale banner replaced by its allowed successor is out of scope here).
    deleted = (pre_lines - post_lines) - allow_lines
    if deleted:
        preview = list(deleted.elements())[:6]
        fails.append(f"L3 prose deleted ({sum(deleted.values())} line(s)); e.g. {preview}")


def layer4_anchors(post: str, cfg: dict, fails: list[str]) -> None:
    """Layer 4 (§5-4): pluggable structural anchor-semantics checks."""
    for chk in cfg.get("anchor_checks", []):
        cid = chk["id"]
        region_txt = _resolve_region(post, chk["region"], cfg)
        if chk["type"] == "table_row_count":
            rows = _count_table_data_rows(region_txt)
            if rows != chk["expect"]:
                fails.append(f"L4 anchor '{cid}': table rows {rows} != expected {chk['expect']}")
        elif chk["type"] == "regex_count":
            n = len(re.findall(chk["pattern"], region_txt))
            if n != chk["expect"]:
                fails.append(f"L4 anchor '{cid}': regex hits {n} != expected {chk['expect']}")
        else:  # pragma: no cover - config error
            raise SystemExit(f"[config] unknown anchor_check type: {chk['type']}")


def _resolve_region(post: str, region: str, cfg: dict) -> str:
    """Resolve an anchor-check region spec to text."""
    if region == "whole":
        return post
    if region.startswith("canonical_block:"):
        bid = region.split(":", 1)[1]
        for block in cfg.get("canonical_blocks", []):
            if block["id"] == bid:
                txt, _ = extract_block(post, block["start_anchor"], block["end_anchor"])
                return txt
        raise SystemExit(f"[config] anchor_check region references unknown block: {bid}")
    raise SystemExit(f"[config] unknown anchor_check region: {region}")


def _count_table_data_rows(text: str) -> int:
    """Count markdown table *data* rows (leading '|', excluding header + separator)."""
    rows = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    out = 0
    for ln in rows:
        cells = ln.strip().strip("|")
        if re.fullmatch(r"[\s:|-]+", cells):  # separator row (---|:--:)
            continue
        out += 1
    # subtract 1 header row per contiguous table is left to the config's `expect`;
    # here we return raw data-ish rows and let expect encode the convention.
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def validate_config(cfg: dict) -> None:
    """Reject config that violates §5-5 (bare exclusion patterns, missing keys)."""
    cfg.setdefault("normalization", {})
    for pat in cfg.get("exclusion_regexes", []):
        if pat.strip() in _BARE_FORBIDDEN:
            raise SystemExit(f"[config] bare context-free exclusion forbidden (§5-5): {pat!r}")
    for block in cfg.get("canonical_blocks", []):
        for key in ("id", "start_anchor", "end_anchor"):
            if key not in block:
                raise SystemExit(f"[config] canonical_block missing '{key}': {block}")


def check_json_sha_invariant(cfg: dict, fails: list[str]) -> None:
    """Optionally assert full_43step.json is byte-identical to a pinned sha (§5)."""
    pin = cfg.get("json_sha_invariant")
    if not pin:
        return
    path = pin["path"]
    if not os.path.isfile(path):
        fails.append(f"json-invariant: {path} missing")
        return
    with open(path, "rb") as handle:
        actual = hashlib.sha256(handle.read()).hexdigest()
    if actual != pin["sha256"]:
        fails.append(f"json-invariant: {path} sha {actual[:12]} != pinned {pin['sha256'][:12]}")


def run_check(cfg: dict, pre: str, post: str) -> list[str]:
    """Run all four layers; return the list of failure strings (empty = PASS)."""
    validate_config(cfg)
    fails: list[str] = []
    pre_spans, post_spans = layer1_blocks(pre, post, cfg, fails)
    layer2_multiset(pre, post, cfg, pre_spans, post_spans, fails)
    layer3_prose(pre, post, cfg, fails)
    layer4_anchors(post, cfg, fails)
    check_json_sha_invariant(cfg, fails)
    return fails


def _report(doc: str, fails: list[str]) -> int:
    """Print a loud PASS/FAIL report; return the process exit code."""
    if not fails:
        print(f"[renewal-invariance] {doc}: ALL LAYERS PASS")
        return 0
    print(f"[renewal-invariance] {doc}: FAIL ({len(fails)} finding(s)) — STOP, do not commit renewal edit")
    for f in fails:
        print(f"  ✗ {f}")
    return 1


# --------------------------------------------------------------------------- #
# Self-test (synthetic fixtures; RENEWAL_PLAN §5 failure modes)
# --------------------------------------------------------------------------- #

_SELF_CFG = {
    "normalization": {"strip_trailing_zeros": False, "endash_range": True},
    "partition_marker": r"^## HISTORICAL",
    "canonical_blocks": [
        {"id": "tbl", "start_anchor": "<<CANON-START>>", "end_anchor": "<<CANON-END>>"},
    ],
    "canonical_values": [{"id": "z-home", "value": "1.12"}],
    "exclusion_regexes": [r"design\.md:[0-9]+"],
    "allowed_additions": ["> BANNER add-only 92.2 line"],
    "anchor_checks": [
        {"id": "tbl-rows", "type": "regex_count", "region": "canonical_block:tbl", "pattern": r"STEP \d+", "expect": 2},
    ],
}

_SELF_PRE = """# Doc
intro line with cite design.md:1284 and value 1.12 here
<<CANON-START>>
STEP 1 z=1.07
STEP 2 z=1.05
<<CANON-END>>
active prose that must survive
## HISTORICAL
old note sha deadbeefcafe0001
"""


def _mk_post(**edits):
    """Build a post fixture from the pre, applying a named single edit."""
    lines = _SELF_PRE
    if edits.get("swap"):
        lines = lines.replace("value 1.12 here", "value 1.15 here")
    if edits.get("block_edit"):
        lines = lines.replace("STEP 1 z=1.07", "STEP 1 z=1.09")
    if edits.get("delete"):
        lines = lines.replace("active prose that must survive\n", "")
    if edits.get("sha"):
        lines = lines.replace("deadbeefcafe0001", "deadbeefcafe0002")
    if edits.get("demote"):
        lines = lines.replace("intro line with cite design.md:1284 and value 1.12 here\n", "")
        lines = lines.replace("## HISTORICAL\n", "## HISTORICAL\ndemoted value 1.12 here\n")
    if edits.get("relocate"):
        block = "<<CANON-START>>\nSTEP 1 z=1.07\nSTEP 2 z=1.05\n<<CANON-END>>\n"
        lines = lines.replace(block, "")
        lines = lines.rstrip("\n") + "\n" + block
    if edits.get("cite_shift"):
        lines = lines.replace("design.md:1284", "design.md:2301")
    if edits.get("allowed_add"):
        lines = lines.replace("# Doc\n", "# Doc\n> BANNER add-only 92.2 line\n")
    return lines


def _judge(name: str, should_fail: bool, needle: str | None, fails: list[str]) -> bool:
    """Print and score one self-test case; return True if it behaved."""
    got = bool(fails)
    verdict, ok = "PASS", True
    if got != should_fail:
        verdict, ok = "MISBEHAVE", False
    elif should_fail and needle and not any(needle in f for f in fails):
        verdict, ok = f"WRONG-LAYER(want {needle})", False
    print(f"  self-test {name:24s} expect={'FAIL' if should_fail else 'PASS':4s} -> {verdict}"
          + (f"  {fails}" if got else ""))
    return ok


# ADV-2 (hardening fix, p1 mechanical-leg): demote a canonical value while a
# numeric *superstring* stays in ACTIVE, with the demoted line moved intact, so
# L1 / L2-number / L3 all pass and only the token-boundary presence check can
# catch it. Before the fix this false-PASSed (substring match); it must FAIL now.
_ADV2_PRE = (
    "# Doc\nintro line value 1.12 here\ntolerance 1.125 stays active\n"
    "<<CANON-START>>\nSTEP 1 z=1.07\nSTEP 2 z=1.05\n<<CANON-END>>\n"
    "prose survives\n## HISTORICAL\nold note deadbeefcafe0001\n"
)
_ADV2_POST = (
    "# Doc\ntolerance 1.125 stays active\n"
    "<<CANON-START>>\nSTEP 1 z=1.07\nSTEP 2 z=1.05\n<<CANON-END>>\n"
    "prose survives\n## HISTORICAL\nold note deadbeefcafe0001\nintro line value 1.12 here\n"
)


def self_test() -> int:
    """Run synthetic fixtures; assert each failure / allowed mode behaves.

    Covers the four layers, the ADV-2 superstring-demotion evasion (the
    token-boundary presence hardening), and L4 / json-invariant coverage.
    """
    ok = True
    shared = [
        ("swap", True, "L2 number"),
        ("block_edit", True, "L1 block"),
        ("delete", True, "L3 prose"),
        ("sha", True, "L2 hex"),
        ("demote", True, "L2 presence"),
        ("relocate", False, None),
        ("cite_shift", False, None),
        ("allowed_add", False, None),
    ]
    for name, should_fail, needle in shared:
        post = _mk_post(**{name: True})
        ok = _judge(name, should_fail, needle, run_check(json.loads(json.dumps(_SELF_CFG)), _SELF_PRE, post)) and ok

    # ADV-2 superstring demotion -> must be caught by token-boundary presence.
    ok = _judge("adv2_superstring_demote", True, "L2 presence",
                run_check(json.loads(json.dumps(_SELF_CFG)), _ADV2_PRE, _ADV2_POST)) and ok

    # L4 coverage: unchanged doc but a wrong expected row count -> only L4 fires.
    cfg_l4 = json.loads(json.dumps(_SELF_CFG))
    cfg_l4["anchor_checks"][0]["expect"] = 99
    ok = _judge("l4_rowcount", True, "L4", run_check(cfg_l4, _SELF_PRE, _SELF_PRE)) and ok

    # json-invariant coverage: pinned json path missing -> json-invariant fires.
    cfg_json = json.loads(json.dumps(_SELF_CFG))
    cfg_json["json_sha_invariant"] = {"path": "/nonexistent/renewal_nope.json", "sha256": "00" * 32}
    ok = _judge("json_missing", True, "json-invariant", run_check(cfg_json, _SELF_PRE, _SELF_PRE)) and ok

    print(f"[self-test] {'ALL OK' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="07-Design renewal canonical-invariance check (RENEWAL_PLAN §5).")
    parser.add_argument("--config", help="JSON config (prep artifact 2): blocks/values/exclusions/allowed/anchors.")
    parser.add_argument("--pre", help="Pre-renewal source: an existing file, or a git ref (uses config 'doc' path).")
    parser.add_argument("--post", help="Post-renewal file (working-tree path).")
    parser.add_argument("--self-test", action="store_true", help="Run synthetic fixtures and exit.")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not (args.config and args.pre and args.post):
        parser.error("--config, --pre and --post are required unless --self-test")

    with open(args.config, encoding="utf-8") as handle:
        cfg = json.load(handle)
    doc = cfg.get("doc", args.post)
    pre = load_pre(args.pre, doc)
    with open(args.post, encoding="utf-8") as handle:
        post = handle.read()
    return _report(doc, run_check(cfg, pre, post))


if __name__ == "__main__":
    sys.exit(main())
