# P3 demo-recorder — 層2/層5 BATCH-FIX report (COORD %11)

**Date:** 2026-07-02 09:05 JST. **Charter:** `charter_recorder_batchfix_coord.txt` (RS-TECH-LEAD %12).
**Adjudication SSOT:** `l2l5_recorder/L2L5_DECIDE.md` (層2 PASS-with-findings / 層5 3/3 PASS; REBUT=0, all findings ACCEPTED).
**Scope:** `route_demo_recorder.py` (rewrite, 227→315 lines, **untracked**) + `test_newton_clip_routing.py` hooks
(**+65 / −3** additive). NO re-record of the shipped canonical npz. 0-commit. INVARIANTS #1-5 + ANTI-REVERT markers untouched.

## Fix-by-finding (every ACCEPTED finding → change → verification)
| Finding | Fix (file) | Verified |
|---|---|---|
| **CC3-F1 / CC2-C3** grip no-match silently unrecorded + counter unconditional + 3rd hardcoded driver copy | `note_grip`: count matched only + `n_grip_unmatched` + warn on no-match (module); construct passes `driver_joints[:2]/[2:]` from SSOT (test:3535) — kills the 3rd hardcode | unit-test T1: matched=2, unmatched=1, warn printed |
| **CC3-F2** `joint_names=[]` (wrong attr `joint_key` + wrong model fk(28) for 74-col arm_q) | construct passes `scene_info["model"].joint_label` (physics, 74) + `joint_names_source` + `arm_q_layout` (test:3540-3543) | newton source (model.py:512 / builder.py:3809) + unit-test T1: 74 names |
| **CC3-F3** torn-frame npz on mid-sample exception (no len assert) | `sample` computes all values into `row` THEN appends atomically (all-or-nothing); `finalize` len-consistency → trim-to-min + `torn_tail` (module) | unit-test T1: 22 keys len==5; T2 disarmed npz still consistent |
| **CC3-F4** sample/note not try-guarded (recorder exception kills route) | `@_guarded` one-shot self-disarm on all 6 public methods → disarm + no-op + route continues (module) | unit-test T2: IndexError → `_armed=False`, route survives, meta `disarmed=True` |
| **CC3-F5** provenance sampled at finalize (14-min 4-pane window) | `_capture_provenance()` at `__init__` (`_prov0`) + re-hash at finalize → `changed_during_run` (module) | unit-test T1: `_prov0` populated at construct, `changed_during_run` present |
| **CC3-F6** no npz integrity marker; non-atomic write | `npz_sha256` in meta + `_atomic_savez` (tmp+`os.replace`) + atomic meta write (module) | unit-test T1: 64-hex npz_sha256, no leftover .tmp |
| **CC2-C1** phase label misalign (TRANSPORT / PRELIFT unlabeled) | 2× `_ph` one-liners: `_ph("GUIDE_PRELIFT")` (test:4232) + `_ph("C2_TRANSPORT")` (test:4535) for future re-records | grep: 15 `_ph` calls (13+2); byte-identical off (guarded helper) |
| **CC2-C2** phase_id=−1 wrap hazard | documented converter-contract (−1 = pre-route settle; never index `phase_names`) — this report + B spec | n/a (doc) |
| **meta** resolved_clip_c2 hardcode + env_gates missing CLIP2 | construct passes env-resolved `resolved_clip_c1_xy`/`c2_xy` (no module hardcode); env_keys += `CLIP2_X`,`CLIP2_Y`,`CUDA_VISIBLE_DEVICES` | unit-test T1: passthrough [0.35,0.15]/[0.40,0.075]; env keys present |
| **meta** ANTI-REVERT marker lines | `_ANTI_REVERT_MARKER_LINES=[4385,4401,4500]` (test:1756) → meta `anti_revert_marker_lines` | unit-test T1 + grep: matches the 3 marker content-lines |
| **CC5-CH1** no scrub artifact; "clean modulo 3" was MANUAL | `p3_dod_evidence/scrub_equality_stdout.sh` — mechanical 3-class scrub + self-report | run on real cpu legs → `STDOUT_EQUALITY=CLEAN` |
| **CC5-INFO5** video-analyst verdict text not preserved | `p3_dod_evidence/video_analyst_verdict.md` | file written |
| **CC4-1** module intent-to-add (empty blob), reports said "untracked" (false); `commit -a` sweep hazard | `git restore --staged` → now genuinely **untracked** (`??`); records corrected; 0-commit maintained | `git status --porcelain` = `??` |
| **CC5-CH4** report hook-table line numbers stale | updated below (finalize/sys.exit + markers) | grep |
| **L5-SSOT §6.4** `/rule-check stage2` unevidenced | Stage 2 checklist generated (ALL PASS) — recorded in the session + summarized below | — |

## DoD (charter DUTY)
| item | verdict |
|---|---|
| `py_compile` both files | ✅ OK |
| ruff check **module** | ✅ **All checks passed** + `ruff format --check` **STABLE** (100% my code) |
| ruff check **test-file** (0 new) | ✅ **140 == 140 legacy baseline** (delta 0; my 3 transient E501 comment-len fixed) |
| module unit-test (F1-F6, GPU-free, no re-record) | ✅ **ALL PASS** (T1 record / T2 self-disarm / T3 idempotent) |
| `DEMO_RECORD=0` byte-identity (static: gating unchanged) | ✅ default `_demo_rec=None` (test:1753) + import-in-gate (test:3532) + 9 `if _demo_rec is not None` guards + `_ph` no-op helper (covers new labels) |
| ANTI-REVERT 3 markers byte-identical | ✅ content unchanged (locked-text count=3); lines shifted +13 → **4385 / 4401 / 4500** |

## Updated line-number table (CC5-CH4; post-batch-fix on-disk)
| hook | pre-fix (CC5-CH4) | **post-fix** |
|---|---|---|
| ANTI-REVERT markers | 4372 / 4388 / 4487 | **4385 / 4401 / 4500** |
| finalize (C2 mid-fn) / its sys.exit | 4756-58 | **4771 / 4772** |
| finalize (fn-tail) / its sys.exit | 5933-35 | **5948** |
| new `_ph` labels | — | GUIDE_PRELIFT **4232**, C2_TRANSPORT **4535** |

## Guarantees / records-vs-fact
- **0-commit**: module untracked (`??`), test-file modified only. No commit created.
- **INVARIANTS #1-5**: untouched (read-only recorder; no control/geometry/solver change).
- **ANTI-REVERT markers**: content byte-identical (Rs-LOCKED text unchanged); only line numbers shifted (+13), reflected in the constant + meta.
- **Banner (test:3334/3816)**: `(CPU)` → `({DEVICE})` — a deliberate records-accuracy fix (charter group 3), independent of `DEMO_RECORD`; route physics unaffected. NOT a byte-identity item (video label only).
- **Shipped canonical npz/meta UNCHANGED** (NO re-record); F2 joint_names + resolved_clip fixes apply to FUTURE records (verified by source + unit-test). The shipped `p3_dod_cuda_demo_raw/route_demo_raw_meta.json` still has `joint_names:[]` — that artifact is frozen by design.
