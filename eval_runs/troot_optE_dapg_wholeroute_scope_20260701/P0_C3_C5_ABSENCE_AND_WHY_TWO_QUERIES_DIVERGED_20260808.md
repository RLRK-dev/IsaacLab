# P0 — do C3/C4/C5 exist in the live path, and why did two queries for them disagree

date: 2026-08-08 23:1x JST (measured)
author: w2:p0
why I ran it: m-p18-107 §1 fixes the chunk DoD at **canonical 1-18 in the C-2 cell — two clips of
five** — and leaves one divergence open with no cause attached. That scope is the input to the
implementation I am to perform, so I measured its precondition rather than inheriting it.
read at: `HEAD` (tracked `.py`, repo-wide).

---

## 0. Verdict

| item | verdict |
|---|---|
| does any tracked `.py` **use** a C3/C4/C5 clip? | ✅ **no** — `rc=1`, with a passing positive control |
| the spec module's clip definitions | ✅ `C1` `:485`, `C2` `:486`, and nothing else |
| p18's two unexplained files | ✅ **explained — two different reasons, neither a UR15 clip** |
| the cause of the divergence | ⭐ **the query form: `"C3"` as a quoted string is non-discriminating — 19 files** |
| ⛔ my own slip while measuring this | **I took `rc` from a pipeline's last stage** — the lesson relayed to me seven minutes earlier |

---

## 1. ✅ No C3/C4/C5 clip exists in tracked `.py`, and the predicate is controlled

```
git grep -nE '\bC[345]\b[[:space:]]*=|\bC[345]\[' HEAD -- '*.py'     -> rc=1, no matches
```

`rc=1` from `git grep` itself — the command ran and found nothing. **Positive control**, same
predicate shape against clips that do exist:

```
git grep -nE '\bC[12]\b[[:space:]]*=' HEAD -- '*ur15_cell_spec.py'   -> rc=0
  ur15_cell_spec.py:485:C1 = (0.150, CLIP_Y_ODD)    # spec §6.4d -- first clip, on the near row
  ur15_cell_spec.py:486:C2 = (0.040, CLIP_Y_EVEN)   # spec §6.4d -- second clip, on the far row
```

⇒ the predicate finds a clip when there is one, and returns nothing when there is not. The absence
is measured, not an empty pipe. **p4's and p18's reading is confirmed independently.**

## 2. ⭐ The divergence: p18's two files are hits of two different kinds, and neither is a clip here

| file | what its `"C3"` actually is |
|---|---|
| `eval_runs/…/pin_ab_lifecycle_probe.py:167/169/177/179` | `legs["C3"]`, `legs["C4"]` — **test-leg labels** in a pin lifecycle probe. Not clips at all |
| `thread_isaac_lab/scripts/wet_run_full_sequence.py:223-225` | `("C3", 0.35, 0.0)`, `("C4", 0.40, -0.075)`, `("C5", 0.35, -0.15)` — **genuine clips**, in a non-UR15 script |

⇒ **one query, two failure modes, stacked**: the first hit fails on the **role** of the token
(label, not clip); the second fails on the **population** (a different arc's script, not a UR15
driver). A quoted-string query for `"C3"` cannot separate either from a real clip definition.

**The measure of how non-discriminating it is:** bare `\bC3\b` over tracked `.py` matches **19
files**.

⇒ the divergence needs no new mechanism. It is p18's own §1203 (read the hit's **role**) and §1193
(membership is not cardinality) arriving together in one query. The conclusion was never at risk —
what differed was what the two forms could tell apart.

## 3. ⛔ My own slip, seven minutes after the lesson reached me

My first run of §1 printed `rc=0` and no lines, and I nearly read that as "matches exist". The `rc`
came from **`head`**, the pipeline's last stage — not from `git grep`. That is exactly the rule
pZ measured and p18 relayed to me at 23:09: *a pipeline's rc belongs to its last stage.*

I caught it because `rc=0` with no output is self-contradictory, and re-ran with the rc taken from
the command itself. ⚠ **The tell was luck of arithmetic**: had the true answer been "matches exist",
`rc=0` would have looked correct and I would have banked a number I had not measured.

⇒ **`rc` has to be captured from the command, not from the pipeline.** This is my fourth instrument
hole tonight and the second one that a rule reached before the error did.

## 4. Scope

**Did**: read the spec module's clip assignments; run the clip-use predicate over all tracked `.py`
with the rc taken from `git grep` itself; run a positive control on `C1`/`C2`; open both of p18's
files and read what their `"C3"` binds to; measure the bare token's file count.

**Did not**: search untracked or working-tree-only paths (this is a tracked-`.py` claim and says
so — the working-tree population needs `command grep` per the adopted division, and the history
population is unresolved); judge whether the two-clip DoD is the right scope, which is Rs's call
per m-p18-107 §1; touch anything.

⛔ No implementation, no route run, nothing started. HOLD unchanged.
