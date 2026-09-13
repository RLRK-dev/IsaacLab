# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test cases for the NEST snapshot builder script."""

import json

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
    """Keys other than children_nodes and dependencies are not loaded as YAML blocks."""
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
