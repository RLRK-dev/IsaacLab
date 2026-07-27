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

## 14. ⛔ -138 (3)/(4): the comparand is 2.00 mm, not 10.00 mm — flagged before the run is authorised

-138 (3) reasons that if the slot moves **13.4 mm** between open and closed and the slot is **10.00 mm** high, the
open-pose and closed-pose bands do not overlap. ⇒ ⛔ **the 10.00 mm is the wrong quantity to compare against.**

What must overlap is not the slot with itself, but the **cable-centre band** with itself:

| predicate on the cable | admissible centre positions | width | bands overlap iff |
|---|---|---|---|
| **fully inside the slot** = **not struck by a claw** | **[31.00, 33.00]** | **2.00 mm** | **Δ < 2.00 mm** |
| merely overlapping the slot span | [23.00, 41.00] | 18.00 mm | Δ < 18.00 mm |

⭐ The two rows of the first line are the **same band** because **the claws bound the slot**: escaping f2ext needs
centre ≥ 31.00 and escaping f1ext needs centre ≤ 33.00. ⇒ **p5's requirement — the cable inside for the whole
closing motion — is exactly that 2.00 mm band.**

### 14.1 The conclusion holds, and by far more than stated

| Δ = 13.4 mm against | verdict |
|---|---|
| the **2.00 mm** band | ⛔ **impossible — short by 11.4 mm, i.e. 6.7× the band** |
| p18's 10.00 mm | would read as short by only 3.4 mm — **understates it by 8 mm** |
| the 18.00 mm span | ⭐ **possible — 4.6 mm of room left** |

⇒ ⭐⭐ **so the design does not automatically invert.** It inverts **only if** the requirement is full containment
throughout. Under the weaker requirement — the cable never leaves the claws' span, contact permitted — a window
still exists, 4.6 mm wide. **Which requirement applies is p5's and p11's call; the arithmetic is not.**

### 14.2 ⛔⛔ The proposed falsifier would return the wrong answer

-138 (4) proposes: fix the arm, close the fingers, measure the slot-centre displacement — *"10.00 mm 未満なら重なる
帯が在り、狙い点 1 点で足りる"*. ⇒ ⛔ **with a 10.00 mm threshold that test answers "the bands overlap" for every Δ
between 2.00 and 10.00, where they do not.** ⭐ **It cannot come out right across an 8 mm span of the very
quantity it measures.**

⇒ ⭐ **the threshold must be 2.00 mm** (or 18.00 mm if the weaker predicate is chosen). The measurement itself is
the right measurement — only the number it is compared against is wrong. **I raise this before the run is
authorised, not after.**

⚠ Everything here is conditional on Δ = 13.4 mm being real and directed along the slot's z. p11 flagged the
direction as unmeasured; §12.1 grounds the **frame** from the vault but **not the displacement**. ⛔ I do not
propose a value, a predicate, or a run.

## 15. -139: the window arithmetic, the axis p5 asked for, and a direct answer on the aim path

### 15.1 ✅ The window checks out, and the in-window displacement is bounded well under the band

| | value | source |
|---|---|---|
| claw tip reaches the cable's y extent at backplate gap | 2 × (4.00 + **5.000**) = **18.00 mm** | my protrusion (§1 of the bound artifact) + `CABLE_RADIUS` `:137` |
| constraint window | backplate gap **[10.16, 18.00]** → **7.84 mm** | ✅ reproduces p11/p18 |
| in ctrl, at 2.675 counts/mm from the crossing 219.16 | **ctrl [198.19, 219.16]** | ✅ reproduces p18's "≈198" |

Against p4's mouth-centre series (relayed): 146.00@18 / 153.17@100 / 156.81@180 / 157.28@214 / 157.23@236. The
window touches **two** sample intervals, not one — `[180,214]` (+0.47) and `[214,236]` (−0.05):

> ⇒ **in-window displacement ≤ 0.52 mm**, bounding by the total variation of the intervals it touches
> ⇒ **3.8× of headroom against the 2.00 mm band** ⇒ ⭐ **supports -139 (3): the bands very likely overlap and the
> design does not invert.**

⚠ Three caveats I keep attached: the series is **relayed** and I have not read it at source; the bound assumes the
motion does not reverse **inside** a sample interval; and the values are **base +z**, not the component §15.2 says
is the deciding one. ⛔ It is a bound from coarse samples, not a measurement of the window.

### 15.2 ⭐⭐ The axis p5 asks for **is the pad's local z** — and it is identifiable from the asset

-139 (4) asks that the displacement be resolved onto the mouth's height axis rather than reported as a base-frame
magnitude. **That axis is exactly the pad's local z**, because `f1ext` and `f2ext` differ in **nothing else**:

| geom | pad-local pos |
|---|---|
| `f1ext` | (0, −0.0026, **0.0382**) |
| `f2ext` | (0, −0.0026, **0.0258**) |

⇒ same x, same y ⇒ **the line joining them is the pad-local ẑ**, exactly. ⇒ the decomposition is *"project onto the
pad body's local z"*, readable from that body's `xmat` — no new geometry needed, and no ambiguity about which axis
is meant. ⭐ Its **world** direction is already grounded in §12.1 (**down** at the grasp pose,
`GD-KoShape-Finger.md:58-59`), so the sign is not free either.

### 15.3 ⛔⛔ -139 (8): the aim path has **not** moved. I read the newest commit.

`git log` on the driver gives three commits — `e9f93a7556` → `7869a01b82` → **`887d3fefde` (newest)**. At the
newest:

```
:767   if num in (2, 3, 4, 5):   # grasp steps: aim at where the cable IS, right now
:768       cl, _ = cable_at(GL[0])        <- STILL the frozen x
:769       cr, _ = cable_at(GR[0])
...
:883       sp  = seat_point(t)            <- only the REPORTING path moved
:886       _ci = argmin(norm(_cc - sp))
```

⇒ ⭐⭐ **p18's caution in (8) is correct and now confirmed at HEAD of that file: the improved residuals
(L 0.09 / R 0.16 mm, from 1.0 / 0.4) measure convergence onto the link the frozen x selected.** They do not
establish that the right link was aimed at — **the target-selection rule did not change; only the convergence onto
it got tighter.**

⇒ ⚠ and that is worth saying plainly because a **10× improvement reads as success**: a smaller residual against a
possibly-wrong target is **tighter convergence, not better targeting**. The two are distinguishable only by the
selection rule, which is unchanged.

## 16. -140 (4): the closed query, and the same blindness in the production env

### 16.1 ⭐⭐⭐ (4)(b) settled — five duplicated builders, not references

-140 (4)(b) records the cylinder definitions in five files and says explicitly it was **not checked** whether they
are duplicated builders or references. Closed query at `e9f93a7556`:

| file | own `stem`/`foot` definitions | imports `ur15_cell` |
|---|---|---|
| `ur15_cell.py` | **2** | 0 |
| `ur15_route.py` | **2** | 0 |
| `ur15_steps.py` | **2** | 0 |
| `ur15_steps_reaim.py` | **2** | 0 |
| `ur15_yoke_video.py` | **2** | 0 |

⇒ ⭐⭐⭐ **every file defines the cylinders itself and none imports the cell builder.** ⇒ **repairing
`ur15_cell.py` alone repairs none of the other four.** p18's suspicion is confirmed and is stronger than
suspected — not "might be duplicated" but "duplicated, with zero imports".

### 16.2 ✅ (4)(a) confirmed

`ur15_cell.py:112` — `<geom name="floor" type="plane" ... contype="0" conaffinity="0"/>` ⇒ collision disabled.
`:118` — `table_top` carries **no** such flags ⇒ it collides. ✅ matches -140.

### 16.3 ⭐⭐⭐ The same blindness exists in the **production** env, by design

`thread_isaac_lab/envs/newton_skill_env_base.py:1574-1583`, verbatim comment and code:

> *"A-1 VISIBLE-only pass (probe-proven, F4c): clear COLLIDE on non-pad arm shapes (→ MuJoCo
> contype=conaffinity=0); KEEP COLLIDE on the gripper PAD geoms (cable grasp)."*

```
for si in range(mj_left_ss, mj_arm_se):
    lbl = str(_labels[si]) if si < len(_labels) else ""
    if "pad" not in lbl.lower():
        proto.shape_flags[si] = int(newton.ShapeFlags.VISIBLE)
```

⇒ ⭐⭐ **every arm shape whose label lacks "pad" has collision cleared, and the comment states the equivalence to
`contype=conaffinity=0` itself.** ⇒ **arm-versus-anything interpenetration produces no contact in the production
env either.**

⇒ ⭐⭐⭐ **so -140 (1)'s conclusion is not confined to p4's driver**: any contact-based check for arm/structure
interference is blind in the production path too, and there by deliberate design rather than by an overlooked flag.
⛔ I am **not** saying the design is wrong — it was taken for a stated reason. I am saying **the detector everyone
would reach for does not exist on that path**, which is exactly -140 (1)'s point one level up.

⚠ And the selection is the **same substring predicate** as `:1392` — `"pad" in lbl`. Two sites, one rule. ⚠ Caveat
I attach: `shape_label` is Newton's label and may not be the MuJoCo geom name, so **I have not verified that the
claws fall inside this set** the way they do at `:1392`; the shared rule is the point, not a specific membership.

### 16.4 ⭐ (3)② rests on a property that survives all of this

`mj_geomDistance` is **independent of the contact filter** — established today by p5's probe and consistent with
what I read of its contract (§9.2 of the bound artifact). ⇒ ⭐ **distance still measures where contact has been
switched off**, so the proposed arm-to-column sweep works despite the flags — and for the same reason it would
work on the production path. ⭐ The instrument this court spent the day arguing about turns out to be the one tool
that sees what the physics was told to ignore.

## 17. -143 (1): the closed query, and the class already has a name in this project

### 17.1 ⭐⭐⭐ The rule being adopted is `ABSENT-IN-CODE`, and `CLAUDE.md` already defines it

`CLAUDE.md:198`, read on disk, verbatim:

> *"**第3 bucket = ABSENT-IN-CODE:** 「robust fact」主張は bank 前に mechanism が runtime code で ACTIVE か検証
> （未 wired = 「wire-then-validate」= premise FALSE、appearance-only ≠ working）"*

⇒ ⭐⭐ **the class rule -143 (1) adopts is the project's own third verdict bucket**, already governing and already
naming the failure ("appearance-only ≠ working").

⭐⭐⭐ **And RS71 already carries an instance of it — for the clips.** `RS71-System-Spec-SSOT.md:55`, verbatim:

> *"**Collision (⚠ ABSENT-IN-CODE):** the clip boxes are `shape_flags=1` VISIBLE-only — collision is OFF … **the
> COMMITTED build is still collision-OFF.** NOT a flat "resolved" until committed + robustness-verified."*

⇒ **the clips — the object the whole routing task exists to engage — have collision off in the committed build, and
the spec says so, with the tag.** ⇒ ⭐ today's stem/foot finding is not a new class. It is **the fourth instance of
a class this project banked, tagged, and wrote a rule for.**

### 17.2 The enumeration -143 (1) asks for, as far as I can close it read-only

**Disabled pairs — `2f85_koshape.xml`, 7 `exclude` elements (closed count):**

| # | pair | examined today? |
|---|---|---|
| 1 | `right_pad` ↔ `left_pad` | ⭐ **yes — the whole claw-interpenetration finding** |
| 2-5 | `base` ↔ {`left_driver`, `right_driver`, `left_spring_link`, `right_spring_link`} | ⛔ **no** |
| 6-7 | `{left,right}_coupler` ↔ `{left,right}_follower` | ⛔ **no** |

⇒ ⭐ **one of seven has been looked at.** ⚠ #2-#7 are within-gripper mechanism pairs in a closed 4-bar, so
suppression there is probably ordinary — but *probably* is what the class rule exists to stop. ⛔ I do not clear
them; I enumerate them.

**Disabled geoms:**

| where | what | note |
|---|---|---|
| p4's cell, **×5 duplicated files** | `floor`, `stem`, `foot` | §16.1-16.2, verified element-wise |
| production, `newton_skill_env_base.py:1581` | every arm shape whose label lacks "pad" | §16.3 |
| production, `test_newton_clip_routing.py:855` | arm shapes — comment: *"arm has no collision role"* | same class |
| production, `test_newton_clip_routing.py:1168`/`:1194` | ⭐⭐ **the CLIPS** — `_clip_collide` defaults to **"0"**, so `shape_flags = 1` VISIBLE-only | ✅ matches RS71:55 |

### 17.3 ⭐ A refinement to -143 / -142 (2)'s discipline, from my own stumble

-142 (2) draws the lesson *"read the element in full before asserting an absence"*, after a line-wise grep gave a
false 0. ⭐ **I then wrote a "multi-line-safe" check and it also failed** — my pattern was
`<geom name="(stem|foot)"[^/]*/>`, and `[^/]*` cannot cross the `/` inside `{SHOULDER_HEIGHT/2:.4f}`, so it
returned **1 per file instead of 2**. Re-done element-wise it gives **2 of 2 collision-disabled in all five
files**, confirming -143 (1).

⇒ ⭐⭐ **so the lesson is not "join the lines" — it is "parse the element, then test it".** Widening a regex to
cover the hazard that was just named inherits a fresh one. My first fix addressed the **symptom** p18 had
described rather than the **shape** of the predicate, which is the same move this court has been correcting all
day, in the correction itself.

## 18. ⭐⭐⭐ -146 (7) resolved by reading: the claws **do** keep collision in the production env

-146 (7) names this the session's highest-value open item: if the claws fall outside the `"pad"` set at
`newton_skill_env_base.py:1580`, then **the claws never collide with the cable in the production env and the whole
capture mechanism is void there.** It is decidable by reading Newton's MJCF importer. I read it.

**`newton/_src/utils/import_mjcf.py:693`** — how a shape's label is formed:

```
shape_label = f"{label_prefix}/{geom_name}" if label_prefix else geom_name
```

⇒ ⭐ **the Newton `shape_label` *is* the MJCF geom name** (optionally prefixed). ⇒ the claws are named
`right_pad_f1ext` / `right_pad_f2ext` / `left_pad_f1ext` / `left_pad_f2ext` (`2f85_koshape.xml:116-117`, `:157-158`)
⇒ every one **contains "pad"** ⇒ `if "pad" not in lbl.lower()` is **False** ⇒ ⭐⭐⭐ **the claws KEEP COLLIDE.**

> **The capture mechanism is not void in the production env. The claws collide with the cable.**

### 18.1 ⭐ The unnamed-geom case closes too, and the two sites turn out to agree

**`import_mjcf.py:597`** — the fallback for a geom with no `name=`:

```
geom_name = geom_attrib.get("name", f"{body_name}_geom_{geo_count}{'_visual' if just_visual else ''}")
```

⇒ ⭐⭐ **the fallback is built from the BODY name**, so an unnamed geom on the `right_pad` body is labelled
`right_pad_geom_N` — which **also contains "pad"**.

⇒ ⭐ therefore `:1580` (Newton label = geom name, with a body-derived fallback) and `:1392`
(`gname + bname` concatenated) **agree even for unnamed geoms** — not because they were designed to match, but
because the importer's fallback already folds in the body name that the other site adds by hand. ⭐ The
label-vs-geom-name caveat I attached in §16.3 is therefore **discharged**, in the direction that keeps the
mechanism working.

⚠ One detail I do **not** close: the fallback appends `_visual` for visual-only geoms, which would also match
"pad", so visual geoms on a pad body would keep COLLIDE. `add_ur5e_robotiq` passes `parse_meshes=False`, so those
geoms may not be created at all — **I have not verified that**, and I do not claim it either way.

### 18.2 What this settles and what it does not

✅ **settles:** the claws collide with the cable in the production env; the capture mechanism exists there; §16.3's
caveat is discharged.
⛔ **does not settle:** anything about the **arm** shapes, which is the finding that stands unchanged —
non-pad arm shapes have COLLIDE cleared across **both** arms (`mj_left_ss` is taken before the first arm and
`mj_arm_se` after the second), so arm-to-arm and arm-to-structure interpenetration still generates no contact.
⭐ **the two facts sit together:** the gripper's working surfaces collide; the arms do not.

## 19. -149 (3): the FK/physics split is exactly what my harness's identity legs guard

-149 (3) reports that the FK/IK model loads the **un-clawed** asset while physics loads the clawed one, so
clearance and interference checks done on the FK model **cannot see the claws**. Verified at source:

| | asset | claws |
|---|---|---|
| `test_newton_clip_routing.py:156` `ROBOTIQ_XML` | `2f85.xml` | ⛔ **absent** — this is the FK/IK model |
| `:161` `ROBOTIQ_STRIPPED_XML` | `2f85_koshape.xml` | ⭐ **present** — this is the physics build |

⇒ ⭐ **two assets, two models, and the 5.00 mm claw protrusion exists in only one of them.**

### 19.1 ⭐⭐⭐ This is the concrete failure the measurement harness was built to prevent

`arm_control_measurement_harness.py`, from its own header:

```
:23   * ``env._fk_model`` (the IK-only robot model) is explicitly excluded from
:24     measurement, and is additionally used as the AC-9 negative control.
:35   * **I-3** measured ``Model`` **is not** ``env._fk_model`` (``newton_route_env.py:690``)
:261      fk_model: Any | None  # env._fk_model -- EXCLUDED from measurement; AC-9 control
```

⇒ ⭐⭐ the harness's structural rule — *measure the `Model` the production env handed to `SolverMuJoCo`, never
`env._fk_model`* — was not abstract hygiene. **AC-9 requires the as-built to pass and the FK model to fail on at
least one leg**, i.e. it asserts that these two models are different *and that the difference is detectable*.
-149 (3) is that difference, made concrete: **the claws.**

⇒ ⭐ so for p11's path and clearance work the rule falls out directly: **run those checks against the physics
model.** A clearance measured on the FK model omits the claws silently — no error, no warning, just 5.00 mm per
side of geometry that is not there.

### 19.2 ⚠ And the naming trap in -149 (2) is the day's first finding again

`ROBOTIQ_STRIPPED_XML` **is the clawed asset**; `ROBOTIQ_XML` is the un-clawed one. "STRIPPED" names the
**tendon** stripping, not the claws. ⇒ reading the constant's name gives exactly the **wrong** model.

⇒ ⭐⭐ this is the same rule as my first measurement of the day (§4.1 of the bound artifact): two files named
`_ur15_2f85_koshape_actuated.xml`, differing in the one line that reverses the conclusion, distinguishable only by
content. **The name does not identify the model. Only the content does.** Two independent instances, at opposite
ends of one session.

## 20. ⛔ -150 (2): I printed that sentence at 13:05 and did not read to the end of it

-150 (2) reports that the model's own comment states this court's central conclusion, with numbers. **I had that
text on screen at ~13:05**, in my own `diff` output, when I compared the two same-named actuated models — the whole
difference between them was this six-line comment plus the `exclude` line it explains. The full comment
(`_ur15_2f85_koshape_actuated.xml:161-165`):

> *"Restored from the banked LOCK design `2f85_koshape.xml:176`. Prevents the claw-claw self-collision jam at the
> scripted close (the protruding コ claws f1ext/f2ext **can overlap at GRIPPER_CLOSE_QPOS**). Cable contact is
> UNAFFECTED (the cable is a separate body). **Without this line the opposing claws jam at −0.07 mm while pad1 is
> still 9.98 mm open, so the flat pads can never reach the cable.**"*

⇒ ⛔⛔ **I cited the first sentence repeatedly through the afternoon** — in -102, -124 and elsewhere, as evidence
that the overlap is by design — **and never once the last sentence**, which is the answer to the question the court
then derived from geometry over the following two hours. **Same comment. Four lines apart.**

⇒ ⭐ what the last sentence says is not a side note. It describes the case **without** the exclude line — i.e. the
world where claws cannot pass through each other, which is **real hardware**. So it is the transfer conclusion
itself, written by the author, with the number: **the flat pads never reach the cable.** Our independent figure is
**10.16 mm** against the comment's **9.98 mm** — 0.18 mm apart, plainly the same phenomenon under slightly
different conditions.

⭐ **The honest form of this**: I did not fail to find the file, or fail to open it, or fail to quote it. **I quoted
the sentence four lines above the answer.** Partial reading of a passage I had already rendered in full is a
narrower failure than any of today's others and it cost the most, because it was the one question the whole
afternoon turned on.

⇒ ⚠ and it sharpens the discipline the court settled on elsewhere: *"read the element in full"* has a companion —
**read the comment to its end.** A citation that stops where the supporting clause ends will systematically miss
the conclusion, because authors put the caveat first and the consequence last.

## 21. ⛔ §20 corrected: the sentence was ours, so quoting it would have cost more than not quoting it

-154 (1) reports that the comment I flagged myself for not quoting was **written by p4 today**. I verified rather
than accepting the relay:

- the actuated model's **only** commit is **`a3fbd7d7e4`, 2026-07-27 12:47:15**, *"Track the gripper model the UR15
  runs actually read"* — **it has no history before today**;
- the **banked LOCK** `2f85_koshape.xml` contains **neither "9.98" nor "never reach"** (closed count: **0**), and
  its comment ends at *"…Cable contact is UNAFFECTED (the cable is a separate body)."*

⇒ ⭐ **the independent authorial statement stops exactly where the court had been quoting it.** The sentence I
blamed myself for skipping was **this court's own measurement, 45 minutes old**, sitting in a file p4 had just
written.

**What stands from §20:** the reading fact. I printed the six-line comment in full at 13:05 and quoted only its
first sentence.

**⛔ What I withdraw:** the cost. I wrote that skipping it "cost the most, because it was the one question the whole
afternoon turned on." **False.** Quoting it would have handed the court **its own measurement back as if it were an
outside authority** — a circular support, which is worse than the two hours of independent derivation that actually
happened.

⇒ ⭐⭐ **and the discipline I derived was the wrong one for this case.** *"Read the passage to its end"* is still a
sound reading rule and I keep it. But the rule that would have **helped here** points the other way:
**check a comment's provenance before treating it as evidence.** Reading further would have made the error larger,
not smaller. ⭐ p18 records the same shape on its own side — the refutation was in output p18 had already printed,
carrying the file's `mtime 12:20:38`.

## 22. ⛔ -154 (5): a guard the arm-column sweep needs, since that sweep sits in my court

p4 found that `mj_geomDistance` returns **+0.00** for a fully-contained configuration (cylinder inside box, centres
coincident), while partial overlap returns a correct −12 to −102.

⇒ ⛔⛔ **a fully penetrating arm link therefore reads `+0.00`, which carries the same sign as "far apart".**
⇒ **the sweep's predicate must not treat `>= 0` as "no penetration"** — zero is ambiguous between *just touching*
and *completely inside*, and those are the two ends of the range the sweep exists to tell apart.

⇒ ⭐ **the disambiguator is already in the function**: `fromto`, the witness segment (§9.2). Its two endpoints
distinguish "the surfaces meet here" from "one geom is inside the other". ⭐ Same tool, second use — it settled the
penetration contract earlier today and it settles this degenerate case.

⇒ ⚠ this is the **third** gap in the same contract: the penetration semantics are undocumented (§9.2), the depth
saturates at the thin-axis geometry (§7), and now zero is overloaded. ⛔ I implement nothing; I record the guard
before the sweep is written, not after.

## 23. ⛔ I ran -181's query on my own file and found one stale row

-181 records that flagging a hazard does not erase the instances already written, and p18 found two in its own
ledger. **I ran the same closed query on mine.** Banked lines are not rewritten; this section corrects them.

**⛔ §14.1's third row is superseded.** It reads *"the 18.00 mm span | possible — 4.6 mm of room left"*, and I later
established that the **18.00 mm band is the wrong one for the design's mechanism**: the banked straddle needs claws
on **both** sides, so the cable's **centre** must be in the slot ⇒ the band is **[27.00, 37.00] = 10.00 mm**, not
18.00. ⇒ at the required roll the figure is **66.4%**, not 100%, and the 100% ceiling is **24.4°**, not 39.3°.
⇒ **the trade softens from 13.3% to 66.4%; it does not vanish.** I sent that correction by message at 15:53 but
never wrote it into this file — **exactly -181's point.**

**⚠ "2.16 mm" appears three times as a margin without its unit qualifier** (`bound artifact` §5, §6, §7). The
number is the **diametral** shortfall — backplate faces at ±5.08 against a cable surface at ±4.00 ⇒ **1.08 mm per
side**. Every use of it in this work compares against other **face-gap** quantities, so the arithmetic is
internally consistent; ⛔ **but read as lateral freedom it is 2× generous**, which is the misreading p18 found in
its ledger. ⇒ **wherever it is quoted as "play" or "clearance", it needs "diametral" attached.**

⭐ **And one absence worth recording:** `forearm` returns **0 hits** here — the link-containment table (which links
can fit inside the column) was sent by message and **never banked in any artifact of mine**. ⇒ it exists only in
p18's ledger. Noting it so it is not later cited to me from a file that does not contain it.

## 24. Scope

⛔ No run, no new measurement of the model, no verdict. The contact-geom names are **pB's** observation, relayed via
-123; everything I add is asset geometry and arithmetic on top of it. If pB's geom list is revised, §2 and §4 move
with it. Gate unchanged; I do not self-start.
