#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Aggregate thread-vault per-node state.md files into nest-snapshot.json for NEST Tracker viewer.

Adapter at load boundary: maps NEST LTM-1 v1.1 state.md frontmatter schema to viewer's NEST_Node schema.
- node_id -> id
- parent_node -> parent
- children_nodes -> children
- dependencies {precedent, blocker} -> flat string[]
- goal_verification -> means (fallback when no explicit means)
- session_history items normalized to {session_id, summary, ts}

Synthesizes missing nodes (T-ROOT virtual root + umbrella parents that have no own state.md).

Usage:
    python3 scripts/build_nest_snapshot.py
    # writes docs/nest-tracker/nest-snapshot.json
"""

import argparse
import fcntl
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
VAULT_ROOT = REPO / "thread_isaac_lab" / "thread-vault"
OUTPUT = REPO / "docs" / "nest-tracker" / "nest-snapshot.json"
MANIFEST = REPO / "thread_isaac_lab" / "thread-vault" / "00-Project-Management" / "project-tree-manifest.md"
GEN_BEGIN = "<!-- GEN:NEST:BEGIN (build_nest_snapshot.py; 手書き禁止) -->"
GEN_END = "<!-- GEN:NEST:END -->"

VALID_STATES = {"IN_PROGRESS", "COMPLETE", "DISCARDED", "ARCHIVED"}

T_ROOT_GOAL = (
    "Isaac Lab / SIM で 5-clip cable routing を vision-based で動作させ、最終/ultimate target として"
    " 95% 成功率へ改善する。現在の bar は rough/imperfect でも SIM で基本動作させること。"
    "real-world / physical UR15 × 2 deploy は current project scope ではない。"
    "REAL2SIM / sim-to-real は future consideration のみ。"
    "Foundation (robot mechanism / environment / cable) は厳密に構成する。"
)
T_ROOT_MEANS = (
    "知覚 (T-Vision) + 制御 (T-Skill) + 統合 (T-L1-B) + 経験基盤 (T-Empirical) + 失敗回復 (T-WM) の 5 capability axis"
)

UMBRELLA_GOALS = {
    "T-ROOT-COORD": ("CC#1 master coordinator (meta-node)", "T-ROOT"),
    "T-Skill": ("per-skill RL execution (capability axis L1.C)", "T-ROOT"),
    "T-Skill-GC": ("Grip-CLAMP skill mastery (umbrella、現 0% true stoch / 29.6% det best)", "T-Skill"),
    "T-Skill-IC": ("Insert Clip skill mastery (umbrella)", "T-Skill"),
    "T-Vision-Pose": ("per-clip pose estimation <5mm/10° (L1.A.1)", "T-Vision"),
    "T-Vision-CableState": ("40 segments cable state estimation <5mm error (L1.A.2)", "T-Vision"),
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Node ID format defined in LTM-1 §1 (v1.3); use with fullmatch.
LTM1_NODE_ID_RE = re.compile(r"T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
PENDING_TO_IN_PROGRESS = {"PENDING"}  # NEST has 'PENDING' but viewer enum lacks it; map to IN_PROGRESS


def _strip_inline_comment(s: str) -> str:
    return re.sub(r"\s+#.*$", "", s).strip()


def _parse_flow_sequence(s: str) -> list | None:
    """Parse a one-line YAML flow sequence such as ``[T-A, T-B]``; return None if ``s`` is not one."""
    s = s.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return None
    try:
        value = yaml.safe_load(s)
    except Exception:  # safe_load also raises ValueError/KeyError/RecursionError on odd tags and nesting
        return None
    return value if isinstance(value, list) else None


def _as_list(value) -> list:
    """Normalize a frontmatter list field without splitting a string into characters."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    if isinstance(value, dict):
        return list(value)
    if isinstance(value, str):
        seq = _parse_flow_sequence(value)
        if seq is not None:
            return seq
        return [value] if value.strip() else []
    return [value]


# Top-level keys whose value is a list (or a mapping of lists). On the fallback path their blocks are read as YAML.
_LIST_KEYS = {"children_nodes", "dependencies"}
# Node ID keys. On the fallback path they are read as YAML the same way, so quotes, ~ and comments read as in YAML.
_ID_KEYS = {"node_id", "parent_node"}


def _load_yaml_block(text: str) -> object:
    """Load one frontmatter block with yaml.safe_load; return None if it is not valid YAML on its own."""
    try:
        return yaml.safe_load(text)
    except Exception:  # safe_load also raises ValueError/KeyError/RecursionError on odd tags and nesting
        return None


def _parse_frontmatter_regex(body: str) -> dict:
    """Line-based fallback parser: top-level scalars + top-level arrays + 1-level nested arrays.

    Handles state.md frontmatter when YAML parse fails (typically due to embedded ': ' in values).
    A list key (children_nodes, dependencies) or an ID key (node_id, parent_node) is read differently: its block,
    from the key line up to the next line that looks like a top-level ``key:``, is loaded with yaml.safe_load on its
    own, and if that gives a mapping that holds the key, the value is used as is. The block then reads as YAML reads
    it alone; an anchor defined outside the block or a flow list continued at column 0 can still read differently
    from the whole file.
    Every other block uses the line reading, where nested structures beyond 1 level are skipped.
    Returns partial dict.
    """
    fm: dict = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m = re.match(r"^([a-zA-Z_][\w_-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if key in _LIST_KEYS or key in _ID_KEYS:
            # The block runs until the next top-level key line.
            j = i + 1
            while j < len(lines) and not re.match(r"^[a-zA-Z_][\w_-]*:", lines[j]):
                j += 1
            loaded = _load_yaml_block("\n".join(lines[i:j]))
            if isinstance(loaded, dict) and key in loaded:
                fm[key] = loaded[key]
                i = j
                continue
        # Strip inline comment for scalar detection (do NOT strip for "" check since empty implies block)
        val_clean = _strip_inline_comment(val) if val else val
        if val == "":
            # Block: check next lines for list or nested mapping
            j = i + 1
            items: list = []
            nested: dict = {}
            while j < len(lines):
                lj = lines[j]
                if lj.startswith("  - "):
                    item = _strip_inline_comment(lj[4:])
                    if item:
                        items.append(item)
                    j += 1
                elif lj.strip() == "":
                    j += 1
                elif re.match(r"^  [a-zA-Z_][\w_-]*:", lj):
                    nm = re.match(r"^  ([a-zA-Z_][\w_-]*):\s*(.*)$", lj)
                    if nm:
                        nkey = nm.group(1)
                        nval = nm.group(2).strip()
                        if nval == "[]":
                            nested[nkey] = []
                            j += 1
                        elif nval == "":
                            # Nested list under nested key
                            k = j + 1
                            n_items: list = []
                            while k < len(lines) and (lines[k].startswith("    - ") or lines[k].strip() == ""):
                                if lines[k].startswith("    - "):
                                    item = _strip_inline_comment(lines[k][6:])
                                    if item:
                                        n_items.append(item)
                                k += 1
                            nested[nkey] = n_items
                            j = k
                        else:
                            nested[nkey] = _strip_inline_comment(nval)
                            j += 1
                    else:
                        j += 1
                else:
                    break
            if items:
                fm[key] = items
            elif nested:
                fm[key] = nested
            else:
                fm[key] = ""
            i = j
        elif val_clean == "[]":
            fm[key] = []
            i += 1
        elif val_clean == "null":
            fm[key] = None
            i += 1
        else:
            fm[key] = val_clean
            i += 1
    return fm


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    body = m.group(1)
    # Try YAML first
    try:
        return yaml.safe_load(body)
    except yaml.YAMLError as e:
        # Fallback: regex line parser (handles embedded ': ' in values)
        print(f"  YAML failed ({e.__class__.__name__}), using regex fallback", file=sys.stderr)
        try:
            return _parse_frontmatter_regex(body)
        except Exception as e2:
            print(f"  Regex parse also failed: {e2}", file=sys.stderr)
            return None


def adapt(fm: dict) -> dict:
    """Map state.md frontmatter -> NEST_Node viewer schema."""
    deps = fm.get("dependencies") or {}
    if isinstance(deps, dict):
        flat_deps = _as_list(deps.get("precedent")) + _as_list(deps.get("blocker"))
    elif isinstance(deps, list):
        flat_deps = deps
    else:
        flat_deps = []

    sh_raw = fm.get("session_history") or []
    norm_sh = []
    for item in sh_raw:
        if not isinstance(item, dict):
            continue
        norm_sh.append(
            {
                "session_id": str(item.get("session_id", "")),
                "summary": str(item.get("summary") or item.get("progress") or item.get("phase") or ""),
                "ts": str(item.get("ts") or item.get("started") or ""),
            }
        )

    means = str(fm.get("means") or fm.get("goal_verification") or "")
    status = fm.get("status", "IN_PROGRESS")
    if status in PENDING_TO_IN_PROGRESS:
        # Map NEST's 'PENDING' (起動待ち) → viewer's 'IN_PROGRESS' (viewer enum lacks PENDING)
        status = "IN_PROGRESS"
    elif status not in VALID_STATES:
        print(
            f"  Warning: invalid status '{status}' on {fm.get('node_id', '?')}, defaulting to IN_PROGRESS",
            file=sys.stderr,
        )
        status = "IN_PROGRESS"

    parent = fm.get("parent_node")
    if parent in (None, "", "null"):
        parent = None
    else:
        parent = str(parent)

    children_raw = _as_list(fm.get("children_nodes"))

    # Node-ID filter for dependency/children values; looser than the LTM-1 §1 (v1.3) node_id format. Drops:
    # - list items that are mappings ('shared_with: T-Foo (...)'), read as a dict or collapsed to a string
    # - non-conformant state.md deps (descriptive strings like 'T-Skill-GC-EvalGap COMPLETE'
    #   or 'T-Skill-IC F1 WarmStart done (...)' which create spurious blockers in viewer)
    _NODE_ID_RE = re.compile(r"^T-[\w-]+$")

    def _is_node_id(s: str) -> bool:
        return bool(_NODE_ID_RE.match(s.strip()))

    return {
        "id": str(fm.get("node_id", "")),
        "goal": str(fm.get("goal", "")),
        "means": means,
        "status": status,
        "dependencies": [str(d).strip() for d in flat_deps if _is_node_id(str(d))],
        "parent": parent,
        "children": [str(c).strip() for c in children_raw if _is_node_id(str(c))],
        "session_history": norm_sh,
    }


def synthesize_stub(node_id: str, parent, children, goal: str = "(synthesized stub)", means: str = "") -> dict:
    return {
        "id": node_id,
        "goal": goal,
        "means": means,
        "status": "IN_PROGRESS",
        "dependencies": [],
        "parent": parent,
        "children": list(children),
        "session_history": [],
    }


def _status_norm(raw) -> str:
    """Comment-stripped, trimmed status token (verbatim otherwise; NO PENDING/invalid coercion)."""
    return re.sub(r"\s+#.*$", "", str(raw)).strip()


def parse_frontmatter_tracked(text: str):
    """Like parse_frontmatter but reports parse method: (data|None, 'yaml'|'regex'|'none')."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "none"
    body = m.group(1)
    try:
        return yaml.safe_load(body), "yaml"
    except yaml.YAMLError:
        try:
            return _parse_frontmatter_regex(body), "regex"
        except Exception:
            return None, "none"


def _load_skiplist() -> set:
    """Load nest_skiplist.txt (relpaths of non-node state.md files). Registered => INFO not HARD."""
    p = MANIFEST.parent / "nest_skiplist.txt"
    out = set()
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            entry = line.split("#", 1)[0].strip()
            if entry:
                out.add(entry)
    return out


# Reasons for a node_id / parent_node outside the LTM-1 §1 format (HARD on every node, as Rs1 (the human) decided).
_NODE_ID_FORMAT_REASON = (
    "does not match the LTM-1 §1 node ID format. LTM-1 §1 makes the node ID permanent, so the session responsible for"
    " this node stops with BLOCKED_FOR_USER and tells Rs1 (the human), who chooses a rename or a revision of LTM-1 §1;"
    " there is no exception list. Do not rename the node, blank node_id, change status, move the folder or add the"
    " file to nest_skiplist.txt."
)
_PARENT_NODE_FORMAT_REASON = (
    "does not match the LTM-1 §1 node ID format. Copy the parent node's node_id into parent_node exactly; if that"
    " node_id is itself outside the format, stop and tell Rs1 (the human). Do not blank parent_node."
)


def collect_state_nodes():
    """Scan */state.md + _archive/**/state.md for the manifest §2 view (strict SSOT).

    Returns (rows, manual_review):
      rows: [{id, status, parent, archived}] sorted by id; status verbatim (comment-stripped, no coercion).
      manual_review: [(severity, relpath, reason)]; SOFT = regex-fallback / non-canonical status,
      HARD = no node_id (skipped) / duplicate node_id / node_id or parent_node outside the LTM-1 §1 format, checked
      on the value as written (row kept).
    """
    rows, manual, seen = [], [], {}
    skip = _load_skiplist()
    files = sorted(VAULT_ROOT.glob("*/state.md")) + sorted(VAULT_ROOT.glob("_archive/**/state.md"))
    for sm in files:
        rel = str(sm.relative_to(VAULT_ROOT))
        archived = "_archive" in sm.parts
        fm, method = parse_frontmatter_tracked(sm.read_text(encoding="utf-8"))
        if method == "regex":
            manual.append(("SOFT", rel, "YAML parse failed -> regex fallback"))
        if not isinstance(fm, dict) or not fm.get("node_id"):
            if rel in skip:
                manual.append(("INFO", rel, "no node_id; in nest_skiplist.txt (intentional non-node)"))
            else:
                manual.append(
                    ("HARD", rel, "no frontmatter / no node_id -> skipped (add to nest_skiplist.txt if intentional)")
                )
            continue
        nid = str(fm.get("node_id")).strip()
        if nid in seen:
            manual.append(("HARD", rel, f"duplicate node_id {nid} (first at {seen[nid]})"))
            continue
        seen[nid] = rel
        status = _status_norm(fm.get("status", ""))
        if status and status not in VALID_STATES and status != "PENDING":
            manual.append(("SOFT", rel, f"non-canonical status '{status}' (kept verbatim)"))
        p = fm.get("parent_node")
        parent = str(p).strip() if p not in (None, "", "null") else "—"
        for field, value, reason in (
            ("node_id", str(fm.get("node_id")), _NODE_ID_FORMAT_REASON),
            ("parent_node", str(p), _PARENT_NODE_FORMAT_REASON),
        ):
            if (field == "node_id" or parent != "—") and not LTM1_NODE_ID_RE.fullmatch(value):
                manual.append(("HARD", rel, f"{field} {value!r} {reason}"))
        rows.append({"id": nid, "status": status or "(missing)", "parent": parent, "archived": archived})
    rows.sort(key=lambda r: r["id"])
    return rows, manual


def _md_cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def _atomic_write(path, text: str) -> None:
    """tempfile + os.replace atomic write (caller holds the flock)."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_gen_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _build_manifest_region():
    """Build the §2 GEN region string from state.md. Returns (region, rows, manual). Pure; no write."""
    rows, manual = collect_state_nodes()
    noncanon = sorted(
        {r["status"] for r in rows if r["status"] not in VALID_STATES and r["status"] not in ("PENDING", "(missing)")}
    )
    out = [GEN_BEGIN, ""]
    out.append(
        f"_{len(rows)} nodes — `build_nest_snapshot.py --emit-manifest-section` 生成 "
        "(SSOT = per-node state.md; 手書き禁止)。status = verbatim (coercion なし)。"
        "全 node 詳細/依存 = NEST jsx tracker + nest-snapshot.json。_"
    )
    out += ["", "| node_id | status | parent |", "|---|---|---|"]
    for r in rows:
        tag = " *(archived)*" if r["archived"] else ""
        out.append(f"| `{_md_cell(r['id'])}`{tag} | {_md_cell(r['status'])} | `{_md_cell(r['parent'])}` |")
    if noncanon:
        out += [
            "",
            f"_legend — 非正準 status (raw, coercion なし): {', '.join(noncanon)}. "
            "正準 = IN_PROGRESS / COMPLETE / DISCARDED / ARCHIVED (+ PENDING)._",
        ]
    out += ["", GEN_END]
    return "\n".join(out), rows, manual


def _report_manual(rows, manual, action) -> int:
    hard = [m for m in manual if m[0] == "HARD"]
    soft = [m for m in manual if m[0] == "SOFT"]
    info = [m for m in manual if m[0] == "INFO"]
    print(f"{action}: {len(rows)} nodes -> {MANIFEST.relative_to(REPO)}", file=sys.stderr)
    if manual:
        print(
            f"MANUAL-REVIEW ({len(hard)} HARD / {len(soft)} SOFT / {len(info)} INFO) — SOFT/INFO 非空は正常 "
            "(raw+legend / skiplist で対処, state.md 一括改変禁止):",
            file=sys.stderr,
        )
        for sev, path, reason in manual:
            print(f"  [{sev}] {path}: {reason}", file=sys.stderr)
    return 1 if hard else (2 if soft else 0)


def emit_manifest_section() -> int:
    """Regenerate manifest §2 GEN region (TERSE id|status|parent) from state.md. Strict SSOT emit.

    Exit: 0 clean / 2 soft review items (regex-fallback or non-canonical status; emit usable) /
    1 hard error (unregistered no-node_id skip / duplicate id / node_id or parent_node outside the LTM-1 §1 format /
    GEN markers missing). With a HARD data issue the region is still written before returning 1.
    """
    lockpath = MANIFEST.parent / ".manifest_gen.lock"
    with open(lockpath, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)  # Tier 3 flock over read-compute-write
        region, rows, manual = _build_manifest_region()
        text = MANIFEST.read_text(encoding="utf-8")
        if GEN_BEGIN not in text or GEN_END not in text:
            print(f"ERROR: GEN:NEST markers not found in {MANIFEST.relative_to(REPO)}", file=sys.stderr)
            return 1
        new_text = text[: text.index(GEN_BEGIN)] + region + text[text.index(GEN_END) + len(GEN_END) :]
        _atomic_write(MANIFEST, new_text)
    return _report_manual(rows, manual, "Emitted §2")


def check_manifest_section() -> int:
    """C3 helper: compare the current manifest §2 GEN region to the generator recompute. No write.

    Exit: 0 = in sync (SOFT review items allowed) / 1 = drift, GEN markers missing, or HARD data
    issue (unregistered no-node_id file / duplicate node_id / node_id or parent_node outside the LTM-1 §1 format).
    HARD grading mirrors emit so the automatic V9→layer-7 path cannot stay green while emit would refuse (M6 CC3-1
    fix): checker and emitter previously skipped identically, silently dropping e.g. a duplicated node's row.
    """
    region, rows, manual = _build_manifest_region()
    hard = [m for m in manual if m[0] == "HARD"]
    text = MANIFEST.read_text(encoding="utf-8")
    if GEN_BEGIN not in text or GEN_END not in text:
        print(f"C3 DRIFT: GEN:NEST markers not found in {MANIFEST.relative_to(REPO)}", file=sys.stderr)
        return 1
    current = text[text.index(GEN_BEGIN) : text.index(GEN_END) + len(GEN_END)]
    if current == region:
        if hard:
            print(
                f"C3-DATA: manifest §2 in sync but {len(hard)} HARD data issue(s) "
                "(same grading as emit; fix the state.md data):",
                file=sys.stderr,
            )
            for sev, path, reason in hard:
                print(f"  [{sev}] {path}: {reason}", file=sys.stderr)
            return 1
        print(f"C3 OK: manifest §2 GEN region in sync ({len(rows)} nodes)", file=sys.stderr)
        return 0
    print(
        "C3 DRIFT: manifest §2 GEN region != generator recompute (fix: build_nest_snapshot.py --emit-manifest-section)",
        file=sys.stderr,
    )
    return 1


def emit_map_index() -> int:
    """Reserved: regenerate a map node-index GEN region. No such region exists yet (M1 did not
    create one; the map's node views are iframe srcdoc where GEN markers are invalid). Deferred."""
    print(
        "--emit-map-index: 地図に GEN:NEST region 未定義 (M1 未作成; srcdoc 内 GEN 不可)。"
        "地図 node 索引の GEN 化は別 step (CP-B report で報告)。",
        file=sys.stderr,
    )
    return 3


def main() -> int:
    nodes_by_id: dict[str, dict] = {}

    # 1. Read all per-node state.md files
    state_files = sorted(VAULT_ROOT.glob("*/state.md"))
    print(f"Scanning {VAULT_ROOT} ...")
    for state_md in state_files:
        text = state_md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm:
            print(f"  Skip (no frontmatter): {state_md.relative_to(VAULT_ROOT)}", file=sys.stderr)
            continue
        if not isinstance(fm, dict) or not fm.get("node_id"):
            print(f"  Skip (no node_id): {state_md.relative_to(VAULT_ROOT)}", file=sys.stderr)
            continue
        node = adapt(fm)
        if node["id"] in nodes_by_id:
            print(f"  Warning: duplicate node_id {node['id']}, overwriting", file=sys.stderr)
        nodes_by_id[node["id"]] = node
        print(f"  Loaded: {node['id']} ({node['status']}, parent={node['parent']})")

    # 2. Synthesize stubs for missing referenced nodes
    referenced: set[str] = set()
    for n in nodes_by_id.values():
        if n["parent"]:
            referenced.add(n["parent"])
        for c in n["children"]:
            referenced.add(c)

    missing = referenced - set(nodes_by_id.keys())
    print(f"\nReferenced but missing: {sorted(missing)}")

    def _infer_parent(child_id: str):
        """Find parent by checking who lists child_id in their children_nodes."""
        for n in nodes_by_id.values():
            if child_id in n.get("children", []):
                return n["id"]
        return None

    for node_id in sorted(missing):
        # Children = nodes whose parent points to this stub
        stub_children = sorted(n["id"] for n in nodes_by_id.values() if n.get("parent") == node_id)
        # Inferred parent: who declares this node as their child?
        inferred_parent = _infer_parent(node_id)

        if node_id == "T-ROOT":
            stub = synthesize_stub("T-ROOT", parent=None, children=stub_children, goal=T_ROOT_GOAL, means=T_ROOT_MEANS)
        elif node_id in UMBRELLA_GOALS:
            goal, parent = UMBRELLA_GOALS[node_id]
            stub = synthesize_stub(node_id, parent=parent, children=stub_children, goal=goal)
        else:
            parent_for_stub = inferred_parent or "T-ROOT"
            stub = synthesize_stub(
                node_id,
                parent=parent_for_stub,
                children=stub_children,
                goal=f"(synthesized stub — no state.md found for {node_id})",
            )
        nodes_by_id[node_id] = stub
        print(f"  Synthesized: {node_id} (parent={stub['parent']}, {len(stub_children)} children)")

    # 3. Repair missing children: a parent's children list should include all nodes that name it as parent.
    # If a node's parent's children list is incomplete (e.g., parent's frontmatter children_nodes is stale),
    # union the declared list with the inferred-from-parent-pointer list.
    for parent_id, parent in nodes_by_id.items():
        inferred = set(n["id"] for n in nodes_by_id.values() if n.get("parent") == parent_id)
        declared = set(parent["children"])
        merged = sorted(declared | inferred)
        if merged != parent["children"]:
            added = sorted(inferred - declared)
            if added:
                print(f"  Repaired children of {parent_id}: +{added}")
            parent["children"] = merged

    # 4. Sort + validate
    nodes = sorted(nodes_by_id.values(), key=lambda n: n["id"])
    for n in nodes:
        for c in n["children"]:
            if c not in nodes_by_id:
                print(f"  Warning: {n['id']} references missing child {c}", file=sys.stderr)
        if n["parent"] and n["parent"] not in nodes_by_id:
            print(f"  Warning: {n['id']} references missing parent {n['parent']}", file=sys.stderr)

    # 5. Write output
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"nodes": nodes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {s: sum(1 for n in nodes if n["status"] == s) for s in VALID_STATES}
    print(f"\nWrote {len(nodes)} nodes to {OUTPUT.relative_to(REPO)}")
    print(f"Status summary: {summary}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="NEST snapshot / manifest §2 generator")
    ap.add_argument(
        "--emit-manifest-section",
        action="store_true",
        help="regenerate manifest §2 GEN region from state.md (TERSE id|status|parent, strict SSOT)",
    )
    ap.add_argument(
        "--check-manifest-section",
        action="store_true",
        help="C3: check manifest §2 GEN region == generator recompute (no write; exit 1 on drift)",
    )
    ap.add_argument(
        "--emit-map-index",
        action="store_true",
        help="(reserved/dropped) map node-index GEN region — see design §10; map keeps a static pointer",
    )
    args = ap.parse_args()
    if args.emit_manifest_section:
        sys.exit(emit_manifest_section())
    if args.check_manifest_section:
        sys.exit(check_manifest_section())
    if args.emit_map_index:
        sys.exit(emit_map_index())
    sys.exit(main())
