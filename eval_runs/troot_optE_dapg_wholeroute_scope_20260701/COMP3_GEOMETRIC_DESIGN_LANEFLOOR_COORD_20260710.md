# /geometric-design: lane-aware EE-Z floor (EE_Z_FLOOR_KO) — G1 root-cause fix, Rs 案B

- Date: 2026-07-10 (COORD; fix chunk dispatch %12 13:40, Rs approval 13:4x = 案B lane-dependent floor)
- Root cause being fixed: `comp3_g1_armq_diag_result.json` `root_cause_floor_clip` (commit `39b206ddb0`) —
  the recorded grasp-park EE z (1.06680, BOTH arms) sits 3.12mm below `EE_Z_FLOOR_KO`=1.06992
  (`newton_route_env.py:163`) across exactly the close window (f897-1146, 250 frames, EVERY grid cell),
  and the target z clip (`newton_route_env.py:988-989`) raised the commanded target -> claw parked
  +3.07mm high -> close pushed the cable into the void instead of caging it (G1 FAIL, Rs human-GT).

## Step 0: Interrogate-the-mechanism (BOUNDED, one pass)

1. Is the floor needed at all? YES — it is the substrate Z safety clamp for trainer-stage residual
   actions (`POS_RESIDUAL_SCALE`=0.015/step, `newton_route_env.py:322`): without it a policy residual can
   command IK targets that drive the pinch below the cable/table (the arm drive is a kinematic joint_q
   overwrite -> nothing else stops it). Removing the floor is NOT a cheaper path.
2. Cheap salvage of existing geometry? YES — this fix IS the salvage: keep the clamp, correct its value
   where its premise (clip base under the cable) is false. No scene/asset change.
3. Downstream-stage risk? The floor also binds the RL trainer's reachable set; the lane floor at the
   table-level cable centerline is exactly the physical lower bound a grasp policy should have.
   FLAGGED (not launched): trainer-stage reward interaction with the clamp is comp5+ scope.

## Step 1: Measured values (all MEASURED, not design values)

| quantity | value | source (measured) |
|---|---|---|
| recorded grasp-park EE z (L & R) | 1.06680 | golden npz `ee_pos_l/r` f897-1146; `comp3_g1_armq_diag_result.json` |
| recorded park pinch z (= EE − EE_TO_PINCH_OPEN) | 0.80588 | == back-check claw park (FK/clamp_pos_ko, `comp3_g1_closewindow_result.json`) — 3-way consistent |
| env achieved EE z under OLD clip | 1.06987 (= floor − 0.05mm) | diag capture, park mean |
| settled cable z at grasp lanes (in-void, table-resting) | 0.8040 | env settle `z_rest`; recording cable ~0.804 |
| TABLE_HEIGHT / CLIP_BASE_HEIGHT / CABLE_RADIUS / EE_TO_PINCH_OPEN | 0.80 / 0.005 / 0.004 / 0.26092 | `task_config.py:20,91,137,326` |
| OLD floor (kept out-of-lane) | 1.06992 | `newton_route_env.py:163` |
| NEW lane floor = TABLE + CABLE_R + EE_TO_PINCH_OPEN | 1.06492 | 案B arithmetic (pinch @ floor = 0.80400 = table-level cable centerline) |
| void footprint (lane) | Y[0.090,0.210] × X[0.234,0.366] | `newton_skill_env_base.py:1746,1750` (Y = WIDE_LEFT_Y−0.016..WIDE_RIGHT_Y+0.016; X = 0.3±0.066); runtime-verified by probe leg C vs the REAL built model |
| recorded park XY envelope | X 0.3000-0.3001, Y 0.1038 (L) / 0.1962 (R) | 81-cell sweep; lane-edge clearance ≥13.8mm (Y), ≥65.9mm (X) |

## Step 2: Constraints

Hard constraints (inviolable):
- H1: the floor must NOT bind the recorded trajectory at any frame, any cell, either arm
  (replay-faithfulness — the clip binding IS the G1 root cause).
- H2: in-lane, pinch@floor >= table-level cable centerline (0.80400) — the clamp must still forbid
  commanding the pinch below the cable center (pushing the cable down = the observed failure mode).
- H3: out-of-lane floor unchanged (1.06992) — clip-base cable centerline bound retained; zero behavior
  change outside the lane (Rs 案B scope).
- H4: no reliance on DISABLE_CONTACTS-style workarounds — in-lane the table is REALLY void (4-box scene),
  so a lower fingertip is physically valid there, and rigid contact remains active at the lane edges.

Soft goals:
- S1: minimal code surface (~10 lines, `newton_route_env.py` only — file-set discipline).
- S2: lane bounds single-sourced from the same primitives as the void builder (no new magic numbers
  beyond mirroring `newton_skill_env_base.py:1746,1750` literals, cross-pinned by unit + probe leg C).

### Step 2a: effective design space
The floor value in-lane must satisfy H1 (< 1.06680 at park) and H2 (>= 1.06492). Effective interval:
**[1.06492, 1.06680) — width 1.88mm.** 案B picks the LOWER bound (= H2 equality: pinch exactly at cable
centerline), leaving the full 1.88mm as H1 margin. LOUD per skill (<5mm band): this margin is
DETERMINISTIC, not stochastic — both bound values are frozen (recording data: 81 cells × 2 arms all
within 0.01mm; floor = exact arithmetic of locked constants). Measured spread across 162 sweeps:
min +1.88 / max +1.89mm. There is no physical variation source on either side; the band evaluation
tables target variable geometry, which this is not. Surfaced for %12/Rs judgment regardless.

### Step 2b: soft-vs-hard conflicts — none. S1/S2 achievable inside H1-H4 (shown below).

## Step 3: Cross-section (pinch frame; pinch = EE − 260.92mm)

```
EE z [mm]              OUT-OF-LANE (clip base)      |      IN-LANE (void footprint)
1069.92 ── EE floor OLD = KEPT ──────────────────── |
1066.80 ── recorded park EE ── was BIND ❌ (+3.12)  |  ── recorded park EE (margin +1.88mm ✅)
1064.92 ─────────────────────────────────────────── | ── EE floor NEW (lane)
                       ~ pinch frame (−260.92mm) ~
 809.00 ── pinch@OLD floor = clip-base cable center |
 805.88 ── recorded park pinch ──────────────────── |  (1.88mm above table-level cable center)
 804.00 ──                                          | ── pinch@NEW floor = cable centerline (0.800+0.004)
 800.00 ── ▓▓▓ TABLE top ▓▓▓                        |    (VOID: no table under the lane — f1ext passes)
```
Lane boundary (XY): Y edges 0.090/0.210, X edges 0.234/0.366; floor steps 5.00mm at the edge.
Recorded trajectory crosses the lane boundary only at z >= 1.13224 (= +62.3mm above even the OLD floor,
81-cell measured) -> the step never bites on the replay path.

## Step 4: Trade study (H-violating rows excluded per skill)

| option | in-lane floor | H1 (no bind) | H2 (>= cable center) | H3 (out-lane unchanged) | notes |
|---|---|---|---|---|---|
| A: keep 1.06992 everywhere | 1.06992 | ❌ (binds 250 f/cell) | — | — | EXCLUDED (this is the bug) |
| B ★Rs-approved | 1.06492 in lane | ✅ +1.88mm | ✅ equality | ✅ | pinch@floor = cable centerline |
| C: 1.06492 everywhere | 1.06492 | ✅ | ✅ in-lane | ❌ out-lane pinch may command below clip-base cable center (押し下げ risk at clips) | EXCLUDED (H3) |
| D: smooth blend at edge | 1.06492 + taper | ✅ | ✅ | ✅ | adds code + tuning for a step that measurably never bites; rejected for S1 (and Rs approved B) |

## Step 5: Reality check
- Real robot: a fingertip descending into a real void slot below table level is physically ordinary;
  the RECORDING itself executed this exact depth at 0.716 SR — replay at recorded depth is
  proven-by-recording, not new geometry.
- H4 note: in-lane there is genuinely no table (4-box scene, probe leg C parity vs real model); at lane
  edges rigid contact with the solid table boxes remains ACTIVE — a residual-driven target near the edge
  produces real contact, not penetration.

### Step 5a: Sensitivity
| variation | width | effect on H1/H2 | verdict |
|---|---|---|---|
| recording park z across 81 cells × 2 arms | ±0.005mm measured | margin +1.88..+1.89mm | H1 ✅ |
| cable settle z (env vs recording) | ±0.15mm (leg G2 aligned) | pinch@floor vs cable center ±0.15mm | H2 ✅ (equality has cable-radius 4mm of throat below center anyway) |
| device numerics (cuda replay) | ~0.05mm (diag: floor−0.05mm tracking) | inside margin | ✅ |
| policy residual (trainer stage) | ±15mm/step commanded | clamped AT floor by design (clamp working as intended) | ✅ |

### Step 5b: Parameter dependency
- `EE_Z_FLOOR_KO` (route env): defined `newton_route_env.py:163`, used ONLY at `:988-989` (verified grep).
  -> both call sites switch to the lane-aware lookup. No other consumer in the route env.
- `newton_approach_cable_mujoco_env.py:200` has its OWN EE_Z_FLOOR_KO (AC env) — OUT OF SCOPE / file-set
  (different env, different task; untouched, noted loud).
- `EE_Z_SAFETY_UPPER` unchanged. Void literals mirror `newton_skill_env_base.py:1746,1750`
  (base file NOT edited — file-set); parity chain: env constants pinned by L4 unit to the banked expected
  bounds, and probe leg C pins the REAL built void to the same bounds.

### Step 5c: Physical causality trace (5 steps, replay path with fix)
| step | state | event | physical response | outcome |
|---|---|---|---|---|
| 0 | t≈89 descend done, target in-lane | floor lookup -> 1.06492, recorded target 1.06680 NOT clipped | commanded = recorded | ✅ |
| 1 | t=90..99 park + close onset | claw parks at pinch 0.80588 (recording-faithful, ±device numerics) | pinch 1.88mm above cable center — cable enters throat as recorded | ✅ |
| 2 | t=99 latch | pads cage cable at recorded geometry | latch offsets ≈ recording (+1.9~4.5mm band) | ✅ (confirmation run measures this) |
| 3 | t=112+ lift | targets rise above both floors | carried cable, floor inactive | ✅ |
| 4 | boundary crossing (residual case) | XY exits lane at low z -> floor steps +5mm | commanded z rises ≤5mm, joint-interp smooths over 10 frames; recoverable, no oscillation driver (step is position-of-XY dependent, not z-feedback) | ✅ (replay path never reaches this: crossings at z≥1.132) |
| 5 | trainer residual pushes down in-lane | clamp at 1.06492 | pinch held at cable centerline — cannot command cable push-down | ✅ (this is the clamp doing its job) |

### Step 5d: Axis-resolved retention — N/A for a clamp bound (no retention claim made here); grasp
retention itself is judged by G1 retry (video + Rs human-GT), not by this fix.

## Verification evidence (measured, this doc's basis)
- 81 cells × 2 arms × 7707 frames sweep: below-NEW-floor frames = 0 in ALL; min margin +1.88mm
  (max +1.89mm); below-OLD-floor = exactly 250 frames in EVERY sweep (latent defect was universal);
  lowest z at any lane-boundary crossing = 1.13224 (+62.3mm above OLD floor).
- Flag-OFF bind check (LOUD): the clip site `:988-989` has NO flag branch — the OLD clip was binding in
  the flag-OFF (Stage-A) drive path identically (same recorded targets). The fix therefore CHANGES the
  flag-OFF close-window trajectory by up to 3.12mm (arms descend to the recorded depth). This is an
  Rs-approved env-core latent-defect fix (floor common to both flags per dispatch), NOT a comp3
  flag-gating break; chunk-1 "flag-OFF byte-preserve" is superseded AT THIS SITE by 案B. run_route
  (`route_executor.py:1001+`, Rs-LOCKED) does not pass through this clip — byte-repro golden leg
  unaffected (and route_executor.py is untouched -> NHA cond5 not triggered).

## Change (implementation)
`newton_route_env.py` only (~10 lines): module constant `EE_Z_FLOOR_KO_LANE` + lane bounds + module fn
`ee_z_floor_ko(x, y)`; `:988-989` switch to per-target lookup. L4 unit: in/out-lane + edge values +
recorded-park non-bind (REAL golden npz) + old-floor bind documentation assert.
