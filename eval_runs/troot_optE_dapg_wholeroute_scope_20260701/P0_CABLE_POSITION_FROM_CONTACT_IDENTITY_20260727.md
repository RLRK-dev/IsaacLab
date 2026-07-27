# P0 — where the cable was, from the contact-geom identity alone (answers -123 (3)/(5)/(7))

**From** w2:p0 (IMPL-BUILDER), measurement material for the clamp court (-096 (1)).
**Read-only asset geometry plus the contact-geom names already in pB's log. No run, no distance query, no verdict.**
⛔ I do not rule on the predicate, on grip vs capture, or on transfer. Those are p11's and p5's court, finally Rs.

Source of the geometry: `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml` (banked LOCK, tracked
and clean). Source of the contact-geom names: pB's log leg as relayed in -123 (3) — **I have not opened the log
myself**, so the identity of the touching geoms is pB's observation and not mine.

---

## 1. The pad-local z map

| geom | pad-local z span | friction |
|---|---|---|
| `pad_box2` (`:63`) | **0.00 - 18.75 mm** | 0.6 |
| `pad_box1` (`:59`) | **18.75 - 37.50 mm** | 0.7 |
| `f2ext` (`:117`) | 24.60 - 27.00 mm | 0.7 |
| `f1ext` (`:116`) | 37.00 - 39.40 mm | 0.7 |

⇒ slot between the claws = **[27.00, 37.00]**; Ø8 fully contained ⇔ cable centre ∈ **[31.00, 33.00]**.

⭐ The two backplate boxes are **stacked, not co-located**: `pad_box2` sits entirely **below** the slot. So *which*
box reported contact is by itself a statement about where the cable was in z.

## 2. ⭐⭐ The contact identity locates the cable — with no distance measurement at all

**Right arm — contact on `Rg_left_pad2` / `Rg_right_pad2` only** (pB, -123 (3)):

- touching `pad_box2` [0.00, 18.75] **and not** `pad_box1` [18.75, 37.50] ⇒ the cable's **top edge ≤ 18.75**
- ⇒ **cable centre ≤ 14.75 mm** (radius 4.0)
- ⇒ that is **at least 16.25 mm below** the containment band [31.00, 33.00]

⇒ ⭐⭐ **the R cable was never in the slot, and this is established by which geoms touched — independently of the
driver's printed distance, of `mj_geomDistance`, and of the instrument contract that has been in question all day.**

**Left arm — contact includes `pad1` among 6 faces** (pB): the cable overlaps [18.75, 37.50] ⇒ centre ∈
**[14.75, 41.50]**. ⇒ ⚠ **compatible with the slot but does not establish it** — the containment band is only
[31.00, 33.00], a 2 mm target inside a 26.75 mm compatible range.

⇒ ⭐ **the conclusion is asymmetric: R is definitively out by contact identity; L is not settled either way by it.**

## 3. ⭐ Cross-check against the driver's printed miss — and a discrepancy to flag

If the printed "slot vs cable" is (slot centre 32.00 − cable centre) in pad-local z, then R's **17.4 mm** implies
cable centre **14.60 mm**, against my contact-identity bound of **≤ 14.75 mm**.

⇒ ⭐ **consistent, and tight to 0.15 mm, from two entirely unrelated signals** (which geoms reported contact, vs a
printed scalar).

⚠ **But the same reading fails for L.** L's printed miss is 25.0 ⇒ centre 7.00 mm, which is **below 14.75** and so
**contradicts L touching `pad1` at all**. ⇒ ⛔ either the printed quantity is signed or framed differently than I
assumed, or it is not computed the same way on both arms. **I do not resolve this** — it is p4's and p11's court.
⭐ I flag it because the R agreement above would otherwise look like it validates the convention, and it does not:
**the convention that makes R agree makes L impossible.**

## 4. ⚠ A correction to -123 (5), offered as a factual narrowing

-123 (5) reads: *"R は背板とケーブルの接触が 0 ⇒ 摩擦を生む面が無い"*.

⛔ **`pad_box2` is also a backplate box and it carries `friction="0.6"` (`:63`).** R therefore **does** have
backplate-cable contact — on the **lower box, outside the slot**. What R lacks is contact on **`pad_box1`**, which
is both the face the measurement uses and the one spanning the slot region.

⇒ ⭐ the supportable statement is **"R's contact is outside the slot, on the lower pad box"**, not "R has no
friction surface." The second is stronger than the evidence carries. ⛔ Whether contact there can hold the cable is
a design question I do not answer.

## 5. ⭐ Arithmetic checks on -123 (7), confirmed

- design: face gap **4.00 mm** with Ø8 ⇒ compression **8.00 − 4.00 = 4.00 mm** (`task_config.py:277`, 2 mm/side)
- L measured face gap **6.81** ⇒ compression **1.19 mm** = **29.8 %** of design ✅ reproduces the "30%"
- ⛔ no R equivalent exists, per §2 and §4: the faces being measured are not the faces in contact.

## 6. ⭐ My instrument limitation was applied correctly by pB

-123 (6) records that pB declined to read transfer from the claw signs (L −2.44 / R −2.48) because those sit in the
**saturated** regime where the reading carries no depth information. ⇒ that is exactly the limit I recorded, used
the way it was meant. I note it because a limitation is only worth stating if it actually stops a downstream claim,
and here it did.

## 7. ⭐ -124 (4): the predicate's lower leg, expressed as compression

-124 (4) asks that taking **2.0** as the predicate's lower leg come with *"理由と量"*. The amount, on Ø8
(`task_config.py:137`) with the design at a 4.00 mm face gap (`task_config.py:277`, 2 mm per side):

| face gap | compression | per side | what it is |
|---|---|---|---|
| 8.00 mm | 0.00 mm — 0 % | 0.00 | first touch |
| **6.81 mm** | 1.19 mm — 14.9 % | 0.60 | **L measured, this run** |
| 5.68 mm | 2.32 mm — 29.0 % | 1.16 | R measured — ⛔ **not a compression**, per §2/§4 the measured faces are not in contact |
| **4.00 mm** | **4.00 mm — 50.0 %** | **2.00** | **the design's full close** |
| **2.00 mm** | **6.00 mm — 75.0 %** | **3.00** | **the predicate's lower leg** |

⇒ ⭐ **the predicate's floor admits 1.50× the design compression**, i.e. 75 % of the cable's diameter against the
design's 50 %, and it extends **2.00 mm past the design's own full close**. The design's own band, from first touch
to full close, is **[4.00, 8.00]**.

⛔ I do not propose a value. This is the *quantity* -124 (4) asked to have stated; the *reason* belongs to whoever
owns the predicate, and -124 (6) records that seat as vacant.

## 8. -126: material for the predicate p11 specified. ⛔ Not an implementation — the gate is CLOSED.

-126 (6) names me as the implementer for p11's L1/L2/L3 and says in the same breath that it is **not** an
implementation instruction and the gate stays closed. I hold to that. What follows is measurement material only.

### 8.1 p11's constants check out, and its 0.30 mm caveat is the box-edge term again

**L1 [31.00, 33.00]** and **L2 [4.0, 8.0]** both reproduce from the asset and `task_config.py` (§1 here, and
`:137` / `:277`). ⭐ p11's caveat — *evaluate L2 at the cable's z, not as the box-pair minimum, difference 0.30 mm* —
is **the same box-edge migration term** I quantified for the claws:

> 2 × |37.50 − 32.00| × sin(1.571°) = **0.302 mm**

i.e. the pad1 box's **upper edge** against the cable's z under the measured tilt. (At the box centre it would be
0.212 mm, at the lower edge 0.727 mm.) ⇒ ⭐ **third appearance of one mechanism today** — the residual in §6 of the
bound artifact, the floor-family split, and now p11's L2 evaluation point. **A box does not measure from its face
once it tilts**, and every quantity in this court that was taken between boxes has had to absorb that.

### 8.2 ⛔ The form defect is worse than a negative filter, and the naming is why

-126 (3) asks for a positive `*_pad1` match instead of "anything without `ext`". ⚠ I have **not** read p4's driver,
so I say nothing about it. But **the analogous classifier in the production env file, which I have read, is worse**:

`thread_isaac_lab/envs/newton_skill_env_base.py:1392`
```
if "pad" in (gname + bname):
    pad_geoms.append(g)
```

The geom names in the banked asset are `right_pad1`, `right_pad2`, **`right_pad_f1ext`**, **`right_pad_f2ext`**,
`right_silicone_pad` — and the **body** is named `right_pad`, so `bname` contains "pad" for **every geom on the pad
body**. ⇒ ⭐⭐ **`pad_geoms` includes the claws and the silicone visual**, regardless of their own names.

⭐⭐ **And the naming is deliberate.** The asset says so at `:112-113`, verbatim:

> *Names contain "pad" so the suite-wide contact filter (`test_newton_clip_routing.py`) keeps COLLIDE + cable
> contact.*

⇒ ⭐⭐⭐ **the claws were named to match "pad" on purpose, for the contact filter.** So any *measurement* predicate
that reuses that substring test inherits a set that was **engineered to include the claws**. ⇒ the fix cannot be
"exclude `ext`" — a later geom named without `ext` rejoins silently. It has to be a **positive match on `*_pad1`**,
which is exactly what p11 asked for, and now with the reason the trap exists.

⚠ This is **carry item 7** on my list (`:1392` production pad classifier), open since this morning. It is a second
site: fixing only the driver leaves the production env with the same set.

### 8.3 Cost: all three legs already exist as measured quantities

- **L1** — already computed and printed by the driver (-126 (4)).
- **L2** — already measured (the 6.81 / 5.68 values).
- **L3** — the contact-geom list is already in the log; pB read it to produce -123 (3).

⇒ ⭐ **no new instrumentation is required for any leg.** What is missing is that the verdict does not consult them.
⛔ I state the cost because I am named as the implementer; I am not proposing to act on it.

### 8.4 ⛔ I take no position on -126 (5)

Whether L1 is full containment [31, 33] or centre containment [28, 36] is the owner's choice. I supplied the
distinction between the two predicates and the geometry behind each; the selection is not mine, and -126 records
p11's recommendation.

## 9. Scope

⛔ No run, no new measurement of the model, no verdict. The contact-geom names are **pB's** observation, relayed via
-123; everything I add is asset geometry and arithmetic on top of it. If pB's geom list is revised, §2 and §4 move
with it. Gate unchanged; I do not self-start.
