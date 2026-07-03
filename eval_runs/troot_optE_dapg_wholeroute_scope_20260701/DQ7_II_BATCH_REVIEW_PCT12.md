# DQ7 stage-(ii) batch deliverable — %12 RS-TECH-LEAD review + 3 decisions

**%12 · 2026-07-03 15:58 JST.** Reviews `dq7_ii_batch_deliverable.md` (%11, 15:44). Independent verification per §運用15 層3 + §運用28. 0-commit build → committed here as a governance checkpoint (local, NOT pushed). rollout PROHIBITED unchanged. band=γ affects CP-(ii)-5 only.

---

## Decision 1 — W0 converter naming fix = **APPROVE** (+ commit)

**Independent verification (%12, not %11's report):**

| Check | Method | Result |
|---|---|---|
| tier-1 wired (NOT ABSENT-IN-CODE) | grep `CABLE_XY_OFFSET` all `.py`/`.sh` | `test_newton_clip_routing.py:6679-6683` passes env `"dx,dy"[m]` → `build_scene(cable_xy_offset=...)` = the **sim's real** cable-IC rigid offset. The recorder writes the **SAME env var** to meta → **meta cannot silently lie about the offset** (sim + recorder read one variable). tier-1 = genuinely authoritative, not theater. |
| 3-tier logic (`_offset_from_meta`) | read diff `route_demo_to_bc.py:551-568` | meta `env_gates.CABLE_XY_OFFSET` (m→mm `int(round(dx*1000))`) → legacy dir `rec_<x>_<y>` → (0,0). Correct; dir basename stays the per-recording identity (no `rec_0_0` collision on same-IC recs). |
| clean-demo byte-identity | `sha256sum` baseline_repro vs patched_repro | `bc_dataset_abs.npz`=**b3472e8c** / `_val.npz`=**0ed5149c** / `_meta.json`=**2396da23** — **baseline == patched EXACT**. W0 does NOT alter the clean rec_<x>_<y> build path. |
| recorder None-path npz byte-id | `sha256sum none_cpu_full_w0/route_demo_raw.npz` | **4eb7234b** == CP-1 baseline `4eb7234b` EXACT. env_keys is meta-only; npz untouched. |
| build-file drift | `sha256` vs deliverable claims | to_bc=`d2fbca1b` ✓ / recorder=`bd5457f3` ✓ / test_newton=`7f5bc711` (== CP-1 review, unchanged) ✓. py_compile ALL OK. |

**Caveat re-adjudicated (%11 flagged "reduced fail-loudness"):** LOW-RISK, not blocking. A silent (0,0) fallback only fires when the cable was **genuinely** at (0,0): the sim offsets the cable ONLY via `CABLE_XY_OFFSET`, and the recorder records that SAME variable, so "meta missing the key" ⟺ "the env var was unset" ⟺ "the sim applied no offset" — the resolved (0,0) is then CORRECT, not a poisoning. The only unreachable failure mode (real offset + free-form name + no meta key) does not occur in the batch flow (batch recs get the meta key; legacy recs have rec_<x>_<y> names). **Optional defense-in-depth (non-blocking follow-up):** a loud `print` on the tier-3 free-form (0,0) path would convert operator-error into a visible audit line (byte-identity-preserving).

**→ APPROVE. Committed (build checkpoint, local, no push).**

---

## Decision 2 — {11}(a) VOLUME-vs-MECHANISM = **MECHANISM** → {11} EXCLUDE from batch + escalate

**§運用28 reconciliation (%12 read `w1a_n2/w1_discriminator_n2_results.json` directly):**

| metric | file value | deliverable claim | match |
|---|---|---|---|
| RHOVER kick-region d_ee (n=2, M2'−M1) | +0.003387 | +0.00339 | ✓ |
| RHOVER seg (m1→m2') | 0.28107 → 0.23229 (down) | 0.281→0.232 down | ✓ |
| ±10mm RHOVER d_ee | +0.004484 | +0.0045 | ✓ |
| probeB all-demo (n=1053) RHOVER d_ee | +0.003313 | +0.0033 | ✓ |
| recovery-band (n=36) d_ee | +0.001797 | +0.0018 | ✓ |

**Verdict (P2 SIGN rule):** own-region d_ee is wrong-signed and moved MORE positive n=1→n=2 (+0.00255→+0.00339) — **no negative flip → MECHANISM** (not volume). P3: BOTH kick directions (c11 [12,9,−5] + c11b [−10,−8,6]) fail → direction-independent. P1: {11}@2 recovery-rows (≈60-72) ≥ {1}@2 (45) → NOT a recovery-row deficit (partially refutes the "short recovery" pathology). Positive control {1} γ⊥ −0.20/−0.40 = probe detects real restoring. **Clean MECHANISM separation.** ({1}+adjA is W1-independent → proceeds.)

---

## Decision 3 — {11} redesign = **ESCALATE to Rs** (Rs専権; generative-design OPTIONS)

The {11} C2_REGRASP kick-and-recover does not teach the intended signal. **Sharper framing than "the kick is broken":** the banked B2 evidence shows the {11} gap is a **cable-FOLLOWING/tracking deficiency** (CP-E OG pair seg-follow **0.282** ≪ band [0.8,1.2]; og_bprime closed-loop contraction **diverges** 5.0→5.525mm), while kick-and-recover teaches off-path **RESTORING to a path** — these may be **MISMATCHED**. Grounded in memory `reference-og-gate-moving-target-gamma-perp-wrong-sign`: the {11} RHOVER target is cable-anchored + MOVING (`_fr`→`_hovR`), so its correct behavior is following (paired seg∈[0.8,1.2] ∧ ee-only≤0.3), NOT γ⊥≤0.5 restoring.

**%12+%9 CONCUR** (%9 §運用28 independent re-extract: d_ee +0.003387/n56, **+0.003313/n1053 high-power**, +0.004484/10mm — no sign-flip; doc `DQ7_II_11_MECHANISM_CROSSPV_PCT9.md`). %9 sharpens the framing: the "mechanism does not teach ee-restoring at {11}" is a **data-confirmed FACT**; the *reason* (following≠restoring) is a **leading HYPOTHESIS** → OPTION B *tests* it (not proven). %9 rejects the alternatives: probe-blind (positive control {1} healthy) / metric-unreachable (**NO** — a good following policy CAN reach the {11} pair band ⇒ metric healthy, a MECHANISM mismatch, distinct from a §7-band or {2,3} un-injectability issue) / hook-bug (regrasp_ok=True + video clean).

**OPTIONS for Rs (generative-design; I do NOT method-swap — FOUNDATIONAL-INVARIANT discipline):**
- **B (FIRST-GATE — must precede A/C/D, which all assume a teachable restoring gap):** two checks:
  - **B0 obs-sufficiency (§運用21, %9-added):** is the {11} following-target IN the obs? FACT (%12 grep): the {11}/C2_REGRASP obs seg_pos = **argmin-to-C2** segment (`_seg_rule` route_demo_to_bc.py:128, recomputed per-frame from cable_xyz) — so NOT trivially blind (a C2-region segment IS present). OPEN: is argmin-to-C2 the *correct* following-target for the re-grasp approach, or does the R arm need a target the obs doesn't isolate? If obs-insufficient → the fix is an **obs change, NOT a teacher redesign** (no teacher fixes an unobservable target; consistent with B2 diversity ALSO failing to move seg 0.282).
  - **B1 following-vs-restoring:** if obs is sufficient, is the gap *following* (→ correct-following is already the band=γ target, **drop the {11} kick**) or *restoring* (→ A)?
- **A (redesign IF a teachable restoring gap survives B):** HOLD-recover at a FIXED-target {11} sub-phase (not the moving `_fr`→`_hovR`) → clean restoring label. Does NOT touch release-margin/`regrasp_ok`.
- **C (Rs-only, last resort):** relax release-margin → touches **LOCKED `regrasp_ok`** (reach+grip verdict) + breaks the v2 §D guard = design-gate = Rs専権. Not proposed.
- **D (alternative):** inject at a different {11} sub-phase (RDESCEND/pre-approach).

**Recommendation (%12+%9):** Rs run **B first** (B0 obs-sufficiency THEN B1 following-vs-restoring). A/C/D only if a teachable restoring gap survives B. C is off-limits absent Rs's invariant call.

**%9 notes (integrated):** (1) frame CP-(ii)-5 as "**{1} achieved + {11} pending-redesign**", NOT a full-GO attempt ({11}-excluded ⇒ the batch never reaches injectable-only full GO; bankable = {1} restoring at scale). (2) **adjA (on-path dense diversity = a following-type teacher) is a cheap probe for B0/B1** — if adjA moves seg-follow → dense following works; if not → reinforces the obs-blindness reading. (3) {11} ≠ gate-reachability (distinct from the un-injectable {2,3}/{0}).

---

## 3 answers to %11
1. **W0:** APPROVE — committed (build checkpoint, local, no push). Optional tier-3 audit-print = non-blocking follow-up.
2. **Batch size/allocation:** {1} = **12** (diverse CP-C-survivor IC × diverse [2,20]mm kick dirs, **direction-BALANCED** ±/axis so restoring generalizes, Z-comp≥0, 1 inj/rec, R_MISS(−8,+8) excluded) + adjA = **8** (distinct 5mm-grid reach-screened, no byte-dup). {11} EXCLUDED. Ensure the batch wrapper exports `CABLE_XY_OFFSET=<dx>,<dy>` per recording (tier-1 live). CP-(ii)-5 OG gate (band=γ) is the checkpoint — if under-taught, ASSESS (do not auto-add).
3. **{11} → Rs:** ESCALATED (above). {1}+adjA batch PROCEEDS in parallel (independent, within the existing 12:11 GPU GO); the {1}+adjA OG-gate result + this {11} escalation go to Rs together.

**Scope reminder:** batch → convert → BC-train (CP-(ii)-4) → OG-gate (CP-(ii)-5) is within the approved envelope. RL/DAPG **rollout PROHIBITED until fresh Rs GO** (even after OG GO).
