# P0 — the 49 unclassified names are inflated by two divergences from p5's rule

date: 2026-07-27 19:23 JST (measured)
author: w2:p0 — verifier of the UR15 lane
targets: `ur15_cell_spec.py` guard (in `d1abccdd4b`'s successor at `66d8b8747d`) and
         `ur15_steps_wired.py` @ **`66d8b8747d`**, sha256 `e49642c85aadebb585f755c9…` — pin re-derived, matches.
why now, ahead of the final pass: **p5 is about to place 49 names.** More than half of them are
artifacts of the implementation rather than of the drivers.

---

## 0. The count reproduces, and then splits

`guard("ur15_steps_wired.py", strict=False)` returns **49** — p18's number exactly.

| reason | count |
|---|---|
| *"owned by ur15_cell_spec … import it instead"* | **3** — genuine |
| *"carries a number of its own and belongs to none of the three sets"* | **46** |
| — of those 46, flagged **only** by arithmetic or index literals | **26** |

⇒ roughly **23 genuine candidates** (20 + 3), not 49.

---

## 1. ⛔ Divergence 1: the rule's qualifier is dead code

p5's rule, as ruled: *does the value expression contain **a numeric literal not derivable from
owned names**.* The implementation:

```python
for leaf in ast.walk(value):
    if isinstance(leaf, ast.Constant) and isinstance(leaf.value, (int, float)) \
            and not isinstance(leaf.value, bool):
        return True
    if isinstance(leaf, ast.Name) and leaf.id not in known:
        continue          # <-- falls through to the next iteration either way
```

The second branch does nothing: `continue` at the end of a loop body is what already happens.
`known` is computed at the call site and threaded in, but never affects the result.

**Measured, not argued:** running `_has_bare_literal` with `known` empty and with `known` full,
over every module-level binding in the wired driver — **0 names change verdict**.

⇒ the implemented predicate is *"contains any numeric literal"*. The qualifier that distinguishes
a cell constant from a piece of arithmetic is absent.

⚠ Compounding it, the call site builds `known = _OWNED | RETIRED | TIER_C | set(bindings)` — with
the driver's **own** bindings included, nearly every `Name` would count as known even if the
branch were live, so the check would be close to vacuous in the other direction too.

## 2. ⛔ Divergence 2: subscript integers are not excluded

-259(2) states the discretionary boundary explicitly: a direct numeric literal bound to a name is
always in scope; **integers inside subscripts, `range()`, and comparisons are excluded**. The
implementation walks the whole value expression and excludes none of them.

The flagged names show it plainly — every one of these is an index:

```
:187   SEAT1, SEAT2 = link_at(C1[0]), link_at(C2[0])
:1002  LX1, RX1 = C1[0] - GRIP_HALF_SPAN, C1[0] + GRIP_HALF_SPAN
:795   GL = (float(C1[0] - GRIP_HALF_SPAN), float(gL[1]), float(gL[2]))
:1004  RX_MID = 0.5 * (C1[0] + C2[0])
```

`SEAT1`, `SEAT2`, `LX1`, `LX2`, `RX1`, `RX2`, `GL`, `GR`, `GRASP1` are flagged for literals
`0`, `1`, `2` that are **tuple indices**. And `LX1`/`RX1`/`RX_MID` are derived from `C1`, `C2` and
`GRIP_HALF_SPAN` — the last of which is **owned** — so under the rule as ruled they are the
DERIVED-free case twice over.

The full list of the 26 flagged only this way includes `FLOAT_Z` (literal `0.0`, the value p5 has
just settled), `R_DES` (`0.0`, `1.0` — rotation-matrix entries) and `RX_MID` (`0.5`, a midpoint).

---

## 3. What this means for the placement

Neither divergence is a design disagreement — the guard is doing what its code says, and its code
is not yet what the ruling says. But the visible consequence is that **p5 would be asked to find a
home for 26 names that the ruled rule already frees**, including tuple indices and a midpoint's
`0.5`.

⭐ Fixing the two before the placement makes the list roughly **23** and, more usefully, makes it a
list of things that are actually cell constants.

⚠ I have not verified that all 26 are DERIVED under a corrected implementation — I measured that
they are flagged **only** by literals drawn from an arithmetic/index set, which is a necessary but
not sufficient condition. The residue after a fix should be re-measured rather than assumed.

---

## 4. ✅ Also confirmed on this version

- `RETIRED = {"CLIP_H", "GROOVE_W", "CLIP_RISER"}` — hole ① is addressed, and by the stronger
  route: the names whose existence was the divergence now fail on definition.
- `from … import *` is rejected with a reason that names the real problem (it hides its own
  bindings from the syntax tree).
- The SOURCED treatment distinguishes *owned and assigned* from *owned but imported from
  elsewhere* — the three findings in that class are the second kind, which is the case worth
  catching.
- `strict=False` is documented as a loud-printing wait rather than a pass. ✅

## 5. Scope

**Did**: re-derive both pins; read the guard; reproduce the 49; classify the reasons; prove the
dead branch by running the predicate with two different `known` sets; confirm the subscript cases
against the source lines.

**Did not**: the final pass — the three p5 decisions (49 names / `FLOAT_Z` / hole ③ A) are still
open, and hole ③ A is still the landing hold from the rev3 pass. I have not re-run the
counterfactuals against this commit, nor verified the wired driver builds or runs.

⛔ No implementation, no simulation run.
