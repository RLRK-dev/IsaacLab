# SRG S0 — BUILD SPEC (option B: self-contained current-substrate CPU pinch) — %11 COORD

**status:** build guide for the NEXT session (recipe reconciled + load-bearing claims verified 2026-07-07 20:53 JST). %12 RULED (B) at 20:08.
**scope:** revise S0 in `srg_probe.py` from the STALE s5-reuse to a self-contained current-koshape CPU pinch. S1/S2 GPU HELD. no-GPU. no production/locked edit (D2).

## Why the s5-reuse broke (verified root cause)
- The current gripper is the **koshape (コ) single-claw asset** `2f85_koshape.xml` (`test_newton_clip_routing.py:161` ROBOTIQ_STRIPPED_XML; asset exists Jun-22). Swapped V-groove→ko-shape in commit **`85315bbec6`** (R-S7.1, 2026-06-23) + `843084ae5e` (task_config koshape). This POST-dates the s5 bench (2026-06-10) → s5 = OLD V-groove gripper.
- koshape puts **8 pad collision box-geoms per gripper** (4/pad-body: `pad1/pad2/pad_f1ext/pad_f2ext` × 2 pad bodies; the f1ext/f2ext claws "wrap the Ø8 cable", `2f85_koshape.xml:7-12,108-158`) → **16 for 2 arms**. s5 asserts `pads_kept==8` (V-groove: 2/pad = 8 total) → STALE FAIL. This is a gripper-MODEL change, not a mesh refinement.
- ⇒ reuse non-representative even if force-patched (s5 downstream pad-filter + com_y assume the 8-pad V-groove). Connects to コ-substrate lore ([[reference-ko-formclosure-twoclaw-cage-gate]], GD-KoShape-Finger, cage≠hold).

## KEEP from the verified S0 design (unchanged — %12 [VERIFY] PASS)
- D1 SSOT fail-closed gate (readback == live task_config R6/condim6/impratio10) + §3 frame-comparability HARD assert (SIM_SUBSTEPS×SIM_DT == RL_SIM_SUBSTEPS×RL_SIM_DT == DT) + K regime-screen 3.5× (= substep-ratio 2.5× + margin).
- force `test_newton_clip_routing.DEVICE = "cpu"` (Finding-1 fix; FK model defaults to module DEVICE=cuda:0 at :1729-30). Run under `CUDA_VISIBLE_DEVICES=""` to prove no-GPU.
- s5 MEASUREMENT ALGORITHM (reused, asset-agnostic): `com` polyfit slope creep µm/f; landing_control rule-2 free-body true-positive (fail-closed); per-substep body_f readback assert; `geom_inverse_map` shape→geom.

## Build recipe (current base primitives — all CPU-viable, cited; agent-mapped + crux-verified)
Build fresh on the CURRENT base, NOT the s5 chain. Reuse the s5 measurement math.
1. **Scene build:** `build_multiworld_scene(...)` (`newton_skill_env_base.py:1484`, 1 world) OR lower-level `add_ur5e_robotiq(builder, base_xform, robotiq_xml=ROBOTIQ_STRIPPED_XML)` (`test_newton_clip_routing.py:184`) + `add_revolute_cable(builder, start_pos, direction=(0,1,0))` (`:936`). `finalize(device="cpu")`. ⚠ `add_revolute_cable` reads module-global `CABLE_SEGMENTS=40` (`task_config.py:135`) → monkeypatch shorter for a minimal pinch. cable_start_pos pattern `newton_skill_env_base.py:1519-1525` (GRASP_X, CLIP1_Y-half, TABLE_HEIGHT+CLIP_BASE_HEIGHT+CABLE_RADIUS).
2. **Solver:** `make_solver(model, backend="mujoco", use_mujoco_cpu=True, enable_cable_contacts=True)` (`newton_skill_env_base.py:1302`). CPU-viable, no GPU hardcode; on CPU `mjw` absent, `_wire_s6_grasp_solref` guards `if mjw is not None`.
3. **Contacts:** condim=6 baked build-time (`:1646-52`); pad rolling 0.005 (`:1653-55`); **R6 pad solref via `_wire_s6_grasp_solref(solver)`** (`:1344`, pokes `m.geom_solref[g]=MUJOCO_PAD_SOLREF` `:1389-91`); impratio=10/cone=elliptic XML-baked (`2f85_koshape.xml:16`). ⚠ **GAP (poke it yourself):** `MUJOCO_CABLE_TABLE_FRICTION=(1.0,0.005,0.005)` (`task_config.py:180`) is NOT wired in base — poke `m.geom_friction` on cable+table geoms for a faithful R6 creep (s5 did this in the stale rev7 payload).
4. **Servo close:** drivers `[6,10]` per arm (`GRIPPER_DRIVER_JOINT_IDX`, `task_config.py:34`). `_set_gripper_target(control, driver_joints, GRIPPER_DRIVER_CLOSE_RAD=0.7407)` (`route_executor.py:967`). Servo ke=66.7/kd=2.0/effort=2.5 baked (`newton_skill_env_base.py:1592-97`, `task_config.py:314-316`). Ramp the close (s5 did 240f ramp 0→0.7407).
5. **Physics step:** `physics_step(model, state_0, state_1, control, solver, contacts, ...)` (`newton_skill_env_base.py:1978-91`) loops SIM_SUBSTEPS×{clear_forces→collide→solver.step→swap}; for the pinch overwrite the arm coords from FK each substep (kinematic arm, physics gripper+cable) — the `step_with_force` pattern (`s5_calib_bench3r.py:158-180`). Use RL_SIM_SUBSTEPS(4)+RL_SIM_DT for the 4-substep floor.
6. **Pad geom ID for contact-force filter:** by-NAME (`"pad" in gname+bname`, `_wire_s6_grasp_solref:1377-85`) — NOT a `==8` count (stale). `geom_inverse_map(solver)` (asset-agnostic, `s5_p1_probe.py:106`). Force loop over `d.ncon` + `mujoco.mj_contactForce` (`s5_calib_bench3r.py:193-203`). NB pad_shapes now hold 4/side not 2.

## Validate (per %12 META-LESSON: real BUILD+RUN, not import)
CPU run under `CUDA_VISIBLE_DEVICES=""`: (a) env BUILDS (koshape 16-pad, no `==8` fail), (b) D1 gate PASS (contact readback==live SSOT), (c) frame-comparability assert holds, (d) creep µm/f produced + K-screen verdict. Report floor µm/f vs 60.4 10-substep bank (⚠ bank was V-groove — the 4-substep koshape floor is a NEW measurement; note bank is old-gripper reference only), collapse/badqacc/NaN, D1 PASS/FAIL. If D1 FAIL or floor>K → STOP+surface.

## Risks / open
- CPU-viability of the full koshape pinch build+step = validate-by-run (agent says viable; AR benches ran build_multiworld_scene CPU, but VALIDATE).
- The 60.4 bank is V-groove 10-substep; the koshape 4-substep floor may differ by gripper too (not just substep) → the K-screen vs 60.4 is a rough regime check, not an exact transfer. Surface this (per-axis conservatism / honest bank caveat).
- short-cable monkeypatch must not change contact representativeness (keep CABLE_SEG_LEN/RADIUS/contact params production).

*%11 COORD 2026-07-07 20:53 JST. Recipe agent-mapped (Explore) + load-bearing claims verified (koshape root cause, build entry, R6 applier). Build in next session.*
