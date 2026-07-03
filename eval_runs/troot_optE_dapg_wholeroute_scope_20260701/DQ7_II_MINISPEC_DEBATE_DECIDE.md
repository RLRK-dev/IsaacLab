# CC1 REBUT_OR_ACCEPT + DECIDE — DQ7 stage (ii) CP-(ii)-0 mini-spec pre-implementation debate (L3, Opus 4.8 re-run)
CC1 = %12 RS-TECH-LEAD. Panel (Opus 4.8): CC2 premise/provenance, CC3 rule/SSOT, CC4 numerical/physics, CC5 side-effects/regression, CC6 NHA. 2026-07-03 09:5x JST.
Subject: dq7_ii_mini_spec.md (injection hooks in Rs-LOCKED test_newton_clip_routing.py for perturb-and-recover). PROPOSE = approve for build with 3 open findings F1/F2/F3.
Note: an earlier Fable-5 launch of this same debate was killed by quota exhaustion (0 usable reports); this is the Opus 4.8 re-run.

## REBUT_OR_ACCEPT (deduplicated ledger; every challenge answered)

U1. **:3931 is LIFT {3} (charter §3 SKIP), mis-assigned to DESCEND {1}** [CC2 CRIT, CC3 CRIT, CC4 HIGH, CC5 CRIT — 4 bodies + CC1 code-verified: test:3927 `_ph("LIFT")`, :3931 `label="ROUTE-LIFT{k}"`, DESCEND has only :3900] — **ACCEPT (CRITICAL)**. Injecting there perturbs the 12-substep gradual LIFT whose gradualness exists to prevent the banked WR-retention drop (RS71:26 / GD-KoShape-Finger:75). Fix: delete :3931; add a build-time assert that every hooked line's `_ph` ∈ eligible set, abort on any SKIP-phase {2,3,6,7,8,14}; re-audit the entire §B line table against `_ph()` boundaries (one confirmed mis-attribution ⇒ the table was not cross-checked).

U2. **dwell-frame KEEP is anti-restoring; the label = achieved ee_pos, not commanded target; my F1 fix formula is wrong** [CC2 CRIT (label=ee_pos :287), CC4 CRIT (hold ⇒ parallel action ⇒ γ⊥≈0 opposes recovery), CC5 HIGH — CC1 code-verified: route_demo_to_bc.py:287 `wp=concat(er[next_f],el[next_f])` where er,el=ee_pos_r/l; :333/:412 "achieved ee_pos delta"] — **ACCEPT (CRITICAL)**. My PROPOSE F1 fix ("relabel dwell = recorded_target − offset") references `ee_tgt_pos`, which is NOT the label — subtracting there changes nothing the trainer reads. Under the real semantics, a held-at-offset dwell frame teaches obs(off-path)→action(parallel/stay) = the FOLLOWING failure the γ⊥ gate penalizes. Fix: **DROP the entire held window (outbound + dwell); keep ONLY post-release recovery frames** (where achieved EE moves back toward the script path = the restoring teacher). Correct the label-provenance statement everywhere (label = achieved next-frame ee_pos, NOT next-waypoint/commanded target). No algebraic relabel.

U3. **dwell=20 "control-steps" unrealizable at call-level hook granularity + 10× clock mismatch** [CC2 HIGH, CC3 HIGH, CC4 HIGH, CC5 HIGH — 4 bodies; CC1 verified: PHYSICS_STEPS_PER_RL=10 (route_demo_to_bc.py:34), cf=arange(0,·,10); loops all <20: N_ROUTE=6/N_GUIDE=8/LIFT_SUBSTEPS=12/DESCEND 8/RHOVER 10/RDESCEND 8] — **ACCEPT (HIGH)**. ik_move_both is atomic per call (target fixed once, n_steps≥50 phys = ≥5 rows), so the achievable quantum is whole CALLS, not control-steps; and §C(control-steps) vs §D(physics-frames) with cadence 10 ⇒ a builder setting end_frame=start+20 masks 10× too short → 90% anti-restoring frames leak into KEEP = silent wrong-teacher. Fix: define dwell in **ik_move_both-CALL units**, record achieved dwell_rows in meta; window fields in ONE clock (control-frame row index) with the ×cadence conversion explicit; converter ASSERT each kept p2r row's achieved-target ≈ script-target within IK residual (add to regression).

U4. **{0} HOVER is a single 52-row call — no in-phase recovery; the #1 worst cell (2.497) gets no direct teacher** [CC2 HIGH, CC4 HIGH — CC1 verified: :3893 single call, next _ph=DESCEND :3896; CC4 ground-truth {0}=52 rows/demo] — **ACCEPT (HIGH)**. Recovery bleeds into {1}'s phase-onehot ⇒ mis-attributed; {0} γ⊥ won't move (repeats (iv)'s {0} 2.497→1.680 miss). Fix: do NOT list {0} as a primary teacher; the robust pre-contact teacher is **{1} DESCEND (40 rows, loop)**. {0} either restructured into a loop (code beyond "wrap the arg" — scope explicitly if wanted) or accepted generalization-only.

U5. **{11}:4494 (RDESCEND onto cable) can corrupt the Rs-LOCKED regrasp_ok verdict / self-filter the recording** [CC2 HIGH, CC3 HIGH, CC4 MED — CC1 verified: reach check :4486-4487 `_reach_R_mm` from achieved _paR → :4515 `_at_88` → :4516 LOCKED regrasp_ok; :4494 RDESCEND immediately precedes cage-close :4499] — **ACCEPT (HIGH)**. Bytes untouched ≠ verdict-VALUE untouched: a detour bleeding past the reach-check corrupts the LOCKED derivation OUTPUT (Rs 2026-07-01「先祖返りしないように」intent). Fix: restrict {11} to the RHOVER loop :4481 ONLY (drop :4494); hard guard offset=0 before the RHOVER→RDESCEND handoff + before the reach check; assert on-disk that injected {11} recordings reproduce the None-path regrasp_ok/_reach_R_mm.

U6. **%9's binding N1 (span-preserving direction at dual-hold) is NOT in the mini-spec; %9 concur is on the CHARTER, not this mini-spec** [CC3 HIGH; CC4 independently rederived N1 as the span-survivorship fix (P(trip)=0.069/inj, 0.132/recording at {4,12}); %9 N1] — **ACCEPT (HIGH)**. mini-spec (08:45) predates N1 (08:48); "single-sided"(INV#1) was conflated with "span-preserving"(INV#2). Resolution folds into U8 (scope): v1 = primaries {1,11} are pre-contact (span not yet established) → N1 is MOOT for v1; N1 (detour X,Z-only / Y≤3mm) is pre-registered for the DEFERRED dual-hold fills {4,5,10,12,13}. The revised mini-spec must be re-validated by %9 (its concur did not license the mini-spec as-written).

U7. **Injection excursions inflate the UNION affine hull → contaminates all clean demos; sha-match regression doesn't cover the p2r+injection affine path** [CC5 HIGH — CC1 verified: _build_abs_affine over full wp min/max per phase (:157), union over all train demos (:519), amax≤0.95 assert (:451)] — **ACCEPT (HIGH)**. Fix: build the affine hull AFTER outbound/hold masking, over kept-p2r+clean frames only (or clip detour excursions from the hull); add a p2r-specific regression asserting per-phase box within tol of the clean-only b2 box + amax≤0.95 recheck on the masked set.

U8. **NHA proportionality: build primaries only; defer fills** [CC6 CHANGE_JUSTIFIED-with-scoped-HOLD; converges with the fill-specific defects] — **ACCEPT**. v1 = **{1,11} (+{0} only if restructured)** = the failing-cell teachers; **defer fills {4,5,10,12,13} to a budget-gated v3**. This halves the locked-file surface AND moots for v1: the {10} contact-fragility (U9), the {4,12} span-survivorship/N1 (U6), and the SEAT_TOPDOWN :4255 conditional (U10) — all fill-phase-only. It is also the version most likely to clear the v1-analog 2× budget (the (iv)-flagged binding constraint), since it spends budget only on scored cells.

U9. **{10} GUIDE_PRELIFT is the LARGEST phase (179 rows) AND a contact-rich しごき — risk is contact-fragility (cradle/JAM/table-load), not size** [CC4 MED — reverses my Q6 "tiny→demote" premise] — **ACCEPT**. Deferred by U8; when v3 revisits {10}, restrict to the aerial PRELIFT sub-loop only or gate on cradle/JAM/slip staying in-band (reuse is_cradle/JAM flags). A cable-loss/JAM mislabeled as a restoring demo would poison BC.

U10. **:4255 conditional on SEAT_TOPDOWN=1** [CC2 MED] — **ACCEPT** (deferred with fills U8; when built, pin the recording SEAT_TOPDOWN mode + gate :4255 eligibility, or use always-live :4263).

U11. **None-path byte-identity: mechanism differs from fix-⑤ (gate/skip vs always-on wrap); cuda:0-1-run is weak; two files change** [CC5 MED, CC2 MED — fix-⑤ test:3875 gates the whole mutation; CC4/CC5 note n_steps int() is ULP-fragile] — **ACCEPT**. Fix: None-path = LITERAL passthrough as first statement (`if sched is None: return tgt_xyz`, pure-Python floats, zero numpy, `is`-identity unit test) per hooked site; byte-identity = TWO-leg (CPU deterministic primary + cuda:0 fingerprint secondary, matching recorder fd005ab83f / fix-⑤ 0b711c6b31 precedents) and TWO-sha (route file e01ac1fa + recorder npz); per-marker re-sync by grepping the ⛔ANTI-REVERT text (not offset arithmetic), asserted at CP-(ii)-1 diff review.

U12. **Loud-notify omits the Rs-LOCKED-file-edit disclosure** [CC3 MED] — **ACCEPT**. Add an explicit non-buried line to the §8 Rs notify: "this build edits the Rs-LOCKED canonical route (flag-gated hooks around pre-contact targets), byte-identity + markers-untouched guaranteed, _ANTI_REVERT re-sync" — so the pre-GPU veto window is informed on the governance-load-bearing fact (RS71 §0 requires surfacing locked-surface touches; %9 §1-(4) tagged「推奨で良い」as interpreted/Rs-correctable).

U13. **§運用14 video leg collapsed to "video legs" — claw-zoom slip/drop dropped** [CC3 MED] — **ACCEPT**. Restate in §G: skill-path (/video-analyzer or video-analyst), unskippable, per grasp/held injection = claw-zoom slip/drop check (memory feedback-video-detect-intra-finger-cable-slip). For v1, {11} grasp gets the claw-zoom leg.

U14. **5mm span-watch bar lacks provenance + sampling-time unspecified** [CC3 MED] — **ACCEPT** (mostly deferred with fills). Cite provenance (= moves_ok 5mm/EE converge gate, RS71 §1:35) or pre-register as chosen; sample span at recovery (post-reconvergence), not during the intentional hold.

U15. **Validity-budget win ≠ γ⊥ movement (the GO bar)** [CC4 LOW — (ii) off/clean 0.065-0.208 ≪ (iv) 1.047 ⇒ validity likely met, but γ⊥ movement unproven] — **ACCEPT**. Pre-register a minimum restoring-frame count per load-bearing cell {1,11} + a wave-1 directional check (γ⊥ at {1}/{11} moved directionally) BEFORE the full batch. Conservatism (§運用15): validity = conservative-safe; γ⊥ movement = **non-conservative, must be SHOWN not assumed**.

REBUTTED (none silent): CC1's original F1 fix (wrong array) and the "keep dwell" design are the items rebutted-by-panel. Surviving intact: control-API legality (5/5 incl. CC4/CC3 NO-CHALLENGE — EE-detour via ik_move_both/solve_ik_dual is DiffIK-legal, no kinematic trick, correctly distinguished from xfrc D-2); {9} GUIDE_C2 vacuous (CC2/CC4/CC5 confirmed 0 rows); beat = CP-D replicate-null as-is is pre-registered (charter §5, %9 N3); GO bar per-cell pinned; markers :4401/:4417/:4516 byte-safe from the wrap (upstream/downstream, not the target arg); INVARIANTS untouched (CC4/CC3).

## NO_ACTION_EVALUATION
- No change (don't build (ii)): rejected — Rs Option A「推奨で良い」(made WITH Outcome B in hand) + %9 CONCUR×8 + %9 stage-(ii) concur + physics discriminator that Outcome B cannot doom (CC6 refutes (d) do-nothing and (b) skip-to-DAgger). Direction stays.
- Already solved by KNOWN_ALTERNATIVES: NO — the direction is correct; the MECHANISM is broken. Not a kill; a revise.
- CC6 NHA judgment: CHANGE_JUSTIFIED with scoped HOLD on fills → honored (U8: primaries-only v1, defer fills).

## DECIDE
**VERDICT on the current mini-spec (as PROPOSE'd for build): FAIL** — 3 CRITICAL (U1 :3931-LIFT, U2 dwell-keep-anti-restoring/label-provenance) + 7 HIGH accepted. The mini-spec is NOT build-ready.
**(ii) direction = UPHELD** (control-API legal, INVARIANTS intact, Rs+%9 authorized, physics discriminator stands). This is a mechanism-design FAIL, not a kill of the leg.
**Action: return to CP-(ii)-0 → issue mini-spec v2** incorporating U1-U15. Core re-architecture: (a) **kick-and-recover** replacing hold-at-offset (drop outbound+hold, keep only recovery); (b) dwell in ik_move_both-CALL units; (c) **v1 scope = primaries {1,11}** (+{0} only if restructured), fills deferred to v3; (d) {11} at :4481 only with a regrasp_ok guard; (e) affine hull after masking; (f) two-leg/two-sha CPU-primary byte-identity; (g) loud-notify locked-file disclosure; (h) γ⊥-movement pre-registration + wave-1 directional check.
**Process:** v2 → %12 conformance check → **%9 RE-VALIDATE the revised mini-spec** (the current concur is charter-scoped + N1-conditioned; U6) → if the kick-and-recover re-architecture is substantial, a targeted cycle-2 re-review of the changed sections (not a fresh 5-body panel unless warranted) → Rs loud notify (now incl. locked-file disclosure) → CP-(ii)-1 build. rollout prohibited (OG GO 後も別途 Rs GO). band α/β/γ = Rs decision, still blocks only CP-(ii)-5.
Consensus stats: :3931-LIFT = 4/5 bodies + CC1 code; dwell-keep-broken = 3/5 (2 CRIT) + CC1 code; dwell-unrealizable = 4/5; {11}-guard = 3/5; N1/fill-defer = CC3+CC4+CC6 converge. Panel value: the L3 pre-debate caught 3 code-grounded CRITICALs (silent-wrong-teacher + a banked-drop re-introduction) on a locked-file edit BEFORE any build or GPU — the gate functioned exactly as designed.

## Consensus triage (machine section)

### CONFIRMED (5/5 or ≥3 bodies + CC1 code-verified)

#### :3931 is LIFT {3} (charter SKIP), mis-assigned to DESCEND {1}
4 bodies (CC2/CC3/CC5 CRIT, CC4 HIGH) + CC1 code. Disposition U1: delete :3931 + build-time _ph-eligibility assert + full §B re-audit. ACCEPTED CRITICAL.

#### dwell-frame KEEP teaches the FOLLOWING failure; label = achieved ee_pos not commanded target
CC2 CRIT + CC4 CRIT + CC5 HIGH + CC1 code (:287/:333/:412). Disposition U2: drop the held window, keep only recovery; correct label-provenance; my F1 fix formula was wrong. ACCEPTED CRITICAL.

#### dwell=20 control-steps unrealizable (call-atomic) + 10× clock mismatch (cadence=10)
CC2/CC3/CC4/CC5 (4 bodies) + CC1 code. Disposition U3: dwell in ik_move_both-call units, one-clock window, converter assert. ACCEPTED HIGH.

### LIKELY (2-3 bodies)

#### {0} HOVER single-call — worst cell 2.497 has no in-phase recovery teacher
CC2 + CC4 + CC1 code. Disposition U4: {0} not primary; {1} DESCEND is the robust teacher; {0} restructure-or-generalization-only. ACCEPTED HIGH.

#### {11}:4494 can corrupt the Rs-LOCKED regrasp_ok verdict
CC2 + CC3 + CC4 + CC1 code. Disposition U5: {11} at :4481 only + release-before-reach-check guard + on-disk regrasp_ok reproduction assert. ACCEPTED HIGH.

#### %9 N1 unimplemented + concur is charter-scoped
CC3 + CC4 (rederived) + %9. Disposition U6: folds into U8 scope (v1 primaries pre-contact = N1 moot); N1 pre-registered for deferred fills; %9 re-validates v2. ACCEPTED HIGH.

#### Union affine hull contamination by injection excursions
CC5 + CC1 code. Disposition U7: build affine after masking + p2r-specific regression. ACCEPTED HIGH.

#### NHA proportionality — primaries-only v1, defer fills
CC6 + convergent fill-defects. Disposition U8: v1={1,11}(+{0}?), defer {4,5,10,12,13}. ACCEPTED.

### POSSIBLE (1-2 bodies)

#### {10} contact-fragility (largest phase, しごき; not "tiny")
CC4. Disposition U9: deferred; v3 restrict to aerial PRELIFT or gate on cradle/JAM. ACCEPTED.

#### :4255 SEAT_TOPDOWN=1 conditional / None-path two-leg-two-sha byte-identity / loud-notify locked-file disclosure / video claw-zoom / 5mm provenance / validity≠γ⊥
CC2/CC5/CC3/CC4. Dispositions U10-U15. ACCEPTED (mediums; several deferred with fills).
