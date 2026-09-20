<!--
Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
-->

# UR15-B: current cell identity and controller specification

Adopted by Rs1 (p19), 2026-09-21, under the user's explicit Rs1 assignment and instruction to proceed.
This lands DDR 68's accepted design in 04-Specs. It records the existing implementation and its evidence limits.

## Current identity

- The current MuJoCo cell has a left UR15 and a right UR15-B. UR15-B is this project's mirrored counterpart of UR15, named by the user's 2026-08-10 directive; it is not asserted to be a manufacturer's separate product.
- The right arm uses `ur15_base_mirrored.xml` with model identity `UR15-B`; its mirrored hand remains a separately identified asset. This specification does not invent a new hand name.
- Both arms remain required. The IK-only rule and existing prohibitions on physics-bypass control continue to apply.

## Controller contract

- Reuse the existing per-arm 6D damped-least-squares IK and position-servo class. Apply the identity joint-value mapping between corresponding mirrored arm poses; do not substitute the reference's non-mirrored right-arm formula.
- Measure and supply each side's tool axes, joint/actuator addresses, pads, tool body and menu sign separately. The identity joint mapping does not assert that identical world-space targets produce mirrored trajectories.
- The live solver is `ur15_steps_wired.py::solve_ik`. The R0 convergence instrument must demonstrate equivalence to that solver and must not advance physics or import the executable driver. R0 establishes convergence only; it does not establish collision avoidance, grasp or dynamic tracking.
- Record both sides at driver startup using the accepted controller-record fields: side, class, AXFIX axes, QADR/VADR/AIDX/GIDX/PAD/TOOLB, sign and design revision. The recorded design revision remains `dc090f7753`, even when later explanatory sections are appended.
- D4 measures the displayed posture cap separately for each arm. This instrumentation change does not alter the motion acceptance gate.
- Stop reporting distinguishes instrumentation/calibration failure, the defined IK/convergence failure and other causes. Run #69's tracking-gate stall is recorded as other, with its specific cause description; it is not relabelled as an R0 failure.
- Keep commencement, implementation, independent verification and acceptance separate. If the existing class cannot represent the B-side requirement, stop and report before changing the control method.

## Accepted evidence and provenance

All abbreviated paths below are under `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/`.

| Object | Accepted record |
| --- | --- |
| User naming and controller directives | p4 kickoff, `e00a990c45` and `1d9974face` |
| Design and later clarifications | `P11_UR15B_CONTROLLER_DESIGN_20260913.md`, section 17 first pinned at `dc090f7753`; accepted R2 comparison correction in section 17.20 at `7b61c9ae2f` |
| D4 and controller record implementation | `3370f7a872` and `96e9ece175` |
| R0 and supplementary target report | p4 acceptance `30897c8a49` and `668e85b26f` |
| R1, R1′ and R2 independent legs | p4 acceptance `e092941348`, `9d6dcccf3f` and `ddbc39ac61` |
| Reference bundle | `p4_ur15_sim_20260727/reference/ur15-dual-arm-cell/`, import `e6172b2e3b`, independent collation `170cbf54a7` |
| Completion declaration | p4 kickoff item 67, `8dd5188a67`, 2026-09-20 15:14:44 JST |

The earlier design-review failures remain part of the record. This landing relies on the later accepted static implementation/verification chain; it does not claim that a third five-agent design-review cycle was conducted.

## Runtime limits and remaining work

Run #69 executed once and stopped at STEP2 with left-arm tracking stalled. Its row 7 and R3 startup records and the built model's parameter collation were reported by pB/pZ; these are not proof of successful motion. pC reported that the close view was occluded and grasp could not be measured visually. Rs1's stopped-run visual review is recorded separately in `RS1_RUN69_REVIEW_20260921.md`.

Static controller completion does not establish dynamic collision clearance, grasp, retention, full-route completion or the suitability of the C-2 mounting. The 0.22/45 reference configuration and the C-2 0.28/20 configuration must retain their distinct provenance; reference-position results from one are not evidence for the other. This landing does not choose a mounting change or authorize another run.

DDR 68's current identity/controller specification is reflected by this page together with RS71 section 0/1 and SOMA's current-cell note. D4′, unrelated WIP and the full-route execution decisions retain their separate scope.
