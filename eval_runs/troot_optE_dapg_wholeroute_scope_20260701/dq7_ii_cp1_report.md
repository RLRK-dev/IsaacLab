# DQ7 stage (ii) CP-(ii)-1 report — build + None-path byte-identity + consumer-reach

**COORD %11 · 2026-07-03 13:19 JST (same-turn date) · 0-commit (commit judgement = %12).** Per Rs GO `DQ7_STAGE_II_RS_GO_20260703.md` (12:11) + charter §8 + mini-spec `dq7_ii_mini_spec_v2.md` (v2.1). Build = kick-and-recover injection (flag-gated `PERTURB_INJECT`, default-off). **STOP here for %12's 縮退 review + go before wave-1 (§8 order).** rollout prohibited (別途 Rs GO).

## §1. Build (3 files, +164/−5, all py_compile OK)
| file | Δ | what |
|---|---|---|
| `route_demo_recorder.py` (NON-locked) | +42 | `mark_injection` + `injection_windows` in **META only** (no npz array added → None-path npz byte-identical); `set_phase`/`finalize` defensive window-close |
| `test_newton_clip_routing.py` (**Rs-LOCKED**) | +83/−5 | module `_pj_load_schedule` (eligibility assert) + `_pj_step` (state machine) + nested `_inject_detour` (None = literal passthrough); hooks at **{1} GRASP_DESCEND `:3975` (call_idx=k, loop 8)** + **{11} C2_REGRASP RHOVER `:4557` (arm=R, loop 10)**; `:4494` RDESCEND **NOT** hooked; release-margin guard (C2 margin=2); markers `[4401,4417,4516]→[4477,4493,4593]` re-synced (grep, byte-untouched) |
| `route_demo_to_bc.py` (NON-locked) | +39 | `_mask_injection` (command-keyed, %9 C1) wired in `convert_b2`; affine-after-mask = %9 C2 automatic |

## §2. None-path byte-identity (2-leg / 2-sha) — PASS
- **Route/recorder, CPU-deterministic primary (2-leg leg 1):** git-stash → HEAD (reverted sha == pre-edit 2e7521ce/d4bf8961/ae2ae591 CONFIRMED) → record `base_cpu*` → pop (restored 7f5bc711/45d0349e/81cd84aa) → `cmp` vs `none_cpu*`:
  - centred config: `base_cpu == none_cpu` **cmp exact** (sha `90808b5d`) — {1} covered.
  - **full C1→C2 config: `base_cpu_full == none_cpu_full` cmp exact (sha `4eb7234b`)** — {1}+{11} covered (RHOVER ran 104× on the None-path; all 15 phases). ⚠ the centred config was non-representative ({11} not reached) → re-ran with the demo's full env (SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.15 S6_ENGAGE_YC=0.15 CLIP2_*) — representativeness gate honored.
- **cuda:0 fingerprint (2-leg leg 2):** `none_cuda`/`none_cuda_full` run clean, injection_windows=[], as_run_sha=edited code (GPU non-det → no sha match expected; runs + windows-empty = the fingerprint).
- **Converter (2-sha leg 2):** `_mask_injection` = byte-identical no-op on **18 real clean b2_cpC demos** (injection_windows=[], tc=770 preserved) → `convert_b2` output `b3472e8c` byte-identical **by construction** (it only wraps `_compute_demo` with an identity-on-clean function).
- **is-identity** unit test (`_inject_detour(None,…)` returns the exact tuples) + **py_compile** all 3 files.

## §3. Consumer-reach (run-the-consumer, end-to-end, full C1→C2 cuda:0) — PASS
`inject_cuda_full` (schedule: {1} DESCEND kick call3 [+12,−6,+8]mm R / {11} C2_REGRASP kick call4 [+15,+10,+6]mm R):
- **hook fires both sites:** DESCEND3 R target = `(0.312,0.038)` = script+offset EXACT, DESCEND4 releases → recovery; recorder stamped **2 windows** (DESCEND [610,660), C2_REGRASP [5195,5255)).
- **route reached all 15 phases**, `regrasp_ok=True` (`SUCCESS_R_GRIP_L_CAGE_AT_88`, reach_resid 0.9mm) → the **release-margin guard protected the LOCKED regrasp_ok** (kick released before the reach-check; verdict identical to a clean run).
- **records-vs-fact:** DESCEND ee_tgt_pos_r X-jump = +12.0mm = meta exact (X constant); C2 X-jump = +16.2mm = meta 15.0 + 1.2mm script RHOVER-step (both legit — C2 target interpolates). The meta `offset_mm` and the applied offset share the single schedule source → cannot diverge.
- **converter consumes it:** `_mask_injection` dropped 13/770 kick control-frames, kept 757 (recovery+normal); %9 C1 command-key holds (no kept frame touches a window).

## §4. 縮退 review
- **edge cases tested:** None-path passthrough (byte-id), clean-demo no-op (byte-id 18 demos), release-margin SKIP guard (unit test + regrasp_ok held live), set_phase/finalize defensive window-close (unit test).
- **lint:** F-category (pyflakes) clean for my additions (the 7 F-errors are pre-existing legacy, e.g. `pad_geoms` `:3655`); my >120-char lines are code+inline-comment (ruff-format doesn't wrap; HEAD already has 114 such lines; repo ruff-check doesn't enforce E501) → **pre-commit-safe, no marker re-shift**. Recommend %12 re-run the `⛔ANTI-REVERT` grep re-sync after `./isaaclab.sh -f` at commit as a defensive check.
- **INVARIANTS:** single-arm-per-injection (INV#1 preserved); markers byte-untouched; DiffIK-only (EE-target detour via `ik_move_both`, no kinematic trick, debate 5/5).

## §5. Not done (gated) / provenance
- **NOT started:** wave-1 recordings (CP-(ii)-2) — awaiting %12 go. band α/β/γ = γ (Rs GO) but affects CP-(ii)-5 only.
- **artifacts:** `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/dq7_ii_cp1_byteid/` (base_cpu/none_cpu/none_cuda + *_full + inject_cuda + inject_cuda_full + smoke_schedule.json). Edited file shas: route 7f5bc711 / recorder 45d0349e / converter 81cd84aa (0-commit, on-disk).
- **next:** %12 縮退 review → go → CP-(ii)-2 wave-1 (4 recs: {0,1}inj×2 / {11}inj×1 / adj-A×1) + §運用14 video legs + validity + span-watch.
