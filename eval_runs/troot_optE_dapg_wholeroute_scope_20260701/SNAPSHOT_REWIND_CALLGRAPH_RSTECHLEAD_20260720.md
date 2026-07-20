# Snapshot-rewind call-graph materials (p4, 2026-07-20 10:1x JST)

Requested by p5 §14.24(4) (premise for the snapshot single-disposition) and made a fence item by pN
10:13. Static reachability measured at branch tip **c25 `e1e24617c3`** (clean tree, committed blobs).
Method: closed grep + AST queries over every `.py` in the tree; per-symbol (not per-module) caller
attribution.

## Q: does the per-STEP rewind sit on the training path?

**A: No — at c25 both rewind implementations are statically unreachable from any live entry point.
The orchestrator's retry engine is dead code; the script twins are standalone.**

## Implementation A — `skills/snapshot.py` `SnapshotManager.restore` (the skills-bucket 3: `:119/:120/:128`)

| edge | file:line | status |
|---|---|---|
| import + instantiate | `orchestrator/routing_orchestrator.py:59` / `:792` | in-module only |
| wrapper | `restore_snapshot:1292` | called from exactly 2 sites |
| call site 1 | `execute_step:1129` (RL TIMEOUT/FAIL retry; enclosing def `:1058`) | **`execute_step` has 0 callers** (closed query: only doc mentions + `cluster_g` audit text) |
| call site 2 | `_rollback:1184` (enclosing def `:1159`) | called only from `execute_step:1131` ⇒ same dead root |
| class entry | `RoutingOrchestrator` | **instantiated nowhere in the whole tree** (only the `orchestrator/__init__.py:6` re-export + a docstring mention in `skills/scripted_skills.py:15`) |
| script consumer | `scripts/test_step_table_dryrun.py` `:50` import / `:111` instantiate / `.save :128` / `.restore :210/:226` | standalone VBD-track dry-run script — live callable, **not a training surface** |

**Correction to the §14.23(I) framing**: the open question was phrased as "does `_run_rl_episode`
reach `:1129/:1184`". Measured: **`_run_rl_episode` (`:946-1055`) contains no restore/snapshot call at
all** — the rewind lives in `execute_step`/`_rollback`, and *those* are the dead functions. The premise
question dissolves: nothing reaches them.

## Implementation B — `scripts/newton_routing_utils.py` `restore_state_snapshot:1806`

Per-symbol closure (distinct from the module's 11-consumer closure — the 11 import *other* symbols):

| caller | file:line |
|---|---|
| `scripts/test_newton_5clip_routing.py` | `:51` import, `:350` call — standalone script |
| (no other caller) | closed query over all `.py`, 0 further hits |

In particular **`policy_route_runner.py` (B0/B1 evaluator) does not call either restore** — its
`routing_utils` import is for other symbols. So the B0/B1 evidence chain never exercised the rewind.

## Consequences for the single disposition (owner = p5 design × pN scope; facts only here)

1. Both implementations can be dispositioned **without a training-path carve-out** — nothing on the
   training path reaches them today.
2. Dead-today ≠ dead-by-design: `RoutingOrchestrator` is the designed retry-engine home
   (RL-Routing-Design §14 reference). Whether the rewind concept is re-implemented physics-faithfully
   later or removed outright is a design call, not settled by this artifact.
3. The two standalone script consumers (`test_step_table_dryrun`, `test_newton_5clip_routing`) are the
   only code that would break; neither carries a guard FAIL of its own (writes are counted at the
   write-site files).
4. pN C2 sequencing ruling (10:13, recorded): **A-first**; post-A-land, B0/B1 artifacts whose source
   closure includes `routing_utils`/`clip_routing` become HISTORICAL / NOT_COMPARABLE and are freshly
   re-acquired; #18 is then implemented/re-measured on the compliant substrate — not verified twice on
   the old kinematic substrate.
