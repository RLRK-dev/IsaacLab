# UR15 dual-arm assembly cell

Two UR15 arms on an angled Y yoke over a rotating column, with Robotiq 2F-85 grippers and a stereo head between the arms.

Lengths in m, angles in rad. Frame: cell origin at the centre of the plinth, +Z up, +Y towards the line.

## Mounting

| Item | Value |
| --- | --- |
| yoke_angle_deg | 45.0 |
| yoke_spread_m | 0.22 |
| yoke_rise_m | 0.0 |
| shoulder_height_m | 1.53 |
| column_radius_m | 0.102 |
| column_stem_bottom_m | 0.37 |
| column_stem_height_m | 1.16 |

Arm base pose, left (row-major 4x4):

```
   0.707107  -0.000000  -0.707107  -0.220000
   0.000000   1.000000  -0.000000   0.000000
   0.707107   0.000000   0.707107   1.530000
   0.000000   0.000000   0.000000   1.000000
```

## Arm

| Joint | origin xyz | origin rpy |
| --- | --- | --- |
| shoulder | [0.0, 0.0, 0.2186] | [0.0, 0.0, 0.0] |
| upper_arm | [0.0, 0.0, 0.0] | [1.570796, 0.0, 0.0] |
| forearm | [-0.6475, 0.0, 0.0] | [0.0, 0.0, 0.0] |
| wrist_1 | [-0.5164, 0.0, 0.1824] | [0.0, 0.0, 0.0] |
| wrist_2 | [0.0, -0.1361, 0.0] | [1.570796, 0.0, 0.0] |
| wrist_3 | [0.0, 0.1434, 0.0] | [1.570796, 3.141593, 3.141593] |

Every joint turns about its own +Z. The base carries a 3.14159 rad yaw before the chain starts, and the flange is rotated twice to reach tool0 — the values are in the JSON.

## End effector

| Item | Value |
| --- | --- |
| model | Robotiq 2F-85 |
| grip_point_offset_from_tool0_m | 0.19 |
| finger_travel_rad | [0.0, 0.8] |
| pad_size_m | [0.022, 0.00635, 0.0375] |

## Stereo head

| Item | Value |
| --- | --- |
| pitch_below_horizontal_deg | 45.0 |
| baseline_m | 0.176 |
| body_size_m | [0.24, 0.085, 0.075] |

## Envelope

Drawn in the `turn` pose.

| Item | Value |
| --- | --- |
| bounds min | [-0.7571, -0.3, -0.04] |
| bounds max | [0.7571, 0.345, 1.7711] |
| size | [1.5141, 0.645, 1.8111] |

## Poses

Joint values are for the left arm; the right arm is the exact kinematic mirror. `tuned` are the values hand-set against the flat mounting the cell was first built on; `on yoke` are the values that put the tool in the same place on the angled Y yoke actually built. The residual is how far the retargeted pose misses the tuned tool position.

| Pose | joints on yoke (left) | tool0 position | residual |
| --- | --- | --- | --- |
| home | -3.1521, -0.2867, +2.4674, -1.3953, +1.5634, -1.5782 | -0.300, -0.180, +1.140 | 0.0000 |
| stock_high | -2.0905, -0.0995, +0.9340, +0.2754, +2.2316, -0.6803 | -0.300, -0.845, +1.080 | 0.0000 |
| stock | -2.1195, +0.3445, -0.0000, +0.4983, +2.1427, -0.8549 | -0.302, -0.971, +0.946 | 0.3225 |
| housing_load_high | -2.1271, -0.2781, +1.3392, -0.2857, +1.8676, -0.8998 | -0.288, -0.819, +1.112 | 0.0000 |
| connector_insert_high | -2.3236, -0.3350, +1.6089, -0.2336, +1.9716, -1.0207 | -0.326, -0.606, +1.078 | 0.0000 |
| main_route_high | -2.1475, -0.3368, +1.4576, -0.2807, +1.8685, -0.9221 | -0.296, -0.769, +1.135 | 0.0000 |
| branch_route_high | -2.0612, -0.1818, +1.1944, -0.2890, +1.8405, -0.8719 | -0.228, -0.883, +1.103 | 0.0000 |
| clip_seat_high | -2.1016, -0.1795, +1.2753, -0.2718, +1.8522, -0.8963 | -0.218, -0.820, +1.081 | 0.0000 |
| strain_relief_high | -2.1017, -0.2815, +1.3651, -0.2887, +1.8520, -0.8971 | -0.264, -0.816, +1.130 | 0.0000 |
| cover_place_high | -2.0520, -0.4261, +1.5206, -0.3161, +1.8107, -0.8967 | -0.280, -0.804, +1.233 | 0.0000 |
| latch_press_high | -2.0896, -0.1641, +1.1982, -0.2774, +1.8505, -0.8838 | -0.230, -0.861, +1.077 | 0.0000 |
| electrical_test_high | -2.0871, -0.2619, +1.3317, -0.2909, +1.8473, -0.8893 | -0.254, -0.833, +1.128 | 0.0000 |
| vision_inspect_high | -2.0037, -0.5873, +1.6665, -0.3474, +1.7566, -0.9021 | -0.304, -0.789, +1.342 | 0.0000 |
| housing_load | -2.2336, +0.0616, +0.8932, -0.2654, +1.9538, -0.9235 | -0.261, -0.837, +0.878 | 0.0000 |
| connector_insert | -2.4330, -0.0146, +1.1860, -0.2499, +2.0489, -1.0260 | -0.300, -0.620, +0.840 | 0.0000 |
| main_route | -2.2561, -0.0099, +1.0424, -0.2656, +1.9614, -0.9336 | -0.270, -0.788, +0.902 | 0.0000 |
| branch_route | -2.1684, +0.1785, +0.6969, -0.2453, +1.9269, -0.9013 | -0.198, -0.898, +0.870 | 0.0000 |
| clip_seat | -2.2116, +0.1695, +0.7945, -0.2436, +1.9403, -0.9186 | -0.187, -0.834, +0.848 | 0.0000 |
| strain_relief | -2.2107, +0.0513, +0.9326, -0.2648, +1.9435, -0.9141 | -0.237, -0.835, +0.898 | 0.0000 |
| cover_place | -2.1643, -0.1155, +1.1559, -0.2823, +1.9161, -0.8972 | -0.258, -0.828, +1.006 | 0.0000 |
| latch_press | -2.1967, +0.2010, +0.6869, -0.2385, +1.9346, -0.9145 | -0.199, -0.875, +0.843 | 0.0000 |
| electrical_test | -2.1961, +0.0740, +0.8912, -0.2633, +1.9382, -0.9083 | -0.226, -0.850, +0.896 | 0.0000 |
| vision_inspect | -2.1190, -0.2897, +1.3576, -0.3005, +1.8741, -0.8927 | -0.287, -0.818, +1.121 | 0.0000 |
| turn | -3.4927, +0.3103, +2.9501, -2.4881, +0.9986, -1.8063 | -0.276, -0.211, +1.333 | - |
