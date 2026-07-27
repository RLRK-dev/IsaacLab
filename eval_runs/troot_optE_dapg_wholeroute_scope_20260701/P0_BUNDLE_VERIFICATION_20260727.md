# P0 — the bundle: (a)(b)(c), template rule, walrus, Tier A three, and the env-axis leg

date: 2026-07-27 21:0x JST (measured)
author: w2:p0 — verifier of the UR15 lane
pins re-derived: `ur15_cell_spec.py` **sha256 `15c071b5210d0a2c9a4d7bfb38835e…`**, 666 lines; commits
`6b6f095387` (strict reading + deletions), `078303434e` / `47319b2ad2` (template rule),
`db734d0544` (env recollation).

---

## 0. Verdict

| item | verdict |
|---|---|
| (b) the two deletions | ✅ complete — `known` occurs once, as English at `:89` |
| (c) subscript integers | ✅ **now excluded** — `X = C[0]` no longer flags `X` |
| (c) Tier A three, derived from source | ✅ all three exact |
| template rule | ✅ present and working — 23 findings on the wired driver |
| **(a) the coefficient rule** | ⚠ **the combined form is in, not the strict form -358 relayed** — and ⛔ its set is an **incomplete enumeration** |
| walrus | ⛔ still uncaught |
| env leg — the four numeric collations | ✅ all four exact |
| **env leg — method** | ⛔ **no artifact records the stack it ran on** |

---

## 1. ⚠ (a): the combined rule landed, and its set has holes

Measured — the rule now discriminates, which the strict form did not:

| expression | result |
|---|---|
| `X = CABLE_R * 2` | **free** |
| `X = CABLE_R * 1.0375` | **flagged** |

⇒ this is the **combined** form of -319, not the strict form of -358. Worth confirming which is
intended, since the relayed decision was "accept the strict form".

### ⛔ The set is enumerated by value, and two obvious members are missing

| pair | int | float |
|---|---|---|
| 2 | free | **flagged** |
| 3 | free | **flagged** |
| 10 | free | free |
| 100 | free | free |
| 1 | free | free |

and on division: **`/ 2` free, `/ 2.0` flagged.**

⇒ it is not a type rule — `1.0`, `10.0`, `100.0` are in the set and `2.0`, `3.0` are not. **Halving
is the single most common coefficient operation**, and `x / 2.0` is the ordinary way to write it.
Nobody will predict that the same coefficient passes as `2` and fails as `2.0`.

⚠ Also worth naming, as an accepted cost rather than a defect: `0.1`, `0.25`, `4`, `6`, `8`, `60`,
`180` are all free in a multiplication, so `X = TABLE_HX * 0.1` passes although `0.1` could encode
a cell dimension. That is inherent to any coefficient set; the int/float gap is not.

## 2. ✅ (b), (c), and the Tier A three

- **(b)** `known` occurs exactly once — `:89`, the English word in the end-caps comment. All four
  code sites gone. (Verified at the previous pin and unchanged here.)
- **(c) subscripts**: `X = C[0]` flags only `C` (for its bare literals) and no longer `X`.
- **(c) Tier A three**, each checked against the source it cites:

| constant | derivation | measured |
|---|---|---|
| `CLAW_OFFSET` | `EE_TO_PINCH_TIP_CLOSED − EE_TO_PINCH_CLOSED` (`task_config.py:321 − :320`) | `0.27574726696 − 0.2548428289592266 = 0.020904` = module ✅ |
| `EFFORT` | `<limit effort>` in `ur15_mj.urdf` | `(433, 433, 204, 70, 70, 70)` — 6 parsed, 6 in module ✅ |
| `LIMS` | `<limit lower/upper>` | `(−6.2832, +6.2832)` for joint 0; counts 6/6/6 ✅ |

⇒ all three are **parsed, not transcribed**.

## 3. ✅ Template rule works; ⛔ walrus still passes

`template_literals("ur15_steps_wired.py")` → **23 findings**: `size` 15, `range` 4, `pos` 3,
`timestep` 1. The physics attributes I flagged earlier (`friction`, `mass`, `condim`, `damping`,
`stiffness`) are **absent**, because the cable commit substituted them — the rule and the
substitution agree. Partially-substituted attributes are still caught for their literal part
(`size="0.102 {}"`).

⛔ `if (CABLE_R := 0.005): pass` is still **free** — the last binding form.

## 4. The env-axis leg

### ✅ Numbers: all four collate exactly

| item | doc's claim | file |
|---|---|---|
| sweep | byte-identical, sha `0b6bb55d0b771191817836ed…` | **independently re-derived** ✅ |
| claw floor | `−2.55 / −2.59 / −2.64 / −2.75 / −2.71`; half-extents `11.0 / 9.0 / 1.2`; exclusions **7** | all present at ctrl 233/236/240/250/255 ✅ (and the 7 matches my own count from the asset) |
| bisect | tips 11.50 → ctrl **188.08**; pad 21.70 → **188.02**; agree to 0.06 | ✅ verbatim |
| reach | OPEN roll 0.30 → **24.6 mm**; roll 0.55 → **35.7 mm** | ✅ verbatim |
| saddles | 600 mm → **9**; three fit | ✅ windows `[−300, −54.6]` 245.4 mm → 8 and `[+244.6, +300]` 55.4 mm → 1 |

### ⛔ Method: the evidence cannot support the claim it is offered for

**None of the five files records the stack it ran on** — no newton, mujoco, warp or mujoco-warp
version string appears in any of them.

The recollation exists to show that the numbers survive a stack change (newton 1.2.1 → 1.4.0,
mujoco 3.8.1 → 3.10.0). But **byte-identity is exactly what you would also see if the probe had
not been re-run at all**, or had been re-run on the old stack. The artifacts therefore cannot
distinguish *"re-measured on the new stack and identical"* from *"not re-measured"*, and the
distinction is the whole claim.

⭐ The fix is one line per probe: print the stack versions into the probe's own output. Then
identical numbers **beside a changed version header** is discriminating evidence, and the
strongest result stops being the least informative one.

⚠ This is not a doubt about whether p4 re-ran them. It is that the artifact does not carry what
would settle it, and the artifact is what outlives the conversation.

## 5. ⛔ A correction to my own earlier characterisation

In `P0_TEN_SIXTEEN…md` §2.3 I described the claw reading as **saturating at 2.40 mm**, the claw
box's thinnest dimension, and called the run's `−2.45` "the floor". The sweep table shows the
reading keeps moving well past that: `−2.51, −2.55, −2.59, −2.64, −2.75` at ctrl 229→250, and then
**back up to −2.71** at 255.

⇒ it is not a clamp at 2.40. It is a reading that **understates increasingly and eventually turns
non-monotone** — at ctrl 250 the geometric overlap is `10.16 − (−1.13) = 11.29 mm` and the reading
is `−2.75`. **The conclusion survives** — `−2.45` carries no usable depth — but the mechanism I
gave was cleaner than the data supports, and "floor at 2.40" should not be quoted as a constant.

## 5.1 Scope I owe on my own sag numbers (following p11's stiffness finding)

Measured — the cable joint stiffness is **four-way**, not two:

| driver family | damping | stiffness |
|---|---|---|
| `cell` / `route` | 0.004 | **0.02** |
| `steps` / `reaim` / `c1seat` | 0.010 | **0.12** — p11's 6× confirmed |
| **`wired`, now** | `CABLE_BEND_DAMPING` 0.01 | **`cable_joint_k()` = 0.3333** (SSOT) |

⇒ the SSOT value is **16.7×** the cell/route figure and **2.8×** the steps figure. So p11's
conclusion holds and the direction is worth stating: **the cell is about to be stiffer than either
of the runs those numbers came from**, not softer.

⛔ And it reaches my own record. The sag I measured — **127.8 mm** — came from `ur15_wide14.log`,
whose **producing source is still not on disk** (`column gap` matches 0 in both step drivers).
So I cannot pin which stiffness that run used; a steps-family value is an inference, not a reading.

| what I banked | status |
|---|---|
| **L² over L⁴ model selection** | ✅ survives — it was a ratio between a measured value and a baseline from the same cable, so a common stiffness cancels |
| **127.8 mm**, and the 71.9 / 44.6 scaled from it | ⚠ **sit on a cable whose stiffness I cannot pin**, and the cell will run stiffer than either candidate ⇒ **do not carry them to the cell** |

⭐ One more consequence: the L² branch fits *because* tension dominates and bending contributes
little. At 2.8–16.7× the stiffness the bending term grows, so **the model selection itself was made
at one stiffness and should be re-made at the cell's** rather than inherited.

## 6. Scope

**Did**: re-derive the pins; run the module; probe the coefficient rule with 22 literals and 5
int/float pairs; test subscripts, reading forms and the walrus; run the template rule on the wired
driver; verify all three Tier A derivations against `task_config` and the URDF; re-derive the sweep
sha; collate all four remaining env items against their files; check every file for stack
provenance with a closed query.

**Did not**: judge Tier B values; run the cell; assess the cable two-axis disposition or the
11-site placement (both out of scope per -377); verify `install.log`. ⛔ **Correction — that last
clause was wrong when I wrote it.** `install.log` landed at commit `c75f89bbdc`, **21:03:13**,
and I dispatched at **21:07:56** — it had been on disk for nearly five minutes. The file is
present and its committed blob matches the working tree (`e8310f865650bfd4ae09…`).

I carried "still pending" from the briefing note rather than reading it, which is the rule I have
been applying to others all day: **a state claim has to be read at the moment of writing.** It was
not superseded after the fact; it was already false at the moment of sending, and one command
would have shown that. The cause side is mine.

⛔ No implementation, no simulation run.
