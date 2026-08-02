# CLAUDE.md (Global + IsaacLab project rules)

This file defines:

- **Global personal defaults** (output roles, modes, scope boundaries, status updates), and
- **IsaacLab-wide project rules** (Newton / PhysX / verification harness / CC Debate patterns).

Project- or phase-specific rules SHOULD go into project-local CLAUDE.md files or skills.

## Global rules summary (詳細: `~/.claude/CLAUDE.md`)

Personal defaults と汎用ワークフロー (Modes / Scope boundaries / Output style / Mode switch / Gate FAIL strategy / 階層ゲート運用 L 判定 / Splitting patterns) は global CLAUDE.md (`~/.claude/CLAUDE.md`、auto-load) で定義。本ファイルは THREAD project 固有ルールに集中。

- **Modes**: Default (balanced) / High-accuracy (strict) / Exploration (breadth)
- **Output style**: User-facing (Japanese) + Internal (English)
- **Mode switch**: 切替時は明示宣言 (User-facing)
- **Scope boundaries**: 別問題は別 session 推奨
- **Gate FAIL**: fix root cause first (受容 / 緩和 / skip は infeasibility 証拠後)
- **L 判定 (階層ゲート運用)**: L0-L3 汎用枠組みは global 参照、project 拡張は §0 階層ゲート運用 (本ファイル後述)

---

@AGENTS.md

# CLAUDE.md v26.07.12

## ⛔ 三原則（常時意識）

1. **変えるな**: rs承認なしにCLAUDE.md・制御方式・方針を変更しない。迷ったら止まって報告
2. **騙すな（自分を）**: 仮説を否定する証拠を先に探せ。rsに迎合するな。3回失敗したら方針を疑え
3. **飛ばすな**: 原因特定→THREAD条件検証→具体的適用。この順序を省略しない

全詳細: `.claude/rules/prohibited.md`（自動ロード）

## 🛑 ハードストップ（該当したら即座に作業中断→rs報告）

- 同一エラーに対する修正が3回失敗した
- 禁止されたAPIやtrickを「今回だけ」使いたくなった
- 修正の修正の修正をしている（パッチの連鎖）
- 「とりあえずこれで動く」という解が浮かんだが根本原因が不明
- 変更の影響範囲を即答できない
- ファイルを編集しようとしているが、そのファイルの最新内容を今のセッションでcatしていない
- 根本原因を特定したにも関わらず、その修正を回避してパラメータ調整・閾値緩和・回避策で対処しようとしている
- PhysX環境の規約をNewton環境に適用しようとしている、またはその逆（再発実績2回。prohibited.md参照）
- `extras["time_outs"]`にexplosion/drop等のterminal stateを含めようとしている（value_loss 105倍爆発の実績。prohibited.md参照）
- タスク指示に含まれない新ファイル作成・新Phase/Gate追加・新CLI引数追加を行おうとしている（改善案がある場合は実装せず提案として報告し、rs承認を待つ）
- 高コスト実験・production launch の根拠が、再現可能な数式・実測値・仮定リスト・低コスト反証テストで裏付けられていない
- ある方針の NO_ACTION / FAIL / 弱さを、別方針の GO 根拠として扱おうとしている
- 引用先を確認した結果、主張された根拠がその file / section / line に存在しない

## ⚓ アンカー式検証（汎用検証方法論）

ロッククライミング原則: **アンカーを打たないと頂上に登れない。自分がいる高さは、最後に「確保した」アンカーまで。未確保のアンカーの上を主張することは “未確認の前進” ではなく、前進していない（＝地面にいる）。** 個別の失敗ごとに対処法を足すのでなく、本方法論 1 本で検証失敗のクラス全体（未知含む）を覆う。

1. **位置は権威ある記録から読む（記憶からでない）。** 多段タスクの現在位置は authoritative な順序記録（ステップ表 / 計画 / node）から読む。目の前の salient な信号や記憶で判断しない。ステップ表は SKILL-DETAIL-DESIGN（旧 VT-DESIGN）が管理する canonical 版（`thread-vault/07-Design/RL-Routing-Design.md` §2 工程設計 等）を driver にする。
2. **各段はアンカー。次へ進む前に ground-truth で確保する。** 「確保」は、その段の述語が**実体（物理状態・権威ソース）**で確認された時のみ成立。代理量（近接・閾値・z 高さ等）／相関した同意（同じ代理を見る複数者・agent の一致＝独立確認でない）／部分・範囲限定の確認（1 点 PASS を面に一般化、phase-scope で whole-route を代替）では確保にならない。全 sub-goal leg を列挙し、主張した成功（成功率の分子）が cover する/しない leg を明示する。
3. **真偽が人間判断を要する所は、人間（Rs）が荷重試験。** critical / 前提アンカー（物理妥当性・把持・固定・着座・貫通等）は、体重をかける（先へ進む・成功を主張する・報告する）前に Rs 確認（動画等）で weight-test する。過去 run / 別条件の確認を流用しない。数値・agent 出力のみで成功を判定しない。
4. **未確保＝地面。そう言う。** 確保できていなければその段は通過していない。位置を正直に報告し、上の点を主張しない・そこから先へ進まない。

本方法論は旧 §運用14/17/18/28/29/30（個別検証対処法）+ §運用19/21/22/23（RL/env 設計 patch）を包摂・置換する。各失敗の specific 事例は vault（`06-Knowledge/LL-*` / memory `feedback-*` / archive `02-Workflow/CLAUDE-md-pruned-archive-2026-07-12.md`）+ 設計 skill（`/reward-design` `/geometric-design` `/pre-check`）に保存し、関連タスク時に §運用4 で参照する（常時ロードの patch にしない）。

## DiffIK制御方式 — PhysX環境の具体 API 形（不変前提「IK 制御のみ・kinematic トリック禁止・制御方式変更は Rs 承認」は全 substrate 共通・§0#3/#5）（他の制御方式への変更はrs承認必須）

**制御API制約（違反はrs承認なしに不可）:**
- **IK: DifferentialIKController のみ使用。JT IK（自前実装）は廃止済み**
- **`write_joint_position_to_sim` 全面禁止**（arm j0-j6 も finger j7/j8 も）
- **`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。例外: オフラインreplay（replay_for_video.py等、制御ループ外の事後可視化）は許可。reset直後の初期化（episode開始時1回）は「関節状態の seed に限り」許可（body 状態の直接書込は不可 — body は `eval_fk`/`mj_forward` で関節から従属させる）。⛔腕を姿勢へ書き込むことは不可 — 腕の開始姿勢は PD の実移動で到達する。ケーブルの reset 再 seed は対象外・現行のまま。〔根拠 = p5 banked charter `charter_v231.md:351`/`:352`/`:360`/`:361`（reset-init 例外 = 失効・cable は対象外）＋ `probe/pd1-arm-pd` で実装済（arm reset 書込 0・サーボ目標のみ）。Rs 承認 2026-07-26〕**
- **finger制御: `set_joint_velocity_target` のみ許可**（open/close両方。符号で方向指定）
- **arm制御: `set_joint_position_target` + `write_data_to_sim` のみ許可**
- **制御方式の変更はrs承認なしに行わない**
- **到達性・収束性の問題はtask_config.pyのパラメータ調整で解決。kinematic attachment、kinematic trick（物理無視のテレポート・強制配置等）禁止**
- 〔上記のうち *具体 API 名*（`DifferentialIKController`/`write_joint_*`/`set_joint_*`）は PhysX 実装形。**不変前提「IK 制御のみ・kinematic トリック（物理無視の強制配置＝アーム関節角の直接書き込み等）禁止・制御方式変更は Rs 承認」は全 substrate 共通（§0#3/#5、`validate.sh` Layer 8 が機械検証）**。**kinematic の認可例外は clip-retention pin の 1 件のみ** ＝ **clip 側がケーブルを保持する機構**（⚠ gripper の把持ではない。工程表の「クランプ」「ケーブル固定」は `RL-Routing-Design.md:1312` のとおり **gripper の把持動作**を指す語なので、本例外の読みに流用しない）。⛔**不許可（不変）= 腕関節角の直接書込 / 指の kinematic close / `update_kinematic_bodies`（FK→physics の body 複写）/ weld・cable-finger attachment。** 根拠 = RS71 §0#5（本節は 07-19 以降も本例外を保持していた）＋ Rs 裁定 2026-07-21 逐語「ただし、クリップのケーブル固定だけは kinematic を使用する」が 07-19 の「完全削除」directive を上書き（custody = `STEP43_C69_EVIDENCE_READBACK_OPSSUP_20260721.md:23`。⚠**Rs 発話は 01:3x と 02:0x の 2 回あり、両 receipt の全体は `RS_PIN_UTTERANCE_CUSTODY_RSTECHLEAD_20260721.md` @ c73 `23c320850e`（branch `probe/pd1-arm-pd`）**）。Newton の対応 API・制御制約は `thread-vault/06-Knowledge/LL-Newton.md` 参照〕

- robot cfg: FRANKA_PANDA_HIGH_PD_CFG ベース（disable_gravity=True（HIGH_PD_CFG準拠）、hand actuatorのみ速度制御に上書き）
- approach: `command_type="position"`、descend/push: `command_type="pose"`
- physics dt: 1/120 (0.00833s)、solver: position=16 / velocity=0 (TGS)
- 根拠: `thread-vault/06-Knowledge/LL-SimPerformance`

## Newton VBD（2026-03-19 開始、rs承認済み）
- **状態:** env6-VBD track（AC/AR/IC/Clamp/Unclamp の全 skill env）は **DISCARDED → mujoco 基盤（コ字形グリッパ）**（Rs 2026-06-26）。Grip（`newton_grip_env.py`）は env7-mujoco **ACTIVE**。成否 SSOT = `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` §FAILED。歴史詳細 = archive `02-Workflow/CLAUDE-md-pruned-archive-2026-07-12.md`
- **環境:** Newton VBD solver（env_isaaclab6 venv）。PhysX環境とは完全に分離
- **⚠ Option-E（mujoco-substrate S-series: S1-S8）の venv は `env_isaaclab7`。版 = 実測 2026-08-03 06:53 JST: Newton 1.4.0 / mujoco 3.11.0 / mujoco-warp 3.11.0 / warp 1.15.0。** ⚠ 版は動く（07-27 20:05 = p5、08-03 06:19 = p4、いずれも Rs 依頼）。経緯と全 246 package の freeze = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P5_ENV7_UPGRADE_20260727/` と `P4_ENV7_UPGRADE_20260803/`。現況は `/home/rlrk/env_isaaclab7/bin/python -m pip list | grep -E 'newton|mujoco|warp'`（4 package 全部が出る。3 package だけ見る書き方は `mujoco-warp` を落とす）。⚠ 旧記載の `env_isaaclab6`（VBD/RL track・Newton 1.0.0）は **on-disk に存在しない**（2026-08-03 実測・preflight P9 WARN）⇒ fallback として引かない。Option-E の smoke/test/build は `/home/rlrk/env_isaaclab7/bin/python` で実行する
- **RL進捗:** `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md`（成否 SSOT）+ 地図 `docs/logical_decomposition.html`（現在 frame）
- **RL設計:** `thread-vault/07-Design/RL-Routing-Design.md`
- **テスト:** `thread_isaac_lab/scripts/test_newton_clip_routing.py`（scripted検証用）
- **ハーネス実行:** 単一ハーネス（`monitor_code_a.sh` + systemd）。複数GPU使用時は複数インスタンスを個別起動
- **検証インフラ:** Video Gate（enforce_video_gate.sh）+ 独立検証（verify_raw_evidence.py）+ Code C独立動画判定（INIT_CODE_C.md）
- 詳細: `thread-vault/06-Knowledge/LL-Newton.md`

## 📊 階層ゲート運用 (L判定) — THREAD project 拡張

L 判定の汎用枠組みは global CLAUDE.md (`~/.claude/CLAUDE.md` の「階層ゲート運用 (L判定) — 汎用枠組み」セクション) を参照。
本セクションは THREAD project 固有の L3 自動昇格キーワード + 直交ゲートを定義する。framework 導入履歴 (Day 1-5) は archive `02-Workflow/CLAUDE-md-pruned-archive-2026-07-12.md`。

### THREAD project L3 自動昇格キーワード

**⛔ FOUNDATIONAL INVARIANT 抵触で即 L3 + STOP (最優先、2026-06-21 single-arm 重大事故後 landing):**
設計案が `thread-vault/04-Specs/RS71-System-Spec-SSOT.md` §0 の不変前提 (DUAL-ARM / 88mm grasp span / DiffIK-only / gripper geometry LOCK / no-kinematic-trick) を**変更する**場合 → 即 L3 + **STOP → BLOCKED_FOR_USER で Rs 確認 → build/probe 前に §運用2 [VERIFY] 5体検証**。前提変更は design tradeoff ではなく Rs専権 (`prohibited.md:18`)。設計を生成する側（CC）は OPTIONS + ESCALATION を出すのみで、独自 method-swap 不可。判定基準: 「この案は §0 不変前提のどれかを変えるか?」— 変えるなら build せず報告。本前提は session 開始時に `handoff_grounding_gate.sh` が auto-echo。

**ファイルパス一致で即 L3 (workflow / ロジック変更時):**
- `thread_isaac_lab/configs/task_config.py` (SSOT、全数値パラメータ)
- `CLAUDE.md` / `.claude/rules/prohibited.md` (本ルールファイル)
- `.claude/skills/*/SKILL.md` の **workflow / protocol 部分** (コメント・typo・docs は除外、L0-L1 扱い)
- `~/.claude/hooks/*` の **logic 部分** (`auto_handoff.sh`、`statusline.sh`、`context_watchdog.sh`、`ctx_thresholds.sh`)
- `thread-vault/04-Specs/SOMA.md` (目標定義)
- `thread-vault/07-Design/RL-Routing-*.md` (RL 設計)
- `thread-vault/00-Project-Management/operational-rule-LTM-1.md` (NEST 仕様書、改訂は L3 cascade per NEST §9)

**diff 内容パターン該当で即 L3:**
- 報酬・成功条件: `reward`、`R_TASK`、`success`、`terminated`、`time_outs` (大文字小文字 grep -i 推奨)
- 物理・制御: `newton`、`vbd`、`featherstone`、`physx`、`ik`、`diffik`、`solver`、`gravity`
- Phase: `phase`、`_reset_worlds`、`episode_length`
- セッション継続性 (context 限定で false-positive 回避): `--compact` コマンド、`/handoff` skill 呼び出し、`PreCompact` hook、`ctx_thresholds`

**領域系:**
- reward/env/成功条件 設計 (旧 §18-23 = ground-truth / obs-reward 整合 / penalty 比率 / multi-world 状態分離 は ⚓ アンカー式検証 + `/reward-design` `/geometric-design` `/pre-check` skill + vault LL-* に集約)
- prohibited.md 記載領域 (timeouts 汚染禁止、PhysX/Newton 混同禁止、崩壊 checkpoint resume 禁止 等)
- prohibited.md 記載の思考プロセス系禁止事項 (対処療法、確証バイアス等) は diff 検出不可、§2 [VERIFY] CC Debate と CC 自己 review でカバー

### 直交ゲート (L 判定と独立、常時必須)

global「直交ゲート」セクションを参照。本 project では:
- **§2 [DESIGN-GATE]** (`/reward-design` + `/pre-check`): reward / env / 成功条件の変更時、L0-L3 いずれでも常時必須
- **prohibited.md 記載領域**: 触れる変更は L 判定と独立に追加検証

## 🌳 NEST 運用 (Node-bound Execution Session Tree)

THREAD project の全 task は logic tree 上の node として管理し、各 node を CC session に 1:1 binding する。本 architecture を NEST と呼ぶ (2026-04-27 命名、Rs 採択)。

**仕様書 (SSOT):** `thread-vault/00-Project-Management/operational-rule-LTM-1.md` (LTM-1 v1.1)
**Root node:** T-ROOT「5-clip cable routing を vision-based で 95% 成功率達成」
**運用開始:** 2026-04-27、新 task は完全準拠、既存 active は次 milestone から段階適用 (NEST §6.1 / §6.2)

**主要 rule (詳細は仕様書参照):**
- node = goal + means + status + dependencies (precedent / blocker のみ) + parent_node + children_nodes + session_history (§2.1、必須要素 8 個)
- session = CC instance、1 node に 1:1 binding (§5.1)
- node ID format: `T-{seq}-{sub}-...` (depth 可変、tree path 反映、§1)
- node 起動承認 (NEST §3.1 #4) = §運用2 [DEFINE] rs 承認で兼ねる (子 node 作成承認は §3.1 別 gate 維持)
- handoff 二系統 (独立): vault sidecar `.sha256` hash file = node progress artifact (§4.2、長期 provenance) / `/handoff` skill = CC context state save (memory `handoff_cc_*.md`)。CC Debate launch 前の `/handoff` は **原則必須ではない**、CC1 状況判断
- cascade: 親 COMPLETE は全子完了 (COMPLETE / ARCHIVED / DISCARDED) が hard precondition (§3.3 #6 + §3.5、auto-absorb 禁止)。自分が parent か leaf かは state.md `children_nodes` field で判定
- DISCARDED → IN_PROGRESS 遷移禁止、復活は新 node_id + provenance reference (§3.7)
- 並行干渉防止 3-tier: per-session signal file (Tier 1) / parent-mediated queue (Tier 2) / flock(2) (Tier 3) (§5.2)
- 本 rule 改訂は CLAUDE.md 変更扱い、L3 cascade per §0 + §運用15 Layer 2 (§9)

**既存 rule との precedence:**
- 抵触時優先順位: CLAUDE.md > NEST 仕様書 > task DEFINE (NEST §0、userMemories は priority chain 別扱い)
- 階層ゲート運用 (L 判定): NEST と直交軸 (L=変更リスク、NEST=task lifecycle)
- parent/child session 概念は NEST node 階層に内包 (詳細 = NEST 仕様書 §3.2 / §3.3 / §4 / §5.1)

## 運用ルール

### セッション管理 (§1, 1b, 11, 13)

1. **Conversation compacted時: 以下を順に実行し再読み込みせよ**
   - `cat ~/IsaacLab/CLAUDE.md`
   - `cat ~/IsaacLab/.claude/rules/prohibited.md`
1b. **セッション開始時のpreflight check必須:** `bash ~/IsaacLab/harness/scripts/preflight_check.sh` を実行。FAILがあれば作業開始禁止 — rsに報告して解決を待つ。WARNはタスク報告に含める
11. **タスク完了時の/clear必須:** タスクのstatus→done移行（Proof of Work確認済み）後、次タスク着手前に必ず`/clear`を実行する。CLAUDE.md が自動再読み込みされ前タスクの context 汚染を防ぐ。同一タスク内の連続作業中は不要
13. **context 制御:** raw ctx 70% で auto `/compact` 自動発火（SSOT: `~/.claude/hooks/lib/ctx_thresholds.sh` SOFT=70/HARD=92）。`/handoff` は状況判断で manual 実行（long task / CC Debate 前 / ctx70% 接近時に state 保全推奨、lossless）。**manual `/compact` は禁止**（情報損失が handoff の保険を上回る）。CC Debate 前 `/handoff` は原則必須ではない（CC1 判断）

### タスク着手前 (§2, 4, 7, 8, 24)

2. **[DEFINE]→[TASK]→[L-TRIAGE]→[DEFER-RECON]→[CHECK]→[VERIFY]→[DESIGN-GATE if 直交該当]→[RULE-CHECK]→[CHANGE]→[HIGH-COST-GATE if 該当]→[RUN]→[RESULT]** — Unknownが残った状態で着手禁止。各 gate:
   - **[HIGH-COST-GATE]** (GPU 10h+ / production launch / multi-skill chain): default NO_GO。`/production-launch-gate` PASS まで [RUN] 不可。chain math / expected SR は file:line 根拠 + 実測再計算 + 仮定リスト必須、仮定は低コスト falsification test を定義。proxy metric だけで判断しない (actual success condition / raw metrics / termination reason 確認)。Rs explicit approval なしに production launch しない
   - **[TASK]** (NEST): node_id (`T-{seq}-{sub}-...`) 併記、tree = `project-tree-manifest.md`。node 起動承認 = 本 [DEFINE] rs 承認で兼ねる
   - **[L-TRIAGE]** (全タスク): `/rule-check stage1` で §0 keyword (path/diff/領域) から final_L (L0-L3) 確定 → 後続 gate に条件付与 ([VERIFY] CC Debate は L2+、§15 層2 事後 debate は L3、層5 多視点は L3 or 3+file)
   - **[DEFER-RECON]** (全 chunk/task、[L-TRIAGE] と [CHECK] の間): 本 chunk の前提を **DEFERRED/PENDING DEPENDENCY REGISTER** (`00-DESIGN-STATUS-LEDGER.md` §DDR、SSOT) と照合。前提が register の未解決 deferred/pending 項目に依存するなら**その項目が本 chunk を GATE** — 解消 or Rs 明示 disposition まで [CHECK] 以降不可。出力 = **reconciliation record** (前提 × register 各項目の依存判定、必須 artifact)。§運用4 prior-art guard は継続必須だが keyword-miss を許すため、本 gate の **register 構造照合が backstop** (grep 単独に依存しない — 2026-07-16/18 の 2 回 miss 再発防止)。**FOUNDATIONAL 依存が未解決なら着手不可** (premise に地面が無い)。register 現行性維持 = PLAN-KEEPER (defer/carry 発生時に即 entry)。
   - **[DESIGN-GATE]** (直交、reward/env/成功条件 変更時常時): `/reward-design` (到達可能性テーブル + 因果DAG + ground-truth値 + トレース) + `/pre-check` (失敗モード検証)、両 PASS まで進まない
   - **[VERIFY]** (adversarial planning は全タスク、CC Debate は L2+): 計画が目的達成するか / 失敗シナリオ最低1 / THREAD 固有条件 (dual-arm/cable/PhysX-Newton/N-dependency) / CHECK と独立ツール検証。proxy・簡略化 setup は ⚓ methodology に従い代表性 verify (実 SSOT = `task_config.py` の CLIP_POSITIONS/table/GRASP_X、矛盾/artifact 無を確認)。CC Debate 詳細 = `verification-subagent` skill (CC1 PROPOSE → CC2-5 Challenger + CC6 NHA → REBUT_OR_ACCEPT → DECIDE)
   - **[RULE-CHECK]** (全変更): `/rule-check stage2` で Tier 0-3 チェックリスト、全 PASS まで [CHANGE] 不可
4. **Vault参照必須（着手前）:**
   タスク内容に基づき参照すべき Vault ファイルを自律判断し、着手前に「参照予定ファイル一覧」を報告。発掘補助 `./scripts/rag_query_vault.sh "..."` は任意（実ファイル `cat` 参照義務は残る）。参照したファイル名・セクションを報告に含める。
   最低限の参照先: 目標定義・Phase進捗 → `SOMA.md` / パラメータ → `SOMA.md` + `task_config.py` / RL設計 → `RL-Routing-Design.md` + `00-DESIGN-STATUS-LEDGER.md` / 現在状態 → `HARNESS_STATE.md` / 実験分析 → `05-Thinking/Experiment Log.md`
   **banked design SSOT 接地（必須・[CHECK]→[VERIFY] の hard gate、handoff/clear 後の最初の着手で特に厳守）:** node の設計・提案・[VERIFY] を伴うタスクでは、支配する banked design SSOT を read + report に cite してから [VERIFY] に進む。handoff narrative / log / memory だけを ground truth にしない。接地順: `00-DESIGN-STATUS-LEDGER.md`（成否SSOT）→ 該当 node の banked design doc → `SOMA.md` → node spec。純粋な readback/status 確認は対象外
   **確定事項の即反映（書込側 hard gate）:** node の設計・状態・値が human により確定/supersede された場合、同一ターンで (1) `00-DESIGN-STATUS-LEDGER.md` の該当行を更新/追加、(2) 主張する全 authoritative doc（07-Design spec + SSOT-INDEX + `SOMA.md`）に supersession flag 反映、(3) 計画 surface（地図 + node state.md、manifest §2 は `build_nest_snapshot.py --emit-manifest-section` で再生成）。07-Design/04-Specs は CC read-only（設計=Rs専権）ゆえ spec 編集未承認時は §運用26 で「spec 更新待ち」を loud に surface。反映 commit は explicit-path の atomic commit
   **新ファイル作成・新仕組み提案の前に、既存Vault・skill定義に同等機能が存在しないことを確認する**（重複作成防止）
   **restore-of-banked-DISCARDED/deleted-track gate:** LEDGER で DISCARDED/FAILED と banked された設計、または git 削除済 track の restore/port は、着手前に §運用10 + §運用26 に従い OPS-SUPERVISOR ↔ RS-TECH-LEAD の cross-PV (advisory、Rs-override 可)
   **Prior-art / no-repeat + Current-state freshness gate (VaultProtocol V7/V9/V10、必須):** 実験・再試行・rerun・source-level promotion 前は `scripts/check_thread_vault_prior_art.sh --fail-on-blocker <keywords...>`（blocker context で STOP）。HANDOFF/SOMA/state surface 編集前後は `scripts/audit_thread_vault_current_state.sh --strict-log` + `scripts/validate.sh --layer 4`（RUNNING/PENDING は観測時刻つきで記録）。guard は fail-closed ゆえ `env_isaaclab/bin/python` 直呼び（`./isaaclab.sh -p` は非ゼロ exit を隠す）
7. **新技術・手法・ライブラリ導入時の事前調査（必須）:** 公式 doc/Changelog で使用条件・既知修正、GitHub Issues/PR/Forums で既知バグ（最低50件）、THREAD 固有条件（dual-arm/segmented cable/PhysX batch solver/N-dependency）との照合でリスク洗い出し → 報告してから着手。詳細 = `/web-research`
8. **設計着手前に `thread-vault/06-Knowledge/` の該当ファイルを参照。未調査の技術は §運用7 を先に実行**
24. **スコープ境界:** CCの実装範囲はrsが指示したタスクの明示的スコープに限定。関連改善アイデアは実装せず「提案」として報告し rs承認後に別タスク。判断基準:「このファイル/Phase/引数はタスク指示文に名前があるか？」— なければ実装禁止。scope外 user 質問は「scope外:」と明示してから回答し実装に発展させない

### 実装中 (§3, 16, 20)

3. **Vault書き込み権限:** `thread-vault/02-Workflow/Vault Write Permissions.md` の権限マトリクスに従う。許可されたディレクトリ以外への書き込み禁止（Rs明示指示時を除く）
16. **先祖返り防止:** ファイルを編集する前に必ず `cat` で最新内容を確認せよ。コンテキスト内の記憶を信用しない。compaction後は特に厳守
20. **不要（ゾンビ）プロセスの即時kill:** 新バージョンの訓練起動時、旧バージョンの**訓練ゾンビプロセス**（defunct・停止済で残存）が `ps aux | grep train_` で見つかったら即座に kill せよ — **Rs 承認不要**。⚠ **稼働中の訓練プロセスの kill・ハーネス停止は Rs 承認必須**（prohibited.md）。ゾンビでない限り自律 kill しない

### 検証・報告 (§5, 15, 25)

5. **報告内の判定・主張の各項目に根拠（ファイル:行番号）必須。推測は「推測」と明記。** 例: `U6 RESOLVED — task_config.py:142 APPROACH_OFFSET_Z=0.15 確認`。根拠なしの判定（「RESOLVED」「PASS」等）は不遵守
15. **結果報告前の事後独立検証（確認バイアス排除、⚓ アンカー式検証に従う）:**
    - **対象:** コード・パラメータ・座標を含む報告は全て。純粋な調査・質問は対象外
    - **層3 機械的検証（全変更）:** `./isaaclab.sh -f` + 変更モジュールの該当テスト + Layer 3 Pattern Verifier（PostToolUse hook）
    - **層2 CC Debate（L3 該当時のみ事後）:** on-disk state を verify（§2 [VERIFY] pre は計画 diff を verify、補完関係）。詳細 = `verification-subagent` skill
    - **層5 多視点並行検証（L3 該当 OR 3+ファイル同時変更）:** 幾何・物理・SSOT 整合の3視点。トリガーは `git diff` パース結果で機械判定
    - **層4 過去の失敗パターン参照:** `scripts/check_thread_vault_prior_art.sh --fail-on-blocker <keywords...>`、blocker で STOP（CC 手動 grep で代替しない）
    - **verdict の conservatism 方向（必須）:** sim が現実より成功を難しく=conservative / 易しく=non-conservative。non-conservative PASS は転移前に高fidelity/実機確認、conservative FAIL は確定的（bank）。**第3 bucket = ABSENT-IN-CODE:** 「robust fact」主張は bank 前に mechanism が runtime code で ACTIVE か検証（未 wired = 「wire-then-validate」= premise FALSE、appearance-only ≠ working）
    - **records-must-match-fact:** (a) date-THEN-write（timestamp は書く前に `date`）(b) 存在/状態主張は同一ターン on-disk 検証 + 時刻限定（無時刻 RUNNING/PENDING 禁止）(c) 「human が X を決定」推論は inference とタグ付け、伝播前に human verbatim と照合
    - **検証出力はrsへの報告に添付する。検証出力なしの結果報告は不遵守**
25. **CC Debate launch 前の context 制御:** `/handoff` は原則必須ではない（CC1 判断）。以下いずれか該当時のみ事前 /handoff 推奨: (a) raw ctx 70% 以上で debate 中 auto-compact 発火 risk (b) debate 結果を後続 turn で再利用する non-trivial work (c) Rs が明示要求。manual `/compact` は禁止（§13）。対象 = §2 [VERIFY] 事前 debate（L2+）+ §15 層2 事後 debate（L3）

### 通信 (§27)

27. **メッセージは必要なことだけ簡潔に書く（Rs 指示 2026-07-15）。** pane 間・Rs 宛とも。
    - **型 = 3 行**: (1) 何をしたか (2) 数値 + **どこに在るか**（`file:line` / sha） (3) 相手に要るもの
    - 詳細・推論・事前登録・撤回は **artifact（doc/json）に書き、path だけ送る**。message に書かない
    - ⛔ **artifact に無い数値を送らない** ／ ⛔ **checkpoint 以外で報告しない**（起動した・走行中・思いつき・途中経過は送らない）
    - ⛔ **他 pane の message の数値で裁定しない**（artifact を自分で見てから裁定する）
    - 例外 = **STOP**（走行中の危険 / 前提の崩壊）のみ即時・短文
    - **メッセージ末尾に日時を付加する（Rs 指示 2026-07-17）**: Rs 宛の報告・他 pane 宛 dispatch とも、message 末尾に `date` 実測の日時（JST）を付加。記憶からの時刻記載は不可（date-THEN-write、§15 records-must-match-fact と同根）
    - **理由**: 未検証の主張が即流れ → 受け手が即裁定 → SSOT に着地 → 訂正が後を追う。2026-07-14 の誤り（artifact に無い「14.5%」を spec に記載 / 撤回済 over-claim の再導出 / stale 行番号の全 pane 伝播）は**すべてこの連鎖**から出た

### エスカレーション (§10, 26)

10. **不整合解消ルール: CCがCLAUDE.md・タスク定義・ユーザー発言の間、または それらと自身の作業状態の間に不整合を発見した場合、実行を止めてrsに報告する。rsが指示を修正・補完した後に実行する**
26. **BLOCKED_FOR_USER（承認ゲート）:** 判断に迷う・承認が必要な場合、state.mdに以下を追記して停止:
    ```
    BLOCKED_FOR_USER: <具体的な質問（1行）>
    Context: <判断に必要な情報>
    Options:
      A) <選択肢1>
      B) <選択肢2>
    Recommendation: <CCの推奨（任意）>
    ```
    - ユーザー承認を得るまで Write/Edit/MultiEdit/NotebookEdit は PreToolUse hook で自動ブロック
    - 他のツールで回避しない（Bashで書き込む等）
    - 承認後は `task-state.sh update` で BLOCKED_FOR_USER 行を削除してから再開
    - Read/Grep/Glob は状況確認のため許可

## スキル参照ガイド（対策案を出す前にスキルをロードし、プロトコルに従って分析）

CCは対策案や推奨を出す前に、該当スキルをロードし、プロトコルの出力（テーブル・断面図・チェックリスト等）を応答内に生成すること。出力なしに提案するのは不遵守。「ロードした」「確認した」だけの言及も不遵守。

| タスク分類 | スキル | いつ使う |
|-----------|--------|---------|
| **設計** | | |
| 位置・形状パラメータ変更 | `/geometric-design` | GRASP_Z, APPROACH_Z, クリップ配置等 |
| 力・剛性パラメータ変更 | `/force-design` | PD gains, 接触剛性, 摩擦係数等 |
| EE軌道設計・IK変更 | `/diffik-trajectory` | `_ik_move_both`, Phase軌道, step size |
| 報酬・env・成功条件設計 | `/reward-design` | reward関数, auto-close threshold, success条件 |
| **事前検証** | | |
| 設計の失敗モード検証 | `/pre-check` | train起動前, env変更前, GPU時間を消費する変更前 |
| **診断** | | |
| NaN・segfault・物理爆発 | `/physics-diagnosis` | cable explosion, force spike |
| テスト結果の判定 | `/gate-evaluation` | PASS/FAIL verdict, Goal Evidence |
| テスト結果の検証 | `/verify-run` | 動画→ログ→照合の三段検証 |
| **Newton環境** | | |
| URDFロボットのセットアップ | `/newton-urdf-setup` | Joint drive mode, solver選択, gravcomp |
| Cable構築・パラメータ設計 | `/newton-cable-design` | add_rod, bend/stretch, 接触, Dahl摩擦 |
| Newton IK設計 | `/newton-ik-design` | IKSolver, Custom Objective, Multi-EE |
| Robot+Cable統合 | `/newton-dual-solver` | Featherstone+VBD, ContactSensor, ArticulationView |
| 環境の段階的検証 | `/newton-validation` | Phase順序, N-dependency |
| **運用** | | |
| 実験実行 | `/experiment-run` | run_id, RUN_METRICS, headless 動画事後生成 |
| シミュレーション実行 | `/isaac-sim-execution` | GPU, zombie process, cable無しテスト高速化 |
| 技術調査 | `/web-research` | 新技術導入前の事前調査 |
| セッション引き継ぎ | `/handoff` | コンテキスト残量少ない時 |

**強制ゲート（スキップ不可）:**
- `/geometric-design` → 位置・形状パラメータ変更時。6ステップ出力（実測・制約・断面図・トレード表・感度分析・因果連鎖）を生成しないと実装に進めない
- `/reward-design` → reward/env/成功条件の設計・変更時。4つの出力物（到達可能性テーブル、因果DAG、ground-truth値、エピソードトレース）を生成しないと実装に進めない
- `/pre-check` → train起動前・GPU時間を消費する変更前。Claude sub-agentで設計の失敗モードを検証。BLOCK判定なら実装禁止

## テスト検証プロトコル（必須）

- **[RUN]完了後、数値報告だけで成功判定しない（⚓ アンカー式検証）**
- **motion-bearing sim RESULT は視覚レグ必須（mandatory-or-justified）:** task 関連 motion（settle/grasp/close/lift/route/drag 等）を含む sim/probe の RESULT/verdict は、視覚レグを skill-path（`/verify-run` or `/video-analyzer` + `video-analyst`）経由で evidence に含める。省略は理由を明示記録（loud）。manual 単一フレーム Read はレグを満たさない
- **検証順序（厳守）: 動画 → ログ → 照合**（動画を先に視覚判定 → `/log-analyzer` でエラー/NaN/IK/Phase → 動画・ログ・RUN_METRICS.json の三者一致で成功判定）。ログ数値で動画解釈を上書きしない
- **Code C（独立動画判定）:** 独立 LLM が動画フレームのみで物理妥当性判定（INIT_CODE_C.md、数値・タスク結果を読まない）→ VERDICT_C.md
- **Fingertip Z-Check Gate（Newton VBD）:** test_newton_clip_routing.py が episode 後 fingertip z を TABLE_HEIGHT と比較、貫通で PASS→FAIL 自動降格（`[ZCHECK]` ログ）
- **ハーネスサイクル完了時の解析対象:** `RESULTS_B.md` / `STATE.json` / `EVENT_LOG.jsonl` / `VERDICT_C.md` + カメラ別動画5本（`ep{N}_{overhead,front,back,left,right}.mp4`）

## Project Identity

THREAD — Dual-arm cable manipulation (UR15 × 2, segmented cable, clip routing).
Repository: Isaac Lab fork with `thread_isaac_lab/`.

## GPU

| 優先順 | Device | Model | Usage |
|--------|--------|-------|-------|
| 1 | cuda:1 | RTX PRO 4000 Blackwell 24GB | VLM + 訓練 |
| 2 | cuda:0 | RTX A6000 48GB | Isaac Sim / Newton |

- **プロセス上限:** A6000 48GB / PRO 4000 24GB は最大**4**プロセス。起動前に `nvidia-smi --query-compute-apps` で確認
- **`CUDA_VISIBLE_DEVICES` 必須:** 訓練プロセス起動時は `CUDA_VISIBLE_DEVICES=N` で使用GPUを限定。未設定だと PyTorch が cuda:0 に不要な context (~264MiB) を確保。例: `CUDA_VISIBLE_DEVICES=1 python train_xxx.py --device cuda:0`（VISIBLE内の相対index）
- **ハーネス**: 単一ハーネス方式。SHARED_DIR: `/home/rlrk/Claudecode/shared/`（cuda:1優先）
- **複数GPU使用時**: 個別にハーネスインスタンスを起動（SHARED_DIR + --device で分離）

## Key Files (SSOT)

| File | Purpose |
|------|---------|
| `thread_isaac_lab/configs/task_config.py` | 全数値パラメータ |
| `thread-vault/04-Specs/SOMA.md` | 目標定義・Phase進捗・実装マッピング |
| `GOALS.md` | pointer + goal_evidence 契約 stub（実体 = SOMA.md / 地図 / LEDGER） |
| `HARNESS_STATE.md` | 自動生成サマリ（手動編集禁止） |
| `${SHARED_DIR}/CONSENSUS.md` | B+C verdict統合判定（自動生成） |
| `thread-vault/07-Design/RL-Routing-Design.md` | RL Routing統合設計（工程・スキル・DAPG・DR。旧 `thread_isaac_lab/docs/DAPG_DESIGN.md` は本書 §5-9 へ consolidated 済） |
| `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` | 成否 SSOT |
| `data/test_{run_id}/RUN_METRICS.json` | run単位メトリクス |

## Vault Operation Protocol

See: `thread-vault/02-Workflow/VaultProtocol.md` (Karpathy LLM Wiki pattern)
Session start: Read `index.md` → `handoff.md` → `tail -20 log.md` (mandatory) + grep correction entries from `log.md` (Rule V8).
Auto-log decisions/corrections/discoveries proactively (Rule V6).
Pre-task prior-art/no-repeat guard (V7/V10) + current-state freshness guard (V9): §運用4 参照。

## Vault Paths

- **thread-vault:** `~/IsaacLab/thread_isaac_lab/thread-vault/`
- **sublimate-vault:** `~/sublimate-vault/`

## Output Format

| 区分 | 主張 | 根拠（出典） |
|------|------|-------------|
| 事実 | ... | ファイル:行番号 |
| 推測 | ... | なぜ推測か + 検証方法 |
