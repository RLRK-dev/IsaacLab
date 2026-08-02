# Why the route never moved — and what it does to today's results

**Driver** `ur15_steps_wired.py` @ `3474e3ab2c`. All measurements at `START_TRIES=240`, grasp
centre −0.200, the built mounting.

---

## 1. The symptom

Every run of the route ends the same way, at the same place:

```
STEP 2 COMMAND L: reached 0.0% of the way to the solved pose in 2.2s,
  held back on 10560 of 10560 ticks because THIS arm was more than 5.2 mrad behind its own command
STEP 2 COMMAND R: reached 0.0% ... held back on 10560 of 10560 ticks
```

Both arms, every tick, no progress. The step ramp advances only while an arm is within
`TRACK_TOL = ARM_CLEARANCE / ARM_REACH = 8 mm / 1546 mm = 5.18 mrad` of its own command.

## 2. The measurement that explains it

Standing error at the start pose, before any step runs — the exact quantity the gate compares:

| arm | standing error | tolerance | per joint |
|---|---|---|---|
| L | **18.14 mrad** | 5.18 | j1 = +18.1, rest ≈ 0 |
| R | **929.31 mrad** | 5.18 | **j0 = −929.3**, j2 = −486.9 |

and, in the same readout:

```
L touching: R_wrist_1_link, R_wrist_3_link   (via L_upper_arm_link)
R touching: L_upper_arm_link                 (via R_wrist_1_link, R_wrist_3_link)
```

⇒ **The two arms are jammed against each other.** The right arm's j0 is 53° short of its command
because the left arm is in the way. No joint is at a limit.

⇒ The gate cannot open, so every step reports 0.0%, and the route has never taken its first step.

## 3. The cause, in the driver's own words

The clearance test checks each arm against two obstacles:

| obstacle | at the pose | **along the move** |
|---|---|---|
| the mast (stem, foot, crown) | yes | **yes** — `path_mast_min`, sample count derived from the obstacle's radius |
| **the other arm** | yes | ⛔ **nothing** |

`path_mast_min`'s docstring says why the mast needed it, and describes exactly what is happening
here with the other arm as the obstacle:

> the FOREARM sweeps through the mast on the way there and jams. Joint 1 then sits at its whole
> 433 N·m pushing on the column and arrives 92 degrees short. **A pose the arm never reaches is not
> made safe by being clear.**

The fix written for the mast on 07-28 was never extended to the other arm. Both arms sweep about
**250°** from home to their start poses (L 274°, R 244°) and pass through each other on the way.

⚠ Two orderings were tried and neither is a workaround: **L first** → L arrives (1.93 mrad), R jams
at 94°; **R first** → both jam worse (R 100°, L 165°). My prediction that whichever arm moved first
would arrive was **wrong**, and being wrong is what pointed at the path test rather than the order.

## 4. ⛔ What this does to the results banked today

`path_arm_min` adds the missing test (same derivation as the mast's, using the other arm's smallest
bounding radius as the obstacle size), behind `ARM_PATH=1` because it changes what counts as clear.
At grasp centre −0.200:

| | without the path test | **with it** |
|---|---|---|
| L | 138 solved / 31 clear | 138 / **20** |
| R | 139 solved / 4 clear | 139 / **0 — all put back** |

Rejections now read `the other arm ON THE WAY (e.g. 44 ↔ 8 at 32/36 along the move)`.

⇒ **Every witness reported today is an endpoint witness.** The seven open grasp centres, the crown
columns, the all-pairs separations — all of them are statements about poses, and at the one centre
now tested with paths included **the right arm has no clear start pose at all**.

⛔ This does not say the cell is impossible. It says the question was never asked, and where it has
now been asked once, the answer was zero.

## 5. What is not yet known

1. **One centre.** −0.200 only. Whether any grasp centre keeps a right-arm pose whose path is clear
   is unmeasured.
2. **The path is a straight line in joint space.** The ramp interpolates linearly from home; a
   different route between the same endpoints might be clear. Nothing here tests that, and the
   clearance test cannot, because it only knows the straight line too.
3. **The sample count bounds tunnelling, not grazing** — the same limit the mast's test carries.
4. ⚠ **The stereo head is still not in the default cell** (`STEREO_HEAD=1`, §
   `RS_AUTHORISATION_CUSTODY_P4_20260802.md`), so these counts are still measured without an
   obstacle the reference declares.

---

## 6. ⭐⭐ The whole open region, with the path test in — the right arm keeps nothing

`GRASP_CENTRE_SWEEP_TRIES240_ARMPATH.txt`, `ARM_PATH=1`, same mounting, 240 draws:

| centre x [m] | L solved / clear | **R solved / clear** |
|---|---|---|
| −0.110 | 123 / 1 | 140 / **0** |
| −0.120 | 124 / 1 | 139 / **0** |
| −0.130 | 126 / 6 | 138 / **0** |
| −0.140 | 137 / 8 | 139 / **0** |
| −0.150 | 140 / 9 | 139 / **0** |
| −0.200 | 138 / 20 | 139 / **0** |
| −0.250 | 133 / 9 | 140 / **0** |

⇒ **Not one grasp centre in the open region leaves the right arm a start pose that survives an
arm-to-arm path test.** The left arm keeps between 1 and 20; the right arm keeps none, everywhere.

⇒ The blocker is **the right arm's approach**, and it does not move with the grasp centre — which
is what every measurement before today was varying.

### ⚠ Precisely which path this tests

The solve runs three rounds with `near` = the previous round's pose, so the path tested in the
**printed** round is from that pose, not from home. The physically travelled path — **home → final
start pose** — is the one round 0 tests, and it is the one the standing-error measurement (§2)
observes directly: the arms arrive **in contact**, the right arm 53° short. ⇒ The sweep and the
physical measurement agree in direction; the sweep is not a restatement of it.

### ⛔ What is NOT worth running next, and why

Adding the stereo head (`STEREO_HEAD=1`) on top of this can only remove candidates from counts that
are **already zero** on the right arm. It cannot change the verdict, so it is not the next
measurement. It becomes worth running again if the right arm's approach is changed and starts
keeping poses.

---

## 7. ⭐⭐⭐ The blocker was the path REPRESENTATION, and both arms now arrive

`solve_ik` wraps its answer into a principal range. The ramp then interpolates linearly from the
previous pose to that wrapped number, so a base joint sitting near ±π is driven **almost a full
turn the wrong way** — 274° where 86° would do, 244° where 116° would do. That sweep is what
carried the arms through each other and through the furniture.

⚠ **Unwrapping after the solve does not work**, and measuring that is what located the fix:
`UNWRAP_START` (applied to the chosen pose) took the left arm to 0.00 mrad on its own, and did
nothing at all when combined with the path tests — *"nothing to unwrap"* — because the candidates
whose **wrapped** path collides had already been discarded. The shorter path was never tested.

`UNWRAP_SOLVE` shifts each candidate by the multiple of 2π nearest the previous pose **before** the
path tests run, so every path test sees the path the arm will actually take (only where the shifted
value stays inside the joint's range).

**Measured at grasp centre −0.200, 240 draws, ARM_PATH on:**

| | path test, unwrap after | **unwrap inside the solve** |
|---|---|---|
| L clear | 20 | **36** |
| **R clear** | **0** | **8** |
| L standing error | 43.96 mrad | **0.00 — gate 100% free** |
| **R standing error** | **275.97 mrad** | **0.00 — gate 100% free** |

⇒ **Both arms reach their start poses exactly.** The right arm's zero — which held against a left
arm at home, at its solved pose, in both solve orders, and at all seven grasp centres — was **the
wrapped path**, not the geometry, the placement, the crown, the grasp centre or the solve order.

### ⭐ It carries the stereo head, as the deferral protocol requires

p6's condition: the first **positive** claim must carry the reference's stereo head, and so must
any claim that the candidate set moved. Both apply here (0 → 8). Run with `STEREO_HEAD=1`
(`unwrap_logs/unwrap_solve_with_head.txt`):

| | without the head | **with it** |
|---|---|---|
| L | 138 / 36 | 138 / **36** |
| R | 139 / 8 | 139 / **8** |
| standing error | 0.00 / 0.00 | **0.00 / 0.00** |

**Identical.** The obstacle the cell was missing does not touch this result.

### What is now true, and what is not

1. ⭐ **The route has passed the point where every run today stopped.** It is past the start-pose
   reach and into the per-step aim solves.
2. ⛔ **It is not finished, and the aim solves are already falling back** (`NOT ONE of 1 candidates
   cleared`). Passing the first blocker is not completing the route, and nothing here says it will.
3. ⚠ **One grasp centre.** −0.200 only; the other six are unmeasured under `UNWRAP_SOLVE`.
4. ⚠ The zeros banked earlier today remain correct **as measured** — they were zeros under the
   wrapped straight line, which is the scope p18 formalised. This narrows that scope; it does not
   retract the measurements.
