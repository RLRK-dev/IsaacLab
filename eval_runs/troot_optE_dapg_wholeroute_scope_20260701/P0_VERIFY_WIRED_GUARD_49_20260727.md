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

## 4.5 The two new rules, measured before they are implemented (MSG-P18-310)

### The units rule — the gap I went looking for is not there

I expected **call arguments** to escape a rule phrased as *multiplication/division = dimensionless,
addition/subtraction = carries units* — `math.radians(20.0)` puts a real cell constant in neither.
Measured: **0 bindings** in the wired driver have their only unclassified literals in call
arguments. The gap does not occur here. Reported as a non-finding.

⭐ What the census does show is that the two named kinds are a small minority. Every numeric
literal site among the module-level bindings, by immediate syntactic parent:

| parent | count | rule says |
|---|---|---|
| bare inside a tuple/list/dict | **86** | bare literal — in scope ✅ |
| subscript | 67 | excluded ✅ |
| **unary (a negated literal)** | **13** | ⚠ **not named** |
| mul / div | 9 | dimensionless ✅ |
| add / sub | 8 | carries units ✅ |
| comprehension (`GeneratorExp` / `DictComp`) | 4 | ⚠ **not named** |
| call argument | 1 | ⚠ not named — but harmless here |
| comparison | 1 | excluded ✅ |

⇒ **the negated case is the one that matters**: `REST_X = (-0.300, -0.055, +0.245)` is a **Tier B
value**, and each of its entries parses as `UnaryOp(USub, Constant)`, not as a bare constant. An
implementation that classifies by immediate parent will not see them as bare literals. Folding
`UnaryOp` over a numeric constant into the bare case fixes it; leaving it out loses the very row
the 600 mm ruling just added.

### The template rule — the attribute list has to be wider than "geometric"

Counting XML attributes in the wired driver that carry a number the f-string does not substitute:
**59 sites across 28 distinct attributes**.

| group | attributes | sites |
|---|---|---|
| geometric | `pos` 11, `size` 8, `fromto` 2, `axis` 2, `anchor` 2, `range` 2 | **27** |
| **contact / physics** | `friction` 2, `damping` 2, `stiffness` 2, `condim` 2, `mass` 2 | **10** |
| rendering / viewer | `rgba` 6, `ambient`, `diffuse`, `specular`, `offwidth`, `offheight`, `znear`, `width`, `height`, `texrepeat`, `reflectance`, `rgb1`, `rgb2`, `timestep`, `contype`, `conaffinity`, `type` | 22 |

⇒ a geometry-only list covers **27 of 59**. The **contact group is the one worth adding**: the
cell spec already owns `CLIP_SOLREF` and `CLIP_FRICTION` at Tier A, so a `friction=` or
`stiffness=` baked into a template is the same failure the rule exists to catch, one axis over.
The rendering group is genuinely run-specific and can stay out.

⚠ My attribute scan is a regex — it strips `{…}` and looks for a remaining digit — so the counts
are indicative, and at least one (`type`) is a false positive from a digit inside a non-numeric
value. The grouping is the point, not the exact totals.

## 5. Scope

**Did**: re-derive both pins; read the guard; reproduce the 49; classify the reasons; prove the
dead branch by running the predicate with two different `known` sets; confirm the subscript cases
against the source lines.

**Did not**: the final pass — the three p5 decisions (49 names / `FLOAT_Z` / hole ③ A) are still
open, and hole ③ A is still the landing hold from the rev3 pass. I have not re-run the
counterfactuals against this commit, nor verified the wired driver builds or runs.

⛔ No implementation, no simulation run.
