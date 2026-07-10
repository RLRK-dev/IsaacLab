---
doc_class: reference
---
> ⛔ SUPERSEDED / HISTORICAL (as-of 2026-07-11, COORD2 vault-audit) — tracking SSOT = LEDGER VL2 (`00-DESIGN-STATUS-LEDGER.md`). optE-B-BC-imitation: superseded by ladder-v2 / env-core. Do not copy live values — pointer task_config.py / successor docs.

# B0 BUILD REPORT (COORD %11) — converter + evaluator + open-loop replay (DQ1=B)

**Charter:** `charter_b0_build_coord.txt` (RS-TECH-LEAD %12). **Binding:** `B_BC_BUILD_SPEC.md v2.2` (§10 ERRATA E1-E11 + E4'/E10/E11 override). **env7 python.** New files 0-commit; route file IMPORT-ONLY.
**Build order (checkpoint per step):** 1 converter → 2 evaluator → 3 smoke → 4 full B0.

---

## STEP 1 — CONVERTER `thread_isaac_lab/scripts/route_demo_to_bc.py` ✅ COMPLETE (2026-07-02 10:10 JST)

Pure offline transform (numpy + json + hashlib + pure-CONSTANT `task_config.GROOVE_CENTER_Z`; no sim runtime). 306 LOC (core `convert()` ~150; remainder = §2.6 self-check harness + 5-row dump + `main`). Input = FROZEN 13-phase `p3_dod_cuda_demo_raw/route_demo_raw.npz` (sha `509ad193…`, as-run test sha `9bdf8f63…`).

**Outputs** (`b0_dataset/`): `bc_dataset.npz` (obs `[770,25]` f32 + actions `[770,6]` f32 + embedded meta) + `schedule.json` + `bc_dataset_meta.json`.

**§2 build faithfulness (independent npz probe reconciled — §運用28):**
- **§2.1 cadence:** control frames 0,10,…,7700 (771) → T_ctrl=**770**; 6-frame tail (7701-7706) zero-motion (max 0.0), dropped.
- **§2.2 actions [770,6]:** `concat(Δee_pos_r, Δee_pos_l)/0.015`, **R-then-L**; achieved ee_pos delta. max|a|=**0.588**<1 (no clip); max‖Δ‖ R=8.53 / L=11.39mm.
- **§2.3 obs [770,25]:** ee_r(0:3)+ee_l(3:6)+seg_pos(6:9)+next_clip(9:12)+phase-onehot13(12:25). −1→GRASP_HOVER. seg-rule table (echoed to meta): phases 0-4→`nearest_seg_r`; C1_SEAT/C1_PIN→**seated_seg=27** (`pinned_body−28`, NOT phase-entry argmin 28); L_HALF_UNCLAMP/R_UNCLAMP_RISE→grip-predicated `held_seg_l` (grip col0=L ≥0.6) else `nearest_seg_r`; GUIDE_C2..→`argmin_to_c2` (recomputed from `cable_xyz`). next-clip: C1 through C1_PIN, C2 from L_HALF_UNCLAMP; **z_top=0.829** (GROOVE_CENTER_Z 0.809 + CLIP_FLOAT_Z 0.020 == canonical groove_z 829.0mm).
- **E4' assert (integer-exact):** argmin-to-C1 at pin-fire = 27 == `pinned_body(55) − cable_body_start(28)`; discriminating (argmin 2.81mm vs runner-up 12.22mm).
- **§2.4 schedule.json:** 37 per-arm grip transitions (init `[0,0]` asserted; first L@910=0.667, last R@7617=0.0); pin_event (frame 2544, body 55, eqid 27, anchor=LIVE-derived note); 13 phase_transitions; override window [5000,6180]; verdict_landmarks (c1_seat 2084 / c2_hover_end 6800 / post_close_settle 7616 / c2_settle 7706) + `ee_tgt_pos_r_at_c2_hover_end`=[0.400,0.119,1.127]. **quat-default assert PASS** (maxdev 0.0 both arms, exactly ONE override window).

**DoD §9-Converter:** §2.6 self-checks **12/12 PASS on the real npz** (shapes / |a|≤1 / finite / one-hot=1 / cumulative-recon **1.56e-9**<1e-5 / seg-table 13 / grip init+37 / cable_body_start 28 / z_top 0.829 / pin 2544) + 5-row human dump (physically coherent: GRASP_HOVER aloft→C1_SEAT settled→GUIDE_C2 flip→C2_REGRASP R-approach→C2_SETTLE seated) + meta complete (seg table echoed). **層3:** py_compile OK / ruff **All-passed** + format **STABLE**. Locked files (`test_newton_clip_routing.py`, `task_config.py`) **untouched** (converter standalone). 0-commit.

**→ NEXT: Step 2 evaluator** `policy_route_runner.py` (§4; E5 re-grep anchors vs fd005ab83f; code + 層3 checkpoint BEFORE any GPU run).

---

## STEP 2 — EVALUATOR `thread_isaac_lab/scripts/policy_route_runner.py` ✅ CODE COMPLETE + 層3 PASS (2026-07-02 10:40 JST) — awaiting %12 STOP-flag ruling before GPU

Built per §4 + §10 ERRATA (implementation delegated to a fresh-context sub-agent; **COORD owner-verified** independently — NOT rubber-stamped). **696 LOC** (>the ~250-400 est: faithful re-impl of the route's inline verdict machinery ≈500 route lines + ruff one-per-line expansion; every fn maps to a §4 subsection). 0-commit (untracked). Route file + task_config.py + newton_skill_env_base.py = **IMPORT-ONLY, untouched**.

**E5 resolved-anchor table (re-grepped on current committed files; reconciled with COORD's own grep — MATCH):** route `build_scene:1031 / build_fk_model:1689 / physics_step:1759 (gripper_dynamic 1782/1796) / solve_ik_dual:1823 / ik_move_both:1927 (sub-interp 1993-2007) / _set_gripper_target:2986 / _run_mujoco_grasp_route:3499 (gripper_dynamic 3528, open 3529) / _arm_split:3689 / _min_dist_mm:3606 / _claw_cable_load(mj_contactForce):4033 / partition-freeze:4097 / pin poke:4132 / 4-way verdict:4507-4515 / _c2_regrasp_rec:4523-4531 / C2 settle:4587 / main wiring:6494-6640` + base `make_solver:1301 / _wire_s6_grasp_solref:1343`. **SHAs:** route `ac0e3f53` ∈ E1 set ✓ / task_config `1a0851db` == E9 ✓ / base `e6d3cdbc…488e00` == E10 ✓.

**COORD independent verification (owner, decider≠implementer):**
- **層3 (re-run, not trusting the sub-agent):** `py_compile` OK / `ruff check` **All-passed** / `ruff format --check` **stable**.
- **E-errata compliance (grep + read):** E1/E9/E10 sha asserts present w/ correct pins (runner L36-40); E9 force `DEMO_RECORD=0` (L72) + skip-null; `state=model.state()` (L333); gripper_dynamic=True + pre-loop assert (L336-337); servo on `scene_info["vbd_control"]` — never a fresh control (L351/L479, E6); E2 `total==7700` assert (L414).
- **Faithfulness (read the load-bearing blocks):** §4.2 apply-path = IK-once → **sub-interpolate joint Δ ×10, gripper coords preserved** (L494-501, mirrors ik_move_both) + grip fires BEFORE frame's physics_step, mapped by NAMED arm (L477-480, E2/E6) + §9-B0 per-step tracking error (L507); §4.5 pin = **seat-verify FIRST → unseated=NO-FIRE=FAIL** → live-anchor `eq_data[3:6]=live seat pos`, `eq_active=1`, **no extra settle** (L202-236, mirrors :4118-4134). Verdict deep-fidelity is exercised by the Step-4 canonical-fingerprint comparison (the designed test).
- Locked files git-clean; new file `??` (0-commit).

**Compliance checklist:** §4.1 (8 steps) / §4.2 (5) / §4.4 (verdict + json fields) / §4.5 / §4.6 smoke `--max-control-steps` / §4.7 `--record-video` (offscreen, not auto-run) / E8 IK-fail log+tag + try/finally always-emit verdict — **ALL implemented** (line refs in the sub-agent deliverable, COORD-spot-verified above).

**⚠ 7 STOP-FLAGS surfaced (binding-contract: reported, NOT improvised — for spec-owner %12):**
- **SF-2 (verdict, needs ruling):** 6 `_c2_regrasp_rec` fields are the route's **C2-regrasp CONTROL decisions** (r_target_x/y/z, r_x_offset, picked_body_dy, tilt_theta), NOT recoverable from open-loop state → set **null w/ provenance**. JUDGED categories (reach/grips/span/verdict/regrasp_ok) ARE recovered → fingerprint intact. Confirm null-ing non-judged control fields satisfies §4.4 (else the runner would have to replicate C2-regrasp control = not open-loop).
- **SF-3 (C1 seat bars, needs ruling):** route has no single C1-seat boolean; runner **borrows the C2-settle criterion** (cable↔clip ≤0.5mm AND |z−829|≤3mm) for C1, cross-checked TRUE on the demo (z=829, dist=−0.613). Confirm the borrowed bars or supply exact C1 bars.
- **SF-1 / SF-6 (B1, not B0):** live obs seg_pos / obs-frame alignment cannot bit-match the recorder's `nearest_seg` metric (not in read-set). **B0 UNAFFECTED (action=lookup, obs unread); B1 obs-distribution-shift risk** — resolve before B1 (confirm/import recorder seg fn).
- **SF-4 (minor):** `bc_dataset_meta.json` has no `env_gates` (they're in `route_demo_raw_meta.json`); runner reads `--raw-meta`. Non-blocking; recommend converter echo env_gates.
- **SF-5 / SF-7 (notes):** partition freeze @2084 = time-invariant (same geoms); C1-held read at the pin frame 2544 (cable actually seated); `c2_settle_end 7706`=zero-motion tail → seat captured on final loop state; solref "demo-known" ≡ `MUJOCO_PAD_SOLREF` (SSOT constant _wire pokes).

**→ NEXT (gated on %12):** Step 3 GPU smoke `--max-control-steps` (GRASP..LIFT, does NOT hit the C2 verdict, so SF-2/SF-3 don't block it) — hold for %12 review of the code + STOP-flag ruling before burning GPU (charter: code+層3 checkpoint BEFORE any GPU run).

---

## STEP 3 — GPU SMOKE (GRASP..LIFT, cuda:0) ✅ PASS + caught & fixed BUG-1(validated) & BUG-2 (2026-07-02 11:21 JST)

Smoke = `--max-control-steps 172` (GRASP_HOVER..LIFT; ROUTE_C1 starts at control step 172), cuda:0 (A6000, CUDA_VISIBLE_DEVICES=0). runner 773 LOC. **%12 pre-approved smoke after BUG-1 fix + 層3.**

**BUG-1 (grasp_yc) VALIDATED on GPU:** `[RUNNER] caveat-a GRASP_YC=+150.00mm` — matches the canonical route's caveat-a EXACTLY; the `assert |GRASP_YC-0.150|<10mm` passed. The claw-partition centre is now correct (was the 0.0-hardcode L/R-attribution trap).

**BUG-2 (initial arm pose) — caught by COORD's absolute-drift pre-read, fixed:**
- The charter's smoke deliverable is a tracking-error curve; COORD ALSO computed the **absolute ‖ee_replay − ee_demo‖** (the §9-B0 real fidelity metric) as a cheap pre-read BEFORE the 40-min full run. First smoke: per-step tracking <1mm BUT **absolute drift ~1.1m** (R max 1288mm) — the delta-based open-loop masks an origin error.
- **Diagnosis:** offset was **EE-only** (cable/seg/next_clip Δ~0 = frame correct) → arm-init problem. Root cause = the runner mirrored `main()`'s home config (`joint_target_pos`, EE X=−0.817 folded) but MISSED the route fn's **grasp-approach SEED config** set right before its settle (`test_newton_clip_routing.py:3839-3847`, `seed_l/seed_r`, EE=[0.267,0.202,1.560]) — the demo's frame-0 arm = that seed.
- **First fix WRONG (transparent):** `update_kinematic_bodies` alone → byte-identical drift (no-op; it aligned to the wrong = home config). Re-diagnosed → the seed was the missing piece.
- **Corrected fix:** replicate `seed_l/seed_r` + `eval_fk` + `update_kinematic_bodies` (sync physics body_q) before obs[0] (runner startup, mirrors route:3839-3848).
- **VALIDATED (smoke3):** absolute drift **1.1m → 12.4mm** (R max, ~100× reduction); **t=0 = 0.004mm** (origin now exact); per-step tracking max **1.02mm**, terminal **0.02mm**; ik_failures **0**; GRASP_YC=+150mm.

**Smoke verdict:** startup 8-step preamble PASS (scene build / neq=46 asserts / solref+I11 asserts / sha asserts → shas_seen {route ac0e3f53, task_config 1a0851db, base e6d3cdbc} = E1/E9/E10 pins) + BUG-1 & BUG-2 validated + no IK failures. `failure_mode=unseated_pin` = EXPECTED (smoke stops at LIFT, pre-pin frame 2544). 層3 PASS (ruff All-passed + format stable), locked files untouched, 0-commit.

**Honest apply-path gap (§6 row1):** absolute EE drift GROWS 0→12.4mm across GRASP_DESCEND→LIFT (open-loop sub-interp vs exact-IK + contact). The C2 seat is a 0.9mm knife-edge (E7) at ~step 700; the full B0 measures whether the accumulated drift stays within margin (the C1 pin anchors the cable at frame 2544, so EE drift ≠ direct seat failure, but it must be measured). Smoke debug artifacts: `b0_smoke` (BUG-2 present), `b0_smoke2` (no-op fix), `b0_smoke3` (VALIDATED).

**→ NEXT (gated on %12): Step 4 full B0** open-loop replay (~40min cuda:0, full 770 + `--record-video`) → §9-B0 DoD (startup parity + categories vs canonical + full absolute-drift series both arms + drift@events + E7 C2 margin + §4.4 delta table + obs-parity table + video-analyst leg + 0-diff locked + 層3). %12 said "Step 4 = smoke 結果次第".

---

## STEP 4 — FULL B0 open-loop replay (770 steps + video, cuda:0) — ⚠ CATEGORY **FAIL**, attributed to the open-loop apply-path gap (2026-07-02 11:45 JST)

%12 GO (ckpt3) conditions met: (1) nvidia-smi pre-check + CUDA_VISIBLE_DEVICES=0 (GPU0 free); (2) durable to `b0_full/` (non-scratch: run_config.sh + full_stdout.txt + runner_verdict.json + obs_series.npy + runner_route.mp4); (3) §6-row1 attribution below (NO redesign talk). Startup PASS (shas_seen E1/E9/E10 pins; solref+I11; GRASP_YC=+150mm; perclip_pin=40). ik_failures 0. total_physics_frames 7700.

**Categories vs canonical (§4.4 pre-declared, set-based) — FAIL:**
| category | runner (B0 replay) | canonical (demo) | verdict |
|---|---|---|---|
| regrasp_ok | **False** | True | ✗ |
| regrasp_verdict | **R_MISS_AT_88** | SUCCESS_R_GRIP_L_CAGE_AT_88 | ✗ |
| C1_held (seat incl z) | **False** | (seated) | ✗ |
| C2 settled_in_notch | **False** | True | ✗ |
| pin fired | **False (unseated)** | (fired) | ✗ |

Root proximate: at the pin frame (2544 / step 254), **cable↔C1 = 23.1mm** (vs ≤0.5mm bar), seat_z 803.9mm (vs 829), `seated=False` → pin NO-FIRE (§4.5, correct) → all downstream (C1-held / C2 regrasp / C2 seat) fail. r_reach 18.0mm (canonical 0.9), r_grip 0.0N (canonical 104.51).

**§9-B0 absolute drift series ‖ee_replay − ee_demo‖ (the DoD deliverable + the attribution evidence):** R max **16.71mm** (terminal) / mean 13.06 / NEVER >20mm; L max 14.60 / mean 12.07. Accumulation by phase entry: 0.0 (HOVER) → 9.6 (GRASP_CLOSE s91) → 12.5 (ROUTE_C1 s173) → 13.2 (C1_SEAT s209) → 13.9 (C1_PIN s255) → 16.7 (C2_SETTLE s762). **Per-step tracking err (achieved vs its own target): max 1.02mm / terminal 0.007mm** — the apply path REACHES each step's target, but the ABSOLUTE pose drifts because open-loop deltas ≠ the demo's exact trajectory. obs-parity overall max 0.102 (B1-前 gate measurement, saved). E7 C2-margin: N/A (C1 seat failed → C2 never properly reached).

**§6-row1 ATTRIBUTION (control run FIRST, no redesign talk):**
- **Scripted-route control = the demo** (canonical `_run_mujoco_grasp_route`, cuda:0, TODAY, `cuda_leg_route_c2_pin.json` regrasp_ok=True) — a scripted-route SUCCESS on the EXACT current state (route sha ac0e3f53 / task_config 1a0851db / base e6d3cdbc all **asserted identical** by the runner ⇒ env provably unchanged since the demo). ⇒ the ENV + scripted controls WORK.
- **Ruled out:** converter (§2.6 self-checks PASS + cumulative-recon 1.6e-9), wiring (startup asserts PASS + GRASP_YC=150mm + per-step tracking <1mm), non-determinism (drift is SYSTEMATIC + monotonically growing, not stochastic).
- **Attribution = the open-loop APPLY-PATH GAP (§6 row1 category c):** the replay applies 1 IK + linear joint-Δ sub-interp across 10 frames; the demo used exact per-leg IK convergence (`ik_move_both` converge_mm + multi-iteration). The two diverge, accumulating ~14mm EE drift by C1 → the carried cable lands 23mm off C1 → seat FAIL. **This is precisely the "honest apply-path gap" the charter §6-row1 + §1-B0 anticipated** ("B0 DELIVERS the per-step ‖ee_replay−ee_demo‖ series"; "honest framing = pipeline shakedown"). The B0 pipeline works end-to-end (startup→replay→verdict→video→drift series); B0's job was to CHARACTERIZE this gap, and it did (bounded ~14-17mm EE, converting to a 23mm cable miss at the 0.5mm-seat C1).

**DoD status:** categories FAIL (characterized + attributed) / drift series DELIVERED / tracking DELIVERED / obs-parity DELIVERED / startup-parity PASS / 0-diff on LOCKED files (route + task_config = 0 vs fd005ab83f; base = Rs-committed 7eded5368c, runner import-only + sha-pinned) / 層3 PASS / video leg DONE (below). **NO redesign talk** — %12 to decide the next fork (this is a §6-row1 attribution report, not a solution proposal).

**Video-analyst leg (§運用14, independent, frames-only) — CORROBORATES the FAIL + attribution:** VERDICT = **PHYSICALLY VALID (no sim bug) but CONFIRMED C1 seat MISS** — the cable ends the episode held at the gripper gap, visibly off to the side of the clip cluster, never seated (visually confirms the ~23mm C1 miss / R_MISS_AT_88); motion smooth/continuous with NO teleport/NaN/explosion; grasp appears real (cable co-located at the gap, not empty air); no gross interpenetration. The flagged behavioral (not-physics) issue = **very small effective routing displacement over the whole replay, consistent with open-loop apply-path drift** = independent visual corroboration of the §6-row1 attribution. Conservatism: the miss is at the visible (≳cm) scale (render non-conservative would HIDE a small gap — yet the off-clip gap is visible) → miss call robust; sub-cm interpenetration + clamp-tightness unresolvable at this render scale (single 640×480 offscreen panel).

---

## STEP 4a — B0a ABSOLUTE-WAYPOINT diagnostic replay (spec E13, %12 fork-b) — pipeline legs LARGELY validated; C1-seat knife-edge NOT reached (2026-07-02 12:18 JST)

`--absolute-waypoints` (~30 LOC, layer-3 PASS): `tgt[t] = seeded-origin + cumsum(actions×scale)` = the demo's ABSOLUTE EE waypoints (consumes only converter output; breaks the B0-(i) live-anchor accumulation). ⚠ **pipeline-validation leg, NOT a B0-(i) pass-bar substitute (E13).** Smoke first (172 steps): drift 12mm→1.4mm bounded → full run (770 + video, cuda:0).

**What B0a VALIDATED (vs B0-(i)):**
- **Accumulation BROKEN:** absolute EE drift-from-demo R **max 1.38mm / mean 0.79 / terminal 1.37** (B0-(i) was 16.7 / 13.1) — ~12× reduction; obs-parity EE dims all ≤1.4mm.
- **R re-grasp verdict cross-validation vs canonical PASS (§4.4):** `regrasp_ok=True` (canonical True); verdict `SUCCESS_DUAL_LOADED_AT_88` **∈ SUCCESS_*** (set-based match with canonical `SUCCESS_R_GRIP_L_CAGE_AT_88`; the DUAL_LOADED variant = L also loaded 65.9N); r_reach **3.6mm** (bar ≤20; B0-(i) 18), r_grip **9.34N** (bar >0.1; B0-(i) 0). ⇒ the reach + grip + 4-way verdict re-impl WORKS.
- **§4.5 pin seat-verify logic VALIDATED (correct no-fire):** at the pin frame cable↔C1 = **1.684mm** (B0-(i) 23.1), seat_z 828.44 (|Δgroove|=0.56mm) — the ~1.4mm EE residual → cable **just over** the 0.5mm C1 seat bar → `seated=False` → pin correctly did NOT fire (pinning an unseated cable is outside the Rs authorization).

**What B0a did NOT reach (honest):** **pin FIRE / C1-held / C2-seat**. Root chain: EE tracks the demo to ~1.4mm, but the residual (10-frame linear sub-interp vs the demo's exact per-frame IK) puts the cable **1.68mm off C1 — just over the 0.5mm knife-edge seat bar** → pin no-fire → the cable is NOT anchored at C1 → during L_HALF_UNCLAMP the un-anchored cable drifts (seg_y up to **72mm** @step 269) → C2 not settled (`c2_settle` cable_c2 1.58mm / z 18mm off). So the C1-seat/pin/C2 legs remain **unvalidated by execution** — not because the pipeline is wrong, but because the 0.5mm C1 seat is a knife-edge the residual sub-interp fidelity can't quite hit.

**Attribution refinement (B0a isolates it):** B0-(i) FAIL had TWO stacked causes — (1) accumulation from live-anchoring [FIXED by absolute waypoints: 23mm→1.68mm] and (2) residual per-step apply-path fidelity (linear sub-interp vs exact IK) [remaining ~1.4mm EE → 1.68mm cable, misses the 0.5mm C1 knife-edge]. B0a confirms the pipeline (converter→replay→verdict→video→drift) is correct; the residual is a **fidelity gap at the sub-interp**, not a pipeline bug. **NO redesign talk** (a per-frame exact-IK apply path would be a fork-(ii) — %12's call, not proposed here).

**⚠ Non-conservative recording nuance (%12-flagged):** B0a reproduced the R re-grasp CATEGORY (SUCCESS_*, set-based) but NOT the grip PHYSICS magnitude — B0a `r_grip_N=9.34` vs canonical `104.51` (and `l_grip_N=65.9` vs canonical `0.0`, the DUAL_LOADED-vs-R_GRIP_L_CAGE variance). The verdict category matches on the set-based bar (`>0.1N`), but the contact-force magnitude is far from the canonical — i.e. B0a's category-reproduction is **non-conservative for grip-force fidelity** (a policy/real transfer must not read the category match as force-equivalence). This is expected for the absolute-waypoint apply (EE-target-driven, not force-driven).

**B0a DoD:** waypoint_mode `absolute_cumsum(B0a,E13)` echoed / GRASP_YC=+150mm / ik_fail 0 / startup parity PASS (E1/E9/E10 shas) / drift+obs-parity DELIVERED / R re-grasp verdict cross-val PASS / §4.5 pin logic VALIDATED / 0-diff locked / 層3 PASS / durable `b0a_full/` (run_config + verdict + obs_series + mp4 + stdout).

**Video-analyst leg (B0a seating case, independent, frames-only) — CONFIRMS the improved gross picture:** VERDICT = **PASS, PHYSICALLY VALID** — real grasp+lift (the cable ascends WITH the raised claws at f10/f82, not empty air); the cable is routed to the C1 clip region and **ends immediately adjacent to / at the clip with NO gross lateral gap = the near-seat picture, distinctly better than B0-(i)'s gross side-miss**; coherent motion (no teleport/NaN/explosion); no gross interpenetration. Honest limits (stated): the render is non-conservative <1cm → CANNOT distinguish "seated" from the ~1.68mm near-miss, and the discrete C2 re-grasp is below this single-640×480-panel resolution (re-grasp-like close/lift activity near the clip IS seen but not independently adjudicable). ⇒ visual corroboration that B0a closed the gross miss (23mm→near-seat); the sub-cm C1-knife-edge (seated vs 1.68mm) is a numeric-only distinction, consistent with the report.

---

## STEP 4b — B0b MACRO-IK-REPLAY diagnostic (spec E14, %12 fork-ii-as-diagnostic) — pin-FIRE + C1-held VALIDATED; C2 re-grasp NOT reached (2026-07-02 12:46 JST)

`--macro-ik-replay` (converter `emit_macro_schedule` +54 LOC / runner mode 3 +120 LOC; layer-3 PASS): extract 110 macro-legs from the npz `ee_tgt_pos_l/r` transitions → replay each leg via the route's OWN `rt.ik_move_both` (byte-identical apply) + events mapped to legs (pin@leg35). ⚠ **pipeline-validation leg, NOT a B0-(i) pass-bar (E14).** Startup preamble reused (BUG-2 seed + GRASP_YC=+150 + E1/E9/E10 shas). total_physics_frames 8055 (variable n_steps; the ==7700 assert correctly skipped in macro mode). ik_fail 0.

**What B0b VALIDATED (the legs B0-(i)/B0a could NOT reach):**
- **C1 SEAT achieved + PIN FIRED** ✓✓: at the pin leg (35) cable↔C1 = **−2.567mm** (seated, ≤0.5mm bar; B0a was 1.68mm no-fire), seat_z 831.1 (|Δgroove|=2.1mm ≤3mm) → `seated=True` → **the §4.5 pin FIRED** (live-anchor eq poke). This validates the pin-FIRE path (not just B0a's correct no-fire) + **C1_held = True** + the C1-seat verdict leg. r_reach 2.2mm (canon 0.9).
- The subagent's SF-B0b-1 event-ordering fix worked (pre-pin grips at leg-start, pin seat-verify+fire, post-pin L-half-unclamp AFTER the pin) — the pin captured the CLOSED-gripper seat.

**What B0b did NOT reach (honest):** the **C2 re-grasp / C2-seat** legs. regrasp_ok **False** (R_MISS_AT_88; canon True), r_grip **0N**, C2 `settled_in_notch` False (cable_c2 = **50mm** off, z 16mm off). **Attribution:** (a) the C2 re-grasp targets the ACTUAL cable bow (a demo-specific recorded `ee_tgt_pos_r`), and after C1-pin the guide/しごき dynamics diverge, so the fixed recorded C2 target no longer lands on the cable; (b) **SF-B0b-3** — the demo's guide/seat legs used slow `speed_factor` (~0.20-0.25 per the route) but B0b used ik_move_both's default 1.0 (per-leg converge/speed were NOT recorded), so the fast guide しごき ends the cable ~50mm from the demo's C2 bow. Both are open-loop-replay / diagnostic-mode limits, NOT pipeline bugs.

**Union B0a + B0b — the complete B0 diagnostic picture:** across the two diagnostic legs, EVERY leg MECHANISM + the §4.4 verdict machinery is now validated — B0a validated the **R re-grasp verdict** (SUCCESS_*, set-based match) + drift-bounding; B0b validated **C1-seat + pin-FIRE + C1-held** + the §4.5 fire path. But **no single open-loop run reproduces all 4 canonical categories at once** — the recorded targets are demo-state-specific, and the contact-rich route (guide しごき, re-grasp-onto-the-actual-cable) accumulates enough state divergence that a fixed-target replay hits either the C1 seat (B0b) or the R re-grasp region (B0a) but not both. This is the honest ceiling of open-loop replay for this route; the pipeline itself is CORRECT + fully exercised. **NO redesign talk** — %12's fork call.

**B0b DoD:** source `b0b_macro_ik_replay` / waypoint_mode `macro_ik(B0b,E14)` / GRASP_YC=+150 / ik_fail 0 / startup E1/E9/E10 / pin-FIRE + C1-held VALIDATED / §4.4 cross-val (C1 legs pass, C2 legs miss-attributed) / 0-diff locked / 層3 PASS / durable `b0b_full/`. video-analyst leg (independent, frames-only) = **CONFIRMS the numeric gross picture**: VERDICT **PHYSICALLY VALID — C1 OK / C2 re-grasp FAIL**. Real grasp+lift (cable lifted aloft, not empty air); **C1 = consistent-with-seated** (cable reaches + stays at the C1/void region, no gross near-miss — corroborates pin-fired/C1-held); **C2 re-grasp MISS CONFIRMED at gross scale** (the R gripper reaches right toward C2 while the cable stays ~one clip-spacing ≈50mm left at C1, visible gripper↔cable gap — confirms R_MISS); no teleport/NaN/explosion/gross interpenetration. Caveats: single low-res panel → sub-cm C1 seat + finger-closure symmetry unresolvable (render non-conservative <1cm; but the ~50mm C2 miss is visibly present, conservative for the gross failure).

**⚠ E7 C2-margin measurement note (%12-flagged):** the C2-seat verdict code (`settled_in_notch` = cable↔C2 ≤0.5mm AND |z−groove|≤3mm + the E7 margin series) is EXERCISED (its C1 twin fired the pin) but has **never been applied at an actually-SEATED C2** in any B0 leg (B0-(i)/B0a/B0b all fail to seat C2). So the **first genuine E7 C2-margin measurement will occur in B1/B2 if/when a rollout seats C2** — recorded here so the first C2-seat is treated as the initial E7 measurement, not a re-confirmation. **%12 fork ruling (E14):** fork-(ii) policy-semantics adoption = NO (diagnostic-only, no new evidence); **B1 = GO** (§8-1 ratified, E13c low-rate prediction stands); SF-B0b-3 (speed_factor unrecorded) → B2 schema-v2 list.

---

## STEP 5 — B1 BC-TRAIN + N=5 POLICY ROLLOUTS (§8-1 ratified) — 0/5 category-SUCCESS (E13c low-rate CONFIRMED); pipeline end-to-end VALIDATED (2026-07-02 15:13 JST)

**Train (`bc_train_route.py` wrapper → locked `bc_pretrain`):** `build_actor_critic(obs=25, act=6, (128,128), cuda:0)` → `train_bc(epochs=100, batch=256, lr=1e-3)` → `save_bc_checkpoint` → `policy.pt` (166,889 B). Converged, no overfit: train_loss 0.013038→**0.000492** (min 0.000483), val_loss 0.006496→**0.000335** (min 0.000335), val≈train both low. `loss_curve.json` (100 epochs) durable in `b1_train/`.

**Rollout (`policy_route_runner.py --policy`):** deterministic MEAN forward — `inference_mode=actor_mean`, `a=policy.actor(obs)` under no_grad (§3), `policy_sha256=2d44158755ac` (identical all 5). waypoint_mode `relative_delta(B1-policy)` / sub_interp `joint_delta_lerp_10frame`. Startup preamble reused (BUG-2 seed + GRASP_YC=**+150.00mm** + E1/E9/E10 shas + DEMO_RECORD=0). N=5 sequential cuda:0 + video.

**⚠ Testing-harness infra fix (X11→EGL, NOT a pipeline change):** the first attempt's rollouts 2&3 hard-died on X11 `BadWindow` (X_SendEvent) — `mujoco.Renderer` (runner:467, `--record-video`) rendered via GLFW/X (DISPLAY=:1, MUJOCO_GL unset) and the Xlib default error handler `abort()`s the process (bypassing the E8 try/finally → no verdict). Re-ran rollouts 2-5 under `MUJOCO_GL=egl` + `unset DISPLAY` (headless EGL, no X path → race eliminated); rollout 1 kept — its verdict is byte-identical under either backend, confirming the renderer is passive w.r.t. physics. Rs-approved the kill+re-run.

**Result — ALL 5 rollouts BYTE-IDENTICAL:** verdict **`BLOCKED_REACH_WALL`** / failure_mode `unseated_pin` / c1_held **False** / pin_fired **False** / regrasp_ok **False**. frames **7700** (E2) / ik_fail **0** / grasp_yc **150.0mm** / artifacts_valid True / obs_parity overall_max **0.113** (within tol, SF-1/6) / tracking max **1.09/1.08mm** R/L (terminal 0.205/0.207mm) / r_reach_resid **95.2mm** / achieved_3d_span **122.9mm** (vs 88.0mm target) / l_grip 0N r_grip 0N / mp4 **14745 B** — *every* field identical across all 5, including the rendered mp4 bytes.

**Category rate: 0/5 SUCCESS** — numeric 0/5 (all BLOCKED_REACH_WALL); video-verified 0 (no SUCCESS to verify → best-failure video-analyst on rollout 1, representative since all 5 identical).

**Per-rollout taxonomy (desync / drift / non-det / converter):**

| bucket | r1 | r2 | r3 | r4 | r5 | attribution |
|--------|----|----|----|----|----|-------------|
| **desync** | — | — | — | — | — | 0/5 — frames exactly 7700 (E2), phases aligned, obs-parity within tol |
| **drift** | ✓ | ✓ | ✓ | ✓ | ✓ | **5/5 PRIMARY** — BC clones relative-delta actions (tracking 1.09mm = faithful to its OWN commanded deltas), but relative-delta accumulates open-loop → R re-grasp target 95.2mm out of reach (reach wall) → span 122.9≠88mm → no grip → C1 unseated → pin never fires → BLOCKED. Same mechanism as B0-(i) |
| **non-det** | — | — | — | — | — | **0/5 observed** — all 5 byte-identical (r_reach_resid/span/tracking/mp4-bytes ALL equal); GPU #562 non-det did NOT manifest for this policy/route on cuda:0 (stronger determinism than SF-B1-4 assumed) |
| **converter** | — | — | — | — | — | 0/5 — obs-parity 0.113 ok, grasp_yc=150 (BUG-1 fix correct), E4' pass, DEMO_RECORD=0 forced |

**Honest shakedown framing:** the B1 pipeline runs END-TO-END and every stage is exercised + validated — converter (raw npz→bc_dataset) → train (converged, val 0.000335) → policy mode (deterministic actor_mean) → 5 rollouts → verdict+video; layer-3 PASS, locked files 0-diff. The policy CLONED the demo well (tracking 1.09mm, low val loss). But BC cloned the **relative-delta action representation**, so it inherits B0-(i)'s open-loop accumulation → reach-wall → **0/5, exactly the E13c low-rate prediction (CONFIRMED as measured, not a surprise).** ⚠ **conservatism direction (GROVE §2.2): 0/5 BLOCKED_REACH_WALL is a CONSERVATIVE FAIL** — open-loop delta accumulation is a genuine failure mechanism that makes the task no *easier* than reality on the reach-wall axis → the FAIL is a definite floor (a relative-delta BC policy does not solve this contact-rich route), banked without needing a high-fidelity re-check. **NO redesign talk** — the residual levers (action representation relative-delta→absolute/closed-loop-corrective; SF-B0b-3 speed_factor; sub-interp fidelity) are %12/B2's call, recorded as B2 schema-v2 items only.

**B1 DoD:** train converged (val 0.000335, loss_curve.json) / policy deterministic (actor_mean, sha 2d44158755ac) / N=5 cuda:0 + video / 5 verdict json durable / category rate 0/5 + taxonomy delivered / GRASP_YC=+150 / ik_fail 0 / E1/E9/E10 shas / obs-parity SF-1/6 / 0-diff locked files (bc_pretrain + route + task_config) / 層3 PASS / durable `b1_train/` + `b1_rollout_{1..5}/`. **Video-analyst leg (best-failure rollout 1, independent frames-only, all-154-frame contact sheet + 22 full-res crops):** VERDICT = **PHYSICALLY VALID (PLAUSIBLE)** — across all 154 frames NO sim-breakdown signature (no explosion / NaN-collapse / teleport / object-disappearance / gross interpenetration); clips fixed, cable continuous. Observed behavior = **grippers stall near the C1-clip region with no large C2 re-grasp excursion = CONSISTENT with the numeric BLOCKED_REACH_WALL** — the failure is a **control/reachability failure, NOT a physics-engine breakdown** (task-fail ≠ physics-INVALID; corroborates that the 0/5 is a genuine relative-delta-drift stall, not a sim artifact). Honest limits (stated by the analyst): single low-res free-camera (action region ≈40×16 px) + very-low-bitrate compression → **pinch / C1-seat / finger-closure symmetry / sub-mm interpenetration are INDETERMINABLE** (render non-conservative at fine scale), and the discrete reach-wall event + arm-span are not visually adjudicable → those stay numeric-only. No table penetration, no arm-slam. ⇒ visual corroboration that B1's 0/5 is a physically-valid control stall consistent with the reach-wall verdict; grasp SUCCESS is neither claimed nor visually certifiable (none present) — per the human-ground-truth rule, any SUCCESS verdict would defer to human, but there is no SUCCESS to adjudicate here.

**⚠ E7 C2-margin (carried from B0b):** no B1 rollout seats C2 (all block at the C1-region reach-wall) → the first genuine E7 C2-margin measurement still pending B2 (unchanged from B0b note).

---

## STEP 6 — E15 A-FORK (absolute-target action representation, fork-(iv)) — CP1-CP5′ COMPLETE; OG gate STOP (structural n=1 integrator ceiling); P2a = fork KILLS the integration drift (Rs A-question = YES) (2026-07-02 20:46 JST)

**Context:** post-B1 (E13c), Rs approved fork-A (absolute-target repr) to test whether replacing the relative-delta action representation removes the integration pathology. Binding = spec §10 E15 v2.2 (5-body debate all-ACCEPT + `/pre-check` R1 BLOCK→R2→v2.2 CLOSED, `E15_PRECHECK_RECORD.md`). L3 chain (stage1 on each diff; 層2/層5 = %12).

**CP1 CONVERTER v1.1:** `--action-repr {delta,abs}` — abs = per-phase(13)×per-axis affine `a=2(wp−lo_p)/(hi_p−lo_p)−1` (lo/hi = in-phase wp min/max ±10% margin; guard-1 v2 widens span<30mm to 30mm midpoint-centered). decode round-trip **6.84e-06mm**; guard-1 58 fires spec-consistent (C1_SEAT/Rz fires, C2_DUAL_SEAT/Rz,Lz no-fire, spec:131 exact). delta trio NOT overwritten (assert-exists + mtime-verified). Outputs `b1p_dataset/` (delta trio + abs pair, obs bundled).

**CP2 TRAIN:** seed-pinned (0) + sidecar (ckpt/dataset sha + repr). ep100 val 0.052 (still-descending at ep100 → underfit signal). **convergence-extension (spec:154, both conditions met, 1-time only):** ep2000 val 0.052→**0.00105** (50× drop, 12s). `policy_abs_e2000.pt` sha 0bdcd284.

**CP3 OG OFFLINE GATE = COMBINED STOP (structural, not underfit):** OG-a ep100 STOP (8 verdict-critical cells, 7-37mm) → ep2000 verdict-critical STOP ELIMINATED (decode <2mm; underfit ruled out) BUT **OG-b γ⊥ = STOP** (C2_REGRASP 1.17; verdict-critical 0.66-0.83) = **the 1-demo abs policy is still an INTEGRATOR** (∂tgt/∂ee≈1 transverse) — the spec-anticipated "n=1 = replay-in-disguise", now measured structurally. OG-b′: seat phases CONTRACT (restoring) / sweep+reach diverge (HOVER→372mm). OG-c slope 0.63. **%12 adjudication:** fail-closed STOP confirmed; residual = n=1 data limit (off-path coverage 0), NOT a repr defect (repr shows decode-fidelity + seat-restoring, properties delta lacks). CP5 pass-bar FORBIDDEN → CP5′ characterization permitted. Durable `b1p_og_e100/`, `b1p_og_e2000/`, `b1p_og_e2000_full/`.

**CP4 RUNNER `--policy-absolute`:** NEW independent abs-decode branch (`decode(clamp(a))` per-phase affine — NOT the B0a cumsum LOOKUP fake-SUCCESS channel) + guard-2 v2 (per-arm 15mm rate-limit) + t=0 canary (<30mm) + repr assert (abs meta + sidecar) + e15 verdict fields. Subagent-built + **owner-verified** (every load-bearing block re-read from disk; a NameError-regression suspicion raised + cleared on-disk; existing delta/B0a/B0b/B1-relative paths byte-unchanged). SMOKE PASS (MUJOCO_GL=egl, 7700 frames, ik_fail 0, canary OK, per_axis_clamp Lx476/Lz480, guard2 102, verdict BLOCKED_REACH_WALL as OG-predicted). Producer post-snapshot `e15_producer_snapshots_postE15/`.

**CP5′ CHARACTERIZATION (N=2 nominal, EGL, ep2000 — purpose-scoped, NOT pass-bar):** P7 deterministic (rollout 1 vs 2 obs+mp4 BYTE-IDENTICAL; verdict differs only in `video_path`). **⭐ P2a (Rs A-question "does absolute repr kill the closed-loop integration drift?") = YES, KILLED:** abs-drift(ee_rollout vs ee_demo) corr(t) NEGATIVE (R −0.42 / L −0.37), spikes 433mm at approach (off-manifold |a|>1) → RE-ANCHORS to 9-16mm final = NOT a monotonic integrator ramp (delta B0-i/B1 showed monotonic accumulation → this is the fork's DEMONSTRATED VALUE). BUT 1-demo → box-scale residual drift (GUIDE_C2/C2_REGRASP L 103mm) → BLOCKED_REACH_WALL (resid 56.1mm, cable↔C1 20.7mm ≫ P4′ band). P6 guard2 102 ≫ OG-a expected ~49 (off-manifold). ik_resid = combined objective cost (position-only variant deferred to B2 verdict-bearing runs, %12 note-11). **video-analyst VALID (PLAUSIBLE) + visually CORROBORATES the spike→re-anchor** (f13-17 upward excursion → f24-33 return to cluster, recurs f64-97; no half-table translation); reach not completed; honest single-low-res limits (sub-cm indeterminable). Durable `b1p5_rollout_1/2/`.

**Disposition (fork-decision evidence, %12 → Rs):** the absolute-target fork (iv) FIXES the integration pathology (P2a bounded + re-anchored, Rs A-question = YES) — structural value DEMONSTRATED — while 1-demo provides no restoring within the phase box (OG-b γ⊥ high) → reach-wall fail. CLEAN SEPARATION: fork fixes integration; restoring = B2-DR multi-demo learning target. P-table = characterization (NOT adopt/revert — the fork-adoption call is Rs's, %12 presents). B2 (schema-v2 + DR) NOT started (its own Rs gate + production-launch-gate + §5.1 wiring). locked 3 files 0-diff; new scripts 0-commit + ruff clean throughout.
