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

## 9. -128 (8): my §2 contradicts pC's visual leg. ⛔ I downgrade §2 and name what could be wrong on my side.

pC places the R cable **inside the opening** at STEP 4 (t = 10.2 s); my §2 places it **at least 16.25 mm below the
containment band**. -128 (8) leaves this unresolved. Since §2 is mine, I examine my own side first.

### 9.1 The two claims are incompatible by a margin that excludes noise

The slot **[27.00, 37.00]** lies **entirely inside** `pad_box1`'s span [18.75, 37.50]. A cable centred anywhere in
the containment band spans at most **[27.00, 37.00]**, and `pad_box2`'s top is **18.75**.

> ⇒ **a cable in the slot misses `pad_box2` by at least 8.25 mm.**

⇒ ⭐ this is not a near-miss that measurement noise could bridge. **The disagreement has to be an alignment error or
an identity error — it cannot be a measurement error.** That narrows what to check.

### 9.2 ⛔ Where my side can be wrong — ranked, with the check for each

1. ⛔⛔ **Time alignment — my strongest candidate.** §2 rests on the contact-geom list cited in -123 (3) as "log
   `:65`". **I never established that that log line is the same instant as pC's t = 10.2 s.** If they are different
   moments, there is no contradiction at all and both observations stand. **Check:** read the timestamp on that log
   line. Cheap, no run.
2. ⚠ **Geom identity.** I mapped the runtime name `Rg_left_pad2` to the asset's `left_pad2` = the `pad_box2` class
   **by its name**. That is a name-based inference — the exact class of inference that failed elsewhere in this
   court today (§8.2, where "pad" matches the claws on purpose). **Check:** resolve the geom id to its asset class
   rather than to its name.
3. ⚠ **The relay itself.** ⛔ **I have not opened the log.** §2's input is pB's observation as relayed through p18,
   and -128 (1) is a live example of a correct account being overturned by an unverified relay. **I therefore
   downgrade §2 from established to conditional:** *if* the relayed geom list is correct and refers to pC's instant,
   then §2 follows; the geometry is sound but its input is not mine.

⭐ **What survives unconditionally** is the geometry, not the conclusion: **`pad_box2` sits entirely below the slot,
so contact on pad2 and presence in the slot cannot both be true of the same cable at the same moment.** That
statement holds whoever's data turns out to be right, and it is what makes the check worth doing.

⚠ **Frame check, since I raised the hazard myself:** pC's "below the blue plate, above the red plate" is world-frame
and describes the space between `f2ext` (blue/TOP) and `f1ext` (red/BOTTOM) — the same region as the pad-local slot
[27.00, 37.00], because `f1ext` carries the **larger** pad-local z despite being labelled BOTTOM (`:9`). ⇒ **the
frame inversion is not the source of the disagreement**; I checked before offering the contradiction.

### 9.3 What I take from -128 (8) about my own §2

⭐ pC established the world-frame attribution (close-up panel: screen-left = world L, screen-right = world R) and
withdrew the basis of its own earlier "both arms" reading. ⇒ **STEP 4 has world R inside the opening and world L
outside** — not both outside. My §2 spoke about "R" using an arm label I took from the relay and never verified
against pC's attribution. ⚠ **That is a fourth way my §2 could be misaligned, and it is the same kind as the other
three: every input to §2 came from someone else's reading, and only the geometry was mine.**

## 10. -131 (6): the label↔arm binding, resolved from source at the producing commit. No run.

-131 (6) puts the arm-label question in my court and asks for a **non-circular** resolution. I read the driver
**at the producing commit** rather than at HEAD:
`git show e9f93a7556:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/ur15_steps_reaim.py`

### 10.1 The name prefix and the position are bound in the same statement

```
:42    SIDES = {"L": -1.0, "R": +1.0}
:193   for tag, sign in SIDES.items():
:195       f = column.add_frame(pos=[sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT], quat=...)
:196       f.attach_body(_a.bodies[1], f"{tag}_", "")
```

⇒ ⭐⭐ **the name prefix and the frame position are set in the same loop iteration, from the same `sign`.** With
`YOKE_SPREAD = 0.40` (`:37`):

> **"L" is the arm at column-local x = −0.40. "R" is the arm at x = +0.40. They cannot be swapped** — there is no
> second place where the association could be re-made.

⚠ Note the separation is along the **column's local x**, **not** the production env's y = ∓0.35
(`task_config.py:21-22`). **This driver builds its own cell**, so the production base constants do not govern here.
⛔ Anyone carrying `ROBOT_LEFT_BASE`/`ROBOT_RIGHT_BASE` into a reading of this run is on the wrong cell.

And the arm selection inside the predicate uses that same prefix:

```
:230   PADG = {t: {g for g in range(m.ngeom)
:231           if (mj_id2name(m, mjOBJ_GEOM, g) or "").startswith(f"{t}g_")} for t in SIDES}
```

⇒ ⭐ **the arm identity carried by a geom name like `Rg_left_pad2` is sound by construction.**

### 10.2 ⭐ This breaks the circularity from the other end

-131 (6) notes pC's world attribution was derived from **the same log's STEP 8 values**, so pC's leg cannot
adjudicate itself. ⇒ ⭐ **the binding above is fixed at build time and depends on no log value at all**, which is
the independent anchor that was missing.

⇒ **what is now established:** the log's L/R **is** a reliable arm identity, and it is the arm at ∓0.40 in x.
⇒ **what remains open:** the mapping from **column-local x** to **which side of the screen** a viewer sees.

⚠ The close-up panel uses `cam2` with **`azimuth = 250`, fixed** (`:723`; only `cam.azimuth` varies, `:813`), and
`cam2.lookat` is the midpoint of the two pinch points (`:816`). ⇒ ⭐ **this confirms pC's methodological claim from
source**: the close-up panel has a stable attribution and the wide panel does not. ⛔ **But I will not convert
azimuth 250° into "screen-left is +x" from memory of MuJoCo's convention** — that is exactly the sort of unverified
convention claim that has cost this court all day. It needs the convention verified, or one rendered frame with the
two pinch points read off. **That is the last link and I leave it open.**

### 10.3 ⭐ The mix-up I suspected does NOT exist — checked before reporting

`clamp_faces(t)` computes `side = "L" if "_left_" in nm else ...`, and `Rg_left_pad2` **does** contain `_left_`.
That looks like an arm/pad confusion. **It is not.** The arm is selected by `a in PADG[t]` (`:364`), and the `L`/`R`
computed inside are **the two pads of that one gripper** — as the docstring says, *"split by side and role."*
⇒ ⛔ **there is no arm mix-up in that function, and I do not report one.**

### 10.4 ⛔ But the real defect is confirmed at the producing commit, by direct read rather than relay

```
:366   (claw if "ext" in nm else pad).add(side)
:371   def grasped(t):
:372       """Clamped = the cable is compressed between the two pad1 faces (bilateral)."""
:374       return {"L", "R"} <= pad
```

⇒ only `ext` is split out, so **`pad` accepts `pad1` OR `pad2`**, while the docstring says **pad1**. ⇒ ⭐ **that is
exactly how arm R reported clamped on `left_pad2` / `right_pad2` alone** — both *pads* of that gripper touched, on
the wrong *box*. ✅ -123 (3)'s account confirmed **from source**, not from a relay.

### 10.5 ⭐⭐ The positive-form set p11 asked for already exists in this file

```
:234   CLAWG = {t: [... f"{t}g_{s}_pad_{c}ext" ...]}
       # The four ko claws of each arm, by explicit name -- ... Named, not substring-matched,
       # so the set cannot silently pick up another geom.
:236   PAD1G = {t: [mj_name2id(m, mjOBJ_GEOM, f"{t}g_{s}_pad1") for s in ("left", "right")]}
```

⇒ ⭐⭐⭐ **the author already knew the substring hazard and built `CLAWG` and `PAD1G` by explicit name to defend
against it — and `clamp_faces` then uses the prefix-only `PADG`, which readmits `pad2`.** ⇒ the set -126 (3) asks
for **is already constructed, one line away from the predicate that needed it.**

### 10.6 What this does to my §9.2 doubts

- doubt **② geom identity** — ✅ **resolved**: `Rg_left_pad2` is arm R's `left_pad2`, i.e. the asset's `pad_box2`
  class. My z-map was right.
- doubt **③ the relay** — ✅ **largely resolved**: I have now read the driver source myself. ⚠ I still have **not**
  opened the log.
- doubt **① time alignment** — ⛔ **still live, and now the only one.** Whether the cited contact line is pC's
  instant remains unchecked, and it alone would dissolve the -128 (8) conflict.

## 11. -134 (5): read at the producing commit. The answer is a third option neither hypothesis named.

-134 (5) asks whether `slot vs cable` uses a **fixed link index** or the **nearest link at evaluation time**, and
says it can be settled by reading. I read it at `e9f93a7556`.

### 11.1 Neither. It is the link nearest a **fixed x**, re-selected every evaluation

```
:523  def cable_at(x):
:524      """Centre of the cable link nearest this x.  A link's body origin is the START of its capsule,
:525      so the material sits half a segment further along the link's own x axis -- targeting the origin
:526      misses by ~15 mm."""
:527      C = [d.xpos[b] + d.xmat[b] @ [CABLE_SEG/2, 0, 0]  for b in CAB]
:529      i = int(np.argmin(np.abs(C[:, 0] - x)))
:530      return C[i], i
...
:535  GL = (float(C1[0] - GRIP_HALF_SPAN), ...)          # frozen at setup
:842  cw, _ci = cable_at(GL[0] if t == "L" else GR[0])   # the x is the frozen one
:843  sc_err = (seat_point(t) - cw) * 1000.0
:845  print(... "slot vs cable, live" ...)
:849  print(... "cable moved {norm(cw - aim_cable[t])} mm since the aim")
```

⇒ ⭐⭐ **the x is fixed; the link is chosen fresh by `argmin` at every call; the position is live.** So:

- ⛔ **not** a fixed index — the selected link can change;
- ⛔ **not** the link in the jaw — nothing references the jaw;
- ⭐ **the link nearest a frozen x**, which is neither.

⇒ ⭐⭐⭐ **if the cable slides along x, `argmin` hops to a different link, and both prints change discontinuously —
reporting that "the cable moved" when what changed is *which link is being measured*.** That is a concrete
mechanism for -134 (5), and it applies to `cable moved since the aim` too, since `:849` reuses the same `cw`.

### 11.2 The magnitude is consistent with a single hop — ⛔ but that is not proof

Link spacing is **`CABLE_SEG = 0.030` = 30 mm** (`:47`). L's printed drift is **25.1 mm** — **less than one
spacing**. ⇒ ⭐ a single index hop is a **sufficient** explanation and consistent in magnitude. ⛔ It is not
established; a genuine 25 mm cable movement produces the same number.

### 11.3 ⭐⭐ The discriminator is computed and then discarded

`cable_at` **returns the index** (`:530`), and `:842` throws it away — `_ci`. And `aim_cable[t]` stores **only the
position** (`:749`, `:768`), never the index. ⇒ ⭐ **comparing the aim-time index with the grasp-time index would
separate "the cable moved" from "the measurement hopped" outright, and both indices exist at the moment they are
needed.**

⇒ ⚠ this is -123 (2)'s pattern **one step worse**: there, the discriminating quantity was computed and printed but
left out of the verdict. Here it is computed and **discarded**. ⛔ On the existing logs the comparison cannot be
made, because neither index was ever emitted.

### 11.4 ⭐⭐⭐ Two different "nearest cable link" quantities — and the second has the defect the first documents

```
:823  dists = [norm(d.xpos[b] - pw) for b in CAB]     # reference = the PINCH ; body ORIGINS
:824  j = int(np.argmin(dists))
:860  print(... "nearest cable link cab{j} at {dists[j]} mm from the pinch" ...)
```

against `:842`'s **fixed x** reference using **segment centres**. ⇒ the two differ in **both** the reference point
**and** whether the half-segment correction is applied.

⭐⭐ And `cable_at`'s own docstring states the size of that omission, verbatim: *"A link's body origin is the START
of its capsule, so the material sits half a segment further along the link's own x axis — **targeting the origin
misses by ~15 mm**."* Half a segment is **15.0 mm**, exactly.

⇒ ⭐⭐⭐ **the correction was written, its magnitude was documented, and it was applied in one of the two places.**
The pinch-referenced number at `:860` — the one a reader uses to judge "was the cable near the jaw" — carries the
~15 mm bias its neighbour's docstring warns about.

⚠ **Scope.** I read source at `e9f93a7556` only. ⛔ I have not opened the log and have run nothing, so **whether a
hop actually occurred is not established** — I supply the mechanism and the two checks, not a verdict. Aiming
choices (p4's question ①) are p5's court.

## 12. -135: the frame p11 flagged as unmeasured **is** measured, and the hop has a threshold

### 12.1 ⭐⭐ The frame is banked. p11's refutation stands on measured ground.

p11 dropped its own "the slot moves up" hypothesis because R's cable was **above** the slot, and flagged that the
direction rested on *"p4 の相対値を p11 が world 上と読んだもので、フレームは未実測"*. **It is measured** —
`thread_isaac_lab/thread-vault/06-Knowledge/GD-KoShape-Finger.md:58-59`, which I read:

> *"At the grasp pose: **f1ext Z≈796.6 (BELOW cable)**, **f2ext Z≈809 (ABOVE cable)**, cable Z≈800-808 between
> them."*

against the asset's pad-local z: **f1ext 38.20 > f2ext 25.80**.

⇒ ⭐⭐ **larger pad-local z ⇔ lower in world** ⇒ **pad-local +z points DOWN in world at the grasp pose.** ⇒ p11's
reading is **supported by a banked measurement**, so the refutation does not rest on an assumed frame.
⚠ Scope: *"at the grasp pose"* — the mapping follows the hand's orientation and is not universal.

### 12.2 ⚠ A citation that does not resolve at the pinned commit

-135 (1) cites `ur15_steps.py:548-555` as `cable_at` and `:878` as the call site. At **`e9f93a7556`** I read
`:548-555` as the **camera block** (`cam`/`cam2` construction). In that file at that commit:

| | line |
|---|---|
| `def cable_at(x)` | **:370** |
| `GL` / `GR` frozen | **:382-383**, and **re-frozen at :509-510** |
| call sites `cable_at(GL[0])` / `(GR[0])` | **:570-571** |

⇒ ⛔ either a different commit of that file was read, or the line numbers are stale. **I do not adjudicate** — I
report what resolves at the commit that was pinned. ⚠ Note also that `ur15_steps.py` has **two** freeze points, so
"frozen at STEP 1 and never updated" needs care in that file.

### 12.3 ⭐ The mechanism is in **both** drivers

`ur15_steps_reaim.py` — `cable_at` `:523`, `GL` `:535`, call `:842`.
`ur15_steps.py` — `cable_at` `:370`, `GL`/`GR` `:382-383` and `:509-510`, calls `:570-571`.

⇒ ⭐ **fixing one leaves the other.** Same shape as §8.2's second site.

### 12.4 ⭐⭐ The hop has a threshold, so -135 (3)'s state-dependence becomes a number

The selection is `argmin |C[:,0] − x|` over link centres spaced `CABLE_SEG = 30 mm` apart. ⇒ **the selected link
changes only when the cable slides in x by more than half a spacing — 15.0 mm.**

| arm | evidence | against the 15.0 mm threshold |
|---|---|---|
| **R** | instrument 17.4 vs my contact-based ≤14.75 — agree to **0.15 mm** | ⭐ consistent with **no hop** |
| **L** | printed drift **25.1 mm** | ⚠ **above the threshold — a hop is admissible** |

⇒ ⭐ this is the quantitative form of p11's "state-dependent": the condition is not "something in the jaw" but
**"an x-slide past 15.0 mm"**, and the two arms fall on opposite sides of it. ⛔ It stays undecidable for L without
the index, per §11.3 — real motion and a hop produce numbers of the same size, which is precisely why the discarded
index mattered.

## 13. -137 (4): what the repair reaches, and what it does not

I named the defect, so I checked the fix against it, at `887d3fefde`. **The content sha reproduces**:
`770b2271b6cea1392684eb264098bf9ec9ba9d78e7a18102f07546e5f4e408f1` ✅ (my own `sha256sum` of `git show`).

### 13.1 ✅ The reporting path is fixed, exactly as claimed

```
:886   _ci = int(np.argmin(np.linalg.norm(_cc - sp, axis=1)))     # reference = the SEAT point, 3-D norm
:887   cw  = _cc[_ci]
:890   print(... f"seat vs NEAREST cable link cab{_ci}, live" ...)
:895   print(... "nearest link is N mm from where the aimed link was (identity may differ -- not a drift)")
```

⇒ ✅ the frozen x is gone from this path — selection is now against the **seat point**, in a full 3-D norm.
⇒ ✅ **the index that was computed and discarded is now printed**, which is the check §11.3 said was missing.
⇒ ✅ the drift line no longer asserts movement it cannot establish.

### 13.2 ⚠ Two related sites are not reached

**(a) The aiming path still selects by the frozen x.**

```
:767   if num in (2, 3, 4, 5):   # grasp steps: aim at where the cable IS, right now
:768       cl, _ = cable_at(GL[0])
:769       cr, _ = cable_at(GR[0])
...        aim_cable[t] = np.asarray(c, dtype=float)      # position only; still no index
```

⇒ ⭐ **the report now tracks the seat point while the aim still tracks a frozen x.** The same hop therefore
survives on the **control** path rather than the reporting one: past 15.0 mm of x-slide (§12.4) the arm aims at a
different link than it did before. ⚠ And because `aim_cable` stores only the position, the new
*"nearest link is N mm from where the aimed link was"* compares a **seat-selected** link against a
**frozen-x-selected** one — two different selection rules. ⭐ The added caveat *"identity may differ -- not a
drift"* is honest about the consequence; the two-rule mismatch underneath is still there.

**(b) The pinch-referenced print still uses body origins.**

```
:859   dists = [float(np.linalg.norm(np.array(d.xpos[b]) - pw)) for b in CAB]
:860   j = int(np.argmin(dists))
```

⇒ ⚠ **no half-segment correction**, so the ~15.0 mm bias that `cable_at`'s own docstring documents is still on that
number. ⭐ -137 (3) already instructs that this value not be used, so the practical risk is handled by the
instruction — but the code still emits it, and an instruction is not a guard.

### 13.3 Verdict on the repair, stated narrowly

⭐ **It does what -137 (4) claims: the reporting reference is repaired and the index is visible.** ⛔ It is **not** a
general fix of the mechanism — the frozen-x selection remains on the aiming path, and the uncorrected origin
remains on the pinch print. ⇒ "the instrument is repaired" is true of the **reported slot quantity** and should not
be widened past that.

⚠ Scope: source read only, at `887d3fefde`. I ran nothing, and I am not the designated verifier; this is material
about a defect I raised, not a verification verdict. ⛔ I propose no change.

## 14. Scope

⛔ No run, no new measurement of the model, no verdict. The contact-geom names are **pB's** observation, relayed via
-123; everything I add is asset geometry and arithmetic on top of it. If pB's geom list is revised, §2 and §4 move
with it. Gate unchanged; I do not self-start.
