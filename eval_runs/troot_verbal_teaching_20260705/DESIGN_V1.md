# Verbal-Teaching Motion Authoring — DESIGN v1.4 (proposal, paper-only)

**Author:** VT-DESIGN (w2:p5). **Charter:** `CHARTER_V1.md` (Rs 承認 2026-07-05 20:0x).
**Proposed node:** `T-ROOT-Verbal-Teaching-20260705` (parent `T-ROOT`; precedent `T-ROOT-StepTable-Verbal-Teaching-20260703`). Node 起票 = Rs [DEFINE] approval (`CHARTER_V1.md:33`).
**Status:** DRAFT / 0-commit / paper-only. Locked runner `test_newton_clip_routing.py` NOT touched. No new motion invented.
**Rev:** v1.4 = v1.3 + **L3 targeted re-verify** (2026-07-06; FAIL-triggers RESOLVED; 2 new HIGH + 4 MED + 1 LOW folded/recorded; `L3_REVERIFY_RESULT.md`; %12 v1.4-then-PASS 03:11). v1.3 = 5-body L3 debate FAIL→revise (1 CRIT + 6 HIGH). v1.2 = %10 CONCUR. v1.1 = %12 review. See §9.
**Path:** this doc → targeted re-verify (CRIT+6HIGH) → %12 → Rs 設計承認 packet → build (W0-e close 後).

> Concretizes the 07-03 scoping (`STEPTABLE_SCOPING_COORD2.md`). The L3 debate VALIDATED the core (obstacle-B thesis; St1a env-routing; scope discipline) and corrected a CRITICAL 先祖返り risk + three structural mis-framings of what the deviation-detector can enforce — all folded here.

**Path convention:** unqualified code/data paths (e.g. `test_newton_clip_routing.py:3569`, `full_43step.json`) are relative to `thread_isaac_lab/`; `eval_runs/…`, `docs/…`, vault paths are repo-root-relative.

---

## §0. Grounding (anchor set, §運用4)

| Anchor | Cite | Fact used |
|---|---|---|
| Charter | `CHARTER_V1.md:3-5,7-15,17-21,23-33` | goal = teach scripted-route motion in words, minimize round-trips; **offset set = F-1b / F-2 / F-1a *v1*形 = 既存 leg の座標補正 (`:15`)**; INVARIANTS untouched; locked-runner edit = L3+Rs auth |
| Motion standard | `00-DESIGN-STATUS-LEDGER.md:44` | `p2r_c11_route.mp4` = Rs-DECLARED MOTION STANDARD; "no legs absent from reference structure / step-table-first / fixes = coordinate-only / 新動作追加 = Rs 専権"; **W0-e の発明 legs (C1v2-LIFT/SHIFT/TRIM) + F-3 X-shift = 逸脱 → 撤去 2026-07-05** |
| INVARIANTS #1-5 | `RS71-System-Spec-SSOT.md §0` (+ §2 pin = clip-retention only) | #1 DUAL-ARM / #2 88mm span / #3 DiffIK-only / #4 コ LOCK / #5 no-kinematic-trick (pin = the ONE exception, **clip-retention only**) |
| 43-step table | `data/waypoints/full_43step.json` (v2) | 43 steps, 5 clips, phases A/B/C+D/E; per-row targets+finger; **notes 13/21/29/37 "R-hand X=L-hand X"** |
| Deviation detector | `w0e_video_tools/route_leg_diff.py:17,25,30,40,57` | diffs the leg-LABEL sequence of **two run.logs** (`:30` `main(ref,cand)`); matches ONLY `ik_move_both` dist-lines (`LEG_RE:17`); >1mm = coord delta (`:40`) |
| byte-identity basis | `RUN1_REFERENCE_V2.md:3-4,6-9,11,15` | `route_demo_raw.npz` sha `5f1c3f92…`; npz-only compared; `:6-9` loud-supersession lineage; `:15` tri-key = %11/%9/%12 (**CC-only; Rs is NOT a key**) |
| Live route | `test_newton_clip_routing.py:3569` `_run_mujoco_grasp_route` | taught env7 motion; C1→C2 only (`:3571-3580`); 15 recorder phases; hand-written |
| Prior scoping | `STEPTABLE_SCOPING_COORD2.md` (07-03, COORD2/%10) | R1/R2/R3; row schema; options a/b/c; **S-7 primitive vocabulary "nearly enumerated (≈6), fix-⑤ class nearly closed"** |

Prior-art gate CLEARED (differentiator: 07-05 charter = new Rs directive; task = paper 0-commit).

---

## §1. Motivation — the fix-⑤ counterfactual

`full_43step.json` rows 13/21/29/37 carry `note="R-hand X=L-hand X (cable follows L clamp)"` = the fix-⑤ intent, authored ~10 weeks ago; the abs-waypoint schema had no derived-target field → demoted to prose → hand-implemented at a measured **~1.5h + 2 Rs messages** (`STEPTABLE_SCOPING_COORD2.md:15,38`). A schema with a `R.x := cable-X` derived-target primitive makes fix-⑤ a row edit. *The round-trip cost came from the representation, not the robot.* (⚠ this measured case is a NEW-primitive change — St2 territory — not the amplitude class St1a targets; see §7 evidence-gate.)

---

## §2. Current state — 3 representations, byte-id obstacles, param scatter

### §2.1 Three representations (scoping S-1)

| # | Representation | Path | Generative? | Connected to live route? |
|---|---|---|---|---|
| R1 | design decomposition | `RL-Routing-Design.md:1226` | prose | ✗ |
| R2 | abs-waypoint table | `full_43step.json` | ✗ constant targets | ✗ (env6/VBD `dry_run_43step.py:71`) |
| R3 | hand-written live route | `test_newton_clip_routing.py:3569` | ✗ imperative | ✓ (env7) |

**Geometry is current** (per scoping live re-verification `STEPTABLE_SCOPING_COORD2.md:33`; table re-based UR5e+コ, `SOMA.md:312,1035`) — the concern is schema expressiveness (§2.2), not stale geometry. (Param-scatter instance, §2.3: R3's as-run `z_grasp=1.0668` `:3635` overrides the table's descend-z 1.025; **byte-id is defined on the as-run value, not the table's**.)

### §2.2 The route unit + why a static table cannot be byte-identical

R3 "move-leg" = `ik_move_both(target_left, target_right, label, converge_mm, speed_factor)` (`:1929`); it prints the detector's dist-line at `:1971`. Duration DERIVED: `n_steps = max(int(dist*100*STEPS_PER_CM*speed_factor),50)` (`:1960`; `dist` `:1959`; clamp `:1961`). Dual-arm via `tgt(x,z)` (`:3982`), `GHS=0.044`=88mm (INV#2, `:3634`). **Non-move primitives exist and do NOT print a dist-line:** gripper cage-close = substep loops (`:4017-4034`, `_set_gripper_target:2990`), settle = `physics_step` loops, pin = scene op — see §4.4 (they are invisible to the current detector).

Byte-identity obstacles (debate-verified):

| # | Obstacle | Cite | Consequence |
|---|---|---|---|
| B | nominal targets are runtime-MEASURED — `GRASP_YC=np.mean(_near)` runs **unconditionally** on nominal (`:3937-3948`, assign `:3946`) | `:3946` | a row must carry a **target-SOURCE**; static table can never be byte-identical (CC2 VERIFIED) |
| C | gripper close = substep loops (`:4017-4034`); orientation = per-arm register (`:4718-4802`) | — | richer row types (hold-N-steps-at-gripper=r; per-arm orientation) |
| D | npz = `route_demo_recorder.py` (`np.savez :295`, emit `:283-284`), `DEMO_RECORD=1`; **byte-affecting taps = `_ph`/`note_targets`/`_sample`/`note_ik_rot`/`note_grip`/`note_pin` (6, not 4)** | recorder `:283-284,295` | byte-id is behavioral; preserve the 6-tap order |
| E | `W0E_LIFT_M=0.08` = GLOBAL nominal change (`:3642`, comment `:3639`) | `:3642` | keep in table nominal defaults; it is class-B / global (§6 = L3) |

### §2.3 Param-ownership scatter (%12 2026-07-06 01:55)

| Param | Current home | Cite |
|---|---|---|
| C1-C2 spacing (`CLIP2_Y`) | env override | `LEDGER:44`; runner read `:3688` |
| clip x/y (`CLIP_X`/`CLIP_Y`) | env override | `:3645-3646` |
| transport raise (`LIFT_M`) | runner default (env) | `:3642` |
| grasp height (`z_grasp=1.0668`) | runner literal | `:3635` |
| grasp X (`GRASP_X`), span, `STEPS_PER_CM` | `task_config.py` | `:231,235,350` |

---

## §3. W1 — table-driven runner architecture

### §3.1 The route-table row schema (generative)

| Row field | Encodes | Grounded in (R3) |
|---|---|---|
| `primitive` | the verb | `ik_move_both` (`:1929`) \| `cage_close` (`:4017-4034`) \| `settle` \| `grip`/`unclamp` \| `pin` (clip-retention only, §4.3) |
| `target_l/r` **+ `target_source`** | constant vs derived, per arm | `constant` (`x_grasp=GRASP_X:3644`) \| `cable-derived` (caveat-a Y `:3946`, fix-⑤ X `:3970-3978`, argmin) \| `clip-derived` |
| `orientation` (per-arm) | square-on vs tilt-follow. **⚠ C2_REGRASP-arm `inv_binding` = square-on (`C2_TILT_SIGN=0`), Rs-LOCKED** (Rs Q5 2026-07-06 `b7d7857dfc`): tilt-follow is floating-cable-specific & does NOT transfer to the taut C1→C2 route (tilt → "R misses 0N"); a teaching that sets the C2_REGRASP arm to tilt-follow → `BLOCKED_FOR_USER` | `_ROT["L"/"R"]` (`:4718-4719`); **C2_REGRASP lock = `:4678-4681` ANTI-REVERT (`C2_TILT_SIGN` default 0)** |
| `gripper_l/r` | per-arm finger cmd | `GRIPPER_DRIVER_OPEN/CLOSE_RAD` (`task_config.py:289,291`) |
| `gate` | success/advance condition | reach window / `_at_88` / seat-verified pin |
| **`emits_legs`** (NEW, debate finding 3) | the row's DECLARED leg-label list + count | binds the 1:N primitive→leg mapping (§4.4) |
| `amplitudes` | quantitative knobs | **within-leg** (`converge_mm`, `speed_factor` `:1929`) = NON-STRUCTURAL (but **class-B if applied to nominal** — byte-affecting); **sub-leg count** = STRUCTURAL = Rs 専権 (not an amplitude) |
| `inv_binding` | non-negotiable premises | 88mm span, dual-arm, DiffIK-only, no-kinematic-trick |

**Taut-route caveat (%10 #2):** `cable-derived` sources hold under the **taut-route premise** (cable L-clamped); under slack/floating cable they are NOT equivalent → a `cable-derived` row carries an implicit taut-route gate; the parser flags it where the cable is not L-clamped.

**Two orthogonal axes (debate finding 17 + re-verify N3):** (i) **structural?** = does the edit change the leg COUNT — `speed_factor`/`converge_mm`/`n_steps` are **NON-STRUCTURAL** (leg count unchanged); **sub-leg counts** (`N_ROUTE` `:3647`, `LIFT_SUBSTEPS` `:4042`, descend-loop `:4010 range(1,9)`) are **STRUCTURAL** (`route_leg_diff.py:25` normalizes `k/N` → a count change → STRUCTURE-DEVIATES = Rs 専権). (ii) **class-A vs class-B?** = does it change the nominal sha — a NON-structural within-leg change to the NOMINAL route IS byte-affecting (`n_steps` scales frames → sha) = **class-B**; it is class-A only when offset-gated. So `speed_factor` on nominal = non-structural BUT **class-B** — NOT a "class-A amplitude."

**Row↔leg is 1:N, not 1:1 (debate finding 3):** one primitive emits N legs via code loops/flags. So "row list = leg sequence" is false; instead each row DECLARES `emits_legs`, and a mechanical assertion (§4.4) binds primitive output to the declaration. Adding/removing a row OR changing a row's declared leg-count = new motion = Rs 専権.

### §3.2 Param-ownership consolidation (target end-state)

- **Target:** route-table = the single authoritative home for as-run route params; `task_config.py` = physics/robot constants only; env overrides + runner literals fold in.
- **Delivered incrementally (debate finding 20):** **St1a REDUCES scatter** (env params `CLIP2_Y`/`CLIP_X`/`CLIP_Y`/`LIFT_M` → table), but **runner literals (`z_grasp=1.0668 :3635`) stay in R3 under St1a** — so "single home" is a **St1b+ property**, not delivered by the recommended-first stage.
- **Migration invariant:** folded nominal values MUST reproduce `RUN1_REFERENCE` latest (byte-id test §3.4).

### §3.3 Staged architecture (St1a first + evidence-gated; St1b/St2/St3 DEFERRED)

**Per the L3 NHA (findings 6/7): the near-term candidate is St1a, and its build is evidence-gated; St1b/St2/St3 are deferred on measured triggers — NOT presented as a roadmap to adopt now.**

| Stage | Build | route code | byte-id | status |
|---|---|---|---|---|
| **St1a — external param layer (launch-wrapper)** | route-table nominal → the env params R3 reads, via a **launch-wrapper** (env exported before runner exec — R3 reads env at call time, `:3642/3645/3646/3688`); + row-diff→gate machinery | R3 **untouched** | **trivial ONLY IF the FULL nominal env is reproduced** (the **exact enumerated nominal env set** — §11 build-time N5 — + `NEWTON_DEVICE=cuda:0`; the 4 owned params are necessary-not-sufficient; canonical route is cuda:0-conditional, [[project-canonical-route-device-fragile]]) | **near-term, evidence-gated (§7)** |
| St1b — locked-file table-read shim | R3 reads per-leg literals (`z_grasp`, per-leg `speed_factor`) from the table | R3 **min-edit** | re-proof required | **DEFERRED** — L3 + **Rs explicit auth** + byte-id re-proof; only if a param is proven un-env-routable |
| St2 — schema enrichment + fix-⑤ proof | derived-source rows; fix-⑤-as-row | R3 edit | behavioral | **DEFERRED** — L3 + Rs auth; gated on ≥2 measured new-primitive needs |
| St3 — generative (b codegen / c interpreter) | table generates legs | route artifact | (b) file-sha / (c) npz-behavioral | **DEFERRED** — L3 + Rs auth; gated on St2 measuring the primitive set OPEN |

**St3 "structurally impossible" → tempered (finding 3):** a generative runner does NOT make invented legs *impossible* (a primitive can internally emit LIFT/SHIFT/TRIM — exactly the charter's `:9` invention). It makes them **structurally DETECTED + generation-time rejected** via the §4.4 table→leg-count assertion + primitive audit. (b)-vs-(c) = Rs decision (D-2), deferred to St2 evidence:

| axis | (b) CODEGEN | (c) INTERPRETER |
|---|---|---|
| artifact | reviewable generated `route.py` (lockable) | table + engine |
| byte-id fit | file-sha | **npz-behavioral (matches RUN1_REFERENCE natively)** |
| migration cost | medium-high | highest (re-verify ALL banked) |
| migration safety | **incremental** (static per-phase pre-sim check) | **all-or-nothing** (runtime behavioral parity) |
| Rs-LOCK | lock row+template | lock row+primitive |

**Fallback rail:** St1a (R3 untouched) is retained as a **permanent** byte-id-safe path even if St3 ever lands.

### §3.4 byte-identity migration proof plan

- Artifact = `route_demo_raw.npz` (`np.savez :295`), `DEMO_RECORD=1`; **npz sha only** (`RUN1_REFERENCE_V2.md:11`); %12 recomputes from raw.
- Test = table-driven nominal (class-A teaching-null, **FULL nominal env incl. cuda:0**) → sha == `RUN1_REFERENCE` latest (version-independent).
- St1a = trivially passes **given the full env**; St1b/St2/St3 = behavioral re-proof (preserve the 6-tap order, obstacle D).

---

## §4. W2 — verbal teaching loop

### §4.1 Instruction vocabulary → table param

`consumed-by`: **scene** = feeds clip geometry → all legs at that clip; **leg** = local; **global** = all legs of a phase / nominal-changing (→ L3, §6).

| 指示 | param → field | consumed-by | R3 cite | stage |
|---|---|---|---|---|
| 「間隔を倍に」 | clip spacing (`CLIP2_Y`) | **scene** | `LEDGER:44`; `:3688` | St1a |
| 「クリップを動かす」 | clip xy (`CLIP_X`/`CLIP_Y`) | **scene** | `:3645-3646` | St1a |
| 「もっと持ち上げて」 | lift (`LIFT_M`) | **global** (all transport legs, nominal-changing) | `:3642` | St1a |
| 「真上から降ろす」 | approach xy | leg (scene if clip moves) | `:4003` | St1a |
| 「もっと深く押し込む」 | seat z | leg (per-leg literal) | `:4205,4828` | St1b/St2 |
| 「ゆっくり／速く」 | `speed_factor` (within-leg) | leg (per-leg literal) | `:1929,1960` | St1b/St2 |
| 「右手をケーブルに合わせる」 | `R.x:=cable-X` (target_source) | leg | notes 13/21/29/37; `:3970-3978` | St2 |

**「間隔」referent gate (debate finding 12):** 「間隔/spacing」 denotes BOTH clip-spacing (allowed) AND grasp/arm span (INV#2, Rs 専権; RS71 §1 calls the 88mm span "spacing"). The parser MUST resolve the referent (clip vs grasp/arm/EE) BEFORE mapping; a grasp/arm/EE-span referent → INV#2 `BLOCKED_FOR_USER`, never bound to `CLIP2_Y`.

### §4.2 Teaching loop — class-A / class-B (corrected)

**class A = offset/param-gated, nominal PRESERVED.** ⚠ **The legitimate offset set is EXACTLY `{F-1b, F-2, F-1a *v1*形}` (coordinate-offset on existing legs, `CHARTER_V1.md:15`).** An offset that **adds/removes any `ik_move_both` leg** (e.g. **F-1a *v2*** = C1v2-LIFT/SHIFT/TRIM, `:4242-4268`) or is a **removed deviation** (**F-3**, `:4835-4867`; both 撤去 2026-07-05, `LEDGER:44`) is **NOT class-A — it is STRUCTURAL = Rs 専権** (debate CRITICAL; treating them as routine class-A would re-introduce the exact 先祖返り the charter prevents).

**class B = base-motion 修正, nominal CHANGES (what Rs actually does):** e.g. 今日の 「間隔を倍に」→`CLIP2_Y=0.000`, 「かすり修正」→`LIFT_M 0.05→0.08` (`RUN1_REFERENCE_V2.md:9`).

Loop:
1. **Rs 言葉.**
2. **CC map + classify:** (i) INVARIANT-touching (incl. grasp-span referent, §4.1) → `BLOCKED_FOR_USER`. (ii) **leg-adding/removing / removed-deviation (F-1a-v2, F-3)** → structural = `BLOCKED_FOR_USER` (Rs 専権). (iii) else class A (offset) or class B (base). Unknown verb/object → `BLOCKED_FOR_USER`.
3. **Reachability (debate finding 16; split per re-verify N4):** (pre, STATIC) a `/geometric-design` reach-envelope check on the new coordinate (§6) — but this CANNOT pre-detect the device-fragile reach-wall (`n_steps`/`MAX_MOVE_STEPS :1961`/residual `:4090` are RUN-TIME, and the wall flips cpu vs cuda:0, [[project-canonical-route-device-fragile]]); (post, at step 5) a **post-run** reachability catch reads the residual / clamp-hit → if unsatisfiable coordinate-only → `BLOCKED_FOR_USER` (structural = Rs), never silently accept a clamped motion. So reachability = a static envelope pre-filter + a load-bearing post-run catch, not a full pre-check.
4. **Edit the row** — coordinate/param only, `emits_legs` unchanged.
5. **Regenerate + mechanical verify:**
   a. **table→run gate (§4.4, ordered-multiset)** — executed leg SEQUENCE == the table's declared `emits_legs` (order + multiplicity); at St1a this covers `ik_move_both` legs ONLY (§4.4 limitation).
   b. **leg-diff** (`route_leg_diff.py`, **run-vs-run regression guard ONLY**) SAME-STRUCTURE, diffing the `p2r_c11` **run.log** (not the `.mp4`).
   c. **byte-id sha, class-branched:** class A → nominal sha UNCHANGED (a change = bug). class B → sha CHANGES (expected); freeze is **PROVISIONAL** (see below).
   d. **reference-diff 2-pass video** vs `p2r_c11` (structure + motion-quality). **⚠ leg-diff + sha guard STRUCTURE + nominal-drift ONLY, NOT coordinate motion quality** — F-3 (a removed deviation) passes BOTH gates yet is counterproductive (`LEDGER:44`); so the **video + Rs leg is LOAD-BEARING, not automatable-away**.
6. **Rs 確認** (authorizing).
7. **class-B commit (debate finding 2 + %12; hardened re-verify N6/N7):** the new `RUN1_REFERENCE` freeze is effective **ONLY after the step-6 Rs authorizing confirmation** (Rs = the required authorizing key for standard supersession — the CC tri-key `:15` validates sha INTEGRITY, not motion CORRECTNESS). Until Rs confirms, the step-5 regenerated `route_demo_raw.npz` is **quarantined in a non-canonical path** (NOT the RUN1_REFERENCE location) so no downstream / parallel pane can consume it as the standard (§11 N6). On Rs confirm → freeze + **same-turn LEDGER:44 annotation citing Rs's verbatim confirmation + timestamp** (not a bare CC assertion; §運用15c) + sha lineage per §運用4; `p2r_c11` stays the FROZEN structure+quality reference. **Honesty note:** the current `RUN1_REFERENCE_V2` freeze is a **precedent-WITH-caveat** — frozen via the CC tri-key before an explicit Rs re-declaration of the new base as the standard; v1.4 **formalizes the correct order** (Rs key up front → freeze → LEDGER), which the V2 precedent did not follow.

**Round-trip ≤ 1:** steps 2-5 are mechanical/automatable; **steps 5d/6 (video + Rs) remain human + load-bearing** — the efficiency claim is on the authoring turns, not on removing the Rs confirm.

### §4.3 Fail-loud parser + generation-time gates

- Unknown verb/object/condition = STOP + `BLOCKED_FOR_USER` (fail-closed).
- INVARIANTS rejected at generation time (single-arm INV#1 / span≠88 INV#2 / non-DiffIK/teleport INV#3/#5) → `BLOCKED_FOR_USER`.
- **pin = clip-retention SEMANTIC, not the token (debate finding 11):** RS71 §2 authorizes the pin ONLY for clip-retention (cable seated at a clip). Every `pin` row carries a **mandatory seat-AT-CLIP gate**; a pin not gated on a clip-seat → `BLOCKED_FOR_USER`. `ピン留め` is the ONLY physics-bypass token, AND only when clip-seat-gated.

### §4.4 Structural enforcement — what makes step-table-first MECHANICAL (debate findings 3/4/5; staging corrected re-verify N1/N2)

The v1.2 claim that `route_leg_diff.py` enforces step-table-first was WRONG: leg-diff compares two **run.logs** (`:30`), never the table, and matches ONLY `ik_move_both` dist-lines (`LEG_RE:17`). It is a **run-vs-run regression guard**. Step-table-first needs three additions — **with an honest stage split (re-verify N1):**

1. **All-primitive structural tokens (St1b — locked-runner edit, L3 + Rs auth):** grip/settle/pin print NO parseable token today (`_set_gripper_target:2990` writes only the recorder; settle = inline `physics_step` loops). Emitting `[LABEL] event=…` for them requires editing the LOCKED runner = **St1b, NOT St1a.** Until St1b, these primitives stay sequence-invisible.
2. **Per-row leg-count declaration + primitive audit (St1b):** each row declares `emits_legs`; a mechanical assertion checks the primitive emits EXACTLY the declared legs (bounds the 1:N mapping so invention can't hide inside a primitive). This audit ships with the St1b/St2/St3 runner instrumentation.
3. **table→run gate — ordered-multiset / sequence equality (re-verify N2):** parse the executed leg SEQUENCE and assert it == the table rows' declared `emits_legs` **preserving order AND multiplicity** (NOT a set/union — `route_leg_diff.py:25` normalizes `k/N`, so a set-union is BLIND to an `N_ROUTE` 6→8 sub-leg-count change, the exact deviation to catch). This — NOT leg-diff — enforces "no legs absent from the table structure." leg-diff remains, scoped to run-to-run regression.

**⚠ St1a limitation (explicit — the blind spot is NOT hidden, re-verify N1):** at St1a (R3 untouched) the table→run gate can consume ONLY the already-emitted `ik_move_both` legs. So under St1a a moved / added / dropped **grip / settle / pin** passes as SAME-STRUCTURE — **including a moved/added pin, which is INVARIANT #5's SOLE authorized kinematic exception.** St1a therefore guards `ik_move_both`-leg structure + run-regression; **full step-table-first (grip/settle/pin-move detection) is DEFERRED to St1b** (runner instrumentation). This limitation is a reason St1a is *minimal*, and it is surfaced, not hidden.

---

## §5. DoD mapping (`CHARTER_V1.md:23-27`)

| DoD | Satisfied by | Stage |
|---|---|---|
| 0 (added, finding 18) — establish the discipline-only baseline | run the 3 examples via existing env-override + `route_leg_diff.py` + sha; St1a's value = the **measured gap** over this | pre-build |
| 1. 実例 3 本 ≤1 往復 | §4.1 rows + §4.2 loop; pick **env-routable** examples (spacing/clip/lift = St1a); 降下速度 = St1b/St2 | St1a (+St1b) |
| 2. leg-diff SAME-STRUCTURE (run-regression) + **table→run gate** (ordered-multiset) | §4.4 — at St1a scoped to `ik_move_both` legs; full all-primitive incl. **pin-move = St1b** | St1a (ik_move) / St1b (full) |
| 3. nominal byte-id (**class-A only**) | class-A sha guard (§4.2-5c) | St1a |
| (+) fix-⑤-as-row proof | notes **13/21** (C1→C2 scope; 29/37 under D-3) | St2 (deferred) |

### §6. Gates, L-triage, build sequence

- Build after W0-e close.
- **L of a build:** St1a = new external module + launch-wrapper (no locked-runner edit). St1b/**St2/St3 = locked-runner edit = L3 + Rs explicit auth + byte-id re-proof** (debate finding 13 — St2/St3 carry the same tag as St1b, not a bare "→L3").
- **L-triage of a table edit (debate finding 14):** amplitude-within-leg non-critical = L1; **scene-consumed OR GLOBAL (LIFT_M) OR class-B (nominal-changing) OR verdict-critical phase = L3.** (Added a GLOBAL bucket — LIFT_M is global, not "leg".) verdict-critical = C1_SEAT/C1_PIN/C2_REGRASP/C2_DUAL_SEAT/C2_SETTLE; **grasp/clamp params are non-teachable (constant-only) by design** (GRASP_X = `constant`), so absent from the vocabulary — if ever exposed → L3 (finding 23). The table-edit TOOL = core infra = L3.
- Build-time orthogonal gates: `/geometric-design` (new coordinate — wired into §4.2-3); `/diffik-trajectory` (trajectory change).

### §7. Rs decision points

- **D-1 (revised per L3 NHA + re-verify N3):** adopt **St1a as the near-term candidate, evidence-gated**; **St1b/St2/St3 DEFERRED**, each on a measured trigger. ⚠ **St1a's 4 params ALREADY carry runner env-overrides** (`CLIP2_Y :3688`, `CLIP_X :3645`, `CLIP_Y :3646`, `LIFT_M :3642`) — so its DoD-1 examples are already one-shot env edits today (DoD-0); **St1a's value is param-address ORGANIZATION (single-home for the env subset) + the row-diff gate, NOT a new edit capability.** **St1a build precondition:** (a) a measured **scene/global param-edit** baseline showing today's cost >> minutes (§運用18), AND (b) a demonstration that the discipline-only path (DoD-0, existing env-override) does not already meet ≤1-round-trip. If (a)/(b) show ≈0 gap, **HOLD St1a**.
- **D-2:** St3 (b) vs (c) — deferred to St2 evidence.
- **D-3:** scope = C1→C2 (charter); full-5-clip = later separately-validated.
- **D-4:** Rs-LOCK semantics for St3.
- **D-5:** `/web-research` on skill-DSLs before St3? (recommend internal precedent).
- **D-6:** 3 DoD examples as class-A offsets or class-B base changes? (recommend ≥1 of each; class-A must use the `{F-1b,F-2,F-1a-v1}` set, NOT v2/F-3).
- **D-7 (new):** class-B reference supersession requires **Rs as the authorizing key** + same-turn LEDGER:44 (§4.2-7) — Rs to ratify this governance addition.

### §8. Reuse-first + conservatism

**Reuse:** byte-id sha pattern / §運用14 video legs / OG offline gate / RobotTAS baseline-hash guard (env6/VBD — patterns only, re-target env7) / **RUN1_REFERENCE loud-supersession lineage** (`:6-9`) = the class-B base-update procedure.

**Conservatism (§運用15):** cost/efficiency figures = 推測 (only fix-⑤ ~1.5h measured — and it is a NEW-primitive change, NOT St1a's class; St1a ROI is unmeasured → evidence-gated, D-1). Byte-id direction: **St1a = conservative** (R3 untouched, given full env); St1b/St3 reproduction = the risk (hard FAIL). **Mechanical gates (leg-diff+sha+table→run) guard STRUCTURE only; coordinate motion-quality → video + Rs remain load-bearing.** The L3 debate (1 CRIT + 6 HIGH folded) is the record of this doc's hardening. paper-only / 0-commit.

### §9. changelog

**v1.4 (L3 targeted re-verify — 2 new HIGH + 4 MED + 1 LOW folded/recorded; `L3_REVERIFY_RESULT.md`; %12 v1.4-then-PASS 03:11):** N1 §4.4 all-primitive tokens re-staged to St1b + **explicit St1a pin-blind limitation kept visible**; N2 table→run gate = ordered-multiset/sequence (not union); N3 amplitude = non-structural axis (orthogonal to class-A/B) + class-B when nominal + St1a value = organization-not-capability; N4 reachability = static envelope + post-run catch; N7 dropped the unsupported "shown to Rs" softener; N5/N6 → §11 build-time.

**v1.3 (5-body L3 [VERIFY] debate FAIL→revise, 2026-07-06; `L3_DEBATE_DECIDE.md`; %12 GO 02:49):**

| finding | Change |
|---|---|
| **CRIT** (CC4) | §4.2 class-A restricted to `{F-1b, F-2, F-1a-v1}`; F-1a-v2 (LIFT/SHIFT/TRIM) + F-3 explicitly EXCLUDED as structural/removed-deviation = Rs 専権 |
| HIGH class-B freeze (CC2+CC3) | §4.2-7 freeze PROVISIONAL until Rs authorizing key + same-turn LEDGER:44; V2 precedent-with-caveat honesty note |
| HIGH leg-diff=run-vs-run (CC4) | §4.4 table→run gate added; leg-diff scoped to regression guard |
| HIGH 1-primitive→N-legs (CC4) | §3.1 `emits_legs` field + §4.4 primitive audit; "structurally impossible" → "structurally detected + rejected" |
| HIGH grip/settle/pin invisible (CC4) | §4.4 all-primitive structural tokens |
| HIGH St1a ROI unmeasured (CC6) | §7 D-1 evidence-gate + §5 DoD-0 baseline |
| HIGH St2/St3 nearly-closed (CC6) | §3.3 St1b/St2/St3 DEFERRED on measured triggers |
| MED×~12 | St1a launch-wrapper + full env + cuda:0 (§3.3); pin clip-semantic (§4.3); 間隔 referent (§4.1); L-triage GLOBAL (§6); St2/St3 Rs-auth tag (§6); reachability branch (§4.2-3); substep-count split (§3.1); coordinate-quality caveat (§4.2-5d); note_grip/pin taps (§2.2 D); single-home qualification (§3.2); St1b via env-example (§5) |
| LOW×~7 | 6 citation fixes (GHS:3634, z_grasp:3635, CLIP_X/Y:3645-3646, CLIP2_Y:3688, R.x:3970-3978, np.savez:295); class-B run.log; verdict-critical grasp; St2 note-scope 13/21 |

Prior: **v1.2** (%10 CONCUR — taut-route caveat / geometry / path). **v1.1** (%12 review — St1a/b split / class-A/B / consumed-by / n_steps:1960).

### §10. Re-verification (COMPLETED)

Targeted re-verify (CC1, %12-approved; RV1 fix-adequacy + RV2 adversarial-on-new-mechanisms; `L3_REVERIFY_RESULT.md`): the CRITICAL + 6 HIGH FAIL-triggers were confirmed **RESOLVED** (RV1 7/7; RV2 code-confirmed the class-A restriction). The 2nd pass surfaced **2 new HIGH + 4 MED + 1 LOW** from the rework (all bounded); per §運用15 these were surfaced to %12/Rs, and %12 adopted **v1.4-then-PASS** (2026-07-06 03:11). v1.4 folds N1/N2/N3/N4/N7 (above); N5/N6 → §11.

### §11. Build-time spec items (recorded; do NOT block the design)

- **N5 — exact nominal env enumeration:** the launch-wrapper's byte-id correctness requires the EXACT set of env vars whose nominal value ≠ the runner `os.environ.get` default (86 read sites). At build: grep every nominal-path `os.environ.get`+default; enumerate the vars whose `RUN1_REFERENCE_V2` value differs (≥ `CLIP2_Y=0.000`, `W0E_LIFT_M=0.08`, `NEWTON_DEVICE=cuda:0`); St1a byte-id is contingent on that explicit list.
- **N6 — class-B freeze artifact mechanics:** implement the step-5 npz quarantine (non-canonical staging path until Rs step-6) + the Rs-verbatim-cited LEDGER:44 annotation (§4.2-7) as concrete build artifacts.

*VT-DESIGN (w2:p5) — DESIGN v1.4 draft.*
