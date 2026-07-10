# Rs 承認 packet — St2 Derived-Source Row Schema (design paper)

**For:** Rs (via %12; presented alongside W0-a′ v1.1). **From:** VT-DESIGN (w2:p5). **Date:** 2026-07-06. **Status:** L3 chain COMPLETE → **v0.3a PASS** (%12 verify 10:04).
**The ask:** Rs 承認 of the St2 design DIRECTION + the **staging decision (Q2)** and the **orientation-escalation (Q5)** below. **Paper only** (0-commit, no runner edit); the BUILD is separately Rs-gated (spec chain → this packet → Rs build-auth → L3 + byte-id re-proof).

---

## 1. Design in one paragraph

St2 makes the C1→C2 route's **runtime-derived targets** (caveat-a / fix-⑤ / F-1a / argmin / pin) expressible as **table rows** instead of hand-authored runner code, so a "make the right hand follow the cable"-class teaching becomes a **row edit**. A row carries a `target_source ∈ {constant, cable-derived, clip-derived}` + a bounded derivation (measure/reduce/transform/gate). It adds **no new motion primitive** and changes **no INVARIANT**; structural leg add/remove and Rs-LOCKED derivation fields stay Rs-専権. Build is staged and Rs-gated; heavier stages deferred.

## 2. Provenance (the L3 process that hardened it)

| Step | Result | File |
|---|---|---|
| draft v0.1 → v0.1a (self-review) → v0.1b (%12 Q1/Q2) | — | `ST2_BUILD_SPEC.md` |
| %10 author-review | **CONCUR / 1 MEDIUM** (branch-completeness folded → v0.2) | — |
| v0.2 → **5-body L3 debate** (CC2-5 + CC6 NHA) | **FAIL** (3 HIGH + ~7 MED + ~5 LOW + NHA-HOLD) — caught defects the single-pass review missed | `ST2_L3_DEBATE_PROPOSE.md`, `ST2_L3_DEBATE_DECIDE.md` |
| %12 independent DECIDE verify | **PASS** (code-confirmed all 3 HIGH + F-3) | — |
| v0.3 (fold Groups A-D) → **targeted re-verify (RV)** | fixes **ADEQUATE**, no new HIGH; 2 MED + 3 LOW folded → v0.3a | `ST2_BUILD_SPEC.md` §9 changelog |
| %12 verify (v0.3a) | **PASS** (10:04) | — |

The 6 independent adversarial agents (5 debate + 1 re-verify) **materially hardened** the spec; the record is in the three files above.

## 3. What the debate changed (honest — the gate worked)

**Validated (no defect):** Q1 (byte-id target `RUN1_REFERENCE_V2 5f1c3f92` unchanged, snap-down offset-gated); the F-1a leaf-complete branch fold; Q2 staging governance; 33/36 cites EXACT; no INVARIANT-field leak.

**Caught + fixed (the debate's value):**
- ⚠ **A build-breaking byte-id error (HIGH):** v0.2 claimed *every* derived source is offset-gated (collapses to a constant on nominal). FALSE for **DS1 (caveat-a) + DS4 (argmin)** — they run **unconditionally**; byte-id holds by **deterministic reproduction**, not offset-collapse. Building them per `gate=offset` would have **failed the byte-id DoD**. Fixed = two-mechanism taxonomy.
- ⚠ **Two Rs-LOCK safety loopholes on DS4 (HIGH×2):** (a) a **second Rs-LOCK** (re-grasp **orientation** `C2_TILT_SIGN=0`, `:4678`) was missing from the binding; (b) the "don't-pin-to-a-constant" tripwire was the **wrong predicate** — editing `reduce` argmin→mean stays "derived" yet re-introduces the air-grip bug. Fixed = dual-Rs-LOCK + per-DS **immutable** derivation-field carve-out.
- ⚠ **A 先祖返り echo (F-3):** a self-review addition inadvertently folded **F-3** (a withdrawn counterproductive deviation, `LEDGER:44`) in as a live primitive. Fixed = excluded + the proof must run `W0E_F3=0` (operationally realized by the FON_V1 pin, %12).
- **Records-fact correction:** F-3's flag is code-default **ON** (I'd relayed "OFF"); re-grounded the determinism basis (the "seed :355-356" was actually video-init). Both fixed.

**Net:** the design DIRECTION is sound and Rs-approvable; the L3 gate converted a plausible-but-flawed v0.2 into a hardened v0.3a. This is the same value the DESIGN_V1 debate delivered.

## 4. Rs decision items

- **Q2 (STAGING — the primary decision):** DESIGN_V1 (Rs-approved) stages **St1b before St2**. St2's runner instrumentation overlaps St1b's → two options, **not pre-decided**:
  - **A — keep St1b→St2 separate** (matches approved staging).
  - **B — St2 absorbs St1b** (single runner-edit arc, 1× byte-id re-proof + a 2-checkpoint bisectability guard). **%12 lean = B.** Choosing B is a **change to the Rs-approved DESIGN_V1 staging** → **Rs decision.**
- **Q5 (orientation-escalation):** DESIGN_V1 §3.1's Rs-approved `orientation` row exposes the C2_REGRASP arm to **tilt-follow with no lock** = a teachable 先祖返り of the `:4678` Rs-LOCK. St2 leaves DESIGN_V1 untouched (Rs-専権) and **flags it**: the C2_REGRASP orientation companion should gain the same `C2_TILT_SIGN=0` inv_binding — **Rs to rule.**
- **Reference only (not a St2 decision):** NEW-1's code-default-ON flip (`W0E_F3`/`W0E_F1A_V2`) is a **separate Rs-batch item on %12's side** (banked `867625e9e1`); the St2 spec only requires the guard, which the official run already satisfies via FON_V1.

## 5. Honest scope (NHA / CC6 — folded)

St2's value is for **FUTURE, genuinely-new (non-reuse) derived sources** — it makes **no existing source cheaper** (all 5 are already built; fix-⑤'s ~1.5h is sunk). The "gate met by 2" counts **built** sources, and DS1/DS2 are the **same template** (≈1 class); the scoping calls the set "nearly closed." So the **St2 BUILD stays DEFERRED** on a genuine new-source trigger — this paper defines the schema so a future new source is a row edit; it does **not** claim the build pays off today. (The fix-⑤-as-row demo is a **fidelity** proof, not a prospective efficiency saving.)

## 6. CC1 recommendation

**Approve the St2 design DIRECTION + schema + governance (dual-Rs-LOCK, immutable carve-outs, INVARIANT gates, F-3 exclusion) as the design.** For **Q2**, %12's lean = **B (absorb)** is well-founded (no standalone St1b trigger; identical instrumentation; 1× re-proof + bisectability guard) — but it is a DESIGN_V1 staging change, so **Rs decides**. For **Q5**, recommend Rs add the C2_REGRASP orientation inv_binding to DESIGN_V1 §3.1 (closes a real teachable 先祖返り). **The BUILD remains deferred + Rs-gated** (per §5 honest scope); build starts only on a genuine new-source trigger + Rs build-auth + L3 + byte-id re-proof.

*VT-DESIGN (w2:p5) — St2 Rs 承認 packet. L3 chain complete; v0.3a PASS.*
