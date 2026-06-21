---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: Mechanical Specifications
created: '2026-03-28'
tags:
  - design
  - hardware
  - reference
---

# Mechanical Specifications

THREAD dual-arm cable manipulation システムの全メカ仕様。
数値パラメータのSSOTは `task_config.py`。本ファイルは閲覧用まとめ。

---

## Current R2-A Track A Note (2026-05-27)

S1A progressed through a bounded env-only/default-off source mutation and is now
confirmed default-off safe at both static and runtime construction boundaries,
with the S1A-enabled E0 construction/schema path also passing one bounded
cuda:0 reset/step. A later numeric-log-adapter entrypoint smoke completed one
bounded 1-iteration cuda:0 attempt and resolved the previous RSL-RL string-log
abort as a plumbing issue. The current planning surface is a 0GPU summary schema
patch package plus `%3` Tier-A review COMPLETE for the adapter, followed by a
0GPU CC6 efficacy gate package, a 0GPU exact-command review package, and a 0GPU
launch-parameter/safety-threshold design package, and a 0GPU budget/safety-schema
closure package, a 0GPU schema-v2 summary patch package, and a 0GPU
budget-parameter design package, followed by a 0GPU schema-v2 calibration-scout
necessity review, a 0GPU schema-v2 field-emission source/static audit, a
0GPU field-emission runner-copy patch package, a 0GPU field-emission semantic
gapfix package, semantic exact-command review, terminal budget/safety gapfix,
runner-horizon cap contradiction review, runner-gate redesign scope package,
runner-gate redesign patch package, runner-gate patch supervisor review, and
patched-runner exact-command review, a 0GPU threshold-provenance audit,
release-horizon scout design, `%3` Tier-A review, and one exact authorized
cuda:0 release-horizon scout diagnostic attempt, followed by an artifact-only
0GPU schema-gap review and a 0GPU release-horizon schema patch package. This is
not product evidence.
`newton_aerial_regrasp_env.py` changed from SHA
`87875a488a96338f4b8836e82b750252f4054e83e5e6a80d56715ae21002e0db` to
`c45771d1eaa5370b41192241ddd5f802a9f3136f7ab4540b36d02e6fb0e5f4f2`; `%3`
accepted the true diff, static import passed, one bounded cuda:0
construction/reset/one-step check passed with `num_obs=45`, obs shape `[41,45]`,
finite obs/reward, all S1A flags false, no S1A log keys, kinematic support
false, and protected SHAs unchanged. A separate S1A-enabled E0 check then passed
with `num_obs=52`, obs shape `[41,52]`, finite obs/reward, S1A metadata present,
S1A reward step0 zero, kinematic support false, product scoring/credit false,
and protected SHAs unchanged. Current state:
`R2A_TRACK_A_S1B_COLLECTION_EXACT_COMMAND_GATE_AFTER_PROVENANCE_MUTATION_0GPU_COMPLETE /
S1B_COLLECTION_EXACT_COMMAND_AFTER_PROVENANCE_MUTATION_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED /
PRODUCT_GO_FALSE`.
The S1B collection command moved through `%3` Tier-A COMPLETE and exactly one
Rs/TL-authorized cuda:0 smoke. The run produced a labeled NPZ with S1B
schema/provenance fields, but actual release events were `0/41` and
retained-after-release labels were `0/41`. The follow-on 0GPU artifact review
confirmed the artifact is mechanically valid schema smoke / negative-only
diagnostic evidence. The latest 0GPU root-cause redesign then classified the
outcome as pre-release termination before scheduled release, not
release-without-retention: transition step max `47` before command release step
`80`, terminal reasons `cable_drop=22`, `explosion=11`, `clamp_loss=3`,
`unspecified=5`, and persisted `configured_release_step=-1` due to a collector
label-provenance gap in no-release rows. `%4` then packaged a collector-only
exact source diff under
`eval_runs/r2a_track_a_s1b_collector_provenance_terminal_step_patch_package_0gpu_20260527/`.
`%3` accepted the exact diff at `2026-05-28T00:04:30+09:00`, and `%4` applied
that collector-only diff under
`eval_runs/r2a_track_a_s1b_collector_provenance_terminal_step_source_mutation_20260528/`.
Collector SHA changed from `20eda9cb...` to `8516a23c...`. The mutation persists
configured release step, adds terminal/first-done-step provenance, adds direct
provenance aliases, and preserves fail-closed no-product-positive semantics.
`%4` then completed the 0GPU post-provenance exact-command gate package under
`eval_runs/r2a_track_a_s1b_collection_exact_command_gate_after_provenance_mutation_0gpu_20260528/`.
The guarded future command exits `64`, binds collector SHA `8516a23c...`, keeps
cuda:0 only, preserves the prior 41-world envelope, and records the future
output root as absent. Current next route is
`SUPERVISOR_TIERA_REVIEW_FOR_S1B_COLLECTION_EXACT_COMMAND_AFTER_PROVENANCE_MUTATION_OR_HOLD`.
Product success remains `0`; `cc6_null_hypothesis_falsified=false`; S1A
efficacy, training, and product routing require separate approval and remain
unauthorized. The optional schema-v1 re-smoke is held by default because it would
only add provenance, not efficacy evidence. The CC6 gate package binds baseline
retained-after-release `40/77 = 0.5194805195`; the later threshold-provenance
audit found the `+0.15` margin was local-draft rather than earlier Rs/R1-derived.
Rs/TL explicitly selected `+0.15` as a diagnostic null-hypothesis margin only,
so derived threshold `0.6694805195` is an
`RS_TL_SELECTED_DIAGNOSTIC_THRESHOLD`, not a product predicate. cable_drop/explosion
thresholds remain `REVIEW_REQUIRED`. The exact-command review is not launch-ready
because timeout, training iterations, steps, seed/replicate policy, output root,
and cable_drop/explosion safety thresholds remain unresolved. The
launch-parameter/safety-threshold design resolved only output-root convention and
future summary assertions; normalized cable_drop/explosion fields are a
data-schema gap. The budget/safety-schema closure package defined schema-v2
requirements and a preferred eval-runs-local future patch surface, but launch
readiness remains false because timeout, GPU-hours, iterations, steps, seed
policy, and cable_drop/explosion thresholds are still not evidence-backed. The
schema-v2 summary patch package then created only an eval-runs-local patched
copy with normalized cable_drop/explosion fields and fail-closed direct-run
behavior; it closes the data-shape gap but leaves timeout, GPU-hours,
iterations, steps, and seed/replicate policy unresolved. The budget-parameter
design then confirmed that those fields are not evidence-backed for efficacy;
the only apparently defensible future envelope was a separate
budget-calibration scout (`timeout=3600`, `max_iterations=1`,
`num_steps_per_env=8`, `world_count=41`, `seed=42`, `cuda:0`) for
runtime/provenance plumbing only. The subsequent necessity review rejected that
same-envelope scout as non-informative: `num_steps_per_env=8` cannot reach
`d0_control_release_step=80`, and the current env/adapter path does not emit
`cc6_safety_schema_v2_records`. The subsequent field-emission source/static
audit found protected env mutation unnecessary: the env already emits raw
per-world fields, while the eval-runs-local runner/adapter copy must collect
`extras["log_per_world"]` into `cc6_safety_schema_v2_records`. The next clean
route was HOLD or a bounded 0GPU runner/adapter copy patch package. That package
then created only an eval-runs-local patched copy, SHA
`2dd3af5472be2ab3bcf8a18b7b91487abb8d063c152911636957801675e3a024`, with
`extras["log_per_world"]` to `cc6_safety_schema_v2_records` conversion and
static/synthetic PASS. Supervisor review was interrupted without a final
COMPLETE/INCOMPLETE marker, but its visible partial review exposed a valid
semantic gap around observed release-step and post-release-retention derivation.
The subsequent semantic gapfix package created a new eval-runs-local copy, SHA
`2713ec78190e065f67e79ec8d926a201b81816adcb55f5da661907017ec43759`, which keeps
configured and observed release steps separate, derives observed release from
raw `s1a_post_release_phase`, and counts 30-step retention strictly after
release while failing on post-release cable drop or explosion. Current next
route is supervisor Tier-A review of the semantic-gapfixed copy or HOLD; no GPU,
runner execution, training, protected source mutation, product scoring, or
strategic routing is authorized. A concise `%3` review attempt after the
semantic gapfix timed out without a COMPLETE/INCOMPLETE marker and was
interrupted to conserve supervisor tokens. Later, `%3` returned
`SEM_GAP_REVIEW_0527 COMPLETE`, concluding the semantic-gapfixed package is
sufficient as the basis for a later exact-command Tier-A review. This is not an
execution GO; the next clean route is bounded 0GPU exact-command review package
work over the semantic-gapfixed copy, or HOLD. `%4` then completed that bounded
0GPU semantic exact-command review package. Launch-readiness remains
`NOT_LAUNCH_READY_REVIEW_REQUIRED`: semantic field emission and retention
semantics are bound, but timeout, estimated GPU-hours, max iterations, steps per
env, seed/replicate policy, exact future output root, and cable_drop/explosion
non-inferiority thresholds remain `REVIEW_REQUIRED`. Current next route is a
0GPU CC6 efficacy budget and safety-threshold gapfix or HOLD. `%4` then
completed that terminal gapfix and found the current artifact set exhausted:
only fresh output-root policy is evidence-backed, `num_steps_per_env` has a
static lower bound of at least 111 emitted step payloads, and timeout/GPU-hours/
iterations/seed policy/cable_drop threshold/explosion threshold remain without
existing evidence. `%4` then confirmed the runner-horizon cap contradiction:
the semantic CC6 retention contract requires at least 111 emitted step payloads,
while the current base future entrypoint rejects `num_steps_per_env > 32`; the
semantic-gapfixed copy delegates through that base entrypoint, so parameter
selection alone cannot make this runner path launch-ready. The runner-gate
redesign scope review found protected env/source mutation unnecessary; the
minimal future surface was an eval-runs-local runner-copy patch package that
replaces the hardcoded 32-step gate with a semantic-horizon-aware gate while
preserving authorization and no-crutch/product-refusal checks. The runner-gate
patch package then created only a fresh eval-runs-local runner copy,
SHA `1fdb75a7d6cd680cbc06e6f80ba53d4ac3e9a3eab44299326654efbc49450c9f`,
with a semantic-horizon gate default lower bound `80 + 30 + 1 = 111` emitted
step payloads. Static/synthetic validation passed: `110` fails and `111` passes
the helper, direct future-run without exact GO exits `64`, product credit is
refused, and missing required safety fields fail closed. No exact command,
execution, training, protected mutation, or product claim was created. `%3`
then returned `RUNNER_GATE_PATCH_REVIEW_0527 COMPLETE`: the patch package has no
package-level gap and is sufficient as the basis for a later exact-command
review. `%4` then completed that patched-runner exact-command review. It remains
`NOT_LAUNCH_READY_REVIEW_REQUIRED`: the patched runner closes the local
`111 > 32` contradiction, but timeout/GPU-hours/iterations/exact steps/env,
seed policy, fresh output root, and cable_drop/explosion non-inferiority
thresholds remain unsupported. At that point the route was
`HOLD_OR_NEW_EVIDENCE_SOURCE_FOR_CC6_BUDGET_AND_SAFETY_THRESHOLDS_NOT_AUTHORIZED`.
Rs/TL selected the diagnostic threshold, `%4` completed release-horizon scout
design, `%3` completed Tier-A review, and `%4` ran exactly one bounded cuda:0
diagnostic scout under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_scout_gpu_diagnostic_20260527/`.
The run exited `0` with no timeout or retry (`85s` wall time), using
`world_count=41`, `max_iterations=1`, `num_steps_per_env=128`, and `seed=42`.
It captured actual releases `3/41 = 0.0731707317`, retained-after-release
`0/3 = 0.0`, all-world cable_drop `40/41 = 0.9756097561`, all-world explosion
`35/41 = 0.8536585366`, derived release-normalized cable_drop `2/3 =
0.6666666667`, and derived release-normalized explosion `1/3 = 0.3333333333`.
The retained-after-release comparison against diagnostic threshold
`0.6694805195` is diagnostic only; it is not an efficacy proof or product
predicate. `%4` then completed the artifact-only schema-gap review under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_scout_schema_gap_review_0gpu_20260527/`.
It confirmed that observed release-step distribution is absent and cannot be
recovered from existing artifacts because raw per-world schema-v2 records were
not persisted; first-class actual-release-denominator-normalized
cable_drop/explosion fields are absent; release-class split values are derived
diagnostics only (`2/3` cable_drop and `1/3` explosion over the actual-release
denominator); and cable_drop/explosion non-inferiority thresholds remain
`REVIEW_REQUIRED`. `%4` then generated the bounded 0GPU schema patch package
under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_schema_patch_package_0gpu_20260527/`;
after `%4` stalled before final report, `%7` added and verified the missing
checksum manifest. The copied runner SHA is
`117b6d0f0ee0b77c1868857da25bcdb9958ed1311e9c3ff67f6f829a0057163d`; it adds
observed release-step distribution, bounded per-world schema-v2 records
(`record_limit=64`), and first-class actual-release-denominator-normalized
cable_drop/explosion fields. py_compile PASS, direct guard rc=64 before env
construction, and synthetic release-horizon checks PASS. `%3` then returned
`RELEASE_HORIZON_SCHEMA_PATCH_TIERA_REVIEW_COMPLETE`: the package is sufficient
as a basis for a later exact-command/runtime review route, not an execution GO.
That next route was
`BOUNDED_0GPU_RELEASE_HORIZON_EXACT_COMMAND_RUNTIME_REVIEW_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.
`%4` then completed that bounded 0GPU exact-command/runtime review. The
runtime-confirmation command envelope is ready for `%3` Tier-A review only
(`cuda:0`, 41 worlds, one iteration, 128 steps/env, seed 42, timeout 3600,
fresh output root absent, guarded draft exits 64). It is not execution GO, not
CC6 efficacy readiness, and not product evidence. At that point the route was
`SUPERVISOR_TIERA_EXACT_COMMAND_REVIEW_FOR_RELEASE_HORIZON_RUNTIME_ROUTE_NOT_AUTHORIZED_OR_HOLD`.
`%3` then returned INCOMPLETE: the package must disclose the prior same-envelope
scout's already-known retained_after_release_rate `0.0`, actual releases `3/41`,
derived release-normalized cable_drop `2/3`, and derived release-normalized
explosion `1/3`, and must narrow any rerun value to field/schema confirmation.
`%4` then completed the bounded 0GPU disclosure gapfix: the prior same-envelope
negative outcome is now explicit in the decision basis (`0/3` retained,
`3/41` actual releases, `2/3` cable_drop, `1/3` explosion), and any future
schema-patched rerun value is narrowed to field/schema confirmation only.
The then-current route was
`SUPERVISOR_TIERA_REVIEW_OF_DISCLOSURE_GAPFIX_NOT_AUTHORIZED_OR_HOLD`.
`%3` then returned
`RELEASE_HORIZON_EXACT_RUNTIME_DISCLOSURE_GAPFIX_TIERA_REVIEW_COMPLETE`: the
disclosure gap is closed, but this is not execution GO. The next route is
`COMBINED_SUPERVISOR_TIERA_EXACT_GO_REVIEW_FOR_RELEASE_HORIZON_RUNTIME_FIELD_SCHEMA_CONFIRMATION_NOT_AUTHORIZED_OR_HOLD`, which must bind
the exact-command package and disclosure delta together before any GPU launch.
`%3` then returned `RELEASE_HORIZON_COMBINED_EXACT_GO_TIERA_REVIEW_COMPLETE`:
the combined gate is complete for an Rs/TL launch decision, not launch itself.
The then-current route was
`RS_TL_DECISION_AUTHORIZE_ONE_RELEASE_HORIZON_RUNTIME_FIELD_SCHEMA_CONFIRMATION_ATTEMPT_OR_HOLD`.
Rs/TL then authorized exactly one cuda:0 runtime field/schema confirmation
attempt. `%4` completed it with shell exit `0`, no timeout/crash, one attempt
only, cuda:0 only. Runtime schema-v2 field emission is confirmed, but runtime
retention remains negative: actual releases `4/41`, retained-after-release
`0/4 = 0.0`, release-normalized cable_drop `3/4`, release-normalized explosion
`3/4`, product success `0`, and `PRODUCT_GO=false`. The then-current
supervisor result-review route has now completed.
`%3` then returned `SCHEMA_V2_RUNTIME_RESULT_REVIEW_COMPLETE`: field/schema
emission is a real-runtime PASS, but retained-after-release is `0.0` in both
same-envelope runs. Existing AR demos are not train-ready for
release-retention BC/DAPG because they lack actual-release, release-step/class,
post-release retention, cable_drop, explosion, and no-crutch provenance labels.
The current S1B data-label contract now defines the fail-closed sim2real label
requirements for future collection; no data generation or training is
authorized from this contract. The collection schema patch package has now
specified the future collector/runner patch surface without applying source
changes. `%3` reviewed that spec package as COMPLETE for proceeding to a
separate mutation-review gate, while binding exact unified diff as a mandatory
next-gate requirement. The exact source diff package has now completed as an
eval-runs-local collector-only draft: it defaults/refuses away from `cuda:1`,
adds opt-in release-retention labels, requires provenance plus real-observability
attestation, and keeps converter/training changes deferred. `%3` reviewed that
exact diff package as COMPLETE for a separate collector source mutation
decision. Rs/TL then authorized and `%4` completed the collector-only source
mutation. Collector SHA is now
`0cdbc9b3324b7775d9e1012edfcda2b43b35886141f56095ea3c1e4114cddcfa`; converter,
training, task_config, env, and w41 cache SHAs remained unchanged. Collector
execution, data generation, training, product claims, and cuda:1 remain
unauthorized. The collection exact-command gate found the current collector is
still not launch-ready because it cannot pass reviewed D0/S1A release telemetry
cfg into the env; without that cfg, `s1a_post_release_phase` remains zero.
Rs/TL completed the bounded 0GPU collector env-cfg arg source-diff package; the
exact collector-only diff is ready for supervisor Tier-A mutation review, but
source mutation is not authorized. Supervisor `%3` then returned COMPLETE and
Rs/TL applied the reviewed env-cfg arg source mutation to the collector only.
Collector SHA is now `20eda9cb...`; task_config, env, and w41 cache remained
unchanged. Supervisor `%3` then returned
`S1B_COLLECTION_EXACT_COMMAND_TIERA_REVIEW_COMPLETE`, after which Rs/TL
authorized exactly one cuda:0 S1B collection smoke. `%4` completed the single
attempt with exit `0`, no timeout, no retry, and no cuda:1 use. Output root:
`eval_runs/r2a_track_a_s1b_collection_smoke_after_env_cfg_20260527/`.
The generated NPZ SHA is
`04039ce73c1318433b61df1ced80988d91bc1712190f61514cb06e2c4e3f98dc`.
It contains S1B label/provenance fields but recorded `0/41` actual releases and
`0/41` retained-after-release labels. `%4` then completed 0GPU artifact review:
schema/provenance fields are present, but all rows are `aborted_before_release`,
transition step max is `47`, and `configured_release_step` persisted as `-1`
despite the command env-cfg release step `80`. Therefore the current route is
`BOUNDED_0GPU_S1B_COLLECTION_ZERO_RELEASE_ROOT_CAUSE_REDESIGN_NOT_AUTHORIZED_OR_HOLD`.
Mechanical/product predicate remains sim2real-oriented:
autonomous post-release cable retention is required for product success;
hold-to-completion, hidden support, kinematic support, fixture pinning,
`inv_mass=0`, or direct sim-state writes do not count.

---

## 1. 座標系

- **原点:** ロボット左腕ベース直下（床面）
- **+X:** ロボット正面方向（テーブル奥へ）
- **+Y:** 左腕→右腕方向
- **+Z:** 鉛直上
- **単位:** メートル [m]、ラジアン [rad]

---

## 2. ロボット — Franka Panda × 2

**ソース:** `task_config.py:16-17`, `test_newton_clip_routing_sdf_plain.py:83-86`

### 2.1 ベース配置

| パラメータ | Left Arm | Right Arm |
|-----------|----------|-----------|
| Base X [m] | 0.0 | 0.0 |
| Base Y [m] | -0.35 | +0.35 |
| Base Z [m] | 0.80 (TABLE_HEIGHT) | 0.80 (TABLE_HEIGHT) |
| 向き | +X方向 | +X方向 |
| Arm-to-Arm間隔 [m] | 0.70 | (左右対称) |

### 2.2 エンドエフェクタ

| パラメータ | 値 | 単位 | ソース |
|-----------|-----|------|--------|
| EE_TO_FINGERTIP | 0.220 | m | task_config.py:22 |
| 内訳 (URDF) | 0.107 + 0.0584 + 0.0545 | m | panda_hand→finger tip |
| EE Body Index | 6 (panda_hand) | — | per arm relative |
| Finger Body Index | 7, 8 | — | left/right finger |

### 2.3 グリッパ

| パラメータ | 値 | 単位 | ソース |
|-----------|-----|------|--------|
| FINGER_OPEN_POS | 0.04 | m | task_config.py:112 |
| FINGER_HALF_OPEN_POS | 0.006 | m | task_config.py:113 |
| FINGER_CLOSE_POS | 0.002 | m | task_config.py:114 |
| Max Finger Width | 0.08 (2×0.04) | m | 全開時の指間距離 |
| Close Gap | 0.004 (2×0.002) | m | 把持時指間距離 |

### 2.6 Scoop Claw 指設計

VBD solver の kinematic body (inv_mass=0) は摩擦力による引き上げを生成しない。
側面からの把持（lateral normal force）では cable lift 不可能。

**2026-05-23 R2-A Track A consistency note:** Track A の
`release_after_success_hold_k` は Phase4 で `MECHANISM_GO_RELEASE_GATE_V2 /
PRODUCT_GO_FALSE`、C5A/C5B で `C5A_GUARD_REVIEW / C5B_TRIAGE_COMPLETE`、
C6A/C6B で timeout-recovery design/runnable eval path COMPLETE、C6B smoke で
`C6B_TIMEOUT_RECOVERY_REVIEW_OR_NO_GO`、C6C で
`C6C_POSTHOC_TRIAGE_COMPLETE`、C6D/C6E で eval-path telemetry contract
design/scaffold COMPLETE、C6F で contract-results review COMPLETE、C6G で
telemetry auth package COMPLETE、C6H で telemetry runner scaffold COMPLETE、
C6I で scaffold review COMPLETE、C6J で telemetry GPU-auth draft review
COMPLETE、C6K で live telemetry runner scaffold COMPLETE、C6L で telemetry
GPU-auth package review COMPLETE、C6M で live telemetry GPU smoke COMPLETE、
C6N で C6M posthoc review COMPLETE、C6O で timeout-recovery no-go closeout
COMPLETE、C7 で new timeout-recovery variable design COMPLETE、C7A で early
strict-ready capture scaffold COMPLETE、C7B で scaffold review COMPLETE、C7C
で launch-capable runner implementation COMPLETE、C7D で C7C runner review /
GPU-auth package review COMPLETE、C7E で eval-path completion COMPLETE、
C7F で C7E review / GPU-auth package review COMPLETE、C7F post-review
launch-path sanity correction COMPLETE、C7H で launch-path 0GPU implementation
COMPLETE、C7I で C7H review / GPU-auth package review COMPLETE、さらに C7J で
bounded GPU smoke COMPLETE、C7K で C7J posthoc review COMPLETE、C7L で
objective/policy redesign COMPLETE、C7M で objective/policy package review
COMPLETE、C7N で payload completion package COMPLETE、C7O で payload runner
scaffold COMPLETE、C7P で payload collection auth package review COMPLETE、C7Q で
payload collection runner implementation COMPLETE、C7R で payload collection
auth package review COMPLETE、C7S で collect-path completion COMPLETE、C7T で
payload collection auth package review COMPLETE、C7U で payload collection launch
decision REVIEW-HOLD、C7V で real payload-writing path 0GPU COMPLETE、C7W で
payload collection auth package review COMPLETE、C7X で real collector-to-writer
integration COMPLETE、C7Y で payload collection auth package review COMPLETE、C7Z
で launch-capable collector-writer runner COMPLETE、C8A で payload collection auth
package review COMPLETE、C8B で guarded writer invocation path COMPLETE、C8C で
payload collection auth package review COMPLETE、C8D で real C7V writer output
path COMPLETE、C8E で payload collection auth package review COMPLETE まで進んだ。
**2026-05-24 current-state addendum:** Track A は D0+C4 decision package
`R2A_TRACK_A_D0_C4_DECISION_PACKAGE_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで進行。
D0 は future release-transient/oracle-retention discriminator、C4 は
autonomous post-release hold と continuous hold until clip hand-off の
product-predicate clarification。これは mechanical/product predicate の
分岐整理であり、GPU/simulator execution、source/task_config mutation、training、
product claim、physical-grasp claim、T-ROOT 95 claim は未承認。
**2026-05-24 G1-G3 refinement addendum:** Track A は
`R2A_TRACK_A_D0_C4_G1_G3_REFINEMENT_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで進行。
G1 は oracle を credible physical upper bound とし、weak oracle failure を
`D0_INCONCLUSIVE_REVIEW_HOLD` に落とす。G2 は abrupt support-removal / inv_mass
release artifact と sustained physics/task limit と policy/control gap を分離し、
ramp artifact は cheap smooth/handoff design delta に送る。G3 は C4 を
SOMA/routing/product-predicate sources に grounding し、continuous-hold reframing
は明示選択がない限り descope/reframe と扱う。
**2026-05-24 D0 discriminator preflight addendum:** Track A は
`R2A_TRACK_A_D0_DISCRIMINATOR_PREFLIGHT_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで進行。
future D0 question、arms、stop conditions、G1 oracle sanity gate、G2 branch
taxonomy、C4 predicate gate、metrics、sample budget、classification rules、
future command draft `NOT_AUTHORIZED_DO_NOT_RUN`、Tier-A review packet が
artifact-only で整備された。runner/source mutation が future D0 execution の
前提だが、execution、GPU/simulator、source/task_config mutation、training、
product claim、physical-grasp claim、T-ROOT 95 claim は未承認かつ
Tier-A-required。
**2026-05-24 D0 Tier-A gap closure addendum:** Track A は
`R2A_TRACK_A_D0_TIERA_GAP_CLOSURE_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで進行。
GAP-1 は L0-L3 graded oracle capability ladder で閉じ、hard-row oracle
failure は `ORACLE_CAPABILITY_SUSPECT_OR_INCONCLUSIVE` へ送る。GAP-2 は
`AMBIGUOUS_REQUIRES_RS_DECISION` として閉じた。local sources は routing/no-drop/
unclamp/handoff constraints を支持するが、autonomous post-release hold と
continuous hold until clip hand-off のどちらを binding product predicate と
するかは客観的に選ばない。GAP-3 は runner-design Tier-A へ carry-forward。
execution、GPU/simulator、source/task_config mutation、training、product claim、
physical-grasp claim、T-ROOT 95 claim は未承認。
**2026-05-24 D0 runner-design review addendum:** Track A は
`R2A_TRACK_A_D0_RUNNER_DESIGN_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで進行。
Rs proxy は original product predicate として autonomous post-release hold を
選択し、continuous hold until clip hand-off は descope/comparator only とした。
oracle pose hold、release_ramp_5、release_ramp_10、support-removal ablation は
bounded source surface で implementable。hold-to-completion は comparator only。
contact-force-limited impedance handoff は `UNCLEAR_REQUIRES_SOURCE_SPIKE`。
次は impedance telemetry/proxy feasibility の 0GPU source-surface spike/review。
source/task_config mutation、D0 execution、GPU/simulator、training、product claim、
physical-grasp claim、T-ROOT 95 claim は未承認。
**2026-05-24 D0 impedance source-surface spike addendum:** Track A は
`R2A_TRACK_A_D0_IMPEDANCE_SOURCE_SURFACE_SPIKE_0GPU_COMPLETE / PRODUCT_GO_FALSE`
まで進行。spike outcome は
`SPIKE_PASS_TRUE_CONTACT_FORCE_TELEMETRY_SURFACE_IDENTIFIED`。Track A env は
direct contact-force telemetry をまだ expose していないが、in-repo
ContactSensor surfaces は `net_forces_w` と filtered `force_matrix_w` による
true normal contact force telemetry を示す。left-finger spring force は proxy-only。
次は future source implementation draft 前の supervisor Tier-A review。
source/task_config mutation、D0 execution、GPU/simulator、training、product claim、
physical-grasp claim、T-ROOT 95 claim は未承認。
**2026-05-24 D0 telemetry-only source draft addendum:** Track A は
`R2A_TRACK_A_D0_TELEMETRY_SOURCE_DRAFT_COMPLETE / PRODUCT_GO_FALSE` まで進行。
`newton_aerial_regrasp_env.py` に opt-in/default-OFF、
observational-only、normal-force-only の ContactSensor telemetry surface を
追加し、left-finger spring effort は proxy telemetry として別ラベル化した。
`task_config.py` は `1b8f2739...` のまま、env SHA は `d5b9cad...` に
再baseline。D0 execution、oracle/impedance/ramp control implementation、
GPU/simulator、training、further source/task_config mutation、product claim、
physical-grasp claim、T-ROOT 95 claim は未承認。
**2026-05-24 D0 control-source design packet addendum:** Track A は
`R2A_TRACK_A_D0_CONTROL_SOURCE_DESIGN_PACKET_0GPU_COMPLETE / PRODUCT_GO_FALSE`
まで進行。oracle hold、release ramps、impedance handoff、
support-removal ablation、hold-to-completion comparator の per-arm
control-source design と no-crutch matrix を作成し、kinematic pin /
`inv_mass=0` support、direct reset、hidden support、active/hold-to-completion
product credit を禁止した。future bounded source implementation は
separate Tier-A-required かつ未承認。
**2026-05-24 D0 control-source implementation draft addendum:** Track A は
`R2A_TRACK_A_D0_CONTROL_SOURCE_IMPLEMENTATION_DRAFT_COMPLETE / PRODUCT_GO_FALSE`
まで進行。`newton_aerial_regrasp_env.py` に opt-in/default-OFF の D0
control-arm config/metadata surfaces を追加し、oracle hold、release ramps、
impedance handoff、support-removal ablation、hold-to-completion comparator を
future runner が選択できる source draft を作成した。D0 product arms は
kinematic left-finger support 有効時に fail closed し、D0 checked paths は
kinematic pin / `KINEMATIC_INV_MASS` / `write_joint_state_to_sim` を使わない
ことを AST で確認済み。`task_config.py` は `1b8f2739...` のまま、env SHA は
`87875a...` に再baseline。D0 execution、GPU/simulator、training、further
source/task_config mutation、product claim、physical-grasp claim、T-ROOT 95
claim は未承認。
**2026-05-24 D0 control-source artifact review addendum:** supervisor `%3` が
completed source draft と artifacts を read-only で独立確認し、
`R2A_TRACK_A_D0_CONTROL_SOURCE_IMPL_ARTIFACT_REVIEW_COMPLETE / PRODUCT_GO_FALSE`
と判定。source draft は bounded no-crutch/default-OFF として COMPLETE、
source gap fix 不要。real spring force scaling + IK target blend、kinematic
support mutual exclusion、default-OFF baseline preservation、product-false
metadata を確認済み。次は separately scoped final 0GPU D0 runner/preflight
package for Tier-A review、または HOLD。D0 execution/GPU/simulator/training は
未承認で、human Rs predicate confirmation は GPU D0 前に必要。
**2026-05-24 D0 runner/preflight package addendum:** Track A は
`R2A_TRACK_A_D0_RUNNER_PREFLIGHT_PACKAGE_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで
進行。final 0GPU package が future D0 executable boundary、arms、oracle
ladder、G2 materiality thresholds、sample guards、refusal states、protected SHA
locks、cuda:0-only future command shape、人間 Rs predicate gate を束ねた。
future command は `NOT_AUTHORIZED_DO_NOT_RUN`。次は supervisor Tier-A review
over the completed package、または HOLD。D0 execution/GPU/simulator/training は
未承認。
**2026-05-24 D0 runner/preflight Tier-A review addendum:** supervisor `%3` は
completed package を read-only で review し、
`R2A_TRACK_A_D0_RUNNER_PREFLIGHT_TIERA_REVIEW_INCOMPLETE / PRODUCT_GO_FALSE`
と判定。GAP-A は human-Rs predicate confirmation が CLI flag で自己申告可能な
点で、verifiable human-Rs confirmation artifact contract へ強化が必要。GAP-B
は package が contract/preflight であり functional D0 runner ではないという
forward clarification。次は bounded 0GPU GAP-A gate-strengthening fix、または
HOLD。D0 execution/GPU/simulator/training、functional D0 runner implementation、
product/physical-grasp/T-ROOT 95 claim は未承認。
**2026-05-24 D0 human-Rs gate GAP-A fix addendum:** real `%4` は
`R2A_TRACK_A_D0_HUMAN_RS_GATE_GAPFIX_0GPU_COMPLETE / PRODUCT_GO_FALSE` まで
進行。fresh artifact-only package は
`eval_runs/r2a_track_a_d0_human_rs_gate_gapfix_0gpu_20260524/`。CLI boolean
自己申告モデルを fail-closed human-Rs confirmation artifact contract に置換する
static delta と contract を作成し、actual confirmation は `NOT_PRESENT` のまま。
GAP-B の functional D0 runner は separate Tier-A item として未承認。次は
supervisor Tier-A review of GAP-A fix、または HOLD。
**2026-05-24 D0 human-Rs gate GAP-A fix review addendum:** supervisor `%3` は
GAP-A fix を read-only review し、
`R2A_TRACK_A_D0_HUMAN_RS_GATE_GAPFIX_TIERA_REVIEW_COMPLETE / PRODUCT_GO_FALSE`
と判定。contract fix は COMPLETE。ただし sufficient condition は user channel
で human Rs が predicate decision を明示し、supervisor `%3` が artifact が
その実 decision に trace すると attest すること。actual confirmation は
`NOT_PRESENT` のまま。次は human Rs predicate decision + supervisor
attestation、または HOLD。
**2026-05-25 human-Rs predicate attestation addendum:** supervisor `%3` は
`%7` relay 経由の human Rs predicate quote を review し、
`R2A_TRACK_A_HUMAN_RS_PREDICATE_ATTESTATION_PENDING_DIRECT_CONFIRMATION /
PRODUCT_GO_FALSE` と判定。predicate 内容（sim2real 前提、post-release
autonomous retention、kinematic support / inv_mass=0 / sim-state write /
active_at_completion / hold-to-completion-only success を product success から
除外）は operational に同意。ただし `%7` relay は agent-mediated なので GAP-A
sufficiency closure には不足。次は human Rs が `%3` に直接 confirmation、または
HOLD。
**2026-05-25 Rs-proxy predicate transmission review addendum:** supervisor
`%3` は、human Rs が `%7`/Rs proxy に predicate 送付を明示許可したことを review
し、`R2A_TRACK_A_HUMAN_RS_PREDICATE_ATTESTED_VIA_RS_PROXY /
PRODUCT_GO_FALSE` と判定。attested predicate は sim2real 前提で、post-release
autonomous cable retention を product success に要求し、kinematic support /
inv_mass=0 / sim-state write / active_at_completion / hold-to-completion-only
success を除外する。standing Rs principle: sim2real が実現できない目標は採用しない。
次は GAP-B functional D0 runner Tier-A planning、または HOLD。
**2026-05-25 GAP-B functional runner planning addendum:** Track A は
`R2A_TRACK_A_GAPB_FUNCTIONAL_D0_RUNNER_TIERA_PLANNING_0GPU_COMPLETE /
PRODUCT_GO_FALSE` まで進行。fresh artifact-only package は
`eval_runs/r2a_track_a_gapb_functional_d0_runner_tiera_planning_0gpu_20260525/`。
future functional D0 runner の behavior、sim2real product-success/refusal
gates、no-crutch schema、sample/power guard、Tier-A review questions を定義した。
これは planning only で、functional runner implementation、D0 execution、
GPU/simulator、source/task_config mutation、training、product claim、
physical-grasp claim、T-ROOT 95 claim は未承認。次は supervisor `%3` Tier-A
review of the GAP-B planning package、または HOLD。
**2026-05-25 GAP-B planning review addendum:** supervisor `%3` は GAP-B
planning package を read-only review し、
`R2A_TRACK_A_GAPB_FUNCTIONAL_D0_RUNNER_TIERA_PLANNING_REVIEW_COMPLETE /
PRODUCT_GO_FALSE` と判定。planning は future functional-runner
implementation-authorization decision の基礎として COMPLETE。M1:
task-appropriate release timing を implementation 前/中に具体定義すること。
M2: existing default-off D0 surfaces で十分か、source mutation が必要なら stop
して separate Tier-A に送ること。次は bounded functional D0 runner
implementation authorization request、または HOLD。GPU D0 は別 Tier-A。
**2026-05-25 GAP-B functional runner implementation addendum:** Track A は
`R2A_TRACK_A_GAPB_FUNCTIONAL_D0_RUNNER_IMPL_0GPU_COMPLETE /
PRODUCT_GO_FALSE` まで進行。fresh eval-root package は
`eval_runs/r2a_track_a_gapb_functional_d0_runner_impl_0gpu_20260525/`。
future runner `run_gapb_functional_d0_runner.py` を実装したが、D0 execution /
GPU/simulator は未実行。M1 は right clamp + cable-not-dropped sustained K=5
then next-step release として encode。M2 は
`SURFACE_SUFFICIENT_NO_SOURCE_MUTATION`。py_compile、JSON parse、static
checks、protected SHA、GPU empty、forbidden-output/bytecode cleanup は relay
側でも PASS。次は minimal supervisor artifact-only review、または HOLD。
**2026-05-25 GAP-B functional runner schema-fix addendum:** `%3` visible
minimal-review findings と relay-side verification により、prior implementation
package は `info["log_per_world"]` を list-of-dicts と仮定し、current env が emit
しない stale kinematic pseudo-fields を読んでいるため INCOMPLETE と判定。real
`%4` は fresh root
`eval_runs/r2a_track_a_gapb_functional_d0_runner_impl_schemafix_0gpu_20260525/`
を作成し、`R2A_TRACK_A_GAPB_FUNCTIONAL_D0_RUNNER_SCHEMAFIX_0GPU_COMPLETE /
PRODUCT_GO_FALSE` まで進行。repaired runner は dict-of-arrays の
`log_per_world` schema を読み、stale key reads を除去し、missing required schema
では product/no-crutch credit を fail closed する。prior impl root、source、
`task_config.py` は未変更。py_compile、JSON parse、describe-contract、static
schema checks、protected SHA、GPU empty、forbidden-output/bytecode cleanup は
relay 側でも PASS。次は minimal supervisor artifact-only review of schema-fix
package、または HOLD。D0 execution/GPU/simulator/training/product claim は未承認。
**2026-05-25 GAP-B schema-fix review addendum:** supervisor `%3` は schema-fix
package を read-only review し、
`R2A_TRACK_A_GAPB_FUNCTIONAL_D0_RUNNER_SCHEMAFIX_REVIEW_COMPLETE /
PRODUCT_GO_FALSE` と判定。B1 は resolved（dict-of-arrays `log_per_world`
handling accepted、old `per_world[0]` assumption absent）。B2 は resolved
（stale kinematic pseudo-fields absent、emitted `kinematic_left_finger_support_enabled`
と `kinematic_active_at_completion` を使用）。`schema_incomplete_no_crutch` が
`PRODUCT_EXCLUDED_REASONS` に入り、missing schema / active support は
`product_success=false` に fail closed。次は separately scoped GPU D0
authorization review、または HOLD。D0 execution/GPU/simulator/training/product
claim は依然未承認。
**2026-05-25 GPU D0 authorization packet addendum:** real `%4` は
review-only packet
`eval_runs/r2a_track_a_gapb_gpu_d0_authorization_packet_0gpu_20260525/` を作成し、
`R2A_TRACK_A_GPU_D0_AUTHORIZATION_PACKET_0GPU_COMPLETE / PRODUCT_GO_FALSE`
まで進行。exact cuda:0 command、predicate attestation JSON、fresh future output
root `eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_20260525/` を
bind したが、future output root は absent のまま。relay 側で JSON parse、
canonical text SHA、runner `validate_static_preconditions()`、protected SHA、
runner SHA、cuda:0-only command scan、GPU empty が PASS。これは
AUTH_REVIEW_ONLY_DO_NOT_RUN で、次は supervisor `%3` Tier-A review of exact
packet、または HOLD。D0 execution/GPU/simulator/training/product claim は依然未承認。
**2026-05-25 GPU D0 authguard fix addendum:** supervisor `%3` は first GPU D0
authorization packet を B-GPU-1 で INCOMPLETE と判定。`compiled_by` に proxy
compilation が正直に記録されている一方、runner validator が `generated_by` のみを
見ていたため、proxy attestation が product-scoring guard を bypass し得た。real
`%4` は fresh runner root
`eval_runs/r2a_track_a_gapb_functional_d0_runner_impl_authguardfix_0gpu_20260525/`
と fresh packet root
`eval_runs/r2a_track_a_gapb_gpu_d0_authorization_packet_authguardfix_0gpu_20260525/`
を作成し、`R2A_TRACK_A_GPU_D0_AUTHGUARD_FIX_0GPU_COMPLETE / PRODUCT_GO_FALSE`
まで進行。authguardfix runner は proxy provenance を検出し、
`DIAGNOSTIC_ONLY_PROXY_ATTESTED` としてのみ受理、`predicate_product_scoring_authorized=false`
かつ `strategic_routing_authorized=false` に固定。synthetic classification で
actual release + retained_30 + no crutch でも `product_success=false` を確認。
supervisor `%3` は light re-review で B-GPU-1 closure を COMPLETE と確認
（proxy provenance は `compiled_by` を含む provenance fields で検出され、
packet attestation の `%4`/`%7` proxy token set に一致し、product scoring は
false に固定）。次は separately scoped diagnostic-only GPU D0 launch
authorization、または HOLD。D0 execution/GPU/simulator/training/product claim は
その別 directive まで未承認で、product scoring / strategic routing は引き続き不可。
**2026-05-25 diagnostic-only GPU D0 abort addendum:** `%7` は `%3` COMPLETE
後に exact cuda:0 command を 1 回だけ authorization し、real `%4` が実行した。
D0 は実行されず、IsaacLab import が env instantiation 前に
`ModuleNotFoundError: No module named 'lazy_loader'` で abort。completion は
0/861 expected、future output root は absent、結果 artifact なし。
protected SHA は維持、GPU compute-app query empty、cuda:1 使用証拠なし。
その後 bounded 0GPU import-dependency / canonical-runtime remediation triage
を実施済み。retry / same-scope launch は未承認。
**2026-05-25 import-runtime triage addendum:** real `%4` は 0GPU/read-only
triage root
`eval_runs/r2a_track_a_d0_import_runtime_remediation_triage_0gpu_20260525/`
を作成し、`R2A_TRACK_A_D0_IMPORT_RUNTIME_TRIAGE_0GPU_COMPLETE /
PRODUCT_GO_FALSE` まで進行。failed wrapper は `/home/rlrk/env_isaaclab6/bin/python`
で `isaaclab` / `thread_isaac_lab` は resolve するが `lazy_loader` は absent。
repo-local `env_isaaclab` は `lazy_loader` present だが runtime switch は
launch-relevant で未承認。prior-art は piecemeal `lazy_loader` install + retry
を禁止。次は separate 0GPU canonical runtime provisioning / runtime-selection
review package、または HOLD。
**2026-05-25 canonical runtime review addendum:** real `%4` は separate
0GPU/read-only review root
`eval_runs/r2a_track_a_d0_canonical_runtime_review_0gpu_20260525/` を作成し、
`R2A_TRACK_A_D0_CANONICAL_RUNTIME_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`
まで進行。`isaaclab.sh` は explicit `VIRTUAL_ENV=/home/rlrk/env_isaaclab6`
指定時に `/home/rlrk/env_isaaclab6/bin/python` を選び、default では
repo-local `env_isaaclab` を選ぶことを確認。failed command の runtime family は
Python 3.12 / Isaac Sim 6.0 / Warp 1.13 の `env_isaaclab6` で、ここに
`lazy_loader` が absent。repo-local `env_isaaclab` は `lazy_loader` present だが
Python 3.11 / Isaac Sim 5.1 / Warp 1.10 へ切り替わるため、runtime switch は
選択しない。recommended route は Option A: explicit `env_isaaclab6`
provisioning repair with holistic 0GPU verification、または HOLD。install / venv
mutation / runtime switch / runner patch / D0 retry / GPU launch は別 directive まで
未承認。
**2026-05-25 env_isaaclab6 provisioning repair addendum:** supervisor `%3` は
repair directive を G1 shared-venv safety gap で INCOMPLETE としたが、%7 が
mandatory process-binding check と rollback reference/restore condition を directive に
incorporate。real `%4` は
`eval_runs/r2a_track_a_d0_env_isaaclab6_provisioning_repair_20260525/` で
bounded 0GPU repair を完了し、
`/home/rlrk/env_isaaclab6/bin/python -m pip install --no-deps lazy-loader==0.5`
のみを実行。G1 process guard PASS、`pip check` before/after は pre-existing
`isaacsim-core 6.0.0.0` requires `filelock==3.20.0` だが env has
`filelock 3.25.2` の同一 issue のみで new breakage なし、rollback なし。
`VIRTUAL_ENV=/home/rlrk/env_isaaclab6 ./isaaclab.sh -p` は canonical env6
Python を使い、`lazy_loader` / `isaaclab` / `isaaclab.sim` / `isaaclab.app` /
`thread_isaac_lab` / `torch` / `warp` / `pxr` namespace は lightweight check で
resolve。D0 retry / GPU / simulator / runtime switch / runner patch /
source/task_config mutation / product scoring / D1-D3 routing は未承認。
**2026-05-25 post-repair D0 GPU abort addendum:** `%3` は post-repair exact
D0 GPU gate を COMPLETE とし、`%7` は exact diagnostic-only cuda:0 command を
1 回のみ authorize。real `%4` が実行したが、D0 は開始せず、Omniverse Kit
EULA prompt が Yes/No を要求し、non-interactive bootstrap が
`Unable to bootstrap inner kit kernel: EOF when reading a line` で abort。
completion は 0/861、output root は absent、`full_summary.json` /
`completion_records.json` なし。これは product result ではなく runtime
bootstrap abort。relay は
`eval_runs/r2a_track_a_postrepair_d0_gpu_abort_20260525/` に evidence-preservation
artifact を作成。retry / EULA acceptance / runtime remediation / GPU launch /
runtime switch / runner patch / source/task_config mutation / product scoring /
D1-D3 routing は未承認。
**2026-05-25 runtime EULA/bootstrap review addendum:** real `%4` は
`eval_runs/r2a_track_a_runtime_eula_bootstrap_review_0gpu_20260525/` で
bounded 0GPU/read-only review を完了。status は
`R2A_TRACK_A_RUNTIME_EULA_BOOTSTRAP_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`、
decision は
`RECOMMEND_HUMAN_OPERATOR_EULA_ACCEPTANCE_ATTESTATION_THEN_SEPARATE_EXACT_COMMAND_REVIEW_NOT_AUTHORIZED`。
post-repair abort は `RUNTIME_EULA_PROMPT_BOOTSTRAP_ABORT_NOT_D0_OUTCOME`
で、D0 outcome ではない。local evidence は first Isaac Sim run が NVIDIA
Omniverse License Agreement acceptance を prompt すること、および future
transient `OMNI_KIT_ACCEPT_EULA=YES` precedent があることを示すが、
その使用は明示 human/operator EULA acceptance provenance 後、separate
exact-command review 後に限る。persistent license-state mutation は未選択。
EULA acceptance、`OMNI_KIT_ACCEPT_EULA=YES` execution、D0 retry、GPU/sim、
runtime remediation/switch、venv/dependency/source/task_config/runner mutation、
product scoring、D1-D3 routing は未承認。
**2026-05-25 EULA-attested exact-command review addendum:** real `%4` は
`eval_runs/r2a_track_a_eula_attestation_exact_command_review_0gpu_20260525/`
で bounded 0GPU/artifact-only package を完了。status は
`EULA_ATTESTED_EXACT_D0_COMMAND_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`、
decision は `READY_FOR_SUPERVISOR_TIER_A_REVIEW_OF_EXACT_DIAGNOSTIC_COMMAND_NOT_AUTHORIZED`。
user-channel の interactive first-run transcript（EULA prompt に `Yes`、
`The EULA was accepted.`、`isaacsim import ok`）を
`HUMAN_OPERATOR_EULA_ATTESTATION` として保存し、runtime/workspace/
protected SHAs/authguardfix runner/future output root に bind。relay は
display-derived transcript typo を補正し、`import isaacsim; print(...)` を保存。
future exact command は transient `OMNI_KIT_ACCEPT_EULA=YES` を含むが
`NOT_AUTHORIZED_DO_NOT_RUN`。次は `%3` Tier-A review、または HOLD。
D0 retry/GPU/sim/`OMNI_KIT_ACCEPT_EULA=YES` execution/product scoring/D1-D3
routing は未承認。
**2026-05-25 EULA-attested D0 GPU abort addendum:** `%3` は exact-command
packet の Q4 blocker を COMPLETE とし、`%7` は EULA-attested diagnostic-only
cuda:0 command を 1 回だけ authorize。real `%4` は exact command を実行したが、
D0 は開始せず、lazy env import が
`ImportError: cannot import name 'DeformableObject' from 'isaaclab.assets'`
で output root 作成前に abort。completion は 0/861、output root は absent、
`full_summary.json` / `completion_records.json` なし、post-run GPU query empty、
cuda:1 unused。これは cable mechanics や D0 discriminator の結果ではなく、
IsaacLab API import mismatch。次は bounded 0GPU import API mismatch remediation
review、または HOLD。D0 retry/execution、API/source fix、GPU/simulator、
runtime/dependency mutation、product scoring、D1-D3 routing は未承認。
**2026-05-25 import API mismatch review addendum:** relay `%7` は
`eval_runs/r2a_track_a_import_api_mismatch_review_0gpu_20260525/` で bounded
0GPU/read-only review を完了。status は
`R2A_TRACK_A_IMPORT_API_MISMATCH_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`。
原因は `LOCAL_THREAD_PACKAGE_IMPORT_SIDE_EFFECT_PLUS_ISAACLAB_6_ASSET_API_SPLIT`。
D0 runner が `thread_isaac_lab.envs.newton_aerial_regrasp_env` を package 経由で
import するため `thread_isaac_lab/envs/__init__.py` が legacy `assets_cfg.py` を
eager import し、そこが IsaacLab 6 で `isaaclab_physx` に移動済みの
`DeformableObject` / `DeformableObjectCfg` を core `isaaclab.assets` から
import しようとして abort。これは cable mechanics ではなく import route/API split
問題。recommended next は fresh 0GPU runner direct-env-import bypass patch
package、または HOLD。D0 retry/execution、GPU/simulator、source/task_config
mutation、runtime/dependency mutation、product scoring、D1-D3 routing は未承認。
**2026-05-25 runner direct-import bypass addendum:** relay `%7` は
`eval_runs/r2a_track_a_runner_direct_import_bypass_0gpu_20260525/` で fresh
eval_runs-only runner package を完了。status は
`R2A_TRACK_A_RUNNER_DIRECT_IMPORT_BYPASS_0GPU_COMPLETE / PRODUCT_GO_FALSE`。
新 runner SHA は
`af5d6806a0cd125ccb552373c7b7c407d4a95b7aaab8aab35849b4a7f6223b0e`。変更は
future runner の import route のみで、`thread_isaac_lab/envs` を `sys.path`
に追加し `newton_aerial_regrasp_env` を direct import することで
`thread_isaac_lab.envs.__init__` / legacy `assets_cfg.py` side effect を回避。
env6 `py_compile`、`describe-contract`、invalid-marker refusal、old-import
static scan、protected source diff、protected SHA、GPU query empty は PASS。
次は artifact review または separate Tier-A launch review、または HOLD。
D0 retry/execution、GPU/simulator、source/task_config/runtime/dependency
mutation、product scoring、D1-D3 routing は未承認。
**2026-05-25 direct-import D0 refusal addendum:** `%3` Tier-A COMPLETE 後、
relay `%7` は direct-import runner の diagnostic cuda:0 command を 1 回だけ
authorize し、real `%4` が exactly once 実行。status は
`R2A_TRACK_A_DIRECT_IMPORT_D0_REFUSED_WRONG_TARGET_OUTPUT_ROOT / PRODUCT_GO_FALSE`。
runner は D0 前に `future_preconditions_failed` / `wrong_target_output_root`
で fail-closed refusal。原因は predicate attestation の `target_output_root`
が `eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_authguardfix_20260525`
なのに対し、command が
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_direct_import_bypass_20260525`
を指定したこと。D0 execution=false、completion 0/861、両 root absent、
result JSON absent、protected SHA unchanged、GPU query empty、cuda:1 unused、
retry なし。次は bounded 0GPU exact-command alignment review、または HOLD。
retry/GPU/simulator/source/task_config/runner/runtime/dependency/attestation
mutation/product scoring/D1-D3 routing は未承認。
**2026-05-25 exact-command alignment review addendum:** relay `%7` は
`eval_runs/r2a_track_a_exact_command_alignment_review_0gpu_20260525/` で
bounded 0GPU review を完了。status は
`R2A_TRACK_A_EXACT_COMMAND_ALIGNMENT_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`。
既存 predicate attestation の `target_output_root` は
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_authguardfix_20260525`
で、review 時点では両 root は absent。aligned root で direct-import runner の
`validate_static_preconditions` を 0GPU static call した結果は
`STATIC_PRECONDITIONS_OK`、expected completion 861、
`predicate_product_scoring_authorized=false`、
`strategic_routing_authorized=false`。当時の次手は concise `%3` Tier-A re-review
of corrected exact command、または HOLD。retry/GPU/simulator/source/task_config/
runner/runtime/dependency/attestation mutation/product scoring/D1-D3 routing
は未承認。
**2026-05-25 corrected-root D0 record-errors addendum:** `%3` corrected-root
Tier-A COMPLETE 後、relay `%7` は corrected-root diagnostic cuda:0 command を
1 回だけ authorize し、real `%4` が exactly once 実行。status は
`R2A_TRACK_A_CORRECTED_ROOT_D0_RECORD_ERRORS_REVIEW_REQUIRED /
PRODUCT_GO_FALSE`。runner は output root を作成し `aborted=false` で終了したが、
records は 21/861 expected のみで全件 `execution_status=ERROR`。actual
release、post-release retained 30-step、product success はすべて 0。主因は
precondition cache `aerial_regrasp_w41_p0_v2.npz` missing が 18 records、
`d0_contact_telemetry_enabled=True` に対して `d0_contact_sensor_prim_path` が
ない `BLOCKED_CONTACT_SENSOR_INTEGRATION` が 3 records。これは D0
diagnostic 判定、product evidence、D1-D3 routing basis ではない。protected
SHA は task_config `1b8f...`、env `87875a...`、direct-import runner
`af5d6806...` のまま、cuda:1 unused、post-run GPU query empty、retry なし。
次は bounded 0GPU precondition-cache/contact-sensor error review、または
HOLD。retry/GPU/simulator/source/task_config/runner/runtime/dependency
mutation/product scoring/D1-D3 routing は未承認。
**2026-05-25 corrected-root D0 error-review addendum:** real `%4` は
`eval_runs/r2a_track_a_corrected_root_d0_error_review_0gpu_20260525/` で
bounded 0GPU/read-only review を完了。status は
`R2A_TRACK_A_CORRECTED_ROOT_D0_ERROR_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`。
decision は
`D0_NOT_ANSWERED_ALL_RECORDS_ERROR_REQUIRES_GATED_INPUT_AND_CONTACT_SENSOR_REMEDIATION_OR_HOLD`。
D0 result は 21/861 records すべて `execution_status=ERROR` のため判定不能。
missing precondition cache は non-impedance 6 arms の 18 records を占め、
required path は
`thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w41_p0_v2.npz`。
既存 cache は w4/w32/w200/w256 のみ。contact-sensor config は impedance arm
3 records を占め、runner が `d0_contact_telemetry_enabled=True` を有効化する
一方で `d0_contact_sensor_prim_path` を渡していない。次は 0GPU
precondition-cache readiness review plus D0 contact-sensor config remediation
review、または HOLD。retry/cache build/contact-sensor patch/GPU/simulator/
source/task_config/runner/runtime/dependency mutation/product scoring/D1-D3
routing は未承認。
**2026-05-25 D0 cache/contact remediation-review addendum:** real `%4` は
`eval_runs/r2a_track_a_d0_cache_contact_remediation_review_0gpu_20260525/`
で bounded 0GPU/read-only remediation review を完了。status は
`R2A_TRACK_A_D0_CACHE_CONTACT_REMEDIATION_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`RECOMMEND_SEPARATE_GATED_W41_CACHE_AND_CONTACT_CONFIG_REMEDIATION_BEFORE_ANY_D0_RERUN_NOT_AUTHORIZED`。
future w41 cache creation は separate cuda:0-only gate が必要で、
`build_aerial_regrasp_precondition.py` の default/documented path は cuda:1
前提を含むため forbidden cuda:1 を使えない。contact remediation は独立に
review 可能だが、future D0 rerun は both blockers を close するか、
arm/sample plan を明示的に re-scope する必要がある。existing w32/w256 cache
への切替は 41-world reviewed sample plan と expected count を変えるため
drop-in ではない。次は
`R2A_TRACK_A_D0_CACHE_CONTACT_REMEDIATION_PREFLIGHT_0GPU_NOT_AUTHORIZED`、
または HOLD。retry/cache build/contact-sensor patch/GPU/simulator/
source/task_config/runner/runtime/dependency mutation/product scoring/D1-D3
routing は未承認。
**2026-05-25 D0 cache/contact remediation-preflight addendum:** real `%4` は
`eval_runs/r2a_track_a_d0_cache_contact_remediation_preflight_0gpu_20260525/`
で bounded 0GPU/read-only preflight package を完了。status は
`R2A_TRACK_A_D0_CACHE_CONTACT_REMEDIATION_PREFLIGHT_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`READY_FOR_SEPARATE_CACHE_BUILD_AND_CONTACT_CONFIG_TIER_GATES_NOT_AUTHORIZED`。
preflight は prior review を exact future gate boundaries に変換しただけで、
implementation/execution は未承認。future gate candidate は cuda:0-only w41
cache build、D0 contact-sensor config remediation package、または HOLD。
future D0 rerun は reviewed w41 cache と contact config closure、または
impedance arm/sample plan の明示 re-scope、combined exact command review を
必要とする。sim2real product predicate は維持され、kinematic support、
`inv_mass=0`、direct sim-state writes、active-at-completion product success、
hold-to-completion-only success は除外。retry/cache build/write/
contact-sensor patch/GPU/simulator/source/task_config/runner/runtime/
dependency mutation/product scoring/D1-D3 routing は未承認。
**2026-05-25 D0 contact-sensor config package addendum:** real `%4` は
bounded 0GPU/read-only contact-sensor package を
`eval_runs/r2a_track_a_d0_contact_sensor_config_package_0gpu_20260525/` で完了。
relay `%7` は delayed pane response 後に同一 artifacts を verify。status は
`R2A_TRACK_A_D0_CONTACT_SENSOR_CONFIG_REMEDIATION_PACKAGE_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`RUNNER_CONFIG_SURFACE_SUFFICIENT_BUT_PRIM_FILTER_UNKNOWN_REQUIRES_SEPARATE_STATIC_OR_MICRO_SIM_PRIMPATH_GATE_NOT_AUTHORIZED`。
既存 env/runner config surface は ContactSensor を渡す構造としては十分だが、
runtime prim path と shape/filter expression は static 0GPU evidence では不明。
guess は sim2real/product predicate と no-repeat discipline に反するため禁止。
次は
`R2A_TRACK_A_D0_CONTACT_SENSOR_CANDIDATE_PRIMPATH_GATE_NOT_AUTHORIZED`、
`R2A_TRACK_A_D0_CONTACT_SENSOR_RUNNER_CONFIG_REPAIR_NOT_AUTHORIZED`、
`R2A_TRACK_A_D0_IMPEDANCE_ARM_HOLD_SAMPLE_PLAN_REVIEW_NOT_AUTHORIZED`、または
HOLD。別途 w41 cache build gate は未解決。retry/cache build/write/
contact-sensor patch/GPU/simulator/source/task_config/runner/runtime/
dependency mutation/product scoring/D1-D3 routing は未承認。
**2026-05-25 D0 candidate primpath gate addendum:** real `%4` は
bounded 0GPU/static-only candidate primpath gate を
`eval_runs/r2a_track_a_d0_contact_sensor_candidate_primpath_gate_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_CONTACT_SENSOR_CANDIDATE_PRIMPATH_GATE_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`STATIC_EVIDENCE_INSUFFICIENT_REQUIRES_MICRO_SIM_PRIMPATH_DISCOVERY_GATE_NOT_AUTHORIZED`。
`assets_cfg.py` には candidate-looking path pattern があるが、D0 env path の
actual Newton runtime body/shape/filter 名の証拠ではない。env/routing utils/
NewtonManager/ContactSensor source の static read でも exact string は確定
できないため、`d0_contact_sensor_prim_path` と shape/filter expression の
guess は禁止。次は separate Tier-A micro-sim primpath discovery gate、または
impedance-arm hold/sample-plan review。別途 w41 cache build gate は未解決。
retry/cache build/write/contact-sensor patch/GPU/simulator/source/task_config/
runner/runtime/dependency mutation/product scoring/D1-D3 routing は未承認。
**2026-05-25 D0 micro-sim primpath preflight addendum:** real `%4` は
bounded 0GPU/no-run micro-sim primpath discovery preflight を
`eval_runs/r2a_track_a_d0_contact_sensor_micro_sim_primpath_discovery_preflight_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_CONTACT_SENSOR_MICROSIM_PRIMPATH_PREFLIGHT_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`MICROSIM_PRIMPATH_PREFLIGHT_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`。
future discovery は runtime label inventory と ContactSensor initialization
evidence だけを目的にし、D0 scoring/cache build/product routing は禁止。main
Tier-A risk は、normal env construction が contact telemetry init 後に cache
restoration へ進むため、future script が pre-cache/no-D0 isolation を証明
できなければ HOLD または impedance-arm sample-plan review に送る点。micro-sim
launch/GPU/CUDA/simulator/env instantiation/D0 retry/cache build/write/source
mutation/product scoring/D1-D3 routing は未承認。

**2026-05-25 D0 micro-sim Tier-A review addendum:** supervisor `%3` は上記
preflight の Tier-A review を
`T_ROOT_OPS_SUP_R2A_D0_CONTACT_MICROSIM_PRIMPATH_PREFLIGHT_TIERA_REVIEW_20260525:
INCOMPLETE` と判定。根拠は corrected-root D0 output の 21/861 records が全て
`ERROR` であり、6/7 arms は missing w41 precondition cache、impedance arm
のみが `BLOCKED_CONTACT_SENSOR_INTEGRATION` だったこと。したがって
ContactSensor micro-sim discovery は secondary blocker への対応であり、D0 を
evaluable にする critical path は w41 cache blocker の解決/判断。次は
`R2A_TRACK_A_D0_W41_CACHE_BUILD_EXACT_PREFLIGHT_OR_AUTH_NOT_AUTHORIZED`、
`R2A_TRACK_A_D0_IMPEDANCE_ARM_HOLD_SAMPLE_PLAN_REVIEW_NOT_AUTHORIZED`、または
HOLD。ContactSensor micro-sim launch/D0 retry/cache build/write/source mutation
は、別途 gate まで未承認。

**2026-05-25 D0 w41 cache-build exact preflight addendum:** real `%4` は
bounded 0GPU/no-run w41 cache-build exact preflight を
`eval_runs/r2a_track_a_d0_w41_cache_build_exact_preflight_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_W41_CACHE_BUILD_EXACT_PREFLIGHT_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`W41_CACHE_BUILD_PREFLIGHT_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`。
target cache
`thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w41_p0_v2.npz`
は absent、existing caches は w4/w32/w200/w256。future command draft は
`NOT_AUTHORIZED_DO_NOT_RUN`、cuda:0-only、builder default cuda:1 risk を明示。
次は exact cache-build command の supervisor Tier-A review、impedance-arm
hold/sample-plan review、または HOLD。cache build/write/GPU/CUDA/sim/env
launch/D0 retry は未承認。

**2026-05-25 D0 w41 cache-build one-attempt addendum:** supervisor `%3` の
Tier-A COMPLETE 後、real `%4` は exact cuda:0-only command を 1 回だけ実行し、
`R2A_TRACK_A_D0_W41_CACHE_BUILD_ONE_ATTEMPT_COMPLETE / PRODUCT_GO_FALSE` で完了。
command は exit_code=0、timeout=false、elapsed_seconds=303。
`thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w41_p0_v2.npz`
が生成され、SHA は
`05e3d417ddbff4a5bf59fa55e467a30ee31c4a7a73cefaa5455f8dc4a9d700fa`、
size 65725、NPZ parse PASS、`world_count=41`、`body_count=2378`、expected
keys present。protected SHA/diff clean、post-run GPU query empty、cuda:1 unused。
ContactSensor blocker は impedance arm で未解決。D0 retry/product scoring/
ContactSensor remediation/source mutation は未承認。

**2026-05-25 D0 impedance-arm sample-plan review addendum:** real `%4` は
bounded 0GPU/no-run decision package を
`eval_runs/r2a_track_a_d0_impedance_arm_sample_plan_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_IMPEDANCE_ARM_SAMPLE_PLAN_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`HOLD_DROP_IMPEDANCE_ARM_AND_PREPARE_6_ARM_D0_AUTH_REVIEW_NOT_AUTHORIZED`。
ContactSensor prim/filter evidence が未解決の
`impedance_handoff_contact_force_limited` は immediate path から hold/drop し、
future 6-arm D0 auth review を準備する。対象 arm は `source_default`、
`oracle_pose_or_force_hold`、`release_ramp_5`、`release_ramp_10`、
`support_removal_ablation`、`hold_to_completion_comparator`。expected count は
41 worlds x 3 seeds x 1 episode x 6 arms = 738 records。これは product claim
ではなく、impedance handoff / ContactSensor validity / D1-D3 routing は答えない。
次は `R2A_TRACK_A_D0_6_ARM_AUTH_REVIEW_0GPU_NOT_AUTHORIZED`、または HOLD。
D0 retry/GPU/CUDA/simulator/env launch/ContactSensor patch/source mutation は
別 gate まで未承認。

**2026-05-25 D0 six-arm auth review addendum:** real `%4` は bounded
0GPU/no-run six-arm authorization review を
`eval_runs/r2a_track_a_d0_6_arm_auth_review_0gpu_20260525/` で完了。status は
`R2A_TRACK_A_D0_6_ARM_AUTH_REVIEW_0GPU_COMPLETE / PRODUCT_GO_FALSE`。decision は
`D0_6_ARM_AUTH_REVIEW_BLOCKED_FRESH_PREDICATE_ATTESTATION_OR_ROOT_BINDING_REVIEW_REQUIRED_NOT_AUTHORIZED`。
six-arm shape は coherent だが、existing predicate attestation は既に
21-record error run が入った authguardfix root に bind されているため command は
packageable ではない。fresh six-arm root は `wrong_target_output_root`、old root は
`output_root_already_exists` で fail する。次は
`R2A_TRACK_A_D0_6_ARM_PREDICATE_ATTESTATION_ROOT_BINDING_REVIEW_0GPU_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/source mutation/product scoring は
未承認。

**2026-05-25 D0 predicate root-binding review addendum:** real `%4` は
bounded 0GPU/no-run predicate root-binding review を
`eval_runs/r2a_track_a_d0_6_arm_predicate_root_binding_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_6_ARM_PREDICATE_ROOT_BINDING_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_6_ARM_PREDICATE_ROOT_BINDING_REVIEW_COMPLETE_READY_FOR_6_ARM_AUTH_REVIEW_NOT_AUTHORIZED`。
fresh diagnostic-only predicate attestation
`human_rs_predicate_attestation_for_d0_6_arm.json` を作成し、SHA は
`cfc1b19a463b76dcaa5df43df22af811ae54a9b5d3ed8e918f55fdf2bce6c524`。
canonical predicate text SHA
`861994173a28cb7701a9b1a87b46b68ba9c60a77bf3f62abb0a4e8338a540433` を保持し、
fresh future output root
`eval_runs/r2a_track_a_d0_6_arm_gpu_diagnostic_20260525` に bind した。
target expected count は 738、product scoring / strategic routing / product
GO / physical grasp claim は false。future output root は absent。次は
`R2A_TRACK_A_D0_6_ARM_AUTH_REVIEW_AFTER_ROOT_BINDING_0GPU_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/source mutation/product scoring は
未承認。

**2026-05-25 D0 auth review after root-binding addendum:** real `%4` は
bounded 0GPU/no-run six-arm authorization review after root-binding を
`eval_runs/r2a_track_a_d0_6_arm_auth_review_after_root_binding_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_6_ARM_AUTH_REVIEW_AFTER_ROOT_BINDING_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_6_ARM_AUTH_REVIEW_AFTER_ROOT_BINDING_COMPLETE_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`。
exact future six-arm command は supervisor `%3` Tier-A review 向けには
packageable。command draft は `NOT_AUTHORIZED_DO_NOT_RUN`、cuda:0-only、
new attestation SHA
`cfc1b19a463b76dcaa5df43df22af811ae54a9b5d3ed8e918f55fdf2bce6c524` と
fresh output root `eval_runs/r2a_track_a_d0_6_arm_gpu_diagnostic_20260525`
に bind。future output root は absent、result/status output は未作成。
次は `R2A_TRACK_A_D0_6_ARM_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`、または
HOLD。D0 retry/GPU/CUDA/simulator/env launch/source mutation/product scoring は
未承認。

**2026-05-25 D0 six-arm supervisor Tier-A incomplete addendum:** supervisor
`%3` は six-arm authorization package を review し、launch clearance 前の
blocking runner contract mismatch を検出。direct-import runner は
`for arm` / `for seed` / `for episode` で completion record を append し、
`log_per_world_row(log_by_key, 0)` により world 0 のみを読む。relay は
runner lines 528-546 で確認。prior corrected-root run も 21 records =
7 arms x 3 seeds x 1 episode であり、861 ではなかった。従って current
six-arm command は最大 18 world-0 records で、package の
`expected_completion_count=738` 前提は成立しない。current state は
`R2A_TRACK_A_D0_6_ARM_SUPERVISOR_TIERA_REVIEW_INCOMPLETE / PRODUCT_GO_FALSE`。
次は
`R2A_TRACK_A_D0_6_ARM_RUNNER_WORLD_COUNT_CONTRACT_REVIEW_0GPU_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/source mutation/product scoring は
未承認。

**2026-05-25 D0 runner world-count contract review addendum:** real `%4` は
bounded 0GPU/no-run contract review を
`eval_runs/r2a_track_a_d0_6_arm_runner_world_count_contract_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_6_ARM_RUNNER_WORLD_COUNT_CONTRACT_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`、decision は
`OPTION_A_RUNNER_CONTRACT_IMPLEMENTATION_REVIEW_REQUIRED_NOT_AUTHORIZED`。
review は current runner の expected-count formula が `world_count` を使う一方、
emission path は arm/seed/episode のみを loop して world 0 の record だけを
emit することを確認した。six-arm command は最大 18 records しか emit できず、
claimed 738 records は成立しない。Option A が選択され、future runner
contract/implementation package は one completion record per world、
`world_index`、per-world execution/release/retention/no-crutch fields、
aggregate coverage、world-0 hardcoding static checks を必須とする。18-record
world-0-only への re-scope は D0 には不足として reject。次は
`R2A_TRACK_A_D0_6_ARM_RUNNER_PER_WORLD_CONTRACT_IMPLEMENTATION_0GPU_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/source mutation/product
scoring/product claim/physical-grasp claim/T-ROOT 95 claim は未承認。

**2026-05-25 D0 per-world runner implementation addendum:** real `%4` は
bounded 0GPU/no-run eval_runs-local implementation package を
`eval_runs/r2a_track_a_d0_6_arm_runner_per_world_contract_impl_0gpu_20260525/`
で作成。status は
`R2A_TRACK_A_D0_6_ARM_RUNNER_PER_WORLD_CONTRACT_IMPLEMENTATION_0GPU_COMPLETE /
PRODUCT_GO_FALSE`、decision は
`PER_WORLD_RUNNER_CONTRACT_IMPLEMENTED_READY_FOR_FRESH_0GPU_AUTH_REVIEW_NOT_AUTHORIZED`。
new runner SHA は
`5057ea4f7cc7ea8b6969bb1907b87d9c2a6c1831a7bb348e60d42493ebe371d0`。
future runner は one completion record per `(arm, seed, episode, world_index)`、
expected count 738、`world_index`/`world_count`/`run_tuple_id`、per-world
execution/release/retention/no-crutch fields、aggregate coverage、
world-0 hardcoding static checks を実装した。runner SHA が変わったため existing
six-arm auth/root-binding package は launch authorization として無効。次は
`R2A_TRACK_A_D0_6_ARM_AUTH_REVIEW_FOR_PER_WORLD_RUNNER_0GPU_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/protected source mutation/
product scoring/product claim/physical-grasp claim/T-ROOT 95 claim は未承認。

**2026-05-25 D0 per-world auth/root-binding review addendum:** real `%4` は
bounded 0GPU/no-run auth/root-binding review を
`eval_runs/r2a_track_a_d0_6_arm_auth_review_for_per_world_runner_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_6_ARM_AUTH_REVIEW_FOR_PER_WORLD_RUNNER_0GPU_COMPLETE /
PRODUCT_GO_FALSE`、decision は
`D0_6_ARM_PER_WORLD_AUTH_REVIEW_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`。
fresh diagnostic-only root-binding artifact
`human_rs_predicate_attestation_for_d0_6_arm_per_world.json` SHA は
`37016545f3a21aa31139c6d61b5d2d69b0857d74a3dca64da26d80718c6b3af0`。
runner SHA `5057ea4f7cc7ea8b6969bb1907b87d9c2a6c1831a7bb348e60d42493ebe371d0`、
future root `eval_runs/r2a_track_a_d0_6_arm_per_world_gpu_diagnostic_20260525`、
expected count 738、six selected arms に bind。future root は absent、static
preflight は PASS。次は
`SUPERVISOR_TIERA_REVIEW_FOR_EXACT_SIX_ARM_PER_WORLD_DIAGNOSTIC_GPU_COMMAND_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/protected source mutation/
product scoring/product claim/physical-grasp claim/T-ROOT 95 claim は未承認。

**2026-05-25 D0 per-world GPU diagnostic completion addendum:** supervisor
`%3` の Tier-A `VERDICT: COMPLETE` 後、real `%4` は exactly one
diagnostic-only cuda:0 command を
`eval_runs/r2a_track_a_d0_6_arm_per_world_gpu_diagnostic_20260525/` で実行した。
status は
`R2A_TRACK_A_D0_6_ARM_PER_WORLD_GPU_DIAGNOSTIC_ONE_ATTEMPT_COMPLETE /
PRODUCT_GO_FALSE`。shell exit code 0、timeout false、retry count 0、runner
elapsed 1266.109s。expected/actual completion records は 738/738、全 record
`COMPLETE`、各 six selected arm は 123 records、world indices 0..40 を covered。
ただし全 arm で `actual_release_count=0`、`post_release_retained_30_count=0`、
`product_success_count=0`。coverage は pass したが schema guard は
`missing_schema_count=738` で failed（D0 control/contact telemetry keys 欠落）。
これは product evidence ではなく、D1/D2/D3 routing evidence でもない。次は
zero-release result と schema guard failure の bounded 0GPU artifact-only
review、または HOLD。D0 retry/follow-on GPU launch/ContactSensor patch/
source-task_config-runner-runtime-cache mutation/product scoring/product claim/
physical-grasp claim/T-ROOT 95 claim は未承認。

**2026-05-25 D0 zero-release/schema review addendum:** real `%4` は bounded
0GPU artifact-only review を
`eval_runs/r2a_track_a_d0_per_world_zero_release_schema_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_PER_WORLD_ZERO_RELEASE_SCHEMA_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_RESULT_NON_EVALUABLE_FOR_RELEASE_TRANSIENT_DISCRIMINATOR_ZERO_ACTUAL_RELEASE_AND_SCHEMA_GUARD_FAIL_RECOMMEND_0GPU_RUNNER_RELEASE_SCHEMA_REVIEW_NOT_AUTHORIZED`。
738/738 COMPLETE と world coverage は成立したが、actual release が 0 のため
release-transient/oracle-retention discriminator には非評価。zero-release は
`RUNNER_RELEASE_TRIGGER_NEVER_FIRED` と分類された。runner は
`right_clamp && cable_not_dropped` sustained を actual release として扱う一方、
env D0 force-ramp/scheduled release-step behavior は `actual_release_occurred`
として記録されていない。schema guard failure は optional D0 contact telemetry
keys を impedance/contact arm dropped 後も global required にした runner
schema-contract gap。これは product scoring と D0 diagnostic interpretation の
双方を invalidates。次は
`BOUNDED_0GPU_RUNNER_RELEASE_TRIGGER_AND_SCHEMA_REVIEW_OR_PATCH_PROPOSAL_NOT_AUTHORIZED`、
または HOLD。D0 retry/follow-on GPU launch/command repair/ContactSensor patch/
source-task_config-runner-runtime-cache mutation/product scoring/product claim/
physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 runner release/schema contract proposal addendum:** real `%4`
は bounded 0GPU/no-run/no-mutation contract proposal を
`eval_runs/r2a_track_a_d0_runner_release_schema_contract_proposal_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_RUNNER_RELEASE_SCHEMA_CONTRACT_PROPOSAL_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`RUNNER_RELEASE_SCHEMA_CONTRACT_DELTA_PROPOSED_NOT_AUTHORIZED`。proposal は
terminal-predicate release、scheduled D0 force-ramp/support-removal event、
no release attempted、release predicate never reached を明示的な release
evidence class として分離し、contact telemetry を contact/impedance arm のみ
required とする arm-specific schema contract を提案した。`source_default` は
D0 control disabled / no release attempted を明示し、D0 control arms は selected
arm、configured release step、force scale/min/final、target blend、scheduled
release event、terminal predicate trace、retention、product authorization、
no-crutch provenance を残す必要がある。次は
`BOUNDED_0GPU_RUNNER_RELEASE_SCHEMA_CONTRACT_IMPLEMENTATION_PACKAGE_NOT_AUTHORIZED`、
または HOLD。implementation/D0 retry/GPU launch/product scoring/strategic
routing/product claim/physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 runner release/schema contract implementation addendum:** real
`%4` は bounded 0GPU/no-run/no-sim eval_runs-local runner package を
`eval_runs/r2a_track_a_d0_runner_release_schema_contract_impl_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_6_ARM_RUNNER_RELEASE_SCHEMA_CONTRACT_IMPLEMENTATION_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`RUNNER_RELEASE_SCHEMA_CONTRACT_IMPLEMENTED_READY_FOR_ROOT_BINDING_AUTH_REVIEW_NOT_AUTHORIZED`。
new runner SHA は
`54db6ef378e886f23717ae14696d7f17bfa36080013be8596f96341400d298ba` で、
old per-world runner SHA `5057ea4f...` と prior auth/root-binding packages を
invalidates。release evidence classes、arm-specific schema、non-contact
nullable contact telemetry、source_default no-release contract、product-success
fail-closed、no-crutch guards を実装済み。次は
`BOUNDED_0GPU_ROOT_BINDING_AUTH_REVIEW_FOR_RELEASE_SCHEMA_RUNNER_NOT_AUTHORIZED`、
または HOLD。future GPU diagnostic/product scoring/strategic routing/product
claim/physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 release/schema runner root-binding auth review addendum:** real
`%4` は bounded 0GPU/no-run/no-launch review を
`eval_runs/r2a_track_a_d0_release_schema_runner_root_binding_auth_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_RELEASE_SCHEMA_RUNNER_ROOT_BINDING_AUTH_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_RELEASE_SCHEMA_RUNNER_AUTH_REVIEW_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`。
fresh predicate/root-binding artifact SHA
`8e679ef86e4c2f5a5ad4d30b597fa73553ac173f72fb699be2f0ab77f80decd9` は runner SHA
`54db6ef3...`、future output root
`eval_runs/r2a_track_a_d0_release_schema_runner_gpu_diagnostic_20260525`、
expected count 738、six target arms、protected SHAs、w41 cache SHA、diagnostic-only
sim2real predicate を bind する。future command draft は cuda:0-only かつ
`NOT_AUTHORIZED_DO_NOT_RUN`。次は
`SUPERVISOR_TIERA_REVIEW_FOR_RELEASE_SCHEMA_D0_GPU_DIAGNOSTIC_NOT_AUTHORIZED`、
または HOLD。future GPU diagnostic/product scoring/strategic routing/product
claim/physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 release/schema diagnostic authorization addendum:** supervisor
`%3` は上記 release/schema runner package について Tier-A `VERDICT:
COMPLETE` を `2026-05-25 21:16:12 JST` に返し、`%7` は real `%4` へ exactly
one diagnostic-only cuda:0 D0 release/schema attempt を authorization dispatch
済み。`%4` は `ACK_R2A_D0_RELEASE_SCHEMA_GPU_AUTH_RECEIVED_20260525` を返し、
state update 時点で visibly `Working`。これは completion claim ではなく、
timestamped authorization/working observation。run は runner SHA
`54db6ef3...`、attestation SHA `8e679ef8...`、output root
`eval_runs/r2a_track_a_d0_release_schema_runner_gpu_diagnostic_20260525`、
expected count 738、six arms、protected SHAs、w41 cache SHA、diagnostic-only
sim2real predicate に bound。no retry、no cuda:1、no source/task_config/runner/
runtime/cache mutation、no ContactSensor patch、no product scoring、no D1/D2/D3
routing、no product/physical-grasp/T-ROOT 95 claim。
**2026-05-25 D0 release/schema diagnostic completion addendum:** real `%4` は
exact one-attempt diagnostic-only cuda:0 run を
`eval_runs/r2a_track_a_d0_release_schema_runner_gpu_diagnostic_20260525/` で
完了。status は
`R2A_TRACK_A_D0_RELEASE_SCHEMA_GPU_DIAGNOSTIC_ONE_ATTEMPT_COMPLETE /
PRODUCT_GO_FALSE`。738/738 complete、coverage/schema guard PASS、execution
status COMPLETE=738。release class は `no_release_attempted=246`、
`release_predicate_never_reached=441`、`scheduled_d0_release_event_applied=51`。
terminal predicate release は 0、scheduled release events は 51、retained-30 は
23、product_success は 0、record schema valid は 738。per-arm retained-30 は
oracle=7、ramp5=4、ramp10=5、support_removal_ablation=7、source_default=0、
hold_to_completion=0。no arm reached terminal-predicate release。protected SHA
locks/diff empty/post-run GPU empty/cuda:1 unused。next は bounded 0GPU artifact
review before strategic interpretation、または HOLD。
**2026-05-25 D0 release/schema diagnostic artifact review addendum:** real
`%4` は bounded 0GPU artifact-only review を
`eval_runs/r2a_track_a_d0_release_schema_artifact_review_0gpu_20260525/` で
完了。status は
`R2A_TRACK_A_D0_RELEASE_SCHEMA_DIAGNOSTIC_ARTIFACT_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_RELEASE_SCHEMA_DIAGNOSTIC_PARTIAL_EVIDENCE_UNDERPOWERED_FOR_STRATEGIC_ROUTING_RECOMMEND_0GPU_SAMPLE_POWER_RELEASE_YIELD_REVIEW_OR_HOLD_NOT_AUTHORIZED`。
738/738、coverage/schema PASS、release classes は no_release_attempted=246、
predicate_never_reached=441、scheduled_release=51、retained-30=23/51、
product_success=0。actual scheduled release yield 51 が configured min 60 未満
なので、D1/D2/D3 strategic routing には underpowered。next は 0GPU
sample-power/release-yield review、または HOLD。no retry/no GPU/no mutation/no
product claim/cuda:1 unused。
**2026-05-25 D0 sample-power release-yield review addendum:** real `%4` は
bounded 0GPU/no-run review/package を
`eval_runs/r2a_track_a_d0_sample_power_release_yield_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_SAMPLE_POWER_RELEASE_YIELD_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`ACTUAL_RELEASE_YIELD_GATE_DEFINED_CURRENT_RESULT_UNDERPOWERED_RECOMMEND_RUNNER_CONTRACT_AMENDMENT_OR_HOLD_NOT_AUTHORIZED`。
separate gates として completion coverage、schema guard、configured
release-yield、actual release-yield、retention evaluability、product scoring、
strategic routing を定義した。current result は completion/schema を pass するが、
actual release-yield は 51 scheduled release events vs configured minimum 60 で
fail。terminal predicate releases は 0、retained-after-release は 23。従って現
result は scheduled release が起きたこと、23/51 が30step保持したこと、
terminal predicate が一度も fired しなかったこと、source_default /
hold_to_completion が no-release non-product strata であることまでの
descriptive evidence に限られる。product success、D1/D2/D3 strategic routing、
physical grasp、T-ROOT 95、sim2real product commitment は支持しない。次は
`BOUNDED_0GPU_RUNNER_SAMPLE_POWER_STATUS_CONTRACT_AMENDMENT_PROPOSAL_NOT_AUTHORIZED`、
または HOLD。D0 retry/GPU/CUDA/simulator/env launch/source-task_config-runner-
runtime-cache mutation/ContactSensor patch/product scoring/strategic routing/
product claim/physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 runner sample-power/status contract amendment proposal
addendum:** real `%4` は bounded 0GPU/no-run/no-launch/no-mutation proposal を
`eval_runs/r2a_track_a_d0_runner_sample_power_status_contract_amendment_proposal_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_RUNNER_SAMPLE_POWER_STATUS_CONTRACT_AMENDMENT_PROPOSAL_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`RUNNER_SAMPLE_POWER_STATUS_CONTRACT_AMENDMENT_PROPOSED_READY_FOR_BOUNDED_0GPU_IMPLEMENTATION_OR_HOLD_NOT_AUTHORIZED`。
proposal は configured-yield gate と actual-yield gate を分離し、current
diagnostic では 738/738 completion と schema PASS でも actual release yield が
51 < configured minimum 60 のため `sample_power_guard_passed=false` になると
定義した。future status/summary/per-record outputs は configured expected/min
release-yield、actual scheduled/terminal/total release counts、retained-after-
release count/denominator、product-success count、coverage/schema/configured-
yield/actual-yield/retention-evaluability gates、sample-power no-go reasons、
authorization flags、CUDA provenance、no-crutch provenance を永続化する必要が
ある。`source_default` は no-D0-control baseline、`hold_to_completion_comparator`
は comparator-only で、どちらも product success 不可。次は
`BOUNDED_0GPU_RUNNER_SAMPLE_POWER_STATUS_CONTRACT_IMPLEMENTATION_PACKAGE_NOT_AUTHORIZED_OR_HOLD`。
D0 retry/GPU/CUDA/simulator/env launch/source-task_config-runner-runtime-cache
mutation/ContactSensor patch/product scoring/strategic routing/product claim/
physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 runner sample-power/status contract implementation
addendum:** real `%4` は bounded 0GPU/no-run/no-launch eval-runs-local runner
implementation を
`eval_runs/r2a_track_a_d0_runner_sample_power_status_contract_impl_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_RUNNER_SAMPLE_POWER_STATUS_CONTRACT_IMPLEMENTATION_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`RUNNER_SAMPLE_POWER_STATUS_CONTRACT_IMPLEMENTED_READY_FOR_ROOT_BINDING_AUTH_REVIEW_OR_HOLD_NOT_AUTHORIZED`。
new runner `run_gapb_functional_d0_runner_sample_power_status.py` SHA は
`838b8e73b4100d1ebe2aa97e5f0dc709e31382ff5e361ec84dcc55f6733de0e7`。
configured-yield と actual-yield を persisted gates として分離し、
`sample_power_guard_passed` は coverage/schema/configured-yield/actual-yield/
retention-evaluability gates 全てを要求する。synthetic validation は 51 < 60
で `actual_yield_gate_passed=false`、`sample_power_guard_passed=false`、
`actual_release_yield_below_minimum` を確認。new runner SHA により prior
auth/root-binding/launch packages は無効化。次は
`BOUNDED_0GPU_ROOT_BINDING_AUTH_REVIEW_FOR_SAMPLE_POWER_STATUS_RUNNER_NOT_AUTHORIZED_OR_HOLD`。
D0 retry/GPU/CUDA/simulator/env launch/protected source/task_config/runtime/
cache/dependency mutation/ContactSensor patch/product scoring/strategic
routing/product claim/physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 sample-power/status runner root-binding auth review
addendum:** real `%4` は bounded 0GPU/no-run/no-launch root-binding/auth review
を
`eval_runs/r2a_track_a_d0_sample_power_status_runner_root_binding_auth_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_SAMPLE_POWER_STATUS_RUNNER_ROOT_BINDING_AUTH_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_SAMPLE_POWER_STATUS_RUNNER_AUTH_REVIEW_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`。
runner SHA `838b8e73...`、implementation summary SHA `c3ca763...`、fresh
attestation SHA `3cee37e...`、future output root
`eval_runs/r2a_track_a_d0_sample_power_status_runner_gpu_diagnostic_20260525`
absent、protected SHAs、w41 cache SHA、six selected arms、expected count 738 を
bind。future command draft は `NOT_AUTHORIZED_DO_NOT_RUN`、cuda:0-only、
cuda:1 absent。old auth/root-binding/launch packages は old runner SHA
`54db6ef3...` または older roots に bind しているため無効。次は
`SUPERVISOR_TIERA_REVIEW_FOR_SAMPLE_POWER_STATUS_D0_GPU_DIAGNOSTIC_NOT_AUTHORIZED_OR_HOLD`。
D0 run/GPU/CUDA/simulator/env launch/source-task_config-runner-runtime-cache
mutation/ContactSensor patch/product scoring/strategic routing/product claim/
physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-25 D0 sample-power/status GPU diagnostic addendum:** real `%4` は
exactly one bounded cuda:0 diagnostic を
`eval_runs/r2a_track_a_d0_sample_power_status_runner_gpu_diagnostic_20260525/`
で実行完了。status は
`R2A_TRACK_A_D0_SAMPLE_POWER_STATUS_GPU_DIAGNOSTIC_ONE_ATTEMPT_COMPLETE /
PRODUCT_GO_FALSE`。exact command は exit 0、`1073.977s`、738/738 COMPLETE。
coverage/schema は PASS、configured-yield は PASS (`80 >= 60`) だが、
actual-yield は FAIL (`46 < 60`; scheduled D0 45 + terminal predicate 1)。
したがって `sample_power_guard_passed=false`、no-go reason は
`actual_release_yield_below_minimum`。retained-after-release は `24/46`、
product success は `0`、`product_go=false`、
`product_scoring_authorized=false`、`strategic_routing_authorized=false`。
per-arm release/retention は source_default 1 terminal/0 retained、
oracle 8 scheduled/5 retained、ramp5 15/7、ramp10 11/6、
support_removal_ablation 11/6、hold_to_completion_comparator 0 release。
device は `cuda:0`、`CUDA_VISIBLE_DEVICES=0`、cuda:1 unused。protected SHAs
locked、protected diff empty、post-run GPU empty。次は
`BOUNDED_0GPU_SAMPLE_POWER_STATUS_DIAGNOSTIC_ARTIFACT_REVIEW_NOT_AUTHORIZED_OR_HOLD`。
retry/follow-on GPU launch/mutation/ContactSensor patch/product scoring/
strategic routing/product claim/physical-grasp claim/T-ROOT 95 claim は未承認。
**2026-05-26 D0 sample-power/status diagnostic artifact review addendum:**
real `%4` は bounded 0GPU artifact-only review を
`eval_runs/r2a_track_a_d0_sample_power_status_diagnostic_artifact_review_0gpu_20260525/`
で完了。status は
`R2A_TRACK_A_D0_SAMPLE_POWER_STATUS_DIAGNOSTIC_ARTIFACT_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`D0_SAMPLE_POWER_STATUS_DIAGNOSTIC_DESCRIPTIVE_ONLY_UNDERPOWERED_FOR_STRATEGIC_ROUTING_HOLD_OR_NEW_0GPU_DELTA_NOT_AUTHORIZED`。
review は completed GPU diagnostic を mechanically clean だが descriptive-only
and underpowered と分類。738/738 complete、coverage/schema PASS、
configured-yield PASS (`80 >= 60`)、actual-yield FAIL (`46 < 60`)、
`sample_power_guard_passed=false`、no-go reason
`actual_release_yield_below_minimum`、retained-after-release `24/46`、
product success `0`。product scoring/strategic routing/product GO/
physical-grasp/T-ROOT 95 は全て false。artifact SHAs は report
`f2cfaacba53133dfd752037ee0a06b0b3c1b294966b270633047842739df4d82`、
summary `4d66610da3c89df103a2f06731ba7b7edae98dfb155a529dd3ebc2bb329f3f9f`、
guard `9e3054d67acd12e6bc5022bbd9f63ee23f4bbc2a8ba6b8f9adf2fb7adb45ac3b`、
SHA256SUMS `f05adb60fcdcbf5b18fe57a06c5b2a74d377043d6d24c391e73ec685bdb180f1`。
次は
`HOLD_STRATEGIC_ROUTING_AFTER_UNDERPOWERED_D0_SAMPLE_POWER_STATUS_DIAGNOSTIC_OR_BOUNDED_0GPU_RELEASE_YIELD_DELTA_REVIEW_NOT_AUTHORIZED`。
この artifact 単独から follow-on GPU run は推奨されない。
**2026-05-26 D0 sample-power/status release-yield delta review addendum:**
real `%4` は bounded 0GPU release-yield delta review を
`eval_runs/r2a_track_a_d0_sample_power_status_release_yield_delta_review_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_D0_SAMPLE_POWER_STATUS_RELEASE_YIELD_DELTA_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`NO_SAFE_RELEASE_YIELD_DELTA_FROM_EXISTING_ARTIFACTS_HOLD_RECOMMENDED_NOT_AUTHORIZED`。
actual release yield は `46 < 60` のまま。release split は scheduled D0 45
+ terminal predicate 1。release class distribution は no-release-attempted 245、
release-predicate-never-reached 447、scheduled 45、terminal 1。four
release-producing arms では scheduled release 到達が `45/492` のみで、
no-release control-arm records は schema/cache/contact failures ではなく
cable_drop/explosion で release 前に終了。yield threshold を下げる、
task-appropriate timing review なしに早期 release する、hold-to-completion/
active-at-completion を数える、sim2real product predicate を弱める、といった
automatic delta は却下。recommended route は
`HOLD_STRATEGIC_ROUTING_AFTER_UNDERPOWERED_D0_SAMPLE_POWER_STATUS_DIAGNOSTIC`。
**2026-05-26 S1 post-release stability policy/data scope addendum:**
real `%4` は bounded 0GPU/read-only S1 successor-scope package を
`eval_runs/r2a_track_a_s1_post_release_stability_policy_data_scope_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_S1_POST_RELEASE_STABILITY_POLICY_DATA_SCOPE_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`S1_POLICY_DATA_SCOPE_COMPLETE_RECOMMEND_0GPU_S1A_REWARD_OBSERVATION_CURRICULUM_DELTA_AUDIT_NOT_AUTHORIZED_OR_HOLD`。
D0 sample-power/status lineage は terminal/HOLD のまま、S1 は sim2real
no-crutch product predicate 下の policy/data/reward/observation/curriculum
successor scope としてのみ整理された。future surfaces は observation terms、
reward terms、release/termination labels、action/control authority、
curriculum/sample-power protocol、dataset/BC/DAPG feasibility、evaluation
metrics。recommended next decision は
`BOUNDED_0GPU_S1A_REWARD_OBSERVATION_CURRICULUM_DELTA_AUDIT_NOT_AUTHORIZED_OR_HOLD`。
GPU/sim/env launch、source/task_config/runner mutation、training、product scoring、
strategic routing、product claim、physical-grasp claim、sim2real-success claim、
T-ROOT 95 claim、cuda:1 use は未承認。
**2026-05-26 S1A implementation-design addendum:** real `%4` は bounded
0GPU/read-only S1A minimal reward/observation/curriculum implementation-design
package を
`eval_runs/r2a_track_a_s1a_minimal_reward_obs_curriculum_impl_design_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_S1A_MINIMAL_REWARD_OBS_CURRICULUM_IMPLEMENTATION_DESIGN_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`S1A_MINIMAL_IMPL_DESIGN_COMPLETE_RECOMMEND_TIERA_SOURCE_MUTATION_REVIEW_PACKAGE_NOT_AUTHORIZED_OR_HOLD`。
required deltas は reward/stability pressure、release-readiness observation
state、curriculum/sample-power schedule。minimal bundle は `task_config.py`
mutation を含まず、default-off / versioned behavior、actual-yield sample
power、retention denominator、cable_drop/explosion labels、no-crutch provenance
を維持する。次 route は
`SUPERVISOR_TIERA_REVIEW_FOR_BOUNDED_S1A_SOURCE_MUTATION_PACKAGE_NOT_AUTHORIZED_OR_HOLD`。
mutation、GPU/sim/env launch、training、product scoring、strategic routing、
product claim、physical-grasp claim、sim2real-success claim、T-ROOT 95 claim、
cuda:1 use は未承認。
**2026-05-26 S1A Tier-A visible-blocker addendum:** `%7` は S1A source
mutation 前に supervisor `%3` を loop-in。`%3` は design bundle を read-only
確認し、formal verdict marker 前に visible blocker を提示した。D0
sample-power/status run は 738/738・coverage PASS で mechanically
interpretable だが、actual_release_events_total `46 < 60`、
`actual_release_yield_below_minimum`、retention `24/46`、product success `0`
で sample-power guard FAILED。さらに SHA-locked env への初の
reward/obs/curriculum mutation であり、mutation authorization は block と
観測された。`%3` は token 節約のため formal marker 前に interrupt。relay は
visible finding を advisory-blocking として扱う。source mutation は HOLD。
新しい 0GPU delta で underpowered-evidence/source-mutation justification gap を
解消するまで、mutation、GPU/sim/env launch、training、product scoring、
strategic routing、product claim、physical-grasp claim、sim2real-success claim、
T-ROOT 95 claim、cuda:1 use は未承認。
**2026-05-26 S1A source-mutation blocker gap-closure addendum:** real `%4` は
bounded 0GPU/no-run gap-closure package を
`eval_runs/r2a_track_a_s1a_source_mutation_blocker_gap_closure_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_S1A_SOURCE_MUTATION_BLOCKER_GAP_CLOSURE_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`HOLD_SOURCE_MUTATION_AFTER_VISIBLE_BLOCKER_WITH_OPTIONAL_0GPU_EVIDENCE_THRESHOLD_TOPUP_DESIGN_NOT_AUTHORIZED`。
blocker は B1 underpowered D0 evidence (`actual_release_events_total=46 < 60`),
B2 first SHA-locked env reward/obs/curriculum mutation, B3 no product/strategic
inference, B4 same-scope D0 rerun no-repeat risk に分解された。mutation review
再開には actual release yield `>=60`、retention denominator alignment、
no-crutch provenance、no-repeat-clean evidence acquisition、default-off/versioned
source contract が必要。optional top-up は design-only candidate で未承認。
mutation、D0 rerun、GPU/sim/env launch、training、product scoring、strategic
routing、product claim、physical-grasp claim、sim2real-success claim、T-ROOT 95
claim、cuda:1 use は未承認。
**2026-05-26 S1A evidence-threshold top-up design addendum:** real `%4` は
bounded 0GPU/no-run evidence-threshold / top-up design package を
`eval_runs/r2a_track_a_s1a_evidence_threshold_topup_design_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_S1A_EVIDENCE_THRESHOLD_TOPUP_DESIGN_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`HOLD_OR_FUTURE_TIERA_REVIEW_FOR_NONMUTATING_S1A_TOPUP_EVIDENCE_ACQUISITION_NOT_AUTHORIZED`。
existing 46 actual releases は old/new roots、protected SHAs、runner/schema、
no-crutch provenance が immutable/comparable の場合のみ累積可能。mathematical
gap は +14 releases だが、conservative reopen threshold は total actual
releases `>=70`、recommended top-up target は +24 valid actual releases。future
candidate shape は design-only で、41 worlds x new seeds `[3, 4]` x 1 episode x
six non-impedance arms = 492 records、`NOT_AUTHORIZED_DO_NOT_RUN`。top-up 実行、
mutation、D0 rerun、GPU/sim/env launch、training、product scoring、strategic
routing、product claim、physical-grasp claim、sim2real-success claim、T-ROOT 95
claim、cuda:1 use は未承認。
**2026-05-26 S1A top-up runner-SHA binding gapfix addendum:** real `%4` は
bounded 0GPU/no-run runner-SHA binding gapfix package を
`eval_runs/r2a_track_a_s1a_topup_runner_sha_binding_gapfix_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_S1A_TOPUP_RUNNER_SHA_BINDING_GAPFIX_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`S1A_TOPUP_RUNNER_SHA_BINDING_GAPFIX_COMPLETE_READY_FOR_SUPERVISOR_TIERA_EXACT_COMMAND_REVIEW_NOT_AUTHORIZED_OR_HOLD`。
%3 の pooling-comparability blocker は、future non-mutating top-up evidence を
existing 46 actual releases と同じ sample-power/status runner SHA
`838b8e73b4100d1ebe2aa97e5f0dc709e31382ff5e361ec84dcc55f6733de0e7`
に bind することで閉じた。prior top-up package は編集せず、この
runner-bound contract が future Tier-A exact-command review 用に supersede
する。future launch は exact cuda:0 command、fresh output root absence、
old diagnostic JSON SHA 不変、protected SHA 不変、runner SHA mismatch abort
を別途 bind しなければならない。top-up 実行、mutation、D0 rerun、
GPU/sim/env launch、training、product scoring、strategic routing、
product claim、physical-grasp claim、sim2real-success claim、T-ROOT 95 claim、
cuda:1 use は未承認。
**2026-05-26 S1A runner-bound top-up exact-command packet addendum:** real
`%4` は bounded 0GPU/no-run exact-command packet を
`eval_runs/r2a_track_a_s1a_topup_runner_bound_exact_command_review_0gpu_20260526/`
で完了。status は
`R2A_TRACK_A_S1A_TOPUP_RUNNER_BOUND_EXACT_COMMAND_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`。decision は
`S1A_TOPUP_RUNNER_BOUND_EXACT_COMMAND_PACKET_COMPLETE_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED_OR_HOLD`。
packet は guarded `NOT_AUTHORIZED_DO_NOT_RUN` command draft のみを emit し、
future output root
`eval_runs/r2a_track_a_s1a_runner_bound_topup_gpu_diagnostic_20260526`、
seeds `[3, 4]`、six non-impedance arms、expected completion count `492`、
top-up min actual-release target `24`、combined reopen rule `46 + top-up
actual releases >= 70`、runner SHA
`838b8e73b4100d1ebe2aa97e5f0dc709e31382ff5e361ec84dcc55f6733de0e7`、
old diagnostic JSON SHA、protected SHA、w41 cache SHA、fresh diagnostic-only
predicate attestation を bind した。future output root は absent のまま。
次は supervisor `%3` Tier-A exact-command review、または HOLD。top-up 実行、
mutation、D0 rerun、GPU/sim/env launch、runner execution、training、
product scoring、strategic routing、product claim、physical-grasp claim、
sim2real-success claim、T-ROOT 95 claim、cuda:1 use は未承認。
C8F で launch-capable real C7V writer output path COMPLETE、C8G で payload
collection auth package review COMPLETE、C8H で executable collect-writer output
path COMPLETE、C8I で payload collection auth package review COMPLETE まで進み、
future valid collect path は `FileWriteInterceptor` なしで定義され、C8H で
valid collect executable boundary まで進むことが確認された。C8I は C8J
launch-decision package を `DRAFT_NOT_AUTHORIZED` としてのみ draftable と判定し、
artifact consistency patch で C8J draft の stale previous-stage output path を除去した。
C8J は fresh scoped directive で 1 回だけ実行され、boundary-ready には到達したが
required payload outputs を生成しなかった。C8K は C8H collect mode が boundary
manifest を print するだけで C7V writer を呼ばず、C8J `boundary_outputs` も
writer output root に bind されていないことを特定した。
C8L は C8J `boundary_outputs` root を actual C7V writer path に write suppression
下で bind し、all five required future output paths を `boundary_outputs/results`
配下で intercept したが、real payload outputs は生成していない。C8M は C8L
proof を artifact-only review し、future C8N draft を `DRAFT_NOT_AUTHORIZED` と
して作成した。C8N は fresh scoped 0GPU command で actual C7V writer path を invoke
し、C8J `boundary_outputs/results` 配下に exactly five authorized files を作成、
42 payload rows / 42 completion records を validate した。
C8O は five C8J result files、42 payload rows、42 completion records、C7N
required fields 22/22 coverage、target-slice identity、protected SHA locks、
forbidden-output absence を artifact-only review し、
`C8O_READY_FOR_C8P_PAYLOAD_DATASET_CONSUMPTION_OR_TRAINING_AUTH_REVIEW_DRAFT_ONLY`
とした。次は C8P payload dataset-consumption/training-auth review 0GPU。
C8P は payload semantics を artifact-only review し、C8J/C8N payload は
structural/provenance-ready only で training-auth not ready と判定した。全 42 rows
は dry-run/proxy-shaped で、actions/rewards は zero、strict-ready /
terminal-candidate labels は false、residual/alignment は zero、timestep は 0 のみ。
次は C8Q payload semantic validation 0GPU draft-only。C8Q は field provenance を
audit し、live observed per-step fields=0、existing-live-derived fields=0、
static-manifest-derived fields=9、constant/default fields=2、dry-run/proxy
placeholders=11 と分類した。既存 artifacts から semantic training payload への
transform は supported ではない。次は C8R live payload collection path design
0GPU draft-only。C8R は design-only で future live capture boundary と 22 field
hook map を定義し、C8S live payload collection scaffold を draft-only next とした。
collection、payload writes、dataset consumption、training、GPU は未承認。C8S は
local eval_runs-only scaffold runner を実装し、22 fields の fail-closed hook map、
refusal-proof、auth-dry-run boundary を 0GPU で検証した。次は C8T live payload
collection auth review 0GPU draft-only。C8T は C8S artifacts を review し、
valid scaffold だが collect auth ready now=false と判定した。次は C8U live
payload collection path/auth package 0GPU draft-only。C8U は no-output path
boundary を定義し、C8V live payload collection launch-or-review 0GPU draft-only
next とした。C8V は review branch のみを実行し、C8U artifact package と
no-output boundary を検証した。次は C8W launch-capable live collection runner
path 0GPU draft-only。C8W は eval_runs-local runner/path package を作成し、
valid-marker auth-dry-run は `LIVE_COLLECTION_RUNNER_PATH_READY_NO_COLLECTION_NO_OUTPUT_WRITES`
のみ到達した。C8X は C8W artifacts を review し、collection-auth ready now=false
と判定した。C8Y は valid-marker collect を
`EXECUTABLE_LIVE_COLLECTION_BOUNDARY_READY_NO_COLLECTION_NO_OUTPUT_WRITES`
へ到達させた。C8Z は C8Y boundary を review し、C9 draft-only package には
sufficient だが live collection launch auth ready now=false と判定した。次は C9
live collection execution path 0GPU draft-only。
C9 は post-boundary preflight handoff と fail-closed guards を定義し、launch
auth/output auth false を維持した。次は C9A live collection execution path auth
review 0GPU draft-only。
C9A は C9 を future launch-decision draft に sufficient と review したが、
launch/output auth は now=false のまま維持した。次は C9B live collection launch
decision draft / fresh scoped directive only。
C9B は no-command `DRAFT_NOT_AUTHORIZED` launch-decision draft を作成した。
実行は未承認で、次は explicitly authorized な fresh scoped C9C-or-later
launch directive/review only。
C9C は 0GPU fresh-scoped launch directive/review package を作成した。
future command は `DO_NOT_RUN / DRAFT_NOT_AUTHORIZED` のままで、C9C 自体は
実行を authorize しない。次は explicitly authorized な fresh scoped C9D-or-later
launch decision/review only。
C9D は relay-side 0GPU launch readiness gap review で、C9C command が C8Y
boundary-only であり real live collection runner ready ではないと判定した。
C9E は real `%4` で 0GPU artifact-only review として完了し、C8S/C8U/C8W/C8Y
が still boundary-only であり、no reviewed artifact が real live collection
runner launch-ready ではないと判定した。payload record writes / payload output
writes は now=false。次は C9F real live collection runner implementation 0GPU
only。
C9F は eval_runs-local 0GPU scaffold として完了し、all 22 C7N fields を
future live hook boundaries に bind、C8S fail-closed semantics を維持した。
最大 boundary は `REAL_LIVE_COLLECTION_RUNNER_SCAFFOLD_READY_NO_COLLECTION_NO_OUTPUT_WRITES`。
C9G は real `%4` で 0GPU artifact-only auth review として完了し、C9F が
C9H live collection launch decision draft-only に sufficient と判定。ただし
launch/collection/payload writes は未承認。
C9H は real `%4` で 0GPU draft-only package として完了し、
`DRAFT_NOT_AUTHORIZED / DO_NOT_RUN` の future command shape のみを定義した。
C9I は real `%4` で 0GPU artifact-only directive review として完了し、
current C9F scaffold は real live collection / payload records / payload outputs
を new implementation delta なしに生成できないと判定した。
次は C9J executable real live collection surface 0GPU only。
C9J は real `%4` で eval_runs-local 0GPU executable surface package として完了し、
valid-marker collect は
`EXECUTABLE_REAL_LIVE_COLLECTION_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_OUTPUT_WRITES`
に到達する。これは C9F auth-dry-run/refusal-only behavior を越えるが、
simulator/CUDA/live collection/payload writes の前で停止する。
次は C9K auth review draft-only over C9J artifacts。
C9K は real `%4` で 0GPU artifact-only auth review として完了し、C9J artifacts
を read-only で検証した。C9J runner modes は実行していない。
次は C9L live collection launch decision draft-only。
C9L は real `%4` で 0GPU draft-only package として完了し、
`DRAFT_NOT_AUTHORIZED / DO_NOT_RUN` の future command shape のみを定義した。
command execution / C9J runner modes execution は行っていない。
次は C9M fresh scoped launch directive or review。
C9M は real `%4` で fresh-scoped 0GPU boundary command として完了したが、
C9J runner が C9M output directory を C9J root 外として拒否したため
`C9M_FAIL_OR_ABORT / PRODUCT_GO_FALSE` として閉じた。retry は行っていない。
次は C9N 0GPU review or implementation delta for output-dir guard mismatch。
C9N は real `%4` で 0GPU artifact-only output-dir guard review として完了し、
C9M を fail-closed scope/contract mismatch と分類した。C9J root lock は
prior artifact protection として正しく、runner guard bug ではない。
次は C9O eval_runs-local output-dir guard adapter/runner implementation
0GPU draft-only。
C9O は real `%4` で 0GPU eval_runs-local output-dir guard adapter/runner として
完了し、C9O_ROOT allowlist で C9M mismatch を package/proof level で解消した。
static/dry/refusal/valid boundary/outside-root proof は PASS。C9J semantics と
prior artifacts は read-only で維持し、launch/collection/payload writes/GPU/training
は未承認。次は C9P boundary command or auth review draft-only。
C9P は real `%4` が artifacts を作成したが formal marker 前で stall したため、
%7 relay-side verification により artifact-derived COMPLETE として受理した。
C9P は C9O boundary proof repeat を same-scope repeat と判定し skip。
次は C9Q next non-repeat review/design draft-only。
C9Q は real `%4` が artifacts を作成したが formal marker 前で stall したため、
%7 relay-side verification により artifact-derived COMPLETE として受理した。
C9Q は accepted boundary stack が real live collection / payload record emission
の前で止まっていると判定し、次は C9R post-boundary live collection
preflight/handoff 0GPU draft-only。
C9R は real `%4` で 0GPU post-boundary live collection preflight/handoff package
として完了した。accepted C9O/C9J boundary readiness の後段に fail-closed
handoff surface を定義し、最大 terminal state は
`POST_BOUNDARY_LIVE_COLLECTION_PREFLIGHT_HANDOFF_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`。
payload record / payload output writes は未承認。次は C9S post-boundary
preflight/handoff auth review 0GPU draft-only。
C9S は real `%4` で 0GPU artifact-only auth review として完了し、C9R handoff
contract は C9T draft-only next-route review/design に十分と判定した。launch /
collection / payload writes / dataset consumption / training / GPU は未承認。
次は C9T next-route auth review or design 0GPU draft-only。
C9T は real `%4` で 0GPU artifact-only next-route review/design として完了し、
C9U post-handoff implementation or launch-readiness route draft-only を選定した。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
次は C9U post-handoff implementation or launch-readiness route 0GPU draft-only。
C9U は real `%4` で 0GPU artifact-only post-handoff route package として完了し、
launch-readiness review は premature、C9V bounded post-handoff implementation
delta draft-only が次と判定した。launch / collection / payload writes /
dataset consumption / training / GPU は未承認。
C9V は real `%4` で 0GPU bounded post-handoff implementation delta として完了し、
C9R handoff contract を consume する post-handoff execution plan object を作成した。
terminal state は `POST_HANDOFF_IMPLEMENTATION_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9W は real `%4` で 0GPU artifact-only auth review として完了し、C9V artifacts を
review して C9X launch-readiness route draft-only に sufficient と判定した。
C9V runner/proof modes は実行していない。launch / collection / payload writes /
dataset consumption / training / GPU は未承認。
C9X は real `%4` で 0GPU artifact-only launch-readiness route review として完了し、
C9Y launch-decision draft は NOT_AUTHORIZED として packageable と判定した。
launch command / launch-decision command / C9V-C9W modes は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9Y は real `%4` で 0GPU artifact-only launch-decision draft package として完了し、
future C9Z fresh-scoped launch directive draft は NOT_AUTHORIZED としてのみ作成した。
launch command / launch-decision command / C9V-C9W-C9X modes は実行していない。
future command shape は `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` のみで、launch /
collection / payload writes / dataset consumption / training / GPU は未承認。
C9Z は real `%4` で 0GPU artifact-only fresh-scoped launch directive draft として完了し、
current C9V runner は auth-dry-run が prior C9V root に書き戻し、fresh output root
を C9V root guard で拒否するため exact future command は as-is で safe draft 不可と判定した。
launch command / launch-decision command / runner/proof modes / C9V-C9W-C9X-C9Y modes は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AA は real `%4` で 0GPU eval_runs-local fresh-scoped command-surface delta として完了し、
C9V post-handoff semantics を read-only で保存しながら C9AA-local output root のみへ
artifact を書く adapter/proof package を作成した。valid-marker auth-dry-run は
`C9AA_FRESH_SCOPED_COMMAND_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`
のみ到達し、outside-root / protected-SHA mismatch refusal は file/payload writes 前に fail-closed。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AB は real `%4` で 0GPU artifact-only authorization review として完了し、
C9AA terminal state、C9V read-only preservation、C9AA root-only writes、
root-escape/prior-overwrite refusal proofs を確認した。C9AA runner/proof modes /
prior runner modes / launch command は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AC は real `%4` で 0GPU artifact-only launch-decision draft package として完了し、
future command shape を `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` として定義した。
future command shape / launch command / C9AA runner modes / prior runner modes は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AD は real `%4` で 0GPU artifact-only fresh-scoped launch-directive
command-safety review として完了し、exact C9AC command は completed C9AA
root を指し `c9aa_auth_dry_run_manifest.json` を overwrite し得るため
as-is carry-forward 不可と判定した。C9AC command shape / launch command /
C9AA runner modes / prior runner modes は実行していない。
C9AE は real `%4` で 0GPU eval_runs-local no-prior-mutation command-surface
delta として完了し、fresh C9AE root のみへ proof artifacts を書く local
surface を作成した。valid-marker auth-dry-run は
`C9AE_NO_PRIOR_MUTATION_COMMAND_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`
のみ到達し、C9AC command shape / C9AA runner modes / prior runner modes は実行していない。
C9AF は real `%4` で 0GPU artifact-only auth review として完了し、
C9AE artifact hashes、terminal state、fail-closed refusal proofs、protected
SHA/diff、C9AA auth-manifest immutability、forbidden-output absence、
bytecode absence、empty GPU compute-app state を確認した。C9AF は C9AE
runner/proof modes、C9AC command shape、C9AA/prior runner modes を実行していない。
C9AG は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、candidate future command を `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` として
draft のみ行った。current C9AE command surface は completed C9AE root へ
書くため as-is carry-forward 不可で、future route root へ移すと current
C9AE root guard が file creation 前に refuse する。C9AG decision は
`C9AG_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AH は real `%4` で 0GPU eval_runs-local fresh non-mutating command-surface
delta として完了し、fresh C9AH root のみへ proof artifacts を書く local
surface を作成した。valid-marker auth-dry-run は
`C9AH_FRESH_NON_MUTATING_COMMAND_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`
のみ到達し、C9AG candidate command / C9AE runner modes / C9AC command shape /
C9AA runner modes / prior runner modes は実行していない。C9AH decision は
`C9AH_FRESH_NON_MUTATING_COMMAND_SURFACE_DELTA_0GPU_COMPLETE_READY_FOR_C9AI_AUTH_REVIEW_DRAFT_ONLY`。
C9AI は real `%4` で 0GPU artifact-only auth review として完了し、C9AH
artifact hashes、status/decision/terminal state、C9AE command-surface
semantics read-only preservation、C9AH root-only write behavior、C9AA/C9AE/C9AH
auth-manifest immutability、fail-closed refusal proofs、protected SHA/diff、
forbidden-output absence、bytecode absence、empty GPU compute-app state を確認した。
C9AI は C9AH runner/proof modes、C9AG candidate command、C9AE runner modes、
C9AC command shape、C9AA/prior runner modes を実行していない。C9AI decision は
`C9AI_AUTH_REVIEW_COMPLETE_C9AH_SUFFICIENT_FOR_C9AJ_LAUNCH_DECISION_DRAFT_ONLY`。
C9AJ は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AI/C9AH artifacts を read-only で review した。C9AJ は C9AH を
valid proof evidence と認めたが、C9AH runner は completed C9AH root 内の
`c9ah_auth_dry_run_manifest.json` を書くため executable future command として
as-is carry-forward 不可と判定した。future route root へ移すと current C9AH
root guard が file creation 前に refuse する。C9AJ decision は
`C9AJ_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AK は real `%4` で 0GPU eval_runs-local future-fresh-root command-surface
delta として完了し、explicit future fresh output root を受け取る C9AK-local
runner/proof package を作成した。valid-marker auth-dry-run は C9AL future root
候補を検証したが作成せず、proof artifacts は C9AK root 内だけに書かれた。
C9AK decision は
`C9AK_FUTURE_FRESH_ROOT_COMMAND_SURFACE_DELTA_0GPU_COMPLETE_READY_FOR_C9AL_AUTH_REVIEW_DRAFT_ONLY`。
C9AL は real `%4` で 0GPU artifact-only auth review として完了し、C9AK
artifact hashes、status/decision/terminal state、explicit future-fresh-root
behavior、proof-root containment、outside-eval-runs/prior-root/existing-collision
refusal behavior、protected SHA/diff、C9AA/C9AE/C9AH auth-manifest immutability、
forbidden-output filename absence、bytecode absence、C9AL future-root absence、
empty GPU compute-app state を確認した。C9AL decision は
`C9AL_AUTH_REVIEW_COMPLETE_C9AK_SUFFICIENT_FOR_C9AM_LAUNCH_DECISION_DRAFT_ONLY`。
C9AM は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AL/C9AK hashes/status/decision と C9AK future-fresh-root behavior を
確認したが、C9AK auth-dry-run が completed C9AK root の
`c9ak_auth_dry_run_manifest.json` を書くため safe future command shape は
emit しなかった。C9AM decision は
`C9AM_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
次は future 0GPU command-surface implementation/review delta /
broader routing review / HOLD。
C9AN は real `%4` で 0GPU proof-output fresh-root command-surface delta として
完了し、C9AK future-root validation を read-only で維持しつつ、
proof/auth-dry-run output を explicit caller-supplied fresh output root に
bind した。valid-marker auth-dry-run は C9AN-local
`c9an_proof_outputs/auth_dry_run/` に manifest を書き、prior-root /
outside-eval-runs / existing-collision / protected-SHA mismatch refusals は
file creation 前に fail-closed した。C9AN decision は
`C9AN_PROOF_OUTPUT_FRESH_ROOT_COMMAND_SURFACE_DELTA_COMPLETE_READY_FOR_C9AO_AUTH_REVIEW_DRAFT_ONLY`。
次は C9AO auth review over C9AN command-surface delta 0GPU draft-only /
broader routing review / HOLD。
C9AO は real `%4` で 0GPU artifact-only auth review として完了し、C9AN
hashes/status/decision/terminal state、explicit proof-output binding、proof
containment、refusal proofs、protected locks、C9AP future-root absence、empty
GPU state を確認した。C9AO decision は
`C9AO_AUTH_REVIEW_COMPLETE_C9AN_SUFFICIENT_FOR_C9AP_LAUNCH_DECISION_DRAFT_ONLY`。
次は C9AP launch-decision or directive draft 0GPU draft-only /
broader routing review / HOLD。
C9AP は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AO/C9AN hashes/status/decision と C9AN proof-output binding を確認
したが、C9AN runnable auth-dry-run が completed C9AN root under output を
要求するため safe future command shape は emit しなかった。C9AP decision は
`C9AP_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AQ は real `%4` で 0GPU route-fresh output-root command-surface delta として
完了し、caller-supplied route-fresh output root を path string として validate
しつつ future C9AR root を作成しない C9AQ-local runner/proof package を作成した。
proof artifacts は C9AQ root 内に限定され、invalid/missing marker、
outside-eval-runs、prior-artifact-root、existing-output-collision、
output-root escape、simulated protected-SHA mismatch refusals は file creation 前に
fail-closed した。C9AQ decision は
`C9AQ_ROUTE_FRESH_OUTPUT_ROOT_COMMAND_SURFACE_DELTA_COMPLETE_READY_FOR_C9AR_AUTH_REVIEW_DRAFT_ONLY`。
C9AR は real `%4` で 0GPU artifact-only auth review として完了し、C9AQ
hashes/status/decision/terminal state、route-fresh output-root semantics、proof
containment、refusal proofs、protected locks、C9AS future-root absence、empty
GPU state を確認した。C9AR decision は
`C9AR_AUTH_REVIEW_COMPLETE_C9AQ_SUFFICIENT_FOR_C9AS_LAUNCH_DECISION_DRAFT_ONLY`。
C9AS は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AR/C9AQ evidence は read-only proof evidence として有効だが、
C9AQ auth-dry-run が completed C9AQ root の
`c9aq_auth_dry_run_manifest.json` を書くため safe future command shape は emit
しなかった。C9AS decision は
`C9AS_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AT は real `%4` で 0GPU route-fresh proof-output binding command-surface
delta として完了し、executable auth/proof manifest output を caller-supplied
`c9at_route_outputs/auth_dry_run/` に bind した。C9AT decision は
`C9AT_ROUTE_FRESH_PROOF_OUTPUT_BINDING_DELTA_COMPLETE_READY_FOR_C9AU_AUTH_REVIEW_DRAFT_ONLY`。
C9AU は real `%4` で 0GPU artifact-only auth review として完了し、C9AT を
C9AV launch-decision draft-only に十分と判定した。C9AU decision は
`C9AU_AUTH_REVIEW_COMPLETE_C9AT_SUFFICIENT_FOR_C9AV_LAUNCH_DECISION_DRAFT_ONLY`。
C9AV は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AU/C9AT evidence は有効だが、C9AT auth-dry-run の local-only proof
execution guard が completed C9AT root under proof manifest を要求するため safe
future executable command shape は emit しなかった。C9AV decision は
`C9AV_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AW は real `%4` で 0GPU future-root proof-manifest binding implementation
delta として完了し、auth/proof manifest output を explicit caller-supplied
route output root に bind し、C9AT completed-root-only proof-manifest guard を
future command surface へ carry しないことを証明した。C9AW decision は
`C9AW_FUTURE_ROOT_PROOF_MANIFEST_BINDING_DELTA_COMPLETE_READY_FOR_C9AX_AUTH_REVIEW_DRAFT_ONLY`。
C9AX は real `%4` で 0GPU artifact-only auth review として完了し、C9AW を
C9AY launch-decision draft-only に十分と判定した。C9AX decision は
`C9AX_AUTH_REVIEW_COMPLETE_C9AW_SUFFICIENT_FOR_C9AY_LAUNCH_DECISION_DRAFT_ONLY`。
C9AY は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、future command shape は `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` としてのみ
package 可能、future C9AZ route output root は未作成と判定した。C9AY decision は
`C9AY_LAUNCH_DECISION_OR_DIRECTIVE_DRAFT_READY_DRAFT_ONLY`。
C9AZ は real `%4` で 0GPU scoped launch-or-review preflight として完了し、
C9AY/C9AW authorized command string を照合したが、C9AW `auth-dry-run` が
manifest write 後に `refresh_summary()` を呼び completed C9AW artifacts を
rewrite する prior-artifact mutation risk を検出したため実行前に中止した。
C9AZ decision は `FAIL_OR_ABORT`。
C9BB は real `%4` で 0GPU no-prior-mutation auth-dry-run implementation delta
として完了し、valid auth-dry-run が caller-supplied route output root under
`c9bb_auth_dry_run_manifest.json` のみを書き、`refresh_summary` path を持たず、
summary/report/future-draft artifacts を manifest creation 後に rewrite しない
ことを証明した。C9BB decision は
`C9BB_NO_PRIOR_MUTATION_AUTH_DRY_RUN_DELTA_COMPLETE_READY_FOR_C9BC_AUTH_REVIEW_DRAFT_ONLY`。
C9BC は real `%4` で 0GPU artifact-only auth review over C9BB delta artifacts
を作成し、formal completion marker 前に post-verification 中断となったが、
relay-side verification は PASS。C9BC decision は
`C9BC_AUTH_REVIEW_COMPLETE_C9BB_SUFFICIENT_FOR_C9BD_LAUNCH_DECISION_DRAFT_ONLY`。
C9BD は real `%4` で 0GPU launch-decision/directive draft として完了し、
future C9BE command shape を `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` としてのみ
draft した。future C9BE root / route-output root は未作成。C9BD decision は
`C9BD_LAUNCH_DECISION_OR_DIRECTIVE_DRAFT_COMPLETE_READY_FOR_C9BE_SCOPED_LAUNCH_OR_REVIEW_DRAFT_ONLY`。
C9BE は real `%4` で exact C9BB auth-dry-run command を 0GPU で一度だけ
実行し、exit 0、route output は `c9bb_auth_dry_run_manifest.json` のみ、
terminal state は
`C9BB_NO_PRIOR_MUTATION_AUTH_DRY_RUN_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`。
C9BE decision は
`C9BE_SCOPED_AUTH_DRY_RUN_SUCCESS_REVIEW_REQUIRED_READY_FOR_C9BF_AUTH_REVIEW_DRAFT_ONLY`。
C9BF は real `%4` で 0GPU artifact-only auth review over C9BE として完了し、
C9BE exact-once / route-output / no-GPU verdicts、protected locks、prior
artifact immutability、C9BG future-root absence を確認した。C9BF decision は
`C9BF_AUTH_REVIEW_COMPLETE_C9BE_SUFFICIENT_FOR_C9BG_NEXT_ROUTE_DRAFT_ONLY`。
C9BG は real `%4` で 0GPU next-route review として完了し、C9BH
launch-decision/directive draft-only を選択した。C9BG decision は
`C9BG_NEXT_ROUTE_REVIEW_COMPLETE_READY_FOR_C9BH_LAUNCH_DECISION_DRAFT_ONLY`。
C9BH は real `%4` usage limit 後に relay-side 0GPU artifact-only draft として
完了し、C9BE auth-dry-run repeat となる C9BI command shape は emit しないと
判断した。C9BH decision は `C9BH_BROADER_ROUTING_REVIEW_RECOMMENDED`。
C9BJ は relay-side 0GPU artifact-only broader routing review として完了し、
C9BI と追加 C9 auth-dry-run wrapper を exhausted repeat path として退けた。
C9BJ decision は
`C9BJ_C9_AUTH_DRY_RUN_LOOP_SATURATED_SELECT_C10_LIVE_COLLECTION_SEMANTIC_BRIDGE_DRAFT_ONLY`。
C10 は relay-side 0GPU artifact-only semantic bridge specification として
完了し、C9R handoff と C9V execution plan を semantic entrypoint contract
へ束ねた。C10 decision は
`C10_SEMANTIC_BRIDGE_CONTRACT_COMPLETE_READY_FOR_C10A_ENTRYPOINT_SPEC_DRAFT_ONLY`。
C10A は relay-side 0GPU artifact-only entrypoint interface specification
として完了し、`future_live_collector_semantic_preflight(...)` の interface
contract を定義した。C10A decision は
`C10A_ENTRYPOINT_SPEC_COMPLETE_READY_FOR_C10B_SCAFFOLD_OR_REVIEW_DRAFT_ONLY`。
C10B は real `%4` により 0GPU data-only scaffold-or-review として完了し、
C10A interface を非実行 scaffold に materialize した。C10B decision は
`C10B_ENTRYPOINT_SCAFFOLD_REVIEW_COMPLETE_READY_FOR_C10C_LIVE_COLLECTION_AUTH_OR_REVIEW_DRAFT_ONLY`。
C10C は real `%4` により 0GPU artifact-only auth-or-review として完了し、
C10B が nonexecuting authorization-surface basis としては十分だが
launch/live-collection-ready ではないことを確認した。C10C decision は
`C10C_NONEXECUTING_AUTH_SURFACE_REVIEW_COMPLETE_READY_FOR_C10D_ENTRYPOINT_PREFLIGHT_PROOF_DRAFT_ONLY`。
C10D は real `%4` により 0GPU standard-library-only entrypoint preflight
proof として完了し、10 個の fail-closed refusal case を data-only で
記録した。C10D は launch-capable でも live-collection-ready でもない。
No C10E draft emitted。Phase3 current-env launch-preflight は real `%4` により
0GPU runner-copy preflight として完了した。既存 Phase3 runner は old env SHA
`b429c1e...` を期待していたため direct launch gate は
`INCOMPLETE_FROM_EXISTING_RUNNER_ENV_SHA_MISMATCH_NO_GPU_LAUNCH_AUTHORIZED`。
current protected env SHA `9a90600f...` 向けの eval_runs-local runner copy は
`OUTPUT_DIR` と `ENV_SHA_EXPECTED` のみを変更し、compile no-import/no-bytecode
PASS。future cuda:0 smoke command draft は `NOT_AUTHORIZED_DO_NOT_RUN`。
この command は後続で `%7`/Rs proxy により separately authorized され、real
`%4` が exactly once on cuda:0 で実行完了した。結果は
`R2A_TRACK_A_PHASE3_CURRENT_ENV_GPU_SMOKE_COMPLETE / PRODUCT_GO_FALSE`、
`SUCCESS_REVIEW_REQUIRED`、`IMPLEMENTATION_EQUIVALENCE_NO_GO`。1107/1107
completions、high_drop cable_drop は source_default 0.6389 から
kinematic_predicate 0.1111 (delta -0.5278)。後続の 0GPU artifact-only
review も完了し、current state は terminal accept/no-go for implementation
equivalence。次は broader track decision、new design delta 付き
release/productization design draft、または HOLD。same-scope Phase3 GPU rerun
は unauthorized。後続の current-env productization delta 0GPU も完了し、
Option B `release_after_success_hold_k` は primary のまま、Option A
`hold_to_completion` は comparator/fallback のまま。future release-gate
implementation/preflight と future GPU gate は NOT_AUTHORIZED。さらに
current-env release-gate launch preflight 0GPU も完了し、copied runner は
four-arm / 1476 completions 形を preserve、future command は
`NOT_AUTHORIZED_DO_NOT_RUN` として draft された。この command は後続で
`%7`/Rs proxy により separately authorized され、real `%4` が exactly once
on cuda:0 で実行完了した。結果は
`R2A_TRACK_A_CURRENT_ENV_RELEASE_GATE_GPU_SMOKE_COMPLETE / PRODUCT_GO_FALSE`、
`SUCCESS_REVIEW_REQUIRED / REVIEW_RELEASE_GATE_SMOKE`。1476/1476
completions、`release_after_success_hold_k` high/mixed/low cable_drop は
0.0/0.0/0.0、released high/mixed n=219 success=1.0 cable_drop=0.0
explosion=0.0。ただし active success regression criterion が fail のため
`PRODUCT_GO=false` は維持し、same-scope GPU rerun は unauthorized。
後続の current-env release-gate artifact-only review 0GPU も完了し、
decision は
`CURRENT_ENV_RELEASE_GATE_REVIEW_COMPLETE_RECOMMEND_RELEASE_GATE_CRITERIA_SCHEMA_REVISION_DESIGN_ONLY`。
`release_after_success_hold_k` の v1 active-success-regression failure は、
成功行が released stratum に移動する release-gated arm には不適切な
criteria/schema mismatch と整理された。`kinematic_step30` は real
fixed-release blocker、`hold_to_completion` は comparator/fallback のまま。
後続の current-env release-gate criteria/schema revision 0GPU も完了し、
decision は
`CURRENT_ENV_RELEASE_GATE_SCHEMA_REVISION_DESIGN_COMPLETE_READY_FOR_SEPARATE_V3_POSTHOC_OR_SOURCE_DESIGN_DRAFT_ONLY`。
v3 は execution_status、legacy_v1_diagnostics、
release_gate_mechanism_verdict、active_unreleased_coverage_diagnostics、
comparator_roles、productization_verdict、`PRODUCT_GO`、
`physical_grasp_claim` を分離する。後続の v3 posthoc/source-design draft、
D0+C4 decision package、G1-G3 refinement package、D0 discriminator preflight
package、D0 Tier-A gap closure package、D0 runner-design review package、D0
impedance source-surface spike package、D0 telemetry-only source draft package、
D0 control-source design packet、D0 control-source implementation draft、
supervisor artifact-only review、D0 runner/preflight package も COMPLETE。
D0 runner/preflight Tier-A review は INCOMPLETE 後、D0 human-Rs gate GAP-A
fix とその review は COMPLETE。Rs-proxy predicate transmission は `%3` が
ATTESTED。現在の次手は GAP-B functional D0 runner Tier-A planning、または
HOLD。future D0 execution、GPU/simulator、functional D0 runner
implementation、further source/task_config mutation、training、product claim、
physical-grasp claim、T-ROOT 95 claim は Tier-A-required かつ未承認。
C5A support-manifold guard は high/mixed cable_drop 0.0 を維持し
high/mixed active explosion を timeout debt に変換したが、これは左指
kinematic fixture による pre-contact support diagnostic / product-shaping
predicate であり、物理把持 claim ではない。`physical_grasp_claim=false` と
`PRODUCT_GO=false` は維持する。C6B smoke は 492/492 completions で実行PASS
だったが timeout debt を回復せず、tested arms は control と同一 outcome だった。
C6C は extended arm が timeout step 200 のままであることと、late probes が
terminal outcome を変えないことを確認した。C6E は historical C6B を
contract-fail として扱い、C6F はその contract result を coherent と判定した。
C6G は C6H 0GPU implementation の範囲と gates を package 化し、C6H は
historical C6B の expected contract failure を明示する runner/report scaffold
を実装した。C6I は C6H scaffold を PASS と判定したが GPU auth ready ではない
と結論した。C6J は executable GPU auth を
`REDESIGN_REQUIRED_BEFORE_EXECUTABLE_GPU_AUTH` とし、future launch draft を
`DRAFT_NOT_AUTHORIZED_BLOCKED_ON_C6K` に留めた。同一 scope の repeat GPU は
不要。C6K は 0GPU live eval-path telemetry runner scaffold を実装し、eval は未承認
のまま。C6L は C6M launch directive draft を `DRAFT_NOT_AUTHORIZED` として
作成した。C6M は 492/492 completions、no abort、cuda:0 only で実行し、
live branch/horizon telemetry は存在したが terminal outcome は全 candidate が
control と一致した。C6N は timeout-recovery no-go as run を支持し、C6O は
C6B/C6M timeout-recovery family を no-go as run として closeout した。C7 は
`early_strict_ready_capture_controller` を primary non-repeat variable として選定し、
C7A は 0GPU scaffold/auth package を実装し、check/dry-run/refusal を PASS した。
C7B は future C7C 0GPU launch-capable runner implementation の準備可能性を
review したが、GPU auth ではない。C7C は 0GPU runner package を実装し、
py_compile/check/dry-run/refusal/JSON を PASS、target slice n=42/high_drop=20/
mixed=22/timeout=42 と future eval guard を確認した。C7D は C7C runner を
review し、valid-marker path が concrete eval implementation へ移らないため
`C7D_REDESIGN_REQUIRED_BEFORE_GPU_AUTH` とした。C7E は copy-derived runner/package
を実装し、valid-marker `auth-dry-run` が `EVAL_TRANSFER_READY` を出すことを
0GPU で確認した。C7F は future C7G GPU smoke を draft-only で initially
packageable と review したが、C7F correction で C7G draft marker prefix
mismatch と C7E valid-marker eval refusal を確認し、その GPU auth draft は
executable ではないと retracted/qualified した。C7H は 0GPU launch-path
implementation を完了し、future marker prefix alignment、invalid-marker refusal
before heavy imports/simulator/CUDA/output writes、valid-marker auth-dry-run
`CONCRETE_FUTURE_EVAL_BOUNDARY_READY` を確認した。C7I は C7H を 0GPU review
し、future GPU-smoke package を draft-only ready と判定したが launch は承認して
いない。C7J は fresh explicit scoped directive により cuda:0 で 246/246
completions、no abort で実行PASSしたが、C7H candidate は control と terminal
metrics が完全一致し、terminal-signature delta は 0 だった。C7K は 0GPU
posthoc review で early-capture activation は live だが作用量/方向と軌道目的が
不足して terminal 改善に届かなかったと結論した。C7L は
`strict_ready_dwell_objective_policy_redesign` を選定した。C7M は loss spec を
ready としたが C7 target-slice trainable payload は not ready と判定した。C7N は
42-row manifest と required payload schema を package 化した。C7O は 0GPU
payload runner scaffold を実装し、check/dry-run/refusal を PASS した。C7P は
direct collection auth を blocked とし、C7Q 0GPU launch-capable runner
implementation を推奨した。C7Q は valid-marker auth-dry-run で
`PAYLOAD_COLLECTION_BOUNDARY_READY` を確認した。C7R は actual collect path が
refusal-only のため collection launch draft を blocked とした。C7S は
valid-marker collect が `COLLECT_PATH_BOUNDARY_READY` へ到達することを 0GPU で
確認し、payload records/tensor shards/checkpoints/model files/training outputs
を生成しなかった。C7T は future C7U launch decision を `DRAFT_NOT_AUTHORIZED`
として packageable と判定したが、launch/GPU/collection は承認していない。
C7U は 1 回だけ command を実行し `COLLECT_PATH_BOUNDARY_READY` に到達したが、
payload output dir は absent で required payload outputs は missing のため
review-hold とした。C7V は C7-local writer scaffold を 0GPU で実装し、
py_compile/check/dry-run を PASS したが payload outputs は生成していない。
C7W は payload collection auth package review を 0GPU で完了し、writer scaffold
は valid だが real collect-record integration が未証明のため launch draft を
blocked とした。C7X は real collector-to-writer integration を 0GPU で完了し、
42 件の payload records と 42 件の completion records を in-memory validate、
C7V writer signature へ exact kwargs を bind し、file write 前に output writes を
suppress した。C7Y は payload collection auth package review を 0GPU で完了し、
単一 launch-capable runner が C7S collect preflight、future real collector
records、C7X validation、C7V writer call をまだ接続していないため launch draft を
blocked とした。C7Z は launch-capable collector-writer runner proof を 0GPU で
完了し、`COLLECTOR_WRITER_LAUNCH_BOUNDARY_READY`、in-memory records validation、
C7V writer kwargs binding、writer/file-write suppression を確認した。C8A は C7Z
を review し、single-runner boundary proof は閉じたが writer invocation は
suppressed のままなので launch draft は未作成とした。C8B は write-disabled
recording writer/shim を records ready 後に invoke し、real C7V file-writing path
未実行かつ payload output files なしで guarded invocation semantics を証明した。
C8C は C8B package を artifact-only review し、real C7V file-writing path と
real output path が未証明のため launch draft を blocked とした。
C8D は actual C7V `PayloadOutputWriter.write_payload_outputs(...)` method を
records ready 後に invoke し、real file-writing path を reached、lower-level file
writes を creation 前に intercept した。C8E は C8D package を artifact-only review
し、valid collect が intercepted dry-run に route するため launch draft を blocked
とした。C8F は launch-capable future valid collect path を `FileWriteInterceptor`
なしで定義し、actual C7V writer signature binding、records-ready 後 writer
invocation plan、output-collision guard、invalid-marker refusal guard を確認したが、
writer invocation、collection launch、payload outputs 生成はしていない。C8G は
C8F package を review し、current C8F valid `--mode collect` が dry-run/
suppression-only で `collection_launch_suppressed_by_c8f_0gpu_scope=true` のため
launch draft を blocked とした。C8H は valid `--mode collect` を
`EXECUTABLE_COLLECT_WRITER_OUTPUT_BOUNDARY_READY` に到達させたが、collection
launch と payload outputs は生成していない。
C8I は C8H package を artifact-only review し、C8J launch-decision package を
`DRAFT_NOT_AUTHORIZED` としてのみ draftable と判定した。artifact consistency patch
で C8J draft の output path は
`eval_runs/r2a_track_a_strict_gate_c8j_payload_collection_launch_decision_20260523/boundary_outputs/results/`
に整合済み。C8J は one-run launch decision として
`EXECUTABLE_COLLECT_WRITER_OUTPUT_BOUNDARY_READY` に到達したが、payload output
files は生成しなかった。C8K は missing transition を C8H collect manifest-only /
no C7V writer call / no C8J output-root binding と特定した。C8L は actual C7V
writer path binding を write suppression 下で証明し、all five future C8J output
paths を intercept したが files は生成していない。C8M は C8L proof を review し、
C8N draft を `DRAFT_NOT_AUTHORIZED` として作成した。C8N は actual C7V writer
path で five authorized output files を作成し、42 payload rows / 42 completion
records を validate した。C8O はその output completion を artifact-only review し、
five files、42-row counts、22/22 required field coverage、target-slice row-key
match、protected SHA locks、forbidden-output absence を確認した。次は C8P
payload dataset-consumption/training-auth review 0GPU、broader productization/
routing review、または HOLD。C8P は payload semantics を review し、
structural/provenance-ready only だが dry-run/proxy-shaped values のため
training-auth は blocked とした。C8Q は field provenance audit で live per-step
fields が存在しないことを確認した。次は C8R live payload collection path design
0GPU draft-only。C8R は 0GPU design-only で 22 C7N fields を future live hooks /
fail-closed validations に mapping し、次は C8S live payload collection scaffold
0GPU draft-only とした。C8S は local scaffold runner と proof artifacts を作成し、
collection/output writes/GPU/training なしで all 22 fields の fail-closed hook map
と refusal behavior を検証した。次は C8T live payload collection auth review
0GPU draft-only。C8T は C8S artifacts を検証し、collection-auth ready now=false、
C8U live payload collection path/auth package 0GPU draft-only next とした。C8U は
no-output path boundary を定義し、C8V live payload collection launch-or-review
0GPU draft-only next とした。C8V は review branch のみを実行し、C8U artifact
package と no-output boundary を検証した。次は C8W launch-capable live
collection runner path 0GPU draft-only。C8W は eval_runs-local runner/path
package を作成し、valid-marker auth-dry-run は
`LIVE_COLLECTION_RUNNER_PATH_READY_NO_COLLECTION_NO_OUTPUT_WRITES` のみ到達した。
C8X は C8W artifacts を review し、collection-auth ready now=false と判定した。
C8Y は valid-marker collect を
`EXECUTABLE_LIVE_COLLECTION_BOUNDARY_READY_NO_COLLECTION_NO_OUTPUT_WRITES`
へ到達させた。C8Z は C8Y boundary を review し、C9 draft-only package には
sufficient だが live collection launch auth ready now=false と判定した。次は C9
live collection execution path 0GPU draft-only。
C9 は post-boundary preflight handoff と fail-closed guards を定義し、launch
auth/output auth false を維持した。次は C9A live collection execution path auth
review 0GPU draft-only。
C9A は C9 を future launch-decision draft に sufficient と review したが、
launch/output auth は now=false のまま維持した。次は C9B live collection launch
decision draft / fresh scoped directive only。
C9B は no-command `DRAFT_NOT_AUTHORIZED` launch-decision draft を作成した。
実行は未承認で、次は explicitly authorized な fresh scoped C9C-or-later
launch directive/review only。
C9C は 0GPU fresh-scoped launch directive/review package を作成した。
future command は `DO_NOT_RUN / DRAFT_NOT_AUTHORIZED` のままで、C9C 自体は
実行を authorize しない。次は explicitly authorized な fresh scoped C9D-or-later
launch decision/review only。
C9D は relay-side 0GPU launch readiness gap review で、C9C command が C8Y
boundary-only であり real live collection runner ready ではないと判定した。
C9E は real `%4` で 0GPU artifact-only review として完了し、C8S/C8U/C8W/C8Y
が still boundary-only であり、no reviewed artifact が real live collection
runner launch-ready ではないと判定した。payload record writes / payload output
writes は now=false。次は C9F real live collection runner implementation 0GPU
only。
C9F は eval_runs-local 0GPU scaffold として完了し、all 22 C7N fields を
future live hook boundaries に bind、C8S fail-closed semantics を維持した。
最大 boundary は `REAL_LIVE_COLLECTION_RUNNER_SCAFFOLD_READY_NO_COLLECTION_NO_OUTPUT_WRITES`。
C9G は real `%4` で 0GPU artifact-only auth review として完了し、C9F が
C9H live collection launch decision draft-only に sufficient と判定。ただし
launch/collection/payload writes は未承認。
C9H は real `%4` で 0GPU draft-only package として完了し、
`DRAFT_NOT_AUTHORIZED / DO_NOT_RUN` の future command shape のみを定義した。
C9I は real `%4` で 0GPU artifact-only directive review として完了し、
current C9F scaffold は real live collection / payload records / payload outputs
を new implementation delta なしに生成できないと判定した。
次は C9J executable real live collection surface 0GPU only。
C9J は real `%4` で eval_runs-local 0GPU executable surface package として完了し、
valid-marker collect は
`EXECUTABLE_REAL_LIVE_COLLECTION_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_OUTPUT_WRITES`
に到達する。これは C9F auth-dry-run/refusal-only behavior を越えるが、
simulator/CUDA/live collection/payload writes の前で停止する。
次は C9K auth review draft-only over C9J artifacts。
C9K は real `%4` で 0GPU artifact-only auth review として完了し、C9J artifacts
を read-only で検証した。C9J runner modes は実行していない。
次は C9L live collection launch decision draft-only。
C9L は real `%4` で 0GPU draft-only package として完了し、
`DRAFT_NOT_AUTHORIZED / DO_NOT_RUN` の future command shape のみを定義した。
command execution / C9J runner modes execution は行っていない。
次は C9M fresh scoped launch directive or review。
C9M は real `%4` で fresh-scoped 0GPU boundary command として完了したが、
C9J runner が C9M output directory を C9J root 外として拒否したため
`C9M_FAIL_OR_ABORT / PRODUCT_GO_FALSE` として閉じた。retry は行っていない。
次は C9N 0GPU review or implementation delta for output-dir guard mismatch。
C9N は real `%4` で 0GPU artifact-only output-dir guard review として完了し、
C9M を fail-closed scope/contract mismatch と分類した。C9J root lock は
prior artifact protection として正しく、runner guard bug ではない。
次は C9O eval_runs-local output-dir guard adapter/runner implementation
0GPU draft-only。
C9O は real `%4` で 0GPU eval_runs-local output-dir guard adapter/runner として
完了し、C9O_ROOT allowlist で C9M mismatch を package/proof level で解消した。
static/dry/refusal/valid boundary/outside-root proof は PASS。C9J semantics と
prior artifacts は read-only で維持し、launch/collection/payload writes/GPU/training
は未承認。次は C9P boundary command or auth review draft-only。
C9P は real `%4` が artifacts を作成したが formal marker 前で stall したため、
%7 relay-side verification により artifact-derived COMPLETE として受理した。
C9P は C9O boundary proof repeat を same-scope repeat と判定し skip。
次は C9Q next non-repeat review/design draft-only。
C9Q は real `%4` が artifacts を作成したが formal marker 前で stall したため、
%7 relay-side verification により artifact-derived COMPLETE として受理した。
C9Q は accepted boundary stack が real live collection / payload record emission
の前で止まっていると判定し、次は C9R post-boundary live collection
preflight/handoff 0GPU draft-only。
C9R は real `%4` で 0GPU post-boundary live collection preflight/handoff package
として完了した。accepted C9O/C9J boundary readiness の後段に fail-closed
handoff surface を定義し、最大 terminal state は
`POST_BOUNDARY_LIVE_COLLECTION_PREFLIGHT_HANDOFF_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`。
payload record / payload output writes は未承認。次は C9S post-boundary
preflight/handoff auth review 0GPU draft-only。
C9S は real `%4` で 0GPU artifact-only auth review として完了し、C9R handoff
contract は C9T draft-only next-route review/design に十分と判定した。launch /
collection / payload writes / dataset consumption / training / GPU は未承認。
次は C9T next-route auth review or design 0GPU draft-only。
C9T は real `%4` で 0GPU artifact-only next-route review/design として完了し、
C9U post-handoff implementation or launch-readiness route draft-only を選定した。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
次は C9U post-handoff implementation or launch-readiness route 0GPU draft-only。
C9U は real `%4` で 0GPU artifact-only post-handoff route package として完了し、
launch-readiness review は premature、C9V bounded post-handoff implementation
delta draft-only が次と判定した。launch / collection / payload writes /
dataset consumption / training / GPU は未承認。
C9V は real `%4` で 0GPU bounded post-handoff implementation delta として完了し、
C9R handoff contract を consume する post-handoff execution plan object を作成した。
terminal state は `POST_HANDOFF_IMPLEMENTATION_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9W は real `%4` で 0GPU artifact-only auth review として完了し、C9V artifacts を
review して C9X launch-readiness route draft-only に sufficient と判定した。
C9V runner/proof modes は実行していない。launch / collection / payload writes /
dataset consumption / training / GPU は未承認。
C9X は real `%4` で 0GPU artifact-only launch-readiness route review として完了し、
C9Y launch-decision draft は NOT_AUTHORIZED として packageable と判定した。
launch command / launch-decision command / C9V-C9W modes は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9Y は real `%4` で 0GPU artifact-only launch-decision draft package として完了し、
future C9Z fresh-scoped launch directive draft は NOT_AUTHORIZED としてのみ作成した。
launch command / launch-decision command / C9V-C9W-C9X modes は実行していない。
future command shape は `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` のみで、launch /
collection / payload writes / dataset consumption / training / GPU は未承認。
C9Z は real `%4` で 0GPU artifact-only fresh-scoped launch directive draft として完了し、
current C9V runner は auth-dry-run が prior C9V root に書き戻し、fresh output root
を C9V root guard で拒否するため exact future command は as-is で safe draft 不可と判定した。
launch command / launch-decision command / runner/proof modes / C9V-C9W-C9X-C9Y modes は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AA は real `%4` で 0GPU eval_runs-local fresh-scoped command-surface delta として完了し、
C9V post-handoff semantics を read-only で保存しながら C9AA-local output root のみへ
artifact を書く adapter/proof package を作成した。valid-marker auth-dry-run は
`C9AA_FRESH_SCOPED_COMMAND_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`
のみ到達し、outside-root / protected-SHA mismatch refusal は file/payload writes 前に fail-closed。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AB は real `%4` で 0GPU artifact-only authorization review として完了し、
C9AA terminal state、C9V read-only preservation、C9AA root-only writes、
root-escape/prior-overwrite refusal proofs を確認した。C9AA runner/proof modes /
prior runner modes / launch command は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AC は real `%4` で 0GPU artifact-only launch-decision draft package として完了し、
future command shape を `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` として定義した。
future command shape / launch command / C9AA runner modes / prior runner modes は実行していない。
launch / collection / payload writes / dataset consumption / training / GPU は未承認。
C9AD は real `%4` で 0GPU artifact-only fresh-scoped launch-directive
command-safety review として完了し、exact C9AC command は completed C9AA
root を指し `c9aa_auth_dry_run_manifest.json` を overwrite し得るため
as-is carry-forward 不可と判定した。C9AC command shape / launch command /
C9AA runner modes / prior runner modes は実行していない。
C9AE は real `%4` で 0GPU eval_runs-local no-prior-mutation command-surface
delta として完了し、fresh C9AE root のみへ proof artifacts を書く local
surface を作成した。valid-marker auth-dry-run は
`C9AE_NO_PRIOR_MUTATION_COMMAND_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`
のみ到達し、C9AC command shape / C9AA runner modes / prior runner modes は実行していない。
C9AF は real `%4` で 0GPU artifact-only auth review として完了し、
C9AE artifact hashes、terminal state、fail-closed refusal proofs、protected
SHA/diff、C9AA auth-manifest immutability、forbidden-output absence、
bytecode absence、empty GPU compute-app state を確認した。C9AF は C9AE
runner/proof modes、C9AC command shape、C9AA/prior runner modes を実行していない。
C9AG は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、candidate future command を `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` として
draft のみ行った。current C9AE command surface は completed C9AE root へ
書くため as-is carry-forward 不可で、future route root へ移すと current
C9AE root guard が file creation 前に refuse する。C9AG decision は
`C9AG_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AH は real `%4` で 0GPU eval_runs-local fresh non-mutating command-surface
delta として完了し、fresh C9AH root のみへ proof artifacts を書く local
surface を作成した。valid-marker auth-dry-run は
`C9AH_FRESH_NON_MUTATING_COMMAND_SURFACE_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`
のみ到達し、C9AG candidate command / C9AE runner modes / C9AC command shape /
C9AA runner modes / prior runner modes は実行していない。C9AH decision は
`C9AH_FRESH_NON_MUTATING_COMMAND_SURFACE_DELTA_0GPU_COMPLETE_READY_FOR_C9AI_AUTH_REVIEW_DRAFT_ONLY`。
C9AI は real `%4` で 0GPU artifact-only auth review として完了し、C9AH
artifact hashes、status/decision/terminal state、C9AE command-surface
semantics read-only preservation、C9AH root-only write behavior、C9AA/C9AE/C9AH
auth-manifest immutability、fail-closed refusal proofs、protected SHA/diff、
forbidden-output absence、bytecode absence、empty GPU compute-app state を確認した。
C9AI は C9AH runner/proof modes、C9AG candidate command、C9AE runner modes、
C9AC command shape、C9AA/prior runner modes を実行していない。C9AI decision は
`C9AI_AUTH_REVIEW_COMPLETE_C9AH_SUFFICIENT_FOR_C9AJ_LAUNCH_DECISION_DRAFT_ONLY`。
C9AJ は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AI/C9AH artifacts を read-only で review した。C9AJ は C9AH を
valid proof evidence と認めたが、C9AH runner は completed C9AH root 内の
`c9ah_auth_dry_run_manifest.json` を書くため executable future command として
as-is carry-forward 不可と判定した。future route root へ移すと current C9AH
root guard が file creation 前に refuse する。C9AJ decision は
`C9AJ_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AK は real `%4` で 0GPU eval_runs-local future-fresh-root command-surface
delta として完了し、explicit future fresh output root を受け取る C9AK-local
runner/proof package を作成した。valid-marker auth-dry-run は C9AL future root
候補を検証したが作成せず、proof artifacts は C9AK root 内だけに書かれた。
C9AK decision は
`C9AK_FUTURE_FRESH_ROOT_COMMAND_SURFACE_DELTA_0GPU_COMPLETE_READY_FOR_C9AL_AUTH_REVIEW_DRAFT_ONLY`。
C9AL は real `%4` で 0GPU artifact-only auth review として完了し、C9AK
artifact hashes、status/decision/terminal state、explicit future-fresh-root
behavior、proof-root containment、outside-eval-runs/prior-root/existing-collision
refusal behavior、protected SHA/diff、C9AA/C9AE/C9AH auth-manifest immutability、
forbidden-output filename absence、bytecode absence、C9AL future-root absence、
empty GPU compute-app state を確認した。C9AL decision は
`C9AL_AUTH_REVIEW_COMPLETE_C9AK_SUFFICIENT_FOR_C9AM_LAUNCH_DECISION_DRAFT_ONLY`。
C9AM は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AL/C9AK hashes/status/decision と C9AK future-fresh-root behavior を
確認したが、C9AK auth-dry-run が completed C9AK root の
`c9ak_auth_dry_run_manifest.json` を書くため safe future command shape は
emit しなかった。C9AM decision は
`C9AM_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
次は future 0GPU command-surface implementation/review delta /
broader routing review / HOLD。
C9AN は real `%4` で 0GPU proof-output fresh-root command-surface delta として
完了し、C9AK future-root validation を read-only で維持しつつ、
proof/auth-dry-run output を explicit caller-supplied fresh output root に
bind した。valid-marker auth-dry-run は C9AN-local
`c9an_proof_outputs/auth_dry_run/` に manifest を書き、prior-root /
outside-eval-runs / existing-collision / protected-SHA mismatch refusals は
file creation 前に fail-closed した。C9AN decision は
`C9AN_PROOF_OUTPUT_FRESH_ROOT_COMMAND_SURFACE_DELTA_COMPLETE_READY_FOR_C9AO_AUTH_REVIEW_DRAFT_ONLY`。
次は C9AO auth review over C9AN command-surface delta 0GPU draft-only /
broader routing review / HOLD。
C9AO は real `%4` で 0GPU artifact-only auth review として完了し、C9AN
hashes/status/decision/terminal state、explicit proof-output binding、proof
containment、refusal proofs、protected locks、C9AP future-root absence、empty
GPU state を確認した。C9AO decision は
`C9AO_AUTH_REVIEW_COMPLETE_C9AN_SUFFICIENT_FOR_C9AP_LAUNCH_DECISION_DRAFT_ONLY`。
次は C9AP launch-decision or directive draft 0GPU draft-only /
broader routing review / HOLD。
C9AP は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AO/C9AN hashes/status/decision と C9AN proof-output binding を確認
したが、C9AN runnable auth-dry-run が completed C9AN root under output を
要求するため safe future command shape は emit しなかった。C9AP decision は
`C9AP_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AQ は real `%4` で 0GPU route-fresh output-root command-surface delta として
完了し、caller-supplied route-fresh output root を path string として validate
しつつ future C9AR root を作成しない C9AQ-local runner/proof package を作成した。
proof artifacts は C9AQ root 内に限定され、invalid/missing marker、
outside-eval-runs、prior-artifact-root、existing-output-collision、
output-root escape、simulated protected-SHA mismatch refusals は file creation 前に
fail-closed した。C9AQ decision は
`C9AQ_ROUTE_FRESH_OUTPUT_ROOT_COMMAND_SURFACE_DELTA_COMPLETE_READY_FOR_C9AR_AUTH_REVIEW_DRAFT_ONLY`。
C9AR は real `%4` で 0GPU artifact-only auth review として完了し、C9AQ
hashes/status/decision/terminal state、route-fresh output-root semantics、proof
containment、refusal proofs、protected locks、C9AS future-root absence、empty
GPU state を確認した。C9AR decision は
`C9AR_AUTH_REVIEW_COMPLETE_C9AQ_SUFFICIENT_FOR_C9AS_LAUNCH_DECISION_DRAFT_ONLY`。
C9AS は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AR/C9AQ evidence は read-only proof evidence として有効だが、
C9AQ auth-dry-run が completed C9AQ root の
`c9aq_auth_dry_run_manifest.json` を書くため safe future command shape は emit
しなかった。C9AS decision は
`C9AS_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AT は real `%4` で 0GPU route-fresh proof-output binding command-surface
delta として完了し、executable auth/proof manifest output を caller-supplied
`c9at_route_outputs/auth_dry_run/` に bind した。C9AT decision は
`C9AT_ROUTE_FRESH_PROOF_OUTPUT_BINDING_DELTA_COMPLETE_READY_FOR_C9AU_AUTH_REVIEW_DRAFT_ONLY`。
C9AU は real `%4` で 0GPU artifact-only auth review として完了し、C9AT を
C9AV launch-decision draft-only に十分と判定した。C9AU decision は
`C9AU_AUTH_REVIEW_COMPLETE_C9AT_SUFFICIENT_FOR_C9AV_LAUNCH_DECISION_DRAFT_ONLY`。
C9AV は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、C9AU/C9AT evidence は有効だが、C9AT auth-dry-run の local-only proof
execution guard が completed C9AT root under proof manifest を要求するため safe
future executable command shape は emit しなかった。C9AV decision は
`C9AV_REQUIRES_ANOTHER_0GPU_REVIEW_OR_IMPLEMENTATION_DELTA`。
C9AW は real `%4` で 0GPU future-root proof-manifest binding implementation
delta として完了し、auth/proof manifest output を explicit caller-supplied
route output root に bind し、C9AT completed-root-only proof-manifest guard を
future command surface へ carry しないことを証明した。C9AW decision は
`C9AW_FUTURE_ROOT_PROOF_MANIFEST_BINDING_DELTA_COMPLETE_READY_FOR_C9AX_AUTH_REVIEW_DRAFT_ONLY`。
C9AX は real `%4` で 0GPU artifact-only auth review として完了し、C9AW を
C9AY launch-decision draft-only に十分と判定した。C9AX decision は
`C9AX_AUTH_REVIEW_COMPLETE_C9AW_SUFFICIENT_FOR_C9AY_LAUNCH_DECISION_DRAFT_ONLY`。
C9AY は real `%4` で 0GPU artifact-only launch-decision/directive draft として
完了し、future command shape は `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` としてのみ
package 可能、future C9AZ route output root は未作成と判定した。C9AY decision は
`C9AY_LAUNCH_DECISION_OR_DIRECTIVE_DRAFT_READY_DRAFT_ONLY`。
C9AZ は real `%4` で 0GPU scoped launch-or-review preflight として完了し、
C9AY/C9AW authorized command string を照合したが、C9AW `auth-dry-run` が
manifest write 後に `refresh_summary()` を呼び completed C9AW artifacts を
rewrite する prior-artifact mutation risk を検出したため実行前に中止した。
C9AZ decision は `FAIL_OR_ABORT`。
C9BB は real `%4` で 0GPU no-prior-mutation auth-dry-run implementation delta
として完了し、valid auth-dry-run が caller-supplied route output root under
`c9bb_auth_dry_run_manifest.json` のみを書き、`refresh_summary` path を持たず、
summary/report/future-draft artifacts を manifest creation 後に rewrite しない
ことを証明した。C9BB decision は
`C9BB_NO_PRIOR_MUTATION_AUTH_DRY_RUN_DELTA_COMPLETE_READY_FOR_C9BC_AUTH_REVIEW_DRAFT_ONLY`。
C9BC は real `%4` で 0GPU artifact-only auth review over C9BB delta artifacts
を作成し、formal completion marker 前に post-verification 中断となったが、
relay-side verification は PASS。C9BC decision は
`C9BC_AUTH_REVIEW_COMPLETE_C9BB_SUFFICIENT_FOR_C9BD_LAUNCH_DECISION_DRAFT_ONLY`。
C9BD は real `%4` で 0GPU launch-decision/directive draft として完了し、
future C9BE command shape を `DRAFT_NOT_AUTHORIZED_DO_NOT_RUN` としてのみ
draft した。future C9BE root / route-output root は未作成。C9BD decision は
`C9BD_LAUNCH_DECISION_OR_DIRECTIVE_DRAFT_COMPLETE_READY_FOR_C9BE_SCOPED_LAUNCH_OR_REVIEW_DRAFT_ONLY`。
C9BE は real `%4` で exact C9BB auth-dry-run command を 0GPU で一度だけ
実行し、exit 0、route output は `c9bb_auth_dry_run_manifest.json` のみ、
terminal state は
`C9BB_NO_PRIOR_MUTATION_AUTH_DRY_RUN_READY_NO_SIM_NO_CUDA_NO_COLLECTION_NO_PAYLOAD_WRITES`。
C9BE decision は
`C9BE_SCOPED_AUTH_DRY_RUN_SUCCESS_REVIEW_REQUIRED_READY_FOR_C9BF_AUTH_REVIEW_DRAFT_ONLY`。
C9BF は real `%4` で 0GPU artifact-only auth review over C9BE として完了し、
C9BE exact-once / route-output / no-GPU verdicts、protected locks、prior
artifact immutability、C9BG future-root absence を確認した。C9BF decision は
`C9BF_AUTH_REVIEW_COMPLETE_C9BE_SUFFICIENT_FOR_C9BG_NEXT_ROUTE_DRAFT_ONLY`。
C9BG は real `%4` で 0GPU next-route review として完了し、C9BH
launch-decision/directive draft-only を選択した。C9BG decision は
`C9BG_NEXT_ROUTE_REVIEW_COMPLETE_READY_FOR_C9BH_LAUNCH_DECISION_DRAFT_ONLY`。
C9BH は real `%4` usage limit 後に relay-side 0GPU artifact-only draft として
完了し、C9BE auth-dry-run repeat となる C9BI command shape は emit しないと
判断した。C9BH decision は `C9BH_BROADER_ROUTING_REVIEW_RECOMMENDED`。
C9BJ は relay-side 0GPU artifact-only broader routing review として完了し、
C9BI と追加 C9 auth-dry-run wrapper を exhausted repeat path として退けた。
C9BJ decision は
`C9BJ_C9_AUTH_DRY_RUN_LOOP_SATURATED_SELECT_C10_LIVE_COLLECTION_SEMANTIC_BRIDGE_DRAFT_ONLY`。
C10 は relay-side 0GPU artifact-only semantic bridge specification として
完了し、C9R handoff と C9V execution plan を semantic entrypoint contract
へ束ねた。C10 decision は
`C10_SEMANTIC_BRIDGE_CONTRACT_COMPLETE_READY_FOR_C10A_ENTRYPOINT_SPEC_DRAFT_ONLY`。
C10A は relay-side 0GPU artifact-only entrypoint interface specification
として完了し、`future_live_collector_semantic_preflight(...)` の interface
contract を定義した。C10A decision は
`C10A_ENTRYPOINT_SPEC_COMPLETE_READY_FOR_C10B_SCAFFOLD_OR_REVIEW_DRAFT_ONLY`。
C10B は real `%4` により 0GPU data-only scaffold-or-review として完了し、
C10A interface を非実行 scaffold に materialize した。C10B decision は
`C10B_ENTRYPOINT_SCAFFOLD_REVIEW_COMPLETE_READY_FOR_C10C_LIVE_COLLECTION_AUTH_OR_REVIEW_DRAFT_ONLY`。
C10C は real `%4` により 0GPU artifact-only auth-or-review として完了し、
C10B が nonexecuting authorization-surface basis としては十分だが
launch/live-collection-ready ではないことを確認した。C10C decision は
`C10C_NONEXECUTING_AUTH_SURFACE_REVIEW_COMPLETE_READY_FOR_C10D_ENTRYPOINT_PREFLIGHT_PROOF_DRAFT_ONLY`。
C10D は real `%4` により 0GPU standard-library-only entrypoint preflight
proof として完了し、10 個の fail-closed refusal case を data-only で
記録した。C10D は launch-capable でも live-collection-ready でもない。
No C10E draft emitted。Phase3 current-env launch-preflight は real `%4` により
0GPU runner-copy preflight として完了した。既存 Phase3 runner は old env SHA
`b429c1e...` を期待していたため direct launch gate は
`INCOMPLETE_FROM_EXISTING_RUNNER_ENV_SHA_MISMATCH_NO_GPU_LAUNCH_AUTHORIZED`。
current protected env SHA `9a90600f...` 向けの eval_runs-local runner copy は
`OUTPUT_DIR` と `ENV_SHA_EXPECTED` のみを変更し、compile no-import/no-bytecode
PASS。future cuda:0 smoke command draft は `NOT_AUTHORIZED_DO_NOT_RUN`。
この command は後続で `%7`/Rs proxy により separately authorized され、real
`%4` が exactly once on cuda:0 で実行完了した。結果は
`R2A_TRACK_A_PHASE3_CURRENT_ENV_GPU_SMOKE_COMPLETE / PRODUCT_GO_FALSE`、
`SUCCESS_REVIEW_REQUIRED`、`IMPLEMENTATION_EQUIVALENCE_NO_GO`。1107/1107
completions、high_drop cable_drop は source_default 0.6389 から
kinematic_predicate 0.1111 (delta -0.5278)。後続の 0GPU artifact-only
review も完了し、current state は terminal accept/no-go for implementation
equivalence。次は broader track decision、new design delta 付き
release/productization design draft、または HOLD。same-scope Phase3 GPU rerun
は unauthorized。後続の current-env productization delta 0GPU も完了し、
Option B `release_after_success_hold_k` は primary のまま、Option A
`hold_to_completion` は comparator/fallback のまま。future release-gate
implementation/preflight と future GPU gate は NOT_AUTHORIZED。さらに
current-env release-gate launch preflight 0GPU も完了し、copied runner は
four-arm / 1476 completions 形を preserve、future command は
`NOT_AUTHORIZED_DO_NOT_RUN` として draft された。この command は後続で
`%7`/Rs proxy により separately authorized され、real `%4` が exactly once
on cuda:0 で実行完了した。結果は
`R2A_TRACK_A_CURRENT_ENV_RELEASE_GATE_GPU_SMOKE_COMPLETE / PRODUCT_GO_FALSE`、
`SUCCESS_REVIEW_REQUIRED / REVIEW_RELEASE_GATE_SMOKE`。1476/1476
completions、`release_after_success_hold_k` high/mixed/low cable_drop は
0.0/0.0/0.0、released high/mixed n=219 success=1.0 cable_drop=0.0
explosion=0.0。ただし active success regression criterion が fail のため
`PRODUCT_GO=false` は維持し、same-scope GPU rerun は unauthorized。
後続の current-env release-gate artifact-only review 0GPU も完了し、
decision は
`CURRENT_ENV_RELEASE_GATE_REVIEW_COMPLETE_RECOMMEND_RELEASE_GATE_CRITERIA_SCHEMA_REVISION_DESIGN_ONLY`。
`release_after_success_hold_k` の v1 active-success-regression failure は、
成功行が released stratum に移動する release-gated arm には不適切な
criteria/schema mismatch と整理された。`kinematic_step30` は real
fixed-release blocker、`hold_to_completion` は comparator/fallback のまま。
後続の current-env release-gate criteria/schema revision 0GPU も完了し、
decision は
`CURRENT_ENV_RELEASE_GATE_SCHEMA_REVISION_DESIGN_COMPLETE_READY_FOR_SEPARATE_V3_POSTHOC_OR_SOURCE_DESIGN_DRAFT_ONLY`。
v3 は execution_status、legacy_v1_diagnostics、
release_gate_mechanism_verdict、active_unreleased_coverage_diagnostics、
comparator_roles、productization_verdict、`PRODUCT_GO`、
`physical_grasp_claim` を分離する。次は separately authorized 0GPU v3
posthoc-summary/source-design draft、broader track/product predicate
decision、または HOLD。

**解決策**: 凹形状指（本体 + 上爪 + 下爪）の BOX composite。
下爪が cable の下に滑り込み、**法線力（normal force）** で cable を持ち上げる。

#### 寸法（create_grooved_finger.py 由来）

| 部品 | 寸法 (mm) | 備考 |
|------|----------|------|
| **本体 (Wall)** | 10.5(X) × 13.0(Y) × 54.0(Z) | Franka default の半分 |
| **下爪 (Lower claw)** | 10.5(X) × 3.0(Y突出) × 0.5(Z厚) | fingertip 側、table方向 |
| **上爪 (Upper claw)** | 10.5(X) × 3.0(Y突出) × 0.5(Z厚) | finger base 側、上方向 |

- 爪は inner face (Y=0) から **-Y方向**（cable側）に 3mm 突出
- URDF座標系: X=width, Y=depth (0=inner), Z=length (0=base, +54=tip)
- hand が下向き時: Z_MAX (tip) = world 下方 (table側)

#### 断面図 (YZ, 閉位置, cable along X)

```
Z [mm]  (world座標, hand下向き時)

  821 ─┤  ┌─upper claw─┐      ┌─upper claw─┐
       │  │             │      │             │
  811 ─┤  │    ╔═cable═╗│      │             │  cable top
       │  │    ║       ║│      │             │
  807 ─┤  │    ║   ●   ║│      │             │  cable center (r=4mm)
       │  │    ║       ║│      │             │
  803 ─┤  │    ╚═══════╝│      │             │  cable bottom
       │  │  Wall    Wall│      │             │
  801 ─┤  │  ┌claw┐┌claw┐      │             │  lower claw top
  800 ─┤  ▓▓▓▓TABLE▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓           │  lower claw bottom = TABLE
       │
       ├──┬──┬──┬──┬──┬──┬──┬──┬──┤
      -8  -6  -4  -2   0   2   4   6   8  Y[mm]
         L-wall    L-claw  R-claw   R-wall
                         cable center
```

- Wall inner face: Y = ±4mm (cable surface に接触)
- Claw tip: Y = ±(4-3) = ±1mm (cable center を 2mm オーバーラップ)
- Contact distance: finger_gap(1mm) + cable_gap(2mm) = 3mm

#### Newton 衝突形状の実装

**問題**: `add_shape_mesh(finger.dae)` → CONVEX_MESH (convex hull) 変換で爪の凹形状が消失。

**解決**: finger body (7, 8) に **3つの BOX primitive** を body-relative xform で付与:

```python
# Per finger body:
# 1. Wall (main body)
add_shape_box(body=finger, xform=identity, hx=W, hy=W, hz=W, cfg=finger_cfg)
# 2. Lower claw (at wall bottom, extends inward toward cable)
add_shape_box(body=finger, xform=lower_xf, hx=C, hy=C, hz=C, cfg=finger_cfg)
# 3. Upper claw (at wall top, extends inward)
add_shape_box(body=finger, xform=upper_xf, hx=C, hy=C, hz=C, cfg=finger_cfg)
```

Visual rendering は finger.dae DAE mesh で別途行う（collision と分離）。

#### 接触パラメータ

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| finger_cfg.ke | 2500 | CABLE_CONTACT_KE |
| finger_cfg.kd | 100 | CABLE_CONTACT_KD |
| finger_cfg.mu | 1.0 | (摩擦は kinematic body で無効だが設定) |
| finger_cfg.gap | 0.001 | 1mm (cable gap 2mm と合わせて contact distance 3mm) |

#### 制約条件

| ID | 制約 | 種別 |
|----|------|------|
| H1 | Claw bottom ≥ TABLE_HEIGHT | Hard (table非貫通) |
| H2 | Claw top + contact_dist > cable bottom | Hard (cable到達) |
| H3 | Wall top > cable top | Hard (vertical containment) |
| H4 | Close時の claw tip overlap > 0 | Hard (cable center を覆う) |
| S1 | Close gap ≥ cable diameter | Soft (wall-cable圧縮を避ける) |

#### 検証結果 (2026-03-30)

| テスト | 爪寸法 | Cable lift | Tracking | 結果 |
|-------|--------|-----------|----------|------|
| test_l_finger_cable_lift.py (large ledge) | 12mm×2mm | 52mm / 50mm target | 103% | PASS |
| **test_l_finger_cable_lift.py (既存claw)** | **3mm×0.5mm** | **48mm / 50mm target** | **96%** | **PASS** |

- 5-segment cable rod, 全セグメント均一 lift (50.3-50.4mm)
- Rod bend stiffness が爪範囲外のセグメントにも力を伝達
- Hold phase 安定 (854mm, drift < 0.3mm)

### 2.4 PD制御ゲイン

| パラメータ | 値 | 単位 | ソース |
|-----------|-----|------|--------|
| ARM_KE (stiffness) | 8000.0 | N·m/rad | task_config.py:53 |
| ARM_KD (damping) | 400.0 | N·m·s/rad | task_config.py:54 |
| FINGER_KE | 2000.0 | N/m | task_config.py:55 |
| FINGER_KD | 100.0 | N·s/m | task_config.py:56 |
| FINGER_EFFORT_LIMIT | 60.0 | N | task_config.py:57 |
| FINGER_ARMATURE | 0.5 | kg·m² | task_config.py:58 |

### 2.5 URDF

- パス: `source/extensions/isaaclab_tasks_thread/data/robots/panda_independent_fingers.urdf`
- DOF: 9 (arm 7 + finger 2)
- 到達半径: 0.855 m

---

## 3. テーブル / ワークスペース

**ソース:** `task_config.py:15`, `test_newton_clip_routing_sdf_plain.py:514-527`

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| TABLE_HEIGHT | 0.80 m | Newton: 無限平面 (z=0.80) |
| 表面摩擦 μ | 1.0 | cable traction用 |
| 接触剛性 ke | 1e4 | Newton ShapeConfig |
| 接触減衰 kd | 1e2 | |
| 接触ギャップ | 0.005 m (5mm) | |

### 3.1 有効ワークスペース（両腕到達可能領域）

| 軸 | 範囲 [m] | 備考 |
|----|---------|------|
| X | 0.0 〜 0.62 | 重複領域 |
| Y | -0.44 〜 +0.46 | 重複領域 |
| Safe X_max | 0.707 | 0.757 - 50mm margin |

---

## 4. ケーブル（Cosserat Rod）

**ソース:** `task_config.py:62-76`

### 4.1 形状

| パラメータ | 値 | 単位 |
|-----------|-----|------|
| CABLE_SEGMENTS | 40 | セグメント数 |
| CABLE_SEG_LEN | 0.015 | m |
| 全長 | 0.600 (40×0.015) | m |
| CABLE_RADIUS | 0.004 | m (直径 8mm) |

### 4.2 剛性・減衰

| パラメータ | 値 | 単位 | 備考 |
|-----------|-----|------|------|
| CABLE_BEND_STIFFNESS | 0.1 | N·m² | EI (曲げ) |
| CABLE_BEND_DAMPING | 0.01 | N·m·s | |
| CABLE_STRETCH_STIFFNESS | 1.0e6 | N | EA (引張、伸び防止) |
| CABLE_STRETCH_DAMPING | 0.0 | N·s | |

### 4.3 接触

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| CABLE_CONTACT_KE | 2500.0 | 接触剛性 |
| CABLE_CONTACT_KD | 100.0 | 接触減衰 |
| CABLE_CONTACT_MU | 1.0 | 摩擦係数 |

### 4.4 初期配置

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| GRASP_X | 0.30 m | ケーブル初期X |
| Cable Z | TABLE_HEIGHT + CABLE_RADIUS ≈ 0.804 m | テーブル面+半径 |

---

## 5. クリップ配置（5クリップ、千鳥）

**ソース:** `task_config.py:79-107`

### 5.1 レイアウトパラメータ

| パラメータ | 値 | 単位 |
|-----------|-----|------|
| CLIP_Y_SPACING | 0.075 | m |
| CLIP_X_ODD (C1,C3,C5) | 0.35 | m |
| CLIP_X_EVEN (C2,C4) | 0.40 | m (+50mm千鳥) |
| CLIP_Y_CENTER | 0.0 | m |
| CLIP_GROOVE_INNER_RADIUS | 0.006 | m |
| P3_X_OFFSET | 0.012 | m |
| GRIP_HALF_SPAN | 0.044 | m (arm-to-arm 88mm) — corrected 2026-06-21 from stale 0.030/60mm (`task_config.py:235` reach-flag resolution 0.060→0.028→0.044) |

### 5.2 各クリップ座標

| Clip | X [m] | Y [m] | Z [m] | 種別 |
|------|-------|-------|-------|------|
| C1 | 0.35 | +0.150 | 0.80 | Odd |
| C2 | 0.40 | +0.075 | 0.80 | Even |
| C3 | 0.35→0.40※ | 0.000 | 0.80 | Odd→Even※ |
| C4 | 0.40 | -0.075 | 0.80 | Even |
| C5 | 0.35 | -0.150 | 0.80 | Odd |

> ※ **Y-labels C1↔C5 / C2↔C4 corrected 2026-06-21** (were Y-mirrored vs `task_config.py:211-216`: routing dir = C1=+Y right-side → C5=−Y left-side, `task_config.py:209`). **C3 X 0.35→0.40 DECIDED 2026-06-21** (off grasp-void; **committed code still C3=0.35, commit DEFERRED** to the table-slot/multi-clip landing — see §10 diagram note + `06-Knowledge/GD-KoShape-Finger.md` "Clip placement resolution"). [%4, records-must-match-fact / human-approved spec reflect]

---

## 6. 高さパラメータ（IKターゲット = panda_hand body6）

**ソース:** `task_config.py:33-37`

| Phase | パラメータ | Body6 Z [m] | Fingertip Z [m] | テーブルからの高さ |
|-------|-----------|-------------|-----------------|-----------------|
| Approach | APPROACH_Z | 1.120 | 0.900 | +100mm |
| Grasp | GRASP_Z | 1.020 | 0.800 | 0mm (テーブル面) |
| Lift | LIFT_Z | 1.120 | 0.900 | +100mm |
| Push | PUSH_Z | 1.020 | 0.800 | 0mm (テーブル面) |

有効GRASP_Z範囲: [1.020, 1.024]（4mmバンド）

---

## 7. モーション制御

**ソース:** `task_config.py:119-124`

| パラメータ | 値 | 単位 |
|-----------|-----|------|
| STEPS_PER_CM | 50 | steps/cm |
| CONVERGE_MM | 2.0 | mm |
| MAX_MOVE_STEPS | 3000 | steps |
| SETTLE_STEPS | 200 | steps |
| FINGER_CLOSE_STEPS | 500 | steps |
| FINGER_STEP_SIZE | 0.001 | m/step |

---

## 8. ソルバー / 物理

**ソース:** `task_config.py:40-48`, `test_newton_clip_routing_sdf_plain.py:69-70`

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| Newton DT | 1/480 s | |
| SIM_SUBSTEPS | 10 | Featherstone substeps/frame |
| GRAVITY | -9.81 | m/s² |
| NJMAX | 64000 | Max constraint rows |
| DISABLE_CONTACTS | False | Capsule接触有効 |

---

## 9. カメラ配置

### 9.1 録画用6カメラ（Newton VBD検証）

**ソース:** `test_newton_clip_routing_sdf_plain.py:97-112`

| カメラ | 位置 (X, Y, Z) [m] | ターゲット (X, Y, Z) [m] | 用途 |
|--------|-------------------|------------------------|------|
| overhead | (0.35, -0.05, 1.50) | (0.35, -0.05, 0.80) | 真上: XY概観 |
| front | (1.00, -0.05, 1.05) | (0.30, -0.05, 0.82) | +X→-X: Z高さ・テーブル貫通 |
| diag_upper | (0.65, -0.40, 1.00) | (0.35, -0.05, 0.82) | 斜め45°上: R-arm遮蔽低減 |
| left | (0.35, -0.65, 0.93) | (0.35, -0.05, 0.82) | -Y→+Y: テーブル+13cm |
| right | (0.35, +0.55, 0.93) | (0.35, -0.05, 0.82) | +Y→-Y: テーブル+13cm |
| clip_close | (0.50, -0.05, 0.83) | (0.35, -0.05, 0.82) | groove水平: 挿入確認 |

**録画パラメータ:**

| パラメータ | 値 |
|-----------|-----|
| 解像度 | 1280 × 960 |
| FPS | 30 (480Hz / 16step) |
| Near Plane | 0.01 m |
| Far Plane | 10.0 m |
| 出力形式 | `ep{N}_{camera}.mp4` (カメラ毎個別) |

**方位計算:** position→target ベクトルから pitch/yaw を自動計算 (`_cam_angles()`)

### 9.2 シーンカラーリング（動画判定用）

**ソース:** `test_newton_clip_routing_sdf_plain.py:301-305`

| 対象 | 色 (RGB) | 視覚的識別 |
|------|----------|-----------|
| Finger | (1.0, 0.2, 0.2) | 赤 — テーブル貫通検出最優先 |
| Table | (0.65, 0.50, 0.35) | タン/茶 — デフォルト色と区別 |
| Hand | (0.3, 0.3, 0.6) | 青灰 — fingerと区別 |
| Clip | 緑系 | — |

### 9.3 RL訓練用TiledCamera（PhysX環境）

**ソース:** `dual_arm_camera_env_cfg.py:179-251`

| カメラ | 取付先 | 解像度 | Focal Length | Clipping |
|--------|-------|--------|-------------|----------|
| Left Wrist | 左EEフレーム | 224×224 | 12.0mm | 0.01-2.0m |
| Right Wrist | 右EEフレーム | 224×224 | 12.0mm | 0.01-2.0m |
| Overhead | ワールド固定 (0.5, 0.0, 1.5) | 640×480 | 18.0mm | 0.1-10.0m |

---

## 10. 空間関係サマリ（俯瞰図）

```
Y [m]
+0.35  ────── Right Arm Base ──────
+0.15  ── C1 (0.35, +0.150) ──────
+0.075 ── C2 (0.40, +0.075) ─千鳥─
 0.00  ── C3 (0.35→0.40※,0.000) ──
-0.075 ── C4 (0.40, -0.075) ─千鳥─
-0.15  ── C5 (0.35, -0.150) ──────
-0.35  ────── Left Arm Base ───────

       0.0   0.30  0.35  0.40     X [m]
             Cable  Odd   Even
             Init   Clips Clips
```

> ※ **C3 X 0.35→0.40 DECIDED 2026-06-21** (human option A) — off the grasp-void X[0.234,0.366]; 2D footprint check: ONLY C3 conflicted (C1/C5 Y-clear 75mm, C2/C4 X-clear 14mm). ⚠ `task_config.py:214` numeric commit **DEFERRED** to the table-slot/multi-clip landing — **committed code still C3=0.35** (decision recorded `06-Knowledge/GD-KoShape-Finger.md` "Clip placement resolution" §).
> **Clip LABELS C1↔C5 / C2↔C4 corrected 2026-06-21** to match `task_config.py:211-216` + `RS71-SSOT:28` (the diagram was Y-mirrored: routing dir is C1=+Y right-side → C5=−Y left-side, `task_config.py:209`). [%4, human-approved spec reflect 2026-06-21]

```
Z [m]
1.50   overhead camera
1.12   APPROACH_Z / LIFT_Z (body6)
1.05   front camera
1.02   GRASP_Z / PUSH_Z (body6)
1.00   diag_upper camera
0.93   left/right cameras
0.90   fingertip at APPROACH_Z
0.83   clip_close camera
0.804  cable center (table + radius)
0.80   TABLE_HEIGHT / fingertip at GRASP_Z
```
