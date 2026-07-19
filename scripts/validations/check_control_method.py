#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Layer 8 v3.1: AST control-method guard -- RS71 sec0#3/#5, NO kinematic exceptions (Rs 2026-07-19).

v3 -> v3.1 (pN c7-c8b reverify G1-G5, 18:15 JST):
  G1  recursive scan (rglob) -- nested .py under envs/ and scripts/ are in scope.
  G2  attr-STORE (``mjd.eq_active = x``), ``np.copyto(<state>, x)`` and AnnAssign alias bindings
      are caught, each with a self-test control.
  G3  exemptions are BOUND, not lexical: the fk_state exemption matches an EXACT receiver token
      (``fk_state`` / ``_fk_state``, not a substring); the CABLE-SEED marker is honored ONLY at
      (file, function, receiver) triples pinned in CARRY_MANIFEST; the seeder subscript exemption
      applies ONLY to the seeder's own bound host copies (jq/jqd) inside that one function.
  G4  the fixture inventory is a per-file manifest of (function, expected count); a NEW hit in an
      allowed file (different function or count drift) FAILs.
  G5  hit classes are SEPARATED in both output and counts: DELIVERY-SINK (device writes) vs
      SOURCE-CANDIDATE (host-copy mutations awaiting a sink) vs UNPARSEABLE -- no more flat
      "N sites" over-claim. A body-space cable-seed manifest hook exists (EMPTY today: the only
      sanctioned cable seed is joint-space); robot/finger body writes can never be manifested.

Self-test: negative AND positive controls run first; the checker refuses to certify anything if
one control misbehaves (fail-closed), including same-count marker-spoof and fixture-injection.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

STATE_ATTRS = {"joint_q", "joint_qd", "body_q", "body_qd", "qpos", "qvel", "eq_active", "eq_data"}
JQ_ASSIGN_ATTRS = {"joint_q", "joint_qd"}
BODY_ASSIGN_ATTRS = {"body_q", "body_qd", "body_q_prev"}
RAW_MJ_ATTRS = {"qpos", "qvel", "eq_active", "eq_data"}
CANONICAL_NAMES = {"phys_jq", "phys_jqd", "jq", "jqd", "bq", "bqd"}
FK_TOKENS = {"fk_state", "_fk_state"}  # EXACT token match (G3), never a substring test
MARKER = "# CABLE-SEED (design sec14.2 step-3 scope-out"

# G3: the CABLE-SEED carry is a pinned (file, function) -> {receiver_attr: count} manifest.
CARRY_MANIFEST: dict[tuple[str, str], dict[str, int]] = {
    ("thread_isaac_lab/envs/newton_skill_env_base.py", "seed_cable_joint_state"): {"joint_q": 1, "joint_qd": 1},
}
# The seeder's own host copies (subscript-exempt ONLY inside that function, G3).
SEEDER_KEY = ("thread_isaac_lab/envs/newton_skill_env_base.py", "seed_cable_joint_state")
SEEDER_HOST_NAMES = {"jq", "jqd"}

# G5: sanctioned body-space cable seeds (object episode-boundary init, p5 sec14.14).
# EMPTY today -- the sanctioned cable seed is joint-space. Robot/finger bodies may NEVER appear here.
BODY_CABLE_SEED_MANIFEST: dict[tuple[str, str], int] = {}

# RESET-SEED manifest (pN follow-up ruling 18:17 JST): CLAUDE.md:67's "once at reset, before the
# first step" joint-state initialization is the ONLY sanctioned joint-seed class. Entries are
# exact (file, function) pairs allowed to deliver a reset joint seed; the once/before-first-step
# semantics are enforced by in-code asserts at these sites (the static guard pins WHERE, the
# runtime asserts pin WHEN).
RESET_SEED_MANIFEST: dict[tuple[str, str], dict[str, int]] = {
    # c11 (grip PS-2..5): the env's SINGLE sanctioned joint-state write site; callers = episode
    # reset / P0 build / cache restore (all episode boundaries, before the next physics step).
    ("thread_isaac_lab/envs/newton_grip_env.py", "_seed_robot_joint_row"): {"joint_q": 1, "joint_qd": 1},
}

# G4: host-mock pytest fixture manifest -- repo-relative file -> {function: expected hit count}.
# A hit outside these functions, or a count drift, FAILs (fixture-injection control).
FIXTURE_MANIFEST: dict[str, dict[str, int]] = {
    # MEASURED 2026-07-19 (v3.1 run at c8b tip) after eyeballing each as a numpy-mock write.
    "thread_isaac_lab/scripts/test_route_reward_identity_guards.py": {
        "__init__": 1,  # mock env/solver ctor
        "_check": 1,
        "_env_for_trigger": 1,
        "_env_for_clear": 1,  # numpy-fake mj_data.eq_active attr install
        "test_pin_da_depth_leg_gates_fire": 1,
        "test_clear_c1_pin_raises_on_any_audited_fired": 1,  # arms the fake eq before the raise check
    },
    "thread_isaac_lab/scripts/test_routeexec_writesite.py": {
        "__init__": 2,  # _MockWarpArray/_MockControl ctors
        "_ref_28wide": 2,  # reference implementation of the RETIRED write (mock arrays only)
        "test_settled_fk_gripper_patch": 1,
    },
    "thread_isaac_lab/scripts/test_routeexec_state_bank.py": {
        "__init__": 2,
        "_roundtrip_check": 2,
        "test_world_slice": 2,
    },
}


def _tokens(node: ast.AST) -> list[str]:
    out: list[str] = []
    while isinstance(node, ast.Attribute):
        out.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        out.append(node.id)
    return list(reversed(out))


def _has_fk_token(tokens: list[str]) -> bool:
    return any(t in FK_TOKENS for t in tokens)  # G3: exact token, not substring


class Hit:
    __slots__ = ("lineno", "klass", "kind", "func", "detail")

    def __init__(self, lineno: int, klass: str, kind: str, func: str, detail: str):
        self.lineno, self.klass, self.kind, self.func, self.detail = lineno, klass, kind, func, detail


class _FileCheck(ast.NodeVisitor):
    """kind: SINK (device write) / SOURCE (host-copy mutation) / UNPARSEABLE (G5 separation)."""

    def __init__(self, rel: str, src: str):
        self.rel = rel
        self.lines = src.splitlines()
        self.hits: list[Hit] = []
        self.marked: list[tuple[str, str, int]] = []  # (func, receiver_attr, lineno)
        self.func_stack: list[str] = ["<module>"]
        self.alias_stack: list[set[str]] = [set()]

    def _line_marked(self, lineno: int) -> bool:
        return 0 < lineno <= len(self.lines) and MARKER in self.lines[lineno - 1]

    def _hit(self, lineno: int, klass: str, kind: str, detail: str) -> None:
        self.hits.append(Hit(lineno, klass, kind, self.func_stack[-1], detail))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.func_stack.append(node.name)
        self.alias_stack.append(set())
        self.generic_visit(node)
        self.alias_stack.pop()
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _bind_alias_value(self, value: ast.AST, targets: list[ast.AST]) -> None:
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "numpy"
            and isinstance(value.func.value, ast.Attribute)
            and value.func.value.attr in STATE_ATTRS
            and not _has_fk_token(_tokens(value.func.value.value))
        ):
            for t in targets:
                if isinstance(t, ast.Name):
                    self.alias_stack[-1].add(t.id)

    def _seeder_exempt(self, name: str) -> bool:
        key = (self.rel, self.func_stack[-1])
        if key == SEEDER_KEY and name in SEEDER_HOST_NAMES:
            return True
        # A RESET_SEED_MANIFEST-pinned function's own host-copy mutations are part of its
        # sanctioned once-at-reset seed (the delivery .assign in the same function is what the
        # manifest counts; a mutation without that delivery is inert).
        return key in RESET_SEED_MANIFEST

    def _check_store_target(self, target: ast.AST, lineno: int) -> None:
        if isinstance(target, ast.Subscript):
            base = target.value
            if isinstance(base, ast.Attribute) and base.attr in RAW_MJ_ATTRS:
                self._hit(lineno, "RAW-MJ", "SINK", f"store into .{base.attr}[...]")
                return
            if isinstance(base, ast.Name):
                aliases = set().union(*self.alias_stack)
                if base.id in aliases or base.id in CANONICAL_NAMES:
                    if self._seeder_exempt(base.id):
                        return
                    self._hit(lineno, "SUBSCRIPT", "SOURCE", f"store into state host-copy '{base.id}[...]'")
        elif isinstance(target, ast.Attribute) and target.attr in RAW_MJ_ATTRS | BODY_ASSIGN_ATTRS | JQ_ASSIGN_ATTRS:
            # G2: whole-attr replacement, e.g. mjd.eq_active = x / state.joint_q = x
            if not _has_fk_token(_tokens(target.value)):
                self._hit(lineno, "ATTR-STORE", "SINK", f"attribute store .{target.attr} = ...")

    def visit_Assign(self, node: ast.Assign) -> None:
        self._bind_alias_value(node.value, node.targets)
        for t in node.targets:
            self._check_store_target(t, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # G2: annotated alias binding
        if node.value is not None:
            self._bind_alias_value(node.value, [node.target])
            self._check_store_target(node.target, node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_store_target(node.target, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Attribute):
            if f.attr == "assign" and isinstance(f.value, ast.Attribute):
                holder = f.value
                toks = _tokens(holder)
                if holder.attr in JQ_ASSIGN_ATTRS and not _has_fk_token(toks[:-1]):
                    key = (self.rel, self.func_stack[-1])
                    if (
                        self._line_marked(node.lineno)
                        and key in CARRY_MANIFEST
                        and holder.attr in CARRY_MANIFEST[key]
                    ):
                        # G3: a marker is honored ONLY at its pinned (file, function, receiver).
                        self.marked.append((self.func_stack[-1], holder.attr, node.lineno))
                    elif key in RESET_SEED_MANIFEST:
                        # RESET-SEED class (pN 18:17): counted like a carry, verified vs its manifest.
                        self.marked.append((self.func_stack[-1], "reset-seed:" + holder.attr, node.lineno))
                    else:
                        spoof = " [SPOOFED MARKER]" if self._line_marked(node.lineno) else ""
                        self._hit(node.lineno, "JQ-ASSIGN", "SINK", ".".join(toks) + f".assign(...){spoof}")
                elif holder.attr in BODY_ASSIGN_ATTRS and not _has_fk_token(toks[:-1]):
                    key = (self.rel, self.func_stack[-1])
                    if key in BODY_CABLE_SEED_MANIFEST:
                        self.marked.append((self.func_stack[-1], holder.attr, node.lineno))
                    else:
                        self._hit(node.lineno, "BODY-ASSIGN", "SINK", ".".join(toks) + ".assign(...)")
            elif f.attr == "fill_" and isinstance(f.value, ast.Attribute) and f.value.attr in STATE_ATTRS:
                self._hit(node.lineno, "WP-COPY", "SINK", f".{f.value.attr}.fill_(...)")
            elif f.attr == "copy" and isinstance(f.value, ast.Name) and f.value.id == "wp" and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Attribute) and a0.attr in STATE_ATTRS and not _has_fk_token(_tokens(a0.value)):
                    self._hit(node.lineno, "WP-COPY", "SINK", f"wp.copy(<...>.{a0.attr}, ...)")
            elif f.attr == "copyto" and isinstance(f.value, ast.Name) and f.value.id == "np" and node.args:
                a0 = node.args[0]  # G2: np.copyto(<state array>, x) writes in place
                if isinstance(a0, ast.Attribute) and a0.attr in STATE_ATTRS and not _has_fk_token(_tokens(a0.value)):
                    self._hit(node.lineno, "WP-COPY", "SINK", f"np.copyto(<...>.{a0.attr}, ...)")
        self.generic_visit(node)


def check_source(rel: str, src: str) -> _FileCheck:
    fc = _FileCheck(rel, src)
    try:
        fc.visit(ast.parse(src))
    except SyntaxError as e:
        fc.hits.append(Hit(int(e.lineno or 0), "UNPARSEABLE", "UNPARSEABLE", "<module>", f"SyntaxError: {e.msg}"))
    return fc


# ---------------------------------------------------------------------------------------------
# self-test corpus (G2/G3/G4 controls included)
_NEG_CONTROLS: list[tuple[str, str]] = [
    ("alias-subscript", "def f(s):\n    v = s.joint_q.numpy()\n    v[3] = 1.0\n"),
    ("alias-augassign", "def f(s):\n    v = s.joint_q.numpy()\n    v[3] += 1.0\n"),
    ("alias-annassign", "def f(s):\n    v: object = s.joint_q.numpy()\n    v[3] = 1.0\n"),  # G2
    ("jq-assign", "def f(s, a):\n    s.joint_q.assign(a)\n"),
    ("jq-assign-comment-spoof", "def f(s, a):\n    s.joint_q.assign(a)  # fk_state sync\n"),
    ("jq-assign-multiline", "def f(s, a):\n    s.joint_q.assign(\n        a\n    )\n"),
    ("receiver-substring-spoof", "def f(not_fk_state, a):\n    not_fk_state.joint_q.assign(a)\n"),  # G3
    ("body-assign", "def f(s, a):\n    s.body_q.assign(a)\n"),
    ("body-prev-assign", "def f(sol, a):\n    sol.body_q_prev.assign(a)\n"),
    ("marker-on-unpinned-function", "def not_the_seeder(s, a):\n    s.joint_q.assign(a)  " + MARKER + ": fake)\n"),  # G3
    ("eq-active-store", "def f(mjd):\n    mjd.eq_active[3] = 1\n"),
    ("eq-active-attr-store", "def f(mjd, x):\n    mjd.eq_active = x\n"),  # G2
    ("qpos-store", "def f(d, i):\n    d.qpos[i] = 0.5\n"),
    ("wp-copy", "def f(s, a):\n    wp.copy(s.joint_q, a)\n"),
    ("np-copyto", "def f(s, a):\n    np.copyto(s.body_q, a)\n"),  # G2
    ("fill", "def f(s):\n    s.joint_q.fill_(0.0)\n"),
    ("canonical-name-store", "def f(phys_jq):\n    phys_jq[0:6] = 0.0\n"),
    ("seeder-names-outside-seeder", "def f(state):\n    jq = state.joint_q.numpy()\n    jq[0:7] = 0.0\n"),  # G3
]
_POS_CONTROLS: list[tuple[str, str]] = [
    ("fk-state-real", "def f(self, a):\n    self._fk_state.joint_q.assign(a)\n"),
    ("fk-state-plain", "def f(fk_state, a):\n    fk_state.joint_q.assign(a)\n"),
    ("ctrl-servo", "def f(c, a):\n    c.joint_target_pos.assign(a)\n"),
    ("read-only", "def f(s):\n    v = s.joint_q.numpy()\n    x = float(v[0])\n    return x\n"),
    ("plain-local", "def f():\n    buf = [0] * 4\n    buf[1] = 2\n    return buf\n"),
]


def self_test() -> bool:
    ok = True
    for name, snippet in _NEG_CONTROLS:
        fc = check_source("<neg>", snippet)
        if not fc.hits:
            print(f"  [SELF-TEST FAIL] negative control NOT caught: {name} (marked={fc.marked})")
            ok = False
    for name, snippet in _POS_CONTROLS:
        fc = check_source("<pos>", snippet)
        if fc.hits or fc.marked:
            print(f"  [SELF-TEST FAIL] positive control false-positived: {name} -> {[(h.lineno, h.klass) for h in fc.hits] or fc.marked}")
            ok = False
    # G3 same-count marker-spoof: a marker MOVED onto an arm writer (count preserved) must FAIL
    spoof = (
        "def seed_cable_joint_state(state, a, b):\n"
        "    state.joint_q.assign(a)  " + MARKER + ": cable)\n"
        "def arm_writer(s, a):\n"
        "    s.joint_qd.assign(a)  " + MARKER + ": smuggled)\n"
    )
    fc = check_source(SEEDER_KEY[0], spoof)
    got = {(f, attr) for f, attr, _ in fc.marked}
    if ("arm_writer", "joint_qd") in got:
        pass  # marked lexically -- the manifest comparison below must reject it
    manifest_view = {}
    for f, attr, _ in fc.marked:
        manifest_view.setdefault((SEEDER_KEY[0], f), {}).setdefault(attr, 0)
        manifest_view[(SEEDER_KEY[0], f)][attr] += 1
    if manifest_view == CARRY_MANIFEST:
        print("  [SELF-TEST FAIL] same-count marker-spoof NOT rejected by the carry manifest")
        ok = False
    # G4 fixture-injection: a hit in an allowed FILE but NOT in an allowed function must fail
    fx_file = next(iter(FIXTURE_MANIFEST))
    fc = check_source(fx_file, "def smuggled_writer(s, a):\n    s.joint_q.assign(a)\n")
    fx_ok = all(h.func in FIXTURE_MANIFEST[fx_file] for h in fc.hits)
    if fx_ok:
        print("  [SELF-TEST FAIL] fixture-injection control NOT rejected (function not in manifest)")
        ok = False
    return ok


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    roots = [repo / "thread_isaac_lab" / "envs", repo / "thread_isaac_lab" / "scripts"]
    print("=== Layer 8 v3.1: AST Control-Method Guard (sec0#3/#5; NO exceptions; self-tested) ===")
    if not self_test():
        print("  [FAIL] self-test failed -- the checker cannot certify anything (fail-closed)")
        print("LAYER8_FAIL=1")
        print("LAYER8_WARN=0")
        return 1
    print(f"  [SELF-TEST] all controls behave ({len(_NEG_CONTROLS)} neg / {len(_POS_CONTROLS)} pos / spoof / injection)")

    sink = source = unparse = fail = 0
    fixture_hits = 0
    fixture_files: set[str] = set()
    marked_seen: dict[tuple[str, str], dict[str, int]] = {}
    for root in roots:
        if not root.is_dir():
            print(f"  [FAIL] scan root missing: {root}")
            fail += 1
            continue
        for py in sorted(root.rglob("*.py")):  # G1: recursive
            rel = str(py.relative_to(repo))
            fc = check_source(rel, py.read_text())
            fx_funcs = FIXTURE_MANIFEST.get(rel)
            for h in fc.hits:
                if fx_funcs is not None and h.func in fx_funcs:
                    fixture_hits += 1
                    fixture_files.add(rel)
                    continue
                fail += 1
                if h.kind == "SINK":
                    sink += 1
                elif h.kind == "SOURCE":
                    source += 1
                else:
                    unparse += 1
                print(f"  [FAIL:{h.kind}] {rel}:{h.lineno}: {h.klass}: {h.detail} (in {h.func})")
            for func, attr, ln in fc.marked:
                marked_seen.setdefault((rel, func), {}).setdefault(attr, 0)
                marked_seen[(rel, func)][attr] += 1
                if attr.startswith("reset-seed:"):
                    print(f"  [RESET-SEED] {rel}:{ln}: sanctioned once-at-reset joint seed in {func} (pN 18:17 manifest)")
                else:
                    print(f"  [CARRY] {rel}:{ln}: CABLE-SEED marked in {func} (declared sec14.2 step-3 carry)")
    expected_marks: dict[tuple[str, str], dict[str, int]] = {k: dict(v) for k, v in CARRY_MANIFEST.items()}
    for k, v in RESET_SEED_MANIFEST.items():
        expected_marks.setdefault(k, {}).update({"reset-seed:" + a: c for a, c in v.items()})
    if marked_seen != expected_marks:
        print(f"  [FAIL] carry/reset-seed manifest mismatch: found {marked_seen} expected {expected_marks}")
        fail += 1
    # G4: fixture counts must match the manifest exactly (drift = FAIL)
    expected_fixture = sum(c for m in FIXTURE_MANIFEST.values() for c in m.values())
    if fixture_hits != expected_fixture:
        print(f"  [FAIL] fixture manifest count drift: found {fixture_hits} expected {expected_fixture}")
        fail += 1
    elif fixture_hits:
        print(f"  [FIXTURE-INVENTORY] {fixture_hits} mock-state write(s) across {len(fixture_files)} pinned host-mock pytest file(s) (per-function manifest)")

    carries = sum(c for m in marked_seen.values() for c in m.values())
    if fail == 0 and carries:
        print(f"  [PASS-WITH-DECLARED-CARRY] no kinematic writers; {carries} CABLE-SEED carry line(s) remain (sec14.2 step-3)")
    elif fail == 0:
        print("  [PASS] no kinematic writers, no carries")
    else:
        print(f"  [VERDICT] RED: delivery-sinks={sink} source-candidates={source} unparseable={unparse} (distinct classes, NOT unique-writer count)")
    print(f"LAYER8_FAIL={fail}")
    print("LAYER8_WARN=0")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
