# CANONICAL comp3 grasp point-data ledger v1 (Rs directive #6, 2026-07-11)

> NEAR/手前 = R arm (lane Y 0.194); FAR/奥 = L arm (lane Y 0.106) -- camera-verified dfbe7fca0b. rise is hook-capable; read WITH z_drop (clamp-retention).

Machine-extracted from banked run JSONs (comp3_point_data_ledger_v1.py). Standing rule (Rs #6): key point data supplied to this ledger same-turn as the result bank.

### T1 z_drop [mm] (clamp-retention; lower=better)

| cell | scene | L_z_drop_mm | R_z_drop_mm | provenance |
|---|---|---|---|---|
| dz+0 | FLAT | 88.701 | 33.37 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+3 | FLAT | 84.913 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+4 | FLAT | 27.685 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+5 | FLAT | 8.963 | 5.699 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| R+3/L+0 | FLAT | 78.367 | 15.856 | 73c246f812 FLAT ik_chord R+3/L+0 |
| dz+0 | SUPPORTED[confounded] | 52.971 | 28.534 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| dz+3 | SUPPORTED[confounded] | 46.922 | 27.718 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| dz+4 | SUPPORTED[confounded] | 36.498 | 23.015 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| dz+5 | SUPPORTED[confounded] | 15.185 | 13.583 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |

### T2 claw z @close [m] (per-arm height; Rs #3 symmetry)

| cell | scene | claw_z_L | claw_z_R | claw_dz_LmR_mm | provenance |
|---|---|---|---|---|---|
| dz+0 | FLAT | 0.80583 | 0.80583 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+3 | FLAT | 0.80885 | 0.80884 | 0.01 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+4 | FLAT | 0.80982 | 0.80984 | -0.02 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+5 | FLAT | 0.81084 | 0.81084 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |

### T3 lane cable z [m] + L-R diff [mm] (seesaw substrate)

| cell | scene | cable_z_lane_L | cable_z_lane_R | lane_LmR_mm | provenance |
|---|---|---|---|---|---|
| dz+0 | FLAT | 0.80403 | 0.80447 | -0.44 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+3 | FLAT | 0.79565 | 0.79844 | -2.79 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+4 | FLAT | 0.79579 | 0.78913 | 6.66 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+5 | FLAT | 0.79614 | 0.79809 | -1.95 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |

### T4 bend close-window peak [deg] by scene

| cell | scene | bend_peak_L_deg | bend_peak_R_deg | provenance |
|---|---|---|---|---|
| dz+0 | FLAT | 39.48 | 51.55 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+3 | FLAT | 47.41 | 59.79 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+4 | FLAT | 37.13 | 45.92 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+5 | FLAT | 2.66 | 4.91 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| R+3/L+0 | FLAT | 46.54 | 48.91 | 73c246f812 FLAT ik_chord R+3/L+0 |
| dz+0 | SUPPORTED | 2.99 | 6.89 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| dz+3 | SUPPORTED | 1.37 | 11.38 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| dz+4 | SUPPORTED | 1.96 | 2.81 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| dz+5 | SUPPORTED | 2.42 | 3.57 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |

### T5 per-arm park z [m] (commanded depth)

| condition | R_park_EE_z | R_park_pinch_z | L_park_EE_z | L_park_pinch_z | provenance |
|---|---|---|---|---|---|
| recording nominal | 1.0668 | 0.80588 | 1.0668 | 0.80588 | 39b206ddb0 baseline geometry |
| uniform +3 | 1.0698 | 0.80888 | 1.0698 | 0.80888 | 39b206ddb0 baseline geometry |
| R+3/L+0 (Rs #5) | 1.0698 | 0.80888 | 1.0668 | 0.80588 | 73c246f812 FLAT ik_chord R+3/L+0 |

### T6 rise [mm] (lift outcome; hook-capable, read with T1 z_drop)

| cell | scene | rise_L_mm | rise_R_mm | provenance |
|---|---|---|---|---|
| dz+0 | FLAT | -39.7 | 16.1 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+3 | FLAT | -7.0 | 76.5 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+4 | FLAT | -6.4 | 28.2 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| dz+5 | FLAT | 0.0 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| R+3/L+0 | FLAT | -29.2 | 34.4 | 73c246f812 FLAT ik_chord R+3/L+0 |
