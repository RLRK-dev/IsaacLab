# DQ7 stage (ii) mini-spec **v2** — kick-and-recover injection hooks (CP-(ii)-0, post-debate re-architecture)

**COORD %11 · 2026-07-03 09:55 JST (same-turn date) · 0-commit, 0-GPU, locked-UNTOUCHED (design only).**
**SUPERSEDES `dq7_ii_mini_spec.md` (v1 = debate FAIL: 3 CRITICAL + 7 HIGH; (ii) direction UPHELD = mechanism-design gap, not a leg kill).** v1 kept on disk for provenance. Authoritative source = `DQ7_II_MINISPEC_DEBATE_DECIDE.md` (U1-U15 + core re-architecture, full-read + code-verified below). Per `charter_dq7_stage_ii_coord.txt` §8. Build (CP-(ii)-1) starts only after **%12 conformance → %9 RE-VALIDATE (v1 concur was charter-scoped + N1-conditioned, U6) → Rs loud notify (locked-file disclosure) → build**. This doc edits NO code.

**Grounding (self-read THIS session, direct-cited — NOT context memory, rule 16):** DECIDE `DQ7_II_MINISPEC_DEBATE_DECIDE.md` U1-U15/§DECIDE. Route `test_newton_clip_routing.py` re-audited at the `_ph()` boundaries: `:3891 _ph("GRASP_HOVER")`→`:3893` single call / `:3896 _ph("GRASP_DESCEND")`→loop `:3898`→**`:3900` single site** / `:3905 _ph("GRASP_CLOSE")` / `:3927 _ph("LIFT")`→`:3931`=`ROUTE-LIFT{k}` / `:3961 _ph("ROUTE_C1")`→`:3966` / `:4479 for kk`→**`:4481` C2-RHOVER** (R=`_fr`, L=`_La`), reach-check `:4486-4487 _reach_R_mm(_paR)`, `:4492 for kk`→`:4494` C2-RDESCEND, `:4515 _at_88`, `:4516` ⛔ANTI-REVERT regrasp_ok. Converter `route_demo_to_bc.py`: `:34 PHYSICS_STEPS_PER_RL=10`, `:287 wp=concat([er[next_f],el[next_f]])` (abs label = achieved next-frame ee_pos), `:333-336 d_r=(er[next_f]-er[step_f])/scale` (delta label = achieved ee_pos delta), `:156-157 wp[rows].min/max` per-phase box, `:451-452 amax≤0.95`, `:519` union affine over all train demos.

**L-TRIAGE (§8 self-run):** final_L = **L3** (unchanged) — CP-(ii)-1 build edits Rs-LOCKED `test_newton_clip_routing.py` (§0 path-match auto-escalation, no demotion). CP-(ii)-0 v2 (this doc) = design-only precursor (0-GPU, 0-edit). The completed 5体 pre-debate (Opus 4.8) = the L3 [VERIFY]; a **targeted cycle-2 re-review of the changed sections** may follow per DECIDE §Process; rule-check stage2 before the build (not for this design doc). **Prior-art V10:** DQ7 self-referential (2 legs run + delta recorded), continue per charter §8.

---

## §0. CHANGE-MAP (v1 FAIL → v2) — %12 conformance table

| # | debate item | v1 (FAILED) | v2 disposition | v2 loc |
|---|---|---|---|---|
| 1 | **U1 CRIT** :3931 mis-attributed | §B listed `:3931` under DESCEND{1} | **:3931 = LIFT{3} (SKIP) — DELETED.** Full §B re-audit at `_ph` boundaries + **build-time `_ph`-eligibility assert** (abort if any hooked line's phase ∈ SKIP{2,3,6,7,8,14}) | §B |
| 2 | **U2 CRIT** hold-at-offset anti-restoring; label=achieved ee_pos | hold-at-offset dwell KEPT; F1 "target−offset relabel" | **kick-and-recover:** drop the whole kick(outbound) window, **keep ONLY post-release recovery frames**. label-provenance corrected (achieved ee_pos `:287`/`:333`, NOT commanded target). **F1 discarded** (no algebraic relabel) | §A, §F |
| 3 | **U3 HIGH** dwell unrealizable + 10× clock | dwell=20 "control-steps" | dwell/kick in **ik_move_both-CALL units**; ONE clock (control-frame row index) + ×10 cadence explicit; converter assert kept-row achieved-target≈script-target | §C, §F |
| 4 | **U4 HIGH** {0} single-call no recovery | {0} listed primary | {0} NOT primary ({1} DESCEND=robust loop teacher); {0}=generalization-only unless restructured (out of "wrap the arg" scope) | §B, §J |
| 5 | **U5 HIGH** {11}:4494 corrupts LOCKED regrasp_ok | {11}=:4481+:4494 | **{11}=:4481 (RHOVER) ONLY**; :4494 dropped; offset=0 guard before reach-check; on-disk regrasp_ok/_reach_R_mm reproduction assert | §B, §D |
| 6 | **U6 HIGH** %9 N1 unimplemented; concur charter-scoped | span-watch only | v1 primaries {1,11}=pre-contact → **N1 MOOT for v1**; N1 (X,Z-only/Y≤3mm) pre-registered for **deferred** dual-hold fills; **%9 re-validates v2** | §J |
| 7 | **U7 HIGH** injection inflates union affine hull | affine over raw wp | build affine **AFTER masking** (kept-p2r+clean only); p2r regression: per-phase box within tol of clean-b2 + amax≤0.95 recheck on masked set | §F |
| 8 | **U8 HIGH** NHA proportionality | inject {0,1,4,5,10,11,12,13} | **v1 scope = primaries {1,11} only; fills {4,5,10,12,13} → v3** (budget-gated). Sweeps out {10}/{4,12}/SEAT_TOPDOWN from v1 | §B, §J |
| 9-14 | U9/U10/U14 fill-defects | in-scope | deferred with fills → §J | §J |
| 15 | **U11 MED** None-path weak | gate/skip, 1-run | literal passthrough first-stmt (pure-python, `is`-identity test) + 2-leg (CPU-primary + cuda:0) + 2-sha | §G |
| 16 | **U12 MED** loud-notify locked-file | buried | explicit non-buried locked-file disclosure line | §K |
| 17 | **U13 MED** video claw-zoom | "video legs" | skill-path unskippable + {11} grasp claw-zoom slip/drop | §I |
| 18 | **U15 LOW** validity≠γ⊥ | validity only | pre-register min restoring-frame/cell {1,11} + wave-1 directional γ⊥ check; conservatism tagged | §H |

**REBUTTED/surviving intact (DECIDE §38, carried unchanged):** control-API legal (EE-detour via `ik_move_both`/`solve_ik_dual` = DiffIK, no kinematic trick, ≠xfrc); {9} vacuous (0 rows); beat = CP-D replicate-null as-is (%9 N3); markers `:4401/:4417/:4516` byte-safe (wrap is on the target-arg, upstream derivation + downstream verdict untouched); INVARIANTS untouched.

## §A. Mechanism — **kick-and-recover** (U2, core re-architecture; replaces v1 hold-at-offset)
Flag-gated **`PERTURB_INJECT`** (default unset/off → literal passthrough = byte-identity, §G). When set = a pre-sampled deterministic **injection schedule** (seed-recorded). Within an eligible **loop** phase, at a scheduled loop-iteration the hook adds a **detour offset** to ONE arm's `ik_move_both` target for **`kick_calls` calls (CALL units, §C)** — the "kick". Then the offset is **released (→0)**; the script's subsequent same-phase loop calls target the true waypoints, so the achieved EE **servos back toward the script path = the recovery**. NO xfrc (D-2). Cable never teleported (INV#5).

**Label provenance (U2, code-verified):** the BC action label is the **achieved next-frame ee_pos** — abs `wp=er[next_f]/el[next_f]` (`:287`) or delta `(er[next_f]−er[step_f])/scale` (`:333`) — **NEVER the commanded IK target**. Consequence, which drives the masking (§F):
- **kick/outbound frame:** obs=on-/going-off-path, label=achieved-moving-toward-detour = anti-restoring → **DROP**.
- **(no hold window** — v1's held-at-offset dwell is ABOLISHED; a held frame's label=achieved-stay-off-path = teaches the FOLLOWING failure the γ⊥ gate penalizes.**)**
- **recovery frame (post-release):** obs=off-path, label=achieved-moving-back-toward-script = **the restoring teacher** → **KEEP**.

My v1 F1 ("relabel dwell = recorded_target − offset") referenced `ee_tgt_pos`, which is NOT the label → subtracting there changes nothing the trainer reads. **F1 discarded; no algebraic relabel.**

## §B. Hook insertion points — v1 ACTIVE = {1},{11} ONLY (re-audited at `_ph` boundaries, U1)
Single helper `_inject_detour(sched, phase_name, arm, tgt_xyz, call_idx, rec)` wraps the **target argument** at each eligible `ik_move_both` call. None-path = literal passthrough (§G). The LOCKED target-derivations and the markers are NOT re-authored.

| 15-idx phase | `_ph` line | ik_move_both site | v2 status | note |
|---|---|---|---|---|
| 0 GRASP_HOVER | :3891 | :3893 (`tgt`, single call) | **generalization-only** (NOT hooked v1) | single 52-row call, no in-phase recovery (U4) → recovery would bleed into {1} onehot |
| 1 GRASP_DESCEND | :3896 | **:3900** (`tgt`, loop×8) | ✅ **ACTIVE primary** | robust loop teacher; one arm; **Z-comp ≤0 forbidden** (table) |
| 3 LIFT | :3927 | :3931 (`tgt`, loop×12) | ⛔ **SKIP — :3931 DELETED** | v1 error; gradual LIFT prevents banked WR-drop (RS71:26) |
| 4 ROUTE_C1 | :3961 | :3966 (`tgt2`, loop×N_ROUTE) | ⏸ **v3 (deferred)** | dual-hold → N1; re-audit at v3 |
| 11 C2_REGRASP | :4479 | **:4481** (`_fr`=R, RHOVER loop×10) | ✅ **ACTIVE primary (R-arm)** | :4494 (RDESCEND) **DROPPED** (U5); markers :4401/:4417/:4516 upstream/downstream untouched |
| 5,10,12,13 | — | (v1 map UNVERIFIED post-:3931) | ⏸ **v3 (deferred)** | line numbers **re-audited at v3**, NOT carried from v1 |
| 2,6,7,8,9,14 | — | — | ⛔ SKIP | close/pin/gripper-transition/vacuous{9}/verdict-window |

**Build-time `_ph`-eligibility assert (U1, CP-(ii)-1):** at build, each hooked call site resolves its enclosing `_ph()` label; **assert `_ph ∈ {GRASP_DESCEND, C2_REGRASP}` (the v1 active set); abort if any hooked line's phase ∈ SKIP{2,3,6,7,8,14}.** One confirmed mis-attribution (:3931) ⇒ v1 table was un-cross-checked ⇒ this assert is the structural guard, not a comment.

## §C. kick/recovery numerics — **ik_move_both-CALL units** (U3)
`ik_move_both` is **atomic per call** (target fixed once, `n_steps≥50` phys = ≥5 control rows at cadence 10). The achievable quantum is **whole CALLS**, not control-steps.
- **kick_calls = 1** (initial) for {1} DESCEND (8-call loop → kick 1, recovery ~7); **kick_calls ≤ 2** for {11} RHOVER (10-call loop) **AND offset=0 by the final 2 calls** (§D guard). Recorded as `kick_calls` (nominal) + achieved `kick_rows`/`recovery_rows` (physics-frame rows) in meta.
- **ONE clock:** all window fields = control-frame **row index** (the recorder/converter clock, cadence `PHYSICS_STEPS_PER_RL=10`); the ×10 physics-step conversion is stated explicitly, never mixed. (v1's §C control-steps vs §D physics-frames with a silent ×10 = the U3 leak.)
- **direction:** unit-3D per injection, magnitude log-U per §E; {1} DESCEND **Z-comp ≤0 forbidden** (resample). per-arm single-sided (INV#1 both-arms-engaged preserved). seed recorded.
- **converter assert (U3, add to regression):** every KEPT p2r row's achieved-target ≈ script-target within IK residual (a kick/outbound row that leaked in fails this).

## §D. {11} regrasp_ok guard (U5, LOCKED-verdict protection)
The reach-check `:4486-4487` reads achieved `_paR` **after the whole RHOVER loop**; it feeds `:4515 _at_88` → `:4516` LOCKED `regrasp_ok`. Therefore:
- restrict {11} injection to the **RHOVER loop `:4481` ONLY** (drop `:4494` RDESCEND).
- **hard guard: offset=0 for the final RHOVER call(s)** before the RHOVER→RDESCEND handoff and before the reach check (kick early kk≤3, recovery completes by kk≤8, kk=9-10 clean).
- **on-disk assert:** injected {11} recordings reproduce the None-path `regrasp_ok` / `_reach_R_mm` (verdict-VALUE untouched, not just bytes — Rs 2026-07-01「先祖返りしないように」intent).

## §E. recorder meta injection-window fields (records-vs-fact, U-追加1) + §3 amplitude
`mark_injection(...)` appends to `meta["injection_windows"]` (additive; absent when off = byte-identity):

| field | type | meaning |
|---|---|---|
| `phase`/`phase_idx` | str/int | eligible phase ({1} or {11}) |
| `arm` | "L"/"R" | single perturbed arm |
| `offset_mm` | [dx,dy,dz] | **ACTUAL** applied detour [mm] (not nominal) |
| `kick_call_idx` / `kick_calls` | int | loop-iteration start + kick length (CALL units) |
| `kick_rows` / `recovery_rows` | int | achieved physics-frame rows (kick=dropped, recovery=kept) |
| `release_before_reach` | bool | {11}: offset=0 confirmed before reach-check |
| `schedule_seed` | int | reproducibility |

**records-vs-fact (CP-(ii)-1 review):** meta `offset_mm`/`kick_rows`/`recovery_rows` MUST equal what the hook applied — verified by (a) converter reading `injection_windows` back and (b) on-disk cross-check that the recorded EE-target during kick = script_target + `offset_mm` (±IK residual) and =script_target after release. A meta that could lie under a future config = build-review BLOCK.

**§3 amplitude (charter, verbatim for ACTIVE cells — ZERO deviation):** {1}[2,20] Z≤0-forbidden / {11}[2,20] R. Fills {4,5,10,12,13} amplitudes = **v3** (deferred; not re-listed here to avoid implying v1 scope). Any change = %9 re-concur.

## §F. converter — kick-and-recover masking + affine-after-masking (U2/U7)
Additive default-off branch on `route_demo_to_bc.py` (my augment-branch precedent; regression = normal convert sha b3472e8c/0ed5149c + py_compile):
1. **mask (U2):** DROP kick/outbound rows (target=detour); KEEP post-release recovery rows (label=achieved-moving-back=restoring). No hold window exists to keep.
2. **affine AFTER masking (U7):** build `_build_abs_affine` over **kept-p2r + clean** frames only (or clip detour excursions from the hull) so injection excursions don't inflate the union box (`:156-157`/`:519`). **p2r regression:** per-phase box within tol of the clean-only b2 box + `amax≤0.95` (`:451`) recheck on the masked set.
3. **converter assert (U3):** each kept p2r row achieved-target≈script-target within IK residual.
Output `b2_dataset_v2_p2r/bc_dataset_abs_p2r.npz` (`_p2r` schema tag, truthful meta: n_clean/n_p2r/injection stats per-(phase×bin)). **beat = CP-D replicate-null as-is** (physical recordings non-replicable → no augmented-null; charter §5 / %9 N3).

## §G. None-path byte-identity (U11)
- **literal passthrough as the FIRST statement** per hooked site: `if sched is None: return tgt_xyz` — pure-Python floats, zero numpy, `is`-identity unit test. (fix-⑤ `:3875` gates the whole mutation; ULP-fragile `int(n_steps)` never re-touched on None-path.)
- **byte-identity = TWO-leg:** CPU-deterministic **primary** + cuda:0 fingerprint secondary (recorder fd005ab83f / fix-⑤ 0b711c6b31 precedents).
- **TWO-sha:** route file (`e01ac1fa…` re-proof) + recorder-output npz.
- per-marker re-sync by **grepping the ⛔ANTI-REVERT text** (`:4401/:4417/:4516`), not offset arithmetic; asserted at CP-(ii)-1 diff review.

## §H. γ⊥-movement pre-registration + wave-1 directional check (U15)
Validity-budget pass ≠ the GO bar (γ⊥ movement). **Pre-register BEFORE the full batch:**
- **min restoring-frame floor per load-bearing cell** {1},{11}: measured `recovery_rows` (meta) per cell ≥ floor (kick=1 call {1} / kick≤2 {11} → recovery = remaining loop calls; exact physics-frame floor read at wave-1, not fabricated here).
- **wave-1 directional γ⊥ check:** γ⊥ at {1} and {11} moved **directionally ↓** (toward the restoring bar) on the 4-recording wave-1 before committing the ~28-recording batch.
- **conservatism (§運用15):** validity = **conservative-safe**; **γ⊥ movement = non-conservative, must be SHOWN not assumed** (a validity win does not imply the GO bar).

## §I. video leg (U13, §運用14)
Skill-path **unskippable** (`/video-analyzer` or `video-analyst`): injection→kick→release→recovery visual + for the {11} grasp a **claw-zoom slip/drop check** (memory feedback-video-detect-intra-finger-cable-slip). Wave-1 (§H) carries the video leg; motion-bearing RESULT verdict gated on it.

## §J. deferred to v3 (U6/U8/U9/U10/U14) — NOT in v1
- fills **{4,5,10,12,13}** (budget-gated v3): line numbers **re-audited at v3** (v1 map unverified post-:3931).
- **%9 N1** (dual-hold detour X,Z-only / Y-span ≤3mm proactive cap, survivor-bias fix) — pre-registered for the deferred dual-hold fills {4,5,10,12,13}; **MOOT for v1** (primaries {1,11} pre-contact, span unformed).
- **{10}** contact-fragility (179-row しごき): v3 restrict to aerial PRELIFT or gate on cradle/JAM/slip in-band (reuse is_cradle/JAM flags) — a JAM/loss mislabeled as restoring poisons BC (U9).
- **:4255 SEAT_TOPDOWN=1** conditional (U10): pin recording mode or use always-live :4263.
- **5mm span-watch** provenance (U14): cite moves_ok/EE-converge gate (RS71 §1:35) or pre-register; sample span at **recovery (post-reconvergence)**, not during the intentional kick.

## §K. loud-notify locked-file disclosure (U12) — for §8 Rs notify
Explicit non-buried line: **"CP-(ii)-1 build EDITS the Rs-LOCKED canonical route `test_newton_clip_routing.py` (flag-gated kick-and-recover hooks around the {1} DESCEND `:3900` + {11} RHOVER `:4481` pre-contact targets); byte-identity (2-leg/2-sha) + markers `:4401/:4417/:4516` untouched + `_ANTI_REVERT` re-sync guaranteed."** (RS71 §0 requires surfacing locked-surface touches; the pre-GPU Rs veto window must be informed.)

## §L. chain / next
CP-(ii)-0 v2 (this) → **%12 conformance check** → **%9 RE-VALIDATE v2** (v1 concur was charter-scoped + N1-conditioned, U6) → optional targeted cycle-2 re-review of changed sections (kick-and-recover) → **Rs loud notify (§K locked-file disclosure + GPU-h ~3-5h + device pins cuda:0/EGL + (iv) Outcome-B summary + wave-granular early-abort + abort procedure)** → CP-(ii)-1 build (hooks + converter mask + meta + `_ph`-assert + regrasp_ok guard) + None-path byte-identity (2-leg/2-sha) + 縮退 review. 0-commit; commit 判断 = %12. band α/β/γ (§7) = Rs decision, blocks CP-(ii)-5 (OG gate) ONLY. **rollout prohibited (OG GO 後も別途 Rs GO).**

## CC4 ground-truth phase rows (recovery-floor reference, DECIDE)
{0}52 {1}**40** {2}21 {3}60 {4}36 {5}46 {6}4 {7}11 {8}52 {9}0 {10}179 {11}**118** {12}62 {13}81 {14}8. (Active cells bold; {1}=40 rows/8 calls≈5 rows/call; {11}=118 rows incl RHOVER+RDESCEND+cage, RHOVER-only floor read at wave-1.)
