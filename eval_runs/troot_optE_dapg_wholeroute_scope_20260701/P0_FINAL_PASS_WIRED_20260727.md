# P0 — final pass on the wired version

date: 2026-07-27 20:00 JST (measured)
author: w2:p0 — verifier of the UR15 lane
requested: **Rs verbatim, relayed as MSG-P18-341: 「配線版の最終 pass をお願いします」**
targets, pins re-derived at HEAD `a1ba2fb3db`:
- `ur15_cell_spec.py` — **sha256 `df0c7bca1778703aad8b427baa…`**, 470 lines, commit `ad7952511d` ✅ matches the relayed pin
- `ur15_steps_wired.py` — sha256 `8fd5f0130f2d0ef90129d053dc…`, 1392 lines

method: ran the module; ran the hole-③ predicate against **six** synthesised env sources including
a control; ran `guard()` over all 17 drivers; probed the contract with 16 binding and reading
forms; tested whether the override declaration reaches an importer.

⚠ p4's remaining (a)–(e) are in flight. This pass is against the version above and says so per item.

---

## 0. Verdict

| item | verdict |
|---|---|
| hole ③ — conditional detection | ✅ **closed**, 6/6 including the control |
| SOURCED — reading a constant the sanctioned way | ✅ **closed** (was my §4 finding) |
| negative literals (`REST_X`) | ✅ **closed** (was my §4.5 finding) |
| fail-closed on a constant invented tomorrow | ✅ works |
| three sets — `OWNED` / `RETIRED` / `TIER_C` | ✅ present |
| per-element three — mass / stiffness / damping | ✅ all three correct |
| **units rule + coefficient set** | ⚠ **not implemented — deliberately, with a reason. Diverges from -310/-319** |
| **`known` parameter and its branch** | ⛔ **vestigial, and the docstring's first line describes a test the body does not do** |
| **subscript integers excluded** (-259(2)) | ⛔ **not excluded** |
| **override loud print** | ⛔ **does not reach an importer** |
| template rule | ⛔ absent from this version |
| walrus binding | ⛔ still uncaught |

---

## 1. ✅ Hole ③ is closed — and it discriminates in both directions

| synthesised source | predicate | |
|---|---|---|
| **A** — C1+C2 wrapped in a statement-level `if` | `False` | ✅ **the landing condition** |
| **A2** — only C2 (`:1925`) wrapped | `False` | ✅ |
| **A3** — wrapped in an `else` branch | `False` | ✅ (my own case, not in p4's set) |
| B — spacer only, `0x6 → 1` | `False` | ✅ |
| D — ternary gate | `False` | ✅ |
| **E — unchanged (control)** | **`True`** | ✅ **not a predicate that always says False** |

The control matters: without it, a predicate hard-wired to `False` would "pass" every
counterfactual. The implementation walks the ancestor chain (`:168` `IfExp`, `:174`
`isinstance(cur, ast.If) and child in (cur.body + cur.orelse)`), so it tests conditionality itself
rather than the assigned value. **My rev3 finding is discharged.**

## 2. ✅ Reading, negatives, fail-closed, the three sets

| probe | result | |
|---|---|---|
| `from ur15_cell_spec import CABLE_R` | free | ✅ my §4 false positive is fixed |
| `import ur15_cell_spec as spec` | free | ✅ |
| `from ur15_cell_spec import *` | flagged as `*` with a reason | ✅ |
| `REST_X = (-0.300, -0.055)` | flagged | ✅ my §4.5 unary-minus finding is fixed |
| `CLIP_W = 0.012` (a new constant) | flagged | ✅ fail-closed |

`RETIRED = {CLIP_H, GROOVE_W, CLIP_RISER}`, `TIER_C`, `_OWNED` all present.

## 3. ✅ The per-element three

`CABLE_N=40  SEG=0.015  seg_mass=1.1243 g  k=0.3333`, `self_check: all sources agree`.
mass ∝ SEG, stiffness ∝ 1/SEG, damping passed verbatim — the three different scalings, each as
the source dictates.

## 4. ⚠ The units rule is not implemented, and that is a choice rather than an omission

Measured — all four give the **same** answer:

| expression | ruled treatment | actual |
|---|---|---|
| `X = CABLE_R * 2` | free (plain coefficient) | **flagged** |
| `X = CABLE_R / 2` | free | **flagged** |
| `X = CABLE_R * 1.0375` | flagged (the smuggled ratio) | flagged |
| `X = CABLE_R + 0.02` | flagged (carries units) | flagged |

The docstring states the choice outright:

> *Small arithmetic factors are not exempted — that was tempting, but "0.5 is obviously just
> arithmetic" is the same judgement call that let two files disagree about a cable radius.*

⇒ **the module implements a stricter rule than -310/-319 ruled, and gives a reason.** The reason is
of the same kind that produced `RETIRED`, so this is a divergence for p5 to accept or overturn,
not a defect. ⛔ But while it stands, **the 49 is the strict count**, and my earlier measurement is
unchanged: 26 of the 46 "carries a number" findings come from arithmetic or index literals.

## 5. ⛔ `known` is vestigial, and the summary line promises a test that is not there

```python
def _has_bare_literal(node, known):
    """Does this value expression contain a number that does not come from a name we know about?
    ...
    for leaf in ast.walk(value):
        if isinstance(leaf, ast.Constant) and …: return True
        if isinstance(leaf, ast.Name) and leaf.id not in known: continue   # still dead
```

The first docstring line describes a **derivability** test; the body implements *"contains any
number"*; the fourth paragraph describes the body and justifies it. Two of the three agree and the
one that does not is the line a reader reads first — the same shape as hole ③'s original
docstring, which cost this court two passes.

⇒ either delete `known` and its branch, or implement the derivability test. Leaving a parameter
that changes nothing invites the next reader to believe a check is happening.

⚠ **Forward note for when the rule does land:** the sanctioned reading form is
`import ur15_cell_spec as spec`, so owned names appear in expressions as **`Attribute` nodes**
(`spec.CABLE_R`), not `Name` nodes. A derivability test keyed on `ast.Name` would treat every
such expression as underivable. Both forms are currently flagged for the same reason, so this is
not visible yet.

## 6. ⛔ Subscript integers are still not excluded

`X = C[0]` → flagged. -259(2) named subscripts, `range()` and comparisons as excluded. Consistent
with §4 — if nothing is exempted, indices are not either — but it was called out explicitly, so it
should be settled rather than inherited.

## 7. ⛔ The override declaration does not reach an importer

The module declares which source supplies the bend stiffness, and marks the environment override
loudly (`:103-112`, *"NOT task_config; the producer rescales it"*). Measured: importing the module
in a fresh interpreter prints **nothing**. The declaration only runs under `__main__`.

⇒ **a driver that imports the module gets no declaration, and the driver is what runs.** Since
`CABLE_BEND_STIFFNESS_OVERRIDE` can rescale EI at runtime, a run under an override would leave no
trace at the place the trace is needed. One line at import, or a call the drivers must make.

## 7.1 ✅ (d) independently reproduced — and the promise it makes is true

Commit `5a428777b5`, sha256 `72359f781d9d4987cdf4a5b5…` — pin re-derived, matches.

| | measured |
|---|---|
| import, override **unset** | **0 lines** |
| import, `CABLE_BEND_STIFFNESS_OVERRIDE=0.02` | **1 line**, naming the variable, its value, that the EI does **not** come from `task_config.py:144`, and that `self_check()` will refuse |
| does the override actually take effect? | `k = 1.3333` = `0.02 / 0.015` ✅ — the declaration is truthful, not decorative |

⭐ And the warning makes a **checkable promise**, so I checked it:

| | `self_check()` |
|---|---|
| override set | **refuses**, citing the producer line `test_newton_clip_routing.py:928` and the consequence |
| override unset (control) | *all sources agree* |

⇒ the string's promise is backed by the body. That is the opposite of the two cases this court
corrected today — the `66.67` contract text and the `known` docstring — where the prose claimed a
behaviour the code did not have. Here the prose was checked and holds.

**(d) is closed**, on both legs: the print discriminates, and what it says is true.

## 8. Guard over every driver, measured

| driver | findings | | driver | findings |
|---|---|---|---|---|
| `ur15_steps_c1seat.py` | 71 | | `ur15_cell.py` | 28 |
| `ur15_steps_reaim.py` | 65 | | `ur15_grip_video.py` | 18 |
| `ur15_steps.py` | 63 | | `ur15_final_video.py` | 15 |
| **`ur15_steps_wired.py`** | **49** | | `probe_saddle_windows.py` | 11 |
| `ur15_route.py` | 40 | | `probe_release_bisect.py` | 9 |
| `ur15_yoke_video.py` | 26 | | four other probes | 4, 4, 2, 1 |
| | | | `probe_claw_floor.py`, `probe_handedness.py` | 0 |

Only the wired driver is being brought into the contract; the rest are untouched and would each
need their own placement.

## 9. Scope

**Did**: re-derive both pins; run the module and its self-check; synthesise six env sources and
measure the hole-③ predicate on each including a control; run `guard()` over all 17 drivers; probe
16 binding and reading forms; test the import-time declaration in a fresh interpreter.

**Did not**: judge any Tier B value; verify the wired driver builds a scene or runs; re-verify the
clip cross-lock or the counts already confirmed in earlier passes; assess p4's in-flight (a)–(e).
The template rule is absent from this version, so it is untested rather than failing.

⛔ No implementation, no simulation run.
