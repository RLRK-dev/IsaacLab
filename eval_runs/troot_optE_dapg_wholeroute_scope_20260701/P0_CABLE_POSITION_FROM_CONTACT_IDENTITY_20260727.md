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

## 8. Scope

⛔ No run, no new measurement of the model, no verdict. The contact-geom names are **pB's** observation, relayed via
-123; everything I add is asset geometry and arithmetic on top of it. If pB's geom list is revised, §2 and §4 move
with it. Gate unchanged; I do not self-start.
