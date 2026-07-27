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

## 6. The last 0.4 mm: it is box-edge migration, and it closes to 0.01 mm

-097 A establishes the measured relation **claw gap = backplate gap − 10.11**, and reports pZ's static 10.00 as
confirmed within 0.11 mm. My §5 left a **0.39 mm** residual against my own tilt-corrected figure (10.548 at the
measured 1.57°), and that residual was pointing the wrong way — my model was *further* from the measurement than
the zero-tilt value was. Two measured quantities implied two different tilts:

- the measured **pair separation** 0.68 mm ⇒ θ = 0.68/24.8 = **1.571°**
- the measured **absolute offset** 10.11 mm ⇒ θ ≈ **0.31°** on face-centre geometry

⇒ a factor of five apart. Something structural was missing, and w2:p11 had already named it: *the backplate is a
box, so the closest point migrates.*

**Quantified from the asset dimensions.** `mj_geomDistance` returns the minimum distance between two **boxes**.
Once the pad tilts, the closest point leaves the face centre and moves to the **leading edge**, and the two boxes
have very different heights — backplate `pad_box1` half-height **9.375 mm** (`:59`), claw half-height **1.200 mm**
(`:116`/`:117`). The differential advance is therefore **(9.375 − 1.200)·sin θ = 8.175·sin θ per side**.

| per side [mm] | face-centre | edge term | min-distance offset |
|---|---|---|---|
| `f1ext` | 5.2743 | −0.2241 | **5.0502** |
| `f2ext` | 4.9344 | −0.2241 | **4.7103** |

| | predicted (asset only) | measured (p4 sweep) | residual |
|---|---|---|---|
| pair separation | **0.680 mm** | 0.68 - 0.70 mm | ✅ |
| deeper pair | **f1** | `f1×f1` crosses first | ✅ |

For the absolute offset I pin **my** number and give the spread, because the measured figure has itself moved across
messages and pinning to one value of it would be the mistake this project has been correcting all day:

| measured value in circulation | source | residual vs my 10.100 | residual without the edge term (10.549) |
|---|---|---|---|
| 10.11 mm | -097 A | **−0.010 mm** | +0.439 mm |
| 10.16 mm | -093 B, -097 A upper | **−0.060 mm** | +0.389 mm |
| 10.20 mm | -098 A upper | **−0.100 mm** | +0.349 mm |

⇒ ⭐ **the finite box heights account for 0.448 mm, which is the right size against every circulating value, and the
residual after it is ≤ 0.10 mm in the worst pairing.** ⛔ I do **not** claim the 0.010 mm agreement — that is one
pairing out of three, and I have no basis for choosing it. The edge term is **common to both claws**, so it cancels
in their difference: the separation stays 0.680 mm and the tilt derived from it was never contaminated. That is why
the separation and the absolute offset disagreed about θ — only one of the two was affected.

⚠ **What is fitted and what is not.** The tilt (1.571°) is **not mine** — it is p4's measured separation through
pZ's relation. The only thing I chose is the **sign** of the tilt, so that the edge term subtracts. Given that one
binary choice, **two independent quantities come out right** (absolute offset to 0.01 mm, separation to 0.00 mm)
plus the pair ordering. Still idealised: rigid boxes, symmetric tilt, min distance taken at the leading edge.

**Consequence for -097 C③ ("carry 10.11 forward as the constant").** Strictly it is not a constant — it is the
function evaluated at the tilt that happened to hold. Its sensitivity is
**d/dθ = 2·(10.075 − 8.175) = 3.80 mm/rad = 0.066 mm per degree of pad tilt.** ⇒ ⭐ carrying **10.11** forward is
safe to about **0.07 mm per degree** of tilt variation, which over any plausible variation is far below the 2.16 mm
clearance the ordering question turns on. ⇒ **the ordering conclusion is insensitive to this; a future claim at
0.1 mm resolution would not be.**

⇒ this also sharpens §2: the bound is unchanged (the edge term only ever *reduces* the offset by at most
8.175·sin θ, and at the joint-limit corner the bound was already computed on face-centre geometry, so **the bound
should be re-derived with the edge term before being relied on at the corner**). ⚠ I flag that rather than silently
keeping the corner figure: **+0.188 mm at −67° is a face-centre number and the edge term is ±7.5 mm at that
angle**, so the corner margin is not established. The working-range conclusion (near-parallel pads, margin ≈2 mm,
measured 2.16 mm) is unaffected.

## 7. p4's saturation finding (-101 B): the exact cap, and what it does and does not touch

p4 found that the claw-distance reading **saturates** near −2.5 mm, which kills the "the jaw stopped on the cable"
explanation (the sweep was cable-free) and with it the reconciliation everyone including me had built around it.
The asset gives the **exact cap**:

| claw box (`:116`/`:117`) | full extent |
|---|---|
| x | 22.00 mm |
| y (the closing direction) | 18.00 mm |
| **z** | **2.400 mm** |

Two same-index claws meet face-to-face along y at equal z (the mirror is 180° about z, `:128`/`:142`). Their
overlap region is therefore 22.0 × y(growing) × **2.40** mm, and a minimum-translation penetration depth is the
**smallest** of those. ⇒ **the depth cannot exceed 2.400 mm however far the jaw closes.**

⇒ ⭐ p4's plateau ≈ −2.5 mm **is the claw's own thickness**. The old datum −2.57 sits **0.17 mm past the cap**;
I do not have an explanation for that excess and do not paper over it.

**Untouched by saturation** — because saturation distorts values only *after* contact, never the crossing itself:

- ✅ **my §2 bound**, which is entirely a statement about where the distance reaches **zero**;
- ✅ the **deeper-pair identification** (crossings at ctrl 219.16 / 220.99, both before the plateau);
- ✅ the **pair separation** used to derive the 1.571° tilt (measured at those crossings, pre-saturation);
- ✅ **§6**, which used the offset at ctrl 219-225 — p4's own valid window.

⚠ **Affected, and this is new for pZ's court.** Any claw reading below about −2.4 mm **carries no depth
information** — it is the instrument's floor, not the geometry. ⇒ the alternative instrument floated in -093 D,
*"the actual gap at verdict time"*, **cannot serve as a graded measure once the claws interpenetrate**, which is
the regime CLAMP-1 is being asked about. A graded predicate there needs a different quantity (e.g. the commanded
closure, or the backplate gap, both of which stay informative).

⚠ **-101 D noted, and I keep the two margins apart.** The measured operating point gives **2.16 mm** of clearance;
my worst-case-over-all-tilts figure gives **0.188 mm**. The second is the one that matters for transfer — and it is
**not established**, by my own §6 caveat (it was computed on face-centre geometry, where the edge term reaches
several mm at that angle). I will not let it be quoted as though it were.

## 8. ⛔ I correct my own 2.400 mm cap — and with it the one OPEN item it created

**Cause side is me.** In §7 I wrote *"the cap is exactly 2.400 mm"* and reported that the old datum −2.57 sat
**0.170 mm past it** with no explanation. That excess became the single OPEN item p18 is holding (-102 (4)). It was
**my error, and it is the same error class as §6**: I computed the cap on **parallel** boxes while the pads are
demonstrably tilted.

The minimum-translation depth is capped by the overlap along the thin axis, and once the two claw boxes are
mutually rotated by an angle *a*, that overlap is **h_z + (h_y·|sin a| + h_z·|cos a|)** — the tall 18.0 mm y-extent
starts contributing as soon as *a* ≠ 0:

| mutual angle of the two claw boxes | cap on the reported depth | old datum −2.57 |
|---|---|---|
| 0° — parallel (what my 2.400 assumed) | **2.4000 mm** | exceeds by 0.170 |
| θ = 1.571° (the measured per-pad tilt) | **2.6463 mm** | **within by 0.076** |
| 2θ = 3.142° | **2.8915 mm** | **within by 0.321** |

⇒ ⭐ **under either tilted convention the old −2.57 sits inside the cap, so it is not anomalous.** The excess was an
artefact of my parallel-box assumption.

⭐ **This also identifies pZ's convention.** pZ reported a floor of **−2.647 mm** at the measured tilt and declined
to claim it fit. My cap at mutual angle θ is **2.6463 mm** — the two agree to **0.0007 mm**, which says pZ used
mutual angle = θ. ⚠ I cannot settle from geometry alone whether the mutual angle is θ or 2θ (it turns on how the
180° z-mirror composes with the two pads' tilt senses), and I do not need to: **both resolve the excess**.

⛔ **I do not mark the OPEN item resolved** — -102 (4) says not to, and the disposition is p18's and pZ's. What I
supply is the retraction of the number that created it. ⚠ Note also that pZ was correct twice over here: pZ
computed the tilted floor rather than the parallel one, **and** declined to assert the fit. I asserted an exact cap
that was not exact.

**Axis disambiguation for -102 (3).** Two ~10 mm quantities appear in this document on **orthogonal axes**. Every
occurrence is labelled in place, but so that no figure can be lifted out of a table without its axis:

- **10.00 mm — the コ opening's clear gap. Axis = pad-local z.** Between `f1ext` (z 37.00) and `f2ext` (z 27.00).
  Used in §3 and §5 to exclude the cross pair. **This one is measured and valid.**
- **10.00 / 10.100 / 10.11-10.20 mm — the backplate gap at which the claws touch. Axis = the jaw's closing
  direction (pad-local y).** Used in §2, §5, §6. **This one is a function of tilt, not a constant.**

⛔ They are never the same number and must not share a column.

## 9. -110: the convention settled from the asset, the instrument contract checked, and my formula split again

### 9.1 (2)(a) — the mutual angle is **2θ**, and the asset alone settles it

-110 (2)(a) puts the θ-vs-2θ convention in p4's and my court. It is decidable **read-only**:

- `left_driver` (`:128`) and `left_spring_link` (`:142`) carry `quat="0 0 0 1"` = **180° about z**;
- every joint has `axis="1 0 0"` = **local x** (`:39`);
- ⇒ after that 180°, the left chain's local x points along **world −x**, so equal joint angles — and the equality at
  `:200` couples the two drivers **1:1** (`polycoef="0 1 0 0 0"`) — produce **opposite** rotations about world x;
- ⇒ the two pads' **relative** rotation is **2θ**;
- ⇒ and a box is **invariant** under a 180° rotation about its own z, so the mirror itself contributes **nothing**
  to the box-to-box relative orientation.

⇒ ⭐ **mutual angle = 2θ = 3.142°, cap = 2.8915 mm.** ⚠ This assumes the two *followers* reach equal angles; the
drivers are coupled but the followers are passive, so asymmetric contact could break it.

⚠ Consequence for the record: pZ's floor −2.647 corresponds to mutual **θ** and p11's 2.891 to mutual **2θ**.
⇒ **my derivation supports p11's number.**

⛔ **Correction to my own first wording here (cause side is me).** I originally wrote that "p11's label was the
slip." **That is wrong and I withdraw it.** Per -114 (8), p11 used 1.571° as the **per-plate** angle and doubled it
inside the formula, so **p11's convention was correct throughout**. What failed in p11's expression was using a
**constant (the half-width)** in the tilt arm — the same family-I defect as mine — not the angle. I attributed a
mistake that did not happen, in the course of agreeing with p11's number.

### 9.2 (2)(b) — the instrument contract is genuinely undocumented, but it carries its own witness

I checked the installed MuJoCo rather than assuming. **The only documentation that exists locally is one sentence**,
identical in the C header and in the bindings:

> `mujoco.h:628` — *"Return smallest signed distance between two geoms and optionally segment from geom1 to geom2."*

(the same string is the `doc=` field of the `mj_geomDistance` `FunctionDecl` in `mujoco/introspect/functions.py`,
and the Python `__doc__`.) ⇒ ⛔ **nothing states what "smallest signed distance" means once the geoms
interpenetrate.** -110 (2)(b) is confirmed: all four floor formulas rest on an undocumented reading.

⭐ **But the function returns `fromto` — a 6-vector holding the segment from geom1 to geom2.** That segment is the
**witness of what the number measured**: at a penetrating configuration its two endpoints say directly whether the
returned value is a thin-axis minimum translation or something else. ⇒ **the contract is observable, not merely
assumable**, and it needs **no new run** if the sweep already captured `fromto` (it is the optional 6th argument).
⇒ offered to p4's court; I am not requesting a run.

### 9.3 (3) — my formula survives as a bound and fails as an explanation. Third time today.

-110 (3) separates two families and lets p5's data discriminate. Mine is in family I (tilt term ∝ the constant
half-width), so **my floor is constant in closure**. p5's measured floor **rises**: ctrl 227 → 2.47, 229 → 2.49,
235 → 2.56, 239 → 2.61.

| | verdict |
|---|---|
| as an **explanation** of the trend | ⛔ **refuted** — a constant cannot produce a monotone rise |
| as a **bound** | ✅ **intact** — all four measured values sit below both my caps (2.6463 / 2.8915) |

⇒ I withdraw the explanatory reading of §7-§8 and keep the bound. p5's family fits with **zero free parameters** and
reproduces the old datum at ctrl 235 to **0.01 mm**; mine does not compete with that and should not be quoted as if
it did.

⭐ **This is the third time today the same split has appeared in my own work**: §2's bound held while §3's magnitude
failed; §6's tilt-free part held while the fitted part failed; now §7's mechanism holds as a bound while its shape
fails. **The tilt-free / bound-shaped parts survive; the parts that carry a fitted or assumed parameter do not.**

⛔⛔ **VOID — and the defective inference is mine, not the pane that relayed it.** I wrote here that "if the floor
rises past 2.6463 at any higher ctrl, mutual-θ is refuted and only 2θ survives," and offered it as a free second
route to 9.1. **It is not a test.** p5 measured past the half-width and found **no ceiling at all** (overlap 8.00 →
2.617, 9.00 → 2.645, 10.00 → 2.672, 12.00 → 2.727, 14.00 → 2.782, 16.00 → 2.837): under the **θ** convention the
floor **exceeds 2.6463 at about 9.05 mm of overlap by prediction**. ⇒ the exceedance is what θ *predicts*, so it
cannot refute θ. No length of sweep rescues it.

⚠ p18 has taken cause side for publishing it as an open route. **I decline that division: the inference was mine.**
And the diagnosis is sharper than "a bad test":

⭐ **I built the discriminator out of the number of a model I had just refuted — in the adjacent section of this
same file.** §9.3's own table says family I is "⛔ refuted" as an explanation of the trend. A refuted model's value
cannot discriminate anything; its number is not a threshold, it is an artefact. This is the exact error the court
had already named in -092 C (*"both arithmetics come from the same refuted model"*), and I committed it **while
writing the refutation on the page above**. Having the refutation in hand was not enough; I did not ask the one
question that would have caught it — **can this test come out the other way?**

### 9.4 -110 (1) — agreed, and my artifact already says it that way

The OPEN closed **by withdrawal, not by explanation**: §8 states that nobody explained the 0.17 mm and that the
quantity it was an excess *from* was mine and wrong. ⛔ It must not be recorded as "explained by tilt."

## 10. -114: what p5's probe did to my numbers, and which results the env update can and cannot touch

### 10.1 My 2.400 was exact — for the quantity it actually described

p5's synthetic-box probe returns **−2.400 for every overlap ≥ 3.0 mm** with parallel boxes, and the `fromto` segment
switches from y to z **exactly at the thickness**. ⇒ ⭐ **2.400 is confirmed to the digit as the zero-relative-tilt
floor.** My §8 retraction was correctly calibrated and I do not widen it: the *number* was right, and what was
wrong was **applying it as the cap for tilted pads**. It is not "my wrong number"; it is the right number for a
configuration the pads are not in.

### 10.2 My family-I cap: a valid bound, and a loose one

Against the probe at θ = 1.571°/plate: measured **−2.478 / −2.499 / −2.561 / −2.601**, family-II predicts those to
**0.002 mm**, and my family-I figure is **2.893** — over by **0.29-0.33 mm**.

⇒ ⛔ **never attained**, so it carries no explanatory weight.

⚠ **And it is a bound only inside the band that was measured** (-116 (5), reproduced here): p5's series past the
half-width rises at **0.0275 mm of floor per mm of overlap**, so **2.6463 is exceeded at ≈9.07 mm of overlap and
2.8915 at ≈17.98 mm**. ⇒ ⛔ **neither is a bound in general.** Quoted without the band, "still a bound" becomes a
false claim, so I attach the band to it here rather than leaving the qualifier in a neighbouring message.

⚠ **Two different things in this file are called a bound. They must not be conflated:**

- **the contact bound (§2)** — on the **backplate gap at which the claws first touch** (≥ 8.188 mm). Geometric,
  **contract-free**, and unaffected by everything in this section, because at first contact there is no penetration.
- **the floor bound (§7-§10)** — on the **reported penetration depth** (2.6463 / 2.8915). Contract-dependent,
  never attained, and **band-limited** as above.

⇒ -116 (5)'s scope limit applies to the **second** only. It does not reach §2.

### 10.3 The convention: two independent routes agreed

-114 (3) records that my asset-kinematics derivation (2θ, §9.1) and p5's probe parametrisation (A at −θ, B at +θ ⇒
relative 2θ) reached the same convention by different means, and that **p4's 1.571° is per-plate**. ⇒ 9.1 stands as
independently corroborated rather than as my reading alone.

### 10.4 ⛔ The env update — which results need re-verification and which do not

-114 (6) surfaces that the queued env7 update (mujoco 3.8.1 → 3.10.0) **replaces the very library whose contract was
just measured**. Sorting my own results by whether they depend on that contract:

| result | depends on the penetration contract? | after the update |
|---|---|---|
| **§2 bound** — where the claw distance reaches **zero** | ⛔ **no.** At zero there is no penetration, so the SAT-vs-anything question does not arise | ✅ **survives by construction** |
| §5 confirmations — zero crossings, deeper pair, pair separation | ⛔ no — all read at or before first contact | ✅ survives |
| §6 offset reconciliation — ctrl 219-225 | ⛔ no — pre-saturation window | ✅ survives |
| §7-§9 floor / cap work | ⭐ **yes, entirely** | ⚠ **must be re-measured** |

⇒ ⭐ **the ordering conclusion (claws first, no window) is the part that does not rest on the contract**, so the
update does not put it back in question. Everything about the floor does.

⭐ **Proposal only — I implement nothing and request no run.** p5's probe is **synthetic boxes with no THREAD asset,
no harness, no GPU and no gate**. ⇒ it is the **only measurement in this whole chain that can be repeated
identically on both sides of the update**. If it is kept as a script with its numbers banked, the update becomes
**verifiable** rather than a leap: run it on 3.8.1 and on 3.10.0 and diff the contract.

⭐⭐ **Already done — and my "the opportunity exists only before the update" was wrong about the timing** (-116 (1)):
p5 did not wait for the update. It ran the same probe against staging (`env_isaaclab7_latest`, **mujoco 3.10.0**)
and **all 15 points are identical to 3.8.1** — overlap 5.93 → −2.561 on both, parallel ≥3.00 → −2.400 on both.
⇒ ⭐ **the env7 update is neutral with respect to this instrument's contract.**

⇒ ⭐ and the wider point is not mine but worth carrying: the bucket I labelled *"dies with the version by
definition"* **did not die in fact**. A definitional argument said it must be re-measured; the measurement said it
did not change. That is the whole case for measuring rather than reasoning about it.

⚠ Scope of that neutrality, kept attached: what was tested is **`mj_geomDistance`'s box-box penetration convention
only**. Solver behaviour, contact, and run reproducibility are **separate axes and untested** — a post-update smoke
is still required for those.

⚠ I also keep -114 (5)'s limits attached rather than dropping them: the probe is **synthetic boxes, not the real
pads** (which also carry `pad1`/`pad2`, and whose tilt comes from the 4-bar); **p4's 1.571° is not itself
probe-verified**; and the probe ran on **mujoco 3.8.1 default flags only** (`nativeccd` and friends untested).

## 11. Scope

⛔ I do not rule on window-open / window-closed, on whether the clamp is reachable on real hardware, on capture vs
grip, or on any change to the locked geometry (§0#4 = Rs). ⛔ I ran nothing and hold no RUN authorization. What I
provide is one geometric bound from the banked LOCK asset, its falsifier, and a prediction that -092 D(2) will
settle. Gate unchanged; I do not self-start.
