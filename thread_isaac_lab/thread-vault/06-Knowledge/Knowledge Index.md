# Knowledge Index

#knowledge #index

> 06-Knowledge/ 全ファイルへのナビゲーション。カテゴリ別に整理。

---

## Critical Preflight: Mechanism / Sensor / Measurement

ロボット機構、接触、ケーブル、カメラ、測定点、動画確認を変更・評価する前に、`[[LL-Process]]` の `LL-2026-06-03-PROC-006` と「機構・センサ作業前の必読 Knowledge セット」を確認する。今回の S1B retained-zero 失敗は、公式/実績ある Franka 機構・Newton demo・接触 pipeline・カメラ/測定点の知見が分散しており、前提ゲートとして参照されなかったことが主因だった。

- [[LL-CrossAgent-KnowHow-Sharing]] — Claude Code (%3) ↔ Codex 横断ノウハウの共有 canon (**DRAFT, 独立レビュー待ち**)。spring-follow≠公式Franka / 右手=FK-cache zero-inv-mass passive / faithful 系譜=PhysX DiffIK / reuse-first / dual-format 共有機構 (Rs 2026-06-04)。

---

## Newton VBD / Physics

Newton 1.0 VBD solver 関連の知見。THREAD の現行物理エンジン。

- [[LL-Newton]] — Newton VBD solver 総合知見 (solver一覧, GA情報, VBD設定, 落とし穴)
- [[Newton-Solver-Compatibility]] — Newton 8 solver 機能マトリクス (Featherstone, VBD, MuJoCo等)
- [[Newton-Cable-Test-Results]] — Newton VBD cable 物理テスト結果 (N-dependency 完全解消の実証)
- [[Newton-FEM-Cable-Findings]] — add_soft_grid FEM cable 知見 (Rod NaN回避, grip成功)
- [[LL-Cable-Model-Mismatch]] — add_soft_grid vs add_rod 移行 (cable X追従不良の根本原因)
- [[WR-AddRod-CableModel]] — add_rod (Cosserat rod) cable パラメータ設計 (FEM vs Rod比較)
- [[LL-VBD-MultiWorld-Verification]] — VBD multi-world 検証結果 (4/8/16/32 worlds ALL PASS, ~55 FPS)
- [[VBD-SoftContact-Grasping-Research]] — VBD soft contact による FEM cable 把持の技術調査
- [[LL-CablePreconditionDiversity]] — AR vs AC/Grip cable precondition per-world diversity 構造解析 (Option C' fix 提案)

## Newton Collision / Contact

Newton の衝突検出・接触パイプライン。

- [[LL-CollisionPipeline]] — CollisionPipeline 動作条件と制約 (MESH形状, MuJoCo内蔵との違い)
- [[LL-CollisionPipeline-Hydroelastic]] — CollisionPipeline + HydroelasticSDF 知見 (requires_grad排他, ke averaging)
- [[Newton-SDF-Collision-Pipeline]] — SDF衝突検出パターン (rigid mesh同士, nut_bolt_sdf例)
- [[Newton-BallJoint-Cable-Attachment]] — BALL joint cable attachment パターン (kinematic anchor構築)

## SolverMuJoCo CPU (Option-E S5 grasp findings, 2026-06-10)

S5 把持 (UR5e+Robotiq, rigid-link cable) のベンチ群で確定した SolverMuJoCo CPU 基盤知見。
全て DRAFT (author %13, %3 独立レビュー待ち)。

- [[LL-Xfrc-Inert-Actuation-TruePositive]] — `d.xfrc_applied` は無音 no-op / 正路 = `state.body_f` LIN-first per-substep / 力・駆動計器の着地真陽性必須 (RULE-2 EXTENSION)
- [[LL-GhostContact-DoNotUse]] — 正値 solref ζ>1 は k∝1/ζ² 軟化 → N≈0 不動のゴースト接触 (真 overdamp = 負値形式)
- [[LL-Condim-Rolling-Mechanism]] — condim=3 に転がり摩擦なし (log-rolling escape −80.6mm) / ノブは rolling 行が立って初めて有効 / μ_roll は長さ単位・明示必須
- [[LL-G3-Vacuity]] — 「荷重下 zero-slip ≤2mm」偽 PASS の二重機構 (刺激不着地 + 内在 creep で到達不能) と creep-budgeted ゲート再設計則
- [[LL-Creep-Characterization]] — ピンチ creep は内在的・荷重鈍感 (5×でも −7〜14%) / R4 134.9 vs R6 60.4 µm/f / §1.4 lift 系ゲートへの含意

## Newton Robot / Integration

Newton でのロボットセットアップと統合パターン。

- [[Newton-URDF-Import-Guide]] — URDF Import 手順と落とし穴 (Joint Drive 不動問題, gravity comp)
- [[Newton-Panda-Hydro-IK-Pattern]] — Panda Hydroelastic IK Pick-and-Place パターン (公式デモ)
- [[Newton-DualSolver-Cloth-Franka]] — Featherstone + VBD デュアルソルバーパターン (cloth_franka例)
- [[Newton-RSL-RL-Compatibility]] — RSL-RL + Newton multi-world 互換性調査 (VBD例ゼロの注意)

## Newton Demo Survey

Newton 1.0 GA 公式デモの網羅的調査。

- [[Newton-Demo-Complete-Survey]] — 全62デモ完全調査 (THREAD移行に必要な全APIパターン)
- [[Newton-Demo-Survey-Batch2]] — THREAD関連度の高い6本の詳細分析 (Hydroelastic, cable, IK, dual-solver)

## IK / Trajectory

DifferentialIKController と軌道計画。

- [[Isaac-Lab-DiffIK]] — DiffIK 使用条件・設定・既知問題 (frame変換, PD gains, command形式)
- [[LL-IK-Trajectory]] — Franka Panda 到達性解析 + IK/軌道計画の知見
- [[DiffIK-X-Drift]] — DiffIK Xドリフト調査 (Null Space Drift, Rotated Base Frame)
- [[DiffIK-Incremental-Target-Research]] — DiffIK 漸進目標 + PhysX把持中クラッシュ調査

## RL / Reward / DAPG

強化学習パイプライン関連。**設計は `thread-vault/07-Design/RL-Routing-Design.md` に統合済み。**

- **07-Design/RL-Routing-Design.md** — 統合設計書 (工程・スキル・DAPG・DR・成功条件・報酬・obs)
- **07-Design/RL-Routing-Progress.md** — 進捗記録（⚠ ≤2026-05-28 FROZEN; 現進捗 → 00-DESIGN-STATUS-LEDGER + 地図）
- [[LL-Terminology]] — THREAD 用語集 (routing, DAPG, dry-run/wet-run)
- [[LL-DualArm-RewardStructure]] — dual-arm 報酬構造設計
- [[LL-RewardDeadlock]] — 報酬デッドロックパターン (penalty dominance等)
- [[LL-RewardHacking-Analysis]] — 4スキル横断の報酬ハッキング脆弱性分析
- [[LL-TimeoutBootstrapping]] — timeout bootstrapping value_loss爆発の根本原因
- [[LL-InsertClip-AlphaMin]] — InsertClip α_min=0.5 BC維持方針
- [[LL-BaseAdapter-Design]] — Base Adapter設計 (スキル別判断)
- [[LL-SkillEnvConsistency]] — スキル-Env整合性チェック
- [[LL-SkillChaining-Verify]] — スキルチェイニング検証
- [[WR-DAPG-StateConditional-BC]] — DAPG State-Conditional BC 技術調査
- [[LL-DemoData-Expansion-Strategy]] — デモデータ拡張方針 (DAPG+DR / 失敗近傍重視 / 接触可観測性制約 / 機構fidelity下流; GR00T風の大規模合成は不要)

## Bug History

スキル別のバグ修正経緯・失敗分析。

- [[LL-ApproachCable-BugHistory]] — ApproachCable env バグ修正経緯 (SSOT)
- [[LL-AerialRegrasp-BugHistory]] — AerialRegrasp env バグ修正経緯
- [[LL-KinematicAttachment-Failure]] — kinematic attachment 失敗と公式Franka準拠確認の教訓

## Process / Methodology

設計方法論・プロセス改善。

- [[LL-Aletheia]] — Generator-Verifier分離原則 (Code A/B/C境界)
- [[LL-Retrain-Framework]] — 再訓練フレームワーク (崩壊checkpoint対処)
- [[LL-Orchestration-Design]] — オーケストレーション設計


## Harness / Infrastructure

GPU, 動画, 設定管理, ハーネス, 開発プロセス。

- [[LL-Infrastructure]] — GPU, Video, インフラ知見 (GPU誤診断, CUDA設定, 動画記録)
- [[LL-Process]] — プロセス・設計判断の知見 (摩擦係数不一致, 設定管理, 公式仕様/既存実装優先; VaultProtocol V11 参照)
- [[LL-SimPerformance]] — シミュレーション性能プロファイリング (physics_step 85%, 最適化)
- [[LL-HarnessEngineering]] — 長時間自律エージェントのハーネス工学 (Legible Env, Verification, Generic Tools)
- [[LL-HarnessArchReview-2026-04-01]] — ハーネスアーキテクチャレビュー (2026-04-01)
- [[LL-BestOfN-Harness]] — Best-of-N ハーネス設計
- [[LL-NemotronVerifier]] — Nemotron Layer 3 Pattern Verifier
- [[Nemotron-Nano-AWQ-vLLM]] — Nemotron Nano AWQ vLLM セットアップ

## External Technology Research

NVIDIA 技術・外部ツールの調査。

- [[KN-NVIDIA-Demo-Strategy]] — NVIDIA デモ提供戦略 (Newton dual-arm cable の技術的希少性)
- [[KN-Toyota-RL-Perception-Sim2Real]] — Toyota 未来創生センター RL の知覚 sim2real (観測誤差+遅延を実測→sim観測に注入)。THREAD image-level DR (D1-D8) に無い delta = 観測 latency 次元 + 実測-then-match (`PoseEstimation-Design-v1:55` が「未実装の解」と flag 済)。fact-checked 2026-06-24、採用=Rs判断 (NOT yet adopted)。
- [[LL-Cosmos]] — NVIDIA Cosmos World Foundation Model (World Model RL候補, 未調査)
- [[LL-GR00T]] — NVIDIA GR00T ロボット基盤モデル (低優先度, THREAD直接関連薄い)
- [[LL-ActiveInference]] — Active Inference 理論調査
- [[Isaac-Sim-6.0-Migration]] — Isaac Sim 6.0 移行調査 (リリース状態, Newton統合)
- [[FSM-LLM-Recovery]] — FSM + LLM リカバリ方式調査

## Legacy (PhysX-era)

PhysX ベースの知見。Newton 移行後は参考情報。

- [[LL-Physics]] — PhysX solver 知見 (NaN爆発, solver iterations, 数値安定性)
- [[PhysX-N-Dependency]] — PhysX N-dependency 調査 (GPU batch collision の致命的バグ)

---

**Total:** 102 top-level .md files (1 index + 101 notes; measured `ls *.md | wc -l` 2026-06-24 — prior "97"@2026-06-10 was stale; not all notes are indexed above)
**Updated:** 2026-06-24
