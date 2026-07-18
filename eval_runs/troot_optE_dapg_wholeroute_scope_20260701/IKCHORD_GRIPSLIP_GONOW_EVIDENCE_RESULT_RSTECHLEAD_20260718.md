# #18 GRIP — GO-NOW EVIDENCE RESULT (mechanical P / three-state analysis)

**Author (CC1):** RS-TECH-LEAD (w2:p4). **Stamped:** 2026-07-18 17:49 JST.
**Prereg:** `IKCHORD_GRIPSLIP_GONOW_MEASURE_PREREG_RSTECHLEAD_20260718.md` (v3.1 §B1/B2/B3 + v3.2 §C1/C2; OPS-SUP PASS-CLOSE 17:11 + prior-art PASS-CLOSE/run-OPEN 17:25).
**Harness:** `gonow_measure.py` commit `78d2b94c0c` (on-disk sha256 `de44d4a14dce…`; git-clean). **Run:** v3.2 fail-closed block M1→M2→M2b→M3, one pass, 17:31–17:41 JST, `CUDA_VISIBLE_DEVICES=0` cuda:0 (A6000). **All four legs rc=0, `status=COMPLETE`, `source_integrity_ok=True`** (⊇ device_provenance_ok). Raw: `gonow_evidence_20260718/{m1_b4shadow_ikchord, m2_ff_pin_shadow, m2b_ff_shadow_nopin, m3_ikchord_natterm}/{summary_*,per_step_*,COMPLETE.ok}` + `run_*.log`; analysis = `gonow_evidence_20260718/analyze_v32.py`.

## Per-leg (evidence-grade)

| leg | drive | pin | g3 | shadow first-fire | drop | cause | term_cause_set |
|---|---|---|---|---|---|---|---|
| **M1** b4shadow | ik_chord | ON | **false** | **None (=0)** | 267 | A_held_z_floor | {A_held_z_floor} |
| **M2** ff_pin | feedforward | ON | 242 | **246** | 347 | B_contact_loss | **{B_contact_loss}** |
| **M2b** ff_nopin | feedforward | off | 242 | 246 | 342 | **C_c1_escape** | **{C_c1_escape}** |
| **M3** natterm | ik_chord | off | false | — (no shadow) | 267 | A_held_z_floor | {A_held_z_floor} |

(All done_reward = −10.0. M2 shadow max_dwell=985, shadow_fire_before_drop=True; M2b shadow max_dwell=504.)

## Mechanical gates (from `analyze_v32.py`)

- **B1 causal boundary:** `f := M2.shadow.first_shadow_fire_step = 246` → frozen expectation `f==246` **PASS**.
- **B1 pre-fire trace equality [0, f−1]=[0,245]:** all 246 rows present in both legs; **0 / 246 divergent steps** over `{contact_r, contact_l, held_z_minus_rest, dx_c1, g_latched, held_i, grasped, contact_loss_count}` → **bitwise-equal** = clean physics isolation before the pin fires.
- **Config diff-set (M2 vs M2b):** `{route_c1_pin_effective}` only (subset of the registered `{route_c1_pin_effective, pin_seat_seg}` "only/any-other-diff" bar; **`pin_seat_seg=27` identical in ALL legs** — it is the C1-seat constant, not a pin-arming effect; `cable_z_rest`, `Z_FIRE_DEPTH_M`, substeps, recording sha all equal). → **subset_ok = True** (a *tighter* one-variable isolation than registered).
- **Run-independent provenance equality (M2 vs M2b):** `harness_self_sha256_post`, `source_closure_run_end`, `recording_sha256`, `venv_python` all equal; `changed/missing/added_during_drive/build_added_unstable == []` on both. → **equal = True**.
- **P (common validity predicate) = True** (both COMPLETE+integrity ∧ prov-equal ∧ cfg-subset ∧ f==246 ∧ trace-equal ∧ all rows present). **The experiment is VALID.**

## THREE-STATE VERDICT = **INCONCLUSIVE**

- M2 clean-B in [f,347] = **True** (term_cause_set={B_contact_loss}, done 347 ∈ [246,347]).
- M2b clean-B in [f,347] = **False** (term_cause_set={C_c1_escape} ≠ {B}).
- M2b no-terminal-through-347 = **False** (M2b terminates @342 ≤ 347).
- ⇒ **PIN-ASSOCIATED = False** (requires M2b to have NO terminal through 347) **∧ BRANCH-INTRINSIC = False** (requires M2b clean-B) ⇒ **INCONCLUSIVE**.

**INCONCLUSIVE rests on the SUBSTANTIVE reason** (not a provenance/validity artifact — P holds): M2b (FF, no-pin) terminates by **C_c1_escape@342**, an *other cause*. This is the diagnostic-predicted outcome (`gonow_20260718/ff_nopin_wholeroute` C_c1_escape@342), now confirmed on evidence-grade data. Non-binding expectation → **confirmed**.

## Substantive findings (beyond the narrow attribution)

1. **Necessity (CC6 / B4) = DISCHARGED (evidence-grade).** M1 (ik_chord+pin): `g3=false` ∧ shadow-fire=**0** ⇒ the (d-b) C1 pin **never fires before the ik_chord drop@267** ⇒ it **cannot moot the #18 grip fix**. (Positive control: M2's FF drive fires the same detector @246, max_dwell 985 — the detector *can* come out non-zero, so M1's zero is real, not a dead probe.) The recorded-branch IK seed fix (design v2.0) **remains necessary**.
2. **Coverage (CC2 CH-1) = the recorded FF branch does NOT hold C1 whole-route, pin or no-pin.** FF-no-pin escapes C1 (`C_c1_escape@342`); FF-pin welds C1 (prevents the escape) but then loses grip (`B_contact_loss@347`). Neither reaches C2_REGRASP (~step 500) / G6. The pin **changes the failure MODE (C→B) and delays it (342→347) but does not prevent the drop.** → a coverage concern for p5 (bears on whole-route fix efficacy = B5b post-impl, and possibly the (d-b) pin design).
3. **Attribution (pin-vs-branch) = INCONCLUSIVE** — the binary does not resolve because M2b fails by a *third* mode (C1 escape); the pin is neither cleanly "the cause of the drop" nor "irrelevant" — it alters the failure. Non-binding, as pre-registered.
4. **B5a reachability (M3) = BLOCKED_BY_PRE_C2_DROP.** ik_chord (no-pin) drops `A_held_z_floor@267` — cannot reach C2_REGRASP pre-fix (so B5b whole-route ik_chord is post-impl only).

## Records notes (transparency)

- **Config diff-set (prereg vs actual):** prereg v3.1/v3.2 registered `{route_c1_pin_effective, pin_seat_seg}`; the actual diff is `{route_c1_pin_effective}` (pin_seat_seg=27 constant). The registered bar is "only / any other diff → INCONCLUSIVE" (**subset** semantics) → satisfied. Not a mis-run; a tighter-than-expected isolation. (The v3.1 analysis note that the diff-set *would* be {route_c1_pin_effective, pin_seat_seg} was a conservative over-estimate; the seat index is recording-derived, shared by the real pin and the shadow.)
- **Harness sha:** on-disk `de44d4a14dce37cedf93e9582dffab7f5d2dd19df0bb7d9164ec34813809a732`; prereg abbreviations use `de44d4a1…` (the 8-char pin + commit `78d2b94c` are authoritative and match; the prereg's one full-string spelling dropped a `4` — cosmetic, superseded by the commit pin).

## Disposition

- **Deliver to OPS-SUP (pN):** rc0-set + raw evidence + this mechanical analysis (per the run-OPEN directive). Necessity DISCHARGED; verdict INCONCLUSIVE (substantive); coverage finding surfaced.
- **Escalate to p5 (design):** the coverage finding (FF branch does not hold C1 whole-route, pin or no-pin; pin changes the failure mode) — bears on the v2.0 fix's whole-route efficacy and the (d-b) pin design.
- **Unchanged authorization:** B6-char / B5b / impl / training remain **UNAUTHORIZED**; execution HOLD; training-ready LOCKED; WMSO untouched (released to pQ). The next design step (B6-char auth → re-debate v2.1) is p5/Rs-gated, not opened by this run.

## Visual leg (motion-bearing-sim rule — OMITTED-WITH-REASON, loud)

Per CLAUDE.md "motion-bearing sim RESULT は視覚レグ必須（mandatory-or-justified）", this record carries a route/grip motion, so the visual-leg disposition is recorded here:
- **Omitted for THIS record.** The gonow harness is a **read-only numeric drop-metric measurement** (mirrors `_compute_rewards_dones_batch` :1653-1660 per physics frame); it **renders no video**. The load-bearing claims are **mechanical/numeric** — shadow-fire count (necessity), terminal `done_step` + `term_cause_set` (attribution), pre-fire trace equality — all verifiable from the banked `per_step_*.json`. **No physical-validity success is claimed** (verdict = INCONCLUSIVE; necessity = a zero count).
- **Deferred visual requirement (flagged):** the **drop-mode** claims (M2b `C_c1_escape@342` vs M2 `B_contact_loss@347`; "FF branch does not hold C1 whole-route") are physical and, **if the coverage finding is escalated to a design decision** (p5), a **video leg on the FF drop modes** (skill-path `/verify-run` or `/video-analyzer` + `video-analyst`, Rs human-GT for physical validity) is required before that decision — per the motion-bearing rule + Rs video-at-milestones directive. Not produced now because no design decision is opened by this diagnostic (all downstream steps remain UNAUTHORIZED).
