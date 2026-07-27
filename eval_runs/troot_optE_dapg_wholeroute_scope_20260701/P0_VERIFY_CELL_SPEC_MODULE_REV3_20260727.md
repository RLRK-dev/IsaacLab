# P0 — rev3 pass: the landing condition, independently reproduced

date: 2026-07-27 (measured at dispatch)
author: w2:p0 — verifier of the UR15 lane
target: `ur15_cell_spec.py` at **`d1abccdd4b`**, sha256 `ce059296b9ad5eeb3640dfc6…` — pin re-derived, matches.
asked: MSG-P18-278 (confirm the two counterfactuals fail the new predicate) and -292 ① (independent reproduction, because p4 ran them themselves).

---

## 0. Verdict

| rev3 change | verdict |
|---|---|
| 600 mm ruling — `CABLE_N = _tc.CABLE_SEGMENTS`, special case removed | ✅ confirmed, runs, `40 × 15 mm = 0.600 m` |
| p4 removed the module-side length check themselves | ✅ confirmed — the source-side assertion is retained and can still fail |
| `REST_X` adopted | ✅ `(-0.300, -0.055, +0.245)`, matching p5 §10-1 |
| **hole ③ reimplemented as `scene.` + `all()`** | ⚠ **the selection fix works — but counterfactual A is MISSED** |

⇒ **the landing condition p5 set is not met as stated.**

---

## 1. ⛔ The counterfactuals, run against rev3

| case | predicate | |
|---|---|---|
| **A — C1+C2 wrapped in `if _clip_collide:`, right-hand side untouched** | **`True`** | ⛔ **MISSED** |
| B — C2 spacer only, `0x6 → 1` | `False` | ✅ detected |
| C — C1 (`:1908`) value `0x6 → 1` | `False` | ✅ detected |
| D — env-var gate as a **ternary**, `0x6 if _cc else 1` | `False` | ✅ detected |

Baseline `CLIP_COLLIDE = True`.

**What improved, genuinely:** the walk-order defect is gone. The predicate now reads every
`scene.shape_flags` assignment — `1854, 1908, 1925, 1937` — and requires all of them, so it no
longer depends on breadth-first ordering and no longer misses `:1925`. B, C and D all fire.

**What did not:** the predicate still examines the **assigned value** only. Nothing inspects
whether the assignment sits inside an `if`. That is precisely the part I marked *"not measured —
recommending it as the requirement, not as a verified implementation"* in the rev2 pass §3.4: my
`scene.` + `all()` recommendation fixed **which lines are read**, not **whether they are guarded**.
The accidental detection is gone and nothing has replaced it.

⇒ the docstring's *"If that ever becomes conditional this returns False"* is still a claim the
code does not implement.

### 1.1 ⭐ A mitigation that matters

The only real precedent for gating this flag anywhere in the repo is
`test_newton_clip_routing.py:1194`:

```python
builder.shape_flags[idx] = 0x6 if _clip_collide else 1
```

— a **ternary**, and ternaries **are** caught (case D), because the right-hand side stops being a
plain constant. So the historically-attested way of making this conditional is detected. The
uncaught form is a **statement-level `if`** wrapping the assignment.

That narrows the exposure considerably, and it is worth weighing against the cost of closing it.

### 1.2 Closing it

Check the assignment's **ancestor chain** for `If` / `IfExp` — walk the tree keeping parents, and
require that no `scene.shape_flags` assignment has a conditional ancestor between it and the
enclosing function body. ⚠ I have still not implemented this, so I am still recommending it as a
requirement rather than reporting it verified.

### 1.3 ⚠ Divergence from the self-run result

-292 reports p4's own five counterfactuals as all-False, *"p0's two plus per-line off ×4 plus one
unrelated writer"*. **My A, written as above with the right-hand side untouched, returns `True`.**
I cannot see p4's script, so the likely explanation is a different rendition of A — for instance
changing the value as well as adding the `if`, which case C already shows is detected. What I can
report is only what I measured on `d1abccdd4b`.

⚠ Also, as a counting note in a court that has been counting all day: *two plus four plus one* is
seven, not five.

---

## 2. ✅ Confirmed on the rest of rev3

- `:49` `CABLE_N = _tc.CABLE_SEGMENTS` — a direct import; the derivation special case is gone.
- `:145` `REST_X = (-0.300, -0.055, +0.245)` — p5's §10-1 window placement.
- `:260-270` the module-side length claim is removed with the reason written down, and the
  source-side assertion `_tc.CABLE_SEGMENTS * _tc.CABLE_SEG_LEN == 0.600` is retained. ⭐ Note
  that with a direct import those two expressions are now **the same expression**, so the
  distinction I drew in the rev1 pass has collapsed into one — the retained form is still the
  right one, for a simpler reason than when I asked for it.
- Runs clean: `CABLE_N=40 CABLE_SEG=0.015`, `40 × 15 mm = 0.600 m`, self-check *all sources agree*, exit 0.

---

## 3. ⭐ Unasked: p5's explicitly unmeasured point is in the banked log

Spec §10-1 states the absolute sag figures are extrapolation, not measurement, and adds *"実際に
は途中でテーブルに触って止まっているはずで、そこは私は測っていません"*. The judged run's log
answers it — `ur15_wide14.log:3`:

```
cable settled: x[-0.469,+0.410] y[+0.280,+0.280] z-table[+0.0262,+0.1588] ncon=6
```

- the cable's lowest point is **26.2 mm above the table** ⇒ **it does not touch the table**;
- `ncon=6` with three saddles is two contacts each ⇒ it rests on the saddles and nothing else;
- support line = `REST_TOP` 150 mm + cable radius 4 mm = **154 mm**, against a measured top of
  **158.8 mm** (+4.8 mm) ⇒ consistent with resting on them;
- ⇒ **measured sag below the support line = 127.8 mm.**

Against p5's two extrapolations for the current layout: **L² (tension-dominated) 157 mm = 1.23×
the measured value; L⁴ (bending-dominated) 2827 mm = 22.1×.**

⇒ the tension-dominated branch is the right model, and **§10-1's "unrealistic under either
scaling" is too pessimistic** — the sag is 128 mm, not thousands. p5's conclusion is untouched and
in fact strengthened: the 600 mm alternative reduces the maximum unsupported span from 380 to
299 mm, and the sag it has to reduce is a real 128 mm rather than a divergent estimate.

⚠ Scope: one run, one layout, and the 8.7 mm / 89.5 mm baseline p5 extrapolated from reached them
via p11 rather than from the log directly. The whole log carries the provenance caveat recorded in
`P0_WIDE14_ASSET_AND_LOG_PROVENANCE_20260727.md` §2 — its producing source is still not on disk.

---

## 4. Scope

**Did**: re-derive the pin; read the new predicate; run the module; build four counterfactual env
sources and measure the predicate on each; confirm the 600 mm ruling, `REST_X`, and the removed
check; compute the sag from the banked log.

**Did not**: implement or verify an ancestor-chain conditionality test; verify the SOURCED class
or the three-set guard — **not in this version**, as -278 ② states; re-check the clip cross-lock,
counts, or Tier B values, unchanged since earlier passes. p4's withdrawn `CLAWG` L/R values are
not used anywhere in this document.

⛔ No implementation, no simulation run.
