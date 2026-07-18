# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 — factual read-only inventory **v3** (fixes R1–R4)

- supersedes v2 `…_v2.md` (sha `45aad61a…`) / v1 (`59d0e11c…`). node `T-WMSO`; verify `w2:pN`; custody `w2:p6`.
- prepared_at: 2026-07-18 14:54 JST · repo HEAD `1f1b500b19` · **read-only, no run, no gate PASS**.
- pN v2 verdict addressed: provenance leg PASS + B2–B5 corrections VERIFIED; new HOLD R1 CRITICAL / R2 HIGH / R3 HIGH / R4 MED.
- provenance: base v3 manifest (`6abb176e…`/`5d8d2216…`) + ext-v2 (`672bf624…`/`3f91fc85…`, registered taxonomy, freeze-before-reextraction).
  **combined post-bracket unchanged = 54 checked / 0 changed = `changed_during_inventory=[]`.** R1 fix used **path discovery only**
  (no checkpoint/dataset/sidecar content read), so no new source enters the closure.
- pN-VERIFIED-in-v2 and carried unchanged: 3-surface A/B/C separation, SkillName 5RL+3scripted+1wait, obs schemas, unwired SOMA
  envelope, timeouts finding.

---

## 0. THREE surfaces (Surface B reworded per R4 — it is a code path, not a verified live/active selection)

| surface | file | role | obs / action | policy |
|---|---|---|---|---|
| **A** per-skill orchestrator | `orchestrator/routing_orchestrator.py` + 43 `StepDef` | chains per-skill RL+scripted+wait; snapshot/rollback recovery | per-skill env schemas; `SkillResult` | dispatches per-skill policies |
| **B** whole-route RL env **code path** | `envs/newton_route_env.py` (`NewtonRouteEnv(VecEnv)`) | RL MDP over C1→C2, G1–G6 latched; **module header = "STAGED COMPONENT 1 of 5 … ROUTE-VIA-STUB, CPU-SMOKE-ONLY intended. NO training / NO GPU here"** (`:8,:49-51`) | 62D privileged / 6D alpha-residual | **no internal policy load**; trainer authority = **RLPD residual-on-script** (planned; `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md:7,14,21`) |
| **C** route runner/mirror | `scripts/policy_route_runner.py` | route rollout (B0 default / B1 optional `--policy`) | 25/27D (12+n_phases) / 6D | BC actor-mean; default B0 open-loop demo replay |

`route_executor.py` = surface-B scripted phase-clock engine; `newton_skill_env_base.py` = shared utility (scene/IK/quat), no
termination logic. **No surface is asserted "live/active"** — current active selection is UNVERIFIED (§7).

---

## 1. Learned skills + policy lineage (item 1) — verified in v2, unchanged

Skill vocabularies (unreconciled): **`SkillName`** 9-type mixed (`step_table.py:35-51` + `routing_orchestrator.py:71-81`):
5 RL (APPROACH_CABLE/CLAMP/INSERT_INTO_CLIP/UNCLAMP/AERIAL_REGRASP) / 3 scripted (TRANSPORT/RECLAMP_L/HALF_UNCLAMP_RELEASE) /
1 wait (CLIP_CONFIRM); **`SkillType`** 7 RL (`skill_adapter.py:45-58`); **scripted fns** (`scripted_skills.py`); **`bimanual_*`** 6 WM
(`skill_adapter_with_prediction.py:150-157`). Families: per-skill RL = DAPG (LoRA on BC base, `train_common.py`/`train_grip.py`;
AC/AR/IC wrappers ABSENT); base = BC-only (`train_base_model.py`); surface-C route policy = BC actor-mean (`bc_train_route.py`);
surface-B whole-route = RL residual (RLPD planned, BC-independent); `bimanual_*` = WM+PPO. Version hash: YES in
`bc_train_route.py:117-135` + `policy_route_runner.py:35-46,456,622`; NO in `eval_skill.py`/`train_common.py`/`train_base_model.py`.

## 2. Obs/action + vision (item 2) — verified in v2, unchanged

Surface B: 62D privileged obs (`_compute_obs_batch:1475-1587`; `route_env_config.py:45`) / 6D alpha-residual (`:427,401,1137-1195`);
all 62 dims privileged/const, ZERO vision. Surface C: 25/27D obs (`route_demo_to_bc.py:301`, runner `:200-212`). Vision modules
(`vision_pipeline.py`, `visual_encoder.py`, `vision_obs_assembler.py` `NotImplementedError` stub, `obs_builder.py` broken import)
UNWIRED to B/C.

## 3. Termination / timeout + safe-interruption (item 3) — verified in v2, unchanged

`SkillResult` 5-class (`result.py:18-25`); orch mapping `:419-469` (CABLE_DROP→FAIL). Surface-B done `newton_route_env.py:1720`
(G6 success `:1704-1711`; explosion `:1635-1640`; drop `:1653-1672`). Timeouts-invariant honored in route/AC/AR envs (`:1725/1003/1334`);
grip divergence `:1258/1441` (§10). **Insert RL env** = ABSENT_IN_DECLARED_CLOSURE (`find thread_isaac_lab -name 'newton_insert*env*.py'`→0).
**Safe-interruption checkpoint** = ABSENT_IN_DECLARED_CLOSURE (`grep -rniE "interrupt|preempt|safe.interrupt|safe.stop|switch.mid|mid.skill" thread_isaac_lab/{envs,orchestrator,skills,configs}`→0 core hits).

## 4. Handoff / transition / recovery (item 4) — R3 fixed

Surface A sequencer + recovery engine `execute_step` (retry≤3/rollback≤3, `routing_orchestrator.py:1063-1214`); OOD gate
`bc_p0_region_check` default-accept stub (`:1152-1162`); handoff-state = physics `StateSnapshot` (`snapshot.py:19-31`), not a
charter-§3 skill-handoff-state contract. Surface B: `RouteInterfaceV1` + `reset_to_phase(k=0 stub)`.
**Dedicated recovery/fallback SKILL = ABSENT_IN_DECLARED_CLOSURE** (exact query `grep -nE 'RECOVERY|FALLBACK' thread_isaac_lab/skills/step_table.py`
→ 0 hits; SkillName enum = the 9 listed).

## 5. Surface behaviors + safety mechanisms (item 5 — R4 wording; per-surface guards enumerated)

- **Surface A** = heuristic skill-chaining + retry/rollback recovery = the baseline gate⑨ compares WMSO against; single-world only
  (`routing_orchestrator.py:799-809`).
- **Surface B env code path** in-env guards: (1) **static Z-clip** on IK target (`clip(z, lane-floor, EE_Z_SAFETY_UPPER)`,
  `newton_route_env.py:1189-1193`); (2) **task-level fault detect+terminate** — explosion (`near>1.0`|NaN, `:1635-1640`) & drop
  (`:1653-1672`) → `done`+`TERM_PENALTY=-10` (`:1714-1720`).
- **Surface C runner** in-runner guards: action clip `np.clip(raw,-1,1)` (`policy_route_runner.py:229,808`) + **GUARD2** per-arm 3D
  15 mm rate-limit (`GUARD2_M=0.015`, `:55,830`).
- **SOMA `SafetyEnvelope`/`FallbackGuard`** (L1-3 measure-only, L4 residual-zero; `safety_envelope.py:8-11,116-126`) **UNWIRED to B/C**
  (`grep FallbackGuard|SafetyEnvelope|safety_guard` in `newton_route_env.py`/`route_executor.py`/`policy_route_runner.py`→0).
- ⇒ gate⑧: **none of the above is an independent low-level real-time safety monitor** (charter §2.4); they are target/action clips,
  reward/termination faults, and an unwired legacy envelope.

## 6. Timing / deadline (item 6 — R2: query split, verbatim)

Timing = sim-step counts: `DT=1/480 s`; `PHYSICS_STEPS_PER_RL=10` (`newton_route_env.py:404`) ⇒ ~20.83 ms/RL-step (~48 Hz);
IK 100/30, VBD 20 (`newton_skill_env_base.py:97-99`); horizon `ROUTE_TERMINAL_STEPS=900` (`route_env_config.py:99`); per-skill 100–300
(`task_config.py:378-383`).
**Real-time/deadline constant = ABSENT_IN_DECLARED_CLOSURE**, corrected split queries (verbatim):
- `grep -rncE '\bHz\b' thread_isaac_lab/{envs,orchestrator,skills,configs}/` → **only `envs/hook_hanging_env.py:2`** (derived-Hz prints
  in the unrelated `ManagerBasedEnv`).
- `grep -rniE 'latency|deadline|real.?time|wall.?clock|hertz' thread_isaac_lab/{envs,orchestrator,skills,configs}/` → **0**.
- (v2 correction: v2's case-insensitive `Hz` erroneously also matched lowercase `hz` = geometry half-height, e.g.
  `task_config.py:91 hz=2.5mm`; those are NOT real-time constants.) Conclusion unchanged: no wall-clock deadline exists;
  charter §4's `D_situation`/`T_*` must be DESIGNED.

## 7. Fail-closed register (R1 checkpoint trichotomy + R3 taxonomy; exact queries)

**R1 — checkpoint fact corrected (v1/v2 "not materialized" was FALSE and non-closed):** the query must include `eval_runs/` and
sidecar patterns. Trichotomy:
- **materialized candidates EXIST** — surface-C route policies/datasets under
  `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/` (roots `b0_dataset/`, `b1_train/`, `b1p_train/`, `b1p_train_e2000/`,
  `b2_cpD/`, `b2_cpE_iv/`, `dq7_*/`). Counts: **46 `bc_dataset*.npz`, 1 `policy.pt`, 22 `policy_abs*.pt`, 22 `*_sidecar.json`**.
  Query: `find eval_runs data thread_isaac_lab/data -type f \( -name 'bc_dataset*.npz' -o -name 'policy.pt' -o -name 'policy_abs*.pt' -o -name '*_sidecar.json' \)`.
- **default-selected = none** — `policy_route_runner.py` `--policy default=None` (`:1491`), B0 demo-replay is the no-`--policy` path.
- **current-active = UNVERIFIED** — no launcher/config cited that selects one of the candidates as the active policy.
- disposition: **path discovery only; no content/sidecar read**; if any candidate is later read, it is frozen (v3_ext-style) first.

| finding | class | exact query |
|---|---|---|
| Default active checkpoint selection (surface C) | ABSENT_IN_DECLARED_CLOSURE | `policy_route_runner.py --policy default=None` (:1491) |
| Current active checkpoint selection | UNVERIFIED | no launcher/config selects a candidate |
| Insert RL env file | ABSENT_IN_DECLARED_CLOSURE | `find thread_isaac_lab -name 'newton_insert*env*.py'`→0 |
| Safe-interruption checkpoint (core) | ABSENT_IN_DECLARED_CLOSURE | §3 grep→0 |
| Real-time/deadline constant | ABSENT_IN_DECLARED_CLOSURE | §6 split greps |
| Dedicated recovery/fallback SKILL | ABSENT_IN_DECLARED_CLOSURE | §4 grep→0 |
| Skill-level anti-thrash (hysteresis/dwell/switch-penalty) | ABSENT_IN_DECLARED_CLOSURE | `grep -rniE 'hysteresis\|dwell\|switch.?penalt\|thrash\|min.?switch\|cooldown' thread_isaac_lab/{orchestrator,skills}/ newton_route_env.py` → only unrelated `_c1_pin_dwell` pin-latch |
| Vision belief → B/C obs | UNVERIFIED (effectively unwired) | 62D & 25/27D carry no vision term; assembler `NotImplementedError` |
| `ObsBuilder24D` config import | broken (legacy) | `OBS_DIM/OBS_MODES/OBS_NORMALIZATION` undefined in `task_config.py` |
| T3 WM trainer / AC-AR-IC `train_*.py` | ABSENT_IN_DECLARED_CLOSURE | `find … train_dual_arm_msa.py / train_{approach,insert,aerial,clamp}*.py`→0 |

## 8. Charter §5 six-schema mapping (R3: transition softened)

state/belief = 62D/25-27D privileged, vision unwired · skill action/lifecycle = multiple unreconciled vocabularies · **transition
distribution = not established / UNVERIFIED** (no skill-resolution dynamics model feeds B/C; `WorldModelEncoder` predicts latent for
the separate `bimanual_*` stack) · handoff/recovery = snapshot rollback + phase-bank refork, no recovery skill · safety/event/abstention
= clips + task-fault termination, envelope unwired, abstention stub · per-event deadline = none.

## 9. Charter §6 10-gate factual state (D0 registers contracts; NO gate PASS)

| # | gate | state | class |
|---|---|---|---|
| 1 | algorithm independence | multiple unreconciled vocabularies | PARTIAL |
| 2 | vision grounding | obs 100% privileged; vision unwired | ABSENT_IN_DECLARED_CLOSURE |
| 3 | model calibration | no skill-resolution dynamics model | UNVERIFIED / not-established |
| 4 | unknown-state abstention | `bc_p0_region_check` default-accept stub | PARTIAL (stub) |
| 5 | safe interruption | grep→0 | ABSENT_IN_DECLARED_CLOSURE |
| 6 | anti-thrashing | grep→only pin-latch dwell | ABSENT_IN_DECLARED_CLOSURE |
| 7 | real-time | split greps; no wall-clock deadline | ABSENT_IN_DECLARED_CLOSURE |
| 8 | safety independence | clips + task-fault termination; envelope unwired; no independent low-level monitor | PARTIAL |
| 9 | comparative value | baseline present (orchestrator heuristic recovery + fixed chain) | PARTIAL (baseline exists) |
| 10 | no premature claim | **contract registered / evidence pending** | — |

## 10. Flagged latent finding (surfaced, NOT fixed — p4/§DDR#18) — unchanged

`newton_grip_env.py:1258/1441` `timeouts=int(timeout)` unguarded vs the AC/AR/route guard (prohibited.md timeouts汚染). Impact
UNVERIFIED (orchestrator verdict unaffected; reaches trainer only if grip trained standalone). p4 domain; surfaced only.

## Disposition

D0 factual inventory **v3** — R1 checkpoint trichotomy (materialized candidates exist / no default / current UNVERIFIED, path-only),
R2 real-time split queries verbatim, R3 absolute negatives backed-or-softened + taxonomy fixed, R4 "code path" wording + per-surface
guards. No content read beyond the frozen closure; post-bracket `[]`. Request pN re-verify; on D0 factual PASS the charter §5
architecture draft proceeds to its own D0-exit design verify. production/training/sim/inference/closed-loop/p4-grip UNAUTHORIZED.
