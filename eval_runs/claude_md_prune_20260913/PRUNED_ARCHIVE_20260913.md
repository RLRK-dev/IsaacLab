# CLAUDE.md pruned-content archive (2026-09-13)

**作成:** 2026-09-13 06:55:44 JST / **repo HEAD at prune:** `6e5926039b` / **branch:** rlrk/optE-s2-substrate-swap
**指示:** Rs 2026-09-13「claude.mdを最適化したい。不要なものを削除」→ 候補表に対し Rs が「A + B 全部」を選択。
**結果:** 45,204 B / 354 行 → 44,033 B / 315 行（**−1,171 B, −2.5%**）。
⚠ **当初案は −6,053 B（−13.4%）だったが、5 体の事前検証（BLOCKER 5 / SERIOUS 11）で「不要」と判断した内容の大半が実際には効いていると判明し、復元した。**下記 §A/§B は**実際に移設・削除した分のみ**を記録する。
**復元:** `git show <prune-commit>^:CLAUDE.md` でも全文復元できる。
**置き場所:** 先例の `thread-vault/02-Workflow/CLAUDE-md-pruned-archive-2026-07-12.md` と並べたいが `02-Workflow/` は **CC = Read-only**（`Vault Write Permissions.md:22`）。Rs が移すのは随時可。
**⚠ 対象外:** CLAUDE.md の未コミット差分（`:82-86` env7 / env_isaacsim6、他 pane の 2026-09-10 作業）。draft でも **5/5 byte 一致**で保持。

---

## §A2 — 旧ヘッダ + Global rules summary 節（削除）

理由: `~/.claude/CLAUDE.md`（毎セッション自動ロード、本セッションでも注入を実証）の要約。旧 `:5-6`（本ファイルが global 既定を定義）と旧 `:12`（global は別ファイル）が矛盾していた。
⚠ 併せて **§運用1 に `cat ~/.claude/CLAUDE.md` を追加**した — 旧 §運用1 は compact 後の再読込を 2 本しか指定しておらず、要約を消すと compaction 経路で global 規則が手元から消えるため（検証 CH1-S6）。

```
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
```

## §A3 — 文中 H1 の版ヘッダ（移設）

削除ではなく**移設**: `harness/scripts/preflight_check.sh:42` が `grep -oP 'v\d+\.\d+\.\d+'` で CLAUDE.md の版を読む（検証 CH4-S1）。消すと P1 が PASS→WARN に落ち全 pane が継承するため、新ヘッダ 1 行目に `v26.09.13` として残した。

```
# CLAUDE.md v26.07.12
```

## §A1 — DiffIK 節: 制御API制約 7 bullets（1 行へ集約）

理由: 規範内容は `.claude/rules/prohibited.md`「⛔ 禁止事項」の制御 API 7 項（現 `:21-27`）と一致し、同 file も自動ロードされる。
⚠ **「逐語重複」は誤りだった**（検証 CH2-S1 / CH3-B1）: 次の 2 つは prohibited.md に**無く**、自動ロード面では CLAUDE.md が唯一の所在 —「（reset-init 例外 = 失効・cable は対象外）」「（arm reset 書込 0・サーボ目標のみ）」。**両方とも CLAUDE.md 本体に残した**（前者は制限を*狭める*側の但し書きで、失うと許可側だけが残る）。
⚠ 併せて、この行の**未解決の不整合**（本文は reset 直後の関節 seed を許可、括弧は同例外を失効と書く）を `§運用10` 事項として CLAUDE.md 本体に loud に明記した。CC は解消していない。係争 = `00-DESIGN-STATUS-LEDGER.md:60`。

```
**制御API制約（違反はrs承認なしに不可）:**
- **IK: DifferentialIKController のみ使用。JT IK（自前実装）は廃止済み**
- **`write_joint_position_to_sim` 全面禁止**（arm j0-j6 も finger j7/j8 も）
- **`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。例外: オフラインreplay（replay_for_video.py等、制御ループ外の事後可視化）は許可。reset直後の初期化（episode開始時1回）は「関節状態の seed に限り」許可（body 状態の直接書込は不可 — body は `eval_fk`/`mj_forward` で関節から従属させる）。⛔腕を姿勢へ書き込むことは不可 — 腕の開始姿勢は PD の実移動で到達する。ケーブルの reset 再 seed は対象外・現行のまま。〔根拠 = p5 banked charter `charter_v231.md:351`/`:352`/`:360`/`:361`（reset-init 例外 = 失効・cable は対象外）＋ `probe/pd1-arm-pd` で実装済（arm reset 書込 0・サーボ目標のみ）。Rs 承認 2026-07-26〕**
- **finger制御: `set_joint_velocity_target` のみ許可**（open/close両方。符号で方向指定）
- **arm制御: `set_joint_position_target` + `write_data_to_sim` のみ許可**
- **制御方式の変更はrs承認なしに行わない**
- **到達性・収束性の問題はtask_config.pyのパラメータ調整で解決。kinematic attachment、kinematic trick（物理無視のテレポート・強制配置等）禁止**
```

## §A4 — 破棄済みトラックの venv 不在メモ（削除）

理由: 直前行 `:80` が env6-VBD track を DISCARDED と宣言済み。かつ `harness/scripts/preflight_check.sh:173` が同じ venv を参照し **毎セッション P9 WARN として出力**するため、情報は preflight 面が運んでいる。

```
- **環境:** Newton VBD solver。⚠ 旧記載の `env_isaaclab6` venv は **on-disk に存在しない**（2026-08-03 実測・preflight P9 WARN）— 本 track は DISCARDED 済（上行）。PhysX環境とは完全に分離
```

## §B3 — NEST 運用: 仕様書 (LTM-1) に実在を確認した要約 bullet（圧縮）

理由: 下記のうち 8 項目は SSOT `thread-vault/00-Project-Management/operational-rule-LTM-1.md` に実在を確認（規範本体の行 = auto-absorb 禁止 `:221` / 復活は新 node_id `:215`,`:247` / §3.3 #6 `:185` / §9 `:571-575` / §5.2 `:416-441` / §2.1 `:76-88` / §2.3 `:123` / §0 `:52`）。
⚠ 検証で **SSOT が持たないと判明した 2 項は CLAUDE.md に残した** — 「session = CC instance、1 node に 1:1 binding」（LTM-1 §5.1 `:403-409` は「同一 node の異なる session は同時並行禁止」までで `1:1` の語は 0 hit）と「handoff **二系統**（独立）」（§4.2 `:276-300` は vault sidecar 系統のみ規定）。
⚠ `node ID format: T-{seq}-{sub}-...` は LTM-1 §1 `:66` が例 `T-08-1-3` を示すのみで書式テンプレートを持たないため、「§1 が SSOT」とは書かず注記付きにした。⚠ 版表記 `LTM-1 v1.1` は実ファイル `:8` の **v1.2** に訂正した。

```
**仕様書 (SSOT):** `thread-vault/00-Project-Management/operational-rule-LTM-1.md` (LTM-1 v1.1)
**Root node (tree):** T-PRODUCTION-LINE（生産ライン工程①〜⑧）/ **THREAD subtree root:** T-ROOT「5-clip cable routing を vision-based で成功させる — 目標は 100% へ定性的に再定義済（Rs 2026-06-23・SSOT = SOMA:16）」〔宣言修正 = Rs 逐語「直して」2026-08-08・裁定 custody = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md` §7〕
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
```

## §B4 — §運用31 memory 規則: 経緯 2 項（移設）

⚠ **CLAUDE.md からこの節へのポインタが在る。** 検証（CH2-S4 / NHA-S5）により、**hard limit 24,986 の導出（= 24.4K×1024、K は ×1024）・その commit pin `6db8eed757` の `:18155`・成長率の区間（+1,860 chars / 13.9 日）・「規則をここに置く理由」の文は CLAUDE.md 本体に残した**（いずれも commit `f98aa82425`「Make the rule state the number the line it cites states」が drift 防止のため意図的に追加したもの）。本節へ移したのは下記のうち **2026-08-04 全面凍結の解除経緯**と**「行番号は "どの物の中の位置か" を連れて初めて恒久になる」の全文**、および **「過去 96.1% まで達し圧縮で戻した実績」**。

```
31. **memory ディレクトリの書き込み規則（Rs 裁定 2026-08-05）:** 対象 = `~/.claude/projects/-home-rlrk-IsaacLab/memory/`（全 pane 共有・⛔ **git 管理外＝削除が見えない**）。
    - **topic file（`feedback-*` / `reference-*` / `project-*` / per-pane `handoff_cc_*`）= 解放。** 単独所有・追記型・容量上限なしゆえ通常どおり書いてよい
    - **`MEMORY.md`（索引）= 成長条件つき。** hard limit = **24,986 chars**（= 24.4K×1024 = 24,985.6 の切り上げ。⚠ K は **×1024**、`LEDGER:18155` の決着値と同一。これを越えると索引が読めない）。**90%（≈22,487 chars）を超えたら coordinated 圧縮を起票**する。⛔ **単独で圧縮しない**（他 pane の行の要約を含むため。file 冒頭の同旨記載が SSOT）。⚠ 90% 未満なら hook が「17.1K まで圧縮せよ」と言っても**従わない**（17,510 は hook の目標であって要件ではない）
    - **`handoff.md` = SHARED last-writer。** 自分の節のみ Edit で狙い撃ち。⛔ **全書き換え禁止**（他 pane の節を消す）
    - **判断軸は水準でなく成長**（実測 **+1,860 chars / 13.9 日 ≈ +134/日** = 07-21 17:24 18,549 → 08-04 14:51 20,409。⚠ 区間を書くこと — 日数の丸めで ±1 動く）。過去 96.1% まで達し圧縮で戻した実績あり ⇒ 全面停止でなく閾値運用
    - ⛔ **2026-08-04 15:52 からの全面凍結は本裁定で解除**（旧根拠 = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P18_CLAMP_COURT_EVIDENCE_LEDGER_20260727.md` **@ commit `6db8eed757`** の `:19706` §700(e) / `:19782` §703(b) — ⚠ **commit を添えるのが本体**。同 file は追記で伸び続けるので、commit 無しの行番号は上への挿入で静かに外れる。§番号も台帳側で振り直せる**指し手**であって物ではない。⇒ ⭐ **行番号は「どの物の中の位置か」を連れて初めて恒久になる**）。⭐ **規則をここに置く理由 = 凍結は台帳にしか無く、新 session から見えず、守れなかった**（見えない規則は予防でなく確定した違反になる）
```

## §B5 — スキル参照ガイドの対応表（Newton 5 行を除いて削除）

理由: skill の一覧と説明は harness が毎セッション自動注入する（on-disk 33 / 注入 28）。
⚠ **検証（CH1-M1 / CH2-BLOCKER2 / NHA-S4）で削除根拠の一部が偽と判明**: `newton-urdf-setup` `newton-cable-design` `newton-ik-design` `newton-dual-solver` `newton-validation` の 5 件のみ SKILL.md frontmatter に `disable-model-invocation: true` を持ち、**自動注入されない**。よってこの 5 行（「いつ使う」列つき）は CLAUDE.md 本体に表として残した。表が名指していた skill は 17 件（残り 12 件分をここへ移設）。強制ゲート 3 項目は本体に逐語保持。

```
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
```

## §B2 — Pane Message Routing Protocol: OPS-SUP 内部 triage 3 項（移設）

⚠ **CLAUDE.md からこの節へのポインタが在る。**
⚠ **当初案は 18 項中 10 項を移設する予定だったが、検証で分類が誤りと判明し撤回した**（CH1-B1/B2/S1/S2/S3・NHA-BLOCKER2）。`:340`（readback）`:341`（OPS-SUP の解釈を Rs 裁定として提示するな）`:346`（actionable message の必須欄）`:350`（遅延を理由に gate を迂回するな）`:353`（RETURNED 中は実装・run・push・status/gate 反転を fail-closed）は **OPS-SUP 内部手順ではなく全 pane を拘束する**。**15 項を英語原文のまま CLAUDE.md に残した。**
移したのは下記 3 項のみ（OPS-SUP が受信時に行う triage 手続き）。原文は commit `06705484cb` が「custody, not authorship」として bank したもので、CC は文言を書き換えていない。節の実質的な改訂は owner（OPS-SUP）と Rs の領分。

```
- Check each message for ambiguity in role/authority, scope, status, version/SHA, evidence basis, timestamps, and supersession.
- If ambiguity or contradiction is detected, return the message to its source pane with the unclear text, missing evidence, required fixes, and resubmission condition. Do not silently normalize it.
- Before forwarding, compare pane role, node, SSOT, owner, gate, and authority scope. Conflicts between `T-ROOT-RS-TECH-LEAD`, `T-ROOT-RS-TECH-LEAD2`, and `pX:SKILL-DESIGN` must be surfaced and held for the proper authority.
```

---

## 削除ではない訂正（本 prune で併せて実施）

| 箇所 | 旧 | 新 | 根拠 |
|---|---|---|---|
| `:108` L3 昇格 path | `hooks/` 直下に `statusline.sh` `ctx_thresholds.sh` | `lib/ctx_thresholds.sh` + `~/.claude/statusline.sh` | 実測: `~/.claude/hooks/statusline.sh` は**不在**、`~/.claude/statusline.sh` が実体（`settings.json` の statusLine が指す）。旧記載では L3 判定が実ファイルに当たらなかった |
| `:94` 見出し | `## 📊 階層ゲート運用 (L判定)…` | `## 📊 §0 階層ゲート運用 (L判定)…` | `§0` を本節に束縛していたのは削除した `:19` だけ。外部依存 = `.claude/skills/rule-check/SKILL.md:89,:95,:97` / `operational-rule-LTM-1.md:571` |
| `:134` | LTM-1 v1.1 | LTM-1 **v1.2** | 実ファイル `:8` |
| `:74` robot cfg 行 | 注記なし | 先頭に「以下は PhysX 実機設定（prohibited.md に無い・本ファイル固有）」 | 検証 CH3-MINOR2: 旧草案の「substrate 差分のみ」という語と噛み合わず、次に剪定する者が重複と誤読し得たため、内容はそのままで性格を明記 |
| §運用1 | 再読込 2 本 | 3 本（global を追加） | 検証 CH1-S6 |


**書き換えた 3 行の原文（逐語）:**

```
- robot cfg: FRANKA_PANDA_HIGH_PD_CFG ベース（disable_gravity=True（HIGH_PD_CFG準拠）、hand actuatorのみ速度制御に上書き）
## 📊 階層ゲート運用 (L判定) — THREAD project 拡張
- `~/.claude/hooks/*` の **logic 部分** (`auto_handoff.sh`、`statusline.sh`、`context_watchdog.sh`、`ctx_thresholds.sh`)
```

## ⚠ 行番号 pin への影響（本 prune の副作用）

CLAUDE.md の行番号は 2026-09-13 に移動した。repo + memory に `CLAUDE.md:<N>` 形式の pin が **770 件 / 80 file** 存在し、うち現行有効と確認されたものは本 prune で指し先が変わる。主なもの:

| 旧 | 内容 | 被引用 | 新 |
|---|---|---|---|
| `:72` | kinematic 認可例外（clip-retention pin）の bracket | 127 件 (eval_runs) + `LEDGER:38`,`:129`, `T-ROOT-Kinematic-Pin-…/state.md:97` | `:49` 付近 |
| `:46` | 新ファイル作成のハードストップ | 83 件 | `:30` 付近 |
| `:49` | 「引用先に根拠が無い」ハードストップ | 41 件 | `:33` 付近 |
| `:67` | `write_joint_state_to_sim` の offline-replay 例外 | 19 件 | 1 行へ集約（→ `prohibited.md:23` を推奨 pin 先とする） |
| `:271` | Fingertip Z-Check Gate（`LEDGER:60` が未決 Rs 判断として pin） | — | `:227` 付近 |

⇒ **`CLAUDE.md:<N>` は恒久 address ではない。**以後は節見出し等の内容語で引くこと（本 project が既に持つ教訓 =「行番号は "どの物の中の位置か" を連れて初めて恒久になる」）。
