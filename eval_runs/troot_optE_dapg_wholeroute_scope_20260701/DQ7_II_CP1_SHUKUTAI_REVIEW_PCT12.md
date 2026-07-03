# DQ7 stage-(ii) CP-(ii)-1 — %12 independent 縮退 review = PASS

**Timestamp:** 2026-07-03 13:28 JST
**Reviewer:** %12 RS-TECH-LEAD (independent; on-disk code read via git diff, NOT reusing %11's CHECK/grep outputs — §運用15 independent-tool-verification)
**Subject:** %11 CP-(ii)-1 build (`dq7_ii_cp1_report.md`; 3 files, sha256 route 7f5bc711 / recorder 45d0349e / converter 81cd84aa).
**Gate purpose:** authorize CP-(ii)-2 wave-1 (4 recordings, ~1 GPU-h, abort gate).
**Triggers applied:** §運用15 層3 (mechanical, all changes) + 層5 (3-file + L3 locked-file) + §運用14 (self-check) + records-vs-fact + §運用28 (numeric).

## Verified — 12 load-bearing points (all independent, on-disk)
1. **Hooks at eligible phases ONLY:** `{1}` GRASP_DESCEND `:3975` (loop 8) + `{11}` C2_REGRASP RHOVER `:4557` (loop 10). `grep -c "_inject_detour("` = 3 (1 def + 2 calls). **NO hook on LIFT/GRASP_CLOSE/RDESCEND/SEAT** (grep 0). CRIT U1 (v1 `:3931`=LIFT mis-attribution) RESOLVED; double-guarded by `_PJ_ELIGIBLE=("GRASP_DESCEND","C2_REGRASP")` + `_pj_load_schedule` eligibility assert. ✅
2. **Converter `_mask_injection` command-keyed (%9 C1, verdict-critical):** `keep = ~(kick[step_f] | kick[next_f])` keys on `injection_windows` frame membership (== commanded offset==0), NOT achieved-ee_pos. Drops kick (obs `step_f` in-window) AND anti-restoring-action (target `next_f` in-window) frames; KEEPs recovery (obs off-path achieved / action=script commanded = restoring teacher). Self-consistency assert present. Clean demo `if not wins: return dm` = byte-identity. ✅
3. **affine-after-mask (%9 C2):** `convert_b2` = `_mask_injection(_compute_demo(...))` → union affine built over masked `wp` → {1}/{11} box expands to fit recovery excursions (`amax<=0.95`, expand-not-clip). ✅
4. **Recorder meta-only:** `mark_injection` touches no npz array (only `len(phase_id)` read + append to `_injection_windows` meta list); None-path → `injection_windows=[]`, npz byte-identical. ✅
5. **None-path literal passthrough:** `if _pj_sched is None: return tgl, tgr` = pure-Python identity (no float round-trip) = structural byte-identity. ✅
6. **Markers `[4477,4493,4593]` = the 3 ⛔ANTI-REVERT lines** (grep-confirmed: R argmin cable-X bow / square-on `C2_TILT_SIGN=0` / `regrasp_ok=_at_88 ∧ _R_grips`); shifted down +76/+76/+77 by the insertions above; LOCKED logic byte-untouched (read 4477-4496). ✅
7. **release-margin guard (U5):** `_PJ_RELEASE_MARGIN={"C2_REGRASP":2}` + `call_idx+kc <= loop_len - margin` → final 2 RHOVER calls forced offset=0 → LOCKED `regrasp_ok` computed on clean recovery. ✅
8. **INVARIANTS:** INV#1 single-arm-per-injection (offsets ONE arm; in {11} `_La` [L held] not perturbed, only `_fr` [R]); INV#2 span via span-watch validity filter + N1 (dual-hold Y-span restriction) + release-margin. ✅
9. **py_compile ALL 3 OK** (independent, env7). ✅
10. **sha256sum = %11 report EXACTLY** (7f5bc711/45d0349e/81cd84aa). §運用28 resolved: my initial git-blob sha1 (7c2947dc…) differed by ALGORITHM only; %11 reported sha256sum; both are the same on-disk file. ✅
11. **Empirical byte-identity (2-leg/2-sha, %11) cross-checked structurally:** centred `90808b5d` + full C1→C2 `4eb7234b`, `base_cpu==none_cpu` cmp exact (RHOVER 104× on None-path, all 15 phases); converter no-op on 18 clean demos → `b3472e8c`. Artifacts exist on-disk (`dq7_ii_cp1_byteid/` base_cpu*/none_cpu*/inject_cuda*/none_cuda + smoke_schedule.json). My structural read + %11's empirical cmp = 2 independent modalities. ✅
12. **Consumer-reach (run-the-consumer):** all 15 phases reached + `regrasp_ok=True` (`SUCCESS_R_GRIP_L_CAGE_AT_88`, reach 0.9mm) with a live kick schedule → release-margin guard protected `regrasp_ok`. Records-vs-fact: meta `offset_mm` == applied (single schedule source). ✅

## Minor (§運用28, cosmetic)
Report §1 "+164/−5" = ins+del double-count; git ground truth = **159 insertions / 5 deletions**. No substantive impact.

## Conservatism direction (§運用15)
- **None-path byte-identity = CONSERVATIVE-definite:** structural (code) + empirical (cmp) hard guarantee that the injection is purely additive and cannot corrupt the clean baseline.
- **Consumer-reach = BUILD-integrity check** (the injected path runs end-to-end without breaking the route), NOT the CP-(ii)-5 restoring VERDICT (whether the recovery teaches restoring is answered downstream by wave-1+train+OG gate, non-conservative).

## VERDICT = PASS
→ **go %11 CP-(ii)-2 wave-1** (4 recordings: {0,1}inj×2 / {11}inj×1 / adj-A×1; abort gate) + §運用14 video legs (skill-path) + validity + span-watch → **%12 loud wave gate + %9 independent cross-PV BEFORE the full batch.**
- **Build commit DEFERRED** to post-wave-gate (bundle structural + empirical validation; on-disk files persist meanwhile; 0-commit until then).
- **rollout PROHIBITED** (別途 Rs GO). band=γ affects CP-(ii)-5 only.

— %12 RS-TECH-LEAD 2026-07-03 13:28 JST
