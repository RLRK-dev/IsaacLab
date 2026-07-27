# P0 — re-verification of the revised constants module

date: 2026-07-27 (measured at dispatch)
author: w2:p0 — verifier of the UR15 lane
target: `ur15_cell_spec.py` at commit **`cda9bc0379`**, **sha256 `59ee284b2fefb6d82378477ee31a229a022ded15b045729ccb463efb3d1424fe`**, 290 lines — pin re-derived, matches.
prior pass: `P0_VERIFY_CELL_SPEC_MODULE_20260727.md` (against `646dd42741`)
method: read the diff, **ran** the module, measured the new predicate against the real env source,
        and built **two counterfactual sources** to test the claim the rewrite makes.

---

## 0. Verdict

| claim | verdict |
|---|---|
| ruling ① implemented — SEG imported, N derived = 64 | ✅ confirmed by running |
| identity moved to the sources | ✅ confirmed — the new assertion **can** fail |
| hole ② — extra binding forms caught | ✅ **six** caught, better than the five claimed; walrus remains |
| **hole ③ — "unconditional `0x6` read by AST; turns False if it becomes conditional"** | ⛔⛔ **the transcription is gone, but the replacement does not test conditionality. The claimed behaviour reproduces for an unrelated reason.** |
| — new — guard rejects the sanctioned way of reading a constant | ⛔ **false positive** |

---

## 1. ✅ Confirmed

Running it: `CABLE_N = 64`, `CABLE_SEG = 0.015`, `CABLE_TOTAL = 0.96`, self-check *all sources
agree*, exit 0. Ruling ① is in, with the cost noted in the source (64 joints bend more easily and
cost twice the computation) — that note is the right thing to have written down.

The identity is properly relocated. The old line asserted the derived product; the new one asserts

```python
ssot_total = _tc.CABLE_SEGMENTS * _tc.CABLE_SEG_LEN
if abs(ssot_total - 0.600) > 1e-9:
```

which reads **two independent SSOT bindings** and can therefore still disagree. The comment marks
the derived form as an identity rather than deleting it silently. ✅

## 2. ✅ Hole ② — six binding forms now caught

| form | before | now |
|---|---|---|
| `CABLE_R = 0.005` | ✅ | ✅ |
| `GROOVE_W, TILT = 1, 2` | ✅ | ✅ |
| `CLAMP += 1` | ⛔ | ✅ |
| `from math import pi as TILT` | ⛔ | ✅ |
| `for CLAMP in range(3)` | ⛔ | ✅ |
| `with … as CABLE_R` | (untested) | ✅ |
| `if (CABLE_R := 0.005)` | ⛔ | ⛔ **still through** |

---

## 3. ⛔⛔ Hole ③ — the replacement measures something else

`_clip_collides_in_source()` collects every `*.shape_flags[...] = …` in the env file, records
whether the **right-hand side** is the constant `0x6`, and returns `all(unconditional[:2])`,
commented *"the two clip builders, C1 and C2"*.

Two things are wrong, and both are measured, not argued.

### 3.1 It never tests conditionality

The predicate examines the assigned value only. Nothing in it inspects whether the assignment
sits inside an `if`. The docstring's *"with no flag or environment variable in front of it"* is
not a property the code evaluates.

### 3.2 `[:2]` is `ast.walk` order — breadth-first, not source order, and not the clip builders

The file has **seven** such assignments. Measured walk order and what the slice inspects:

| | walk order | `[:2]` inspects | result |
|---|---|---|---|
| **baseline** | `1937, 1908, 1925, 1581, 1854, 1733, 1735` | **1937 + 1908** | True |
| **C1+C2 made conditional** | `1939, 1581, 1854, 1909, 1927, 1733, 1735` | **1939 + 1581** | False |

- **1937 is the C2 spacer**, not a clip builder. **1925 — the C2 clip the comment names — is never
  inspected.**
- Under the counterfactual the predicate does return **False**, exactly as claimed. But the
  `False` comes from **line 1581**, `proto.shape_flags[si] = int(newton.ShapeFlags.VISIBLE)` —
  an **arm-shape** write with nothing to do with clips. Wrapping the clip lines in an `if` pushed
  them deeper in the tree, so breadth-first ordering moved a different pair into the slice.

⇒ **the claimed behaviour reproduces, and not by the claimed mechanism.**

### 3.3 The other direction confirms it

Second counterfactual: change **only the C2 spacer** (`:1937` → `= 1`), leaving both clips
untouched. Measured: `_clip_collides_in_source()` → **False**. A non-clip shape flipped
`CLIP_COLLIDE`.

⇒ so the value is governed by *whichever two assignments breadth-first order happens to yield
first*, currently the C2 spacer and C1. It is right today by luck, and it fails in both
directions.

⚠ This is the same shape as the errors this court has been retiring all day — p11's 0.01 mm
identity, and my own claw residual measured against a saturated instrument. **A check that gives
the right answer for a reason unrelated to what it claims to measure.** It is also, precisely,
the theme the module's own docstring invokes: *the name does not identify the object.* The
comment names C1 and C2; the code selects "the first two in walk order".

### 3.4 A fix, with the part I measured marked

The clip builders use `scene.shape_flags`; the arm passes use `proto.shape_flags`. Filtering on
that and requiring **all** of them — rather than the first two — gives `1937, 1908, 1925, 1854`,
**all `0x6` today**, so it evaluates True now and flips if any one changes. ✅ measured.

⚠ Not measured: testing conditionality itself. That needs the assignment's **ancestor chain**
checked for `If` / `IfExp` (walk the tree keeping parents, or use a visitor that tracks depth in
conditionals). I am recommending it as the requirement, not as a verified implementation.

---

## 4. ⛔ New: the guard rejects the sanctioned way to read a constant

| a driver writes | guard |
|---|---|
| `import ur15_cell_spec as spec` | ✅ not flagged |
| **`from ur15_cell_spec import CABLE_R`** | ⛔ **flagged as a redefinition** |

The new `ImportFrom` handling binds the imported name, and the name is owned, so importing a
constant **from the module that owns it** trips the guard. Spec §6.1 says drivers *"read them
from one module"*, and this is a natural reading of that instruction.

⇒ either the guard exempts imports whose source module is this one, or the spec has to mandate
attribute access (`spec.CABLE_R`) and say so. One line either way, but it has to be decided
before drivers are wired, or the first driver to follow the spec literally will fail its own guard.

---

## 5. Scope

**Did**: re-derive the pin; read the full diff; run the module; enumerate all seven `shape_flags`
assignments and the walk order; build two counterfactual env sources and measure the predicate on
each; probe the guard with nine binding and reading forms.

**Did not**: implement or verify an ancestor-chain conditionality test; re-verify the clip
cross-lock, the counts, or the Tier B values (unchanged since the prior pass and still standing);
verify p5's rule implementation — **the guard's three sets are not in this version yet**, so that
part of the re-verification is still owed against a later commit.

⛔ No implementation, no simulation run.
