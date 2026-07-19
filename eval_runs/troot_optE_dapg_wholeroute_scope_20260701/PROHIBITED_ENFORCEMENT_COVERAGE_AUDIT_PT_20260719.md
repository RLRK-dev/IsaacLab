# PROHIBITED ENFORCEMENT COVERAGE AUDIT — 禁止事項 × 執行機構カバレッジ監査

- 作成: pane w2:pT（無名 pane、session `2388e4fc`、Rs 直命 chunk）、2026-07-19 11:27 JST
- 経緯: Rs「特に禁止事項守られないことがあり障害となっている」→ 提案「執行カバレッジ監査」→ Rs 承認「A B」の B（2026-07-19）
- 目的: `.claude/rules/prohibited.md` 全 25 項 + CLAUDE.md ハードストップ 13 項を**実在する執行機構と突き合わせ**、(1) 機械で守られている (2) 機械化可能なのに未実装 (3) 原理的に判断依存、に分類し、機械化提案 G-1〜G-11 を優先度付けする。
- ⛔ **本書は監査のみ。G 提案の実装は全て Rs 承認後**（多くが hooks/settings/validate 変更 = L3）。
- 方法: 全主張 on-disk 実測（file:line）。「無い」主張は検索コマンド+空出力根拠。**5体 CC Debate 1 round 済み**（CRITICAL 1 / HIGH 5 級の指摘を全 ACCEPT・本版に反映。記録 = `harness-vault/verification-log/` task `task-prohibited-enforcement-audit-20260719`）。
- ⚠ **鮮度注意（debate 指摘）**: 本表は audit 時点（HEAD 世代 `e32c75c3a4`、hooks/settings 2026-07-19 実測）の snapshot。**依拠する前に §1 を現物（`~/.claude/settings.json` / `scripts/validate.sh` / hooks）と再照合すること**。hooks は進化する。

## 分類記号

| 記号 | 意味 | 強さ |
|---|---|---|
| **F** | fail-closed 機械ゲート（実行前 block / FAIL 停止） | 最強 |
| **F(要呼出)** | script は fail-closed だが**呼び出しが CC 規律**（hook 未配線） | 中（呼出忘れは守られない） |
| **C** | commit 時機械ゲート（pre-commit → validate.sh --staged-only） | 強（commit まで検出遅延） |
| **D** | 機械検出・事後（PostToolUse annotate/log。防止でなく検出） | 中 |
| **P** | 手続きゲート（skill/checklist/gate echo = LLM 注意依存） | 弱 |
| **J** | 判断依存（機械化不能。debate・アンカー式検証・Rs 荷重試験の領域） | — |

## §1 執行機構インベントリ（2026-07-19 実測。配線 = settings.json で確認済みのもののみ「配線済」と記す）

| 機構 | 種別 | 実体 (file:line) | 発火点 / 配線 |
|---|---|---|---|
| preflight P1-P11 | **F(要呼出)** | `harness/scripts/preflight_check.sh:33-260`（FAIL→exit 1、§運用1b で作業開始禁止） | **hook 未配線**（SessionStart hooks 全読で preflight 参照 0 件 = debate CC2/CC5 実測）。呼出 = CC 規律 → G-10 |
| pre-commit → validate.sh | **C**(層別) | `.git/hooks/pre-commit` → `scripts/validate.sh --staged-only`（FAIL→exit 1、`--no-verify` で迂回可） | git commit。**commit 時実効は層別**: L6/L8 常時全走査・L1-L3 混在・**L4 条件付き**（staged に vault 面がある時のみ）・**L5/L7 は commit 時 無条件 SKIP**（repo-state 検査。`check_nest_freshness.sh:37-43` / `check_planning_consistency.sh:48-52`）。full run は手動 `validate.sh`（hook/CI 未配線、`.github/workflows/` に validate 参照なし） |
| L8 制御方式ガード | **C** | `scripts/validations/check_control_method.sh:71` grep `(phys_jq\|joint_q\|qpos)\[..\]=`（ENVS_DIR=envs/ scope :38）、BASELINE 照合 :87-91、既知=WARN/新規=FAIL、移行時 baseline 行削除で再発 FAIL 化 :44 | git commit + 手動。staged フラグ非参照 = 常時全走査 |
| pattern_verifier（層3） | **D** | `~/.claude/hooks/pattern_verifier.py` — **PROTECTED_FILES :37-41（CLAUDE.md / prohibited.md / HARNESS_STATE.md / RUN_METRICS.json）+ check_rule1 :107-131**（Edit/Write + Bash sed/awk/echo リダイレクトも検出）/ BANNED :45-49（write_joint_position_to_sim・write_joint_state_to_sim・sudo reboot）/ 捏造 echo :52-58 / check_rule4 未 cat 編集 :172-199（**Edit のみ。Write 上書きは未検査 :175**、履歴 10 件窓、破損時 fail-open） | PostToolUse 全 tool（配線済 settings.json:93-102）。**検出+log は実証**（`~/logs/nemotron_verifier.jsonl` 本 session live-fire 確認）。**⚠ annotation の context 注入は未実証**（advisory・exit 0 常時 :224,251,281。本 session で CLAUDE.md 編集時に model 側へ可視 feedback なし = 少なくとも silent な場合あり） |
| BLOCKED_FOR_USER 書込 block | **F** | `~/.claude/hooks/check-blocked.sh:52` exit 2 = block（state.md に `^BLOCKED_FOR_USER:` 行がある時） | PreToolUse Write\|Edit\|MultiEdit\|NotebookEdit（配線済）。**Bash は無条件免除 :15-16**（§運用26「Bashで回避しない」は手続きのみ） |
| permissions deny/ask | —(空) | `~/.claude/settings.json:35-36` `"deny": []` / `"ask": []` — **両方未使用**。かつ **`"Bash(sudo:*)"` が allow 済み :20** | (PreToolUse 相当、実行前に止められる唯一の層) |
| post_edit_review | **D**(nudge) | `~/.claude/hooks/post_edit_review.sh:47-55` — env/reward/task_config/train ファイル編集時にチェックリスト注入（「影響範囲を列挙（ハードストップ条件）」「cat で再読」） | PostToolUse Edit/Write（配線済）。ハードストップ #5/#6 の機械 nudge |
| escalate_on_error | **死んだ自動化** | `~/.claude/hooks/escalate_on_error.py:16` が `~/Downloads/escalate.py` を指すが**実体不存在**（debate CC3 実測）+ 自動路 無効化 :165-166 | Stop（配線済だが実効なし）。ハードストップ #1/:32 に最近接の機構が死んでいる — 修理 or 撤去は Rs 判断 |
| train_alert_check | D(弱) | `~/.claude/hooks/train_alert_check.sh` — `~/logs/*_alerts.jsonl` の HIGH/CRITICAL を転送 | PostToolUse（配線済）。:41 への関連は上流 monitor 内容次第（未監査） |
| kill_isaac_zombies | 衛生(注意) | `~/.claude/hooks/kill_isaac_zombies.sh:18-26` — **ELAPSED>60s のみで `poc_\|test_clip` python を kill -9**（zombie 判定は log 表示のみ） | PostToolUse Bash。⚠ 生きた正当プロセスも 60s 超で kill され得る（G-2 設計時に要考慮） |
| Video Gate / 独立検証 / ZCHECK | F/C | `harness/scripts/enforce_video_gate.sh`（monitor_code_b.sh から呼出）+ `thread_isaac_lab/scripts/verify_raw_evidence.py` + `INIT_CODE_C.md`; ZCHECK = `test_newton_clip_routing.py`（PASS→FAIL 自動降格、正規 run コマンドに内在） | run 判定時（harness 稼働時） |
| V7/V9 guard scripts | **F(要呼出)** | `scripts/check_thread_vault_prior_art.sh` / `scripts/audit_thread_vault_current_state.sh` | 実験/state 編集前。呼出 = CC 規律（backstop = [DEFER-RECON]） |
| DDRG / [DEFER-RECON] | **P**(構造) | `00-DESIGN-STATUS-LEDGER.md` §DDR（:75-）+ `RECURRENCE_PREVENTION_DDRG_SPEC_RSTECHLEAD_20260718.md` — chunk 前提を register と構造照合（grep 単独に依存しない backstop） | 全 chunk の scoping 時（手続き） |
| anchor gate echo | P | `.claude/hooks/handoff_grounding_gate.sh`（§0 invariants + LEDGER digest 注入。exit 0 常時 = salience のみ） | SessionStart×4 + UserPromptSubmit（project settings 配線済） |
| rule-check / verification-subagent / pre-check / reward-design / production-launch-gate | P | `.claude/skills/*/SKILL.md` | 該当タスク時（LLM 実行 = 確率的注意） |

## §2 表A — prohibited.md 全 25 項（行 = 現行行番号 :17-:41 連番、25 項実測一致）

| 行 | 禁止事項（要旨） | 分類 | 現行機構 / 根拠 | ギャップ→提案 |
|---|---|---|---|---|
| :17 | CLAUDE.md 変更は rs 指示時のみ | **D** | **pattern_verifier PROTECTED_FILES :37-41 + check_rule1 :107-131 が Edit/Write/Bash-リダイレクトを検出**（初版で「無し」と誤記 → debate CC3 が CRITICAL 指摘・訂正。なお本日の Rs 承認済 CLAUDE.md 編集でも silent 発火 = log のみ確認） | G-6: **D→F 昇格**（保護パス PreToolUse ask 化） |
| :18 | 指示された方針・手法を独自判断で変更しない | **J** | 意味判断。debate/[VERIFY] | — |
| :19 | ⭐substrate 非依存不変前提（IK-only / kinematic トリック禁止 / 制御方式変更 Rs 承認） | **C**(部分) | L8（§1）。ただし (a) commit 時発火 (b) envs/ の *.py 限定 (c) mocap/eq テレポート等の別形は未パターン化 | G-3: 編集時 mirror + 別形追補（⚠ p4/p5 の §0 是正 arc `ARM_CONTROL_REMEDIATION_D_*` と同一面 — 実装は当該 arc と要調整） |
| :20 | 〔API 名は PhysX 実装形という注記〕 | — | 規則でなく注記行 | — |
| :21 | IK = DifferentialIKController のみ / JT IK 廃止 | **P** | JT-IK 再導入検出なし | G-8 (低優先) |
| :22 | `write_joint_position_to_sim` 全面禁止 | **D** | pattern_verifier :46（事後 annotate のみ）。**実測: 実呼出 14 件現存**（`test_grip_diag.py`×6 / `poc_dual_arm_vectorized.py`×8）+ fixture 文字列 7 件（`test_nemotron_verifier_phase2*.py`）+ 注釈 2 件 — commit ゲートなし | G-4: baseline 方式 commit 層へ昇格 |
| :23 | `write_joint_state_to_sim` 制御ループ中禁止（replay/reset 例外） | **D** | pattern_verifier :47。**例外の実態（debate CC5 実測）: replay_for_video.py の呼出は現在コメントアウト（:266,:272 PENDING rs）・envs/ 内の唯一の呼出は `hook_hanging_env.py:642` = `reset_robot_to_default` 内（許可された reset-init）** → 「機械判別不能」は初版の誤り（撤回）。path/関数名 allowlist + baseline で C 化可能 | G-4 に統合（:22 と同一チェックで cover） |
| :24 | finger 制御 = `set_joint_velocity_target` のみ | **P** | 検出パターンなし | G-8 (低優先、PhysX 縮退中) |
| :25 | arm 制御 = `set_joint_position_target` + `write_data_to_sim` のみ | **P** | 同上 | G-8 (低優先) |
| :26 | 制御方式の変更は rs 承認なし不可 | **J** | 「方式変更」は意味判断（最頻出形のみ L8 が機械化済） | — |
| :27 | 到達性は task_config で解決 / kinematic attachment・trick 禁止〔全 substrate〕 | **C**(部分) | :19 と同じ L8。attachment 系（weld/eq の目的外使用）未パターン化（認可例外 = clip-retention pin） | G-3 に含む |
| :28 | 対処療法禁止 | **J** | 思考過程。debate + アンカー式検証 | — |
| :29 | 解法比較の前に原因仮説を裏付けよ | **J** | 同上 | — |
| :30 | 確証バイアス禁止 | **J** | 同上（同日実例: factsync E1/E5 を事前 debate が捕捉） | — |
| :31 | 同意バイアス禁止 | **J** | 同上 | — |
| :32 | 複雑化エスカレーション禁止（3 回で方針を疑う） | **J**(半) | 「同一」判定が意味依存。⚠ 最近接機構 escalate_on_error は**死んでいる**（§1） | — (修理/撤去は Rs 判断) |
| :33 | サンクコスト禁止 | **J** | 思考過程 | — |
| :34 | 抽象化したら具体に戻せ | **J** | 思考過程 | — |
| :35 | 一般解を THREAD 条件で検証せよ | **J** | 思考過程（[VERIFY] の THREAD 固有条件が手続き対応） | — |
| :36 | `sudo reboot` 自動実行禁止 | **D** | pattern_verifier :48 = **実行後**検出のみ。**さらに `"Bash(sudo:*)"` が allow 済（settings.json:20）+ deny 空(:35) = 実行前は素通し** | **G-1: deny 1 行（最小工数・FP ゼロ・素通し現状ゆえ必須級）** |
| :37 | 訓練プロセス kill / ハーネス停止は rs 承認必須 | **なし** | PreToolUse Bash ガード不在（§1 配線一覧に Bash matcher なし）。kill_isaac_zombies は別目的（かつ 60s 超プロセスを無差別 kill する注意点あり） | **G-2: kill/stop 系 permissions.ask 化** |
| :38 | ルール引用は原文 cat 確認後 | **P** | rule-check Tier0 が cat 証拠要求（手続き） | — |
| :39 | timeouts 汚染禁止（time_outs には真の timeout のみ） | **なし** | validate 全層・hook に `time_outs` パターン 0 件（grep 実測・debate 再現）。**事故実績最大（value_loss 105 倍）+ 現物の生きたバグあり**: `newton_grip_env.py:1258,:1441` が排除なし `int(timeout)`（既知 latent finding 20260718 文書化済・未修正） | **G-5: 極性認識ガード（下記・再設計版）** |
| :40 | PhysX/Newton 環境規約の混同禁止 | **P** | 再発実績 2 回。機械化可能な切片 = import 境界のみ（quat 規約等は不能） | G-7: import 境界チェック |
| :41 | 崩壊 checkpoint からの resume 禁止 | **なし** | resume 経路に崩壊 marker 照合なし。**RUN_METRICS.json 552 件に value_loss/collapse フィールド 0 件（debate 実測）= 契約が先** | G-9: marker 契約設計チケット |

**集計（debate 訂正後・24 規則行 + 注記 1 = 25）**: F=0 / C=2(部分) / **D=4**（:17 :22 :23 :36）/ **P=5**（:21 :24 :25 :38 :40）/ **J=10** / 機構なし=3（:37 :39 :41）。
**要旨: 実行前に止められる層（deny/ask）が完全に空。事故実績最大の :39 と承認必須の :37 が機構なし、:36 は allow で素通し。**

## §3 表B — CLAUDE.md ハードストップ 13 項（表A 重複は参照のみ）

| # | 項目（要旨） | 分類 | 対応 |
|---|---|---|---|
| 1 | 同一エラー修正 3 回失敗 | J(半) | = :32（escalate_on_error は死亡 — §1） |
| 2 | 禁止 API/trick を「今回だけ」 | D/C | = :22/:19 |
| 3 | パッチの連鎖 | J | debate |
| 4 | 「とりあえず動く」根本原因不明 | J | debate |
| 5 | 影響範囲を即答できない | **J+D(nudge)** | **post_edit_review.sh:47-55 が該当ファイル編集時に「影響範囲を列挙（ハードストップ条件）」を機械注入**（初版 J 単独は不完全 → debate CC3 訂正） |
| 6 | 未 cat ファイル編集 | **D**(部分) | pattern_verifier check_rule4 :172-199。**Edit のみ・Write 上書き未検査 :175**・履歴 10 件窓・fail-open | G-11 (小) |
| 7 | 根本原因回避のパラメータ調整 | J | debate |
| 8 | PhysX 規約⇔Newton 適用 | P | = :40（G-7） |
| 9 | time_outs に terminal state | なし | = :39（G-5） |
| 10 | 指示外の新ファイル/Phase/CLI 追加 | P(半) | rule-check Tier2。新ファイル PreToolUse 通知は FP 過大（scratchpad/eval_runs 常用）で非推奨 |
| 11 | 高コスト実験の根拠なし launch | P | production-launch-gate skill + HIGH-COST-GATE |
| 12 | 別方針の NO_ACTION/FAIL を GO 根拠に流用 | J | debate |
| 13 | 引用先に根拠が存在しない | P | claim-check Tier4 |

## §4 ギャップ → 機械化提案（優先度順。**全て Rs 承認待ち・本書では実装しない**）

| ID | 提案 | 対象 | 形 | 工数 | FP | 根拠 |
|---|---|---|---|---|---|---|
| **G-1** | `permissions.deny` に `Bash(sudo reboot*)` 追加（deny/ask 構文は CLI 実体から確認済 = debate CC4。**現状は `sudo:*` allow で素通し**） | :36 | **F** | 数分 | ゼロ | 実行前に止める唯一の層が未使用 |
| **G-10** | **preflight の自動配線**: SessionStart hook で preflight 実行 or 実行 marker の鮮度チェック→未実行なら警告注入 | §運用1b | **F 化** | 小 | 低 | 現状 hook 参照 0 件 = 呼出忘れは構造的に守られない（debate CC2/CC5） |
| **G-2** | 訓練 kill/ハーネス停止系を `permissions.ask` 化（`pkill -f train`・`systemctl stop/disable *monitor*`・`tmux kill-*` 等）。⚠ ask の非対話 session 挙動は導入前に smoke-test（debate CC4 注意） | :37 | **F**(ask) | 小 | 中→ask で吸収 | rs 承認必須ルールに機構ゼロ |
| **G-5** | **timeouts 純度ガード（極性認識・再設計版）**: env コードの `timeouts... =` 導出行を抽出し、**排除結合（`and not (explosion\|drop\|success)` 等）を欠く bare 代入を FAIL/WARN**（初版の「汚染語を含む行を flag」は逆向きで廃案 — 正しいコードが語を含み、実バグは語を欠く。debate CC4 決定打）。fixture (`cascade_c_dataset_gen.py`) は allowlist。**導入即日で既知バグ `newton_grip_env.py:1258,:1441` を検出できる**（`LATENT_FINDING_GRIPENV_TIMEOUT_PURITY_RSTECHLEAD_20260718.md` の未修正案件） | :39/H9 | **C** | 中 | 低-中 | 事故実績最大 + 生きた検出対象が現存 |
| **G-3** | L8 の編集時 mirror: pattern_verifier に `phys_jq[..]=` 系を追加。**必須条件: ENVS_DIR 相当の path scope**（無 scope だと envs/ 外の正当 7 件 — `test_routeexec_writesite.py` 等 — を常時誤検知 = debate CC4）。⚠ `ARM_CONTROL_REMEDIATION_D` arc と同一面 → 実装は p4/p5 と調整 | :19/:27 | D 強化 | 小 | 中（scope 必須） | 検出を commit 時→編集時へ前倒し |
| **G-4** | PhysX 禁止 API の commit 層昇格（:22+:23 統合 1 チェック、baseline 方式: 既知 14 件=WARN・新規=FAIL。allowlist = verifier fixture・`replay_for_video.py`・reset-init 関数） | :22 :23 | **C** | 小 | 低 | 全面禁止 API が annotate 止まり + 未 flag 14 件 |
| **G-6** | 保護パス（CLAUDE.md/prohibited.md/skills workflow 部）編集の PreToolUse ask 化 = 既存 D（PROTECTED_FILES）の F 昇格 | :17 | **F** | 小 | 低 | ルールファイル無承認編集の構造的防止 |
| **G-7** | PhysX/Newton import 境界チェック（`newton_*.py` ↔ isaaclab/physx 相互 import で WARN）。**実測: 現状違反 0・allowlist は約 6 件で足りる**（assets_cfg / flexible_cable_cfg / dual_arm_flex_env_cfg / hook_hanging_env + train/eval = debate CC4 実測） | :40/H8 | C(WARN) | 小-中 | 低（実測済） | 再発 2 回の混同の最頻入口 |
| **G-11** | check_rule4 を Write（既存ファイル上書き）にも拡張 + fail-open の明示 log | H6 | D 強化 | 小 | 低 | Write 経由の未 cat 上書きが盲点（:175） |
| **G-9** | 崩壊 checkpoint resume ガード — **前提: RUN_METRICS 契約に collapse marker を追加する設計が先**（現行 552 件に該当フィールド 0 = debate CC4 実測）。まず契約設計チケット | :41 | **F**(将来) | 大 | — | 事故実績 1 回、grep では作れない |
| **G-8** | PhysX 制御 API 誤用 grep（:21/:24/:25） | 同左 | C(WARN) | 中 | 中 | 低優先: PhysX track 削除進行中（母集団縮退） |

推奨順: **G-1 → G-10 → G-2 → G-5**（事故実績×工数比の最上位群）→ G-3 → G-4 → G-6 → G-7 → G-11 → G-9 → G-8。
共通原則（L8 実証済）: **既知=baseline WARN / 新規=FAIL / 移行完了で baseline 行削除→再発 FAIL 化**。

## §5 限界と注意（正直な線引き）

- **J 項 10 個（思考過程系）は機械化しない**。担当 = §運用2 [VERIFY] debate + アンカー式検証 + Rs 荷重試験。同日実例 2 件: (1) CLAUDE.md factsync で事前 debate が CC1 誤読 2 件を [CHANGE] 前に捕捉 (2) 本監査自体も 1 round で CRITICAL 1 + HIGH 5 を捕捉・修正（初版の :17「機構なし」誤記は、まさに本書 §0 方法論の違反だった）。
- **D（PostToolUse）は防止でなく検出**、かつ **annotation の context 到達は未実証**（log 到達は実証済）。実行前に止められるのは deny/ask と PreToolUse block のみ — 現状 deny/ask は空。
- **「script 実在」≠「script 発火」**: preflight / V7 / V9 / full validate.sh は呼出が CC 規律（F(要呼出)）。commit 時の validate も層別に実効が異なる（§1）。CI backstop なし。
- **BLOCKED_FOR_USER block は Bash 免除**（check-blocked.sh:15-16）— 「Bash で回避しない」は手続き遵守に依存。
- scope 外だが隣接: RS71 §0 FOUNDATIONAL INVARIANTS（DUAL-ARM / 88mm / gripper LOCK 等）は prohibited.md の 25 項に含まれない並行規則面（gate echo + L3 自動昇格が担当）。CLAUDE.md DiffIK 節は :21-:27 の逐語重複（両面同期の維持コストは別議論）。escalate_on_error の死亡は修理 or 撤去を Rs 判断へ。

## §6 DoD 照合

1. prohibited.md 25 項（`grep -n "^- \*\*"` = :17-:41 連番 25 件）全行が表A に対応、対称差 ∅（:20 は注記と明示）。
2. ハードストップ 13 項（section bullet 13 件実測）全て表B に対応。
3. 「機構あり」= file:line 引用、「機構なし」= 検索空出力根拠（:39 の 0 件 grep は 2 者独立再現）。最重要 5 主張（PROTECTED_FILES / grip_env :1258,:1441 / sudo:* allow / replay コメントアウト / latent finding 実在）は landing 直前に CC1 が自己再導出。
4. 提案 G-1〜G-11 全てに形・工数・FP・根拠。実装ゼロ。
5. 5体 debate 1 round: 指摘全 ACCEPT 反映（REBUT 0）。集計は訂正後値（D4/P5/J10）。

## §7 実装記録 — G-1 / G-10 / G-2（2026-07-19 13:24 JST 着地、Rs 承認「A」= 本バンドル）

- **着地物**（backup = `settings.json.bak_20260719_132228_pre_{G1G2,G10}`、rollback 即可）:
  - G-1: `~/.claude/settings.json` **deny 16 entries**（reboot 意味論のみ: sudo/bare reboot・systemctl (soft-)reboot・shutdown -r・init 6・telinit 6。⚠ audit 原文 `Bash(sudo reboot*)` 1 個からの**拡張は実装時 5体 debate CC2 指摘による — Rs 追認待ち**、一言で rollback 可）
  - G-2: 同 file **ask 16 entries**（debate 採用: `Bash(kill:*)` は**意図的に不採用**〔isaac-sim-execution 必須手順・kill -0/-USR1 慣用と衝突、CC5〕/ systemctl **restart** 系を追加〔monitor restart = ハーネス停止相当、monitor_ssot.sh:1400 実例〕）
  - G-10: `.claude/hooks/preflight_gate.sh`（advisory・exit 0 常時・WARN 詳細注入・~1KB）+ project settings SessionStart ×4 matcher に配線。**「F 化」は過大表現と判明 → 正しくは「強制注入つき P」**（SessionStart は block 不能）
  - allow 配列は両 file とも **byte-identical**（緩和ゼロ、post-panel set-diff = ∅ 検証済）
- **Positive control（実弾）**: `sudo reboot --help` → **"Permission ... has been denied" = deny 発火・再起動不要で即 live** ✓ / ask 対象 `pkill -f 'z[z]z…'` → **prompt なしで実行**（rc=1 無害）
- **⭐ モード発見（本実装の最重要知見）**: user settings `defaultMode: "auto"` により session は don't-ask 系モード — CLI binary 実証（v2.1.215 strings）:「bypassPermissions auto-approves every tool call **(except explicit deny rules)**」「denied because Claude Code is running in don't ask mode」⇒ **ask 層は現行運用モードで silent auto-approve（inert）・deny のみ貫通**。系:
  - G-2 の実効分類は F(ask) でなく **「LANDED-inert-in-auto-mode」**（default モード pane でのみ prompt 発火）。§4 G-2 行の F(ask) 表記はこの条件付きで読むこと。
  - 逆に **G-1 deny は `--dangerously-skip-permissions` の自律 worker 経路（run_cc_agent.sh:146）にも効く**（bypass も deny は除外されない）— §7 以前の「自律経路は対象外」推定（CC3-F2）を上方修正。
- **既知の迂回限界**（naive/事故防止が目的、確信犯は防げない）: `bash -c "…"` / `python -c os.system` / パイプ先頭別コマンド（`ps|…|xargs kill` は kill 規則に非該当）。`Bash(bash *)` が allow 済みである事も標準的迂回路。
- **G-2 実効化の選択肢（Rs 裁定待ち）**: (i) 現状維持 = default モード pane 向け defense-in-depth（コストゼロ） (ii) 最鋭利パターンのみ deny 昇格（例 `Bash(pkill -f train:*)` — CC は常に不可・必要時は Rs が `!` で自走） (iii) pane を default モード運用に変更（全操作 prompt 化）。
- **随伴 findings（別裁定推奨）**: isaac-sim-execution SKILL.md:214-238 の hygiene-kill が `isaac` substring で**稼働中 train プロセスを誤 kill し得る**（env_isaaclab6 python パス一致、CC5 発見 — skill の grep 修正が根治）/ 過去実事故 = `05-Thinking/Incident-20260405-Unauthorized-Kill.md`（CC が PID 146232 を無承認 kill = G-2 は再発防止）/ implementation-rules SKILL.md の reboot 文言（「approved 後実行」）は deny と不整合 → 「提案のみ・実行は Rs」へ改訂推奨 / `pkill:*` の allow/ask 重複整理・poweroff/halt への deny 拡張・settings.local.json 残置 allow 整理 = 任意。
