# COMP3 PLAN — route-executor Stage-B grasp_actuation flag-flip + FORK-1 build_multiworld CLOSE-kinematics validation — %11 COORD (w2:p3)

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec (IN_PROGRESS) — charter %12, D-1=C.
**re-trigger:** %12 RS-TECH-LEAD 2026-07-10 05:57 JST — Rs 方向確定 = comp3 へ進む。**PLANNING only (no-GPU, structural plan; GPU spend = plan+[VERIFY] 後に別途 Rs surface)**.
**extends:** BUILD_PLAN_ROUTEEXEC_LAYERB_COORD_20260707.md (v0.2.2 `62fcbefe57`) §2 comp3+comp4 (thin rows) → 本 doc = full Stage-B comp3 plan.
**status:** PLANNING (paper-only). No code. No GPU. → %12 [VERIFY] gate.

---

## §0. Grounding (anchor set, §運用4) — read + cited

| SSOT | file:line | grounded fact |
|---|---|---|
| LEDGER (成否SSOT) | `07-Design/00-DESIGN-STATUS-LEDGER.md:47` | ⟦07-08 02:42 SRG COMPLETE⟧ = 4-substep grip premise ROBUST; **comp3 = FORK-1 multiworld-close validation** (3 carry flags). minimal Stage-A COMPLETE ⟦07-07 17:29⟧. |
| node state.md | `T-ROOT-...-P2-routeexec/state.md:16,30-32` | minimal Stage-A COMPLETE (comp1+comp2, 3-leg gate PASS no-GPU); Stage-B = comp3-8 HELD; SRG carry **FORK-1 = build_multiworld CLOSE NOT established by SRG**. |
| build plan | `BUILD_PLAN_ROUTEEXEC_LAYERB_COORD_20260707.md:32-33` (§2) | comp3 = grasp_actuation flag-flip (:391 default False→flag, §10.1, grip activation); comp4 = 3-pattern write-site FLAG-GATED (CC4-C1: flag-OFF byte-exact 28-wide / flag-ON gripper-excluded). |
| 5体 verdict | `LAYERB_5TAI_VERIFY_VERDICT_RSTECHLEAD_20260707.md:29,33,42` | CC4-C1 HIGH (write-site exclusion MUST be flag-gated; flag-OFF byte-exact); CC4-SOUND (grasp_actuation byte-clean by construction — all 4 mutations gated, else rebuilds identical solid table); CC6 (4=DEFER grasp_actuation=ON only). |
| route env call site | `envs/newton_route_env.py:391-399` | `build_multiworld_scene(...)` passes add_support_clips/add_target_clip/target_clip_float_z, **grasp_actuation NOT passed → default False** (the %9 gap). |
| base signature+gates | `envs/newton_skill_env_base.py:1492,1537,1586,1738,1905` | `grasp_actuation=False` param **already in signature (:1492)**; 4 gated mutations (§6 below). |
| route env write-sites | `envs/newton_route_env.py:440,670,791` | 3 sites write full 28-wide `phys_jq[jq0:jq0+28]` INCLUDING gripper {6-13,20-27} → kinematic pin (fingers forced OPEN :747-749/:777-780). |
| route_executor machinery | `envs/route_executor.py:80-81,181,206,229,290` | **BUILT + unit-PASS**: `_GRIPPER_COORDS_LOCAL`{6-13,20-27} / `apply_arm_only_write_broadcast` / `_perworld` (gripper-excluded) / `set_gripper_target` (servo single-writer) / `servo_seed_assert`. |
| SRG probe (precedent) | `troot_optE_srg_probe_20260707/srg_probe.py` + node state.md:30 | grip ROBUST on **build_scene** (scripted single-world); void-parity build_scene==build_multiworld void [0.090,0.210]; worst=nominal. FORK-1 = the build_multiworld delta. |

⚠ SOMA (`04-Specs/SOMA.md`) carries no route-executor/grasp_actuation row yet = planning-surface freshness gap (PLAN-KEEPER/%12 charter surface, NOT this task; LEDGER is the current 成否SSOT).

## §1. [TASK]/[L-TRIAGE] = L3 (high-care, invariant-PRESERVING — NOT immediate-STOP)
- **path-match**: newton_route_env.py (core) → §0 L3 auto-escalate. **diff-keyword**: grasp_actuation / servo / physics / ik / gravity(void geom) → L3. **>200L / ≥3 files** (planned).
- **FOUNDATIONAL INVARIANT check** (RS71 §0): comp3 does NOT change DUAL-ARM / 88mm span / DiffIK-only / gripper geometry / no-kinematic-trick. grasp_actuation flip = **model-servo activation (proven build_scene mirror), NOT a kinematic pin** — it REMOVES a kinematic pin (gripper) in favour of POSITION-servo physics → invariant-PRESERVING → high-care L3, NOT immediate-STOP. Rs=A (`bad0d25204`) authorizes the cross-node flag-gate source-edit.
- **PLANNING artifact** = this doc (L0-L1 doc write). The PLANNED code (comp3/comp4) is L3 → gated by %12 [VERIFY] (this doc) → later 5体 + design-gate + RULE-CHECK before any build (per build plan §5 Stage-B chain).

## §2. comp3 objective = FORK-1 build_multiworld CLOSE-kinematics validation
**The residual gap SRG could NOT close.** SRG (S0/S1/de-confound/S2) proved the 4-substep koshape grip CAGES + HOLDS the cable ROBUSTLY — but on the **build_scene** substrate (scripted single-world pinch: SEED arms + ik-descend + close). FORK-1 = **does the same gripper CLOSE + CAGE + HOLD in build_multiworld_scene** (the RL env: multi-world, per-world cable FREE-root offset, `_apply_actions_batch` kinematic-arm-drive + `route_executor` step_target targets + POSITION-servo grip, 4-substep, cuda:0-cg)?

**Delta build_scene(SRG) → build_multiworld(comp3):**
| axis | build_scene (SRG proved) | build_multiworld (comp3 must prove) | conservatism |
|---|---|---|---|
| worlds | 1 (single) | 4+ (per-world offset, cable FREE-root world-offset) | multi-world = NEW (world≥1 index correctness) |
| arm drive | scripted `grasp_cable` (SEED+ik-descend) | `_apply_actions_batch` kinematic write + route step_target | drive-path NEW |
| grip drive | `T._set_gripper_target` close | `route_executor.set_gripper_target(grip_cmd)` servo | wiring NEW (comp4) |
| substep | 4 (S1/S2) | 4 (RL_SIM_SUBSTEPS) | **MATCHED** (SRG carries) |
| void geom | build_scene void [0.090,0.210] | build_multiworld void [0.090,0.210] (base:1738) | **PARITY** (SRG void-gate) |
| solver | cuda:0-cg (S1/S2) | cuda:0-cg | **MATCHED** |

⇒ SRG gives a HIGH PRIOR (grip robust, substep+void+solver matched); the genuinely-unproven delta = **the env drive-path + multi-world + comp4 write-site wiring**. comp3 validates that delta.

## §3. %9 grasp_actuation gap resolution = **STAGED-GAP** (NOT wiring-omission) — DECIDED
%9 finding (env-core [VERIFY]): `newton_route_env.py` build_multiworld_scene call does NOT pass grasp_actuation, but `test_newton_clip_routing.py:3715` asserts `scene_info.get("grasp_actuation")` REQUIRED for the S6_GRASP_ROUTE (live route) path. Is the missing kwarg a **staged-gap** (intentional) or a **wiring-omission** (bug)?

**VERDICT = STAGED-GAP (intentional), 5 independent evidences (all §運用4-grounded):**
1. **Signature already accepts it** — `build_multiworld_scene(..., grasp_actuation=False, ...)` base:1492. The wire EXISTS at the callee; only the caller's kwarg is (intentionally) omitted → default-off. A wiring-omission bug would be a signature that CAN'T receive it.
2. **Default-off = env-core byte-preserve BY CONSTRUCTION** — CC4-SOUND (verdict:33): "all 4 scene mutations gated, else rebuilds identical solid table". env-core node was validated + Rs-video-gate PASSED with grasp_actuation=False; passing True would CHANGE the scene (void, servo) → BREAK env-core byte-identity (gate-iii). So omission is REQUIRED for Stage-A byte-preserve.
3. **build plan §2 comp3 EXPLICITLY defers it** — row 32: "grasp_actuation flag-flip (:391 default False→flag) | **B** | grip activation, bundle w/ SRG". It was scoped as Stage-B from v0.2.
4. **The code docstring says so** — newton_route_env.py:334-336: "Note (Stage-A scope): the flag-ON env is not rolled out in Stage-A ... a live flag-ON run ... belong to the Stage-B / trainer stage."
5. **test:3715 CONSISTENT, not contradictory** — the assert says the LIVE route path NEEDS grasp_actuation=True. Stage-A route_executor is **recorded_replay only (live CUT, Q1)** → no live grip → grasp_actuation legitimately OFF. Stage-B comp3 flips it ON → live grip → satisfies test:3715's requirement. The two are the SAME staged design, not a conflict.

⇒ **comp3 ADDS the kwarg as a flag-gate** (default-off preserves env-core; flag-on enables live grip). NOT a bug-fix; the intended Stage-B activation. **%9's finding is CORRECTLY tracked as a comp3 input** (it names the exact site + the test-3715 consumer that comp3 must satisfy).

## §4. comp3 mechanism = grasp_actuation flag-flip (newton_route_env.py:391)
- Add a cfg flag (e.g. `cfg["grasp_actuation"]`, default False = 4th flag, Rs=A range). At the `build_multiworld_scene(...)` call :391, pass `grasp_actuation=self.cfg.get("grasp_actuation", False)`.
- **flag-OFF** (default) = kwarg False (or omitted-equivalent) → env-core byte-identity (solid table, no servo, fingers-open kinematic) = **CC4-C1 / gate-iii preserved**.
- **flag-ON** = grasp_actuation=True → the 4 base mutations (§6) fire: void 4-box, POSITION servo drivers, condim6, 4-bar + `_wire_s6_grasp_solref`.
- ~10-25 LOC (build plan §2). Bundle with comp4 (§5) — inseparable.

## §5. CC4-C1 write-site flag-gate = **INSEPARABLE design constraint** (%12 requirement 3)
**Why inseparable:** grasp_actuation ON builds the POSITION-servo drivers, but the 3 kinematic write-sites STILL write the full 28-wide `phys_jq[jq0:jq0+28]` every frame (:440/:670/:791) INCLUDING gripper coords {6-13,20-27}. That KINEMATICALLY PINS the gripper open → the servo can never close it = the **v1.5 "inert grip" defect** (node state.md 03:0x, 5体 CRIT). So comp3 (flag-ON grip) is USELESS without comp4 (gripper-exclusion). They MUST build+validate together.

**The invariant (DESIGN CONSTRAINT, plan-binding):**
- **flag-OFF** → each write-site keeps the current 28-wide `phys_jq[jq0:jq0+28]=...` (+ `phys_jqd=0`) INCLUDING gripper = **byte-exact** (env-core preserve). Guarded by B⑨a′ = **full-arm_q sha incl gripper coords** (CC4-C4; else gripper drift invisible).
- **flag-ON** → each write-site uses the BUILT `route_executor.apply_arm_only_write_*` (writes ONLY `_ARM_OVERWRITE_LOCAL`{0-5,14-19}; gripper {6-13,20-27} NEVER indexed → stays DYNAMIC) + `set_gripper_target(control.joint_target_pos, drivers, grip_cmd)` drives the servo close. gripper qd also excluded from the `phys_jqd=0` zero (servo must accelerate).
- **3 sites** (current line#): `_broadcast_arm_jointq`:440 (broadcast, grip-close arm-hold) → `apply_arm_only_write_broadcast`; `_apply_actions_batch`:791 (per-world drive) → `apply_arm_only_write_perworld`; `_reset_worlds`:670 (per-world reset) → banked-restore (§8-B / F5, arm+gripper from state_bank when flag-ON). Also the fingers-OPEN forcing :747-749/:777-780 must become grip_cmd-driven when flag-ON.
- **REUSE, do not reimplement** — the machinery is BUILT + unit-PASS in route_executor.py (state.md 08:09 `d2e3a4e73c`, no-repin ground-truth PASS). comp4 = the WIRING (flag-branch) into the env, not new code.

## §6. The 4 grasp_actuation mutations (base) + geometry parity (SRG-validated)
grasp_actuation=True fires (base):
1. **:1537-1540** — condim=6 pad rolling-friction custom-attr register (SHAPE, before finalize).
2. **:1586-1600** — POSITION servo on drivers [6,10,20,24]: joint_target_mode=POSITION, target_ke=GRIPPER_SERVO_TARGET_KE, target_kd, effort_limit=GRIPPER_DRIVER_EFFORT_LIMIT_NM, target_pos=OPEN (start; runner schedules CLOSE) + 4-bar CONNECT eqs (by label, both arms).
3. **:1738-1760** — **table SOLID box → VOID 4-box** (2 Y-slot boxes [0.090,0.210] + 2 X-fill): f1ext reaches UNDER the cable to cage it (solid table blocks f1ext → no hook). **GEOMETRY CHANGE.**
4. **:1905-1918** — in-builder eq-count assert (6/world = 4 CONNECT + 2 follower-mirror) + `_wire_s6_grasp_solref(solver)` (negative PAD_SOLREF into mjw all-worlds + stiffen 4-bar).

**Geometry parity (§運用14/GROVE 2.2):** mutation-3 (void) is the only geometry change. **SRG void-parity gate (no-GPU) already confirmed** build_multiworld void formula (base:1746) == build_scene void == FIXED [0.090,0.210], CPU corner readback NO artifact (node state.md:30). ⇒ when comp3 flips ON, the void appears EXACTLY as SRG validated. flag-OFF = solid box (byte-preserve). **Re-confirm** at Stage-B /geometric-design on the flag-ON build_multiworld (first time actualized in the RL env; state.md 05:43 ran table-void×C1-clip parity PASS on the design — comp3 re-runs on the built model).

## §7. /force-design gate (grip servo) = %12 requirement 4 (Stage-B design-gate, directゲート)
comp3 servo (4-substep POSITION close) = force/stiffness/contact → **/force-design MANDATORY** at Stage-B design-gate (before build), per §運用2 [DESIGN-GATE] + build plan §11. Scope of the /force-design analysis:
- servo gains GRIPPER_SERVO_TARGET_KE / _KD / GRIPPER_DRIVER_EFFORT_LIMIT_NM (task_config SSOT — **inherited from the proven build_scene/AR path, NOT new-designed** → expect LIGHT; confirm hierarchy consistency + dt-dependence).
- condim=6 + PAD_SOLREF (negative, `_wire_s6_grasp_solref`) contact stiffness — inherited; verify no drift vs SRG's D1-gate SSOT (16-pad by-NAME / pad_solref / condim6 / impratio10 — SRG D1 confirmed == live task_config).
- 4-substep close dynamics = the SRG-measured regime (creep-budgeted). /force-design confirms the servo close is force-consistent with SRG's S0/S1 measurements (no re-design; the SRG probe IS the force measurement).
⇒ expect **/force-design = LIGHT PASS** (inherited params), but it is a REQUIRED gate (not skippable), run at Stage-B design-gate. Also /geometric-design (§6 void re-confirm).

## §8. Validation plan — no-GPU structural (NOW) + GPU-deferred (separate Rs surface)
### (A) no-GPU structural legs — what comp3 PLANNING validates without GPU (build+verify-before-GPU discipline):
- **L1 flag-OFF byte-preserve** (CC4-C1 invariant): static code-diff — flag-OFF branch == current env-core (28-wide write, no grasp_actuation kwarg) byte-identical. + B⑨a′ = full-arm_q sha INCL gripper coords (re-regression legacy-config == env-core 25/81). **This is the gate-iii analogue for comp3/comp4.**
- **L2 geometry parity** (no-GPU CPU readback, reuse SRG's s2_void_check pattern on build_multiworld directly): flag-ON void == [0.090,0.210], no claw↔table artifact, f1ext reaches under cable. Confirms §6 on the RL-env built model.
- **L3 servo-seed assert** (CPU build, flag-ON): `route_executor.servo_seed_assert` — drivers seeded to OPEN (fail-loud), 6 eqs/world registered (base:1905 assert), condim/PAD_SOLREF == SRG D1 SSOT.
- **L4 write-site wiring unit** (no-GPU): flag-ON path calls apply_arm_only_write_* → gripper coords {6-13,20-27} UNCHANGED after arm write (reuse the BUILT no-repin unit `d2e3a4e73c` pattern); set_gripper_target is the SOLE joint_target_pos writer.
### (B) GPU-deferred legs — the actual FORK-1 CLOSE-kinematics (separate Rs surface, per %12; NOT this task):
- **G1 live close+cage+hold** (cuda:0-cg, build_multiworld grasp_actuation ON + comp4 wiring + route_executor grip_cmd): the gripper closes on the cable, cages it, holds under the creep-budgeted criterion (per-axis lateral/z-drop, SRG S1/S2 method) at nominal + tail cells, multi-world. **This is the real FORK-1 proof** (SRG's build_scene result transferred to build_multiworld).
- **G2 ⑦(b)** 1-step-after-reset divergence (grasp_actuation ON) + cable-fork re-seed (§8-B build plan, k≥1).
- video leg (§運用14): claw-zoom + intra-finger slip time-series + human-GT (grip verdict = NEVER numeric-only).

## §9. Conservatism direction (GROVE 2.2, per-leg)
- flag-OFF byte-preserve (L1) = **conservative-definite** (static byte-identity, exact).
- geometry parity (L2) = **conservative** (SRG void-gate already conservative-favourable; re-confirm).
- G1 live close = **SRG prior is conservative-favourable** (firmer solver holds tighter, cg pessimistic-passed); build_multiworld delta (env-drive + multi-world) direction = **UNKNOWN until measured** — do NOT presume; G1 measures it. Non-conservative surprises (env-drive EASIER than scripted) → flag for high-fidelity check before over-claim.

## §10. Design constraints (plan-binding) + risks
**Constraints:** (1) flag-OFF byte-identity absolute (comp3+comp4+comp5 all flag-gated; B⑨a′ full-arm_q sha incl gripper). (2) comp3⊕comp4 INSEPARABLE (build+validate together; flag-ON grip needs gripper-exclusion). (3) REUSE route_executor BUILT machinery (no reimpl). (4) no-kinematic-trick preserved (servo = physical PD close, NOT kinematic pin). (5) /force-design + /geometric-design at Stage-B design-gate (§7). (6) GPU spend = separate Rs surface after this plan + [VERIFY]. (7) PLANNING only now.
**Risks:** substrate-transfer material (SRG build_scene → build_multiworld; G1 measures) / multi-world index correctness (cable FREE-root world-offset — apply_arm_only_write_perworld already no-repin-unit-PASS for world≥1) / servo close in the env drive-loop (never run live; G1) / geometry re-confirm on built RL-env model (L2).
**Carry (SRG 3 flags, still open):** FORK-1 = THIS comp3 (G1). C2-whiff x-20_y5 = comp5/C2. dy=±20 table-edge retention = downstream-seat = route-exec/comp.

## §11. Deliverable + next
- **This doc = comp3 PLANNING** (structural, no-GPU, no code). → %12 [VERIFY].
- **On %12 [VERIFY] PASS** → Stage-B design-gate (/force-design + /geometric-design) → 5体 [VERIFY] (comp3⊕comp4 build plan) → RULE-CHECK → build no-GPU structural (L1-L4) → **/production-launch-gate + Rs GPU surface** → G1 FORK-1 close-kinematics (cuda:0-cg).
- ⛔ comp5-8 STAY HELD (comp5=C2 scene, comp6=§9 tripwire, comp7/8=live DoD) behind comp3 G1.

---
*%11 COORD (w2:p3) 2026-07-10. comp3 PLANNING (no-GPU, structural). Extends build plan v0.2.2 §2 comp3/comp4. %9 grasp_actuation gap = STAGED-GAP (§3). CC4-C1 = inseparable design constraint (§5). /force-design = Stage-B gate (§7). → %12 [VERIFY]. GPU = separate Rs surface.*
