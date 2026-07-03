# DQ7 stage (ii) full-batch deliverable (W0 + {11}(a) verdict + W3 design) — STOP for %12 review before batch spend

**COORD %11 · 2026-07-03 15:44 JST · 0-commit.** Per %12's W0-W3 gate. rollout prohibited. Full batch does NOT convert/spend until %12 reviews this.

## W0 — converter demo-naming fix = DONE + byte-id VERIFIED
- **converter** `route_demo_to_bc.py` (`_offset_from_meta`, 3-tier: meta `env_gates.CABLE_XY_OFFSET` → legacy dir `rec_<x>_<y>` → (0,0); dir basename stays the demo identity, offset drives only affine/hull/val). **byte-id regression PASS** (rebuilt clean b2 == `b3472e8c`/`0ed5149c` EXACT) + arbitrary-naming works (rec_d1a+rec_c11 both IC(0,0) distinct, no crash). sha `d2fbca1b`.
- ⚠ **recorder gap closed (I completed):** NO existing recording meta had `CABLE_XY_OFFSET` → tier-1 was dormant → added `CABLE_XY_OFFSET` to `route_demo_recorder.py` `env_keys`. **npz byte-id PASS** (None-path re-check `none_cpu_full_w0` == `4eb7234b` cmp-exact; env_keys is meta-only, used solely in `_write_meta`) + meta now carries `CABLE_XY_OFFSET` → tier-1 LIVE for batch recordings. sha `bd5457f3`.
- **caveat (accepted):** reduced fail-loudness — a typo'd offset-dir now → (0,0) not STOP (cost of free-form names; batch uses meta-authoritative naming so moot). Both files NON-locked, 0-commit, need %12 commit approval.

## {11}(a) — VOLUME-vs-MECHANISM = **MECHANISM** (§運用28-verified, %9 P1-P4 applied)
Added rec_c11b ({11} R kick **[−10,−8,6]mm**, opposite dir to c11's [12,9,−5]; regrasp_ok=True under kick — guard held) → M2' = M2 + c11b ONLY (affine/val-split byte-identical to M2, controlled) → re-probe.
- **own-region RHOVER Δ_ee (P4 readout) = +0.00339 at n=2** (n=1 was +0.00255) — **wrong-signed, moved MORE positive** (away from restoring), ~30σ from the −0.08 VOLUME threshold. **P2 SIGN: no negative flip → MECHANISM.** Robust: ±10mm +0.0045 / probe-B(1053 rows) +0.0033 / boundary-sweep all +. Positive control {1} γ⊥ −0.20/−0.40 = probe detects real restoring (not a machinery null).
- **P3 direction-independence:** BOTH c11 [12,9,−5] AND c11b [−10,−8,6] fail → MECHANISM confirmed direction-independent (P3 confound moot in this branch).
- **P1 recovery-rows (apples-to-apples):** {1}@2 = 45 (d1a 20 + d1b 25); {11}@2 RHOVER-recovery ≈ 60-72 (c11/c11b post-kick). **{11} has ≥ {1} recovery-rows → NOT a recovery-row/volume deficit** — partially REFUTES %9's "short recovery" pathology, strengthens MECHANISM.

### Escalation packet (→ %12→Rs; %9 requirement)
- **verdict basis:** own-region sign +0.00339 (n=2, both directions, direction-independent) + recovery-rows comparable/more → mechanism-not-volume.
- **refined pathology (candidates, %9's list minus "short recovery" which P1 refuted):** (i) **moving-target** — {11} RHOVER `_fr` interpolates toward `_hovR`, so post-release "recovery" is toward a MOVING waypoint → the restoring label is ambiguous/degenerate; (ii) **cable-argmin dependence** — {11} restoring is cable-position-dependent (`_kR` argmin), which the cable-INDEPENDENT ee_only probe may not reward; BUT seg_following ALSO moved wrong-direction (0.281→0.232 down) = "pair-restoring [seg↑ + ee↓] not taught" is the observed fact; (iii) re-grasp-APPROACH geometry ≠ {1}'s pre-grasp hold-recover.
- ⚠ **redesign caution (design-gate, Rs専権):** release-margin relaxation would touch the LOCKED `regrasp_ok` (reach+grip verdict) → NOT proposed. Restoring-label-strengthening candidates instead (e.g. a HOLD-recover at {11} vs the moving-target kick, a different {11} sub-phase) = Rs design decision.
- **{11} = HOLD from batch + escalate redesign.**

## W3 — full-batch design ({1}+adjA; {11} EXCLUDED pending redesign)
- **composition:** {1} GRASP_DESCEND injection recordings (the WORKING phase, γ⊥ −0.159 at n=2) + adjA (seg-follow, non-load-bearing). **NO {11}** (MECHANISM). Proposed ~16 {1} + 8 adjA (%12 sizes to GPU budget / target {1}-γ⊥-toward-GO≤0.5; wave-1 {1}×2 gave −0.159 so more needed for the bar — or accept directional).
- **{1}:** IC from CP-C survivor grid (R_MISS (−8,+8) excluded), diverse kick directions/magnitudes ([2,20]mm, Z-comp ≥0), 1 injection/recording (isolated).
- **naming (uses W0):** free-form `rec_batch_NN` + meta `CABLE_XY_OFFSET` (tier-1 live) → correct IC; same-IC recordings no longer collide.
- **adjA:** distinct 5mm-grid reach-screened offsets (±5,0),(0,±5),(±5,∓5)… via the fix-⑤ CP-A′ reach screen — **NO byte-dup of existing clean recs** (avoid the wave-1 adjA≡p10_0 issue).
- **val twin-leak avoidance (%12 W3):** ensure no byte-identical twin split across train/val → **whole-demo val = SECONDARY check only**; the OG directional-γ⊥ (own-region) is the primary anchor (as wave-1).

## Deliverable status → %12 review
W0 (byte-id verified) + {11}(a) MECHANISM (escalate) + W3 {1}+adjA design. **STOP — no batch convert/spend until %12 review.** {11} allocation resolved = EXCLUDE + escalate. Open for %12: (1) W0 commit approval; (2) {1}/adjA batch size + IC/direction allocation; (3) route the {11} redesign escalation to Rs. 0-commit / rollout prohibited / band=γ CP-(ii)-5 only.
