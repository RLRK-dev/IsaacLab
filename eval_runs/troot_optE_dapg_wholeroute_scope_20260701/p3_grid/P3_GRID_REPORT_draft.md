# P3-GRID REPORT (DRAFT — %11 aggregate; %9 re-count + %12/%9 joint read finalizes)

cells parsed = 81 (expect 81). infra = 0 (no-json 0 / non-finite 0).
class counts: strict=59  seat_miss(any-seat∧¬strict, rider-1)=21  FAIL=1  infra=0

## SR (PREREG §2 + A1; PRIMARY=strict, SECONDARY=any-seat)
- PRIMARY strict (SUCCESS*∧seated_honest): 59/81 winnable-candidate = 0.728 (Wilson95 [0.623,0.813]) | 59/81 all-cells = 0.728 [0.623,0.813] (winnable EXCLUDES draw cells -> %9/%12 joint-read finalizes)
- SECONDARY any-seat (SUCCESS*): 80/81 winnable-candidate = 0.988 (Wilson95 [0.933,0.998]) | 80/81 all-cells = 0.988 [0.933,0.998] (winnable EXCLUDES draw cells -> %9/%12 joint-read finalizes)
- evidence-gate (PREREG §2): strict SR ≥95% -> M-C bites (α-DR: perturb/obs-noise) / ≤80% -> position-DR+c2 / mid -> Rs
- ≥95% certify needs n_winnable≥59 (rule-of-3). candidate winnable = 81.

## Derivations (PREREG §4)
- corner-miss: R reach residual [mm] (row2 p_hit input): n=81 p1=0.10 p50=0.90 p99=1.12 max=1.20
- corner-miss: c2 wall dist [mm] (pos=off-wall/miss, neg=seated; c1->c2 Δ bound input): n=81 p1=-2.22 p50=-0.52 p99=16.39 max=17.98
- dual-grip achieved span [mm] (row3, target=88): n=81 p1=92.42 p50=92.42 p99=92.42 max=92.42
- episode length [RAW FRAMES] (row4): n=81 p1=7706.00 p50=7708.00 p99=7712.00 max=7712.00
  -> CONTROL-STEPS = frames/10: p99≈771 ctrl-steps (horizon unit). horizon 900 OK (<810 bump thresh). n<100 -> max-of-n conservative.
- c2_seat_dist [mm] (neg=penetrated/seated): n=81 p1=-2.22 p50=-0.52 p99=16.39 max=17.98
- ⭐ c2z_gap [mm] (DOMINANT seat separator, %9/%12 13:35-38; cable Z at c2 − groove ref 829.0): n=81 p1=-0.12 p50=0.40 p99=45.80 max=56.20
    strict-class: n=59 p1=-0.14 p50=0.30 p99=2.77 max=3.00 | seat_miss+FAIL: n=22 p1=3.14 p50=7.00 p99=53.47 max=56.20
- c2 regrasp tilt [deg]: n=81 p1=-23.95 p50=-21.35 p99=9.87 max=9.93
- max_slip_xy [mm]: n=81 p1=0.66 p50=2.36 p99=2.80 max=2.80

## 2D offset-grid map (rows dy=+20(top)..-20(bottom), cols dx=-20..+20 mm)
(p_hit object, %12 2026-07-05: Delta_EE common-mode compensates cable offset ~1:1 (first order) -> P(correction
 lands in success region) = success-region SHAPE in offset space = THIS map. Witness-vector only sets within-
 cell curvature; 5mm pitch ~ sigma 2-7.5mm same scale -> grid resolution suffices. (a) is more direct, not a compromise.)
class (. strict / s seat_miss / X FAIL / ? no-json / ! non-finite):
         dx=  -20  -15  -10   -5    0    5   10   15   20
  dy=  20       .    .    s    s    .    .    .    s    s
  dy=  15       s    s    .    .    s    .    .    .    .
  dy=  10       .    .    s    .    .    .    .    .    .
  dy=   5       X    .    .    .    s    s    s    s    .
  dy=   0       .    s    .    .    .    .    .    .    .
  dy=  -5       .    .    .    .    .    .    .    .    .
  dy= -10       .    .    .    .    .    s    s    s    .
  dy= -15       s    s    .    .    .    .    .    .    .
  dy= -20       .    .    s    s    s    .    .    .    .
signed c2_wall_dist [mm] (+off-wall/miss, -seated = wall-normal directed component):
         dx=    -20    -15    -10     -5      0      5     10     15     20
  dy=  20      -0.5   -0.5   -0.3   -0.3   -0.6   -0.5   -0.7   -0.3   -0.3
  dy=  15      -0.8   16.0   -0.7   -0.5   -0.4   -0.5   -2.1   -2.1   -2.1
  dy=  10      -0.3   -0.4   -0.4   -0.4    0.0   -0.8   -0.8   -0.4   -0.8
  dy=   5      12.7   -0.6   -0.6   -0.6   -0.6   -0.5   -0.5   -0.3   -0.4
  dy=   0      -0.8    1.3   -0.7   -2.1   -0.4   -2.1   -2.2   -2.1   -2.2
  dy=  -5       0.0   -0.4   -0.4   -0.4   -0.7   -0.8   -0.8   -0.3   -0.8
  dy= -10      -0.6   -0.8   -0.6   -0.5   -0.6   -0.5   18.0   -0.3   -0.3
  dy= -15      -2.4   -0.7   -0.7   -0.4   -0.4   -2.1   -2.2   -2.1   -2.1
  dy= -20      -0.5   -0.3   -0.4   -0.2   -0.2   -0.4   -0.3   -0.3   -0.8
⭐ c2z_gap [mm] (DOMINANT separator, %9/%12 13:35-38: strict≈0, miss perches +Z above groove):
         dx=    -20    -15    -10     -5      0      5     10     15     20
  dy=  20       0.2    0.5    7.1    6.9    2.0    3.0    2.3    4.6    8.8
  dy=  15       3.9   43.2   -0.1    1.4   10.6    0.5    0.1    0.2    0.2
  dy=  10       0.3    0.3   12.9    0.3    0.3    0.1    0.1    0.1    0.2
  dy=   5       5.7    0.4    0.7    0.7    3.1    3.8    4.0    4.1    0.0
  dy=   0       1.5   25.5    2.6    0.3    1.6    0.1    0.1    0.2    0.2
  dy=  -5       0.3    0.4    0.8    0.3    0.3    0.2    0.1    0.1    0.2
  dy= -10       1.1    0.6    0.6    0.8    0.4    3.6   15.3    4.1   -0.1
  dy= -15      56.2    3.3   -0.2    0.7    1.3    0.2    0.2    0.2    0.2
  dy= -20       0.3    0.4   13.2   14.1   15.2    0.2    0.3    0.2    0.1
NOTE (real separating axis = Z): seat-miss is separated by Z (cable perched above groove), NOT lateral wall
  (wall within margin = NON-separating). z_gap = the p_hit-relevant miss magnitude; c2_wall identifies only the
  3 XY-lateral-tail cells. in_groove(z) leg = the failing measure for all 22 non-strict (%9/%12 joint-read 13:35-40).
RESERVED (per-cell XY-lateral miss vector): c2_miss_dx/dy_mm + c1_miss_dx/dy_mm — !! DO NOT re-invent from npz nodes.
  WHY ABSENT (evidence, rider r-a2): producer c2_wall_dist (test_newton_clip_routing.py:4743) = mujoco geom<->
  geom SURFACE min-dist (_min_dist_mm(cable_geoms, c2_wall_g)); its 2D witness points are NOT saved in JSON/npz.
  c2x/c2y (JSON) = CONSTANT target (0.40/0.075) NOT landing. Naive nearest-cable-node-to-target proxy gives
  |miss|=40.2mm vs producer scalar 12.655mm = 3x off = INVALID (would mislead p_hit sigma). Correct fill =
  model reload + mj_geomDistance witness at joint-read, ONLY if within-cell curvature resolution is needed.

## Draw-class CANDIDATES (PREREG §3 step1 forensics; corner-vs-draw line = joint-read step2)
FAIL cells (1) + seat_miss cells (21) — per-cell forensics (miss geom classified provisionally):
     x-20_y5 cls=FAIL      verdict=R_MISS_AT_88 r_grip=0.0 reach_resid=0.4mm achieved_span=92.42mm (excess=4.42) c2_wall=12.655mm ⭐c2z_gap=5.7mm rpad_c1=42.22mm -> seat/other
   x-20_y-15 cls=seat_miss verdict=SUCCESS_R_GRIP_L_CAGE_AT_88 r_grip=125.41 reach_resid=0.4mm achieved_span=92.42mm (excess=4.42) c2_wall=-2.418mm ⭐c2z_gap=56.2mm rpad_c1=40.557mm -> seat/other
    x-20_y15 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=73.11 reach_resid=0.9mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.795mm ⭐c2z_gap=3.9mm rpad_c1=40.438mm -> seat/other
   x-15_y-15 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=67.88 reach_resid=0.9mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.739mm ⭐c2z_gap=3.3mm rpad_c1=40.568mm -> seat/other
     x-15_y0 cls=seat_miss verdict=SUCCESS_R_GRIP_L_CAGE_AT_88 r_grip=26.42 reach_resid=1.0mm achieved_span=92.42mm (excess=4.42) c2_wall=1.344mm ⭐c2z_gap=25.5mm rpad_c1=40.528mm -> seat/other
    x-15_y15 cls=seat_miss verdict=SUCCESS_R_GRIP_L_CAGE_AT_88 r_grip=28.55 reach_resid=1.0mm achieved_span=92.42mm (excess=4.42) c2_wall=15.996mm ⭐c2z_gap=43.2mm rpad_c1=40.451mm -> seat/other
   x-10_y-20 cls=seat_miss verdict=SUCCESS_R_GRIP_L_CAGE_AT_88 r_grip=73.99 reach_resid=0.8mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.433mm ⭐c2z_gap=13.2mm rpad_c1=41.909mm -> seat/other
    x-10_y10 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=90.45 reach_resid=0.8mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.447mm ⭐c2z_gap=12.9mm rpad_c1=41.772mm -> seat/other
    x-10_y20 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=75.62 reach_resid=0.2mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.278mm ⭐c2z_gap=7.1mm rpad_c1=42.229mm -> seat/other
    x-5_y-20 cls=seat_miss verdict=SUCCESS_R_GRIP_L_CAGE_AT_88 r_grip=76.98 reach_resid=0.9mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.176mm ⭐c2z_gap=14.1mm rpad_c1=41.882mm -> seat/other
     x-5_y20 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=43.78 reach_resid=0.2mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.313mm ⭐c2z_gap=6.9mm rpad_c1=42.192mm -> seat/other
     x0_y-20 cls=seat_miss verdict=SUCCESS_R_GRIP_L_CAGE_AT_88 r_grip=143.93 reach_resid=0.9mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.19mm ⭐c2z_gap=15.2mm rpad_c1=41.956mm -> seat/other
       x0_y5 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=99.95 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.558mm ⭐c2z_gap=3.1mm rpad_c1=42.115mm -> seat/other
      x0_y15 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=62.03 reach_resid=0.9mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.401mm ⭐c2z_gap=10.6mm rpad_c1=40.475mm -> seat/other
     x5_y-10 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=84.71 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.499mm ⭐c2z_gap=3.6mm rpad_c1=42.196mm -> seat/other
       x5_y5 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=91.69 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.485mm ⭐c2z_gap=3.8mm rpad_c1=42.198mm -> seat/other
    x10_y-10 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=74.9 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=17.98mm ⭐c2z_gap=15.3mm rpad_c1=42.206mm -> seat/other
      x10_y5 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=91.63 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.473mm ⭐c2z_gap=4.0mm rpad_c1=42.196mm -> seat/other
    x15_y-10 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=103.22 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.313mm ⭐c2z_gap=4.1mm rpad_c1=42.2mm -> seat/other
      x15_y5 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=94.34 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.295mm ⭐c2z_gap=4.1mm rpad_c1=42.199mm -> seat/other
     x15_y20 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=108.53 reach_resid=0.1mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.292mm ⭐c2z_gap=4.6mm rpad_c1=42.2mm -> seat/other
     x20_y20 cls=seat_miss verdict=SUCCESS_DUAL_LOADED_AT_88 r_grip=79.32 reach_resid=0.2mm achieved_span=92.42mm (excess=4.42) c2_wall=-0.325mm ⭐c2z_gap=8.8mm rpad_c1=42.163mm -> seat/other

## Conservatism (PREREG §5): script grid = α base behavior; for β = UPPER bound on 'script-solvable support' (NOT β from-P0 SR).
## Verification scope (video-leg, §運用14): visual leg OMITTED-with-justification (loud, not silent) — this RESULT is
  a NUMERIC verdict-aggregate over the PRODUCER's pinned honest metrics (c2_seated_honest geom-dist :4756 / c2_regrasp
  :4805 = validated success criteria), over the banked Rs-confirmed WORKING square-on route (nominal x0_y0 byte-
  identical to b2_cpC), varying only CABLE_XY_OFFSET (DR sweep, NOT a new motion-capability claim). Targeted video =
  joint-read step2 ONLY for specific FAIL/seat_miss cells whose miss MECHANISM needs visual confirm before draw-class.