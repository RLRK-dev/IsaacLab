# THREAD Vault Index

Content-oriented catalog of all wiki pages.
Read this FIRST on session start. See [[VaultProtocol]] for conventions.

**Total: ~124 pages across 9 directories (00-08) + raw/templates**

---

## 00 Project Management (7)

- [[project-tree-manifest]] — NEST tree view（§2 = `build_nest_snapshot.py` 生成の薄い view; 全 body は `project-tree-manifest-archive-2026H1.md`）
- [[project-tree-manifest-archive-2026H1]] — manifest 歴史 body の byte 保全 archive（2026-07-02 統合 M1）
- [[operational-rule-LTM-1]] — NEST 仕様書 (SSOT, LTM-1 v1.2)
- [[operational-rule-LTM-1-v1.2-diff-proposal]] — WITHDRAWN (2026-05-31 Neumann 案; ⚠ 本「v1.2」は landed v1.2 注記と別物 — label collision note 参照)
- [[nest-adoption-runbook]] — NEST 段階採用 runbook
- [[assumption-register]] — 仮定台帳
- [[decision-ledger]] — 決定台帳

## 01 Architecture (6)

- [[System Overview]] — dual-arm cable manipulation 全体像
- [[Agent-Independent Architecture]] — Code A/B/C エージェント非依存設計
- [[Hardware Configuration]] — A6000 + Blackwell GPU構成
- [[Software Stack]] — Isaac Sim/Lab, Newton, VLM, 制御スタック
- [[Coordinate Systems and Conventions]] — 座標系, 四元数, DH
- [[harness-code-a-4phase-analysis-20260401]] — Code A 4-phase分析

## 02 Workflow (10)

- [[VaultProtocol]] — Karpathy LLM Wiki pattern, 3層アーキテクチャ, V1-V10ルール
- [[Claude Code Integration]] — Code A/B/C 自律システム
- [[Autonomous Agents]] — サブエージェント一覧
- [[Vault Write Permissions]] — Vault書き込み権限マトリクス (SSOT)
- [[Vault Maintenance]] — 健全性チェック・定期メンテナンス
- [[Operational Rules]] — 試行錯誤禁止・パラメータプロトコル
- [[Video Analyzer Gate]] — 動画検証ゲート + Evidence Pack
- [[Remote Monitoring]] — system-monitor, SSOT監視
- [[Terminal Workflow T1-T4]] — Legacy (現在はsystemd)
- [[HANDOFF]] — セッション引き継ぎ状態

## 03 Issues (7)

- [[Issue Index]] — 全Issue一覧 (ISS-001〜005, LL-ID)
- [[IC-ObsReward-Misalignment]] — ~~CRITICAL~~ FIXED: obs groove-relative axis-angle error (2026-04-09)
- [[AR-PenaltyDominance]] — CRITICAL: penalty:reward=18.6:1, hover deadlock (2026-04)
- [[DH Parameter Mismatch]] — ISS-002 Resolved: Standard/Modified DH混同
- [[NaN Explosion Investigation]] — ISS-001 Mitigated (PhysX-era)
- [[Common Failure Patterns]] — カテゴリ別 症状→原因→対策
- [[Error Pattern Tracking]] — LL-ID追跡

## 04 Specs (21)

Core:
- [[SOMA]] — 目標定義・Phase進捗・実装マッピング (SSOT)
- [[SUBLIMATE]] — 上位プロジェクト構造
- [[Single Source of Truth Registry]] — 全SSOT一覧
- [[Gate System]] — 中間Gate + PASS/FAIL判定 + Evidence Gate
- [[RUN Metrics]] — run共通言語 / 進捗SSOT
- [[Testing Progression]] — テスト段階的複雑化ルール

Robot & Physics:
- [[Robot Parameters]] — Franka Panda (task_config.py SSOT)
- [[Cable Physics Parameters]] — VBD rod パラメータ
- [[IK Solver Configuration]] — DifferentialIKController のみ
- [[Dual-Arm Reaching]] — 双腕到達 v1-v9 (40/40 PASS, Completed)

RL & Policy:
- [[Phase 3 RL Roadmap]] — RL段階的アプローチ
- [[Unified Policy Architecture]] — 3層統合ポリシー設計
- [[Phase E-G Design Stock]] — Phase E-G 設計ストック

Vision:
- [[Vision Pipeline]] — ビジョンパイプライン
- [[Camera Backend]] — Depth逆投影 (Completed)
- [[Vision Stack Roadmap]] — ビジョン技術進化ロードマップ

Harness & Tooling:
- [[Validate Script Spec]] — validate.sh 3層invariant enforcement
- [[Harness Improvement v1]] — Harness v2 spec + 実装結果

SUBLIMATE Mapping:
- [[Crystal9-THREAD-Mapping]] — DU/R → コード対応
- [[Deterministic Core - Stochastic Shell]] — 決定論コア設計
- [[NFRCP-THREAD]] — NFRCP マッピング

## 05 Thinking (8)

- [[Experiment Log]] — 実験記録 (CC追記可)
- [[Bug-and-Mistake-History]] — バグ・ミス履歴
- [[DLO Research Survey]] — DLO操作研究サーベイ (2025-2026)
- [[Knowledge Map]] — ビジュアル化された知識体系
- [[Next Moves]] — 優先行動
- [[Open Questions]] — 未解決の問い
- [[Incident-20260405-Unauthorized-Kill]] — インシデント記録
- [[progress_delta_2026-04-25]] — RL-Routing-Progress.md 乖離 + 2026-04-24/25 findings delta memo（歴史記録; 対象 file は 2026-07-02 FROZEN、監視は終了）

## 06 Knowledge (57)

**Full listing: [[Knowledge Index]]** (カテゴリ別ナビゲーション)

Newton VBD / Physics (9): [[LL-Newton]], [[Newton-Solver-Compatibility]], [[Newton-Cable-Test-Results]], [[Newton-FEM-Cable-Findings]], [[LL-Cable-Model-Mismatch]], [[WR-AddRod-CableModel]], [[LL-VBD-MultiWorld-Verification]], [[VBD-SoftContact-Grasping-Research]], [[LL-CablePreconditionDiversity]]

Newton Collision / Contact (4): [[LL-CollisionPipeline]], [[LL-CollisionPipeline-Hydroelastic]], [[Newton-SDF-Collision-Pipeline]], [[Newton-BallJoint-Cable-Attachment]]

Newton Robot / Integration (4): [[Newton-URDF-Import-Guide]], [[Newton-Panda-Hydro-IK-Pattern]], [[Newton-DualSolver-Cloth-Franka]], [[Newton-RSL-RL-Compatibility]]

Newton Demo Survey (2): [[Newton-Demo-Complete-Survey]], [[Newton-Demo-Survey-Batch2]]

IK / Trajectory (4): [[Isaac-Lab-DiffIK]], [[LL-IK-Trajectory]], [[DiffIK-X-Drift]], [[DiffIK-Incremental-Target-Research]]

RL / Reward (9): [[LL-DualArm-RewardStructure]], [[LL-RewardDeadlock]], [[LL-RewardHacking-Analysis]], [[LL-TimeoutBootstrapping]], [[LL-InsertClip-AlphaMin]], [[LL-BaseAdapter-Design]], [[LL-SkillEnvConsistency]], [[LL-SkillChaining-Verify]], [[WR-DAPG-StateConditional-BC]]

Bug History (3): [[LL-ApproachCable-BugHistory]], [[LL-AerialRegrasp-BugHistory]], [[LL-KinematicAttachment-Failure]] (includes official Franka mechanism-baseline lesson)

Harness / Infrastructure (6): [[LL-BestOfN-Harness]], [[LL-HarnessArchReview-2026-04-01]], [[LL-HarnessEngineering]], [[LL-NemotronVerifier]], [[LL-Infrastructure]], [[Nemotron-Nano-AWQ-vLLM]]

Process / Methodology (5): [[LL-Aletheia]], [[LL-Process]], [[LL-Retrain-Framework]], [[LL-Terminology]], [[LL-RobotTAS-Day6-Lessons]]

External Tech (5): [[LL-Cosmos]], [[LL-GR00T]], [[LL-ActiveInference]], [[Isaac-Sim-6.0-Migration]], [[KN-NVIDIA-Demo-Strategy]]

Legacy PhysX (3): [[LL-Physics]], [[PhysX-N-Dependency]], [[LL-Orchestration-Design]]

Visual Obs / Camera (1): [[LL-VisualObs-CameraSystem]]

Other (2): [[FSM-LLM-Recovery]], [[LL-SimPerformance]]

Coordinator (1): [[LL-Coordinator-Parallel-Work-Candidates-2026-04-27]] (CC#1 並行 work 24 candidates 包括列挙、2026-04-27 fresh resume session)

Option-E Design (1): [[GD-S2A-ControlledDelivery]] — S2(a) Level-2 controlled-delivery implementation SPEC (B-ii elevate→cage→release retention; 6 deliverables + 10 downstream reqs to S6/S1/S8; banked 2026-06-14, rs+%18 PV)

## 07 Design (11)

- [[00-DESIGN-STATUS-LEDGER]] — 07-Design 成否 SSOT (成否 = 本 file が権威)
- [[RL-Routing-Design]] — RL Routing統合設計 (工程・スキル・DAPG・DR) (SSOT)
- [[RL-Routing-Progress]] — ⚠ FROZEN (≤2026-05-28 歴史、env6-VBD 系譜); 現進捗 → 地図 `docs/logical_decomposition.html` + [[00-DESIGN-STATUS-LEDGER]]
- [[S1B-Faithful-Finger-Design]] — historical failed/abandoned Newton faithful-finger design; do-not-repeat record
- [[Gripper-VGroove-Design]] — ◇ V-groove (SUPERSEDED by コ 2026-06-20; up-cap/drag reference のみ)
- [[PoseEstimation-Design-v3.2]] — pose estimation 設計 (head)
- [[PoseEstimation-Design-v3.1]] / [[PoseEstimation-Design-v3]] / [[PoseEstimation-Design-v2]] / [[PoseEstimation-Design-v1]] — superseded pose-est 系譜
- [[Mechanical-Specs]] — 機械仕様

## 08 DA-MPPI (10)

Dashboard (DA-MPPI M3 skill demo generation + M4 converter):

- `08-DA-MPPI/01-Dashboard/status.md` — DA-MPPI overall status
- `08-DA-MPPI/01-Dashboard/m3_ac_design.md` — M3-AC design (ApproachCable, α-4 npz COMPLETE)
- `08-DA-MPPI/01-Dashboard/m3_aerial_regrasp_design.md` — M3-AR design (AerialRegrasp)
- `08-DA-MPPI/01-Dashboard/m3_aerial_regrasp_define_v1.md` — M3-AR DEFINE
- `08-DA-MPPI/01-Dashboard/m3_aerial_regrasp_pre_check.md` — M3-AR pre-check
- `08-DA-MPPI/01-Dashboard/m3_aerial_regrasp_reward_design.md` — M3-AR reward design
- `08-DA-MPPI/01-Dashboard/m3_grip_design.md` — **M3-Grip design (G1-G2 COMPLETE 2026-04-22, G3 pending)**
- `08-DA-MPPI/01-Dashboard/m3_ic_design.md` — M3-IC design (InsertClip, G0-G1 COMPLETE 2026-04-24)
- `08-DA-MPPI/01-Dashboard/m3_unclamp_design.md` — M3-Unclamp design (G0-G1 COMPLETE 2026-04-24)
- `08-DA-MPPI/01-Dashboard/m4_converter_design.md` — M4 converter (HDF5 → DAPG npz)
- `08-DA-MPPI/01-Dashboard/results-phase6.md` — Phase 6 results
- `08-DA-MPPI/01-Dashboard/results-phase6-ar.md` — Phase 6 AR results

## raw (1)

- [[RT-TrainMonitor-Design]] — Train Monitor設計 (source document)

## templates (2)

- [[define-template]] — タスク定義テンプレート
- [[Issue Template]] — Issue作成テンプレート

---

## Maintenance Rules

1. This file MUST stay under 200 lines. If exceeded, split by category.
2. Every wiki page MUST have an entry here.
3. Orphan detection: vault-lint skill flags pages not listed here.
4. On every ingest: update relevant section + append to log.md.
