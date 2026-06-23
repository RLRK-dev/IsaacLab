# L1.X Substrate real-fidelity — B-SIM CONSOLIDATION VERDICT (substrate MEETS the foundation-rigor bar)

**Node:** T-ROOT-optE-L1.X-Substrate-real-fidelity (P0-KILL #1, reinterpreted).
**Scope:** B-SIM (in-sim physics-realism verify), Rs-ratified 2026-06-23. (B-REAL = calibrate-to-real-cable is hardware-BLOCKED, documented below.)
**By:** %9 RS-TECH-LEAD; %2 OPS-SUP cross-PV (foundation-rigor reframe + B2/B1 refinements folded).
**Mode:** consolidation of ALREADY-BANKED evidence — **0 new GPU run** (no-repeat gate V7/V10).
**Status:** SUBSTRATE **MEETS the foundation-rigor bar** → SUFFICIENT to advance. (Justification = foundation-rigor MET, NOT "rough-OK lets us skip" — SOMA:108/:18-23/:57: rough/imperfect latitude does NOT extend to the foundation.)

---

## 0. Rs-ratified reinterpretation of P0-KILL #1 (2026-06-23)

"Substrate physical-realism FIRST — the 0.332 figure rests on a 10–30×-too-soft substrate"
(`troot_p0:27,104-108`) was framed as "stiffen the too-soft cable." That premise is **inverted/stale**:

- "10–30× too soft (`CABLE_BEND_STIFFNESS=0.1`)" was **stale-on-write** — env6 was already `1.0` at P0 time (`troot_r0:42-56`).
- Current env7 working-tree **EI=0.005** (`task_config.py:144`) is **inside** the validated window **1e-3…5e-2 N·m² (median ~1e-2)** for an 8 mm flexible cable (`Cable-Bending-Stiffness-EI-8mm.md:14,74,104`, 3 methods + IEC, HIGH conf). The old `1.0` was **20–1000× too STIFF** (`Cable-EI:15,95`).
- P0-KILL feasibility is **stiffness-INSENSITIVE** anyway (`troot_r0:111-118`).

**Ratified reinterpretation:** substrate real-fidelity = **contact-fidelity + solver-NaN separation + drape**, NOT "stiffen the cable." (Rs ratify 2026-06-23; %9 5体 debate + %2 cross-PV.)

---

## 1. Consolidated banked evidence (cite — nothing re-run)

| realism axis | banked finding | foundation-rigor status | source |
|---|---|---|---|
| **cable-bend EI** | EI=0.005 **in the physical window** (1e-3..5e-2); CPU-stable; **NOT the NaN root** (rigid 1.0 WORSE: 0/3 vs floppy 4/9) | ✅ physically-defensible value | `Cable-EI:74,104`; `R_S66_GPU_STABILITY_CHECK_RESULT.md:21-22,46` |
| **drape (discrete-vs-continuum)** | %3 **AUDIT-PASS**: drape monotonic / anchored / droops-past-edge / **no penetration**, §運用14 self-checked; discrete-vs-continuum analytic compared; EI=0.005 in {0.01,0.005,0.003} all stable + rendered for the human VISUAL pick | ✅ gate-reviewed (independent %3) | `R_S71_CABLE_DRAPE_AUDIT_03.md:3,28-29,44` |
| **settle-stability** | env7 GPU free-cable settle = **non-det NaN, EI-independent** (#562); **CPU = reliable 3/3**; njmax not the fix | ✅ characterized; CPU = the physically-valid path | `R_S66_GPU_STABILITY_CHECK_RESULT.md:8,34,40-43`; `r_s66_cg_vs_newton_N10.log` |
| **solver-NaN #1415** | contact-rich GRASP: `newton` 0/30 vs `cg` **30/30 finite**, cg penetration-FAITHFUL (%2 `mj_geomDistance`, −0.661mm shallower-not-softer); extends through close+lift (30/30) | ✅ a REAL stiff contact (not a trick); NaN = solver limit, cg-fixed | `R_S66_VERDICT_cg_fixes_1415_on_ko_20260623.md`; `R_S66_CG_LIFT_CROSSPV_OPSSUP.md` |
| **contact-model (PAD_SOLREF) — B1 light gate-review** | `MUJOCO_PAD_SOLREF=(-65789,-2105.3)` = MuJoCo **direct (stiffness,damping)** form (documented, not a bypass); bench-calibrated (`s5_calib_bench3r`, force datum 37.1N@q=0.7407); deliberately avoids the positive-form ghost-contact softening (`task_config:193`); behaviorally real-grip-not-crush (penetration cross-PV −1.06/−1.39mm @14-17N); bench JSON re-read (R6_F00/F044/F22 creep 134.86→~57µm/f, collapse=0 while other forms collapsed) | ✅ **DEFENSIBLE — BANKED** (%2 formal cross-PV CONFIRM 2026-06-23); ⚠ bench-strong / chain-via-R4-fallback (rev8 chain validated R4, not active R6 → validate R6 at next full-chain); ⊥ #1415 GPU-NaN (cg-mitigated, separate) — defensible-model ≠ GPU-NaN-free | `task_config.py:162-165,187-194`; `s5_calib_bench3r_result.json` R6_F00/F044/F22; penetration cross-PV (`reference-mj-geomdistance-penetration-crosspv`) |
| **CC4/%2 "0.005 special NaN driver" HIGH** | **REFUTED** — env6 0.3→NaN is VBD-scoped; on env7 lower-EI is relatively BETTER | — | `R_S66_GPU_STABILITY_CHECK_RESULT.md:46`; `Cable-EI:97` |

**Net (foundation-rigor basis):** the substrate is physically-valid + gate-reviewed across every axis — cable
EI in-window, drape AUDIT-PASS, contacts are REAL (no kinematic-trick / physics-bypass), the contact-model
param is defensible, and the GPU NaN is a solver limit (cg-fixed) not a realism defect. The substrate
**MEETS the foundation-rigor bar** (SOMA:108) — that, not rough-OK latitude, is the sufficiency basis.

---

## 2. Pending-gaps (labeled non-conservative — documented, NOT built; GROVE §2.2)

1. **real-hardware DER / drape calibration** — `Cable-EI:109-112`. **BLOCKED**: no hardware (`LEDGER:49`; `SOMA:13-14,50-56`). In-sim values are "calibrated-to-physics-estimate, real-pending-hardware." Reopens only on a future real-world directive.
2. **GPU mjw fix / HELD-RATE** — `cg` is a screening-bar #1415 candidate; production NaN-rate (N≥30, GPU #562) + general GPU free-settle non-det remain → upstream Newton/mujoco_warp robustness (`R_S66_GPU_STABILITY_CHECK_RESULT.md:42`); no THREAD source change indicated. CPU = the safe path.
3. **contact-model real-fidelity + chain-evidence (B1 caveats a/b, %2 cross-PV)** — (b) PAD_SOLREF is bench-calibrated against SIM physical-targets (creep/collapse/clearance), NOT real-hardware contact stiffness → absolute magnitude uncalibrated (same no-hardware limit as EI; document alongside real-DER). (a) the active R6 direct form is bench + 1 S5b run; the rev8 CHAIN validated the R4 positive fallback, not R6 → validate R6 at the next full-chain run (else chain-evidence is inherited-from-fallback). NON-blocking. Overdamping is jitter-conservative.
4. **F-B analytic re-derive (optional, non-blocking)** — %3 drape audit's analytic used L≈0.30 m vs true overhang ≈0.19 m (`R_S71_CABLE_DRAPE_AUDIT_03.md:F-B`); does NOT touch the visual-pick or stability/window facts; treat the EI pick as VISUAL. Optional cheap cleanup.

---

## 3. Verdict

**SUBSTRATE-REALISM MEETS the foundation-rigor bar → SUFFICIENT to advance.**
Justified on FOUNDATION-RIGOR (physically-valid + gate-reviewed + no-trick), NOT on rough-OK latitude
(which SOMA:108/:18-23/:57 forbid extending to the foundation). The four pending-gaps are explicitly
non-conservative / deferred (real-DER hardware-blocked; GPU-fix upstream; magnitude + F-B optional).

**Recommend: advance to the forward capability work** — route/hook + full-route retention on CPU (the
production-pending increment, `SOMA.md:80`, partly banked CPU `r_s71_clip_dropin_72.py` «成功»); perception.

**No-repeat note:** this verdict consolidates banked evidence; it re-runs nothing (V7/V10). The reuse/no-repeat
inventory (incl. the %3 drape audit + the R_S66 settle/EI/cg docs) was completed BEFORE this consolidation
(lesson `feedback-inventory-existing-results-before-designing-experiments`, 2026-06-23).
