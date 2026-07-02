---
title: THREAD Project Tree Manifest
created: 2026-04-28T03:22:00+09:00
last_updated: 2026-06-29T04:11:00+09:00 (AR mujoco-コ L-hold lift-fix RESULT = PARTIAL/FAIL triple-converged: single-L cage creeps to table → NEEDS-DUAL, WR-gradual banked ~5×, R3 PASS, 0-commit, sufficiency-test/Rs-fork pending — see LEDGER:53 + docs/logical_decomposition.html §1+CURRENT FRAME; full subtree sync = deferred lazy-view)
root_node_id: T-ROOT
root_goal: Isaac Lab / SIM 5-clip cable routing vision-based task operation; 100% remains final/ultimate goal (Rs 2026-06-23, 95 to 100; qualitative target at this stage, not a literal statistical SR), current bar is basic SIM operation first
root_goal_source: thread_isaac_lab/thread-vault/log.md:2026-06-05 03:42 decision + 03:48 correction
program_status: |
  Human-Rs SIM rescope (2026-06-05): current project target is Isaac Lab / SIM.
  Real-world / physical Franka x2 deployment is out of current scope; REAL2SIM / sim-to-real transfer remains future-awareness only.
  100% is the final/ultimate goal (Rs 2026-06-23, 95 to 100; qualitative target at this stage, not a literal statistical SR; = the P0-KILL #2 predicate-redefinition), not the current bar; the current bar is basic SIM operation, rough/imperfect task performance acceptable before precision/accuracy improvement.
  Human-Rs foundation rigor correction (2026-06-05): robot mechanism, environment, and cable are the foundation and must be rigorous / physically-valid / reuse-first / gate-reviewed.
  Rough/imperfect latitude does not apply to foundation; spring-follow / KINEMATIC_INV_MASS / kinematic tricks / teleport / physics-bypass holds are not acceptable as foundation.
  L1.F/G and L1.H H3/H4/H5/H6 real/HIL lanes are future REAL2SIM / out-of-current-scope unless Human-Rs reopens them. L1.H H2 is current SIM bring-up lane; H7 is final/ultimate SIM 95% acceptance lane.
  PRODUCT_GO=false; physical_grasp_claim=false; sim2real_success_claim=false; T_ROOT95=false; Stage_2=false; production=false.
  2026-06-05 H2 runtime update: AppLauncher import-surface preflight PASS was %3 post-verified; SIM-foundation scene bring-up smoke PASS was %3 post-verified; retroactive %3 Tier-A of the task_config.py init constants diff and assets_cfg.py modular-split import diff PASS. These are prerequisite foundation bring-up milestones only, not task success, foundation sufficiency, 95%, product, physical, sim2real, Stage-2, or production.
  2026-06-05 source authority update: foundational source changes (task_config.py, assets_cfg.py, dual_arm_cfg_opt_a.py, and other mechanism/env/cable source) require %3 Tier-A before apply. %7 autonomous authority covers HCG/GPU launches, not foundational source mutation.
  2026-06-05 methodology update: Human-Rs added a parallel Claude Code + Codex development-methodology goal, explicitly including NEST. %7 determined it should be nodeized under T-Meta; no numeric KPI and no unilateral LTM-1/VaultProtocol/automation rewrite.
  P0 KILL (2026-05-19): T-ROOT 95% as originally scoped assessed infeasible-as-scoped (goal NOT abandoned).
  Restructured spine: T-ROOT-Legacy-Architecture (ARCHIVED) -> T-ROOT-R0-Measurement-Foundation
  (COMPLETE: f(1.0)=0.7227, ceiling 1-f=0.277 << 0.95) -> T-ROOT-R1-Product-Predicate-Decision
  (COMPLETE; sim2real-only predicate attested; verdict PROVISIONAL pending %7/Rs, Q1) ->
  T-ROOT-R2-Architecture-Redesign (#3, DEFERRED/conditional - was "current axis", SUPERSEDED 2026-06-23 by L1.X Substrate-Realism #1 (Option-E); child R2-A-Track-A = env6-VBD, PRODUCT_GO_FALSE, superseded; see the 2026-06-23 body UPDATE block + docs/logical_decomposition.html §1).
  Recorded into NEST 2026-05-31 (tracking lapsed since 2026-05-13; manifest frozen since 2026-05-05).
  Historical COMPLETE statuses are NOT product/launch GO.
spec_version: LTM-1 v1.1
runbook_version: nest-adoption-runbook v1.1
adoption_phase: "archived to project-tree-manifest-archive-2026H1.md (section adoption_phase); 24KB inline append-log moved 2026-07-02 (M2, audit P2-8); frontmatter key retained"
note: |
  本 manifest は NEST first-adopter trigger (nest-adoption-runbook §1) の Y2 採択時 deployment 経で起票。
  Logic tree v1 + master list v2 を tree skeleton として採用 (Y2 = KA2 partial、γ tree v2 redesign defer)。
  既存 active legacy task は §6.2 段階適用、現 phase 中は legacy format 維持、次 phase 起動時 NEST 準拠 reflect。
---

# THREAD Project Tree Manifest


> ⚠ **薄い生成 view（planning-surface consolidation 2026-07-02, node `T-ROOT-Planning-Surfaces-Consolidation-20260702`）。**
> - **manifest への `## UPDATE` block 追記は禁止** — node 追記・進捗は各 node の `state.md` にのみ書く（LTM-1 v1.2 注記準拠）。
> - **§2 全 node list は `scripts/build_nest_snapshot.py` の生成領域**（`GEN:NEST` marker 間、手書き禁止）。
> - §1/§4/§6/§7 の本文は `project-tree-manifest-archive-2026H1.md` に byte 保全で移設済。§3（session）/§5（archive list）は本ファイルに温存。

## §1 Tree 構造 (text)

Logic tree v1 (`~/.claude/projects/-home-rlrk-IsaacLab/memory/project_logic_tree_2026-04-27.md`) の skeleton をそのまま採用。Y2 では γ tree v2 redesign を defer (LTM-1 v3 defer 原則整合、empirical motivation 不足)。

**→ 完全な NEST tree（234-node ASCII skeleton）は [`project-tree-manifest-archive-2026H1.md`](./project-tree-manifest-archive-2026H1.md) §1 に byte 保全で移設。** 現用の正規詳細ビュー = NEST jsx tracker（`docs/nest-tracker/index.html`）+ §2 GEN node list + `docs/nest-tracker/nest-snapshot.json`。読む入口 = 地図 `docs/logical_decomposition.html`。

## §2 全 node list (state.md exists or archived nodes only)

<!-- GEN:NEST:BEGIN (build_nest_snapshot.py; 手書き禁止) -->

_234 nodes — `build_nest_snapshot.py --emit-manifest-section` 生成 (SSOT = per-node state.md; 手書き禁止)。status = verbatim (coercion なし)。全 node 詳細/依存 = NEST jsx tracker + nest-snapshot.json。_

| node_id | status | parent |
|---|---|---|
| `T-AC-RewardRedesign-Phase1` | COMPLETE | `T-Skill-AC` |
| `T-AR-Alpha4b` | IN_PROGRESS | `T-Skill-AR` |
| `T-CLAMP-R-Phase-3-Future-Roadmap-Draft` | IN_PROGRESS | `T-Skill-CR` |
| `T-CLAMP-R-Train-PROPOSE-Prep` | IN_PROGRESS | `T-Skill-CR` |
| `T-CLAMP-R-Train-Phase-1-PROPOSE` | IN_PROGRESS | `T-Skill-CR` |
| `T-CLAMP-R-Train-Phase-2-Smoke-Actual-Runner` | IN_PROGRESS | `T-Skill-CR` |
| `T-CLAMP-R-Train-Phase-2-Smoke-Execute-Spec` | IN_PROGRESS | `T-Skill-CR` |
| `T-CLAMP-R-Train-Phase-2-Smoke-Plan` | IN_PROGRESS | `T-Skill-CR` |
| `T-CLAMP-R-Train-Phase-2-Smoke-Run-Readiness-Check` | IN_PROGRESS | `T-Skill-CR` |
| `T-Coord-NEST-Audit-Wave-2` | IN_PROGRESS | `T-ROOT-COORD` |
| `T-Coord-NEST-Snapshot-Manifest-Final-Consolidation-Wave-6` | IN_PROGRESS | `T-ROOT-COORD` |
| `T-Coord-NEST-Snapshot-Manifest-Final-Wave-7-Consolidation` | IN_PROGRESS | `T-ROOT-COORD` |
| `T-Coord-Wave-6-Cross-Skill-Consistency-Audit` | IN_PROGRESS | `T-ROOT-COORD` |
| `T-Coord-Wave-7-Cross-Skill-Consistency-Audit` | IN_PROGRESS | `T-ROOT-COORD` |
| `T-DA-MPPI` | IN_PROGRESS | `T-L1C-PerSkill-RL` |
| `T-Empirical` | IN_PROGRESS | `T-ROOT` |
| `T-FC-MultiClip` | PENDING | `T-Forward-Capability` |
| `T-FC-OffCenter-Grasp` | COMPLETE | `T-Forward-Capability` |
| `T-FC-Perception` | PENDING | `T-Forward-Capability` |
| `T-FC-SingleClip` | COMPLETE | `T-Forward-Capability` |
| `T-Forward-Capability` | IN_PROGRESS | `T-ROOT` |
| `T-GC-KA7-Noise-Sweep` | IN_PROGRESS | `T-Skill-GC` |
| `T-IC-P4-Cable-Seg-Cost-Lower` | IN_PROGRESS | `T-Skill-IC` |
| `T-IC-P4-Phase-2-Smoke-Plan` | IN_PROGRESS | `T-IC-P4-Cable-Seg-Cost-Lower` |
| `T-IC-Phase-A-P3` | COMPLETE | `T-Skill-IC` |
| `T-L1-B` | IN_PROGRESS | `T-ROOT` |
| `T-L1-F` | PENDING | `T-ROOT` |
| `T-L1-F-1` | PENDING | `T-L1-F` |
| `T-L1-F-2` | PENDING | `T-L1-F` |
| `T-L1-F-3` | PENDING | `T-L1-F` |
| `T-L1-F-4` | PENDING | `T-L1-F` |
| `T-L1-F-5` | PENDING | `T-L1-F` |
| `T-L1-F-6` | PENDING | `T-L1-F` |
| `T-L1-F-7` | PENDING | `T-L1-F` |
| `T-L1-G` | PENDING | `T-ROOT` |
| `T-L1-G-1` | PENDING | `T-L1-G` |
| `T-L1-G-2` | PENDING | `T-L1-G` |
| `T-L1-G-3` | PENDING | `T-L1-G` |
| `T-L1-G-4` | PENDING | `T-L1-G` |
| `T-L1-G-5` | PENDING | `T-L1-G` |
| `T-L1-G-6` | PENDING | `T-L1-G` |
| `T-L1-G-7` | PENDING | `T-L1-G` |
| `T-L1-H` | IN_PROGRESS | `T-ROOT` |
| `T-L1-H-H0` | IN_PROGRESS | `T-L1-H` |
| `T-L1-H-H1` | PENDING | `T-L1-H` |
| `T-L1-H-H2` | IN_PROGRESS | `T-L1-H` |
| `T-L1-H-H2-SIM-Foundation-AppLauncher-Preflight-20260605` | COMPLETE | `T-L1-H-H2` |
| `T-L1-H-H2-SIM-Foundation-Scene-Bringup-20260605` | COMPLETE | `T-L1-H-H2` |
| `T-L1-H-H3` | PENDING | `T-L1-H` |
| `T-L1-H-H4` | PENDING | `T-L1-H` |
| `T-L1-H-H5` | PENDING | `T-L1-H` |
| `T-L1-H-H6` | PENDING | `T-L1-H` |
| `T-L1-H-H7` | PENDING | `T-L1-H` |
| `T-L1C-PerSkill-RL` | IN_PROGRESS | `T-ROOT` |
| `T-L1X-Substrate-Realism` | IN_PROGRESS | `T-ROOT` |
| `T-Meta` | IN_PROGRESS | `T-ROOT` |
| `T-Meta-Claude-Codex-Development-Methodology` | IN_PROGRESS | `T-Meta` |
| `T-Meta-Cross-Pane-Coordination-Patterns` | IN_PROGRESS | `T-Meta` |
| `T-Meta-Cross-Pane-Coordination-Patterns-AP-13-Update` | IN_PROGRESS | `T-Meta-Cross-Pane-Coordination-Patterns` |
| `T-Meta-Cross-Pane-Coordination-Patterns-Wave-7-Retrospective-Update` | IN_PROGRESS | `T-Meta-Cross-Pane-Coordination-Patterns` |
| `T-Meta-Multi-Pane-Orchestration-Patterns` | IN_PROGRESS | `T-Meta` |
| `T-Meta-Operational-Framework-V2-Design` | IN_PROGRESS | `T-Meta` |
| `T-Meta-Path-Y-Precedent-Index` | IN_PROGRESS | `T-Meta` |
| `T-Meta-Path-Y-Precedent-Index-2026-05-04-Update` | IN_PROGRESS | `T-Meta-Path-Y-Precedent-Index` |
| `T-Option-E` | COMPLETE | `T-L1X-Substrate-Realism` |
| `T-Predicate-Redefinition` | IN_PROGRESS | `T-ROOT` |
| `T-ROOT-COORD` | IN_PROGRESS | `T-ROOT` |
| `T-ROOT-COORD2-AC-IC-GC-Audit-2026-05-13` | IN_PROGRESS | `T-ROOT-Pivot-Chain-Architecture-Review` |
| `T-ROOT-Cable-Physics-Calibration-Packet-Design-2026-05-13` | IN_PROGRESS | `T-ROOT-Pivot-Chain-Architecture-Review` |
| `T-ROOT-Chain-Architecture-Pivot-Design-Packet-2026-05-13` | IN_PROGRESS | `T-ROOT-Pivot-Chain-Architecture-Review` |
| `T-ROOT-Chain-Context-Math-Diagnostic-2026-05-13` | COMPLETE | `T-ROOT-Pivot-Chain-Architecture-Review` |
| `T-ROOT-D0-AC-PreCheck-Review-2026-05-13` | COMPLETE | `T-ROOT-Pivot-D0-AC-Pre-Check-Packet-2026-05-13` |
| `T-ROOT-D0-AC-Revision-MicroDesign-2026-05-13` | COMPLETE | `T-ROOT-Pivot-D0-AC-Pre-Check-Packet-2026-05-13` |
| `T-ROOT-D0-AC-Warmup-MicroDesign-2026-05-13` | COMPLETE | `T-ROOT-D0-AC-Revision-MicroDesign-2026-05-13` |
| `T-ROOT-D0-Close-D1-ResetForensics-2026-05-13` | COMPLETE | `T-ROOT-Pivot-Chain-Architecture-Review` |
| `T-ROOT-D1-LoRA-S1-Design-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-Snapshot-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Finger-Threshold-Design-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Parity-Review-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Gate-Review-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Design-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Heuristic-Saturation-Review-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Phase2-Design-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Parity-Review-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Revision-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Phase2-Design-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Finger-Threshold-Design-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Phase2a-Design-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Phase2-Design-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-Revision-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Gate-Review-2026-05-13` |
| `T-ROOT-D1-LoRA-S1-S3-PPO-Design-2026-05-13` | COMPLETE | `T-ROOT-D1-LoRA-S1-Phase2a-Design-2026-05-13` |
| `T-ROOT-D1-LoRA-Snapshot-2026-05-13` | COMPLETE | `T-ROOT-D0-Close-D1-ResetForensics-2026-05-13` |
| `T-ROOT-Legacy-Architecture` | ARCHIVED | `T-ROOT` |
| `T-ROOT-Phase2-V2-Provenance-Repair-Design-2026-05-13` | COMPLETE | `T-ROOT-Cable-Physics-Calibration-Packet-Design-2026-05-13` |
| `T-ROOT-Pivot-Chain-Architecture-Review` | COMPLETE | `T-ROOT` |
| `T-ROOT-Pivot-D0-AC-Pre-Check-Packet-2026-05-13` | COMPLETE | `T-ROOT-Pivot-D0-AC-Scripted-Base-Design-2026-05-13` |
| `T-ROOT-Pivot-D0-AC-Scripted-Base-Design-2026-05-13` | COMPLETE | `T-ROOT-Chain-Architecture-Pivot-Design-Packet-2026-05-13` |
| `T-ROOT-Planning-Surfaces-Consolidation-20260702` | IN_PROGRESS | `T-ROOT` |
| `T-ROOT-R0-Measurement-Foundation` | COMPLETE | `T-ROOT` |
| `T-ROOT-R1-Product-Predicate-Decision` | COMPLETE | `T-ROOT` |
| `T-ROOT-R2-A-Track-A-S1B-5FCF-Default-Off-Checker-Syntax-Guardfix-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-5FCF-Default-Off-Runtime-Parity-Gate-Package-20260531` | DISCARDED | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-5FCF-Telemetry-Collection-Exact-Command-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-CLI-Schema-Gap-Review-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Exact-Source-Diff-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Exact-Spec-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Post-Release-Hold-Redirection-Design-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Redesign-Exact-Source-Diff-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Redesign-Exact-Spec-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Redesign-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-Reward-Design-Precheck-Gate-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-V2-Redesign-Exact-Source-Diff-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-V2-Redesign-Exact-Spec-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-V2-Redesign-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-V2-Reward-Design-Precheck-Gate-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-V21-Hold-Strategic-Reassessment-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D1-V21-Reward-Design-Precheck-Gate-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-D245-Default-Off-Runtime-Parity-Gate-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Host-NVIDIA-Stability-Attestation-V1-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Host-NVIDIA-Stability-Root-Cause-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-OptionB-Source-Alignment-Exact-Diff-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-OptionB-Source-Alignment-Exact-Diff-Resealed-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-OptionB-Source-Apply-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Post-Release-Retention-Architecture-Reassessment-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Provenance-Dtype-Exact-Diff-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Provenance-Dtype-Source-Apply-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Retained-Zero-Video-Verification-Exact-Source-Diff-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Retained-Zero-Video-Verification-Exact-Spec-Package-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Telemetry` | IN_PROGRESS | `T-ROOT-R2-Architecture-Redesign` |
| `T-ROOT-R2-A-Track-A-S1B-Telemetry-Diagnostic-Artifact-Analysis-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Telemetry-Diagnostic-Comparative-Analysis-20260601` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Telemetry-Exact-Command-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Telemetry-GPU-Query-Guardfix-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-A-Track-A-S1B-Telemetry-Rebased-Exact-Command-Package-20260531` | COMPLETE | `T-ROOT-R2-A-Track-A-S1B-Telemetry` |
| `T-ROOT-R2-Architecture-Redesign` | IN_PROGRESS | `T-ROOT` |
| `T-ROOT-optE-route-dapg-C1C2` | IN_PROGRESS | `T-L1C-PerSkill-RL` |
| `T-RS6-6` | IN_PROGRESS | `T-L1X-Substrate-Realism` |
| `T-RS7-1` | IN_PROGRESS | `T-L1X-Substrate-Realism` |
| `T-Retention-Model` | IN_PROGRESS | `T-Forward-Capability` |
| `T-Skill` | IN_PROGRESS | `T-ROOT` |
| `T-Skill-AC` | IN_PROGRESS | `T-Skill` |
| `T-Skill-AC-Cross-Skill-Apply-Transfer-Design` | IN_PROGRESS | `T-Skill-AC` |
| `T-Skill-AR` | IN_PROGRESS | `T-Skill` |
| `T-Skill-AR-Architecture-Redesign-Control-Authority-Terminal-Hold` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Architecture-Redesign-Design` | COMPLETE | `T-Skill-AR` |
| `T-Skill-AR-Architecture-Redesign-Terminal-Stability` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Architecture-Redesign-World-Distribution-Heterogeneity` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Dispatcher-v2-Fix-A-Apply` | COMPLETE | `T-Skill-AR` |
| `T-Skill-AR-Dispatcher-v2-Fix-A-Spec` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Master-Verdict-6of6-Aggregate-Final-Apply` | COMPLETE | `T-Skill-AR` |
| `T-Skill-AR-Master-Verdict-Aggregation-Design` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Master-Verdict-Aggregator-v2-Actual-Impl` | COMPLETE | `T-Skill-AR` |
| `T-Skill-AR-Pair3-Completion-Monitor-Master-Verdict-6of6-Plan` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Phase-4-2-Attribution-Bridge` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Phase-4-3-H1-Terminal-Stability-Bridge` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Terminal-Stability` |
| `T-Skill-AR-Phase-4-Terminal-Metric-Layer-Baseline` | COMPLETE | `T-Skill-AR` |
| `T-Skill-AR-Phase-5-A6-A2-Design-Re-Entry` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Phase-5-A6-Implementation-Packet` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Phase-5-RightArm-R1R3-Narrowing-Design` | COMPLETE | `T-Skill-AR-Architecture-Redesign-Design` |
| `T-Skill-AR-Phase-Alpha4c-PROPOSE-Final` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Phase-Alpha4c-PROPOSE-Final-5-CC-Pre-Debate-L3-Launch-Readiness-Final` | COMPLETE | `T-Skill-AR` |
| `T-Skill-AR-Phase-Alpha4c-PROPOSE-Final-Launch-Readiness-Checklist` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Phase-Alpha4c-PROPOSE-Prep` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Phase-Alpha4c-Pre-Debate-Prep` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-AR-Phase-Alpha4c-Smoke-Plan` | IN_PROGRESS | `T-Skill-AR` |
| `T-Skill-CR` | IN_PROGRESS | `T-Skill` |
| `T-Skill-CR-B5-Semantic-Design` | COMPLETE | `T-Skill-CR` |
| `T-Skill-CR-Phase-2-Detailed-Design` | IN_PROGRESS | `T-Skill-CR` |
| `T-Skill-CR-Phase-3-Design-Draft` | IN_PROGRESS | `T-Skill-CR` |
| `T-Skill-CR-Sub-Tree-Audit-Initial-Design` | IN_PROGRESS | `T-Skill-CR` |
| `T-Skill-GC` | IN_PROGRESS | `T-Skill` |
| `T-Skill-GC-EvalGap` | COMPLETE | `T-Skill-GC` |
| `T-Skill-GC-PostKA7-PROPOSE-Prep` | IN_PROGRESS | `T-Skill-GC` |
| `T-Skill-IC` | IN_PROGRESS | `T-Skill` |
| `T-Skill-IC-P4-Phase1-Sweep-Actual-Run-Readiness-Check` | COMPLETE | `T-Skill-IC` |
| `T-Skill-IC-P4-Phase1-Sweep-Run-Trial-Neumann-Application` | ARCHIVED | `T-Skill-IC` |
| `T-Skill-IC-P4-Phase1-Sweep-Wrapper-Actual-Impl` | IN_PROGRESS | `T-Skill-IC` |
| `T-Skill-IC-P4-Phase1-Sweep-Wrapper-Impl-Spec` | IN_PROGRESS | `T-Skill-IC` |
| `T-Skill-IC-P4-Phase2-Smoke-Wrapper-Actual-Impl` | COMPLETE | `T-Skill-IC` |
| `T-Skill-IC-P4-Phase2-Smoke-Wrapper-Impl-Spec` | IN_PROGRESS | `T-Skill-IC` |
| `T-Skill-IC-P5-Cost-Redesign-Design` | IN_PROGRESS | `T-Skill-IC` |
| `T-VBD-AC` *(archived)* | ARCHIVED | `—` |
| `T-Vision` | IN_PROGRESS | `T-ROOT` |
| `T-Vision-CableState` | IN_PROGRESS (design APPROVED 2026-05-03 + impl Phase 1 COMPLETE 2026-05-04T03:50 + impl Phase 2 design 2026-05-04T03:55 + impl Phase 3 integration design 2026-05-04T05:05 + impl Phase 4 validation design spawn 2026-05-04T14:05 + master closure design spawn 2026-05-04T14:50 T-ROOT-COORD#s11、impl phased decomposition 採択経 Q1+Q2 = T-Vision-CableState-Impl-Phase-1、Phase 2 design (Stage C/D/E skeleton + impl-design memo) = T-Vision-CableState-Impl-Phase-2-Design、Phase 3 = Stages A-E end-to-end integration design + Q5 benchmark protocol initial = T-Vision-CableState-Impl-Phase-3-Integration-Design、Phase 4 = validation methodology + benchmark protocol final = T-Vision-CableState-Impl-Phase-4-Validation-Design、Master Closure = 4-phase design master closure synthesis + Phase 5/6/7 impl spawn-readiness assessment = T-Vision-CableState-Master-Closure-Design (cross-Phase synthesis 軸 + impl spawn forward-looking 軸、orthogonal vs Phase 3 horizontal cross-stage / Phase 4 vertical cross-criteria)、Phase 5 train + Phase 6 impl + Phase 7 benchmark execution は後続子 node 候補 — Phase 番号 renumber 2-shift 経 (Phase 3 で旧 Phase 3=Stage C train → 新 Phase 4 に 1-shift 済、本 Phase 4 = Validation Design 占有 経で更に 1-shift: 旧 Phase 4-6 → 新 Phase 5-7)、Phase 3 が Integration Design + Phase 4 が Validation Design を占有 + Master Closure が cross-Phase synthesis を占有 (Phase 番号 占有せず)) | `T-Vision` |
| `T-Vision-CableState-Impl-Phase-1` | COMPLETE | `T-Vision-CableState` |
| `T-Vision-CableState-Impl-Phase-2-Design` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-CableState-Impl-Phase-3-Integration-Design` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-CableState-Impl-Phase-4-Validation-Actual-Test-Runner` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-CableState-Impl-Phase-4-Validation-Dataset-Prep-Spec` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-CableState-Impl-Phase-4-Validation-Design` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-CableState-Impl-Phase-4-Validation-Execute-Spec` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-CableState-Master-Closure-Design` | IN_PROGRESS | `T-Vision-CableState` |
| `T-Vision-DR` | approved (design phase 2026-05-03 Rs batch approve T-ROOT-COORD#s11) — NEST canonical lifecycle PENDING (impl trigger 待ち per §1 dependencies、T-Vision-Pose Stage 1-2 + T-Vision-CableState Stage A-E ready 後 IN_PROGRESS 遷移) | `T-Vision` |
| `T-Vision-DR-Impl-Phase0-PrepDesign` | IN_PROGRESS | `T-Vision-DR` |
| `T-Vision-DR-Impl-Phase1-D6-Background-Design` | IN_PROGRESS | `T-Vision-DR` |
| `T-Vision-Fusion` | IN_PROGRESS | `T-Vision` |
| `T-Vision-Fusion-Impl-Phase-0-Skeleton` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-Fusion-Impl-Phase-1-Architecture-Design` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Integration` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Skeleton` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-Fusion-Impl-Phase-1-Baseline-Design` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-Fusion-Impl-Phase-2-Benchmark-Design` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-Fusion-Impl-Phase-3-Optimization-Design` | IN_PROGRESS | `T-Vision-Fusion` |
| `T-Vision-L1A-Master-Integration-Design` | IN_PROGRESS | `T-Vision` |
| `T-Vision-Pose` | APPROVED_FOR_IMPL | `T-Vision` |
| `T-Vision-Pose-MVP0` | IN_PROGRESS | `T-Vision-Pose` |
| `T-Vision-Pose-MVP0-Impl-PhaseA1-Restart` | IN_PROGRESS | `T-Vision-Pose-MVP0` |
| `T-Vision-Pose-MVP0-Impl-PhaseA2-Actual-Impl-Skeleton` | IN_PROGRESS | `T-Vision-Pose-MVP0` |
| `T-Vision-Pose-MVP0-Impl-PhaseA2-Design` | IN_PROGRESS | `T-Vision-Pose-MVP0` |
| `T-Vision-Pose-MVP0-Impl-PhaseB` | IN_PROGRESS | `T-Vision-Pose` |
| `T-Vision-Pose-MVP0-Impl-PhaseB1-Eval-Resume-Plan` | IN_PROGRESS | `T-Vision-Pose` |
| `T-Vision-Pose-MVP0-PhaseB-Actual-Impl-Production-Code` | IN_PROGRESS | `T-Vision-Pose-MVP0` |
| `T-Vision-Pose-MVP0-PhaseB-Trial-Neumann-Application` | ARCHIVED | `T-Vision-Pose-MVP0` |
| `T-WM` | IN_PROGRESS | `T-ROOT` |
| `T-WM-G1` | IN_PROGRESS | `T-WM` |
| `T-WM-G2` | IN_PROGRESS | `T-WM` |
| `T-WM-G2-4-Task-Chain-Spawn-Execution-Gate-Verify` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-4-Task-Chain-Spawn-Launch-Final-Readiness` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A0` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A1-Setup` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A1-Train-Run` | COMPLETE | `T-WM-G2-P1-Layer1-Spawn-Coord` |
| `T-WM-G2-A1-Train-Run-Qwen-Variant` | COMPLETE | `T-WM-G2-P1-Layer1-Spawn-Coord` |
| `T-WM-G2-A2-PromptAdapter` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A3-Build-Run` | COMPLETE_WITH_LIMITATION | `T-WM-G2-P1-Layer1-Spawn-Coord` |
| `T-WM-G2-A3-Build-Run-Qwen-Variant` | COMPLETE_WITH_LIMITATION | `T-WM-G2-P1-Layer1-Spawn-Coord` |
| `T-WM-G2-A3-TensorRTLLM-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A4-Pipeline-Integration-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A5-Eval-Methodology-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A6-Bench-Run` | PENDING | `T-WM-G2-P1-Layer1-Spawn-Coord` |
| `T-WM-G2-A6-Risk-Register-Expansion` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A6-Risk-Register-N4-N8-Trial-Neumann-Application` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A7-Hook-Run` | PENDING | `T-WM-G2-P1-Layer1-Spawn-Coord` |
| `T-WM-G2-A8-Integration-Test-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A9-PreDeploy-ClusterG-Audit-Hook-Actual-Script` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A9-PreDeploy-ClusterG-Audit-Hook-Spec` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A9-Production-Deploy-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-A9-Production-Deploy-PRECHECK-Gate-Spec` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-Implementation-Sequence-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-Master-Roadmap-Design` | COMPLETE | `T-WM-G2` |
| `T-WM-G2-P1-Layer1-Spawn-Coord` | COMPLETE_WITH_LIMITATION | `T-WM-G2` |
| `T-WM-G2-Spawn-Readiness-Final-Consolidation` | COMPLETE | `T-WM-G2` |

_legend — 非正準 status (raw, coercion なし): APPROVED_FOR_IMPL, COMPLETE_WITH_LIMITATION, IN_PROGRESS (design APPROVED 2026-05-03 + impl Phase 1 COMPLETE 2026-05-04T03:50 + impl Phase 2 design 2026-05-04T03:55 + impl Phase 3 integration design 2026-05-04T05:05 + impl Phase 4 validation design spawn 2026-05-04T14:05 + master closure design spawn 2026-05-04T14:50 T-ROOT-COORD#s11、impl phased decomposition 採択経 Q1+Q2 = T-Vision-CableState-Impl-Phase-1、Phase 2 design (Stage C/D/E skeleton + impl-design memo) = T-Vision-CableState-Impl-Phase-2-Design、Phase 3 = Stages A-E end-to-end integration design + Q5 benchmark protocol initial = T-Vision-CableState-Impl-Phase-3-Integration-Design、Phase 4 = validation methodology + benchmark protocol final = T-Vision-CableState-Impl-Phase-4-Validation-Design、Master Closure = 4-phase design master closure synthesis + Phase 5/6/7 impl spawn-readiness assessment = T-Vision-CableState-Master-Closure-Design (cross-Phase synthesis 軸 + impl spawn forward-looking 軸、orthogonal vs Phase 3 horizontal cross-stage / Phase 4 vertical cross-criteria)、Phase 5 train + Phase 6 impl + Phase 7 benchmark execution は後続子 node 候補 — Phase 番号 renumber 2-shift 経 (Phase 3 で旧 Phase 3=Stage C train → 新 Phase 4 に 1-shift 済、本 Phase 4 = Validation Design 占有 経で更に 1-shift: 旧 Phase 4-6 → 新 Phase 5-7)、Phase 3 が Integration Design + Phase 4 が Validation Design を占有 + Master Closure が cross-Phase synthesis を占有 (Phase 番号 占有せず)), approved (design phase 2026-05-03 Rs batch approve T-ROOT-COORD#s11) — NEST canonical lifecycle PENDING (impl trigger 待ち per §1 dependencies、T-Vision-Pose Stage 1-2 + T-Vision-CableState Stage A-E ready 後 IN_PROGRESS 遷移). 正準 = IN_PROGRESS / COMPLETE / DISCARDED / ARCHIVED (+ PENDING)._

<!-- GEN:NEST:END -->

## §3 Active session list (並行 CC 干渉防止用、Tier 2 parent-mediated queue 経由 update)

| session_id | node_id | host_pid | started_at | last_heartbeat |
|---|---|---|---|---|
| T-ROOT-COORD#s2 | T-ROOT-COORD | 3655709 | 2026-04-28T01:30:00+09:00 | 2026-04-28T04:30:00+09:00 |
| T-Skill-GC-EvalGap#s2 | T-Skill-GC-EvalGap | 4102709 (dead) | 2026-04-28T18:18:00+09:00 | 2026-04-28T18:18:00+09:00 (BOOT only、no heartbeat、stale_no_close per L0-Coordinator#s4 audit) |

### Scheduled cron monitors (passive、CC-A-HIGH-1 fix)

| schedule_id | node_id (provisional) | type | next_fire | description |
|---|---|---|---|---|
| `trig_018DSGsMfRYY1Mwz...` (2026-05-08 hook review) | T-COORD-MONITOR-HOOK-REVIEW | cron monitor | 2026-05-08T10:07:00+09:00 | Multi-agent hook 2-week pattern review (`scheduled_multi_agent_hook_review_2026-05-08.md`) |
| `trig_0186rZzNh8MLLzhN...` (2026-05-09 §16 re-trigger) | T-COORD-MONITOR-S16-RECHECK | cron monitor | 2026-05-09T09:00:00+09:00 | Phase 5-3 v2 §16 commit re-trigger evaluation (`scheduled_section16_recheck_2026-05-09.md`) |
| `trig_019YZZELFBKSK418...` (2026-05-09 Phase 5-3 v2 / C5 cable loss) | T-COORD-MONITOR-LAYER4B-C5 | cron monitor | 2026-05-09T10:00:00+09:00 | Layer 4b / C5 cable loss 2-week follow-up (`scheduled_layer4b_c5_check_2026-05-09.md`) |
| `trig_01MX1ZGCG41c83WF...` (2026-05-10 F1-WarmStart G5 readiness) | T-COORD-MONITOR-F1-WARMSTART | cron monitor | 2026-05-10T09:00:00+09:00 | F1-WarmStart G5 wet-run readiness check (`scheduled_f1_warmstart_g5_followup_2026-05-10.md`) |

**注 (cron monitor as nodes)**: 各 cron は logical NEST node、actual state.md 配置は cron 発火時の receiving CC が起票 (§6.2 段階適用 trigger)。本 manifest §3 は schedule registration only、cron 発火 までは PENDING 相当。

**注 (host_pid 履歴、CC-D-HIGH-1 fix)**:
- 2026-04-28T03:22:00+09:00 entry: pid 3513195 (manifest 起票時)
- 2026-04-28T04:15:00+09:00 entry: pid 3655709 (7-fix turn)
- 2026-04-28T04:30:00+09:00 entry: pid 3655709 (本 残 issue 解決 turn、変化なし)
- session continuity (CC#1 conversation) は同一 session、host_pid は claude runtime spawn 経で update可能。Tier 2 queue 経で本 update 反映。

**注 (legacy active sessions、本 manifest 起票時点で per-session naming handoff 経で signal、Tier 2 queue 経由 update 想定)**:
- T-MainCCA-Phase2#s? (latest mtime 2026-04-27T05:46:00+09:00、heartbeat stale ~22h)
- T-CLAMPR-PhaseC5#s? (latest mtime 2026-04-27T01:25:00+09:00、heartbeat stale ~26h)
- T-GC-EVAL-GAP#s? (handoff_cc_grip_clamp_eval_task_gap*.md mtime 推定 ~2026-04-27、heartbeat stale ~24h+)

→ 上記 3 sessions 全 stale (≥22h)、coordinator drift incident framework 中期対策 #1 (central daemon) urgency 増大 evidence。本 manifest §3 で stale heartbeat 明示 化、後続 routing 判断 (close marker 起票 / restart 起票 等) の input。

## §4 Dependency graph (precedent / blocker、cross-tree dependent scan 用)

**→ 完全な依存グラフ（precedent/blocker、cross-tree dependent scan 用）は [`project-tree-manifest-archive-2026H1.md`](./project-tree-manifest-archive-2026H1.md) §4 に byte 保全で移設。** 各 node の最新依存は state.md `dependencies:` が SSOT。

## §5 Archive list (DISCARDED + ARCHIVED + COMPLETE、依存解決用 status snapshot 保持)

| node_id | original_name | status | archived_at | reason | provenance |
|---|---|---|---|---|---|
| T-VBD-AC | AC-VBD-Physics-Investigation | ARCHIVED (DISCARDED 2026-04-27 → ARCHIVED 2026-04-28) | 2026-04-28T03:21:00+09:00 (state.md 配置 + archive 移管 turn) | NO_ACTION (Rs Option C-1 採択 2026-04-27)、true mechanism 不確定 + WM Cascade primary path | `~/.claude/projects/-home-rlrk-IsaacLab/memory/handoff_cc_ac_vbd_physics_investigation_close_2026-04-27.md` |

### COMPLETE meta-process tasks (CC-A-HIGH-4 fix、DONE feedback rules archived)

| node_id (provisional) | original_name | status | completed_at | reason | provenance |
|---|---|---|---|---|---|
| T-COORD-RULE-CLOSE-DISCIPLINE | B-3 Coordinator-Close-Discipline | COMPLETE | 2026-04-27 | drift framework 中期対策 #1 候補 base、12-18h close obligation formalize | `~/.claude/projects/-home-rlrk-IsaacLab/memory/feedback_cc1_session_close_discipline.md` |
| T-COORD-RULE-NOTIFYBACK | B-4 Subsession-NotifyBack-Protocol | COMPLETE | 2026-04-27 | per-session naming signal file pattern、SSOT contention 防止 | `~/.claude/projects/-home-rlrk-IsaacLab/memory/feedback_subsession_notifyback_protocol.md` |
| T-COORD-RULE-RSDISPLOG | B-5 Rs-Disposition-Log-Centralization | COMPLETE | 2026-04-27 | Rs bypass disposition の `_pending_index.txt` log obligation | `~/.claude/projects/-home-rlrk-IsaacLab/memory/feedback_rs_disposition_log_centralization.md` |
| T-COORD-CASCADE-A-G-FLOOR | L1.E.1 Cascade A Cluster G floor | COMPLETE (shipped) | 2026-04-25 | routing_orchestrator 877 LoC + 1271 LoC growth、test 91/91 PASS、WM Cascade Gate 1 達成 | (vault `06-Knowledge` Cluster G design memo + log.md 2026-04-25 entry) |

### Legacy COMPLETE pre-NEST tasks (CC-D-MEDIUM fix、legacy pre-NEST format)

| node_id (provisional) | original_name | status | completed_at | reason | state.md path |
|---|---|---|---|---|---|
| T-LEGACY-SSOT-43STEP | 10-SSOT-Integrity-43STEP | COMPLETE (legacy pre-NEST format、frontmatter LTM-1 v1.1 NOT compliant) | 2026-04-20 | Phase 4c closure、`d42f0376...4d72` task_config.py state pin、wet_run 43 STEP PASS | `thread-vault/10-SSOT-Integrity-43STEP/state.md` |

**注**: T-VBD-AC は NEST issuance (2026-04-27) 以前から active legacy、close (2026-04-27 01:39) 自体は s1 session 中、state.md 配置 + archive 移管 は本 turn (2026-04-28 Y2 採択) で retroactive reflect。

## §6 Y2 採択 (KA2 partial、本 manifest 起票) 経の adoption status

**→ 本文は [`project-tree-manifest-archive-2026H1.md`](./project-tree-manifest-archive-2026H1.md) §6 に byte 保全で移設。**

## §7 Cross-references

**→ 本文は [`project-tree-manifest-archive-2026H1.md`](./project-tree-manifest-archive-2026H1.md) §7 に byte 保全で移設。**

