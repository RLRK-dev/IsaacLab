---
title: GD — KO-shape (C-bracket) single-claw finger (BANKED 2026-06-21 CPU building-block — SHAPE/LIFT/しごき/place/mid-air/clip-insert human-confirmed; GPU + full-route/snag-retention + R2/R3 = production-pending)
created: '2026-06-20'
owner: T-ROOT-COORD (recorded per human directive 2026-06-20 「vaultに記録」)
status: BANKED (CPU building-block, Rs source-GO 2026-06-21; GPU R-S6.6 + full-route/snag retention + R2/R3 §運用14 = production-pending) — SHAPE + LIFT + しごき + PLACE + MID-AIR RE-GRASP (tilt-follow) + CLIP-INSERTION (drop-in onto REAL collidable clip B) all human-CONFIRMED (2026-06-21); recipe = vertical descend + −4mm both-arms [human-preferred] + gradual lift; mid-air re-grasp = LEFT-tilt-follows-cable + gap10; clip-insertion = lower claw into the mouth (REL_CABLE_Z 0.820) then release → re-seats 809; CPU/visual/full-clamp; BANKED 2026-06-21 (CPU building-block, Rs source-GO); grip-robustness/GPU/real-clip = production-pending
tags: [design, gripper, finger, ko-shape, C-bracket, R-S7.1, option-E, banked]
---

# GD — KO-shape (C-bracket) single-claw finger

**What this is.** A human-directed (2026-06-20) exploration: REMOVE the V-groove ◇ and make the gripper
finger a コ (⊏) so the left/right pads' claws wrap the cable on all sides incl. the bottom (intended to
close the ◇'s open bottom = the verified lift-fail root). Built on a SCRATCH asset; the committed ◇ is
UNTOUCHED.

## ⚠ CONSISTENCY CAVEATS (records-must-match-fact — read FIRST)
- **⛔ 2026-06-21 (human decision): the ◇ V-groove is DISCARDED as a design reference** — NOT retained, NOT locked (this SUPERSEDES the "retained as up-cap/drag reference" framing elsewhere in this doc). Active finger = コ. ⚠ records-ahead-of-code: the committed asset `2f85_tendon_stripped.xml` (`7afa84b463`) still physically contains the ◇ + コ is unwired scratch → ◇→コ asset swap = deferred L3. Reflected on-disk: RS71-SSOT §0 INVARIANT 4 + §5/§6, LEDGER:50/51, Gripper-VGroove status:5 (SOMA:80/87 + this doc's deeper body = deferred reconcile). (5体 [VERIFY] gated this: bare "DISCARDED" over-claims vs the running ◇ → recorded as "discard DECIDED, asset swap pending".)
- **This REMOVES the V-groove** (which the prior banked spec called 100% mandatory). **✅ コ is now BANKED
  2026-06-21 (Rs source-GO) — V-groove SUPERSEDED→コ across the authoritative specs** (LEDGER:50/51, RS71-SSOT
  §5/§6/LOCK, SOMA:80/87, Gripper-VGroove banner+:18/:22; applied by %9 per the human's explicit authorization,
  after a %2 cross-PV CONDITIONAL-PASS whose conditions were met). コ banks as a **CPU-verified building-block**;
  GPU R-S6.6 + full-route/snag retention + R2/R3 §運用14 = production-pending.
  - **⚠ UPDATE 2026-06-21 21:09 — Rs source-GO to BANK コ GRANTED** (human directive "コ を BANK 承認"). Banking
    package = `eval_runs/troot_optE_rs71_kinematic_retention_20260616/R_S71_KO_BANKING_PACKAGE_78.md` (the exact
    atomic LEDGER + Gripper-VGroove + RS71-SSOT + SOMA supersession edits). コ banks as a **CPU-verified
    building-block** (penetration/crush + retention + grip-down clamp **0.69**, %2 cross-PV CONVERGENT 0.001mm;
    2026-06-17 5体 crush CRITICAL retired); **GPU R-S6.6 + R2/R3 §運用14 visual = PRODUCTION-pending** (same
    caveat as the banked-(A) lift). The authoritative LEDGER / 07-Design / 04-Specs flip is **APPLIED 2026-06-21**
    (%9 per the human's explicit apply-authorization; %2 cross-PV CONDITIONAL-PASS conditions met: content-match
    apply + retention-residual caveat + Gripper-VGroove:18/:22 inline flags; post-apply re-grep = 0 stale residual);
    this doc's `status:` is now **BANKED**. Clamp **0.69** supersedes the proposed 0.667 (numeric landing in
    `task_config.py` = separate L3 + Rs source-GO).
- **The コ path was already 5体-DEBATE FAILED 2026-06-17** (`DISPATCH_12to18_COCAGE_5TAI_FAIL_CONSULT_2026-06-17.md`:
  1 CRIT + 5 HIGH; crush/penetration, open-top up-escape, "pad"-solref NaN relocation, axial-friction-only on
  a no-stick substrate). The findings below are consistent with that FAIL.
- **SCRATCH only / CPU / full-clamp.** Committed ◇ asset untouched (git clean).

## Geometry (SCRATCH asset `assets/ur5e_robotiq/robotiq_2f85/2f85_koshape_scratch.xml`; gen `r_s71_make_koshape_asset_48.py`)
Per pad, ONLY two geoms (S1 cage f1up/f1lo/lip + V-groove vgu/vgl REMOVED):

| geom | role | pad-local pos (m) | size (half, m) | quat | color |
|---|---|---|---|---|---|
| `*_pad_f1ext` | BOTTOM claw (the existing L-foot, enlarged) | 0 −0.0026 0.0382 | 0.011 **0.009** **0.0012** | 1 0 0 0 | red |
| `*_pad_f2ext` | TOP claw (z-mirror of f1ext) | 0 −0.0026 ~0.0258 | 0.011 **0.009** **0.0012** | 1 0 0 0 | blue |

- pad-local **Y = world X (closing axis, toward cable)**; pad-local Z = world Z (vertical); pad-local X (0.011 = 22mm) = along the cable (world Y).
- **`half_y` 0.004 → 0.009** = the FIX (human 2026-06-20 「上下のつめが出ていない」): the original claw was FLUSH
  with the pad face (inner X ≈ pad face ≈ 302.8mm); enlarged it PROTRUDES (`dimX` 8→18mm, inner edge ≈ 298mm)
  past the cable centre to WRAP the Ø8 cable.
- Gap between the two claws ≈ 10mm (Ø8 + 2mm). At the grasp pose: f1ext Z≈796.6 (BELOW cable), f2ext Z≈809
  (ABOVE cable), cable Z≈800-808 between them.

## Findings
- **✅ SHAPE — the コ forms (human-CONFIRMED 2026-06-20 「ok」).** Both claws protrude toward the cable and
  wrap it top+bottom; the two pads close into a □ (close-up `~/Downloads/r_s71_claw_closeup.png`).
- **✅ LIFT — ACHIEVED 2026-06-21 with a refined recipe (human-CONFIRMED «成功» via video).** Both hands
  grasp the cable and lift it **~45mm roughly LEVEL** (no scoop, finger vertical). RECIPE
  (`r_s71_vertical_grasp_56.py`, CPU env7, full-clamp): **(1) VERTICAL descend** straight down at GX — drop
  the sideways slide that was scooping (a tilted claw sliding in levers the cable up; a vertical claw does
  not); **(2) lower the descend-end z by −3 to −4mm** (`z_grasp = ZE+0.009 .. +0.008`, BOTH arms) so the FAR
  (LEFT) hand also reaches the cable — **human insight 2026-06-21**: the L/R reach lag left the far claws
  above the cable; −3 and −4mm are EQUIVALENT (both → both-arm capture + level lift), **−5mm (ZE+0.007)
  FAILS** (claws end ABOVE the cable 806-808, no capture; the cable rising to 864 there is a push-up artifact,
  NOT a grip) ⇒ **sweet spot −3..−4mm, do not go deeper** (autonomous depth-judge `r_s71_depth_judge_59.py`,
  judged by per-arm CAPTURE not finger-tilt). **−4mm is the human-PREFERRED/CHOSEN depth** (2026-06-21 00:32
  «明確に判断できないが今回(−4mm)のほうがよい») — the per-arm-capture metric rated −3≈−4 EQUIVALENT, so the
  human's EYE distinguished a subtle improvement the numeric did NOT = another **human-visual > numeric** case; **(3) lift in 12 GRADUAL sub-steps** (a single 50mm move slipped
  = empty rise; the gradual lift HOLDS the cable). Measured: cable 804→849mm (+45), finger-tilt 0.0 deg,
  cable level on table through close (no scoop). Human confirmed from `~/Downloads/r_s71_vertical_grasp.mp4`
  (41-frame dense). Level lift (not one-sided) = both hands hold.
- **⚠ CORRECTION 2026-06-21 — tilt+scoop is REAL and human-ACCEPTED (NOT "vertical/no-scoop"):** the human
  clarified «tilt+scoop 許容している。なぜならフィンガ機構自体が垂直制御不可能だから» — the 2F-85/コ CLOSE
  mechanism inherently tilts the pads (cannot be made vertical by IK or descend tuning), so a residual
  tilt+scoop is INHERENT and the human ACCEPTS it. **The earlier "finger-tilt 0.0 / no scoop" numeric was
  UNRELIABLE (missed the real residual tilt+scoop — same metric-failure as all session).** ⇒ SUCCESS is judged
  by the OUTCOME (both-arm capture + level lift), NOT by tilt/scoop. The "vertical descend (drop the sideways
  slide)" + "−4mm" + "gradual lift" recipe still HOLDS as the success recipe — it just does NOT make the grasp
  perfectly vertical/scoop-free (mechanically impossible); it makes the OUTCOME succeed (both hands capture +
  level lift). Do not over-claim "vertical/no-scoop" anywhere downstream.
- **⚠ Conservatism / caveats (UPDATED 2026-06-21 — CPU contact-physics now VERIFIED; GPU still pending; do NOT over-claim).**
  Verify-first (%9 probe 73/74 + %2 independent cross-PV, doc `eval_runs/troot_optE_rs71_kinematic_retention_20260616/R_S71_KO_GRASP_VERIFY_FIRST_VERDICT_73_74.md`):
  - **penetration NOW QUANTIFIED — NO 5体 crush:** deepest **1.06mm (CLOSED) / 1.39mm (LIFTED)** vs the 2026-06-17
    5体 4.8mm crush class (3.5–4.5× under). Contact channel **LIVE** (`can_collide=True`, 14–17N real force, not
    inert) → **NOT a penetration-looks-like-grip artifact**. Committed `MUJOCO_PAD_SOLREF`=[−65789,−2105.3]
    confirmed ACTIVE (the asset's `solref="0.004 1"` is overridden by the `_wire_s6_grasp_solref` poke,
    `test_newton_clip_routing.py:2585`) → matches the banked-(A) contact model. Grip = **COMPOSITE**: lateral
    flat-pad (`pad1`) pinch [dominant, −1.06/−1.39] + vertical claw (f1ext/f2ext) straddle [−0.7]; **f1ext bottom
    claw engages under lift load** = the open-bottom catch the V-groove lacked (the コ rationale, CPU-supported).
    %9 (`mphd.contact.dist`) ⇆ %2 (`mj_geomDistance`, solver-independent) agree to **0.01mm** on 2 independent
    primitives (§運用28 CONVERGENT).
  - **RETENTION (X+Z load axes) NOW TESTED (CPU):** HOLD 200 steps sag 0 (848→850mm) + lateral ±8mm EE wiggle
    holds (no drop). Axial Y = out-of-scope by design (through-cable topological; clip-pin downstream).
  - **grip-force NOW MEASURED:** ~76–153N/arm (lift needs <1N) = over-squeeze, SAME regime as banked-(A) (within
    the 2F-85 ≤235N envelope, non-blocker) → grip-DOWN tuning recommended (also shrinks penetration + GPU-NaN risk).
  - **STILL UNVERIFIED (hard gate):** GPU (R-S6.6, env7 mjw non-det NaN, `SOMA.md:83`) — penetration MAGNITUDE
    (1.39 > 1.1mm ref by 1.26×) + grip force are **NON-conservative ×3** (CPU vs GPU); GPU verify + grip-tune
    before PRODUCTION. **FULL-clamp** (NOT the step-table half-clamp ◇, `RS71-System-Spec-SSOT.md:50`). The コ
    remains **UN-BANKED** vs the FROZEN V-groove (formal bank = Rs source-GO). Verdict: コ grasp does NOT fail the
    CPU contact-physics banking gates as a building block; same caveat structure as banked-(A).
- **(SUPERSEDED) earlier "LIFT NOT achieved":** the `r_s71_koshape_depth_47.py` depth-sweep used a SINGLE-move
  lift + non-centered depth → found cable-in-gap ⊻ lift; the refined recipe above (centered + −3mm + GRADUAL
  lift) resolves it. The "+51mm penetration artifact" caveat still applies to single-frame NUMERIC reads —
  the 2026-06-21 success is human-VIDEO-confirmed, not numeric. **Process note: throughout this exploration
  the numeric metrics (finger-tilt 0.0, cable_z) repeatedly MIS-judged (false PASS); the video-analyst agent
  gave both a false-positive AND a false-negative; the HUMAN's visual judgment was the consistent ground
  truth and supplied the −3mm fix.**

## Mid-air clamp / re-grasp (TILT-FOLLOW) — human-CONFIRMED 2026-06-21
**Goal (human 2026-06-21 「一方でケーブルを持ち上げているところに、もう一方でその空中に浮いている状態のケーブルをクランプ」):**
while RIGHT anchors the cable ALOFT, LEFT unclamps then RE-grasps the FLOATING (mid-air) cable = dual-arm
2nd-point re-grasp / hand-over.

- **Finding 1 — the released cable barely droops (~4mm), stays ALOFT ~841-843mm.** When LEFT unclamps, the
  LEFT region does NOT free-fall (the long −Y cable arm rests on the table + the 88mm inner span is short) →
  the floating cable IS available for re-grasp. (v1 `r_s71_midair_clamp_63.py`; the handoff's "likely droops a
  lot" prediction was WRONG.)
- **Finding 2 — the floating cable is locally TILTED ~+9–12°** (catenary from the RIGHT apex down to the −Y
  arm); a square-on (vertical) LEFT re-clamp MISSES — the tilted floating cable squirts out (no table under it
  to react against the descending claw). (v1.)
- **✅ FIX = TILT-FOLLOW (human insight 2026-06-21 「つかもうとするフィンガの傾きがケーブルの傾きに追従する必要がある」).**
  Measure the cable local pitch θ (Y-Z tangent of the adjacent cable segments at the LEFT grasp point); set the
  LEFT EE rotation target to **Rx(−90°+θ)** so the LEFT claws ALIGN with the tilted cable. RIGHT keeps the
  default Rx(−90°) (anchor). → on re-lift, **cable@LEFT rises +20mm = the +20mm LEFT-EE move** (carried) —
  human-CONFIRMED via video (`~/Downloads/r_s71_midair_clamp64.mp4`). Script `r_s71_midair_clamp_64.py` (v2,
  sign +1). **This is the CONFIRMED mid-air re-grasp recipe (human-DECIDED 確定 2026-06-21).**
- **❌ claw-gap widening REJECTED (human lever 「爪の間隔を数mm広げる」, tested 10→14mm
  `2f85_koshape_scratch_wide.xml` / `r_s71_midair_clamp_65.py`):** widening HURT the hold — cable rise dropped
  +20mm → **+6mm (slip)** (the 8mm cable rattles in the wider 14mm mouth; capture easier but retention looser).
  → **keep gap 10mm + tilt** (human «v2(gap10+tilt) を確定»). The wide asset/probe are kept as the rejected
  variant record only.
- **Implementation (grounded, §運用16):** the probe's `T = test_newton_clip_routing` (NOT newton_routing_utils,
  a prior mis-grounding); its `solve_ik_dual` rotation = **XYZW** convention, FIXED `vec4(−.7071,0,0,.7071) =
  Rx(−90°)` for BOTH arms (`test_newton_clip_routing.py:1538`). Per-arm tilt = a runtime **monkeypatch of
  `T.solve_ik_dual`** (ik_move_both calls it as a module global → patch propagates); **production file UNCHANGED**.
- **⚠ Judge caveat (relevant to the telemetry-anchor work):** `per_arm` CAPTURE (b<c<t) returned a
  **FALSE-NEGATIVE** here (`claw[None,None]`) — it breaks when the gripper TILTS (the f1ext/f2ext Y-window + the
  `GX=0.30` hardcode miss the tilted/shifted claw + cable geoms). The RELIABLE signal was
  **cable-displacement-tracks-commanded-EE-motion** (cable@LEFT +20mm = EE +20mm). **Human visual = final ground
  truth** (another numeric-misleads case, [[feedback-grasp-verdict-numeric-and-video-analyst-both-unreliable-human-ground-truth]]).
- **Caveats:** CPU/scratch (BANKED 2026-06-21 (Rs source-GO); V-groove superseded→コ); full-clamp re-grip; grip-force / GPU (R-S6.6) /
  real-clip integration UNVERIFIED; "secure grip vs draped-and-lifted" distinction rests on the human visual.

## Slot-descent visualization
The gripper DOES physically descend into the table void (VOID X[0.234,0.366] Y[−0.060,0.060], grasp X=0.30
Y±0.044). Render the PHYSICS geoms + steep cameras to SHOW it — see [[LL-Render-SlotDescent-Cameras]].

## Artifacts
- Asset gen: `r_s71_make_koshape_asset_48.py`; depth sweep: `r_s71_koshape_depth_47.py`; close-up + geom:
  `r_s71_claw_closeup_51.py`; videos: `r_s71_koshape_video_46.py`, `r_s71_slot_descend_video_50.py`.
- Figures: `~/Downloads/r_s71_claw_closeup.png` (コ wraps the cable), `~/Downloads/r_s71_slot_descend.mp4`.

## Clip insertion (drop-in onto the REAL collidable clip B) — human-CONFIRMED «成功» 2026-06-21

**⚠⚠ CRITICAL CORRECTION 2026-06-21 (human diagnosis 「明らかに設置できない所に設置した」, %9-relayed → %4-confirmed): the FIRST insertion test below put the clip ON the grasp VOID (`CLIP_X=0.30,Y=0.0` = void X[0.234,0.366] Y[−0.060,0.060]) — a GEOMETRIC ERROR + COUPLED-CONSTRAINT: the void must be EMPTY for the lower-claw grasp; the clip needs a SOLID floor to seat → co-located → every clip change perturbed the grasp → the FINGER-TILT regression + the "fix clip ↔ break finger" back-and-forth.** Test-confirmed: clip ON-void (0.30,0.0) → grasp TILTED; clip OFF-void on solid table (0.40,0.0 / 0.40,−0.075) → grasp VERTICAL (= `vertical_grasp_56`). **✅ FIXED B→A (`r_s71_clip_dropin_72.py`, `CLIP_X=0.40,Y=0.0` SEPARATED from the slot + a ROUTE leg):** grasp center 0.30 over the void (clean/VERTICAL, cable rest=804 on table) → ROUTE +0.10X symmetric → drop-in into the clip mouth → seat 809 → pin → ascend → RETAINS @809 (gripper away). human video-confirmed «成功» `~/Downloads/r_s71_clip_dropin72_pin.mp4`. The mechanism findings below (drop-in depth 0.820, A/B floor-retain) HOLD; only the clip POSITION was wrong. ⚠ (0.40,0.0) = simplified Y=0 symmetric-route pos; real C2/C4 (Y=±0.075) need a lateral route + LEFT-arm reach. **Clip-placement vs grasp-void RESOLVED 2026-06-21 (human option A + 5体 Debate): only C3 conflicts in 2D (NOT "C1/C3/C5" — C1/C5 are Y-clear 75mm); C3→(0.40,0.0) decided, `task_config.py` commit DEFERRED — see "Clip placement resolution" subsection below.** Lesson: [[feedback-mechanism-first-generative-design]] (missed the cross-phase clip↔grasp coupling; human mechanism-first diagnosis solved my 3-failure hard-stop).

### Clip placement resolution (2026-06-21 — human option A + 5体 Debate → DEFER the SSOT commit)

**Decision (human option A 2026-06-21):** the one conflicting clip moves off the grasp void to the validated insertion position — **C3 (0.35, 0.0) → (0.40, 0.0)** (`CLIP_X_ODD`→`CLIP_X_EVEN`; (0.40,0.0) = where `r_s71_clip_dropin_72.py` succeeded).

**⚠ records-must-match-fact — the conflict is C3 ONLY (not "C1/C3/C5"):** that earlier claim (here + `RS71-SSOT:30`) was an **X-only** check. The 2D footprint check — clip base ±0.020 X × ±0.015 Y (`test_newton_clip_routing.py:1008`) vs the grasp swept-void X[0.234,0.366] ∧ Y[−0.060,+0.060] (`test:978`/`:968-969`) — shows **only C3 (0.35,0.0)** overlaps in BOTH axes. C1/C5 (0.35,±0.150) X-overlap but **Y-clear 75mm**; C2/C4 (0.40,±0.075) **X-clear 14mm**. → moving C3 is a **complete** void-conflict fix, not partial. (Gripper-footprint band X[0.249,0.351] `test:973`: pierced 21mm by C3@0.35, cleared 29mm by C3@0.40.)

**5体 CC Debate (L3, pre-impl):** geometry / consumer / regression = **PASS** — CC4 ran `test_orchestrator_transforms` = **143/143** both at C3=0.35 AND monkey-patched C3=0.40; all `CLIP_POSITIONS` consumers are dynamic (`routing_orchestrator.py:771` / `step_table.py:79` / `scripted_skills.py:69`); the hardcoded `0.35` test literals are C1 (Y=0.15), not C3. **NHA = HOLD** (decisive): the `task_config.py` edit is **inert now** — the committed build has no void (multi-box table NOT landed, `RS71-SSOT:37`); the validated probe sets the clip via the `CLIP_X` env-override (`test:1005`), not `CLIP_POSITIONS[2]`; and C3→0.40 would newly diverge from the frozen `full_43step.json` (C3=0.35, currently consistent).

**→ DECISION (human option 1, 2026-06-21):** record the resolved placement HERE now; **DEFER the `task_config.py:214` L3 numeric commit** to the table-slot / multi-clip-routing landing (when `CLIP_POSITIONS` is actually consumed — the 5-clip routing needs the array then anyway). Use `CLIP_X`/`CLIP_Y` env-override for single-clip probes meanwhile. **`task_config.py` UNCHANGED this session** (verified `:214` still `(CLIP_X_ODD, CLIP_Y_CENTER)` = 0.35).

**Pending Rs-update (read-only specs — §運用4 write-side / `feedback-confirmed-decision-reflect-in-authoritative-spec`):** `04-Specs/RS71-System-Spec-SSOT.md:30` ("C1/C3/C5 overlap") → "only C3 (2D); C3→0.40 decided, commit deferred"; `07-Design/Mechanical-Specs.md:2619` stale "C3 (0.35,0.000)" diagram (+ a pre-existing C1/C5 Y-swap bug, CC5-flagged). CC is read-only on 04-Specs/07-Design.

**Downstream (NOT fixed here):** the real 5-clip blocker = LEFT-arm reach for the off-center clips (Y=±0.150, `RS71-SSOT:37` / `:154`) = a SEPARATE problem.

— recorded 2026-06-21 19:37 JST (%4)

### (Historical — the FLAWED clip-on-void test; mechanism still valid)
**Context:** R-S7.1.1 (B) wired REAL clip collision (`CLIP_COLLISION=1`, harness `test_newton_clip_routing.py:1006`).
Script `eval_runs/troot_optE_rs71_kinematic_retention_20260616/r_s71_clip_dropin_72.py` (derived from `_70`;
working-tree, env7, HEAD 4783108a7b; CPU). Videos `~/Downloads/r_s71_clip_dropin72_{pin,nopin}.mp4`.

- **✅ The clip is a CATCHER (self-seating).** A cable lying across the collidable clip self-seats at the groove
  `GROOVE_CENTER_Z=809` (`task_config.py:226`) with NO manipulation — confirmed: the gripped seg rested at 809 at
  the START (`rest=809`), vs 804 (table) without collision (`r_s71_clip_collide_feas_71.py` A/B). **This RESOLVES
  F-1** ("clip-as-catcher cannot retain until collision-wiring is added", `RS71-System-Spec-SSOT.md` §2): with (B)
  wired the clip DOES catch + retain the cable. (⚠ RS71-SSOT §2 + the LEDGER still state F-1 unresolved → Rs-update
  flagged; CC is Read-only on 04-Specs/07-Design.)
- **✅ B→A sequence works (CPU, human video-confirmed «A»):** grasp (self-seated 809) → lift OFF the clip (~850,
  groove emptied) → lower back into the clip MOUTH → UNCLAMP → cable re-seats at 809 → [pin] → ascend → the cable
  stays in the clip at 809 (gripper retracted away).
- **⚠ MECHANISM = "lower into the mouth, then release" (NOT "release high above & let it drop in").** v1 (release
  at cable~842, claws above the clip top 830) FAILED — the cable rested ON the clip top (834), never threading the
  25mm into the 809 groove. ROOT: the ko bottom claw (18mm) FITS the 22mm edge-mouth but is wider than the 15mm
  wall-channel → it stops at the wall top (~820). FIX (`REL_CABLE_Z=0.820`): lower the claw to the wall top (cable
  ~827) THEN unclamp → the cable drops the last ~18mm into the 809 channel. **Depth-critical: 0.842 fails / 0.820
  seats** (placement is NOT yet robust to depth).
- **✅ A/B — the real clip floor RETAINS without the pin (vertical):** PIN=1 → 809 retained; **PIN=0 (control) →
  809 retained, fell_to_table=False** (gripper ascended away, the cable stayed in the clip on the real-collision
  floor ALONE). ⇒ the authorized kinematic pin (`log.md:6534`) is DOWNGRADED to Y-slide insurance, NOT the primary
  vertical retainer.
- **⚠ Caveats / conservatism (do NOT over-claim, GROVE §2.2):** (1) SCOPE = a single clip at the grasp X,Y
  (0.30,0.0) that the cable ALREADY crossed → this tests lift-off + re-seat, NOT route-to-a-clip-the-cable-doesn't-
  cross (off-center route + LEFT-arm reach = a SEPARATE problem). (2) DEPTH-sensitive (hand-tuned 0.820) =
  NON-conservative robustness. (3) CPU/static, no perturbation / routing-tension → Y-slide / tension retention
  UNTESTED = NON-conservative for the real task. (4) ko UN-banked vs FROZEN V-groove; `CLIP_COLLISION` flag
  uncommitted working-tree; GPU (R-S6.6) not run. Numeric + my frame-reads + the human's «A» video confirm agree;
  human visual = ground truth ([[feedback-grasp-verdict-numeric-and-video-analyst-both-unreliable-human-ground-truth]]).

## See also
- Banked finger SSOT (deviated from): `07-Design/Gripper-VGroove-Design.md` (V-groove ◇, FROZEN).
- FORM-vs-LIFT saga + the human's accepted ◇-below lift: `04-Specs/RS71-System-Spec-SSOT.md` §3 / :37.
- Prior コ 5体-FAIL: `eval_runs/.../DISPATCH_12to18_COCAGE_5TAI_FAIL_CONSULT_2026-06-17.md`.
</content>
