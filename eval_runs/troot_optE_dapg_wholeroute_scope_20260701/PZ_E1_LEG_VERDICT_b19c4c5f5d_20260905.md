# pZ — E1 leg VERDICT on `b19c4c5f5d` (RUN_METRICS.json written by the driver at exit), judged against its own parent

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-05 08:0x JST. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Rows** = `PZ_E1_RUN_METRICS_LEG_PREREG_20260905.md` (sha256 `d61a2eb485116d4bb90d2475b71ce2d15db444f45b798dc04b84959a39f3c7ae`, 43 lines) — written 07:55:35, **14 s after the landing**, blind to it; stated there, not called pre-registered.
**Object**: `b19c4c5f5d` (07:55:21, "Write RUN_METRICS.json at exit from the wired driver, by the existing contract"), **1 file, +119/−0**. Parent `d6a112261e`, whose driver blob **== `c737f6974e`'s** (`45b1e7f5ea`, blob-id equality) — every parent number below is at that blob. Landed content sha256 **`18355d408aed06839a81b79987eb5557dbd6c9e4bd83fff583703dc0ccc37e1a`**.
⛔ Nothing wired ran from this desk. L1 had **not** been run by anyone as of 08:03 JST (no `RUN_METRICS.json`, no `run.log.sha256` under `_gen/`; measured).

## 0. Headline — F-d: as landed, the writer writes on ONE exit path, and it is the one L1 exercises

Stand-in = the E1 block extracted **verbatim** from the landed blob (new-blob lines 41–138: `_RM`, `_RM_ENV`, the four functions, the `atexit.register`) on stub globals, run as `python file.py OUT > run.log 2>&1` under env7 Python 3.12.3, sidecar taken by `sha256sum` after exit — never importing the driver:

| exit path | driver equivalent | JSON written? | the writer's own last log line |
|---|---|---|---|
| `raise SystemExit(0)` | `:1103` (`P4_CLIP_DUMP`, reached **after** the live 2000-step cable settle `:1044–:1049`) / `:2928` (`P4_RELEASE_ONLY`) = **L1's exit mechanism** | **yes**, every field right (§2) | `[steps] RUN_METRICS.json -> … (end_reason=exited_early)` |
| uncaught `RuntimeError` | the stall raise `:3846` = **L2** | **NO** | `[steps] RUN_METRICS.json NOT written: NameError: name '__file__' is not defined` |
| normal completion | a finished route = **L2** | **NO** | same |

**Mechanism, proven minimally** (`pz_file_at_exit.py`, three paths × two handler variants): CPython deletes `__main__.__file__` when the script body ends — normal end **or** a non-`SystemExit` exception — **before** the atexit handlers run; `SystemExit` finalizes from inside `PyErr_Print` while `__file__` still exists. The landed handler reads the **global** `__file__` at exit twice: `:80` (`here = Path(__file__).resolve().parent`) and `:106` (`"driver": xml(Path(__file__).resolve())`). The existing `_depth_audit_report` references `__file__` **0** times — which is why it has always printed on the raised path in the real logs, and why nothing before E1 could have shown this.
**Fix shape (p0's, one line)**: capture `Path(__file__).resolve()` at import (beside `_RM`) and use the captured value in the handler. **Proven**: with `__file__` captured, the same writer is correct on both L2 paths (§2).
⭐ **Why p0's own probe passed (§8.46 §2, "PASS r1 end_reason raised")**: their harness `exec`s the block in a **fake module namespace with `__file__` injected** (`ns = {"__file__": str(DRV), …}`, `exec(compile(block, …), ns)` — §8.46 lines 110/123). That dict is not `__main__.__dict__`, so CPython's end-of-script deletion never reaches it and the name survives to atexit. The real driver's handler lives in `__main__`. My stand-in ran the same verbatim block **as** `__main__` (`python file.py`), which is how the driver runs — and it failed. The fixture protected exactly the name the production environment removes: a test that could not come out differently on this defect.
⚠ **Consequence for L1**: L1 exercises exactly the path that works. An L1 PASS is real and **proves nothing about this defect**. The discriminating test is the writer's own unit probe that §8.45 §5 itself names ("raise → end_reason raised, message byte-equal") — and it **fails** at `b19c4c5f5d`. Row 8 (loud failure) did its job: the NOT-written line is how this was found.

## 1. Rows, parent-relative

| # | row | verdict | evidence |
|---|---|---|---|
| 1 | scope | **holds** | 1 file (the driver only), `+119/−0`, ≤ 120; kinonly `120746a49b`, `compare_24_vs_240.py`, spec files untouched |
| 2 | control invariance | **holds, mechanical** | ordered control-class sequence sha **`426aa229deb2cb2b`** == parent (57 lines); live state writes **0 → 0**; `d.ctrl` writes **7 → 7, same order** (`[1046, 2407, 2580, 2631, 2639, 3538, 3542]` → `[1145, 2506, 2679, 2730, 2738, 3639, 3643]`); `mj_step(` sites **11 → 11**; AST of the four added functions: banned calls **none**, writes to `d`/`m` **none** |
| 3 | handler placement | **holds** | `atexit.register(_write_run_metrics)` `:138` before `_depth_audit_report` `:1755` ⇒ runs last (LIFO proven); registered before both early exits |
| 4 | M2 semantics | **holds on the SystemExit path; fails on raised/completed as landed (F-d)** | `end_reason` from `_RM["completed"]` / `sys.last_value`; `exit_code` 0 / 1 / null; `exception{type,message}`; `SystemExit` leaves `sys.last_value` unset (control B) so `exited_early` is reachable; **both** early-exit paths classify as `exited_early` (F-a handled) |
| 5 | M1 / A1 | **holds** | `readlink(/proc/self/fd/1)` → regular file else `OUT.resolve().parent`; announce → `flush` stdout+stderr → **one read** → bytes + sha; at-write sha == sha(prefix) **and** == the launcher's sidecar with **0 B tail** on all three stand-in paths (captured variant); the driver does **not** write the sidecar (the string appears once, in a comment) |
| 6 | A2 shape | **holds** | 8 top-level keys = the 7 + `ur15_steps` (`goal_context` absent — F-b); `judgement` = `{"PENDING", null}`; `identity.RIGHT.arm` = "UR15-B"; sentinel ≥ 1e8 → null (1e9 → null, 0.0123 kept); code-object depth-audit keys stringified as `name:firstlineno` |
| 7 | identity / provenance | **holds (shape)** | `xml()` = {path, sha256 of bytes} for arm/grip L/R, the driver, the cell dump — re-hashed against blobs when L1's output exists |
| 8 | loud failure | **holds — demonstrated** | `try/except` prints `[steps] RUN_METRICS.json NOT written: <type>: <e>`; control A: an atexit exception leaves the exit code unchanged (`rc=7`) |
| 9 | transport (L2 only) | **deferred** | needs a run; note `sigma_min(t)` is **re-evaluated** in the dict, not re-read — same function, same `d`, nothing steps in between (row 2), so equal in practice; the transport check will say |
| 10 | analyzer pickup | **holds (static)** | `artifacts.logs.path` and `run.log_path` both written; file lands at `$RUN_DIR/RUN_METRICS.json` (SKILL.md `:39`, `:52-63`) |
| 11 | no run from this desk | **holds** | the writer's unit probe ran only on my stand-in; the driver never imported; L1 unrun by anyone at 08:03 |
| 12 | pins | **holds** | commit, parent blob, content sha256 named above |

## 2. The writer with `__file__` captured — what it will do once the one line lands (my stand-in, captured variant)

- **raised**: `end_reason` "raised", `exit_code` 1, `exception.type` "RuntimeError", **message byte-equal** to the text after `RuntimeError: ` on the log's traceback line; at-write sha == sha(prefix) == sidecar, tail 0 B; last log line = the announce; `steps` 1, `phase_max_reached` 2; `np.float64` → `float`; `elapsed_s` filled; depth-audit keys `<module>:1`.
- **completed**: "completed", 0, no exception, same integrity.
- **exited_early**: as landed (already correct).

## 3. Findings that ride (F-a, F-b registered in the prereg; F-c, F-d new)

- **F-a** — a second `SystemExit(0)` at parent `:2928`, the last line of the module-level `if P4_RELEASE_ONLY == "1"` block (`:2916–:2928`, which calls `release_ctrl()`, `def :2725`); it steps **scratch** physics (`_sc`). And the `:1103` path is not physics-free either: the **live** 2000-step cable settle `:1044–:1049` precedes the `P4_CLIP_DUMP` check (p0's own retraction in §8.46; my prereg inherited the same false clause and is corrected in place). §8.45's "the only such path is :1103" is wrong in words; the writer handles both correctly (`exited_early`, armed at `:138`).
- **F-b** — the live contract's 8th key `goal_context` is absent; analyzer-neutral.
- **F-c** — `_RM_ENV` (23 names) is **not** the population the run reads (24): it **omits `CABLE_BEND_STIFFNESS_OVERRIDE`** (spec `:202`, `:1205`, `:1228` read it; the spec prints it loudly at `:1229` when set — mitigated, not covered by the echo) and **includes `P4_OLD_SEAT_AIM`** (driver `:84`, read with **single quotes**: `_os.environ.get('P4_OLD_SEAT_AIM')`) — which **my own** double-quote query missed. My "23" and the edit's "23" were different sets: same numeral, not same quantity. The edit was right to include it; my population was short by one, corrected here.
- **F-d** — §0.

## 4. Verdict (four clauses)

1. **Structure**: instrument only, machine-proven — no control line moved, no live write, no banned call in the added code; +119/−0.
2. **Contract**: the document the writer builds **is** the `run_metrics.v1` contract with the driver's content under `ur15_steps`, and every M1/M2/A1/A2 mechanism is proven live on stand-ins outside the driver.
3. ⛔ **Defect F-d**: as landed, the file is written on the `SystemExit` path only; the two paths the next authorized route run will take (a stall raise, or completion) yield the loud line and **no file**. One-line fix, p0's. **Until it lands, an L1 PASS must not be read as "the writer works."**
4. **Riders**: F-a (wording), F-b (key), F-c (one spec switch missing from the echo; one name my query missed).

## 5. Provenance

`git show`/`rev-parse`/`numstat`; `sha256sum`; own AST + ordered-grep walk (`pz_e1_ctrl.py`) at the named parent and at the commit; own stand-ins (`pz_e1_mech.py`, `pz_file_at_exit.py`, `e1_unit/writer_standin.py` + captured variant) under `/home/rlrk/env_isaaclab7/bin/python` 3.12.3, outputs captured; env population by grep with a quote-shape hole found and named. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian, together with the prereg.**
