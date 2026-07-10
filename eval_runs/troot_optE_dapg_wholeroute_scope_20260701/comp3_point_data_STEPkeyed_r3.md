# comp3 grasp point-data -- STEP-keyed r3 (Rs #6 fmt; for p5 §1.2 unified-table integration)

> NEAR/手前 = R arm (lane Y 0.194); FAR/奥 = L arm (lane Y 0.106) -- camera-verified dfbe7fca0b. rise is hook-capable; read WITH z_drop (clamp-retention).
> Canonical 43-step map (full_43step.json, phase-A initial pick): STEP2 Above / STEP3 Descend(park z) / STEP4 Clamp(grasp) / STEP5 Lift. Machine-extracted; per-row provenance. r3 = this integration round.

## STEP 3 -- Descend to cable (per-arm PARK z, commanded) [m]
| condition | R_pinch_z (手前) | L_pinch_z (奥) | R_EE_z | L_EE_z | provenance |
|---|---|---|---|---|---|
| recording nominal | 0.80588 | 0.80588 | 1.0668 | 1.0668 | 39b206ddb0 baseline geometry |
| uniform +3 | 0.80888 | 0.80888 | 1.0698 | 1.0698 | 39b206ddb0 baseline geometry |
| R+3/L+0 (Rs #5) | 0.80888 | 0.80588 | 1.0698 | 1.0668 | 73c246f812 FLAT ik_chord R+3/L+0 |

## STEP 4 -- Clamp cable (grasp; close-window measurements)
Primary: per-arm claw z @close = SYMMETRIC <=0.05mm (claws descend equally; the L/R height diff Rs saw on the slot videos was a slot-contact artifact, absent on flat).

| footnote | cell | scene | L | R | provenance |
|---|---|---|---|---|---|
| claw_z@close [m] | dz+0 | FLAT | 0.80583 | 0.80583 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| claw_z@close [m] | dz+3 | FLAT | 0.80885 | 0.80884 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| claw_z@close [m] | dz+4 | FLAT | 0.80982 | 0.80984 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| claw_z@close [m] | dz+5 | FLAT | 0.81084 | 0.81084 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| lane_cable_z L-R [mm] | dz+0 | FLAT | 0.80403 | 0.80447 (L-R=-0.44) | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| lane_cable_z L-R [mm] | dz+3 | FLAT | 0.79565 | 0.79844 (L-R=-2.79) | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| lane_cable_z L-R [mm] | dz+4 | FLAT | 0.79579 | 0.78913 (L-R=6.66) | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| lane_cable_z L-R [mm] | dz+5 | FLAT | 0.79614 | 0.79809 (L-R=-1.95) | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| bend_peak [deg] | dz+0 | FLAT | 39.48 | 51.55 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| bend_peak [deg] | dz+3 | FLAT | 47.41 | 59.79 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| bend_peak [deg] | dz+4 | FLAT | 37.13 | 45.92 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| bend_peak [deg] | dz+5 | FLAT | 2.66 | 4.91 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| bend_peak [deg] | R+3/L+0 | FLAT | 46.54 | 48.91 | 73c246f812 FLAT ik_chord R+3/L+0 |
| bend_peak [deg] | dz+0 | SUPPORTED | 2.99 | 6.89 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| bend_peak [deg] | dz+3 | SUPPORTED | 1.37 | 11.38 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| bend_peak [deg] | dz+4 | SUPPORTED | 1.96 | 2.81 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| bend_peak [deg] | dz+5 | SUPPORTED | 2.42 | 3.57 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |

## STEP 5 -- Lift cable (retention; z_drop is the clamp-quality proxy, rise is hook-capable)
| footnote | cell | scene | L | R | provenance |
|---|---|---|---|---|---|
| z_drop_end [mm] | dz+0 | FLAT | 88.701 | 33.37 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| z_drop_end [mm] | dz+3 | FLAT | 84.913 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| z_drop_end [mm] | dz+4 | FLAT | 27.685 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| z_drop_end [mm] | dz+5 | FLAT | 8.963 | 5.699 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| z_drop_end [mm] | R+3/L+0 | FLAT | 78.367 | 15.856 | 73c246f812 FLAT ik_chord R+3/L+0 |
| z_drop_end [mm] | dz+0 | SUPPORTED[confounded] | 52.971 | 28.534 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| z_drop_end [mm] | dz+3 | SUPPORTED[confounded] | 46.922 | 27.718 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| z_drop_end [mm] | dz+4 | SUPPORTED[confounded] | 36.498 | 23.015 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| z_drop_end [mm] | dz+5 | SUPPORTED[confounded] | 15.185 | 13.583 | 47c075dad9 (verdict c1a9d66523) 2-slot SUPPORTED [CONFOUNDED per footprint retraction 44aacb92a5] |
| rise [mm] | dz+0 | FLAT | -39.7 | 16.1 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| rise [mm] | dz+3 | FLAT | -7.0 | 76.5 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| rise [mm] | dz+4 | FLAT | -6.4 | 28.2 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| rise [mm] | dz+5 | FLAT | 0.0 | 0.0 | 5227d9e916 (verdict 00e191e4ba) FLAT ik_chord |
| rise [mm] | R+3/L+0 | FLAT | -29.2 | 34.4 | 73c246f812 FLAT ik_chord R+3/L+0 |

## Load-bearing reads for p5 §1.2
- ik_chord holds the NEAR(R/手前) arm (z_drop 0 at uniform dz3) but NEVER the FAR(L/奥) arm at any depth; only FEEDFORWARD (D rho=0, f8b1ff6b4c) holds L. STEP4/5 are the failing legs on ik_chord.
- per-arm depth is CABLE-COUPLED (R+3/L+0 -> R z_drop 15.9mm vs uniform-dz3 R 0.0mm): R-only depth does NOT recover R's uniform-depth quality. VN-2 R-only-+3..4mm is NOT a clean independent lever.
- seesaw substrate real (lane cable z L-R flips sign with dz) but the outcome winner (R) does not flip.