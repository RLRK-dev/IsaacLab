# P0 — delta verification: `:415` deletion, 11-site placement, stack printing, and the citation check

date: 2026-07-27 21:34 JST (measured)
author: w2:p0 — verifier of the UR15 lane
target: `ur15_cell_spec.py` **sha256 `f6f0d357af64ff9a5809ff2d…`** — pin re-derived, matches; commit
`691648d445` *"Take the strict form, land the placements, and correct my own notes"*.

---

## 0. Verdict

| item | verdict |
|---|---|
| `:415` `_plain_coefficient` deleted, strict form restored | ✅ **confirmed and discriminating** |
| 11-site placement | ✅ **template 0, one name left (`FLOAT_Z`, frozen)** |
| stack printing | ✅ **5/5, and p4's own test reproduces 5/5** |
| the extra citation check | ⭐ **not a citation error** — but ⛔ **the spec is dirty right now** |
| p18's EI_eff correction to my -389R | ✅ **verified — I take it; my ratios were 2× too large** |

---

## 1. ✅ The strict form is back, and the hole went with the set

`_plain_coefficient` occurs **0 times**. Probed:

| expression | result |
|---|---|
| `X = CABLE_R * 2` / `* 3` / `* 1000.0` / `/ 2` / `* 0.5` | **all flagged** |
| `X = C[0]` | only `C` — the subscript does not flag `X` |
| `for i in range(3)` | free |
| `X = sum(LIMS[0])` | free |
| `X = CABLE_R` | free |

⇒ every literal is caught regardless of position, and structure — subscripts, `range()`, calls over
owned names — stays free.

⭐ **The `2.0`/`3.0` asymmetry I reported is gone because the set is gone.** I had listed the
borderline members as if the fix were to complete the enumeration; removing the enumeration is the
better fix, and it is the one that cannot develop a new hole next week.

## 2. ✅ 11-site placement

| | before | now |
|---|---|---|
| `template_literals("ur15_steps_wired.py")` | 23 | **0** |
| `guard("ur15_steps_wired.py")` | 49 | **1** — `FLOAT_Z` only |

The single remaining name is the one frozen on p5's two conflicting rulings, so the placement is
complete up to that.

## 3. ✅ Stack printing, closed in the strongest form

All five recollation artifacts now carry `newton 1.4.0 / mujoco 3.10.0 / warp 3.10.0.3`.

⭐ And p4's own test reproduces. Stripping the stack lines from each current file and comparing
against the pre-header version at `db734d0544`:

| file | old md5 | stripped md5 | |
|---|---|---|---|
| bisect | `d7226b33d3cf` | `d7226b33d3cf` | MATCH |
| clawfloor | `e047f624cd5b` | `e047f624cd5b` | MATCH |
| reach | `90f690aef1ec` | `90f690aef1ec` | MATCH |
| saddles | `14869082a826` | `14869082a826` | MATCH |
| sweep | `8079965ac459` | `8079965ac459` | MATCH |

⇒ **5/5.** This is the right closure of my finding 2, and stronger than adding a header would have
been on its own: it establishes that the numbers did **not** change when the header was added, so
*identical numbers beside a changed stack* is now on the artifact. The evidence discriminates.

## 4. ⭐ The citation check: not an error, but the spec is unbanked right now

Resolving both shas against the spec's own history:

| commit | time | blob |
|---|---|---|
| `1c31c1b416` | **21:15:45** | **`41c5b24eae18`** ← what the -077 report cited |
| `691648d445` | **21:27:01** | **`f29a68411869`** ← HEAD, what -397 calls the banked blob |
| working tree | now | **`c61b03c2e770`** |

⇒ **the report's citation was correct when it was written.** `41c5b2…` was the current blob at
21:15:45, and the spec moved eleven minutes later — in `691648d445`, the very commit that landed
the report's own subject. Both values are right at their moments; neither is stale.

⛔ **What is worth reporting instead:** `git status` shows the spec **modified** — the working tree
(`c61b03c2e770`) matches no commit. Anyone reading the spec on disk right now is reading content
that is not banked, and a pin taken from it would not reproduce in a clean checkout.

⭐ The general form, which this is the third instance of today: a citation should carry **the commit
it was read at**, not only the sha. `41c5b2…` alone cannot be resolved to a moment by a later
reader; `41c5b2… @ 1c31c1b416` can.

## 5. ✅ I take the EI_eff correction

`EI_eff = K × SEG`:

| | K | SEG | `EI_eff` |
|---|---|---|---|
| cell / route | 0.02 | 0.030 | 0.00060 |
| steps / reaim | 0.12 | 0.030 | 0.00360 |
| wired (SSOT) | 0.3333 | **0.015** | 0.00500 |

⇒ **wired/steps = 1.39×, wired/cell = 8.33×** — p18's figures reproduce exactly. My **2.78× /
16.66×** were **per-joint K** ratios, which overstate by exactly 2× because the segment halved at
the same time.

⇒ I compared a per-joint quantity across configurations whose per-joint length differs — the same
"same name, different measurement surface" class I have been reporting in others. **Direction and
conclusion survive** (both ratios exceed 1; the bending term still grows; the L² selection still
needs re-making at the cell's stiffness), but the magnitude was twice what I said.

## 6. Scope

**Did**: re-derive the module pin; probe the restored strict form with 9 forms; measure the
template and name residue on the wired driver; check all five artifacts for the stack header;
reproduce p4's md5 test against `db734d0544`; resolve both cited spec shas against the file's
commit history and check its working-tree state; verify the EI_eff ratios from the drivers' own
constants.

**Did not**: read p4's -077 message itself (it is a message, not a banked file — the citation is
known to me only through p18's ledger); judge the `FLOAT_Z` freeze; run the cell.

⛔ No implementation, no simulation run.
