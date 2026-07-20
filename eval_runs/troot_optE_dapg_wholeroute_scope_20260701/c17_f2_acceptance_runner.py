"""Durable F2 acceptance runner (c17 records-fix c18, pN verdict B2 2026-07-20 09:24).

Static + runtime legs for the removal of ``import_chain_state_into_env``'s body
(commit c17 ``3117bbd21c``). No sim, no GPU, no heavy package import — the target module is
loaded by file path so ``thread_isaac_lab.envs.__init__`` never runs.

Evidence classes (pN B1):
- BANKED legs (gate the exit code): symbol/signature, warn+raise, zero env/state read/write
  at raise time, approach-wrapper fail-close (committed in THIS repo tree), runtime
  propagation, and the A5 absence legs (no dead writer).
- OBSERVATIONS (never gate): grip / aerial wrapper shapes — dirty-tree / untracked surfaces;
  reported when present, skipped silently-loudly when absent.

Run from anywhere inside the repo: paths resolve relative to this file's location.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import subprocess
import sys
import warnings as _w
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MOD_PATH = REPO / "thread_isaac_lab/envs/chain_runtime_state.py"
APPROACH = REPO / "thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py"
# Cross-tree observation surfaces (pN B1: NON-BANKED). Absence is tolerated.
OBS_WRAPPERS = [
    ("grip", REPO / "thread_isaac_lab/envs/newton_grip_env.py"),
    ("aerial", REPO / "thread_isaac_lab/envs/newton_aerial_regrasp_mujoco_env.py"),
    ("grip@main", Path("/home/rlrk/IsaacLab/thread_isaac_lab/envs/newton_grip_env.py")),
    ("aerial@main", Path("/home/rlrk/IsaacLab/thread_isaac_lab/envs/newton_aerial_regrasp_mujoco_env.py")),
]

EXPECTED_SIG = (
    "(env: 'Any', state: 'ChainRuntimeState', *, target_skill: 'str | None' = None,"
    " validate: 'bool' = True) -> 'ChainRuntimeRestoreReport'"
)


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=REPO, timeout=30).stdout.strip()
    except Exception as exc:  # noqa: BLE001
        return f"<git unavailable: {exc}>"


def wrapper_shape(path: Path) -> tuple[bool | None, str]:
    """AST check: is import_chain_state's body a single return of the removed function?"""
    if not path.exists():
        return None, "FILE ABSENT"
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as exc:
        return False, f"unparseable: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "import_chain_state":
            body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
            ok = (
                len(body) == 1
                and isinstance(body[0], ast.Return)
                and isinstance(body[0].value, ast.Call)
                and getattr(body[0].value.func, "id", None) == "import_chain_state_into_env"
            )
            return ok, f"line={node.lineno} sole_call_to_removed_fn={ok}"
    return False, "no import_chain_state def"


def main() -> int:
    print("== F2 acceptance runner (banked) ==")
    print(f"repo            : {REPO}")
    print(f"HEAD            : {_git('rev-parse', 'HEAD')}")
    print(f"module blob     : {_git('hash-object', str(MOD_PATH))}")
    dirty = _git("status", "--porcelain", "--", str(MOD_PATH))
    print(f"module dirty?   : {dirty if dirty else 'CLEAN (committed state measured)'}")

    spec = importlib.util.spec_from_file_location("chain_runtime_state_probe", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    results: list[tuple[str, bool, str]] = []

    def leg(name: str, ok: bool, detail: str) -> None:
        results.append((name, ok, detail))

    # LEG 1 — symbol + signature
    fn = getattr(mod, "import_chain_state_into_env", None)
    sig = str(inspect.signature(fn)) if fn else "<absent>"
    leg("1 symbol importable", callable(fn), f"callable={callable(fn)}")
    leg("1 signature preserved", sig == EXPECTED_SIG, f"got={sig}")

    # traps: record every attribute read and every write on the former sink surfaces
    log: list[str] = []

    class TrapArray:
        def __init__(self, name: str) -> None:
            object.__setattr__(self, "_n", name)

        def assign(self, value):  # noqa: ANN001
            log.append(f"WRITE {object.__getattribute__(self, '_n')}.assign")

        def __setitem__(self, key, value):  # noqa: ANN001
            log.append(f"WRITE {object.__getattribute__(self, '_n')}[...]")

    class TrapObj:
        def __init__(self, label: str, fields: dict) -> None:
            object.__setattr__(self, "_label", label)
            object.__setattr__(self, "_fields", fields)

        def __getattribute__(self, name):  # noqa: ANN001
            label = object.__getattribute__(self, "_label")
            if name not in ("_label", "_fields"):
                log.append(f"READ {label}.{name}")
                fields = object.__getattribute__(self, "_fields")
                if name in fields:
                    return fields[name]
                raise AttributeError(name)
            return object.__getattribute__(self, name)

        def __setattr__(self, name, value):  # noqa: ANN001
            log.append(f"WRITE {object.__getattribute__(self, '_label')}.{name}")
            object.__setattr__(self, name, value)

    trap_env = TrapObj(
        "env",
        {
            "_state_0": TrapObj(
                "state_0",
                {"body_q": TrapArray("state_0.body_q"), "body_qd": TrapArray("state_0.body_qd")},
            ),
            "_solver": TrapObj("solver", {"body_q_prev": TrapArray("solver.body_q_prev")}),
            "_fk_state": TrapObj("fk_state", {"joint_q": TrapArray("fk_state.joint_q")}),
            "_per_world_fk_jq": TrapArray("env._per_world_fk_jq"),
        },
    )
    trap_state = TrapObj("state", {})

    # LEG 2 + 3 — warn + raise, zero read / zero mutation
    log.clear()
    raised: Exception | None = None
    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        try:
            fn(trap_env, trap_state)
        except Exception as exc:  # noqa: BLE001
            raised = exc
    dep = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    leg("2 DeprecationWarning emitted", len(dep) == 1, f"n={len(dep)}")
    leg("2 RuntimeError raised", isinstance(raised, RuntimeError), f"raised={type(raised).__name__}")
    writes = [e for e in log if e.startswith("WRITE")]
    reads = [e for e in log if e.startswith("READ")]
    leg("3 env/state mutation == 0", not writes, f"writes={writes}")
    leg("3 env/state read == 0", not reads, f"reads={reads}")

    # LEG 4 — BANKED wrapper: approach env in THIS repo tree (committed surface)
    ok, detail = wrapper_shape(APPROACH)
    leg("4 wrapper approach (BANKED, committed)", bool(ok), detail)

    class _WrapperShape:
        def import_chain_state(self, state, *, world_idx=0, validate=True):  # noqa: ANN001
            return fn(self, state, target_skill="AC", validate=validate)

    log.clear()
    prop: Exception | None = None
    with _w.catch_warnings(record=True):
        _w.simplefilter("always")
        try:
            _WrapperShape().import_chain_state(trap_state)
        except Exception as exc:  # noqa: BLE001
            prop = exc
    leg("4 propagation through wrapper shape", isinstance(prop, RuntimeError), f"raised={type(prop).__name__}")

    # A5 — absence legs: no dead writer
    src = MOD_PATH.read_text()
    tree = ast.parse(src)
    defs = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    leg("A5 _assign_array deleted (AST)", "_assign_array" not in defs, f"n_defs={len(defs)}")
    leg("A5 _assign_array absent from text", "_assign_array" not in src, "closed query over module text")
    assigns = [
        str(n.lineno) for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "assign"
    ]
    leg("A5 no .assign() call in module", not assigns, f"lines={assigns}")

    print("\n-- BANKED LEGS --")
    allok = True
    for name, ok_, detail in results:
        allok &= ok_
        print(f"[{'PASS' if ok_ else 'FAIL'}] {name}\n        {detail}")

    print("\n-- OBSERVATIONS (NON-BANKED, pN B1; never gate exit code) --")
    seen: set[str] = set()
    for label, path in OBS_WRAPPERS:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        ok_o, detail_o = wrapper_shape(path)
        if ok_o:
            state = "OBS-CONSISTENT"  # wrapper present, sole call to removed fn -> inherits raise
        elif ok_o is None:
            state = "OBS-ABSENT"  # file not on this surface
        elif detail_o == "no import_chain_state def":
            state = "OBS-NO-WRAPPER"  # surface has no chain wrapper at all (B1: committed grip/aerial)
        else:
            state = "OBS-DIVERGENT"  # wrapper exists but body is not the sole call -- investigate
        print(f"[{state}] {label}: {path} — {detail_o}")

    print(f"\nOVERALL (banked legs): {'ALL PASS' if allok else 'FAIL'}")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
