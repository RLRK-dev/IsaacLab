# P-D1 RESULT (prereg v1.2 `32617b119a`; design v1.6 `f200bfd78c`; probe v0.7 `7b4690eed2`)

- **Date:** 2026-07-19 13:1x JST (exact stamps in the run summaries; date-THEN-write at commit).
- **Author:** RS-TECH-LEAD (w2:p4). **Verdict authority:** p5 (design court) + **Rs (video human-GT — video leg PENDING at this doc's first commit, flagged loud)**.
- **Evidence:** 6 runs `pd1_probe_20260719/r{0..5}v12_*` (all `COMPLETE.ok`, source-integrity + device bars PASS) + `analysis_result_v12.json`. Numbers below are from the analysis file; nothing here is from memory.

## 1. Parity table (all runs)

| run | g3 | pin | done | first cause | note |
|---|---|---|---|---|---|
| R0 contaminated-kin | 242 | 246 | 347 | B_contact_loss | reproduces the banked chain exactly |
| R1 clean-kin (L-P0) | **never** | never | 899 (horizon) | none | **chain does not form on the clean substrate** |
| R2 PD nominal | never | never | 141 | B_contact_loss | matches R1 on chain predicates; termination differs (§3) |
| R3 PD+ramp | never | never | 141 | B_contact_loss | **≡ R2 exactly** (q delta = 0.0) |
| R4 stale | never | never | 899 | none | instrument run |
| R5 ×0.1 | never | never | 899 | none | exploratory |

## 2. L-P0 contamination effect (R0 vs R1) — the headline

Same build, same seed, kinematic drive both; ONLY the imported-actuator tug removed (B1-strip):
the grasp chain flips from **g3=242 / pin=246 / drop B@347** to **no grasp at all, no pin, full-horizon**.
Arm q divergence R0-vs-R1 ≤ **1.1 mrad** (the kinematic drive forces the same arm poses) ⇒ the flip is
carried entirely by the CABLE-side physics response to the hidden saturated tug. **The banked
choreography's grasp chain requires the contamination.** Per design §7-5/§12: banked fidelity/transfer
claims stay UNVERIFIED-on-clean-substrate; **S-1 route-reproduction gate = choreography-blocked → re-sequencing
(demo re-record on the corrected substrate, #21 fold) = Rs surface.** ⚠ this is the impact-assessment
output (REQUIRED-to-RUN); it is NOT a probe pass/fail condition.

## 3. PD realization effect (R1 vs R2) — the pivotal-unknown answer

- **L-P1 bars: FAIL (transient)** — tr_joint_max **0.512 rad** (bar 5 mrad), tr_EE_max **99.9 mm** (bar 3 mm).
  Quasi-static window EMPTY (g3 never) → qs bars = **N/A per P-2** (never PASS).
- **L-P3 saturation: PASS — 0.0% on every joint.** Max |f_raw| at the worst joint = **25.1 N·m < 28 cap**.
- **Mechanism (measured, not assumed):** the error is a **viscous velocity-tracking lag**, not force
  starvation: worst joint = wrist_2 (both arms, symmetric 0.512), where steady slew lag ≈ (kd/ke)·ω =
  (100/500)·(~2 rad/s) ≈ **0.4 rad** — matching the measured 0.45-0.51 during the fast early phase, decaying
  to ~1-5 mrad in slow phases (profile: 0.45 → 0.51 → 0.20 → 0.02 → 0.005 → 0.001). Size3 joints show the
  same law at (400/2000)·ω. ⇒ at vendor gains the arm is force-FEASIBLE but velocity-LAGGED; the fast
  recorded phases exceed the vendor damping's tracking bandwidth.
- L-P4 no-haul: **PASS** (err[frame 0] = 4.2e-5). M-6 dwell events (15 mrad × 48 frames): 0-2 per joint
  (reported). A-4: penetration 0.0 ≥ −3 mm PASS; cable Δv 2.1e-4 ≤ 0.01 PASS. A-1..A-3/A-5..A-7 + L-P6
  census: PASS in-run (loud asserts, none fired).
- **L-P2′ vs the clean reference R1:** chain predicates MATCH (both g3-never/pin-never); termination
  DIFFERS (R1 horizon vs R2 drop B@141 — the lagging arms trip the contact-loss debounce). P-1 continuous
  divergence (REPORTED, no bar): arm Δq max 0.512 (the lag itself), EE 99.9 mm, cable proxy divergence
  present. ⇒ **L-P2′ = PARTIAL: predicate parity holds, termination parity does not.**

## 4. Instrument legs

- **R4 stale-target (§12.1): instrument VALID** — calibration dev max **8.9 mrad** ≪ band (196 mrad max);
  fail-ability ✓ (rad-scale measured error exceeds the L-P1 bars and the pipeline flags it).
- **R3 ramp ≡ R2 exactly (0.0)** — the M-5 ramp at a synced start is identity, as designed.
- L-P1 stream cross-check: max|ctrl − intended| = **0.0** (the FF ctrl path updated every frame — the
  positive path-readback demanded by review v3 A-P0-3).

## 5. Probe verdict INPUT (bar arithmetic only; verdict = p5 court)

- Prereg §5 tree: **FAIL(tracking)** branch — with saturation 0% ⇒ NOT the re-trajectory branch;
  the §8-4 gains-sensitivity frame applies (the viscous mechanism suggests the kd/ke ratio, not ke
  magnitude, as the lever — p5's call; effort caps stay untouched per §3.1).
- BUT ordered with §2: the clean substrate does not carry the banked chain even kinematically, so
  "PD fails the banked choreography" is bounded by "the banked choreography is itself contamination-
  dependent". The two directions (gains re-tune vs choreography re-record) meet at the Rs re-sequencing
  surface (§12 note).

## 6. Video leg (mandatory-or-justified) — status

**PENDING at first commit (flagged loud).** Next action in this chunk: offline replay renders of R0/R1/R2
from the per-step `bq_steps` logs → `~/Downloads` for Rs human-GT (motion standard alongside
`p2r_c11_route.mp4`). No physical-validity claim in this doc is final until the Rs video leg.
