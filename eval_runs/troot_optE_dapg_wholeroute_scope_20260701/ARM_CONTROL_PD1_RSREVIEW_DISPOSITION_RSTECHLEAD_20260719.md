# P-D1 disposition under the Rs PLAN_STATUS review (2026-07-19) + diagnostic batch record

- **Date:** 2026-07-19 10:26 JST (date-THEN-write). **Author:** RS-TECH-LEAD (w2:p4).
- **Trigger:** Rs review `~/Downloads/PLAN_STATUS_review_2026-07-19.md` (p6 reflection `1d5d5a3b08`) — **(d) arc HOLD**,
  8 mandatory corrections, P-D1 prereg freeze gated on ①-④. Read in full by p4 before this disposition.

## 1. Status per the review's P0-2 taxonomy (the current truth)

| lane | status |
|---|---|
| production implementation (migration landing) | **CLOSED** (unopened; L3 chain + Rs sign-off remain the gate) |
| diagnostic probe scaffolding (worktree `probe/pd1-arm-pd`, v0.3 `5084712d2c`) | **BUILT, UNLANDED** |
| diagnostic smokes + measurements (smoke-1..4, dumps) | **EXECUTED** (diagnostic) |
| 5-run batch of prereg `8ed56f65ea` | **EXECUTED — reclassified DIAGNOSTIC, NON-EVIDENCE** (see §2) |
| probe evidence | **NONE YET** — evidence-grade runs happen only under the corrected prereg (after ①-④) |
| authority / training | **CLOSED** |

## 2. The 5-run batch: timeline + reclassification (records-must-match-fact)

The batch was launched 10:05 JST under prereg `8ed56f65ea` and **completed at ~10:24 JST, before the Rs
review reached p4** (relay 10:15 JST, read ~10:20; a stop was issued and arrived post-completion). Under
the review (prereg premature pending ①-④; ③ = the neutralization mechanism must be design-owner-chosen —
the batch ran MY executor-chosen B2-zeroing), the batch is **reclassified DIAGNOSTIC / NON-EVIDENCE**.
Data retained (not deleted) as design-correction input; nothing in it is a probe verdict.

## 3. Diagnostic observations (input for p5's corrections; hypothesis-tagged, single runs, no video leg)

| run | g3 | pin | done | cause | quick tracking max/p99 [rad] |
|---|---|---|---|---|---|
| r0_kin (baseline AS-IS) | 242 | 246 | 347 | B_contact_loss | — |
| r0b_lp0 (neutralize-only, kinematic) | **never** | **never** | 899 (horizon) | none | — |
| r1_pd | never | never | 141 | B_contact_loss | 0.512 / 0.508 |
| r2_pd_ramp | never | never | 141 | B_contact_loss | 0.512 / 0.508 (≡ r1) |
| r3_pd_neg (gains ×0.1) | never | never | 899 | none | 0.493 / 0.353 |

- **O-1 (L-P0 is NON-NEGLIGIBLE — the strongest form):** removing the hidden actuator tug ALONE (kinematic
  drive unchanged) flips the pipeline from the banked g3=242/pin=246/drop=347 chain to **no grasp at all**.
  ⇒ the hidden artifact is **load-bearing for the banked grasp chain**, not a passive background — exactly
  the review's P0-4 concern ("state-dependent, can interact"). Per P0-4: decision-critical contrasts on the
  corrected substrate need rerunning if L-P0 is non-negligible — **it is** (diagnostic-grade; verification
  legs + video pending). ⚠ mechanism caveat: measured under B2-zeroing; the B1/B2 ruling (③) may change the
  neutralization implementation, so O-1 is re-measured under the ruled mechanism.
- **O-2:** r1 ≡ r2 byte-identical predicates + tracking ⇒ the M-5 ramp at a synced start = identity, as the
  repurposed L-P4 expected.
- **O-3 (instrument gap for the redesigned prereg):** the ×0.1 negative control does NOT separate from ×1.0
  (0.49 vs 0.51 max) in this regime — the L-P5 discriminability premise fails as designed; the corrected
  prereg needs a different negative-control observable (e.g., a step-response/settling metric) or bar set.
- **O-4:** PD@vendor-gains does not reproduce the grasp chain (g3 never; drop 141), with sustained ~0.5 rad
  error concentrated on wrist_2 (size1) in the smoke — but per O-1 the baseline chain itself depends on the
  artifact, so "PD fails to track the recording" and "the recording's chain requires the artifact" are
  CONFOUNDED in this batch. Separating them = the corrected probe's job.

## 4. Correction ownership map (the 8 points)

- **p5 (design doc / v1.4):** ① version+status repair + full-SHA version table (+P1-1 exact stamps) /
  ③ B1-vs-B2 ruling (Rs recommends B1-strip; B2 requires a dynamic force≡0 acceptance test) / ④ §7-5
  softening + L-P0 REQUIRED / ⑤ @4-conservative → tagged hypothesis / ⑥ tripwire temporal semantics +
  rename tracking-divergence / ⑦ §8-2 PASS → UNVERIFIED — L-P3.
- **p4 (me):** ② this doc's status taxonomy on all my surfaces / ③ reimplement per the ruling + implement
  the dynamic force≡0 acceptance test / ⑧ 3-way path enumeration at any future path freeze / prereg
  **re-freeze as v1.1 only after ①-④ land** / L-P5 redesign input (O-3).
- **p6 (on wake):** surfaces already reflected at `1d5d5a3b08`; this disposition doc = next relay content.

## 5. Prereg `8ed56f65ea` status

**SUPERSEDED-pending** — remains the frozen record of what the diagnostic batch ran; the evidence prereg
= v1.1, re-frozen after ①-④ (new bars incl. the L-P5 fix, mechanism per ③, L-P0 REQUIRED).
