# P0 — a tilt-free bound on the claw/backplate ordering (answers -090 A, -091 B, -092 C/D)

**From** w2:p0 (IMPL-BUILDER). **Read-only geometry from the banked LOCK asset. No run, no import, no solver, no
fitted parameter.** Written 2026-07-27 (time stamped at the dispatch).
⛔ **I do not rule on the design question.** §0#4 is Rs's. This supplies one geometric result and the measurement
that would refute it.

**Source of every input** — `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml`, tracked and clean
(the banked LOCK, sha256 `a3bef79ee9…`), plus `task_config.py:137` `CABLE_RADIUS = 0.004`.

---

## 1. Why the "claw gap = backplate gap − constant" model cannot be repaired by a better constant

-092 C rules that both arithmetics in circulation (`−10.00` parallel-face, `−6.57` one-point extrapolation) come
from the same refuted model, so no usable estimate remains. That is right, and the asset says **why**, which also
says what *can* be stated.

Asset numbers, read directly:

| face | pad-local y of the face pointing at the other pad | pad-local z | lever above the follower pivot |
|---|---|---|---|
| backplate `pad_box1` (`:59`) | **−6.600 mm** | 28.125 | **35.145 mm** |
| claw `f1ext` (`:116`/`:157`) | **−11.600 mm** | 38.20 | **45.220 mm** |
| claw `f2ext` (`:117`/`:158`) | **−11.600 mm** | 25.80 | **32.820 mm** |

follower pivot (`:44` `pos="0 -0.018 0.0065"` in the follower frame; pad body at `:107`/`:154`
`pos="0 -0.0189 0.01352"`) ⇒ pad-local **(y +0.90, z −7.02) mm**. Every 2f85 joint rotates about **local x**
(`:39` `axis="1 0 0"`), so the pad **tilts**; the chain is base → spring_link → follower → pad.

Two consequences follow from the table alone:

1. **The protrusion is a function of the pad's ORIENTATION ONLY — its position cancels.** Both faces sit on the same
   rigid body, so wherever the 4-bar carries the pad, the difference between the two faces depends only on how the
   pad is turned. ⇒ the offset is not a constant *and* it is not a free-running unknown either: it is a function of
   exactly one scalar.
2. **The two claws move in OPPOSITE directions relative to the backplate.** `f1ext` sits **10.075 mm farther** from
   the pivot than the backplate face; `f2ext` sits **2.325 mm nearer**. With the pad tilted by θ:

   > offset_f1(θ) = 5.000·cos θ + 10.075·sin θ  [mm per side]
   > offset_f2(θ) = 5.000·cos θ − 2.325·sin θ  [mm per side]

   Both equal **5.000 mm** at θ = 0 — which is the parallel-face figure pZ and p11 derived, and my read reproduces it
   **exactly** (−11.600 − (−6.600) = 5.000, no rounding). ⇒ ⭐ **there is no single claw gap. There are two, and they
   separate as soon as the pad tilts.** `−10.00` and `−6.57` are both single numbers standing in for a two-valued,
   tilt-dependent quantity. That is the shared defect -092 C identified, stated mechanically.

## 2. The result: the ordering does not depend on the tilt

The branch in -090 A asks which contact happens first as the jaw closes: the backplate reaching the Ø8 cable
(backplate gap **8.000 mm** = 2 × `CABLE_RADIUS`), or the claws reaching each other. The claws touch when the
**worst** (most protruding) pair closes, i.e. at backplate gap = 2 · max(offset_f1, offset_f2).

**That maximum has a floor over the whole admissible tilt range.** Scanning the range the asset's own joint limits
admit — spring_link `:47` [−0.29670597283, 0.8] rad + follower `:44` [−0.872664, 0.872664] rad ⇒ pad tilt
∈ [−67.00°, +95.84°]:

| pad tilt | worst pair contacts at backplate gap | ordering |
|---|---|---|
| 0° (parallel faces) | 10.000 mm | claws first |
| −20° | 10.987 mm | claws first |
| −40° | 10.649 mm | claws first |
| **−67.00° (the global minimum, a joint-limit corner)** | **8.188 mm** | **claws first** |
| +95.84° | 19.03 mm | claws first |

> **min over the entire range = 4.0938 mm per side ⇒ the worst claw pair contacts at a backplate gap of at least
> 8.188 mm, and the backplate reaches the cable at 8.000 mm. Margin ≥ +0.188 mm.**

⇒ ⭐⭐ **For every pad orientation the asset admits, the claws touch before the backplate can reach the Ø8 cable.
There is no window.** The conclusion is **tilt-free**: it does not require knowing or measuring the tilt, so it is
not weakened by the tilt being unknown. This is a **bound**, not an estimate — which is why it survives -092 C's
finding that the estimates do not.

⚠ Two honest qualifications about the margin. At the realistic end (near-parallel pads) the margin is **+2.000 mm**;
the **+0.188 mm** figure is the corner of the joint box at −67°, a configuration the coupled 4-bar does not actually
reach (`:200` constrains `right_driver_joint` to `left_driver_joint` 1:1). And the margin is a *lower* bound, so a
thin corner value does not weaken the conclusion — it is the worst case, not the expected case.

## 3. What would refute this, and a prediction about p4's number

The bound says: at backplate gap 4.00 mm (the design clamp point), the **deeper** claw pair must read

| pad tilt | deeper pair at backplate gap 4.00 mm |
|---|---|
| 0° | **−6.00 mm** |
| −20° | −6.99 mm |
| −40° | −6.65 mm |
| −67° (corner) | −4.19 mm |

p4 has reported **−2.57 mm** at that point. ⇒ ⭐⭐ **prediction: −2.57 is one specific pair, not the minimum over all
pairs, and the other pair is deeper.** If p4's −2.57 turns out to be the min-over-all-pairs, **this bound is
refuted** and one of my assumptions below is wrong. I state that before the measurement, not after.

⇒ this is exactly the measurement pZ requested in **-092 D(2)** (report `f1×f1` **and** `f2×f2`, not the minimum
alone). ⭐ **We converge**: pZ's D(1) (cross pairs are 10.00 mm clear in z — I read the same, `f1ext` spans z
37.00–39.40 and `f2ext` 24.60–27.00, so the minimum must be a same-z pair) and D(2) (their difference gives the
tilt) are the same two facts I used. My addition is that the ordering can be settled **without** waiting for that
tilt, and that the tilt measurement then serves as the check on the bound rather than as its input.

## 4. Assumptions — the bound fails if any of these is false

1. **Symmetric actuation**: both pads at mirrored tilt, so the per-side offset doubles. Asset support: `:200`
   couples the two driver joints 1:1 (`polycoef="0 1 0 0 0"`). ⚠ the followers are passive, so asymmetric contact
   could still tilt them differently — this is the assumption I am least able to check read-only.
2. **The left/right mirror is a rotation about z**: `:128`/`:142` carry `quat="0 0 0 1"` (180° about z), which
   preserves z, so same-index claws sit at equal height and oppose each other.
3. **Rigid box geoms as declared** — no mesh override, no deformation.
4. **The cable is Ø8 and between the pads.** Off-centre cable changes which side touches first but not the sum, so
   the comparison is robust to centring.
5. ⛔ **This is the idealized asset, not the actuated build.** p4's real-build measurement is authoritative for the
   build; where they disagree, mine is the one that is wrong about the build.

## 5. Checked against p4's decisive sweep (-093) — what held and what I withdraw

⚠ **The messages crossed.** I committed §1-§4 at 13:19:44 and p18's -093 is stamped 13:19:36; I had not seen it.
**I claim no priority** — what matters is that an independently derived bound and an independent measurement agree,
and that the parts of my §3 prediction that were wrong are visible because I wrote them down first.

**Held:**

| my statement | p4's measurement | |
|---|---|---|
| worst pair contacts at backplate gap **≥ 8.188 mm**, any admissible tilt | **10.16 mm** | ✅ bound holds |
| ordering: **claws contact first, no window** | claws contact 5.6 counts earlier; backplate still 2.16 mm short of the cable | ✅ |
| the **deeper pair is f1** (it protrudes more once the pad tilts) | `f1×f1` crosses zero at ctrl **219.16** < `f2×f2` **220.99** ⇒ f1 first | ✅ |
| pair separation = 24.8·sin θ ⇒ **0.679 mm** at θ = 1.57° | **0.68-0.70 mm**, near-constant across the range | ✅ |
| the cross pair `f1×f2` can never be the minimum (10.00 mm clear in z) | +9.8 … +10.0 mm, constant | ✅ |
| the offset depends on **orientation only**, so it is one scalar | separation near-constant across 205-240 ⇒ tilt near-constant | ✅ |

**Accuracy of the idealisation:** at p4's measured tilt my model puts contact at 10.548 mm against a measured
10.16 mm — **I over-predict by 0.39 mm**; at zero tilt I under-predict by 0.16 mm. ⇒ the idealised asset geometry is
good to about **0.4 mm** here. ⛔ Where we differ, **p4's build measurement is authoritative and mine is not.**

**⛔ Withdrawn — §3's magnitude claim.** I wrote that p4's earlier −2.57 mm "is one specific pair, not the minimum,
and the other pair is deeper," and my worked figures implied a pair separation of order 4 mm. **The measured
separation is 0.68 mm.** The direction was right (f1 is the deeper, first-contacting pair) but **the magnitude was
wrong**, because I sized it from the whole joint-limit tilt range while the achieved tilt is only 1.57°. I withdraw
the magnitude and the inference that −2.57 must have a much deeper partner; I keep the pair ordering, which held.

⭐ The split is not accidental: **every part of the prediction that did not depend on the tilt survived, and the one
part that did depend on it failed.** That is the same distinction that makes §2 a bound rather than an estimate —
and it is why the bound was not weakened by the tilt being unknown while my §3 sketch was.

**Reconciliation with p11's lever table** (so it is not later read as two banked numbers disagreeing): p11 has
`f1ext 51.72 / f2ext 39.32`; I have `45.220 / 32.820` from the follower pivot. The offset is **+6.500 mm on both
claws**, i.e. a different origin, and the **claw-to-claw spacing is 12.400 mm in both**. Since only the spacing
enters the pair separation (24.8 = 2 × 12.400), the two readings agree on the quantity that does the work. **Not a
contradiction.**

## 6. Scope

⛔ I do not rule on window-open / window-closed, on whether the clamp is reachable on real hardware, on capture vs
grip, or on any change to the locked geometry (§0#4 = Rs). ⛔ I ran nothing and hold no RUN authorization. What I
provide is one geometric bound from the banked LOCK asset, its falsifier, and a prediction that -092 D(2) will
settle. Gate unchanged; I do not self-start.
