# A-group PHYSICS_REWRITE — prereg (p4, 2026-07-20 10:3x JST)

The last p4-lane fence leg (pN 10:13/10:22): exact closure + per-site plan, preregistered **before**
any A source edit. Governing design: charter §14.24 (banked c25 `e1e24617c3`) as corrected by
§14.24-a (#16/#17) and §14.23-b (#18 + snapshot disposition), banked c27 `bfc35ca87c`
(blob `e85c4e369bc0`). Facts base: call-graph materials c26 (blob `c84c2743f51e`).
**No source edit occurs under this document until pN re-readback OPENs A [CHANGE].**

## §1 Frozen closure (measured; c23 for modules, c26 per-symbol; re-asserted at execution time)

| surface | value | provenance |
|---|---|---|
| `newton_routing_utils` module consumers | **11 unique / 23 import nodes** | c23 AST, p4 ∩ pN exact |
| `test_newton_clip_routing` module consumers | **10 unique / 12 import nodes** | c23 AST (pre-c22 "18" = HISTORICAL) |
| `restore_state_snapshot` (per-symbol) | **1 caller**: `test_newton_5clip_routing.py:350` | c26 |
| `SnapshotManager.restore` live consumers | `test_step_table_dryrun.py` (`:111/:210/:226`) only; orchestrator chain = wired-dead (instantiation 0) | c26, pN FACTUAL PASS + p5 #18 concur |
| starting census (canonical, c22..c27 stable) | **35** = clip_routing 17 + routing_utils 7 + aerial 5 + snapshot 3 + grip_modes 2 + dry_run 1 | guard @ banked shas |

Execution-time gate: each bundle re-runs the closure queries at its base sha; any drift from this
table = STOP + re-prereg (freshness has a lifetime; peers commit).

## §2 Per-site plan

### Bundle A-1 (single atomic unit; expected census 35 → 6)

One decision point, several files — atomicity forced by §14.24(2) single-realization convergence,
§14.23-b(a) simultaneous body removal, and no-solo-land on `routing_utils`.

| site | FAILs | class (governing §) | action |
|---|---|---|---|
| **single realization (new)** | — | §14.24(2) | ONE physics-faithful realization (joint targets → solver step / `eval_fk` for FK reads; NO body/solver-state write), placed in the surviving shared library; all callers call it. Guard must-fire negative control: injecting a `body_q.assign` into it turns the census red. |
| `newton_routing_utils.update_kinematic_bodies:910` | (of 7) | DRIVE (訂正#15) | body deleted; call sites → realization |
| `newton_routing_utils.restore_state_snapshot:1806` | (of 7) | §14.23-b DELETE | writer body deleted; compat symbol (if kept) = F2-shape fail-closed (warn+raise before any read; provenance comment; signature preserved); no dead writer |
| `skills/snapshot.py` `restore` `:119/:120/:128` | 3 | §14.23-b DELETE | same, same commit (condition (a)) |
| `test_newton_clip_routing.py` (17) | 17 | PHYSICS_REWRITE + §14.24(3) | migrate to realization; **harness acceptance (i)-(iv)** below |
| `test_grip_modes.py:345` variant (2) | 2 | absorbed into §14.15 PS-1 | servo-aligned; `skip_bodies` = finger-exclusion semantics |
| consumers: `test_step_table_dryrun` / `test_newton_5clip_routing` | 0 own | §14.23-b(c) | retire **or** adapt to physical-reset-replay in the same bundle; if adapted → §14.24(3) acceptance applies |
| remaining 9 `routing_utils` module consumers | 0 own | adaptation | import-compat verified (symbols they import unchanged or adapted); closure re-run must stay closed |

**Harness acceptance (§14.24(3), verbatim duties)**: (i) positive control fires — injected known defect
→ FAIL; (ii) instrument identity — Fingertip Z-Check predicate measures the same quantity via
joint→FK derivation; (iii) any pre/post verdict difference attributed to physics, not instrument;
(iv) ⛔ kinematic-era PASSes are re-acquired under the actuator path. **(iv) is a RUN leg** — fenced
by the standing HALT; runs occur only under pN per-run OPEN (or the §14.10 HALT-exception class if pN
confirms it covers replacement-verification runs). Not assumed here.

### Bundle A-2 — `dry_run_43step.py` (1 FAIL; expected census 6 → 5)

Class = **typed OFFLINE-REPLAY joint-state** (訂正#16: per-frame `set_jq` render loop `:197/:227/:236`,
contract `:6-11` no-physics). Duty = **typed preserve, not migrate**: marking "visualization-only, NOT
a physics claim"; non-solver-step / non-training / non-physical-verdict.
⚠ **Dependency (pN lane)**: the banked guard has **no typed OFFLINE mechanism** (closed query over
`check_control_method.py` = 0 hits for OFFLINE). Clearing this 1 FAIL needs a guard-side typed
exemption (marked + echoed, RESET_SEED_MANIFEST-style) — guard owner = pN. Until then the row stays a
counted FAIL with this prereg as its disposition record; p4 does not self-extend the guard.

### Out of scope (unchanged)

`demo_aerial_regrasp.py` 5 = D BLOCKED_OWNER (pN ①D). Floor after A-1+A-2 = **5** (aerial only);
after A-1 alone = **6**. ⛔ No Layer8=0 claim from this prereg.

## §3 Per-bundle acceptance (uniform, from the c19-c24 pattern)

clean tree at base sha → edits → `py_compile` + `ruff check` (0 new findings) + target tests →
commit (pathspec, staged-set assert) → canonical guard at banked sha: exact expected census,
FAIL-line-count == `LAYER8_FAIL`, per-file 0 for migrated files → closure re-run (all §1 queries) →
must-fire negative control for the realization → two-key (p5 design / pN evidence) → pN readback.
`--no-verify` diagnostic commits per standing ruling; full hooks + two-key before any promotion.

## §4 Sequencing (pN C2 ruling, recorded)

**A-first.** After A-1 lands: B0/B1 artifacts whose source closure includes `routing_utils` /
`clip_routing` (producer = `policy_route_runner`) = HISTORICAL / NOT_COMPARABLE (scoped to
source-closure-dependent artifacts, not blanket) → fresh re-acquisition on the compliant substrate →
then #18 implement/re-measure there. Old-kinematic #18 verification is not repeated.

## §5 Execution order proposal (for pN)

1. A-1 as one commit (large but atomically forced; census 35→6, identity, closures, must-fire).
2. A-2 marking lands with A-1 or after; its census effect waits on the pN guard extension.
3. Two-key on the bundle → landing planning stays behind §14.9 (L3 chain + Rs sign-off) — untouched here.
