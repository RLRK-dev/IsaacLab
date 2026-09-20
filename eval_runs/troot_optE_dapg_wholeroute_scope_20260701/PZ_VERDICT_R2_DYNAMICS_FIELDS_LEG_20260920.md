# pZ — verdict on leg R2 (asset-grade dynamics fields), rows R2-1..10 of `PZ_R2_DYNAMICS_FIELDS_LEG_PREREG_20260920.md` @ `ad06cff8eb`, judged against the bars fixed there before the single run — with two bar defects reported as such, not re-graded

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 14:47:02 JST on m-p18-426 (p4 m-p4-288 (2), R2 in parallel with W/R1). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted**: acceptance and the disposition of the two bar defects are p4's (and p11's, whose §10 row set the bars).

**Order of existence**: pre-registration committed `ad06cff8eb` at 14:42:52 JST (maps, bars, controls, instrument sha `3f6dab44b655d64b…` fixed; outputs asserted absent) → **one** run of `pz_r2.py` finishing 14:42:52 JST → this verdict. HEAD at writing `adb85cccd8`; objects = the blobs pinned there (gripper acceptance `f1909891539c` after the accepted `mkdir` follow-up; `build_side` untouched); the leg ran in the `git archive` of `792e62e460`. **Run 0**; `mj_step` = 0; driver not imported. **Stop-cause tag: none.**

## The one-line result before the rows
Every field p11's §10 R2 names is the mirror of its counterpart **to double precision**: 21 of the 28 field comparisons on L vs B pass their pre-registered bar outright; **5 "exact" fields fail by one unit in the last place of a double (≤ 2.8e-17 m)** and **`body_iquat` fails on 3 of 20 bodies by a 180° principal-axis sign choice whose inertia tensor is identical (difference 0.0)**. Both are defects of the pre-registered bars (an "exact" that no text-serialised double can meet; a quaternion bar for a quantity MuJoCo does not define uniquely), not of the assets — and this desk reports them as FAILs under the bar it wrote, with the magnitudes, and does **not** re-grade them. The negative controls fire on the fields that carry chirality; one pre-registered control expectation (hand `jnt_axis`) is refuted and explained.

## Verdict per row

| # | row (bar as pre-registered) | verdict | measured (`pz_r2.py`, appendix A; full log appendix B) |
|---|---|---|---|
| R2-1a | `body_mass`, `body_inertia` (exact) | **CONFIRMED** | mass 20/20 within bar, max 0.00e+00; inertia 20/20 within bar, max 0.00e+00 |
| R2-1b | `body_pos`, `body_ipos` (Mx, exact) | **FAIL under the pre-registered bar — by one ulp** | pos 19/20 within bar, max 3.11e-18, fails: ['g_base_mount: 3.109e-18'] m; ipos 19/20 within bar, max 3.79e-19, fails: ['g_base_mount: 3.795e-19'] m — the only pair is `g_base_mount`, off by 3e-18 / 4e-19 m = the last bit of a double; every other pair exactly equal |
| R2-1c | `body_quat` (Mx·R·Mx ≤ 1e-12) | **CONFIRMED** | 20/20 within bar, max 6.66e-16 |
| R2-1d | `body_iquat` (Mx·R·Mx ≤ 1e-8) | **FAIL under the pre-registered bar on 3 of 20 bodies — a principal-axis sign choice, not an inertia difference** | 17/20 within bar, max 2.00e+00, fails: ['g_base_mount: 2.000e+00', 'g_left_silicone_pad: 2.000e+00', 'g_right_silicone_pad: 2.000e+00'] (residual 2.000 = a 180° turn about a principal axis on `g_base_mount`, `g_left_silicone_pad`, `g_right_silicone_pad`); the 17 others ≤ 5.63e-09. Supplementary measurement (appendix C, not pre-registered): the frame-independent inertia tensor `R·diag(I)·Rᵀ` under `Mx` conjugation differs by **0.0** on those three bodies and by ≤ 1.04e-10 kg·m² over all 20; their principal moments are equal and non-degenerate on both sides — MuJoCo's compile picks eigenvector signs differently across the reflection, which changes the quaternion and nothing physical |
| R2-2 | joints: `jnt_type`/`jnt_range`/`jnt_stiffness`/`qpos_spring`/`dof_armature`/`dof_damping` (exact); `jnt_axis` → `−A·a` (exact); `jnt_pos` (Mx, exact) | **CONFIRMED** | all 14 joints exact on every field; `jnt_axis (−A·a)` 14/14 within bar, max 0.00e+00; `jnt_pos` 14/14 within bar, max 0.00e+00. Reported (not a bar): `−a` holds on the 6 arm joints and fails on the 8 hand joints, whose axes are `(1, 0, 0)` — for an x-axis `−A·a = a ≠ −a`; the pre-registration's expectation that every axis has `a_x = 0` was wrong for the hand (appendix C lists the axes) |
| R2-3 | geoms: `geom_type`, `geom_solref`/`solimp`, `friction`/`condim`/`contype`/`conaffinity` (exact); `geom_size` (exact); `geom_pos` (Mx, exact); non-mesh `geom_quat` (≤ 1e-12) | **CONFIRMED except two exact fields off by one ulp** | type/solref-solimp/friction… exact on 38/38; non-mesh quat 8/8 within bar, max 0.00e+00; **`geom_size` 24/38 within bar, max 1.04e-17, fails: ['g_base#0: 6.939e-18', 'g_base#1: 6.939e-18', 'g_left_coupler#0: 8.674e-19'] m; `geom_pos` 16/38 within bar, max 2.78e-17, fails: ['a_wrist_1_link#0: 2.776e-17', 'a_wrist_3_link#0: 2.082e-17', 'g_base#0: 6.939e-18'] m** — 1e-17..1e-18 m = double-precision rounding of mesh-derived sizes/centres and of text-serialised offsets, on both the arm and the hand |
| R2-4 | hand actuator `fingers_actuator` (exact) | **CONFIRMED** | gain/bias 1/1 within bar, max 0.00e+00; ctrl/force/gear 1/1 within bar, max 0.00e+00; types 1/1 within bar, max 0.00e+00 |
| R2-5 | tendon `split` (exact) | **CONFIRMED** | stiffness/damping/range 1/1 within bar, max 0.00e+00; wraps 1/1 within bar, max 0.00e+00 |
| R2-6 | equalities (exact) | **CONFIRMED except `eq_data` off by one ulp on the two `connect`s** | type/active 3/3 within bar, max 0.00e+00; solref/solimp 3/3 within bar, max 0.00e+00; **`eq_data` 1/3 within bar, max 2.08e-16, fails: ['0:g_left_follower:g_left_coupler: 2.082e-16', '0:g_right_follower:g_right_coupler: 1.527e-16']** — the compile-time second anchor of the two follower–coupler connects differs at 2e-16 m (its x is 0, so `Mx` and identity coincide; the residual is rounding, not a mapped anchor) |
| R2-7 | single-asset compiles | **arm: CONFIRMED except `geom_size`/`geom_pos` by one ulp; hand: the same pattern as the composed model** | arm (`body_iquat ≤ 1e-10`): iquat 6/6 within bar, max 9.26e-11, quat 6/6 within bar, max 6.66e-16, pos/ipos/mass/inertia/joints all exact; `geom_size` 6/7 within bar, max 1.39e-17, fails: ['world#0: 1.388e-17'], `geom_pos` 5/7 within bar, max 2.78e-17, fails: ['wrist_1_link#0: 2.776e-17', 'wrist_3_link#0: 2.082e-17'] m. hand (`≤ 1e-8`): iquat 11/14 within bar, max 2.00e+00, fails: ['base_mount: 2.000e+00', 'left_silicone_pad: 2.000e+00', 'right_silicone_pad: 2.000e+00'] (the same three bodies), ipos 13/14 within bar, max 3.79e-19, fails: ['base_mount: 3.795e-19'], geom_size 18/32 within bar, max 1.04e-17, fails: ['base#0: 6.939e-18', 'base#1: 6.939e-18', 'left_coupler#0: 8.674e-19'], geom_pos 12/32 within bar, max 6.94e-18, fails: ['base#0: 6.939e-18', 'base#1: 6.939e-18', 'base_mount#0: 3.795e-19'], eq_data 1/3 within bar, max 4.16e-17, fails: ['0:left_follower:left_coupler: 4.163e-17', '0:right_follower:right_coupler: 4.163e-17']; every other hand field exact — the text-rounding effect the pre-registration expected at 1e-9 does not appear: the 8-digit normalised quaternions of the mirrored xml reproduce the stock frames to 6.7e-16 (arm) / 5.6e-09 (hand, the 11 non-flipped bodies) |
| R2-8 | negative controls (p4 condition ②) | **CONFIRMED — each fires where it must, with one pre-registered expectation refuted** | **NH** (stock hand): hand rows fail — `body_ipos` 6 pairs up to 7.21e-04 m, `body_quat` `g_base` 2.0, `body_iquat` 9 bodies, `geom_pos` 26 geoms up to 7.21e-04 m; arm rows pass. ⚠ The pre-registration also expected the hand `jnt_axis` (−A·a) row to fail on NH: it does **not** — every hand axis is `(1, 0, 0)`, for which `−A·a = a`, so that row cannot see the hand's chirality (`body_pos` likewise: the hand's local offsets have `x = 0`). **RC** (stock arm on the right mount): arm rows fail — `body_pos` up to 1.295 m, `body_ipos` 12 up to 0.457 m, `jnt_axis (−A·a)` 6 arm joints, `body_iquat` 15, `geom_pos` 30 up to 0.573 m. **B′** (one hand mass +1e-7): exactly one field differs from B's result — `body_mass` on `g_right_follower` (1.0e-07 kg), every other field identical to B's — the instrument sees a single perturbed number |
| R2-9 | driver-injected parameters | **not measured (as pre-registered)** | arm actuator kp/kv/`forcerange`/`ctrlrange` (driver `:426-433`) and `arm_spec` armature/damping (`:238-244`) are not in these models; text-cited equalities; #69's R4 |
| R2-10 | control invariance / no run | **CONFIRMED** | `mj_step` calls 0; driver family in `sys.modules` `[]`; model fields only; run 0 |

## Disposition proposal (for p4 / p11; nothing applied here)
- Replace "exact" by **≤ 1e-12** (the bar `body_quat` already carries) for `body_pos`, `body_ipos`, `geom_size`, `geom_pos`, `eq_data`: under that bar every L-vs-B pair passes (max 2.8e-17) and every control still fails by ≥ 1.7e-8 m (NH's smallest failing pair) — the discrimination is untouched.
- Replace the `body_iquat` row by the **frame-independent inertia tensor** `Mx·(R·diag(I)·Rᵀ)·Mx = R_R·diag(I_R)·R_Rᵀ`, bar ≤ 1e-9 kg·m² (measured max 1.0e-10; the three flipped bodies read 0.0); `body_iquat` itself stays reported. If p4 adopts either, the instrument is deterministic and the numbers above are the numbers; a re-run under the corrected pre-registration would be a formality this desk will perform on request.
- The pre-registration's expectation that the hand `jnt_axis` row fails on NH is withdrawn: with x-axes the map is trivial. The hand's chirality is carried by `body_ipos` / `body_iquat` / `geom_pos` (and by R1′'s world geometry), which do fail on NH.

## What this leg does not show (holes)
- Fields only, on the composed one-arm models and the single assets; nothing dynamic is exercised (no `mj_forward`, no contact, no run).
- Mesh geom quaternions are excluded by design (principal-axis re-framing); the mesh shapes are R1′'s.
- Driver-injected actuator/armature/damping values (R2-9) are not in these models.

## Appendix A — `pz_r2.py` (verbatim = appendix A of the pre-registration; sha256 3f6dab44b655d64bd38d23696fe5aeadaddffa6aa3a92b31cb3e6b1d71ace5f0)
(not repeated; the pre-registration @ `ad06cff8eb` carries it verbatim)

## Appendix B — instrument output (verbatim, `r2.log`)
```text
[r2] composed_L_vs_B: bodies matched 22 (L 22 / R 22; unmatched []), joints 14, geoms 38, actuators 1, tendons 1, eqs 3 | fields 28, FAILED 7: ['body_ipos (Mx, exact)', 'body_iquat (Mx.R.Mx)', 'body_pos (Mx, exact)', 'eq_data (exact)', 'geom_pos (Mx, exact)', 'geom_size (exact)', 'jnt_axis (-a, reported)']
[r2]    body_mass (exact)                                    n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_inertia (exact)                                 n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_pos (Mx, exact)                                 n= 20 fail=  1 max=3.109e-18 bar=exact  e.g. ['g_base_mount: 3.109e-18']
[r2]    body_ipos (Mx, exact)                                n= 20 fail=  1 max=3.795e-19 bar=exact  e.g. ['g_base_mount: 3.795e-19']
[r2]    body_quat (Mx.R.Mx)                                  n= 20 fail=  0 max=6.661e-16 bar=1e-12
[r2]    body_iquat (Mx.R.Mx)                                 n= 20 fail=  3 max=2.000e+00 bar=1e-08  e.g. ['g_base_mount: 2.000e+00', 'g_left_silicone_pad: 2.000e+00', 'g_right_silicone_pad: 2.000e+00']
[r2]    jnt_type (exact)                                     n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_range (exact)                                    n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-A.a, exact)                               n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-a, reported)                              n= 14 fail=  8 max=2.000e+00 bar=exact  e.g. ['g_left_coupler_joint: 2.000e+00', 'g_left_driver_joint: 2.000e+00', 'g_left_follower_joint: 2.000e+00']
[r2]    jnt_pos (Mx, exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_stiffness (exact)                                n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    qpos_spring (exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    dof_armature/damping (exact)                         n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_type (exact)                                    n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_size (exact)                                    n= 38 fail= 14 max=1.041e-17 bar=exact  e.g. ['g_base#0: 6.939e-18', 'g_base#1: 6.939e-18', 'g_left_coupler#0: 8.674e-19']
[r2]    geom_pos (Mx, exact)                                 n= 38 fail= 22 max=2.776e-17 bar=exact  e.g. ['a_wrist_1_link#0: 2.776e-17', 'a_wrist_3_link#0: 2.082e-17', 'g_base#0: 6.939e-18']
[r2]    geom_solref/solimp (exact)                           n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_friction/condim/contype/conaffinity (exact)     n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_quat non-mesh (Mx.R.Mx)                         n=  8 fail=  0 max=0.000e+00 bar=1e-12
[r2]    actuator_gainprm/biasprm (exact)                     n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_ctrlrange/forcerange/gear (exact)           n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_trntype/dyntype/gaintype/biastype (exact)   n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon_stiffness/damping/range (exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon wraps (obj names + coef, exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_type/active (exact)                               n=  3 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_data (exact)                                      n=  3 fail=  2 max=2.082e-16 bar=exact  e.g. ['0:g_left_follower:g_left_coupler: 2.082e-16', '0:g_right_follower:g_right_coupler: 1.527e-16']
[r2]    eq_solref/solimp (exact)                             n=  3 fail=  0 max=0.000e+00 bar=exact
[r2] composed_L_vs_NH (negative: stock hand): bodies matched 22 (L 22 / R 22; unmatched []), joints 14, geoms 38, actuators 1, tendons 1, eqs 3 | fields 28, FAILED 7: ['body_ipos (Mx, exact)', 'body_iquat (Mx.R.Mx)', 'body_pos (Mx, exact)', 'body_quat (Mx.R.Mx)', 'eq_data (exact)', 'geom_pos (Mx, exact)', 'jnt_axis (-a, reported)']
[r2]    body_mass (exact)                                    n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_inertia (exact)                                 n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_pos (Mx, exact)                                 n= 20 fail=  1 max=3.109e-18 bar=exact  e.g. ['g_base_mount: 3.109e-18']
[r2]    body_ipos (Mx, exact)                                n= 20 fail=  6 max=7.212e-04 bar=exact  e.g. ['g_base_mount: 7.212e-04', 'g_left_silicone_pad: 9.524e-19', 'g_left_spring_link: 1.730e-08']
[r2]    body_quat (Mx.R.Mx)                                  n= 20 fail=  1 max=2.000e+00 bar=1e-12  e.g. ['g_base: 2.000e+00']
[r2]    body_iquat (Mx.R.Mx)                                 n= 20 fail=  9 max=2.000e+00 bar=1e-08  e.g. ['g_base_mount: 2.000e+00', 'g_left_coupler: 2.000e+00', 'g_left_pad: 2.000e+00']
[r2]    jnt_type (exact)                                     n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_range (exact)                                    n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-A.a, exact)                               n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-a, reported)                              n= 14 fail=  8 max=2.000e+00 bar=exact  e.g. ['g_left_coupler_joint: 2.000e+00', 'g_left_driver_joint: 2.000e+00', 'g_left_follower_joint: 2.000e+00']
[r2]    jnt_pos (Mx, exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_stiffness (exact)                                n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    qpos_spring (exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    dof_armature/damping (exact)                         n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_type (exact)                                    n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_size (exact)                                    n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_pos (Mx, exact)                                 n= 38 fail= 26 max=7.212e-04 bar=exact  e.g. ['a_wrist_1_link#0: 2.776e-17', 'a_wrist_3_link#0: 2.082e-17', 'g_base#0: 1.839e-07']
[r2]    geom_solref/solimp (exact)                           n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_friction/condim/contype/conaffinity (exact)     n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_quat non-mesh (Mx.R.Mx)                         n=  8 fail=  0 max=0.000e+00 bar=1e-12
[r2]    actuator_gainprm/biasprm (exact)                     n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_ctrlrange/forcerange/gear (exact)           n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_trntype/dyntype/gaintype/biastype (exact)   n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon_stiffness/damping/range (exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon wraps (obj names + coef, exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_type/active (exact)                               n=  3 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_data (exact)                                      n=  3 fail=  2 max=2.082e-16 bar=exact  e.g. ['0:g_left_follower:g_left_coupler: 2.082e-16', '0:g_right_follower:g_right_coupler: 1.527e-16']
[r2]    eq_solref/solimp (exact)                             n=  3 fail=  0 max=0.000e+00 bar=exact
[r2] composed_L_vs_RC (negative: stock arm on the right mount): bodies matched 22 (L 22 / R 22; unmatched []), joints 14, geoms 38, actuators 1, tendons 1, eqs 3 | fields 28, FAILED 8: ['body_ipos (Mx, exact)', 'body_iquat (Mx.R.Mx)', 'body_pos (Mx, exact)', 'body_quat (Mx.R.Mx)', 'eq_data (exact)', 'geom_pos (Mx, exact)', 'jnt_axis (-A.a, exact)', 'jnt_axis (-a, reported)']
[r2]    body_mass (exact)                                    n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_inertia (exact)                                 n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_pos (Mx, exact)                                 n= 20 fail=  3 max=1.295e+00 bar=exact  e.g. ['a_forearm_link: 1.295e+00', 'a_wrist_1_link: 1.033e+00', 'g_base_mount: 3.109e-18']
[r2]    body_ipos (Mx, exact)                                n= 20 fail= 12 max=4.570e-01 bar=exact  e.g. ['a_forearm_link: 4.219e-01', 'a_shoulder_link: 4.800e-05', 'a_upper_arm_link: 4.570e-01']
[r2]    body_quat (Mx.R.Mx)                                  n= 20 fail=  1 max=2.000e+00 bar=1e-12  e.g. ['g_base: 2.000e+00']
[r2]    body_iquat (Mx.R.Mx)                                 n= 20 fail= 15 max=2.000e+00 bar=1e-08  e.g. ['a_forearm_link: 2.000e+00', 'a_shoulder_link: 2.000e+00', 'a_upper_arm_link: 2.000e+00']
[r2]    jnt_type (exact)                                     n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_range (exact)                                    n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-A.a, exact)                               n= 14 fail=  6 max=2.000e+00 bar=exact  e.g. ['a_elbow_joint: 2.000e+00', 'a_shoulder_lift_joint: 2.000e+00', 'a_shoulder_pan_joint: 2.000e+00']
[r2]    jnt_axis (-a, reported)                              n= 14 fail= 14 max=2.000e+00 bar=exact  e.g. ['a_elbow_joint: 2.000e+00', 'a_shoulder_lift_joint: 2.000e+00', 'a_shoulder_pan_joint: 2.000e+00']
[r2]    jnt_pos (Mx, exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_stiffness (exact)                                n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    qpos_spring (exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    dof_armature/damping (exact)                         n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_type (exact)                                    n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_size (exact)                                    n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_pos (Mx, exact)                                 n= 38 fail= 30 max=5.734e-01 bar=exact  e.g. ['a_forearm_link#0: 4.615e-01', 'a_shoulder_link#0: 7.671e-06', 'a_upper_arm_link#0: 5.734e-01']
[r2]    geom_solref/solimp (exact)                           n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_friction/condim/contype/conaffinity (exact)     n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_quat non-mesh (Mx.R.Mx)                         n=  8 fail=  0 max=0.000e+00 bar=1e-12
[r2]    actuator_gainprm/biasprm (exact)                     n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_ctrlrange/forcerange/gear (exact)           n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_trntype/dyntype/gaintype/biastype (exact)   n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon_stiffness/damping/range (exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon wraps (obj names + coef, exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_type/active (exact)                               n=  3 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_data (exact)                                      n=  3 fail=  2 max=3.816e-17 bar=exact  e.g. ['0:g_left_follower:g_left_coupler: 3.816e-17', '0:g_right_follower:g_right_coupler: 2.125e-17']
[r2]    eq_solref/solimp (exact)                             n=  3 fail=  0 max=0.000e+00 bar=exact
[r2] composed_L_vs_Bperturbed (negative: one hand mass +1e-7): bodies matched 22 (L 22 / R 22; unmatched []), joints 14, geoms 38, actuators 1, tendons 1, eqs 3 | fields 28, FAILED 8: ['body_ipos (Mx, exact)', 'body_iquat (Mx.R.Mx)', 'body_mass (exact)', 'body_pos (Mx, exact)', 'eq_data (exact)', 'geom_pos (Mx, exact)', 'geom_size (exact)', 'jnt_axis (-a, reported)']
[r2]    body_mass (exact)                                    n= 20 fail=  1 max=1.000e-07 bar=exact  e.g. ['g_right_follower: 1.000e-07']
[r2]    body_inertia (exact)                                 n= 20 fail=  0 max=0.000e+00 bar=exact
[r2]    body_pos (Mx, exact)                                 n= 20 fail=  1 max=3.109e-18 bar=exact  e.g. ['g_base_mount: 3.109e-18']
[r2]    body_ipos (Mx, exact)                                n= 20 fail=  1 max=3.795e-19 bar=exact  e.g. ['g_base_mount: 3.795e-19']
[r2]    body_quat (Mx.R.Mx)                                  n= 20 fail=  0 max=6.661e-16 bar=1e-12
[r2]    body_iquat (Mx.R.Mx)                                 n= 20 fail=  3 max=2.000e+00 bar=1e-08  e.g. ['g_base_mount: 2.000e+00', 'g_left_silicone_pad: 2.000e+00', 'g_right_silicone_pad: 2.000e+00']
[r2]    jnt_type (exact)                                     n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_range (exact)                                    n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-A.a, exact)                               n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-a, reported)                              n= 14 fail=  8 max=2.000e+00 bar=exact  e.g. ['g_left_coupler_joint: 2.000e+00', 'g_left_driver_joint: 2.000e+00', 'g_left_follower_joint: 2.000e+00']
[r2]    jnt_pos (Mx, exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_stiffness (exact)                                n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    qpos_spring (exact)                                  n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    dof_armature/damping (exact)                         n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_type (exact)                                    n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_size (exact)                                    n= 38 fail= 14 max=1.041e-17 bar=exact  e.g. ['g_base#0: 6.939e-18', 'g_base#1: 6.939e-18', 'g_left_coupler#0: 8.674e-19']
[r2]    geom_pos (Mx, exact)                                 n= 38 fail= 22 max=2.776e-17 bar=exact  e.g. ['a_wrist_1_link#0: 2.776e-17', 'a_wrist_3_link#0: 2.082e-17', 'g_base#0: 6.939e-18']
[r2]    geom_solref/solimp (exact)                           n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_friction/condim/contype/conaffinity (exact)     n= 38 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_quat non-mesh (Mx.R.Mx)                         n=  8 fail=  0 max=0.000e+00 bar=1e-12
[r2]    actuator_gainprm/biasprm (exact)                     n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_ctrlrange/forcerange/gear (exact)           n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_trntype/dyntype/gaintype/biastype (exact)   n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon_stiffness/damping/range (exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon wraps (obj names + coef, exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_type/active (exact)                               n=  3 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_data (exact)                                      n=  3 fail=  2 max=2.082e-16 bar=exact  e.g. ['0:g_left_follower:g_left_coupler: 2.082e-16', '0:g_right_follower:g_right_coupler: 1.527e-16']
[r2]    eq_solref/solimp (exact)                             n=  3 fail=  0 max=0.000e+00 bar=exact
[r2] arm_stock_vs_mirrored (single asset): bodies matched 7 (L 7 / R 7; unmatched []), joints 6, geoms 7, actuators 0, tendons 0, eqs 0 | fields 19, FAILED 2: ['geom_pos (Mx, exact)', 'geom_size (exact)']
[r2]    body_mass (exact)                                    n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    body_inertia (exact)                                 n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    body_pos (Mx, exact)                                 n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    body_ipos (Mx, exact)                                n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    body_quat (Mx.R.Mx)                                  n=  6 fail=  0 max=6.661e-16 bar=1e-12
[r2]    body_iquat (Mx.R.Mx)                                 n=  6 fail=  0 max=9.259e-11 bar=1e-10
[r2]    jnt_type (exact)                                     n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_range (exact)                                    n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-A.a, exact)                               n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-a, reported)                              n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_pos (Mx, exact)                                  n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_stiffness (exact)                                n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    qpos_spring (exact)                                  n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    dof_armature/damping (exact)                         n=  6 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_type (exact)                                    n=  7 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_size (exact)                                    n=  7 fail=  1 max=1.388e-17 bar=exact  e.g. ['world#0: 1.388e-17']
[r2]    geom_pos (Mx, exact)                                 n=  7 fail=  2 max=2.776e-17 bar=exact  e.g. ['wrist_1_link#0: 2.776e-17', 'wrist_3_link#0: 2.082e-17']
[r2]    geom_solref/solimp (exact)                           n=  7 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_friction/condim/contype/conaffinity (exact)     n=  7 fail=  0 max=0.000e+00 bar=exact
[r2] hand_stock_vs_mirrored (single asset): bodies matched 15 (L 15 / R 15; unmatched []), joints 8, geoms 32, actuators 1, tendons 1, eqs 3 | fields 28, FAILED 6: ['body_ipos (Mx, exact)', 'body_iquat (Mx.R.Mx)', 'eq_data (exact)', 'geom_pos (Mx, exact)', 'geom_size (exact)', 'jnt_axis (-a, reported)']
[r2]    body_mass (exact)                                    n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    body_inertia (exact)                                 n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    body_pos (Mx, exact)                                 n= 14 fail=  0 max=0.000e+00 bar=exact
[r2]    body_ipos (Mx, exact)                                n= 14 fail=  1 max=3.795e-19 bar=exact  e.g. ['base_mount: 3.795e-19']
[r2]    body_quat (Mx.R.Mx)                                  n= 14 fail=  0 max=4.441e-16 bar=1e-12
[r2]    body_iquat (Mx.R.Mx)                                 n= 14 fail=  3 max=2.000e+00 bar=1e-08  e.g. ['base_mount: 2.000e+00', 'left_silicone_pad: 2.000e+00', 'right_silicone_pad: 2.000e+00']
[r2]    jnt_type (exact)                                     n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_range (exact)                                    n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-A.a, exact)                               n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_axis (-a, reported)                              n=  8 fail=  8 max=2.000e+00 bar=exact  e.g. ['left_coupler_joint: 2.000e+00', 'left_driver_joint: 2.000e+00', 'left_follower_joint: 2.000e+00']
[r2]    jnt_pos (Mx, exact)                                  n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    jnt_stiffness (exact)                                n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    qpos_spring (exact)                                  n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    dof_armature/damping (exact)                         n=  8 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_type (exact)                                    n= 32 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_size (exact)                                    n= 32 fail= 14 max=1.041e-17 bar=exact  e.g. ['base#0: 6.939e-18', 'base#1: 6.939e-18', 'left_coupler#0: 8.674e-19']
[r2]    geom_pos (Mx, exact)                                 n= 32 fail= 20 max=6.939e-18 bar=exact  e.g. ['base#0: 6.939e-18', 'base#1: 6.939e-18', 'base_mount#0: 3.795e-19']
[r2]    geom_solref/solimp (exact)                           n= 32 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_friction/condim/contype/conaffinity (exact)     n= 32 fail=  0 max=0.000e+00 bar=exact
[r2]    geom_quat non-mesh (Mx.R.Mx)                         n=  8 fail=  0 max=0.000e+00 bar=1e-12
[r2]    actuator_gainprm/biasprm (exact)                     n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_ctrlrange/forcerange/gear (exact)           n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    actuator_trntype/dyntype/gaintype/biastype (exact)   n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon_stiffness/damping/range (exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    tendon wraps (obj names + coef, exact)               n=  1 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_type/active (exact)                               n=  3 fail=  0 max=0.000e+00 bar=exact
[r2]    eq_data (exact)                                      n=  3 fail=  2 max=4.163e-17 bar=exact  e.g. ['0:left_follower:left_coupler: 4.163e-17', '0:right_follower:right_coupler: 4.163e-17']
[r2]    eq_solref/solimp (exact)                             n=  3 fail=  0 max=0.000e+00 bar=exact
[r2] mj_step calls: 0; driver family in sys.modules: []
```

## Appendix C — supplementary measurement (`pz_r2_inertia.py`, sha256 b96f2bc967325e6801b38e73174767261fef6b707595194a80ff83fca8c8e166; reported, not pre-registered)
```text
[r2-sup] inertia tensor under Mx (R diag(I) R^T, frame-independent): worst |diff| over 20 bodies = 1.042e-10 kg m^2
[r2-sup] iquat residual 2.000 at g_base_mount: principal moments L=[0.000102345489, 5.3599687e-05, 5.2171763e-05] B=[0.000102345489, 5.3599687e-05, 5.2171763e-05]; inertia-tensor diff 0.000e+00
[r2-sup] iquat residual 2.000 at g_left_silicone_pad: principal moments L=[2.00804e-07, 1.49536e-07, 5.1824e-08] B=[2.00804e-07, 1.49536e-07, 5.1824e-08]; inertia-tensor diff 0.000e+00
[r2-sup] iquat residual 2.000 at g_right_silicone_pad: principal moments L=[2.00804e-07, 1.49536e-07, 5.1824e-08] B=[2.00804e-07, 1.49536e-07, 5.1824e-08]; inertia-tensor diff 0.000e+00
[r2-sup] hand joint axes (L): {'g_right_driver_joint': [1.0, 0.0, 0.0], 'g_right_coupler_joint': [1.0, 0.0, 0.0], 'g_right_spring_link_joint': [1.0, 0.0, 0.0], 'g_right_follower_joint': [1.0, 0.0, 0.0], 'g_left_driver_joint': [1.0, 0.0, 0.0], 'g_left_coupler_joint': [1.0, 0.0, 0.0], 'g_left_spring_link_joint': [1.0, 0.0, 0.0], 'g_left_follower_joint': [1.0, 0.0, 0.0]}
```
```python
"""pZ R2 supplementary (reported, not pre-registered): frame-independent inertia comparison I_body = R diag(I) R^T under Mx conjugation,
principal moments of the bodies whose iquat failed, and the hand joint axes.  argv: W OUT"""
import sys, io, json, contextlib, numpy as np, mujoco
W, OUT = sys.argv[1], sys.argv[2]; sys.path.insert(0, W)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import ur15_gripper_mirror_acceptance as g
    L = g.build_side("ur15_base.xml", g.KO_LEFT, g.acc.SIDE_SIGN["L"])[0]; B = g.build_side("ur15_base_mirrored.xml", g.KO_MIRROR, g.acc.SIDE_SIGN["R"])[0]
Mx = np.diag([-1.0, 1.0, 1.0])
def q2R(q): m = np.zeros(9); mujoco.mju_quat2Mat(m, np.asarray(q, float)); return m.reshape(3, 3)
def name(m, i): return mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(i))
bL = {name(L, i): i for i in range(L.nbody)}; bR = {name(B, i): i for i in range(B.nbody)}
res = {"inertia_tensor_Mx_max_per_body": {}, "iquat_residual_per_body": {}, "principal_moments": {}, "hand_joint_axes_L": {}}
worst = 0.0
for k in sorted(set(bL) & set(bR)):
    if k in ("world", "column"): continue
    i, j = bL[k], bR[k]
    IL = q2R(L.body_iquat[i]) @ np.diag(L.body_inertia[i]) @ q2R(L.body_iquat[i]).T; IR = q2R(B.body_iquat[j]) @ np.diag(B.body_inertia[j]) @ q2R(B.body_iquat[j]).T
    d = float(np.abs(Mx @ IL @ Mx - IR).max()); res["inertia_tensor_Mx_max_per_body"][k] = d; worst = max(worst, d)
    res["iquat_residual_per_body"][k] = float(np.abs(Mx @ q2R(L.body_iquat[i]) @ Mx - q2R(B.body_iquat[j])).max())
    res["principal_moments"][k] = {"L": L.body_inertia[i].tolist(), "B": B.body_inertia[j].tolist()}
res["inertia_tensor_worst"] = worst
for ji in range(L.njnt):
    n = mujoco.mj_id2name(L, mujoco.mjtObj.mjOBJ_JOINT, ji)
    if n.startswith("g_"): res["hand_joint_axes_L"][n] = L.jnt_axis[ji].tolist()
open(OUT, "w").write(json.dumps(res, indent=1))
print(f"[r2-sup] inertia tensor under Mx (R diag(I) R^T, frame-independent): worst |diff| over 20 bodies = {worst:.3e} kg m^2")
for k, v in res["iquat_residual_per_body"].items():
    if v > 1e-8: print(f"[r2-sup] iquat residual {v:.3f} at {k}: principal moments L={np.round(res['principal_moments'][k]['L'], 12).tolist()} B={np.round(res['principal_moments'][k]['B'], 12).tolist()}; inertia-tensor diff {res['inertia_tensor_Mx_max_per_body'][k]:.3e}")
print(f"[r2-sup] hand joint axes (L): {res['hand_joint_axes_L']}")
```

## Provenance
The run's JSON and log under the scratchpad; the perturbed hand xml written beside the original inside the archive only. Zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-426.
