---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: RL Routing Design (Consolidated)
created: '2026-03-28'
consolidated_from:
  - thread-vault/04-Specs/routing_motion_sequence.md
  - thread_isaac_lab/docs/DAPG_DESIGN.md
  - thread-vault/06-Knowledge/LL-3Skill-UnifiedDesign.md
  - thread-vault/06-Knowledge/LL-P1-Sequential-DualArm.md
tags:
  - design
  - rl
  - routing
  - dapg
  - skill
---

# RL Routing Design

> 5-clip dual-arm cable routing の RL 設計統合文書。
> 工程設計・スキル設計・訓練パイプライン・DR を1箇所にまとめる。
>
> **確定日:** 2026-03-26 (DAPG), 2026-03-27 (3スキル統合, P1分割), 2026-03-28 (43ステップ化: L固定ステップ+R-hand X修正), 2026-04-05 (クランプ/アンクランプ独立RL化)

---

## Current R2-A Track A State (2026-05-27)

Track A kinematic predicate is a terminal diagnostic, not a product solution.
The current NEST position is
`R2A_TRACK_A_S1B_COLLECTION_EXACT_COMMAND_GATE_AFTER_PROVENANCE_MUTATION_0GPU_COMPLETE /
S1B_COLLECTION_EXACT_COMMAND_AFTER_PROVENANCE_MUTATION_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED /
PRODUCT_GO_FALSE` as observed from `%4`'s completed report on
`2026-05-27`, with relay finalizing the checksum manifest and verifying at
`2026-05-27T16:38:00+09:00` after `%4` stalled before final report, and `%3`
returning package-level Tier-A COMPLETE at `2026-05-27T16:54:21+09:00`, followed
by `%4` completing the bounded exact-command/runtime review at
`2026-05-27T17:19:28+09:00` and `%3` returning exact-runtime Tier-A INCOMPLETE
at `2026-05-27T17:43:31+09:00`, then `%4` completing the prior-scout outcome
disclosure gapfix at `2026-05-27T17:55+09:00`, followed by `%3` returning
disclosure-gapfix Tier-A COMPLETE at `2026-05-27T18:10:04+09:00` and combined
exact-GO Tier-A COMPLETE at `2026-05-27T18:20:40+09:00`, then `%4` completing
one authorized cuda:0 runtime field/schema confirmation attempt at
`2026-05-27T18:29:49+09:00`, followed by `%3` result review COMPLETE at
`2026-05-27T18:46:42+09:00`, then S1A negative-retention strategic disposition
complete at `2026-05-27T19:08:00+09:00`, S1B data/label feasibility audit
complete at `2026-05-27T19:18:00+09:00`, and S1B data-label contract complete
at `2026-05-27T19:58:24+09:00`, then S1B collection schema patch package
complete at `2026-05-27T20:10:01+09:00`, followed by `%3` Tier-A review
complete at `2026-05-27T20:33:57+09:00`, and S1B exact source diff package
complete at `2026-05-27T21:08:42+09:00`, followed by `%3` exact-diff Tier-A
review complete at `2026-05-27T21:21:00+09:00`, and S1B collector source
mutation complete at `2026-05-27T21:50:00+09:00`, followed by the collection
exact-command gate package at `2026-05-27T22:00:00+09:00`, the env-cfg arg
source-diff package, env-cfg arg source mutation, collection exact-command gate
after env-cfg mutation, `%3` exact-command Tier-A COMPLETE at
`2026-05-27T23:02:00+09:00`, and exactly one authorized cuda:0 S1B collection
smoke complete at `2026-05-27T23:12:00+09:00`, followed by S1B labeled NPZ
artifact review complete at `2026-05-27T23:24:00+09:00`, and S1B zero-release
root-cause redesign complete at `2026-05-27T23:36:00+09:00`, followed by S1B
collector provenance terminal-step exact diff package complete at
`2026-05-27T23:58:00+09:00`, `%3` provenance exact-diff Tier-A COMPLETE at
`2026-05-28T00:04:30+09:00`, and S1B collector provenance terminal-step source
mutation complete at `2026-05-28T00:21:16+09:00`, followed by S1B collection
exact-command gate after provenance mutation complete at
`2026-05-28T00:34:11+09:00`. A bounded
env-only/default-off S1A source mutation is on disk at env SHA
`c45771d1eaa5370b41192241ddd5f802a9f3136f7ab4540b36d02e6fb0e5f4f2`. The exact
baseline preimage `87875a488a96338f4b8836e82b750252f4054e83e5e6a80d56715ae21002e0db`
was reconstructed, `%3` accepted the true diff, static import passed, one
bounded cuda:0 construction/reset/one-step default-off check passed, and one
separately authorized cuda:0 S1A-enabled E0 construction/reset/one-step schema
check passed. Enabled E0 confirms only construction and wiring: `num_obs=52`,
obs shape `[41,52]`, finite obs/reward, S1A metadata present, S1A reward mean
zero at step 0, kinematic support false, product scoring/credit false, and
protected SHAs unchanged. Product success remains `0`; `PRODUCT_GO=false`;
`cc6_null_hypothesis_falsified=false`.

The latest 0GPU redesign package is under
`eval_runs/r2a_track_a_s1b_collection_zero_release_root_cause_redesign_0gpu_20260527/`.
It classifies the S1B smoke as pre-release termination before scheduled release,
not release-without-retention: actual releases `0/41`, all rows
`aborted_before_release`, transition step max `47` before command release step
`80`, terminal reasons `cable_drop=22`, `explosion=11`, `clamp_loss=3`,
`unspecified=5`, and `configured_release_step=-1` because the collector does not
persist the configured release step into no-release S1B label rows. Recommended
next route is
`BOUNDED_0GPU_S1B_COLLECTOR_PROVENANCE_TERMINAL_STEP_PATCH_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.
No collection rerun, mutation, training, product claim, sim2real claim,
T-ROOT95 claim, Stage-2 claim, or cuda:1 use is authorized.

The collector provenance mutation package is under
`eval_runs/r2a_track_a_s1b_collector_provenance_terminal_step_source_mutation_20260528/`.
After `%3` accepted the exact diff, `%4` applied the collector-only
`SOURCE_DIFF.patch` to `thread_isaac_lab/scripts/collect_aerial_regrasp_demos.py`.
Collector SHA changed from
`20eda9cb55f3468bbfc79b84567ea142020f4e82b3956279fe6c88b13d0f4c8a` to
`8516a23c3501468a0bc057da16fd8e04664d7b0fea86c3ac5899d0217661b582`.
The mutation persists configured release step from reviewed env-cfg for every
S1B row, preserves observed release step as actual-release metadata, adds
`terminal_step`, `first_done_step`, `terminal_before_configured_release`,
`steps_until_configured_release`, and `terminal_break_reason_source`, adds direct
`schema_version`, `policy_id`, `runner_sha`, and `dataset_source` aliases, and
preserves no-crutch/no-product-positive semantics. Current next route is
`SUPERVISOR_TIERA_REVIEW_FOR_S1B_COLLECTION_EXACT_COMMAND_AFTER_PROVENANCE_MUTATION_OR_HOLD`.

The post-provenance exact-command gate package is under
`eval_runs/r2a_track_a_s1b_collection_exact_command_gate_after_provenance_mutation_0gpu_20260528/`.
It is 0GPU/no-run/no-mutation and only prepares a future exact command for
separate `%3` Tier-A review. The guarded command exits `64` before launch, binds
collector SHA `8516a23c3501468a0bc057da16fd8e04664d7b0fea86c3ac5899d0217661b582`,
uses cuda:0 only, preserves the prior envelope (`world_count=41`, seed `42`,
max_steps `140`, hold_steps `30`, warmup_steps `5`, retention horizon `30`),
and records the future output root as absent. It carries forward the prior
negative S1B smoke outcome (`0/41` actual releases, transition max `47` before
release step `80`) and makes no efficacy, product, physical-grasp, sim2real,
T-ROOT95, Stage-2, or training claim.

`%4` completed the retained-threshold provenance audit under
`eval_runs/r2a_track_a_s1a_cc6_threshold_provenance_audit_0gpu_20260527/`.
The audit found the retained-after-release baseline `40/77 = 0.5194805195` is
evidence-backed, while the `+0.15` margin did not trace to an earlier explicit
Rs/R1/product-predicate decision. Rs/TL explicitly selected `+0.15` as a
diagnostic CC6 null-hypothesis margin only. Therefore `0.6694805195` may be
carried forward as `RS_TL_SELECTED_DIAGNOSTIC_THRESHOLD`, not as product
success, physical-grasp success, sim2real-success, T-ROOT95, Stage-2, or
production-GO evidence. Future artifacts must split baseline evidence, selected
diagnostic margin, and derived diagnostic threshold.

At `2026-05-27T15:28+09:00`, `%7` routed and real `%4` ACKed a bounded
0GPU/no-run/no-mutation release-horizon scout design directive. After `%3`
Tier-A review found no blocking gap, `%7` authorized exactly one cuda:0
diagnostic scout attempt, and `%4` completed it under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_scout_gpu_diagnostic_20260527/`.
The exact scoped run exited `0` with no timeout or retry (`85s` wall time,
`74.03s` summary elapsed, `70.89` steps/s), using `world_count=41`,
`max_iterations=1`, `num_steps_per_env=128`, `seed=42`, and cuda:0 only. It
captured new runtime evidence: actual releases `3/41 = 0.0731707317`,
retained-after-release `0/3 = 0.0`, all-world cable_drop `40/41 =
0.9756097561`, all-world explosion `35/41 = 0.8536585366`, derived
release-normalized cable_drop `2/3 = 0.6666666667`, and derived
release-normalized explosion `1/3 = 0.3333333333`. The threshold comparison is
diagnostic only: retained-after-release `0.0` is below the Rs/TL-selected
diagnostic threshold `0.6694805195`, but this is not an efficacy proof,
product result, physical-grasp result, sim2real-success claim, T-ROOT95 claim,
Stage-2 claim, or training result. Product success remains `0`; `PRODUCT_GO`
remains `false`.

Remaining scout gaps are explicit: observed release-step distribution was not
emitted; first-class actual-release-denominator-normalized cable_drop/explosion
fields were not emitted; cable_drop/explosion non-inferiority thresholds remain
`REVIEW_REQUIRED`; and any later efficacy pilot budget, seed policy, or exact
GO/HOLD decision remains unauthorized.

`%4` then completed the bounded 0GPU artifact-only schema-gap review under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_scout_schema_gap_review_0gpu_20260527/`.
Primary decision:
`SCOUT_ARTIFACT_REVIEW_CONFIRMS_SCHEMA_GAPS_RECOMMEND_0GPU_SCHEMA_PATCH_PACKAGE_NOT_AUTHORIZED`.
The review confirmed that `observed_release_step_distribution` is absent from
`summary.json` and cannot be recovered from existing artifacts because the raw
per-world schema-v2 records were not persisted. First-class
actual-release-denominator-normalized cable_drop/explosion fields are also
absent. The release-class split fields permit derived diagnostics only:
`cable_drop_by_release_class.scheduled_d0_release_event_applied=2` over
`actual_release_denominator=3`, and
`explosion_by_release_class.scheduled_d0_release_event_applied=1` over
`actual_release_denominator=3`. These are not sufficient by themselves as
non-inferiority threshold sources, and no cable_drop/explosion thresholds were
invented. The clean next route is
`BOUNDED_0GPU_RELEASE_HORIZON_SCHEMA_PATCH_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.

`%4` then generated that bounded 0GPU schema patch package under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_schema_patch_package_0gpu_20260527/`.
It creates only a fresh eval-runs-local copied runner, SHA
`117b6d0f0ee0b77c1868857da25bcdb9958ed1311e9c3ff67f6f829a0057163d`, with
`SOURCE_DIFF.patch` SHA
`79f53980ff71aaaf2cc9e2b75511637ec6bfca2f87434393cef48e79f92b6667`. `%4`
validated py_compile, direct future-run refusal with exit `64`, synthetic
release-horizon fields, protected locks, and GPU idle state, then stalled
before final report and before writing `SHA256SUMS.txt`; `%7` added the
manifest and independently verified checksum self-check, JSON parse, protected
SHAs/diff, direct refusal, no checkpoint/pycache residue, and GPU idle state.
The patch adds `observed_release_step_distribution`, bounded per-world
schema-v2 record persistence with limit `64`, and first-class
actual-release-denominator-normalized cable_drop/explosion count/denominator/
rate fields. It preserves release-class split diagnostics, product-credit
refusal, no-crutch flags, and false product/scoring/routing claims. No
thresholds, execution, training, protected source mutation, product claim,
physical/sim2real/T-ROOT95/Stage-2 claim, or cuda:1 use is authorized. `%3`
then returned `RELEASE_HORIZON_SCHEMA_PATCH_TIERA_REVIEW_COMPLETE`: the package
is sufficient as the basis for a later exact-command/runtime route, with no
package-level blocking gap, but this is not execution authorization. Carried
conditions are: release-normalized safety fields are ever-flag rates unless a
later route uses bounded post-release records or adds explicit release-caused
safety fields; real runtime `extras["log_per_world"]` emission remains to be
confirmed; record limit `64` is sufficient for the current 41-world scout only;
and no-crutch, horizon-continuity, diagnostic-threshold-only, and full GPU gate
constraints remain binding. That clean next route was
`BOUNDED_0GPU_RELEASE_HORIZON_EXACT_COMMAND_RUNTIME_REVIEW_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.

`%4` then completed that bounded 0GPU exact-command/runtime review under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_exact_command_runtime_review_0gpu_20260527/`.
Decision:
`RELEASE_HORIZON_RUNTIME_ROUTE_EXACT_COMMAND_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`.
The route binds a future runtime-confirmation envelope for `%3` review only:
cuda:0, world_count `41`, max_iterations `1`, num_steps_per_env `128`, seed
`42`, timeout `3600`, fresh future output root absent, direct draft guard exit
`64`, and protected SHAs unchanged. It remains not efficacy readiness and not
product evidence. Real runtime `extras["log_per_world"]` confirmation,
release-caused safety semantics, cable_drop/explosion thresholds, and any exact
GO stay outside this package. At that point the next route was:
`SUPERVISOR_TIERA_EXACT_COMMAND_REVIEW_FOR_RELEASE_HORIZON_RUNTIME_ROUTE_NOT_AUTHORIZED_OR_HOLD`.

`%3` then marked the exact-runtime Tier-A review INCOMPLETE. The blocker is not
artifact mechanics: checksum, JSON, guarded draft exit `64`, protected SHAs, and
GPU idle all passed. The gap is decision-basis disclosure. The package cites the
prior same-envelope scout for the `85s` timing/GPU-hour estimate but does not
surface that same scout's raw outcome: retained_after_release_rate `0.0`
(`0.0 < 0.6694805195` diagnostic threshold), actual releases `3/41`,
release-normalized cable_drop `2/3`, and release-normalized explosion `1/3`.
Because the schema patch only changes emission, a future rerun must be framed as
runtime field/schema confirmation, not efficacy measurement. The then-next route was:
`BOUNDED_0GPU_PRIOR_SCOUT_OUTCOME_DISCLOSURE_GAPFIX_NOT_AUTHORIZED_OR_HOLD`.

`%4` then completed the bounded 0GPU/no-run prior-scout outcome disclosure
gapfix under
`eval_runs/r2a_track_a_s1a_cc6_prior_scout_outcome_disclosure_gapfix_0gpu_20260527/`.
Decision:
`PRIOR_SCOUT_OUTCOME_DISCLOSED_FOR_RUNTIME_REVIEW_BASIS_NOT_AUTHORIZED`.
The decision basis now explicitly includes the same-envelope negative outcome:
retained-after-release `0/3 = 0.0`, diagnostic threshold `0.6694805195`
(`FAIL`), actual releases `3/41`, release predicate never reached `38/41`,
release-normalized cable_drop `2/3`, and release-normalized explosion `1/3`.
The gapfix also states the narrow value of any schema-patched rerun:
field/schema emission confirmation only, not efficacy measurement and not
product evidence. `%3` then returned
`RELEASE_HORIZON_EXACT_RUNTIME_DISCLOSURE_GAPFIX_TIERA_REVIEW_COMPLETE`: the
named disclosure gap is closed, with all three review questions passing. This is
not execution GO. Any future exact-GO Tier-A review must bind both the original
exact-command/runtime package and this disclosure delta. The then-next route was
`COMBINED_SUPERVISOR_TIERA_EXACT_GO_REVIEW_FOR_RELEASE_HORIZON_RUNTIME_FIELD_SCHEMA_CONFIRMATION_NOT_AUTHORIZED_OR_HOLD`.

`%3` then returned `RELEASE_HORIZON_COMBINED_EXACT_GO_TIERA_REVIEW_COMPLETE`.
The exact command is gate-complete as a basis for a later Rs/TL launch decision
only. Residual caveats remain binding: Rs/TL explicit authorization, immediate
TOCTOU checks before launch, one attempt only, no cuda:1, and field/schema
confirmation only. The then-next route was
`RS_TL_DECISION_AUTHORIZE_ONE_RELEASE_HORIZON_RUNTIME_FIELD_SCHEMA_CONFIRMATION_ATTEMPT_OR_HOLD`.

Rs/TL then authorized exactly one cuda:0 runtime field/schema confirmation
attempt, and `%4` completed it under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_schema_v2_runtime_gpu_diagnostic_20260527/`
with review artifacts under
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_schema_v2_runtime_gpu_diagnostic_review_20260527/`.
Decision:
`SCHEMA_V2_RUNTIME_FIELD_SCHEMA_CONFIRMATION_COMPLETE_NEGATIVE_RETENTION_OUTCOME_DIAGNOSTIC_ONLY`.
The schema-v2 fields emitted successfully in real runtime: observed
release-step distribution, bounded per-world records `41/41` with no truncation,
first-class release-normalized cable_drop/explosion fields, and real
`extras["log_per_world"]` compatibility. The outcome remains negative and
diagnostic only: retained-after-release `0/4 = 0.0`,
release-normalized cable_drop `3/4 = 0.75`, release-normalized explosion
`3/4 = 0.75`, product success `0`, and `PRODUCT_GO=false`. The then-next
supervisor result-review route has now completed.

`%3` then returned `SCHEMA_V2_RUNTIME_RESULT_REVIEW_COMPLETE`: field/schema
confirmation is accepted as real-runtime PASS, no claims or locks were violated,
and the negative retention outcome is correctly diagnostic-only. `%3` also
flagged run-to-run nondeterminism in release/drop/explosion under the same
seed/envelope, so single-run safety rates cannot become thresholds; retention
`0.0` is consistent across both runs and is the decisive no-go fact for this
candidate. Rs/TL then completed the S1A negative-retention strategic
disposition package: the field/schema branch is diagnostic PASS but
retention-negative/product-false, full S1A training efficacy was not measured,
and a CC6 efficacy pilot is not authorized from current evidence. That S1B
feasibility route has now completed.

Rs/TL then completed that S1B audit. Existing AR demos are not sufficient for
release-retention BC/DAPG: 18 AerialRegrasp NPZ files were inspected, zero
contain release-retention/no-crutch labels, two contain only `episode_success`,
and the large S1A demo `aerial_regrasp_demos_v12_45d.npz` has only
`obs/actions`.

Rs/TL then completed the bounded 0GPU/no-run/no-mutation S1B data-label
contract under `eval_runs/r2a_track_a_s1b_data_label_contract_0gpu_20260527/`.
The contract requires actual release, observed release step, release class,
post-release retention horizon, post-release cable_drop, post-release explosion,
no-crutch provenance, and real-observability mapping before future collection or
training can be considered. It explicitly excludes `episode_success`,
active-at-completion, hold-to-completion, kinematic/hidden/fixed support,
`inv_mass=0`, direct sim-state writes, and any label with no real-robot proxy
from product-facing positive labels. Current next route is
`BOUNDED_0GPU_S1B_COLLECTION_SCHEMA_PATCH_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.

Rs/TL then completed the bounded 0GPU/no-run/no-mutation S1B collection schema
patch package under
`eval_runs/r2a_track_a_s1b_collection_schema_patch_package_0gpu_20260527/`.
It identifies the future source/runner patch surface without applying it:
`collect_aerial_regrasp_demos.py` must stop defaulting to `cuda:1`, opt in to
S1B label emission, read raw `extras["log_per_world"]`, persist
transition-to-episode mapping and episode/world release-retention labels, and
fail closed on missing release/no-crutch/real-observability evidence. Training
loader changes are deferred to a later label-aware training route. Current next
route is
`SUPERVISOR_TIERA_REVIEW_FOR_S1B_COLLECTION_SCHEMA_PATCH_SOURCE_MUTATION_OR_HOLD`.

`%3` then completed the Tier-A review of the S1B collection schema spec
package. The package is COMPLETE as a spec/contract basis for proceeding toward
a separate bounded source/runner mutation review, but mutation review itself
requires exact unified diffs and is not complete. Required next-gate conditions
are exact diff per target script, TOCTOU SHA re-check, in-place-vs-copy decision,
L-triage for training code, and line-by-line review of fail-closed behavior and
cuda:1 refusal. That route has now advanced.

Rs/TL then completed the bounded 0GPU/no-run/no-mutation exact source diff
package under
`eval_runs/r2a_track_a_s1b_exact_source_diff_package_0gpu_20260527/`.
It provides an eval-runs-local draft collector copy plus `SOURCE_DIFF.patch`
against `collect_aerial_regrasp_demos.py`. The proposed collector-only diff
defaults/refuses away from `cuda:1`, adds opt-in S1B release-retention label
emission, derives release from raw per-world telemetry, persists
transition-to-episode mapping and episode/world label arrays, requires
provenance SHAs and real-observability attestation, and keeps product/physical/
sim2real/T-ROOT95/Stage-2 flags false. Converter and training changes are
deferred; source mutation and training remain unauthorized. Current next route
was `SUPERVISOR_TIERA_REVIEW_FOR_S1B_EXACT_SOURCE_DIFF_PACKAGE_OR_HOLD`.

`%3` then completed that review with
`S1B_EXACT_SOURCE_DIFF_TIERA_REVIEW_COMPLETE`. The package is complete for a
separate collector source mutation decision, but still does not authorize source
mutation. Carry-forward conditions: re-check collector SHA immediately before
any mutation; consciously accept the behavior change of `cuda:1` refusal,
`cuda:0` default, and unconditional seeding; keep converter/training no-change
and deferred; keep all product, physical, sim2real, T-ROOT95, Stage-2, and
training claims false. Current next route is
`RS_TL_DECISION_AUTHORIZE_BOUNDED_S1B_COLLECTOR_SOURCE_MUTATION_OR_HOLD`.

Rs/TL then authorized and `%4` completed the bounded collector-only source
mutation. The reviewed diff was applied only to
`thread_isaac_lab/scripts/collect_aerial_regrasp_demos.py`; collector SHA is
now `0cdbc9b3324b7775d9e1012edfcda2b43b35886141f56095ea3c1e4114cddcfa`.
Converter/training files, task_config, env, and w41 cache stayed unchanged.
Validation passed with `py_compile`, protected diff empty, and GPU idle. No
collector execution, data generation, training, product claim, physical claim,
sim2real claim, T-ROOT95 claim, Stage-2 claim, or cuda:1 use occurred. Current
next route was
`BOUNDED_0GPU_S1B_COLLECTION_EXACT_COMMAND_GATE_PACKAGE_OR_HOLD_NOT_AUTHORIZED`.

Rs/TL then completed that bounded 0GPU gate package. The result is
`COLLECTION_COMMAND_NOT_LAUNCH_READY_COLLECTOR_CFG_ARG_SOURCE_GAP_REQUIRED_NO_RUN`:
the collector can persist S1B labels, but it has no reviewed CLI/env-cfg path to
enable D0/S1A release telemetry. Without a D0 product release arm in env cfg,
`s1a_post_release_phase` remains zero and a collection run would be
non-informative for actual-release/retained-after-release labels. Current next
route is
`BOUNDED_0GPU_S1B_COLLECTOR_ENV_CFG_ARG_SOURCE_DIFF_PACKAGE_OR_HOLD_NOT_AUTHORIZED`.

Rs/TL then completed the bounded 0GPU/no-run/no-mutation collector env-cfg arg
source-diff package. The proposed exact collector-only diff adds
`--env-cfg-json`, validates an allowlisted D0/S1A release-telemetry cfg, fails
closed unless S1B labels have a D0 product release arm plus
`d0_human_rs_predicate_confirmed=true` and
`s1a_curriculum_metadata_enabled=true`, passes the cfg into
`NewtonAerialRegraspEnv`, and persists cfg provenance. Status:
`R2A_TRACK_A_S1B_COLLECTOR_ENV_CFG_ARG_SOURCE_DIFF_PACKAGE_0GPU_COMPLETE /
PRODUCT_GO_FALSE`. Decision:
`ENV_CFG_ARG_EXACT_COLLECTOR_DIFF_PACKAGED_READY_FOR_SUPERVISOR_TIERA_MUTATION_REVIEW_SOURCE_MUTATION_NOT_AUTHORIZED`.
Current next route is
`SUPERVISOR_TIERA_REVIEW_FOR_S1B_COLLECTOR_ENV_CFG_ARG_SOURCE_DIFF_PACKAGE_OR_HOLD`.

Supervisor `%3` returned
`S1B_ENV_CFG_ARG_SOURCE_DIFF_TIERA_REVIEW_COMPLETE`. Rs/TL accepted the
carry-forward conditions and applied the reviewed exact diff only to
`thread_isaac_lab/scripts/collect_aerial_regrasp_demos.py`. Collector SHA is now
`20eda9cb55f3468bbfc79b84567ea142020f4e82b3956279fe6c88b13d0f4c8a`.
`task_config.py`, `newton_aerial_regrasp_env.py`, and the w41 cache remained
unchanged. Status:
`S1B_COLLECTOR_ENV_CFG_ARG_SOURCE_MUTATION_COMPLETE / PRODUCT_GO_FALSE`.
Decision:
`REVIEWED_ENV_CFG_ARG_COLLECTOR_EXACT_DIFF_APPLIED_SOURCE_MUTATION_ONLY_NO_RUN`.
No collector run, data generation, GPU/sim/env launch, training, product claim,
physical claim, sim2real claim, T-ROOT95 claim, Stage-2 claim, or cuda:1 use
occurred. Current next route is
`BOUNDED_0GPU_S1B_COLLECTION_EXACT_COMMAND_GATE_PACKAGE_AFTER_ENV_CFG_MUTATION_OR_HOLD_NOT_AUTHORIZED`.

Rs/TL then completed the bounded 0GPU/no-run/no-mutation exact-command gate
package for an S1B labeled collection smoke after env-cfg mutation. The command
is recorded only in a guarded script that exits `64`; it is ready for supervisor
Tier-A review but not launch-authorized. Status:
`R2A_TRACK_A_S1B_COLLECTION_EXACT_COMMAND_GATE_AFTER_ENV_CFG_MUTATION_0GPU_COMPLETE /
PRODUCT_GO_FALSE`. Decision:
`S1B_COLLECTION_EXACT_COMMAND_READY_FOR_SUPERVISOR_TIERA_REVIEW_NOT_AUTHORIZED`.
At that point the next route was
`SUPERVISOR_TIERA_REVIEW_FOR_S1B_COLLECTION_EXACT_COMMAND_AFTER_ENV_CFG_MUTATION_OR_HOLD`.

Supervisor `%3` then returned
`S1B_COLLECTION_EXACT_COMMAND_TIERA_REVIEW_COMPLETE`. Rs/TL authorized exactly
one cuda:0 S1B collection smoke, and `%4` completed it once under
`eval_runs/r2a_track_a_s1b_collection_smoke_after_env_cfg_20260527/`. The run
exited `0`, did not time out, and produced
`results/aerial_regrasp_s1b_labeled_demos_smoke.npz` with SHA
`04039ce73c1318433b61df1ced80988d91bc1712190f61514cb06e2c4e3f98dc`. It is
schema/runtime evidence only: 41 episodes, 688 transitions, collector success
`22/41`, actual release events `0/41`, retained-after-release labels `0/41`,
and release class `aborted_before_release` for all rows. The S1B label and
provenance fields are present, but the data does not support training
sufficiency, retention efficacy, product success, physical-grasp success,
sim2real success, T-ROOT95, or Stage-2. Current next route is
`BOUNDED_0GPU_ARTIFACT_REVIEW_OF_S1B_LABELED_NPZ_ZERO_RELEASE_OUTCOME_OR_HOLD_NOT_AUTHORIZED`.

`%4` then completed the bounded 0GPU S1B labeled NPZ artifact review under
`eval_runs/r2a_track_a_s1b_labeled_npz_artifact_review_0gpu_20260527/`.
Decision:
`ZERO_RELEASE_SCHEMA_SMOKE_VALID_NEGATIVE_ONLY_NOT_TRAIN_READY_RECOMMEND_0GPU_COLLECTION_ZERO_RELEASE_ROOT_CAUSE_REDESIGN_NOT_AUTHORIZED`.
The review validates the NPZ as a schema/runtime artifact but rejects it as
positive S1B training data. It found actual release events `0/41`, release class
`aborted_before_release` for all rows, observed release step `-1` for all rows,
retained-after-release labels `0/41`, terminal reasons `cable_drop=22`,
`explosion=11`, `clamp_loss=3`, `unspecified=5`, and transition step max `47`,
which is before the configured release step `80` in the command. The review also
identified a semantic gap: `configured_release_step` is persisted as `-1` for
all rows despite command env-cfg requesting release step `80`. Current next
route is
`BOUNDED_0GPU_S1B_COLLECTION_ZERO_RELEASE_ROOT_CAUSE_REDESIGN_NOT_AUTHORIZED_OR_HOLD`.

The next-route preparation advanced through entrypoint, high-cost, and
exact-approval packages, then a numeric-log-adapter entrypoint smoke completed
one bounded 1-iteration cuda:0 attempt. `%4` artifact review accepted entrypoint
viability as plumbing evidence only and found that `summary.json` lacked
numeric-log-adapter provenance. `%4` then completed a 0GPU schema review and
patch package. The patch package creates only a new eval-runs-local patched
copy, keeps the existing adapter entrypoint unchanged, adds schema v1 summary
provenance support, passes py_compile and static/synthetic adapter-provenance
checks, and leaves the future command draft guarded by `exit 64`. `%3` returned
schema-v1 Tier-A review `COMPLETE` for decision-basis sufficiency only, not GO:
the patch is runner-only/additive, preserves cuda:0 bounds and protected locks,
and adds provenance without changing the already validated numeric-log split.
`%3` also classified a patched-copy re-smoke as optional / low marginal value,
because it would only enrich provenance and not advance CC6 efficacy. No
follow-on GPU, runner execution, training, retry/rerun, protected mutation,
product, physical-grasp, sim2real-success, T-ROOT95, Stage-2, or cuda:1 route is
authorized.

`%4` then completed the bounded 0GPU/no-run CC6 efficacy gate package under
`eval_runs/r2a_track_a_s1a_cc6_efficacy_gate_package_0gpu_20260527/`. It binds
baseline actual releases `77`, retained-after-release `40`, baseline rate
`0.5194805195`, and threshold `0.6694805195`; it also carries schema-v1 adapter
provenance forward. cable_drop and explosion non-inferiority thresholds remain
`REVIEW_REQUIRED` because the existing summaries do not support defensible exact
thresholds. The package is not launchable and any CC6 efficacy pilot remains a
separate supervisor Tier-A/high-cost exact-GO decision, or HOLD.

`%4` then completed the bounded 0GPU/no-run exact-command review package under
`eval_runs/r2a_track_a_s1a_cc6_efficacy_exact_command_review_0gpu_20260527/`.
It is explicitly not launch-ready: the package binds command path, schema-v1
adapter SHA, cuda:0 policy, `world_count=41`, and the CC6 metric contract, but
timeout, expected GPU-hours, `max_iterations`, `num_steps_per_env`,
seed/replicate policy, fresh future output root, and cable_drop/explosion
non-inferiority thresholds remain `REVIEW_REQUIRED`. The correct next route is
0GPU launch-parameter and safety-threshold design, or HOLD; no execution is
authorized.

`%4` then completed that bounded 0GPU design under
`eval_runs/r2a_track_a_s1a_cc6_launch_parameter_safety_threshold_design_0gpu_20260527/`.
It resolves the future output-root convention and the required post-run summary
assertion contract, but launch remains not ready. The remaining blockers are
timeout/hard wall, estimated GPU-hours, `max_iterations`, `num_steps_per_env`,
seed/replicate policy, and cable_drop/explosion thresholds. The latter are
blocked by a data-schema gap in existing artifacts: normalized cable_drop and
explosion count/rate fields are not available for defensible non-inferiority
thresholds.

`%4` then completed the bounded 0GPU budget/safety-schema closure package under
`eval_runs/r2a_track_a_s1a_cc6_budget_safety_schema_design_0gpu_20260527/`.
It defines schema-v2 requirements and preserves the baseline contract (`40/77`,
rate `0.5194805195`, threshold `0.6694805195`), but still refuses launch-ready
status: timeout, GPU-hours, iterations, steps, seed policy, and cable_drop /
explosion thresholds remain `REVIEW_REQUIRED`. Existing artifacts cannot compute
the normalized cable_drop/explosion thresholds needed for non-inferiority; no
launch command was emitted. The next clean route is a bounded 0GPU schema-v2
summary patch package, or HOLD.

`%4` then completed the bounded 0GPU schema-v2 summary patch package under
`eval_runs/r2a_track_a_s1a_cc6_schema_v2_summary_patch_package_0gpu_20260527/`.
It creates only an eval-runs-local patched copy,
`run_s1a_enabled_train_aerial_regrasp_numeric_log_adapter_schema_v2_DRAFT_NOT_AUTHORIZED.py`,
SHA `52786112b6179d32a52eb1875c959fcfb01714e1133b0f32b1fc9b4d84c48591`. The
existing schema-v1 adapter is not modified in place. The copy adds normalized
cable_drop/explosion counts, denominators, rates, release-class/condition
splits, no-crutch flags, actual-release and retention fields, numeric-log
adapter provenance, and `product_success_count=0`; missing cable_drop/explosion
booleans fail closed. Direct future-run invocation without an exact-GO env var
returns `64` before env construction. The schema-v2 data-shape gap is now
closed, but the command is still not launch-ready because timeout, GPU-hours,
iterations, steps, and seed/replicate policy remain `REVIEW_REQUIRED`. The next
clean route is budget-parameter design, or HOLD.

`%4` then completed the bounded 0GPU budget-parameter design package under
`eval_runs/r2a_track_a_s1a_cc6_budget_parameter_design_0gpu_20260527/`.
It is explicitly fail-closed for a CC6 efficacy pilot: timeout, estimated
GPU-hours, `max_iterations`, `num_steps_per_env`, and seed/replicate policy
remain `REVIEW_REQUIRED` because the available runtime evidence covers only
one-iteration plumbing. The package supports only a separately reviewed
schema-v2 budget-calibration scout envelope (`timeout=3600`,
`max_iterations=1`, `num_steps_per_env=8`, `world_count=41`, `seed=42`,
`cuda:0`). That scout would be runtime/provenance calibration only, not efficacy
evidence, product evidence, or strategic-routing evidence. The next clean route
was HOLD or a supervisor Tier-A review for that calibration scout; no efficacy
launch was ready.

`%4` then completed a bounded 0GPU calibration-scout necessity review under
`eval_runs/r2a_track_a_s1a_cc6_schema_v2_calibration_scout_necessity_review_0gpu_20260527/`.
Primary decision: `SCOUT_NOT_INFORMATIVE_NO_RELEASE_FIELDS`. The proposed
same-envelope scout cannot reach the configured release step
(`num_steps_per_env=8` vs `d0_control_release_step=80`) and the current
env/adapter path does not produce `cc6_safety_schema_v2_records`, so it cannot
emit real release, retained-after-release, cable_drop/explosion, or CC6
denominator evidence. The schema-v2 helper itself is already covered by
static/synthetic checks. The next clean route is HOLD or a 0GPU
schema-v2 field-emission source/static audit; no GPU, runner execution,
training, product scoring, or mutation is authorized.

`%4` then completed that bounded 0GPU field-emission source/static audit under
`eval_runs/r2a_track_a_s1a_cc6_schema_v2_field_emission_source_static_audit_0gpu_20260527/`.
Primary decision: `RUNNER_COPY_PATCH_REQUIRED_NOT_AUTHORIZED`. The audit found
that protected env mutation is not required by static evidence: the env already
emits the raw per-world release/control, S1A post-release, cable_drop,
explosion, no-crutch, and product-credit refusal surfaces. The missing piece is
that the eval-runs-local schema-v2 adapter copy does not collect
`extras["log_per_world"]` into `cc6_safety_schema_v2_records`. The next clean
route is HOLD or a bounded 0GPU runner/adapter copy patch package; no protected
source mutation, GPU, runner execution, training, product scoring, or strategic
routing is authorized.

`%4` then completed a bounded 0GPU runner-copy patch package under
`eval_runs/r2a_track_a_s1a_cc6_schema_v2_field_emission_runner_copy_patch_package_0gpu_20260527/`.
Primary decision:
`RUNNER_COPY_PATCH_PACKAGED_STATIC_SYNTHETIC_PASS_NOT_AUTHORIZED`. The package
created only an eval-runs-local patched copy with SHA
`2dd3af5472be2ab3bcf8a18b7b91487abb8d063c152911636957801675e3a024`. It
captures raw `extras["log_per_world"]` before numeric metadata filtering,
builds `cc6_safety_schema_v2_records`, supports dict-of-arrays and
list-of-per-world-dicts, fails closed on missing release/cable_drop/explosion
fields, and refuses product-credit authorization. `py_compile`, static guard
checks, and pure synthetic record-builder tests passed. The next clean route is
supervisor Tier-A review of this runner-copy patch package or HOLD; no execution
or product claim is authorized.

Relay requested that supervisor review. `%3` ACKed and began read-only review,
but no COMPLETE/INCOMPLETE marker returned before the 900s dispatch timeout, so
`%7` interrupted `%3` to conserve supervisor tokens. The visible partial review
identified a valid semantic gap: the runner copy needed to prove or fix observed
release-step and post-release-retention derivation from raw `log_per_world`
signals.

`%4` then completed a bounded 0GPU semantic gapfix package under
`eval_runs/r2a_track_a_s1a_cc6_field_emission_semantic_gapfix_0gpu_20260527/`.
Primary decision:
`FIELD_EMISSION_SEMANTIC_GAPFIX_PATCHED_COPY_STATIC_SYNTHETIC_PASS_NOT_AUTHORIZED`.
The package created only a new eval-runs-local patched copy with SHA
`2713ec78190e065f67e79ec8d926a201b81816adcb55f5da661907017ec43759`. It keeps
`configured_release_step` separate, derives observed `release_step` from the
first adapter/env step where raw `s1a_post_release_phase > 0.0` for a
D0-enabled non-source/non-comparator arm, records observed adapter/env step
fields, and counts retention strictly after release. The synthetic suite passes
never-reached release predicate, source-default/no release, hold-to-completion
comparator/no product credit, observed release step, exact 30-step retention,
premature cable drop, explosion, missing fields fail-closed, both
`log_per_world` shapes, and product-credit refusal. The current clean route is
supervisor Tier-A review of the semantic-gapfixed field-emission runner copy or
HOLD; no GPU, runner execution, training, product scoring, strategic routing, or
product claim is authorized. A concise `%3` review attempt after the semantic
gapfix timed out without a COMPLETE/INCOMPLETE marker and was interrupted to
conserve supervisor tokens. Later, `%3` returned `SEM_GAP_REVIEW_0527
COMPLETE`: the semantic-gapfixed package is sufficient as the basis for a later
exact-command Tier-A review. This is not an execution GO; the next clean route
is a bounded 0GPU exact-command review package over SHA
`2713ec78190e065f67e79ec8d926a201b81816adcb55f5da661907017ec43759`, or HOLD.

`%4` then completed the bounded 0GPU semantic exact-command review package under
`eval_runs/r2a_track_a_s1a_cc6_semantic_exact_command_review_0gpu_20260527/`.
Primary decision:
`CC6_SEMANTIC_EXACT_COMMAND_REVIEW_COMPLETE_NOT_LAUNCH_READY_REVIEW_REQUIRED`.
Launch-readiness remains `NOT_LAUNCH_READY_REVIEW_REQUIRED`. The package binds
the semantic-gapfixed runner SHA, `%3` verdict, schema-v2 field emission,
observed release-step semantics, post-release retention semantics,
retained-after-release threshold `0.6694805195`, and cuda:0-only policy. It does
not produce a defensible exact efficacy command because timeout, GPU-hours,
iterations, steps/env, seed/replicate policy, exact future output root, and
cable_drop/explosion non-inferiority thresholds remain `REVIEW_REQUIRED`.
Current next route is a bounded 0GPU CC6 efficacy budget and safety-threshold
gapfix, or HOLD; no execution or product claim is authorized.

`%4` then completed that bounded 0GPU terminal gapfix under
`eval_runs/r2a_track_a_s1a_cc6_budget_safety_terminal_gapfix_0gpu_20260527/`.
Primary decision:
`TERMINAL_GAP_NO_EXISTING_EVIDENCE_HOLD_NO_MORE_SAME_SCOPE_0GPU_DRAFTS`.
Only the fresh future output-root policy is evidence-backed. `num_steps_per_env`
has a static lower bound only: at least 111 contiguous emitted step payloads are
needed to observe release step 80 plus 30 post-release steps. This is not an
exact launch value. timeout, estimated GPU-hours, max iterations,
seed/replicate policy, and cable_drop/explosion non-inferiority thresholds still
lack existing evidence. The artifact-only path is therefore exhausted; the next
route is HOLD or a strategic decision that brings genuinely new evidence. No
more same-scope 0GPU exact-command/budget/safety drafting over the current
artifact set is recommended.

`%4` then completed a bounded 0GPU runner-horizon cap contradiction review under
`eval_runs/r2a_track_a_s1a_cc6_runner_horizon_cap_contradiction_0gpu_20260527/`.
Primary decision:
`RUNNER_HORIZON_CAP_CONTRADICTION_CONFIRMED_REDIRECTION_REQUIRED_NOT_AUTHORIZED`.
The semantic CC6 retention contract requires at least `111` contiguous emitted
step payloads (`release_step=80` plus 30 post-release observed steps, release
step excluded), while the current base future entrypoint rejects
`num_steps_per_env > 32`. The semantic-gapfixed copy delegates future-run
through that base entrypoint, so exact-command parameter selection alone cannot
make the current runner path launch-ready. No patch, exact command, execution,
or product claim was created. The clean next route is
`HOLD_OR_0GPU_RUNNER_GATE_REDESIGN_SCOPE_FOR_CC6_HORIZON_CAP_NOT_AUTHORIZED`.

`%4` then completed a bounded 0GPU runner-gate redesign scope package under
`eval_runs/r2a_track_a_s1a_cc6_runner_gate_redesign_scope_0gpu_20260527/`.
Primary decision:
`RUNNER_GATE_REDESIGN_SCOPE_COMPLETE_READY_FOR_0GPU_PATCH_PACKAGE_NOT_AUTHORIZED`.
The recommended redesign surface is a future eval-runs-local runner-copy patch
package. Protected env/source mutation is not required by static evidence: the
protected env already emits `s1a_post_release_phase`, and the semantic-gapfixed
copy already derives observed release, retention, cable_drop/explosion,
no-crutch provenance, and product-credit refusal. The structural blocker is the
base future entrypoint's `num_steps_per_env > 32` fail-closed gate. No patch,
exact command, execution, or product claim was created. The clean next route is
`BOUNDED_0GPU_RUNNER_GATE_REDESIGN_PATCH_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.

`%4` then completed the bounded 0GPU runner-gate redesign patch package under
`eval_runs/r2a_track_a_s1a_cc6_runner_gate_redesign_patch_package_0gpu_20260527/`.
Primary decision:
`RUNNER_GATE_REDESIGN_PATCH_PACKAGED_STATIC_SYNTHETIC_PASS_NOT_AUTHORIZED`.
The package creates only a fresh eval-runs-local patched runner copy, SHA
`1fdb75a7d6cd680cbc06e6f80ba53d4ac3e9a3eab44299326654efbc49450c9f`, with
`SOURCE_DIFF.patch` SHA
`93c9a2d6059eb9d851bfb36d943fd018d340794837a12c5c276f78f202f94388`. The copied
future-run path replaces the obsolete `num_steps_per_env > 32` gate with a
semantic-horizon lower-bound gate: default `80 + 30 + 1 = 111` emitted step
payloads, fail-closed below the lower bound. This is static feasibility only,
not an exact launch value. Static/synthetic validation passed, including helper
behavior where `110` fails and `111` passes, direct run without exact GO exits
`64` before env construction, product credit is refused, and missing required
safety fields fail closed. No exact command, execution, training, protected
mutation, product claim, sim2real claim, T-ROOT95 claim, Stage-2 claim, or
cuda:1 use occurred. The clean next route is
`SUPERVISOR_TIERA_REVIEW_FOR_RUNNER_GATE_PATCH_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.

`%3` then returned `RUNNER_GATE_PATCH_REVIEW_0527 COMPLETE`. The package-level
gate is closed for this patch package: the copied path no longer blocks the
semantic horizon with the old 32-step cap, the new semantic-horizon gate is
fail-closed with default lower bound `111`, `110` fails and `111` passes while
the bound remains non-launch, direct future-run without exact GO exits `64`,
exact-GO/cuda:0/protected-SHA/no-crutch/product-refusal guards are preserved,
and there are no execution/product/sim2real/T-ROOT95/Stage-2/cuda:1 claims or
authorizations. `%3` noted one forward watch item for any later exact-command
review: if the base precheck adds new `num_steps_per_env`-dependent checks, the
`capped_args` assumption must be re-reviewed. The clean next route is
`BOUNDED_0GPU_PATCHED_RUNNER_EXACT_COMMAND_REVIEW_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.

`%4` then completed the bounded 0GPU patched-runner exact-command review
package under
`eval_runs/r2a_track_a_s1a_cc6_patched_runner_exact_command_review_0gpu_20260527/`.
Primary decision:
`CC6_PATCHED_RUNNER_EXACT_COMMAND_REVIEW_COMPLETE_NOT_LAUNCH_READY_REVIEW_REQUIRED`.
The patched runner closes the local `111 > 32` gate contradiction, but an exact
CC6 efficacy command is still not launch-ready. Evidence-backed fields are the
patched runner SHA, source diff SHA, `%3` patch review complete, semantic-gap
review complete, retained-after-release baseline/threshold, semantic horizon
lower bound `111`, protected SHA locks, and cuda:0/cuda:1-forbidden policy.
Still `REVIEW_REQUIRED`: timeout, estimated GPU-hours, `max_iterations`, exact
steps/env launch value, seed/replicate policy, fresh output root, cable_drop
non-inferiority threshold, and explosion non-inferiority threshold. The blocked
draft exits `64` and no executable exact command was created. The clean next
route is
`HOLD_OR_NEW_EVIDENCE_SOURCE_FOR_CC6_BUDGET_AND_SAFETY_THRESHOLDS_NOT_AUTHORIZED`.

`%4` then completed the retained-threshold provenance audit under
`eval_runs/r2a_track_a_s1a_cc6_threshold_provenance_audit_0gpu_20260527/`.
The audit found the retained-after-release baseline `40/77 = 0.5194805195` is
evidence-backed, while the `+0.15` margin was local-draft rather than earlier
Rs/R1-derived. `%7` selected `+0.15` only as a diagnostic CC6 null-hypothesis
margin, yielding diagnostic threshold `0.6694805195`; it is not a product
predicate or sim2real success predicate.

`%4` then completed a bounded 0GPU release-horizon scout design, `%3` completed
Tier-A review for the exact one-attempt scout, and `%4` ran the exact
authorized cuda:0 diagnostic scout once. The scout root is
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_scout_gpu_diagnostic_20260527/`
and the review root is
`eval_runs/r2a_track_a_s1a_cc6_release_horizon_scout_gpu_diagnostic_review_20260527/`.
The run captured runtime/budget/schema evidence but did not establish efficacy:
actual releases were `3/41`, retained-after-release was `0/3`, all-world
cable_drop was `40/41`, all-world explosion was `35/41`, and no product,
physical-grasp, sim2real-success, T-ROOT95, Stage-2, training, or routing claim
is authorized. `%4` then completed the artifact-only 0GPU schema-gap review:
observed release-step distribution and first-class release-normalized
cable_drop/explosion fields required a later schema patch package if this
branch continued; that package is now generated and awaits supervisor Tier-A
review or HOLD. Another GPU run requires a fresh Tier-A gate and exact
authorization.

The previous NEST position was
`S1A_DEFAULT_OFF_CONSTRUCTION_ONE_STEP_PASS / PRODUCT_GO_FALSE` as observed at
`2026-05-26T20:55:00+09:00`. `%3` independently verified the cuda:0
default-off construction/reset/one-step runtime boundary: `num_obs=45`, obs
shape `[41,45]`, finite obs/reward, all S1A flags false, no S1A log keys,
kinematic support false, and protected SHAs unchanged. It was a parity result
only and did not authorize enabled execution or product claims.

The earlier NEST position was
`R2A_TRACK_A_S1A_L3_PREMUTATION_SOURCE_DESIGN_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T15:02:12+09:00`. Real `%4`
completed the bounded 0GPU/no-run/no-mutation L3 pre-mutation source-design
package under
`eval_runs/r2a_track_a_s1a_l3_premutation_source_design_0gpu_20260526/`.
It binds `%3` COMPLETE and the requirement that any actual source-mutation gate
must use L3 5-body CC Debate pre-review plus multi-perspective post-review
before any source byte is mutated. It includes reward-design four outputs,
pre-check failure modes, obs-reward consistency, threshold reachability,
penalty/reward budgeting, a 5-body CC debate, and a draft patch explicitly
marked not authorized. Source mutation remains unauthorized.

Predecessor review state:
`T_ROOT_OPS_SUP_S1A_SOURCE_MUTATION_REVIEW_GATE_VERDICT_20260526:
COMPLETE` as observed at `2026-05-26 14:35:57 JST`. `%3` verified that the
S1A design-gate/L3 gapfix closes the named blocker as a readiness basis for a
later separate bounded S1A source-mutation gate. The reviewed package state is
`R2A_TRACK_A_S1A_SOURCE_MUTATION_DESIGN_GATE_GAPFIX_0GPU_COMPLETE /
PRODUCT_GO_FALSE`; the package root is
`eval_runs/r2a_track_a_s1a_source_mutation_design_gate_gapfix_0gpu_20260526/`.
It directly answers `%3` verdict
`T_ROOT_OPS_SUP_S1A_SOURCE_MUTATION_REVIEW_GATE_VERDICT_20260526:
INCOMPLETE` by adding forced design-gate / L3 carry-forward for any future
reward/observation/success-shaping source mutation: `/reward-design` four
outputs, `/pre-check`, obs-reward consistency, ground-truth threshold
reachability, penalty/reward ratio, L3 pre-mutation design review,
post-mutation multi-perspective verification, and predicate provenance
carry-forward. The actual source-mutation gate remains unauthorized and must
explicitly use the L3 5-body CC Debate pre-review plus multi-perspective
post-review before any source byte is mutated.

Predecessor reviewed package state:
`R2A_TRACK_A_S1A_SOURCE_MUTATION_REVIEW_GATE_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T13:52:39+09:00`. Real `%4`
completed a bounded 0GPU/no-run review gate package under
`eval_runs/r2a_track_a_s1a_source_mutation_review_gate_0gpu_20260526/`.
Decision:
`FUTURE_SUPERVISOR_OR_REVIEW_FOR_BOUNDED_S1A_SOURCE_MUTATION_NOT_AUTHORIZED`.

The review gate confirms the combined evidence threshold for reopening a
bounded S1A source-mutation review: original `46` actual releases + top-up `31`
actual releases = `77 >= 70`. This is a review-reopen condition only. It does
not authorize source mutation, product scoring, D1/D2/D3 routing, training,
product/physical-grasp/sim2real-success claims, T-ROOT 95 claims, or follow-on
GPU execution. Product success remains `0`. The gapfix does not authorize source
mutation either; next safe routes are review of the bounded v2 source-mutation
gate package, or HOLD.

The predecessor top-up diagnostic state was
`R2A_S1A_TOPUP_GPU_DIAGNOSTIC_ONE_ATTEMPT_COMPLETE / PRODUCT_GO_FALSE`. Real
`%4` ran exactly one bounded non-mutating cuda:0 top-up diagnostic under
`eval_runs/r2a_track_a_s1a_runner_bound_topup_gpu_diagnostic_20260526`.
It exited `0` without timeout, completed `492/492` records, used `cuda:0` only,
kept `cuda1_unused=true`, produced `31` top-up actual release events, retained
`16/31` after release, and product success count was `0`.

The predecessor exact-command packet state was
`R2A_TRACK_A_S1A_TOPUP_RUNNER_BOUND_EXACT_COMMAND_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE`. It bound the fresh top-up root, seeds `[3, 4]`, six
non-impedance arms, expected completion count `492`, top-up min actual-release
target `24`, combined reopen rule, protected SHAs, w41 cache SHA, and
diagnostic-only predicate attestation.

The predecessor runner-SHA binding state is
`R2A_TRACK_A_S1A_TOPUP_RUNNER_SHA_BINDING_GAPFIX_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T08:58:00+09:00`. Real `%4`
completed a bounded 0GPU/no-run runner-SHA binding gapfix package under
`eval_runs/r2a_track_a_s1a_topup_runner_sha_binding_gapfix_0gpu_20260526/`.
Decision:
`S1A_TOPUP_RUNNER_SHA_BINDING_GAPFIX_COMPLETE_READY_FOR_SUPERVISOR_TIERA_EXACT_COMMAND_REVIEW_NOT_AUTHORIZED_OR_HOLD`.
That package closed the `%3` pooling-comparability blocker by binding any future
non-mutating top-up evidence to the same sample-power/status runner that
produced the existing 46 actual releases.

The predecessor top-up design state is
`R2A_TRACK_A_S1A_EVIDENCE_THRESHOLD_TOPUP_DESIGN_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T08:05:26+09:00`. Real `%4`
completed a bounded 0GPU/no-run evidence-threshold / top-up design package under
`eval_runs/r2a_track_a_s1a_evidence_threshold_topup_design_0gpu_20260526/`.
Decision:
`HOLD_OR_FUTURE_TIERA_REVIEW_FOR_NONMUTATING_S1A_TOPUP_EVIDENCE_ACQUISITION_NOT_AUTHORIZED`.
Existing 46 actual releases may be accumulated only if old/new roots, protected
SHAs, runner/schema, and no-crutch provenance remain immutable/comparable. The
conservative reopen threshold is total actual releases `>=70`, so the
recommended top-up target is `+24` valid actual releases.

The predecessor S1A implementation-design state is
`R2A_TRACK_A_S1A_MINIMAL_REWARD_OBS_CURRICULUM_IMPLEMENTATION_DESIGN_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T01:40:24+09:00`. Real `%4`
completed the bounded 0GPU/read-only implementation-design package under
`eval_runs/r2a_track_a_s1a_minimal_reward_obs_curriculum_impl_design_0gpu_20260526/`.
Decision:
`S1A_MINIMAL_IMPL_DESIGN_COMPLETE_RECOMMEND_TIERA_SOURCE_MUTATION_REVIEW_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.
The design keeps `task_config.py` locked, requires default-off or versioned
behavior, and narrows S1A to reward/stability pressure, release-readiness
observation state, and curriculum/sample-power schedule while preserving
actual-yield and no-crutch gates. Recommended next route is
`SUPERVISOR_TIERA_REVIEW_FOR_BOUNDED_S1A_SOURCE_MUTATION_PACKAGE_NOT_AUTHORIZED_OR_HOLD`.
No source mutation, GPU/sim/env launch, training, product scoring, strategic
routing, product claim, physical-grasp claim, sim2real-success claim, T-ROOT 95
claim, or cuda:1 use is authorized by this package.

The predecessor S1 scope state is
`R2A_TRACK_A_S1_POST_RELEASE_STABILITY_POLICY_DATA_SCOPE_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T00:56:04+09:00`. Real `%4`
completed a bounded 0GPU/read-only successor-scope package under
`eval_runs/r2a_track_a_s1_post_release_stability_policy_data_scope_0gpu_20260526/`.
Decision:
`S1_POLICY_DATA_SCOPE_COMPLETE_RECOMMEND_0GPU_S1A_REWARD_OBSERVATION_CURRICULUM_DELTA_AUDIT_NOT_AUTHORIZED_OR_HOLD`.
The package keeps the D0 sample-power/status lineage terminal/HOLD for strategic
routing and scopes S1 to policy/data/reward/observation/curriculum design under
the no-crutch sim2real product predicate. Recommended next decision is
`BOUNDED_0GPU_S1A_REWARD_OBSERVATION_CURRICULUM_DELTA_AUDIT_NOT_AUTHORIZED_OR_HOLD`.
No execution, source/task_config/runner mutation, training, product scoring,
strategic routing, product claim, physical-grasp claim, sim2real-success claim,
T-ROOT 95 claim, or cuda:1 use is authorized by this package.

The predecessor D0 terminal state is
`R2A_TRACK_A_D0_SAMPLE_POWER_STATUS_RELEASE_YIELD_DELTA_REVIEW_0GPU_COMPLETE /
PRODUCT_GO_FALSE` as observed at `2026-05-26T00:16:53+09:00`. Real `%4`
completed a bounded 0GPU release-yield delta review under
`eval_runs/r2a_track_a_d0_sample_power_status_release_yield_delta_review_0gpu_20260526/`.
Decision:
`NO_SAFE_RELEASE_YIELD_DELTA_FROM_EXISTING_ARTIFACTS_HOLD_RECOMMENDED_NOT_AUTHORIZED`.
The review found no genuinely safe release-yield delta from existing artifacts:
actual release yield remains `46 < 60`; in the four release-producing arms only
`45/492` records reached scheduled release; the no-release records ended before
release via cable_drop or explosion rather than schema/cache/contact failures.
Changing the threshold, releasing earlier without a task-appropriate timing
review, counting hold-to-completion or active-at-completion, or weakening the
sim2real predicate would change the question to pass sample power. Recommended
route is `HOLD_STRATEGIC_ROUTING_AFTER_UNDERPOWERED_D0_SAMPLE_POWER_STATUS_DIAGNOSTIC`.
Protected SHAs remained locked, protected diff empty, GPU query empty, and
cuda:1 unused. No rerun, follow-on GPU launch, source/task_config/runner/runtime
mutation, ContactSensor patch, product scoring, product claim, physical-grasp
claim, or T-ROOT 95 claim occurred.
The corrected-root run is still non-evaluable D0 evidence. The prior
contact-sensor config package found the env/runner config surface structurally
sufficient in principle, and the candidate primpath gate found static evidence
insufficient for exact runtime ContactSensor prim path and shape/filter
expressions. `%3` ruled that ContactSensor micro-sim sequence INCOMPLETE because
the executed corrected-root D0 output has 21/861 records, all `ERROR`: 6/7 arms
were blocked by missing w41 precondition cache, while only the impedance arm was
blocked by ContactSensor integration. The latest w41 build created the target
cache
`thread_isaac_lab/data/rl_aerial_regrasp_cache/aerial_regrasp_w41_p0_v2.npz`;
it parses with `world_count=41`, `body_count=2378`, and expected keys present.
Protected checks remained clean and cuda:1 was unused. The selected immediate
route drops/holds `impedance_handoff_contact_force_limited` and prepares a later
six-arm D0 authorization review for `source_default`,
`oracle_pose_or_force_hold`, `release_ramp_5`, `release_ramp_10`,
`support_removal_ablation`, and `hold_to_completion_comparator`. Expected
future count is 738 with a fresh output root and explicit `--arm` selection.
The six-arm plan cannot answer impedance handoff or ContactSensor telemetry
validity and cannot produce product scoring, product readiness, or D1/D2/D3
routing. The root-binding review created a fresh diagnostic-only predicate
attestation for the future output root
`eval_runs/r2a_track_a_d0_6_arm_gpu_diagnostic_20260525`; attestation SHA is
`cfc1b19a463b76dcaa5df43df22af811ae54a9b5d3ed8e918f55fdf2bce6c524`, and
canonical predicate text SHA remains
`861994173a28cb7701a9b1a87b46b68ba9c60a77bf3f62abb0a4e8338a540433`. The latest
auth review found the exact future six-arm command packageable for supervisor
`%3` Tier-A review only; the subsequent `%3` Tier-A review exposed the
world-count contract mismatch, the per-world runner fixed it, and the one
authorized diagnostic run above then completed. Product scoring is false,
strategic routing is false, and any D0 retry remains unauthorized. This is not
product evidence and not D1/D2/D3 routing basis. The attested predicate
remains binding: product success requires post-release autonomous cable retention
by real-world-reproducible physical mechanisms and excludes kinematic support,
`inv_mass=0`, direct sim-state writes, `active_at_completion`, and
hold-to-completion-only success.
Standing Rs principle: do not adopt goals that cannot be realized under
sim2real. GAP-B planning is complete under
`eval_runs/r2a_track_a_gapb_functional_d0_runner_tiera_planning_0gpu_20260525/`:
the package defines the future functional D0 runner behavior, no-crutch product
schema, sample/power guard, sim2real success/refusal gates, and Tier-A review
questions. Supervisor `%3` reviewed the package COMPLETE as a basis for
implementation, and real `%4` then created the future runner implementation
package under
`eval_runs/r2a_track_a_gapb_functional_d0_runner_impl_0gpu_20260525/`. `%3`
visible review findings and relay verification then found that prior package
incomplete because it assumed `info["log_per_world"]` was a list of rows and
read stale kinematic pseudo-fields. Real `%4` created the schema-fix package
under
`eval_runs/r2a_track_a_gapb_functional_d0_runner_impl_schemafix_0gpu_20260525/`.
M1 is encoded as right clamp plus cable-not-dropped sustained for K=5, then
release next step. M2 is classified `SURFACE_SUFFICIENT_NO_SOURCE_MUTATION`. The
runner is future execution code only and was not run. `%3` reviewed the
schema-fix package COMPLETE for the prior B1/B2 blockers and confirmed the
fail-closed no-crutch schema wiring. Real `%4` then created a review-only GPU D0
authorization packet under
`eval_runs/r2a_track_a_gapb_gpu_d0_authorization_packet_0gpu_20260525/`. The
packet binds the exact cuda:0 command, predicate attestation artifact, and fresh
future output root
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_20260525/`, which
remained absent. Relay-side static-precondition checks passed without heavy
import/GPU. `%3` then reviewed that packet INCOMPLETE for B-GPU-1 because proxy
compilation recorded in `compiled_by` could bypass a validator checking only
`generated_by`. Real `%4` created the authguardfix runner and packet under
`eval_runs/r2a_track_a_gapb_functional_d0_runner_impl_authguardfix_0gpu_20260525/`
and
`eval_runs/r2a_track_a_gapb_gpu_d0_authorization_packet_authguardfix_0gpu_20260525/`.
The authguardfix runner detects proxy provenance, accepts it only as diagnostic,
and forces product scoring plus strategic routing authorization false.
Supervisor `%3` then completed the light B-GPU-1 re-review and confirmed the
guard is now source-enforced: the packet's proxy provenance is detected through
`compiled_by` and related provenance fields, product scoring is forced false,
and proxy evidence cannot yield `product_success=true`.
`%7` then authorized exactly one diagnostic-only cuda:0 run from the
authguardfix packet. Real `%4` ran the exact command once. D0 did not execute:
IsaacLab import aborted before env instantiation with
`ModuleNotFoundError: No module named 'lazy_loader'`; completion count is 0/861
expected, the future output root remained absent, and no result artifacts were
created. Real `%4` then completed a 0GPU/read-only import-runtime triage under
`eval_runs/r2a_track_a_d0_import_runtime_remediation_triage_0gpu_20260525/`.
The triage classified the abort as import-runtime provisioning, not a D0
outcome: the failed wrapper resolves `isaaclab` and `thread_isaac_lab` under
`env_isaaclab6`, but `lazy_loader` is absent there; repo-local `env_isaaclab`
has `lazy_loader`, but runtime selection change is not implicitly authorized.
Real `%4` then completed the separate canonical runtime review under
`eval_runs/r2a_track_a_d0_canonical_runtime_review_0gpu_20260525/`.
The review selected Option A: repair/provision `env_isaaclab6`, because it is the
exact failed command's Python 3.12 / Isaac Sim 6.0 / Warp 1.13 runtime. Runtime
switching to repo-local `env_isaaclab` is not selected because it changes to
Python 3.11 / Isaac Sim 5.1 / Warp 1.10.
`task_config.py` remains locked at `1b8f2739...`; env SHA remains
`87875a...`. Supervisor `%3` reviewed the provisioning-repair directive
INCOMPLETE for one shared-venv safety gap; `%7` incorporated that G1 as mandatory
process-binding and rollback guards. Real `%4` then completed the bounded 0GPU
repair under
`eval_runs/r2a_track_a_d0_env_isaaclab6_provisioning_repair_20260525/`:
`lazy-loader==0.5` was installed into `/home/rlrk/env_isaaclab6` with `--no-deps`,
`pip check` had no new breakage versus the before snapshot, and the wrapper now
resolves `lazy_loader` plus the required IsaacLab/thread/torch/warp import
surface without env instantiation. `%3` then reviewed the post-repair exact D0
GPU gate COMPLETE for boundedness/preconditions, and `%7` authorized exactly
one diagnostic cuda:0 run. Real `%4` ran the exact command once, but D0 did not
execute: Omniverse Kit requested EULA Yes/No and the non-interactive bootstrap
failed with `Unable to bootstrap inner kit kernel: EOF when reading a line`.
Completion remains 0/861 and the output root remained absent. The next route is
no longer another technical retry. Real `%4` completed the bounded 0GPU
runtime EULA/bootstrap review under
`eval_runs/r2a_track_a_runtime_eula_bootstrap_review_0gpu_20260525/`. It
classified the abort as `RUNTIME_EULA_PROMPT_BOOTSTRAP_ABORT_NOT_D0_OUTCOME`
and recommended human/operator NVIDIA Omniverse/Isaac Sim EULA acceptance
attestation, then separate exact D0 diagnostic command review, or HOLD. Future
transient `OMNI_KIT_ACCEPT_EULA=YES` use is locally precedented but allowed only
after explicit acceptance provenance; persistent license-state mutation is not
selected. Until separately authorized, D0 retry/execution, EULA acceptance,
`OMNI_KIT_ACCEPT_EULA=YES` execution, runtime remediation, GPU/simulator
execution, runtime switch, further dependency or venv mutation, runner patch,
further source/task_config mutation, training, product claim, physical-grasp
claim, and T-ROOT 95 claim remain not authorized; product scoring and D1/D2/D3
strategic routing remain blocked.
Human/operator EULA acceptance was then provided through the user-channel
interactive first-run transcript (`Yes`, `The EULA was accepted.`, `isaacsim
import ok`). Real `%4` completed the bounded 0GPU exact-command review under
`eval_runs/r2a_track_a_eula_attestation_exact_command_review_0gpu_20260525/`.
The future command draft now includes transient `OMNI_KIT_ACCEPT_EULA=YES` but
is still `NOT_AUTHORIZED_DO_NOT_RUN`. Relay corrected the preserved transcript
to match the user evidence, including `import isaacsim; print(...)`. The next
route was supervisor `%3` Tier-A review of this exact-command packet, or HOLD;
D0 execution remained a separate later launch gate. `%3` then closed the only
Q4 blocker for the exact-command packet, and `%7` authorized one EULA-attested
diagnostic cuda:0 run. Real `%4` ran the exact command once. D0 still did not
execute: lazy env import aborted before output-root creation with import error
`cannot import name 'DeformableObject' from 'isaaclab.assets'`. Completion is
0/861, the output root
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_authguardfix_20260525/`
remained absent, `full_summary.json` and `completion_records.json` are absent,
post-run GPU query is empty, cuda:1 was unused, and relay preserved abort
evidence under `eval_runs/r2a_track_a_eula_attested_d0_gpu_abort_20260525/`.
Relay then completed the bounded 0GPU import API mismatch review under
`eval_runs/r2a_track_a_import_api_mismatch_review_0gpu_20260525/`. This is an
import API mismatch before D0, not a D0 diagnostic outcome. The review
classifies the cause as
`LOCAL_THREAD_PACKAGE_IMPORT_SIDE_EFFECT_PLUS_ISAACLAB_6_ASSET_API_SPLIT` and
recommends Option A. Relay then completed the fresh eval_runs-only runner
direct-import bypass package under
`eval_runs/r2a_track_a_runner_direct_import_bypass_0gpu_20260525/`. The new
runner SHA is
`af5d6806a0cd125ccb552373c7b7c407d4a95b7aaab8aab35849b4a7f6223b0e`, and the
patch changes only the future execution import route so the runner imports
`newton_aerial_regrasp_env` directly from `thread_isaac_lab/envs`, avoiding
package `__init__` / legacy `assets_cfg.py` side effects. env6 `py_compile`,
`describe-contract`, invalid-marker refusal, static old-import scan, protected
diff, protected SHA, and GPU-empty checks passed. `%3` then reviewed the exact
direct-import command COMPLETE and `%7` authorized one diagnostic cuda:0
command. Real `%4` ran it exactly once; the runner refused before D0 execution
with `future_preconditions_failed` / `wrong_target_output_root` because the
predicate attestation is bound to the authguardfix output root while the command
used a new direct-import output root. Both roots were absent at refusal time, completion was
0/861, result JSON files were absent, protected SHAs were unchanged, post-run GPU
query is empty, cuda:1 was unused, and no retry occurred. Relay then completed
bounded 0GPU exact-command alignment review under
`eval_runs/r2a_track_a_exact_command_alignment_review_0gpu_20260525/`. The
smallest candidate delta is command-only: align `--output-dir` to the existing
attestation `target_output_root`
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_authguardfix_20260525`.
Both roots remained absent at review time, and a static `validate_static_preconditions` call with
the aligned root returned `STATIC_PRECONDITIONS_OK`, expected completion count
861, `predicate_product_scoring_authorized=false`, and
`strategic_routing_authorized=false`. `%3` then completed corrected-root
Tier-A re-review, `%7` authorized exactly one corrected-root run, and real `%4`
ran it once with the record-error outcome above. `%4` then completed the 0GPU
error review and classified missing w41 cache plus missing contact-sensor prim
path. Next route is 0GPU precondition-cache readiness review plus D0
contact-sensor config remediation review, or HOLD. D0 retry/execution,
GPU/simulator execution, source/task_config mutation,
runtime/dependency/attestation mutation, product scoring, D1/D2/D3 routing,
product claim, physical-grasp claim, and T-ROOT 95 claim remain not authorized.

## 1. 概要

**目的:** 5-clip cable routing を RL スキル + scripted transport で実現
**手法:** DAPG (Demo Augmented Policy Gradient) + Domain Randomization
**構造:** 排他的単腕 (RIGHT→CLIP0,1 / LEFT→CLIP2,3,4 / HANDOVER at CLIP1→2)

### スキル分割

```
ApproachCable [RL] → Clamp [RL] → TransportToClip [scripted] → InsertIntoClip [RL]
                                                                    ↓
                                                             Unclamp [RL]
                                                                    ↓
                                                          AerialRegrasp [RL] (clip間)
                                                                    ↓
                                                          Handover [scripted] (CLIP1→2)
```

> **2026-04-05 設計変更:** クランプ/アンクランプを独立スキルに分離。
> 各スキル内でfinger状態は固定（AC=OPEN, IC=CLOSED等）。finger open/closeの学習は専用スキルの責務。
> 半クランプ/半アンクランプはscripted（固定値指令）。フルクランプ/フルアンクランプは純RL。
>
> | スキル | 方式 | finger状態 | 学習内容 |
> |--------|------|-----------|---------|
> | ApproachCable | RL | 常にOPEN | ケーブル位置へのapproach |
> | **Clamp** (新規) | RL | OPEN→CLOSED | finger閉じタイミング・力の学習 |
> | TransportToClip | scripted | 常にCLOSED | 搬送 |
> | InsertIntoClip | RL | 常にCLOSED | groove押し込み+着座 (アンクランプ手前まで) |
> | **半アンクランプ** | scripted | CLOSED→半OPEN | 誘導ハンド半保持 (固定値0.006) |
> | ~~**Unclamp**~~ | ~~RL~~ → **scripted** | 半OPEN→OPEN | v4完走後scripted化決定 (2026-04-06) |
> | **半クランプ** | scripted | OPEN→半CLOSED | ケーブル軽保持 (固定値0.006) |
> | AerialRegrasp | RL | L:CLOSED, R:approach | ハンドオーバー接近 |
> | Handover | scripted | scripted | CLIP1→2 受け渡し |
>
> **Handover STEP割当:** 43ステップ表では独立STEPなし。C1→C2遷移 (STEP 10→11) 時のTransportToClip移動に腕役割切替（R支配→L支配）を含む。物理的にはTransportToClipと同一動作のため、独立STEPは不要。
>
> **未割当スキル (2026-04-05時点):**
> - **半クランプ** (OPEN→0.006): 43ステップ表に対応STEPなし。全finger遷移はCLOSED→半(HalfUnclamp)方向のみ
> - **Unclamp RL** (半OPEN→OPEN): 43ステップ表に直接対応なし。STEP 8等のR手全開放(CLOSED→OPEN)を HalfUnclamp+Unclamp RL に分解する場合に使用可能
>
> **2026-04-05 GripEnv統合:** Clamp+Unclampを`NewtonGripEnv`に一体化。
> ~~42D obs / 14D action（双方向finger [-1,+1]）。mode="clamp"|"unclamp"切替。~~
> SkillType: CLAMP, UNCLAMP を追加 (skill_adapter.py)。GRIP は CLAMP/UNCLAMP で代替のため不要。
> Env: `thread_isaac_lab/envs/newton_grip_env.py`
>
> **2026-04-06 D2改訂:** Clamp → 12D action + auto-close (pos+ori閾値でfinger自動close)。
> Unclamp → scripted化決定 (v4完走後、finger開きのみでRL不要と判断)。
> 全RLスキルが12D action統一。§14.6のaction_dim問題は解消。

### パイプライン全体像

```
[Stage 0a] dry-run → verified waypoints (IK reachability check)
[Stage 0b] wet-run → Newton VBD physics replay → (obs, action) pairs
[Stage 0c] aggregate → demos.npz
[Stage 1]  train_dapg.py → PPO + BC loss (α減衰, demos.npz直接参照) → pure RL policy
```

**CCはこのパイプラインを Stage 0 から順に実行すること。Stage をスキップしない。**

---

## 1.1 実行計画

CCはこの計画に従って順に実行する。Phase をスキップしない。Gate NG 時は次 Phase に進まずrsに報告する。

### Phase 1: ApproachCable + DAPG

#### v8-v12 (廃止, 参考データ)

> v5設計転換 (2026-03-30) により廃止。旧obs(11D)/action(6D)/reward前提。

| Step | 内容                                                 | 成果物                                          |
| ---- | -------------------------------------------------- | -------------------------------------------- |
| 1-1  | v8 乗算結合報酬 実装                                       | newton_approach_cable_env.py 変更                 |
| 1-2  | dry-run + wet-run                                  | approach_cable_demos.npz (60tr), waypoints JSON |
| 1-3  | wet-run改善 (多EP + cable query)                      | approach_cable_demos_v2.npz (cuda:0)            |
| 1-4  | DAPG 30iter (alpha=0.3固定) — 報酬検証                   | 訓練ログ (cuda:2, 1-3と並行)                        |
| 1-5  | DAPG 300iter (alpha 0.3→0, linear, cuda:2, w=1024) | policy checkpoint                            |

**Gate G1a (1-4後):** dist_mean<50mm, close_step∈[30,150], close_before_min_dist=0%, diverge<50%, death_zone<30%
**Gate G1b (1-5後):** SUCCESS > 0% (C1∧C2∧F1_R∧C5)。Section 4 成功条件定義参照

#### v5 Architecture (current)

| Step | 内容 | 成果物 |
|------|------|--------|
| v5-1 | v5 env実装 (42D obs, 12D action, pose_match reward, STEP machine) | newton_approach_cable_env.py |
| v5-2 | v5 demo収集 (12D action scripted、両腕full pose delta) | approach_cable_demos_v10.npz |
| v5-3 | sanity check 3iter | 訓練ログ |
| v5-4 | DAPG 30iter (α=0.1, anneal=50) | 訓練ログ |
| v5-5 | DAPG 100iter+ | policy checkpoint |
| v5-6 | T_ALIGN / T_SEAT 実測 | 閾値確定 |

**Gate G1-v5a (v5-4後):** pose_match品質: R_pos mean > -1.0, STEP完了率 > 0%
**NG →** obs/reward設計問題。Section 4 再検討
**Gate G1-v5b (v5-5後):** clamp成功: clamp(R) ∧ sustained(K=5) > 0%
**NG →** curriculum追加 or 報酬再設計

### Phase 1': A/B 判定 — CANCELLED

> **2026-03-30: CANCELLED.** v5設計転換でB統合env (GraspAndInsertEnv) がv5 obs/action非互換。A路線（独立スキル）で確定。

### Phase 2: InsertIntoClip

**前提:** Phase 1 Gate G1-v5b PASS

| Step | 内容 | 成果物 |
|------|------|--------|
| 2-1 | 合成初期状態構築 (finger間cable配置 → VBD settle → cache) | precondition cache |
| 2-2 | InsertIntoClip env実装 (obs 12D, act 4D) | newton_insert_clip_env.py |
| 2-3 | dry-run: CLIP1 insert waypoints | data/waypoints/insert_clip_c1.json |
| 2-4 | wet-run → demo収集 | data/bc_demos/insert_clip_demos.npz |
| 2-5 | DAPG 300iter (cuda:0, w=512) + DR v1 (clip XY ±5mm) | policy checkpoint |

**Gate G2:** I1∧I2∧I3 成功率 10%+
**NG →** DR無効で再試行 → curriculum

### Phase 3: AerialRegrasp

**前提:** Phase 1 Gate G1-v5b PASS

| Step | 内容 | 成果物 |
|------|------|--------|
| 3-1 | 合成初期状態構築 (左finger cable保持 → settle → cache) | precondition cache |
| 3-2 | AerialRegrasp env実装 (obs 11D, act 4D) | newton_aerial_regrasp_env.py |
| 3-3 | demo収集 (dry-run → wet-run) | demos.npz |
| 3-4 | DAPG 300iter (cuda:1, w=512) | policy checkpoint |

**Gate G3:** A1∧A2∧A3∧A4 成功率 10%+

### Phase 4: P1工程分割

**前提:** Phase 1 Gate G1-v5b PASS (P1c = ApproachCable)

| Step | 内容 | 成果物 |
|------|------|--------|
| 4-1 | P1a env実装 (左しごき, obs/act 3D) | newton_shigoki_env.py |
| 4-2 | P1a DAPG訓練 | policy checkpoint |
| 4-3 | P1b scripted bridge実装 | scripted module |
| 4-4 | P1a→P1b→P1c チェーン検証 | E2E eval結果 |

**Gate G4:** mu_clamped でのP1c success >= Phase 1 単体の成功率

### Phase 5: スキル連鎖統合

**前提:** G1-v5b, G2, G3, G4 全PASS

**アーキテクチャ:** MultiSkillActorCritic (`models/skill_adapter.py`)
- 凍結ベース (mixed base backbone) + 5 RLスキルアダプタ (LoRA + MLP + gate)
- `set_skill(SkillType.XXX)` でスキル切り替え。adapter ~4K params / skill
- 使用法: `apply_skill_adapter(runner, base_model_path, SkillType.XXX)`
- **SkillType (RL only):** APPROACH_CABLE, CLAMP, INSERT_INTO_CLIP, UNCLAMP, AERIAL_REGRASP
- Scripted スキル (TransportToClip, ReClamp, HalfUnclampRelease, ClipConfirm) は SkillType 外。Orchestrator が直接実行 (§14)

| Step | 内容                                                 | 成果物               |
| ---- | -------------------------------------------------- | ----------------- |
| 5-0  | **Skill Adapter統合 (DONE 2026-04-04)**               | skill_adapter.py  |
| 5-1  | scripted TransportToClip 実装                        | transport module  |
| 5-2  | ApproachCable → Transport → InsertIntoClip 1-clip E2E | 1-clip eval       |
| 5-3  | AerialRegrasp 挿入 (clip間遷移)                         | 2-clip eval       |
| 5-4  | 5-clip full routing                                | full routing eval |

**Gate G5:** 1-clip routing success 50%+

### GPU割当

| Phase | cuda:0              | cuda:2               |
| ----- | ------------------- | -------------------- |
| 1     | ApproachCable DAPG     | ApproachCable DAPG (並行) |
| 2 + 3 | InsertIntoClip DAPG | AerialRegrasp DAPG   |
| 4     | P1a訓練               | -                    |
| 5     | E2E統合               | -                    |

### 依存グラフ

```
P1 ──→ P2 ──→ P5
 │             ↑
 ├──→ P3 ──────┤
 │             │
 └──→ P4 ──────┘
```

### 現在地 (2026-04-05 Session 91)


- Phase 1 [v5]: **AC v35完走 → v36準備完了** (hybrid報酬, W_ORI=0.1, noise_std_max=1.0)
- Phase 2: **IC v17完走 → v18準備完了** (hybrid報酬, alpha 0.9→0.5, noise_std_max=1.0)
- Phase 3: **AR v22 完走待ち** (cuda:2, 256w, success=0.74%発生中)
- **Grip: clamp v2 稼働中** (cuda:2)。**unclamp v2 稼働中** (cuda:0)
- Phase 5: **5-0 Skill Adapter統合 DONE。** MSA方式 (skill_adapter.py)。**§14 Orchestrator設計追加**
- **報酬改修 (Session 94):** 全スキルでnoise_std単調増加の構造的問題を特定。AC/IC envにhybrid報酬（additive）・explosion固定ペナルティ・noise_std cap・sanitization強化を実装
- **クランプ/アンクランプ独立RL化 (Session 91確定):** 全ステップでclamp/unclampは独立RLスキル (GripEnv統合)
- **動的指バネ (Session 90):** AC/ARで動的指バネ方式を採用。ICは VBD dynamic body→cable force 伝達不成立により撤回→kinematic finger復帰 (v17)
- Phase 1': CANCELLED (v5設計転換でB統合env非互換)


## 2. 工程設計 (43ステップ)

### 用語


| 用語 | 意味 | 値 |
|------|------|-----|
| Home高度 | ホーム位置・復帰高度 | z=1.12 |
| 上昇点(routing) | ルーティングクリップ上空 (rise/above/regrasp) | z=1.07 |
| 上昇点(rest) | 置き台上空 (Phase A approach/lift) | z=1.05 |
| 下降点(X) | X位置のテーブル面 (GRASP_Z/PUSH_Z相当) | z=1.02 |
| クランプ | フィンガ閉 (cable把持) | 0.002 |
| 半アンクランプ | フィンガ半開き (cable軽保持・誘導用) | 0.006 |
| アンクランプ | フィンガ全開 (解放) | 0.04 |

> **Z値変更 (2026-03-28 セッション28):**
> - routing上昇: 1.12 → 1.07 (push Z=1.02 との gap を半減: 10cm→5cm)
> - Phase A approach/lift: 1.12 → 1.05 (IK到達性確保、REST_CLIPS X=0.15)
> - Phase A grasp X: 0.30 → 0.15 (REST_CLIPS位置と一致)
> - REST_CLIPS: X=0.15 (routing clips X=0.35 から20cm離間)

### クリップレイアウト (8クリップ)

**Routing方向:** C1(y=+0.15, 右ロボ側) → C5(y=-0.15, 左ロボ側)。SSOT: `task_config.py` CLIP_POSITIONS。

| クリップ | X | Y | 用途 |
|---------|------|--------|------|
| C1 | 0.35 | +0.150 | routing (千鳥 odd) |
| C2 | 0.40 | +0.075 | routing (千鳥 even) |
| C3 | 0.35 | 0.000 | routing (千鳥 odd) |
| C4 | 0.40 | -0.075 | routing (千鳥 even) |
| C5 | 0.35 | -0.150 | routing (千鳥 odd) |
| S1 | 0.15 | +0.200 | REST (cable支持) |
| S2 | 0.15 | 0.000 | REST (cable支持) |
| S3 | 0.15 | -0.200 | REST (cable支持) |

ロボットbase: L=(0, -0.35), R=(0, +0.35)。Z=TABLE_HEIGHT(0.80)。

> **Y座標統一 (2026-03-28 セッション31):**
> task_config.py / full_43step.json / Newton scripts の CLIP1_Y を統一。
> 旧: 4つの座標系が混在（task_config C1=y-0.15, JSON C1=y+0.15, Newton CLIP1_Y=-0.05）。
> 新: task_config.py CLIP_POSITIONS がSSoT。CLIP1_X/Y/Z を導出定数として追加。
> 6ファイルのハードコード CLIP1_Y=-0.05 を `from task_config import` に置換。



### 再クランプ手順 (C2-C5共通、4ステップ)

各クリップルーティング後、次クリップへ移動する前の再把持手順:

1. **CX上空移動**: 両手を次クリップ上空へ。L=半アンクランプ、R=アンクランプ
2. **L固定** (v2追加): Lをクランプ。ケーブルをL-handに固定。位置変更なし
3. **R再把持移動**: Rがケーブル位置へ移動（R-hand X = L-hand X。ケーブルはLに追従するため）
4. **両手クランプ**: 両手クランプで再把持完了

> **R-hand X = L-hand X の根拠:** ケーブルはL-handでクランプ済みのためL-hand位置に追従する。
> R-hand Y はクリップ間中点 `(prev_clip.y + next_clip.y) / 2`（dry-run固定値。wet-runでは nearest cable body query に置換予定）。

### Phase A: 初期把持 (STEP 1-5)

| STEP | 左ハンド      | 右ハンド      | 左フィンガ  | 右フィンガ  | 動作      |
| ---- | --------- | --------- | ------ | ------ | ------- |
| 1    | 上昇点(原点)   | 上昇点(原点)   | アンクランプ | アンクランプ | 初期位置    |
| 2    | 上昇点(ケーブル) | 上昇点(ケーブル) | アンクランプ | アンクランプ | ケーブル上空へ |
| 3    | 下降点(ケーブル) | 下降点(ケーブル) | アンクランプ | アンクランプ | ケーブルへ下降 |
| 4    | 下降点(ケーブル) | 下降点(ケーブル) | クランプ   | クランプ   | ケーブル把持  |
| 5    | 上昇点(ケーブル) | 上昇点(ケーブル) | クランプ   | クランプ   | 持ち上げ    |

### Phase B: C1 ルーティング (STEP 6-10)

| STEP | 左ハンド    | 右ハンド    | 左フィンガ   | 右フィンガ  | クリップ状態 | 動作         |
| ---- | ------- | ------- | ------- | ------ | ------ | ---------- |
| 6    | 上昇点(C1) | 上昇点(C1) | クランプ    | クランプ   | -      | C1上空へ搬送    |
| 7    | 下降点(C1) | 下降点(C1) | クランプ    | クランプ   | -      | C1へ押し込み    |
| 8    | 下降点(C1) | 下降点(C1) | 半アンクランプ | アンクランプ | -      | 誘導ハンド半保持   |
| 9    | 下降点(C1) | 下降点(C1) | 半アンクランプ | アンクランプ | C1クランプ | C1がcable固定 |
| 10   | 上昇点(C1) | 上昇点(C1) | 半アンクランプ | アンクランプ | C1     | C1から上昇     |
|      |         |         |         |        |        |            |

### Phase C+D: C2 ルーティング (STEP 11-18)

| STEP | 左ハンド    | 右ハンド    | 左フィンガ   | 右フィンガ  | クリップ状態 | 動作            |
| ---- | ------- | ------- | ------- | ------ | ------ | ------------- |
| 11   | 上昇点(C2) | 上昇点(C2) | 半アンクランプ | アンクランプ | C1     | C2上空へ         |
| 12   | 上昇点(C2) | 上昇点(C2) | クランプ    | アンクランプ | C1     | 左クランプ（ケーブル固定） |
| 13   | 上昇点(C2) | ケーブル    | クランプ    | アンクランプ | C1     | 右がケーブル再把持へ    |
| 14   | 上昇点(C2) | ケーブル    | クランプ    | クランプ   | C1     | 両手クランプ        |
| 15   | 下降点(C2) | 下降点(C2) | クランプ    | クランプ   | C1     | C2へ押し込み       |
| 16   | 下降点(C2) | 下降点(C2) | クランプ    | クランプ   | C1,C2  | C2固定          |
| 17   | 下降点(C2) | 下降点(C2) | 半アンクランプ | アンクランプ | C1,C2  | 解放            |
| 18   | 上昇点(C2) | 上昇点(C2) | 半アンクランプ | アンクランプ | C1,C2  | 上昇            |

### Phase C+D: C3 ルーティング (STEP 19-26)

| STEP | 左ハンド | 右ハンド | 左フィンガ | 右フィンガ | クリップ状態 | 動作 |
|------|---------|---------|-----------|-----------|------------|------|
| 19 | 上昇点(C3) | 上昇点(C3) | 半アンクランプ | アンクランプ | C1,C2 | C3上空へ |
| 20 | 上昇点(C3) | 上昇点(C3) | クランプ | アンクランプ | C1,C2 | 左クランプ（ケーブル固定） |
| 21 | 上昇点(C3) | ケーブル | クランプ | アンクランプ | C1,C2 | 右がケーブル再把持へ |
| 22 | 上昇点(C3) | ケーブル | クランプ | クランプ | C1,C2 | 両手クランプ |
| 23 | 下降点(C3) | 下降点(C3) | クランプ | クランプ | C1,C2 | C3へ押し込み |
| 24 | 下降点(C3) | 下降点(C3) | クランプ | クランプ | C1-C3 | C3固定 |
| 25 | 下降点(C3) | 下降点(C3) | 半アンクランプ | アンクランプ | C1-C3 | 解放 |
| 26 | 上昇点(C3) | 上昇点(C3) | 半アンクランプ | アンクランプ | C1-C3 | 上昇 |

### Phase C+D: C4 ルーティング (STEP 27-34)

| STEP | 左ハンド    | 右ハンド    | 左フィンガ   | 右フィンガ  | クリップ状態 | 動作            |
| ---- | ------- | ------- | ------- | ------ | ------ | ------------- |
| 27   | 上昇点(C4) | 上昇点(C4) | 半アンクランプ | アンクランプ | C1-C3  | C4上空へ         |
| 28   | 上昇点(C4) | 上昇点(C4) | クランプ    | アンクランプ | C1-C3  | 左クランプ（ケーブル固定） |
| 29   | 上昇点(C4) | ケーブル    | クランプ    | アンクランプ | C1-C3  | 右がケーブル再把持へ    |
| 30   | 上昇点(C4) | ケーブル    | クランプ    | クランプ   | C1-C3  | 両手クランプ        |
| 31   | 下降点(C4) | 下降点(C4) | クランプ    | クランプ   | C1-C3  | C4へ押し込み       |
| 32   | 下降点(C4) | 下降点(C4) | クランプ    | クランプ   | C1-C4  | C4固定          |
| 33   | 下降点(C4) | 下降点(C4) | 半アンクランプ | アンクランプ | C1-C4  | 解放            |
| 34   | 上昇点(C4) | 上昇点(C4) | 半アンクランプ | アンクランプ | C1-C4  | 上昇            |

### Phase C+D: C5 ルーティング (STEP 35-42)

| STEP | 左ハンド | 右ハンド | 左フィンガ | 右フィンガ | クリップ状態 | 動作 |
|------|---------|---------|-----------|-----------|------------|------|
| 35 | 上昇点(C5) | 上昇点(C5) | 半アンクランプ | アンクランプ | C1-C4 | C5上空へ |
| 36 | 上昇点(C5) | 上昇点(C5) | クランプ | アンクランプ | C1-C4 | 左クランプ（ケーブル固定） |
| 37 | 上昇点(C5) | ケーブル | クランプ | アンクランプ | C1-C4 | 右がケーブル再把持へ |
| 38 | 上昇点(C5) | ケーブル | クランプ | クランプ | C1-C4 | 両手クランプ |
| 39 | 下降点(C5) | 下降点(C5) | クランプ | クランプ | C1-C4 | C5へ押し込み |
| 40 | 下降点(C5) | 下降点(C5) | クランプ | クランプ | C1-C5 | C5固定 |
| 41 | 下降点(C5) | 下降点(C5) | 半アンクランプ | アンクランプ | C1-C5 | 解放 |
| 42 | 上昇点(C5) | 上昇点(C5) | 半アンクランプ | アンクランプ | C1-C5 | 上昇 |

### Phase E: 完了 (STEP 43)

| STEP | 左ハンド | 右ハンド | 左フィンガ | 右フィンガ | クリップ状態 | 動作 |
|------|---------|---------|-----------|-----------|------------|------|
| 43 | 上昇点(原点) | 上昇点(原点) | アンクランプ | アンクランプ | C1-C5 | ホーム復帰 |

### 2.1 Cable Layout & Segment-Clip Routing Plan (2026-03-29)

**Cable:**
- 40 segments (body 0–39), SEG_LEN=15mm, total=600mm
- Y方向 (direction=(0,1,0))、center Y = CLIP_Y_CENTER (0.000)
- Y range: [−0.300, +0.300]
- Body n START position: Y = −0.300 + n × 0.015
- **注意:** Newton `add_rod` の `body_q[:3]` はカプセルの START 位置（FRAME原点）を返す。カプセル中心は START + 0.0075 (half_seg_len)。距離計算時に 7.5mm の系統誤差が生じうる（TODO: 修正）

**GRIP_HALF_SPAN** = 30mm = 2 segments

**ルーティング方向:** C1 (+Y, body 30) → C5 (−Y, body 10)

| Clip | Clip Y | L hand Y | Groove Y | R hand Y | L body | Groove body | R body | Cable margin |
|------|--------|----------|----------|----------|--------|-------------|--------|-------------|
| C1 | +0.150 | +0.120 | +0.150 | +0.180 | 28 | 30 | 32 | R: 7 bodies (105mm) |
| C2 | +0.075 | +0.045 | +0.075 | +0.105 | 23 | 25 | 27 | |
| C3 | 0.000 | −0.030 | 0.000 | +0.030 | 18 | 20 | 22 | |
| C4 | −0.075 | −0.105 | −0.075 | −0.045 | 13 | 15 | 17 | |
| C5 | −0.150 | −0.180 | −0.150 | −0.120 | 8 | 10 | 12 | L: 8 bodies (120mm) |

**導出根拠:**
- Clip間隔 = 75mm = 5 segments → groove: 30, 25, 20, 15, 10
- GRIP_HALF_SPAN = 30mm = 2 segments → L = groove − 2, R = groove + 2
- Cable端余裕: C1右手 (body 32) から端 (body 39) まで 105mm、C5左手 (body 8) から端 (body 0) まで 120mm

**再クランプ時のセグメント対応 (C2–C5):**

各クリップへの再クランプ時、L hand が先にケーブルを固定し、R hand が指定セグメントへ移動して再把持する。

| Step | 動作 | L hand seg | R hand seg |
|------|------|-----------|-----------|
| STEP 11-14 (C2) | L固定→R再把持 | body 21 | body 29 |
| STEP 19-22 (C3) | L固定→R再把持 | body 16 | body 24 |
| STEP 27-30 (C4) | L固定→R再把持 | body 11 | body 19 |
| STEP 35-38 (C5) | L固定→R再把持 | body 6 | body 14 |

**スクリプト更新要件:**
- `cable_y_start` 計算: 全スクリプトで `CLIP1_Y - cable_half_len` → `CLIP_Y_CENTER - cable_half_len` に変更が必要
- 対象: `newton_approach_cable_env.py`, `test_newton_clip_routing.py`, `collect_approach_cable_demos.py`, `wet_run_full_sequence.py`, `test_grip_modes.py`
- 単クリップRL訓練 (Phase 1): `CLIP1_Y - cable_half_len` でも動作するが、multi-clip一貫性のため変更推奨

### 2.2 STEP ↔ Cable Segment 対応表

全43ステップにおける各手のクランプ対象セグメント（cable body index）とgroove挿入対象。
`(h)` = 半アンクランプ（しごき保持）、`—` = 接触なし。

| STEP | Phase | Clip | L hand body | R hand body | Groove body→Clip | 動作 |
|------|-------|------|------------|------------|-----------------|------|
| 1 | A | — | — | — | — | 初期位置 |
| 2 | A | — | — | — | — | ケーブル上空へ |
| 3 | A | — | →26 | →34 | — | ケーブルへ下降 |
| 4 | A | — | **26** | **34** | — | 初期把持（クランプ） |
| 5 | A | — | **26** | **34** | — | 持ち上げ |
| 6 | B | C1 | **26** | **34** | — | C1上空へ搬送 |
| 7 | B | C1 | **26** | **34** | 30→C1 | C1へ押し込み |
| 8 | B | C1 | 26(h) | — | C1=30 | 誘導ハンド半保持 |
| 9 | B | C1 | 26(h) | — | C1=30 | C1がcable固定 |
| 10 | B | C1 | 26(h) | — | C1=30 | C1から上昇 |
| 11 | C | C2 | 21(h) | — | C1=30 | C2上空へ |
| 12 | C | C2 | **21** | — | C1=30 | 左クランプ |
| 13 | C | C2 | **21** | →29 | C1=30 | 右がケーブル再把持へ |
| 14 | C | C2 | **21** | **29** | C1=30 | 両手クランプ |
| 15 | D | C2 | **21** | **29** | 25→C2 | C2へ押し込み |
| 16 | D | C2 | **21** | **29** | C2=25 | C2固定 |
| 17 | D | C2 | 21(h) | — | C1=30,C2=25 | 解放 |
| 18 | D | C2 | 21(h) | — | C1=30,C2=25 | 上昇 |
| 19 | C | C3 | 16(h) | — | C1=30,C2=25 | C3上空へ |
| 20 | C | C3 | **16** | — | C1=30,C2=25 | 左クランプ |
| 21 | C | C3 | **16** | →24 | C1=30,C2=25 | 右がケーブル再把持へ |
| 22 | C | C3 | **16** | **24** | C1=30,C2=25 | 両手クランプ |
| 23 | D | C3 | **16** | **24** | 20→C3 | C3へ押し込み |
| 24 | D | C3 | **16** | **24** | C3=20 | C3固定 |
| 25 | D | C3 | 16(h) | — | C1-C3 | 解放 |
| 26 | D | C3 | 16(h) | — | C1-C3 | 上昇 |
| 27 | C | C4 | 11(h) | — | C1-C3 | C4上空へ |
| 28 | C | C4 | **11** | — | C1-C3 | 左クランプ |
| 29 | C | C4 | **11** | →19 | C1-C3 | 右がケーブル再把持へ |
| 30 | C | C4 | **11** | **19** | C1-C3 | 両手クランプ |
| 31 | D | C4 | **11** | **19** | 15→C4 | C4へ押し込み |
| 32 | D | C4 | **11** | **19** | C4=15 | C4固定 |
| 33 | D | C4 | 11(h) | — | C1-C4 | 解放 |
| 34 | D | C4 | 11(h) | — | C1-C4 | 上昇 |
| 35 | C | C5 | 6(h) | — | C1-C4 | C5上空へ |
| 36 | C | C5 | **6** | — | C1-C4 | 左クランプ |
| 37 | C | C5 | **6** | →14 | C1-C4 | 右がケーブル再把持へ |
| 38 | C | C5 | **6** | **14** | C1-C4 | 両手クランプ |
| 39 | D | C5 | **6** | **14** | 10→C5 | C5へ押し込み |
| 40 | D | C5 | **6** | **14** | C5=10 | C5固定 |
| 41 | D | C5 | 6(h) | — | C1-C5 | 解放 |
| 42 | D | C5 | 6(h) | — | C1-C5 | 上昇 |
| 43 | E | — | — | — | C1-C5 | ホーム復帰 |

**凡例:**
- **太字**: クランプ中（フルクランプ、cable body指定）
- `(h)`: 半アンクランプ（しごき位置、cable軽保持）
- `→N`: 移動中（body Nへ接近中、まだクランプ前）
- `—`: 接触なし（アンクランプ or ケーブル未到達）
- `N→Cn`: groove body N をクリップ Cn に挿入する動作
- `Cn=N`: クリップ Cn がbody N を保持中

**パターン（C2-C5共通）:**
1. 移動: L=(h), R=— → L hand が次クリップ用 body へ移動
2. L固定: L=**clamp** → L hand が先に cable を固定
3. R再把持: R=→body → R hand が cable へ接近
4. 両手clamp: L+R=**clamp** → insert準備完了
5. 押し込み: groove body → clip
6. 解放: L=(h), R=— → 次クリップへ移行

### 2.3 STEP→Skill 完全マッピング (2026-04-05)

全43 STEPの実行担当スキルと種別。RL=学習、S=scripted、W=待機/確認。

#### Phase A: 初期把持 (STEP 1-5)

| STEP | Skill | Type | 動作 | L finger | R finger |
|------|-------|------|------|----------|----------|
| 1 | TransportToClip | S | Home位置 | — | — |
| 2 | TransportToClip | S | ケーブル上空 | — | — |
| 3 | ApproachCable | RL | approach (finger OPEN維持) | — | — |
| 4 | Clamp | RL | L+R同時クランプ | OPEN→0.002 | OPEN→0.002 |
| 5 | TransportToClip | S | リフト | — | — |

#### Phase B: C1 ルーティング (STEP 6-10)

| STEP | Skill | Type | 動作 | L finger | R finger |
|------|-------|------|------|----------|----------|
| 6 | TransportToClip | S | C1上空搬送 | — | — |
| 7 | InsertIntoClip | RL | C1 groove押込 | — | — |
| 8 | HalfUnclamp+Release | S | L半開放+R全開放 | 0.002→0.006 | 0.002→0.04 |
| 9 | (ClipConfirm) | W | C1ラッチ確認 | — | — |
| 10 | TransportToClip | S | C1上昇 | — | — |

#### Phase C+D: C2-C5 共通パターン (8 STEP/clip)

STEP番号: C2=11-18, C3=19-26, C4=27-34, C5=35-42。オフセット +0〜+7。

| Offset | Skill | Type | 動作 | L finger | R finger |
|--------|-------|------|------|----------|----------|
| +0 | TransportToClip | S | Cn上空移動 | — | — |
| +1 | ReClamp(L) | S | L再クランプ (半→全) | 0.006→0.002 | — |
| +2 | AerialRegrasp | RL | R再把持approach | — | — |
| +3 | Clamp(R) | RL | R把持 | — | OPEN→0.002 |
| +4 | InsertIntoClip | RL | Cn groove押込 | — | — |
| +5 | (ClipConfirm) | W | Cnラッチ確認 | — | — |
| +6 | HalfUnclamp+Release | S | L半開放+R全開放 | 0.002→0.006 | 0.002→0.04 |
| +7 | TransportToClip | S | 上昇 | — | — |

> **C1→C2遷移 (offset +0, STEP 11):** Handover（腕役割切替 R支配→L支配）を含む。§1参照。

#### Phase E: 完了 (STEP 43)

| STEP | Skill | Type | 動作 | L finger | R finger |
|------|-------|------|------|----------|----------|
| 43 | TransportToClip | S | Home復帰 | 0.006→0.04 | — |

#### 集計

| Skill | Type | STEP数 | 対応STEP |
|-------|------|--------|----------|
| ApproachCable | RL | 1 | 3 |
| Clamp | RL | 5 | 4, 14, 22, 30, 38 |
| InsertIntoClip | RL | 5 | 7, 15, 23, 31, 39 |
| AerialRegrasp | RL | 4 | 13, 21, 29, 37 |
| TransportToClip | S | 14 | 1,2,5,6,10,11,18,19,26,27,34,35,42,43 |
| ReClamp(L) | S | 4 | 12, 20, 28, 36 |
| HalfUnclamp+Release | S | 5 | 8, 17, 25, 33, 41 |
| ClipConfirm | W | 5 | 9, 16, 24, 32, 40 |
| **合計** | | **43** | |

> **RL: 15 STEP (35%) / scripted: 23 STEP (53%) / wait: 5 STEP (12%)**
>
> **ユーザーテーブルとの差分 (2026-04-05レビュー):**
> - ~~HalfClamp STEPs 12,20,28,36 = finger固定値0.006~~ → 実際は0.002 (全クランプ)。ReClamp(L) に改名
> - Unclamp RL / 半クランプ: 43ステップ表に直接対応STEPなし (§1 注記参照)

---

## 3. P1 工程分割 (ApproachCable)

### 3段分割 (2026-03-27 rs決定)

左手が先行してcable固定 → 右手が後から把持。

| Sub-phase | Arm | 制御 | 内容 |
|-----------|-----|------|------|
| P1a: しごき | Left | **RL** | EE delta XY + finger delta。cable変形に適応 |
| P1b: 左クランプ | Left | **Scripted** | HALF_OPEN → FULL_CLOSE |
| P1c: 右把持+lift | Right | **RL** | Descend → close → lift |

### 圏論的ポリシー合成

```
P1a:  (S, mu_p0)      -> (S, mu_shigoki)     [RL, Left arm]
P1b:  (S, mu_shigoki) -> (S, mu_clamped)     [Scripted, Left finger close]
P1c:  (S, mu_clamped) -> (S, mu_lifted)      [RL, Right arm]
```

合成が well-defined になる条件: cod(pi_k) = dom(pi_{k+1})

**解消方針:**
- A (型合わせ): P1a+P1b実装 → mu_clamped生成 → P1cを mu_clamped で訓練
- B (現行の位置づけ): mu_p0 での訓練は「右手grasp学習可能性テスト」。成功率が出れば precondition を差し替え

### Action space

### Action space (v5統一, 2026-04-06 D2改訂)

**全RLスキル 12D統一:**

| Index | 内容 | 備考 |
|-------|------|------|
| 0-2 | 右EE ΔXYZ | POS_ACTION_SCALE (15mm/step) |
| 3-5 | 右EE Δaxis-angle | ROT_ACTION_SCALE (0.05 rad/step) |
| 6-8 | 左EE ΔXYZ | POS_ACTION_SCALE (15mm/step) |
| 9-11 | 左EE Δaxis-angle | ROT_ACTION_SCALE (0.05 rad/step) |

- **全RLスキル (AC/IC/AR/Clamp):** 12D action。finger は env 側 auto-control (AC: disable, Clamp: pos+ori閾値, IC/AR: 役割固定)
- **Unclamp:** scripted (RL不使用)。§4.0参照
- **[Rs 2026-06-24] 5th forward RL skill = Guide/Route (しごき; 現 scripted TransportToClip `step_table.py:46`) — CONFIRMED added (4→5).** RL-ization は obs 拡張に GATED (rule-21: route-stability 報酬は full cable-shape を要するが 45D obs は最近接 segment のみ) + reward-design+L3 impl gate。⚠ CLAMP を AC/AR に fold する案 = 5CC Debate 2026-06-24 で NO_ACTION (AC と CLAMP は別 env/policy; parked merge の蒸し返し)。詳細 `log.md` 2026-06-24。
- 旧設計 (v13以前): 6D → v5: 14D統一 → D2: 12D統一 (finger action廃止)


## 4. スキル詳細設計

### 成功条件定義 (2026-03-29 v3)

#### 設計原理

成功条件 = **対応セグメントの位置姿勢が所望の状態であるか**

- clamp: フィンガと対応セグメントの相対位置姿勢
- seated: クリップと対応セグメントの相対位置姿勢

#### 共通プリミティブ: approach / clamp / seated

**±1 body ウィンドウ:** GRIP_HALF_SPAN = 30mm = 2 segments（整数倍）→ 手位置が常にセグメント接続部に来る。隣接bodyを許容する (v13 GRIP_SEG_WINDOW = 1)。

```python
def approach(hand, n):
    """ハンドが対応セグメントの把持可能位置・姿勢に到達している (finger状態は問わない)"""
    pos  = min(dist(hand, body[k]) for k in [n-1, n, n+1]) < T_DIST_APPROACH  # 12mm (Grip INIT_POS_NOISE=12mmと整合)
    ori  = |dot(cable_tangent(n), finger_close_axis(hand))| < T_ALIGN
    return pos and ori

def clamp(hand, n):
    """フィンガが対応セグメントを所望の位置姿勢でクランプしている (= approach + grip)"""
    pos  = min(dist(hand, body[k]) for k in [n-1, n, n+1]) < T_DIST
    ori  = |dot(cable_tangent(n), finger_close_axis(hand))| < T_ALIGN
    grip = finger_opening(hand) < T_FINGER
    return pos and ori and grip

def seated(groove_n, clip):
    """対応セグメントがクリップ溝に所望の位置姿勢で嵌合している"""
    pos = min(dist(body[k], clip.center) for k in [groove_n-1, groove_n, groove_n+1]) < T_GROOVE
    ori = |dot(cable_tangent(groove_n), clip.groove_axis)| > T_SEAT
    return pos and ori
```

**clamp 姿勢条件:** ケーブル接線がフィンガ閉方向と直交 → 両パッドで挟める。平行だとすり抜ける。
**seated 姿勢条件:** ケーブル接線が溝走行方向と平行 → 溝に着座。直交だと嵌合しない。

**cable_tangent(n):** `normalize(body[n+1].pos - body[n-1].pos)` (前後bodyの差分で平滑化)。端点 body 0, 39 は片側差分。

#### ApproachCable SUCCESS (approach-only, STEP 3完了判定)

```
SUCCESS = approach(L, L_n) ∧ approach(R, R_n) ∧ sustained(K=5)
```

> **タスク定義変更 (2026-04-03 Session 83):** ApproachCableはapproach-onlyスキル。
> finger closeは次ステップ（scripted or 別スキル）の責務。
> 成功 = 両腕の位置+姿勢が把持可能位置に到達し維持。finger_openingは判定しない。

Phase 1 簡略化 (P1c, 右腕のみ): `approach(R, R_n) ∧ sustained(K=5)`

#### InsertIntoClip SUCCESS (STEP 9/16/24/32/40)

```
SUCCESS = seated(groove_n, clip_n) ∧ sustained(K=10)
```

#### AerialRegrasp SUCCESS

> ⚠️ **STALE / SUPERSEDED 2026-05-12** per Rs代行 disposition `T_ROOT_COORD_V6_FINAL_VERDICT_PASS_BEHAVIORAL_SIGNAL_NEGATIVE_DELTA_20260512_0830 root` Decision C step 4 (P0.2 sync, post Phase 4 #2 V6 close).
>
> **Locked AR success criterion (canonical, used in V5/V6 evaluation, all 30720 completions canonical_k_parity_pass=true):**
> ```
> SUCCESS = clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)
> ```
>
> The "approach(L) ∧ approach(R)" wording below is a 2026-04-03 Session 83 historical design interpretation that does NOT match the current standing verdict and is NOT used in evaluation/training/acceptance. Preserved for traceability only. Do NOT cite the historical block below as authoritative.

##### Historical block (Session 83, 2026-04-03; preserved for traceability)

```
SUCCESS = approach(L, L_n) ∧ approach(R, R_n) ∧ cable_not_dropped ∧ sustained(K=5)
```

`cable_not_dropped = min(body[k].z for all k) > TABLE_HEIGHT + 0.02`

> **タスク定義変更 (2026-04-03 Session 83、HISTORICAL — superseded by clamp(R)-based locked criterion 2026-05-12):** AerialRegraspもapproach-onlyスキル。
> finger closeは次ステップの責務。ApproachCableと同様、finger_openingは判定しない。

ApproachCable と構造同一。差分は `cable_not_dropped`（空中操作の落下検知）のみ。

#### Target bodies (Section 2.1 Routing Plan)

| Clip | L_n | groove_n | R_n |
|------|-----|----------|-----|
| C1 | 26 | 30 | 34 |
| C2 | 21 | 25 | 29 |
| C3 | 16 | 20 | 24 |
| C4 | 11 | 15 | 19 |
| C5 | 6 | 10 | 14 |

±1 window 適用後の実効範囲: L_n±1, groove_n±1, R_n±1

#### 閾値

| パラメータ | 値 | 根拠 |
|-----------|-----|------|
| T_FINGER | 12mm | 2×CABLE_RADIUS(4mm) + 4mm margin |
| T_DIST | 2mm | clamp/grip精密位置閾値 (task_config.py SSOT) |
| T_DIST_APPROACH | 12mm | approach粗位置閾値。Grip INIT_POS_NOISE=12mmと整合 (2026-04-07) |
| T_ALIGN | TBD | clamp姿勢。実測で決定（cos閾値、0に近いほど直交） |
| T_GROOVE | 3mm | CLIP_GROOVE_INNER_RADIUS(6mm) の半分。溝内着座判定 |
| T_SEAT | TBD | seated姿勢。実測で決定（cos閾値、1に近いほど平行） |
| K (grasp) | 5 steps | 50 physics steps = 0.42s |
| K (insert) | 10 steps | 100 physics steps = 0.83s。嵌合安定性に長い保持 |

#### 偽陽性排除

| 偽陽性パターン | 排除する条件 |
|---------------|-------------|
| finger open + cable跳ね | clamp.grip |
| finger close空振り | clamp.pos |
| ケーブルがフィンガ閉方向に平行（すり抜け） | clamp.ori |
| 間違ったセグメントを把持 | clamp.pos の target body ±1 指定 |
| 片手のみclamp | L∧R 両手条件 |
| 溝に対して斜め/直交に接触 | seated.ori |
| 瞬間的な接触 | sustained(K) |
| 空中操作でcable落下 | cable_not_dropped |

#### 廃止条件 (旧C1-C5体系)

| 旧条件 | 状態 | 理由 |
|--------|------|------|
| C1 (Grip closure) | → clamp.grip | |
| C2 (Cable contact) | → clamp.pos | |
| C3 (Relative lift) | 廃止 | scripted工程 (STEP 5) |
| C4 (Co-movement) | 廃止 | clamp L∧R で代替 |
| C5 (Sustained) | → sustained(K) | |
| F1 (Both-pad) | → clamp(L) ∧ clamp(R) | |

### 特徴量×成功条件×報酬関数 整合性マトリクス

### 特徴量×成功条件×報酬関数 整合性マトリクス (v5)

| 成功条件 | 判定量 | obs対応 | dense報酬 | sparse報酬 | 整合 |
|---------|--------|---------|----------|-----------|------|
| clamp.pos | min dist(hand, body[n±1]) | obs[0:2]/[8:10] vs obs[16:18] | R_pos | R_step (gate) | OK |
| clamp.ori | quat_dist(hand, seg) | obs[3:6]/[11:14] vs obs[19:22] | R_ori | R_step (gate) | OK |
| clamp.grip | finger_opening | obs[7] (R), obs[15] (L) | — (auto) | R_step (gate) | OK |
| seated.pos | min dist(body[n±1], clip) | obs[16:18] vs obs[23:25] | R_pos | R_step (gate) | OK |
| seated.ori | quat_dist(seg, clip) | obs[19:22] vs obs[26:29] | R_ori | R_step (gate) | OK |
| sustained | temporal counter | — | — | R_step (gate) | OK |
| cable_not_dropped | min cable_z | env内部計算 | — | R_drop | OK |

**全成功条件がobs内の位置・姿勢quatから直接計算可能。** 関係量(距離・alignment)を事前計算してobsに入れる必要なし。


### Obsスケーリング根拠

### 統一 obs / action / 報酬設計 (v5, 2026-03-30)

全スキル共通。スキル固有の差分は各スキルセクション参照。

#### obs 42D (世界座標・quaternion w>0正規化) — 2026-04-05更新

> **v5設計 (30D) → 実装 (42D):** 全4 env (AC, Grip, IC, AR) で共通42D。
> 追加12D = L/R各 position error + orientation error。事前計算した誤差信号により学習効率向上。

| Index | 特徴量 | 次元 | オブジェクト |
|-------|--------|------|------------|
| 0-2 | 右クランプ部位置 XYZ | 3D | 右ハンド |
| 3-6 | 右クランプ部姿勢 quat (xyzw, w>0) | 4D | 右ハンド |
| 7 | 右finger opening | 1D | 右ハンド |
| 8-10 | 左クランプ部位置 XYZ | 3D | 左ハンド |
| 11-14 | 左クランプ部姿勢 quat (xyzw, w>0) | 4D | 左ハンド |
| 15 | 左finger opening | 1D | 左ハンド |
| 16-18 | target seg位置 XYZ | 3D | ケーブル |
| 19-22 | target seg姿勢 quat (xyzw, w>0) | 4D | ケーブル |
| 23-25 | 現ターゲットclip位置 XYZ | 3D | クリップ |
| 26-29 | 現ターゲットclip姿勢 quat (xyzw, w>0) | 4D | クリップ |
| 30-32 | 右 orientation error (axis-angle) | 3D | R hand→target seg |
| 33-35 | 右 position error (hand−target) | 3D | R hand→target seg |
| 36-38 | 左 orientation error (axis-angle) | 3D | L hand→target seg |
| 39-41 | 左 position error (hand−target) | 3D | L hand→target seg |

**設計原則:**
- **クランプ部位置:** `clamp_pos = ee_pos + quat_rotate(ee_quat, [0, 0, -EE_TO_FINGERTIP])`。EEリンクではなくfingertip
- **姿勢はquat (w>0):** RPYはpitch≈-90°でgimbal lock。double-cover対策: `if w < 0: q = -q`
- **temporal consistency:** quatのdouble-coverフリップ防止。前フレームquatとの内積が負なら符号反転
- **error信号 [30:42]:** 報酬関数と同一のposition/orientation errorを事前計算。policyの負荷を軽減し、学習初期の収束を加速
- **orientation error:** axis-angle形式 (3D)。`quat_diff → log → axis_angle`。回転の大きさと方向を直接表現
- **position error:** `hand_clamp_pos - target_seg_pos` (3D)。符号付き誤差ベクトル
- **GripEnv clamp mode:** L/R各arm独立nearest cable point。**unclamp mode:** groove最近傍cable point（両arm共通）
- **ロボット関節角なし:** 報酬と無関係。IKソルバーが処理
- **STEP番号なし:** 報酬と無関係
- **target seg:** ±1窓内最近傍body。報酬・成功条件と整合

#### action 12D (全RLスキル統一, D2改訂 2026-04-06)

| Index | 内容 | 次元 | 備考 |
|-------|------|------|------|
| 0-2 | 右EE ΔXYZ | 3D | POS_ACTION_SCALE (15mm/step) |
| 3-5 | 右EE Δaxis-angle | 3D | ROT_ACTION_SCALE (0.05 rad/step) |
| 6-8 | 左EE ΔXYZ | 3D | POS_ACTION_SCALE |
| 9-11 | 左EE Δaxis-angle | 3D | ROT_ACTION_SCALE |

- DiffIK `command_type="pose"` に直結。Δquat 4Dは過剰パラメータ+正規化制約のため不採用
- **全RLスキル (AC/IC/AR/Clamp):** 12D action。finger は env 側 auto-control
  - AC: disable_finger_close=True (C1後にClamp必要)
  - Clamp: pos+ori閾値で自動close (5mm + ~20deg)
  - IC/AR: 役割固定 (RIGHT=auto-close, LEFT=CLOSED)
- **Unclamp:** scripted (RL不使用)
- ~~旧: 14D (12D EE + 2D finger)。D2で finger action廃止~~

#### 報酬構造 (pose_matchベース)

```
R_pos = -||current_pos - target_pos|| / ε_pos   (w_pos=1.0)
R_ori = -quat_dist(current_quat, target_quat) / ε_ori   (w_ori=1.0)
R_step = 5.0   (STEP完了ボーナス、pose_match達成時)
R_task = 20.0   (全STEP完了ボーナス)
R_penalty = -0.01   (ステップペナルティ)

R_total = w_pos * R_pos + w_ori * R_ori + R_step + R_task + R_penalty
```

- ε_pos = 15mm (EPS_POS), ε_ori = 0.25 rad
- 正規化済みで閾値付近で同スケール(-1.0) → 等重み自然
- 両手STEPの場合: `R = R_right + R_left` (加算、平均化なし — 各腕フル勾配)
- 報酬ターゲットはSTEP依存: 把持→cable seg, 搬送→clip上昇点, 押し込み→clip位置

#### スケール感

| 状況 | R_pos (2腕合計) | R_ori (2腕合計) | R_step | 合計 |
|------|-----------------|-----------------|--------|------|
| 遠い (50mm, 0.5rad) | -2.03 | -1.73 | 0 | ≈-3.76 |
| 閾値 (12mm, 0.17rad) | -1.13 | -0.99 | +5.0 | ≈+2.88 |
| pose_match達成 | 0 | 0 | +5.0 | +5.0 |

#### 旧obs設計との対応 (v7→v5)

| 旧obs | 状態 | 新obs |
|-------|------|-------|
| obs[0:3] R EE XYZ | → クランプ部位置に変更 | obs[0:2] |
| obs[3:6] cable body XYZ | 維持 | obs[16:18] |
| obs[6] finger opening (×5) | スケーリング再検討 | obs[7] |
| obs[7] dist (×50) | 削除（導出可能） | — |
| obs[8:10] L EE XY | → クランプ部XYZ + Z追加 | obs[8:10] |
| obs[10] L finger (×5) | スケーリング再検討 | obs[15] |
| obs[11:13] tangent XYZ | → seg姿勢quat | obs[19:22] |
| — | 新規: 右ハンド姿勢 | obs[3:6] |
| — | 新規: 左ハンド姿勢 | obs[11:14] |
| — | 新規: clip位置+姿勢 | obs[23:29] |
| — | 新規: R ori error (axis-angle) | obs[30:32] |
| — | 新規: R pos error (hand−target) | obs[33:35] |
| — | 新規: L ori error (axis-angle) | obs[36:38] |
| — | 新規: L pos error (hand−target) | obs[39:41] |


### 乗算結合型 Progress 報酬 (全スキル共通)

2目的(a, b)を独立に報酬化すると magnitude 差で一方が支配する。乗算項で「両方同時改善」のみ強報酬。

```
score_a = clamp(1 - metric_a / range_a, 0, 1)
score_b = clamp(1 - metric_b / range_b, 0, 1)

progress = 0.2*a + 0.2*b + 0.6*a*b

R_progress = SCALE * max(0, delta_progress)
```

比率 0.2+0.2+0.6 の根拠:
- 積のみ (0+0+1): 片方=0で勾配ゼロ。学習不能
- 線形のみ (0.5+0.5+0): 競合そのまま
- 0.2+0.2+0.6: 線形項が最低限の勾配保証。積項が同時改善を強誘導

### 合成初期状態 (Synthetic Precondition)

スキル間の順序依存を解消し並行訓練を可能にする。

| 手法 | 挙動 | 許可 |
|------|------|------|
| kinematic attach | 毎stepでcable位置を強制上書き | 禁止 |
| 合成初期配置 | t=0で配置、以降VBD物理のみ | 許可 (reset直後) |

**2026-05-23 R2-A Track A consistency note:** 上表の禁止は cable 位置を毎step
強制上書きする fake grasp / kinematic attach を指す。Track A の
`release_after_success_hold_k` は別物で、左指 body を kinematic fixture として
pre-contact support する default-off diagnostic / product-shaping predicate。
Track A は C8I payload collection auth package review 完了・artifact consistency
patch 適用時点で
`C8I_PAYLOAD_COLLECTION_AUTH_PACKAGE_REVIEW_COMPLETE / PRODUCT_GO_FALSE`。C5A
support-manifold guard は high/mixed cable_drop 0.0 と success を C3B 同等に
保ち、high/mixed active explosion を timeout debt に変換した。C6B smoke は
492/492 completions で実行PASSだったが、tested timeout-recovery arms は全て
control と同一 outcome となり timeout debt を回復しなかった。C6C は
extended arm が timeout step 200 のままで、late probes は metadata 差分を
作るが terminal outcome を変えないことを確認した。C6D/C6E はこれを
eval-path telemetry contract に変換し、historical C6B を contract-fail として
扱う scaffold を 0GPU で実装した。C6F は C6E result を coherent と判定し、
same-scope C6B GPU repeat を BLOCKED、C6B no-go as run を SUPPORTED、
次を C6G 0GPU telemetry runner patch auth package とした。C6G は C6H
0GPU implementation の allowed/disallowed paths、required telemetry fields、
static/dry-run gates、future GPU preconditions を package 化した。
C6H は runner/report scaffold を新規 `eval_runs` 配下に実装し、
py_compile/check/dry-run/refusal/JSON validation PASS。dry-run は historical
C6B を expected failure として扱い、timeout step 200 と branch/env-horizon
telemetry missing を明示する。C6I は C6H を
`PASS_0GPU_CONTRACT_SCAFFOLD` と判定したが、future live eval runner の branch
activation/horizon evidence が未証明のため `gpu_auth_ready_now=false` とした。
C6J は executable GPU auth を `REDESIGN_REQUIRED_BEFORE_EXECUTABLE_GPU_AUTH`
として拒否し、future launch draft を `DRAFT_NOT_AUTHORIZED_BLOCKED_ON_C6K`
に留めた。
C6K は live eval-path telemetry runner scaffold を 0GPU で実装し、
py_compile/check/dry-run/unauthorized-refusal/JSON validation を PASS した。
C6L は C6M launch directive draft を `DRAFT_NOT_AUTHORIZED` として作成し、
`READY_FOR_RS_C6M_GPU_LAUNCH_DECISION_DRAFT_ONLY` と判定した。eval は未承認のまま。
C6M は corrected marker で cuda:0 smoke を実行し、492/492 completions、no abort。
C6E/C6H/C6K telemetry fields は全 record に存在し、late probe branch override と
extended horizon 260 は live だったが、全 candidate arm は control と同一 terminal
metrics で passing candidates は空。
C6N は telemetry plumbing と mechanism improvement を分離し、C6B/C6M
timeout-recovery candidate family を no-go as run supported と判定した。
C6O は同 candidate family を no-go as run として closeout し、same-scope
GPU repeat を blocked/not recommended とした。
C7 は primary non-repeat variable として `early_strict_ready_capture_controller`
を選定した。対象は C6M high/mixed active timeout rows `n=42` で、left hold と
cable-not-dropped は clean、near-clamp は sustained だが strict right-clamp dwell
が本質的に欠ける。C7A は 0GPU scaffold/auth package を実装し、
py_compile/check/dry-run/refusal PASS。eval/GPU は未承認。
C7B は C7A scaffold を review し、future C7C 0GPU launch-capable runner
implementation は準備可能だが GPU authorization ではないと判定した。
C7C は 0GPU launch-capable runner package を新規 `eval_runs` 配下に実装し、
py_compile/check/dry-run/refusal/JSON を PASS、target slice n=42/high_drop=20/
mixed=22/timeout=42 と future eval guard を確認した。
C7D は C7C runner を 0GPU review し、static gates は PASS だが valid-marker
path が `REFUSE_EVAL_C7D_REVIEW_REQUIRED` で止まり concrete eval implementation
へ移らないため GPU auth ready ではないと判定した。
C7E は copy-derived runner/package を 0GPU で実装し、valid-marker
`auth-dry-run` が `EVAL_TRANSFER_READY` を出すことを確認した。
C7F は C7E package を 0GPU review し、future C7G GPU smoke は draft-only で
initially packageable と判定したが、C7F correction で C7G draft marker prefix
mismatch と C7E valid-marker eval refusal を確認し、その GPU auth draft は
executable ではないと retracted/qualified した。C7H は 0GPU launch-path
implementation を完了し、future marker prefix を C7H runner/draft と一致させ、
invalid-marker eval refusal before heavy imports/simulator/CUDA/output writes と
valid-marker auth-dry-run `CONCRETE_FUTURE_EVAL_BOUNDARY_READY` を確認した。
C7I は C7H を 0GPU review し、future GPU-smoke package を draft-only ready と
判定したが launch は承認していない。C7J は fresh explicit scoped directive により
cuda:0 で 246/246 completions、no abort で実行PASSしたが、C7H candidate は
control と terminal metrics が完全一致し、terminal-signature delta は 0 だった。
C7K は 0GPU posthoc review で、early-capture activation は live だったが
bounded action magnitude/direction と trajectory-objective insufficiency により
strict right-clamp / terminal-candidate consecutive-step 改善が生じなかったと
結論した。C7L は `strict_ready_dwell_objective_policy_redesign` を選定し、
policy objective/loss と timeout debt 形成前の learned state trajectory を変える
設計へ進めた。C7M は loss package を定義したが、C7 target-slice trainable
per-step payload は未準備と判定した。C7N は 42-row target manifest と
future per-step payload schema を定義したが、payload collection execution は
していない。C7O は 0GPU payload runner scaffold を実装し、C7N manifest/schema
の check/dry-run、payload records/tensor shards 非生成、unauthorized collect/eval
refusal before heavy imports/simulator/CUDA/output writes を確認した。C7P は direct
payload collection auth を review し、C7O が collection-launch-capable ではないため
not ready と判定した。
 C7Q は 0GPU launch-capable runner scaffold を実装し、valid-marker
auth-dry-run が `PAYLOAD_COLLECTION_BOUNDARY_READY` に到達することを確認した。
C7R は actual `--mode collect` が refusal-only のままであるため collection launch
draft を blocked と判定した。C7S は valid-marker collect が
`COLLECT_PATH_BOUNDARY_READY` へ到達することを 0GPU で確認し、invalid-marker
refusal は before heavy imports/CUDA/simulator/output writes のまま保持した。
C7T は C7S package を artifact-only review し、future C7U launch decision を
`DRAFT_NOT_AUTHORIZED` として packageable と判定した。C7U は 1 回だけ command を
実行し、`COLLECT_PATH_BOUNDARY_READY` へ到達したが required payload outputs は
missing のため review-hold とした。C7V は older C2I writer を concrete prior writer
として確認し、future real records が渡された場合に required payload outputs を書く
C7-local `PayloadOutputWriter.write_payload_outputs(...)` scaffold を 0GPU で実装した。
C7W は C7V package を artifact-only review し、writer scaffold は valid だが
future bounded collect command が real per-step payload records と completion
records を writer に渡す concrete integration evidence は無いと判定した。C7X は
その 0GPU proof gap を閉じ、42 件の real-shaped payload records と 42 件の
completion records を in-memory で validate し、C7V writer signature へ exact
kwargs を bind、writer call は未実行で output writes は file write 前に suppress
した。C7Y は artifact-only review で launch draft を blocked とし、C7S collect
preflight、future real collector records、C7X adapter validation、C7V writer call
を単一 launch-capable runner/command で接続する evidence が未作成と判定した。
C7Z はこの missing runner proof を 0GPU で実装し、valid-marker launch-dry-run で
`COLLECTOR_WRITER_LAUNCH_BOUNDARY_READY`、42-row in-memory record validation、
C7X adapter application、C7V writer kwargs binding、writer/file-write suppression
を確認した。C8A は C7Z package を artifact-only review し、single-runner
boundary proof は閉じたが、current C7Z path は `writer_call_invoked=false` かつ
write-suppressed のため launch draft は boundary-only になると判定した。
C8B は write-disabled recording writer/shim を records ready 後に invoke し、
guarded writer invocation semantics を証明した。C8C はその package を
artifact-only review し、real C7V file-writing path が未実行で、real payload
outputs が生成されていないため launch draft は blocked と判定した。C8D は
actual C7V `PayloadOutputWriter.write_payload_outputs(...)` method を records ready
後に invoke し、real file-writing path を reached、lower-level file writes を
creation 前に intercept した。C8E は C8D package を artifact-only review し、
real writer method/path proof は closed としたが、valid collect が intercepted
dry-run に route して `collection_launch_suppressed_by_c8d_scope=true` であるため
launch draft は blocked と判定した。C8F は launch-capable future valid collect
path を `FileWriteInterceptor` なしで定義し、actual C7V writer signature を
future launch 用に bind、records-ready 後の writer invocation plan と
output-collision/invalid-marker refusal guards を確認した。C8F では writer
invocation、collection launch、payload outputs 生成はしていない。C8G は C8F
package を artifact-only review し、`FileWriteInterceptor` blocker は
launch-dry-run contract level で closed としたが、current C8F valid `--mode collect`
は dry-run/suppression-only で
`collection_launch_suppressed_by_c8f_0gpu_scope=true` のため launch draft は
blocked と判定した。C8H は valid `--mode collect` を
`EXECUTABLE_COLLECT_WRITER_OUTPUT_BOUNDARY_READY` に到達させ、C8F dry-run/
suppression marker を解消したが、collection launch、writer invocation for real
output writing、payload outputs 生成はしていない。C8I は C8H package を
artifact-only review し、C8J launch-decision package を `DRAFT_NOT_AUTHORIZED`
としてのみ draftable と判定した。artifact consistency patch で C8J draft の
stale previous-stage output path は除去済み。C8J は fresh scoped directive で
1 回だけ実行され、`EXECUTABLE_COLLECT_WRITER_OUTPUT_BOUNDARY_READY` には到達した
が、required payload output files は生成しなかった。C8K は C8H collect mode が
boundary manifest を print するだけで C7V writer を呼ばず、C8J `boundary_outputs`
を writer output root に bind していないことを特定した。
C8L は C8J `boundary_outputs` root を actual C7V writer path に write suppression
下で bind し、all five future output paths を intercept して real files を作成しない
ことを確認した。C8M は C8L proof fields を artifact-only review し、future C8N
payload-output completion launch-decision draft を `DRAFT_NOT_AUTHORIZED` として
作成した。C8N は fresh scoped 0GPU command で actual C7V writer path を invoke
し、C8J `boundary_outputs/results` 配下に exactly five authorized output files を
作成し、42 payload rows / 42 completion records を validate した。
`physical_grasp_claim=false`、`PRODUCT_GO=false`。T-ROOT 95%、物理把持、
product readiness、broad generalization、retraining completion は claim しない。
同一 scope repeat GPU は不要。C8O は five C8J result files、42 payload rows、
42 completion records、C7N required fields 22/22 coverage、target-slice identity、
protected SHA locks、forbidden-output absence を artifact-only review し、
`C8O_READY_FOR_C8P_PAYLOAD_DATASET_CONSUMPTION_OR_TRAINING_AUTH_REVIEW_DRAFT_ONLY`
とした。次は C8P payload dataset-consumption/training-auth review 0GPU、
broader productization/routing review、または HOLD であり、dataset consumption、
追加GPU、payload collection、retraining、tracked-source promotion は別途 scoped
directive が必要。C8P は payload semantics を artifact-only review し、C8J/C8N
payload は structural/provenance-ready only で training-auth not ready と判定した。
全 42 rows は dry-run/proxy-shaped で、actions/rewards は zero、strict-ready /
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
relay-side verification は PASS。C9BC は C9BB auth-dry-run function body に
`refresh_summary` call がなく、caller route manifest のみを書き、route output
が `c9bb_auth_dry_run_manifest.json` だけであり、required refusal proofs が
file creation 前に pass することを確認した。C9BC decision は
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
D0 control-source artifact-only review、D0 runner/preflight package も完了した。
D0 runner/preflight Tier-A review は INCOMPLETE だったが、GAP-A human-Rs
predicate attestation、GAP-B planning review、GAP-B functional runner
implementation、GAP-B schema-fix package、schema-fix review、GPU D0
authorization packet、authguard fix、supervisor `%3` authguardfix light review
まで完了し、その後の exact diagnostic-only GPU D0 launch は `lazy_loader`
missing で D0 前に abort した。0GPU import-runtime triage、separate canonical
runtime review、supervisor `%3` provisioning gate review、bounded
`env_isaaclab6` provisioning repair も完了し、`lazy-loader==0.5` が
`/home/rlrk/env_isaaclab6` に `--no-deps` で provision 済み。post-repair exact
GPU D0 gate は `%3` COMPLETE となり、`%7` が exactly once authorize したが、
Omniverse Kit EULA prompt / inner kit kernel EOF により D0 前に abort。runtime
switch は Python/Isaac Sim/Warp runtime family を変えるため選択しない。その後
runtime EULA/bootstrap review が 0GPU/read-only で完了し、
human/operator NVIDIA Omniverse/Isaac Sim EULA acceptance attestation、
separate exact D0 diagnostic command review が完了。future command は
transient `OMNI_KIT_ACCEPT_EULA=YES` を含むが `NOT_AUTHORIZED_DO_NOT_RUN`。
その後 `%3` が exact-command packet の Q4 blocker を COMPLETE とし、`%7` が
EULA-attested diagnostic-only cuda:0 command を 1 回だけ authorize。real `%4` は
exact command を実行したが、lazy env import が
`ImportError: cannot import name 'DeformableObject' from 'isaaclab.assets'`
で D0 前に abort。completion は 0/861、output root は absent、結果 artifact
なし。これは D0 outcome ではなく import API mismatch。relay は bounded 0GPU
import API mismatch review を完了し、原因を
`LOCAL_THREAD_PACKAGE_IMPORT_SIDE_EFFECT_PLUS_ISAACLAB_6_ASSET_API_SPLIT`
と分類。relay `%7` はその次手として
`eval_runs/r2a_track_a_runner_direct_import_bypass_0gpu_20260525/` の fresh
eval_runs-only runner direct-import bypass package を完了。new runner SHA は
`af5d6806a0cd125ccb552373c7b7c407d4a95b7aaab8aab35849b4a7f6223b0e`。変更は
future runner の import route のみで、`thread_isaac_lab/envs` から
`newton_aerial_regrasp_env` を direct import して package `__init__` /
legacy `assets_cfg.py` side effect を回避する。その後 `%3` Tier-A COMPLETE、
`%7` authorization を経て real `%4` が command を exactly once 実行したが、
runner は D0 前に `future_preconditions_failed` / `wrong_target_output_root`
で拒否。predicate attestation の `target_output_root` は
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_authguardfix_20260525`
で、command は
`eval_runs/r2a_track_a_gapb_functional_d0_gpu_diagnostic_direct_import_bypass_20260525`
を指定していた。両 root absent、completion 0/861、retry なし。relay `%7` は
bounded 0GPU exact-command alignment review を完了し、aligned root で
`validate_static_preconditions` が `STATIC_PRECONDITIONS_OK` を返すことを確認。
その後 `%3` corrected-root Tier-A COMPLETE、`%7` authorization を経て real `%4`
が corrected-root command を exactly once 実行したが、21/861 records すべて
`execution_status=ERROR` で D0 判定不能。その後 0GPU error review は missing
w41 cache と missing contact-sensor prim path を分類済み。w41 cache はその後
1 回の cuda:0 build で provision 済み。impedance arm は ContactSensor 未解決
として hold/drop され、6-arm D0 auth review は command packageability を
blocked と判定した。現在の次手は predicate attestation/output-root binding の
0GPU review、または HOLD。future D0 retry/execution、GPU/simulator、
ContactSensor remediation、source/task_config mutation、runtime/dependency
mutation、attestation mutation、further source mutation、training、product claim、
physical-grasp claim、T-ROOT 95 claim は Tier-A-required または別 scope required
かつ未承認。

| スキル | 初期配置 | 構築方法 |
|--------|---------|---------|
| ApproachCable | cable on table, fingers open | P0 scripted (既存cache) |
| Clamp | cable at approach pos, fingers open | ApproachCable成功状態 → VBD settle → cache |
| InsertIntoClip | cable between closed fingers, LIFT_Z | finger間配置 → close → VBD settle → cache |
| AerialRegrasp | 左arm cable保持, 右arm open | 左finger間配置 → close → settle → cache |
| Unclamp | cable in groove, L=HALF_OPEN, R=OPEN | groove配置 → PUSH_Z IK → VBD settle → cache |

### 4.0 GripEnv: Clamp / Unclamp (2026-04-06 D2改訂)

> **改訂履歴:** 旧設計 (obs 22D / action 4D / 左arm only) → GripEnv統合 (obs 42D / action 14D / 両arm) → **D2: Clamp 12D auto-close + Unclamp scripted化**。
> 旧 newton_unclamp_env.py / train_unclamp.py は廃止。

**env:** `newton_grip_env.py` (NewtonGripEnv) / **train:** `train_grip.py --mode clamp`

**Clamp (RL, 12D action + auto-close):**
- obs: 統一 42D (Section 4 obs表参照。AC/IC/AR と完全互換)
- action: 12D (EE delta のみ、他RLスキルと統一)
- finger: pos+ori閾値で自動close (FINGER_CLOSE_POS_THRESH=5mm, ORI_THRESH=~20deg)
- action damping: finger close後はarm delta を10%に減衰 (CLOSE_ACTION_DAMPING=0.1)

**Unclamp (scripted):**
- v4訓練完走後、finger開きのみでRL不要と判断 → scripted化決定 (2026-04-06)
- 実装: `scripted_skills.py` の `half_unclamp_release()` (既存)。L→HALF_OPEN(6mm) + R→OPEN(40mm)
- orchestrator の `is_scripted(RoutingPhase.UNCLAMP)` = True

#### mode=clamp

**前提条件:** ApproachCable完了後。両腕がcable位置に到達、finger OPEN。
**目的:** 両腕でcableを同時クランプ。位置微調整 + finger close タイミングの学習。

**報酬: 乗算結合 (grip_progress × clamp_alignment)**

```
score_grip_r = exp(-finger_r / CLAMP_RANGE_GRIP)   # CLAMP_RANGE_GRIP=20mm
score_grip_l = exp(-finger_l / CLAMP_RANGE_GRIP)
score_grip = 0.5 * (score_grip_r + score_grip_l)
score_clamp = 0.25 * (score_pos_r + score_ori_r + score_pos_l + score_ori_l)
progress = 0.2*grip + 0.2*clamp + 0.6*grip*clamp
R = 2.0 * (progress - 1.0) + R_step(5.0) + R_task(20.0) + R_penalty(-0.01)
```

**成功条件:** `clamp(L, L_n) ∧ clamp(R, R_n) ∧ sustained(K=5)` (EXP-094: K=10→P≈1e-7。K=5に緩和)
**terminal:** success | timeout(100) | cable_drop(z < TABLE-20mm) | explosion(dist>1m)

#### mode=unclamp

**前提条件:** IC完了 + 半アンクランプ（scripted）後。cable groove着座、L=HALF_OPEN(0.006)、R=OPEN(0.04)。
**目的:** cable groove着座を維持しながらL finger全開。

**報酬: 乗算結合 (finger_progress × cable_seated)**

```
score_finger = clamp((opening - HALF_OPEN_SUM) / (FULL_OPEN_SUM - HALF_OPEN_SUM), 0, 1)
score_seated = 0.5 * exp(-dist_pos / 5mm) + 0.5 * exp(-dist_ori / 0.5rad)
progress = 0.3*finger + 0.3*seated + 0.4*finger*seated
R = 2.0 * (progress - 1.0) + R_step(5.0) + R_task(20.0) + R_penalty(-0.01) + R_drop(-5.0)
```

**成功条件:** `finger_open(L) ∧ seated(groove_n, clip_n) ∧ sustained(K=5)`
- finger_open: finger_opening >= 0.074 (OPEN_SUM - 6mm tolerance)
- seated: dist_pos < T_GROOVE(3mm) ∧ cos_sim > T_SEAT(0.85) ∧ bodies_in_groove >= 2

**terminal:** success | timeout(100) | cable_drop(z < TABLE-20mm) | explosion(dist>1m)

### 4.1 ApproachCable (approach-only)

**obs:** 統一 42D (Section 4 obs表参照)
**action:** 14D MSA統一 (12D EE。action[12:13] finger はゼロマスク)
**フィンガ:** action外。常にOPEN維持。finger close は次スキル (Clamp) の責務
**報酬:** 統一 pose_match ベース (R_pos + R_ori + R_step + R_task + R_penalty)

**成功条件:** `approach(L, L_n) ∧ approach(R, R_n) ∧ sustained(K=5)` (成功条件定義 v3, §4 L622 参照)

> approach-only (2026-04-03 Session 83 変更)。finger_opening は判定しない。

**報酬ターゲット:** cable target seg (obs[16:22])。両手がtarget segに接近+姿勢合致で報酬増加


### 4.2 InsertIntoClip

### 4.2 InsertIntoClip

**obs:** 統一 42D
**action:** 統一 12D
**フィンガ:** STEPテーブル auto-control
**報酬:** 統一 pose_match ベース。ターゲット: clip位置+姿勢 (obs[23:29])
**Episode:** 200 steps

**成功条件:** `seated(groove_n, clip_n) ∧ sustained(K=10)` (成功条件定義 v3 参照)

**スキル固有:**
- 報酬ターゲットがclip (obs[23:29])。ケーブルseg姿勢がclip姿勢に一致することが目標
- R_drop = -5.0 (cable落下検出: `min(body[k].z) < TABLE_HEIGHT + 0.02`)


### 4.3 AerialRegrasp (approach-only)

**obs:** 統一 42D (Section 4 obs表参照)
**action:** 14D MSA統一 (12D EE。action[12:13] finger はゼロマスク)
**フィンガ:** action外。左arm=CLOSED固定、右arm=OPEN→auto-close (pose_match達成時)。finger close タイミングは次スキル (Clamp) の責務
**報酬:** 統一 pose_match ベース。ターゲット: cable target seg (obs[16:22])
**Episode:** 200 steps

**成功条件 (canonical, locked 2026-05-12):** `clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)`

> ⚠️ **STALE / SUPERSEDED 2026-05-12** per Rs代行 disposition `T_ROOT_COORD_V6_FINAL_VERDICT_PASS_BEHAVIORAL_SIGNAL_NEGATIVE_DELTA_20260512_0830 root` Decision C step 4 (P0.2 sync). Historical wording `approach(L, L_n) ∧ approach(R, R_n) ∧ cable_not_dropped ∧ sustained(K=5)` (Session 83, 2026-04-03) does NOT match the current standing verdict and is NOT used in V5/V6 evaluation. Phase 4 #2 V6 (2026-05-12) confirmed the locked criterion through 30720 completions with canonical_k_parity_pass=true on both arms. See §4.3 AerialRegrasp (above, line ~642) for the full SUPERSEDED block context.

`cable_not_dropped = min(body[k].z for all k) > TABLE_HEIGHT + 0.02`

**スキル固有:**
- ApproachCable と構造同一。差分は `cable_not_dropped`（空中操作の落下検知）と Z-clamp (LIFT_Z±0.05m)
- R_drop = -5.0 (cable落下検出)


## 5. 訓練パイプライン (DAPG)

### 5.1 概要

IL+RL → pure RL への段階的移行。

```
L = (1-alpha) * L_ppo + alpha * L_bc

alpha: 0.7 -> 0.5 (linear annealing over 200 iterations, α_min=0.5 BC維持)
```

- `L_bc = MSE(pi(s_demo), a_demo)` (Demo data direct, DAPG原論文準拠)
- demo = scripted IK 固定軌道。質は低い。clip方向への初期 guidance のみ
- BC pretrain不要: DAPGのL_bcがdemos.npzを直接参照するため、重み事前学習は冗長

### 5.2 alpha スケジュール

```python
ALPHA_INIT = 0.7          # S118 7体レビューで確定。α_min=0.5以上必須
ALPHA_MIN = 0.5           # BC維持方針 (sparse reward manipulation環境)
ALPHA_ANNEAL_ITERS = 200
ALPHA_SCHEDULE = "linear"  # 推奨

def get_alpha(iteration):
    t = min(1.0, iteration / ALPHA_ANNEAL_ITERS)
    return ALPHA_INIT + t * (ALPHA_MIN - ALPHA_INIT)
```

ログ: 各iterationで alpha, L_ppo, L_bc, L_total を記録。alpha=α_min(0.5) 到達後も L_bc を計算(乖離度モニタ)。

### 5.3 BC loss 統合方式

RSL-RL の OnPolicyRunner を改造せず、PPO更新の後に BC loss を1回適用。

```python
demo_data = np.load(args.demos)
demo_obs = torch.tensor(demo_data["obs"], device=device)
demo_act = torch.tensor(demo_data["actions"], device=device)

# BC uses PPO optimizer (unified Adam momentum — rs承認済み設計選択)
for iteration in range(max_iterations):
    # 1. Standard PPO update (RSL-RL)
    runner.learn(num_learning_iterations=1, init_at_random_ep_len=False)
    # 2. BC auxiliary update
    alpha = get_alpha(iteration)  # 0.7 -> 0.5 linear
    if alpha > 0:
        idx = torch.randint(0, len(demo_obs), (bc_batch_size,))
        pred = runner.alg.policy.actor(demo_obs[idx])
        loss_bc = F.mse_loss(pred, demo_act[idx])
        runner.alg.optimizer.zero_grad()
        (alpha * loss_bc).backward()
        runner.alg.optimizer.step()
```

### 5.4 Finger action (全スキル共通)

```python
FINGER_STEP_SIZE = 0.001  # 1mm per RL step
# finger_cmd in [-1, 1]: -1=open, 0=hold, +1=close
new_pos = current_pos + finger_cmd * FINGER_STEP_SIZE
new_pos = clip(new_pos, FINGER_CLOSE_POS, FINGER_OPEN_POS)
```

---

## 6. Demo Collection Pipeline

### 6.1 原則

**wet-run は dry-run が出した waypoints をそのまま追従する。独自に位置計算しない。**

```
dry-run (IK検証)
  -> clip配置 + groove angles -> waypoints計算
  -> IK到達性 + collision clearance 検証
  -> guide手選択 (L/R) 確定
  -> verified_waypoints.json

wet-run (物理実行)
  -> verified_waypoints.json 読み込み
  -> IK -> joint target -> physics stepping
  -> (obs, action) pairs -> demos.npz
```

### 6.2 verified_waypoints.json フォーマット

```json
{
  "version": 2,
  "layout": {
    "clip_positions": [[0.35, 0.15], [0.40, 0.075], [0.35, 0.0], [0.40, -0.075], [0.35, -0.15]],
    "groove_angles_rad": [0.0, ...],
    "grip_offset_m": 0.055
  },
  "steps": [
    {
      "step": 1,
      "desc": "Home",
      "target_l": [x, y, z],
      "target_r": [x, y, z],
      "guide_hand": null,
      "status": "PASS",
      "err_l_mm": 0.1,
      "err_r_mm": 0.2,
      "clearance_mm": 85.0
    }
  ],
  "summary": { "total": 43, "pass": 43, "warn": 0, "fail": 0 }
}
```

### 6.3 既知の divergence (v1 修正対象)


| 項目 | dry-run | wet-run (現行) | 問題 | 状態 |
|------|---------|----------------|------|------|
| grip 配置 | groove angle基準 +/-55mm | routing direction +/-60mm | 座標ズレ | 未解消 |
| ~~再把持X位置~~ | ~~CABLE_X=0.3 固定~~ | ~~nearest cable body query~~ | ~~物理依存~~ | **解消 (v2)**: R-hand X = L-hand X |
| 再把持Y位置 | prev->next 中点 固定 | nearest cable body query | 物理依存 | 未解消（Y軸のみ残存） |
| guide手選択 | L/R テスト->良い方 | 常にleft固定 | 不一致 | 未解消 |

修正: wet-run は dry-run JSON を読んで追従。独自計算しない。

> **v2 変更点 (2026-03-28):** 39→43ステップ。再クランプ前にL固定ステップ挿入×4。
> R-hand X をケーブル原点(0.3)からL-hand X に修正。`full_43step.json` が現行SSOT。
> dry-run: `dry_run_43step.py`、IK 43/43 PASS (max 0.71mm)。

> **v3 変更点 (2026-03-28 セッション28):**
> - Phase A grasp位置: X=0.30→0.15 (REST_CLIPS一致)、Z=1.12→1.05 (IK到達性)
> - routing上昇Z: 1.12→1.07 (クリップ-フィンガ間隔半減)
> - REST_CLIPS: X=0.15 (routing clips X=0.35 から20cm離間)
> - URDF visual mesh: finger.dae復元 (Newton ViewerGL互換)
> - Cartesian補間: `solve_ik_dual` 戻り値 `jq` を直接使用 (旧: `fk_state.joint_q` 未更新バグ修正)
> - IK 43/43 PASS (max 0.71mm)、6カメラ動画生成
> - 動画: `~/Downloads/dryrun_43step_{overhead,front,diag_upper,left,right,clip_close}.mp4`

> **⚠訂正注記 (2026-07-11、Rs 承認 D-1):** 上記 v3 の「Phase A grasp X: 0.30 → 0.15」は後日 revert 済みで現行 = **X=0.30**(full_43step.json STEP 2-5 + task_config.py:231 GRASP_X=0.30 と一致)。Z=1.05 は反映済で有効。裁定記録 = `eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md` §2 D-1。

> **v4 変更点 (2026-03-28 セッション31): Y座標統一**
> - task_config.py CLIP_POSITIONS Yフリップ: C1=y-0.15→y+0.15 (JSON SSOT に合わせる)
> - CLIP1_X/CLIP1_Y/CLIP1_Z を task_config.py に導出定数として追加
> - WIDE_LEFT_Y/WIDE_RIGHT_Y 自動更新: -0.21/-0.09 → +0.09/+0.21
> - 6ファイルのハードコード CLIP1_Y=-0.05 → `from task_config import` に統一
> - newton_grasp_and_insert_env.py: import元を test_newton_clip_routing → task_config に変更
> - Routing方向確定: C1(y=+0.15, 右ロボ側) → C5(y=-0.15, 左ロボ側)



### 6.4 ApproachCable demo (新規収集)

現行 demo (102,400 transitions) は P3 後のデータ → ApproachCable には使えない。

```python
# approach_cable_demos.npz — matches NewtonApproachCableEnv obs/action space
{
    "obs": np.array([N, 11], dtype=float32),   # 11D obs (env format, scaled)
    "actions": np.array([N, 6], dtype=float32), # 6D: R_EE_dxyz(3) + R_finger(1) + L_EE_dxy(2)
}
```

### 6.5 DR-varied layout でのdemo収集

```
for each DR layout (clip position +/-Xmm):
  1. dry-run: layout -> verified_waypoints_{id}.json
     FAIL step あればスキップ
  2. wet-run: waypoints -> Newton VBD replay -> demos_{id}.npz
  3. aggregate: 全layout結合 -> demos.npz
```

v1 (InsertIntoClip, single clip): DR は env 内 target offset のみ。demo は固定 clip 位置で十分。

---

## 7. Domain Randomization

### 7.1 設計原則

1. obs は clip-relative 座標 → policy が clip 位置に自動適応
2. visual clip と target clip を分離 → visual固定, target のみ randomize
3. P3 precondition cache は固定 → DR は target offset として適用

### 7.2 パラメータ

```python
DR_CLIP_XY_RANGE = 0.005       # +/-5mm
DR_CLIP_Z_RANGE = 0.0          # v1: Z固定
DR_CLIP_ORIENT_RANGE = 0.0     # v1: 回転なし
DR_CABLE_INIT_OFFSET = 0.003   # +/-3mm
DR_GRASP_OFFSET = 0.003        # +/-3mm
DR_ENABLED = False              # テスト時False, 訓練時True
```

### 7.3 段階的拡大

| Phase | DR_CLIP_XY | DR_CLIP_ORIENT | DR_CABLE | 目的 |
|-------|-----------|----------------|----------|------|
| v1 | +/-5mm | 0 | 0 | 基本位置適応 |
| v2 | +/-10mm | +/-5deg | +/-3mm | 中程度 |
| v3 | +/-15mm | +/-10deg | +/-5mm | 本番想定 |

---

## 8. 検証計画

### Phase 1: DAPG 動作確認 (alpha固定)

```bash
python train_dapg.py --world-count 256 --max-iterations 10 \
    --alpha-init 0.7 --alpha-anneal-iters 99999 \
    --demos thread_isaac_lab/data/bc_demos/insert_clip_demos.npz \
    --device cuda:0
```

成功基準: reward > from-scratch RL の iter 10 時点

### Phase 2: alpha annealing

```bash
python train_dapg.py --world-count 512 --max-iterations 300 \
    --alpha-init 0.7 --alpha-min 0.5 --alpha-anneal-iters 200 \
    --device cuda:0
```

成功基準: success > 0%, alpha=0.5 到達後も reward 維持

### Phase 3: DR 有効化

```bash
python train_dapg.py --world-count 512 --max-iterations 300 \
    --alpha-init 0.7 --alpha-min 0.5 --alpha-anneal-iters 200 \
    --dr-clip-xy 0.005 --device cuda:0
```

成功基準: DR有効で success > 0%

### Phase 4: Pure RL baseline comparison

```bash
python train_dapg.py --world-count 512 --max-iterations 300 \
    --alpha-init 0.0 --dr-clip-xy 0.005 --device cuda:0
```

Phase 3 との差を定量化。

---

## 9. 並列実験: A (独立スキル) vs B (統合スキル)

### A: ApproachCable 独立

| 項目 | 設計 |
|------|------|
| env | NewtonApproachCableEnv |
| precondition | cable on table + arm at APPROACH_Z |
| obs (8D) | EE(3) + cable(3) + finger_opening(1) + cable-finger dist(1) |
| action (4D) | EE delta(3) + finger delta(1) |
| terminal | cable lifted to LIFT_Z (成功) / 200 steps |
| chain | ApproachCable RL -> scripted transport -> InsertIntoClip RL |

### B: Grasp+Insert 統合

| 項目 | 設計 |
|------|------|
| env | NewtonGraspAndInsertEnv |
| obs (12D) | EE(3) + cable(3) + finger(1) + clip(2) + cable-clip dist(1) + cable-finger dist(1) + Z gap(1) |
| action (4D) | EE delta(3) + finger delta(1) |
| terminal | bodies in groove >= 2 (成功) / 400 steps |
| reward | phase-aware: approach -> grasp -> transport -> insert |

### 判断基準

| 結果 | 判断 |
|------|------|
| A成功 + B失敗 | スキル分割路線 |
| B成功 + A成功 | B優先 (遷移不要) |
| 両方失敗 | reward/obs見直し, curriculum追加 |
| A失敗 + B成功 | B採用 |

---

## 10. Failure Recovery / Reverse Curriculum (v2以降)

### Failure Recovery (v2)

```python
# 1% chance per step で cable perturbation
if dr_enabled and random() < 0.01:
    # non-grasped cable bodies に微小変位
```

v1 では実装しない。

### Reverse Curriculum (alpha=α_min 到達後)

```python
CURRICULUM_STAGES = [
    {"init_offset_mm": 5,   "advance_threshold": 0.3},
    {"init_offset_mm": 15,  "advance_threshold": 0.3},
    {"init_offset_mm": 30,  "advance_threshold": 0.3},
    {"init_offset_mm": 50,  "advance_threshold": 0.2},
]
```

v1 のスコープ外。

---

## 11. 制約・注意事項

1. **demo obs整合:** 固定 clip 位置で収集。DR > 10mm で BC loss 有効性低下の可能性
2. **RSL-RL互換:** learn() の外で BC loss 適用。内部改造なし
3. **cache invalidation:** DR は target position のみ。clip offset > 15mm で初期状態が unrealistic に
4. **GPU メモリ:** demo tensor ~6MB。無視可能
5. **CLAUDE.md遵守:** DiffIK維持。write_joint_position_to_sim 不使用

---

## 12. ファイル構成

```
thread_isaac_lab/
  models/
    __init__.py                            # SkillAdapter, SkillType等 export
    skill_adapter.py                       # MSA: LoRA + MLP + gate adapter (42D/12D)
  envs/
    newton_approach_cable_env.py              # ApproachCable (v5 12D action)
    newton_insert_clip_env.py              # InsertIntoClip (v5 12D action)
    newton_aerial_regrasp_env.py           # AerialRegrasp (v5 12D action)
    newton_skill_env_base.py               # 共通基盤 (scene, IK, physics, cache)
  scripts/
    train_approach_cable.py                   # ApproachCable訓練 (--base-model でskill adapter)
    train_insert_clip.py                   # InsertIntoClip訓練
    train_aerial_regrasp.py                # AerialRegrasp訓練
    test_motion_sequence_dry_run.py        # dry-run (--clip-x/y CLI追加)
    collect_demo_data.py                   # wet-run (--waypoints JSON読込)
  configs/
    task_config.py                         # DR パラメータ追加
  data/
    waypoints/
      insert_clip_c1.json                  # CLIP1 dry-run出力
    bc_demos/
      insert_clip_demos.npz               # InsertIntoClip demo
      approach_cable_demos.npz               # ApproachCable demo
```

---

## 13. 並行訓練計画

| GPU | スキル | world count | 備考 |
|-----|--------|-------------|------|
| cuda:0 | ApproachCable (v8) | 1024 | 乗算結合報酬 |
| cuda:1 | InsertIntoClip or AerialRegrasp | 256-512 | 新規env |

実装順序:
1. ApproachCable v8: 報酬関数を乗算結合に変更 (最小差分)
2. InsertIntoClip env: 新規 + 合成初期状態
3. AerialRegrasp env: ApproachCable と構造が近い

---

## 14. Orchestrator 設計 (2026-04-05)

### 14.1 概要

43 STEP cable routing を RL policy + scripted waypoint で実行するオーケストレータ。
各STEP開始前に物理状態をsnapshot し、失敗時は直近STEP先頭から復旧する。

**前提:** G1-v5b, G2, G3, G-Grip 全PASS。Phase 5 (Step 5-2以降) で実装。

### 14.2 アーキテクチャ

```
RoutingOrchestrator
├── STEP_TABLE[43]       # §2.3 マッピング (step_id, skill, type, params)
├── snapshots[43]        # per-STEP物理状態
├── policy               # MultiSkillActorCritic (RL実行)
├── scripted_executor    # IK waypoint / finger指令 (scripted実行)
├── clip_status[5]       # C1-C5 固定状態
└── recovery_engine      # Retry → Rollback → Abort
```

### 14.3 State Snapshot

既存 `save_precondition_cache` (newton_skill_env_base.py) と同じデータ構造を流用。

```python
snapshot = {
    "body_q":       state_0.body_q.numpy().copy(),     # cable+robot全body位置姿勢
    "body_qd":      state_0.body_qd.numpy().copy(),    # 速度
    "fk_jq":        fk_state.joint_q.numpy().copy(),   # 関節角度 (FK状態)
    "clip_status":  clip_status.copy(),                 # C1-C5固定状態
    "finger_state": (l_finger_pos, r_finger_pos),       # finger opening
    "ik_target":    (l_ik_target, r_ik_target),          # 現在のIKターゲット
}
```

**メモリ:** cable 40body×13float + robot 2×(11body×13float) + joint 2×9 ≈ 4KB/world。
43 STEP × 256 world ≈ **44 MB**。GPU/CPUメモリに対して無視可能。

**保存タイミング:** 各STEP `_execute_skill()` 呼び出し直前。
**復元:** `body_q.assign()` + `body_qd.assign()` + `joint_q.assign()` (既存API)。

### 14.4 スキル実行インターフェース

```python
class SkillResult(Enum):
    SUCCESS = "success"         # 成功条件達成
    TIMEOUT = "timeout"         # episode step上限
    FAIL = "fail"               # 成功条件未達 (cable維持)
    CABLE_DROP = "cable_drop"   # cable落下
    EXPLOSION = "explosion"     # VBD発散 (dist > 1m)

def execute_skill(self, step_id, skill, stype, params) -> SkillResult:
    if stype == "RL":
        self.policy.set_skill(SKILL_TO_TYPE[skill])
        return self._run_rl_episode(params)
    elif stype == "S":
        return self._run_scripted(skill, params)
    elif stype == "W":
        return self._run_wait(skill, params)
```

**RL実行:** `policy.act(obs)` → env.step() を episode 終了まで繰り返す。
env の terminal 条件 (success/timeout/cable_drop/explosion) が SkillResult にマップ。

**Scripted実行:** IK waypoint移動 or finger指令。IK収束確認 (pos_error < 2mm) で SUCCESS。
IK発散 (100step未収束) は FAIL を返す。

**Wait実行:** ClipConfirm。cable segment が groove 内に残っているか N step 確認。

### 14.5 復旧エンジン

#### 失敗モード → 復旧戦略マッピング

| SkillResult | 初手 | cable状態 |
|-------------|------|-----------|
| TIMEOUT | Retry (同STEP) | 維持 |
| FAIL | Retry (同STEP) | 維持 |
| CABLE_DROP | Rollback (直前STEP) | 喪失 |
| EXPLOSION | Abort | 破壊 |

#### 復旧フロー

```
execute_skill(step_id)
  │
  ├─ SUCCESS → 次STEPへ
  │
  ├─ TIMEOUT / FAIL (cable維持) ─┐
  │                               ├→ Retry (同STEP先頭, max 3回)
  │                               │   └─ 全Retry失敗 → Rollback
  │
  ├─ CABLE_DROP ─────────────────→ Rollback (直前STEP先頭)
  │
  └─ EXPLOSION ──────────────────→ Abort (即時)

Rollback:
  restore(snapshots[step_id - 1])  # 直前STEP先頭
  re-execute from step_id - 1
    ├─ SUCCESS → step_id を再実行
    ├─ FAIL → restore(snapshots[step_id - 2])  # さらに1つ前
    │           ... (max depth 3)
    └─ depth超過 → Abort
```

#### パラメータ

| パラメータ | 値 | 根拠 |
|-----------|-----|------|
| MAX_RETRY | 3 | RL stochasticity で復旧可能な回数 |
| MAX_ROLLBACK_DEPTH | 3 | clip単位の巻き戻し上限 (8 STEP/clip × 3 = 24 STEP) |
| ROLLBACK_UNIT | 1 STEP | 直近動作手前から再開 (save point制限なし) |

#### Rollback の制約

- **clip固定は不可逆と仮定:** C1が固定済みの状態でC2に失敗→C1固定直後 (STEP 10) まで戻せるが、C1固定前 (STEP 6) には戻さない。clipの物理的取り外しは未対応。
- **Rollback先が scripted STEP の場合:** scripted は決定的なので同結果が期待できる。問題がRLスキルにある場合、rollbackしてscripted→RL再実行で復旧を試みる。
- **Abort後のepisode統計:** abort_step, abort_reason, retry_count, rollback_depth を記録。

### 14.6 action_dim 統合 — **解消済み (D2, 2026-04-06)**

> **旧問題:** GripEnv (Clamp/Unclamp) = 14D, 他 = 12D → MSA統一に14Dゼロマスクが必要だった。
>
> **D2解決:** Clamp → 12D + auto-close。Unclamp → scripted。全RLスキルが12D統一。
> `SkillAdapterConfig.action_dim = 12` で統一。ゼロマスク不要。

### 14.7 SkillType 整理

```python
class SkillType(Enum):
    APPROACH_CABLE = "approach_cable"
    CLAMP = "clamp"
    INSERT_INTO_CLIP = "insert_into_clip"
    UNCLAMP = "unclamp"
    AERIAL_REGRASP = "aerial_regrasp"
    # 削除: TRANSPORT_TO_CLIP (scripted — SkillType不要)
    # 削除: GRIP (CLAMP/UNCLAMPで代替)
```

Scripted スキル (TransportToClip, ReClamp, HalfUnclampRelease, ClipConfirm) は
SkillType enum に含めない。オーケストレータが直接実行。

### 14.8 実装ファイル

```
thread_isaac_lab/
  skills/
    __init__.py                # exports
    scripted_skills.py         # TransportToClip, ReClamp, HalfUnclampRelease, ClipConfirm
    step_table.py              # STEP_TABLE 定義 (§2.3 から生成, 43 StepDef)
    snapshot.py                # state snapshot 保存/復元 (SnapshotManager)
    routing_orchestrator.py    # RoutingOrchestrator 本体 (TODO: Phase 5)
```

---

## 15. Phase 5-2 1-clip E2E (2026-04-25 追記)

> **⚠ STALE-SUBSTRATE BANNER (2026-06-21): §15's target architecture (X1 = `routing_orchestrator` + Newton multi-skill env wrapper, Featherstone+VBD / env6 `:3122`; Franka-era `REST_CLIP_X=0.15` coords; X3 = `test_newton_clip_routing.py` ABANDONED) PREDATES the R2 Option-E substrate swap.** The current R-S7.1 substrate = **env7 Newton 1.2.1 / mujoco SolverMuJoCo, UR5e×2 + 2F-85** (`04-Specs/RS71-System-Spec-SSOT.md:15`, `SOMA.md`), and active R-S7.1 work RUNS on `test_newton_clip_routing.py` (mujoco backend). → §15 = the **env6-VBD RL design**, NOT the current substrate; porting the X1 PATTERN onto env7 is an OPEN L3 (env7-RL-substrate). RL itself = **NO-GO / premature** (pre-RL-readiness plan, 4 prereq tracks). Do NOT treat §15 as the live RL-env spec without the env7 port.

> 5-CC Debate (2026-04-25、rs A 承認) で確定。当初 PROPOSE (Path X3 + Z2 mid-checkpoint + 本 session smoke) は CRITICAL 5 + HIGH 9 で BLOCKed、本 §15 は NHA revised scope。Phase 5-1b 14/14 CRIT COMPLETE を前提に、Phase 5-2 1-clip E2E wet-run の設計仕様を定める。

### 15.1 Goal & scope

- **Goal**: §14 orchestrator (Phase 5-1b 完成、`routing_orchestrator.py` 812 LoC、86/86 unit tests PASS) を Newton 実機で 1-clip routing wet-run、Gate G5 (success ≥50%) 達成
- **Scope**: STEP 1-10 (Phase A STEP 1-5 + Phase B STEP 6-10 = 1-clip)
  - Phase A: Home → cable_above (REST_CLIPS) → AC RL → CLAMP RL → lift
  - Phase B: Transport C1 → IC RL → HALF_UNCLAMP → CLIP_CONFIRM → C1 上昇
- **Out of scope**: STEP 11-42 (C2-C5 routing は Phase 5-3/5-4)、cable lift regression fix (`12-Cable-Lift-Regression/` 別 task 既起票)

### 15.2 Architecture path 比較 (CC5 CRIT 1-3 解消)

| Path | 内容 | 判定 |
|------|------|------|
| X3: test_newton_clip_routing.py reuse | P1-P4 scripted + AC RL replace | **ABANDONED** (座標系 mismatch X 150mm/Z 70mm、kinematic FK vs dynamic-joint architecture mismatch、prohibited.md kinematic-trick 違反 risk) |
| **X1: full integration** | `routing_orchestrator` + Newton multi-skill env wrapper | **採用** (推奨 target architecture) |
| X2: env-switching | STEP ごと env 切替 + snapshot state transfer | X1 simplified subset、Sub-B 初期 iteration 候補 |

### 15.3 Coordinate system reconciliation (CC5 CRIT 1 fix)

43-STEP **REST_CLIP_X=0.15 schema** 採用 (`task_config.py` SSOT):

| STEP | target_left / target_right | SSOT reference |
|------|---------------------------|----------------|
| STEP 2/5 cable_above/lift | `(REST_CLIP_X, WIDE_LEFT_Y, REST_RISE_Z)` / `(REST_CLIP_X, WIDE_RIGHT_Y, REST_RISE_Z)` | `task_config.py:106` REST_CLIP_X=0.15, WIDE_LEFT_Y/WIDE_RIGHT_Y, `scripted_skills.py:54` REST_RISE_Z=1.05 |
| STEP 6/10 C1 above | `(CLIP1_X, ±GRIP_HALF_SPAN, ROUTING_RISE_Z)` | `task_config.py` CLIP_POSITIONS[0], ROUTING_RISE_Z=1.07 |

AC RL env precondition: cable 位置 = REST_CLIPS S1/S2/S3 (X=0.15)。test_newton_clip_routing.py GRASP_X=0.30 / APPROACH_Z=1.12 は X3 ABANDON で不使用。

### 15.4 Architecture compatibility (CC5 CRIT 2-3 fix)

**dynamic-joint Featherstone+VBD architecture 採用** (kinematic FK 不採用):

- Newton envs (`newton_*_env.py`) = `VecEnv` + dynamic joint、AC RL training time architecture と一致
- State handoff: `body_q.assign() + body_qd.assign()` + Phase 5-1b Cluster B `body_q_prev.assign(snap.body_q)` VBD velocity spike 防止
- prohibited.md kinematic-trick 禁止整合 (`test_newton_clip_routing.py:1527-1559` kinematic FK joint_q assignment は **採用しない**)

**2026-05-23 R2-A Track A consistency note:** この節の dynamic-joint target
architecture は保持する。Track A は source-level default-off mechanism support
として `release_after_success_hold_k` を検証し、Phase4 schema-v2 で
`MECHANISM_GO_RELEASE_GATE_V2 / PRODUCT_GO_FALSE`、C5A/C5B で
`C5A_GUARD_REVIEW / C5B_TRIAGE_COMPLETE`、C6A/C6B で timeout-recovery
design/scaffold/eval path COMPLETE、さらに C6B smoke で
`C6B_TIMEOUT_RECOVERY_REVIEW_OR_NO_GO`、C6C で
`C6C_POSTHOC_TRIAGE_COMPLETE`、C6D/C6E で
eval-path telemetry contract design/scaffold COMPLETE、C6F で
contract-results review COMPLETE、C6G で telemetry auth package COMPLETE、
C6H で telemetry runner scaffold COMPLETE、C6I で scaffold review COMPLETE、
C6J で telemetry GPU-auth draft review COMPLETE、C6K で live telemetry runner
scaffold COMPLETE、C6L で telemetry GPU-auth package review COMPLETE、C6M で
live telemetry GPU smoke COMPLETE、C6N で C6M posthoc review COMPLETE、C6O で
timeout-recovery no-go closeout COMPLETE、C7 で new timeout-recovery variable
design COMPLETE、C7A で early strict-ready capture scaffold COMPLETE、C7B で
early strict-ready capture scaffold review COMPLETE、C7C で early strict-ready
capture launch-capable runner implementation COMPLETE、C7D で C7C runner
review / GPU-auth package review COMPLETE、C7E で eval-path completion COMPLETE
、C7F で C7E review / GPU-auth package review COMPLETE、C7F post-review
launch-path sanity correction COMPLETE、C7H で launch-path 0GPU implementation
COMPLETE、C7I で C7H review / GPU-auth package review COMPLETE、さらに C7J で
bounded GPU smoke COMPLETE、C7K で C7J posthoc review COMPLETE、C7L で
objective/policy redesign COMPLETE、C7M で objective/policy package review
COMPLETE、C7N で payload completion package COMPLETE、C7O で payload runner
scaffold COMPLETE、C7P で payload collection auth package review COMPLETE、
C7Q で payload collection runner implementation COMPLETE、C7R で payload
collection auth package review COMPLETE、C7S で collect-path completion COMPLETE、
C7T で payload collection auth package review COMPLETE、C7U で payload collection
launch decision REVIEW-HOLD、C7V で real payload-writing path 0GPU COMPLETE、C7W
で payload collection auth package review COMPLETE、C7X で real
collector-to-writer integration COMPLETE、C7Y で payload collection auth package
review COMPLETE、C7Z で launch-capable collector-writer runner COMPLETE、C8A で
payload collection auth package review COMPLETE、C8B で guarded writer invocation
path COMPLETE、C8C で payload collection auth package review COMPLETE、C8D で
real C7V writer output path COMPLETE、C8E で payload collection auth package
review COMPLETE、C8F で launch-capable real C7V writer output path COMPLETE、C8G
で payload collection auth package review COMPLETE、C8H で executable
collect-writer output path COMPLETE、C8I で payload collection auth package review
COMPLETE / artifact consistency patch COMPLETE、C8J で boundary-only no-payload-output
review-hold、C8K で output-path binding review COMPLETE、C8L で payload output
writer completion path COMPLETE、C8M で payload output writer completion auth
review COMPLETE、C8N で payload-output completion run COMPLETE となった。
これは物理把持や production readiness の承認ではないため、
`physical_grasp_claim=false` と `PRODUCT_GO=false` を維持する。次の product
gap は C5A active timeout debt のままであり、C6H は historical C6B の
contract-fail を explicit にし、C6I は GPU auth ready ではないと判定した。
C6J は C6H が launch-capable live telemetry eval runner ではないため
executable GPU auth を blocked と判定した。C6K は C6E/C6H/C6K telemetry schema
coverage と unauthorized eval refusal を実装・検証した。C6L は future C6M draft
を作成し、C6M は live branch/horizon telemetry を実行確認したが terminal outcome
を変えなかった。C6N は no-go as run を支持し、C6O は C6B/C6M
timeout-recovery family を no-go as run として closeout した。C7 は
`early_strict_ready_capture_controller` を primary non-repeat variable として選定し、
C7A は 0GPU scaffold/auth package を実装し、check/dry-run/refusal を PASS した。
C7B は C7A scaffold を future C7C 0GPU launch-capable runner implementation
に十分と review したが、GPU auth ではない。C7C は 0GPU runner package を
実装し、py_compile/check/dry-run/refusal/JSON を PASS、future eval guard を
保持した。C7D は C7C runner を review し、valid-marker path が concrete eval
implementation へ移らないため `C7D_REDESIGN_REQUIRED_BEFORE_GPU_AUTH` とした。
C7E は copy-derived runner/package を実装し、valid-marker `auth-dry-run` が
`EVAL_TRANSFER_READY` を出すことを 0GPU で確認した。C7F は future C7G GPU
smoke を draft-only で packageable と initially review したが、C7F correction
で C7G draft marker prefix mismatch と C7E valid-marker eval refusal を確認し、
その GPU auth draft は executable ではないと retracted/qualified した。C7H は
0GPU launch-path implementation を完了し、future marker prefix alignment、
invalid-marker refusal before heavy imports/simulator/CUDA/output writes、
valid-marker auth-dry-run `CONCRETE_FUTURE_EVAL_BOUNDARY_READY` を確認した。
C7I は C7H を review し、future GPU-smoke package を draft-only ready と判定した
が launch は承認していない。C7J は fresh explicit scoped directive により
cuda:0 で 246/246 completions、no abort で実行PASSしたが、C7H candidate は
control と terminal metrics が完全一致し、terminal-signature delta は 0 だった。
C7K は 0GPU posthoc review で early-capture null effect を確認した。C7L は
`strict_ready_dwell_objective_policy_redesign` を選定した。C7M は loss spec を
ready としたが C7 target-slice trainable payload は not ready と判定した。C7N は
42-row manifest と required payload schema を package 化した。C7O は runner scaffold
を 0GPU で実装し、check/dry-run/refusal を PASS した。C7P は direct collection
auth を blocked とし、C7Q 0GPU launch-capable runner implementation を推奨した。
C7Q は valid-marker auth-dry-run で payload collection boundary ready を確認した。
C7R は actual collect path が refusal-only のため collection launch draft を blocked
とした。C7S は valid-marker collect が `COLLECT_PATH_BOUNDARY_READY` へ到達する
ことを 0GPU で確認し、payload output は生成していない。C7T は future C7U launch
decision を `DRAFT_NOT_AUTHORIZED` として packageable と判定したが、launch/GPU/
collection は承認していない。C7U は boundary に到達したが payload outputs を
生成しなかったため review-hold とした。C7V は C7-local payload writer scaffold を
0GPU で実装し、future real records から required payload outputs を書く path を
定義した。C7W は artifact-only review で launch draft を blocked とし、
real collect-record integration into writer が必要と判定した。C7X は 0GPU
in-memory proof で exact writer boundary を確認し、output writes を suppress した。
C7Y は artifact-only review で単一 launch-capable collect-to-writer runner が
未作成と判定した。C7Z はその runner proof を 0GPU で完成させ、
`COLLECTOR_WRITER_LAUNCH_BOUNDARY_READY` へ到達した。C8A は C7Z を review し、
writer invocation が suppress されたままなので launch draft は未作成とした。
C8B は write-disabled recording writer/shim invocation を 0GPU で証明した。
C8C は real C7V file-writing path が未証明のため launch draft を blocked とした。
C8D は actual C7V writer method/file path を reached し、file writes を creation 前に
intercept した。C8E は launch draft を blocked とし、C8F launch-capable real writer
path 0GPU を要求した。C8F は future valid collect path を `FileWriteInterceptor`
なしで定義し、actual C7V writer signature binding、records-ready 後 writer
invocation plan、output-collision guard、invalid-marker refusal guard を確認したが、
writer invocation、collection launch、payload outputs 生成はしていない。次は C8G
payload collection auth package review 0GPU に進み、C8G は current C8F valid
`--mode collect` が dry-run/suppression-only で
`collection_launch_suppressed_by_c8f_0gpu_scope=true` のため launch draft を
blocked とした。C8H は valid `--mode collect` を
`EXECUTABLE_COLLECT_WRITER_OUTPUT_BOUNDARY_READY` に到達させたが、collection
launch と payload outputs は生成していない。C8I は C8H を artifact-only review
し、C8J launch-decision package を `DRAFT_NOT_AUTHORIZED` としてのみ draftable
と判定した。artifact consistency patch で C8J draft の stale previous-stage
output path は C8J results path に整合済み。次は C8J payload collection launch
decision fresh scoped directive only に進み、C8J は exit 0 で executable boundary
に到達したが required payload outputs を生成しなかった。C8K は missing transition
を C8H collect manifest-only / no C7V writer call / no C8J output-root binding と
特定した。C8L は C8J `boundary_outputs` を actual C7V writer path に bind し、
write suppression/interception の下で all five future output paths を確認したが、
real payload outputs は生成していない。C8M は C8L proof を review し、C8N draft
を `DRAFT_NOT_AUTHORIZED` として作成した。C8N は actual C7V writer path で five
authorized C8J result files を作成し、42 payload rows / 42 completion records を
validate した。C8O はそれらを artifact-only review し、five files、42-row counts、
22/22 required field coverage、target-slice row-key match、protected SHA locks、
forbidden-output absence を確認した。次は C8P payload dataset-consumption or
training-auth review 0GPU、broader productization/routing review、または HOLD。
C8P は payload semantics を review し、structural/provenance-ready only だが
dry-run/proxy-shaped values のため training-auth は blocked とした。C8Q は field
provenance audit で live per-step fields が存在しないことを確認した。次は C8R
live payload collection path design 0GPU draft-only。C8R は 0GPU design-only で
22 C7N fields を future live hooks / fail-closed validations に mapping し、次は
C8S live payload collection scaffold 0GPU draft-only とした。C8S は local scaffold
runner と proof artifacts を作成し、collection/output writes/GPU/training なしで
all 22 fields の fail-closed hook map と refusal behavior を検証した。次は C8T
live payload collection auth review 0GPU draft-only。C8T は C8S artifacts を検証し、
collection-auth ready now=false、C8U live payload collection path/auth package
0GPU draft-only next とした。C8U は no-output path boundary を定義し、C8V live
payload collection launch-or-review 0GPU draft-only next とした。C8V は review
branch のみを実行し、C8U artifact package と no-output boundary を検証した。
次は C8W launch-capable live collection runner path 0GPU draft-only。
C8W は eval_runs-local runner/path package を作成し、valid-marker auth-dry-run は
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
relay-side verification は PASS。C9BC は C9BB auth-dry-run function body に
`refresh_summary` call がなく、caller route manifest のみを書き、route output
が `c9bb_auth_dry_run_manifest.json` だけであり、required refusal proofs が
file creation 前に pass することを確認した。C9BC decision は
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

### 15.5 Per-STEP success criteria (CC3 CRIT C7 fix、§運用18 ground-truth pre-declare)

Smoke L-probe criteria (evaluation のみ、RL training success 条件変更ではない):

| STEP | skill | type | success criterion |
|------|-------|------|-------------------|
| 1 | TRANSPORT (Home) | S | both EE within 5mm of (0, ±0.10, HOME_Z) |
| 2 | TRANSPORT (cable_above) | S | both EE within 5mm of target + finger-cable dist < 10mm |
| 3 | AC RL | RL | `derive_skill_result(extras) == SUCCESS`、fingertip-cable dist < 5mm |
| 4 | CLAMP RL | RL | `derive_skill_result == SUCCESS`、finger closure < 4mm + finger-cable contacts ≥ 2/arm |
| 5 | TRANSPORT (lift) | S | EE at target + **cable_z_delta ≥ X mm** (Layer 4b blocker、暫定値は `12-Cable-Lift-Regression` 解決後に確定) |
| 6 | TRANSPORT (C1 above) | S | both EE within 5mm of C1 target |
| 7 | IC RL | RL | `derive_skill_result == SUCCESS`、cable_in_groove segments ≥ GROOVE_BODIES_MIN=2 |
| 8 | HALF_UNCLAMP | S | L finger 0.006、R finger 0.04 |
| 9 | CLIP_CONFIRM | W | groove segments ≥ 2 sustained N=20 steps |
| 10 | TRANSPORT (C1 上昇) | S | both EE within 5mm of target |

**Smoke aggregate pass (Gate G5 ≥50%)**: STEP 1-10 全 success 比率 ≥50% over N=10 episodes (cuda:2 w=1)

### 15.6 Failure modes & abort gate (CC4 fix)

| SkillResult | 対処 (既存 §14.5) |
|-------------|-----------------|
| TIMEOUT | Retry max 3 回 |
| FAIL | Retry → Rollback |
| CABLE_DROP | Rollback (直前 STEP) |
| EXPLOSION | Abort 即時 |

**Pre-flight check (smoke 起動前)**:
- TensorBoard surr_loss / value_loss / policy std smoothness (CC4 IC v9a iter 17 + AC v21 iter 6 collapse 回避)
- AC checkpoint α-anneal (α ≤ 0.65 推奨、iter ≥ 100/200 で BC dominance 軽減)
- `enable_camera=False`、`assert env.num_obs == 45` (CC3 MED C4 fix)

**Smoke abort criteria**:
- ≥2 ep 連続 NaN (単一許容、`feedback_autonomous_kill_authorized.md` lesson 整合)
- ≥3 ep 連続 EXPLOSION
- STEP 1-2 (scripted) 失敗 = scene/IK 設計 bug、即 abort

### 15.7 Smoke methodology (CC2/CC3/NHA fix)

**Z3 採用** (CC#2 Option C' 完了後の AC adapter checkpoint、A6 UPGRADED to RECOMMENDED):

| Option | 不採用/採用理由 |
|--------|--------------|
| Z1 (legacy AC Apr 19) | REJECTED: KA7 empirical 0/10 (cable-randomized) |
| Z2 (CC#2 mid-training iter 19/400) | REJECTED: SR declining 24.6%→23.3%、α=0.69 BC dominant (PPO 31%、MPPI demo imitator behavior)、`model_best.pt` plain ActorCritic NOT MultiSkillActorCritic (CC3 CRIT C1)、`build_multi_skill_policy` 不適合 |
| **Z3 (CC#2 完了後)** | **採用**: Option C' 完了 checkpoint、α=0.5 converged、cable-DR trained、MultiSkillActorCritic adapter 想定 |

**Smoke trigger condition**:
- CC#2 Option C' 完了確認 (`handoff.md` mtime update、script mtime、rs 通知)
- TensorBoard success_rate plateau + mean_reward smoothness check
- α ≤ 0.65 (実装 iter ≥ 100)

**Smoke 実行 device**: **cuda:2** (CLAUDE.md GPU セクション明記、RTX PRO 4000 Blackwell 24GB、CC#2 cuda:0 干渉なし)

### 15.8 Implementation plan (CC6 NHA fix)

**eval_skill.py extension 採用** (新規 `wet_run_phase5_2_1clip.py` 不要、重複回避):

- 既存 `eval_skill.py:302-337` `_load_policy` pattern 流用:
  - base_model なし: `runner.alg.policy.load_state_dict(sd)` plain ActorCritic load
  - base_model あり: `apply_skill_adapter(runner, base_model, skill_type)` adapter load
  - skill_embedding remapping (5→7 skill) handling
- 既存 `eval_skill.py:71-143` `SKILL_REGISTRY` (6 entry) 拡張:
  - 新 entry `phase5_2_1clip`: AC + CLAMP + IC の 3 checkpoint 投入
- 拡張 interface (Sub-B 実装、本 §15 は spec のみ):
  - `--orchestrator-1clip` mode + `--ac-checkpoint` + `--clamp-checkpoint` + `--ic-checkpoint` + `--base-model`
  - STEP 1-10 execution driven by `routing_orchestrator.execute_step(step_id)`
  - State handoff: `SnapshotManager.capture/restore` (Phase 5-1b Cluster B)
  - Per-STEP video recording: `eval_skill.py:164` `EvalRecorder` 流用
- LoC 推定: **~100-150 LoC 拡張** (eval_skill.py 編集) vs 元 PROPOSE 250 LoC 新規

### 15.9 §14 との関連

§14 全 section (14.1-14.8) と §15 は consistent: §15 は §14 orchestrator design の **Phase 5-2 実行仕様 specialization**。§14.5 recovery engine / §14.4 `derive_skill_result` / §14.3 SnapshotManager / §14.6 12D action 統一 / §14.7 5 RL SkillType は全て §15 実装で流用。

### 15.10 Out of scope (rs 承認、別 task escalate)

- **CLAMP success 条件問題** (RL-Routing-Progress.md Session 127、dist 5-6mm OK success 0%) → 別 task 起票候補 (Critical path 漏れ)
- **Layer 4b cable lift regression** (`thread-vault/12-Cable-Lift-Regression/` 既起票、`DEFINE_PENDING_APPROVAL`)
- **AC retrain**: CC#2 Option C' active (P0、本 session touch せず、~17-35h 推定)
- **IC G5 converter / DAPG retrain**: P4 + P6、別 CC session 起票予定 (critical path ~2-3週)
- **AR Phase 6 F8 writeup**: Phase 5-3 で AR 必要、別 CC session 起票予定
- **Path X1 / X2 wet-run script 実装**: Sub-B 別 session、CC#2 完了 trigger
- **Phase 5-3 (2-clip) / Phase 5-4 (5-clip full)**: 本 §15 scope 外、別 section 起草候補

---

## 教訓

- 加算型報酬の構造的欠陥: per-step magnitude差が支配目的を決める
- 乗算結合は2目的に対する構造的解: magnitude無関係に両方改善が有利
- 合成初期状態でスキル並行化: VBD settle -> cache で正当化

---

## Related

- `thread-vault/04-Specs/SOMA.md` - 目標定義・Phase進捗
- `thread-vault/06-Knowledge/LL-SuccessCondition-C1C5.md` - C1-C5定義
- `thread-vault/06-Knowledge/LL-P1-Sequential-DualArm.md` - P1詳細 (圏論)

## Consolidated from (原本)

- `thread-vault/04-Specs/routing_motion_sequence.md` - 43ステップ工程 (-> Section 2)
- `thread_isaac_lab/docs/DAPG_DESIGN.md` - DAPG+DR+Demo Pipeline (-> Section 5,6,7,8,9)
- `thread-vault/06-Knowledge/LL-3Skill-UnifiedDesign.md` - 3スキル統合設計 (-> Section 4)
- `thread-vault/06-Knowledge/LL-P1-Sequential-DualArm.md` - P1分割 (-> Section 3)



## 3スキル統一仕様 (2026-04-02 追記)

InsertIntoClip env作成時にBUG 3件 + 不整合 6件を検出・修正。
全スキル共通の定数・インターフェース・IK convention・FK interpolation仕様を策定。

**詳細:** [[06-Knowledge/LL-SkillEnvConsistency]]

**修正済みBUG:**
- IK rotation target: wxyz→xyzw (ik_objectives.py:618 準拠)
- FK interpolation loop: PHYSICS_STEPS_PER_RL=10 必須
- Batched FK buffer: wp.transform / wp.spatial_vector / dof_count

**統一済み定数:** ROT_ACTION_SCALE=0.05, EPS_POS=0.015, EPS_ORI=0.25, INSERT_TERMINAL_STEPS=200
