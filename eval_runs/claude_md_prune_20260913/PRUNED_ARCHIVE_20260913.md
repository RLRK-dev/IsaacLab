# CLAUDE.md pruned-content archive (2026-09-13)

**更新:** 2026-09-13 07:21:04 JST / **branch:** rlrk/optE-s2-substrate-swap
**指示:** Rs 2026-09-13「claude.mdを最適化したい。不要なものを削除」→ 候補表に対し Rs が「A + B 全部」を選択 → 検証後の版に Rs が「commit する」。
**最終結果（commit blob 基準）:** 44,048 B / 350 行 → **43,231 B / 321 行（−817 B, −1.9%）**。作業ツリー基準（他 pane の未コミット行を含む）では 45,204 B / 354 行 → 44,387 B / 325 行。
**復元:** 本 file のほか `git show 2995cad44e~1:CLAUDE.md` で prune 前の全文を復元できる。
**置き場所:** `02-Workflow/` は CC = Read-only（`Vault Write Permissions.md:22`）ゆえ先例 `CLAUDE-md-pruned-archive-2026-07-12.md` の隣に置けない。Rs が移すのは随時可。
**対象外:** 他 pane の未コミット行（Newton 節の env7 / env_isaacsim6、2026-09-10）。どちらの commit にも含めていない（HEAD 基準で自分の変更だけを index に載せた）。

## この prune の経緯（2 commit）

1. **`2995cad44e`** — 5 体の事前検証（BLOCKER 5 / SERIOUS 11）を反映した版を commit。−1,171 B。
2. **本 commit（follow-up）** — commit 後の独立検証 2 体が、**反映のために新しく書いた文言**に BLOCKER 3 件を見つけた。**規則の節を圧縮して書き直した 4 節（DiffIK / routing / NEST / §31）すべてで、規則が失われるか意味が反転していた**ため、4 節を元の原文（byte 一致）に戻し、実測で確かめた訂正だけを残した。−817 B。

⭐ **教訓:** 安全だったのは「自動ロード済みの逐語重複の削除」「実測で誤りの事実の訂正」「harness 注入済み skill の表行の削除」だけ。**規則文を要約・言い換えた箇所は、5 体検証を通った後でも毎回壊れた。**

---

## 最終的に削除・移設したもの

### §A2 — 旧ヘッダ + Global rules summary 節（削除）

理由: `~/.claude/CLAUDE.md`（毎セッション自動ロード）の要約。旧 `:5-6`（本ファイルが global 既定を定義）と旧 `:12`（global は別ファイル）が矛盾していた。
併せて **§運用1 の compact 後再読込に `~/.claude/CLAUDE.md` `~/.claude/l-gate.md` `~/.claude/operational-know-how.md` `~/IsaacLab/AGENTS.md` を追加**した — `cat` は `@` import を展開しない（global `:68` `@l-gate.md` / `:70` `@operational-know-how.md`）ため、要約を消すと compaction 経路で L 判定の汎用枠組みが手元から消える。

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

### §A3 — 文中 H1 の版ヘッダ（題名行へ移設）

`harness/scripts/preflight_check.sh:42` が `grep -oP 'v\d+\.\d+\.\d+'` で版を読む。消すと P1 が PASS→WARN。新題名行に `v26.09.13` として残した（commit 後の preflight 実走で P1 PASS を確認）。

```
# CLAUDE.md v26.07.12
```

### §A4 — 破棄済みトラックの venv 不在メモ（削除）

直前行が env6-VBD track を DISCARDED と宣言済み。`preflight_check.sh:173` が同 venv を参照し毎セッション P9 WARN を出すので、情報は preflight 面が運ぶ。

```
- **環境:** Newton VBD solver。⚠ 旧記載の `env_isaaclab6` venv は **on-disk に存在しない**（2026-08-03 実測・preflight P9 WARN）— 本 track は DISCARDED 済（上行）。PhysX環境とは完全に分離
```

### §B5 — スキル参照ガイドの対応表（12 行削除・Newton 5 行は残置）

skill の一覧と説明は harness が毎セッション自動注入する（`.claude/skills/` の 33 のうち 28）。**Newton 系 5 skill だけは SKILL.md frontmatter に `disable-model-invocation: true` を持ち注入されない**ので、その 5 行は「いつ使う」付きで残し、model から Skill tool で呼べないこと（SKILL.md を Read する / Rs に依頼する）を明記した。強制ゲート 3 項目は逐語保持。

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

## 削除ではない訂正

| 箇所 | 旧 | 新 | 根拠（実測） |
|---|---|---|---|
| L 判定節の見出し | `## 📊 階層ゲート運用 (L判定)…` | `## 📊 §0 階層ゲート運用 (L判定)…` | `§0` を本節に束縛していた唯一の行は §A2 で消えた旧 `:19`。外部依存 = `.claude/skills/rule-check/SKILL.md:89,95,97` / `operational-rule-LTM-1.md` §9 |
| L3 昇格 path | `hooks/` 直下に `statusline.sh` `ctx_thresholds.sh` | `lib/ctx_thresholds.sh` + `~/.claude/statusline.sh` | `~/.claude/hooks/statusline.sh` と `hooks/ctx_thresholds.sh` は不在。実体は `~/.claude/statusline.sh`（`settings.json:255`）と `hooks/lib/ctx_thresholds.sh` |
| NEST 仕様書の版 | LTM-1 v1.1 | LTM-1 v1.2 | `operational-rule-LTM-1.md:1`,`:8` |
| §運用1 | 再読込 2 本 | global 3 本 + CLAUDE.md + AGENTS.md + prohibited.md | `cat` は `@` import を展開しない |

**書き換えた行の原文（逐語）:**

```
## 📊 階層ゲート運用 (L判定) — THREAD project 拡張
- `~/.claude/hooks/*` の **logic 部分** (`auto_handoff.sh`、`statusline.sh`、`context_watchdog.sh`、`ctx_thresholds.sh`)
**仕様書 (SSOT):** `thread-vault/00-Project-Management/operational-rule-LTM-1.md` (LTM-1 v1.1)
1. **Conversation compacted時: 以下を順に実行し再読み込みせよ**
   - `cat ~/IsaacLab/CLAUDE.md`
```

---

## `2995cad44e` で入れて本 commit で原文へ戻したもの（誤りの記録）

| 節 | `2995cad44e` の変更 | 何が壊れたか（事後検証・実測） |
|---|---|---|
| DiffIK 制御 API | 7 bullets を 1 行に要約し、「但し書き 2 つは本ファイルにしか無い」「🔺 未解決の不整合…係争は `00-DESIGN-STATUS-LEDGER.md:60` に生きている」を追加 | **偽の記述。** LEDGER:60 は「RESET 衝突 = pN 18:17 **解消**（reset 1 回 joint-seed 認可…旧『reset-init 例外失効』を refine）」、`charter_v231.md:474` は「Q3 RESET = **RESOLVED**」、commit `e391b10c3f`「Narrow the reset-init exception to the joint seed」。括弧は charter の**解決前**見出し `:360` への注釈で、矛盾ではなかった。要約で「seed に限り許可」の本文が消え、CLAUDE.md だけ読むと現行ルール（`prohibited.md:23` = 許可）と**逆**に読めた。さらに `.claude/` は gitignore（`.gitignore:101`、追跡 0 件）ゆえ、7 項目を git 管理下で自動ロードされる形で持つのは CLAUDE.md だけだった |
| Pane Message Routing Protocol | OPS-SUP 内部 triage 3 項を移設し、読み先ポインタと「owner（OPS-SUP）」の注記を追加 | 残した `AMBIGUITY DETECTED` / `RETURNED` と fail-closed の規則は、**状態に入る条件**を移設した 3 項（旧 `:337`/`:338`）にしか持っていなかった。「owner」は commit `06705484cb` の「Provenance is not established」と合わず根拠が無かった |
| NEST 運用 | 要約 bullet を圧縮 | **「本 rule 改訂は CLAUDE.md 変更扱い」が消えた。** LTM-1 §9 に同語は無く（0 hit）、CC は `00-Project-Management/` に Update 権限を持つ（`Vault Write Permissions.md:28`）ため、LTM-1 改訂が `prohibited.md:17`「CLAUDE.md の変更は rs 指示時のみ」の対象から外れていた |
| §運用31 | 導出の一部と経緯を移設 | 「⛔ 2026-08-04 15:52 からの全面凍結は本裁定で**解除**」の明示と「file 冒頭の同旨記載が SSOT」が消え、残った「凍結は台帳にしか無く」が**凍結が有効**と読める形になった |
| robot cfg 行 | 「PhysX 実機設定」の前置きを追加 | 「実機」は物理ハードを指すが、これは sim の設定 |

## Rs への所見（既存の問題・本 prune では変更していない）

- NEST: `§運用2 [TASK]` は node_id 書式 `T-{seq}-{sub}-...` を指定するが、LTM-1 §1 は例 `T-08-1-3` のみで書式テンプレートを持たない。「1:1 binding (§5.1)」の §5.1（`:408`）は「同時並行は禁止」までで `1:1` の語を持たない。「handoff 二系統 (§4.2)」の §4.2 は sidecar 側のみを規定する
- `§0` の語が本ファイル内で複数の意味を持つ（本節見出し / RS71 §0 の不変前提 / LTM-1 §0）
- `.claude/rules/prohibited.md` と `.claude/skills/` は gitignore されており、git worktree・clone には存在しない
- `MEMORY.md` は 22,770 chars（wc -m, 本 session 実測）= hard limit 24,986 の 91.1%。§運用31 の 90% 起票閾値を超過（起票済 ticket = memory `project-memory-index-coordinated-compaction-ticket-2026-09-12`）

## ⚠ 行番号 pin への影響

CLAUDE.md の行番号は 2026-09-13 に移動した。repo + memory に `CLAUDE.md:<N>` 形式の pin が 770 件 / 80 file ある（事前検証の実測）。主な pin の移動先（旧 blob `2995cad44e~1` の行を内容一致で探した結果。作業ツリー列は他 pane の未コミット行を含む現物）:

| 旧 | 内容 | 新（blob） | 新（作業ツリー） |
|---|---|---|---|
| `:46` | 新ファイル作成等のハードストップ | `:30` | `:30` |
| `:49` | 引用先に根拠が無いハードストップ | `:33` | `:33` |
| `:67` | write_joint_state_to_sim 例外 | `:51` | `:51` |
| `:72` | kinematic 認可例外 (clip-retention pin) | `:56` | `:56` |
| `:82` | Option-E venv 行 | `:65` | `:none` |
| `:271` | Fingertip Z-Check Gate | `:242` | `:246` |
| `:340` | routing: readback | `:311` | `:315` |
| `:348` | routing: branch/dirty-tree | `:319` | `:323` |

旧 `:82` は他 pane が書き換えた行なので作業ツリーに同一行は無い。⇒ **`CLAUDE.md:<N>` は恒久 address ではない。節見出し等の内容語で引くこと。**
