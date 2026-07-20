# F2 — chain-state import writer removal: implementation + evidence (p4 / RS-TECH-LEAD, 2026-07-20)

**v1.1 records-fix (2026-07-20 09:3x JST)** — pN c17 verdict (09:24) B1-B3 folded; see §7 for the
change log and the superseded v1.0 sha. Code surface untouched by this revision
(`chain_runtime_state.py` blob `5c67bab83fb4…` unchanged).

**Authority**: pN B-drive court ruling ② (2026-07-20 08:04) = ADOPT / implementation GO, within Rs
option B (03:42). **Worktree lane only — this is not a landing.** Main-tree HALT and commit freeze stand.
**Verdict status**: pN 09:24 = **CORE MECHANISM PASS / EVIDENCE HOLD B1-B3** → this revision is the
records-fix; F2 evidence CLOSE = pN readback after it banks.

**Banked commit**: `3117bbd21cd7fad7e790d9d2ab50180817d06448` on `probe/pd1-arm-pd`
(parent = c16 `3e9b973144`). Tree clean at commit and at every measurement below.
**File blob**: `5c67bab83fb41461147b62032c070b08e4d64c51` (`thread_isaac_lab/envs/chain_runtime_state.py`).
**Diff**: 1 file, +24 / −50. `--no-verify` diagnostic commit per the standing pN ruling for this
worktree (worktree lacks Layer4/6 infra; final landing takes the full pre-commit flow).

---

## 1. What changed

`import_chain_state_into_env` restored solver/body state (`body_q`, `body_qd`, `body_q_prev`) plus
joint and per-world arrays directly into a live env — a kinematic placement. Three edits:

1. `import warnings` added (plain, stdlib-first per isort; **not** aliased — see §5-A4).
2. The function body replaced by: docstring + provenance comment + `warnings.warn(msg,
   DeprecationWarning, stacklevel=2)` + `raise RuntimeError(msg)`. **Name, signature and return
   annotation preserved byte-for-byte.** No `env` or `state` access precedes the raise.
3. `_assign_array` **deleted** (its 5 call sites were all inside the removed body) — so no dead writer
   remains behind the raise, per charter §14.12 TK-2.

Disposition class = §14.16-R **body-deleted entry-raise** (the sanctioned shape), *not* the refuted
"entry-raise that leaves the body". Provenance comment carries the pre-deletion sha + charter pointer
as TK-2 requires.

## 2. Acceptance — all legs at the banked sha, clean tree

Runner (**B2 records-fix**): banked as
`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/c17_f2_acceptance_runner.py` + output log
`c17_f2_acceptance_runner_OUTPUT.txt` on `probe/pd1-arm-pd` (c18). It loads the module by file path
(repo-relative from its own location), so the heavy `thread_isaac_lab.envs` package `__init__` is never
imported. The original `scratchpad/c17_F2_acceptance.py` was session-local and is superseded (pN B2:
worktree had no such file); pN's independent reproduction corroborates every leg. Re-run not required
per pN; the banked log below was regenerated from the banked runner anyway (durable evidence).

| # | leg | result |
|---|---|---|
| 1 | symbol importable | PASS |
| 1 | signature preserved | PASS — `(env: 'Any', state: 'ChainRuntimeState', *, target_skill: 'str \| None' = None, validate: 'bool' = True) -> 'ChainRuntimeRestoreReport'` |
| 2 | `DeprecationWarning` emitted | PASS (n=1) |
| 2 | `RuntimeError` raised | PASS |
| 3 | env/state **mutation** == 0 | PASS — trap records `writes=[]` |
| 3 | env/state **read** == 0 | PASS — trap records `reads=[]`; the raise precedes every access |
| 4 | wrapper fail-close — **banked: approach ×1 (committed at c17)** | PASS — grip/aerial = **non-banked observations** (pN B1), see §3 |
| 4 | propagation through wrapper shape (runtime) | PASS — `RuntimeError` |
| A5 | `_assign_array` deleted (AST) | PASS |
| A5 | `_assign_array` absent from module text | PASS |
| A5 | **no `.assign()` call anywhere in module** | PASS — `lines=[]` |
| 5 | guard census | PASS — see §4 |
| 6 | `py_compile` / `ruff check` | PASS / "All checks passed!" |

Leg-3 trap: stub `env`/`state` whose every attribute read is logged and whose former sink targets
(`state_0.body_q`, `state_0.body_qd`, `solver.body_q_prev`, `fk_state.joint_q`, `env._per_world_fk_jq`)
are objects recording `.assign()` and `__setitem__`. Both logs empty.

**A5 exists because the census alone cannot see a retained dead writer**: a variant keeping
`_assign_array` uncalled also measures 125 / envs 0. The census is structurally blind to edit 3, so
"leave no dead writer" needs its own leg. (Surfaced by the pre-change panel; folded before [CHANGE].)

## 3. caller0 vs wrapper3 — recorded separately, as the ruling requires

- **caller0** (callsite query): **0 runtime callers.** Closed query over all filetypes across both
  trees: the only call sites are the wrapper methods themselves; the Stage-0 facade
  (`newton_chain_context_facade.py:37`) holds the *string* `"import_chain_state"` in
  `REQUIRED_ENV_METHODS` and `verify_env_api` tests only `callable(getattr(...))` — it never invokes.
  Remaining hits are historical copies under `eval_runs/` (evidence artifacts, not active source).
- **wrapper3** (exposed surface): **3 env wrappers**, each of whose entire body is a single call to the
  removed function — verified by AST, so fail-close propagation is *structural*, not sampled:

| env wrapper | line | provenance at read time | evidence class (pN B1) |
|---|---|---|---|
| `newton_approach_cable_mujoco_env.py` | `:1203` (worktree) / `:1242` (main) | **committed** (in main HEAD) | **banked PASS** |
| `newton_grip_env.py` | `:1739` | **dirty-tree only** — main HEAD has 0 refs | **NON-BANKED OBSERVATION / carry** |
| `newton_aerial_regrasp_mujoco_env.py` | `:1635` | **untracked** — aerial lane, pN-excluded (①D) | **NON-BANKED OBSERVATION / carry** |

**B1 records-fix (pN 09:24, adopted)**: at the c17 *committed* state, the only wrapper is the approach
env. The earlier "wrapper ×3 PASS" over-scoped: grip is a dirty-tree observation and aerial an untracked
observation — neither is bankable evidence (pin-over-committed-state rule). Banked acceptance =
**wrapper ×1 (approach)**; grip/aerial legs become banked only when those files are committed on a
verified sha (carry). The mechanism statement is unchanged: any wrapper whose body is the single call
inherits the raise.

⇒ **This settles the ruling's ambiguity.** "3 env wrapper" = the `import_chain_state` wrapper on each of
3 **envs** (AC / GC_CLAMP / AR) — which is why the ruling also says to record "wrapper3" separately from
"caller0". Under that reading there is no tension with "migration target = read-only export/validate":
all 3 *import* wrappers fail-close, while `export`/`validate` stay functional and read-only.
The alternative reading (export/import/validate on one env) is self-refuting, since export/validate are
the declared migration target. **The code edit is identical under either reading** — no wrapper was
touched; all 3 inherit the raise. Only the verification scope differs, and the broader scope was used.
⚠ Blast radius on landing: the grip and aerial wrappers begin raising when this lands on main. Neither
was edited; both are outside the p4 lane.

## 4. Guard census at the banked sha

| | before (c16 `3e9b973144`) | after (c17 `3117bbd21c`) |
|---|---|---|
| `LAYER8_FAIL` | 128 | **125** |
| `LAYER8_WARN` | 0 | 0 |
| envs | **3** (`chain_runtime_state.py:278/280/286`, all `BODY-ALIAS … helper-param body write`) | **0** |
| scripts | 125 | 125 (unchanged) |
| total `[FAIL` lines == `LAYER8_FAIL` | 128 == 128 | **125 == 125** |

The last row is a deliberate anti-false-pass check: on self-test failure the guard prints
`LAYER8_FAIL=1` and **zero** per-file lines, so a naive "envs count" grep returns 0 and passes for the
wrong reason. Asserting the identity defeats that. Raw: `scratchpad/guard_c16_baseline.txt`,
`scratchpad/guard_c17_post.txt`.

### 4b. Canonical (F3-expanded) guard — the comparable delta is 131 → 128

pN closed the F3 scan-root gap by banking an expanded guard: commit `7803f58f17` (branch
`codex/f3-layer8-scan-root`, guard blob `f498f888f18c…`) — recursive scan of **all** of
`thread_isaac_lab/` (roots line: `roots = [repo / "thread_isaac_lab"]`) plus local getattr-alias
direct-assign detection. Under it, the table above is the **historical restricted-scope** view
(roots = envs+scripts). The canonical full-surface numbers:

| canonical (F3 guard) | c16-equivalent `3e9b973144` | c17-equivalent `3117bbd21c` |
|---|---|---|
| `LAYER8_FAIL` | **131** | **128** (= scripts 125 + `skills/snapshot.py` 3) |
| delta | | **−3** = exactly the three `chain_runtime_state.py` sinks |

**Independently reproduced by p4 this session** (not relayed): guard extracted via
`git show codex/f3-layer8-scan-root:scripts/validations/check_control_method.py`; run against a
read-only `git archive 3e9b973144` extraction (c16-equiv) and a symlink view of the clean c17 worktree
(c17-equiv); worktree untouched (`git status --porcelain` empty throughout). Results: 131 / 128 exact;
`snapshot.py` FAILs = 3 (`:119/:120/:128`); `:121` absent from FAIL lines; envs bucket at c17 = 0.
⇒ **The acceptance "repo bar 128→125" in §4 is the bar the 08:04 ruling was phrased against, kept as
the historical acceptance record; the canonical comparable delta is 131→128 (−3).** Both agree on the
substance: the three chain_runtime_state sinks are gone and nothing else moved.

## 5. Open items carried out of this chunk

- **F3 — guard scan-root gap: mechanism CLOSED (pN), remediation OPEN (separate owner gate).**
  Found this chunk: the pre-F3 guard's `roots = [thread_isaac_lab/envs, thread_isaac_lab/scripts]`
  (`check_control_method.py:493`) never scanned `thread_isaac_lab/skills/` or
  `thread_isaac_lab/orchestrator/` — guard-blindness by **scan root**, the same class as F1 one level
  up. pN closed the guard leg same-day: expanded guard banked `7803f58f17` (§4b; selftest 33neg/10pos;
  baseline snippet hits=[] → must-fire BODY-ALIAS after fix) = **F3 guard mechanism PASS-CLOSE**.
  **B3 correction (pN, adopted — supersedes v1.0's "4 writes" framing)**: `skills/snapshot.py` carries
  **3** prohibited body writes — `:119 state_0.body_q.assign`, `:120 state_0.body_qd.assign`,
  `:128 body_q_prev` local-alias — while `:121 fk_state.joint_q.assign` is **sanctioned FK scratch,
  not a violation**. Confirmed by my canonical-guard run: exactly 3 `snapshot.py` FAIL lines, `:121`
  absent. The writer is live: `orchestrator/routing_orchestrator.py:59` imports it on the
  retry/rollback path (read directly this session).
  **snapshot.py writer remediation = separate owner gate, HOLD** — out of the p4 lane, not touched
  (§運用24). Related: `scripts/newton_routing_utils.py` is library code misfiled under `scripts/`
  (11-consumer closure incl. `envs/route_executor.py`); pN reclassified it env-class by placement,
  action unchanged PHYSICS_REWRITE, no solo land (manifest v2.1 §1).
  ⇒ **envs Layer8 = 0 is true (both guards) and necessary; "envs kinematic-clean" is still not
  claimed** — the canonical surface carries `skills/snapshot.py` 3 with a live caller.
- **A4 (panel correction, folded)**: the alias `import warnings as _warnings` was proposed on a *wrong*
  justification (a local `warnings` list in one function cannot shadow the module in another). Plain
  `import warnings` was adopted — matches repo convention (~43 plain, 0 aliased) and was verified to
  work. Two functions bind a local `warnings` (`:152`, `:181`); neither uses the module.
- **Terminology (folded)**: this is *removal with name/signature retention + fail-close shim*, not a
  deprecation in the sense AGENTS.md means (228 in-repo `DeprecationWarning` sites all keep working
  after warning). The AGENTS.md rule also scopes to `source/<package>/`, not `thread_isaac_lab/`, and
  this symbol is not exported (`envs/__init__.py` `__all__` has no chain symbol). The *shape* is the
  house pattern (`envs/route_executor.py:1683-1694` does the same). **Do not bank this as precedent
  that "IsaacLab deprecations may raise."**
- **Facade now certifies a dead leg (records-only)**: `verify_env_api` returns `ready=True` identically
  before and after the import capability was destroyed — an information-zero check. pN forbade touching
  the facade, so this is recorded, not fixed.
- **Guard positive control lost**: `_assign_array` was the only live in-repo exercise of the
  helper-param taint path; the guard's comments at `check_control_method.py:137,343` now reference a
  deleted symbol. A synthetic fixture would restore the control. Guard owner = pN.
- **Pre-existing format drift, deliberately not absorbed**: `ruff format --diff` wants to collapse the
  ternary at `chain_runtime_state.py:50-56` (inside `ChainRuntimeState.summary()`), untouched by this
  edit. Absorbing it would put unrelated lines in this commit (AGENTS.md atomic commits). Carry to
  landing, where the full pre-commit flow runs.
- **§14.20:505 supersession**: that ruling fenced "env writer disposition + source edit" to a separate
  gate, "handled at landing". pN's 08:04 GO reopens it now, in the worktree. Recorded so a later reader
  does not read §14.20 as still governing.
- **DDR #25 staleness**: its status text ends `⛔impl 認可なし`, written 03:45 — before the 08:04 GO.
  Read as stale, not conflicting; the GO is worktree-scoped and lifts no landing HALT. Reflection at
  verdict (07-18 reflect-verdicts-only rule), owner p6.

## 6. Gates run

`[L-TRIAGE]` → **L3** (`solver` keyword, semantically load-bearing: the deleted `solver.body_q_prev`
write) · `[DEFER-RECON]` → **PASS**, no FOUNDATIONAL DDR item supplies a premise this chunk stands on
(record: `scratchpad/c17_F2_DEFER_RECON.md`) · `[VERIFY]` → 5-lens adversarial panel (API/contract,
removal-completeness, consumer/regression, charter-conformance, null-hypothesis advocate); **5/5
SURVIVES_WITH_AMENDMENTS**, null defeated for "do not proceed", survives as a constraint on what may be
claimed afterwards (§5 F3). All amendments folded **before** [CHANGE] · `[RULE-CHECK] stage2` → Tier 0-4
ALL PASS · `[CHANGE]` → banked · `[RESULT]` → this document.

**Not claimed**: no landing, no run, no training, no "envs kinematic-clean". Remaining to canonical
Layer8=0 = the scripts 125 (manifest v2) **plus** `skills/snapshot.py` 3 (separate owner gate, HOLD).
The F3 scan-root gap itself is closed (guard `7803f58f17`); what remains open is the writer it exposed.

## 7. Records-fix log (v1.1)

| ver | as-read sha256 | change |
|---|---|---|
| v1.0 | `fb5b432b506f247ce67e33afbc5060a74c2dbfaee6b69cfebacedca635a3e504` | initial (dispatched 09:16) |
| v1.1 | (= the banked c18 blob of this file) | pN 09:24 verdict fold: **B1** wrapper×3 PASS demoted → wrapper×1 banked (approach, committed) + grip/aerial NON-BANKED OBSERVATION/carry (§2 table, §3) · **B2** acceptance runner banked as `c17_f2_acceptance_runner.py` + `_OUTPUT.txt`, scratchpad reference superseded (§2) · **B3** snapshot.py = 3 violations not 4; `:121` fk joint_q = sanctioned FK scratch (§5) · §4b canonical F3-guard delta 131→128 added with p4 independent reproduction · footer restated against the canonical surface |
