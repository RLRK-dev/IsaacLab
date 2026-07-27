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

## 4.6 The combined coefficient set and the inverted template, measured (MSG-P18-319)

### The combined rule adds flags; it does not only close a hole

Across every driver, **23 distinct** literals appear in a multiplication or division. The
dimensional rule frees all 23. A *plain-coefficient* set would free only some, and the rest are
**physical values that happen to be written in a multiplication**:

`0.72` ×4, `0.15` ×4, `14.0` ×4, `0.0007` ×4, `30.0` ×2, `0.0011` ×2, `0.0008`, `0.0009`,
`0.85`, `0.55`, `18.0`, `24.0`, `500`, `100.0`, `10` …

⇒ roughly half of the 23 are borderline: the unit-conversion and halving/doubling family
(`0.5`, `2`, `10`, `100`, `1000`) is plainly a coefficient; `0.0007`, `0.15`, `0.72`, `14.0` are
plainly quantities. ⭐ So the combined form **flags more than the dimensional rule did**, which is
the intent — the `1.0375` hole is exactly this class — but it should be adopted knowing it moves
about a dozen names into scope rather than only catching a smuggled ratio. ⛔ Membership of the
set is p5's; I am listing the borderline members, not choosing them.

### The inverted template rule: 23 substitutions

Of the **37** geometry + contact sites, splitting by whether *bare 0/1* alone would allow them:

| | count | attributes |
|---|---|---|
| allowed by bare 0/1 | **14** | `pos` 8, `fromto` 2, `axis` 2, `anchor` 2 |
| **need substitution** | **23** | `size`, `mass`, `friction`, `condim`, `range`, `damping`, `stiffness`, some `pos` |

⇒ a concrete and modest edit. Examples: `size="0.014 0.004 0.006"`, `pos="0 -0.012 {h+0.006}"`,
`range="-1.2 1.2"`, `condim="6"`.

### ⛔ A near-miss I caught before sending it

I was about to report that `friction="1.1 0.03 0.002"` disagrees with Tier A's
`CLIP_FRICTION = (1.0, 0.005, 0.005)`. Checking the context first:

```
:145  f'friction="{CLIP_FRICTION[0]} {CLIP_FRICTION[1]} {CLIP_FRICTION[2]}"'     <- the CLIP
:168  <geom name="cab0_g" … friction="1.1 0.03 0.002" condim="6"/>               <- the CABLE
```

The clip already substitutes from Tier A correctly. The `1.1 0.03 0.002` is on the **cable**
geoms — a different object. **There is no disagreement**, and I would have manufactured one out of
the coincidence that both attributes are called `friction`. Same shape as the day's other
same-name-different-thing findings, caught by opening the line instead of trusting the match.

⭐ What does survive: the cable's own physics is baked with no source cited — `mass="0.004"`,
`friction="1.1 0.03 0.002"`, `damping="0.010"`, `stiffness="0.12"`, `condim="6"`,
`range="-1.2 1.2"`. The inverted rule will surface all of them, and the question it raises is
**whether `task_config` owns those values** (a Tier A question) rather than a matter of style.

### ✅ The wiring is visibly working

`x0 = -CABLE_SEG * CABLE_N / 2.0`, `z0 = REST_TOP + CABLE_R`, and
`pos="{x0:.4f} {REST_Y} {z0:.4f}"` — the cable's placement is now built entirely from owned names.

## 4.7 The cable mass — p5's arithmetic verified, and one consequence they did not state

The authority is real and measured, not asserted. `task_config.py:138-139` verbatim:

> *Cable mass MODEL-TRUTH = 44.97 g (~45.0 g): capsule volume × ρ=1100 → 1.1243 g/seg × 40
> [measured: `s5_p1_probe_rev7_result.json gates.cable_mass.measured_kg = 0.04497085511684418`]*

⇒ authoritative linear density = 1.1243 g / 15 mm = **0.0750 kg/m**.

| configuration | mass per segment | segment | linear density | vs authority |
|---|---|---|---|---|
| before the ruling | 0.004 (literal) | 0.030 | 0.1333 kg/m | **1.78×** |
| **now, as wired** | 0.004 (literal) | **0.015** | **0.2667 kg/m** | **3.56×** |

Both of p5's ratios reproduce, and **p5 used the right one**: 1.78× is the configuration the
measured 127.8 mm was taken in, and sag ∝ linear density at fixed span and tension, so
127.8 / 1.778 = **71.9 mm** — p5's ~72. Their second figure also reproduces:
71.9 × (299.2/380)² = **44.6 mm** — p5's ~45.

### ⭐⭐ The consequence: the seg-halving doubled the error

The template substitutes the segment length but keeps the per-segment mass as a literal —
`:168` `fromto="0 0 0 {CABLE_SEG:.4f} 0 0" … mass="0.004"`. Halving the segment while holding the
mass per segment **doubles the mass per metre**. So as currently wired the cable is 3.56× too
heavy rather than 1.78×, and a run would show roughly

**127.8 × (3.556/1.778) = 255.6 mm of sag** — twice the sag of the run that produced the 127.8.

⇒ **the 600 mm ruling's fidelity gain and the mass substitution have to land in the same change.**
Taken alone, the ruling improves the quantisation floor from 15.0 to 7.5 mm and simultaneously
doubles the linear-density error. Total cable mass as wired is 40 × 4 g = **160 g** against the
authority's **45 g**, whose service load `:141` puts at 0.44 N.

⚠ The 255.6 mm is a scaling estimate on the same three free variables p5 named, not a measurement,
and it inherits the provenance caveat on the source log. The falsifier is the same single run p5
already specified — mass restored, same span.

✅ And my L² selection stands for the reason p5 gives: both the measured value and the baseline it
was compared against came from the same heavy cable, so choosing between L² and L⁴ was a ratio
question and the common factor cancels.

## 4.8 The damping question, settled by one read (MSG-P18-331)

**Answer: no — the damping is not the same shape as K. It carries no `SEG` dependence at all.**

Read from `test_newton_clip_routing.py`, all three per-element quantities:

| quantity | per-element form | line | `SEG` dependence |
|---|---|---|---|
| mass | `cable_cfg.density * π * CABLE_RADIUS**2 * CABLE_SEG_LEN` | `:907`, `:1020` | **∝ SEG** |
| stiffness | `CABLE_MUJOCO_BEND_K = _CABLE_EI_ACTIVE / CABLE_SEG_LEN` → `"mujoco:dof_passive_stiffness"` | `:928` → `:1012` | **∝ 1/SEG** |
| **damping** | `"mujoco:dof_passive_damping": CABLE_BEND_DAMPING` — **verbatim** | `:1013` | **none** |

⇒ halving `SEG`: mass per segment **halves**, stiffness per joint **doubles**, damping per joint
**does not change**. That is exactly p5's "mass and stiffness, opposite 2× each", and it completes
the set: **damping needs no correction.**

⚠ Whether a bending damping *should* be `SEG`-independent is a modelling question — a continuum
damping coefficient would scale like the stiffness. I am reporting what the implementation does,
which is what was asked; the physical question is not mine.

### 4.8.1 By-product: the docstring's `66.67` is stale by 200×

`:920` states the contract as *"k = EI/L = 66.67 N·m/rad"*, and `:943` repeats it. But `:928`
computes `0.005 / 0.015 = 0.3333`. **66.67 implies EI = 1.000**, whereas `:144` carries
**EI = 0.005** — the human VISUAL "power-cable-floppy" pick of 2026-06-19. And `task_config:147-148`
gives the realistic Ø8 window as `1e-3 .. 5e-2`, so 1.000 is twenty times above its top.

⇒ the two docstrings record a pre-floppy EI and were never updated. The code is right; the contract
text next to it is not.

### 4.8.2 By-product: the stiffness is env-var dependent

`:928` `_CABLE_EI_ACTIVE = float(os.environ.get("CABLE_BEND_STIFFNESS_OVERRIDE", "") or CABLE_BEND_STIFFNESS)`

⇒ **`CABLE_MUJOCO_BEND_K` is not a pure function of `task_config`** — an environment variable
rescales it at runtime, documented at `:922-926` as a 0-commit probe override. So a template that
substitutes the bend stiffness is reading a runtime-variable quantity, and a Tier A entry for it
would need to say so. ⭐ Structurally the same shape as the clip-collision flag gated on
`CLIP_COLLISION` — worth noting because that one has already cost this court two passes.

## 5. Scope

**Did**: re-derive both pins; read the guard; reproduce the 49; classify the reasons; prove the
dead branch by running the predicate with two different `known` sets; confirm the subscript cases
against the source lines.

**Did not**: the final pass — the three p5 decisions (49 names / `FLOAT_Z` / hole ③ A) are still
open, and hole ③ A is still the landing hold from the rev3 pass. I have not re-run the
counterfactuals against this commit, nor verified the wired driver builds or runs.

⛔ No implementation, no simulation run.
