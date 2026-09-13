# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test cases for the NEST snapshot builder script."""

import json
from pathlib import Path

import pytest

import scripts.build_nest_snapshot as bns

# A value containing ": " makes yaml.safe_load fail for the whole frontmatter, so the fallback parser is used.
BREAKS_YAML = "goal: fix this: now\n"


def _parse(front: str, method: str) -> dict:
    fm, used = bns.parse_frontmatter_tracked("---\n" + front + "---\n")
    assert used == method
    return fm


def _fallback_node(front: str) -> dict:
    return bns.adapt(_parse("node_id: T-N\n" + BREAKS_YAML + front, "regex"))


@pytest.mark.parametrize(
    ("front", "field", "expected"),
    [
        ("dependencies:\n  precedent: [T-A, T-B]\n  blocker: []  # none\n", "dependencies", ["T-A", "T-B"]),
        ("children_nodes: [T-C, T-D]  # two children\n", "children", ["T-C", "T-D"]),
        ("children_nodes:  # declared below\n  - T-E  # first\n  - T-F\n", "children", ["T-E", "T-F"]),
        (
            "dependencies:\n  precedent:\n    - T-G  # note\n      # continued note\n    - T-H\n  blocker: []\n",
            "dependencies",
            ["T-G", "T-H"],
        ),
        ("dependencies:\n  # explanation\n  precedent: [T-I]\n  blocker: []\n", "dependencies", ["T-I"]),
        ("children_nodes: []\ndependencies:\n  precedent: []\n  blocker: []\n", "dependencies", []),
        ("dependencies:\n  precedent:\n  - T-A\n  # blockers\n  blocker:\n  - T-B\n", "dependencies", ["T-A", "T-B"]),
        ("dependencies:\n  precedent:\n    - \"T-A\"\n    - 'T-B'\n", "dependencies", ["T-A", "T-B"]),
        ("children_nodes: [T-A,\n  T-B]\n", "children", ["T-A", "T-B"]),
        ("children_nodes:\n- T-A\n- T-B\n", "children", ["T-A", "T-B"]),
        ("dependencies:\n  blocker: [T-D]\n  blocker: [T-E]\n", "dependencies", ["T-E"]),
        ("dependencies:\n  precedent:\n    - T-A\n      - waits on review\n", "dependencies", []),
    ],
    ids=[
        "nested-flow-lists",
        "top-level-flow-list",
        "comment-only-value",
        "comments-between-items",
        "comment-before-keys",
        "empty-lists",
        "pyyaml-dump-layout-with-comment",
        "quoted-items",
        "flow-list-over-two-lines",
        "items-at-column-0",
        "repeated-key-last-wins",
        "deeper-item-joins-the-string",
    ],
)
def test_fallback_reads_list_blocks_as_yaml(front, field, expected):
    """On the fallback path a valid children_nodes or dependencies block reads the same as the YAML path."""
    assert _fallback_node(front)[field] == expected
    assert bns.adapt(_parse("node_id: T-N\n" + front, "yaml"))[field] == expected


def test_fallback_invalid_list_block_keeps_line_reading():
    """A list block that is not valid YAML on its own is read line by line, as before YAML blocks were used."""
    assert _fallback_node("children_nodes:\n  T-M: note\n  # c\n  - T-A\n")["children"] == ["T-M"]
    assert _fallback_node("dependencies:\n  precedent:\n    - T-A\n  # c\n  - T-B\n")["dependencies"] == ["T-A"]


def test_fallback_scalar_keys_are_not_read_as_yaml():
    """Keys other than the list keys and node_id / parent_node are not loaded as YAML blocks."""
    fm = _parse("node_id: T-N\n" + BREAKS_YAML + "status: [COMPLETE]\n", "regex")
    assert fm["status"] == "[COMPLETE]"


def test_prose_is_not_read_as_refs():
    """Node IDs inside a sentence are not guessed as dependencies."""
    assert _fallback_node("dependencies: precedent = T-J (scoping) / blocker = something\n")["dependencies"] == []
    assert _fallback_node("dependencies:\n  precedent:\n    - waits for T-A to finish\n")["dependencies"] == []


def test_fallback_bad_flow_tag_keeps_node():
    """A list block that YAML cannot load does not drop the node."""
    node = _fallback_node("children_nodes: [!!int abc]\n")
    assert node["id"] == "T-N"
    assert node["children"] == []


def test_yaml_path_values_are_not_split():
    """A single string, a quoted flow list, a set or a number is read without splitting it into characters."""
    fm = _parse(
        "node_id: T-N\nchildren_nodes: !!set {T-A: null}\ndependencies:\n  precedent: T-C\n  blocker: '[T-D, T-E]'\n",
        "yaml",
    )
    node = bns.adapt(fm)
    assert node["children"] == ["T-A"]
    assert node["dependencies"] == ["T-C", "T-D", "T-E"]
    assert bns.adapt(_parse("node_id: T-N\nchildren_nodes: 7\n", "yaml"))["children"] == []
    node = bns.adapt({"node_id": "T-N", "dependencies": {"precedent": "T-K", "blocker": None}, "children_nodes": "T-L"})
    assert node["dependencies"] == ["T-K"]
    assert node["children"] == ["T-L"]


def test_snapshot_includes_fallback_refs(tmp_path, monkeypatch):
    """The snapshot written by main() carries children and dependencies read on the fallback path."""
    fronts = {
        "T-P": "node_id: T-P\n" + BREAKS_YAML + "status: COMPLETE\nchildren_nodes: [T-N]\n",
        "T-N": "node_id: T-N\n" + BREAKS_YAML + "status: IN_PROGRESS\ndependencies:\n  precedent: [T-P]\n",
    }
    vault = tmp_path / "vault"
    for name, front in fronts.items():
        _parse(front, "regex")
        (vault / name).mkdir(parents=True)
        (vault / name / "state.md").write_text("---\n" + front + "---\n", encoding="utf-8")
    output = tmp_path / "nest-snapshot.json"
    monkeypatch.setattr(bns, "REPO", tmp_path)
    monkeypatch.setattr(bns, "VAULT_ROOT", vault)
    monkeypatch.setattr(bns, "OUTPUT", output)
    assert bns.main() == 0
    nodes = {n["id"]: n for n in json.loads(output.read_text(encoding="utf-8"))["nodes"]}
    assert nodes["T-N"]["dependencies"] == ["T-P"]
    # T-N has no parent_node, so T-P's children can only come from T-P's own children_nodes.
    assert nodes["T-P"]["children"] == ["T-N"]


def _write_vault(vault: Path, fronts: dict[str, str]) -> None:
    for name, front in fronts.items():
        (vault / name).mkdir(parents=True, exist_ok=True)
        (vault / name / "state.md").write_text("---\n" + front + "---\n", encoding="utf-8")


def _scan(vault: Path, monkeypatch, fronts: dict[str, str]) -> tuple[list, list]:
    _write_vault(vault, fronts)
    monkeypatch.setattr(bns, "VAULT_ROOT", vault)
    monkeypatch.setattr(bns, "MANIFEST", vault.parent / "manifest.md")
    return bns.collect_state_nodes()


def _hard(manual: list) -> list[tuple[str, str]]:
    return sorted((path, reason.split()[0]) for severity, path, reason in manual if severity == "HARD")


@pytest.mark.parametrize(
    ("node_id", "valid"),
    [
        ("T-08-1-3", True),
        ("T-ROOT", True),
        ("T-a", True),
        ("T-", False),
        ("T--A", False),
        ("T-A-", False),
        ("T-A--B", False),
        ("t-A", False),
        ("X-A", False),
        ("T-A_B", False),
        ("T-A.B", False),
        ("T-A B", False),
        ("T-\uff11", False),
        ("T-\u00e9", False),
        ("T-A\n", False),
    ],
)
def test_ltm1_node_id_format(node_id, valid):
    """The format check follows LTM-1 §1: ASCII letters and digits joined by single hyphens after "T-"."""
    assert bool(bns.LTM1_NODE_ID_RE.fullmatch(node_id)) is valid


@pytest.mark.parametrize("folder", ["", "_archive/"])
@pytest.mark.parametrize(
    "status",
    [
        "IN_PROGRESS",
        "PENDING",
        "HOLD",
        "COMPLETE",
        "ARCHIVED",
        "DISCARDED",
        "COMPLETE_WITH_LIMITATION",
        "complete",
        None,
    ],
)
def test_manifest_scan_fails_ids_outside_ltm1_format_on_every_node(tmp_path, monkeypatch, status, folder):
    """A node_id or parent_node outside the LTM-1 §1 format is HARD whatever the status or folder; the row is kept."""
    status_line = "" if status is None else f"status: {status}\n"
    rows, manual = _scan(
        tmp_path / "vault",
        monkeypatch,
        {
            "T-Good": "node_id: T-Good\nstatus: IN_PROGRESS\n",
            folder + "T-bad_id": "node_id: T-bad_id\n" + status_line + "parent_node: T-Good (see notes)\n",
        },
    )
    assert [r["id"] for r in rows] == ["T-Good", "T-bad_id"]
    bad = folder + "T-bad_id/state.md"
    assert _hard(manual) == [(bad, "node_id"), (bad, "parent_node")]


def test_manifest_scan_format_reasons_say_how_to_fix(tmp_path, monkeypatch):
    """A node_id issue goes to Rs1 (the human); a parent_node issue is fixed by copying the parent's node_id."""
    _, manual = _scan(
        tmp_path / "vault",
        monkeypatch,
        {
            "T-Good": "node_id: T-Good\nstatus: IN_PROGRESS\n",
            "T-bad_id": "node_id: T-bad_id\nstatus: IN_PROGRESS\n",
            "T-Child": "node_id: T-Child\nstatus: IN_PROGRESS\nparent_node: T-Good (see notes)\n",
        },
    )
    reasons = {path: reason for severity, path, reason in manual if severity == "HARD"}
    assert set(reasons) == {"T-bad_id/state.md", "T-Child/state.md"}
    node_reason = reasons["T-bad_id/state.md"]
    assert node_reason.startswith("node_id 'T-bad_id' does not match the LTM-1 §1 node ID format.")
    for clause in (
        "stops with BLOCKED_FOR_USER and tells Rs1 (the human)",
        "chooses a rename or a revision of LTM-1 §1",
        "there is no exception list",
        "Do not rename the node, blank node_id, change status, move the folder or add the file to nest_skiplist.txt.",
    ):
        assert clause in node_reason
    parent_reason = reasons["T-Child/state.md"]
    assert parent_reason.startswith("parent_node 'T-Good (see notes)' does not match the LTM-1 §1 node ID format.")
    for clause in (
        "Copy the parent node's node_id into parent_node exactly",
        "stop and tell Rs1 (the human)",
        "Do not blank parent_node.",
    ):
        assert clause in parent_reason
    assert "rename" not in parent_reason


@pytest.mark.parametrize(
    ("front", "row", "hard"),
    [
        ('node_id: "T-Q"\nparent_node: ~\n', ("T-Q", "—"), []),
        ("node_id: T-Q  # comment\nparent_node: # none\n", ("T-Q", "—"), []),
        ("node_id: T-Q\nparent_node: Null\n", ("T-Q", "—"), []),
        ("node_id: T-Q\nparent_node: NULL\n", ("T-Q", "—"), []),
        ("node_id: T-Q\nparent_node: ''\n", ("T-Q", "—"), []),
        ("node_id: >-\n  T-Q\nparent_node: 'T-P'\n", ("T-Q", "T-P"), []),
        ("node_id: T-bad_x\n", ("T-bad_x", "—"), ["node_id"]),
        ("node_id: T-Q\nparent_node: T-P\n  (moved from T-O)\n", ("T-Q", "T-P (moved from T-O)"), ["parent_node"]),
    ],
    ids=["quoted-id", "comments", "Null", "NULL", "empty-quotes", "folded-id", "bad-id", "continuation-line"],
)
def test_manifest_scan_reads_id_lines_as_yaml_on_fallback(tmp_path, monkeypatch, front, row, hard):
    """On the fallback path node_id and parent_node read as on the YAML path, so only a real format issue is HARD."""
    for name, text in (("yaml", front), ("regex", BREAKS_YAML + front)):
        _parse(text, name)
        rows, manual = _scan(tmp_path / name, monkeypatch, {"T-Q": text})
        assert [(r["id"], r["parent"]) for r in rows] == [row], name
        assert [field for _, field in _hard(manual)] == hard, name


def test_manifest_scan_checks_ids_as_written(tmp_path, monkeypatch):
    """LTM-1 §1 applies to the whole value, so a quoted space, an ideographic space or a no-break space is HARD."""
    rows, manual = _scan(
        tmp_path / "vault",
        monkeypatch,
        {
            "T-A": 'node_id: "T-A "\nstatus: IN_PROGRESS\n',
            "T-B": "node_id: T-B\u3000\nstatus: IN_PROGRESS\nparent_node: T-A\u00a0\n",
        },
    )
    assert [(r["id"], r["parent"]) for r in rows] == [("T-A", "—"), ("T-B", "T-A")]
    assert _hard(manual) == [("T-A/state.md", "node_id"), ("T-B/state.md", "node_id"), ("T-B/state.md", "parent_node")]


def test_manifest_check_fails_on_id_format_until_fixed(tmp_path, monkeypatch, capsys):
    """The manifest check (Layer 7 C3) fails while a node_id is outside the LTM-1 §1 format, even on a COMPLETE node."""
    vault = tmp_path / "vault"
    _write_vault(vault, {"T-A": "node_id: T-A\nstatus: IN_PROGRESS\n", "T-B": "node_id: T-b.2\nstatus: COMPLETE\n"})
    manifest = tmp_path / "manifest.md"
    manifest.write_text(bns.GEN_BEGIN + "\n" + bns.GEN_END + "\n", encoding="utf-8")
    monkeypatch.setattr(bns, "REPO", tmp_path)
    monkeypatch.setattr(bns, "VAULT_ROOT", vault)
    monkeypatch.setattr(bns, "MANIFEST", manifest)
    assert bns.emit_manifest_section() == 1
    assert "`T-b.2`" in manifest.read_text(encoding="utf-8")
    capsys.readouterr()
    assert bns.check_manifest_section() == 1
    assert "C3-DATA" in capsys.readouterr().err
    _write_vault(vault, {"T-B": "node_id: T-B-2\nstatus: COMPLETE\n"})
    assert bns.emit_manifest_section() == 0
    assert bns.check_manifest_section() == 0
