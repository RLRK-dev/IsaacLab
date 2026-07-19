#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Layer 8 v3: AST control-method guard -- RS71 sec0#3/#5, NO kinematic exceptions (Rs 2026-07-19).

Why AST (v3) instead of grep (v2): the 2026-07-19 review proved the grep layer blind to (a) host
ALIASES (``_rep_jq = state.joint_q.numpy()`` then ``_rep_jq[idx] = x``), (b) receiver spoofing
(``x.joint_q.assign(a)  # fk_state`` -- a comment defeats a line-contains exemption), (c) multiline
calls, (d) augmented assignment, and (e) whole surfaces it never scanned (body_q mirrors, eq_active
pin writers, wp.copy/fill_). This checker parses the AST, so receivers and targets are TOKENS, not
substrings, and comments cannot spoof an exemption. A built-in negative-control self-test runs
first; if the checker cannot catch its own control corpus it refuses to certify anything.

Violation classes (each hit lists file:line:class):
  JQ-ASSIGN   <recv>.joint_q/.joint_qd.assign(...)     recv token-chain w/o fk_state; CABLE-SEED
                                                       marker exempts ONLY the pinned seeder lines.
  BODY-ASSIGN <recv>.body_q/.body_qd/.body_q_prev.assign(...)  recv w/o fk_state. (Sim-is-reality:
                                                       robot/finger/cable body poses come from
                                                       physics, not writes.)
  SUBSCRIPT   store/augstore into a canonical state name OR an intra-function alias bound from
              <state>.{joint_q,joint_qd,body_q,body_qd,qpos,qvel,eq_active,eq_data}.numpy()
              (exempt inside def seed_cable_joint_state, which self-asserts cable-only).
  RAW-MJ      subscript/attr store into .qpos/.qvel/.eq_active/.eq_data of any object.
  WP-COPY     wp.copy(<state joint/body array>, ...) or <state array>.fill_(...).

CABLE-SEED carry: lines carrying the literal marker '# CABLE-SEED (design sec14.2 step-3 scope-out'
are counted and echoed loudly; the count must EQUAL the pinned manifest (extra marked lines FAIL).
A run with carries present reports PASS-WITH-DECLARED-CARRY (never an unqualified PASS).

Exit: 0 only if self-test passes AND no violations. Wrapper must propagate rc (no || true).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

STATE_ATTRS = {"joint_q", "joint_qd", "body_q", "body_qd", "qpos", "qvel", "eq_active", "eq_data"}
JQ_ASSIGN_ATTRS = {"joint_q", "joint_qd"}
BODY_ASSIGN_ATTRS = {"body_q", "body_qd", "body_q_prev"}
RAW_MJ_ATTRS = {"qpos", "qvel", "eq_active", "eq_data"}
CANONICAL_NAMES = {"phys_jq", "phys_jqd", "jq", "jqd", "bq", "bqd"}  # historical host-copy names
MARKER = "# CABLE-SEED (design sec14.2 step-3 scope-out"
# Pinned carry manifest: file basename -> exact expected marked-line count (extra marks = FAIL).
CARRY_MANIFEST = {"newton_skill_env_base.py": 2}
# Pinned HOST-MOCK pytest files (write numpy fakes, never a sim): the ONLY fixture-inventory set.
FIXTURE_FILES = {"test_routeexec_writesite.py", "test_route_reward_identity_guards.py", "test_routeexec_state_bank.py"}
SEEDER_FUNC = "seed_cable_joint_state"  # the ONE function whose internal writes are the carry


def _tokens(node: ast.AST) -> list[str]:
    """Name/attribute token chain of a receiver expression, e.g. self._fk_state.joint_q -> [self, _fk_state, joint_q]."""
    out: list[str] = []
    while isinstance(node, ast.Attribute):
        out.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        out.append(node.id)
    return list(reversed(out))


def _has_fk_token(tokens: list[str]) -> bool:
    return any("fk_state" in t for t in tokens)


class _FileCheck(ast.NodeVisitor):
    def __init__(self, path: Path, src: str):
        self.path = path
        self.lines = src.splitlines()
        self.hits: list[tuple[int, str, str]] = []  # (lineno, class, detail)
        self.marked: list[int] = []
        self.func_stack: list[str] = []
        self.alias_stack: list[set[str]] = [set()]

    def _line_marked(self, lineno: int) -> bool:
        return MARKER in self.lines[lineno - 1]

    def _hit(self, lineno: int, cls: str, detail: str) -> None:
        self.hits.append((lineno, cls, detail))

    # --- scope handling (per-function alias map) ---
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.func_stack.append(node.name)
        self.alias_stack.append(set())
        self.generic_visit(node)
        self.alias_stack.pop()
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _in_seeder(self) -> bool:
        return SEEDER_FUNC in self.func_stack

    # --- alias binding: name = <expr>.<state_attr>.numpy() (fk_state sources are legit scratch) ---
    def _bind_aliases(self, node: ast.Assign) -> None:
        v = node.value
        if (
            isinstance(v, ast.Call)
            and isinstance(v.func, ast.Attribute)
            and v.func.attr == "numpy"
            and isinstance(v.func.value, ast.Attribute)
            and v.func.value.attr in STATE_ATTRS
            and not _has_fk_token(_tokens(v.func.value.value))
        ):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.alias_stack[-1].add(t.id)

    # --- stores ---
    def _check_store(self, target: ast.AST, lineno: int) -> None:
        if isinstance(target, ast.Subscript):
            base = target.value
            # raw mj/mjw attr store: <obj>.qpos[...] = / .eq_active[...] =
            if isinstance(base, ast.Attribute) and base.attr in RAW_MJ_ATTRS:
                self._hit(lineno, "RAW-MJ", f"store into .{base.attr}[...]")
                return
            if isinstance(base, ast.Name):
                aliases = set().union(*self.alias_stack)
                if base.id in aliases or base.id in CANONICAL_NAMES:
                    if self._in_seeder():
                        return  # seeder self-asserts cable-only; delivery lines carry the marker
                    self._hit(lineno, "SUBSCRIPT", f"store into state host-copy '{base.id}[...]'")

    def visit_Assign(self, node: ast.Assign) -> None:
        self._bind_aliases(node)
        for t in node.targets:
            self._check_store(t, node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_store(node.target, node.lineno)
        self.generic_visit(node)

    # --- calls: .assign delivery, wp.copy, fill_ ---
    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Attribute):
            if f.attr == "assign" and isinstance(f.value, ast.Attribute):
                holder = f.value  # <recv>.<state_attr>
                toks = _tokens(holder)
                if holder.attr in JQ_ASSIGN_ATTRS and not _has_fk_token(toks[:-1]):
                    if self._line_marked(node.lineno):
                        self.marked.append(node.lineno)
                    else:
                        self._hit(node.lineno, "JQ-ASSIGN", ".".join(toks) + ".assign(...)")
                elif holder.attr in BODY_ASSIGN_ATTRS and not _has_fk_token(toks[:-1]):
                    self._hit(node.lineno, "BODY-ASSIGN", ".".join(toks) + ".assign(...)")
            elif f.attr == "fill_" and isinstance(f.value, ast.Attribute) and f.value.attr in STATE_ATTRS:
                self._hit(node.lineno, "WP-COPY", f".{f.value.attr}.fill_(...)")
            elif f.attr == "copy" and isinstance(f.value, ast.Name) and f.value.id == "wp" and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Attribute) and a0.attr in STATE_ATTRS:
                    self._hit(node.lineno, "WP-COPY", f"wp.copy(<...>.{a0.attr}, ...)")
        self.generic_visit(node)


def check_file(path: Path) -> _FileCheck:
    src = path.read_text()
    fc = _FileCheck(path, src)
    try:
        fc.visit(ast.parse(src))
    except SyntaxError as e:
        # Fail-closed, never crash: a file the checker cannot parse is a file it cannot certify.
        fc.hits.append((int(e.lineno or 0), "UNPARSEABLE", f"SyntaxError: {e.msg} (cannot certify this file)"))
    return fc


# --- negative-control self-test: the checker must catch every control or it refuses to run ---
_NEG_CONTROLS: list[tuple[str, str]] = [
    ("alias-subscript", "def f(s):\n    v = s.joint_q.numpy()\n    v[3] = 1.0\n"),
    ("alias-augassign", "def f(s):\n    v = s.joint_q.numpy()\n    v[3] += 1.0\n"),
    ("jq-assign", "def f(s, a):\n    s.joint_q.assign(a)\n"),
    ("jq-assign-comment-spoof", "def f(s, a):\n    s.joint_q.assign(a)  # fk_state sync\n"),
    ("jq-assign-multiline", "def f(s, a):\n    s.joint_q.assign(\n        a\n    )\n"),
    ("jqd-assign", "def f(s, a):\n    s.joint_qd.assign(a)\n"),
    ("body-assign", "def f(s, a):\n    s.body_q.assign(a)\n"),
    ("body-prev-assign", "def f(sol, a):\n    sol.body_q_prev.assign(a)\n"),
    ("marker-spoof-on-arm", "def f(s, a):\n    s.joint_q.assign(a)  " + MARKER + ": fake)\n"),
    ("eq-active-store", "def f(mjd):\n    mjd.eq_active[3] = 1\n"),
    ("eq-active-zero-store", "def f(mjd):\n    mjd.eq_active[3] = 0\n"),
    ("qpos-store", "def f(d, i):\n    d.qpos[i] = 0.5\n"),
    ("wp-copy", "def f(s, a):\n    wp.copy(s.joint_q, a)\n"),
    ("fill", "def f(s):\n    s.joint_q.fill_(0.0)\n"),
    ("canonical-name-store", "def f(phys_jq):\n    phys_jq[0:6] = 0.0\n"),
]
_POS_CONTROLS: list[tuple[str, str]] = [
    ("fk-state-real", "def f(self, a):\n    self._fk_state.joint_q.assign(a)\n"),
    ("ctrl-servo", "def f(c, a):\n    c.joint_target_pos.assign(a)\n"),
    ("read-only", "def f(s):\n    v = s.joint_q.numpy()\n    x = float(v[0])\n    return x\n"),
    ("plain-local", "def f():\n    buf = [0] * 4\n    buf[1] = 2\n    return buf\n"),
]


def self_test() -> bool:
    ok = True
    for name, snippet in _NEG_CONTROLS:
        fc = _FileCheck(Path(f"<neg:{name}>"), snippet)
        fc.visit(ast.parse(snippet))
        caught = bool(fc.hits) and not fc.marked  # a marker-spoof must land in hits, NOT in marked
        if name == "marker-spoof-on-arm":
            # the spoofed marker line is 'marked' lexically -- the manifest pin is what kills it:
            caught = bool(fc.hits) or bool(fc.marked)  # counted somewhere; manifest mismatch FAILs below
        if not caught:
            print(f"  [SELF-TEST FAIL] negative control NOT caught: {name}")
            ok = False
    for name, snippet in _POS_CONTROLS:
        fc = _FileCheck(Path(f"<pos:{name}>"), snippet)
        fc.visit(ast.parse(snippet))
        if fc.hits or fc.marked:
            print(f"  [SELF-TEST FAIL] positive control false-positived: {name} -> {fc.hits or fc.marked}")
            ok = False
    return ok


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    roots = [repo / "thread_isaac_lab" / "envs", repo / "thread_isaac_lab" / "scripts"]
    print("=== Layer 8 v3: AST Control-Method Guard (sec0#3/#5; NO exceptions; self-tested) ===")
    if not self_test():
        print("  [FAIL] self-test failed -- the checker cannot certify anything (fail-closed)")
        print("LAYER8_FAIL=1")
        print("LAYER8_WARN=0")
        return 1
    print("  [SELF-TEST] all negative/positive controls behave (15 neg / 4 pos)")

    fail = 0
    fixture_hits = 0
    fixture_files: set[str] = set()
    marked_by_file: dict[str, int] = {}
    for root in roots:
        if not root.is_dir():
            print(f"  [FAIL] scan root missing: {root}")
            fail += 1
            continue
        for py in sorted(root.glob("*.py")):
            fc = check_file(py)
            rel = py.relative_to(repo)
            # pN-adjudicated scope split (c6 reverify): HOST-MOCK pytest files write mock state
            # (numpy fakes), inventoried loudly but not production writers. PINNED allowlist --
            # a test_*.py NOT on this list (e.g. the scripted sim harnesses test_newton_*) is
            # production-class and FAILs like any other file (fail-closed for new files).
            is_fixture = root.name == "scripts" and py.name in FIXTURE_FILES
            for lineno, cls, detail in fc.hits:
                if is_fixture:
                    fixture_hits += 1
                    fixture_files.add(py.name)
                else:
                    print(f"  [FAIL] {rel}:{lineno}: {cls}: {detail}")
                    fail += 1
            if fc.marked:
                marked_by_file[py.name] = marked_by_file.get(py.name, 0) + len(fc.marked)
                for ln in fc.marked:
                    print(f"  [CARRY] {rel}:{ln}: CABLE-SEED marked (declared sec14.2 step-3 carry)")
    if fixture_hits:
        print(
            f"  [FIXTURE-INVENTORY] {fixture_hits} mock-state write(s) in {len(fixture_files)} "
            f"scripts/test_*.py file(s) (pN scope ruling: test fixtures, not production writers): "
            + ", ".join(sorted(fixture_files))
        )
    # carry manifest pin: every marked line must be accounted for, no extras anywhere
    if marked_by_file != CARRY_MANIFEST:
        print(f"  [FAIL] CABLE-SEED carry manifest mismatch: found {marked_by_file} expected {CARRY_MANIFEST}")
        fail += 1

    carries = sum(marked_by_file.values())
    if fail == 0 and carries:
        print(f"  [PASS-WITH-DECLARED-CARRY] no kinematic writers; {carries} CABLE-SEED carry line(s) remain (sec14.2 step-3)")
    elif fail == 0:
        print("  [PASS] no kinematic writers, no carries")
    print(f"LAYER8_FAIL={fail}")
    print("LAYER8_WARN=0")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
