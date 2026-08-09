# pZ — pre-registered acceptance for the four mounting C-2 edits, written **before the edit exists**

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-08-10 01:05 JST, on m-p18-267's heads-up, while p0's editor holds the ball. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Why pre-registered**: the judgment is declared before the object exists so the judge cannot fit the table to the artifact. (Unlike the wired case, nothing here *expires* — both surfaces are tracked, so the parent blob preserves every pre-edit value; the pre-registration buys bias protection, not evidence preservation.)

## 0. The commission (verbatim scope, m-p18-267 §1)

Four edits per the ACCEPTED design spec §2: **three tokens** (YOKE_SPREAD 0.28 / TILT 20.0 / CROWN_R literal 0.110) **plus the grounds comment** (witness `SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt:54`; the #54 member condition; the stereo-head absence condition; D4 rides as carry). Surfaces: `ur15_cell_spec.py` + `sweep_mounting.py`. No behavior/output-format change; past sweeps reproducible via env vars. Judged **against the edit commit's own parent** when p0 announces it.

## 1. Pre-edit baselines, measured 01:04-01:05 JST (worktree == both lock pins, verified)

- Locks are real: `ur15_cell_spec.py` last commit **`2fba2dfd67`** (its lock pin), `sweep_mounting.py` last commit **`2bb1aad4e7`** (its lock pin), both `git status` clean.
- Built tokens today: `:358` `YOKE_SPREAD = … else **0.22**` · `:374-375` `TILT = π/2 − radians(… else **45.0**)` · `:429-432` `CROWN_R = 0.0 if "none" | float(override) | (SHOULDER−Z0)/2 if Z0-override | else **YOKE_SPREAD / 2**` (derived, = 0.11 only while spread is 0.22).
- Witness read: `SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt:54` = `0.110 0.280 20 106 5 122 30 +14.7 no "both clear" PASS (7 <-> 46)` — the sole PASS row in its neighbourhood, at exactly the three token values.
- Sweep's printed built-default labels: `:169` `"0.220 (built default)"`, `:170` `"45 (built default)"`.

## 2. The seven rows

| # | row | requirement |
|---|---|---|
| 1 | surfaces | the commit touches exactly the two unlocked files; each judged from its own parent content (== the lock-pin blobs) |
| 2 | token 1 | `:358` built default `0.22` → `0.28`; the override arm survives verbatim |
| 3 | token 2 | `:375` built default `45.0` → `20.0`; the `π/2 − radians(...)` form unchanged |
| 4 | token 3 | CROWN_R's built value becomes the **literal `0.110`** — the `"none"` arm and the override arm survive; `YOKE_SPREAD / 2` must NOT remain the effective built path (at spread 0.28 the derivation gives 0.14 — the exact drift the word "literal" exists to prevent) |
| 5 | grounds | the comment names all four: witness file`:54` · the #54 member condition · the stereo-head absence condition · D4 as carry |
| 6 | no behavior/format change | override `environ.get` lines survive; diff hunks = the three values + comments only; ⭐ **and the sweep's printed built-default labels (`:169`/`:170`) must agree with the new built values** — left stale they become printed false claims about the built cell (the F1/c14 class, this time pre-registered before the edit rather than found after) |
| 7 | reproducibility | override precedence order unchanged, so the OLD cell remains expressible: `YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45 CROWN_R_OVERRIDE=0.110` reproduces today's built values numerically |

Row 6's label clause cuts both ways, recorded now: if p0 updates the labels, that is NOT a scope violation of "no output-format change" — the format is unchanged, the stale VALUE inside the fallback string is corrected; if p0 leaves them, my leg reports the stale claim as a finding, not a blocker.

## 3. What this table does not judge

Whether 0.28/20.0/0.110 are the right values (Rs2's design court already ruled; the witness is the design's). Whether anything runs (nothing does; DoD and wired remain behind Rs1 (the human)'s authorization; dep-2 stays the grade cap; DEV-C2X's 35 mm stays unruled). The instrument (`kinonly_step_solve.py`) — not a surface of this commission; its nominated blob `120746a49b` is immutable.

## 4. Provenance

Measurements from `git log -1`, `git status`, `grep -n`/`sed -n` on the worktree (== lock pins, verified first). Zero tracked-content modifications by pZ; **written, not banked; banking requested of a custodian.**
