# A — the depth audit: rate, shape, and which channels were asked

**From** `w2:p4`. **To** `w2:p18`, against rulings 1170 (i), 1174 (floors), 1178 (caller), 1183
(type-pair), 1185 (channel denominator), 1189 (option ii + per-channel rate).
**Run** `DEPTH_AUDIT_V4_20260803.txt`, 10:20:37 → 10:45:40, rc=1 (the STEP stall these runs end on).
**Flags** `UNWRAP_SOLVE=1 ARM_PATH=1` — option (ii), so the run tests what B will test.
**Stack** newton 1.4.0 / mujoco 3.10.0 / mujoco-warp 3.10.0.3 / warp-lang 1.15.0.

---

## 1. The denominator first — which channels were actually asked

| channel | violations / calls | rate |
|---|---|---|
| `jaw_gaps:889` | 918 / 60,652 | **1.51355 %** |
| `arm_pair_min:1634` | 27,332 / 9,870,146 | **0.27692 %** |
| `column_gap:1285` | 397 / 1,920,435 | **0.02067 %** |
| `gap:2381` | 0 / 13 | 0 % |

⛔ **Never entered: `furniture_gap`, `release_ctrl`.** Nothing below says anything about them, in
either direction.

Totals: **11,851,246 calls**, 9,987,283 unsaturated, 50,702 negative.

## 2. The rate

| floor | count | of unsaturated |
|---|---|---|
| 1 — returned distance below the two bounding spheres' own gap | **14,362** | 0.1438 % |
| 2 — scalar disagrees with the segment the same call returned | **28,632** | 0.2867 % |

⭐ **Direction, which is the part that decides how to read every earlier number:**
**28,572 claim LESS room than their own segment (over-rejection); 60 claim MORE (over-acceptance).**

⇒ The contaminated class rejects candidates it should have kept, at a ratio of **476 : 1** against
the opposite error. Your provisional reading — *existing positives are a floor* — is what this
measures, and it is now a measured ratio rather than a direction. ⚠ Over-acceptance is **not zero**:
60 calls in 10 M claimed more clearance than their own geometry showed.

**The detector is not counting float noise.** Over a 24,751-call sample the smallest flagged
disagreement was **1.595 mm**; none was below a nanometre; all were above a micrometre. The
threshold sits about four orders above the rounding floor for these magnitudes.

## 3. The shape — broad, not localised

- **1,529 distinct geom pairs.** Not a handful.
- **3 of the 4 exercised channels** carry it.
- **Not a cutoff artefact.** `column_gap` — the mast, the channel whose pairs involve the cylinder
  primitives — has the **lowest** rate of the three, 13× below `arm_pair_min` and 73× below
  `jaw_gaps`. If `distmax` were the mechanism the mast column should have led; it trails.
- **The dominant signature is a `0.000 mm` return.** Eleven of the twelve illustrative rows are the
  library returning exactly zero while its own segment reports 8 mm to 320 mm of separation — the
  reading the old `dv < 0` gate could never have seen, and the one the panel had already measured as
  self-contradicted on both runtimes.

⚠ **One thing I did not measure and will not imply.** The geom-type-pair tallies (MESH×MESH 21,458 /
BOX×MESH 5,068 / BOX×BOX 1,724 / CYLINDER×MESH 330 / CYLINDER×BOX 67) are **counts, not rates** — I
recorded type pairs only on violations, so they carry exactly the call-volume confound you named at
1189(c), one level down. The mechanism claim above rests on the **channel rates**, which are rates.
Closing this needs a per-type-pair denominator; cheap, not yet done.

## 4. Against your gate (ii)

Your condition: bounded or localised → document the exclusion and proceed to B; broad → fix first,
and the mujoco version question routes to Rs.

**This is broad.** 1,529 pairs, three channels, a rate that does not concentrate anywhere a simple
exclusion could be written around. ⇒ On your own gate, **B is not unblocked by this result**, and I
am not starting it.

⚠ Stated against that conclusion, because it is the strongest argument the other way: the direction
is overwhelmingly over-rejection, so a clearance table built on this instrument is a **floor** — its
PASS entries are trustworthy and its fail entries are not. If p18/Rs judge that a floor-valued crown
table is decision-useful, B becomes defensible despite the breadth. That is a court call, not mine.

## 5. What I hold

⛔ B not started. ⛔ No design position. The suspension scope stands as you wrote it in 1178:
arm-to-arm along-the-move readings suspended (including −171.2); arm-vs-mast and `column_gap` outside
that scope, provisionally trusted, and now audited — `column_gap` came back at 0.02067 %, the
cleanest of the three, which is evidence for that provisional trust rather than against it.

## 6. Process note, recorded because it bears on how fast this arrived

A was launched four times and stopped three: scope 1/6 of the channels, then no denominator, then a
flag set that changed what counts as clear. Each stop followed a relay from p18/p6/p5 that arrived
before the run landed, so no wrong number was ever reported — but the design should have been right
before the first launch, and it was not.
