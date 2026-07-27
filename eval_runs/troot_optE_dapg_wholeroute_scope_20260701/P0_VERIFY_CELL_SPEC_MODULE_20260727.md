# P0 — pre-landing verification of `ur15_cell_spec.py`

date: 2026-07-27 (measured at dispatch)
author: w2:p0 — verifier of the UR15 lane (`RSTECHLEAD_ROLE_BRIEF_p4_20260727.md:33`)
target: `p4_ur15_sim_20260727/ur15_cell_spec.py`
pin: **sha256 `4d8625ac59856700eb5a34af9e40b16dee49173b120f4ea2a72b93622bc35c0a`** — re-derived, matches. commit `646dd42741` present, 231 lines.
method: read the module, **ran it** (`env_isaaclab7`, pure python, no simulation), ran its `guard()`
        over every driver, and probed the guard with six binding forms.
⛔ out of scope per -224: whether the drivers should be wired to it (p5's ruling).

---

## 0. Verdict

| p4's claim | verdict |
|---|---|
| ① Tier A = imported, **0 transcriptions** | ⚠ **one exception** — `CLIP_COLLIDE = True` at `:58` is a literal |
| ② clip = AST read + 90° turn, **cross-locked** to p5's table | ✅ **confirmed by running it** |
| ③ guard = AST **value comparison**, catches tuple targets | ⚠ **tuple targets confirmed; "value comparison" is not what `guard()` does** |
| ④ 21 / 21 / 21 and 14 / 14; **agrees with p5's independent 21** | ✅ counts exact — ⛔ **the agreement with p5's 21 is a coincidence of two different quantities** |
| ⑤ `float_z` fail-closed | ✅ confirmed |
| my -206R three fixes | ✅ **all three reflected** |

**Holes found: 3.** One is load-bearing (§4).

---

## 1. ✅ Confirmed by execution

`python ur15_cell_spec.py` exits **0** and prints `self-check: all sources agree`. That check is
not decorative — it compares three things and all three hold:

- the clip read out of `newton_skill_env_base.py` by syntax tree and turned a quarter turn
  equals p5's table **exactly** (5 boxes, printed and compared);
- `seat_z(0)` equals `task_config.GROOVE_CENTER_Z` to 1e-12 — the two ways of writing 0.809 agree;
- `40 × 0.015 = 0.600 m`, the length `task_config.py:135` states.

Tier A resolved live: `TABLE_TOP=0.8 CABLE_R=0.004 CABLE_N=40 CABLE_SEG=0.015
GRIP_HALF_SPAN=0.044 GROOVE_CENTER_Z=0.809 solref=(-40000.0,-400.0)
friction=(1.0,0.005,0.005)`.

⭐ The cross-lock is the strong part of this module: the clip is **read**, not copied, and then
checked against an independently written table, so either side moving breaks the check rather
than passing quietly.

### 1.1 My three fixes are in

| fix (-206R) | where | state |
|---|---|---|
| cite `:136 CABLE_SEG_LEN`, not the `:135` comment | `:47` — *"the variable, not the comment the spec §3 cited"* | ✅ and the run shows 0.015 |
| the seat cannot be read as one row | `:52` imports `GROOVE_CENTER_Z`; `:144-150` `seat_z(float_z_m)` takes the float as a **parameter** and builds 0.009 from `CLIP_BASE_HEIGHT + CABLE_R`, both Tier A | ✅ and `self_check` ties the two together |
| a byte sha is not a gate | `:154-156` says so explicitly | ✅ |

---

## 2. ✅ Counts confirmed exactly

Running `guard(driver, strict=False)` over the directory:

| file | redefinitions |
|---|---|
| `ur15_steps.py`, `ur15_steps_c1seat.py`, `ur15_steps_reaim.py` | **21 each** |
| `ur15_cell.py`, `ur15_route.py` | **14 each** |
| `ur15_yoke_video.py` / `ur15_grip_video.py` / `ur15_final_video.py` | 8 / 6 / 5 |
| the five probes and `p4_pd_video.py` | **0** |
| **total** | **110** |

⚠ The directory now holds **14** `.py` files, not the 12 p5 analysed — `probe_claw_floor.py` and
`probe_finger_reach_below_cable.py` were added today. Both return 0, so no count changes.

---

## 3. ⛔ Refuted: the agreement between the two 21s

p4 reports 21 and notes it **agrees with p5's independent count of 21**. Measured, the two sets
are not the same kind of thing:

- **p5's 21** = constants whose **values disagree across files** (spec `:21`, of which 10 change
  the physics and 11 are legitimate run-to-run differences).
- **p4's 21** = names **redefined inside one driver** that this module owns — `ur15_steps.py`
  binds 21 of the module's 27 owned names.

The populations differ (27 owned names vs a cross-file disagreement set), the unit differs (names
in one file vs constants across twelve), and the two numbers landing on 21 carries no information.

⇒ ⛔ **it is not corroboration.** This is the fourth time today two unrelated quantities have
shared a number here — Ø8 cable vs the 8.00 mm band, `0.088` DH links vs the grasp span, and
p18's own §63. The right reading is: p4's count is correct, p5's count is correct, and neither
checks the other.

---

## 4. ⛔ Hole 1 (load-bearing): `CLIP_H` is not owned, so the guard cannot see it

`"CLIP_H" in _OWNED` → **False**.

`CLIP_H` is one of p5's **ten physical** disagreements — the clip wall at **0.070 in two files and
0.026 in three**, the split p6 found and the one p5 cites as proof that *"that clip"* was not a
single object.

The module supplies the clip as `CLIP_PARTS` (the whole 5-box table), which does contain the wall
height, so the **value** is available. But the guard's reach is exactly the module's own name
set, so a driver that keeps `CLIP_H = 0.026` and uses it **passes the guard**.

⇒ 9 of p5's 10 physical constants are owned; `CLIP_H` is the one that is not. Whatever the
drivers are meant to call the wall height, the guard should own that name too, or the constant
that caused this whole exercise is the one it cannot catch.

## 5. ⚠ Hole 2: four module-level binding forms pass the guard

Probed with six forms; the guard walks `ast.Assign` / `ast.AnnAssign` targets in `tree.body`:

| form | caught |
|---|---|
| `CABLE_R = 0.005` | ✅ |
| `GROOVE_W, TILT = 0.016, 1.0` (tuple target) | ✅ — **p4's claim confirmed** |
| `CLAMP += 1` (augmented) | ⛔ no |
| `from math import pi as TILT` (import alias) | ⛔ no |
| `for CLAMP in range(3):` (loop target) | ⛔ no |
| `if (CABLE_R := 0.005):` (walrus) | ⛔ no |

The realistic one is the **import alias** — it is a normal way to shadow a name and reads as
innocuous. The other three are unlikely in these drivers. Cheap to close: extend the target walk
to `AugAssign`, `For`, `NamedExpr`, and `ImportFrom`/`Import` aliases.

## 6. ⚠ Hole 3: `CLIP_COLLIDE = True` is a transcription inside Tier A

`:58` `CLIP_COLLIDE = True  # clip design §6-A: newton_skill_env_base.py:1908 / :1925 are unconditional`

That reading is right — I verified those two lines set `0x6` with no condition. But the value is
**written down**, not imported and not read by syntax tree, and `self_check` does not test it. If
those lines ever become conditional (the way `test_newton_clip_routing.py:1168` gates the same
flag on `CLIP_COLLISION`), this module keeps saying `True` silently.

It is the one place the module does what its own docstring warns against, and it is a one-line
fix: read the flag off the syntax tree the same way `_v_groove_clip_parts` already is, or assert
in `self_check` that both lines are unconditional.

---

## 7. On claim ③'s wording, and why the substance is still fine

`guard()` does **redefinition detection only**. The value checks live in `self_check()` and cover
three derived relations. So "guard = AST value comparison" overstates what that function does.

⭐ The substance is nonetheless right, and by a stronger route than I asked for: I asked for value
comparison because I expected a **copy** to exist. There is no copy — Tier A is imported, so the
value *is* the source's and there is nothing to compare. Import beats collation. The wording
should follow the code.

---

## 8. Following p18 -229 (p5's ruling ②)

- **`float_z` fail-closed stays correct as a mechanism**, but `:133-136` gives as its reason a
  question the ruling has just voided ("whether STEP 8 opens the fingers at the seat"). The
  mechanism survives, its stated reason does not — the same repair shape used all day.
- ⚠ One question for the next revision, not a defect now: **fail-closed and "default 0" are
  different dispositions.** Once the spec records float_z = 0 as settled, a `float_z()` that
  raises is failing closed on something that is no longer open, and should return 0.0.
- **REST**: p5's final self-assessment is that §4's REST rows have **no grounds**. The module at
  `:113-119` calls them "⚠ weak" and already records that p4's own measurement does not reproduce
  the quoted note — and note that `REST_TOP = TABLE_TOP + 0.150` while the comment it quotes says
  **+0.060**. After the ruling that comment is not weak support for 0.150; it is not support.

---

## 8.5 ⚠ The spec changed under this verification, and it kills one of the three checks

Added after MSG-P18-235. The spec is now **sha256 `76053688e6387c4203ecfdb3ac019f77b5e48fe1e486372dd16114d431e15d46`, 176 lines** (re-derived, matches), and `:63` makes `CABLE_N` a **derived** quantity — required length ÷ `CABLE_SEG_LEN`, **64** for this cell's 960 mm — noting that `task_config.py:135`'s 40 is *the env cell's length*, not a constant.

⇒ the third relation in `self_check` (`:209-212`) does not survive that change:

```python
if abs(CABLE_N * CABLE_SEG - 0.600) > 1e-9:
```

Once `CABLE_N = required_length / CABLE_SEG`, the product is `required_length` **by
construction**, so the check becomes either

- an **identity** that cannot fail (if the required length is 0.600), or
- **unconditionally false** (if it is 0.960, which the spec says it is for this cell).

Vacuously true or always failing — either way it stops discriminating. My §1 recorded this
relation as one of three that hold; that was true of the pinned module, and it is about to stop
being a test rather than start being a failure.

⭐ **What made it worth having, and how to keep it:** the check had force because
`CABLE_SEGMENTS` (`:135`) and `CABLE_SEG_LEN` (`:136`) are **two independent bindings in the
SSOT** whose product must match the length `:135`'s own comment states. That relation is still
real and can still fail, but it has to be asserted **on the sources**:

```python
assert abs(_tc.CABLE_SEGMENTS * _tc.CABLE_SEG_LEN - 0.600) < 1e-9   # the env cell's length
```

A separate assertion on the module's own derived `CABLE_N × CABLE_SEG` is fine to keep, but it
is an identity and should say so rather than look like a check.

⚠ Note the cell length itself does not move: the drivers' `32 × 0.030 = 0.960` and the spec's
`64 × 0.015 = 0.960` are the same cable at two discretisations. Only the step halves — which is
the change that halves the nearest-link sampling floor from ±15 mm to ±7.5 mm.

⇒ **Re-verification is owed against the revised module, not this pin.** Everything else in this
document is unaffected: the clip cross-lock, the seat relation, the counts, the three holes, and
the refutation of the two-21s agreement all stand.

## 9. Scope of this verification

**Did**: re-derive the pin; read all 231 lines; execute the module and its `self_check`; run
`guard()` over all 13 other files; probe the guard with 6 binding forms; check the 3 fixes;
verify `newton_skill_env_base.py:1908`/`:1925` are unconditional; confirm `CLIP_H ∉ _OWNED`.

**Did not**: re-run p5's cross-file value-disagreement extraction (I checked the *sets differ*,
not p5's 21 itself); judge any Tier B **value**; check that a driver wired to this module still
builds or runs; assess whether the drivers should be wired at all (p5's court).

⛔ No implementation, no simulation run.
