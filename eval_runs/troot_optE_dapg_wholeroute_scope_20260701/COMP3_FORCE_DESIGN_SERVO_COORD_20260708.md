# /force-design — comp3 grip servo close (Stage-B design-gate) — %11 COORD

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec — comp3 (grasp_actuation flag-flip) Stage-B design-gate.
**trigger:** %12 06:08 — /force-design on servo close (inherited gains + condim6 + PAD_SOLREF vs SRG D1 SSOT drift-check + dt/substep 整合). PLANNING (no-GPU, paper).
**⛔ scope note:** comp3 introduces **ZERO new force parameters**. Every gain/limit/contact constant is INHERITED from `task_config.py` (SSOT) via the PROVEN `build_scene(grasp_actuation=True)` path that SRG (S0/S1/S2) validated at 4-substep. This gate = **drift-check + hierarchy + dt-consistency verification**, NOT a new force design. Skill demands artifacts regardless → produced below.
**⚠ substrate = Newton/mujoco-ko (NOT PhysX/VBD):** the skill's default hierarchy table (Arm PD ke=400 / VBD SOFT_CONTACT / GRASP_KE spring) is PhysX/VBD-scoped and does NOT apply. mujoco-ko uses POSITION-servo drivers + mj contact (condim/solref/impratio). Adapted below (prohibited.md PhysX/Newton 混同禁止).

---

## 1. パラメータ (all INHERITED — 変更値 == 現在値, no change)
| パラメータ | 値 | file:line | grasp_actuation が読む先 | SRG-validated? |
|---|---|---|---|---|
| GRIPPER_SERVO_TARGET_KE | 66.7 | task_config.py:314 | base:1594 `proto.joint_target_ke[dof]` | ✅ S1/S2 4-sub GRIP_GO |
| GRIPPER_SERVO_TARGET_KD | 2.0 | task_config.py:315 | base:1595 `proto.joint_target_kd[dof]` | ✅ |
| GRIPPER_DRIVER_EFFORT_LIMIT_NM | 2.5 (~5N tendon×0.5) | task_config.py:316 | base:1596 `proto.joint_effort_limit[dof]` | ✅ (cage holds) |
| GRIPPER_DRIVER_OPEN_RAD | 0.0 (gap 85.4mm) | task_config.py:289 | base:1597 `proto.joint_target_pos[dof]` (start) | ✅ |
| GRIPPER_DRIVER_CLOSE_RAD | 0.7407 (=q free-air 4.0mm) | task_config.py:291 | recorded grip_cmd schedule (runner CLOSE) | ✅ |
| GRIPPER_DRIVER_JOINT_IDX | [6,10] (→[6,10,20,24] both) | task_config.py:34 | base:1588-1591 driver-index assert | ✅ |
| MUJOCO_CONTACT_CONDIM | 6 (rolling rows) | task_config.py:176 | register_custom_attributes base:1540 | ✅ D1 |
| MUJOCO_PAD_SOLREF | (-65789.0, -2105.3) TRUE-overdamp | task_config.py:187 | `_wire_s6_grasp_solref` base:1389 (mj+mjw all-worlds) | ✅ D1 |
| MUJOCO_OPT_IMPRATIO | 10.0 | task_config.py:196 | mj option (built) | ✅ D1 |

**Change to task_config.py = NONE.** comp3 = flag-wire (§4 of comp3 plan) + reuse. build_multiworld grasp_actuation ON reads the SAME constants build_scene does (base:1586-1600 verbatim) → no drift by construction.

## 2. 階層整合性 (mujoco-ko servo, adapted)
The route env arm is **kinematic** (joint_q overwrite :791), NOT PD — so the PhysX "Arm PD > Contact > Grasp" force-competition does not apply. The ONLY PD-force layer is the gripper POSITION servo. Hierarchy for comp3:
| 層 | 機構 | coords | force | vs 隣接層 | 判定 |
|---|---|---|---|---|---|
| Arm | kinematic joint_q write (comp4 flag-ON) | {0-5,14-19} `_ARM_OVERWRITE_LOCAL` | ∞ (positional) | disjoint from gripper | ✅ |
| Gripper servo | POSITION drive ke=66.7/kd=2.0/eff=2.5N | {6-13,20-27} `_GRIPPER_COORDS_LOCAL` | ≤2.5N per driver | driven, NOT overwritten | ✅ |
| Pad↔cable contact | condim=6 + PAD_SOLREF overdamp + impratio=10 | pad box geoms | reaction | transmits servo close → cage | ✅ |
| Cable | rigid-link REVOLUTE chain (mujoco) | {28-73}/world | — | caged by form-closure | ✅ |
- **⭐ Key: comp4 write-site exclusion makes arm-kinematic ({0-5,14-19}) and gripper-servo ({6-13,20-27}) DISJOINT** → the kinematic arm drive does NOT fight the servo close (no competition, no pin). This is precisely why comp3⊕comp4 are inseparable (comp3 plan §5). flag-OFF = 28-wide write pins gripper OPEN (inert = v1.5 defect); flag-ON = disjoint = servo closes.
- **effort_limit=2.5N adequacy:** koshape grip is a form-closure CAGE (not a friction pinch) — the servo need only close the 4-bar to the cage config, not exert large clamp force. SRG S1/S2 confirmed the cage HOLDS (cage-escape lateral/z within DROP margins) at effort=2.5N. ✅
- ✅ hierarchy INTACT (no inversion; disjoint coords remove the classic competition).

## 3. dt依存性 (the substep question — RESOLVED consistent)
PD servo effective force is dt-dependent: `F = ke*(target-q) - kd*(q-q_prev)/dt`.
| context | substep | dt | role |
|---|---|---|---|
| oracle/monolith (Layer-A) | SIM_SUBSTEPS=10 | SIM_DT=1/4800 | arm TRAJECTORY byte-repro |
| route env (comp3 target) | RL_SIM_SUBSTEPS=4 | RL_SIM_DT=1/1920 | **grip servo runs HERE** |
| SRG S0/S1/S2 (grip measure) | **4** (`T.SIM_SUBSTEPS=4`) | DT/4 | **grip force MEASURED HERE** |
- ⭐ **The grip servo in comp3 runs at RL_SIM_SUBSTEPS=4 == the substep SRG MEASURED the grip at.** So there is **NO un-validated dt change for the grip force**: SRG S0 explicitly re-measured the creep floor at 4-substep (koshape 4-sub 1.29µm/f vs 10-sub 3.25µm/f → K_clean 0.40 ≪ 3.5 = no regime change — LEDGER:47, node state.md:30). S1/S2 cage-escape ran at 4-substep = GRIP_GO.
- The 10-substep is a DIFFERENT concern (Layer-A arm-trajectory byte-repro, already CLOSED 81/81) — it is NOT the grip-force dt. The grip force is dt-consistent with its own SRG validation.
- ✅ dt-consistency SATISFIED (grip servo dt == grip measurement dt).

## 4. 感度テスト (SRG IS the sensitivity characterization — cite, no redundant re-run)
The force-sensitivity of THIS exact servo+contact config is already measured by SRG (creep-budgeted, 4-substep, cuda:0-cg). No-GPU constraint + non-redundancy → cite SRG rather than re-run:
| lever (skill-ranked) | SRG evidence | result |
|---|---|---|
| servo close (ke/kd/eff, 4-sub) | S1 nominal cage-escape | GRIP_GO (z-drop 6.93mm/10, lat 1.53mm/60) |
| solver firmness (cg vs newton) | S1 CPU de-confound | firmer holds TIGHTER → cg pessimistic-passed = conservative-favourable |
| offset/DR tail | S2 5-cell (nominal+4 corners) | GRIP_GO all; WORST=nominal (offset RELIEVES sag) |
| creep floor (intrinsic) | S0 axial | 1.29µm/f 4-sub, no-regime |
- SRG banked levers (noslip_iterations 110×, impratio ∝1/impratio) = campaign-affecting, NOT touched by comp3 (inherited defaults). substep 4→N = Rs-level, NOT proposed.
- ⚠ non-conservative axis (SRG carry): grip measured on **build_scene single-world scripted**; the **build_multiworld env-drive multi-world live close = G1 GPU-deferred** (a wiring/substrate question, NOT a force-param question — the params are identical).

## 5. 変更ファイル + 実装制約 (force-design binding) — ⚠ (a) REWORDED per 5体 R2
- **task_config.py change = NONE.** comp3 = flag-wire + RouteExecutor grip-applier (comp3 plan v2 §4/§5/§6).
- ⛔ **(a) grip = recorded grip_cmd STAIRCASE replayed EXACT per-physics-frame (5体 R2 correction):** ~~my v1 "proven ramp, no instant jump" was a MISCHARACTERIZATION~~ — the recorded schedule IS engineered **jumps + staircase** (NOT a smooth ramp): cage90 = instant→0.667 then 12×12 to 0.7407 (run_route:1565-1577); L_HALF_UNCLAMP transit hold L=0.69 while R re-grasps (:2071/:2091/:2418); SRG itself closed with a single jump (srg_probe:307). The skill's 指閉じ漸進化 anti-jump rule is SATISFIED because the recorded staircase IS the PROVEN close (not an arbitrary target the solver can't track). ⛔ **NO thresholding/smoothing/re-ramping**; the {0,1} threshold (build plan §6) is phase/is_dual ONLY. Mechanism = a RouteExecutor-owned accessor reading `_recording["grip_cmd"]` [L,R] at physics frame cf[t]+i, [L,R]→per-arm driver dofs, read→mutate→`.assign()` (device-robust; a `.numpy()` host copy never reaches the solver — 5体 CC3-CH5). route_executor.py enters the file set.
- **(b) ⚠ solref NOTIFY-FRAGILE (base:1360):** `_wire_s6_grasp_solref` pokes BOTH mj_model AND mjw all-worlds (base:1389-1402). L3 leg reads BOTH; **per 5体 CC3-CH7 + R3: on the as-coded CPU substrate, `mj_model` is authoritative** (mjw recorded inert); a GPU path (if ever) would use the dual-read as a preflight. 4-bar eq stiffening = mj_model-template-only; **mjw eq re-poke DEFERRED by design (base:1355-1358) — comp3 FORBIDS mjw eq re-poke** (CC3-CH6).
- **(c) substrate (5体 R3): the route env runs mujoco-CPU newton (USE_MUJOCO_CPU=True, solver="newton" hardwired), NOT cuda:0-cg.** ⭐favorable: this cpu-newton substrate is the one SRG's de-confound found holds TIGHTER (0.09/0.54mm vs cuda:0-cg 1.53/6.93mm) = conservative-FAVOURABLE prior. dt-consistency (substep=4) UNCHANGED and still holds.

## VERDICT = PASS (LIGHT — inherited, hierarchy-intact, dt-consistent, SRG-characterized)
- No new force parameters; all inherited from task_config SSOT + the proven build_scene(grasp_actuation=True) path.
- Hierarchy intact (arm-kinematic ⟂ gripper-servo via comp4 exclusion; no competition).
- dt-consistent (grip servo runs at RL_SIM_SUBSTEPS=4 == SRG measurement substep; NO un-validated dt change).
- Sensitivity = SRG (S0/S1/S2 4-substep) = GRIP_GO conservative-favourable.
- **binding implementation constraints carried (5体 R2/R3 corrected):** (a) grip = recorded grip_cmd STAIRCASE replayed EXACT per-physics-frame (jumps+holds ARE the proven schedule; NO threshold/smooth/re-ramp; RouteExecutor accessor + read→mutate→.assign() device-robust); (b) L3 leg reads mj_model authoritative on the CPU substrate (mjw inert; dual-read = GPU preflight if ever); mjw eq re-poke FORBIDDEN; (c) `_settled_fk_jq` gripper patch AR:866-872 flag-ON.
- **Residual (NOT a force-param question):** live close in the env-drive loop = **G1 on the as-coded mujoco-CPU-newton substrate (world-0/nominal)** = GPU-cost leg, Rs-deferred. ⭐direction FAVOURABLE-prior (cpu-newton = SRG-de-confound firmer), but env-drive path + staircase fidelity measured by G1 (comp3 plan v2 §7/§13).

---
*%11 COORD (w2:p3) 2026-07-10. /force-design comp3 servo. No-GPU paper. PASS-LIGHT (inherited params). Pairs with COMP3_GEOMETRIC_DESIGN (void). → both PASS → %12 5体 [VERIFY].*
