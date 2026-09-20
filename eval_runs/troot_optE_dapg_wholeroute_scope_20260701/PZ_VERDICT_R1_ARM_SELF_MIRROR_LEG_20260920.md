# pZ — verdict on leg R1 (arm self-mirror on the composed arm-only models), rows R1-1..8 of `PZ_R1_ARM_SELF_MIRROR_LEG_PREREG_20260920.md` @ `3a3b5bbc6e`, judged against the bars fixed there before the single run

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 14:26:14 JST on m-p18-426 (p4 m-p4-288 (2), order W → R1′ → R1). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. **Landed ≠ accepted**: acceptance is p4's word.

**Order of existence**: pre-registration committed `3a3b5bbc6e` at 14:24:39 JST (sha256 `3ae3b83f78047630…`; seed 20260920, M 24, radius 0.1 rad, bars fixed; instrument outputs asserted absent at writing) → **one** run of `pz_r1.py` (appendix A, sha256 `b52621fa0927cc8e…` = the pre-registered sha) finishing 14:24:51 JST → this verdict; nothing re-drawn, no parameter changed. HEAD at writing `c7e8d0787d`. Objects = the blobs pinned in the pre-registration (unchanged: commits touching `ur15_mirror_acceptance.py` after `92059373a3` = 0); leg run in the `git archive` of `92059373a3`; env7 `3.12.3 mujoco 3.11.0 numpy 2.3.1 scipy 1.17.0`. **Run 0**; `mj_step` = 0; driver family in `sys.modules` = `[]`. **Stop-cause tag: none.**

## Verdict per row

| # | row (bar) | verdict | measured |
|---|---|---|---|
| R1-1 | identity map at HOME_POSE: 6 link bodies, pos ≤ 1e-3 mm, rot ≤ 1e-6 rad | **CONFIRMED** | identity max pos **4.59e-13 mm** (at HOME_POSE), max rot **3.29e-16 rad** (at HOME_POSE) |
| R1-2 | the reference's 24 left on-yoke poses (JSON sha256 `20ac0935c707757c…`) | **CONFIRMED** | 24 poses: identity max pos **1.26e-12 mm** (at cover_place), max rot **6.59e-16 rad** (at housing_load_high) |
| R1-3 | 24 random in-limit draws, seed 20260920, exclusion radius 0.1 rad from `q*` | **CONFIRMED** | 24 draws (rejected by the exclusion: **0** — no draw fell within 0.1 rad of `q*`; the rule was armed, not exercised): identity max pos **1.17e-12 mm** (at draw0), max rot **7.62e-16 rad** (at draw21). Draws listed in appendix C |
| R1-4 | negative control (i) = the R-form on the mirrored arm; wrist_3 margin ≥ 10 mm on every pose | **CONFIRMED (fires everywhere)** | HOME **664.701 mm** (p11's CC4 expectation 664.70 ✓); reference-24 min **357.675 mm** at `turn` (p11's 357.68 ✓); random-24 min **29.877 mm** at `draw12` (this desk's draws; p11's own draws gave 51.3 — a different seed, both ≥ 10 mm). Min over poses of the max-link margin: 1242.1 / 452.2 / 128.5 mm |
| R1-5 | negative control (ii) = the stock arm on the right mount, identity q; ≥ 10 mm | **CONFIRMED (fires everywhere)** | min wrist_3 margins **664.701 / 357.675 / 29.877 mm** (HOME / reference / random) — **numerically identical to control (i)** on every pose: the R-form on the mirrored arm reproduces the rotated-copy machine's wrist position exactly, which is p11 `:24`'s statement 「R 式は非鏡像機（stock 腕を右 mount へ）の経路」 measured |
| R1-6 | the fixed point under control (i): margin ≈ 0 (≤ 1e-6 mm) | **CONFIRMED** | `R-form(q*) = q*`; margin at `q*` = **1.09e-12 mm** — the exclusion has a cause |
| R1-7 | control invariance / no run | **CONFIRMED** | `mj_step` 0; driver not imported; `mj_kinematics` only; overrides unset (mount = C-2 defaults {'YOKE_SPREAD': 0.28, 'TILT_rad': 1.2217304763960306, 'SHOULDER_HEIGHT': 1.5299999999999998}) |
| R1-8 | pins | **CONFIRMED** | pre-registration `3a3b5bbc6e`; instrument sha256 `b52621fa0927cc8ebb9ea89b45793c1bac0b5ca548c05c36412ddda7a5d9b033`; LIMS = [[-6.283185307179586, 6.283185307179586], [-6.283185307179586, 6.283185307179586], [-3.141592653589793, 3.141592653589793], [-6.283185307179586, 6.283185307179586], [-6.283185307179586, 6.283185307179586], [-6.283185307179586, 6.283185307179586]]; HOME_POSE = [-3.1521, -0.2867, 2.4674, -1.3953, 1.5634, -1.5782] |

**Reading (fact, not design)**: on the composed arm-only models the mirrored arm is the x-mirror of the stock arm under the **identity** joint map to ~1e-12 mm / ~1e-15 rad on 49 poses × 6 link bodies (positions and frames), while the reference's own right-column rule (the R-form) and the rotated-copy arm both miss by 30-1242 mm and coincide with each other. The reference-24 negative margins reproduce p11's CC4 derivation to 0.01 mm on the two reproducible sets.

## What this leg does not show (holes)
- Arm link bodies on the arm-only builder: no hand (R1′), no masses / inertias / joint ranges / actuators (R2), no motion or contact (#69); tool0's rotation is not a row by construction (pre-registration's note).
- The exclusion radius was not exercised (0 rejections): its effect on the draw set is untested here; only its cause (R1-6) is.
- The C-2 default mount only; the identity predicates are mount-independent by construction, but no second mount was run.

## Appendix A — instrument output (verbatim, `r1.log`)
```text
[r1] mount {'YOKE_SPREAD': 0.28, 'TILT_rad': 1.2217304763960306, 'SHOULDER_HEIGHT': 1.5299999999999998} | LIMS [(-6.283185307179586, 6.283185307179586), (-6.283185307179586, 6.283185307179586), (-3.141592653589793, 3.141592653589793), (-6.283185307179586, 6.283185307179586), (-6.283185307179586, 6.283185307179586), (-6.283185307179586, 6.283185307179586)] | seed 20260920 M 24 radius 0.1 rejected 0 | ref json sha256 20ac0935c707757c
[r1] set HOME_POSE                    n= 1: identity max pos 4.592e-13 mm (at HOME_POSE), max rot 3.294e-16 rad (at HOME_POSE) | neg R-form: min wrist_3 664.701 mm (at HOME_POSE), min over poses of max-link 1242.073 mm | neg RC identity: min wrist_3 664.701 mm (at HOME_POSE)
[r1] set reference_24_left_on_yoke    n=24: identity max pos 1.261e-12 mm (at cover_place), max rot 6.590e-16 rad (at housing_load_high) | neg R-form: min wrist_3 357.675 mm (at turn), min over poses of max-link 452.243 mm | neg RC identity: min wrist_3 357.675 mm (at turn)
[r1] set random_24_seed_20260920      n=24: identity max pos 1.166e-12 mm (at draw0), max rot 7.621e-16 rad (at draw21) | neg R-form: min wrist_3 29.877 mm (at draw12), min over poses of max-link 128.509 mm | neg RC identity: min wrist_3 29.877 mm (at draw12)
[r1] fixed point q*=[0.0, 1.5707963267948966, 0.0, 1.5707963267948966, 0.0, 0.0]: R-form(q*)=[-0.0, 1.5707963267948966, -0.0, 1.5707963267948966, -0.0, -0.0] -> negative-control margin at q* = 1.093e-12 mm
[r1] mj_step calls: 0; driver family in sys.modules: []
```

## Appendix B — per pose (49 rows): distance to `q*` [rad], identity max pos [mm] / rot [rad] over the 6 bodies, negative (i) wrist_3 / max-link [mm], negative (ii) wrist_3 [mm]
| set | pose | d(q, q*) | id pos | id rot | neg(i) wrist_3 | neg(i) max link | neg(ii) wrist_3 |
|---|---|---|---|---|---|---|---|
| HOME | HOME_POSE | 3.131 | 4.59e-13 | 3.29e-16 | 664.701 | 1242.073 | 664.701 |
| reference | home | 3.131 | 5.28e-13 | 3.38e-16 | 664.675 | 1242.056 | 664.675 |
| reference | stock_high | 2.232 | 8.97e-13 | 3.66e-16 | 749.548 | 749.548 | 749.548 |
| reference | stock | 2.143 | 1.07e-12 | 5.10e-16 | 941.632 | 941.632 | 941.632 |
| reference | housing_load_high | 2.127 | 1.01e-12 | 6.59e-16 | 687.868 | 687.868 | 687.868 |
| reference | connector_insert_high | 2.324 | 5.98e-13 | 2.01e-16 | 789.012 | 836.173 | 789.012 |
| reference | main_route_high | 2.148 | 7.04e-13 | 5.09e-16 | 665.375 | 666.469 | 665.375 |
| reference | branch_route_high | 2.061 | 4.48e-13 | 4.17e-16 | 615.784 | 615.784 | 615.784 |
| reference | clip_seat_high | 2.102 | 6.06e-13 | 3.59e-16 | 631.850 | 645.070 | 631.850 |
| reference | strain_relief_high | 2.102 | 5.44e-13 | 3.75e-16 | 628.073 | 629.886 | 628.073 |
| reference | cover_place_high | 2.052 | 1.12e-12 | 3.44e-16 | 505.442 | 545.837 | 505.442 |
| reference | latch_press_high | 2.090 | 1.07e-12 | 2.79e-16 | 654.085 | 654.085 | 654.085 |
| reference | electrical_test_high | 2.087 | 8.08e-13 | 3.82e-16 | 615.748 | 617.510 | 615.748 |
| reference | vision_inspect_high | 2.158 | 5.80e-13 | 3.04e-16 | 385.386 | 452.243 | 385.386 |
| reference | housing_load | 2.234 | 7.45e-13 | 2.89e-16 | 979.291 | 979.291 | 979.291 |
| reference | connector_insert | 2.433 | 8.79e-13 | 4.51e-16 | 1088.872 | 1088.872 | 1088.872 |
| reference | main_route | 2.256 | 3.98e-13 | 2.98e-16 | 958.139 | 958.139 | 958.139 |
| reference | branch_route | 2.168 | 5.64e-13 | 3.43e-16 | 902.333 | 902.333 | 902.333 |
| reference | clip_seat | 2.212 | 6.91e-13 | 3.96e-16 | 918.579 | 918.579 | 918.579 |
| reference | strain_relief | 2.211 | 8.50e-13 | 4.94e-16 | 917.885 | 917.885 | 917.885 |
| reference | cover_place | 2.164 | 1.26e-12 | 3.35e-16 | 794.634 | 794.634 | 794.634 |
| reference | latch_press | 2.197 | 1.20e-12 | 4.80e-16 | 940.958 | 940.958 | 940.958 |
| reference | electrical_test | 2.196 | 9.33e-13 | 3.09e-16 | 904.633 | 904.633 | 904.633 |
| reference | vision_inspect | 2.119 | 9.75e-13 | 3.27e-16 | 672.125 | 672.125 | 672.125 |
| reference | turn | 2.950 | 5.28e-13 | 1.83e-16 | 357.675 | 1157.922 | 357.675 |
| random | draw0 | 3.111 | 1.17e-12 | 3.14e-16 | 619.901 | 867.866 | 619.901 |
| random | draw1 | 3.058 | 5.24e-13 | 2.76e-16 | 266.062 | 621.313 | 266.062 |
| random | draw2 | 2.606 | 5.09e-13 | 2.43e-16 | 77.205 | 157.371 | 77.205 |
| random | draw3 | 3.099 | 4.44e-13 | 2.70e-16 | 494.337 | 622.833 | 494.337 |
| random | draw4 | 2.891 | 4.87e-13 | 2.41e-16 | 809.147 | 1185.691 | 809.147 |
| random | draw5 | 2.642 | 6.30e-13 | 3.42e-16 | 56.399 | 549.979 | 56.399 |
| random | draw6 | 2.704 | 1.12e-12 | 1.44e-16 | 81.258 | 128.509 | 81.258 |
| random | draw7 | 2.874 | 4.79e-13 | 3.06e-16 | 317.871 | 849.753 | 317.871 |
| random | draw8 | 2.850 | 3.14e-13 | 6.08e-16 | 540.758 | 540.758 | 540.758 |
| random | draw9 | 2.406 | 4.15e-13 | 4.56e-16 | 198.836 | 436.943 | 198.836 |
| random | draw10 | 2.543 | 4.55e-13 | 2.83e-16 | 426.710 | 507.473 | 426.710 |
| random | draw11 | 3.052 | 2.31e-13 | 3.86e-16 | 339.672 | 759.469 | 339.672 |
| random | draw12 | 2.826 | 6.50e-13 | 4.50e-16 | 29.877 | 558.431 | 29.877 |
| random | draw13 | 3.002 | 5.09e-13 | 5.84e-16 | 979.225 | 979.225 | 979.225 |
| random | draw14 | 2.502 | 7.39e-13 | 4.17e-16 | 233.210 | 703.246 | 233.210 |
| random | draw15 | 2.298 | 8.99e-13 | 3.21e-16 | 1542.728 | 1542.728 | 1542.728 |
| random | draw16 | 2.785 | 5.98e-13 | 2.96e-16 | 1896.500 | 2100.244 | 1896.500 |
| random | draw17 | 2.997 | 4.97e-13 | 4.73e-16 | 474.845 | 788.354 | 474.845 |
| random | draw18 | 2.776 | 4.48e-13 | 2.87e-16 | 583.333 | 583.333 | 583.333 |
| random | draw19 | 2.890 | 7.08e-13 | 5.88e-16 | 690.754 | 690.754 | 690.754 |
| random | draw20 | 2.752 | 5.55e-13 | 5.11e-16 | 284.442 | 284.442 | 284.442 |
| random | draw21 | 2.561 | 7.11e-13 | 7.62e-16 | 1337.822 | 1337.822 | 1337.822 |
| random | draw22 | 2.165 | 1.04e-12 | 2.61e-16 | 508.395 | 508.395 | 508.395 |
| random | draw23 | 2.967 | 7.77e-13 | 5.06e-16 | 319.446 | 527.190 | 319.446 |

## Appendix C — the 24 pre-registered draws (seed 20260920, uniform in LIMS; verbatim from `r1.json`)
```text
draw0: [-5.733448, -5.115586, -0.187175, -1.601170, +5.264870, +3.534354]
draw1: [+1.198132, -3.183682, +2.141146, -0.154490, -3.057816, -3.233312]
draw2: [-1.811187, -1.035122, +0.096608, +5.299659, -4.942598, +5.208824]
draw3: [+2.688586, +4.669641, -2.543777, +5.621258, -6.057813, -0.477806]
draw4: [-5.871915, +6.235951, -1.829043, -5.068373, -2.204587, -3.392205]
draw5: [-5.253996, -5.680517, -2.641846, -0.493964, -4.329946, +5.532917]
draw6: [-1.464128, +3.512286, -0.269984, -2.008727, +2.283065, +4.364530]
draw7: [+3.408744, +3.964199, +2.593946, +1.219007, +5.504083, -4.653285]
draw8: [+1.700539, +2.065313, -2.571237, +5.485818, -5.066047, -2.849610]
draw9: [-4.226030, +5.518884, -2.320514, -0.835023, +1.171266, -0.181664]
draw10: [+5.525608, -4.142673, +2.542763, +3.966442, +4.026265, -0.410645]
draw11: [+3.231022, -0.941204, -2.937683, +2.844479, +2.051877, -3.893969]
draw12: [-5.412091, +0.837115, +2.017047, -4.691830, +4.141719, -3.457247]
draw13: [-0.514903, -1.431122, +2.209122, +1.390063, +5.594305, -3.556334]
draw14: [-2.469596, -5.479306, +2.238257, +5.627874, -2.501604, +5.967846]
draw15: [+5.746508, +0.505885, +1.073840, +2.605114, -0.896702, +3.985194]
draw16: [-2.785091, -6.155687, +0.245310, +3.269515, -4.462814, +2.382805]
draw17: [-2.996849, -4.049748, -2.580127, -1.913740, -1.140235, +1.840141]
draw18: [-1.524491, -1.936123, -2.438370, -1.083809, -5.864793, +1.081644]
draw19: [-2.478437, +1.415474, +2.427245, +0.136108, +1.511753, -2.890403]
draw20: [-5.047974, -1.111247, +2.752327, +2.668607, -5.333721, -0.759553]
draw21: [+5.659413, -3.805679, +1.606318, +5.503727, -3.722018, -4.974809]
draw22: [-1.604618, -6.036462, +0.547463, -2.547825, +0.703107, -4.267980]
draw23: [+5.140238, -2.947166, +0.919765, -0.314675, +1.322284, -2.966904]
```

## Provenance
The run's JSON and log under the scratchpad; the instrument is appendix A of the pre-registration (sha equal); the archive is the one used by W and R1′. Zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-426.
