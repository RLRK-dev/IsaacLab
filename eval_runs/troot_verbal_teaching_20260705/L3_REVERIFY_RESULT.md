# L3 targeted re-verification — RESULT (VT-DESIGN / CC1)

**Subject:** `DESIGN_V1.md` v1.3 (post-debate revision). **Date:** 2026-07-06. **Approved by %12** 02:49/02:57.
**Scope:** focused pass on the CRITICAL + 6 HIGH-changed sections (RV1 fix-adequacy + regression; RV2 adversarial-on-new-mechanisms).

## Tallies

| Agent | result |
|---|---|
| RV1 (fix-adequacy) | **7 of 7 CRIT+HIGH fully RESOLVED**; 0 new CRIT, 0 new HIGH, 2 new MED; all 4 MED spot-checks RESOLVED; 6 citation fixes VERIFIED EXACT |
| RV2 (adversarial) | 0 CRIT, **2 HIGH**, 4 MED, 1 LOW (on the NEW v1.3 mechanisms); confirmed the CRITICAL class-A restriction is code-correct, launch-wrapper reaches R3, evidence-gate NOT circular |

## Part 1 — the FAIL-triggers (debate CRIT + 6 HIGH): RESOLVED

RV1 grep-verified each; RV2 code-confirmed the CRITICAL. class-A = `{F-1b, F-2, F-1a-v1}` matches `CHARTER_V1.md:15` exactly, F-1a-v2 (`:4245/4254/4268` = real leg-adding) + F-3 excluded; class-B freeze provisional + Rs key + LEDGER; §4.4 table→run gate present; `emits_legs` + primitive audit; "structurally impossible" → "detected+rejected"; evidence-gate + St1b/2/3 defer; 6 citations EXACT. **The design's core hardening PASSED.**

## Part 2 — 2nd-pass NEW issues (from the v1.3 rework) — §運用15 → %12/Rs

| # | New issue | Agent(s) | Sev | Verdict | Fix |
|---|---|---|---|---|---|
| N1 | §4.4 all-primitive tokens require editing the LOCKED runner (grip/settle/pin print nothing today) = **St1b, not St1a**; so at St1a the table→run gate is blind to a moved/added **pin** (INV#5 sole exception) | RV1(MED)+RV2(HIGH) converge | **HIGH** | ACCEPT | re-stage §4.4#1/#2 to St1b (L3+Rs auth); scope St1a's table→run gate to `ik_move_both` legs; state grip/settle/pin visibility DEFERRED to St1b; correct §5 DoD-2 + §9 |
| N2 | table→run gate SET/"union" semantics are multiplicity-blind (`route_leg_diff.py:25` normalizes `k/N`) → cannot catch the `N_ROUTE`/`LIFT_SUBSTEPS` sub-leg-count change §3.1 calls THE deviation | RV2 | **HIGH** | ACCEPT | specify ORDERED-MULTISET / sequence equality (preserve order + multiplicity), NOT set-union; fix §4.4#3 + §4.2-5a |
| N3 | "class-A amplitude" mislabels `speed_factor`/`n_steps` — a within-leg speed change to NOMINAL is byte-affecting = class-B; AND St1a's 4 params already have runner env-overrides → **St1a marginal ROI over DoD-0 ≈ 0** (St1a = table-SSOT organization, not a new edit capability) | RV1(MED)+RV2(MED) converge | MED | ACCEPT | rename §3.1 axis "non-structural"; within-leg amplitude on nominal = class-B; §7 D-1(a) relabel "scene/global param-edit"; state St1a's value = organization, require D-1(b) to show a gap beyond existing env-override |
| N4 | reachability "pre-check" (§4.2-3) uses RUN-TIME signals (`n_steps`/clamp/residual `:4090`/device-fragile wall) → cannot pre-gate; it is a post-run catch | RV2 | MED | ACCEPT | step-3 = STATIC `/geometric-design` envelope only (note it can't pre-detect the device wall); add a step-5 post-run reachability catch; reconcile "steps 2-5 mechanical" wording |
| N5 | "full nominal env = ~19 vars" not enumerated (runner has 86 `os.environ.get`) → byte-id "trivial" asserted, not established | RV2 | MED | ACCEPT (build-time) | enumerate the EXACT nominal env set (grep every nominal-path `os.environ.get`+default; list vars whose `RUN1_REFERENCE_V2` value ≠ default); make St1a byte-id contingent on that list |
| N6 | provisional class-B freeze = a LABEL with no artifact-quarantine (step-5 regenerates the npz before Rs step-6 → pre-Rs consumption possible in the 4-pane env); "Rs key" yields no verifiable artifact | RV2 | MED | ACCEPT | stage step-5 artifacts in a NON-canonical path until Rs step-6; LEDGER:44 Rs-auth annotation must CITE Rs verbatim + timestamp (§運用15c) |
| N7 | class-B honesty-note softener "(shown to Rs before 81-cell use)" is unsupported by `RUN1_REFERENCE_V2` (records Rs-directed CHANGES + CC-key freeze, NOT an Rs re-declaration of the frozen ref) | RV2 | LOW | ACCEPT | drop the softener (records-must-match-fact); the core caveat is correct + sufficient without it |

**Nature of the new issues:** all 7 are BOUNDED text/spec/staging fixes with exact fixes given; **none reopens the CRITICAL or breaks a governance gate**; several (N1 §4.4→St1b, N3 St1a ROI≈0) **further honest-scope St1a**, consistent with the debate's NHA HOLD direction (St1a minimal, defer heavier).

## §運用15 disposition

2nd verification pass surfaced 2 NEW HIGH → per §運用15 ("2回目の検証で新たな問題が出たら報告して判断を仰ぐ"), surfaced to %12 (→Rs); NOT auto-iterated.

**CC1 recommendation (for %12/Rs judgment):** one FINAL bounded v1.4 folding N1/N2/N7 (claim-correctness: §4.4→St1b staging, multiset gate semantics, drop the softener) + N3/N4 (recommendation honesty: St1a ROI≈0 + reachability post-run); record N5/N6 as explicit **build-time spec items** (exact env enumeration; freeze-quarantine mechanism — naturally impl-level). Then PASS → Rs 設計承認 packet. This is bounded (fixes enumerated; CRITICAL/core stable) — NOT an open loop. Alternative: PASS v1.3 now with all 7 recorded as build-time items (the design DIRECTION + gating are validated; N1-N7 are precision/staging). %12/Rs to choose.

*VT-DESIGN (w2:p5) — L3 re-verify: FAIL-triggers RESOLVED; 2 new HIGH (bounded) → §運用15 to %12/Rs.*
